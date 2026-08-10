---
name: relay-docs-authoring
description: Write, simplify, review, and reorganize Relay’s Mintlify documentation. Use for any Relay docs page, navigation, quickstart, concept, integration, status, OpenAPI, or machine-readable docs change. Combines the strongest Linq, Photon, OpenClaw, Hermes, Stripe, Twilio, Vercel AI SDK, and Telegram patterns while preserving Relay’s real contract.
---

# Relay docs authoring

Write for a developer who wants one agent reply working now.

## Source order

1. Read `AGENTS.md`.
2. Read the affected Relay page and `docs.json`.
3. Read `api-reference/openapi.yaml` for wire behavior.
4. Read current owning product code or a verified release receipt for status.
5. Load only the reference-style skills needed for the page.

External docs teach structure. They never prove Relay behavior.

## Site hierarchy

Use this reader path:

1. Start: home, quickstart, core concepts, agent creation, authentication.
2. Build: messages, media, groups, streams.
3. Receive: webhooks, delivery, history, receipts.
4. Connect: runtime integrations.
5. Reference: API, events, errors, limits, data, status.
6. About: product explanation and comparisons.

Keep pages at three navigation levels or fewer.

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
- Show raw HTTPS and JSON before integrations.
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
