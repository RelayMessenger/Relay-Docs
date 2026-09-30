#!/usr/bin/env python3
"""Form documentation behavior checks; no browser or API requests.

FORM_DOCS_ROOT supports isolated mutation receipts outside the published tree.
The Server contract and its tests remain the behavior authority.
"""
import datetime
import json
import os
import re
import unittest
from pathlib import Path

ROOT = Path(os.environ.get("FORM_DOCS_ROOT", Path(__file__).resolve().parents[1]))
PRODUCTION = (ROOT / ".docs-target").is_file() and (ROOT / ".docs-target").read_text().strip() == "production"
API_ORIGIN = "https://api.relayapp.im" if PRODUCTION else "https://api.staging.relayapp.im"
PAGE = "interactions/form.mdx"
TOKEN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
FENCES = re.compile(r"^```(\w+)([^\n]*)\n(.*?)^```[ \t]*$", re.M | re.S)


def read(path):
    return (ROOT / path).read_text()


def blocks():
    return list(FENCES.findall(read(PAGE)))


def request():
    code = next(code for lang, title, code in blocks() if lang == "typescript" and title.strip() == "TypeScript SDK")
    return json.JSONDecoder().raw_decode(code.split("const request = ", 1)[1])[0]


def response():
    return next(json.loads(code)["data"] for lang, _, code in blocks()
                if lang == "json" and '"event_type"' in code)


def form():
    return next(part for part in request()["message"]["parts"] if part["type"] == "form")


def fields():
    return [field for page in form()["pages"] for field in page["fields"]]


def schema(name):
    match = re.search(rf"^    {name}:\n(.*?)(?=^    \w|\Z)",
                      read("api-reference/openapi.yaml"), re.M | re.S)
    assert match, f"Missing canonical schema {name}"
    return match[1]


def prop(name, key):
    match = re.search(rf"^        {key}:[^\n]*\n(.*?)(?=^        \w|\Z)",
                      schema(name), re.M | re.S)
    assert match, f"Missing canonical property {name}.{key}"
    return match[1]


class FormDocsTests(unittest.TestCase):
    def test_navigation_and_message_parts_discover_form(self):
        nav = json.loads(read("docs.json"))
        self.assertEqual(json.dumps(nav["navigation"]).count('"interactions/form"'), 1)
        self.assertIn('<Card title="Form" href="/interactions/form">', read("interactions/index.mdx"))
        self.assertIn("/interactions/form#read-whether-someone-answered", read("messages/parts.mdx"))
        self.assertRegex(read(PAGE), r'\A---\ntitle: "Form"\ndescription: ".+"\nkeywords: \[.+\]\n---')
        self.assertIn("## Next steps\n", read(PAGE))

    def test_sdk_and_https_send_the_same_request(self):
        source = read(PAGE)
        group = re.search(r"<CodeGroup>(.*?)</CodeGroup>", source, re.S)[1]
        self.assertLess(group.index("```typescript TypeScript SDK"), group.index("```bash HTTPS"))
        shell = next(code for lang, title, code in blocks() if lang == "bash" and title.strip() == "HTTPS")
        wire = json.loads(re.search(r"-d '(.+)'", shell, re.S)[1])
        self.assertEqual(request(), wire)
        self.assertIn('relay.chats.messages.send("CHAT_ID", request)', source)
        self.assertIn(f'curl -sS "{API_ORIGIN}/v1/chats/$CHAT_ID/messages"', shell)
        self.assertIn("Authorization: Bearer $RELAY_AGENT_TOKEN", shell)
        self.assertTrue(wire["message"]["idempotency_key"])
        self.assertIn("HTTP/1.1 202 Accepted", source)

    def test_example_covers_pages_and_all_field_variants(self):
        prompt = form()
        self.assertEqual(len(prompt["pages"]), 2)
        self.assertEqual({f["type"] for f in fields()}, {"text", "select", "picker", "date"})
        self.assertEqual({f.get("multiline", False) for f in fields() if f["type"] == "text"}, {True, False})
        self.assertEqual({f.get("multiple", False) for f in fields() if f["type"] == "select"}, {True, False})
        self.assertTrue(any(f["type"] == "select" and f.get("multiple") and len(f["options"]) > 1
                            for f in fields()), "Keep a multiple-choice example in addition to the one-option opt-in")
        self.assertEqual(len({f["id"] for f in fields()}), len(fields()))
        self.assertTrue(any(f.get("required") is True for f in fields()))
        self.assertEqual(len({p["id"] for p in prompt["pages"]}), len(prompt["pages"]))
        for page in prompt["pages"]:
            self.assertRegex(page["id"], TOKEN)
            self.assertLessEqual(len(page["id"]), 19)
            self.assertTrue(1 <= len(page["fields"]) <= 50)
        for field in fields():
            self.assertRegex(field["id"], TOKEN)
            self.assertLessEqual(len(field["id"]), 100)
            self.assertLessEqual(len(field["label"]), {"text": 20, "select": 30, "picker": 20, "date": 40}[field["type"]])
            if "options" in field:
                self.assertTrue(1 <= len(field["options"]) <= (200 if field["type"] == "picker" else 20))
                self.assertEqual(len({o["value"] for o in field["options"]}), len(field["options"]))
                for option in field["options"]:
                    self.assertRegex(option["value"], TOKEN)
                    self.assertLessEqual(len(option["label"]), 30)

    def test_defaults_and_field_limits_are_precise(self):
        source = read(PAGE)
        for row in (
            "| `text` | 20 |",
            "| `select` | 30 | 1 to 20",
            "| `picker` | 20 | 1 to 200",
            "| `date` | 40 |",
        ):
            self.assertIn(row, source)
        self.assertIn("30 for single-line text and 300 for multiline text", source)
        self.assertIn("These are defaults", source)
        self.assertIn("positive integer", source)
        self.assertIn("`9007199254740991`, the API's safe-integer bound", source)
        self.assertIn("`placeholder` is optional text", source)
        self.assertNotRegex(source, r"(?i)placeholder.{0,45}(?:[0-9]+ characters|at most|max(?:imum)? \d)")
        self.assertNotRegex(source, r"(?i)(?:hard cap|hard ceiling|at most)\s+(?:30|300)\b")
        self.assertIn("Unicode scalar", source)
        self.assertIn("Only text fields take `max_length`", source)
        self.assertIn("`YYYY-MM-DD`", source)
        self.assertIn("`required` defaults to `false`", source)

    def test_splash_summary_and_native_completion_are_documented(self):
        prompt = form()
        self.assertTrue(prompt["show_summary"])
        self.assertTrue(prompt["splash"]["button_title"])
        self.assertEqual(prompt["reply_message"]["title"], "Form sent")
        self.assertTrue(prompt["received_message"]["title"])
        source = read(PAGE)
        for phrase in ("native sheet", "**Next**", "**Back**", "**Send**",
                       "`show_summary` defaults to `false`", "read-only",
                       "`received_message.title`", "`form.title`", "Each page uses its page title"):
            self.assertIn(phrase, source)

    def test_answers_are_keyed_by_field_id_and_match_the_prompt(self):
        answers = response()["parts"][1]["answers"]
        self.assertIsInstance(answers, dict)
        self.assertTrue(set(answers) <= {f["id"] for f in fields()})
        for field in fields():
            value = answers.get(field["id"])
            if field.get("required"):
                self.assertTrue(value)
            if value is None:
                continue
            multi = field["type"] == "select" and field.get("multiple", False)
            self.assertIsInstance(value, list if multi else str)
            if "options" in field:
                selected = value if multi else [value]
                self.assertEqual(selected, [o["value"] for o in field["options"] if o["value"] in selected])
                self.assertTrue(all(v in {o["value"] for o in field["options"]} for v in selected))
            elif field["type"] == "date":
                self.assertEqual(datetime.date.fromisoformat(value).isoformat(), value)
                self.assertGreaterEqual(value, field.get("min_date", "1900-01-01"))
                self.assertLessEqual(value, field.get("max_date", "2100-12-31"))
            elif field["type"] == "text":
                self.assertLessEqual(len(value), field.get("max_length", 300 if field.get("multiline") else 30))
                if not field.get("multiline"):
                    self.assertNotRegex(value, r"[\r\n]")
        source = read(PAGE)
        for phrase in ("source-option order", "Omit optional unanswered fields", "one-option multi-select"):
            self.assertIn(phrase, source)
        opt_in = next(f for f in fields() if f["id"] == "updates")
        self.assertTrue(opt_in["multiple"])
        self.assertEqual(len(opt_in["options"]), 1)

    def test_response_has_exact_fallback_and_reply_target(self):
        data = response()
        self.assertEqual([p["type"] for p in data["parts"]], ["text", "form_response"])
        self.assertEqual(data["parts"][0], {"type": "text", "value": "Form sent"})
        source_parts = request()["message"]["parts"]
        self.assertEqual(source_parts[data["reply_to"]["part_index"]]["type"], "form")
        self.assertRegex(data["reply_to"]["message_id"], r"^[0-9a-f-]{36}$")
        source = read(PAGE)
        self.assertIn('part.type === "form_response"', source)
        self.assertIn("answers: response.answers", source)
        self.assertIn("source: event.data.reply_to", source)
        self.assertIn("**Read `answers` by field ID", source)

    def test_viewer_projection_and_retry_rules_are_documented(self):
        source = read(PAGE)
        for phrase in (
            "## Read whether someone answered", "`has_responded`", "`answers`",
            "`reactions: null`", "For an agent", "`false`", "`null`",
            "`message.upserted`", "one answer", "same request and idempotency key",
            "| `400` |", "| `403` |", "| `404` |", "| `409` |", "| `422` |",
        ):
            self.assertIn(phrase, source)
        self.assertRegex(source, r"For an agent, `has_responded` is always `false` and `answers` is always `null`")
        self.assertIn("A user submits one answer to a form", source)
        self.assertIn("A matching retry returns the original answer", source)
        for forbidden in (r"\bA2A\b", r"/v1/tasks\b", r"\bexpires?[_ -]", r"\bexpiry\b",
                          r"FormPreview", r"<svg", r"<canvas"):
            self.assertNotRegex(source, forbidden)

    def test_counter_review_rules_are_documented(self):
        source = read(PAGE)
        for phrase in ("`min_date`", "`max_date`", "`1900-01-01`", "`2100-12-31`", "An answer outside the range is refused",
                       "`keyboard`", "`email`", "`phone`", "`number`", "`url`", "E.164", "Only text fields take `max_length`",
                       "Only text may sit beside a form", "is an ordinary reply", "Only a Message with `form_response` answers it",
                       "zero-width space"):
            self.assertIn(phrase, source)
        text = schema("FormTextField")
        self.assertIn("keyboard:", text)
        date = schema("FormDateField")
        self.assertIn("min_date:", date)
        self.assertNotIn("max_length:", date)
        self.assertNotIn("max_length:", schema("FormSelectField"))

    def test_form_checks_run_in_validation(self):
        scripts = json.loads(read("package.json"))["scripts"]
        self.assertEqual(scripts.get("check:form"), "python3 scripts/test-form-docs.py")
        self.assertIn("npm run check:form", scripts["validate"])

    def test_canonical_copy_contains_form_schemas_and_union(self):
        canonical = read("api-reference/openapi.yaml")
        anchors = re.findall(r"(?m)^[^#\n]*:\s*&([A-Za-z0-9_-]+)\s*$", canonical)
        self.assertEqual(len(anchors), len(set(anchors)),
                         "Duplicate YAML anchors can rebind existing non-form schemas")
        for name in (
            "FormOption", "FormTextField", "FormSelectField", "FormPickerField",
            "FormDateField", "FormField", "FormPage", "FormSplash",
            "FormReceivedMessage", "FormReplyMessage", "FormAnswers",
            "FormPart", "FormPartResponse", "FormResponsePart", "FormResponsePartResponse",
        ):
            self.assertRegex(canonical, rf"(?m)^    {name}:$")
        union = re.search(r"^    MessagePart:\n(.*?)(?=^    \w|\Z)", canonical, re.M | re.S)[1]
        for name in ("FormPart", "FormResponsePart"):
            self.assertIn(f'$ref: "#/components/schemas/{name}"', union)
        source = os.environ.get("RELAY_OPENAPI_SOURCE")
        if source:
            self.assertEqual((ROOT / "api-reference/openapi.yaml").read_bytes(), Path(source).read_bytes())
        self.check_contract_limits()

    def test_staging_and_mintlify_projections_keep_form(self):
        for path in ("api-reference/openapi.staging.yaml", "api-reference/openapi.mint.yaml"):
            with self.subTest(path=path):
                contract = read(path)
                for name in ("FormPart", "FormResponsePart", "FormPartResponse", "FormResponsePartResponse"):
                    self.assertRegex(contract, rf"(?m)^    {name}:$")
                for value in ("form", "form_response"):
                    self.assertRegex(contract, rf"(?m)^\s+{value}: ['\"]?#/components/schemas/Form")

    def check_contract_limits(self):
        for name, label_limit in (("FormTextField", 20), ("FormSelectField", 30),
                                  ("FormPickerField", 20), ("FormDateField", 40)):
            self.assertIn(f"maxLength: {label_limit}\n", prop(name, "label"))
            self.assertNotIn("maxLength", prop(name, "placeholder"))
            self.assertIn("default: false", prop(name, "required"))
        self.assertIn("maximum: 9007199254740991", prop("FormTextField", "max_length"))
        for name, count in (("FormSelectField", 20), ("FormPickerField", 200)):
            self.assertIn(f"maxItems: {count}\n", prop(name, "options"))
            self.assertIn("minItems: 1", prop(name, "options"))
        self.assertIn("minimum: 1", prop("FormTextField", "max_length"))
        self.assertIn("30 for single-line and 300 for multiline", prop("FormTextField", "max_length"))
        self.assertIn('default: "1900-01-01"', prop("FormDateField", "min_date"))
        self.assertIn('default: "2100-12-31"', prop("FormDateField", "max_date"))
        self.assertIn("maxLength: 19", prop("FormPage", "id"))
        self.assertIn("maxItems: 50", prop("FormPage", "fields"))
        self.assertNotIn("maxItems", prop("FormPart", "pages"))


if __name__ == "__main__":
    unittest.main()
