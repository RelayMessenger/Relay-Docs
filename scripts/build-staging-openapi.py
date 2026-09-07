#!/usr/bin/env python3
"""Project deployment origins for this checkout; never edit the canonical contract.

On staging the API origins become api.staging.relayapp.im. On the derived
production branch (`.docs-target` = production, or `--production`) the
projection is the identity, so the presented contract equals the canonical one.
"""
import argparse
from pathlib import Path
from origins import origin

ROOT = Path(__file__).resolve().parents[1]


def staging_openapi(source: str) -> str:
    api = origin("api.staging.relayapp.im")
    return source.replace(
        "https://api.relayapp.im", f"https://{api}"
    ).replace(
        "wss://api.relayapp.im", f"wss://{api}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--production", action="store_true")
    args = parser.parse_args()
    source = (ROOT / "api-reference/openapi.yaml").read_text()
    expected = staging_openapi(source)
    target = ROOT / "api-reference/openapi.staging.yaml"
    if args.check:
        if not target.exists() or target.read_text() != expected:
            raise SystemExit("Presented OpenAPI is stale; run scripts/build-staging-openapi.py")
    else:
        target.write_text(expected)
    print("Presented OpenAPI differs from the canonical contract only by API origins")


if __name__ == "__main__":
    main()
