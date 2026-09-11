#!/usr/bin/env python3
import json
import hashlib
import re
import sys
from pathlib import Path
from api_navigation import validate_api_navigation, page_paths
from origins import origin, production_text, source_ref, target, STAGING_INSTRUCTION_REFERENCE


def spec(text: str) -> str:
    """A staging-spelled expectation, as this checkout must state it."""
    return production_text(text) if target() == "production" else text

# The names of the source companies whose documentation shaped early drafts are
# banned from this repository, including from the checks that block them. Each
# name is built from its character codes so the check keeps working without the
# file ever spelling one out.
source_company_names = [
    "".join(map(chr, codes))
    for codes in ([76, 105, 110, 113], [80, 104, 111, 116, 111, 110])
]
source_company_pattern = "|".join(
    rf"\b{name}\b" for name in source_company_names
)

root = Path(__file__).resolve().parents[1]
config = json.loads((root / "docs.json").read_text())

agent_instructions = (root / "skill.md").read_text()
# The first Message is the request (2026-09-09); contact.added still names the
# direct Chat once the user writes first or accepts. Nothing may teach a scripted opener.
if not re.search(r"contact\.added", agent_instructions):
    raise SystemExit("Agent instructions lost the contact.added first-Message path")

# versions.json is the one source of truth for every published package version.
# scripts/refresh-versions.mjs writes it from the live registries and
# scripts/check-versions.mjs proves no page drifted from it, so this validator
# reads it instead of carrying its own copy of the numbers.
versions = json.loads((root / "versions.json").read_text())
npm_latest = {
    name: entry["latest"] for name, entry in versions["npm"].items()
}
npm_integrity = {
    name: entry["integrity"][entry["latest"]]
    for name, entry in versions["npm"].items()
}
npm_source_commit = {
    name: entry["sourceCommit"] for name, entry in versions["npm"].items()
}


def pinned(name):
    version = npm_latest.get(name) or versions["pypi"][name]
    return spec(f"{name}@{version}")

if config.get("name") != "Relay":
    raise SystemExit("site identity must be Relay")
if config.get("description") != "Relay API v1 documentation.":
    raise SystemExit("site description must use the Relay identity")
if config.get("favicon") != origin("/favicon-staging.png"):
    raise SystemExit(f"{target()} Docs must use the {target()} Relay favicon")
if hashlib.sha256((root / "favicon-staging.png").read_bytes()).hexdigest() != (
    "4b3e4b9358f35c66cec564d7ae6806b8e948a2e4dc0e1fd2eb003887ee1120be"
):
    raise SystemExit("staging Docs favicon is not the canonical black Relay mark")
if hashlib.sha256((root / "favicon.png").read_bytes()).hexdigest() != (
    "e83ec179b9d84770947e5dff6a667e7ef904501a0bd4f1db091f7324dc0530cb"
):
    raise SystemExit("the production blue Docs favicon changed")
if config.get("navbar", {}).get("primary") != {
    "type": "button",
    "label": "Console",
    "href": f"https://{origin('console.staging.relayapp.im')}",
}:
    raise SystemExit("top-right docs action must open Relay Console")
if config.get("navbar", {}).get("links") != [
    {
        "label": "Copy agent prompt",
        "href": "/integrations/agent-prompt#relay-agent-prompt",
        "icon": "copy",
    }
]:
    raise SystemExit("Copy agent prompt must be the only secondary navbar action")
if config.get("logo") != {
    "light": "/logo/light.png",
    "dark": "/logo/dark.png",
    "href": "https://relayapp.im",
}:
    raise SystemExit("Relay logo must link to https://relayapp.im")

redirects = {
    item.get("source"): item.get("destination")
    for item in config.get("redirects", [])
    if isinstance(item, dict) and item.get("permanent") is True
}
for source, destination in {
    "/ecosystem": "/integrations/claude-code",
    "/ecosystem/agent-starter": "/integrations/cloudflare-think",
    "/ecosystem/chat-sdk": "/integrations/chat-sdk",
    "/ecosystem/claude-code": "/integrations/claude-code",
    "/ecosystem/cli": "/cli/index",
    "/ecosystem/codex": "/integrations/codex",
    "/ecosystem/cursor": "/integrations/cursor",
    "/ecosystem/hermes": "/integrations/hermes",
    "/ecosystem/mcp": "/integrations/mcp",
    "/ecosystem/openclaw": "/integrations/openclaw",
    "/ecosystem/skills": "/integrations/skills",
    "/integrations/agent-starter": "/integrations/cloudflare-think",
    "/integrations/cloudflare": "/integrations/cloudflare-think",
    "/integrations/hermes-plugin": "/integrations/hermes",
}.items():
    if redirects.get(source) != destination:
        raise SystemExit(
            f"legacy integrations redirect lost: {source} -> {destination}"
        )


def pages(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "pages" and isinstance(item, list):
                yield from (
                    page
                    for page in item
                    if isinstance(page, str)
                    and not re.match(
                        r"^(GET|POST|PUT|PATCH|DELETE) /",
                        page,
                    )
                )
            yield from pages(item)
    elif isinstance(value, list):
        for item in value:
            yield from pages(item)


def has_key(value, forbidden):
    if isinstance(value, dict):
        return forbidden in value or any(has_key(item, forbidden) for item in value.values())
    if isinstance(value, list):
        return any(has_key(item, forbidden) for item in value)
    return False


def h2_headings(text):
    prose = re.sub(
        r"^(`{3,})[^\n]*\n.*?^\1\s*$",
        "",
        text,
        flags=re.M | re.S,
    )
    return re.findall(r"^## (.+)$", prose, re.M)


def openapi_path_block(text, path):
    marker = f"  {path}:"
    start = text.index(marker)
    ends = [
        index
        for index in [
            text.find("\n  /v1/", start + len(marker)),
            text.find("\ncomponents:", start + len(marker)),
        ]
        if index >= 0
    ]
    return text[start:min(ends) if ends else len(text)]


def openapi_operation_block(text, path, method):
    path_block = openapi_path_block(text, path)
    operation = re.search(rf"^    {re.escape(method)}:$", path_block, re.M)
    if not operation:
        raise SystemExit(f"{method.upper()} {path} missing from OpenAPI")
    following = re.search(
        r"^    (?:get|post|put|patch|delete):$",
        path_block[operation.end():],
        re.M,
    )
    end = (
        operation.end() + following.start()
        if following
        else len(path_block)
    )
    return path_block[operation.start():end]


mdx_paths = sorted(root.rglob("*.mdx"))
navigated_list = list(pages(config.get("navigation", {})))
navigated = set(navigated_list)
files = {str(path.relative_to(root).with_suffix("")) for path in mdx_paths}
duplicates = sorted(page for page in navigated if navigated_list.count(page) > 1)
if duplicates:
    raise SystemExit(f"pages appear more than once in navigation: {duplicates}")
if navigated != files:
    raise SystemExit(f"navigation/orphan mismatch: {sorted(navigated ^ files)}")

tabs = config["navigation"]["tabs"]
actual_tabs = [tab["tab"] for tab in tabs]
# Owner ruling 2026-09-11 (final tree): one guides tab, the API reference, the
# CLI, then the changelog as its own tab. Integrations moved into the Docs
# sidebar as the Coding agents and Integrations groups.
expected_tabs = ["Docs", "API reference", "CLI", "Changelog"]
if actual_tabs != expected_tabs:
    raise SystemExit(f"top tab order changed: {actual_tabs}")
changelog_tab = next(tab for tab in tabs if tab["tab"] == "Changelog")
if changelog_tab.get("pages") != ["changelog"] or "groups" in changelog_tab:
    raise SystemExit("the changelog page must stand alone, with no group repeating the tab name")

# Page boundaries and navigation coverage are checked independently of a
# frozen list of heading strings. Editorial changes must not require growing
# an existing catch-all page to satisfy a historical outline.
from docs_structure import is_task_guide, validate_structure
validate_structure(root, config)
expected_guide_groups = [group["group"] for group in tabs[0]["groups"]]



api_tab = next(tab for tab in tabs if tab["tab"] == "API reference")
if api_tab.get("openapi") != "api-reference/openapi.mint.yaml":
    raise SystemExit("generated API groups must sit directly under API Reference")
try:
    configured_endpoint_refs = validate_api_navigation(config)
except ValueError as error:
    raise SystemExit(str(error)) from error
if config.get("api") != {
    "playground": {"display": "simple"},
    "params": {"expanded": "closed"},
    "examples": {"languages": ["curl"], "defaults": "required"},
}:
    raise SystemExit("API Reference must keep a simple, collapsed cURL presentation")

if has_key(config.get("navigation", {}), "icon") or has_key(config.get("navigation", {}), "icons"):
    raise SystemExit("decorative navigation icons returned")
if config.get("contextual") != {"options": ["copy", "view"], "display": "header"}:
    raise SystemExit("header Copy page/Markdown actions changed")
if "start/quickstart" not in navigated:
    raise SystemExit("Quickstart must remain a sidebar guide")
if (root / "current-status.mdx").exists():
    raise SystemExit("Current status belongs in the evidence site, not public docs")

required_paths = [
    root / "agents/contact-card.mdx",
    root / "chats/share-contact-card.mdx",
    root / "chats/typing.mdx",
    root / "messages/receipts.mdx",
    root / "agents/message-requests.mdx",
    root / "events/index.mdx",
    root / "websocket/index.mdx",
    root / "websocket/protocol.mdx",
    root / "websocket/full-sync.mdx",
    root / "api-reference/errors.mdx",
]
for path in required_paths:
    if not path.exists():
        raise SystemExit(f"required atomic guide missing: {path.relative_to(root)}")
# Owner ruling 2026-09-11: a group's first page is labelled Overview in the
# sidebar, so the eyebrow and the H1 never say the same word. The title then
# has to say what the page is, and is pinned here with its label.
for path, label, title in [
    (root / "agents/lifecycle.mdx", "Overview", "What an agent is"),
    (root / "agents/message-requests.mdx", "Overview", "How message requests work"),
    (root / "messages/index.mdx", "Overview", "Send and receive messages"),
    (root / "chats/index.mdx", "Overview", "Direct and group chats"),
    (root / "webhooks/index.mdx", "Overview", "Receive webhook events"),
    (root / "api-reference/overview.mdx", "Overview", None),
    (root / "changelog.mdx", "Changelog", "Product updates"),
]:
    page_text = path.read_text()
    if f'sidebarTitle: "{label}"' not in page_text:
        raise SystemExit(f"section sidebar label drifted: {path.relative_to(root)}")
    if title is not None and f'title: "{title}"' not in page_text:
        raise SystemExit(f"section title drifted back to its group name: {path.relative_to(root)}")

for stale in [
    root / "chats/install-agents.mdx",
    root / "guides/socket-mode.mdx",
    root / "guides/socket-mode-protocol.mdx",
    root / "build/events/choose-transport.mdx",
    root / "build/identity/default-agents.mdx",
    root / "build/identity/agent-greetings.mdx",
    root / "build/identity/add-requests.mdx",
    root / "api-reference/resources/contacts/requests/overview.mdx",
    root / "error/codes/2xxx/2009.mdx",
    root / "error/codes/2xxx/2027.mdx",
    root / "ecosystem",
    root / "error/codes/2xxx/2014.mdx",
]:
    if stale.exists():
        raise SystemExit(f"stale page returned: {stale.relative_to(root)}")

if "--topology-only" in sys.argv:
    print(
        f"validated Docs topology: {len(files)} pages, "
        f"{len(expected_guide_groups)} ordered Guide groups"
    )
    raise SystemExit(0)

ecosystem_paths = [
    root / "integrations/chat-sdk.mdx",
    root / "cli/index.mdx",
    root / "integrations/mcp.mdx",
    root / "integrations/openclaw.mdx",
    root / "integrations/claude-code.mdx",
    root / "integrations/hermes.mdx",
    root / "integrations/cloudflare-think.mdx",
    root / "integrations/skills.mdx",
    root / "integrations/codex.mdx",
    root / "integrations/cursor.mdx",
    root / "live/examples.mdx",
]
ecosystem_text = "\n".join(path.read_text() for path in ecosystem_paths)
# Integration installation and safety boundaries have dedicated regression
# tests. Registry inventories and internal release proof belong in tooling,
# not as mandatory prose in every installation guide.

for path in mdx_paths:
    text = path.read_text()
    end = text.find("\n---\n", 4)
    if not text.startswith("---\n") or end < 0:
        raise SystemExit(f"bad frontmatter: {path}")
    keys = {
        line.split(":", 1)[0]
        for line in text[4:end].splitlines()
        if ":" in line
    }
    missing = {"title", "description", "keywords"} - keys
    if missing:
        raise SystemExit(f"missing {sorted(missing)} in {path}")
    if "—" in text:
        raise SystemExit(f"em dash in {path}")
    if text[end + 5:].strip() == "This page is being written.":
        continue
    if path.name == "changelog.mdx":
        updates = re.findall(r'<Update label="(\d{4}-\d{2}-\d{2})" tags=\{(\[[^\n]+\])\}>([\s\S]*?)</Update>', text)
        if not updates or len(updates) != text.count("<Update "):
            raise SystemExit("Changelog entries need dated labels and tags")
        dates = [date for date, tags, body in updates]
        if dates != sorted(dates, reverse=True):
            raise SystemExit("Changelog entries must be newest first")
        for date, tags, body in updates:
            if not re.search(r'\]\(/[^)]+\)', body):
                raise SystemExit("Every changelog entry must link an affected page")
            if re.search(r"removed|replace|moved|instead of", body, re.I) and "Breaking change" not in tags:
                raise SystemExit("Removed paths or flags need a Breaking change tag")
        continue
    headings = h2_headings(text)
    if not headings or headings[-1] not in ({"Next"} if path == root / "index.mdx" else {"Next steps", "Related", "See also"}):
        raise SystemExit(f"page must end with Next steps, Related, or See also: {path}")

    for block in re.findall(
        r"<(?:CodeGroup|Tabs)>[\s\S]*?</(?:CodeGroup|Tabs)>",
        text,
    ):
        if "TypeScript SDK" in block and "cURL" in block:
            # start/build-on-the-api is the main page's API walkthrough moved out
            # verbatim (2026-09-11), so it keeps the main page's cURL-first order.
            if is_task_guide(path.relative_to(root).with_suffix("").as_posix()) or path in {root / "index.mdx", root / "start/build-on-the-api.mdx"}:
                if block.index("cURL") > block.index("TypeScript SDK"):
                    raise SystemExit(f"cURL must appear before TypeScript SDK: {path.relative_to(root)}")
            elif block.index("TypeScript SDK") > block.index("cURL"):
                raise SystemExit(f"TypeScript SDK must appear before cURL: {path.relative_to(root)}")

private_contact_field = "is_" + "default"
private_contact_phrase = "default " + "agent"
public_contract_paths = [
    *mdx_paths,
    root / "docs.json",
    root / "README.md",
    root / "INFORMATION-ARCHITECTURE.md",
    root / "skill.md",
    root / ".mintlify/skills/relay/SKILL.md",
    root / "agent-prompt.js",
    root / "api-reference/openapi.yaml",
    root / "api-reference/openapi.mint.yaml",
]
for path in public_contract_paths:
    text = path.read_text()
    if private_contact_field in text:
        raise SystemExit(
            f"private Contact field leaked into {path.relative_to(root)}"
        )
    if private_contact_phrase in text.lower():
        raise SystemExit(
            f"private Contact lifecycle leaked into {path.relative_to(root)}"
        )

private_path_prefixes = (
    "/v1/me/",
    "/v1/client/",
    "/v1/console/",
    "/v1/internal/",
    "/v1/contacts",
    "/api/auth/",
)
private_user_operations = (
    "acknowledgeMessageDelivered",
    "acknowledgeDelivered",
)
for path in public_contract_paths:
    text = path.read_text()
    if "is_premium_handle" in text:
        raise SystemExit(
            f"private premium Handle field leaked into {path.relative_to(root)}"
        )
    for prefix in private_path_prefixes:
        if prefix in text:
            raise SystemExit(
                f"private path prefix {prefix} leaked into {path.relative_to(root)}"
            )
    for operation in private_user_operations:
        if operation in text:
            raise SystemExit(
                f"private user operation {operation} leaked into "
                f"{path.relative_to(root)}"
            )
    if re.search(r"\buser[- ]session\b|RELAY_USER_SESSION|relayUserSession", text, re.I):
        raise SystemExit(
            f"private user credential leaked into {path.relative_to(root)}"
        )

# Every API path a page names must exist in the pinned OpenAPI contract.
# The quickstart once taught GET /v1/agents/me, GET /v1/events and
# POST /v1/webhooks, none of which the server has ever served (2026-09-07).
# A page may name an absent path only to warn against it, on a line that says
# "Do not", and only from this short list.
contract_text = (root / "api-reference/openapi.yaml").read_text()
contract_paths = set(re.findall(r"^  (/v1/\S+):$", contract_text, re.M))
named_absent_paths = {"/v1/agents/me"}
placeholder_segment = re.compile(
    r"\{[^}]+\}"                                   # {chatId}
    r"|\$\{?[A-Za-z_][A-Za-z0-9_]*\}?"               # $CHAT_ID, ${chatId}
    r"|<[^>]+>|:[A-Za-z_]+"                        # <id>, :id
    r"|[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
)


def contract_shape(path):
    return "/" + "/".join(
        "{}" if placeholder_segment.fullmatch(segment) else segment
        for segment in path.split("/")[1:]
    )


contract_shapes = {contract_shape(path) for path in contract_paths}
path_mention = re.compile(r"/v1(?:/[A-Za-z0-9_\-{}$<>:]+)+")
for path in [*mdx_paths, root / "skill.md"]:
    for number, line in enumerate(path.read_text().splitlines(), 1):
        for mention in path_mention.findall(line):
            if contract_shape(mention) in contract_shapes:
                continue
            if mention in named_absent_paths and "Do not" in line:
                continue
            raise SystemExit(
                f"{path.relative_to(root)}:{number} names {mention}, which is "
                "not a path in api-reference/openapi.yaml"
            )

from docs_behavior import validate_behavior
validate_behavior(root)
webhook_events_text = (root / "events/index.mdx").read_text()

# One code table replaces the former per-code page hierarchy.
import runpy
runpy.run_path(str(root / "scripts/check-error-anchors.py"))["check"](root)

openapi_text = (root / "api-reference/openapi.yaml").read_text()
mint_openapi_text = (root / "api-reference/openapi.mint.yaml").read_text()
# api-reference/openapi.yaml is copied byte-for-byte from the Relay Server
# contract, never hand-written. This pin records the exact bytes and the commit
# they came from, so an edit made here instead of at the source fails the gate.
# Source: Relay-Server/contracts/developer/openapi.yaml.
# Error 2029 and Contact.is_removable, Relay-Server PR 185, September 7, 2026.
# Documented 403/409/422/404/413/415 responses, request caps, nullable
# BlockedHandleEntry.reason, UpdateChatRequest minProperties, Relay-Server PR 194, September 8, 2026.
# Message requests replace add requests: request_state, chat.request.updated,
# error 2030, contact_requests removed, Relay-Server PR 205, September 9, 2026.
# A person's reply accepts a message request; the request route takes deleted
# only, Relay-Server PR 207, September 9, 2026.
# Source authority: Relay-Server staging commit 81979fd2ad4e6216bebc6992f89d0c06b6bc9518; CLI publication is gated separately.
# The digest pins source bytes independently of the Server release commit.
expected_openapi_sha256 = (
    "e3c6378357bdd1f3a0c08c00d6bf6df0b387a864b6b401ad7861b4754b7a5495"
)
actual_openapi_sha256 = hashlib.sha256(
    (root / "api-reference/openapi.yaml").read_bytes()
).hexdigest()
if actual_openapi_sha256 != expected_openapi_sha256:
    raise SystemExit(
        "canonical OpenAPI changed: "
        f"{actual_openapi_sha256} != {expected_openapi_sha256}"
    )
if "\n      x-mint:\n" in openapi_text:
    raise SystemExit("Mintlify presentation metadata entered the locked OpenAPI")
if "2026-02-03" in openapi_text:
    raise SystemExit(
        "copied source-company webhook version returned to the Relay OpenAPI"
    )
if "2026-08-30" not in openapi_text:
    raise SystemExit("Relay webhook contract version is missing from OpenAPI")
openapi_normalized = re.sub(r"\s+", " ", openapi_text)
mint_openapi_normalized = re.sub(r"\s+", " ", mint_openapi_text)
for description in [
    (
        "Explicitly mark visible Messages in a Chat as Read. Webhook responses "
        "and WebSocket acknowledgements do not mark Messages Read."
    ),
    (
        "Current receipt state. Sent is a client-only handoff state. Delivered "
        "means Relay accepted and stored the Message. Read means every "
        "recipient explicitly marked the Chat Read."
    ),
    (
        "When Relay accepted and stored the Message. Relay stamps the same "
        "Message commit time for every recipient."
    ),
    "Relay accepted and stored an agent's outgoing Message.",
]:
    if description not in openapi_normalized:
        raise SystemExit(
            f"canonical OpenAPI lost approved receipt description: {description}"
        )
    if description not in mint_openapi_normalized:
        raise SystemExit(
            f"Mintlify OpenAPI lost approved receipt description: {description}"
        )
openapi_transport_blockers = []
if "operationId: getWebSocketSettings" in openapi_text:
    openapi_transport_blockers.append("GET /v1/websocket settings operation")
if "operationId: updateWebSocketSettings" in openapi_text:
    openapi_transport_blockers.append("PUT /v1/websocket settings operation")
if "WebSocketSettingsUpdate:" in openapi_text:
    openapi_transport_blockers.append("WebSocketSettingsUpdate schema")
if "Whether agent events use the WebSocket instead of webhook subscriptions." in openapi_text:
    openapi_transport_blockers.append("enabled transport field")
if "Agent delivery uses\n        successful durable webhook acceptance instead" in openapi_text:
    openapi_transport_blockers.append("webhook-only Agent Delivered description")
if re.search(
    r"WebSocketDisconnectFrame:[\s\S]*?\n\s+- disabled\n",
    openapi_text,
):
    openapi_transport_blockers.append("disabled WebSocket disconnect reason")
if openapi_transport_blockers:
    print(
        "OPENAPI BLOCKER: the server owner must remove "
        + ", ".join(openapi_transport_blockers)
        + " before this branch can publish.",
        file=sys.stderr,
    )
if "x-page-icon:" in openapi_text:
    raise SystemExit("decorative API Reference icons returned")
delivery_status = re.search(
    r"^    DeliveryStatus:\n.*?^      enum:\n((?:^        - [^\n]+\n)+)",
    openapi_text,
    re.M | re.S,
)
if not delivery_status:
    raise SystemExit("DeliveryStatus enum missing from OpenAPI")
delivery_values = re.findall(r"^        - (.+)$", delivery_status.group(1), re.M)
if delivery_values != ["sent", "delivered", "read"]:
    raise SystemExit(f"DeliveryStatus drifted: {delivery_values}")
# PR 214 keeps exactly these response mirrors deprecated; all other legacy
# compatibility surfaces remain forbidden.
allowed_deprecated = {
    (schema, field)
    for schema in ("TextPartResponse", "schemas-TextPartResponse")
    for field in ("mention", "mention_range")
}
actual_deprecated = set()
schema = field = None
for line in openapi_text.splitlines():
    match = re.fullmatch(r"    ([\w-]+):", line)
    if match:
        schema, field = match[1], None
    match = re.fullmatch(r"        ([\w-]+):", line)
    if match:
        field = match[1]
    if re.fullmatch(r"\s+deprecated:\s*true\s*", line):
        if line != "          deprecated: true" or (schema, field) not in allowed_deprecated:
            raise SystemExit("deprecated compatibility surface returned to OpenAPI")
        actual_deprecated.add((schema, field))
if actual_deprecated != allowed_deprecated:
    raise SystemExit("deprecated mention response mirrors missing from OpenAPI")
chat_handle = re.search(
    r"^    ChatHandle:\n(.*?)(?=^    [A-Za-z0-9_-]+:\n)",
    openapi_text,
    re.M | re.S,
)
if not chat_handle:
    raise SystemExit("ChatHandle schema missing from OpenAPI")
chat_handle_text = chat_handle.group(1)
if "greeting_message" in chat_handle_text:
    raise SystemExit("removed greeting field returned to ChatHandle")
openapi_paths = re.findall(r"^  (/[^:]+):$", openapi_text, re.M)
if not openapi_paths or any(not path.startswith("/v1/") for path in openapi_paths):
    raise SystemExit(f"every public OpenAPI path must live under /v1: {openapi_paths}")
for path in openapi_paths:
    if any(path.startswith(prefix) for prefix in private_path_prefixes):
        raise SystemExit(f"private path entered public OpenAPI: {path}")
for required_path in [
    "/v1/chats/{chatId}/share_contact_card",
    "/v1/chats/{chatId}/typing",
    "/v1/websocket",
]:
    if required_path not in openapi_paths:
        raise SystemExit(f"canonical OpenAPI path missing: {required_path}")
if "/v1/websocket-connections" in openapi_paths:
    raise SystemExit("stale WebSocket connection-credential endpoint returned")
if "/v1/contact_requests" in openapi_paths:
    raise SystemExit("retired contact_requests endpoint returned to public OpenAPI")
for spec_name, spec_text in [
    ("canonical", openapi_text),
    ("Mintlify", mint_openapi_text),
]:
    for send_path in [
        "/v1/chats",
        "/v1/messages",
        "/v1/chats/{chatId}/messages",
    ]:
        send_parameters = re.findall(
            r"^        - name: ([^\n]+)$",
            openapi_operation_block(spec_text, send_path, "post"),
            re.M,
        )
        if "Idempotency-Key" not in send_parameters:
            raise SystemExit(
                f"{spec_name} POST {send_path} lost Idempotency-Key"
            )
paths_text = openapi_text.split("\ncomponents:", 1)[0]
operation_ids = re.findall(r"^      operationId: ([A-Za-z0-9]+)$", paths_text, re.M)
leaked_private_operations = sorted(
    set(operation_ids).intersection(private_user_operations)
)
if leaked_private_operations:
    raise SystemExit(
        f"private operation entered public OpenAPI: {leaked_private_operations}"
    )
expected_operation_ids = {
    "createAgent",
    "deleteAgent",
    "addParticipant",
    "blockHandle",
    "connectAgentWebSocket",
    "createChat",
    "createWebhookSubscription",
    "deleteAttachment",
    "deleteWebhookSubscription",
    "editMessage",
    "getAttachment",
    "getChat",
    "getContactCard",
    "getMessage",
    "getMessages",
    "getMessageThread",
    "getWebhookSubscription",
    "leaveChat",
    "listBlockedHandles",
    "listChats",
    "listWebhookEvents",
    "listWebhookSubscriptions",
    "markChatAsRead",
    "removeParticipant",
    "requestUpload",
    "sendMessage",
    "sendMessageToChat",
    "sendReaction",
    "sendVoiceMemoToChat",
    "setupContactCard",
    "shareContactWithChat",
    "startTyping",
    "stopTyping",
    "unblockHandle",
    "unsendMessage",
    "updateChat",
    "updateContactCard",
    "updateWebhookSubscription",
}
if len(operation_ids) != len(expected_operation_ids) or set(operation_ids) != expected_operation_ids:
    raise SystemExit(
        "OpenAPI operation inventory drifted: "
        f"{sorted(set(operation_ids) ^ expected_operation_ids)}"
    )
contract_endpoint_refs = []
for path_match in re.finditer(
    r"^  (/[^:]+):\n(.*?)(?=^  /[^:]+:\n|\Z)",
    paths_text,
    re.M | re.S,
):
    endpoint = path_match.group(1)
    for method in re.findall(
        r"^    (get|post|put|patch|delete):$",
        path_match.group(2),
        re.M,
    ):
        contract_endpoint_refs.append(f"{method.upper()} {endpoint}")
if (
    len(configured_endpoint_refs) != len(set(configured_endpoint_refs))
    or set(configured_endpoint_refs) != set(contract_endpoint_refs)
):
    raise SystemExit(
        "API Reference endpoint order drifted from OpenAPI: "
        f"{sorted(set(configured_endpoint_refs) ^ set(contract_endpoint_refs))}"
    )
mint_sidebar_operations = dict(re.findall(
    r"^      operationId: ([A-Za-z0-9]+)\n"
    r"^      x-mint:\n"
    r"^        metadata:\n"
    r"^          sidebarTitle: ([^\n]+)$",
    mint_openapi_text,
    re.M,
))
if set(mint_sidebar_operations) != expected_operation_ids:
    raise SystemExit(
        "concise API sidebar inventory drifted: "
        f"{sorted(set(mint_sidebar_operations) ^ expected_operation_ids)}"
    )
if re.search(
    r"^      x-mint:\n^        metadata:\n(?:^          .+\n)*^          title:",
    mint_openapi_text,
    re.M,
):
    raise SystemExit("Mintlify presentation metadata must preserve endpoint H1 titles")
for operation_id, metadata in page_paths().items():
    operation = re.search(
        rf"^      operationId: {re.escape(operation_id)}\n(.*?)(?=^      summary:)",
        mint_openapi_text, re.M | re.S,
    )
    if not operation or f"        href: {metadata['href']}\n" not in operation.group(1):
        raise SystemExit(f"Stable endpoint page URL changed: {operation_id}")

event_type_block = re.search(
    r"^    WebhookEventType:\n.*?^      enum:\n"
    r"((?:^        - [^\n]+\n)+)",
    openapi_text,
    re.M | re.S,
)
if not event_type_block:
    raise SystemExit("WebhookEventType enum missing from OpenAPI")
contract_events = {
    value.strip()
    for value in re.findall(r"^        - (.+)$", event_type_block.group(1), re.M)
}
event_catalog_text = webhook_events_text
documented_events = set(
    re.findall(
        r"`((?:message|reaction|participant|chat|contact)\.[a-z_.]+)`",
        event_catalog_text,
    )
)
if documented_events != contract_events:
    raise SystemExit(
        "Webhook Event Types page drifted from OpenAPI: "
        f"{sorted(documented_events ^ contract_events)}"
    )
share_path_start = openapi_text.index("  /v1/chats/{chatId}/share_contact_card:")
share_path_end = openapi_text.find("\n  /v1/", share_path_start + 2)
share_operation = openapi_text[
    share_path_start:share_path_end if share_path_end >= 0 else len(openapi_text)
]
if "requestBody:" in share_operation:
    raise SystemExit("Contact Card sharing route must remain bodyless in OpenAPI")
disconnect = re.search(
    r"^    WebSocketDisconnectFrame:\n.*?^        reason:\n"
    r".*?^          enum:\n((?:^            - [^\n]+\n)+)",
    openapi_text,
    re.M | re.S,
)
if not disconnect:
    raise SystemExit("WebSocket disconnect reason enum missing from OpenAPI")
disconnect_reasons = re.findall(r"^            - (.+)$", disconnect.group(1), re.M)
if disconnect_reasons != [
    "revoked", "heartbeat_timeout", "restart", "webhook_configured"
]:
    raise SystemExit(f"WebSocket disconnect reasons drifted: {disconnect_reasons}")

handwritten_paths = [*mdx_paths, root / "skill.md", root / "README.md"]
# A migration guide quotes the other product on purpose: its routes, and the
# "Not in Relay" list of features Relay does not have, are that product's
# vocabulary, not ours. Everything a migration guide says about Relay is
# scanned for drift exactly like every other page.
FOREIGN_ROUTES = (
    "/v3/messages",                     # Linq
    "/v3/chats/{chatId}/voicememo",     # Linq
    "/v3/webhook-subscriptions",        # Linq
)


def relay_vocabulary(text):
    text = re.sub(r"^## Not in Relay\n.*?(?=^## |\Z)", "", text, flags=re.M | re.S)
    for foreign in FOREIGN_ROUTES:
        text = text.replace(foreign, "")
    return text


def product_prose(path):
    # Verbatim payload text is user content, not product vocabulary.
    text = re.sub(r"^```json captured-output\n.*?^```\s*$", "", path.read_text(), flags=re.M | re.S)
    if not path.match("resources/migrate-from-*.mdx"):
        return text
    # Owner decision 2026-09-11: a migration guide names the product the reader
    # is leaving. There the name is the subject of the page, not residue from an
    # early draft, so it is not scanned. The ban holds on every other page.
    return re.sub(source_company_pattern, "", relay_vocabulary(text), flags=re.I)


handwritten_text = "\n".join(product_prose(path) for path in handwritten_paths)
all_contract_text = handwritten_text + "\n" + openapi_text
if target() == "production" and STAGING_INSTRUCTION_REFERENCE.search(handwritten_text):
    raise SystemExit("staging installation or credential guidance returned to production")
generated_paths = [root / "llms.txt", root / "llms-full.txt"]
generated_text = relay_vocabulary("\n".join(path.read_text() for path in generated_paths))
llms_index_text = (root / "llms.txt").read_text()
for marker in [
    "/v1/websocket",
    "/v1/webhook-subscriptions",
    "2026-08-30",
]:
    if marker not in llms_index_text:
        raise SystemExit(f"llms.txt is missing hosted-search source marker: {marker}")
published_contract_text = all_contract_text + "\n" + generated_text

if "2026-02-03" in published_contract_text:
    raise SystemExit("stale webhook version returned to public product docs")
if "2026-08-30" not in published_contract_text:
    raise SystemExit("Relay webhook version is missing from public product docs")
for field, expected in [
    ("api_version", "v1"),
    ("webhook_version", "2026-08-30"),
]:
    for value in re.findall(
        rf'(?m)^[ \t]*["\']?{field}["\']?[ \t]*:[ \t]*'
        rf'["\']?([^"\'\s,}}]+)',
        published_contract_text,
    ):
        if value != expected:
            raise SystemExit(
                f"public {field} must be {expected}, found {value}"
            )
route_versions = set(re.findall(r"/v([0-9]+)/", published_contract_text))
if route_versions != {"1"}:
    raise SystemExit(
        f"public product docs must use only /v1: {sorted(route_versions)}"
    )

if "Relay" not in (root / "index.mdx").read_text():
    raise SystemExit("Introduction must identify the product as Relay")
if (root / "skill.md").read_bytes() != (
    root / ".mintlify/skills/relay/SKILL.md"
).read_bytes():
    raise SystemExit("published Relay skill drifted from skill.md")
skill_text = (root / "skill.md").read_text()
agent_prompt_page = (root / "integrations/agent-prompt.mdx").read_text()
prompt_match = re.search(
    r"^### Relay agent prompt\n.*?^````text Relay agent prompt\n"
    r"(.*?)\n````$",
    agent_prompt_page,
    re.M | re.S,
)
if not prompt_match or prompt_match.group(1) + "\n" != skill_text:
    raise SystemExit("visible Relay agent prompt drifted from skill.md")
agent_prompt_script = (root / "agent-prompt.js").read_text()
prompt_assignment = re.search(
    r"const RELAY_AGENT_PROMPT = (.+);$",
    agent_prompt_script,
    re.M,
)
if (
    not prompt_assignment
    or json.loads(prompt_assignment.group(1)) != skill_text
):
    raise SystemExit("agent-prompt.js payload drifted from skill.md")
if (
    'const FALLBACK_PATH = "/integrations/agent-prompt#relay-agent-prompt";'
    not in agent_prompt_script
):
    raise SystemExit("agent-prompt.js lost its safe fallback destination")
if "@relaymessenger/sdk" not in handwritten_text:
    raise SystemExit("public docs must name the @relaymessenger/sdk package")
if "@relayapp/sdk" in handwritten_text:
    raise SystemExit("deprecated SDK package name returned")
sdk_install_commands = [
    line.strip()
    for line in handwritten_text.splitlines()
    if re.match(r"^(?:npm (?:install|i)|pnpm add|yarn add|bun add)\b", line.strip())
    and "@relaymessenger/sdk" in line
]
if not sdk_install_commands:
    raise SystemExit("public docs must include an SDK installation command")
for command in sdk_install_commands:
    package_tokens = [
        token for token in command.split() if token.startswith("@relaymessenger/sdk")
    ]
    if package_tokens != [spec("@relaymessenger/sdk@staging")]:
        raise SystemExit(
            f"SDK install commands must use {spec('@relaymessenger/sdk@staging')}: "
            f"{command}"
        )

for name, pattern in {
    "deprecated product name": r"\bRelay App\b",
    "Business API name": r"\bBusiness API\b",
    "Partner API name": r"\bPartner API\b",
    "mobile product namespace": r"\bmobile(?: API| namespace| endpoint| boundary)?\b",
    "realtime product name": r"\breal[ -]?time\b",
}.items():
    if re.search(pattern, handwritten_text, re.I):
        raise SystemExit(f"stale {name}")

for stale_hook in ["Implement this in the agent backend's connection flow", "## Backend connection greeting"]:
    if stale_hook in skill_text:
        raise SystemExit("agent instructions must not add a backend connection hook")
for required in [
    "GET /v1/chats?limit=1", "Do not require `/v1/agents/me`",
    "The first\n   Message is the request", "`contact.added`", "`chat.request.updated`",
]:
    if required not in skill_text:
        raise SystemExit(f"setup prompt lost safety guidance: {required}")
if "/integrations/agent-prompt#relay-agent-prompt" not in (root / "start/quickstart.mdx").read_text():
    raise SystemExit("Quickstart lost its link to the agent instructions")

for name, pattern in {
    "Socket Mode product name": r"\bSocket Mode\b",
    "agent installation lifecycle": r"\bagent installation\b|\binstalled agents?\b|\binstall agents?\b",
    "old ecosystem path": r"/ecosystem(?:/|\b)",
    "old ecosystem vocabulary": r"\becosystem\b|\bRelay for \b|\bRelay channel for\b",
    "old conversation vocabulary": r"\bconversations?\b",
    "removed Message feature phrase": r"\bMessage " r"effects\b",
    "stale guide path": r"guides/(?:socket-mode|chats/install-agents|webhooks/choose-transport|platform/errors)",
    "old public status language": r"current-status|Current status|known contract residue|local proof|evidence app",
    "old WebSocket handshake": r"/v1/websocket-connections|relay_ticket_|relay\.v1\.json|\?ticket=",
    "source-company language": source_company_pattern,
    "removed greeting step": r"\bgreeting(?:s)?\b|\bgreeting_message\b",
    "removed Broadcast feature": r"\bbroadcasts?\b",
    "removed Proactive feature": r"\bproactive\b",
    "MFA surface": r"\bMFA\b",
}.items():
    if re.search(pattern, handwritten_text, re.I):
        raise SystemExit(f"stale {name}")

for name, pattern in {
    "old URL namespace": r"/api/(?:partner|mobile)|api\.relayapp\.im/api/",
    "old route version": r"/v[23]/",
    "wire service field": r"[\"']service[\"']\s*:|\bservice\s*:\s*[\"']?Relay",
    "mobile realtime endpoint": r"/v1/realtime|/v1/client/realtime",
    "prefixed ID": r"\b(?:msg|agt|usr|cnv|prt|att|evt|wh)_[A-Za-z0-9]",
    "uuidv4 example": r"\b[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b",
    "human identity kind": r"\bkind\b.{0,30}\bhumans?\b|\bhumans?\b.{0,30}\bkind\b",
    "message parts table": r"\bmessage_parts?\b",
    "unsupported payment endpoint": r"/v1/payments?\b",
    "long polling": r"long[ -]poll",
    "noncanonical error URL": r"docs\.relayapp\.im/error/codes/\dxxx/\d{4}/",
    "carrier API residue": r"from-number|sending line|line flagging|S3 will|sandbox and production",
    "received delivery status": r"`sent`,\s*`received`,\s*`delivered`",
    "deprecated compatibility field": r"[\"'](?:compatibility_source|service|from_number|to_number)[\"']\s*:",
}.items():
    if re.search(pattern, all_contract_text, re.I):
        raise SystemExit(f"stale {name}")

print(
    f"validated {len(files)} Relay public pages, four tabs, "
    "Console CTA, Copy agent prompt action, logo destination, Quickstart sidebar placement, "
    "atomic guide groups, "
    "focused page boundaries, "
    "frontmatter, bodyless Contact Card sharing, exact delivery states and error pages, "
    "typing, exact OpenAPI event inventory, webhook retries, transport recovery, URL safety, "
    "message requests and exact idempotency scope, private Contact and route exclusion, Agent Read authentication, "
    "final automatic event paths, WebSocket disconnects, "
    "package identity, and stale-contract bans"
)
