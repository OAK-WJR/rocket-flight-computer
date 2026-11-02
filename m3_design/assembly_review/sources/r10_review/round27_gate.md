# R10 round 27: gate lens

- **Target:** commit `816038c`, board `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c`. The hash is
  the same before and after the review.
- **Reviewer:** Claude.
- **Probe directory:** `.supervisor/r27_gate/`, which holds the seed scripts (`seeds_a.py` … `seeds_f.py`), the seeded
  copies and the logs.

## Totals

0 Critical, 0 Major, 0 Minor. No realistic seed passed the gate.

## Fix verification

| Change | Seed and checker output | Verdict |
|---|---|---|
| D-R26-01 board | The GND vias at (7.4,16.5) and (7.4,20.0) are 1.500 mm from J440.3 and J440.4. Pins 3 / 4 of J410, J420, J440 and J9 are flashed on F.Cu / B.Cu only. `pad_layer_changes` finds J440.3 and J440.4. route_check r10 gives 0 gated failures. | confirmed |
| D-R26-01 gate | Each seed fails `critical_via_no_gnd` (layer 'pad'): **A1** (partner removed) J440.3 at 2.0 mm; **A2** J440.4 at 4.037 mm; **A3 / A4 / A4b** (partner moved to 1.6 mm on the column or diagonally) 1.6 mm; **A5** (a second-layer branch from the pin) J410.3 2.427 mm, J420.4 3.775 mm, J9.3 4.037 mm, J121.1 2.9 mm. | confirmed |
| D-R26-01 K-region | Four refilled voids that reach beyond the pad disc and the partner antipad each fail on the AUX_TX B.Cu run, with 181 samples over no In2 copper: **B1a** partner moved to 1.6 mm; **B1b** a PORT_4V8 via at (6.75,16.2); **B1c** a chained GND via at (7.4,15.75); **B1d** an In2 keep-out. B.Cu runs over the merged void outside the pad disc also fail: **B2a** 20 samples, **B2b** 6 samples, **B2c** 11 samples. | confirmed |
| D-R26-02 | PYRO1_OUT to 3V3 / 3V3A is 1.040 mm. On saved copies, `test_r26_pyro1_out_clear_of_3v3_and_3v3a` fails at 0.514 mm with R173 put back, 0.566 mm with the column back and 0.62 mm with R13's via back. | confirmed |
| D-R26-04 | The gate nets are 1.0585 mm from 3V3 / 3V3A: GATE_N 1.065, GATE 1.0585, GATE to 3V3A 1.145. With R164's via back, `test_r26_gate_nets_clear_of_3v3_and_3v3a` fails at 0.331 mm (19.05,55.25) and 0.676 mm (19.05,55.9). | confirmed |
| D-R26-03 binding note | Each of these edits fails K-binding ("saved firmware_obligations differs"): the saved note's chatter obligation (5.71 → 5.73 V, or 7.50 → 7.63 ms); rule 8's corner (5.71 → 5.37 V); the generator (copy, 7.50 → 7.52 ms) without regenerating. With the same generator edit regenerated, `test_r23_binding_note_rules_and_pin_table` fails. | confirmed |
| D-R24-17 right_angle (re-run) | An exact 90° un-chamfer fails `right_angle` (free) on AUX_TX_WIRE, BAT_FAULT_N, USB_ILIM, 3V3, CAM_5V and RAW_PROTECTED, and so does a 0.5 µm sub-TOL mismatch. A 0.5 mm via at a 0.4 mm bend fails (at='via'), and a 0.6 mm via is exempt, as specified. The stop-short, overshoot and both-short variants (0.01 / 0.05 mm) fail through dead_copper, and also through overlap_only_joint on critical and power nets. | confirmed |

## Observations (not counted)

1. All the requested seeds fail their gates.
2. The D-R26-02 / -04 clearance guards are RealBoardSeeds self-tests, not check_r10 rules. check.sh runs them on the
   checked board, so they still block it.
3. Near-miss right_angle corners are caught by dead_copper on every net. On non-critical nets overlap_only_joint is only
   counted. This repeats R26-GATE observation 5.
4. `pad_layer_changes` reads straight tracks only. That is enough, because arcs fail `arc_segment` on every net.
5. With the J440.3 / .4 inner rings put back (KEEP_ALL, refilled), DRC gives 8 hole_clearance errors at 0.400 mm against
   0.55 mm, plus lib_footprint_mismatch.

## Checks executed

- route_check r10 `scan` / `evaluate` on the board and on seeded copies.
- check_r10 `region_issues` and `k_binding` on seeded copies.
- The two D-R26-02 / -04 RealBoardSeeds tests on six saved copies.
- `test_r23_binding_note_rules_and_pin_table` against an edited generator copy.
- kicad-cli 10.0.7 DRC on the ring seed.
- The five round 26 unit tests on the unmodified board: all OK.

## Limits

- check.sh and r10_build.sh were not run end to end on any seed.
- Most route_check seeds were not refilled; the K-region seeds were.
- The figures in the generated text were not recomputed.
