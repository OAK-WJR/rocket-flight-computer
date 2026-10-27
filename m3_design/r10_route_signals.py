"""R10 signal copper, all hand-drawn: the external-port UARTs and IO rails, then every non-critical signal.

Hand-routed (AGENTS 3 critical nets, r10 route_check classes 'uart' and 'power'): GPS_*_MCU and RADIO_*_MCU from U1's
north edge to the port buffers U411 / U421, and the three port IO rails (*_IO_3V3: the TPS70933 output, its capacitors,
its bleed resistor and the buffer's VCCB). The radio pair crosses once (PB12 / PB13 order against U421's pin order):
RADIO_TX_MCU hops under RADIO_RX_MCU on B.Cu, a GND via within 1.5 mm of each layer change (AGENTS 3).

Every other signal is a deliberate hand-drawn polyline (R10_DECISIONS D-R2-08 / D-R2-09), grouped by cell; the design
aid's earlier frozen table (m3_design/r10_aid/ncroute.py) served only as a sketch of feasible paths.
"""
S, IO = 0.2, 0.3        # signal width; IO rail trunk width (bottom)


def uarts(d):
    t, p, via = d.track, d.pad, d.via
    # GPS (USART6): two parallel lanes north from U1.64 / U1.63, one 45 deg diagonal each, into U411's west pins.
    t('GPS_RX_MCU', 'F', S, [p('U1.64'), (22.5, 28.1), (33.2, 17.4), (33.2, 15.05), p('U411.4')])
    t('GPS_TX_MCU', 'F', S, [p('U1.63'), (23.0, 28.35), p('U411.5')])
    # Radio (UART5): RX (PB12, U1.51, east pin) on F.Cu into U421.4 from the west; TX (PB13, U1.52) hops under it.
    t('RADIO_RX_MCU', 'F', S, [p('U1.51'), (29.0, 34.4), (30.0, 33.4), (30.0, 29.35), (33.55, 25.8), p('U421.4')])
    t('RADIO_TX_MCU', 'F', S, [p('U1.52'), (28.5, 32.4)])
    t('RADIO_TX_MCU', 'B', S, [(28.5, 32.4), (30.95, 32.4)])
    t('RADIO_TX_MCU', 'F', S, [(30.95, 32.4), p('U421.5')])
    for at in ((28.5, 32.4), (30.95, 32.4)):
        via('RADIO_TX_MCU', at)
    for at in ((28.5, 31.5), (31.85, 32.4)):          # 0.9 mm from each RADIO_TX_MCU layer change
        via('GND', at)


def io_rails(d):
    t, p, via = d.track, d.pad, d.via
    # GPS / radio (the radio cell is the GPS cell 12 mm forward): LDO output -> its capacitors on B.Cu, the buffer's VCCB
    # through a via under it, and over the port-rail track on F.Cu to the bleed resistor east of it.
    for net, dy in (('GPS_IO_3V3', 0.0), ('RADIO_IO_3V3', 12.0)):
        ldo, cin, cbulk, bleed, buf = (('U412', 'C443', 'C442', 'R443', 'U411') if dy == 0 else
                                        ('U422', 'C453', 'C452', 'R453', 'U421'))
        t(net, 'B', IO, [p(f'{ldo}.5'), p(f'{cin}.1')])
        t(net, 'B', IO, [p(f'{cin}.1'), (34.675, 22.525 + dy), p(f'{cbulk}.1')])
        t(net, 'F', S, [p(f'{buf}.7'), (35.45, 17.75 + dy)])
        via(net, (35.45, 17.75 + dy))
        t(net, 'B', IO, [(35.45, 17.75 + dy), (35.45, 18.45 + dy)])
        t(net, 'F', S, [(35.45, 17.75 + dy), (36.9, 19.2 + dy), (40.0, 19.2 + dy), (42.0, 17.2 + dy)])
        via(net, (42.0, 17.2 + dy))
        t(net, 'B', IO, [(42.0, 17.2 + dy), p(f'{bleed}.1')])
    # Camera: U13 -> C93 -> C92 -> R103 on B.Cu, U12's VCCB through a via under it.
    net = 'CAM_IO_3V3'
    t(net, 'B', IO, [p('U13.5'), (35.6, 42.45), p('C93.1')])        # node at the VCCB via: C93 is U12.7's bypass (D-R2-11)
    t(net, 'B', IO, [p('C93.1'), (34.675, 45.245), p('C92.1')])
    t(net, 'B', IO, [p('C92.1'), (40.695, 46.02), p('R103.1')])
    t(net, 'F', S, [p('U12.7'), (35.45, 41.75), (35.6, 41.9)])
    via(net, (35.6, 41.9))
    t(net, 'B', IO, [(35.6, 41.9), (35.6, 42.45)])


def port_wires(d):
    """GPS / radio connector side: the buffer orders RX above TX, the connector TX above RX, so the wires cross once.
    RX runs under the cell on B.Cu (x 38.8) between two vias; TX stays on F.Cu west of the ESD diodes (x 38.25)."""
    t, p, via = d.track, d.pad, d.via
    for pre, r_rx, r_tx, d_tx, d_rx, j, dy in (('GPS', 'R440', 'R441', 'D410', 'D411', 'J410', 0.0),
                                               ('RADIO', 'R450', 'R451', 'D420', 'D421', 'J420', 12.0)):
        tx, rx = f'{pre}_TX_WIRE', f'{pre}_RX_WIRE'
        t(tx, 'F', S, [p(f'{r_tx}.2'), (38.25, 18.55 + dy), (38.25, 15.325 + dy), p(f'{d_tx}.1')])
        t(tx, 'F', S, [p(f'{d_tx}.1'), (40.6, 14.775 + dy), p(f'{j}.3')])
        t(rx, 'F', S, [p(f'{r_rx}.1'), (38.8, 12.15 + dy)])
        t(rx, 'B', S, [(38.8, 12.15 + dy), (38.8, 16.95 + dy)])
        t(rx, 'F', S, [(38.8, 16.95 + dy), p(f'{d_rx}.1')])
        t(rx, 'F', S, [p(f'{d_rx}.1'), (40.35, 16.275 + dy), p(f'{j}.4')])
        for at in ((38.8, 12.15 + dy), (38.8, 16.95 + dy)):
            via(rx, at)


def camera_control(d):
    """U1's east pins to the camera buffer U12 and switch U402. The buffer orders RX above TX and OE below both while
    U1 orders OE, TX, RX from the top, so RX and TX each take one short B.Cu hop east of USB_LIMITED; the switch enable
    reaches its pull-down R431 on B.Cu through one via between R431 and C93."""
    t, p, via = d.track, d.pad, d.via
    t('CAM_MCU_RX', 'F', S, [p('U1.37'), (32.55, 43.5), (32.95, 43.9)])
    t('CAM_MCU_RX', 'B', S, [(32.95, 43.9), (32.95, 39.8), (33.55, 39.2)])
    t('CAM_MCU_RX', 'F', S, [(33.55, 39.2), (34.45, 38.3), p('U12.4')])
    t('CAM_MCU_TX', 'F', S, [p('U1.38'), (33.25, 43.0), (33.55, 43.3)])
    t('CAM_MCU_TX', 'B', S, [(33.55, 43.3), (33.55, 41.55), (33.75, 41.35)])
    t('CAM_MCU_TX', 'F', S, [(33.75, 41.35), (34.2, 40.9), p('U12.5')])
    for net, at in (('CAM_MCU_RX', (32.95, 43.9)), ('CAM_MCU_RX', (33.55, 39.2)),
                    ('CAM_MCU_TX', (33.55, 43.3)), ('CAM_MCU_TX', (33.75, 41.35))):
        via(net, at)
    t('CAM_UART_OE', 'F', S, [p('U12.6'), p('R102.1')])
    t('CAM_UART_OE', 'F', S, [p('U1.39'), (34.95, 42.5)])                    # square T onto U12.6 -> R102.1
    t('CAM_PWR_EN', 'F', S, [p('U1.41'), (32.75, 41.5), (34.25, 40.0)])
    via('CAM_PWR_EN', (34.25, 40.0))
    t('CAM_PWR_EN', 'B', S, [(34.25, 40.0), (34.6, 40.0), p('R431.1')])
    t('CAM_PWR_EN', 'B', S, [p('R431.1'), (35.675, 38.15), p('U402.3')])
    t('CAM_FAULT_N', 'F', S, [p('U1.42'), (32.6, 41.0), p('R432.1')])
    t('CAM_FAULT_N', 'F', S, [p('R432.1'), (33.9, 37.525), (33.9, 36.825)])
    via('CAM_FAULT_N', (33.9, 36.825))
    t('CAM_FAULT_N', 'B', S, [(33.9, 36.825), (37.575, 36.825), p('U402.4')])


def gps_oe(d):
    """GPS_UART_OE (PD15, U1.62) in the strip south-east of the GPS UART lanes, under C420 to the pull-down R442."""
    t, p = d.track, d.pad
    t('GPS_UART_OE', 'F', S, [p('U1.62'), (23.5, 28.65), (28.1, 24.05), (31.6, 24.05), (32.8, 22.85), (32.8, 20.725),
                               p('R442.1')])
    t('GPS_UART_OE', 'F', S, [p('U411.6'), p('R442.1')])


def gnd_joins(d):
    """GND pads the signal copper boxes in, joined by hand (the fan-out aid runs after this family)."""
    t, p, via = d.track, d.pad, d.via
    t('GND', 'B', S, [(21.28, 53.65), (21.82, 53.65)])           # R63's GND pad onto C14's GND strap (core table)
    t('GND', 'F', S, [p('U1.49'), (28.75, 37.5)])                # west between pin 50's / 48's vias into the pour
    t('GND', 'F', S, [p('U12.2'), (35.45, 36.6)])                # into C100's GND pad (its own via)
    # C93 (U13's output capacitor) returns straight to U13's GND pin: a short strap between the two pads, east under
    # U12 and down the gap between U13's pin columns (its pad is boxed in on three sides, D-R2-09).
    t('GND', 'B', IO, [p('C93.2'), (37.0, 40.9), (37.6, 41.5), (37.6, 43.4), p('U13.2')])
    for d_gnd, y in (('D411.2', 15.625), ('D421.2', 27.625)):     # ESD returns boxed in by the port wires
        t('GND', 'F', S, [p(d_gnd), (39.4, y)])           # hole >= 0.1 mm off the pad's mask, ring off its paste (D-R2-11)
        via('GND', (39.4, y))


def servo_lanes(d):
    """SERVO1-4_MCU (U1.22-25, PA0-PA3) as one F.Cu bundle (R10_DECISIONS D-R2-09): straight south from the pins,
    one staggered 45 deg turn (0.6 / 0.7 / 0.6 mm between the diagonals), straight south again over the bottom sense
    rows to one via each at the head of the servo cell (SERVO1's lower, beside R122, so no bottom GND pour finger is
    left between it and TP120's 1 mm clearance). The diagonals run parallel to the two sense lanes east of them."""
    t, p, via = d.track, d.pad, d.via
    for net, pin, turn, x, end in (('SERVO1_MCU', 'U1.22', 54.8, 20.4, 68.6), ('SERVO2_MCU', 'U1.23', 55.15, 22.7, 66.2),
                                   ('SERVO3_MCU', 'U1.24', 55.65, 23.3, 66.7), ('SERVO4_MCU', 'U1.25', 56.0, 25.7, 66.4)):
        a = p(pin)
        t(net, 'F', S, [a, (a[0], turn), (x, turn + a[0] - x), (x, end)])
        via(net, (x, end))


def servo_cell(d):
    """Bottom servo cell: D121 (turned 90 deg) has S2 / S1 in its west column and S3 / S4 in its east column, so the
    inner lanes S2 and S3 run down the channel between the columns (tapping their pins and pull-downs from inside) and
    the outer lanes S1 and S4 pass outside and tap the south pins; each lane then ends in its 1 k resistor's MCU pad.
    Every lane enters from its via straight south (D-R2-09: R157 turned so its GND pad sits east of the S4 lane).
    The clamp's GND and 3V3 pins strap out sideways to one via each."""
    t, p, via = d.track, d.pad, d.via
    t('SERVO1_MCU', 'B', S, [(20.4, 68.6), p('R154.1')])
    # R150-R153 and D121 sit 1.15 / 0.6 mm aft of D-R2-07's spots (M-6: 1.5 mm from J122's pins, D-R2-12).
    t('SERVO1_MCU', 'B', S, [p('R154.1'), (20.4, 73.04), p('R150.1')])
    t('SERVO1_MCU', 'B', S, [(20.4, 72.55), p('D121.1')])
    t('SERVO2_MCU', 'B', S, [(22.7, 66.2), (22.7, 73.28), p('R151.1')])
    t('SERVO2_MCU', 'B', S, [(22.7, 69.03), p('R155.1')])
    t('SERVO2_MCU', 'B', S, [(22.7, 70.65), p('D121.3')])
    t('SERVO3_MCU', 'B', S, [(23.3, 66.7), (23.3, 73.28), p('R152.1')])
    t('SERVO3_MCU', 'B', S, [(23.3, 69.03), p('R156.1')])
    t('SERVO3_MCU', 'B', S, [(23.3, 70.65), p('D121.4')])
    t('SERVO4_MCU', 'B', S, [(25.7, 66.4), p('R157.1')])
    t('SERVO4_MCU', 'B', S, [p('R157.1'), (25.7, 73.14), p('R153.1')])
    t('SERVO4_MCU', 'B', S, [(25.7, 72.55), p('D121.6')])
    t('GND', 'B', IO, [p('D121.2'), (21.05, 71.6)])                # hole / ring clear of R123.2's mask / paste (top)
    via('GND', (21.05, 71.6))
    t('3V3', 'B', IO, [p('D121.5'), (25.05, 71.6)])
    via('3V3', (25.05, 71.6))


def east_lanes(d):
    """U1's east-side status and supply-sense lines (R10_DECISIONS D-R2-09). The pyro sense lanes (pyro family) leave
    U1.33 / U1.34 through R170 / R172 and run south at x 34.4 / 35.1. The three lines from U1.28-30 escape straight
    east inside them, drop through one via each east of the USB_LIMITED run and cross under the sense lanes on B.Cu:
    VLOGIC_SENSE (PA6) and BAT_FAULT_N (PA5) straight east under C92's body (between its pads), to the VLOGIC divider
    and to BAT_FAULT_N's F.Cu column x 37.0; LOGIC_SOURCE_ST (PA4) straight south to U11.9, taking its pull-up R91 and
    test pad TP87 by short stubs. BAT_FAULT_N's column takes its pull-up R89 and test pad TP85, passes C82 and runs
    under C84's body (between its pads) to a via, then straight south on B.Cu between C9 and the VLOGIC spine into
    U9.4."""
    t, p, via = d.track, d.pad, d.via
    # VLOGIC_SENSE (PA6): divider R61 / C60 / R60 hangs off a short lane x 38.66, R60's VLOGIC pad on the spine.
    t('VLOGIC_SENSE', 'F', S, [p('U1.30'), (33.5, 47.0)])
    via('VLOGIC_SENSE', (33.5, 47.0))
    t('VLOGIC_SENSE', 'B', S, [(33.5, 47.0), (38.66, 47.0), p('R61.1')])
    t('VLOGIC_SENSE', 'B', S, [p('R61.1'), p('C60.1')])
    t('VLOGIC_SENSE', 'B', S, [p('C60.1'), p('R60.2')])
    # BAT_FAULT_N (PA5)
    t('BAT_FAULT_N', 'F', S, [p('U1.29'), (33.2, 47.5), (33.6, 47.9)])
    via('BAT_FAULT_N', (33.6, 47.9))
    t('BAT_FAULT_N', 'B', S, [(33.6, 47.9), (37.0, 47.9)])
    via('BAT_FAULT_N', (37.0, 47.9))
    t('BAT_FAULT_N', 'F', S, [(37.0, 47.9), p('R89.2')])
    t('BAT_FAULT_N', 'F', S, [p('R89.2'), p('TP85.1')])
    t('BAT_FAULT_N', 'F', S, [p('TP85.1'), (37.0, 74.0)])
    via('BAT_FAULT_N', (37.0, 74.0))
    t('BAT_FAULT_N', 'B', S, [(37.0, 74.0), (37.0, 78.9), (38.1, 78.9)])
    # LOGIC_SOURCE_ST (PA4)
    t('LOGIC_SOURCE_ST', 'F', S, [p('U1.28'), (32.65, 48.0), (32.95, 48.3)])
    via('LOGIC_SOURCE_ST', (32.95, 48.3))
    t('LOGIC_SOURCE_ST', 'B', S, [(32.95, 48.3), (32.95, 57.0), (33.8, 57.85), p('U11.9')])
    t('LOGIC_SOURCE_ST', 'B', S, [(32.95, 54.85), p('R91.2')])
    t('LOGIC_SOURCE_ST', 'B', S, [(32.95, 56.6), p('TP87.1')])


def cam_sense(d):
    """CAM_5V_SENSE (PB1, U1.35): straight east from the pin above the sense resistors, one 45 deg rise between the
    camera UART hop vias, east under R102's body (between its pads) and straight south into the camera-supply
    divider column R104 / R105 / C94 (R10_DECISIONS D-R2-09)."""
    t, p = d.track, d.pad
    t('CAM_5V_SENSE', 'F', S, [p('U1.35'), (33.35, 44.5), (34.45, 43.4), (39.57, 43.4), p('R104.2')])
    t('CAM_5V_SENSE', 'F', S, [p('R104.2'), p('R105.1')])
    t('CAM_5V_SENSE', 'F', S, [p('R105.1'), p('C94.1')])


def south_sense(d):
    """V3V3_SENSE (PC3_C, U1.18): one via under the pin, one 45 deg run south-west on B.Cu and into the divider node
    R62.2 / R63.1 from the south."""
    t, p, via = d.track, d.pad, d.via
    t('V3V3_SENSE', 'F', S, [p('U1.18'), (25.5, 51.75)])
    via('V3V3_SENSE', (25.5, 51.75))                      # ring clear of U1.18's paste (D87)
    t('V3V3_SENSE', 'B', S, [(25.5, 51.75), (22.7, 54.55), (20.42, 54.55), p('R63.1')])
    t('V3V3_SENSE', 'B', S, [p('R62.2'), p('R63.1')])


def port_links(d):
    """Port buffer to series-resistor links (one straight pad-to-pad run each) and the camera wire side: the buffer
    orders RX above TX, J9 TX above RX, so CAM_RX_WIRE steps east above D401 and CAM_TX_WIRE runs west of D400."""
    t, p = d.track, d.pad
    for net, a, b in (('GPS_RX_BUFFER', 'R440.2', 'U411.1'), ('GPS_TX_BUFFER', 'R441.1', 'U411.8'),
                      ('RADIO_RX_BUFFER', 'U421.1', 'R450.2'), ('RADIO_TX_BUFFER', 'U421.8', 'R451.1'),
                      ('CAM_RX_BUFFER', 'U12.1', 'R100.2'), ('CAM_TX_BUFFER', 'R101.1', 'U12.8')):
        t(net, 'F', S, [p(a), p(b)])
    t('CAM_RX_WIRE', 'F', S, [p('R100.1'), (39.4, 36.15), (39.4, 38.775), (40.6, 38.775), p('J9.3')])
    t('CAM_RX_WIRE', 'F', S, [(39.4, 38.775), p('D401.1')])
    t('CAM_TX_WIRE', 'F', S, [p('R101.2'), (38.8, 42.55), p('D400.1')])
    t('CAM_TX_WIRE', 'F', S, [p('D400.1'), (40.35, 40.275), p('J9.4')])


def port_control(d):
    """GPS / radio power-switch enables and fault flags from U1's north edge (pins 55 / 56 / 57 / 61) and the radio
    UART OE from its east edge. The radio pair leaves as two parallel 45 deg escapes: RADIO_FAULT_N north through its
    pull-up R422 and one 45 deg run to a via over U420.4; RADIO_PWR_EN to one via and south on B.Cu beside the GPS_FAULT_N lane
    (0.55 mm pitch, so no GND pour finger between them) into U420.3. The GPS pair passes under the GPS UART lanes and U401's cell on B.Cu (two parallel lanes x 24.9 / 26.9),
    then two parallel 45 deg F.Cu runs to vias beside U410 (USB_LIMITED's B.Cu run and C408 / U401 / C405 fence the
    bottom side, so each takes three vias)."""
    t, p, via = d.track, d.pad, d.via
    # radio
    t('RADIO_FAULT_N', 'F', S, [p('U1.56'), (26.5, 34.15), (27.4, 33.25), p('R422.1')])
    t('RADIO_FAULT_N', 'F', S, [p('R422.1'), (28.4, 28.425), (32.3, 24.525)])
    via('RADIO_FAULT_N', (32.3, 24.525))
    t('RADIO_FAULT_N', 'B', S, [(32.3, 24.525), p('U420.4')])
    t('RADIO_PWR_EN', 'F', S, [p('U1.55'), (27.0, 34.35), (28.0, 33.35), (28.0, 29.45)])
    via('RADIO_PWR_EN', (28.0, 29.45))
    t('RADIO_PWR_EN', 'B', S, [(28.0, 29.45), (27.45, 28.9), (27.45, 25.45), p('U420.3')])
    t('RADIO_UART_OE', 'F', S, [p('U421.6'), p('R452.1')])
    t('RADIO_UART_OE', 'F', S, [p('R452.1'), (31.75, 33.775), (31.75, 39.5), p('U1.45')])
    # GPS
    t('GPS_FAULT_N', 'F', S, [p('R412.1'), p('U1.57')])
    t('GPS_FAULT_N', 'F', S, [p('R412.1'), (26.9, 32.525)])
    via('GPS_FAULT_N', (26.9, 32.525))
    t('GPS_FAULT_N', 'B', S, [(26.9, 32.525), (26.9, 15.825)])
    via('GPS_FAULT_N', (26.9, 15.825))
    t('GPS_FAULT_N', 'F', S, [(26.9, 15.825), (26.9, 14.725), (30.2, 11.425), (31.3, 11.425)])
    via('GPS_FAULT_N', (31.3, 11.425))
    t('GPS_FAULT_N', 'B', S, [(31.3, 11.425), (31.3, 9.05), p('U410.4')])
    t('GPS_PWR_EN', 'F', S, [p('U1.61'), (24.0, 33.45), (24.9, 32.55)])
    via('GPS_PWR_EN', (24.9, 32.55))
    t('GPS_PWR_EN', 'B', S, [(24.9, 32.55), (24.9, 14.45)])
    via('GPS_PWR_EN', (24.9, 14.45))
    t('GPS_PWR_EN', 'F', S, [(24.9, 14.45), (27.2, 12.15)])
    via('GPS_PWR_EN', (27.2, 12.15))
    t('GPS_PWR_EN', 'B', S, [(27.2, 12.15), (27.2, 9.05), p('U410.3')])


def leds(d):
    """Status LEDs west of U1: each series resistor straight to its LED, U1's pins to the resistors by one bend."""
    t, p = d.track, d.pad
    t('LED_RED_A', 'F', S, [p('R32.2'), (11.9, 39.65), p('LED1.2')])
    t('LED_YEL_A', 'F', S, [p('LED2.1'), p('R33.2')])
    t('LED_RED', 'F', S, [p('R32.1'), (14.0, 40.75), (14.0, 42.0), p('U1.86')])
    t('LED_YEL', 'F', S, [p('U1.88'), (14.3, 43.0), p('R33.1')])


def buzzer(d):
    """Buzzer: BUZZ_DRV (PC14, U1.8, south edge) north under U1 on F.Cu, across USB_LIMITED by one F.Cu run beside
    the USB pair, then straight north on B.Cu to the gate resistor R162. BUZZ_OUT (D-R2-09: Q123 shifted 0.25 mm east
    so its drain lines up under LS120.2) is one via under LS120.2 on Q123's drain column, the clamp D123 tapped by one
    45 deg run."""
    t, p, via = d.track, d.pad, d.via
    t('BUZZ_DRV', 'F', S, [p('U1.8'), (20.5, 48.75), (21.8, 47.45), (21.8, 37.95), (23.1, 36.65)])
    via('BUZZ_DRV', (23.1, 36.65))
    t('BUZZ_DRV', 'B', S, [(23.1, 36.65), (20.3, 33.85)])
    via('BUZZ_DRV', (20.3, 33.85))
    t('BUZZ_DRV', 'F', S, [(20.3, 33.85), (20.3, 33.05), (17.8, 30.55)])
    via('BUZZ_DRV', (17.8, 30.55))
    t('BUZZ_DRV', 'B', S, [(17.8, 30.55), (16.8, 29.55), (16.8, 18.85), p('R162.1')])
    t('BUZZ_G', 'B', S, [p('R162.2'), (18.3, 17.95), p('Q123.1')])
    t('BUZZ_G', 'B', S, [p('R163.1'), (17.6, 17.65), p('R162.2')])
    t('BUZZ_OUT', 'F', S, [p('LS120.2'), (21.85, 17.95)])
    via('BUZZ_OUT', (21.85, 17.95))
    t('BUZZ_OUT', 'B', S, [p('Q123.3'), (21.85, 17.95), (21.85, 18.78), p('D123.2')])


def pullpin(d):
    """Pull-pin: PULLPIN (PC13, U1.7) north under U1 on F.Cu to one via, then west and up the board's west edge on
    B.Cu (between the USB-C shell holes and USB_FAULT_N's corner) to the clamp D122 and the input filter C160 / R160 /
    R161 at J123; J123.1 reaches R160 by one via."""
    t, p, via = d.track, d.pad, d.via
    t('PULLPIN', 'F', S, [(20.05, 51.0), (20.05, 46.2), (21.4, 44.85), (21.4, 42.15), (20.4, 41.15)])
    via('PULLPIN', (20.4, 41.15))
    t('PULLPIN', 'B', S, [(20.4, 41.15), (13.3, 41.15), (10.8, 38.65), (10.8, 37.55), (5.0, 31.75), (5.0, 23.0),
                          p('D122.3')])
    t('PULLPIN', 'B', S, [p('D122.3'), (11.0, 13.58), p('C160.1')])
    t('PULLPIN', 'B', S, [p('C160.1'), p('R160.2')])
    t('PULLPIN', 'B', S, [p('R160.2'), (13.0, 11.43), p('R161.2')])
    t('PULLPIN_EXT', 'F', S, [p('J123.1'), (8.375, 14.45)])
    via('PULLPIN_EXT', (8.375, 14.45))
    t('PULLPIN_EXT', 'B', S, [(8.375, 14.45), (8.375, 10.57), p('R160.1')])


def servo_out(d):
    """Series resistors R150-R153 straight up into J122's signal row (2.54 mm pitch, one column each)."""
    for i, pin in ((1, 1), (2, 4), (3, 7), (4, 10)):
        d.track(f'SERVO{i}_OUT', 'B', S, [d.pad(f'J122.{pin}'), d.pad(f'R{149 + i}.2')])


def draw(d):
    uarts(d)
    io_rails(d)
    port_wires(d)
    camera_control(d)
    gps_oe(d)
    servo_lanes(d)
    servo_cell(d)
    east_lanes(d)
    south_sense(d)
    cam_sense(d)
    port_links(d)
    port_control(d)
    leds(d)
    buzzer(d)
    pullpin(d)
    servo_out(d)
    gnd_joins(d)
