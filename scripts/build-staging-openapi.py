#!/usr/bin/env python3
"""Project deployment origins for staging; never edit the canonical contract."""
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def staging_openapi(source: str) -> str:
    return source.replace(
        "https://api.relayapp.im", "https://api.staging.relayapp.im"
    ).replace(
        "wss://api.relayapp.im", "wss://api.staging.relayapp.im"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    source = (ROOT / "api-reference/openapi.yaml").read_text()
    expected = staging_openapi(source)
    target = ROOT / "api-reference/openapi.staging.yaml"
    if args.check:
        if not target.exists() or target.read_text() != expected:
            raise SystemExit("Staging OpenAPI is stale; run scripts/build-staging-openapi.py")
    else:
        target.write_text(expected)
    print("Staging OpenAPI differs from the canonical contract only by API origins")


if __name__ == "__main__":
    main()
