# R8 step 4 progress log: placement freeze

Running log so a successor can resume. Newest entries at the bottom.

## 2026-10-19 start
- Read r8_plan, step 0-2 handoffs, spike RESULT.md (a-d), R8_DECISIONS D1-D28, plan_partial, survey_constraints.
- No step-3 handoff exists; the four spike RESULT.md files are the step-3 record. Their proposed decisions
  (spike b 1-3, spike c 1-7, spike d P1-P9, findings) are not yet in R8_DECISIONS; step 4 records the ones it uses.

## Build tooling written (in the repo, uncommitted)
- m3_design/r8_pcb.py (build start: R7 SHA check, netlist (28 pads), rigid copper kept, zones, TH removed, silk keep
  list, placement from r8_place.tsv, legaliser strict (--draft / --propose for design), fill, save, rigid asserts).
  R6_BAT_IN_crossbar_F is kept as a placeholder F.Cu power pour (strip_gcpw fill noise, spikes a/b/d F-1).
- m3_design/r8_legalise.py (rules: courtyards, edge, holes, pad clearances incl. pyro A-H / TP 1.0 / J2, R5 L10
  bottom keep-outs, washers, tie path, strip content, F10, reservations from r8_keepclear.tsv).
- m3_design/r8_place_check.py (step-4 gate: rigid, legaliser, DRC+parity, F10, fit vs R7, tabs (plan of 5), MST,
  contract, actuators, sensor areas).
- sources/r8_design/step4/make_keepclear.py -> m3_design/r8_keepclear.tsv (spike a-d copper + step-4 lanes).
- Scratch design loop: $SCRATCH/r8_step4/{merge.py, build_table.py, ov.txt (overrides), dev.sh, view.sh/view.py}.
  Table = build_table.py merged0.tsv + ov.txt. merged0 = seed + spikes a/b/c/d (spike c's divider dropped).

## Placement decisions so far (to record as D29-D38)
- D30 L10 nudges in the band (R80, R165, R120, D8); D32 RAW_ACT_SENSE divider at J122's aft end (B), RAS lane
  B.Cu x 25.92 -> y 58.1 under the servo lanes -> x 30.6 -> R172 under U1's east pad row (30.6, 48.1);
  D33 VLOGIC divider top at pin 17 (VLOGIC via (26.9, 60.5)), V3V3 divider bottom at pin 18; CAM_5V sense divider
  at pin 35's via; east-face escapes 34/35/41/42 outward; D34 C100/C93 swapped to their own U12 pins, LS120 nudge;
  D36 eFuse U9 cluster aft of J121's L10 zone (U9 (41.5, 85.5)), BAT_IN lane x 41.25, EN spine x 40.42, C87 + TP84
  top on the EN F lane (x 42.9), RAW_PROT F lane x 45.3 -> 42.15 (between J9's pads) -> B y 25.6 to U7 IN;
  D37 camera eFuse U7 (33.8, 30.7) rot -90 with PWR_EN round the west end (x 28.0) to R74 SW, FLT north (R77/R76),
  ILIM/DVDT inside the loop, TPs re-homed.
- Gate (r8_place_check) passes on scratch board b22 (t22.tsv): MST 1631, tabs L 48.5-77.25 / 86.25-117.5, R 104.25+.

## Fit bottom margin, decisions, final build
- Fit gate tightened to per-category margins against R7 (fit_r7 measured on c872a3d3). Worst bottom part was
  1.73 mm (L3) < R7's 2.34; six east-edge bottom parts moved 0.07-0.65 mm inward plus four neighbours (D39). Now
  2.36 mm (C91); bottom support 4.70 (U5), top support 5.008 (TP30), C84 1.37 (R7 0.11).
- r8_place.tsv written from the final scratch table (t29), 203 rows grouped by block with a basis column.
- Decisions recorded in R8_DECISIONS: D29-D39 (step-4 block at the end of the file).
- tools/test_r8_place.py: 13 tests OK (seeded defects for every legaliser rule, rule table, reserved gate).
  test_r8_check, test_route_check, test_fit_check, test_check_shell, test_dc_solve, test_r7_check also OK.
- r8_place_check now writes the board path repo-relative in its report (AGENTS.md: no local absolute paths).
- Final: m3_design/r8_build.sh exits 0, "R8 placement gate: OK", all 11 gates ok. Board SHA-256
  40e516fac14f310f5e5cacfab6c373e088f55caa607d331ef8acdc88b0f91acd, identical on three consecutive builds; netlist
  0cc1ed69... unchanged. Report: step4/place_report.json.
- Full check_r8 on the placed board: 26 findings, all for later steps (listed in the handoff).
- Scratch board copies deleted (only small scripts / tables kept in the session scratchpad).
- Handoff written: r8_step4_handoff.md. Step 4 done.
