#!/usr/bin/env python3
"""Check onboarding contracts and task boundaries, not a page's exact prose.

Wire shapes remain pinned independently of the human guides. Task checks follow
owning pages and their links, so a router need not repeat credential, image, or
runtime instructions. Runtime enforcement is tested in the owning SDK/Server.
"""
import json
import re
import unittest
from pathlib import Path
from urllib.parse import urlsplit

from origins import origin, production_text, target

ROOT = Path(__file__).resolve().parents[1]
AGENT_PAGES = tuple(f"agents/{name}" for name in (
    "lifecycle", "create-agent", "create-agent-api", "list-agents",
    "delete-agent",
))
# The Console page moved into the Console group (owner, 2026-09-11); it keeps
# every guarantee the agent pages have, at its own path.
CONSOLE_AGENT_PAGE = "console/agents"
CLI_TASKS = tuple(f"cli/{name}" for name in (
    "auth", "watch",
))
PHOTO_PAGE = "agents/profile-photos"
RECIPE_PAGE = "agents/image-recipes"
OBSERVER_PAGE = "websocket/observe-events"
PROMPT_PAGE = "integrations/agent-prompt"


def expected(value):
    return production_text(value) if target() == "production" else value


def route(href):
    """Compare an owning page across local links and hosted Markdown links."""
    url = urlsplit(href)
    if url.netloc and url.netloc not in {
        "docs.staging.relayapp.im", "docs.relayapp.im",
    }:
        return None
    path = re.sub(r"\.(?:mdx|md)$", "", url.path.strip("/"))
    return path.removesuffix("/index")


def links(text):
    markdown = re.findall(r'(?<!!)\[[^\]\n]*\]\(([^\s)]+)', text)
    components = re.findall(r'''\bhref=["']([^"']+)["']''', text)
    return {route(href) for href in (*markdown, *components)}


def code_blocks(text, language):
    return re.findall(
        rf"^```{re.escape(language)}(?:[ \t]+[^\n]*)?\n(.*?)^```[ \t]*$",
        text, re.M | re.S,
    )


def visible_document_text(text):
    """Empty bookmark spans are routing metadata, not product prose."""
    return re.sub(
        r"""<span\b(?=[^>]*\bid\s*=)[^>]*(?:/\s*>|>\s*</span\s*>)""",
        "", text, flags=re.I,
    )


def command_examples(text):
    """Read executable examples and inline commands, not ordinary link labels."""
    text = visible_document_text(text)
    shell = [block for language in ("bash", "sh", "shell", "zsh", "powershell", "console")
             for block in code_blocks(text, language)]
    # A text fence may be either a terminal command or a full agent prompt.
    # Keep explicit invocations without treating the prompt's prose as shell.
    text_commands = [line for block in code_blocks(text, "text")
                     for line in block.splitlines()
                     if re.match(r"\s*(?:npx\s+relaymessenger|relaymessenger|relay)\b", line)]
    inline = [match.group(2) for match in re.finditer(
        r"(?<!`)(`{1,2})(?!`)([^\n]*?)\1(?!`)", text,
    )]
    return "\n".join((*shell, *text_commands, *inline))


def objects(value):
    """Walk nested navigation or JSON without depending on group ordering."""
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from objects(child)


def navigation_pages(value):
    return {
        page for node in objects(value) for page in node.get("pages", [])
        if isinstance(page, str)
    }


class AgentOnboardingTests(unittest.TestCase):
    def page(self, slug):
        slug = route(slug)
        candidates = (ROOT / f"{slug}.mdx", ROOT / slug / "index.mdx",
                      ROOT / f"{slug}.md")
        path = next((path for path in candidates if path.is_file()), None)
        self.assertIsNotNone(path, f"Missing owning documentation page: {slug}")
        return path.read_text()

    def assert_links_to_pages(self, text, *slugs):
        for slug in slugs:
            with self.subTest(destination=slug):
                self.page(slug)
                self.assertIn(route(slug), links(text), f"Missing task link: {slug}")

    def assert_identifiers(self, text, *identifiers):
        # Flags and wire identifiers are stable; wrapping and prose are not.
        normalized = " ".join(visible_document_text(text).replace("\\\n", " ").split())
        for identifier in identifiers:
            with self.subTest(identifier=identifier):
                self.assertIn(expected(identifier), normalized)

    def assert_concept(self, text, pattern):
        normalized = " ".join(visible_document_text(text).replace("`", "").split())
        self.assertRegex(normalized, re.compile(pattern, re.I))

    def json_examples(self, text):
        return [json.loads(block) for block in code_blocks(text, "json")]

    def assert_operation_link(self, text, operation):
        paths = json.loads((ROOT / "scripts/api-page-paths.json").read_text())
        self.assertIn(route(paths[operation]["href"]), links(text))

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

    def test_cli_front_door_routes_to_owning_tasks(self):
        cli = self.page("cli/index")
        versions = json.loads((ROOT / "versions.json").read_text())
        cli_versions = versions["npm"]["relaymessenger"]
        self.assert_identifiers(
            cli,
            f"npx relaymessenger@{cli_versions['staging']} --help",
            "--json",
        )
        self.assert_links_to_pages(
            cli, *CLI_TASKS, "agents/create-agent",
            "agents/list-agents", "agents/delete-agent",
            "integrations/claude-code", "integrations/skills",
        )
        # Both released CLI channels have these operations. Do not require a
        # dated availability announcement or a particular tutorial order.
        for slug in ("cli/index", *CLI_TASKS, *AGENT_PAGES, CONSOLE_AGENT_PAGE):
            self.assertNotRegex(visible_document_text(self.page(slug)),
                                r"(?i)\bcoming soon\b|\bcoming release\b")

    def test_prose_checks_ignore_empty_bookmarks_not_visible_content(self):
        text = (
            '<span id="prepare-hosted-proof" />\n'
            "<span id='agents setup'></span>\n"
            '<span id="visible">Keep tokens private.</span>\n'
        )
        visible = visible_document_text(text)
        self.assertNotIn("prepare-hosted-proof", visible)
        self.assertNotIn("agents setup", visible)
        self.assertIn("Keep tokens private.", visible)

    def test_command_checks_distinguish_link_labels_from_commands(self):
        prose = "[agents setup](/cli/auth)"
        self.assertNotIn("agents setup", command_examples(prose))
        for example in (
            "`agents setup`",
            "```bash\nnpx relaymessenger agents setup\n```",
            "```powershell\nrelaymessenger agents setup\n```",
            "```text\nnpx relaymessenger agents setup\n```",
        ):
            with self.subTest(example=example):
                self.assertIn("agents setup", command_examples(example))

    def test_no_invented_cli_package_or_commands(self):
        for path in ROOT.rglob("*.mdx"):
            if {"node_modules", ".git", ".mint"} & set(path.parts):
                continue
            text = visible_document_text(path.read_text())
            commands = command_examples(text)
            with self.subTest(path=path.relative_to(ROOT)):
                for obsolete in ("@relaymessenger/cli", "relaymessenger@latest"):
                    self.assertNotIn(obsolete, text)
                # Retired with the 2026-09-09 CLI rebuild (Relay-SDK PR 176):
                # the runtime-configuration flags on auth login, and the
                # acknowledged listener. The retired top-level commands are
                # spelled as patterns so this guard does not itself match a
                # sweep of the docs for the retired words.
                for obsolete in ("agents setup", "--token-stdin", "--from-env",
                                 "auth login --connect", "--confirm-configure",
                                 "--runtime-stopped", "--acknowledge-events"):
                    self.assertNotIn(obsolete, commands)
                self.assertNotRegex(commands, r"\btoken (?:import|status|clear)\b|\bevents\s+listen\b")
                self.assertNotRegex(commands, r"(?m)^\s*relay (?:agents|profiles|doctor|events|connect|watch)\b")

    def test_agent_management_router_is_short_and_links_to_tasks(self):
        router = self.page("agents/lifecycle")
        self.assertLess(len(router.splitlines()), 50)
        self.assert_links_to_pages(router, *AGENT_PAGES[1:], CONSOLE_AGENT_PAGE,
                                   PHOTO_PAGE, "integrations/claude-code")
        self.assertFalse(code_blocks(router, "bash"))
        self.assertFalse(code_blocks(router, "typescript"))

    def test_cli_creation_and_api_storage_have_separate_owners(self):
        create = self.page("agents/create-agent")
        self.assert_identifiers(create, "npx relaymessenger@staging agents create",
                                "https://api.staging.relayapp.im", "--profile")
        self.assert_links_to_pages(create, "agents/create-agent-api", PHOTO_PAGE)
        self.assert_operation_link(create, "createAgent")
        self.assert_concept(create, r"(?:Relay )?Console|sign in")
        self.assert_concept(create, r"uncertain|unconfirmed")
        self.assert_concept(create, r"(?:no|never|not|without).{0,30}automatic\w* retr")

        api = self.page("agents/create-agent-api")
        self.assert_identifiers(api, "Relay.createAgent", "maxRetries: 0", "mode: 0o600",
                                'flag: "wx"', "Retry-After", "8192", "Cache-Control: no-store")
        self.assert_operation_link(api, "createAgent")
        sdk = "\n".join(code_blocks(api, "typescript"))
        https = "\n".join(code_blocks(api, "bash"))
        self.assertLess(sdk.index("mkdtemp("), sdk.index("Relay.createAgent("))
        self.assertLess(sdk.index("writeFile("), sdk.index("console.log("))
        self.assertNotRegex(sdk, r"console\.log\(\s*created(?:\.secret)?\s*\)")
        self.assert_identifiers(https, "umask 077", "mktemp -d", "--output", "POST", "/v1/agents")
        self.assertLess(https.index("mktemp -d"), https.index("curl "))
        self.assertNotRegex(https, r"--retry\b|Authorization:")
        self.assert_links_to_pages(api, PHOTO_PAGE)

    def test_cli_agent_json_is_flat_safe_and_consistent(self):
        created = [item for item in self.json_examples(self.page("agents/create-agent"))
                   if isinstance(item, dict) and "profile" in item]
        self.assertEqual(len(created), 1)
        record = created[0]
        keys = {"profile", "handle", "display_name", "image_url", "share_url", "api_url", "token"}
        self.assertEqual(set(record), keys)
        self.assertEqual(record["token"], "stored")
        self.assertEqual(record["api_url"], f"https://{origin('api.staging.relayapp.im')}")
        self.assertTrue(record["share_url"].startswith("https://"))
        self.assertTrue(urlsplit(record["share_url"]).path.endswith(f'/@{record["handle"]}'))
        self.assertIn(urlsplit(record["share_url"]).hostname, {
            origin("staging.relayapp.im"), origin("go.staging.relayapp.im"),
        })

        listing = self.page("agents/list-agents")
        self.assert_identifiers(listing, "agents list --json")
        examples = self.json_examples(listing)
        inventories = [item for item in examples if isinstance(item, dict) and "agents" in item]
        self.assertEqual(len(inventories), 1)
        self.assertEqual(set(inventories[0]), {"agents"})
        self.assertEqual(inventories[0]["agents"], [{key: record[key] for key in keys - {"share_url"}}])
        failures = [item for item in examples if isinstance(item, dict) and "error" in item]
        self.assertEqual(len(failures), 1)
        self.assertEqual(set(failures[0]), {"profile", "api_url", "token", "error"})
        self.assertEqual(failures[0]["error"], "Agent details unavailable")
        self.assertEqual(failures[0]["token"], "stored")
        self.assert_concept(listing, r"local\w* (?:CLI )?(?:profile|config|sav)")
        self.assert_concept(listing, r"(?:each|own).{0,90}(?:saved token|saved credential)")

    def test_delete_keeps_identity_authorization_history_and_retry_safety(self):
        delete = self.page("agents/delete-agent")
        self.assert_identifiers(delete, "--profile", "agents delete", "relay.agents.delete",
                                "Authorization: Bearer $RELAY_AGENT_TOKEN", "--json")
        self.assert_operation_link(delete, "deleteAgent")
        for concept in (r"irreversib", r"archiv", r"revok", r"history.{0,35}retain",
                        r"same (?:identity|Handle)|exact Handle", r"pending.{0,30}WebSocket|WebSocket.{0,30}pending",
                        r"durabl", r"409", r"(?:keep|retain).{0,40}(?:local )?credentials"):
            self.assert_concept(delete, concept)
        results = self.json_examples(delete)
        self.assertTrue(any(item.get("ok") is True and item.get("token") == "removed"
                            for item in results if isinstance(item, dict)))
        self.assert_links_to_pages(delete, "agents/list-agents", "websocket")

    def test_authentication_keeps_private_input_and_profile_selection(self):
        auth = self.page("cli/auth")
        self.assert_identifiers(auth, "Get-Content -Raw $TokenFile", "auth login --with-token",
                                "auth status", "auth logout", "--profile", "relay login",
                                "RELAY_AGENT_TOKEN")
        self.assert_concept(auth, r"browser|signs this computer in")
        self.assert_concept(auth, r"(?:never|not).{0,35}command arguments")
        self.assert_links_to_pages(auth, "agents/create-agent", "agents/delete-agent",
                                   "integrations/claude-code")

    def test_start_supports_anonymous_or_existing_token_without_console(self):
        skill = self.page("skill")
        start = skill.split("## Start\n", 1)[1].split("\n## ", 1)[0]
        self.assert_identifiers(start, "POST /v1/agents", "Agent Token", "RELAY_API_URL",
                                "GET /v1/chats?limit=1", "event_id", "/v1/websocket")
        self.assert_concept(start, r"anonymous|unauthenticated")
        self.assert_concept(start, r"existing.{0,25}Agent Token")
        self.assert_concept(start, r"(?:Neither|without|no|not requir).{0,80}Console account")
        self.assertNotRegex(start, r"created in that environment.s\s+Console")
        self.assert_links_to_pages(skill, "agents/create-agent", "cli/auth",
                                   "integrations/claude-code", PHOTO_PAGE, "agents/delete-agent",
                                   "integrations/skills")

    def test_full_prompt_has_one_generated_owner_and_no_greeting(self):
        skill = self.page("skill")
        prompt = self.page(PROMPT_PAGE)
        self.assertIn("## Start\n", skill)
        vocabulary = skill.split("## Vocabulary\n", 1)[1].split("\n## ", 1)[0]
        self.assert_identifiers(vocabulary, "Contact", "Handle", "Chat", "Message", "part_index")
        # The first Message is the request (2026-09-09), so no setup step may
        # teach a scripted opener; contact.added still names the direct Chat.
        self.assertNotRegex(skill, r"(?i)\bgreeting")
        self.assertNotIn("Hello, I'm here", skill)
        self.assert_identifiers(skill, "contact.added")
        visible = re.search(r"^````text Relay agent prompt\n(.*?)^````$", prompt, re.M | re.S)
        self.assertIsNotNone(visible)
        self.assertEqual(visible.group(1), (ROOT / "agent-prompt.md").read_text())
        # Owner ruling 2026-09-11 (final tree): the main page is an overview
        # and the quickstart owns coding-agent onboarding, so the quickstart
        # carries the link to the prompt. The main page still may not embed it.
        self.assert_links_to_pages(self.page("start/quickstart"), PROMPT_PAGE)
        main = self.page("index")
        self.assertNotIn("````text Relay agent prompt", main)
        config = json.loads((ROOT / "docs.json").read_text())
        self.assertTrue(any(link.get("href") == f"/{PROMPT_PAGE}#relay-agent-prompt"
                            for link in config["navbar"]["links"]))

    def test_native_guides_link_setup_without_dated_availability_claims(self):
        # Owner ruling 2026-09-12: no runtime is the default; sibling guides route to the runtimes index.
        for name in ("openclaw", "hermes"):
            with self.subTest(integration=name):
                text = self.page(f"integrations/{name}")
                self.assert_links_to_pages(text, "integrations/index")
        self.assert_identifiers(self.page("integrations/openclaw"),
                                "openclaw plugins install @relaymessenger/openclaw-plugin@staging")
        self.assert_identifiers(self.page("integrations/hermes"), "hermes plugins install")
        self.assert_identifiers(self.page("integrations/claude-code"),
                                "/plugin marketplace add RelayMessenger/Relay-SDK@staging")

    def test_custom_profile_uses_existing_recipe_and_rendered_image_pair(self):
        spec = (ROOT / "api-reference/openapi.yaml").read_text()
        request = spec.split("    CreateAgentRequest:\n", 1)[1].split("    AgentImageRecipe:\n", 1)[0]
        for field in ("handle:", "first_name:", "image_url:", "image_recipe:"):
            self.assertIn(field, request)
        self.assertIn("dependentRequired:", request)
        self.assertIn("image_recipe:\n          - image_url", request)
        # Field rules belong to the generated operation, rendering to recipes.
        self.assert_operation_link(self.page("agents/create-agent"), "createAgent")
        recipes = self.page(RECIPE_PAGE)
        self.assert_links_to_pages(self.page(PHOTO_PAGE), RECIPE_PAGE)
        self.assert_links_to_pages(recipes, PHOTO_PAGE)
        self.assert_identifiers(recipes, "image_recipe", "monogram", "linearGradient", "5B9BFA")
        # The public contract requires a rendered image and its recipe, not a
        # private Console renderer or a particular CLI presentation.
        sdk = [block for block in code_blocks(recipes, "typescript") if "image_recipe" in block]
        https = [block for block in code_blocks(recipes, "bash") if "image_recipe" in block]
        self.assertTrue(sdk, "Missing SDK recipe update example")
        self.assertTrue(https, "Missing HTTPS recipe update example")
        for example in (*sdk, *https):
            self.assertRegex(example, r'''["']?image_recipe["']?\s*:\s*\{''')
            self.assertRegex(example, r'''["']?(?:attachment_id|image_url)["']?\s*:''')
        for example in sdk:
            self.assertIn("relay.contactCard.update", example)
        for example in https:
            self.assert_identifiers(example, "/v1/contact_card",
                                    "Authorization: Bearer $RELAY_AGENT_TOKEN")
            self.assertRegex(example, r"(?:--request|-X)\s+PATCH\b")
        self.assert_concept(recipes, r"rendered|render\w* (?:image|PNG)")
        self.assert_concept(recipes, r"recipe.only.{0,70}(?:400|render)|(?:400|render).{0,70}recipe.only")
        for slug in ("agents/lifecycle", "agents/create-agent", "agents/create-agent-api"):
            self.assert_links_to_pages(self.page(slug), PHOTO_PAGE)
            self.assertNotRegex(self.page(slug), r'"recipe"\s*:\s*\{\s*"monogram"')

    def test_image_upload_uses_completed_owned_attachment_and_existing_profile_retry(self):
        photos = self.page(PHOTO_PAGE)
        self.assert_identifiers(photos, "attachment_id", "image_url", "relay.contactCard.update",
                                "/v1/contact_card", "Authorization: Bearer $RELAY_AGENT_TOKEN")
        for language in ("typescript", "bash"):
            examples = [block for block in code_blocks(photos, language) if "attachment_id" in block]
            self.assertTrue(examples, f"Missing {language} completed-attachment update")
            for example in examples:
                if language == "typescript":
                    self.assertIn("relay.contactCard.update", example)
                else:
                    self.assertRegex(example, r"(?:--request|-X)\s+PATCH\b")
        self.assert_links_to_pages(photos, "messages/attachments", "agents/contact-card")
        for concept in (r"complet", r"own\w*|same agent", r"public.{0,30}(?:image|storage)",
                        r"retry.{0,90}(?:same|existing|saved).{0,30}(?:agent|profile|identity)"):
            self.assert_concept(photos, concept)
        self.assert_links_to_pages(self.page("agents/contact-card"), PHOTO_PAGE)
        # The canonical shape, rather than an English sentence in a router,
        # proves completion, same-agent ownership, and mutually exclusive inputs.
        for schema in ("SetContactCardRequest", "UpdateContactCardRequest"):
            body = spec_section((ROOT / "api-reference/openapi.yaml").read_text(), schema)
            self.assertIn("not:\n        required: [image_url, attachment_id]", body)
            self.assertIn("- required: [attachment_id]", body)
            self.assertIn("- required: [image_url]", body)
            self.assertRegex(body, r"attachment_id:\s+type: string\s+format: uuid")
            self.assertNotRegex(body, r"format:\s*(?:binary|byte)\b")
            self.assertRegex(body, r"(?i)complete")
            self.assertRegex(body, r"authenticated agent|This agent's")
            self.assertRegex(body, r"permanent public")

    def test_released_ux_preserves_script_and_observer_behavior(self):
        observer = self.page("cli/watch")
        self.assert_identifiers(observer, "watch", "--profile", "--json",
                                "Ctrl-C", "observe=true", "observational: true", "full_sync_complete")
        self.assert_concept(observer, r"read.only|watches only")
        self.assert_concept(observer, r"(?:neither|never|not|no).{0,45}(?:ACK|acknowledg)")
        self.assert_concept(observer, r"runtime.{0,40}consumer|consumer.{0,40}runtime")
        self.assertTrue(any(re.match(r"\s*npx relaymessenger\S* watch\b", line)
                            for line in command_examples(observer).splitlines()))
        self.assert_links_to_pages(observer, "integrations/claude-code", OBSERVER_PAGE)

    def test_optional_skill_installation_preserves_consent_and_secret_isolation(self):
        skills = self.page("integrations/skills")
        self.assert_identifiers(skills, "skills@1.5.24", "--skill relay")
        self.assert_concept(skills, r"opt.in|optional|consent")
        self.assert_concept(skills, r"declin|cancel")
        self.assert_concept(skills, r"before.{0,20}setup")
        # Check the operator's confirmation and credential boundaries here.
        # Detection states and environment filtering remain SDK implementation
        # tests, not required paragraphs in the installation task.
        self.assert_concept(skills, r"confirm.{0,120}(?:appears|installed)")
        self.assert_concept(skills, r"install.{0,150}(?:not|never).{0,50}(?:confirm|connect)")
        docs_mcp_rows = [row for row in skills.splitlines()
                         if row.strip().startswith("|") and "Docs MCP" in row]
        self.assertTrue(docs_mcp_rows)
        for row in docs_mcp_rows:
            self.assertRegex(row, r"\|\s*None\s*\|")
        self.assert_identifiers(skills, "Relay Agent Token")
        install_commands = [line for language in ("bash", "powershell")
                            for block in code_blocks(skills, language)
                            for line in block.replace("\\\n", " ").splitlines()
                            if re.search(r"\bnpx\s+skills@", line)]
        self.assertTrue(install_commands)
        for command in install_commands:
            self.assertNotRegex(
                command,
                r"\b[A-Z][A-Z0-9_]*_(?:API_KEY|TOKEN|SECRET)\b"
                r"|--(?:api-key|token|secret)\b|rly_live_",
            )
        skill = self.page("skill")
        self.assert_links_to_pages(skill, "integrations/skills")
        self.assert_concept(skill, r"separate.{0,40}consent")
        self.assert_concept(skill, r"credential consent.{0,60}(?:not|never).{0,40}install")
        self.assert_links_to_pages(skills, "cli/index", "integrations/mcp")

    def test_observer_wire_is_canonical_and_distinct_from_ack_consumer(self):
        spec = (ROOT / "api-reference/openapi.yaml").read_text()
        socket = spec.split("  /v1/websocket:\n", 1)[1].split("\ncomponents:", 1)[0]
        self.assertIn("name: observe", socket)
        self.assertIn("observational:true", socket)
        self.assertIn("ACK and full_sync_complete frames are rejected", socket)
        observer = self.page(OBSERVER_PAGE)
        self.assert_identifiers(observer, "observe=true", "full_sync_complete", "invalid_frame")
        self.assert_concept(observer, r"connection.local.{0,30}cursor")
        ready = [item for item in self.json_examples(observer) if item.get("type") == "ready"]
        self.assertTrue(ready)
        for frame in ready:
            self.assertIs(frame.get("observational"), True)
            self.assertIs(frame.get("full_sync_required"), False)
            self.assertIsNone(frame["full_sync_through"])
        self.assert_links_to_pages(self.page("websocket"), OBSERVER_PAGE)

    def test_released_agent_admission_keeps_authorization_and_session_caveats(self):
        openclaw = self.page("integrations/openclaw")
        claude = self.page("integrations/claude-code")
        self.assert_identifiers(openclaw, ">=2026.8.1 <2026.9.0", "allowFrom")
        self.assert_concept(openclaw, r"Contact UUID")
        self.assert_concept(openclaw, r"stable.ID")
        self.assert_concept(openclaw, r"dmScope|DM session scope")
        self.assert_links_to_pages(openclaw, "websocket/full-sync")
        self.assert_concept(self.page("websocket/full-sync"), r"snapshot")
        for text in (openclaw, claude):
            self.assert_concept(text, r"agent Contacts?")
            self.assert_concept(text, r"allowlist|allowFrom")
            self.assert_concept(text, r"session")
            # Owner ruling 2026-09-12: the CLI sets the API origin, so a
            # runtime page never tells the user to set RELAY_API_URL.
            self.assertNotIn("RELAY_API_URL", text)
        self.assert_concept(claude, r"reply.origin")
        self.assert_concept(claude, r"contact\.is_me|agent.s own delivery row")
        self.assert_concept(claude, r"authenticat")
        self.assert_concept(claude, r"FULL sync")

    def test_new_pages_and_operations_are_integrated(self):
        config = json.loads((ROOT / "docs.json").read_text())
        navigation = navigation_pages(config["navigation"])
        for slug in (*AGENT_PAGES, CONSOLE_AGENT_PAGE, *CLI_TASKS, PHOTO_PAGE, RECIPE_PAGE, OBSERVER_PAGE, PROMPT_PAGE,
                     "integrations/claude-code", "api-reference/resources/agents/overview"):
            with self.subTest(page=slug):
                self.page(slug)
                self.assertIn(slug, navigation)
        for operation in ("POST /v1/agents", "DELETE /v1/agents/{handle}"):
            self.assertIn(operation, navigation)

    def test_getting_started_excludes_management_ai_and_checklist_pages(self):
        config = json.loads((ROOT / "docs.json").read_text())
        groups = [node for node in objects(config["navigation"])
                  if node.get("group", "").casefold() == "getting started"]
        self.assertTrue(groups, "Getting started navigation group is missing")
        # Owner ruling 2026-09-11 (final tree): the reliability checklist now
        # closes Getting started. Agent management and the copyable AI
        # instructions still belong to their own groups.
        forbidden = {"agents/lifecycle", "integrations/claude-code", PROMPT_PAGE}
        for group in groups:
            self.assertFalse(forbidden & navigation_pages(group),
                             "Management and AI instructions belong outside Getting started")


def spec_section(source, name):
    """Read one top-level schema without changing the pinned contract input."""
    return re.split(r"\n    [A-Za-z][A-Za-z0-9_]*:\n",
                    source.split(f"    {name}:\n", 1)[1], maxsplit=1)[0]


if __name__ == "__main__":
    unittest.main()
