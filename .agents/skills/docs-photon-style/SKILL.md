---
name: docs-photon-style
description: Apply Photon’s current README-led SDK documentation patterns to messaging integration pages. Use when a Relay guide needs a compact feature map, fast install path, exact send-versus-observe semantics, or examples beside each capability. Do not treat Photon APIs as Relay APIs.
---

# Photon documentation style

Use Photon for compact SDK explanation and precise runtime boundaries.

## Structure

1. Name the package and its one job.
2. Give a feature table with method and example links.
3. Show install, basic usage, and required permissions.
4. Define identifiers before advanced operations.
5. Group the rest by resource: messages, attachments, chats, contacts, and events.
6. Link every feature to a runnable example file.

## Writing pattern

- Start sections with the action: “Send messages,” “Upload attachments.”
- Put the normal call first.
- Follow it with one important variant.
- State exact return semantics.
- State what a successful call does not prove.
- Put supported formats and bounds in tables or short lists.

Photon is strongest when it says that a send result confirms one local action,
not final delivery. Preserve that precision in Relay receipt documentation.

## What to adapt

- Feature, method, example tables.
- One-screen quick starts.
- Exact identifier examples.
- Concrete lifecycle and teardown guidance.
- Clear distinctions between local files and server-hosted objects.

## What to avoid

- Photon’s canonical material is split across repositories and long READMEs.
- Do not copy its package-centric hierarchy into Relay’s HTTP API.
- Do not imply that open-source iMessage behavior proves Relay production state.

## Verify

- Each capability links to one runnable example or request.
- Success language names the exact confirmed state.
- Permission and platform requirements appear before the first failing step.
- The page stays useful without reading a source repository.

## Sources

- https://photon.codes
- https://github.com/photon-hq/imessage-kit
- https://github.com/photon-hq/advanced-imessage
- `@photon-ai/imessage-kit` and `@photon-ai/advanced-imessage` README files

Sources checked on 2026-08-10.
