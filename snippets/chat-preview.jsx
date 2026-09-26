// A Relay chat drawn the way the Relay iOS app draws it, for the Messages,
// Chats and Calls pages. Every number below is read from Relay-iOS
// origin/staging 0517992d; each comment names the Swift file and line.
//
// The page passes the exact JSON its "JSON" tab shows as `json`, and the
// preview reads its words from that object, so the two cannot drift
// (scripts/test-contract-source.py checks it). Everything runs in the
// browser: no request leaves the page.
//
// The preview shows only the messages and their parts, in Mintlify's own
// <Frame> on the app's chat background (style.css .relay-preview): no chat
// header, composer, or status bar (owner, 2026-09-26). The map and the link
// card are crops of Relay-iOS .context/forensics recordings
// (location-sharing-20260923, link-preview-lp-20260924).
//
// The place card and the document card follow Relay-iOS origin/staging
// 1ef73e93 (Views/Transcript/RelayLocationRows.swift,
// Views/Transcript/RelayFileMessageRow.swift). The place map is a crop of
// the app's own map, marker included, from Relay-iOS .context/forensics/
// location-pin-20260925 (b-panel-pin-button-dragged-pin-send-pin.png); the
// words under it come from the JSON.
//
// Text balloons use a CSS radius of 20 and the same BubbleKit round tail
// contour that snippets/buttons-preview.jsx draws (Relay-iOS
// Views/MessageBubbleShape.swift:39-42). The exported MessageBubble draws a
// fixed-width SVG from a character count, which cannot wrap a sentence, so
// wrapped text rides an HTML balloon with the identical tail path instead.
export const ChatPreview = ({ scene, json, label }) => {
  // MDX keeps only exports in scope, so every constant and helper lives here.

  // RelayTextMessageCell.swift:49-50, textBalloonPillContentInsets 14 x 10.
  const INSET_X = 14;
  // RelayTextMessageCell.swift:152-156, 276pt balloon at a 402pt viewport.
  const BALLOON_MAX = 276;
  // RelayTextMessageCell.swift:121-122, direct and group row gutters.
  const GUTTER_DIRECT = 16;
  const GUTTER_GROUP = 12;
  // RelayTextMessageCell.swift:191-192, group avatar 28 and its 8pt gap.
  const AVATAR = 28;
  const AVATAR_GAP = 8;
  // MessageBubbleShape.swift:42, the round tail's full depth below the body.
  const TAIL_DEPTH = 6.785;
  // RelayTextMessageCell.swift:556, receipt right edge 21pt inside the balloon.
  const RECEIPT_INSET = 21;
  // RelayMediaRowLayout.swift:224, single photo width = row - (448/3 - 32).
  const PHOTO_WIDTH = 402 - GUTTER_DIRECT * 2 - (448 / 3 - 32);
  // RelaySyncModels.swift:602-607, reaction type to glyph.
  const GLYPHS = { love: "❤️", like: "👍", dislike: "👎", laugh: "😂", emphasize: "‼️", question: "❓" };
  // RelayDefaultAvatarColor.swift pairs (top, base); the app seeds the pick
  // from the contact id, so the preview fixes one ground per name.
  const GROUNDS = {
    rose: ["#E0567A", "#AD2A52"], blue: ["#5B9BFA", "#0B52C0"], teal: ["#2596A6", "#116A79"],
    green: ["#2FA46A", "#137347"], violet: ["#8F6CF2", "#5F38CF"], orange: ["#EC8A3C", "#C85F1C"],
  };
  // The BubbleKit roundTailed contour, leading orientation, copied from
  // snippets/buttons-preview.jsx (.buttons-preview-text-tail). Body bottom
  // sits at y 16.
  const TAIL = "M 0 0 C 0 0.306 1.415 4.498 4.028 7.924 C 5.087 9.312 6.309 10.536 7.660 11.577 C 9.585 13.078 10.418 14.644 10.418 16.404 C 10.418 17.587 10.209 18.756 8.510 20.988 C 7.695 22.058 8.513 23.150 9.787 22.666 C 12.407 21.671 15.391 19.860 18.005 17.927 C 20.347 16.195 20.971 16.020 22.070 16.013 L 22.070 0 Z";

  const CSS = `
.chatp { position: relative; font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", system-ui, sans-serif; }
.chatp img { margin: 0 !important; max-width: none; border-radius: 0; }
.chatp-phone { position: relative; width: 100%; max-width: 402px; margin: 0 auto; color: #000000; }
.dark .chatp-phone { color: #ffffff; }
.chatp-phone.has-overlay { min-height: 440px; }
.chatp-transcript { position: relative; padding: 16px; }
.chatp-transcript.has-bar { padding-bottom: 12px; }
.chatp-transcript.is-group { padding-left: 12px; padding-right: 12px; }
.chatp-row { position: relative; display: flex; align-items: flex-end; }
.chatp-row.out { justify-content: flex-end; }
.chatp-col { display: flex; flex-direction: column; min-width: 0; }
.chatp-row.out .chatp-col { align-items: flex-end; }
.chatp-row.in .chatp-col { align-items: flex-start; }
.chatp-bubble { position: relative; box-sizing: border-box; max-width: ${BALLOON_MAX}px; padding: 10px ${INSET_X}px; border-radius: 20px; font-size: 17px; line-height: 22px; letter-spacing: -0.43px; white-space: pre-wrap; isolation: isolate; overflow-wrap: anywhere; --fill: #E9E9E9; background: var(--fill); color: #000000; }
.dark .chatp-bubble { --fill: #2C2C2E; color: #ffffff; }
.chatp-bubble.out { --fill: #0B75FF; color: #ffffff; }
.dark .chatp-bubble.out { --fill: #007EFF; color: #E9E9E9; }
.chatp-bubble.has-tail { margin-bottom: ${TAIL_DEPTH}px; }
/* The tail paints UNDER the bubble's text, as in the app: every carrier is
   its own stacking context and the tail sits at z-index -1 inside it, so it
   can never cover a descender on the last line. */
.chatp-tail { position: absolute; top: calc(100% - 16px); width: 23px; height: 24px; fill: var(--fill); pointer-events: none; z-index: -1; }
.chatp-audio, .chatp-link, .chatp-place, .chatp-doc, .chatp-locstop, .chatp-tailed { isolation: isolate; }
.chatp-tail.in { left: 0; }
.chatp-tail.out { right: 0; transform: scaleX(-1); }
.chatp-bubble code { font-family: ui-monospace, "SF Mono", Menlo, monospace; font-size: 16px; }
.chatp-bubble a { color: #0B75FF; text-decoration: underline; }
.dark .chatp-bubble a { color: #007EFF; }
.chatp-mention { font-weight: 600; }
.chatp-sender { font-size: 11px; line-height: 13px; letter-spacing: 0.06px; color: rgba(60,60,67,.6); margin: 0 0 4px ${INSET_X}px; }
.dark .chatp-sender, .dark .chatp-receipt { color: rgba(235,235,245,.6); }
.chatp-avatar { flex: none; width: ${AVATAR}px; height: ${AVATAR}px; margin-right: ${AVATAR_GAP}px; display: flex; align-items: center; justify-content: center; color: #fff; font-weight: 700; font-size: ${Math.round(AVATAR * 0.38 * 10) / 10}px; }
.chatp-avatar.is-agent { border-radius: ${AVATAR * 0.225}px; }
.chatp-avatar.is-spacer { visibility: hidden; }
.chatp-receipt { align-self: flex-end; margin: 0 ${RECEIPT_INSET}px 0 0; font-size: 11px; line-height: 13px; letter-spacing: 0.06px; color: rgba(60,60,67,.6); font-variant-numeric: tabular-nums; }
.chatp-receipt b { font-weight: 600; }
.chatp-tapable { cursor: pointer; }
.chatp-tapable:focus-visible { outline: 2px solid #0B75FF; outline-offset: 3px; }
.chatp-flash { animation: chatp-flash 1.2s linear; }
@keyframes chatp-flash { 0% { filter: brightness(1); } 33% { filter: brightness(.6); } 67% { filter: brightness(.6); } 100% { filter: brightness(1); } }
.chatp-arrive { animation: chatp-arrive .3s ease-out; }
@keyframes chatp-arrive { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: none; } }
/* Reply quote: MessageReplyPreview.swift:71-117, ReplyQuotePalette 632-667. */
.chatp-quote { box-sizing: border-box; position: relative; max-width: ${BALLOON_MAX}px; min-height: 26px; border: 1px solid rgba(0,0,0,.20); border-radius: 18px; padding: 6.5px 10px; font-size: 11px; line-height: 13px; color: rgba(0,0,0,.44); background: transparent; margin-bottom: 8.5px; font-family: inherit; text-align: left; }
.dark .chatp-quote { border-color: rgba(255,255,255,.22); color: rgba(255,255,255,.44); }
.chatp-quote.is-own { border-color: rgba(11,117,255,.40); color: rgba(11,117,255,.80); }
.dark .chatp-quote.is-own { border-color: rgba(0,126,255,.42); color: rgba(0,126,255,.80); }
.chatp-quote.is-media { padding: 0; overflow: hidden; }
.chatp-quote.is-media img { display: block; height: 48px; width: auto; opacity: .55; }
.chatp-replyline { position: absolute; left: 0; top: 0; overflow: visible; pointer-events: none; fill: none; stroke: rgba(0,0,0,.08); stroke-width: 4; stroke-linecap: round; }
.dark .chatp-replyline { stroke: rgba(254,255,255,.16); }
/* Tapbacks: RelayTapbackBalloon.swift:52-116. */
.chatp-tapback { position: absolute; pointer-events: none; }
.chatp-tapback { position: absolute; overflow: visible; pointer-events: none; }
.chatp-tb-seam { fill: #ffffff; }
.dark .chatp-tb-seam { fill: #000000; }
.chatp-tb-fill { fill: #E9E9E9; }
.dark .chatp-tb-fill { fill: #2C2C2E; }
.chatp-tb-fill.mine { fill: #0B75FF; }
.dark .chatp-tb-fill.mine { fill: #007EFF; }
.chatp-tb-glyph { font-size: 21px; font-family: "Apple Color Emoji", "Segoe UI Emoji", "Noto Color Emoji", sans-serif; }
/* Reaction bar: MessageReactionPicker.swift:53-69, 1343-1349. */
/* Typing: TypingIndicator.swift:79-95. */
.chatp-typing { position: relative; width: 57.5px; height: 35px; border-radius: 17.5px; background: #E9E9E9; display: flex; align-items: center; justify-content: center; gap: 4px; margin-bottom: 6.71px; }
.dark .chatp-typing, .dark .chatp-typing-trail { background: #2C2C2E; }
.chatp-typing-trail { position: absolute; border-radius: 50%; background: #E9E9E9; }
.chatp-typing i { width: 8.5px; height: 8.5px; border-radius: 50%; background: #000000; opacity: .2; animation: chatp-pulse .5s cubic-bezier(.7567,.0153,.58,1) infinite alternate; }
.dark .chatp-typing i { background: #ffffff; }
.chatp-typing i:nth-child(2) { animation-delay: .25s; }
.chatp-typing i:nth-child(3) { animation-delay: .5s; }
@keyframes chatp-pulse { from { opacity: .2; } to { opacity: .45; } }
/* Voice memo: MessageBubble.swift:49-52, RelayAudioMessageRow.swift:108-110, 605-649. */
.chatp-audio { position: relative; box-sizing: border-box; flex: none; width: 280px; height: 52px; border-radius: 20px; --fill: #E9E9E9; background: var(--fill); display: flex; align-items: center; padding: 0 10px; gap: 9px; margin-bottom: ${TAIL_DEPTH}px; }
.dark .chatp-audio { --fill: #2C2C2E; }
.chatp-play { flex: none; width: 28px; height: 28px; border-radius: 50%; border: 0; padding: 0; background: #0B75FF; display: flex; align-items: center; justify-content: center; cursor: pointer; }
.dark .chatp-play { background: #007EFF; }
.chatp-play svg { width: 11px; height: 13px; fill: #ffffff; }
.chatp-wave { flex: 1; height: 30px; display: flex; align-items: center; justify-content: space-between; min-width: 0; }
.chatp-wave span { width: 2px; border-radius: 1px; background: rgba(60,60,67,.6); opacity: .42; }
.dark .chatp-wave span { background: rgba(235,235,245,.6); }
.chatp-wave span.played { background: #0B75FF; opacity: 1; }
.dark .chatp-wave span.played { background: #007EFF; }
.chatp-duration { flex: none; font-size: 11.5px; font-variant-numeric: tabular-nums; color: rgba(60,60,67,.6); }
.dark .chatp-duration { color: rgba(235,235,245,.6); }
/* Photo: MessageBubble.swift:30, 42-43; RelayMediaRowView.swift:143-144. */
.chatp-photo { position: relative; display: block; flex: none; border: 0; padding: 0; margin: 0; width: ${PHOTO_WIDTH}px; line-height: 0; font-size: 0; border-radius: 20px; overflow: hidden; box-shadow: inset 0 0 0 .5px rgba(0,0,0,.1); background: #f2f2f7; cursor: pointer; }
.dark .chatp-photo { box-shadow: inset 0 0 0 .5px rgba(255,255,255,.1); background: #1c1c1e; }
.chatp-photo img { display: block; width: 100%; height: auto; }
.chatp-playbadge { position: absolute; left: 50%; top: 50%; width: 52px; height: 52px; margin: -26px 0 0 -26px; border-radius: 26px; background: rgba(0,0,0,.56); display: flex; align-items: center; justify-content: center; }
.chatp-playbadge svg { width: 20px; height: 22px; fill: #fff; margin-left: 3px; }
.chatp-viewer { position: absolute; inset: 0; z-index: 4; background: #000; display: flex; align-items: center; justify-content: center; animation: chatp-arrive .2s ease-out; }
.chatp-viewer img { width: 100%; height: auto; }
.chatp-viewer button { position: absolute; top: 12px; left: 12px; width: 36px; height: 36px; border-radius: 50%; border: 0; background: rgba(255,255,255,.18); color: #fff; font-size: 18px; cursor: pointer; }
/* Link card: a crop of the app's LPLinkView for relayapp.im. */
.chatp-link { position: relative; flex: none; width: 280px; margin-bottom: ${TAIL_DEPTH}px; --fill: rgb(8,103,228); }
.chatp-link img { display: block; width: 100%; height: auto; border-radius: 20px !important; }
/* Contact card: RelayContactCardRow.swift:122-133, 462-492. */
.chatp-card { box-sizing: border-box; min-width: 187px; min-height: 58px; padding: 10px 14px; display: flex; align-items: center; gap: 8px; }
.chatp-card-name { flex: 1; font-size: 17px; line-height: 22px; font-weight: 600; letter-spacing: -0.43px; }
.chatp-card-avatar { flex: none; width: 38px; height: 38px; display: flex; align-items: center; justify-content: center; color: #fff; font-weight: 700; font-size: 14.4px; border-radius: 8.55px; }
.chatp-chevron { flex: none; width: 8px; height: 13px; fill: none; stroke: rgba(60,60,67,.33); stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }
.dark .chatp-chevron { stroke: rgba(235,235,245,.33); }
/* Call marker: RelayCallMarkerRow.swift:60-71, 106-130, 426-448. */
.chatp-call { box-sizing: border-box; min-width: 220px; min-height: 58px; padding: 10px 14px; display: flex; align-items: center; gap: 10px; }
.chatp-disc { flex: none; width: 40px; height: 40px; border-radius: 50%; background: rgba(118,118,128,.12); display: flex; align-items: center; justify-content: center; }
.dark .chatp-disc { background: rgba(118,118,128,.24); }
.chatp-disc.is-active { background: #34C759; }
.dark .chatp-disc.is-active { background: #30D158; }
.chatp-disc svg { width: 20px; height: 20px; fill: currentColor; }
.chatp-disc.is-missed { color: #FF3B30; }
.dark .chatp-disc.is-missed { color: #FF453A; }
.chatp-disc.is-active { color: #ffffff; }
.chatp-call-title { font-size: 17px; line-height: 22px; font-weight: 600; letter-spacing: -0.43px; }
.chatp-call-sub { margin-top: 2px; font-size: 15px; line-height: 20px; letter-spacing: -0.23px; color: rgba(60,60,67,.6); }
.dark .chatp-call-sub { color: rgba(235,235,245,.6); }
.chatp-call-sub.is-action { color: #007AFF; }
.dark .chatp-call-sub.is-action { color: #0A84FF; }
/* Location: RelayLocationRows.swift:36-58, 115-134, 464-470, 552, 695. */
.chatp-locreq { box-sizing: border-box; width: 226px; min-height: 190px; padding: 16px; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; white-space: normal; }
.chatp-locdot { position: relative; width: 46px; height: 46px; border-radius: 50%; background: rgba(0,122,255,.22); flex: none; }
.chatp-locdot::before { content: ""; position: absolute; left: 50%; top: 50%; width: 42%; height: 42%; transform: translate(-50%,-50%); border-radius: 50%; background: #fff; }
.chatp-locdot::after { content: ""; position: absolute; left: 50%; top: 50%; width: 30%; height: 30%; transform: translate(-50%,-50%); border-radius: 50%; background: #007AFF; }
.chatp-loctext { margin-top: 8px; text-wrap: balance; }
.chatp-capsule { margin-top: 14px; min-height: 48px; padding: 12px 22px; border: 0; border-radius: 24px; background: #007AFF; color: #fff; font-size: 17px; line-height: 22px; letter-spacing: -0.43px; font-family: inherit; cursor: pointer; }
.dark .chatp-capsule { background: #0A84FF; }
.chatp-menu { position: absolute; z-index: 3; width: 250px; border-radius: 22px; background: rgba(255,255,255,.96); box-shadow: 0 8px 32px rgba(0,0,0,.2); padding: 6px 0; animation: chatp-arrive .18s ease-out; }
.dark .chatp-menu { background: rgba(40,40,42,.97); }
.chatp-menu-title { padding: 6px 16px 4px; font-size: 13px; color: rgba(60,60,67,.6); }
.dark .chatp-menu-title { color: rgba(235,235,245,.6); }
.chatp-menu button { display: flex; align-items: center; gap: 12px; width: 100%; border: 0; background: transparent; padding: 11px 16px; font-size: 17px; letter-spacing: -0.43px; color: inherit; font-family: inherit; cursor: pointer; text-align: left; }
.chatp-menu svg { width: 18px; height: 18px; fill: none; stroke: currentColor; stroke-width: 1.6; flex: none; }
.chatp-map { position: relative; width: 256px; height: 226px; border-radius: 20px; overflow: hidden; margin-bottom: ${TAIL_DEPTH}px; }
.chatp-map img { display: block; width: 256px; height: 226px; }
.chatp-quote.is-media img { border-radius: 17px !important; }
.chatp-badge { position: absolute; left: 8px; top: 8px; height: 25px; border-radius: 12.5px; background: #FF9500; color: #fff; display: flex; align-items: center; gap: 4px; padding: 0 9px 0 7px; font-size: 15px; font-weight: 600; }
.chatp-badge svg { width: 14px; height: 14px; fill: none; stroke: #fff; stroke-width: 2; }
.chatp-locstop { box-sizing: border-box; width: 176px; height: 131px; border-radius: 20px; background: rgba(0,122,255,.14); display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; padding: 0 16px; color: #007AFF; font-size: 17px; line-height: 20px; letter-spacing: -0.43px; margin-bottom: ${TAIL_DEPTH}px; }
.dark .chatp-locstop { color: #0A84FF; background: rgba(10,132,255,.14); }
/* Place card: RelayLocationRows.swift:1047-1069 (210 wide, 210 map, insets
   17.5/14, title 17 semibold, detail 15), 1212 (systemThickMaterial band),
   1176-1188 (the marker's title, 11 semibold systemRed, white edge, 4pt under
   the point). Band colour read off d-received-agent-place.png: (247,246,241). */
.chatp-place { position: relative; flex: none; width: 210px; margin-bottom: ${TAIL_DEPTH}px; --fill: #F7F6F1; cursor: pointer; border: 0; padding: 0; background: none; text-align: left; font-family: inherit; color: inherit; display: block; }
.dark .chatp-place { --fill: #404042; }
.chatp-place:focus-visible { outline: 2px solid #0B75FF; outline-offset: 3px; border-radius: 20px; }
.chatp-place-clip { position: relative; border-radius: 20px; overflow: hidden; background: var(--fill); }
.chatp-place-map { position: relative; width: 210px; height: 210px; line-height: 0; }
.chatp-place-map img { width: 210px; height: 210px; display: block; }
.chatp-place-label { position: absolute; left: 12px; right: 12px; top: 109px; text-align: center; font-size: 11px; line-height: 13px; font-weight: 600; color: #FF3B30; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; text-shadow: 0 0 1px #fff, 0 0 1px #fff, 0 0 2px #fff; }
.chatp-place-band { position: relative; overflow: hidden; }
.chatp-place-under { position: absolute; left: -12px; top: -12px; width: 234px !important; height: 234px; transform: scaleY(-1); filter: blur(14px) saturate(1.3); opacity: .9; }
.chatp-place-text { position: relative; padding: 7.5px 14px 8.8px 17.5px; background: rgba(250,250,247,.8); }
.dark .chatp-place-text { background: rgba(37,37,39,.86); }
.chatp-place-title { font-size: 17px; line-height: 20px; font-weight: 600; letter-spacing: -0.43px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.chatp-place-detail { font-size: 15px; line-height: 18px; letter-spacing: -0.23px; color: rgba(60,60,67,.6); display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
.dark .chatp-place-detail { color: rgba(235,235,245,.6); }
.chatp-place-detail svg { display: inline-block; width: 12px; height: 14px; fill: currentColor; vertical-align: -1px; margin-right: 1px; }
/* Maps, which the card's tap opens (RelayLocationRows.swift:1267-1275). */
.chatp-maps { position: absolute; inset: 0; z-index: 4; display: flex; flex-direction: column; background: #f2f2f7; animation: chatp-arrive .2s ease-out; }
.dark .chatp-maps { background: #1c1c1e; }
.chatp-maps-map { position: relative; flex: 1; overflow: hidden; line-height: 0; }
.chatp-maps-map img { position: absolute; left: 50%; top: 50%; width: 420px; height: 420px; transform: translate(-50%, -50%); }
.chatp-maps-sheet { padding: 16px 20px 20px; border-radius: 22px 22px 0 0; background: #ffffff; box-shadow: 0 -4px 20px rgba(0,0,0,.12); }
.dark .chatp-maps-sheet { background: #2c2c2e; }
.chatp-maps-app { font-size: 13px; color: rgba(60,60,67,.6); margin-bottom: 4px; }
.dark .chatp-maps-app { color: rgba(235,235,245,.6); }
.chatp-maps-title { font-size: 22px; line-height: 28px; font-weight: 700; letter-spacing: .35px; }
.chatp-maps-sheet a { display: inline-block; margin-top: 12px; padding: 10px 16px; border-radius: 20px; background: #0B75FF; color: #fff !important; font-size: 15px; font-weight: 600; text-decoration: none; border: 0; }
.chatp-close { position: absolute; top: 12px; right: 12px; z-index: 1; width: 32px; height: 32px; border-radius: 50%; border: 0; background: rgba(120,120,128,.24); color: inherit; font-size: 15px; cursor: pointer; }
/* Document card: RelayFileMessageRow.swift:29-36 (LPLinkView's neutral
   E9E9EB / 262629), MessageBubble.swift:21 (246 wide), RelayFileMessageRow
   .swift:858-870 (the file's name and size as LPLinkView's title). The page
   thumbnail fills the top the way the relayapp.im link card's image does. */
.chatp-doc { position: relative; flex: none; display: block; width: 246px; margin-bottom: ${TAIL_DEPTH}px; --fill: #E9E9EB; border: 0; padding: 0; background: none; text-align: left; font-family: inherit; color: inherit; cursor: pointer; }
.dark .chatp-doc { --fill: #262629; }
.chatp-doc:focus-visible { outline: 2px solid #0B75FF; outline-offset: 3px; border-radius: 20px; }
.chatp-doc-clip { position: relative; border-radius: 20px; overflow: hidden; background: var(--fill); }
.chatp-doc-clip::after { content: ""; position: absolute; inset: 0; border-radius: 20px; box-shadow: inset 0 0 0 .5px rgba(0,0,0,.1); pointer-events: none; }
.dark .chatp-doc-clip::after { box-shadow: inset 0 0 0 .5px rgba(255,255,255,.1); }
.chatp-doc-thumb { height: 128px; background: #ffffff; overflow: hidden; line-height: 0; }
.chatp-doc-thumb img { display: block; width: 100% !important; height: auto; }
.chatp-doc-cap { padding: 11px 16px; font-size: 17px; line-height: 20px; font-weight: 600; letter-spacing: -0.43px; }
.chatp-doc-cap span { display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.chatp-ql { position: absolute; inset: 0; z-index: 4; background: #f2f2f7; display: flex; flex-direction: column; animation: chatp-arrive .2s ease-out; }
.dark .chatp-ql { background: #000000; }
.chatp-ql-bar { position: relative; padding: 18px 56px 12px; text-align: center; font-size: 17px; font-weight: 600; letter-spacing: -0.43px; }
.chatp-ql-page { flex: 1; min-height: 0; margin: 4px 28px 28px; overflow: hidden; line-height: 0; }
.chatp-ql-page img { display: block; width: 100% !important; height: auto; box-shadow: 0 2px 12px rgba(0,0,0,.12); }
@media (prefers-reduced-motion: reduce) {
  .chatp *, .chatp *::before, .chatp *::after { animation: none !important; transition: none !important; scroll-behavior: auto !important; }
  .chatp-typing i { opacity: .325; }
}
`;

  // ---------- State ----------
  const [read, setRead] = useState(false);
  const [flash, setFlash] = useState(false);
  const [playing, setPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const [typing, setTyping] = useState(true);
  const [viewer, setViewer] = useState(false);
  const [video, setVideo] = useState(false);
  const [menu, setMenu] = useState(false);
  const [share, setShare] = useState(null);
  const [status, setStatus] = useState("completed");
  const [ranged, setRanged] = useState(true);
  const [maps, setMaps] = useState(null);
  const root = useRef(null);

  // ---------- Pieces ----------
  const tail = (side) => (
    <svg className={"chatp-tail " + side} viewBox="0 0 23 24" aria-hidden="true" focusable="false"><path d={TAIL} /></svg>
  );
  const avatar = (name, ground, isAgent, spacer) => (
    <div className={"chatp-avatar" + (isAgent ? " is-agent" : "") + (spacer ? " is-spacer" : "")}
      style={{ background: `linear-gradient(${GROUNDS[ground][0]}, ${GROUNDS[ground][1]})`, borderRadius: isAgent ? undefined : "50%" }}
      aria-hidden="true">{name.slice(0, 1).toUpperCase()}</div>
  );
  const bubble = (side, content, opts = {}) => (
    <div className={"chatp-bubble " + side + (opts.tail !== false ? " has-tail" : "") + (opts.className ? " " + opts.className : "")}
      style={opts.style} onClick={opts.onClick} role={opts.onClick ? "button" : undefined}
      tabIndex={opts.onClick ? 0 : undefined} aria-label={opts.ariaLabel}
      onKeyDown={opts.onClick ? (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); opts.onClick(e); } } : undefined}>
      {content}
      {opts.tail !== false ? tail(side) : null}
    </div>
  );
  const row = (side, children, opts = {}) => (
    <div className={"chatp-row " + side + (opts.className ? " " + opts.className : "")} style={{ marginTop: opts.gap ?? 0 }}>
      {opts.avatar || null}
      <div className="chatp-col">{children}</div>
    </div>
  );
  const receipt = (text) => {
    // ChatMessage.swift:280-293 statusFooterText; RelayTextMessageCell.swift
    // receiptAttributedText: the state word semibold, the time regular.
    const [word, ...rest] = text.split(" ");
    return <div className="chatp-receipt" role="status"><b>{word}</b>{rest.length ? " " + rest.join(" ") : ""}</div>;
  };
  // Inline Markdown, the six formats messages/send.mdx lists. The app hides
  // the delimiters on text it receives (RelayMessageBodyText,
  // MessageBubble.swift:196-290).
  const markdown = (source) => {
    const out = [];
    const re = /\*\*(.+?)\*\*|~~(.+?)~~|`([^`]+)`|\[([^\]]+)\]\(([^)]+)\)|<u>(.+?)<\/u>|\*(.+?)\*/g;
    let last = 0;
    let m;
    let k = 0;
    while ((m = re.exec(source))) {
      if (m.index > last) out.push(source.slice(last, m.index));
      if (m[1] !== undefined) out.push(<strong key={k++}>{m[1]}</strong>);
      else if (m[2] !== undefined) out.push(<s key={k++}>{m[2]}</s>);
      else if (m[3] !== undefined) out.push(<code key={k++}>{m[3]}</code>);
      else if (m[4] !== undefined) out.push(<a key={k++} href={m[5]} onClick={(e) => e.preventDefault()}>{m[4]}</a>);
      else if (m[6] !== undefined) out.push(<u key={k++}>{m[6]}</u>);
      else if (m[7] !== undefined) out.push(<em key={k++}>{m[7]}</em>);
      last = re.lastIndex;
    }
    if (last < source.length) out.push(source.slice(last));
    return out;
  };

  // Tapback pile over a bubble's top corner, copied from Relay-iOS
  // origin/staging 1ef73e93 Views/Transcript/RelayTapbackBalloon.swift
  // (RelayTapbackGeometry and layoutSubviews): one balloon per reactor, Ø34,
  // centred 2.83pt inside the corner edge and 10.33pt above the top edge;
  // older balloons step 19.985419pt toward the screen centre; only the front
  // balloon carries the trail, a Ø10 dot 18.75pt out on a 36° ray and a Ø5
  // dot 10.5pt further on a 38° ray, descending on the outer side. The front
  // balloon and its dots are ONE silhouette, and a 1.33pt seam in the
  // transcript colour sits behind each silhouette, never between its parts.
  // `reactions` runs back to front.
  const tapbacks = (reactions, isOutgoing) => {
    if (!reactions.length) return null;
    const R = 17;
    const STEP = 19.985419;
    const INSET = 2.83;
    const RISE = 10.33;
    const SEAM = 4 / 3;
    const n = reactions.length;
    const dir = isOutgoing ? -1 : 1;
    const md = { x: 18.75 * Math.sin(36 * Math.PI / 180), y: 18.75 * Math.cos(36 * Math.PI / 180) };
    const sd = { x: md.x + 10.5 * Math.sin(38 * Math.PI / 180), y: md.y + 10.5 * Math.cos(38 * Math.PI / 180) };
    const centre = (i) => -dir * STEP * (n - 1 - i);
    const style = { top: -RISE, [isOutgoing ? "left" : "right"]: INSET };
    return (
      <svg className="chatp-tapback" style={style} width="1" height="1" aria-hidden="true" focusable="false">
        {reactions.map((r, i) => {
          const circles = i === n - 1
            ? [[0, 0, R], [dir * md.x, md.y, 5], [dir * sd.x, sd.y, 2.5]]
            : [[centre(i), 0, R]];
          return (
            <g key={i}>
              <g className="chatp-tb-seam">{circles.map(([x, y, radius], k) => <circle key={k} cx={x} cy={y} r={radius + SEAM} />)}</g>
              <g className={"chatp-tb-fill" + (r.mine ? " mine" : "")}>{circles.map(([x, y, radius], k) => <circle key={k} cx={x} cy={y} r={radius} />)}</g>
              <text className="chatp-tb-glyph" x={centre(i)} y={0} textAnchor="middle" dominantBaseline="central">{r.glyph}</text>
            </g>
          );
        })}
      </svg>
    );
  };

  // Seeded placeholder waveform, RelayAudioMessageRow.swift:277-297.
  const waveform = (seed, count) => {
    let hash = 14695981039346656037n;
    for (const ch of seed) { hash ^= BigInt(ch.codePointAt(0)); hash = (hash * 1099511628211n) & 0xffffffffffffffffn; }
    let state = hash === 0n ? 1n : hash;
    const ref = [];
    for (let i = 0; i < 100; i += 1) {
      state = (state * 1664525n + 1013904223n) & 0xffffffffffffffffn;
      const random = Number(state & 0xffffn) / 65535;
      const fast = 0.5 + 0.5 * Math.sin(i * 1.18 + seed.length * 0.31);
      const slow = 0.5 + 0.5 * Math.sin(i * 0.37 + seed.length * 0.19);
      ref.push(Math.min(0.98, Math.max(0.12, 0.16 + random * 0.46 + fast * 0.30 + slow * 0.18)));
    }
    return Array.from({ length: count }, (_, i) => {
      const a = Math.floor(i * 100 / count);
      const b = Math.max(a + 1, Math.floor((i + 1) * 100 / count));
      return Math.max(...ref.slice(a, b));
    });
  };

  const phoneGlyph = (
    <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M6.6 10.8a15.2 15.2 0 0 0 6.6 6.6l2.2-2.2c.3-.3.7-.4 1-.2 1.1.4 2.3.6 3.6.6.6 0 1 .4 1 1V20c0 .6-.4 1-1 1A17 17 0 0 1 3 4c0-.6.4-1 1-1h3.5c.6 0 1 .4 1 1 0 1.3.2 2.5.6 3.6.1.3 0 .7-.2 1z" /></svg>
  );
  const chevron = <svg className="chatp-chevron" viewBox="0 0 8 13" aria-hidden="true" focusable="false"><path d="M1.5 1.5l5 5-5 5" /></svg>;

  // A place's words (PlaceComponent, Models/LocationSharing.swift): the card's
  // title is the name, else "Dropped Pin"; Maps names the point with the
  // name, else the address, else "Dropped Pin". Blank counts as absent.
  const present = (v) => (typeof v === "string" && v.trim() ? v.trim() : null);
  // The Apple logo (simple-icons "apple", CC0) for the " Maps" line; the app
  // draws SF Symbols "apple.logo" (RelayLocationRows.swift:1077-1088).
  const appleLogo = <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M12.152 6.896c-.948 0-2.415-1.078-3.96-1.04-2.04.027-3.91 1.183-4.961 3.014-2.117 3.675-.546 9.103 1.519 12.09 1.013 1.454 2.208 3.09 3.792 3.039 1.52-.065 2.09-.987 3.935-.987 1.831 0 2.35.987 3.96.948 1.637-.026 2.676-1.48 3.676-2.948 1.156-1.688 1.636-3.325 1.662-3.415-.039-.013-3.182-1.221-3.22-4.857-.026-3.04 2.48-4.494 2.597-4.559-1.429-2.09-3.623-2.324-4.39-2.376-2-.156-3.675 1.09-4.61 1.09zM15.53 3.83c.843-1.012 1.4-2.427 1.245-3.83-1.207.052-2.662.805-3.532 1.818-.78.896-1.454 2.338-1.273 3.714 1.338.104 2.715-.688 3.559-1.701" /></svg>;
  // The Dropped Pin card (RelayLocationRows.swift:1005-1400). A tap opens
  // Maps at the point, named (RelayPlaceRowView.openInMaps).
  const placeCard = (place, side, withTail) => {
    const title = present(place.name) || "Dropped Pin";
    const address = present(place.address);
    return (
      <div className="chatp-place" role="button" tabIndex={0} onClick={() => setMaps(place)}
        onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); setMaps(place); } }}
        aria-label={[title, address, "Maps"].filter(Boolean).join(", ") + ". Opens Apple Maps"}>
        <div className="chatp-place-clip">
          <div className="chatp-place-map">
            <img src="/images/chat/place-map.png" alt="" />
            <span className="chatp-place-label" aria-hidden="true">{title}</span>
          </div>
          <div className="chatp-place-band">
            <img className="chatp-place-under" src="/images/chat/place-map.png" alt="" />
            <div className="chatp-place-text">
              <div className="chatp-place-title">{title}</div>
              {address ? <div className="chatp-place-detail">{address}</div> : null}
              <div className="chatp-place-detail">{appleLogo}Maps</div>
            </div>
          </div>
        </div>
        {withTail ? tail(side) : null}
      </div>
    );
  };
  const mapsOverlay = (place) => {
    const name = present(place.name) || present(place.address) || "Dropped Pin";
    const href = `https://maps.apple.com/?ll=${place.latitude},${place.longitude}&q=${encodeURIComponent(name)}`;
    return (
      <div className="chatp-maps" role="dialog" aria-modal="true" aria-label="Apple Maps"
        onKeyDown={(e) => { if (e.key === "Escape") setMaps(null); }}>
        <button type="button" className="chatp-close" autoFocus aria-label="Close" onClick={() => setMaps(null)}>✕</button>
        <div className="chatp-maps-map"><img src="/images/chat/place-map.png" alt="" /></div>
        <div className="chatp-maps-sheet">
          <div className="chatp-maps-app">The app opens Apple Maps here</div>
          <div className="chatp-maps-title">{name}</div>
          {present(place.address) && name !== present(place.address) ? <div className="chatp-place-detail">{present(place.address)}</div> : null}
          <a href={href} target="_blank" rel="noopener noreferrer">Open in Apple Maps</a>
        </div>
      </div>
    );
  };
  // A text part and the balloon that follows it: the composite row's
  // grammar (RelayCompositeRow.swift:14-22), the lobe on the last part only,
  // 5pt between parts of different kinds.
  const stack = (side, items) => row(side, items.map((item, i) => (
    <div key={i} style={{ marginTop: i ? 5 : 0 }}>{item(i === items.length - 1)}</div>
  )));

  // ---------- Scenes ----------
  let title = "Echo";
  let isGroup = false;
  let body = null;
  let controls = null;
  let overlay = null;
  // The corner icon: Reset demo once the reader has changed something, or
  // Replay for a scene whose only motion is the message arriving.
  let corner = null;
  let caption;
  // A state switcher at the frame's bottom edge (style.css .relay-preview-seg).
  const toggle = (pressed, onClick, words) => (
    <div className="relay-preview-seg">
      <button type="button" aria-pressed={pressed} onClick={onClick}>{words}</button>
    </div>
  );

  const parts = json && json.message && json.message.parts;

  if (scene === "send" || scene === "markdown") {
    const text = parts[0].value;
    body = row("in", bubble("in", scene === "markdown" ? markdown(text) : text));
  } else if (scene === "replies") {
    // The person sent a caption and a photo; the agent replies to part 1.
    // Quote on the original author's side in the viewer's blue family
    // (MessageReplyPreview.swift:556-579, 632-657), 8.5pt above the reply.
    const target = json.message.reply_to.part_index;
    const original = [
      <div key="t">{bubble("out", "Does the chart look right?", { tail: false })}</div>,
      <div key="p" style={{ marginTop: 4 }}>
        <button type="button" className={"chatp-photo" + (flash ? " chatp-flash" : "")} id="chatp-original" tabIndex={-1} aria-label="Chart, part 1">
          {/* The chart the words ask about, generated 2026-09-26 with Google's
              gemini-3-pro-image through the Gemini API (aspect 4:3), prompt:
              "A clean, photographic close-up of a laptop screen showing a
              simple quarterly sales bar chart: four blue bars labelled Q1, Q2,
              Q3, Q4 rising left to right, a short title 'Quarterly sales',
              light background, soft daylight, shallow depth of field,
              product-photography quality, no people, no logos." */}
          <img src="/images/chat/chart-quarterly-sales.jpg" alt="" />
        </button>
      </div>,
    ];
    const jump = (e) => {
      setFlash(false);
      requestAnimationFrame(() => setFlash(true));
      setTimeout(() => setFlash(false), 1200);
    };
    // The reply answers ONE part of a two-part message, so the app does not
    // take the adjacent-row shortcut (ReplyLinePlanner.swift, "An exact-part
    // reply may not bracket a whole multipart row"): it shows the quote of
    // that part and joins it to the reply with the reply line. The line is
    // ReplyLineShape (MessageReplyPreview.swift): a 4pt round-capped stroke
    // on the leading centreline 32pt in, black 8% (white 16% in dark); an
    // arm at the quote's vertical centre reaching 32pt past the centreline
    // on ReplyBracketCurve's three cubics, and a reduced cap 2pt + half a
    // stroke above the reply (capAboveBubbleReduced).
    const QUOTE_H = 50;
    const REPLY_GAP = 8.5;
    const X = 16;
    const topY = QUOTE_H / 2;
    const bottomY = QUOTE_H + REPLY_GAP - (2 + 2);
    const fullExtent = 21 * 1.52866;
    const used = Math.min(fullExtent, bottomY - topY);
    const k = used / fullExtent;
    const r = 21 * k;
    const armX = X + 32 * k;
    const f = (n) => n.toFixed(2);
    const linePath = [
      `M ${f(armX)} ${f(topY)}`,
      `C ${f(X + r * 1.08849)} ${f(topY)} ${f(X + r * 0.868407)} ${f(topY)} ${f(X + r * 0.631494)} ${f(topY + r * 0.0749114)}`,
      `C ${f(X + r * 0.372824)} ${f(topY + r * 0.16906)} ${f(X + r * 0.16906)} ${f(topY + r * 0.372824)} ${f(X + r * 0.0749114)} ${f(topY + r * 0.631494)}`,
      `C ${f(X + r * 0.0749114)} ${f(topY + r * 0.868407)} ${f(X)} ${f(topY + r * 1.08849)} ${f(X)} ${f(topY + used)}`,
      `L ${f(X)} ${f(bottomY)}`,
    ].join(" ");
    body = (
      <div style={{ position: "relative" }}>
        {row("out", <div className="chatp-col" style={{ alignItems: "flex-end" }}>{original}</div>)}
        <div style={{ height: 12 }} aria-hidden="true" />
        <div style={{ position: "relative" }}>
          {row("out", (
            <button type="button" className="chatp-quote is-own is-media" onClick={jump}
              style={{ height: QUOTE_H, marginBottom: REPLY_GAP }}
              aria-label={`Replying to you: chart, part ${target}. Jumps to the chart`}>
              <img src="/images/chat/chart-quarterly-sales.jpg" alt="" />
            </button>
          ))}
          <svg className="chatp-replyline" width="1" height="1" aria-hidden="true" focusable="false"><path d={linePath} /></svg>
          {row("in", bubble("in", parts[0].value))}
        </div>
      </div>
    );
    caption = "Tap the quote to jump to the chart";
  } else if (scene === "reactions") {
    // The agent's reaction, as the person's app draws a reaction from
    // someone else on their own blue bubble: one grey balloon on the
    // bubble's top-leading corner (TranscriptReactionPile.swift,
    // RelayTapbackBalloon.swift). The glyph is the JSON's own type.
    const agentGlyph = GLYPHS[json.type] || json.custom_emoji;
    // The balloon rises 27.33pt over the bubble; 28px more on top keeps
    // 16px of frame above the badge, the same as below the bubble.
    body = row("out", (
      <div style={{ position: "relative", marginTop: 28 }}>
        {bubble("out", "Can you send the report by Friday?")}
        {tapbacks([{ glyph: agentGlyph, mine: false }], true)}
      </div>
    ));
  } else if (scene === "mentions") {
    // Group: sender caption, avatar beside the tailed balloon, the mention
    // semibold (MessageBubble.swift:381-395, MentionRangeMapping.swift:44-61).
    isGroup = true;
    const part = parts[0];
    const value = part.value;
    const [start, end] = ranged && part.mention_range ? part.mention_range : [0, value.length];
    const content = [value.slice(0, start), <span key="m" className="chatp-mention">{value.slice(start, end)}</span>, value.slice(end)];
    body = row("in", [
      <div key="s" className="chatp-sender">Planner</div>,
      <div key="b">{bubble("in", content)}</div>,
    ], { avatar: avatar("Planner", "teal", true) });
    controls = toggle(ranged, () => setRanged((r) => !r), ranged ? "mention_range [0, 4]" : "No mention_range");
  } else if (scene === "receipts") {
    body = row("out", [
      <div key="b">{bubble("out", "Can you check the draft?")}</div>,
      <div key="r">{receipt(read ? "Read 9:41 AM" : "Delivered")}</div>,
    ]);
    controls = toggle(read, () => setRead((r) => !r), read ? "Back to Delivered" : "Agent marks the chat Read");
  } else if (scene === "voice-memo") {
    const seconds = 12;
    const bars = waveform(json.attachment_id, 48);
    const toggle = () => {
      if (playing) { setPlaying(false); return; }
      setPlaying(true);
      const startedAt = performance.now() - progress * seconds * 1000;
      const stepFn = () => {
        const p = Math.min(1, (performance.now() - startedAt) / (seconds * 1000));
        setProgress(p);
        if (p < 1 && document.body.contains(root.current)) {
          root.current.__raf = requestAnimationFrame(stepFn);
        } else { setPlaying(false); if (p >= 1) setProgress(0); }
      };
      root.current.__raf = requestAnimationFrame(stepFn);
    };
    body = row("in", (
      <div className="chatp-audio">
        <button type="button" className="chatp-play" onClick={() => { if (playing && root.current) cancelAnimationFrame(root.current.__raf); toggle(); }}
          aria-label={playing ? "Pause voice message" : "Play voice message"}>
          {playing
            ? <svg viewBox="0 0 11 13" aria-hidden="true" focusable="false"><rect x="1" y="0.5" width="3" height="12" rx="1" /><rect x="7" y="0.5" width="3" height="12" rx="1" /></svg>
            : <svg viewBox="0 0 11 13" aria-hidden="true" focusable="false" style={{ marginLeft: 1.5 }}><path d="M1 1.2v10.6c0 .8.8 1.2 1.5.8l8.4-5.3c.6-.4.6-1.2 0-1.6L2.5.4C1.8 0 1 .4 1 1.2z" /></svg>}
        </button>
        <div className="chatp-wave" aria-hidden="true">
          {bars.map((l, i) => <span key={i} className={(i + 0.5) / bars.length <= progress ? "played" : ""} style={{ height: Math.max(2, 30 * l) }} />)}
        </div>
        <span className="chatp-duration">0:{String(seconds).padStart(2, "0")}</span>
        {tail("in")}
      </div>
    ));
  } else if (scene === "link") {
    const host = (() => { try { return new URL(parts[0].value).host; } catch (e) { return parts[0].value; } })();
    body = row("in", (
      <div className="chatp-link" role="img" aria-label={`Link preview: All your agents. One app. ${host}`}>
        <img src="/images/chat/link-relayapp.png" alt="" />
        {/* Only the lobe: the card's caption runs to the corner. */}
        <svg className="chatp-tail in" viewBox="0 12 23 12" style={{ top: "calc(100% - 4px)", height: 12 }} aria-hidden="true" focusable="false"><path d={TAIL} /></svg>
      </div>
    ));
  } else if (scene === "attachment") {
    // A media part to send, or one as it arrives, which names its type.
    const media = json.message ? json.message.parts[0] : json;
    const typed = typeof media.mime_type === "string";
    const isVideo = typed ? media.mime_type.startsWith("video/") : video;
    // A part as it arrives came from a person: their own screen draws it on
    // the right. The photo (images/chat/photo-tartine.jpg, 786 x 474, the
    // size the JSON states) was generated 2026-09-26 with gemini-3-pro-image
    // through the Gemini API, prompt: "Overhead bakery photography on a light
    // wooden table: a golden sourdough loaf, two croissants, a morning bun and
    // a cappuccino, bright natural daylight, clean and appetizing, magazine
    // quality, no people, no text, no logos."
    body = row(typed ? "out" : "in", (
      <button type="button" className="chatp-photo" onClick={() => setViewer(true)} aria-label={isVideo ? "Video. Tap to open" : "Photo. Tap to open"}>
        <img src="/images/chat/photo-tartine.jpg" alt="" />
        {isVideo ? <span className="chatp-playbadge"><svg viewBox="0 0 20 22" aria-hidden="true" focusable="false"><path d="M1 1.6v18.8c0 1.1 1.2 1.8 2.2 1.2l15.6-9.4c.9-.6.9-1.9 0-2.4L3.2.4C2.2-.2 1 .5 1 1.6z" /></svg></span> : null}
      </button>
    ));
    overlay = viewer ? (
      <div className="chatp-viewer" role="dialog" aria-modal="true" aria-label={isVideo ? "Video viewer" : "Photo viewer"}
        onKeyDown={(e) => { if (e.key === "Escape") setViewer(false); }}>
        <button type="button" autoFocus aria-label="Close" onClick={() => setViewer(false)}>✕</button>
        <img src="/images/chat/photo-tartine.jpg" alt="" />
      </div>
    ) : null;
    controls = typed ? null : toggle(video, () => setVideo((v) => !v), video ? "Show as a photo" : "Show as a video");
  } else if (scene === "typing") {
    const handle = json.data.contact.handle;
    title = handle.charAt(0).toUpperCase() + handle.slice(1);
    body = typing ? row("in", (
      <div className="chatp-typing" role="status" aria-label={`${title} is typing`}>
        <span className="chatp-typing-trail" style={{ width: 11.5, height: 11.5, left: 5.64 - 5.75, top: 35 - 2.7 - 5.75 }} />
        <span className="chatp-typing-trail" style={{ width: 5, height: 5, left: -2.45 - 2.5, top: 35 + 4.21 - 2.5 }} />
        <i /><i /><i />
      </div>
    )) : <div role="status" aria-label="Not typing" style={{ height: 42 }} />;
    controls = toggle(typing, () => setTyping((t) => !t), typing ? "Stop typing" : "Start typing");
  } else if (scene === "location") {
    // Request card, the Share My Location menu, then the person's card.
    // Models/LocationSharing.swift:141-163: Once first, then the three
    // durations, word for word. Once sends one place and starts no share.
    const durations = [["once", "Once", null], ["hour", "For One Hour", "1 hr"], ["day", "Until End of Day", null], ["forever", "Indefinitely", null]];
    const chosen = share === "once" ? null : durations.find((d) => d[0] === share);
    const badge = chosen ? (chosen[0] === "hour" ? "1 hr" : chosen[0] === "day" ? "9 hr" : null) : null;
    body = (
      <div style={{ position: "relative", minHeight: menu ? 376 : undefined }}>
        {row("in", bubble("in", (
          <div className="chatp-locreq" style={{ minHeight: share && share !== "once" ? 190 : 204 }}>
            <span className="chatp-locdot" aria-hidden="true" />
            <div className="chatp-loctext">{title} requested your location</div>
            {share && share !== "once" ? null : (
              <button type="button" className="chatp-capsule" aria-haspopup="menu" aria-expanded={menu}
                onClick={() => setMenu((m) => !m)}>Share My Location</button>
            )}
          </div>
        ), { style: { padding: 0 } }))}
        {menu ? (
          <div className="chatp-menu" role="menu" aria-label="Share My Location" style={{ left: 0, top: 132 }}
            onKeyDown={(e) => { if (e.key === "Escape") setMenu(false); }}>
            <div className="chatp-menu-title">Share My Location</div>
            {durations.map((d) => (
              <button type="button" role="menuitem" key={d[0]} onClick={() => { setShare(d[0]); setMenu(false); }}>
                <svg viewBox="0 0 18 18" aria-hidden="true" focusable="false">
                  {d[0] === "once" ? <g><circle cx="9" cy="5.6" r="3.6" /><path d="M9 9.2v7.3" /></g> : null}
                  {d[0] === "hour" ? <g><circle cx="9" cy="9" r="7.2" /><path d="M9 4.8V9l2.8 1.7" /></g> : null}
                  {d[0] === "day" ? <g><rect x="2" y="3" width="14" height="13" rx="2.4" /><path d="M2 7h14M5.5 1.5v3M12.5 1.5v3" /></g> : null}
                  {d[0] === "forever" ? <path d="M9 9c-1.6-2-3-3-4.4-3a3 3 0 0 0 0 6C6 12 7.4 11 9 9zm0 0c1.6 2 3 3 4.4 3a3 3 0 0 0 0-6C12 6 10.6 7 9 9z" /> : null}
                </svg>
                {d[1]}
              </button>
            ))}
          </div>
        ) : null}
        {share === "once" ? row("out", placeCard({}, "out", true), { gap: 12 }) : share === "stopped" ? row("out", (
          <div className="chatp-locstop" style={{ position: "relative", "--fill": "rgba(0,122,255,.14)" }}>
            <span className="chatp-locdot" aria-hidden="true" style={{ marginBottom: 8 }} />You stopped sharing location
          </div>
        ), { gap: 12 }) : chosen ? row("out", [
          <div key="m" className="chatp-tailed" style={{ position: "relative", marginBottom: TAIL_DEPTH, "--fill": "rgba(120,120,128,.16)" }}>
          <div className="chatp-map" style={{ marginBottom: 0 }} role="img" aria-label={"Your location" + (badge ? ", " + badge : "")}>
            <img src="/images/chat/location-map.png" alt="" />
            {badge ? <span className="chatp-badge"><svg viewBox="0 0 14 14" aria-hidden="true" focusable="false"><circle cx="7" cy="7.8" r="5.2" /><path d="M7 5v3M5.4 1h3.2" /></svg>{badge}</span> : null}
          </div>
          {tail("out")}
          </div>,
          <div key="r">{receipt("Delivered")}</div>,
        ], { gap: 12 }) : null}
      </div>
    );
    controls = share && share !== "stopped" && share !== "once" ? toggle(false, () => setShare("stopped"), "Stop sharing") : null;
    corner = share ? { label: "Reset demo", run: () => { setShare(null); setMenu(false); } } : null;
  } else if (scene === "place") {
    // An agent's message draws on the left; a person's own place, as the
    // agent receives it, draws on the person's screen on the right.
    const side = json.message ? "in" : "out";
    const list = json.message ? json.message.parts : [json];
    body = stack(side, list.map((part) => (last) => (
      part.type === "place" ? placeCard(part, side, last) : bubble(side, part.value, { tail: last })
    )));
    overlay = maps ? mapsOverlay(maps) : null;
  } else if (scene === "document") {
    // Text, then the document card. The file is real: Claude Shannon, "A
    // Mathematical Theory of Communication" (1948), downloaded 2026-09-26 from
    // https://people.math.harvard.edu/~ctm/home/text/others/shannon/entropy/entropy.pdf
    // (366,296 bytes, which ByteCountFormatter's .file style shows as
    // "366 KB", RelayFileMessageRow.swift:107-108). The thumbnail is its
    // real first page, rendered with qlmanage. The words above it come from
    // the JSON.
    const file = ["shannon-mathematical-theory-of-communication.pdf", "366 KB"];
    const page = <img src="/images/chat/shannon-page-1.jpg" alt="" />;
    body = stack("in", json.message.parts.map((part) => (last) => (
      part.type === "media" ? (
        <div className="chatp-doc" role="button" tabIndex={0} onClick={() => setViewer(true)} aria-label={file.join(", ") + ". Tap to open"}
          onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); setViewer(true); } }}>
          <div className="chatp-doc-clip">
            <div className="chatp-doc-thumb" aria-hidden="true">{page}</div>
            <div className="chatp-doc-cap"><span>{file[0]}</span><span>{file[1]}</span></div>
          </div>
          {last ? tail("in") : null}
        </div>
      ) : bubble("in", part.value, { tail: last })
    )));
    // The tap opens the file in Quick Look (RelayFileMessageRow.swift:455-475).
    overlay = viewer ? (
      <div className="chatp-ql" role="dialog" aria-modal="true" aria-label={"Quick Look: " + file[0]}
        onKeyDown={(e) => { if (e.key === "Escape") setViewer(false); }}>
        <div className="chatp-ql-bar">{file[0]}<button type="button" className="chatp-close" autoFocus aria-label="Close" onClick={() => setViewer(false)}>✕</button></div>
        <div className="chatp-ql-page" aria-hidden="true">{page}</div>
      </div>
    ) : null;
  } else if (scene === "contact-card") {
    const card = json;
    const name = [card.first_name, card.last_name].filter(Boolean).join(" ");
    const initials = name.split(" ").slice(0, 2).map((w) => w[0]).join("").toUpperCase();
    title = name;
    body = row("in", bubble("in", (
      <div className="chatp-card">
        <span className="chatp-card-name">{name}</span>
        <span className="chatp-card-avatar" style={{ background: `linear-gradient(${GROUNDS.green[0]}, ${GROUNDS.green[1]})` }} aria-hidden="true">{initials}</span>
        {chevron}
      </div>
    ), { style: { padding: 0 } }));
  } else if (scene === "group") {
    isGroup = true;
    const from = json.from;
    const sender = from.charAt(0).toUpperCase() + from.slice(1);
    body = row("in", [
      <div key="s" className="chatp-sender">{sender}</div>,
      <div key="b">{bubble("in", parts[0].value)}</div>,
    ], { avatar: avatar(sender, "rose", true) });
  } else if (scene === "call") {
    title = "Atlas";
    // MessageComponent.swift:168-254: titles and subtitles by status.
    const states = {
      ringing: ["Incoming Call", "Ringing…", ""],
      "in-progress": ["Incoming Call", "0:12", "is-active"],
      completed: ["Incoming Call", "3 min", ""],
      "no-answer": ["Missed Call", "Call Back", "is-missed"],
    };
    const [t, sub, disc] = states[status];
    body = row("in", bubble("in", (
      <div className="chatp-call">
        <span className={"chatp-disc " + disc} aria-hidden="true">{phoneGlyph}</span>
        <span>
          <div className="chatp-call-title">{t}</div>
          <div className={"chatp-call-sub" + (sub === "Call Back" ? " is-action" : "")}>{sub}</div>
        </span>
      </div>
    ), { style: { padding: 0 } }));
    controls = (
      <div className="relay-preview-seg">
        {Object.keys(states).map((s) => (
          <button type="button" key={s} aria-pressed={status === s} onClick={() => setStatus(s)}>{s}</button>
        ))}
      </div>
    );
  }

  useEffect(() => () => { if (root.current && root.current.__raf) cancelAnimationFrame(root.current.__raf); }, []);

  return (
    <Frame className="relay-preview" caption={caption}>
    <div className="chatp" ref={root} role="group" aria-label={label}>
      <style dangerouslySetInnerHTML={{ __html: CSS }} />
      <div className={"chatp-phone" + (overlay ? " has-overlay" : "")}>
        <div className={"chatp-transcript" + (isGroup ? " is-group" : "") + (controls ? " has-bar" : "")}
>
          {body}
        </div>
        {overlay}
      </div>
      {controls ? <div className="relay-preview-bar">{controls}</div> : null}
      {corner && !overlay ? (
        <button type="button" className="relay-preview-reset" aria-label={corner.label} title={corner.label} onClick={corner.run}>
          <Icon icon="rotate-left" size={16} />
        </button>
      ) : null}
    </div>
    </Frame>
  );
};
