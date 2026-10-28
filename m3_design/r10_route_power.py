"""R10 power copper: the inner planes and the hand-routed supply nets (AGENTS 3), explicit pad-referenced polylines.

In1 is solid GND. In2 is split by rail (R10_DECISIONS D-R2-03, D-R2-05, D-R2-06): RAW_PROTECTED wraps the board (the
forward area, an east strip and an aft band that reaches the 5.3 V buck's input), PORT_5V3 is a band aft of U410
(y 4.7-6.8) and a column x 35.2-39.7 from the buck output to the camera switch (y <= 42.5), PORT_4V8 the LDO output
block x 28.3-32.4 with U410's cell, and 3V3 is the rest: a strip x 32.7-34.9 under the port buffers, the area east of
U1 forward of the camera switch, and a forward finger for the 3V3 buck's output, D120 and the servo clamp. Each port
control net's B.Cu run lies wholly over one region (D-R3-xx, below).
Two In2 GND zones take priority over the rail regions (R10_DECISIONS D-R3-01, D-R3-05): IN2_GND_CH1 under the whole CH1
column (J121, J124, R134, Q124 and its gate network, TP122 and their pyro copper), so that no rail plane lies near a
pyro barrel; and IN2_GND_Y1, R9's crystal plane (R9_DECISIONS D-S8-20) translated by CORE_SHIFT, with R9's In2 track
keep-out over it.
The outer GND pours are drawn by the ground family. Zones are filled at the end of the build.
"""
import pcbnew

FULL = pcbnew.ZONE_CONNECTION_FULL
BAT, W = 1.0, 0.4                      # battery / rail width; ordinary supply branch width
PAD_W = 0.3                            # U9's IN / OUT bars entered at their full 0.3 mm width (D-R3-02)

IN1_GND = [(0.3, 0.3), (45.7, 0.3), (45.7, 89.7), (0.3, 89.7)]
# D-R3-xx (K-reference on the port control nets, R3-RTE-01): every B.Cu run of a *_PWR_EN / *_FAULT_N / *_UART_OE
# net lies wholly over one In2 region (outside its own vias' antipads), the regions 0.3 mm apart:
# - GPS: PORT_4V8 takes U410's whole cell (its north pin row, R411.1 and both control runs, x 28.3-33.6 from y 7.1),
#   so the PORT_5V3 band moves aft of it to y 4.7-6.8 (RAW_PROTECTED's aft band then ends at y 4.4 east of x 24.2):
#   1.5 mm at its narrowest, beside R411.2's GND via (30.3, 6.6); the 3V3 strip starts at y 9.9. A notch (x 27.85 /
#   28.15, y 8.7-10.5) keeps PORT_4V8 under GPS_PWR_EN's 45 deg run off its via (28.1, 9.8).
# - Radio: PORT_4V8 reaches x 32.75 at y 24.4-26.0 (the 3V3 strip x 33.05 there) under RADIO_FAULT_N's run to U420.4.
# - Camera: PORT_5V3 reaches west of the column under CAM_FAULT_N's run (x >= 34.2, y 36.35-39.44) and CAM_PWR_EN's
#   (R431 and its run from the via (33.15, 41.5): x >= 33.1 below the 45 deg edge x + y = 73.64, which keeps 3V3 under
#   CAM_MCU_RX's B.Cu hop (33.65, 39.2)-(32.5, 40.35)-(32.5, 43.7), >= 0.15 mm beyond its copper edges).
IN2_RAW = [(0.3, 0.3), (45.7, 0.3), (45.7, 89.7), (0.3, 89.7), (0.3, 58.0), (17.5, 58.0), (17.5, 62.0), (21.8, 62.0),
           (21.8, 76.0), (32.0, 76.0), (32.0, 58.0), (40.0, 58.0), (40.0, 4.4), (24.2, 4.4), (24.2, 7.0), (18.0, 7.0),
           (18.0, 10.5), (9.0, 10.5), (9.0, 7.0), (0.3, 7.0)]
IN2_PORT = [(24.5, 4.7), (39.7, 4.7), (39.7, 42.5), (33.1, 42.5), (33.1, 40.64), (33.95, 39.79), (33.95, 38.4), (34.2, 38.4),
            (34.2, 36.35), (35.2, 36.35), (35.2, 9.6), (33.9, 9.6), (33.9, 6.55), (28.0, 6.55), (28.0, 8.7), (27.85, 8.7), (27.85, 10.5),
            (28.0, 10.5), (28.0, 15.5), (24.5, 15.5)]
IN2_4V8 = [(28.3, 6.85), (33.6, 6.85), (33.6, 9.6), (32.4, 9.6), (32.4, 24.4), (33.05, 24.4), (33.05, 26.0), (32.4, 26.0),
           (32.4, 29.0), (28.3, 29.0), (28.3, 10.2), (28.15, 10.2), (28.15, 9.0), (28.3, 9.0)]
IN2_3V3 = [(0.3, 7.3), (8.7, 7.3), (8.7, 10.8), (18.3, 10.8), (18.3, 7.3), (24.2, 7.3), (24.2, 15.8), (28.0, 15.8),
           (28.0, 29.3), (32.7, 29.3), (32.7, 26.3), (33.35, 26.3), (33.35, 24.1), (32.7, 24.1), (32.7, 9.9),
           (34.9, 9.9), (34.9, 36.05), (33.9, 36.05), (33.9, 38.1), (33.65, 38.1), (33.65, 39.9), (32.8, 40.75), (32.8, 42.8), (39.7, 42.8),
           (39.7, 57.7), (31.7, 57.7), (31.7, 75.7), (22.1, 75.7), (22.1, 61.7), (17.8, 61.7), (17.8, 57.7), (0.3, 57.7)]
# D-R3-01: In2 GND under the CH1 column, priority over the rail regions. Every PYRO1_BUS / _IGN / _OUT / _GATE barrel
# and its outer copper lies >= 1.25 mm inside it (a rail fill keeps its 0.25 mm clearance beyond it), J124's inter-pad
# window included. One notch (x 8.65-9.75) keeps R13's 3V3 via (9.2, 52.98) on the 3V3 region, 1.41 mm from J121.1's
# barrel; a 3V3 tongue (y 56.85-57.75 from the east, x 17.45-18.75 down to y 59.15) reaches D120's 3V3 via (18.0, 58.6),
# which PYRO1_CONT, PYRO1_BUS and PYRO1_COLD enclose on B.Cu, its fill 0.79 mm from R132.1 (PYRO1_BUS, B.Cu); R164's 3V3
# via (19.05, 55.9) and C14's (20.2, 52.1) stay east of x 18.55; R122's RAW via sits south of y 68.4. West of x 16.3
# the zone reaches y 69.7, so RAW_PROTECTED also keeps >= 1.0 mm from J124.2's barrel and from under Q121's RAW_ACT
# drain pad (a RAW_PROTECTED - RAW_ACT defect would bypass the load switch).
IN2_GND_CH1 = [(0.3, 51.8), (8.65, 51.8), (8.65, 53.55), (9.75, 53.55), (9.75, 51.3), (18.55, 51.3), (18.55, 53.4),
               (18.0, 53.4), (18.0, 56.45), (19.85, 56.45), (19.85, 55.55), (20.4, 55.55), (21.4, 54.55), (22.5, 54.55),
               (22.5, 53.9), (25.7, 53.9), (25.7, 56.1), (21.5, 56.1), (21.5, 56.75), (20.3, 56.75), (19.85, 57.2), (17.45, 57.2), (17.45, 59.15),
               (18.75, 59.15), (18.75, 58.2), (25.2, 58.2), (25.2, 57.65), (28.6, 57.65), (28.6, 60.8), (24.2, 60.8),
               (24.2, 59.45), (21.8, 59.45), (21.8, 63.35), (25.8, 63.35), (25.8, 62.85), (28.6, 62.85), (28.6, 65.75),
               (23.4, 65.75), (23.4, 64.7), (21.8, 64.7), (21.8, 68.4), (16.3, 68.4), (16.3, 69.7),
               (12.3, 69.7), (12.3, 71.5), (10.5, 71.5), (10.5, 69.7), (0.3, 69.7)]
# R6 fix pass (R6-RTE-01): the three via-ending arms are widened round their vias so no In2 GND sliver is narrower than
# 0.5 mm (via antipad r 0.40): PYRO1_CONT's to x 22.5-25.7, y 53.9-56.1 (GND via (25.2, 55.0) inside), ARM1_SENSE's to
# x 25.2-28.6, y 57.65-60.8 (GND vias (24.8, 60.24), (26.8, 60.15), (28.2, 59.6) inside), RAW_ACT_SENSE's to x 25.8-28.6,
# y 62.85-65.75 (x 23.4-25.8: south edge only; GND vias (23.93, 64.86), (24.8, 65.49), (27.2, 65.4) inside).
# R5 fix pass (R5-RTE-01/-02/-06, In2 reference check with 0.1 mm margins; the pad and chain rules need whole pads and whole
# chains over one plane): the PYRO1_CONT strip is >= 1.05 mm wide (x 19.85-21.15 round C127.1, y 54.55-55.6 east of it, x 19.85-21.5 round the pad and the diagonal)
# and its south edge y 57.2 (the track at y 56.8 keeps 0.2 mm each side); two arms run east to x 27.9 (y 58.05-59.45,
# 63.35-64.7) so the ARM1_SENSE / RAW_ACT_SENSE divider pads R175 / R124 and their B.Cu runs to the via at x 27.2 lie wholly
# over In2 GND (a 0603 pair 0.29 mm apart cannot straddle two regions 0.3 mm apart); a bay (x 10.5-12.3, to y 71.5) puts
# Q121.4's gate pad over GND; C127.2's GND via moves east to (22.1, 57.55), out of the 3V3 corridor to D120's via.
# R4-RTE-01 (K-reference): the zone also covers the whole B.Cu run of PYRO1_CONT (R178.1 -> C127.1 -> its via, a strip
# hugging the run >= 0.3 mm each side), ARM1_SENSE_MID (to x 21.8) and RAW_ACT_SENSE_MID, so each lies wholly over In2
# GND; ARM1_SENSE and RAW_ACT_SENSE start over In2 3V3 (its edge x 22.1, the zone clearance 0.25 beyond GND's x 21.8);
# the 3V3 tongue's corridor to D120's via is y 57.25-57.95 (R128.2's GND via moved off it, r10_route_ground), and the
# zone's west edge steps back to x 18.0 at y 53.4-56.45 so R164.1's 3V3 via (19.05, 55.9) keeps a 3V3 path round the
# GND vias (19.42, 55.02) / (20.23, 55.07) to the 3V3 region north (x >= 18.25, 0.67 mm wide).
# D-R3-05: R9's Y1_In2_keepout (x 13.9-21.8, y 45.8-50.45) + CORE_SHIFT (5, -1.5), and R9_GND_In2_Y1's outline: the area
# less r9_ground.xtal_outline's one notch (NRST's B.Cu run (24.3, 49.1)-(25.33, 49.1) to C24.1, its box grown by
# 0.1 + 0.3 mm), the same rule re-run on R10's routed board (no other critical B.Cu track lies wholly outside within
# reach).
Y1_AREA = [(18.9, 44.3), (26.8, 44.3), (26.8, 48.95), (18.9, 48.95)]
IN2_GND_Y1 = [(20.6, 44.3), (26.8, 44.3), (26.8, 48.95), (25.73, 48.95), (25.73, 48.7), (23.9, 48.7), (23.9, 48.95),
              (18.9, 48.95), (18.9, 45.45), (20.6, 45.45)]


def keepout(d, name, pts):
    """An In2 track keep-out rule area (fills, vias and pads allowed), as R9's Y1_In2_keepout after its step 8."""
    z = pcbnew.ZONE(d.board)
    z.SetIsRuleArea(True)
    z.SetLayer(pcbnew.In2_Cu)
    z.SetZoneName(name)
    z.SetDoNotAllowTracks(True)
    z.SetDoNotAllowVias(False)
    z.SetDoNotAllowPads(False)
    z.SetDoNotAllowZoneFills(False)
    z.SetDoNotAllowFootprints(False)
    o = z.Outline()
    o.NewOutline()
    for x, y in pts:
        o.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
    if not d.dry:
        d.board.Add(z)


def planes(d):
    d.zone('R10_GND_In1', 'GND', 'In1', IN1_GND, 1, clr=0.25, conn=FULL)
    d.zone('R10_RAW_In2', 'RAW_PROTECTED', 'In2', IN2_RAW, 1, clr=0.25, conn=FULL)
    d.zone('R10_PORT_5V3_In2', 'PORT_5V3', 'In2', IN2_PORT, 1, clr=0.25, conn=FULL)
    d.zone('R10_PORT_4V8_In2', 'PORT_4V8', 'In2', IN2_4V8, 1, clr=0.25, conn=FULL)
    d.zone('R10_3V3_In2', '3V3', 'In2', IN2_3V3, 1, clr=0.25, conn=FULL)
    d.zone('R10_GND_In2_CH1', 'GND', 'In2', IN2_GND_CH1, 2, clr=0.25, conn=FULL)
    d.zone('R10_GND_In2_Y1', 'GND', 'In2', IN2_GND_Y1, 2, clr=0.25, conn=FULL)
    keepout(d, 'R10_Y1_In2_keepout', Y1_AREA)


def battery(d):
    t, p, via = d.track, d.pad, d.via
    # F.Cu: J1.1 -> one bar along y 77 -> the protection column (C95 / C89 / C96 / C80 on x 27.52), D8 tapped.
    t('BAT_IN', 'F', BAT, [p('J1.1'), (9.9, 77.0), (27.525, 77.0), p('C95.1')])
    t('BAT_IN', 'F', BAT, [p('C95.1'), p('C89.1')])
    t('BAT_IN', 'F', BAT, [p('C89.1'), p('C96.1')])
    t('BAT_IN', 'F', BAT, [p('C96.1'), p('C80.1')])
    t('BAT_IN', 'F', BAT, [p('D8.1'), (19.85, 77.0)])
    t('BAT_IN', 'F', W, [(13.8, 77.0), p('TP80.1')])
    # B.Cu: J1.1 -> Q120's drain pad; Q120.7 -> down the west side of the J122 tie hole -> under J122's GND row ->
    # U9's IN bar (south tip: the 1.0 mm run ends 0.6 mm short of the bar, 0.195 mm clear of the corner pads 1 / 10,
    # and the bar is entered at its full 0.3 mm width, D-R3-02), with R167 / R82 / C88 tapped.
    t('BAT_IN', 'B', BAT, [p('J1.1'), (10.6, 74.1), (12.0, 75.5)])
    t('BAT_IN', 'B', BAT, [p('Q120.7'), (12.87, 86.6), (17.35, 86.6), (36.725, 86.6), (38.75, 86.6), (38.75, 81.4)])
    via('BAT_IN', (17.35, 86.6))
    t('BAT_IN', 'F', W, [(17.35, 86.6), (16.625, 86.6)])                 # into R80.1's pad (R80's battery side)
    t('BAT_IN', 'B', W, [(36.725, 86.6), p('R82.1')])
    t('BAT_IN', 'B', PAD_W, [(38.75, 81.4), p('U9.5')])            # pad-entry neck: 0.6 mm to the bar's tip
    t('BAT_IN', 'B', W, [(29.825, 86.6), p('R167.1')])
    t('BAT_IN', 'B', W, [(38.75, 82.37), p('C88.1')])


def control(d):
    t, p, via = d.track, d.pad, d.via
    # Damper (C89 / C95 -> R166) on F.Cu, clear of J122's tie hole (30.8, 79) by >= 1.85 mm.
    t('BAT_DAMP', 'F', W, [p('C89.2'), p('C95.2')])
    t('BAT_DAMP', 'F', W, [p('C95.2'), p('R166.1')])               # one 45 deg run to R166 turned north-south (D-R2-12)
    # External switch J400 (GH 2-pin): SW_SOURCE to R80, SW_RETURN to R165 (7 uA contact current).
    t('BAT_SW_SOURCE', 'F', 0.2, [p('J400.1'), (9.875, 86.1), (14.775, 86.1), p('R80.2')])
    t('BAT_SW_RETURN', 'F', 0.2, [p('J400.2'), (12.075, 88.4), p('R165.1')])
    # BAT_ENABLE: R165 -> C87 -> TP84 -> R81 pull-down, then east on F.Cu below J122's GND row and down to U9.1.
    t('BAT_ENABLE', 'F', 0.2, [p('R165.2'), (17.225, 87.6), p('C87.1')])
    t('BAT_ENABLE', 'F', 0.2, [p('C87.1'), (19.1, 86.7), (22.1, 86.7), p('TP84.1')])
    t('BAT_ENABLE', 'F', 0.2, [p('TP84.1'), (24.8, 85.8), (28.175, 85.8), (37.3, 85.8), (37.7, 85.4)])
    t('BAT_ENABLE', 'F', 0.2, [(28.175, 85.8), p('R81.1')])
    via('BAT_ENABLE', (37.7, 85.4))
    t('BAT_ENABLE', 'B', 0.2, [(37.7, 85.4), (37.7, 80.7), p('U9.1', at=(38.1, 80.3))])


def efuse(d):
    t, p, via = d.track, d.pad, d.via
    rp = 'RAW_PROTECTED'
    # U9's OUT bar (north tip, entered at its full 0.3 mm width; the 1.0 mm run starts 0.6 mm from the bar, 0.195 mm
    # clear of the corner pads 4 / 7) -> through R92.1 (bleed) -> east along y 76.725 to four vias into In2 RAW, east of
    # C84's VLOGIC pad (top): the 1.0 mm run to the first, 0.4 mm links at 0.7 mm pitch to the others (a 1.0 mm link
    # would be a short segment), the last ring 1.1 mm from TP88's bare pad (K-retained 1.0 mm) (D-R3-02).
    t(rp, 'B', PAD_W, [p('U9.6'), (39.25, 77.8)])
    u9_out = ((40.3, 76.725), (41.0, 76.725), (41.7, 76.725), (42.4, 76.725))
    t(rp, 'B', BAT, [(39.25, 77.8), p('R92.1'), u9_out[0]])
    t(rp, 'B', W, list(u9_out))                                     # a node at each via (no via on a track body)
    for at in u9_out:
        via(rp, at)
    # U11's RAW input (bottom) and C97 (top, directly over it) share one via into In2 RAW.
    t(rp, 'B', 0.3, [p('U11.2'), (32.3, 63.0)])
    t(rp, 'F', 0.3, [p('C97.1'), (32.3, 63.0)])
    via(rp, (32.3, 63.0))
    # U9 control and timing pins.
    t('BAT_ILIM', 'B', 0.2, [p('U9.9'), p('R84.1')])
    t('BAT_ILIM', 'B', 0.2, [p('R84.1'), (41.275, 81.83)])          # TP89 on the top, clear of the support (D-R2-12)
    via('BAT_ILIM', (41.275, 81.83))
    t('BAT_ILIM', 'F', 0.2, [(41.275, 81.83), p('TP89.1')])
    t('BAT_DVDT', 'B', 0.2, [(39.9, 78.9), (40.7, 78.1), p('C81.1')])
    t('BAT_OVLO', 'B', 0.2, [p('U9.2'), p('R83.1')])
    t('BAT_OVLO', 'B', 0.2, [p('R83.1'), p('R82.2')])
    # The 5.3 V buck's input on the aft band: C400 to U400's two IN pins; C401 south of U400 spanning pin 3 (VIN,
    # straight down 2.5 mm) and pin 4 (GND, 2.5 mm up to pin 4's fan-out via), Diodes DS41326 p.15 layout item 4 /
    # Figure 25 (D-R3-04).
    # Two vias into In2 RAW on the C400.1 -> C401.1 run, 0.65 / 1.0 mm clear of the pads (D-R2-11).
    t(rp, 'F', W, [p('C400.1'), p('U400.2')])
    t(rp, 'F', W, [p('U400.2'), p('U400.3')])
    t(rp, 'F', W, [p('U400.3'), (15.8, 9.0)])                       # into C401.1 (centre x 15.85)
    t('GND', 'F', W, [p('C401.2', at=(18.85, 9.0)), (18.85, 6.5)])    # onto U400.4's fan-out via (r10_fanout.tsv)
    t(rp, 'F', W, [p('C400.1'), (14.1, 7.6), (14.1, 9.0), p('C401.1', at=(15.85, 9.0))])
    for at in ((14.1, 7.6), (14.1, 9.0)):
        via(rp, at)


def ports(d):
    t, p, via = d.track, d.pad, d.via
    # 5.3 V buck (top, aft band): SW node and bootstrap, feedback divider on y 1.8, output bar to C403 / C404, two vias
    # into In2 PORT_5V3 (Diodes DS41326 layout guidance: short SW loop, input caps at IN).
    t('PORT_SW', 'F', W, [p('U400.5'), p('C402.2')])
    t('PORT_SW', 'F', W, [p('C402.2'), p('L400.1')])
    t('PORT_BST', 'F', 0.25, [p('U400.6'), (18.6, 4.0), p('C402.1')])
    t('PORT_FB', 'F', 0.2, [p('U400.1'), p('R404.2')])
    t('PORT_FB', 'F', 0.2, [p('R404.2'), p('R401.1')])
    t('PORT_FB_TOP', 'F', 0.2, [p('R404.1'), p('R400.2')])
    t('PORT_5V3', 'F', 0.2, [p('R400.1'), (27.8, 1.8), (28.6, 2.6)])
    t('PORT_5V3', 'F', BAT, [p('L400.2'), (28.6, 5.55)])
    t('PORT_5V3', 'F', BAT, [p('C403.1'), (28.6, 5.55)])
    t('PORT_5V3', 'F', BAT, [(28.6, 5.55), p('C404.1')])
    t('PORT_5V3', 'F', W, [p('C404.1'), (27.6, 8.0), (26.8, 8.0)])
    for at in ((27.6, 8.0), (26.8, 8.0)):
        via('PORT_5V3', at)
    # 4.8 V LDO (bottom): IN from C405 and its own via, EN (pin 7) to the PORT_5V3 plane, SS to C408, OUT and FB
    # through vias to the top divider R402 / R403 and into In2 PORT_4V8.
    t('PORT_5V3', 'B', W, [p('C405.1'), (25.9, 8.6)])
    via('PORT_5V3', (25.9, 8.6))
    t('PORT_5V3', 'B', W, [p('C405.1'), (25.9, 12.6), p('U401.10')])
    t('PORT_5V3', 'B', 0.25, [p('U401.10'), p('U401.9')])
    t('PORT_5V3', 'B', 0.2, [p('U401.7'), (25.65, 14.1), (25.65, 14.9)])
    via('PORT_5V3', (25.65, 14.9))
    t('PORT_LDO_SS', 'B', 0.2, [p('U401.8'), p('C408.1')])
    t('PORT_4V8', 'B', 0.25, [p('U401.1'), p('U401.2')])
    t('PORT_4V8', 'B', W, [p('U401.1'), (29.75, 12.6)])
    t('PORT_LDO_FB', 'B', 0.2, [p('U401.3'), (29.75, 13.6)])
    via('PORT_4V8', (29.75, 12.6))
    t('PORT_4V8', 'B', W, [(29.75, 12.6), (31.6, 12.6)])        # into C406.1's pad
    via('PORT_LDO_FB', (29.75, 13.6))
    t('PORT_4V8', 'F', W, [(29.75, 12.6), p('R402.1')])
    t('PORT_LDO_FB', 'F', 0.2, [(29.75, 13.6), (32.225, 13.6)])
    t('PORT_LDO_FB', 'F', 0.2, [p('R402.2'), (32.225, 13.6), p('R403.1')])
    # PORT_4V8 taps: each pad on its own via into the In2 PORT_4V8 region.
    t('PORT_4V8', 'B', W, [p('U410.1'), (29.3, 10.95)])
    via('PORT_4V8', (29.3, 10.95))
    t('PORT_4V8', 'F', W, [(29.3, 10.95), (29.75, 10.5), p('C410.1')])
    for pad, at in (('C407.1', (31.7, 21.6)), ('R405.1', (29.0, 19.4)),
                    ('U420.1', (28.7, 27.35))):
        t('PORT_4V8', 'B', W, [p(pad), at])
        via('PORT_4V8', at)
    via('PORT_4V8', (31.0, 23.5))                 # south-east of C420, clear of the GPS UART pair (D-R2-07)
    t('PORT_4V8', 'F', W, [p('C420.1'), (30.225, 22.725), (31.0, 23.5)])
    # Port rails east to their cells (B.Cu), the GH connector pin through one via each.
    # Each port's connector pin 1 takes its rail through one via 0.3 mm aft of the pad (hole and ring clear of the pad's
    # mask and paste) on the cell's B.Cu spine at x 40.05, clear of the ESD return vias at x 39.4 (D-R2-11).
    t('GPS_4V8', 'B', W, [p('U410.6'), (40.05, 10.95)])
    t('GPS_4V8', 'B', W, [(40.05, 10.95), (41.4, 10.95)])
    t('GPS_4V8', 'B', W, [(40.05, 10.95), (40.05, 11.45), (40.05, 18.45), p('U412.1')])
    t('GPS_4V8', 'B', W, [(40.05, 18.45), (40.675, 19.075)])
    via('GPS_4V8', (40.05, 11.45))
    t('GPS_4V8', 'F', W, [(40.05, 11.45), (40.725, 12.125)])
    # RADIO_4V8 (D-R3-03, replacing R2's In2 leg, D-R2-07): U420.6 -> B.Cu east along y 27.35, south at x 37.25 between
    # U422's pads 5 and 1 into U422.1, whose spine at x 40.05 carries it on to C421 and J420.1's via; west of the RX
    # wire's B.Cu run and via (38.8, 24.1-28.9), so In2 carries no track in the radio cell and the PORT_5V3 column under
    # it is whole (2.4 mm single piece beside the C450 GND via).
    t('RADIO_4V8', 'B', W, [p('U420.6'), (37.25, 27.35), (37.25, 30.45), p('U422.1')])
    t('RADIO_4V8', 'B', W, [p('U422.1'), (40.05, 30.45), (40.05, 23.5), (40.05, 22.2), p('C421.1')])
    t('RADIO_4V8', 'B', W, [(40.05, 30.45), (40.675, 31.075)])
    via('RADIO_4V8', (40.05, 23.5))
    t('RADIO_4V8', 'F', W, [(40.05, 23.5), (40.675, 24.125)])
    t('CAM_5V', 'B', W, [p('U402.6'), p('U13.1')])
    t('CAM_5V', 'B', W, [p('U13.1'), (40.43, 42.45)])
    t('CAM_5V', 'B', W, [(40.43, 42.45), (40.43, 44.6)])          # through C91.1's pad
    via('CAM_5V', (40.43, 44.6))
    t('CAM_5V', 'F', 0.2, [(40.43, 44.6), p('R104.1')])
    # The camera's 1.0-1.25 A: CAM_5V has no pour, so a second via in parallel would be a track loop; its one layer
    # change is a 0.45 mm drill via (1.5 x a 0.3 mm via's barrel). U402.1's PORT_5V3 via moves 0.05 mm west, its hole
    # 0.15 mm from the pad's opening (R3-MFG-03) and 0.15 mm from CAM_UART_OE's F.Cu lead at x 34.95; R431.1, C93.2, U402.2 and U12's pins leave no spot for a second (D-R3-06).
    t('CAM_5V', 'B', W, [p('U402.6'), (42.9, 40.05), (42.9, 35.7), p('C431.1')])
    via('CAM_5V', (42.9, 35.7), size=(0.8, 0.45))                 # at the B.Cu corner, clear of R430's designator
    t('CAM_5V', 'F', W, [(42.9, 35.7), (42.475, 36.125), p('J9.1')])
    t('PORT_5V3', 'B', W, [p('U402.1'), (35.45, 40.05)])
    via('PORT_5V3', (35.45, 40.05))
    t('PORT_5V3', 'B', W, [(39.6, 41.25), (39.95, 40.9), p('C430.1')])
    via('PORT_5V3', (39.6, 41.25))
    # Each port buffer's 3V3 pin joins its decoupling capacitor, whose own via reaches the In2 3V3 strip (D-R2-06).
    t('3V3', 'F', 0.2, [p('U411.3'), (34.95, 12.9), (34.425, 12.375), p('C440.1')])
    t('3V3', 'F', 0.2, [p('U421.3'), (34.95, 25.35), (34.425, 24.825)])     # C442 (bottom) blocks a via west of C450
    t('3V3', 'F', 0.3, [p('C450.1'), (34.425, 24.825)])
    via('3V3', (34.425, 24.825))
    t('3V3', 'F', 0.2, [p('U12.3'), (34.95, 36.77), p('C100.1')])
    # Switch control (local): ILIM resistors, EN pull-downs.
    t('GPS_ILIM', 'B', 0.2, [p('U410.5'), p('R410.1')])
    t('RADIO_ILIM', 'B', 0.2, [p('U420.5'), p('R420.1')])
    t('CAM_ILIM', 'B', 0.2, [p('U402.5'), p('R430.1')])
    t('GPS_PWR_EN', 'B', 0.2, [p('R411.1'), p('U410.3')])
    t('RADIO_PWR_EN', 'B', 0.2, [p('R421.1'), p('U420.3')])


def logic(d):
    t, p, via = d.track, d.pad, d.via
    # U11 (source mux) -> VLOGIC: one B.Cu spine x 33.0 through U11's two OUT pads, C99 and U2's IN, east to C6, then a
    # spine at x 37.8 (C7, R60's sense tap, and a via up to C84 and TP83 on F.Cu).
    t('VLOGIC', 'B', W, [p('U11.8'), p('U11.1')])
    t('VLOGIC', 'B', W, [p('U11.1'), p('C99.1')])
    t('VLOGIC', 'B', W, [p('C99.1'), p('U2.2')])
    t('VLOGIC', 'B', W, [p('U2.2'), p('U2.3')])
    t('VLOGIC', 'B', W, [p('U2.3'), (35.75, 65.6), (37.8, 65.6)])
    t('VLOGIC', 'B', W, [(37.8, 65.6), p('R60.1')])
    t('VLOGIC', 'B', W, [(37.8, 65.6), (37.8, 67.0), (37.8, 69.8), p('C7.1')])
    t('VLOGIC', 'B', W, [(37.8, 69.8), (37.8, 75.15)])
    via('VLOGIC', (37.8, 75.15))                                    # 0.35 mm aft of C84.1's pad, not in it (D-R2-11)
    t('VLOGIC', 'F', W, [(37.8, 75.15), (37.8, 76.6)])
    t('VLOGIC', 'B', W, [(37.8, 67.0), p('TP83.1')])
    t('LOGIC_ILIM', 'B', 0.2, [p('U11.10'), p('R86.1')])
    t('LOGIC_SS', 'B', 0.2, [p('U11.11'), (34.15, 61.75), p('C85.1')])
    t('USB_OVLO', 'B', 0.2, [p('U11.5'), p('R87.2')])
    t('USB_OVLO', 'B', 0.2, [p('R87.2'), p('R88.1')])
    # 3V3 buck U2 (Diodes DS41326 Figure 25): SW node, bootstrap, the output into the In2 3V3 finger.
    t('SW_NODE', 'B', W, [p('U2.5'), p('L1.1')])
    t('SW_NODE', 'B', W, [(32.4, 69.5), (29.78, 69.5), p('C5.1')])
    t('BST', 'B', 0.25, [p('U2.6'), (31.05, 68.0), p('C5.2')])
    t('3V3', 'B', W, [p('U2.1'), (31.2, 65.6)])
    via('3V3', (31.2, 65.6))
    t('3V3', 'B', W, [(32.2, 74.0), (31.6, 74.6)])
    via('3V3', (31.6, 74.6))                                        # off L1.2's pad corner and paste (D-R2-11)
    t('3V3', 'B', W, [p('C8.1'), p('C9.1')])
    t('3V3', 'B', W, [p('L1.2'), (33.0, 74.88), p('C8.1')])       # output caps join L1.2, whose via is in the finger


def joins(d):
    """Rail pads the fan-out aid finds no clear spot for, joined by hand (R10_DECISIONS D-R2-06)."""
    t, p, via = d.track, d.pad, d.via
    t('3V3', 'B', 0.2, [p('R62.1'), (21.28, 52.4), p('C14.1')])            # onto C14's 3V3 pad and its via
    # C82's RAW end into In2 RAW by one 45 deg stub to a via under the part, between U2's pad rows on B.Cu (moved off
    # the BAT_FAULT_N column east of C82, D-R2-09).
    t('RAW_PROTECTED', 'F', W, [p('C82.1'), (33.1, 66.6)])
    via('RAW_PROTECTED', (33.1, 66.6))
    # U1.74 (VSS): south on F.Cu between pin 75's 3V3 via and pin 73's VCAP2 via (TP82 forbids a via north of it), to a
    # via that also takes C17's GND pad.
    # (into the core table's GND via (17.5, 39.3), off C17.2's pad and paste: D-R2-11)
    t('GND', 'F', 0.2, [p('U1.74'), (17.5, 39.3)])
    t('GND', 'B', 0.3, [p('C17.2'), (17.5, 38.82), (17.5, 39.3)])
    t('GND', 'B', 0.2, [p('U9.8'), (40.325, 79.375), (40.7, 79.0)])         # U9's GND pin, via into the F pour / In1
    via('GND', (40.7, 79.0))
    t('GND', 'B', 0.3, [p('C88.2'), (40.65, 81.53)])                       # C88's return: its own via (D-R2-12)
    via('GND', (40.65, 81.53))
    # The USB-C receptacle's GND contacts strap onto its plated shell tabs (GND on every layer) instead of fan-out vias
    # over the tabs' paste (D-R2-11).
    t('GND', 'F', 0.3, [p('J3.A1B12'), (6.88, 26.8)])
    t('GND', 'F', 0.3, [p('J3.B1A12'), (6.88, 34.8)])
    t('GND', 'B', 0.2, [p('C98.2'), p('U11.6')])                             # C98's return straight to U11's GND pin


def draw(d):
    planes(d)
    battery(d)
    control(d)
    efuse(d)
    ports(d)
    logic(d)
    joins(d)
