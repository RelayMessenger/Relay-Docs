---
name: docs-hermes-style
description: Apply current Hermes Agent documentation patterns to CLI, messaging gateway, configuration, security, feature, and troubleshooting pages. Use when Relay needs a fast command-first path, separate terminal and messaging flows, exact success checks, or symptom-led repair. Do not use Hermes behavior as proof of Relay behavior.
---

# Hermes documentation style

Use Hermes for command-first setup and large runtime documentation.

## Structure

1. Put installation and the first working command first.
2. Separate getting started, user guides, features, tutorials, developer guides, and reference.
3. Split terminal use from messaging gateway setup.
4. Give each messaging platform one page with the same setup order.
5. Keep complete commands, flags, environment variables, and schemas in reference.
6. Put security beside every externally exposed gateway or credential step.

## Page pattern

1. State the working result.
2. Show the shortest command path.
3. List what success looks like.
4. Add the next feature only after the base path works.
5. Route optional choices through a compact table.
6. Troubleshoot from the visible symptom and a diagnostic command.

Use command tables when several actions are equivalent. Name each command's
effect instead of repeating a long explanation.

## What to adapt

- A goal table that sends each reader to one first command.
- Separate CLI and messaging paths.
- Explicit success checks after setup.
- Repeated integration templates.
- Security guidance at the exposure point.
- Machine-readable documentation indexes for coding agents.

## What to avoid

- The current Hermes quickstart has about 1,028 prose words and 34 headings.
- Its configuration page has about 12,027 prose words and 120 headings.
- Do not copy Hermes's feature catalogue into Relay navigation.
- Do not put provider choice before Relay's first message.
- Do not copy marketing comparisons from the Hermes homepage.
- Keep migration details outside normal Relay onboarding.

## Verify

- A beginner reaches one working result before optional configuration.
- Terminal and messaging routes do not interrupt each other.
- Every command names its effect and success signal.
- Gateway pages include access, secret, and exposure guidance.
- Troubleshooting begins with symptoms and commands.
- Relay claims still match Relay's OpenAPI and shipped behavior.

## Sources

- https://github.com/NousResearch/hermes-agent
- https://hermes-agent.nousresearch.com/docs/
- https://hermes-agent.nousresearch.com/docs/llms.txt
- https://hermes-agent.nousresearch.com/docs/getting-started/quickstart
- https://hermes-agent.nousresearch.com/docs/user-guide/cli
- https://hermes-agent.nousresearch.com/docs/user-guide/messaging
- https://hermes-agent.nousresearch.com/docs/user-guide/security
- https://hermes-agent.nousresearch.com/docs/guides/cron-troubleshooting
- https://hermes-agent.nousresearch.com/docs/reference/cli-commands

Sources checked on 2026-08-10 at repository commit
`49c632310dd6877302e8dfa92e740b0ceddb97b8`.
