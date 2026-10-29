#!/usr/bin/env python3
"""Build the R8 board's power copper (M3-ASSY-R8, build step 5) on the placed board r8_pcb.py made.

usage: <KiCad python3> -I m3_design/r8_power.py [--board m3_design/assembly_review/m3.kicad_pcb] [--no-fill]

The board must be r8_pcb.py's output: parts placed, the rigid R7 copper only, no In2 zone (checked). It is rebuilt in
place, so the project's m3.kicad_pro and m3.kicad_dru apply while it is filled. Design basis: r8_plan.md section 3
step 5, R8_DECISIONS (D12, D18-D20, D29-D39 and the step-5 block D40-D50), spike (c)
(m3_design/r8_spikes/c_battery), the makers' layout guides (Diodes DS41326 Figure 25, DS42002 Figure 39; TI SLVSEA3F
12.1, SLVSFC9C 8.4.1). Every number is board mm (y forward).

1. In2 (D47): the GND plane (the board less the other regions), the 3V3 region under the MCU zone (with the pyro
   corridor's GND notch, the Y1 keep-out of R5 V1, GND east of x 35.3 under both bucks), the RAW_ACT islands and the
   BAT_IN band of spike (c), each power island >= 2.5 mm in plan view from PYRO1_BUS / IGN / OUT copper (D18).
2. The 7.7 A copper of spike (c) ("west chain"): BAT_IN, ACT_FET_S and RAW_ACT pours on the outer layers and In2, the
   via fields, the actuator-switch gate network, the switch legs, the input damper and the BAT_IN feed to the eFuse.
3. RAW_PROTECTED (D46): the eFuse output column under U9, the F.Cu trunk down the east edge to the logic mux U11 and
   the camera eFuse U7, and the gate-drive feed R122.
4. Logic supplies (D40, D42, D44): USB_LIMITED from U10 to U11, VLOGIC to the 3V3 buck U2 and the hold-up C84, the
   buck's switching loop, the 3V3 output to In2 and the F.Cu 3V3 spine to D121 / D120 / R89, the 3V3A filter to the
   VDDA pins and a trunk end for the sensors, U1's decoupling and VCAP (spike (a)) and the supply parts' 3V3 taps.
5. Camera supplies (D41): CAM_INPUT_LIMITED from U7 to the camera buck U8, its loop and feedback, CAM_5V to J9.1
   with its remote sense, TP72, R78, C75 and C76.
6. The GND vias of every power part, native fill, the vias' nets asserted (a via on foreign copper is re-netted by
   connectivity, spike (c)'s pitfall), save, the 12 rigid digests asserted.
Left to step 6 (D48): VBUS at J3 / D4 / U10, the sensors' 3V3A past the trunk end (15.0, 62.2), the U13 translator
cluster (CAM_5V to U13 / C91 / R104, CAM_IO_3V3), the other 3V3 pull-ups and bypasses (taps over In2 3V3), the eFuse /
mux control pins; GND stitching is step 7's.
Deterministic (fixed KIID seed): a rebuild reproduces the board byte for byte.
"""
import argparse
import sys
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import check_r8  # noqa: E402

PROJECT = ROOT / 'm3_design/assembly_review'
MM, mm = pcbnew.FromMM, pcbnew.ToMM
F, In1, In2, B = pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu
LAYER = {'F': F, 'B': B, 'In2': In2}
KIID_SEED = 8805
VIA = (0.6, 0.3)                     # the board's via (m3.kicad_pro Default)
CONN = {'full': pcbnew.ZONE_CONNECTION_FULL, 'thermal': pcbnew.ZONE_CONNECTION_THERMAL,
        'tht': pcbnew.ZONE_CONNECTION_THT_THERMAL}


def P(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


# ======================================================================================================================
# 1. In2 regions
# ======================================================================================================================
# 3V3 under the MCU zone: from the strip (y 24.0; the strip's In2 stays GND to y 23.75, check_r7 rf_strip) to y 70.0
# (0.8 mm clear of the servo rows' B.Cu at y 71.79, spike (b)), west tongue to y 81.0 under the buzzer and pull-pin
# parts (to y 81.3, beside the RAW_ACT island from y 81.6); the pyro corridor notch (x 17.25-20.35 from y 53.6,
# CONT's jog y 56.7-58.3 to x 24.6 and its leg to R168) is GND under every B.Cu pyro
# lane from U1's field to the block (r8_plan section 1); east of x 35.3 the In2 is GND under both buck stages (DS42002
# Layout 6: GND on the inner layers) and joins the strip to the band.
IN2_3V3 = [(0.3, 24.0), (35.3, 24.0), (35.3, 70.0), (20.35, 70.0), (20.35, 58.3), (24.6, 58.3), (24.6, 53.6),
           (22.37, 53.6), (22.37, 56.7), (20.35, 56.7), (20.35, 53.6), (17.25, 53.6), (17.25, 81.3), (0.3, 81.3)]
# spike (c) section 3.3, its west island now from y 81.6 (the divider left the band, D32; 3V3 to y 81.3 beside it)
IN2_RAW_ACT_WEST = [(0.5, 81.6), (16.4, 81.6), (16.4, 91.6), (6.0, 91.6), (6.0, 100.3), (11.0, 100.3), (11.0, 108.0),
                    (0.5, 108.0)]
# spike (c)'s J122 finger, its forward edge at y 86.2: >= 0.5 mm (rule A) in plan view from C127's pads (CH1 block)
IN2_RAW_ACT_J122 = [(20.2, 70.5), (24.6, 70.5), (24.6, 86.2), (20.2, 86.2)]
# Fix pass 2 (R8P2-POWER-02, D97): the BAT_IN island ends where the outer BAT_IN pours do (x 33.5, y 112.6). Its old
# east and forward parts (x 33.5-45.5, y 112.6-117.5, about 220 mm2) carried no current (every BAT_IN via lies at
# x <= 26.2 and J1.1 is the only BAT_IN hole), yet put unfused battery copper 0.5 mm from the east and forward edges,
# 0.2 mm above B.Cu GND, under the right forward panel tab and round the M3 hole (42, 114.4); In2 GND takes it back.
# J1.1's In2 annulus stays whole (its pad edge 1.6 mm inside x 33.5, 0.9 mm inside y 112.6)
IN2_BAT_IN = [(12.4, 100.3), (33.5, 100.3), (33.5, 112.6), (12.4, 112.6)]
Y1_IN2_KEEPOUT = [(18.9, 46.3), (26.8, 46.3), (26.8, 50.95), (18.9, 50.95)]     # R5 V1, spike (a): no plane under Y1


# ======================================================================================================================
# 2. 7.7 A copper (spike (c) "west chain", m3_design/r8_spikes/c_battery/battery.py; step-4 moves applied)
# ======================================================================================================================
# Fix pass 1 (R8_DECISIONS D85): ACT_FET_S is battery-live through Q120's body diode whatever the switch does, so its
# B.Cu pour keeps rule E's 1.0 mm (not rule F's 0.5 mm) from J124.1's bare ring (PYRO1_BUS): the corner at (11.4, 97.6)
# is chamfered to (12.4, 97.6) (R8P1-PYRO-01); RAW_ACT's F.Cu pour is chamfered at (21.3, 88.0) to stay >= 1.0 mm
# from bare R127.1 (PYRO1_GATE_N, the one bridge that fires an armed channel) (R8P1-PYRO-02 (a)); neither moves a
# 7.7 A neck
BAND_ZONES = [   # name, net, layer, priority, outline
    ('R8_ACT_FET_S_B', 'ACT_FET_S', 'B', 40, [(9.6, 98.6), (11.4, 98.6), (12.4, 97.6), (14.78, 97.6), (14.78, 106.9),
                                               (11.9, 106.9), (11.9, 105.8), (9.6, 105.8)]),
    # west region (no divider notch: the divider sits at J122's aft end, D32)
    ('R8_RAW_ACT_B_west', 'RAW_ACT', 'B', 36, [(0.5, 81.8), (16.5, 81.8), (16.5, 93.2), (7.4, 93.2), (7.4, 97.7),
                                               (9.6, 99.9), (9.6, 108.0), (0.5, 108.0)]),
    ('R8_RAW_ACT_B_box', 'RAW_ACT', 'B', 36, [(21.3, 70.9), (24.7, 70.9), (24.7, 80.35), (25.1, 80.35), (25.1, 86.9),
                                              (19.65, 86.9), (19.65, 80.35), (21.3, 80.35)]),
    ('R8_BAT_IN_B', 'BAT_IN', 'B', 34, [(15.0, 98.6), (31.0, 98.6), (31.0, 101.9), (41.3, 101.9), (41.3, 105.6),
                                        (35.2, 105.6), (35.2, 108.2), (33.4, 108.2), (33.4, 112.6), (27.8, 112.6),
                                        (27.8, 108.6), (17.0, 108.6), (17.0, 104.6), (15.0, 104.6)]),
    ('R8_RAW_ACT_F', 'RAW_ACT', 'F', 36, [(0.5, 79.6), (6.6, 79.6), (6.6, 84.8), (10.8, 84.8), (10.8, 79.6),
                                          (19.6, 79.6), (19.6, 80.35), (21.3, 80.35), (21.3, 70.9), (24.7, 70.9),
                                          (24.7, 80.35), (25.1, 80.35), (25.1, 86.3), (21.3, 86.3), (21.3, 87.3),
                                          (20.6, 88.0), (15.8, 88.0), (15.8, 93.1), (7.4, 93.1), (7.4, 97.7), (9.6, 99.9),
                                          (12.8, 99.9), (12.8, 108.0), (7.4, 108.0), (7.4, 109.5), (0.5, 109.5)]),
    ('R8_BAT_IN_F', 'BAT_IN', 'F', 34, [(17.0, 104.9), (22.5, 104.9), (22.5, 103.0), (27.3, 103.0), (27.3, 104.9),
                                        (33.5, 104.9), (33.5, 112.6), (27.8, 112.6), (27.8, 108.6), (17.0, 108.6)]),
]


def grid(x0, x1, y0, y1, pitch):
    """Via field points on a pitch (>= 0.9 mm, plan A's via-column rule), inclusive ends."""
    nx, ny = int(round((x1 - x0) / pitch)), int(round((y1 - y0) / pitch))
    return [(round(x0 + i * pitch, 3), round(y0 + j * pitch, 3)) for i in range(nx + 1) for j in range(ny + 1)]


RAW_ACT_VIAS = (grid(1.3, 5.5, 92.8, 99.8, 1.4) + grid(1.3, 2.7, 101.2, 106.8, 1.4) + grid(4.1, 8.3, 106.8, 106.8, 1.4)
                + [(1.3, 85.6), (3.3, 85.6), (5.3, 85.6), (11.3, 85.6)]
                + [(x, 87.6) for x in (5.3, 7.3, 9.3, 11.3)]
                + [(x, 89.6) for x in (1.3, 3.3, 5.3, 7.3, 12.7, 14.7)]
                + [(x, 91.0) for x in (12.7, 14.7)]
                + grid(20.6, 23.4, 81.4, 85.6, 1.4))
BAT_IN_VIAS = (grid(17.7, 19.1, 105.6, 107.0, 1.4) + grid(22.0, 26.2, 105.6, 107.0, 1.4)
               + grid(21.25, 21.25, 100.9, 103.7, 1.4))
BAND_GND_VIAS = [(19.6, 104.4), (37.35, 100.6), (42.0, 100.6), (37.4, 107.6), (44.6, 104.2)]   # spike (c), D31

ACT_GATE_Y = 107.16          # the gate bus, on C120.2 and R120.2 (C120 placed with its gate pad on R120's, D43)
GATE_X = 13.48               # Q120's source / gate column: the F.Cu hop
BAND_TRACKS = [   # net, layer, width, polyline
    # ACT_GATE: B.Cu bus (Q121.4 stub, C120.2, R120.2), via A, F.Cu hop at x 13.48 (R121.1, TP121), via B, Q120.4: the
    # gates sit at opposite corners of the facing-row bridge and In2 carries power only (spike (c) decision 3, D20)
    # Q121.4's stub chamfered into the bus (fix pass 1, D91: the square corner at (10.9, 107.16) was a 1.32 x chain
    # detour with a DRC-clean redraw)
    ('ACT_GATE', 'B', 0.25, [(10.9, 104.9), (10.9, 105.56), (12.5, ACT_GATE_Y), (GATE_X, ACT_GATE_Y)]),
    ('ACT_GATE', 'B', 0.25, [(GATE_X, ACT_GATE_Y), (14.3, ACT_GATE_Y)]),
    ('ACT_GATE', 'B', 0.25, [(GATE_X, 99.82), (GATE_X, 98.95)]),
    ('ACT_GATE', 'F', 0.25, [(GATE_X, 98.95), (GATE_X, 100.85)]),
    ('ACT_GATE', 'F', 0.25, [(GATE_X, 100.85), (GATE_X, 103.2)]),
    ('ACT_GATE', 'F', 0.25, [(GATE_X, 103.2), (GATE_X, ACT_GATE_Y)]),
    # gate drive on F: ACT_DRV Q122.3 -> R121.2; ACT_EN Q122.1 -> R122.2 -> R123.1
    ('ACT_DRV', 'F', 0.25, [(14.34, 100.85), (15.6, 100.85)]),
    # D69: R122 / R123 sit east of Q122's pin-1 mark (its silk dot lay on R122.2): one 45 deg out of Q122.1, then
    # down R122's axis
    ('ACT_EN', 'F', 0.25, [(17.6, 101.8), (18.2, 102.4), (18.2, 102.93)]),
    ('ACT_EN', 'F', 0.25, [(18.2, 102.93), (19.15, 102.93)]),
    # damper: BAT_DAMP C89.2 -> C95.2 -> R166.1 on y 100.675 (F)
    ('BAT_DAMP', 'F', 0.5, [(24.0, 100.675), (26.5, 100.675)]),
    ('BAT_DAMP', 'F', 0.5, [(26.5, 100.675), (27.875, 100.675), (28.9, 101.7)]),
    # switch legs at J1.3 / J1.4 (R80 / R165 at y 106.1, D30)
    ('BAT_SW_SOURCE', 'B', 0.25, [(20.46, 106.92), (20.46, 110.4)]),
    ('BAT_SW_RETURN', 'B', 0.25, [(16.6, 106.92), (16.6, 109.18), (15.38, 110.4)]),
    # BAT_IN feed to the eFuse (D36): x 41.25 through R82.1 and C88.1 into U9.5's north end; TP80 on a stub
    ('BAT_IN', 'B', 0.5, [(41.25, 102.4), (41.25, 94.6), (41.25, 88.9), (41.25, 87.6)]),
    ('BAT_IN', 'B', 0.3, [(41.25, 87.6), (41.25, 85.5)]),          # into U9.5's centre (fix pass 1, R8P1-ROUTING-02)
    ('BAT_IN', 'B', 0.3, [(41.25, 94.6), (43.4, 94.6)]),
    # RAW_ACT tap to the RAW_ACT_SENSE divider's top, J122.11 -> R177.1 (D32)
    ('RAW_ACT', 'B', 0.25, [(23.0, 71.89), (25.92, 68.97)]),
]


class Draw:
    def __init__(self, board):
        self.b = board
        self.vias = {}

    def net(self, name):
        n = self.b.FindNet(name)
        assert n is not None, name
        return n

    def zone(self, name, net, layer, pts, prio, clr=0.3, minw=0.3, conn='full'):
        z = pcbnew.ZONE(self.b)
        z.SetLayer(LAYER[layer])
        z.SetNet(self.net(net))
        z.SetZoneName(name)
        z.SetAssignedPriority(prio)
        z.SetLocalClearance(MM(clr))
        z.SetMinThickness(MM(minw))
        z.SetPadConnection(CONN[conn])
        z.SetThermalReliefGap(MM(0.25))
        z.SetThermalReliefSpokeWidth(MM(0.4))
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        ol = z.Outline()
        ol.NewOutline()
        for x, y in pts:
            ol.Append(MM(x), MM(y))
        assert not ol.IsSelfIntersecting(), name
        self.b.Add(z)
        return z

    def keepout(self, name, layer, pts):
        z = pcbnew.ZONE(self.b)
        z.SetIsRuleArea(True)
        z.SetLayer(LAYER[layer])
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
        self.b.Add(z)

    def track(self, net, layer, width, pts):
        n = self.net(net)
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            assert (x0, y0) != (x1, y1), (net, pts)
            t = pcbnew.PCB_TRACK(self.b)
            t.SetStart(P(x0, y0))
            t.SetEnd(P(x1, y1))
            t.SetWidth(MM(width))
            t.SetLayer(LAYER[layer])
            t.SetNet(n)
            self.b.Add(t)

    def via(self, net, x, y, size=VIA):
        key = (round(x, 4), round(y, 4))
        assert key not in self.vias, f'two vias at {key}'
        v = pcbnew.PCB_VIA(self.b)
        v.SetPosition(P(x, y))
        v.SetWidth(MM(size[0]))
        v.SetDrill(MM(size[1]))
        v.SetNet(self.net(net))
        self.b.Add(v)
        self.vias[key] = net


def poly(pts):
    s = pcbnew.SHAPE_POLY_SET()
    s.NewOutline()
    for x, y in pts:
        s.Append(MM(x), MM(y))
    return s


def in2(d):
    # the GND plane's outline is the board less the other regions, so it leaves no GND ring round a GND via or pin
    # inside them (In1 is the solid GND reference of every such via)
    z = d.zone('R8_GND_In2', 'GND', 'In2', [(0.3, 0.3), (45.7, 0.3), (45.7, 117.7), (0.3, 117.7)], 1, clr=0.25,
               minw=0.2, conn='tht')
    for pts in (IN2_3V3, IN2_RAW_ACT_WEST, IN2_RAW_ACT_J122, IN2_BAT_IN):
        z.Outline().BooleanSubtract(poly(pts))           # in place: the zone keeps its own outline object
    assert z.Outline().OutlineCount() == 1, z.Outline().OutlineCount()
    d.zone('R8_3V3_In2', '3V3', 'In2', IN2_3V3, 10, clr=0.25, minw=0.2, conn='thermal')
    d.zone('R8_RAW_ACT_In2_west', 'RAW_ACT', 'In2', IN2_RAW_ACT_WEST, 12)
    d.zone('R8_RAW_ACT_In2_j122', 'RAW_ACT', 'In2', IN2_RAW_ACT_J122, 12)
    d.zone('R8_BAT_IN_In2', 'BAT_IN', 'In2', IN2_BAT_IN, 12)
    d.keepout('Y1_In2_keepout', 'In2', Y1_IN2_KEEPOUT)
    # no GND sliver beside L1.2
    d.keepout('R8_POUR_TRIM_L1', 'B', [(45.0, 64.0), (45.7, 64.0), (45.7, 69.2), (45.0, 69.2)])


def band(d):
    for name, net, layer, prio, pts in BAND_ZONES:
        d.zone(name, net, layer, pts, prio)
    for net, layer, w, pts in BAND_TRACKS:
        d.track(net, layer, w, pts)
    d.via('ACT_GATE', GATE_X, ACT_GATE_Y)
    d.via('ACT_GATE', GATE_X, 98.95)
    for x, y in RAW_ACT_VIAS:
        d.via('RAW_ACT', x, y)
    for x, y in BAT_IN_VIAS:
        d.via('BAT_IN', x, y)
    for x, y in BAND_GND_VIAS:
        d.via('GND', x, y)


# ======================================================================================================================
# 3. RAW_PROTECTED (the eFuse U9's output)
# ======================================================================================================================
TRUNK_X = 45.2               # F.Cu down the east edge (0.5 mm: 45.45 <= 45.5, the copper-to-edge clearance)
V_U9 = (41.75, 83.7)         # U9.6's via to the trunk (D36)
V_IN1 = (35.25, 60.5)        # the logic mux U11's IN1 via, north of U11.2 (D42); 0.5 mm ring (SMALL_VIA, fix pass 2)
V_U7 = (42.15, 25.6)         # the trunk's drop to the camera eFuse U7 (D37), aft of C73
RAW_PROTECTED_TRACKS = [
    ('F', 0.5, [(TRUNK_X, 83.7), (TRUNK_X, 62.6), (TRUNK_X, 51.5), (43.5, 49.8), (42.15, 49.8), (42.15, 25.6)]),
    ('F', 0.5, [V_U9, (42.475, 83.7), (TRUNK_X, 83.7)]),        # R92.1 (top) taps it at x 42.475
    # R122 (gate drive), spike (c)'s lane: east past R123 (ACT_EN) and the BAT_IN via field, then aft at y 99.75
    ('F', 0.25, [(18.2, 103.79), (20.3, 103.79), (20.3, 99.75), (TRUNK_X, 99.75), (TRUNK_X, 83.7)]),
    ('F', 0.3, [(42.475, 82.6), (42.475, 83.7)]),               # R92 (10k bleed, top)
    ('F', 0.4, [(TRUNK_X, 62.6), (35.25, 62.6), V_IN1]),       # under C84's body, between its pads
    ('B', 0.3, [(41.75, 85.5), V_U9]),                          # out of U9.6 (0.3 mm pad, 0.5 mm pitch)
    ('B', 0.5, [V_U9, (41.75, 80.0), (41.75, 78.2), (41.75, 75.75), (40.5, 74.5)]),   # TP81
    ('B', 0.5, [(41.75, 80.0), (43.51, 80.0)]),                 # D9.1 (the clamp)
    ('B', 0.5, [(41.75, 78.2), (40.95, 78.2)]),                 # C82.1
    ('B', 0.4, [V_IN1, (35.25, 59.275)]),                       # U11.2 (IN1)
    ('B', 0.3, [V_IN1, (35.25, 61.6)]),                         # C97.1 (IN1 capacitor)
    ('B', 0.5, [V_U7, (37.4, 25.6), (36.52, 25.6), (35.5, 26.62), (34.55, 26.62), (34.55, 29.75)]),   # TP70, C71, U7.4
    ('B', 0.25, [(34.55, 29.75), (34.05, 29.75)]),              # U7.3
]
# U9's output parts on a B.Cu column x 41.75 under U9.6 (via, D9, C82, TP81; R92 on the top); no pour: a pour would
# make route_check judge R122's branch round the block as one chain (1.33 x its octile distance) rather than the net


def raw_protected(d):
    for layer, w, pts in RAW_PROTECTED_TRACKS:
        d.track('RAW_PROTECTED', layer, w, pts)
    for xy in (V_U9, V_U7):
        d.via('RAW_PROTECTED', *xy)
    # fix pass 2 (R8P2-ROUTING-01, D98): the board's 0.5 / 0.3 mm via (same drill and barrel, so the same current
    # capacity) opens the 0.150 mm gap to the VLOGIC column x 35.95 (U11's pin pitch) to 0.20 mm
    d.via('RAW_PROTECTED', *V_IN1, SMALL_VIA)
    d.track('GND', 'B', 0.5, [(43.51, 76.0), (43.51, 74.2)])     # D9.2 (anode) to its GND via
    d.via('GND', 43.51, 74.2)


# ======================================================================================================================
# 4. Logic supplies
# ======================================================================================================================
# USB_LIMITED (U10 -> U11 IN2): B.Cu under U1's aft pad row (y 37.3), north on x 29.95, one 45-degree F.Cu hop over
# the RAW_ACT_SENSE lane (x 30.65), B.Cu east on y 55.3 into C98.1 and U11.7 (D42); the hop is no longer than the lane
# needs, so BAT_FAULT_N's reserved F.Cu lane (x 33.6, D50) crosses USB_LIMITED's B.Cu. 0.4 mm: the TPS2553 limit is
# 0.45 A. Fix pass 3 (R8P3-ROUTING-01, D106): the trunk sits on y 37.3, not 37.25, so CAM_PWR_EN's y 36.8 lane is
# 0.20 mm from it (was 0.150 mm); with R172 and the RAW_ACT_SENSE lane on x 30.65 the x 29.95 run is 0.23 mm from
# R172's pads (was 0.180 mm). Fix pass 4 (R8P4-ROUTING-02, D111): R87.1 (the OVLO divider top) lies straight below the
# y 55.3 trunk, so its 0.25 mm branch is one T drop at x 32.2 (it left C98.1's centre at 45 degrees to the trunk's
# diagonal and ran 2.55 mm back west under the trunk: an acute pair and a doubled run, 1.86 mm longer)
V_USB = ((29.95, 54.0), (31.25, 55.3))
USB_LIMITED_TRACKS = [
    ('B', 0.4, [(13.7, 36.35), (15.4, 36.35), (16.35, 37.3), (19.4, 37.3), (29.95, 37.3), V_USB[0]]),
    ('B', 0.4, [(15.4, 36.35), (15.4, 34.38)]),                 # C86.1
    ('B', 0.3, [(19.4, 37.3), (19.4, 31.6)]),                   # TP82
    ('F', 0.4, [V_USB[0], V_USB[1]]),                           # over the RAW_ACT_SENSE lane (B.Cu, x 30.65)
    ('B', 0.4, [V_USB[1], (32.2, 55.3), (34.35, 55.3), (35.25, 56.2), (35.25, 57.925)]),     # C98.1, U11.7
    ('B', 0.25, [(32.2, 55.3), (32.2, 57.775)]),                # R87.1 (OVLO divider top), a T off the trunk
]
# VLOGIC (U11 OUT): one column x 36.75 through C99.1, C6.1, U2.3 (VIN) and U2.2 (EN), C7 west, one via to the hold-up
# C84's top pad, on to TP83; the sense divider's via (26.95, 60.5) (D33) joins at C7.1. Fix pass 1 (D85): the C84 via
# sits at x 35.65, its ring clear of C7.1's pasted pad (B) by >= 0.03 mm and C84.1's (F) by 0.10 mm (R8P1-DFM-01; R7's
# ViaCheck rule, now gated by check_r8 via_paste); the sense via is a signal via (0.5 mm), 0.20 mm from SERVO1_MCU
V_VLOGIC = (35.65, 66.6)
VLOGIC_TRACKS = [
    ('B', 0.4, [(35.95, 57.925), (35.95, 59.275)]),             # U11.8 -> U11.1
    ('B', 0.5, [(35.95, 59.275), (35.95, 60.7), (36.75, 61.5), (36.75, 63.86), (36.75, 65.65),
                (36.75, 66.6)]),
    ('B', 0.4, [(36.75, 65.65), (34.75, 65.65)]),               # C7.1
    ('B', 0.4, [(36.75, 66.6), V_VLOGIC, (34.5, 67.75), (33.0, 67.75)]),      # C84 via, TP83
    ('F', 0.6, [V_VLOGIC, (36.4, 66.6)]),                       # into C84.1 (1.9 x 4.4 mm pad)
    ('F', 0.2, [(26.53, 55.3), (26.95, 55.3), (26.95, 60.5)]),  # R60.1 (VLOGIC sense divider, D33)
    # one 45-degree run to C7.1's row (fix pass 1, D91: the L round (30.4, 60.5) was a 1.30 x chain detour, +3.0 mm,
    # with a DRC-clean redraw, the M2 sweep's chain_detour / alt_audit)
    ('B', 0.2, [(26.95, 60.5), (32.1, 65.65), (34.75, 65.65)]),
]
# 3V3 buck U2 (DS41326 Figure 25, D40): SW strap into L1.1, C5 north of BST, Cout C8 / C9 on L1.2's column, the
# output north then west to the In2 3V3 via at (34.4, 69.65); FB (U2.1) senses that trace; R91 (pull-up) below C9
V_3V3_OUT = (34.4, 69.65)
BUCK3_TRACKS = [
    ('SW_NODE', 'B', 0.8, [(39.15, 66.6), (41.1, 66.6)]),
    ('SW_NODE', 'B', 0.4, [(39.99, 69.4), (41.1, 68.29)]),     # C5.1 -> L1.1
    ('BST', 'B', 0.3, [(39.15, 67.55), (39.15, 69.4)]),        # U2.6 -> C5.2
    ('3V3', 'B', 0.6, [(44.3, 59.625), (44.3, 61.33), (44.3, 63.32), (44.3, 66.6), (44.3, 68.7), (42.6, 70.4),
                       (35.15, 70.4), V_3V3_OUT]),                # R91.1 (pull-up), C9.1, C8.1, L1.2 -> In2
    ('3V3', 'B', 0.2, [(36.75, 67.55), (36.75, 70.4)]),        # FB
]
BUCK3_GND_VIAS = [(40.5, 63.3), (40.5, 61.8)]
# 3V3 beyond In2: an F.Cu spine from V_3V3_OUT north through D121.5's via (spike (b)), stepped east to x 35.2 past
# D121.2's GND via (34.4, 78.2) (spike (b), step 6), to one line on y 82.0 from D120.3 (the pyro block's cold pull-up,
# not block copper, D15) to R89.1's via (U9's fault pull-up); In2 there is GND
V_D121 = (34.4, 73.2)
V_R89 = (39.325, 82.0)
SPINE_TRACKS = [
    ('F', 0.3, [V_3V3_OUT, V_D121, (35.2, 74.0), (35.2, 82.0)]),
    ('F', 0.3, [(32.0, 82.0), (35.2, 82.0), V_R89]),            # D120.3, R89
    ('B', 0.3, [(34.4, 74.55), V_D121]),                        # D121.5
    ('B', 0.3, [(39.325, 83.6), V_R89]),                        # R89.1
]
# 3V3 taps into In2 of the supply-monitoring and supply parts (other pull-ups and bypasses: their step-6 families)
TAPS_3V3 = [   # pad, via
    ((22.375, 58.8), (22.375, 59.75)),     # R164.1 (3V3A filter)
    ((25.3, 57.73), (25.3, 58.6)),         # R62.1 (V3V3 sense divider)
    ((35.6, 53.68), (34.8, 53.68)),        # C90.1
]
# 3V3A (R164 -> C10 / C11 column x 24.025): into U1's VDDA pocket through the door between R62 and the RAW_ACT_SENSE
# lane (its chamfer moved north-east, D45) to C22.1 (spike (a)'s C21 / C22 / pins 20-21 copper), and an F.Cu hop over
# the pyro corridor to a trunk end west of it (15.0, 62.2) for the sensors (step 6, imu_i2c)
V_3V3A = ((20.9, 62.2), (15.0, 62.2))
TRACKS_3V3A = [
    ('B', 0.3, [(24.025, 58.8), (24.025, 59.6), (24.025, 61.0), (24.025, 62.2), (24.025, 63.4)]),
    ('B', 0.25, [(24.025, 59.6), (25.6, 59.6), (27.7, 57.5), (27.7, 55.18)]),
    ('B', 0.3, [(24.025, 62.2), V_3V3A[0]]),
    ('F', 0.3, [V_3V3A[0], V_3V3A[1]]),
]
# U1's own decoupling and VCAP (spike (a) spike_geom.copper(), the power items; C21 / C22's GND via as D31): every
# track 0.2 mm, every via 0.5 / 0.3 mm
DECOUPLING_TRACKS = [
    ('3V3', 'B', [(26.13, 45.1), (28.0, 45.1), (28.75, 45.1)]),     # U3.8 -> C29 -> via
    ('VCAP2', 'F', [(18.0, 37.45), (18.0, 39.3)]), ('VCAP2', 'B', [(18.0, 39.3), (19.1, 39.3)]),
    ('3V3', 'F', [(17.0, 37.45), (17.0, 38.75)]), ('3V3', 'B', [(17.0, 38.75), (17.0, 39.48)]),
    ('VCAP1', 'F', [(30.55, 40.0), (29.25, 40.0)]), ('VCAP1', 'B', [(29.25, 40.0), (28.35, 40.0)]),
    ('3V3', 'F', [(30.55, 39.0), (29.25, 39.0)]), ('3V3', 'B', [(29.25, 39.0), (28.87, 38.62), (28.52, 38.62)]),
    ('3V3', 'F', [(30.55, 50.5), (29.2, 50.5)]), ('3V3', 'B', [(29.2, 50.5), (29.2, 49.82)]),
    ('3V3', 'F', [(19.5, 52.55), (19.5, 51.15)]), ('3V3', 'B', [(19.5, 51.15), (18.72, 51.15)]),
    ('3V3', 'F', [(15.45, 51.0), (14.1, 51.0)]), ('3V3', 'B', [(14.1, 51.0), (14.1, 51.68)]),
    ('GND', 'B', [(14.1, 52.52), (14.1, 53.3)]),
    ('3V3', 'F', [(22.0, 52.55), (22.0, 54.15)]), ('3V3', 'B', [(22.0, 54.15), (22.0, 54.78)]),
    ('GND', 'B', [(22.0, 55.62), (22.0, 56.4)]),
    ('3V3A', 'F', [(26.5, 52.55), (26.5, 54.4)]), ('3V3A', 'F', [(27.0, 52.55), (27.0, 53.7), (26.5, 53.7)]),
    ('3V3A', 'B', [(26.5, 54.4), (26.5, 55.18), (27.7, 55.18)]),
    ('GND', 'B', [(26.5, 56.02), (26.5, 56.65), (26.3, 56.85)]), ('GND', 'B', [(29.1, 55.18), (29.85, 55.18)]),
    ('3V3', 'B', [(15.45, 43.25), (16.7, 43.25), (16.7, 44.24)]),     # C23 and R10 on one via
    ('GND', 'B', [(29.2, 48.98), (29.2, 48.2)]), ('GND', 'B', [(20.5, 39.3), (21.4, 39.3)]),
    ('GND', 'B', [(17.88, 51.15), (17.88, 50.35)]), ('GND', 'B', [(28.35, 41.4), (29.25, 41.4)]),
    ('GND', 'B', [(17.5, 41.3), (19.07, 41.3)]),                       # U3.4
]
DECOUPLING_VIAS = [('3V3', 28.75, 45.1), ('VCAP2', 18.0, 39.3), ('3V3', 17.0, 38.75), ('VCAP1', 29.25, 40.0),
                   ('3V3', 29.25, 39.0), ('3V3', 29.2, 50.5), ('3V3', 19.5, 51.15), ('3V3', 14.1, 51.0),
                   ('GND', 14.1, 53.3), ('3V3', 22.0, 54.15), ('GND', 22.0, 56.4), ('3V3A', 26.5, 54.4),
                   ('GND', 26.3, 56.85), ('GND', 29.85, 55.18), ('3V3', 16.7, 43.25), ('GND', 29.2, 48.2),
                   ('GND', 21.4, 39.3), ('GND', 17.88, 50.35), ('GND', 29.25, 41.4), ('GND', 17.5, 41.3)]
SMALL_VIA = (0.5, 0.3)


def logic(d):
    for layer, w, pts in USB_LIMITED_TRACKS:
        d.track('USB_LIMITED', layer, w, pts)
    for xy in V_USB:
        d.via('USB_LIMITED', *xy)
    for layer, w, pts in VLOGIC_TRACKS:
        d.track('VLOGIC', layer, w, pts)
    d.via('VLOGIC', *V_VLOGIC)
    d.via('VLOGIC', 26.95, 60.5, SMALL_VIA)                     # the D33 sense divider's via: a signal via
    for net, layer, w, pts in BUCK3_TRACKS:
        d.track(net, layer, w, pts)
    d.via('3V3', *V_3V3_OUT)
    for xy in BUCK3_GND_VIAS:
        d.via('GND', *xy)
    for layer, w, pts in SPINE_TRACKS:
        d.track('3V3', layer, w, pts)
    d.via('3V3', *V_D121)
    d.via('3V3', *V_R89)
    for pad, via in TAPS_3V3:
        d.track('3V3', 'B', 0.3, [pad, via])
        d.via('3V3', *via)
    for layer, w, pts in TRACKS_3V3A:
        d.track('3V3A', layer, w, pts)
    for xy in V_3V3A:
        d.via('3V3A', *xy)
    for net, layer, pts in DECOUPLING_TRACKS:
        d.track(net, layer, 0.2, pts)
    for net, x, y in DECOUPLING_VIAS:
        d.via(net, x, y, SMALL_VIA)


# ======================================================================================================================
# 5. Camera supplies (D37, D41)
# ======================================================================================================================
V_CAM_FB = (38.25, 33.1)
V_CAM_5V = (40.75, 41.4)                       # beside J9.1 (top), from L3.2's B.Cu
CAMERA_TRACKS = [
    # CAM_INPUT_LIMITED: U7.5 (OUT) -> TP71 -> C73.1 -> C72.1 -> U8.3 (VIN) and U8.2 (EN)
    ('CAM_INPUT_LIMITED', 'B', 0.25, [(34.55, 31.65), (35.0, 31.65)]),
    ('CAM_INPUT_LIMITED', 'B', 0.5, [(35.0, 31.65), (36.36, 31.65), (43.41, 31.65)]),
    ('CAM_INPUT_LIMITED', 'B', 0.6, [(43.41, 31.85), (43.41, 33.45)]),
    ('CAM_INPUT_LIMITED', 'B', 0.6, [(40.9, 33.85), (43.41, 33.85)]),
    ('CAM_INPUT_LIMITED', 'B', 0.3, [(39.95, 33.85), (40.9, 33.85)]),
    ('GND', 'B', 0.6, [(40.9, 36.05), (43.41, 36.05)]),                    # U8.4 -> C72.2: the input loop
    ('CAM_SW', 'B', 0.7, [(39.95, 36.05), (39.95, 38.47)]),               # U8.5 -> L3.1
    ('CAM_SW', 'B', 0.4, [(36.1, 37.61), (39.95, 37.61)]),                # C74.1
    ('CAM_BST', 'B', 0.3, [(39.0, 36.05), (36.1, 36.05)]),                # U8.6 -> C74.2
    ('CAM_FB', 'B', 0.25, [(39.0, 33.85), V_CAM_FB]),
    ('CAM_FB', 'F', 0.25, [V_CAM_FB, (38.675, 33.1)]),
    ('CAM_FB', 'F', 0.25, [(38.675, 32.3), (38.675, 33.1), (38.675, 33.9), (38.675, 35.5)]),   # R72.1, R71.2, C77.2
    # CAM_5V: L3.2 -> C75.1, C76.1, TP72, R78 and two vias to J9.1; the feedback senses at J9.1 (R71.1, C77.1)
    ('CAM_5V', 'B', 0.8, [(38.85, 43.17), (38.85, 46.07)]),
    ('CAM_5V', 'B', 0.8, [(35.29, 42.45), (39.2, 42.45)]),
    ('CAM_5V', 'B', 0.3, [(39.95, 43.17), (44.2, 43.17)]),
    ('CAM_5V', 'B', 0.3, [(38.5, 45.2), (36.325, 45.2)]),
    ('CAM_5V', 'B', 0.8, [V_CAM_5V, (40.75, 43.17)]),
    ('CAM_5V', 'F', 0.6, [V_CAM_5V, (40.75, 42.325)]),
    ('CAM_5V', 'F', 0.25, [(40.3, 33.9), (40.3, 35.5), (40.3, 40.95), V_CAM_5V]),
]
# pad -> via (B.Cu unless F), via size. Fix pass 2 (R8P2-ROUTING-01, D98): C75.2's and R78.2's GND vias are the
# board's 0.5 / 0.3 mm via (same drill and barrel): their 0.150 mm gaps to CAM_5V and CAM_MCU_TX open to 0.20 mm
CAMERA_GND = [
    ('B', (43.41, 36.45), (43.41, 37.6), VIA), ('B', (43.41, 28.85), (43.41, 27.8), VIA),
    ('B', (41.4, 46.07), (41.4, 47.8), SMALL_VIA),
    ('B', (35.29, 39.16), (34.4, 38.27), VIA),
    ('B', (34.675, 45.2), (33.9, 45.2), SMALL_VIA),                    # R78.2 (CAM_5V bleed) north-west of the radio lanes
]


def camera(d):
    for net, layer, w, pts in CAMERA_TRACKS:
        d.track(net, layer, w, pts)
    d.via('CAM_FB', *V_CAM_FB)
    d.via('CAM_5V', *V_CAM_5V)
    for layer, pad, via, size in CAMERA_GND:
        d.track('GND', layer, 0.4, [pad, via])
        d.via('GND', *via, size)
    d.track('GND', 'F', 0.3, [(40.325, 32.3), (41.15, 32.3), (41.45, 32.6)])    # R72.2 (top)
    d.via('GND', 41.45, 32.6, SMALL_VIA)        # 0.5 mm (fix pass 2, D98): 0.20 mm from the RAW_PROTECTED trunk


SECTIONS = [in2, band, raw_protected, logic, camera]


def check_input(b):
    """The board is r8_pcb.py's placed board: the rigid copper only and no In2 zone yet."""
    issues, digests = check_r8.rigid(b)
    assert not issues, issues
    zones = [z.GetZoneName() for z in b.Zones() if not z.GetIsRuleArea() and z.IsOnLayer(In2)]
    assert not zones, f'In2 already has zones {zones}: run r8_pcb.py first'


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--board', type=Path, default=PROJECT / 'm3.kicad_pcb')
    ap.add_argument('--no-fill', action='store_true', help='design aid: save unfilled')
    args = ap.parse_args()
    board = args.board.resolve()
    for ext in ('.kicad_pro', '.kicad_dru'):
        assert board.with_suffix(ext).is_file(), f'{board.with_suffix(ext).name} must sit beside the board'
    b = pcbnew.LoadBoard(str(board))
    check_input(b)
    pcbnew.KIID.SeedGenerator(KIID_SEED)
    for z in list(b.Zones()):
        if not z.GetIsRuleArea():
            z.UnFill()                     # stale fills would re-net new vias (spike (c) pitfall)
            if z.GetZoneName() == 'R6_BAT_IN_crossbar_F':
                b.Delete(z)                # D29's placeholder: the band's F.Cu pours replace it
    d = Draw(b)
    for section in SECTIONS:
        section(d)
    if not args.no_fill:
        b.BuildConnectivity()
        assert pcbnew.ZONE_FILLER(b).Fill(b.Zones()), 'native zone fill failed'
    b.BuildConnectivity()
    moved = [(mm(v.GetPosition().x), mm(v.GetPosition().y), d.vias.get((round(mm(v.GetPosition().x), 4),
              round(mm(v.GetPosition().y), 4))), v.GetNetname()) for v in b.GetTracks() if v.GetClass() == 'PCB_VIA']
    moved = [m for m in moved if m[2] is not None and m[2] != m[3]]
    assert not moved, f'connectivity re-netted vias (a via sits on foreign copper): {moved}'
    assert pcbnew.SaveBoard(str(board), b, True), 'save failed'
    b = pcbnew.LoadBoard(str(board))
    issues, digests = check_r8.rigid(b)
    assert not issues, issues
    print(f'r8_power: {len(d.vias)} vias, rigid digests {len(digests)}/12 equal R7')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
