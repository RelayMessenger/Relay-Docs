---
name: docs-vercel-ai-sdk-style
description: Apply current Vercel AI SDK documentation patterns to streaming, typed message parts, framework adapters, and JavaScript examples. Use when Relay needs a clear split between core transport, UI integration, agent behavior, providers, and API reference.
---

# Vercel AI SDK documentation style

Use the AI SDK for layered framework documentation.

## Structure

1. Explain the toolkit in one sentence.
2. Route readers to Core, UI, Agents, Providers, or Reference.
3. Give each concept one focused page.
4. Link the concept page to exact helper references.
5. Publish a search endpoint, `llms.txt`, targeted Markdown, and a skill.

## Writing pattern

- Name the helper before explaining its internals.
- Start with the common path.
- Add type definitions before advanced stream composition.
- Keep framework variants in tabs.
- Explain the wire format only when the reader must debug it.

## What to adapt

- Stable product layers.
- Search-first machine-readable access.
- Type-safe examples.
- Focused pages for one stream or message-part problem.
- Direct links from examples to symbols.

## What to avoid

- Do not let framework abstractions hide Relay’s raw HTTPS contract.
- Do not copy provider or model setup into Relay transport pages.
- Do not assume a remembered SDK version.

## Verify

- Raw Relay behavior appears before framework convenience.
- Each helper name links to current documentation.
- Stream completion, abort, retry, and storage semantics are explicit.
- Examples use the current UIMessageStream version from Relay’s contract.

## Sources

- https://ai-sdk.dev/llms.txt
- https://ai-sdk.dev/docs/introduction.md
- https://ai-sdk.dev/docs/getting-started.md
- https://ai-sdk.dev/docs/ai-sdk-ui/streaming-data.md
- https://ai-sdk.dev/docs/reference.md

Sources checked on 2026-08-10.
