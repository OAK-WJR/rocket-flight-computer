# Fix pass 4, agent F5 (board, tools): running log

Start board SHA-256 636a6bdc7234586a659741a3da921335a47197648c29cd9612c8374733847650 (fix pass 3 final).
Scratch: <scratch>/fx4/

## Log
- [1] No previous progress file; started fresh. Reading pass-4 reports/verdicts and F4 handoff.
- [2] Read pass-4 verdicts, F4 handoff/progress, r7_polish, route_check, r7_hygiene.gnd_vias, dc_solve. Scratch fx4/:
  base.kicad_pcb = start board copy; an.sh BOARD TAG (route_check, cref, scan.py, DC); baseline TAG=base reproduces
  F4 (route_check 0/42; cref 864/1122). Tools copied from fx3: router.py (+ --avoidL L:box / V:box via-only,
  --clr NET=mm), segcheck.py, check_route.py, viaprobe.py (legal via spots), try.py (run snippet with r7_polish helpers
  on a board copy), rm_items.py. fx4/build_hyg.sh regenerates the post-hygiene board (fx4/hyg.kicad_pcb) for dev.
- [3] Item 5 (SWCLK via >= 2 mm from Y1.3) explored: router finds NO F/B route for SWCLK with vias kept >= 2 mm (edge)
  from Y1.3 (nor with In2 + 3V3 blocked), even with BUZZ_DRV's local copper removed (fx4/rt, w/nobz). Constraints
  measured: the F exit between U1.25/U1.26 is the line x+y=75; SERVO4_MCU via (25.30,50.51) needs >= 0.72 mm, ARM1_SENSE
  In2 x=25.88 caps via x <= 25.36, RAW_ACT_SENSE via (23.03,49.3) forces any B run north of the crystal to y >= 49.835,
  so the only via spots are (25.25,49.75)/(25.3,49.7), reachable from y 49.85 only by a 0.14-0.21 mm jog; (25.15,49.85)
  needs SERVO4's via onto x 25.3752, which ARM1_SENSE In2 refuses (0.105 mm). BUZZ_DRV then has no path either.
  Deferred; record if nothing better.
- [4] Dev chain validated: fx4/hyg.kicad_pcb (build to r7_hygiene) + r7_polish + r7_post == start SHA 636a6bdc (fx4/rep).
- [5] Tools (written, unit-tested): r7_hygiene.GndFit (gnd_vias' legality as a class, window-limited) + gnd_spots (0.025
  mm grid) + gnd_vias(fine=); route_check: nognd_audit (gated: allowlisted critical_via_no_gnd fails if gnd_spots finds a
  spot; base board flags PYRO1_GATE_N (22.9,89.555) 0.5 mm 1.229 mm, none else), pad_pour_cut (POUR, gated: pad touching
  its pour when refilled without fill keep-outs but not as saved; base: 13 pads = the 5 of P4-REGRESSION-02 + J2.5,
  U4.2/3/6/7, U5.3/4/5), pour_finger ignores pad relief rings (outline + PAD_RING 0.75 mm: spokes are not fingers; the
  C150/C30 "fingers" left after ring protection were only spokes, no legal stitch spot), LEFTOVERS + leftover_check
  (gated record of non-critical detour/extra_vias/tiny_jog/short_segment). NOTE KiCad 10.0.6 quirk: Python-GC of a
  Remove()d ZONE breaks SWIG types for all boards -> keep-outs are disabled, not removed. tests: test_route_check 32 OK,
  new tools/test_dc_solve.py 3 OK. dc_solve reads the stack-up from the board file (In1/In2 30 um).
- [6] r7_polish: pyro1_cont = 6-via plane-preserving route (47.53 mm, GND vias (35.18,61.05) 0.6, (40.93,78.65) 0.6,
  (28.55,87.21) 0.5; gap to PYRO1_GATE_N 1.080 mm asserted >= 1.0); new stages band (NRST step inside via, SCK/NSS
  steps later: staircases 4 -> 2), debris (10 redraws), rf_relief (C302.2 thermal), gnd_vias (+fine), gnd_vias2;
  pour_trim keeps pad rings + asserts no pad loses contact (19 areas on dev board). First dev run fx4/d1 in progress.
- Router searches for non-critical detour/over-via nets: fx4/det/r1 (+ r2 reruns, full window; router fix: own PTH
  holes no longer block the start).
- [7] Dev run d1 (no reroutes): gate DRC/unconn/parity/ERC 0, R7 contract OK, route_check 0 failing / 37 allowlisted /
  0 audit / pad_pour_cut 0 (after limiting pad_pour_cut to R7_POUR_TRIM_* areas: J2/IMU/BARO body keep-outs are design
  keep-outs); 34 non-critical leftovers to record. Pad contacts: C7.2/C150.2/C30.2/C31.2/R64.2 back to pass-3 values.
  cref (R6 method) 864 -> 603 lost, 1122 -> 861 new; groups identical; CH1 pyro copper 0.00000 mm2 changed; In2 3V3
  island under U1/U4 72.15 mm2 / 4 vias again (was 41.93 + 22.69). gnd_vias added only (22.85, 89.63) 0.6 mm.
- [8] Added stage reroutes (CAM_UART_OE 44.1/6 -> 30.7/4; NRST J2 branch off In1, 6 -> 4 vias); TRIM_EXPECTED 21.
  LEFTOVERS written in route_check (26 entries so far; BAT_SW_RETURN/SOURCE, CAM_5V_SENSE, LED_RED, SERVO2_MCU pending
  full-window searches fx4/det/r4). Tests: route_check 32, dc_solve 3, r7_check 34, fit 23, r6 17, maze 10, check_shell 2,
  fab 23, procurement OK, quality_audit 21 x2 OK; r5_repair known error. Dev run d2 (with reroutes) in progress; then
  final r7_build.sh.
- Item 5 (SWCLK/crystal): no copper change (constraints in [3]); GND B.Cu: 39 -> 35 polygons overall, crystal island
  133.2 mm2 / 27 vias unchanged. DC (stack-aware) start board 0.1 mm: RAW_ACT 3.95, BAT_IN J1->Q120 4.55 (was 3.91 at
  35 um), ACT_FET_S 1.36, BAT_IN J1->U9 15.14 mOhm.
- [9] Final: r7_build.sh (clean, from R6) exit 0, gate passed; board SHA c6fe595cafb91b088ac0b2c812f409f9ca5b86ac45a651102e168b0a5d83c7c7
  == dev chain d2. route_check 323 / 0 failing / 37 allowlisted / 0 audit / 34 leftovers recorded. scan.py 969 -> 958.
  cref 603 / 861. Fab regenerated (BOM/CPL identical, manifest bound). All tests OK (r5_repair known error).
  Leftover searches: det/r3 (0.05 mm), det/r5 (0.1 mm whole board for the long/no-path ones). Band alternatives
  verified colliding with segcheck. Handoff written (fix4_F5_handoff.md); DC table (stack-aware, base vs final at 0.1,
  final heavy paths at 0.05) running in fx4/an/dc*, to be pasted into handoff §5.1.
- [10] DONE. DC table complete (handoff §5.1). Standalone tools/check.sh on the final board exit 0; board SHA
  c6fe595cafb91b088ac0b2c812f409f9ca5b86ac45a651102e168b0a5d83c7c7. Handoff: fix4_F5_handoff.md.
