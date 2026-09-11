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
UPSTREAM_COMMIT = "63d887d4ddc6d7bd04abc8cc14cdb7d1ca01868f"
UPSTREAM_STAGING_COMMIT = "63d887d4ddc6d7bd04abc8cc14cdb7d1ca01868f"
UPSTREAM_SHA256 = "19bc597eee8369938354f4eac91fbf527bed3ee9e2084675173c5e5035bfb693"


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
        for path in ("api-reference/openapi.staging.yaml", "api-reference/openapi.mint.yaml"):
            with self.subTest(path=path):
                text = (ROOT / path).read_text()
                self.assertIn("code: 2029", text)
                self.assertIn("is_removable:", text)
        page_text = (ROOT / f"{page}.mdx").read_text()
        self.assertIn('<a id="2029">2029</a> | 403', page_text)
        self.assertIn("This agent cannot be removed.", page_text)


if __name__ == "__main__":
    unittest.main()
