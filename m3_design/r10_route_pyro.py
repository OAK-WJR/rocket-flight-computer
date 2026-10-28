"""R10 CH1 pyro channel, its load switch and the two sense chains: explicit pad-referenced polylines (no search).

Fire feed on B.Cu at 0.5 mm (AUD-6): Q121 drain (RAW_ACT) -> R134 (2 ohm shorted-igniter limit) -> J121.2 (IGN);
J121.1 (OUT) -> Q124's drain on F.Cu. Pulse at most 4.2 A for 20 ms (8.4 V / 2 ohm; firmware ends every pulse by
20 ms); no steady current. The external power switch is the pad arming device (owner, 2026-10-28); Q120 / Q121
remain the independent load switch ahead of R134, and both bus-sense dividers tap RAW_ACT.
Fire-gate and OUT layer changes retain their GND partners; filtered ADC and ACT controls are exempt (AUD-2).
Pad positions are asserted by Draw.pad: a moved part stops the build.
"""

S, P = 0.2, 0.3          # signal, gate / GND bar widths
FIRE = 0.5               # 20 ms fire-only copper (AUD-6)
RAWW = 0.4               # RAW_ACT branch to TP120 / the sense divider


def draw(d):
    t, link, via = d.track, d.link, d.via

    # R134 occupies the removed ARM terminal's west-edge space on B.Cu: straight feed and igniter runs, no fire via.
    link('RAW_ACT', 'B', FIRE, 'Q121.9', 'R134.2')
    link('PYRO1_IGN', 'B', FIRE, 'R134.1', 'J121.2')
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
    # D120's 3V3 clamp rail: its own via into a 3V3 tongue of In2 that reaches it from the east (enclosed on B.Cu by
    # PYRO1_CONT, RAW_ACT and PYRO1_COLD; r10_route_power.IN2_GND_CH1, D-R3-01).
    t('3V3', 'B', S, [d.pad('D120.3'), (18.0, 58.6)])
    via('3V3', (18.0, 58.6))

    # Gate: U1.3 -> R126 (series) -> Q124.4, C126 / R128 (gate-source hold and pull-down), TP122.
    link('PYRO1_GATE_N', 'F', S, 'U1.3', 'R126.1')
    link('PYRO1_GATE_N', 'F', S, 'R126.1', 'R127.1')
    # TP122 (the gate's bare test pad) sits on the bottom (check_actuators; R9 practice): one via beside it, its GND
    # partner 1.49 mm away and >= 1.0 mm from the bare pad's edge (R10_DECISIONS D-R2-11).
    t('PYRO1_GATE', 'B', P, [d.pad('TP122.1'), (14.4, 53.3)])
    via('PYRO1_GATE', (14.4, 53.3))
    via('GND', (15.35, 52.15))
    t('PYRO1_GATE', 'F', P, [(14.4, 53.3), (16.0, 53.3), d.pad('R126.2')])
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
    t('PYRO1_CONT', 'F', S, [(24.0, 55.0), d.pad('R168.1')])
    link('PYRO1_CONT_MCU', 'F', S, 'R168.2', 'U1.15')

    # Bus sense (ARM1_SENSE signal names retained): RAW_ACT -> R132 / R175 -> divider -> R170 -> U1.33 (PC5).
    t('RAW_ACT', 'B', S, [d.pad('Q121.8'), (19.0, 61.58), (19.0, 59.32), d.pad('R132.1')])
    link('ARM1_SENSE_MID', 'B', S, 'R132.2', 'R175.1')
    link('ARM1_SENSE', 'B', S, 'R175.2', 'R133.1')
    link('ARM1_SENSE', 'B', S, 'R133.1', 'R180.1')
    link('ARM1_SENSE', 'B', S, 'R180.1', 'C129.1')
    t('ARM1_SENSE', 'B', S, [d.pad('C129.1'), (27.2, 58.75)])
    via('ARM1_SENSE', (27.2, 58.75))
    # F.Cu (R10_DECISIONS D-R2-09): one 45 deg run parallel to the servo lanes, north as the inner sense lane x 34.4
    # (outside the status-line vias at U1's east pins), west into R170 beside U1.33.
    t('ARM1_SENSE', 'F', S, [(27.2, 58.75), (34.4, 51.55), (34.4, 46.2), d.pad('R170.1')])
    link('ARM1_SENSE_MCU', 'F', S, 'R170.2', 'U1.33', ((31.43, 45.5),))

    # AUD-3: compact facing-source DFN3x3 pair. The source bridge retains the qualified 0.4 mm pulse width;
    # no series via. The gates use F.Cu to cross the bridge, separate from the two MCU controls.
    # Square tee from the bridge; the diagonal passes through C120.1 before the straight R120.1 entry.
    t('ACT_FET_S', 'B', P, [(14.475, 70.1), (16.3, 70.1), (17.37, 71.17), d.pad('R120.1')])
    t('ACT_FET_S', 'B', RAWW, [d.pad('Q120.1'), (12.525, 70.1), (14.475, 70.1), d.pad('Q121.1')])
    for n in ('2', '3'):
        for q in ('Q120', 'Q121'):
            a = d.pad(f'{q}.{n}')
            t('ACT_FET_S', 'B', RAWW, [a, (a[0], 70.1)])
    t('ACT_GATE', 'B', P, [d.pad('Q120.4'), (15.575, 72.3), (16.2, 72.3)])
    t('ACT_GATE', 'B', P, [(16.2, 72.3), d.pad('C120.2')])
    t('ACT_GATE', 'B', P, [d.pad('C120.2'), (18.23, 72.3), d.pad('R120.2')])
    via('ACT_GATE', (16.2, 72.3))
    t('ACT_GATE', 'F', P, [d.pad('TP121.1'), (16.2, 72.3)])
    t('ACT_GATE', 'B', P, [d.pad('Q121.4'), (11.8, 69.0)])
    via('ACT_GATE', (11.8, 69.0))
    t('ACT_GATE', 'F', P, [(11.8, 69.0), (11.8, 70.4), (13.7, 72.3), d.pad('R121.1')])
    t('ACT_GATE', 'F', P, [d.pad('R121.1'), (16.2, 72.3)])
    link('ACT_DRV', 'F', P, 'Q122.3', 'R121.2', ((15.8, 70.14),))
    # PC1 controls the load switch independently of PE4's fire gate. F.Cu stays east of R168 / its GND via, then
    # parallels SERVO1's diagonal on its inner side; no layer change. R123 holds Q122 off while PC1 floats at reset.
    t('ACT_EN_MCU', 'F', S, [d.pad('U1.16'), (24.5, 51.6), (26.6, 53.7), (26.6, 54.6),
                            (19.6, 61.6), d.pad('R122.1')])
    link('ACT_EN', 'F', S, 'Q122.1', 'R122.2', ((19.08, 70.75),))
    link('ACT_EN', 'F', S, 'R122.2', 'R123.1')

    # RAW_ACT: Q121's drain to TP120 and the retained second bus-sense divider top R177.
    t('RAW_ACT', 'B', RAWW, [d.pad('Q121.9'), d.pad('TP120.1', at=(18.0, 67.6))])
    t('RAW_ACT', 'B', S, [d.pad('TP120.1'), (18.0, 65.57), d.pad('R177.1')])
    link('RAW_ACT_SENSE_MID', 'B', S, 'R177.2', 'R124.1')
    link('RAW_ACT_SENSE', 'B', S, 'R124.2', 'R125.1')
    link('RAW_ACT_SENSE', 'B', S, 'R125.1', 'R182.1')
    link('RAW_ACT_SENSE', 'B', S, 'R182.1', 'C122.1')
    t('RAW_ACT_SENSE', 'B', S, [d.pad('C122.1'), (27.2, 64.0)])
    via('RAW_ACT_SENSE', (27.2, 64.0))
    # F.Cu (D-R2-09): a 45 deg run parallel to ARM1_SENSE, north as the outer sense lane x 35.1, west into R172 beside U1.34.
    t('RAW_ACT_SENSE', 'F', S, [(27.2, 64.0), (35.1, 56.1), (35.1, 45.25), d.pad('R172.1')])
    link('RAW_ACT_SENSE_MCU', 'F', S, 'R172.2', 'U1.34', ((31.88, 45.0),))
