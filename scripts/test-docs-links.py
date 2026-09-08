#!/usr/bin/env python3
"""Resolve internal page links and fragment targets, including legacy anchors."""
import json
import re
import unittest
from pathlib import Path
from urllib.parse import unquote, urlsplit
from docs_structure import prose
from api_navigation import page_paths

ROOT = Path(__file__).resolve().parents[1]


def slug(text):
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"\s+", "-", text.strip())


def check_links(root=ROOT):
    config = json.loads((root / "docs.json").read_text())
    redirects = {x['source']: x['destination'] for x in config.get('redirects', [])}
    pages = {}
    for path in root.rglob('*.mdx'):
        if 'node_modules' in path.parts:
            continue
        route = '/' + str(path.relative_to(root).with_suffix(''))
        pages[route] = path
        if route.endswith('/index'):
            pages[route[:-6] or '/'] = path
        if route == '/index':
            pages['/'] = path
            pages['/guides'] = path
    endpoints = {v['href'] for v in page_paths().values()}
    anchors = {}
    for path in set(pages.values()):
        body = prose(path.read_text())
        heads = re.findall(r'^#{1,6}\s+(.+)$', body, re.M)
        anchors[path] = {slug(h) for h in heads}
        anchors[path].update(re.findall(r'\bid=["\']([^"\']+)["\']', body))
    failures = []
    for path in set(pages.values()):
        text = path.read_text()
        # Examples inside code blocks may deliberately show a user's receiver;
        # only actual links and MDX href attributes are navigation.
        body = prose(text)
        links = re.findall(r'\]\((/[^)\s]+|#[^)\s]+)\)', body)
        links += re.findall(r'\bhref=["\'](/[^"\']+|#[^"\']+)["\']', body)
        for link in links:
            parts = urlsplit(link)
            route = unquote(parts.path).rstrip('/') or '/'
            if link.startswith('#'):
                destination = path
            else:
                if route.endswith('.md'):
                    route = route[:-3]
                seen = set()
                while route in redirects and route not in seen:
                    seen.add(route)
                    route = urlsplit(redirects[route]).path
                if route in endpoints or (root / parts.path.lstrip('/')).is_file():
                    continue
                destination = pages.get(route)
            if not destination:
                failures.append(f'{path.relative_to(root)}: missing page {link}')
            elif parts.fragment and unquote(parts.fragment) not in anchors[destination]:
                failures.append(f'{path.relative_to(root)}: missing anchor {link}')
    return sorted(failures)


class InternalLinkTests(unittest.TestCase):
    def test_all_authored_links_and_anchors(self):
        self.assertEqual(check_links(), [])

    def test_heading_slug(self):
        self.assertEqual(slug('1. Send a `Message`'), '1-send-a-message')
        self.assertEqual(slug('SDK retries and idempotency'), 'sdk-retries-and-idempotency')


if __name__ == '__main__':
    unittest.main()
