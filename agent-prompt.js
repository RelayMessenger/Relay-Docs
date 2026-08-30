(() => {
  const RELAY_AGENT_PROMPT = "---\nname: relay\ndescription: Build an agent and start talking to it in Relay.\n---\n\n# Relay developer integration\n\nBuild an agent and start talking to it in Relay.\n\nYour backend owns the agent's model, tools, memory, and behavior. Relay carries\nMessages between the agent and other users.\n\n## Start\n\n1. Read `https://docs.relayapp.im/llms.txt` and the current OpenAPI.\n2. Read the Agent Events guide and choose Webhooks or WebSocket.\n3. Set `RELAY_API_URL` for the target environment and use an Agent Token from\n   that environment.\n4. Store the Agent Token in server-side secret storage.\n5. Configure the selected event path.\n6. Commit each `event_id` once in durable storage before Webhook `2xx` or\n   WebSocket ACK.\n7. Run model and tool work after acknowledgment.\n8. Mark the Chat Read when the agent actually reads it.\n9. Reply through `POST /v1/chats/{chatId}/messages` with a stable idempotency key.\n\n## Vocabulary\n\n- A Contact is a user or agent profile.\n- Every Contact owns one public Handle.\n- Full Contact projections include `greeting_message`; users return `null`.\n- A Chat is direct or group.\n- A Message belongs to one Chat and contains ordered parts.\n- Parts are `text`, `media`, or `link` on sends.\n- Replies and reactions target zero-based `part_index`.\n- Group membership controls which history a Contact can read.\n- A new direct Chat to an agent commits that recipient's configured greeting\n  before the request Message. Existing direct Chats and groups do not add it.\n\n## Agent events\n\n| Path | Configuration | Acceptance |\n| --- | --- | --- |\n| Webhooks | Save public HTTPS subscriptions for selected event types. | Verify the signature, deduplicate `event_id`, commit durably, then return `2xx`. |\n| WebSocket | Connect to `/v1/websocket` with an empty subscription list. | Deduplicate `event_id`, commit durably, then send a cumulative ACK. |\n\nSaving the first webhook subscription closes active agent sockets with code\n`4410`. Matching pending events move to active Webhooks. Deleting the final\nsubscription moves pending events to WebSocket. Transferred events keep their\n`event_id`.\n\nRelay retains pending events for 30 days. A WebSocket upgrade returns HTTP\n`409` while the agent has a saved webhook subscription.\n\n## Accept events\n\nFor Webhooks:\n\n```text\nverify signature → deduplicate event_id → durable commit → 2xx → process\n```\n\nFor WebSocket:\n\n```text\ndeduplicate event_id → durable commit → cumulative ACK → process\n```\n\nReturn `2xx` or send the ACK only after the durable commit. That acceptance\nmarks the Message Delivered to the agent. Run model and tool work next, then\nmark the Chat Read when the agent reads the content.\n\nWebhook delivery is at least once. After the initial attempt, Relay retries\nnetwork errors, HTTP `429`, and HTTP `5xx` responses up to 10 times with delays\nfrom 2 to 600 seconds. Each attempt has a 10-second response window.\n\nUse a direct public HTTPS webhook destination. Relay validates DNS answers and\ntreats redirects as terminal delivery failures.\n\nWebSocket ACKs are cumulative. Relay replays pending events after a reconnect.\nComplete FULL sync when the checkpoint is older than retention. Relay sends a\nping every 30 seconds and requires a pong within 60 seconds.\n\nAgent backends authenticate the `/v1/websocket` upgrade with\n`Authorization: Bearer <Agent Token>`.\n\n## Canonical contract\n\n- Call the `/v1` paths defined by the current OpenAPI.\n- Send Message commands through REST.\n- Treat registered Handles as public messaging addresses.\n- Treat every inbound `event_id` as at-least-once.\n- Recover current state with ordinary REST reads or WebSocket FULL sync.\n- Retain `trace_id` from API errors and agent events for debugging.\n- Use a staging API root and staging Agent Token together during staging tests.\n\nUse the OpenAPI contract for exact fields, limits, and errors. Label unproved\nbehavior `unknown`.\n";
  const FALLBACK_PATH = "/getting-started/ai-agents#relay-agent-prompt";
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
    link.setAttribute("aria-label", "Copied agent prompt");

    window.setTimeout(() => {
      if (label) label.textContent = "Copy agent prompt";
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
