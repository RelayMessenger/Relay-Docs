#!/usr/bin/env python3
import copy
import json
import unittest
from pathlib import Path
from api_navigation import validate_api_navigation, walk_pages

ROOT = Path(__file__).resolve().parents[1]


class NavigationTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ROOT / "docs.json").read_text())
        self.api = next(tab for tab in self.config["navigation"]["tabs"] if tab["tab"] == "API Reference")
        self.chats = self.api["groups"][0]["pages"][1]

    def test_every_existing_endpoint_is_nested_once(self):
        self.assertEqual(len(validate_api_navigation(self.config)), 37)

    def test_duplicate_endpoint_rejected(self):
        self.chats["pages"].append("GET /v1/chats")
        with self.assertRaisesRegex(ValueError, "exactly once"):
            validate_api_navigation(self.config)

    def test_flattening_chat_messages_rejected(self):
        messages = next(item for item in self.chats["pages"] if isinstance(item, dict) and item["group"] == "Messages")
        self.chats["pages"].extend(messages["pages"])
        self.chats["pages"].remove(messages)
        with self.assertRaisesRegex(ValueError, "Incorrect resource nesting"):
            validate_api_navigation(self.config)

    def test_overview_required(self):
        self.chats["pages"].pop(0)
        with self.assertRaisesRegex(ValueError, "overview"):
            validate_api_navigation(self.config)

    def test_root_flattening_rejected(self):
        self.api["groups"] = [copy.deepcopy(self.chats)]
        with self.assertRaisesRegex(ValueError, "nested under HTTP"):
            validate_api_navigation(self.config)

    def test_recursive_walk_preserves_order_and_parentage(self):
        self.assertEqual(
            list(walk_pages([{"group": "A", "pages": ["one", {"group": "B", "pages": ["two"]}]}])),
            [(("A",), "one"), (("A", "B"), "two")],
        )


if __name__ == "__main__":
    unittest.main()
