"""R8 spike (a) geometry under U1: placement overrides, In2 keep-outs and copper tables (final; RESULT.md).

Coordinates: KiCad mm, y = 0 aft edge, +y forward. U1 at (23.0, 45.0), rotation 0 (D1): pins 1-25 forward face
(y 52.55, x 17.0 + 0.5 (n - 1)), 26-50 east face (x 30.55, y 51.0 - 0.5 (n - 26)), 51-75 aft face (y 37.45,
x 29.0 - 0.5 (n - 51)), 76-100 west face (x 15.45, y 39.0 + 0.5 (n - 76)). U1 pads 0.3 x 1.6: the inner ends are at
x 16.25 / 29.75 and y 38.25 / 51.75.
"""
U1 = (23.0, 45.0)


def u1_pin(n):
    if n <= 25:
        return (17.0 + 0.5 * (n - 1), 52.55)
    if n <= 50:
        return (30.55, 51.0 - 0.5 * (n - 26))
    if n <= 75:
        return (29.0 - 0.5 * (n - 51), 37.45)
    return (15.45, 39.0 + 0.5 * (n - 76))


# ---------------------------------------------------------------------------------------------------------------------
# Placement (x, y, rotation, side). Seed: partial/b0_place_final.tsv. Bottom parts: KiCad rotation as placed.
PLACE = {
    'U3': (22.6, 43.2, 90, 'B'),      # QSPI flash under U1 (seed): W row pins 1-4 (fwd->aft), E row 5-8 (aft->fwd)
    'Y1': (22.85, 48.6, 90, 'B'),     # pad 1 HSE_IN fwd-W under V12, pad 3 HSE_OUT aft-E above V13, GND pads 2/4
    'C25': (19.95, 49.7, 180, 'B'),   # HSE_IN load cap W of Y1, pad 1 east on Y1.1's row
    'C26': (25.75, 47.5, 0, 'B'),     # HSE_OUT load cap E of Y1, pad 1 west on Y1.3's row
    'R170': (28.0, 47.93, 90, 'B'),   # ARM series 4.7k at pin 33: pad 2 (MCU) aft at V33's y, pad 1 (ARM) fwd
    'C18': (18.3, 51.15, 180, 'B'),   # VBAT (pin 6) 100n: pad 1 east at V6
    'C15': (29.2, 49.4, 90, 'B'),     # VDD pin 27 100n, under V27
    'C16': (28.1, 38.62, 180, 'B'),   # VDD pin 50 100n
    'C19': (28.35, 40.7, 270, 'B'),   # VCAP1 2.2u: pad 1 aft at V48's y
    'C20': (19.8, 39.3, 0, 'B'),      # VCAP2 2.2u: pad 1 west at V73's y
    'C17': (17.0, 39.9, 270, 'B'),    # VDD pin 75 100n: pad 1 aft under V75
    'C23': (15.45, 43.95, 270, 'B'),  # 3V3 bulk 4.7u under the W pad row, pad 1 aft on the R10 3V3 via's row
    'C29': (28.0, 45.52, 270, 'B'),   # flash VCC 100n: pad 1 at U3.8's y
    'R10': (16.7, 44.67, 90, 'B'),    # QSPI_NCS pull-up: pad 1 fwd at V_NCS's y
    'C24': (25.75, 51.1, 0, 'B'),     # NRST 100n beside V_NRST
    'R5': (17.9, 48.0, 0, 'B'),       # BOOT0 pull-down beside V94
    'C13': (14.1, 52.1, 270, 'B'),    # VDD pin 100 100n at the outward via V100
    'C14': (22.0, 55.2, 270, 'B'),    # VDD pin 11 100n at the outward via V11
    'C21': (26.5, 55.6, 270, 'B'),    # VDDA/VREF+ 100n below the outward via (26.5, 54.4)
    'C22': (28.4, 55.18, 0, 'B'),     # VDDA 1u, pad 1 west on C21.1's row
    'Q123': (16.0, 66.4, 0, 'B'), 'R162': (16.4, 62.95, 90, 'B'),  # not spike parts: buzzer driver clear of ARM
    # not spike parts: the sense dividers no longer fit under U1 (ARM1_SENSE, C24 and C15 take the NE corner);
    # parked forward of pins 17/18 on B.Cu, unrouted (their home is step 4's)
    'R62': (24.9, 56.45, 0, 'B'), 'R63': (24.9, 57.4, 0, 'B'),
    'R60': (27.5, 56.95, 0, 'B'), 'R61': (29.4, 56.95, 0, 'B'), 'C60': (30.2, 53.65, 0, 'B'),
}
FALLBACK_PLACE = {}

FALLBACK_KEEPOUTS = []

W = 0.2                # signal width
V = (0.5, 0.3)         # via diameter, drill


def copper():
    t, v = [], []

    def tr(net, layer, *pts, w=W):
        t.append((net, layer, list(pts), w))

    def via(net, x, y, d=V):
        v.append((net, x, y, d[0], d[1]))

    # --- QSPI -----------------------------------------------------------------------------------------------------
    tr('QSPI_NCS', 'F', (15.45, 47.0), (16.6, 47.0), (17.5, 46.1), (17.5, 45.1))
    via('QSPI_NCS', 17.5, 45.1)
    tr('QSPI_NCS', 'B', (16.7, 45.1), (17.5, 45.1), (19.07, 45.1))
    tr('QSPI_IO2', 'F', (17.0, 52.55), (17.0, 49.0), (18.1, 47.9), (18.1, 43.17), (17.5, 42.57))
    via('QSPI_IO2', 17.5, 42.57)
    tr('QSPI_IO2', 'B', (17.5, 42.57), (19.07, 42.57))
    tr('QSPI_IO1', 'F', (25.0, 37.45), (25.0, 39.4))
    via('QSPI_IO1', 25.0, 39.4)
    tr('QSPI_IO1', 'B', (25.0, 39.4), (20.57, 43.83), (19.07, 43.83))
    tr('QSPI_IO0', 'F', (25.5, 37.45), (25.5, 38.55), (26.13, 39.18), (26.13, 40.55))
    via('QSPI_IO0', 26.13, 40.55)
    tr('QSPI_IO0', 'B', (26.13, 40.55), (26.13, 41.3))
    tr('QSPI_IO3', 'F', (24.5, 37.45), (24.5, 38.45), (24.0, 38.95), (24.0, 40.08), (27.75, 43.83))
    via('QSPI_IO3', 27.75, 43.83)
    tr('QSPI_IO3', 'B', (27.75, 43.83), (26.13, 43.83))
    tr('QSPI_CLK', 'F', (30.55, 46.0), (29.3, 46.0), (29.3, 42.57), (27.75, 42.57))
    via('QSPI_CLK', 27.75, 42.57)
    tr('QSPI_CLK', 'B', (27.75, 42.57), (26.13, 42.57))
    tr('3V3', 'B', (26.13, 45.1), (28.0, 45.1))
    tr('3V3', 'B', (28.0, 45.1), (28.75, 45.1))
    via('3V3', 28.75, 45.1)           # U3.8 / C29 to In2 3V3
    via('GND', 17.5, 41.3)
    tr('GND', 'B', (17.5, 41.3), (19.07, 41.3))
    via('GND', 28.6, 43.2)            # IO3 / CLK vias
    via('GND', 25.5, 40.0)            # IO0 / IO1 vias
    via('GND', 16.8, 45.9)            # NCS via

    # --- HSE --------------------------------------------------------------------------------------------------------
    tr('HSE_IN', 'F', (22.5, 52.55), (22.5, 51.6), (22.0, 51.1))
    via('HSE_IN', 22.0, 51.1)
    tr('HSE_IN', 'B', (22.0, 51.1), (22.0, 49.7), (20.37, 49.7))
    tr('HSE_OUT', 'F', (23.0, 52.55), (23.0, 48.0), (23.7, 47.3), (23.7, 46.35))
    via('HSE_OUT', 23.7, 46.35)
    tr('HSE_OUT', 'B', (23.7, 46.35), (23.7, 47.5), (25.33, 47.5))
    via('GND', 21.0, 51.1)            # HSE_IN via
    via('GND', 22.65, 46.35)          # HSE_OUT via
    tr('GND', 'B', (19.53, 49.7), (18.75, 49.7))
    via('GND', 18.75, 49.7)           # C25 GND
    tr('GND', 'B', (26.17, 47.5), (26.95, 47.5))
    via('GND', 26.95, 47.5)           # C26 GND

    # --- NRST -------------------------------------------------------------------------------------------------------
    tr('NRST', 'F', (23.5, 52.55), (23.5, 51.6), (24.0, 51.1))
    via('NRST', 24.0, 51.1)
    tr('NRST', 'B', (25.33, 51.1), (24.0, 51.1), (23.15, 51.95), (16.1, 51.95), (12.0, 47.85), (7.6, 47.85),
       (7.6, 42.6))
    via('NRST', 7.6, 42.6)
    tr('NRST', 'F', (7.6, 42.6), (8.65, 42.6))
    tr('GND', 'B', (26.17, 51.1), (26.95, 51.1))
    via('GND', 26.95, 51.1)           # C24 GND

    # --- ARM1_SENSE -------------------------------------------------------------------------------------------------
    tr('ARM1_SENSE_MCU', 'F', (30.55, 47.5), (29.3, 47.5))
    via('ARM1_SENSE_MCU', 29.3, 47.5)
    tr('ARM1_SENSE_MCU', 'B', (29.3, 47.5), (28.0, 47.5))
    tr('ARM1_SENSE', 'B', (28.0, 48.36), (28.0, 51.95), (27.5, 52.45), (18.83, 52.45), (18.18, 53.1), (18.18, 91.3))
    via('GND', 28.6, 46.6)            # ARM_MCU via
    via('GND', 17.4, 90.2)            # exit via (18.18, 91.30), 1.35 mm: R7's (18.18, 90.55) sits on the lane, and a
                                      # via on a block GND track end would join the rigid ch1_copper group
    via('GND', 13.95, 93.75)          # block-internal ARM1_SENSE vias (rigid): R7's GND vias, same positions
    via('GND', 13.95, 97.15)

    # --- BOOT0 ------------------------------------------------------------------------------------------------------
    tr('BOOT0', 'F', (15.45, 48.0), (16.75, 48.0))
    via('BOOT0', 16.75, 48.0)
    tr('BOOT0', 'B', (16.75, 48.0), (17.47, 48.0))

    # --- VCAP / VDD -------------------------------------------------------------------------------------------------
    tr('VCAP2', 'F', (18.0, 37.45), (18.0, 39.3))
    via('VCAP2', 18.0, 39.3)
    tr('VCAP2', 'B', (18.0, 39.3), (19.1, 39.3))
    tr('3V3', 'F', (17.0, 37.45), (17.0, 38.75))
    via('3V3', 17.0, 38.75)
    tr('3V3', 'B', (17.0, 38.75), (17.0, 39.48))
    tr('VCAP1', 'F', (30.55, 40.0), (29.25, 40.0))
    via('VCAP1', 29.25, 40.0)
    tr('VCAP1', 'B', (29.25, 40.0), (28.35, 40.0))
    tr('3V3', 'F', (30.55, 39.0), (29.25, 39.0))
    via('3V3', 29.25, 39.0)
    tr('3V3', 'B', (29.25, 39.0), (28.87, 38.62), (28.52, 38.62))
    tr('3V3', 'F', (30.55, 50.5), (29.2, 50.5))
    via('3V3', 29.2, 50.5)
    tr('3V3', 'B', (29.2, 50.5), (29.2, 49.82))
    tr('3V3', 'F', (19.5, 52.55), (19.5, 51.15))
    via('3V3', 19.5, 51.15)
    tr('3V3', 'B', (19.5, 51.15), (18.72, 51.15))
    tr('3V3', 'F', (15.45, 51.0), (14.1, 51.0))
    via('3V3', 14.1, 51.0)
    tr('3V3', 'B', (14.1, 51.0), (14.1, 51.68))
    via('GND', 14.1, 53.3)            # C13 GND
    tr('GND', 'B', (14.1, 52.52), (14.1, 53.3))
    # VDD pin 11 outward (pin 12's HSE_IN escape takes its inner column)
    tr('3V3', 'F', (22.0, 52.55), (22.0, 54.15))
    via('3V3', 22.0, 54.15)
    tr('3V3', 'B', (22.0, 54.15), (22.0, 54.78))
    tr('GND', 'B', (22.0, 55.62), (22.0, 56.4))
    via('GND', 22.0, 56.4)
    # VDDA / VREF+ outward, VSSA in the F.Cu pour
    tr('3V3A', 'F', (26.5, 52.55), (26.5, 54.4))
    tr('3V3A', 'F', (27.0, 52.55), (27.0, 53.7), (26.5, 53.7))
    via('3V3A', 26.5, 54.4)
    tr('3V3A', 'B', (26.5, 54.4), (26.5, 55.18), (27.7, 55.18))
    via('GND', 27.2, 56.1)            # C21 / C22 GND
    tr('GND', 'B', (26.5, 56.02), (26.5, 56.1), (27.2, 56.1))
    # R10 / C23 3V3
    via('3V3', 16.7, 43.25)
    tr('3V3', 'B', (15.45, 43.25), (16.7, 43.25), (16.7, 44.24))

    # decoupling GND returns: a GND via at each cap's GND pad where one fits
    tr('GND', 'B', (29.2, 48.98), (29.2, 48.2))
    via('GND', 29.2, 48.2)            # C15 (VDD27)
    tr('GND', 'B', (20.5, 39.3), (21.4, 39.3))
    via('GND', 21.4, 39.3)            # C20 (VCAP2)
    tr('GND', 'B', (17.88, 51.15), (17.88, 50.35))
    via('GND', 17.88, 50.35)          # C18 (VBAT)
    tr('GND', 'B', (28.35, 41.4), (29.25, 41.4))
    via('GND', 29.25, 41.4)           # C19 (VCAP1)
    return t, v


def fallback_copper():
    return [], []


# In2 keep-out under Y1 and its load caps C25 / C26 (R5 V1): no 3V3 plane under the crystal
KEEPOUTS = [('Y1_In2_keepout', 'In2', [(18.9, 46.3), (26.8, 46.3), (26.8, 50.95), (18.9, 50.95)])]

NETS = ['QSPI_CLK', 'QSPI_NCS', 'QSPI_IO0', 'QSPI_IO1', 'QSPI_IO2', 'QSPI_IO3', 'HSE_IN', 'HSE_OUT', 'NRST',
        'ARM1_SENSE', 'ARM1_SENSE_MCU', 'VCAP1', 'VCAP2', 'BOOT0']
PARTS = ['U3', 'C29', 'R10', 'Y1', 'C25', 'C26', 'C13', 'C14', 'C15', 'C16', 'C17', 'C18', 'C19', 'C20', 'C21', 'C22',
         'C23', 'C24', 'R5', 'R170']
FALLBACK_NETS, FALLBACK_PARTS = NETS, PARTS
