#!/usr/bin/env python3
"""Offline regressions for the hosted validator's canonical cache gate."""
from contextlib import redirect_stdout
import hashlib
import importlib.util
from io import StringIO
from pathlib import Path
import unittest

from hosted_cache import CANONICAL_PATHS, canonical_cache_pairs

spec = importlib.util.spec_from_file_location(
    "validate_hosted_llms", Path(__file__).with_name("validate-hosted-llms.py"))
hosted = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hosted)


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
            CANONICAL_PATHS, ("", "start/quickstart", "llms.txt", "llms-full.txt", "skill.md", "agent-prompt.md")
        )
        fetch, calls = self.responses()
        self.assertEqual(len(list(canonical_cache_pairs(fetch))), 6)
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
        self.assertEqual(len(list(canonical_cache_pairs(fetch, {"skill.md": b"current"}))), 6)

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


class HostedSourceOriginTests(unittest.TestCase):
    """The origin body is the truth; Mintlify's edge cache is a warning, never a failure."""

    def fetch_for(self, *, canonical, origin):
        def fetch(path, cache_busted=False):
            body = origin if cache_busted or path != "llms-full.txt" else canonical
            return {"body": body, "sha256": hashlib.sha256(body).hexdigest(),
                    "headers": {"age": "20179", "cache-control": "public, max-age=86400"}}
        return fetch

    def test_stale_edge_with_current_origin_passes_with_a_warning_line(self):
        fetch = self.fetch_for(canonical=b"old", origin=b"current")
        output = StringIO()
        with redirect_stdout(output):
            pairs = list(hosted.hosted_source_pairs(fetch, {"llms-full.txt": b"current"}))
        self.assertEqual([path for path, _, _ in pairs], list(CANONICAL_PATHS))
        self.assertEqual(output.getvalue(), "warning: /llms-full.txt: Mintlify edge cache is 20179 s "
                         "behind origin (max-age 86400); origin matches checkout\n")

    def test_stale_origin_fails_even_when_edge_agrees(self):
        fetch = self.fetch_for(canonical=b"old", origin=b"old")
        with self.assertRaisesRegex(SystemExit, "served body does not match expected checkout source bytes"):
            list(hosted.hosted_source_pairs(fetch, {"llms-full.txt": b"current"}))

    def test_edge_freshness_is_opt_in_only(self):
        self.assertFalse(hosted.argument_parser().parse_args(["https://docs.test"]).require_edge_fresh)
        fetch = self.fetch_for(canonical=b"old", origin=b"current")
        with self.assertRaisesRegex(SystemExit, "canonical body .* does not match current origin body"):
            list(hosted.hosted_source_pairs(fetch, {"llms-full.txt": b"current"}, require_edge_fresh=True))


if __name__ == "__main__":
    unittest.main()
