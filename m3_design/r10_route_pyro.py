"""R10 CH1 pyro channel, its load switch and the two sense chains: explicit pad-referenced polylines (no search).

Fire loop on F.Cu at 1.0 mm: J124.1 (BUS) -> R134 (2 ohm shorted-igniter limit) -> J121.2 (IGN); J121.1 (OUT) ->
Q124's drain. Pulse at most 4.2 A for 20 ms (8.4 V / 2 ohm; firmware ends every pulse by 20 ms); no steady current.
The load switch Q120 / Q121 (bottom, sources facing) feeds RAW_ACT, which reaches only J124.2 and the RAW_ACT
sense, so the ARM plug is the only path from RAW_ACT to the pyro bus (AGENTS 2.1).
Every layer change of a pyro, arming or sense net has a GND via within 1.5 mm (AGENTS 3).
Pad positions are asserted by Draw.pad: a moved part stops the build.
"""

S, P = 0.2, 0.3          # signal, gate / GND bar widths
FIRE = 1.0               # fire-loop copper
RAWW = 0.4               # RAW_ACT branch to TP120 / the sense divider


def draw(d):
    t, link, via = d.track, d.link, d.via

    # Fire loop (F.Cu).
    link('PYRO1_IGN', 'F', FIRE, 'J121.2', 'R134.1', ((10.425, 61.025),))
    link('PYRO1_BUS', 'F', FIRE, 'J124.1', 'R134.2', ((9.5, 64.1), (11.575, 66.175)))  # >= 1.5 mm from J124.2 (S-5)
    t('PYRO1_OUT', 'F', FIRE, [d.pad('J121.1'), (10.33, 54.1), (11.33, 55.1)])
    t('PYRO1_OUT', 'F', FIRE, [(11.33, 55.1), d.pad('Q124.5')])

    # Q124 source return: a bar over the three source pads, two GND vias into In1.
    t('GND', 'F', P, [d.pad('Q124.3'), d.pad('Q124.1')])
    for n in ('2', '1'):
        a = d.pad('Q124.' + n)
        t('GND', 'F', P, [a, (15.75, a[1])])
        via('GND', (15.75, a[1]))

    # OUT to the bottom: the continuity tap R173, the snubber C128 and the cold-side divider R131.
    via('PYRO1_OUT', (11.33, 55.1))
    via('GND', (10.0, 55.6))
    t('PYRO1_OUT', 'B', S, [(11.33, 55.1), (10.37, 56.06), d.pad('R173.1')])
    t('PYRO1_OUT', 'B', S, [d.pad('R173.1'), (10.37, 59.5)])
    t('PYRO1_OUT', 'B', S, [(10.37, 59.5), d.pad('C128.1')])
    t('PYRO1_OUT', 'B', S, [(10.37, 59.5), d.pad('R131.1')])
    link('PYRO1_COLD', 'B', S, 'R131.2', 'D120.1')
    t('3V3', 'B', S, [d.pad('D120.3'), (18.0, 58.6)])
    via('3V3', (18.0, 58.6))

    # Gate: U1.3 -> R126 (series) -> Q124.4, C126 / R128 (gate-source hold and pull-down), TP122.
    link('PYRO1_GATE_N', 'F', S, 'U1.3', 'R126.1')
    link('PYRO1_GATE_N', 'F', S, 'R126.1', 'R127.1')
    link('PYRO1_GATE', 'F', P, 'TP122.1', 'R126.2', ((16.0, 53.3),))
    t('PYRO1_GATE', 'F', P, [d.pad('R126.2'), (16.0, 55.395)])
    t('PYRO1_GATE', 'F', P, [(16.0, 55.395), (15.0, 55.395), d.pad('Q124.4')])   # square T (no 45 deg branch)
    t('PYRO1_GATE', 'F', P, [(16.0, 55.395), (16.0, 56.275), d.pad('C126.1')])
    link('PYRO1_GATE', 'F', P, 'C126.1', 'R128.1')

    # Continuity: R173 / R129 / R130 / R178 divider (bottom), C127 filter, R168 at U1.15.
    link('PYRO1_CONT_MID', 'B', S, 'R173.2', 'R129.1')
    link('PYRO1_CONT', 'B', S, 'R129.2', 'R130.1')
    link('PYRO1_CONT', 'B', S, 'R130.1', 'R178.1')
    link('PYRO1_CONT', 'B', S, 'R178.1', 'C127.1', ((19.85, 56.8),))
    t('PYRO1_CONT', 'B', S, [d.pad('C127.1'), (21.65, 55.0), (24.0, 55.0)])
    via('PYRO1_CONT', (24.0, 55.0))
    via('GND', (25.2, 55.0))
    t('PYRO1_CONT', 'F', S, [(24.0, 55.0), d.pad('R168.1')])
    link('PYRO1_CONT_MCU', 'F', S, 'R168.2', 'U1.15')

    # ARM sense: BUS -> R132 / R175 -> node (R133 / R180 / C129) -> R170 -> U1.33 (PC5).
    t('PYRO1_BUS', 'F', P, [d.pad('R134.2'), (17.0, 63.7)])
    via('PYRO1_BUS', (17.0, 63.7))
    via('GND', (16.0, 63.7))
    t('PYRO1_BUS', 'B', S, [(17.0, 63.7), (19.0, 61.7), (19.0, 59.32), d.pad('R132.1')])
    link('ARM1_SENSE_MID', 'B', S, 'R132.2', 'R175.1')
    link('ARM1_SENSE', 'B', S, 'R175.2', 'R133.1')
    link('ARM1_SENSE', 'B', S, 'R133.1', 'R180.1')
    link('ARM1_SENSE', 'B', S, 'R180.1', 'C129.1')
    t('ARM1_SENSE', 'B', S, [d.pad('C129.1'), (27.2, 58.75)])
    via('ARM1_SENSE', (27.2, 58.75))
    via('GND', (28.2, 59.6))
    t('ARM1_SENSE', 'F', S, [(27.2, 58.75), (32.6, 53.35), d.pad('R170.1')])
    link('ARM1_SENSE_MCU', 'F', S, 'R170.2', 'U1.33', ((31.6, 45.5),))

    # Load switch (bottom): sources bridged by C120 / R120, gates tied on F.Cu through R121 to the driver Q122.
    # C120 / R120 tap the source and gate rows: each pad pair joined straight, R120 by a stub to its centre.
    t('ACT_FET_S', 'B', P, [d.pad('Q121.1'), (16.7, 70.5), d.pad('C120.1')])
    t('ACT_FET_S', 'B', P, [d.pad('C120.1'), (18.5, 70.9), d.pad('R120.1')])
    # Source bridge between the facing source rows (pulse current), clear of both gate pads.
    t('ACT_FET_S', 'B', RAWW, [d.pad('Q120.1'), (11.59, 71.6), (15.41, 71.6), d.pad('Q121.1')])
    for n in ('2', '3'):
        for q in ('Q120', 'Q121'):
            a = d.pad(f'{q}.{n}')
            t('ACT_FET_S', 'B', RAWW, [a, (a[0], 71.6)])
    # Gate: Q120.4 -> via (16.2, 72.3) -> C120.2 -> R120.2 on B.Cu; on F.Cu the via takes TP121 (north stub) and the run
    # west through R121.1 to Q121's gate via.
    t('ACT_GATE', 'B', P, [d.pad('Q120.4'), (15.8, 72.7), (16.2, 72.3)])
    t('ACT_GATE', 'B', P, [(16.2, 72.3), d.pad('C120.2')])
    t('ACT_GATE', 'B', P, [d.pad('C120.2'), (18.5, 72.3), d.pad('R120.2')])
    via('ACT_GATE', (16.2, 72.3))
    t('ACT_GATE', 'F', P, [d.pad('TP121.1'), (16.2, 72.3)])
    # Q121's gate (west end) hops over the source bridge: via west of it, F.Cu to R121.1; GND partner via.
    t('ACT_GATE', 'B', P, [d.pad('Q121.4'), (10.8, 71.3)])
    via('ACT_GATE', (10.8, 71.3))
    via('GND', (9.9, 70.4))
    t('ACT_GATE', 'F', P, [(10.8, 71.3), (11.8, 72.3), d.pad('R121.1')])
    t('ACT_GATE', 'F', P, [d.pad('R121.1'), (16.2, 72.3)])
    link('ACT_DRV', 'F', P, 'Q122.3', 'R121.2', ((15.8, 70.14),))
    link('ACT_EN', 'F', S, 'Q122.1', 'R122.2', ((19.08, 70.75),))
    link('ACT_EN', 'F', S, 'R122.2', 'R123.1')
    link('RAW_PROTECTED', 'F', P, 'R122.1', 'D9.1', ((19.6, 66.4),))

    # RAW_ACT: Q121's drain to J124.2 (the ARM plug's live side), TP120 and the sense divider top R177.
    t('RAW_ACT', 'B', FIRE, [d.pad('J124.2'), (11.5, 67.6)])
    t('RAW_ACT', 'B', RAWW, [(15.4, 67.4), (17.3, 67.4), d.pad('TP120.1')])
    t('RAW_ACT', 'B', S, [d.pad('TP120.1'), (18.0, 65.57), d.pad('R177.1')])
    link('RAW_ACT_SENSE_MID', 'B', S, 'R177.2', 'R124.1')
    link('RAW_ACT_SENSE', 'B', S, 'R124.2', 'R125.1')
    link('RAW_ACT_SENSE', 'B', S, 'R125.1', 'R182.1')
    link('RAW_ACT_SENSE', 'B', S, 'R182.1', 'C122.1')
    t('RAW_ACT_SENSE', 'B', S, [d.pad('C122.1'), (27.2, 64.0)])
    via('RAW_ACT_SENSE', (27.2, 64.0))
    via('GND', (27.2, 65.4))
    t('RAW_ACT_SENSE', 'F', S, [(27.2, 64.0), (33.9, 57.3), (33.9, 45.0), d.pad('R172.1')])
    link('RAW_ACT_SENSE_MCU', 'F', S, 'R172.2', 'U1.34')
