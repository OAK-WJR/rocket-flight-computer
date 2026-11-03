# R10 round 31: requirements lens

Target commit `3366287`, board `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c` (SHA-256 identical
before and after). Strict real-error rule (`.supervisor/r31_review_brief.md`).

**Totals: 0 Critical / 0 Major / 0 Minor real errors.** 21 observations (not counted).

## Method

Each row of `docs/REQUIREMENTS.md` (Sources, F1–F12, P1–P3, M1–M3, operating assumptions, acceptance) was mapped
to the board by read-only pcbnew dumps (`.supervisor/r31_requirements/`), to `pin_table.tsv`, `parts_budget.json`,
`stock_check.json` and `cost_check.json`, to the cached datasheets, and to `../../docs/VEHICLE.md`. I recomputed
the key figures myself.

## Findings

None. No requirement fails on the board, no two requirements contradict each other, and no figure is wrong against
VEHICLE.md.

## Main confirmations (detail in the JSON observations)

- **Outline and supports:** 46 × 90 mm with five supports at the stated points.
- **Pin map:** U1's pad nets match `pin_table.tsv` on all 100 pins: the port UARTs, SPI3 / PD0, PC1 / PE4 / PC0 / PC5,
  PA6, PC14, PB1 and the six EXTI lines.
- **F4:** J122 has four 1 kΩ series resistors, four 10 kΩ pull-downs, the SRV05-4 and GND on pin 5.
- **F8 / F10 legends:** every DB125 pin legend matches its net, J121's E1− / E1+ included.
- **F9 / F10:** the rails compute to 5.456 V and 4.792 V. D402's tap is 4.114 mm long and its GND via sits 0.700 mm away.
  The U401.11 vias are at the stated points.
- **F7:** the fire feed is 1.0 mm. ACT_FET_S has exactly seven 0.4 mm bridges, and the other narrow copper is
  sense or bias branches.
- **F8:**

  | Figure | Recomputed |
  |---|---|
  | Q122 gate | 0.218 V |
  | Fault ceiling | 3.342171 V |
  | Fault current | 1.397 mA |
  | Cold-screen levels | 99.370 / 99.335 / 146.226 mV, within the stated "≈" |

- **F6 / Pack:**

  | Figure | Recomputed |
  |---|---|
  | Budget figures (5.713 V; 1.541 / 1.476 / 1.279 A; hold-up times) | match `parts_budget.json` |
  | U9 turn-off corner | 4.802 V |
  | Single drop-out at 6.0 V | 10.34 ms |
  | IWDG timeout | 28.571–32.653 ms (DS12110 Table 146) |

- **F1:** the DS15034 Rev 1 limits match, and the budget arithmetic reproduces.
- **Temperature row:** θJA 45 °C/W and the TJ range match the datasheet, and so do the part temperature ratings.
- **VEHICLE.md:** the aft edge is at joint + 79.4–83.4 mm. Both flights use 635 mm motors in 721 mm boosters. Apogee
  is 8.8 km MSL, about 317 hPa.
- **M1 / M3:** the U4 and U9 shortfalls are as stated, and the cost is $85.26 against $84.41.

## Fix verification

| Item | Verdict |
|---|---|
| R30-TRI-02: Temperature-row pass criterion is "every 85 °C part ≤ 85 °C"; LS120's rise is recorded and is not a gate; 48 °C is the pre-test estimate; ORDERING, M3_R10 and owner rows 33 / 36 agree | confirmed |
| R30-TRI-01: R10_VALIDATION §1 bridge figures and the 5.6 kΩ EN load (no REQUIREMENTS text involved) | confirmed |
| R29-TRI-04: LS120 as a +70 °C part in the Temperature row | confirmed |
| R29-TRI-01: Inference labels in F6 / F8 / F9 | confirmed |

## Coverage limits

- No gate, DRC or fab regeneration was run (read-only).
- I did not re-source the HV6120 stall torque or the K850DM masses, and did not re-run the envelope.
- The DB125 temperature rating is not readable in the cached drawing.
- I did not re-query live JLC stock or prices.
