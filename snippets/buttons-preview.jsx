// Adapted from buttons-docs-fix dc55e9e; bubble geometry shared by component previews.
// A rendered buttons part, drawn the way the app draws it: a vertical stack of
// equally sized pills capped at 75% of the maximum text-balloon column, a URL
// button marked with an arrow, and the tap as
// the person's own bubble. The bubble is the app's own silhouette: a port of
// RelayBubbleGeometry.trailingRoundTailedPath (Relay-iOS,
// Views/MessageBubbleShape.swift), the iOS 26.5 BubbleKit round-tailed bubble
// at radius 20, with the app's 17pt body text and 14pt side insets.
export const MessageBubble = ({ text }) => {
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
    // The app's one-line body, measured on the simulator: 40pt tall, 17pt
    // text, 14pt side insets. The text width is estimated; the page cannot
    // measure it.
    const h = 40;
    const w = Math.max(2 * 20, Math.round(text.length * 8.6 + 28));
    const radius = Math.min(WIDE, w / 2, h / 2);
    const total = Math.ceil(h + radius * TAIL_DEPTH_FACTOR);
    return (
      <svg className="buttons-preview-tap" width={w} height={total} viewBox={`0 0 ${w} ${total}`} aria-hidden="true">
        <path d={bubblePath(w, h)} />
        <text x={w / 2} y={h / 2} dominantBaseline="central" textAnchor="middle">{text}</text>
      </svg>
    );
  };

  return tapBubble(text);
};

// Mintlify isolates snippet exports. The page passes the shared bubble renderer
// explicitly so previews reuse geometry without relying on nested imports.
export const ButtonsPreview = ({ text, items, tapped, label, bubble }) => {
  return (
    <div className="buttons-preview" role="img" aria-label={text ? `${text} ${label}` : label}>
      <div className="buttons-preview-stage">
        {tapped ? (
          bubble({ text: tapped })
        ) : (
          <div className="buttons-preview-message">
            {text ? <div className="buttons-preview-text">{text}</div> : null}
            <div className="buttons-preview-stack">
              {items.map((item) => (
                <div key={item.label} className={"buttons-preview-pill" + (item.url ? " is-link" : "")}>
                  <span>{item.label}</span>
                  {item.url ? <span className="buttons-preview-arrow" aria-hidden="true">↗</span> : null}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};


// Local-only interaction. No API, analytics, or credentials. Uses the same
// column/pills/bubble primitives as ButtonsPreview and native selection colors.
export const SelectionPreview = ({ text, options, received, bubble }) => {
  const [selected, setSelected] = useState([]);
  const [sent, setSent] = useState(false);
  const ordered = options.filter((option) => selected.includes(option.value));
  const reply = received || ordered.map((option) => option.label).join(", ");
  return (
    <div className="buttons-preview selection-preview" role="group" aria-label={received ? "Selection reply preview" : "Interactive selection preview"}>
      <div className="buttons-preview-stage">
        {received ? bubble({ text: received }) : (
          <div className="buttons-preview-message">
            <div className="buttons-preview-text">{text}</div>
            {sent ? (
              <div className="selection-reply" role="status">{bubble({ text: reply })}</div>
            ) : (
              <div className="buttons-preview-stack selection-stack">
                {options.map((option) => (
                  <button type="button" key={option.value} className="buttons-preview-pill selection-option"
                    aria-pressed={selected.includes(option.value)} onClick={() => setSelected((current) => current.includes(option.value) ? current.filter((value) => value !== option.value) : [...current, option.value])}>
                    <svg viewBox="0 0 20 20" className="selection-check" aria-hidden="true">
                      <circle cx="10" cy="10" r="8.5" />
                      <path d="m6 10 2.5 2.5 5.5-6" />
                    </svg>
                    <span>{option.label}</span>
                  </button>
                ))}
                <div className="selection-actions">
                  <button type="button" disabled={!selected.length} onClick={() => setSelected([])}>Clear</button>
                  <button type="button" disabled={!selected.length} onClick={() => setSent(true)}>Send</button>
                </div>
              </div>
            )}
            {sent ? <button type="button" className="selection-reset" onClick={() => { setSent(false); setSelected([]); }}>Reset demo</button> : null}
          </div>
        )}
      </div>
    </div>
  );
};
