# R10 round 28: gate lens

- **Target:** commit `19dd0b52`, board `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c` (SHA-256
  the same before and after the review).
- **Method:** the committed tree went into `.supervisor/r28_gate/tree` with `git archive`. Every seed ran on a clone or
  a board copy, refilled before checking. No tracked file was changed.
- **Totals:** 0 Critical / 0 Major / 0 Minor. **No realistic gate miss found.**

## Findings

None.

## Fix verification

| Change | Seed or measurement | Result | Verdict |
|---|---|---|---|
| D-R27-03 | A1: `circuit.json` J410 back to `M3:CameraTerminal`, regenerated with `r10_sch.py` | `r10_sch_check` FAIL: J410 pin names 5V_OUT / GND / RX_FROM_CAMERA_TX / TX_TO_CAMERA_RX, in the checked netlist and in the fresh export | confirmed |
| | A2: `PORT_TERMINAL_PINS` 3 / 4 named RXI / TXO, library copy re-added, regenerated | FAIL on J410, J420 and J440 (6 issues) | |
| | A3: names swapped by hand in the kilib symbol and the sheet's embedded copy, netlist re-exported | exit 1 on the build assertion "kilib/m3.kicad_sym PortTerminal differs from r10_parts" | |
| | Hashes | netlist `535a8fdf`, sheet `695cfa0d`, library `7a3c7d8d` and circuit `3220e5f9` match the record; 3 PortTerminal + 1 CameraTerminal | |
| D-R27-01 | Independent calculation | 5.88101 / 4.38874 V; budget `ecc45417` matches | confirmed |
| | Generator regression (sB1): `loaded_pack` back to 5.456 V × 1.46 A, budget regenerated | lines 91–92 go back to 5.899 / 4.414 V; nothing fails: `r10_parts --check` rc 0, `test_r10_parts` OK, no test or rule pins the figure (observation 1) | |
| | Hand-edited stale budget | `r10_parts --check`: "stale: parts_budget.json", rc 1 | |
| D-R27-02 | sB2a: saved note's `mcu_revision` hand-edited back to the round 27 wording | K-binding FAIL ("saved sources differs") | confirmed |
| | sB2b: generator reverted, note regenerated | K-binding OK, as designed; the self-test `test_r23_binding_note_rules_and_pin_table` FAILS | |
| D-R26-01 | D1a: partner via (7.4, 16.5) removed | route_check FAIL `critical_via_no_gnd`, J440.3 at gnd 2.0 mm; the RealBoardSeeds test fails | confirmed |
| | D1b: partner via 1.56 mm away | route_check FAIL at gnd 1.56 mm; the test fails | |
| D-R26-02 | PYRO1_OUT to 3V3 / 3V3A on the board | 1.0400 mm | confirmed |
| | P2: R13's 3V3 via 0.1 mm south | the test fails at 0.95 mm | |
| D-R26-04 | Gate nets to 3V3 / 3V3A on the board | 1.0585 mm (BUZZ_DRV to PYRO1_OUT 0.7935 mm, as disclosed) | confirmed |
| | P1: R164's 3V3 via 0.1 mm north | the test fails at 0.965 mm | |
| D-R26-03 | sC1: generator's 7.50 ms changed to 7.63 ms, note regenerated | K-binding OK; the self-test FAILS on the pinned words | confirmed |
| right_angle | Seeds on SERVO2_MCU B.Cu (30.55, 71.85), non-critical, and QSPI_IO2 F.Cu (17.0, 49.1), critical; see below | | confirmed |

Right_angle seeds, from the 77 chamfered corners found on the board:
- **Square corner:** FAIL `right_angle` on both nets (RA1, RA2).
- **Second leg ending 0.05 mm short, inside the first leg's copper:** FAIL `dead_copper`, plus `overlap_only_joint` on
  the critical net (RA3, RA8).
- **First leg running 0.05 mm past the corner:** FAIL `dead_copper`, plus `overlap_only_joint` on the critical net
  (RA4, RA7).
- **Square corner plus a duplicate leg:** FAIL `right_angle`, because duplicates are merged first (RA9, RA11).
- **Square corner plus a 0.3 mm overlapping piece:** FAIL `fold_back` (RA10).
- **Zero-length segment at a square corner:** route_check passes; DRC fails it with `track_dangling` (RA6).
- **0.042 mm chamfer:** passes, with an INFO leftover (RA5; observation 3).

`test_route_check` 72 / 72 OK.

## Observations (not counted)

1. **D-R27-01 regression.** A generator regression in `loaded_pack` that is then regenerated passes every check.
   STATUS, parts_qualification and R10_VALIDATION would then quote 5.881 / 4.389 V against a budget of 5.899 /
   4.414 V. This is the class the round 26 triage ruled out (R26-GATE obs 2): no stated rule binds a budget figure to a
   check.
2. **D-R27-02 generator revert.** K-binding cannot see it by design, because it compares the saved note with the
   generator's output. The check.sh self-test catches it.
3. **RA5's 0.042 mm chamfer.** It makes two 135° bends, so the letter of the rule holds. It is reported as an INFO
   non-critical `micro_segment` leftover, which AGENTS §3 counts without blocking. On a critical net it would fail.
4. **RA6's zero-length segment.** It hides the bend from `right_angle`, because the corner then has three track ends.
   DRC's `track_dangling` blocks it in check.sh.
5. **Unflashed via barrels.** The D-R26 tests' `copper_gap` leaves out inner barrels that have no ring: PYRO1_OUT
   (11.63, 55.1) and PYRO1_GATE (14.4, 53.3). S-8 holds those barrels at least 1.0 mm from all foreign inner copper.
6. **Where D-R26-02 / -04 are held.** The spacing is kept by RealBoardSeeds tests that check.sh runs on the checked
   board, not by a check_r10 rule. They fail on a 0.1 mm via move.

## Checks run

- Ran:
  - `r10_sch_check` and `r10_sch.py` regeneration;
  - `r10_parts` `--budget-only` and `--check`, and `test_r10_parts`;
  - `check_r10 --only K-binding`;
  - `route_check --profile r10` on 14 seeded boards and the baseline;
  - DRC on RA6;
  - the D-R26 / D-R27 unit tests, on the baseline and on the seeds;
  - `test_route_check`;
  - `fab_manifest --content` (OK).
- Full `test_r10_check` on sB1 (the D-R27-01 regression copy): 268 tests OK, 6 skipped, rc 0.
- Not run: the full `check.sh` or `r10_build.sh` (the review is read-only), and no physical, firmware or supplier
  checks.

## Coverage limits

- The right_angle seeds use two of the 77 chamfers.
- The pad and via holder cases rely on `test_r24_right_angle`.
- K-region's D-R26-01 exemption was checked by reading the code and by its synthetic test only.
