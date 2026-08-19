---
name: docs-stripe-style
description: Apply current Stripe documentation patterns to API onboarding, task guides, object reference, testing, webhooks, and errors. Use when a Relay page needs a shorter use-case path, a sandbox-first flow, or a clean split between guides and resource reference.
---

# Stripe documentation style

Use Stripe for task selection and resource-oriented reference.

## Structure

1. Start with common user outcomes.
2. Give one quickstart per major outcome.
3. Let readers test without touching live systems.
4. Organize API reference around stable resources.
5. Keep webhook setup, event types, signature repair, and errors distinct.

## Writing pattern

- Use action titles: “Build a checkout page,” “Set up a webhook.”
- Name the result in the first sentence.
- Keep account and environment setup short.
- Show a complete request and response together.
- State whether the example uses test or live state.
- Put language choice in the code surface, not repeated prose.

## What to adapt

- Use-case routing before product taxonomy.
- Test-state labels beside every runnable example.
- Object pages with canonical shapes first.
- Focused troubleshooting pages for common failures.
- Short index pages that send readers to one next task.

## What to avoid

- Stripe’s full product catalogue is much larger than Relay.
- Do not create navigation categories for future Relay products.
- Do not copy payment-specific lifecycle or account concepts.

## Verify

- A reader can choose the right start in one screen.
- Test and production effects are explicit.
- Guides do not duplicate complete endpoint schemas.
- Error pages give one direct repair path.

## Sources

- https://docs.stripe.com/llms.txt
- https://docs.stripe.com/get-started.md
- https://docs.stripe.com/api.md
- https://docs.stripe.com/webhooks.md
- https://docs.stripe.com/api/errors.md

Sources checked on 2026-08-10.
