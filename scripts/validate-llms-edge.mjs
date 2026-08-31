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
  config.env.staging.routes.map((route) => route.pattern).sort(),
  [
    "docs.staging.relayapp.im/llms-full.txt",
    "docs.staging.relayapp.im/llms.txt",
  ],
);

const worker = await readFile(
  new URL("edge/llms-proxy/src/index.ts", root),
  "utf8",
);
assert.match(worker, /response\.body/);
assert.match(worker, /no-store, max-age=0/);
assert.doesNotMatch(worker, /response\.(text|json|arrayBuffer)\(/);
assert.doesNotMatch(worker, /Set-Cookie.*set/i);

console.log("staging LLM edge source, routes, and streaming boundary verified");
