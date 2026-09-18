// A rendered buttons part, drawn the way the app draws it: a vertical stack of
// pills under the message, a link button marked with an arrow, and the tap as
// the person's own bubble. The bubble outline, tail included, is the Relay
// bubble from images/hero/background.svg (228 x 75 at a 68-tall body),
// scaled to the bubble's height and stretched to its width.
export const ButtonsPreview = ({ items, tapped, label }) => {
  // Helpers live inside the component: the snippet is compiled as MDX, which
  // keeps only exports in scope and reads a capitalised tag as an MDX component.
  const bubblePath = (w, h) => {
    const s = h / 68;
    const L = (x) => (x * s).toFixed(2);
    const R = (x) => (w - (228 - x) * s).toFixed(2);
    const Y = (y) => (y * s).toFixed(2);
    return [
      `M ${L(0)} ${Y(30.57)}`,
      `C ${L(0)} ${Y(21.77)} ${L(0)} ${Y(17.37)} ${L(1.5)} ${Y(12.63)}`,
      `C ${L(3.38)} ${Y(7.46)} ${L(7.46)} ${Y(3.38)} ${L(12.63)} ${Y(1.5)}`,
      `C ${L(17.37)} ${Y(0)} ${L(21.77)} ${Y(0)} ${L(30.57)} ${Y(0)}`,
      `L ${R(197.43)} ${Y(0)}`,
      `C ${R(206.23)} ${Y(0)} ${R(210.63)} ${Y(0)} ${R(215.37)} ${Y(1.5)}`,
      `C ${R(220.54)} ${Y(3.38)} ${R(224.62)} ${Y(7.46)} ${R(226.5)} ${Y(12.63)}`,
      `C ${R(228)} ${Y(17.37)} ${R(228)} ${Y(21.77)} ${R(228)} ${Y(30.57)}`,
      `C ${R(228)} ${Y(52.31)} ${R(226.59)} ${Y(56.5)} ${R(223.97)} ${Y(59.92)}`,
      `C ${R(222.91)} ${Y(61.31)} ${R(221.69)} ${Y(62.54)} ${R(220.34)} ${Y(63.58)}`,
      `C ${R(218.42)} ${Y(65.08)} ${R(217.58)} ${Y(66.64)} ${R(217.58)} ${Y(68.4)}`,
      `C ${R(217.58)} ${Y(69.59)} ${R(217.79)} ${Y(70.76)} ${R(219.49)} ${Y(72.99)}`,
      `C ${R(220.31)} ${Y(74.06)} ${R(219.49)} ${Y(75.15)} ${R(218.21)} ${Y(74.67)}`,
      `C ${R(215.59)} ${Y(73.67)} ${R(212.61)} ${Y(71.86)} ${R(210)} ${Y(69.93)}`,
      `C ${R(207.65)} ${Y(68.19)} ${R(207.03)} ${Y(68.02)} ${R(205.93)} ${Y(68.01)}`,
      `L ${L(30.57)} ${Y(68)}`,
      `C ${L(21.77)} ${Y(68)} ${L(17.37)} ${Y(68)} ${L(12.63)} ${Y(66.5)}`,
      `C ${L(7.46)} ${Y(64.62)} ${L(3.38)} ${Y(60.54)} ${L(1.5)} ${Y(55.37)}`,
      `C ${L(0)} ${Y(50.63)} ${L(0)} ${Y(46.23)} ${L(0)} ${Y(37.43)}`,
      "Z",
    ].join(" ");
  };

  const tapBubble = (label) => {
    const h = 38;
    const w = Math.max(56, Math.round(label.length * 8.4 + 30));
    const total = Math.ceil((75 / 68) * h);
    return (
      <svg className="buttons-preview-tap" width={w} height={total} viewBox={`0 0 ${w} ${total}`} aria-hidden="true">
        <path d={bubblePath(w, h)} />
        <text x={w / 2 - 3} y={h / 2} dominantBaseline="central" textAnchor="middle">{label}</text>
      </svg>
    );
  };

  return (
    <div className="buttons-preview" role="img" aria-label={label}>
      <div className="buttons-preview-stage">
        {tapped ? (
          tapBubble(tapped)
        ) : (
          <div className="buttons-preview-stack">
            {items.map((item) => (
              <div key={item.label} className={"buttons-preview-pill" + (item.url ? " is-link" : "")}>
                <span>{item.label}</span>
                {item.url ? <span className="buttons-preview-arrow" aria-hidden="true">↗</span> : null}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
