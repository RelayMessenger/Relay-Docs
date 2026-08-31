#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://docs.staging.relayapp.im"
ENDPOINT = re.compile(
    r"^(GET|POST|PUT|PATCH|DELETE) (/v1/[^\s]+)$"
)


def frontmatter(path: Path) -> tuple[str, str, str]:
    text = path.read_text()
    if not text.startswith("---\n"):
        raise SystemExit(f"frontmatter missing: {path.relative_to(ROOT)}")
    try:
        raw, body = text[4:].split("\n---\n", 1)
    except ValueError as error:
        raise SystemExit(
            f"frontmatter is not closed: {path.relative_to(ROOT)}"
        ) from error

    def field(name: str) -> str:
        match = re.search(rf"^{name}:\s*(.+)$", raw, re.M)
        if not match:
            raise SystemExit(
                f"{name} missing from {path.relative_to(ROOT)}"
            )
        value = match.group(1).strip()
        if value.startswith('"'):
            return json.loads(value)
        return value

    return field("title"), field("description"), body.strip()


def navigation_entries(config: dict) -> list[tuple[str, str, str]]:
    entries = []
    for tab in config["navigation"]["tabs"]:
        for group in tab["groups"]:
            for page in group["pages"]:
                entries.append((tab["tab"], group["group"], page))
    return entries


def scalar(raw: str, continuation: list[str]) -> str:
    value = raw.strip()
    folded = value in {">", ">-", ">+", "|", "|-", "|+"}
    parts = [line.strip() for line in continuation if line.strip()]
    if folded:
        value = " ".join(parts)
    elif parts:
        value = " ".join([value, *parts])

    if value.startswith('"') and value.endswith('"'):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value[1:-1]
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1].replace("''", "'")
    return value


def operation_field(block: str, name: str) -> str:
    lines = block.splitlines()
    prefix = f"      {name}:"
    for index, line in enumerate(lines):
        if not line.startswith(prefix):
            continue
        raw = line[len(prefix):].lstrip()
        continuation = []
        for following in lines[index + 1:]:
            if following.strip() and len(following) - len(
                following.lstrip()
            ) <= 6:
                break
            continuation.append(following)
        return scalar(raw, continuation)
    raise SystemExit(f"OpenAPI operation is missing {name}")


def openapi_operations(text: str) -> dict[str, dict[str, str]]:
    paths_text = text.split("\ncomponents:", 1)[0]
    path_matches = list(
        re.finditer(r"^  (/v1/[^:]+):$", paths_text, re.M)
    )
    operations = {}
    for path_index, path_match in enumerate(path_matches):
        path = path_match.group(1)
        path_end = (
            path_matches[path_index + 1].start()
            if path_index + 1 < len(path_matches)
            else len(paths_text)
        )
        path_block = paths_text[path_match.end():path_end]
        method_matches = list(
            re.finditer(
                r"^    (get|post|put|patch|delete):$",
                path_block,
                re.M,
            )
        )
        for method_index, method_match in enumerate(method_matches):
            method_end = (
                method_matches[method_index + 1].start()
                if method_index + 1 < len(method_matches)
                else len(path_block)
            )
            block = path_block[method_match.end():method_end]
            endpoint = f"{method_match.group(1).upper()} {path}"
            operations[endpoint] = {
                "summary": operation_field(block, "summary"),
                "description": operation_field(block, "description"),
            }
    return operations


def slug(value: str) -> str:
    normalized = value.lower().replace("’", "").replace("'", "")
    return re.sub(r"(^-|-$)", "", re.sub(r"[^a-z0-9]+", "-", normalized))


def authored_page(page: str) -> tuple[Path, str, str, str]:
    path = ROOT / f"{page}.mdx"
    if not path.is_file():
        raise SystemExit(f"authored page missing: {path.relative_to(ROOT)}")
    title, description, body = frontmatter(path)
    return path, title, description, body


def render_index(
    config: dict,
    entries: list[tuple[str, str, str]],
    operations: dict[str, dict[str, str]],
) -> str:
    lines = [
        f"# {config['name']}",
        "",
        f"> {config['description']}",
        "",
    ]
    for _, group, page in entries:
        endpoint_match = ENDPOINT.fullmatch(page)
        if endpoint_match:
            operation = operations.get(page)
            if operation is None:
                raise SystemExit(f"navigation endpoint missing from OpenAPI: {page}")
            path = (
                f"api-reference/{slug(group)}/"
                f"{slug(operation['summary'])}.md"
            )
            title = operation["summary"]
            description = operation["description"]
        else:
            _, title, description, _ = authored_page(page)
            path = f"{page}.md"
        lines.append(
            f"- [{title}]({BASE_URL}/{path}): {description}"
        )
    lines.extend(
        [
            "",
            "## OpenAPI specs",
            "",
            "- [Canonical OpenAPI](/api-reference/openapi.yaml)",
            "- [Mintlify OpenAPI](/api-reference/openapi.mint.yaml)",
            "",
        ]
    )
    return "\n".join(lines)


def render_full(
    config: dict,
    entries: list[tuple[str, str, str]],
    openapi_text: str,
) -> str:
    sections = [f"# {config['name']}"]
    seen = set()
    for _, _, page in entries:
        if ENDPOINT.fullmatch(page) or page in seen:
            continue
        seen.add(page)
        _, title, description, body = authored_page(page)
        sections.append(
            "\n".join(
                [
                    f"# {title}",
                    "",
                    f"> {description}",
                    "",
                    f"Source: {BASE_URL}/{page}.md",
                    "",
                    body,
                ]
            )
        )

    sections.append(
        "\n".join(
            [
                "# Relay API OpenAPI",
                "",
                "> Exact Relay API v1 paths, fields, limits, and errors.",
                "",
                f"Source: {BASE_URL}/api-reference/openapi.yaml",
                "",
                "````yaml api-reference/openapi.yaml",
                openapi_text.rstrip(),
                "````",
            ]
        )
    )
    return "\n\n".join(sections) + "\n"


def check_or_write(path: Path, expected: str, check: bool) -> None:
    if check:
        if not path.is_file() or path.read_text() != expected:
            raise SystemExit(
                f"{path.name} is stale; run npm run build:llms"
            )
        return
    path.write_text(expected)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    config = json.loads((ROOT / "docs.json").read_text())
    entries = navigation_entries(config)
    openapi_text = (ROOT / "api-reference/openapi.yaml").read_text()
    operations = openapi_operations(openapi_text)

    configured_endpoints = {
        page for _, _, page in entries if ENDPOINT.fullmatch(page)
    }
    if configured_endpoints != set(operations):
        raise SystemExit(
            "navigation and OpenAPI endpoints differ: "
            f"{sorted(configured_endpoints ^ set(operations))}"
        )

    index = render_index(config, entries, operations)
    complete = render_full(config, entries, openapi_text)
    check_or_write(ROOT / "llms.txt", index, args.check)
    check_or_write(ROOT / "llms-full.txt", complete, args.check)

    verb = "Verified" if args.check else "Built"
    print(
        f"{verb} llms.txt and llms-full.txt from "
        f"{len(entries) - len(configured_endpoints)} authored pages and "
        f"{len(configured_endpoints)} OpenAPI operations"
    )


if __name__ == "__main__":
    main()
