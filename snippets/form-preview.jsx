// Native sources: scripts/interaction-preview-sources.json. The request is the
// guide's literal SDK example, not a second invented form contract.
export const FormPreview = ({ request, bubble }) => {
  const parts = request.message.parts;
  const partIndex = parts.findIndex((part) => part.type === "form");
  const form = parts[partIndex];
  const [answers, setAnswers] = useState({});
  const [sent, setSent] = useState(false);
  const [open, setOpen] = useState(false);
  const [step, setStep] = useState(form.splash ? -1 : 0);
  const [openDate, setOpenDate] = useState(null);
  const [month, setMonth] = useState("");
  const [bubbleLayout, setBubbleLayout] = useState({ width: 276, measure: null });
  const transcript = useRef(null);
  const dialog = useRef(null);
  useEffect(() => {
    const canvas = document.createElement("canvas").getContext("2d");
    const measure = (text, kind) => {
      canvas.font = `${kind === "title" ? "600 15" : "400 13"}px -apple-system, BlinkMacSystemFont, "SF Pro Text", system-ui, sans-serif`;
      return canvas.measureText(text).width;
    };
    const observer = new ResizeObserver(([entry]) => setBubbleLayout({
      width: Math.max(40, Math.min(350, entry.target.getBoundingClientRect().width - 126)),
      measure,
    }));
    if (transcript.current) observer.observe(transcript.current);
    return () => observer.disconnect();
  }, []);
  useEffect(() => {
    if (open && dialog.current && !dialog.current.open) dialog.current.showModal();
    if (!open && dialog.current?.open) dialog.current.close();
  }, [open]);
  const summary = sent || step === form.pages.length;
  const page = form.pages[step];
  const fields = form.pages.flatMap((item) => item.fields);
  const put = (id, value) => setAnswers((previous) => ({ ...previous, [id]: value }));
  const accepts = (field) => {
    const value = answers[field.id];
    if (value === undefined || value === "" || (Array.isArray(value) && !value.length)) return !field.required;
    if (field.type === "select" || field.type === "picker") {
      const values = Array.isArray(value) ? value : [value];
      return values.every((v) => field.options.some((option) => option.value === v));
    }
    if (field.type === "date") return /^\d{4}-\d{2}-\d{2}$/.test(value)
      && value >= (field.min_date || "1900-01-01") && value <= (field.max_date || "2100-12-31")
      && new Date(value + "T12:00:00Z").toISOString().slice(0, 10) === value;
    return (!field.required || value.trim().length > 0)
      && (field.multiline || !/[\r\n]/.test(value))
      && [...value].length <= (field.max_length || (field.multiline ? 300 : 30))
      && (field.keyboard !== "email" || /^(?!\.)(?!.*\.\.)([A-Za-z0-9_'+\-.]*)[A-Za-z0-9_+-]@([A-Za-z0-9][A-Za-z0-9-]*\.)+[A-Za-z]{2,}$/.test(value))
      && (field.keyboard !== "phone" || /^\+[1-9][0-9]{1,14}$/.test(value));
  };
  const cap = (field, value) => {
    if (field.keyboard === "phone") value = value.replace(/[ \-\.()\u00a0]/g, "");
    let kept = "";
    for (const { segment } of new Intl.Segmenter(undefined, { granularity: "grapheme" }).segment(value)) {
      if ([...(kept + segment)].length > (field.max_length || (field.multiline ? 300 : 30))) break;
      kept += segment;
    }
    return kept;
  };
  const display = (field) => {
    const value = answers[field.id];
    if (value === undefined || value === "" || (Array.isArray(value) && !value.length)) return null;
    if (field.options) return field.options.filter((o) => Array.isArray(value) ? value.includes(o.value) : value === o.value).map((o) => o.label).join(", ");
    if (field.type === "date") return new Date(value + "T12:00:00").toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
    return value;
  };
  const choose = (field, option) => {
    if (!field.multiple) return put(field.id, answers[field.id] === option.value ? "" : option.value);
    const chosen = new Set(answers[field.id] || []);
    if (chosen.has(option.value)) chosen.delete(option.value); else chosen.add(option.value);
    put(field.id, field.options.filter((o) => chosen.has(o.value)).map((o) => o.value));
  };
  const showCalendar = (field) => {
    setOpenDate(openDate === field.id ? null : field.id);
    const today = new Date();
    const localDay = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;
    const min = field.min_date || "1900-01-01", max = field.max_date || "2100-12-31";
    setMonth((answers[field.id] || (localDay < min ? min : localDay > max ? max : localDay)).slice(0, 7));
  };
  const calendar = (field) => {
    const date = new Date(month + "-01T12:00:00");
    const start = date.getDay();
    const days = new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
    const shift = (delta) => {
      const next = new Date(date.getFullYear(), date.getMonth() + delta, 1, 12);
      return `${next.getFullYear()}-${String(next.getMonth() + 1).padStart(2, "0")}`;
    };
    return <div className="form-calendar" role="group" aria-label={`${field.label} calendar`}>
      <div className="form-calendar-heading">
        <strong>{date.toLocaleDateString("en-US", { month: "long", year: "numeric" })}</strong>
        <button type="button" aria-label="Previous month" disabled={shift(-1) < (field.min_date || "1900-01-01").slice(0, 7)} onClick={() => setMonth(shift(-1))}>‹</button>
        <button type="button" aria-label="Next month" disabled={shift(1) > (field.max_date || "2100-12-31").slice(0, 7)} onClick={() => setMonth(shift(1))}>›</button>
      </div>
      <div className="form-calendar-grid">
        {["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"].map((day) => <span key={day} aria-hidden="true">{day}</span>)}
        {Array.from({ length: start }, (_, i) => <span key={`empty-${i}`} />)}
        {Array.from({ length: days }, (_, i) => {
          const value = month + "-" + String(i + 1).padStart(2, "0");
          return <button type="button" key={value} aria-label={value} aria-pressed={answers[field.id] === value}
            disabled={value < (field.min_date || "1900-01-01") || value > (field.max_date || "2100-12-31")}
            onClick={() => put(field.id, value)}>{i + 1}</button>;
        })}
      </div>
    </div>;
  };
  const title = sent ? "Form sent" : summary ? "Summary" : step === -1 ? form.splash.title || form.title : page.title;
  const canAdvance = step === -1 || (summary ? fields : page.fields).every(accepts);
  const sendStep = summary || (step === form.pages.length - 1 && !form.show_summary);
  const response = {
    parts: [{ type: "text", value: "Form sent" }, { type: "form_response", answers }],
    reply_to: { message_id: "01993d50-ef7b-7b37-886b-23fd80c7ec13", part_index: partIndex },
  };
  return (
    <Frame className="relay-preview" caption="Interactive web preview. Answers stay in this page.">
      <div className="native-preview form-preview" role="group" aria-label="Interactive form preview">
        <div className="native-transcript" ref={transcript}>
          {parts.filter((part) => part.type === "text").map((part, index) => <div key={index} className="native-text">{part.value}</div>)}
          <button type="button" className="native-form-prompt" aria-haspopup="dialog" onClick={() => setOpen(true)} aria-label={`Open ${form.received_message?.title || form.title}`}>
            {bubble({ rows: [{ kind: "title", text: form.received_message?.title || form.title }, { kind: "subtitle", text: sent ? "Form sent" : form.received_message?.subtitle ?? "Open form" }], side: "leading", chevron: true, ...bubbleLayout })}
          </button>
          {sent ? <button type="button" className="native-form-answer" aria-haspopup="dialog" onClick={() => setOpen(true)} aria-label="Review sent form">
            {bubble({ rows: [{ kind: "title", text: "Form sent" }, { kind: "subtitle", text: form.reply_message?.subtitle ?? "Tap to view answers" }], side: "trailing", chevron: true, ...bubbleLayout })}
          </button> : null}
        </div>
        {sent ? <>
          <button type="button" className="relay-preview-reset" aria-label="Reset demo" onClick={() => { setAnswers({}); setSent(false); setStep(form.splash ? -1 : 0); setOpenDate(null); }}><Icon icon="rotate-left" size={16} /></button>
          <details className="native-response"><summary>Reply data (local preview)</summary><pre>{JSON.stringify(response, null, 2)}</pre></details>
        </> : null}
        <dialog ref={dialog} className="native-dialog native-form-sheet" aria-label={title} onClose={() => setOpen(false)}>
          <div className="native-grabber" aria-hidden="true" />
          <div className="native-sheet-bar">
            {!sent && step > (form.splash ? -1 : 0) ? <button type="button" className="native-back" aria-label="Back" onClick={() => { setStep(step - 1); setOpenDate(null); }}>‹</button> : <span />}
            <strong>{title}</strong>
            <button type="button" aria-label="Close form" onClick={() => { if (!sent && step === form.pages.length) setStep(form.pages.length - 1); setOpen(false); setOpenDate(null); }}>×</button>
          </div>
          <div className="native-form-content" key={title}>
            {summary ? form.pages.map((item) => {
              const answered = item.fields.filter((field) => display(field) !== null);
              return answered.length ? <section key={item.id}><h3>{item.title}</h3><div className="native-field-group">{answered.map((field) => <div className="form-answer-row" key={field.id}><span>{field.label}</span><div>{display(field)}</div></div>)}</div></section> : null;
            }) : step === -1 ? <div className="native-field-group form-intro">{form.splash.text}</div> : page.fields.map((field) => (
              <section key={field.id}>
                {(field.type === "text" || field.type === "select" || !field.required) ? <h3><span>{field.type === "text" || field.type === "select" ? field.label : ""}</span>{!field.required ? <span>Optional</span> : null}</h3> : null}
                <div className="native-field-group">
                  {field.type === "text" ? field.multiline ? <textarea aria-label={field.label} aria-required={!!field.required} rows={3} placeholder={field.placeholder || ""} value={answers[field.id] || ""} onChange={(e) => put(field.id, cap(field, e.target.value))} /> : <input aria-label={field.label} aria-required={!!field.required} inputMode={{ email: "email", phone: "tel", number: "decimal", url: "url" }[field.keyboard] || "text"} placeholder={field.placeholder || ""} value={answers[field.id] || ""} onChange={(e) => put(field.id, cap(field, e.target.value))} /> : null}
                  {field.type === "picker" ? <label className="form-picker">{field.label}<select aria-label={field.label} aria-required={!!field.required} value={answers[field.id] || ""} onChange={(e) => put(field.id, e.target.value)}><option value="">{field.placeholder || ""}</option>{field.options.map((o) => <option value={o.value} key={o.value}>{o.label}</option>)}</select></label> : null}
                  {field.type === "select" ? field.options.map((option) => {
                    const chosen = field.multiple ? (answers[field.id] || []).includes(option.value) : answers[field.id] === option.value;
                    const toggle = field.multiple && field.options.length === 1;
                    return <button type="button" className="form-choice" key={option.value}
                      role={toggle ? "switch" : undefined} aria-checked={toggle ? chosen : undefined}
                      aria-pressed={toggle ? undefined : chosen} onClick={() => choose(field, option)}>
                      <span>{option.label}</span>{toggle ? <span className={"form-switch" + (chosen ? " is-on" : "")} aria-hidden="true"><span /></span> : <span className="form-check" aria-hidden="true">{chosen ? "✓" : ""}</span>}
                    </button>;
                  }) : null}
                  {field.type === "date" ? <>
                    <button type="button" className="form-date" aria-label={`${field.label}, ${display(field) || "Choose date"}`} aria-expanded={openDate === field.id} onClick={() => showCalendar(field)}><span>{field.label}</span><span>{display(field) || "Choose date"}</span></button>
                    {openDate === field.id ? calendar(field) : null}
                    {answers[field.id] && !field.required ? <button type="button" className="form-clear-date" onClick={() => { put(field.id, ""); setOpenDate(null); }}>Clear Date</button> : null}
                  </> : null}
                </div>
                {field.type === "text" && answers[field.id] && !accepts(field) ? <p className="form-hint" role="status">{field.keyboard === "phone" ? "Enter the number with its country code, starting with +." : field.keyboard === "email" ? "Enter an email address." : "Enter a valid answer."}</p> : null}
              </section>
            ))}
          </div>
          {!sent ? <div className="native-form-bottom"><button type="button" className="native-capsule is-primary" disabled={!canAdvance}
            onClick={() => { if (!canAdvance) return; if (sendStep) { setSent(true); setOpen(false); } else setStep(step + 1); setOpenDate(null); }}>
            {step === -1 ? form.splash.button_title : sendStep ? "Send" : "Next"}
          </button></div> : null}
        </dialog>
      </div>
    </Frame>
  );
};
