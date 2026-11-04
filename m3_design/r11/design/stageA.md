# R11 stage A: parts and schematic (2026-11-02)

Stage A of `r11_plan.md` §4: R10's circuit, unchanged in nets and values (D-R11-01), regenerated as the R11
schematic with the R11 MCU package, 0402 passives and connectors. No board, placement or copper exists yet. Nothing
is committed or ordered.

## 1. What was built

| File | What it is |
|---|---|
| `design/r10_input/` | R10's 15 sheets, `schematic.net.xml`, DRU, project, lib tables, `m3.kicad_sym`, `pin_table.tsv` and `circuit.json`, copied from `m3_design/assembly_review` (commit `deb179e`); `manifest.json` holds their SHA-256s and those of the 89 R10 footprint / model files R11 may copy (left in R10's kilib). `r11_sch.source_check()` verifies all of them before every generation, check and library run. |
| `design/circuit.json` | The R11 change list: a catalog of 21 LCSC codes (Manufacturer, Manufacturer Part, footprint, datasheet) and 60 changed refs, each with its R10 footprint / code / value and the reason; the J9 pin map, U1's removed (VREF+) and added (PDR_ON) pins. |
| `design/pin_table.tsv` | R10's pin table (the reviewed function map, every R10 column verbatim) plus `r11_ball`, `r11_net` and `r11_ball_source`, and a PDR_ON row; written by `r11_sch.py --pin-table` from `r11_sch.BALL` and checked against it on every build. |
| `design/parts_r11.md` | Rating check of every package change, the parts kept in their R10 case and why, connector and wire-pad sources. |
| `design/jlc_r11_stock.json` | JLC query of every catalog code (2026-11-03T02:11:50Z). |
| `kilib/` | `m3.kicad_sym` (R10's symbols + `MCU_TFBGA100` + `CameraGH6`, GH texts on `PortTerminal` / `ServoTerminal`), `rocket.pretty` (the 40 R10 lands R11 uses, copied by hash, + 6 new), `rocket.3dshapes` / `generic.3dshapes` (their models + 5 new envelopes). Every path is `${KIPRJMOD}/kilib/...`. |
| `m3.kicad_sch` + 14 sheets, `schematic.net.xml`, `m3.kicad_dru`, `m3.kicad_pro`, lib tables | The R11 project (`r11_sch.py`). |
| `../r11_parts.py`, `../r11_sch.py`, `../r11_sch_check.py`, `../r11_build.sh` | Generators, gate and build (stage A wired; hooks for B–D). |

## 2. U1: STM32H743VIH6 TFBGA-100 ball map

Source: ST DS12110 Rev 8 (April 2021), https://www.st.com/resource/en/datasheet/stm32h743vi.pdf, read from the text
extract the R10 MCU review rounds used (page numbers from its page footers): Table 9 "Pin/ball definition"
pp. 64–88, Figure 6 "TFBGA100 pinout" p. 56. All 82 GPIOs, VBAT, NRST, VSSA, VDDA, BOOT0, both VCAPs (48 → F8,
73 → E7) and two VSS pins (49 → E4, 74 → E5) share a Table 9 row with their LQFP100 pin, so their ball is the
datasheet's (Datasheet). PC2_C / PC3_C (17 / 18 → E2 / F3) were checked on their split Table 9 rows. KiCad 10's
`STM32H743V_G-I_Hx` symbol (ST pin data) agrees on every ball and name (cross-check, not the source).

Differences between the packages and how R11 ties them:

| LQFP100 | TFBGA100 | R11 connection | Basis |
|---|---|---|---|
| VREF+ (pin 20, on 3V3A in R10) | no ball | none needed: VREF+ is double-bonded to VDDA (H1, 3V3A) in the package; keep the internal reference buffer disabled, as R10's firmware rule already requires | Datasheet: Table 9 note 7, p. 88 |
| PDR_ON tied to VDD inside the package | F7 PDR_ON | 3V3 (VDD): the power-down reset supervisor stays on, as on R10. PDR_ON low would disable it (p. 29) and VBAT operation (p. 37) | Datasheet: p. 23 note 4 |
| VDDLDO tied to VDD inside the package | F4 VDDLDO | 3V3 (on R10's VDD pin 100's net) | Datasheet: Table 9 note 8, p. 88 |
| no separate USB supply | F6 VDD33USB | 3V3 (on R10's VDD pin 75's net): VDD = 3.3 V, USB regulator bypassed | Datasheet: p. 18 (USB supplies on all packages except LQFP100), p. 27 (bypass when VDD = 3.3 V), p. 106 note 1 (VDD33USB must be connected) |
| 5 × VDD (11, 27, 50, 75, 100) | 3 × VDD (D2, F5, K1) + VDDLDO (F4) + VDD33USB (F6) | all 3V3 | paired by net only (11 → D2, 27 → K1, 50 → F5, 75 → F6, 100 → F4); Table 9 lists them on separate rows |
| 5 × VSS (10, 26, 49, 74, 99) | 5 × VSS (C2, E4, E5, E6, J1) | all GND | 49 / 74 share rows with E4 / E5; 10 → C2, 26 → J1, 99 → E6 by net |

Firmware consequences (Inference until RM0433 is read): the USB regulator must be configured for the bypassed
supply (VDD33USB from VDD), and the R10 rule never to write VREFBUF_CSR now rests on the package bond, not the board
tie. The R10 pin table's `source` column still cites LQFP100 pin numbers; `r11_ball` is the R11 key. The DS12110 Rev 8
device-summary table marks TFBGA100 "(7) under development"; ST sells the VIH6 and JLC stocks it (4355), so this is
a stale note in Rev 8 (Inference; a later revision was not read).

The decoupling capacitors stay on their nets (3V3: C8, C9, C13–C18, C23, C29, C90, C100, C460, C461; 3V3A: C10, C11,
C21, C22, C30–C32; VCAP1 C19, VCAP2 C20); which ball each one serves is a stage B placement decision. The BGA land is ST's
Table 219 recommendation (`parts_r11.md` §5).

## 3. Package changes

* U1 LQFP-100 → TFBGA-100 (C964146).
* 38 resistors and 13 capacitors 0603 / 0805 → 0402 (`parts_r11.md` §2–3), all JLC-stocked; JLC Basic codes where
  they exist (C25744, C11702, C4109, C25741, C25091, C25792, C307331, C15195; the first four and the last two are R10's
  own 0402 lines; C25790 and
  C25774 are "preferred" extended; C26960, C29381 and the four Yageo RT 0.1 % codes are extended).
* J410 / J420 / J440 → SM04B-GHS-TB, J9 → SM06B-GHS-TB, J122 → SM05B-GHS-TB, J400 → SM02B-GHS-TB, J1 / J121 → AWG 20
  plated wire pads (not in the BOM or CPL).
* Kept in their R10 case: R134, R166, R82, R83, R402, R92, R405, R150–R153, R164, C81, C85, C86, C87, C97, C98, C120,
  C126, C128, C19, C20, C22, C23, C28, C92 and all bulk parts (reasons in `parts_r11.md` §4).

The pin contract changes are exactly: U1 every pin re-keyed to its ball; U1.20 (VREF+) gone; U1.F7 (PDR_ON) added on
3V3; J9 pins 1–4 → 1+2 / 3+4 / 5 / 6. Every other (ref, pin, net) of R10's 216 parts is identical
(`r11_sch_check.py`: 670 pins, 216 parts).

## 4. JLC queries (2026-11-03T02:11:50Z, JLC component API as `tools/jlc_stock.py lookup()`)

Orderable = min(stockCount, canPresaleNumber) (R20-BOM-01, an Inference about JLC's fields). Demand is five boards.

| Code | Part | Per board | Stock / orderable |
|---|---|---|---|
| C964146 | STM32H743VIH6 | 1 | 4355 / 4043 ($8.8446) |
| C189893 | SM02B-GHS-TB(LF)(SN) | 1 | 19732 / 18278 |
| C189895 | SM04B-GHS-TB(LF)(SN) | 3 | 22206 / 20181 |
| C189896 | SM05B-GHS-TB(LF)(SN) | 1 | 31891 / 30827 |
| C133065 | SM06B-GHS-TB(LF)(SN) | 1 | 23350 / 22825 |
| C26960 | 0402WGF2262TCE (22.6k) | 1 | 1971 / 46 (thin) |
| C25790 | 0402WGF4703TCE (470k) | 2 | 171585 / 9302 |
| C852923 | RT0402BRD0780K6L | 1 | 3989 / 3449 |
| C705636 | RT0402BRD0756K2L | 1 | 5585 / 5429 |
| C852911 | RT0402BRD07750RL | 1 | 13022 / 11075 |
| others | 0402 resistors and capacitors | — | ≥ 50 000 orderable each |

Full rows (library type, price, datasheet link): `jlc_r11_stock.json`. Rejected for stock: RT0402BRD072ML (C5189456,
0 stock), RT0402BRD0749K9L (C852808, −10649 orderable), JST SM06B-GHS-TB C19626244 / SM05B C20089325 / SM04B
C20584968 (0 stock; the (LF)(SN) codes above are used), XYECONN GH clones (not genuine JST).

## 5. Gate results (this run)

* `r11_parts.py --check`: 46 footprints parsed with pcbnew; BGA, GH and wire-pad dimensions asserted; kilib current
  and nothing unlisted in it.
* `r11_sch_check.py`: ok; strict ERC 0 violations (every severity); 216 parts, 670 pins equal to R10's through the
  declared maps; pin table, R10 safety / port / SD contracts with ball keys, R11 connector and package contracts,
  terminal pin names, BOM grouping; DRU; deterministic regeneration of every sheet, netlist, DRU, project and lib
  table; fresh export of the supplied sheets; 54 / 54 seeded faults caught (R10's set adapted plus R11's: PDR_ON low /
  floating, VDDLDO floating, VDD33USB on VBUS, VDDA on 3V3, LQFP numbers left, VCAP swap, camera supply / GND on one
  contact, camera and port TX / RX swaps, pyro pads swapped, wire pads in the BOM / CPL, DB125 / LQFP lands left,
  disagreeing part fields, a changed value).

## 6. Verified and not verified

Verified (Datasheet / Calculation, this stage): the ball map against DS12110 Rev 8; the GH land against JST eGH p. 2;
the BGA land against DS12110 Tables 218–219; JLC stock and part identity of every new code; voltage and dissipation of
every moved passive (Calculation on R10's rail voltages); the schematic gates above.

Not verified (Inference or open):
* DC-bias capacitance of the moved 0402 capacitors (no maker curves read); the 85 °C derating shape.
* IPC-2222 values behind the wire-pad sizing and the AWG 20 strand diameters; the GH body depth.
* RM0433 USB-regulator and VREFBUF register behaviour for the TFBGA package.
* Everything physical: no board exists. The fire-budget, hot-plug, hold-up, IPC-2152, S-8 and fit figures are R10's
  and are not quoted for R11 until stage B–D re-run them (r11_plan.md §1).
* R10's sheet notes are carried verbatim except those rewritten for R11 (connectors, ball numbers, the package note on
  the MCU sheet); R10-specific narrative in them (for example R10 coordinates or "screw switch" wording for J400's
  external switch) is still R10's.

## 7. Open items for later stages

* Cost: the 0402 change adds extended lines (C26960, C29381, C852911, C852923, C705636, C190095; C25790 / C25774 are
  preferred) while removing R10's 0603 lines; the feeder-fee effect against the $84.41 cap is for stage D's cost run.
* C26960 (22.6k) has only 46 orderable: re-check on order day.
* `parts_r11.md` keeps R150–R153 in 0603 for the servo-lead fault; an owner decision could accept 0402 there.
* GH contacts are rated 1.0 A with AWG 26 crimps; the harness (AWG 26 leads to GPS, radio, servo signals and the
  camera) and its strain relief are stage E procedure items.
* The board DRU sets R11 floors (0.1 mm clearance / track, JLC 0.15 / 0.25 mm vias); net classes, stackup and
  via-in-pad policy for the BGA (JLC's filled-and-capped default from six layers) are stage B / C decisions.
