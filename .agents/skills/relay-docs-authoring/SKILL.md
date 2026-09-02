---
name: relay-docs-authoring
description: Write, simplify, review, and reorganize Relay Messenger's Mintlify documentation while preserving the current Relay API contract.
---

# Relay Messenger docs authoring

Write for a developer who wants one agent reply working now.

## Source order

1. Read `AGENTS.md`.
2. Read the affected Relay page and `docs.json`.
3. Read `api-reference/openapi.yaml` for wire behavior.
4. Read current owning product code or a verified release receipt for status.
5. Load only the reference-style skills needed for the page.

External docs teach structure. They never prove Relay behavior.

## Site hierarchy

Keep the three top-level tabs in this order:

1. Guides
2. Error Codes
3. API Reference

Within Guides, use the current `docs.json` order: Introduction, Getting
started, Messaging, Chats, Contacts, Webhooks, WebSocket, Platform, and
Examples.

Keep pages at three navigation levels or fewer. Add a category only when a
current, source-backed page requires it.

## Page templates

### Task guide

1. Outcome sentence.
2. Prerequisites.
3. First runnable request.
4. Real response.
5. Remaining steps.
6. Failure and retry behavior.
7. Next steps.

### Concept

1. Definition.
2. Ownership boundary.
3. Smallest object or flow.
4. Lifecycle and invariants.
5. See also.

### Reference

1. Canonical shape.
2. Field, state, error, and limit tables.
3. See also.

## Plain-English limits

- Use one idea per sentence.
- Aim for 18 words per prose sentence.
- Rewrite prose sentences above 30 words.
- Keep paragraphs to three sentences.
- Put fields, states, limits, errors, and comparisons in tables.
- Keep task-guide prose near 700 words or less.
- Put long complete handlers in an accordion or dedicated example.
- Use at most five top-level sections before Next steps.

Code, JSON, tables, and exact error text do not count toward prose limits.

## Writing rules

- Lead with the action or fact.
- Prefer common verbs: send, receive, save, retry, stop, open.
- Define a Relay noun once, then use it consistently.
- Show the TypeScript SDK and equivalent raw HTTPS side by side, with the SDK
  first.
- State what success proves.
- State what a retry can duplicate and how the key prevents it.
- Keep Relay as the messenger and the external backend as the agent brain.
- Mark unshipped behavior as coming soon.

## Review

1. Remove duplicated setup and product framing.
2. Move full schemas to OpenAPI.
3. Move optional detail below the main path.
4. Check every linked page exists in `docs.json`.
5. Run `mint broken-links` and `mint validate`.
6. Preview the changed route and inspect the full viewport.

## Reference skills

- `$docs-linq-style`: messaging object hierarchy and shared vocabulary.
- `$docs-photon-style`: compact feature maps and exact send semantics.
- `$docs-openclaw-style`: complex integration and troubleshooting structure.
- `$docs-hermes-style`: command-first setup, messaging gateways, and repair.
- `$docs-stripe-style`: task routing and resource reference.
- `$docs-twilio-style`: complete communications tutorials.
- `$docs-vercel-ai-sdk-style`: streams and typed framework examples.
- `$docs-telegram-style`: compact events and method reference.
