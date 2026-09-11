"""Reader-facing structure checks; API schemas remain the contract authority."""
import json
import re
from pathlib import Path

# Frame catalogs and a complete copyable agent instruction are reference, not
# onboarding. All ordinary task guides keep five sections before related links.
REFERENCE_PAGES = {"build/events/websocket/protocol", "connect/agent-prompt"}
LANDING_SECTIONS = ["Give the agent on your computer a phone number.", "What you need", "Connect your coding agent", "Message it from your phone", "Or build on the API", "Group chats and mentions", "Receive events", "Your agent’s identity", "Going live", "Next"]
START_PAGES = ["index", "start/quickstart", "start/key-concepts", "start/authentication", "start/sdks"]
INTERNAL_PROSE = re.compile(
    r"Prepare hosted proof|only after this docs candidate is pushed|"
    r"Local Docs validation prepares|Published artifact source commit|"
    r"registry integrity hash|Reviewed CLI source `[0-9a-f]+`", re.I
)


BUILD_FIXED = {"Before you start", "What you get back", "When it fails", "Next steps"}
TASK_VERBS = set("Add Allocate Apply Block Choose Clear Configure Connect Create Debug Delete Derive Download Edit Follow Handle Inspect Install Keep Leave List Mark Observe Open Preserve Read Receive Refresh Register Remove Rename Reply Resolve Retrieve Retry Review Run Save Select Send Set Share Start Stop Store Subscribe Supply Target Track Unblock Unsend Update Upload Use Validate Verify Watch".split())

def validate_build_headings(page, body):
    headings = re.findall(r"^## (.+)$", body, re.M)
    if not headings or headings[-1] != "Next steps":
        raise SystemExit(f"{page}: Next steps must be last")
    for heading in headings:
        if heading not in BUILD_FIXED and heading.split()[0] not in TASK_VERBS:
            raise SystemExit(f"{page}: guide heading must name an imperative task: {heading}")
    if "What you get back" in headings and "When it fails" not in headings:
        raise SystemExit(f"{page}: response requires When it fails")
    if "When it fails" in headings and headings[-2] != "When it fails":
        raise SystemExit(f"{page}: When it fails must precede Next steps")


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
        if page == "index" and re.findall(r"^## (.+)$", body, re.M) != LANDING_SECTIONS:
            raise SystemExit("index: landing sections must match the approved order")
        if page.startswith("build/"):
            validate_build_headings(page, body)
        if not page.startswith("build/") and page not in REFERENCE_PAGES and page not in {"changelog", "index"} and len(sections) > 8:
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
