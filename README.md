# Relay Docs

Public developer documentation for Relay.

The site has three top-level tabs:

```text
Guides
  Getting started
  Messaging
  Chats
  Contact Cards
  Webhooks
  WebSocket
  Platform
  Resources
Error Codes
API Reference
```

`api-reference/openapi.yaml` is copied byte-for-byte from the Relay Server contract.

## Validate

```bash
python3 scripts/sync-current-contract.py
scripts/check-openapi-sync.sh ../_worktrees/Relay-Server-local/contracts/developer/openapi.yaml
scripts/build-mint-openapi.sh
npm run validate
```

## Preview

```bash
npm run dev
```
