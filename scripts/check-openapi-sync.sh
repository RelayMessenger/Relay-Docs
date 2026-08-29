#!/bin/sh
set -eu
R=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
S=${1:-${RELAY_OPENAPI_SOURCE:-"$R/../Relay-Server/contracts/developer/openapi.yaml"}}
[ -f "$S" ] || { echo "missing canonical OpenAPI: $S" >&2; exit 2; }
cmp -s "$S" "$R/api-reference/openapi.yaml" || { diff -u "$S" "$R/api-reference/openapi.yaml" || true; exit 1; }
echo "OpenAPI is byte-identical: $S"
