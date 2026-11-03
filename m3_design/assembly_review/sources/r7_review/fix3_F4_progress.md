# Fix pass 3, agent F4: running log

Start board SHA-256 7660620cfa834e4d381d2a2638780e9a341341c9b93c6e6f526791204dc77c9c (fix pass 2 final).
Scratch: <scratch>/f4/

## Log
- [1] No previous progress file; started fresh. Read pass-3 verdicts (findings extract in scratch f4/findings.txt).
- [2] Work dir scratch fx3/ (NOT f4/, which is F3's old dir). fx3/base.kicad_pcb = start board copy (+pro/dru, kilib
  link); fx3/an.sh BOARD TAG runs groups/pyro-xor (vs base), route_check, cref (R6 method + extended), scan.py, DC
  (heavy nets, 4 dp) and 3V3 DC into fx3/an/TAG_*. Baseline TAG=base: route_check 0 failing / 20 allowlisted;
  cref 603 / 861 (R6 method), 874 / 2659 (extended) = F3's numbers.
- Plan: (A) route_check upgrades + pour checks + tests; (B) new build stage m3_design/r7_polish.py (after
  r7_hygiene, before r7_post) with all board changes (reroutes, redraws, via moves, keep-out rule areas);
  (C) check_r7 / fit_check; (D) r7_post silk; (E) build x2, gate, tests, analyses, handoff.
- [3] tools/route_check.py upgraded (UNTESTED by unit tests yet): short_segment (hygiene), tiny_jog inside longer runs,
  graph island nodes (graph(island_nodes=True)) + dead(pour_islands=True) incl. pour-ended stubs (pad-group test),
  r7_hygiene's dead stage now calls rc.dead(nc, pour_islands=False) (keeps the build's upstream output identical),
  net-level detour / extra_vias (hygiene, critical nets; DETOUR_MAX 1.6 + 2 mm slack; VIA_SLACK 2), pour_sliver
  (<0.25 mm, >3 mm, all pour nets) and pour_finger (GND, <0.5 mm, >3 mm, any point >4 mm through copper from a GND
  via / plated GND hole) gated, power_via_no_gnd info, --routes report. Base board: 101 failing (dead 40, detour 9,
  extra_vias 10, pour_finger 19, pour_sliver 6, short_segment 13, tiny_jog 4) -> fixes go in the new polish stage.
- [4] SWD reroute exploration (scratch fx3/router.py A* raster router, check_route.py / segcheck.py exact checks,
  edit.py/apply.py board edits). Findings: no F/B path for CAM_PWR_EN at all (even with SWD removed); SWD corridors:
  N (under U1 body, U1 NE corner, east side x 33-36) and S (B x 18.55, F between J122 rows 1-2 at y 73.1, In2 hop
  under the SPI/I2C bundle, B, F diagonal); one track each. Chosen: SWCLK = N (fx3/rt/swclk_f2.json, 62.9 mm, 4 vias,
  F/B only), SWDIO = S (fx3/rt/swdio_f2.json, 54.2 mm, 5 vias, 5.9 mm In2), after removing dead copper
  (fx3/dead_rm.py) and pre-edits fx3/rt/pre1.json (3V3 via (41.135,77.92) -> 0.5 mm at (40.99,77.92); SERVO1_MCU via
  (34.6,58.7) -> (34.6,58.5), its F corner (31.2,62.1) -> (31.0,62.1)). Both pass exact clearance checks.
- [5] NEW m3_design/r7_polish.py (fix-pass-3 stage, to run between r7_hygiene and r7_post; NOT yet in r7_build.sh):
  stages dead (40 tracks), neck, swd (SWCLK N route, SWDIO S route via In2 between J122 rows: F.Cu there would cut
  the RAW_ACT_F pour; ends at x 42.15 because J2's footprint keep-out starts at the pad centres), pyro1_cont
  (staircase removed, GND via (35.8,83.225)->(36.3,83.15)), pyro_corners (GATE_N straight x 21.9, COLD 2-seg, GND
  corner), corners (C17.1, R164 branch, D9.1, J3 GND, C8.2), l1_node, gnd_moves (RXEN / GNSS GND vias nudged, new GND
  via (35.5,29.4) by C160.2), dead2 (1), pour_trim (22 keep-out rule areas R7_POUR_TRIM_n, generated from the fill
  scan). Dev copy fx3/w/w1 (= base + polish): DRC 0 / unconnected 0 / parity 0; route_check left: detour 9,
  extra_vias 10, band + SW_NODE jogs/short segs (to allowlist), 3 stale allowlist entries.
- Decisions: CAM_PWR_EN kept (router with power pours whole returns the present route, 81.9 mm / 8 vias; no F/B
  path). P3-REGRESSION-01 (MOSI-IMU_CS 0.3 mm) NOT feasible: C121.1's corner forces MOSI x-y >= -43.0; IMU_CS/I2C1
  can't move east (SERVO1_MCU via (27.1,68.2), SERVO2_MCU via (26.3,67.4), 3V3 via (30.17,71.17)); MISO-MOSI sliver
  trimmed by pour_trim. CAM_MCU_TX candidate 50.8 mm / 3 vias (fx3/rt/cmt_w1.json; In2 under L1 like the present
  route) pending 3V3 DC check (fx3/an/w1_dc3v3.txt vs w2).
- [6] r7_polish.py now: dead, neck, swd, pyro_corners, pyro1_cont (FULL reroute R168.1 -> R178.1, 41.8 mm, 4 vias,
  2 new GND return vias; replaces the staircase-only edit), corners, l1_node, gnd_moves, dead2, pour_trim (21 areas),
  strip_stitch (3 GND vias: strip GND reach <= 4.0 mm), pour_trim2 (0). fx3/w/w1 = base + polish: DRC 0/0/0,
  check_r7 OK (new: RF_PART incl. Q3x + coverage test, C304 in DNP, In2 launch reference, strip GND reach 4.0 mm),
  check_actuators OK, route_check 0 failing / 42 allowlisted (allowlist rewritten with measured reasons; detour /
  extra_vias entries cite fx3 router runs in fx3/det/*.txt).
- Pending: CAM_MCU_TX candidate DC (fx3/w/w2 = w1 + fx3/rt/cmt_w1.json; dc3v3 running -> an/w1b / w2b), route_check
  tests, check_r7 tests, fit_check (P3-MECH-04), r7_post silk (P3-DFM-06), P3-RQ-02 corridor stitching, build
  integration, analyses, handoff.
- [7] CAM_MCU_TX candidate REJECTED: its 27 mm In2 run splits the 3V3 plane at the buck output: L1.2 -> U1.75 14.25 ->
  29.66 mOhm (fx3/an/w2b_dc3v3.txt vs w1b). Kept as is (P3-RQ-03 NRST broadside stays; record).
  Tests added: tools/test_route_check.py (+8: inner tiny jog, short segment + pad exemption, one-island dead, pour-end
  stub vs island bridge, detour/extra_vias gated, slow-net detour info, pour sliver/finger, power via info) all 27 OK;
  tools/test_r7_check.py (+5: RF_PART incl. Q30-32, coverage, C304 DNP, launch In2, strip reach) 33 OK;
  tools/test_fit_check.py (+1: bare/DNP bottom pads) 23 OK. fit_check.py: bare/DNP exposed bottom pads in the standoff
  rule. r7_post.py: jack legends keep 0.2 mm from vias (JACK_VIA_GAP; 0.25/0.35 found no spot) and 0.8 mm from other
  silk (J31's designator no longer runs on with RADIO); dev run: 83 hidden designators (F3: 89).
- [8] r7_build.sh now runs r7_polish.py (after r7_hygiene). Verified: post-hygiene copper of the new chain == old
  final board copper (fx3/cucompare.py: tracks/vias/fills identical), i.e. r7_hygiene's rc.dead(pour_islands=False)
  keeps the upstream output. Clean build b2: gate exit 0 (DRC/unconn/parity/ERC 0, audit, silk, R7 contract OK,
  routing hygiene 0 failing / 42 allowlisted, actuator OK, fit OK), board SHA 636a6bdc7234586a659741a3da921335a47197648c29cd9612c8374733847650
  (copy fx3/b2.kicad_pcb). Build b3 (reproducibility) and analyses (an.sh b2) running. Next: fab regeneration
  (export_fab.py; BOM/CPL should be unchanged), tests, handoff.
- [9] DONE. Builds b2 and b3 byte-identical: 636a6bdc7234586a659741a3da921335a47197648c29cd9612c8374733847650; gate exit 0;
  fab regenerated (BOM/CPL identical); renders redone; all tests OK except the known test_r5_repair error. Handoff:
  fix3_F4_handoff.md.
