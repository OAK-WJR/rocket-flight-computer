# R10 round 29: gate lens (Claude)

- **Target:** commit `09a564e`, board `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c` (SHA-256
  checked before and after: unchanged).
- **Method:** every seed ran on a `git archive 09a564e` copy (or a copy of its board) in `.supervisor/r29_gate/`.
  Generator seeds were judged twice: once with the saved binding note, and once after regenerating it the way
  `r10_build.sh`'s record step does.
- **Totals:** 0 Critical, 0 Major, 1 Minor.

## Finding

### R29-GATE-01 (gate, Minor): the turn-on-delay Inference marking added by D-R28-03 is not pinned

- **What it contradicts:**
  - AGENTS §2.5.
  - D-R28-03 lists "The 30-130 ms turn-on delay is marked as the same model" as one of its new labels. The figure
    rests on C87's 0.72–1.27 × factor, whose DC-bias loss is inferred (D-R19-10).
  - D-R28-03 also says "Test: `test_r23_binding_note_rules_and_pin_table` pins each new label and rejects the old
    Calculation-only forms" (`round28_fix_cad.md`:89 says the same).
- **Seed F6:** in `m3_design/r10_sch_check.py`, the text "... reboots the board after a 30-130 ms EN turn-on delay (the
  same model over C87 0.72-1.27 x)." becomes "... EN turn-on delay.". That is exactly the round 27 text
  (`git show 19dd0b5:m3_design/r10_sch_check.py`).
- **Result:** after the note is regenerated (rc 0), every check passes:
  - `r10_sch_check` (check.sh stage) rc 0;
  - `check_r10 --only K-binding` OK;
  - the pinned test OK;
  - the whole `tools/test_r10_check.py` on the seed copy: 268 tests OK (6 skipped).
- **Why it passes:** the test pins only "after a 30-130 ms EN turn-on delay" (`tools/test_r10_check.py`:452). It has no
  negative pin for the unlabelled form.
- **Contrast:** every other D-R28-03 / -04 label seeded the same way fails the pinned test (B4, C4, E2, F1, F2, F4, F5,
  F7, F9).
- **Impact:** a later edit of the chatter obligation could again state an inferred figure as fact (the R28-TRI-09
  class), and check.sh would pass. The committed note is correct today.
- **Fix:**
  - add "after a 30-130 ms EN turn-on delay (the same model over C87 0.72-1.27 x)" to the D-R28-03 `assertIn` list;
  - add "EN turn-on delay. Resume" to its `assertNotIn` list.

## Fix verification

| Change | Seeds / measurement | Verdict |
|---|---|---|
| D-R28-01 `port_A` | 5.456 V × 1.561 A gives 5.8808312 / 4.3884907 V, equal to budget lines 91–92. Budget SHA `42676342…` matches. `--check` reports "current". | confirmed |
| D-R28-01 literal seeds (A1 `loaded_pack`, A2 `ports_w`) | Caught only as "stale: parts_budget.json" (rc 1). After `--budget-only`, `--check` rc 0 and test_r10_parts OK (A1 5.881014 / 4.388745 V; A2 moves the fire current 1.278747 → 1.278789 A). | known uncovered class (observation) |
| D-R28-02 rule 3 meter criterion | R127 ‖ (R126 + R128) = 0.9109 kΩ. B1 (full revert), B2 ("or open" dropped), B3 ("unpowered" dropped) and B6 (clamp Inference dropped) each fail the pinned test. | confirmed |
| D-R28-03 rule 3 figures and label | B4 and B5 fail. | confirmed |
| D-R28-03 sweep labels | F1, F2, F4, F5, F7, F9 and C4 fail. F3 and F8 (part of a label) pass, but the figure stays labelled. F6 passes everything. | partly (R29-GATE-01) |
| D-R28-04 rule 4 / "before first power" | C1 (revert), C2 (4.5 → 2.5 V) and C3 (0.2 → 1.0 V) fail. C5 (source reference dropped) passes, but the text is not false. | confirmed |
| D-R28-04 obligation 15 | 3.3 / 196 + 4 ms = 20.8 ms and 3.7 / 166 + 4 ms = 26.3 ms. E1 and E2 fail. | confirmed |
| D-R28-04 DS15034 p. 11 | D1 ("pp. 10-11") and D2 ("p. 10") fail. The note's SHA `30796f5e…` is reproduced byte for byte. | confirmed |
| D-R26-01 partners | D1a (dropped) and D1b (moved to 1.56 mm) fail route_check `critical_via_no_gnd` J440.3 and the RealBoardSeeds test. | confirmed |
| D-R26-02 | P1 (R13 via) fails at 0.62 mm. P2 (R173) fails at 0.514 mm. | confirmed |
| D-R26-04 | P3 (R164 via) fails at 0.676 mm. | confirmed |
| D-R27-02 | G1 fails the pinned test. | confirmed |
| D-R27-03 | G2 (J410 back to CameraTerminal, regenerated) fails r10_sch_check's pin names. G3 stops the build in r10_sch.py. | confirmed |
| right_angle (D-R24-17) | Square corners fail `right_angle` (RA1, RA2, RA7, RA9, RA14). Overlap, overshoot and partial variants fail other route rules. A 0.05 mm chamfer on a critical net fails `short_segment`. A zero-length segment fails `micro_segment`. T stubs fail `dead_copper` (RA12, RA13). | confirmed |

## Observations (not counted)

1. **D-R28-01 literal regressions.** Once the budget is regenerated, they pass every check, and the docs' 5.880831 /
   4.388491 V would no longer match. This is the R26-GATE obs 2 / R28-GATE obs 1 class: no rule binds a budget
   figure to a check.
2. **F3 (part of GAP-5's label dropped).** It passes, but "Calculation on allocations … need bench tests" still marks
   the figures as unmeasured.
3. **F8 (the 5.71 V inferred-input clause dropped).** It passes, but the obligation keeps its pinned
   "Calculation / Inference" labels.
4. **C5 (rule 4's "against Q120's source at R120.1" dropped).** It passes; "|VGS|" still defines the measurement.
5. **D-R28-02's negative pin.** It writes "kOhm", while the generator writes "kΩ". The positive pin covers the interim
   form (B2).
6. **K-binding.** By design, it passes any generator seed once the note is regenerated; the pinned test is the guard.
7. **RA10.** A 0.02 mm chamfer on non-critical BAT_FAULT_N passes, with an INFO `micro_segment` leftover: two 135°
   bends, which AGENTS §3 counts without blocking.
8. **RA12 / RA13.** A T stub cannot hide a square bend: `dead_copper` fails it.
9. **P2.** It also fails route_check `dead_copper`.
10. **G3.** It was not carried past r10_sch.py. r10_sch_check's independent PORT_PIN_NAMES would still catch it.
11. **Interim checks during probing.** Before a wrong seed string was corrected, the seed-replacement step failed for
    F7 and G3. Those copies were not judged: both seeds were re-run with the correct string, and only the re-runs
    count.

## Checks run

- Ran:
  - r10_parts `--check` / `--budget-only` and test_r10_parts (A1, A2);
  - `r10_sch_check --binding-note` with KiCad CLI 10.0.7;
  - the pinned SchematicContract test and `check_r10 --only K-binding` on 21 generator seeds, each with the note saved
    and regenerated;
  - r10_sch.py and r10_sch_check (G2, G3);
  - route_check r10 on the base board and 20 board seeds;
  - the three RealBoardSeeds D-R26 tests on the base copy and each D-R26 seed;
  - the full test_r10_check on F6 (268 OK).
- Not run:
  - a full `tools/check.sh` per seed;
  - datasheet re-reads (arithmetic only);
  - pad / via right-angle seeds this round.
