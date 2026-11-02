# R10 round 28 — parts lens

Target commit `19dd0b5`, board `a0ec075e…` (SHA-256 before and after: `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c`).

**Totals: 0 Critical / 0 Major / 0 Minor.** No real errors found.

## Fix verification
- **D-R27-03 (M3:PortTerminal on J410/J420/J440):** schematic.net.xml: J410/J420/J440 lib M3:PortTerminal, pinfunctions 4V8_1/GND_2/TXO_3/RXI_4 on PORT_4V8/GND/*_TX_WIRE/*_RX_WIRE; fields LCSC C2757925, Manufacturer DORABO, MPN DB125-3.5-4P-GN-S, footprint rocket:M3_DB125_4P_GN, equal to the BOM line and the board; symbol ki_fp_filters M3_DB125_4P_GN; J9 keeps CameraTerminal. Verdict: confirmed.
- **D-R27-01 / D-R27-02 / D-R26 fix pass, parts-relevant part (BOM / CPL after the four moved CPL rows):** BOM 81 codes / 206 parts, CPL 70 top / 136 bottom; jlc_orient --verify-cpl: 67 + 125 rebuilt, worst pad residual 0.491 mm, errors none, 14 placement-only; cost_check 60.47 + 123.93/5 = 85.26 USD, fixed 83.96/5 = 16.79; stock U4 9/2, U9 30/-81/7, C2757925 35895/35052, C535146 196/189, as the docs quote. Verdict: confirmed.

## Observations (not counted)
- R164's maker part 0603WAF220KT5E decodes to 2.2 ohm (UNI-ROYAL value code: 220 x K = 10^-2; uniroyal.pdf section 2.4), so it agrees with the 2.2R value field; 22 ohm would be 220J.
- J3 and J430 CPL rows differ from their footprint origins (J3 x 4.505 vs 4.600; J430 y 25.85 vs 24.30): both equal the pad-bounding-box centre and are the recorded jlc_corrections offsets, so they are correct.
- ESD103-B1-02EL (D402) VRWM is +/-15 V (Infineon datasheet, table 'Reverse working voltage'); J400.2 sits at 8.4 x 770/1240 = 5.22 V with the switch closed, and at most 12.4 V even at the SMBJ12CA 19.9 V clamp, inside VRWM.
- Port and camera supplies: U400 feedback 0.8 x (1 + 58.2k/10k) = 5.456 V and U401 0.8 x (1 + 49.9k/10k) = 4.792 V match the quoted nominals; U402's R430 22.6 kohm gives about 1.12 A typical (TPS2553 I_OS = 23500 / R^0.977), consistent with the 1 A camera allowance.
- Bleeder and divider dissipations are all far below 0603 / 0402 ratings: R92 21 mW, R405 28 mW, R167 7 mW, R103 11 mW.
- Every capacitor's rated voltage exceeds its net's maximum (BAT_IN parts 25-50 V against the 8.4 V pack and the 19.9 V SMBJ12CA clamp; 3V3 / 3V3A / VCAP parts 16-50 V).
- Test pads TP74/TP80-TP83/TP88/TP120/TP122 and the J2 TC2030 pattern are board-only items with no BOM or CPL line, as recorded.

## Checks executed
- Every JLC and owner BOM designator (207) compared with the board footprint's LCSC, Manufacturer Part, footprint name and value: 0 mismatches (.supervisor/r28_parts/cmp.py)
- Every CPL row (206) compared with board position and side: 0 mismatches except the recorded J3 / J430 centroid corrections (pad-bbox centres, .supervisor/r28_parts/cmp2.py)
- tools/jlc_orient.py --verify-cpl on the committed CPL with tools/jlc_easyeda/pads.json (output to the probe dir): errors none, 192 rebuilt + 14 placement-only
- MPN value / tolerance / voltage / dielectric / size decode by hand for all 81 BOM lines against the Value field and footprint
- Port symbol fields, pin names and nets from schematic.net.xml and kilib/m3.kicad_sym
- Rating-versus-operating-point pass over capacitor voltages, resistor dissipation, ESD VRWM, TVS standoff, FET Vds/Vgs, regulator inputs and feedback dividers
- cost_check.json / stock_check.json figures against AGENTS, M3_R10, ORDERING, R10_VALIDATION, REQUIREMENTS, HANDOFF and STATUS

## Coverage limits
- No live supplier query this round; supplier facts taken from the committed snapshots
- Thermal and pulse ratings of R134 / R166 and Q124 not re-derived (records disclose them as unqualified)
- CPL bottom-side rotation convention remains the recorded Inference; not confirmed in JLC's preview
