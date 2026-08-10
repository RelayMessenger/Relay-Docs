---
name: docs-openclaw-style
description: Apply selected OpenClaw documentation patterns to complex runtime, channel, CLI, configuration, security, and troubleshooting pages. Use when Relay must explain a large integration without mixing onboarding, concepts, operations, and reference. Do not copy OpenClaw’s product scope or navigation size.
---

# OpenClaw documentation style

Use OpenClaw for separating a large system into reader tasks.

## Structure

1. Give every page a short summary and a clear reader need.
2. Keep the first-time path separate from full setup reference.
3. Split concepts, channels, CLI, security, and troubleshooting.
4. Give each channel one setup page with the same order.
5. Keep command reference under the command name.
6. Put repair commands beside failure signatures.

The current getting-started page is about 539 words and reaches a working
dashboard in four steps. Use that scale for Relay integration starts.

## Channel page pattern

1. State support and scope.
2. List requirements.
3. Show setup commands.
4. Show the smallest configuration.
5. Explain inbound and outbound behavior.
6. List supported and unsupported capabilities.
7. Give symptom, cause, and fix rows.

## What to adapt

- `summary` and `read_when` thinking.
- A fast start that links to deeper references.
- Stable page templates across integrations.
- Security at the point of exposure.
- Troubleshooting by visible symptom.

## What to avoid

- OpenClaw’s index contains hundreds of pages and deep parallel hierarchies.
- Do not expose internal proposals, QA pages, aliases, or operator notes.
- Do not make readers learn configuration before they complete the basic task.
- Do not let every feature create a top-level navigation item.

## Verify

- A beginner path is under five steps.
- Integration pages use one repeated template.
- Troubleshooting starts from the user-visible failure.
- Internal architecture does not leak into public onboarding.

## Sources

- https://docs.openclaw.ai/llms.txt
- https://docs.openclaw.ai/start/getting-started.md
- https://docs.openclaw.ai/concepts/messages.md
- https://docs.openclaw.ai/channels
- https://docs.openclaw.ai/gateway/security
- https://github.com/openclaw/openclaw

Sources checked on 2026-08-10.
