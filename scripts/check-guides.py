#!/usr/bin/env python3
"""SPEC section 7 acceptance checks. --root supports isolated mutation receipts.

Existing coverage: 1 mint validate; 4 docs_structure; 5 test-integration-docs
(runtime subset); 11/12 check-error-anchors; 15 test-docs-links; 16
check:contract-source + check:openapi-bundle; 17 check:llms. CLI generation
and staging-origin checks are additional gates, not substitutes for these 18.
"""
import argparse
import hashlib
import importlib.util
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import urlsplit
from docs_structure import TASK_VERBS, authored_paths, is_task_guide, prose

ROOT = Path(__file__).resolve().parents[1]
FENCES = re.compile(r'^(`{3,})([^\n]*)\n(.*?)^\1[ \t]*$', re.M | re.S)
CONNECT = ['Before you start', 'Connect', 'Send it a message', 'What it can do', 'When it fails', 'Next steps']  # moved 2026-09-11 with the integrations rewrite
FIXED = {'Before you start', 'What you get back', 'When it fails', 'Next steps'}


def load(name):
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'), ROOT / 'scripts' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def pages(root):
    return sorted(p for p in root.rglob('*.mdx') if not {'node_modules', '.git'}.intersection(p.parts))


def scoped(root):
    return [p for p in pages(root) if p.relative_to(root).parts[0] in {'start', 'integrations', 'agents', 'chats', 'messages', 'webhooks', 'events', 'websocket', 'live', 'cli'}]


def heads(text):
    return re.findall(r'^## (.+)$', prose(text), re.M)


def fail(path, message):
    raise AssertionError(f'{path}: {message}')


def links(text):
    return re.findall(r'\]\(([^)\s]+)\)', prose(text)) + re.findall(r'\bhref=["\']([^"\']+)', prose(text))


def requests(text):
    """Network calls only: SDK construction, verify/unwrap, event handlers are local.
    Group equivalent variants by CodeGroup, otherwise each fence is one request.
    """
    groups = list(re.finditer(r'<CodeGroup\b[^>]*>.*?</CodeGroup>', text, re.S))
    candidates = groups + [b for b in FENCES.finditer(text) if not any(g.start() <= b.start() < g.end() for g in groups)]
    result = []
    for block in sorted(candidates, key=lambda x: x.start()):
        variants = []
        for f in FENCES.finditer(block[0]):
            lang, code = f[2].lower(), f[3]
            if re.search(r'\bcurl\s+(?:[^\n]*|\\\n)', code) and lang.split(' ')[0] in {'bash', 'sh', 'shell', 'console'}:
                variants.append('curl')
            if lang.split(' ')[0] in {'typescript', 'ts', 'javascript', 'js'} and re.search(r'\b(?:(?:relay|client)\.(?!(?:webhooks\.(?:verify|unwrap)|events\.(?:on|off))\b)[\w.]+|Relay\.createAgent|\w+\.getNextPage|fetch)\s*\(', code):
                variants.append('typescript')
        if variants:
            result.append((block.start(), block.end(), set(variants)))
    return result


def check_01(root):
    config = json.loads((root / 'docs.json').read_text())
    def walk(value):
        if isinstance(value, dict):
            keys = set(value) & {'tabs', 'groups', 'pages', 'anchors', 'dropdowns'}
            assert len(keys) <= 1, 'docs.json: mixed navigation element types'
            for item in value.values(): walk(item)
        elif isinstance(value, list):
            for item in value: walk(item)
    walk(config['navigation'])
    for page in authored_paths(config['navigation']):
        assert (root / f'{page}.mdx').is_file(), f'{page}: navigation page missing'


def check_02(root):
    for p in scoped(root):
        h = heads(p.read_text())
        assert h and h[-1] == 'Next steps', f'{p.relative_to(root)}: Next steps must be last'
        assert 'This page is being written.' not in p.read_text(), f'{p.relative_to(root)}: unfinished placeholder'


def check_03(root):
    for p in scoped(root):
        text = prose(p.read_text())
        section = re.search(r'^## Next steps\s*\n(.*?)(?=^## |\Z)', text, re.M | re.S)
        count = len(links(section[1])) if section else 0
        assert 3 <= count <= 5, f'{p.relative_to(root)}: Next steps has {count} links (need 3–5)'


def check_04(root):
    for p in [q for d in ('agents', 'chats', 'messages', 'webhooks', 'events', 'websocket', 'live') for q in (root / d).rglob('*.mdx') if is_task_guide(q.relative_to(root).with_suffix('').as_posix())]:
        text = p.read_text(); h = heads(text)
        for heading in h:
            assert heading in FIXED or heading.split()[0] in TASK_VERBS, f'{p.relative_to(root)}: invalid H2 {heading}'
        if 'Before you start' in h:
            assert h[0] == 'Before you start', f'{p.relative_to(root)}: prerequisites must come first'
        if requests(text):
            assert h[-3:] == ['What you get back', 'When it fails', 'Next steps'], f'{p.relative_to(root)}: request requires response/failure/next-step sections'


def check_05(root):
    for p in (root / 'integrations').glob('*.mdx'):
        assert heads(p.read_text()) == CONNECT, f'{p.relative_to(root)}: Connect skeleton out of order'


def check_06(root):
    for p in (root / 'api-reference/resources').glob('*/overview.mdx'):
        h = heads(p.read_text())
        assert len(h) == 5 and re.fullmatch(r'The .+ object', h[0]) and h[1:] == ['Example', 'Operations', 'Errors', 'Next steps'], f'{p.relative_to(root)}: reference skeleton out of order'


def task_pages(root):
    # Owner ruling 2026-09-11 (final tree): the main page and the migration
    # guides show one call to orient a reader, not to be copied; both answer in
    # prose by design, the same exemption index already holds in
    # docs_structure. Every documented task page keeps the full request
    # skeleton: cURL plus TypeScript in one CodeGroup, then a real response.
    exempt = {'index.mdx'}
    return [p for p in pages(root)
            if p.relative_to(root).as_posix() not in exempt
            and p.relative_to(root).parts[0] != 'resources']


def missing_responses(root):
    """Every request needs a real response fence after it. A prose marker such as
    "(unverified: ...)" never counts: the relay-language skill bans provenance in
    prose, and a request with no real response is deleted, not hedged."""
    found = []
    for p in task_pages(root):
        text = p.read_text(); reqs = requests(text)
        for i, (_, end, _) in enumerate(reqs):
            tail = text[end:reqs[i + 1][0] if i + 1 < len(reqs) else len(text)]
            if not any(re.match(r'(?:json|http|text)\b', b[2]) for b in FENCES.finditer(tail)):
                found.append(f'{p.relative_to(root)}: request {i + 1} has no following response')
    return found


def check_07(root):
    import tempfile
    # Mutation receipt: a page whose only "response" is an unverified marker must fail.
    with tempfile.TemporaryDirectory() as scratch:
        page = Path(scratch) / 'guide.mdx'
        request = '<CodeGroup>\n```bash cURL\ncurl -sS "https://api.example/v1/chats"\n```\n```typescript TypeScript SDK\nconst page = await relay.chats.listChats({ limit: 1 });\n```\n</CodeGroup>\n'
        page.write_text(request + '\n(unverified: response not captured)\n')
        assert missing_responses(Path(scratch)), 'check_07 receipt: an unverified marker satisfied the response rule'
        page.write_text(request + '\n```json\n{"chats": []}\n```\n')
        assert not missing_responses(Path(scratch)), 'check_07 receipt: a real response fence was not accepted'
    errors = missing_responses(root)
    assert not errors, errors[0]


def check_08(root):
    for p in task_pages(root):
        for i, (_, _, languages) in enumerate(requests(p.read_text())):
            assert languages == {'curl', 'typescript'}, f'{p.relative_to(root)}: request {i + 1} needs cURL + TypeScript in one CodeGroup'


def check_09(root):
    token = re.compile(r'\b(?:rly_(?:live|test|staging)_[A-Za-z0-9_-]+|relay_(?:live|test|staging|agent|token)_[A-Za-z0-9_-]{12,}|sk_(?:live|test)_[A-Za-z0-9_-]+|eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+)\b|Bearer\s+(?!\$|<|\{|["\']|YOUR_)[A-Za-z0-9_-]{20,}')
    for p in pages(root):
        assert not any(token.search(b[3]) for b in FENCES.finditer(p.read_text())), f'{p.relative_to(root)}: literal secret in code block'


def check_10(root):
    for p in pages(root):
        body = prose(p.read_text())
        endpoint = re.search(r'\b(?:GET|POST|PUT|PATCH|DELETE)\s+/v\d+/[^\s`|]+', body)
        parameters = re.search(r'^\|\s*(?:Parameter|Param|Name)\s*\|.*(?:Type|Required|Description)', body, re.M | re.I)
        assert not (endpoint and parameters), f'{p.relative_to(root)}: handwritten endpoint parameters'


def check_11(root):
    spec = (root / 'api-reference/openapi.yaml').read_text()
    schema = re.search(r'^    ErrorCode:\n(.*?)(?=^    \w|\Z)', spec, re.M | re.S)
    assert schema, 'ErrorCode schema missing'
    enum = re.search(r'      enum:\s*\n((?:        - \d+\n)+)', schema[1])
    codes = set(load('check-error-anchors').SERVER_CODES)
    if enum: codes.update(map(int, re.findall(r'\d+', enum[1])))
    rows = set(map(int, re.findall(r'^\|\s*<a id="(\d+)">\d+</a>\s*\|', (root / 'api-reference/errors.mdx').read_text(), re.M)))
    assert codes <= rows, f'api-reference/errors.mdx: missing error rows {sorted(codes - rows)}'


def check_12(root):
    redirects = {r['source']: r['destination'] for r in json.loads((root / 'docs.json').read_text())['redirects']}
    spec = (root / 'api-reference/openapi.yaml').read_text()
    urls = re.findall(r'\bdoc_url:\s*(https?://[^\s]+)', spec)
    urls += [f'/error/codes/{c // 1000}xxx/{c}' for c in load('check-error-anchors').SERVER_CODES]
    for url in urls:
        dest = urlsplit(url); seen = set()
        while dest.path in redirects:
            assert dest.path not in seen, f'error.doc_url redirect cycle: {url}'
            seen.add(dest.path); dest = urlsplit(redirects[dest.path])
        page = root / (dest.path.lstrip('/') + '.mdx')
        assert page.is_file() and dest.fragment and dest.fragment in re.findall(r'\bid=["\']([^"\']+)', page.read_text()), f'error.doc_url unresolved: {url}'


def check_13(root):
    for p in pages(root):
        assert not re.search(r'<span\s+id=["\'][^"\']+["\']\s*(?:/\s*>|>\s*</span\s*>)', prose(p.read_text())), f'{p.relative_to(root)}: empty span anchor'


def baseline(root):
    # The page set before the 2026-09-10 rebuild, committed so the check needs
    # no git ref: CI checks out shallow and has no origin/staging, and after
    # the merge origin/staging is the rebuilt tree itself. Every path ever
    # removed must keep its redirect; append to the file, never prune it.
    return (root / 'scripts' / 'page-set-baseline.txt').read_text().splitlines()


def check_14(root):
    old = {p[:-4] for p in baseline(root) if p.endswith('.mdx')}
    current = {p.relative_to(root).with_suffix('').as_posix() for p in pages(root)}
    redirects = {r['source'] for r in json.loads((root / 'docs.json').read_text())['redirects']}
    assert all('/' + p in redirects for p in old - current), 'docs.json: removed paths without redirect ' + ','.join(sorted(p for p in old - current if '/' + p not in redirects))


def check_15(root):
    errors = load('test-docs-links').check_links(root)
    assert not errors, errors[0] if errors else ''


def check_16(root):
    expected = load('test-contract-source').UPSTREAM_SHA256
    assert hashlib.sha256((root / 'api-reference/openapi.yaml').read_bytes()).hexdigest() == expected, 'api-reference/openapi.yaml: differs from pinned Server contract'
    # Existing check:openapi-bundle validates the generated Mintlify projection.


def check_17(root):
    module = load('build-llms'); module.ROOT = root
    config = json.loads((root / 'docs.json').read_text())
    entries = module.navigation_entries(config)
    spec = (root / 'api-reference/openapi.staging.yaml').read_text()
    outputs = {'llms.txt': module.render_index(config, entries, module.openapi_operations(spec)), 'llms-full.txt': module.render_full(config, entries, spec)}
    for name, expected in outputs.items():
        assert (root / name).read_text() == expected, f'{name}: stale page set'


def check_18(root):
    text = (root / 'changelog.mdx').read_text()
    for attrs, body in re.findall(r'<Update\b([^>]*)>(.*?)</Update>', text, re.S):
        assert re.search(r'\blabel="\d{4}-\d{2}-\d{2}"', attrs), 'changelog.mdx: Update missing date label'
        breaking = re.search(r'\bbreaking\b|\bremoved\b|\breplace[sd]?\b|\binstead of\b|\bold paths redirect\b|\blimits? (?:change|now|reduc|increas)', body, re.I)
        assert not breaking or re.search(r'\btags=\{\[[^\]]*"Breaking change"', attrs), 'changelog.mdx: breaking entry missing Breaking change tag'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--check', type=int, choices=range(1, 19))
    args = parser.parse_args(); failed = 0
    for number in ([args.check] if args.check else range(1, 19)):
        try:
            globals()[f'check_{number:02}'](args.root)
            print(f'PASS {number:02}')
        except (AssertionError, ValueError, OSError) as error:
            print(f'FAIL {number:02} {error}'); failed += 1
    raise SystemExit(bool(failed))


if __name__ == '__main__':
    main()
