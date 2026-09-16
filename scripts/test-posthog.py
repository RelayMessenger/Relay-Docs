#!/usr/bin/env python3
"""Environment and mutation tests; run in Daytona."""
import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from docs_analytics import configuration, rendered, validate
from origins import ROOT, POSTHOG_PROJECTS, production_text, target

spec = importlib.util.spec_from_file_location("derive", ROOT / "scripts/derive-production.py")
derive = importlib.util.module_from_spec(spec)
spec.loader.exec_module(derive)


class PostHogTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        for name in ("posthog.js", "docs.json", ".mintignore", ".docs-target",
                     "scripts/posthog-projects.json", "scripts/api-page-paths.json"):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, path)

    def test_checked_in_integration(self):
        validate(ROOT, target())

    def test_both_environments_have_distinct_public_tokens(self):
        staging = configuration(self.root, "staging")
        production = configuration(self.root, "production")
        self.assertNotEqual(staging["token"], production["token"])
        self.assertEqual(staging["origin"], "https://docs.staging.relayapp.im")
        self.assertEqual(production["origin"], "https://docs.relayapp.im")
        for config in (staging, production):
            self.assertTrue(config["token"].startswith("phc_"))
            self.assertIn("/", config["paths"])
            self.assertIn("/messages/send", config["paths"])
            self.assertIn("/api-reference/messages/send-a-message-to-an-existing-chat", config["paths"])
            self.assertNotIn("/v1/chats/{chatId}/messages", config["paths"])

    @unittest.skipIf(target() == "production", "authored staging fixture only")
    def test_actual_promotion_switches_token_and_is_idempotent(self):
        before = (self.root / "posthog.js").read_text()
        self.assertEqual(production_text(before).count(POSTHOG_PROJECTS["staging"]["token"]), 0)
        derive.rewrite_tree(self.root)
        validate(self.root, "production")
        after = (self.root / "posthog.js").read_text()
        self.assertIn(POSTHOG_PROJECTS["production"]["token"], after)
        self.assertNotIn(POSTHOG_PROJECTS["staging"]["token"], after)
        self.assertEqual(derive.rewrite_tree(self.root), [])
        self.assertEqual(rendered(self.root, "production"), after)
        self.assertEqual((ROOT / "posthog.js").read_text(), before)

    def test_missing_script_fails(self):
        (self.root / "posthog.js").unlink()
        with self.assertRaises(FileNotFoundError):
            validate(self.root, target())

    def test_missing_configuration_fails(self):
        (self.root / "posthog.js").write_text("(() => {})();\n")
        with self.assertRaises(ValueError):
            validate(self.root, target())

    def test_wrong_environment_token_fails_in_each_environment(self):
        path = self.root / "posthog.js"
        for environment, wrong in (("staging", "production"), ("production", "staging")):
            path.write_text(rendered(self.root, environment))
            valid = path.read_text()
            path.write_text(valid.replace(POSTHOG_PROJECTS[environment]["token"], POSTHOG_PROJECTS[wrong]["token"]))
            with self.assertRaises(ValueError):
                validate(self.root, environment)

    def test_missing_and_private_tokens_fail(self):
        path = self.root / "posthog.js"
        original = path.read_text()
        for token in ("", "phx_private", "phc_unknown"):
            path.write_text(original.replace(POSTHOG_PROJECTS[target()]["token"], token))
            with self.assertRaises(ValueError):
                validate(self.root, target())

    def test_invalid_project_mapping_is_rejected(self):
        path = self.root / "scripts/posthog-projects.json"
        original = path.read_text()
        for field, value in (
            ("projectId", 533131),
            ("token", POSTHOG_PROJECTS["production"]["token"]),
            ("token", "phx_private"),
        ):
            projects = json.loads(original)
            projects["staging"][field] = value
            path.write_text(json.dumps(projects))
            with self.assertRaises(ValueError):
                validate(self.root, target())

    def test_wrong_origin_fails(self):
        path = self.root / "posthog.js"
        path.write_text(path.read_text().replace(configuration(self.root, target())["origin"], "https://example.com"))
        with self.assertRaises(ValueError):
            validate(self.root, target())

    def test_stale_routes_fail(self):
        path = self.root / "docs.json"
        config = json.loads(path.read_text())
        config["navigation"]["tabs"][0]["groups"][0]["pages"].append("new-page")
        path.write_text(json.dumps(config))
        with self.assertRaises(ValueError):
            validate(self.root, target())

    def test_native_duplicate_is_rejected(self):
        path = self.root / "docs.json"
        original = json.loads(path.read_text())
        for key in ("integrations", "analytics"):
            config = {**original, key: {"posthog": {"apiKey": POSTHOG_PROJECTS[target()]["token"]}}}
            path.write_text(json.dumps(config))
            with self.assertRaises(ValueError):
                validate(self.root, target())

    def test_ignored_script_is_rejected(self):
        path = self.root / ".mintignore"
        path.write_text(path.read_text() + "\nposthog.js\n")
        with self.assertRaises(ValueError):
            validate(self.root, target())


if __name__ == "__main__":
    unittest.main()
