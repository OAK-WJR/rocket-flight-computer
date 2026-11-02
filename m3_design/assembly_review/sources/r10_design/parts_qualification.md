# R10 component and harness qualification

This is the component contract, not board acceptance. `circuit.json` and the reviewed
`pin_table.tsv` define the current schematic; `parts.json` is a retired selection worksheet. `r10_parts.py` reproduces nine local
lands, nine small VRML envelopes, and `parts_budget.json`. It never edits the board.
Sources were read on 2026-10-26 locally; the R3 fix pass (2026-10-27) re-read
DS41326, SLVS841F, SLVSEA3F, SBVS282A, SCES942A and the LR900 manual. No physical
tests were performed. The current always-on ports, screw terminals, microSD and sole-bus-sense amendment below supersedes the earlier port-switch/translator, header, duplicated sense and ride-through records. AUD/GAP amendments still apply where not explicitly superseded; dated review records remain historical.


## Current circuit amendment and review status

Review status, checks, cost and open items are stated once, in [M3_R10.md, "Current state"](../../../../docs/M3_R10.md#current-state). In short: PCB `a0ec075e…` (46 × 90 mm) is not accepted and nothing is ordered. Rounds 22 and 23 (ten Claude lenses each) were the closing pair on `5516eeec…` (0 Critical / 0 Major; 22 and 55 Minor). The round 24 board pass (D-R24-01 … D-R24-17) made `1407e850…`; round 24's ten lenses and triage found 17 Minor real errors on it (R24-TRI-01 … -17), and the round 24 fix pass (D-R24-18 … D-R24-23) changed the board to `92c3ad59…` (one capped chamfer; no part or code changed). Round 25 then found 10 Minor real errors on `92c3ad59…` (R25-TRI-01 … -10, none on the board), and its fix pass (D-R25-01 … -03) left the board unchanged. Round 26 found 12 Minor real errors on `92c3ad59…` (R26-TRI-01 … -12), and its fix pass (D-R26-01 … -04) changed the board to `a0ec075e…` (two GND vias at J440, and C10, C11, R164, R173 and R164's 3V3 via moved; no part number or code changed), so rounds 27 and 28 review it under the owner's strict rule (only verified real errors count). AGENTS section 2 is unchanged. This file is the component contract; where a section below is marked historical it describes
hardware that was removed from R10 and is kept only for the record. The round 19 amendments below supersede earlier text in this file where they differ.

## Round 24 component amendment (2026-11-01; D-R24-11)

| Ref | Part | Change and evidence |
|---|---|---|
| D402 | Infineon **ESD103-B1-02EL E6327**, LCSC C535146 (the port clamps' existing line) | New: J400.2's contact clamp (R22-REQUIREMENTS-03, R23-SAFETY-06), from J400.2 to GND at B(4.45,65.9), rot 90, under J400 between its pins. Its 4.114 mm B.Cu tap leaves J400.2's own pad, so a discharge at the screw reaches D402 before R165; D402.2 returns 0.7 mm to its own GND via (5.15,65.575). BAT_SW_RETURN is now exactly {J400.2, R165.1, D402.1} (S-5, K-actuators). Leakage I_R ≤ 50 nA ([Infineon product page](https://www.infineon.com/de/part/ESD103-B1-02EL), parametrics; ESD103 datasheet Rev 1.3, at 15 V per D-R24-11): with J400 closed (J400.2 about 5.2 V at 8.4 V) it moves EN by at most 50 nA × R80 × R81 / (R80 + R165 + R81) = 5.7 mV (Calculation), a quarter of the 0.1 µA EN leakage the D-R20-11 timing already carries. The two leakages add, so the EN timing does not stand unchanged (R24-TRI-02): D-R24-19 gives single-drop-out immunity 10.3 / 20.1 / 26.0 ms at 6.0 / 7.4 / 8.4 V, about 8.1 ms at the four-stall 5.71 V (8.07 ms; D-R26-03, where 8.2 ms at 5.73 V predated the 100 mA AUX allowance), 6.3 ms at 5.5 V (repeated drop-outs add up), turn-on 30–130 ms and a turn-off corner of 4.80 V (Calculation). The J400 chatter bench rule is total open time under 7 ms in every sliding 100 ms window with U9 on at 5.71 V (D-R25-01, D-R26-03; worst-corner limit 7.50 ms); the earlier "pack ≥ 5.96 V for a 10 ms drop-out" rule is replaced. Inference: Infineon gives no 85 °C leakage and no trigger tolerance (21 V typical), so a screw discharge raises C87 by about 14 mV (21 V on 150 pF). Failure modes: shorted, it holds the board off (seen by the closed-switch check); open, the board is back to the unclamped state, with the ORDERING 8.3 handling rule as the second layer. Datasheet survey of the alternatives (SRV05-4, USBLC6-2SC6, SMBJ12CA, BAT54A, BZX84-B5V1): none meets both the leakage and the clamp limit (D-R24-11). Cost: the C535146 line goes 8 → 9 per board at $0.2306, no new code or feeder fee. |

Board totals with D402: JLC BOM 81 lines (45 Extended / 36 Basic) plus C84 on the owner BOM; 206 placed parts. Live JLC 2026-11-02T12:44:13Z (cost) and 12:43:17Z (stock), final files of `a0ec075e…` (BOM and owner BOM byte-identical to `1407e850…`'s; four CPL rows moved): **$85.26 per board** against the $84.41 cap, $0.85 over ($85.60 at 01:43:55Z on the same BOM and $85.36 before D402, the differences being D402 and JLC price movement; owner decision pending; see M3_R10 "Cost and stock"). U4 shows 9 in stock and only 2 orderable against 5; U9 (TPS259470LRPWR C3662793) 30 in stock, −81 orderable, minimum purchase 7; C535146 196 in stock, 189 orderable against 45. The stock check fails on U4 and U9; it reads JLC's `canPresaleNumber` as the orderable quantity, an Inference about JLC's field. For both, confirm in the JLC cart on order day, else consign franchised parts (R20-BOM-01).

Other round 24 placement changes, same parts and codes: C88 B(18.67,83.56) rot 0 on U9.5's axis (D-R24-17; was B(19.4,83.95) rot 90), R402 / R403 B(30.9,12.85) / B(30.9,14.6) beside U401 on B.Cu (D-R24-09; were on F.Cu), R92 F(31,86.7) and TP88 F(35.5,86.4) off the forward edge (D-R24-15).

## Round 19 component amendments (2026-10-30/31; D-R19-04, -07, -10, -11, -14)

No new BOM code except U4's. JLC BOM 81 lines (45 Extended / 36 Basic) plus C84 on the owner BOM; 205 placed parts at the time (206 since D402, above). Live JLC 2026-10-31T23:24Z (final files of `5516eeec…`, superseded by the round 24 figures above): $85.37 per board against the $84.41 cap; U4 shows 9 in stock and only 2 orderable, so the stock check (`stock_check.json` 2026-10-31T23:23Z) failed on U4, 2 orderable against 5, and also on U9 (TPS259470LRPWR C3662793: 40 in stock, −69 orderable, minimum purchase 7); it reads JLC's `canPresaleNumber` as the orderable quantity, an Inference about JLC's field. For both, confirm in the JLC cart on order day, else consign franchised parts (R20-BOM-01).

| Ref | Part | Change and evidence |
|---|---|---|
| U4 (fitted) | ST **ISM6HG256XTR**, LCSC C51931514, Extended | Replaces LSM6DSV320XTR (0 JLC stock; R19-BOM-01) on the unchanged `LGA-14_L3.0-W2.5-P0.50-TL` land and pose B(17,45.9), 180°. [DS15034 Rev 1](https://www.st.com/resource/en/datasheet/ism6hg256x.pdf): LGA-14L 2.5 × 3.0 × 0.83 mm, drawing p187 the same as DS14623's (14 × 0.475 × 0.25 mm pads, 0.5 mm pitch); Figure 5 p9 and Table 2 pp10–11 give the same pin map and axis directions as DS14623 Rev 1 p9, so roll stays −gyro_Y and the lever arm is unchanged; gyro ±4000 dps, low-g ±16 g and high-g ±32…256 g meet F1 / F2; −40…+105 °C (p1). Pins 10–11 (OCS_Aux, SDO_Aux) stay unconnected ("VDDIO or unconnected", Table 2). WHO_AM_I reads 0x73 on both parts (p66). **The high-g full-scale codes differ** (Table 150 p93: on the ISM part 100 = ±256 g and 011 is reserved; on the LSM part 011 = ±256 g, 100 = ±320 g), so firmware uses only codes 001 / 010, which mean the same on both. Live JLC 2026-10-31: 9 in stock but 2 orderable for 5 (`stock_check.json` 2026-10-31T23:23Z): consign franchised ISM6HG256XTR if the JLC cart is short (R21-BOM-02); franchised stock was also 0 on 2026-11-01 (DigiKey due 22-Mar-2027), so see the owner's procurement choices in ORDERING 8.1, $14.34 at 1–9. CPL rotation 180° from the EasyEDA `LGA-14_L3.0-W2.5-P0.50-BR` footprint (14 pads matched, residual 0.040 mm); confirm pin 1 in JLC's bottom-side preview. That the two parts' register maps otherwise match is not checked (Inference). |
| U4 (alternate) | ST LSM6DSV320XTR, LCSC C26633007 | Second fallback only, after consigned franchised ISM6HG256XTR; also 0 at JLC (−18 orderable) and LCSC (2026-10-31T13:40Z): same land, pins, axes and board pose; its `pads.json` record is kept. Its CPL rotation comes from its own EasyEDA TL footprint (0°, as before round 19), so regenerate and re-verify the CPL (`jlc_orient --verify-cpl`) if it is fitted. [DS14623 Rev 1](https://www.st.com/resource/en/datasheet/lsm6dsv320x.pdf) pp9, 187. |
| C87 | Samsung **CL10B224KA8NNNC**, 220 nF 25 V X7R 10 % 0603, LCSC C21120 (Basic, C126's line) | Was 2.2 µF C23630 (R19-REQ-02, D-R19-10); same 0603 land (at F(17,65) until round 21; since D-R21-05 at F(18.7232,81.8768), beside R81 F(18.8482,80.0) at U9's end of the EN run, so C87 stays at the divider's 2.03 V nominal (≤ 2.06 V with 1 % parts, at 8.4 V; Calculation) while R81 is intact, against EN/UVLO's 6.5 V absolute maximum, [TI SLVSFC9C](https://www.ti.com/lit/ds/symlink/tps25947.pdf) §6.1 p7). EN stays ≤ 2.06 V (8 % of C87's 25 V rating). With R80 + R165 = 940 kΩ, R81 = 300 kΩ and the [TPS25947 SLVSFC9C p9](https://www.ti.com/lit/ds/symlink/tps25947.pdf) EN thresholds (Calculation): turn-on 88 / 56 / 45 ms at 6.0 / 7.4 / 8.4 V (30–130 ms over C 0.72–1.27 ×, 1 % resistors and thresholds, U9's ±0.1 µA EN leakage and D402's ≤ 50 nA; D-R24-19); a single J400 drop-out shorter than 19 / 33 / 41 ms (worst 10.3 / 20.1 / 26.0 ms; 10.6 / 20.5 / 26.4 ms without D402) cannot trip U9; repeated drop-outs add up, and the bench rule is total open time under 7 ms in every sliding 100 ms window (D-R25-01). The X7R DC-bias loss at ≤ 2.06 V is taken as ≤ 6 % inside the 0.72 × minimum (Inference: Samsung's curve not re-read). C19 / C20 keep C23630. |
| C123 | Samsung CL05B103KB5NNNC, 10 nF 50 V X7R 10 % 0402, LCSC C15195 (Basic, C408's line) | New Q122 gate–source capacitor at F(18.22,71.85), ACT_EN to GND (R19-SAF-06, D-R19-04). R122 ∥ R123 = 667 Ω with 10 nF plus AO3400A Ciss 630 pF typical ([AO3400A Rev 3.1 p2](https://www.aosmd.com/res/datasheets/AO3400A.pdf)): τ ≈ 7.1 µs (Calculation), microseconds against the load switch's millisecond C120 network. |
| J440, R470 / R471, D440 / D441, C444, C445 | DB125-3.5-4P-GN-S C2757925; 1 kΩ C21190; ESD103-B1-02EL C535146; 100 nF C14663; 22 µF C21397 | The spare AUX port (D-R19-14, owner-approved 2026-10-30): an electrical copy of J410's cell, no new codes. Since D-R20-09 D440 / D441 sit on the bottom under J440, as D410 / D411 under J410, 4.08 / 4.18 mm from their pins centre to centre (3.16 / 3.19 mm pad edge to pad edge). Per board the terminal code is now 4 and the ESD code 8 (37,827 and 201 in JLC stock, 2026-10-31). AUX may draw at most 100 mA at 4.8 V (GAP-3: U401 junction ≤ 125 °C at a 70 °C bay with the inferred 80–110 °C/W; [TPS7A91 SBVS282A p1, p5](https://www.ti.com/lit/ds/symlink/tps7a91.pdf)). Its UART is USART6 PC6 / PC7; the GPS on J410 moves to USART3 PD8 / PD9 (AF7, [DS12110 Rev 8](https://www.st.com/resource/en/datasheet/stm32h743vi.pdf) Table 13 p94; FT_h, Table 9 p75). J410 / J420 / J440 are electrically identical; firmware keeps the port map. Eight DB125 terminals now carry 27 contacts, all Ø1.30 mm holes / Ø1.90 mm copper (R19-BOM-04 carried). |
| C84 | MA25V470M8x10, C46550466 | Its generated footprint `M3_MA_8x10` has no F.Paste since round 19 (D-R19-07; R19-MFG-02 / R19-BOM-02): no stencil aperture, the hand fit applies its own solder. The [supplier sheet](https://atta.szlcsc.com/upload/public/pdf/source/20260306/24758A4FC016E80367B87853635CDCC1.pdf) gives no manual or reflow profile; ORDERING §8.2 holds the heat limit (Inference) and the re-inspection of the bottom joints under it (R19-MEC-02). |
| TP121 | removed | TP121 and its 7.14 mm ACT_GATE stub are gone (D-R19-03); probe ACT_GATE at R119.1, R120.2 or C120.2 before coating. |

**Round 23 notes (R23-MCU-03, R23-PARTS-01; text only).** FS_XL_HG code 010 is 3.904 mg/LSB on the ISM6HG256X, the LSM6DSV320X and the LSM6DSV80X (DS14764 Table 3 p12) and clips at ±80 g on the 80X, so codes 001 / 010 serve all three; never use ST's ism6hg256x driver's 256 g enum (0x3 is reserved in DS15034 Table 150). Hot-end ratings are judged against part temperature, not bay air: the 85 °C parts (MS5611, AP6320x, J430, the U4 alternates) need bay air ≤ about 55–60 °C until the first-article 70 °C chamber test at the pad load passes (ORDERING 8.3; Inference for the board rise).

**Cold-end ratings (R19-BOM-03).** Four fitted parts are rated above −40 °C at the cold end. The bay is −20…+70 °C (85 °C unshaded, DESIGN_ASSURANCE §6.1):
- LS120 buzzer: −20…+70 °C (no cold margin at the −20 °C bay floor).
- J430 Molex 472192001 (C164170): −20…+85 °C in the [JLC / LCSC listing](https://www.lcsc.com/product-detail/C164170.html) and the Molex product page (above); some distributors list −40 °C. No cold margin at −20 °C; confirm with the Molex product specification (not retrieved). J430 is the in-flight secondary log.
- LED1 Nationstar NCD0805R1 (C84256): −30…+85 °C ([datasheet p1](https://datasheet.lcsc.com/datasheet/pdf/e3e35db60c068efe42b02d21fe498cf3.pdf?productCode=C84256)); 10 °C of cold margin.
- J3 HRO TYPE-C-31-M-12 (C165948): −30…+80 °C ([drawing 2020-12-08 rev A p1, note 5](https://datasheet.lcsc.com/lcsc/1903211732_Korean-Hroparts-Elec-TYPE-C-31-M-12_C165948.pdf)); its +80 °C is below the 85 °C unshaded case, but J3 is unmated in flight (non-operating exposure).
Every other fitted part is rated −40…+85 °C or wider in maker or supplier data (the round 19 parts lens scanned 82 codes). No flight-critical part is affected.

**R16 retained MEMS stress deviation (R16-MEC-01, Minor):** component-side B.Cu
still crosses U4's nominal body outside its lands: IMU_CS 0.7596+0.0918 mm,
SPI1_MISO 0.3257 mm,IMU_INT1 0.3250 mm and3V3A 0.3257 mm (0.001mm midpoint sampling;
native body x15.50..18.50/y44.65..47.15). Signal widths are0.20mm; the0.25mm
3V3A rail also departs from the same-width guidance. These specifically depart from
[ST TN1383 Rev1 pp7–9](https://www.st.com/resource/en/technical_note/tn1383-pcb-design-guidelines-for-mems-sensors-stmicroelectronics.pdf)
pad-axis/outside-body stress guidance. The R15 GND correction and passing M-7/P3
checks are narrower than complete compliance. The bounded supply prototype
has only0.106949mm clearance; the next combined recipe creates an acute45degree
CS junction at B(14.2,44.7). Both are rejected, with no production copper change
or full PCB/CLI/gate qualification of that MEMS recipe. Retain first-article
bias/temperature/vibration qualification. [Prototype evidence](../r10_review/round16_minor_prototypes.json)
and R16-MEC-01/D-R16-02 preserve the limits; no offset error or physical failure
is demonstrated.

**R17 record amendments (D-R17-01..03).** Pad sizing uses the explicit
upper-load6 V/80% [worksheet](../../../../docs/ORDERING.md#811-pad-energy-worksheet-d-r17-01-calculationinference)
and [calculation](../r10_review/round17_pad_energy.json): two-hour board charge
1.812657/2.390393/4.123602 Ah for camera0/0.5/2 h; board-only20%-unused capacities
2.265821/2.987991/5.154503 Ah. Add all motor,flight and recovery charge before
dividing by0.8. Efficiency/duty are allocations, not maker guarantees; no pack
is selected/qualified. Camera off unless recording; source reserve/resistance,
aged/cold capacity,transients and bay fit remain required. The old mixed-basis
capacity examples are superseded without changing dated D-CIR-02.

Future programming acceptance records/readbacks intended user-flash BOOT_ADD0
and relevant boot settings, then verifies reset reaches the bound application
with the e-match disconnected. BOOT0 low alone selects BOOT_ADD0 and can enter
ROM at0x1FF0; PA2 then drives loader USART2_TX/servo3 ([ST AN2606 Rev70 Table2
Pattern10 p35,Table135 p321](https://www.st.com/resource/en/application_note/an2606-stm32-microcontroller-system-memory-boot-mode-stmicroelectronics.pdf)).
No option-byte programming/readback or R10 firmware exists here. Deliberate
service remains before IWDG,PC1/PE4 locked low,camera EN/OE low,SD_CS high,
dummy loads/no e-match. Current PDF raster inspection is not claimed.

U5's1.1 mm model/cover height is a conservative engineering allocation
(native model1.100074 mm), not maker maximum. [TE MS5611-01BA03 06/2017
p15 Fig18](https://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocFormat=pdf&DocLang=English&DocNm=MS5611-01BA03&DocType=Data+Sheet&PartCntxt=MS561101BA03-50)
specifies1.0 mm +0/-0.10; at nominal4 mm standoffs the package-only gap is3.0 mm,
allocated cover gap2.9 mm. Seating/foam/adhesive/compression/venting and barometer
behavior remain unqualified; no model/CAD change.

**Always-on GPS/radio.** J410/J420 pin1 directly joins PORT_4V8. Delete U410/U420,
R410–412/R420–422, U411/U421, R442/R452 and C440/C443/C450/C453. Keep the four
1k series resistors and ground-only ESD, and C410/C411/C420/C421 as local supply
bypass. R440/R450 connect RX_WIRE to RX_MCU; R441/R451 connect TX_MCU to TX_WIRE.
No firmware port power-cycle, individual FAULT or OE remains. **Current pin map (D-R19-14, R20-MCU-04):** PD8 / PD9
(GPS, J410, USART3, through R441 / R440) and PC6 / PC7 (AUX, J440, USART6, through R471 / R470, ESD D440 / D441) are
FT_h; PB12 / PB13 (radio, J420, UART5, through R450 / R451) are FT_u ([ST DS12110 Rev 8](https://www.st.com/resource/en/datasheet/stm32h743vi.pdf)
Table 9 pp. 74–79; AF Tables 11–13 pp. 91–94; Table 119 p. 212). The digital FT absolute ceiling is
min(min(relevant supplies) + 4 V, 6 V), with zero positive-injection allowance (Rev 8 Table 119 pp. 212–213; the 6 V cap
is a Rev 11 design limit, Inference for Rev 8). Keep direct UART RX internal pulls disabled throughout operation: Rev 8
Table 122 note 3 p. 215 / Table 157 note 7 p. 247 require pulls off above the relevant I/O supply + 0.3 V; the 4 V
absolute-stress condition does not replace that operating rule. **Endpoint rule (R20-MCU-02):** any device on J410,
J420 or J440 must drive its TX high at no more than 3.6 V (no 5 V-logic devices), because PORT_4V8 rises about 44 ms or
more before 3V3 and an FT pin allows only 4.0 V while VDD = 0 (Table 119 p. 212). Confirm module levels and the
PORT_4V8-to-3V3 lag on the bench. A1k resistor does not give powered-off isolation: no self-powered
GPS/radio with the board off. Direct power pins can also back-feed the shared LDO/buck
(Inference); connect the e-match only without USB or any self-powered port source.

**Camera switch retained.** U402, U12 and U13 remain. A direct CAM_5V connection
would provide a back-feed path into PORT_5V3. [TPS2553 SLVS841F pp7/13–14](https://www.ti.com/lit/ds/symlink/tps2553.pdf)
has disabled reverse blocking; enabled reverse blocking needs the specified voltage
threshold and3–7ms trip transition, so it does not remove the no-back-feed operating rule.
Camera OE must go low before EN. Only camera EN/OE/FAULT GPIOs remain.

**Current camera harness allocation.** J9 is DB125, not GH. The conditional
5.031682V minimum at1A uses the port-buck low corner5.366682V, switch135mOhm,
an additional complete supply-plus-return loop<=150mOhm and negative transient
allocation<=50mV. Measure that loop four-wire, including native copper, both
DB125 joints/contacts, ferrules, leads and camera-end termination. The old GH
100mOhm/26AWG/6-7cm split below is historical and is not a current DB125 lead
length limit. DB125 accepts28-16AWG; use qualified ferrules or wire>=28AWG.

**Round12 evidence correction.** D-R12-01 withdraws the PC14<=2.9mA proof.
DS12110 Rev11 Table149p244's3mA output-drop test point does not supply a minimum
driver resistance. R1621k remains; resistor-only initial current is3.3mA nominal
or3.363636mA at the stated3.33V/990Ohm initial-tolerance corner, with about
0.306mA steady current. Gate/driver transients and all-temperature limits remain
unmeasured; use4kHz with LSE disabled. Pin-table provenance is regenerated.

**Shared port fault budget (Calc / Inference).** [TPS7A91 SBVS282A p5](https://www.ti.com/lit/ds/symlink/tps7a91.pdf)
limits at1.5–1.9A; hard-short foldback≈1.45A is typical, not a guaranteed maximum.
A GPS/radio cable short can collapse both modules. With camera1A and11mA allowance,
prospective U400 demand is2.911A, above its2A continuous rating; camera plus LDO
both at their limits would demand3.160498A. Current-limit/hiccup/thermal behavior is
allowed to remove the ports; continuous fault operation is not qualified.
[AP63201 DS41326 Rev3-2 p5](https://www.diodes.com/assets/Datasheets/AP63200-AP63201-AP63203-AP63205.pdf)
gives3.1A maximum high-side peak limit. Conservatively using the whole input pulse
without duty/hiccup reduction, add(1.4W core+0.825W SDwrite)/3.5V,3.147mA R92 bleed
at U9's 10.18 V OVLO corner (with the OVLO pin leakage IOVLKG ±0.1 µA, TI SLVSFC9C §6.5; D-R25-03, R25-TRI-04; it was
3.083 mA at 9.97 V) and5mA allowance: **3.743861A** (`parts_budget.json`), below the calculated U9 minimum3.946188A
by0.202327A. TI TPS25947 RevC p9/eq7 p32 gives3.96–4.84A at exact750ohm.
Inverse-R sensitivity for R84 RT0603BRD07750RL0.1%/25ppm/K over100K
(+/-0.35%) gives3.946188–4.856999A (Calculation/Inference, not new TI
characterization). This is a
threshold-based inference excluding comparator overshoot and parasitic rail dips;
bench a short on either port with camera and SD writing while observing logic/flight
state. No ideal2A clamp is assumed. Normal minimum endpoint estimates improve to
radio4.601504V and GPS4.631504V because the deleted switches no longer drop voltage.

**microSD socket and supply.** J430 is Molex **472192001 / C164170**, locking hinge,
no spring-eject mechanism and no mechanical card-detect switch. [Molex product](https://www.molex.com/en-us/products/part-detail/472192001)
gives0.434g and–20…85°C; a closed hinge retains the card, but flight shock/vibration
qualification remains open. JLC exact-code public lookup at2026-10-29T02:23:02Z
returned8740 in stock, minimum1, Extended, USD0.7288 each at5; refresh before order.
[JLC part page](https://jlcpcb.com/partdetail/Molex-472192001/C164170).
The maker [SD-47219-001 RevG, sheet1](https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/salesdrawingpdf/472/47219/472192001_sd.pdf)
was inspected as a rendered drawing; the identical maker-document
[mirror](https://cdn.promelec.ru/upload/items/2020/09/01/472192001_sd.pdf)
was used when the maker download timed out. Local origin is the midpoint of shell
columns, on the signal-pad row. Pin1 is to the right. Pins1–8 centres are
x3.205/2.105/1.005/–0.095/–1.195/–2.295/–3.395/–4.495,y0mm; pads0.80×1.50mm.
Shell G1/G2/G3/G4 use supplier numeric aliases12/9/10/11 at
(+6.875,+2.6)/(+6.875,–5.7)/(–6.875,–5.7)/(–6.875,+2.6), pads1.45×2.00mm,
all GND. Maker body13.60×14.50×1.90mm,±0.15mm general tolerance. The generated
15.05×15.70×2.10mm closed card/socket allocation includes the nails and general
tolerances: width=(13.60+0.15)+2×(0.50+0.15)=15.05mm. Socket extent is
y−9.70…+5.35mm; retain the inferred card front at+6.00mm and height2.10mm.
Common seating/centring and the card front remain **Inference**, not a maker-
certified maximum assembled envelope. Check actual card, solder seating and lid
access. Board must be out
of the bay and off for card insertion/removal. Remove the board from the continuous
sled before opening the bottom hinge, unless a physical access window has been
qualified; the closed-card envelope does not allocate lid-opening space.
Maker stencil is0.10or0.12mm with100%
apertures;0.08mm is not recommended. Supplier pad evidence is from
[JLCEDA/EasyEDA Official Library](https://easyeda.com/api/products/C164170/components)
([library](https://easyeda.com/), [JLCEDA](https://lceda.cn/)); after origin translation the
maker/supplier signal/shell differences are about0.005mm, not a pin-order substitution.

SPI3 uses PC10/PC11/PC12 AF6 (U1.78/79/80) and PD0 softwareCS(U1.81).
Card pins1DAT2,2CS,3MOSI/CMD,4=3V3,5SCK,6GND,7MISO/DAT0,8DAT1;
R460–46410k pullups onCS/CMD/DAT0/DAT1/DAT2, C460100nF+C46122uF local bypass,
no clock pull. The pullup choice follows [Espressif's primary SD interface guidance](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/peripherals/sd_pullup_requirements.html)
for SPI/one-bit operation. [SD Association Physical Layer Simplified v9.10](https://www.sdcard.org/downloads/pls/)
§6.4.1p274 requires power/ramp settling and≥74clocks withCMD/CS high beforeCMD0
entersSPI. Use100–400kHz initialization and≤25MHz default-speed operation. These
are firmware obligations, not measured card timing. PC11 is an AN2606 loader output;
R460 keeps CS high, leaving card DAT0 deselected. Keep synchronous trace disabled.

QSPI remains the primary crash-safe log; SD is secondary, nonblocking and expendable
under overload or power loss. Allocate card≤200mA writing and≤30mA idle at3.3V;
select/bench-confirm a card within those allocations, and do not treat them as universal
card maxima. The budget adds0.776–0.825W write or0.116–0.124W idle at80–85% converter
efficiency. Card write busy may continue after SPI clocks stop. F6 shedding stops
SD/QSPI writes without a blocking flush, stopsUARTs, lowers cameraOE/EN/MCUclock
and LEDs/buzzer; GPS/radio/card remain powered. The physically-unloaded ports-off
estimate is not an achievable GPS/radio software state. Always-on GPS/radio with
cameraoff/logic-shed/cardidle is now a separate quantified case in `parts_budget.json`.

**All wired connectors use screw terminals.** J400 uses green2-position
DB125-3.5-2P-GN-S/C466970; J9/J410/J420 use green4-position
DB125-3.5-4P-GN-S/C2757925; J122 uses green5-position
DB125-3.5-5P-GN-S/C3646874. Exact JLC public lookup at2026-10-29T03:20:07Z returned
35981/38010/4315 available respectively, minimum1 each; no alternate5-position color
was returned. J121 remains black; body count and explicit function/pin legends distinguish
unkeyed green terminals. [Maker DB125 T0-1 drawing,2022-11-26](https://atta.szlcsc.com/upload/public/pdf/source/20251124/8C215F69B14C8E54AE0F8E5023D4AE9F.pdf)
covers2–24positions and verifies3.5mm pitch, N×3.5 body length,7.4mm depth,8.6mm
height,0.50×0.85mm pins,1.20mm maker holes and28–16AWG solid/stranded clamp range.
All 23 contacts retain nominal Ø1.30mm holes/Ø1.90mm copper at 3.50mm pitch, with
1.60mm nominal interpad gap; the insertion/process allocation remains open below.
Four-position x–5.25/–1.75/+1.75/+5.25; five-position
x–7/–3.5/0/+3.5/+7mm. Round11 corrected the envelope from the maker's
independent end datum, interlock and dimensional tolerances (D-R11-01):

| Positions | Maximum local x union, mm | Maximum local y union, mm | Height, mm |
|---|---|---|---|
| 2 | −4.62…+3.70 | −4.10…+4.00 | 8.90 |
| 4 | −8.32…+7.20 | −4.10…+4.00 | 8.90 |
| 5 | −10.07…+8.95 | −4.10…+4.00 | 8.90 |

The wire face can reach7.70−3.70=+4.00mm; repeated3.90mm annotations name
one rear datum. These unions enclose different permitted tolerance corners, not
an individual8.10mm-deep body. Courtyards add0.20mm around the entire union.
The16mm port pitch retains at least0.48mm between maximum body unions; this
does not qualify screwdriver, wire or staking access.
The current [JLCEDA/EasyEDA Official Library](https://lceda.cn/api/products/C2757925/components)
([five-position](https://lceda.cn/api/products/C3646874/components)) pads were fetched and
matched numerically: both terminal rotations0°, zero origin offset and<0.001mm worst
residual; microSD rotation0°, offset(0,+1.550)mm and0.005mm worst residual across
all12pads. Next-best rotation residuals7.42/9.90/11.36mm distinguish orientation.
These are library/CPL geometry checks, not JLC preview or assembled-board evidence.

J122 pins1–4 areSERVO1–4_OUT, pin5GND signal reference; no servo power on the board.
The1k resistors, pull-downs andSRV05-4 stay. J400 pins1/2 remainBAT_SW_SOURCE/RETURN.
Ports retain their prior signal convention: GPS/radio pins1supply,2GND,3boardTX,
4boardRX; camera pins1CAM_5V,2GND,3CAM_RX_WIRE(boardRX),4CAM_TX_WIRE(boardTX).
DB125 leads at clamps must be≥28AWG,≤16AWG; use qualified ferrules/splices for thinner
module leads, verify clamp retention under vibration, avoid solder-tinned stranded ends.
Keep existing camera≤0.15Ω and GPS/radio≤0.20Ω copper-loop allowances; verify actual
assembled harness loss including clamps before flight. Physical polarity/keying is lost:
full per-pin legends and end-to-end harness checks are mandatory. Screw access and
wire bend clearance remain physical-fit qualifications.


## Round-9 retained capacitor labels (2026-10-28; R9-BOM-01)

`circuit.json`'s `value_overrides` expands 21 retained R9 Value labels; order codes,
maker identities, nets and lands are unchanged. Source inventory:

| References | Full Value | Existing order code / source |
|---|---|---|
| C6–C11 | 22uF 25V X5R 20% | C45783, Samsung [CL21A226MAQNNNE](https://product.samsungsem.com/mlcc/CL21A226MAQNNN.do) |
| C19/C20 (C87 until round 19; now C21120 220 nF) | 2.2uF 16V X5R 10% | C23630, Samsung [CL10A225KO8NNNC](https://www.lcsc.com/product-detail/C23630.html) |
| C22 | 1uF 50V X5R 10% | C15849, Samsung [CL10A105KB8NNNC](https://product.samsungsem.com/mlcc/CL10A105KB8NNN.do) |
| C23/C28 | 4.7uF 16V X5R 10% | C19666, Samsung [CL10A475KO8NNNC](https://product.samsungsem.com/mlcc/CL10A475KO8NNN.do) |
| C25/C26 | 10pF 50V C0G 5% | C32949, Samsung [CL05C100JB5NNNC](https://product.samsungsem.com/mlcc/CL05C100JB5NNN.do) |
| C60/C94/C127/C129 (C122 later removed) | 10nF 50V X7R 10% | C57112, FH [0603B103K500NT](https://www.lcsc.com/product-detail/C57112.html) |
| C88/C99 | 100nF 50V X7R 10% | C307331, Samsung [CL05B104KB54PNC](https://product.samsungsem.com/mlcc/CL05B104KB54PN.do) |


## Round-15 component qualification (2026-10-30; R15-BOM-02 / R15-MCU-01)

The fresh independent verifiers retain both items as Minor qualification gaps.
Keep the current terminal holes and C19/C20 for the unqualified CAD candidate;
no physical insertion failure, installed C/ESR violation or regulator failure
has been demonstrated. Focused measurements below belong to the reviewed
`7866d6b8…`; the R15 fix retains these terminal lands/holes and exact capacitors.

**DB125 insertion and fabrication allocation.** All seven exact terminal variants
have 23 contacts with nominal Ø1.30mm holes, Ø1.90mm lands and 3.50mm pitch.
[DORABO T0-1, sheet1/1, 2022-11-26](https://atta.szlcsc.com/upload/public/pdf/source/20251124/8C215F69B14C8E54AE0F8E5023D4AE9F.pdf)
shows nominal 0.50×0.85mm pins and recommends Ø1.20mm holes. Applying its ±0.20mm
general table independently to both pin dimensions gives a **conditional sharp**
0.70×1.05mm section, diagonal 1.261942946mm. [JLC's current drilling table](https://jlcpcb.com/capabilities/pcb-capabilities)
allows +0.13/−0.08mm finished PTH size, giving 1.22mm minimum and a size-only
allowance of −0.041942946mm under that model. Actual insertion-section corners,
burrs, pin form and relative pattern limits are unresolved. The cited
[GB/T14486-2008 record](https://openstd.samr.gov.cn/bzgk/std/newGbInfo?hcno=D13DCBFC8E64A2B32F77B4CE9EBD4B92)
covers moulded plastic parts; clarify the drawing table's metal-pin applicability
with the maker rather than assuming either its application or exclusion.

Native S-8 passes. On `632a9ad3…` the minimum was **1.102501576 mm**, J121.1 nominal hole wall to In2 3V3 fill (1.103 mm on `a3144b15…`); since the round 18 fix pass S-8 also covers the load-switch gate and enable barrels, whose nominal minimum is 1.050 mm.
That is CAD geometry. A conditional +0.13 mm hole diameter and 0.075 mm displacement
toward that fill consume 0.140 mm radially, leaving 0.962501576 mm (0.910 mm at a 1.050 mm barrel; arithmetic only). This illustrative
process corner is not a measured failure or nominal CAD violation: position
datum/correlation, layer registration and maximum outer barrel need fabricator
allocation. Present nominal annulus is 0.30 mm. Enlarging holes alone reduces both
annulus and S-8 reserve; **no enlarged drill is approved**.

Before assembly, obtain maker/assembler maximum insertion profile, relative pin
pattern/form limits and an approved seating/lead-form method. Agree finished-hole
minimum/maximum, relative pattern error, annulus and protected barrel-to-inner-copper
realization with the fabricator. A sufficient geometric allocation is
`Dhole_min ≥ Dpin_circumscribed_max + 2×eresidual + positive assembly allowance`
(Inference), with residual error after permitted alignment/forming; do not add
per-pitch errors again on top of a dimensioned row-span tolerance. On first
articles inspect all 23 contacts for full seating, undamaged barrels/plating and
solder fill, then complete the existing clamp, harness, staking and retention
checks. [JLC's assembly inspection guidance](https://jlcpcb.com/blog/pcb-header-design)
distinguishes finished-hole, plating, seating and solder-fill checks. If allocation
fails, review holes/lands and protected inner copper together before fabrication.
Evidence: [terminal verification](../r10_review/round15_terminal_verification.md)
and [measurements](../r10_review/round15_terminal_verification.json).

**VCAP C19/C20 operating qualification.** Retain Samsung **CL10A225KO8NNNC /
C23630**, 2.2µF 16V X5R ±10%, separately on VCAP1/U1.48 and VCAP2/U1.73.
Initial 1.98–2.42µF complies with nominal selection. [ST DS12110 Rev11 Table114
p211](https://www.st.com/resource/en/datasheet/stm32h743vi.pdf) specifies 2.2µF
typical with ±20% variation and ESR<0.1Ω. Its numerical 1.76–2.64µF window needs
ST's measurement/interpretation resolved: the table does not specify frequency,
AC amplitude or separate nominal selection from combined operating capacitance.

The [exact Samsung specification, p2 and manual pp12–17](https://product.samsungsem.com/part/download.do?masterKey=CL10A225KO8NNN&type=specsheet)
uses 1kHz±10%/1.0±0.2Vrms after 150°C/1h treatment and 24±2h recovery; X5R allows
±15% temperature change. Its zero-bias initial-tolerance/TCC envelope is
1.683–2.783µF (Calculation), not demonstrated simultaneous corners. Combining
−10% initial tolerance with the separate [typical Samsung curves](https://product.samsungsem.com/mlcc/CL10A225KO8NNN.do)
at 70°C/1.0V gives **1.716525µF (Inference)**, not a guaranteed joint corner.
Temperature/DC-bias dependence is not established as separable; the 8V biased-TCC
example cannot qualify VCAP. Small-signal AC dependence and model-dependent aging
add uncertainty; do not multiply another curve into that inference or treat typical
ESR as an operating guarantee.

Resolve ST's C/ESR test conditions; record fitted silicon revision and allowed
startup/operating regulator modes, including VOS transitions. Obtain maker-supported
combined bounds, or qualify the exact fitted parts after reflow/rework and defined
aging over actual bias, local temperature and relevant frequency/ripple conditions.
Check **both lower and upper capacitance, ESR, startup and load/clock transients**.
The −20…+70°C bay scope does not establish capacitor temperature; keep its surface
within the −55…+85°C part rating. A 3.3µF±10% substitution spans 2.97–3.63µF nominal,
already above 2.64µF: larger nominal capacitance alone is not a correction. Any
replacement needs exact identity, compatible lands/process and the same complete
C/ESR qualification. Evidence: [VCAP verification](../r10_review/round15_vcap_verification.md)
and [conditions/calculations](../r10_review/round15_vcap_verification.json).


## AUD/GAP component amendments (2026-10-28; CAD / Calc / Inference only)

**AUD-1:** C92 is Samsung CL10A475KO8NNNC / C19666, 4.7 µF 16 V X5R ±10%
0603, B (34.2,45.2), −90°, using `rocket:C0603` as already used by C23/C28
with the same C19666 code. The FAB integration correction uses these local-library measurements:
local pad centres ±0.775 → ±0.700 mm, pads 0.90 × 0.95 mm roundrect →
0.80 × 0.90 mm rectangular, courtyard 2.96 × 1.46 → 2.70 × 1.40 mm.
C92.1/.2 move to (34.2, 44.500) / (34.2, 45.900); three local routing corners
must follow the 0.075 mm inward pad shifts. The component value, nets and
capacitance calculation are unchanged. [The exact maker page](https://product.samsungsem.com/mlcc/CL10A475KO8NNN.do)
gives a typical retained fraction 0.6832757 at 3.4 V. Applying 0.9 initial,
0.85 temperature and 0.9 aging factors gives **2.211046 µF**, above
[TPS709's 1.5 µF effective minimum](https://www.ti.com/lit/ds/symlink/tps709.pdf).
Bias and aging allowances are **Inference**, not a guaranteed production minimum;
the part is NRND. Bench stability and load-transient verification remain open.

**AUD-3 / D-AUD-03a:** Q120/Q121 become AOS AONR21357 / C431196.
[Maker Rev2.1 pp1–4](https://www.aosmd.com/res/datasheets/AONR21357.pdf)
specifies −30 V drain, ±25 V gate and 12.3 mΩ maximum at −4.5 V /25°C.
The ~18 V gate event therefore remains inside its absolute gate limit.
The ~1.4 hot factor at 125°C is a typical curve: 17.22 mΩ is **Inference**;
use **40 mΩ per FET** for the primary fire-current acceptance envelope and
measure hot resistance. At 6 V loaded BAT_IN, 4.2 A through that source-side
resistance, 0.1 V allowed at Q122 drain, and resistor 1% plus 100 ppm/K through
125 °C, settled |Vgs| ≥ 4.7444 V (R119∥R120 = 50 kΩ since the round 18 fix pass; 5.1916 V with R120 alone). Fully-on 4.2 A /20 ms at 40 mΩ dissipates
0.706 W /0.0141 J per FET. The shorted-load turn-on line is
I=(8.4−|Vds|)/R134min; maximum one-FET linear dissipation is 8.95 W at
|Vds|=4.2 V, I=2.13 A. This is inside the maker's reference-case SOA after
70°C derating; the reference-board 50 ms power curve is about24 W at25°C,
about15 W after derating. These graph reads and extrapolation to actual copper
are **Inference**: note F assumes a heatsink, note H a 1 in² /2 oz board.
Bench shorted-dummy enabling and 20 ms /4.2 A pulses at70°C must measure Vgs,
Vds, current and case rise; 85°C remains a sensitivity until qualified.

The new land follows [AOS PO-00047 rev I](https://www.aosmd.com/sites/default/files/res/packaging_information/DFN3x3A_8L_EP1_P.pdf),
DFN3x3A_8L_EP1_P: nominal3×3 mm body, max3.1×3.1×0.9 mm and3.3 mm lead span.
Local S1–3/G4 centres are x−0.975/−0.325/+0.325/+0.975,y+1.4, pads0.35×0.50;
D5–8 are x+0.975/+0.325/−0.325/−0.975,y−1.495, pads0.40×0.31 (0.01 overlap
with drain9, leaving the maker's0.30 mm finger copper union). Drain9 is the
maker polygon, x±1.225,y−1.35…+0.63, with wings to x±1.605 at y±0.215.
The 3.3×3.3×0.9 mm model is a fit envelope. Verify actual supplier numbered
pads and CPL orientation, stencil/assembly quality and solder coverage before order.

C120 reuses Samsung **CL10B105KA8NNNC / C29936**, 1 µF 25 V X7R ±10%, on
`rocket:C_0603_1608Metric`, matching C86/C97/C98 with the same C29936 code.
This FAB integration correction supersedes the initial unchanged-C0603-land choice:
the pad and courtyard changes are the reverse of C92's above. Move C120 0.075 mm
north to B (17.1, 71.525), −90°, retaining pad 2 on the existing ACT_GATE lane
at (17.1, 72.300); pad 1 becomes (17.1, 70.750). Review its source tap and local
clearance after regeneration. The electrical timing assumptions are unchanged.
[Maker identity and typical curves](https://product.samsungsem.com/mlcc/CL10B105KA8NNN.do)
replace the former 2.2 µF16 V part's above-rating condition. Cmax=1.265 µF;
R121 with R119∥R120 (50 kΩ) gives tau ≤ 10.7525 ms and ≤ 31.89 ms to |Vgs|=4.5 V at the corner above (R120∥R121: ≤ 11.73 ms and ≤ 23.65 ms before the round 18 fix pass).
Hold PE4 low and wait **≥100 ms after ACT_EN** before bus checks or a permitted
fire. The typical bias curve with0.9 tolerance/0.85 temperature/0.9 aging yields
Ceff≈0.587 µF at4.5 V (linear interpolation), so both FETs'2×70 nC maximum10 V total gate charge
would step it about0.239 V (**Inference**, not a hot off-state guarantee).
Check Miller turn-on with power attachment, reset/unpowered behavior and gate
turn-off on the actual board. The load-switch off RC is≤129.03 ms; Q124's
independent fast current-off contract remains below.

**AUD-4/5/7/9:** J123/R160/R161/C160/D122 and TP84/85/86/87/89/92 are removed;
PC13 U1.7 is NC/analog, no EXTI13. Keep TP80–83/TP120–122 and USB-only U10/U11.
R412/R422/R432 use10 kΩ1%0402 C25744; R150–153 use1 kΩ1%0603 C21190,
UNI-ROYAL0603WAF1001T5E rated100 mW through70°C.
[Maker series specification](https://datasheet.lcsc.com/datasheet/pdf/0a975aaa49b7c97f38a963127be4a823.pdf)
gives the above10Ω resistors100 ppm/K. The8.4 V chafe is64 mW with a0.4 V
low output, or a conservative72 mW at0 V and980Ω; neither needs the inherited
30%-of-rating rule. Port and servo component changes retain their protective networks.

**Single-switch passive cold check (Calc / Inference, no firmware thresholds):**
keep PC1 ACT_EN low and PE4 low. If the load switch was previously enabled, wait
at least1 s and verify RAW_ACT has discharged / ACT_GATE has returned off before
classifying a reading. New C120/R120 maximum off tau≈129 ms makes1 s about7.75tau;
this wait is provisional until bench-qualified. At boot without a prior enable,
C120 starts near Vgs=0. Only after a valid passive fault check may firmware enable
PC1, still holding PE4 low, then wait≥100 ms before powered-bus checks.

OUT has one11.2 kΩ divider; RAW_ACT now has one11.2 kΩ ARM1_SENSE divider.
The duplicate R177/R124/R125/R182/R172/C122 chain is removed; PB0 is NC/analog.
Each is10.2 kΩ over1 kΩ (two5.1 kΩ series, two2 kΩ parallel). With a1–2Ω e-match
plus R1342Ω, both banks load D120/R13110 kΩ. For U=3V3−Vf,
Rload=11.2k∥(Rmatch+R134+11.2k), Vout=U×Rload/(10k+Rload),
Vraw=Vout×11.2k/(Rmatch+R134+11.2k); each sense ADC is its bus divided by11.2.
Use nominal3V3=3.3 V, Vf=0.20 V for the nominal column. **One basis (R23-DOCS_BINDING-02):** this nominal Vf = 0.20 V table (healthy cold CONT / BUS 99.369 / 99.338 mV, open 146.23 / 0 mV) is the reference; the 96.2 / 96.1 / 141.5 mV figures quoted for the R19-SAF-04 bridge cases elsewhere are the same formula at Vf = 0.30 V (a 3.0 V source; Calculation). The illustrative band
uses3V3=3.135–3.465 V (existing±5% budgeting assumption), Vf=0–0.32 V, and each
resistor at±1.45% (1% plus100 ppm/K to70°C). The diode range is an **Inference**
from the [JSCJ BAT54/A/C/S25°C table](https://www.lcsc.com/datasheet/lcsc_datasheet_1809200014_Jiangsu-Changjing-Electronics-Technology-Co---Ltd--BAT54A_C8591.pdf)
(Vf max0.32 V at1 mA, above the diagnostic current); it is not a guaranteed hot/cold
range. Original supplier PDF access was blocked in this pass; the cached maker
excerpt was available. ADC pins are analog with no pull, fully settled, and the
listed bands assume zero ADC/FET/board leakage and no external backfeed.

| ACT_EN off / PE4 low, settled state | CONT ADC nominal (illustrative band) | Sole ARM1 bus ADC nominal (illustrative band) |
|---|---|---|
| Healthy1–2Ω dummy e-match |99.368924 mV (86.985560–115.190914 mV)|99.337881 mV (86.956912–115.157028 mV)|
| Open e-match |146.23 mV (129.16–168.02 mV)|0 V before leakage|
| Q124 drain grounded / stuck-on, e-match connected |approximately0 V|approximately0 V|
| Shorted e-match |approximately the healthy row|approximately the healthy row; not distinguishable here|

These bands exclude leakage, ADC offset, reference error, acquisition effects and
unqualified diode temperature behavior. As sensitivity only, ±10 µA net leakage
at both OUT and RAW shifts a healthy ADC about±6.4103 mV; with an open e-match,
±10 µA shifts CONT about±4.72 mV or the sole bus sense about±10.0 mV. Audit2 removes the extra4.7k series resistors: ADC-pin leakage of
1µA now adds about0.911mV through the nominal10.2k∥1k source impedance; the10nF
filter nominalRC is9.11µs. One top-short/bottom-open at the19.9Vclamp gives
19.9×1014.5/(5026.05+1014.5)=3.342171V, below4.0Vanalog absolute maximum.
Both split tops, parallel bottoms and filter capacitors remain; double faults remain
allowed to damage the MCU and are not made safe by software. These are
assumptions, not published hot leakage guarantees. Bench the actual low/healthy/open
states and unexpected powered-bus states across temperature before selecting hard
refusal thresholds. Old ARM-plug-out≈100 mV bands do not transfer. These checks
are hard refusals on the ground; in flight they only log/annunciate and never veto
a fire (AGENTS§2.3).

**GAP-1, requirements audit 2 (current Calc / Inference):** select MJG J-Tek
LEAD-FREE, standard 24 AWG, protective shroud retained. The [maker sheet p1](https://electricmatch.com/upload/JTEK_TECHNICAL_INFORMATION_SHEET_SPECIFICATIONS.PDF)
publishes 0.75 A all-fire at 0.5 s, recommended minimum 1.00 A/nominal 1.25 A,
average 1 Ω bridgewire (standard deviation 0.09 Ω), 40 mA maximum test, 0.30 A no-fire
and 4 mJ minimum all-fire energy. One 1.5× current margin gives **1.125 A**;
the old 1.5 A criterion came from an unnamed 1 A e-match and is superseded.

`parts_budget.json` now includes 12.370807 W normal converter allocation with SD
writes and always-on GPS/radio. Voc ≥ 7.4 V equivalent is required **at the fire instant**
after pad/flight drain, Rpack ≤ 0.15 Ω, servo stall 1.92 A each. Solve
(1+Rpack/Rfire)V²−(Voc−Rpack×Iservo)V+Rpack×Pother=0 using its high root;
Ifire=V/Rfire. Retain conservative 2 Ω e-match and ≤ 0.3 Ω external leads/harness,
R134 tolerance/hot corner 2.02909 Ω, hot FETs, 5 mΩ ground/10 mΩ contact allowances.
The current `parts_budget.json` is regenerated and bound to PCB
`a0ec075e…` (fire-path figures unchanged from `50a39de5…`) instead of carrying circuit-pass length literals. Native fire-path pruning
gives BAT_IN 6.307107 mm / 1.0 mm, RAW_ACT 5.886133 mm, IGN 10.523276 mm and
OUT 7.854478 mm at 0.5 mm, plus one aligned 2.2 mm/0.4 mm source path. BAT_IN includes
the additional 0.707107 mm routed entry inside Q120's common drain pad; dead sense
branches are excluded, no parallel-source credit is taken and no fire path has a
series via. Copper is 29.650284 mΩ at 20 °C/35.476565 mΩ at 70 °C (TCR 0.00393/K).
With the primary 40 mΩ/FET ceiling, total loop 4.617802565 Ω gives 0/1/2/3/4-stall
currents 1.540851284/1.475765326/1.410415927/1.344760704/1.278747143 A
(other converter load 13.064 W with the 100 mA AUX allowance);
all exceed 1.125 A. D-R11-03 binds the generator to native geometry. The regenerated
budget SHA-256 is `5204280e098eea4981b968789840d97ca3d8f2f4565ca7b5043c3918215ae3bc` (round 26 docs lane read, on `a0ec075e…`; only its board hash changed in round 26; it was `f92611a8…` on `92c3ad59…` after D-R25-03 changed the OVLO-corner keys, 9V97_* → 10V18_*, and the U9 bound, with the fire-path figures unchanged, `52ada1ed…` after the round 24 fix pass, `f734dff7…` on `1407e850…`, `d2e22ea3…` on `5516eeec…`).
On `a3144b15…` the same loop gave 1.544251030/1.479327596/1.414158454/1.348704524/1.282917526 A
(budget SHA-256 `61727af7baec761ded6d75c963bf6442f702a827e59b7e5656de08e526ce54fa`); the AUX allowance's extra load accounts for the change.
On `632a9ad3…` (IGN 10.230382 mm, copper 29.362412 mΩ/35.132126 mΩ) the loop was 4.617458126 Ω with
1.544366072/1.479437787/1.414263776/1.348804955/1.283013039 A and budget SHA-256 `c5fb1337b9561be9f88243145d3e8aa071822116533a70805acfb9f52a42a7ea`;
the longer IGN run (D-R18-05) accounts for the change.
The intermediate `419a8f49…` board had the same fire-path lengths/current estimates;
the new budget binds the later target independently.
The earlier `0c50b9fd…` review calculation (4.618006 Ω, 1.544183 A idle / 1.282861 A
four stalls) remains historical and does not bind the changed board.
These are conditional calculations, not measured guarantees. Neutral/200 ms wait
cannot clear a jam. R134 stays 2 Ω; its normal 20 ms/fault 36 ms pulse bounds stay.
Maker 0.5 s all-fire does not qualify our 20 ms pulse: selected-lot 20 ms firing,
charge deployment, actual source/harness resistance and reserve remain bench gates.

**GAP-5:** [ST DS12110 Rev11 Table136 p233](https://www.st.com/resource/en/datasheet/stm32h743vi.pdf)
gives RevV LSI29.4–33.6 kHz through Tj125°C (29.76 kHz applies only through110°C;
RevY has a different qualification). Bind the actual silicon ID and temperature.
IWDG prescaler÷4/reload239 =960 cycles, nominal30 ms, actual28.571–32.653 ms.
Refresh immediately **before** PE4 rises and never refresh while fire is active.
An independent timer/DMA abort ends normal **physical current within20 ms**,
including gate tail; set its command cutoff early enough for the measured tail.
After current off, complete a valid SAFETY pass and refresh within5 ms:
20+5<28.571 ms. Refreshing during fire is invalid: a late hang adds the watchdog
time to elapsed current and can exceed the resistor envelope.

Floating-MCU discharge is10 kΩ∥(220Ω+1 kΩ)=1087.344Ω. C126 is Samsung
[CL10B224KA8NNNC / C21120](https://product.samsungsem.com/mlcc/CL10B224KA8NNN.do),220 nF X7R ±10% with±15% temperature:
Cmax278.3 nF. Resistor1%+100 ppm/K through125°C gives Rmax1109.091Ω.
From3.6 V to0.4 V, RC≤0.67820 ms; adding [AON7524's22 nC maximum gate-charge](https://www.aosmd.com/sites/default/files/res/datasheets/AON7524.pdf)
allowance yields≈0.73920 ms (**Inference**: hot charge and0.4 V off criterion
are not guaranteed). Use **1.5 ms actual-current tail** only after bench validation.
With prefire/sync≤0.2 ms and reset-to-HiZ≤0.5 ms, total≤34.8531 ms, guarded
at **36 ms**. No firmware or reset/current-tail bench test has passed.

[Bourns CRM2512 maker pulse chart p3](https://www.bourns.com/docs/product-datasheets/CRM.pdf),
≥1Ω curve, reads about90 W at10 ms and25 W at100 ms. Log interpolation gives
61.204 W at20 ms /44.134 W at36 ms (**Inference**, graphical precision).
R134 minimum at70°C is1.97109Ω; ignoring every other series resistance gives
35.7975 W,0.71595 J/20 ms and1.28871 J/36 ms. Thus36 ms has about1.23×
chart margin at70°C under those assumptions. Applying linear155°C derating at
85°C gives only36.345 W versus35.851 W demand (**Inference**), essentially no
useful margin; the85°C condition is unqualified. Scope watchdog refresh, PE4,
TP122, NRST and dummy-load current for early/late CPU starvation, normal abort,
postfire refresh, reset/unpowered gate tails and hot R134 pulses; record resistor
drift and actual physical20/36 ms limits across supply and temperature.

**Current local output paths (GAP-2, native CAD / Inference):** measured on `632a9ad3…` and unchanged on `a3144b15…`; the round 19 CAD hand-back lists no change to these nets on `50a39de5…` (not re-measured by the docs lane) (a net-level comparison of tracks and vias finds no change to U9's BAT_IN or RAW_PROTECTED copper, or to C82 or D9); original paths preserved by exact native comparison,
U9 is B(18.5,81.6), C82 is B(19.3,76.75),90°, and D9 is B(15.0,79.3),−90°.
The saved-copper API gives:

| Part | OUT route (mm) | Local GND route (mm) | Total loop (mm) | Projected area (mm²) |
|---|---:|---:|---:|---:|
| C82 | 3.577817459 | 9.426345597 | 13.004163056 | 6.591562500 |
| D9 | 6.585533906 | 8.176345597 | 14.761879503 | 7.012187500 |

The GND measurement uses the saved fill on a0.05mm grid and full-thickness via
penalties; the projected area is geometry, not an inductance or transient measurement.
Both paths fit the existing GAP-2 bounds without widening them. U9 OUT reaches
RAW_PROTECTED through exactly two local0.5mm-pad/0.3mm-drill vias at
(20.3,79.1)/(21.1,79.1), joined by a0.8mm-long0.4mm B.Cu track. The former
four-via ladder is historical. Current sharing, local heating and collapse waveforms
on this two-via path remain unmeasured. C126 remains220nF at F(16.85,57.675),−90°;
the gate timing and physical-tail obligations above are unchanged.

## Supply contract and sources

RAW_PROTECTED feeds U400 AP63201WU-7 (C2071044), with EN tied to its input.
The buck is always ready with battery protection on; the camera switch U402 defaults off.
**Historical (R18-PWR-03):** the intermediate boards also had GPS and radio port switches U410 and U420; they were removed with the always-on ports, and U402 is the only TPS2553 on the current board.
Neither the buck nor its LDO nor any port supply connects to VLOGIC or 3V3.
The existing logic/USB mux and hold-up path remain separate. U401 is
TPS7A9101DSKR (C2878140); U402 is TPS2553DBVR (C55266).

- [Diodes AP63200/1/3/5, DS41326 Rev3-2](https://www.diodes.com/assets/Datasheets/AP63200-AP63201-AP63203-AP63205.pdf), pp1,5,11–14:
  AP63201 forced PWM, 500 kHz, reference 0.792–0.808 V, input 3.8–32 V,
  high-side current limit 2.5–3.1 A. Pin1 FB,2 EN,3 VIN,4 GND,5 SW,6 BST.
  Section13 supports near-100% duty with bootstrap refresh; it does not specify a
  guaranteed maximum loaded dropout. The 125/68 mΩ switch resistances are typical,
  not maximum. Existing local TSOT26 land is reused.
- [TI TPS7A91 SBVS282A](https://www.ti.com/lit/ds/symlink/tps7a91.pdf), pin table p3,
  electrical table pp5–6, DSK0010A drawing4218903/C:
  output accuracy ±1% for 5 mA–1 A; feedback leakage ±100 nA; dropout at most
  200 mV at 1 A; input at most6.5 V. The electrical table takes precedence over
  contradictory 100 mV prose on the cover. R405820Ω provides at least5.63 mA
  when all ports are off, keeping the accuracy claim inside its specified range.
  IN9/10, OUT1/2, FB3, GND4/11, PG5 unused, SS_CTRL6 ground, EN7 input,
  NR/SS8 has10 nF. No extrapolated accuracy at zero load is used.
- [TI TPS2553 SLVS841G](https://www.ti.com/lit/ds/symlink/tps2553.pdf), October2026,
  electrical table p7 and revision history p27 (retrieved2026-10-28):
  operating2.5–6.5 V, DBV maximum RON135 mΩ over temperature; current-limit
  equations with resistor tolerance; overcurrent FAULT assertion/de-assertion
  deglitch3–11 ms, superseding revisionF's2–10 ms. Reverse-voltage FAULT deglitch
  is separately2–7 ms; reverse-voltage-to-MOSFET-off remains3–7 ms. Pin1 IN,2 GND,
  3 EN,4 open-drain FAULT,5 ILIM,6 OUT. EN has a100 kΩ pull-down; FAULT has a
  logic-side pull-up. Each switch has local input and output capacitors.
- [Bourns SRP5030T](https://www.bourns.com/docs/product-datasheets/srp5030t.pdf):
  L4006.8µH C1329837, ±20%, DCR76.2 mΩ maximum, Irms4 A, Isat4.3 A.
  Keep the existing maker land. At8.4 V input,5.367–5.546 V output, Lmin5.44µH
  and470 kHz (500 kHz less the±6% spread spectrum, DS41326 p5; Inference for the
  low edge), calculated ripple is0.74–0.76 A (DS41326 p13 equation). The peak
  inductor current at the all-ports-shorted load is in the next section. Isat is a
  typical20% drop rating, not an absolute limit.
- [Yageo RT part specification](https://yageogroup.com/component-documentation/download/specsheet/RT0603BRD0725K5L)
  and the same RT0603BRD ordering family establish0.1%/25 ppm/°C.
  [UNI-ROYAL thick-film specification](https://www.uni-royal.cn/en/images/userfile/file/1753752986c56505e6d9ab55c7.pdf)
  specifies100 ppm/°C for0603 values above10Ω. The calculation conservatively
  combines initial tolerance with100°C excursion from25°C independently for
  each resistor. The buck itself is rated ambient−40…85°C, not125°C ambient.
- Capacitors reuse Murata GRM32ER71E226KE15L C21397,22µF/25 V X7R10%,
  on the current board: two at the buck input (C400, C401), three on PORT_5V3 at the buck output, which is also the LDO input (C403, C404, C405), four on PORT_4V8
  (C406, C407, C411, C421, plus C410 and C420 as local bypasses) and one on CAM_5V (C431). Existing 100 nF bootstrap C14663 and 10 nF C15195 are reused.
  **Open:** verify effective capacitance at bias/temperature/aging against
  the maker curves and the assembled converter's stability. Nominal44µF is
  not a stability proof. The LDO requires at least10µF effective at its input
  and output. No substitution to lower-voltage small MLCCs is qualified here.

## Voltage, current and thermal budgets

The rail remains named PORT_5V3 but its qualified *nominal setting* is5.456 V:
R40056.2 kΩ0.1% plus R4042 kΩ1% over R40110 kΩ0.1%.
O5 explicitly leaves the exact set point to implementation. A5.3 V setting cannot
cover the full1 A camera load after aged GH contacts and harness loss.
The LDO nominal is4.792 V:49.9 kΩ/10 kΩ, both0.1%.

The reproducible values in `parts_budget.json` include reference tolerance,
resistor initial tolerance/TCR and LDO feedback leakage. They give:

| Boundary | Calculated bound | Explicit acceptance condition |
|---|---:|---|
| Buck steady rail | 5.367–5.546 V | Regulating input, specified component temperature |
| LDO steady rail | 4.712–4.873 V | Input headroom;5 mA minimum ensured by bleeder |
| Camera at module | ≥5.032 V at1 A | Switch135 mΩ; harness+contacts+copper≤150 mΩ; negative transient≤50 mV |
| Radio at module | ≥4.561 V at300 mA | Harness+contacts+copper≤200 mΩ; negative transient≤50 mV |
| GPS at module | ≥4.611 V at150 mA | Same200 mΩ and50 mV limits |
| Radio/GPS maximum | ≤4.923 V | Positive transient≤50 mV |
| LDO headroom | ≥443 mV | Includes buck negative50 mV; exceeds200 mV maximum dropout |

**The radio and GPS rows above are historical:** they include the drop of the removed U410 / U420 switches. With the switches gone, the conditional endpoint minima on the current board are 4.601504 V at the radio (0.30 A) and 4.631504 V at the GPS (0.15 A), and the camera 5.031682 V at 1 A (see "Always-on GPS/radio", "Current camera harness allocation" and "Shared port fault budget" above, and `parts_budget.json`).

The manufacturer [LR900 manual](https://micoair.com/en/docs/telemetry/lr900/lr900-telemetry)
specifies4.5–5 V and3.3 V UART. [HGLRC](https://www.hglrc.com/products/hglrc-m100_mini-gps)
specifies3.3–5 V. The300/150 mA allocations above are **engineering load envelopes**,
not proven maximum module demand; measure radio TX peaks, GPS startup and camera
startup. The RunCam minimum5 V and battery-surge prohibition remain as cited in
`docs/SIMULATION.md` item20. A current allocation is not permission to exceed GH's
1 A/contact rating. The camera's fault limit exceeds1 A briefly; firmware must
turn off a faulted port, with thermal cycling only a backup.
Budget **11 ms** worst-case overcurrent FAULT deglitch plus firmware detection /
handling latency and actual switch turn-off / current-decay time before claiming
fault shutdown (R9-PWR-02; SLVS841G p7). FAULT is unsuitable for battery-break
detection. This timing correction does not change the current-limit or rail budgets.

R430 (camera) 22.6 kΩ is the only port current-limit resistor on the current board; it includes a 1 % initial plus 1 % temperature allowance in TI SLVS841F equation 1 (p15,
IOSmin / IOSmax). Camera bound: 1.041–1.249 A. R430 is now the FOJAN FRC0603F2262TS (C2999509; ±1 %, ±100 ppm/°C, 0603); that the allowance carries over unchanged is an Inference, because the replaced part's temperature coefficient was not compared here.
**Historical (R18-PWR-03):** R420 (radio) 66.5 kΩ and R410 (GPS) 100 kΩ (R10_DECISIONS D-R3-01) belonged to the removed U420 / U410 switches and bounded the radio at 0.348–0.453 A and the GPS at 0.230–0.309 A;
"a camera short with the other two at their normal allocations is 1.711 A" and "the LDO's two shorted ports (0.762 A) stay below its 1 A rating" are superseded. On the current board the GPS and radio share PORT_4V8, so one cable short runs U401 into its
1.5–1.9 A limit (TI SBVS282A p5) and can collapse both ports, as "Shared port fault budget" above states; the buck (2.5–3.1 A peak limit) hiccups when the camera is also loaded.

**Historical (the removed per-port switch budget; superseded by "Shared port fault budget" above):** **All three ports shorted** (three simultaneous faults) plus11 mA quiescent,
divider and bleeder load draw2.022 A from the buck,1.1% over the AP63201's2 A
continuous rating (DS41326 p1). The criterion that matters is the cycle-by-cycle
limit: the peak inductor current, 2.022 A plus half the ripple (L400 6.8µH−20%,
buck output5.367–5.546 V), must stay below the2.5 A minimum HS peak current
limit (DS41326 p5). Calculated (`parts_budget.json`): 2.38 A at8.4 V and500 kHz,
2.40 A at8.4 V and470 kHz; at the then 9.97 V OVLO corner (the highest RAW_PROTECTED
U9 lets through, M3_R4 A2; the corner is 10.18 V since D-R25-03, which counts the OVLO pin leakage, and the current
budget's prospective all-shorts peak without limiting is 3.657 / 3.627 A at 470 / 500 kHz)2.48 A at500 kHz and2.51 A at470 kHz, i.e. up to
0.007 A over the limit at the spread-spectrum low edge. If the limit is reached
the buck limits each cycle and after2 ms enters hiccup (DS41326 p11): the ports
lose supply, VLOGIC and3V3 are a separate path. Accepted as a triple-fault,
out-of-range-input corner (Inference, no transient simulation). `r10_parts.py`
then asserted the8.4 V figure below2.41 A and the OVLO figures below2.5 A (500 kHz)
and2.51 A (470 kHz); the current generator has no such assert. Shorted switch outputs dissipate watts before shutdown; do
not characterize this as continuous thermal capability. Hardware limits current
even before the MCU handles FAULT.

**Inference, upstream coordination:** with≥80% buck efficiency,5.8 V buck input,
logic path≤0.5 A and all port shorts, U9 current is about2.92 A (below2.95 A,
asserted), versus its3.96 A minimum limit. Buck's own3.1 A maximum peak limit
plus0.5 A logic is3.6 A.
These bounds exclude switching overshoot and are not a proof of transient
selectivity. Starting the2 A logic mux and all peripherals together is prohibited;
port enables default off and firmware sequences their startup. Test a short on
one port and all ports while checking3V3 and VLOGIC remain in regulation.

**Inference, stall input:** for0.15Ω pack resistance,7.68 A stalled servos,
0.5 A board input logic allocation,1.46 A at5.456 V peripheral output and80%
efficiency, solving the constant-power pack sag gives5.921 V from a7.4 V open-pack
floor, before U9 and board losses. A6 V open pack gives4.436 V. Buck near-100%
duty cannot boost either case. No all-load camera guarantee exists at the low-pack
four-stall corner. Shed all port enables before RAW_PROTECTED falls below6.2 V;
accept loss of peripheral operation while retaining logic/recovery. The MCU's
actual threshold, sampling latency, load transients and 3V3 ride-through require
simulation and bench testing. Even at6 V loaded input, loaded-dropout qualification
is open because AP63201 only gives typical switch resistance; never label that
corner guaranteed from the nominal duty calculation.

**GAP-3, LDO thermal (Calc / Inference):** allocated 460 mA output, extreme
rail tolerances and 4 mA quiescent draw give 0.406177 W. U401 pad 11 is
1.2 × 2.0 mm, centred at (27.6,13.6), and now has two GND vias at
(27.3,13.6)/(27.9,13.6), 0.5 mm ring / 0.3 mm drill. These two vias require
resin filling, copper capping and planar VIPPO; the maker's paste windows stay
unchanged. Fabricator acceptance is pending. TI TPS7A91 §7.1.4 / layout guidance
calls for thermal vias; its 62.5°C/W JEDEC thetaJA is not this board's thermal
resistance. Retain 80–110°C/W as a conservative **Inference**, without claiming
that the vias establish or improve that number. Junction estimate is
102.494–114.679°C at the 70°C bay ambient, below 125°C recommended maximum;
at 85°C it is 117.494–129.679°C, an unqualified unshaded sensitivity. Full-load
thermal measurement remains required; the inferred theta ceiling for 125°C at
70°C is 135.409°C/W. Measure the complete power knot and qualify the actual
fabricated via process; do not substitute an unfilled hole or shrink the paste.
Buck thermal qualification remains open:89°C/W is a reference-board metric,
maximum MOSFET resistance and switching loss are not specified, and80% conversion
efficiency is an input-current budgeting assumption rather than a guarantee of
acceptable junction temperature. Test the complete power knot under full load.

## Off-state and USB back-feed

**AUD-8 (historical for the GPS and radio; current for the camera, R18-PWR-03).** On the current board U411 / U421, U412 / U422 and C440 / C443 / C450 / C453 no longer exist (always-on ports); only the camera's U12 (TXU0202), U13 and C92 / C93 remain. As recorded for the intermediate boards: U411/U421 TXU0202DCUR C5186957 used main 3V3 on both VCCA and
VCCB. U412/U422, R443/R453 and C441/C442/C451/C452 are removed. C443/C453 remain
100 nF local VCCB bypasses, retagged to 3V3: [TI TXU0202 §12.1 and Fig12-1](https://www.ti.com/lit/ds/symlink/txu0202.pdf)
recommend a local 0.1 µF at each supply. C440/C450 remain the VCCA bypasses.
Camera U13 TPS70933DBVR and C92/C93 remain because PORT_5V3 can exceed the
TXU0202's 5.5 V maximum supply. Port ESD returns to GND. EN/OE default low;
firmware holds OE low whenever its peripheral supply is off, and lowers OE before
EN. Accepted: incorrect OE can feed an unpowered external module a few mA through
1 kΩ. Partial-power isolation still requires the installed-module bench test.

TPS2553 specifies≤1µA reverse leakage at OUT6.5 V/IN0 V **at25°C only**.
It is not an instantaneous ideal diode: powered reverse detection can take7 ms
and requires up to190 mV difference. EN input leakage is±0.5µA and FAULT off
leakage≤1µA under their stated electrical-table conditions. The datasheet does
not separately guarantee every unpowered EN/FAULT combination across temperature.
Radio USB-powered/board-off and board-on transitions must be measured; the reverse
transient can charge the shared rail before cutoff. Camera supply back-drive remains
prohibited. Small leakage does not establish a zero-voltage unpowered rail without
its discharge impedance. No unconditional back-feed immunity claim is made here.

**Back-feed through an ENABLED switch (R3-SAF-02).** TPS2553's reverse comparator
trips only when OUT exceeds IN by95/135/190 mV, after3/5/7 ms (SLVS841F §7.5 p7,
§9.3.2 p14); with r_DS(on)≤135 mΩ that is≥0.7 A of reverse current before any
blocking. A self-powered or USB-powered GPS (J410), radio (J420, LR900-F has its
own USB-C) or camera (J9) on an enabled port therefore back-feeds GPS_4V8 /
RADIO_4V8 → PORT_4V8 → U401 (TPS7A91 states no reverse-current behaviour:
Inference) → PORT_5V3, and CAM_5V → PORT_5V3, then through U400's high-side body
diode (Inference) into RAW_PROTECTED. From there U11 can keep VLOGIC and the MCU alive with the external screw
switch open. The single-switch implementation replaces the former automatic R122/R123 divider with PC1
(ACT_EN_MCU) through R122 1 kΩ and R123 2 kΩ to GND (100 kΩ before the round 18 fix pass). The pyro load switch is off during MCU reset or loss of
3V3, but a still-running MCU can retain its deliberate enable: no physical ARM break remains. Treat the pyro
channel as live while any source powers the board. Connect the e-match only with the screw switch off and no USB
or self-powered port attached; perform bench work from USB with the e-match disconnected. Firmware drops UART
OEs and port ENs on a VLOGIC sag, clears PC1 and PE4 on every safety fault, and must never fire before a confirmed
accelerometer-plus-barometer launch. No separately wired switch-position input exists, so firmware cannot promise
to detect a switch opening that a back-fed supply hides. The installed dummy-load bench test measures the behavior
with each port independently powered and enabled. A passing CAD gate does not verify these firmware or transient
behaviors (D-SS-01).

The camera back-feed prohibition (REQUIREMENTS
"Camera") extends to J410 and J420.

**Port UART ESD (R3-MCU-05; current direct-port amendment).** D400/D401, D410/D411, D420/D421 and D440/D441 (and, since D-R24-11, D402 at J400.2; see the round 24 amendment) are ESD103-B1-02EL
(shared code with R9's RF clamps): ±15 V working, clamping at about20/36/48 V at
1/8/16 A TLP (Infineon ESD103-B1-02 datasheet; R3 review read rev 1.3 Tables 3/5
p6, R7 pass 2 v2.0 Tables 2/4/6). That clamp is far above a 3.3–5 V I/O, so the
diode limits the surge without establishing a safe receiving-pin voltage.
Only the camera retains 1 kΩ resistors into TXU0202 U12's B side, with the MCU
behind its A side (TI SCES942A §7.2 p5 gives ±2500 V component HBM).
GPS, radio and AUX instead connect directly through R440 / R441 (PD9 / PD8), R450 / R451 (PB12 / PB13) and
R470 / R471 (PC7 / PC6), with D440 / D441 the AUX clamps (R20-MCU-04). There is no translator or additional rail clamp on
those six paths.
Neither the resistor nor a component HBM rating demonstrates installed cable
ESD survival or compliance with ST's pin/injection limits. Handling protection
is an Inference; installed waveform/ESD qualification remains open and no
system-level IEC 61000-4-2 rating is claimed. Connect unpowered harnesses on an
ESD-safe bench, with no independent module power.

**Camera supply loop split, historical GH-era version (R3-PWR-08; superseded, R18-PWR-03).** The camera's
≥5.03 V at 1 A rests on a ≤150 mΩ supply-plus-return loop (table above). Of it,
the board-end GH contacts may take up to 2 × 50 mΩ = 100 mΩ (JST eGH, maximum after
test) and the board copper CAM_5V / GND about 14 mΩ (R3 review figure, not
re-solved here), leaving **≤36 mΩ for both harness conductors and any camera-end
termination**. At about 0.134 Ω/m for 26 AWG (GH's largest wire; Inference,
typical annealed copper) that is about 0.13 m of conductor in total, roughly a
6–7 cm two-wire lead with a soldered camera end. A longer lead or a camera-end
connector needs a measured camera minimum below 5 V, a lower camera current or a
different supply arrangement (owner / harness item); measure the installed loop
four-wire.

**Camera supply loop split, current DB125 version (R18-PWR-03; native DC solve).** The supply side of the board copper is PORT_5V3 from C403.1 to U402.1, 36.07 mΩ, plus CAM_5V from U402.6 to J9.1, 17.06 mΩ: 53.13 mΩ in total (the GND return was not solved; three planes, small). Of the ≤ 150 mΩ supply-plus-return loop this leaves about 97 mΩ for the DB125 contacts, the harness and the camera-end termination. The GH figures above (2 × 50 mΩ contacts, about 14 mΩ of board copper) no longer apply; measure the installed loop four-wire.

**LR900-F maker figures (R3-REQ-08/09).** MicoAir's LR900 manual (URL above,
updated 2026-10-25): LR900-F 27 dBm (500 mW) transmit, **maximum average power
consumption 1 W**, 4.5–5 V supply, operating band **890–915 MHz** with manual
channels 0–25 for 890–915 MHz: only channels 12–25 (902–915 MHz) lie in the US
902–928 MHz band, and the FHSS channel set and its restriction are not documented.
Configure manual channels 12–25 only, or confirm the FHSS set with MicoAir before
flight (regulatory: Inference). R420 no longer exists (always-on ports). The 1 W
average is about 0.21 A at 4.8 V against the 0.30 A radio allocation, but the transmit peak is unpublished: measure the
radio's supply current at full power on J420 before flight.

## Battery-lead break ride-through (REQUIREMENTS F6; R3-PWR-02)

C84 sits on VLOGIC after U11. In a battery-lead break it also back-feeds
RAW_PROTECTED through U11: TPS2121 blocks reverse current only above IRCB
0.2/1/2 A (SLVSEA3F §7.5 p8), and the port buck U400 on RAW_PROTECTED has EN tied
to VIN, so it keeps drawing until RAW_PROTECTED collapses; firmware shedding of the
ports cannot act in time (TPS2553 turn-off up to3 ms, SLVS841G §6.5 p7). Energy
from 7.4 V, constant-power loads, no credit for RAW_PROTECTED, C6 / C7 capacitance
or for U11 blocking (Calc / Inference; `parts_budget.json`
`battery_break_ride_through_ms`; each case includes an explicit 16.93 mW constant allowance for R92 at 7.4 V and minimum resistance, D-OA-05):

| Case (load at the converter inputs) | C84 300.8 µF, to 3.5 V / 3.8 V | C84 470 µF, to 3.5 V / 3.8 V |
|---|---|---|
| (a) ports off, logic shed: 0.62 W retained + 0.1 W idle port chain | 8.7 / 8.2 ms | 13.6 / 12.9 ms |
| (b) ports off, no shed: 0.6–1.4 W logic (`pass1_electrical.md` §4.4, no RF) + 0.1 W | 4.2–8.9 / 4.0–8.5 ms | 6.6–13.9 / 6.2–13.2 ms |
| (c) camera 1 A, radio, GPS on: 9.2–10.1 W ports + 0.6–1.4 W logic | 0.55–0.65 / 0.53–0.62 ms | 0.87–1.02 / 0.82–0.96 ms |

3.5 V is the logic floor used since R7; 3.8 V is the AP63203's minimum input
(DS41326 p4). Case (a) assumes shedding from the first moment (detection latency
not credited). R9 had the same camera-on limitation (about 1–3 ms, its F6 text);
R10 adds the radio and GPS to it.

**OQ-5 hardware option (not adopted by the owner, 2026-10-28):** an AP63201 EN divider
from RAW_PROTECTED to GND in place of the EN–VIN tie (DS41326 p10 eq. 1–2), on
existing BOM values R5 47 kΩ 1% (C25819) / R6 10 kΩ, turns the port buck off at
VOFF 5.73–6.30 V (6.01 V typical; VEN_L 1.05–1.15 V, EN currents typical) and back
on at VON 6.49–6.94 V, which puts this file's own rule "shed all port enables
before RAW_PROTECTED falls below 6.2 V" into hardware. In a lead break with all
ports on, C84 then carries the ports only from 7.4 V down to VOFF (0.29–0.53 ms at
the lowest VOFF) and the logic alone below it: ride-through at least 4.6 / 7.2 ms
with shedding and 2.3 / 3.7 ms without (300.8 / 470 µF, to 3.5 V;
`parts_budget.json` `option_oq5_*`). Cost: two 0603 parts on existing codes, a
0.13 mA divider load, a placement and routing change at U400.2; the ports turn off
whenever a four-servo stall pulls the pack below about 6 V (already accepted for
the firmware rule).

## Local lands, envelopes and assembly

All models are small generated fit envelopes, not vendor STEP models. Their paths
use `${KIPRJMOD}/kilib/rocket.3dshapes`. New lands have no clearance overrides.

| Part | Source and local land | Qualification status |
|---|---|---|
| DB125 black C52993880; green C466970 | [DORABO supplier-linked T0-1 drawing](https://atta.szlcsc.com/upload/public/pdf/source/20251124/8C215F69B14C8E54AE0F8E5023D4AE9F.pdf):3.5 mm pitch,7.0×7.4×8.6 mm body,28–16 AWG,10 A UL/13.5 A IEC,0.2 N·m,4–5 mm strip. Pads±1.75 mm,Ø1.9 copper/Ø1.3 drill. Bodyy−3.9…3.5; wire-entry+y. | T0-1 recommendsØ1.2 holes; the [older maker drawing](https://www.nbdibo.com/wp-content/uploads/2020/06/DB125-3.5-XXP-C-S.pdf) was reported as1.3 in round1. CurrentØ1.30mm nominal holes do not close insertion/process extremes; use the round15 allocation above. Nominal copper gap1.6 mm and radial annulus0.3 mm are calculated, not actual manufactured measurements. Final board must hold≥1.5 mm including tracks; no role alias inherited from R9. Envelope7.3×7.7×8.9 includes general tolerance. J1 peak≈6 A is below10 A; validate installed wire/contact heating. |
| GH2 C161690 | [JST eGH pp2–3](https://www.jst-mfg.com/product/pdf/eng/eGH.pdf):1.25 mm pitch; pads0.6×1.7 atx±0.625,y1.95; tabs1×2.8 atx±2.475,y−1.4. | Same frame as GH4; mechanical pads unnamed. Body5.75×4.25, mated height7.3 mm, further3 mm wire allowance belongs to fit gate.1 A withAWG26; contact50 mΩ maximum after test. Harness allocation must include both supply and return contacts. |
| GH4 C161692 | Existing M3_GH_BM04B_GHS_TBT land/model, same JST drawing. | Used for camera/GPS/radio; keyed connectors remain electrically different, require labels and harness pin check. |
| TPS7A9101 C2878140 | TI DSK0010A:0.6×0.25 pads,0.5 pitch,row centres±1.15; pad11 1.2×2.0. | Maker land, thermal-pad paste split to the maker's84%. GAP-3 adds two 0.5/0.3 GND vias in pad11, resin-filled/copper-capped planar VIPPO; original paste windows unchanged (thermal estimate above). Body maximum2.6×2.6×0.8 mm. |
| C84 MA25V470M8x10 C46550466 | [MA-series supplier datasheet](https://atta.szlcsc.com/upload/public/pdf/source/20260306/24758A4FC016E80367B87853635CDCC1.pdf), logo JIERRUI/深圳市捷而瑞:470µF25 V,25 mΩ/100 kHz,4.1 A ripple/105°C; tolerance±20%, endurance±20% of initial andESR≤150%. Base8.3±0.2, lead gap3.1±0.2,width0.8–1.1, height10±0.5 plus0.3 mm projection conservatively. | Inference: derived3.5×1.7 pads at±3.25 give3.0 mm copper gap and toe allowance. Envelope8.5×8.5×10.8. Not a maker-recommended land: datasheet supplies no land/reflow profile. GAP-4: manually fit AFTER ALL REFLOW; do not expose this part to an unprovided reflow profile. Keep fitted BOM/CPL identity/polarity, with manual-fit order remarks. Qualify the hand-solder process and first-article capacitance/ESR, polarity and height before release. |

C84 conservative beginning/end-of-life capacitance is470×0.8×0.8=300.8µF,
ESR at most37.5 mΩ under the specified endpoint test. Neither number supplies an
unpublished cold ESR bound. R10 hold-up simulation must use these values and a
separately sourced temperature factor; nominal470µF is insufficient.

Supplier/EasyEDA API calls for the four new package codes returnedHTTP403 in this
session. Their pad-number/orientation check remains open; no CPL rotation correction
has been guessed. Local maker geometry was parsed and checked using KiCad. Final
BOM/CPL gate must fetch each actual supplier package and check numbered pads and
GH mechanical tabs.

**CPL orientation items to confirm in JLC's placement preview (R4-BOM-01 to -03;
`tools/jlc_corrections.json`, residuals are the worst pad distance between our land and the EasyEDA
footprint):**

- **L400 (C1329837, SRP5030T-6R8M, land `M3_SRP5030TA` at (24.2, 5.55), rotation 0):** EasyEDA has no entry for
  C1329837, so the JLC orientation comes from the proxy C189932 (SRP5030T-100M, the same SRP5030T package): rotation
  correction 0, offset 0, residual 0.05 mm since the round 18 fix pass (0.15 mm before). The part is symmetric (two terminals, no pin-1 mark that matters
  electrically), so a 180° error is harmless electrically; the land is now Bourns' SRP5030T p1 recommended layout (2.0 × 1.8 mm pads at ±2.25 mm, generated by `r10_parts.srp5030t()`, D-R18-08;
  the proxy supplies the numbering, not the dimensions).
- **U411 / U12 / U421 (TXU0202DCUR C5186957, land `M3_TXU0202_DCU`, top, rotation −90 on the board):** correction
  180°, offset 0, residual 0.147 mm. Pin 1 on JLC's footprint is matched by pad
  geometry, not by the mark: confirm pin 1 in JLC's preview on all three before paying.
- **C84 (C46550466, MA25V470M8x10; historical position (38.5, 74.0), rotation 90; it is now at F(27.5,78.5), 90°, and since the round 18 fix pass it is on the owner BOM, not in the JLC CPL):** correction 0, residual 0.045 mm. The board has
  + on pad 1 (VLOGIC at (38.5, 77.25)) and − on pad 2 (GND at (38.5, 70.75)); the polarity in JLC's CPL / preview
  is not confirmed (the MA-series datasheet gives no land, see the parts table above): confirm + on the VLOGIC pad in the
  preview, and check the fitted part's polarity stripe on the first boards (ORDERING §8). `parts_stock.json` is a dated component snapshot, not a final
BOM stock gate. Camera ILIM resistor R430 is now C2999509 (FOJAN FRC0603F2262TS): 84,923 in stock, minimum 1 (JLC, 2026-10-30T23:50:54Z); the C185349 it replaced had 17 in stock against a 3,610-piece minimum purchase
(JLC, 2026-10-27). Recheck the actual quantity before ordering.

## Servo-reference return and mechanical mass

The adopted O6 harness topology is a pack-negative star: every servo has its own
paired positive/negative motor lead directly to the pack. Each J122 reference wire
returns to the pack star, **not to the servo's motor-negative terminal**. Keep motor
return contacts separate from board-reference contacts. If their finite star
transfer resistance is≤1 mΩ at7.68 A, the potential spread is≤7.68 mV. With four
reference branches each≥50 mΩ, an intentionally conservative independent-branch
sum is4×7.68 mV/50 mΩ=0.6144 A through the board, ignoring the additionalJ1 return
impedance. Qualify board/J122 reference copper for1 A; record≤0.62 A residual under
these conditions. Four-wire measurements must establish both transfer resistance
and minimum branch resistance on the assembled harness. Do not obtain the latter
from a guessed wire length. Strain relief and star attachments are bench acceptance
items. An open reference branch must leave the servo's direct motor ground intact.

If reference leads instead join the negative at each servo,50 mΩ motor return and
130 mΩ reference return permit2.13 A through the board at four stalls; shorter
reference leads can approach the whole7.68 A. That alternative is not the accepted
R10 harness topology. This analysis does not claim zero servo return.

`masses.json` explicitly lists R10 body and additive plug/local-wire masses. These
are conservative **Inference** allowances, not manufacturer or measured masses.
A plate result using them remains conditional on weighing the populated assembly
and supporting the long leads independently. Four corner mounting alone and bore
fit must be established from the final board and actual mated plugs.

## Round-5 power and pin records (R5-PWR-01 … -04, R5-MCU-04 / -05)

Figures are Calc from the netlist values unless marked; datasheet figures marked "reviewer" are the round-5
reviewer's readings and were not re-read from the PDFs in this pass (Inference until checked).

- **U9 OVLO pin range (R5-PWR-01).** U9.2 sits on R82 2 MΩ / R83 280 kΩ (ratio 280 / 2280 = 0.1228). The pin leaves
  the recommended 0.5–1.5 V range (reviewer, TPS259470L) above an input of 1.5 / 0.1228 = about 12.2 V, reaches
  2.44 V at the 19.9 V D8 clamp, and would reach the 6.5 V absolute maximum (reviewer) only at 52.9 V, far above the clamp.
  Above 12.2 V the part is in the over-voltage state it is there to detect; the out-of-range pin in that
  fault state is recorded and accepted (Inference: behaviour of the pin outside its range is not specified).
- **TP89 on U9 ILM (R5-PWR-02).** TP89 is the BAT_ILIM node (U9 pin 9, R84 750 Ω to GND; C81 4.7 nF is on BAT_DVDT, pin 7), an analog monitor that the
  maker marks "do not leave floating" (reviewer). Bench probing is high-impedance only; never load, short or drive
  it (ORDERING §8 bench gates). Loading it changes the current limit and the monitor reading.
- **AP63201 quiescent current (R5-PWR-03).** 258 µA per the Diodes AP63200/1/3/5 datasheet (DS41326; reviewer); LCSC's
  22 µA is the AP63200 / 63203 / 63205 figure. No idle figure in this directory used 22 µA; the 11 mA
  "quiescent, divider and bleeder" allowance in the all-ports-shorted budget covers 0.258 mA of it with margin (Calc).
- **Low-pack dropout (R5-PWR-04).** The AP63201's loaded dropout is typical-only (already stated above under
  "Inference, stall input"); ORDERING §8 adds a bench step with the port rails read at a 6.0 V loaded battery.
- **PA6 (VLOGIC_SENSE) single-fault pin damage (R5-MCU-04).** The divider is R60 100 kΩ (VLOGIC) / R61 10 kΩ with C60
  10 nF, and there is no 4.7 kΩ pin resistor. A shorted R60 puts VLOGIC (up to RAW_PROTECTED, 8.4 V nominal full
  pack) straight on PA6. For this FT_a pin used by the ADC, VIN maximum is **4.0 V**, with positive injection
  allowance **0 mA** ([DS12110 Rev11](https://www.st.com/resource/en/datasheet/stm32h743vi.pdf), Table109 pp207-208
  notes3-5 and Table110 p208; R10-MCU-01). The digital FT ceiling is min(min(relevant supplies)+4.0 V,6.0 V),
  hence 6.0 V with powered 3.3 V supplies; pulls must be disabled above 4.0 V. The former 7.3 V claim omitted
  both limits. Normal 8.4 V /11 = 0.764 V remains below 4.0 V (Calc); a shorted R60 still overstresses PA6.
  An open R61 can also raise the steady-state node toward VLOGIC through R60 (Inference; leakage dependent).
  Single-fault cases, pin damage;
  listed as an owner deviation by the orchestrator. Mitigation none on the board.
- **PB1 (CAM_5V_SENSE) single-fault pin damage (R5-MCU-04).** The divider is R104 10 kΩ (CAM_5V) / R105 1 kΩ with C94,
  and PB1 has no 4.7 kΩ pin resistor. An open R105 puts CAM_5V (5.456 V nominal) on PB1 through R104 10 kΩ; PB1
  is a TT_a pin with a 4.0 V limit (reviewer) and the fault current is about 0.15–0.19 mA ((5.456 − 4.0) / 10 kΩ to
  (5.456 − 3.56) / 10 kΩ, depending on where the clamp conducts; the reviewer's figure is 0.19 mA). Single-fault
  case, pin damage; listed as an owner deviation by the orchestrator.
- **VBUS_SENSE threshold (R5-MCU-05).** PC8 = VBUS / 2 (R9 1 kΩ / R110 1 kΩ 1 %). At 4.4 V VBUS the node is 2.20 V,
  below VIH = 0.7 × VDD = 2.31 V at 3.3 V (VIH as reviewer's figure, DS12110 row not re-read): VBUS detection needs
  VBUS ≥ 4.62 V (2 × 2.31 V) at VDD 3.3 V. A host or charger within USB's 4.40–5.25 V band can read "absent".
  Firmware must not treat a low PC8 as "no USB" in a safety decision (binding note).
- **LSEON (R5-MCU-02).** PC14 is OSC32_IN and drives BUZZ_DRV through R162; VBAT is tied to 3V3, so a stray LSEON set in
  the backup domain survives NRST and would load the buzzer node: LSEON stays 0 and the backup domain is never
  set up for the LSE (binding note).

**Current USB-only calculation (round 10):** native R85 66.5 kΩ with ±2% resistance envelope gives
347.7–453.0 mA. Nominal 514.1 µF to 4.7 V requires 2.416 mC, or ideal no-load 5.33–6.95 ms. Actual host /
startup load remains unqualified; a 450 mA rating alone is insufficient. The 355–445 mA / 5.8–7.2 ms / ≥450 mA
statements in the historical sections below are superseded for current R10. This is calculation, not USB compliance.

## Round-6 records (historical pre-AUD hardware; Calc unless marked)

- **USB-only attach (R6-PWR-02).** With only USB-C connected, VBUS feeds VLOGIC through U10 (TPS2553, current limit
  355–445 mA as the round-6 reviewer reads it; ILIM resistor and datasheet limit not re-read here) and U11 behind it:
  C84 470 µF, C6 and C7 22 µF each and C99 100 nF are charged through that limit. With the load ignored, the charge
  of about 514 µF to 5 V (2.57 mC) takes 5.8 ms at 445 mA and 7.2 ms at 355 mA (dV/dt about 0.7–0.87 V/ms; Calc).
  Bench: attach USB alone and measure the VBUS current and dV/dt, and the 3V3 start-up. USB-only programming or logging
  needs a host that allows at least 450 mA (Inference: a USB 2.0 port allows 500 mA after enumeration, 100 mA before; the
  board's draw with the MCU running and the ports off is not measured).
- **Q120 / Q121 turn-on time (R6-PWR-03).** The gate network is R120 100 kΩ (gate to source, RAW side) in parallel with
  R121 10 kΩ (gate to Q122's drain) charging C120 2.2 µF: R120 ∥ R121 = 9.09 kΩ, tau = 9.09 kΩ x 2.2 µF = 20.0 ms.
  Q120 / Q121 are fully enhanced about 22 ms after Q122 turns on (1.1 tau: Vgs about 67 % of its final value, which
  is 0.909 x RAW, so about −4.5 V at 7.4 V; threshold and Rds(on) against Vgs not re-read; Calc). This supersedes the
  microsecond-scale switching figures of R9's servo-power path for R10, where Q120 / Q121 only switch the pyro bus:
  RAW_ACT (TP120) rises over tens of milliseconds, so a gate or RAW_ACT reading taken sooner than about 50 ms after the
  enable is not valid (Inference: 50 ms is about 2.5 tau).
- **PORT_5V3 In2 band narrowest point (R6-PWR-01).** 1.20 mm at x about 30.25 (a via clearance notch; round-6
  reviewer's measurement, not re-measured here); `tools/ipc2152.py` internal fit, 1.20 mm, 2.02 A: 8.5 °C (re-computed),
  so the earlier 1.49 mm / 6.7 °C figure is superseded.

## Round-7 records (R7-PWR-02, R7-BOM-03, R7-MCU-03 / -04; Calc unless marked)

- **USB attach inrush (R7-PWR-02).** Behind U10 sit C84 470 µF, C6 / C7 22 µF each and C99 100 nF, about 514 µF; charged to about 4.7 V that is about 2.4 mC, which at U10's 355–445 mA limit (round-6 reviewer's reading, not re-read) takes about 6 ms. USB 2.0's attach allowance of about 10 µF (50 µC at 5 V) is quoted from memory of the specification (**Inference**, not re-read), so the board is about 48× over it. USB-only attach is host-dependent: test against a current-limited hub and record the hosts that fail (ORDERING §8 bench gate).
- **Camera ILIM fallback (R7-BOM-03).** TI SLVS841F (revision F, August 2016), equation 1, read in this pass: IOSmax = 22980 / RILIM^0.94 mA, IOSnom = 23950 / RILIM^0.977, IOSmin = 25230 / RILIM^1.016 (RILIM in kΩ, 15–232 kΩ). With RILIM ±2 % (1 % initial plus 1 % temperature, as the camera bounds above): 22.6 kΩ (R430, C185349) gives 1.041–1.249 A (reproduces the record above); a **22 kΩ** resistor (C31850, basic; code and value as the reviewer gave them, **not checked on LCSC here**) gives 1.070–1.282 A. The camera-short case with the other two ports at their allocations rises from 1.711 A to about 1.744 A and the all-ports-shorted draw from 2.022 A by about 0.033 A. A fallback only, **not adopted**: it needs the port budget and U400's peak-current check redone first. R430 itself: 17 in stock, 3,610-piece minimum purchase (JLC, 2026-10-27); confirm acceptance in the quote.
- **W25Q128JV erase times (R7-MCU-04).** Winbond W25Q128JV Rev I (08/23/2021), AC characteristics (erase and program), read in this pass: sector (4 KB) erase 45 ms typical / 400 ms maximum, 32 KB block 120 ms / 1,600 ms, 64 KB block 150 ms / 2,000 ms, chip erase 40 s / 200 s, /CS high to next instruction after suspend (tSUS) 20 µs. The earlier "about 45 ms" was the typical value only; the maximum is 400 ms.
- **IWDG period (R7-MCU-03).** LSI 29.76–33.60 kHz (DS12110 Table 39 as the reviewer read it; **not re-read**, ST's server refused the download in this pass) gives a nominal 32 ms setting a worst case of about 34 ms (32 ms × 32 kHz / 29.76 kHz ≈ 34 ms with a 32 kHz-based reload), inside F6's 50 ms target. A started IWDG cannot be stopped; a loader jump after it starts lands in the application about 32 ms later with BOOT0 low (**Inference**, AN2606 not read).
- **PA15 reset state (R7-MCU-01).** PA15 resets to JTDI with the internal pull-up, not analog (**Inference**: the reviewer's reading of DS12110 / RM0433, not re-read); firmware sets it to analog explicitly.

## Round-8 records (historical pre-AUD hardware; records only, board unchanged)

- **GPS UART level (R8-MCU-02).** HGLRC's M100 Mini page gives the supply as 3.3–5 V and does not specify the UART
  logic level. **Inference:** a u-blox M10 part with 3.3 V I/O; the J410 translator (TXU0202, B side on GPS_IO_3V3
  from U412, enabled with GPS_4V8)
  tolerates a B2 input up to 5.5 V, so a 3.3 V or a 5 V device both stay inside its rating. Measure the module's TX
  high level before flight; do not treat the level as qualified.
- **GPS cable (R8-MCU-02).** The GPS's own cable is SH1.0-4P (plan, as the owner's list gives it; not re-checked
  against HGLRC's drawing here), while J410 is a JST GH 1.25 mm 4-position header: a **SH1.0-to-GH1.25 harness
  adapter** is needed, with the pin order of ORDERING §8 "Camera harness and port cables" checked end to end.
- **DB125 height (R8-MEC-05).** DORABO T0-1 drawing (read 2026-10-28, link in the "Local lands" table above): body
  height 8.60 mm with the drawing's general tolerance ±0.30 mm for 6–10 mm (so 8.9 mm maximum, the envelope used),
  body width 7.40 mm, pin length below the body 3.90 mm. A first-article caliper check of the seated terminal remains
  advised.
- **Port UART break (R8-MCU-01).** With a port's OE high and its device unplugged or unpowered, the TXU0202's 5 MΩ
  input pull-down holds the MCU RX low, a continuous break (Inference from the pull-down, not measured): the firmware
  obligation is in the binding note and M3_R10 "Firmware".

## Historical R92 discharge change before round 9 (2026-10-28)

OQ-2's requalification must include U9 OUT as well as IN: below -10 C, TPS25947's input limit is
`max(-15 V, VOUT - 21 V)` (TI SLVSFC9C p. 7). R92 changes from 10 kohm to **3.3 kohm, 1%, 0603** on the same land
and RAW_PROTECTED-to-GND nets. This reduces retained output voltage after unplugging without adding a component or
changing the pack-change waiting rule. U11's reverse-current threshold is not treated as an ideal blocking diode.

The replacement is **UNI-ROYAL 0603WAF3301T5E, C22978**. The
[LCSC part specification](https://www.lcsc.com/product-detail/Chip-Resistor-Surface-Mount_Uniroyal-Elec-0603WAF3301T5E_C22978.html)
gives 100 mW, 75 V, +/-1%, +/-100 ppm/C and -55 to +155 C; the same 0603 package family preserves the existing land.
[JLC's part page](https://jlcpcb.com/partdetail/C22978) and the exact-code public lookup on 2026-10-28 identify it as
Basic, with 5,345,859 available and a 1-piece tier of USD 0.0022. This adds one Basic code, no extended code; refresh
the complete BOM cost/stock evidence before ordering. The fields in `circuit.json` agree on this exact part.

At 8.5 V the nominal loss is 21.89 mW (14.67 mW more than 10 kohm). The hot-plug record includes the board's
capacitor inventory, a doubled-C84 sensitivity and the other explicit model assumptions. With all 1675.3395136 uF
of that conservative inventory initially at 8.5 V, R92 alone at its +1% tolerance and +0.65% temperature corner
(3354.6645 ohm) gives 5.954856276 V after two seconds in the common-node model. No load current or divider bleeds are
credited. These are CAD estimates, not a guarantee of C84's unprovided capacitance-versus-temperature curve or
of arbitrary converter reverse-energy behavior. The existing simultaneous U9 IN / OUT reverse-plug bench
qualification remains mandatory.

## Historical R166 damper change before round 9 (2026-10-28)

OQ-2's model selects **0.36 Ω, 1%, UNI-ROYAL 25121WF360LT4E / C168925** in place of 0.33 Ω. The preliminary
feed with 0.33 Ω reaches -15.100485 V at the cold/tolerance corner; 0.36 Ω passed that model's 2304 cases.
The preliminary local-shunt approximation is superseded by D-OA-07: C88 is now fed before U9 and its actual
trace path stays in the model. The historical production-bound model results at that stage recorded
all 2304 required cases passing on board `3b960b46…`, with -14.497874 V minimum and
8.525257 V/µs maximum falling slew. Its assumptions in `hotplug.md` remain simulation inferences.
[LCSC's exact-part page](https://item.szlcsc.com/180309.html) confirms the identity and 2512 package.
[UNI-ROYAL SMD-SP-001 V10, pp. 4–6](https://www.uni-royal.cn/en/images/userfile/file/1753752986c56505e6d9ab55c7.pdf)
gives 6.35 ±0.10 × 3.20 ±0.20 × 0.55 ±0.10 mm, matching the existing family and land; 1 W through 70 °C,
derating to zero at 155 °C; and ±800 ppm/°C below 1 Ω. Over -40…85 °C, tolerance and temperature give
0.3378672–0.3825072 Ω, swept independently of the capacitor and copper corners. `circuit.json` binds the new
value, order code and maker part without changing nets or footprint. Refresh BOM stock and cost before ordering.

**Pulse qualification remains open.** The maker's ordinary thick-film specification gives a five-second overload
test at 2.5 times sqrt(P×R), or 1.5 V for this value at the 1 W rating; it supplies no microsecond pulse curve.
The absolute 200 V family ceiling is not the low-value resistor's allowable continuous voltage. That historical sweep
gives 504.292318 W peak and 2.888490051 mJ over 150 µs in different corners; separate half-step checks give
504.293235 W and 2.888489824 mJ. A low energy alone does not prove survival. Obtain maker confirmation for
that waveform or test repeated hot/cold insertions and resistance drift. This is a component-data/model update,
not a claim of measured pulse durability or board acceptance.

The historical final round-11 target PCB `0ad0135c…` has a separately bound 2304-case
sweep: R166 stress reaches579.049147 W and2.979359077 mJ in different corners;
the retained-output common-node estimate is5.877715489 V after two seconds with
1616.123714 µF. `hotplug.md` records that exact board, electrical/input/model hashes
and its native feed. These replace the older stresses only for that named board.
The historical intermediate `419a8f49…` run had the same stress figures under its
own binding; the target was re-extracted and the full sweep rerun. Both complete
builds/full gates pass with all 42 recorded generated file hashes matching. Neither calculation
qualifies pulse durability.
