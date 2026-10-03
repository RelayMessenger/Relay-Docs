#!/usr/bin/env python3
"""Production docs never say "staging".

A reader of docs.relayapp.im builds against production: the App Store app only
reaches production agents. On 2026-10-03 a MHacks student followed "A staging
agent" on a production page, made his agent on staging, and the Relay app could
never reach it. The origin and package sweeps catch hosts and tags; this check
catches the word itself in every file Mintlify publishes, and in the generated
llms files, once the tree is derived for production.

In production mode (`.docs-target` is `production`) it scans this tree. In
staging mode it copies the authored tree, derives production there, regenerates
the llms files and the PostHog client, and scans the copy, so a staging-only
phrase fails the staging pull request before it can be promoted.

ALLOWLIST is deliberately empty. Wording that needs to name staging belongs in a
file Mintlify does not publish (.mintignore) or under scripts/ and .github/.
"""
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from origins import CONTENT_SUFFIXES, ROOT, target

WORD = re.compile(r"staging", re.I)
ALLOWLIST: frozenset[str] = frozenset()
SKIP_DIRS = {".git", "node_modules", ".mint", "scripts", ".github", "_worktrees", ".context"}
# Build inputs, not published pages: the CLI pin used to reproduce captured
# help and the registry observations. Mintlify serves none of them.
SKIP_FILES = {"versions.json", "package.json", "package-lock.json"}
REGENERATE = (
    ["python3", "scripts/docs_analytics.py"],
    ["python3", "scripts/build-llms.py"],
    ["python3", "scripts/build-agent-prompt.py"],
)


def unpublished(root: Path) -> set[str]:
    ignore = root / ".mintignore"
    if not ignore.is_file():
        return set()
    return {line.strip().rstrip("/") for line in ignore.read_text().splitlines() if line.strip() and not line.startswith("#")}


def published_files(root: Path):
    ignored = unpublished(root)
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if not path.is_file() or SKIP_DIRS & set(relative.parts):
            continue
        rel = relative.as_posix()
        if rel in SKIP_FILES or rel in ignored or relative.parts[0] in ignored:
            continue
        if path.suffix in CONTENT_SUFFIXES:
            yield rel, path


def findings(root: Path) -> list[str]:
    found = []
    for rel, path in published_files(root):
        for number, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
            if WORD.search(line) and f"{rel}:{number}" not in ALLOWLIST:
                found.append(f"{rel}:{number}: {line.strip()[:160]}")
    return found


def derived_copy() -> Path:
    copy = Path(tempfile.mkdtemp(prefix="production-wording-")) / "docs"
    files = subprocess.run(
        ["git", "ls-files", "-co", "--exclude-standard"], cwd=ROOT, check=True,
        capture_output=True, text=True,
    ).stdout.splitlines()
    for name in files:
        if name.startswith("_worktrees/") or not (ROOT / name).is_file():
            continue
        destination = copy / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, destination)
    subprocess.run(["python3", "scripts/derive-production.py", "--no-generate"], cwd=copy, check=True, capture_output=True)
    for command in REGENERATE:
        subprocess.run(command, cwd=copy, check=True, capture_output=True)
    return copy


class WordingTests(unittest.TestCase):
    def test_word_is_found_in_published_prose_and_ignored_in_tooling(self):
        root = Path(tempfile.mkdtemp(prefix="production-wording-test-"))
        (root / "guides").mkdir()
        (root / "scripts").mkdir()
        (root / "guides" / "page.mdx").write_text("- A staging agent, Agent Token.\n")
        (root / "guides" / "ok.mdx").write_text("- An agent, its Agent Token.\n")
        (root / "scripts" / "tool.py").write_text("STAGING = 1\n")
        (root / "NOTES.md").write_text("Publish staging first.\n")
        (root / ".mintignore").write_text("NOTES.md\n")
        self.assertEqual(findings(root), ["guides/page.mdx:1: - A staging agent, Agent Token."])

    def test_allowlist_is_empty(self):
        self.assertEqual(ALLOWLIST, frozenset())


def main() -> None:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(WordingTests)
    if not unittest.TextTestRunner().run(suite).wasSuccessful():
        sys.exit(1)
    if target() == "production":
        root = ROOT
    else:
        root = derived_copy()
    found = findings(root)
    if root != ROOT:
        shutil.rmtree(root.parent, ignore_errors=True)
    if found:
        sys.exit("The production docs say \"staging\":\n" + "\n".join(found))
    print("Production docs never say staging")


if __name__ == "__main__":
    main()
