// Test-only boundary. These tokens are not credentials for any real project.
// Request interception is not an egress boundary, especially during unload.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

export const FIXTURE_TOKENS = Object.freeze({
  // Mintlify's inline React flight records carry a UTF-8 byte length. Keep
  // literal replacement equal-width so no framing/header rewrite is needed.
  staging: "phc_RelayDocsMockStagingNotARealProject".padEnd(48, "X"),
  production: "phc_RelayDocsMockProductionNotARealProject".padEnd(48, "X"),
});
const allowedTokens = new Set(Object.values(FIXTURE_TOKENS));
const tokenPattern = /\bph[cxs]_[A-Za-z0-9_+/=-]+/g;

function decodedForAudit(value) {
  // Recognize common HTML/JS/JSON/URL serialization without altering the bytes
  // served to the browser. Encoded live tokens fail closed rather than being
  // silently rewritten through a second, nonliteral substitution mechanism.
  return value
    .replace(/\\u\{([0-9a-f]+)\}/gi, (_, code) => String.fromCodePoint(parseInt(code, 16)))
    .replace(/\\u([0-9a-f]{4})/gi, (_, code) => String.fromCharCode(parseInt(code, 16)))
    .replace(/\\x([0-9a-f]{2})/gi, (_, code) => String.fromCharCode(parseInt(code, 16)))
    .replace(/&#x([0-9a-f]+);/gi, (_, code) => String.fromCodePoint(parseInt(code, 16)))
    .replace(/&#([0-9]+);/g, (_, code) => String.fromCodePoint(Number(code)))
    .replace(/%([0-9a-f]{2})/gi, (_, code) => String.fromCharCode(parseInt(code, 16)));
}

export function assertFixtureTokensOnly(input, label = "browser content") {
  let text = Buffer.isBuffer(input) ? input.toString("latin1") : String(input);
  const maximumDecodes = 4;
  for (let pass = 0; pass <= maximumDecodes; pass++) {
    for (const token of text.match(tokenPattern) || []) {
      assert.ok(allowedTokens.has(token), `Non-fixture PostHog token rejected in ${label}`);
    }
    const decoded = decodedForAudit(text);
    if (decoded === text) return;
    assert.ok(pass < maximumDecodes, `Token-audit decoding limit exceeded in ${label}`);
    text = decoded;
  }
}

export function createProofFixture({ source, projects, target }) {
  assert.ok(Object.hasOwn(FIXTURE_TOKENS, target), "Unknown mock proof environment");
  for (const environment of Object.keys(FIXTURE_TOKENS)) {
    assert.match(projects[environment]?.token || "", /^phc_[A-Za-z0-9]+$/);
    assert.ok(!allowedTokens.has(projects[environment].token),
      "Load the actual public config for comparison; substitution happens only in memory");
    assert.equal(projects[environment].token.length, FIXTURE_TOKENS[environment].length,
      "Configured token width changed; update nonfunctional fixtures before executing framed preview content");
  }
  assert.notEqual(projects.staging.token, projects.production.token);
  assert.ok(source.includes(projects[target].token), "Candidate does not contain its configured project token");

  function forBrowser(input, label = "browser content") {
    const binary = Buffer.isBuffer(input);
    // Latin-1 makes the replacement byte-preserving for binary/static assets.
    let output = binary ? input.toString("latin1") : String(input);
    for (const environment of Object.keys(FIXTURE_TOKENS)) {
      output = output.replaceAll(projects[environment].token, FIXTURE_TOKENS[environment]);
    }
    assertFixtureTokensOnly(output, label);
    return binary ? Buffer.from(output, "latin1") : output;
  }

  const executableSource = forBrowser(source, "candidate JavaScript");
  return Object.freeze({
    token: FIXTURE_TOKENS[target],
    source: executableSource,
    forBrowser,
    async respond(request, response) {
      // Every HTML, inline-flight payload, SDK, and served JS response passes
      // this guard before Puppeteer can deliver it for browser execution.
      assertFixtureTokensOnly(request.url(), "request URL");
      assertFixtureTokensOnly(JSON.stringify(response.headers || {}), "response headers");
      const body = forBrowser(response.body ?? "", "served response");
      return request.respond({ ...response, body });
    },
  });
}

export function loadOfflineProofSdk(environment = process.env) {
  // This flag records operator confirmation; it does not create the firewall.
  // Verify the Daytona runner's outbound-deny policy before setting it.
  assert.equal(environment.POSTHOG_TEST_NETWORK_DENIED, "1",
    "Confirm sandbox outbound deny, then set POSTHOG_TEST_NETWORK_DENIED=1");
  assert.ok(environment.POSTHOG_TEST_SDK_PATH,
    "Set POSTHOG_TEST_SDK_PATH to a separately GET-downloaded SDK asset");
  const sdk = readFileSync(environment.POSTHOG_TEST_SDK_PATH);
  assertFixtureTokensOnly(sdk, "offline SDK");
  return sdk;
}
