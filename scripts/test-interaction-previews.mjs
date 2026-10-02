import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";
import { createHash } from "node:crypto";
import vm from "node:vm";
import { transform } from "sucrase";
import YAML from "yaml";
import Ajv from "ajv/dist/2020.js";
import addFormats from "ajv-formats";

const read = (path) => readFileSync(new URL("../" + path, import.meta.url), "utf8");
const examples = JSON.parse(read("snippets/interaction-examples.jsx").split("=> (")[1].split(");\n")[0]);
const schemas = YAML.parse(read("api-reference/openapi.yaml")).components.schemas;
const ajv = new Ajv({ strict: false, allErrors: true });
addFormats(ajv);
const validate = (name, value) => {
  const check = ajv.compile({ components: { schemas }, $ref: "#/components/schemas/" + name });
  assert.ok(check(value), JSON.stringify(check.errors));
};

// Execute the actual snippet and handlers, not a second copy of their logic.
// Browser focus/dialog/geometry remain covered by the T3-rendered check.
function mount(file, name, props) {
  const state = [];
  let cursor = 0;
  const context = {
    exports: {}, Frame: "Frame", Icon: "Icon", Intl, Date, Set,
    React: { createElement: (type, props, ...children) => ({ type, props: props || {}, children: children.flat(Infinity) }) },
    useState: (initial) => {
      const index = cursor++;
      if (!(index in state)) state[index] = initial;
      return [state[index], (value) => { state[index] = typeof value === "function" ? value(state[index]) : value; }];
    },
    useRef: () => ({ current: null }), useEffect: () => {},
  };
  vm.runInNewContext(transform(read(file), { transforms: ["jsx", "imports"] }).code, context);
  const render = () => { cursor = 0; return context.exports[name](props); };
  return { render };
}
function nodes(tree, predicate) {
  if (!tree || typeof tree !== "object") return [];
  return [...(predicate(tree) ? [tree] : []), ...(tree.children || []).flatMap((child) => nodes(child, predicate))];
}
const text = (node) => typeof node === "string" || typeof node === "number" ? String(node) : (node?.children || []).map(text).join("");
const find = (app, predicate) => {
  const result = nodes(app.render(), predicate)[0];
  assert.ok(result, "Expected rendered control");
  return result;
};
const button = (app, label) => find(app, (n) => n.type === "button" && (n.props["aria-label"] === label || text(n) === label));
const click = (app, label) => {
  const control = button(app, label);
  assert.ok(!control.props.disabled, label + " must be enabled");
  control.props.onClick();
};
const input = (app, label, value) => find(app, (n) => ["input", "textarea", "select"].includes(n.type) && n.props["aria-label"] === label).props.onChange({ target: { value } });
const bubble = (props) => ({ type: "Bubble", props, children: [] });

test("live fixtures use the exact guide payloads and the current schemas", () => {
  validate("RichCardPart", examples.card.message.parts[1]);
  validate("CarouselPart", examples.carousel.message.parts[1]);
  validate("FormPart", examples.form.message.parts[1]);
  if (process.env.RELAY_OPENAPI_SOURCE) {
    const current = YAML.parse(readFileSync(process.env.RELAY_OPENAPI_SOURCE, "utf8")).components.schemas;
    for (const name of Object.keys(schemas).filter((name) => /^(Form|RichCard|Carousel|Suggestion)/.test(name))) {
      assert.deepEqual(schemas[name], current[name], `${name} drifted from current Server staging`);
    }
  }
});

test("rich card replies retain suggestion ID and source part, allow repeat taps, and reset", () => {
  const app = mount("snippets/rich-card-preview.jsx", "RichCardPreview", { request: examples.card, bubble });
  click(app, "Book");
  click(app, "Book");
  assert.equal(nodes(app.render(), (n) => n.type === "Bubble").length, 2);
  const response = JSON.parse(text(find(app, (n) => n.type === "pre")));
  assert.equal(response.parts[1].id, "book_lagoon");
  assert.equal(response.reply_to.part_index, 1);
  validate("SuggestionResponsePartResponse", response.parts[1]);
  click(app, "Reset demo");
  assert.equal(nodes(app.render(), (n) => n.type === "Bubble").length, 0);
});

test("URL and photo taps never invent a reply; carousel replies name the chosen card", () => {
  const app = mount("snippets/rich-card-preview.jsx", "RichCardPreview", { request: examples.card, bubble });
  click(app, "Details ↗");
  assert.equal(nodes(app.render(), (n) => n.type === "Bubble").length, 0);
  click(app, "Close");
  click(app, "Open sample photo for Lagoon House, Railay");
  assert.equal(nodes(app.render(), (n) => n.type === "Bubble").length, 0);
  const carousel = mount("snippets/rich-card-preview.jsx", "RichCardPreview", { request: examples.carousel, bubble });
  nodes(carousel.render(), (n) => n.type === "button" && text(n) === "Book")[1].props.onClick();
  const response = JSON.parse(text(find(carousel, (n) => n.type === "pre")));
  assert.equal(response.parts[1].id, "book_cliffside");
  assert.equal(nodes(carousel.render(), (n) => n.props.className === "rich-followups").length, 0);
});

test("form: required fields, back/close draft, ordered multi-select, date, summary, send and read-only reopen", () => {
  const app = mount("snippets/form-preview.jsx", "FormPreview", { request: examples.form, bubble });
  click(app, "Open Visit details");
  click(app, "Continue");
  assert.equal(button(app, "Next").props.disabled, true);
  input(app, "Name", "   ");
  click(app, "Vegetarian");
  assert.equal(button(app, "Next").props.disabled, true);
  input(app, "Name", "Ada");
  click(app, "Cake");
  click(app, "Tea");
  click(app, "Next");
  click(app, "Back");
  assert.equal(find(app, (n) => n.type === "input").props.value, "Ada");
  click(app, "Next");
  click(app, "Close form");
  click(app, "Open Visit details");
  assert.ok(button(app, "Visit date, Choose date"));
  input(app, "Region", "east");
  click(app, "Visit date, Choose date");
  // Opening a calendar must not fill the required answer.
  assert.equal(button(app, "Next").props.disabled, true);
  // Month is clamped to the fixture range, even after the example's year.
  while (!nodes(app.render(), (n) => n.props["aria-label"] === "2026-10-02").length) click(app, "Previous month");
  click(app, "2026-10-02");
  assert.ok(button(app, "Visit date, Oct 2, 2026"));
  input(app, "Notes", "Window seat, please.");
  click(app, "Send me visit updates");
  click(app, "Next");
  assert.equal(text(find(app, (n) => n.type === "strong" && text(n) === "Summary")), "Summary");
  click(app, "Send");
  const response = JSON.parse(text(find(app, (n) => n.type === "pre")));
  assert.deepEqual(response.parts[0], { type: "text", value: "Form sent" });
  assert.deepEqual(response.parts[1].answers.extras, ["tea", "cake"]);
  assert.deepEqual(response.parts[1].answers.updates, ["yes"]);
  assert.equal(response.reply_to.part_index, 1);
  validate("FormResponsePart", response.parts[1]);
  click(app, "Review sent form");
  assert.equal(nodes(app.render(), (n) => ["input", "textarea", "select"].includes(n.type)).length, 0);
  assert.equal(nodes(app.render(), (n) => n.type === "button" && text(n) === "Send").length, 0);
  click(app, "Close form");
  click(app, "Reset demo");
  click(app, "Open Visit details");
  click(app, "Continue");
  assert.equal(find(app, (n) => n.type === "input").props.value, "");
});

test("form caps Unicode scalars without splitting a grapheme; instances do not share drafts", () => {
  const request = structuredClone(examples.form);
  request.message.parts[1].pages[0].fields[0].max_length = 3;
  const app = mount("snippets/form-preview.jsx", "FormPreview", { request, bubble });
  click(app, "Continue");
  input(app, "Name", "a👩‍💻z");
  assert.equal(find(app, (n) => n.type === "input").props.value, "a");
  const other = mount("snippets/form-preview.jsx", "FormPreview", { request, bubble });
  click(other, "Continue");
  assert.equal(find(other, (n) => n.type === "input").props.value, "");
});

test("native metrics, app colors and photo identities are pinned without page chrome", () => {
  const css = read("style.css");
  for (const value of ["#0b75ff", "#007eff", "#e9e9e9", "#2c2c2e", "border-radius: 18px", "min-height: 40px", "calc(100% - 94px)"]) assert.ok(css.includes(value), value);
  const sources = JSON.parse(read("scripts/interaction-preview-sources.json"));
  for (const asset of sources.assets) assert.equal(createHash("sha256").update(readFileSync(new URL("../" + asset.path, import.meta.url))).digest("hex"), asset.sha256);
  for (const name of ["form", "rich-card"]) {
    const source = read(`snippets/${name}-preview.jsx`);
    assert.ok(!/\b(fetch|XMLHttpRequest|localStorage|WebSocket)\s*[(.]/.test(source));
    assert.ok(!/A2UI|phone-header|status-bar|composer/i.test(source));
    assert.ok(source.includes("<dialog") && source.includes("showModal()"));
  }
});

test("form bubbles wrap at narrow widths and keep the existing selection geometry opt-in", () => {
  const props = { rows: [{ kind: "title", text: "Form sent" },
    { kind: "subtitle", text: "Tap to review your answers" }],
    side: "trailing", chevron: true, width: 154 };
  const baseline = mount("snippets/buttons-preview.jsx", "MessageBubble", props).render();
  const wrapped = mount("snippets/buttons-preview.jsx", "MessageBubble",
    { ...props, measure: (text) => text.length * 7 }).render();
  assert.ok(wrapped.props.height > baseline.props.height);
  const texts = nodes(wrapped, (n) => n.type === "text");
  assert.ok(texts.length > 2);
  for (const row of texts) assert.ok(text(row).length * 7 <= 110);
  const css = read("style.css");
  assert.ok(css.includes(".native-field-group:focus-within"));
  assert.ok(css.includes("outline-offset: -3px"));
  assert.ok(css.includes("fill: rgba(255,255,255,.8)"));
  assert.ok(css.includes("fill: rgba(255,255,255,.6)"));
  assert.ok(css.includes(".dark .rich-followups .native-capsule { background: #101e33; color: #6fb0ff; }"));
});
