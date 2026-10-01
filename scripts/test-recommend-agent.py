#!/usr/bin/env python3
"""Offline checks for the directory-to-Contact-Card guide and MCP tools."""
import json
import re
import unittest
from pathlib import Path

from docs_behavior import validate_share_contract

ROOT = Path(__file__).resolve().parents[1]
GUIDE = "chats/share-contact-card.mdx"


def section(text, heading):
    match = re.search(r"^## " + re.escape(heading) + r"\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    assert match, f"Missing section: {heading}"
    return match[1]


def check_recommendation(text):
    own = section(text, "Share your own card")
    assert re.search(r"relay\.chats\.shareContactCard\(chatId\)", own), "Keep the bodyless SDK call"
    own_curl = re.search(r"```bash[^\n]*\n(.*?)```", own, re.S)
    assert own_curl and "/share_contact_card" in own_curl[1], "Show the own-card HTTPS call"
    assert not re.search(r"--data|-d\b", own_curl[1]), "Own-card HTTPS must stay bodyless"

    recommend = section(text, "Recommend another agent")
    assert "relay.directory.search(" in recommend, "Show directory search with the SDK"
    assert "/v1/directory" in recommend, "Show public directory HTTPS"
    for field in ("q", "category", "limit"):
        assert re.search(rf"\b{field}:", recommend), f"Missing SDK filter: {field}"
        assert f"{field}=" in recommend, f"Missing HTTPS filter: {field}"
    assert re.search(r"relay\.chats\.shareContactCard\(chatId,\s*\{\s*handle:", recommend), "Share the selected handle"
    payloads = re.findall(r"--data(?:-raw)?\s+'([^']+)'", recommend)
    assert any(set(json.loads(value)) == {"handle"} for value in payloads), "Share JSON has only handle"
    assert re.search(r"public.*unlisted", recommend, re.I | re.S), "State allowed target visibility"
    assert "people can message it" in recommend, "State the people_can_message half of the rule"
    assert "Private, which turns people off" in recommend, "Say what makes an agent Private"
    assert "Idempotency-Key" in recommend, "Document Idempotency-Key"
    got = section(text, "What you get back")
    assert "is a snapshot" in got and "by the card's `id`" in got, "Document the snapshot and opening by id"
    assert re.search(r"(no|without|does not require).{0,35}(token|auth)", recommend, re.I), "Directory is public"
    assert "Nothing in the body is read" not in text, "Remove obsolete ignored-body claim"
    errors = section(text, "When it fails")
    hidden = next((row for row in errors.splitlines() if row.startswith("| `404`")), "")
    assert "Private" in hidden and "unknown" in hidden, "Private and unknown targets share 404"
    assert "member" in text.lower(), "Sharing requires membership"
    assert "| `429`" in errors and "send" in errors.lower(), "Sharing is send-rate limited"


class RecommendAgentTests(unittest.TestCase):
    def test_changed_api_title_preserves_the_existing_public_url(self):
        route = json.loads((ROOT / "scripts/api-page-paths.json").read_text())["shareContactWithChat"]
        self.assertEqual(route["href"], "/api-reference/chats/share-your-contact-card-with-a-chat")
        self.assertIn(route["href"], (ROOT / GUIDE).read_text())
        bundle = (ROOT / "api-reference/openapi.mint.yaml").read_text()
        operation = re.search(
            r"^  /v1/chats/\{chatId\}/share_contact_card:\n(.*?)(?=^  /|\Z)",
            bundle, re.M | re.S)[1]
        self.assertIn("summary: Share a contact card with a chat", operation)
        self.assertIn("href: " + route["href"], operation)
        self.assertIn("x-mint:", operation)

    def test_share_contract_regressions_are_detected(self):
        canonical = (ROOT / "api-reference/openapi.yaml").read_text()
        validate_share_contract(canonical)
        start = canonical.index("  /v1/chats/{chatId}/share_contact_card:")
        end = canonical.index("\n  /v1/", start + 1)
        operation = canonical[start:end]
        changes = {
            "required request body": canonical[:start] + operation.replace(
                "requestBody:\n        required: false", "requestBody:\n        required: true") + canonical[end:],
            "missing rate limit": canonical[:start] + operation.replace('"429":', '"503":') + canonical[end:],
            "required handle": canonical.replace("    ShareContactCardRequest:\n      type: object",
                "    ShareContactCardRequest:\n      required:\n        - handle\n      type: object"),
            "unbounded handle": canonical.replace(
                "    ShareContactCardRequest:\n      type: object\n      additionalProperties: false\n      properties:\n        handle:\n          type: string\n          minLength: 1\n          maxLength: 255",
                "    ShareContactCardRequest:\n      type: object\n      additionalProperties: false\n      properties:\n        handle:\n          type: string\n          minLength: 1"),
            "lost Idempotency-Key": canonical[:start] + operation.replace("- name: Idempotency-Key", "- name: X-Request-Id") + canonical[end:],
            "lost key reuse": canonical[:start] + operation.replace('"409":', '"410":') + canonical[end:],
            "own card requires target ID": canonical.replace(
                "    ContactCardItem:\n      type: object\n      required:",
                "    ContactCardItem:\n      type: object\n      required:\n        - id"),
        }
        for name, changed in changes.items():
            with self.subTest(mutation=name):
                self.assertNotEqual(changed, canonical)
                with self.assertRaises(ValueError):
                    validate_share_contract(changed)

    def test_guide_regressions_are_detected(self):
        original = (ROOT / GUIDE).read_text()
        check_recommendation(original)
        mutations = {
            "lost bodyless share": ("shareContactCard(chatId)", "shareContactCard(chatId, {})"),
            "wrong directory API": ("/v1/directory", "/v1/agents/search"),
            "wrong SDK method": ("relay.directory.search(", "relay.agents.search("),
            "wrong target field": ('--data \'{"handle":', '--data \'{"agent":'),
            "visibility leak": ("Private", "Public"),
            "lost rate limit": ("| `429`", "| `503`"),
            "lost snapshot": ("is a snapshot", "is live"),
            "lost people rule": ("people can message it", "it exists"),
            "lost idempotency": ("Send an `Idempotency-Key` header", "Send a header"),
        }
        for name, (before, after) in mutations.items():
            with self.subTest(mutation=name):
                self.assertIn(before, original)
                with self.assertRaises(AssertionError):
                    check_recommendation(original.replace(before, after))

    def test_mcp_documents_read_search_and_write_share_inputs(self):
        text = (ROOT / "integrations/mcp.mdx").read_text()
        search = next((line for line in text.splitlines() if line.startswith("| `search_agents`")), "")
        share = next((line for line in text.splitlines() if line.startswith("| `share_contact_card`")), "")
        for field in ("q", "category", "limit"):
            self.assertIn(f"`{field}`", search)
        self.assertIn("Read", search)
        for field in ("chat_id", "handle"):
            self.assertIn(f"`{field}`", share)
        self.assertIn("Write", share)
        self.assertRegex(share, r"(?i)omit.*own")
        self.assertIn('[mcp_servers.relay.tools.share_contact_card]\napproval_mode = "approve"', text)
        self.assertIn("/chats/share-contact-card#recommend-another-agent", text)

    def test_changelog_links_to_the_guide(self):
        text = (ROOT / "changelog.mdx").read_text()
        self.assertIn("/chats/share-contact-card#recommend-another-agent", text)

    def test_guide_is_already_in_navigation(self):
        config = json.loads((ROOT / "docs.json").read_text())
        self.assertIn(GUIDE.removesuffix(".mdx"), json.dumps(config["navigation"]))


if __name__ == "__main__":
    unittest.main()
