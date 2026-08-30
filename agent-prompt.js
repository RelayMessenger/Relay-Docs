(() => {
  const RELAY_AGENT_PROMPT = "---\nname: relay\ndescription: Build a Relay Messenger agent backend with the v1 API, Webhooks, or WebSocket.\n---\n\n# Relay Messenger developer integration\n\nRelay Messenger carries Messages between users and agents. The agent backend\nowns its model, tools, memory, and behavior.\n\n## Start\n\n1. Read `https://docs.relayapp.im/llms.txt` and the current OpenAPI.\n2. Read the Agent Events guide before choosing a backend shape.\n3. Set `RELAY_API_URL` for the target environment and use a matching Agent Token.\n4. Store the Agent Token in server-side secret storage.\n5. Save a webhook subscription for Webhook delivery, or save none and connect by WebSocket.\n6. Commit each `event_id` under a uniqueness rule before webhook `2xx` or WebSocket ACK.\n7. Run model and tool work after acknowledgement.\n8. Mark the Chat Read when the agent actually reads it.\n9. Reply through `POST /v1/chats/{chatId}/messages` with a stable idempotency key.\n\n## Vocabulary\n\n- A Contact is a user or agent profile.\n- Every Contact owns one public Handle.\n- A Chat is direct or group.\n- A Message belongs to one Chat and contains ordered parts.\n- Parts are `text`, `media`, or `link` on sends.\n- Replies and reactions target zero-based `part_index`.\n- Group membership controls which history a Contact can read.\n\n## Event path\n\n| Saved configuration | Agent event path |\n| --- | --- |\n| At least one webhook subscription | Webhook only |\n| No webhook subscriptions | WebSocket only |\n\nThere is no mode, toggle, or transport setting. Relay never sends one event\nthrough both paths.\n\nCreating the first subscription closes connected agent sockets and drains\npending events to Webhooks. Deleting the last drains pending events to\nWebSocket. With no subscription and no connection, events wait durably for up\nto 30 days.\n\nA WebSocket upgrade while any subscription exists returns HTTP `409`. Pending\nevents keep the same `event_id` across path changes.\n\n## Event acceptance\n\n```text\nverify → deduplicate event_id → durable commit → 2xx or ACK → process\n```\n\nAcknowledgement does not mean bytes received, handler start, model completion,\nreply, or Read.\n\nWebhook retries can repeat an `event_id`. Reject webhook destinations that\nresolve to localhost, private, link-local, or cloud metadata addresses. Never\nfollow redirects.\n\nWebSocket ACKs are cumulative. Recover with replay or FULL sync after a stale\ncheckpoint. Relay pings every 30 seconds and requires a pong within 60\nseconds.\n\nThe shared `/v1/websocket` path uses authentication to distinguish user and\nagent connections. Agent backends authenticate the upgrade with\n`Authorization: Bearer <Agent Token>`.\n\nUse the SDK WebSocket directly during local development. The `relay listen`\ncommand is deleted.\n\n## Canonical contract\n\n- Call the `/v1` paths defined by the current OpenAPI.\n- Send Message commands through REST.\n- Treat registered Handles as public messaging addresses.\n- Treat every inbound `event_id` as at-least-once.\n- Recover current state with ordinary REST reads or WebSocket FULL sync.\n- Use a staging API root and staging Agent Token together during staging tests.\n\nUse the OpenAPI for exact fields, limits, and errors. Mark anything not proved\nby the docs or contract as unknown.\n";
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
