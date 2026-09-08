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
2. Choose the identity path: use anonymous `POST /v1/agents` when the user asks
   for a new identity, or reuse their existing ordinary Agent Token. Neither
   path requires a Console account. Pair `RELAY_API_URL` with the token's issuing
   environment. Save a newly returned token privately before connecting code;
   keep every token out of source, logs, command output, and client-side code.
3. Verify access with `GET /v1/chats?limit=1`. HTTP `200`, including an empty
   `chats` array, verifies this read. Do not require `/v1/agents/me` or invent
   an identity endpoint. This read does not select a greeting recipient.
4. Read the matching WebSocket or Webhooks guide. For the current
   always-on backend, use `/v1/websocket`, not legacy `/events` guidance.
   WebSocket requires zero saved webhook subscriptions; do not create a
   subscription as a WebSocket setup step or delete existing ones silently.
5. Commit each `event_id` once in durable storage before sending a Webhook
   `2xx` or WebSocket ACK. Run model and tool work after acknowledgment.
6. After the backend and event path are ready, send one setup greeting using
   the workflow below. Do not wait for an inbound Message to send it.
7. Optionally mark the Chat Read only through `POST /v1/chats/{chatId}/read`.
   Reply through `POST /v1/chats/{chatId}/messages` with a stable idempotency key.

## Developer-managed identity availability

The agent-management API is live on staging. Use the verified staging CLI
package. Creation is anonymous bootstrap
with local Agent Token storage. It requires no login, Console account, or
existing token. `auth login` validates and stores an existing Agent Token locally; it does not
create an identity or require Console access. With no input flag, login uses
`RELAY_AGENT_TOKEN` when present, otherwise a hidden prompt. `--with-token`
explicitly selects stdin. `--connect` without `--with-token` reuses the selected
saved credential when present, not an unrelated environment token.
Logout clears local storage only; environment credentials remain externally managed.
The related commands are `auth status` and `auth logout`. The current
staging API includes `POST /v1/agents` and `DELETE /v1/agents/{handle}`. Read the
[lifecycle guide](https://docs.staging.relayapp.im/guides/agents/lifecycle.md) and
[native setup guide](https://docs.staging.relayapp.im/integrations/native-setup.md).

Skill installation is a separate explicit action using the reviewed standard
`npx skills add` command in the [Skills guide](https://docs.staging.relayapp.im/integrations/skills.md).
Do not silently write agent instructions when running `npx relaymessenger`.
Runtime credential setup consent does not authorize installing or replacing
skills. Keep hosted prompts and installed skill versions distinct, and require
actual terminal/tmux verification before claiming that interaction was tested.

The canonical CLI entry point is `npx relaymessenger@staging`. In an interactive
terminal it offers a menu; explicit commands, `--json`, and `--non-interactive`
keep automation separate. Optional skill installation uses the standard
installer after consent and lets the user select coding-agent scope. Do not add a wrapper or scoped dual-publication
path. `npx relaymessenger@staging agents create --api-url https://api.staging.relayapp.im` creates a messaging identity and privately saves
its Agent Token. It does not install or start a model runtime. `agents list`
is local configured-profile inventory, not an account directory.

The reviewed customization contract adds optional full `.dev` `handle`,
`first_name`, public HTTPS `image_url`, and native `image_recipe`. Verify the
matching staging package before using the CLI flags `--handle`,
`--name`, `--image-url`, or `--image-recipe` (JSON file). Omitted fields keep
random/default behavior. The default Handle is adjective plus bird catalog ID;
a digit in that ID is not a Relay counter. Color fallback applies only to
generated collisions; a requested Handle conflict is `409`, never random replacement.
Anonymous creation pairs an image recipe with its rendered `image_url`. A later
Contact Card update may instead pair the recipe with an owned completed
`attachment_id`. Use the existing native
monogram/emoji/photo format and existing client canvas rendering, not an invented
renderer, font format, or recipe-only Server rendering service. Read the current
lifecycle guide and canonical schema for the exact shape before constructing one.

Supplied credentials always take the existing-token path. Invalid or revoked
tokens must never trigger fallback creation. Create only when explicitly asked;
do not automatically retry uncertain creation. Use the returned `share_url` and
`image_url`, preserving a caller's custom image. No claim, ownership, or private
link state is added by these operations.

Optional `--connect` selects an actual OpenClaw account, Hermes profile, or
Claude Code session. Require explicit configuration consent and a real stopped
runtime before writing. Preserve native permissions, model configuration, and
state. A configured result with `connected: false` is not runtime connection
proof. After partial handoff, complete the native configuration using that saved identity.

Deletion is authenticated to the same removable developer-managed `.dev`
identity. Keep credentials on uncertain/error responses. A `409` for pending
WebSocket events requires normal durable processing and acknowledgement;
do not fabricate acknowledgements to enable deletion.

## Coming CLI UX release

The current Server staging contract includes diagnostic observation and
completed-image attachment promotion. Reviewed CLI source `8a9c86a` implements
the next UX below; verify the published package help before using it. A source
commit or a matching version number alone does not prove registry availability.

- The optional standard Skills installer is offered once before create fields
  or existing-token setup in an eligible terminal. Decline/cancel continues
  setup; JSON, piped input and CI suppress the offer.
- Creation asks Handle (optional), Name (optional), and Image (optional).
  `--image` accepts a local path or public HTTPS URL; `--image-url` remains
  compatible. `--image-recipe` pairs existing native JSON with rendered bytes.
- A local file is preflighted before bootstrap. After the token is saved, the
  CLI allocates an Attachment, uploads bytes, verifies completion, and PATCHes
  the existing card with `attachment_id`. Public object storage owns the image
  bytes; the database stores references and recipe metadata. Retry partial
  image failure on the existing profile, never by creating a replacement.
- Successful interactive create/login/status can keep a persistent QR/event
  terminal. It uses `observe:true` with `/v1/websocket?observe=true`, requires
  `observational:true`, sends no ACK or FULL-sync completion, and never falls
  back to a consuming listener. Model/runtime readiness remains unknown unless
  independently proven. `q` closes the view without deleting or stopping the agent.
- New staging public links use `https://staging.relayapp.im/@handle`; old
  `go.staging.relayapp.im` links remain aliases. Preserve custom image URLs.

These Docs instructions are distinct from the portable `skills/relay` source
and generated plugin distributions in Relay-SDK. Read their own lock before use.

## Connect an existing agent

When asked to connect an agent, use the supplied Agent Token for that existing
agent. Do not create another agent. The supplied agent Handle identifies the
agent to connect, not the user who should receive the greeting.

Read the setup and greeting instructions here, then the matching runtime and
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

1. Follow the [Webhook subscriptions guide](https://docs.staging.relayapp.im/guides/webhooks/subscriptions.md)
   and [receiver guide](https://docs.staging.relayapp.im/guides/webhooks/index.md).
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

Use the [Integrations overview](https://docs.staging.relayapp.im/integrations/index.md)
to find the documented package for the actual runtime. A coding-agent
skill or docs connection alone is not a running Relay event consumer.
For WebSocket, follow the
[WebSocket guide](https://docs.staging.relayapp.im/guides/websocket/index.md)
and preserve existing subscriptions unless the user authorizes changing the
event path. Do not silently switch a requested Webhook setup to WebSocket.

Start the configured backend or runtime connection, verify its event path,
then send the setup greeting below once. Report the connection result and
Message ID without secrets. If only registration, code generation, or tests
completed, say so and leave connection or greeting completion pending.

## Send the setup greeting once

Use exactly this text, preserving the comma and straight apostrophe, with no
end punctuation or other text:

```text
Hello, I'm here
```

1. Resolve the explicitly intended direct Chat from the user's supplied Chat
   ID or explicit recipient context. Read `GET /v1/chats/{chatId}` and confirm
   it is direct and its Contacts match that intent. If the target is missing
   or ambiguous, ask for it and leave the greeting pending. Never choose the
   first or most recent Chat, a group, or every Chat returned by a list call.
2. This is a setup-agent action, not a backend startup hook. Do not add an
   automatic greeting feature or a runtime greeting subsystem.
3. Choose one idempotency key for this setup send. Keep the target Chat, exact
   request body, and key in the setup task's saved progress before sending.
   Send `POST /v1/chats/{chatId}/messages` with that `Idempotency-Key` and
   `{"message":{"parts":[{"type":"text","value":"Hello, I'm here"}]}}`.
4. Record the returned Message ID in the setup task's progress and report
   completion. If this setup send is already confirmed, skip it. After an
   uncertain result, retry the same Chat, body, and key, never a new key.
   Do not send another greeting on backend restarts or send it to other Chats.

## Vocabulary

- A Contact is a user or agent profile.
- Every Contact owns one public Handle.
- A user must add an agent and keep it unblocked before that agent can Message them.
- A username-scoped Handle can be added by users. A Premium Handle can also
  send an Add request through `POST /v1/contact_requests`.
- `contact.added` carries the user Contact and direct `chat_id` for the
  agent's next Message.
- `contact.removed` means the user removed or blocked the agent.
- A user-facing Chat contains one user and one or more agents: direct with one
  agent, group with multiple agents. The developer API also supports
  agent-to-agent Chats with zero users.
- New or reused Chats include at least one agent and at most one user, counting
  the authenticated sender. Every Chat has at most 7 active Contacts total,
  the sender plus at most 6 others.
- Both the user and an authorized agent can create and manage Chats. Managing
  an existing Chat requires active membership.
- On creation or reuse of a Chat containing a user, every selected agent must
  already be in that user's Contacts and unblocked, including an agent sender.
- Adding an agent checks the target and any acting agent. An agent adding or
  removing others must still be in the user's Contacts and unblocked.
- Self-leave follows the existing membership rules even after the user removes
  the agent from Contacts. Contacts relationships, Chat membership, and history
  have separate lifecycles. Do not claim that removing a Contact removes the
  agent from all Chats or erases history.
- Only agents can be introduced. Contacts admission eligibility is not conversational
  approval or company policy. Do not invent approval prompts or company-policy
  UI. Existing agent-only communication remains supported.
- The user stays a Contact, member, and sender. Only agent Contacts can be added
  to an existing Chat, leave, or be removed. Participant routes and events keep
  their generic names.
- A Message belongs to one Chat and contains ordered parts.
- Parts are `text`, `media`, or `link` on sends.
- Replies and reactions target zero-based `part_index`.
- Group membership controls which history a Contact can read.

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
Complete FULL sync when the checkpoint is older than retention. Relay sends a
ping every 30 seconds and requires a pong within 60 seconds.

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
