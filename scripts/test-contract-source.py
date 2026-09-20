#!/usr/bin/env python3
"""Pin the independently read Server input, not a checksum derived from Docs."""
import hashlib
import json
import os
import re
import tempfile
import unittest
from pathlib import Path

from origins import target
from contract_source import verify_contract_source

ROOT = Path(__file__).resolve().parents[1]
# Independently read canonical contract at the Server staging removal merge.
UPSTREAM_COMMIT = "eb83978b6b2c625da82471e4af16acad8de0e618"
UPSTREAM_STAGING_COMMIT = "eb83978b6b2c625da82471e4af16acad8de0e618"
UPSTREAM_SHA256 = "27698655d12500fb9cd2e10dbf1c94025fbc64c288df6151db673a7649877111"


class ContractSourceTests(unittest.TestCase):
    def test_selection_review_uses_production_facing_copy(self):
        overview = (ROOT / "interactive-components/index.mdx").read_text()
        self.assertIn('<Card title="Selection" href="/interactive-components/selection">', overview)
        pages = [
            ROOT / "interactive-components/index.mdx",
            ROOT / "interactive-components/selection.mdx",
            *(ROOT / "integrations").glob("*.mdx"),
        ]
        for page in pages:
            source = page.read_text().lower()
            self.assertNotIn("selection, coming soon", source)
            self.assertNotIn("candidate request", source)
            self.assertNotIn("interactive local preview", source)
        selection = (ROOT / "interactive-components/selection.mdx").read_text().lower()
        self.assertNotIn("coming soon", selection)
        self.assertNotIn("under local development", selection)

    def test_selection_guide_keeps_runtime_summary_brief(self):
        selection = (ROOT / "interactive-components/selection.mdx").read_text()
        self.assertNotIn("### Choose and submit", selection)
        self.assertNotIn("## Selection fields", selection)
        runtime = selection.split("## Send from a runtime\n", 1)[1].split("\n## ", 1)[0]
        self.assertLess(len(runtime.split()), 100)
        self.assertNotIn("\n|", runtime)
        self.assertNotIn("```", runtime)
        self.assertIn("/integrations/index", runtime)
        self.assertIn("selected_values", selection)
        self.assertIn("reply_to", selection)

    def test_message_parts_links_to_interactive_components(self):
        parts = (ROOT / "messages/parts.mdx").read_text()
        section = parts.split("## Add interactive components\n", 1)[1].split("\n## ", 1)[0]
        self.assertIn("[Interactive components](/interactive-components/index)", section)
        self.assertLess(len(section.split()), 60)
        self.assertNotIn("buttons", section.lower())
        self.assertNotIn("selections", section.lower())
        self.assertIn("`parts`", section)

    def test_canonical_bytes_equal_pinned_upstream(self):
        verify_contract_source(ROOT, UPSTREAM_SHA256)

    def test_local_candidate_rejects_modified_bytes_and_release_relabeling(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "scripts").mkdir()
            (root / "api-reference").mkdir()
            record = json.loads((ROOT / "scripts/local-contract-source.json").read_text())
            record_file = root / "scripts/local-contract-source.json"
            record_file.write_text(json.dumps(record))
            contract = root / "api-reference/openapi.yaml"
            original = (ROOT / "api-reference/openapi.yaml").read_bytes()
            contract.write_bytes(original)
            verify_contract_source(root, UPSTREAM_SHA256)
            contract.write_bytes(original + b"\n# unreviewed drift\n")
            with self.assertRaises(AssertionError):
                verify_contract_source(root, UPSTREAM_SHA256)
            contract.write_bytes(original)
            record["status"] = "published"
            record_file.write_text(json.dumps(record))
            with self.assertRaises(AssertionError):
                verify_contract_source(root, UPSTREAM_SHA256)

    def test_buttons_are_text_only_and_a_tap_is_the_label_as_text(self):
        canonical = (ROOT / "api-reference/openapi.yaml").read_text()
        items = canonical.split("    ButtonItem:\n", 1)[1].split("    ButtonsPart:\n", 1)[0]
        self.assertNotIn("image_url", items)
        self.assertNotIn("          id:", items)
        self.assertNotIn("button_reply", canonical)
        self.assertIn("The only reply it accepts is a tap", canonical)
        parts = (ROOT / "messages/parts.mdx").read_text()
        self.assertNotIn("button_reply", parts)
        self.assertIn("/interactive-components/index", parts)
        buttons = (ROOT / "interactive-components/buttons.mdx").read_text()
        self.assertNotIn("image_url", buttons)
        self.assertNotIn("button_reply", buttons)
        self.assertIn('"parts": [{"type":"text","value":"Jupiter"}]', buttons)
        for path in ("skill.md", ".mintlify/skills/relay/SKILL.md"):
            skill = (ROOT / path).read_text()
            self.assertIn("not ordinary replies or reactions", skill)
            self.assertNotIn("button_reply", skill)
        full = (ROOT / "llms-full.txt").read_text()
        self.assertNotIn("button_reply", full)

    def assert_buttons_previews_match_requests(self, source):
        requests = 0
        buttons_only = 0
        with_text = 0
        for group in re.findall(r"<Tabs\b[^>]*>(.*?)</Tabs>", source, re.S):
            tabs = dict(re.findall(r'<Tab title="([^"]+)">\s*(.*?)</Tab>', group, re.S))
            if "Request" not in tabs:
                continue
            requests += 1
            blocks = re.findall(r"```json\s*\n(.*?)```", tabs["Request"], re.S)
            self.assertEqual(len(blocks), 1, "Each request needs one JSON payload")
            parts = json.loads(blocks[0])["message"]["parts"]
            buttons = [part for part in parts if part["type"] == "buttons"]
            text = [part["value"] for part in parts if part["type"] == "text"]
            self.assertEqual(len(buttons), 1)
            self.assertLessEqual(len(text), 1, "Preview supports one text part")
            previews = re.findall(r"<ButtonsPreview\b(.*?)/>", tabs.get("Preview", ""), re.S)
            self.assertEqual(len(previews), 1, "Each request needs its own preview")
            preview = previews[0]
            items_prop = re.search(r"\bitems\s*=\s*\{", preview)
            self.assertIsNotNone(items_prop, "Request preview must include items")
            items, end = json.JSONDecoder().raw_decode(preview[items_prop.end():].lstrip())
            self.assertTrue(preview[items_prop.end():].lstrip()[end:].lstrip().startswith("}"))
            self.assertEqual(items, buttons[0]["items"], "Preview items differ from request")
            text_prop = re.search(r"\btext\s*=", preview)
            if text:
                with_text += 1
                self.assertIsNotNone(text_prop, "Request text is omitted from preview")
                # Text props use JSON double-quoted strings, just like the payload.
                value, _ = json.JSONDecoder().raw_decode(preview[text_prop.end():].lstrip())
                self.assertEqual(value, text[0], "Preview text differs from request")
            else:
                buttons_only += 1
                self.assertIsNone(text_prop, "Buttons-only preview must omit the text prop")
                self.assertEqual(parts, buttons, "Buttons-only example must contain only buttons")
        self.assertGreaterEqual(requests, 4, "Keep plain, URL, mixed, and buttons-only examples")
        self.assertGreater(with_text, 0, "Include a request with text")
        self.assertGreater(buttons_only, 0, "Include a valid buttons-only request")

    def test_buttons_previews_match_adjacent_requests(self):
        self.assert_buttons_previews_match_requests(
            (ROOT / "interactive-components/buttons.mdx").read_text())

    def test_buttons_preview_matches_native_shared_width(self):
        # Relay-iOS 004cd885, RelayButtonsRowLayout: pillWidthShare = 0.75,
        # pillHeight = 48, pillSpacing = 4, leading/trailingInset = 20/16.
        css = (ROOT / "style.css").read_text()

        def declarations(selector):
            block = re.search(r"^" + re.escape(selector) + r"\s*\{([^}]*)\}", css, re.M)
            self.assertIsNotNone(block, f"Missing {selector}")
            return dict(re.findall(r"([\w-]+)\s*:\s*([^;]+);", block[1]))

        stack = declarations(".buttons-preview-stack")
        self.assertEqual(stack["width"], "75%")
        self.assertEqual(stack["max-width"], "75%")
        self.assertEqual(stack["align-self"], "flex-start")
        self.assertEqual(stack["gap"], "4px")
        pill = declarations(".buttons-preview-pill")
        # Every pill fills the narrowed stack, never the whole message column
        # and never a separate label-dependent width.
        self.assertEqual(pill["width"], "100%")
        self.assertEqual(pill["box-sizing"], "border-box")
        self.assertEqual(pill["min-height"], "48px")
        self.assertEqual(pill["padding"], "12px 16px 12px 20px")
        self.assertEqual(pill["border-radius"], "24px")

    def test_buttons_preview_regressions_are_detected(self):
        source = (ROOT / "interactive-components/buttons.mdx").read_text()
        text_prop = re.search(r'\btext\s*=\s*("(?:\\.|[^"\\])*")', source)
        self.assertIsNotNone(text_prop, "Need a text preview for regression checks")
        for name, replacement in (
            ("mismatched text", 'text="Incorrect preview text"'),
            ("omitted text", ""),
        ):
            with self.subTest(regression=name):
                changed = source[:text_prop.start()] + replacement + source[text_prop.end():]
                with self.assertRaises(AssertionError):
                    self.assert_buttons_previews_match_requests(changed)
        items_prop = re.search(r"\bitems\s*=\s*\{", source)
        self.assertIsNotNone(items_prop)
        with self.subTest(regression="mismatched items"):
            tail = source[items_prop.end():]
            _, end = json.JSONDecoder().raw_decode(tail.lstrip())
            changed = (source[:items_prop.end()] + '[{"label":"Incorrect choice"}]' +
                       tail.lstrip()[end:])
            with self.assertRaises(AssertionError):
                self.assert_buttons_previews_match_requests(changed)
        for group in re.findall(r"<Tabs\b[^>]*>.*?</Tabs>", source, re.S):
            if '<Tab title="Request">' not in group:
                continue
            preview = re.search(r"<ButtonsPreview\b(.*?)/>", group, re.S)
            if preview and not re.search(r"\btext\s*=", preview[1]):
                with self.subTest(regression="invented buttons-only text"):
                    changed = source.replace(group, group.replace(
                        "<ButtonsPreview", '<ButtonsPreview text="Not in the request"', 1), 1)
                    with self.assertRaises(AssertionError):
                        self.assert_buttons_previews_match_requests(changed)
                with self.subTest(regression="missing buttons-only example"):
                    with self.assertRaises(AssertionError):
                        self.assert_buttons_previews_match_requests(source.replace(group, "", 1))
                break
        else:
            self.fail("Need a buttons-only preview for regression checks")

    def test_buttons_policy_section_and_backlinks_are_removed(self):
        paths = [
            path for path in ROOT.rglob("*.mdx")
            if not {"node_modules", ".mint", ".git"}.intersection(path.relative_to(ROOT).parts)
        ] + [ROOT / "llms.txt", ROOT / "llms-full.txt"]
        for path in paths:
            with self.subTest(path=str(path.relative_to(ROOT))):
                source = path.read_text()
                for stale in ("choose when to send buttons", "choose-when-to-send-buttons",
                              "if the person asks for buttons, send them."):
                    self.assertFalse(stale in source.lower(), f"{path.relative_to(ROOT)}: {stale}")

    def test_projection_changes_only_environment_origins(self):
        expected = (ROOT / "api-reference/openapi.yaml").read_bytes()
        if target() == "staging":
            for host in ("api", "docs", "go"):
                for scheme in ("https", "wss"):
                    expected = expected.replace(
                        f"{scheme}://{host}.relayapp.im".encode(),
                        f"{scheme}://{host}.staging.relayapp.im".encode(),
                    )
        self.assertEqual((ROOT / "api-reference/openapi.staging.yaml").read_bytes(), expected)

    def test_error_is_integrated_in_navigation_and_generated_surfaces(self):
        page = "api-reference/errors"
        config = json.loads((ROOT / "docs.json").read_text())
        self.assertIn(page, json.dumps(config["navigation"]))
        self.assertTrue((ROOT / f"{page}.mdx").is_file())
        for path in ("llms.txt", "llms-full.txt"):
            self.assertIn(page, (ROOT / path).read_text())
        # Error 2029 left with "Add comes back" (owner ruling 2026-09-13:
        # every agent is removable) and came back with a new meaning in
        # Relay-Server PR 233 (console.ts, organization membership).
        page_text = (ROOT / f"{page}.mdx").read_text()
        self.assertIn('<a id="2029">2029</a> | 403 | You are not a member of this organization.', page_text)
        self.assertNotIn("This agent cannot be removed.", page_text)


if __name__ == "__main__":
    unittest.main()
