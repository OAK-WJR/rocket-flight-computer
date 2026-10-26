#!/usr/bin/env python3
"""Bind a tool report that does not name its board to the board it was run on (R9_DECISIONS D-S10-01).

usage: python3 bind_report.py BOARD.kicad_pcb IN OUT [--note TEXT]

A JSON object gets a `board_sha256` field (and `bound_by` naming this script); any other file gets a first line
`# <BOARD> sha256 <hex>[ (TEXT)]`. Local absolute paths inside the report are replaced by `<repo>` (AGENTS §4).
The caller runs the tool on BOARD and passes its output straight here, so the hash is the board the tool read.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('board', type=Path)
    ap.add_argument('inp', type=Path)
    ap.add_argument('out', type=Path)
    ap.add_argument('--note', default='')
    a = ap.parse_args()
    digest = hashlib.sha256(a.board.read_bytes()).hexdigest()
    text = a.inp.read_text().replace(str(ROOT), '<repo>')
    try:
        data = json.loads(text)
    except ValueError:
        data = None
    if isinstance(data, dict):
        data['board_sha256'] = digest
        data['bound_by'] = 'step10/bind_report.py'
        a.out.write_text(json.dumps(data, indent=1) + '\n')
    else:
        note = f' ({a.note})' if a.note else ''
        a.out.write_text(f'# {a.board.as_posix()} sha256 {digest}{note}\n' + text)
    print(f'{a.out}: bound to {digest[:12]}')


if __name__ == '__main__':
    main()
