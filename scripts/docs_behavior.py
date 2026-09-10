"""Check safety-critical documentation against its focused owning pages.

These checks complement (never replace) the unchanged Server OpenAPI digest,
operation/schema assertions, and example validators in validate-docs.py.
"""
import re


def validate_behavior(root):
    failures = []
    def read(*paths):
        return '\n'.join((root / path).read_text() for path in paths)

    def require(label, text, *patterns):
        normalized = ' '.join(text.replace('**', '').split())
        for pattern in patterns:
            if not re.search(pattern, normalized, re.I):
                failures.append(f'{label}: missing safety boundary {pattern}')

    share = read('guides/chats/share-contact-card.mdx')
    require('Contact Card sharing', share, r'/v1/chats/\{chatId\}/share_contact_card', r'existing Chat', r'empty request')
    card = read('guides/contact-cards.mdx')
    require('Contact Card configuration', card, r'relay\.contactCard\.create', r'relay\.contactCard\.update', r'/v1/contact_card', r'PATCH')
    requests = read('guides/contacts/message-requests.mdx')
    require('Message requests', requests, r'first Message.{0,20}is the request', r'message_requests_from', r'verified_agents', r'request_state', r'chat\.request\.updated', r'contact\.added', r'2030', r'2026', r'no request and no approval')

    receipts = read('guides/messaging/delivery-receipts.mdx')
    require('Delivered and Read', receipts, r'server.commit receipt', r'Read is optional', r'/v1/chats/\{chatId\}/read', r'Authorization: Bearer', r'transport only', r'not show.*labels in group Chats')
    uploads = read('guides/messaging/attachments.mdx')
    require('Upload attachments', uploads, r'relay\.attachments\.create', r'relay\.attachments\.upload', r'relay\.attachments\.retrieve', r'complete', r'--data-binary', r'Content-Type')
    imports = read('guides/messaging/import-media.mdx')
    require('Public URL import', imports, r'10 MiB \(10,485,760 bytes\)', r'DNS|resolved address', r'redirect', r'private', r'credentials')
    downloads = read('guides/messaging/receiving-media.mdx')
    require('Download attachments', downloads, r'relay\.attachments\.retrieve', r'60 minutes', r'Range:', r'206', r'416')
    require('Delete attachments', read('guides/messaging/delete-attachments.mdx'), r'relay\.attachments\.delete', r'owner', r'409', r'404')
    require('Attachment types', read('guides/messaging/attachment-types.mdx'), r'any (?:file type|valid MIME type)', r'application/octet-stream', r'nosniff', r'Content-Disposition', r'SVG', r'100 MiB \(104,857,600 bytes\)')

    signing = read('guides/webhooks/verify-signatures.mdx')
    require('Signature verification', signing, r'raw body', r'webhook-id', r'webhook-timestamp', r'webhook-signature', r'relay\.webhooks\.unwrap', r'HMAC-SHA256')
    receiver = read('guides/webhooks/index.mdx')
    require('Webhook receiver', receiver, r'commit.*before.*2xx', r'event_id', r'503', r'204')
    subscriptions = read('guides/webhooks/subscriptions.mdx')
    require('Subscription lifecycle', subscriptions, r'relay\.webhookSubscriptions\.create', r'signing_secret', r'HTTPS', r'first subscription', r'last subscription', r'event_id')
    delivery = read('guides/webhooks/delivery.mdx')
    require('Webhook delivery', delivery, r'10 seconds', r'up to 10', r'429', r'5xx', r'3xx', r'redirect.*not followed', r'localhost', r'private', r'link-local', r'event_id', r'terminal')

    socket = read('guides/websocket/index.mdx')
    require('WebSocket connect', socket, r'zero saved webhook subscriptions', r'Authorization: Bearer', r'relay\.websocket\.run', r'409', r'wss://')
    frames = read('guides/websocket/protocol.mdx')
    require('WebSocket frames', frames, r'4410', r'webhook_configured', r'revoked', r'heartbeat_timeout', r'restart', r'stale_connection', r'fatal error', r'30 seconds', r'60 seconds')
    ack = read('guides/websocket/acknowledgements.mdx')
    require('Durable acknowledgements', ack, r'cumulative', r'commit', r'through_sequence', r'event_id', r'ack_out_of_range')
    recovery = read('guides/websocket/full-sync.mdx')
    require('WebSocket recovery', recovery, r'full_sync_complete', r'checkpoint_outside_retention', r'30.day', r'every.*page', r'commit', r'full_sync_mismatch')
    observe = read('guides/websocket/observe-events.mdx')
    require('Non-consuming observer', observe, r'observe=true', r'observational', r'ack', r'full_sync_complete', r'reject')

    require('Typing', read('guides/chats/typing-indicators.mdx'), r'chat\.typing_indicator\.started', r'chat\.typing_indicator\.stopped', r'every 60 seconds', r'90 seconds')
    limits = read('guides/platform/rate-limits.mdx')
    require('Chat limits', limits, r'Other Contacts in `to` \| 6', r'Total active Contacts \| 7')
    membership = read('guides/chats/participants.mdx')
    require('Membership', membership, r'agent Contacts?', r'hide_history', r'false', r'earlier retained', r'participant\.added', r'participant\.removed', r'three active')
    idempotency = read('guides/platform/idempotency.mdx')
    require('Idempotency', idempotency, r'Idempotency-Key', r'255', r'different body.*409', r'unique constraint')

    # Explicitly stop previously incorrect wording from returning anywhere.
    all_pages = '\n'.join(p.read_text() for p in root.rglob('*.mdx') if 'node_modules' not in p.parts)
    for obsolete in [
        'marks the Message Delivered to the agent',
        'agent reaches Delivered after a webhook',
        'Media a user sends to you belongs to that user, so its URL cannot be refreshed',
        'relay.websocket.update',
    ]:
        if obsolete.lower() in ' '.join(all_pages.split()).lower():
            raise SystemExit(f'Stale documented behavior returned: {obsolete}')

    if failures:
        raise SystemExit('\n'.join(failures))
