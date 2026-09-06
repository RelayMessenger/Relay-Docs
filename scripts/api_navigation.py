"""Nested API navigation with stable public endpoint-page URLs."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


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
    api = next(tab for tab in config["navigation"]["tabs"] if tab["tab"] == "API Reference")
    groups = api["groups"]
    if len(groups) != 1 or groups[0]["group"] != "HTTP":
        raise ValueError("API resources must be nested under HTTP")
    entries = list(walk_pages(groups))
    methods = ("GET ", "POST ", "PUT ", "PATCH ", "DELETE ")
    endpoints = [(parents, page) for parents, page in entries if page.startswith(methods)]
    expected = {entry["endpoint"]: entry for entry in page_paths().values()}
    found = [page for _, page in endpoints]
    if len(found) != len(set(found)) or set(found) != set(expected):
        raise ValueError("API navigation must contain every endpoint exactly once")
    for parents, page in endpoints:
        if parents != ("HTTP", *expected[page]["group"]):
            raise ValueError(f"Incorrect resource nesting for {page}: {parents}")
    hrefs = [entry["href"] for entry in expected.values()]
    if len(set(hrefs)) != len(hrefs) or any(not href.startswith("/api-reference/") for href in hrefs):
        raise ValueError("Endpoint page URLs must be unique API reference paths")

    def check_overviews(items):
        for item in items:
            if not isinstance(item, dict):
                continue
            pages = item["pages"]
            if item["group"] != "HTTP":
                if not pages or not isinstance(pages[0], str) or not pages[0].endswith("/overview"):
                    raise ValueError(f"{item['group']} must start with its overview")
                if item.get("expanded") is not False:
                    raise ValueError(f"{item['group']} must collapse when inactive")
            check_overviews(pages)

    check_overviews(groups)
    return found
