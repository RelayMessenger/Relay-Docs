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
        self.api = next(tab for tab in self.config["navigation"]["tabs"] if tab["tab"] == "API")
        self.chats = next(g for g in self.api["groups"] if g["group"] == "Chats")

    def test_every_existing_endpoint_is_nested_once(self):
        self.assertEqual(len(validate_api_navigation(self.config)), 38)

    def test_duplicate_endpoint_rejected(self):
        self.chats["pages"].append("GET /v1/chats")
        with self.assertRaisesRegex(ValueError, "exactly once"):
            validate_api_navigation(self.config)

    def test_wrong_resource_rejected(self):
        self.chats["pages"].remove("GET /v1/chats/{chatId}/messages")
        self.api["groups"][2]["pages"].append("GET /v1/chats/{chatId}/messages")
        with self.assertRaisesRegex(ValueError, "Incorrect resource nesting"):
            validate_api_navigation(self.config)

    def test_overview_required(self):
        self.chats["pages"].pop(0)
        with self.assertRaisesRegex(ValueError, "overview"):
            validate_api_navigation(self.config)

    def test_root_flattening_rejected(self):
        self.api["groups"] = [copy.deepcopy(self.chats)]
        with self.assertRaisesRegex(ValueError, "their own groups"):
            validate_api_navigation(self.config)

    def test_recursive_walk_preserves_order_and_parentage(self):
        self.assertEqual(
            list(walk_pages([{"group": "A", "pages": ["one", {"group": "B", "pages": ["two"]}]}])),
            [(("A",), "one"), (("A", "B"), "two")],
        )


if __name__ == "__main__":
    unittest.main()
