"""R11 family `pyro` (stage C2): the load switch Q120 / Q121 on RAW_ACT, its gate drive Q122 / R121 and local gate bias,
R134, the J121 wire pads, the fire FET Q124 with its full gate network, the high legs of the sense dividers and the cold
pull-up (r11_plan.md section 4; stageC2.md section 3; AGENTS section 2).

Explicit tables only (D-R11-07). Board mm (x east, y forward from the aft edge, KiCad's y). Placement changes this family
needed are D-R11-21 (Q120 rotated so its sources face Q121 across the gap; local gate-bias resistors R120 / R119 beside
each FET; Q122 / R121 / R122 / R123 / C123 south of PE4's lane; the Q124 gate network as a gate column and a GND column;
TP120 / TP122 moved clear of the MCU lanes; D120 rotated).

Fire path, all F.Cu, no series via (AGENTS section 2, R10 AUD-6 widths): J1.1 BAT_IN 1.0 mm to Q120's drain tab; ACT_FET_S
0.5 mm from Q120's sources (north row) through the gap between the FETs to Q121's sources (south row); RAW_ACT 0.5 mm from
Q121's drain tab to R134.2; PYRO1_IGN 0.5 mm R134.1 to J121.2; PYRO1_OUT 0.5 mm J121.1 to Q124's drain; Q124's sources by a
0.3 mm bar to two 0.6 / 0.3 mm GND vias (R10 FIRE_RETURN).

The gate islands: Q120.4 with R120 (its own 100 k to its sources) and C120 on F.Cu; Q121.4 with R119 on F.Cu; R121 (from
Q122's drain) south of PE4's lane. Q120's and Q121's islands each drop by one ACT_GATE barrel to a B.Cu trunk ending at R121 (on B.Cu); Q122's drain
reaches R121 by one ACT_DRV barrel (route_check r11 allows no parallel barrel, D-R11-22); every barrel keeps a 1.3 mm keep-out on In1..In4 (S-8: 1.0 mm from its inner ring;
ACT_GATE counts GND). J121's barrels keep 1.75 mm keep-outs (no inner rings since D-R11-28: the 0.65 mm barrel wall plus
1.0585 mm), on In2 / In3 for J121.2 (IGN, GND exempt) and on In1..In4 for J121.1 (PYRO1_OUT counts GND).
"""
import math

import pcbnew

NETS = ('ACT_FET_S', 'ACT_GATE', 'ACT_DRV', 'ACT_EN', 'ACT_EN_MCU', 'RAW_ACT', 'PYRO1_IGN', 'PYRO1_OUT', 'PYRO1_GATE', 'PYRO1_GATE_N', 'PYRO1_COLD', 'PYRO1_CONT_MID', 'PYRO1_CONT', 'ARM1_SENSE_MID')

FIRE, BAT, SIG, PWR = 0.5, 1.0, 0.15, 0.3
SV, PV, BV = (0.4, 0.2), (0.45, 0.25), (0.6, 0.3)

# ACT_GATE barrels: Q120's island (north line) and Q121's island; R121 sits on B.Cu at the trunk's end. ACT_DRV's barrel
VG_X, VG_B, VD = (14.6, 15.9), (13.95, 21.0), (15.4, 29.7)
# D-R11-29: each FET island's second ACT_GATE barrel, joined to the first on F.Cu and B.Cu (R10 D-R24-02)
VG_X2, VG_B2 = (14.6, 15.1), (13.95, 21.65)
BARRELS_GND = (VG_X, VG_B, VD, VG_X2, VG_B2)
G_COLD = (7.35, 24.0)                                  # GND partner of the COLD via (critical net, AGENTS section 3)
# Q124 fire return vias, the COLD and CONT_MID vias, local GND vias
V_RET1, V_RET2 = (6.925, 31.6), (8.225, 31.6)
V_COLD, V_CMID = (7.05, 24.97), (5.3, 22.87)
G_Q122, G_Q122B = (14.73, 31.2), (17.0, 29.3)


def keepout(board, centre, radius, layers, name):
    """A rule area (no tracks, no fills; vias allowed: the barrel itself sits inside) on the given inner layers."""
    z = pcbnew.ZONE(board)
    ls = pcbnew.LSET()
    for lay in layers:
        ls.AddLayer(lay)
    z.SetLayerSet(ls)
    z.SetIsRuleArea(True)
    z.SetDoNotAllowTracks(True)
    z.SetDoNotAllowZoneFills(True)
    z.SetDoNotAllowVias(False)
    z.SetDoNotAllowPads(False)
    z.SetDoNotAllowFootprints(False)
    z.SetZoneName(name)
    ol = z.Outline()
    ol.NewOutline()
    n = 16
    r = radius / math.cos(math.pi / n)                 # circumscribed: the polygon contains the circle
    for k in range(n):
        a = 2 * math.pi * (k + 0.5) / n
        ol.Append(pcbnew.FromMM(centre[0] + r * math.cos(a)), pcbnew.FromMM(centre[1] + r * math.sin(a)))
    board.Add(z)


INNER = (pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.In3_Cu, pcbnew.In4_Cu)
# D-R11-28: J121's pads keep no inner ring (remove_unused_layers, R10 D-R20-05), so the keep-out is measured from the
# 1.30 mm barrel wall: 0.65 + 1.0585 (D-R26-04's gate-net spacing, which also covers S-8's 1.0 mm) = 1.7085, held at 1.75
J121_KEEPOUT = 1.75


def fire(d):
    t, p, v = d.track, d.pad, d.via
    # BAT_IN: J1.1 to Q120's drain (west tab), 1.0 mm (S-9 BAT_IN floor); the rest of BAT_IN is the power family's
    t('BAT_IN', 'F', BAT, [p('J1', '1', net='BAT_IN'), (4.6, 16.6), (4.6, 18.6), (5.6, 19.6), (6.7, 19.6)])
    # ACT_FET_S: Q120's sources (north row) along the row, through the gap, Q121's sources (south row)
    t('ACT_FET_S', 'F', FIRE, [p('Q120', '3', net='ACT_FET_S'), p('Q120', '2'), p('Q120', '1'), (9.6, 18.2)])
    t('ACT_FET_S', 'F', FIRE, [(9.6, 18.2), (10.15, 18.75), (10.15, 20.45), (10.7, 21.0), p('Q121', '1', net='ACT_FET_S'),
                               p('Q121', '2'), p('Q121', '3')])
    t('ACT_FET_S', 'F', PWR, [(9.6, 18.2), (10.925, 16.875)])                          # C120.1
    t('ACT_FET_S', 'F', PWR, [p('Q120', '3'), (7.675, 17.2)])                          # R120.1 (Q120's own bias)
    t('ACT_FET_S', 'F', PWR, [p('Q121', '3'), (12.625, 21.8)])                         # R119.2 (Q121's own bias)
    # RAW_ACT: Q121's drain tab east, south to R134.2; R132 (bus-sense top) and TP120 taps
    t('RAW_ACT', 'F', FIRE, [p('Q121', '9', net='RAW_ACT'), (14.2, 19.6), (14.65, 20.05), (14.65, 22.03)])
    t('RAW_ACT', 'F', FIRE, [(14.65, 22.03), (14.65, 24.1)])
    t('RAW_ACT', 'F', PWR, [(14.65, 22.03), p('R132', '1', net='RAW_ACT')])
    t('RAW_ACT', 'F', FIRE, [(14.65, 24.1), p('TP120', '1', net='RAW_ACT')])
    # PYRO1_IGN: R134.1 to J121.2
    t('PYRO1_IGN', 'F', FIRE, [(8.3, 23.1), (7.05, 21.85), (3.25, 21.85), p('J121', '2', net='PYRO1_IGN')])
    # PYRO1_OUT: J121.1 to a trunk feeding R173.1 / R131.1 and Q124's drain; C128.1 from the drain's west side
    t('PYRO1_OUT', 'F', FIRE, [p('J121', '1', net='PYRO1_OUT'), (4.3, 24.7)])
    t('PYRO1_OUT', 'F', FIRE, [(4.3, 24.7), (4.3, 24.13), (4.7, 23.73), p('R173', '1', net='PYRO1_OUT')])
    t('PYRO1_OUT', 'F', FIRE, [(4.3, 24.7), (4.3, 25.83)])
    t('PYRO1_OUT', 'F', FIRE, [(4.3, 25.83), p('R131', '1', net='PYRO1_OUT')])
    t('PYRO1_OUT', 'F', FIRE, [(4.3, 25.83), (4.3, 26.6), (7.0, 29.3), p('Q124', '5', net='PYRO1_OUT')])
    t('PYRO1_OUT', 'F', PWR, [(7.0, 29.3), (6.3, 30.0), (6.3, 31.975), p('C128', '1', net='PYRO1_OUT')])
    # Q124's sources: a 0.3 mm bar and two 0.6 / 0.3 mm GND vias; C128.2 to the east one
    t('GND', 'F', PWR, [p('Q124', '1', net='GND'), p('Q124', '2'), p('Q124', '3')])
    t('GND', 'F', PWR, [p('Q124', '1'), V_RET1])
    t('GND', 'F', PWR, [p('Q124', '3'), V_RET2])
    t('GND', 'F', PWR, [p('C128', '2', net='GND'), (8.675, 32.05), V_RET2])
    v('GND', V_RET1, BV)
    v('GND', V_RET2, BV)


def gates(d):
    t, p, v = d.track, d.pad, d.via
    # Q120's island: Q120.4 to R120.2 (its bias), R120.2 to C120.2, the north line east to its two barrels
    t('ACT_GATE', 'F', PWR, [p('Q120', '4', net='ACT_GATE'), (7.025, 17.2)])
    t('ACT_GATE', 'F', 0.2, [p('R120', '2', net='ACT_GATE'), (6.92, 16.73), (7.2, 16.45), (8.5, 16.45)])
    t('ACT_GATE', 'F', 0.2, [(8.5, 16.45), (9.025, 16.45), p('C120', '2', net='ACT_GATE')])
    t('ACT_GATE', 'F', 0.2, [(8.5, 16.45), (8.5, 16.2), (8.8, 15.9), VG_X])
    # Q121's island: Q121.4 to R119.1 (its bias) and to its barrel east of it
    t('ACT_GATE', 'F', PWR, [p('Q121', '4', net='ACT_GATE'), (13.275, 21.8)])
    t('ACT_GATE', 'F', PWR, [p('Q121', '4'), VG_B])
    v('ACT_GATE', VG_X, SV)
    v('ACT_GATE', VG_B, SV)
    v('ACT_GATE', VG_X2, SV)
    v('ACT_GATE', VG_B2, SV)
    t('ACT_GATE', 'F', PWR, [VG_X, VG_X2])
    t('ACT_GATE', 'B', PWR, [VG_X2, VG_X])
    t('ACT_GATE', 'F', 0.2, [VG_B, VG_B2])
    t('ACT_GATE', 'B', PWR, [VG_B2, (13.6, 21.65)])
    # B.Cu trunk: Q120's barrel, Q121's barrel, south west of the crystal to R121.1 (B.Cu)
    t('ACT_GATE', 'B', PWR, [VG_X, (14.6, 20.35), VG_B, (13.6, 21.35), (13.6, 21.65), (13.6, 28.77), (14.0, 29.17),
                             p('R121', '1', net='ACT_GATE')])
    # Q122: PC1 lane (F2) to R122, ACT_EN to Q122's gate and its pull-down R123 / 10 nF C123, ACT_DRV to R121
    t('ACT_EN_MCU', 'F', 0.1, [p('U1', 'F2', net='ACT_EN_MCU'), (20.8, 28.0), p('R122', '1', net='ACT_EN_MCU')])
    t('ACT_EN', 'F', SIG, [p('R122', '2', net='ACT_EN'), (17.57, 28.4)])
    t('ACT_EN', 'F', SIG, [(17.57, 28.4), (17.57, 29.85), (17.87, 30.15), p('Q122', '1', net='ACT_EN')])
    t('ACT_EN', 'F', SIG, [(17.57, 28.4), (14.27, 28.4), (13.87, 28.8), p('R123', '1', net='ACT_EN')])
    t('ACT_EN', 'F', SIG, [p('R123', '1'), (13.87, 30.0)])
    t('ACT_DRV', 'F', PWR, [p('Q122', '3', net='ACT_DRV'), (16.6, 31.2), (15.85, 31.2), (15.4, 30.75), VD])
    v('ACT_DRV', VD, SV)
    t('ACT_DRV', 'B', PWR, [VD, (15.07, 30.03), p('R121', '2', net='ACT_DRV')])
    t('GND', 'F', PWR, [p('Q122', '2', net='GND'), (16.6, 29.7), G_Q122B])
    v('GND', G_Q122B, PV)
    t('GND', 'F', PWR, [p('R123', '2', net='GND'), p('C123', '2', net='GND'), G_Q122])
    v('GND', G_Q122, PV)
    # Q124's gate network: PE4 lane (C3) west at y 26.4 / 27.3 to R126.1 and R127.1; gate column x 10.97 (R126.2,
    # R128.1, C126.1, TP122) with Q124.4 on its own branch; GND column to one via
    # D-R11-23 (corrected): the lane hugs C2 (GND) at the 0.1 mm floor, so D2 (3V3) gets the rest of the 0.8 mm row gap
    t('PYRO1_GATE_N', 'F', 0.1, [p('U1', 'C3', net='PYRO1_GATE_N'), (21.65, 26.35), (16.55, 26.35), (15.6, 27.3),
                                 (12.9, 27.3)])
    t('PYRO1_GATE_N', 'F', 0.15, [(12.9, 27.3), (12.53, 27.3), p('R126', '1', net='PYRO1_GATE_N')])
    t('PYRO1_GATE_N', 'F', 0.15, [(12.9, 27.3), p('R127', '1', net='PYRO1_GATE_N')])
    t('PYRO1_GATE', 'F', PWR, [p('R126', '2', net='PYRO1_GATE'), p('R128', '1'), p('C126', '1'), (10.97, 31.2),
                               p('TP122', '1', net='PYRO1_GATE')])
    t('PYRO1_GATE', 'F', PWR, [(10.97, 31.2), (9.375, 31.2), p('Q124', '4', net='PYRO1_GATE')])
    # its GND column (R127.2, R128.2, C126.2) east, south of C123, to the via of Q122's pull-downs (G_Q122)
    t('GND', 'F', PWR, [p('R128', '2', net='GND'), (12.9, 29.1)])
    t('GND', 'F', PWR, [p('R127', '2', net='GND'), (12.9, 29.1), (12.9, 30.3), (12.9, 30.6), (13.5, 31.2), G_Q122])
    t('GND', 'F', PWR, [p('C126', '2', net='GND'), (12.9, 30.3)])


def sense(d):
    t, p, v = d.track, d.pad, d.via
    # cold pull-up: R131.2 by a via to D120.1 (B.Cu); D120.3's 3V3 is the power family's (a B.Cu run to R164.1, D-R11-27)
    t('PYRO1_COLD', 'F', SIG, [p('R131', '2', net='PYRO1_COLD'), V_COLD])
    v('PYRO1_COLD', V_COLD, SV)
    t('PYRO1_COLD', 'B', SIG, [V_COLD, (7.9, 25.82), (9.12, 25.82), (9.95, 26.65), p('D120', '1', net='PYRO1_COLD')])
    v('GND', G_COLD, PV)
    # continuity divider middle: R173.2 by a via to R129.1 (B.Cu), west of the bus-sense bank
    t('PYRO1_CONT_MID', 'F', SIG, [p('R173', '2', net='PYRO1_CONT_MID'), V_CMID])
    v('PYRO1_CONT_MID', V_CMID, SV)
    t('PYRO1_CONT_MID', 'B', SIG, [V_CMID, (5.3, 21.13), p('R129', '1', net='PYRO1_CONT_MID')])


# Stage C2c (O-C2-1, D-R11-35): the sense lines. PYRO1_CONT leaves U1.F1 by the west site (20.0, 28.8), runs north on
# B.Cu in the via-free lane x 20.4 under ball column 1, crosses the crystal's north side to (16.9, 21.9), hops on In3
# under the ACT_GATE B.Cu trunk (the In3 corridor between the ACT_GATE keep-outs) and reaches the continuity bank's row
# on B.Cu. ARM1_SENSE_MID: R132.2 by one via to In3, west along y 18.57 and diagonally over the banks to a via south of
# R175 (B.Cu). ARM1_SENSE's own MCU run (U1.H4) is not drawn: stageC3.md O-C3-1; only its bank row is.
V_CONT = ((20.0, 28.8), (16.9, 21.9), (14.0, 19.0))
V_MID = ((15.6, 20.02), (6.95, 23.47))
SENSE_TRACKS = (
    ('PYRO1_CONT', 'F', [('U1', 'F1'), (20.0, 28.8)]),
    ('PYRO1_CONT', 'B', [(20.0, 28.8), (20.4, 28.4), (20.4, 25.4), (16.9, 21.9)]),
    ('PYRO1_CONT', 'In3', [(16.9, 21.9), (14.0, 19.0)]),
    ('PYRO1_CONT', 'B', [(14.0, 19.0), (12.7, 20.3), (9.7, 20.3)]),
    ('PYRO1_CONT', 'B', [(9.45, 20.43), ('R178', '1'), ('R130', '1'), (6.86, 20.43), ('R129', '2')]),
    ('ARM1_SENSE', 'B', [(9.45, 22.83), ('R180', '1'), ('R133', '1'), (6.86, 22.83), ('R175', '2')]),
    ('ARM1_SENSE_MID', 'F', [('R132', '2'), (15.6, 20.02)]),
    ('ARM1_SENSE_MID', 'In3', [(15.6, 20.02), (14.15, 18.57), (11.85, 18.57), (6.95, 23.47)]),
    ('ARM1_SENSE_MID', 'B', [(6.95, 23.47), (6.25, 22.77)]),                 # ends inside R175.1
)


def sense_c2(d):
    for net, layer, pts in SENSE_TRACKS:
        d.track(net, layer, 0.1, [d.pad(*p, net=net) if isinstance(p[0], str) else p for p in pts])
    for at in V_CONT:
        d.via('PYRO1_CONT', at, SV)
    for at in V_MID:
        d.via('ARM1_SENSE_MID', at, SV)


def keepouts(d):
    for k, at in enumerate(BARRELS_GND):
        # 1.0 mm from the 0.4 mm ring (0.2 + 1.0) plus margin; VG_B2 at 1.25 so In3 I2C1_SDA (y 23.0) stays outside
        keepout(d.board, at, 1.25 if at == VG_B2 else 1.3, INNER, f'S8_ACT_GATE_{k}')
    j121 = d.board.FindFootprintByReference('J121')
    for pad in j121.Pads():
        c = pad.GetPosition()
        at = (pcbnew.ToMM(c.x), pcbnew.ToMM(c.y))
        lays = INNER if pad.GetNetname() == 'PYRO1_OUT' else (pcbnew.In2_Cu, pcbnew.In3_Cu)
        keepout(d.board, at, J121_KEEPOUT, lays, f'S8_J121_{pad.GetNumber()}')


def draw(d):
    import r11_escape
    r11_escape.draw(d, 'pyro')
    fire(d)
    gates(d)
    sense(d)
    sense_c2(d)
    if not d.dry:
        keepouts(d)
