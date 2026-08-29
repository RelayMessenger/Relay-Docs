---
name: relay
description: Build a Relay agent backend with the v1 API, webhooks, or WebSocket.
---

# Relay developer integration

Relay is the messenger. The agent backend owns its model, tools, memory, and behavior.

## Start

1. Read `https://docs.relayapp.im/llms.txt` and the current OpenAPI.
2. Set the API root to `https://api.relayapp.im`.
3. Store the Agent Token in server-side secret storage.
4. Use signed webhooks by default, or enable agent-only WebSocket as the alternate.
5. For WebSocket, upgrade `wss://api.relayapp.im/v1/websocket` with `Authorization: Bearer <Agent Token>`.
6. Commit each `event_id` under a uniqueness rule before webhook `2xx` or WebSocket ACK.
7. Run model and tool work after acknowledgement.
8. Mark the Chat Read when the agent actually reads it.
9. Reply through `POST /v1/chats/{chatId}/messages` with a stable idempotency key.

## Vocabulary

- A Contact is a user or agent profile.
- Every Contact owns one public Handle.
- A Chat is direct or group.
- A Message belongs to one Chat and contains ordered parts.
- Parts are `text`, `media`, or `link` on sends.
- Replies and reactions target zero-based `part_index`.
- Group membership controls which history a Contact can read.

## Event acceptance

```text
verify → deduplicate event_id → durable commit → 2xx or ACK → process
```

Acknowledgement does not mean bytes received, handler start, model completion, reply, or Read.

Relay sends events through one selected transport, not both. Pending events
keep the same `event_id` when the transport changes. Every event uses the fixed
`webhook_version` value `2026-02-03`.

Typing uses `POST` and `DELETE /v1/chats/{chatId}/typing`. Agent transports
receive `chat.typing_indicator.started` and
`chat.typing_indicator.stopped`; both payloads identify the authenticated
`contact`.

## Do not invent

- No partner or mobile URL namespace
- No public polling or redrive API
- No reply payload in WebSocket ACK frames
- No service discriminator
- No unregistered phone-only recipient

Use the OpenAPI for exact fields, limits, and errors. Mark anything not proved by the docs or contract as unknown.
