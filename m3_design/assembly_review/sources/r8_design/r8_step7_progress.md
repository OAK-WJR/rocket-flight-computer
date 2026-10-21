# R8 step 7 progress log: ground

Running log so a successor can resume. Newest entries at the bottom. Scratch: `$SCRATCH/r8_step7/` (session
scratchpad).

## 2026-10-19 start
- No earlier step-7 log. Read r8_plan, step 0/1/4/5/6 handoffs, R8_DECISIONS D9-D61 (ground-relevant ones closely),
  plan_partial/cleansheet/incremental ground sections, survey_baseline P rows.
- Board at start: step 6's board, SHA-256 b7a4d34d7af69fcd... (worktree file matches the step-6 handoff).

## Baseline on the step-6 board (survey, NO_DC)
- route_check: 1 failure (GND pour finger F.Cu between the I2C diagonals over U5), C6 = 2 (A8 + finger), C2 109
  (22 power_via_no_gnd). check_r8 step-7 findings: fence (no fence vias at all), strip GND reach (F 11.25 mm, B 6.45).
- P7 11, P9 11.55, P10 23.51, P11 10.03, P6 1495.

## Design (scratch prototypes in $SCRATCH/r8_step7: legal.py, proto.py, lbound.py, view7.py/view.sh, trial.sh)
- Structure chosen: table-driven like steps 4-6. Generator `sources/r8_design/step7/make_ground.py` (design time,
  deterministic) writes `m3_design/r8_ground.tsv`; build stage `m3_design/r8_ground.py` draws it (once, KIID seed
  8815, native fill, rigid asserted, no via re-netted); gate `m3_design/r8_ground_check.py` (to write).
- Legal-spot model = polygon booleans (legal()): board rules + margins, pyro D 0.5 from all pyro/arming copper,
  no via on GND tracks, GND SMD pads 0.3, paste 0.1, mask (vias_in_smd_pads), holes, no-via rule areas, outer power
  pours whole, In2 power islands whole inside the 7.7 A corridors (run_dc terminal box + 2 mm), In2 antipads kept
  off B.Cu tracks over non-GND In2, edge 1.0, y >= 23.55 (strip_gnd rigid; fence row excepted), no revival of
  dormant GND islands (except island step), no via on the body of a 2-3 pad part (convex hull of its pads).
- Order: trims, fence/stitch/C24 (fixed, spike d/a) -> refill -> power returns (1.5 mm) -> 4 mm grid (x 3+4k,
  y 27.3+4k, snap 1.0, skip if a GND via within 2.0) -> cover (outer GND pour points within 3.0, min gain 6) ->
  refill -> island rounds (revive allowed) -> report.
- Trims (fill keep-outs R8_POUR_TRIM_G1-G6, outlines on lane centre lines): the U5 I2C finger and five 1-via
  islands no second via can reach (IMU F strip, U4 via ring on B, band via ring at Q120, strip crumb at U31,
  B strip under U8). Generator asserts only GND fill inside the outlines went.
- P9 / P10 bounds measured (step-6 board): with every legal spot of the step-7 rules: P9 >= 3.97, P10 >= 9.42;
  DRC-minimum rules, every spot filled: P9 >= 3.43 (4.9 % share), P10 >= 8.67; any placement keeping the 7.7 A
  corridors whole: P10 >= 8.67 at the west edge (0.25, ~90): the RAW_ACT west pour is RAW_ACT on F, In2 and B.
- Trial t8 (table g8.tsv, 193 vias, 1 track, 6 trims): route_check OK (C6 = 1 = A8), P7 1 (D4.2 pocket:
  enclosed by the USB DM/DP flow-through lanes, no legal spot), P9 4.48, P10 9.65, P11 2.90, P6 1789 (+294 mm of
  In2 antipads), R rows unchanged, check_r8: fence and strip reach clear; only J2/J9 legends (step 8), the
  ARM1_SENSE In2 open item, and LS120 model (scratch-dir artefact).

## Integration
- Body rule added (no via on a 2-3 pad part's body; 20 vias of the first trial sat under L1/L3/C72/C73/R134/R166...)
  and island-step revival (C75/C91's B island got its second via through a revived F pocket); trim G6 (B strip under
  U8). Table: 200 rows (193 vias: fence 25, stitch 2, c24 1, return 17, grid 88, cover 57, island 3; 1 track;
  6 trims). `m3_design/r8_ground.tsv` generated from the worktree step-6 board (b7a4d34d) = scratch g8.tsv.
- route_check: TRIM_PREFIXES ('R7_POUR_TRIM_', 'R8_POUR_TRIM_') so pad_pour_cut covers R8 trims (step 5's L1 too);
  test_route_check extended; 57 OK.
- `m3_design/r8_ground_check.py` written (14 gates). r8_build.sh appends r8_ground.py + gate.
- In place on the worktree board: r8_ground.py -> 52c643d6...; keepclear regenerated (0 rows, 529 dropped, D66;
  make_keepclear wording for step 7); gate: all 14 OK (reach: board p95 4.48 max 9.65, pours p95 2.90 max 5.89;
  one allowed weak island D4.2).
- Gate tightened: WEAK_EXCEPT carries the pocket's via count (1). Tests `tools/test_r8_ground.py` (11, ~10 s) OK.
  KiCad pitfall: board.Remove(item) without a live Python reference breaks SWIG (GetTracks fails / segfault 139);
  use board.Delete(item) (make_ground --built and the tests do).
- DC 0.1 mm (run_dc.sh) on step-6 and trial t8 (= final table): RAW 5.90 mm / 17.6 C / 1.45 mOhm both; FET 4.77 /
  22.5 / 0.19 both; BAT 6.86 / 14.8, 0.41 -> 0.42 mOhm. Two-pass `make_ground.py BUILT --built` = committed table.
- R8_DECISIONS D62-D67 written. test_r8_place.test_reserved_route adapted (temp keepclear row; table empty, D66).
- Full build 1 started (`$SCRATCH/r8_step7/build1.log`).
- Full builds 1, 2, 3 (after a lint pass: unused import, long lines; outputs unchanged): every gate OK (placement,
  power, nine route gates, ground), board SHA-256 52c643d679e54a62... each time; netlist 0cc1ed69... unchanged.
  The trial board t8 (DC-solved) is byte-identical to it.
- Tests: test_r8_ground 11, test_r8_route 12, test_route_check 57, test_r8_power 7, test_r8_place 13, test_r8_check 19,
  test_check_shell 2, test_dc_solve 3, test_fit_check 23, test_r7_check 35: all OK. test_fab_validation: 2 failures,
  the R7 CPL against the moved parts (step 8 regenerates the fab package; unchanged by step 7).
- check.sh: stops at DRC with 163 silkscreen violations only (step 8); unconnected 0, parity 0, ERC 0. Run apart:
  metadata audit fails on the same silk DRC classes only; silk_check: silk outside the outline (step 8); check_r8:
  J2 / J9 legends + the ARM1_SENSE In2 open item only; route_check OK; check_actuators OK; fit_check OK.
- `sources/r8_design/step7/bounds.py` (design aid) reproduces D64's floors from the built board (--built): any
  p95 3.30 / max 8.67; rules (current D62 model, with the body rule) p95 4.32 / max 9.42. D64 updated (the earlier
  3.97 was the model before the body rule).
- 0.05 mm DC solves started in the background on the final board ($SCRATCH/r8_step7/dc005).
- 0.05 mm DC on the final board: RAW_ACT 5.94 mm / 17.5 C / 1.45 mOhm; BAT_IN 7.00 / 14.5 / 0.42; ACT_FET_S 4.97 /
  21.5 / 0.18 (D49: 5.93 / 7.00 / 4.97 mm). D67 and the handoff updated. Gate report regenerated
  (step7/ground_report.json). Handoff written (r8_step7_handoff.md). Step 7 done; open: P7 = 1 (D63), P9 / P10 floors
  (D64).
