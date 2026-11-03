# Round 32 gate lens (Claude)

Commit `3366287`, board `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c` before and after.

**Totals: 0 Critical / 0 Major / 0 Minor real errors.** No findings.

## Fix verification
- D-R28-01 (one port current): r10_parts.py line 416 port_A = 1.461 + aux_A used by ports_w (417) and loaded_pack (450); budget 5.8808312 / 4.3884907 V; revert caught only as stale budget before regeneration. **confirmed (fix present; regression binding is the ruled budget class)**.
- D-R28-02 (rule 3 both-polarity meter check): clause revert, 'both polarities' drop and 'before first power' drop each fail test_r23_binding_note_rules_and_pin_table. **confirmed**.
- D-R28-03 (Inference labels): rule 3 label, fight qualifier, port-map label, rule 4 VSD citation reverts each fail the test. **confirmed**.
- D-R28-04 (obligation 15, rule 4 Q120, DS15034 p. 11): each revert fails the test; 4.5 V -> 3.5 V and 0.2 V -> 1.2 V threshold edits fail. **confirmed**.
- D-R29-01 (47–58 µs): revert to '47–53 µs' fails the test. **confirmed**.
- D-R29-02 (pins): turn-on label drop fails the test. **confirmed**.
- D-R27-02 (Rev 11 exceptions): revert fails the test. **confirmed**.
- D-R26-01 / -02 / -04 seeds and D-R24-17 right_angle: see observations 5-7: all caught. **confirmed**.
- Round 30 corrections (R30-TRI-01 / -02): text-only docs fixes; no gate element in this lens. **not applicable to the gate lens**.

## Observations (not counted)
1. D-R28-01 seed (loaded_pack power 5.456 V x port_A -> 5.456 V x (1.46 + aux_A)): r10_parts --check fails stale ('r10_parts: stale: parts_budget.json'); after regeneration the full tools/check.sh on the seeded copy passes (rc 0, 268 test_r10_check tests OK) with pack_7V4/6V0_four_stall_loaded_V 5.880831 -> 5.881014 V and 4.388491 -> 4.388745 V. Previously ruled class (R26-GATE obs 2 / R28-GATE obs 1 / R29-GATE obs 1): no stated rule binds a budget figure to a check.
2. D-R28-04 obligation 15 sub-figures are not individually pinned: changing '166–196 V/s' to '150–200 V/s' or dropping 'Diodes DS41326 p. 5' passes the pinned test after regeneration (K-binding fails until regeneration). These are arbitrary edits, not reverts of the fix; every revert of D-R28-02 ... -04 / D-R29-01 / -02 is caught.
3. right_angle: a zero-length track at a reverted LED_YEL F.Cu corner (14.4, 44.6) hides the bend from route_check (4 track ends at the node; micro_segment on a non-critical net is INFO only), but KiCad DRC, the gate's first step, fails it (track_dangling at (14.4, 44.6)), so the gate catches it. On SD_SCK (critical) micro_segment fails it.
4. right_angle: a duplicated segment at a reverted corner (LED_YEL F.Cu (14.4, 44.6), SD_SCK B.Cu (22.805, 25.6)) does not hide the bend: right_angle FAIL plus duplicate_segment (counted review).
5. right_angle: all 78 plain 45-degree chamfers on the board (H / D / V of one width, plain nodes) reverted at once to 90-degree corners: route_check reports exactly 78 right_angle FAIL instances (B.Cu 39, F.Cu 36, In2 3; every class).
6. D-R26-01 seeds: GND partner via (7.4, 16.5) removed -> critical_via_no_gnd FAIL J440.3 at 2.0 mm (nearest is the (7.4, 20.0) via); (7.4, 20.0) removed -> FAIL J440.4 at 4.037 mm; test_r26_aux_pins_have_gnd_partner_vias fails on the first copy.
7. D-R26-02 seed: R13's 3V3 via (9.2, 52.55) -> (9.2, 52.98): test_r26_pyro1_out_clear_of_3v3_and_3v3a fails (0.62 < 1.0 mm). D-R26-04 seed: R164's 3V3 via (19.55, 55.825) -> (19.05, 55.9): test_r26_gate_nets_clear_of_3v3_and_3v3a fails (0.676 < 1.0 mm). Both pass on the unseeded copy.
8. K-binding: a generator edit (DS15034 'Table 2 p. 11' -> 'pp. 10-11') without regeneration fails K-binding ('saved firmware_obligations differs from native binding-note regeneration'); baseline empty.
9. D-R27-03: test_r27_port_terminal_pin_names (with its own camera-name and four name seeds) passed inside the full seeded-copy gate run; not separately reseeded.

## Checks executed
- 17 generator-text seeds on r10_sch_check.py in a git-archive copy, each run against test_r23_binding_note_rules_and_pin_table (.supervisor/r32_gate/text_seeds.json): 15 caught, 2 non-revert edits pass
- K-binding seed without regeneration (.supervisor/r32_gate/kbinding_seed.txt)
- D-R28-01 seed: r10_parts --check (stale), regeneration, then full tools/check.sh on the seeded copy (rc 0; log .supervisor/r32_gate/check_seed_dr2801.log)
- route_check --profile r10 on: base copy (0 failing), 78-chamfer revert, zero-length and duplicate hiders on LED_YEL and SD_SCK, GND partner via drops
- kicad-cli 10.0.7 pcb drc on the zero-length LED_YEL seed (track_dangling)
- test_r10_check RealBoardSeeds r26 tests with R10_BOARD = base, r13via, r164via, dropvia copies
- board SHA-256 before and after

## Coverage limits
- D-R27-03 not separately reseeded (its test's own seeds ran in the full gate)
- right_angle seeds limited to plain chamfers between H and V segments; chamfers ending at pads or vias not reverted on the real board (covered by the synthetic test_r24_right_angle)
- no board refill after via moves; spacing tests read saved fills
- round 31 gate report not opened
