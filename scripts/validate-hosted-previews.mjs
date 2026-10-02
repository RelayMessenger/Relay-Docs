// Read-only HTTP gate. Run against an owned Daytona preview before merge;
// run against hosted staging after its deployment, never infer deployment from git.
import assert from "node:assert/strict";

const base = new URL(process.env.DOCS_BASE_URL || "https://docs.staging.relayapp.im");
assert.ok(["https:", "http:"].includes(base.protocol));
async function read(path) {
  const url = new URL(path, base);
  const response = await fetch(url, { signal: AbortSignal.timeout(30_000) });
  assert.equal(response.status, 200, `${url.pathname}: HTTP ${response.status}`);
  return response.text();
}
const integrations = await read("/integrations");
for (const title of ["Coding agents", "Frameworks and protocols", "Voice", "Build it yourself"]) {
  assert.ok(integrations.includes(title), `Missing shipped integration section: ${title}`);
}
assert.match(integrations, /images\/brands\/mcp\.svg/);
const logo = await read("/images/brands/mcp.svg");
assert.match(logo, /<svg/);
assert.match(logo, /viewBox="0 0 180 180"/);
const cards = await read("/interactions/rich-cards");
assert.match(cards, /Interactive rich card preview/);
assert.match(cards, /Interactive carousel preview/);
assert.match(cards, /rich-suggestions/);
const form = await read("/interactions/form");
assert.match(form, /Interactive form preview/);
assert.match(form, /native-form-sheet/);
assert.match(form, /Answers stay in this page/);
console.log(JSON.stringify({
  origin: base.origin,
  checks: ["shipped integration groups", "MCP SVG response", "card preview", "carousel preview", "form preview"],
  note: "DOM interaction, rendered dimensions, themes and keyboard behavior require the T3 preview check.",
}));
