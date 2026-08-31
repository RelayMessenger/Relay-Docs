#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
BEFORE=$(mktemp)
trap 'rm -f "$BEFORE"' EXIT

cd "$ROOT"
cp api-reference/openapi.mint.yaml "$BEFORE"
scripts/build-mint-openapi.sh

if ! cmp -s "$BEFORE" api-reference/openapi.mint.yaml; then
  diff -u "$BEFORE" api-reference/openapi.mint.yaml || true
  echo "api-reference/openapi.mint.yaml is stale" >&2
  exit 1
fi

echo "Mintlify OpenAPI bundle is reproducible"
