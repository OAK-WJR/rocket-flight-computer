"""R9 step 7 family power_ctl: the battery eFuse U9's enable, fault and current-limit lanes, the source mux U11's status
lane, the USB current-limited rail from U10 to U11 and the control pins' GND straps (r9_route.py; R9_DECISIONS D-S7-16).

Parts re-placed (r9_place.tsv, D-S7-16): C86 / TP82 onto the USB_LIMITED trunk, R85 on U10.5's line and R90 0.3 mm
west (usb_swd's tables follow), R89 / R91 in the pin-28..31 box's exit band and C90 out of it, C81 / R84 so that U9.8's
GND via fits between the DVDT and ILIM lanes, TP84 onto BAT_ENABLE's forward-edge lane, and the east test-pad column's
slots reassigned (TP87 south, TP83 / TP85 / TP89 north of the VLOGIC column) so that each lane reaches its pad without a
crossing. Step-6 table edits (r9_power.py): C97 0.7 mm east, R92.2 on its own GND via, TP83's VLOGIC tap moved with
TP83, and the RAW_ACT B.Cu pour's south step raised to y 61.45 so that the corridor's three lanes pass under it.
  USB_LIMITED  0.3 mm, power class, two vias. B.Cu from U10.6 through C86.1 north between R90 and VBUS_SENSE's via,
               45 degrees through TP82 under U1's aft row to a via; F.Cu through U1's interior (NE diagonal between
               NRST's and QSPI_IO3's, north on x 23.1 between the interior vias, out at the NE corner between U1.25 and
               U1.26) to a via in the pin-28..31 box; B.Cu along the box's exit band (north lane), up the corridor west
               of OE and the camera parts (one 45-degree jog past OE's via), east in the slot between C92 and the
               RAW_ACT pour, north and 45 degrees onto y 63.2 south of C98 (a T up into R87.1), east and north into
               C98.1, then 45 degrees into U11.7 (the mux's IN2) from the south: C98 sits beside U11.7 / U11.6 (TI
               SLVSEA3F section 11; R9P1-POWER-01, D-F1-05), C98.1 1.94 mm of track from U11.7 (it was 5.29 mm)
  LOGIC_SOURCE_ST  U1.29 by a box via west of BAT_FAULT_N's (the two cross there, on F.Cu), the band's middle lane
               through R91's T, the corridor's middle lane, east and 45 degrees round the (42, 59.5) support's
               north-west into U11.9 from the south, a branch east to TP87's via south of the pad
  BAT_FAULT_N  U1.28 by a box via, the band's south lane through R89's T, the corridor's east lane, east and 45 degrees
               round the support, north on the east edge x 45.15 (the one B.Cu lane past the VLOGIC column; D-S8-08) with a T to
               TP85's via, round the north of U9's OVLO divider and down into U9.4 (FLT) between R82's pads
  BAT_ENABLE   R165.2 (under J1.4) by one via to F.Cu, north between J1.4 and J1.3, 45 degrees onto the forward edge
               north of the BAT_IN pour (y 100.4) through TP84, 45 degrees past the (42, 98) support and south on x 38.8
               into C87.1, a T east to a via inside BAT_FAULT_N's loop; B.Cu round R83's east to U9.1 (EN) and R81.1
  BAT_ILIM     U9.9 down beside U9.8's GND via, 45 degrees into R84.1, east of R84 and below the RAW_PROTECTED column's
               via, down and east to TP89's via
  3V3 / GND    R89.1 / R91.1 / C90.1 by one In2 via each; U9.8 and U11.3 / 4 / 6 strapped to GND vias (In2 GND)
None of these nets is a critical class but USB_LIMITED (power): its two vias are the interior hop's. U9 / U11's other
links (OVLO, DVDT, ILIM, SS) are the links stage's.
"""
from r9_route import W, VIA_SIG, VIA_PWR, u1_pin

NETS = ('USB_LIMITED', 'LOGIC_SOURCE_ST', 'BAT_FAULT_N', 'BAT_ENABLE', 'BAT_ILIM')
RAILS = ('GND', '3V3')
BUDGET = dict(length_mm=175.0, vias=7, critical_layer_changes=0, ratio=1.40)
W_U = 0.3                          # USB_LIMITED (R8 D42 used 0.4; 0.3 fits the corridor's three lanes, 0.45 A limit)

# vias
V_U1, V_UB = (18.25, 39.75), (26.05, 51.15)                       # USB_LIMITED: under U1's aft row, the box
V_LS, V_BF = (26.75, 49.0), (27.95, 49.9)                        # the pin-28..31 box: LOGIC_SOURCE_ST, BAT_FAULT_N
V_TP87, V_TP85, V_TP89 = (44.6, 66.2), (43.35, 80.8), (43.35, 83.4)
V_BE1, V_BE2 = (14.03, 91.25), (44.6, 93.0)                       # BAT_ENABLE: at R165, east of U9's OVLO divider
V3 = dict(R89=(29.05, 49.125), R91=(27.6, 51.125), C90=(2.725, 26.95))
G = dict(U9=(40.1, 88.4), U11S=(38.5, 65.2), U11N=(38.5, 68.35))

# lane rows / columns (B.Cu): the band (y), the corridor before / after its jog (x), the slot under the RAW_ACT pour (y)
Y_BF, Y_LS, Y_U = 49.9, 50.4, 51.9
X_U, X_LS, X_BF = 32.32, 32.72, 33.12
X_U2, X_LS2, X_BF2 = 33.07, 33.47, 33.87
J_U, J_LS, J_BF = 54.05, 53.85, 53.75     # the jogs' starts, staggered so the 45-degree runs keep their spacing
S_BF, S_LS, S_U = 59.97, 60.32, 60.72
X_E = 45.15                        # BAT_FAULT_N up the east edge (0.35 mm off BAT_ENABLE's x 44.6 column: no GND
                                   # finger between them, D-S8-08)
Y_N = 95.0                         # BAT_FAULT_N across U9's north
P_C98 = (40.05, 64.2)              # C98.1 (C98 beside U11.7 / U11.6, D-F1-05); the trunk runs south of C98 on Y_C98
X_C98, Y_C98 = P_C98[0], 63.2

TRACKS = [   # net, layer, width, polyline
    # USB_LIMITED
    ('USB_LIMITED', 'B', W_U, [(13.9, 31.95), (14.35, 32.4), (15.95, 32.4)]),                        # U10.6 -> C86.1
    ('USB_LIMITED', 'B', W_U, [(15.95, 32.4), (15.95, 34.45), (18.25, 36.75), V_U1]),                 # TP82
    ('USB_LIMITED', 'F', W_U, [V_U1, (23.1, 44.6), (23.1, 49.8), (24.45, 51.15), V_UB]),
    ('USB_LIMITED', 'B', W_U, [V_UB, (26.8, Y_U), (X_U, Y_U), (X_U, J_U), (X_U2, J_U + 0.75), (X_U2, S_U - 0.4),
                               (X_U2 + 0.4, S_U), (35.825, S_U), (36.225, S_U + 0.4), (36.225, 62.425), (37.0, Y_C98)]),
    ('USB_LIMITED', 'B', W_U, [(37.0, Y_C98), (X_C98, Y_C98), P_C98]),                                  # C98.1
    ('USB_LIMITED', 'B', W_U, [P_C98, (39.3, 64.95), (39.3, 65.825)]),                                  # U11.7
    ('USB_LIMITED', 'B', W_U, [(37.0, Y_C98), (37.0, 64.6)]),                                           # R87.1
    # LOGIC_SOURCE_ST
    ('LOGIC_SOURCE_ST', 'F', W, [u1_pin(29), V_LS]),
    ('LOGIC_SOURCE_ST', 'B', W, [V_LS, (26.75, Y_LS), (30.05, Y_LS), (X_LS, Y_LS), (X_LS, J_LS), (X_LS2, J_LS + 0.75),
                                 (X_LS2, S_LS - 0.25), (X_LS2 + 0.25, S_LS), (38.25, S_LS), (40.8, 62.87),
                                 (40.8, 64.75),
                                 (40.8, 65.75)]),                                                         # U11.9
    ('LOGIC_SOURCE_ST', 'B', W, [(30.05, Y_LS), (30.05, 51.125)]),                                      # R91.2
    ('LOGIC_SOURCE_ST', 'B', W, [(40.8, 64.75), (44.6, 64.75), V_TP87]),
    ('LOGIC_SOURCE_ST', 'F', W, [V_TP87, (44.6, 67.8)]),                                                # TP87
    # BAT_FAULT_N
    ('BAT_FAULT_N', 'F', W, [u1_pin(28), (27.55, 49.5), V_BF]),
    ('BAT_FAULT_N', 'B', W, [V_BF, (31.4, Y_BF), (X_BF, Y_BF), (X_BF, J_BF), (X_BF2, J_BF + 0.75), (X_BF2, S_BF),
                             (38.4, S_BF), (40.4, 61.97), (X_E, 61.97), (X_E, 80.8), (X_E, Y_N - 0.4), (X_E - 0.4, Y_N),
                             (40.0, Y_N), (39.6, Y_N - 0.4), (39.6, 91.3)]),                              # U9.4
    ('BAT_FAULT_N', 'B', W, [(31.4, Y_BF), (31.4, 49.125)]),                                            # R89.2
    ('BAT_FAULT_N', 'B', W, [(X_E, 80.8), V_TP85]),
    ('BAT_FAULT_N', 'F', W, [V_TP85, (44.6, 80.8)]),                                                    # TP85
    # BAT_ENABLE
    ('BAT_ENABLE', 'B', W, [(14.03, 90.2), V_BE1]),                                                     # R165.2
    ('BAT_ENABLE', 'F', W, [V_BE1, (14.03, 93.95), (20.48, 100.4), (35.0, 100.4), (36.4, 100.4), (38.8, 98.0),
                            (38.8, 93.5), (38.8, 92.4)]),                                                # TP84, C87.1
    ('BAT_ENABLE', 'F', W, [(38.8, 93.5), (44.1, 93.5), V_BE2]),
    ('BAT_ENABLE', 'B', W, [V_BE2, (44.6, 92.0), (41.0, 92.0), (41.0, 91.3)]),                          # U9.1
    ('BAT_ENABLE', 'B', W, [(44.6, 92.0), (44.6, 90.125), (43.7, 90.125)]),                            # R81.1
    # BAT_ILIM
    ('BAT_ILIM', 'B', W, [(40.6, 89.5), (40.6, 87.925), (41.1, 87.425), (41.86, 87.425), (41.86, 84.2),
                          (42.66, 83.4), V_TP89]),                                                        # U9.9, R84.1
    ('BAT_ILIM', 'F', W, [V_TP89, (44.6, 83.4)]),                                                       # TP89
    # 3V3: the pull-ups and C90
    ('3V3', 'B', W, [(29.75, 49.125), V3['R89']]),                                                       # R89.1
    ('3V3', 'B', W, [(28.4, 51.125), V3['R91']]),                                                       # R91.1
    ('3V3', 'B', W, [(2.725, 26.0), V3['C90']]),                                                        # C90.1
    # GND: U9.8, U11.6, U11.4 / U11.3
    ('GND', 'B', W, [(40.1, 89.5), G['U9']]),
    ('GND', 'B', W, [(38.5, 65.75), G['U11S']]),
    ('GND', 'B', W, [(38.5, 66.75), (38.5, 67.25), G['U11N']]),
]
SIGNAL_VIAS = [('LOGIC_SOURCE_ST', V_LS), ('LOGIC_SOURCE_ST', V_TP87), ('BAT_FAULT_N', V_BF), ('BAT_FAULT_N', V_TP85),
               ('BAT_ENABLE', V_BE1), ('BAT_ENABLE', V_BE2), ('BAT_ILIM', V_TP89)]
PADS = [
    ('U10', '6', 'USB_LIMITED', (13.9, 31.95)), ('C86', '1', 'USB_LIMITED', (15.95, 32.4)),
    ('TP82', '1', 'USB_LIMITED', (18.25, 36.75)), ('C98', '1', 'USB_LIMITED', P_C98),
    ('R87', '1', 'USB_LIMITED', (37.0, 64.6)), ('U11', '7', 'USB_LIMITED', (39.3, 65.825)),
    ('U1', '29', 'LOGIC_SOURCE_ST', u1_pin(29)), ('R91', '2', 'LOGIC_SOURCE_ST', (30.05, 51.125)),
    ('U11', '9', 'LOGIC_SOURCE_ST', (40.8, 65.75)), ('TP87', '1', 'LOGIC_SOURCE_ST', (44.6, 67.8)),
    ('U1', '28', 'BAT_FAULT_N', u1_pin(28)), ('R89', '2', 'BAT_FAULT_N', (31.4, 49.125)),
    ('TP85', '1', 'BAT_FAULT_N', (44.6, 80.8)), ('U9', '4', 'BAT_FAULT_N', (39.6, 91.3)),
    ('R165', '2', 'BAT_ENABLE', (14.03, 90.2)), ('TP84', '1', 'BAT_ENABLE', (35.0, 100.4)),
    ('C87', '1', 'BAT_ENABLE', (38.8, 92.4)), ('R81', '1', 'BAT_ENABLE', (43.7, 90.125)),
    ('U9', '1', 'BAT_ENABLE', (41.0, 91.3)),
    ('U9', '9', 'BAT_ILIM', (40.525, 89.5)), ('R84', '1', 'BAT_ILIM', (41.1, 87.425)),
    ('TP89', '1', 'BAT_ILIM', (44.6, 83.4)),
    ('R89', '1', '3V3', (29.75, 49.125)), ('R91', '1', '3V3', (28.4, 51.125)), ('C90', '1', '3V3', (2.725, 26.0)),
    ('U9', '8', 'GND', (40.075, 89.5)), ('U11', '6', 'GND', (38.5, 65.75)), ('U11', '4', 'GND', (38.5, 66.75)),
    ('U11', '3', 'GND', (38.5, 67.25)),
]


def draw(d):
    for net, layer, w, pts in TRACKS:
        d.track(net, layer, w, pts)
    d.via('USB_LIMITED', V_U1, VIA_PWR)
    d.via('USB_LIMITED', V_UB, VIA_PWR)
    for net, at in SIGNAL_VIAS:
        d.via(net, at, VIA_SIG)
    for at in V3.values():
        d.via('3V3', at, VIA_SIG)
    for at in G.values():
        d.via('GND', at, VIA_SIG)
