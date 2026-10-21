# R8 step 8 progress log: post and fab

Running log so a successor can resume. Newest entries at the bottom. Scratch: `$SCRATCH/r8_step8/` (session
scratchpad, <scratch>).

## 2026-10-19 start
- No earlier step-8 log. Read r8_plan, step 7 handoff/progress, R8_DECISIONS headings + D8/D9/D15/D20, AGENTS.md,
  r7_post.py, check.sh, check_r8 (inner_signal, rigid, check_board), check_r7 pin_legends / legend_subjects.
- Board at start: step 7's board, SHA-256 52c643d679e54a62... (matches the step-7 handoff).
- Coordinator decisions to record: D63 accepted (P7 = 1, D4.2 pocket), D64 accepted (P9/P10 measured misses).
- Step-8 scope: r8_post.py (silk), J2/J9 legends, ARM1_SENSE In2 item (D15 vs D20), fab package, renders, full gate.
- Baseline DRC on the step-7 board: 163 silk violations; all designators / board texts but ONE footprint graphic:
  Q122's pin-1 silk circle (17.4-17.8, 102.4-102.8) over R122.2's pad (top 102.647). r8_post cannot move it
  (lib_footprint_mismatch). Placement amendment D69: R122 (17.6 -> 18.2, 103.36), R123 (18.9 -> 19.15, 102.5);
  r8_power ACT_EN (17.6,101.8)->(18.2,102.4)->(18.2,102.93)->(19.15,102.93), RAW_PROTECTED starts at (18.2, 103.79).
  Alternatives measured and rejected (R122 +y hits spike (c)'s band GND via (19.6,104.4) / thins the F GND strip;
  Q122 -y limited to 0.12 mm by R175's courtyard; R122 west hits BAT_ENABLE's riser).
- Rebuild with D69 (`$SCRATCH/r8_step8/build_d69.log`): every gate OK, board 303474be...; make_ground --built
  reproduces r8_ground.tsv byte for byte (table unchanged).
- check_r8 D70: RIGID_IN2 exemption (exact R7 segment ARM1_SENSE In2 (14.55,94.15)-(14.55,97.55) w 0.2);
  test_r8_check +1 test (20 OK).
- tools/paste_check.py (paste Gerbers vs pads, 4 rules) + tools/test_paste_check.py (5 OK); on the step-7 board:
  OK, F 348 / B 359 flashes, 20 dry pads.
- m3_design/r8_post.py written (silk from scratch; r7_post helpers; asserts rigid + copper digest).
- r8_post run 1 (no run-on rule): check.sh exit 0 on first try, 84 hidden designators; renders showed run-on text
  ('TP1214:SW', 'R1662:E1+', 'FB31C310', 'Q124R128', 'TP740'), as R7 had ('R33TH1', 'C82C29').
- r8_post: RunOnSilk (no text ends within 0.6 mm of another text on its line, any angle) + place_designator (r7's
  courtyard_designator with RunOnSilk, bottom parts stay bottom, per-part courtyard test). PITFALL: SWIG proxies are
  new objects per call: never compare footprints with `is` (r7_post does; harmless there, fatal in a run-on check).
  Result: 167 designators shown, 82 hidden (R7 90), check.sh exit 0, renders reviewed clean.
- r8_build.sh: appends r8_post.py and tools/check.sh (step gates kept). m3_design/r8_fab.sh written.
- Fab on the post board: jlc_orient CHECK none (jlc_corrections.json: only two "via" comments changed, proxy order);
  export_fab: BOM 92 lines byte-identical to R7's, CPL 219 rows; verify-cpl 85 top + 126 bottom rebuilt, worst
  0.491 mm, 8 placement-only, no errors; paste_check OK (F 348 / B 359, 20 dry pads); manifest OK.
  jlc_stock: U4 short (consigned, as R7); jlc_cost: $106.00/board, 52 extended codes: met. procurement --cost-only OK.
- Next: two full rebuilds (r8_build.sh now ends with post + check.sh), compare SHA with the post board
  (sha in $SCRATCH/r8_step8/sha_post4.txt), then r8_fab.sh, tests, survey, decisions, handoff.
- r8_post report keys made unique per subject (2:GND J1 / J123); board unaffected.
- R8_DECISIONS D68-D72 written (step-8 block).
- Full rebuild 1 (`$SCRATCH/r8_step8/build1.log`): every gate OK, check.sh exit 0, board 6e9498734d597cee...
  = the in-place post board. Project copied to `$SCRATCH/r8_step8/final` for the survey.
- Started: rebuild 2 (build2.log) and the survey (NO_GATE=1 DC_GRID=0.05, survey_final/, ~40 min).
- Full rebuild 2 (build2.log): exit 0, board 6e9498734d597cee... again (two byte-identical rebuilds; netlist 0cc1ed69...
  unchanged).
- r8_fab.sh FAB_NET=1 on the final board (fab_final.log): exit 0 (jlc_stock made non-fatal: U4 consigned); CHECK none;
  BOM 92 lines = R7; CPL 219, verify 85 top / 126 bottom, worst 0.491, 8 placement-only; paste OK; manifest OK;
  r8_top.png / r8_bottom.png; cost $106.00 / 52 extended: met; cost-only procurement OK.
- Tests (KiCad Python): check_shell 2, dc_solve 3, fab_validation 23, fit_check 23, maze_clearances 10, paste_check 5,
  procurement 15, r6_check 17, r7_check 35, r8_check 20, r8_ground 11, r8_place 13, r8_power 7, r8_route 12,
  route_check 57: OK; r5_repair 13 with the known R5-geometry error (routing_lands_spacing, as R6/R7);
  quality_audit 21 OK under KiCad Python and python3.
- step8/post_report.json (r8_post on a copy of the pre-post board reproduces 6e949873...) and step8/paste_report.json.
- Survey running (DC 0.05).
- Survey (survey_final/, DC 0.05): index 16.0; 20 met / 11 missed (C1/C3 3: A8+D51; C2 93; S8/S9 4/2; S15 3.4 D70;
  P6 1788.7; P7 1; P9/P10 4.48/9.65; R6b 0.1157); DC RAW 5.94/17.5 C, BAT 7.00/14.5 C, FET 4.97/21.5 C (= step 7).
- test_r5_repair retargeted to the R5 commit 580d358 (D73; M3_R7's recommendation): 13 OK; R6/R7/R8 boards fail it.
- r8_post is not idempotent on its own output (2nd pass 6c7f5716...): added a run-once guard (refuses a board with the
  J9/J2 pin tables); output from the pre-post board unchanged (6e949873...).
- Handoff written. Rebuild 3 with the final scripts started (build3.log).
- Found in review: place_designator held a BOTTOM part's designator inside its own courtyard box (copied from
  r7_post). Fixed (only a top part's bottom label must sit under it); build 3 stopped. On a copy of the pre-post board:
  C32 now shown (B 5.81, 58.81), 168 shown / 81 hidden, board 429b6db4dc95c1a0..., check.sh exit 0.
- Started builds 3 and 4 (build3.log, build4.log) with the final scripts. Then: r8_fab.sh FAB_NET=1, quick survey
  (copper identical), post_report.json regenerate, handoff numbers (hash, hidden list).
- Builds 3 and 4 (final scripts): exit 0, both 429b6db4dc95c1a0fd3e... (final board). r8_fab.sh FAB_NET=1
  (fab_final2.log): exit 0, cost $106.00 / 52 (23:51Z), manifest bound to 429b6db4 (173 inputs), BOM be711876 = R7,
  CPL d26572d3, paste OK. Quick survey on the final board: every non-DC row = the full survey's.
- All 16 tools suites (266 tests) and quality_audit (21, both Pythons) OK on the final state.
- Handoff finalised. Step 8 done.
