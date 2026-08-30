#!/usr/bin/env python3
import re
import sys
from urllib.parse import urljoin
from urllib.request import Request, urlopen


if len(sys.argv) != 2:
    raise SystemExit(
        "usage: python3 scripts/validate-hosted-llms.py <preview-base-url>"
    )

base_url = sys.argv[1].rstrip("/") + "/"


def fetch(path: str) -> str:
    request = Request(
        urljoin(base_url, path),
        headers={"User-Agent": "Relay-Docs-LLM-Validator/1.0"},
    )
    with urlopen(request, timeout=30) as response:
        if response.status != 200:
            raise SystemExit(f"{path} returned HTTP {response.status}")
        body = response.read().decode("utf-8")
    if not body.strip():
        raise SystemExit(f"{path} is empty")
    return body


index = fetch("llms.txt")
complete = fetch("llms-full.txt")
normalized = re.sub(r"\s+", " ", complete).lower()

for page in [
    "Agent Events",
    "Webhook Subscriptions",
    "Webhook delivery",
    "WebSocket Protocol",
    "WebSocket FULL Sync",
]:
    if page.lower() not in index.lower():
        raise SystemExit(f"llms.txt is missing page: {page}")

for rule in [
    "one or more saved subscriptions",
    "zero webhook subscriptions",
    "empty subscription list",
    "http `409`",
    "closes connected agent sockets",
    "deleting the last subscription",
    "wait durably",
    "30 days",
    "cumulative ack",
    "full sync",
    "ping every 30 seconds",
    "within 60 seconds",
    "localhost",
    "private",
    "link-local",
    "redirect is not followed",
    "same `event_id`",
]:
    if rule not in normalized:
        raise SystemExit(f"llms-full.txt is missing final transport rule: {rule}")

for stale in [
    "relay.websocket.update",
    '{"enabled":true}',
    '"enabled": true',
    "enable or disable websocket event delivery",
    "get websocket settings",
    "update websocket settings",
]:
    if stale in normalized:
        raise SystemExit(f"llms-full.txt still contains stale transport text: {stale}")

print(
    "validated hosted llms.txt and llms-full.txt against the final "
    "Relay transport decision"
)
