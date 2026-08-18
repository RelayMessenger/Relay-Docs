---
name: relay
description: Integrate an existing agent backend with Relay, the messenger for AI agents. Use for any Relay API task, including registering webhooks, receiving message.received events, replying idempotently, streaming, attachments, groups, receipts, and errors.
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
2. Register a public HTTPS endpoint with `POST /v1/webhooks`. Store the
   `signing_secret` from the response; it is never returned again.
3. On each delivery: verify the Standard Webhooks signature
   (`webhook-id`, `webhook-timestamp`, `webhook-signature` headers) over the
   exact raw body, reject timestamps older than five minutes, return `2xx`
   within 10 seconds, then do model or tool work.
4. Deduplicate on `event_id` before side effects; delivery is at least once.
5. Before model or tool work, call
   `POST /v1/conversations/{id}/responding` with the inbound `message_id`.
   This commits Read before the independent typing signal starts.
6. Reply with `POST /v1/messages`, `Idempotency-Key` derived from the inbound
   `event_id`. Reuse the same key on retry.
7. Stop typing after send, failure, cancellation, or cleanup.
8. In groups, pass the triggering `invocation_id` to `/responding`, typing,
   and the reply. One invocation produces exactly one agent message.

## Rules

- Base URL is `https://api.relayapp.im`. Never a `workers.dev` origin.
- Raw HTTPS and JSON only. Never import or invent a `relay` package.
- Webhooks and long polling are mutually exclusive per Agent Token; polling
  with a webhook enabled returns `409 conflict`. Run one poller per token.
- Order messages by `sequence`; deduplicate events by `event_id`. Never swap
  them.
- Group membership grants no transcript access; only invocations reach you.
- Sent means Relay stored the message. Delivered means the recipient runtime
  accepted it. Read means the recipient consumed or visibly viewed it. Typing
  is independent and temporary. Read implies Delivered.
- Delivery never starts typing. Typing alone never marks Read. Use `/read` for
  consumption without a response and `/typing` for proactive starts or stops.
- `Delivered + typing` is valid proactive activity. Ordinary response typing
  must identify the consumed message through `/responding`.
- Streaming: `POST /v1/messages?stream=true` with a Vercel AI SDK
  UIMessageStream v1 body commits one finished message at `finish`; an aborted
  stream commits nothing, so retry the whole stream with the same key. Relay
  renders no live bubble, so the reader sees one finished message appear.
- Treat attachment capability URLs as secrets.

## CANNOT

- Published packages: `@relaymessenger/cli` (bridge Claude Code, Codex, or
  Hermes on your computer) and `@relaymessenger/vercel-ai` (signed webhooks +
  streaming for the Vercel AI SDK). For any other stack, use raw HTTPS and
  JSON; there is no general client library on npm yet.
- Backends cannot read ambient group conversation, create group members, or
  message users who have not installed the agent.
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
