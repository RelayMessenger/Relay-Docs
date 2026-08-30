#!/usr/bin/env python3
import argparse
import hashlib
import json
import re
import secrets
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen


parser = argparse.ArgumentParser(
    description=(
        "Validate Relay's canonical hosted pages and prove that generated LLM "
        "files are not stale edge-cache variants."
    )
)
parser.add_argument("base_url")
parser.add_argument("--expected-sha")
parser.add_argument("--receipt", type=Path)
args = parser.parse_args()

base_url = args.base_url.rstrip("/") + "/"
probe = secrets.token_hex(12)
canonical_paths = ("", "guides", "llms.txt", "llms-full.txt")
deleted_wording = {
    "Socket Mode product name": re.compile(r"\bsocket mode\b", re.IGNORECASE),
    "WebSocket settings event": re.compile(
        r"relay\.websocket\.update", re.IGNORECASE
    ),
    "WebSocket enabled flag": re.compile(
        r'"enabled"\s*:\s*true', re.IGNORECASE
    ),
    "WebSocket enable setting": re.compile(
        r"enable or disable websocket event delivery", re.IGNORECASE
    ),
    "WebSocket get settings": re.compile(
        r"get websocket settings", re.IGNORECASE
    ),
    "WebSocket update settings": re.compile(
        r"update websocket settings", re.IGNORECASE
    ),
    "transport mode disclaimer": re.compile(
        r"there is no mode, toggle, or transport setting", re.IGNORECASE
    ),
    "duplicate-path disclaimer": re.compile(
        r"relay never sends one event through both paths", re.IGNORECASE
    ),
}


def sha256(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def fetch(path: str, cache_busted: bool = False) -> dict:
    relative_url = path
    if cache_busted:
        relative_url += ("&" if "?" in relative_url else "?") + urlencode(
            {"relay_cache_probe": probe}
        )
    requested_url = urljoin(base_url, relative_url)
    request = Request(
        requested_url,
        headers={"User-Agent": "Relay-Docs-Hosted-Validator/2.0"},
    )
    with urlopen(request, timeout=60) as response:
        body = response.read()
        status = response.status
        headers = {key.lower(): value for key, value in response.headers.items()}
        final_url = response.url
    if status != 200:
        raise SystemExit(f"/{path} returned HTTP {status}")
    if not body.strip():
        raise SystemExit(f"/{path} is empty")
    return {
        "requested_url": requested_url,
        "final_url": final_url,
        "status": status,
        "bytes": len(body),
        "sha256": sha256(body),
        "headers": {
            key: headers[key]
            for key in (
                "age",
                "cache-control",
                "cf-cache-status",
                "etag",
                "last-modified",
                "x-served-version",
                "x-version",
            )
            if key in headers
        },
        "body": body,
    }


pages = {}
for path in canonical_paths:
    canonical = fetch(path)
    cache_busted = fetch(path, cache_busted=True)
    if canonical["body"] != cache_busted["body"]:
        raise SystemExit(
            f"/{path} canonical body {canonical['sha256']} does not match "
            f"current origin body {cache_busted['sha256']}"
        )
    text = canonical["body"].decode("utf-8")
    for label, pattern in deleted_wording.items():
        if pattern.search(text):
            raise SystemExit(f"/{path} contains deleted wording: {label}")
    pages["/" + path] = {
        "canonical": {
            key: value for key, value in canonical.items() if key != "body"
        },
        "cache_busted": {
            key: value for key, value in cache_busted.items() if key != "body"
        },
    }

root_version = pages["/"]["canonical"]["headers"].get("x-served-version")
guides_version = pages["/guides"]["canonical"]["headers"].get("x-served-version")
if not root_version or root_version != guides_version:
    raise SystemExit(
        "root and /guides are not served by the same Mintlify deployment"
    )

index = fetch("llms.txt")["body"].decode("utf-8")
complete = fetch("llms-full.txt")["body"].decode("utf-8")
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

deployment = None
if args.expected_sha:
    if not re.fullmatch(r"[0-9a-f]{40}", args.expected_sha):
        raise SystemExit("--expected-sha must be a full lowercase Git SHA")
    deployments_url = (
        "https://api.github.com/repos/RelayMessenger/Relay-Docs/deployments?"
        + urlencode(
            {
                "sha": args.expected_sha,
                "environment": "staging",
                "per_page": 10,
            }
        )
    )
    request = Request(
        deployments_url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "Relay-Docs-Hosted-Validator/2.0",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urlopen(request, timeout=60) as response:
        deployments = json.load(response)
    if not deployments:
        raise SystemExit(
            f"GitHub has no staging deployment for {args.expected_sha}"
        )
    for candidate in deployments:
        statuses_url = candidate["statuses_url"]
        status_request = Request(
            statuses_url,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "Relay-Docs-Hosted-Validator/2.0",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        with urlopen(status_request, timeout=60) as response:
            statuses = json.load(response)
        successful = next(
            (
                status
                for status in statuses
                if status["state"] == "success"
                and status.get("environment_url", "").rstrip("/")
                == base_url.rstrip("/")
            ),
            None,
        )
        if successful:
            deployment = {
                "id": candidate["id"],
                "sha": candidate["sha"],
                "ref": candidate["ref"],
                "environment": candidate["environment"],
                "created_at": candidate["created_at"],
                "status_id": successful["id"],
                "status": successful["state"],
                "environment_url": successful["environment_url"],
                "updated_at": successful["updated_at"],
            }
            break
    if deployment is None:
        raise SystemExit(
            f"GitHub has no successful {base_url.rstrip('/')} deployment "
            f"for {args.expected_sha}"
        )

receipt = {
    "schema_version": 1,
    "checked_at": datetime.now(timezone.utc).isoformat(),
    "base_url": base_url.rstrip("/"),
    "expected_sha": args.expected_sha,
    "mintlify_deployment_version": root_version,
    "github_deployment": deployment,
    "deleted_wording": list(deleted_wording),
    "pages": pages,
    "verdict": "passed",
}
serialized = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
if args.receipt:
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(serialized)

print(
    "validated canonical root, /guides, llms.txt, and llms-full.txt; "
    "bare and cache-busted bodies match and contain no deleted wording"
)
if deployment:
    print(
        f"validated staging deployment {deployment['id']} at "
        f"{deployment['sha']}"
    )
if args.receipt:
    print(f"receipt: {args.receipt}")
