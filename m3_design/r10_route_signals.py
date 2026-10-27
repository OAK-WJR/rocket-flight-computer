"""R10 signal copper: the external-port UARTs and IO rails by hand, the other signals from a frozen table.

Hand-routed (AGENTS 3 critical nets, r10 route_check classes 'uart' and 'power'): GPS_*_MCU and RADIO_*_MCU from U1's
north edge to the port buffers U411 / U421, and the three port IO rails (*_IO_3V3: the TPS70933 output, its capacitors,
its bleed resistor and the buffer's VCCB). The radio pair crosses once (PB12 / PB13 order against U421's pin order):
RADIO_TX_MCU hops under RADIO_RX_MCU on B.Cu, a GND via within 1.5 mm of each layer change (AGENTS 3).

AUTO (below the marker) is the non-critical signal table frozen from the design aid m3_design/r10_aid/ncroute.py
(R10_DECISIONS D-R2-04, D-R2-07): explicit polylines and vias, drawn without search.
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
    t(net, 'B', IO, [p('U13.5'), p('C93.1')])
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
    t('GND', 'B', IO, [p('C93.2'), (35.35, 40.9)])                # C93's return into the bottom pour east of it
    for d_gnd, y in (('D411.2', 15.625), ('D421.2', 27.625)):     # ESD returns boxed in by the port wires
        t('GND', 'F', S, [p(d_gnd), (39.3, y)])
        via('GND', (39.3, y))


def servo_cell(d):
    """Bottom servo cell: D121 (turned 90 deg) has S2 / S1 in its west column and S3 / S4 in its east column, so the
    inner lanes S2 and S3 run down the channel between the columns (tapping their pins and pull-downs from inside) and
    the outer lanes S1 and S4 pass outside and tap the south pins; each lane then ends in its 1 k resistor's MCU pad.
    The lanes reach the cell through vias the MCU-side table brings them to (S1 west of D9, S2 / S3 between D9's pads,
    S4 between R89's pads). The clamp's GND and 3V3 pins strap out sideways to one via each."""
    t, p, via = d.track, d.pad, d.via
    t('SERVO1_MCU', 'B', S, [(19.3, 65.05), (20.4, 66.15), p('R154.1')])
    t('SERVO1_MCU', 'B', S, [p('R154.1'), (20.4, 74.19), p('R150.1')])
    t('SERVO1_MCU', 'B', S, [(20.4, 73.15), p('D121.1')])
    t('SERVO2_MCU', 'B', S, [(22.7, 66.5), (22.7, 74.43), p('R151.1')])
    t('SERVO2_MCU', 'B', S, [(22.7, 69.03), p('R155.1')])
    t('SERVO2_MCU', 'B', S, [(22.7, 71.25), p('D121.3')])
    t('SERVO3_MCU', 'B', S, [(23.3, 67.2), (23.3, 74.43), p('R152.1')])
    t('SERVO3_MCU', 'B', S, [(23.3, 69.03), p('R156.1')])
    t('SERVO3_MCU', 'B', S, [(23.3, 71.25), p('D121.4')])
    t('SERVO4_MCU', 'B', S, [(28.3, 65.6), (28.3, 69.73), p('R157.1')])
    t('SERVO4_MCU', 'B', S, [p('R157.1'), (25.7, 74.29), p('R153.1')])
    t('SERVO4_MCU', 'B', S, [(25.7, 73.15), p('D121.6')])
    for net, at in (('SERVO1_MCU', (19.3, 65.05)), ('SERVO2_MCU', (22.7, 66.5)), ('SERVO3_MCU', (23.3, 67.2)),
                    ('SERVO4_MCU', (28.3, 65.6))):
        via(net, at)
    t('GND', 'B', IO, [p('D121.2'), (20.95, 72.2)])
    via('GND', (20.95, 72.2))
    t('3V3', 'B', IO, [p('D121.5'), (25.05, 72.2)])
    via('3V3', (25.05, 72.2))


# ---- AUTO: generated by m3_design/r10_aid/ncroute.py + freeze_signals.py, then hand-cleaned (D-R2-07) ----
AUTO_TRACKS = [
    ('GPS_RX_BUFFER', 'F', ['R440.2', 'U411.1']),
    ('GPS_TX_BUFFER', 'F', ['R441.1', 'U411.8']),
    ('RADIO_RX_BUFFER', 'F', ['U421.1', 'R450.2']),
    ('RADIO_TX_BUFFER', 'F', ['U421.8', 'R451.1']),
    ('CAM_RX_BUFFER', 'F', ['U12.1', 'R100.2']),
    ('CAM_TX_BUFFER', 'F', ['R101.1', 'U12.8']),
    ('CAM_RX_WIRE', 'F', ['R100.1', (39.4, 36.15), (39.4, 38.775), (40.6, 38.775), 'J9.3']),
    ('CAM_RX_WIRE', 'F', [(39.4, 38.775), 'D401.1']),
    ('CAM_TX_WIRE', 'F', ['R101.2', (38.8, 42.55), 'D400.1']),
    ('CAM_TX_WIRE', 'F', ['D400.1', (40.35, 40.275), 'J9.4']),
    ('RADIO_UART_OE', 'F', ['U421.6', (34.95, 29.4), (34.3625, 29.9875), 'R452.1']),
    ('RADIO_UART_OE', 'F', ['R452.1', (31.75, 33.775), (31.75, 39.5), 'U1.45']),
    ('LED_RED_A', 'F', ['R32.2', (11.9, 39.65), 'LED1.2']),
    ('LED_YEL_A', 'F', ['LED2.1', 'R33.2']),
    ('LED_RED', 'F', ['R32.1', (14, 40.75), (14, 42), 'U1.86']),
    ('LED_YEL', 'F', ['U1.88', (14.3, 43), 'R33.1']),
    ('BUZZ_G', 'B', ['R162.2', (18.3, 17.95), 'Q123.1']),
    ('BUZZ_G', 'B', ['R163.1', (17.6, 17.65), 'R162.2']),
    ('BUZZ_OUT', 'F', ['LS120.2', (21.85, 20.6)]),
    ('BUZZ_OUT', 'B', [(21.85, 20.6), (21.17, 20.6), 'D123.2']),
    ('BUZZ_OUT', 'B', [(21.85, 20.6), (21.85, 17.25), 'Q123.3']),
    ('PULLPIN_EXT', 'F', ['J123.1', (8.375, 14.45)]),
    ('PULLPIN_EXT', 'B', [(8.375, 14.45), (8.375, 10.57), 'R160.1']),
    ('SERVO1_OUT', 'B', ['J122.1', 'R150.2']),
    ('SERVO2_OUT', 'B', ['J122.4', 'R151.2']),
    ('SERVO3_OUT', 'B', ['J122.7', 'R152.2']),
    ('SERVO4_OUT', 'B', ['J122.10', 'R153.2']),
    ('CAM_5V_SENSE', 'F', ['C94.1', (40.73, 49.2), 'R105.1']),
    ('CAM_5V_SENSE', 'F', ['R105.1', (40.43, 49.11), (39.57, 48.25), 'R104.2']),
    ('CAM_5V_SENSE', 'F', ['R104.2', (38.97, 47.8)]),
    ('CAM_5V_SENSE', 'B', [(38.97, 47.8), (33.37, 53.4)]),
    ('CAM_5V_SENSE', 'F', [(33.37, 53.4), (31.67, 55.1)]),
    ('CAM_5V_SENSE', 'B', [(31.67, 55.1), (31.67, 44.4)]),
    ('CAM_5V_SENSE', 'F', [(31.67, 44.4), (31.57, 44.5), 'U1.35']),
    ('GPS_FAULT_N', 'F', ['R412.1', 'U1.57']),
    ('GPS_FAULT_N', 'F', ['R412.1', (26.9, 32.525)]),
    ('GPS_FAULT_N', 'B', [(26.9, 32.525), (26.9, 15.725)]),
    ('GPS_FAULT_N', 'F', [(26.9, 15.725), (26.9, 14.725), (30.2, 11.425), (31.3, 11.425)]),
    ('GPS_FAULT_N', 'B', [(31.3, 11.425), (31.3, 9.05), 'U410.4']),
    ('GPS_PWR_EN', 'F', ['U1.61', (24, 34.35), (24.9, 33.45), (24.9, 28.25)]),
    ('GPS_PWR_EN', 'B', [(24.9, 28.25), (24.9, 14.45)]),
    ('GPS_PWR_EN', 'F', [(24.9, 14.45), (27.2, 12.15)]),
    ('GPS_PWR_EN', 'B', [(27.2, 12.15), (27.2, 9.05), 'U410.3']),
    ('RADIO_FAULT_N', 'F', ['U1.56', (26.5, 34.15), (27.4, 33.25), 'R422.1']),
    ('RADIO_FAULT_N', 'F', ['R422.1', (28.7, 28.425), (32.3, 24.825), (32.3, 24.5)]),
    ('RADIO_FAULT_N', 'B', [(32.3, 24.5), 'U420.4']),
    ('RADIO_PWR_EN', 'F', ['U1.55', (27, 34.35), (28, 33.35), (28, 29.45)]),
    ('RADIO_PWR_EN', 'B', [(28, 29.45), (27.35, 28.8), (27.35, 25.45), 'U420.3']),
    ('V3V3_SENSE', 'F', ['U1.18', (25.5, 51.55)]),
    ('V3V3_SENSE', 'B', [(25.5, 51.55), (22.6, 54.45), (20.42, 54.45), 'R63.1']),
    ('V3V3_SENSE', 'B', ['R62.2', 'R63.1']),
    ('BUZZ_DRV', 'F', ['U1.8', (20.5, 48.75), (21.8, 47.45), (21.8, 37.95), (23.1, 36.65)]),
    ('BUZZ_DRV', 'B', [(23.1, 36.65), (20.3, 33.85)]),
    ('BUZZ_DRV', 'F', [(20.3, 33.85), (20.3, 33.05), (17.8, 30.55)]),
    ('BUZZ_DRV', 'B', [(17.8, 30.55), (16.8, 29.55), (16.8, 18.85), 'R162.1']),
    ('PULLPIN', 'F', [(20.05, 51.0), (20.05, 46.2), (21.4, 44.85), (21.4, 42.15), (20.4, 41.15)]),
    ('PULLPIN', 'B', [(20.4, 41.15), (13.3, 41.15), (10.8, 38.65), (10.8, 37.55), (5, 31.75), (5, 23), 'D122.3']),
    ('PULLPIN', 'B', ['D122.3', (11, 13.58), 'C160.1']),
    ('PULLPIN', 'B', ['C160.1', 'R160.2']),
    ('PULLPIN', 'B', ['R160.2', (13, 11.43), 'R161.2']),
]
AUTO_VIAS = [
    ('BUZZ_OUT', (21.85, 20.6)),
    ('PULLPIN_EXT', (8.375, 14.45)),
    ('CAM_5V_SENSE', (38.97, 47.8)),
    ('CAM_5V_SENSE', (33.37, 53.4)),
    ('CAM_5V_SENSE', (31.67, 55.1)),
    ('CAM_5V_SENSE', (31.67, 44.4)),
    ('GPS_FAULT_N', (26.9, 32.525)),
    ('GPS_FAULT_N', (26.9, 15.725)),
    ('GPS_FAULT_N', (31.3, 11.425)),
    ('GPS_PWR_EN', (24.9, 28.25)),
    ('GPS_PWR_EN', (24.9, 14.45)),
    ('GPS_PWR_EN', (27.2, 12.15)),
    ('RADIO_FAULT_N', (32.3, 24.5)),
    ('RADIO_PWR_EN', (28, 29.45)),
    ('V3V3_SENSE', (25.5, 51.55)),
    ('BUZZ_DRV', (23.1, 36.65)),
    ('BUZZ_DRV', (20.3, 33.85)),
    ('BUZZ_DRV', (17.8, 30.55)),
    ('PULLPIN', (20.4, 41.15)),
]
# ---- end AUTO ----


def draw(d):
    uarts(d)
    io_rails(d)
    port_wires(d)
    camera_control(d)
    gps_oe(d)
    servo_cell(d)
    gnd_joins(d)
    for net, layer, pts in AUTO_TRACKS:
        d.track(net, layer, S, [d.pad(p) if isinstance(p, str) else p for p in pts])
    for net, at in AUTO_VIAS:
        d.via(net, at)
