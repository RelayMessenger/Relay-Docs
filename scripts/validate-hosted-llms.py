#!/usr/bin/env python3
import argparse
import hashlib
import json
import re
import secrets
import struct
import zlib
from datetime import datetime, timezone
from html.parser import HTMLParser
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


def png_color_counts(body: bytes) -> dict:
    if not body.startswith(b"\x89PNG\r\n\x1a\n"):
        raise SystemExit("generated favicon is not a PNG")
    offset = 8
    chunks = {}
    idat = []
    while offset < len(body):
        length = struct.unpack(">I", body[offset : offset + 4])[0]
        kind = body[offset + 4 : offset + 8]
        data = body[offset + 8 : offset + 8 + length]
        offset += 12 + length
        if kind == b"IDAT":
            idat.append(data)
        else:
            chunks[kind] = data
        if kind == b"IEND":
            break

    width, height, bit_depth, color_type, _, _, interlace = struct.unpack(
        ">IIBBBBB", chunks[b"IHDR"]
    )
    if bit_depth != 8 or interlace != 0 or color_type not in {2, 3, 6}:
        raise SystemExit(
            "generated favicon uses an unsupported PNG encoding "
            f"(depth={bit_depth}, color={color_type}, interlace={interlace})"
        )
    channels = {2: 3, 3: 1, 6: 4}[color_type]
    stride = width * channels
    decoded = zlib.decompress(b"".join(idat))
    previous = bytearray(stride)
    rows = []
    cursor = 0

    def paeth(a, b, c):
        estimate = a + b - c
        distances = (abs(estimate - a), abs(estimate - b), abs(estimate - c))
        return (a, b, c)[distances.index(min(distances))]

    for _ in range(height):
        filter_type = decoded[cursor]
        cursor += 1
        encoded = decoded[cursor : cursor + stride]
        cursor += stride
        row = bytearray(stride)
        for index, value in enumerate(encoded):
            left = row[index - channels] if index >= channels else 0
            above = previous[index]
            upper_left = previous[index - channels] if index >= channels else 0
            if filter_type == 0:
                predicted = 0
            elif filter_type == 1:
                predicted = left
            elif filter_type == 2:
                predicted = above
            elif filter_type == 3:
                predicted = (left + above) // 2
            elif filter_type == 4:
                predicted = paeth(left, above, upper_left)
            else:
                raise SystemExit(f"generated favicon uses PNG filter {filter_type}")
            row[index] = (value + predicted) & 0xFF
        rows.append(row)
        previous = row

    palette = chunks.get(b"PLTE", b"")
    transparency = chunks.get(b"tRNS", b"")
    counts = {"opaque": 0, "black": 0, "blue": 0, "white": 0}
    for row in rows:
        for index in range(0, len(row), channels):
            if color_type == 3:
                palette_index = row[index]
                base = palette_index * 3
                red, green, blue = palette[base : base + 3]
                alpha = (
                    transparency[palette_index]
                    if palette_index < len(transparency)
                    else 255
                )
            elif color_type == 2:
                red, green, blue = row[index : index + 3]
                alpha = 255
            else:
                red, green, blue, alpha = row[index : index + 4]
            if alpha <= 16:
                continue
            counts["opaque"] += 1
            if red < 32 and green < 32 and blue < 32:
                counts["black"] += 1
            if blue > 128 and blue > red * 1.4 and blue > green * 1.1:
                counts["blue"] += 1
            if red > 224 and green > 224 and blue > 224:
                counts["white"] += 1
    return counts


class IconLinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.icons = []

    def handle_starttag(self, tag, attrs):
        if tag != "link":
            return
        values = dict(attrs)
        rel = set((values.get("rel") or "").split())
        if "icon" in rel:
            self.icons.append(values)


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
page_bodies = {}
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
    page_bodies["/" + path] = canonical["body"]

staging_favicon = fetch("favicon-staging.png")
expected_favicon_sha = (
    "4b3e4b9358f35c66cec564d7ae6806b8e948a2e4dc0e1fd2eb003887ee1120be"
)
if staging_favicon["sha256"] != expected_favicon_sha:
    raise SystemExit(
        "hosted /favicon-staging.png is not the canonical black Relay mark"
    )

icon_parser = IconLinkParser()
icon_parser.feed(page_bodies["/"].decode("utf-8"))
generated = next(
    (
        icon
        for icon in icon_parser.icons
        if icon.get("sizes") == "192x192"
        and icon.get("href", "").endswith(".png")
    ),
    None,
)
if generated is None:
    raise SystemExit("hosted Docs root has no generated 192x192 favicon")
generated_favicon = fetch(generated["href"])
favicon_colors = png_color_counts(generated_favicon["body"])
if (
    favicon_colors["opaque"] == 0
    or favicon_colors["black"] <= favicon_colors["blue"]
    or favicon_colors["black"] / favicon_colors["opaque"] < 0.5
):
    raise SystemExit(
        "hosted Docs generated favicon is not the black staging identity: "
        + json.dumps(favicon_colors, sort_keys=True)
    )
brand = {
    "source": {
        key: value
        for key, value in staging_favicon.items()
        if key != "body"
    },
    "generated": {
        **{
            key: value
            for key, value in generated_favicon.items()
            if key != "body"
        },
        "colors": favicon_colors,
    },
}

root_headers = pages["/"]["canonical"]["headers"]
guides_headers = pages["/guides"]["canonical"]["headers"]
root_version = root_headers.get("x-served-version") or root_headers.get("x-version")
guides_version = guides_headers.get("x-served-version") or guides_headers.get(
    "x-version"
)
if not root_version or root_version != guides_version:
    raise SystemExit(
        "root and /guides are not served by the same Mintlify deployment"
    )

index = fetch("llms.txt")["body"].decode("utf-8")
complete = fetch("llms-full.txt")["body"].decode("utf-8")
normalized = re.sub(r"\s+", " ", complete).lower()

sdk_install_commands = [
    line.strip()
    for line in complete.splitlines()
    if re.match(r"^(?:npm (?:install|i)|pnpm add|yarn add|bun add)\b", line.strip())
    and "@relaymessenger/sdk" in line
]
if len(sdk_install_commands) != 2:
    raise SystemExit(
        "llms-full.txt must contain both staging SDK installation commands"
    )
for command in sdk_install_commands:
    package_tokens = [
        token for token in command.split() if token.startswith("@relaymessenger/sdk")
    ]
    if package_tokens != ["@relaymessenger/sdk@staging"]:
        raise SystemExit(
            "llms-full.txt contains a non-staging SDK install command: "
            f"{command}"
        )

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
    "staging_brand": brand,
    "pages": pages,
    "verdict": "passed",
}
serialized = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
if args.receipt:
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(serialized)

print(
    "validated canonical root, /guides, llms.txt, and llms-full.txt; "
    "bare and cache-busted bodies match, the favicon is black, and "
    "deleted wording is absent"
)
if deployment:
    print(
        f"validated staging deployment {deployment['id']} at "
        f"{deployment['sha']}"
    )
if args.receipt:
    print(f"receipt: {args.receipt}")
