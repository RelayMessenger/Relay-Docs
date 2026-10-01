#!/usr/bin/env python3
"""Every code snippet on a cookbook-backed integration page is real recipe code.

Each ```ts or ```python block must appear, line for line (indentation may be
shifted as a whole, blank lines kept), in a source file of the recipes the
page documents. Run against a Relay-SDK checkout at the branch the page
links (`source_ref()`):

    RELAY_SDK_DIR=/path/to/Relay-SDK python3 scripts/test-cookbook-snippets.py

Without RELAY_SDK_DIR the test is skipped: this repository's checks run
offline.
"""

import os
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FENCE = re.compile(r"^```(ts|typescript|python)[^\n]*\n(.*?)^```[ \t]*$", re.M | re.S)
PAGES = {
    "integrations/xai-grok.mdx": ("cookbook/grok-voice-agent", "cookbook/grok-imagine-agent"),
    "integrations/elevenlabs.mdx": ("cookbook/elevenlabs-voice-agent", "cookbook/elevenlabs-agents-call"),
}
SUFFIXES = {".ts", ".py"}


def indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def contains(source: list[str], block: list[str]) -> bool:
    first = next(index for index, line in enumerate(block) if line.strip())
    for start in range(len(source) - len(block) + 1):
        anchor = source[start + first]
        if anchor.strip() != block[first].strip():
            continue
        shift = indent(anchor) - indent(block[first])
        if all(
            (not want.strip() and not have.strip()) or have == " " * shift + want
            for want, have in zip(block, source[start:start + len(block)])
        ):
            return True
    return False


def snippets(page: str) -> list[list[str]]:
    text = (ROOT / page).read_text()
    return [match.group(2).rstrip("\n").split("\n") for match in FENCE.finditer(text)]


@unittest.skipUnless(os.environ.get("RELAY_SDK_DIR"), "set RELAY_SDK_DIR to a Relay-SDK checkout")
class CookbookSnippets(unittest.TestCase):
    def test_every_snippet_is_recipe_code(self) -> None:
        sdk = Path(os.environ["RELAY_SDK_DIR"])
        for page, recipes in PAGES.items():
            sources = [
                path.read_text().split("\n")
                for recipe in recipes
                for path in sorted((sdk / recipe).rglob("*"))
                if path.suffix in SUFFIXES and "node_modules" not in path.parts and ".venv" not in path.parts
            ]
            self.assertTrue(sources, f"{page}: no recipe source under {recipes}")
            blocks = snippets(page)
            self.assertTrue(blocks, f"{page}: no code snippets")
            for number, block in enumerate(blocks, 1):
                with self.subTest(page=page, snippet=number, first=block[0]):
                    self.assertTrue(any(contains(source, block) for source in sources))


if __name__ == "__main__":
    unittest.main()
