---
name: relay
description: Integrate an agent backend with Relay using signed webhooks and idempotent REST writes.
---

# Relay developer integration

Relay is the messenger. The backend owns the model, tools, memory, and behavior.

1. Use an existing Agent Token and verify `GET /v1/agents/me`.
2. Create `POST /v1/webhook-subscriptions` with `Idempotency-Key`.
3. Verify Standard Webhooks over the exact raw body.
4. Deduplicate on `event_id`, store durably, then return `2xx`.
5. Successful `message.received` delivery records Delivered.
6. Call `POST /v1/chats/{chat_id}/read` with `through_message_id`.
7. Start typing with bodyless `POST /v1/chats/{chat_id}/typing`.
8. Reply with `POST /v1/chats/{chat_id}/messages` and a stable key.
9. Stop typing with `DELETE /v1/chats/{chat_id}/typing`.

IDs are server-assigned UUIDv7. One send creates one immutable message. Input parts are text, image, file, audio, and link. History is newest first and cursor-paged. Token issuance, agent creation, SDKs, CLI, developer polling, and developer Socket Mode are outside this contract.
