#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"
python3 scripts/build-staging-openapi.py
npx --yes @redocly/cli@latest bundle api-reference/openapi.staging.yaml --output api-reference/openapi.mint.yaml
node scripts/prepare-mint-openapi.mjs
echo "Mintlify OpenAPI bundle rebuilt"
