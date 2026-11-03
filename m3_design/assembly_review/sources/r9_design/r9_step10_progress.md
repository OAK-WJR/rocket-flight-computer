# R9 step 10 (requalification and records): progress log

Board bound: `m3_design/assembly_review/m3.kicad_pcb`, SHA-256 `fc3d5b34a4bfbaecfbcb44bdf8144c87015fc71be7accf48354f23410e8d0f51`
(step 9's, re-hashed at the start of session 1). Evidence folder: `step10_evidence/`.

## Session 1 (2026-10-24)

- Read the plan, owner decisions, step 1-9 handoffs, survey_constraints §8.4 / §9.4 / §11-§12, R8 step 9's handoff (the
  records precedent). Scratch shim (`<scratch>/s6/inj/nomouse.dylib`) and wrapper (`<scratch>/s9/kicad-cli`) still exist.
- `tools/check.sh` on fc3d5b34: exit 0 (153 s). First attempt failed at the metadata audit only because check.sh
  derives KICAD_PY from the kicad-cli path and the scratch wrapper is not inside KiCad.app (fell back to /usr/bin/python3,
  no pcbnew): run with KICAD_PY set explicitly (environment, no repo change). Reports copied, local paths scrubbed, to
  `step10_evidence/gate/` (check_sh.txt, drc/erc/audit/fit/plate/seed/r9/route json).
- New scripts in `sources/r9_design/step10/`: `requalify_r9.py` (pyro / RF / mech / IMU / probes sections, gate
  functions called, R8 step-9 measurements reused with R9 constants), `run_dc_r9.sh` (supply 26 paths, fire loop, GND
  returns), `binding_note_r9.py`, `m2_sweep_r9.py` (R8 sweep, profile r9, no rigid copper).
- Ran: requalify_r9 (58 s, no section error, no issue) -> `step10_evidence/requalify_r9.json`; reference audit (R6b
  3206 / 31359 = 10.22 %, all own-via antipads but 1 other-via sample) -> `reference_audit*.{txt,json}`; hot-plug
  (identical to step 6: R_b 2.32, feed 3.232 nH, +0.0021 V, x1.028) -> `hotplug_feed.json`; binding note ->
  `r9_binding_note.json` (U1 = R8 map, U4 rot 180, lever x -11.0 / z -2.06, 1.17 g at 1850 dps).
- run_dc_r9.sh first launch: bash 3.2 empty-array bug killed the non-window rows (fixed: `${extra[@]+...}`); the two
  GND-window solves of that launch kept running into `<scratch>/r9/s10/dc`; fire + supply re-launched into `dc2`.
- M2 sweep running in background.
- (found in session 2) Session 1 also drafted `docs/M3_R9.md`, `docs/R9_VALIDATION.md` (with double-brace placeholders,
  FIRE_*, SUPPLY_LINE and GND_SERVO, waiting on the DC solves) and ORDERING's header and section 1; it
  cited D-S10-01 ... 09 without recording them. Its dc2 solves stopped part-way (v33_c9 / v33_fb30 / v33_u3 and both
  GND-window rows hold only the wx banner; the rp_u7 ... cam_j9 rows never started).

## Session 2 (2026-10-24, the "try again" run)

- Resumed from this log. The machine was not rebooted since step 6 (uptime 1 d 23 h): the scratch folder is intact
  (shim `<scratch>/s6/inj/nomouse.dylib`, wrapper `<scratch>/s9/kicad-cli`); no GUI session (`who` empty).
- Board still `fc3d5b34…`. `requalify_r9.json` is bound to the board, to the current `requalify_r9.py` (a44710e9…) and
  to every input it hashes (check_r9, pyro_probe, bridge_table, r9_pyro_check, r9_rf_check, gcpw_solve, the DRU):
  reused, its figures checked against the records below.
- DC: all 32 rows of `run_dc_r9.sh` (gnd, fire, supply) re-launched from scratch into `<scratch>/r9/s10/dc3` (the
  dc2 partials are not used).
- `run_dc_r9.sh`'s queue waited on the oldest solve (the hour-long GND window), so the supply rows sat idle behind it:
  the scheduler now refills a slot whenever any solve ends (`DC_JOBS`, default 8; bash 3.2 has no `wait -n`). Killed
  the first launch and re-ran all 32 rows into `<scratch>/r9/s10/dc3`.
- New `step10/tab_plan_r9.py` -> `step10_evidence/tab_plan.json` (D-S10-03): four tabs, each GND on all four layers
  under its band and >= 5 mm from PYRO_BLOCK: west y 0.5-5.5 and 96.5-101.5, east 8.75-13.75 and 96.5-101.5.
- New `step10/ordering_facts_r9.py` -> `step10_evidence/ordering_facts.json` (D-S10-06): assembly counts (top 76 SMD +
  2 jacks + 5 THT + 14 TP; bottom 136 + 10 TP), edges, J3 legs (C83 1.541 mm from J3.4's slot), J2 (NRST pad 0.483 mm
  from pads 1 / 4 / 5), PYRO_BLOCK contents, staking (no MEMS under C84 / C121), U9 (IN 13.22 mm from J1.1; C88 2.1 mm),
  bottom power pours, jack-to-ESD 0.5 mm, the 7.7 A necks' cut boxes (all three at an FET's courtyard).

## Session 3 (2026-10-25, after the Mac restarted)

- The restart (uptime 16 h 40 min at 11:49) wiped the session scratch folder: the shim, the kicad-cli wrapper and every
  DC output of sessions 1-2 (`<scratch>/r9/s10/dc`, `dc2`, `dc3`) are gone. The repository is intact: board SHA-256
  re-hashed, still `fc3d5b34a4bfbaecfbcb44bdf8144c87015fc71be7accf48354f23410e8d0f51`.
- **A GUI session is now logged in** (`who`: the user on `console` since 2026-10-24 19:10). Probe: `kicad-cli pcb drc
  --severity-all --schematic-parity` straight on the board, no shim, rc 0, 0 violations / 0 unconnected / 0 parity
  (4.3 s). So the shim and the wrapper are not rebuilt (the brief rebuilds them only without a GUI session); this
  session runs `tools/check.sh`, the tests and kicad-cli unchanged (D-S10-15).
- DC: all 32 rows of `run_dc_r9.sh` re-launched at 11:51 into `<scratch>/r9/s10/dc` with `DC_JOBS=8` and the rows in
  the order `gnd fire supply` (the script's own argument: the two hour-long GND windows start first instead of last).
- 12:06: the 30 fire and supply rows done (the two GND windows still running). `fire_raw` 10.06, `fire_bus` 2.41,
  `fire_ign` 2.42, `fire_out` 1.58 mOhm: equal to the figures session 2 had already put in M3_R9 (its dc3 solves before
  the restart). Every output starts with wx's "create wxApp" assertion line (stderr, new with the GUI session), then
  the board line; the evidence copies drop the assertion (D-S10-15, D-S10-17). USB_LIMITED U10:6 -> U11:7 83.02 mOhm
  (R8 52.66: the trunk through U1's interior, D-S7-16; 42 mV at 0.5 A).
- `tools/check.sh` on fc3d5b34 with no shim or wrapper: exit 0 in 214 s, board SHA unchanged. Its reports compared
  field by field with session 1's (shim) reports: drc / erc / fit / plate / route / seed equal but timestamps and paths;
  audit.json differs only in paths, times and the DRC / ERC report hashes (their dates); r9.json differs only in R-5's
  per-part split of the in-window GNSS samples (C303 12 -> 8, C305 8 -> 12, D30 0 -> 2, L30 26 -> 28, R304 36 -> 32;
  total 155 both; verdict OK both): an attribution-order effect, recorded for the review loop (D-S10-18). The session-3
  reports, paths scrubbed and each bound by `bind_report.py`, replace session 1's in `step10_evidence/gate/` (session 1's
  drc / erc / route / audit / plate.txt were not bound; the new ones are).
- New `step10/fire_loop_r9.py` (D-S10-16) and `step10/check_records.py` (D-S10-13; first trial runs found the
  requalification rows that cited only a key or a decision: now each cites a file).
- Records applied this session (D-S10-08 / D-S10-10 had been decided but not written): REQUIREMENTS (F4, F8, F10, P1, P2,
  M2, M3, the retired accepted risk, "R9 acceptance"), AGENTS §1 and §3, README. D-S10-04's Q124 gate-drive figure
  corrected to MARGIN's 2.77 V (D-S10-16). Decisions D-S10-15 ... 18 recorded.
- Tests (26 suites + quality_audit + audit_artifacts) running in the background with the real kicad-cli.
- Tests done (19:12-19:17Z): 26 suites, 474 tests OK, none skipped; audit_artifacts exit 0; git status and the board /
  fab files unchanged by the run. quality_audit failed 4 of 21 in that runner, which exported `KICAD_PY`:
  `verify_board.native_refill_python` prefers the environment's KICAD_PY to the tests' fake tools. Re-run with
  `KICAD_PY` / `KICAD_CLI` unset (as step 9 ran it): 21 OK under python3 and under KiCad python3. A test-hermeticity
  observation for the review loop (D-S10-18), not a board finding. Evidence: `step10_evidence/tests.txt`.
- 12:25: `gnd_servo` done: 0.32 mOhm (R8 0.69 over its own window), 2.5 mV / 0.019 W at 7.7 A, In1 40 %, In2 29 %, B.Cu
  22 %, F.Cu 9 % at mid-path, 151 GND vias carry current, the largest 0.29 A. `fire_gnd` still running.
- Supply table generated from the bound solves into M3_R9 "Power" (no hand transcription); R9_VALIDATION's supply row
  filled. D-S10-19 (MARGIN P1-9 R9 status) recorded.
- 12:27: `fire_gnd` done, the run complete: all 32 rows rc 0 (18:51-19:27Z, 35.6 min). `fire_gnd` 0.81 mOhm (In1 71 %,
  F.Cu 29 %); its two GND vias beside Q124's source pins carry 1.23 and 1.00 A of the 2.8 A, <= 20 ms pulse (under
  0.5 K adiabatic, Inference; recorded, not a rule: the 1 A per-via line is the continuous-current one).
- Evidence: the 32 outputs copied to `step10_evidence/dc/` by a checking copy (wx line dropped, `<repo>` paths, first
  line = board line, refused otherwise); `dc_summary.txt` (the script's table, bound); `fire_loop.txt` by
  `fire_loop_r9.py`: copper 17.70 mOhm, FETs 14.40, board 32.10 mOhm, F7 budget 1.651 A (1.663 without the board) >=
  1.5 A: met. Every DC-dependent sentence (R9_VALIDATION fire / GND rows, D-S10-04's result, M3_R9 power and headline,
  REQUIREMENTS F4 / F7, MARGIN P1-9, STATUS) written from those files by a generator, not by hand.
- STATUS: the R9 section ahead of R8's; R8's heading "owner-accepted, orderable fallback" and its stale "uncommitted"
  lines corrected to its commit 9c8179b (board cc044ea0 verified in that commit); R7 "earlier candidate".
- `check_records.py` OK on the second run (the first run creates `check_records.txt`, which the records cite): 56
  evidence files bound, 151 hashed inputs equal to disk, 10 records free of placeholders, every cited path resolving,
  39 requalification rows each citing a file, 87 stated figures equal to their evidence.
- `r9_step10_handoff.md` written. Final `tools/check.sh` re-run on the finished records started (background).
- Final `tools/check.sh` on the finished records (19:30:26-19:33:45Z, no shim): exit 0, board SHA-256 fc3d5b34 before
  and after; its r9.json equals the bound one but for R-5's GNSS split, a third different one (C303 8, C305 8, L30 34,
  R304 32; total 155), which D-S10-18 now lists. USB_LIMITED's 83.02 mOhm added to R9_VALIDATION C16.
- Final `check_records.py` after the last handoff edits: OK (`step10_evidence/check_records.txt`). Board SHA-256 at the
  end of the session: fc3d5b34a4bfbaecfbcb44bdf8144c87015fc71be7accf48354f23410e8d0f51 (unchanged; step 10 changed no
  copper). Scratch `<scratch>/r9/s10` and this session's check.sh / test report folders in the system temp folder
  deleted (the evidence is in `step10_evidence/`). Nothing committed. Step 10 complete; the review loop is next.
