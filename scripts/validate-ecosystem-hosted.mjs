import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const lock = JSON.parse(
  await readFile(new URL("./ecosystem-hosted-lock.json", import.meta.url)),
);

async function json(url) {
  const response = await fetch(url, {
    headers: {
      accept: "application/json",
      "user-agent": "Relay-Docs-Hosted-Ecosystem-Validator/1.0",
    },
    signal: AbortSignal.timeout(30_000),
  });
  assert.equal(response.status, 200, `${url} returned ${response.status}`);
  return response.json();
}

let lockedPathCount = 0;
for (const [repository, expected] of Object.entries(lock.repositories)) {
  assert.match(expected.commit, /^[0-9a-f]{40}$/);
  assert.ok(Array.isArray(expected.paths));

  const commit = await json(
    `https://api.github.com/repos/RelayMessenger/${repository}/commits/staging`,
  );
  assert.equal(
    commit.sha,
    expected.commit,
    `${repository} staging is not the documented exact source`,
  );

  if (expected.paths.length > 0) {
    const tree = await json(
      `https://api.github.com/repos/RelayMessenger/${repository}/git/trees/`
        + `${commit.commit.tree.sha}?recursive=1`,
    );
    assert.equal(tree.truncated, false, `${repository} tree response was truncated`);
    const hostedPaths = new Set(tree.tree.map((item) => item.path));
    for (const path of expected.paths) {
      assert.ok(
        hostedPaths.has(path),
        `${repository}@${expected.commit} is missing ${path}`,
      );
      lockedPathCount += 1;
    }
  }
}

for (const [packageName, expected] of Object.entries(lock.npm)) {
  const metadata = await json(
    `https://registry.npmjs.org/${encodeURIComponent(packageName)}`,
  );
  const versions = new Set(Object.values(expected.tags));
  assert.equal(versions.size, 1, `${packageName} live tags do not select one version`);

  for (const [tag, version] of Object.entries(expected.tags)) {
    assert.equal(
      metadata["dist-tags"]?.[tag],
      version,
      `${packageName}@${tag} drifted`,
    );
    assert.ok(metadata.versions?.[version], `${packageName}@${version} is absent`);
    assert.equal(
      metadata.versions[version].dist?.integrity,
      expected.integrity,
      `${packageName}@${version} integrity drifted`,
    );
  }
}

console.log(
  `verified ${Object.keys(lock.repositories).length} hosted staging repositories, `
    + `${lockedPathCount} canonical paths, and `
    + `${Object.keys(lock.npm).length} live npm latest/staging identities`,
);
