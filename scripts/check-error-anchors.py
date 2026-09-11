#!/usr/bin/env python3
"""Check code anchors and legacy error.doc_url redirects.

Source snapshot: Relay-Server deba0b500870549e0af878d8117eb4e5545b9abd.
server/src/errors.ts maps HTTP statuses (including 402 -> 2009); literal
ApiError constructors and code fields across server/src supply the other codes.
app.ts composes /error/codes/${Math.floor(api.code / 1000)}xxx/${api.code}.
agent-socket.ts, attachments.ts, and worker.ts also emit literal legacy URLs.
Use --server-repo PATH to verify that snapshot against origin/staging read-only.
"""
import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVER_CODES = {1004, 1005, 2001, 2003, 2004, 2005, 2006, 2007, 2008, 2009,
                2015, 2023, 2025, 2026, 2028, 2029, 2030, 3006}


def check(root=ROOT, server_repo=None):
    page = (root / 'api-reference/errors.mdx').read_text()
    anchors = re.findall(r'<a id="(\d+)">', page)
    assert len(anchors) == len(set(anchors)), 'Duplicate error anchors'
    codes = set(SERVER_CODES)
    # ErrorCode currently has no enum. Read one if the canonical spec adds it.
    spec = (root / 'api-reference/openapi.yaml').read_text()
    schema = re.search(r'^    ErrorCode:\n(.*?)(?=^    \w|\Z)', spec, re.M | re.S)
    assert schema, 'ErrorCode schema missing'
    enum = re.search(r'      enum:\s*\n((?:        - \d+\n)+)', schema[1])
    if enum:
        codes.update(map(int, re.findall(r'\d+', enum[1])))
    redirects = {x['source']: x['destination'] for x in json.loads((root / 'docs.json').read_text())['redirects']}
    if server_repo:
        def git(*args):
            return subprocess.check_output(['git', '-C', str(server_repo), *args], text=True)
        paths = git('ls-tree', '-r', '--name-only', 'origin/staging', 'server/src').splitlines()
        sources = {p: git('show', 'origin/staging:' + p) for p in paths if p.endswith('.ts')}
        live = set()
        for text in sources.values():
            live.update(map(int, re.findall(r'new ApiError\(\s*\d+,\s*(\d{4})', text)))
            live.update(map(int, re.findall(r'\bcode:\s*(\d{4})\b', text)))
        live.update(map(int, re.findall(r'[?:]\s*(\d{4})', sources['server/src/errors.ts'])))
        assert live == SERVER_CODES, f'Server codes changed: {live ^ SERVER_CODES}'
        template = '/error/codes/${Math.floor(api.code / 1000)}xxx/${api.code}'
        assert template in sources['server/src/app.ts'], 'error.doc_url template changed'
        for path, text in sources.items():
            for url in re.findall(r'doc_url:\s*["`]([^"`]+)', text):
                if template in url:
                    continue
                if '/error/codes/' in url:
                    route = '/error/codes/' + url.split('/error/codes/', 1)[1]
                    assert route in redirects, f'Unresolved {path}: {route}'
                else:
                    # webhooks.ts returns the event catalog help URL, not error.doc_url.
                    assert path == 'server/src/webhooks.ts' and url.endswith('/guides/webhooks/events'), f'New doc_url shape: {path}: {url}'
    assert set(map(int, anchors)) == codes, 'Error code anchors do not match sources'
    for code in codes:
        route = f'/error/codes/{code // 1000}xxx/{code}'
        assert redirects.get(route) == f'/api-reference/errors#{code}', f'Broken redirect: {route}'
    assert not list((root / 'error/codes').rglob('*.mdx')), 'Per-code pages remain'
    return len(codes)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--server-repo', type=Path)
    args = parser.parse_args()
    print(f'Error anchors and legacy doc_url redirects valid: {check(server_repo=args.server_repo)} codes')
