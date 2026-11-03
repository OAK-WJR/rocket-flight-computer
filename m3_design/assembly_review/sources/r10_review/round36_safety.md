# R10 round 36 — safety lens

Commit `c3c4249`, board `a0ec075e…` (SHA-256 identical before and after).

**Totals: 0 Critical / 0 Major / 0 Minor.** No real errors found.

## What was checked
- AGENTS §2 on the board as built: Q124's gate network (R126 220 Ω series, R128 10 kΩ pull-down, C126 220 nF gate–source, R127 1 kΩ at PE4); Q122 (R122 / R123 / C123); Q120 / Q121 (R120 / R119, R121, C120); pyro bus behind the load switch (R134.2 on RAW_ACT).
- Firmware rules 3 and 4 against the board and ORDERING 8.3: U3.3 and U1.1 are the only QSPI_IO2 pads; 0.91 kΩ = 1 k ∥ 10.22 k; R120.2 / C120.2 / R120.1, TP80 / TP120 / TP74 / TP88 nets match the probe instructions.
- Fire-chain adjacencies re-measured (PYRO1_OUT–GND 0.177 / 0.180, –3V3 1.050, –3V3A 1.040, –BUZZ_DRV 0.794; gate nets to 3V3 ≥ 1.0585, to 3V3A 1.145 mm) and R10_VALIDATION §1 rows and owner rows 1 / 2: all match.
- A whole-net scan of the bus, enable, EN and sense nets for single faults: every case found is covered by the disclosures in owner rows 1, 2 and 24.

## Fix verification
- R34-TRI-01 (outside this lens): confirmed.

## Observations
12 (in the JSON). None counted. Among them: PYRO1_OUT–BUZZ_G is 0.510 mm but cannot fire (behind 1 k / 10 k). The Q120 stub open is caught by the BAT_IN − RAW_ACT criterion. Q122's 2.19 V is the 1 % corner (D-R18-01). Harness EN 1.28 V was ruled by round 30. The S-8 table's J400.2 In1 figure is labelled historical.
