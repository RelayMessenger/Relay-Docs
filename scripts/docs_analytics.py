"""Build and validate the environment-specific, pageview-only docs client.

Official sources read 2026-09-16:
https://mintlify.com/docs/integrations/analytics/posthog.md
https://mintlify.com/docs.json
https://mintlify.com/docs/customize/custom-scripts
https://posthog.com/docs/libraries/js/config
https://posthog.com/docs/advanced/proxy
https://github.com/PostHog/posthog-js/blob/main/packages/browser/src/posthog-core.ts

Mintlify's native schema exposes apiKey/apiHost/sessionRecording only. The live
docs.staging.relayapp.im/mintlify-assets/_next/static/chunks/8048dcef7298cf99.js
loader sets capture_pageview:false and recording, not autocapture or before_send.
A custom client is needed to preserve the requested
privacy boundary. Public phc_ tokens were read from Infisical /shared, prod and
staging; they are not credentials. Never put a personal API key in this file.
"""
import json
import re
from pathlib import Path

from origins import ROOT, production_text, target

CONFIG_BLOCK = re.compile(
    r"  // BEGIN GENERATED POSTHOG CONFIG\n.*?  // END GENERATED POSTHOG CONFIG",
    re.S,
)


def configuration(root: Path, environment: str) -> dict:
    projects = json.loads((root / "scripts/posthog-projects.json").read_text())
    for name, project_id in (("staging", 577466), ("production", 533131)):
        project = projects[name]
        if project["projectId"] != project_id or not re.fullmatch(r"phc_[A-Za-z0-9]+", project["token"]):
            raise ValueError(f"invalid {name} PostHog public project configuration")
    if projects["staging"]["token"] == projects["production"]["token"]:
        raise ValueError("PostHog environments must use separate project tokens")
    config = json.loads((root / "docs.json").read_text())
    # Native analytics would add a second client without our privacy filter.
    for key in ("integrations", "analytics"):
        if "posthog" in config.get(key, {}):
            raise ValueError("PostHog must use the single privacy-filtered docs client")
    paths = {"/", "/index"}

    def visit(value):
        if isinstance(value, dict):
            for key, children in value.items():
                if key == "pages":
                    for page in children:
                        if isinstance(page, str) and not re.match(r"^[A-Z]+ |https?://", page):
                            paths.add("/" + page.strip("/"))
                visit(children)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(config["navigation"])
    endpoints = json.loads((root / "scripts/api-page-paths.json").read_text())
    paths.update(entry["href"] for entry in endpoints.values())
    origin = "https://docs.staging.relayapp.im"
    return {
        "token": projects[environment]["token"],
        "origin": production_text(origin) if environment == "production" else origin,
        "paths": sorted(paths),
    }


def rendered(root: Path, environment: str) -> str:
    source = (root / "posthog.js").read_text()
    if len(CONFIG_BLOCK.findall(source)) != 1:
        raise ValueError("posthog.js must contain exactly one generated configuration")
    block = "  // BEGIN GENERATED POSTHOG CONFIG\n"
    block += "  const CONFIG = " + json.dumps(configuration(root, environment), separators=(",", ":")) + ";\n"
    block += "  // END GENERATED POSTHOG CONFIG"
    return CONFIG_BLOCK.sub(lambda _: block, source)


def validate(root: Path, environment: str) -> None:
    source = (root / "posthog.js").read_text()
    if source != rendered(root, environment):
        raise ValueError(f"missing, stale, or wrong-environment PostHog integration ({environment}); run npm run build:posthog")
    ignored = (root / ".mintignore").read_text().splitlines()
    if "posthog.js" in ignored or "*.js" in ignored:
        raise ValueError("Mintlify must publish posthog.js")


if __name__ == "__main__":
    import sys
    if "--check" in sys.argv:
        validate(ROOT, target())
        print(f"validated {target()} PostHog integration")
    else:
        (ROOT / "posthog.js").write_text(rendered(ROOT, target()))
        print(f"built {target()} PostHog integration")
