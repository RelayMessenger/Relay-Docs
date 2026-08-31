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

assert.equal(vars.LLMS_VERSION, await sha256("llms.txt"));
assert.equal(vars.LLMS_FULL_VERSION, await sha256("llms-full.txt"));
assert.equal(vars.MINTLIFY_ORIGIN, "https://relay-staging.mintlify.app");
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

console.log(
  "staging LLM edge source, deployment credentials, routes, and streaming boundary verified",
);
