---
name: relay
description: Build a Relay Messenger agent backend with the v1 API, Webhooks, or WebSocket.
---

# Relay Messenger developer integration

Relay Messenger carries Messages between users and agents. The agent backend
owns its model, tools, memory, and behavior.

## Start

1. Read `https://docs.relayapp.im/llms.txt` and the current OpenAPI.
2. Read the Agent Events guide before choosing a backend shape.
3. Set `RELAY_API_URL` for the target environment and use a matching Agent Token.
4. Store the Agent Token in server-side secret storage.
5. Save a webhook subscription for Webhook delivery, or save none and connect by WebSocket.
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

## Event path

| Saved configuration | Agent event path |
| --- | --- |
| At least one webhook subscription | Webhook only |
| No webhook subscriptions | WebSocket only |

There is no mode, toggle, or transport setting. Relay never sends one event
through both paths.

Creating the first subscription closes connected agent sockets and drains
pending events to Webhooks. Deleting the last drains pending events to
WebSocket. With no subscription and no connection, events wait durably for up
to 30 days.

A WebSocket upgrade while any subscription exists returns HTTP `409`. Pending
events keep the same `event_id` across path changes.

## Event acceptance

```text
verify → deduplicate event_id → durable commit → 2xx or ACK → process
```

Acknowledgement does not mean bytes received, handler start, model completion,
reply, or Read.

Webhook retries can repeat an `event_id`. Reject webhook destinations that
resolve to localhost, private, link-local, or cloud metadata addresses. Never
follow redirects.

WebSocket ACKs are cumulative. Recover with replay or FULL sync after a stale
checkpoint. Relay pings every 30 seconds and requires a pong within 60
seconds.

The shared `/v1/websocket` path uses authentication to distinguish user and
agent connections. Agent backends authenticate the upgrade with
`Authorization: Bearer <Agent Token>`.

Use the SDK WebSocket directly during local development. The `relay listen`
command is deleted.

## Canonical contract

- Call the `/v1` paths defined by the current OpenAPI.
- Send Message commands through REST.
- Treat registered Handles as public messaging addresses.
- Treat every inbound `event_id` as at-least-once.
- Recover current state with ordinary REST reads or WebSocket FULL sync.
- Use a staging API root and staging Agent Token together during staging tests.

Use the OpenAPI for exact fields, limits, and errors. Mark anything not proved
by the docs or contract as unknown.
