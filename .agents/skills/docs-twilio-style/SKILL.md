---
name: docs-twilio-style
description: Apply selected Twilio documentation patterns to communications quickstarts, inbound webhooks, phone and message examples, and language-specific guides. Use when Relay needs a complete send-and-receive tutorial with clear credentials and test effects. Avoid Twilio’s catalogue depth.
---

# Twilio documentation style

Use Twilio for complete communications tutorials and language switching.

## Structure

1. Name the communication result.
2. State account, credential, sender, and recipient requirements.
3. Let the reader choose one language.
4. Send one message.
5. Receive one message.
6. Show the result and the next operational step.

## What to adapt

- One coherent send-and-receive story.
- Persistent language tabs across a guide.
- Explicit test credentials and recipient effects.
- Real response examples.
- Links from tutorials to the exact API resource.

## What to avoid

- Twilio’s SMS quickstart was about 5,806 words on 2026-08-10.
- Do not repeat install, environment, and server code for every language inline.
- Do not mix multiple Twilio-like products into one Relay task.
- Do not use marketing descriptions in technical steps.

## Verify

- One language path reads continuously from start to result.
- Credentials appear before the first request.
- The guide says what external action the example performs.
- Advanced hosting and production hardening move to later pages.

## Sources

- https://www.twilio.com/docs/llms.txt
- https://www.twilio.com/docs/messaging/quickstart.md
- https://www.twilio.com/docs/messaging
- https://www.twilio.com/docs/usage/webhooks

Sources checked on 2026-08-10.
