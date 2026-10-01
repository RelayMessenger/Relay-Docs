#!/usr/bin/env python3
"""Select executable PR checks; protected pushes and uncertain diffs run validate.

Only isolated tooling/test owners are narrowed. Markdown is the product here:
content, shared generators, dependencies and workflow edits run the full suite.
GitHub templates are the only notes exemption. No workflow-level path filtering:
the named validation job always reports a result, even for templates alone.
"""
import json
import os
from pathlib import Path
import subprocess
import sys

# Tests map to their existing owning package command, including sibling tests.
OWNERS = {
    'check:posthog': ['scripts/test-posthog.py', 'scripts/test-posthog.mjs',
                      'scripts/test-posthog-proof-safety.mjs'],
    'check:hosted-cache': ['scripts/test-hosted-cache.py', 'scripts/test-hosted-environments.py'],
    'check:versions': ['scripts/test-refresh-versions.mjs'],
    'check:contract-source': ['scripts/test-contract-source.py', 'scripts/test-payment-fee.py'],
    'check:agent-onboarding': ['scripts/test-agent-onboarding.py'],
    'check:api-navigation': ['scripts/test-api-navigation.py'],
    'check:structure': ['scripts/test-docs-structure.py', 'scripts/test-docs-links.py'],
    'check:integration-docs': ['scripts/test-integration-docs.py'],
    'check:promote-workflow': ['scripts/test-promote-workflow.py'],
    'check:environments': ['scripts/test-environments.py'],
    'check:cli-reference': ['scripts/test-cli-reference.py', 'scripts/test-connect-forms.py'],
    'check:guides': ['scripts/test-recommend-agent.py'],
    'check:list-picker': ['scripts/test-list-picker.mjs'],
    'check:form': ['scripts/test-form-docs.py'],
    'check:cookbook-snippets': ['scripts/test-cookbook-snippets.py'],
    'check:ci': ['scripts/test-ci-selection.mjs'],
}
PATH_CHECKS = {path: check for check, paths in OWNERS.items() for path in paths}


def select():
    full = {'mode': 'full', 'checks': ['validate']}
    if os.environ.get('GITHUB_EVENT_NAME') != 'pull_request':
        return full
    base = os.environ.get('CI_BASE_SHA', '')
    if not base:
        return full
    try:
        # --no-renames reports both sides of renames; NUL preserves every path.
        diff = subprocess.check_output(
            ['git', 'diff', '--name-only', '--no-renames', '-z', f'{base}...HEAD', '--'],
            stderr=subprocess.DEVNULL).decode().split('\0')
    except (subprocess.CalledProcessError, UnicodeError):
        return full
    paths = [path for path in diff if path]
    if not paths:
        return full
    checks = set()
    for path in paths:
        # Deletions include both the source of a rename and removed tests.
        if not Path(path).is_file():
            return full
        if path == '.github/PULL_REQUEST_TEMPLATE.md' or (
                path.startswith('.github/ISSUE_TEMPLATE/') and
                Path(path).suffix in {'.md', '.yml', '.yaml'}):
            continue
        if path not in PATH_CHECKS:
            return full
        checks.add(PATH_CHECKS[path])
    return {'mode': 'affected' if checks else 'notes', 'checks': sorted(checks)}


def main():
    plan = select()
    print(json.dumps(plan), flush=True)
    if output := os.environ.get('GITHUB_OUTPUT'):
        with open(output, 'a') as stream:
            stream.write(f"mode={plan['mode']}\n")
            stream.write('cookbook=' + str(plan['mode'] == 'full' or
                         'check:cookbook-snippets' in plan['checks']).lower() + '\n')
    if '--run' in sys.argv:
        for check in plan['checks']:
            result = subprocess.run(['npm', 'run', check])
            if result.returncode:
                return result.returncode
    return 0


if __name__ == '__main__':
    sys.exit(main())
