#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"
npx --yes @redocly/cli@latest bundle api-reference/openapi.yaml --output api-reference/openapi.mint.yaml
echo "Mintlify OpenAPI bundle rebuilt"
