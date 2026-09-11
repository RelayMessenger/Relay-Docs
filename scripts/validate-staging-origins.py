#!/usr/bin/env python3
"""Keep examples, SDK clients, and generated API targets on this checkout's origins.

Staging (the authored branch) must show only staging origins in runnable
examples. Production (`main`, derived by scripts/derive-production.py) must
show only production origins and carry no staging origin anywhere. Pass
`--production` or record `production` in `.docs-target` to select the mode.
"""
import json
import re
import unittest
from pathlib import Path
from origins import STAGING_HOSTS, STAGING_PACKAGE_REFERENCE, STAGING_INSTRUCTION_REFERENCE, ROOT, origin, target

PRODUCTION = re.compile(r"(?:https|wss)://(?:api|console|docs|go)\.relayapp\.im")
STAGING = re.compile(
    "|".join([*(re.escape(host) for host in STAGING_HOSTS),
              STAGING_PACKAGE_REFERENCE.pattern, STAGING_INSTRUCTION_REFERENCE.pattern]),
    re.I,
)
# The server hard-codes one docs host in every error's doc_url, on staging and
# on production alike (Relay-Server/server/src/app.ts:237, and the 404 handler
# at :217). That single value is environment-free, so an example that quotes it
# is correct on both branches and is exempt from the staging origin sweep.
# The exemption is keyed on the doc_url field, so a bare production docs URL
# anywhere else in an example is still rejected.
ENVIRONMENT_FREE_DOC_URL = re.compile(
    r'"doc_url"\s*:\s*"https://docs\.relayapp\.im/error/codes/[^"]*"'
)
CONTENT_SUFFIXES = {".mdx", ".md", ".json", ".yaml", ".yml", ".txt", ".js", ".mjs"}
# The tooling that knows both spellings is exempt from the production sweep,
# and so is versions.json, the mirror of what the registries actually publish.
SWEEP_EXEMPT = {".github", "node_modules", "scripts", ".git", ".mint"}


def example_errors(text: str, mode: str = "staging") -> list[str]:
    errors = []
    # Match Markdown fences including four-backtick LLM sections.
    for match in re.finditer(r"^(`{3,})([^\n]*)\n(.*?)^\1[ \t]*$", text, re.M | re.S):
        # `text captured-output` marks verbatim program output, not a runnable
        # example. CLI help prints environment-free docs links on both targets.
        # The marker never exempts bash, curl, or TypeScript request blocks.
        if match[2].strip() == "text captured-output":
            continue
        block = ENVIRONMENT_FREE_DOC_URL.sub("", match[3])
        if mode == "staging" and PRODUCTION.search(block):
            errors.append("production API, Console, docs, or share URL in a runnable example")
        for constructor in re.finditer(r"new Relay\(\{(.*?)\}\)", block, re.S):
            if not re.search(r"\bbaseURL\s*:", constructor[1]):
                errors.append("SDK constructor omits explicit baseURL")
    if mode == "production" and STAGING.search(text):
        errors.append("staging origin in production content")
    return errors


class RegressionTests(unittest.TestCase):
    def test_captured_program_output_is_not_a_request(self):
        self.assertFalse(example_errors("```text captured-output\nDocs: https://docs.relayapp.im\n```\n"))

    def test_output_marker_does_not_exempt_runnable_blocks(self):
        self.assertTrue(example_errors("```bash captured-output\ncurl https://api.relayapp.im/v1/chats\n```\n"))

    def test_production_curl_is_rejected(self):
        self.assertTrue(example_errors("```bash\ncurl https://api.relayapp.im/v1/chats\n```\n"))

    def test_doc_url_keeps_its_one_server_value_on_staging(self):
        self.assertFalse(example_errors(
            '```json\n{"doc_url":"https://docs.relayapp.im/error/codes/2xxx/2001"}\n```\n'
        ))

    def test_production_docs_url_outside_doc_url_is_still_rejected(self):
        self.assertTrue(example_errors(
            '```json\n{"see":"https://docs.relayapp.im/error/codes/2xxx/2001"}\n```\n'
        ))

    def test_production_share_and_docs_examples_are_rejected(self):
        for host in ("go", "docs"):
            self.assertTrue(example_errors(f"```text\nhttps://{host}.relayapp.im/@agent.dev\n```\n"))

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

    def test_production_mode_accepts_production_curl(self):
        self.assertFalse(example_errors(
            "```bash\ncurl https://api.relayapp.im/v1/chats\n```\n", "production"
        ))

    def test_production_mode_rejects_every_staging_host(self):
        for host in STAGING_HOSTS:
            with self.subTest(host=host):
                self.assertEqual(
                    example_errors(f"Read https://{host}/llms.txt first.", "production"),
                    ["staging origin in production content"],
                )

    def test_production_mode_rejects_staging_package_references(self):
        for reference in (
            "npm install @relaymessenger/sdk@staging",
            "npx relaymessenger@staging --help",
            "`relay-claude-channel@0.3.0-staging.4`",
            "| `@relaymessenger/sdk` | `0.3.0-staging.8` |",
        ):
            with self.subTest(reference=reference):
                self.assertEqual(
                    example_errors(reference, "production"),
                    ["staging origin in production content"],
                )

    def test_production_mode_accepts_plain_package_references(self):
        self.assertFalse(example_errors(
            "npm install @relaymessenger/sdk\n`@relaymessenger/cli` is `latest`\n"
            "/plugin marketplace add RelayMessenger/Relay-SDK@main\n", "production"
        ))

    def test_named_profile_suffix_is_not_token_environment_prose(self):
        self.assertFalse(example_errors(
            "Profile: existing-staging token source: config", "production"
        ))

    def test_production_mode_still_requires_explicit_base_url(self):
        self.assertTrue(example_errors(
            "```typescript\nnew Relay({ apiKey: token })\n```\n", "production"
        ))


def validate() -> None:
    mode = target()
    api = origin("api.staging.relayapp.im")
    config = json.loads((ROOT / "docs.json").read_text())
    assert config["navbar"]["primary"]["href"] == f"https://{origin('console.staging.relayapp.im')}"
    failures = []
    for path in ROOT.rglob("*.mdx"):
        if "node_modules" in path.parts:
            continue
        for error in example_errors(path.read_text(), mode):
            failures.append(f"{path.relative_to(ROOT)}: {error}")
    if mode == "production":
        for path in sorted(ROOT.rglob("*")):
            relative = path.relative_to(ROOT)
            if not path.is_file() or path.suffix not in CONTENT_SUFFIXES:
                continue
            if relative.as_posix() in {"versions.json", "api-reference/openapi.yaml"}:
                continue
            if SWEEP_EXEMPT & set(relative.parts) or path.suffix == ".mdx":
                continue
            if STAGING.search(path.read_text()):
                failures.append(f"{relative}: staging origin in production content")
    for name in ("openapi.staging.yaml", "openapi.mint.yaml"):
        text = (ROOT / "api-reference" / name).read_text()
        if mode == "staging" and PRODUCTION.search(text):
            failures.append(f"{name}: production target in staging API presentation")
        if f"url: https://{api}\n" not in text:
            failures.append(f"{name}: missing {mode} server origin")
    if failures:
        raise SystemExit("\n".join(failures))
    print(f"{mode.capitalize()} API targets, Console links, and explicit SDK baseURL verified")


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(RegressionTests)
    if not unittest.TextTestRunner().run(suite).wasSuccessful():
        raise SystemExit(1)
    validate()
