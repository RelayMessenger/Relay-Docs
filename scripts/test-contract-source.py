#!/usr/bin/env python3
"""Pin the independently read Server input, not a checksum derived from Docs."""
import hashlib
import json
import unittest
from pathlib import Path

from origins import target

ROOT = Path(__file__).resolve().parents[1]
# Relay-Server/contracts/developer/openapi.yaml at this reviewed staging commit.
# Update only after reading and synchronizing a newly agreed upstream contract.
UPSTREAM_COMMIT = "8c66df98287cc588401fbfeccdc301384e6e5f4d"
UPSTREAM_SHA256 = "b1504c934cc8a13f9bce87ed73c30879fb4d0302bc91aec1ee366518c0766680"


class ContractSourceTests(unittest.TestCase):
    def test_canonical_bytes_equal_pinned_upstream(self):
        canonical = (ROOT / "api-reference/openapi.yaml").read_bytes()
        self.assertEqual(hashlib.sha256(canonical).hexdigest(), UPSTREAM_SHA256,
                         f"Canonical input differs from Relay-Server {UPSTREAM_COMMIT}")

    def test_projection_changes_only_environment_origins(self):
        expected = (ROOT / "api-reference/openapi.yaml").read_bytes()
        if target() == "staging":
            expected = expected.replace(b"https://api.relayapp.im", b"https://api.staging.relayapp.im")
            expected = expected.replace(b"wss://api.relayapp.im", b"wss://api.staging.relayapp.im")
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
