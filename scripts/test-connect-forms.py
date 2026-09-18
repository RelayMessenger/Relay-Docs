#!/usr/bin/env python3
"""Owner ruling 2026-09-18: two connect forms only, and @staging on every CLI line.

General pages show `npx relaymessenger@staging connect` and nothing after it;
only a provider's own page under integrations/ shows its direct command.
Main is derived: scripts/origins.py rewrites `relaymessenger@staging` to bare
`relaymessenger`, so staging source never carries the bare or pinned form.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {"node_modules", "_worktrees", ".git"}
PROVIDERS = ("claude-code", "codex", "cursor", "cline", "hermes",
             "openclaw", "opencode", "pi", "gemini-cli", "vs-code")
PROVIDER_PAGES = {ROOT / f"integrations/{name}.mdx" for name in PROVIDERS}
PROVIDER_ALT = "|".join(re.escape(name) for name in PROVIDERS)
COMMAND_LINE = re.compile(r"^(?:npx relaymessenger|npm install --global relaymessenger)\b", re.M)
FORBIDDEN = re.compile(rf"\bconnect (?:{PROVIDER_ALT})\b|RUNTIME=")
PROVIDER_LINK = re.compile(rf"/integrations/(?:{PROVIDER_ALT})\b")
# The integrations index is the one general page that lists the providers (a card each).
CARD_INDEX = ROOT / "integrations/index.mdx"


def pages():
    for path in sorted(ROOT.rglob("*.mdx")):
        if SKIP_DIRS & set(path.relative_to(ROOT).parts):
            continue
        yield path


class ConnectFormsTests(unittest.TestCase):
    def test_every_cli_line_names_the_staging_tag(self):
        offending = []
        for path in pages():
            for number, line in enumerate(path.read_text().splitlines(), 1):
                if COMMAND_LINE.match(line) and "relaymessenger@staging" not in line:
                    offending.append(f"{path.relative_to(ROOT)}:{number}: {line}")
        self.assertEqual(offending, [], "CLI lines without relaymessenger@staging")

    def test_general_pages_never_name_a_provider_runtime(self):
        offending = []
        for path in pages():
            if path in PROVIDER_PAGES or path == ROOT / "changelog.mdx":
                continue
            for number, line in enumerate(path.read_text().splitlines(), 1):
                if FORBIDDEN.search(line) or (path != CARD_INDEX and PROVIDER_LINK.search(line)):
                    offending.append(f"{path.relative_to(ROOT)}:{number}: {line}")
        self.assertEqual(offending, [], "General pages must not name a provider runtime")


if __name__ == "__main__":
    unittest.main()
