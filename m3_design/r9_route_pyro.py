"""R9 step 7 family pyro: the RAW_ACT_SENSE divider (r9_route.py; R9_DECISIONS D-S5-07, D-S7-08).

The step-5 block drew every CH1 net; this family is the battery-voltage sense divider of the actuator rail: RAW_ACT -
R177 (5.1 k) - RAW_ACT_SENSE_MID - R124 (5.1 k) - RAW_ACT_SENSE - R125 || R182 (2 k each) to GND, C122 (10 nF) to GND,
and R172 (4.7 k) at the MCU end into U1.34 (P-8). All on B.Cu but the MCU pin's stub; parts re-placed (r9_place.tsv,
D-S7-08) so that the battery-live copper is a 1.35 mm tap and the long run is the sense node:
  RAW_ACT          one via into In2's RAW_ACT region (y >= 57.0) at (27.45, 57.95): west of the ARM1_SENSE F.Cu lane
                   (rule A 0.5 + 0.2 margin: 0.73 mm on F.Cu; east of the lane the J122 tie hole's 0.5 mm edge clearance
                   leaves no spot inside the region), clear of R153.2 and J122.10; straight down into R177.1 (the step-6
                   PARTIAL rail's last pad)
  ..._MID          R177.2 straight east into R124.1, on B.Cu under the ARM lane
  RAW_ACT_SENSE    the column x 30.07: R124.2, R125.1, R182.1, C122.1; from C122.1 one 45-degree step to y 52.45 (between
                   the servo pull-downs' GND pads and C90), west, one 45-degree corner and down x 25.42 under U1's east
                   pad ends (U1's eastward escapes keep their vias at x >= 26.75) into R172.1 from the north
  ..._MCU          U1.34 straight east on F.Cu to the via (26.95, 46.5), B.Cu one 45-degree step west into R172.2:
                   2.24 mm of track (P-8 <= 3.0); the via sits on pin 34's line (D-S7-12) so that U1.35's lane
                   (camera, CAM_5V_SENSE) leaves east under it
Sense nets are not critical signal nets (route_check classes), so the MCU-side via needs no GND partner. The GND pads
(R125.2, R182.2, C122.2) are step 8's (B.Cu pour). Bridge table (P-5): every sense pad >= 1.0 mm from the 3V3 pads of
C90, R89 and R91, RAW_ACT's R177.1 >= 1.0 mm from the midpoint's R124.1 (legaliser, step 3 gate).
"""
from r9_route import W, VIA_SIG, u1_pin

NETS = ('RAW_ACT_SENSE', 'RAW_ACT_SENSE_MID', 'RAW_ACT_SENSE_MCU')
CONTINUES = ('RAW_ACT',)           # step 6's PARTIAL rail, open at R177.1 (r9_power.PARTIAL)
RAILS = ()
BUDGET = dict(length_mm=18.0, vias=1, critical_layer_changes=0, ratio=1.45)

V_RAW = (27.45, 57.95)             # RAW_ACT: In2 tap
V_MCU = (26.95, 46.5)              # RAW_ACT_SENSE_MCU: U1.34's layer change (D-S7-12: on pin 34's line)
SPINE_X, BRANCH_Y, LANE_X = 30.07, 52.45, 25.42

TRACKS = [   # net, layer, polyline (0.2 mm)
    ('RAW_ACT', 'B', [V_RAW, (27.45, 56.6)]),                                                        # R177.1
    ('RAW_ACT_SENSE_MID', 'B', [(28.31, 56.6), (29.21, 56.6)]),                                      # R177.2 -> R124.1
    ('RAW_ACT_SENSE', 'B', [(SPINE_X, 56.6), (SPINE_X, 55.5)]),                                      # R124.2 -> R125.1
    ('RAW_ACT_SENSE', 'B', [(SPINE_X, 55.5), (SPINE_X, 54.6)]),                                      # -> R182.1
    ('RAW_ACT_SENSE', 'B', [(SPINE_X, 54.6), (SPINE_X, 53.2)]),                                      # -> C122.1
    ('RAW_ACT_SENSE', 'B', [(SPINE_X, 53.2), (SPINE_X - 0.75, BRANCH_Y), (LANE_X + 0.5, BRANCH_Y),
                            (LANE_X, BRANCH_Y - 0.5), (LANE_X, 46.1)]),                             # R172.1
    ('RAW_ACT_SENSE_MCU', 'F', [u1_pin(34), V_MCU]),
    ('RAW_ACT_SENSE_MCU', 'B', [V_MCU, (26.55, 46.1), (26.28, 46.1)]),                                # R172.2
]
PADS = [('R177', '1', 'RAW_ACT', (27.45, 56.6)), ('R177', '2', 'RAW_ACT_SENSE_MID', (28.31, 56.6)),
        ('R124', '1', 'RAW_ACT_SENSE_MID', (29.21, 56.6)), ('R124', '2', 'RAW_ACT_SENSE', (SPINE_X, 56.6)),
        ('R125', '1', 'RAW_ACT_SENSE', (SPINE_X, 55.5)), ('R182', '1', 'RAW_ACT_SENSE', (SPINE_X, 54.6)),
        ('C122', '1', 'RAW_ACT_SENSE', (SPINE_X, 53.2)), ('R172', '1', 'RAW_ACT_SENSE', (LANE_X, 46.1)),
        ('R172', '2', 'RAW_ACT_SENSE_MCU', (26.28, 46.1)), ('U1', '34', 'RAW_ACT_SENSE_MCU', u1_pin(34))]


def draw(d):
    for net, layer, pts in TRACKS:
        d.track(net, layer, W, pts)
    d.via('RAW_ACT', V_RAW, VIA_SIG)
    d.via('RAW_ACT_SENSE_MCU', V_MCU, VIA_SIG)
