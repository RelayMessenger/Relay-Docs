#!/usr/bin/env python3
"""Validate the selected environment against this checkout, without rewriting it.

--production selects production checks, not a projection of staging source bytes.
Use a derived production checkout when checking a production deployment.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import secrets
import struct
import textwrap
from urllib.parse import urlencode, urljoin, urlsplit, unquote
from urllib.request import Request, urlopen
import zlib

import origins
from hosted_cache import CANONICAL_PATHS, canonical_cache_pairs

ROOT = Path(__file__).resolve().parents[1]
AGENT_SOURCES = ("skill.md", "agent-prompt.md", "llms.txt", "llms-full.txt")
USER_AGENT = "Relay-Docs-Hosted-Validator/3.0"
ENDPOINT = re.compile(r"^(?:GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS) /v1/")
FENCE = re.compile(r"^[ \t]*(`{3,}|~{3,})([^\n]*)\n(.*?)^[ \t]*\1[ \t]*$", re.M | re.S)

deleted_wording = {
    "Socket Mode product name": re.compile(r"\bsocket mode\b", re.IGNORECASE),
    "WebSocket settings event": re.compile(
        r"relay\.websocket\.update", re.IGNORECASE
    ),
    # The deleted WebSocket settings object was a bare {"enabled": true} or an
    # "enabled" flag inside a websocket settings payload. OpenClaw's channel
    # config legitimately carries "enabled": true (packages/openclaw/src/types.ts),
    # so a bare "enabled" match is not evidence of the deleted wording.
    "WebSocket enabled flag": re.compile(
        r'\{\s*"enabled"\s*:\s*true\s*\}|websocket[^{}]{0,160}\{[^{}]{0,80}"enabled"\s*:\s*true',
        re.IGNORECASE,
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
    "stale Relay webhook version": re.compile(r"2026-02-03"),
    "webhook acknowledgement controls Delivered": re.compile(
        r"marks that agent recipient delivered", re.IGNORECASE
    ),
    "transport acceptance controls Delivered": re.compile(
        r"marks the message delivered to the agent", re.IGNORECASE
    ),
}



def sha256(body):
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


def environment_config(production=False):
    environment = "production" if production else origins.target()
    favicon = "/favicon-staging.png"
    if environment == "production":
        favicon = origins.STAGING_TO_PRODUCTION[favicon]
    return {"environment": environment, "favicon": favicon.lstrip("/"),
            "color": "blue" if environment == "production" else "black"}


def make_fetch(base_url, opener=urlopen):
    probe = secrets.token_hex(12)

    def fetch(path, cache_busted=False):
        url = urljoin(base_url.rstrip("/") + "/", path)
        if cache_busted:
            url += ("&" if "?" in url else "?") + urlencode({"relay_cache_probe": probe})
        request = Request(url, headers={"User-Agent": USER_AGENT})
        with opener(request, timeout=60) as response:
            body = response.read()
            status = response.status
            headers = {key.lower(): value for key, value in response.headers.items()}
            final_url = response.url
        if status != 200 or not body.strip():
            raise SystemExit(f"/{path} returned HTTP {status} or an empty body")
        return {"requested_url": url, "final_url": final_url, "status": status,
                "bytes": len(body), "sha256": sha256(body), "body": body,
                "headers": {key: headers[key] for key in (
                    "age", "cache-control", "cf-cache-status", "etag", "last-modified",
                    "x-served-version", "x-version") if key in headers}}
    return fetch


def response_pair(canonical, busted):
    return {name: {key: value for key, value in response.items() if key != "body"}
            for name, response in (("canonical", canonical), ("cache_busted", busted))}


def hosted_source_pairs(fetch, expected, require_edge_fresh=False):
    """Check published source bytes; keep non-source cache checks unchanged."""
    for path in CANONICAL_PATHS:
        if path not in expected:
            yield from canonical_cache_pairs(fetch, paths=[path])
            continue
        canonical = fetch(path)
        busted = fetch(path, cache_busted=True)
        if busted["body"] != expected[path]:
            raise SystemExit(f"/{path} served body does not match expected checkout source bytes")
        if canonical["body"] != busted["body"]:
            if require_edge_fresh:
                raise SystemExit(
                    f"/{path} canonical body {canonical['sha256']} does not match "
                    f"current origin body {busted['sha256']}"
                )
            headers = canonical["headers"]
            max_age = re.search(r'(?:^|,)\s*max-age\s*=\s*"?(\d+)',
                                headers.get("cache-control", ""), re.I)
            print(f"/{path}: edge cache is {headers.get('age', 'unknown')} s behind origin "
                  f"(max-age {max_age[1] if max_age else 'unknown'}); origin matches checkout")
        yield path, canonical, busted


def check_brand(fetch, root_html, root, settings):
    source = settings["favicon"]
    expected = {source: (root / source).read_bytes()}
    _, canonical, busted = next(canonical_cache_pairs(fetch, expected, paths=[source]))
    parser = IconLinkParser()
    parser.feed(root_html.decode("utf-8"))
    icon = next((item for item in parser.icons if item.get("sizes") == "192x192"
                 and urlsplit(item.get("href", "")).path.endswith(".png")), None)
    if icon is None:
        raise SystemExit("hosted Docs root has no generated 192x192 favicon")
    _, generated, generated_busted = next(canonical_cache_pairs(fetch, paths=[icon["href"]]))
    colors = png_color_counts(generated["body"])
    wanted = settings["color"]
    other = "black" if wanted == "blue" else "blue"
    if (not colors["opaque"] or colors[wanted] <= colors[other]
            or colors[wanted] / colors["opaque"] < 0.5):
        raise SystemExit(f"generated favicon is not the {wanted} {settings['environment']} identity: {colors}")
    return {"source": response_pair(canonical, busted),
            "generated": response_pair(generated, generated_busted), "colors": colors}


def navigation_pages(config):
    """Discover all pages, including arbitrarily nested navigation groups."""
    found = []

    def walk(value, in_pages=False):
        if isinstance(value, str) and in_pages:
            if not urlsplit(value).scheme:
                found.append(value)
        elif isinstance(value, list):
            for item in value:
                walk(item, in_pages)
        elif isinstance(value, dict):
            for key, item in value.items():
                walk(item, key == "pages")
    walk(config["navigation"])
    if not found:
        raise SystemExit("navigation contains no pages")
    return list(dict.fromkeys(found))


def read_page(root, page):
    path = root / f"{page}.mdx"
    if not path.is_file():
        raise SystemExit(f"navigation source missing: {page}.mdx")
    source = path.read_text()
    match = re.match(r"\A---\n(.*?)\n---\n(.*)\Z", source, re.S)
    if not match:
        raise SystemExit(f"invalid frontmatter: {page}.mdx")
    title = re.search(r"^title:\s*(.+)$", match[1], re.M)
    if not title:
        raise SystemExit(f"title missing: {page}.mdx")
    value = title[1].strip()
    if value.startswith('"'):
        value = json.loads(value)
    elif value.startswith("'") and value.endswith("'"):
        value = value[1:-1].replace("''", "'")
    return {"page": page, "title": value, "body": match[2]}


def check_discovery(root, config, index, complete):
    links = {unquote(urlsplit(link).path) for link in re.findall(r"\]\(([^)]+)\)", index)}
    endpoint_map = json.loads((root / "scripts/api-page-paths.json").read_text())
    endpoint_routes = {value["endpoint"]: value["href"] for value in endpoint_map.values()}
    # Parse Source URLs independently of the hostname or local preview origin.
    sources = {unquote(urlsplit(line).path) for line in re.findall(r"^Source:\s+(\S+)$", complete, re.M)}
    authored = []
    for page in navigation_pages(config):
        if ENDPOINT.match(page):
            route = endpoint_routes.get(page)
            if route is None:
                raise SystemExit(f"navigation endpoint has no source route: {page}")
            markdown = route + ".md"
        else:
            authored.append(read_page(root, page))
            markdown = "/" + page + ".md"
            if markdown not in sources:
                raise SystemExit(f"llms-full.txt is missing navigation source: {markdown}")
        if markdown not in links:
            raise SystemExit(f"llms.txt is missing navigation route: {markdown}")
    contract = (root / "api-reference/openapi.yaml").read_text()
    pattern = r"^\s+operationId:\s*[\"']?([A-Za-z0-9_.-]+)"
    expected_ids = set(re.findall(pattern, contract, re.M))
    carried_ids = set(re.findall(pattern, complete, re.M))
    if not expected_ids or expected_ids - carried_ids:
        raise SystemExit(f"llms-full.txt is missing current contract operation IDs: {sorted(expected_ids - carried_ids)}")
    return authored, sorted(expected_ids)


def check_sdk_installs(complete, environment):
    """Check actual install commands, not a prescribed number of prose copies."""
    commands = []
    for line in re.sub(r"\\\r?\n\s*", " ", complete).splitlines():
        line = line.strip()
        if re.match(r"^(?:npm (?:install|i)|pnpm add|yarn add|bun add)\b", line):
            specs = re.findall(r"@relaymessenger/sdk(?:@[^\s`\"']+)?(?=[\s`\"']|$)", line)
            if specs:
                commands.extend(specs)
    expected = "@relaymessenger/sdk" + ("@staging" if environment == "staging" else "")
    if not commands or any(spec != expected for spec in commands):
        raise SystemExit(f"{environment} SDK install commands must use {expected}: {commands}")
    return len(commands)


class VisibleHTML(HTMLParser):
    """Ignore hydration/navigation metadata; retain rendered prose and code."""
    BLOCKS = {"p", "div", "section", "article", "main", "li", "tr", "td", "th", "pre", "br",
              "h1", "h2", "h3", "h4", "h5", "h6"}
    HIDDEN = {"script", "style", "svg", "noscript", "nav", "aside"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.titles = []
        self.hidden = 0
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        if tag in self.HIDDEN:
            self.hidden += 1
        if not self.hidden:
            if tag in self.BLOCKS:
                self.parts.append("\n")
            if tag == "h1":
                self.in_title = True
                self.titles.append("")

    def handle_endtag(self, tag):
        if tag in self.HIDDEN:
            self.hidden = max(0, self.hidden - 1)
        if not self.hidden:
            if tag in self.BLOCKS:
                self.parts.append("\n")
            if tag == "h1":
                self.in_title = False

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)
            if self.in_title:
                self.titles[-1] += data


def prose(text):
    """Normalize presentation only. Keep words, case, numbers and punctuation."""
    text = re.sub(r"\{/[\*].*?[\*]/\}|<!--.*?-->", "", text, flags=re.S)
    text = re.sub(r"</?[A-Z][A-Za-z0-9.]*\b[^>]*>", "\n", text)
    text = re.sub(r"</?(?:p|div|span|br|strong|em|a|code)\b[^>]*>", "", text)
    text = re.sub(r"!?\[([^]\n]*)\]\([^\n]*?\)", r"\1", text)
    text = re.sub(r"^\s*\|?[ :|\-]+\|\s*$", "", text, flags=re.M)
    text = re.sub(r"^\s*(?:#{1,6}\s+|>\s*|[-*+]\s+|\d+\.\s+)", "", text, flags=re.M)
    text = text.replace("**", "").replace("`", "").replace("|", " ")
    text = re.sub(r"\\([`*_{}\[\]()#+.!|<>-])", r"\1", text)
    return " ".join(html.unescape(text).split())


def source_fragments(body):
    without_blocks = FENCE.sub("", body)
    without_blocks = re.sub(r"\{/[\*].*?[\*]/\}|<!--.*?-->", "", without_blocks, flags=re.S)
    without_blocks = re.sub(r"</?[A-Z][A-Za-z0-9.]*\b[^>]*>", "\n\n", without_blocks)
    return [value for part in re.split(r"\n\s*\n", without_blocks)
            if len(value := prose(part)) >= 24]


def code_blocks(body):
    return [textwrap.dedent(match[3]).strip("\n").replace("\r\n", "\n")
            for match in FENCE.finditer(body)]


def check_page_content(page, body, markdown=False):
    text = body.decode("utf-8")
    title = prose(page["title"])
    if markdown:
        titles = [prose(value) for value in re.findall(r"^#\s+(.+)$", FENCE.sub("", text), re.M)]
        front = re.match(r"\A---\n(.*?)\n---", text, re.S)
        if front:
            match = re.search(r"^title:\s*(.+)$", front[1], re.M)
            if match:
                titles.append(prose(match[1].strip().strip('\"\'')))
        visible = prose(text)
        hosted_blocks = code_blocks(text)
        for block in code_blocks(page["body"]):
            if block not in hosted_blocks:
                raise SystemExit(f"/{page['page']}.md has a missing or stale source code block")
    else:
        parser = VisibleHTML()
        parser.feed(text)
        titles = [prose(value) for value in parser.titles]
        visible = prose("".join(parser.parts))
    if title not in titles:
        raise SystemExit(f"/{page['page']} has a missing or stale title: {page['title']}")
    fragments = source_fragments(page["body"])
    if not fragments:
        raise SystemExit(f"/{page['page']} has no distinctive source prose to verify")
    for fragment in fragments:
        if fragment not in visible:
            raise SystemExit(f"/{page['page']} has missing or stale source content: {fragment[:140]}")


def authored_route(page):
    if page == "index":
        return ""
    return page.removesuffix("/index")


def check_all_pages(fetch, authored, workers=6):
    if not 1 <= workers <= 16:
        raise SystemExit("--workers must be between 1 and 16")

    def check(page):
        route = authored_route(page["page"])
        markdown = page["page"] + ".md"
        receipt = {}
        for path, canonical, busted in canonical_cache_pairs(fetch, paths=[route, markdown]):
            check_page_content(page, canonical["body"], markdown=path == markdown)
            receipt["/" + path] = response_pair(canonical, busted)
        return receipt

    pages = {}
    executor = ThreadPoolExecutor(max_workers=workers)
    try:
        for checked in executor.map(check, authored):
            pages.update(checked)
    finally:
        executor.shutdown(wait=True, cancel_futures=True)
    return pages


def check_authored_inventory(root, authored):
    published = {page["page"] for page in authored}
    existing = {path.relative_to(root).with_suffix("").as_posix()
                for path in root.rglob("*.mdx")
                if not any(part.startswith(".") or part == "node_modules"
                           for part in path.relative_to(root).parts)}
    if existing - published:
        raise SystemExit(f"authored routes missing from navigation: {sorted(existing - published)}")


def github_json(url, opener=urlopen):
    request = Request(url, headers={"Accept": "application/vnd.github+json",
                      "User-Agent": USER_AGENT, "X-GitHub-Api-Version": "2022-11-28"})
    with opener(request, timeout=60) as response:
        return json.load(response)


def check_deployment(expected_sha, environment, base_url, get_json=github_json):
    if not re.fullmatch(r"[0-9a-f]{40}", expected_sha):
        raise SystemExit("--expected-sha must be a full lowercase Git SHA")
    url = "https://api.github.com/repos/RelayMessenger/Relay-Docs/deployments?" + urlencode(
        {"sha": expected_sha, "environment": environment, "per_page": 100})
    for candidate in get_json(url):
        # Do not trust server-side filtering alone, including mocked/API-cached lists.
        if candidate.get("sha") != expected_sha or candidate.get("environment") != environment:
            continue
        statuses = get_json(candidate["statuses_url"])
        # An older success must not mask a newer failure or inactive status.
        latest = max(statuses, key=lambda status: status.get("updated_at")
                     or status.get("created_at") or "", default={})
        if (latest.get("state") == "success"
                and latest.get("environment_url", "").rstrip("/") == base_url.rstrip("/")):
            return {"id": candidate["id"], "sha": candidate["sha"],
                    "ref": candidate.get("ref"), "environment": environment,
                    "status_id": latest.get("id"), "status": latest["state"],
                    "environment_url": latest["environment_url"],
                    "updated_at": latest.get("updated_at")}
    raise SystemExit(f"GitHub has no current successful {environment} deployment for {expected_sha} at {base_url}")


def run(args, root=ROOT, fetch=None, get_json=github_json):
    settings = environment_config(args.production)
    config = json.loads((root / "docs.json").read_text())
    if config.get("favicon") != "/" + settings["favicon"]:
        raise SystemExit(f"checkout favicon does not match {settings['environment']}; use the matching derived checkout")
    fetch = fetch or make_fetch(args.base_url)
    expected = {name: (root / name).read_bytes() for name in AGENT_SOURCES}
    pages, bodies = {}, {}
    for path, canonical, busted in hosted_source_pairs(fetch, expected, args.require_edge_fresh):
        text = busted["body"].decode("utf-8")
        for label, pattern in deleted_wording.items():
            if pattern.search(text):
                raise SystemExit(f"/{path} contains deleted wording: {label}")
        pages["/" + path] = response_pair(canonical, busted)
        bodies[path] = busted["body"]
    versions = [pages[path]["canonical"]["headers"].get("x-served-version")
                or pages[path]["canonical"]["headers"].get("x-version") for path in ("/", "/start/quickstart")]
    if not versions[0] or versions[0] != versions[1]:
        raise SystemExit("root and /start/quickstart are not served by the same Mintlify deployment")
    authored, contract_ids = check_discovery(root, config, bodies["llms.txt"].decode(), bodies["llms-full.txt"].decode())
    install_count = check_sdk_installs(bodies["llms-full.txt"].decode(), settings["environment"])
    brand = check_brand(fetch, bodies[""], root, settings)
    if args.all_pages:
        check_authored_inventory(root, authored)
        pages.update(check_all_pages(fetch, authored, args.workers))
    deployment = check_deployment(args.expected_sha, settings["environment"], args.base_url, get_json) if args.expected_sha else None
    return {"schema_version": 2, "checked_at": datetime.now(timezone.utc).isoformat(),
            "base_url": args.base_url.rstrip("/"), "environment": settings["environment"],
            "expected_sha": args.expected_sha, "mintlify_deployment_version": versions[0],
            "github_deployment": deployment, "brand": brand, "pages": pages,
            "authored_pages": len(authored), "contract_operation_ids": contract_ids,
            "sdk_install_commands": install_count, "all_pages": args.all_pages,
            "deleted_wording": list(deleted_wording), "verdict": "passed"}


def argument_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base_url")
    parser.add_argument("--production", action="store_true", help="Select production checks; source bytes remain exact")
    parser.add_argument("--require-edge-fresh", action="store_true", help="Also require canonical source bytes to match origin")
    parser.add_argument("--all-pages", action="store_true", help="Check every navigation-authored route and its Markdown")
    parser.add_argument("--workers", type=int, default=6, help="Concurrent page checks, 1–16 (default: 6)")
    parser.add_argument("--expected-sha")
    parser.add_argument("--receipt", type=Path)
    return parser


def main(argv=None):
    args = argument_parser().parse_args(argv)
    if not 1 <= args.workers <= 16:
        raise SystemExit("--workers must be between 1 and 16")
    receipt = run(args)
    if args.receipt:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(f"validated {receipt['environment']} hosted docs: exact origin and checkout bytes, "
          f"navigation, contract IDs, and {receipt['brand']['colors']} favicon colors")
    if args.all_pages:
        print(f"validated HTML and Markdown for {receipt['authored_pages']} authored pages")
    if args.receipt:
        print(f"receipt: {args.receipt}")


if __name__ == "__main__":
    main()
