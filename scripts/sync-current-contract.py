#!/usr/bin/env python3
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OPENAPI_SOURCE = Path(os.environ.get(
    "RELAY_OPENAPI_SOURCE",
    ROOT / "../_worktrees/Relay-Server-local/contracts/developer/openapi.yaml",
)).resolve()
MIGRATION_SOURCE = Path(os.environ.get(
    "RELAY_MIGRATION_SOURCE",
    ROOT / "../_worktrees/Relay-Server-local/server/migrations/0001_relay.sql",
)).resolve()
TRUTH_SOURCE = Path(os.environ.get(
    "RELAY_CURRENT_TRUTH",
    ROOT / "../Relay-Research/research/relay-rebuild-20260828/demo-site/notes/data/38-current-truth.json",
)).resolve()

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

truth = json.loads(TRUTH_SOURCE.read_text())
openapi_sha = sha256(OPENAPI_SOURCE)
migration_sha = sha256(MIGRATION_SOURCE)
if truth["openapi"]["sha256"] != openapi_sha:
    raise SystemExit("Research current-truth OpenAPI hash is stale; regenerate evidence first")
if truth["postgresql"]["sha256"] != migration_sha:
    raise SystemExit("Research current-truth migration hash is stale; regenerate evidence first")

(ROOT / "api-reference/openapi.yaml").write_bytes(OPENAPI_SOURCE.read_bytes())

o = truth["openapi"]
p = truth["postgresql"]
generated = f"""{{/* GENERATED:CURRENT_CONTRACT:START */}}
## Contract evidence

| | Surface | Current evidence |
| :---: | --- | --- |
| ⚠️ | OpenAPI | {o["path_count"]} path keys, {o["reachable_schemas"]} reachable schemas, and {o["webhook_callbacks"]} current webhook callbacks, all under `/v1`; SHA-256 `{o["sha256"]}` |
| ⚠️ | PostgreSQL | {p["tables"]} tables, {p["columns"]} columns, {p["declared_foreign_keys"]} declared foreign keys, {p["indexes"]} indexes, {p["triggers"]} triggers; SHA-256 `{p["sha256"]}` |
| ⚠️ | Namespace | One `/v1` API with no business-role or client-role URL namespace |
| ⚠️ | Agent events | Signed webhooks or agent-only Socket Mode; no polling |

`api-reference/openapi.yaml` is byte-identical to the current local Server contract. Mintlify reads a generated endpoint bundle from that source.
{{/* GENERATED:CURRENT_CONTRACT:END */}}"""

status_path = ROOT / "current-status.mdx"
status = status_path.read_text()
start = "{/* GENERATED:CURRENT_CONTRACT:START */}"
end = "{/* GENERATED:CURRENT_CONTRACT:END */}"
if start not in status or end not in status:
    raise SystemExit("current-status.mdx is missing generated contract markers")
before, remainder = status.split(start, 1)
_, after = remainder.split(end, 1)
status_path.write_text(before + generated + after)

print(
    f"synced Docs: {o['path_count']} paths, {o['reachable_schemas']} schemas, "
    f"{o['webhook_callbacks']} callbacks; OpenAPI {openapi_sha[:10]}…; "
    f"migration {migration_sha[:10]}…"
)
