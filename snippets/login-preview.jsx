// The Log in with Relay screens, drawn the way Relay draws them on
// 2026-10-02: the Connect Relay button from relay-login.js, Relay's account
// page on auth.relayapp.im ("Choose an account"), the confirmation the Relay
// app shows as a sheet (and Relay's page shows on a computer), and the
// "Logged in" sheet. The docs show mockups, never screenshots (owner,
// 2026-09-11 and 2026-10-02). Like the other previews, the frame carries no
// status bar: the screen sits in a 402pt column centred in the frame.
//
// Local-only. No API, analytics, or credentials. The switches turn on and
// off in place, email turned on as Ana did in the real capture; on is Relay's primary blue (owner: every toggle is primary).
export const LoginPreview = ({ screen, device = "iphone", label }) => {
  // Everything lives inside the component: the snippet is compiled as MDX,
  // which keeps only exports in scope.
  const SITE = "acme.com";
  const AGENT = "Acme";
  const [shared, setShared] = useState({ email: true, phone: false, birthday: false });

  // Relay's mark (Relay-Auth public/brand/relay-mark.svg): the speech
  // balloon with two smiling eyes knocked out.
  const mark = (size) => (
    <svg width={size} height={size} viewBox="210 185 644 700" aria-hidden="true" focusable="false">
      <path fill="currentColor" fillRule="evenodd"
        d="M512 185C701 185 854 314 854 475C854 656 695 827 523 827C493 827 467 824 446 815C369 861 302 883 284 865C268 848 300 773 317 720C246 665 210 582 210 484C210 319 344 185 512 185Z" />
      <path d="M372 514C372 470 408 434 452 434C496 434 532 470 532 514M600 514C600 470 636 434 680 434C724 434 760 470 760 514"
        fill="none" stroke="var(--login-eye)" strokeWidth="48" strokeLinecap="round" />
    </svg>
  );
  const close = (
    <span className="login-close" aria-hidden="true">
      <svg viewBox="0 0 16 16" focusable="false"><path d="M3 3l10 10M13 3L3 13" /></svg>
    </span>
  );
  const icons = {
    email: <path d="M2.5 5.5h15v10h-15zM2.5 5.5l7.5 6 7.5-6" />,
    phone: <path d="M5 2.8l2.6.2 1.3 3.4-1.7 1.3c.9 2 2.4 3.6 4.4 4.6l1.4-1.7 3.3 1.4.2 2.6c-.1.9-.8 1.6-1.7 1.6C8.9 16 4.2 11.3 4 5.5c0-.9.6-1.8 1-2.7z" />,
    birthday: <path d="M10 2.5c.9 1 .9 2 0 2.7-.9-.7-.9-1.7 0-2.7zM10 5.5v2.5M5 8h10v3H5zM3.5 11h13v5.5h-13zM3.5 13.5c1.6 1 3.3 1 5 0 1.7 1 3.3 1 5 0 1 .6 2 .8 3 .6" />,
  };
  const rows = [
    { key: "email", text: "ana@example.com", name: "email" },
    { key: "phone", text: "+1 313-555-0142", name: "phone number" },
    { key: "birthday", text: "March 22, 2004", name: "birthday" },
  ];

  const confirmation = (
    <div className={"login-sheet" + (device === "computer" ? " is-computer" : "")}>
      <div className="login-head">
        {close}
        <div className="login-title">Log in to {SITE}</div>
      </div>
      <div className="login-tile" aria-hidden="true">A</div>
      <p className="login-body">{AGENT} will get your name, @handle and photo. Its agent can message you in Relay.</p>
      <div className="login-device">
        <svg viewBox="0 0 22 16" aria-hidden="true" focusable="false"><path d="M4 2.5h14v9H4zM1.5 13.5h19" /></svg>
        Chrome on Mac · Detroit, MI
      </div>
      <div className="login-section">Share with {SITE}</div>
      <div className="login-list">
        {rows.map((row) => (
          <div className="login-row" key={row.key}>
            <svg className="login-row-icon" viewBox="0 0 20 20" aria-hidden="true" focusable="false">{icons[row.key]}</svg>
            <span className="login-row-text">{row.text}</span>
            <button type="button" role="switch" aria-checked={shared[row.key]} aria-label={`Share ${row.name}`}
              className="login-switch" onClick={() => setShared({ ...shared, [row.key]: !shared[row.key] })}>
              <span />
            </button>
          </div>
        ))}
      </div>
      <div className="login-spacer" />
      <div className="login-primary is-narrow">Log in</div>
    </div>
  );

  const screens = {
    button: {
      spoken: "The Connect Relay button",
      body: (
        <div className="login-center">
          <div className="login-primary is-button">{mark(22)}Connect Relay</div>
        </div>
      ),
    },
    choose: {
      spoken: `Relay's page: Choose an account to log in to ${SITE}, with Ana Lopez selected and Continue with Relay`,
      body: (
        <div className="login-page">
          <div className="login-pair" aria-hidden="true">
            <span className="login-pair-relay">{mark(34)}</span>
            <span className="login-pair-site">A</span>
          </div>
          <div className="login-heading">Choose an account</div>
          <div className="login-sub">to log in to <span className="login-link">{SITE}</span></div>
          <div className="login-accounts">
            <div className="login-account">
              <span className="login-avatar" aria-hidden="true">AL</span>
              <span className="login-account-name">Ana Lopez</span>
              <span className="login-radio" aria-hidden="true" />
            </div>
            <div className="login-account is-add">
              <span className="login-plus" aria-hidden="true">+</span>
              <span className="login-link">Use another account</span>
            </div>
          </div>
          <div className="login-primary is-wide">{mark(18)}Continue with Relay</div>
        </div>
      ),
    },
    confirm: {
      spoken: device === "computer"
        ? `Relay's page on a computer: Log in to ${SITE}, with switches to share email, phone number and birthday, and a Log in button`
        : `The Relay app's confirmation: Log in to ${SITE}, with switches to share email, phone number and birthday`,
      body: confirmation,
    },
    done: {
      spoken: `The Relay app: Logged in to ${SITE}`,
      body: (
        <div className="login-sheet is-done">
          <div className="login-head">{close}</div>
          <div className="login-done">
            <span className="login-check" aria-hidden="true">
              <svg viewBox="0 0 24 24" focusable="false"><path d="M5 12.5l4.5 5L19 6" /></svg>
            </span>
            <div className="login-title">Logged in to {SITE}</div>
          </div>
        </div>
      ),
    },
  };
  const current = screens[screen];

  return (
    <Frame className="relay-preview">
    <div className="login-preview" role="group" aria-label={label || current.spoken}>
      <style>{`
        .login-preview { --login-font: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Inter", system-ui, sans-serif;
          --login-blue: #0b75ff; --login-eye: #0b75ff; --login-ground: #f2f2f7; --login-card: #ffffff; --login-line: #d1d1d6;
          --login-muted: #8a8a8e; --login-off: #e3e3e8; --login-chip: #ffffff;
          font-family: var(--login-font); color: #000000; }
        .dark .login-preview { --login-blue: #007eff; --login-eye: #007eff; --login-ground: #1c1c1e; --login-card: #2c2c2e;
          --login-line: #3a3a3c; --login-muted: #8d8d92; --login-off: #5b5b5f; --login-chip: #3a3a3c; color: #ffffff; }
        .login-stage { box-sizing: border-box; max-width: 402px; margin: 0 auto; padding: 16px; }
        .login-center { display: flex; justify-content: center; padding: 8px 0; }
        .login-primary { display: flex; align-items: center; justify-content: center; gap: 10px; box-sizing: border-box;
          border-radius: 999px; background: var(--login-blue); color: #ffffff; font-weight: 600; white-space: nowrap; }
        .login-primary.is-button { height: 40px; padding: 0 18px; font-size: 17px; }
        .login-primary.is-wide { height: 46px; font-size: 16px; }
        .login-primary.is-narrow { align-self: center; width: 62%; height: 50px; font-size: 17px; }
        .login-page { display: flex; flex-direction: column; align-items: stretch; padding: 4px 8px 8px; }
        .login-pair { display: flex; justify-content: center; margin-bottom: 18px; }
        .login-pair > span { display: flex; width: 64px; height: 64px; border-radius: 50%; align-items: center; justify-content: center; }
        .login-pair-relay { background: var(--login-blue); color: #ffffff; }
        .login-pair-site { margin-left: -12px; background: #157347; color: #ffffff; font-size: 30px; font-weight: 600;
          box-shadow: 0 0 0 2px var(--login-pair-ring, #ffffff); }
        .dark .login-pair-site { --login-pair-ring: #000000; }
        .login-heading { text-align: center; font-size: 22px; font-weight: 700; }
        .login-sub { margin-top: 6px; text-align: center; font-size: 15px; color: var(--login-muted); }
        .login-link { color: var(--login-blue); }
        .login-accounts { margin: 24px 0 20px; padding: 6px 0; border-radius: 16px; background: var(--login-ground); }
        .login-account { display: flex; align-items: center; gap: 12px; padding: 10px 16px; font-size: 16px; }
        .login-avatar { display: flex; flex: none; width: 32px; height: 32px; border-radius: 50%; align-items: center; justify-content: center;
          background: #2f6fde; color: #ffffff; font-size: 12px; font-weight: 600; }
        .login-account-name { flex: 1; }
        .login-radio { flex: none; width: 14px; height: 14px; border-radius: 50%; border: 2px solid var(--login-blue);
          background: var(--login-blue); box-shadow: inset 0 0 0 3px var(--login-ground); }
        .login-plus { display: flex; flex: none; width: 32px; justify-content: center; color: var(--login-blue); font-size: 22px; line-height: 1; }
        .login-sheet { display: flex; flex-direction: column; box-sizing: border-box; min-height: 600px; padding: 14px 16px 24px;
          border-radius: 34px; background: var(--login-ground); }
        .login-sheet.is-computer { min-height: 0; }
        .login-sheet.is-computer .login-spacer { flex: none; height: 20px; }
        .login-sheet.is-done { min-height: 360px; background: var(--login-card); box-shadow: inset 0 0 0 1px var(--login-line); }
        .login-head { position: relative; display: flex; align-items: center; justify-content: center; min-height: 40px; }
        .login-close { position: absolute; left: 0; top: 0; display: flex; width: 40px; height: 40px; border-radius: 50%;
          align-items: center; justify-content: center; background: var(--login-chip); box-shadow: 0 1px 4px rgba(0, 0, 0, .08); }
        .login-close svg { width: 16px; height: 16px; fill: none; stroke: currentColor; stroke-width: 1.8; stroke-linecap: round; }
        .login-title { font-size: 17px; font-weight: 600; }
        .login-tile { align-self: center; display: flex; width: 80px; height: 80px; margin: 22px 0 14px; border-radius: 20px;
          align-items: center; justify-content: center; background: #157347; color: #ffffff; font-size: 34px; font-weight: 600; }
        .login-body { margin: 0; padding: 0 12px; text-align: center; font-size: 16px; line-height: 1.35; }
        .login-device { display: flex; align-items: center; justify-content: center; gap: 8px; margin: 16px 0 26px;
          color: var(--login-muted); font-size: 14px; }
        .login-device svg { width: 22px; height: 16px; fill: none; stroke: currentColor; stroke-width: 1.3; }
        .login-section { padding: 0 16px 8px; color: var(--login-muted); font-size: 15px; font-weight: 600; }
        .login-list { border-radius: 22px; background: var(--login-card); }
        .login-row { display: flex; align-items: center; gap: 12px; min-height: 48px; padding: 0 14px; }
        .login-row + .login-row { box-shadow: inset 0 0.5px 0 var(--login-line); }
        .login-row-icon { flex: none; width: 22px; height: 22px; fill: none; stroke: currentColor; stroke-width: 1.3; stroke-linejoin: round; }
        .login-row-text { flex: 1; font-size: 16px; }
        .login-switch { position: relative; flex: none; width: 60px; height: 28px; margin: 0; padding: 0; border: 0; border-radius: 14px;
          background: var(--login-off); cursor: pointer; transition: background .2s ease-out; }
        .login-switch > span { position: absolute; top: 2px; left: 2px; width: 36px; height: 24px; border-radius: 12px;
          background: #ffffff; box-shadow: 0 1px 3px rgba(0, 0, 0, .2); transition: transform .2s ease-out; }
        .login-switch[aria-checked="true"] { background: var(--login-blue); }
        .login-switch[aria-checked="true"] > span { transform: translateX(20px); }
        .login-switch:focus-visible { outline: 2px solid var(--login-blue); outline-offset: 2px; }
        .login-spacer { flex: 1; min-height: 24px; }
        .login-done { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 16px; padding-bottom: 40px; }
        .login-check { display: flex; width: 72px; height: 72px; border-radius: 50%; align-items: center; justify-content: center;
          background: var(--login-card); box-shadow: 0 0 0 1px var(--login-line), 0 4px 12px rgba(0, 0, 0, .08); }
        .login-check svg { width: 30px; height: 30px; fill: none; stroke: currentColor; stroke-width: 2.6; stroke-linecap: round; stroke-linejoin: round; }
        @media (prefers-reduced-motion: reduce) {
          .login-switch, .login-switch > span { transition: none; }
        }
      `}</style>
      <div className="login-stage">{current.body}</div>
    </div>
    </Frame>
  );
};
