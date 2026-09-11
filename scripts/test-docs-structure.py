#!/usr/bin/env python3
"""Mutation tests for reader-facing boundaries, independent of exact prose."""
import json
import tempfile
import unittest
from pathlib import Path
from docs_structure import (LANDING_SECTIONS, OVERVIEW_PAGES, START_PAGES,
                            validate_structure, validate_build_headings)

ROOT = Path(__file__).resolve().parents[1]


class DocumentationStructureTests(unittest.TestCase):
    def fixture(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        for page in START_PAGES:
            path = root / f"{page}.mdx"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("---\ntitle: Test\n---\nOne task.\n\n## Next steps\n")
        (root / "index.mdx").write_text("\n".join("## " + heading for heading in LANDING_SECTIONS) + "\n")
        config = {"navigation": {"tabs": [{"groups": [
            {"group": "Overview", "pages": list(OVERVIEW_PAGES)},
            {"group": "Getting started", "pages": list(START_PAGES)},
        ]}]}}
        return root, config

    def test_landing_order_mutation(self):
        root, config = self.fixture()
        path = root / "index.mdx"
        path.write_text(path.read_text().replace("## Receive events", "## Another section"))
        with self.assertRaisesRegex(SystemExit, "approved order"):
            validate_structure(root, config)

    def test_build_heading_mutation(self):
        with self.assertRaisesRegex(SystemExit, "imperative task"):
            validate_build_headings("messages/send", "## Background\n## Next steps\n")

    def test_event_heading_mutation(self):
        with self.assertRaisesRegex(SystemExit, "imperative task"):
            validate_build_headings("events/message-sent", "## Fields\n## Next steps\n")

    def test_current_site(self):
        validate_structure(ROOT, json.loads((ROOT / "docs.json").read_text()))

    def test_onboarding_cannot_absorb_management(self):
        root, config = self.fixture()
        config["navigation"]["tabs"][0]["groups"][1]["pages"].append("agents/lifecycle")
        with self.assertRaisesRegex(SystemExit, "Getting started"):
            validate_structure(root, config)

    def test_independent_sections_fail(self):
        root, config = self.fixture()
        path = root / f"{START_PAGES[2]}.mdx"
        path.write_text(path.read_text() + "\n".join(f"## Task {i}" for i in range(9)))
        with self.assertRaisesRegex(SystemExit, "split independent tasks"):
            validate_structure(root, config)

    def test_internal_release_notes_fail(self):
        root, config = self.fixture()
        path = root / f"{START_PAGES[2]}.mdx"
        path.write_text(path.read_text() + "\n## Prepare hosted proof\n")
        with self.assertRaisesRegex(SystemExit, "internal publishing"):
            validate_structure(root, config)

    def test_full_prompt_cannot_return_to_onboarding(self):
        root, config = self.fixture()
        path = root / f"{START_PAGES[0]}.mdx"
        path.write_text(path.read_text() + "\n````text Relay agent prompt\nInstructions\n````\n")
        with self.assertRaisesRegex(SystemExit, "machine instructions"):
            validate_structure(root, config)

    def test_code_headings_do_not_count_as_page_sections(self):
        root, config = self.fixture()
        path = root / f"{START_PAGES[2]}.mdx"
        path.write_text(path.read_text() + "\n```text\n" + "\n".join(f"## Example {i}" for i in range(10)) + "\n```\n")
        validate_structure(root, config)

    def test_orphan_and_duplicate_pages_fail(self):
        root, config = self.fixture()
        (root / "orphan.mdx").write_text("Missing navigation")
        with self.assertRaisesRegex(SystemExit, "navigation owner"):
            validate_structure(root, config)


if __name__ == "__main__":
    unittest.main()
