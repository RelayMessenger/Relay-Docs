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
        self.assertLess(cli.index("## Create an agent"), cli.index("## Authenticate an existing Agent Token"))
        self.assertNotIn("Coming soon on staging", cli)
        self.assertIn("canonical CLI package", cli)
        for marker in ("hidden Agent Token prompt", "Get-Content -Raw $TokenFile", "auth login --with-token", "auth status", "auth logout", "RELAY_AGENT_TOKEN"):
            self.assertIn(marker, cli)
        for path in ROOT.rglob("*.mdx"):
            if "node_modules" in path.parts:
                continue
            text = path.read_text()
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertNotIn("@relaymessenger/cli", text)
                self.assertNotIn("relaymessenger@latest", text)
                self.assertNotIn("agents setup", text)
                self.assertNotIn("--token-stdin", text)
                self.assertNotIn("--from-env", text)
                self.assertNotIn("token import", text)
                self.assertNotIn("token status", text)
                self.assertNotIn("token clear", text)
                self.assertNotRegex(text, r"(?m)^\s*relay (?:agents|auth|profiles|doctor|events)\b")

    def test_lifecycle_boundaries_and_explicit_origin(self):
        text = (ROOT / "guides/agents/lifecycle.mdx").read_text()
        for marker in ("live in the staging API", "locally saved profiles", "no automatic retry",
                       "`image_url`", "HTTP `409`", "history retained", 'token: "stored"'):
            self.assertIn(marker, text)
        self.assertIn(expected("agents create --api-url https://api.staging.relayapp.im"), text)
        self.assertIn('maxRetries: 0', text)
        self.assertIn('mode: 0o600', text)

    def test_native_consent_and_separate_connection_proof(self):
        text = (ROOT / "integrations/native-setup.mdx").read_text()
        for marker in ("auth login --with-token --api-url", "--confirm-configure", "--runtime-stopped",
                       "--runtime-account", "--runtime-context", '"connected": false',
                       "RELAY_ALLOWED_SENDERS", "sender permissions"):
            self.assertIn(marker, text)

    def test_start_supports_anonymous_or_existing_token_without_console(self):
        skill = (ROOT / "skill.md").read_text()
        start = skill.split("## Start\n", 1)[1].split("\n## ", 1)[0]
        for marker in ("anonymous `POST /v1/agents`", "existing ordinary Agent Token", "Neither", "requires a Console account"):
            self.assertIn(marker, start)
        self.assertNotRegex(start, r"created in that environment.s\s+Console")
        self.assertIn("API is live on staging", skill)
        self.assertNotIn("Agent management is coming soon", skill)

    def test_native_guides_gate_cli_publication_not_live_api(self):
        for name in ("openclaw", "hermes", "claude-code"):
            text = (ROOT / f"integrations/{name}.mdx").read_text()
            with self.subTest(integration=name):
                self.assertIn("through the staging CLI", text)
                self.assertIn("already live on staging", text)
                self.assertNotIn("staging route and package verification", text)

    def test_custom_profile_uses_existing_recipe_and_rendered_image_pair(self):
        spec = (ROOT / "api-reference/openapi.yaml").read_text()
        request = spec.split("    CreateAgentRequest:\n", 1)[1].split("    AgentImageRecipe:\n", 1)[0]
        for field in ("handle:", "first_name:", "image_url:", "image_recipe:"):
            self.assertIn(field, request)
        self.assertIn("dependentRequired:", request)
        self.assertIn("image_recipe:\n          - image_url", request)
        guide = (ROOT / "guides/agents/lifecycle.mdx").read_text()
        for marker in ("--handle", "--name", "--image-url", "--image-recipe", "8192", "drawAvatar", '"monogram"', '"5B9BFA"'):
            self.assertIn(marker, guide)
        self.assertIn("Server does not render a recipe-only request", guide)

    def test_released_ux_preserves_script_behavior(self):
        cli = (ROOT / "integrations/cli.mdx").read_text()
        for marker in ("published staging CLI", "--image", "path or public HTTPS URL",
                       "Handle (optional)", "Name (optional)", "Image (optional)",
                       "before setup", "read-only", "observational: true", "--json",
                       "Ctrl-C", "full_sync_complete", "real consumer"):
            self.assertIn(marker, cli)
        self.assertNotIn("Coming soon", cli)
        self.assertNotIn("coming release", cli)
        self.assertIn('export RELAY_CONFIG_PATH="$(mktemp -d)/config.json"', cli)
        self.assertLess(cli.index("## Keep the terminal open"), cli.index("## Use local event forwarding"))
        skills = (ROOT / "integrations/skills.mdx").read_text()
        for marker in ("Offer skills before setup", "opt-in", "Decline or cancel", "unknown detection", "provider API keys"):
            self.assertIn(marker, skills)

    def test_image_upload_uses_completed_owned_attachment_and_existing_profile_retry(self):
        guide = (ROOT / "guides/agents/lifecycle.mdx").read_text()
        for marker in ("--image ./avatar.png", "published staging CLI", "allocates an Attachment", "verifies completion",
                       "attachment_id", "not image binary data", "--attachment-id", "not with another create"):
            self.assertIn(marker, guide)
        self.assertIn(expected("https://staging.relayapp.im/@brave_cangoo.dev"), guide)
        self.assertIn("compatible aliases", guide)
        cards = " ".join((ROOT / "guides/contact-cards.mdx").read_text().split())
        for marker in ("attachment must be complete", "authenticated agent", "mutually exclusive", "permanent public image storage"):
            self.assertIn(marker, cards)

    def test_observer_wire_is_canonical_and_distinct_from_ack_consumer(self):
        spec = (ROOT / "api-reference/openapi.yaml").read_text()
        socket = spec.split("  /v1/websocket:\n", 1)[1].split("  /v1/contact_requests:", 1)[0]
        self.assertIn("name: observe", socket)
        self.assertIn("observational:true", socket)
        self.assertIn("ACK and full_sync_complete frames are rejected", socket)
        websocket = (ROOT / "guides/websocket/index.mdx").read_text()
        self.assertIn("observe=true", websocket)
        self.assertIn("Connection-local transient cursor", websocket)
        self.assertNotIn("An upgrade URL with a query string returns", websocket)

    def test_released_agent_admission_keeps_authorization_and_session_caveats(self):
        openclaw = (ROOT / "integrations/openclaw.mdx").read_text()
        claude = (ROOT / "integrations/claude-code.mdx").read_text()
        self.assertIn("`>=2026.8.1 <2026.9.0`", openclaw)
        self.assertIn("build version `2026.8.1`", openclaw)
        for text in (openclaw, claude):
            for marker in ("agent Contact", "allowlist", "FULL sync", "session", "API origin"):
                self.assertIn(marker, text)
        for marker in ("allowFrom", "Contact UUID", "stable-ID", "dmScope", "Snapshot recovery"):
            self.assertIn(marker, openclaw)
        for marker in ("RELAY_ALLOWED_SENDERS", "reply-origin", "contact.is_me", "authenticated origin"):
            self.assertIn(marker, claude)
        for name in ("cli", "skills"):
            self.assertNotIn("Coming soon", (ROOT / f"integrations/{name}.mdx").read_text())

    def test_new_pages_and_operations_are_integrated(self):
        navigation = json.dumps(json.loads((ROOT / "docs.json").read_text())["navigation"])
        for path in ("guides/agents/lifecycle", "integrations/native-setup",
                     "api-reference/resources/agents/overview", "POST /v1/agents", "DELETE /v1/agents/{handle}"):
            self.assertIn(path, navigation)


if __name__ == "__main__":
    unittest.main()
