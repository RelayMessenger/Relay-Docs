#!/usr/bin/env python3
"""Offline environment, source-freshness and full-route hosted regressions."""
import argparse
import hashlib
import importlib.util
from contextlib import redirect_stdout
from io import BytesIO, StringIO
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

spec = importlib.util.spec_from_file_location(
    "hosted_validator", Path(__file__).with_name("validate-hosted-llms.py"))
hosted = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hosted)


def response(body):
    return {"body": body, "sha256": hashlib.sha256(body).hexdigest(),
            "headers": {"x-version": "same-deployment"}, "status": 200}


class HostedEnvironmentTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def fixture(self, environment="staging"):
        root = self.root
        (root / ".docs-target").write_text(environment + "\n")
        for directory in ("scripts", "guides/task", "api-reference"):
            (root / directory).mkdir(parents=True, exist_ok=True)
        self.config = {"favicon": "/favicon.png" if environment == "production" else "/favicon-staging.png",
                       "navigation": {"tabs": [{"tab": "Any title", "groups": [{"group": "Nested",
                           "pages": ["index", {"group": "Task", "pages": ["guides/task/index", "GET /v1/things"]}]}]}]}}
        (root / "docs.json").write_text(json.dumps(self.config))
        (root / "scripts/api-page-paths.json").write_text(json.dumps({
            "listThings": {"endpoint": "GET /v1/things", "href": "/api-reference/things/list"}}))
        contract = "paths:\n  /v1/things:\n    get:\n      operationId: listThings\n"
        (root / "api-reference/openapi.yaml").write_text(contract)
        self.authored = [
            {"page": "index", "title": "Current introduction", "body": "Receive the current event format into your durable inbox.\n"},
            {"page": "guides/task/index", "title": "A newly named atomic task", "body": "Verify this distinctive task against the current deployment.\n"},
        ]
        self.bodies = {}
        index = []
        complete = []
        for page in self.authored:
            (root / (page["page"] + ".mdx")).write_text(
                f'---\ntitle: "{page["title"]}"\ndescription: "Current task"\n---\n{page["body"]}')
            index.append(f'- [{page["title"]}](https://docs.test/{page["page"]}.md)')
            complete.append(f'# {page["title"]}\n\nSource: https://docs.test/{page["page"]}.md\n\n{page["body"]}')
            self.bodies[hosted.authored_route(page["page"])] = (
                f'<h1>{page["title"]}</h1><p>{page["body"]}</p>').encode()
            self.bodies[page["page"] + ".md"] = f'# {page["title"]}\n\n{page["body"]}'.encode()
        index.append('- [Generated operation](https://docs.test/api-reference/things/list.md)')
        package = "@relaymessenger/sdk" + ("@staging" if environment == "staging" else "")
        complete.append(f'```bash\nnpm install {package}\n```\n\n{contract}')
        for name, text in (("skill.md", "Canonical instruction bytes.\n"), ("agent-prompt.md", "Canonical instruction bytes.\n"),
                           ("llms.txt", "\n".join(index)), ("llms-full.txt", "\n".join(complete))):
            (root / name).write_text(text)
            self.bodies[name] = text.encode()
        self.bodies[""] += b'<link rel="icon" sizes="192x192" href="/generated.png?v=1">'
        self.bodies["start/quickstart"] = self.bodies[""]
        favicon = self.config["favicon"].lstrip("/")
        (root / favicon).write_bytes(b"exact-source-icon")
        self.bodies[favicon] = b"exact-source-icon"
        self.bodies["/generated.png?v=1"] = b"generated-icon"
        self.calls = []

        def fetch(path, cache_busted=False):
            self.calls.append((path, cache_busted))
            if path not in self.bodies:
                raise SystemExit(f"missing route: {path}")
            return response(self.bodies[path])
        return fetch

    def args(self, **overrides):
        values = dict(base_url="https://docs.test", production=False, all_pages=False,
                      workers=2, expected_sha=None, receipt=None, require_edge_fresh=False)
        values.update(overrides)
        return argparse.Namespace(**values)

    def run_fixture(self, environment, **options):
        fetch = self.fixture(environment)
        colors = {"opaque": 100, "black": 80 if environment == "staging" else 0,
                  "blue": 80 if environment == "production" else 0, "white": 20}
        with patch.object(hosted.origins, "TARGET_FILE", self.root / ".docs-target"), \
                patch.object(hosted.origins.sys, "argv", ["validator"]), \
                patch.object(hosted, "png_color_counts", return_value=colors):
            return hosted.run(self.args(**options), self.root, fetch)

    def test_staging_and_production_pass_without_fixed_titles_or_install_count(self):
        for environment in ("staging", "production"):
            with self.subTest(environment=environment):
                receipt = self.run_fixture(environment, all_pages=True)
                self.assertEqual(receipt["environment"], environment)
                self.assertEqual(receipt["authored_pages"], 2)
                self.assertEqual(receipt["contract_operation_ids"], ["listThings"])
                self.assertEqual(receipt["sdk_install_commands"], 1)
                for path in ("", "index.md", "guides/task", "guides/task/index.md"):
                    self.assertIn((path, False), self.calls)
                    self.assertIn((path, True), self.calls)

    def test_production_flag_overrides_target_without_rewriting_sources(self):
        with patch.object(hosted.origins, "target", return_value="staging"):
            self.assertEqual(hosted.environment_config(True)["environment"], "production")
        self.assertEqual(self.run_fixture("production", production=True)["environment"], "production")
        fetch = self.fixture("staging")
        with self.assertRaisesRegex(SystemExit, "matching derived checkout"):
            hosted.run(self.args(production=True), self.root, fetch)

    def test_parser_accepts_production_and_bounded_all_page_options(self):
        args = hosted.argument_parser().parse_args(["https://docs.test", "--production", "--all-pages", "--workers", "3"])
        self.assertTrue(args.production)
        self.assertTrue(args.all_pages)
        self.assertEqual(args.workers, 3)
        with self.assertRaisesRegex(SystemExit, "between 1 and 16"):
            hosted.check_all_pages(lambda *a, **k: None, [], workers=17)

    def test_package_environment_not_number_of_commands_is_checked(self):
        for count in (1, 3, 5):
            self.assertEqual(hosted.check_sdk_installs("npm install @relaymessenger/sdk\n" * count, "production"), count)
        for environment, command in (("production", "@relaymessenger/sdk@staging"),
                                     ("production", "@relaymessenger/sdk@1.0.0-staging.1"),
                                     ("staging", "@relaymessenger/sdk")):
            with self.subTest(environment=environment, command=command), self.assertRaises(SystemExit):
                hosted.check_sdk_installs("npm install " + command, environment)

    def test_navigation_and_contract_additions_must_be_discoverable(self):
        self.fixture()
        index = self.bodies["llms.txt"].decode()
        complete = self.bodies["llms-full.txt"].decode()
        for missing_index, missing_complete in ((index.replace("guides/task/index.md", "old.md"), complete),
                                                (index, complete.replace("guides/task/index.md", "old.md")),
                                                (index, complete.replace("listThings", "oldOperation"))):
            with self.assertRaises(SystemExit):
                hosted.check_discovery(self.root, self.config, missing_index, missing_complete)

    def test_unnavigated_authored_route_cannot_escape_full_page_check(self):
        self.fixture()
        (self.root / "orphan.mdx").write_text("Unpublished authored page")
        with self.assertRaisesRegex(SystemExit, "missing from navigation"):
            hosted.check_authored_inventory(self.root, self.authored)

    def test_wrong_generated_brand_and_stale_source_icon_fail(self):
        for environment in ("staging", "production"):
            fetch = self.fixture(environment)
            with patch.object(hosted.origins, "target", return_value=environment):
                settings = hosted.environment_config()
            wrong = {"opaque": 100, "black": 0 if environment == "staging" else 80,
                     "blue": 80 if environment == "staging" else 0, "white": 20}
            with patch.object(hosted, "png_color_counts", return_value=wrong), self.assertRaisesRegex(SystemExit, "identity"):
                hosted.check_brand(fetch, self.bodies[""], self.root, settings)
            self.bodies[settings["favicon"]] = b"stale-source-icon"
            with self.assertRaisesRegex(SystemExit, "checkout source bytes"):
                hosted.check_brand(fetch, self.bodies[""], self.root, settings)

    def test_all_pages_reject_missing_stale_or_cached_route(self):
        for failure in ("missing", "title", "prose", "cache"):
            with self.subTest(failure=failure):
                fetch = self.fixture()
                path = "guides/task/index.md"
                if failure == "missing":
                    del self.bodies[path]
                elif failure == "title":
                    self.bodies[path] = self.bodies[path].replace(b"A newly named atomic task", b"Old task")
                elif failure == "prose":
                    self.bodies[path] = self.bodies[path].replace(b"current deployment", b"old deployment")
                else:
                    original = fetch
                    def fetch(path, cache_busted=False):
                        result = original(path, cache_busted)
                        return response(b"stale") if path == "guides/task" and not cache_busted else result
                with self.assertRaises(SystemExit):
                    hosted.check_all_pages(fetch, self.authored, workers=2)

    def test_mdx_wrappers_can_change_but_payload_bytes_cannot(self):
        page = {"page": "payload", "title": "Payload", "body": '<Note>Preserve this distinctive current payload exactly.</Note>\n\n```json\n{"code":3006}\n```\n'}
        markdown = b'# Payload\n\n> Preserve this distinctive current payload exactly.\n\n```json Payload\n{"code":3006}\n```\n'
        hosted.check_page_content(page, markdown, markdown=True)
        with self.assertRaisesRegex(SystemExit, "source code block"):
            hosted.check_page_content(page, markdown.replace(b"3006", b"3005"), markdown=True)
        hosted.check_page_content(page, b'<main><h1>Payload</h1><p>Preserve this distinctive current payload exactly.</p></main>')
        with self.assertRaisesRegex(SystemExit, "source content"):
            hosted.check_page_content(page, b'<h1>Payload</h1><script>Preserve this distinctive current payload exactly.</script>')

    def test_agent_prompt_allows_mintlify_wrapper_and_link_rendering_only(self):
        source = (
            b"Connect this project to Relay. Read https://docs.staging.relayapp.im/llms.txt "
            b"and follow its Agent onboarding section before you run anything. Open "
            b"https://docs.staging.relayapp.im/llms-full.txt when a step needs a page's full text. "
            b"Use only the endpoints, commands, and files those documents name; if a step cannot "
            b"be verified there, stop and say so.\n"
        )
        hosted_body = (
            b"> ## Documentation Index\n"
            b"> Fetch the complete documentation index at: https://docs.staging.relayapp.im/llms.txt\n"
            b"> Use this file to discover all available pages before exploring further.\n\n"
            b"# Agent prompt\n\n"
            b"Connect this project to Relay. Read "
            b"[https://docs.staging.relayapp.im/llms.txt](https://docs.staging.relayapp.im/llms.txt) "
            b"and follow its Agent onboarding section before you run anything. Open "
            b"[https://docs.staging.relayapp.im/llms-full.txt](https://docs.staging.relayapp.im/llms-full.txt) "
            b"when a step needs a page's full text. Use only the endpoints, commands, and files those "
            b"documents name; if a step cannot be verified there, stop and say so.\n"
        )
        self.assertTrue(hosted.source_body_matches("agent-prompt.md", hosted_body, source))
        self.assertFalse(
            hosted.source_body_matches(
                "agent-prompt.md",
                hosted_body.replace(b"stop and say so", b"continue anyway"),
                source,
            )
        )

    def test_full_route_checks_have_bounded_concurrency(self):
        active = 0
        maximum = 0
        lock = threading.Lock()
        page = {"page": "task", "title": "Task", "body": "Preserve this distinctive current task description."}
        def fetch(path, cache_busted=False):
            nonlocal active, maximum
            with lock:
                active += 1
                maximum = max(maximum, active)
            time.sleep(0.005)
            with lock:
                active -= 1
            body = (f'# Task\n\n{page["body"]}' if path.endswith(".md") else f'<h1>Task</h1><p>{page["body"]}</p>').encode()
            return response(body)
        pages = [{**page, "page": f"task-{i}"} for i in range(8)]
        self.assertEqual(len(hosted.check_all_pages(fetch, pages, workers=2)), 16)
        self.assertLessEqual(maximum, 2)

    def test_expected_sha_filters_environment_sha_and_latest_status(self):
        sha = "a" * 40
        for environment in ("staging", "production"):
            candidate = {"id": 1, "sha": sha, "environment": environment, "ref": "main", "statuses_url": "https://github.test/status"}
            success = {"state": "success", "environment_url": "https://docs.test", "id": 2}
            calls = []
            def get_json(url):
                calls.append(url)
                return [success] if url.endswith("/status") else [candidate]
            result = hosted.check_deployment(sha, environment, "https://docs.test", get_json)
            self.assertEqual(result["environment"], environment)
            self.assertEqual(parse_qs(urlsplit(calls[0]).query)["environment"], [environment])
            for bad in ({**candidate, "sha": "b" * 40}, {**candidate, "environment": "other"}):
                with self.assertRaises(SystemExit):
                    hosted.check_deployment(sha, environment, "https://docs.test", lambda url: [bad])
            with self.assertRaises(SystemExit):
                hosted.check_deployment(sha, environment, "https://docs.test", lambda url: [
                    {**success, "updated_at": "2026-09-07T12:00:00Z"},
                    {"state": "failure", "updated_at": "2026-09-08T12:00:00Z"}]
                    if url.endswith("/status") else [candidate])
            with self.assertRaises(SystemExit):
                hosted.check_deployment(sha, environment, "https://other.test", get_json)

    def run_origin_fixture(self, edge_stale=False, origin_stale=False, strict=False):
        self.fixture()
        class HTTPResponse(BytesIO):
            status = 200
            headers = {"X-Version": "same-deployment", "Age": "20179",
                       "Cache-Control": "public, max-age=86400"}

        def opener(request, timeout):
            url = urlsplit(request.full_url)
            path = url.path.lstrip("/")
            if path == "generated.png":
                path = "/generated.png?v=1"
            body = self.bodies[path]
            if path == "llms-full.txt":
                busted = "relay_cache_probe" in parse_qs(url.query)
                if (origin_stale and busted) or (edge_stale and not busted):
                    body = b"stale source bytes"
            result = HTTPResponse(body)
            result.url = request.full_url
            return result

        with patch.object(hosted.origins, "target", return_value="staging"), \
                patch.object(hosted, "png_color_counts", return_value={"opaque": 100, "black": 100, "blue": 0}):
            return hosted.run(self.args(require_edge_fresh=strict), self.root,
                              hosted.make_fetch("https://docs.test", opener))

    def test_origin_matches_stale_edge_passes_with_lag(self):
        output = StringIO()
        with redirect_stdout(output):
            receipt = self.run_origin_fixture(edge_stale=True)
        self.assertEqual(receipt["verdict"], "passed")
        self.assertEqual(output.getvalue(), "/llms-full.txt: edge cache is 20179 s behind origin "
                         "(max-age 86400); origin matches checkout\n")
        pair = receipt["pages"]["/llms-full.txt"]
        self.assertNotEqual(pair["canonical"]["sha256"], pair["cache_busted"]["sha256"])

    def test_origin_mismatch_fails_with_existing_message(self):
        for edge_stale in (False, True):
            with self.subTest(edge_stale=edge_stale), self.assertRaisesRegex(
                    SystemExit, r"^/llms-full.txt served body does not match expected checkout source bytes$"):
                self.run_origin_fixture(edge_stale=edge_stale, origin_stale=True)

    def test_matching_origin_and_edge_pass_silently(self):
        output = StringIO()
        with redirect_stdout(output):
            receipt = self.run_origin_fixture()
        self.assertEqual(receipt["verdict"], "passed")
        self.assertEqual(output.getvalue(), "")

    def test_require_edge_fresh_rejects_stale_edge(self):
        self.assertFalse(hosted.argument_parser().parse_args(["https://docs.test"]).require_edge_fresh)
        self.assertTrue(hosted.argument_parser().parse_args(
            ["https://docs.test", "--require-edge-fresh"]).require_edge_fresh)
        with self.assertRaisesRegex(SystemExit, "canonical body .* does not match current origin body"):
            self.run_origin_fixture(edge_stale=True, strict=True)

    def test_http_errors_and_empty_bodies_fail_and_query_is_cache_busted(self):
        calls = []
        class HTTPResponse(BytesIO):
            status = 200
            headers = {}
            url = "https://docs.test/task"
        def opener(request, timeout):
            calls.append(request.full_url)
            return HTTPResponse(b"current")
        fetch = hosted.make_fetch("https://docs.test", opener)
        fetch("task?existing=1", cache_busted=True)
        query = parse_qs(urlsplit(calls[0]).query)
        self.assertEqual(query["existing"], ["1"])
        self.assertIn("relay_cache_probe", query)
        for status, body in ((404, b"missing"), (200, b"")):
            result = HTTPResponse(body)
            result.status = status
            with self.assertRaises(SystemExit):
                hosted.make_fetch("https://docs.test", lambda *a, **k: result)("task")


if __name__ == "__main__":
    unittest.main()
