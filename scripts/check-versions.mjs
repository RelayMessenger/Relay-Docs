#!/usr/bin/env node
// Fail the build when a page states a package version that versions.json does
// not carry, or states one with no package name beside it.
//
// This is the offline half of the version contract. scripts/refresh-versions.mjs
// reads the live registries and writes versions.json plus every page; this check
// runs inside npm run validate with no network and proves no page drifted away
// from that one source, and that nobody reintroduced a loose literal.

import { readFile } from "node:fs/promises";
import { readdirSync, statSync } from "node:fs";
import path from "node:path";
import process from "node:process";

const root = path.resolve(import.meta.dirname, "..");

// Generated outputs are rebuilt from the pages and verified by npm run
// check:llms, and scripts/ecosystem-hosted-lock.json is verified against the
// live registry by npm run validate:ecosystem-hosted, so neither is scanned
// here.
const SCAN_DIRECTORIES = [
  "integrations",
  "examples",
  "getting-started",
  "guides",
  "error",
  "api-reference",
  ".agents",
  ".mintlify",
  ".github",
];
const SCAN_FILES = [
  "index.mdx",
  "README.md",
  "skill.md",
  "AGENTS.md",
  "INFORMATION-ARCHITECTURE.md",
  "agent-prompt.js",
  "scripts/validate-docs.py",
  "scripts/validate-examples.py",
  "scripts/build-llms.py",
  "scripts/build-agent-prompt.py",
  "scripts/validate-hosted-llms.py",
  "scripts/validate-ecosystem-hosted.mjs",
];
const SCAN_EXTENSIONS = new Set([".mdx", ".md", ".py", ".mjs", ".js", ".yaml", ".yml"]);
const SKIP_NAMES = new Set(["node_modules", ".git", ".mint", "dist"]);

// Only prerelease trains this repository publishes. A plain 1.2.3 belongs to a
// third-party dependency and is not this file's business.
const VERSION = /\b\d+\.\d+\.\d+(?:-staging\.\d+|rc\d+)\b/g;

function walk(directory, found = []) {
  let entries;
  try {
    entries = readdirSync(directory);
  } catch {
    return found;
  }
  for (const entry of entries) {
    if (SKIP_NAMES.has(entry)) continue;
    const full = path.join(directory, entry);
    if (statSync(full).isDirectory()) walk(full, found);
    else if (SCAN_EXTENSIONS.has(path.extname(entry))) found.push(full);
  }
  return found;
}

const versions = JSON.parse(await readFile(path.join(root, "versions.json"), "utf8"));
const expected = new Map();
for (const [name, entry] of Object.entries(versions.npm)) {
  expected.set(name, new Set([entry.latest, entry.staging]));
}
for (const [name, version] of Object.entries(versions.pypi)) {
  expected.set(name, new Set([version]));
}

const files = [
  ...SCAN_FILES.map((name) => path.join(root, name)),
  ...SCAN_DIRECTORIES.flatMap((name) => walk(path.join(root, name))),
].filter((file) => {
  if (file === path.join(root, "scripts/check-versions.mjs")) return false;
  if (file === path.join(root, "scripts/refresh-versions.mjs")) return false;
  try {
    return statSync(file).isFile();
  } catch {
    return false;
  }
});

const failures = [];
let checked = 0;

for (const file of new Set(files)) {
  const relative = path.relative(root, file);
  const lines = (await readFile(file, "utf8")).split("\n");
  lines.forEach((line, index) => {
    const matches = line.match(VERSION);
    if (!matches) return;
    const named = [...expected.keys()].filter((name) => line.includes(name));
    for (const match of matches) {
      checked += 1;
      if (named.length === 0) {
        failures.push(
          `${relative}:${index + 1} states version ${match} with no package name `
          + "on the same line, so nothing can keep it true: name the package "
          + "beside the version, or remove the version",
        );
        continue;
      }
      const allowed = named.some((name) => expected.get(name).has(match));
      if (!allowed) {
        const wanted = named
          .map((name) => `${name} is ${[...expected.get(name)].join(" or ")}`)
          .join("; ");
        failures.push(
          `${relative}:${index + 1} states version ${match}, but versions.json `
          + `says ${wanted}: run npm run refresh:versions`,
        );
      }
    }
  });
}

// The manifest lives on the Relay-SDK staging branch, so it carries the
// `staging` tag's version, which is what integrations/claude-code.mdx says.
// Plain releases (0.3.0) fall outside VERSION on purpose, so a page could
// state `@relaymessenger/sdk@0.2.0` and nothing above would notice. Every
// `<package>@<version>` and every `| \`<package>\` | \`<version>\` |` row
// must therefore name a version versions.json carries, whatever its train.
const PLAIN = String.raw`\d+\.\d+\.\d+(?:-[0-9A-Za-z.]+)?`;
for (const file of new Set(files)) {
  const relative = path.relative(root, file);
  const lines = (await readFile(file, "utf8")).split("\n");
  lines.forEach((line, index) => {
    for (const [name, allowed] of expected) {
      const escaped = name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
      const claims = [
        ...line.matchAll(new RegExp(`(?<![\\w./@-])${escaped}@(${PLAIN})\\b`, "g")),
        ...line.matchAll(new RegExp(`\\|\\s*\`${escaped}\`\\s*\\|\\s*\`(${PLAIN})\``, "g")),
      ];
      for (const claim of claims) {
        checked += 1;
        if (!allowed.has(claim[1])) {
          failures.push(
            `${relative}:${index + 1} states ${name}@${claim[1]}, but versions.json `
            + `says ${[...allowed].join(" or ")}: run npm run refresh:versions`,
          );
        }
      }
    }
  });
}

if (versions.claudeCodePluginManifest
  !== versions.npm["relay-claude-channel"]?.staging) {
  failures.push(
    "versions.json says the Relay-SDK Claude Code plugin manifest "
    + `(${versions.claudeCodePluginManifest}) differs from the staging tag `
    + `relay-claude-channel@${versions.npm["relay-claude-channel"]?.staging}, but `
    + "integrations/claude-code.mdx tells readers the staging catalog carries it",
  );
}

if (failures.length > 0) {
  for (const failure of failures) console.error(failure);
  process.exit(1);
}

console.log(
  `verified ${checked} published version strings against versions.json across `
  + `${new Set(files).size} authored files`,
);
