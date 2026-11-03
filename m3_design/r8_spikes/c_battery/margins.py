#!/usr/bin/env python3
"""Spike 3(c) measured margins of the battery band against the pyro spacing rules (m3.kicad_dru A-H) and D18, on a
filled scratch board (KiCad Python). Same-layer edge-to-edge distances (DRC's view) for the rules; plan view for D18.

usage: <KiCad python3> -I margins.py BOARD
"""
import sys
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import check_r8  # noqa: E402

LIVE = {'PYRO1_BUS', 'PYRO1_IGN', 'PYRO1_OUT'}
CONTROL = {'PYRO1_GATE', 'PYRO1_GATE_N', 'ARM1_SENSE', 'PYRO1_CONT', 'PYRO1_COLD', 'PYRO1_CONT_MID', 'ARM1_SENSE_MID'}
RULES = [  # (name, minimum, net set A, net set B, pads only)
    ('E RAW_ACT to BUS/IGN', 1.0, {'RAW_ACT'}, {'PYRO1_BUS', 'PYRO1_IGN'}, False),
    ('A RAW_ACT to pyro control', 0.5, {'RAW_ACT'}, CONTROL, False),
    ('A2 RAW_ACT to RAW_ACT_SENSE', 0.3, {'RAW_ACT'}, {'RAW_ACT_SENSE'}, False),
    ('F BAT_IN/ACT_FET_S/ACT_GATE/ACT_DRV/ACT_EN to BUS/IGN/OUT', 0.5,
     {'BAT_IN', 'ACT_FET_S', 'ACT_GATE', 'ACT_DRV', 'ACT_EN', 'BAT_DAMP'}, LIVE, False),
    ('F RAW_ACT to OUT', 0.5, {'RAW_ACT'}, {'PYRO1_OUT'}, False),
    ('H live pads (RAW_ACT, BUS/IGN/OUT) to ACT_GATE/ACT_DRV pads', 1.0, {'RAW_ACT'} | LIVE, {'ACT_GATE', 'ACT_DRV'}, True),
    ('H RAW_ACT pads to sense/gate pads', 1.0, {'RAW_ACT'},
     {'ARM1_SENSE', 'PYRO1_CONT', 'RAW_ACT_SENSE', 'PYRO1_GATE', 'PYRO1_GATE_N'}, True),
    ('H RAW_ACT_SENSE_MID pads to gate pads', 1.0, {'RAW_ACT_SENSE_MID'},
     {'PYRO1_GATE', 'PYRO1_GATE_N', 'ACT_GATE', 'ACT_DRV'}, True),
]


def main(path):
    b = pcbnew.LoadBoard(path)
    for name, limit, na, nb, pads in RULES:
        a = check_r8.net_items(b, lambda n, s=na: n in s)
        c = check_r8.net_items(b, lambda n, s=nb: n in s)
        if pads:
            a = [i for i in a if isinstance(i[4], pcbnew.PAD)]
            c = [i for i in c if isinstance(i[4], pcbnew.PAD)]
        best = None
        for la, n1, lay1, s1, _ in a:
            for lc, n2, lay2, s2, _ in c:
                if lay1 != lay2:
                    continue
                if pads and la.split('.')[0] == lc.split('.')[0] and la.split('.')[0] in ('Q120', 'Q121', 'Q122', 'Q124'):
                    continue                        # rule H exempts each FET's own pads
                g = check_r8.min_gap(s1, s2, limit + 3.0)
                if g is not None and (best is None or g < best[0]):
                    best = (g, f'{la} ({n1}) to {lc} ({n2}) on {b.GetLayerName(lay1)}')
        verdict = 'none within reach' if best is None else ('OK' if best[0] >= limit - 1e-3 else 'FAIL')
        print(f'{name}: min {limit} mm; nearest {best[0]:.3f} mm, {best[1]}  {verdict}' if best else
              f'{name}: min {limit} mm; {verdict}')
    _, ev = check_r8.inner_power_pyro(b)
    print(f'D18 inner RAW_ACT/BAT_IN plan view to BUS/IGN/OUT: min 2.5 mm; nearest {ev["nearest"]}')


if __name__ == '__main__':
    main(sys.argv[1])
