"""R11 family `core` (stage C1): U1's TFBGA-100 fan-out and the MCU's own circuit (r11_plan.md section 4; stageC1.md).

Explicit tables only (D-R11-07): every via, stub and polyline is written here; the build never searches. Coordinates are
board mm (x east, y forward from the aft edge), F / In3 / B the signal layers (In1 / In4 GND and In2 power are poured by
the later families). U1 sits at (24, 28): ball column c is at x = 20.4 + 0.8 (c - 1), row r (A..K, no I) at
y = 24.4 + 0.8 r. A dog-bone via sits at an interstitial site (x 20.8 + 0.8 i, y 24.8 + 0.8 j), 0.566 mm from its four
balls; the sites under the bottom decoupling (C13-C16, C18, C19 / C20) are closed to vias (stageC1.md section 2; C17,
C21 and R5 left the field in stage C1b, D-R11-43). I2C, NRST, BOOT0 and QSPI_NCS are drawn from r11_escape.py (D-R11-44).
"""

# Every net this family completes (r11_stage_check: these may not stay unconnected or fail route_check after `core`).
NETS = ('HSE_IN', 'HSE_OUT', 'NRST', 'BOOT0', 'VCAP1', 'VCAP2', 'SWDIO', 'SWCLK', 'I2C1_SCL', 'I2C1_SDA', 'BARO_SDO',
        'IMU_CS', 'SPI1_SCK', 'SPI1_MISO', 'SPI1_MOSI', 'IMU_INT1', 'QSPI_CLK', 'QSPI_IO0', 'QSPI_IO1', 'QSPI_IO2',
        'QSPI_IO3', 'QSPI_NCS')    # QSPI_NCS: D-R11-49

SIG = 0.1          # signal width: one track between two 0.4 mm lands at 0.8 mm pitch (0.15 mm each side)
PWR = 0.2          # decoupling straps and power dog-bones


def ball(name):
    rows = 'ABCDEFGHJK'
    return (round(20.4 + 0.8 * (int(name[1:]) - 1), 4), round(24.4 + 0.8 * rows.index(name[0]), 4))


# ---- 1. Rails: dog-bones of the supply balls and the bottom decoupling straps (pending nets: In2 / In1 / In4 join them
# in stage C2 and the ground family). (net, balls, via, width) -------------------------------------------------------
RAIL_FANOUT = (
    ('3V3', ('B2',), (20.8, 24.8)),
    ('3V3', ('D2',), (20.8, 27.2)),
    ('3V3', ('F4', 'F5'), (23.2, 28.0)),
    ('3V3', ('F6', 'F7'), (24.8, 28.0)),
    ('3V3', ('K1',), (20.0, 32.0)),
    ('GND', ('C2',), (20.8, 25.6)),
    ('GND', ('E4',), (22.4, 28.0)),
    ('GND', ('G1',), (20.0, 29.6)),
    ('GND', ('J1',), (20.0, 31.2)),
    ('3V3A', ('H1',), (20.0, 30.4)),
)
# extra vias of the rails (no ball): decoupling pads' own vias and GND partners of critical layer changes
RAIL_VIAS = (
    ('3V3', (25.6, 30.4)),      # C18.1
    ('GND', (23.2, 26.4)),      # C20.2; QSPI_NCS partner
    ('GND', (26.4, 30.4)),      # C18.2
    ('GND', (18.95, 25.15)),    # Y1.2 / C25.2; HSE_IN partner
    ('GND', (19.0, 27.5)),      # HSE_OUT partner
    ('GND', (14.2, 26.85)),     # Y1.4
    ('GND', (18.0, 29.2)),      # C26.2
    # D-R11-43: the decoupling and pull-down moved out of the ball field get their own vias
    ('3V3', (29.88, 24.7)),     # C17.1
    ('GND', (30.72, 24.7)),     # C17.2
    ('3V3A', (18.57, 21.12)),   # C21.1 (In2 3V3A strip)
    ('GND', (19.45, 22.52)),    # C21.2 (D-R11-49: east of the pad, so CAM_5V_SENSE's In3 run leaves the field north)
    ('GND', (24.0, 31.2)),      # C19.2 (south cap), the J / K row site under C19's column
    ('GND', (29.27, 34.35)),    # R5.2
    ('GND', (27.2, 26.4)),      # D-R11-49: SD_MOSI's dog-bone (27.2, 25.6) partner (BOOT0's old via site)
)
# (net, layer, width, points) straps on B (and the E-row GND link on F)
RAIL_TRACKS = (
    ('GND', 'F', SIG, [(24.4, 27.6), (23.6, 27.6), (22.8, 27.6)]),          # E6 - E5 - E4 (E4's via joins all three)
    ('3V3', 'B', PWR, [(20.8, 24.8), (21.2, 25.2), (21.58, 25.2)]),         # C13.1
    ('3V3', 'B', PWR, [(20.8, 27.2), (21.2, 26.8), (21.58, 26.8)]),         # C15.1
    ('GND', 'B', PWR, [(22.4, 25.2), (22.4, 26.8), (22.4, 28.0)]),           # C13.2, C15.2 to E4's via
    ('GND', 'B', PWR, [(24.0, 26.0), (23.6, 26.0), (23.2, 26.4)]),          # C20.2 (north cap)
    ('3V3', 'B', PWR, [(25.6, 29.2), (25.6, 30.4)]),                        # C18.1
    ('GND', 'B', PWR, [(26.4, 29.2), (26.4, 30.4)]),                        # C18.2
    ('GND', 'B', PWR, [(17.02, 23.4), (17.02, 23.9), (17.7, 24.58), (17.7, 25.15), (18.95, 25.15)]),  # C25.2, Y1.2
    ('GND', 'B', PWR, [(15.5, 26.85), (14.2, 26.85)]),                      # Y1.4
    ('GND', 'B', PWR, [(17.02, 28.6), (17.4, 28.6), (18.0, 29.2)]),         # C26.2
    ('3V3', 'B', PWR, [(29.88, 25.3), (29.88, 24.7)]),                      # C17.1
    ('GND', 'B', PWR, [(30.72, 25.3), (30.72, 24.7)]),                      # C17.2
    ('3V3A', 'F', PWR, [(18.85, 21.68), (18.57, 21.4), (18.57, 21.12)]),     # C21.1
    ('GND', 'F', PWR, [(18.85, 22.52), (19.45, 22.52)]),                     # C21.2
    ('GND', 'B', PWR, [(24.0, 30.15), (24.0, 31.2)]),                       # C19.2
    ('GND', 'B', PWR, [(28.82, 33.9), (29.27, 34.35)]),                     # R5.2
)


def stub(d, net, b, via, width):
    d.track(net, 'F', width, [d.pad('U1', b, net=net, at=ball(b)), via])


def rails(d):
    for net, balls, via in RAIL_FANOUT:
        d.via(net, via)
        for b in balls:
            stub(d, net, b, via, PWR)
    for net, via in RAIL_VIAS:
        d.via(net, via)
    for net, layer, width, pts in RAIL_TRACKS:
        d.track(net, layer, width, pts)


# ---- 2. Crystal, reset, BOOT0 and the VCAP pair -----------------------------------------------------------------------
J2_SOUTH, J2_NORTH = 40.4, 38.8   # track ends inside J2's pads but outside its keep-out strip (y 38.965 ... 40.235)
HSE = 0.15         # crystal nets: short B runs to Y1 / C25 / C26 (R10's 0.15 mm HSE width class)


def mcu_local(d):
    # HSE: C1 / D1 escape west to vias outside the field; on B the two nets run either side of the 0.5 mm gap between
    # Y1's pad rows (HSE_IN along y 26.0, HSE_OUT into Y1.3), each load cap on its own side; GND vias (20.8, 25.6),
    # (18.95, 25.15) and (19.0, 27.5) are their partners (AGENTS section 3, 1.5 mm).
    d.via('HSE_IN', (20.0, 25.6))
    stub(d, 'HSE_IN', 'C1', (20.0, 25.6), HSE)
    d.track('HSE_IN', 'B', HSE, [(20.0, 25.6), (19.6, 26.0), (16.35, 26.0), d.pad('Y1.1', net='HSE_IN')])
    d.track('HSE_IN', 'B', HSE, [d.pad('Y1.1'), (15.5, 24.08), d.pad('C25.1', net='HSE_IN')])
    d.via('HSE_OUT', (20.0, 27.2))
    stub(d, 'HSE_OUT', 'D1', (20.0, 27.2), HSE)
    d.track('HSE_OUT', 'B', HSE, [(20.0, 27.2), (19.65, 26.85), d.pad('Y1.3', net='HSE_OUT')])
    d.track('HSE_OUT', 'B', HSE, [d.pad('Y1.3'), (16.18, 28.37), d.pad('C26.1', net='HSE_OUT')])
    # NRST and BOOT0: the escape plan's (r11_escape.py, stageC1b.md, D-R11-44)
    # VCAP: E7 -> (24.8, 27.2) -> C20.1 (north cap); F8 -> (25.6, 28.0) -> C19.1 (south cap) (D-R11-15 swap)
    d.via('VCAP2', (24.8, 27.2))
    stub(d, 'VCAP2', 'E7', (24.8, 27.2), PWR)
    d.track('VCAP2', 'B', PWR, [(24.8, 27.2), (24.0, 27.2)])
    d.pad('C20.1', net='VCAP2', at=(24.0, 27.25))
    d.via('VCAP1', (25.6, 28.0))
    stub(d, 'VCAP1', 'F8', (25.6, 28.0), PWR)
    d.track('VCAP1', 'B', 0.15, [(25.6, 28.0), (24.85, 28.75), d.pad('C19.1', net='VCAP1')])
    # D-R11-34 (O-C2-12): F8's second barrel at its NE site, joined to the first on F.Cu (through the ball) and B.Cu, so
    # one open barrel leaves C19 on VCAP1 (check_r11 K-power single-open taps; r11_gate_data.json parallel_vias)
    d.via('VCAP1', (26.4, 28.0))
    stub(d, 'VCAP1', 'F8', (26.4, 28.0), PWR)
    d.track('VCAP1', 'B', PWR, [(26.4, 28.0), (25.6, 28.0)])


# ---- 3. SWD: A9 / A10 north to vias, B.Cu east along the aft edge of the field and down the free column x 32.0 / 32.35
# under U3 (between the B.Cu USB / VBUS column x <= 31.52 and U10 / D4 x >= 33.05), vias beside J2.2 / J2.4.
def swd(d):
    # D-R11-44: both leave the field on its east side (exit E, J2 lies south-east): SWCLK's via north of A9, B.Cu east
    # along y 23.6; SWDIO's via at A10's north-east outer site, B.Cu east along y 24.0 (north of QSPI_IO2's y 24.4 run)
    d.via('SWCLK', (26.8, 23.6))
    stub(d, 'SWCLK', 'A9', (26.8, 23.6), SIG)
    d.track('SWCLK', 'B', SIG, [(26.8, 23.6), (31.95, 23.6), (32.35, 24.0), (32.35, 37.25), (32.9, 37.8)])
    d.via('SWCLK', (32.9, 37.8))
    d.pad('J2.4', net='SWCLK', at=(32.9, 38.965))
    d.track('SWCLK', 'F', SIG, [(32.9, 37.8), (32.9, J2_NORTH)])
    d.via('SWDIO', (28.0, 24.0))
    stub(d, 'SWDIO', 'A10', (28.0, 24.0), SIG)
    d.track('SWDIO', 'B', SIG, [(28.0, 24.0), (31.6, 24.0), (32.0, 24.4), (32.0, 37.43), (31.63, 37.8)])
    d.via('SWDIO', (31.63, 37.8))
    d.pad('J2.2', net='SWDIO', at=(31.63, 38.965))
    d.track('SWDIO', 'F', SIG, [(31.63, 37.8), (31.63, J2_NORTH)])


# ---- 4. QSPI flash U3 (SOIC-8 at (32.2, 30.5), pins 5-8 aft row y 26.97, 1-4 forward row y 34.03). Under U3's body on
# F.Cu, north to south: IO3 (y 28.35, to pin 7's south end), CLK (28.8, pin 6), IO0 (29.6, pin 5), IO2 (30.6, pin 3's
# north end), IO1 (31.6, pin 2); NCS enters pin 1 from the via south-west of it. CLK / IO0 / IO1 have no via.
def qspi(d):
    # CLK G5: F channel y 28.8 between rows F and G, out between F10 / G10
    d.track('QSPI_CLK', 'F', SIG, [d.pad('U1', 'G5', net='QSPI_CLK'), (24.0, 28.8), (32.23, 28.8), (32.83, 28.2),
                                   (32.83, 27.6)])
    d.pad('U3.6', net='QSPI_CLK', at=(32.83, 26.97))
    # IO0 G9: F channel y 29.6 between G10 / H10
    d.track('QSPI_IO0', 'F', SIG, [d.pad('U1', 'G9', net='QSPI_IO0'), (27.2, 29.6), (33.1, 29.6), (34.1, 28.6),
                                   (34.1, 27.6)])
    d.pad('U3.5', net='QSPI_IO0', at=(34.1, 26.97))
    # IO1 K10: F east along row K, into pin 2's north end
    d.track('QSPI_IO1', 'F', SIG, [d.pad('U1', 'K10', net='QSPI_IO1'), (30.97, 31.6), (31.57, 32.2), (31.57, 33.4)])
    d.pad('U3.2', net='QSPI_IO1', at=(31.57, 34.03))
    # IO3 J10: dog-bone east, In3 hop north over the CLK / IO0 lanes, F under U3 to pin 7's south end
    d.via('QSPI_IO3', (28.0, 30.4))
    stub(d, 'QSPI_IO3', 'J10', (28.0, 30.4), SIG)
    d.track('QSPI_IO3', 'In3', SIG, [(28.0, 30.4), (28.4, 30.0), (28.4, 28.35)])
    d.via('QSPI_IO3', (28.4, 28.35))
    d.track('QSPI_IO3', 'F', SIG, [(28.4, 28.35), (31.37, 28.35), (31.57, 28.15), (31.57, 27.6)])
    d.pad('U3.7', net='QSPI_IO3', at=(31.57, 26.97))
    # IO2 A3: dog-bone north-west, B.Cu east along y 24.4 (under row A, between the via rows) and south down x 29.0, F under U3
    # D-R11-49: the via sits on A3's own column north of row A (was (21.6, 24.0)), so B3's F.Cu lane x 21.6 is free
    d.via('QSPI_IO2', (22.0, 23.6))
    stub(d, 'QSPI_IO2', 'A3', (22.0, 23.6), SIG)
    d.track('QSPI_IO2', 'B', SIG, [(22.0, 23.6), (22.8, 24.4), (28.6, 24.4), (29.0, 24.8), (29.0, 30.6)])
    d.via('QSPI_IO2', (29.0, 30.6))
    d.track('QSPI_IO2', 'F', SIG, [(29.0, 30.6), (32.23, 30.6), (32.83, 31.2), (32.83, 33.4)])
    d.pad('U3.3', net='QSPI_IO2', at=(32.83, 34.03))
    # NCS: the escape plan's (r11_escape.py, D-R11-44)
    for v in ((28.0, 31.2), (28.9, 33.0), (28.0, 27.2)):     # GND partners (AGENTS section 3)
        d.via('GND', v)


# ---- 5. IMU U4 (bottom, rotation 180: pins 12 CS / 13 SCK / 14 MOSI on its aft row, 1 MISO / 4 INT1 east column).
# MISO on B.Cu round the east; CS / SCK / MOSI on In3 straight under U4 to vias aft of its pins (one crossing-free
# order, W -> E CS, MOSI, SCK; SCK sweeps aft of MOSI's via); INT1 F north, B.Cu to pin 4 from the east.
def imu(d):
    # D-R11-49: MISO A6 on F.Cu straight up x 24.4 over U4 to a via east of pin 1 (no field-edge via); B.Cu into pin 1
    d.track('SPI1_MISO', 'F', SIG, [d.pad('U1', 'A6', net='SPI1_MISO'), (24.4, 19.9), (25.0, 19.3)])
    d.via('SPI1_MISO', (25.0, 19.3))
    d.track('SPI1_MISO', 'B', SIG, [(25.0, 19.3), (24.55, 19.75), d.pad('U4.1', net='SPI1_MISO')])
    # MOSI C5 on F.Cu up the lane x 24.0 over U4 to a via aft of pin 14. CS (B3) and INT1 (B6) are the escape plan's
    # (r11_escape.py, D-R11-49)
    d.track('SPI1_MOSI', 'F', SIG, [d.pad('U1', 'C5', net='SPI1_MOSI'), (24.0, 25.6), (24.0, 18.7)])
    d.via('SPI1_MOSI', (24.0, 18.7))
    d.track('SPI1_MOSI', 'B', SIG, [(24.0, 18.7), (24.0, 19.04), d.pad('U4.14', net='SPI1_MOSI')])
    # SCK A7: via north, In3 under the F channel and aft of MOSI's via to a via under pin 13 (the one crossing of the
    # three, U1's MOSI-SCK order being the reverse of U4's)
    d.via('SPI1_SCK', (25.2, 23.6))
    stub(d, 'SPI1_SCK', 'A7', (25.2, 23.6), SIG)
    # D-R11-49: diagonal under U4 to a via at (22.75, 18.3) (was (23.0, 18.25)), so CAM_MCU_RX's lane x 23.2 passes east of it
    d.track('SPI1_SCK', 'In3', SIG, [(25.2, 23.6), (24.6, 23.0), (24.6, 20.15), (22.75, 18.3)])
    d.via('SPI1_SCK', (22.75, 18.3))
    d.track('SPI1_SCK', 'B', SIG, [(22.75, 18.3), (23.0, 18.55), d.pad('U4.13', net='SPI1_SCK')])
    # U4 supply: pins 5 / 8 (3V3A) and C30 / C31 to their own vias (In2 3V3A), pins 2 / 3 and 6 / 7 (GND) to vias. F.Cu
    # over U4 carries LED1 / LED2 / R32 / R33, so every via sits clear of their pads.
    d.track('3V3A', 'B', PWR, [d.pad('U4.5', net='3V3A'), (23.5, 22.1), (23.6, 22.2)])
    d.via('3V3A', (23.6, 22.2))
    # D-R11-49: U4.8's via at (19.6, 21.25) (was (19.9, 21.0)), so CAM_PWR_EN's In3 run x 20.0 passes it straight
    d.track('3V3A', 'B', PWR, [d.pad('U4.8', net='3V3A'), (19.6, 21.25)])
    d.via('3V3A', (19.6, 21.25))
    d.track('GND', 'B', PWR, [d.pad('U4.6', net='GND'), d.pad('U4.7', net='GND'), (22.11, 21.85), (20.4, 21.85)])
    d.via('GND', (20.4, 21.85))
    d.track('GND', 'B', PWR, [d.pad('U4.2', net='GND'), (24.75, 20.25), (25.0, 20.5)])
    d.track('GND', 'B', PWR, [d.pad('U4.3', net='GND'), (24.75, 20.75), (25.0, 20.5)])
    d.via('GND', (25.0, 20.5))
    d.track('3V3A', 'B', PWR, [d.pad('C30.1', net='3V3A'), d.pad('C31.1', net='3V3A')])
    d.track('3V3A', 'B', PWR, [(26.75, 20.02), (26.75, 20.7)])
    d.via('3V3A', (26.75, 20.7))
    d.track('GND', 'B', PWR, [d.pad('C30.2', net='GND'), d.pad('C31.2', net='GND')])
    d.track('GND', 'B', PWR, [(26.75, 19.18), (26.75, 18.5)])
    d.via('GND', (26.75, 18.5))
    for v in ((24.8, 24.0), (21.6, 18.1), (24.6, 18.0)):     # GND partners (D-R11-49: (26.0, 23.1) dropped, A8's lane)
        d.via('GND', v)


# ---- 6. Barometer U5 (bottom, (9, 40)) and the I2C pair: SDA (A4) / SCL (B4) dog-bones, In3 west north of Y1's keep-out,
# south down x 13.2 / 13.75 (west of Y1), vias beside R13 / R12, then under U5 to vias south of its pads 7 / 8;
# BARO_SDO from R64 by In3 under U5 to a via south of pad 6.
def baro(d):
    # I2C1_SDA / I2C1_SCL: the escape plan's (r11_escape.py; D-R11-41 moved them to balls K7 / J7)
    d.via('BARO_SDO', (7.97, 36.0))
    d.track('BARO_SDO', 'B', SIG, [(7.97, 36.0), d.pad('R64.1', net='BARO_SDO')])
    d.track('BARO_SDO', 'In3', SIG, [(7.97, 36.0), (9.63, 37.66), (9.63, 42.7)])
    d.via('BARO_SDO', (9.63, 42.7))
    d.track('BARO_SDO', 'B', SIG, [(9.63, 42.7), (9.63, 41.825)])
    d.via('GND', (20.75, 23.05))                              # QSPI_IO2 dog-bone partner (D-R11-49; was (21.6, 23.2))


def draw(d):
    rails(d)
    mcu_local(d)
    swd(d)
    qspi(d)
    imu(d)
    baro(d)
    import r11_escape
    r11_escape.draw(d, 'core')
