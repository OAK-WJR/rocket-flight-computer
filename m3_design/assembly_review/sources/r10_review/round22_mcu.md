# R10 round 22: MCU lens (Claude)

- Target commit `ec8cb98`.
- Board SHA-256 before and after: `5516eeec5b9e79b49d157146baf6f7652cc0fb0fdb9f1c3c13921c26f9d315a1` (unchanged).
- **Totals: 0 Critical, 0 Major, 1 Minor.** Machine-readable version: `round22_mcu.json`.

## Findings

| ID | Sev | Title | Key evidence |
|---|---|---|---|
| R22-MCU-01 | Minor | The diagnostics sheet note still has a 5.25 V camera example and a 19.9 V "TVS clamp" case on CAM_5V | The R10 camera supply is 5.456 V nominal, which reads 0.496 V; the note gives 0.477 V. The 19.9 V figure is D8's clamp (SMBJ12CA) on BAT_IN, ahead of U9's 9.77 V OVLO; CAM_5V has no TVS. A failed U400 reads ≤ 0.89 V. Text only. |

## Round 21 pass at U1

- **No pad net changed.** All 701 pad entries were compared on `0dc84776…` and `5516eeec…`: 0 net differences. Only R81 and C87 moved, and U1's 100 pads are identical.
- **No U1 net's copper changed.** The track and via diff touches only BAT_ENABLE, GND (the R81 / C87 stubs and vias that were removed) and 3V3 (the new U2.1 run).
- **Gate-net neighbourhoods are unchanged.** Every foreign-net approach under 1 mm, on all layers including fills, is identical on both boards for ACT_EN_MCU, ACT_EN, PYRO1_GATE_N, PYRO1_GATE, BAT_FAULT_N (PA5), LOGIC_SOURCE_ST (PA4), 3V3A and IMU_INT1.

## Checks

**Netlists and records**
- A fresh kicad-cli 10.0.7 netlist matches the committed `schematic.net.xml` and the board on 666 / 666 pins.
- DRC with schematic parity: 0 / 0 / 0. ERC: 0.
- `pin_table.tsv` `r10_net` matches the board on 100 / 100 pins, and so do the binding note's `u1_pins`.
- The binding note's board, netlist, pin_table and circuit hashes match the files.

**DS12110 Rev 8 pins and alternate functions**
- Table 9 confirms all 100 pin names.
- PD8 / PD9 are AF7 USART3 (p94). PB12 / PB13 are AF14 UART5 (p91). PC6 / PC7 are AF7 USART6 (p92). PE7 / PE8 are AF7 UART7 (p95). Each was read by column under the AF header.
- ADC channels: PC0 ADC123_INP10, PA6 ADC12_INP3, PC5 ADC12_INP8, PB1 ADC12_INP5.

**Port rules**
- **Port-UART enable (PA4).** U11's PR1 and CP2 are both grounded, so it runs in VCOMP mode (TPS2121 Table 9-3 p18): ST is low whenever the pack powers the output, which includes with USB attached. The PD8 / PB13 / PC6 rule appears in binding obligations 16 and 21 and in `port_states`.
- **Port map.** Obligation 3 keeps the port map and holds an unmapped port's USART off with its pins in analog mode.
- **Back-feed.** An FT pin allows Min(VDD, …) + 4.0 V, which is 4.0 V at VDD = 0, and takes no positive injection (Tables 119 / 120 pp212-213). A port device TX at ≤ 3.6 V through 1 kΩ is inside that.

**Gate networks**
- **PC1 → Q122.** R122 1 k series, R123 2 k pull-down and C123 10 nF gate–source. PC1 high gives 2.2 V at the gate. Against a 30 kΩ internal pull-up the gate sits at ≤ 0.218 V, under the AO3400A's 0.65 V minimum threshold.
- **PE4 → Q124.** R127 1 k at the pin, R126 220 Ω series, R128 10 k and C126 gate–source. The pull-up case gives 0.104 V, under the AON7524's 0.4 V minimum threshold. PE4 is active high.

**Sentinels**
- PE3, PE5, PE6 and PC4 have no net.
- None of the 31 no-net U1 pads has copper or fill on it.

**IMU and VREFBUF**
- **IMU_INT1.** It joins only U1.98 (PE1) and U4.4. INT1's default is "output forced to ground", and IF_CFG resets to push-pull, active high (DS15034 p60).
- **VREFBUF.** VREF+ and VDDA are both on 3V3A. ST's SVD gives the CSR reset value as 0x00000002 (ENVR = 0, HIZ = 1). The pull-down mode row still comes from a second-hand quote.

**Round 21 schematic notes**
- **sensors: correct.** ISM6HG256X high-g ranges ±32 / 64 / 128 / 256 g. Code 001 is ±64 g and 010 is ±128 g on both parts (Table 150 p93 of each). Codes 011 and 100 differ between the parts. Pins 10 / 11 default to input with pull-up (Table 25). SPI runs at up to 10 MHz.
- **battery_entry: correct.** The BAT_IN members are as listed. TPS259470**L** is the latch-off variant. Q120's drain is on BAT_IN, and R134 joins RAW_ACT and IGN.
- **diagnostics: partly.** The new sentence is right. The older second line is stale (R22-MCU-01).

## Fix verification

| Item | Verdict |
|---|---|
| D-R21 (no MCU pad net changed) | Confirmed |
| D-R21-01 (MCU impact; In2 3V3 still one piece) | Confirmed |
| D-R21-02 (U2.1 FB, the 3V3 sense: two vias, both inside the In2 3V3 fill) | Confirmed |
| D-R21-03 sensors / battery_entry | Confirmed |
| D-R21-03 diagnostics | Partly (R22-MCU-01) |
| D-R21-04 / -05 (MCU side) | Confirmed |
| D-R19-14, D-R19-04, D-R19-11 | Confirmed |
| D-R19-13 VREFBUF | Confirmed; the mode table is still an Inference |

## Fix now

- **R22-MCU-01 (text only).** In `r10_sch.py` `R21_SHEET_NOTES`, change line 2 of the diagnostics note to: "Nominal 5.456 V (PORT_5V3 via U402) reads 0.496 V; a failed U400 passes RAW_PROTECTED (U9 OVLO 9.77 V) and reads ≤ 0.89 V; even D8's 19.9 V clamp would read 1.81 V." The netlist and board are unchanged.

## Coverage limits

- RM0433 and AN5690 downloads failed again.
- AN2606 was not re-read.
- No firmware exists and no hardware was measured.
