# R8 step 1 progress log (gate tools first)

Resume from the last entry. Outputs: `tools/check_r8.py` + `tools/test_r8_check.py`, route_check R8 profile (empty
lists, D10 detour baseline), `tools/` scorecard (run_survey.sh, survey_metrics.py, scorecard.py, run_dc.sh) and the
dc neck analysis, `tools/check.sh` wired to check_r8, R8_DECISIONS additions, `r8_step1_handoff.md`.

Scratch: `$SCRATCH/step1/` (session scratchpad; probes only, delete when done).

## Log

1. Read r8_plan, step-0 handoff/progress, R8_DECISIONS D1-D14, REQUIREMENTS F4/F10/M2 (R8 marks), AGENTS, surveys
   (baseline fully; constraints RF/pyro sections), plans (grepped for gate items), check_r7 + tests, route_check
   (lists, detour code, main), check.sh + test_check_shell, dc_solve vs dc_neck (dc_neck = dc_solve + `cuts()`),
   scorecard.py, survey_metrics.py header. Board in worktree is still R7 `c872a3d3`.
2. Inventoried R7 (scratch inv*.py): zones, Edge.Cuts (5 M3 + 2 tie circles), strip copper (197 GND vias, 1 GND
   track), CH1 block nets/copper (exit vias GATE_N (23,88.33), CONT (28.4,88.61), ARM1_SENSE (18.18,91.3)), strip
   parts. Design of hash groups and new checks: see R8_DECISIONS D15+ (written as decided).
3. tools/check_r8.py written (imports check_r7's generic checks unchanged; check_r7.py untouched). Rigid digests
   computed on R7 and pinned (RIGID_BASELINE, 12 groups); stable across a native refill and save/reload; GCPW profile
   unchanged when far tracks, the limiter DC copper or the strip interface leads are deleted and refilled (local).
   check_r8 on R7: hashes OK; known values reproduced: FB30-C6 5.875 mm (pass2_rf 5.87), U30-C6 7.185, U31-C6 9.092,
   FB31-U3 9.896; fence 21 vias, openings 6.3-12.4 / 20.0-23.8 (pass4_rf); stitching 3.90/2.65/1.55/1.55; S15 901.0 mm.
   Expected R7 failures: 27 pin-map rows, TH1-3, R310 rail, NSS/DIO1 strip vias, fence openings > 2.7, PB10/PB14 loader,
   BAT_IN In2 under pyro copper, GATE_N/servo proximity, In2 signal tracks.
4. route_check: R7 lists moved verbatim to tools/route_lists_r7.py; profiles r8 (default: A8 only, empty leftovers,
   D10 baseline) / r7. `--profile r7` on R7 prints exactly the baseline survey's route.txt (OK, 45 / 29). r8 on R7:
   TXEN plain 10.95 -> keep-out-aware 20.11 mm (ratio 2.30 -> 1.25), 43 failing + A8 + 29 unrecorded = 73.
   test_route_check: 50 -> 57 tests, pass.
5. check.sh: check_r8 + route_check --profile r8 replace check_r7; test_check_shell updated (2 pass). Full gate on R7
   (absolute board path; a relative one breaks the pre-existing `cd quality_audit` step): DRC/parity/ERC 0, audit OK,
   silk OK, check_r8 FAIL (expected R8 findings), exit 1.
6. tools/test_r8_check.py: 19 tests, each new check fires on a seeded defect (pin table, pin map, R310, STRIP_B/VIA,
   fence, loader pins, F10 separation, inner power/pyro, gate/servo, close layer pairs, S15/S16, every rigid group,
   GCPW profile, check_actuators hash, line stitching). test_route_check 57 (D10 + profiles). All tool suites pass
   (test_r5_repair's known pre-existing subtest failure unchanged; STATUS.md records it).
7. Scorecard into tools/: survey_metrics.py (default --tools = tools/), scorecard.py (baseline JSON, targets,
   R6b share), run_survey.sh (ROUTE_PROFILE), run_dc.sh (dc_solve --necks with D12 limits), ipc2152.py. dc_solve
   --necks = survey cuts() verbatim + IPC line. R7 FET at 0.1 mm: identical to r7_quick (1.19 mOhm, 2.64 mm, 44.3 C).
   New-tools survey of R7: survey.json identical to baseline; cref identical; route (r7) identical. Full DC 0.05 run
   in progress -> scorecard_r7.json baseline; then quick run -> scorecard_r7_quick.json.
8. R8_DECISIONS D15-D23 written.
9. Added D4 MCU-end check for R310 (+test; check_r8 on R7 now 92 findings). check.sh now makes the board path
   absolute (R7's script failed its audit on a relative path); gate rerun with a relative path: same result.
   Handoff drafted (DC baseline numbers pending). Waiting on survey_r7 (DC 0.05) and survey_r7_quick (DC 0.1).
10. Full survey (DC 0.05) and quick survey (DC 0.1) of R7 with the new tools: scorecards equal the baseline survey in
    every row (G rows absent: NO_GATE; new R6b 0.2791). Installed tools/scorecard_r7.json and
    scorecard_r7_quick.json (index 100.0 against itself; R6 vs R7 142.9). Handoff completed. Final test run: all
    suites pass. Board, check_r7, test_r7_check, check_actuators unchanged. Scratch (scratchpad/step1) deleted.
    STEP 1 COMPLETE.
