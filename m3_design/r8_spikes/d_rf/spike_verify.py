#!/usr/bin/env python3
"""Spike (d) verification on a scratch board: the check_r8 / check_r7 parts that concern the RF strip and its buses,
DRC (kicad-cli) and route_check, each filtered to the spike's nets and parts.

usage: <KiCad python3> -I spike_verify.py board.kicad_pcb [--json out.json] [--no-drc] [--no-route]

The board must be filled (spike_base / rf_route_r8 fill natively). Nothing here weakens a check: each tool runs
unchanged on the whole board and only its findings are sorted into "spike" (an item of a spike net or a spike part
takes part) and "elsewhere" (other spikes' or later steps' work, e.g. unrouted nets of other families).
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(HERE))
import check_r8  # noqa: E402
import check_r7 as r7  # noqa: E402
import route_check as rc  # noqa: E402

CLI = os.environ.get('KICAD_CLI', '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli')
# the spike's nets: every radio / GNSS interface net (module side included), the module supplies and their 3V3 feeds'
# strip copper, the status LED nets (the camera status lines CAM_FAULT_N / CAM_PWR_EN are the camera family's; RESULT.md
# records the corridor this spike leaves them)
SPIKE_NET = re.compile(r'^(RADIO_(?!RF).*|GNSS_(?!RF_|ANT_|VCC_RF|LNA_EN).*|3V3_GNSS|3V3_RADIO|LED_.*)$')
SPIKE_PARTS = {'R305', 'R306', 'R307', 'R310', 'R311', 'R312', 'R313', 'R314', 'R315', 'C300', 'C301', 'FB30', 'FB31',
               'C310', 'C311', 'C312', 'LED1', 'LED2', 'R32', 'R33'}


def drc(board_path):
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / 'drc.json'
        subprocess.run([CLI, 'pcb', 'drc', '--format', 'json', '--severity-all', '--all-track-errors', '--output',
                        str(out), str(board_path)], capture_output=True, text=True)
        return json.loads(out.read_text())


def item_is_spike(it):
    d = it.get('description', '')
    m = re.search(r'\[([^\]]*)\]', d)
    net = m.group(1) if m else ''
    if SPIKE_NET.match(net):
        return True
    m = re.search(r'\b(?:of|on|Footprint) ([A-Z]+\d+)\b', d)
    return bool(m and m.group(1) in SPIKE_PARTS)


# The scratch project carries no footprint library table, so KiCad's library-link checks cannot run there; they are
# board-wide and unchanged from R7 (the real gate runs them in the project). Every other DRC type is classified.
LIB_ONLY = ('lib_footprint_issues', 'lib_footprint_mismatch')


def drc_split(report):
    spike, other = [], []
    for kind in ('violations', 'unconnected_items', 'schematic_parity'):
        for v in report.get(kind, []):
            if v.get('type') in LIB_ONLY:
                other.append(dict(kind=kind, type=v.get('type')))
                continue
            items = v.get('items', [])
            row = dict(kind=kind, type=v.get('type'), severity=v.get('severity'), description=v.get('description'),
                       items=[i.get('description') for i in items], pos=[i.get('pos') for i in items])
            if kind == 'unconnected_items':       # a ratsnest pair is the spike's only when its net is a spike net
                mine = any(SPIKE_NET.match((re.search(r'\[([^\]]*)\]', i.get('description', '')) or [None, ''])[1])
                           for i in items)
            else:
                mine = any(item_is_spike(i) for i in items)
            (spike if mine else other).append(row)
    return spike, other


REGION = (0.0, 0.0, 46.0, 46.0)     # the strip and the band up to U1's aft half: where pour findings are the spike's


def route(board_path):
    """route_check (profile r8, unchanged) on the whole board; its failures and unrecorded leftovers on spike nets,
    and pour findings (any net) inside REGION."""
    with tempfile.TemporaryDirectory() as tmp:
        rep = Path(tmp) / 'rc.json'
        proc = subprocess.run([sys.executable, '-I', str(ROOT / 'tools/route_check.py'), str(board_path), '--report',
                               str(rep)], capture_output=True, text=True)
        data = json.loads(rep.read_text())
    bad = data['failures'] + data['leftovers_missing']
    pour = ('pour_sliver', 'pour_finger', 'pad_pour_cut')

    def mine(d):
        if SPIKE_NET.match(d.get('net') or ''):
            return True
        x, y = d.get('x'), d.get('y')
        return d['cat'] in pour and x is not None and REGION[0] <= x <= REGION[2] and REGION[1] <= y <= REGION[3]
    spike = [d for d in bad if mine(d)]
    tail = [ln for ln in proc.stdout.splitlines() if ln.startswith('detour baseline') or 'routing hygiene:' in ln]
    return spike, len(bad) - len(spike), data, tail


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('board', type=Path)
    ap.add_argument('--json', type=Path)
    ap.add_argument('--no-drc', action='store_true')
    ap.add_argument('--no-route', action='store_true')
    args = ap.parse_args()
    bp = args.board.resolve()
    board = pcbnew.LoadBoard(str(bp))
    out = {}
    issues, ev = check_r8.rigid(board)
    out['rigid'] = dict(issues=issues, groups={k: v['sha256'][:16] for k, v in ev.items()})
    print('rigid groups:', 'OK (all 12 equal R7)' if not issues else issues)
    for name, fn in (('fence', check_r8.fence), ('rf_strip', check_r8.rf_strip),
                     ('rf_line_stitching', check_r8.rf_line_stitching), ('rf_separation', check_r8.rf_separation)):
        issues, ev = fn(board)
        out[name] = dict(issues=issues, evidence=ev)
        print(f'{name}:', 'OK' if not issues else f'{len(issues)} issue(s)')
        for i in issues:
            print('   ', i)
    for name, fn in (('rf_gnd_reach', r7.rf_gnd_reach), ('launch_reference', r7.launch_reference),
                     ('module_ground', r7.module_ground)):
        issues, ev = fn(board)
        out[name] = dict(issues=issues, evidence=ev)
        print(f'{name}:', 'OK' if not issues else issues)
    issues, ev = r7.rf_grounds(board, '')
    out['rf_grounds'] = dict(issues=issues, evidence=ev)
    print('rf_grounds:', 'OK' if not issues else issues)
    issues = check_r8.inner_signal(board)[0]
    out['inner_signal'] = issues
    print('inner_signal (S15/S16):', 'OK' if not issues else issues)
    if not args.no_drc:
        spike, other = drc_split(drc(bp))
        out['drc'] = dict(spike=spike, elsewhere_count=len(other),
                          elsewhere_types=sorted({(o['kind'], o['type']) for o in other}))
        print(f'DRC: {len(spike)} on spike nets/parts; {len(other)} elsewhere')
        for s in spike:
            print('   ', s['kind'], s['type'], '|', ' / '.join(s['items']))
    if not args.no_route:
        spike, n_other, data, tail = route(bp)
        nets = sorted({d['net'] for d in data['instances'] if SPIKE_NET.match(d.get('net') or '')})
        out['route_check'] = dict(spike=spike, elsewhere_count=n_other, info_on_spike_nets=[
            d for d in data['instances'] if SPIKE_NET.match(d.get('net') or '') and d not in data['failures']],
            detour_baseline=[r for r in data['detour_baseline'] if SPIKE_NET.match(r['net'])], tail=tail)
        print(f'route_check: {len(spike)} failing on spike nets / pours in the region; {n_other} elsewhere')
        for d in spike:
            print('   ', d['cat'], d['net'], d['layer'], (d['x'], d['y']))
        for r in out['route_check']['detour_baseline']:
            print('    D10 baseline:', r['net'], r['len_mm'], r['keepout_mst_mm'], r['keepout_ratio'])
    if args.json:
        args.json.write_text(json.dumps(out, indent=1, default=str) + '\n')


if __name__ == '__main__':
    main()
