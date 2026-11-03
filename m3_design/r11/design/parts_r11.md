# R11 parts: package changes and rating checks (stage A)

Scope: D-R11-04 (MCU), D-R11-05 (connectors), D-R11-06 (passives). Every changed part keeps R10's net and value
(D-R11-01); `circuit.json` is the machine-readable list and `r11_sch_check.py` enforces it. Supplier data: JLCPCB
component API (`r11_parts.py --stock`, the same query as `tools/jlc_stock.py lookup()`), run 2026-11-03T02:11:50Z,
recorded in `jlc_r11_stock.json` (stock, `canPresaleNumber`, library type, price). Every R11 code passed: orderable
quantity at least five boards' demand.

Evidence labels (AGENTS §2.5): **Datasheet** = the maker or LCSC listing, URL given; **Calculation** = arithmetic on
stated inputs; **Inference** = not measured and not read from the original datasheet.

## 1. Rating rule

A part moves to 0402 only when (a) its rated voltage is at least R10's part's rating or at least 2 × the highest
steady voltage on its nets, (b) its worst steady dissipation, and any credible single wiring fault, stays at or under
62.5 mW, the 0402 thick- and thin-film rating at 70 °C (LCSC listings below), with steady dissipation at or under
50 % of the rating derated to 85 °C (linear to zero at 155 °C, 62.5 × 70 / 85 = 51.5 mW → 25.7 mW; the derating
shape is the makers' usual curve, Inference), and (c) for a capacitor, its capacitance after DC bias does not matter
to a reviewed calculation or the bias is under 10 % of the rating. Otherwise the part keeps its R10 case.

Highest steady net voltages used (R10 `M3_R10.md` "Power"): BAT_IN 8.4 V (2S full; 19.9 V is D8's clamp, a transient);
RAW_PROTECTED 9.77 V (U9's OVLO, nominal); USB_LIMITED / VBUS 5.5 V; PORT_5V3 / CAM_5V 5.456 V; PORT_4V8 4.792 V;
3V3 / 3V3A / CAM_IO_3V3 3.3 V.

## 2. Resistors moved to 0402

| Refs | R10 part | R11 part (JLC) | Worst stress | Check | Source |
|---|---|---|---|---|---|
| R88, R89, R90, R91, R102, R460–R464 (10k 1 %) | 0603WAF1002T5E C25804 | 0402WGF1002TCE C25744, Basic | ≤ 3.3 V: 1.1 mW | pass | [LCSC C25744](https://www.lcsc.com/datasheet/lcsc_datasheet_2411221126_UNI-ROYAL-Uniroyal-Elec-0402WGF1002TCE_C25744.pdf) 50 V, 62.5 mW |
| R167 (10k 1 %, BAT_IN–GND) | C25804 | C25744 | 8.4 V: 7.1 mW; 19.9 V clamp transient: 39.6 mW | pass (Calculation) | as above |
| R100, R101 (1k 1 %, camera UART) | 0603WAF1001T5E C21190 | 0402WGF1001TCE C11702, Basic | fault: camera wire on CAM_5V with the buffer side at 0 V, 5.456 V: 29.8 mW | pass under 62.5 mW (fault only) | [LCSC C11702](https://www.lcsc.com/datasheet/lcsc_datasheet_2206010216_UNI-ROYAL-Uniroyal-Elec-0402WGF1001TCE_C11702.pdf) |
| R440, R441, R450, R451, R470, R471 (1k 1 %, port UARTs) | C21190 | C11702 | fault: TX / RX wire on PORT_4V8 with the MCU pin at 0 V: 23.0 mW | pass (fault only) | as above |
| R103 (1k, CAM_IO_3V3–GND) | C21190 | C11702 | 3.3 V: 10.9 mW | pass | as above |
| R110 (1k, VBUS_SENSE–GND) | C21190 | C11702 | VBUS / 2 ≤ 2.75 V: 7.6 mW | pass | as above |
| R162 (1k, BUZZ_DRV) | 0805W8F1001T5E C17513 | C11702 | ≤ 3.3 V: 10.9 mW | pass | as above |
| R404 (2k 1 %) | 0603WAF2001T5E C22975 | 0402WGF2001TCE C4109, Basic | divider leg, < 1 mW | pass | [LCSC C4109](https://www.lcsc.com/datasheet/lcsc_datasheet_2206010230_UNI-ROYAL-Uniroyal-Elec-0402WGF2001TCE_C4109.pdf) |
| R431 (100k 1 %) | RC0603FR-07100KL C14675 | 0402WGF1003TCE C25741, Basic | 3.3 V: 0.1 mW | pass | [LCSC C25741](https://www.lcsc.com/datasheet/lcsc_datasheet_2206010100_UNI-ROYAL-Uniroyal-Elec-0402WGF1003TCE_C25741.pdf) |
| R80, R165 (470k 1 %) | 0603WAF4703T5E C23178 | 0402WGF4703TCE C25790 | 19.9 V across one: 0.8 mW; 50 V rated | pass | [LCSC C25790](https://www.lcsc.com/datasheet/lcsc_datasheet_2206010100_UNI-ROYAL-Uniroyal-Elec-0402WGF4703TCE_C25790.pdf) |
| R81 (300k 1 %) | 0603WAF3003T5E C23024 | 0402WGF3003TCE C25774 | EN ≤ 6.5 V: 0.1 mW | pass | [LCSC C25774](https://www.lcsc.com/datasheet/lcsc_datasheet_2206010100_UNI-ROYAL-Uniroyal-Elec-0402WGF3003TCE_C25774.pdf) |
| R87 (47k 1 %) | 0603WAF4702T5E C25819 | 0402WGF4702TCE C25792, Basic | ≤ 5.5 V: 0.6 mW | pass | [LCSC C25792](https://www.lcsc.com/datasheet/lcsc_datasheet_2206010100_UNI-ROYAL-Uniroyal-Elec-0402WGF4702TCE_C25792.pdf) |
| R85 (66.5k 1 %, U10 ILIM) | RC0603FR-0766K5L C137691 | 0402WGF6652TCE C29381 | ≤ 5.5 V bound: 0.5 mW | pass | [LCSC C29381](https://www.lcsc.com/datasheet/lcsc_datasheet_2206010030_UNI-ROYAL-Uniroyal-Elec-0402WGF6652TCE_C29381.pdf) |
| R430 (22.6k 1 %, U402 ILIM) | FRC0603F2262TS C2999509 | 0402WGF2262TCE C26960 | ≤ 5.5 V bound: 1.3 mW | pass; only 46 orderable (5 needed) | [LCSC C26960](https://www.lcsc.com/datasheet/lcsc_datasheet_2206010030_UNI-ROYAL-Uniroyal-Elec-0402WGF2262TCE_C26960.pdf) |
| R84 (750R 0.1 % 25 ppm, U9 ILIM) | RT0603BRD07750RL C861551 | RT0402BRD07750RL C852911 | ILIM is a current-reference output, about 1.2 V or less in operation (Inference: SLVSFC9C not re-read in stage A): ≤ 1.9 mW; even 5.5 V would be 40 mW | pass | [LCSC C852911](https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2210181700_YAGEO-RT0402BRD07750RL_C852911.pdf) |
| R86 (80.6k 0.1 %, U11 ILM) | RT0603BRD0780K6L C861568 | RT0402BRD0780K6L C852923 | ≤ 5.5 V bound: 0.4 mW | pass | [LCSC C852923](https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2311211102_YAGEO-RT0402BRD0780K6L_C852923.pdf) |
| R400 (56.2k 0.1 %, PORT_5V3 feedback) | RT0603BRD0756K2L C705784 | RT0402BRD0756K2L C705636 | ≤ 5.46 V: 0.5 mW | pass | [LCSC C705636](https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2210242030_YAGEO-RT0402BRD0756K2L_C705636.pdf) |
| R401, R403 (10k 0.1 %, feedback) | RT0603BRD0710KL C95204 | RT0402BRD0710KL C190095 | ≤ 1.2 V: 0.1 mW | pass | [LCSC C190095](https://www.lcsc.com/datasheet/lcsc_datasheet_2304140030_YAGEO-RT0402BRD0710KL_C190095.pdf) |
| R126 (220R, Q124 gate series) | 0805W8F2200T5E C17557 | 0402WGF2200TCE C25091, Basic | gate-charge edge: 3.3 V / 220 Ω = 15 mA, 49.5 mW peak, τ = 220 Ω × 220 nF = 48 µs, 1.2 µJ per edge; 0 mW steady | pass (Calculation; µs pulse capability of an 0402 thick-film part is far above this, Inference) | [LCSC C25091](https://www.lcsc.com/datasheet/lcsc_datasheet_2205311900_UNI-ROYAL-Uniroyal-Elec-0402WGF2200TCE_C25091.pdf) |
| R32, R33 (220R, LEDs) | C17557 | C25091 | (3.3 − Vf ≥ 1.8) V: ≤ 10.2 mW | pass | as above |

The 0.1 % parts keep R10's series (Yageo RT, ±25 ppm/°C), so the feedback and current-limit tolerances behind the
R10 figures are unchanged (Datasheet: the listings). The 1 % 0402 parts are
±100 ppm/°C (listings).

## 3. Capacitors moved to 0402

| Refs | R10 part | R11 part (JLC) | Nets (highest V) | Check | Source |
|---|---|---|---|---|---|
| C83, C90, C93, C402, C410, C420, C430, C444, C460 (100 nF 50 V X7R) | CC0603KRX7R9BB104 C14663 | CL05B104KB54PNC C307331, Basic (R10's own 0402 decoupler line, 16 places on R10) | VBUS 5.5 V, PORT_5V3 5.46 V, PORT_4V8, 3V3, CAM_IO_3V3; C402 PORT_BST–PORT_SW ≈ 5.5 V | same 50 V X7R rating; bias ≤ 11 % of rating; decoupling and the AP63201 bootstrap only, no reviewed calculation uses their value. The 0402's bias loss is larger than the 0603's (Inference: Samsung's curve for CL05B104KB54PNC not read; the maker page lists no DC-bias figures) | [LCSC C307331](https://www.lcsc.com/datasheet/lcsc_datasheet_2304140030_Samsung-Electro-Mechanics-CL05B104KB54PNC_C307331.pdf), [Samsung](https://product.samsungsem.com/mlcc/CL05B104KB54PN.do) |
| C60, C94, C127, C129 (10 nF 50 V X7R, ADC filters) | 0603B103K500NT C57112 | CL05B103KB5NNNC C15195, Basic (R10's own 0402 line) | sense nodes ≤ 3.3 V (VLOGIC_SENSE, CAM_5V_SENSE ≤ 0.9 V; PYRO1_CONT, ARM1_SENSE = node / 11.2) | same 50 V X7R; bias ≤ 7 % of rating, so the filter time constants are unchanged within the X7R tolerance (Inference: maker bias curve not read) | [LCSC C15195](https://www.lcsc.com/product-detail/C15195.html) |

## 4. Passives kept in their R10 case (D-R11-06)

| Refs | R10 case | Reason |
|---|---|---|
| R134 (2 Ω 2 W pulse, 2512) | 2512 | fire-path pulse part (D-R11-06) |
| R166 (0.36 Ω, 2512) | 2512 | U9 input damper; R10's sizing (D-R11-06) |
| R82 (2M 0.1 %), R83 (280k 0.1 %) | 0603 | U9 OVLO divider: no 0402 0.1 % part orderable at JLC on 2026-11-02 (RT0402BRD072ML C5189456: 0 stock; RT0402BRD07280KL not listed) |
| R402 (49.9k 0.1 %) | 0603 | RT0402BRD0749K9L C852808: stock 1807 but canPresaleNumber −10649, so not orderable |
| R92 (3.3k, RAW_PROTECTED–GND) | 0603 | 21.4 mW at 8.4 V and 28.9 mW at the 9.77 V OVLO: above 25.7 mW, 50 % of the 85 °C rating (Calculation) |
| R405 (820R, PORT_4V8–GND) | 0603 | 28.0 mW at 4.792 V, 36.3 mW if PORT_4V8 rises to 5.456 V: above 25.7 mW (Calculation) |
| R150–R153 (1k servo series) | 0603 | a servo lead chafed onto the pack + puts up to 8.4 V across one: 70.6 mW, above the 0402's 62.5 mW (Calculation); the 0603 (100 mW) keeps it |
| R164 (2.2 Ω, 3V3 → 3V3A) | 0603 | carries the 3V3A charge current into C10 / C11 (44 µF): the pulse is not checked against an 0402 pulse curve |
| C81 (4.7 nF 50 V C0G, U9 dV/dt) | 0603 | no 0402 4.7 nF 50 V C0G part at JLC (searched 2026-11-02); sets U9's slew, a reviewed timing |
| C87, C126 (220 nF 25 V X7R) | 0603 | timing capacitors in reviewed calculations (EN chatter, gate time constant): an 0402 change would move their capacitance after bias |
| C85 (470 nF 25 V), C86, C97, C98, C120 (1 µF 25 V X7R) | 0603 | U11 soft-start (reviewed VLOGIC slew) and RAW_PROTECTED / USB_LIMITED / ACT gate: no equal-rating (25 V X7R) 0402 part with a verified bias curve |
| C19, C20 (2.2 µF VCAP), C22 (1 µF 50 V), C23, C28, C92 (4.7 µF 16 V) | 0603 | X5R ≥ 1 µF: capacitance after bias would fall; VCAP is already an open qualification item |
| C128 (100 nF, PYRO1_OUT) | 0603 | Murata GCJ automotive soft-termination part on the pyro output, kept as reviewed |
| C6–C11 (22 µF 25 V 0805), C80, C89, C91, C95, C96 (1206), the 1210 bulk capacitors, C84 (470 µF polymer) | R10 | bulk parts (D-R11-06); C84 unchanged |

LEDs (LED1, LED2, 0805) and every IC keep their R10 parts; J3 (USB-C), J430 (microSD, owner decision F5) and J2
(TC2030) are unchanged.

## 5. MCU (D-R11-04)

U1 STM32H743VIH6, TFBGA-100, JLC C964146 (STMicroelectronics STM32H743VIH6, [LCSC](https://www.lcsc.com/datasheet/lcsc_datasheet_2203091604_STMicroelectronics-STM32H743VIH6_C964146.pdf)):
4355 in stock, 4043 orderable, $8.8446 (2026-11-03 query). Land `M3_TFBGA100_8x8_P0.8` from ST DS12110 Rev 8
Table 218 p. 324 (D = E 8.000 mm, 7.850–8.150; A ≤ 1.100; ball 0.35–0.45; e 0.8) and Table 219 p. 325 (Dpad 0.400 mm,
solder-mask opening 0.470 mm typical, stencil 0.400 mm, pad trace width 0.120 mm): 0.40 mm copper, 0.035 mm mask margin,
0.40 mm paste; courtyard 9.15 mm square (body maximum + 0.5 mm). Ball map: `pin_table.tsv` and `stageA.md` §2.

## 6. Connectors (D-R11-05)

| Ref | R10 | R11 (JLC, all JST genuine) | Pins |
|---|---|---|---|
| J410, J420, J440 | DB125-3.5-4P-GN-S | SM04B-GHS-TB(LF)(SN) C189895 | 1 PORT_4V8, 2 GND, 3 TXO, 4 RXI (as R10) |
| J9 | DB125-3.5-4P-GN-S | SM06B-GHS-TB(LF)(SN) C133065 | 1–2 CAM_5V, 3–4 GND, 5 CAM_RX_WIRE (board RX), 6 CAM_TX_WIRE (board TX) |
| J122 | DB125-3.5-5P-GN-S | SM05B-GHS-TB(LF)(SN) C189896 | 1–4 SERVO1–4_OUT, 5 GND (as R10) |
| J400 | DB125-3.5-2P-GN-S | SM02B-GHS-TB(LF)(SN) C189893 | 1 BAT_SW_SOURCE, 2 BAT_SW_RETURN (as R10) |
| J1 | DB125-3.5-2P-GN-S | two plated wire pads, `M3_WIREPAD_2P_AWG20`, no part | 1 BAT_IN, 2 GND (as R10) |
| J121 | DB125-3.5-2P-BK-S | two plated wire pads, `M3_WIREPAD_2P_AWG20`, no part | 1 PYRO1_OUT (OUT), 2 PYRO1_IGN (IGN) (as R10) |

GH rating (Datasheet, [JST eGH.pdf](https://www.jst-mfg.com/product/pdf/eng/eGH.pdf) p. 1, read 2026-11-02): 1.0 A AC/DC
per contact with AWG 26, 50 V, −40 to +105 °C, AWG 30–26 crimps (insulation 0.76–1.0 mm). The JLC listings give
−25 to +85 °C for the same parts (a narrower figure; Inference that it is the distributor's generic range). Land
pattern from eGH p. 2, "PC board layout", side entry: contact lands 0.6 ± 0.05 wide at 1.25 ± 0.05 pitch, 1.7 long;
solder-tab lands 1.0 × 2.7; 1.0 gap between them; 5.4 overall; tab inner edge 1.35 from the No. 1 contact centre.
`r11_parts.py --check` asserts each of these on the parsed footprints. The header body outline (y −1.6 to +2.45) and
the 4.35 mm envelope height are from eGH p. 2 / p. 3 and KiCad's generator for the same drawing (Inference for the
body depth). The solder tabs are unnumbered and carry no net, as R10's GH lands did.

Wire pads (`M3_WIREPAD_2P_AWG20`): finished hole 1.30 mm, land 2.50 mm, pitch 3.80 mm (1.30 mm copper gap), plated
through on all layers, no paste, footprint attributes exclude from BOM and position files. AWG 20 stranded conductor
bundle 0.97 mm (7 × 0.32 mm) to 1.02 mm (19 × 0.203 mm) (Inference: typical maker values, no wire chosen yet), so the
hole leaves 0.28–0.33 mm diametral clearance, inside the 0.2–0.7 mm lead-to-hole range commonly quoted from IPC-2222
Level B (Inference: IPC-2222 not re-read). IPC-2222's minimum land a + 2b + c with a = 1.30 + 0.13 (JLC hole tolerance,
Inference) = 1.43, b = 0.05 and c = 0.6 gives 2.13 mm ≤ 2.50 mm (Calculation on those inputs); the nominal ring is
0.60 mm against JLC's 0.15 mm minimum and 0.20 mm recommendation (Datasheet, JLC capabilities page, read 2026-11-02).
Current: J1 carries the board's battery current including the fire pulse (about 4.2 A into a short, 8.4 V / 2 Ω,
R10); AWG 20 copper and a 2.5 mm land are not limiting at that pulse (Inference; the IPC-2152 check of the copper
behind the pads is stage C's).
