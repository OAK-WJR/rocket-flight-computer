"""R9 step 7 family servo: the four servo lanes U1.22-25 -> R150-R153 (1 k) -> J122, the SRV05-4 clamp D121 and the
10 k pull-downs R154-R157 (r9_route.py; R9_DECISIONS D-S7-09).

The chain is check_actuators 7's: MCU -> pull-down + clamp -> 1 k series -> header. The 1 k resistors sit on the top under
the plug columns (D-S3-06), so each OUT lane is one straight F.Cu segment R15x.2 -> J122.(3i-2). The MCU side:
  F.Cu  the four lanes leave U1.22-25 forward and fan out in pin order into R150.1-R153.1: the outer lanes (S1 west, S4
        east) turn on y 53.85, clear of the pin-row escapes the status family drops at y 53.3, and enter their pad by one
        45-degree run from the inside; the inner lanes go straight forward and enter theirs, S2 from the east, S3 by
        one 45-degree run. Each lane continues out of its 1 k pad's far side to one via in the gap between the 1 k
        columns (S1 west of R150, S2 between R150 / R151, S3 between R152 / R153, S4 east of R153): 4 vias, the
        layer change the bottom clamp and pull-downs force.
  B.Cu  D121 turned 90 degrees (r9_place.tsv) sits between the inner vias, its pins counter-clockwise S1 (NW), S2 (SW),
        S3 (SE), S4 (NE) like the vias west to east, so every link is planar: the inner vias run straight into the
        south pins (S2, S3) with their pull-downs (R155, R156) on the same line beyond the via; the outer vias run one
        45-degree run round the clamp into the north pins (S1, S4) and drop straight into their pull-downs (R154,
        R157) under the via. D121.2 (GND) and D121.5 (3V3) each strap out of the clamp's side to one via.
U1.19 (GND), boxed in by S1's lane, drops forward to one GND via. GND vias wait for step 8's In1 pour (PENDING); the
pull-downs' GND pads are step 8's. D19: the gate lanes are 8 mm away.
"""
from r9_route import W, VIA_SIG, u1_pin

NETS = tuple(f'SERVO{i}_{s}' for i in (1, 2, 3, 4) for s in ('MCU', 'OUT'))
RAILS = ('GND', '3V3')
BUDGET = dict(length_mm=50.0, vias=4, critical_layer_changes=0, ratio=1.40)

Y_OUTER = 53.85                       # S1 / S4 turn
V1, V2, V3, V4 = (18.05, 54.9), (20.46, 54.4), (25.54, 54.4), (27.95, 54.9)
V_GND_D121, V_3V3_D121, V_GND_U1 = (20.46, 55.35), (25.54, 55.35), (21.4, 53.3)   # beside V2 / V3
R15X = {1: 19.19, 2: 21.73, 3: 24.27, 4: 26.81}   # R150-R153 / J122 columns
Y_MCU, Y_OUT, Y_J122 = 54.9, 56.9, 59.46

TRACKS = [   # net, layer, width, polyline
    # F.Cu: U1 -> 1 k pad -> via
    ('SERVO1_MCU', 'F', W, [u1_pin(22), (22.5, Y_OUTER), (20.24, Y_OUTER), (R15X[1], Y_MCU)]),
    ('SERVO1_MCU', 'F', W, [(R15X[1], Y_MCU), V1]),
    ('SERVO2_MCU', 'F', W, [u1_pin(23), (23.0, 54.4), (22.5, Y_MCU), (R15X[2], Y_MCU)]),
    ('SERVO2_MCU', 'F', W, [(R15X[2], Y_MCU), (20.96, Y_MCU), V2]),
    ('SERVO3_MCU', 'F', W, [u1_pin(24), (23.5, 54.13), (R15X[3], Y_MCU)]),
    ('SERVO3_MCU', 'F', W, [(R15X[3], Y_MCU), (25.04, Y_MCU), V3]),
    ('SERVO4_MCU', 'F', W, [u1_pin(25), (24.0, Y_OUTER), (25.76, Y_OUTER), (R15X[4], Y_MCU)]),
    ('SERVO4_MCU', 'F', W, [(R15X[4], Y_MCU), V4]),
    # B.Cu: via -> clamp pin, pull-down
    ('SERVO1_MCU', 'B', W, [(18.05, 54.18), V1]),                                         # R154.1
    ('SERVO1_MCU', 'B', W, [V1, (19.45, 56.3), (21.85, 56.3)]),                           # D121.1
    ('SERVO2_MCU', 'B', W, [(19.25, 54.4), V2]),                                          # R155.1
    ('SERVO2_MCU', 'B', W, [V2, (21.85, 54.4)]),                                          # D121.3
    ('SERVO3_MCU', 'B', W, [(24.15, 54.4), V3]),                                          # D121.4
    ('SERVO3_MCU', 'B', W, [V3, (26.75, 54.4)]),                                          # R156.1
    ('SERVO4_MCU', 'B', W, [(27.95, 54.18), V4]),                                         # R157.1
    ('SERVO4_MCU', 'B', W, [V4, (26.55, 56.3), (24.15, 56.3)]),                           # D121.6
    # OUT: 1 k pad -> header pin, straight
    ('SERVO1_OUT', 'F', W, [(R15X[1], Y_OUT), (R15X[1], Y_J122)]),
    ('SERVO2_OUT', 'F', W, [(R15X[2], Y_OUT), (R15X[2], Y_J122)]),
    ('SERVO3_OUT', 'F', W, [(R15X[3], Y_OUT), (R15X[3], Y_J122)]),
    ('SERVO4_OUT', 'F', W, [(R15X[4], Y_OUT), (R15X[4], Y_J122)]),
    # rails
    ('GND', 'B', W, [(21.85, 55.35), V_GND_D121]),                                        # D121.2
    ('3V3', 'B', W, [(24.15, 55.35), V_3V3_D121]),                                        # D121.5
    ('GND', 'F', W, [u1_pin(19), (21.0, 52.9), V_GND_U1]),                                # U1.19
]
VIAS = [('SERVO1_MCU', V1, VIA_SIG), ('SERVO2_MCU', V2, VIA_SIG), ('SERVO3_MCU', V3, VIA_SIG),
        ('SERVO4_MCU', V4, VIA_SIG), ('GND', V_GND_D121, VIA_SIG), ('3V3', V_3V3_D121, VIA_SIG),
        ('GND', V_GND_U1, VIA_SIG)]
PENDING = [V_GND_D121, V_GND_U1]
PADS = [('U1', '22', 'SERVO1_MCU', u1_pin(22)), ('U1', '23', 'SERVO2_MCU', u1_pin(23)),
        ('U1', '24', 'SERVO3_MCU', u1_pin(24)), ('U1', '25', 'SERVO4_MCU', u1_pin(25)),
        ('U1', '19', 'GND', u1_pin(19))] + \
    [(f'R{149 + i}', '1', f'SERVO{i}_MCU', (R15X[i], Y_MCU)) for i in (1, 2, 3, 4)] + \
    [(f'R{149 + i}', '2', f'SERVO{i}_OUT', (R15X[i], Y_OUT)) for i in (1, 2, 3, 4)] + \
    [('J122', str(3 * i - 2), f'SERVO{i}_OUT', (R15X[i], Y_J122)) for i in (1, 2, 3, 4)] + \
    [('D121', '1', 'SERVO1_MCU', (21.85, 56.3)), ('D121', '2', 'GND', (21.85, 55.35)),
     ('D121', '3', 'SERVO2_MCU', (21.85, 54.4)), ('D121', '4', 'SERVO3_MCU', (24.15, 54.4)),
     ('D121', '5', '3V3', (24.15, 55.35)), ('D121', '6', 'SERVO4_MCU', (24.15, 56.3)),
     ('R154', '1', 'SERVO1_MCU', (18.05, 54.18)), ('R155', '1', 'SERVO2_MCU', (19.25, 54.4)),
     ('R156', '1', 'SERVO3_MCU', (26.75, 54.4)), ('R157', '1', 'SERVO4_MCU', (27.95, 54.18))]


def draw(d):
    for net, layer, w, pts in TRACKS:
        d.track(net, layer, w, pts)
    for net, at, size in VIAS:
        d.via(net, at, size)
