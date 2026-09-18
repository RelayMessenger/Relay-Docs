#!/usr/bin/env python3
"""Pin the independently read Server input, not a checksum derived from Docs."""
import hashlib
import json
import os
import unittest
from pathlib import Path

from origins import target

ROOT = Path(__file__).resolve().parents[1]
# Independently read canonical contract at the Server staging removal merge.
UPSTREAM_COMMIT = "ef8cedb1015e1e0d0856d61b69057f2b831f7c90"
UPSTREAM_STAGING_COMMIT = "ef8cedb1015e1e0d0856d61b69057f2b831f7c90"
UPSTREAM_SHA256 = "1b687dc9ffc7a6296a04b570d20fe32bed758deb2ed8f38fc48d0d44a10db2ec"


class ContractSourceTests(unittest.TestCase):
    def test_canonical_bytes_equal_pinned_upstream(self):
        canonical = (ROOT / "api-reference/openapi.yaml").read_bytes()
        local_source = os.environ.get("RELAY_OPENAPI_SOURCE")
        if local_source:
            # Uncommitted coordinated work uses independent Server bytes without
            # claiming that the historical public commit contains the new contract.
            self.assertEqual(canonical, Path(local_source).read_bytes())
        else:
            self.assertEqual(hashlib.sha256(canonical).hexdigest(), UPSTREAM_SHA256,
                             f"Canonical input differs from Relay-Server {UPSTREAM_COMMIT}; "
                             "for local coordinated changes set RELAY_OPENAPI_SOURCE")

    def test_buttons_are_text_only_and_keep_tap_reply_semantics(self):
        canonical = (ROOT / "api-reference/openapi.yaml").read_text()
        items = canonical.split("    ButtonItem:\n", 1)[1].split("    ButtonsPart:\n", 1)[0]
        self.assertNotIn("image_url", items)
        self.assertIn("only a valid sole-part `button_reply`", canonical)
        self.assertIn("Text and `button_reply` parts remain replyable", canonical)
        self.assertIn("Text and `button_reply` parts remain reactable", canonical)
        parts = (ROOT / "messages/parts.mdx").read_text()
        self.assertNotIn("image_url", parts)
        self.assertIn('"type":"button_reply"', parts)
        self.assertIn("ordinary replies and reactions", parts)
        for path in ("skill.md", ".mintlify/skills/relay/SKILL.md"):
            self.assertIn("not\n  ordinary replies or reactions", (ROOT / path).read_text())

        self.assertIn("The accompanying `text` part and the tap", (ROOT / "llms-full.txt").read_text())

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
