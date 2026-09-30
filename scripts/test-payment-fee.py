#!/usr/bin/env python3
"""Restore Docs #216's fee behavior and the contract removed by Docs #243."""
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = (
    "api-reference/openapi.yaml",
    "api-reference/openapi.staging.yaml",
    "api-reference/openapi.mint.yaml",
)


def read(path):
    return (ROOT / path).read_text()


def section(text, start, end):
    return text.split(start, 1)[1].split(end, 1)[0]


class PaymentFeeTests(unittest.TestCase):
    def test_guide_names_five_percent_stripe_direct_charge_fee(self):
        guide = read("interactions/payments.mdx")
        self.assertIn("Every payment is a direct charge on your own Stripe account", guide)
        self.assertIn("You are the merchant of record.", guide)
        self.assertIn("Relay takes 5% of each payment as a Stripe application fee", guide)
        self.assertIn("Stripe's card fees are yours.", guide)

    def test_guide_applies_fee_to_each_subscription_renewal(self):
        self.assertIn(
            "Relay takes 5% of each payment as a Stripe application fee, including each subscription renewal",
            read("interactions/payments.mdx"),
        )

    def test_guide_returns_proportional_fee_on_refunds(self):
        guide = read("interactions/payments.mdx")
        self.assertIn("Refunds and disputes stay in your Stripe Dashboard.", guide)
        self.assertIn("When a refund succeeds, Relay returns the same share of its fee.", guide)

    def test_payment_request_examples_include_fee_in_minor_units(self):
        examples = [
            json.loads(block)
            for block in re.findall(r"```json\s*\n(.*?)```", read("interactions/payments.mdx"), re.S)
        ]
        requests = [item for item in examples if item.get("object") == "payment_request"]
        self.assertEqual({item["status"] for item in requests}, {"requested", "canceled"})
        for item in requests:
            with self.subTest(status=item["status"]):
                self.assertEqual(item["amount"], 2400)
                self.assertEqual(item.get("application_fee_amount"), 120)

    def test_contracts_name_five_percent_application_fee_on_direct_charges(self):
        for path in CONTRACTS:
            with self.subTest(path=path):
                operation = " ".join(section(read(path), "  /v1/payment_requests:\n", "      tags:").split())
                self.assertIn("as a direct charge", operation)
                self.assertIn("Relay takes a 5% fee on every payment, as a Stripe application fee (`application_fee_amount`)", operation)

    def test_contracts_apply_five_percent_to_every_subscription_period(self):
        for path in CONTRACTS:
            with self.subTest(path=path):
                operation = " ".join(section(read(path), "  /v1/payment_requests:\n", "      tags:").split())
                self.assertIn("in subscription mode it is 5% of every period", operation)

    def test_contracts_return_proportional_fee_on_refunds(self):
        for path in CONTRACTS:
            with self.subTest(path=path):
                operation = " ".join(section(read(path), "  /v1/payment_requests:\n", "      tags:").split())
                self.assertIn("when a refund of a payment succeeds, Relay returns the same share of its fee", operation)

    def test_contracts_require_integer_fee_and_explain_first_period_and_zero(self):
        for path in CONTRACTS:
            with self.subTest(path=path):
                schema = re.split(r"\n    \w", read(path).split("    PaymentRequest:\n", 1)[1], maxsplit=1)[0]
                required = section(schema, "      required:", "      properties:")
                self.assertRegex(required, r"\bapplication_fee_amount\b")
                field = re.search(r"        application_fee_amount:\n(.*?)(?=\n        \w|\Z)", schema, re.S)
                self.assertIsNotNone(field, "PaymentRequest must expose application_fee_amount")
                self.assertIn("type: integer", field[1])
                self.assertIn("Relay's 5% fee on `amount`, in minor units", field[1])
                self.assertIn("in subscription mode, the first period's fee", field[1])
                self.assertIn("0 when 5% rounds to nothing", field[1])

    def test_agent_docs_carry_the_fee_guide_and_contract(self):
        agent = read("llms-full.txt")
        paragraph = section(read("interactions/payments.mdx"), "## Connect Stripe\n", "## Create a payment request")
        self.assertIn("Relay takes 5%", paragraph)
        self.assertIn(paragraph.strip(), agent)
        self.assertIn("Relay takes a 5% fee on every payment", agent)
        self.assertIn("        application_fee_amount:\n", agent)
        self.assertIn('"application_fee_amount": 120', agent)

    def test_changelog_announces_the_fee_and_its_required_field(self):
        entries = re.findall(r"<Update label=\"([^\"]+)\" tags=\{([^}]*)\}>(.*?)</Update>", read("changelog.mdx"), re.S)
        fee = [entry for entry in entries if "`application_fee_amount`" in entry[2]]
        self.assertEqual(len(fee), 1, "one changelog entry names application_fee_amount")
        label, tags, body = fee[0]
        text = " ".join(body.split())
        self.assertEqual(label, "2026-09-30")
        self.assertIn('"API"', tags)
        self.assertIn("Relay takes 5% of each payment as a Stripe application fee", text)
        self.assertIn("required `application_fee_amount`", text)
        self.assertIn("the first period's fee in subscription mode", text)
        self.assertIn("`0` when 5% rounds to nothing", text)
        self.assertIn("When a refund succeeds, Relay returns the same share of its fee.", text)
        self.assertIn("(/interactions/payments)", text)

    def test_public_docs_do_not_claim_relay_takes_no_fee(self):
        stale = re.compile(
            r"Relay (?:holds no money and )?(?:takes|keeps|charges) no fee"
            r"|You receive the full amount of each payment and each subscription renewal"
            r"|your account receives the full amount, less Stripe's own processing fees",
            re.I,
        )
        pages = [path for path in ROOT.rglob("*.mdx") if "node_modules" not in path.parts]
        generated = [ROOT / path for path in (*CONTRACTS, "llms-full.txt", "llms.txt")]
        for path in [*pages, *generated]:
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertIsNone(stale.search(" ".join(path.read_text().split())))


if __name__ == "__main__":
    unittest.main()
