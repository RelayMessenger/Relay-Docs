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

// `latest` and `staging` may select different versions. Relay-SDK publishes
// every merge to the `staging` tag and the owner promotes `latest` separately,
// so the lock records one version and one integrity per tag.
for (const [packageName, expected] of Object.entries(lock.npm)) {
  const metadata = await json(
    `https://registry.npmjs.org/${encodeURIComponent(packageName)}`,
  );
  assert.ok(expected.tags.latest, `${packageName} lock has no latest tag`);
  assert.ok(expected.tags.staging, `${packageName} lock has no staging tag`);

  for (const [tag, version] of Object.entries(expected.tags)) {
    assert.equal(
      metadata["dist-tags"]?.[tag],
      version,
      `${packageName}@${tag} drifted`,
    );
    assert.ok(metadata.versions?.[version], `${packageName}@${version} is absent`);
    assert.ok(
      expected.integrity[version],
      `${packageName}@${version} has no locked integrity`,
    );
    assert.equal(
      metadata.versions[version].dist?.integrity,
      expected.integrity[version],
      `${packageName}@${version} integrity drifted`,
    );
  }
}

const lockedTagCount = Object.values(lock.npm).reduce(
  (total, entry) => total + Object.keys(entry.tags).length,
  0,
);

console.log(
  `verified ${Object.keys(lock.repositories).length} hosted staging repositories, `
    + `${lockedPathCount} canonical paths, and `
    + `${lockedTagCount} live npm tag identities across `
    + `${Object.keys(lock.npm).length} packages`,
);
