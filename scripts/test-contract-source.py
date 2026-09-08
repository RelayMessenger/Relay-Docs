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
UPSTREAM_COMMIT = "04c729e3e3b2249eb9cca93fbb09ee3dd5fd69a6"
UPSTREAM_STAGING_COMMIT = "04c729e3e3b2249eb9cca93fbb09ee3dd5fd69a6"
UPSTREAM_SHA256 = "7d46b16f5dc19034cbdcb45bdd79816a9a2f4c9f6febb8520db0517dfe9eae64"


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
        page = "error/codes/2xxx/2029"
        config = json.loads((ROOT / "docs.json").read_text())
        self.assertIn(page, json.dumps(config["navigation"]))
        self.assertTrue((ROOT / f"{page}.mdx").is_file())
        for path in ("error/index.mdx", "llms.txt", "llms-full.txt"):
            with self.subTest(path=path):
                self.assertIn(page, (ROOT / path).read_text())
        for path in ("api-reference/openapi.staging.yaml", "api-reference/openapi.mint.yaml"):
            with self.subTest(path=path):
                text = (ROOT / path).read_text()
                self.assertIn("code: 2029", text)
                self.assertIn("is_removable:", text)
        page_text = (ROOT / f"{page}.mdx").read_text()
        self.assertIn("| `403` | `2029` |", page_text)
        self.assertIn("`This agent is not removable.`", page_text)
        self.assertIn("Group membership can change", page_text)


if __name__ == "__main__":
    unittest.main()
