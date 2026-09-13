#!/usr/bin/env python3
"""CLI-specific checks for the source-generated staging help projection."""
import json
import os
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "node_modules/relaymessenger/dist/cli.js"
EXPECTED = "0.1.6-staging.40"


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
        for heading in ("VERSION", "USAGE", "TOPICS", "COMMANDS"):
            self.assertIn(f"\n{heading}\n", actual)
        self.assertNotRegex(actual, r"(?m)^Options:\s*$")
        self.assertIn("⢀", actual)

    def test_overview_has_one_source_generated_full_tree(self):
        text = (ROOT / "cli/index.mdx").read_text()
        self.assertEqual(len(re.findall(r"^```text command-tree$", text, re.M)), 1)
        tree = re.search(r"^```text command-tree\n(.*?)^```", text, re.M | re.S).group(1)
        root_help = subprocess.check_output(["node", str(CLI), "--agent", "no", "--help"], text=True)
        root_commands = re.findall(r"^  ([a-z][a-z-]*)\s{2,}", root_help, re.M)
        for name in root_commands:
            self.assertRegex(tree, rf"[├└]── {re.escape(name)}(?:\s|$)")
        for name in ("chats", "messages", "attachments", "blocked-handles", "webhooks", "contact-card", "profiles", "listen", "login", "whoami", "logout"):
            self.assertRegex(tree, rf"[├└]── {re.escape(name)}(?:\s|$)")

    def test_approved_task_tree_and_page_anatomy(self):
        spec = json.loads((ROOT / "scripts/cli-tree-spec.json").read_text())
        config = json.loads((ROOT / "docs.json").read_text())
        cli = next(tab for tab in config["navigation"]["tabs"] if tab["tab"] == "CLI")
        self.assertEqual(cli["groups"], spec["groups"])
        def flatten(items):
            for item in items:
                if isinstance(item, str):
                    yield item
                else:
                    yield from flatten(item["pages"])
        all_pages = list(flatten(cli["groups"]))
        self.assertEqual(set(all_pages), set(spec["pages"]))
        self.assertEqual(len(all_pages), len(set(all_pages)))
        generated = {str(path.relative_to(ROOT).with_suffix("")) for path in (ROOT / "cli/reference").glob("*.mdx")}
        self.assertEqual(generated, {page for page in all_pages if page.startswith("cli/reference/")})
        for page, expected in spec["pages"].items():
            text = (ROOT / (page + ".mdx")).read_text()
            self.assertIn('title: ' + json.dumps(expected["title"]) + '\n', text, page)
            if "sidebarTitle" in expected:
                self.assertIn('sidebarTitle: ' + json.dumps(expected["sidebarTitle"]), text)
            if "command" in expected:
                self.assertEqual(re.search(r"^```bash\n(.*?)^```", text, re.M | re.S).group(1).strip(), "npx " + expected["command"])
                self.assertLess(text.index("```bash"), text.index("## Usage"))
                self.assertNotIn("## Output", text)
                # Three links: the family's concept guide (a page that exists), then the two CLI pages.
                steps = text.split("## Next steps\n\n")[1]
                guide = re.match(r"- \[[^\]]+\]\((/[^)]+)\)\n", steps)
                self.assertIsNotNone(guide, page)
                target = guide.group(1).lstrip("/")
                self.assertTrue((ROOT / (target + ".mdx")).exists() or (ROOT / target / "index.mdx").exists(), guide.group(1))
                self.assertEqual(steps[guide.end():], "- [CLI](/cli/index)\n- [Global options](/cli/global-options)\n")
        for page in spec["dropped_generated_pages"]:
            self.assertFalse((ROOT / (page + ".mdx")).exists(), page)


if __name__ == "__main__":
    unittest.main()
