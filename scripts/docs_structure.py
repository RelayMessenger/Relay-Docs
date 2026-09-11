"""Reader-facing structure checks; API schemas remain the contract authority."""
import json
import re
from pathlib import Path

# Frame catalogs and a complete copyable agent instruction are reference, not
# onboarding. All ordinary task guides keep five sections before related links.
REFERENCE_PAGES = {"build/events/websocket/protocol", "connect/agent-prompt"}
START_PAGES = ["index", "start/quickstart", "start/key-concepts", "start/authentication", "start/sdks"]
INTERNAL_PROSE = re.compile(
    r"Prepare hosted proof|only after this docs candidate is pushed|"
    r"Local Docs validation prepares|Published artifact source commit|"
    r"registry integrity hash|Reviewed CLI source `[0-9a-f]+`", re.I
)


def prose(text):
    return re.sub(r"^(`{3,})[^\n]*\n.*?^\1\s*$", "", text, flags=re.M | re.S)


def authored_paths(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "pages":
                for page in item:
                    if isinstance(page, str) and not re.match(r"^(GET|POST|PUT|PATCH|DELETE) /", page):
                        yield page
            yield from authored_paths(item)
    elif isinstance(value, list):
        for item in value:
            yield from authored_paths(item)


def validate_structure(root: Path, config: dict):
    groups = config["navigation"]["tabs"][0]["groups"]
    start = next((group for group in groups if group.get("group") == "Getting started"), None)
    if start is None or start.get("pages") != START_PAGES:
        raise SystemExit("Getting started must stay focused on quickstart, authentication, and SDK installation")
    pages = list(authored_paths(config["navigation"]))
    existing = {str(p.relative_to(root).with_suffix("")) for p in root.rglob("*.mdx") if "node_modules" not in p.parts}
    if len(pages) != len(set(pages)) or set(pages) != existing:
        raise SystemExit("Every authored page needs exactly one navigation owner")
    for page in pages:
        text = (root / f"{page}.mdx").read_text()
        body = prose(text)
        sections = [h for h in re.findall(r"^## (.+)$", body, re.M) if h not in {"Next steps", "Related", "See also"}]
        if page not in REFERENCE_PAGES and len(sections) > 8:
            raise SystemExit(f"{page}: {len(sections)} top-level sections; split independent tasks rather than expanding this page")
        if page != "connect/agent-prompt" and INTERNAL_PROSE.search(body):
            raise SystemExit(f"{page}: internal publishing instructions do not belong in a reader task")
        if page != "connect/agent-prompt" and "````text Relay agent prompt" in text:
            raise SystemExit(f"{page}: full machine instructions belong in the agent reference")
        if page == "start/quickstart":
            for detail in ("onFullSync", "through_sequence", "## Review with an agent", "## Delete", "image_recipe"):
                if detail in text:
                    raise SystemExit(f"Quickstart absorbed a separate task: {detail}")
            if len(text.split()) > 600:
                raise SystemExit("Quickstart must fit a short first-run task, including examples and tables")
    return len(pages)
