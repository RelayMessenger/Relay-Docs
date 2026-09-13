#!/usr/bin/env python3
"""Pin the independently read Server input, not a checksum derived from Docs."""
import hashlib
import json
import unittest
from pathlib import Path

from origins import target

ROOT = Path(__file__).resolve().parents[1]
# Exact customization contract at the confirmed Server staging merge.
# Update only after reading and synchronizing a newly agreed upstream contract.
UPSTREAM_COMMIT = "935a558ee806aeb0d231460a6bd79dc54786ba96"
UPSTREAM_STAGING_COMMIT = "935a558ee806aeb0d231460a6bd79dc54786ba96"
UPSTREAM_SHA256 = "787e5dd583a2ba382931fe6799ecc7a421d1a4f94dce11a890fc6a1eeca4ea97"


class ContractSourceTests(unittest.TestCase):
    def test_canonical_bytes_equal_pinned_upstream(self):
        canonical = (ROOT / "api-reference/openapi.yaml").read_bytes()
        self.assertEqual(hashlib.sha256(canonical).hexdigest(), UPSTREAM_SHA256,
                         f"Canonical input differs from Relay-Server {UPSTREAM_COMMIT}")

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
        # Error 2029 and Contact.is_removable left with "Add comes back"
        # (owner ruling 2026-09-13): every agent is removable, so the errors
        # page must not list the code. The vendored contract loses it when the
        # lead re-vendors after the Server PR merges; validate-docs pins bytes.
        page_text = (ROOT / f"{page}.mdx").read_text()
        self.assertNotIn('<a id="2029">2029</a>', page_text)
        self.assertNotIn("This agent cannot be removed.", page_text)


if __name__ == "__main__":
    unittest.main()
