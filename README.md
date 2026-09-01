# Relay Docs

Public developer documentation for Relay.

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
  Developer ecosystem
  Examples
Error Codes
API Reference
```

`api-reference/openapi.yaml` is copied byte-for-byte from the Relay Server contract.

## Validate

```bash
scripts/check-openapi-sync.sh ../_worktrees/Relay-Server-local/contracts/developer/openapi.yaml
scripts/build-mint-openapi.sh
npm run validate
```

The validation sequence checks contract synchronization, rebuilds the Mintlify
OpenAPI bundle, validates examples, checks links, validates the site, and runs
Mintlify accessibility checks.

Mintlify hosted previews generate `llms.txt`, `llms-full.txt`, and page
Markdown. Validate those generated files with:

```bash
npm run validate:hosted-llms -- https://<mintlify-preview-url>
```

## Preview

```bash
npm run dev
```

## Staging preview

`.github/workflows/preview.yml` validates a pull request or the selected
`staging` branch, then creates a Mintlify preview deployment.

Configure these GitHub values:

| Name | Kind | Purpose |
| --- | --- | --- |
| `MINTLIFY_API_KEY` | Environment secret in `docs-preview` | Mintlify admin API authentication |
| `MINTLIFY_PROJECT_ID` | Repository variable | Relay Docs deployment identifier |

The workflow waits for the deployment, then validates the generated
`llms.txt` and `llms-full.txt`. The Mintlify GitHub App supplies the selected
repository branch. Preview authentication is configured in Mintlify.

Use `workflow_dispatch` with `branch=staging` to rebuild the hosted staging
preview.
