# R10 round 20: MCU lens (Claude)

- Target commit `6628488cf34bf33bdf104cb4383fcbe447c5da65`, reviewed from a `git archive` copy in `.supervisor/r20_mcu/tree`.
- Board SHA-256 before and after: `50a39de5b76dec3cb58bbb1b0ab528fd4d65098de9dfe8f89f49e2e7adcbd976` (unchanged).
- **Totals: 0 Critical, 0 Major, 4 Minor.** All four are text-only. Machine-readable version: `round20_mcu.json`.

## Findings

| ID | Sev | Title | Key evidence |
|---|---|---|---|
| R20-MCU-01 | Minor | The VREFBUF obligation guards only against enabling the buffer. It does not cover the ENVR = 0 / HIZ = 0 mode, which pulls VREF+ to VSSA. | Obligation 35 forbids only ENVR = 1. VREF+ (U1.20) is on 3V3A, which is also VDDA, U4 (IMU) and U5 (barometer), fed through R164 (2.2 Ω). The RM0433 mode table, as quoted by ST community, says ENVR = 0 with HIZ = 0 pulls VREF+ down to VSSA. RM0433 was not re-read, so this is an Inference. |
| R20-MCU-02 | Minor | The port rule allows 0–5 V endpoints. But at every battery power-up PORT_4V8 comes up tens of ms before 3V3, and while VDD = 0 the FT limit is 4.0 V. The spare AUX port invites an unspecified device. | DS12110 Rev 8 Table 119 p212: the limit is Min(VDD…) + 4.0 V, which is 4.0 V at VDD = 0. U11's C85 (470 nF) gives about 166–170 V/s, so VLOGIC takes about 44 ms to reach 7.4 V (SLVSEA3F Table 9-1 p13, Calculation). Binding obligation 15, ORDERING line 577 and M3_R10 line 701 say "0–5 V"; R10_VALIDATION lines 1574 and 1926 say "≤ 3.6–4.0 V". |
| R20-MCU-03 | Minor | There is no obligation for a port with no mapped device. J440 has none by default and is normally unplugged, so its RX pin floats if USART6 is enabled. Obligation 20 also parks only the TX pins while PA4 is high. | Nothing pulls AUX_RX_MCU / AUX_RX_WIRE either way. Obligation 31 reacts only after errors occur. |
| R20-MCU-04 | Minor | `parts_qualification.md` still gives the pre-D-R19-14 pin map (R440 / R441 to PC7 / PC6) with Rev 11 cites, and leaves out the AUX path (R470 / R471, D440 / D441). | Lines 82–84 and 727. The board has R440 to PD9, R441 to PD8, R470 to PC7 and R471 to PC6. |

## Round 19 fix verification

| Fix | Verdict | What I measured |
|---|---|---|
| R19-MCU-01 (port-UART enable on PA4) | Confirmed | U11 IN1 = USB_LIMITED, IN2 = RAW_PROTECTED, ST goes to PA4 (R91 10 kΩ pull-up). Per SLVSEA3F Table 9-3 p18, ST low means IN2 is selected. The rule appears for all three TX pins (PD8, PB13, PC6) in pin_table, the binding note and the docs. |
| R19-MCU-02 (single DS12110 revision) | Confirmed | All 82 rows cite Rev 8. The page spot-checks match the cached Rev 8 copy. |
| R19-MCU-03 (sheet notes) | Confirmed | Both notes are present. PE3, PE5 and PE6 have no copper. |
| R19-MCU-04 (VREFBUF) | Partly | The obligation exists, but see R20-MCU-01. |
| D-R19-04 (C123 on Q122's gate) | Confirmed | C123 is ACT_EN to GND. Time constant τ = 7.09 µs. The gate reaches 1.45 V after 7.63 µs, falls in 8.64 µs, and falls in 25.9 µs after a reset. PC1 sees a 3.3 mA peak. AGENTS §2.4 is met. |
| D-R19-11 (U4 interface) | Confirmed | Page 9 of DS15034 and DS14623 render the same. INT1 is forced low by default (p52). IF_CFG defaults to push-pull, active high (p60). WHO_AM_I is 0x73 (p66). U4.4 is wired to PE1 (EXTI1). |
| D-R19-14 (MCU part) | Confirmed | Port D and port C AF7 give USART3 on PD8 / PD9 (Table 13 p94) and USART6 on PC6 / PC7 (Table 12 p92); all four pins are FT_h. Board, committed netlist, a fresh kicad-cli 10.0.7 netlist, pin_table and binding note agree on all 100 U1 pins. TX/RX directions are correct. DRC with parity: 0 / 0 / 0. |
| D-R19-05 (U1.19) | Confirmed | Pad 19 is set to no zone connection. |

## Worth fixing now (text only)

- **R20-MCU-02:** state one rule everywhere: a device's TX high level on J410 / J420 / J440 must be ≤ 3.6 V.
- **R20-MCU-01:** add "never clear HIZ; never write VREFBUF_CSR".
- **R20-MCU-04:** correct `parts_qualification.md` to the current pin map.

## Coverage limits

- The AN2606 and RM0433 PDFs timed out. Loader roles and the VREFBUF mode table rest on the existing AN2606 Rev64 reading in pin_table plus ST community quotes, so they are Inferences.
- No firmware exists, and nothing was measured on hardware.
