#!/usr/bin/env python3
"""Keep pending agent onboarding on the one staging CLI and canonical contract."""
import json
import re
import unittest
from pathlib import Path
from origins import origin, production_text, target

ROOT = Path(__file__).resolve().parents[1]


def expected(value):
    return production_text(value) if target() == "production" else value


class AgentOnboardingTests(unittest.TestCase):
    def test_canonical_bootstrap_and_scoped_delete(self):
        source = (ROOT / "api-reference/openapi.yaml").read_text()
        create = source.split("  /v1/agents:\n", 1)[1].split("  /v1/agents/{handle}:\n", 1)[0]
        delete = source.split("  /v1/agents/{handle}:\n", 1)[1].split("  /v1/chats:\n", 1)[0]
        self.assertIn("operationId: createAgent", create)
        self.assertIn("security: []", create)
        self.assertIn("operationId: deleteAgent", delete)
        self.assertIn("- BearerAuth: []", delete)
        self.assertIn('"409":', delete)
        self.assertNotRegex(create, r"(?m)^    get:")
        self.assertNotIn("x-mint:", source)

    def test_one_pending_cli_front_door(self):
        cli = (ROOT / "integrations/cli.mdx").read_text()
        self.assertIn(expected("npx relaymessenger@staging --help"), cli)
        self.assertIn("no login, Console account, or existing Agent Token", cli)
        self.assertLess(cli.index("## Create an agent"), cli.index("## Import an existing Agent Token"))
        self.assertIn("Coming soon on staging", cli)
        for path in ROOT.rglob("*.mdx"):
            if "node_modules" in path.parts:
                continue
            text = path.read_text()
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertNotIn("@relaymessenger/cli", text)
                self.assertNotRegex(text, r"\brelaymessenger@\d")
                self.assertNotIn("agents setup", text)
                self.assertNotIn("auth login", text)
                self.assertNotIn("auth status", text)
                self.assertNotIn("auth logout", text)
                self.assertNotRegex(text, r"(?m)^\s*relay (?:agents|auth|profiles|doctor|events)\b")

    def test_lifecycle_boundaries_and_explicit_origin(self):
        text = (ROOT / "guides/agents/lifecycle.mdx").read_text()
        for marker in ("Coming soon on staging", "locally saved profiles", "no automatic retry",
                       "`image_url`", "HTTP `409`", "history retained", 'token: "stored"'):
            self.assertIn(marker, text)
        self.assertIn(expected("agents create --api-url https://api.staging.relayapp.im"), text)
        self.assertIn('maxRetries: 0', text)
        self.assertIn('mode: 0o600', text)

    def test_native_consent_and_separate_connection_proof(self):
        text = (ROOT / "integrations/native-setup.mdx").read_text()
        for marker in ("token import --api-url", "--confirm-configure", "--runtime-stopped",
                       "--runtime-account", "--runtime-context", '"connected": false',
                       "RELAY_ALLOWED_SENDERS", "sender permissions"):
            self.assertIn(marker, text)

    def test_new_pages_and_operations_are_integrated(self):
        navigation = json.dumps(json.loads((ROOT / "docs.json").read_text())["navigation"])
        for path in ("guides/agents/lifecycle", "integrations/native-setup",
                     "api-reference/resources/agents/overview", "POST /v1/agents", "DELETE /v1/agents/{handle}"):
            self.assertIn(path, navigation)


if __name__ == "__main__":
    unittest.main()
