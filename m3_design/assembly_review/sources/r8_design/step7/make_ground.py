#!/usr/bin/env python3
"""Generate m3_design/r8_ground.tsv: the R8 GND stitching copper (build step 7; R8_DECISIONS D62 on).

usage: <KiCad python3> -I make_ground.py BOARD OUT.tsv [--built]

BOARD is the step-6 board (r8_route.py links output, filled) with m3.kicad_pro / m3.kicad_dru beside it. With --built,
BOARD is a built board (r8_ground.py's output): the items of the current m3_design/r8_ground.tsv are removed from it
(in memory) and the zones refilled, which gives back the step-6 board, so a regeneration can be checked against the
committed table (two-pass: it must reproduce it byte for byte). The design aid writes only OUT.tsv.

Rows (each with its basis; r8_ground.py draws them in this order, r8_ground_check.py gates the result), generated in
this order, each stage on the board refilled after the one before:
  fence    the strip fence row (D16, check_r8 fence): spike (d)'s FENCE_X at y 23.3, its 25 reservations
  stitch   spike (d)'s two stitching vias above the fence (the MISO-MOSI slot and the NSS-SCK gap)
  c24      spike (a)'s C24 GND stub and via (NRST's decoupling return under U1)
  trim     TRIMS: fill keep-outs over the GND pieces no second via can reach (D65); drawn before the vias
  return   a GND via within RETURN_REACH of every power-net layer change that has none (route_check power_via_no_gnd;
           AGENTS 3 asks it of critical signals, which step 6 already meets: the plan's "GND via at every critical
           layer change" holds for both)
  grid     the stitching grid (r8_plan step 7: <= 4 mm): one GND via per node of a PITCH lattice over the board, at the
           legal spot nearest the node within SNAP, unless a GND via already lies within SERVED of it
  cover    greedy: while a point of the outer GND pours lies more than COVER from every GND via, the legal spot that
           brings most such points (raster RASTER) within COVER, while it brings at least MIN_GAIN
  island   every outer (F / B) GND pour island with fewer than two GND vias or plated GND holes gets them, up to four
           rounds (P7); an island no legal spot reaches is printed (the D4.2 pocket, D63)
  pad      every GND SMD pad of an IC (a U part with four or more pads, forward of the strip) whose copper reaches a GND
           via or plated GND hole only beyond PAD_REACH gets the legal spot its own copper reaches soonest, when that
           spot is within PAD_REACH of copper (fix pass 2, R8P2-PLANES-01, D102: TI SLVSFC9C 8.4.1 asks for the eFuse
           U9's GND terminal tied to the plane at the IC, and D62's cover step judges Euclidean distance only); a pad
           no legal spot serves is printed
Every via is VIA (0.5 / 0.3 mm, the board's stitching and fence via) and keeps >= SPACING from every GND via.

The through-hole GND pins of r8_ground.RELIEF_PADS are given their thermal relief first, as r8_ground.py does before
it draws the table (D101), so the model is the board that stage fills.

A legal spot (legal()) is a via centre that, for every copper layer:
  - lies in an outer GND pour fill (F or B), >= EDGE from the outline, >= 23.55 mm from the aft edge (the strip's GND
    vias are rigid, check_r8 strip_gnd; only the fence row is not);
  - keeps the board rules plus MARGIN from every other net's track, via and pad (0.15 mm; RF nets 0.25; J30 / J31
    pads 0.30; bare test pads 1.0; J2 0.508; RAW_ACT pins 0.30; a pad's own local clearance), and Pyro D's 0.5 mm from
    the copper (fills included) of every pyro and arming net (rule D names the bus, igniter and drain; it is kept from
    the gate and sense nets too);
  - keeps hole to hole and copper to hole 0.25 mm, 0.52 mm from Edge.Cuts circles, stays out of rule areas that
    forbid vias (the sensors') and off GND tracks (no overlap joint; the CH1 block's GND ties stay as they are);
  - stays off the body of every part with two or three pads (the convex hull of its pads: passives, inductors,
    diodes, SOT-23s, terminals);
  - is 0.3 mm (SMD) / 0.25 mm (through-hole) clear of GND pads, 0.1 mm from paste apertures and its hole 0.1 mm from
    SMD mask openings (check_r7 vias_in_smd_pads);
  - cuts no outer power pour (0.3 mm from every non-GND F / B fill), no In2 power island inside its 7.7 A corridor
    (the box round tools/run_dc.sh's terminal pads + 2 mm: RAW_ACT, BAT_IN, ACT_FET_S), and puts no In2 antipad
    under a B.Cu track that runs over a non-GND In2 fill (its reference, D47);
  - revives no removed GND island on the other outer layer (dormant(): an island held by that one via), except in the
    island step, which gives every island it revives a second via in a later round.
"""
import argparse
import csv
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
TABLE = ROOT / 'm3_design/r8_ground.tsv'
mm, MM = pcbnew.ToMM, pcbnew.FromMM
F, IN1, IN2, B = pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu
CU4 = (F, IN1, IN2, B)
ERR = MM(0.005)

VIA = (0.5, 0.3)              # mm: diameter, drill (spike (d)'s fence and stitching via; VIA_SIG in r8_route.py)
MARGIN = 0.02                 # mm over every rule (r7_route.ViaCheck's practice)
EDGE = 1.0                    # mm, via centre to the outline
STRIP_Y = 23.5                # check_r7 STRIP_Y: GND vias aft of it are rigid (strip_gnd), the fence row excepted
SPACING = 1.0                 # mm, GND via centre to GND via centre
RETURN_REACH = 1.5            # mm (route_check GND_REACH)
PITCH = 4.0                   # mm, r8_plan step 7: a stitching grid at <= 4 mm
GRID_X0, GRID_Y0 = 3.0, 27.3  # lattice origin: columns 3, 7, ... 43; rows 4 mm forward of the fence row
SNAP = 1.0                    # mm: a node's via within this of the node
SERVED = 2.0                  # mm: a node with a GND via this close needs none
COVER = 3.0                   # mm
RASTER = 0.5                  # mm (survey_metrics' stitching raster)
MIN_GAIN = 6                  # raster points (1.5 mm2)
PAD_REACH = 4.0               # mm of copper from an IC GND pad to a GND via or plated GND hole (D102)
PAD_RASTER = 0.1              # mm, the pad stage's copper-distance raster (R8 pass 2 planes' gndpads method)
STEP = 0.05                   # mm, the spot search grid
LEFTOVER = 1.0                # mm2: unconnected GND crumbs a trim may leave (dropped by the fill)

FENCE_Y = 23.3
# spike (d) rf_route_r8.FENCE_X / STITCH, but for fix pass 4 (R8P4-ROUTING-01, D110): the radio trio's opening
# vias x 20.00 / 22.10 -> 19.95 / 22.05 and the MISO-MOSI slot's stitch via x 22.10 -> 22.05, centring the trio
# (r8_route_rf.TRIO, 0.1 mm west) so RXEN, MISO and MOSI keep 0.200 mm from them (were 0.250 / 0.150 / 0.150 mm)
FENCE_X = (0.90, 2.90, 4.90, 6.40, 7.685, 9.70, 12.30, 14.20, 16.20, 18.20, 19.95, 22.05, 24.15, 26.00, 28.00, 30.00,
           31.80, 33.00, 34.40, 35.80, 37.80, 39.40, 40.60, 42.60, 44.60)
STRIP_STITCH = ((22.05, 26.70), (24.15, 26.50))
C24_STUB = ((26.17, 51.1), (26.95, 51.1))       # spike (a) spike_geom: C24.2 -> its GND via, B.Cu 0.2 mm
# Pour trims (fill keep-out rule areas, one layer each): the GND pieces no second via can reach, which step 6's lanes
# enclose. Each outline runs on the centre lines of the lanes that bound the piece (or round a lone via), so it removes
# that piece and nothing else (generate() asserts it by fill area); route_check's pad_pour_cut gates the pads.
TRIMS = [
    ('R8_POUR_TRIM_G1', 'F', [(12.0, 59.57), (12.5, 59.57), (12.5, 60.32), (10.47, 62.35), (9.22, 62.35)],
     'finger between the I2C diagonals over U5 (BARO_body_B: no via)'),
    ('R8_POUR_TRIM_G2', 'F', [(9.5, 50.5), (11.25, 50.5), (11.25, 55.65), (9.5, 55.65)],
     'island between SPI1_MOSI and IMU_CS over U4 (IMU_body_B: no via; one GND via)'),
    ('R8_POUR_TRIM_G3', 'B', [(9.5, 51.5), (11.21, 51.5), (11.21, 52.45), (9.5, 52.45)],
     "island inside U4's 3V3A loop round its GND via (10.5, 52.1)"),
    ('R8_POUR_TRIM_G4', 'B', [(19.28, 104.09), (19.91, 104.09), (19.91, 104.71), (19.28, 104.71)],
     "the band GND via (19.6, 104.4)'s ring in the BAT_IN pour (r8_power BAND_GND_VIAS)"),
    ('R8_POUR_TRIM_G5', 'F', [(22.6, 14.4), (23.0, 14.0), (24.4, 14.0), (24.4, 15.27), (23.6, 15.27), (23.2, 15.67),
                              (22.6, 15.67)],
     'island between RADIO_MOSI and RADIO_NSS at U31 (strip: GND vias rigid; one GND via)'),
    ('R8_POUR_TRIM_G6', 'B', [(37.9, 31.65), (43.2, 31.65), (43.2, 33.5), (37.9, 33.5)],
     "island between CAM_INPUT_LIMITED's B.Cu lane and U8's input pins (R72 and the RAW_PROTECTED trunk close it)"),
    # fix pass 1 (R8P1-RF-01 / R8P1-PLANES-01, D90): outline on the two lanes' centre lines (NSS x - y = -7.072, SCK
    # x - y = -5.6), from y 30.3 (below R310.2 / R313.1) to the lanes' turns at U1's east face
    ('R8_POUR_TRIM_G7', 'F', [(31.65, 38.722), (32.25, 38.722), (32.25, 37.85), (25.1, 30.7), (25.1, 30.3),
                              (23.228, 30.3)],
     'finger between the RADIO_NSS and RADIO_SCK_MCU diagonals (0.54 mm wide, its tip 15.1 mm of copper from a GND '
     'via; a via needs 0.84 mm, the gap is 0.841 mm)'),
]

RF_NETS = ('GNSS_RF_ANT', 'GNSS_RF_IN', 'RADIO_RF_ANT', 'RADIO_RF')
PYRO = re.compile(r'^(PYRO1_|ARM1_)')
BARE = re.compile(r'^(TP\d+|J2)$')
CORRIDORS = {'BAT_IN': [('J1', {'1'}), ('Q120', {'5', '6', '7', '8', '9'})],          # tools/run_dc.sh terminals
             'RAW_ACT': [('Q121', {'5', '6', '7', '8', '9'}), ('J122', {'2', '5', '8', '11'})],
             'ACT_FET_S': [('Q120', {'1', '2', '3'}), ('Q121', {'1', '2', '3'})]}
POWER_CLASS = None            # route_check.net_class, bound in main()


def P(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


def r4(v):
    return round(v + 0.0, 4)


def rect(x0, y0, x1, y1):
    s = pcbnew.SHAPE_POLY_SET()
    s.NewOutline()
    for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        s.Append(MM(x), MM(y))
    return s


def fill(z, lid):
    f = pcbnew.SHAPE_POLY_SET(z.GetFilledPolysList(lid))
    f.Unfracture()
    return f


def clearance(net, pad=None):
    """Board rule (mm) between a new GND via and other-net copper, plus MARGIN."""
    c = 0.15
    if net in RF_NETS:
        c = 0.25
    if PYRO.match(net or ''):
        c = 0.5
    if pad is not None:
        ref = pad.GetParentFootprint().GetReference()
        if ref in ('J30', 'J31'):
            c = max(c, 0.30)
        if ref.startswith('TP') and pad.GetAttribute() == pcbnew.PAD_ATTRIB_SMD:
            c = max(c, 1.0)
        if ref == 'J2':
            c = max(c, 0.508)
        if pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH and net == 'RAW_ACT':
            c = max(c, 0.3)
        if pad.GetLocalClearance():
            c = max(c, mm(pad.GetLocalClearance()))
    return c + MARGIN


def circle(p, radius, out):
    pcbnew.SHAPE_CIRCLE(p, MM(radius)).TransformToPolygon(out, ERR, pcbnew.ERROR_OUTSIDE)


def refill(b):
    for z in b.Zones():
        if not z.GetIsRuleArea():
            z.UnFill()
    b.BuildConnectivity()
    assert pcbnew.ZONE_FILLER(b).Fill(b.Zones()), 'native zone fill failed'
    b.BuildConnectivity()


def dormant(b):
    """{layer: SHAPE_POLY_SET} of the outer GND pour's removed islands: what a fill that kept islands would add. A via
    there would revive an island held by that via alone; the board's own fill is restored before returning."""
    zones = [z for z in b.Zones() if not z.GetIsRuleArea() and z.GetNetname() == 'GND']
    before = outer_gnd(b)
    modes = [z.GetIslandRemovalMode() for z in zones]
    for z in zones:
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_NEVER)
    refill(b)
    kept = outer_gnd(b)
    for z, m in zip(zones, modes):
        z.SetIslandRemovalMode(m)
    refill(b)
    after = outer_gnd(b)
    out = {}
    for lid in (F, B):
        assert abs(before[lid].Area() - after[lid].Area()) < 1e6, 'a refill changed the outer GND fill'
        extra = pcbnew.SHAPE_POLY_SET(kept[lid])
        extra.BooleanSubtract(after[lid])
        out[lid] = extra
    return out


def small_body(f):
    """The convex hull of the copper pads of a part with two or three of them (passives, diodes, inductors, SOT-23s,
    terminals): its body between the pads; None for other parts."""
    pads = [p for p in f.Pads() if p.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH]
    if not 2 <= len(pads) <= 3:
        return None
    pts = set()
    for p in pads:
        lid = F if p.IsOnLayer(F) else B
        ps = pcbnew.SHAPE_POLY_SET()
        p.TransformShapeToPolygon(ps, lid, 0, ERR, pcbnew.ERROR_OUTSIDE)
        for i in range(ps.OutlineCount()):
            o = ps.Outline(i)
            pts.update((o.CPoint(k).x, o.CPoint(k).y) for k in range(o.PointCount()))
    pts = sorted(pts)

    def cross(o, a, c):
        return (a[0] - o[0]) * (c[1] - o[1]) - (a[1] - o[1]) * (c[0] - o[0])
    lo, hi = [], []
    for q in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], q) <= 0:
            lo.pop()
        lo.append(q)
    for q in reversed(pts):
        while len(hi) >= 2 and cross(hi[-2], hi[-1], q) <= 0:
            hi.pop()
        hi.append(q)
    hull = pcbnew.SHAPE_POLY_SET()
    hull.NewOutline()
    for x, y in lo[:-1] + hi[:-1]:
        hull.Append(int(x), int(y))
    return hull


def legal(b, revive=False):
    """SHAPE_POLY_SET of the legal centres of a new VIA GND via (module docstring); revive=True drops the dormant-island
    rule (the island step, which then gives a revived island its second via too)."""
    r = VIA[0] / 2
    sleeping = {F: pcbnew.SHAPE_POLY_SET(), B: pcbnew.SHAPE_POLY_SET()} if revive else dormant(b)
    hole = VIA[1] / 2
    forbid = pcbnew.SHAPE_POLY_SET()
    for t in b.GetTracks():
        n = t.GetNetname()
        if t.GetClass() == 'PCB_VIA':
            if n == 'GND':
                circle(t.GetPosition(), SPACING, forbid)
            else:
                for lid in CU4:
                    t.TransformShapeToPolygon(forbid, lid, MM(clearance(n) + r), ERR, pcbnew.ERROR_OUTSIDE)
            circle(t.GetPosition(), mm(t.GetDrillValue()) / 2 + 0.25 + hole + MARGIN, forbid)
        elif n == 'GND':
            t.TransformShapeToPolygon(forbid, t.GetLayer(), MM(r + 0.05), ERR, pcbnew.ERROR_OUTSIDE)
        else:
            t.TransformShapeToPolygon(forbid, t.GetLayer(), MM(clearance(n) + r), ERR, pcbnew.ERROR_OUTSIDE)
    for f in b.GetFootprints():
        ref = f.GetReference()
        body = small_body(f)
        if body is not None:
            body.Inflate(MM(r + MARGIN), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, ERR)
            forbid.BooleanAdd(body)
        for p in f.Pads():
            n = p.GetNetname()
            att = p.GetAttribute()
            for lid in CU4:
                if not p.IsOnLayer(lid) or att == pcbnew.PAD_ATTRIB_NPTH:
                    continue
                if n == 'GND':
                    c = 0.3 if att == pcbnew.PAD_ATTRIB_SMD else 0.25
                else:
                    c = clearance(n, p)
                p.TransformShapeToPolygon(forbid, lid, MM(c + r), ERR, pcbnew.ERROR_OUTSIDE)
            for lid in (pcbnew.F_Paste, pcbnew.B_Paste):
                if p.IsOnLayer(lid):
                    p.TransformShapeToPolygon(forbid, lid, MM(0.1 + r + MARGIN), ERR, pcbnew.ERROR_OUTSIDE)
            if att in (pcbnew.PAD_ATTRIB_SMD, pcbnew.PAD_ATTRIB_CONN) and not BARE.match(ref):
                for cu, mk in ((F, pcbnew.F_Mask), (B, pcbnew.B_Mask)):
                    if p.IsOnLayer(cu) and p.IsOnLayer(mk):
                        grow = max(0.0, mm(p.GetSolderMaskExpansion(mk))) + 0.1 + hole + MARGIN
                        p.TransformShapeToPolygon(forbid, cu, MM(grow), ERR, pcbnew.ERROR_OUTSIDE)
            if att in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH):
                circle(p.GetPosition(), mm(max(p.GetDrillSize().x, p.GetDrillSize().y)) / 2 + 0.25 + r + MARGIN,
                       forbid)
    in2_power = pcbnew.SHAPE_POLY_SET()
    for z in b.Zones():
        if z.GetIsRuleArea():
            if z.GetDoNotAllowVias():
                o = pcbnew.SHAPE_POLY_SET(z.Outline())
                o.Inflate(MM(r + MARGIN), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, ERR)
                forbid.BooleanAdd(o)
            continue
        n = z.GetNetname()
        for lid in CU4:
            if not (z.IsOnLayer(lid) and z.HasFilledPolysForLayer(lid)) or n == 'GND':
                continue
            grow = 0.5 if PYRO.match(n) else 0.3 if lid in (F, B) else None
            if lid == IN2:
                in2_power.BooleanAdd(fill(z, lid))
            if grow is None:
                continue
            fp = fill(z, lid)
            fp.Inflate(MM(grow + r + MARGIN), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, ERR)
            forbid.BooleanAdd(fp)
    for net, ends in CORRIDORS.items():
        xs, ys = [], []
        for ref, pins in ends:
            for p in b.FindFootprintByReference(ref).Pads():
                if p.GetNumber() in pins:
                    xs.append(mm(p.GetPosition().x))
                    ys.append(mm(p.GetPosition().y))
        corridor = rect(min(xs) - 2, min(ys) - 2, max(xs) + 2, max(ys) + 2)
        for z in b.Zones():
            if not z.GetIsRuleArea() and z.GetNetname() == net and z.IsOnLayer(IN2) and z.HasFilledPolysForLayer(IN2):
                fp = fill(z, IN2)
                fp.Inflate(MM(0.5 + r), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, ERR)
                fp.BooleanIntersection(corridor)
                forbid.BooleanAdd(fp)
    guard = pcbnew.SHAPE_POLY_SET()
    for t in b.GetTracks():
        if t.GetClass() != 'PCB_VIA' and t.GetLayer() == B and t.GetNetname() != 'GND':
            t.TransformShapeToPolygon(guard, B, MM(0.3 + r + MARGIN), ERR, pcbnew.ERROR_OUTSIDE)
    in2_power.Inflate(MM(r + 0.3), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, ERR)
    guard.BooleanIntersection(in2_power)
    forbid.BooleanAdd(guard)
    for d in b.GetDrawings():
        if d.GetLayer() == pcbnew.Edge_Cuts and d.GetShape() == pcbnew.SHAPE_T_CIRCLE:
            circle(d.GetCenter(), mm(d.GetRadius()) + 0.52 + r, forbid)
    allow = pcbnew.SHAPE_POLY_SET()
    for z in b.Zones():
        if not z.GetIsRuleArea() and z.GetNetname() == 'GND':
            for lid in (F, B):
                if z.IsOnLayer(lid) and z.HasFilledPolysForLayer(lid):
                    allow.BooleanAdd(fill(z, lid))
    allow.BooleanIntersection(rect(EDGE, STRIP_Y + 0.05, 46 - EDGE, 118 - EDGE))
    for lid in (F, B):
        sl = sleeping[lid]
        sl.Inflate(MM(r), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, ERR)
        forbid.BooleanAdd(sl)
    allow.BooleanSubtract(forbid)
    return allow


class Spots:
    """The legal region less the spacing round every via placed so far."""

    def __init__(self, b, revive=False):
        self.region = legal(b, revive)
        self.placed = []

    def ok(self, q):
        return self.region.Contains(P(*q)) and all(math.dist(q, v) >= SPACING - 1e-9 for v in self.placed)

    def nearest(self, q, reach, inside=None):
        """The legal spot on the STEP grid round q nearest it within reach (ties: lower y, then lower x)."""
        n = int(round(reach / STEP))
        cand = sorted((math.hypot(i, j) * STEP, r4(q[1] + j * STEP), r4(q[0] + i * STEP))
                      for j in range(-n, n + 1) for i in range(-n, n + 1) if math.hypot(i, j) * STEP <= reach + 1e-9)
        for _, y, x in cand:
            if (inside is None or inside.Contains(P(x, y))) and self.ok((x, y)):
                return (x, y)
        return None

    def add(self, q):
        self.placed.append(q)


def gnd_points(b):
    pts = [(mm(t.GetPosition().x), mm(t.GetPosition().y)) for t in b.GetTracks()
           if t.GetClass() == 'PCB_VIA' and t.GetNetname() == 'GND']
    pts += [(mm(p.GetPosition().x), mm(p.GetPosition().y)) for f in b.GetFootprints() for p in f.Pads()
            if p.GetNetname() == 'GND' and p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH]
    return pts


class Near:
    """Nearest-point queries over a growing point set (bucket grid)."""

    def __init__(self, pts, cell=2.0):
        self.cell = cell
        self.bk = defaultdict(list)
        for p in pts:
            self.add(p)

    def add(self, p):
        self.bk[(int(p[0] // self.cell), int(p[1] // self.cell))].append(p)

    def dist(self, q, cap=60.0):
        ci, cj = int(q[0] // self.cell), int(q[1] // self.cell)
        best, ring = math.inf, 0
        while ring * self.cell <= cap + self.cell:
            for di in range(-ring, ring + 1):
                for dj in range(-ring, ring + 1):
                    if max(abs(di), abs(dj)) == ring:
                        for p in self.bk.get((ci + di, cj + dj), ()):
                            best = min(best, math.dist(p, q))
            if best <= ring * self.cell:
                return best
            ring += 1
        return best


def outer_gnd(b):
    """{layer: SHAPE_POLY_SET} of the F / B GND pour fills."""
    out = {}
    for lid in (F, B):
        ps = pcbnew.SHAPE_POLY_SET()
        for z in b.Zones():
            if not z.GetIsRuleArea() and z.GetNetname() == 'GND' and z.IsOnLayer(lid) and z.HasFilledPolysForLayer(lid):
                ps.BooleanAdd(fill(z, lid))
        out[lid] = ps
    return out


def islands(ps):
    out = []
    for i in range(ps.OutlineCount()):
        one = pcbnew.SHAPE_POLY_SET()
        one.AddOutline(ps.Outline(i))
        for j in range(ps.HoleCount(i)):
            one.AddHole(ps.Hole(i, j))
        out.append(one)
    return out


def in_island(one, q):
    return one.Collide(P(*q), MM(0.15))          # survey_metrics' P7 test


def power_layer_changes(b, rc):
    """Vias of power nets (route_check class 'power', GND excepted) whose net has tracks on two or more of the via's
    layers ending at it: route_check's power_via_no_gnd population."""
    out = []
    tracks = defaultdict(list)
    for t in b.GetTracks():
        if t.GetClass() != 'PCB_VIA':
            tracks[t.GetNetname()].append(t)
    for v in b.GetTracks():
        n = v.GetNetname()
        if v.GetClass() != 'PCB_VIA' or n == 'GND' or rc.net_class(n) != 'power':
            continue
        p = v.GetPosition()
        r = v.GetWidth(F) / 2
        layers = {t.GetLayer() for t in tracks[n]
                  if min(math.hypot(e.x - p.x, e.y - p.y) for e in (t.GetStart(), t.GetEnd())) <= r}
        if len(layers) >= 2:
            out.append((n, (r4(mm(p.x)), r4(mm(p.y)))))
    return sorted(out, key=lambda t: (t[1][1], t[1][0], t[0]))


def draw_vias(b, qs):
    gnd = b.FindNet('GND')
    for q in qs:
        v = pcbnew.PCB_VIA(b)
        v.SetPosition(P(*q))
        v.SetWidth(MM(VIA[0]))
        v.SetDrill(MM(VIA[1]))
        v.SetLayerPair(F, B)
        v.SetNet(gnd)
        b.Add(v)


def weak_islands(b):
    """[(layer name, island)] of the outer GND pour islands with fewer than two GND vias / plated GND holes (P7)."""
    have = gnd_points(b)
    pours = outer_gnd(b)
    out = []
    for lid, name in ((F, 'F'), (B, 'B')):
        for one in islands(pours[lid]):
            if sum(1 for q in have if in_island(one, q)) < 2:
                out.append((name, one))
    return out


def cover_points(b):
    pours = outer_gnd(b)
    pts = []
    yy = RASTER / 2
    while yy < 118:
        xx = RASTER / 2
        while xx < 46:
            if any(pours[lid].Contains(P(xx, yy)) for lid in (F, B)):
                pts.append((r4(xx), r4(yy)))
            xx += RASTER
        yy += RASTER
    return pts


def fills(b):
    """{(net, layer): fill area mm2} of every zone fill."""
    out = defaultdict(float)
    for z in b.Zones():
        if not z.GetIsRuleArea():
            for lid in CU4:
                if z.IsOnLayer(lid) and z.HasFilledPolysForLayer(lid):
                    out[(z.GetNetname(), lid)] += fill(z, lid).Area() / 1e12
    return out


def trim_targets(b):
    """{layer: GND fill area mm2 inside the trim outlines} before they are drawn; each outline must reach GND fill."""
    out = defaultdict(float)
    pours = outer_gnd(b)
    for name, layer, pts, _ in TRIMS:
        lid = F if layer == 'F' else B
        o = pcbnew.SHAPE_POLY_SET()
        o.NewOutline()
        for x, y in pts:
            o.Append(MM(x), MM(y))
        o.BooleanIntersection(pours[lid])
        assert o.Area() > 0, f'{name}: no GND fill inside its outline'
        out[lid] += o.Area() / 1e12
    return out


def check_trims(before, after, gone):
    """The trims took the GND fill inside their outlines (plus at most LEFTOVER of GND crumbs a trim left without a
    connection, which the fill's island removal drops) and changed no other fill of any net on any layer."""
    for key in set(before) | set(after):
        net, lid = key
        d = before.get(key, 0.0) - after.get(key, 0.0)
        if net == 'GND' and lid in (F, B):
            assert gone.get(lid, 0.0) - 0.05 < d < gone.get(lid, 0.0) + LEFTOVER, \
                f'GND fill on layer {lid} changed by {d:.3f} mm2, inside the trims {gone.get(lid, 0.0):.3f}'
        else:
            assert abs(d) < 0.01, f'{net} fill on layer {lid} changed by {d:.3f} mm2'


def draw_trims(b):
    for name, layer, pts, _ in TRIMS:
        z = pcbnew.ZONE(b)
        z.SetIsRuleArea(True)
        z.SetLayer(F if layer == 'F' else B)
        z.SetZoneName(name)
        z.SetDoNotAllowZoneFills(True)
        z.SetDoNotAllowTracks(False)
        z.SetDoNotAllowVias(False)
        z.SetDoNotAllowPads(False)
        z.SetDoNotAllowFootprints(False)
        ol = z.Outline()
        ol.NewOutline()
        for x, y in pts:
            ol.Append(MM(x), MM(y))
        b.Add(z)


def generate(b, rc, log=print):
    rows = []

    def via_row(q, basis):
        rows.append(('via', 'GND', 'FB', f'{VIA[0]}/{VIA[1]}', q[0], q[1], '', '', basis, ''))

    # 1. the reserved rows (spikes (a) and (d)), drawn first: the rest is placed round them
    fixed = [(x, FENCE_Y) for x in FENCE_X] + list(STRIP_STITCH) + [C24_STUB[1]]
    for x in FENCE_X:
        via_row((x, FENCE_Y), 'fence')
    for q in STRIP_STITCH:
        via_row(q, 'stitch')
    rows.append(('track', 'GND', 'B', '0.2', C24_STUB[0][0], C24_STUB[0][1], C24_STUB[1][0], C24_STUB[1][1], 'c24', ''))
    via_row(C24_STUB[1], 'c24')
    for name, layer, pts, why in TRIMS:
        outline = ' '.join(f'{x:g},{y:g}' for x, y in pts)
        rows.append(('trim', 'GND', layer, '', '', '', '', '', f'trim {name}', outline))
    before = fills(b)
    gone = trim_targets(b)
    draw_trims(b)
    refill(b)
    check_trims(before, fills(b), gone)
    draw_vias(b, fixed)
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(P(*C24_STUB[0]))
    t.SetEnd(P(*C24_STUB[1]))
    t.SetWidth(MM(0.2))
    t.SetLayer(B)
    t.SetNet(b.FindNet('GND'))
    b.Add(t)
    refill(b)
    # 2. returns, grid and cover on the legal region of that board
    sp = Spots(b)
    near = Near(gnd_points(b))
    new = []

    def put(q, basis):
        sp.add(q)
        near.add(q)
        new.append(q)
        via_row(q, basis)

    for net, q in power_layer_changes(b, rc):
        if near.dist(q) <= RETURN_REACH:
            continue
        s = sp.nearest(q, RETURN_REACH)
        if s:
            put(s, f'return {net}')
        else:
            log(f'  return: no legal spot within {RETURN_REACH} mm of the {net} layer change {q}')
    y = GRID_Y0
    while y < 118 - EDGE:
        x = GRID_X0
        while x < 46 - EDGE:
            node = (r4(x), r4(y))
            if near.dist(node) > SERVED:
                s = sp.nearest(node, SNAP)
                if s:
                    put(s, 'grid')
            x += PITCH
        y += PITCH
    pts = cover_points(b)
    cand = []
    yy = STRIP_Y + 0.125
    while yy < 118:
        xx = 0.125
        while xx < 46:
            if sp.region.Contains(P(xx, yy)):
                cand.append((r4(xx), r4(yy)))
            xx += 0.25
        yy += 0.25
    while True:
        bad = [q for q in pts if near.dist(q, COVER + 1) > COVER]
        if not bad:
            break
        bk = defaultdict(list)
        for q in bad:
            bk[(int(q[0] // COVER), int(q[1] // COVER))].append(q)
        best = None
        for c in cand:
            if not sp.ok(c):
                continue
            ci, cj = int(c[0] // COVER), int(c[1] // COVER)
            gain = sum(1 for di in (-1, 0, 1) for dj in (-1, 0, 1) for q in bk.get((ci + di, cj + dj), ())
                       if math.dist(q, c) <= COVER)
            if best is None or gain > best[0]:
                best = (gain, c)
        if best is None or best[0] < MIN_GAIN:
            break
        put(best[1], 'cover')
    draw_vias(b, new)
    refill(b)
    # 3. islands: every outer GND island gets two GND vias / plated GND holes where a legal spot exists
    for _ in range(4):
        weak = weak_islands(b)
        if not weak:
            break
        sp = Spots(b, revive=True)
        new = []
        for name, one in weak:
            inside = [q for q in gnd_points(b) if in_island(one, q)]
            while len(inside) < 2:
                bb = one.BBox()
                best = None
                yy = mm(bb.GetTop()) + STEP / 2
                while yy < mm(bb.GetBottom()):
                    xx = mm(bb.GetLeft()) + STEP / 2
                    while xx < mm(bb.GetRight()):
                        q = (r4(xx), r4(yy))
                        if one.Contains(P(*q)) and sp.ok(q):
                            d = min((math.dist(q, v) for v in inside), default=0.0)
                            if best is None or d > best[0] + 1e-9:
                                best = (d, q)
                        xx += STEP
                    yy += STEP
                if best is None:
                    break
                sp.add(best[1])
                new.append(best[1])
                inside.append(best[1])
                via_row(best[1], f'island {name}')
        if not new:
            break
        draw_vias(b, new)
        refill(b)
    for name, one in weak_islands(b):
        bb = one.BBox()
        log(f'  island {name}.Cu ({mm(bb.GetLeft()):.2f}, {mm(bb.GetTop()):.2f})-({mm(bb.GetRight()):.2f}, '
            f'{mm(bb.GetBottom()):.2f}), {one.Area() / 1e12:.2f} mm2: fewer than two GND vias, no legal spot')
    # 4. pads: every IC GND pad within PAD_REACH of copper of a GND via where a legal spot allows (D102)
    new = pad_returns(b, rc, Spots(b), via_row, log)
    if new:
        draw_vias(b, new)
        refill(b)
    return rows


def ic_gnd_pads(b):
    """[(name, pad, layer)] of the GND SMD pads of the ICs (U parts with >= 4 pads) forward of the strip, sorted."""
    out = []
    for f in b.GetFootprints():
        ref = f.GetReference()
        if not re.match(r'^U\d+$', ref) or len(f.Pads()) < 4:
            continue
        for p in f.Pads():
            if p.GetNetname() != 'GND' or p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
                continue
            if mm(p.GetPosition().y) < STRIP_Y:
                continue
            out.append((f'{ref}.{p.GetNumber()}', p, F if p.IsOnLayer(F) else B))
    return sorted(out, key=lambda t: (t[0].split('.')[0], t[0]))


def pad_reach(b, rc, pad, lid, extra=(), limit=PAD_REACH):
    """(copper distance mm from the pad to the nearest GND via / plated GND hole or None beyond limit, the raster, the
    distance array) over the layer's GND copper (route_check.reach); extra = new via centres not yet drawn."""
    c = pad.GetPosition()
    w = limit + 1.5
    win = (mm(c.x) - w, mm(c.y) - w, mm(c.x) + w, mm(c.y) + w)
    r = rc.Raster(tuple(v / rc.NM for v in win), PAD_RASTER / rc.NM)
    cop, stitch = rc.net_copper(b, 'GND', lid)
    for q in extra:
        ps = pcbnew.SHAPE_POLY_SET()
        circle(P(*q), VIA[0] / 2, ps)
        cop.append(ps)
        stitch.append(ps)
    copper = r.fill(cop)
    src = pcbnew.SHAPE_POLY_SET()
    pad.TransformShapeToPolygon(src, lid, 0, ERR, pcbnew.ERROR_INSIDE)
    d = rc.reach(r, copper, r.fill([src]), limit + 1.0)
    st = r.fill(stitch)
    best = min((d[k] for k in range(r.nx * r.ny) if st[k] and d[k] >= 0), default=None)
    return best, r, d


def pad_returns(b, rc, sp, via_row, log=print):
    """The pad stage (module docstring): a via per IC GND pad beyond PAD_REACH, at the legal spot nearest it through
    its copper; returns the new via centres (drawn by the caller)."""
    new = []
    for name, pad, lid in ic_gnd_pads(b):
        d0, r, d = pad_reach(b, rc, pad, lid, new)
        if d0 is not None and d0 <= PAD_REACH:
            continue
        c = (mm(pad.GetPosition().x), mm(pad.GetPosition().y))
        n = int(round(PAD_REACH / STEP))
        best = None
        for j in range(-n, n + 1):
            for i in range(-n, n + 1):
                q = (r4(c[0] + i * STEP), r4(c[1] + j * STEP))
                if math.dist(q, c) > PAD_REACH + 1e-9 or not sp.ok(q):
                    continue
                ci = int((q[0] / rc.NM - r.x0) // r.step)
                cj = int((q[1] / rc.NM - r.y0) // r.step)
                if not (0 <= ci < r.nx and 0 <= cj < r.ny):
                    continue
                dq = d[cj * r.nx + ci]
                if dq < 0 or dq > PAD_REACH:
                    continue
                key = (round(dq, 6), q[1], q[0])
                if best is None or key < best[0]:
                    best = (key, q)
        if best is None:
            log(f'  pad: {name} ({c[0]:.2f}, {c[1]:.2f}) reaches a GND via beyond {PAD_REACH} mm of copper; no legal '
                f'spot within {PAD_REACH} mm of its copper')
            continue
        q = best[1]
        sp.add(q)
        new.append(q)
        via_row(q, f'pad {name}')
        log(f'  pad: {name} beyond {PAD_REACH} mm of copper -> via {q} ({best[0][0]:.2f} mm of copper)')
    return new


HEADER = ('# R8 GND stitching copper (m3_design/assembly_review/sources/r8_design/step7/make_ground.py; R8_DECISIONS '
          'D62 on): drawn by m3_design/r8_ground.py in this order. item via: layer FB, size diameter/drill; '
          'item track: '
          'size = width; item trim: a fill keep-out rule area on layer, outline points x,y. basis: fence (D16), stitch '
          '(spike d), c24 (spike a), trim NAME, return NET, grid, island F|B, cover, pad REF.PIN (D102)\n')
COLS = ('item', 'net', 'layer', 'size', 'x0', 'y0', 'x1', 'y1', 'basis', 'points')


def write(rows, out):
    with open(out, 'w', newline='') as fh:
        fh.write(HEADER)
        w = csv.writer(fh, delimiter='\t', lineterminator='\n')
        w.writerow(COLS)
        for row in rows:
            w.writerow([f'{v:g}' if isinstance(v, float) else v for v in row])


def read(path=TABLE):
    with open(path) as fh:
        return list(csv.DictReader((line for line in fh if not line.startswith('#')), delimiter='\t'))


def strip_built(b, rows):
    """Remove the table's items from a built board (and refill): the step-6 board back."""
    want_v = {(float(r['x0']), float(r['y0'])) for r in rows if r['item'] == 'via'}
    want_t = {(float(r['x0']), float(r['y0']), float(r['x1']), float(r['y1'])) for r in rows if r['item'] == 'track'}
    gone = 0
    for t in list(b.GetTracks()):
        if t.GetNetname() != 'GND':
            continue
        if t.GetClass() == 'PCB_VIA':
            key = (r4(mm(t.GetPosition().x)), r4(mm(t.GetPosition().y)))
            if key in want_v:
                b.Delete(t)
                gone += 1
        else:
            key = (r4(mm(t.GetStart().x)), r4(mm(t.GetStart().y)), r4(mm(t.GetEnd().x)), r4(mm(t.GetEnd().y)))
            if key in want_t:
                b.Delete(t)
                gone += 1
    assert gone == len(want_v) + len(want_t), f'built board lacks {len(want_v) + len(want_t) - gone} table items'
    names = {r['basis'].split()[1] for r in rows if r['item'] == 'trim'}
    zones = [z for z in b.Zones() if z.GetIsRuleArea() and z.GetZoneName() in names]
    assert len(zones) == len(names), 'built board lacks a trim of the table'
    for z in zones:
        b.Delete(z)
    for z in b.Zones():
        if not z.GetIsRuleArea():
            z.UnFill()
    b.BuildConnectivity()
    assert pcbnew.ZONE_FILLER(b).Fill(b.Zones()), 'native zone fill failed'
    b.BuildConnectivity()


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('board', type=Path)
    ap.add_argument('out', type=Path)
    ap.add_argument('--built', action='store_true')
    a = ap.parse_args()
    sys.path.insert(0, str(ROOT / 'tools'))
    import route_check as rc  # noqa: E402
    sys.path.insert(0, str(ROOT / 'm3_design'))
    import r8_ground  # noqa: E402
    b = pcbnew.LoadBoard(str(a.board.resolve()))
    r8_ground.relieve(b, strict=False)         # D101: the board r8_ground.py fills has J123.2 relieved
    if a.built:
        strip_built(b, read())                 # (refills)
    else:
        refill(b)                              # the relief's fill, as r8_ground.py fills it
    rows = generate(b, rc)
    write(rows, a.out)
    count = defaultdict(int)
    for row in rows:
        count[row[8].split()[0]] += 1
    print(f'make_ground: {len(rows)} rows', dict(count))


if __name__ == '__main__':
    main()
