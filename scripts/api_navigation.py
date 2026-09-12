"""Nested API navigation with stable public endpoint-page URLs."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Owner ruling 2026-09-11 (night): the seventeen webhook event pages are their
# own top tab, "Webhook events", next to API reference. Their files never
# moved, so every /events path still resolves.
RESOURCE_GROUPS = ["Chats", "Messages", "Attachments", "Contacts", "Webhooks", "WebSocket", "Agents"]
RESOURCE_OBJECTS = {"Chats": "Chat", "Messages": "Message", "Attachments": "Attachment", "Contacts": "Contact", "Webhooks": "Webhook", "WebSocket": "WebSocket", "Agents": "Agent"}
EVENT_GROUP = "Webhook events"
EVENT_PAGES = [
    "events/index", "events/chat-created", "events/chat-group-icon-updated",
    "events/chat-group-name-updated", "events/chat-request-updated",
    "events/chat-typing-indicator-started", "events/chat-typing-indicator-stopped",
    "events/contact-added", "events/contact-removed", "events/message-delivered",
    "events/message-failed", "events/message-read",
    "events/message-received", "events/message-sent",
    "events/participant-added", "events/participant-removed",
    "events/reaction-added", "events/reaction-removed",
]
# The tab groups events by subject, in the API reference's resource order.
EVENT_TAB_GROUPS = [
    ("Overview", ["events/index"]),
    ("Messages", ["events/message-received", "events/message-sent", "events/message-delivered", "events/message-read", "events/message-failed"]),
    ("Chats", ["events/chat-created", "events/chat-group-name-updated", "events/chat-group-icon-updated", "events/chat-request-updated", "events/chat-typing-indicator-started", "events/chat-typing-indicator-stopped"]),
    ("Participants", ["events/participant-added", "events/participant-removed"]),
    ("Contacts", ["events/contact-added", "events/contact-removed"]),
    ("Reactions", ["events/reaction-added", "events/reaction-removed"]),
]
assert sorted(page for _, pages in EVENT_TAB_GROUPS for page in pages) == sorted(EVENT_PAGES)


def walk_pages(items, parents=()):
    for item in items:
        if isinstance(item, str):
            yield parents, item
        elif isinstance(item, dict) and isinstance(item.get("pages"), list):
            yield from walk_pages(item["pages"], (*parents, item["group"]))
        else:
            raise ValueError(f"Invalid navigation entry: {item!r}")


def page_paths():
    return json.loads((ROOT / "scripts/api-page-paths.json").read_text())


def validate_api_navigation(config):
    api = next(tab for tab in config["navigation"]["tabs"] if tab["tab"] == "API reference")
    groups = api["groups"]
    if not set(RESOURCE_GROUPS).issubset({g["group"] for g in groups}):
        raise ValueError("API resources must have their own groups")
    expected_groups = ["Overview", *RESOURCE_GROUPS]
    if [g["group"] for g in groups] != expected_groups:
        raise ValueError("API group order must match the resource tree")
    events_tab = next((tab for tab in config["navigation"]["tabs"] if tab["tab"] == EVENT_GROUP), None)
    if events_tab is None:
        raise ValueError("Webhook events must be its own tab")
    events_groups = events_tab.get("groups", [])
    if [g["group"] for g in events_groups] != [name for name, _ in EVENT_TAB_GROUPS]:
        raise ValueError("The Webhook events tab groups events by subject: Overview, Messages, Chats, Participants, Contacts, Reactions")
    for (name, expected_pages), group in zip(EVENT_TAB_GROUPS, events_groups):
        if group["pages"] != expected_pages:
            raise ValueError(f"Webhook events group {name} must list exactly its event pages in order")
    if groups[0]["pages"] != ["api-reference/overview", "api-reference/errors"]:
        raise ValueError("API must start with Overview and Error codes")
    if api.get("openapi") != "api-reference/openapi.mint.yaml":
        raise ValueError("API must use the generated OpenAPI bundle")
    entries = list(walk_pages(groups))
    methods = ("GET ", "POST ", "PUT ", "PATCH ", "DELETE ")
    endpoints = [(parents, page) for parents, page in entries if page.startswith(methods)]
    expected = {entry["endpoint"]: entry for entry in page_paths().values()}
    found = [page for _, page in endpoints]
    if len(found) != len(set(found)) or set(found) != set(expected):
        raise ValueError("API navigation must contain every endpoint exactly once")
    for parents, page in endpoints:
        if parents != (expected[page]["group"][0],):
            raise ValueError(f"Incorrect resource nesting for {page}: {parents}")
    hrefs = [entry["href"] for entry in expected.values()]
    if len(set(hrefs)) != len(hrefs) or any(not href.startswith("/api-reference/") for href in hrefs):
        raise ValueError("Endpoint page URLs must be unique API reference paths")

    def check_overviews(items):
        for item in items:
            if not isinstance(item, dict):
                continue
            pages = item["pages"]
            if item["group"] in {"Chats", "Messages", "Attachments", "Contacts", "Webhooks", "WebSocket", "Agents"}:
                if not pages or not isinstance(pages[0], str) or not pages[0].endswith("/overview"):
                    raise ValueError(f"{item['group']} must start with its overview")
                if item.get("expanded") is not False:
                    raise ValueError(f"{item['group']} must collapse when inactive")
            check_overviews(pages)

    check_overviews(groups)
    resources = [g for g in groups if g["group"] in set(RESOURCE_GROUPS)]
    for group in resources:
        if any(not page.startswith(methods) for page in group["pages"][1:]):
            raise ValueError("Only generated endpoints may follow a resource overview")
    import re
    for group in resources:
        path = ROOT / (group["pages"][0] + ".mdx")
        headings = re.findall(r"^## (.+)$", path.read_text(), re.M)
        resource = RESOURCE_OBJECTS[group["group"]]
        if headings != [f"The {resource} object", "Example", "Operations", "Errors", "Next steps"]:
            raise ValueError(f"Resource overview skeleton drifted: {path}")
    return found
