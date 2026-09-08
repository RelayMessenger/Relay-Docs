#!/usr/bin/env node
// Read only the two approved registry releases. No package publication or tag writes.
import { readFile, writeFile } from 'node:fs/promises';
const root = new URL('../', import.meta.url);
const requested = [
  ['relaymessenger', '0.1.0-staging.0', '0.0.0', 'sha512-S4+2VC+SABQQ0g7jnvYjllaUCtAvuL9jtXdZPbiSkiHuVaa6t7jp/NPwypXz4orHAkLS4Sn/KJioSVKjaEWsuA=='],
  ['@relaymessenger/sdk', '0.3.1-staging.1', '0.3.0', 'sha512-wqg+3Cio8rxbRrqagknXKf7MChGwVEhQQJxXwSbl4H9gH42OkzhsAIZHBeCbsid+fB6uVZv5cF+JX5lghYxe2A=='],
];
const versions = JSON.parse(await readFile(new URL('versions.json', root), 'utf8'));
const lock = JSON.parse(await readFile(new URL('scripts/ecosystem-hosted-lock.json', root), 'utf8'));
for (const [name, stage, latest, integrity] of requested) {
  const response = await fetch(`https://registry.npmjs.org/${encodeURIComponent(name)}`);
  if (!response.ok) throw new Error(`${name}: registry HTTP ${response.status}`);
  const metadata = await response.json();
  if (metadata['dist-tags'].staging !== stage || metadata['dist-tags'].latest !== latest || metadata.versions[stage]?.dist?.integrity !== integrity) {
    throw new Error(`${name}: registry no longer matches the approved release receipt`);
  }
  const hashes = { ...(versions.npm[name]?.integrity ?? {}) };
  for (const version of [stage, latest]) {
    const value = metadata.versions[version]?.dist?.integrity;
    if (!value) throw new Error(`${name}@${version}: missing integrity`);
    hashes[version] = value;
  }
  // gitHead is absent in the approved releases; do not infer npm provenance.
  versions.npm[name] = { latest, staging: stage, integrity: hashes, sourceCommit: versions.npm[name]?.sourceCommit ?? null };
  lock.npm[name] = { tags: { latest, staging: stage }, integrity: hashes };
  console.log(`${name}@${stage}: registry tag and integrity verified; latest remains ${latest}`);
}
versions.checked = new Date().toISOString().slice(0, 10);
await writeFile(new URL('versions.json', root), JSON.stringify(versions, null, 2) + '\n');
await writeFile(new URL('scripts/ecosystem-hosted-lock.json', root), JSON.stringify(lock, null, 2) + '\n');
