#!/usr/bin/env node

import { readFile, writeFile } from "node:fs/promises";

const path = new URL("../api-reference/openapi.mint.yaml", import.meta.url);
const input = await readFile(path, "utf8");
const webhooks = input.search(/^webhooks:\s*$/m);
const components = input.search(/^components:\s*$/m);

if (webhooks < 0 && components >= 0) {
  console.log("Mintlify bundle already has no top-level webhooks");
  process.exit(0);
}
if (webhooks < 0 || components < 0 || components <= webhooks) {
  throw new Error("Expected top-level webhooks before components in the Mintlify bundle.");
}

const output = `${input.slice(0, webhooks)}${input.slice(components)}`;
await writeFile(path, output);
console.log("Mintlify bundle keeps HTTP endpoints; webhook events use the hand-written reference");
