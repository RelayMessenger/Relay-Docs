#!/usr/bin/env python3
import json
import re
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


navigated = set(pages(config.get("navigation", {})))
files = {
    str(path.relative_to(root).with_suffix(""))
    for path in root.rglob("*.mdx")
}
if navigated != files:
    raise SystemExit(f"navigation/orphan mismatch: {sorted(navigated ^ files)}")

expected_groups = [
    "Getting started",
    "Messaging",
    "Chats",
    "Webhooks and Socket Mode",
    "Platform",
    "Resources",
]
documentation = config["navigation"]["tabs"][0]
actual_groups = [group["group"] for group in documentation["groups"]]
if actual_groups != expected_groups:
    raise SystemExit(f"documentation group order changed: {actual_groups}")
if "icons" in config or any("icon" in tab for tab in config["navigation"]["tabs"]):
    raise SystemExit("decorative navigation icons returned")
if (root / "current-status.mdx").exists():
    raise SystemExit("Current status belongs in the evidence site, not public docs")

for path in sorted(root.rglob("*.mdx")):
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

text = "\n".join(path.read_text() for path in [*root.rglob("*.mdx"), root / "skill.md"])
for name, pattern in {
    "old URL namespace": r"/api/(?:partner|mobile)|api\.relayapp\.im/api/",
    "old route version": r"/v[23]/",
    "wire service field": r"[\"']service[\"']\s*:|\bservice\s*:\s*[\"']?Relay",
    "old public status language": r"current-status|Current status|known contract residue|local proof|evidence app",
    "source-company language": r"\bLinq\b",
    "mobile realtime endpoint": r"/v1/realtime|/v1/client/realtime|/v1/chats/\{chatId\}/typing",
    "prefixed ID": r"\b(?:msg|agt|usr|cnv|prt|att|evt|wh)_[A-Za-z0-9]",
    "uuidv4 example": r"\b[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b",
    "human identity kind": r"\bkind\b.{0,30}\bhumans?\b|\bhumans?\b.{0,30}\bkind\b",
    "message parts table": r"\bmessage_parts?\b",
    "unsupported payments": r"\bpayments?\b",
    "unsupported edits": r"\b(?:edited|editing|edits?)\b",
    "unsupported unsend": r"\bunsend\b",
    "long polling": r"long[ -]poll",
}.items():
    if re.search(pattern, text, re.I):
        raise SystemExit(f"stale {name}")

print(
    f"validated {len(files)} public pages, exact navigation, frontmatter, "
    "prose, and stale-contract bans"
)
