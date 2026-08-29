#!/usr/bin/env python3
import hashlib
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OPENAPI_SOURCE = Path(os.environ.get(
    "RELAY_OPENAPI_SOURCE",
    ROOT / "../_worktrees/Relay-Server-local/contracts/developer/openapi.yaml",
)).resolve()
TARGET = ROOT / "api-reference/openapi.yaml"

if not OPENAPI_SOURCE.is_file():
    raise SystemExit(f"Relay OpenAPI source not found: {OPENAPI_SOURCE}")

TARGET.write_bytes(OPENAPI_SOURCE.read_bytes())
sha = hashlib.sha256(TARGET.read_bytes()).hexdigest()
print(f"synced Relay OpenAPI {sha[:12]}…")
