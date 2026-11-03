"""R11 family `core` (stage C1): U1's TFBGA-100 fan-out and the MCU's own circuit (r11_plan.md section 4; stageC1.md).

Explicit tables only (D-R11-07): every via, stub and polyline is written here; the build never searches. Coordinates are
board mm (x east, y forward from the aft edge), F / In3 / B the signal layers (In1 / In4 GND and In2 power are poured by
the later families). U1 sits at (24, 28): ball column c is at x = 20.4 + 0.8 (c - 1), row r (A..K, no I) at
y = 24.4 + 0.8 r. A dog-bone via sits at an interstitial site (x 20.8 + 0.8 i, y 24.8 + 0.8 j), 0.566 mm from its four
balls; the sites under the bottom decoupling (C13-C18, C21, C19 / C20, R5) are closed to vias (stageC1.md section 2).
"""
import csv

from r11_route import ROOT

FANOUT = ROOT / 'm3_design/r11_fanout.tsv'

# Every net this family completes (r11_stage_check: these may not stay unconnected or fail route_check after `core`).
NETS = ('HSE_IN', 'HSE_OUT', 'NRST', 'BOOT0', 'VCAP1', 'VCAP2', 'SWDIO', 'SWCLK', 'I2C1_SCL', 'I2C1_SDA', 'BARO_SDO',
        'IMU_CS', 'SPI1_SCK', 'SPI1_MISO', 'SPI1_MOSI', 'IMU_INT1', 'QSPI_CLK', 'QSPI_NCS', 'QSPI_IO0', 'QSPI_IO1',
        'QSPI_IO2', 'QSPI_IO3')

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
    ('3V3', (21.6, 28.0)),      # C17.1
    ('3V3', (25.6, 30.4)),      # C18.1
    ('GND', (25.23, 32.4)),     # R5.2
    ('GND', (23.2, 26.4)),      # C20.2; QSPI_NCS partner
    ('GND', (26.4, 30.4)),      # C18.2
    ('GND', (22.0, 32.2)),      # C21.2
    ('GND', (18.95, 25.15)),    # Y1.2 / C25.2; HSE_IN partner
    ('GND', (19.0, 27.5)),      # HSE_OUT partner
    ('GND', (14.2, 26.85)),     # Y1.4
    ('GND', (18.0, 29.2)),      # C26.2
)
# (net, layer, width, points) straps on B (and the E-row GND link on F)
RAIL_TRACKS = (
    ('GND', 'F', SIG, [(24.4, 27.6), (23.6, 27.6), (22.8, 27.6)]),          # E6 - E5 - E4 (E4's via joins all three)
    ('3V3', 'B', PWR, [(20.8, 24.8), (21.2, 25.2), (21.58, 25.2)]),         # C13.1
    ('3V3', 'B', PWR, [(20.8, 27.2), (21.2, 26.8), (21.58, 26.8)]),         # C15.1
    ('3V3', 'B', PWR, [(21.6, 28.0), (21.6, 29.2)]),                        # C17.1
    ('GND', 'B', PWR, [(22.4, 25.2), (22.4, 26.8), (22.4, 28.0), (22.4, 29.2)]),  # C13.2, C15.2, C17.2 to E4's via
    ('GND', 'B', PWR, [(24.0, 26.0), (23.6, 26.0), (23.2, 26.4)]),          # C20.2 (north cap)
    ('3V3', 'B', PWR, [(25.6, 29.2), (25.6, 30.4)]),                        # C18.1
    ('GND', 'B', PWR, [(26.4, 29.2), (26.4, 30.4)]),                        # C18.2
    ('GND', 'B', SIG, [(24.0, 30.15), (24.38, 30.53), (24.38, 31.6)]),      # C19.2 (south cap) to R5.2
    ('GND', 'B', PWR, [(24.43, 31.6), (25.23, 32.4)]),                      # R5.2
    ('GND', 'B', PWR, [(22.42, 30.8), (22.42, 31.78), (22.0, 32.2)]),       # C21.2
    ('3V3A', 'B', SIG, [(20.0, 30.4), (20.4, 30.8), (21.58, 30.8)]),        # H1 to C21.1 (between the servo vias)
    ('GND', 'B', PWR, [(17.02, 23.4), (17.02, 23.9), (17.7, 24.58), (17.7, 25.15), (18.95, 25.15)]),  # C25.2, Y1.2
    ('GND', 'B', PWR, [(15.5, 26.85), (14.2, 26.85)]),                      # Y1.4
    ('GND', 'B', PWR, [(17.02, 28.6), (17.4, 28.6), (18.0, 29.2)]),         # C26.2
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
    # NRST: E1 west to its via; C24 on B beside it; the Tag-Connect pad J2.3 by In3 south of U1 (y 33.5) and a via
    # beside J2.3 (Tag-Connect contacts keep 0.508 mm from foreign copper)
    d.via('NRST', (19.6, 27.6))
    stub(d, 'NRST', 'E1', (19.6, 27.6), SIG)
    d.track('NRST', 'B', SIG, [(19.6, 27.6), (19.0, 28.2), (19.0, 28.48)])          # C24.1 (D-R11-27)
    d.track('NRST', 'In3', SIG, [(19.6, 27.6), (19.6, 33.1), (20.0, 33.5), (33.1, 33.5), (33.5, 33.9), (33.5, 40.7),
                                 (32.9, 41.3)])
    d.via('NRST', (32.9, 41.3))
    d.pad('J2.3', net='NRST', at=(32.9, 40.235))
    d.track('NRST', 'F', SIG, [(32.9, 41.3), (32.9, J2_SOUTH)])   # ends inside J2.3, outside J2's F.Cu keep-out strip
    # BOOT0: D5 to (23.2, 27.2); In3 straight down the via-free x 23.6 lane to a via beside R5; R5.1 on B
    d.via('BOOT0', (23.2, 27.2))
    stub(d, 'BOOT0', 'D5', (23.2, 27.2), SIG)
    d.track('BOOT0', 'In3', SIG, [(23.2, 27.2), (23.6, 27.6), (23.6, 32.0), (23.2, 32.4)])
    d.via('BOOT0', (23.2, 32.4))
    d.track('BOOT0', 'B', SIG, [(23.2, 32.4), (23.57, 32.03), d.pad('R5.1', net='BOOT0')])
    # VCAP: E7 -> (24.8, 27.2) -> C20.1 (north cap); F8 -> (25.6, 28.0) -> C19.1 (south cap) (D-R11-15 swap)
    d.via('VCAP2', (24.8, 27.2))
    stub(d, 'VCAP2', 'E7', (24.8, 27.2), PWR)
    d.track('VCAP2', 'B', PWR, [(24.8, 27.2), (24.0, 27.2)])
    d.pad('C20.1', net='VCAP2', at=(24.0, 27.25))
    d.via('VCAP1', (25.6, 28.0))
    stub(d, 'VCAP1', 'F8', (25.6, 28.0), PWR)
    d.track('VCAP1', 'B', 0.15, [(25.6, 28.0), (24.85, 28.75), d.pad('C19.1', net='VCAP1')])


# ---- 3. SWD: A9 / A10 north to vias, B.Cu east along the aft edge of the field and down the free column x 32.0 / 32.35
# under U3 (between the B.Cu USB / VBUS column x <= 31.52 and U10 / D4 x >= 33.05), vias beside J2.2 / J2.4.
def swd(d):
    d.via('SWCLK', (26.8, 23.6))
    stub(d, 'SWCLK', 'A9', (26.8, 23.6), SIG)
    d.track('SWCLK', 'B', SIG, [(26.8, 23.6), (27.2, 23.2), (31.95, 23.2), (32.35, 23.6), (32.35, 37.25), (32.9, 37.8)])
    d.via('SWCLK', (32.9, 37.8))
    d.pad('J2.4', net='SWCLK', at=(32.9, 38.965))
    d.track('SWCLK', 'F', SIG, [(32.9, 37.8), (32.9, J2_NORTH)])
    d.via('SWDIO', (27.6, 23.6))
    stub(d, 'SWDIO', 'A10', (27.6, 23.6), SIG)
    d.track('SWDIO', 'B', SIG, [(27.6, 23.6), (31.6, 23.6), (32.0, 24.0), (32.0, 37.43), (31.63, 37.8)])
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
    d.via('QSPI_IO2', (21.6, 24.0))
    stub(d, 'QSPI_IO2', 'A3', (21.6, 24.0), SIG)
    d.track('QSPI_IO2', 'B', SIG, [(21.6, 24.0), (22.0, 24.4), (28.6, 24.4), (29.0, 24.8), (29.0, 30.6)])
    d.via('QSPI_IO2', (29.0, 30.6))
    d.track('QSPI_IO2', 'F', SIG, [(29.0, 30.6), (32.23, 30.6), (32.83, 31.2), (32.83, 33.4)])
    d.pad('U3.3', net='QSPI_IO2', at=(32.83, 34.03))
    # NCS B5: dog-bone (23.2, 25.6), In3 east along y 26.0 (between the via rows 25.6 / 26.4) and south down x 29.5 to a via south-west of pin 1; R10 (the
    # pull-up, B.Cu) from that via
    d.via('QSPI_NCS', (23.2, 25.6))
    stub(d, 'QSPI_NCS', 'B5', (23.2, 25.6), SIG)
    d.track('QSPI_NCS', 'In3', SIG, [(23.2, 25.6), (23.6, 26.0), (28.6, 26.0), (29.5, 26.9), (29.5, 32.4)])
    d.via('QSPI_NCS', (29.5, 32.4))
    d.track('QSPI_NCS', 'F', SIG, [(29.5, 32.4), (30.3, 33.2), (30.3, 33.4)])
    d.pad('U3.1', net='QSPI_NCS', at=(30.3, 34.03))
    d.track('QSPI_NCS', 'B', SIG, [(29.5, 32.4), (29.5, 29.97), d.pad('R10.1', net='QSPI_NCS')])
    for v in ((28.0, 31.2), (28.9, 33.0), (28.0, 27.2)):     # GND partners (AGENTS section 3)
        d.via('GND', v)


# ---- 5. IMU U4 (bottom, rotation 180: pins 12 CS / 13 SCK / 14 MOSI on its aft row, 1 MISO / 4 INT1 east column).
# MISO on B.Cu round the east; CS / SCK / MOSI on In3 straight under U4 to vias aft of its pins (one crossing-free
# order, W -> E CS, MOSI, SCK; SCK sweeps aft of MOSI's via); INT1 F north, B.Cu to pin 4 from the east.
def imu(d):
    # MISO A6: via north, B.Cu round the east of U4 into pin 1
    d.via('SPI1_MISO', (24.4, 23.6))
    stub(d, 'SPI1_MISO', 'A6', (24.4, 23.6), SIG)
    d.track('SPI1_MISO', 'B', SIG, [(24.4, 23.6), (24.8, 23.2), (25.5, 22.5), (25.5, 20.15), (25.1, 19.75),
                                    d.pad('U4.1', net='SPI1_MISO')])
    # CS A5 and MOSI C5 on F.Cu down the channel between LED1 / R32 and LED2 / R33 (x 22.85 ... 25.35) over U4, vias aft
    # of pins 12 / 14; R11 (CS pull-up) on B.Cu from CS's via
    d.track('IMU_CS', 'F', SIG, [d.pad('U1', 'A5', net='IMU_CS'), (23.6, 23.4), (23.1, 22.9), (23.1, 19.3), (22.3, 18.5)])
    d.via('IMU_CS', (22.3, 18.5))
    d.track('IMU_CS', 'B', SIG, [(22.3, 18.5), (22.5, 18.7), d.pad('U4.12', net='IMU_CS')])
    d.track('IMU_CS', 'B', SIG, [(22.3, 18.5), (21.33, 18.5), (19.8, 20.03)])
    d.pad('R11.1', net='IMU_CS', at=(19.8, 20.03))
    d.track('SPI1_MOSI', 'F', SIG, [d.pad('U1', 'C5', net='SPI1_MOSI'), (24.0, 25.6), (24.0, 18.7)])
    d.via('SPI1_MOSI', (24.0, 18.7))
    d.track('SPI1_MOSI', 'B', SIG, [(24.0, 18.7), (24.0, 19.04), d.pad('U4.14', net='SPI1_MOSI')])
    # SCK A7: via north, In3 under the F channel and aft of MOSI's via to a via under pin 13 (the one crossing of the
    # three, U1's MOSI-SCK order being the reverse of U4's)
    d.via('SPI1_SCK', (25.2, 23.6))
    stub(d, 'SPI1_SCK', 'A7', (25.2, 23.6), SIG)
    d.track('SPI1_SCK', 'In3', SIG, [(25.2, 23.6), (24.6, 23.0), (24.6, 18.65), (24.2, 18.25), (23.0, 18.25)])
    d.via('SPI1_SCK', (23.0, 18.25))
    d.track('SPI1_SCK', 'B', SIG, [(23.0, 18.25), d.pad('U4.13', net='SPI1_SCK')])
    # INT1 C4: F channel x 22.4 north between B3 / B4 and A3 / A4, via north of row A, B.Cu east above U4's pin row
    # and into pin 4 from the east
    d.track('IMU_INT1', 'F', SIG, [d.pad('U1', 'C4', net='IMU_INT1'), (22.4, 25.6), (22.4, 23.05)])
    d.via('IMU_INT1', (22.4, 23.05))
    d.track('IMU_INT1', 'B', SIG, [(22.4, 23.05), (22.85, 22.6), (24.6, 22.6), (24.9, 22.3), (24.9, 21.6), (24.55, 21.25),
                                   d.pad('U4.4', net='IMU_INT1')])
    # U4 supply: pins 5 / 8 (3V3A) and C30 / C31 to their own vias (In2 3V3A), pins 2 / 3 and 6 / 7 (GND) to vias. F.Cu
    # over U4 carries LED1 / LED2 / R32 / R33, so every via sits clear of their pads.
    d.track('3V3A', 'B', PWR, [d.pad('U4.5', net='3V3A'), (23.5, 22.1), (23.6, 22.2)])
    d.via('3V3A', (23.6, 22.2))
    d.track('3V3A', 'B', PWR, [d.pad('U4.8', net='3V3A'), (20.15, 21.25), (19.9, 21.0)])
    d.via('3V3A', (19.9, 21.0))
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
    for v in ((24.8, 24.0), (26.0, 23.1), (21.6, 18.1), (24.6, 18.0)):     # GND partners
        d.via('GND', v)


# ---- 6. Barometer U5 (bottom, (9, 40)) and the I2C pair: SDA (A4) / SCL (B4) dog-bones, In3 west north of Y1's keep-out,
# south down x 13.2 / 13.75 (west of Y1), vias beside R13 / R12, then under U5 to vias south of its pads 7 / 8;
# BARO_SDO from R64 by In3 under U5 to a via south of pad 6.
def baro(d):
    d.via('I2C1_SDA', (22.8, 23.6))
    stub(d, 'I2C1_SDA', 'A4', (22.8, 23.6), SIG)
    d.track('I2C1_SDA', 'In3', SIG, [(22.8, 23.6), (21.2, 23.6), (20.6, 23.0), (13.8, 23.0), (13.2, 23.6), (13.2, 42.3)])
    d.via('I2C1_SDA', (13.2, 42.3))
    d.track('I2C1_SDA', 'B', SIG, [(13.2, 42.3), (13.0, 42.1), d.pad('R13.1', net='I2C1_SDA')])
    d.track('I2C1_SDA', 'In3', SIG, [(13.2, 42.3), (13.2, 42.75), (12.8, 43.15), (8.77, 43.15), (8.37, 42.75)])
    d.via('I2C1_SDA', (8.37, 42.75))
    d.track('I2C1_SDA', 'B', SIG, [(8.37, 42.75), (8.37, 41.825)])
    d.via('I2C1_SCL', (23.2, 24.8))
    stub(d, 'I2C1_SCL', 'B4', (23.2, 24.8), SIG)
    d.track('I2C1_SCL', 'In3', SIG, [(23.2, 24.8), (22.8, 24.4), (21.2, 24.4), (20.4, 23.6), (14.35, 23.6),
                                     (13.75, 24.2), (13.75, 39.7)])
    d.via('I2C1_SCL', (13.75, 39.7))
    d.track('I2C1_SCL', 'B', SIG, [(13.75, 39.7), (13.48, 39.43), d.pad('R12.1', net='I2C1_SCL')])
    d.track('I2C1_SCL', 'In3', SIG, [(13.75, 39.7), (13.75, 43.15), (13.35, 43.55), (7.52, 43.55), (7.12, 43.15)])
    d.via('I2C1_SCL', (7.12, 43.15))
    d.track('I2C1_SCL', 'B', SIG, [(7.12, 43.15), (7.12, 41.825)])
    d.via('BARO_SDO', (7.97, 36.0))
    d.track('BARO_SDO', 'B', SIG, [(7.97, 36.0), d.pad('R64.1', net='BARO_SDO')])
    d.track('BARO_SDO', 'In3', SIG, [(7.97, 36.0), (9.63, 37.66), (9.63, 42.7)])
    d.via('BARO_SDO', (9.63, 42.7))
    d.track('BARO_SDO', 'B', SIG, [(9.63, 42.7), (9.63, 41.825)])
    d.via('GND', (21.6, 23.2))                                # QSPI_IO2 dog-bone partner


def fanout_check(d):
    """r11_fanout.tsv covers every connected ball of U1 with its net; every `drawn` row with a site has core's via there;
    no `via` / `lane` row's site holds a core via (the reservations the later families rely on)."""
    with FANOUT.open() as fh:
        rows = list(csv.DictReader((ln for ln in fh if not ln.startswith('#')), delimiter='\t'))
    u1 = d.board.FindFootprintByReference('U1')
    balls = {p.GetNumber(): p.GetNetname() for p in u1.Pads()
             if p.GetNetname() and not p.GetNetname().startswith('unconnected')}
    table = {r['ball']: r for r in rows}
    assert set(table) == set(balls), ('fan-out table / U1 balls differ', set(table) ^ set(balls))
    for b, r in table.items():
        assert r['net'] == balls[b], (b, r['net'], balls[b])
        if r['x'] == '-':
            continue
        site = (float(r['x']), float(r['y']))
        if r['state'] == 'drawn' and r['family'] == 'core':
            assert d.vias.get(site) == r['net'], (b, site, d.vias.get(site))
        else:
            assert site not in d.vias, (b, site, 'reserved site holds a core via')


def draw(d):
    rails(d)
    mcu_local(d)
    swd(d)
    qspi(d)
    imu(d)
    baro(d)
    fanout_check(d)
