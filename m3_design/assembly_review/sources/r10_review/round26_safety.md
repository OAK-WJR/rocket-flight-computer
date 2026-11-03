# Round 26 safety lens (Claude)

- Target: commit `3d8e845`, PCB `92c3ad59174afe1ffe206f6384c8cd9a8962e09647ccd6a8c418b95b5312056f`.
- The SHA-256 was the same before and after the review and matches `git show 3d8e845:` of the board. No tracked file
  changed except these two reports.
- Rule: only real errors count. Full detail is in `round26_safety.json`. Probe scripts and outputs are in
  `.supervisor/r26_safety/`.

**Totals: 0 Critical / 0 Major / 4 Minor.** All four are record or calculation errors; none is on the board.

- AGENTS §2 holds on the built board: every gate network (Q124; Q120 / Q121; Q122), the off-by-default states and the
  bus behind the back-to-back load switch were read from the board netlist.
- The new chatter rule (D-R25-01) is correct at the stated worst corner, and the post-trip hold-up (D-R25-02) and the
  OVLO corner (D-R25-03) reproduce. The four-stall voltages behind them are wrong (02, 03).
- The single-fault sweep found no new hazard pair since `5516eeec…`, but the records misstate what two recorded pairs
  can do (01).

## Findings

| ID | Kind | Sev. | What is wrong | Key number |
|---|---|---|---|---|
| R26-SAFETY-01 | doc | Minor | R10_VALIDATION §1 (line 2340) says "None of the pairs below fires the match by itself", and owner row 2 says "Firing still needs a second fault at Q124" for the §1 residuals (line 2219). The table's own PYRO1_OUT-to-3V3 (R173.1–D120.3) and PYRO1_OUT-to-3V3A (R164.2) rows give 0.3–0.8 A in the match with the bus enabled, against the 0.75 A all-fire, and they put bus voltage onto 3V3 (the I-5 mechanism). FMEA I-5's route list and owner row 1 omit them. | 0.5136 / 0.5662 mm on B.Cu (`92c3ad59…`); 0.3–0.8 A (records) or 0.93–1.33 A if 3V3 held, vs 0.75 A all-fire; AP63203 does not sink in PFM (DS41326) |
| R26-SAFETY-02 | calc | Minor | "The fire budget's four-stall BAT_IN of 5.73 V" (F6, F4, binding note, AGENTS, M3_R10, ORDERING 8.3, R10_VALIDATION, STATUS, handoff) is the pre-AUX value. The bound `parts_budget.json` gives 5.713 V since D-R19-14. | 5.7132 V (5.7318 V without AUX); at 5.713 V: single drop-out 8.07 ms (not 8.2), window limit 7.50 ms (not 7.63), margin 0.50 ms; the 7 ms line holds down to 5.646 V |
| R26-SAFETY-03 | calc | Minor | Rule 8's "5.37 V four-stall-plus-fire corner" (binding note, M3_R10, F6, owner row 25) is 5.73 − 0.15 × 2.41 A: it subtracts the fire current from a four-stall point that already carries it. | Budget model: 5.71 V healthy match, 5.56 V shorted match, 5.50 V with match and leads shorted (cold) |
| R26-SAFETY-04 | doc | Minor | R10_VALIDATION line 2350 calls U11.5 "OV2". | TI SLVSEA3F p4 and the schematic: pin 5 = OV1 (IN1 = USB), pin 4 = OV2 (GND on the board) |

Fixes (text and generated text only; no board change):

- **01:** restate the §1 sentence: the two PYRO1_OUT-to-3V3 / 3V3A pairs can fire an enabled match by themselves,
  QSPI_IO2–PE4 needs a sustained IO2-high pattern, and the rest cannot. Limit row 2's "second fault at Q124" to the
  load-switch, EN and divider pairs. Add the two pairs to owner row 1 and FMEA I-5 (lever: owner row 18; respin: ≥ 1 mm
  or a GND guard).
- **02:** quote the four-stall point as 5.71 V (8.1 ms single, 7.50 ms window limit, 0.50 ms margin). Run the bench test
  at ≤ 5.71 V. Edit `m3_design/r10_sch_check.py` and its test pin, regenerate the binding note, then update the docs.
- **03:** replace 5.37 V with the budget-consistent corner (BAT_IN 5.50–5.71 V, VLOGIC about 5.35–5.56 V) in rule 8
  (generator and binding note), M3_R10, F6 and row 25.
- **04:** "U11.5 (OV1)".

## Fix verification

| Change | Measurement | Verdict |
|---|---|---|
| D-R25-01 chatter rule | Own model: 7.629 / 5.871 / 9.594 ms, trip-fraction table, 1.0953 V and 1.0277 V counter-examples. Corner search: the D-R24-19 corner is worst. The latest-placement periodic train is the worst window-feasible train. | partly: rule right at the corner, but the 5.73 V point is stale (02) |
| D-R25-02 rule 8 hold-up | 0.1034–0.1643 / 0.2906–0.4303 ms, fraction 0.222–0.305 | confirmed (its 5.37 V corner is 03, from round 23) |
| D-R25-03 OVLO corner | 10.1764 V; R92 3.147 mA; U9 bound 3.743861 A, margin 0.202327 A | confirmed |
| D-R24-02 gate-drive barrels | Four ACT_GATE vias; S-8 1.050 mm at each | confirmed |
| D-R24-11 D402 | BAT_SW_RETURN = {D402.1, J400.2, R165.1}; D402.2 GND; only GND within 0.6 mm | confirmed |
| D-R24-17 / -18 chamfers | BAT_ENABLE via to BAT_FAULT_N 0.2000 mm; protected-net adjacency unchanged except two benign pairs | confirmed |
| D-R24-19 EN figures | 10.345 / 20.111 / 26.023 / 8.204 / 6.300 ms, 5.96 V, 1.4014 V, 30.3–130.3 ms, ramp 4.29–4.80 / 4.72–5.25 V | confirmed (5.73 V label: 02) |

## Checks executed

- Board SHA-256 before and after; `git show` of the board at `3d8e845`.
- pcbnew (read-only): netlist, pad and probe-point dumps; plated-barrel count; S-8 wall-to-inner-copper; adjacency of 19
  protected nets on all four layers within 0.6 mm on `92c3ad59…`, `1407e850…` and `5516eeec…`, diffed.
- Independent EN / chatter model: corner search, window limits, trip fractions, random window-feasible trains, TCR
  sensitivity, turn-on range.
- Budget re-runs: four-stall fire voltage with and without the AUX allowance; shorted-match corners; hold-up; OVLO; U9
  bound.
- Datasheets: TI SLVSFC9C, TI SLVSEA3F, Diodes DS41326 Rev 3-2, AOS AONR21357 and AON7524.
- The round 24 and 25 safety reports were opened only after these findings were written.

## Observations (not counted): 17

Selected:

- The "4000-train search kept EN ≥ 1.1173 V" is a sample, not a bound: the periodic 7.62 ms train reaches 1.1162 V.
- With the fitted ±100 ppm/K at a 70 °C bay the window limit is 7.31 ms (5.73 V) / 7.18 ms (5.713 V): still above 7 ms.
- The window rule treats J400 as binary; a steady contact above about 241 kΩ trips a worst-case U9 at 5.73 V.
- Step 3's "off within 1 s" is met by telemetry / buzzer and J121.2 (about 0.2–0.3 s). The TP81 < 0.3 V alternative may
  take 0.9–1.35 s while C84 back-feeds through U11 (Inference). The error is fail-safe.
- F4's "pack ≥ 5.96 V" option rests on the replaced single-drop-out reasoning; it is harmless because ORDERING 8.3 requires
  the window test anyway.
- Disclosed single-fault classes were re-found on the board: ACT_DRV / ACT_GATE to GND 0.2506 mm, Q121 G–D 0.520 mm,
  U9 IN–OUT 0.200 mm, In2 RAW_PROTECTED 0.2506 mm from the BAT_IN via (17.5,87.15), OUT–GND 0.1768 / 0.1800 mm,
  BUZZ_OUT–ACT_EN_MCU 0.520 mm, and BAT_FAULT_N–ACT_EN_MCU 0.550 mm (0.554 V against a 25 °C threshold).

## Coverage limits

- No bench or physical measurement. TPS2121 reverse conduction below IRCB is an Inference (observation only).
- The adjacency sweep was limited to 19 named nets and 0.6 mm.
- check.sh, DRC and route_check were not run (read-only brief). No gate seeds were attempted.
- Firmware rules were checked only where they touch J400, PA6 and pyro sequencing.
