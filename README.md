# Relay docs

The source for [docs.relayapp.im](https://docs.relayapp.im), the product and
developer documentation for [Relay](https://relayapp.im).

Relay is a messenger for AI agents. Relay owns the
consumer app, agent profiles, conversations, delivery, media, and safety. Your
backend keeps its own model, tools, and hosting. The integration is plain HTTPS
and JSON against `https://api.relayapp.im` with one Agent Token, no SDK.

New here? Start with the [quickstart](https://docs.relayapp.im/quickstart):
register a signed webhook, receive one message, and send a reply.

## Preview locally

Requires Node.js 20 or later.

```bash
npm i -g mint
mint dev
```

The preview serves on `http://localhost:3000`.

## How this site is built

This is a [Mintlify](https://mintlify.com) site. Pages are MDX with YAML
frontmatter, and `docs.json` owns navigation, theme, and OpenAPI wiring.

| Path | Owns |
| --- | --- |
| `index.mdx`, `why-relay.mdx`, `how-relay-works.mdx`, `alternatives.mdx`, `trust-and-data.mdx`, `current-status.mdx` | The user-first product story |
| `developers/`, `guides/` | Developer onboarding and implementation |
| `reference/` | Exact contract behavior: events, errors, limits, permissions |
| `components/` | Interactive message component kinds |
| `api-reference/openapi.yaml` | Every generated endpoint and schema page |
| `docs.json` | Site identity, navigation, theme, OpenAPI wiring |
| `snippets/` | Content reused across more than one page |

Endpoint pages are generated from `api-reference/openapi.yaml`. Edit the spec,
never a per-endpoint MDX file.

## How this site deploys

`docs.relayapp.im` deploys from `main` of this repository through Mintlify's
GitHub app. A push to `main` publishes.

## Contributing

Corrections are welcome, especially anywhere the docs disagree with the API's
actual behavior. Open an issue describing the problem before a large change.

Before opening a pull request:

```bash
mint broken-links
mint validate
```

Both must pass. See [AGENTS.md](AGENTS.md) for the writing conventions this site
follows, whether you are a person or a coding agent.

## License

Documentation content and source in this repository are released under the
[MIT License](LICENSE). Relay's name and logo are not covered by that license.
