#!/usr/bin/env python3
import json,re
from pathlib import Path
r=Path(__file__).resolve().parents[1];c=json.loads((r/'docs.json').read_text())
need={"index","quickstart","concepts","authentication","current-status","api-reference/overview","guides/sending-messages","guides/webhooks","guides/webhook-deliveries","guides/attachments","guides/reactions","guides/read-receipts","guides/typing-indicators","guides/conversation-history","reference/events","reference/errors","reference/limits"}
def w(x):
 if isinstance(x,dict):
  for k,v in x.items():
   if k=='pages' and isinstance(v,list):yield from (z for z in v if isinstance(z,str))
   yield from w(v)
 elif isinstance(x,list):
  for v in x:yield from w(v)
found=set(w(c.get('navigation',{})))
if found!=need:raise SystemExit(f'navigation mismatch {found^need}')
for p in sorted(r.rglob('*.mdx')):
 t=p.read_text();end=t.find('\n---\n',4)
 if not t.startswith('---\n') or end<0:raise SystemExit(f'bad frontmatter {p}')
 keys={x.split(':',1)[0] for x in t[4:end].splitlines() if ':' in x}
 if {'title','description','keywords'}-keys:raise SystemExit(f'missing frontmatter {p}')
 if '—' in t:raise SystemExit(f'em dash {p}')
for x in need:
 if not (r/f'{x}.mdx').is_file():raise SystemExit(f'missing {x}')
t='\n'.join(p.read_text() for p in [*r.rglob('*.mdx'),r/'skill.md'])
for n,q in {'event pull':r'GET /v1/events|/v1/events\?','global send':r'POST /v1/messages(?:\s|`|")','v2':r'/v2/','prefixed id':r'\b(?:msg|agt|usr|cnv|prt|att|evt|wh)_[A-Za-z0-9]','long polling':r'long[ -]poll','invalid shell JSON':r'-d \"\{(?!\\)'}.items():
 if re.search(q,t,re.I):raise SystemExit(f'stale {n}')
print(f'validated {len(need)} pages, navigation, frontmatter, prose, and stale-contract bans')
