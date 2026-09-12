(() => {
  const RELAY_AGENT_PROMPT = "Connect this project to Relay. Read https://docs.staging.relayapp.im/llms.txt and follow its Agent onboarding section before you run anything. Open https://docs.staging.relayapp.im/llms-full.txt when a step needs a page's full text. Use only the endpoints, commands, and files those documents name; if a step cannot be verified there, stop and say so.\n";
  const FALLBACK_PATH = "/integrations/agent-prompt#relay-agent-prompt";
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
