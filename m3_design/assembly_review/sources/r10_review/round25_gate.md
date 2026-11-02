# R10 round 25: gate lens

- Target: commit `c4bb56b`, board `92c3ad59174afe1ffe206f6384c8cd9a8962e09647ccd6a8c418b95b5312056f` (before and after).
- Reviewer: Claude.
- Probe directory: `.supervisor/r25_gate/` (seed scripts, seeded boards and checker output).

**Totals: 0 Critical / 0 Major / 0 Minor.** No realistic gate miss was found.

## Fix verification

| Change | What was checked | Verdict |
|---|---|---|
| D-R24-18 (BAT_FAULT_N cut 0.32 mm) | **Board as committed.** Via (17.1, 82.8) to the chamfer is 0.2015 mm; to both legs 0.200 mm. The diagonal is 0.4525 mm. The length rises by 0.023 mm, which matches 1867.023 → 1867.046.<br>**Restore seed.** Putting the 0.36 mm cut back and refilling gives a board byte-identical to `1407e850`, with the gap at 0.1733 mm. | confirmed |
| D-R24-19 (EN text and tests) | **G1:** battery_entry note edited in `r10_sch.py`, sheets not regenerated. Sheet replay FAILs.<br>**G2:** the same edit, sheets regenerated. `test_r21_sheet_notes` FAILs.<br>**G3a:** chatter obligation edited, binding note not regenerated. K-binding FAILs.<br>**G4:** "5.92 V (6.6 ms)" put back and the note regenerated. `test_r23_binding_note_rules_and_pin_table` FAILs. | confirmed |
| D-R24-20 (M-8) | **Baseline:** OK at the six recorded distances.<br>**Board seeds, each FAILs:**<br>- L400 0.1 mm aft (2.405 mm)<br>- R82 (bottom) 3 mm forward (2.325 mm)<br>- R92 rotated 90° (1.775 mm)<br>- TP88 flipped (2.355 mm)<br>- C95 moved clear (stale)<br>- C95 0.4 mm aft (re-record)<br>- R400 moved to the forward edge (wrong edge)<br>**Table seeds, each FAILs:** an entry added for L400, R92 or a missing R999; R400 loosened; R166 on the wrong edge; C95 dropped. | confirmed |
| D-R24-17 (`right_angle`, re-run) | **Sharpened corners:** BAT_FAULT_N F.Cu (16.55, 83.35) and GND B.Cu (14.7, 48.0) each FAIL `right_angle`.<br>**Sharp corner plus a defect:** a wider copy of a leg FAILs `fold_back`; a 0.3 mm stub FAILs `dead_copper`; a 2 µm end offset FAILs `dead_copper`; a zero-length piece passes `route_check` but DRC flags `track_dangling`.<br>`test_r24_right_angle` passes. | confirmed |

## Observations (not counted)

1. **BAT_FAULT_N back at the 0.36 mm cut.**
   - The current gate fails this board only on the hash-bound records: K-binding and F9-1's stale model inputs.
   - `r10_build.sh` regenerates both, so after a rebuild nothing fails.
   - 0.1733 mm is above F8's 0.15 mm board clearance and breaks no stated rule.
   - The 0.200 mm in R10_VALIDATION row 24 is held only by the CHAMFER_CUTS entry and by review.
2. **"EN 1.407 V at 6.0 V" put back and regenerated.** It passes K-binding and the D-R24-19 tests. The tests pin the headline figures, not the 1.401 V intermediate.
3. **A zero-length segment at a 90° corner on a non-critical net.** It hides the bend from `route_check`, but DRC `track_dangling` still fails the gate. The generators also assert against zero-length segments.
4. **M-8's 0.005 mm tolerance.** A listed part 0.004 mm nearer than its record passes. That is a measurement tolerance.
5. **M-8 on a footprint with no courtyard.** M-8 falls back to the footprint's bounding box. The seed, with the part moved 0.3 mm forward, reads 2.418 mm against 2.225 mm with the courtyard, and still fails. Every footprint on the board has its own-side courtyard.
6. **M-8 also holds the BOM- and position-excluded test points.** This is conservative.

## Checks executed

- **Board copy.** `git archive` of `c4bb56b` into the probe directory; `fit_check` and `check_r10` (full) on the unseeded copy: OK.
- **M-8.** `check_r10 --only M-8` on 9 seeded boards; `check_r10.m8` with 6 edited tables.
- **BAT_FAULT_N restore.** kicad-cli 10.0.7 DRC (every severity, with parity), `check_r10` (full) and `route_check r10` on the restored board.
- **Schematic and binding.** `r10_sch_check` on G1 / G2; `--binding-note` regeneration on G3 / G4; the named `test_r10_check` tests.
- **Corners.** `route_check` on 6 `right_angle` seeds; DRC on two of them; the `test_route_check` right-angle tests.

## Limits

- The full `r10_build.sh` was not run on a seeded generator.
  - The board edit plus refill reproduces the generator's 0.36 mm output byte for byte.
  - The binding refresh was read from `r10_build.sh`'s steps, not run.
- Of check.sh's self-test suites, only the named tests were run.
