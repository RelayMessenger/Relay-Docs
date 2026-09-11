#!/usr/bin/env python3
"""Offline integration-doc regressions, scoped to the page that owns each task.

SDK evidence reread on 2026-09-08 at origin/staging (28db9cd):
  packages/cli/src/{program,config,event-listen,terminal-watch,agent-handoff}.ts
  packages/cli/src/agents.ts and agents.test.ts (flat developer-facing records)
  packages/cli/test/runtime-connect.test.ts
  packages/openclaw/src/dispatch.real-ingress.test.ts
  packages/claude-code/{README.md,src/config.ts}
  packages/mcp/src/{cli,auth}.ts
  packages/chat-sdk-adapter/test/adapter.test.ts (file-byte uploads are supported)
  .{agents/plugins,cursor-plugin,claude-plugin}/marketplace.json

No registry inventories, artifact hashes, live calls, or SDK checkout required.
Mintlify and the hosted checks own rendering and remote URL availability.
"""

import json
import re
import tempfile
import unittest
from pathlib import Path
from urllib.parse import unquote, urlsplit

from origins import origin, production_text, source_ref, target

ROOT = Path(__file__).resolve().parents[1]
CLI = "integrations/cli.mdx"
AUTH = "integrations/cli/authentication.mdx"
OBSERVE = "integrations/cli/observe-events.mdx"
NATIVE = "integrations/native-setup.mdx"
SKILLS = "integrations/skills.mdx"
MCP = "integrations/mcp.mdx"
OBSERVER_REFERENCE = "guides/websocket/observe-events.mdx"
FENCE = re.compile(r"^```[^\n]*\n(.*?)^```\s*$", re.M | re.S)
FINISH = {"Next steps", "See also", "Related"}
SOURCES = {
    CLI: "packages/cli",
    NATIVE: "packages/cli/src/runtime-connect",
    MCP: "packages/mcp",
    SKILLS: "skills/relay",
    "integrations/chat-sdk.mdx": "packages/chat-sdk-adapter",
    "integrations/openclaw.mdx": "packages/openclaw",
    "integrations/claude-code.mdx": "packages/claude-code",
    "integrations/cloudflare-think.mdx": "cookbook/cloudflare-think-agent",
    "integrations/codex.mdx": "plugins/relay",
    "integrations/cursor.mdx": "plugins/relay",
    "examples/index.mdx": "cookbook",
}
RETIRED_REPOS = (
    "Relay-Chat-SDK", "Relay-CLI", "Relay-MCP", "Relay-OpenClaw",
    "Relay-Agent-Starter", "Relay-Skills", "Relay-Examples",
    "Relay-Codex", "Relay-Cursor", "Relay-Claude-Code",
)


def read(relative):
    return (ROOT / relative).read_text()


def expected(value):
    return production_text(value) if target() == "production" else value


def assigned_pages():
    return sorted({
        *ROOT.glob("integrations/*.mdx"),
        *ROOT.glob("integrations/cli/*.mdx"),
        ROOT / "examples/index.mdx",
    })


def prose(text):
    return FENCE.sub("", text)


def normalized(text):
    return re.sub(r"\s+", " ", text).lower()


def commands(text):
    """Join shell continuations without mistaking Markdown prose for commands."""
    return [
        line.strip()
        for block in FENCE.findall(re.sub(
            r"^```text captured-output\n.*?^```[ \t]*$", "", text, flags=re.M | re.S
        ))
        for line in re.sub(r"\\\s*\n\s*", " ", block).splitlines()
        if line.strip()
    ]


def links(text):
    text = prose(text)
    return re.findall(r"\]\(([^)\s]+)(?:\s+[^)]*)?\)", text) + re.findall(
        r'\bhref=["\']([^"\']+)["\']', text
    )


def anchors(text):
    result = set(re.findall(r'\bid=["\']([^"\']+)["\']', prose(text)))
    counts = {}
    for heading in re.findall(r"^#{1,6}\s+(.+)$", prose(text), re.M):
        slug = re.sub(r"[^\w\s-]", "", heading.lower()).replace(" ", "-")
        occurrence = counts.get(slug, 0)
        counts[slug] = occurrence + 1
        result.add(f"{slug}-{occurrence}" if occurrence else slug)
    return result


def local_link_error(root, source, href, redirects):
    """Resolve local MDX pages, directory indexes, redirects, and fragments."""
    parts = urlsplit(href)
    if parts.scheme or parts.netloc:
        return None
    route = parts.path or "/" + source.relative_to(root).with_suffix("").as_posix()
    fragment = parts.fragment
    seen = set()
    while True:
        if route in seen:
            return f"redirect cycle: {href}"
        seen.add(route)
        base = root / route.lstrip("/")
        candidates = (base.with_suffix(".mdx"), base.with_suffix(".md"), base / "index.mdx")
        page = next((p for p in candidates if p.is_file()), None)
        if page:
            if fragment and unquote(fragment) not in anchors(page.read_text()):
                return f"missing anchor: {href}"
            return None
        if route not in redirects:
            return f"missing page: {href}"
        destination = urlsplit(redirects[route])
        if destination.scheme or destination.netloc:
            return None
        route = destination.path
        fragment = destination.fragment or fragment


def connect_command_errors(text):
    """`connect` writes a token into a runtime's config, so its examples must
    never show a token as a literal argument, and never point at production."""
    errors = []
    connects = [line for line in commands(text) if re.search(r"\bconnect\b", line)]
    if not connects:
        errors.append("connect task has no connect command")
    for command in connects:
        for value in re.findall(r"--token(?:=|\s+)(\S+)", command):
            if not re.match(r'^["\']?[$<]', value):
                errors.append(f"connect example carries a literal token: {command}")
    if any("https://api.relayapp.im" in line for line in commands(text)):
        errors.append("connect command selects the production API")
    return errors


class IntegrationDocsTests(unittest.TestCase):
    def assertConcept(self, text, pattern, message):
        self.assertRegex(normalized(text), pattern, message)

    def assertLink(self, relative, route):
        self.assertTrue(
            any(urlsplit(link).path == route for link in links(read(relative))),
            f"{relative} must link to its task owner: {route}",
        )

    def test_pages_are_focused_tasks_or_directories(self):
        for path in assigned_pages():
            with self.subTest(page=path.relative_to(ROOT)):
                text = path.read_text()
                self.assertRegex(text, r"\A---\n[\s\S]+?\n---\n")
                frontmatter = text.split("---", 2)[1]
                for key in ("title", "description", "keywords"):
                    self.assertRegex(frontmatter, rf"(?m)^{key}:")
                headings = re.findall(r"^## (.+)$", prose(text), re.M)
                self.assertTrue(headings, "page needs a related-task section")
                self.assertIn(headings[-1], FINISH)
                self.assertLessEqual(len(headings) - 1, 5, "split independent tasks, not paragraph length")

    def test_owned_links_resolve_including_fragments(self):
        config = json.loads(read("docs.json"))
        redirects = {r["source"]: r["destination"] for r in config.get("redirects", [])}
        for path in assigned_pages():
            for href in links(path.read_text()):
                with self.subTest(page=path.relative_to(ROOT), href=href):
                    self.assertIsNone(local_link_error(ROOT, path, href, redirects))

    def test_sources_remain_in_maintained_repositories(self):
        for page, directory in SOURCES.items():
            with self.subTest(page=page):
                self.assertIn(
                    f"https://github.com/RelayMessenger/Relay-SDK/tree/{source_ref()}/{directory}",
                    links(read(page)),
                )
        self.assertIn("https://github.com/RelayMessenger/Relay-Hermes", links(read("integrations/hermes.mdx")))
        for path in assigned_pages():
            text = path.read_text()
            for repository in RETIRED_REPOS:
                self.assertNotIn(f"RelayMessenger/{repository}", text, str(path))
            for command in commands(text):
                if command.startswith("git clone") and "RelayMessenger/Relay-SDK" in command:
                    self.assertIn(f"--branch {source_ref()}", command)

    def test_install_commands_select_actual_packages_and_plugin_trees(self):
        installs = {
            CLI: "npm install --global relaymessenger@staging",
            MCP: "npm install --global @relaymessenger/mcp@staging",
            "integrations/openclaw.mdx": "openclaw plugins install @relaymessenger/openclaw-plugin@staging",
            "integrations/hermes.mdx": "hermes plugins install RelayMessenger/Relay-Hermes --enable",
            "integrations/claude-code.mdx": "/plugin install relay@relay-messenger",
            "integrations/codex.mdx": "codex plugin add relay@relay-plugin-marketplace",
        }
        for page, command in installs.items():
            self.assertIn(expected(command), commands(read(page)), page)
        self.assertIn(expected("npx relaymessenger@staging --help"), commands(read(CLI)))
        self.assertIn(
            expected("/plugin marketplace add RelayMessenger/Relay-SDK@staging"),
            commands(read("integrations/claude-code.mdx")),
        )
        self.assertTrue(any(
            line.startswith("codex plugin marketplace add ") for line in commands(read("integrations/codex.mdx"))
        ))
        self.assertTrue(any(
            line.startswith("ln -s ") and "/plugins/relay" in line and ".cursor/plugins/local/relay" in line
            for line in commands(read("integrations/cursor.mdx"))
        ))
        self.assertTrue(any(
            re.search(r"npx skills@\S+ add \./Relay-SDK/skills/relay --skill relay", line)
            for line in commands(read(SKILLS))
        ))
        adapter_commands = "\n".join(commands(read("integrations/chat-sdk.mdx")))
        self.assertIn("chat@4.39.0", adapter_commands)
        self.assertIn(expected("@relaymessenger/chat-sdk-adapter@staging"), adapter_commands)

    def test_environment_pairing_and_runtime_requirements(self):
        api = f"https://{origin('api.staging.relayapp.im')}"
        for page in (AUTH, NATIVE, "integrations/chat-sdk.mdx", "integrations/openclaw.mdx",
                     "integrations/claude-code.mdx", "integrations/hermes.mdx", "integrations/cloudflare-think.mdx"):
            self.assertIn(api, read(page), page)
        for page in (CLI, MCP, NATIVE, "integrations/openclaw.mdx", "integrations/claude-code.mdx"):
            self.assertIn("22.22.3", read(page), "Keep the supported Node minimum at the install task")
        self.assertIn(">=2026.8.1 <2026.9.0", read("integrations/openclaw.mdx"))
        for version in ("3.11", "3.13"):
            self.assertIn(version, read("integrations/hermes.mdx"))
        self.assertConcept(read("integrations/claude-code.mdx"), r"channels.*research.preview", "Keep channel availability prerequisite")
        self.assertLink(MCP, "/integrations/cli/authentication")
        self.assertIn("RELAY_API_URL", read(MCP))
        self.assertConcept(read(MCP), r"(?:match|pair).*token", "MCP environment overrides must stay paired")

    def test_cli_routes_to_task_owners_without_copying_agent_flows(self):
        for task in ("create-agent", "list-agents", "delete-agent"):
            self.assertLink(CLI, f"/guides/agents/{task}")
        for page in (AUTH, OBSERVE, NATIVE):
            self.assertLink(CLI, "/" + page.removesuffix(".mdx"))
        for path in ROOT.glob("integrations/**/*.mdx"):
            self.assertFalse(
                any(re.search(r"\bagents (?:create|list|delete)\b", line) for line in commands(path.read_text())),
                f"Agent workflows belong to guides/agents, not {path.relative_to(ROOT)}",
            )
        # Inspect the owning guides, not a duplicated record on the CLI overview.
        for page, is_list in (("guides/agents/create-agent.mdx", False), ("guides/agents/list-agents.mdx", True)):
            records = []
            for block in re.findall(r"^```json\n(.*?)^```", read(page), re.M | re.S):
                value = json.loads(block)
                records.extend(value.get("agents", []) if is_list else [value])
            records = [
                r for r in records
                if isinstance(r, dict) and r.get("token") == "stored" and "error" not in r
            ]
            self.assertTrue(records, f"{page} must show its developer-facing record")
            for record in records:
                self.assertTrue({"handle", "display_name", "image_url"} <= record.keys())
                self.assertNotIn("agent", record, "CLI records are flat, unlike the API bootstrap response")

    def test_authentication_owns_private_input_resolution_and_logout(self):
        text = read(AUTH)
        for command in ("auth login", "auth status", "auth logout", "--with-token", "--profile"):
            self.assertIn(command, "\n".join(commands(text)))
        for variable in ("RELAY_AGENT_TOKEN", "--api-url", "--profile"):
            self.assertIn(variable, text)
        self.assertConcept(text, r"never as command arguments", "Tokens must not become shell arguments")
        self.assertConcept(text, r"save a token for this computer", "Use the shipped login description")
        self.assertConcept(text, r"logout.*(?:only|selected|that profile)", "Logout scope is local")
        self.assertConcept(text, r"relay_agent_token is honored in scripts only", "Use the shipped environment rule")
        self.assertLink(AUTH, "/guides/agents/delete-agent")

    def test_observation_delegates_protocol_without_becoming_a_consumer(self):
        self.assertLink(OBSERVE, "/guides/websocket/observe-events")
        text = read(OBSERVE)
        reference = read(OBSERVER_REFERENCE)
        self.assertTrue(any(re.match(r"npx relaymessenger\S* watch\b", line) for line in commands(text)))
        self.assertConcept(text, r"read.only|without consuming|watches only", "The terminal is an observer")
        self.assertNotRegex("\n".join(commands(text)), r"\bevents\s+listen\b|--acknowledge-events")
        for marker in ("observe=true", "observational", "full_sync_complete"):
            self.assertIn(marker, reference, "Wire details belong to the observer reference")
        self.assertConcept(reference, r"(?:neither|no|without).*ack", "An observer must never ACK")
        self.assertConcept(reference, r"without.*consuming fallback", "Observer failure must not start a consumer")
        self.assertLink(OBSERVE, "/integrations/native-setup")

    def test_connect_examples_keep_tokens_out_of_arguments(self):
        text = read(NATIVE)
        self.assertEqual(connect_command_errors(text), [])
        self.assertTrue(any("--token" in line for line in commands(text)),
                        "Show how an existing agent is connected by token")
        self.assertConcept(text, r"secret store", "Tokens come from a secret store")
        self.assertConcept(text, r"owner.only", "The channel file is written owner-only")
        self.assertConcept(text, r"dry.run.{0,60}change(?:s)? nothing", "A dry run must be described as inert")

    def test_native_configuration_owns_consent_selection_and_success_checks(self):
        text = read(NATIVE)
        connections = [line for line in commands(text) if re.search(r"\bconnect\b", line)]
        self.assertTrue(connections, "Keep a connect example on the connect page")
        for command in connections:
            self.assertRegex(command, r"^npx relaymessenger@staging connect\b|^npx relaymessenger connect\b",
                             "connect is the front door; examples name it directly")
        scripted = [line for line in connections if "--json" in line and "--dry-run" not in line]
        self.assertTrue(scripted, "Show the scripted form")
        for command in scripted:
            for flag in ("--yes", "--allow"):
                self.assertIn(flag, command, "A scripted connect needs consent and senders spelled out")
        for flag in ("--token", "--allow", "--yes", "--dry-run", "--no-start",
                     "RELAY_ALLOWED_SENDERS", "RELAY_CHANNEL_DIR"):
            self.assertIn(flag, text)
        for pattern, message in (
            (r"owner.only", "Credential files remain private"),
            (r"sender permissions", "Configuration must preserve permission policy"),
            (r"take the plan as it is", "Use the shipped consent description"),
            (r"first message", "Pairing waits for the first message"),
            (r"reply arrives.*same chat", "Verify an actual reply, not only configuration"),
            (r"does not\s+prove", "A written config is not connection proof"),
        ):
            self.assertConcept(text, pattern, message)
        self.assertIn('"dry_run": true', text)
        self.assertIn('"agent": "claude-code"', text)
        self.assertNotIn('"connected"', text, "Do not invent a connection field the CLI does not print")
        for runtime in ("openclaw", "hermes", "claude-code"):
            page = f"integrations/{runtime}.mdx"
            self.assertLink(page, "/integrations/native-setup")
            self.assertNotRegex("\n".join(commands(read(page))), r"\bconnect\b.*--(?:yes|allow|token)",
                                "Keep connect flags canonical on the connect page")

    def test_native_admission_stays_with_the_runtime_setup(self):
        openclaw = read("integrations/openclaw.mdx")
        claude = read("integrations/claude-code.mdx")
        hermes = read("integrations/hermes.mdx")
        for text in (openclaw, claude, hermes):
            self.assertConcept(text, r"zero saved webhook subscriptions", "Native channels use the WebSocket path")
        for pattern in (r"allowfrom", r"contact uuids", r"stable.id", r"session scope", r"token.*api origin"):
            self.assertConcept(openclaw, pattern, "Keep account-specific admission and session boundaries")
        self.assertConcept(claude, r"allowlist", "Claude requires explicit sender permission")
        self.assertConcept(claude, r"permission prompts remain local", "Relay cannot grant Claude tool permissions")
        self.assertConcept(claude, r"separate.*model contexts", "Sender admission is not context isolation")
        for marker in ("RELAY_ALLOWED_CONTACTS", "RELAY_STATE_DIR"):
            self.assertIn(marker, hermes)
        self.assertConcept(hermes, r"active profile", "Hermes credentials resolve per profile")
        self.assertConcept(hermes, r"slash commands.*withheld", "Remote chat cannot run operator slash commands")
        self.assertConcept(hermes, r"operator commands.*trusted local", "Keep the trusted operator path")

    def test_api_mcp_and_docs_search_have_one_explanation(self):
        self.assertIn("stdio", read(MCP))
        self.assertConcept(read(MCP), r"trusted local", "The MCP host is the security boundary")
        self.assertIn("RELAY_PROFILE", read(MCP))
        text = read(SKILLS)
        self.assertIn(f"https://{origin('docs.staging.relayapp.im')}/mcp", text)
        self.assertConcept(text, r"docs mcp.*none.*read.only", "Docs search needs no Agent Token")
        self.assertConcept(text, r"api mcp.*agent token", "API tools require an Agent Token")
        self.assertConcept(text, r"installing a skill alone.*does not confirm", "Skill installation is not MCP connection proof")
        self.assertLink(SKILLS, "/integrations/mcp")
        for page in (MCP, "integrations/codex.mdx", "integrations/cursor.mdx"):
            self.assertLink(page, "/integrations/skills")

    def test_setup_pages_do_not_regrow_release_or_maintainer_checklists(self):
        for path in assigned_pages():
            with self.subTest(page=path.relative_to(ROOT)):
                # Empty bookmark aliases are not visible maintainer prose.
                # Leave headings and non-empty spans subject to every check.
                text = re.sub(
                    r"""<span\s+id=(["'])[^"']+\1\s*(?:/\s*>|>\s*</span\s*>)""",
                    "",
                    path.read_text(),
                    flags=re.I,
                )
                self.assertNotRegex(text, r"(?i)test:live|hosted.proof|lockfile|registry integrity|sha(?:256|512)-")
                self.assertNotRegex(text, r"(?im)^## (?:Package versions|Package status)\s*$")
                self.assertNotRegex(text, r"(?i)\bcoming[- ]soon\b|\bsource[- ]only\b")
        self.assertLink("integrations/chat-sdk.mdx", "/guides/messaging/attachments")
        self.assertNotRegex(
            normalized(read("integrations/chat-sdk.mdx")),
            r"rejects.{0,40}(?:local byte|file upload)",
            "Current adapter source supports file-byte uploads",
        )
        for recipe in ("send-a-message", "send-an-image", "send-a-voice-memo"):
            self.assertIn(f"/cookbook/{recipe}", read("examples/index.mdx"))

    def test_safety_guard_detects_literal_token_or_production_origin(self):
        example = "```bash\nnpx relaymessenger@staging connect claude --token \"$RELAY_AGENT_TOKEN\" --yes\n```\n"
        self.assertEqual(connect_command_errors(example), [])
        self.assertTrue(connect_command_errors(example.replace('"$RELAY_AGENT_TOKEN"', "rly_live_abc123")))
        self.assertTrue(connect_command_errors(example.replace("--yes", "--api-url https://api.relayapp.im")))
        self.assertTrue(connect_command_errors("```bash\nnpx relaymessenger@staging doctor\n```\n"))

    def test_fenced_headings_do_not_inflate_the_task_budget(self):
        example = "## Install\n```bash\n## shell comment, not a section\n```\n## See also\n"
        self.assertEqual(re.findall(r"^## (.+)$", prose(example), re.M), ["Install", "See also"])

    def test_link_guard_checks_fragments_and_redirects(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "guide.mdx"
            source.write_text("## Install\n## See also\n")
            redirects = {"/old-guide": "/guide#install", "/cycle": "/cycle"}
            self.assertIsNone(local_link_error(root, source, "/guide#install", redirects))
            self.assertIsNone(local_link_error(root, source, "#see-also", redirects))
            self.assertIsNone(local_link_error(root, source, "/old-guide", redirects))
            self.assertEqual(local_link_error(root, source, "/missing", redirects), "missing page: /missing")
            self.assertEqual(local_link_error(root, source, "/guide#missing", redirects), "missing anchor: /guide#missing")
            self.assertEqual(local_link_error(root, source, "/cycle", redirects), "redirect cycle: /cycle")


if __name__ == "__main__":
    unittest.main()
