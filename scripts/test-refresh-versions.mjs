import assert from "node:assert/strict";
import { test } from "node:test";
import { refreshHostedLock, refreshSourcePaths } from "./refresh-versions.mjs";

function fixture() {
  return {
    lock: {
      npm: { packageA: {}, legacyCLI: {} },
      repositories: { SDK: { paths: ["a"] }, Hermes: { paths: [] } },
    },
    next: {
      npm: {
        packageA: { latest: "1.0.0", staging: "1.1.0-staging.1",
          integrity: { "1.0.0": "one", "1.1.0-staging.1": "two" } },
        legacyCLI: { latest: "2.0.0", staging: "2.1.0-staging.1",
          integrity: { "2.0.0": "three", "2.1.0-staging.1": "four" } },
      },
    },
    heads: { SDK: "a".repeat(40), Hermes: "b".repeat(40) },
  };
}

test("refresh covers every locked repository, package tag, and integrity", () => {
  const { lock, next, heads } = fixture();
  const updated = refreshHostedLock(lock, next, heads);
  for (const name of Object.keys(next.npm)) {
    assert.deepEqual(updated.npm[name].tags, {
      latest: next.npm[name].latest, staging: next.npm[name].staging,
    });
    assert.deepEqual(updated.npm[name].integrity, next.npm[name].integrity);
  }
  assert.equal(updated.repositories.Hermes.commit, heads.Hermes);
  assert.equal(updated.repositories.SDK.commit, heads.SDK);
  assert.deepEqual(updated.repositories.SDK.paths, ["a"]);
});

test("an unobserved legacy package cannot silently retain stale metadata", () => {
  const { lock, next, heads } = fixture();
  delete next.npm.legacyCLI;
  assert.throws(() => refreshHostedLock(lock, next, heads), /legacyCLI/);
});

test("an unobserved repository cannot silently retain a release-era pin", () => {
  const { lock, next, heads } = fixture();
  delete heads.Hermes;
  assert.throws(() => refreshHostedLock(lock, next, heads), /Hermes/);
});

test("metadata-only refresh selects no published source files", () => {
  assert.deepEqual(refreshSourcePaths(true), []);
  assert.ok(refreshSourcePaths(false).some((file) => file.endsWith("/index.mdx")));
});
