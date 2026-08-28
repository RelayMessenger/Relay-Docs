# Relay docs

Minimal developer documentation for Relay dev.

`api-reference/openapi.yaml` must equal `../Relay-Server/contracts/developer/openapi.yaml`.

```bash
scripts/check-openapi-sync.sh
scripts/build-mint-openapi.sh
python3 -m json.tool docs.json > /dev/null
python3 scripts/validate-docs.py
npx --yes @redocly/cli@latest lint api-reference/openapi.yaml
npx --yes mint@4.2.831 broken-links
npx --yes mint@4.2.831 validate
```

Preview with `npx --yes mint@4.2.831 dev` at `http://localhost:3000`. Mintlify publishes from `main`; `dev` remains local until separately merged.
