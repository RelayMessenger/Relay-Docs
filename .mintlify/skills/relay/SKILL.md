---
name: relay
description: Integrate an agent backend with Relay Partner API v3 and signed webhooks.
---

# Relay developer integration

Relay is the messenger. The backend owns the model, tools, memory, and behavior.

1. Set the API root to `https://api.relayapp.im/api/partner`.
2. Use an Agent Token as a bearer credential.
3. Create `POST /v3/webhook-subscriptions`.
4. Verify Standard Webhooks over the exact raw body.
5. Deduplicate on `event_id`, save the event, then return `2xx`.
6. Treat a successful `message.received` response as Delivered for that agent.
7. Call `POST /v3/chats/{chatId}/read`.
8. Start typing with `POST /v3/chats/{chatId}/typing`.
9. Reply with `POST /v3/chats/{chatId}/messages`.
10. Stop typing with `DELETE /v3/chats/{chatId}/typing`.

`Contact` owns `kind`, name, and image. `kind` is `user` or `agent`.
Better Auth owns the user account. `Handle` is the Relay username used to
address a Contact. Every Relay chat, message, and handle has `service: "Relay"`.

Message `parts` are ordered projections of Apple's `attributedBody`. Text can
carry a mention. Media carries image, video, audio, or file bytes. A link is
one URL balloon. Replies and reactions target zero-based `part_index`.

Agents receive new messages through webhooks. HTTP reads reconcile known
resources. User mobile clients reconcile through HTTP after startup,
foreground, reconnect, or a hint-only WebSocket signal.
