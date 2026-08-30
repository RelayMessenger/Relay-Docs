# Relay Messenger Docs

Public developer documentation for Relay Messenger.

The site has three top-level tabs:

```text
Guides
  Introduction
  Getting started
  Messaging
  Chats
  Contacts
  Agent events
  Webhooks
  WebSocket
  Platform
  Examples
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

Mintlify generates `llms.txt`, `llms-full.txt`, and page Markdown during a
hosted deployment. The local preview does not serve these generated files.
Validate them on a Mintlify preview:

```bash
npm run validate:hosted-llms -- https://<mintlify-preview-url>
```

## Preview

```bash
npm run dev
```

## Staging preview

`.github/workflows/preview.yml` validates an internal pull-request branch,
then calls Mintlify's preview-only API. It never calls the production
deployment endpoint.

Configure these GitHub values:

| Name | Kind | Purpose |
| --- | --- | --- |
| `MINTLIFY_API_KEY` | Environment secret in `docs-preview` | Mintlify admin API authentication |
| `MINTLIFY_PROJECT_ID` | Repository variable | Relay Docs deployment identifier |

The workflow waits for the deployment, then validates the generated
`llms.txt` and `llms-full.txt`. The Mintlify GitHub App must be installed, and
the branch must exist in the connected repository. Preview authentication is
configured in Mintlify because the preview API creates a public URL by default.

Use `workflow_dispatch` to rebuild a long-running `dev` preview without
merging it into `main`.
