# R10 round 29 — MCU lens

Target commit `09a564e`, board `a0ec075e…` (SHA-256 before and after:
`a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c`). Read-only; probes in `.supervisor/r29_mcu/`.
Full detail in `round29_mcu.json`.

## Totals

| Critical | Major | Minor |
|---|---|---|
| 0 | 0 | 1 |

## Finding

### R29-MCU-01 (calc, Minor): rule 3's gate time constant "47–53 µs" leaves out C126's +10 % tolerance

- **What is wrong:** generated firmware rule 3 (binding note obligation 38, from `m3_design/r10_sch_check.py:366`),
  `docs/M3_R10.md:1095`, `docs/FMEA_REDUNDANCY.md:39` and `docs/R10_VALIDATION.md:2561` say "the gate time constant
  is 47–53 µs". The source, `round23_safety_severity_check.md:68`, computed only the cases "47–50 µs with C126 at
  −10 % plus Ciss, and 53.0 µs nominal".
- **Contradicts:** the fitted C126 is Samsung CL10B224KA8NNNC (C21120, JLC BOM line 15). Its tolerance code K means
  ±10 % (Samsung part-numbering guide, cached `samsung.pdf` p4). `parts_qualification.md:521` also gives ±10 %.
- **Evidence (Calculation):** on board `a0ec075e`, R126 is 220 Ω, R127 1 kΩ, R128 10 kΩ and C126 220 nF, and Ciss
  is 2.25 nF (AON7524 p2). The source's model uses drivers of ≤ 50 Ω, so R_th = (220 + 50∥50∥1k) ∥ 10k = 238.6 Ω.
  This reproduces the source's −10 % and nominal cases, 47.8 µs and 53.0 µs. At +10 %, 244.25 nF gives 58.3 µs.
  Over the source's driver range, C126's ±10 % spans 46.6–60.9 µs.
- **Impact:** text only. A larger time constant only slows the gate, so the rule's conclusions stay conservative:
  a fire after about 0.55 ms of sustained fight, and ≤ 6 mA RMS when logging at ≥ 25 MHz. Still, the stated range is
  false for a board with C126 in the upper half of its tolerance.
- **Fix:** in all four places, write "about 47–61 µs over C126's ±10 % (53 µs nominal; Calculation, driver
  resistances Inference)". Or keep 47–53 µs and qualify it as "C126 −10 % to nominal". Then regenerate the binding
  note and update any test that pins the string. No board change.

## Fix verification (round 28, this lens)

| Item | Result |
|---|---|
| D-R28-02: rule 3 meter check | **Confirmed.** It reads both polarities with the board unpowered, before first power. The pass rule is > 0.9 kΩ or open both ways; a beep or < 100 Ω rejects. 1 kΩ ∥ 10.22 kΩ = 0.911 kΩ. Same wording in the binding note, M3_R10, ORDERING 8.3 and FMEA. |
| D-R28-03: Inference labels | **Confirmed.** Rule 3, the port map, GAP-5, chatter, rule 4 and rule 8 carry the labels that D-R28-03 lists. The separate 47–53 µs range is R29-MCU-01. |
| D-R28-04: port-supply lead | **Confirmed.** TPS2121 Table 9-1 p13 scaled to C85 (470 nF) gives 166–196 V/s. AP63203: UVLO 3.30–3.70 V and tSS 4 ms (DS41326 p5). That gives 20.8–26.3 ms. |
| D-R28-04: rule 4 Q120 criterion | **Confirmed.** With both gate vias removed on a probe copy, ACT_GATE splits into {Q120.4, R120.2, C120.2} and {Q121.4, R119.1, R121.1}. R120.1 is ACT_FET_S at B(18.5,72.17). The settled \|VGS\| of 0.833 × V_S is ≥ 4.74 V at the lowest loaded pack. |
| D-R28-04: DS15034 citation | **Confirmed.** Figure 5 is on p9, section 3.1 / Figure 6 on p10, Table 2 on p11 and section 4 starts on p12. |
| R28-TRI-06: PB1 is TT_u | **Confirmed** in `parts_qualification.md:958` and R10_VALIDATION:1916, against Table 9 p70. |
| Binding note SHA `30796f5e…` | **Confirmed.** Regenerating it on a probe copy gives a byte-identical file, and `test_r23_binding_note_rules_and_pin_table` passes. |

## Observations (17, not counted)

- **U1 pin map:** all 100 U1 pads equal pin_table and the binding note's `u1_pins`. All port names and every cited
  Table 9 page match DS12110 Rev 8. The AF numbers are re-read from Tables 10–14.
- **Pin types:** every pin-type statement in current text matches Table 9. Two entries in labelled history are
  imprecise:
  - M3_ACTUATOR_MERGE:52 gives PC1 as "FT_a"; it is FT_ha. That line is in the historical R2 record.
  - ROCKET_FC_FROZEN_DESIGN gives PB8 / PB9 as "FT_f, suffix unverified".
- **Port and camera wiring:** each port's resistors and ESD clamps sit on the pins pin_table names. The TXU0202 pin
  use and the TPS2121 ST meaning are confirmed.
- **Rule 3 meter physics:** re-derived. Neither polarity nor any parallel path changes the verdict.
- **Rule 4 ratios:** "0.93–1.01×" covers the source table's variants. It is a bound, not a false ratio.
- **Citations and arithmetic:** the DS15034 / DS14623 and other DS12110 citations, and the pull-up, divider, IWDG
  and PA6-window arithmetic, are reproduced.
- **PA4 / PA5:** Table 120 gives them a 0 mA injection limit. No stated path injects into either pin.

## Coverage limits

- AN2606 and RM0433 were not available locally and were not re-read.
- Power and safety budgets were checked only where MCU obligations quote them.
- No physical measurement was made.
