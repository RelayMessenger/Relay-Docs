---
name: docs-linq-style
description: Apply the current Linq Partner API documentation patterns to messaging API guides. Use when a Relay page needs a clearer onboarding path, shared vocabulary, runnable multi-language examples, or concise messaging concepts. Do not use Linq as proof of Relay behavior.
---

# Linq documentation style

Use Linq for information structure, not wording or product claims.

## Structure

1. Lead with the result, such as “Send your first message.”
2. Put prerequisites before setup.
3. Keep one shared concepts page for handles, chats, messages, parts, webhooks, idempotency, and limits.
4. Organize guides by product object: chats, messaging, webhooks, phone numbers, and platform.
5. Keep generated endpoint reference separate from task guides.
6. Give each error a stable code, cause, fix, and retry rule.

## Page pattern

1. State the task in one sentence.
2. Show the smallest runnable request.
3. Show the real response.
4. Explain only the fields needed for the task.
5. Put language variants in tabs.
6. End with specific next pages.

Keep prose direct. Prefer “Send the same key on a retry” to a general
idempotency essay.

## What to adapt

- Use examples to carry mechanics.
- Define one noun once, then link back to it.
- Put limits near the object they constrain.
- State automatic behavior before optional overrides.
- Use tables for services, states, fields, errors, and limits.

## What to avoid

- Linq’s quickstart was about 1,760 words on 2026-08-10. Do not copy that size.
- Do not lead Relay readers through optional plugins before the first API call.
- Do not copy Linq’s carrier, line-selection, SDK, or account model.

## Verify

- The first runnable request appears before deep architecture.
- A new reader can name the main objects after one page.
- Every failure path says whether to retry.
- Relay claims still match its OpenAPI contract.

## Sources

- https://docs.linqapp.com/llms.txt
- https://docs.linqapp.com/getting-started/quickstart/index.md
- https://docs.linqapp.com/getting-started/key-concepts/index.md
- https://docs.linqapp.com/guides/messaging/sending-messages/index.md
- https://docs.linqapp.com/guides/webhooks/index.md
- https://cdn.linqapp.com/openapi/linq-api-v3.yaml

Sources checked on 2026-08-10.
