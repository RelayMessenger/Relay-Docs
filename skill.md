---
name: relay
description: Integrate an agent backend with the Relay API v1 and signed webhooks.
---

# Relay developer integration

Relay is the messenger. The backend owns the model, tools, memory, and behavior.

1. Set the API root to `https://api.relayapp.im`.
2. Use an Agent Token as a bearer credential.
3. Create `POST /v1/webhook-subscriptions`.
4. Verify Standard Webhooks over the exact raw body.
5. Deduplicate on `event_id`, save the event, then return `2xx`.
6. Treat a successful `message.received` response as Delivered for that agent.
7. Call `POST /v1/chats/{chatId}/read`.
8. Reply with `POST /v1/chats/{chatId}/messages`.

Relay has one `/v1` API. Authentication determines whether the caller is a user or agent. There is no business-role URL namespace, client-role URL namespace, or realtime endpoint.

`Contact` owns `kind`, name, and image. `kind` is `user` or `agent`. Better Auth owns the user account. `Handle` is the Relay username used to address a Contact. No resource carries a transport discriminator.

Message `parts` are ordered projections of Apple's `attributedBody`. Text can carry a mention. Media carries image, video, audio, or file bytes. A link is one URL balloon. Replies and reactions target zero-based `part_index`.

Agents receive new Messages through webhooks. HTTP reads reconcile known resources. The Relay app reconciles through finite HTTP lifecycle triggers. Realtime transport is deferred.
