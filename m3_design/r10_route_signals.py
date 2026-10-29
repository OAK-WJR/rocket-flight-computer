"""R10 signal copper, all hand-drawn: the external-port UARTs and IO rails, then every non-critical signal.

Hand-routed (AGENTS 3): GPS and radio connect directly through 1k resistors and ESD clamps to their always-on
external terminals. The radio crosses the GPS lanes on B.Cu and its reversed terminal order by a second local
TX hop, with a GND via within 1.5 mm of each UART layer change. Camera isolation and IO supply remain local.
AUD-2: fast UART layer changes retain their GND partners. Slow EN / FAULT / OE controls keep their copper but no
longer require partner vias or one In2 region per chain; the redundant partners are removed.

Every other signal is a deliberate hand-drawn polyline (R10_DECISIONS D-R2-08 / D-R2-09), grouped by cell; the design
aid's earlier frozen table (m3_design/r10_aid/ncroute.py) served only as a sketch of feasible paths.
"""
S, IO = 0.2, 0.3        # signal width; IO rail trunk width (bottom)
# This former control partner also joins the F.Cu GND pour island, so it remains a general stitch (AUD-2).
PORT_CONTROL_GND = ((25.7, 30.6),)


def uarts(d):
    t, p, via = d.track, d.pad, d.via
    t('GPS_RX_MCU', 'F', S, [p('U1.64'), (22.5, 28.1), (33.2, 17.4), (33.2, 13.2), p('R440.2')])
    t('GPS_TX_MCU', 'F', S, [p('U1.63'), (23.0, 28.35), (33.7, 17.65), (33.7, 14.55), p('R441.1')])
    t('RADIO_RX_MCU', 'F', S, [p('U1.51'), (29.0, 33.5), (24.7, 29.2), (23.6, 29.2)])
    t('RADIO_TX_MCU', 'F', S, [p('U1.52'), (28.5, 33.8), (24.6, 29.9), (23.6, 29.9)])
    for net, y in (('RADIO_RX_MCU', 29.2), ('RADIO_TX_MCU', 29.9)):
        x = 21.8 if net == 'RADIO_RX_MCU' else 21.5
        t(net, 'B', S, [(23.6, y), (x, y)])
        via(net, (23.6, y)); via(net, (x, y))
    t('RADIO_RX_MCU', 'F', S, [(21.8, 29.2), (18.8, 26.2), (18.8, 25.0), (15.05, 21.25), p('R450.2')])
    # R451 sits on B.Cu where the second forced hop (under the USB / RX lanes) lands, so the MCU net keeps three vias
    # (its pads are on both layers) and the wire net one.
    t('RADIO_TX_MCU', 'F', S, [(21.5, 29.9), (19.2, 27.6), (18.1, 27.6)])
    t('RADIO_TX_MCU', 'B', S, [(18.1, 27.6), p('R451.1')])
    via('RADIO_TX_MCU', (18.1, 27.6))
    t('RADIO_TX_WIRE', 'B', S, [p('R451.2'), (11.9, 18.5)])
    via('RADIO_TX_WIRE', (11.9, 18.5))
    for at in ((21.6, 28.1), (22.0, 30.5), (24.0, 28.6), (18.1, 28.5), (10.9, 19.0)):
        via('GND', at)

def io_rails(d):
    t, p, via = d.track, d.pad, d.via
    # Camera: U13 -> C93 -> C92 -> R103 on B.Cu, U12's VCCB through a via under it.
    net = 'CAM_IO_3V3'
    t(net, 'B', IO, [p('U13.5'), (35.6, 42.45), p('C93.1')])        # node at the VCCB via: C93 is U12.7's bypass (D-R2-11)
    t(net, 'B', IO, [p('C93.1'), (34.675, 44.025), p('C92.1')])
    t(net, 'B', IO, [p('C92.1'), (35.72, 46.02), (40.695, 46.02), p('R103.1')])
    t(net, 'F', S, [p('U12.7'), (35.45, 41.75), (35.6, 41.9)])
    via(net, (35.6, 41.9))
    t(net, 'B', IO, [(35.6, 41.9), (35.6, 42.45)])

def port_wires(d):
    t, p, via = d.track, d.pad, d.via
    t('GPS_RX_WIRE', 'F', S, [p('R440.1'), p('D411.1'), p('J410.4')])
    t('GPS_TX_WIRE', 'F', S, [p('R441.2'), (35.3, 14.6), (35.3, 13.75), p('D410.1'), p('J410.3')])
    t('RADIO_RX_WIRE', 'F', S, [p('R450.1'), p('D421.1'), p('J420.4')])
    t('RADIO_TX_WIRE', 'F', S, [(11.9, 18.5), (11.9, 17.75), p('D420.1'), p('J420.3')])
    for diode, at in (('D410', (35.85, 13.1)), ('D411', (36.5, 8.9)),
                      ('D420', (10.0, 16.0)), ('D421', (10.0, 19.8))):
        t('GND', 'F', S, [p(f'{diode}.2'), at])
        via('GND', at)

def camera_control(d):
    """U1's east pins to the camera buffer U12 and switch U402 (R10_DECISIONS D-R3-B2). U1 orders FAULT_N, PWR_EN, OE,
    TX, RX from the top; U12's west face orders RX (pin 4, top row), TX (pin 5, bottom row). OE enters U12.6 from
    between the pad rows (west of TX's pin 5 and under RX's pin 4), so OE and TX stay on F.Cu without crossing; only
    RX, the southern pin with the northern pad, crosses OE and TX: one B.Cu hop in the channel between USB_LIMITED
    (x 31.8) and R431 / C93. The enable drops to B.Cu once beside its pin (its pull-down R431 and U402.3 are bottom
    parts); GND vias G1 / G3 sit within 1.5 mm of the hop's and the enable's layer changes (AGENTS 3)."""
    t, p, via = d.track, d.pad, d.via
    t('CAM_MCU_RX', 'F', S, [p('U1.37'), (32.3, 43.5), (32.5, 43.7)])
    t('CAM_MCU_RX', 'B', S, [(32.5, 43.7), (32.5, 40.35), (33.65, 39.2)])
    t('CAM_MCU_RX', 'F', S, [(33.65, 39.2), (34.45, 38.4), p('U12.4')])
    for at in ((32.5, 43.7), (33.65, 39.2)):
        via('CAM_MCU_RX', at)
    t('CAM_MCU_TX', 'F', S, [p('U1.38'), (34.1, 43.0), (34.1, 41.25), p('U12.5')])
    t('CAM_UART_OE', 'F', S, [p('U12.6'), p('R102.1')])
    t('CAM_UART_OE', 'F', S, [p('U1.39'), (33.7, 42.5), (33.7, 40.2), (34.95, 40.2), p('U12.6')])
    t('CAM_PWR_EN', 'F', S, [p('U1.41'), (33.15, 41.5)])
    via('CAM_PWR_EN', (33.15, 41.5))
    t('CAM_PWR_EN', 'B', S, [(33.15, 41.5), (33.9, 40.75), (33.9, 40.1), (34.6, 40.1), p('R431.1')])
    t('CAM_PWR_EN', 'B', S, [p('R431.1'), (35.675, 38.15), p('U402.3')])
    for at in ((33.2, 43.85), (33.15, 40.55)):
        via('GND', at)          # CAM_MCU_RX fast return partners; slow-only FAULT_N partner removed (AUD-2)
    t('CAM_FAULT_N', 'F', S, [p('U1.42'), (32.6, 41.0), (32.6, 38.825), (33.1, 38.825),
                               (33.9, 38.025), (33.9, 36.825)])
    t('CAM_FAULT_N', 'F', S, [p('R432.1'), (32.6, 38.825)])  # axial entry clears the opposite 0402 pad
    via('CAM_FAULT_N', (33.9, 36.825))
    t('CAM_FAULT_N', 'B', S, [(33.9, 36.825), (37.575, 36.825), p('U402.4')])

def gps_oe(d):
    """No GPS translator or OE remains after the always-on-port decision."""
    pass

def gnd_joins(d):
    """GND pads the signal copper boxes in, joined by hand (the fan-out aid runs after this family)."""
    t, p, via = d.track, d.pad, d.via
    t('GND', 'B', S, [(21.28, 53.65), (21.82, 53.65)])           # R63's GND pad onto C14's GND strap (core table)
    # Circuit pass: U1.49's former 1.8 mm GND stub into the F.Cu pour is gone (the fill no longer reaches it; the pad joins
    # the pour directly).
    t('GND', 'F', S, [p('U12.2'), (35.45, 36.6)])                # into C100's GND pad (its own via)
    # C93 (U13's output capacitor) returns straight to U13's GND pin: a short strap between the two pads, east under
    # U12 and down the gap between U13's pin columns (its pad is boxed in on three sides, D-R2-09).
    t('GND', 'B', IO, [p('C93.2'), (37.0, 40.9), (37.6, 41.5), (37.6, 43.4), p('U13.2')])
    # AUD-1: small C92 returns to the existing UART GND partner, without another via.
    t('GND', 'B', IO, [p('C92.2'), (33.2, 44.9), (33.2, 43.85)])

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
    t('SERVO1_MCU', 'B', S, [p('R154.1'), (20.4, 73.215), p('R150.1')])
    t('SERVO1_MCU', 'B', S, [(20.4, 72.55), p('D121.1')])
    t('SERVO2_MCU', 'B', S, [(22.7, 66.2), (22.7, 73.455), p('R151.1')])
    t('SERVO2_MCU', 'B', S, [(22.7, 69.03), p('R155.1')])
    t('SERVO2_MCU', 'B', S, [(22.7, 70.65), p('D121.3')])
    t('SERVO3_MCU', 'B', S, [(23.3, 66.7), (23.3, 73.455), p('R152.1')])
    t('SERVO3_MCU', 'B', S, [(23.3, 69.03), p('R156.1')])
    t('SERVO3_MCU', 'B', S, [(23.3, 70.65), p('D121.4')])
    t('SERVO4_MCU', 'B', S, [(25.7, 66.4), p('R157.1')])
    t('SERVO4_MCU', 'B', S, [p('R157.1'), (25.7, 73.315), p('R153.1')])
    t('SERVO4_MCU', 'B', S, [(25.7, 72.55), p('D121.6')])
    t('GND', 'B', IO, [p('D121.2'), (21.05, 71.6)])                # hole / ring clear of R123.2's mask / paste (top)
    via('GND', (21.05, 71.6))
    t('3V3', 'B', IO, [p('D121.5'), (25.05, 71.6)])
    via('3V3', (25.05, 71.6))


def arm_sense(d):
    t, p, via = d.track, d.pad, d.via
    t('ARM1_SENSE', 'B', S, [p('C129.1'), (27.2, 58.75)])
    via('ARM1_SENSE', (27.2, 58.75))
    # F.Cu (R10_DECISIONS D-R2-09): one 45 deg run parallel to the servo lanes, north as the inner sense lane x 34.4
    # (outside the status-line vias at U1's east pins), west directly into U1.33.
    t('ARM1_SENSE', 'F', S, [(27.2, 58.75), (34.4, 51.55), (34.4, 46.2), (32.13, 46.2), (31.43, 45.5), p('U1.33')])



def east_lanes(d):
    """U1's east-side status and supply-sense lines (R10_DECISIONS D-R2-09). The pyro sense lanes (pyro family) leave
    U1.33 / U1.34 through R170 / R172 and run south at x 34.4 / 35.1. The three lines from U1.28-30 escape straight
    east inside them, drop through one via each east of the USB_LIMITED run and cross under the sense lanes on B.Cu:
    VLOGIC_SENSE (PA6) and BAT_FAULT_N (PA5) straight east under C92's body (between its pads), to the VLOGIC divider
    and to BAT_FAULT_N's F.Cu column x 37.0; LOGIC_SOURCE_ST (PA4) straight south to U11.9, taking its pull-up R91 and
    its pull-up R91. BAT_FAULT_N's column takes its pull-up R89, passes C82 and runs
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
    t('BAT_FAULT_N', 'F', S, [(37.0, 47.9), (37.0, 53.8), (38.0, 54.8), (38.0, 68.2), (37.0, 69.2), (37.0, 74.0)])
    t('BAT_FAULT_N', 'F', S, [(37.0, 53.8), (35.875, 53.8), p('R89.2')])
    via('BAT_FAULT_N', (37.0, 74.0))
    t('BAT_FAULT_N', 'B', S, [(37.0, 74.0), (37.0, 78.9), (38.1, 78.9)])
    # LOGIC_SOURCE_ST (PA4)
    t('LOGIC_SOURCE_ST', 'F', S, [p('U1.28'), (32.65, 48.0), (32.95, 48.3)])
    via('LOGIC_SOURCE_ST', (32.95, 48.3))
    t('LOGIC_SOURCE_ST', 'B', S, [(32.95, 48.3), (32.95, 57.0), (33.8, 57.85), p('U11.9')])
    t('LOGIC_SOURCE_ST', 'B', S, [(32.95, 54.85), p('R91.2')])


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
    t, p, via = d.track, d.pad, d.via
    t('CAM_RX_BUFFER', 'F', S, [p('U12.1'), p('R100.2')])
    t('CAM_TX_BUFFER', 'F', S, [p('R101.1'), p('U12.8')])
    t('CAM_RX_WIRE', 'F', S, [p('R100.1'), (39.4, 36.15), (42.0, 36.15), (43.0, 37.15), (43.0, 57.75), p('J9.3')])
    t('CAM_RX_WIRE', 'F', S, [p('D401.1'), (43.0, 38.625)])
    t('CAM_TX_WIRE', 'F', S, [p('R101.2'), (38.8, 42.55), p('D400.1')])
    t('CAM_TX_WIRE', 'F', S, [p('D400.1'), (42.0, 40.275), (42.0, 53.75), p('J9.4')])

def port_control(d):
    """GPS/radio power switches, fault flags and translator enables were removed."""
    pass

def leds(d):
    """Local status cell clears the SPI3/SWD escapes and retained IMU supply vias."""
    t, p = d.track, d.pad
    t('LED_RED', 'F', S, [p('U1.86'), (13.7, 42.0), p('R32.1')])
    t('LED_RED_A', 'F', S, [p('R32.2'), (10.3, 42.6), p('LED1.2')])
    t('LED_YEL', 'F', S, [p('U1.88'), (14.4, 43.0), (14.1, 42.7),
                         (12.4, 42.7), (11.6, 43.5), (11.6, 43.9), p('R33.1')])
    t('LED_YEL_A', 'F', S, [p('R33.2'), (9.9, 45.0), p('LED2.1')])
    # Reuse the existing C32 GND via; it is already connected to the solid In1 plane.
    t('GND', 'F', S, [p('LED1.1'), (8.1, 44.18), (8.72, 44.8)])
    t('GND', 'F', S, [p('LED2.2'), (6.5, 46.5)])
    d.via('GND', (6.5, 46.5))


def buzzer(d):
    """The driver passes the SPI3 fan, USB supply and UART bundles by explicit hops."""
    t,p,via=d.track,d.pad,d.via
    t('BUZZ_DRV','F',S,[p('U1.8'),(20.5,48.75),(21.8,47.45),(21.8,37.95),(23.1,36.65)])
    via('BUZZ_DRV',(23.1,36.65))
    # Two hops carry the driver over the USB_LIMITED B.Cu run (y 33.45) between the U1 pad row and that run.
    t('BUZZ_DRV','B',S,[(23.1,36.65),(25.7,34.05),(26.5,34.05)]);via('BUZZ_DRV',(26.5,34.05))
    t('BUZZ_DRV','F',S,[(26.5,34.05),(26.5,32.6)]);via('BUZZ_DRV',(26.5,32.6))
    t('BUZZ_DRV','B',S,[(26.5,32.6),(26.5,28.0)]);via('BUZZ_DRV',(26.5,28.0))
    t('BUZZ_DRV','F',S,[(26.5,28.0),(27.95,26.55),(27.95,25.5)]);via('BUZZ_DRV',(27.95,25.5))
    t('BUZZ_DRV','B',S,[(27.95,25.5),(27.95,21.9)]);via('BUZZ_DRV',(27.95,21.9))
    t('BUZZ_DRV','F',S,[(27.95,21.9),(27.95,17.8),(14.2,17.8)]);via('BUZZ_DRV',(14.2,17.8))
    t('BUZZ_DRV','B',S,[(14.2,17.8),(14.2,15.8),p('R162.1')])
    t('BUZZ_G','B',S,[p('R163.1'),(17.0,13.63),p('R162.2')])
    t('GND','B',S,[p('R163.2'),(17.6,11.4)]);via('GND',(17.6,11.4))
    t('BUZZ_G','B',S,[p('R162.2'),(17.0,15.3),(18.65,16.95),p('Q123.1')])
    t('BUZZ_OUT','F',S,[p('LS120.2'),(21.85,20.6)]);via('BUZZ_OUT',(21.85,20.6))
    t('BUZZ_OUT','B',S,[p('Q123.3'),(21.85,20.6)])
    t('BUZZ_OUT','B',S,[p('Q123.3'),(22.6,16.0),(22.8,15.8)]);via('BUZZ_OUT',(22.8,15.8))
    t('BUZZ_OUT','F',S,[(22.8,15.8),(25.5,15.8),(26.3,15.0),p('D123.2')])
    t('3V3','F',S,[p('D123.1'),(24.0,15.0),(23.0,14.0)]);via('3V3',(23.0,14.0))
    t('3V3','B',S,[(23.0,14.0),(23.0,14.775),p('R461.2')])
    via('GND',(22.3,13.5))


def servo_out(d):
    """Four protected signal outputs to the five-position screw terminal; motor power stays in the harness."""
    for i in range(1, 5):
        start, end = d.pad(f'R{149+i}.2'), d.pad(f'J122.{i}')
        # Distinct terminal pitch is legalized by one 45-degree fan-out followed by a straight pin entry.
        turn = (end[0], start[1] + abs(end[0] - start[0]))
        d.track(f'SERVO{i}_OUT', 'B', S, [start, turn, end])


def draw(d):
    import r10_route_sd
    r10_route_sd.draw(d)
    uarts(d)
    io_rails(d)
    port_wires(d)
    camera_control(d)
    gps_oe(d)
    servo_lanes(d)
    servo_cell(d)
    east_lanes(d)
    arm_sense(d)
    south_sense(d)
    cam_sense(d)
    port_links(d)
    port_control(d)
    leds(d)
    buzzer(d)
    servo_out(d)
    gnd_joins(d)
