#!/usr/bin/env python3
import json
import hashlib
import re
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
config = json.loads((root / "docs.json").read_text())
if config.get("name") != "Relay":
    raise SystemExit("site identity must be Relay")
if config.get("description") != "Relay API v1 documentation.":
    raise SystemExit("site description must use the Relay identity")
if config.get("favicon") != "/favicon-staging.png":
    raise SystemExit("staging Docs must use the black Relay favicon")
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
    "href": "https://console.relayapp.im",
}:
    raise SystemExit("top-right docs action must open Relay Console")
if config.get("navbar", {}).get("links") != [
    {
        "label": "Copy agent prompt",
        "href": "/getting-started/ai-agents#relay-agent-prompt",
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
expected_tabs = ["Guides", "Error Codes", "API Reference"]
if actual_tabs != expected_tabs:
    raise SystemExit(f"top tab order changed: {actual_tabs}")

expected_guide_groups = [
    "Introduction",
    "Getting started",
    "Messaging",
    "Chats",
    "Contacts",
    "Agent events",
    "Webhooks",
    "WebSocket",
    "Platform",
    "Examples",
]
actual_guide_groups = [group["group"] for group in tabs[0]["groups"]]
if actual_guide_groups != expected_guide_groups:
    raise SystemExit(f"guide group order changed: {actual_guide_groups}")

expected_guide_pages = {
    "Introduction": ["index"],
    "Getting started": [
        "getting-started/quickstart",
        "getting-started/authentication",
        "getting-started/sdks",
        "getting-started/key-concepts",
        "getting-started/ai-agents",
        "getting-started/best-practices",
    ],
    "Messaging": [
        "guides/messaging/index",
        "guides/messaging/sending-messages",
        "guides/messaging/mentions",
        "guides/messaging/message-details",
        "guides/messaging/message-parts",
        "guides/messaging/attachments",
        "guides/messaging/voice-memos",
        "guides/messaging/rich-link-previews",
        "guides/messaging/replies",
        "guides/messaging/reactions",
        "guides/messaging/delivery-receipts",
    ],
    "Chats": [
        "guides/chats/index",
        "guides/chats/group-chats",
        "guides/chats/participants",
        "guides/chats/typing-indicators",
        "guides/chats/share-contact-card",
        "guides/chats/message-history",
    ],
    "Contacts": [
        "guides/contacts/add-requests",
        "guides/contact-cards",
        "guides/chats/blocked-handles",
    ],
    "Agent events": [
        "guides/agent-events/index",
        "guides/agent-events/events",
    ],
    "Webhooks": [
        "guides/webhooks/index",
        "guides/webhooks/subscriptions",
        "guides/webhooks/delivery",
    ],
    "WebSocket": [
        "guides/websocket/index",
        "guides/websocket/protocol",
        "guides/websocket/acknowledgements",
        "guides/websocket/full-sync",
    ],
    "Platform": [
        "guides/platform/idempotency",
        "guides/platform/rate-limits",
        "guides/platform/debugging",
    ],
    "Examples": ["examples/index"],
}
for group in tabs[0]["groups"]:
    expected = expected_guide_pages[group["group"]]
    if group["pages"] != expected:
        raise SystemExit(
            f"{group['group']} page order changed: {group['pages']}"
        )

expected_error_groups = [
    "Overview",
    "1xxx request errors",
    "2xxx errors",
    "3xxx server errors",
]
actual_error_groups = [group["group"] for group in tabs[1]["groups"]]
if actual_error_groups != expected_error_groups:
    raise SystemExit(f"error group order changed: {actual_error_groups}")

api_tab = tabs[2]
if api_tab.get("openapi") != "api-reference/openapi.mint.yaml":
    raise SystemExit("generated API groups must sit directly under API Reference")
expected_api_groups = [
    {
        "group": "API Reference",
        "pages": ["api-reference/overview"],
    },
    {
        "group": "Chats",
        "pages": [
            "POST /v1/chats",
            "GET /v1/chats",
            "GET /v1/chats/{chatId}",
            "PUT /v1/chats/{chatId}",
            "POST /v1/chats/{chatId}/participants",
            "DELETE /v1/chats/{chatId}/participants",
            "POST /v1/chats/{chatId}/leave",
            "POST /v1/chats/{chatId}/typing",
            "DELETE /v1/chats/{chatId}/typing",
            "POST /v1/chats/{chatId}/read",
            "POST /v1/chats/{chatId}/share_contact_card",
        ],
    },
    {
        "group": "Messages",
        "pages": [
            "POST /v1/messages",
            "POST /v1/chats/{chatId}/messages",
            "GET /v1/chats/{chatId}/messages",
            "GET /v1/messages/{messageId}/thread",
            "POST /v1/chats/{chatId}/voicememo",
            "GET /v1/messages/{messageId}",
            "POST /v1/messages/{messageId}/reactions",
        ],
    },
    {
        "group": "Attachments",
        "pages": [
            "POST /v1/attachments",
            "GET /v1/attachments/{attachmentId}",
            "DELETE /v1/attachments/{attachmentId}",
        ],
    },
    {
        "group": "Blocked Handles",
        "pages": [
            "GET /v1/blocked_handles",
            "POST /v1/blocked_handles",
            "DELETE /v1/blocked_handles",
        ],
    },
    {
        "group": "Webhooks",
        "pages": [
            "GET /v1/webhook-events",
            "POST /v1/webhook-subscriptions",
            "GET /v1/webhook-subscriptions",
            "GET /v1/webhook-subscriptions/{subscriptionId}",
            "PUT /v1/webhook-subscriptions/{subscriptionId}",
            "DELETE /v1/webhook-subscriptions/{subscriptionId}",
        ],
    },
    {
        "group": "Contact Card",
        "pages": [
            "GET /v1/contact_card",
            "POST /v1/contact_card",
            "PATCH /v1/contact_card",
        ],
    },
    {
        "group": "WebSocket",
        "pages": ["GET /v1/websocket"],
    },
    {
        "group": "Contacts",
        "pages": ["POST /v1/contact_requests"],
    },
]
if api_tab.get("groups") != expected_api_groups:
    raise SystemExit(f"API Reference operation order changed: {api_tab.get('groups')}")
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
if "getting-started/quickstart" not in navigated:
    raise SystemExit("Quickstart must remain a sidebar guide")
if (root / "current-status.mdx").exists():
    raise SystemExit("Current status belongs in the evidence site, not public docs")

required_paths = [
    root / "guides/contact-cards.mdx",
    root / "guides/chats/share-contact-card.mdx",
    root / "guides/chats/typing-indicators.mdx",
    root / "guides/messaging/delivery-receipts.mdx",
    root / "guides/contacts/add-requests.mdx",
    root / "guides/agent-events/events.mdx",
    root / "guides/websocket/index.mdx",
    root / "guides/websocket/protocol.mdx",
    root / "guides/websocket/full-sync.mdx",
    root / "error/index.mdx",
]
for path in required_paths:
    if not path.exists():
        raise SystemExit(f"required atomic guide missing: {path.relative_to(root)}")
for path in [
    root / "guides/messaging/index.mdx",
    root / "guides/chats/index.mdx",
    root / "guides/webhooks/index.mdx",
    root / "guides/websocket/index.mdx",
    root / "api-reference/overview.mdx",
]:
    if 'sidebarTitle: "Overview"' not in path.read_text():
        raise SystemExit(f"overview sidebar label drifted: {path.relative_to(root)}")
for relative, label in {
    "error/index.mdx": "All errors",
    "guides/agent-events/events.mdx": "Event types",
    "guides/webhooks/subscriptions.mdx": "Subscriptions",
    "guides/webhooks/delivery.mdx": "Delivery",
    "guides/websocket/protocol.mdx": "Frames",
    "guides/websocket/acknowledgements.mdx": "Acknowledgements",
    "guides/websocket/full-sync.mdx": "FULL sync",
}.items():
    path = root / relative
    if f'sidebarTitle: "{label}"' not in path.read_text():
        raise SystemExit(f"concise sidebar label drifted: {relative}")
for stale in [
    root / "guides/chats/install-agents.mdx",
    root / "guides/socket-mode.mdx",
    root / "guides/socket-mode-protocol.mdx",
    root / "guides/webhooks/choose-transport.mdx",
    root / "guides/platform/errors.mdx",
    root / "guides/contacts/default-agents.mdx",
    root / "guides/contacts/agent-greetings.mdx",
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
    headings = h2_headings(text)
    if not headings or headings[-1] not in {"Next steps", "Related", "See also"}:
        raise SystemExit(f"page must end with Next steps, Related, or See also: {path}")

    for block in re.findall(
        r"<(?:CodeGroup|Tabs)>[\s\S]*?</(?:CodeGroup|Tabs)>",
        text,
    ):
        if "TypeScript SDK" in block and "cURL" in block:
            if block.index("TypeScript SDK") > block.index("cURL"):
                raise SystemExit(
                    f"TypeScript SDK must appear before cURL: {path.relative_to(root)}"
                )

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

architecture_text = (root / "INFORMATION-ARCHITECTURE.md").read_text()
heading_inventory = architecture_text.split(
    "## 16. Exact heading skeletons", 1
)[1].split("## 17. Current page map", 1)[0]
documented_heading_rows = {
    page.strip().lower(): re.findall(r"`([^`]+)`", order)
    for page, order in re.findall(r"^\| ([^|]+) \| (.+) \|$", heading_inventory, re.M)
    if "`" in order
}
heading_aliases = {
    "participants and membership": "participants",
    "websocket acknowledgements": "acknowledgements",
    "websocket full sync": "full sync",
    "websocket frames": "websocket frames",
    "limits": "rate limits",
    "error codes": "error codes",
    "api reference": "api reference overview",
}
for path in mdx_paths:
    text = path.read_text()
    frontmatter = text.split("---", 2)[1]
    title_match = re.search(r'^title:\s*"([^"]+)"', frontmatter, re.M)
    if not title_match:
        raise SystemExit(f"quoted title missing from frontmatter: {path}")
    title = title_match.group(1).lower()
    if "error/codes/" in str(path.relative_to(root)):
        inventory_key = "one error code"
    else:
        inventory_key = heading_aliases.get(title, title)
    expected_headings = documented_heading_rows.get(inventory_key)
    if expected_headings is None:
        raise SystemExit(
            f"heading inventory missing for {path.relative_to(root)}: {inventory_key}"
        )
    actual_headings = h2_headings(text)
    if actual_headings != expected_headings:
        raise SystemExit(
            f"heading inventory drifted for {path.relative_to(root)}: "
            f"{actual_headings} != {expected_headings}"
        )

side_by_side_guides = [
    "getting-started/quickstart.mdx",
    "guides/chats/index.mdx",
    "guides/messaging/sending-messages.mdx",
    "guides/messaging/mentions.mdx",
    "guides/messaging/message-details.mdx",
    "guides/messaging/attachments.mdx",
    "guides/messaging/voice-memos.mdx",
    "guides/messaging/rich-link-previews.mdx",
    "guides/messaging/replies.mdx",
    "guides/messaging/reactions.mdx",
    "guides/messaging/delivery-receipts.mdx",
    "guides/chats/group-chats.mdx",
    "guides/chats/participants.mdx",
    "guides/chats/typing-indicators.mdx",
    "guides/chats/share-contact-card.mdx",
    "guides/chats/message-history.mdx",
    "guides/chats/blocked-handles.mdx",
    "guides/contact-cards.mdx",
    "guides/contacts/add-requests.mdx",
    "guides/webhooks/index.mdx",
    "guides/webhooks/subscriptions.mdx",
    "guides/agent-events/events.mdx",
    "guides/websocket/index.mdx",
]
for relative in side_by_side_guides:
    text = (root / relative).read_text()
    if "TypeScript SDK" not in text or "cURL" not in text:
        raise SystemExit(f"SDK/cURL task variants missing: {relative}")

share_text = (root / "guides/chats/share-contact-card.mdx").read_text()
if "POST /v1/chats/{chatId}/share_contact_card" not in share_text:
    raise SystemExit("Contact Card sharing guide lost the canonical route")
if not re.search(r"\bexisting Chat\b", share_text):
    raise SystemExit("Contact Card sharing guide must require an existing Chat")
if not re.search(
    r"\b(?:send an empty request|empty request body)\b",
    share_text,
    re.I,
):
    raise SystemExit("Contact Card sharing guide must state that the route is bodyless")

contact_text = (root / "guides/contact-cards.mdx").read_text()
if not re.search(r"\bPOST https://api\.relayapp\.im/v1/contact_card\b", contact_text):
    raise SystemExit("Contact Card configuration guide lost POST /v1/contact_card")
if not re.search(
    r"\bPATCH\b[\s\S]{0,100}api\.relayapp\.im/v1/contact_card\?handle=",
    contact_text,
):
    raise SystemExit("Contact Card configuration guide lost its PATCH operation")

add_requests_text = (root / "guides/contacts/add-requests.mdx").read_text()
for required in [
    "Username-scoped Handle",
    "Premium Handle",
    "relay.contactRequests.create",
    "POST https://api.relayapp.im/v1/contact_requests",
    '"state": "pending"',
    "`402`",
    "`contact.added`",
    "`contact.removed`",
    '"chat_id":',
]:
    if required not in add_requests_text:
        raise SystemExit(f"Add requests guide is missing: {required}")
if "greeting" in add_requests_text.lower():
    raise SystemExit("Add requests guide invented greeting behavior")

receipt_text = (root / "guides/messaging/delivery-receipts.mdx").read_text()
if "/v1/chats/$CHAT_ID/read" not in receipt_text:
    raise SystemExit("Delivery receipt guide lost the Agent Read route")
if "Authorization: Bearer $RELAY_AGENT_TOKEN" not in receipt_text:
    raise SystemExit("Delivery receipt guide must authenticate Read with an Agent Token")
for required in [
    "`deliveries`",
    "direct and group Chats",
    "per-recipient",
]:
    if required not in receipt_text:
        raise SystemExit(f"Delivery receipt rationale is missing: {required}")

attachments_text = (root / "guides/messaging/attachments.mdx").read_text()
if "Public URL media parts per Message" not in attachments_text:
    raise SystemExit("Attachment guide must scope the 40-part limit to URL media")
if not all(term in attachments_text for term in [
    "Every DNS answer",
    "Every hop is revalidated",
    "at most five redirects",
]):
    raise SystemExit("Attachment guide lost URL import safety boundaries")
if (
    "WebP" not in attachments_text
    or not re.search(r"\brejects\s+SVG\b", attachments_text)
):
    raise SystemExit("Attachment guide lost the Relay WebP/SVG decision")
for required in [
    "relay.attachments.retrieve",
    'attachment.status !== "complete"',
    '"Range: bytes=0-1048575"',
    "relay.attachments.delete",
]:
    if required not in attachments_text:
        raise SystemExit(f"Attachment lifecycle guide is missing: {required}")

webhook_text = (root / "guides/webhooks/index.mdx").read_text()
webhook_events_text = (root / "guides/agent-events/events.mdx").read_text()
webhook_delivery_text = (root / "guides/webhooks/delivery.mdx").read_text()
webhook_delivery_normalized = re.sub(r"\s+", " ", webhook_delivery_text)
websocket_text = (root / "guides/websocket/index.mdx").read_text()
websocket_protocol_text = (root / "guides/websocket/protocol.mdx").read_text()
websocket_recovery_text = (root / "guides/websocket/full-sync.mdx").read_text()
typing_text = (root / "guides/chats/typing-indicators.mdx").read_text()
typing_normalized = re.sub(r"\s+", " ", typing_text)
agent_event_text = (root / "guides/agent-events/index.mdx").read_text()
transport_text = "\n".join([
    agent_event_text,
    webhook_text,
    websocket_text,
    websocket_protocol_text,
    webhook_delivery_text,
])
for required in [
    "one or more saved subscriptions",
    "subscription list must be empty",
    "HTTP `409`",
    "closes connected agent sockets",
    "same `event_id`",
    "wait durably",
    "30 days",
]:
    if required.lower() not in transport_text.lower():
        raise SystemExit(f"final event path decision is missing: {required}")
for forbidden in [
    "relay.websocket.update",
    "PUT https://api.relayapp.im/v1/websocket",
    '{"enabled":true}',
    '{"enabled":false}',
    "WebSocket is enabled",
]:
    if forbidden.lower() in transport_text.lower():
        raise SystemExit(f"stale WebSocket setting returned: {forbidden}")
if (
    '"webhook_version": "2026-08-30"' not in webhook_events_text
    or "use this fixed payload version" not in webhook_events_text
):
    raise SystemExit("webhook event guide lost the fixed payload version")
for required in [
    "MessageEvent",
    "ReactionEventBase",
    "ParticipantAddedEvent",
    "ParticipantRemovedEvent",
    "ChatCreatedEvent",
    "ChatGroupNameUpdatedEvent",
    "ChatGroupIconUpdatedEvent",
    "ChatTypingIndicatorStartedEvent",
    "ChatTypingIndicatorStoppedEvent",
    "ContactAddedEvent",
    "ContactRemovedEvent",
]:
    if f"`{required}`" not in webhook_events_text:
        raise SystemExit(f"event payload schema missing from catalog: {required}")
if '"data": {}' in webhook_events_text:
    raise SystemExit("event catalog returned an empty event-specific payload")
if (
    "`4410`" not in websocket_protocol_text
    or "`webhook_configured`" not in websocket_protocol_text
):
    raise SystemExit("WebSocket protocol is missing the webhook-configured close")
for reason in ["revoked", "heartbeat_timeout", "restart", "webhook_configured"]:
    if f"`{reason}`" not in websocket_protocol_text:
        raise SystemExit(f"WebSocket protocol is missing disconnect reason: {reason}")
if "`stale_connection`" not in websocket_protocol_text:
    raise SystemExit("WebSocket protocol is missing stale-connection error handling")
if "A fatal error ends consumption" not in websocket_protocol_text:
    raise SystemExit("WebSocket protocol lost fatal error handling")
for required in [
    "wss://api.relayapp.im/v1/websocket",
    "Authorization: Bearer $RELAY_AGENT_TOKEN",
    "Agent Token",
    "multiple connected sockets",
    "HTTP `409`",
    "relay.websocket.run",
]:
    if required not in websocket_text:
        raise SystemExit(f"WebSocket authentication guide is missing: {required}")
if (
    not re.search(r"\bping(?: frame)? every 30 seconds\b", websocket_protocol_text)
    or "within 60 seconds" not in websocket_protocol_text
):
    raise SystemExit("WebSocket guide lost the 30-second ping and 60-second pong timeout")
for forbidden in [
    "/v1/websocket-connections",
    "relay_ticket_",
    "relay.v1.json",
]:
    if forbidden in websocket_text + "\n" + websocket_protocol_text:
        raise SystemExit(f"stale WebSocket handshake returned: {forbidden}")
for required in [
    "full_sync",
    "full_sync_complete",
    "checkpoint_outside_retention",
    "same `event_id`",
    "pending agent events for 30 days",
]:
    if required not in websocket_recovery_text:
        raise SystemExit(f"WebSocket recovery guide is missing: {required}")
for required in [
    "1 immediate attempt",
    "Up to 10",
    "10 seconds per attempt",
    "`429`",
    "`5xx`",
    "Relay stops after a terminal response",
    "Recover current Chat and Message state",
    "HTTP `3xx`",
    "redirect is not followed",
    "localhost",
    "private",
    "link-local",
    "cloud metadata",
    "same `event_id`",
]:
    if required not in webhook_delivery_normalized:
        raise SystemExit(f"Webhook delivery policy is missing: {required}")
for required in [
    "chat.typing_indicator.started",
    "chat.typing_indicator.stopped",
    "every 60 seconds",
    "85 to 90 seconds",
    '"contact": {',
    "expires automatically",
]:
    if required not in typing_normalized:
        raise SystemExit(f"Typing guide is missing: {required}")

group_text = (root / "guides/chats/group-chats.mdx").read_text()
if (
    "2 to 31 recipient Handles plus the sender" not in group_text
    or "keep at least three active Contacts" not in group_text
):
    raise SystemExit("Group Chat guide lost max-32 and minimum-three rules")

expected_error_codes = {
    1004, 1005, 2001, 2003, 2004, 2005, 2006,
    2007, 2008, 2015, 2023, 2025, 2026, 3006,
}
error_paths = sorted((root / "error/codes").rglob("*.mdx"))
actual_error_codes = {int(path.stem) for path in error_paths}
if actual_error_codes != expected_error_codes:
    raise SystemExit(
        f"error code pages drifted: {sorted(actual_error_codes ^ expected_error_codes)}"
    )
expected_error_statuses = {
    1004: "`400`",
    1005: "`400`",
    2001: "`404`",
    2003: "`403`",
    2004: "`401`",
    2005: "`500`",
    2006: "`413`, `415`, or `422`",
    2007: "`404`",
    2008: "`429`",
    2015: "`409`",
    2023: "`409`",
    2025: "`404`",
    2026: "`403`",
    3006: "`500`",
}
error_overview_text = (root / "error/index.mdx").read_text()
for path in error_paths:
    error_text = path.read_text()
    code = int(path.stem)
    sidebar_match = re.search(r'^sidebarTitle: "([^"]+)"$', error_text, re.M)
    if (
        not sidebar_match
        or not sidebar_match.group(1).startswith(path.stem)
        or sidebar_match.group(1).startswith(f"Error {path.stem}")
        or len(sidebar_match.group(1)) > 28
    ):
        raise SystemExit(
            f"error sidebar title is not concise: {path.relative_to(root)}"
        )
    if f'| {expected_error_statuses[code]} | `{code}` |' not in error_text:
        raise SystemExit(f"error status/code row drifted in {path.relative_to(root)}")
    if "## Troubleshooting" not in error_text or "**Retry:**" not in error_text:
        raise SystemExit(f"error recovery guidance missing in {path.relative_to(root)}")
    if "```json" in error_text:
        raise SystemExit(f"shared error envelope duplicated in {path.relative_to(root)}")
    if f'description: "Resolve Relay error {code}."' in error_text:
        raise SystemExit(f"generic error description returned in {path.relative_to(root)}")
    expected_link = f"/error/codes/{code // 1000}xxx/{code}"
    if expected_link not in error_overview_text:
        raise SystemExit(f"error overview link missing: {expected_link}")

openapi_text = (root / "api-reference/openapi.yaml").read_text()
mint_openapi_text = (root / "api-reference/openapi.mint.yaml").read_text()
if "\n      x-mint:\n" in openapi_text:
    raise SystemExit("Mintlify presentation metadata entered the locked OpenAPI")
if "2026-02-03" in openapi_text:
    raise SystemExit("copied Linq webhook version returned to the Relay OpenAPI")
if "2026-08-30" not in openapi_text:
    raise SystemExit("Relay webhook contract version is missing from OpenAPI")
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
if re.search(r"^\s+deprecated:\s*true\s*$", openapi_text, re.M):
    raise SystemExit("deprecated compatibility surface returned to OpenAPI")
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
    "/v1/contact_requests",
    "/v1/websocket",
]:
    if required_path not in openapi_paths:
        raise SystemExit(f"canonical OpenAPI path missing: {required_path}")
if "/v1/websocket-connections" in openapi_paths:
    raise SystemExit("stale WebSocket connection-credential endpoint returned")
contact_request_start = openapi_text.index("  /v1/contact_requests:")
contact_request_end = openapi_text.find(
    "\n  /v1/",
    contact_request_start + 2,
)
contact_request_operation = openapi_text[
    contact_request_start:
    contact_request_end if contact_request_end >= 0 else openapi_text.index(
        "\ncomponents:",
        contact_request_start,
    )
]
contact_request_methods = re.findall(
    r"^    (get|post|put|patch|delete):$",
    contact_request_operation,
    re.M,
)
if contact_request_methods != ["post"]:
    raise SystemExit(
        "public contact_requests must expose only the agent POST: "
        f"{contact_request_methods}"
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
    "addParticipant",
    "blockHandle",
    "connectAgentWebSocket",
    "createContactRequest",
    "createChat",
    "createWebhookSubscription",
    "deleteAttachment",
    "deleteWebhookSubscription",
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
configured_endpoint_refs = [
    page
    for group in expected_api_groups[1:]
    for page in group["pages"]
]
if (
    len(configured_endpoint_refs) != len(set(configured_endpoint_refs))
    or set(configured_endpoint_refs) != set(contract_endpoint_refs)
):
    raise SystemExit(
        "API Reference endpoint order drifted from OpenAPI: "
        f"{sorted(set(configured_endpoint_refs) ^ set(contract_endpoint_refs))}"
    )
api_overview_text = (root / "api-reference/overview.mdx").read_text()
for endpoint_ref in configured_endpoint_refs:
    method, endpoint = endpoint_ref.split(" ", 1)
    if f"| `{method}` | `{endpoint}` |" not in api_overview_text:
        raise SystemExit(f"API overview endpoint missing: {endpoint_ref}")
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
event_catalog_text = webhook_events_text.split(
    "## All event types", 1
)[1].split("## Envelope", 1)[0]
documented_events = set(
    re.findall(
        r"`((?:message|reaction|participant|chat|contact)\.[a-z_.]+)`",
        event_catalog_text,
    )
)
if documented_events != contract_events:
    raise SystemExit(
        "Agent event types page drifted from OpenAPI: "
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
handwritten_text = "\n".join(path.read_text() for path in handwritten_paths)
all_contract_text = handwritten_text + "\n" + openapi_text

if "Relay" not in (root / "index.mdx").read_text():
    raise SystemExit("Introduction must identify the product as Relay")
if (root / "skill.md").read_bytes() != (
    root / ".mintlify/skills/relay/SKILL.md"
).read_bytes():
    raise SystemExit("published Relay skill drifted from skill.md")
skill_text = (root / "skill.md").read_text()
agent_prompt_page = (root / "getting-started/ai-agents.mdx").read_text()
prompt_match = re.search(
    r"^## Relay agent prompt\n.*?^````text Relay agent prompt\n"
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
    'const FALLBACK_PATH = "/getting-started/ai-agents#relay-agent-prompt";'
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
    if package_tokens != ["@relaymessenger/sdk@staging"]:
        raise SystemExit(
            "staging SDK install commands must use @relaymessenger/sdk@staging: "
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

for name, pattern in {
    "Socket Mode product name": r"\bSocket Mode\b",
    "agent installation lifecycle": r"\bagent installation\b|\binstalled agents?\b|\binstall agents?\b",
    "agent share-link lifecycle": r"\bshare[- ]link\b",
    "stale guide path": r"guides/(?:socket-mode|chats/install-agents|webhooks/choose-transport|platform/errors)",
    "old public status language": r"current-status|Current status|known contract residue|local proof|evidence app",
    "old WebSocket handshake": r"/v1/websocket-connections|relay_ticket_|relay\.v1\.json|\?ticket=",
    "source-company language": r"\bLinq\b",
    "removed greeting behavior": r"\bgreeting(?:_message|s)?\b",
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
    "unsupported payments": r"\bpayments?\b",
    "unsupported edits": r"\b(?:edited|editing|edits?)\b",
    "unsupported unsend": r"\bunsend\b",
    "long polling": r"long[ -]poll",
    "noncanonical error URL": r"docs\.relayapp\.im/error/codes/\dxxx/\d{4}/",
    "carrier API residue": r"from-number|sending line|line flagging|S3 will|sandbox and production",
    "received delivery status": r"`sent`,\s*`received`,\s*`delivered`",
    "deprecated compatibility field": r"[\"'](?:compatibility_source|service|from_number|to_number)[\"']\s*:",
}.items():
    if re.search(pattern, all_contract_text, re.I):
        raise SystemExit(f"stale {name}")

print(
    f"validated {len(files)} Relay public pages, three tabs, "
    "Console CTA, Copy agent prompt action, logo destination, Quickstart sidebar placement, "
    "atomic guide groups, "
    "exact heading inventory, "
    "frontmatter, bodyless Contact Card sharing, exact delivery states and error pages, "
    "typing, exact OpenAPI event inventory, webhook retries, transport recovery, URL safety, "
    "Add requests, private Contact and route exclusion, Agent Read authentication, "
    "final automatic event paths, WebSocket disconnects, "
    "package identity, and stale-contract bans"
)
