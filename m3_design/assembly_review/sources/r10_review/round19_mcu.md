# Round 19 MCU pin map and interfaces review (Claude)

Target commit `1e604412015002be941f7056d0788d23f508e6ac`. PCB SHA-256 before and after:
`a3144b151b58daf8ba5747def50decc4d1751ad35be478fafc89ef53aa533918` (unchanged).
**0 Critical / 0 Major / 5 Minor (4 new, 1 carried).** This is a CAD and record review, not firmware or bench
evidence. Full evidence is in `round19_mcu.json`; probe files are in `.supervisor/r19_mcu/`.

## Findings

### R19-MCU-01 (Minor, new): the round 18 USB-only UART rule uses the wrong TPS2121 status polarity

`docs/M3_R10.md` lines 592-593 say: enable the GPS and radio UARTs only when PA4 (LOGIC_SOURCE_ST) shows U11's
"IN1 (the battery)" selected, and park PC6/PB13 "when PA4 falls".

On this board, IN1 is the USB input:

- U11 pin 7 is `IN1_USB` = USB_LIMITED, and pin 2 is `IN2_BAT` = RAW_PROTECTED.
- PR1 and CP2 are tied low, so U11 runs in VCOMP mode.

TI SLVSEA3F (p4 pin table, p18 Table 9-3, p21) gives the status pin as:

- ST low means IN2 (the battery) powers the output.
- ST high means IN1 (USB), or no valid input.

The schematic's own note agrees: "ST LOW = IN2 battery" (logic_power_path sheet, (20.32, 274.32)). The error
started in R18-MCU-02, which swapped the pins.

If firmware followed the rule as written:

- on the pack, the UARTs would never come up, so there would be no GPS or telemetry (F10);
- on USB only, TX would idle high into the unpowered modules, at about 2.7 mA per line. That is the back-drive the
  rule was written to prevent.
- "park when PA4 falls" would park the UARTs exactly when the battery path turns on.

The binding note has three related gaps:

- it never says how firmware knows the ports are powered;
- it does not park the TX pins on shedding;
- obligation 14 still says "GPS/radio are always powered".

**Fix (text only):**

- Enable the UARTs only while PA4 reads **low**, after a settling delay.
- Park PC6/PB13 in analog mode with no pull when PA4 **rises** or when the PA6 trigger fires.
- Carry the same rule into the binding note and regenerate it.
- Change obligation 14's "always powered" wording.
- Use one parking mode everywhere.

Option for the owner: the same PA4-low test could also gate PC1. That blocks the documented case where USB powers
the board with the switch open.

### R19-MCU-02 (Minor, new): DS12110 citations mix revisions and electrical chapters

Only Rev 8 was reachable here. st.com timed out, and the LCSC copy is byte-identical to the cache. Rev 8 has two
electrical chapters: rev Y (pp104-209) and rev V (pp210-320).

**Chapter mix.** These cite rev Y tables:

- D-R18-01: Table 60 p139 and Table 61 p141;
- pin_table row 18 and binding obligation 20: Tables 28/29 and Table 94.

The binding note's Rev 11 table numbers otherwise map to rev V. The values agree in both chapters.

**Page offsets.** Several unchanged pin_table rows cite AF pages one page below Rev 8:

| Pins | Pin table cites | Rev 8 page |
|---|---|---|
| PA0-PA3, PA11, PA12 | p. 88 | p89 |
| PB8/PB9 | p. 90 | p91 |
| PD11-PD13 | p. 93 | p94 |
| PE2 | p. 94 | p95 |

The 1e60441 edits cite p91/p92, the same as Rev 8. In Rev 8, PB8/PB9 and PB12/PB13 share p91, so the two sets of
cites cannot both be right.

**Note number.** The pull-off rule is cited as "Table 147 note 6". In Rev 8 it is Table 157 **note 7**.

No pin, alternate function or value is wrong.

**Fix:** do one citation pass on a single revision (the rev V chapter) when st.com is reachable.

### R19-MCU-03 (Minor, new): two retained R8 schematic notes contradict the R10 pin map

**Camera note.** `camera_uart.kicad_sch` (20.32, 231.14) says "PA7/pin31 controls OE as GPIO". In R10, OE is PE9
(CAM_UART_OE, with R102 to GND), and PA7 has no net.

**Sentinel note.** `mcu.kicad_sch` (20.32, 280.0) says "PE3 (pin 2) and PE6 (pin 5) are pyro-gate sentinels - no
net, firmware drives them low". Two things are wrong:

- The pin table and binding obligation 5 say these pins stay analog and are never driven (R5-MCU-03).
- PE4's neighbours are PE3 and PE5, not PE6.

`check_actuators.py:431` repeats the wording. No earlier round mentions either note.

**Fix:** replace both notes in `r10_sch.py`, fix the comment, and rebuild the sheets. The netlist and board are
unchanged.

### R19-MCU-04 (Minor, new): no obligation keeps VREFBUF disabled

VREF+ (U1.20) is tied to VDDA (U1.21) on 3V3A, which also feeds the IMU and barometer. ST supports this
(DS12110 Rev 8 Figure 95 p285), and VREFBUF resets to HIZ = 1 (ST SVD).

One HAL call would turn the buffer on. Its 1.5-2.5 V output would then drive a pin held near 3.3 V through 2.2 Ω
(Table 189: 4 mA load). Compare DS Table 9 note 7: where VREF+ is bonded to VDDA, the buffer "must be kept
disabled". RM0433 was not re-read, so this is an Inference.

**Fix:** add one obligation: keep VREFBUF_CSR at its reset value, never enable it, and scale the ADC from VREFINT.

### R19-MCU-05 (Minor, carried R18-MCU-04): VCAP qualification

C19/C20 are 2.2 µF ±10 % X5R. This meets Table 124 p216 nominally (2.2 µF ±20 %, ESR below 100 mΩ). The corners
remain unqualified. Keep deviation D-R15-02. No CAD change.

## Round 18 fix verification

| Decision | Check | Verdict |
|---|---|---|
| D-R18-01 (R123 2 kΩ) | Board, BOM and budget agree. The gate is held at ≤ 0.220 V against a 30 kΩ pull-up. With PC1 high it is 2.19 V; the floor is 1.90 V (not 1.92 V) at AP63203 VFB minimum 3.27 V, still 0.45 V above VGS(th) max. C120 discharge gives 0.84 mA peak. A BAT_ENABLE bridge now fails safe. | confirmed |
| D-R18-01 (PC3_C NC) | U1.18 is isolated, with 33 NC pads. The pin is analog behind either PMCR switch state. Note: VBAT/4 is ratiometric with ±10 % error, so the 3V3 figure really comes from VREFINT. | confirmed |
| D-R18-03 (PC1 run) | The recorded gaps reproduce (0.550 / 0.520 / 0.425 / 0.251 / 0.200 / 0.330 mm). The record leaves out the PYRO1_CONT track at 0.250 mm and its via at 0.393 mm. A bridge there is fail-safe (gate ≤ 0.38 V). | confirmed (record incomplete) |
| D-R18-10 (PE4 text) | The text is present. The gate stays at ≤ 0.104 V (0.105 V with 1 % parts). Inrush is 18.65 mA against 20 mA. Hi-Z gate off takes 0.50 ms. | confirmed |
| D-R18-10 follow-up (R18-MCU-02) | Most records are right, but the M3_R10 rule is inverted and the binding note has the gaps above. | partly |
| D-R18-10 follow-up (PC5 text, cites) | The PC5 text matches the netlist and DS. Rev 11 is unverifiable, and the page offsets remain. | partly |

## Verified clean

- **Pin map.** All 100 pins agree across board, fresh netlist, pin table and binding note, including the binding
  hashes. The fresh kicad-cli 10.0.7 netlist matches the board pads (0 mismatches) and the committed netlist
  (0 differences). Pin names match DS Figure 5 (100/100).
- **Alternate functions.** Checked from the Rev 8 page images: USART6 AF7, UART5 AF14, UART7 AF7, SPI3 AF6, SPI1
  AF5, QUADSPI AF9/AF10, I2C1 AF4, OTG_FS AF10, SWD AF0, TIM5 AF2. ADC channels: PC0 INP10, PC5 INP8, PA6 INP3,
  PB1 INP5.
- **Package.** The LQFP-100 land matches ST's 16.7 mm toe span with a 0.4 mm longer heel (the library land used
  since the first M3 board).
- **Peripheral wiring.** QSPI, IMU (R11 CS pull-up), MS5611 (PS high, CSB low) and SWD are correct.
- **HSE.** gm_crit is 0.40-0.71 mA/V against 1.5 mA/V.
- **Back-feed into an unpowered MCU.** This stays within the FT limit of 4.0 V at VDD = 0.
- **DRC.** kicad-cli 10.0.7 with all severities and schematic parity: 0 / 0 / 0.

## Fix now

1. R19-MCU-01: the text corrections above, with a binding-note regeneration.
2. R19-MCU-03: the two schematic notes and the comment.
3. Optionally, R19-MCU-04's obligation in the same regeneration.

## Limits

- st.com was unreachable, so Rev 11, RM0433 and AN2606 were not re-read. PMCR, VREFBUF and tamper behaviour are
  Inference.
- The silicon revision is unknown.
- No firmware, bench work or check.sh run.
- Other round19 reports were not opened.
