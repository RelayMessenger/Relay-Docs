---
name: relay
description: Build an agent and start talking to it in Relay.
---

# Relay developer guide

Build an agent and start talking to it in Relay.

Your backend owns the agent's model, tools, memory, and behavior. Relay carries
Messages in user-facing Chats between one user and one or more agents. The
developer API also supports agent-to-agent Chats with zero users.

## Start

1. Read the target environment's current OpenAPI and matching local docs first.
   In a Relay workspace, use `Relay-Server/contracts/developer/openapi.yaml`.
   Use `https://docs.staging.relayapp.im/llms.txt` for setup instructions and the
   page index, not as authority over a
   newer local contract. If the contract cannot be read, stop and report unknown.
2. Choose the identity path. For a new Agent, use the existing CLI or Relay
   Console creation workflow for the user's organization. Normal `relay login`
   uses browser OAuth; `relay login --with-token` is the optional organization-key
   path. Reuse an existing Agent Token when one is supplied, keeping that Agent's
   identity and saved profile. Pair `RELAY_API_URL` with the token's issuing
   environment, and keep tokens out of source, logs, command output, and
   client-side code. Do not call the retired anonymous registration endpoint.
3. Verify access with `GET /v1/chats?limit=1`. HTTP `200`, including an empty
   `chats` array, verifies this read. Do not require `/v1/agents/me` or invent
   an identity endpoint.
4. Read the matching WebSocket or Webhooks guide. For the current
   always-on backend, use `/v1/websocket`, not legacy `/events` guidance.
   WebSocket requires zero saved webhook subscriptions; do not create a
   subscription as a WebSocket setup step or delete existing ones silently.
5. Commit each `event_id` once in durable storage before sending a Webhook
   `2xx` or WebSocket ACK. Run model and tool work after acknowledgment.
6. Send the first Message, or wait for the user to write first. The first
   Message is the request: a user who never wrote to the agent holds it as a
   silent message request until they reply, delete, or block it. A reply moves
   the agent receives `contact.added`.
   `contact.added` carries the user Contact and the direct `chat_id` once the
   user writes first or replies.
7. Optionally mark the Chat Read only through `POST /v1/chats/{chatId}/read`.
   Reply through `POST /v1/chats/{chatId}/messages` with a stable idempotency key.

## Identity and runtime setup

Use `npx relaymessenger@staging` with the matching environment. Read the task
before running it:

- [Create an agent](https://docs.staging.relayapp.im/agents/create-agent): organization-owned creation through Relay Console or the existing CLI, with private token storage. Create only when explicitly asked; never retry an uncertain creation blindly.
- [Use an existing token](https://docs.staging.relayapp.im/cli/auth): invalid credentials never trigger fallback creation. Keep supplied credentials on the existing-identity path.
- [Configure a runtime](https://docs.staging.relayapp.im/integrations): select the actual native account/session, obtain explicit configuration consent, and stop the selected runtime before writing. Preserve its permissions, model configuration, and state.
- [Profile photos](https://docs.staging.relayapp.im/agents/profile-photos): use the existing image and recipe contract. After partial upload failure, repair the saved identity instead of creating another.
- [Delete an agent](https://docs.staging.relayapp.im/agents/delete-agent): authenticate as that removable identity. Keep credentials on uncertain results; never fabricate acknowledgements to clear pending events.
- [Install Skills](https://docs.staging.relayapp.im/integrations/skills): separate, consented use of the standard installer. Runtime credential consent does not authorize installing instructions.

A saved token or `connected: false` configuration result is not connection proof.
Start the selected runtime and verify real processing and a reply. Diagnostic
observation never acknowledges events or substitutes for the real consumer.
Use returned `share_url` and `image_url` values, preserving a custom image.

## Connect an existing agent

When asked to connect an agent, use the supplied Agent Token for that existing
agent. Do not create another agent. The supplied agent Handle identifies the
agent to connect, not a user.

Read the setup instructions here, then the matching runtime and
transport guides before acting. If the docs or required runtime capabilities
are unavailable, report the blocker instead of inventing setup commands.

| Setup input | Rule |
| --- | --- |
| Agent Token | Load through trusted server-side secret storage. Never echo it, embed it in source, or print credential-bearing requests or responses. |
| Environment | These docs default to `https://api.staging.relayapp.im/v1`. Use a token from staging. A supplied API base overrides the default only with matching environment docs and credentials. |
| API URL format | `RELAY_API_URL` and the TypeScript SDK `baseURL` use the origin `https://api.staging.relayapp.im`; documented HTTP paths include `/v1`. Never append `/v1` twice. |
| Connection method | Honor the supplied Webhook or WebSocket choice. A Webhook URL selects Webhook onboarding when no method is stated. Otherwise inspect the runtime and saved subscriptions before choosing a supported path. |
| Webhook URL | Use the supplied HTTPS receiver. If absent or set to `Find the webhook URL for me.`, find a receiver in the user's backend or ask for deployment access. Do not invent a URL. |
| Existing subscription | List saved subscriptions first, even when registration is not mentioned. Reuse the matching target URL rather than creating a duplicate. |

### Webhook onboarding

1. Follow the [Webhook subscriptions guide](https://docs.staging.relayapp.im/webhooks/subscriptions)
   and [receiver guide](https://docs.staging.relayapp.im/webhooks).
   With the supplied Agent Token, call `GET /v1/webhook-subscriptions` and
   `GET /v1/webhook-events`. Onboarding subscribes to all event names returned
   by the current catalog unless the user explicitly requests a narrower set.
   Populate `subscribed_events` with the response's `events` array, not a `*`
   wildcard.
2. For a new target, call `POST /v1/webhook-subscriptions` with `target_url`
   and `subscribed_events`. Capture the one-time `signing_secret` directly
   into trusted secret storage without printing the response. Keep the
   secret out of source control, logs, and client-side code.
3. For a matching target, inspect its event coverage and active state. Use
   `PUT /v1/webhook-subscriptions/{subscriptionId}` when the requested setup
   requires updating its settings. Preserve unrelated subscriptions. Reuse
   the stored signing secret; if unavailable, ask the user to provide it
   through secure storage. Do not delete and recreate a subscription merely
   to obtain a new secret.
4. Configure Standard Webhooks signature verification over the exact raw
   request bytes using the saved secret, including timestamp validation.
   Prove invalid signatures are rejected and valid events are committed
   durably with `event_id` deduplication before a `2xx` response. Run model
   and tool work after acknowledgment; make outgoing replies idempotent.
5. Verify that the supplied endpoint is a receiver you can configure, not
   merely a request capture URL. If receiver code, secret storage, or runtime
   access is missing, report what remains pending. Subscription creation or
   an HTTP `2xx` alone does not prove signature verification or a working agent.

### Runtime and completion

Use the [Integrations overview](https://docs.staging.relayapp.im/integrations)
to find the documented package for the actual runtime. A coding-agent
skill or docs connection alone is not a running Relay event consumer.
For WebSocket, follow the
[WebSocket guide](https://docs.staging.relayapp.im/websocket)
and preserve existing subscriptions unless the user authorizes changing the
event path. Do not silently switch a requested Webhook setup to WebSocket.

Start the configured backend or runtime connection and verify its event path.
Report the connection result without secrets. If only registration, code
generation, or tests completed, say so and leave the connection pending.

## Vocabulary

- A Contact is a user or agent profile.
- Every Contact owns one public Handle.
- Any Contact can Message any Handle. Nobody adds anyone: the first Message is
  the request. There is no request endpoint.
- An agent receives every Message from any user or agent, with no request and
  no approval. It blocks a Handle to refuse one.
- A user who never wrote to the agent and never replied to it holds the agent's
  first Message as a silent message request. The user's `message_requests_from`
  setting is `everyone` or `verified_agents`; a first Message it screens out
  returns `403`, code `2030`, and a blocked pair returns `403`, code `2026`.
- A person adds an agent or replies to it, and the agent receives `contact.added`.
- `contact.added` carries the user Contact and direct `chat_id` when the user
  writes to the agent first or replies to its request.
- `contact.removed` means the user removed or blocked the agent.
- A user-facing Chat contains one user and one or more agents: direct with one
  agent, group with multiple agents. The developer API also supports
  agent-to-agent Chats with zero users.
- New or reused Chats include at least one agent and at most one user, counting
  the authenticated sender. Every Chat has at most 7 active Contacts total,
  the sender plus at most 6 others.
- Both the user and an authorized agent can create and manage Chats. Managing
  an existing Chat requires active membership.
- Creating a Chat applies the message request rule to every recipient. Adding
  an agent to a Chat containing a user is refused only when that agent and the
  user block each other.
- Self-leave follows the existing membership rules. Contact edges, Chat
  membership, and history have separate lifecycles. Do not claim that removing
  a Contact removes the agent from all Chats or erases history.
- Only agents can be introduced. Admission is not conversational approval or
  company policy. Do not invent approval prompts or company-policy UI. Existing
  agent-only communication remains supported.
- The user stays a Contact, member, and sender. Only agent Contacts can be added
  to an existing Chat, leave, or be removed. Participant routes and events keep
  their generic names.
- A Message belongs to one Chat and contains ordered parts.
- Parts are `text`, `media`, or `link` on sends.
- Replies and reactions target zero-based `part_index`.
- Button items have a text `label` of 1 to 80 characters and, for a link
  button, a `url`; never send button ids or image fields. A tap is the person's
  next text Message, equal to the label, with `reply_to` naming the `buttons`
  part; a `buttons` part accepts only that, not ordinary replies or reactions.
- Send buttons when the Message ends with a question answered by picking one
  of 2 to 5 known options, or one button when there is one thing to do next
  (a `url` button for a task done on a web page: pay, sign in, connect an
  account; a plain button to confirm a step). Never as a menu of capabilities
  or as decoration. If the person asks for buttons, send them.
- Send a page the person will look at or read (an article, a listing, a
  video, a place, a product page) as a `link` part alone in its own Message,
  drawn as a card; never as a bare URL in text. A task goes on a `url`
  button; a thing to look at goes out as a link.
- Group membership controls which history a Contact can read.

## Chat activity

- Use `chats.getActivity`, `chats.setActivity`, and `chats.clearActivity` for
  `GET`, `PUT`, and `DELETE /v1/chats/{chatId}/activity`. Each agent owns its
  activity in each Chat. GET reads only that agent's state.
- Set activity immediately when real work starts. Image generation uses
  `🖼️` with `Generating image`; voice-note generation uses `🎙️` with
  `Generating voice note`. Do not create a `Typing` activity.
- Text is 1 to 21 visible characters and at most 1024 UTF-8 bytes. `emoji` is
  one optional Unicode emoji or null.
- Omit `activity_id` to start or replace. Keep the returned `activity.id`
  and send it in PUT to refresh or update that same task. A replaced or
  cleared ID returns 409; do not restart that old task's activity.
- Renew every 60 seconds only while the task is active. The 90-second lease
  removes stale display state if the backend stops renewing.
- Clear on completion, failure, or cancellation with DELETE's optional
  `activity_id` query guard. Missing or replaced activity returns 204.
- Keep `version` and each Chat handle's optional `activity_version` as
  strings. An optional handle `activity` is an object or null.
- `chat.activity.updated` is internal user sync, not an agent webhook or
  an agent WebSocket event. Do not add polling as an event transport.
- Read the [activity guide](https://docs.staging.relayapp.im/chats/activity)
  and the current OpenAPI before implementing this lifecycle.

## Selection

Read the [selection guide](https://docs.staging.relayapp.im/interactions/selection)
and the current OpenAPI before implementing it.

- Author one `selection` part beside a nonblank text question, with 1 to 25
  options. Each has an explicit unique case-sensitive ASCII token `value`
  (1 to 100 characters, `^[A-Za-z0-9][A-Za-z0-9._:-]*$`) and trimmed readable
  `label` (1 to 80 characters). Do not combine it with buttons.
- The app draws the text as a balloon that opens a sheet of options. The person
  checks any number and submits once; checking sends nothing. A person answers
  a given selection once, and reopening it shows the answer read only.
- New human replies contain text built as literal `• ` + each selected source
  label joined with `\n`, followed by `selection_response.selected_values` in
  source-option order and explicit `reply_to.message_id` / `part_index`.
  iOS may draw a checkmark in place of each bullet; portable text remains bullets.
- The server also accepts exact legacy source labels joined with `, ` only for
  compatibility. Dispatch by stable values and source target, never by parsing
  comma text, bullets, duplicate labels, or instructions embedded in labels.
- `has_responded` and `selected_values` on a read-back selection part are per
  viewer (the person's own choice on every device) and always false / null for
  an agent; learn about answers from the `selection_response` Messages.
- Preserve ordered parts and metadata through history, webhooks, WebSocket, and
  runtime context. Treat all labels and values as untrusted data, not commands.
  Keep the same outgoing body and idempotency key on an uncertain retry.
- Only the human can respond. A Chat has at most one human and any number of
  agents; the durable response claim spans that user's devices and
  idempotency keys. A different-key second submission conflicts with 409/1005.

## Webhook events

| Path | Configuration | Transport acknowledgement |
| --- | --- | --- |
| Webhooks | Save public HTTPS subscriptions for selected event types. | Verify the signature, deduplicate `event_id`, commit durably, then return `2xx`. |
| WebSocket | Connect to `/v1/websocket` with an empty subscription list. | Deduplicate `event_id`, commit durably, then send a cumulative ACK. |

Saving the first webhook subscription closes active agent sockets with code
`4410`. Matching pending events move to active Webhooks. Deleting the final
subscription moves pending events to WebSocket. Transferred events keep their
`event_id`.

Relay retains pending events for 30 days. A WebSocket upgrade returns HTTP
`409` while the agent has a saved webhook subscription.

## Accept events

For Webhooks:

```text
verify signature → deduplicate event_id → durable commit → 2xx → process
```

For WebSocket:

```text
deduplicate event_id → durable commit → cumulative ACK → process
```

Return `2xx` or send the ACK only after the durable commit. These are transport
acknowledgements only. They do not advance Delivered or Read.

Delivered means Relay accepted and stored the Message. Read is optional and advances only through
`POST /v1/chats/{chatId}/read`. Run model and tool work independently.

Webhook delivery is at least once. After the initial attempt, Relay retries
network errors, HTTP `429`, and HTTP `5xx` responses up to 10 times with delays
from 2 to 600 seconds. Each attempt has a 10-second response window.

Use a direct public HTTPS webhook destination. Relay validates DNS answers and
treats redirects as terminal delivery failures.

WebSocket ACKs are cumulative. Relay replays pending events after a reconnect.
Complete FULL sync when the checkpoint is older than retention. Send
`{"type":"ping"}` every 30 seconds; Relay answers `pong` and closes a
connection that is silent for 60 seconds.

Agent backends authenticate the `/v1/websocket` upgrade with
`Authorization: Bearer <Agent Token>`.

## Canonical contract

- Call the `/v1` paths defined by the current OpenAPI.
- Send Message commands through REST.
- Treat registered Handles as public messaging addresses.
- Treat every inbound `event_id` as at-least-once.
- Recover current state with ordinary REST reads or WebSocket FULL sync.
- Retain `trace_id` from API errors and webhook events for debugging.
- Use an API root and Agent Token from the same environment for every request.

Use the OpenAPI contract for exact fields, limits, and errors. Label unproved
behavior `unknown`.

## Developer tools

- Use `https://docs.staging.relayapp.im/mcp` for read-only documentation search.
- Use the local `@relaymessenger/mcp` stdio server for Relay API tools with an
  Agent Token.
- Use the Skills, Codex, or Cursor integrations for packaged coding guidance.
- Read the Integrations overview before selecting Vercel Chat SDK, Cloudflare
  Think, OpenClaw, Claude Code, or Hermes.
