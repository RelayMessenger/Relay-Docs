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
            CANONICAL_PATHS, ("", "start/quickstart", "llms.txt", "llms-full.txt", "skill.md")
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

    def test_equally_stale_responses_cannot_pass_source_gate(self):
        fetch, _ = self.responses()
        with self.assertRaisesRegex(SystemExit, "expected checkout source bytes"):
            list(canonical_cache_pairs(fetch, {"skill.md": b"new-source"}))

    def test_matching_source_bytes_are_accepted(self):
        fetch, _ = self.responses()
        self.assertEqual(len(list(canonical_cache_pairs(fetch, {"skill.md": b"current"}))), 5)

    def test_existing_llms_cache_gate_is_preserved(self):
        fetch, _ = self.responses(stale="llms-full.txt")
        with self.assertRaisesRegex(SystemExit, r"/llms-full\.txt canonical body"):
            list(canonical_cache_pairs(fetch))

    def test_discovered_routes_use_the_same_strict_cache_gate(self):
        fetch, calls = self.responses()
        paths = ["guides/new-task", "guides/new-task.md"]
        self.assertEqual(len(list(canonical_cache_pairs(fetch, paths=paths))), 2)
        self.assertEqual(calls, [(path, busted) for path in paths for busted in (False, True)])

    def test_discovered_markdown_staleness_is_rejected(self):
        fetch, _ = self.responses(stale="guides/new-task.md")
        with self.assertRaisesRegex(SystemExit, "canonical body"):
            list(canonical_cache_pairs(fetch, paths=["guides/new-task.md"]))

    def test_all_agent_sources_require_exact_bytes_even_if_caches_agree(self):
        for path in ("skill.md", "llms.txt", "llms-full.txt"):
            with self.subTest(path=path):
                fetch, _ = self.responses()
                with self.assertRaisesRegex(SystemExit, "expected checkout source bytes"):
                    list(canonical_cache_pairs(fetch, {path: b"current\n"}))

    def test_cache_comparison_does_not_normalize_whitespace(self):
        def fetch(path, cache_busted=False):
            body = b"same words\n" if cache_busted else b"same words"
            return {"body": body, "sha256": hashlib.sha256(body).hexdigest()}
        with self.assertRaisesRegex(SystemExit, "canonical body"):
            list(canonical_cache_pairs(fetch))


if __name__ == "__main__":
    unittest.main()
