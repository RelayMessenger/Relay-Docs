// Native sources and fixture provenance: scripts/interaction-preview-sources.json.
// This is an interactive documentation example, not a captured app screen.
export const RichCardPreview = ({ request, bubble }) => {
  const [replies, setReplies] = useState([]);
  const [opened, setOpened] = useState(null);
  const dialog = useRef(null);
  const shelf = useRef(null);
  const parts = request.message.parts;
  const partIndex = parts.findIndex((part) => part.type === "rich_card" || part.type === "carousel");
  const part = parts[partIndex];
  const cards = part.type === "carousel" ? part.cards : [part];
  // The same illustrative photographs used by the existing native card lab.
  // The example.com URLs in the wire examples are never fetched.
  const photos = ["/images/interactions/lagoon.jpg", "/images/interactions/cliffside.jpg"];
  useEffect(() => {
    if (opened && dialog.current && !dialog.current.open) dialog.current.showModal();
    if (!opened && dialog.current?.open) dialog.current.close();
  }, [opened]);
  const reply = (suggestion) => setReplies((previous) => [...previous, {
    parts: [
      { type: "text", value: suggestion.label },
      { type: "suggestion_response", id: suggestion.id, label: suggestion.label },
    ],
    reply_to: { message_id: "01993d50-ef7b-7b37-886b-23fd80c7ec13", part_index: partIndex },
  }]);
  return (
    <Frame className="relay-preview" caption="Interactive web preview. Sample photos; actions stay in this page.">
      <div className="native-preview rich-preview" role="group" aria-label={part.type === "carousel" ? "Interactive carousel preview" : "Interactive rich card preview"}>
        <div className="native-transcript">
          {parts.filter((item) => item.type === "text").map((item, index) => (
            <div className="native-text" key={index}>{item.value}</div>
          ))}
          <div className={"rich-shelf" + (part.type === "carousel" ? " is-carousel" : "")}
            ref={shelf} tabIndex={part.type === "carousel" ? 0 : undefined}
            role={part.type === "carousel" ? "region" : undefined}
            aria-label={part.type === "carousel" ? "Cards, scroll sideways to compare" : undefined}>
            {cards.map((card, index) => (
              <div className={"rich-balloon" + (part.card_width === "small" ? " is-small" : "")} key={index}>
                <div className="rich-card">
                  {card.media ? (
                    <button className="rich-media" type="button"
                      style={{ height: { short: 112, medium: 168, tall: 264 }[card.media.height || "medium"] }}
                      aria-label={`Open sample photo for ${card.title || "card"}`}
                      onClick={() => setOpened({ photo: photos[index], title: card.title })}>
                      <img src={photos[index]} alt="" />
                    </button>
                  ) : null}
                  <div className="rich-copy">
                    {card.title ? <div className="rich-title">{card.title}</div> : null}
                    {card.description ? <div className="rich-description">{card.description}</div> : null}
                  </div>
                  <div className="rich-suggestions">
                    {card.suggestions.map((suggestion, i) => (
                      <button type="button" key={i} className={"native-capsule" + (i === 0 ? " is-primary" : "")}
                        onClick={() => suggestion.type === "reply" ? reply(suggestion) : setOpened({ url: suggestion.url })}>
                        {suggestion.label}{suggestion.type === "open_url" ? <span aria-hidden="true"> ↗</span> : null}
                      </button>
                    ))}
                  </div>
                </div>
                {part.type !== "carousel" ? <svg className="native-tail" viewBox="0 0 23 24" aria-hidden="true"><path d="M0 0C0 .306 1.415 4.498 4.028 7.924C5.087 9.312 6.309 10.536 7.66 11.577C9.585 13.078 10.418 14.644 10.418 16.404C10.418 17.587 10.209 18.756 8.51 20.988C7.695 22.058 8.513 23.15 9.787 22.666C12.407 21.672 15.391 19.86 18.005 17.927C20.347 16.195 20.971 16.02 22.07 16.013L22.07 0Z" /></svg> : null}
              </div>
            ))}
          </div>
          {part.type === "carousel" ? <div className="rich-scroll-controls">
            <button type="button" aria-label="Previous card" onClick={() => shelf.current.scrollBy({ left: -shelf.current.clientWidth, behavior: "auto" })}>‹</button>
            <button type="button" aria-label="Next card" onClick={() => shelf.current.scrollBy({ left: shelf.current.clientWidth, behavior: "auto" })}>›</button>
          </div> : null}
          {replies.length === 0 ? parts.filter((item) => item.type === "buttons").map((item, index) => (
            <div className="rich-followups" key={index}>{item.items.map((button, i) => (
              <button className="native-capsule" type="button" key={i}
                onClick={() => setReplies([{ parts: [{ type: "text", value: button.label }] }])}>{button.label}</button>
            ))}</div>
          )) : null}
          <div className="native-replies" aria-live="polite">
            {replies.map((response, index) => <div className="buttons-reply" key={index} aria-label={`Reply: ${response.parts[0].value}`}>{bubble({ text: response.parts[0].value })}</div>)}
          </div>
        </div>
        {replies.length ? <>
          <button type="button" className="relay-preview-reset" aria-label="Reset demo" onClick={() => { setReplies([]); if (shelf.current) shelf.current.scrollLeft = 0; }}><Icon icon="rotate-left" size={16} /></button>
          <details className="native-response"><summary>Reply data (local preview)</summary><pre>{JSON.stringify(replies[replies.length - 1], null, 2)}</pre></details>
        </> : null}
        <dialog ref={dialog} className={"native-dialog" + (opened?.photo ? " is-photo" : "")} aria-label={opened?.photo ? "Sample photo" : "In-app browser preview"} onClose={() => setOpened(null)}>
          <div className="native-sheet-bar"><span>{opened?.photo ? opened.title : "In-app browser preview"}</span><button type="button" aria-label="Close" onClick={() => setOpened(null)}>×</button></div>
          {opened?.photo ? <img className="rich-photo" src={opened.photo} alt={`Sample photo for ${opened.title}`} /> : <div className="rich-url"><strong>{opened?.url}</strong><p>The app opens the page in its browser. This preview does not navigate or send a reply.</p></div>}
        </dialog>
      </div>
    </Frame>
  );
};
