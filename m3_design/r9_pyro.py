#!/usr/bin/env python3
"""Build the R9 CH1 pyro column copper (M3-ASSY-R9, build step 5) on the step-4 board.

usage: <KiCad python3> -I m3_design/r9_pyro.py [--board m3_design/assembly_review/m3.kicad_pcb] [--out OUT]
       design aid (r9_build.sh never passes it): --no-fill

r9_plan.md section 4 step 5; R9_OWNER_DECISIONS.md items 1-2; R9_DECISIONS.md D-S5-*. The board is rebuilt in place
(the project's m3.kicad_pro and m3.kicad_dru apply while it is filled). Every point below is derived from pad
centres (pad-referenced): the copper is a template of the CH1 column that follows its parts, and the relations it
relies on (a bar straight between two pads, a 45-degree run landing on a pad) are asserted, so a placement change
that breaks one stops the build instead of drawing a bent bar.

The step draws every CH1 net whole, from the terminals to U1's pins (D-S5-07): PYRO1_BUS / IGN / OUT (the fire loop),
PYRO1_GATE, PYRO1_GATE_N, PYRO1_CONT, PYRO1_CONT_MID, PYRO1_CONT_MCU, PYRO1_COLD, ARM1_SENSE, ARM1_SENSE_MID,
ARM1_SENSE_MCU, plus the CH1 column's own GND copper (Q124's source return, the GATE_N guard, TP122's GND partner) and
D120's 3V3 feed out of the column. RAW_ACT (J124.2's feed, step 6), the GND pours and stitching of the small parts'
GND pads (step 8) and every other net are later steps'.

  fire loop   F.Cu, W_ARMED (adiabatic sizing, MARGIN P1-9): J124.1 BUS == R134.2, R134.1 == J121.2 IGN (two straight
              bars on the terminals' pin lines), J121.1 OUT straight down into Q124's drain pad; the BUS tap to the
              arm divider top R132, the OUT branch to R173 / R131 (continuity top, cold pull-up) and C128 off the
              drain's west edge. Q124's sources return through a comb to two GND vias (In1).
  gate        GATE row y 61.23: R126.2 - C126.1 - R128.1, one 45-degree run to the gate via and straight into
              Q124.4 (ending in the pin's aft half: rule B); B.Cu one 45-degree run to TP122; TP122's GND partner is
              Q124's source via (1.37 mm, AGENTS 3; no via in TP122: A8 gone).
  GATE_N      R126.1 - R127.1, east on R127.1's line, one 45-degree run to U1.3 (no via, F.Cu, D-S5-08); a GND guard on
              its north-east side from C126.2 to a GND via between C10's and C11's GND pads (r9_plan section 1 graft).
  CONT        divider column x 13.2 (R173 OUT - MID - R129 - CONT), CONT row y 61.23 (R178, R130, C127), the exit
              between C127.2 and R130.2, one 45-degree run to R168.1 (4.7 k at the MCU end), R168.2 to U1.15
              (PYRO1_CONT_MCU <= 3 mm, P-8).
  COLD        R131.2 - D120.1, one 45-degree run; D120.3's 3V3 drops to D120.1's line (1.4 mm off the COLD pad),
              then leaves the column on F.Cu past J122's west end to a via (the In2 3V3 region, step 6): In1 / In2 stay
              GND-only in the CH1 hull (P-3).
  ARM         the BUS tap into R132.1, MID R132.2 - R175.1, the node R175.2 / R180.1 / R133.1 / C129.1, then one
              lane: 45 degrees to x of R170.1 and straight down east of J122 to R170 (top, D-S5-02), R170.2 to U1.33.
              All F.Cu, no via.
Divider pads (0402: 0.29 mm between a part's own pads) take their tracks from the outer end and the track ends 0.1 mm
past the pad centre, outward, so every track keeps rule C + 0.2 mm from the part's other pad (D-S5-09).
The PYRO_BLOCK rule area is re-derived with the copper (r9_legalise.block_area: P-1 by construction).
Deterministic (fixed KIID seed, pad-derived points only): a rebuild reproduces the board byte for byte.
"""
import argparse
import math
import sys
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'm3_design'))
sys.path.insert(0, str(ROOT / 'tools'))
import check_r9 as C9  # noqa: E402
import r9_legalise  # noqa: E402

PROJECT = ROOT / 'm3_design/assembly_review'
MM, mm = pcbnew.FromMM, pcbnew.ToMM
KIID_SEED = 9905
LAYER = {'F': pcbnew.F_Cu, 'B': pcbnew.B_Cu}
W_ARMED = 1.0          # bus / igniter / drain bars: adiabatic (MARGIN P1-9: 1 mm x 1 oz rises ~6 K at 8.8 A / 20 ms;
                       # the fire pulse is <= 4.1 A, <= 20 ms, F7); also step 6's RAW branch to J124.2 (D-S5-10)
W_CAP = 0.4            # OUT to C128 (the drain snubber's discharge path), an existing board width (step 4: 0.40)
W_SRC = 0.3            # Q124's source pins (0.35 mm wide) to their vias
W_SIG = 0.2            # signals, the divider taps, the guard, D120's 3V3 (microamps)
VIA_SIG, VIA_GND = (0.5, 0.3), (0.6, 0.3)          # the board's via sizes (step 4)
EPS = 1e-4

# The CH1 column and the parts its copper lands on (r9_place.tsv rows; D-S5-01 ... 06): ref -> (rotation, side). The
# positions are read from the board (pad-referenced); the rotation and side the template assumes are asserted.
PARTS = {
    'J124': (90.0, 'F'), 'J121': (90.0, 'F'), 'R134': (-90.0, 'F'), 'Q124': (180.0, 'F'), 'C128': (90.0, 'F'),
    'R126': (-90.0, 'F'), 'R127': (90.0, 'F'), 'C126': (90.0, 'F'), 'R128': (90.0, 'F'), 'TP122': (0.0, 'B'),
    'C127': (90.0, 'F'), 'R130': (90.0, 'F'), 'R178': (90.0, 'F'), 'R129': (90.0, 'F'), 'R173': (90.0, 'F'),
    'R131': (0.0, 'F'), 'D120': (180.0, 'F'), 'R132': (0.0, 'F'), 'R175': (0.0, 'F'), 'R133': (0.0, 'F'),
    'R180': (0.0, 'F'), 'C129': (0.0, 'F'), 'R168': (0.0, 'F'), 'R170': (180.0, 'F'), 'U1': (0.0, 'F'),
    'J122': (180.0, 'F'), 'C10': (0.0, 'B'), 'C11': (0.0, 'B'),
}
# the nets this step completes (every pad joined; r9_pyro_check gates it); GND and 3V3 copper is the step's own only
NETS = ('PYRO1_BUS', 'PYRO1_IGN', 'PYRO1_OUT', 'PYRO1_GATE', 'PYRO1_GATE_N', 'PYRO1_CONT', 'PYRO1_CONT_MID',
        'PYRO1_CONT_MCU', 'PYRO1_COLD', 'ARM1_SENSE', 'ARM1_SENSE_MID', 'ARM1_SENSE_MCU')

# offsets (mm) the template uses, each with its reason
PAD_OUT = 0.1          # a divider track ends this far past the pad centre, away from the part's other pad: 0.577 mm from
                       # it (rule C + 0.2 mm needs 0.5; ending at the centre gives 0.477, D-S5-09)
SRC_STUB = 0.15        # Q124's source stubs end this far aft of the pin centres: their caps keep 0.77 mm from the drain
                       # pad (rule D + 0.2 mm needs 0.7)
GATE_IN = 0.15         # the GATE run ends this far aft of Q124.4's centre (the pin's aft half): 0.82 mm from the drain
                       # pad (rule B + 0.2 mm needs 0.7)
SRC_BAR = 0.75         # the source comb's bar this far aft of the pins, between the pins and the CONT row
SRC_VIA_E = 0.725      # the second source via east of pin 1: 0.64 mm from R130.1, 1.22 mm from the drain pad
DRAIN_IN = 0.505       # the C128 branch starts this far inside the drain land's west tab edge (in the pad body)
OUT_IN = 0.6           # the OUT bar ends this far inside the drain pad's forward edge: its cap keeps 1.7 mm from the
                       # source pins (rule D + 0.2 mm; ending at the pad centre gave 0.66)
PIN_END = 0.1          # GATE_N / CONT_MCU end this far inside U1's pin from its outer end
GATE_N_STUB = 0.5      # GATE_N's 45-degree run ends this far outside U1.3 (outside U1's courtyard, 0.51 mm from the
                       # sentinel pins' pad ends) and enters the pin straight
CONT_MCU_E = 0.5       # CONT_MCU leaves R168.2 east this far before its 45-degree run (U1.14's pad end 0.27 mm off)
ARM_KNEE = 1.06        # the ARM lane turns 45 degrees this far aft of R180.1 (C129.2's GND pad 0.21 mm off the knee)
THREE_V3_GAP = 0.39    # D120's 3V3 lane runs this far from J122.2's land (RAW_ACT pin rule 0.3 mm); the west tie hole's
                       # edge is then 0.6 mm off (copper to edge 0.5 mm, D-S5-05)
THREE_V3_VIA_DY = 1.8  # its via this far forward of R168 (1.28 mm from R168's pads; outside the CH1 hull + 1 mm, P-3)


def r4(v):
    return round(v, 4)


def octilinear(a, b):
    dx, dy = abs(b[0] - a[0]), abs(b[1] - a[1])
    return dx < 1e-6 or dy < 1e-6 or abs(dx - dy) < 1e-6


class Pads:
    """Pad centres read from the board: P['J121.2'] -> (x, y); P.x('J121.2'), P.y(...)."""

    def __init__(self, b):
        self.fps = {f.GetReference(): f for f in b.GetFootprints()}
        self.c = {}
        self.net = {}
        self.box = {}
        for ref in PARTS:
            f = self.fps[ref]
            rot, side = PARTS[ref]
            assert abs(((f.GetOrientationDegrees() - rot + 180) % 360) - 180) < 1e-6 and f.IsFlipped() == (side == 'B'), \
                f'{ref}: rotation {f.GetOrientationDegrees()} {"B" if f.IsFlipped() else "F"} (template {rot} {side})'
            for p in f.Pads():
                if p.GetNumber():
                    k = f'{ref}.{p.GetNumber()}'
                    self.c[k] = (r4(mm(p.GetPosition().x)), r4(mm(p.GetPosition().y)))
                    self.net[k] = p.GetNetname()
                    bb = p.GetBoundingBox()
                    self.box[k] = tuple(r4(mm(v)) for v in (bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom()))

    def __getitem__(self, k):
        return self.c[k]

    def x(self, k):
        return self.c[k][0]

    def y(self, k):
        return self.c[k][1]


def same(a, b, what):
    assert abs(a - b) < EPS, f'{what}: {a} != {b} (the template needs them aligned; check r9_place.tsv)'


def diag(a, b, what):
    """b is on a 45-degree line from a."""
    assert abs(abs(b[0] - a[0]) - abs(b[1] - a[1])) < EPS, f'{what}: {a} -> {b} is not 45 degrees'


def copper(P):
    """[(net, layer, width, [points])], [(net, (x, y), size, basis)] from the pad map P."""
    T, V = [], []

    def t(net, layer, w, pts):
        T.append((net, layer, w, [(r4(x), r4(y)) for x, y in pts]))

    def v(net, at, size, basis):
        V.append((net, (r4(at[0]), r4(at[1])), size, basis))

    # pad nets the template relies on (the netlist; check_actuators 1 holds the pins)
    for k, n in (('J124.1', 'PYRO1_BUS'), ('J124.2', 'RAW_ACT'), ('J121.1', 'PYRO1_OUT'), ('J121.2', 'PYRO1_IGN'),
                 ('R134.1', 'PYRO1_IGN'), ('R134.2', 'PYRO1_BUS'), ('Q124.4', 'PYRO1_GATE'), ('Q124.5', 'PYRO1_OUT'),
                 ('R132.1', 'PYRO1_BUS'), ('R173.1', 'PYRO1_OUT'), ('R131.1', 'PYRO1_OUT'), ('R131.2', 'PYRO1_COLD'),
                 ('D120.1', 'PYRO1_COLD'), ('D120.3', '3V3'), ('U1.3', 'PYRO1_GATE_N'), ('U1.15', 'PYRO1_CONT_MCU'),
                 ('U1.33', 'ARM1_SENSE_MCU'), ('R170.1', 'ARM1_SENSE'), ('R168.1', 'PYRO1_CONT'),
                 ('C126.2', 'GND'), ('C10.2', 'GND'), ('C11.2', 'GND'), ('J122.2', 'RAW_ACT')):
        assert P.net[k] == n, f'{k} is {P.net[k]}, the template expects {n}'

    # --- fire loop -----------------------------------------------------------------------------------------------
    same(P.y('J121.2'), P.y('R134.1'), 'IGN bar J121.2 - R134.1')
    same(P.y('J124.1'), P.y('R134.2'), 'BUS bar J124.1 - R134.2')
    same(P.x('J121.1'), P.x('Q124.5'), 'OUT bar J121.1 - Q124 drain')
    t('PYRO1_IGN', 'F', W_ARMED, [P['J121.2'], P['R134.1']])
    t('PYRO1_BUS', 'F', W_ARMED, [P['J124.1'], P['R134.2']])
    yb = P.y('R131.1')                                    # the OUT branch line (R131's axis)
    same(P.y('R131.1'), P.y('R131.2'), 'R131 horizontal')
    x_out = P.x('J121.1')
    t('PYRO1_OUT', 'F', W_ARMED, [P['J121.1'], (x_out, yb)])
    dl, dt, dr, db = P.box['Q124.5']                  # the drain pad (the AON7524's exposed pad)
    t('PYRO1_OUT', 'F', W_ARMED, [(x_out, yb), (x_out, db - OUT_IN)])
    # the OUT branch: over R173.1 (a node in its pad, north of its centre) into R131.1's west half
    same(P.x('R173.1'), P.x('R173.2'), 'R173 vertical')
    assert P.y('R173.1') > P.y('R173.2'), 'R173: OUT pad forward of MID'
    assert P.y('R173.1') < yb < P.y('R173.1') + 0.283, 'the OUT branch must cross R173.1 north of its centre'
    t('PYRO1_OUT', 'F', W_SIG, [(x_out, yb), (P.x('R173.1'), yb)])
    t('PYRO1_OUT', 'F', W_SIG, [(P.x('R173.1'), yb), (P.x('R131.1') - PAD_OUT, yb)])
    # C128 on the drain land's west tab (the AON7524 land: a 0.38 x 0.43 mm tab on the pad's centre line), straight
    same(P.x('C128.1'), P.x('C128.2'), 'C128 vertical')
    same(P.y('C128.1'), P.y('Q124.5'), 'C128.1 on the drain tab line')
    t('PYRO1_OUT', 'F', W_CAP, [(dl + DRAIN_IN, P.y('C128.1')), P['C128.1']])
    # the BUS tap into R132.1's west half
    same(P.y('R132.1'), P.y('R134.2'), 'R132 on the BUS bar line')
    t('PYRO1_BUS', 'F', W_SIG, [P['R134.2'], (P.x('R132.1') - PAD_OUT, P.y('R132.1'))])
    # Q124's sources: a comb of stubs to a bar and two GND vias (the fire current's return to In1)
    ys = r4(P.y('Q124.1') - SRC_STUB)
    yv = r4(P.y('Q124.1') - SRC_BAR)
    srcs = [P['Q124.3'], P['Q124.2'], P['Q124.1']]
    for s in srcs:
        same(s[1], P.y('Q124.1'), 'Q124 source row')
        t('GND', 'F', W_SRC, [(s[0], ys), (s[0], yv)])
    xe = r4(P.x('Q124.1') + SRC_VIA_E)
    t('GND', 'F', W_SRC, [(srcs[0][0], yv), (srcs[1][0], yv)])
    t('GND', 'F', W_SRC, [(srcs[1][0], yv), (srcs[2][0], yv)])
    t('GND', 'F', W_SRC, [(srcs[2][0], yv), (xe, yv)])
    v('GND', (srcs[1][0], yv), VIA_GND, 'Q124 source return; TP122 gate via partner (AGENTS 3)')
    v('GND', (xe, yv), VIA_GND, 'Q124 source return')

    # --- gate ----------------------------------------------------------------------------------------------------
    gate_row = [P['R126.2'], P['C126.1'], P['R128.1']]
    for g in gate_row:
        same(g[1], P.y('R128.1'), 'GATE row')
    t('PYRO1_GATE', 'F', W_SIG, [P['R126.2'], P['C126.1']])
    t('PYRO1_GATE', 'F', W_SIG, [P['C126.1'], P['R128.1']])
    g4 = P['Q124.4']
    vg = (g4[0], r4(P.y('R128.1') + (g4[0] - P.x('R128.1'))))       # 45 degrees from R128.1 to the gate pin's column
    t('PYRO1_GATE', 'F', W_SIG, [P['R128.1'], vg])
    t('PYRO1_GATE', 'F', W_SIG, [vg, (g4[0], g4[1] - GATE_IN)])
    v('PYRO1_GATE', vg, VIA_SIG, 'gate via to TP122 (bottom)')
    tp = P['TP122.1']
    diag(vg, tp, 'gate via -> TP122')
    t('PYRO1_GATE', 'B', W_SIG, [vg, tp])

    # --- GATE_N and its guard ----------------------------------------------------------------------------------
    same(P.x('R126.1'), P.x('R127.1'), 'R126 / R127 column')
    t('PYRO1_GATE_N', 'F', W_SIG, [P['R126.1'], P['R127.1']])
    u3 = P['U1.3']
    u3_end = P.box['U1.3'][3]                              # the LQFP pin's outer end (forward face)
    yn = P.y('R127.1')
    kn = (u3[0], u3_end + GATE_N_STUB)                     # the stub's top: 45 degrees from R127.1's line
    xk = kn[0] - (yn - kn[1])
    t('PYRO1_GATE_N', 'F', W_SIG, [P['R127.1'], (xk, yn)])
    t('PYRO1_GATE_N', 'F', W_SIG, [(xk, yn), kn])
    t('PYRO1_GATE_N', 'F', W_SIG, [kn, (u3[0], u3_end - PIN_END)])
    # the guard: C126.2 -> GATE_N's offset (north-east, uniform) -> a GND via between C11.2 and C10.2 (bottom GND pads)
    same(P.x('C11.2'), P.x('C10.2'), 'C10 / C11 GND pads')
    vgd = (P.x('C11.2'), r4((P.y('C11.2') + P.y('C10.2')) / 2))
    off = (vgd[0] + vgd[1] - (xk + yn)) / math.sqrt(2)    # the guard's offset from GATE_N (centre lines)
    yg = r4(yn + off)
    xg = r4(vgd[0] + vgd[1] - yg)
    assert 0.9 < off < 1.5 and P.box['C126.2'][1] > yg, f'guard offset {off:.3f} mm'
    t('GND', 'F', W_SIG, [P['C126.2'], (P.x('C126.2'), yg)])
    t('GND', 'F', W_SIG, [(P.x('C126.2'), yg), (xg, yg)])
    t('GND', 'F', W_SIG, [(xg, yg), vgd])
    v('GND', vgd, VIA_SIG, 'GATE_N guard; C10.2 / C11.2')

    # --- CONT ----------------------------------------------------------------------------------------------------
    for a, b_ in (('R173.2', 'R129.1'), ('R129.1', 'R129.2'), ('R129.2', 'R178.1')):
        same(P.x(a), P.x(b_), f'CONT column {a} - {b_}')
    t('PYRO1_CONT_MID', 'F', W_SIG, [(P.x('R173.2'), P.y('R173.2') - PAD_OUT), P['R129.1']])
    t('PYRO1_CONT', 'F', W_SIG, [P['R129.2'], P['R178.1']])
    for k in ('R130.1', 'C127.1'):
        same(P.y(k), P.y('R178.1'), 'CONT row')
    xt = r4((P.box['C127.2'][2] + P.box['R130.2'][0]) / 2)   # the exit midway between C127.2 and R130.2
    t('PYRO1_CONT', 'F', W_SIG, [P['R178.1'], P['R130.1']])
    t('PYRO1_CONT', 'F', W_SIG, [P['R130.1'], (xt, P.y('R130.1'))])
    t('PYRO1_CONT', 'F', W_SIG, [(xt, P.y('R130.1')), P['C127.1']])
    r168 = P['R168.1']
    yk = r168[1] + (r168[0] - xt)                          # 45 degrees from the exit's knee onto R168.1
    t('PYRO1_CONT', 'F', W_SIG, [(xt, P.y('R130.1')), (xt, yk)])
    t('PYRO1_CONT', 'F', W_SIG, [(xt, yk), r168])
    u15 = P['U1.15']
    u15_end = P.box['U1.15'][3]
    a = (P.x('R168.2') + CONT_MCU_E, P.y('R168.2'))
    bq = (u15[0], a[1] - (u15[0] - a[0]))
    t('PYRO1_CONT_MCU', 'F', W_SIG, [P['R168.2'], a])
    t('PYRO1_CONT_MCU', 'F', W_SIG, [a, bq])
    t('PYRO1_CONT_MCU', 'F', W_SIG, [bq, (u15[0], u15_end - PIN_END)])

    # --- COLD and D120's 3V3 -----------------------------------------------------------------------------------
    c0 = (P.x('R131.2') + PAD_OUT, P.y('R131.2'))
    diag(c0, P['D120.1'], 'R131.2 -> D120.1 (COLD)')
    t('PYRO1_COLD', 'F', W_SIG, [c0, P['D120.1']])
    d3 = P['D120.3']                                       # down to D120.1's line, 45 degrees west, down past J122
    x3 = r4(P.box['J122.2'][0] - THREE_V3_GAP - W_SIG / 2)
    k3a = (d3[0], P.y('D120.1'))
    k3b = (x3, k3a[1] - (d3[0] - x3))
    v3 = (x3, r4(P.y('R168.1') + THREE_V3_VIA_DY))
    t('3V3', 'F', W_SIG, [d3, k3a])
    t('3V3', 'F', W_SIG, [k3a, k3b])
    t('3V3', 'F', W_SIG, [k3b, v3])
    v('3V3', v3, VIA_SIG, 'D120 3V3 feed: In2 3V3 (step 6)')

    # --- ARM -------------------------------------------------------------------------------------------------------
    for k in ('R132.2', 'R175.1', 'R175.2'):
        same(P.y(k), P.y('R132.1'), 'arm divider row')
    t('ARM1_SENSE_MID', 'F', W_SIG, [(P.x('R132.2') + PAD_OUT, P.y('R132.2')), P['R175.1']])
    same(P.x('R180.1'), P.x('R133.1'), 'R180 / R133 ARM pads')
    na = (P.x('R180.1'), P.y('R175.2'))
    t('ARM1_SENSE', 'F', W_SIG, [P['R175.2'], na])
    t('ARM1_SENSE', 'F', W_SIG, [na, P['R133.1']])
    t('ARM1_SENSE', 'F', W_SIG, [na, P['R180.1']])
    c129 = P['C129.1']
    kc = (P.x('R175.2'), c129[1] + (P.x('R175.2') - c129[0]))
    t('ARM1_SENSE', 'F', W_SIG, [P['R175.2'], kc])
    t('ARM1_SENSE', 'F', W_SIG, [kc, c129])
    r170 = P['R170.1']
    k1 = (P.x('R180.1'), P.y('R180.1') - ARM_KNEE)
    k2 = (r170[0], k1[1] - (r170[0] - k1[0]))
    t('ARM1_SENSE', 'F', W_SIG, [P['R180.1'], k1])
    t('ARM1_SENSE', 'F', W_SIG, [k1, k2])
    t('ARM1_SENSE', 'F', W_SIG, [k2, r170])
    same(P.y('U1.33'), P.y('R170.2'), 'ARM1_SENSE_MCU straight')
    t('ARM1_SENSE_MCU', 'F', W_SIG, [P['U1.33'], P['R170.2']])
    return T, V


class Draw:
    def __init__(self, b):
        self.b = b
        self.vias = {}
        self.tracks = []

    def net(self, name):
        n = self.b.FindNet(name)
        assert n is not None and n.GetNetCode() > 0, f'no net {name}'
        return n

    def track(self, net, layer, width, pts):
        n = self.net(net)
        for a, c in zip(pts, pts[1:]):
            assert a != c, f'{net}: zero-length segment at {a}'
            assert octilinear(a, c), f'{net}: segment {a}-{c} is not 0 / 45 / 90 degrees'
            t = pcbnew.PCB_TRACK(self.b)
            t.SetStart(pcbnew.VECTOR2I(MM(a[0]), MM(a[1])))
            t.SetEnd(pcbnew.VECTOR2I(MM(c[0]), MM(c[1])))
            t.SetWidth(MM(width))
            t.SetLayer(LAYER[layer])
            t.SetNet(n)
            self.b.Add(t)
            self.tracks.append((net, layer, width, a, c))

    def via(self, net, at, size, basis=''):
        assert at not in self.vias, f'two vias at {at}'
        v = pcbnew.PCB_VIA(self.b)
        v.SetPosition(pcbnew.VECTOR2I(MM(at[0]), MM(at[1])))
        v.SetWidth(MM(size[0]))
        v.SetDrill(MM(size[1]))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        v.SetNet(self.net(net))
        self.b.Add(v)
        self.vias[at] = (net, basis)


def block(b):
    """PYRO_BLOCK re-derived with the drawn copper (r9_legalise.block_area: P-1 and check_actuators 15b by
    construction)."""
    zs = [z for z in b.Zones() if z.GetIsRuleArea() and z.GetZoneName() == 'PYRO_BLOCK']
    assert len(zs) == 1
    z = zs[0]
    pts = r9_legalise.block_area(b)
    o = z.Outline()
    o.RemoveAllContours()
    o.NewOutline()
    for x, y in pts:
        o.Append(MM(x), MM(y))
    return pts


def build(b):
    assert not [t for t in b.GetTracks() if t.GetNetname() in NETS], \
        'the CH1 nets carry copper already (r9_pyro.py runs once, on r9_rf.py\'s board)'
    P = Pads(b)
    tracks, vias = copper(P)
    d = Draw(b)
    for net, layer, w, pts in tracks:
        d.track(net, layer, w, pts)
    for net, at, size, basis in vias:
        d.via(net, at, size, basis)
    drawn = {net for net, *_ in d.tracks}
    assert set(NETS) <= drawn, f'nets not drawn: {sorted(set(NETS) - drawn)}'
    assert drawn <= set(NETS) | {'GND', '3V3'}, f'foreign nets drawn: {sorted(drawn - set(NETS) - {"GND", "3V3"})}'
    area = block(b)
    return d, area


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--board', type=Path, default=PROJECT / 'm3.kicad_pcb')
    ap.add_argument('--out', type=Path, help='design aid: save here instead of --board')
    ap.add_argument('--no-fill', action='store_true', help='design aid: save unfilled')
    args = ap.parse_args()
    board = args.board.resolve()
    for ext in ('.kicad_pro', '.kicad_dru'):
        assert board.with_suffix(ext).is_file(), f'{board.with_suffix(ext).name} must sit beside the board'
    b = pcbnew.LoadBoard(str(board))
    pcbnew.KIID.SeedGenerator(KIID_SEED)
    d, area = build(b)
    if not args.no_fill:
        b.BuildConnectivity()
        assert pcbnew.ZONE_FILLER(b).Fill(b.Zones()), 'native zone fill failed'
    b.BuildConnectivity()
    moved = []
    for v in b.GetTracks():
        if v.GetClass() == 'PCB_VIA':
            key = (r4(mm(v.GetPosition().x)), r4(mm(v.GetPosition().y)))
            if key in d.vias and d.vias[key][0] != v.GetNetname():
                moved.append((key, d.vias[key][0], v.GetNetname()))
    assert not moved, f'connectivity re-netted vias (a via sits on foreign copper): {moved}'
    out = (args.out or board).resolve()
    assert pcbnew.SaveBoard(str(out), b, True), 'save failed'
    length = sum(math.dist(a, c) for _, _, _, a, c in d.tracks)
    print(f'r9_pyro: {len(d.tracks)} segments ({length:.1f} mm), {len(d.vias)} vias, PYRO_BLOCK {len(area)} vertices')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
