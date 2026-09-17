import assert from "node:assert/strict";
import { readFileSync, mkdtempSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";
import {
  FIXTURE_TOKENS, assertFixtureTokensOnly, createProofFixture, loadOfflineProofSdk,
} from "./posthog-proof-safety.mjs";

const projects = {
  staging: { token: "phc_SentinelStagingMustNeverExecute".padEnd(48, "X") },
  production: { token: "phc_SentinelProductionMustNeverExecute".padEnd(48, "X") },
};
const source = token => `(() => { const token = "${token}"; const privacy = false; })();\n`;
const fixture = target => createProofFixture({
  source: source(projects[target].token), projects, target,
});

test("both environments get separate nonfunctional tokens with token-only source changes", () => {
  assert.notEqual(FIXTURE_TOKENS.staging, FIXTURE_TOKENS.production);
  for (const target of ["staging", "production"]) {
    const proof = fixture(target);
    assert.equal(proof.token, FIXTURE_TOKENS[target]);
    assert.equal(proof.source,
      source(projects[target].token).replace(projects[target].token, FIXTURE_TOKENS[target]));
    assertFixtureTokensOnly(proof.source);
  }
});

test("inline HTML, flight JSON, and served JavaScript substitute only configured tokens", () => {
  const proof = fixture("production");
  for (const input of [
    `<script>${source(projects.production.token)}</script>`,
    `self.__next_f.push(${JSON.stringify([1, source(projects.staging.token)])})`,
    `window.key="${projects.production.token}";`,
  ]) {
    const expected = input.replaceAll(projects.production.token, FIXTURE_TOKENS.production)
      .replaceAll(projects.staging.token, FIXTURE_TOKENS.staging);
    assert.equal(proof.forBrowser(input), expected);
  }
});

test("token-only substitution preserves Mintlify inline flight byte framing", () => {
  const original = source(projects.staging.token);
  const length = Buffer.byteLength(original);
  const header = `49:T${length.toString(16)},`;
  const body = `<script>self.__next_f.push(${JSON.stringify([1, header])})</script>`
    + `<script>self.__next_f.push(${JSON.stringify([1, original])})</script>`;
  const transformed = fixture("staging").forBrowser(body);
  assert.equal(Buffer.byteLength(fixture("staging").source), length);
  assert.equal(Buffer.byteLength(transformed), Buffer.byteLength(body));
  assert.ok(transformed.includes(header), "the original byte-count header is unchanged");
  assert.equal(transformed, body.replaceAll(projects.staging.token, FIXTURE_TOKENS.staging));
});

test("a future configured token-width change refuses the proof before browser launch", () => {
  assert.throws(() => createProofFixture({
    source: source("phc_Short"), projects: { ...projects, staging: { token: "phc_Short" } },
    target: "staging",
  }), /Configured token width changed/);
});

test("binary responses remain byte-identical except literal token substitution", () => {
  const bytes = Buffer.from([0, 255, 195, 40, 128, 254]);
  assert.deepEqual(fixture("staging").forBrowser(bytes), bytes);
});

test("unknown capture and personal keys are rejected, not silently removed", () => {
  for (const token of ["phc_UnexpectedRealProject", "phx_PrivateKeySentinel", "phs_PrivateKeySentinel"]) {
    assert.throws(() => fixture("staging").forBrowser(`<script>init("${token}")</script>`),
      /Non-fixture PostHog token rejected/);
    assert.throws(() => createProofFixture({
      source: source(projects.staging.token) + source(token), projects, target: "staging",
    }), /Non-fixture PostHog token rejected/);
  }
});

test("encoded live keys fail closed in HTML, JSON, JavaScript and URLs", () => {
  for (const token of [
    "\\u0070hc_UnexpectedRealProject", "\\u{70}hc_UnexpectedRealProject",
    "\\u{00000070}hc_UnexpectedRealProject", "\\x70hc_UnexpectedRealProject",
    "&#112;hc_UnexpectedRealProject", "&#x70;hc_UnexpectedRealProject",
    "%70hc_UnexpectedRealProject", "%2570hc_UnexpectedRealProject",
    "%25252570hc_UnexpectedRealProject",
  ]) assert.throws(() => assertFixtureTokensOnly(token), /Non-fixture PostHog token rejected/);
});

test("decoding beyond the audit limit fails closed, even before a token is visible", () => {
  assert.throws(() => assertFixtureTokensOnly("%2525252570hc_UnexpectedRealProject"),
    /Token-audit decoding limit exceeded/);
  assert.throws(() => assertFixtureTokensOnly("%2525252561"),
    /Token-audit decoding limit exceeded/);
});

test("response guard rejects unsafe JS before calling the browser response API", async () => {
  const calls = [];
  const request = { url: () => "https://docs.relayapp.im/asset.js",
    respond: value => calls.push(value) };
  await assert.rejects(() => fixture("production").respond(request, {
    contentType: "text/javascript", body: 'init("phc_UnexpectedRealProject")',
  }), /Non-fixture PostHog token rejected/);
  assert.equal(calls.length, 0);
  await fixture("production").respond(request, {
    contentType: "text/javascript", body: source(projects.production.token),
  });
  assert.equal(calls.length, 1);
  assert.equal(calls[0].body, source(FIXTURE_TOKENS.production));
});

test("offline SDK setup requires egress-deny confirmation and rejects SDK-embedded keys", () => {
  const directory = mkdtempSync(join(tmpdir(), "docs-safe-sdk-"));
  try {
    const file = join(directory, "sdk.js");
    writeFileSync(file, "window.posthog = {};");
    assert.throws(() => loadOfflineProofSdk({ POSTHOG_TEST_SDK_PATH: file }), /outbound deny/);
    assert.throws(() => loadOfflineProofSdk({ POSTHOG_TEST_NETWORK_DENIED: "1" }), /SDK_PATH/);
    assert.equal(loadOfflineProofSdk({
      POSTHOG_TEST_NETWORK_DENIED: "1", POSTHOG_TEST_SDK_PATH: file,
    }).toString(), "window.posthog = {};");
    writeFileSync(file, 'init("phc_UnexpectedRealProject");');
    assert.throws(() => loadOfflineProofSdk({
      POSTHOG_TEST_NETWORK_DENIED: "1", POSTHOG_TEST_SDK_PATH: file,
    }), /Non-fixture PostHog token rejected/);
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});

test("both browser proofs use the shared guard, offline SDK, and fixture token assertions", () => {
  for (const name of ["test-posthog-browser.mjs", "test-mintlify-posthog-preview.mjs"]) {
    const text = readFileSync(new URL(name, import.meta.url), "utf8");
    assert.match(text, /createProofFixture/);
    assert.match(text, /loadOfflineProofSdk/);
    assert.match(text, /fixture\.respond\(request,/);
    assert.doesNotMatch(text, /request\.respond\(/);
    assert.ok(text.indexOf("createProofFixture({") < text.indexOf("puppeteer.launch("));
    assert.ok(text.indexOf("loadOfflineProofSdk()") < text.indexOf("puppeteer.launch("));
    assert.match(text, /event\.properties\.token, fixture\.token/);
    assert.doesNotMatch(text, /allAnalyticsInterceptedBeforeNavigation: true|all browser network intercepted/);
  }
});
