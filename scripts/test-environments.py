#!/usr/bin/env python3
"""Offline regression tests. Run in Daytona with the repository dependencies.

Production is derived only in temporary copies. The staging checkout is never
reversed from production: dropped prerelease refs cannot be recovered that way.
Roundtrip means generate staging, derive production twice, then regenerate the
untouched staging source and prove its bytes did not change.
"""
import hashlib
import importlib.util
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from origins import ROOT, production_text, target


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


derive = load("derive-production")
validator = load("validate-staging-origins")

CASES = {
    "Use a token from staging.": "Use a token from production.",
    "Use a staging Agent Token": "Use a production Agent Token",
    "The root above is staging; use a staging token.":
        "The root above is production; use a production token.",
    "export RELAY_AGENT_TOKEN='<staging-agent-token>'":
        "export RELAY_AGENT_TOKEN='<production-agent-token>'",
    "https://github.com/RelayMessenger/Relay-SDK/tree/staging/skills/relay":
        "https://github.com/RelayMessenger/Relay-SDK/tree/main/skills/relay",
    "https://github.com/RelayMessenger/Relay-SDK/blob/staging/.claude-plugin/marketplace.json":
        "https://github.com/RelayMessenger/Relay-SDK/blob/main/.claude-plugin/marketplace.json",
    "https://raw.githubusercontent.com/RelayMessenger/Relay-SDK/staging/package.json":
        "https://raw.githubusercontent.com/RelayMessenger/Relay-SDK/main/package.json",
    "/plugin marketplace add RelayMessenger/Relay-SDK@staging":
        "/plugin marketplace add RelayMessenger/Relay-SDK@main",
    "https://github.com/RelayMessenger/Relay-SDK --ref staging":
        "https://github.com/RelayMessenger/Relay-SDK --ref main",
    "git clone --branch staging \\\n  https://github.com/RelayMessenger/Relay-SDK.git":
        "git clone --branch main \\\n  https://github.com/RelayMessenger/Relay-SDK.git",
    'relay profiles add staging --api-url https://api.staging.relayapp.im':
        'relay profiles add production --api-url https://api.relayapp.im',
    "relay auth login --profile staging --token-stdin":
        "relay auth login --profile production --token-stdin",
    'export RELAY_STATE_DIR="$HOME/.hermes/relay-staging"':
        'export RELAY_STATE_DIR="$HOME/.hermes/relay-production"',
    '"RELAY_PROFILE": "staging"': '"RELAY_PROFILE": "production"',
}


class EnvironmentTests(unittest.TestCase):
    def test_instructions_and_refs(self):
        for staging, production in CASES.items():
            with self.subTest(staging=staging):
                self.assertEqual(production_text(staging), production)
                self.assertEqual(production_text(production), production)
                self.assertTrue(validator.example_errors(staging, "production"))
                self.assertFalse(validator.example_errors(production, "production"))
                self.assertFalse(validator.example_errors(staging, "staging"))

    def test_unrelated_refs_and_environment_boundaries_are_preserved(self):
        text = (
            "git clone --branch staging https://github.com/other/project.git\n"
            "https://github.com/RelayMessenger/Relay-SDK/tree/staging-fix/README.md\n"
            "https://github.com/RelayMessenger/Relay-SDK --ref staging-fix\n"
            "/plugin marketplace add RelayMessenger/Relay-SDK@staging-fix\n"
            "relay --profile staging-fix events listen --acknowledge-events\n"
            "relay profiles add staging-fix\n"
            "Another repository documents its `staging` branch.\n"
            'export RELAY_STATE_DIR="$HOME/.hermes/relay-staging-fix"\n'
            "Staging and production credentials belong with their respective API roots.\n"
            'relay --profile "$RELAY_DEV_PROFILE" events listen --acknowledge-events\n'
            "The listener refuses the production API and FULL sync.\n"
        )
        self.assertEqual(production_text(text), text)
        self.assertFalse(validator.example_errors(text, "production"))

    def test_wrapped_token_instructions_are_rejected(self):
        for text in ("Provide the staging Agent Token.", "Use a\nstaging token.",
                     "Use a token\nfrom staging.", "Use a staging-agent-token."):
            with self.subTest(text=text):
                self.assertTrue(validator.example_errors(text, "production"))

    def test_registry_and_contract_are_immutable_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in derive.SKIP_FILES:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("api.staging.relayapp.im @relaymessenger/sdk@0.3.0")
            before = {name: (root / name).read_bytes() for name in derive.SKIP_FILES}
            derive.rewrite_tree(root)
            self.assertEqual(before, {name: (root / name).read_bytes() for name in derive.SKIP_FILES})

    @unittest.skipIf(target() == "production", "roundtrip starts from authored staging; production has its own validators")
    def test_roundtrip_and_validator_mutations(self):
        with tempfile.TemporaryDirectory(prefix="docs-environments-") as directory:
            staging = Path(directory) / "staging"
            shutil.copytree(ROOT, staging, ignore=shutil.ignore_patterns(
                ".git", "node_modules", ".mint", "__pycache__"))
            self.assertEqual((staging / ".docs-target").read_text(), "staging\n")
            self.generate(staging)
            before = self.digest(staging)
            production = Path(directory) / "production"
            shutil.copytree(staging, production)
            derive.rewrite_tree(production)
            self.generate(production)
            derived = self.digest(production)
            self.assertEqual(derive.rewrite_tree(production), [])
            self.generate(production)
            self.assertEqual(
                [], [name for name, digest in derived.items()
                     if self.digest(production).get(name) != digest],
            )
            self.generate(staging)
            self.assertEqual(before, self.digest(staging))
            for tree in (staging, production):
                for command in (
                    ["python3", "scripts/validate-docs.py"],
                    ["python3", "scripts/validate-staging-origins.py"],
                    ["node", "scripts/check-versions.mjs"],
                    ["python3", "scripts/build-agent-prompt.py", "--check"],
                    ["python3", "scripts/build-llms.py", "--check"],
                ):
                    self.run_command(tree, command)
            # A production validator must reject regression, not merely accept
            # whatever the derivation currently emits.
            for reference in CASES:
                path = production / "skill.md"
                original = path.read_text()
                path.write_text(original + "\n" + reference + "\n")
                self.run_command(production, ["python3", "scripts/validate-staging-origins.py"], success=False)
                path.write_text(original)
            page = production / "integrations/claude-code.mdx"
            original = page.read_text()
            page.write_text(original.replace("Relay-SDK@main", "Relay-SDK@staging"))
            self.run_command(production, ["python3", "scripts/validate-docs.py"], success=False)
            page.write_text(original)
            # Valid registry prereleases still cannot become production claims.
            import json
            versions = json.loads((production / "versions.json").read_text())
            version = versions["npm"]["@relaymessenger/sdk"]["staging"]
            for tree, success in ((staging, True), (production, False)):
                page = tree / "getting-started/sdks.mdx"
                original = page.read_text()
                page.write_text(original + f"\n`@relaymessenger/sdk@{version}`\n")
                self.run_command(tree, ["node", "scripts/check-versions.mjs"], success=success)
                page.write_text(original)
            (production / ".docs-target").write_text("invalid\n")
            self.run_command(production, ["node", "scripts/check-versions.mjs"], success=False)

    def generate(self, tree):
        # Projection and generated prompts without a network-dependent bundle.
        # Full Redocly/Mintlify rebuild is also exercised by npm run validate.
        for command in (
            ["python3", "scripts/build-staging-openapi.py"],
            ["python3", "scripts/build-agent-prompt.py"],
            ["python3", "scripts/build-llms.py"],
        ):
            self.run_command(tree, command)

    def digest(self, tree):
        return {str(p.relative_to(tree)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in tree.rglob("*") if p.is_file() and "__pycache__" not in p.parts}

    def run_command(self, tree, command, success=True):
        result = subprocess.run(command, cwd=tree, text=True, capture_output=True)
        if success:
            self.assertEqual(result.returncode, 0, f"{command}\n{result.stdout}\n{result.stderr}")
        else:
            self.assertNotEqual(result.returncode, 0, f"unexpected acceptance: {command}")


if __name__ == "__main__":
    unittest.main()
