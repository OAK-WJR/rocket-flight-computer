#!/usr/bin/env python3
"""Build the R9 power copper (M3-ASSY-R9, build step 6) on the step-5 board.

usage: <KiCad python3> -I m3_design/r9_power.py [--board m3_design/assembly_review/m3.kicad_pcb] [--out OUT]
       design aid (r9_build.sh never passes it): --no-fill

r9_plan.md section 4 step 6; R9_OWNER_DECISIONS.md item 5 (the mid support); R9_DECISIONS.md D-S6-*. The board is
rebuilt in place (the project's m3.kicad_pro and m3.kicad_dru apply while it is filled). Every number is board mm (y
forward). The copper lands on the parts at their r9_place.tsv positions, which PARTS freezes: a part that moves without
its copper stops the build (the copper is a template of the east column, like r9_rf.py's and r9_pyro.py's).

  In2         four regions (r9_plan section 3, D-S6-03): RAW_ACT (the spine column and J122's whole footprint), BAT_IN
              (J1.1 to Q120's drains), 3V3 (the MCU domain from the RF strip's edge, with a finger up the spine's east
              side to the 3V3 buck), GND everywhere else (the CH1 hull, the RF strip's forward edge, the east column).
  7.7 A       J1.1 -> BAT_IN (B / F / In2) -> Q120 -> ACT_FET_S (B bridge + F plate) -> Q121 -> RAW_ACT spine (B / F /
              In2) -> J122's RAW row, J124.2 (F bar), C121 / C150 / C151; via fields stitch the layers, no series via
              (D-S6-02). The switch legs, the BAT_IN taps (U9 IN, R80) and the input damper.
  gate        the actuator switch's gate network (D-S6-04): C120 / R120 west of Q121.4 on the gate bus, the driver
              column Q122 / R121 / R122 / R123 east of the pair beside Q120.4, one F.Cu hop over the ACT_FET_S bridge.
  efuse       RAW_PROTECTED (D-S6-05): U9.6 east to its column and two vias, an F.Cu pour down the east column (under
              C84's body) to C82, branches to U11's IN1 (C97), R122, TP81 and the camera eFuse U7 (R8 D46's route).
  logic       VLOGIC (U11 OUT -> C99 -> U2 EN / VIN -> C6, C7, TP83, the hold-up C84), the 3V3 buck U2 (Diodes DS41326
              Figure 25: VIN cap at VIN / GND, SW straight into L1, BST cap BST - SW, FB on the In2 3V3 plane), 3V3 out
              L1 -> C8 -> C9 and one via into the In2 finger (D-S6-06).
  camera      the camera eFuse U7 output to the camera buck U8, its loop, feedback and CAM_5V to J9.1 with its sense (R8
              D37 / D41 moved with the camera block, +4 mm in y; widths mapped onto the board's six, D-S6-07).
  decoupling  U1's decoupling and VCAP (R8 spike (a), moved with U1), C13 / C14's own taps (D-S6-08).
  ground      the GND vias and straps of the power parts' loops (the buck input loop, the clamps, the bulk caps).
Left to later steps (D-S6-10): step 7 power_ctl (U9 / U11 / U7 control pins, BAT_ENABLE, the status lanes, USB_LIMITED
from U10 to U11 with its corridor note), the RAW_ACT_SENSE divider tap (R177.1), VLOGIC_SENSE's tap (R60.1), CAM_5V
to U13 / R104 / C91 (camera family), the 3V3A filter and the other 3V3 pull-ups and bypasses; step 8 the board-wide
GND pours and stitching (In1, F.Cu, B.Cu), which the GND vias of PENDING wait for.
Deterministic (fixed KIID seed, tables only): a rebuild reproduces the board byte for byte.
"""
import argparse
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / 'm3_design/assembly_review'
MM, mm = pcbnew.FromMM, pcbnew.ToMM
KIID_SEED = 9906
LAYER = {'F': pcbnew.F_Cu, 'B': pcbnew.B_Cu, 'In1': pcbnew.In1_Cu, 'In2': pcbnew.In2_Cu}
VIA_SIG, VIA_PWR = (0.5, 0.3), (0.6, 0.3)        # the board's two via sizes (steps 4 and 5)
W_SIG, W_GATE, W_FEED, W_RAIL, W_BIG = 0.2, 0.25, 0.3, 0.4, 1.0      # the board's five widths (D-S5-08)
EPS = 1e-4
FULL, THERMAL, THT = pcbnew.ZONE_CONNECTION_FULL, pcbnew.ZONE_CONNECTION_THERMAL, pcbnew.ZONE_CONNECTION_THT_THERMAL

# Every part the step's copper lands on, at its r9_place.tsv position: ref -> (x, y, rotation, side). Asserted against
# the board (Pads), so a placement edit that the copper does not follow stops the build (D-S6-01).
PARTS = {
    'C120': (27.6, 85.5, 90, 'B'), 'C121': (33.4, 66.6, 90, 'F'), 'C13': (9.85, 51.6, -90, 'B'),
    'C14': (16.4, 53.6, 0, 'B'), 'C15': (24.2, 48.9, 90, 'B'), 'C150': (30.2, 74.6, 90, 'B'),
    'C151': (32.6, 74.6, 90, 'B'), 'C16': (23.1, 38.12, 180, 'B'), 'C17': (12.0, 39.4, -90, 'B'),
    'C18': (13.3, 50.65, 180, 'B'), 'C19': (23.35, 39.95, -90, 'B'), 'C20': (14.8, 38.8, 0, 'B'),
    'C23': (22.8, 36.8, 180, 'B'), 'C29': (23.0, 45.02, -90, 'B'), 'C5': (37.2, 73.4, 90, 'B'),
    'C6': (42.75, 71.75, -90, 'B'), 'C7': (43.3, 75.8, -90, 'B'), 'C71': (35.5, 31.4, -90, 'B'),
    'C72': (43.41, 38.95, -90, 'B'), 'C73': (43.41, 34.35, 90, 'B'), 'C74': (36.1, 40.83, 90, 'B'),
    'C75': (40.0, 50.07, 0, 'B'), 'C76': (35.29, 44.66, 90, 'B'), 'C77': (39.5, 39.5, 180, 'F'),
    'C8': (41.0, 80.28, 0, 'B'), 'C80': (19.0, 99.7, 180, 'B'), 'C82': (40.9, 70.9, 90, 'F'),
    'C84': (37.0, 80.5, -90, 'F'), 'C88': (38.2, 90.23, 90, 'B'), 'C89': (32.25, 91.7, -90, 'F'),
    'C9': (41.0, 82.24, 0, 'B'), 'C95': (32.25, 96.6, 90, 'F'), 'C96': (24.0, 99.7, 180, 'B'),
    'C97': (39.3, 66.4, 90, 'F'), 'C99': (40.5, 68.9, 0, 'B'), 'D8': (25.0, 89.2, 180, 'B'),
    'D9': (41.6, 89.6, 180, 'F'), 'J1': (20.0, 94.4, 180, 'F'), 'J122': (23.0, 62.0, 180, 'F'),
    'J124': (10.1, 83.5, 90, 'F'), 'J9': (42.7, 48.2, -90, 'F'), 'L1': (40.0, 76.6, -90, 'B'),
    'L3': (39.95, 44.82, -90, 'B'), 'Q120': (34.0, 91.5, 0, 'B'), 'Q121': (32.73, 82.2, 180, 'B'),
    'Q122': (37.35, 84.5, 90, 'B'), 'R120': (29.35, 86.47, 90, 'B'),
    'R121': (37.35, 87.55, 90, 'B'), 'R122': (36.83, 82.0, 180, 'B'), 'R123': (36.4, 80.56, 90, 'B'),
    'R165': (13.205, 90.2, 0, 'B'), 'R166': (35.32, 94.4, 90, 'F'), 'R167': (30.5, 99.6, 0, 'B'),
    'R71': (39.5, 37.9, 180, 'F'), 'R72': (39.5, 36.3, 0, 'F'), 'R78': (35.5, 49.2, 180, 'B'),
    'R80': (18.285, 90.2, 180, 'B'), 'R82': (39.7, 92.9, 0, 'B'), 'R92': (43.1, 86.25, 90, 'B'),
    'TP120': (30.2, 78.4, 0, 'F'), 'TP121': (24.0, 85.86, 0, 'B'), 'TP70': (35.8, 28.9, 0, 'B'),
    'TP71': (36.36, 35.65, 0, 'B'), 'TP72': (44.2, 47.17, 0, 'B'), 'TP80': (36.0, 96.8, 0, 'B'),
    'TP81': (44.6, 70.4, 0, 'F'), 'TP83': (44.6, 78.2, 0, 'F'), 'U1': (18.0, 44.5, 0, 'F'),
    'U11': (39.65, 66.5, 90, 'B'), 'U2': (40.0, 71.8, 0, 'B'), 'U3': (17.6, 42.7, 90, 'B'),
    'U7': (33.8, 34.7, -90, 'B'), 'U8': (39.95, 38.95, -90, 'B'), 'U9': (40.3, 90.4, 90, 'B'),
}


def r4(v):
    return round(v, 4)


def octilinear(a, b):
    dx, dy = abs(b[0] - a[0]), abs(b[1] - a[1])
    return dx < 1e-6 or dy < 1e-6 or abs(dx - dy) < 1e-6


def same(a, b, what):
    assert abs(a - b) < EPS, f'{what}: {a} != {b} (the template needs them aligned; check r9_place.tsv)'


class Pads:
    """Pad centres and boxes read from the board: P['Q121.5'] -> (x, y); P.box[k] -> (x0, y0, x1, y1). The PARTS
    positions are asserted first."""

    def __init__(self, b):
        self.fps = {f.GetReference(): f for f in b.GetFootprints()}
        bad = []
        for ref, (x, y, rot, side) in sorted(PARTS.items()):
            f = self.fps[ref]
            p = f.GetPosition()
            got = (r4(mm(p.x)), r4(mm(p.y)), f.GetOrientationDegrees(), 'B' if f.IsFlipped() else 'F')
            if abs(got[0] - x) > EPS or abs(got[1] - y) > EPS or abs(((got[2] - rot + 180) % 360) - 180) > 1e-6 \
                    or got[3] != side:
                bad.append(f'{ref}: board {got}, template {(x, y, rot, side)}')
        assert not bad, 'power parts off their template (r9_place.tsv and PARTS disagree):\n  ' + '\n  '.join(bad)
        self.c, self.net, self.box = {}, {}, {}
        for ref, f in self.fps.items():
            for p in f.Pads():
                if not p.GetNumber():
                    continue
                k = f'{ref}.{p.GetNumber()}'
                bb = p.GetBoundingBox()
                box = tuple(r4(mm(v)) for v in (bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom()))
                if k in self.box:             # multi-shape pins (U9's L-shaped pads): the union of their boxes
                    o = self.box[k]
                    box = (min(o[0], box[0]), min(o[1], box[1]), max(o[2], box[2]), max(o[3], box[3]))
                else:
                    self.c[k] = (r4(mm(p.GetPosition().x)), r4(mm(p.GetPosition().y)))
                    self.net[k] = p.GetNetname()
                self.box[k] = box

    def __getitem__(self, k):
        return self.c[k]

    def x(self, k):
        return self.c[k][0]

    def y(self, k):
        return self.c[k][1]


class Draw:
    """Draws the step's copper on the board; dry=True records it only (r9_power_check's template gate)."""

    def __init__(self, b, dry=False):
        self.b = b
        self.dry = dry
        self.vias = {}
        self.via_size = {}
        self.tracks = []
        self.zones = []

    def net(self, name):
        n = self.b.FindNet(name)
        assert n is not None and n.GetNetCode() > 0, f'no net {name}'
        return n

    def track(self, net, layer, width, pts):
        n = self.net(net)
        pts = [(r4(x), r4(y)) for x, y in pts]
        for a, c in zip(pts, pts[1:]):
            assert a != c, f'{net}: zero-length segment at {a}'
            assert octilinear(a, c), f'{net}: segment {a}-{c} is not 0 / 45 / 90 degrees'
            t = pcbnew.PCB_TRACK(self.b)
            t.SetStart(pcbnew.VECTOR2I(MM(a[0]), MM(a[1])))
            t.SetEnd(pcbnew.VECTOR2I(MM(c[0]), MM(c[1])))
            t.SetWidth(MM(width))
            t.SetLayer(LAYER[layer])
            t.SetNet(n)
            if not self.dry:
                self.b.Add(t)
            self.tracks.append((net, layer, width, a, c))

    def via(self, net, at, size=VIA_PWR):
        at = (r4(at[0]), r4(at[1]))
        assert at not in self.vias, f'two vias at {at}'
        v = pcbnew.PCB_VIA(self.b)
        v.SetPosition(pcbnew.VECTOR2I(MM(at[0]), MM(at[1])))
        v.SetWidth(MM(size[0]))
        v.SetDrill(MM(size[1]))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        v.SetNet(self.net(net))
        if not self.dry:
            self.b.Add(v)
        self.vias[at] = net
        self.via_size[at] = size

    def zone(self, name, net, layer, pts, prio, clr=0.3, minw=0.3, conn=FULL, tgap=0.25, spoke=0.4):
        z = pcbnew.ZONE(self.b)
        z.SetLayer(LAYER[layer])
        z.SetNet(self.net(net))
        z.SetZoneName(name)
        z.SetAssignedPriority(prio)
        z.SetLocalClearance(MM(clr))
        z.SetMinThickness(MM(minw))
        z.SetPadConnection(conn)
        z.SetThermalReliefGap(MM(tgap))
        z.SetThermalReliefSpokeWidth(MM(spoke))
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        o = z.Outline()
        o.NewOutline()
        for x, y in pts:
            o.Append(MM(x), MM(y))
        assert not o.IsSelfIntersecting(), name
        if not self.dry:
            self.b.Add(z)
        self.zones.append((name, net, layer, z))
        return z

# the nets this step completes (every pad joined; r9_power_check gates it), and the nets it leaves partial with the pads
# later steps join (D-S6-10); GND and 3V3 are shared rails (the step's own copper only)
NETS = ('BAT_IN', 'BAT_DAMP', 'BAT_SW_SOURCE', 'BAT_SW_RETURN', 'ACT_FET_S', 'ACT_GATE', 'ACT_DRV', 'ACT_EN',
        'RAW_PROTECTED', 'SW_NODE', 'BST', 'CAM_INPUT_LIMITED', 'CAM_SW', 'CAM_BST', 'CAM_FB', 'VCAP1', 'VCAP2')
PARTIAL = {'RAW_ACT': ('R177.1',),                       # the RAW_ACT_SENSE divider's top: step 7 "pyro" (D-S5-07)
           'VLOGIC': ('R60.1',),                         # VLOGIC_SENSE's divider top: step 7 status / sense
           'CAM_5V': ('U13.1', 'R104.1', 'C91.1')}       # the camera translator supply and sense: step 7 camera
RAILS = ('GND', '3V3')


def poly(pts):
    s = pcbnew.SHAPE_POLY_SET()
    s.NewOutline()
    for x, y in pts:
        s.Append(MM(x), MM(y))
    return s


def grid(x0, x1, y0, y1, pitch_x, pitch_y=None):
    pitch_y = pitch_y or pitch_x
    nx, ny = int(round((x1 - x0) / pitch_x)), int(round((y1 - y0) / pitch_y))
    return [(r4(x0 + i * pitch_x), r4(y0 + j * pitch_y)) for j in range(ny + 1) for i in range(nx + 1)]


# ======================================================================================================================
# In2: four regions (r9_plan section 3; D-S6-03)
# ======================================================================================================================
# RAW_ACT: the spine column and J122's whole footprint (the RAW mouth between J122's SIG and GND rows is fed on In2 as
# well as B.Cu, plan_spine 5.2); its north-west edge steps round the CH1 hull (P-3: In1 / In2 GND only in the hull +
# 1 mm); >= 2.65 mm in plan view from bus / igniter / drain copper (D18, X9c); clear of D120's 3V3 via (17.9, 56.3)
IN2_RAW_ACT = [(18.6, 57.0), (36.0, 57.0), (36.0, 84.0), (29.4, 84.0), (29.4, 78.5), (28.6, 78.5), (28.6, 66.6),
               (20.0, 66.6), (18.6, 64.6)]
# BAT_IN: J1.1 to Q120's drains, no further than the outer BAT_IN pours carry current (R8 D97: no unfused battery
# copper on In2 beyond the current path; the forward edge keeps a 2.5 mm GND strip)
IN2_BAT_IN = [(24.4, 89.6), (37.4, 89.6), (37.4, 97.8), (30.6, 97.8), (30.6, 99.2), (24.4, 99.2)]
# 3V3: the MCU domain from the RF strip's edge (y 23.5: R-2 keeps In2 GND-only below y_f) to U1's forward field, its
# north edge 0.15 mm off the CH1 hull, the camera translator tongue, and a 1.5 mm finger (x 36.3-37.8) up the spine's
# east side to the 3V3 buck's output via and its FB sense via
IN2_3V3 = [(0.5, 23.5), (35.3, 23.5), (35.3, 31.6), (33.3, 31.6), (33.3, 52.0), (38.0, 52.0), (38.0, 56.7),
           (37.8, 56.7), (37.8, 79.3), (36.3, 79.3), (36.3, 56.7), (18.3, 56.7), (18.3, 58.85), (14.0, 58.85),
           (5.6, 55.2), (0.5, 55.2)]
IN2_GND = [(0.3, 23.0), (45.7, 23.0), (45.7, 101.7), (0.3, 101.7)]     # from the strip's In2 pour edge (y 23.0)


def in2(d, P):
    z = d.zone('R9_GND_In2', 'GND', 'In2', IN2_GND, 2, clr=0.25, minw=0.2, conn=THT)
    for pts in (IN2_RAW_ACT, IN2_BAT_IN, IN2_3V3):
        z.Outline().BooleanSubtract(poly(pts))
    d.zone('R9_RAW_ACT_In2', 'RAW_ACT', 'In2', IN2_RAW_ACT, 12)
    d.zone('R9_BAT_IN_In2', 'BAT_IN', 'In2', IN2_BAT_IN, 12)
    d.zone('R9_3V3_In2', '3V3', 'In2', IN2_3V3, 10, clr=0.25, minw=0.2, conn=THERMAL)


# ======================================================================================================================
# The 7.7 A path (D-S6-02): J1.1 -> BAT_IN -> Q120 -> ACT_FET_S -> Q121 -> RAW_ACT spine -> J122 (and J124.2)
# ======================================================================================================================
BAT_IN_B = [(24.4, 87.75), (28.75, 87.75), (28.75, 89.65), (37.6, 89.65), (37.6, 90.36), (38.8, 90.36), (38.8, 91.6),
            (39.2, 91.6), (39.2, 93.7), (37.4, 93.7), (37.4, 97.8), (30.6, 97.8), (30.6, 100.9), (24.5, 100.9),
            (24.5, 98.5), (21.35, 98.5), (21.35, 100.9), (19.6, 100.9), (19.6, 96.0), (24.4, 96.0)]
BAT_IN_F = [(26.3, 89.4), (33.37, 89.4), (33.37, 92.3), (31.05, 92.3), (31.05, 96.0), (33.37, 96.0),
            (33.37, 99.2), (26.3, 99.2)]
ACT_FET_S_B = [(31.42, 84.0), (35.77, 84.0), (35.77, 84.3), (36.6, 84.3), (36.6, 87.76), (35.31, 87.76),
               (35.31, 89.44), (29.0, 89.44), (28.7, 89.14), (28.7, 87.75), (27.05, 87.75), (27.05, 85.6), (30.2, 85.6),
               (30.2, 85.94), (31.42, 85.94)]
ACT_FET_S_F = [(31.2, 83.9), (35.75, 83.9), (35.75, 86.97), (31.2, 86.97)]
RAW_ACT_B = [(18.4, 60.56), (32.2, 60.56), (32.2, 61.45), (34.85, 61.45), (34.85, 62.15), (35.6, 62.15), (35.6, 83.7),
             (28.6, 83.7), (28.6, 63.44), (18.4, 63.44)]
# D-S8-05: west edge 29.75 beside the ARM1_SENSE lane (x 28.53) for y 65.4-76.6, so the GND between the lane and the pour
# is 0.69 mm wide (0.30 at 29.4: an unstitched 10.9 mm GND finger); fix pass 1 (R9P1-PLANES-01) carries the 29.75 edge
# past the lane's turn at y 75.64 to 76.6 (it stepped back to 29.4 at 75.6, a 0.37 mm neck in that GND strip);
# D-S8-06: the pour covers the RAW bar's east end up to 0.3 mm off the ACT_GATE hop (y 87.4), where a 0.45 mm GND finger
# lay between the bar and the hop
RAW_ACT_F = [(29.75, 65.4), (35.75, 65.4), (35.75, 83.6), (31.15, 83.6), (31.15, 87.0), (26.9, 87.0), (26.9, 85.5),
             (29.4, 85.5), (29.4, 76.6), (29.75, 76.6)]

# ACT_FET_S: the F.Cu plate joins the B.Cu bridge on Q120's side (y 86.75) and on Q121's, beside its source row and
# north of each source pin (ring 0.06 mm off the pad, hole 0.21 mm off its paste: via_paste D87)
FET_S_VIAS = ([(x, 86.75) for x in (31.7, 32.75, 33.8, 34.85)] + [(35.45, 85.1)] +
              [(x, 84.2) for x in (32.1, 33.37, 34.64)])
# BAT_IN: two columns between J1.1 and Q120's drain tab, one more at the damper's corner
BAT_IN_VIAS = [(30.8, y) for y in (90.6, 91.8, 93.0, 94.2)] + [(29.6, y) for y in (90.6, 91.8, 93.0, 94.2)] + \
              [(32.0, 96.4)]
# the spine's field: a row and two columns round Q121's drain, then a 1.8 mm grid less the spots on C121.1's land (F)
# and on C150 / C151's lands (B) (a via in or at a pad's paste / mask opening: K-copper, D87)
RAW_GRID_SKIP = {(33.5, 67.8), (33.5, 69.6), (33.5, 71.4), (29.9, 73.2), (31.7, 73.2), (33.5, 73.2), (29.9, 75.0),
                 (31.7, 75.0), (33.5, 75.0)}
# R9P1-ROUTING-02: the row's two west vias opened into TP120's bare pad (1.5 mm at (30.2, 78.4)); its west via is
# dropped (the column below starts at 79.6) and (31.0, 78.2) moves 0.5 mm east, 0.4 mm of hole clear of the pad
RAW_ACT_VIAS = ([(x, 78.2) for x in (31.5, 32.2, 33.4, 34.6, 35.5)] + [(35.5, y) for y in (80.0, 81.4, 82.8)] +
                [(29.6, y) for y in (79.6, 81.0, 82.4)] +
                [p for p in grid(29.9, 35.3, 66.0, 76.8, 1.8, 1.8) if p not in RAW_GRID_SKIP])


def band(d, P):
    d.zone('R9_BAT_IN_B', 'BAT_IN', 'B', BAT_IN_B, 20)
    d.zone('R9_BAT_IN_F', 'BAT_IN', 'F', BAT_IN_F, 20)
    d.zone('R9_ACT_FET_S_B', 'ACT_FET_S', 'B', ACT_FET_S_B, 20)
    d.zone('R9_ACT_FET_S_F', 'ACT_FET_S', 'F', ACT_FET_S_F, 20)
    d.zone('R9_RAW_ACT_B', 'RAW_ACT', 'B', RAW_ACT_B, 20)
    d.zone('R9_RAW_ACT_F', 'RAW_ACT', 'F', RAW_ACT_F, 20)
    for at in FET_S_VIAS:
        d.via('ACT_FET_S', at)
    for at in BAT_IN_VIAS:
        d.via('BAT_IN', at)
    for at in RAW_ACT_VIAS:
        d.via('RAW_ACT', at)
    # J124.2's RAW branch: F.Cu on J124.2's pin line into the F.Cu spine (D-S5-08: the board's 1.0 mm width); it ends
    # 0.7 mm inside the pour's west edge (x 26.9, D-S8-06: a longer run inside the fill is a route_check pour_stub)
    j = P['J124.2']
    d.track('RAW_ACT', 'F', W_BIG, [j, (27.6, j[1])])


def battery(d, P):
    """BAT_IN taps (U9's IN feed, R80), the switch legs, the damper (D8 / C80 / C96 / R167 sit in the B pour)."""
    # U9's IN feed: C88.1 -> the IN bar's west end (the bar is 0.3 mm wide: a 0.3 mm track, 0.2 mm off FLT's and
    # DVDT's arms and the OUT bar)
    same(P.y('C88.1'), P.y('U9.5'), "C88.1 on U9.5's bar line")
    d.track('BAT_IN', 'B', W_FEED, [P['C88.1'], (P.box['U9.5'][0] + 0.3, P.y('U9.5'))])
    # R80 (BAT_IN -> the external switch's source leg): from the B pour down the channel between J1.3 and J1.2, 45
    # degrees into R80.1
    r = P['R80.1']
    xc = r4((P.box['J1.3'][2] + P.box['J1.2'][0]) / 2)
    d.track('BAT_IN', 'B', W_GATE, [(xc, 96.3), (xc, r[1] + (xc - r[0])), r])
    # switch legs straight down from the terminal pins
    for k, j in (('R80.2', 'J1.3'), ('R165.1', 'J1.4')):
        same(P.x(k), P.x(j), f'{k} under {j}')
        d.track(P.net[k], 'B', W_GATE, [P[j], P[k]])
    # damper: C89.2 == C95.2 (straight), C95.2 -> R166.1 (one 45-degree run, into the pad's centre)
    a, b2, rr = P['C89.2'], P['C95.2'], P['R166.1']
    same(a[0], b2[0], 'damper caps on one column')
    k = (r4(b2[0] + (rr[1] - b2[1])), rr[1])
    d.track('BAT_DAMP', 'F', W_BIG, [a, b2, k, rr])


def gate(d, P):
    """ACT_GATE / ACT_DRV / ACT_EN (B.Cu) and the F.Cu hop across the ACT_FET_S bridge (Q120.4 and Q121.4 sit at
    opposite corners of the face-to-face pair)."""
    g = 'ACT_GATE'
    q4 = P['Q121.4']
    yb = q4[1]                                         # the west gate bus on Q121.4's row (through C120.2's pad)
    tp = P['TP121.1']
    r = P['R120.2']
    vw = (26.6, 87.4)                                  # the hop's west via, between C120 and the BAT_IN pour
    d.track(g, 'B', W_GATE, [q4, (tp[0] + (tp[1] - yb), yb), tp])
    d.track(g, 'B', W_GATE, [(r[0], yb), r])
    d.track(g, 'B', W_GATE, [(vw[0], yb), vw])
    d.via(g, vw, VIA_SIG)
    q = P['Q120.4']
    r1 = P['R121.1']
    ve = (r1[0], 89.0)                                 # the hop's east via, north of R121 on Q120.4's side
    d.track(g, 'B', W_GATE, [q, (q[0] + (ve[1] - q[1]), ve[1]), ve])   # 45 degrees out of Q120.4's centre onto ve's row
    d.track(g, 'B', W_GATE, [r1, ve])
    d.via(g, ve, VIA_SIG)
    yh = vw[1]
    d.track(g, 'F', W_GATE, [vw, (ve[0] - 0.8, yh), (ve[0], yh + 0.8), ve])
    same(P.x('R121.2'), P.x('Q122.3'), 'R121 over Q122.3')
    d.track('ACT_DRV', 'B', W_GATE, [P['R121.2'], P['Q122.3']])
    for k in ('R122.2', 'R123.1'):
        same(P.x(k), P.x('Q122.1'), 'ACT_EN column')
    d.track('ACT_EN', 'B', W_SIG, [P['Q122.1'], P['R122.2'], P['R123.1']])


# ======================================================================================================================
# RAW_PROTECTED (the eFuse U9's output; D-S6-05, R8 D36 / D46)
# ======================================================================================================================
RP_COL_X = 42.3                                     # B.Cu column east of U9's OUT bar end (R92 aft of it)
RP_VIAS = [(42.3, 91.3), (42.3, 88.0)]              # U9's output to the F.Cu pour: two vias, so each barrel carries
                                                    # half of the rail: at most 1.62 A of the downstream limiters'
                                                    # 3.24 A (U7 1.24 A + U11 2.0 A); U9's own limit with R84 = 750 ohm
                                                    # is 3.96-4.84 A (TI SLVSFC9C 6.5 / Eq. 7), the fault case on the
                                                    # net itself (R9P1-POWER-02; R8's "2.2 A" was R5's 1.65 kohm R84)
# the F.Cu pour down the east column: from U9's vias (D9.1 on it) under C84's body to C82.1, 1.0 mm off the test-pad
# column (DRU bare test-pad rule) and 0.35 mm off C87 (top)
# D-S8-09: east edge x 41.3 from y 72.0 to 84.2 (was 42.85), so the C6 / C7 / C8 GND vias (x 41.9-42.2) sit in the F.Cu GND
# east of the pour (each was a via-only GND island inside it) and TP74 / TP88 reach them through that GND
RP_F = [(40.0, 91.6), (42.85, 91.6), (42.85, 84.2), (41.3, 84.2), (41.3, 72.0), (39.85, 72.0), (39.85, 86.2),
        (40.0, 86.2)]
V_IN1 = (39.3, 68.2)                                # U11 IN1 (B) / C97 (F), south of U11.2 between U11.3 and VLOGIC
V_R122 = (37.26, 80.9)                              # R122.1 (ACT_EN pull-up), between C84's pads
V_U7 = (42.15, 31.5)                                # the camera branch's drop to the camera eFuse U7 (R8 D46 + 4 mm)
P_C82 = (40.9, 72.4)                                # C82.1, where the U11 IN1 branch leaves the pour
RP_TRACKS = [   # layer, width, polyline
    ('F', W_RAIL, [P_C82, (39.3, 72.4), V_IN1]),                    # U11 IN1, west of C82.2
    ('F', W_RAIL, [V_IN1, (39.3, 67.175)]),                         # C97.1, straight under the via (D-S7-16)
    ('B', W_RAIL, [V_IN1, (39.3, 67.175)]),                                         # U11.2 (IN1)
    ('F', W_GATE, [V_R122, (40.2, 80.9)]),                                          # R122 from the pour
    ('B', W_GATE, [V_R122, (37.26, 82.0)]),                                         # R122.1
    ('F', W_RAIL, [(42.45, 70.4), (44.6, 70.4)]),                                   # TP81 off the camera branch (D-S8-11)
    # the camera branch (R8 D46): east of C82, south past TP83, east of the mid support (42, 59.5) at x 44.35 (0.55 mm
    # from its hole), back to x 42.15 between J9's pins and its mounting pads, down to U7's via
    ('F', W_RAIL, [P_C82, (42.45, 72.4), (42.45, 66.0), (44.35, 64.1), (44.35, 57.4), (42.15, 55.2), V_U7]),  # D-S8-09
    # B.Cu to C71.1, U7.3 / U7.4 and TP70, 1.0 mm aft of J123's pins (R8's y 29.6 lane is J123's pin row in R9)
    ('B', W_RAIL, [V_U7, (36.675, 31.5), (35.8, 30.625), (34.55, 30.625), (34.55, 33.75)]),
    ('B', W_GATE, [(34.55, 33.75), (34.05, 33.75)]),
    ('B', W_RAIL, [(35.8, 28.9), (35.8, 30.625)]),
]
RP_VIAS_OTHER = [(V_IN1, VIA_PWR), (V_R122, VIA_SIG), (V_U7, VIA_PWR)]


def efuse(d, P):
    rp = 'RAW_PROTECTED'
    o = P['U9.6']
    xc = RP_COL_X
    same(P.x('C82.1'), P_C82[0], 'C82.1 on the IN1 branch')
    same(P.y('C82.1'), P_C82[1], 'C82.1 on the IN1 branch')
    d.track(rp, 'B', W_FEED, [(P.box['U9.6'][2] - 0.3, o[1]), (xc, o[1])])
    d.track(rp, 'B', W_FEED, [P['R92.1'], (xc, P.y('R92.1')), (xc, RP_VIAS[1][1]), (xc, o[1]), (xc, RP_VIAS[0][1])])
    for at in RP_VIAS:
        d.via(rp, at)
    d.zone('R9_RAW_PROTECTED_F', rp, 'F', RP_F, 20)
    for layer, w, pts in RP_TRACKS:
        d.track(rp, layer, w, pts)
    for at, size in RP_VIAS_OTHER:
        d.via(rp, at, size)


# ======================================================================================================================
# Logic supplies (D-S6-06): VLOGIC (U11 OUT), the 3V3 buck U2 (Diodes DS41326 Figure 25), 3V3 into In2 (R8 D40 / D42)
# ======================================================================================================================
V_HOLDUP = (38.5, 69.6)                             # VLOGIC to the hold-up C84 (top); x 38.5, 0.4 mm off the U11 IN1
                                                    # branch (x 39.3): no GND finger between them (D-S8-10)
V_TP83 = (43.35, 78.2)                              # VLOGIC to TP83 (top), west of it (D-S7-16: TP83's new slot)
V_FB = (37.3, 71.3)                                 # U2.1 (FB of the fixed 3.3 V part) senses In2's 3V3 finger
V_3V3 = (37.6, 78.9)                                # the buck's output into the In2 3V3 finger
LOGIC_TRACKS = [   # net, layer, width, polyline
    # U11.8 -> U11.1 -> C99.1 -> U2.2 (EN) -> U2.3 (VIN) -> C6.1 -> the C7 / TP83 column (x 44.6)
    ('VLOGIC', 'B', W_RAIL, [(40.0, 65.825), (40.0, 69.6), (40.0, 70.6), (44.6, 70.6)]),
    ('VLOGIC', 'B', W_RAIL, [(44.6, 70.6), (44.6, 74.8), (43.3, 74.8)]),
    ('VLOGIC', 'B', W_RAIL, [(44.6, 74.8), (44.6, 77.45), (43.85, 78.2), V_TP83]),      # on to TP83 (D-S7-16)
    ('VLOGIC', 'F', W_RAIL, [V_TP83, (44.6, 78.2)]),
    ('VLOGIC', 'B', W_RAIL, [(40.0, 69.6), V_HOLDUP]),
    ('VLOGIC', 'F', W_RAIL, [V_HOLDUP, (38.5, 73.2), (37.5, 74.2)]),               # C84.1 (4.4 x 1.9 mm pad)
    # the switching node: U2.5 straight into L1.1 (1.0 mm past the pin row); C5 bootstrap (BST U2.6, SW L1.1)
    ('SW_NODE', 'B', W_RAIL, [(40.0, 73.0), (40.0, 73.9)]),
    ('SW_NODE', 'B', W_BIG, [(40.0, 73.9), (40.0, 75.0)]),
    ('SW_NODE', 'B', W_RAIL, [(37.2, 73.82), (37.2, 74.6), (38.6, 74.6)]),
    ('BST', 'B', W_FEED, [(39.05, 73.0), (37.2, 73.0)]),
    # 3V3: L1.2 -> C8.1 -> C9.1 (1.0 mm), one via into the In2 finger; FB on its own via into the finger
    ('3V3', 'B', W_BIG, [(40.0, 78.2), (40.0, 78.9), (40.0, 80.28), (40.0, 82.24)]),
    ('3V3', 'B', W_RAIL, [(40.0, 78.9), V_3V3]),
    ('3V3', 'B', W_SIG, [(39.05, 70.6), (39.05, 71.3), V_FB]),
]
LOGIC_VIAS = [('VLOGIC', V_HOLDUP, VIA_PWR), ('VLOGIC', V_TP83, VIA_PWR), ('3V3', V_FB, VIA_SIG),
              ('3V3', V_3V3, VIA_PWR)]

# ======================================================================================================================
# Camera supplies (D-S6-07; R8 D37 / D41): R8's CAMERA_TRACKS / CAMERA_GND moved with the camera block (+4 mm in y),
# widths mapped onto the board's six (0.25 -> 0.25, 0.3 -> 0.3, 0.5 / 0.6 / 0.8 -> 1.0, 0.7 SW strap -> 0.4: 1.0 mm
# would sit 0.1 mm from U8.4 / U8.6)
# ======================================================================================================================
V_CAM_FB = (38.25, 37.1)
V_CAM_5V = (40.75, 45.4)
CAMERA_TRACKS = [
    ('CAM_INPUT_LIMITED', 'B', W_GATE, [(34.55, 35.65), (35.4, 35.65)]),
    ('CAM_INPUT_LIMITED', 'B', W_BIG, [(35.4, 35.65), (43.41, 35.65)]),                  # through TP71
    ('CAM_INPUT_LIMITED', 'B', W_BIG, [(43.41, 35.85), (43.41, 37.45)]),
    ('CAM_INPUT_LIMITED', 'B', W_BIG, [(40.9, 37.85), (43.41, 37.85)]),
    ('CAM_INPUT_LIMITED', 'B', W_FEED, [(39.95, 37.85), (40.9, 37.85)]),
    ('GND', 'B', W_RAIL, [(40.9, 40.05), (43.41, 40.05)]),                                 # U8.4 -> C72.2
    ('CAM_SW', 'B', W_RAIL, [(39.95, 40.05), (39.95, 42.47)]),                             # U8.5 -> L3.1
    ('CAM_SW', 'B', W_RAIL, [(36.1, 41.61), (39.95, 41.61)]),                              # C74.1
    ('CAM_BST', 'B', W_FEED, [(39.0, 40.05), (36.1, 40.05)]),                              # U8.6 -> C74.2
    ('CAM_FB', 'B', W_GATE, [(39.0, 37.85), V_CAM_FB]),
    ('CAM_FB', 'F', W_GATE, [V_CAM_FB, (38.675, 37.1)]),
    ('CAM_FB', 'F', W_GATE, [(38.675, 36.3), (38.675, 37.1), (38.675, 37.9), (38.675, 39.5)]),
    ('CAM_5V', 'B', W_BIG, [(38.85, 47.17), (38.85, 50.07)]),
    ('CAM_5V', 'B', W_BIG, [(35.29, 46.45), (39.2, 46.45)]),
    ('CAM_5V', 'B', W_FEED, [(39.95, 47.17), (44.2, 47.17)]),
    ('CAM_5V', 'B', W_FEED, [(38.5, 49.2), (36.325, 49.2)]),
    ('CAM_5V', 'B', W_BIG, [V_CAM_5V, (40.75, 47.17)]),
    ('CAM_5V', 'F', W_RAIL, [V_CAM_5V, (40.75, 46.325)]),                                # J9.1
    ('CAM_5V', 'F', W_GATE, [(40.3, 37.9), (40.3, 39.5), (40.3, 44.95), V_CAM_5V]),        # sense at J9.1
]
CAMERA_GND = [   # layer, pad, via, size
    ('B', (43.41, 40.45), (43.41, 41.6), VIA_PWR), ('B', (43.41, 32.85), (43.41, 31.8), VIA_PWR),
    ('B', (41.4, 50.07), (41.4, 51.8), VIA_SIG), ('B', (35.29, 43.16), (34.4, 42.27), VIA_PWR),
    ('B', (34.675, 49.2), (34.675, 50.15), VIA_SIG),     # R78.2: north under U12 (D-S7-13), its old spot is OE's
]

# ======================================================================================================================
# U1's decoupling and VCAP (D-S6-08; R8 spike (a), D31): R8's DECOUPLING_TRACKS / VIAS moved with U1 (-5, -0.5); C13
# and C14 (placed differently in R9) get their own taps; the 3V3A pocket (C21 / C22 / U1.20-21) is step 7's (step-5
# handoff)
# ======================================================================================================================
DECOUPLING_TRACKS = [   # net, layer, polyline (0.2 mm)
    ('3V3', 'B', [(21.13, 44.6), (23.0, 44.6), (23.75, 44.6)]),                    # U3.8 -> C29 -> via
    ('VCAP2', 'F', [(13.0, 36.95), (13.0, 38.8)]), ('VCAP2', 'B', [(13.0, 38.8), (14.1, 38.8)]),
    ('3V3', 'F', [(12.0, 36.95), (12.0, 38.25)]), ('3V3', 'B', [(12.0, 38.25), (12.0, 38.98)]),
    ('VCAP1', 'F', [(25.55, 39.5), (24.25, 39.5)]), ('VCAP1', 'B', [(24.25, 39.5), (23.35, 39.5)]),
    ('3V3', 'F', [(25.55, 38.5), (24.25, 38.5)]), ('3V3', 'B', [(24.25, 38.5), (23.87, 38.12), (23.52, 38.12)]),
    ('3V3', 'F', [(25.55, 50.0), (24.2, 50.0)]), ('3V3', 'B', [(24.2, 50.0), (24.2, 49.32)]),
    ('3V3', 'F', [(14.5, 52.05), (14.5, 50.65)]), ('3V3', 'B', [(14.5, 50.65), (13.72, 50.65)]),
    ('3V3', 'F', [(10.45, 50.5), (10.45, 51.3)]), ('3V3', 'B', [(10.45, 51.3), (9.85, 51.3)]),     # U1.100 -> C13
    ('GND', 'B', [(9.85, 52.02), (9.85, 52.8)]),
    ('3V3', 'F', [(17.0, 52.05), (17.0, 52.95), (16.35, 53.6), (15.2, 53.6)]),                       # C14
    ('3V3', 'B', [(15.2, 53.6), (15.98, 53.6)]),
    ('GND', 'B', [(16.82, 53.6), (16.82, 55.3)]),
    ('3V3', 'B', [(23.52, 36.8), (23.52, 38.12)]),                                  # C23 -> C16.1 (D-S7-11)
    ('GND', 'B', [(24.2, 48.48), (24.2, 47.7)]), ('GND', 'B', [(15.5, 38.8), (16.4, 38.8)]),
    ('GND', 'B', [(12.88, 50.65), (12.88, 50.37), (13.2, 50.05)]),                 # C18.2 (D-S7-10: off U4's north)
    ('GND', 'B', [(23.35, 40.65), (24.25, 40.65)]),                               # C19.2 (D-S7-14)
    ('GND', 'B', [(12.5, 40.8), (14.07, 40.8)]),                                       # U3.4
]
DECOUPLING_VIAS = [('3V3', (23.75, 44.6)), ('VCAP2', (13.0, 38.8)), ('3V3', (12.0, 38.25)), ('VCAP1', (24.25, 39.5)),
                   ('3V3', (24.25, 38.5)), ('3V3', (24.2, 50.0)), ('3V3', (14.5, 50.65)), ('3V3', (10.45, 51.3)),
                   ('GND', (9.85, 52.8)), ('3V3', (15.2, 53.6)), ('GND', (16.82, 55.3)),
                   ('GND', (24.2, 47.7)), ('GND', (16.4, 38.8)), ('GND', (13.2, 50.05)), ('GND', (24.25, 40.65)),
                   ('GND', (12.5, 40.8))]

# ======================================================================================================================
# GND of the power parts (the switching and clamp loops, the bulk and input caps); the small parts' GND pads are step
# 8's pours, U9's / U11's own GND pins step 7's (power_ctl: they sit between the control pins)
# ======================================================================================================================
G_R92 = (42.4, 84.725)          # R92.2's GND via (In2 GND), off the strap to C9.2 that BAT_ILIM's lane needs (D-S7-16)
GND_TRACKS = [   # layer, width, polyline
    ('B', W_RAIL, [(30.2, 73.6), (31.4, 73.6), (32.6, 73.6)]),     # C150.2 / C151.2 (RAW_ACT bulk) in the spine
    ('B', W_BIG, [(40.95, 73.0), (42.75, 73.0)]),                  # U2.4 -> C6.2: the buck's input loop, one strap
    ('B', W_RAIL, [(41.9, 73.0), (41.9, 73.75)]),                  # its via, off the strap's body (beside L1.1)
    ('B', W_RAIL, [(42.0, 80.28), (42.0, 81.26), (42.0, 82.24)]),  # C8.2, C9.2 (the output caps) and their via
    ('B', W_RAIL, [(43.3, 76.8), (42.2, 76.8)]),                   # C7.2
    ('B', W_RAIL, [(38.3, 83.5), (39.2, 83.5)]),                   # Q122.2 (the gate driver's source)
    ('B', W_GATE, [(36.4, 80.13), (38.5, 80.13)]),                 # R123.2
    ('B', W_GATE, [(43.1, 85.425), G_R92]),                       # R92.2 to its own via (D-S7-16)
    ('B', W_FEED, [(38.2, 89.81), (38.6, 89.41), (38.6, 88.2)]),   # C88.2 (U9's input cap)
    ('F', W_RAIL, [(38.6, 88.2), (38.6, 89.6)]),                   # D9.2 (the output clamp)
    ('F', W_BIG, [(36.5, 90.4), (38.6, 90.4)]),                    # R166.2 (the damper) -> D9.2
    ('B', W_RAIL, [(40.8, 67.25), (40.8, 68.25), (40.8, 68.9)]),   # U11.12, C99.2
    ('F', W_RAIL, [(40.8, 68.25), (40.8, 69.4)]),                  # C82.2
    ('F', W_RAIL, [(39.3, 65.625), (40.8, 67.125), (40.8, 68.25)]),  # C97.2
    # the battery input: the TVS D8 straight to J1.2 (the hot-plug clamp loop), the input caps and the bleed
    ('B', W_BIG, [(22.85, 89.2), (22.85, 91.8), (22.85, 94.4)]),
    ('B', W_RAIL, [(22.85, 89.2), (20.9, 89.2)]),
    ('B', W_RAIL, [(22.525, 99.7), (22.525, 101.1)]),              # C96.2
    ('B', W_RAIL, [(17.525, 99.7), (17.525, 101.1)]),              # C80.2
    ('B', W_RAIL, [(31.325, 99.6), (31.325, 101.1)]),              # R167.2
]
GND_VIAS = [(31.4, 73.6), (41.9, 73.75), (42.0, 81.26), (42.2, 76.8), (39.2, 83.5), (38.5, 80.13), (38.6, 88.2),
            (40.8, 68.25), (20.9, 89.2), (22.85, 91.8), (22.525, 101.1), (17.525, 101.1), (31.325, 101.1)]
# GND vias whose only GND layer is In1 until step 8 pours it (In2 under them is 3V3 or RAW_ACT; their B.Cu / F.Cu
# straps join a pad), and the copper that feeds them: DRC via_dangling and route_check dead_copper until then
PENDING = [(24.25, 40.65), (12.5, 40.8), (16.4, 38.8), (9.85, 52.8), (16.82, 55.3), (24.2, 47.7), (13.2, 50.05),
           (31.4, 73.6)]


def logic(d, P):
    for net, layer, w, pts in LOGIC_TRACKS:
        d.track(net, layer, w, pts)
    for net, at, size in LOGIC_VIAS:
        d.via(net, at, size)


def camera(d, P):
    for net, layer, w, pts in CAMERA_TRACKS:
        d.track(net, layer, w, pts)
    d.via('CAM_FB', V_CAM_FB, VIA_PWR)
    d.via('CAM_5V', V_CAM_5V, VIA_PWR)
    for layer, pad, at, size in CAMERA_GND:
        d.track('GND', layer, W_RAIL, [pad, at])
        d.via('GND', at, size)
    d.track('GND', 'F', W_FEED, [(40.325, 36.3), (41.15, 36.3), (41.45, 36.6)])     # R72.2 (top)
    d.via('GND', (41.45, 36.6), VIA_SIG)


def decoupling(d, P):
    for net, layer, pts in DECOUPLING_TRACKS:
        d.track(net, layer, W_SIG, pts)
    for net, at in DECOUPLING_VIAS:
        d.via(net, at, VIA_SIG)


def ground(d, P):
    for layer, w, pts in GND_TRACKS:
        d.track('GND', layer, w, pts)
    for at in GND_VIAS:
        d.via('GND', at, VIA_PWR)
    d.via('GND', G_R92, VIA_SIG)


SECTIONS = [in2, band, battery, gate, efuse, logic, camera, decoupling, ground]


def build(b, dry=False):
    P = Pads(b)
    d = Draw(b, dry)
    for section in SECTIONS:
        section(d, P)
    return d


def check_vias(b, d):
    """Every via keeps the net it was drawn with after connectivity (a via landing on foreign copper is re-netted by
    KiCad's connectivity: spike (c)'s pitfall, R8)."""
    bad = []
    for t in b.GetTracks():
        if t.GetClass() != 'PCB_VIA':
            continue
        at = (r4(mm(t.GetPosition().x)), r4(mm(t.GetPosition().y)))
        if at in d.vias and t.GetNetname() != d.vias[at]:
            bad.append(f'{at}: drawn {d.vias[at]}, now {t.GetNetname()}')
    assert not bad, 'vias re-netted:\n  ' + '\n  '.join(bad)


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
    d = build(b)
    if not args.no_fill:
        b.BuildConnectivity()
        assert pcbnew.ZONE_FILLER(b).Fill(b.Zones()), 'native zone fill failed'
    b.BuildConnectivity()
    check_vias(b, d)
    out = (args.out or board).resolve()
    assert pcbnew.SaveBoard(str(out), b, True), 'save failed'
    print(f'r9_power: {len(d.tracks)} segments, {len(d.vias)} vias, {len(d.zones)} zones')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
