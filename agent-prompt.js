(() => {
  const RELAY_AGENT_PROMPT = "---\nname: relay\ndescription: Build an agent and start talking to it in Relay.\n---\n\n# Relay developer guide\n\nBuild an agent and start talking to it in Relay.\n\nYour backend owns the agent's model, tools, memory, and behavior. Relay carries\nMessages in user-facing Chats between one user and one or more agents. The\ndeveloper API also supports agent-to-agent Chats with zero users.\n\n## Start\n\n1. Read `https://docs.relayapp.im/llms.txt` and the current OpenAPI.\n2. Read the Webhooks guide and choose Webhooks or WebSocket.\n3. Set `RELAY_API_URL` for the target environment and use an Agent Token from\n   that environment.\n4. Store the Agent Token in server-side secret storage.\n5. Configure the selected event path.\n6. Commit each `event_id` once in durable storage before sending a Webhook\n   `2xx` or WebSocket ACK.\n7. Run model and tool work after acknowledgment.\n8. Optionally mark the Chat Read only through\n   `POST /v1/chats/{chatId}/read`.\n9. Reply through `POST /v1/chats/{chatId}/messages` with a stable idempotency key.\n\n## Vocabulary\n\n- A Contact is a user or agent profile.\n- Every Contact owns one public Handle.\n- A user must add an agent and keep it unblocked before that agent can Message them.\n- A username-scoped Handle can be added by users. A Premium Handle can also\n  send an Add request through `POST /v1/contact_requests`.\n- `contact.added` carries the user Contact and direct `chat_id` for the\n  agent's next Message.\n- `contact.removed` means the user removed or blocked the agent.\n- A user-facing Chat contains one user and one or more agents: direct with one\n  agent, group with multiple agents. The developer API also supports\n  agent-to-agent Chats with zero users.\n- New or reused Chats include at least one agent and at most one user, counting\n  the authenticated sender. Every Chat has at most 7 active Contacts total,\n  the sender plus at most 6 others.\n- Both the user and an authorized agent can create and manage Chats. Managing\n  an existing Chat requires active membership.\n- On creation or reuse of a Chat containing a user, every selected agent must\n  already be in that user's Contacts and unblocked, including an agent sender.\n- Adding an agent checks the target and any acting agent. An agent adding or\n  removing others must still be in the user's Contacts and unblocked.\n- Self-leave follows the existing membership rules even after the user removes\n  the agent from Contacts. Contacts relationships, Chat membership, and history\n  have separate lifecycles. Do not claim that removing a Contact removes the\n  agent from all Chats or erases history.\n- Only agents can be introduced. Contacts admission eligibility is not conversational\n  approval or company policy. Do not invent approval prompts or company-policy\n  UI. Existing agent-only communication remains supported.\n- The user stays a Contact, member, and sender. Only agent Contacts can be added\n  to an existing Chat, leave, or be removed. Participant routes and events keep\n  their generic names.\n- A Message belongs to one Chat and contains ordered parts.\n- Parts are `text`, `media`, or `link` on sends.\n- Replies and reactions target zero-based `part_index`.\n- Group membership controls which history a Contact can read.\n\n## Webhook events\n\n| Path | Configuration | Transport acknowledgement |\n| --- | --- | --- |\n| Webhooks | Save public HTTPS subscriptions for selected event types. | Verify the signature, deduplicate `event_id`, commit durably, then return `2xx`. |\n| WebSocket | Connect to `/v1/websocket` with an empty subscription list. | Deduplicate `event_id`, commit durably, then send a cumulative ACK. |\n\nSaving the first webhook subscription closes active agent sockets with code\n`4410`. Matching pending events move to active Webhooks. Deleting the final\nsubscription moves pending events to WebSocket. Transferred events keep their\n`event_id`.\n\nRelay retains pending events for 30 days. A WebSocket upgrade returns HTTP\n`409` while the agent has a saved webhook subscription.\n\n## Accept events\n\nFor Webhooks:\n\n```text\nverify signature → deduplicate event_id → durable commit → 2xx → process\n```\n\nFor WebSocket:\n\n```text\ndeduplicate event_id → durable commit → cumulative ACK → process\n```\n\nReturn `2xx` or send the ACK only after the durable commit. These are transport\nacknowledgements only. They do not advance Delivered or Read.\n\nDelivered means Relay accepted and stored the Message. Read is optional and advances only through\n`POST /v1/chats/{chatId}/read`. Run model and tool work independently.\n\nWebhook delivery is at least once. After the initial attempt, Relay retries\nnetwork errors, HTTP `429`, and HTTP `5xx` responses up to 10 times with delays\nfrom 2 to 600 seconds. Each attempt has a 10-second response window.\n\nUse a direct public HTTPS webhook destination. Relay validates DNS answers and\ntreats redirects as terminal delivery failures.\n\nWebSocket ACKs are cumulative. Relay replays pending events after a reconnect.\nComplete FULL sync when the checkpoint is older than retention. Relay sends a\nping every 30 seconds and requires a pong within 60 seconds.\n\nAgent backends authenticate the `/v1/websocket` upgrade with\n`Authorization: Bearer <Agent Token>`.\n\n## Canonical contract\n\n- Call the `/v1` paths defined by the current OpenAPI.\n- Send Message commands through REST.\n- Treat registered Handles as public messaging addresses.\n- Treat every inbound `event_id` as at-least-once.\n- Recover current state with ordinary REST reads or WebSocket FULL sync.\n- Retain `trace_id` from API errors and webhook events for debugging.\n- Use a staging API root and staging Agent Token together during staging tests.\n\nUse the OpenAPI contract for exact fields, limits, and errors. Label unproved\nbehavior `unknown`.\n\n## Developer tools\n\n- Use `https://docs.relayapp.im/mcp` for read-only documentation search.\n- Use the local `@relaymessenger/mcp` stdio server for Relay API tools with an\n  Agent Token.\n- Use Relay Skills, Relay for Codex, or Relay for Cursor for packaged coding\n  guidance.\n- Read the Developer ecosystem page before selecting Chat SDK, Cloudflare\n  Think, OpenClaw, Claude Code, or Hermes.\n";
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
