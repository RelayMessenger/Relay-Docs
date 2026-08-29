# Relay Docs

Public developer documentation for Relay.

The site follows one information architecture:

```text
Getting started
Messaging
Chats
Webhooks and Socket Mode
Platform
Resources
API Reference
```

`api-reference/openapi.yaml` is byte-identical to the Relay Server contract.

## Validate

```bash
python3 scripts/sync-current-contract.py
scripts/check-openapi-sync.sh ../_worktrees/Relay-Server-local/contracts/developer/openapi.yaml
scripts/build-mint-openapi.sh
python3 scripts/validate-docs.py
npx --yes mint@latest broken-links
npx --yes mint@latest validate
```

## Preview

```bash
npx --yes mint@latest dev
```
