#!/usr/bin/env node
// Refresh every published version claim in this repository from the live
// registries, then propagate the new values into the pages, the hosted lock,
// and the validator.
//
// Ninety stale version strings across fourteen pages existed because each page
// held its own copy and nothing read a registry. versions.json is now the one
// source of truth: this script writes it, and every other file receives its
// values from here. scripts/check-versions.mjs fails the build when a page
// states a version this file does not carry.
//
// Run: npm run refresh:versions
//      npm run refresh:versions -- --check   (fail instead of writing)

import { readFile, writeFile } from "node:fs/promises";
import { readdirSync, statSync } from "node:fs";
import path from "node:path";
import process from "node:process";

const root = path.resolve(import.meta.dirname, "..");
const versionsPath = path.join(root, "versions.json");
const lockPath = path.join(root, "scripts/ecosystem-hosted-lock.json");
const checkOnly = process.argv.includes("--check");

const NPM_PACKAGES = [
  "@relaymessenger/sdk",
  "@relaymessenger/chat-sdk-adapter",
  "@relaymessenger/cli",
  "@relaymessenger/mcp",
  "@relaymessenger/openclaw-plugin",
  "relay-claude-channel",
];
const PYPI_PACKAGES = ["relay-hermes"];
const CLAUDE_PLUGIN_MANIFEST =
  "https://raw.githubusercontent.com/RelayMessenger/Relay-SDK/staging"
  + "/packages/claude-code/plugin/.claude-plugin/plugin.json";

// Text this repository authors. Generated files (llms.txt, llms-full.txt,
// package-lock.json) are rebuilt from these, so they are never edited here.
const SCAN_DIRECTORIES = [
  "ecosystem",
  "examples",
  "getting-started",
  "guides",
  "error",
  "api-reference",
  ".agents",
  ".mintlify",
  "scripts",
];
const SCAN_FILES = [
  "index.mdx",
  "README.md",
  "skill.md",
  "AGENTS.md",
  "INFORMATION-ARCHITECTURE.md",
  "agent-prompt.js",
];
const SCAN_EXTENSIONS = new Set([".mdx", ".md", ".py", ".mjs", ".js", ".yaml", ".yml"]);
const SKIP_NAMES = new Set(["node_modules", ".git", ".mint", "dist"]);

async function json(url, description) {
  const response = await fetch(url, {
    headers: {
      accept: "application/json",
      "user-agent": "Relay-Docs-Version-Refresh/1.0",
    },
  });
  if (response.status !== 200) {
    throw new Error(`${description} returned HTTP ${response.status}: ${url}`);
  }
  return response.json();
}

async function npmPackage(name) {
  const metadata = await json(
    `https://registry.npmjs.org/${encodeURIComponent(name)}`,
    `npm ${name}`,
  );
  const tags = metadata["dist-tags"] ?? {};
  const entry = {
    latest: tags.latest,
    staging: tags.staging,
    integrity: {},
    sourceCommit: null,
  };
  if (!entry.latest) throw new Error(`${name} has no latest dist-tag`);
  if (!entry.staging) throw new Error(`${name} has no staging dist-tag`);
  for (const version of new Set([entry.latest, entry.staging])) {
    const integrity = metadata.versions?.[version]?.dist?.integrity;
    if (!integrity) throw new Error(`${name}@${version} has no registry integrity`);
    entry.integrity[version] = integrity;
  }
  entry.sourceCommit = await npmSourceCommit(name, entry.latest);
  return entry;
}

// npm provenance records the exact commit the published bytes were built from.
// Pages that quote a "published artifact source commit" read it from here, so
// the claim stays checkable instead of remembered.
async function npmSourceCommit(name, version) {
  const url = "https://registry.npmjs.org/-/npm/v1/attestations/"
    + `${encodeURIComponent(name)}@${version}`;
  const response = await fetch(url, {
    headers: { accept: "application/json" },
  });
  if (response.status !== 200) return null;
  const body = await response.json();
  for (const attestation of body.attestations ?? []) {
    const payload = attestation?.bundle?.dsseEnvelope?.payload;
    if (!payload) continue;
    let statement;
    try {
      statement = JSON.parse(Buffer.from(payload, "base64").toString("utf8"));
    } catch {
      continue;
    }
    const resolved =
      statement?.predicate?.buildDefinition?.resolvedDependencies ?? [];
    for (const dependency of resolved) {
      const commit = dependency?.digest?.gitCommit;
      if (commit) return commit;
    }
  }
  return null;
}

async function pypiVersion(name) {
  const metadata = await json(`https://pypi.org/pypi/${name}/json`, `PyPI ${name}`);
  const version = metadata?.info?.version;
  if (!version) throw new Error(`PyPI ${name} has no version`);
  return version;
}

function walk(directory, found = []) {
  for (const entry of readdirSync(directory)) {
    if (SKIP_NAMES.has(entry)) continue;
    const full = path.join(directory, entry);
    if (statSync(full).isDirectory()) {
      walk(full, found);
    } else if (SCAN_EXTENSIONS.has(path.extname(entry))) {
      found.push(full);
    }
  }
  return found;
}

function scanPaths() {
  const found = [];
  for (const name of SCAN_FILES) found.push(path.join(root, name));
  for (const name of SCAN_DIRECTORIES) {
    try {
      walk(path.join(root, name), found);
    } catch {
      // A directory that does not exist carries no version claim.
    }
  }
  found.push(path.join(root, ".github/workflows"));
  return found
    .filter((file) => {
      try {
        return statSync(file).isFile();
      } catch {
        return false;
      }
    })
    .filter((file) => file !== path.join(root, "scripts/refresh-versions.mjs"))
    .filter((file) => file !== path.join(root, "scripts/check-versions.mjs"));
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

const SEMVER = String.raw`\d+\.\d+\.\d+(?:-staging\.\d+|rc\d+)`;

// Replacement is anchored to the package name so two packages that share a
// version string can never overwrite each other.
function propagate(text, previous, next) {
  let output = text;
  const packages = [
    ...Object.keys(next.npm).map((name) => [
      name,
      previous.npm[name]?.latest,
      next.npm[name].latest,
    ]),
    ...Object.keys(next.pypi).map((name) => [
      name,
      previous.pypi[name],
      next.pypi[name],
    ]),
  ];

  for (const [name, oldVersion, newVersion] of packages) {
    const escaped = escapeRegExp(name);
    // `package@version` anywhere.
    output = output.replaceAll(
      new RegExp(`(?<![\\w./@-])(${escaped}@)${SEMVER}`, "g"),
      `$1${newVersion}`,
    );
    // A table row that names the package in one cell and the version in the next.
    output = output.replaceAll(
      new RegExp(
        `(\`${escaped}\`\\s*\\|\\s*\`)${SEMVER}(\`)`,
        "g",
      ),
      `$1${newVersion}$2`,
    );
    // A Python or JSON list that pairs the name and the version as neighbours.
    output = output.replaceAll(
      new RegExp(`("${escaped}"\\s*:\\s*")${SEMVER}(")`, "g"),
      `$1${newVersion}$2`,
    );
    if (oldVersion && oldVersion !== newVersion) {
      const integrity = previous.npm[name]?.integrity?.[oldVersion];
      const replacement = next.npm[name]?.integrity?.[newVersion];
      if (integrity && replacement) {
        output = output.replaceAll(integrity, replacement);
      }
    }
  }

  // Registry integrity and published source commits are globally unique, so a
  // whole-text replacement of the previous value cannot hit anything else.
  for (const [name, entry] of Object.entries(next.npm)) {
    const before = previous.npm[name];
    if (!before) continue;
    if (before.sourceCommit && entry.sourceCommit
      && before.sourceCommit !== entry.sourceCommit) {
      output = output.replaceAll(before.sourceCommit, entry.sourceCommit);
    }
  }
  return output;
}

function refreshHostedLock(lock, next) {
  for (const [name, entry] of Object.entries(next.npm)) {
    if (!lock.npm[name]) continue;
    lock.npm[name].tags = { latest: entry.latest, staging: entry.staging };
    lock.npm[name].integrity = { ...entry.integrity };
  }
  return lock;
}

async function main() {
  const previous = JSON.parse(await readFile(versionsPath, "utf8"));
  const next = {
    comment: previous.comment,
    checked: new Date().toISOString().slice(0, 10),
    npm: {},
    pypi: {},
    claudeCodePluginManifest: null,
  };

  for (const name of NPM_PACKAGES) next.npm[name] = await npmPackage(name);
  for (const name of PYPI_PACKAGES) next.pypi[name] = await pypiVersion(name);

  const manifest = await json(CLAUDE_PLUGIN_MANIFEST, "Claude Code plugin manifest");
  next.claudeCodePluginManifest = manifest.version;

  // ecosystem/claude-code.mdx states that the catalog plugin carries the same
  // version as the published channel package. That sentence is only true while
  // the two agree, so the refresh proves it instead of assuming it.
  const channelVersion = next.npm["relay-claude-channel"].latest;
  if (next.claudeCodePluginManifest !== channelVersion) {
    throw new Error(
      "the Relay-SDK Claude Code plugin manifest "
      + `(${next.claudeCodePluginManifest}) no longer matches `
      + `relay-claude-channel@${channelVersion}; ecosystem/claude-code.mdx must `
      + "state the two versions separately before this refresh can pass",
    );
  }

  const files = scanPaths();
  const edits = [];
  for (const file of files) {
    const text = await readFile(file, "utf8");
    const updated = propagate(text, previous, next);
    if (updated !== text) edits.push([file, updated]);
  }

  const lock = refreshHostedLock(
    JSON.parse(await readFile(lockPath, "utf8")),
    next,
  );
  const lockText = `${JSON.stringify(lock, null, 2)}\n`;
  const versionsText = `${JSON.stringify(next, null, 2)}\n`;

  const staleFiles = [
    ...edits.map(([file]) => path.relative(root, file)),
    ...(versionsText === await readFile(versionsPath, "utf8") ? [] : ["versions.json"]),
    ...(lockText === await readFile(lockPath, "utf8")
      ? []
      : ["scripts/ecosystem-hosted-lock.json"]),
  ];

  if (checkOnly) {
    if (staleFiles.length > 0) {
      console.error(
        `these files disagree with the live registries: ${staleFiles.join(", ")}`,
      );
      process.exit(1);
    }
    console.log("every published version claim matches the live registries");
    return;
  }

  for (const [file, updated] of edits) await writeFile(file, updated);
  await writeFile(versionsPath, versionsText);
  await writeFile(lockPath, lockText);

  console.log(
    `refreshed ${Object.keys(next.npm).length} npm packages, `
    + `${Object.keys(next.pypi).length} PyPI package, and the Claude Code plugin `
    + `manifest into ${edits.length} files`,
  );
  for (const file of staleFiles) console.log(`  updated ${file}`);
}

await main();
