"""R10 explicit CH1 and pyro load-switch routes, paired with pyro_place.tsv.

Pulse path: 1 mm, 1 oz copper; the inherited R9 adiabatic bound is ~6 K at
8.8 A/20 ms, so ~1.4 K at 4.2 A/20 ms (I-squared scaling, inference).
No steady servo current is allocated to this circuit. Actual pulse, resets,
shorted igniter and harness return still require bench qualification.
"""
NETS = ('PYRO1_BUS', 'PYRO1_IGN', 'PYRO1_OUT', 'PYRO1_GATE', 'PYRO1_GATE_N',
        'PYRO1_CONT', 'PYRO1_CONT_MID', 'PYRO1_CONT_MCU', 'PYRO1_COLD',
        'ARM1_SENSE', 'ARM1_SENSE_MID', 'ARM1_SENSE_MCU', 'ACT_GATE', 'ACT_DRV',
        'ACT_EN', 'ACT_FET_S', 'RAW_ACT', 'RAW_ACT_SENSE', 'RAW_ACT_SENSE_MID', 'RAW_ACT_SENSE_MCU')


def draw(d):
    p, t, link = d.pad, d.track, d.link

    def via(net, at, ground=None):
        d.via(net, at)
        if ground:
            d.via('GND', ground)

    def node(net, layer, points, width=.2):
        t(net, layer, width, points)

    # Three current-carrying bars. R134 is the mandatory 2 ohm short limit.
    link('PYRO1_IGN', 'F', 1.0, 'J121.2', 'R134.1', ((9.45, 58.2), (16.775, 58.2)))
    link('PYRO1_BUS', 'F', 1.0, 'J124.1', 'R134.2', ((15.675, 62.25),))
    link('PYRO1_OUT', 'F', 1.0, 'J121.1', 'Q124.5',
         ((8.75, 54.0), (11.8, 54.0)))
    # Six parallel source returns; pulse current stays outside the gate pads.
    for number in ('1', '2', '3'):
        a = p('Q124.' + number)
        node('GND', 'F', [a, (14.6, a[1])], .3)
    node('GND', 'F', [(14.6, 54.875), (14.6, 56.75)], .4)
    for y in (55.65, 56.2, 56.75):
        node('GND', 'F', [(14.6, y), (15.2, y)], .3)
        for x in (14.6, 15.2):
            d.via('GND', (x, y), (.5, .3))

    link('PYRO1_GATE_N', 'F', .2, 'U1.3', 'R126.1', ((18, 52.225),))
    link('PYRO1_GATE_N', 'F', .2, 'R126.1', 'R127.1', ((18.745, 52.625),))
    link('PYRO1_GATE', 'F', .2, 'R126.2', 'Q124.4', ((14.4, 53.825),))
    link('PYRO1_GATE', 'F', .2, 'Q124.4', 'C126.1', ((15.625, 54.225),))
    link('PYRO1_GATE', 'F', .2, 'C126.1', 'R128.1', ((16.3, 56.23),))
    node('PYRO1_GATE', 'F', [p('R126.2'), (13.6, 52.625)])
    via('PYRO1_GATE', (13.6, 52.625), (13, 51.7))
    node('PYRO1_GATE', 'B', [(13.6, 52.625), (7.625, 58.6), p('TP122.1')])

    # Continuity tap and drain snubber. High pulse current stays on F.Cu.
    node('PYRO1_OUT', 'F', [p('Q124.5'), (11.97, 55.2), (10.37, 56.8)], .4)
    via('PYRO1_OUT', (10.37, 56.8), (9.37, 56.8))
    node('PYRO1_OUT', 'B', [(10.37, 56.8), p('R173.1')])
    node('PYRO1_OUT', 'B', [p('R173.1'), (10.37, 58.645), p('C128.1')], .4)
    node('PYRO1_OUT', 'B', [p('C128.1'), (10.07, 59.5), p('R131.1')])
    link('PYRO1_CONT_MID', 'B', .2, 'R173.2', 'R129.1')
    node('PYRO1_CONT', 'B', [p('R129.2'), (13.3, 57.57), p('R130.1'), p('R178.1'), (18.08, 57.57), p('C127.1')])
    node('PYRO1_CONT', 'B', [p('C127.1'), (23.15, 57.15), (24, 56.3), (24, 54)])
    via('PYRO1_CONT', (24, 54), (23, 54))
    node('PYRO1_CONT', 'F', [(24, 54), p('R168.1')])
    link('PYRO1_CONT_MCU', 'F', .2, 'R168.2', 'U1.15')
    link('PYRO1_COLD', 'B', .2, 'R131.2', 'D120.1',
         ((10.93, 61.8), (16.8, 61.8), (16.8, 59.25)))

    # Armed-bus divider has its own distinct tap and four fault-tolerant resistors.
    node('PYRO1_BUS', 'F', [p('R134.2'), (17.675, 62.9), (18, 62.9)])
    via('PYRO1_BUS', (18, 62.9), (18, 61.5))
    node('PYRO1_BUS', 'B', [(18, 62.9), (19.2, 61.7), (19.2, 58.87), p('R132.1')])
    link('ARM1_SENSE_MID', 'B', .2, 'R132.2', 'R175.1')
    node('ARM1_SENSE', 'B', [p('R175.2'), (22.5, 58.77), p('R133.1'), p('R180.1'), p('C129.1')])
    node('ARM1_SENSE', 'B', [p('C129.1'), (26.1, 56.3), (29.4, 53), (33.8, 53)])
    via('ARM1_SENSE', (33.8, 53), (32.8, 52))
    node('ARM1_SENSE', 'F', [(33.8, 53), (33.8, 45.77), p('R170.1')])
    link('ARM1_SENSE_MCU', 'F', .2, 'R170.2', 'U1.33')

    # Back-to-back pyro load FETs: all pulse current on B.Cu, no series via.
    for ref in ('Q120', 'Q121'):
        row = sorted([p(f'{ref}.{n}') for n in ('5', '6', '7', '8')])
        node('BAT_IN' if ref == 'Q120' else 'RAW_ACT', 'B', row, 1.0)
        node('BAT_IN' if ref == 'Q120' else 'RAW_ACT', 'B',
             [p(f'{ref}.9'), (p(f'{ref}.9')[0], row[0][1])], 1.0)
    link('BAT_IN', 'B', 1.0, 'J1.1', 'Q120.9', ((7.15, 72.4), (11.21, 72.4)))
    link('RAW_ACT', 'B', 1.0, 'Q121.9', 'J124.2', ((13.06, 65.75),))
    for ref in ('Q120', 'Q121'):
        row = sorted([p(f'{ref}.{n}') for n in ('1', '2', '3')])
        node('ACT_FET_S', 'B', row, 1.0)
    node('ACT_FET_S', 'B', [p('Q121.2'), (12.86, 70.18), p('Q120.2')], 1.0)
    node('ACT_FET_S', 'B', [p('Q120.1'), (11.59, 70.39), (11.2, 70)], .3)
    via('ACT_FET_S', (11.2, 70))
    node('ACT_FET_S', 'F', [(11.2, 70), p('C120.1')], .3)
    link('ACT_FET_S', 'F', .2, 'C120.1', 'R120.1', ((12.37, 70.27),))
    node('ACT_GATE', 'B', [p('Q121.4'), (10.6, 68.9)])
    via('ACT_GATE', (10.6, 68.9), (9.6, 68.9))
    node('ACT_GATE', 'B', [p('Q120.4'), (16.3, 71.1)])
    via('ACT_GATE', (16.3, 71.1), (16.3, 70.1))
    node('ACT_GATE', 'F', [(10.6, 68.9), (12.4, 68.9), (13.5, 70), (15.2, 70), (16.3, 71.1)])
    link('ACT_GATE', 'F', .2, 'C120.2', 'R120.2', ((13.5, 71.73),))
    link('ACT_GATE', 'F', .2, 'R120.2', 'R121.1', ((13.43, 72.2),))
    link('ACT_DRV', 'F', .2, 'R121.2', 'Q122.3')
    node('ACT_GATE', 'F', [(10.6, 68.9), (9.9, 69.6), (9.2, 69.6), (9, 69.8)])
    via('ACT_GATE', (9, 69.8))
    node('ACT_GATE', 'B', [(9, 69.8), (8.6, 69.4), p('TP121.1')])
    link('ACT_EN', 'F', .2, 'Q122.1', 'R123.1', ((16.73, 74.22),))
    link('ACT_EN', 'F', .2, 'R123.1', 'R122.2')
    # RAW sense/probe branch is separate from the current-carrying run to ARM.
    node('RAW_ACT', 'B', [p('Q121.9'), (16, 65.31), (17.19, 66.5), p('TP120.1')], .3)
    node('RAW_ACT', 'B', [p('Q121.9'), (18.26, 65.31), p('R177.1')], .3)
    link('RAW_ACT_SENSE_MID', 'B', .2, 'R177.2', 'R124.1')
    node('RAW_ACT_SENSE', 'B', [p('R124.2'), (22.5, 64.27), p('R125.1'), p('R182.1'), p('C122.1')])
    node('RAW_ACT_SENSE', 'B', [p('C122.1'), (26.1, 61.3), (28.5, 58.9), (28.5, 57.4), (32.1, 53.8), (34.3, 53.8)])
    via('RAW_ACT_SENSE', (34.3, 53.8), (33.3, 54.7))
    node('RAW_ACT_SENSE', 'F', [(34.3, 53.8), (34.3, 45.07), p('R172.1')])
    link('RAW_ACT_SENSE_MCU', 'F', .2, 'R172.2', 'U1.34', ((32, 44.3), (31.3, 45)))
    # GND/3V3/RAW_PROTECTED endpoints are joined by the explicit ground/power families.
