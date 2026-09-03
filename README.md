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
OpenAPI bundle, checks every published package version against `versions.json`,
validates examples, checks links, validates the site, and runs Mintlify
accessibility checks.

## Package versions

`versions.json` is the one source of truth for every published package version,
registry integrity, and published source commit. Refresh it, and every page that
states one, from the live registries:

```bash
npm run refresh:versions
```

`npm run validate` fails when a page states a version `versions.json` does not
carry, or states one with no package name beside it.

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

`.github/workflows/preview.yml` validates every push to `staging`, every pull
request, and any branch chosen by a manual run, then creates a Mintlify preview
deployment.

Configure these GitHub values:

| Name | Kind | Purpose |
| --- | --- | --- |
| `MINTLIFY_API_KEY` | Environment secret in `docs-preview` | Mintlify admin API authentication |
| `MINTLIFY_PROJECT_ID` | Repository variable | Relay Docs deployment identifier |

The workflow waits for the deployment, then validates the generated
`llms.txt` and `llms-full.txt`. The Mintlify GitHub App supplies the selected
repository branch. Preview authentication is configured in Mintlify.

Every merge into `staging` rebuilds the hosted staging preview on its own. Use
`workflow_dispatch` with `branch=staging` only to rebuild it without a new
commit.
