"""M3-ASSY-R7's route_check exception lists, kept verbatim for the R7 record (tools/route_check.py --profile r7).

The owner accepted these on 2026-10-18 for board c872a3d3... (REQUIREMENTS M2; docs/R7_VALIDATION.md "R7 deviations
for owner acceptance"). R8 uses route_check's own lists (profile r8, R8_DECISIONS D9 / D10); nothing here applies to
an R8 board. Moved out of route_check.py unchanged in R8 build step 1.
"""

# Justified exceptions: (category, net, layer ('via' for via categories, 'net' for detour / extra_vias), (x, y) mm,
# reason). An entry matches an instance of that category and net within 0.02 mm of (x, y). Every entry needs a measured
# reason, and an entry that no longer matches fails the gate (a critical_via_no_gnd entry also fails when nognd_audit
# finds a legal GND via spot for it). M3-ASSY-R7 (sources/r7_review/fix3_F4_handoff.md, fix4_F5_handoff.md):
# "raster search" = scratch A* over F/B/In2 at 0.05 mm with the net's copper removed, every clearance of the board
# (m3.kicad_dru incl. the pyro rules, bare test pads 1.0 mm, Tag-Connect 0.508 mm), the power pours kept whole and the
# crystal kept clear; it does not know the RF strip's fence openings, its GND-only In2 or the module keep-outs.
_BAND = ('radio band fan-in step out of the via rows: the band vias sit in two columns (x 9.4 / 10.0) on 0.5 mm rows '
         'and the F.Cu lanes run at 0.4 mm pitch (fixed by RADIO_DIO1\'s lane at y 27.2 and BAT_SW_RETURN 0.175 mm south of '
         'RADIO_NSS\'s lane), so a lane leaves its via 0.2 mm (BUSY: row 28.2, lane 28.0) or 0.3 mm (MISO_MCU: row 28.7, lane '
         '28.4) off its row: a 45 deg step of 0.2 / 0.3 mm offset is a tiny jog at any length (the class is offset < 0.25 '
         'mm or a middle < 0.5 mm: 0.3 mm gives 0.424 mm). The step cannot sit before the 10.0 column (a 9.4-column lane '
         'on its new row passes the 10.0-column vias 0.075 mm apart; BUSY at y 28.0 at x 10.0 overlaps RADIO_NRST\'s via '
         '(10.0, 27.7) by 0.025 mm), nor be avoided without re-spacing the via columns or rows (the U1-side columns, '
         'RADIO_DIO1 and BAT_SW_RETURN with them: a re-layout of the interface band). With every lane on its via row, the '
         'binding obstacles are D9.1 / D9.2\'s pads (top edge y 30.3: RADIO_NSS\'s lane at y 30.2 would pass them at '
         '0.025 mm) and the GND via (19.71, 30.51), which that lane would overlap (pass 6, P6-ROUTING_GEOMETRY-03(e)). '
         'alt_audit re-measures it on every run. '
         'Fix pass 5 removed the two band staircases (east chamfers lengthened to 1.004 mm; RG-11)')
_NOGND = ('no legal GND via spot within 1.5 mm on the final board: nognd_audit (below, gated) runs '
          'm3_design/r7_hygiene.gnd_spots there on every check (GndFit: r7_route.ViaCheck with board rules +0.02 mm '
          'and no via within 0.15 mm of a GND solder pad, bare test pads 1.02 mm, Tag-Connect 0.528 mm, Pyro D 0.52 mm, '
          'the 7.7 A corridors; 0.6 and 0.5 mm vias; 0.025 mm grid) and finds none; sliding the signal via along its '
          'tracks\' axis by up to 0.6 mm opens none either (fix pass 4, fx4/snip/slide.py)')
_IFACE = ('R7 interface topology (M3_R7 "Interface": west escape to the left-edge B.Cu corridor over In2 GND, the F.Cu '
          'band forward of the strip, lanes between the modules; the strip admits signals only through its fence '
          'openings and holds no In2 signal copper, F10 / check_r7)')
_LIMITER = ('antenna-bias limiter on B.Cu under U30 (M3_R7 "Limiter"): U30.13 / U30.14 are F.Cu pads on the module\'s '
            'aft row and only GND may cross F.Cu / In1 under the module (U30 keep-out, u-blox IM 4.4), so the net leaves '
            '1.9 mm aft to a via outside the module and runs back under it on B.Cu')
_POUR6 = ('fix pass 6 (P6-DOCS-01), a net with a pour: ')
ALLOWLIST = [
    ('tiny_jog', 'RADIO_BUSY', 'F.Cu', (9.4, 28.2), _BAND + ' (0.283 mm step)'),
    ('tiny_jog', 'RADIO_MISO_MCU', 'F.Cu', (10.0, 28.7), _BAND + ' (0.424 mm step)'),
    ('critical_via_no_gnd', 'RADIO_RXEN', 'via', (23.8, 39.45), _NOGND + '; nearest GND via 2.23 mm'),
    ('critical_via_no_gnd', 'RADIO_NRST', 'via', (9.3, 50.0), _NOGND + ' (left-edge corridor); nearest 3.18 mm'),
    ('critical_via_no_gnd', 'RADIO_BUSY', 'via', (9.4, 28.2), _NOGND + ' (band via columns); nearest 1.65 mm'),
    ('critical_via_no_gnd', 'RADIO_BUSY', 'via', (10.0, 49.5), _NOGND + ' (left-edge corridor); nearest 2.60 mm'),
    ('critical_via_no_gnd', 'RADIO_MOSI', 'via', (9.4, 29.2), _NOGND + ' (band via columns); nearest 1.65 mm'),
    ('critical_via_no_gnd', 'RADIO_DIO1', 'via', (10.0, 50.5), _NOGND + ' (left-edge corridor); nearest 3.57 mm'),
    ('critical_via_no_gnd', 'RADIO_MISO_MCU', 'via', (10.0, 28.7), _NOGND + ' (band via columns); nearest 2.11 mm'),
    ('critical_via_no_gnd', 'RADIO_MOSI_MCU', 'via', (9.4, 48.5), _NOGND + ' (left-edge corridor); nearest 1.71 mm'),
    ('critical_via_no_gnd', 'PYRO1_GATE', 'via', (20.45, 92.4),
     'the via sits in TP122\'s 1.5 mm bare test pad (B.Cu), the gate drive\'s test point: a GND via within 1.5 mm of its '
     'centre would come within 0.45 mm of the pad edge, against the 1.0 mm a bare test pad keeps from foreign copper '
     '(check_r7; GndFit 1.02 mm), so nognd_audit finds no spot (fix pass 5: the layer change into a pad is now counted). '
     'The layer change carries no through current: TP122 is a terminal (probe point), the gate is driven on F.Cu; '
     'nearest GND via 2.93 mm'),
    ('detour', 'GNSS_RESET_N', 'net', (14.3, 54.5),
     _IFACE + ': 59.3 mm / 2 vias; the raster search finds 39.3 mm only with a 28.7 mm In2 run through the 3V3 plane '
     'and an F.Cu run crossing the strip fence at x 14.8, outside its openings'),
    ('detour', 'RADIO_DIO1', 'net', (14.3, 50.5),
     _IFACE + ': 69.1 mm / 4 vias; the raster search finds 48.0 mm / 2 vias only with a 39.8 mm In2 run ending inside '
     'the strip (In2 carries only GND there)'),
    ('extra_vias', 'RADIO_DIO1', 'net', (14.3, 50.5), _IFACE + ': 4 vias, as its detour entry'),
    ('detour', 'RADIO_NRST', 'net', (37.0, 14.0),
     _IFACE + ' (and R311 beside U31): 85.4 mm / 4 vias; the raster search U1.56 -> U31.3 finds 51.3 mm only with a '
     '32.1 mm In2 run into the strip'),
    ('extra_vias', 'RADIO_NRST', 'net', (37.0, 14.0), _IFACE + ': 4 vias, as its detour entry'),
    ('extra_vias', 'RADIO_NSS', 'net', (24.2, 20.39),
     _IFACE + ': 58.4 mm / 4 vias; the raster search U1.51 -> U31.14 finds 3 vias only with a 25.2 mm In2 run ending '
     'inside the strip'),
    ('extra_vias', 'RADIO_RXEN', 'net', (25.6, 7.43),
     'fix-pass-2 RXEN route (F.Cu lane x 20.6 between the modules, R312 at U31): 51.9 mm / 4 vias; the raster search '
     'U1.45 -> U31.10 finds 2 vias only with an 18.2 mm In2 run straight under the 3V3 buck (U2, C7, L1: x 19.6-20.7, '
     'y 27-44) through the 3V3 plane'),
    ('detour', 'RADIO_TXEN', 'net', (31.13, 18.95),
     'U31.19 -> U31.9 are on opposite sides of the module and only GND may cross its pad field on any layer (EBYTE '
     'manual 4.1; U31_KEEPOUT, B.Cu and In2 under the whole body), so TXEN runs round the module\'s west side on B.Cu '
     '(M3_R7 exceptions): 25.2 mm / 2 vias; the raster search\'s 12.2 mm path crosses the keep-out'),
    ('detour', 'GNSS_LNA_EN', 'net', (13.0, 13.3), _LIMITER + ': 7.45 mm for a 3.72 mm pad tree'),
    ('detour', 'GNSS_VCC_RF', 'net', (9.7, 12.25), _LIMITER + ': 6.2 mm for a 2.61 mm pad tree'),
    ('extra_vias', 'PYRO1_CONT', 'net', (24.6, 87.2),
     'net copper 53.33 mm (the rerouted chain R168.1 -> R129.2 47.53 mm): fix pass 4 plane-preserving route '
     '(r7_polish.pyro1_cont; fix pass 5 drew its F.Cu run S/SE/S): R168.1 on B.Cu at U1, the divider on F.Cu in the pyro '
     'block, SWCLK/SWDIO and the IMU between; the raster search with every power pour on every layer kept whole '
     '(3V3/3V3A included), 1.0 mm to PYRO1_GATE_N and every pyro rule finds no route with fewer than 6 vias (fx4/rt/pc8, '
     'via cost 15); the 4-via route of fix pass 3 cut the In2 3V3 island under U1/U4 (P4-REGRESSION-01); each layer '
     'change has a GND via within 1.5 mm'),
    ('extra_vias', 'ARM1_SENSE', 'net', (19.2, 92.4),
     '63.7 mm / 4 vias: R170.1 on B.Cu at U1, the divider (R133, R180, R175, C129) on F.Cu in the pyro block; the raster '
     'search R170.1 -> R133.1 (every pyro rule) finds no route with fewer than 4 vias (51.8 mm / 4)'),
    ('extra_vias', 'QSPI_IO2', 'net', (29.4, 59.5),
     '33.3 mm / 3 vias: U1.1 (U1\'s right column) to U3.3 (the QSPI flash north of U1) crosses U1\'s right-side escapes '
     'and the QSPI fan; the raster search finds 31.9 mm / 3 vias at best'),
    ('detour', 'VCAP1', 'net', (18.2, 45.9),
     '6.71 mm / 2 vias for 1.37 mm: C19.1 sits on B.Cu under U1 between its escape vias; the raster search finds '
     'nothing shorter than 5.81 mm / 2 vias (inherited R6; a shorter loop needs C19 moved)'),
    ('detour', 'VCAP2', 'net', (16.0, 60.8),
     '12.67 mm / 1 via for 3.0 mm: U1.73 escapes west and C20.1 sits on B.Cu under U1\'s SW corner; the direct via '
     'spots collide with C17, 3V3, USB_DP\'s via, the SWD lines and TP85 (pass-3 fitprobe) and the raster search '
     'finds the same west loop at 10.75 mm / 1 via (inherited R6; needs C20 moved next to U1.73, '
     'P3-ROUTING_QUALITY-05)'),
    ('detour', 'VBUS', 'net', (6.8, 76.3),
     '8 pads: J3\'s two VBUS contact groups (F.Cu, 4.8 mm apart) and C83 on F.Cu, C28, D4, R9 and U10 on B.Cu: a '
     '42.5 mm tree joining both contacts through C28 and the ESD clamp D4 (USB-C input, inherited R6)'),
    ('extra_vias', 'VBUS', 'net', (6.8, 76.3), 'as its detour entry: 6 vias for F/B pads that interleave'),
    ('extra_vias', 'RAW_PROTECTED', 'net', (35.7, 85.675),
     '12 pads, 3 on F.Cu (U9.6, C82.1, D9.1) and 9 on B.Cu from y 27 to y 104 (U11, C97, R92, TP70, TP81, U7, C71, '
     'R122): a distribution tree whose F and B pads interleave, 7 vias for 143.5 mm (inherited R6 topology)'),
    # fix pass 6 (P6-DOCS-01): poured nets' chain detours and series layer hops, each with its run's measured length
    # (measured_check) and, for a chain detour, alt_audit's gated search for a 1-3 segment redraw (none clean)
    ('chain_detour', '3V3', 'B.Cu', (36.94, 52.65),
     _POUR6 + 'C7 (U12 / C100): 3V3 from the via (36.94, 52.65) round the south end of C11 (B.Cu, 39.4-40.8, '
     '53.9-57.3: C11.1 3V3A, C11.2 GND) and back up into C100.1, 14.37 mm for 5.16 (fix pass 7: 16.32, the two local '
     'bumps at its ends redrawn, P7-ROUTING-01): the north side is closed by 3V3A\'s B.Cu run x 40.1 (y 51.9-54.6), '
     'which ends in C11.1, so both octilinear two-segment routes cross it; a run between C11\'s two pads (0.65 mm gap) '
     'is not taken (bump_audit strict); the local-bump search finds no other shorter window (inherited R6; a shorter '
     'feed needs C100 or C11 moved, or C100.1 its own via into 3V3_In2)', dict(path_mm=14.368)),
    ('chain_detour', 'GND', 'F.Cu', (14.3, 59.0),
     _POUR6 + 'U1.74 (VSS) to its GND via (11.3, 59.3), 6.62 mm for 3.12, round 3V3\'s F.Cu run (12.6-14.3, y 59.5) and '
     'via (12.6, 59.5), which both two-segment routes cross (inherited R6)', dict(path_mm=6.621)),
    ('chain_detour', 'GND', 'F.Cu', (16.35, 45.95),
     _POUR6 + 'U1.49 (VSS) to the GND via (16.35, 43.55) 2.4 mm straight above it: the straight run passes the 3V3 via '
     '(15.85, 44.25) at 0.075 mm (rule 0.15), so the run goes round it (6.56 mm; inherited R6)', dict(path_mm=6.556)),
    ('chain_detour', 'GND', 'F.Cu', (27.65, 29.85),
     _POUR6 + 'GND via (27.65, 29.85) to C99.2, 2.31 mm for 1.78: both two-segment routes cross VLOGIC\'s F.Cu diagonal '
     '(27.905, 29.25)-(28.505, 29.85); the clean three-segment redraws are longer (2.53 mm)', dict(path_mm=2.308)),
    ('chain_detour', 'GND', 'B.Cu', (13.7, 80.6),
     _POUR6 + 'U10.2 to Q123.2, 6.08 mm for 3.42: the two-segment routes cross U10.1 (VBUS) and RAW_ACT\'s via '
     '(12.6, 81.27) (inherited R6)', dict(path_mm=6.084)),
    ('chain_detour', 'GND', 'B.Cu', (32.3, 55.7),
     _POUR6 + 'C23.2 to the GND via (31.5, 53.5), 4.01 mm for 2.53: the two-segment routes cross 3V3\'s B.Cu run to '
     'C23.1 (31.1-32.1, y 54.5); the clean three-segment redraws are longer (4.05 mm)', dict(path_mm=4.014)),
    ('chain_detour', 'RAW_ACT', 'F.Cu', (10.4, 64.67),
     _POUR6 + 'RAW_ACT_SENSE tap (a divider feed, uA) from R177.1 round R182 / R125 to its via (13.7, 65.37), 5.60 mm '
     'for 3.59: the direct routes cross GND\'s F.Cu (11.37, 64.1-65.1) between R177 and R182, and a via beside R177.1 '
     'collides with VBUS_SENSE\'s F.Cu diagonal (8.0, 65.9)-(10.9, 63.0) and USB_DM / USB_DP\'s B.Cu at x 10.05 '
     '(probed, fix pass 6)', dict(path_mm=5.604)),
    ('chain_detour', 'RAW_ACT', 'F.Cu', (12.6, 81.27),
     _POUR6 + 'the same tap\'s end from its In2 / F.Cu via (12.6, 81.27) into R6_RAW_ACT_F, 7.11 mm for 5.12: VBUS\'s '
     'F.Cu run (10.8, 79.95)-(10.8, 81.525)-(11.325, 82.05)-(13.225, 82.05) and C83.1 box the via in (the 0.5 mm2 fill '
     'fragment round it joins nothing), so the run goes round VBUS\'s via (10.8, 79.95) to the fill west of it; the '
     'direct routes cross that VBUS copper (inherited R6)', dict(path_mm=7.108)),
    ('pour_net_hop', '3V3', 'via', (41.0, 77.92),
     _POUR6 + '3V3 into J2.1 (Tag-Connect; its via-in-pad is M2\'s named exception): on F.Cu the feed crosses SWDIO\'s '
     'diagonal (33.43, 69.65)-(41.7, 77.92) into J2 and J2\'s 0.508 mm contact rule, so it runs on B.Cu under J2\'s pad '
     'field between the via (41.0, 77.92) and J2.1\'s via (44.035, 77.92)', dict(path_mm=11.186, vias=2)),
    ('pour_net_hop', '3V3', 'via', (12.5, 89.2),
     _POUR6 + '3V3 In2 feed (7.9, 84.6) -> (21.9, 96.125): In2 between x 12.5 and 16.3 holds the BAT_IN In2 fill '
     '(x < 14) and CAM_FAULT_N\'s and SERVO4_MCU\'s In2 runs (x 14.64-16.0), which an In2 run cannot cross; the 3.8 mm '
     'F.Cu hop passes over them', dict(path_mm=22.974, vias=2)),
    ('pour_net_hop', '3V3', 'via', (35.1, 45.025),
     _POUR6 + '3V3 from B.Cu (33.8, 43.725) to the F.Cu T (36.5, 51.65) through an In2 run in a 3V3_In2 void: on B.Cu '
     'the run crosses 3V3A\'s B.Cu (36.9-39.4, y 48.1), on F.Cu RAW_PROTECTED\'s diagonal (36.15, 47.9)-(38.05, 49.8)',
     dict(path_mm=12.316, vias=2)),
    ('pour_net_hop', 'RAW_ACT', 'via', (13.1, 75.97),
     _POUR6 + 'RAW_ACT_SENSE tap R177.1 (F.Cu) -> R6_RAW_ACT_F (F.Cu) through B.Cu and In2 (a divider feed, uA): F.Cu '
     'is closed by LS120.1, D123.1 and 3V3\'s F.Cu runs (x 11-13.4, y 76.5-80.2), B.Cu by the BAT_IN_B pour from '
     'y 80.9 and Q123 / U10 / R163 (inherited R6)', dict(path_mm=22.291, vias=2)),
    ('pour_net_hop', 'CAM_5V', 'via', (41.3, 32.425),
     _POUR6 + 'U13.1 -> C91.1, both B.Cu: the B.Cu route crosses CAM_IO_3V3\'s B.Cu diagonal (42.8, 32.45)-(40.75, 34.5) '
     'and U13.5 (probed); the 2.4 mm F.Cu hop passes over it (inherited R6)', dict(path_mm=4.614, vias=2)),
    ('extra_vias', 'VLOGIC', 'net', (18.2, 29.4),
     '10 pads, 2 on F.Cu (C84.1 at x 7.5, C99.1 at U11) and 8 on B.Cu (U2, C7, C6, TP83, U11, R60): 5 vias for '
     '66.37 mm (inherited R6 tree; C84, the bulk capacitor, sits 10 mm west of U2; fix pass 5 ended two runs at the U2.2 '
     '/ U2.3 pad centres, +0.1 mm; fix pass 7 took the 0.6 mm F.Cu peak round D122.2 out, P7-ROUTING-01)'),
    ('local_bump', 'USB_LIMITED', 'B.Cu', (33.1, 26.15),
     'fix pass 7: C98.1 (U11\'s input bulk capacitor, B.Cu) to the U11.7 node (30.8, 27.85) leaves the pad\'s top edge NW, '
     'W, SW round BAT_SW_RETURN\'s via (31.9, 26.325) and comes back S (4.35 mm; inherited R6). The shorter redraws bump_audit '
     'finds (S, SW past the GND via (32.2, 27.033), W into the node: 3.4 mm) cut the B.Cu GND copper that is R105.2\'s '
     'only path to that via: R105.2 (GND) leaves the net\'s pad group (r7_polish pad-group check, fix pass 7); between '
     'that GND via and the BAT_SW_RETURN via there is 0.216 mm, too little for the 0.25 mm run'),
    ('chain_detour', '3V3A', 'B.Cu', (35.5, 76.54),
     'fix pass 7 (P7-ROUTING-04 / P7-REGRESSION-02), a net with a pour: the hop from U4.5\'s (VDDIO) via (35.5, 76.54) to '
     'the U4.8 / C31 / C30 node\'s via (37.4, 76.52), 2.505 mm for 1.908: the GND via (36.5, 76.54), U4.6 / U4.7\'s '
     'return via, sits on the straight line 1.0 / 0.9 mm from the two, and the IMU\'s GND ties fill the south side, so '
     'the hop goes round it to the north (NE, E, SE); its gap to that via (0.200 mm) is set by the SE diagonal into the '
     'east via\'s centre, whose line the via positions fix. A drawing short enough to pass the chain test (E leg '
     '0.12 mm lower, fix pass 6) only cut that gap to 0.169 mm. Both vias also join the one 3V3A_In2 island: the hop is '
     'kept as U4.5\'s short path to the 100 nF capacitors at U4.8 (Inference: via-island-via adds about 1 nH)',
     dict(path_mm=2.505)),
]


# Non-critical leftovers (counted, not gated; REQUIREMENTS M2 review items, P4-DOCS-01): (category, net, layer, (x, y),
# measured reason). Every non-critical instance of a LEFTOVER_CATS (hygiene) category must have an entry, and an
# entry that matches nothing fails, as for the allowlist (leftover_check). Filled from the fix-pass-4 searches
# (sources/r7_review/fix4_F5_handoff.md).
_S = ('raster search on the fix-pass-4 board (scratch fx4/det/r3, r4, r5: F/B/In2 at 0.05 mm (r5: 0.1 mm over the '
      'whole board), the net\'s copper removed, every board clearance incl. the pyro rules, a multi-pad net searched edge '
      'by edge over the octilinear MST of its pads and summed). The search blocks every power pour on every layer, a '
      'stricter rule than the board follows (most of these nets run partly through a void of a 3V3 / 3V3A / BAT_IN '
      'pour on In2, P5-DOCS-01(d)), so "no route" or "the best found" holds under that rule only, not for every route '
      'the board would take')
LEFTOVERS = [
    ('detour', 'BAT_FAULT_N', 'net', (11.975, 43.1),
     '39.97 mm / 4 vias for a 22.47 mm pad tree (R89.2 / U9.4 on F.Cu, TP85 on B.Cu, U1.81 on F.Cu; inherited R6); ' + _S +
     ': 31.4 mm / 2 vias, but only with a forced 0.125 mm jog (B.Cu between VLOGIC at x 11.9 and QSPI_IO0\'s via '
     '(12.9, 44.4): the corridor needs x <= 12.365 by the via and x >= 12.385 by VLOGIC) and a via hairpin under U1.81 '
     '(TP87\'s 1.0 mm bare-pad keep-out and C20 leave no via spot on the pin\'s line): kept'),
    ('extra_vias', 'BAT_FAULT_N', 'net', (11.975, 43.1), 'as its detour entry: 4 vias; the search\'s 2-via route needs '
     'the forced jog and the hairpin'),
    ('detour', 'BAT_SW_RETURN', 'net', (15.38, 110.4),
     '160.34 mm / 5 vias for 76.28 mm (J1.4, the external switch return, to R165.1 at (3.3, 39.1): up the east edge, '
     'across the forward end and down the west side; inherited R6); ' + _S + ' (det/r5): 177.7 mm / 7 vias, longer; the '
     'direct west side is closed by the 7.7 A BAT_IN / RAW_ACT pours'),
    ('extra_vias', 'BAT_SW_RETURN', 'net', (15.38, 110.4), 'as its detour entry: the search\'s best has 7 vias'),
    ('extra_vias', 'BAT_SW_SOURCE', 'net', (20.46, 110.4),
     '129.2 mm / 7 vias (J1.3, the external switch source, to R80.2 at (17.1, 24.5), up the east edge; inherited R6); '
     + _S + ' (det/r5): 124.9 mm / 6 vias, with six F/B hops along the strip\'s forward edge (y 23.9-25.1): one via less '
     'for as many layer hops, not simpler'),
    ('detour', 'BUZZ_OUT', 'net', (14.87, 79.8),
     '22.55 mm / 1 via for an 8.76 mm pad tree (D123, LS120 on F.Cu, Q123 on B.Cu); ' + _S + ': 21.7 mm / 1 via, the '
     'present route'),
    ('detour', 'CAM_EN', 'net', (36.7, 84.975),
     '6.95 mm / 1 via for 3.73 mm (R74.2 / R75.1 on F.Cu, U7.2 on B.Cu); its B.Cu leg threads C71.1 / U7.1 (fix pass 5: '
     'W, S, SW instead of the 0.293 mm step, +0.18 mm); ' + _S + ': 7.45 mm / 1 via, longer'),
    ('detour', 'CAM_FAULT_N', 'net', (20.8, 96.175),
     '92.46 mm / 5 vias for 53.69 mm (R76.2 and R77.1 by the camera eFuse, U1.85; across the pyro block and under the IMU '
     'area; inherited R6; fix pass 5 straightened its In2 run: its tiny step and its staircase went; fix pass 6 moved its '
     'In2 run back to x 14.64 through its via down to y 91.85, one 0.78 mm step onto x 15.19, so SERVO4_MCU\'s run is '
     '0.67-0.71 mm away again, -0.55 mm; fix pass 7 took its In2 bump between the vias (16.04, 67.46) and (19.82, 62.35) '
     'out, -2.61 mm); ' + _S +
     ' (fix-pass-4 copper): 78.9 mm but 7 vias'),
    ('extra_vias', 'CAM_FAULT_N', 'net', (20.8, 96.175), 'as its detour entry: the shorter search route has 7 vias'),
    ('extra_vias', 'CAM_MCU_RX', 'net', (17.35, 45.95),
     '32.81 mm / 6 vias; its F.Cu hop (25.85-28.25, y 42.35) between two In2 runs passes over a 3V3_In2 fill bridge (fix '
     'pass 5, measured: on In2 the same run clears every track but cuts that fill); ' + _S + ': 32.1 mm / 5 vias, by four '
     'In2 / F.Cu alternations along y 42.3 under the QSPI flash (In2 runs 4.6 and 2.9 mm, 0.05-0.1 mm grid jogs): one '
     'via less for two more In2 hops, not simpler'),
    ('detour', 'CAM_MCU_TX', 'net', (17.85, 45.95),
     '65.87 mm / 5 vias; ' + _S + ': 66.0 mm / 5 vias, the present route (fix pass 3: the 50.8 mm / 3-via candidate cuts '
     'the In2 3V3 plane at the buck output, L1.2 -> U1.75 14.25 -> 29.66 mOhm)'),
    ('extra_vias', 'CAM_MCU_TX', 'net', (17.85, 45.95), 'as its detour entry: the search\'s best also has 5 vias'),
    ('detour', 'CAM_PWR_EN', 'net', (36.7, 86.625),
     '81.9 mm / 8 vias (R74.1 by the camera eFuse to U1.84; no F/B-only route exists, fix pass 3); ' + _S + ': 59.1 mm / 8 '
     'vias, hopping F / In2 / B / F / B / F / B / In2 / F through the pyro block and under U1 (det/r3/CAM_PWR_EN_0): '
     'shorter, as many vias and more layer hops; the corridor trade-off with the SWD lines is P3-REQUIREMENTS-01 '
     'option (b), for the owner'),
    ('extra_vias', 'CAM_PWR_EN', 'net', (36.7, 86.625), 'as its detour entry: the search\'s best also has 8 vias'),
    ('extra_vias', 'CAM_UART_OE', 'net', (42.175, 45.7),
     'rerouted in fix pass 4 (r7_polish.reroutes): 44.1 mm / 6 vias -> 30.68 mm / 4 vias; ' + _S + ': 33.1 mm / 5 vias. '
     'R102.1, U12.6 and TP91 are on B.Cu, U1.7 on F.Cu, and the run must cross SWCLK\'s F.Cu diagonal (a 2.7 mm In2 hop)'),
    ('extra_vias', 'LED_YEL', 'net', (40.7, 29.4),
     '36.26 mm / 3 vias (R33.1 to U1.37, both F.Cu, across the U1-side radio lanes); ' + _S + ': 36.0 mm / 3 vias, the '
     'present route'),
    ('extra_vias', 'LOGIC_SOURCE_ST', 'net', (30.725, 38.6),
     '58.31 mm / 11 vias (U11.9 / R91.2 and TP87 on B.Cu, U1.82 on F.Cu; inherited R6; fix pass 5 took the step across '
     'its via (30.725, 37.5) out); its F.Cu hop (16.42-18.78, y 48.2) between two In2 runs passes over a 3V3_In2 fill '
     'bridge (measured: on In2 it clears every track but cuts that fill); ' + _S + ': 55.5 mm / 10 vias with 21 mm of '
     'In2 in four runs: one via less, not simpler'),
    ('extra_vias', 'NRST', 'net', (29.4, 47.92),
     'J2 branch rerouted in fix pass 4 (r7_polish.reroutes; off In1): 54.33 mm / 6 vias -> 46.11 mm / 4 vias; ' + _S +
     ': 45.4 mm / 5 vias. C24.1 is on B.Cu, U1.14 and J2.3 on F.Cu, and the J2 branch crosses SWCLK and the SPI1 area'),
    ('detour', 'RAW_ACT_SENSE', 'net', (13.75, 67.4),
     '38.93 mm / 2 vias for a 24.05 mm pad tree (C122, R124, R125, R182 by the servo feed, R172 at U1); ' + _S + ': '
     '41.4 mm / 2 vias, longer'),
    ('extra_vias', 'SERVO1_MCU', 'net', (31.05, 81.25),
     '65.32 mm / 5 vias (D121 / R154 / R150 on B.Cu, U1.22 on F.Cu); ' + _S + ': 62.2 mm / 4 vias, with 14.6 mm of In2 in '
     'two runs under U1\'s SE corner and the SPI1 area: one via less for two In2 runs, not simpler'),
    ('extra_vias', 'SERVO2_MCU', 'net', (32.95, 81.25),
     '76.72 mm / 9 vias (D121, R155, R151 by the servo header on B.Cu, U1.23 on F.Cu; inherited R6). Measured blockers '
     '(fix pass 5, and pass-5 review): its F.Cu hairpin between vias (28.1, 58.6) and (30.1, 60.8) hops C13.2\'s B.Cu GND '
     'tie (x 29.4, y 57.82-59.7): the straight B.Cu run at y 58.6 collides with it, and GndFit finds no legal GND via spot '
     'within 1 mm of C13.2 north of that row to shorten the tie; its In2 hop (26.3, 67.4) -> (24.4, 69.3) crosses '
     'SPI1_SCK\'s B.Cu diagonal; ' + _S + ': the header legs 21.4 mm / 2 vias and 1.8 mm, and no route from D121.3 into '
     'U1.23 under that rule'),
    ('detour', 'SERVO2_OUT', 'net', (25.54, 76.97),
     '34.94 mm / 1 via for 16.9 mm (J122.4 to R151.2; inherited R6; fix pass 7 redrew its In2 run below the pyro block, '
     'S, E, NE -> SE, E, NE, -2.13 mm, the pass-7 review\'s redraw); bump_audit --bumps-all finds no shorter clean '
     'redraw of any window of it; ' + _S + ': 31.4 mm / 1 via only with 0.15 and 0.55 mm jogs on B.Cu in the pyro block '
     '(det/r3/SERVO2_OUT_0); with every segment >= 0.6 mm it needs 3 vias (32.3 mm, rt/s2o_a)'),
    ('detour', 'SERVO4_MCU', 'net', (31.05, 83.55),
     '96.38 mm / 3 vias for 56.3 mm (D121.6, R153, R157 by the servo header, U1.25; fix pass 5 straightened its In2 run '
     'down x 15.505, the 0.36 mm step gone; fix pass 6: one 0.71 mm SE step onto x 16.005 below the 3V3 via '
     '(16.3, 90.525), 0.67 mm from CAM_FAULT_N, same length); ' + _S + ' (fix-pass-4 copper): 97.8 mm / 11 vias'),
    ('detour', 'SERVO4_OUT', 'net', (25.54, 71.89),
     '46.92 mm / 3 vias for 25.74 mm (J122.10 to R153.2); ' + _S + ': 52.4 mm / 6 vias'),
    ('extra_vias', 'SERVO4_OUT', 'net', (25.54, 71.89), 'as its detour entry: the search\'s best has 6 vias'),
    ('detour', 'SWCLK', 'net', (42.365, 76.65),
     'fix-pass-3 route, 62.7 mm / 4 vias, F/B only, out of U1\'s SW corner (SWD is idle in flight); ' + _S + ': 61.0 mm / '
     '4 vias in the same corridor'),
    ('extra_vias', 'SWCLK', 'net', (42.365, 76.65), 'as its detour entry: the search\'s best also has 4 vias'),
    ('extra_vias', 'SWDIO', 'net', (42.365, 77.92),
     'fix-pass-3 route, 53.72 mm / 4 vias; ' + _S + ': 54.0 mm / 4 vias, the present route'),
    ('extra_vias', 'VBUS_SENSE', 'net', (16.1, 71.875),
     '43.13 mm / 4 vias (R110, R9, TP92 on B.Cu, U1.62 on F.Cu); ' + _S + ': 47.2 mm / 6 vias'),
]

# Measured route figures (len_mm, vias: route_check --routes on the final board) of every net with a detour or
# extra_vias entry in ALLOWLIST or LEFTOVERS: the entries' search results and reasons describe these routes, and the
# gate fails when the board's route differs (measured_check).
ROUTE_FIGURES = {
    'ARM1_SENSE': (63.73, 4), 'BAT_FAULT_N': (39.97, 4), 'BAT_SW_RETURN': (160.34, 5), 'BAT_SW_SOURCE': (129.2, 7),
    'BUZZ_OUT': (22.55, 1), 'CAM_EN': (6.95, 1), 'CAM_FAULT_N': (92.46, 5),
    'CAM_MCU_RX': (32.81, 6), 'CAM_MCU_TX': (65.87, 5), 'CAM_PWR_EN': (81.9, 8), 'CAM_UART_OE': (30.68, 4),
    'GNSS_LNA_EN': (7.45, 1), 'GNSS_RESET_N': (59.34, 2), 'GNSS_VCC_RF': (6.2, 1), 'LED_YEL': (36.26, 3),
    'LOGIC_SOURCE_ST': (58.31, 11), 'NRST': (46.11, 4), 'PYRO1_CONT': (53.33, 6), 'QSPI_IO2': (33.26, 3),
    'RADIO_DIO1': (69.09, 4), 'RADIO_NRST': (85.44, 4), 'RADIO_NSS': (58.4, 4), 'RADIO_RXEN': (51.88, 4),
    'RADIO_TXEN': (25.17, 2), 'RAW_ACT_SENSE': (38.93, 2), 'RAW_PROTECTED': (143.53, 7), 'SERVO1_MCU': (65.32, 5),
    'SERVO2_MCU': (76.72, 9), 'SERVO2_OUT': (34.94, 1), 'SERVO4_MCU': (96.38, 3), 'SERVO4_OUT': (46.92, 3),
    'SWCLK': (62.7, 4), 'SWDIO': (53.72, 4), 'VBUS': (42.49, 6), 'VBUS_SENSE': (43.13, 4), 'VCAP1': (6.71, 2),
    'VCAP2': (12.67, 1), 'VLOGIC': (66.37, 5),
}
