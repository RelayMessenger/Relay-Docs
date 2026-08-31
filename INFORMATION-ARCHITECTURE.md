# Relay documentation information architecture

This file controls Relay's public documentation structure. It keeps
navigation, page responsibilities, examples, and generated reference content
aligned with the current contract.

## Product identity

| Surface | Name |
| --- | --- |
| Product and company | Relay |
| Developer interface | Relay API |
| Developer dashboard | Relay Console |
| TypeScript package | `@relaymessenger/sdk` |
| Public API origin | `https://api.relayapp.im` |
| Console origin | `https://console.relayapp.im` |

The `relayapp.im` hostnames are Relay's current domains.

## 1. Contract boundary

Public behavior comes from three current sources:

1. Relay Server OpenAPI defines public paths, fields, limits, errors, and
   authentication.
2. Relay Server implementation and tests prove runtime behavior.
3. Relay SDK source and tests prove TypeScript methods and return types.

`api-reference/openapi.yaml` is byte-identical to the approved Relay Server
contract. `api-reference/openapi.mint.yaml` is the generated Mintlify bundle.
Endpoint pages come from that bundle.

Every public claim maps to a current contract field, implementation branch, or
test. Public pages describe the supported Relay path directly.

## 2. Public model

Use Relay's current resource names consistently:

| Resource | Meaning |
| --- | --- |
| Contact | A user or agent profile |
| Handle | A Contact's public messaging address |
| Chat | A direct or group message container |
| Message | One ordered set of parts in a Chat |
| part | A text, media, or link unit inside a Message |
| Attachment | Uploaded media referenced by a Message part |
| Agent event | A versioned event delivered by Webhook or WebSocket |

Use `participants` for group membership operations and `participant.*` event
names. Use Webhooks for signed HTTPS event delivery and WebSocket for a durable
agent connection. Message commands use REST.

## 3. Site topology

Relay has three top-level tabs:

```text
Guides
Error Codes
API Reference
```

The Guides tab uses this exact order:

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
  Add requests
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

Error Codes groups stable errors by `1xxx`, `2xxx`, and `3xxx`. API Reference
contains the shared conventions page followed by generated endpoint groups.

## 4. Reader order

The sidebar teaches Relay in this sequence:

1. complete a first request;
2. authenticate;
3. install the maintained SDK;
4. learn shared resources;
5. send and read Messages;
6. manage Chat content and membership;
7. receive agent events;
8. implement reliability and debugging.

Pages follow task frequency rather than alphabetical order.

## 5. Page responsibilities

A page owns one developer job. Separate pages carry separate resource
lifecycles, credentials, protocols, acknowledgement boundaries, retry rules,
or common search terms.

Current focused pages include:

- Sending Messages, Mentions, Message Details, and Message Parts;
- Attachments, Voice Memos, and Rich Link Previews;
- Group Chats, Participants, Typing Indicators, and Message History;
- Add requests, Contact Card configuration, and Sharing Contact Card;
- Webhooks, Webhook Subscriptions, Webhook Event Types, and Webhook Delivery;
- WebSocket, Protocol, Acknowledgements, and FULL sync.

Closely related operations stay together: webhook subscription CRUD, reaction
add/remove, typing start/stop, and participant add/remove/leave.

## 6. Page archetypes

### Task guide

```text
Outcome sentence
Prerequisites when required
## Perform the task
TypeScript SDK and cURL
Real response
## Rules
## Failure and retry behavior
## Next steps
```

### Concept page

```text
Direct definition
## Core model
Small table or diagram
## Invariants
## Example
## Related
```

### Protocol page

```text
Direct protocol boundary
## Connect and authenticate
## Client to server frames
## Server to client frames
## Ordering and acknowledgement
## Reconnect and recovery
## Errors and close codes
## Review with an agent
```

### Error page

```text
One-sentence cause
HTTP status and Relay code
## Response
## Fix
## Retry
## Related
```

## 7. Heading and prose system

Mintlify supplies the page title from frontmatter. H2 headings describe the
reader's sequence. H3 headings group comparable variants under one H2.

Public prose uses:

- one direct opening sentence;
- paragraphs of one to three sentences;
- active voice and second person;
- sentence case headings;
- bold text for a single operational rule;
- numbered lists for ordered work;
- tables for fields, states, limits, and comparisons;
- `Next steps`, `Related`, or `See also` as the final section.

Relay nouns keep their contract capitalization: Contact, Handle, Chat, Message,
Attachment, Agent Token, Webhooks, and WebSocket.

## 8. TypeScript SDK and cURL

Executable developer tasks show equivalent options in this order:

```text
TypeScript SDK
cURL
```

The TypeScript call comes from `@relaymessenger/sdk`. The cURL request uses the
same operation, identifiers, and payload. Pure concepts, retry tables,
WebSocket frame examples, and generated endpoint reference use the clearest
single representation.

Attachment examples keep allocation, raw upload, and Message creation in one
workflow. WebSocket examples use the SDK's maintained connection runner and
the current `/v1/websocket` contract.

## 9. Code and response presentation

Code examples use current paths, fields, event names, and limits. Each task
keeps identifiers consistent from request through response. Credentials appear
as environment variables.

The first mutation on a page includes its canonical response when later steps
use the returned ID. Error examples include HTTP status, `error.code`, and
`trace_id`. Retry guidance names the exact idempotency or acknowledgement
boundary.

## 10. Operational safety

Developer-facing safety instructions stay next to the action they protect:

- Agent Tokens remain in server-side secret storage.
- Message retries reuse a stable idempotency key.
- Webhook receivers verify the signature and commit `event_id` before `2xx`.
- WebSocket consumers commit `event_id` before a cumulative ACK.
- Webhook destinations use direct public HTTPS endpoints.
- FULL sync completes before later WebSocket acknowledgements.
- Logs retain `trace_id` and omit credentials, signing secrets, and message
  content unless the developer explicitly needs that content.

Warnings are reserved for security, data loss, irreversible actions, and
duplicate side effects. Notes and tips carry ordinary context.

## 11. Agent-friendly treatment

Mintlify header actions expose page copy and source viewing:

```json
{
  "contextual": {
    "options": ["copy", "view"],
    "display": "header"
  }
}
```

The secondary navbar action copies `skill.md`. The primary navbar action opens
Relay Console. The Relay logo opens `https://relayapp.im`.

Review-with-an-agent blocks are used for concrete codebase audits such as
authentication, idempotency, webhook verification, durable ACK, and FULL sync.
Each prompt reads current Relay docs and OpenAPI, requests file-and-line
evidence, and reports unknown findings explicitly.

## 12. Overview pages

Overview pages orient multiple child tasks and provide the shortest useful
path through the category. Messaging, Chats, Webhooks, and WebSocket have
category overviews. Agent Events connects the two supported agent event paths.
Contacts and Platform link directly to their task pages.

## 13. API Reference and errors

The API Reference overview owns conventions shared by all endpoints. Generated
endpoint pages own request fields, response fields, status codes, and schemas.
Guides own workflows, sequencing, acceptance boundaries, and recovery.

Each Error Code page includes:

1. HTTP status and Relay error code;
2. response example;
3. corrective action;
4. retry behavior;
5. related endpoint or guide.

## 14. Page jobs

| Page | Developer job |
| --- | --- |
| Quickstart | Send a first Message and receive an agent event |
| Authentication | Store and send an Agent Token |
| Client SDKs | Install and use `@relaymessenger/sdk` |
| Key Concepts | Learn Contact, Handle, Chat, Message, part, and event |
| Sending Messages | Create or use a Chat and send ordered parts |
| Mentions | Address a Contact with UTF-16 ranges in a group Chat |
| Message Details | Retrieve a Message, thread, or Chat history |
| Attachments | Allocate, upload, retrieve, and delete media |
| Voice Memos | Upload and send audio with voice presentation |
| Rich Link Previews | Send a link part |
| Replies | Target a Message and `part_index` |
| Reactions | Add and remove a reaction on a Message part |
| Delivery Receipts | Read per-recipient state and acknowledgement boundaries |
| Group Chats | Create and update a group Chat |
| Participants | Add, remove, leave, and understand membership periods |
| Typing Indicators | Start, refresh, stop, and receive typing state |
| Sharing Contact Card | Share the configured card inside an existing Chat |
| Message History | Page through visible Message and Chat event history |
| Add requests | Let users add an agent or request a Contact from a Premium Handle |
| Contact Cards | Configure an agent's public card |
| Blocked Handles | Block, list, and unblock Handles |
| Agent Events | Select and operate an agent event path |
| Webhooks | Receive and verify signed HTTPS events |
| Webhook Subscriptions | Configure event destinations and event filters |
| Webhook Event Types | Read the versioned event envelope and payloads |
| Webhook Delivery | Implement retries and terminal handling |
| WebSocket | Connect an always-on agent backend |
| Protocol | Implement current frames, heartbeats, and close codes |
| Acknowledgements | Commit and cumulatively acknowledge events |
| FULL sync | Recover after a checkpoint falls outside retention |
| Idempotency | Retry commands without duplicate side effects |
| Rate Limits | Design around current request and content limits |
| Debugging | Use IDs, errors, and traces to diagnose requests |

## 15. Validation sequence

A documentation change passes these checks in order:

1. Relay Server and Docs OpenAPI byte comparison;
2. Mintlify OpenAPI bundle rebuild and diff;
3. agent prompt synchronization;
4. docs topology and heading inventory;
5. JSON and shell example validation;
6. Mintlify broken-link validation;
7. Mintlify site validation;
8. Mintlify accessibility validation;
9. desktop and narrow rendered inspection.

## 16. Exact heading skeletons

These outlines match the current public pages. A heading change must preserve
the page's single job and update this inventory in the same commit.

### Introduction and Getting started

| Page | H2 order |
| --- | --- |
| Introduction | `Prerequisites` → `What you can build` → `Key capabilities` → `Authentication` → `Quick example` → `Next steps` |
| Quickstart | `Prerequisites` → `1. Set your credentials` → `2. Choose the SDK or HTTPS` → `3. Create a webhook subscription` → `4. Accept the event durably` → `5. Mark Read and reply` → `Review with an agent` → `Next steps` |
| Authentication | `Credentials` → `Agent Tokens` → `WebSocket authentication` → `Errors` → `Related` |
| Client SDKs | `Install` → `Create a client` → `Send a Message` → `Resources` → `Pagination` → `Retries and idempotency` → `Errors` → `Webhook verification` → `Browser limitation` → `Runnable examples` → `Related` |
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
| Attachments | `1. Create an upload` → `2. Upload the raw bytes` → `3. Confirm the upload` → `4. Send the Attachment` → `5. Download or delete` → `Import a public media URL` → `Media metadata` → `Image formats` → `Limits` → `Ownership` → `Related` |
| Voice Memos | `Upload audio` → `Send the voice memo` → `Read the response` → `Related` |
| Rich Link Previews | `Send a link part` → `Composition rules` → `Start a Chat with a link` → `Related` |
| Replies | `Reply to a Message` → `Target a part` → `List a reply thread` → `Related` |
| Reactions | `Add a reaction` → `Reaction types` → `Remove a reaction` → `Events` → `Related` |
| Delivery Receipts | `Response fields` → `Delivered boundaries` → `Mark Read` → `Direct and group presentation` → `Related` |

### Chats and Contacts

| Page | H2 order |
| --- | --- |
| Chats | `Chat types` → `Create a Chat` → `Chat fields` → `Next steps` |
| Group Chats | `Create a group` → `Limits` → `Rename the group` → `Set a group photo` → `Group metadata events` → `Related` |
| Participants | `Add a Contact` → `Remove a Contact` → `Leave` → `Membership periods` → `Events` → `Related` |
| Typing Indicators | `Start` → `Keep typing active` → `Stop` → `Receive events` → `API reference` → `Related` |
| Sharing Contact Card | `Before sharing` → `Share the card` → `Keep configuration separate` → `Related` |
| Message History | `Pagination` → `Group-history rows` → `Membership visibility` → `Agent recovery` → `Related` |
| Add requests | `How Add works` → `Send an Add request` → `Read the response` → `Receive Contact events` → `Related` |
| Contact Cards | `How Contact Cards work` → `Retrieve the card` → `Upsert the card` → `Update the card` → `Fields` → `Sharing is separate` → `Related` |
| Blocked Handles | `Block` → `Behavior` → `List` → `Unblock` → `Related` |

### Agent events, Webhooks, and WebSocket

| Page | H2 order |
| --- | --- |
| Agent Events | `Choose a transport` → `Shared envelope` → `Switch transports` → `Recovery` → `Review with an agent` → `Related` |
| Webhooks | `Flow` → `Create a subscription` → `Verify the signature` → `Acknowledge safely` → `Review with an agent` → `Related` |
| Webhook Subscriptions | `Create` → `Store the signing secret` → `List, retrieve, update, or delete` → `Related` |
| Webhook Event Types | `List supported events` → `Envelope` → `Message events` → `Payload version` → `Reaction events` → `Chat events` → `Contact events` → `Related` |
| Webhook Delivery | `Delivery policy` → `Retry classes` → `Receiver pattern` → `Delivered meaning` → `Terminal delivery` → `Review with an agent` → `Related` |
| WebSocket | `Select WebSocket delivery` → `Connect` → `Review with an agent` → `Related` |
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
| `guides/contacts/add-requests.mdx`, `guides/contact-cards.mdx`, `guides/chats/blocked-handles.mdx` | Contacts | integrated |
| `guides/agent-events/index.mdx` | Agent events | integrated comparison hub |
| `guides/webhooks/*` | Webhooks | integrated |
| `guides/websocket/*` | WebSocket | integrated |
| `guides/platform/*` | Platform | integrated |
| `examples/index.mdx` | Examples | integrated |
| `api-reference/*` | API Reference | generated from the current OpenAPI |
| `error/*` | Error Codes | integrated one-code pages |

## 18. Release gates

A release is ready when:

- every MDX page appears once in `docs.json` navigation;
- the three top-level tabs and Guide groups match the current topology;
- page headings match the inventory below;
- TypeScript and cURL variants perform equivalent operations;
- the Docs OpenAPI is byte-identical to the approved Relay Server contract;
- the Mintlify OpenAPI bundle is reproducible;
- examples match the current API and SDK;
- generated `llms.txt` and `llms-full.txt` contain the current public pages;
- links, site validation, and accessibility checks pass;
- desktop and narrow layouts remain readable.

## 19. Final principle

Relay documentation teaches the current product from the first request through
reliable event processing. The contract defines behavior, the SDK defines
maintained TypeScript calls, and each public page explains one developer job in
simple language.
