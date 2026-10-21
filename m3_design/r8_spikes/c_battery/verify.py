#!/usr/bin/env python3
"""Spike 3(c) checks on a filled scratch board (KiCad Python): check_r8's rigid hash groups (D11 / D15), D18 inner
power near pyro live copper, D20 inner signal, and the spike nets' route_check failures from a --report JSON.

usage: <KiCad python3> -I verify.py BOARD [ROUTE_REPORT.json]
"""
import json
import sys
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import check_r8  # noqa: E402

SPIKE_NETS = {'BAT_IN', 'BAT_DAMP', 'ACT_FET_S', 'RAW_ACT', 'ACT_GATE', 'ACT_DRV', 'ACT_EN', 'BAT_SW_SOURCE',
              'BAT_SW_RETURN', 'RAW_ACT_SENSE_MID'}
BAND = (0.0, 66.5, 46.0, 118.0)
sys.path.insert(0, str(Path(__file__).resolve().parent))
from battery import PLACE  # noqa: E402
BAND_PARTS = set(PLACE)


def main(path, route=None):
    b = pcbnew.LoadBoard(path)
    bad = 0
    issues, ev = check_r8.rigid(b)
    for k, v in ev.items():
        print(f'rigid {k:18s} {v["items"]:4d} items {v["sha256"][:16]} '
              f'{"OK" if v["sha256"] == check_r8.RIGID_BASELINE[k] else "DIFFERS"}')
    bad += len(issues)
    issues, ev = check_r8.inner_power_pyro(b)
    print(f'D18 inner RAW_ACT/BAT_IN vs PYRO1_BUS/IGN/OUT: {len(issues)} issues; nearest {ev["nearest"]}')
    for i in issues:
        print('  ' + i)
    bad += len(issues)
    r7 = check_r8.r7
    copper = r7.copper_shapes(b)
    for name, (found, n) in (('vias_in_smd_pads (M2)', r7.vias_in_smd_pads(b)),
                             ('foreign_clearances (bare TPs 1.0 mm, RAW_ACT pins 0.3 mm)', r7.foreign_clearances(b, copper)),
                             ('overlap_only_joints', r7.overlap_only_joints(b, copper))):
        mine = [i for i in found if any(t in i for t in SPIKE_NETS) or any(f'{r}.' in i or f'{r} ' in i for r in BAND_PARTS)]
        print(f'{name}: {len(found)} board-wide, {len(mine)} on spike nets / band parts')
        for i in mine:
            print('  ' + i)
        bad += len(mine)
    found = r7.vias_on_through_pads(b)
    print(f'vias_on_through_pads: {len(found)}')
    bad += len(found)
    issues, ev = check_r8.inner_signal(b)
    print(f'D20 inner signal tracks: {ev}; issues {len(issues)}')
    for i in issues:
        print('  ' + i)
    if route:
        d = json.load(open(route))
        mine = [f for f in d['failures'] if f['net'] in SPIKE_NETS or
                (f['net'] == 'GND' and BAND[0] <= f.get('x', -1) <= BAND[2] and BAND[1] <= f.get('y', -1) <= BAND[3])]
        print(f'route_check failures on spike nets / band GND: {len(mine)}')
        for f in mine:
            print('  ', f)
        bad += len(mine)
        info = [i for i in d['instances'] if i['net'] in SPIKE_NETS]
        print(f'route_check instances (any, info included) on spike nets: {len(info)}')
        for i in info:
            print('  ', i)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(*sys.argv[1:3]))
