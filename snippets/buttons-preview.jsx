// Adapted from buttons-docs-fix dc55e9e; bubble geometry shared by component previews.
// A rendered buttons part, drawn the way the app draws it: a vertical stack of
// equally sized pills capped at 75% of the maximum text-balloon column, a URL
// button marked with an arrow, and the tap as
// the person's own bubble. The bubble is the app's own silhouette: a port of
// RelayBubbleGeometry.trailingRoundTailedPath (Relay-iOS,
// Views/MessageBubbleShape.swift), the iOS 26.5 BubbleKit round-tailed bubble
// at radius 20, with the app's 17pt body text and 14pt side insets.
//
// `rows` switches the same silhouette to the selection card the app draws
// (Relay-iOS, Views/Transcript/RelaySelectionRow.swift): the balloon fills the
// text-balloon column, carries a title a step below body text, a smaller
// second line or one line per chosen label, and a trailing chevron. `side`
// mirrors the tail for an incoming balloon; the glyphs are never mirrored.
export const MessageBubble = ({ text, rows, side = "trailing", chevron = false, width = 260 }) => {
  // Everything lives inside the component: the snippet is compiled as MDX,
  // which keeps only exports in scope and reads a capitalised tag as an MDX
  // component.
  const WIDE = 20;
  const TAIL_DEPTH_FACTOR = 0.33925;
  const P = (x, y) => ({ x, y });
  const corner = (start, c1, c2, p1, c3, c4, p2, c5, c6, end) => ({ start, c1, c2, p1, c3, c4, p2, c5, c6, end });
  const KEYS = ["start", "c1", "c2", "p1", "c3", "c4", "p2", "c5", "c6", "end"];
  const lerp = (a, b, t) => P(a.x + (b.x - a.x) * t, a.y + (b.y - a.y) * t);
  const mix = (a, b, t) => Object.fromEntries(KEYS.map((k) => [k, lerp(a[k], b[k], t)]));
  const scaleCorner = (c, s) => Object.fromEntries(KEYS.map((k) => [k, P(c[k].x * s, c[k].y * s)]));
  const swap = (p) => P(p.y, p.x);

  // Direct iOS 26.5 control-point observations, one profile per body extent.
  const samples = [
    { extent: 40,
      upper: corner(P(0, 20), P(0, 17.465204710537), P(0.481850397518, 14.953513771483), P(1.419892543171, 12.598675328518), P(3.452798428579, 7.495317284242), P(7.45648, 3.452798428579), P(12.62988, 1.498228), P(17.36814, 0), P(21.7698, 0), P(30.5733, 0)),
      lower: corner(P(30.5733, 0), P(21.7698, 0), P(17.36814, 0), P(12.62988, 1.498228), P(7.45648, 3.3812), P(3.3812, 7.495317284242), P(1.419892543171, 12.598675328518), P(0.481850397518, 14.953513771483), P(0, 17.465204710537), P(0, 20)) },
    { extent: 48,
      upper: corner(P(0, 24), P(0, 19.093682211209), P(0.299560895653, 15.866994417456), P(1.449527740065, 12.610480411693), P(3.425711926322, 7.480624696595), P(7.45648, 3.425711926322), P(12.62988, 1.498228), P(17.36814, 0), P(21.7698, 0), P(30.5733, 0)),
      lower: corner(P(30.5733, 0), P(21.7698, 0), P(17.36814, 0), P(12.62988, 1.498228), P(7.45648, 3.3812), P(3.3812, 7.480624696595), P(1.449527740065, 12.610480411693), P(0.299560895653, 15.866994417456), P(0, 19.093682211209), P(0, 24)) },
    { extent: 60,
      upper: corner(P(0, 30), P(0, 21.536398462216), P(0.026126642855, 17.237215386416), P(1.493980535405, 12.628188036454), P(3.385082172936, 7.458585815124), P(7.45648, 3.385082172936), P(12.62988, 1.498228), P(17.36814, 0), P(21.7698, 0), P(30.5733, 0)),
      lower: corner(P(30.5733, 0), P(21.7698, 0), P(17.36814, 0), P(12.62988, 1.498228), P(7.45648, 3.3812), P(3.3812, 7.458585815124), P(1.493980535405, 12.628188036454), P(0.026126642855, 17.237215386416), P(0, 21.536398462216), P(0, 30)) },
    { extent: 61.1466,
      upper: corner(P(0, 30.5733), P(0, 21.7698), P(0, 17.36814), P(1.498228, 12.62988), P(3.3812, 7.45648), P(7.45648, 3.3812), P(12.62988, 1.498228), P(17.36814, 0), P(21.7698, 0), P(30.5733, 0)),
      lower: corner(P(30.5733, 0), P(21.7698, 0), P(17.36814, 0), P(12.62988, 1.498228), P(7.45648, 3.3812), P(3.3812, 7.45648), P(1.498228, 12.62988), P(0, 17.36814), P(0, 21.7698), P(0, 30.5733)) },
  ];

  const profile = (extent) => {
    const first = samples[0];
    const last = samples[samples.length - 1];
    if (extent <= first.extent) return first;
    if (extent >= last.extent) return last;
    for (let i = 0; i < samples.length - 1; i += 1) {
      const lo = samples[i];
      const hi = samples[i + 1];
      if (extent >= lo.extent && extent <= hi.extent) {
        const t = (extent - lo.extent) / (hi.extent - lo.extent);
        return { upper: mix(lo.upper, hi.upper, t), lower: mix(lo.lower, hi.lower, t) };
      }
    }
    return last;
  };

  // Each axis corrected on its own: the first half of a corner follows the
  // vertical profile, the second the horizontal one.
  const corners = (w, h) => {
    const radius = Math.max(0, Math.min(WIDE, w / 2, h / 2));
    const s = radius / WIDE;
    const v = profile(h / s);
    const hz = profile(w / s);
    const vu = scaleCorner(v.upper, s);
    const vl = scaleCorner(v.lower, s);
    const hu = scaleCorner(hz.upper, s);
    const hl = scaleCorner(hz.lower, s);
    return {
      radius,
      upper: corner(vu.start, vu.c1, vu.c2, vu.p1, vu.c3, P(hu.c3.y, vu.c3.x), swap(hu.p1), swap(hu.c2), swap(hu.c1), swap(hu.start)),
      lower: corner(swap(hl.end), swap(hl.c6), swap(hl.c5), swap(hl.p2), swap(hl.c4), vl.c4, vl.p2, vl.c5, vl.c6, vl.end),
    };
  };

  const bubblePath = (w, h) => {
    const { radius, upper, lower } = corners(w, h);
    const s = radius / WIDE;
    const f = (n) => n.toFixed(3);
    const up = (p, mirrored) => P(mirrored ? w - p.x : p.x, p.y);
    const low = (p) => P(p.x, h - p.y);
    const tail = (xFromRight, yFromBottom) => P(w - xFromRight * s, h + yFromBottom * s);
    const d = [];
    const move = (p) => d.push(`M ${f(p.x)} ${f(p.y)}`);
    const curve = (c1, c2, to) => d.push(`C ${f(c1.x)} ${f(c1.y)} ${f(c2.x)} ${f(c2.y)} ${f(to.x)} ${f(to.y)}`);

    move(up(upper.start));
    curve(up(upper.c1), up(upper.c2), up(upper.p1));
    curve(up(upper.c3), up(upper.c4), up(upper.p2));
    curve(up(upper.c5), up(upper.c6), up(upper.end));
    const topRightStart = up(lower.start, true);
    curve(up(upper.end), topRightStart, topRightStart);
    curve(up(lower.c1, true), up(lower.c2, true), up(lower.p1, true));
    curve(up(lower.c3, true), up(lower.c4, true), up(lower.p2, true));
    curve(up(lower.c5, true), up(lower.c6, true), up(lower.end, true));
    // The tail flow replaces the bottom-trailing corner.
    const tailSideStart = up(lower.end, true);
    const tailFlowStart = P(tailSideStart.x, Math.max(tailSideStart.y, low(lower.end).y));
    curve(tailSideStart, tailFlowStart, tailFlowStart);
    // BubbleKit's roundTailed(right, 1) contour at r=20, scaled by the radius.
    curve(tail(0, -15.6938174), tail(1.4149, -11.5018174), tail(4.0279, -8.0758174));
    curve(tail(5.0867, -6.687757), tail(6.3092, -5.4643142), tail(7.66, -4.4234174));
    curve(tail(9.585, -2.9224174), tail(10.418, -1.3564174), tail(10.418, 0.4035826));
    curve(tail(10.418, 1.5865826), tail(10.209, 2.7555826), tail(8.51, 4.9875826));
    curve(tail(7.695, 6.0575826), tail(8.513, 7.1495826), tail(9.787, 6.6655826));
    curve(tail(12.407, 5.6705826), tail(15.391, 3.8595826), tail(18.005, 1.9265826));
    const rejoin = tail(22.07, 0.0125826);
    curve(tail(20.347, 0.1945826), tail(20.971, 0.0195826), rejoin);
    const bottomLeftStart = low(lower.start);
    curve(rejoin, bottomLeftStart, bottomLeftStart);
    curve(low(lower.c1), low(lower.c2), low(lower.p1));
    curve(low(lower.c3), low(lower.c4), low(lower.p2));
    curve(low(lower.c5), low(lower.c6), low(lower.end));
    d.push("Z");
    return d.join(" ");
  };

  const tapBubble = (text) => {
    // Preserve portable newlines as distinct rows. Single-line button replies
    // keep their existing 40pt geometry, 17pt text, and 14pt side insets.
    const lines = text.split("\n");
    const h = 40 + (lines.length - 1) * 24;
    const w = Math.max(2 * 20, Math.round(Math.max(...lines.map(line => line.length)) * 8.6 + 28));
    const radius = Math.min(WIDE, w / 2, h / 2);
    const total = Math.ceil(h + radius * TAIL_DEPTH_FACTOR);
    return (
      <svg className="buttons-preview-tap" width={w} height={total} viewBox={`0 0 ${w} ${total}`} aria-hidden="true">
        <path d={bubblePath(w, h)} />
        {lines.map((line, index) => (
          <text key={index} x={lines.length === 1 ? w / 2 : 14} y={20 + index * 24}
            dominantBaseline="central" textAnchor={lines.length === 1 ? "middle" : "start"}>{line}</text>
        ))}
      </svg>
    );
  };

  // RelaySelectionRowLayout: 14pt side insets, 10pt vertical, 8pt before the
  // chevron, 2pt under the title, 3pt between chosen labels, and a bare
  // checkmark the width of the gap it replaces.
  const CARD_INSET = 14;
  const CARD_VERTICAL = 10;
  const CARD_TITLE_GAP = 2;
  const CARD_LINE_GAP = 3;
  const CARD_MARK_WIDTH = 17;
  const CHEVRON = { width: 8, height: 13 };
  const ROW_METRICS = { title: 20, subtitle: 18, label: 20 };

  const cardBubble = (rows, side, showsChevron, w) => {
    let cursor = 0;
    const placed = rows.map((row, index) => {
      if (index > 0) cursor += rows[index - 1].kind === "title" ? CARD_TITLE_GAP : CARD_LINE_GAP;
      const line = ROW_METRICS[row.kind];
      const top = cursor;
      cursor += line;
      return { ...row, line, top };
    });
    const interior = Math.max(cursor, showsChevron ? CHEVRON.height : 0);
    const h = Math.ceil(interior + CARD_VERTICAL * 2);
    const radius = Math.min(WIDE, w / 2, h / 2);
    const total = Math.ceil(h + radius * TAIL_DEPTH_FACTOR);
    const stackTop = Math.round(CARD_VERTICAL + (interior - cursor) / 2);
    const f = (n) => Number(n.toFixed(2));
    const chevronX = w - CARD_INSET - CHEVRON.width;
    const chevronY = h / 2;
    return (
      <svg className={`selection-card selection-card-${side}`} width={w} height={total}
        viewBox={`0 0 ${w} ${total}`} aria-hidden="true" focusable="false">
        <g transform={side === "leading" ? `translate(${w},0) scale(-1,1)` : undefined}>
          <path className="selection-card-shape" d={bubblePath(w, h)} />
        </g>
        {placed.map((row, index) => {
          const middle = f(stackTop + row.top + row.line / 2);
          return (
            <g key={index}>
              {row.kind === "label" ? (
                <path className="selection-card-mark"
                  d={`M ${CARD_INSET} ${f(stackTop + row.top + row.line / 2 + 0.6)} l 3.6 3.7 l 6.9 -8.5`} />
              ) : null}
              <text className={`selection-card-${row.kind}`} dominantBaseline="central"
                x={row.kind === "label" ? CARD_INSET + CARD_MARK_WIDTH : CARD_INSET}
                y={middle}>{row.text}</text>
            </g>
          );
        })}
        {showsChevron ? (
          <path className="selection-card-chevron"
            d={`M ${chevronX} ${f(chevronY - 5.6)} L ${chevronX + 6.2} ${f(chevronY)} L ${chevronX} ${f(chevronY + 5.6)}`} />
        ) : null}
      </svg>
    );
  };

  return rows ? cardBubble(rows, side, chevron, width) : tapBubble(text);
};

// Mintlify isolates snippet exports. The page passes the shared bubble renderer
// explicitly so previews reuse geometry without relying on nested imports.
// A URL item mirrors Relay-iOS ChatView.relayButtonsActions: the pill opens
// MessagesInAppBrowser (SFSafariViewController, close-style dismiss button)
// as a full-screen cover over the chat, and the button group stays put. The
// cover here is drawn locally and loads nothing.
export const ButtonsPreview = ({ text, items, tapped, label, bubble }) => {
  const [reply, setReply] = useState(null);
  const [openedURL, setOpenedURL] = useState(null);
  const hostOf = (url) => {
    try { return new URL(url).host; } catch (error) { return url; }
  };
  const closeBrowser = (event) => {
    const root = event && event.currentTarget && event.currentTarget.closest(".buttons-preview");
    setOpenedURL(null);
    const opener = root && root.querySelector(".buttons-preview-action.is-link");
    if (opener) opener.focus();
  };
  return (
    <div className={"buttons-preview" + (openedURL ? " is-browser-open" : "")}
      role={tapped ? "img" : "group"} aria-label={text ? `${text} ${label}` : label}>
      <div className="buttons-preview-frame">
      <div className="buttons-preview-stage">
        {tapped ? (
          bubble({ text: tapped })
        ) : (
          <div className="buttons-preview-message">
            {/* The agent's balloon is the last in its run once a plain tap
                hides the buttons, so it takes the incoming tail then: the
                same BubbleKit roundTailed contour as MessageBubble's tap
                bubble, mirrored to the leading edge. With buttons below it,
                the balloon stays tailless. */}
            {text ? (
              <div className={"buttons-preview-text" + (reply !== null ? " has-tail" : "")}>
                {text}
                {reply !== null ? (
                  <svg className="buttons-preview-text-tail" width="23" height="24" viewBox="0 0 23 24" aria-hidden="true" focusable="false">
                    <path d="M 0 0 C 0 0.306 1.415 4.498 4.028 7.924 C 5.087 9.312 6.309 10.536 7.660 11.577 C 9.585 13.078 10.418 14.644 10.418 16.404 C 10.418 17.587 10.209 18.756 8.510 20.988 C 7.695 22.058 8.513 23.150 9.787 22.666 C 12.407 21.671 15.391 19.860 18.005 17.927 C 20.347 16.195 20.971 16.020 22.070 16.013 L 22.070 0 Z" />
                  </svg>
                ) : null}
              </div>
            ) : null}
            {reply !== null ? (
              <div className="buttons-reply" role="status" aria-label={`Reply: ${reply}`}>
                {bubble({ text: reply })}
              </div>
            ) : (
              <div className="buttons-preview-stack">
                {items.map((item, index) => (
                  <button type="button" key={index} tabIndex={openedURL ? -1 : 0}
                    className={"buttons-preview-pill buttons-preview-action" + (item.url ? " is-link" : "")}
                    onClick={() => {
                      if (item.url) {
                        // Documentation fixtures never navigate to example hosts.
                        setOpenedURL(item.url);
                      } else {
                        setOpenedURL(null);
                        setReply(item.label);
                      }
                    }}>
                    <span>{item.label}</span>
                    {item.url ? <span className="buttons-preview-arrow" aria-hidden="true">↗</span> : null}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
      {openedURL ? (
        <div className="buttons-url-preview" role="dialog" aria-modal="true" aria-label="URL action preview"
          onKeyDown={(event) => { if (event.key === "Escape") closeBrowser(event); }}>
          <div className="buttons-browser-bar">
            <button type="button" className="buttons-url-close" autoFocus aria-label="Close" onClick={closeBrowser}>
              <svg viewBox="0 0 16 16" aria-hidden="true" focusable="false"><path d="M4 4l8 8M12 4l-8 8" /></svg>
            </button>
            <div className="buttons-browser-address">
              <svg viewBox="0 0 12 14" aria-hidden="true" focusable="false">
                <rect x="1.5" y="6" width="9" height="7" rx="1.5" />
                <path d="M3.5 6V4.5a2.5 2.5 0 0 1 5 0V6" />
              </svg>
              <span>{hostOf(openedURL)}</span>
            </div>
            <svg className="buttons-browser-reload" viewBox="0 0 16 16" aria-hidden="true" focusable="false">
              <path d="M13 8a5 5 0 1 1-1.46-3.54M13 3v3h-3" />
            </svg>
          </div>
          <div className="buttons-browser-page" role="status">
            <span className="buttons-url-caption">In-app browser preview</span>
            <span className="buttons-url-address">{openedURL}</span>
            <span className="buttons-browser-note">The app opens this page here. The demo loads nothing.</span>
          </div>
          <div className="buttons-browser-toolbar" aria-hidden="true">
            <svg viewBox="0 0 20 20"><path d="M12.5 4l-6 6 6 6" /></svg>
            <svg viewBox="0 0 20 20" className="is-disabled"><path d="M7.5 4l6 6-6 6" /></svg>
            <svg viewBox="0 0 20 20"><path d="M10 12.5V2.5M6.5 6L10 2.5 13.5 6M6 9H4.5v8.5h11V9H14" /></svg>
            <svg viewBox="0 0 20 20"><circle cx="10" cy="10" r="7.5" /><path d="M12.8 7.2l-1.6 4-4 1.6 1.6-4z" /></svg>
          </div>
        </div>
      ) : null}
      </div>
      {reply !== null ? (
        <div className="buttons-preview-controls">
          <button type="button" className="buttons-reset" onClick={() => { setReply(null); setOpenedURL(null); }}>Reset demo</button>
        </div>
      ) : null}
    </div>
  );
};


// Local-only interaction. No API, analytics, or credentials. Mirrors the app
// (Relay-iOS, Views/Transcript/RelaySelectionRow.swift and
// RelaySelectionSheet.swift): nothing is picked in the transcript. The prompt
// balloon opens a sheet carrying the whole option list, Send posts once, and
// the answered prompt or its reply reopens the same sheet read-only.
export const SelectionPreview = ({ text, options, received, bubble }) => {
  const title = text || "Multi-select";
  // The received fixture is the canonical wire text; its labels name the
  // chosen options, so the same sheet can reopen over a static reply.
  const receivedValues = received
    ? options
        .filter((option) => received.split("\n").includes("\u2022 " + option.label))
        .map((option) => option.value)
    : null;
  const [draft, setDraft] = useState([]);
  const [answered, setAnswered] = useState(receivedValues);
  const [opener, setOpener] = useState(null);
  const isStatic = received !== undefined && received !== null;
  const isAnswered = answered !== null;
  const isReadOnly = isAnswered;
  const open = opener !== null;
  const chosen = options.filter((option) => (answered || []).includes(option.value));
  const labels = chosen.map((option) => option.label);

  const focusWithin = (event, selector) => {
    const root = event && event.currentTarget && event.currentTarget.closest(".selection-preview");
    const target = root && root.querySelector(selector);
    if (target) target.focus();
  };
  const openSheet = (from) => {
    setDraft(answered || []);
    setOpener(from);
  };
  const close = (event) => {
    const from = opener;
    setOpener(null);
    focusWithin(event, "." + (from || "selection-prompt"));
  };
  const send = (event) => {
    setAnswered(draft);
    setOpener(null);
    focusWithin(event, ".selection-prompt");
  };
  const reset = () => {
    setAnswered(receivedValues);
    setDraft([]);
    setOpener(null);
  };

  const promptRows = [
    { kind: "title", text: title },
    { kind: "subtitle", text: "Pick options" },
  ];
  const answerRows = [
    { kind: "title", text: title },
    ...labels.map((label) => ({ kind: "label", text: label })),
  ];

  return (
    <div className={"buttons-preview selection-preview" + (open ? " is-sheet-open" : "")}
      role="group" aria-label={isStatic ? "Selection reply preview" : "Interactive selection preview"}>
      <div className="buttons-preview-frame">
      <div className="buttons-preview-stage">
        <div className="buttons-preview-message">
          {isStatic ? null : (
            <button type="button" className="selection-prompt" tabIndex={open ? -1 : 0}
              aria-haspopup="dialog" aria-expanded={opener === "selection-prompt"}
              aria-label={isAnswered ? `${title}. Opens the options you chose` : `${title}. Opens the options`}
              onClick={() => openSheet("selection-prompt")}>
              {bubble({ rows: promptRows, side: "leading", chevron: true })}
            </button>
          )}
          {isAnswered ? (
            <button type="button" className="selection-answer" tabIndex={open ? -1 : 0}
              aria-haspopup="dialog" aria-expanded={opener === "selection-answer"}
              aria-label={`${title}. ${labels.join(", ")}. Opens the options you chose`}
              onClick={() => openSheet("selection-answer")}>
              {bubble({ rows: answerRows, side: "trailing", chevron: true })}
            </button>
          ) : null}
        </div>
      </div>
      {open ? (
        <div className="selection-sheet-layer">
          <div className="selection-sheet-scrim" onClick={close} />
          <div className={"selection-sheet" + (isReadOnly ? " is-read-only" : "")}
            role="dialog" aria-modal="true" aria-label={title}
            onKeyDown={(event) => { if (event.key === "Escape") close(event); }}>
            <button type="button" className="selection-sheet-grabber" autoFocus
              aria-label="Close options" onClick={close} />
            {/* The title alone (owner, 2026-09-22): no "Options" heading.
                Rows fade under it and under the floating Send, the edge
                blur Relay-iOS RelaySelectionSheet.swift gets from its top
                and bottom safeAreaBars. */}
            <div className="selection-sheet-title">{title}</div>
            <div className="selection-sheet-list">
              {options.map((option) => {
                const checked = (isReadOnly ? answered : draft).includes(option.value);
                return (
                  <button type="button" key={option.value} role="checkbox" aria-checked={checked}
                    className="selection-sheet-option" disabled={isReadOnly}
                    onClick={() => setDraft((current) => current.includes(option.value)
                      ? current.filter((value) => value !== option.value)
                      : [...current, option.value])}>
                    <svg className="selection-box" viewBox="0 0 22 22" aria-hidden="true" focusable="false">
                      <circle cx="11" cy="11" r="10" />
                      <path d="m6.4 11.2 3 3 6.2-6.8" />
                    </svg>
                    <span className="selection-sheet-label">{option.label}</span>
                  </button>
                );
              })}
            </div>
            {isReadOnly ? null : (
              <div className="selection-sheet-footer">
                <button type="button" className="selection-send" disabled={draft.length === 0}
                  onClick={send}>Send</button>
              </div>
            )}
          </div>
        </div>
      ) : null}
      </div>
      {isAnswered && !isStatic ? (
        <div className="buttons-preview-controls">
          <button type="button" className="selection-reset" tabIndex={open ? -1 : 0}
            onClick={reset}>Reset demo</button>
        </div>
      ) : null}
    </div>
  );
};
