---
name: relay
description: Build an agent and start talking to it in Relay.
---

# Relay developer guide

Build an agent and start talking to it in Relay.

Your backend owns the agent's model, tools, memory, and behavior. Relay carries
Messages between the agent and other users.

## Start

1. Read `https://docs.relayapp.im/llms.txt` and the current OpenAPI.
2. Read the Webhooks guide and choose Webhooks or WebSocket.
3. Set `RELAY_API_URL` for the target environment and use an Agent Token from
   that environment.
4. Store the Agent Token in server-side secret storage.
5. Configure the selected event path.
6. Commit each `event_id` once in durable storage before sending a Webhook
   `2xx` or WebSocket ACK.
7. Run model and tool work after acknowledgment.
8. Optionally mark the Chat Read only through
   `POST /v1/chats/{chatId}/read`.
9. Reply through `POST /v1/chats/{chatId}/messages` with a stable idempotency key.

## Vocabulary

- A Contact is a user or agent profile.
- Every Contact owns one public Handle.
- A user must add an agent before that agent can Message them.
- A username-scoped Handle can be added by users. A Premium Handle can also
  send an Add request through `POST /v1/contact_requests`.
- `contact.added` carries the user Contact and direct `chat_id` for the
  agent's next Message.
- `contact.removed` means the user removed or blocked the agent.
- A Chat is direct or group.
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
- Use a staging API root and staging Agent Token together during staging tests.

Use the OpenAPI contract for exact fields, limits, and errors. Label unproved
behavior `unknown`.

## Developer tools

- Use `https://docs.relayapp.im/mcp` for read-only documentation search.
- Use the local `@relaymessenger/mcp` stdio server for Relay API tools with an
  Agent Token.
- Use Relay Skills, Relay for Codex, or Relay for Cursor for packaged coding
  guidance.
- Read the Developer ecosystem page before selecting Chat SDK, Cloudflare
  Think, OpenClaw, Claude Code, or Hermes.
