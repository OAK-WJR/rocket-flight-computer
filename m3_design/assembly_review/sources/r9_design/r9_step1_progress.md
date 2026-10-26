# R9 step 1 (gate first): progress log

Brief: r9_plan.md §4 step 1. Build the rule-based gate (check_r9 P-1…P-11, R-1…R-13, M-2…M-7, LC-1), its tests and
tools (pyro_probe, bridge_table, rule_h_seed, gcpw_solve, tab_windows), route_check profile r9, the R9 scorecard in
tools/, and switch check.sh to the R9 contracts. Verify: every rule fails on a seeded defect; R8 fails exactly P-3,
P-7 and LC-1 (explain differences); gcpw_solve reproduces pass 2's 50.3 Ω within 1 Ω; all tool tests pass.

No earlier handoff exists (r9_step*_handoff.md: none at start). Fresh start.

## Plan

1. [x] Baseline: existing tool tests on the untouched worktree (scratch step1/tests_before.txt).
2. [x] tools/gcpw_solve.py (2-D FV, half domain, lid 3 mm, SOR 1e-8) + validation vs pass 2 (50.3 / 52.2 / 49.0 Ω).
3. [x] tools/pyro_probe.py (geometric A–H/A2 + strict pad rules, independent of DRC).
4. [x] tools/bridge_table.py (P-5), tools/rule_h_seed.py (P-4), tools/tab_windows.py.
5. [x] tools/check_r9.py (all contracts) + check_actuators 15b rule-based (decision recorded).
6. [x] route_check profile r9 (empty allowlist), fit_check derived tie holes.
7. [x] tools/test_r9_check.py: a seeded defect per rule, tool tests.
8. [x] tools/r9_scorecard.py (+ r9_extra_metrics.py, run_r9_survey.sh) with r9_plan §2 targets.
9. [x] check.sh → R9 contracts; test_check_shell updated.
10. [x] Run on R8 (expected P-3, P-7, LC-1; explain differences); full test suite; handoff.

## Log

- Baseline tests (run from tools/, KiCad Python): 17 suites, 272 tests, all OK (scratch step1/tests_before.txt).
- KiCad 10 override experiment (scratch step1/lc_exp.py on an R8 copy): a 0.2 mm local clearance on GND pad TP74
  silenced rule D for a PYRO1_BUS track 0.40 mm away (DRC flags it with no override, and reports "pad clearance
  1.0" with a 1.0 mm override). So a pad/footprint override on ANY net replaces the DRU pyro rules for every pair it is
  in: LC-1 must be board-wide, not only on pyro/RAW/gate/sense/BAT_IN/ACT_* pads. Zone clearances are floors (R8's
  fills honour rules A and D above their 0.15/0.3 mm zone clearances: requalify A 0.501, D 0.501).
- DRC on a scratch copy takes ~1.5 s (only lib_footprint_issues without kilib): rule_h_seed can run DRC per variant.
- tools/gcpw_solve.py written; --validate: coated 49.96 (pass 2 50.3, -0.34), bare 51.995 (52.2, -0.21), launch
  48.79 (49.0, -0.21) ohm; all within 1 ohm. Mesh refinement 0.004 -> 0.002 mm moves Z0 by +0.09 ohm. Z0(gap):
  0.30 50.8, 0.35 51.4, 0.40 51.7, 0.5 52.2, 0.7 52.5, 1.0 52.6, 1.5 52.6 ohm (In1 0.2 mm below dominates).
  Gap for 52.3 ohm: 0.58 mm (fine mesh 52.37 at 0.60). R-5 records 0.55 mm as the re-solved bend limit.
- tools/pyro_probe.py (P-0) written: on R8 A .001, B .170, C .077, D .001, E .300, F .200, H .025 (= requalify);
  G with the P-1b scope fails (GATE_N via 0.219 mm from ARM1_SENSE outside the block); H+ fails 5 pairs (1.025-1.161).
- tools/bridge_table.py (P-5) written: R8 has 10 forbidden pairs, among them Q124.5 (OUT) to C128.2 (GND) 0.970 mm
  (a bridge fires the igniter when armed: outside rule H, rule D 0.5 holds) and C128.2 to R134.1 (IGN) 0.621 mm.
  Reset model: ARM1_SENSE short to GATE_N 0.367 V (= R8P1-PYRO-04 0.37 V); MCU-side lane 0.102 V.
- tools/rule_h_seed.py (P-4) written: on R8, 3 pairs x 8 variants all caught; the pad_override variant is caught by
  LC-1 and pyro_probe only (DRC silent: the override blinds DRC, as the spine prototype found). 2 min 15 s.
- check_actuators.py 15b made rule-based (block_cover, bounding boxes, conservative): R8 fails it (J121/J124/D120
  courtyards + 1 mm and D120.1 outside R8's x 4-42 / y 84 rectangle). New sha 6fa58a41... pinned in check_r9.
- tools/tab_windows.py (T-1): R8 windows equal ORDERING's (west 0.5-6, 48.5-77.25, 86.25-117.5; east 0.5-23,
  104.25-117.5).
- tools/fit_check.py: retention_holes() derives the J122 tie holes (R8: equal to the constants); check_board uses it.
- tools/check_r9.py written (40 rule groups). R8 run (with fit, plate 208.7 Hz, seed): fails 17 rules: LC-1, P-0,
  P-1, P-3, P-5, P-6, P-7, P-9, P-10, P-11, R-1, R-4, R-7, M-2, M-6, K-power-pyro, K-inner (13 s; report in scratch
  step1/r8_check_r9.json). Differences from the plan's "P-3, P-7, LC-1" are explained in the handoff.
- route_check profile r9 (empty lists, D10 baseline); check.sh switched (fit -> plate -> rule_h_seed -> check_r9 ->
  route_check r9 -> check_actuators); test_check_shell updated (2 OK).
- tools/r9_scorecard.py / r9_extra_metrics.py / run_r9_survey.sh copied from the survey with r9_plan 2 targets and
  repo-relative paths; R8 baselines tools/scorecard_r8_r9.json (+ _quick) (R8: hard 13/17, done 15/53).
- tools/test_r9_check.py: 52 tests (every rule: clean base passes, seeded defect fails; tool tests; the R8 failing
  set). KiCad 10 pitfall found on the way: BOARD.Remove() on a loaded board, then freeing it, corrupts SWIG's type
  table for later boards in the process; the tests move items off the board instead (noted in the handoff).
- Reports bound strictly: rule_h_seed and the plate model carry the board SHA; check_r9 P-4 / M-2 / --fit refuse a
  report of another board. Outline check accepts four segments or one rectangle.
- Final runs: all 18 tool suites (324 tests) OK, quality_audit 21 OK (both pythons); check.sh on R8 exits 1 at
  check_r9 (17 rules) after DRC 0 / ERC 0 / parity 0 / audit / silk / fit / plate 208.7 Hz / rule-H suite OK (2 min
  47 s); route_check r9 on R8 fails exactly A8, A2, A3; run_r9_survey.sh geometry-only on R8 gives index 100.
- Evidence in step1_evidence/ (R8 gate report, seeded suite, plate, solver validation, tests). Scratch boards: none
  left. R9_DECISIONS.md D-S1-01 ... D-S1-25 written. Handoff: r9_step1_handoff.md. Step 1 complete.
