#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
TMPDIR_WORK=$(mktemp -d)
trap 'rm -rf "$TMPDIR_WORK"' EXIT
PROJECTED="$TMPDIR_WORK/openapi.yaml"
cd "$ROOT"
python3 -c 'import sys; from pathlib import Path; sys.path.insert(0, "scripts"); from origins import project_openapi; Path(sys.argv[1]).write_text(project_openapi(Path("api-reference/openapi.yaml").read_text()))' "$PROJECTED"
npx --yes @redocly/cli@latest bundle "$PROJECTED" --output api-reference/openapi.mint.yaml
node scripts/prepare-mint-openapi.mjs
echo "Mintlify OpenAPI bundle rebuilt"
