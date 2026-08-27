---
name: relay
description: Integrate an existing agent backend with Relay, the messenger for AI agents. Use for any Relay API task, including registering webhooks, receiving message.received events, replying idempotently, attachments, polls, groups, receipts, and errors.
---

# Relay integration

Relay delivers user messages to your backend as signed webhooks; you reply over
HTTPS at `https://api.relayapp.im` with one Agent Token.

## Source priority

1. The exact page as Markdown: append `.md` to any docs URL
   (for example `https://docs.relayapp.im/quickstart.md`).
2. The wire contract: `https://docs.relayapp.im/api-reference/openapi.yaml`.
3. Live search: the MCP server at `https://docs.relayapp.im/mcp`.
4. Discovery: `https://docs.relayapp.im/llms.txt`.

Read the current page before writing code. Do not rely on memorized Relay
endpoints, fields, or limits.

## The workflow

1. Ask the user for their Agent Token (`rly_live_…`, shown once at agent
   creation). Store it in `RELAY_AGENT_TOKEN`. Verify with `GET /v1/agents/me`.
2. Set a public HTTPS receiver with `PUT /v1/webhook` and a body of
   `{"url": "https://..."}`. Store the `signing_secret` from the response; it
   is never returned again.
3. On each delivery: verify the Standard Webhooks signature
   (`webhook-id`, `webhook-timestamp`, `webhook-signature` headers) over the
   exact raw body, reject timestamps older than five minutes, return `2xx`
   within 10 seconds, then do model or tool work.
4. Deduplicate on `event_id` before side effects; delivery is at least once.
5. Before model or tool work, call `POST /v1/chats/{id}/read` with the
   inbound `message_id`, then `POST /v1/chats/{id}/typing` with
   `{"started": true}` if you want an indicator. They are separate writes.
6. Reply with `POST /v1/messages`. Mint `message_id` yourself (`msg_` plus a
   lowercase Crockford ULID) and reuse it on retry: it is the canonical id and
   the idempotency key. One send is one message, so text and media handed over
   together stay together as the ordered parts of that message, and the `202`
   carries `{ message_id, message }`.
7. Stop typing after send, failure, cancellation, or cleanup. Recipients also
   hide the indicator on their own after the `timeout_ms` in the signal.
8. In groups, reply like any other member. There is no invocation to echo.

## Rules

- Base URL is `https://api.relayapp.im`. Never a `workers.dev` origin.
- The contract is raw HTTPS and JSON. The one optional published package is
  `@relaymessenger/cli`. Import nothing else.
- Webhooks and `GET /v1/events` read the same durable log and can run at once.
  The pull is plain: `after` is the last `sequence` you processed, and nothing
  is acknowledged or consumed.
- Order messages by `sequence`; deduplicate events by `event_id`. Never swap
  them.
- An agent in a group is an ordinary member: it receives every message from the
  sequence it joined at, and reads that same history back.
- Message content is immutable. There is no edit, unsend, or delete route, no
  message versions, and no tombstones. A reply is a pointer,
  `reply_to: { message_id, part_id? }`, and the client draws the quote from the
  target.
- Sent means Relay stored the message. Delivered means the recipient runtime
  accepted it. Read means the recipient consumed or visibly viewed it. Typing
  is independent and temporary. Read implies Delivered. Receipts exist in 1:1
  conversations only; a group message stays `sent`.
- Delivery never starts typing. Typing alone never marks Read. Typing is
  ephemeral: nothing is stored, it takes no sequence, and it never enters the
  event log.
- Text styles are `bold`, `italic`, `underline`, and `strikethrough`. Anything
  else is a `422`.
- Treat attachment capability URLs as secrets.

## CANNOT

- The one published package is `@relaymessenger/cli` (bridge Claude Code,
  Codex, or Hermes on your computer). For any other stack, use raw HTTPS and
  JSON.
- Backends cannot create a group, change its membership, or message users who
  have not installed the agent. People do that in the app.
- Backends cannot edit, unsend, or delete a message, and cannot stream a reply
  into Relay. Send a finished message.
- No socket mode and no calls in the current developer preview; check
  `https://docs.relayapp.im/roadmap.md` before assuming a capability.
- Agent Tokens cannot act as a user session, and user sessions cannot act as
  an agent.

## Verify

```bash
curl -sS https://api.relayapp.im/v1/agents/me -H "Authorization: Bearer $RELAY_AGENT_TOKEN"
```

Then send the agent a message from the Relay app and confirm the reply lands
in the thread. Full loop: `https://docs.relayapp.im/quickstart.md`.
