// A rendered buttons part, drawn the way the app draws it: a vertical stack of
// pills under the message, a link button marked with an arrow. Styles live in
// style.css under .buttons-preview so light and dark follow the site theme.
export const ButtonsPreview = ({ items, tapped, caption }) => (
  <div className="buttons-preview" role="img" aria-label={caption}>
    <div className="buttons-preview-stage">
      {tapped ? (
        <div className="buttons-preview-tap">{tapped}</div>
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
    {caption ? <div className="buttons-preview-caption">{caption}</div> : null}
  </div>
);
