#!/usr/bin/env python3
"""What R8's board feed between the protected input node and U9 adds to a reverse hot-plug (REQUIREMENTS F9).

usage: python3 hotplug_feed.py [--json OUT]           (needs numpy; every case is integrated at once)

The R4 hot-plug model (docs/M3_R4.md X1 / Y1 / Y8, its section 5 table) lumps the harness (0.1-2 uH, >= 0.03 ohm) into
one input node that holds C80 + C96, the C89 + C95 / R166 damper, D8 and U9's IN pin, and found U9 IN >= -14.6 V and
<= 9.2 V/us for a reversed 2S pack plugged onto <= 2.0 V left on the input (TPS25947: -15 V, 10 V/us). That model and
its DC-bias data are not in the repository. R8 puts D8, C80, C96, the damper and R167 within 3.9-10.6 mm of J1.1 (centre to
nearest pad centre; 1.9-7.8 mm pad edge to pad edge, R8P3-POWER-04: one node, the model's premise) and U9 27 mm away on the BAT_IN feed, with C88 (100 nF) at U9's IN pin (D36).

This script does not re-derive the R4 figures. It answers the narrower question the re-placement raises: how far U9's
IN pin, behind the feed's series inductance and resistance, departs from the input node the R4 model describes. A
linear two-node circuit is integrated (RK4, 0.5 ns steps, 150 us):

    pack -L_h-R_h- node A [C_A = C80 + C96; C_d + R166 damper; D8 (bidirectional, soft knee); R167] -L_b-R_b- node B [C88]

with constant (derated) capacitances, which is not the R4 model's voltage-dependent one: the absolute minima here are
not the qualification figures, only the B - A differences are used. Sweep: harness 0.1 / 0.5 / 1 / 2 uH at 0.03 /
0.1 ohm; feed L_b 5 / 15 / 30 nH (an upper bound for about 30 mm of 0.5 mm track and two vias over In2 GND (its first
2.1 mm crossed the In2 BAT_IN island until fix pass 2, D97) and In1 GND, Inference); C_A 9.4 (47 % of 20 uF, pass-4 DC-bias figure at 8.4 V) and 20 uF; C_d 16.7 (38 % of 44 uF) and
44 uF; C88 50 and 100 nF; D8 breakdown 12.65 V (-40 C) and 13.3 V, 0.2 ohm above it (SMBJ12CA: 19.9 V at 30 A).
R_b 17.3 mOhm is the dc_solve figure BAT_IN J1:1 -> U9:5 (R8_DECISIONS D49). Every value but R_b and the part
values is an Inference.
"""
import argparse
import itertools
import json

import numpy as np

PACK = -8.4            # V, a reversed 2S pack
V0 = 2.0               # V left on the input (R167 brings it there within 0.73 s; F9 rule: 2 s, TP80 < 1 V)
R_DAMP, R167, R_B = 0.33, 10e3, 17.3e-3
DT, T_END = 0.5e-9, 150e-6
KEYS = ('lh', 'rh', 'lb', 'ca', 'cd', 'cb', 'vbr')
SWEEP = ((0.1e-6, 0.5e-6, 1e-6, 2e-6), (0.03, 0.1), (5e-9, 15e-9, 30e-9), (9.4e-6, 20e-6), (16.7e-6, 44e-6),
         (50e-9, 100e-9), (12.65, 13.3))


def microstrip_nh(w, h, length, er=4.4):
    """Series inductance (nH) of a microstrip of width w over a plane h below it, length in mm (Hammerstad's Z0 and
    effective permittivity for w/h >= 1; L' = Z0 sqrt(eps_eff) / c). An estimate, not a field solve (Inference)."""
    u = w / h
    eeff = (er + 1) / 2 + (er - 1) / 2 / (1 + 12 / u) ** 0.5
    z0 = 120 * np.pi / (eeff ** 0.5 * (u + 1.393 + 0.667 * np.log(u + 1.444)))
    return z0 * eeff ** 0.5 / 299792458.0 * length * 1e6


# The R8 feed (measured on board 429b6db4): B.Cu 0.5 mm along x 41.25 from the BAT_IN B.Cu pour edge (41.25, 102.4)
# to (41.25, 87.6), then 0.3 mm for 0.9 mm into U9.5, over In2 GND (prepreg 0.203 mm) the whole way; no series via.
FEED = (('0.5 mm lane', 0.5, 14.8), ('0.3 mm pad entry', 0.3, 0.9))


def d8(v, vbr, rdyn=0.2, knee=0.1):
    """Bidirectional TVS current (A) at voltage v: soft-knee piecewise-linear above |v| = vbr."""
    x = (np.abs(v) - vbr) / knee
    return np.sign(v) * knee / rdyn * np.logaddexp(0.0, x)


def run(p):
    """Integrate every case of p (dict of equal-length arrays) together; return per-case extremes."""
    lh, rh, lb, ca, cd, cb, vbr = (p[k] for k in KEYS)
    n = lh.size
    s = np.array([np.zeros(n), np.full(n, V0), np.full(n, V0), np.zeros(n), np.full(n, V0)])

    def f(s):
        ih, va, vcd, ib, vb = s
        idamp = (va - vcd) / R_DAMP
        return np.array([(PACK - rh * ih - va) / lh,
                         (ih - idamp - ib - d8(va, vbr) - va / R167) / ca,
                         idamp / cd,
                         (va - R_B * ib - vb) / lb,
                         ib / cb])

    a_min, b_min = np.full(n, V0), np.full(n, V0)
    a_slew, b_slew, ab = np.zeros(n), np.zeros(n), np.zeros(n)
    for _ in range(int(round(T_END / DT))):
        k1 = f(s)
        k2 = f(s + DT / 2 * k1)
        k3 = f(s + DT / 2 * k2)
        k4 = f(s + DT * k3)
        new = s + DT / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
        a_slew = np.maximum(a_slew, np.abs(new[1] - s[1]) / DT / 1e6)       # V/us
        b_slew = np.maximum(b_slew, np.abs(new[4] - s[4]) / DT / 1e6)
        s = new
        a_min, b_min = np.minimum(a_min, s[1]), np.minimum(b_min, s[4])
        ab = np.maximum(ab, np.abs(s[4] - s[1]))
    assert np.all(np.isfinite(s)), 'non-finite state'
    return a_min, b_min, a_slew, b_slew, ab


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--json')
    a = ap.parse_args()
    cases = list(itertools.product(*SWEEP))
    p = {k: np.array([c[i] for c in cases]) for i, k in enumerate(KEYS)}
    a_min, b_min, a_slew, b_slew, ab = run(p)
    rows = [dict(lh_uH=c[0] * 1e6, rh=c[1], lb_nH=round(c[2] * 1e9), ca_uF=round(c[3] * 1e6, 1),
                 cd_uF=round(c[4] * 1e6, 1), cb_nF=round(c[5] * 1e9), vbr=c[6], a_min=round(float(a_min[i]), 3),
                 b_min=round(float(b_min[i]), 3), a_slew=round(float(a_slew[i]), 2), b_slew=round(float(b_slew[i]), 2),
                 ab_max=round(float(ab[i]), 3)) for i, c in enumerate(cases)]
    feed_nh = sum(microstrip_nh(w, 0.203, length) for _, w, length in FEED)
    by_lb = {lb: dict(extra_negative_V=round(max(x['a_min'] - x['b_min'] for x in rows if x['lb_nH'] == lb), 3),
                      slew_ratio=round(max(x['b_slew'] / x['a_slew'] for x in rows if x['lb_nH'] == lb), 3))
             for lb in sorted({x['lb_nH'] for x in rows})}
    summary = dict(cases=len(rows), feed_estimate_nH=round(float(feed_nh), 2), by_feed_nH=by_lb,
                   worst_extra_negative_V=round(float(np.max(a_min - b_min)), 3),
                   worst_extra_slew_V_per_us=round(float(np.max(b_slew - a_slew)), 3),
                   max_instant_b_minus_a_V=round(float(np.max(ab)), 3),
                   lowest_b=min(rows, key=lambda x: x['b_min']), fastest_b=max(rows, key=lambda x: x['b_slew']),
                   lowest_a=min(rows, key=lambda x: x['a_min']))
    print(json.dumps(summary, indent=1))
    if a.json:
        json.dump(dict(summary=summary, rows=rows), open(a.json, 'w'), indent=0)


if __name__ == '__main__':
    main()
