# R8 step 6 progress log: signal families

Running log so a successor can resume. Newest entries at the bottom. Scratch: `$SCRATCH/r8_step6/` (session
scratchpad).

## 2026-10-19 start
- Read r8_plan, step 0/1/2/4/5 handoffs, R8_DECISIONS D1-D50, spike RESULT.md (a, b, d), plan_partial,
  make_keepclear.py, r8_power.py, r8_power_check.py, r8_build.sh.
- Board at start: step 5's board, SHA-256 1818b05f... (r8_build.sh output; worktree file matches).

## Infrastructure and first families
- Structure: `m3_design/r8_route.py` (driver + Draw primitives: octilinear / zero-length / two-vias / pad-position
  asserts, `dogleg`, `offset` bus primitive, `u1_pin`), one module per family `m3_design/r8_route_<family>.py`
  (NETS, RAILS, BUDGET, draw), gate `m3_design/r8_route_check.py FAMILY` (rigid, drc+parity, complete, route
  (failures + unrecorded leftovers on done nets / the family's rails), budget, pyro D18/D19, inner, in2, contract =
  check_r8 findings only of the LATER list + check_actuators). Family order: qspi_hse, rf, servo, pyro, usb_swd, imu,
  camera, status, links. KIID seed 8806 + index.
- Dev loop: `$SCRATCH/r8_step6/dev.sh FAM...` restores the step-5 board snapshot (`step5.kicad_pcb`, 1818b05f) into
  the worktree and runs the families with their gates.
- qspi_hse: spike (a) port. Gate OK: 65.5 mm, 9 vias, ratio 1.38.
- rf: spike (d) port + limiter redraw. DRC 0, rigid 12/12 (strip_gcpw kept). Limiter LNA_EN 6.45 / 3.72 (1.73x) and
  VCC_RF 5.00 / 2.61 (1.91x) are inherent (U30 pad row + U30_KEEPOUT; via at the pad's outer end): decision D51 =
  redraw at the minimum + two allowlist entries with measured reasons (D11's agreed fallback, improved), for owner
  acceptance. route_check ALLOWLIST / ROUTE_FIGURES and test_route_check's profile test updated (57 tests OK).
  Gate OK: 434.2 mm, 4 vias (TXEN 2, limiter 2), ratio 1.91.
- Fence row and strip stitching (spike d FENCE_X / STITCH) left to step 7.
- servo: spike (b) port, gate OK (141.0 mm, 4 vias, 1.13).
- pyro: s4 MANUAL + spike (a) ARM lane; RAS_MCU via moved to (31.75, 47.0) (D33's (31.9, 47.0) failed the 2 mm detour
  slack: pin 34 and R172.2 are 0.67 mm apart); GND partners of the exit vias rebuilt (R7 positions); gate OK
  (166.8 mm, 4 vias, CONT 1.37 corridor-forced).
- Placement amendments (D52, r8_place.tsv): D4 rot 270 at y 33.8 (USB lanes cross-free, DM straight from J3.B7),
  R85 rot 180, TP86 to (12.4, 42.9). r8_build.sh rebuilt: placement + power gates OK; new step-5 board 'dacf7ee3...'.
- usb_swd: written and gate OK (148.0 mm signal, 4 signal vias; VBUS 0.3 mm spine x 7.95; FAULT/ILIM under U10's
  body; NRST to J2.3 via an edge via (0.8, 42.75)). Snapshot $SCRATCH/r8_step6/after_usb.kicad_pcb.
- imu: analysis (long): pin order on U1 (SCK, MISO, MOSI, CS, SCL, SDA, INT1 aft->fwd) vs U4/U5 pad sides gives
  inherent crossings; NRST's B diagonal splits the region; 3V3A can take no more vias (extra_vias: already 3 =
  1 needed + 2 slack). Plan: F ribbon over U4 for SPI with vias round U4, B for the crossings; re-place the sensor
  support parts (C30-C32, R11-R13, R64).
- Placement amendments for imu (D52 continued): C30 (12.95, 55.5, 90, B), C31 (12.95, 53.47, 270, B) east of U4;
  R11 to the top (11.25, 56.08, 270, F) beside CS's via; C32 (7.3, 57.48, 90, B); R12 / R13 / R64 in a row below U5
  (y 64, 270, B). r8_build.sh rebuilt: placement + power gates OK.
- imu: written and gate OK (105.6 mm signal, 7 signal vias = one per signal net, 4 critical layer changes, worst ratio
  SCK 1.56 = the pin-order crossing made on F without a second via; 3V3A 50.6 mm, no new 3V3A via). Fixes on the way:
  U5's pads are two rectangles (pad() reports the first); a staircase (C30 stub, trunk, run, U5.2 stub) removed by
  feeding U4's branch through C30.1; pads 6 / 7 GND via kept outside IMU_body_B (y <= 52.16) and clear of the F lanes
  by dropping CS's lane on R11's x. Snapshot $SCRATCH/r8_step6/after_imu.kicad_pcb.
- camera: the old placement needed four vias (U12's B port faced U1, both B-port lanes trapped) and had C100 crossed.
  Re-placed (D55: U12 turned A-port west, C100 under pins 3 / 2, C93 to the bottom, R100 / R101 stood on end, R102 on
  OE's line, TP75 / TP76 / TP91 moved, the CAM_5V divider stood in a column on B.Cu). One inherent crossing (top-side
  part, U1's RX-forward order) made by RX's hop on U12's aft side. Fixes on the way: TX lifted past R78's GND via
  (33.9, 45.2) (a through via), R100 turned wire-pad-aft so J9.2's pour pocket stays open (it was an F.Cu GND island),
  R105's GND pad joined to C94.2 and the divider spaced so the placement gate's DRC has no starved thermal. Gate OK:
  92.1 mm, 6 signal vias, PWR_EN 1.50 (D37 loop).
- Gate change: `complete` now requires GND whole from imu on (two islands found that DRC alone did not fail: J9.2's
  pocket, then a 64 mm2 B.Cu region around U11 / U13 cut off by LOGIC_SOURCE_ST's B.Cu lane; C92.2 got a GND via).
- status: R162 turned (D57), C160 turned. BAT_ENABLE: spike (c)'s y 99.25 lane with its x 16.6 riser closed Q122's GND
  pocket (Q120's drain under it on B.Cu, no via possible); an east riser crosses RAW_PROTECTED's y 99.75 lane; final:
  lane on y 98.45 with a 45-degree step past R175.2, strip GND via (30.6, 99.1) (D58). LOGIC_SOURCE_ST's F.Cu leg
  re-drawn west of R102 and clear of TP76 (D58). Gate OK: 209.4 mm, 8 signal vias, worst ratio 1.20.
- links: r5_maze tried on the 9 connections: sub-0.1 mm end dog-legs on 7 and "no path" at U9.9 (its margin). Drawn as
  explicit polylines with the plan's constraint asserted (D59). Gate OK, every net on the board complete.
- Reservations: make_keepclear.py `--routed` (D60): 500 rows dropped, 29 left (step 7's fence / stitch, C24's GND
  stub and via). Two-pass generation (old placement, then the new placement with the new table) gave the same table;
  regenerated again from the build's own output: byte-identical. r8_route_check gained `reserved` (overlay DRC +
  stale rows).
- Build integration: r8_build.sh runs the nine families with their gates after r8_power_check. First full run stopped
  at the placement gate (R105 starved thermal before copper) -> divider spaced (R105 y 48.7, C94 y 49.95, TP91 y 52.3).
  Second full run: every gate OK, board SHA-256 d9dd1ec7... Third run for reproducibility: see the handoff.
- Tests: test_r8_route.py (new, 12 tests: Draw primitives, run-once, links ratio, GND-from-imu, budget, stale, L10,
  build order). The earlier steps' tests met the step-6 board: test_r8_power's servo-lane test reads "built" lanes now
  (D60); test_r8_place hands the legaliser the rigid R7 copper (r8_legalise `copper=`, the build's own view: it
  otherwise read routed same-net copper at J123's hole and step 6's pyro dives), its reserved-route tests use rows that
  still exist (step 7's stitch via; a 3V3 lane beside SERVO1's built lane). The offset() / dogleg() helpers, unused by
  any family, were removed (offset() broke octilinearity under 4-dp rounding: found by the new test).
- L10 (D61): on the routed board two MCU-side sense dives are < 1.0 mm from bottom courtyards (ARM1_SENSE_MCU: R170 /
  R172 0.635, C15 0.835; PYRO1_CONT_MCU: R168 0.235). No placement reaches 1.0 mm without moving step 5's copper; R7
  had the same class closer (R5_VALIDATION exception). Gated as measured exceptions (`l10`).
- Polish: FAULT_N's B.Cu lane to x 32.35 and BUZZ_DRV's F.Cu lane to y 60.5 (0.5 mm beside their neighbours): GND pour
  fingers 3 -> 1 (the one left is between the I2C diagonals over U5, step 7's). FAULT_N then runs through R76.2 on
  one 45-degree run (a staircase otherwise).
- Final: builds 5, 6 and 7 identical, SHA-256 b7a4d34d7af69fcdeaeb49652264b85393ca9da20d20f875c3da44495e93caae; every
  gate OK (placement, power, nine route gates incl. l10 / reserved); 108 tests OK; check_r8 27 findings, all
  later-step (J9 / J2 legends, strip fence and strip GND reach, the rigid ARM1_SENSE In2 link); keepclear table
  reproduces from the build output; scorecard simplicity index 19.1 (R7 100, target <= 35).
