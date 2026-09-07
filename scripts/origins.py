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
PACKAGE = r"(?:@relaymessenger/[a-z-]+|relay-claude-channel)"
PRERELEASE = r"\d+\.\d+\.\d+-staging\.\d+"
PACKAGE_REWRITES = (
    (re.compile(rf"({PACKAGE})@{PRERELEASE}\b"), r"\1"),
    (re.compile(rf"({PACKAGE})@staging\b"), r"\1"),
    (re.compile(rf"`{PRERELEASE}`"), "`latest`"),
)
STAGING_PACKAGE_REFERENCE = re.compile(rf"{PACKAGE}@staging\b|{PRERELEASE}")


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
    return text


def origin(host: str) -> str:
    """The host to expect in this checkout, given its staging spelling."""
    if host not in STAGING_TO_PRODUCTION:
        raise KeyError(host)
    return STAGING_TO_PRODUCTION[host] if target() == "production" else host
