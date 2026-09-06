#!/usr/bin/env python3
"""Keep staging examples, SDK clients, and generated API targets consistent."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRODUCTION = re.compile(r"(?:https|wss)://(?:api|console)\.relayapp\.im")


def example_errors(text: str) -> list[str]:
    errors = []
    # Match Markdown fences including four-backtick LLM sections.
    for match in re.finditer(r"^(`{3,})[^\n]*\n(.*?)^\1[ \t]*$", text, re.M | re.S):
        block = match[2]
        if PRODUCTION.search(block):
            errors.append("production API or Console URL in a runnable example")
        for constructor in re.finditer(r"new Relay\(\{(.*?)\}\)", block, re.S):
            if not re.search(r"\bbaseURL\s*:", constructor[1]):
                errors.append("SDK constructor omits explicit baseURL")
    return errors


class RegressionTests(unittest.TestCase):
    def test_production_curl_is_rejected(self):
        self.assertTrue(example_errors("```bash\ncurl https://api.relayapp.im/v1/chats\n```\n"))

    def test_production_websocket_is_rejected(self):
        self.assertTrue(example_errors("```text\nwss://api.relayapp.im/v1/websocket\n```\n"))

    def test_implicit_sdk_default_is_rejected(self):
        self.assertTrue(example_errors("```typescript\nnew Relay({ apiKey: token })\n```\n"))

    def test_explicit_staging_client_is_accepted(self):
        self.assertFalse(example_errors(
            '```typescript\nnew Relay({ apiKey: token, '
            'baseURL: "https://api.staging.relayapp.im" })\n```\n'
        ))

    def test_sdk_default_explanation_is_allowed(self):
        self.assertFalse(example_errors("The SDK defaults to https://api.relayapp.im."))


def validate() -> None:
    config = json.loads((ROOT / "docs.json").read_text())
    assert config["navbar"]["primary"]["href"] == "https://console.staging.relayapp.im"
    failures = []
    for path in ROOT.rglob("*.mdx"):
        if "node_modules" in path.parts:
            continue
        for error in example_errors(path.read_text()):
            failures.append(f"{path.relative_to(ROOT)}: {error}")
    for name in ("openapi.staging.yaml", "openapi.mint.yaml"):
        text = (ROOT / "api-reference" / name).read_text()
        if PRODUCTION.search(text):
            failures.append(f"{name}: production target in staging API presentation")
        if "url: https://api.staging.relayapp.im\n" not in text:
            failures.append(f"{name}: missing staging server origin")
    if failures:
        raise SystemExit("\n".join(failures))
    print("Staging API targets, Console links, and explicit SDK baseURL verified")


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(RegressionTests)
    if not unittest.TextTestRunner().run(suite).wasSuccessful():
        raise SystemExit(1)
    validate()
