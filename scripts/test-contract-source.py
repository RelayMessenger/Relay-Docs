#!/usr/bin/env python3
"""Pin the independently read Server input, not a checksum derived from Docs."""
import hashlib
import json
import os
import re
import tempfile
import subprocess
from unittest.mock import patch
import unittest
from pathlib import Path

from origins import target
from contract_source import verify_contract_source

ROOT = Path(__file__).resolve().parents[1]
# Canonical request lifecycle, scoped lookup, and fixed agent admission Server source.
# Retains the merged activity and live call-marker shapes. The selection
# descriptions now carry the shipped sheet flow; the wire shapes are untouched.
# Location sharing: POST /v1/chats/{chatId}/location/request, GET /v1/chats/{chatId}/location, the location_request and location parts, location.sharing.* webhooks.
# Contact cards carry is_verified; agent contact resources carry creator.
# A2UI cards: the data part, a2ui_errors, targeted taps; the place part; GET /v1/me.
# Agent reach (Server #380): Always Allow and Never Allow lists at /v1/access; error 2031.
# Communities and tasks between agents (Server #381-#388): /v1/communities, PATCH /v1/me, /v1/tasks, task.* events.
# Community feed and About box (Server #391, #394): posts, comments, upvotes, community.* events; A2A door answers with a Message (Server #392).
UPSTREAM_COMMIT = "0ccaba4b78c43101da294442eee0dbd76676fc46"
UPSTREAM_STAGING_COMMIT = "0ccaba4b78c43101da294442eee0dbd76676fc46"
UPSTREAM_SIZE = 325602
UPSTREAM_SHA256 = "890cabaab8fd17cfb7cce03df0c9b7e532b51ff1d52f73c186d54083f1ba5766"
CANDIDATE_RECORD = {
    "status": "local-candidate-not-published",
    "repository": "Relay-SDK",
    "commit": "fa869724ae89128074388c4c0f130e1d063024b2",
    "path": "contracts/relay-v1-openapi.yaml",
    "sha256": UPSTREAM_SHA256,
    "note": "Fixture: a committed local candidate carrying the released bytes.",
    "source_state": "committed",
}


class ContractSourceTests(unittest.TestCase):
    def test_reverted_agent_admission_fields_are_absent_from_public_schemas(self):
        canonical = (ROOT / "api-reference/openapi.yaml").read_text()
        # Person-setting descriptions remain; the reverted public field does not.
        self.assertNotRegex(canonical, r"(?m)^\s+message_requests_from:")
        # Server #379 brought back GET /v1/me as the agent's owner, not an admission field.
        self.assertIn("      operationId: getMe\n", canonical)

    def test_public_contact_lookup_uses_only_the_approved_post_route(self):
        canonical = (ROOT / "api-reference/openapi.yaml").read_text()
        # The lookup path item ends where the next top-level path begins.
        lookup = re.split(
            r"^  /v1/", canonical.split("  /v1/contacts/lookup:\n", 1)[1],
            maxsplit=1, flags=re.M)[0]
        self.assertTrue(lookup.startswith("    post:\n"))
        self.assertIn("      operationId: lookupContact\n", lookup)
        # Server #336 folded the public directory search into this route.
        wrapped = " ".join(lookup.split())
        self.assertIn("Send a handle to look up one active contact", wrapped)
        self.assertIn(
            "Send a task instead to find the public agents whose name, "
            "subtitle, description or skills match it, verified agents first",
            wrapped,
        )
        self.assertIn("                - handle\n", lookup)
        self.assertIn('                    $ref: "#/components/schemas/ContactLookup"', lookup)
        self.assertNotIn("  /v1/contacts:\n", canonical)
        self.assertNotIn("    get:\n", lookup)
        routes = json.loads((ROOT / "scripts/api-page-paths.json").read_text())
        self.assertEqual(routes["lookupContact"]["endpoint"], "POST /v1/contacts/lookup")

    def test_public_directory_and_rating_routes_are_registered(self):
        canonical = (ROOT / "api-reference/openapi.yaml").read_text()
        routes = json.loads((ROOT / "scripts/api-page-paths.json").read_text())
        # Server #336 and #337: the directory and an agent's ratings are public;
        # rating and removing a rating carry the caller's token.
        for operation, endpoint, security in (
            ("listDirectory", "GET /v1/directory", "      security: []\n"),
            ("rateAgent", "PUT /v1/contacts/{handle}/rating",
             "      security:\n        - BearerAuth: []\n"),
            ("deleteAgentRating", "DELETE /v1/contacts/{handle}/rating",
             "      security:\n        - BearerAuth: []\n"),
            ("listAgentRatings", "GET /v1/contacts/{handle}/ratings",
             "      security: []\n"),
        ):
            method, path = endpoint.split(" ", 1)
            block = re.split(
                r"^  /v1/", canonical.split(f"  {path}:\n", 1)[1],
                maxsplit=1, flags=re.M)[0]
            operation_block = block.split(f"    {method.lower()}:\n", 1)[1]
            self.assertTrue(operation_block.startswith(f"      operationId: {operation}\n"))
            self.assertIn(security, operation_block)
            self.assertEqual(routes[operation]["endpoint"], endpoint)
        navigation = json.loads((ROOT / "docs.json").read_text())
        api = next(tab for tab in navigation["navigation"]["tabs"]
                   if tab["tab"] == "API Reference")
        contacts = next(group for group in api["groups"] if group["group"] == "Contacts")
        for endpoint in ("GET /v1/directory", "PUT /v1/contacts/{handle}/rating",
                         "DELETE /v1/contacts/{handle}/rating",
                         "GET /v1/contacts/{handle}/ratings"):
            self.assertIn(endpoint, contacts["pages"])

    def test_request_lifecycle_description_does_not_expose_private_fields(self):
        canonical = (ROOT / "api-reference/openapi.yaml").read_text()
        normalized = " ".join(canonical.split())
        self.assertIn(
            "Removing a Contact keeps an existing conversation in Chats until "
            "another incoming message makes it a message request.",
            normalized,
        )
        for field in ("is_request", "request_expires_at", "request_sender_id"):
            self.assertNotRegex(canonical, rf"(?m)^\s+{field}:")

    def test_combined_contract_keeps_live_call_markers(self):
        canonical = (ROOT / "api-reference/openapi.yaml").read_text()
        marker = canonical.split("    CallMarker:\n", 1)[1].split("    SystemEventParty:\n", 1)[0]
        for field in ("status", "answered_at", "ended_at", "from", "to"):
            self.assertIn(f"        - {field}\n", marker)
        self.assertIn("          description: The Call this event marks. Null unless type is call.", canonical)
        for name in ("calls/index.mdx", "chats/history.mdx", "messages/message-details.mdx",
                     "api-reference/resources/messages/overview.mdx"):
            self.assertNotIn("call_ended", (ROOT / name).read_text())
        self.assertIn('system_event.type: "call"', (ROOT / "calls/index.mdx").read_text())

    def test_chat_activity_guide_and_generated_navigation_match_the_contract(self):
        canonical = (ROOT / "api-reference/openapi.yaml").read_text()
        activity_path = canonical.split("  /v1/chats/{chatId}/activity:\n", 1)[1].split(
            "  /v1/chats/{chatId}/typing:\n", 1)[0]
        routes = json.loads((ROOT / "scripts/api-page-paths.json").read_text())
        for method, operation in (("GET", "getActivity"), ("PUT", "setActivity"), ("DELETE", "clearActivity")):
            self.assertIn(f"operationId: {operation}", activity_path)
            self.assertEqual(routes[operation]["endpoint"], f"{method} /v1/chats/{{chatId}}/activity")
        self.assertIn("x-max-graphemes: 21", canonical)
        self.assertIn("x-max-utf8-bytes: 1024", canonical)
        self.assertIn("name: activity_id\n          in: query", activity_path)
        guide = (ROOT / "chats/activity.mdx").read_text()
        for name in ("getActivity", "setActivity", "clearActivity"):
            self.assertIn(f"relay.chats.{name}(", guide)
        groups = re.findall(r"<CodeGroup>(.*?)</CodeGroup>", guide, re.S)
        self.assertEqual(len(groups), 4)
        for group in groups:
            self.assertLess(group.index("```typescript TypeScript SDK"), group.index("```bash cURL"))
        for value in ("60 seconds", "90 seconds", "21 visible characters", "1024 UTF-8 bytes",
                      "activity_id: activityId", "activity?activity_id=$ACTIVITY_ID", "`409`", "`204`"):
            self.assertIn(value, guide)
        for path in ("skill.md", ".mintlify/skills/relay/SKILL.md"):
            prompt = (ROOT / path).read_text()
            self.assertIn("not an agent webhook", prompt)
            self.assertIn("Do not add polling", prompt)
            self.assertIn("Do not create a `Typing` activity", prompt)
        events = (ROOT / "events/index.mdx").read_text()
        self.assertNotIn("chat.activity.updated", events)

    def test_all_interactive_overview_cards_are_icon_free(self):
        overview = (ROOT / "interactions/index.mdx").read_text()
        cards = re.findall(r"<Card\b[^>]*>", overview, re.S)
        self.assertTrue(cards, "Overview must contain component cards")
        for card in cards:
            with self.subTest(card=card):
                self.assertNotRegex(card, r"\sicon(?:\s|=|/?>)",
                                    "Every interaction card must omit icon")

    def test_selection_local_review_preserves_production_facing_copy(self):
        overview = (ROOT / "interactions/index.mdx").read_text()
        self.assertIn('<Card title="Selection" href="/interactions/selection">', overview)
        selection = (ROOT / "interactions/selection.mdx").read_text()
        for page in [ROOT / "interactions/index.mdx",
                     ROOT / "interactions/selection.mdx",
                     *(ROOT / "integrations").glob("*.mdx")]:
            self.assertNotIn("coming soon", page.read_text().lower(), page)
        self.assertIn("literal `• `", selection)
        self.assertIn("exact selected source labels joined with `, `", selection)
        self.assertNotIn("**Clear**", selection)
        # The contract is a published pin; no local candidate record remains.
        self.assertFalse((ROOT / "scripts/local-contract-source.json").exists())

    def test_selection_preview_and_response_share_canonical_bullet_text(self):
        source = (ROOT / "interactions/selection.mdx").read_text()
        groups = re.findall(r"<Tabs\b[^>]*>(.*?)</Tabs>", source, re.S)
        send = next(group for group in groups if '<Tab title="JSON">' in group)
        received = next(group for group in groups if '<Tab title="What you receive">' in group)
        request = json.loads(re.search(r"```json\s*\n(.*?)```", send, re.S)[1])
        response = json.loads(re.search(r"```json\s*\n(.*?)```", received, re.S)[1])["data"]
        options = request["message"]["parts"][1]["options"]
        values = response["parts"][1]["selected_values"]
        canonical = "\n".join("• " + option["label"] for option in options if option["value"] in values)
        self.assertEqual(response["parts"][0]["value"], canonical)
        self.assertEqual(response["reply_to"]["part_index"], 1)
        preview = re.search(r'received=\{("(?:\\.|[^"\\])*")\}', received)
        self.assertIsNotNone(preview)
        self.assertEqual(json.loads(preview[1]), canonical)
        preview_options = re.search(r'options=\{(\[.*?\])\}', send, re.S)
        self.assertEqual(json.loads(preview_options[1]), options)
        title = re.search(r'<SelectionPreview[^>]*? title=("(?:\\.|[^"\\])*")', send)
        self.assertEqual(json.loads(title[1]), request["message"]["parts"][1]["title"])

    def test_selection_guide_keeps_runtime_summary_brief(self):
        selection = (ROOT / "interactions/selection.mdx").read_text()
        self.assertNotIn("### Choose and submit", selection)
        self.assertNotIn("## Selection fields", selection)
        runtime = selection.split("## Send from a runtime\n", 1)[1].split("\n## ", 1)[0]
        self.assertLess(len(runtime.split()), 100)
        self.assertNotIn("\n|", runtime)
        self.assertNotIn("```", runtime)
        self.assertIn("/integrations/index", runtime)
        self.assertIn("selected_values", selection)
        self.assertIn("reply_to", selection)

    def test_message_parts_links_to_interactions(self):
        parts = (ROOT / "messages/parts.mdx").read_text()
        section = parts.split("## Add interactions\n", 1)[1].split("\n## ", 1)[0]
        self.assertIn("[Interactions](/interactions/index)", section)
        self.assertLess(len(section.split()), 60)
        self.assertNotIn("buttons", section.lower())
        self.assertNotIn("selections", section.lower())
        self.assertIn("`parts`", section)

    def test_canonical_bytes_equal_pinned_upstream(self):
        canonical = (ROOT / "api-reference/openapi.yaml").read_bytes()
        self.assertEqual(len(canonical), UPSTREAM_SIZE)
        verify_contract_source(ROOT, UPSTREAM_SHA256)

    def test_committed_source_verifies_immutable_blob_not_dirty_worktree(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "docs"
            sdk = Path(directory) / "sdk"
            (root / "scripts").mkdir(parents=True)
            (root / "api-reference").mkdir()
            (sdk / ".git").mkdir(parents=True)
            (sdk / "contracts").mkdir()
            canonical = (ROOT / "api-reference/openapi.yaml").read_bytes()
            (root / "api-reference/openapi.yaml").write_bytes(canonical)
            (sdk / "contracts/relay-v1-openapi.yaml").write_bytes(b"unrelated later worktree edit")
            record = dict(CANDIDATE_RECORD)
            self.assertEqual(record["source_state"], "committed")
            record_path = root / "scripts/local-contract-source.json"
            record_path.write_text(json.dumps(record))
            with patch("contract_source.subprocess.check_output", return_value=canonical) as show:
                verify_contract_source(root, UPSTREAM_SHA256)
                show.assert_called_once_with(
                    ["git", "show", f"{record['commit']}:{record['path']}"], cwd=sdk)
            with patch("contract_source.subprocess.check_output", return_value=b"wrong committed bytes"):
                with self.assertRaisesRegex(AssertionError, "SDK checkpoint differs"):
                    verify_contract_source(root, UPSTREAM_SHA256)
            record["checkpoint_sha256"] = UPSTREAM_SHA256
            record_path.write_text(json.dumps(record))
            with self.assertRaisesRegex(AssertionError, "Committed provenance must pin its own blob"):
                verify_contract_source(root, UPSTREAM_SHA256)
            record.pop("checkpoint_sha256")
            record["source_state"] = "unchecked"
            record_path.write_text(json.dumps(record))
            with self.assertRaisesRegex(AssertionError, "Invalid local source state"):
                verify_contract_source(root, UPSTREAM_SHA256)

    def test_local_candidate_rejects_modified_bytes_and_release_relabeling(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "scripts").mkdir()
            (root / "api-reference").mkdir()
            record = dict(CANDIDATE_RECORD)
            record_file = root / "scripts/local-contract-source.json"
            record_file.write_text(json.dumps(record))
            contract = root / "api-reference/openapi.yaml"
            original = (ROOT / "api-reference/openapi.yaml").read_bytes()
            contract.write_bytes(original)
            verify_contract_source(root, UPSTREAM_SHA256)
            contract.write_bytes(original + b"\n# unreviewed drift\n")
            with self.assertRaises(AssertionError):
                verify_contract_source(root, UPSTREAM_SHA256)
            contract.write_bytes(original)
            record["status"] = "published"
            record_file.write_text(json.dumps(record))
            with self.assertRaises(AssertionError):
                verify_contract_source(root, UPSTREAM_SHA256)

    def test_buttons_are_text_only_and_a_tap_is_the_label_as_text(self):
        canonical = (ROOT / "api-reference/openapi.yaml").read_text()
        items = canonical.split("    ButtonItem:\n", 1)[1].split("    ButtonsPart:\n", 1)[0]
        self.assertNotIn("image_url", items)
        self.assertNotIn("          id:", items)
        self.assertNotIn("button_reply", canonical)
        self.assertIn("The only reply it accepts is a tap", canonical)
        parts = (ROOT / "messages/parts.mdx").read_text()
        self.assertNotIn("button_reply", parts)
        self.assertIn("/interactions/index", parts)
        buttons = (ROOT / "interactions/buttons.mdx").read_text()
        self.assertNotIn("image_url", buttons)
        self.assertNotIn("button_reply", buttons)
        self.assertIn('"parts": [{"type":"text","value":"Jupiter"}]', buttons)
        for path in ("skill.md", ".mintlify/skills/relay/SKILL.md"):
            skill = (ROOT / path).read_text()
            self.assertIn("not ordinary replies or reactions", skill)
            self.assertNotIn("button_reply", skill)
        full = (ROOT / "llms-full.txt").read_text()
        self.assertNotIn("button_reply", full)

    def assert_buttons_previews_match_requests(self, source):
        requests = 0
        buttons_only = 0
        with_text = 0
        for group in re.findall(r"<Tabs\b[^>]*>(.*?)</Tabs>", source, re.S):
            tabs = dict(re.findall(r'<Tab title="([^"]+)">\s*(.*?)</Tab>', group, re.S))
            if "JSON" not in tabs:
                continue
            requests += 1
            blocks = re.findall(r"```json\s*\n(.*?)```", tabs["JSON"], re.S)
            self.assertEqual(len(blocks), 1, "Each request needs one JSON payload")
            parts = json.loads(blocks[0])["message"]["parts"]
            buttons = [part for part in parts if part["type"] == "buttons"]
            text = [part["value"] for part in parts if part["type"] == "text"]
            self.assertEqual(len(buttons), 1)
            self.assertLessEqual(len(text), 1, "Preview supports one text part")
            previews = re.findall(r"<ButtonsPreview\b(.*?)/>", tabs.get("Preview", ""), re.S)
            self.assertEqual(len(previews), 1, "Each request needs its own preview")
            preview = previews[0]
            items_prop = re.search(r"\bitems\s*=\s*\{", preview)
            self.assertIsNotNone(items_prop, "Request preview must include items")
            items, end = json.JSONDecoder().raw_decode(preview[items_prop.end():].lstrip())
            self.assertTrue(preview[items_prop.end():].lstrip()[end:].lstrip().startswith("}"))
            self.assertEqual(items, buttons[0]["items"], "Preview items differ from request")
            text_prop = re.search(r"\btext\s*=", preview)
            if text:
                with_text += 1
                self.assertIsNotNone(text_prop, "Request text is omitted from preview")
                # Text props use JSON double-quoted strings, just like the payload.
                value, _ = json.JSONDecoder().raw_decode(preview[text_prop.end():].lstrip())
                self.assertEqual(value, text[0], "Preview text differs from request")
            else:
                buttons_only += 1
                self.assertIsNone(text_prop, "Buttons-only preview must omit the text prop")
                self.assertEqual(parts, buttons, "Buttons-only example must contain only buttons")
        self.assertGreaterEqual(requests, 4, "Keep plain, URL, mixed, and buttons-only examples")
        self.assertGreater(with_text, 0, "Include a request with text")
        self.assertGreater(buttons_only, 0, "Include a valid buttons-only request")

    def test_buttons_previews_match_adjacent_requests(self):
        self.assert_buttons_previews_match_requests(
            (ROOT / "interactions/buttons.mdx").read_text())

    def test_chat_previews_draw_the_adjacent_json(self):
        # Each chat preview reads its words from the payload in its own JSON
        # tab, and every picture it draws ships in the repository.
        snippet = (ROOT / "snippets/chat-preview.jsx").read_text()
        scenes = set(re.findall(r'scene === "([a-z-]+)"', snippet))
        for path in re.findall(r'"/(images/chat/[^"]+)"', snippet):
            self.assertTrue((ROOT / path).is_file(), path)
        seen = set()
        for page in sorted(ROOT.glob("*/*.mdx")):
            source = page.read_text()
            if "<ChatPreview" not in source:
                continue
            self.assertIn('import { ChatPreview } from "/snippets/chat-preview.jsx";', source, page)
            groups = [g for g in re.findall(r"<Tabs\b[^>]*>(.*?)</Tabs>", source, re.S) if "<ChatPreview" in g]
            self.assertEqual(len(groups), source.count("<ChatPreview"), page)
            for group in groups:
                tabs = dict(re.findall(r'<Tab title="([^"]+)">\s*(.*?)</Tab>', group, re.S))
                self.assertEqual(list(tabs), ["Preview", "JSON"], page)
                blocks = re.findall(r"```json\s*\n(.*?)```", tabs["JSON"], re.S)
                self.assertEqual(len(blocks), 1, page)
                scene = re.search(r'scene="([a-z-]+)"', tabs["Preview"])[1]
                self.assertIn(scene, scenes, page)
                start = re.search(r"\bjson=\{", tabs["Preview"]).end()
                drawn, _ = json.JSONDecoder().raw_decode(tabs["Preview"][start:].lstrip())
                self.assertEqual(drawn, json.loads(blocks[0]), f"{page}: preview differs from its JSON tab")
                seen.add(scene)
        self.assertEqual(seen, scenes, "Every chat scene is used on a page")

    def test_reply_preview_answers_a_photo_sent_alone(self):
        # The example reply names part 0 of a message that holds only the
        # photo, so the app draws the photo once, joined by its reply line,
        # with no quote (ReplyLinePlanner.swift: adjacent rows join).
        source = (ROOT / "messages/replies.mdx").read_text()
        request = json.loads(re.search(r"```json\s*\n(.*?)```", source, re.S)[1])
        self.assertEqual(request["message"]["reply_to"]["part_index"], 0)
        self.assertEqual(request["message"]["parts"], [{"type": "text", "value": "Where was this taken?"}])
        snippet = (ROOT / "snippets/chat-preview.jsx").read_text()
        scene = snippet.split('scene === "replies"', 1)[1].split("} else if (scene ===", 1)[0]
        self.assertNotIn("chatp-quote", scene)
        self.assertEqual(scene.count("<img"), 1, "The photo is drawn once")
        self.assertIn("chatp-replyline", scene)

    def test_chat_preview_balloons_wear_the_apps_tails(self):
        # A photo, video or document alone wears the tail on its sender's
        # side (RelayMediaRowLayout.swift: "individual photos and videos wear
        # the bubble tail"); the agent's link is incoming, with no outline;
        # the contact card's picture leads (owner ruling, 2026-09-26).
        snippet = (ROOT / "snippets/chat-preview.jsx").read_text()
        def scene(name):
            return snippet.split(f'scene === "{name}"', 1)[1].split("} else if (scene ===", 1)[0]
        self.assertIn('tailedMedia("out", PHOTO_WIDTH, PHOTO_H', scene("replies"))
        self.assertIn("tailedMedia(side, PHOTO_WIDTH, photoH", scene("attachment"))
        self.assertIn('const side = typed ? "out" : "in";', scene("attachment"))
        self.assertIn('{last ? tail("in") : null}', scene("document"))
        link = scene("link")
        self.assertIn('row("in"', link)
        self.assertIn('{tail("in")}', link)
        self.assertIn("/images/chat/link-relayapp-og.png", link)
        self.assertTrue((ROOT / "images/chat/link-relayapp-og.png").is_file())
        self.assertNotIn("chatp-doc-clip::after", snippet, "No hairline ring on a tailed card")
        # State switchers are one segmented control naming every state, at the
        # block's bottom edge, never a lone chip (the Payments preview's shape).
        self.assertNotIn("const toggle = (pressed", snippet)
        for name, options in (("attachment", '[[false, "Photo"], [true, "Video"]]'),
                              ("receipts", '[[false, "Delivered"], [true, "Read"]]'),
                              ("typing", '[[true, "Typing"], [false, "Stopped"]]')):
            self.assertIn("segmented(", scene(name))
            self.assertIn(options, scene(name))
        card = scene("contact-card")
        self.assertLess(card.index("chatp-card-avatar"), card.index("chatp-card-name"))
        self.assertLess(card.index("chatp-card-name"), card.index("{chevron}"))

    def test_cards_previews_draw_the_adjacent_json(self):
        # Each live card preview draws exactly the messages in its JSON tab. An
        # update preview replays the page's first card, then the update; the
        # ride preview's reply is that same update, applied after the tap.
        source = (ROOT / "interactions/cards.mdx").read_text()
        https = [json.loads(body)["message"]["parts"][0]["data"]
                 for body in re.findall(r"-d '(\{.*?\})'\n```", source, re.S)]
        self.assertEqual(len(https), 2, "Keep the send and update HTTPS samples")

        def prop(preview, name):
            match = re.search(r"\b" + name + r"=\{", preview)
            if match is None:
                return None
            value, _ = json.JSONDecoder().raw_decode(preview[match.end():].lstrip())
            return value

        previews = []
        for group in re.findall(r"<Tabs\b[^>]*>(.*?)</Tabs>", source, re.S):
            tabs = dict(re.findall(r'<Tab title="([^"]+)">\s*(.*?)</Tab>', group, re.S))
            if "<A2uiPreview" not in tabs.get("Preview", ""):
                continue
            self.assertIn("JSON", tabs, "Each card preview needs its JSON tab")
            blocks = re.findall(r"```json\s*\n(.*?)```", tabs["JSON"], re.S)
            self.assertEqual(len(blocks), 1)
            data = json.loads(blocks[0])["message"]["parts"][0]["data"]
            preview = tabs["Preview"]
            messages = prop(preview, "messages")
            self.assertEqual(messages[-len(data):], data, "Preview differs from its JSON tab")
            if messages != data:
                self.assertEqual(messages[:-len(data)], https[0], "An update preview starts from the sent card")
            for local in (prop(preview, "media") or {}).values():
                self.assertTrue((ROOT / local.lstrip("/")).is_file(), local)
            previews.append((data, prop(preview, "reply")))
        self.assertGreaterEqual(len(previews), 2)
        self.assertEqual(previews[0][0], https[0], "The first preview is the ride card that is sent")
        # A preview's replies are keyed by the tapped action's name, and each
        # answers a Button the card really draws.
        def events(messages):
            return {c["action"]["event"]["name"] for m in messages if "updateComponents" in m
                    for c in m["updateComponents"]["components"] if "action" in c}
        # The ride preview answers the pick the reader made: its Comfort reply
        # to review_ride is the documented update, and its UberX reply is that
        # same update with only the ride, its label, and its price changed.
        replies = previews[0][1]
        self.assertEqual(sorted(replies), ["request_ride", "review_ride"])
        self.assertIn("review_ride", events(https[0]))
        self.assertIn("request_ride", events(https[1]))
        review = replies["review_ride"]
        self.assertEqual(sorted(review), ["comfort", "uberx"])
        self.assertEqual(review["comfort"], https[1], "The ride preview's reply is the documented update")
        uberx = json.loads(json.dumps(https[1]).replace("Request Comfort for $51", "Request UberX for $42")
                           .replace('"ride": "comfort"', '"ride": "uberx"'))
        self.assertNotEqual(uberx, https[1])
        self.assertEqual(review["uberx"], uberx, "The UberX reply mirrors the documented update")
        # The commit's tap, request_ride, gets the next update the update's
        # JSON tab documents: the ride is booked and the Button is gone.
        update_group = [g for g in re.findall(r"<Tabs\b[^>]*>(.*?)</Tabs>", source, re.S)
                        if "<A2uiPreview" in g and "Request Comfort for $51 to book it" in g][0]
        update_tabs = dict(re.findall(r'<Tab title="([^"]+)">\s*(.*?)</Tab>', update_group, re.S))
        following = re.search(r"```json The next update, after request_ride\s*\n(.*?)```", update_tabs["JSON"], re.S)
        self.assertIsNotNone(following, "The update's JSON tab shows the next update")
        booked = json.loads(following[1])["message"]["parts"][0]["data"]
        self.assertEqual(events(booked), set(), "The booked card has no Button left")
        self.assertEqual(replies["request_ride"]["comfort"], booked, "The ride preview books with the documented update")
        booked_uberx = json.loads(json.dumps(booked).replace("Your Comfort ride", "Your UberX ride")
                                  .replace("in 6 minutes", "in 4 minutes"))
        self.assertNotEqual(booked_uberx, booked)
        self.assertEqual(replies["request_ride"]["uberx"], booked_uberx, "The UberX booking mirrors it")
        self.assertIn((https[1], {"request_ride": booked}), previews,
                      "The update has its own preview, and its Button books the ride")
        # Every Button tap does something visible, as in the app: the Button
        # spins and the card locks until the agent answers.
        a2ui = (ROOT / "snippets/a2ui-preview.jsx").read_text()
        tap = a2ui.split("const tap = (cid, scope) => {", 1)[1].split("\n  };", 1)[0]
        self.assertIn("setPending(key);", tap)
        self.assertLess(tap.index("setPending(key);"), tap.index("const answer = reply && reply[event.name];"))
        self.assertIn("{spins ? spinner : null}", a2ui)
        self.assertIn('"a2-card" + (pending ? " is-locked" : "")', a2ui)
        # The ride card's JSON tab also shows the tap the preview produces for
        # the default pick, and the Preview tab shows no JSON at all.
        ride_group = [g for g in re.findall(r"<Tabs\b[^>]*>(.*?)</Tabs>", source, re.S) if "<A2uiPreview" in g][0]
        ride_tabs = dict(re.findall(r'<Tab title="([^"]+)">\s*(.*?)</Tab>', ride_group, re.S))
        self.assertNotIn("```", ride_tabs["Preview"])
        received = re.search(r"```json Your agent receives\s*\n(.*?)```", ride_tabs["JSON"], re.S)
        self.assertIsNotNone(received, "The ride card's JSON tab shows what the agent receives")
        action = json.loads(received[1])[0]["action"]
        comps = {c["id"]: c for m in https[0] if "updateComponents" in m for c in m["updateComponents"]["components"]}
        model = [m["updateDataModel"]["value"] for m in https[0] if "updateDataModel" in m][0]
        event = comps[action["sourceComponentId"]]["action"]["event"]
        self.assertEqual(action["name"], event["name"])
        self.assertEqual(action["surfaceId"], https[0][0]["createSurface"]["surfaceId"])
        self.assertEqual(action["context"], {k: model[v["path"].lstrip("/")] for k, v in event["context"].items()})
        snippet = (ROOT / "snippets/a2ui-preview.jsx").read_text()
        self.assertNotIn("<pre", snippet, "A Preview tab never shows code")
        self.assertFalse((ROOT / "images/cards/choice-picker-card.jpg").exists())

    def test_payment_preview_draws_the_adjacent_json(self):
        # The live Pay card draws exactly the part in its JSON tab, and that
        # part is the one the page's 202 response stores.
        source = (ROOT / "interactions/payments.mdx").read_text()
        previews = 0
        for group in re.findall(r"<Tabs\b[^>]*>(.*?)</Tabs>", source, re.S):
            tabs = dict(re.findall(r'<Tab title="([^"]+)">\s*(.*?)</Tab>', group, re.S))
            if "<PaymentPreview" not in tabs.get("Preview", ""):
                continue
            previews += 1
            self.assertIn("JSON", tabs, "The payment preview needs its JSON tab")
            blocks = re.findall(r"```json\s*\n(.*?)```", tabs["JSON"], re.S)
            self.assertEqual(len(blocks), 1)
            preview = tabs["Preview"]
            match = re.search(r"\bpart=\{", preview)
            self.assertIsNotNone(match)
            part, _ = json.JSONDecoder().raw_decode(preview[match.end():].lstrip())
            self.assertEqual(part, json.loads(blocks[0]), "Preview differs from its JSON tab")
            stored = re.search(r"Relay answers `202` with the stored Message.*?```json\s*\n(.*?)```", source, re.S)
            self.assertEqual(part, json.loads(stored[1])["message"]["parts"][0])
        self.assertEqual(previews, 1)

    def test_buttons_preview_has_local_native_controls_and_accessible_feedback(self):
        source = (ROOT / "snippets/buttons-preview.jsx").read_text()
        buttons = source.split("export const ButtonsPreview =", 1)[1].split(
            "export const SelectionPreview =", 1)[0]
        self.assertRegex(buttons, r"\[reply,\s*setReply\]\s*=\s*useState\(")
        self.assertRegex(buttons, r"\[openedURL,\s*setOpenedURL\]\s*=\s*useState\(")
        tags = re.findall(r"<button\b[\s\S]*?(?=>)", buttons)
        self.assertTrue(any("buttons-preview-action" in tag and
                            'type="button"' in tag for tag in tags))
        self.assertRegex(buttons, r'role=\{tapped \? "img" : "group"\}')
        self.assertRegex(buttons, r'className="buttons-reply"[^>]*role="status"')
        self.assertRegex(buttons, r'aria-label=\{`Reply: \$\{reply\}`\}')
        self.assertRegex(buttons, r'className="buttons-url-preview"[^>]*role="dialog"[^>]*aria-modal="true"')
        self.assertIn('aria-label="URL action preview"', buttons)
        self.assertIn("buttons-url-close", buttons)
        self.assertIn("relay-preview-reset", buttons)
        self.assertIn("Reset demo", buttons)
        # URL actions must use local state, never navigation or a network send.
        self.assertRegex(buttons, r"setOpenedURL\(item\.url\)")
        self.assertRegex(buttons, r"setReply\(item\.label\)")
        self.assertRegex(buttons, r"setReply\((?:null|\"\"|'')\)")
        self.assertRegex(buttons, r"setOpenedURL\((?:null|\"\"|'')\)")
        self.assertRegex(buttons, r"\{openedURL\}")
        self.assertRegex(buttons, r"reply(?:\s*!==\s*null)?\s*\?\s*\(")
        self.assertIn("bubble({ text: reply })", buttons)
        self.assertIn("bubble({ text: tapped })", buttons)
        for unsafe in (r"<a\b", r"\bhref\s*=", r"\bwindow\.open\s*\(",
                       r"\blocation\s*(?:[.=]|\[)", r"\bfetch\s*\(",
                       r"\bXMLHttpRequest\b", r"\bnavigator\.sendBeacon"):
            self.assertNotRegex(buttons, unsafe)

    def test_actual_button_handlers_keep_url_local_and_plain_reply_exact(self):
        # Execute only extracted event-handler JavaScript with state setters.
        # Node built-ins only: no JSX compiler, React, browser or network.
        source = (ROOT / "snippets/buttons-preview.jsx").read_text()
        buttons = source.split("export const ButtonsPreview =", 1)[1].split(
            "export const SelectionPreview =", 1)[0]
        click = re.search(r'onClick=\{\(\) => \{([\s\S]*?)\}\}', buttons)
        reset = re.search(r'className="relay-preview-reset"[^>]*onClick=\{\(\) => \{([\s\S]*?)\}\}', buttons)
        self.assertIsNotNone(click)
        self.assertIsNotNone(reset)
        program = r"""
import assert from 'node:assert/strict';
const source = JSON.parse(process.argv[1]);
const click = new Function('item', 'setReply', 'setOpenedURL', source.click);
const reset = new Function('setReply', 'setOpenedURL', source.reset);
let reply = null, openedURL = null;
const setReply = value => { reply = value; };
const setOpenedURL = value => { openedURL = value; };
for (const label of ['Jupiter', 'Continue', ' Approve exactly! ', '研究']) {
  click({label}, setReply, setOpenedURL);
  assert.equal(reply, label);
  assert.equal(openedURL, null);
  reset(setReply, setOpenedURL);
  assert.equal(reply, null);
  assert.equal(openedURL, null);
}
const url = 'https://example.invalid/local-only';
click({label:'Open report', url}, setReply, setOpenedURL);
assert.equal(openedURL, url);
assert.equal(reply, null, 'URL must not consume the group');
click({label:'Open report', url}, setReply, setOpenedURL);
assert.equal(reply, null, 'URL remains repeatable');
click({label:'Approve'}, setReply, setOpenedURL);
assert.equal(reply, 'Approve');
assert.equal(openedURL, null, 'Plain choice clears the URL preview in a mixed group');
reset(setReply, setOpenedURL);
assert.equal(reply, null);
assert.equal(openedURL, null);
"""
        subprocess.run(["node", "--input-type=module", "-e", program,
                        json.dumps({"click": click[1], "reset": reset[1]})], check=True)

    def test_interactive_previews_preserve_selection_behavior(self):
        source = (ROOT / "snippets/buttons-preview.jsx").read_text()
        selection = source.split("export const SelectionPreview =", 1)[1]
        self.assertIn('role="group"', selection)
        # Nothing is picked in the transcript: the prompt is one balloon with
        # the question as its title, a fixed second line, and a chevron.
        self.assertIn('{ kind: "title", text: title }', selection)
        self.assertIn('{ kind: "subtitle", text: "Pick options" }', selection)
        self.assertIn('bubble({ rows: promptRows, side: "leading", chevron: true })', selection)
        self.assertNotIn("selection-option", selection)
        self.assertNotIn("selection-actions", selection)
        self.assertNotIn(">Clear<", selection)
        self.assertNotIn("<img", selection)
        # The sheet the balloon opens: the title alone (no Options heading),
        # one checkbox row per option, and a single floating Send.
        sheet = selection.split('role="dialog"', 1)[1]
        self.assertIn('aria-modal="true"', sheet)
        self.assertIn('<div className="selection-sheet-title">{title}</div>', sheet)
        self.assertNotIn("Pick options", sheet)
        self.assertNotIn("selection-sheet-section", sheet)
        self.assertNotIn(">Options<", sheet)
        self.assertIn('role="checkbox" aria-checked={checked}', sheet)
        self.assertIn("current.filter((value) => value !== option.value)", sheet)
        self.assertEqual(sheet.count('className="selection-send"'), 1)
        footer = sheet.split("isReadOnly ? null : (", 1)[1]
        self.assertIn('className="selection-sheet-footer"', footer)
        self.assertIn("disabled={draft.length === 0}", footer)
        # A reopened prompt or reply is inert and carries no footer at all.
        self.assertIn('className="selection-sheet-option" disabled={isReadOnly}', sheet)
        self.assertIn("const checked = (isReadOnly ? answered : draft).includes(option.value)", sheet)
        # The reply repeats the title over one checkmark line per chosen label,
        # in source-option order, and reopens the same sheet.
        self.assertIn("options.filter((option) => (answered || []).includes(option.value))", selection)
        self.assertIn('...labels.map((label) => ({ kind: "label", text: label }))', selection)
        self.assertIn('bubble({ rows: answerRows, side: "trailing", chevron: true })', selection)
        self.assertIn('openSheet("selection-answer")', selection)
        self.assertIn('openSheet("selection-prompt")', selection)
        self.assertIn("setAnswered(draft)", selection)
        self.assertIn("setAnswered(receivedValues)", selection)
        self.assertIn("setDraft([])", selection)
        # The card renderer draws a bare checkmark, never a dot or a circle.
        card = source.split("const cardBubble =", 1)[1].split("return rows ?", 1)[0]
        self.assertIn("selection-card-mark", card)
        self.assertNotIn("<circle", card)
        self.assertNotIn("\u2022", card)

    def test_selection_send_matches_approved_visual_and_hit_target(self):
        css = (ROOT / "style.css").read_text()
        def rule(selector):
            match = re.search(r"(?:^|\n)" + re.escape(selector) + r"\s*\{([^{}]*)\}", css)
            self.assertIsNotNone(match, selector)
            return match[1]
        # The New Chat capsule: centred, inset a quarter of the content width
        # each side, floating over the list; disabled is a grey capsule.
        send = rule(".selection-send")
        for declaration in ("width: calc(50% + 16px)", "height: 48px", "border-radius: 24px",
                            "background: #0b75ff", "color: #ffffff",
                            "font-size: 17px", "font-weight: 600", "opacity: 1"):
            self.assertIn(declaration, send)
        self.assertNotIn("width: 100%", send)
        disabled = rule(".selection-send:disabled")
        self.assertIn("background: #eceef1", disabled)
        self.assertIn("opacity: 1", disabled)
        pressed = rule(".selection-send:active:not(:disabled)")
        self.assertIn("transform: scale(.96)", pressed)
        self.assertIn("opacity: 1", pressed)
        footer = rule(".selection-sheet-footer")
        self.assertIn("position: absolute", footer)
        self.assertNotIn("border-top", footer)
        # Rows fade under the title and under Send: the app's edge blur.
        self.assertIn("mask-image: linear-gradient", rule(".selection-sheet-list"))
        # Title alone at the top: no rule under it.
        self.assertNotIn("border-bottom", rule(".selection-sheet-title"))
        # Leading checkbox, no icon column, and a scrolling list.
        option = rule(".selection-sheet-option")
        self.assertIn("display: flex", option)
        self.assertIn("overflow-y: auto", rule(".selection-sheet-list"))
        self.assertIn("gap: 4px", rule(".buttons-preview-stack"))
        reduced = css.split("@media (prefers-reduced-motion: reduce)")[-1]
        for declaration in ("transition: none", "animation: none", "transform: none"):
            self.assertIn(declaration, reduced)
        self.assertIn(".selection-send:active:not(:disabled)", reduced)
        self.assertIn(".selection-prompt:active", reduced)

    def test_button_animation_has_scale_only_press_and_reduced_motion(self):
        css = (ROOT / "style.css").read_text()
        active = re.findall(r"([^{}]*\.buttons-preview-action:active[^{}]*)\{([^{}]*)\}", css)
        self.assertTrue(active, "Native buttons need press feedback")
        declarations = "\n".join(body for _, body in active)
        self.assertRegex(declarations, r"transform:\s*scale\(")
        for _, body in active:
            opacity = re.search(r"opacity:\s*([^;]+)", body)
            if opacity:
                self.assertEqual(opacity[1].strip(), "1", "Press feedback must not dim")
        self.assertRegex(css, r"\.buttons-preview-action:focus-visible")
        reduced = css.split("@media (prefers-reduced-motion: reduce)")[-1]
        self.assertIn(".buttons-preview", reduced)
        for rule in ("transition: none", "animation: none", "transform: none"):
            self.assertIn(rule, reduced)
        reply_rule = re.search(r"\.buttons-reply[^{}]*\{([^{}]*)\}", css)
        self.assertIsNotNone(reply_rule)
        self.assertRegex(reply_rule[1], r"animation:")

    def test_buttons_preview_matches_native_shared_width(self):
        # Relay-iOS 004cd885, RelayButtonsRowLayout: pillWidthShare = 0.75,
        # pillHeight = 48, pillSpacing = 4, leading/trailingInset = 20/16.
        css = (ROOT / "style.css").read_text()

        def declarations(selector):
            block = re.search(r"^" + re.escape(selector) + r"\s*\{([^}]*)\}", css, re.M)
            self.assertIsNotNone(block, f"Missing {selector}")
            return dict(re.findall(r"([\w-]+)\s*:\s*([^;]+);", block[1]))

        stack = declarations(".buttons-preview-stack")
        self.assertEqual(stack["width"], "75%")
        self.assertEqual(stack["max-width"], "75%")
        self.assertEqual(stack["align-self"], "flex-start")
        self.assertEqual(stack["gap"], "4px")
        pill = declarations(".buttons-preview-pill")
        # Every pill fills the narrowed stack, never the whole message column
        # and never a separate label-dependent width.
        self.assertEqual(pill["width"], "100%")
        self.assertEqual(pill["box-sizing"], "border-box")
        self.assertEqual(pill["min-height"], "48px")
        self.assertEqual(pill["padding"], "12px 16px 12px 20px")
        self.assertEqual(pill["border-radius"], "24px")

    def test_buttons_preview_regressions_are_detected(self):
        source = (ROOT / "interactions/buttons.mdx").read_text()
        text_prop = re.search(r'\btext\s*=\s*("(?:\\.|[^"\\])*")', source)
        self.assertIsNotNone(text_prop, "Need a text preview for regression checks")
        for name, replacement in (
            ("mismatched text", 'text="Incorrect preview text"'),
            ("omitted text", ""),
        ):
            with self.subTest(regression=name):
                changed = source[:text_prop.start()] + replacement + source[text_prop.end():]
                with self.assertRaises(AssertionError):
                    self.assert_buttons_previews_match_requests(changed)
        items_prop = re.search(r"\bitems\s*=\s*\{", source)
        self.assertIsNotNone(items_prop)
        with self.subTest(regression="mismatched items"):
            tail = source[items_prop.end():]
            _, end = json.JSONDecoder().raw_decode(tail.lstrip())
            changed = (source[:items_prop.end()] + '[{"label":"Incorrect choice"}]' +
                       tail.lstrip()[end:])
            with self.assertRaises(AssertionError):
                self.assert_buttons_previews_match_requests(changed)
        for group in re.findall(r"<Tabs\b[^>]*>.*?</Tabs>", source, re.S):
            if '<Tab title="JSON">' not in group:
                continue
            preview = re.search(r"<ButtonsPreview\b(.*?)/>", group, re.S)
            if preview and not re.search(r"\btext\s*=", preview[1]):
                with self.subTest(regression="invented buttons-only text"):
                    changed = source.replace(group, group.replace(
                        "<ButtonsPreview", '<ButtonsPreview text="Not in the request"', 1), 1)
                    with self.assertRaises(AssertionError):
                        self.assert_buttons_previews_match_requests(changed)
                with self.subTest(regression="missing buttons-only example"):
                    with self.assertRaises(AssertionError):
                        self.assert_buttons_previews_match_requests(source.replace(group, "", 1))
                break
        else:
            self.fail("Need a buttons-only preview for regression checks")

    def test_buttons_policy_section_and_backlinks_are_removed(self):
        paths = [
            path for path in ROOT.rglob("*.mdx")
            if not {"node_modules", ".mint", ".git"}.intersection(path.relative_to(ROOT).parts)
        ] + [ROOT / "llms.txt", ROOT / "llms-full.txt"]
        for path in paths:
            with self.subTest(path=str(path.relative_to(ROOT))):
                source = path.read_text()
                for stale in ("choose when to send buttons", "choose-when-to-send-buttons",
                              "if the person asks for buttons, send them."):
                    self.assertFalse(stale in source.lower(), f"{path.relative_to(ROOT)}: {stale}")

    def test_projection_changes_only_environment_origins(self):
        expected = (ROOT / "api-reference/openapi.yaml").read_bytes()
        if target() == "staging":
            for host in ("api", "docs", "go"):
                for scheme in ("https", "wss"):
                    expected = expected.replace(
                        f"{scheme}://{host}.relayapp.im".encode(),
                        f"{scheme}://{host}.staging.relayapp.im".encode(),
                    )
        self.assertEqual((ROOT / "api-reference/openapi.staging.yaml").read_bytes(), expected)

    def test_error_is_integrated_in_navigation_and_generated_surfaces(self):
        page = "api-reference/errors"
        config = json.loads((ROOT / "docs.json").read_text())
        self.assertIn(page, json.dumps(config["navigation"]))
        self.assertTrue((ROOT / f"{page}.mdx").is_file())
        for path in ("llms.txt", "llms-full.txt"):
            self.assertIn(page, (ROOT / path).read_text())
        # Error 2029 left with "Add comes back" (owner ruling 2026-09-13:
        # every agent is removable) and came back with a new meaning in
        # Relay-Server PR 233 (console.ts, organization membership).
        page_text = (ROOT / f"{page}.mdx").read_text()
        self.assertIn('<a id="2029">2029</a> | 403 | You are not a member of this organization.', page_text)
        self.assertNotIn("This agent cannot be removed.", page_text)


if __name__ == "__main__":
    unittest.main()
