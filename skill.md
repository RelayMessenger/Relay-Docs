---
name: relay
description: Build a Relay agent backend with the v1 API, webhooks, or Socket Mode.
---

# Relay developer integration

Relay is the messenger. The agent backend owns its model, tools, memory, and behavior.

## Start

1. Read `https://docs.relayapp.im/llms.txt` and the current OpenAPI.
2. Set the API root to `https://api.relayapp.im`.
3. Store the Agent Token in server-side secret storage.
4. Choose signed webhooks or agent-only Socket Mode.
5. Commit each `event_id` under a uniqueness rule before webhook `2xx` or Socket Mode ACK.
6. Run model and tool work after acknowledgement.
7. Mark the Chat Read when the agent actually reads it.
8. Reply through `POST /v1/chats/{chatId}/messages` with a stable idempotency key.

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

## Do not invent

- No partner or mobile URL namespace
- No polling
- No typing API
- No reply-over-socket frame
- No service discriminator
- No unregistered phone-only recipient

Use the OpenAPI for exact fields, limits, and errors. Mark anything not proved by the docs or contract as unknown.
