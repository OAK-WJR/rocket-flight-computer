"""R8 step 6 family servo: the four servo lanes through D121 to J122 (r8_route.py).

Port of spike (b) (m3_design/r8_spikes/b_servo/servo_route.py route(), RESULT.md), on the placement it proved
(r8_place.tsv basis spike-b). D7 / D26: D121 keeps the pass-5 channel map (pins 1 / 3 / 4 / 6 = SERVO1-4_MCU), so
check_actuators 7c is unchanged. Per channel i = 1..4 (lane x = U1.(21+i)'s pad, row y = J122.(3i-2)'s pad):
  F.Cu  U1.(21+i) straight forward on the pin's own x, one 45-degree corner (0.5 mm) east onto the J122 row, the
        pull-down R(153+i).1 on the row as a node, a via at x 32.6                          [SERVOi_MCU]
  B.Cu  the via -> R(149+i).1 | 1k | R(149+i).2 -> J122.(3i-2)                           [SERVOi_MCU | SERVOi_OUT]
        the four B.Cu rows cross under the F.Cu lanes: the full reversal from U1's pin order to J122's row order
        (D7: "the reversal after the taps, made by the 1k resistors and the THT pins")
  B.Cu  D121 (rotation 180) tapped from the four vias: pins 3 (S2) and 4 (S3) straight on their rows, pins 1 (S1) and
        6 (S4) round the row ends with one 45-degree corner each
D121.2 drops to a GND via north; D121.5's 3V3 via and stub are step 5's. GND stitching vias sit in the three pockets
between rows (each F.Cu / B.Cu pocket gets a via; spike (b)). In2 under the rows is GND (D47).
"""
from r8_route import W, VIA_PWR

NETS = tuple(f'SERVO{i}_{s}' for i in (1, 2, 3, 4) for s in ('MCU', 'OUT'))
RAILS = ('GND',)
BUDGET = dict(length_mm=145.0, vias=4, critical_layer_changes=0, ratio=1.15)   # spike (b): 141.0 mm, 4 vias, 1.13

CH = (1, 2, 3, 4)
X = {1: 27.5, 2: 28.0, 3: 28.5, 4: 29.0}          # U1.22-25 pad centres
U1_Y = 52.55
Y = {1: 79.51, 2: 76.97, 3: 74.43, 4: 71.89}      # J122.1 / 4 / 7 / 10 (signal column x 25.54)
J122_X = 25.54
CHAMFER = 0.5
RES_X = 30.4                                       # R150-R153 (B, rot 180: pad 1 / MCU east) and R154-R157 (F)
VIA_X = 32.6
D121_PIN = {1: '1', 2: '3', 3: '4', 4: '6'}
D121_GND_VIA = (34.4, 78.20)
POCKET_GND_VIAS = [(31.4, round((Y[i] + Y[i + 1]) / 2, 4)) for i in (1, 2, 3)]
W_PWR = 0.3


def draw(d):
    for i in CH:
        net, out = f'SERVO{i}_MCU', f'SERVO{i}_OUT'
        x, y = X[i], Y[i]
        d.pad('U1', str(21 + i), net, (x, U1_Y))
        d.pad('J122', str(3 * i - 2), out, (J122_X, y))
        d.pad(f'R{149 + i}', '1', net, (RES_X + 1, y))
        d.pad(f'R{149 + i}', '2', out, (RES_X - 1, y))
        d.pad(f'R{153 + i}', '1', net, (RES_X, y))
        d.track(net, 'F', W, [(x, U1_Y), (x, y - CHAMFER), (x + CHAMFER, y), (RES_X, y), (VIA_X, y)])
        d.via(net, VIA_X, y, VIA_PWR)
        d.track(net, 'B', W, [(VIA_X, y), (RES_X + 1, y)])
        d.track(out, 'B', W, [(RES_X - 1, y), (J122_X, y)])
        px, py = d.pad('D121', D121_PIN[i], net)
        if i in (2, 3):                                  # NW / SW pads: straight in on the row (0.12 mm off centre)
            d.track(net, 'B', W, [(VIA_X, y), (px, y)])
        else:                                            # NE / SE pads: round the row end, one 45-degree corner
            s = -1 if i == 1 else 1                      # S1 turns aft (-y) into pin 1, S4 forward into pin 6
            d.track(net, 'B', W, [(VIA_X, y), (px - CHAMFER, y), (px, y + s * CHAMFER), (px, py)])
    gx, gy = d.pad('D121', '2', 'GND')
    d.track('GND', 'B', W_PWR, [(gx, gy), D121_GND_VIA])
    d.via('GND', *D121_GND_VIA, VIA_PWR)
    for xy in POCKET_GND_VIAS:
        d.via('GND', *xy, VIA_PWR)
