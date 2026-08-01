# Authoring Relay docs

Conventions this site follows. They apply to people and to coding agents.

## This directory

- This is a [Mintlify](https://mintlify.com) site. Navigation, theme, and
  OpenAPI wiring live in `docs.json`, not in a framework config.
- Every `.md` and `.mdx` file here becomes a published page. Never add notes,
  plans, or scratch files to this tree.
- A file that exists but is absent from `docs.json` navigation is not an
  integrated page. Wire it in.
- Preview with `npx mint dev`, which serves on port 3000.

## Page anatomy

Start every page with valid frontmatter. `title`, `description`, and `keywords`
are required; `keywords` feeds search and the assistant index.

```yaml
---
title: "Short task or concept title"
description: "One sentence stating the outcome and scope."
keywords: ["term", "term", "term"]
---
```

Then follow the shape for the page type:

| Page type | Shape |
| --- | --- |
| Task guide | Outcome sentence → prerequisites → first runnable `curl` → real response → failure and retry behavior → `Next steps` |
| Concept | Definition and ownership boundary → smallest wire example → lifecycle and invariants → `See also` |
| Reference | Canonical shape first → field, limit, and error tables → `See also` |
| Status | Mark tables, not narrative |

## Write for an agent operator

- Begin with the job: register a webhook, receive an event, send a reply, stream
  output, or inspect history.
- Relay is the messenger. The developer's external backend is the agent brain.
  Keep that boundary explicit.
- Use `https://api.relayapp.im` and `$RELAY_AGENT_TOKEN` in examples.
- Show raw HTTPS and JSON before any abstraction. Do not imply a maintained SDK,
  framework, model provider, or host.
- Prefer `curl -sS` with exact headers, status codes, and idempotency behavior.
- Derive idempotency keys from stable logical inputs such as an inbound
  `event_id`, and reuse the same key on retry.
- Distinguish implemented behavior from roadmap behavior. Mark an intentionally
  documented but unshipped surface `coming soon`; never present it as available.

## Prose

- Open with one sentence naming the outcome. No framing essay.
- Cap paragraphs at three sentences. If it will not split, it is a list or a table.
- Second person, active voice, sentence case headings.
- Every field, limit, error, status, or comparison list is a table. A field list
  written as prose is a defect.
- End every page in `Next steps` or `See also` with real links, never a summary
  paragraph restating the page.
- No em dashes. Use commas, colons, or a period.
- No marketing language, filler ("it's important to note", "in order to"), or
  editorializing ("simply", "just", "obviously").

## Components

Use Mintlify's built-ins deliberately, and sparsely enough that the task path
stays obvious.

| Need | Use |
| --- | --- |
| Ordered actions | `<Steps>` |
| Choose one of several paths | `<Tabs>` |
| Optional or edge-case detail | `<Accordion>` |
| Long payloads | `<Expandable>` |
| Equivalent code or payload alternatives | `<CodeGroup>`, every block titled |
| Small navigation sets | `<Card>` in `<Columns>` |
| Screenshots and diagrams | `<Frame>`, always with alt text |
| Flows, lifecycles, sequences | a ```mermaid block |

Callouts carry severity. Do not route every non-neutral remark through
`<Warning>`; a page where every callout is a warning teaches readers to skip all
of them.

| Callout | Use for |
| --- | --- |
| `<Note>` | Context a reader can skip |
| `<Info>` | Helpful context such as permissions or scope |
| `<Tip>` | A recommendation or better path |
| `<Check>` | Confirming a successful outcome |
| `<Warning>` | Real breakage, security, or data-loss risk |

## Status marks

Availability and status tables use a mark in the first column, because Relay
distinguishes five states and a mark reads faster than five words.

| Mark | Means |
| :---: | --- |
| ✅ | Supported, or production-proved |
| 🔵 | Available in developer preview: the route and schema exist |
| ⚠️ | Conditional, limited, or proved locally but not shipped |
| ⏳ | Specified, coming later |
| ❌ | Not available |

Center mark columns with `| :---: |`.

## Never hand-write endpoint pages

Edit `api-reference/openapi.yaml` for an endpoint's operation, parameters,
request body, responses, schemas, security, examples, tags, summary, and
description. Mintlify generates the endpoint pages from that file. Keep
`api-reference/overview.mdx` for conventions shared across several endpoints.

## Before you open a pull request

```bash
mint broken-links
mint validate
```

Treat any failure as a blocker. Do not waive a broken link because the
destination is planned or expected to deploy later: add the page, correct the
link, remove the claim, or add a redirect in `docs.json`.
