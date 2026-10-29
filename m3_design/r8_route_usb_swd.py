"""R8 step 6 family usb_swd: USB-C J3 through the ESD array D4 to U1, the USB power switch U10's network, and the
Tag-Connect debug port J2 (SWD, NRST) (r8_route.py). R8_DECISIONS D52 (placement), D53 (topology).

Topology (D53). U1's aft face carries, west to east, SWDIO (72), USB_DP (71), USB_DM (70) and VBUS_SENSE (65); all four
go west, so they leave in that order, SWDIO innermost: SWDIO on y 36.40 under pins 73-75 (0.15 mm off their pad ends),
DP on y 36.02, DM on y 35.64 (F10: 5.0 mm from R306's courtyard, which bounds DM), VBUS_SENSE on y 35.10.
  - D4 (TVS array, flow-through) turned to rotation 270 at y 33.8 (D52): its DM pins on y 32.85 (J3.B7's row), its DP
    pins on y 34.75, DP forward of DM as U1 needs (DP west at pin 71), so neither lane crosses the other. Each lane runs
    straight through D4 (pad to pad under its body).
  - J3's two orientations join on F.Cu with no via: DM's A7 pad loops to B7 round the inner ends of the pad column
    (x 5.7, R7's "inner U"), DP's A6 pad tees into the B6 lane at 90 degrees. CC1 / CC2 run to R7 / R8 beside them.
  - VBUS: each J3 VBUS pad drops through a via beside it to one B.Cu spine x 7.95 along J3's inner side, which feeds
    U10.1, C28 and R9; D4's VBUS pin (between its data pins) drops through a via under D4's body to U10.3, tied to
    the spine by one diagonal. 0.3 mm (U10 limits at 0.45 A). Fix pass 1 (R8P1-POWER-03, D88): U10's 100 nF input
    bypass C83 sits beside U10.1 / U10.2 (TPS2553 SLVS841F 12.1), its VBUS pad on the run into U10.1 (the spine's tee
    at y 36.775) and its GND pad on U10.2's return to the D4.2 / U10.2 via; it was at its seed spot 17.5 mm away.
    C83's 1.55 mm pad pitch against U10's 0.95 mm leaves C83.2's centre 0.175 mm aft of U10.2's row. Fix pass 2
    (R8P2-ROUTING-04, D99): U10.2's GND runs straight west on its row into C83.2 (ending 0.175 mm off the pad's centre)
    and the link to the via leaves from C83.2's centre on its axis, so no micro-segment is left (fix pass 1 drew a
    0.247 mm 45-degree jog inside the pad from one to the other). C83 cannot move
    0.175 mm forward instead: its courtyard would come within 1.5 mm of J3.1's slot (R5 L10, r8_legalise) and any
    shift east overlaps U10's courtyard; U10 cannot move 0.175 mm aft: U10.3 would land on V_D's via.
  - U10's east pins sit in a pocket that step 5's USB_LIMITED fences: FAULT and ILIM leave under U10's body (B.Cu,
    between its pad columns): FAULT on x 12.4 north through R90 (pull-up) to its test pad TP86 (moved north beside R90,
    D52) and a via to pin 87, which leaves U1 between the LED pins; ILIM on x 12.85 to R85 (turned, D52).
  - VBUS_SENSE runs west under DM, drops at x 16.6 to TP92 and runs on B.Cu to the R9 / R110 divider.
  - SWD: SWDIO and SWCLK pass between J3's pins and the LEDs (y 38.9 / 39.5) and turn north on x 4.3 / 4.9 into J2's
    east column from the east (J2's 0.508 mm contact rule and its F.Cu key-out between the columns; track ends 0.095 mm
    off the pad centre, outside the key-out).
  - NRST (spike (a)'s dive to C24 and its B.Cu lane under U1's forward row) runs on one straight diagonal to y 42.75 and
    west under J2 (B.Cu: J2's contacts are F.Cu only) to a via at the board edge (x 0.8), then into J2.3 from the west:
    J2.3 is reachable only from the edge side (the key-out east of it, J2's alignment hole (1.334, 45.29) forward).
GND vias: D4.2 / U10.2 (the island the VBUS copper rings), R85.2, R110.2 / C86.2 (the pocket VBUS_SENSE rings), J2.5.
3V3 vias: R90.1, J2.1.
"""
from r8_route import W, VIA_PWR, u1_pin

NETS = ('USB_DP', 'USB_DM', 'CC1', 'CC2', 'VBUS', 'VBUS_SENSE', 'USB_FAULT_N', 'USB_ILIM', 'SWDIO', 'SWCLK', 'NRST')
RAILS = ('GND', '3V3')
BUDGET = dict(length_mm=155.0, vias=4, critical_layer_changes=0, ratio=1.35)   # worst 1.25 since fix pass 1 (DM's 45-degree run)
W_VBUS = 0.3                     # VBUS: U10 limits at 0.45 A

Y_SWDIO, Y_DP, Y_DM, Y_VSENSE = 36.40, 36.02, 35.64, 35.10
V_A, V_B, V_D = (7.95, 31.2), (7.95, 36.0), (11.1, 33.8)
T_U10 = (7.95, 36.775)         # the spine's tee to U10.1 through C83.1, 0.775 mm past V_B
V_FAULT, V_VSENSE, V_NRST = (14.0, 44.5), (16.6, 35.1), (24.0, 51.1)
V_NRST_EDGE = (0.8, 42.75)

TRACKS = [   # net, layer, width, polyline
    # USB data (J3 -> D4 straight through -> U1); J3's second orientation joined on F.Cu
    # out of D4.6 one 45-degree run to DM's lane y 35.64 (fix pass 1, D91: the rise on x 13 was a 1.25 x chain detour,
    # +2.2 mm, with a DRC-clean redraw; F10's 5 mm to R306 binds at x 18.8 on the lane, unchanged)
    ('USB_DM', 'F', W, [(6.88, 32.85), (9.85, 32.85), (12.15, 32.85), (12.6, 32.85), (15.39, Y_DM), (19.5, Y_DM),
                        u1_pin(70)]),
    ('USB_DM', 'F', W, [(6.88, 32.85), (5.7, 32.85), (5.7, 33.85), (6.88, 33.85)]),          # B7 -> A7 inner U
    ('USB_DP', 'F', W, [(6.88, 34.35), (8.4, 34.35), (8.8, 34.75), (9.85, 34.75), (12.15, 34.75), (12.15, 35.62),
                        (12.55, Y_DP), (19.0, Y_DP), u1_pin(71)]),
    ('USB_DP', 'F', W, [(6.88, 33.35), (8.4, 33.35), (8.4, 34.35)]),                          # A6 tees into B6's lane
    ('CC1', 'F', W, [(6.88, 32.35), (7.9, 32.35), (8.57, 31.68), (8.57, 30.0)]),              # R7.1
    ('CC2', 'F', W, [(6.88, 35.35), (8.57, 35.35), (8.57, 37.2)]),                            # R8.1
    # VBUS
    ('VBUS', 'F', W_VBUS, [(6.88, 31.2), V_A]),
    ('VBUS', 'F', W_VBUS, [(6.88, 36.0), V_B]),
    ('VBUS', 'F', W_VBUS, [(12.15, 33.8), V_D]),
    ('VBUS', 'B', W_VBUS, [V_A, V_B, T_U10, (7.95, 40.95), (8.8, 41.8)]),                     # the spine x 7.95, C28.1
    ('VBUS', 'B', W_VBUS, [T_U10, (9.55, 36.775), (10.675, 36.775), (11.1, 36.35)]),        # C83.1, U10.1
    ('VBUS', 'B', W_VBUS, [V_A, (7.95, 29.2), (11.97, 29.2)]),                               # R9.1 (sense divider)
    ('VBUS', 'B', W_VBUS, [V_D, (11.1, 34.45)]),                                              # U10.3
    ('VBUS', 'B', W_VBUS, [V_D, (8.5, 31.2), V_A]),
    # VBUS_SENSE: pin 65 -> under DM -> TP92 -> R9.2 / R110.1
    ('VBUS_SENSE', 'F', W, [u1_pin(65), (22.0, 36.5), (20.6, Y_VSENSE), V_VSENSE]),
    ('VBUS_SENSE', 'B', W, [V_VSENSE, (16.6, 29.6), (12.825, 29.6)]),
    ('VBUS_SENSE', 'B', W, [(12.825, 29.6), (12.825, 29.2)]),                                 # R9.2
    ('VBUS_SENSE', 'B', W, [(12.825, 29.6), (11.825, 30.6), (11.575, 30.6)]),                # R110.1
    # USB_FAULT_N / USB_ILIM (U10's pocket, under its body)
    ('USB_FAULT_N', 'F', W, [u1_pin(87), V_FAULT]),
    ('USB_FAULT_N', 'B', W, [V_FAULT, (12.4, 42.9), (12.4, 39.8), (12.4, 34.45), (13.7, 34.45)]),   # TP86, U10.4
    ('USB_FAULT_N', 'B', W, [(12.4, 39.8), (13.225, 39.8)]),                                 # R90.2
    ('USB_ILIM', 'B', W, [(13.7, 35.4), (12.85, 35.4), (12.85, 38.025), (13.125, 38.3)]),    # U10.5 -> R85.1
    # SWD
    ('SWDIO', 'F', W, [u1_pin(72), (18.5, Y_SWDIO), (14.0, Y_SWDIO), (11.5, 38.9), (4.3, 38.9), (4.3, 41.48),
                       (3.085, 41.48)]),
    ('SWCLK', 'F', W, [u1_pin(76), (14.4, 39.0), (13.9, 39.5), (4.9, 39.5), (4.9, 42.75), (3.085, 42.75)]),
    # NRST (spike (a)): pin 14 -> C24 -> under U1's forward row -> one diagonal -> under J2 -> J2.3 from the edge side
    ('NRST', 'F', W, [u1_pin(14), (23.5, 51.6), V_NRST]),
    ('NRST', 'B', W, [(25.33, 51.1), V_NRST, (23.15, 51.95), (16.1, 51.95), (6.9, 42.75), V_NRST_EDGE]),
    ('NRST', 'F', W, [V_NRST_EDGE, (1.6, 42.75)]),
    # rails: 3V3 and GND taps of this family's parts
    ('3V3', 'B', W, [(11.575, 39.8), (10.8, 40.575)]),                                        # R90.1 (via clear of SWCLK)
    ('3V3', 'F', W, [(1.615, 41.48), (0.8, 40.665)]),                                         # J2.1
    ('GND', 'F', W, [(1.615, 44.02), (0.8, 44.02)]),                                          # J2.5
    ('GND', 'F', W, [(9.85, 33.8), (9.0, 33.8)]),                                             # D4.2
    ('GND', 'B', W, [(11.1, 35.4), (9.55, 35.4)]),                                           # U10.2 -> C83.2 (D99)
    ('GND', 'B', W, [(9.55, 35.225), (9.55, 34.35), (9.0, 33.8)]),                           # C83.2 -> the D4.2 via
    ('GND', 'B', W, [(11.475, 38.3), (10.6, 38.3)]),                                          # R85.2
]
VIAS = [('VBUS', V_A, VIA_PWR), ('VBUS', V_B, VIA_PWR), ('VBUS', V_D, VIA_PWR),
        ('VBUS_SENSE', V_VSENSE, None), ('USB_FAULT_N', V_FAULT, None), ('NRST', V_NRST, None),
        ('NRST', V_NRST_EDGE, None),
        ('3V3', (10.8, 40.575), None), ('3V3', (0.8, 40.665), None),
        ('GND', (0.8, 44.02), None), ('GND', (9.0, 33.8), None), ('GND', (10.6, 38.3), None),
        ('GND', (14.2, 31.5), None)]                    # the pocket VBUS_SENSE rings (R110.2, C86.2): pour keeps it
PADS = [('J3', 'B7', 'USB_DM', (6.88, 32.85)), ('J3', 'A7', 'USB_DM', (6.88, 33.85)),
        ('J3', 'B6', 'USB_DP', (6.88, 34.35)), ('J3', 'A6', 'USB_DP', (6.88, 33.35)),
        ('J3', 'A5', 'CC1', (6.88, 32.35)), ('J3', 'B5', 'CC2', (6.88, 35.35)),
        ('J3', 'A4B9', 'VBUS', (6.88, 31.2)), ('J3', 'B4A9', 'VBUS', (6.88, 36.0)),
        ('D4', '1', 'USB_DM', (9.85, 32.85)), ('D4', '6', 'USB_DM', (12.15, 32.85)),
        ('D4', '3', 'USB_DP', (9.85, 34.75)), ('D4', '4', 'USB_DP', (12.15, 34.75)),
        ('D4', '5', 'VBUS', (12.15, 33.8)), ('D4', '2', 'GND', (9.85, 33.8)),
        ('R7', '1', 'CC1', (8.57, 30.0)), ('R8', '1', 'CC2', (8.57, 37.2)),
        ('U10', '1', 'VBUS', (11.1, 36.35)), ('U10', '3', 'VBUS', (11.1, 34.45)), ('U10', '2', 'GND', (11.1, 35.4)),
        ('U10', '4', 'USB_FAULT_N', (13.7, 34.45)), ('U10', '5', 'USB_ILIM', (13.7, 35.4)),
        ('C28', '1', 'VBUS', (8.8, 41.8)), ('C83', '1', 'VBUS', (9.55, 36.775)), ('C83', '2', 'GND', (9.55, 35.225)),
        ('R9', '1', 'VBUS', (11.97, 29.2)),
        ('R9', '2', 'VBUS_SENSE', (12.83, 29.2)), ('R110', '1', 'VBUS_SENSE', (11.575, 30.6)),
        ('TP92', '1', 'VBUS_SENSE', (16.6, 29.6)), ('TP86', '1', 'USB_FAULT_N', (12.4, 42.9)),
        ('R90', '2', 'USB_FAULT_N', (13.225, 39.8)), ('R90', '1', '3V3', (11.575, 39.8)),
        ('R85', '1', 'USB_ILIM', (13.125, 38.3)), ('R85', '2', 'GND', (11.475, 38.3)),
        ('J2', '2', 'SWDIO', (2.985, 41.48)), ('J2', '4', 'SWCLK', (2.985, 42.75)), ('J2', '3', 'NRST', (1.715, 42.75)),
        ('J2', '1', '3V3', (1.715, 41.48)), ('J2', '5', 'GND', (1.715, 44.02)), ('C24', '1', 'NRST', (25.33, 51.1))]


def draw(d):
    for ref, num, net, at in PADS:
        d.pad(ref, num, net, at)
    for net, layer, w, pts in TRACKS:
        d.track(net, layer, w, pts)
    for net, xy, size in VIAS:
        d.via(net, *xy, **({} if size is None else dict(size=size)))
