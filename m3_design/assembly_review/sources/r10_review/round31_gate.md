# R10 round 31 — gate lens (claude)

Target commit `3366287`, board `a0ec075e…` (SHA-256 identical before and after). Probe directory `.supervisor/r31_gate/`.

**Totals: 0 Critical / 0 Major / 0 Minor.** No realistic gate miss found.

## Findings

None.

## Fix verification

| Item | Measurement | Verdict |
|---|---|---|
| D-R28-01 (one port current) | r10_parts.py port_A = 1.461 + aux_A feeds ports_w and loaded_pack; committed budget pack_7V4 / 6V0_four_stall_loaded_V = 5.8808312 / 4.3884907 V, SHA 42676342...; S1-S3 seeds caught as stale until regenerated | confirmed |
| D-R28-02 (rule 3 meter check) | 6 seeds (full revert, both polarities, unpowered, "or open", 100 ohm, clamp Inference label) each fail the pin test in modes G and G+R and K-binding in modes G and N | confirmed |
| D-R28-03 (Inference labels) | 13 seeds (rule 3 fight qualifiers and label, port map, GAP-5 whole and partial, chatter label, C87 / 5.71 V inputs, rule 4 VSD label, rule 8 corner and hold-up) all caught | confirmed |
| D-R28-04 (procedures, DS15034) | 9 seeds (obligation 15 revert and label-only, rule 4 revert, 4.5 V, 0.2 V, source reference, rule 3 first power, Table 2 pp. 10-11 and p. 10) all caught | confirmed |
| D-R29-01 (47-58 us) | 3 seeds (full revert to 47-53 us, label dropped, range only) all caught | confirmed |
| D-R29-02 (pins every D-R28-02 ... -04 label) | every label D-R28-02 ... -04 lists is a pinned substring; turn-on label seed caught; partial-label seeds caught | confirmed |
| R30-TRI-01 / -02 (docs only; not in this lens) | old strings "1.73 V on RAW_ACT", "0.15 mA through the match", "11.2 kOhm or 2 kOhm", "LS120 <= 70" pass clause absent from current statements (remaining hits are history/disposition text); "2.19-2.21 V on RAW_ACT" and "5.6 kOhm with the e-match" present in R10_VALIDATION; no generated text carries them, so no gate pin is expected | confirmed (text present; no gate involvement) |

## Observations (not counted)

- D-R28-01 seeds (S1 ports_w back to 1.46 + aux_A; S2 loaded_pack back to 5.456 x (1.46 + aux_A); S3 port_A = 1.46 + aux_A): r10_parts --check fails 'stale: parts_budget.json' on each while the budget is not regenerated (check.sh step); after regeneration nothing fails (S2 moves only pack_7V4/6V0_four_stall_loaded_V to 5.881014 / 4.388745 V; S1 moves the c-case loads and fire budget in the 4th decimal, 4-stall BAT_IN 5.713190 -> 5.713377 V). Same class as R26-GATE obs 2 / R28-GATE obs 1 / R29-GATE obs 1 (no stated rule binds a budget figure to a check); not counted.
- D-R28-01 structure: d_gps_radio_on_camera_off_logic_shed still uses the literal .461 + aux_A and the LDO figures .46 + aux_A rather than deriving from port_A; both equal today's allocations (1.561 - 1.0 = 0.561 A), so nothing is wrong now.
- D-R28-02 ... -04, D-R29-01 / -02, D-R27-02, D-R26-03: 35 generator-text seeds (full reverts and partial reverts of every pinned phrase, the DS15034 citation as 'pp. 10-11' and 'p. 10', the 47-53 us range, the turn-on label, the 5.71 V point, the 7.50 ms limit, rule 8's corner, the Rev 11 sentence) each fail test_r23_binding_note_rules_and_pin_table on the seeded generator, still fail it after the saved note is regenerated from the seeded generator (where K-binding then passes), and K-binding fails when the same edit is hand-made in the saved r10_binding_note.json only.
- Regenerating r10_binding_note.json from the committed generator reproduces the committed note byte for byte (c5cd0fa3...).
- right_angle: un-chamfering the 45-degree corner at LED_YEL F.Cu (14.4, 43.0) (non-critical) and ARM1_SENSE B.Cu (29.75, 45.5) (critical) fails route_check r10 with right_angle on both; with a duplicate of one leg added it still fails right_angle on both (the duplicate does not hide the bend).
- right_angle: with a zero-length track added at the un-chamfered corner, route_check r10 skips the bend (three track ends at the node); on ARM1_SENSE micro_segment fails the gate, on LED_YEL it is only an INFO leftover, but KiCad DRC reports track_dangling on the zero-length track (and check.sh fails on any DRC violation), so no realistic defect passes (R25-GATE obs class 'DRC-caught zero-length seed').
- right_angle: hidden-corner scan of the committed board (nodes whose copper turns 90 degrees with two distinct headings but more than two track ends or a through segment): 0 instances.
- D-R26-01: removing the GND partner via at (7.4, 16.5) fails route_check r10: critical_via_no_gnd AUX_TX_WIRE pad J440.3 (7.4, 18.0), gnd_mm 2.0.
- D-R26-02 / -04 at spots the pinned tests do not name: D120 moved 0.15 mm toward R173.1 (D120.3 3V3 at 0.906 mm from PYRO1_OUT) fails test_r26_pyro1_out_clear_of_3v3_and_3v3a; C10 moved 0.25 mm toward the PYRO1_GATE via (14.4, 53.3) (C10.1 3V3A at 0.896 mm) fails test_r26_gate_nets_clear_of_3v3_and_3v3a. Both tests run in check.sh on the checked board (R10_BOARD). Inner-layer barrels the copper_gap measure skips (unflashed) are covered by S-8 (BARREL_NETS includes PYRO1_OUT / PYRO1_GATE / PYRO1_GATE_N).
- D-R27-03: J420 pin functions 3 / 4 swapped in a copy of schematic.net.xml: r10_sch_check exits 1 with "J420: pin names {... '3': 'RXI', '4': 'TXO'}, expected ... (REQUIREMENTS F10, D-R27-03)"; baseline exits 0.
- Committed board measurements: PYRO1_OUT to 3V3 / 3V3A minimum 1.040 mm (R164.2 B.Cu); PYRO1_GATE_N / PYRO1_GATE to 3V3 / 3V3A minimum 1.058 mm (3V3 via (19.55, 55.825) to R128.1, F.Cu); both agree with D-R26-02 / -04 and the AGENTS status line.
- parts_budget.json SHA-256 4267634220f4... and binding note c5cd0fa3... match D-R28-01 / D-R29-02 and the records.

## Checks actually executed

- shasum -a 256 of the board before and after review (a0ec075e... both)
- git archive 3366287 into .supervisor/r31_gate/tree (board SHA verified identical); all seeds on that copy, restored and compared after each
- r10_parts.py --check --budget-only (baseline and seeds S1-S3, with and without regeneration) + JSON diff of parts_budget.json
- seeds/text_seeds.py: 35 generator / saved-note seeds x 3 modes (pin test test_r23_binding_note_rules_and_pin_table, check_r10.k_binding) + regeneration reproducibility; results text_seeds.json, text_seeds_R26.json, text_seeds_chatter.json
- D-R27-02 revision-sentence revert seed against the pin test
- test_r10_check.py -k test_r26 -k test_r27 -k test_r24 on the copy (7 tests OK); test_route_check.py (72 tests OK)
- route_check.py --profile r10 on 7 right_angle seed boards (ra/) and the D-R26-01 seed (bs/s26_01_drop_partner)
- kicad-cli 10.0.7 pcb drc on the zero-length corner seed (track_dangling reported)
- seeds/hidden_corners.py on the committed board (0 hidden 90-degree corners)
- seeds/near_items.py: PYRO1_OUT and gate-net to 3V3 / 3V3A distances on the committed board and on the D120 / C10 seeds; test_r26_pyro1_out_clear / test_r26_gate_nets_clear with R10_BOARD set to each seed
- r10_sch_check.py on the copy: baseline (exit 0) and J420 TXO / RXI netlist swap (exit 1, D-R27-03 issue)

## Coverage limits

- No full tools/check.sh or r10_build.sh run (read-only brief); individual gate stages and tests were run on a copy
- right_angle seeds on two real-board corners plus the synthetic via / pad cases in test_route_check; not every chamfer was reverted
- D-R26-02 / -04 seeds moved footprints without dragging their tracks (DRC would also fail); the spacing tests were the target
- Other lenses' round 31 reports and probe dirs were not opened; the round 30 gate report was not opened
