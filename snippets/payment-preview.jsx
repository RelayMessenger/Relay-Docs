// A rendered `payment` part, drawn the way the app draws it (Relay-iOS,
// Views/Transcript/RelayPaymentRow.swift and RelayPaymentReceiptRow.swift):
// a 274pt #2A292C balloon in light and dark mode alike, the item on line one
// in Caption 1 semibold, "<amount> - Pay with <Stripe wordmark>" on line two,
// and a white 44 x 22 capsule on the right that turns into the settled word.
// The balloon is the app's round-tailed silhouette, the same BubbleKit port
// MessageBubble carries in snippets/buttons-preview.jsx. Its path cannot be
// passed in, because MessageBubble draws a fixed-height text or row balloon,
// so the port is repeated inside this component.
//
// Local-only interaction. No API, analytics, or credentials. Tapping the card
// opens what the app opens (ChatView.relayPaymentActions): Stripe's payment
// sheet for physical goods, and the pay page in Safari for digital goods and
// donations. Both are drawn locally and load nothing.
export const PaymentPreview = ({ part, label, controls = true, receipt = false, storefront: initialStorefront = "USA" }) => {
  // Everything lives inside the component: the snippet is compiled as MDX,
  // which keeps only exports in scope.
  const WIDE = 20;
  const TAIL_DEPTH_FACTOR = 0.33925;
  // RelayPaymentRowLayout: 274 wide, the caption at least 48.5 tall, the
  // picture 170 tall, 14 in on the leading side and 12.5 on the trailing,
  // 12 between the text and the capsule.
  const CARD_WIDTH = 274;
  const MIN_CAPTION = 48.5;
  const PICTURE_HEIGHT = 170;
  const LEADING = 14;
  // The agent's card sits at the transcript's leading edge and the payer's
  // receipt at its trailing edge, across the frame's full width.

  const [status, setStatus] = useState(part.status || "requested");
  const [storefront, setStorefront] = useState(initialStorefront);
  const [cover, setCover] = useState(null);
  const [captionHeight, setCaptionHeight] = useState(49);
  const [receiptSize, setReceiptSize] = useState(null);
  const captionRef = useRef(null);
  const receiptRef = useRef(null);

  useEffect(() => {
    // The app measures the title (up to two lines) before it draws the
    // balloon; the preview reads the laid-out caption instead.
    const measure = () => {
      if (captionRef.current) {
        setCaptionHeight(Math.max(MIN_CAPTION, Math.ceil(captionRef.current.offsetHeight)));
      }
      if (receiptRef.current) {
        setReceiptSize({ w: Math.ceil(receiptRef.current.offsetWidth), h: receiptRef.current.offsetHeight });
      }
    };
    measure();
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(measure);
  }, [status, storefront, part.description, receipt]);

  // PaymentAmountFormatter.cardAmount: minor units over the currency's own
  // decimal places, with "/mo" for a subscription. The docs format in US
  // English; the app uses the person's locale.
  const money = () => {
    const formatter = new Intl.NumberFormat("en-US", { style: "currency", currency: part.currency.toUpperCase() });
    return formatter.format(part.amount / Math.pow(10, formatter.resolvedOptions().maximumFractionDigits));
  };
  const cadence = () => {
    const r = part.recurring;
    if (!r) return "";
    const short = { day: "day", week: "wk", month: "mo", year: "yr" }[r.interval];
    return r.interval_count > 1 ? `/${r.interval_count} ${short}` : `/${short}`;
  };
  const isSubscription = part.mode === "subscription";
  const amount = money() + cadence();
  const payableHere = part.category === "physical_goods"
    || part.category === "donation"
    || (part.category === "digital_goods" && storefront === "USA");
  const tappable = status === "requested" && payableHere;
  const buttonTitle = part.category === "donation" ? "Donate" : isSubscription ? "Subscribe" : "Pay";
  const accessory = status === "requested"
    ? (payableHere ? { kind: "button", text: buttonTitle } : { kind: "unavailable", text: "Unavailable" })
    : status === "succeeded"
      ? { kind: "word", text: isSubscription ? "Subscribed" : "Paid", paid: true }
      : { kind: "word", text: status === "expired" ? "Expired" : "Canceled", paid: false };
  const dimmed = status === "expired" || status === "canceled";
  const lead = isSubscription ? `${amount} ·` : `${amount} - Pay with`;
  const receiptLead = (() => {
    if (!isSubscription || !part.recurring) return `Paid ${money()} with`;
    const r = part.recurring;
    return `Subscribed ${money()} ${r.interval_count > 1 ? `every ${r.interval_count} ${r.interval}s` : `a ${r.interval}`} with`;
  })();
  const spoken = `${part.description}. ${money()}. Pay with Stripe.${accessory.kind === "button" ? "" : ` ${accessory.text}.`}`;

  // The BubbleKit round-tailed path, as snippets/buttons-preview.jsx ports it
  // from Relay-iOS RelayBubbleGeometry. `mirrored` puts the tail on the
  // leading side, where the agent's balloons sit.
  const P = (x, y) => ({ x, y });
  const corner = (start, c1, c2, p1, c3, c4, p2, c5, c6, end) => ({ start, c1, c2, p1, c3, c4, p2, c5, c6, end });
  const KEYS = ["start", "c1", "c2", "p1", "c3", "c4", "p2", "c5", "c6", "end"];
  const lerp = (a, b, t) => P(a.x + (b.x - a.x) * t, a.y + (b.y - a.y) * t);
  const mix = (a, b, t) => Object.fromEntries(KEYS.map((k) => [k, lerp(a[k], b[k], t)]));
  const scaleCorner = (c, s) => Object.fromEntries(KEYS.map((k) => [k, P(c[k].x * s, c[k].y * s)]));
  const swap = (p) => P(p.y, p.x);
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
  const bubblePath = (w, h, mirrored) => {
    const { radius, upper, lower } = corners(w, h);
    const s = radius / WIDE;
    const f = (n) => n.toFixed(3);
    const out = (p) => (mirrored ? P(w - p.x, p.y) : p);
    const up = (p, flip) => P(flip ? w - p.x : p.x, p.y);
    const low = (p) => P(p.x, h - p.y);
    const tail = (xFromRight, yFromBottom) => P(w - xFromRight * s, h + yFromBottom * s);
    const d = [];
    const move = (p) => { const q = out(p); d.push(`M ${f(q.x)} ${f(q.y)}`); };
    const curve = (c1, c2, to) => {
      const [a, b, c] = [out(c1), out(c2), out(to)];
      d.push(`C ${f(a.x)} ${f(a.y)} ${f(b.x)} ${f(b.y)} ${f(c.x)} ${f(c.y)}`);
    };
    move(up(upper.start));
    curve(up(upper.c1), up(upper.c2), up(upper.p1));
    curve(up(upper.c3), up(upper.c4), up(upper.p2));
    curve(up(upper.c5), up(upper.c6), up(upper.end));
    const topRightStart = up(lower.start, true);
    curve(up(upper.end), topRightStart, topRightStart);
    curve(up(lower.c1, true), up(lower.c2, true), up(lower.p1, true));
    curve(up(lower.c3, true), up(lower.c4, true), up(lower.p2, true));
    curve(up(lower.c5, true), up(lower.c6, true), up(lower.end, true));
    const tailSideStart = up(lower.end, true);
    const tailFlowStart = P(tailSideStart.x, Math.max(tailSideStart.y, low(lower.end).y));
    curve(tailSideStart, tailFlowStart, tailFlowStart);
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
  const tailDepth = (w, h) => Math.min(WIDE, w / 2, h / 2) * TAIL_DEPTH_FACTOR;

  // Stripe's wordmark, the app's StripeWordmark asset (60 x 25), tinted the
  // line's own grey; its x-height matches the text's, its letters stand on
  // the baseline (RelayPaymentRowLayout.wordmarkSize / wordmarkAttachment).
  const wordmark = (
    <svg className="pay-wordmark" viewBox="0 0 60 25" role="img" aria-label="Stripe" focusable="false">
      <path fillRule="evenodd" d="M59.6444 14.2813h-8.062c.1843 1.9296 1.5983 2.5476 3.2032 2.5476 1.6352 0 2.9534-.3656 4.0453-.9506v3.3179c-1.1186.7115-2.5964 1.1068-4.5645 1.1068-4.011 0-6.8218-2.5122-6.8218-7.4783 0-4.19441 2.3837-7.52509 6.3017-7.52509 3.912 0 5.9537 3.28038 5.9537 7.49819 0 .3982-.0372 1.261-.0556 1.4835Zm-5.9241-5.62407c-1.0294 0-2.1739.72812-2.1739 2.58387h4.2573c0-1.85362-1.0721-2.58387-2.0834-2.58387ZM40.9547 20.303c-1.4411 0-2.322-.6087-2.9133-1.0417l-.0088 4.6271-4.1181.8755-.0014-19.19053h3.7543l.0864 1.01784c.6035-.52914 1.6114-1.29157 3.2256-1.29162 2.8925 0 5.6162 2.6052 5.6162 7.39971 0 5.2327-2.6948 7.6037-5.6409 7.6037Zm-.959-11.35573c-.9453 0-1.5376.34559-1.9669.81586l.0245 6.11967c.3997.433.9763.7813 1.9424.7813 1.5231 0 2.5437-1.6575 2.5437-3.8745 0-2.1544-1.037-3.84233-2.5437-3.84233Zm-11.7602-3.3739h4.1341V20.0088h-4.1341V5.57337Zm0-4.694699L32.3696 0v3.35821l-4.1341.87868V.878671ZM23.9198 10.2223v9.7861h-4.1156V5.57296h3.6867l.1317 1.21751c1.0035-1.7722 3.0722-1.41321 3.6209-1.21594v3.78524c-.5242-.16908-2.2894-.42779-3.3237.86253Zm-8.5525 4.7221c0 2.4275 2.5988 1.6719 3.1263 1.4609v3.3522c-.5492.3013-1.5437.5458-2.8901.5458-2.4441 0-4.2773-1.7999-4.2773-4.2379l.0173-13.17658 4.0206-.85464.0032 3.5395h3.1278V9.0857h-3.1278v5.8588-.0001Zm-4.9069.7026c0 2.9645-2.31051 4.6562-5.73464 4.6562-1.41958 0-2.92289-.2761-4.453935-.9347v-3.9319c1.382085.7516 3.093705 1.315 4.457755 1.315.91864 0 1.53106-.2459 1.53106-1.0069C6.26064 13.7786 0 14.5192 0 9.95995 0 7.04457 2.27622 5.2998 5.61655 5.2998c1.36404 0 2.72806.20934 4.09208.75351V9.9317c-1.25265-.67618-2.84332-1.05979-4.09588-1.05979-.86296 0-1.44753.24965-1.44753.8924.0001 1.85329 6.29518.97249 6.29518 5.88279v-.0001Z" />
    </svg>
  );

  const pictureHeight = part.image_url ? PICTURE_HEIGHT : 0;
  const bodyHeight = pictureHeight + captionHeight;
  const cardTotal = Math.ceil(bodyHeight + tailDepth(CARD_WIDTH, bodyHeight));
  const cardPath = bubblePath(CARD_WIDTH, bodyHeight, true);

  const openCard = () => {
    if (!tappable) return;
    setCover(part.category === "physical_goods" ? "sheet" : "safari");
  };
  const closeCover = (event) => {
    const root = event && event.currentTarget && event.currentTarget.closest(".pay-preview");
    setCover(null);
    const card = root && root.querySelector(".pay-card");
    if (card) card.focus();
  };
  const payInSheet = () => {
    // Stripe tells Relay, the card changes in place, and the payer's receipt
    // lands at the bottom of the chat.
    setCover(null);
    setStatus("succeeded");
  };

  const cardInner = (
    <>
      <svg className="pay-card-shape" width={CARD_WIDTH} height={cardTotal}
        viewBox={`0 0 ${CARD_WIDTH} ${cardTotal}`} aria-hidden="true" focusable="false">
        <path d={cardPath} />
      </svg>
      {part.image_url ? (
        // The app loads image_url here; the docs draw a stand-in and load nothing.
        <div className={"pay-picture" + (dimmed ? " is-dimmed" : "")} style={{ clipPath: `path('${cardPath}')` }} aria-hidden="true">
          <svg viewBox="0 0 274 170" preserveAspectRatio="xMidYMid slice" focusable="false">
            <defs>
              <linearGradient id="pay-picture-wall" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0" stopColor="#b9b9b6" />
                <stop offset="1" stopColor="#7d7d7a" />
              </linearGradient>
            </defs>
            <rect width="274" height="170" fill="url(#pay-picture-wall)" />
            <path d="M118 44h36l4 14v86c0 4-3 6-6 6h-32c-3 0-6-2-6-6V58z" fill="#f4f4f2" />
            <path d="M154 44l4 14v86c0 4-3 6-6 6h-6c3 0 5-2 5-6V58l-3-14z" fill="#d9d9d6" />
            <rect x="121" y="104" width="30" height="16" rx="1" fill="#e9a23b" />
          </svg>
        </div>
      ) : null}
      <div ref={captionRef} className={"pay-caption" + (dimmed ? " is-dimmed" : "")} style={{ top: pictureHeight }}>
        <div className="pay-text">
          <div className="pay-title">{part.description}</div>
          <div className="pay-subtitle">{lead} {wordmark}</div>
        </div>
        {accessory.kind === "word" ? (
          <div className="pay-word">
            {accessory.paid ? (
              <svg className="pay-check" viewBox="0 0 12 12" aria-hidden="true" focusable="false">
                <circle cx="6" cy="6" r="5.3" />
                <path d="M3.6 6.2l1.7 1.8 3.1-3.9" />
              </svg>
            ) : null}
            <span>{accessory.text}</span>
          </div>
        ) : (
          <div className={"pay-pill" + (accessory.kind === "unavailable" ? " is-unavailable" : "")}>{accessory.text}</div>
        )}
      </div>
    </>
  );

  const showsReceipt = receipt || (controls && status === "succeeded");
  const receiptW = receiptSize ? receiptSize.w : 190;
  const receiptH = receiptSize ? receiptSize.h : 49;
  const receiptTotal = Math.ceil(receiptH + tailDepth(receiptW, receiptH));

  const statuses = [
    { value: "requested", event: null },
    { value: "succeeded", event: "payment.succeeded" },
    { value: "canceled", event: "payment.canceled" },
    { value: "expired", event: "payment.expired" },
  ];
  const current = statuses.find((s) => s.value === status);
  // The one line under the preview is the Frame's own caption.
  const changed = status !== (part.status || "requested") || storefront !== initialStorefront;
  const reset = () => { setCover(null); setStatus(part.status || "requested"); setStorefront(initialStorefront); };
  const note = current && current.event ? `Your agent gets ${current.event}.` : tappable ? "Tap the card to pay." : "The card cannot be paid on this storefront.";

  return (
    <Frame className="relay-preview" caption={controls ? note : undefined}>
    <div className={"buttons-preview pay-preview" + (cover ? " is-cover-open" : "")}
      role="group" aria-label={label || spoken}>
      <style>{`
        .pay-preview { --pay-font: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Inter", system-ui, sans-serif; }
        .pay-preview.is-cover-open .buttons-preview-frame { min-height: 560px; }
        .pay-stage { display: flex; box-sizing: border-box; max-width: 402px; margin: 0 auto; padding: 16px; }
        .pay-preview .relay-preview-bar { padding-top: 0; }
        .pay-column { display: flex; flex-direction: column; gap: 12px; width: 100%; }
        .pay-card { position: relative; display: block; width: ${CARD_WIDTH}px; margin: 0; padding: 0; border: 0;
          background: none; color: inherit; font: inherit; text-align: left; -webkit-tap-highlight-color: transparent; }
        button.pay-card { cursor: pointer; }
        .pay-card:focus-visible { outline: 2px solid #0b75ff; outline-offset: 3px; border-radius: 20px; }
        .pay-card-shape { display: block; }
        .pay-card-shape path, .pay-receipt-shape path { fill: #2a292c; }
        .pay-picture { position: absolute; left: 0; top: 0; width: ${CARD_WIDTH}px; height: ${PICTURE_HEIGHT}px; overflow: hidden; }
        .pay-picture svg { display: block; width: 100%; height: 100%; }
        .pay-picture.is-dimmed { opacity: .6; filter: grayscale(1); }
        .pay-caption { position: absolute; left: 0; width: ${CARD_WIDTH}px; box-sizing: border-box;
          display: flex; align-items: center; min-height: ${MIN_CAPTION}px; padding: 9px 12.5px 8.5px ${LEADING}px;
          font-family: var(--pay-font); font-size: 12px; }
        .pay-text { flex: 1 1 auto; min-width: 0; margin-right: 12px; }
        .pay-title { color: #ffffff; font-weight: 600; line-height: 14.5px; min-height: 15px;
          display: -webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 2; overflow: hidden; overflow-wrap: anywhere; }
        .pay-subtitle { margin-top: 1.5px; color: #8d8d92; line-height: 15px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .pay-caption.is-dimmed .pay-title { color: rgba(255, 255, 255, .5); }
        .pay-caption.is-dimmed .pay-subtitle { color: rgba(141, 141, 146, .5); }
        .pay-wordmark { display: inline-block; height: 1.7123ex; width: 4.1096ex; vertical-align: -0.3425ex; fill: currentColor; }
        .pay-pill { flex: none; box-sizing: border-box; min-width: 44px; height: 22px; padding: 0 9px; border-radius: 11px;
          background: #ffffff; color: #000000; line-height: 22px; text-align: center; white-space: nowrap;
          transition: transform .32s cubic-bezier(.34, 1.4, .64, 1); }
        .pay-pill.is-unavailable { background: #3a3a3c; color: #8d8d92; font-weight: 600; }
        button.pay-card:active .pay-pill { transform: scale(.97); transition: transform .1s ease-out; }
        .pay-word { flex: none; display: flex; align-items: center; gap: 4px; padding: 0 4px; color: #8d8d92; line-height: 15px; white-space: nowrap; }
        .pay-check { width: 11px; height: 11px; fill: none; stroke: currentColor; stroke-width: 1; stroke-linecap: round; stroke-linejoin: round; }
        .pay-receipt { position: relative; align-self: flex-end; animation: selection-appear .2s ease-in-out; }
        .pay-receipt-shape { position: absolute; left: 0; top: 0; }
        .pay-receipt-text { position: absolute; left: 0; top: 0; width: max-content; max-width: ${CARD_WIDTH}px; box-sizing: border-box; padding: 8.5px ${LEADING}px 9px;
          font-family: var(--pay-font); font-size: 12px; }
        .pay-receipt-text .pay-subtitle { margin-top: 1.5px; }
        .pay-sheet-layer { position: absolute; inset: 0; }
        .pay-sheet-scrim { position: absolute; inset: 0; background: rgba(0, 0, 0, .2); }
        .pay-sheet { position: absolute; left: 0; right: 0; bottom: 0; display: flex; flex-direction: column; gap: 12px;
          padding: 16px 20px 20px; border-radius: 16px 16px 11px 11px; background: #ffffff; color: #1d1d1f;
          font-family: var(--pay-font); font-size: 15px; animation: selection-rise .22s ease-out; }
        .dark .pay-sheet { background: #1c1c1e; color: #ffffff; }
        .pay-sheet-close { align-self: flex-end; display: inline-flex; width: 28px; height: 28px; align-items: center; justify-content: center;
          margin: 0; padding: 0; border: 0; background: none; color: #8e8e93; cursor: pointer; }
        .pay-sheet-close svg { width: 16px; height: 16px; fill: none; stroke: currentColor; stroke-width: 2; stroke-linecap: round; }
        .pay-sheet-close:focus-visible, .pay-sheet-pay:focus-visible { outline: 2px solid #0b75ff; outline-offset: 2px; }
        .pay-apple-pay { display: flex; align-items: center; justify-content: center; height: 44px; border-radius: 12px;
          background: #000000; color: #ffffff; font-size: 19px; font-weight: 500; }
        .dark .pay-apple-pay { background: #ffffff; color: #000000; }
        .pay-divider { display: flex; align-items: center; gap: 12px; color: #8e8e93; font-size: 14px; }
        .pay-divider::before, .pay-divider::after { content: ""; flex: 1; height: 1px; background: #e0e0e5; }
        .dark .pay-divider::before, .dark .pay-divider::after { background: #3a3a3c; }
        .pay-field-label { color: #8e8e93; font-size: 14px; margin-bottom: -6px; }
        .pay-fields { display: grid; grid-template-columns: 1fr 1fr; border: 1px solid #e0e0e5; border-radius: 12px; overflow: hidden; }
        .dark .pay-fields { border-color: #3a3a3c; background: #2c2c2e; }
        .pay-fields span { padding: 12px 14px; color: #8e8e93; }
        .pay-fields span:first-child { grid-column: 1 / -1; border-bottom: 1px solid #e0e0e5; }
        .pay-fields span:last-child { border-left: 1px solid #e0e0e5; }
        .dark .pay-fields span:first-child, .dark .pay-fields span:last-child { border-color: #3a3a3c; }
        .pay-sheet-pay { display: flex; align-items: center; justify-content: center; height: 52px; margin: 4px 0 0; border: 0; border-radius: 26px;
          background: #0b75ff; color: #ffffff; font: inherit; font-size: 17px; font-weight: 600; cursor: pointer; transition: transform .15s ease-out; }
        .dark .pay-sheet-pay { background: #007eff; }
        .pay-sheet-pay:active { transform: scale(.98); }
        .pay-sheet-note { color: #8e8e93; font-size: 12px; text-align: center; }
        @media (prefers-reduced-motion: reduce) {
          .pay-preview *, .pay-preview *::before { transition: none !important; animation: none !important; }
          button.pay-card:active .pay-pill, .pay-sheet-pay:active { transform: none; }
        }
      `}</style>
      <div className="buttons-preview-frame">
        <div className="pay-stage">
          <div className="pay-column">
            {tappable ? (
              <button type="button" className="pay-card" style={{ height: cardTotal }} tabIndex={cover ? -1 : 0}
                aria-haspopup="dialog" aria-label={spoken} onClick={openCard}>
                {cardInner}
              </button>
            ) : (
              <div className="pay-card" style={{ height: cardTotal }} role="img" aria-label={spoken}>
                {cardInner}
              </div>
            )}
            {showsReceipt ? (
              <div className="pay-receipt" style={{ width: receiptW, height: receiptTotal }} role="img"
                aria-label={`Your receipt. ${part.description}. ${receiptLead} Stripe.`}>
                <svg className="pay-receipt-shape" width={receiptW} height={receiptTotal}
                  viewBox={`0 0 ${receiptW} ${receiptTotal}`} aria-hidden="true" focusable="false">
                  <path d={bubblePath(receiptW, receiptH, false)} />
                </svg>
                <div ref={receiptRef} className="pay-receipt-text">
                  <div className="pay-title">{part.description}</div>
                  <div className="pay-subtitle">{receiptLead} {wordmark}</div>
                </div>
              </div>
            ) : null}
          </div>
        </div>
        {controls ? (
          <div className="relay-preview-bar" role="group" aria-label="Payment request status">
            <div className="relay-preview-seg">
              {statuses.map((s) => (
                <button type="button" key={s.value} aria-pressed={status === s.value}
                  tabIndex={cover ? -1 : 0} onClick={() => { setCover(null); setStatus(s.value); }}>{s.value}</button>
              ))}
            </div>
            {part.category === "digital_goods" ? (
              <div className="relay-preview-seg">
                {[["USA", "United States storefront"], ["CAN", "Other storefront"]].map(([code, words]) => (
                  <button type="button" key={code} aria-pressed={storefront === code}
                    tabIndex={cover ? -1 : 0} onClick={() => setStorefront(code)}>{words}</button>
                ))}
              </div>
            ) : null}
          </div>
        ) : null}
        {controls && changed && !cover ? (
          <button type="button" className="relay-preview-reset" aria-label="Reset demo" title="Reset demo" onClick={reset}>
            <Icon icon="rotate-left" size={16} />
          </button>
        ) : null}
        {cover === "sheet" ? (
          // Stripe's PaymentSheet as RelayPaymentSheet configures it: Apple
          // Pay at 44pt and radius 12, card fields at radius 12, and a 52pt
          // pill Pay button in Relay's blue. Nothing is charged.
          <div className="pay-sheet-layer">
            <div className="pay-sheet-scrim" onClick={closeCover} />
            <div className="pay-sheet" role="dialog" aria-modal="true" aria-label="Payment sheet preview"
              onKeyDown={(event) => { if (event.key === "Escape") closeCover(event); }}>
              <button type="button" className="pay-sheet-close" autoFocus aria-label="Close" onClick={closeCover}>
                <svg viewBox="0 0 16 16" aria-hidden="true" focusable="false"><path d="M3 3l10 10M13 3L3 13" /></svg>
              </button>
              <div className="pay-apple-pay" aria-hidden="true">
                <svg width="15" height="18" viewBox="0 0 17 20" fill="currentColor" style={{ marginRight: 2 }} focusable="false">
                  <path d="M14.1 10.6c0-2.6 2.1-3.8 2.2-3.9-1.2-1.8-3.1-2-3.7-2-1.6-.2-3.1.9-3.9.9-.8 0-2-.9-3.4-.9-1.7 0-3.3 1-4.2 2.6-1.8 3.1-.5 7.7 1.3 10.2.9 1.2 1.9 2.6 3.2 2.6 1.3-.1 1.8-.8 3.3-.8 1.6 0 2 .8 3.4.8 1.4 0 2.3-1.3 3.1-2.5 1-1.4 1.4-2.8 1.4-2.9 0 0-2.7-1-2.7-4.1zM11.6 3.1C12.3 2.2 12.8 1.1 12.7 0c-1 0-2.2.7-2.9 1.5-.6.7-1.2 1.9-1 3 1.1.1 2.2-.6 2.8-1.4z" />
                </svg>
                Pay
              </div>
              <div className="pay-divider">Or pay using</div>
              <div className="pay-field-label">Card information</div>
              <div className="pay-fields" aria-hidden="true">
                <span>Card number</span>
                <span>MM / YY</span>
                <span>CVC</span>
              </div>
              <button type="button" className="pay-sheet-pay" onClick={payInSheet}>Pay {money()}</button>
              <div className="pay-sheet-note" role="status">Stripe's payment sheet. The demo charges nothing.</div>
            </div>
          </div>
        ) : null}
        {cover === "safari" ? (
          <div className="buttons-url-preview" role="dialog" aria-modal="true" aria-label="Pay page preview"
            onKeyDown={(event) => { if (event.key === "Escape") closeCover(event); }}>
            <div className="buttons-browser-bar">
              <button type="button" className="buttons-url-close" autoFocus aria-label="Close" onClick={closeCover}>
                <svg viewBox="0 0 16 16" aria-hidden="true" focusable="false"><path d="M4 4l8 8M12 4l-8 8" /></svg>
              </button>
              <div className="buttons-browser-address">
                <svg viewBox="0 0 12 14" aria-hidden="true" focusable="false">
                  <rect x="1.5" y="6" width="9" height="7" rx="1.5" />
                  <path d="M3.5 6V4.5a2.5 2.5 0 0 1 5 0V6" />
                </svg>
                <span>{(() => { try { return new URL(part.checkout_url).host; } catch (error) { return "pay.staging.relayapp.im"; } })()}</span>
              </div>
              <span aria-hidden="true" />
            </div>
            <div className="buttons-browser-page" role="status">
              <span className="buttons-url-caption">Pay page in Safari</span>
              <span className="buttons-url-address">{part.checkout_url}</span>
              <span className="buttons-browser-note">The app opens the pay page in Safari. The demo loads nothing.</span>
            </div>
          </div>
        ) : null}
      </div>
    </div>
    </Frame>
  );
};
