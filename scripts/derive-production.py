#!/usr/bin/env python3
"""Derive the production docs tree from the staging tree.

`staging` is the authored branch and speaks staging origins. `main` is generated:
this script rewrites every staging origin in the content to its production twin
(the table in scripts/origins.py), records `production` in `.docs-target`, then
regenerates the derived files the same way the repo does (presented OpenAPI,
Mintlify bundle, agent prompt, llms files). Running it on an already-derived
tree changes nothing.

Usage: python3 scripts/derive-production.py [--no-generate] [--test]
"""
import argparse
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from origins import ROOT, TARGET_FILE, production_text

# Pinned independently of scripts/origins.py so a host dropped from the table
# fails the test instead of silently leaving the table's own list shorter.
EXPECTED_REWRITES = {
    "docs.staging.relayapp.im": "docs.relayapp.im",
    "staging.relayapp.im/@example.dev": "go.relayapp.im/@example.dev",
    "api.staging.relayapp.im": "api.relayapp.im",
    "cdn.staging.relayapp.im": "cdn.relayapp.im",
    "console.staging.relayapp.im": "console.relayapp.im",
    "uploads.staging.relayapp.im": "uploads.relayapp.im",
    "relay-staging.mintlify.app": "relay.mintlify.app",
    "/favicon-staging.png": "/favicon.png",
}
# Package references (owner ruling 2026-09-07): plain name, never a staging
# dist-tag or prerelease; a bare version cell becomes the `latest` tag.
EXPECTED_PACKAGE_REWRITES = {
    "npm install @relaymessenger/sdk@staging": "npm install @relaymessenger/sdk",
    "npx relaymessenger@staging --help": "npx relaymessenger --help",
    "openclaw plugins install @relaymessenger/openclaw-plugin@staging":
        "openclaw plugins install @relaymessenger/openclaw-plugin",
    "`@relaymessenger/sdk@0.3.0-staging.8`": "`@relaymessenger/sdk`",
    "`relay-claude-channel@0.3.0-staging.4`": "`relay-claude-channel`",
    "| `@relaymessenger/sdk` | `0.3.0-staging.8` |": "| `@relaymessenger/sdk` | `latest` |",
    "/plugin marketplace add RelayMessenger/Relay-SDK@staging":
        "/plugin marketplace add RelayMessenger/Relay-SDK@main",
}

CONTENT_SUFFIXES = {".mdx", ".md", ".json", ".yaml", ".yml", ".txt", ".js", ".mjs", ".svg"}
SKIP_DIRS = {".git", "node_modules", ".mint", "scripts", ".github"}
# Immutable contract and registry observations are inputs, not content to derive.
SKIP_FILES = {"api-reference/openapi.yaml", "versions.json"}
GENERATORS = (
    ["python3", "scripts/build-staging-openapi.py"],
    ["scripts/build-mint-openapi.sh"],
    ["python3", "scripts/build-agent-prompt.py"],
    ["python3", "scripts/build-llms.py"],
)


def content_files(root: Path):
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if SKIP_DIRS & set(relative.parts) or not path.is_file():
            continue
        if relative.as_posix() in SKIP_FILES:
            continue
        if path.suffix in CONTENT_SUFFIXES:
            yield path


def rewrite_tree(root: Path) -> list[Path]:
    changed = []
    for path in content_files(root):
        before = path.read_text()
        after = production_text(before)
        if after != before:
            path.write_text(after)
            changed.append(path.relative_to(root))
    target_file = root / TARGET_FILE.name
    if not target_file.is_file() or target_file.read_text() != "production\n":
        target_file.write_text("production\n")
        changed.append(target_file.relative_to(root))
    return changed


def derive(generate: bool) -> None:
    changed = rewrite_tree(ROOT)
    for path in changed:
        print(f"rewrote {path}")
    if generate:
        for command in GENERATORS:
            subprocess.run(command, cwd=ROOT, check=True)
    print(f"derived production tree: {len(changed)} file(s) rewritten")


class DeriveTests(unittest.TestCase):
    def fixture(self) -> Path:
        root = Path(tempfile.mkdtemp(prefix="derive-production-"))
        (root / "guides").mkdir()
        return root

    def test_every_staging_origin_is_rewritten(self):
        root = self.fixture()
        page = root / "guides" / "page.mdx"
        page.write_text("\n".join(f"use {value}/x" for value in EXPECTED_REWRITES) + "\n")
        rewrite_tree(root)
        text = page.read_text()
        for staging_value, production_value in EXPECTED_REWRITES.items():
            with self.subTest(origin=staging_value):
                self.assertNotIn(staging_value, text)
                self.assertIn(production_value, text)
        self.assertEqual((root / ".docs-target").read_text(), "production\n")

    def test_every_staging_package_reference_is_rewritten(self):
        root = self.fixture()
        page = root / "guides" / "packages.mdx"
        page.write_text("\n".join(EXPECTED_PACKAGE_REWRITES) + "\n")
        rewrite_tree(root)
        self.assertEqual(
            page.read_text().splitlines(), list(EXPECTED_PACKAGE_REWRITES.values())
        )

    def test_rewrite_is_idempotent(self):
        root = self.fixture()
        (root / "guides" / "page.mdx").write_text("curl https://api.staging.relayapp.im/v1/chats\n")
        self.assertTrue(rewrite_tree(root))
        self.assertEqual(rewrite_tree(root), [])

    def test_tooling_and_unknown_suffixes_are_left_alone(self):
        root = self.fixture()
        (root / "scripts").mkdir()
        script = root / "scripts" / "tool.py"
        script.write_text('HOST = "api.staging.relayapp.im"\n')
        binary = root / "guides" / "image.png"
        binary.write_bytes(b"api.staging.relayapp.im")
        rewrite_tree(root)
        self.assertEqual(script.read_text(), 'HOST = "api.staging.relayapp.im"\n')
        self.assertEqual(binary.read_bytes(), b"api.staging.relayapp.im")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-generate", action="store_true", help="rewrite only; skip generators")
    parser.add_argument("--test", action="store_true", help="run the self-tests and exit")
    args = parser.parse_args()
    if args.test:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(DeriveTests)
        sys.exit(0 if unittest.TextTestRunner().run(suite).wasSuccessful() else 1)
    derive(generate=not args.no_generate)


if __name__ == "__main__":
    main()
