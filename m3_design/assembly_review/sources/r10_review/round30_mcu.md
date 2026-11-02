# R10 round 30, mcu lens (Claude)

Target: commit `0afaed3`. Board SHA-256 `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c`, the same
before and after. Read-only: probe files are in `.supervisor/r30_mcu/`. Full evidence is in `round30_mcu.json`.

## Totals

| Critical | Major | Minor |
|---|---|---|
| 0 | 0 | 0 |

No real errors found.

## What was checked

- **U1 pin map.** Board pads, `schematic.net.xml` and the binding note `u1_pins` all match `pin_table.tsv` `r10_net`
  on all 100 pins, with 0 mismatches. LQFP100 numbering matches DS12110 Rev 8 Figure 5 p55, power pins included.
- **Pin types.** Every pin-type statement matches DS12110 Rev 8 Table 9:
  - PE4 FT_h, PA4 TT_a, PA5 TT_ha, PA6 FT_a, PC0 FT_a, PC5 TT_a, PB1 TT_u;
  - PB12 / PB13 FT_u, PD8 / PD9 FT_h, PC6 / PC7 FT_h, PC8 FT_h, PE7 / PE8 TT_ha.

  Every Table 9 page in the pin table matches.
- **Alternate functions and ADC channels.** Every AF and its page is correct, as are the AF0 trace pins (PE2 / PC1 /
  PE4) and the ADC channels (PC0 INP10, PA6 INP3, PC5 INP8, PB1 INP5).
- **Datasheet citations.** Tables 119, 120, 122, 126–128, 146, 157, 159, 160, 189 and 192, Figure 95, Table 9 note 7,
  and sections 3.8 / 3.19 all say what is cited, on the cited pages.
- **Binding note bindings.** The board, netlist, pin-table and circuit hashes all match. Rules 3 and 4 match the copper:
  - R127 / R126 / R128 / C126 / Q124 and R119 / R120 / C120 / R121 / Q120 / Q121 have the stated nets.
  - All cited vias and probe points sit on the stated nets.
  - The 3V3 to gate-net clearances are 1.0585 / 1.065 / 1.145 mm, and the In2 3V3 fill is 2.75 mm from the
    gate-via barrel.
  - QSPI_IO2 is 0.550 / 0.700 mm from U1.3.
- **Recomputed figures.**
  - IWDG: 960 cycles, 28.571–32.653 ms, 34.853 ms.
  - Pull-up bounds: 0.104 V (PE4) and 0.218 V (PC1). PC1 high gives 2.2 V. The hard-bridge gate is 3.23 V.
  - Meter path: 0.91 kΩ. Q122 gate constant: 7.1 µs. PA6 window: 4.84–5.17 V.
  - Port-supply lead: 21–26 ms (TPS2121 Table 9-1 p13 scaled to 470 nF, AP63203 p5).
  - GNSS harmonic check: 25 / 75 MHz.
- **IMU citations (DS15034 / DS14623).** Figure 5 p9, Table 2 p11, p15, p17, IF_CFG defaults p60, 73h p66 and Table 150
  p93 are all correct. U4's pads match Table 2.

## Fix verification

| Item | Verdict |
|---|---|
| D-R29-01: rule 3 time constant, 47.78 / 53.03 / 58.28 µs reproduced; phrase present in the note, M3_R10, FMEA, R10_VALIDATION and STATUS | confirmed |
| D-R29-02: test pins for the D-R28 labels (read, not run) | confirmed (by reading) |
| Binding note `c5cd0fa3…` and its four bound hashes; `u1_pins` = pin table | confirmed |
| D-R28 rule 3 meter criterion (both polarities) | confirmed |
| D-R28 rule 4 Q120 criterion, VSD p2, gate barrels, R120.1 / TP80 / TP120 | confirmed |
| D-R28-02 DS15034 Table 2 p. 11 | confirmed |
| Obligation 15, "tens of ms" (21–26 ms) | confirmed |

## Observations (8, not counted)

1. M3_R10:444 says "U1.15 / U1.17 pitch 0.200 mm". The 0.200 mm figure is the pad gap; U1's pitch is 0.5 mm.
2. The ACT_EN_MCU-to-NRST via bridge (0.425 mm) would also reset-loop the MCU when PC1 drives low. That is fail-safe,
   and leaving it out makes no record false.
3. "R121 × C120 = 10 ms" in the owner option that was not adopted. The Thevenin constant is about 8.3 ms.
4. PC8 detection uses the tested 0.7 VDD threshold, not the by-design 0.47 VDD + 0.25 V line. The record is
   conservative, not false.
5. Rule 4's 0.96 band depends on temperature (Q120's body diode is about 0.51 V at 25 °C and about 0.32 V at 125 °C, at
   about 1.8 mA). Round 29 already ruled it covered by "Qualify the band".
6. Rule 4's ratio range is the round 23 envelope. Round 27 already ruled it conservative.
7. AN2606 was not re-read (download unavailable). The loader roles are consistent with the board nets.
8. PA4 / PA5 allow −0/0 injection (Table 120). Both are open-drain inputs pulled to 3V3, so there is no violation.

## Coverage limits

- AN2606 and RM0433 were not read.
- No `check.sh`, test or build was run.
- The u-blox integration-manual and W25Q128JV AC citations were not re-read.
