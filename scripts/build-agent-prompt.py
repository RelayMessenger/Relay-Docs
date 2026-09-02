#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = (root / "skill.md").read_text()
target = root / "agent-prompt.js"
mintlify_skill_target = root / ".mintlify/skills/relay/SKILL.md"
agent_page_target = root / "getting-started/ai-agents.mdx"


def render_agent_page(page: str) -> str:
    pattern = re.compile(
        r"(^## Relay agent prompt\n.*?^````text Relay agent prompt\n)"
        r".*?"
        r"(^````$)",
        re.M | re.S,
    )
    rendered, count = pattern.subn(
        lambda match: match.group(1) + source.rstrip("\n") + "\n" + match.group(2),
        page,
        count=1,
    )
    if count != 1:
        raise SystemExit("could not locate the visible Relay agent prompt")
    return rendered

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

  function iconElement(link) {{
    return link.querySelector("svg");
  }}

  function setCopyIcon(link, copied) {{
    const icon = iconElement(link);
    if (!icon) return;

    if (!icon.dataset.relayPromptOriginalMaskImage) {{
      icon.dataset.relayPromptOriginalMaskImage = icon.style.maskImage;
      icon.dataset.relayPromptOriginalWebkitMaskImage = icon.style.webkitMaskImage;
    }}

    const originalMaskImage = icon.dataset.relayPromptOriginalMaskImage;
    const originalWebkitMaskImage = icon.dataset.relayPromptOriginalWebkitMaskImage;
    if (copied) {{
      icon.style.maskImage = originalMaskImage.replace(/copy\\.svg/g, "check.svg");
      icon.style.webkitMaskImage = originalWebkitMaskImage.replace(/copy\\.svg/g, "check.svg");
    }} else {{
      icon.style.maskImage = originalMaskImage;
      icon.style.webkitMaskImage = originalWebkitMaskImage;
    }}
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
    setCopyIcon(link, true);
    link.setAttribute("aria-label", "Copied agent prompt");

    if (link.__relayPromptCopyTimer) window.clearTimeout(link.__relayPromptCopyTimer);

    link.__relayPromptCopyTimer = window.setTimeout(() => {{
      if (label) label.textContent = "Copy agent prompt";
      setCopyIcon(link, false);
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
    if (
        not mintlify_skill_target.is_file()
        or mintlify_skill_target.read_text() != source
    ):
        raise SystemExit(
            ".mintlify/skills/relay/SKILL.md is stale; "
            "run npm run build:agent-prompt"
        )
    expected_agent_page = render_agent_page(agent_page_target.read_text())
    if agent_page_target.read_text() != expected_agent_page:
        raise SystemExit(
            "the visible Relay agent prompt is stale; "
            "run npm run build:agent-prompt"
        )
    print(
        "Copy action, visible prompt, and Mintlify skill are synchronized "
        "with skill.md"
    )
else:
    target.write_text(output)
    mintlify_skill_target.write_text(source)
    agent_page_target.write_text(render_agent_page(agent_page_target.read_text()))
    print(
        "Built agent-prompt.js, visible prompt, and Mintlify skill "
        "from skill.md"
    )
