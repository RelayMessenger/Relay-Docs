"""Verify an independently pinned release or explicitly labeled local candidate.

The optional local record names an SDK checkpoint, never a hosted release.
RELAY_OPENAPI_SOURCE may supply independent bytes, but cannot bypass the pin.
"""
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path


def verify_contract_source(root: Path, released_sha256: str) -> None:
    canonical = (root / 'api-reference/openapi.yaml').read_bytes()
    record_path = root / 'scripts/local-contract-source.json'
    expected = released_sha256
    if record_path.exists():
        record = json.loads(record_path.read_text())
        assert record['status'] == 'local-candidate-not-published', 'Candidate provenance must stay explicit'
        assert record['repository'] == 'Relay-SDK'
        assert record['path'] == 'contracts/relay-v1-openapi.yaml'
        assert re.fullmatch(r'[0-9a-f]{40}', record['commit']), 'Invalid SDK checkpoint'
        assert re.fullmatch(r'[0-9a-f]{64}', record['sha256']), 'Invalid contract hash'
        expected = record['sha256']
        state = record.get('source_state', 'checkpoint')
        assert state in ('checkpoint', 'committed', 'working-tree'), 'Invalid local source state'
        if state == 'committed':
            assert 'checkpoint_sha256' not in record, 'Committed provenance must pin its own blob, not a historical base'
        checkpoint_sha256 = expected
        if state == 'working-tree':
            checkpoint_sha256 = record['checkpoint_sha256']
            assert re.fullmatch(r'[0-9a-f]{64}', checkpoint_sha256), 'Invalid checkpoint hash'
        # An uncommitted candidate names its base separately, never pretending
        # the old immutable commit contains the new bytes. Never fetch or use origin.
        sdk = root.parent / 'sdk'
        if (sdk / '.git').exists():
            independent = subprocess.check_output(
                ['git', 'show', f"{record['commit']}:{record['path']}"], cwd=sdk)
            assert hashlib.sha256(independent).hexdigest() == checkpoint_sha256, 'SDK checkpoint differs from provenance'
        if state == 'working-tree' and (sdk / record['path']).exists():
            assert canonical == (sdk / record['path']).read_bytes(), 'Docs contract differs from canonical SDK working tree'
    assert hashlib.sha256(canonical).hexdigest() == expected, 'Docs contract differs from recorded independent source'
    local = os.environ.get('RELAY_OPENAPI_SOURCE')
    if local:
        assert canonical == Path(local).read_bytes(), 'Docs contract differs from explicit local source'
