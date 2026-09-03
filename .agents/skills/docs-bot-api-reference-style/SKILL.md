---
name: docs-bot-api-reference-style
description: Apply bot-platform API reference patterns to compact event, method, object, and polling reference pages. Use when Relay needs precise field tables, stable update names, or a simple create-token-then-choose-transport model. Do not copy a giant single-page reference.
---

# Bot platform API reference style

Use this pattern for a simple bot identity and transport model.

## Structure

1. Create the bot identity and token.
2. Choose long polling or webhooks.
3. Define updates as stable typed objects.
4. Define methods with parameters and return values.
5. Keep optional fields explicit.

## What to adapt

- One token represents one bot identity.
- Polling and webhooks are alternative receive paths.
- Method names begin with actions.
- Object pages list fields in tables.
- Event and method names stay stable and literal.

## What to avoid

- These references usually put the whole API on one very large page.
- Do not put Relay’s full event and endpoint catalogue on one page.
- Do not copy a chat, update, or file lifecycle that Relay does not have.
- Do not treat omitted fields as obvious.

## Verify

- Each object has one canonical field table.
- Each method names required inputs and its return.
- The receive-path choice appears once and links to deeper guides.
- Relay-specific privacy and access rules remain explicit.
