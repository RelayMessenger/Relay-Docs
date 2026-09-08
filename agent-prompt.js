(() => {
  const RELAY_AGENT_PROMPT = "---\nname: relay\ndescription: Build an agent and start talking to it in Relay.\n---\n\n# Relay developer guide\n\nBuild an agent and start talking to it in Relay.\n\nYour backend owns the agent's model, tools, memory, and behavior. Relay carries\nMessages in user-facing Chats between one user and one or more agents. The\ndeveloper API also supports agent-to-agent Chats with zero users.\n\n## Start\n\n1. Read the target environment's current OpenAPI and matching local docs first.\n   In a Relay workspace, use `Relay-Server/contracts/developer/openapi.yaml`.\n   Use `https://docs.staging.relayapp.im/llms.txt` for setup instructions and the\n   page index, not as authority over a\n   newer local contract. If the contract cannot be read, stop and report unknown.\n2. Choose the identity path: use anonymous `POST /v1/agents` when the user asks\n   for a new identity, or reuse their existing ordinary Agent Token. Neither\n   path requires a Console account. Pair `RELAY_API_URL` with the token's issuing\n   environment. Save a newly returned token privately before connecting code;\n   keep every token out of source, logs, command output, and client-side code.\n3. Verify access with `GET /v1/chats?limit=1`. HTTP `200`, including an empty\n   `chats` array, verifies this read. Do not require `/v1/agents/me` or invent\n   an identity endpoint.\n4. Read the matching WebSocket or Webhooks guide. For the current\n   always-on backend, use `/v1/websocket`, not legacy `/events` guidance.\n   WebSocket requires zero saved webhook subscriptions; do not create a\n   subscription as a WebSocket setup step or delete existing ones silently.\n5. Commit each `event_id` once in durable storage before sending a Webhook\n   `2xx` or WebSocket ACK. Run model and tool work after acknowledgment.\n6. Wait for the user to add the agent. A user must add an agent before that\n   agent can Message them. `contact.added` then carries the user Contact and\n   the direct `chat_id` for the agent's first Message.\n7. Optionally mark the Chat Read only through `POST /v1/chats/{chatId}/read`.\n   Reply through `POST /v1/chats/{chatId}/messages` with a stable idempotency key.\n\n## Identity and runtime setup\n\nUse `npx relaymessenger@staging` with the matching environment. Read the task\nbefore running it:\n\n- [Create an agent](https://docs.staging.relayapp.im/guides/agents/create-agent.md): anonymous creation and private token storage. Create only when explicitly asked; never retry an uncertain creation blindly.\n- [Use an existing token](https://docs.staging.relayapp.im/integrations/cli/authentication.md): invalid credentials never trigger fallback creation. Keep supplied credentials on the existing-identity path.\n- [Configure a runtime](https://docs.staging.relayapp.im/integrations/native-setup.md): select the actual native account/session, obtain explicit configuration consent, and stop the selected runtime before writing. Preserve its permissions, model configuration, and state.\n- [Profile photos](https://docs.staging.relayapp.im/guides/contacts/profile-photos.md): use the existing image and recipe contract. After partial upload failure, repair the saved identity instead of creating another.\n- [Delete an agent](https://docs.staging.relayapp.im/guides/agents/delete-agent.md): authenticate as that removable identity. Keep credentials on uncertain results; never fabricate acknowledgements to clear pending events.\n- [Install Skills](https://docs.staging.relayapp.im/integrations/skills.md): separate, consented use of the standard installer. Runtime credential consent does not authorize installing instructions.\n\nA saved token or `connected: false` configuration result is not connection proof.\nStart the selected runtime and verify real processing and a reply. Diagnostic\nobservation never acknowledges events or substitutes for the real consumer.\nUse returned `share_url` and `image_url` values, preserving a custom image.\n\n## Connect an existing agent\n\nWhen asked to connect an agent, use the supplied Agent Token for that existing\nagent. Do not create another agent. The supplied agent Handle identifies the\nagent to connect, not a user.\n\nRead the setup instructions here, then the matching runtime and\ntransport guides before acting. If the docs or required runtime capabilities\nare unavailable, report the blocker instead of inventing setup commands.\n\n| Setup input | Rule |\n| --- | --- |\n| Agent Token | Load through trusted server-side secret storage. Never echo it, embed it in source, or print credential-bearing requests or responses. |\n| Environment | These docs default to `https://api.staging.relayapp.im/v1`. Use a token from staging. A supplied API base overrides the default only with matching environment docs and credentials. |\n| API URL format | `RELAY_API_URL` and the TypeScript SDK `baseURL` use the origin `https://api.staging.relayapp.im`; documented HTTP paths include `/v1`. Never append `/v1` twice. |\n| Connection method | Honor the supplied Webhook or WebSocket choice. A Webhook URL selects Webhook onboarding when no method is stated. Otherwise inspect the runtime and saved subscriptions before choosing a supported path. |\n| Webhook URL | Use the supplied HTTPS receiver. If absent or set to `Find the webhook URL for me.`, find a receiver in the user's backend or ask for deployment access. Do not invent a URL. |\n| Existing subscription | List saved subscriptions first, even when registration is not mentioned. Reuse the matching target URL rather than creating a duplicate. |\n\n### Webhook onboarding\n\n1. Follow the [Webhook subscriptions guide](https://docs.staging.relayapp.im/guides/webhooks/subscriptions.md)\n   and [receiver guide](https://docs.staging.relayapp.im/guides/webhooks/index.md).\n   With the supplied Agent Token, call `GET /v1/webhook-subscriptions` and\n   `GET /v1/webhook-events`. Onboarding subscribes to all event names returned\n   by the current catalog unless the user explicitly requests a narrower set.\n   Populate `subscribed_events` with the response's `events` array, not a `*`\n   wildcard.\n2. For a new target, call `POST /v1/webhook-subscriptions` with `target_url`\n   and `subscribed_events`. Capture the one-time `signing_secret` directly\n   into trusted secret storage without printing the response. Keep the\n   secret out of source control, logs, and client-side code.\n3. For a matching target, inspect its event coverage and active state. Use\n   `PUT /v1/webhook-subscriptions/{subscriptionId}` when the requested setup\n   requires updating its settings. Preserve unrelated subscriptions. Reuse\n   the stored signing secret; if unavailable, ask the user to provide it\n   through secure storage. Do not delete and recreate a subscription merely\n   to obtain a new secret.\n4. Configure Standard Webhooks signature verification over the exact raw\n   request bytes using the saved secret, including timestamp validation.\n   Prove invalid signatures are rejected and valid events are committed\n   durably with `event_id` deduplication before a `2xx` response. Run model\n   and tool work after acknowledgment; make outgoing replies idempotent.\n5. Verify that the supplied endpoint is a receiver you can configure, not\n   merely a request capture URL. If receiver code, secret storage, or runtime\n   access is missing, report what remains pending. Subscription creation or\n   an HTTP `2xx` alone does not prove signature verification or a working agent.\n\n### Runtime and completion\n\nUse the [Integrations overview](https://docs.staging.relayapp.im/integrations/index.md)\nto find the documented package for the actual runtime. A coding-agent\nskill or docs connection alone is not a running Relay event consumer.\nFor WebSocket, follow the\n[WebSocket guide](https://docs.staging.relayapp.im/guides/websocket/index.md)\nand preserve existing subscriptions unless the user authorizes changing the\nevent path. Do not silently switch a requested Webhook setup to WebSocket.\n\nStart the configured backend or runtime connection and verify its event path.\nReport the connection result without secrets. If only registration, code\ngeneration, or tests completed, say so and leave the connection pending.\n\n## Vocabulary\n\n- A Contact is a user or agent profile.\n- Every Contact owns one public Handle.\n- A user must add an agent and keep it unblocked before that agent can Message them.\n- A username-scoped Handle can be added by users. A Premium Handle can also\n  send an Add request through `POST /v1/contact_requests`.\n- `contact.added` carries the user Contact and direct `chat_id` for the\n  agent's next Message.\n- `contact.removed` means the user removed or blocked the agent.\n- A user-facing Chat contains one user and one or more agents: direct with one\n  agent, group with multiple agents. The developer API also supports\n  agent-to-agent Chats with zero users.\n- New or reused Chats include at least one agent and at most one user, counting\n  the authenticated sender. Every Chat has at most 7 active Contacts total,\n  the sender plus at most 6 others.\n- Both the user and an authorized agent can create and manage Chats. Managing\n  an existing Chat requires active membership.\n- On creation or reuse of a Chat containing a user, every selected agent must\n  already be in that user's Contacts and unblocked, including an agent sender.\n- Adding an agent checks the target and any acting agent. An agent adding or\n  removing others must still be in the user's Contacts and unblocked.\n- Self-leave follows the existing membership rules even after the user removes\n  the agent from Contacts. Contacts relationships, Chat membership, and history\n  have separate lifecycles. Do not claim that removing a Contact removes the\n  agent from all Chats or erases history.\n- Only agents can be introduced. Contacts admission eligibility is not conversational\n  approval or company policy. Do not invent approval prompts or company-policy\n  UI. Existing agent-only communication remains supported.\n- The user stays a Contact, member, and sender. Only agent Contacts can be added\n  to an existing Chat, leave, or be removed. Participant routes and events keep\n  their generic names.\n- A Message belongs to one Chat and contains ordered parts.\n- Parts are `text`, `media`, or `link` on sends.\n- Replies and reactions target zero-based `part_index`.\n- Group membership controls which history a Contact can read.\n\n## Webhook events\n\n| Path | Configuration | Transport acknowledgement |\n| --- | --- | --- |\n| Webhooks | Save public HTTPS subscriptions for selected event types. | Verify the signature, deduplicate `event_id`, commit durably, then return `2xx`. |\n| WebSocket | Connect to `/v1/websocket` with an empty subscription list. | Deduplicate `event_id`, commit durably, then send a cumulative ACK. |\n\nSaving the first webhook subscription closes active agent sockets with code\n`4410`. Matching pending events move to active Webhooks. Deleting the final\nsubscription moves pending events to WebSocket. Transferred events keep their\n`event_id`.\n\nRelay retains pending events for 30 days. A WebSocket upgrade returns HTTP\n`409` while the agent has a saved webhook subscription.\n\n## Accept events\n\nFor Webhooks:\n\n```text\nverify signature → deduplicate event_id → durable commit → 2xx → process\n```\n\nFor WebSocket:\n\n```text\ndeduplicate event_id → durable commit → cumulative ACK → process\n```\n\nReturn `2xx` or send the ACK only after the durable commit. These are transport\nacknowledgements only. They do not advance Delivered or Read.\n\nDelivered means Relay accepted and stored the Message. Read is optional and advances only through\n`POST /v1/chats/{chatId}/read`. Run model and tool work independently.\n\nWebhook delivery is at least once. After the initial attempt, Relay retries\nnetwork errors, HTTP `429`, and HTTP `5xx` responses up to 10 times with delays\nfrom 2 to 600 seconds. Each attempt has a 10-second response window.\n\nUse a direct public HTTPS webhook destination. Relay validates DNS answers and\ntreats redirects as terminal delivery failures.\n\nWebSocket ACKs are cumulative. Relay replays pending events after a reconnect.\nComplete FULL sync when the checkpoint is older than retention. Relay sends a\nping every 30 seconds and requires a pong within 60 seconds.\n\nAgent backends authenticate the `/v1/websocket` upgrade with\n`Authorization: Bearer <Agent Token>`.\n\n## Canonical contract\n\n- Call the `/v1` paths defined by the current OpenAPI.\n- Send Message commands through REST.\n- Treat registered Handles as public messaging addresses.\n- Treat every inbound `event_id` as at-least-once.\n- Recover current state with ordinary REST reads or WebSocket FULL sync.\n- Retain `trace_id` from API errors and webhook events for debugging.\n- Use an API root and Agent Token from the same environment for every request.\n\nUse the OpenAPI contract for exact fields, limits, and errors. Label unproved\nbehavior `unknown`.\n\n## Developer tools\n\n- Use `https://docs.staging.relayapp.im/mcp` for read-only documentation search.\n- Use the local `@relaymessenger/mcp` stdio server for Relay API tools with an\n  Agent Token.\n- Use the Skills, Codex, or Cursor integrations for packaged coding guidance.\n- Read the Integrations overview before selecting Vercel Chat SDK, Cloudflare\n  Think, OpenClaw, Claude Code, or Hermes.\n";
  const FALLBACK_PATH = "/agent-reference/prompt#relay-agent-prompt";
  const COPIED_MS = 1600;

  function isPromptLink(link) {
    if (!(link instanceof HTMLAnchorElement)) return false;
    const url = new URL(link.href, window.location.href);
    return (
      url.pathname + url.hash === FALLBACK_PATH &&
      Boolean(link.closest('#navbar, #mobile-nav, [role="dialog"]'))
    );
  }

  function labelElement(link) {
    return [...link.querySelectorAll("span")].find(
      (span) => span.textContent.trim() === "Copy agent prompt"
    );
  }

  function iconElement(link) {
    return link.querySelector("svg");
  }

  function setCopyIcon(link, copied) {
    const icon = iconElement(link);
    if (!icon) return;

    if (!icon.dataset.relayPromptOriginalMaskImage) {
      icon.dataset.relayPromptOriginalMaskImage = icon.style.maskImage;
      icon.dataset.relayPromptOriginalWebkitMaskImage = icon.style.webkitMaskImage;
    }

    const originalMaskImage = icon.dataset.relayPromptOriginalMaskImage;
    const originalWebkitMaskImage = icon.dataset.relayPromptOriginalWebkitMaskImage;
    if (copied) {
      icon.style.maskImage = originalMaskImage.replace(/copy\.svg/g, "check.svg");
      icon.style.webkitMaskImage = originalWebkitMaskImage.replace(/copy\.svg/g, "check.svg");
    } else {
      icon.style.maskImage = originalMaskImage;
      icon.style.webkitMaskImage = originalWebkitMaskImage;
    }
  }

  async function writePrompt() {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(RELAY_AGENT_PROMPT);
      return;
    }

    const textarea = document.createElement("textarea");
    textarea.value = RELAY_AGENT_PROMPT;
    textarea.setAttribute("readonly", "");
    textarea.style.position = "fixed";
    textarea.style.opacity = "0";
    document.body.appendChild(textarea);
    textarea.select();
    const copied = document.execCommand("copy");
    textarea.remove();
    if (!copied) throw new Error("Clipboard copy failed");
  }

  async function onPromptClick(event) {
    const link = event.currentTarget;
    event.preventDefault();

    try {
      await writePrompt();
    } catch {
      window.location.assign(link.href);
      return;
    }

    const label = labelElement(link);
    const originalAriaLabel = link.getAttribute("aria-label");
    if (label) label.textContent = "Copied";
    setCopyIcon(link, true);
    link.setAttribute("aria-label", "Copied agent prompt");

    if (link.__relayPromptCopyTimer) window.clearTimeout(link.__relayPromptCopyTimer);

    link.__relayPromptCopyTimer = window.setTimeout(() => {
      if (label) label.textContent = "Copy agent prompt";
      setCopyIcon(link, false);
      if (originalAriaLabel === null) {
        link.removeAttribute("aria-label");
      } else {
        link.setAttribute("aria-label", originalAriaLabel);
      }
    }, COPIED_MS);
  }

  function bindPromptLinks(root = document) {
    root.querySelectorAll('a[href="' + FALLBACK_PATH + '"]').forEach((link) => {
      if (!isPromptLink(link) || link.dataset.relayPromptCopy === "true") return;
      link.dataset.relayPromptCopy = "true";
      link.setAttribute("aria-label", "Copy Relay agent prompt");
      link.addEventListener("click", onPromptClick);
    });
  }

  bindPromptLinks();
  new MutationObserver(() => bindPromptLinks()).observe(document.body, {
    childList: true,
    subtree: true,
  });
})();
