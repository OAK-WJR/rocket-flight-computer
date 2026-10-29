#!/usr/bin/env python3
"""R8 spike (a) verification on a scratch board (KiCad Python).

usage: <KiCad python3> -I spike_verify.py BOARD [--drc DRC.json] [--rc RC.json] [--pads OUT.json] [--fallback]

  rigid   check_r8.rigid(): the 12 rigid groups against the R7 baseline digests (must all match)
  drc     kicad-cli DRC report (made by run_verify.sh) filtered to the spike's nets and parts
  rc      route_check --report filtered to the spike's nets (failures, leftovers missing a reason)
  pads    pad centres of the spike's parts (for designing the geometry tables)
exit 0 = rigid OK, 0 DRC items and 0 gated route_check items on the spike's nets and parts
"""
import argparse
import json
import re
import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / 'tools'))
sys.path.insert(0, str(HERE))
import check_r8                                                # noqa: E402
import spike_geom as G                                         # noqa: E402

mm = pcbnew.ToMM


SILK = ('silk_over_copper', 'silk_overlap', 'silk_edge_clearance', 'lib_footprint_issues', 'lib_footprint_mismatch')


def drc_items(path, nets, parts):
    """DRC items on the spike: every violation naming a spike net or part (silkscreen and library-link items are
    reported apart: silkscreen is the post step's, and the scratch project has no footprint library table), and every
    unconnected item on a spike net (power rails are routed by later families, so their ratsnest is not counted)."""
    rep = json.loads(Path(path).read_text())
    out, silk = [], []
    for sect in ('violations', 'unconnected_items', 'schematic_parity'):
        for v in rep.get(sect, []):
            text = ' | '.join(i.get('description', '') for i in v.get('items', []))
            on_net = any(re.search(r'\[' + re.escape(n) + r'\]', text) for n in nets)
            on_part = any(re.search(r'\b' + re.escape(p) + r'\b', text) for p in parts)
            hit = on_net if sect == 'unconnected_items' else (on_net or on_part)
            if not hit:
                continue
            row = (sect, v.get('type'), v.get('severity'), v.get('description'), text,
                   [(i.get('pos', {}).get('x'), i.get('pos', {}).get('y')) for i in v.get('items', [])])
            (silk if v.get('type') in SILK else out).append(row)
    return out, silk, {k: len(rep.get(k, [])) for k in ('violations', 'unconnected_items')}


def rc_items(path, nets):
    rep = json.loads(Path(path).read_text())
    fail = [d for d in rep.get('failures', []) if d.get('net') in nets]
    miss = [d for d in rep.get('leftovers_missing', rep.get('missing', [])) if d.get('net') in nets]
    inst = [d for d in rep.get('instances', []) if d.get('net') in nets]
    return fail, miss, inst, rep


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('board', type=Path)
    ap.add_argument('--drc', type=Path)
    ap.add_argument('--rc', type=Path)
    ap.add_argument('--pads', type=Path)
    ap.add_argument('--fallback', action='store_true')
    a = ap.parse_args()
    b = pcbnew.LoadBoard(str(a.board))
    ok = True
    issues, ev = check_r8.rigid(b)
    print('RIGID', 'OK' if not issues else 'FAIL', {k: v['sha256'][:12] for k, v in ev.items()})
    for i in issues:
        print('  ', i)
    ok &= not issues
    nets, parts = (G.FALLBACK_NETS, G.FALLBACK_PARTS) if a.fallback else (G.NETS, G.PARTS)
    if a.pads:
        fps = {f.GetReference(): f for f in b.GetFootprints()}
        out = {}
        for r in sorted(set(parts) | {'U1', 'J2'}):
            f = fps[r]
            out[r] = dict(pos=[round(mm(f.GetPosition().x), 4), round(mm(f.GetPosition().y), 4)],
                          rot=f.GetOrientationDegrees(), side='B' if f.IsFlipped() else 'F',
                          pads={p.GetNumber(): [round(mm(p.GetPosition().x), 4), round(mm(p.GetPosition().y), 4),
                                                p.GetNetname()] for p in f.Pads() if p.GetNumber()})
        a.pads.write_text(json.dumps(out, indent=1))
    if a.drc:
        items, silk, totals = drc_items(a.drc, nets, parts)
        print('DRC on spike nets/parts:', len(items), '(silkscreen/library items, not gated:', len(silk),
              '; board totals', totals, ')')
        for it in items:
            print('  ', it[0], it[1], it[2], '|', it[4], it[5])
        ok &= not items
    if a.rc:
        fail, miss, inst, rep = rc_items(a.rc, nets)
        print('ROUTE_CHECK on spike nets: failures', len(fail), 'leftovers without reason', len(miss),
              'instances (all categories)', len(inst))
        for d in fail + miss:
            print('  ', d.get('cat'), d.get('net'), d.get('layer'), d.get('x'), d.get('y'), d.get('detail', ''))
        info = sorted({(d.get('cat'), d.get('net')) for d in inst if d not in fail and d not in miss})
        if info:
            print('   info-only:', info)
        ok &= not fail and not miss
    print('SPIKE', 'PASS' if ok else 'FAIL')
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
