# Relay docs

Minimal developer documentation for Relay dev.

`api-reference/openapi.yaml` must be a byte-identical copy of the canonical
Relay Server developer contract.

```bash
scripts/check-openapi-sync.sh /path/to/contracts/developer/openapi.yaml
scripts/build-mint-openapi.sh
python3 -m json.tool docs.json > /dev/null
python3 scripts/validate-docs.py
npx --yes @redocly/cli@latest lint api-reference/openapi.yaml
npx --yes mint@4.2.831 broken-links
npx --yes mint@4.2.831 validate
```

Preview with `npx --yes mint@4.2.831 dev` at `http://localhost:3000`. Mintlify publishes from `main`; `dev` remains local until separately merged.
