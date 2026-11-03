"""R9 step 7 family usb_swd: the USB-C data, CC and VBUS nets, the USB limit switch's control and sense, the SWD lanes
and NRST (r9_route.py; R9_DECISIONS D-S7-11).

J3 (USB-C, west edge) - D4 (USBLC6-2, flow-through) - U1.70 / 71 (DM / DP); U10 (USB current limit) with R85 (ILIM),
R90 / TP86 (USB_FAULT_N), R9 / R110 / TP92 (VBUS_SENSE); J2 (Tag-Connect, F.Cu) for SWD and NRST.
  USB_DM / DP  F.Cu only. J3's two DM pins joined round the west (inner U, x 5.75), its two DP pins by a T at x 7.9;
               DM jogs once (0.4 mm on a 0.57 mm diagonal) onto D4's DM row, DP runs straight (D4 0.05 mm aft, D-S7-11);
               D4's pin pairs bridged under its body (R8's way); east of D4 DM one 45-degree run to U1.70 and DP one
               to U1.71. Every DM / DP copper >= 5.0 mm from the RF parts' courtyards (R-10 / F10: DM leaves y 33.15 at
               x 11.95)
  VBUS         J3's two VBUS pin pairs dive at once (V_A, V_B) to a B.Cu spine x 7.25, east on y 33.5 to R9.1 and U10.1
               and up to V_D, the via east of D4 that takes D4.5 (VBUS on F.Cu under D4's body); V_A also feeds U10.3
               (EN), C83 and C28. A tree (no loop); 0.3 mm
  CC1 / CC2    one via each beside J3, B.Cu into R7 / R8
  VBUS_SENSE   R9.2 (beside J3) by one via onto F.Cu y 31.2, a second via onto B.Cu for R110 and TP92 (one 45-degree
               run, 1.08 mm from TP82) and F.Cu straight on to U1.65
  USB_FAULT_N  U1.87 inward on F.Cu (x 11.75) to the interior's south-west corner via, B.Cu south under U1's west pads
               and U10's body to U10.4, a branch to R90 and one on to TP86 south of U10
  USB_ILIM     U10.5 straight east to R85.1 (R85 on its line, D-S7-16)
  SWDIO / SWCLK  F.Cu west to x 4.0 / 4.5 and north into J2.2 / J2.4 (track ends outside J2's keep-out rectangle)
  NRST         U1.14 inward on F.Cu east of HSE_OUT (C24 tapped by one via), parallel to QSPI_IO3's F.Cu run to the via
               (17.54, 40.0) under U3's south-west half (south-west of QSPI_IO1's B.Cu diagonal), B.Cu west by the interior
               exit W41.44 to a via beside J2.3. Its 1.50 ratio is the inward route: U1.14 is sealed north of the forward
               face like U1.7 / 8 / 17, and J2 is on the west edge
The SWD nets and NRST are not critical classes (no GND partner via needed); USB data has no via. D4.2's GND via under
D4's body and J2.5's wait for step 8 (PENDING). Step 8 moved NRST's diagonal 0.04 mm east (D-S8-04): with USB_LIMITED's
F.Cu diagonal 0.71 mm away it left a 0.157 mm GND sliver; 0.68 mm leaves the GND fill none.
"""
from r9_route import W, VIA_SIG, VIA_PWR, u1_pin

NETS = ('USB_DP', 'USB_DM', 'CC1', 'CC2', 'VBUS', 'VBUS_SENSE', 'USB_FAULT_N', 'USB_ILIM', 'SWDIO', 'SWCLK', 'NRST')
RAILS = ('GND', '3V3')
BUDGET = dict(length_mm=140.0, vias=8, critical_layer_changes=0, ratio=1.50)
WV = 0.3                                     # VBUS (R8 width)

V_A, V_B, V_D = (7.95, 31.4), (8.0, 37.2), (11.95, 34.1)          # VBUS: J3 A4B9, J3 B4A9, east of D4
V_CC1, V_CC2 = (7.85, 32.75), (7.95, 36.05)
V_SENSE, V_SENSE2 = (9.95, 31.2), (16.6, 33.3)
V_FAULT = (11.75, 40.55)                                           # the interior's south-west corner
V_NRST, V_NRST_E, V_C24 = (17.54, 40.0), (0.95, 43.3), (19.3, 50.6)       # V_NRST 0.04 mm east: D-S8-04
G_D4, G_J2 = (9.95, 34.1), (0.95, 44.57)
V3 = dict(R90=(15.125, 35.65), J2=(0.95, 42.03))

TRACKS = [   # net, layer, width, polyline
    # USB data: J3 -> D4 (DM's two pins joined west, DP's by the T at x 7.9), D4's pairs bridged, D4 -> U1
    ('USB_DM', 'F', W, [(6.88, 33.55), (7.75, 33.55), (8.15, 33.15), (8.8, 33.15)]),                   # J3.B7 -> D4.1
    ('USB_DM', 'F', W, [(6.88, 34.55), (5.75, 34.55), (5.75, 33.55), (6.88, 33.55)]),                  # J3.A7
    ('USB_DP', 'F', W, [(6.88, 35.05), (7.9, 35.05), (8.8, 35.05)]),                                    # J3.B6 -> D4.3
    ('USB_DP', 'F', W, [(6.88, 34.05), (7.9, 34.05), (7.9, 35.05)]),                                    # J3.A6
    ('USB_DM', 'F', W, [(8.8, 33.15), (11.1, 33.15)]),                                                  # D4.1 - D4.6
    ('USB_DP', 'F', W, [(8.8, 35.05), (11.1, 35.05)]),                                                  # D4.3 - D4.4
    ('USB_DM', 'F', W, [(11.1, 33.15), (11.95, 33.15), (14.5, 35.7), u1_pin(70)]),
    ('USB_DP', 'F', W, [(11.1, 35.05), (13.2, 35.05), (14.0, 35.85), u1_pin(71)]),
    # CC
    ('CC1', 'F', W, [(6.88, 33.05), (7.55, 33.05), V_CC1]),
    ('CC1', 'B', W, [V_CC1, (7.93, 32.83), (9.0, 32.83)]),                                              # R7.1
    ('CC2', 'F', W, [(6.88, 36.05), V_CC2]),
    ('CC2', 'B', W, [V_CC2, (8.33, 36.43), (9.0, 36.43)]),                                              # R8.1
    # VBUS
    ('VBUS', 'F', WV, [(6.88, 31.9), (7.45, 31.9), V_A]),
    ('VBUS', 'F', WV, [(6.88, 36.7), (7.5, 36.7), V_B]),
    ('VBUS', 'F', WV, [(11.1, 34.1), V_D]),                                                             # D4.5
    ('VBUS', 'B', WV, [V_B, (7.25, 36.45), (7.25, 33.5)]),
    ('VBUS', 'B', WV, [(7.25, 33.5), (7.25, 32.1), V_A]),
    ('VBUS', 'B', WV, [(7.25, 33.5), (9.95, 33.5), (11.35, 33.5)]),
    ('VBUS', 'B', WV, [(9.95, 33.5), (9.95, 32.83)]),                                                   # R9.1
    ('VBUS', 'B', WV, [(11.35, 33.5), (11.35, 32.15)]),                                                 # U10.1
    ('VBUS', 'B', WV, [(11.35, 33.5), V_D]),
    ('VBUS', 'B', WV, [V_A, (9.3, 30.05)]),
    ('VBUS', 'B', WV, [(9.3, 30.05), (11.3, 30.05)]),                                                   # U10.3
    ('VBUS', 'B', WV, [(9.3, 30.05), (9.3, 28.6)]),                                                     # C83.1
    ('VBUS', 'B', WV, [(11.3, 30.05), (12.35, 29.0), (12.35, 28.4)]),                                   # C28.1
    # VBUS_SENSE
    ('VBUS_SENSE', 'B', W, [(9.95, 31.97), V_SENSE]),                                                   # R9.2
    ('VBUS_SENSE', 'F', W, [V_SENSE, (14.5, 31.2), V_SENSE2]),
    ('VBUS_SENSE', 'F', W, [V_SENSE2, (17.0, 33.7), u1_pin(65)]),
    ('VBUS_SENSE', 'B', W, [V_SENSE2, (17.7, 34.4), (18.975, 34.4)]),                                   # R110.1
    ('VBUS_SENSE', 'B', W, [(18.975, 34.4), (21.6, 31.775)]),                                           # TP92
    # USB_FAULT_N
    ('USB_FAULT_N', 'F', W, [u1_pin(87), (11.75, 44.0), V_FAULT]),
    ('USB_FAULT_N', 'B', W, [V_FAULT, (11.2, 40.0), (11.2, 36.0), (12.6, 34.6), (12.6, 30.05), (13.9, 30.05)]),
    ('USB_FAULT_N', 'B', W, [(13.9, 30.05), (14.85, 29.1), (14.85, 27.3), (14.05, 26.5)]),              # TP86
    ('USB_FAULT_N', 'B', W, [(12.6, 34.6), (12.8, 34.8), (13.475, 34.8)]),                              # R90.2
    # USB_ILIM
    ('USB_ILIM', 'B', W, [(13.9, 31.0), (15.6, 31.0)]),                                         # R85.1 (D-S7-16)
    # SWD
    ('SWDIO', 'F', W, [u1_pin(72), (13.5, 36.1), (13.25, 35.85), (8.85, 35.85), (8.85, 39.6), (4.0, 39.6),
                       (4.0, 42.03), (3.3, 42.03)]),                                                    # J2.2
    ('SWCLK', 'F', W, [u1_pin(76), (9.35, 38.5), (9.35, 40.1), (4.5, 40.1), (4.5, 43.3), (3.3, 43.3)]),  # J2.4
    # NRST
    ('NRST', 'F', W, [u1_pin(14), (18.5, 50.6), (18.5, 49.75), (20.3, 47.95), (20.3, 42.76), V_NRST]),
    ('NRST', 'F', W, [(18.5, 50.6), V_C24]),
    ('NRST', 'B', W, [V_C24, (20.33, 50.6)]),                                                           # C24.1
    ('NRST', 'B', W, [V_NRST, (16.1, 41.44), (3.4, 41.44), (1.54, 43.3), V_NRST_E]),
    ('NRST', 'F', W, [V_NRST_E, (1.4, 43.3)]),                                                          # J2.3
    # rails: J2's 3V3 / GND, R90's pull-up, D4's GND
    ('3V3', 'F', W, [V3['J2'], (1.4, 42.03)]),                                                          # J2.1
    ('GND', 'F', W, [G_J2, (1.4, 44.57)]),                                                              # J2.5
    ('3V3', 'B', W, [(15.125, 34.8), V3['R90']]),                                                       # R90.1
    ('GND', 'F', W, [(8.8, 34.1), G_D4]),                                                               # D4.2
]
SIGNAL_VIAS = [('CC1', V_CC1), ('CC2', V_CC2), ('VBUS_SENSE', V_SENSE), ('VBUS_SENSE', V_SENSE2),
               ('USB_FAULT_N', V_FAULT), ('NRST', V_NRST), ('NRST', V_NRST_E), ('NRST', V_C24)]
PENDING = [G_D4, G_J2]
PADS = [
    ('C24', '1', 'NRST', (20.33, 50.6)), ('C28', '1', 'VBUS', (12.35, 28.4)), ('C83', '1', 'VBUS', (9.425, 28.4)),
    ('D4', '1', 'USB_DM', (8.8, 33.15)), ('D4', '2', 'GND', (8.8, 34.1)), ('D4', '3', 'USB_DP', (8.8, 35.05)),
    ('D4', '4', 'USB_DP', (11.1, 35.05)), ('D4', '5', 'VBUS', (11.1, 34.1)), ('D4', '6', 'USB_DM', (11.1, 33.15)),
    ('J2', '1', '3V3', (1.715, 42.03)), ('J2', '2', 'SWDIO', (2.985, 42.03)), ('J2', '3', 'NRST', (1.715, 43.3)),
    ('J2', '4', 'SWCLK', (2.985, 43.3)), ('J2', '5', 'GND', (1.715, 44.57)), ('J3', 'B7', 'USB_DM', (6.88, 33.55)),
    ('J3', 'A7', 'USB_DM', (6.88, 34.55)), ('J3', 'B6', 'USB_DP', (6.88, 35.05)),
    ('J3', 'A6', 'USB_DP', (6.88, 34.05)), ('J3', 'A5', 'CC1', (6.88, 33.05)), ('J3', 'B5', 'CC2', (6.88, 36.05)),
    ('J3', 'A4B9', 'VBUS', (6.88, 31.9)), ('J3', 'B4A9', 'VBUS', (6.88, 36.7)), ('R7', '1', 'CC1', (9.0, 32.83)),
    ('R8', '1', 'CC2', (9.0, 36.43)), ('R9', '1', 'VBUS', (9.95, 32.83)), ('R9', '2', 'VBUS_SENSE', (9.95, 31.97)),
    ('R85', '1', 'USB_ILIM', (15.6, 31.0)), ('R90', '1', '3V3', (15.125, 34.8)),
    ('R90', '2', 'USB_FAULT_N', (13.475, 34.8)), ('R110', '1', 'VBUS_SENSE', (18.975, 34.4)),
    ('TP86', '1', 'USB_FAULT_N', (13.6, 25.9)), ('TP92', '1', 'VBUS_SENSE', (21.6, 32.0)),
    ('U1', '14', 'NRST', u1_pin(14)), ('U1', '65', 'VBUS_SENSE', u1_pin(65)), ('U1', '70', 'USB_DM', u1_pin(70)),
    ('U1', '71', 'USB_DP', u1_pin(71)), ('U1', '72', 'SWDIO', u1_pin(72)), ('U1', '76', 'SWCLK', u1_pin(76)),
    ('U1', '87', 'USB_FAULT_N', u1_pin(87)), ('U10', '1', 'VBUS', (11.3, 31.95)), ('U10', '3', 'VBUS', (11.3, 30.05)),
    ('U10', '4', 'USB_FAULT_N', (13.9, 30.05)), ('U10', '5', 'USB_ILIM', (13.9, 31.0)),
]


def draw(d):
    for net, layer, w, pts in TRACKS:
        d.track(net, layer, w, pts)
    for at in (V_A, V_B, V_D):
        d.via('VBUS', at, VIA_PWR)
    for net, at in SIGNAL_VIAS:
        d.via(net, at, VIA_SIG)
    for at in V3.values():
        d.via('3V3', at, VIA_SIG)
    for at in PENDING:
        d.via('GND', at, VIA_SIG)
