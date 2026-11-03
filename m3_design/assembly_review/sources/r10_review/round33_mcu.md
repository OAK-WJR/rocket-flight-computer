# R10 round 33 — mcu lens (Claude)

Target commit `feed21f`; board `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c` before and after.

## Totals
0 Critical / 0 Major / 0 Minor real errors.

## Findings
None.

## Checks actually executed
- Board SHA-256 before and after: a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c
- U1 pad nets (pcbnew, 100 pads) vs pin_table.tsv r10_net: 0 mismatches
- binding note u1_pins (port, net, mode) vs pin_table.tsv: 100/100 identical; binding note pin_table_sha256 and circuit_sha256 match the files; board_sha256 matches
- DS12110 Rev 8 (cached PDF, verified 'DS12110 Rev 8'): LQFP100 pin order 1-100, every pin type quoted (PE4 FT_h, PA4 TT_a, PA5 TT_ha, PA6 FT_a, PC5 TT_a, PB1 TT_u, PB12/PB13 FT_u, PD8/PD9 FT_h, PC6/PC7 FT_h, PC0 FT_a, PC2_C/PC3_C TT_a) against Table 9
- Every 'Table 9 p. NN' citation in pin_table.tsv (82 rows) against the printed page of the pin's row: all correct; AF table pages (Tables 10-14) all correct
- AF numbers: TIM5 AF2, USART3/USART6/UART7 AF7, UART5 AF14, QUADSPI AF9 / NCS AF10, SPI1 AF5, SPI3 AF6, I2C1 AF4, OTG_FS AF10, ADC channels PA6 INP3, PC5 INP8, PB1 INP5, PC0 INP10
- Electrical table citations: Table 119 p. 212 (FT Min(VDD..)+4.0 V, TT 4.0 V) and notes 3-4 p. 213; Table 120 note 3 p. 213 (no positive injection, PA4/PA5 0/0); Table 122 note 3 p. 215; Table 157 note 7 p. 247 and VIH 0.7 VDD; Table 146 p. 238 LSI 29.4-33.6 kHz -> IWDG 28.571-32.653 ms; Table 159 p. 249 +/-3 mA; Table 160 note 2 p. 251 2 MHz; Tables 126/127/128/147/189/192, Figure 95 and Table 9 note 7 p. 88; PC1 RTC_TAMP3/WKUP5
- DS15034 Rev 1 / DS14623 Rev 1 (cached PDFs): Figure 5 p. 9, Table 2 p. 11, WHO_AM_I 0x73 p. 66, IF_CFG PP_OD/H_LACTIVE defaults p. 60, Table 150 p. 93 codes (ISM6HG256X 011 reserved / 100 = 256 g; LSM6DSV320X 011 = 256 g / 100 = 320 g), 3.904 mg/LSB at 128 g, SPI 10 MHz p. 17, Ton 40 ms p. 15; U4 pin nets vs Table 2
- Rule 3 values against the board: R127 1k (PYRO1_GATE_N-GND), R126 220R, R128 10k, C126 220 nF on PYRO1_GATE, C128 100 nF on PYRO1_OUT; 1k || 10.22k = 0.911 kohm; gate <= 0.104 V vs 30 kohm pull-up at 3.6 V; U3.3 = QSPI_IO2
- Rule 4 against the board: R120.1 ACT_FET_S at B(18.5,72.17), R120.2 / C120.2 ACT_GATE; ACT_GATE vias at (16.2,73.3), (15.4,72.85), (11.14,71.7), (11.74,72.3); rule 5 vias (28.1,59.4) 3V3 at R91.1 and (30.45,51.4) LOGIC_SOURCE_ST
- Members of every U1 signal net vs reset contracts (pull-ups R89/R90/R91/R432 to 3V3, R10/R11/R460-R464, R102/R431/R154-R157/R163/R5 pull-downs, dividers R60/R61, R104/R105, R9/R110, 10.2k/1k banks, ESD D410-D441 refs, TXU0202 A1/A2Y direction, MS5611 PS/CSB address 0x77)
- route_check.py --profile r10 on a probe copy: 0 failing (copy deleted afterwards)

## Fix verification
- Round 32's three text fixes are outside the mcu lens; nothing in the pin map, binding note or firmware rules changed.

## Observations (not counted)
- Rule 4's '0.93-1.01x the 1.125 A floor' versus 1.128 / 1.063 A (0.945-1.003x) is the envelope of round 23's case table; already ruled not an error (R27 triage).
- PA3 '<= 0.83 V' (pin_table loader role) is correct at nominal VDD 3.3 V; already ruled (R26 / R32 triage).
- Rule 3's 'about 47-58 us' (53 us x 0.9 = 47.7 us): an outward 'about' bound, same class as earlier rulings; the 53 us nominal implies about 27 ohm PE4 driver resistance, labelled Inference.
- parts_qualification.md (PA6 single-fault item) cites the 4.0 V FT_a/ADC limit from DS12110 Rev 11 Table 109 without repeating the binding note's Inference label; Rev 11 was not re-read in this round (coverage limit), and this pre-existing citation has been in the audited record since round 14.
- Q120/Q121 'worst-case settled |VGS| 4.74 V / 31.9 ms' uses the 6.0 V pad-check BAT_IN; already ruled (R27 triage).
- U1 decoupling: VDDA/VREF+ have 1 uF (C22) + 100 nF (C21) as in DS12110 Rev 8 Figure 95 p. 286; every VDD pin has a 100 nF within 1.25-3.97 mm plus 4.7 uF C23.
- HSE: C25 / C26 10 pF C0G with an 8 pF CL crystal is consistent with about 3 pF stray (Inference).

## Coverage limits
- AN2606 and RM0433 not available offline: the loader-role and RM0433 statements were not re-read (already labelled Inference where they matter)
- DS12110 Rev 11 not re-read
- Power, safety and fire-budget figures quoted in the obligations were checked only for arithmetic and board values, not re-modelled
- LSM6DSV80X datasheet not checked
