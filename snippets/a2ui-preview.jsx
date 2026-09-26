// A live A2UI v0.9.1 card, drawn from the exact message array an agent sends,
// the way the Relay app draws it. A port of the approved card renderer
// (custom-cards grid spec 2026-09-25, a2ui_render.py with base_style.css and
// grid.html's second style block): the 274pt grey bubble with the incoming
// tail, 16pt padding, 44pt pills, left-circle choice rows, capsule fields,
// inset boxes for nested Cards, and the paged photo carousel.
//
// Everything is local. Controls write the data model in this page only; a
// Button tap shows the A2UI `action` message Relay would send, and `reply`
// (a follow-up message array, for example updateComponents on the same
// surface) is applied once after the first tap, as an agent's update would be.
// Nothing is sent anywhere.
//
// Snippet rules (see buttons-preview.jsx): Mintlify compiles this file as
// MDX, so only exports stay in scope and every helper lives inside the
// component, and a capitalised tag would be read as an MDX component, so the
// renderer calls lowercase functions and draws only lowercase HTML tags.
export const A2uiPreview = ({ messages, reply, media, label, icons = "/images/cards/icons" }) => {
  const V = "v0.9.1";
  const HEAD = ["h1", "h2", "h3", "h4", "h5"];
  const TEXT_CLS = { h1: "a2-h1", h2: "a2-h2", h3: "a2-h3", h4: "a2-t", h5: "a2-h5" };
  const JUST = { start: "flex-start", center: "center", end: "flex-end", spaceBetween: "space-between",
    spaceAround: "space-around", spaceEvenly: "space-evenly", stretch: "flex-start" };
  const ALIGN = { start: "flex-start", center: "center", end: "flex-end", stretch: "stretch" };
  const TEXTISH = ["heading", "subtitle", "body", "caption", "image", "video", "audio", "field", "slider", "datetime", "iconrow", "icon"];
  const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  // The BubbleKit roundTailed contour, mirrored to the leading edge: the same
  // path buttons-preview.jsx draws under an incoming text balloon.
  const TAIL = "M 0 0 C 0 0.306 1.415 4.498 4.028 7.924 C 5.087 9.312 6.309 10.536 7.660 11.577 C 9.585 13.078 10.418 14.644 10.418 16.404 C 10.418 17.587 10.209 18.756 8.510 20.988 C 7.695 22.058 8.513 23.150 9.787 22.666 C 12.407 21.671 15.391 19.860 18.005 17.927 C 20.347 16.195 20.971 16.020 22.070 16.013 L 22.070 0 Z";

  // ---------- data model ----------
  const clone = (value) => (value === undefined ? undefined : JSON.parse(JSON.stringify(value)));
  const segments = (path) => path.split("/").filter((part) => part !== "");
  const ptrGet = (obj, path) => {
    let cur = obj;
    for (const part of segments(path)) {
      if (Array.isArray(cur)) cur = /^\d+$/.test(part) ? cur[Number(part)] : undefined;
      else if (cur && typeof cur === "object") cur = cur[part];
      else return undefined;
      if (cur === undefined || cur === null) return undefined;
    }
    return cur;
  };
  const ptrSet = (obj, path, value) => {
    const parts = segments(path);
    if (parts.length === 0) return clone(value) || {};
    const root = clone(obj) || {};
    let cur = root;
    parts.slice(0, -1).forEach((part, index) => {
      if (cur[part] === undefined || cur[part] === null || typeof cur[part] !== "object") {
        cur[part] = /^\d+$/.test(parts[index + 1]) ? [] : {};
      }
      cur = cur[part];
    });
    const last = parts[parts.length - 1];
    if (value === undefined) delete cur[last];
    else cur[last] = clone(value);
    return root;
  };
  const applyData = (data, list) => list.reduce((model, message) => {
    const update = message.updateDataModel;
    if (!update) return model;
    return ptrSet(model, update.path || "/", "value" in update ? update.value : undefined);
  }, data);
  const surfaceOf = (list) => {
    const out = { comps: {}, sid: null };
    for (const message of list) {
      if (message.createSurface) out.sid = message.createSurface.surfaceId;
      if (message.updateComponents) {
        out.sid = out.sid || message.updateComponents.surfaceId;
        for (const component of message.updateComponents.components) out.comps[component.id] = component;
      }
      if (message.deleteSurface) out.deleted = true;
    }
    return out;
  };

  const [shown, setShown] = useState(messages);
  const [data, setData] = useState(() => applyData({}, messages));
  const [taps, setTaps] = useState([]);
  const [open, setOpen] = useState(null);
  const [tabs, setTabs] = useState({});
  const [pages, setPages] = useState({});
  const [aspects, setAspects] = useState({});
  const [playing, setPlaying] = useState({});
  const [replied, setReplied] = useState(false);

  const surface = surfaceOf(shown);
  const comps = surface.comps;

  // A scope is the absolute path of a templated List item; relative paths
  // resolve against it.
  const resolve = (path, scope) => (path.startsWith("/") ? path : ((scope || "") + "/" + (path)));
  const get = (path, scope) => ptrGet(data, resolve(path, scope));
  const setBound = (binding, value, scope) => {
    if (binding && typeof binding === "object" && typeof binding.path === "string") {
      const target = resolve(binding.path, scope);
      setData((model) => ptrSet(model, target, value));
    }
  };

  const format = (template, scope) => String(template).replace(/(\\?)\$\{([^}]*)\}/g, (whole, escaped, expression) => {
    if (escaped) return whole.slice(1);
    const x = get(expression.trim(), scope);
    if (Array.isArray(x)) return x.length ? String(x[0]) : "";
    return x === undefined || x === null ? "" : String(x);
  });
  const fn = (v, scope) => {
    const a = v.args || {};
    const val = () => dyn(a.value, scope);
    switch (v.call) {
      case "required": { const x = val(); return !(x === undefined || x === null || x === "" || x === false || (Array.isArray(x) && x.length === 0)); }
      case "email": return /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(String(val() || ""));
      case "regex": try { return new RegExp(a.pattern).test(String(val() ?? "")); } catch (error) { return false; }
      case "length": { const n = String(val() ?? "").length; return (a.min === undefined || n >= a.min) && (a.max === undefined || n <= a.max); }
      case "numeric": {
        const raw = val();
        const x = Number(raw);
        if (raw === "" || raw === null || raw === undefined || Number.isNaN(x)) return false;
        return (a.min === undefined || x >= a.min) && (a.max === undefined || x <= a.max);
      }
      case "not": return !dyn(a.value, scope);
      case "and": return (a.values || []).every((x) => dyn(x, scope));
      case "or": return (a.values || []).some((x) => dyn(x, scope));
      case "formatString": return format(dyn(a.value, scope) ?? "", scope);
      case "formatNumber": {
        const decimals = dyn(a.decimals, scope);
        return Number(val() || 0).toLocaleString("en-US", { minimumFractionDigits: decimals, maximumFractionDigits: decimals ?? 2, useGrouping: dyn(a.grouping, scope) !== false });
      }
      case "formatCurrency": {
        const decimals = dyn(a.decimals, scope);
        return Number(val() || 0).toLocaleString("en-US", { style: "currency", currency: dyn(a.currency, scope) || "USD", minimumFractionDigits: decimals, maximumFractionDigits: decimals });
      }
      case "pluralize": {
        const n = Number(val());
        if (n === 0 && a.zero !== undefined) return dyn(a.zero, scope);
        return n === 1 ? dyn(a.one, scope) : dyn(a.other, scope);
      }
      default: return undefined;
    }
  };
  const dyn = (v, scope) => {
    if (v && typeof v === "object" && !Array.isArray(v)) {
      if (typeof v.path === "string" && !v.call) return get(v.path, scope);
      if (v.call) return fn(v, scope);
    }
    return v;
  };
  const failing = (c, scope) => (c.checks || []).filter((rule) => !dyn(rule.condition, scope)).map((rule) => rule.message);

  // **bold**, *italic* and [links](url), drawn as text: nothing here navigates.
  const md = (s, keyBase = "m") => {
    const out = [];
    const pattern = /\*\*(.+?)\*\*|\*(\S.*?)\*|\[(.+?)\]\((.+?)\)/g;
    let last = 0;
    let match;
    const text = String(s ?? "");
    while ((match = pattern.exec(text))) {
      if (match.index > last) out.push(text.slice(last, match.index));
      const key = ((keyBase) + (match.index));
      if (match[1] !== undefined) out.push(<b key={key}>{match[1]}</b>);
      else if (match[2] !== undefined) out.push(<i key={key}>{match[2]}</i>);
      else out.push(<span key={key} className="a2-link">{match[3]}</span>);
      last = pattern.lastIndex;
    }
    if (last < text.length) out.push(text.slice(last));
    return out;
  };

  const src = (url) => (media && media[url]) || url;
  const aspect = (url) => Math.min(2, Math.max(0.8, aspects[url] || 2));
  const measure = (url) => (element) => {
    if (element && element.complete && element.naturalWidth && !aspects[url]) {
      const ratio = element.naturalWidth / element.naturalHeight;
      setAspects((current) => (current[url] ? current : { ...current, [url]: ratio }));
    }
  };
  const loaded = (url) => (event) => {
    const element = event.currentTarget;
    if (element.naturalWidth) {
      const ratio = element.naturalWidth / element.naturalHeight;
      setAspects((current) => (current[url] ? current : { ...current, [url]: ratio }));
    }
  };
  const icon = (name, cls = "") => (
    <i className={("a2-ic " + (cls))} style={{ "--m": ("url(" + (icons) + "/" + (name) + ".png)") }} aria-hidden="true" />
  );

  // ---------- structure ----------
  const items = (c, scope) => {
    const children = c.children;
    if (Array.isArray(children)) return children.map((id) => ({ id, scope }));
    if (children && children.path) {
      const base = resolve(children.path, scope);
      const list = ptrGet(data, base) || [];
      return list.map((_, index) => ({ id: children.componentId, scope: ((base) + "/" + (index)) }));
    }
    return [];
  };
  const kind = (cid) => {
    const c = comps[cid];
    if (!c) return "missing";
    const t = c.component;
    if (t === "Text") {
      const v = c.variant || "body";
      return HEAD.includes(v) ? "heading" : v;
    }
    if (t === "Button" || t === "Modal") return "button";
    if (t === "Row") {
      const ks = (Array.isArray(c.children) ? c.children : []).map((k) => comps[k] && comps[k].component);
      if (ks.length && ks.every((k) => k === "Button" || k === "Modal")) return "buttons";
      if (ks.length && ks[0] === "Icon" && ks.includes("Text")) return "iconrow";
      return "row";
    }
    return { Image: "image", Video: "video", AudioPlayer: "audio", Column: "col", List: "list", Card: "card",
      Tabs: "tabs", Divider: "divider", TextField: "field", CheckBox: "checkbox", ChoicePicker: "choice",
      Slider: "slider", DateTimeInput: "datetime", Icon: "icon" }[t] || "missing";
  };
  const margin = (prev, k) => {
    if (prev === null) return 0;
    if (k === "subtitle") return 4;
    if (k === "heading") return 12;
    if (["body", "caption", "iconrow", "col", "list", "checkbox", "icon"].includes(k)) return 8;
    if (k === "buttons" || k === "button") return TEXTISH.includes(prev) ? 20 : 14;
    if (k === "choice") return 10;
    return 12;
  };
  const isCarousel = (c) => c && c.component === "List" && c.direction === "horizontal" && Array.isArray(c.children)
    && c.children.every((k) => comps[k] && comps[k].component === "Image");

  // The card's own Column: Relay's block spacing between children.
  const cardColumn = (cid, scope, top) => {
    const kids = items(comps[cid], scope);
    const out = [];
    let prev = null;
    let i = 0;
    if (kids.length && top) {
      const first = comps[kids[0].id];
      if (first && first.component === "Image" && ["mediumFeature", "largeFeature", "header"].includes(first.variant || "mediumFeature")) {
        out.push(<div key="hero">{hero(first, kids[0].scope)}</div>);
        i = 1;
      } else if (isCarousel(first)) {
        out.push(<div key="hero">{carousel(first, true, kids[0].scope)}</div>);
        i = 1;
      }
    }
    while (i < kids.length) {
      let k = kind(kids[i].id);
      let html;
      let next;
      if (k === "button") {
        // Consecutive Buttons in a Column stack.
        let j = i;
        while (j < kids.length && kind(kids[j].id) === "button") j += 1;
        html = buttonGroup(kids.slice(i, j), false);
        next = j;
      } else {
        if (k === "caption" && prev === "heading") k = "subtitle";
        html = block(kids[i].id, k, kids[i].scope);
        next = i + 1;
      }
      const group = k === "button" ? "buttons" : k;
      out.push(<div key={("b" + (i))} className="a2-blk" style={{ marginTop: margin(prev, group) }}>{html}</div>);
      prev = group;
      i = next;
    }
    return out;
  };

  const block = (cid, k, scope, ctx = "card") => {
    const c = comps[cid];
    if (!c) return null;
    const t = c.component;
    if (t === "Text") return text(c, k, scope, ctx);
    if (t === "Image") return image(c, scope, ctx);
    if (t === "Icon") return icon(dyn(c.name, scope));
    if (t === "Video") return video(c, scope);
    if (t === "AudioPlayer") return audio(c, scope);
    if (t === "Row") return row(c, scope, ctx);
    if (t === "Column") return column(c, scope, ctx);
    if (t === "List") return list(c, scope);
    if (t === "Card") {
      const child = comps[c.child];
      const inner = child && child.component === "Column" ? cardColumn(child.id, scope, false) : block(c.child, kind(c.child), scope);
      return <div className="a2-box">{inner}</div>;
    }
    if (t === "Tabs") return tabbed(c, scope);
    if (t === "Divider") return c.axis === "vertical" ? <div className="a2-vd" role="separator" aria-orientation="vertical" /> : <div className="a2-hr" role="separator" />;
    if (t === "Button" || t === "Modal") return buttonGroup([{ id: cid, scope }], false);
    if (t === "TextField") return field(c, scope);
    if (t === "CheckBox") return checkbox(c, scope);
    if (t === "ChoicePicker") return choice(c, scope);
    if (t === "Slider") return slider(c, scope);
    if (t === "DateTimeInput") return datetime(c, scope);
    return null;
  };

  const text = (c, k, scope, ctx) => {
    const s = md(dyn(c.text, scope) ?? "", c.id);
    const v = c.variant || "body";
    if (ctx === "row" || ctx === "listrow") {
      if (HEAD.includes(v)) return <div className={ctx === "listrow" ? "a2-on1 a2-bd" : TEXT_CLS[v]}>{s}</div>;
      if (v === "caption") return <div className="a2-os">{s}</div>;
      return <div className={ctx === "listrow" ? "a2-on1" : "a2-b"}>{s}</div>;
    }
    if (ctx === "hitem") return <div className={v === "caption" ? "a2-hp" : "a2-hn"}>{s}</div>;
    if (HEAD.includes(v)) return <div className={TEXT_CLS[v]} role="heading" aria-level={Number(v.slice(1)) + 2}>{s}</div>;
    if (k === "subtitle") return <div className="a2-s">{s}</div>;
    if (v === "caption") return <div className="a2-tc">{s}</div>;
    return <div className="a2-b">{s}</div>;
  };

  const fitOf = (c) => ({ scaleDown: "scale-down" }[c.fit || "cover"] || c.fit || "cover");
  const image = (c, scope, ctx) => {
    const url = dyn(c.url, scope);
    const v = c.variant || "mediumFeature";
    const alt = dyn(c.description, scope) || "";
    const common = { src: src(url), alt, ref: measure(url), onLoad: loaded(url) };
    const cls = { icon: "ic", avatar: "av", smallFeature: "sm", mediumFeature: "md", largeFeature: "lg", header: "hd" }[v];
    const feature = ["mediumFeature", "largeFeature", "header"].includes(v);
    if (ctx === "hitem") return <img className="a2-hli-img" {...common} />;
    if ((ctx === "row" || ctx === "listrow") && feature) return <img className="a2-im sq" style={{ objectFit: fitOf(c) }} {...common} />;
    if (feature) return <img className="a2-im fe" style={{ aspectRatio: aspect(url).toFixed(4), objectFit: fitOf(c) }} {...common} />;
    return <img className={("a2-im " + (cls))} style={{ objectFit: fitOf(c) }} {...common} />;
  };
  // A link preview's picture: full card width, its own shape between 4:5 and 2:1.
  const hero = (c, scope) => {
    const url = dyn(c.url, scope);
    return <img className="a2-hero" src={src(url)} alt={dyn(c.description, scope) || ""} ref={measure(url)} onLoad={loaded(url)}
      style={{ aspectRatio: aspect(url).toFixed(4), objectFit: fitOf(c) }} />;
  };
  // A horizontal List of Images: one photo per page, in the first photo's
  // clamped shape, with the iOS page control.
  const carousel = (c, isHero, scope) => {
    const imgs = c.children.map((k) => comps[k]);
    const n = imgs.length;
    const page = Math.min(pages[c.id] || 0, n - 1);
    const firstURL = dyn(imgs[0].url, scope);
    const go = (event, index) => {
      const track = event.currentTarget.closest(".a2-car").querySelector(".a2-car-track");
      track.scrollTo({ left: index * track.clientWidth, behavior: "smooth" });
      setPages((current) => ({ ...current, [c.id]: index }));
    };
    return (
      <div className={("a2-car " + (isHero ? "hero" : "inset"))} style={{ aspectRatio: aspect(firstURL).toFixed(4) }}>
        <div className="a2-car-track" tabIndex={0} role="group" aria-roledescription="carousel"
          aria-label={("Photo " + (page + 1) + " of " + (n))}
          onScroll={(event) => {
            const el = event.currentTarget;
            const p = Math.round(el.scrollLeft / el.clientWidth);
            if (p !== (pages[c.id] || 0)) setPages((current) => ({ ...current, [c.id]: p }));
          }}>
          {imgs.map((img, index) => {
            const url = dyn(img.url, scope);
            return <img key={img.id} src={src(url)} alt={dyn(img.description, scope) || ""} ref={measure(url)} onLoad={loaded(url)}
              style={{ objectFit: fitOf(img) }} />;
          })}
        </div>
        {n > 1 ? (
          <div className="a2-pc">
            {imgs.slice(0, 7).map((img, index) => {
              const size = index < 5 || n <= 5 ? 8 : (index === 5 ? 6 : 4);
              return <button type="button" key={img.id} className={index === page ? "on" : ""} style={{ width: size, height: size }}
                aria-label={("Show photo " + (index + 1))} aria-current={index === page ? "true" : undefined}
                onClick={(event) => go(event, index)} />;
            })}
          </div>
        ) : null}
      </div>
    );
  };

  const video = (c, scope) => {
    const on = playing[c.id];
    const toggle = (event) => {
      const el = event.currentTarget.closest(".a2-vid").querySelector("video");
      if (on) el.pause(); else el.play();
      setPlaying((current) => ({ ...current, [c.id]: !on }));
    };
    return (
      <div className="a2-vid">
        <video src={src(dyn(c.url, scope))} preload="metadata" playsInline muted />
        <button type="button" className="a2-pd" aria-label={on ? "Pause video" : "Play video"} onClick={toggle}>{icon(on ? "pause" : "play", "w")}</button>
      </div>
    );
  };
  const audio = (c, scope) => {
    const on = playing[c.id];
    const description = dyn(c.description, scope) || "";
    const toggle = (event) => {
      const el = event.currentTarget.closest(".a2-au").querySelector("audio");
      if (on) el.pause(); else el.play();
      setPlaying((current) => ({ ...current, [c.id]: !on }));
    };
    return (
      <div className="a2-au">
        <div className="a2-ot"><div className="a2-on1">{description}</div></div>
        <button type="button" className="a2-pb" aria-label={((on ? "Pause" : "Play") + " " + (description))} onClick={toggle}>{on ? icon("pause") : icon("play", "pl1")}</button>
        <audio src={src(dyn(c.url, scope))} preload="none" />
      </div>
    );
  };

  const row = (c, scope, ctx) => {
    const kids = items(c, scope);
    const cs = kids.map((k) => comps[k.id]).filter(Boolean);
    const ks = cs.map((x) => x.component);
    if (ks.length && ks.every((k) => k === "Button" || k === "Modal")) return buttonGroup(kids, true, c.justify);
    const al = ALIGN[c.align || "stretch"];
    if (ks.length && ks[0] === "Icon" && ks.includes("Text")) {
      const iconsIn = cs.filter((x) => x.component === "Icon");
      const texts = cs.filter((x) => x.component === "Text");
      const glyphs = iconsIn.map((x) => <span key={x.id} style={{ display: "contents" }}>{icon(dyn(x.name, scope))}</span>);
      const words = texts.map((x, index) => <span key={x.id}>{index ? " " : ""}{md(dyn(x.text, scope), x.id)}</span>);
      if (iconsIn.length === 1 && HEAD.includes(texts[0].variant)) {
        return <div className="a2-ir" style={{ alignItems: al }}>{glyphs}<div className={TEXT_CLS[texts[0].variant]}>{words}</div></div>;
      }
      if (iconsIn.length === 1 && texts[0].variant === "caption") return <div className="a2-note" style={{ alignItems: al }}>{glyphs}<span>{words}</span></div>;
      if (iconsIn.length > 1) return <div className="a2-ir" style={{ gap: 0, alignItems: al }}>{glyphs}<span style={{ marginLeft: 8 }}>{words}</span></div>;
      return <div className="a2-ir" style={{ alignItems: al }}>{glyphs}<span>{words}</span></div>;
    }
    const j = c.justify || "start";
    const texts = cs.filter((x) => x.component === "Text");
    if (j === "spaceBetween" && cs.length === 2 && texts.length === 2 && cs[0].variant === "caption") {
      return <div className="a2-dr">{cs.map((x) => <span key={x.id}>{md(dyn(x.text, kids[0].scope), x.id)}</span>)}</div>;
    }
    const hasImg = ks.includes("Image");
    const onlyImg = ks.every((k) => k === "Image");
    const gap = onlyImg ? 8 : hasImg ? 12 : (["spaceAround", "spaceEvenly"].includes(j) ? 0 : (j === "spaceBetween" ? 8 : 16));
    const sub = ctx === "listrow" ? "listrow" : "row";
    const inner = kids.map((k) => {
      const x = comps[k.id];
      if (!x) return null;
      const w = x.weight;
      const style = j === "stretch" && x.component !== "Divider" ? { flex: 1, minWidth: 0 } : (w ? { flex: w, minWidth: 0 } : null);
      if (x.component === "Column") {
        return <div key={k.id + (k.scope || "")} style={{ display: "flex", flexDirection: "column", ...(style || {}) }}>{column(x, k.scope, sub)}</div>;
      }
      if (x.component === "Button" || x.component === "Modal") return <div key={k.id + (k.scope || "")} className="a2-fxb">{btn(k.id, k.scope).el}</div>;
      const h = block(k.id, kind(k.id), k.scope, sub);
      return style ? <div key={k.id + (k.scope || "")} style={style}>{h}</div> : <span key={k.id + (k.scope || "")} style={{ display: "contents" }}>{h}</span>;
    });
    return <div className="a2-fx" style={{ justifyContent: JUST[j], alignItems: ALIGN[c.align || "stretch"], gap }}>{inner}</div>;
  };

  const column = (c, scope, ctx) => {
    const j = c.justify || "start";
    const a = c.align || "stretch";
    let prev = null;
    const out = items(c, scope).map((k, index) => {
      let kk = kind(k.id);
      if (kk === "caption" && prev === "heading") kk = "subtitle";
      const h = block(k.id, kk, k.scope, ["row", "listrow", "hitem"].includes(ctx) ? ctx : "card");
      let m = 0;
      if (prev !== null && ["start", "center", "end", "stretch"].includes(j)) {
        m = kk === "subtitle" ? 4 : (ctx === "card" ? 8 : 0);
        if (prev === "button") m = 4;
        if (kk === "row") m = 8;
      }
      prev = kk;
      return <div key={k.id + index} style={{ marginTop: m }}>{h}</div>;
    });
    return (
      <div className="a2-fx col" style={{ justifyContent: JUST[j], alignItems: ALIGN[a], textAlign: { center: "center", end: "right" }[a] || "left", flex: "1 1 auto" }}>
        {out}
      </div>
    );
  };

  const isDetail = (r) => {
    const kids = Array.isArray(r.children) ? r.children.map((k) => comps[k]).filter(Boolean) : [];
    return r.justify === "spaceBetween" && kids.length === 2 && kids.every((k) => k.component === "Text") && kids[0].variant === "caption";
  };
  const list = (c, scope) => {
    const entries = items(c, scope);
    if (c.direction === "horizontal" && isCarousel(c)) return carousel(c, false, scope);
    if (c.direction === "horizontal") {
      return (
        <div className="a2-hl">
          {entries.map((k, index) => {
            const x = comps[k.id];
            if (!x) return null;
            return <div key={index} className="a2-hli">{x.component === "Column" ? column(x, k.scope, "hitem") : block(k.id, kind(k.id), k.scope, "hitem")}</div>;
          })}
        </div>
      );
    }
    const a = c.align || "stretch";
    const kinds = entries.map((k) => comps[k.id] && comps[k.id].component);
    if (kinds.length && kinds.every((k) => k === "Row")) {
      const detail = entries.every((k) => isDetail(comps[k.id]));
      const rows = entries.map((k, index) => {
        const r = comps[k.id];
        const h = row(r, k.scope, "listrow");
        if (detail) return <div key={index} style={{ display: "contents" }}>{h}</div>;
        const hasImg = (Array.isArray(r.children) ? r.children : []).some((x) => comps[x] && comps[x].component === "Image");
        return <div key={index} className={("a2-lr" + (hasImg ? " th" : ""))}>{h}</div>;
      });
      return <div className={detail ? "a2-dt" : "a2-fx col"} style={{ alignItems: ALIGN[a] }}>{rows}</div>;
    }
    return (
      <div className="a2-fx col" style={{ alignItems: ALIGN[a], gap: 0 }}>
        {entries.map((k, index) => <div key={index} style={{ padding: "4px 0" }}>{block(k.id, kind(k.id), k.scope, "listrow")}</div>)}
      </div>
    );
  };

  const tabbed = (c, scope) => {
    const on = tabs[c.id] || 0;
    const child = c.tabs[on] && c.tabs[on].child;
    return (
      <div>
        <div className="a2-seg" role="tablist">
          {c.tabs.map((tab, index) => (
            <button type="button" role="tab" key={index} aria-selected={index === on} className={index === on ? "on" : ""}
              onClick={() => setTabs((current) => ({ ...current, [c.id]: index }))}>{dyn(tab.title, scope)}</button>
          ))}
        </div>
        <div style={{ marginTop: 8 }} role="tabpanel">{child ? block(child, kind(child), scope) : null}</div>
      </div>
    );
  };

  // ---------- controls ----------
  const tap = (cid, scope) => {
    const c = comps[cid];
    const event = c && c.action && c.action.event;
    if (!event) return;
    const context = {};
    Object.entries(event.context || {}).forEach(([key, value]) => { context[key] = dyn(value, scope); });
    const message = [{ version: V, action: { name: event.name, surfaceId: surface.sid, sourceComponentId: cid,
      timestamp: new Date().toISOString(), context } }];
    setTaps((current) => [...current, message]);
    setOpen(null);
    if (reply && !replied) {
      setReplied(true);
      setShown((current) => [...current, ...reply]);
      setData((model) => applyData(model, reply));
    }
  };
  // ViewThatFits needs a width: the 16pt medium label, estimated per character.
  const labelWidth = (label) => String(label).length * 8.4;
  const btn = (cid, scope) => {
    const c = comps[cid];
    if (!c) return { el: null, variant: "default", w: 0 };
    if (c.component === "Modal") {
      const inner = btn(c.trigger, scope);
      const trigger = comps[c.trigger];
      const child = trigger && comps[trigger.child];
      const labelText = child && child.component === "Text" ? dyn(child.text, scope) : (child ? dyn(child.name, scope) : "");
      const cls = { primary: "p", default: "", borderless: "bl" }[(trigger && trigger.variant) || "default"];
      return { ...inner, el: (
        <button type="button" className={("a2-btn " + (cls))} aria-haspopup="dialog" onClick={() => setOpen(cid)}>{labelText}</button>
      ) };
    }
    const child = comps[c.child];
    const v = c.variant || "default";
    const cls = { primary: "p", default: "", borderless: "bl" }[v] || "";
    const dis = failing(c, scope).length > 0;
    if (child && child.component === "Icon") {
      const name = dyn(child.name, scope);
      return { el: (
        <button type="button" className={("a2-btn icn " + (cls) + (dis ? " dis" : ""))} disabled={dis} aria-label={name}
          onClick={() => tap(cid, scope)}>{icon(name, v === "primary" ? "w" : "k")}</button>
      ), variant: v, w: 0 };
    }
    const labelText = child ? dyn(child.text, scope) ?? "" : "";
    return { el: (
      <button type="button" className={("a2-btn " + (cls) + (dis ? " dis" : ""))} disabled={dis}
        onClick={() => tap(cid, scope)}>{labelText}</button>
    ), variant: v, w: labelWidth(labelText) };
  };
  const buttonGroup = (kids, isRow, justify) => {
    let bs = kids.map((k) => ({ ...btn(k.id, k.scope), key: k.id + (k.scope || "") }));
    const keyed = (list) => list.map((b) => <span key={b.key} style={{ display: "contents" }}>{b.el}</span>);
    if (bs.every((b) => b.w === 0)) {
      return <div className="a2-btns" style={{ justifyContent: JUST[justify || "start"], gap: justify === "center" ? 24 : undefined }}>{keyed(bs)}</div>;
    }
    if (isRow && bs.length > 1) {
      // Side by side when every label fits, else stacked with the primary first.
      const half = (242 - 8 * (bs.length - 1)) / bs.length - 28;
      if (bs.every((b) => b.w <= half)) return <div className="a2-btns">{keyed(bs)}</div>;
      bs = [...bs].sort((x, y) => (x.variant === "primary" ? 0 : 1) - (y.variant === "primary" ? 0 : 1));
    }
    return <div className="a2-btns v">{keyed(bs)}</div>;
  };

  const field = (c, scope) => {
    const v = c.variant || "shortText";
    const raw = dyn(c.value, scope);
    const val = raw === undefined || raw === null ? "" : String(raw);
    const labelText = dyn(c.label, scope) || "";
    let errs = val ? failing(c, scope) : [];
    let bad = errs.length > 0;
    if (val && c.validationRegexp) {
      try { if (!new RegExp(c.validationRegexp).test(val)) bad = true; } catch (error) { /* an invalid pattern checks nothing */ }
    }
    const cls = { longText: "long", obscured: "pin" }[v] || "";
    const props = {
      className: ("a2-fld " + (cls) + (bad ? " bad" : "")),
      value: val,
      placeholder: labelText,
      "aria-label": labelText,
      "aria-invalid": bad || undefined,
      onChange: (event) => setBound(c.value, event.target.value, scope),
    };
    return (
      <div>
        <div className="a2-fl" hidden={!val} aria-hidden="true">{labelText}</div>
        {v === "longText" ? <textarea key="f" {...props} /> : (
          <input key="f" type={v === "obscured" ? "password" : "text"} inputMode={v === "number" ? "decimal" : undefined} {...props} />
        )}
        {errs.length ? <div className="a2-err" role="alert">{errs[0]}</div> : null}
      </div>
    );
  };

  const checkbox = (c, scope) => {
    const on = Boolean(dyn(c.value, scope));
    return (
      <button type="button" role="switch" aria-checked={on} className="a2-cb" onClick={() => setBound(c.value, !on, scope)}>
        <span>{dyn(c.label, scope)}</span>
        <span className={("a2-sw" + (on ? "" : " off"))} aria-hidden="true" />
      </button>
    );
  };

  const choice = (c, scope) => {
    const rawSel = dyn(c.value, scope);
    const sel = Array.isArray(rawSel) ? rawSel : (rawSel ? [rawSel] : []);
    const multi = c.variant === "multipleSelection";
    const labelText = c.label ? dyn(c.label, scope) : null;
    const pick = (value) => {
      const next = multi ? (sel.includes(value) ? sel.filter((x) => x !== value) : [...sel, value]) : [value];
      setBound(c.value, next, scope);
    };
    return (
      <div>
        {labelText ? <div className="a2-cl">{labelText}</div> : null}
        <div className="a2-opts" style={{ marginTop: labelText ? 2 : 0 }} role={multi ? "group" : "radiogroup"} aria-label={labelText || undefined}>
          {c.options.map((o) => {
            const on = sel.includes(o.value);
            return (
              <button type="button" key={o.value} role={multi ? "checkbox" : "radio"} aria-checked={on} className="a2-opt" onClick={() => pick(o.value)}>
                <span className={("a2-rc" + (on ? " on" : ""))} aria-hidden="true" />
                <span className="a2-ot"><span className="a2-on1">{dyn(o.label, scope)}</span></span>
              </button>
            );
          })}
        </div>
      </div>
    );
  };

  const slider = (c, scope) => {
    const lo = c.min ?? 0;
    const hi = c.max;
    const raw = Number(dyn(c.value, scope));
    const v = Number.isNaN(raw) ? lo : raw;
    const pct = Math.min(100, Math.max(0, ((v - lo) / (hi - lo)) * 100));
    const labelText = dyn(c.label, scope) || "";
    const step = hi - lo >= 10 ? 1 : (hi - lo) / 100;
    return (
      <div className="a2-sl">
        <div className="a2-slh"><span>{labelText}</span><span>{String(Number(v.toFixed(2)))}</span></div>
        <div className="a2-slt">
          <i style={{ width: ((pct.toFixed(1)) + "%") }} />
          <b style={{ left: ("calc(18.5px + (100% - 37px) * " + ((pct / 100).toFixed(3)) + ")") }} />
          <input type="range" min={lo} max={hi} step={step} value={v} aria-label={labelText}
            onChange={(event) => setBound(c.value, Number(event.target.value), scope)} />
        </div>
      </div>
    );
  };

  const datetime = (c, scope) => {
    const v = String(dyn(c.value, scope) || "");
    const labelText = dyn(c.label, scope) || "";
    const hasDate = Boolean(c.enableDate);
    const hasTime = Boolean(c.enableTime);
    const datePart = hasDate ? v.slice(0, 10) : "";
    const timeAt = hasDate ? 11 : 0;
    const timePart = hasTime ? v.slice(timeAt, timeAt + 5) : "";
    const pills = [];
    const openPicker = (event) => { try { event.currentTarget.showPicker(); } catch (error) { /* keyboard entry still works */ } };
    if (hasDate && /^\d{4}-\d{2}-\d{2}$/.test(datePart)) {
      const [y, m, d] = datePart.split("-").map(Number);
      pills.push(
        <label key="d" className="a2-pl">
          <span>{((MONTHS[m - 1]) + " " + (d) + ", " + (y))}</span>
          <input type="date" value={datePart} min={c.min ? String(c.min).slice(0, 10) : undefined} max={c.max ? String(c.max).slice(0, 10) : undefined}
            aria-label={((labelText) + ", date")} onClick={openPicker}
            onChange={(event) => event.target.value && setBound(c.value, event.target.value + v.slice(10), scope)} />
        </label>,
      );
    }
    if (hasTime && /^\d{2}:\d{2}$/.test(timePart)) {
      const h = Number(timePart.slice(0, 2));
      pills.push(
        <label key="t" className="a2-pl">
          <span>{((((h + 11) % 12) + 1) + ":" + (timePart.slice(3)) + " " + (h < 12 ? "AM" : "PM"))}</span>
          <input type="time" value={timePart} aria-label={((labelText) + ", time")} onClick={openPicker}
            onChange={(event) => event.target.value && setBound(c.value, v.slice(0, timeAt) + event.target.value + v.slice(timeAt + 5), scope)} />
        </label>,
      );
    }
    return (
      <div>
        <div className="a2-fl">{labelText}</div>
        <div className="a2-pls">{pills}</div>
      </div>
    );
  };

  // ---------- surface ----------
  const root = comps.root;
  let body = null;
  if (root && !surface.deleted) {
    const top = root.component === "Card" ? comps[root.child] : root;
    body = top && top.component === "Column" ? cardColumn(top.id, undefined, true) : (top ? block(top.id, kind(top.id)) : null);
  }
  const modal = open ? comps[open] : null;
  const modalTitle = (() => {
    const content = modal && comps[modal.content];
    const kids = content && Array.isArray(content.children) ? content.children.map((k) => comps[k]) : [];
    const heading = kids.find((k) => k && k.component === "Text" && HEAD.includes(k.variant));
    return heading ? String(dyn(heading.text) ?? "") : "Details";
  })();
  const closeSheet = () => setOpen(null);
  const reset = () => {
    setShown(messages);
    setData(applyData({}, messages));
    setTaps([]);
    setOpen(null);
    setTabs({});
    setPages({});
    setPlaying({});
    setReplied(false);
  };

  return (
    <div className="a2" role="group" aria-label={label || "Interactive card preview"}>
      <div className={("a2-frame" + (modal ? " is-sheet-open" : ""))}>
        <div className="a2-stage" aria-hidden={modal ? "true" : undefined}>
          <div className="a2-column">
            {body ? (
              <div className="a2-card">
                {body}
                <svg className="a2-tail" width="23" height="24" viewBox="0 0 23 24" aria-hidden="true" focusable="false"><path d={TAIL} /></svg>
              </div>
            ) : null}
          </div>
        </div>
        {modal ? (
          <div className="a2-sheet-layer">
            <div className="a2-dimmer" onClick={closeSheet} />
            <div className="a2-sh" role="dialog" aria-modal="true" aria-label={modalTitle}
              onKeyDown={(event) => { if (event.key === "Escape") closeSheet(); }}>
              <button type="button" className="a2-grab" autoFocus aria-label="Close" onClick={closeSheet} />
              <div className="a2-sheet-body">
                {comps[modal.content] && comps[modal.content].component === "Column"
                  ? cardColumn(modal.content, undefined, false)
                  : block(modal.content, kind(modal.content))}
              </div>
            </div>
          </div>
        ) : null}
      </div>
      {taps.length ? (
        <div className="a2-taps" role="status">
          {taps.map((message, index) => (
            <div key={index} className="a2-tap">
              <div className="a2-tap-label">{("Tap " + (index + 1) + ": your agent receives this A2UI message")}</div>
              <pre><code>{JSON.stringify(message, null, 2)}</code></pre>
            </div>
          ))}
          <div className="buttons-preview-controls">
            <button type="button" className="buttons-reset" onClick={reset}>Reset demo</button>
          </div>
        </div>
      ) : null}
    </div>
  );
};
