#!/usr/bin/env python3
import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = (root / "skill.md").read_text()
target = root / "agent-prompt.js"

output = f"""(() => {{
  const RELAY_AGENT_PROMPT = {json.dumps(source, ensure_ascii=False)};
  const FALLBACK_PATH = "/getting-started/ai-agents#relay-agent-prompt";
  const COPIED_MS = 1600;

  function isPromptLink(link) {{
    if (!(link instanceof HTMLAnchorElement)) return false;
    const url = new URL(link.href, window.location.href);
    return (
      url.pathname + url.hash === FALLBACK_PATH &&
      Boolean(link.closest('#navbar, #mobile-nav, [role="dialog"]'))
    );
  }}

  function labelElement(link) {{
    return [...link.querySelectorAll("span")].find(
      (span) => span.textContent.trim() === "Copy agent prompt"
    );
  }}

  async function writePrompt() {{
    if (navigator.clipboard?.writeText) {{
      await navigator.clipboard.writeText(RELAY_AGENT_PROMPT);
      return;
    }}

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
  }}

  async function onPromptClick(event) {{
    const link = event.currentTarget;
    event.preventDefault();

    try {{
      await writePrompt();
    }} catch {{
      window.location.assign(link.href);
      return;
    }}

    const label = labelElement(link);
    const originalAriaLabel = link.getAttribute("aria-label");
    if (label) label.textContent = "Copied";
    link.setAttribute("aria-label", "Copied agent prompt");

    window.setTimeout(() => {{
      if (label) label.textContent = "Copy agent prompt";
      if (originalAriaLabel === null) {{
        link.removeAttribute("aria-label");
      }} else {{
        link.setAttribute("aria-label", originalAriaLabel);
      }}
    }}, COPIED_MS);
  }}

  function bindPromptLinks(root = document) {{
    root.querySelectorAll('a[href="' + FALLBACK_PATH + '"]').forEach((link) => {{
      if (!isPromptLink(link) || link.dataset.relayPromptCopy === "true") return;
      link.dataset.relayPromptCopy = "true";
      link.setAttribute("aria-label", "Copy Relay agent prompt");
      link.addEventListener("click", onPromptClick);
    }});
  }}

  bindPromptLinks();
  new MutationObserver(() => bindPromptLinks()).observe(document.body, {{
    childList: true,
    subtree: true,
  }});
}})();
"""

if "--check" in sys.argv:
    if not target.is_file() or target.read_text() != output:
        raise SystemExit("agent-prompt.js is stale; run npm run build:agent-prompt")
    print("Copy agent prompt payload is synchronized with skill.md")
else:
    target.write_text(output)
    print("Built agent-prompt.js from skill.md")
