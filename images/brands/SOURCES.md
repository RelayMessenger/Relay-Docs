# Brand mark sources

Every file in this folder, where it came from, and the terms it is published
under. Retrieved 2026-09-11. No mark in this folder has been drawn, cropped, or
otherwise reshaped. The only edits are hardcoded-black to `fill="currentColor"`
so a monochrome mark follows the light or dark theme; each such edit is named in
the notes below.

| File | Product | Source URL | Licence or brand guidelines | Retrieved |
| --- | --- | --- | --- | --- |
| `anthropic.svg` | Anthropic | https://github.com/simple-icons/simple-icons/blob/develop/icons/anthropic.svg | CC0 1.0, https://github.com/simple-icons/simple-icons#license | 2026-09-11 |
| `claude.svg` | Claude | https://github.com/simple-icons/simple-icons/blob/develop/icons/claude.svg | CC0 1.0, https://github.com/simple-icons/simple-icons#license | 2026-09-11 |
| `cline.svg` | Cline | https://cline.bot/assets/branding/brand/cline-brand-assets.zip, `General Logos/Bot/SVG/BOT_LIGHT.svg` | https://cline.bot/brand | 2026-09-11 |
| `cloudflare.svg` | Cloudflare | https://github.com/simple-icons/simple-icons/blob/develop/icons/cloudflare.svg | CC0 1.0, https://github.com/simple-icons/simple-icons#license | 2026-09-11 |
| `cursor.svg` | Cursor | https://ptht05hbb1ssoooe.public.blob.vercel-storage.com/assets/brand/cursor-brand-assets.zip, `General Logos/Cube/SVG/CUBE_25D.svg` | https://cursor.com/brand | 2026-09-11 |
| `gemini.svg` | Google Gemini | https://www.gstatic.com/lamda/images/gemini_sparkle_aurora_33f86dc0c0257da337c63.svg | https://about.google/brand-resource-center/ | 2026-09-11 |
| `hermes.png` | Hermes Agent | https://github.com/NousResearch/hermes-agent , `website/static/img/apple-touch-icon.png` | Nous Research (Hermes Agent project) | 2026-09-11 |
| `linq.png` | Linq | https://docs.linqapp.com/favicon-light.png | https://linqapp.com, no published brand page | 2026-09-11 |
| `openai.svg` | OpenAI | https://github.com/openai/openai-realtime-agents/blob/main/public/openai-logomark.svg | https://openai.com/brand, MIT | 2026-09-11 |
| `openclaw.svg` | OpenClaw | https://openclaw.ai/favicon.svg (byte-identical to https://docs.openclaw.ai/assets/openclaw.svg) | https://github.com/openclaw/openclaw, MIT | 2026-09-11 |
| `opencode.svg` | opencode | https://opencode.ai/favicon.svg | https://github.com/anomalyco/opencode, MIT | 2026-09-11 |
| `photon.svg` | Photon | https://mintcdn.com/photon-6d78d87b/-Sx6UdxO4BG0ZSxk/logo/light.svg (the nav logo on https://docs.photon.codes) | https://photon.codes, no published brand page | 2026-09-11 |
| `telegram.svg` | Telegram | https://telegram.org/img/t_logo.svg | https://telegram.org/press | 2026-09-11 |
| `vercel.svg` | Vercel | https://github.com/simple-icons/simple-icons/blob/develop/icons/vercel.svg | CC0 1.0, https://github.com/simple-icons/simple-icons#license | before 2026-09-11 |
| `vscode.svg` | Visual Studio Code | https://code.visualstudio.com/assets/branding/visual-studio-code-icons.zip, `vscode.svg` | https://code.visualstudio.com/brand, trademark of Microsoft | 2026-09-11 |

## Products with no file of their own

| Product | Mark to use | Why |
| --- | --- | --- |
| OpenAI Codex | `openai.svg` | Codex ships no mark of its own. Its VS Code extension icon and its CLI splash both carry the OpenAI mark. |
| Vercel Chat SDK | `vercel.svg` | The Chat SDK is a Vercel product and carries the Vercel triangle. |

## Notes on the files that were already here

- `anthropic.svg` carries `fill="#D97757"`. That is Claude's brand colour.
  Simple Icons records `#191919` for this mark. The path is correct.
- `claude.svg` carries `fill="#D97757"`, which is correct for Claude.
- `vercel.svg` carries `fill="#737373"`. Vercel's mark is `#000000`
  (https://vercel.com/geist/brands). The path is correct.
- `openai.png` was the OpenAI mark at 128 px with no transparency, a white box
  on dark. Replaced 2026-09-11 by `openai.svg`. OpenAI's brand page publishes
  only construction diagrams, misuse examples and a Photoshop template zip, and
  it refuses requests outside a browser, so the mark comes from an OpenAI
  repository instead.
- `openclaw.png` was JPEG data under a `.png` name, 128 px. Replaced 2026-09-11
  by `openclaw.svg`, the transparent mark both OpenClaw sites serve. Verified
  2026-09-11 byte-identical (1194 B) to the live https://openclaw.ai/favicon.svg.
- `anthropic.svg` keeps its `#D97757` fill. Anthropic publishes no brand page:
  `/brand`, `/brand-kit`, `/press` and `/company/brand` all return 404, and the
  site links no brand asset. There is no official file to replace it with.
- `openai.svg` had no `fill`, so the path drew black and vanished on dark. Set
  `fill="currentColor"` on 2026-09-11 so the Codex mark follows the theme. Path
  unchanged.
- `cline.svg` is byte-identical to the Cline brand kit `BOT_LIGHT.svg`. The kit's
  dark twin `BOT_DARK.svg` is the same path filled `#f9f9f9`. The Mintlify `icon`
  field takes one value, not a light/dark pair, so instead of shipping two files
  we set `fill="currentColor"` on 2026-09-11; it renders dark on light and light
  on dark, matching the pair with one file. Path unchanged.
- `cloudflare.svg` is the simple-icons Cloudflare cloud (CC0), added 2026-09-11
  for the Cloudflare Think page, with `fill="currentColor"` so it follows the
  theme. Cloudflare's official orange logomark needs the company's written
  permission (https://www.cloudflare.com/trademark/) and ships no direct asset
  URL, so the CC0 mark is used. Path unchanged.
- `hermes.png` is the Hermes Agent mark, the app icon the project our
  `connect hermes` targets serves at
  `website/static/img/apple-touch-icon.png` (180x180, self-contained tile so it
  reads on light and dark), used verbatim. It replaces the earlier Nous Research
  seal, which the owner rejected as the wrong mark (2026-09-11). The pixel-art
  winged knight at `apps/desktop/public/hermes.png` is an in-app sprite, not the
  brand mark, so it is not used.

## Marks that follow the theme with `currentColor`

These monochrome marks now carry `fill="currentColor"`, so one file renders on
both light and dark. See the notes above for each.

| File | Sourced dark twin (confirms the intent, not shipped) |
| --- | --- |
| `cline.svg` | `General Logos/Bot/SVG/BOT_DARK.svg` in the Cline brand kit is the same path filled `#f9f9f9`. |
| `openai.svg` | OpenAI publishes no white twin. https://openai.com/favicon.svg is a rounded tile that inverts with the colour scheme. |
| `cloudflare.svg` | The official orange logomark is the two-tone version; it needs Cloudflare's written permission. |

## Marks that still need a second file for dark backgrounds

These publish one mark per background. The file here is the light-background one,
so it disappears on dark. Left as-is on staging.

| File | Dark-background twin |
| --- | --- |
| `photon.svg` | https://mintcdn.com/photon-6d78d87b/-Sx6UdxO4BG0ZSxk/logo/dark.svg |
| `linq.png` | https://docs.linqapp.com/favicon-dark.png |

## Size exceptions

- `linq.png` is 256 px. Linq publishes no SVG and no larger mark-only file.
  The 1800 px asset on linqapp.com is a wordmark lockup, not the mark.
