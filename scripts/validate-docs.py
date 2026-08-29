#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
config = json.loads((root / "docs.json").read_text())


def pages(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "pages" and isinstance(item, list):
                yield from (page for page in item if isinstance(page, str))
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
        "guides/contact-cards",
        "guides/chats/blocked-handles",
    ],
    "Agent events": ["guides/agent-events/index"],
    "Webhooks": [
        "guides/webhooks/index",
        "guides/webhooks/subscriptions",
        "guides/webhooks/events",
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
    "2xxx resource errors",
    "3xxx server errors",
]
actual_error_groups = [group["group"] for group in tabs[1]["groups"]]
if actual_error_groups != expected_error_groups:
    raise SystemExit(f"error group order changed: {actual_error_groups}")

if has_key(config.get("navigation", {}), "icon") or has_key(config.get("navigation", {}), "icons"):
    raise SystemExit("decorative navigation icons returned")
if config.get("contextual") != {"options": ["copy", "view"], "display": "header"}:
    raise SystemExit("header Copy page/Markdown actions changed")
if (root / "current-status.mdx").exists():
    raise SystemExit("Current status belongs in the evidence site, not public docs")

required_paths = [
    root / "guides/contact-cards.mdx",
    root / "guides/chats/share-contact-card.mdx",
    root / "guides/chats/typing-indicators.mdx",
    root / "guides/messaging/delivery-receipts.mdx",
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
for stale in [
    root / "guides/chats/install-agents.mdx",
    root / "guides/socket-mode.mdx",
    root / "guides/socket-mode-protocol.mdx",
    root / "guides/webhooks/choose-transport.mdx",
    root / "guides/platform/errors.mdx",
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
    headings = re.findall(r"^## (.+)$", text, re.M)
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

side_by_side_guides = [
    "getting-started/quickstart.mdx",
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
    "guides/webhooks/index.mdx",
    "guides/webhooks/subscriptions.mdx",
    "guides/webhooks/events.mdx",
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
    r"\b(?:no (?:request )?body|without a (?:request )?body|do not send a request body)\b",
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

receipt_text = (root / "guides/messaging/delivery-receipts.mdx").read_text()
if "/v1/messages/$MESSAGE_ID/delivered" not in receipt_text:
    raise SystemExit("Delivery receipt guide lost the user acknowledgement route")
if not re.search(r"\bcumulative\b", receipt_text, re.I):
    raise SystemExit("Delivery receipt guide must explain cumulative user delivery")
if "Agent Tokens cannot call it" not in receipt_text:
    raise SystemExit("Delivery receipt guide must preserve the user-only boundary")
for required in [
    "`deliveries`",
    "direct and group Chats",
    "owner-approved Relay capability",
    "best-effort group Read signals",
    "complete per-recipient truth",
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
if "WebP" not in attachments_text or "rejects SVG" not in attachments_text:
    raise SystemExit("Attachment guide lost the Relay WebP/SVG decision")

webhook_text = (root / "guides/webhooks/index.mdx").read_text()
webhook_events_text = (root / "guides/webhooks/events.mdx").read_text()
webhook_delivery_text = (root / "guides/webhooks/delivery.mdx").read_text()
websocket_text = (root / "guides/websocket/index.mdx").read_text()
websocket_protocol_text = (root / "guides/websocket/protocol.mdx").read_text()
websocket_recovery_text = (root / "guides/websocket/full-sync.mdx").read_text()
typing_text = (root / "guides/chats/typing-indicators.mdx").read_text()
if "Webhooks are the default" not in webhook_text + "\n" + websocket_text:
    raise SystemExit("event transport docs must identify the default")
if "same event through both" not in webhook_text + "\n" + websocket_text:
    raise SystemExit("event transport docs must prevent dual delivery assumptions")
if (
    'webhook_version":"2026-02-03"' not in webhook_events_text
    or "use this fixed payload version" not in webhook_events_text
):
    raise SystemExit("webhook event guide lost the fixed payload version")
for reason in ["disabled", "replaced", "revoked", "heartbeat_timeout", "restart"]:
    if f"`{reason}`" not in websocket_protocol_text:
        raise SystemExit(f"WebSocket protocol is missing disconnect reason: {reason}")
if "A fatal error ends consumption" not in websocket_protocol_text:
    raise SystemExit("WebSocket protocol lost fatal error handling")
for required in [
    "wss://api.relayapp.im/v1/websocket",
    "Authorization: Bearer $RELAY_AGENT_TOKEN",
    "query credential or cookie",
    "does not require a",
    "Security trade-off",
]:
    if required not in websocket_text:
        raise SystemExit(f"WebSocket authentication guide is missing: {required}")
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
    "PostgreSQL for 30 days",
    "PostHog",
]:
    if required not in websocket_recovery_text:
        raise SystemExit(f"WebSocket recovery guide is missing: {required}")
for required in [
    "1 immediate attempt",
    "Up to 10",
    "10 seconds per attempt",
    "`429`",
    "`5xx`",
    "72 hours",
    "PostgreSQL",
    "30 days",
    "PostHog",
    "recover current Chat and Message state",
]:
    if required not in webhook_delivery_text:
        raise SystemExit(f"Webhook delivery policy is missing: {required}")
for required in [
    "chat.typing_indicator.started",
    "chat.typing_indicator.stopped",
    "every 60 seconds",
    "85 to 90 seconds",
    '"contact": {',
    "expires automatically",
]:
    if required not in typing_text:
        raise SystemExit(f"Typing guide is missing: {required}")

group_text = (root / "guides/chats/group-chats.mdx").read_text()
if (
    "2 to 31 recipient Handles plus the sender" not in group_text
    or "keep at least three active Contacts" not in group_text
):
    raise SystemExit("Group Chat guide lost max-32 and minimum-three rules")

concepts_text = (root / "getting-started/key-concepts.mdx").read_text()
if (
    "reserved inside its owning namespace" not in concepts_text
    or "Archiving the Contact" not in concepts_text
):
    raise SystemExit("Handle archive reservation rule is missing")

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
for path in error_paths:
    blocks = re.findall(r"```json\n(.*?)\n```", path.read_text(), re.S)
    if len(blocks) != 1:
        raise SystemExit(f"expected one JSON response example in {path.relative_to(root)}")
    try:
        example = json.loads(blocks[0])
    except json.JSONDecodeError as error:
        raise SystemExit(f"invalid error JSON in {path.relative_to(root)}: {error}") from error
    status = example.get("error", {}).get("status")
    if not isinstance(status, int):
        raise SystemExit(f"required error.status missing in {path.relative_to(root)}")
    code = example.get("error", {}).get("code")
    if code != int(path.stem):
        raise SystemExit(f"error.code does not match page path in {path.relative_to(root)}")
    expected_doc_url = (
        f"https://docs.relayapp.im/error/codes/{int(path.stem) // 1000}xxx/{path.stem}"
    )
    if example.get("error", {}).get("doc_url") != expected_doc_url:
        raise SystemExit(f"error.doc_url drifted in {path.relative_to(root)}")

openapi_text = (root / "api-reference/openapi.yaml").read_text()
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
openapi_paths = re.findall(r"^  (/[^:]+):$", openapi_text, re.M)
if not openapi_paths or any(not path.startswith("/v1/") for path in openapi_paths):
    raise SystemExit(f"every public OpenAPI path must live under /v1: {openapi_paths}")
for required_path in [
    "/v1/chats/{chatId}/share_contact_card",
    "/v1/chats/{chatId}/typing",
    "/v1/websocket",
]:
    if required_path not in openapi_paths:
        raise SystemExit(f"canonical OpenAPI path missing: {required_path}")
if "/v1/websocket-connections" in openapi_paths:
    raise SystemExit("stale WebSocket connection-credential endpoint returned")
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
    "disabled", "replaced", "revoked", "heartbeat_timeout", "restart"
]:
    raise SystemExit(f"WebSocket disconnect reasons drifted: {disconnect_reasons}")

handwritten_paths = [*mdx_paths, root / "skill.md", root / "README.md"]
handwritten_text = "\n".join(path.read_text() for path in handwritten_paths)
all_contract_text = handwritten_text + "\n" + openapi_text

for name, pattern in {
    "Socket Mode product name": r"\bSocket Mode\b",
    "agent installation lifecycle": r"\bagent installation\b|\binstalled agents?\b|\binstall agents?\b",
    "agent share-link lifecycle": r"\bshare[- ]link\b",
    "stale guide path": r"guides/(?:socket-mode|chats/install-agents|webhooks/choose-transport|platform/errors)",
    "old public status language": r"current-status|Current status|known contract residue|local proof|evidence app",
    "old WebSocket handshake": r"/v1/websocket-connections|relay_ticket_|relay\.v1\.json|\?ticket=",
    "source-company language": r"\bLinq\b",
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
    f"validated {len(files)} public pages, three tabs, atomic guide groups, "
    "frontmatter, bodyless Contact Card sharing, exact delivery states and error pages, "
    "typing, webhook retries, transport recovery, URL safety, WebSocket disconnects, "
    "and stale-contract bans"
)
