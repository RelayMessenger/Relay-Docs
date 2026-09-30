// Examples execute against local capture clients, never a live Relay account.
import assert from 'node:assert/strict';
import { readFileSync, mkdtempSync, mkdirSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';
import vm from 'node:vm';
import YAML from 'yaml';
import Ajv from 'ajv/dist/2020.js';
import addFormats from 'ajv-formats';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const files = ['interactions/selection.mdx', 'interactions/selection-reference.mdx',
  'docs.json', 'messages/parts.mdx', 'api-reference/openapi.yaml'];
const read = (root, path) => readFileSync(join(root, path), 'utf8');
const fences = text => [...text.matchAll(/```(\w+)([^\n]*)\n([\s\S]*?)```/g)];
const clone = value => JSON.parse(JSON.stringify(value));

function validators(root) {
  const schemas = YAML.parse(read(root, 'api-reference/openapi.yaml')).components.schemas;
  const ajv = new Ajv({ strict: false, allErrors: true });
  addFormats(ajv);
  const compile = name => ajv.compile({
    components: { schemas }, $ref: `#/components/schemas/${name}`,
  });
  return { schemas, prompt: compile('SelectionPart'), reply: compile('SelectionResponsePart'),
    stored: compile('SelectionResponsePartResponse'), projected: compile('SelectionPartResponse') };
}

function valid(check, value, label) {
  assert.equal(check(value), true, `${label}: ${JSON.stringify(check.errors)}`);
}

function captureTypeScript(code) {
  const bodies = [];
  const Relay = class {
    chats = { messages: { send: async (chat, body) => { bodies.push(body); } } };
  };
  const clean = code.replace(/^import .*?;\n/gm, '').replace(/process\.env\.(\w+)!/g, 'process.env.$1');
  const context = vm.createContext({
    Relay, process: { env: { RELAY_AGENT_TOKEN: 'test-token', CHAT_ID: 'CHAT_ID' } },
    partsWithSelection: (text, part) => [{ type: 'text', value: text }, part],
  });
  return vm.runInContext(`(async () => {${clean}\n})()`, context, { timeout: 1000 })
    .then(() => clone(bodies));
}

function capturePython(code) {
  const harness = `
import asyncio, json, os, sys, types
bodies = []
class Messages:
    async def send(self, chat, body):
        bodies.append(body)
class Relay:
    def __init__(self, **kwargs):
        self.chats = types.SimpleNamespace(messages=Messages())
module = types.ModuleType("relaymessenger")
module.Relay = Relay
sys.modules["relaymessenger"] = module
os.environ["RELAY_AGENT_TOKEN"] = "test-token"
os.environ["CHAT_ID"] = "CHAT_ID"
exec(${JSON.stringify(code)})
print(json.dumps(bodies))
`;
  return JSON.parse(execFileSync('python3', ['-c', harness], { encoding: 'utf8' }));
}

export async function checkDocs(root) {
  const guide = read(root, files[0]);
  const reference = read(root, files[1]);
  const { schemas, prompt, reply, stored, projected } = validators(root);
  assert.ok(JSON.parse(read(root, 'docs.json')).navigation);
  assert.ok(read(root, 'docs.json').includes('"interactions/selection-reference"'), 'reference navigation');
  assert.ok(guide.includes('/interactions/selection-reference'), 'guide reference link');
  assert.ok(read(root, 'messages/parts.mdx').includes('selected_ids'), 'parts overview IDs');
  for (const phrase of [
    '`multiple` defaults to `true`', 'exactly one of `options` or `sections`',
    '1 to 200', '1 to 100', '1 to 24', '1 to 80', '0 to 72', '0 to 512', '1 to 512',
    '1 to 10', '1 to 25', '2,048', 'source order',
    '`selected_values` is required', '`selected_ids` must equal `selected_values`',
    'copies `reply_message` from the source', 'after the source Message is deleted',
    'source title and chosen labels', 'always includes flat `options`',
    'viewer', 'always `null` for an agent',
    'counts the text as sent', 'blank after trimming is stored as absent', 'ignore `multiple: false`',
  ]) assert.ok(reference.includes(phrase), `reference missing: ${phrase}`);
  assert.ok(guide.includes('ignore `multiple: false`'), 'guide warns about older app versions');
  for (const [field, limits] of [
    ['`title`', ['1 to 60']], ['`subtitle`', ['0 to 512']],
    ['`options`', ['1 to 25']], ['`sections`', ['1 to 10', '1 to 24', '1 to 25']],
    ['`reply_message.title`', ['1 to 512']], ['`reply_message.subtitle`', ['0 to 512']],
    ['`id`', ['1 to 200']], ['`value`', ['1 to 100', '200-character']],
    ['`label`', ['1 to 24', '1 to 80']], ['`image_url`', ['HTTPS', '2,048']],
  ]) {
    const row = reference.split('\n').find(line => line.startsWith(`| ${field} |`));
    assert.ok(row, `missing field row ${field}`);
    for (const limit of limits) assert.ok(row.includes(limit), `${field}: ${limit}`);
  }
  for (const stale of ['An option has only `value` and `label`', '`multiple` defaults to `false`']) {
    assert.ok(!guide.includes(stale) && !reference.includes(stale), `stale claim: ${stale}`);
  }
  for (const text of [guide, reference]) {
    assert.ok(!/\b(?:A2A|expires_at|expireTime|ttl)\b/.test(text), 'out-of-scope addition');
  }

  const groups = [...guide.matchAll(/<CodeGroup>([\s\S]*?)<\/CodeGroup>/g)]
    .map(match => fences(match[1])).filter(blocks => blocks.some(b => b[1] === 'bash'));
  assert.equal(groups.length, 2, 'preserve flat examples and add one grouped send');
  let grouped;
  for (const blocks of groups) {
    assert.equal(blocks[0][1], 'typescript', 'SDK first');
    const https = blocks.find(b => b[1] === 'bash')[3];
    const body = JSON.parse(https.match(/-d '([\s\S]*?)'/)[1]);
    const ts = await captureTypeScript(blocks.find(b => b[1] === 'typescript')[3]);
    assert.deepEqual(ts, [body], 'TypeScript/HTTPS example parity');
    const py = blocks.find(b => b[1] === 'python');
    if (py) assert.deepEqual(capturePython(py[3]), [body], 'Python/HTTPS example parity');
    const part = body.message.parts.find(p => p.type === 'selection');
    valid(prompt, part, 'send example');
    if (part.sections) {
      grouped = part;
      assert.ok(py, 'grouped example needs Python');
      assert.ok(part.subtitle && part.reply_message, 'show card and answered text');
      assert.equal(part.multiple, false, 'show single choice');
      assert.ok(part.sections.flatMap(s => s.options).some(o => o.image_url), 'show row image');
    } else {
      assert.deepEqual(part.options, [{ value: 'research', label: 'Research' },
        { value: 'design', label: 'Design' }], 'old flat example preserved');
    }
  }
  assert.ok(grouped, 'grouped request missing');
  for (const [, lang, , code] of fences(guide)) {
    if (lang !== 'json') continue;
    const value = JSON.parse(code);
    if (value.message) {
      valid(prompt, value.message.parts.find(p => p.type === 'selection'), 'flat JSON prompt');
    } else if (value.event_type === 'message.received') {
      const metadata = value.data.parts[1];
      valid(stored, metadata, 'received answer');
      assert.deepEqual(metadata.selected_ids, metadata.selected_values, 'received aliases agree');
      assert.deepEqual(metadata.selected_ids, ['research', 'design'], 'received source order');
      assert.equal(value.data.parts[0].value, '• Research\n• Design', 'portable answer text');
      assert.equal(value.data.reply_to.part_index, 1, 'answer points at the selection');
    } else if (value.type === 'selection') valid(projected, value, 'viewer prompt');
    else assert.fail('unclassified guide JSON example');
  }
  for (const [, lang, title, code] of fences(reference)) {
    if (lang !== 'json') continue;
    const value = JSON.parse(code);
    const check = ({ 'Prompt': prompt, 'Reply input': reply, 'Stored reply': stored,
      'Prompt response': projected })[title.trim()];
    assert.ok(check, `unclassified reference example: ${title}`);
    valid(check, value, title);
  }

  // Read the canonical schema, not a docs-owned copy of its rules.
  assert.equal(schemas.SelectionPart.properties.multiple.default, true, 'canonical multiple default');
  assert.equal(schemas.SelectionPart.properties.subtitle.maxLength, 512, 'card subtitle limit');
  assert.equal(schemas.SelectionPart.properties.sections.maxItems, 10, 'section limit');
  assert.equal(schemas.SelectionPart.properties.options.maxItems, 25, 'option limit');
  assert.ok(schemas.SelectionResponsePart.required.includes('selected_values'));
  assert.ok(schemas.SelectionResponsePart.properties.selected_ids, 'input IDs');
  assert.ok(!schemas.SelectionResponsePart.properties.reply_message, 'answered copy is server-owned');

  const flat = { type: 'selection', title: 'Topics',
    options: [{ id: 'x'.repeat(200), label: 'L'.repeat(24), subtitle: 'S'.repeat(72),
      image_url: 'https://example.com/row.png' }], subtitle: 'S'.repeat(512),
    reply_message: { title: 'T'.repeat(512), subtitle: 'S'.repeat(512) } };
  valid(prompt, flat, 'maximum new fields');
  const emptySubtitles = clone(flat);
  emptySubtitles.subtitle = '';
  emptySubtitles.options[0].subtitle = '';
  emptySubtitles.reply_message.subtitle = '';
  valid(prompt, emptySubtitles, 'empty optional subtitles');
  valid(prompt, { type: 'selection', title: '🌱'.repeat(60), subtitle: '🌱'.repeat(512),
    options: [{ id: '🌱'.repeat(200), label: '🌱'.repeat(24), subtitle: '🌱'.repeat(72) }],
    reply_message: { title: '🌱'.repeat(512), subtitle: '🌱'.repeat(512) },
  }, 'Unicode character limits match the canonical schema');
  assert.equal(prompt({ type: 'selection', title: 'Unicode',
    options: [{ id: '🌱'.repeat(201), label: 'Label' }],
  }), false, '201 Unicode characters exceed the ID limit');
  valid(prompt, { type: 'selection', title: 'Legacy', options: [
    { value: 'v'.repeat(100), label: 'L'.repeat(80) },
  ] }, 'legacy value/label limits');
  valid(projected, { type: 'selection', title: 'Legacy',
    options: [{ id: 'legacy', value: 'legacy', label: 'L'.repeat(80) }],
    has_responded: false, selected_ids: null, selected_values: null, reactions: null,
  }, 'returned legacy label remains readable with normalized id');
  assert.equal(projected({ type: 'selection', title: 'Legacy',
    options: [{ value: 'legacy', label: 'Legacy' }],
    has_responded: false, selected_ids: null, selected_values: null, reactions: null,
  }), false, 'returned options require id and value');
  const invalidPrompts = [
    ['both arrays', p => { p.sections = [{ title: 'Both', options: p.options }]; }],
    ['no arrays', p => { delete p.options; }],
    ['201-character ID', p => { p.options[0].id += 'x'; }],
    ['25-character new label', p => { p.options[0].label += 'x'; }],
    ['73-character row subtitle', p => { p.options[0].subtitle += 'x'; }],
    ['513-character card subtitle', p => { p.subtitle += 'x'; }],
    ['513-character answered title', p => { p.reply_message.title += 'x'; }],
    ['HTTP image', p => { p.options[0].image_url = 'http://example.com/row.png'; }],
    ['raw space in image URI', p => { p.options[0].image_url = 'https://example.com/a b.png'; }],
    ['raw newline in image URI', p => { p.options[0].image_url = 'https://example.com/a\nb.png'; }],
    ['image over 2048', p => { p.options[0].image_url = 'https://example.com/' + 'x'.repeat(2048); }],
    ['11 sections', p => { delete p.options; p.sections = Array.from({length: 11}, (_, i) =>
      ({ title: `Section ${i}`, options: [{ id: `id-${i}`, label: 'Label' }] })); }],
    ['26 flat options', p => { p.options = Array.from({length: 26}, (_, i) => ({id:`id-${i}`,label:'Label'})); }],
  ];
  for (const [name, mutate] of invalidPrompts) {
    const changed = clone(flat); mutate(changed);
    assert.equal(prompt(changed), false, `contract must reject ${name}`);
  }
  valid(reply, { type: 'selection_response', selected_values: ['x'.repeat(200)],
    selected_ids: ['x'.repeat(200)] }, '200-character reply IDs');
  assert.equal(reply({ type: 'selection_response', selected_ids: ['x'] }), false,
    'selected_ids cannot replace required selected_values');
  assert.equal(reply({ type: 'selection_response', selected_values: ['x'],
    reply_message: { title: 'Forged' } }), false, 'client cannot supply answered copy');
}

async function mutations() {
  const cases = [
    ['default-flipped', files[1], '`multiple` defaults to `true`', '`multiple` defaults to `false`'],
    ['limit-drift', files[1], '1 to 200', '1 to 201'],
    ['required-values-removed', files[1], '`selected_values` is required', '`selected_values` is optional'],
    ['reply-ownership-removed', files[1], 'copies `reply_message` from the source', 'uses client reply copy'],
    ['invented-subtitle-minimum', files[1], '0 to 72', '1 to 72'],
    ['blank-subtitle-rule-removed', files[1], 'blank after trimming is stored as absent', 'may be empty'],
    ['older-app-note-removed', files[0], 'ignore `multiple: false`', 'honor `multiple: false`'],
    ['navigation-removed', 'docs.json', '"interactions/selection-reference"', '"interactions/removed"'],
    ['typescript-example-drift', files[0], 'id: "express"', 'id: "different"'],
    ['python-example-drift', files[0], '"multiple": False', '"multiple": True'],
    ['answer-id-order-drift', files[0], '"selected_ids":["research","design"]',
      '"selected_ids":["design","research"]'],
    ['contract-default-drift', files[4], 'default: true', 'default: false', true],
    ['contract-uri-format-removed', files[4], 'format: uri', '', true],
  ];
  for (const [name, path, before, after, schemaOnly] of cases) {
    const dir = mkdtempSync(join(tmpdir(), 'relay-list-picker-mutation-'));
    try {
      for (const file of files) {
        mkdirSync(dirname(join(dir, file)), { recursive: true });
        let source = read(ROOT, file);
        if (file === path) {
          if (schemaOnly) {
            const spec = YAML.parse(source);
            if (name === 'contract-default-drift') {
              spec.components.schemas.SelectionPart.properties.multiple.default = false;
            } else {
              delete spec.components.schemas.SelectionOption.properties.image_url.format;
            }
            source = YAML.stringify(spec);
          } else {
            assert.ok(source.includes(before), `mutation target missing: ${name}`);
            source = source.replace(before, after);
          }
        }
        writeFileSync(join(dir, file), source);
      }
      await assert.rejects(() => checkDocs(dir), undefined, `survived: ${name}`);
      console.log(`KILLED ${name}`);
    } finally { rmSync(dir, { recursive: true, force: true }); }
  }
}

await checkDocs(ROOT);
console.log('PASS list-picker docs, example parity, canonical schema and boundaries');
if (process.argv.includes('--mutations')) await mutations();
