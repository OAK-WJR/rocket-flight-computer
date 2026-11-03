# R10 round 12: MCU, ports, reset and ESD

Independent read-only lens 5 on commit `d57b216c365fc8d18896bceba37f63caf20d52a4`.
PCB SHA-256 before and after: `0ad0135cb9ff1f6ace7ef9d5ba9006b727b293d7b5224bb97dad47859b91238d`.
U1 is STM32H743VIT6TR, LQFP100, F(23,43), rotation 0.

**Result: 0 Critical / 0 Major / 1 Minor, new.** No pin-map, assigned-AF or demonstrated reset-off hardware failure was found. Both prior MCU record findings are closed. Explicitly pending firmware/physical qualification and the owner's direct-port architecture are retained limits, not new proven hardware failures.

## R12-MCU-01 - Minor, new: PC14 peak-current proof reverses a bound

`m3_design/assembly_review/sources/r10_design/pin_table.tsv:9` states edge current <=about2.9mA using `3.3V/(1kohm+133ohm)`, with the driver estimate taken from `0.4V/3mA`.
Native U1.8/PC14 is at (20.5,50.55); it drives R162=1kohm at B(19.5,57.7), then Q123's gate, with R163=10kohm to GND. R162 is 0805W8F1001T5E/C17513, +/-1% per the [exact supplier specification](https://www.lcsc.com/product-detail/C17513.html), Products Specifications.

[ST DS12110 Rev11 Table149 p244](https://www.st.com/resource/en/datasheet/stm32h743vi.pdf) specifies a maximum output drop at the3mA test point. Even a linear interpretation makes133.3ohm an **upper** resistance bound there, not a minimum resistance that can be added to prove a maximum current. The actual output characteristic is nonlinear. The stated <=2.9mA conclusion therefore is unsupported. A resistor-only initial bound with a discharged gate is3.3mA nominal, or3.364mA at the stated3.33V/990ohm corner (Calc/Inference); steady current is about0.306mA.

This is a bounded evidence error. The3mA table row is an output-level characterization condition; it does not by itself prove a hard transient-current violation or failed buzzer.

**Fix:** replace the <=2.9mA proof with the conservative resistor-only bound and retain unmeasured gate/driver dynamics; regenerate pin-table/binding provenance. If <=3mA is an intended hardware target, choose a resistor minimum >=VDDmax/3mA and qualify the edge. Do not infer minimum driver resistance from maximum VOH drop.

## Executed native checks

The JSON retains every pin, coordinate, net member, selected component and file hash from the independent probe.

| Check | Result |
|---|---|
| Original maker package names | 100/100 match ST Figure5 p55 and XML symbol |
| PCB/XML/table/binding net maps | 100/100 agree;68 connected,32 NC |
| NC copper | All32 are single-pad nets with no track/via/zone |
| Binding SHA fields | PCB,XML,pin table,circuit all match actual bytes |
| Assigned alternate functions | 28/28 match ST Table10 pp89-94 |
| ADCs | PC0 ADC123_INP10;PC5 ADC12_INP8;PA6 ADC12_INP3;PB1 ADC12_INP5;PC3_C ADC3_INP1 |
| EXTI | Six distinct lines:PE1/1,PA4/4,PA5/5,PD6/6,PC8/8,PE12/12 |
| Loader | Latest AN2606 Table135:26 package pins,14 connected/12 NC;PC1/PE4 absent |
| Native power pins | FiveVDD plusVBAT=3V3;VDDA/VREF+=3V3A;allVSS/VSSA=GND;VCAPs each have only their own2.2uF |
| Reset controls | PC1->R1221k->Q122 gate/R123100k GND;PE4->R126220R->Q124 gate/R12810k/C126220nF GND;R1271k onMCU side |
| Camera biases | PE9/U12OE hasR10210k GND;PE11/U402EN hasR431100k GND;PE12fault hasR43210k to3V3 |
| Servo/card defaults | All four PWM pulls present;SD_CS hasR46010k to3V3;BOOT0 hasR5 toGND;NRST hasC24100nF |

ST's original [DS12110](https://www.st.com/resource/en/datasheet/stm32h743vi.pdf), section3.8 p32, supports analog reset mode for non-debug GPIOs. The external pulls remain independent of active firmware. This is static circuit evidence, not measured startup/brownout behavior.

## Direct UARTs and retained limits

| Native path | MCU pad (mm) | Ground clamp |
|---|---|---|
| J410.4->R4401k->U1.64/PC7 | (22.5,35.45) | D411 onGPS_RX_WIRE |
| U1.63/PC6->R4411k->J410.3 | (23,35.45) | D410 onGPS_TX_WIRE |
| J420.4->R4501k->U1.51/PB12 | (29,35.45) | D421 onRADIO_RX_WIRE |
| U1.52/PB13->R4511k->J420.3 | (28.5,35.45) | D420 onRADIO_TX_WIRE |

J410/J420 are F(38.6,15.5)/(38.6,31.5); both pin1 supplies directly join PORT_4V8. No switch, translator or rail clamp intervenes on those four UART paths. PB12/PB13's USB-option pins use VDD in UART operation (DS12110 Table9 note7 p88); PC6/PC7 are FT_h. The operating envelope in Table112 must accompany the absolute limits: disable internal pulls whenever a driven input exceeds its relevant supply+0.3V. Neither1k nor an FT label establishes powered-off isolation. The existing no-self-powered-port/e-match connection restrictions remain necessary.

The [exact Infineon EL page](https://www.infineon.com/part/ESD103-B1-02EL) corroborates the high-voltage clamp characteristic; it does not establish MCU-pin ESD survival. Its datasheet link returned ELS, so that PDF is not substituted for the exact EL package. Installed cable ESD, edge quality and RF immunity remain unqualified. The current qualification record now says this accurately.

Camera U12/U13/U402 remain and their native pins agree with TI. U12 uses main3V3 onA and CAM_IO_3V3 onB, with both directions correct. [TXU0202 SCES942A pp4/20-23](https://www.ti.com/lit/ds/symlink/txu0202.pdf) provides its partial-power isolation; [TPS2553 SLVS841G p7](https://www.ti.com/lit/ds/symlink/tps2553.pdf) still has a reverse-trip threshold/delay. No instantaneous or enabled-camera back-feed immunity is inferred.

[AN2606 Rev70 Table135 pp320-323](https://www.st.com/resource/en/application_note/an2606-stm32-microcontroller-system-memory-boot-mode-stmicroelectronics.pdf) remains consistent with the recorded loader containment. PA6's possible loader drive only reaches its diagnostic divider; SDCS stays pulled high while PC11 can drive. PC1/PE4 locks, disabled synchronous trace, no trace debugger with an e-match and no loader jump after IWDG start remain unimplemented obligations. Ordinary PA6/PB1 diagnostic single-fault damage cases remain recorded residuals.

## Prior findings and coverage limits

- **R11-MCU-01, closed:** current `parts_qualification.md` scopes translator protection to camera and states the direct GPS/radio ESD limits.
- **R11-MCU-02, closed:** seven Rev11 AF citations use Table10 and PC1's source text says analog reset. Four binding hashes independently match.

No native DRC/ERC, full gate, build or generator was run by this lens. No source/CAD changes were made. No firmware, ADC thresholds/accuracy, reset/gate waveform, thermal, cable ESD, RF immunity, back-feed current or physical test was performed. ST's original PDF was read through its web extraction; direct local downloads failed/timed out, so no complete local-page render verification is claimed. CAD agreement is not physical or firmware qualification.

Evidence: [round12_mcu.json](round12_mcu.json). Context reviewed: the supervisor packet, AGENTS, REQUIREMENTS, owner/newest R10 decisions, AVA_LAYOUT, M3_R10, R10_VALIDATION, R9 severity precedents and the read-only VEHICLE reference. No other round12 lens report was read.
