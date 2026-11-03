#!/usr/bin/env python3
"""Per-family build gate for M3-ASSY-R11 (m3_design/r11_build.sh; r11_plan.md section 4, stage C).

usage: <KiCad python3> -I -B m3_design/r11_stage_check.py FAMILY [--board m3_design/r11/m3.kicad_pcb]
       [--state STATE.json] [--report OUT.json]

A family is "done" once it and every family before it in r11_route.FAMILIES have run; its nets are its module's NETS.
The pending nets are every other net: the nets of the families still to come (and of families whose module does not
exist yet), GND and the rails whose planes come later. On a zone-filled copy of the board (a temporary project beside
the board's own m3.kicad_pro / m3.kicad_dru / library tables; the board itself is not touched):
  DRC (kicad-cli, every severity, no schematic parity until the post stage): no violation of any type, except track /
      via ends left dangling on pending nets (a fan-out via waiting for its family, a GND via waiting for the planes);
  unconnected items: never more than after the previous family (--state carries the count); after `ground`, none;
  route_check --profile r11 (the empty-allowlist clean-routing gate): failing instances only on pending nets; after
      `ground`, none at all.
A family whose module does not exist yet is skipped (exit 0, state unchanged), except `ground`, the last: with nets
still pending the final gate cannot pass, so it reports them and fails only when --final is given.
Exit 0 when the family's gate holds.
"""
import argparse
import collections
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'm3_design'))
import r11_route  # noqa: E402

CLI = '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'


def done_nets(family):
    out = set()
    for f in r11_route.FAMILIES[:r11_route.FAMILIES.index(family) + 1]:
        out |= set(r11_route.family_nets(f))
    return out


def net_of(item):
    m = re.search(r'\[([^\]]*)\]', item['description'])
    return m.group(1) if m else None


def route_failures(stdout):
    """(category, net, line) of every FAIL line of route_check."""
    out = []
    for line in stdout.splitlines():
        if line.startswith('FAIL '):
            parts = line.split()
            out.append((parts[1], parts[2] if len(parts) > 2 else '', line))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('family', choices=r11_route.FAMILIES)
    ap.add_argument('--board', type=Path, default=r11_route.PROJECT / 'm3.kicad_pcb')
    ap.add_argument('--state', type=Path)
    ap.add_argument('--report', type=Path)
    ap.add_argument('--final', action='store_true', help='fail when `ground` is reached with nets still pending')
    a = ap.parse_args()
    if not r11_route.implemented(a.family) and a.family != 'ground':
        print(f'r11_stage_check {a.family}: family not written yet; skipped')
        return 0
    cli = os.environ.get('KICAD_CLI', CLI)
    board = a.board.resolve()
    b = pcbnew.LoadBoard(str(board))
    nets = {n for n in b.GetNetsByName().keys() if n and not str(n).startswith('unconnected-')}
    nets = {str(n) for n in nets}
    done = done_nets(a.family)
    pending = nets - done
    final = a.family == 'ground' and r11_route.implemented('ground')
    if a.family == 'ground' and not final:
        print(f'r11_stage_check ground: family not written yet; {len(pending)} nets pending: '
              f'{"FAIL" if a.final else "skipped"}')
        return 1 if a.final else 0
    if final:
        pending = set()
    issues = []
    with tempfile.TemporaryDirectory(prefix='r11_stage_') as tmp:
        t = Path(tmp)
        for name in ('m3.kicad_pro', 'm3.kicad_dru', 'fp-lib-table', 'sym-lib-table'):
            shutil.copy2(board.parent / name, t / name)
        (t / 'kilib').symlink_to(board.parent / 'kilib')
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
        assert pcbnew.SaveBoard(str(t / 'm3.kicad_pcb'), b, True)
        subprocess.run([cli, 'pcb', 'drc', '--severity-all', '--format', 'json', '-o', str(t / 'drc.json'),
                        str(t / 'm3.kicad_pcb')], check=True, capture_output=True)
        drc = json.loads((t / 'drc.json').read_text())
        rc = subprocess.run([sys.executable, '-I', '-B', str(ROOT / 'tools/route_check.py'), str(t / 'm3.kicad_pcb'),
                             '--profile', 'r11', '--report', str(t / 'route.json')], capture_output=True, text=True)
        route = route_failures(rc.stdout)
        if rc.returncode not in (0, 1) or 'routing hygiene:' not in rc.stdout:
            issues.append(f'route_check did not run: {rc.stderr.strip()[-400:]}')
    viol = collections.Counter()
    for v in drc['violations']:
        net = net_of(v['items'][0])
        if v['type'] in ('track_dangling', 'via_dangling') and net in pending:
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
    elif previous is not None and total > previous:
        issues.append(f'unconnected items rose from {previous} to {total}')
    stray = sorted(set(unconnected) & done)
    if stray and not final:
        issues.append(f'unconnected items on finished nets: {stray}')
    bad = [line for cat, net, line in route if final or net not in pending]
    if bad:
        issues.append(f'route_check: {len(bad)} failing instances outside the pending nets, e.g. {bad[:4]}')
    if a.state:
        a.state.write_text(json.dumps(dict(family=a.family, unconnected=total)) + '\n')
    if a.report:
        a.report.write_text(json.dumps(dict(family=a.family, done=sorted(done), pending=len(pending),
                                            drc_counted=[list(k) + [n] for k, n in viol.items()],
                                            unconnected=dict(unconnected), route_bad=bad,
                                            route_pending=len(route) - len(bad), issues=issues), indent=1) + '\n')
    print(f'r11_stage_check {a.family}: DRC {len(drc["violations"])} items ({sum(viol.values())} counted), '
          f'unconnected {total} in {len(unconnected)} nets, route_check {len(route)} failing '
          f'({len(bad)} outside pending nets), {len(done)} nets done: {"OK" if not issues else "FAIL"}')
    for i in issues:
        print('  FAIL', i)
    return 1 if issues else 0


if __name__ == '__main__':
    raise SystemExit(main())
