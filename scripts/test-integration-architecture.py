#!/usr/bin/env python3
"""Offline regression coverage for the approved integration directory.

--root supports mutation proofs in an isolated copy, never the shared checkout.
The inherited snippet hashes pin content from before this reorganization.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import unittest

from origins import production_text

ROOT = Path(__file__).resolve().parents[1]
GROUPS = {
    "Coding agents": [
        "claude-code", "cursor", "codex", "vs-code", "gemini-cli", "cline",
        "opencode", "pi", "openclaw", "hermes",
    ],
    "Frameworks and protocols": ["chat-sdk", "cloudflare-think", "mcp"],
    "Voice & video": ["pipecat", "livekit", "elevenlabs"],
    "Build it yourself": ["your-own-backend", "agent-prompt", "skills"],
}
PROVIDERS = {
    "Brains": ["Grok", "OpenAI Realtime", "Gemini Live"],
    "Voices": ["ElevenLabs", "Cartesia"],
    "Avatars": ["Simli", "LemonSlice"],
    "Character": ["Rive"],
}
FENCE = re.compile(r"^```([^\n]*)\n(.*?)^```[ \t]*$", re.M | re.S)


def read(path):
    return (ROOT / path).read_text()


def integrations():
    config = json.loads(read("docs.json"))
    return next(group for tab in config["navigation"]["tabs"]
                for group in tab.get("groups", [])
                if group.get("group") == "Integrations")


class IntegrationArchitecture(unittest.TestCase):
    def test_directory_has_exactly_the_approved_categories(self):
        # Shipped 07451be: directory owns the grouping, sidebar links its overview.
        self.assertEqual(integrations()["pages"], ["integrations/index"])

    def test_cards_match_each_category_and_use_local_brand_art(self):
        text = read("integrations/index.mdx")
        for group, pages in GROUPS.items():
            section = text.split(f"## {group}\n", 1)[1].split("\n## ", 1)[0]
            self.assertIn("<Columns ", section)
            cards = re.findall(r"<Card\b([^>]+?)/?>", section)
            self.assertEqual(len(cards), len(pages), group)
            for card, page in zip(cards, pages):
                self.assertIn(f'href="/integrations/{page}"', card)
                logo = re.search(r'icon="(/[^"]+)"', card)
                if group == "Build it yourself":
                    self.assertIsNone(logo, f"{page}: preserve the shipped no-logo row")
                    continue
                self.assertIsNotNone(logo, f"{page}: use real brand art, not a placeholder")
                asset = ROOT / logo[1].lstrip("/")
                self.assertTrue(asset.is_file(), str(asset))
                self.assertIn(asset.suffix, {".svg", ".png", ".webp"})
        self.assertNotIn('href="/integrations/grok"', text)
        self.assertNotIn('href="/integrations/xai-grok"', text)

    def test_mcp_logo_and_separate_app_blue_remain_present(self):
        self.assertIn('icon="/images/brands/mcp.svg"', read("integrations/index.mdx"))
        self.assertIn('viewBox="0 0 180 180"', read("images/brands/mcp.svg"))
        self.assertEqual(json.loads(read("docs.json"))["colors"]["primary"].lower(), "#006be6")
        self.assertIn("--relay-brand-blue: #0b75ff", read("style.css"))
        self.assertIn("--app-blue: var(--relay-brand-blue)", read("style.css"))

    def test_provider_matrices_separate_framework_support_from_relay_examples(self):
        classifications = {
            "pipecat": {
                "Grok": "Relay recipe", "OpenAI Realtime": "Supported by Pipecat",
                "Gemini Live": "Supported by Pipecat", "ElevenLabs": "Relay recipe",
                "Cartesia": "Relay example", "Simli": "Relay example",
                "LemonSlice": "Supported by Pipecat", "Rive": "RelayRiveProcessor",
            },
            "livekit": {
                "Grok": "Supported by LiveKit", "OpenAI Realtime": "Supported by LiveKit",
                "Gemini Live": "Relay example", "ElevenLabs": "Supported by LiveKit",
                "Cartesia": "Supported by LiveKit", "Simli": "Supported by LiveKit",
                "LemonSlice": "Supported by LiveKit", "Rive": "RelayRive",
            },
        }
        for framework in ("pipecat", "livekit"):
            text = read(f"integrations/{framework}.mdx")
            matrix = text.split("## Providers\n", 1)[1].split("\n## ", 1)[0]
            for role, providers in PROVIDERS.items():
                for provider in providers:
                    row = re.search(
                        rf"(?m)^\| {role} \| {re.escape(provider)} \| (.+) \|$", matrix,
                    )
                    self.assertIsNotNone(row, f"{framework}: missing {provider}")
                    self.assertIn(classifications[framework][provider], row[1])
                    if framework == "livekit" and role == "Avatars":
                        self.assertIn("Uses a LiveKit room", row[1])
                        self.assertIn("Relay-specific wiring is not shown here", row[1])
            self.assertIn("/calls/rive", matrix)
            self.assertNotIn("xAI Grok", text)
        self.assertIn("RelayTransport", read("integrations/pipecat.mdx"))
        self.assertIn("RelayLiveKitCall", read("integrations/livekit.mdx"))
        self.assertIn("room", read("integrations/livekit.mdx"))

    def test_every_original_recipe_snippet_survives_in_pipecat(self):
        baseline = json.loads(read("scripts/integration-content-baseline.json"))
        digest_key = ("production_sha256" if read(".docs-target").strip() == "production"
                      else "sha256")
        # Hash body only, as the inherited manifest did; fence titles are presentation.
        actual = Counter(hashlib.sha256(body.encode()).hexdigest()
                         for _, body in FENCE.findall(read(baseline["destination"])))
        expected = Counter(block[digest_key] for blocks in baseline["pages"].values()
                           for block in blocks)
        for digest, count in expected.items():
            self.assertGreaterEqual(actual[digest], count, f"missing original snippet {digest}")
        page = read("integrations/pipecat.mdx")
        for concept in (
            "## Grok", "Grok Imagine", "RELAY_STATE_PATH", "stay_silent",
            "Retry-After", "FULL sync", "three deliveries", "ten minutes",
            "elevenlabs-voice-agent", "elevenlabs-agents-call", "pcm_16000",
            "SOYHLrjzK2X1ezoPC6cr", "paid_plan_required",
        ):
            self.assertIn(concept, page)

    def test_every_original_recipe_paragraph_and_table_survives(self):
        baseline = json.loads(read("scripts/integration-content-baseline.json"))
        actual = re.sub(r"\s+", " ", read(baseline["destination"]))
        for source, paragraphs in baseline["prose"].items():
            for paragraph in paragraphs:
                expected = paragraph.get("reframed", paragraph["original"])
                if read(".docs-target").strip() == "production":
                    expected = production_text(expected)
                self.assertIn(re.sub(r"\s+", " ", expected), actual,
                              f"{source}: lost paragraph/table: {expected}")

    def test_call_and_chat_recipes_select_the_documented_environment(self):
        text = read("integrations/pipecat.mdx")
        expected = "https://api.staging.relayapp.im"
        if read(".docs-target").strip() == "production":
            expected = production_text(expected)
        calls, imagine = text.split("#### Send pictures and videos with Grok Imagine", 1)
        self.assertIn(f"export RELAY_BASE_URL={expected}", calls)
        self.assertIn(f"export RELAY_API_URL={expected}", imagine)
        self.assertLess(imagine.index("export RELAY_API_URL="),
                        imagine.index("REFERENCE_IMAGE=./character.png npm start"))

    def test_grok_routes_land_on_the_provider_example(self):
        redirects = {item["source"]: item["destination"]
                     for item in json.loads(read("docs.json"))["redirects"]}
        for route in ("/integrations/xai-grok", "/integrations/grok"):
            self.assertEqual(redirects[route], "/integrations/pipecat#grok")
        self.assertFalse((ROOT / "integrations/xai-grok.mdx").exists())
        for page in (ROOT / "integrations").glob("*.mdx"):
            self.assertNotIn("xAI Grok", page.read_text())
            self.assertNotIn("](/integrations/xai-grok)", page.read_text())

    def test_elevenlabs_owns_the_direct_bridge_not_the_voice_provider(self):
        text = read("integrations/elevenlabs.mdx")
        opening = text.split("---", 2)[2].split("\n## ", 1)[0]
        for concept in ("direct", "@relaymessenger/elevenlabs", "WebSocket"):
            self.assertIn(concept, opening)
        self.assertIn("ElevenLabsCall.connect", text)
        self.assertIn("packages/elevenlabs", text)
        self.assertIn("/integrations/pipecat#elevenlabs-voices-and-agents", text)
        self.assertNotIn("ElevenLabsTTSService(", text)
        self.assertNotIn("RelayTransport(", text)
        # Read-back of the published staging artifact is recorded by the
        # registry refresh, rather than freezing an old "coming soon" claim.
        versions = json.loads(read("versions.json"))
        bridge = versions["npm"]["@relaymessenger/elevenlabs"]
        self.assertIn(bridge["staging"], bridge["integrity"])
        install = "npm install @relaymessenger/sdk@staging @relaymessenger/elevenlabs@staging"
        if read(".docs-target").strip() == "production":
            install = production_text(install)
        for page in (text, read("calls/elevenlabs.mdx")):
            self.assertNotIn("coming soon", page.lower())
            self.assertIn(install, page)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path)
    args, remaining = parser.parse_known_args()
    if args.root:
        ROOT = args.root.resolve()
    unittest.main(argv=[__file__, *remaining])
