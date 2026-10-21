"""R8 step 6 family qspi_hse: the QSPI flash U3 and the crystal Y1 under U1, and BOOT0 (r8_route.py).

Port of spike (a) (m3_design/r8_spikes/a_underU1/spike_geom.py copper(), RESULT.md "Flash U3" / "Crystal Y1"), on
the placement it proved (r8_place.tsv basis spike-a). U3 sits under U1 (bottom, rotation 90): its west row is pins
1-4 forward to aft (NCS, IO1, IO2, GND), its east row 5-8 aft to forward (IO0, CLK, IO3, VCC). Each QSPI signal is
one inward dive: the U1 pad, F.Cu under U1's body, one via, B.Cu into the flash pad, with a GND via within 1.5 mm of
every via (AGENTS section 3). Y1 (rotation 90) sits under pins 12 / 13: HSE_IN and HSE_OUT dive straight to it, and
their load caps C25 / C26 sit on the crystal pads' rows. In2 under Y1 is the R5 V1 keep-out (step 5).
Built elsewhere: U3.8 / C29 3V3 and U3.4's GND via (step 5, decoupling); NRST (usb_swd); ARM1_SENSE (pyro).
"""
from r8_route import W, u1_pin

NETS = ('QSPI_NCS', 'QSPI_IO0', 'QSPI_IO1', 'QSPI_IO2', 'QSPI_IO3', 'QSPI_CLK', 'HSE_IN', 'HSE_OUT', 'BOOT0')
RAILS = ('GND',)
# spike (a): QSPI 49.5 mm with 6 vias (plan estimate about 50 mm, 6); HSE 14.0 mm with 2 vias; BOOT0 2.0 mm, 1 via
BUDGET = dict(length_mm=68.0, vias=9, critical_layer_changes=8, ratio=1.40)

# (net, [(layer, polyline)...], via) -- one dive per net: F.Cu from the U1 pad to the via, B.Cu to the flash pad
DIVES = [
    ('QSPI_NCS', [('F', [u1_pin(92), (16.6, 47.0), (17.5, 46.1), (17.5, 45.1)]),
                  ('B', [(16.7, 45.1), (17.5, 45.1), (19.07, 45.1)])], (17.5, 45.1)),       # R10.1 pull-up on the via
    ('QSPI_IO2', [('F', [u1_pin(1), (17.0, 49.0), (18.1, 47.9), (18.1, 43.17), (17.5, 42.57)]),
                  ('B', [(17.5, 42.57), (19.07, 42.57)])], (17.5, 42.57)),
    ('QSPI_IO1', [('F', [u1_pin(59), (25.0, 39.4)]),
                  ('B', [(25.0, 39.4), (20.57, 43.83), (19.07, 43.83)])], (25.0, 39.4)),     # under the flash body
    ('QSPI_IO0', [('F', [u1_pin(58), (25.5, 38.55), (26.13, 39.18), (26.13, 40.55)]),
                  ('B', [(26.13, 40.55), (26.13, 41.3)])], (26.13, 40.55)),
    ('QSPI_IO3', [('F', [u1_pin(60), (24.5, 38.45), (24.0, 38.95), (24.0, 40.08), (27.75, 43.83)]),
                  ('B', [(27.75, 43.83), (26.13, 43.83)])], (27.75, 43.83)),                 # over the flash diagonally
    ('QSPI_CLK', [('F', [u1_pin(36), (29.3, 46.0), (29.3, 42.57), (27.75, 42.57)]),
                  ('B', [(27.75, 42.57), (26.13, 42.57)])], (27.75, 42.57)),                 # x 29.3: 0.35 mm off the pads
    ('HSE_IN', [('F', [u1_pin(12), (22.5, 51.6), (22.0, 51.1)]),
                ('B', [(22.0, 51.1), (22.0, 49.7), (20.37, 49.7)])], (22.0, 51.1)),           # Y1.1, then C25.1
    # fix pass 1 (R8P1-ROUTING-01, D86): the via sits between Y1.3 and C26.1 (0.14 mm from each, own net), so the
    # F.Cu dive ends over the crystal's near side and B.Cu tees both ways; spike (a)'s far-side via (23.7, 46.35) made
    # the run fold back through it (F.Cu 1.15 mm past Y1.3, B.Cu back under it)
    ('HSE_OUT', [('F', [u1_pin(13), (23.0, 49.19), (24.69, 47.5)]),
                 ('B', [(23.7, 47.5), (24.69, 47.5), (25.33, 47.5)])], (24.69, 47.5)),        # Y1.3, C26.1
    ('BOOT0', [('F', [u1_pin(94), (16.75, 48.0)]),
               ('B', [(16.75, 48.0), (17.47, 48.0)])], (16.75, 48.0)),                       # R5.1 pull-down
]
# pads the tables end on (ref, pad, net, centre): a placement change refuses to draw
PADS = [('U3', '1', 'QSPI_NCS', (19.07, 45.1)), ('U3', '2', 'QSPI_IO1', (19.07, 43.83)),
        ('U3', '3', 'QSPI_IO2', (19.07, 42.57)), ('U3', '5', 'QSPI_IO0', (26.13, 41.3)),
        ('U3', '6', 'QSPI_CLK', (26.13, 42.57)), ('U3', '7', 'QSPI_IO3', (26.13, 43.83)),
        ('R10', '1', 'QSPI_NCS', (16.7, 45.1)), ('Y1', '1', 'HSE_IN', (22.0, 49.7)), ('C25', '1', 'HSE_IN', (20.37, 49.7)),
        ('Y1', '3', 'HSE_OUT', (23.7, 47.5)), ('C26', '1', 'HSE_OUT', (25.33, 47.5)), ('R5', '1', 'BOOT0', (17.47, 48.0)),
        ('C25', '2', 'GND', (19.53, 49.7)), ('C26', '2', 'GND', (26.17, 47.5))]
# GND vias: one within 1.5 mm of each critical dive (QSPI, HSE), and the crystal load caps' GND pads
GND_VIAS = [(28.6, 43.2),     # IO3 / CLK vias
            (25.5, 40.0),     # IO0 / IO1 vias
            (16.8, 45.9),     # NCS via (IO2's partner is step 5's U3.4 via (17.5, 41.3))
            (21.0, 51.1),     # HSE_IN via
            (24.69, 46.25),   # HSE_OUT via (1.25 mm)
            (22.65, 46.35),   # crystal guard (spike (a)'s HSE_OUT partner, kept: Y1's B.Cu GND guard)
            (18.75, 49.7),    # C25.2
            (26.95, 47.5)]    # C26.2
GND_TRACKS = [[(19.53, 49.7), (18.75, 49.7)], [(26.17, 47.5), (26.95, 47.5)]]


def draw(d):
    for ref, num, net, at in PADS:
        d.pad(ref, num, net, at)
    for net, runs, via in DIVES:
        for layer, pts in runs:
            d.track(net, layer, W, pts)
        d.via(net, *via)
    for xy in GND_VIAS:
        d.via('GND', *xy)
    for pts in GND_TRACKS:
        d.track('GND', 'B', W, pts)
