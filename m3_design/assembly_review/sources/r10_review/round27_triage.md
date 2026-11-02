# R10 round 27 triage (Claude verifier)

- **Target:** commit `816038c`. Board SHA-256 `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c` before and after (unchanged).
- **Method:** read-only. Probes and copies are in `.supervisor/r27_triage/`. Machine-readable copy: `round27_triage.json`.

## Totals

**7 real errors: 0 Critical / 0 Major / 7 Minor.**
- All seven lens findings reproduce. One sibling that the triage found is merged into R27-TRI-02.
- None changes copper or placement, so the fix pass needs no board change.
- Round 27 is not a clean round.
- 0 findings were not reproducible.

## Real errors

| ID | From | Kind | Board change | What is wrong (triage evidence) | Fix |
|---|---|---|---|---|---|
| R27-TRI-01 | POWER-01 | doc | no | R10_VALIDATION:2181–2182 and round26_fix_docs:74–75 say the 7.31 / 7.18 ms TCR pair was "computed at 5.73 V; not re-run at 5.71 V". The triage model gives 7.309 ms at 5.73 V and 7.183 ms at 5.7132 V. At the 1 % corner it gives 7.629 / 7.503 ms, which reproduces D-R26-03. | "(7.31 ms at 5.73 V and 7.18 ms at 5.71 V, at 70 °C; still above 7 ms)". Add an erratum line in round26_fix_docs. |
| R27-TRI-02 | POWER-02 + sibling | calc | no | **GAP-3 paragraph** (parts_qualification:673–686) uses the pre-AUX 460 mA: 0.406 W, 102.5–114.7 °C and 135.4 °C/W. The budget gives 0.490 W, 109.2–123.9 °C (70 °C), 124.2–138.9 °C (85 °C) and a 112.3 °C/W ceiling. No limit is crossed.<br>**Sibling:** the stall-input paragraph (:660–668) and `r10_parts.py:433` `loaded_pack` use 1.46 A at 5.456 V, which leaves out the AUX 0.1 A. parts_budget:91–92 therefore give 5.899 / 4.414 V; with AUX it is 5.881 / 4.389 V. | Restate GAP-3 with 560 mA, 0.490 W, 109.2–123.9 / 124.2–138.9 °C and 112.3 °C/W. Add `aux_A` to `loaded_pack`, regenerate the budget and its bound SHA, and restate the stall-input figures. |
| R27-TRI-03 | POWER-03 | doc | no | M3_R10:712 gives the In2 3V3 fill as 1466.52 mm². It measures 1430.05 mm² on `a0ec075e…`. | "1430.05 mm² on `a0ec075e…` (1466.52 mm² when D-R18-06 joined it …)". |
| R27-TRI-04 | MCU-01 | doc | no | Binding note:527 says "every DS12110 citation in this note is Rev 8". Its own line 601 cites Rev 11 Table 109. The note is generated from r10_sch_check:242–243. | Append "…, except the two design limits labelled as read from Rev 11 Table 109 in round 14 (the 6.0 V FT cap and the 4.0 V ADC-mode maximum; R5-MCU-04 obligation, Inference)" before "; Rev 11 and RM0433 were not re-read…". Then regenerate the note. |
| R27-TRI-05 | SAFETY-01 | doc | no | FMEA:37, FMEA:111, R10_VALIDATION:2406 and round26_triage:128 call the 3V3 clamp "H-9". In FMEA §4.2 (line 385), H-9 is the GATE_SW gate-source capacitor, which is C120 on R10 (1 µF, ACT_FET_S / ACT_GATE). | Replace the label with "(not an FMEA change-list item; §4.2's H-9 is the load-switch gate-source capacitor, fitted on R10 as C120)", and mark line 111 as a mislabel. |
| R27-TRI-06 | MECHANICS-01 | doc | no | ORDERING:695 and HANDOFF:63–64 say "keep them south of y 23.5". The records use north = smaller y = aft (D-R26-01 / -02, R10_VALIDATION:2196), so "south" means forward, into the J3 zone that the same row forbids. | "keep them aft of y 23.5 (y < 23.5; J440's forward body end is at y 23.45)". |
| R27-TRI-07 | REQUIREMENTS-01 | doc | no | J410, J420 and J440 use M3:CameraTerminal (telemetry.kicad_sch:115–179). Its visible pin names are "5V OUT", "RX FROM CAMERA TX" and "TX TO CAMERA RX". On the board, pin 3 is the board's TX (PD8 / PB13 / PC6) and pin 1 is PORT_4V8. schematic.net.xml carries the same names. The PCB has no pinfunction strings, and the fab outputs carry no pin names. | Give the ports their own symbol: 4V8 / GND / TXO / RXI. Regenerate the schematic and netlist, run ERC / parity, and add a sch_check assertion. The board hash should stay the same. |

## Sibling sweeps (brief items)

**R27-TRI-02 (460 mA, 0.406 W, 102.5–114.7 °C, 135.4 °C/W).** Every other copy predates D-R19-14 and is labelled with its board or date:
- R10_VALIDATION:2994 (round10 section);
- audit_preflight:94–95 (dated 2026-10-28);
- R10_DECISIONS:865 and :1212;
- r10_final_deviations.json:1043–1054 (bound to `632a9ad3…`).

M3_R10:710 and R10_VALIDATION:2558 are already correct.

**R27-TRI-03 (board-geometry figures).** I checked every mm² figure in M3_R10, R10_VALIDATION, AVA_LAYOUT, ORDERING, STATUS and AGENTS, plus the current In2 figures.
- **Historical:** M3_R10:1267 (history table); R10_VALIDATION:802 (In1 3,778.91 mm², a round 9 section; In1 is now 3717.74 mm²); ORDERING:52 (R9); AVA_LAYOUT:127–150 (`0c50b9fd…`).
- **Reproduces:** M3_R10:431's island measures 2.892 mm².
- **In2 3V3 edge figures** (132.0 / 35.9 / 34.6 mm, minimum 0.300 mm): labelled to `0dc84776…`. With one method, the triage gets 138.84 → 138.24 / 35.80 / 34.84 mm on the two boards. The minimum is 0.300 mm on both, so the length figures depend on the method and have not changed in substance.
- **Labelled Round 18:** the USB_LIMITED track, given as 63.605 mm, is now 63.115 mm (less than 1 % in resistance).

**R27-TRI-05 (cross-references).** All 48 H / I / F / V / T references in the FMEA R10 rows, R10_VALIDATION's current sections and M3_R10's current sections match their definitions, apart from H-9. I-11 is a row label used consistently since R7.

**R27-TRI-06 (compass words).** In ORDERING 8.4 and the whole handoff, only this phrase is inverted.

**R27-TRI-07 (symbols).** I compared every symbol's pin names with its nets, and U1's 100 pins with pin_table. There is no other contradiction, and CameraTerminal is correct for J9.

## Root-flagged observations

| Observation | Verdict | Why |
|---|---|---|
| Manufacturing: inner copper 0.030 mm vs 1 oz | Observation | ORDERING:57 records 0.030 mm as JLC041611-7628's finished 1 oz inner copper, used by both the stackup and the job file. dc_solve reads it, which is conservative. |
| Mechanics: `test_r10_plate.py` fails | Observation | The failure reproduces (J430 / J440 masses missing). check.sh does not run it, and no current doc says to run it or cites it as passing. round19_fix_cad:362 records it as stale. |
| Safety: PYRO1_IGN–3V3 and RAW_ACT–3V3 | Observation | Reproduced: 0.7350 and 0.8370 mm. The I-5 lists say "include" and "has routes". §1 bounds only PYRO1_OUT and the gate nets. No document claims the list is complete or gives a minimum for the class. |

The other observations are reproductions or labelled history; they are listed in the JSON. Not reproducible: none.
