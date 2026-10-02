// Run against a built, pinned SDK candidate. Only the HTTP transport is mocked.
// RELAY_LIST_PICKER_SDK points to its repository; no live Relay account is used.
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const sdk = process.env.RELAY_LIST_PICKER_SDK;
assert.ok(sdk, 'Set RELAY_LIST_PICKER_SDK to the built candidate repository');
const dir = mkdtempSync(join(sdk, '.docs-list-picker-'));
try {
  const guide = readFileSync(join(root, 'interactions/selection.mdx'), 'utf8');
  const groups = [...guide.matchAll(/<CodeGroup>([\s\S]*?)<\/CodeGroup>/g)];
  const typescriptFiles = [];
  for (const [index, group] of groups.entries()) {
    const ts = group[1].match(/```typescript[^\n]*\n([\s\S]*?)```/)[1];
    const https = group[1].match(/```bash[^\n]*\n([\s\S]*?)```/)[1];
    const expected = JSON.parse(https.match(/-d '([\s\S]*?)'/)[1]);
    const imported = ts.replaceAll('"@relaymessenger/sdk"', '"../packages/sdk/dist/index.js"');
    const code = `
import assert from 'node:assert/strict';
const bodies: unknown[] = [];
globalThis.fetch = async (input, init) => {
  assert.equal(String(input), 'https://api.staging.relayapp.im/v1/chats/CHAT_ID/messages');
  assert.equal(init?.method, 'POST');
  assert.equal(new Headers(init?.headers).get('authorization'), 'Bearer test-token');
  assert.equal(new Headers(init?.headers).get('idempotency-key'), ${JSON.stringify(expected.message.idempotency_key)});
  bodies.push(JSON.parse(String(init?.body)));
  return Response.json({}, {status: 202});
};
process.env.RELAY_AGENT_TOKEN = 'test-token';
${imported}
assert.deepEqual(bodies, [${JSON.stringify(expected)}]);
console.log('PASS TypeScript example ${index + 1}: real SDK, captured HTTP');
`;
    const filename = join(dir, `example-${index}.mts`);
    writeFileSync(filename, code);
    typescriptFiles.push(filename);
    const py = group[1].match(/```python[^\n]*\n([\s\S]*?)```/);
    if (py) {
      const python = `
import json, os
from unittest.mock import patch
from relaymessenger.client import _Transport
bodies = []
def capture(self, method, url, body, headers):
    assert method == "POST"
    assert url == "https://api.staging.relayapp.im/v1/chats/CHAT_ID/messages"
    assert headers["authorization"] == "Bearer test-token"
    assert headers["idempotency-key"] == ${JSON.stringify(expected.message.idempotency_key)}
    bodies.append(json.loads(body))
    return 202, b"{}", {}
os.environ["RELAY_AGENT_TOKEN"] = "test-token"
with patch.object(_Transport, "_once", capture):
${py[1].split('\n').map(line => '    ' + line).join('\n')}
assert bodies == json.loads(${JSON.stringify(JSON.stringify([expected]))})
print("PASS Python example ${index + 1}: real SDK, captured HTTP")
`;
      console.log(execFileSync('python3', ['-c', python], {
        encoding: 'utf8',
        env: { ...process.env, PYTHONPATH: join(sdk, 'python/relaymessenger/src') },
      }));
    }
  }
  const handler = guide.match(/```typescript Application handler\n([\s\S]*?)```/)[1];
  const handlerFile = join(dir, 'handler.mts');
  writeFileSync(handlerFile, handler.replaceAll('"@relaymessenger/sdk"', '"../packages/sdk/dist/index.js"'));
  typescriptFiles.push(handlerFile);
  execFileSync(join(sdk, 'node_modules/.bin/tsc'), [
    '--module', 'NodeNext', '--moduleResolution', 'NodeNext', '--target', 'ES2023',
    '--strict', '--skipLibCheck', '--types', 'node', ...typescriptFiles,
  ], { cwd: sdk, stdio: 'inherit' });
  console.log('PASS TypeScript send examples and event handler: typechecked against real SDK');
  for (const file of typescriptFiles.filter(path => !path.endsWith('handler.mts'))) {
    console.log(execFileSync(process.execPath, [file.replace(/\.mts$/, '.mjs')], { encoding: 'utf8' }));
  }
} finally { rmSync(dir, { recursive: true, force: true }); }
