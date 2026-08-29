# Relay Messenger documentation information architecture

Status: working source of truth for the Docs rebuild  
Method: outer shell first, then page structure, then examples and prose  
Source priority: Relay contract → Linq presentation → Photon presentation

This document defines how Relay Messenger documentation is organized and
taught. It is deliberately one document: navigation, page topology,
typography, code presentation, and content boundaries must be decided together
before individual pages are polished.

## Product identity

| Surface | Approved name |
| --- | --- |
| Product and company | Relay Messenger |
| Developer interface | Relay API |
| Developer dashboard | Relay Console |
| TypeScript package | `@relaymessenger/sdk` |
| Public API origin | `https://api.relayapp.im` |
| Console origin | `https://console.relayapp.im` |

The `relayapp.im` hostnames are current domains. They do not change the
product name.

## 1. Source boundary

### Relay behavior

Only the current Relay Server OpenAPI, implementation, and tests prove Relay
behavior:

- `../_worktrees/Relay-Server-local/contracts/developer/openapi.yaml`
- `../_worktrees/Relay-Server-local/server/src`
- `../_worktrees/Relay-Server-local/server/test`
- `../Relay-SDK/packages/sdk/src`
- `../Relay-SDK/packages/sdk/test`

Linq and Photon are presentation and mechanism references. They cannot prove
that Relay implements a feature.

### Linq presentation sources

- Frozen index:
  `../_sources/linq/official-docs/llms.txt`
- Frozen complete corpus:
  `../_sources/linq/official-docs/llms-full.txt`
- Frozen OpenAPI:
  `../_sources/linq/openapi/linq-api-v3.yaml`
- Research:
  `../Relay-Research/research/docs-deep-research/docs-craft-20260818/companies/linq.md`
- Live canonical pages:
  - [docs.linqapp.com](https://docs.linqapp.com/)
  - [Quickstart](https://docs.linqapp.com/getting-started/quickstart/)
  - [Client SDKs](https://docs.linqapp.com/getting-started/sdks/)
  - [Sending Messages](https://docs.linqapp.com/guides/messaging/sending-messages/)
  - [Webhooks](https://docs.linqapp.com/guides/webhooks/)

### Photon presentation sources

- Frozen docs:
  `../_sources/photon/official-docs/pages`
- Frozen SDK:
  `../_sources/photon/repos/spectrum-ts`
- Research:
  `../Relay-Research/research/docs-deep-research/docs-craft-20260818/companies/photon.md`
- Live canonical pages:
  - [Spectrum introduction](https://photon.codes/docs/spectrum-ts/introduction)
  - [Spectrum Getting Started](https://photon.codes/docs/spectrum-ts/getting-started)
  - [Webhook overview](https://photon.codes/docs/webhooks/overview)
  - [Webhook delivery](https://photon.codes/docs/webhooks/delivery)

## 2. The onion method

Documentation is rebuilt from the outside inward.

### Pass A — outer shell

Freeze:

1. top-level tabs;
2. sidebar groups;
3. page inventory;
4. page names;
5. page order;
6. generated-reference boundary.

No page-level prose decision may override this hierarchy.

### Pass B — page system

For each page, freeze:

1. reader job;
2. prerequisites;
3. H2/H3 outline;
4. what belongs here;
5. what links elsewhere;
6. page archetype.

No detailed example is written until the page has one clear job.

### Pass C — presentation system

Apply:

1. TypeScript SDK/cURL tabs;
2. request and response examples;
3. tables;
4. notes and warnings;
5. agent-review prompts;
6. related-page links.

### Pass D — content

Write and edit exact prose. Verify every behavior against Relay source.

### Pass E — rendered proof

Validate links, Mintlify build, accessibility, desktop scanability, narrow
widths, and generated API reference.

## 3. What Linq does well

### Outer topology

Linq separates five products of documentation:

```text
Get started
Guides
Error Codes
API Reference
V2 API (legacy)
```

Its current V3 narrative path is:

```text
Introduction
Quickstart
Authentication
Client SDKs
Key Concepts
AI coding agents
Best Practices

Messaging
Chats
Contact Cards
Integrations
Webhooks
Platform
Examples / FAQ
```

The API Reference is generated and resource-oriented. It does not replace the
task guides. Error Codes have a separate top-level surface and one page per
stable code.

### Ordering principle

The rendered sidebar prioritizes:

1. first success;
2. credentials;
3. supported clients;
4. shared vocabulary;
5. common writes;
6. common content;
7. chat management;
8. inbound events;
9. reliability and debugging;
10. less common integrations.

This is more useful than alphabetical ordering. The frozen `llms.txt` index is
alphabetical inside some groups, so it is evidence of inventory, not always of
the human sidebar order.

### Split decisions

Linq gives separate pages to concepts with different tasks:

- Sending Messages
- Mentions
- Message Details
- Attachments
- Voice Memos
- Rich Link Previews
- Reactions
- Group Chats
- Typing Indicators
- Sharing Contact Card
- Webhooks
- Webhook Subscriptions
- Webhook Events

This makes search results and sidebar labels literal. A reader does not open a
generic “Messaging” essay to find an upload sequence.

### Combine decisions

Linq combines material when it is one workflow:

- text, media, and links begin on Sending Messages;
- create/list/update/delete subscription operations share Webhook
  Subscriptions;
- closely related field semantics live on Message Details;
- one Error Code page combines cause, fix, and retry guidance.

### Page grammar

Strong Linq pages use this order:

1. direct opening sentence;
2. important note when necessary;
3. task heading;
4. rule immediately before code;
5. runnable example;
6. real response or field table;
7. failure/retry behavior;
8. next steps.

Paragraphs are short. Bold text marks an operational rule, not ordinary nouns.
Tables compare states, limits, fields, or decisions. Code carries mechanics.

### Human and agent surfaces

Linq supports:

- Copy Markdown;
- per-page Markdown;
- `llms.txt`;
- `llms-full.txt`;
- OpenAPI;
- AI coding-agent setup;
- copyable audit prompts.

These are additive. Human pages remain readable without an agent.

### Linq weaknesses Relay should not copy

- duplicated or conflicting first-send examples;
- long generated descriptions repeated on resource indexes;
- unsupported or legacy products mixed into modern discovery;
- plugins present only on GitHub and drifting from current webhook docs;
- SDK trees duplicated by language when guide tabs already explain the task.

## 4. What Photon does well

### Outer topology

Photon separates major operating modes into top-level tabs:

```text
Spectrum SDK
CLI
Webhooks
Low-level SDKs
API Reference
```

That separation is important. Runtime SDK work, webhook delivery, management
HTTP, and low-level platform SDKs do not pretend to be one protocol.

### SDK-first teaching

Photon’s primary reader path is:

```text
Introduction
Getting Started
Messages
Spaces and Users
Reactions and Replies
Content builders
Providers
Advanced lifecycle
Best practices
Troubleshooting
```

The first screen usually contains the normal TypeScript call. Exact return
semantics follow it. Package and method names are central because the SDK is
the product surface.

### Hub-and-child pattern

Photon uses a hub page when a category is real and broad:

- Content hub → one page per builder;
- Provider hub → one page per provider;
- iMessage feature hub → one page per feature;
- Webhook overview → quickstart, events, verification, delivery, management,
  troubleshooting.

A hub or Overview is justified only when it orients several child tasks. A
group with one page does not need a ceremonial Overview.

### Transport separation

Photon explicitly separates:

- runtime SDK/gRPC;
- HTTP webhook observation;
- management HTTP API;
- low-level SDKs.

Its webhook pages do not imply that webhooks can perform runtime sends. Its
management API introduction says it is not the message runtime.

### Page grammar

Photon pages commonly use:

1. package or mechanism name;
2. its one job;
3. install;
4. normal call;
5. important variant;
6. exact success boundary;
7. feature/method/example table;
8. troubleshooting.

Mermaid appears where sequence or architecture is easier to understand
visually. Screenshots are rare and reserved for external dashboard work.

### Photon weaknesses Relay should not copy

- runtime behavior split across docs and multiple READMEs;
- TypeScript-only runtime forcing Python integrations through a sidecar;
- marketing provider claims exceeding documented providers;
- broken or stale generated agent assets;
- management API and runtime SDK requiring careful reader disambiguation.

## 5. Relay combine/split rules

Create a separate page when any of these changes:

1. reader goal;
2. credential;
3. protocol;
4. acknowledgement boundary;
5. retry rule;
6. resource lifecycle;
7. failure model;
8. likely search phrase.

Combine material when:

1. it is one short workflow;
2. separating it would force the reader to alternate pages;
3. every section uses the same credential and failure model;
4. the combined page remains scannable from H2 headings.

### Required splits

- Webhooks and WebSocket
- Attachments and Voice Memos
- Group Chats and Participants
- Typing and Message sending
- Contact Card configuration and sharing a Contact Card
- Guides and generated API Reference
- Error explanation and endpoint reference

### Required combinations

- webhook subscription CRUD on one page;
- start and stop typing on one page;
- add and remove reactions on one page;
- add, remove, and leave membership in one Participants page;
- direct and group receipt storage in one Delivery Receipts page, with the UI
  distinction explicit;
- TypeScript SDK and cURL for the same task in one guide.

## 6. Relay Messenger outer topology

Relay Messenger has three top-level tabs.

```text
Guides
Error Codes
API Reference
```

### Guides

Exact group and page order:

```text
Introduction
  Introduction

Getting started
  Quickstart
  Authentication
  Client SDKs
  Key Concepts
  AI coding agents
  Best Practices

Messaging
  Messaging
  Sending Messages
  Mentions
  Message Details
  Message Parts
  Attachments
  Voice Memos
  Rich Link Previews
  Replies
  Reactions
  Delivery Receipts

Chats
  Chats
  Group Chats
  Participants
  Typing Indicators
  Sharing Contact Card
  Message History

Contacts
  Contact Cards
  Blocked Handles

Agent events
  Agent Events

Webhooks
  Webhooks
  Webhook Subscriptions
  Webhook Event Types
  Webhook Delivery

WebSocket
  WebSocket
  Protocol
  Acknowledgements
  FULL sync

Platform
  Idempotency
  Rate Limits
  Debugging

Examples
  Examples
```

### Error Codes

```text
Overview
1xxx request errors
2xxx resource errors
3xxx server errors
```

Each code page must state:

1. HTTP status;
2. cause;
3. exact fix;
4. retry rule;
5. related endpoint or guide.

### API Reference

```text
Overview
Generated endpoint groups from the Relay API OpenAPI
```

Do not hand-maintain endpoint fields in narrative pages. OpenAPI is the field
authority.

## 7. Page inventory decisions

| Page | Job | Why separate |
| --- | --- | --- |
| Quickstart | first successful send and receive setup | highest-frequency onboarding path |
| Authentication | protect and send an Agent Token | security boundary |
| Client SDKs | install and operate `@relaymessenger/sdk` | maintained client surface |
| Key Concepts | define Contact, Handle, Chat, Message, part, event | vocabulary once |
| Sending Messages | choose new/existing Chat and send | primary write |
| Mentions | encode group mention and UTF-16 range | distinct validation failures |
| Message Details | retrieve one Message or thread | read task |
| Message Parts | understand ordered text/media/link parts | content model |
| Attachments | allocate, raw PUT, retrieve, delete | independent upload lifecycle |
| Voice Memos | send audio with voice presentation | dedicated endpoint |
| Rich Link Previews | send a sole link part | special composition rule |
| Replies | target Message and part | threading rule |
| Reactions | add/remove, part target, replacement state | mutation lifecycle |
| Delivery Receipts | per-recipient truth and acknowledgement boundaries | reliability contract |
| Group Chats | create, name, photo, limits | group lifecycle |
| Participants | add/remove/leave and history window | membership authorization |
| Typing Indicators | transient start/stop and expiry | transient failure model |
| Sharing Contact Card | share configured card inside Chat | explicit user action |
| Message History | cursor reads and membership visibility | recovery/read task |
| Contact Cards | configure agent profile card | profile lifecycle |
| Blocked Handles | block/list/unblock | safety state |
| Webhooks | choose and receive webhook transport | serverless-friendly ingress |
| Webhook Subscriptions | configure destinations/events | configuration lifecycle |
| Webhook Event Types | enumerate and interpret envelopes | schema discovery |
| Webhook Delivery | retries, terminal state, redrive | delivery reliability |
| WebSocket | choose and connect transport | long-running ingress |
| Protocol | exact frame grammar and close codes | wire contract |
| Acknowledgements | durable cumulative ACK | correctness boundary |
| FULL sync | recovery outside retention | destructive recovery workflow |

## 8. Canonical page archetypes

### Task guide

```text
Opening sentence: result
Prerequisites (only if needed)
## Perform the task
TypeScript / cURL tabs
Real response
## Rules
## Failure and retry behavior
## Next steps
```

### Concept page

```text
Opening sentence: definition
## Core model
Small diagram or table
## Invariants
## Example
## Related
```

Concept pages do not repeat every operation.

### Protocol page

```text
Opening sentence: boundary
## Connect / authenticate
## Client → server frames
## Server → client frames
## Ordering and acknowledgement
## Reconnect / recovery
## Errors / close codes
## Review with an agent
```

### Error page

```text
One-sentence cause
Status and code
## Why it happened
## Fix
## Retry
## Related
```

### Generated reference

Generated from OpenAPI. Narrative additions belong in operation descriptions
or guides, not duplicated field tables.

## 9. Heading topology

### H1

One page title from frontmatter/Mintlify. Do not write a second decorative H1.

### H2

H2s describe the reader’s sequence or question:

- `## Create an upload`
- `## Upload the raw bytes`
- `## Retry behavior`

Avoid:

- `## Overview` inside a page already titled Overview;
- `## Current status`;
- `## More information`;
- headings used for one sentence.

### H3

Use H3 only when one H2 has multiple comparable variants. Do not descend to
H4 for ordinary guides.

### Scan test

A reader scanning only title, H2s, bold rules, tables, and code must understand
the page’s job and main constraints.

## 10. Typography and prose

- One to three sentences per paragraph.
- Lead with the answer.
- Use **bold** for one operational rule or irreversible boundary.
- Never bold an entire paragraph.
- Use bullets for independent rules.
- Use numbered steps for order.
- Use tables only for comparisons, states, fields, limits, or retry decisions.
- Prefer literal words over internal architecture vocabulary.
- Define a Relay noun once, capitalize it consistently, and link back.
- Use `Contact`, `Handle`, `Chat`, `Message`, `part`, `Agent Token`,
  `Webhooks`, and `WebSocket`.

## 11. TypeScript SDK and cURL

### Rule

Every executable developer task supported by `@relaymessenger/sdk` uses one
Mintlify tab group:

```text
[ TypeScript SDK ] [ cURL ]
```

TypeScript is first. cURL is second. They must perform the same operation with
the same identifiers and content.

### Where tabs are required

- Quickstart
- send/resolve/create Chat
- mentions
- retrieve Message/thread
- attachments
- voice memos
- replies
- reactions
- groups and participants
- typing
- Contact Card configuration/sharing
- blocked Handles
- webhook subscriptions/events where SDK methods exist
- WebSocket setup/run

### Where tabs are not required

- pure concept pages;
- retry tables;
- wire-frame JSON;
- database reasoning;
- generated API Reference;
- user-only internal app operations not exposed by the Agent SDK.

### Attachment exception

The TypeScript tab should show the SDK’s allocate/upload helper. The cURL tab
should show allocation plus raw `PUT`. Do not split one upload workflow across
unrelated pages.

### Accuracy rule

Method names come from `Relay-SDK/packages/sdk/src` and its tests. A guessed
SDK call is worse than a cURL-only example.

## 12. Code and response presentation

- Put the rule immediately before code.
- Include imports/client creation once per page when needed.
- Use the same `chatId`, `messageId`, and Handle throughout a page.
- Show the canonical response after the first mutation where later steps use
  its ID.
- Do not use ellipses inside payloads whose exact shape matters.
- Use UUID-shaped examples and realistic Handles.
- Never show a credential value.
- State what success proves and what it does not prove.

## 13. Callouts

Use:

- `<Note>` for context that prevents a common misunderstanding;
- `<Info>` for a deliberate Relay difference;
- `<Warning>` for data loss, security, irreversible actions, or duplicate
  side effects;
- `<Tip>` for optional convenience.

Do not stack callouts. Most pages need zero or one near the relevant step.

## 14. Agent-friendly treatment

Keep Mintlify header actions:

```json
{
  "contextual": {
    "options": ["copy", "view"],
    "display": "header"
  }
}
```

Header navigation has two actions:

- **Copy agent prompt** is a secondary link with Mintlify's `copy` icon. The
  root custom script copies `skill.md` exactly and shows transient **Copied**
  feedback without replacing the icon. Its normal `href` opens the exact
  `Relay agent prompt` section when JavaScript or clipboard access is
  unavailable.
- **Console** is the primary action and opens Relay Console.

The Relay logo opens `https://relayapp.im`. Mintlify's native **Copy page**
action keeps its original name because it copies the current page Markdown.

Use a Review with an agent block only when a concrete audit is valuable:

- authentication;
- idempotency;
- webhook verification;
- durable ACK;
- FULL sync;
- migration.

The prompt must:

1. read current Relay docs/OpenAPI;
2. be read-only unless asked;
3. require file-and-line evidence;
4. say `unknown` instead of guessing.

## 15. Overview policy

An Overview page is retained only when it:

1. defines a real category;
2. explains how child pages relate;
3. gives a decision or path the children cannot repeat efficiently.

Therefore:

- Messaging, Chats, Webhooks, and WebSocket may have orienting root pages.
- Agent Events is a thin comparison hub because choosing one of two transports
  is a real decision shared by Webhooks and WebSocket; it must not absorb either
  protocol's mechanics.
- Contacts does not need a separate Overview while it has only Contact Cards
  and Blocked Handles.
- Platform does not need an Overview.
- A one-page Introduction group is acceptable because Introduction is the site
  landing page, not a category placeholder.

## 16. Exact heading skeletons

These outlines match the current public pages. A heading change must preserve
the page's single job and update this inventory in the same commit.

### Introduction and Getting started

| Page | H2 order |
| --- | --- |
| Introduction | `Prerequisites` → `What you can build` → `Key capabilities` → `Authentication` → `Quick example` → `Next steps` |
| Quickstart | `Prerequisites` → `1. Set your credentials` → `2. Choose the SDK or HTTPS` → `3. Create a webhook subscription` → `4. Accept the event durably` → `5. Mark Read and reply` → `Review with an agent` → `Next steps` |
| Authentication | `Credentials` → `Agent Tokens` → `WebSocket authentication` → `Errors` → `Related` |
| Client SDKs | `Install` → `Create a client` → `Send a Message` → `Resources` → `Pagination` → `Retries and idempotency` → `Errors` → `Webhook verification` → `WebSocket` → `Browser limitation` → `Runnable examples` → `Related` |
| Key Concepts | `Contacts and Handles` → `Chats` → `Messages and parts` → `Attachments` → `Delivery` → `Events` → `Idempotency` → `Related` |
| AI coding agents | `Documentation files` → `Relay agent prompt` → `Build prompt` → `Audit prompt` → `Related` |
| Best Practices | `Accept events before processing` → `Make commands idempotent` → `Keep replies on REST` → `Treat IDs as opaque` → `Upload media before sending` → `Respect membership visibility` → `Handle duplicates` → `Related` |

### Messaging

| Page | H2 order |
| --- | --- |
| Messaging | `Part types` → `Send paths` → `Message lifecycle` → `Next steps` |
| Sending Messages | `Send to an existing Chat` → `Resolve or create a Chat` → `Send multiple parts` → `Idempotency` → `Limits` → `Next steps` |
| Mentions | `Mention a Contact` → `Choose the range` → `Validation rules` → `Related` |
| Message Details | `Retrieve a Message` → `Read the response` → `Direction` → `List Chat history` → `Related` |
| Message Parts | `Part types` → `Ordering and composition` → `Response-only parts` → `Related` |
| Attachments | `1. Create an upload` → `2. Upload the raw bytes` → `3. Send the Attachment` → `Import a public media URL` → `Media metadata` → `Image formats` → `Limits` → `Ownership` → `Related` |
| Voice Memos | `Upload audio` → `Send the voice memo` → `Read the response` → `Related` |
| Rich Link Previews | `Send a link part` → `Composition rules` → `Start a Chat with a link` → `Related` |
| Replies | `Reply to a Message` → `Target a part` → `List a reply thread` → `Related` |
| Reactions | `Add a reaction` → `Reaction types` → `Remove a reaction` → `Events` → `Related` |
| Delivery Receipts | `Response fields` → `Delivered boundaries` → `Acknowledge user delivery` → `Mark Read` → `Direct and group presentation` → `Related` |

### Chats and Contacts

| Page | H2 order |
| --- | --- |
| Chats | `Chat types` → `Create a Chat` → `Chat fields` → `Next steps` |
| Group Chats | `Create a group` → `Limits` → `Rename the group` → `Set a group photo` → `Group metadata events` → `Related` |
| Participants | `Add a Contact` → `Remove a Contact` → `Leave` → `Membership periods` → `Events` → `Related` |
| Typing Indicators | `Start or refresh` → `Refresh and auto-clear` → `Stop` → `Receive events` → `API reference` → `Related` |
| Sharing Contact Card | `Before sharing` → `Share the card` → `Keep configuration separate` → `Related` |
| Message History | `Pagination` → `Group-history rows` → `Membership visibility` → `Agent recovery` → `Related` |
| Contact Cards | `How Contact Cards work` → `Retrieve the card` → `Upsert the card` → `Update the card` → `Fields` → `Sharing is separate` → `Related` |
| Blocked Handles | `Block` → `Behavior` → `List` → `Unblock` → `Related` |

### Agent events, Webhooks, and WebSocket

| Page | H2 order |
| --- | --- |
| Agent Events | `Choose a transport` → `Shared envelope` → `Switch transports` → `Recovery` → `Review with an agent` → `Related` |
| Webhooks | `Flow` → `Create a subscription` → `Verify the signature` → `Acknowledge safely` → `Review with an agent` → `Related` |
| Webhook Subscriptions | `Create` → `Store the signing secret` → `List, retrieve, update, or delete` → `Rotate a secret` → `Related` |
| Webhook Event Types | `List supported events` → `Envelope` → `Message events` → `Payload version` → `Reaction events` → `Chat events` → `Related` |
| Webhook Delivery | `Delivery policy` → `Retry classes` → `Receiver pattern` → `Delivered meaning` → `Terminal state and redrive` → `Review with an agent` → `Related` |
| WebSocket | `Select WebSocket delivery` → `Connect with the SDK` → `Security trade-off` → `Review with an agent` → `Related` |
| WebSocket Protocol | `Ready frame` → `Event frame` → `Error frame` → `Backpressure` → `Heartbeats` → `Disconnects` → `Related` |
| Acknowledgements | `Frame` → `Safe order` → `Delivery meaning` → `Replay` → `Errors` → `Review with an agent` → `Related` |
| FULL sync | `Normal reconnect` → `When Relay requires FULL sync` → `Commit the snapshot` → `Events during sync` → `Retention` → `Failure handling` → `Related` |

### Platform, Examples, errors, and reference

| Page | H2 order |
| --- | --- |
| Idempotency | `Supply a key` → `Retry behavior` → `Derive reply keys from events` → `Event idempotency` → `Related` |
| Rate Limits | `Messages` → `Chats` → `Attachments` → `Agent events` → `Related` |
| Debugging | `IDs to record` → `Error response` → `Safe logs` → `Event debugging` → `Related` |
| Examples | `Agent backends` → `Messaging` → `Reliability` → `Related` |
| Error overview | `Envelope fields` → `Error code ranges` → `1xxx request errors` → `2xxx resource errors` → `3xxx server errors` → `Related` |
| One error code | `Response` → `Fix` → `Retry` → `Related` |
| API Reference overview | `Conventions` → `Resources` → `Errors` → `Related` |

## 17. Current page map

| Current path | Placement | Status |
| --- | --- | --- |
| `index.mdx` | Introduction | integrated |
| `getting-started/*` | Getting started | integrated |
| `guides/messaging/*` | Messaging | integrated |
| `guides/chats/index.mdx`, `group-chats.mdx`, `participants.mdx`, `typing-indicators.mdx`, `share-contact-card.mdx`, `message-history.mdx` | Chats | integrated |
| `guides/contact-cards.mdx`, `guides/chats/blocked-handles.mdx` | Contacts | integrated |
| `guides/agent-events/index.mdx` | Agent events | integrated comparison hub |
| `guides/webhooks/*` | Webhooks | integrated |
| `guides/websocket/*` | WebSocket | integrated |
| `guides/platform/*` | Platform | integrated |
| `examples/index.mdx` | Examples | integrated |
| `api-reference/*` | API Reference | generated from the current OpenAPI |
| `error/*` | Error Codes | integrated one-code pages |

## 18. Validation gates

### Outer shell

- exact top-level tabs;
- exact group order;
- exact page order;
- Webhooks and WebSocket are separate;
- no unsupported feature page;
- no stale or orphan page.

### Page system

- one job per page;
- no duplicate H1;
- no empty Overview;
- no `Current status`;
- no H4 in ordinary guides;
- every task page ends with related/next steps.

### SDK/API presentation

- TypeScript tab before cURL;
- equivalent operation and payload;
- every SDK method exists in current source;
- no Python or Go examples until maintained SDKs exist;
- no browser Agent Token example.

### Contract

- Server and Docs OpenAPI byte-identical;
- all examples match current paths, fields, events, limits, and auth;
- no ticket, query credential, required subprotocol, polling, `service`, or
  unsupported feature residue.

### Rendering

- Mintlify validate;
- broken links;
- accessibility;
- desktop and narrow screenshots;
- readable heading density;
- code tabs visible without horizontal page overflow.

## 19. Final principle

Relay copies Linq’s resource-oriented discovery and human/agent accessibility.
Relay copies Photon’s SDK precision, transport separation, and explicit
success boundaries.

Relay does not copy either company’s product vocabulary or unsupported
features. The Docs structure follows the product Relay actually has.
