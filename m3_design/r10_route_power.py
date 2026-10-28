"""R10 power copper: the inner planes and the hand-routed supply nets (AGENTS 3), explicit pad-referenced polylines.

In1 is solid GND. In2 is split by rail (R10_DECISIONS D-R2-03, D-R2-05, D-R2-06): RAW_PROTECTED wraps the board (the
forward area, an east strip and an aft band that reaches the 5.3 V buck's input), PORT_5V3 is a band aft of U410
(y 4.7-6.8) and a column x 35.2-39.7 from the buck output to the camera switch (y <= 42.5), PORT_4V8 the LDO output
block x 28.3-32.4 with U410's cell, and 3V3 is the rest: a strip x 32.7-34.9 under the port buffers, the area east of
U1 forward of the camera switch, and a forward finger for the 3V3 buck's output, D120 and the servo clamp. Fast
interfaces retain adjacent reference copper; the slow port/ACT/ADC controls are exempt (AUD-2).
Two In2 GND zones take priority over the rail regions (R10_DECISIONS D-R3-01, D-R3-05): IN2_GND_CH1 under the whole CH1
column (J121, R134, Q124 and its gate network, TP122 and their pyro copper), so that no rail plane lies near a
pyro barrel; and IN2_GND_Y1, R9's crystal plane (R9_DECISIONS D-S8-20) translated by CORE_SHIFT, with R9's In2 track
keep-out over it.
The outer GND pours are drawn by the ground family. Zones are filled at the end of the build.
"""
import pcbnew

FULL = pcbnew.ZONE_CONNECTION_FULL
BAT, W = 1.0, 0.4                      # battery / rail width; ordinary supply branch width
PAD_W = 0.3                            # U9's IN / OUT bars entered at their full 0.3 mm width (D-R3-02)
BYPASS_W = 0.7                         # C88 feed/exit carry U9's full input current (OQ-2 completion)

IN1_GND = [(0.3, 0.3), (45.7, 0.3), (45.7, 89.7), (0.3, 89.7)]
# D-R3-xx: retained rail-region boundaries from the original port-control layout; AUD-2 removes the slow-control
# reference requirement. The fast UART interfaces retain their reference copper; the regions are 0.3 mm apart:
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
# AUD-2: remove the three filtered-ADC arms and Q121 control-gate bay. The base still covers the fire path and
# all S-8 barrels; the R13 notch and D120's 3V3 corridor stay. Fast interfaces keep their reference rules.
IN2_GND_CH1 = [(0.3, 51.8), (8.65, 51.8), (8.65, 53.55), (9.75, 53.55), (9.75, 51.3), (18.55, 51.3),
               (18.55, 53.4), (18.0, 53.4), (18.0, 56.45), (17.45, 56.45), (17.45, 59.15),
               (18.75, 59.15), (18.75, 58.2), (21.8, 58.2), (21.8, 68.4), (16.3, 68.4), (16.3, 69.7), (0.3, 69.7)]
# D-R3-05: R9's Y1_In2_keepout (x 13.9-21.8, y 45.8-50.45) + CORE_SHIFT (5, -1.5), and R9_GND_In2_Y1's outline: the area
# less r9_ground.xtal_outline's one notch (NRST's B.Cu run (24.3, 49.1)-(25.33, 49.1) to C24.1, its box grown by
# 0.1 + 0.3 mm), the same rule re-run on R10's routed board (no other critical B.Cu track lies wholly outside within
# reach).
Y1_AREA = [(18.9, 44.3), (26.8, 44.3), (26.8, 48.95), (18.9, 48.95)]
# R8-RTE-02 (round 8): a bump (x 26.8-28.6, y 45.8-47.0) takes the 3V3 tooth between the island's edge and C22.2's GND via
# (27.8, 46.6) into the island, its edge meeting the antipad of the GND via (29.2, 46.2).
IN2_GND_Y1 = [(20.6, 44.3), (26.8, 44.3), (26.8, 45.8), (28.6, 45.8), (28.6, 47.0), (26.8, 47.0), (26.8, 48.95), (25.73, 48.95), (25.73, 48.7), (23.9, 48.7), (23.9, 48.95),
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
    # F.Cu: J1.1 -> one bar along y 76.8 -> the protection column (C95 / C89 / C96 / C80 on x 27.52), D8 tapped.
    t('BAT_IN', 'F', BAT, [p('J1.1'), (9.7, 76.8), (27.525, 76.8), p('C95.1')])
    t('BAT_IN', 'F', BAT, [p('C95.1'), p('C89.1')])
    t('BAT_IN', 'F', BAT, [p('C89.1'), p('C96.1')])
    t('BAT_IN', 'F', BAT, [p('C96.1'), p('C80.1')])
    t('BAT_IN', 'F', BAT, [p('D8.1'), (19.85, 76.8)])
    t('BAT_IN', 'F', W, [(13.8, 76.8), p('TP80.1')])
    # B.Cu: J1.1 -> Q120's drain; its branch west of the tie hole ends at the R80 switch feed.
    t('BAT_IN', 'B', BAT, [p('J1.1'), (12.0, 74.1), p('Q120.9')])
    t('BAT_IN', 'B', BAT, [p('Q120.8'), (12.525, 86.6), (17.35, 86.6)])
    via('BAT_IN', (17.35, 86.6))
    t('BAT_IN', 'F', W, [(17.35, 86.6), (16.625, 86.6)])                 # into R80.1's pad (R80's battery side)
    # OQ-2: U9 takes its feed from the protection-column node, removing the independent J1 -> U9 branch.
    # The 1.0 mm F.Cu feed goes north/east of J122's east tie hole, then through one 1.0 / 0.5 mm via (JLC plug limit).
    # The via at x 34.7 also clears J122's existing harness legend (OQ-2 completion).
    # The existing U9 bar entry stays 0.3 mm wide, with the 1.0 mm run ending 0.6 mm short (D-R3-03).
    feed = (34.7, 84.0)
    t('BAT_IN', 'F', BAT, [(27.525, 76.8), (33.45, 76.8), (33.45, 82.75), feed])
    via('BAT_IN', feed, size=(1.0, 0.5))
    t('BAT_IN', 'B', BAT, [feed, (34.7, 86.6)])
    # Feed C88's input pad first; U9 is a dead end beyond that local bypass, never an independently driven spur.
    # The 0.7 mm, 0.8 mm-long entry clears C88.2; the diagonal stays clear of U9's downstream bar.
    t('BAT_IN', 'B', BAT, [(29.825, 86.6), (34.7, 86.6), (36.725, 86.6), (38.75, 86.6),
                         (38.75, 84.32), (39.9, 83.17)])
    t('BAT_IN', 'B', BYPASS_W, [(39.9, 83.17), p('C88.1')])
    t('BAT_IN', 'B', W, [(36.725, 86.6), p('R82.1')])
    t('BAT_IN', 'B', BYPASS_W, [p('C88.1'), (38.75, 82.37), (38.75, 81.4)])
    t('BAT_IN', 'B', PAD_W, [(38.75, 81.4), p('U9.5')])            # pad-entry neck: 0.6 mm to the bar's tip
    t('BAT_IN', 'B', W, [(29.825, 86.6), p('R167.1')])


def control(d):
    t, p, via = d.track, d.pad, d.via
    # Damper (C89 / C95 -> R166) on F.Cu, clear of J122's tie hole (30.8, 79.5) by >= 1.85 mm.
    t('BAT_DAMP', 'F', W, [p('C89.2'), p('C95.2')])
    t('BAT_DAMP', 'F', W, [p('C95.2'), (33.475, 75.2), (36.0, 77.725), p('R166.1')])  # clear of the OQ-2 input feed
    # External switch J400 (GH 2-pin): SW_SOURCE to R80, SW_RETURN to R165 (7 uA contact current).
    t('BAT_SW_SOURCE', 'F', 0.2, [p('J400.1'), (9.875, 86.1), (14.775, 86.1), p('R80.2')])
    t('BAT_SW_RETURN', 'F', 0.2, [p('J400.2'), (12.075, 88.4), p('R165.1')])
    # BAT_ENABLE: R165 -> C87 -> R81 pull-down, east below J122's GND row and down to U9.1 (AUD-5).
    t('BAT_ENABLE', 'F', 0.2, [p('R165.2'), (17.225, 87.6), p('C87.1')])
    t('BAT_ENABLE', 'F', 0.2, [p('C87.1'), (20.9, 85.8), (28.175, 85.8), (37.3, 85.8), (37.7, 85.4)])
    t('BAT_ENABLE', 'F', 0.2, [(28.175, 85.8), p('R81.1')])
    via('BAT_ENABLE', (37.7, 85.4))
    t('BAT_ENABLE', 'B', 0.2, [(37.7, 85.4), (37.7, 80.7), p('U9.1', at=(38.1, 80.3))])


def efuse(d):
    t, p, via = d.track, d.pad, d.via
    rp = 'RAW_PROTECTED'
    # GAP-2: local output bypass and Schottky, fed directly from U9's OUT bar. The 0.3 mm pad-entry neck remains;
    # the 1.0 mm copper beyond it carries the continuous logic/port load. BAT_IN/C88/U9 IN copper is unchanged.
    out = (39.25, 77.8)
    t(rp, 'B', PAD_W, [p('U9.6'), out])
    # The diagonal passes through C82.1 before reaching D9; its split point is inside the capacitor pad.
    t(rp, 'B', BAT, [out, (40.375, 76.675), (41.6, 75.45), p('D9.1')])
    u9_out = ((40.8, 77.1), (41.35, 77.1), (41.9, 77.1), (42.45, 77.1))
    # The 0.7 mm entry starts inside C82.1 and crosses the OUT diagonal at its explicit pad-internal node.
    t(rp, 'B', BYPASS_W, [(39.8, 76.1), u9_out[0]])
    t(rp, 'B', W, list(u9_out))
    for at in u9_out:
        via(rp, at)
    # Short component stubs return through the uninterrupted In1 GND plane to U9's GND via (40.7,79.0).
    t('GND', 'B', W, [p('C82.2'), (39.8, 74.35)])
    via('GND', (39.8, 74.35))
    t('GND', 'B', W, [p('D9.2'), (41.7, 69.8)])
    via('GND', (41.7, 69.8))
    # U11's RAW input (bottom) and C97 (top, directly over it) share one via into In2 RAW.
    t(rp, 'B', 0.3, [p('U11.2'), (32.3, 63.0)])
    t(rp, 'F', 0.3, [p('C97.1'), (32.3, 63.0)])
    via(rp, (32.3, 63.0))
    # U9 control and timing pins.
    t('BAT_ILIM', 'B', 0.2, [p('U9.9'), p('R84.1')])
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
    # GAP-3: resin-filled, copper-capped/planar VIPPO, confined to U401's GND exposed pad; paste windows unchanged.
    for at in ((27.3, 13.6), (27.9, 13.6)):
        via('GND', at, size=(0.5, 0.3), filled=True, capped=True)
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
    # AUD-8: only the port supply capacitor and connector remain on the switched rail; IO LDO cells are removed.
    t('GPS_4V8', 'B', W, [p('U410.6'), (40.05, 10.95), (40.65, 10.95), p('C411.1')])
    t('GPS_4V8', 'B', W, [(40.05, 10.95), (40.05, 11.45)])
    via('GPS_4V8', (40.05, 11.45))
    t('GPS_4V8', 'F', W, [(40.05, 11.45), (40.725, 12.125)])
    # The radio supply crosses above the RX wire's B.Cu hop (x38.8,y24.15–28.95).
    t('RADIO_4V8', 'B', W, [p('U420.6'), (36.9, 27.35), (36.9, 23.5), (40.05, 23.5),
                            (40.05, 22.2), p('C421.1')])
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
    t('3V3', 'F', 0.2, [p('U421.3'), (34.95, 25.35), (34.425, 24.825)])
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
    # GAP-2: relocated R92 reuses C82's old RAW/GND plane feeds.
    t('RAW_PROTECTED', 'F', W, [p('R92.1'), (33.1, 66.6)])
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
