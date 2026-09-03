---
name: docs-partner-api-style
description: Apply the documentation patterns of a mature partner messaging API to Relay API guides. Use when a Relay page needs a clearer onboarding path, shared vocabulary, runnable multi-language examples, or concise messaging concepts. Another API's behavior never proves Relay behavior.
---

# Partner messaging API documentation style

Use this pattern for information structure, not wording or product claims.

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

- A partner-API quickstart of about 1,760 words is too long for Relay. Do not copy that size.
- Do not lead Relay readers through optional plugins before the first API call.
- Do not copy a carrier, line-selection, SDK, or account model that Relay does not have.

## Verify

- The first runnable request appears before deep architecture.
- A new reader can name the main objects after one page.
- Every failure path says whether to retry.
- Relay claims still match its OpenAPI contract.
