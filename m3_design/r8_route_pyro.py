"""R8 step 6 family pyro (pyro_exits): the CH1 block's three exits to U1, and the RAW_ACT_SENSE divider (r8_route.py).

The block and its exit vias are rigid (D9, D15): GATE_N (23.0, 88.33), CONT (28.4, 88.61), ARM1_SENSE (18.18, 91.30).
The corridor between the block and U1's forward face is spike (a)'s ("GATE_N and CONT corridor"; R8_DECISIONS D32):
three B.Cu lanes over In2 GND (the D47 notch), ARM1_SENSE westmost on x 18.18, GATE_N on x 18.75, CONT on x 19.25.
  - ARM1_SENSE: one straight B.Cu run from its exit via to y 53.1, then under U1's forward pad row (y 52.45, the U1
    field over In2 3V3, D47) to R170 (4.7k) at pin 33; R170.2 -> pin 33 by one via (spike (a): the inherent
    crossover, pin 33 east, the exit west).
  - GATE_N: B.Cu from its exit via west, then forward on x 18.75 to a via beside pin 3, F.Cu into pin 3 (no via in a
    gate-flanking sentinel's way: pins 2 / 4 stay NC, D14).
  - CONT: B.Cu from its exit via west, forward on x 19.25, then east under C14 to R168.1 (series 4.7k at pin 15);
    R168.2 -> pin 15 by one via (D33).
  - RAW_ACT_SENSE (D32, D45): the divider at J122's aft end (R177 / R124, R125 / R182 / C122 on the spine x 25.92),
    the lane under the servo rows' F.Cu (y 58.1) and down x 30.65, east of ARM1_SENSE, to R172.1 under U1's east pad
    row; pin 34 leaves outward to a via and back under the pad row to R172.2 (D33). Not a pyro net: it crosses nothing.
Every layer change of a pyro net has a GND via within 1.5 mm (AGENTS section 3): the dives' partners, R7's partners
of the exit vias (not rigid: rebuilt here, none touching a block GND track end, which would join ch1_copper), and the
partners of the block's internal ARM1_SENSE In2 link vias (R7's positions).
"""
from r8_route import W, u1_pin

NETS = ('PYRO1_GATE_N', 'PYRO1_CONT', 'PYRO1_CONT_MCU', 'ARM1_SENSE', 'ARM1_SENSE_MCU', 'RAW_ACT_SENSE',
        'RAW_ACT_SENSE_MCU', 'RAW_ACT_SENSE_MID')
RAILS = ('GND',)
# lanes: ARM 52 mm, GATE_N 35.5, CONT 43.5, RAS 21.5, the dives; vias: 4 dives (ARM_MCU, GATE_N, CONT_MCU, RAS_MCU)
# CONT's ratio (1.37) is the corridor's: J122, its tie holes and the RAW_ACT box lie between the block and pin 15
BUDGET = dict(length_mm=170.0, vias=4, critical_layer_changes=3, ratio=1.40)

# RAS_MCU's via sits 0.15 mm off pin 34's pad end: pin 34 and R172.2 are 0.67 mm apart in plan, so every 0.1 mm the
# via moves out adds 0.2 mm of copper against route_check's 2 mm detour slack (D33's (31.9, 47.0) gave 2.17 mm)
V_GATE, V_CONT_MCU, V_ARM_MCU, V_RAS_MCU = (18.75, 54.3), (24.0, 53.7), (29.3, 47.5), (31.75, 47.0)
LANES = [   # net, layer, polyline
    # ARM1_SENSE (spike (a)): R170.1 -> under the forward pad row -> straight to the rigid exit via
    ('ARM1_SENSE', 'B', [(28.0, 48.36), (28.0, 51.95), (27.5, 52.45), (18.83, 52.45), (18.18, 53.1), (18.18, 91.3)]),
    ('ARM1_SENSE_MCU', 'F', [u1_pin(33), V_ARM_MCU]),
    ('ARM1_SENSE_MCU', 'B', [V_ARM_MCU, (28.0, 47.5)]),                                  # R170.2
    # GATE_N: exit via -> west -> forward on x 18.75 -> via beside pin 3 -> F.Cu into pin 3
    ('PYRO1_GATE_N', 'B', [(23.0, 88.33), (19.3, 88.33), (18.75, 87.78), V_GATE]),
    ('PYRO1_GATE_N', 'F', [u1_pin(3), (18.0, 53.55), V_GATE]),
    # CONT: exit via -> west -> forward on x 19.25 -> east under C14 -> R168.1 from the north
    ('PYRO1_CONT', 'B', [(28.4, 88.61), (27.39, 87.6), (19.85, 87.6), (19.25, 87.0), (19.25, 58.1), (19.85, 57.5),
                         (22.57, 57.5), (23.17, 56.9), (23.17, 54.6)]),
    ('PYRO1_CONT_MCU', 'F', [u1_pin(15), V_CONT_MCU]),
    ('PYRO1_CONT_MCU', 'B', [V_CONT_MCU, (24.0, 54.6)]),                                 # R168.2 (0.03 mm off centre)
    # RAW_ACT_SENSE (D32 / D45): the spine x 25.92 through R124.2, R125.1, R182.1, C122.1 (pad centres x 25.97), the
    # chamfer, under the servo lanes on y 58.1, down x 30.65 to R172.1 (fix pass 3, D106: x 30.6 -> 30.65 with R172,
    # 0.23 mm from USB_LIMITED's x 29.95 run)
    ('RAW_ACT_SENSE', 'B', [(25.92, 66.27), (25.92, 65.25), (25.92, 64.25), (25.92, 63.0), (25.92, 60.0),
                            (27.82, 58.1), (30.0, 58.1), (30.65, 57.45), (30.65, 48.53)]),
    ('RAW_ACT_SENSE_MID', 'B', [(25.92, 68.17), (25.92, 67.13)]),                        # R177.2 -> R124.1
    ('RAW_ACT_SENSE_MCU', 'F', [u1_pin(34), V_RAS_MCU]),
    ('RAW_ACT_SENSE_MCU', 'B', [V_RAS_MCU, (31.08, 47.67), (30.65, 47.67)]),            # R172.2
]
SIGNAL_VIAS = [('ARM1_SENSE_MCU', V_ARM_MCU), ('PYRO1_GATE_N', V_GATE), ('PYRO1_CONT_MCU', V_CONT_MCU),
               ('RAW_ACT_SENSE_MCU', V_RAS_MCU)]
GND_VIAS = [(28.6, 46.6),      # ARM1_SENSE_MCU dive (spike (a))
            (17.45, 54.6),     # GATE_N dive: west of the ARM lane, 1.33 mm
            (23.0, 53.85),     # CONT_MCU dive: south of pin 13's pad end, 1.01 mm
            (17.4, 90.2),      # ARM exit via (spike (a); R7's (18.18, 90.55) sits on the straight lane)
            (22.85, 89.63),    # GATE_N exit via (R7's partner)
            (28.55, 87.21),    # CONT exit via (R7's partner)
            (13.95, 93.75),    # the block's ARM1_SENSE In2 link vias (rigid; R7's partners)
            (13.95, 97.15)]
PADS = [('R170', '1', 'ARM1_SENSE', (28.0, 48.36)), ('R170', '2', 'ARM1_SENSE_MCU', (28.0, 47.5)),
        ('R168', '1', 'PYRO1_CONT', (23.17, 54.6)), ('R168', '2', 'PYRO1_CONT_MCU', (24.03, 54.6)),
        ('R124', '2', 'RAW_ACT_SENSE', (25.92, 66.27)), ('R125', '1', 'RAW_ACT_SENSE', (25.97, 65.25)),
        ('R182', '1', 'RAW_ACT_SENSE', (25.97, 64.25)), ('C122', '1', 'RAW_ACT_SENSE', (25.97, 63.0)),
        ('R172', '1', 'RAW_ACT_SENSE', (30.65, 48.53)), ('R172', '2', 'RAW_ACT_SENSE_MCU', (30.65, 47.67)),
        ('R177', '2', 'RAW_ACT_SENSE_MID', (25.92, 68.17)), ('R124', '1', 'RAW_ACT_SENSE_MID', (25.92, 67.13))]


def draw(d):
    for ref, num, net, at in PADS:
        d.pad(ref, num, net, at)
    for net, layer, pts in LANES:
        d.track(net, layer, W, pts)
    for net, xy in SIGNAL_VIAS:
        d.via(net, *xy)
    for xy in GND_VIAS:
        d.via('GND', *xy)
