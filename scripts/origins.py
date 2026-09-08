#!/usr/bin/env python3
"""Single source of truth for the deployment target of this checkout.

The `staging` branch is authored against staging origins. The `main` branch is
derived from it by `scripts/derive-production.py`, which rewrites every staging
origin to its production twin and records `production` in `.docs-target`.
Every script that must know which environment the checkout describes reads
`target()` here; nothing else may hard-code an origin.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET_FILE = ROOT / ".docs-target"

# Staging value -> production value. Order matters only for readability; no
# key is a substring of another key's replacement, so replacement is stable.
STAGING_TO_PRODUCTION = {
    "docs.staging.relayapp.im": "docs.relayapp.im",
    "api.staging.relayapp.im": "api.relayapp.im",
    "go.staging.relayapp.im": "go.relayapp.im",
    "staging.relayapp.im": "relayapp.im",
    "cdn.staging.relayapp.im": "cdn.relayapp.im",
    "console.staging.relayapp.im": "console.relayapp.im",
    "uploads.staging.relayapp.im": "uploads.relayapp.im",
    "relay-staging.mintlify.app": "relay.mintlify.app",
    # The site mark: black on staging, Relay blue on production
    # (scripts/validate-docs.py pins both files by hash).
    "/favicon-staging.png": "/favicon.png",
}

STAGING_HOSTS = tuple(host for host in STAGING_TO_PRODUCTION if "/" not in host)

# npm packages this repository documents. On production a reader installs the
# plain name (the `latest` tag) and never a `@staging` dist-tag or a
# `-staging.N` prerelease (owner ruling, 2026-09-07). The rewrite drops the
# tag or version from a package spec and turns a bare version cell into
# `latest`, which is the version the plain install resolves to.
PACKAGE = r"(?:@relaymessenger/[a-z-]+|relay-claude-channel|relaymessenger)"
PRERELEASE = r"\d+\.\d+\.\d+-staging\.\d+"
PACKAGE_REWRITES = (
    (re.compile(rf"({PACKAGE})@{PRERELEASE}\b"), r"\1"),
    (re.compile(rf"({PACKAGE})@staging\b"), r"\1"),
    (re.compile(rf"`{PRERELEASE}`"), "`latest`"),
)
STAGING_PACKAGE_REFERENCE = re.compile(rf"{PACKAGE}@staging\b|{PRERELEASE}")

# Only documented Relay SDK source refs are projected. Never rewrite arbitrary
# branch names, historical prose, third-party repositories, or registry data.
SOURCE_REWRITES = (
    (re.compile(r"(github\.com/RelayMessenger/Relay-SDK/(?:tree|blob)/)staging(?![\w.-])"), r"\1main"),
    (re.compile(r"(raw\.githubusercontent\.com/RelayMessenger/Relay-SDK/)staging/"), r"\1main/"),
    (re.compile(r"(RelayMessenger/Relay-SDK(?:\.git)?)@staging(?![\w./-])"), r"\1@main"),
    (re.compile(r"(https://github\.com/RelayMessenger/Relay-SDK(?:\.git)? --ref )staging(?![\w./-])"), r"\1main"),
    (re.compile(r"(git clone --branch )staging(\s+(?:\\\s+)?https://github\.com/RelayMessenger/Relay-SDK(?:\.git)?)"), r"\1main\2"),
)
PROFILE_REWRITES = (
    (re.compile(r"(\b(?:relay|npx relaymessenger(?:@staging)?) profiles (?:add|use) )staging(?![\w./-])"), r"\1production"),
    (re.compile(r"(\b(?:relay|npx relaymessenger(?:@staging)?)\b[^\n]*?--profile\s+)staging(?![\w./-])"), r"\1production"),
    (re.compile(r"(\$HOME/\.hermes/relay-)staging(?![\w./-])"), r"\1production"),
)

# Literal operator instructions, not a global staging -> production replace.
# Registry/catalog versions are not inferred from an environment or branch.
INSTRUCTION_REWRITES = {
    "The root above is staging; use a staging token.": "The root above is production; use a production token.",
    "Use a token from staging.": "Use a token from production.",
    "staging Agent Token": "production Agent Token",
    "staging API origin": "production API origin",
    "<staging-agent-token>": "<production-agent-token>",
    "$STAGING_RELAY_AGENT_TOKEN": "$RELAY_AGENT_TOKEN",
    "## Configure staging": "## Configure production",
    "`Configure staging`": "`Configure production`",
    "## Staging package": "## Published package",
    "`Staging package`": "`Published package`",
    "staging package": "package",
    "current published staging package": "current published package",
    "Install the published staging tag:": "Install the published package:",
    "Staging train": "Install",
    "Staging verification": "Environment verification",
    "hosted staging index": "hosted production index",
    "The staging `llms.txt` instructions": "The production `llms.txt` instructions",
    "for this staging candidate": "for this docs candidate",
    "staging profiles": "production profiles",
    '"staging profile"': '"production profile"',
    '"RELAY_PROFILE": "staging"': '"RELAY_PROFILE": "production"',
    "| npm tags | `latest`, `staging` |": "| npm tag | `latest` |",
}
PROSE_REWRITES = (
    (re.compile(r"The `staging` tag\s+selects the current prerelease, which the command above installs\."), "The command above installs the `latest` release."),
    (re.compile(r"; the\s+`staging` tag\s+selects the\s+current prerelease\."), "."),
    (re.compile(r"The `staging`\s+tag on each package selects its current prerelease, which these staging pages\s+install\."), "The commands above install those releases."),
)

STAGING_INSTRUCTION_REFERENCE = re.compile(
    "|".join(pattern.pattern for pattern, _ in (*SOURCE_REWRITES, *PROFILE_REWRITES))
    + r"|(?<![\w-])staging[-\s]+(?:agent[-\s]+)?token\b"
    r"|token\s+from\s+staging\b|staging\s+API\s+(?:root|origin)\b"
    r"|STAGING_RELAY_AGENT_TOKEN\b"
    r'|"RELAY_PROFILE":\s*"staging"'
    r"|Configure staging\b|Staging package\b|published staging tag\b",
    re.I,
)


def target() -> str:
    """`production` when asked explicitly or recorded in `.docs-target`."""
    if "--production" in sys.argv[1:]:
        return "production"
    if TARGET_FILE.is_file():
        value = TARGET_FILE.read_text().strip()
        if value not in ("staging", "production"):
            raise SystemExit(f".docs-target must be staging or production, not {value!r}")
        return value
    return "staging"


def production_text(text: str) -> str:
    for staging_value, production_value in STAGING_TO_PRODUCTION.items():
        text = text.replace(staging_value, production_value)
    for pattern, replacement in PACKAGE_REWRITES:
        text = pattern.sub(replacement, text)
    for pattern, replacement in (*SOURCE_REWRITES, *PROFILE_REWRITES):
        text = pattern.sub(replacement, text)
    for staging_value, production_value in INSTRUCTION_REWRITES.items():
        text = text.replace(staging_value, production_value)
    for pattern, replacement in PROSE_REWRITES:
        text = pattern.sub(replacement, text)
    return text


def source_ref() -> str:
    """The authored SDK source branch selected by this docs target."""
    return "main" if target() == "production" else "staging"


def origin(host: str) -> str:
    """The host to expect in this checkout, given its staging spelling."""
    if host not in STAGING_TO_PRODUCTION:
        raise KeyError(host)
    return STAGING_TO_PRODUCTION[host] if target() == "production" else host
