"""R10 power copper: the inner planes and the hand-routed supply nets (AGENTS 3), explicit pad-referenced polylines.

In1 is solid GND. In2 is split by rail (R10_DECISIONS D-R2-03): RAW_PROTECTED wraps the board (the forward area, an east
strip and an aft band that reaches the 5.3 V buck's input), PORT_5V3 is a column east of U1 with a finger to the buck
output and the LDO input, and 3V3 is the rest with a forward finger for the 3V3 buck's output, D120 and the servo clamp.
The outer GND pours are drawn by the ground family. Zones are filled at the end of the build.
"""
import pcbnew

FULL = pcbnew.ZONE_CONNECTION_FULL
BAT, W = 1.0, 0.4                      # battery / rail width; ordinary supply branch width
NECK = 0.25                            # U9's IN / OUT bar entries (between its corner pads)

IN1_GND = [(0.3, 0.3), (45.7, 0.3), (45.7, 89.7), (0.3, 89.7)]
IN2_RAW = [(0.3, 0.3), (45.7, 0.3), (45.7, 89.7), (0.3, 89.7), (0.3, 58.0), (17.5, 58.0), (17.5, 62.0), (22.0, 62.0),
           (22.0, 76.0), (32.0, 76.0), (32.0, 58.0), (40.0, 58.0), (40.0, 7.0), (18.0, 7.0), (18.0, 10.5), (9.0, 10.5),
           (9.0, 7.0), (0.3, 7.0)]
IN2_PORT = [(24.5, 7.3), (39.7, 7.3), (39.7, 57.7), (33.4, 57.7), (33.4, 8.8), (28.0, 8.8), (28.0, 15.5),
            (24.5, 15.5)]
IN2_4V8 = [(28.3, 9.1), (33.1, 9.1), (33.1, 29.0), (28.3, 29.0)]
IN2_3V3 = [(0.3, 7.3), (8.7, 7.3), (8.7, 10.8), (18.3, 10.8), (18.3, 7.3), (24.2, 7.3), (24.2, 15.8), (28.0, 15.8),
           (28.0, 29.3), (33.1, 29.3), (33.1, 57.7), (31.7, 57.7), (31.7, 75.7), (22.3, 75.7), (22.3, 61.7),
           (17.8, 61.7), (17.8, 57.7), (0.3, 57.7)]


def planes(d):
    d.zone('R10_GND_In1', 'GND', 'In1', IN1_GND, 1, clr=0.25, conn=FULL)
    d.zone('R10_RAW_In2', 'RAW_PROTECTED', 'In2', IN2_RAW, 1, clr=0.25, conn=FULL)
    d.zone('R10_PORT_5V3_In2', 'PORT_5V3', 'In2', IN2_PORT, 1, clr=0.25, conn=FULL)
    d.zone('R10_PORT_4V8_In2', 'PORT_4V8', 'In2', IN2_4V8, 1, clr=0.25, conn=FULL)
    d.zone('R10_3V3_In2', '3V3', 'In2', IN2_3V3, 1, clr=0.25, conn=FULL)


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
    # U9's IN bar (south tip, 0.25 mm neck between its corner pads), with R167 / R82 / C88 tapped.
    t('BAT_IN', 'B', BAT, [p('J1.1'), (10.6, 74.1), (12.0, 75.5)])
    t('BAT_IN', 'B', BAT, [p('Q120.7'), (12.87, 86.6), (17.35, 86.6), (36.725, 86.6), (38.75, 86.6), (38.75, 81.9)])
    via('BAT_IN', (17.35, 86.6))
    t('BAT_IN', 'F', W, [(17.35, 86.6), (16.625, 86.6)])                 # into R80.1's pad (R80's battery side)
    t('BAT_IN', 'B', W, [(36.725, 86.6), p('R82.1')])
    t('BAT_IN', 'B', NECK, [(38.75, 81.9), (38.75, 80.9)])
    t('BAT_IN', 'B', W, [(29.175, 86.6), p('R167.1')])
    t('BAT_IN', 'B', W, [(38.75, 84.32), p('C88.1')])


def control(d):
    t, p, via = d.track, d.pad, d.via
    # Damper (C89 / C95 -> R166) on F.Cu, clear of J122's tie hole (30.8, 79) by >= 1.85 mm.
    t('BAT_DAMP', 'F', W, [p('C89.2'), p('C95.2')])
    t('BAT_DAMP', 'F', W, [p('C95.2'), (33.2, 77.925), (33.2, 81.4), p('R166.1')])
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
    # U9's OUT bar (north tip) -> R92 bleed, two vias into In2 RAW.
    t(rp, 'B', NECK, [(39.25, 78.3), (39.25, 77.9)])
    t(rp, 'B', W, [(39.25, 77.9), (39.25, 77.0), p('R92.1')])
    t(rp, 'B', W, [(39.25, 77.0), (40.9, 77.0), (40.9, 76.2)])
    for at in ((40.9, 77.0), (40.9, 76.2)):       # east of C84's VLOGIC pad (top)
        via(rp, at)
    # U9 control and timing pins.
    t('BAT_ILIM', 'B', 0.2, [p('U9.9'), p('R84.1')])
    t('BAT_ILIM', 'B', 0.2, [p('R84.1'), (41.275, 81.275), p('TP89.1')])
    t('BAT_DVDT', 'B', 0.2, [(39.9, 78.9), (40.7, 78.1), p('C81.1')])
    t('BAT_OVLO', 'B', 0.2, [p('U9.2'), p('R83.1')])
    t('BAT_OVLO', 'B', 0.2, [p('R83.1'), p('R82.2')])
    # The 5.3 V buck's input on the aft band: C400 / C401 to U400's two IN pins, two vias into In2 RAW.
    t(rp, 'F', W, [p('C400.1'), p('U400.2')])
    t(rp, 'F', W, [p('U400.2'), p('U400.3')])
    t(rp, 'F', W, [p('C401.1'), (14.1, 8.3), (14.1, 7.6), (14.1, 6.5), p('U400.3')])
    for at in ((14.1, 7.6), (14.1, 8.3)):
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
    via('PORT_4V8', (28.8, 22.9))
    t('PORT_4V8', 'F', W, [(28.8, 22.9), (29.2, 22.5), p('C420.1')])
    # Port rails east to their cells (B.Cu), the GH connector pin through one via each.
    t('GPS_4V8', 'B', W, [p('U410.6'), (39.9, 10.95)])
    t('GPS_4V8', 'B', W, [(39.9, 10.95), (41.4, 10.95)])
    t('GPS_4V8', 'B', W, [(39.9, 10.95), (39.9, 12.125), (39.9, 18.45), p('U412.1')])
    t('GPS_4V8', 'B', W, [(39.9, 18.45), (40.55, 19.1)])
    via('GPS_4V8', (39.9, 12.125))
    t('GPS_4V8', 'F', W, [(39.9, 12.125), p('J410.1')])
    t('RADIO_4V8', 'B', W, [p('U420.6'), (39.9, 27.35)])
    t('RADIO_4V8', 'B', W, [(39.9, 27.35), (39.9, 24.125), (39.9, 22.2), p('C421.1')])
    t('RADIO_4V8', 'B', W, [(39.9, 27.35), (39.9, 30.45), p('U422.1')])
    t('RADIO_4V8', 'B', W, [(39.9, 30.45), (40.55, 31.1)])
    via('RADIO_4V8', (39.9, 24.125))
    t('RADIO_4V8', 'F', W, [(39.9, 24.125), p('J420.1')])
    t('CAM_5V', 'B', W, [p('U402.6'), p('U13.1')])
    t('CAM_5V', 'B', W, [p('U13.1'), (40.43, 42.45)])
    t('CAM_5V', 'B', W, [(40.43, 42.45), (40.43, 44.6)])          # through C91.1's pad
    via('CAM_5V', (40.43, 44.6))
    t('CAM_5V', 'F', 0.2, [(40.43, 44.6), p('R104.1')])
    t('CAM_5V', 'B', W, [p('U402.6'), (42.9, 40.05), (42.9, 36.125), (42.9, 35.7), p('C431.1')])
    via('CAM_5V', (42.9, 36.125))
    t('CAM_5V', 'F', W, [(42.9, 36.125), (40.75, 36.125)])
    t('PORT_5V3', 'B', W, [p('U402.1'), (35.5, 40.05)])
    via('PORT_5V3', (35.5, 40.05))
    t('PORT_5V3', 'B', W, [(39.6, 41.25), (39.95, 40.9), p('C430.1')])
    via('PORT_5V3', (39.6, 41.25))
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
    t('VLOGIC', 'B', W, [(37.8, 65.6), (37.8, 54.96), p('R60.1')])
    t('VLOGIC', 'B', W, [(37.8, 65.6), (37.8, 67.0), (37.8, 69.8), p('C7.1')])
    t('VLOGIC', 'B', W, [(37.8, 69.8), (37.8, 75.6)])
    via('VLOGIC', (37.8, 75.6))
    t('VLOGIC', 'F', W, [(37.8, 75.6), (37.8, 76.6)])
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
    t('3V3', 'B', W, [(32.2, 74.0), (31.4, 74.0)])
    via('3V3', (31.4, 74.0))
    t('3V3', 'B', W, [p('C8.1'), p('C9.1')])


def draw(d):
    planes(d)
    battery(d)
    control(d)
    efuse(d)
    ports(d)
    logic(d)
