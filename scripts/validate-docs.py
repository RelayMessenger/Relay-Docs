#!/usr/bin/env python3
import json,re
from pathlib import Path
r=Path(__file__).resolve().parents[1];c=json.loads((r/'docs.json').read_text())
need={"index","quickstart","concepts","authentication","current-status","api-reference/overview","guides/sending-messages","guides/webhooks","guides/webhook-deliveries","guides/agent-events","guides/socket-mode","guides/install-agents","guides/blocked-handles","guides/attachments","guides/reactions","guides/read-receipts","guides/conversation-history","reference/events","reference/errors","reference/limits"}
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
if (r/'guides/linq-migration.mdx').exists():raise SystemExit('direct Linq migration guide must remain deleted')
if (r/'guides/typing-indicators.mdx').exists():raise SystemExit('typing guide must remain deleted until typing is implemented')
t='\n'.join(p.read_text() for p in [*r.rglob('*.mdx'),r/'skill.md'])
for n,q in {
 'event pull':r'GET /v1/events|/v1/events\?',
 'old URL namespace':r'/api/(?:partner|mobile)|api\.relayapp\.im/api/',
 'old route version':r'/v3/',
 'v2':r'/v2/',
 'wire service field':r'["\']service["\']\s*:|\bservice\s*:\s*["\']?Relay',
 'partner or mobile API vocabulary':r'\b(?:partner|mobile) API\b',
 'direct migration guide':r'/guides/linq-migration|Migrate from Linq',
 'mobile realtime or typing endpoint':r'/v1/realtime|/v1/client/realtime|/v1/chats/\{chatId\}/typing',
 'prefixed id':r'\b(?:msg|agt|usr|cnv|prt|att|evt|wh)_[A-Za-z0-9]',
 'uuidv4 example':r'\b[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b',
 'human kind':r'\bhumans?\b',
 'message parts table':r'\bmessage_parts?\b',
 'bootstrap':r'\bbootstrap\b',
 'receipt cursor':r'\breceipt[_ ]cursors?\b',
 'event ledger':r'\bevent ledgers?\b',
 'unsupported payments':r'\bpayments?\b',
 'unsupported edits':r'\b(?:edited|editing|edits?)\b',
 'unsupported unsend':r'\bunsend\b',
 'long polling':r'long[ -]poll',
 'invalid shell JSON':r'-d "\{(?!\\)'
}.items():
 if re.search(q,t,re.I):raise SystemExit(f'stale {n}')
print(f'validated {len(need)} pages, navigation, frontmatter, prose, and stale-contract bans')
