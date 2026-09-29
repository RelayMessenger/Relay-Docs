#!/usr/bin/env python3
"""Run every leaf of npm validate, retaining failures and per-gate receipts.

Uses existing tools only (npm offline/no install approval). No publish, push,
registry refresh, hosted browser proof, or deploy command is part of validate.
"""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'node_modules/.cache/selection-review'
OUT.mkdir(parents=True, exist_ok=True)
scripts = json.loads((ROOT / 'package.json').read_text())['scripts']


def leaves(command):
    for part in command.split(' && '):
        if part.startswith('npm run '):
            yield from leaves(scripts[part.removeprefix('npm run ')])
        else:
            yield part


env = {**os.environ, 'npm_config_offline': 'true', 'npm_config_yes': 'false',
       'NO_COLOR': '1'}
results = []
for i, command in enumerate(leaves(scripts['validate']), 1):
    log = OUT / f'{i:02d}.log'
    contracts = {p: p.read_bytes() for p in (ROOT / 'api-reference').glob('openapi*.yaml')}
    start = time.monotonic()
    with log.open('w') as output:
        output.write(f'$ {command}\n'); output.flush()
        process = subprocess.Popen(command, shell=True, cwd=ROOT, env=env,
                                   stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            code = process.wait(timeout=180)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            code = 124
            output.write('\nTIMEOUT after 180 seconds\n')
    # The reproducibility gate rebuilds its inputs. Keep that evidence but
    # never promote generated contract changes as a side effect of validation.
    for path, before in contracts.items():
        if path.read_bytes() != before:
            (OUT / ('generated-' + path.name)).write_bytes(path.read_bytes())
            path.write_bytes(before)
    results.append({'command': command, 'exit_code': code, 'log': str(log),
                    'seconds': round(time.monotonic() - start, 2)})
    (OUT / 'validation-results.json').write_text(json.dumps(results, indent=2) + '\n')
    print(f'{i:02d} {"PASS" if code == 0 else "FAIL"} {command} ({code})', flush=True)
summary = '\n'.join(f'{r["exit_code"]:3} {r["command"]} -> {r["log"]}' for r in results)
(OUT / 'validation-summary.txt').write_text(summary + '\n')
sys.exit(any(r['exit_code'] for r in results))
