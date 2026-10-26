#!/usr/bin/env python3
"""R9's board feed between the protected input node and U9 in R8's reverse hot-plug model (REQUIREMENTS F9; R8 D76).

usage: <python3 with numpy> hotplug_feed_r9.py --rb MOHM [--json OUT]

R8's model (sources/r8_design/step9/hotplug_feed.py, unchanged, imported) integrates the input node A (C80 + C96, the
C89 + C95 / R166 damper, D8, R167; the harness lumped at J1) and U9's IN pin B (C88) behind the feed's series L_b /
R_b, over 384 corners, and reports how far B departs from A. R9 moves U9 to 14 mm from J1.1 and feeds it from the B.Cu
BAT_IN pour (no 15 mm lane), so only R_b (dc_solve BAT_IN J1:1 -> U9:5 on the R9 board, --rb) and L_b change. L_b
here: R9_FEED's three pieces by the model's own microstrip estimate (Inference, as in R8), plus R8's sweep values
(5 / 15 / 30 nH) as upper bounds. Every value but R_b and the part values is an Inference (R8 D76).
"""
import argparse
import importlib.util
import itertools
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('hotplug_feed', HERE.parents[1] / 'r8_design/step9/hotplug_feed.py')
H = importlib.util.module_from_spec(spec)
spec.loader.exec_module(H)

# R9's feed (r9_power.py BAT_IN_B / battery()): (piece, width mm, height to the GND reference mm, length mm)
#   the B.Cu pour band J1.1 -> Q120's drain corner (>= 4 mm wide; In2 under it is BAT_IN, the same net, so the GND
#   reference is In1: B.Cu mid-plane 1.5485 - In1 0.2530 = 1.2955 mm, the board's stack-up), the pour's finger to
#   C88 over In2 GND (B.Cu - In2 1.5485 - 1.3130 = 0.2355 mm), the 0.3 mm track C88.1 -> U9.5's bar end.
R9_FEED = (('B.Cu BAT_IN pour band', 4.0, 1.2955, 11.0), ('pour finger to C88', 1.0, 0.2355, 1.4),
           ('0.3 mm track C88.1 -> U9.5', 0.3, 0.2355, 1.2))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--rb', type=float, required=True, help='dc_solve BAT_IN J1:1 -> U9:5 on the R9 board, mOhm')
    ap.add_argument('--json')
    a = ap.parse_args()
    feed = [dict(piece=n, w=w, h=h, length=l, nH=round(float(H.microstrip_nh(w, h, l)), 3)) for n, w, h, l in R9_FEED]
    lb_est = sum(p['nH'] for p in feed)
    H.R_B = a.rb * 1e-3
    sweep = list(H.SWEEP)
    sweep[2] = (round(lb_est, 3) * 1e-9,) + tuple(sweep[2])
    cases = list(itertools.product(*sweep))
    p = {k: np.array([c[i] for c in cases]) for i, k in enumerate(H.KEYS)}
    a_min, b_min, a_slew, b_slew, ab = H.run(p)
    rows = [dict(lb_nH=round(c[2] * 1e9, 3), a_min=float(a_min[i]), b_min=float(b_min[i]), a_slew=float(a_slew[i]),
                 b_slew=float(b_slew[i])) for i, c in enumerate(cases)]
    by_lb = {lb: dict(extra_negative_V=round(max(x['a_min'] - x['b_min'] for x in rows if x['lb_nH'] == lb), 4),
                      slew_ratio=round(max(x['b_slew'] / x['a_slew'] for x in rows if x['lb_nH'] == lb), 4))
             for lb in sorted({x['lb_nH'] for x in rows})}
    out = dict(rb_mohm=a.rb, r8_rb_mohm=17.3, feed=feed, feed_estimate_nH=round(lb_est, 3), cases=len(rows),
               by_feed_nH=by_lb, lowest_a=round(min(x['a_min'] for x in rows), 3),
               lowest_b=round(min(x['b_min'] for x in rows), 3),
               fastest_b_V_per_us=round(max(x['b_slew'] for x in rows), 2))
    print(json.dumps(out, indent=1))
    if a.json:
        Path(a.json).write_text(json.dumps(out, indent=1) + '\n')


if __name__ == '__main__':
    main()
