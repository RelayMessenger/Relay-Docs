#!/usr/bin/env python3
"""Offline regressions for the hosted validator's canonical cache gate."""
import hashlib
import unittest

from hosted_cache import CANONICAL_PATHS, canonical_cache_pairs


class HostedCacheTests(unittest.TestCase):
    def responses(self, stale=None):
        calls = []

        def fetch(path, cache_busted=False):
            calls.append((path, cache_busted))
            body = b"old" if path == stale and not cache_busted else b"current"
            return {"body": body, "sha256": hashlib.sha256(body).hexdigest()}

        return fetch, calls

    def test_all_canonical_surfaces_are_checked_twice(self):
        self.assertEqual(
            CANONICAL_PATHS, ("", "guides", "llms.txt", "llms-full.txt", "skill.md")
        )
        fetch, calls = self.responses()
        self.assertEqual(len(list(canonical_cache_pairs(fetch))), 5)
        self.assertEqual(
            calls, [(path, busted) for path in CANONICAL_PATHS for busted in (False, True)]
        )

    def test_stale_skill_is_rejected_even_when_every_other_page_is_current(self):
        fetch, _ = self.responses(stale="skill.md")
        with self.assertRaisesRegex(SystemExit, r"/skill\.md canonical body .* does not match"):
            list(canonical_cache_pairs(fetch))

    def test_existing_llms_cache_gate_is_preserved(self):
        fetch, _ = self.responses(stale="llms-full.txt")
        with self.assertRaisesRegex(SystemExit, r"/llms-full\.txt canonical body"):
            list(canonical_cache_pairs(fetch))


if __name__ == "__main__":
    unittest.main()
