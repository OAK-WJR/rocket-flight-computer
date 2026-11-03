# R10 round 31, lens mcu

Target commit `3366287`, board SHA-256 before and after:
`a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c`. Reviewer: Claude. Strict real-error rule.

**Totals: 0 Critical, 0 Major, 0 Minor.** No real errors found.

## What was checked

- **U1 pin map.** I compared four sources for all 100 pins: the U1 pads on the board, the U1 pins in a kicad-cli schematic netlist export, `pin_table.tsv` `r10_net` and the binding note's `u1_pins`. They agree, with 0 mismatches. The symbol's pin functions match the port names.
- **Pin numbers and types (DS12110 Rev 8 Table 9).** These match DS12110 Rev 8 Table 9, and so do every pin-type statement and its page citation:
  - PE4 FT_h, p. 64;
  - PC0 FT_a, p. 67;
  - PA4 TT_a, PA5 TT_ha and PA6 FT_a, p. 69;
  - PC5 TT_a and PB1 TT_u, p. 70;
  - PB12 / PB13 FT_u, p. 74;
  - PD8 / PD9 FT_h, p. 75;
  - PC6 / PC7 FT_h, pp. 78–79;
  - PC14 FT, p. 65.

  The statements checked are in the pin table, the binding note, M3_R10, R10_VALIDATION and parts_qualification.
- **Alternate functions and AF-table pages.** These match Rev 8: UART5 AF14, UART7 AF7, USART3, USART6 and the QUADSPI pins, in Tables 11–14 on pp. 91–95.
- **Binding note.** Regenerated in memory with `r10_sch_check.binding_note` on the committed project and board, it equals the saved note in every key (`c5cd0fa3…`). The pin table and circuit hashes match.
- **Rules 3 and 4 against the copper.**
  - QSPI_IO2 = {U1.1, U3.3}.
  - PYRO1_GATE_N = {U1.3, R126.1, R127.1}.
  - R127 ∥ (R126 + R128) = 0.911 kΩ.
  - ACT_GATE / ACT_FET_S probe points: R120.1 at B(18.5,72.17), R120.2 and C120.2.
  - The four ACT_GATE barrels are present.
  - AONR21357 Rev 2.1 p. 2 gives VSD −0.7 / −1 V, VGS(th) −1.3 / −1.7 / −2.3 V and RDS(on) ≤ 12.3 mΩ.
- **DS15034 / DS14623 citations.** All match: Figure 5 p. 9, Table 2 p. 11, Ton p. 15, SPI p. 17, IF_CFG p. 60, WHO_AM_I p. 66 and Table 150 p. 93.
- **Other figures recomputed.** All reproduce:
  - the gate-hold voltages (PE4 0.104 V, PC1 0.218 V);
  - PC8 2.20 V against VIH 2.31 V;
  - the IWDG at 960 cycles: 28.571–32.653 ms, with a 34.853 ms fault bound;
  - the divider scales: /11, /11 and /11.2;
  - the MS5611 address 0x77 from the footprint nets;
  - the TXU0202 pin roles;
  - the port series and ESD designators;
  - the LED polarity.

## Fix verification

| Item | Verdict |
|---|---|
| R30-TRI-01: the D120 / R131 cold pull-up | **Confirmed.** My own solve gives 2.205 / 2.191 V and 0.107 / 0.109 mA at a BAT54 drop of 0.20 / 0.24 V. The EN load is 11.2 k ∥ 11.2 k = 5.6 kΩ with a load fitted. |
| R30-TRI-02: the LS120 clause | **Confirmed (spot check, outside this lens).** Only history rows still carry the old clause. |
| D-R29-01: rule 3's time constant | **Confirmed.** 47.8 / 53.0 / 58.3 µs. |
| D-R28-02: rule 3's meter check | **Confirmed.** |
| D-R28-04: rule 4's Q120 criterion and the DS15034 Table 2 page | **Confirmed.** Table 2 is on p. 11. |

## Observations

There are 18 observations, none counted; they are listed in the JSON. Among them:
- PA4 / PA5 have a −0/0 mA injection limit in Table 120, and no design case injects into them.
- The trace pins PC8 and PC12 also carry TRACED1 / TRACED3 but no firing copper.
- Two items are repeats the triage has already ruled on: rule 4's 0.93–1.01× range and PA3's ≤ 0.83 V.

## Coverage limits

- AN2606 and RM0433 were not re-read.
- U4's axis directions were not re-derived.
- The power and safety figures in the obligations were checked only where they bear on MCU pins.
- There is no physical evidence.
