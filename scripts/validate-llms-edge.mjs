import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";

const root = new URL("../", import.meta.url);
const configText = await readFile(
  new URL("edge/llms-proxy/wrangler.jsonc", root),
  "utf8",
);
const config = JSON.parse(configText);
const vars = config.env.staging.vars;
const sha256 = async (path) => createHash("sha256")
  .update(await readFile(new URL(path, root)))
  .digest("hex");
const llmsIndex = await readFile(new URL("llms.txt", root), "utf8");
const llmsFull = await readFile(new URL("llms-full.txt", root), "utf8");

assert.equal(vars.LLMS_VERSION, await sha256("llms.txt"));
assert.equal(vars.LLMS_FULL_VERSION, await sha256("llms-full.txt"));
assert.equal(vars.MINTLIFY_ORIGIN, "https://relay-staging.mintlify.app");
assert.match(llmsIndex, /\/guides\/webhooks\/events\.md/);
assert.doesNotMatch(llmsIndex, /\/guides\/agent-events/);
for (const marker of [
  "/v1/websocket",
  "/v1/webhook-subscriptions",
  "2026-08-30",
]) {
  assert.ok(
    llmsIndex.includes(marker),
    `local staging LLM source is missing hosted-search marker ${marker}`,
  );
}
assert.match(llmsFull, /"api_version": "v1"/);
assert.match(llmsFull, /webhook_version": "2026-08-30"/);
assert.doesNotMatch(llmsFull, /2026-02-03/);
assert.match(
  llmsFull,
  /Delivered means Relay accepted and stored the Message/,
);
assert.match(
  llmsFull,
  /Webhook `2xx` responses and WebSocket ACKs acknowledge event transport only/,
);
assert.match(
  llmsFull,
  /the only operation that advances Read is\s+`POST \/v1\/chats\/\{chatId\}\/read`/,
);
assert.match(llmsFull, /does\s+not show those labels in group Chats/);
assert.doesNotMatch(llmsFull, /marks that agent recipient Delivered/i);
assert.doesNotMatch(llmsFull, /marks the Message Delivered to the agent/i);
assert.match(llmsFull, /Prepare hosted proof/);
assert.match(
  llmsFull,
  /Local Docs validation (?:prepares these source markers|does not claim that hosted result)/,
);
assert.deepEqual(
  config.env.staging.routes,
  [
    {
      pattern: "docs.staging.relayapp.im",
      custom_domain: true,
    },
  ],
);

const worker = await readFile(
  new URL("edge/llms-proxy/src/index.ts", root),
  "utf8",
);
assert.match(worker, /import llms from "\.\.\/\.\.\/\.\.\/llms\.txt"/);
assert.match(worker, /import llmsFull from "\.\.\/\.\.\/\.\.\/llms-full\.txt"/);
assert.match(worker, /document\.body/);
assert.match(worker, /response\.body/);
assert.match(worker, /no-store, max-age=0/);
assert.match(worker, /X-Relay-Docs-Proxy/);
assert.doesNotMatch(worker, /response\.(text|json|arrayBuffer)\(/);
assert.doesNotMatch(worker, /Set-Cookie.*set/i);

const workflow = await readFile(
  new URL(".github/workflows/staging-edge.yml", root),
  "utf8",
);
const credentialStepStart = workflow.indexOf(
  "- name: Load approved staging Worker deploy credentials",
);
assert.notEqual(credentialStepStart, -1);
const credentialStepEnd = workflow.indexOf("\n      - ", credentialStepStart + 1);
assert.notEqual(credentialStepEnd, -1);
const credentialStep = workflow.slice(credentialStepStart, credentialStepEnd);
assert.match(credentialStep, /env-slug: staging/);
assert.match(credentialStep, /secret-path: \/ci\/server/);
assert.doesNotMatch(workflow, /secret-path: \/ci\/website/);
assert.match(
  workflow,
  /wrangler deploy[\s\S]*?--config edge\/llms-proxy\/wrangler\.jsonc[\s\S]*?--env staging/,
);
assert.doesNotMatch(workflow, /--env (?:production|prod)\b/);
assert.doesNotMatch(workflow, /Wait for the matching Mintlify source/);

console.log(
  "local staging LLM sources, deployment credentials, routes, and passthrough verified",
);
