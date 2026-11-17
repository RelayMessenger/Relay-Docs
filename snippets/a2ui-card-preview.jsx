// A drawing of an A2UI v1.0 card on Relay's catalog, made from the exact
// message list an agent sends. It follows the app's own card: the incoming
// grey balloon (#e9e9e9 light, #2c2c2e dark) unless StyledCard sets a
// background, 16pt padding, 18pt corners, full-width capsule buttons and
// blue sliders. Controls write the data model in this page only; a button
// tap shows the `action` message your agent would receive. Nothing is sent.
//
// Snippet rules (see buttons-preview.jsx): Mintlify compiles this file as
// MDX, so every helper lives inside the component and only lowercase HTML
// tags are drawn. Frame is Mintlify's own component.
export const A2uiCardPreview = ({ messages, caption }) => {
  const clone = (value) => (value === undefined ? undefined : JSON.parse(JSON.stringify(value)));
  const parts = (path) => String(path || "").split("/").filter(Boolean);
  const getPath = (model, path) => parts(path).reduce((cur, key) => (cur == null ? undefined : cur[key]), model);
  const setPath = (model, path, value) => {
    const keys = parts(path);
    if (!keys.length) return clone(value) || {};
    const root = clone(model) || {};
    let cur = root;
    keys.slice(0, -1).forEach((key) => { if (cur[key] == null || typeof cur[key] !== "object") cur[key] = {}; cur = cur[key]; });
    if (value === null) delete cur[keys[keys.length - 1]];
    else cur[keys[keys.length - 1]] = value;
    return root;
  };
  const initial = () => {
    let components = {};
    let model = {};
    let surfaceId = "";
    for (const message of messages) {
      const create = message.createSurface;
      const update = message.updateComponents;
      const data = message.updateDataModel;
      if (create) {
        surfaceId = create.surfaceId;
        for (const c of create.components || []) components[c.id] = c;
        if (create.dataModel) model = clone(create.dataModel);
      }
      if (update) for (const c of update.components) components[c.id] = { ...(components[c.id] || {}), ...c };
      if (data) model = setPath(model, data.path || "/", data.value);
    }
    return { components, model, surfaceId };
  };
  const start = initial();
  const [model, setModel] = useState(start.model);
  const [tap, setTap] = useState(null);
  const [pin, setPin] = useState(null);
  const [now, setNow] = useState(0);
  useEffect(() => {
    const hasTimer = Object.values(start.components).some((c) => c.component === "Countdown");
    if (!hasTimer) return undefined;
    const timer = setInterval(() => setNow((value) => value + 1), 1000);
    return () => clearInterval(timer);
  }, []);

  const money = (value, currency = "USD", decimals) => new Intl.NumberFormat("en-US", {
    style: "currency", currency,
    minimumFractionDigits: decimals ?? 2, maximumFractionDigits: decimals ?? 2,
  }).format(Number(value) || 0);
  const growth = (monthly, rate, years) => {
    const n = years * 12;
    const r = rate / 1200;
    return r === 0 ? monthly * n : monthly * ((Math.pow(1 + r, n) - 1) / r);
  };
  const resolve = (value) => {
    if (Array.isArray(value)) return value.map(resolve);
    if (!value || typeof value !== "object") return value;
    if ("@path" in value) return getPath(model, value["@path"]);
    if ("@call" in value) {
      const a = Object.fromEntries(Object.entries(value.args || {}).map(([k, v]) => [k, resolve(v)]));
      switch (value["@call"]) {
        case "add": return Number(a.a) + Number(a.b);
        case "subtract": return Number(a.a) - Number(a.b);
        case "multiply": return Number(a.a) * Number(a.b);
        case "divide": return Number(a.b) === 0 ? 0 : Number(a.a) / Number(a.b);
        case "round": { const f = Math.pow(10, a.digits || 0); return Math.round(Number(a.value) * f) / f; }
        case "compoundGrowth": return growth(Number(a.monthly), Number(a.rate), Number(a.years));
        case "formatCurrency": return money(a.value, a.currency, a.decimals);
        case "formatNumber": return new Intl.NumberFormat("en-US").format(Number(a.value) || 0);
        case "formatString": return String(a.value).replace(/\$\{([^}]+)\}/g, (_, p) => String(getPath(model, p) ?? ""));
        default: return "";
      }
    }
    return value;
  };
  const inline = (text) => String(text ?? "").split(/(\*\*[^*]+\*\*)/g).map((piece, i) =>
    piece.startsWith("**") && piece.endsWith("**") ? <strong key={i}>{piece.slice(2, -2)}</strong> : piece);
  const JUSTIFY = { start: "flex-start", center: "center", end: "flex-end", spaceBetween: "space-between", spaceAround: "space-around", spaceEvenly: "space-evenly", stretch: "stretch" };
  const ALIGN = { start: "flex-start", center: "center", end: "flex-end", stretch: "stretch" };
  const WEIGHT = { regular: 400, semibold: 600, bold: 700, heavy: 800, black: 900 };
  const press = (id, action) => {
    if (!action?.event) return;
    const context = Object.fromEntries(Object.entries(action.event.context || {}).map(([k, v]) => [k, resolve(v)]));
    setTap({ version: "v1.0", action: { name: action.event.name, surfaceId: start.surfaceId, sourceComponentId: id, timestamp: new Date().toISOString().replace(/\.\d+Z$/, "Z"), context } });
  };

  const draw = (id) => {
    const c = start.components[id];
    if (!c) return null;
    const flex = c.weight ? { flexGrow: c.weight, flexBasis: 0 } : undefined;
    switch (c.component) {
      case "StyledCard":
      case "Card":
        return <div key={id} className="a2-card" style={{ background: c.background, borderRadius: c.cornerRadius ?? 18, color: c.background ? "#fff" : undefined }}>{draw(c.child)}</div>;
      case "Column":
      case "Row":
      case "List":
        return <div key={id} className={c.component === "Row" || c.direction === "horizontal" ? "a2-row" : "a2-col"}
          style={{ justifyContent: JUSTIFY[c.justify], alignItems: ALIGN[c.align], ...flex }}>{(c.children || []).map(draw)}</div>;
      case "StyledText":
        return <div key={id} className="a2-text" style={{ color: resolve(c.color), fontSize: c.size || 17, fontWeight: WEIGHT[c.weight] || 400, ...flex }}>{inline(resolve(c.text))}</div>;
      case "Text":
        return <div key={id} className={"a2-text" + (c.variant === "caption" ? " is-caption" : "")} style={flex}>{inline(resolve(c.text))}</div>;
      case "Badge":
        return <span key={id} className="a2-badge" style={{ color: resolve(c.color), background: resolve(c.background) }}>{resolve(c.text)}</span>;
      case "Divider":
        return <hr key={id} className="a2-divider" />;
      case "StyledButton":
        return <button key={id} type="button" className="a2-button" style={{ background: c.background, color: c.color }} onClick={() => press(id, c.action)}>{resolve(c.label)}</button>;
      case "Button":
        return <button key={id} type="button" className={"a2-button" + (c.variant === "borderless" ? " is-borderless" : "")} onClick={() => press(id, c.action)}>{draw(c.child)}</button>;
      case "Slider": {
        const value = Number(resolve(c.value)) || 0;
        const path = c.value?.["@path"];
        const step = c.steps ? (c.max - c.min) / c.steps : 1;
        return <label key={id} className="a2-slider">
          <span className="a2-slider-head"><span>{resolve(c.label)}</span><span>{value}</span></span>
          <input type="range" min={c.min ?? 0} max={c.max} step={step} value={value} aria-label={resolve(c.label)}
            style={{ "--a2-fill": `${((value - (c.min ?? 0)) / (c.max - (c.min ?? 0))) * 100}%` }}
            onChange={(event) => path && setModel((m) => setPath(m, path, Number(event.target.value)))} />
        </label>;
      }
      case "CheckBox": {
        const path = c.value?.["@path"];
        const on = Boolean(resolve(c.value));
        return <button key={id} type="button" role="checkbox" aria-checked={on} className={"a2-check" + (on ? " is-on" : "")}
          onClick={() => path && setModel((m) => setPath(m, path, !on))}>
          <span className="a2-box" aria-hidden="true">{on ? "✓" : ""}</span><span>{resolve(c.label)}</span>
        </button>;
      }
      case "ChoicePicker": {
        const path = c.value?.["@path"];
        const chosen = resolve(c.value) || [];
        const single = c.variant !== "multipleSelection";
        return <div key={id} className="a2-choices" role={single ? "radiogroup" : "group"}>{c.options.map((option) => {
          const on = chosen.includes(option.value);
          return <button key={option.value} type="button" role={single ? "radio" : "checkbox"} aria-checked={on} className={"a2-choice" + (on ? " is-on" : "")}
            onClick={() => path && setModel((m) => setPath(m, path, single ? [option.value] : on ? chosen.filter((v) => v !== option.value) : [...chosen, option.value]))}>
            <span className="a2-dot" aria-hidden="true" /><span>{resolve(option.label)}</span>
          </button>;
        })}</div>;
      }
      case "BarChart": {
        const values = (resolve(c.values) || []).map(Number);
        const top = Math.max(...values, 1);
        return <div key={id} className="a2-chart" role="img" aria-label={`Bar chart: ${values.map((v, i) => `${c.labels?.[i] || i + 1} ${Math.round(v)}`).join(", ")}`}>
          {values.map((v, i) => <div key={i} className="a2-bar-slot"><div className="a2-bar" style={{ height: `${(v / top) * 100}%` }} /><span>{c.labels?.[i]}</span></div>)}
        </div>;
      }
      case "MapPins": {
        const lats = c.pins.map((p) => p.lat);
        const lons = c.pins.map((p) => p.lon);
        const [minLat, maxLat, minLon, maxLon] = [Math.min(...lats), Math.max(...lats), Math.min(...lons), Math.max(...lons)];
        const x = (lon) => 12 + ((lon - minLon) / ((maxLon - minLon) || 1)) * 76;
        const y = (lat) => 12 + ((maxLat - lat) / ((maxLat - minLat) || 1)) * 76;
        return <div key={id} className="a2-map-wrap">
          <div className="a2-map" role="group" aria-label="Map drawing with pins">
            {c.pins.map((p, i) => <button key={i} type="button" className={"a2-pin" + (pin === i ? " is-on" : "")} aria-label={p.title}
              style={{ left: `${x(p.lon)}%`, top: `${y(p.lat)}%` }} onClick={() => setPin(i)} />)}
          </div>
          {pin != null ? <div className="a2-pin-detail"><strong>{c.pins[pin].title}</strong><span>{c.pins[pin].detail}</span></div> : null}
        </div>;
      }
      case "Countdown": {
        const left = Math.max(0, (c.seconds || 0) - now);
        const hh = Math.floor(left / 3600);
        const mm = String(Math.floor((left % 3600) / 60)).padStart(hh ? 2 : 1, "0");
        const ss = String(left % 60).padStart(2, "0");
        return <div key={id} className="a2-countdown">{hh ? `${hh}:` : ""}{mm}:{ss}</div>;
      }
      case "Image":
        return <div key={id} className="a2-image" role="img" aria-label={resolve(c.description) || "Image"} />;
      default:
        return null;
    }
  };

  return (
    <Frame className="relay-preview" caption={caption || "Drawing of the card in the Relay app. Controls work in this page only."}>
      <div className="native-preview a2-preview">
        <div className="native-transcript">
          <div className="a2-balloon">{draw("root")}</div>
          {tap ? <details className="native-response" open>
            <summary>Your agent receives (local preview)</summary>
            <pre>{JSON.stringify({ type: "data", media_type: "application/a2ui+json", data: [tap] }, null, 2)}</pre>
          </details> : null}
        </div>
      </div>
    </Frame>
  );
};
