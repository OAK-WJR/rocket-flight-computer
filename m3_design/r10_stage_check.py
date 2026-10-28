#!/usr/bin/env python3
"""Per-family build gate for M3-ASSY-R10 (m3_design/r10_build.sh; R10_DECISIONS D-R2-15).

usage: <KiCad python3> -I m3_design/r10_stage_check.py FAMILY [--board m3_design/assembly_review/m3.kicad_pcb]
       [--state STATE.json]

On a zone-filled copy of the board (in a temporary project beside the board's own m3.kicad_pro / m3.kicad_dru /
library tables; the board itself is not touched):
  DRC (kicad-cli, every severity, no schematic parity until the post stage): no violation of any type, but track /
      via ends left dangling, before `ground`, on the pending nets: GND and the rails whose planes (power family's
      In2 regions) or fan-out vias (ground family, r10_fanout.tsv) join them later;
  unconnected items: before `signals`, no more than after the previous family (--state carries the count); after
      `signals`, only on the pending nets; after `ground`, none;
  route_check --profile r10 (the empty-allowlist clean-routing gate): before `ground`, failing instances only on those
      pending nets, or critical_via_no_gnd (the GND partner vias come with the ground family's plane-via table);
      after `ground`, none.
Exit 0 when the family's gate holds.
"""
import argparse
import collections
import csv
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'm3_design'))
import r10_route  # noqa: E402

CLI = '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
FANOUT = ROOT / 'm3_design/r10_fanout.tsv'


def pending_nets():
    with FANOUT.open() as fh:
        rows = csv.DictReader((line for line in fh if not line.startswith('#')), delimiter='\t')
        return {'GND', '3V3', 'PORT_5V3', 'PORT_4V8', 'RAW_PROTECTED'} | {r['net'] for r in rows}


def net_of(item):
    m = re.search(r'\[([^\]]*)\]', item['description'])
    return m.group(1) if m else None


def main():
    import os
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('family', choices=r10_route.FAMILIES)
    ap.add_argument('--board', type=Path, default=ROOT / 'm3_design/assembly_review/m3.kicad_pcb')
    ap.add_argument('--state', type=Path)
    a = ap.parse_args()
    cli = os.environ.get('KICAD_CLI', CLI)
    board = a.board.resolve()
    final = a.family == 'ground'
    pending = set() if final else pending_nets()
    issues = []
    with tempfile.TemporaryDirectory(prefix='r10_stage_') as tmp:
        t = Path(tmp)
        for name in ('m3.kicad_pro', 'm3.kicad_dru', 'fp-lib-table', 'sym-lib-table'):
            shutil.copy2(board.parent / name, t / name)
        (t / 'kilib').symlink_to(board.parent / 'kilib')
        b = pcbnew.LoadBoard(str(board))
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
        assert pcbnew.SaveBoard(str(t / 'm3.kicad_pcb'), b, True)
        subprocess.run([cli, 'pcb', 'drc', '--severity-all', '--format', 'json', '-o', str(t / 'drc.json'),
                        str(t / 'm3.kicad_pcb')], check=True, capture_output=True)
        drc = json.loads((t / 'drc.json').read_text())
        rc = subprocess.run([sys.executable, '-I', str(ROOT / 'tools/route_check.py'), str(t / 'm3.kicad_pcb'),
                             '--profile', 'r10', '--report', str(t / 'route.json')], capture_output=True, text=True)
        route = [line for line in rc.stdout.splitlines() if line.startswith('FAIL ')]
    viol = collections.Counter()
    for v in drc['violations']:
        net = net_of(v['items'][0])
        if not final and v['type'] in ('track_dangling', 'via_dangling') and net in pending:
            continue
        viol[(v['type'], net)] += 1
    if viol:
        issues.append(f'DRC: {sum(viol.values())} violations {dict(viol)}')
    unconnected = collections.Counter(net_of(u['items'][0]) for u in drc['unconnected_items'])
    total = sum(unconnected.values())
    previous = None
    if a.state and a.state.is_file():
        previous = json.loads(a.state.read_text()).get('unconnected')
    if final and total:
        issues.append(f'{total} unconnected items after the ground family: {dict(unconnected)}')
    elif a.family == 'signals' and set(unconnected) - pending:
        issues.append(f'unconnected nets after signals beyond the ground family\'s: '
                      f'{sorted(set(unconnected) - pending)}')
    elif previous is not None and total > previous:
        issues.append(f'unconnected items rose from {previous} to {total}')
    # before `ground`, a layer change's GND partner may still be pending: the ground family places the plane-via table
    # (r10_fanout.tsv) that the R10 port nets' critical_via_no_gnd test counts (R3-RTE-01); after `ground` it is final
    later = () if final else ('FAIL critical_via_no_gnd ',)
    bad = [line for line in route if final or not (any(f' {n} ' in line for n in pending) or line.startswith(later))]
    if bad:
        issues.append(f'route_check: {len(bad)} failing instances outside the pending nets, e.g. {bad[:3]}')
    if a.state:
        a.state.write_text(json.dumps(dict(family=a.family, unconnected=total)) + '\n')
    print(f'r10_stage_check {a.family}: DRC {len(drc["violations"])} items ({sum(viol.values())} counted), '
          f'unconnected {total} in {len(unconnected)} nets, route_check {len(route)} failing '
          f'({len(bad)} outside pending nets): {"OK" if not issues else "FAIL"}')
    for i in issues:
        print('  FAIL', i)
    return 1 if issues else 0


if __name__ == '__main__':
    raise SystemExit(main())
