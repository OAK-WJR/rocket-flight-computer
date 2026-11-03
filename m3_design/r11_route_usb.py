"""R11 family `usb` (stage C2): USB-C J3, ESD D4, limiter U10, source selector U11's USB side, the D+ / D- pair, CC Rd,
VBUS, VBUS sense, U10's ILIM / FAULT and the USB_LIMITED run to U11 (r11_plan.md section 4; stageC2.md section 2).

Explicit tables only (D-R11-07). Coordinates are board mm (x east, y forward from the aft edge, KiCad's y). Placement
changes this family needed are D-R11-20 (U10 rotated, R85 / R90 into the strip between U10 and D4, C28 / C83 on F.Cu at
J3's VBUS pin, R87 / R88 beside U11).

Pair: D+ (U1.B10) and D- (U1.C10) leave the ball field east on F.Cu north of U3 (y 25.2 / 25.6, 0.2 mm, 0.4 mm pitch),
turn south east of U3 (x 36.2 / 35.8) and run to J3 on F.Cu. J3's two D+ pads (B6, A6) are joined on F.Cu by a loop
west of the pads; the D- pad inside the loop (A7) drops by a via and rejoins D- on In3; the other D- pad (B7) takes the
trunk. D4 (USBLC6, B.Cu) taps the pair by one via each, its two pins of a line bridged under its body. Every layer
change of D+ / D- has a GND via within 1.5 mm (AGENTS section 3).
"""

NETS = ('USB_DP', 'USB_DM', 'VBUS', 'CC1', 'CC2', 'VBUS_SENSE', 'USB_ILIM', 'USB_LIMITED', 'USB_OVLO')

SIG, USB, PWR = 0.1, 0.2, 0.3
SV = (0.4, 0.2)            # signal via
PV = (0.45, 0.25)          # power / GND via

# key vias (x, y)
V_DP, V_DM, V_A7 = (36.25, 28.6), (35.8, 30.75), (38.1, 29.75)
# GND partners: V_DM (0.57 mm), V_DP (0.91) / V_A7 (1.38). D-R11-31: G_D4 sits 0.165 mm clear of D4.2's pad end (was
# inside its mask / paste at x 35.15) as a 0.4 / 0.2 mm via, whose hole keeps 0.27 mm from V_DM's ring
G_D4, G_DP = (35.35, 30.4), (37.15, 28.75)
V_ILIM_G = (35.33, 28.6)                            # R85.2's GND via (V_DP partner, 0.92 mm)
VB1, VB2 = (38.3, 27.6), (38.0, 32.4)              # VBUS at J3.B4A9 / J3.A4B9, joined on In3 east of V_A7
V_CC1, V_CC2 = (38.27, 31.25), (38.27, 28.25)       # CC to B.Cu
V_SENSE_U1 = (27.2, 28.0)                          # F9's dog-bone site (r11_fanout.tsv)


def pair(d):
    t, p, v = d.track, d.pad, d.via
    # D+ : B10 east, south at x 36.2, east at y 29.25 to J3.B6; the loop to J3.A6 west of the pads
    t('USB_DP', 'F', USB, [p('U1', 'B10', net='USB_DP'), (35.9, 25.2), (36.25, 25.55), V_DP])
    t('USB_DP', 'F', USB, [V_DP, (36.9, 29.25), (37.45, 29.25)])
    t('USB_DP', 'F', USB, [(37.45, 29.25), p('J3', 'B6', net='USB_DP')])
    t('USB_DP', 'F', USB, [(37.45, 29.25), (37.45, 30.0), (37.7, 30.25), p('J3', 'A6', net='USB_DP')])
    v('USB_DP', V_DP)
    # D- : C10 north-east, east at y 25.6, south at x 35.8 to V_DM, east at y 30.75 to J3.B7
    t('USB_DM', 'F', USB, [p('U1', 'C10', net='USB_DM'), (28.0, 25.6), (35.4, 25.6), (35.8, 26.0), V_DM])
    t('USB_DM', 'F', USB, [V_DM, p('J3', 'B7', net='USB_DM')])
    v('USB_DM', V_DM)
    # J3.A7 (inside the D+ loop) by a via and In3 back to V_DM
    t('USB_DM', 'F', USB, [p('J3', 'A7', net='USB_DM'), V_A7])
    v('USB_DM', V_A7)
    t('USB_DM', 'In3', USB, [V_A7, (37.1, 30.75), V_DM])
    # D4 on B.Cu: one tap via per line, the two pins of each line bridged under the body
    t('USB_DP', 'B', USB, [V_DP, (36.25, 28.95), p('D4', '4', net='USB_DP')])
    t('USB_DP', 'B', USB, [p('D4', '3', net='USB_DP'), p('D4', '4', net='USB_DP')])
    t('USB_DM', 'B', USB, [p('D4', '1', net='USB_DM'), (35.8, 31.35), p('D4', '6', net='USB_DM')])
    t('USB_DM', 'B', USB, [V_DM, (35.8, 31.35)])
    # GND partners
    t('GND', 'B', PWR, [p('D4', '2', net='GND'), G_D4])
    v('GND', G_D4, SV)
    v('GND', G_DP, PV)


def limiter(d):
    t, p, v = d.track, d.pad, d.via
    # VBUS: J3.B4A9 to VB1, B.Cu north to U10.3 (EN), under U10's body to U10.1 (IN); U10.2's GND via north of it
    t('VBUS', 'F', 0.4, [p('J3', 'B4A9', net='VBUS'), VB1])
    v('VBUS', VB1, SV)
    t('VBUS', 'B', 0.4, [VB1, (38.3, 24.3), (37.8, 23.8), p('U10', '3', net='VBUS')])
    t('VBUS', 'B', PWR, [p('U10', '3', net='VBUS'), (35.85, 24.4), (35.45, 24.8), (34.35, 24.8), (33.95, 24.4),
                         p('U10', '1', net='VBUS')])
    t('GND', 'B', PWR, [p('U10', '2', net='GND'), (34.9, 22.85), (34.9, 22.25)])
    v('GND', (34.9, 22.85), PV)
    v('GND', (34.9, 22.25), SV)          # D-R11-29: U10.2's second GND barrel (SINGLE_OPEN_TAPS U10.2 / R7.2)
    # ILIM to R85 in the strip; R85.2's GND via
    t('USB_ILIM', 'B', 0.15, [p('U10', '5', net='USB_ILIM'), (34.9, 27.5), p('R85', '1', net='USB_ILIM')])
    t('GND', 'B', PWR, [p('R85', '2', net='GND'), V_ILIM_G])
    v('GND', V_ILIM_G, SV)
    t('GND', 'B', PWR, [p('R85', '2'), (35.33, 27.43)])
    v('GND', (35.33, 27.43), SV)         # D-R11-29: R85.2's second GND barrel
    # FAULT: U10.4 to R90.2 (pull-up) on B.Cu; the MCU side (U1.C6) is drawn by ESCAPE (stageC1b.md, D-R11-44)
    t('USB_FAULT_N', 'B', 0.15, [p('U10', '4', net='USB_FAULT_N'), (36.42, 26.97), p('R90', '2', net='USB_FAULT_N')])
    t('3V3', 'B', 0.2, [p('R90', '1', net='3V3'), (37.28, 27.47), (37.55, 27.2)])
    v('3V3', (37.55, 27.2), SV)
    # USB_LIMITED: U10.6 down the column west of D4 to C86 / C98, round the SWD vias to TP82, west on y 40.4 to U11
    t('USB_LIMITED', 'B', PWR, [p('U10', '6', net='USB_LIMITED'), (33.95, 26.95), (33.3, 27.6), (33.3, 32.6),
                                (34.225, 33.525), p('C86', '1', net='USB_LIMITED')])
    t('USB_LIMITED', 'B', PWR, [p('C86', '1', net='USB_LIMITED'), p('C98', '1', net='USB_LIMITED')])
    t('USB_LIMITED', 'B', PWR, [p('C98', '1', net='USB_LIMITED'), (34.225, 38.1), (33.625, 38.7), (29.0, 38.7),
                                (26.55, 41.15), p('TP82', '1', net='USB_LIMITED')])
    t('USB_LIMITED', 'B', PWR, [p('TP82', '1', net='USB_LIMITED'), (18.95, 41.15), (17.6, 39.8), (17.6, 35.83)])
    t('USB_LIMITED', 'B', PWR, [(17.6, 35.83), (17.6, 35.4), (17.15, 34.95), p('U11', '7', net='USB_LIMITED')])
    t('USB_LIMITED', 'B', PWR, [(17.6, 35.83), p('R87', '1', net='USB_LIMITED')])
    # U11's USB over-voltage divider beside U11.5
    t('USB_OVLO', 'B', 0.15, [p('R87', '2', net='USB_OVLO'), p('R88', '1', net='USB_OVLO')])
    t('USB_OVLO', 'B', 0.15, [p('R88', '1', net='USB_OVLO'), (17.85, 33.43), (16.35, 33.43), (16.05, 33.73),
                                    p('U11', '5', net='USB_OVLO')])
    t('GND', 'B', PWR, [p('R88', '2', net='GND'), (18.95, 32.47)])
    v('GND', (18.95, 32.47), PV)


def caps_sense(d):
    t, p, v = d.track, d.pad, d.via
    # C28 / C83 on F.Cu at J3.A4B9; GND to J3.A1B12 and a via
    t('VBUS', 'F', 0.4, [p('J3', 'A4B9', net='VBUS'), VB2, p('C28', '1', net='VBUS')])
    t('VBUS', 'F', PWR, [p('C28', '1', net='VBUS'), p('C83', '1', net='VBUS')])
    t('GND', 'F', PWR, [p('C83', '2', net='GND'), (36.56, 33.8), p('C28', '2', net='GND')])
    t('GND', 'F', 0.4, [p('C28', '2', net='GND'), (37.25, 34.5)])
    t('GND', 'F', PWR, [p('J3', 'A1B12', net='GND'), (38.52, 33.8), p('C28', '2', net='GND')])
    v('GND', (37.25, 34.5), PV)
    # VBUS to R9 (the sense divider top beside U1): F.Cu west south of U3, a via beside R9.1
    t('VBUS', 'F', 0.2, [p('C83', '1', net='VBUS'), (35.7, 32.4), (35.4, 32.7), (35.4, 35.3), (35.0, 35.7), (29.6, 35.7)])
    v('VBUS', (29.6, 35.7), SV)
    t('VBUS', 'B', 0.2, [(29.6, 35.7), p('R9', '1', net='VBUS')])
    # VBUS_SENSE: F9's dog-bone, B.Cu south at x 27.2 to R110.1; R9.2 to R110.1
    t('VBUS_SENSE', 'F', SIG, [p('U1', 'F9', net='VBUS_SENSE'), V_SENSE_U1])
    v('VBUS_SENSE', V_SENSE_U1, SV)
    t('VBUS_SENSE', 'B', 0.15, [V_SENSE_U1, (27.2, 34.53), (29.47, 36.8), p('R110', '1', net='VBUS_SENSE')])
    t('VBUS_SENSE', 'B', 0.15, [p('R9', '2', net='VBUS_SENSE'), (31.23, 35.94), p('R110', '1', net='VBUS_SENSE')])


def cc_vbus(d):
    t, p, v = d.track, d.pad, d.via
    # CC Rd: each CC pad by a via to B.Cu; CC1 south east of C28 / VB2 to R7, CC2 on B.Cu under J3 (east of its
    # shell pins and holes) to R8; R7 / R8 GND pads joined to one via south of them (clear of LS120's dummy pad)
    t('CC1', 'F', 0.15, [p('J3', 'A5', net='CC1'), V_CC1])
    v('CC1', V_CC1, SV)
    t('CC1', 'B', 0.15, [V_CC1, (38.45, 31.43), (38.45, 36.12), p('R7', '1', net='CC1')])
    t('CC2', 'F', 0.15, [p('J3', 'B5', net='CC2'), V_CC2])
    v('CC2', V_CC2, SV)
    t('CC2', 'B', 0.15, [V_CC2, (40.92, 30.9), (40.92, 34.75), p('R8', '1', net='CC2')])
    t('GND', 'B', PWR, [p('R7', '2', net='GND'), (37.55, 38.43)])
    t('GND', 'B', PWR, [(37.55, 38.43), p('R8', '2', net='GND')])
    t('GND', 'B', PWR, [(37.55, 38.43), (37.55, 39.1)])
    v('GND', (37.55, 39.1), PV)
    t('GND', 'B', PWR, [p('R7', '2'), (37.0, 39.08)])
    v('GND', (37.0, 39.08), SV)          # D-R11-29: the R7.2 / R8.2 island's second GND barrel
    # D4.5 (VBUS) by its own via to C28.1; J3's two VBUS pins joined on In3 east of V_A7 and the CC vias
    t('VBUS', 'B', PWR, [p('D4', '5', net='VBUS'), (37.4, 30.4), (37.65, 30.65), (37.65, 32.05), VB2])
    v('VBUS', VB2, PV)
    t('VBUS', 'In3', 0.2, [VB1, (38.6, 27.6), (38.9, 27.9), (38.9, 31.5), VB2])
    # GND vias of the USB support parts
    t('GND', 'B', PWR, [p('C86', '2', net='GND'), p('C98', '2', net='GND')])
    t('GND', 'B', PWR, [p('C86', '2', net='GND'), (36.5, 33.275)])
    v('GND', (36.5, 33.275), PV)
    t('GND', 'B', 0.2, [p('R110', '2', net='GND'), (31.23, 37.27), (31.0, 37.5)])
    v('GND', (31.0, 37.5), SV)


def draw(d):
    import r11_escape
    r11_escape.draw(d, 'usb')
    pair(d)
    limiter(d)
    caps_sense(d)
    cc_vbus(d)
