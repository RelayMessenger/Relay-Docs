#!/usr/bin/env python3
"""Pin the shape of the production promotion workflow.

Production is never updated by a push to staging (owner ruling, 2026-09-07):
a person dispatches .github/workflows/promote-to-production.yml, and the
workflow itself pushes `main` after the derivation guard and production
validation. GitHub Actions may not open pull requests in this org, so a
`pr create` step is a promotion that a person has to finish by hand.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "promote-to-production.yml"

GUARD_STEP = "No staging origin or package reference may remain"
VALIDATE_STEP = "Validate in production mode"
PUSH_STEP = "Push the derived tree to main"


def step_names(text: str) -> list:
    return re.findall(r"^      - name: (.+)$", text, flags=re.MULTILINE)


def step_body(text: str, name: str) -> str:
    start = text.index(f"      - name: {name}\n")
    rest = text[start + 1:]
    match = re.search(r"^      - ", rest, flags=re.MULTILINE)
    return rest[: match.start()] if match else rest


class PromoteWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.text = WORKFLOW.read_text()
        self.names = step_names(self.text)

    def test_dispatch_is_the_only_trigger(self):
        triggers = re.search(r"^on:\n((?:  .*\n|\n)+)", self.text, flags=re.MULTILINE).group(1)
        self.assertEqual(re.findall(r"^  (\w+):", triggers, flags=re.MULTILINE), ["workflow_dispatch"])

    def test_no_pull_request_step(self):
        self.assertNotRegex(self.text, r"gh pr|pr create|pull-requests: write")

    def test_main_is_the_only_push(self):
        pushes = re.findall(r"git push.*$", self.text, flags=re.MULTILINE)
        self.assertEqual(pushes, ["git push origin HEAD:main"])

    def test_push_follows_guard_and_validation(self):
        for name in (GUARD_STEP, VALIDATE_STEP, PUSH_STEP):
            self.assertIn(name, self.names)
        self.assertLess(self.names.index(GUARD_STEP), self.names.index(VALIDATE_STEP))
        self.assertLess(self.names.index(VALIDATE_STEP), self.names.index(PUSH_STEP))
        self.assertEqual(self.names[-1], PUSH_STEP)

    def test_guard_still_rejects_staging_references(self):
        body = step_body(self.text, GUARD_STEP)
        self.assertIn("staging\\.relayapp\\.im", body)
        self.assertIn('test "$(cat .docs-target)" = production', body)

    def test_push_replaces_main_tree_with_the_derived_tree(self):
        body = step_body(self.text, PUSH_STEP)
        self.assertIn("git merge -q -s ours --no-commit", body)
        self.assertIn("git read-tree -u --reset", body)
        # The derived edits must leave the working tree before the switch to
        # main, or checkout refuses (rehearsed 2026-09-07).
        self.assertLess(body.index("git write-tree"), body.index("git reset -q --hard"))
        self.assertLess(body.index("git reset -q --hard"), body.index("git checkout -q -B main origin/main"))
        self.assertIn('test "$(git rev-parse HEAD^{tree})" = "$derived_tree"', body)
        self.assertLess(body.index("read-tree"), body.index("git push origin HEAD:main"))

    def test_commit_names_source_and_run_and_summary_names_production(self):
        body = step_body(self.text, PUSH_STEP)
        self.assertRegex(body, r'-m "Production docs are staging \$short derived \(promotion \$RUN_URL\)"')
        self.assertIn("https://docs.relayapp.im", body)
        self.assertIn("Source staging commit: $source_sha", body)


if __name__ == "__main__":
    unittest.main()
