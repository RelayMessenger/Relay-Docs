#!/usr/bin/env python3
"""CLI-specific checks for the source-generated .37 help projection."""
import json
import os
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "node_modules/relaymessenger/dist/cli.js"
EXPECTED = "0.1.6-staging.37"


def captured(text):
    match = re.search(r"^```text captured-output\n(.*?)^```", text, re.M | re.S)
    if not match:
        raise AssertionError("missing captured help block")
    return match.group(1)


class CLIReferenceTests(unittest.TestCase):
    def test_exact_package_pin(self):
        package = json.loads((ROOT / "package.json").read_text())
        lock = json.loads((ROOT / "package-lock.json").read_text())
        self.assertEqual(package["devDependencies"]["relaymessenger"], EXPECTED)
        self.assertEqual(lock["packages"]["node_modules/relaymessenger"]["version"], EXPECTED)

    def test_root_help_is_real_braille_sections_without_options(self):
        result = subprocess.run(
            ["node", str(CLI), "--agent", "no", "--help"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            env={**os.environ, "NO_COLOR": "1", "FORCE_COLOR": "0"},
        )
        actual = result.stdout.replace("\r\n", "\n").rstrip()
        generated = captured((ROOT / "cli/reference/index.mdx").read_text()).rstrip()
        self.assertEqual(generated, actual)
        for heading in ("VERSION", "USAGE", "TOPICS", "COMMANDS"):
            self.assertIn(f"\n{heading}\n", actual)
        self.assertNotRegex(actual, r"(?m)^Options:\s*$")
        self.assertIn("⢀", actual)

    def test_overview_has_one_source_generated_full_tree(self):
        text = (ROOT / "cli/index.mdx").read_text()
        self.assertEqual(len(re.findall(r"^```text command-tree$", text, re.M)), 1)
        tree = re.search(r"^```text command-tree\n(.*?)^```", text, re.M | re.S).group(1)
        root_help = captured((ROOT / "cli/reference/index.mdx").read_text())
        root_commands = re.findall(r"^  ([a-z][a-z-]*)\s{2,}", root_help, re.M)
        for name in root_commands:
            self.assertRegex(tree, rf"[├└]── {re.escape(name)}(?:\s|$)")
        for name in ("chats", "messages", "attachments", "blocked-handles", "webhooks", "contact-card", "profiles", "listen", "login", "whoami", "logout"):
            self.assertRegex(tree, rf"[├└]── {re.escape(name)}(?:\s|$)")

    def test_generated_pages_are_owned_once_by_cli_commands_group(self):
        config = json.loads((ROOT / "docs.json").read_text())
        cli = next(tab for tab in config["navigation"]["tabs"] if tab["tab"] == "CLI")
        command_group = next(group for group in cli["groups"] if group["group"] == "Commands")
        generated = sorted(str(path.relative_to(ROOT).with_suffix("")) for path in (ROOT / "cli/reference").glob("*.mdx"))
        self.assertEqual(sorted(page for page in command_group["pages"] if page.startswith("cli/reference/")), generated)
        all_pages = [page for group in cli["groups"] for page in group["pages"]]
        for page in generated:
            self.assertEqual(all_pages.count(page), 1, page)


if __name__ == "__main__":
    unittest.main()
