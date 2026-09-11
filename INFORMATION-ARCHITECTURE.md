# Relay documentation information architecture

`docs.json` owns navigation. The Server OpenAPI owns the public API contract.
Each authored page owns one reader task or one reference subject.

## Reader paths

| Area | Reader job | Keep elsewhere |
| --- | --- | --- |
| Introduction | Understand Relay and choose a starting point | Setup walkthroughs and complete capability tables |
| Getting started | Complete a first exchange, authenticate, install the SDK | Agent management, full transport protocols, audit prompts |
| Agents | Create, connect, list, or delete an identity | Profile-image internals and runtime-specific installation |
| Messaging | Perform one Message operation | Whole event envelopes and transport recovery |
| Attachments | Upload, download, import, delete, or check file limits | Model-provider request formats |
| Chats | Create a Chat, change membership, read history, or update metadata | Repeated Contact rules on every page |
| Contacts | Manage contact relationships and profiles | Sending or event-delivery tutorials |
| Webhooks | Receive, verify, manage subscriptions, or handle retries | Full event-specific payloads |
| Webhook event reference | Look up one event's data | Receiver implementation |
| WebSocket | Connect, acknowledge, recover, observe, or inspect frames | CLI terminal controls |
| Integrations | Install and connect one supported runtime or tool | Maintainer publication and package-provenance reports |
| Platform | Check reliability, limits, retries, and errors | Repeated first-run setup |
| Examples | Choose a runnable maintained example | Another copy of each integration guide |
| Agent instructions | Supply a complete machine-readable setup task | Human onboarding prose |
| API Reference | Inspect canonical operations and schemas | Narrative setup walkthroughs |
| Error Codes | Resolve one specific error | Repeated shared error envelopes |

Getting started contains Quickstart, Authentication, and TypeScript SDK.
Management, CLI, and coding-agent pages are grouped by their task, even when
an existing URL retains a `getting-started` prefix for compatibility.

## Page boundaries

Lead with the action or fact. Keep required inputs, the smallest complete
example, its success condition, and relevant failure handling together.

Related operations can share a page when they answer the same question:
start/stop typing, add/remove a reaction, or read a paginated history. A shared
noun alone does not justify combining creation, deletion, customization, and
troubleshooting into an onboarding page.

An overview routes to tasks. It does not reproduce each child's instructions.
A guide links to a concept or reference when that information becomes useful.
A reference can be longer when the reader explicitly came to inspect that
protocol, schema, or machine instruction.

Ordinary task guides have at most five top-level sections before related
links. Examples, tables, tabs, and accordions still cost reader attention.
Do not use formatting to disguise independent tasks inside one page.

## Source and example integrity

- Keep `api-reference/openapi.yaml` byte-identical to the approved Server input.
- Check runtime statements against current implementation or tests.
- Generate endpoint presentation from OpenAPI; preserve stable endpoint URLs.
- Use the maintained SDK and equivalent HTTPS for actual API tasks.
- Show CLI commands for CLI tasks, without an unrelated HTTP walkthrough.
- Keep credentials private, request identifiers consistent, and retry boundaries explicit.
- Keep registry observations in `versions.json`, not repeated inventories on task pages.
- Separate conflicting source evidence from a confirmed behavior; do not invent a rule.

## Machine-readable surfaces

`skill.md` is the source for the navbar copy action, the Mintlify skill copy,
and the full code block on `connect/agent-prompt.mdx`. The short AI coding
agents page links there instead of embedding the full instruction file.

`llms.txt` is a setup entry point and a compact page index. Endpoint entries
name their method and path, not the complete operation description.
`llms-full.txt` contains the authored pages and complete presented OpenAPI.
Both files are generated, not hand-maintained.

## Compatibility and verification

Retain existing page URLs or add redirects. Rewrite internal links to the new
owning page and preserve useful old fragments on retained pages.

Checks cover navigation ownership, focused onboarding, internal fragments,
contract identity, event coverage, safety-critical topic content, examples,
package references, and generated outputs. Tests must not require internal
publishing notes or a frozen list of prose headings in public task pages.

Run the repository's validation and Mintlify link, build, and accessibility
checks in Daytona. Inspect desktop and narrow rendering before release.
Publish and verify staging, then derive production with the same approved
content and verify its hosted pages, machine files, and environment links.
