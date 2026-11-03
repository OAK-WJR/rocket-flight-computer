# R10 round 30: gate lens

- Reviewer: claude. Target commit `0afaed38dafa86edf4453a8bf7b55f9337e41ae1`.
- Board SHA-256 before and after: `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c` (unchanged).
- Probe directory: `.supervisor/r30_gate/` (tree copy from `git archive 0afaed3`; seeds only on copies).

## Totals

Critical 0, Major 0, Minor 0. No real error found.

## Findings

None.

## Fix verification

| Item | Measurement | Verdict |
|---|---|---|
| D-R29-01: rule 3's time constant is about 47–58 µs over C126's ±10 %, labelled | The committed note has the phrase once. R = (220 + 50 ‖ 50 ‖ 1000) ‖ 10000 = 238.6 Ω; with C126 + 2.25 nF the constant is 47.78 / 53.03 / 58.27 µs. Seeds A1–A3 (full revert, label only, range only) all fail the pinned test. A1's regenerated note is round 28's `30796f5e…`. | confirmed |
| D-R29-02: every D-R28-02 … -04 label is pinned | Seeds A4–A12 and A6 each drop one pinned label (the turn-on label and (a)–(f)). All fail `test_r23_binding_note_rules_and_pin_table`, before and after the note is regenerated. Each of the 62 assertIn pins occurs exactly once; each of the 36 assertNotIn pins occurs zero times. | confirmed |
| D-R28-01: one `port_A` | `ports_w` and `loaded_pack` both use `port_A = 1.461 + aux_A`. The budget SHA is `4267634…`. | confirmed |
| D-R28-02 … -04 | Seeds B1–B13 revert each phrase or citation; every one fails the pinned test. | confirmed |
| Round 29 docs (47–58 µs carried) | M3_R10, FMEA I-2, R10_VALIDATION and STATUS all read about 47–58 µs. "47–53 µs" appears only in history rows. | confirmed |

## Seed results (summary)

- **Generator, D-R29 and D-R28 (28 seeds).** Every seed fails the pinned test. K-binding fails on the saved note until the note is regenerated. A hand edit of the saved note alone fails K-binding.
- **D-R27-02 (F1) and D-R27-03 (D1, D2).** All caught:
  - F1 by the pinned test and K-binding;
  - D1 by r10_sch.py's PortTerminal assert and `test_r27_port_terminal_pin_names`;
  - D2 by r10_sch_check (F10 pin names) and the same test.
- **D-R26 (E1–E6).**
  - A missing partner via, or one at 1.56 mm, fails route_check `critical_via_no_gnd` (pad) and the AUX test.
  - R173 at +0.3 mm gives 0.782 mm; R13's via at +0.25 mm gives 0.800 mm; R164's via at (−0.25, −0.3) gives 0.695 mm. The spacing tests fail each one.
  - C10 moved 0.3 mm south is legal: both gaps stay at least 1.0 mm.
- **right_angle (R01–R22, 22 of 77 chamfers, every layer and mode).**
  - Every free square corner fails. J9.1's pad corner fails at `pad`.
  - The overlap, overshoot and partial variants fail on other rules.
  - The remaining passes are outside the rule or caught elsewhere:
    - pad-covered inner corners (C80.2, R432.1);
    - a T (round 24 class);
    - a zero-length segment (DRC `track_dangling`);
    - a non-critical micro-chamfer (counted leftover, R24-GATE-01 class).
- **Budget (C1, C2, F2).** Literal or AUX-less port currents fail `r10_parts --check` as a stale budget until the budget is regenerated, then pass. This is the R26-GATE obs 2 class: no rule binds the figure to a check, and D-R28-01 claims no test.

## Observations (not counted)

The full list is in `round30_gate.json`. In short:

- the budget-figure class above;
- the "; Inference:" prefix in the chatter text is outside the pins, but the parenthetical's pinned label remains;
- 47.78 µs is written "about 47" (rounding, conservative);
- the right_angle passes listed above, each by definition;
- baseline route_check shows 0 FAIL and 5 recorded unrecorded leftovers;
- the binding-note and budget hashes match D-R29-02 and D-R28-01.

## Coverage limits

- The seeds cover 22 of the 77 chamfers.
- No full `tools/check.sh` or `r10_build.sh` was run, as the brief requires. On the tree copy, `test_r10_check` passed 268 tests (6 skipped) and `test_route_check` passed 72.
- Docs were checked only for the D-R29-01 figure.
