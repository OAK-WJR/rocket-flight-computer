# Round 26 MCU review (Claude)

Target commit `3d8e845`. PCB SHA-256 `92c3ad59174afe1ffe206f6384c8cd9a8962e09647ccd6a8c418b95b5312056f` before and after.
**Result: 0 Critical / 0 Major / 0 Minor.** Evidence: [round26_mcu.json](round26_mcu.json); probe scripts in `.supervisor/r26_mcu/`.

## Scope covered

- U1: all 100 pads on the board, the schematic netlist and `r10_binding_note.json` u1_pins equal `pin_table.tsv` r10_net / mode_af (0 mismatches). Pin order matches DS12110 Rev 8 Figure 5; every AF number and cited AF-table page (pp. 89-95) checked against Tables 10-14; pin types (FT_h / FT_u / FT_a / TT_a / TT_u) as cited.
- Binding-note hashes (board, netlist, pin table, circuit) recomputed and equal.
- All 49 firmware obligations read against the copper (nets, part values, vias, divider ratios, gate networks, probe points) and against docs/M3_R10.md "Firmware" (rules 1-13, arming, timing, ports, pins, sensors). No contradiction found.
- Quoted figures re-derived: IWDG 960 cycles / 28.571-32.653 ms / 34.853 ms; pull-up dominance 0.104 V (PE4) and 0.218 V (PC1); chatter rule 17 (D-R25-01) single drop-out, sliding-window and periodic-fraction figures; rule 8 (D-R25-02) hold-up; turn-off corner 4.80 / 4.78 V; divider scales; IMU axis map from DS14623 Figure 5 vs U4 pads.
- Datasheet citations checked for page and content in DS12110 Rev 8, SLVSFC9C, SLVSEA3F, SLVS841G, SCES942A and DS14623.

## Findings

None.

## Fix verification

- **D-R24-03 BOOT0 second via**: BOOT0: U1.94 (15.45,46.0) F.Cu -> vias (14.2,46.0) and (13.8,45.6), joined on F.Cu and B.Cu, -> R5.1 (13.0,45.6) B.Cu; R5 10 k to GND. Verdict: confirmed.
- **D-R24-08 second vias for R91.1 and U1.28 (rule 5 text)**: LOGIC_SOURCE_ST: U1.28 (30.55,48.0) F.Cu -> vias (30.45,51.4) and (30.85,51.8), joined on both layers -> R91.2 / U11.9 on B.Cu; 3V3 via at (28.1,59.4) present. Binding rule 40 and M3_R10 rule 5 coordinates match.. Verdict: confirmed.
- **D-R24-02 second gate barrels (quoted by rule 4 / binding 39)**: ACT_GATE vias (16.2,73.3)+(15.4,72.85) join Q120.4 / C120.2 / R120.2 on B.Cu; (11.14,71.7)+(11.74,72.3) join Q121.4 / R119.1; both pairs meet R121.1 (14.5,72.3) on F.Cu; no B.Cu link between the two groups, so both Q120 barrels open leaves Q120 held off by R120 as stated. R120.2 and C120.2 are ACT_GATE (probe point correct).. Verdict: confirmed.
- **D-R24-19 rule 8 turn-off corner 4.80 V (4.78 V without D402)**: (1.116 + 0.0226 + 0.0057) / 0.23829 = 4.802 V; without D402 4.778 V; PA6 0.44 x 11 = 4.84 V. Verdict: confirmed.
- **D-R25-01 binding rule 17 (sliding 100 ms window, single drop-out figures, periodic fractions)**: Independent EN model (R80 = R165 = 474.7 k, R81 = 297 k, C87 0.72 x 220 nF, 0.1 uA EN + 50 nA D402, VUVLO(F) 1.116 V per SLVSFC9C p. 9): EN0 1.4014 V at 6.0 V; single drop-out 10.345 / 20.111 / 26.023 ms at 6.0 / 7.4 / 8.4 V, 8.204 ms at 5.73 V, 6.300 ms at 5.5 V; one block per 100 ms 7.629 / 5.871 / 9.594 ms at 5.73 / 5.5 / 6.0 V; periodic trip fraction 19.90 % (0.1 ms) to 5.82 % (8 ms) at 5.73 V and 24.31 % (0.1 ms) to 8.32 % (9.9 ms) at 6.0 V; fast-chatter limit 20.0 / 24.4 %. Nominal 19 / 33 / 41 ms reproduce. All quoted figures reproduce.. Verdict: confirmed.
- **D-R25-02 binding rule 8 hold-up after the PA6 trip**: t = C (V^2 - 3.8^2) / 2P at 300.8 uF: all ports on (11.249-13.064 W, parts_budget.json) 0.1034-0.1643 ms; shed (4.295-4.650 W) 0.2906-0.4303 ms; window 4.84-5.17 V = 0.44-0.47 x 11 (R60 100 k / R61 10 k on the board). Break-to-3.8 V from 7.4 V 0.4642-0.5391 / 1.3041-1.4118 ms matches M3_R10 and the budget.. Verdict: confirmed.
- **D-R24-21 BOOT0 citation (comments only)**: not re-read in code; no MCU-visible text affected. Verdict: not checked (out of lens; comment-only).

## Observations (not counted)

- Rule 8 / D-R25-02 "0.22-0.31 of the break-to-3.8 V hold-up": over the stated window (VLOGIC 4.84-5.17 V, break from 7.4 V) the energy fraction is 0.2229-0.3048; the 0.31 upper bound is outward rounding of 0.305 and encloses the true range, so it is not false.
- PA6 trip window with 1 % R60 / R61 (0402WGF, 1 %) spans VLOGIC 4.753-5.265 V; the lower corner is below the 4.84 V nominal edge quoted against U9 4.80 V BAT_IN turn-off, but rule 8 already says the window is "to be qualified with the divider and ADC tolerances" and D-R25-02 / round 25 triage list 4.7529 V; disclosed.
- DS12110 Rev 8 Table 120 p. 213 allows 0 mA injection of either sign on PA4 / PA5 (all other FT/TT pins -5/+0 mA). Both pins are pulled only to 3V3 (R91 / R89 10 k) and driven by open-drain U11 ST / U9 FLT, so no injection path exists; the pin table does not mention the special limit, and no requirement asks it to.
- pin_table row 25 (PA3 loader USART2_RX pull-up against R157 10 k) "<= 0.83 V" is computed at VDD 3.3 V (3.3 x 10/40); at a 3V3 rail tolerance edge it is about 0.84 V. No requirement depends on the figure (servo input threshold far above).
- PA4 is a TT_a pin (DS12110 Rev 8 Table 9 p. 69), not FT; it is only pulled to 3V3, so the FT statements for the port UART pins do not apply to it and nothing is claimed otherwise.
- Binding rule 48 / M3_R10 rule 13 cite the LSM6DSV80X ("all three parts"); its datasheet is not cached and I did not verify the +/-80 g clip or 3.904 mg/LSB on that part.

## Coverage limits

- RM0433, AN2606 and DS15034 (ISM6HG256X) were not re-read; loader pin roles and option-byte items are taken as labelled Inference.
- LSM6DSV80X datasheet not available locally (rule 13 figures for that part not verified).
- Turn-on window (30-130 ms) and the 44 ms PORT_4V8-to-3V3 lag were checked only for plausibility (C87 1.27 x gives 130.3 ms), not re-derived end to end; these belong to the power lens.
- No firmware exists; no physical or bench test was possible.
