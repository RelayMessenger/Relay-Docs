import assert from 'node:assert/strict';
import { execFileSync, spawnSync } from 'node:child_process';
import { mkdtempSync, mkdirSync, readFileSync, writeFileSync, rmSync, existsSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { test } from 'node:test';
import YAML from 'yaml';

const root = resolve(import.meta.dirname, '..');
const runner = join(root, 'scripts/ci-checks.py');
function fixture(t) {
  const dir = mkdtempSync(join(tmpdir(), 'docs-ci-'));
  t.after(() => rmSync(dir, { recursive: true, force: true }));
  const git = (...args) => execFileSync('git', args, { cwd: dir, encoding: 'utf8' }).trim();
  git('init', '-q');
  git('config', 'user.email', 'ci@example.invalid');
  git('config', 'user.name', 'CI test');
  mkdirSync(join(dir, 'scripts'));
  writeFileSync(join(dir, 'scripts/test-hosted-cache.py'), 'before\n');
  git('add', '.'); git('commit', '-qm', 'base');
  const base = git('rev-parse', 'HEAD');
  return { dir, git, base, change(path, value = 'changed\n') {
    mkdirSync(resolve(dir, path, '..'), { recursive: true });
    writeFileSync(join(dir, path), value);
    git('add', '.'); git('commit', '-qm', 'change');
  }, run(env = {}, args = []) {
    return spawnSync('python3', [runner, ...args], { cwd: dir, encoding: 'utf8',
      env: { ...process.env, GITHUB_EVENT_NAME: 'pull_request', CI_BASE_SHA: base, GITHUB_OUTPUT: '', ...env } });
  } };
}
function plan(f, env = {}) {
  const result = f.run(env);
  assert.equal(result.status, 0, result.stderr);
  return JSON.parse(result.stdout);
}

test('isolated tests select their executable owner once; mixed and unknown changes fall back', t => {
  const f = fixture(t);
  f.change('scripts/test-hosted-cache.py');
  f.change('scripts/test-hosted-environments.py');
  assert.deepEqual(plan(f).checks, ['check:hosted-cache']);
  for (const path of ['package-lock.json', 'docs.json', '.github/workflows/ci.yml', 'scripts/hosted_cache.py', '.github/ISSUE_TEMPLATE/package.json']) {
    const changed = fixture(t);
    changed.change(path);
    assert.deepEqual(plan(changed).checks, ['validate'], path);
  }
  f.change('new-tool.py');
  assert.deepEqual(plan(f).checks, ['validate']);
});

test('published Markdown is product; only GitHub templates can skip checks', t => {
  const f = fixture(t);
  f.change('.github/PULL_REQUEST_TEMPLATE.md');
  assert.equal(plan(f).mode, 'notes');
  f.change('skill.md');
  assert.equal(plan(f).mode, 'full');
});

test('protected pushes, dispatch, merge groups, empty and missing diffs always run full', t => {
  const f = fixture(t);
  assert.deepEqual(plan(f).checks, ['validate']);
  f.change('.github/PULL_REQUEST_TEMPLATE.md');
  for (const GITHUB_EVENT_NAME of ['push', 'workflow_dispatch', 'merge_group']) {
    assert.deepEqual(plan(f, { GITHUB_EVENT_NAME }).checks, ['validate']);
  }
  for (const CI_BASE_SHA of ['', 'missing-ref']) {
    assert.deepEqual(plan(f, { CI_BASE_SHA }).checks, ['validate']);
  }
});

test('renames and deletions include their old inputs, not just their destination', t => {
  const f = fixture(t);
  f.change('skill.md');
  const base = f.git('rev-parse', 'HEAD');
  mkdirSync(join(f.dir, '.github'));
  f.git('mv', 'skill.md', '.github/PULL_REQUEST_TEMPLATE.md');
  f.git('commit', '-qm', 'rename');
  assert.deepEqual(plan(f, { CI_BASE_SHA: base }).checks, ['validate']);
  const deleted = fixture(t);
  deleted.git('rm', 'scripts/test-hosted-cache.py');
  deleted.git('commit', '-qm', 'delete');
  assert.equal(plan(deleted).mode, 'full');
});

test('PR selection uses merge-base, not unrelated base-branch changes', t => {
  const f = fixture(t);
  f.git('checkout', '-qb', 'base-new');
  f.change('skill.md');
  const advanced = f.git('rev-parse', 'HEAD');
  f.git('checkout', '-qb', 'feature', f.base);
  f.change('scripts/test-hosted-cache.py');
  assert.deepEqual(plan(f, { CI_BASE_SHA: advanced }).checks, ['check:hosted-cache']);
});

test('selected checks really execute, fail closed, and notes execute nothing', t => {
  const f = fixture(t);
  const bin = mkdtempSync(join(tmpdir(), 'docs-ci-bin-'));
  t.after(() => rmSync(bin, { recursive: true, force: true }));
  const log = join(bin, 'calls');
  writeFileSync(join(bin, 'npm'), '#!/bin/sh\nprintf "%s\\n" "$*" >> "$CALLS"\nexit "${RESULT:-0}"\n', { mode: 0o755 });
  const env = { PATH: `${bin}:${process.env.PATH}`, CALLS: log };
  f.change('.github/PULL_REQUEST_TEMPLATE.md');
  assert.equal(f.run(env, ['--run']).status, 0);
  assert.equal(existsSync(log), false);
  f.change('scripts/test-hosted-cache.py');
  assert.equal(f.run({ ...env, RESULT: '17' }, ['--run']).status, 17);
  assert.equal(readFileSync(log, 'utf8'), 'run check:hosted-cache\n');
  assert.equal(f.run(env, ['--run']).status, 0);
});

const workflow = () => YAML.parse(readFileSync(join(root, '.github/workflows/validate.yml'), 'utf8'));
function evaluate(value, github) {
  if (typeof value !== 'string') return value;
  const expression = value.trim().replace(/^\$\{\{\s*|\s*\}\}$/g, '');
  return Function('github', 'format', `return (${expression});`)(github,
    (template, ...args) => template.replace(/\{(\d+)\}/g, (_, index) => args[index]));
}

test('all protected pushes trigger; only superseded PRs share a cancellable group', () => {
  const w = workflow();
  assert.deepEqual(w.on.push.branches.toSorted(), ['main', 'staging']);
  assert.equal(w.on.push.paths, undefined);
  assert.equal(w.on.push['paths-ignore'], undefined);
  assert.equal(w.on.pull_request?.paths, undefined);
  assert.equal(w.on.pull_request?.['paths-ignore'], undefined);
  const context = (event_name, run_id, ref = 'refs/heads/staging') => ({
    event_name, run_id, ref, workflow: 'Validate docs', event: { pull_request: { number: 278 } },
  });
  const group = g => evaluate(w.concurrency.group, g);
  const cancel = g => evaluate(w.concurrency['cancel-in-progress'], g);
  for (const ref of ['refs/heads/staging', 'refs/heads/main']) {
    assert.notEqual(group(context('push', 1, ref)), group(context('push', 2, ref)));
    assert.equal(cancel(context('push', 1, ref)), false);
  }
  assert.equal(group(context('pull_request', 1)), group(context('pull_request', 2)));
  assert.equal(cancel(context('pull_request', 1)), true);
});

test('workflow executes the selected gate once and propagates its failure', t => {
  const f = fixture(t);
  f.change('scripts/test-hosted-cache.py');
  // Exercise the workflow command in an isolated checkout, not a copy of its
  // selection logic. npm is only an external process/status recorder.
  writeFileSync(join(f.dir, 'scripts/ci-checks.py'), readFileSync(runner));
  const bin = mkdtempSync(join(tmpdir(), 'docs-ci-workflow-'));
  t.after(() => rmSync(bin, { recursive: true, force: true }));
  const log = join(bin, 'calls');
  writeFileSync(join(bin, 'npm'), '#!/bin/sh\necho "$*" >> "$CALLS"\nexit "${RESULT:-0}"\n', { mode: 0o755 });
  const step = workflow().jobs.validate.steps.find(s => s.name === 'Run full or affected validation');
  for (const [event, mode, check] of [
    ['push', 'full', 'validate'], ['pull_request', 'affected', 'check:hosted-cache'],
  ]) {
    const steps = { affected: { outputs: { mode } } };
    assert.equal(Function('steps', `return (${step.if});`)(steps), true);
    for (const status of [0, 17]) {
      writeFileSync(log, '');
      const result = spawnSync('bash', ['-e', '-o', 'pipefail', '-c', step.run], {
        cwd: f.dir, encoding: 'utf8', env: { ...process.env, PATH: `${bin}:${process.env.PATH}`,
          GITHUB_EVENT_NAME: event, CI_BASE_SHA: f.base, GITHUB_OUTPUT: '', CALLS: log, RESULT: String(status) },
      });
      assert.equal(result.status, status, result.stderr);
      assert.equal(readFileSync(log, 'utf8'), `run ${check}\n`);
    }
  }
  assert.equal(Function('steps', `return (${step.if});`)({ affected: { outputs: { mode: 'notes' } } }), false);
});
