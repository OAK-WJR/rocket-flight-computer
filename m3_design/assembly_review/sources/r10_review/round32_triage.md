# R10 round 32 triage

Target commit `3366287`, board `a0ec075e…` (SHA-256 checked before and after; unchanged). Read-only; probes in
`.supervisor/r32_triage/`.

**Totals:** 2 raw findings (R32-MANUFACTURING-01, R32-PARTS-01), 3 verified real errors, all Minor (0 Critical / 0 Major),
none on the board. 0 not reproducible. 132 observations in the ten reports; 11 re-examined, none promoted.
**Round 32 is not clean.** No fix changes copper or placement.

## Real errors

| ID | From | Kind | Severity | What is false | Fix | Board change |
|---|---|---|---|---|---|---|
| R32-TRI-01 | R32-MANUFACTURING-01 (part 1) | doc | Minor | "R166's courtyard is 0.56 mm from C84's". Own pcbnew probe: C84 F.CrtYd y ≤ 83.75, R166 y ≥ 84.40 (line width 0.05): 0.65 mm centreline, 0.60 mm outer edges, 0.66 mm KiCad polygon. 0.56 mm is only the SHAPE_POLY_SET.BBox() figure (83.795 / 84.355), inflated about 0.05 mm per side. Not rounding. | 0.56 → 0.65 mm (0.60 mm between the lines' outer edges) at ORDERING:435 and R10_VALIDATION:3063; annotate R10_VALIDATION:1685. Historical review records (round19_mechanics, round28_audit_proc:59, round29_mechanics) stay as written; the fix record cites the correction. | No |
| R32-TRI-02 | R32-MANUFACTURING-01 (part 2) | doc | Minor | R10_VALIDATION:3063 says ORDERING 8.2 "limits the time and temperature, asks for top-side preheat". ORDERING 8.2:436 asks for top-only heating with the bottom supported, a minimum dwell, and asks for the tip temperature to be recorded. It sets no preheat and no temperature limit, and has not since round 19 (`6628488`). round19_fix_docs.md:38 records the same preheat. | Reword :3063 to "limits the dwell time and asks for the tip temperature and time to be recorded, for top-only heating with the bottom supported on a heat-sinking fixture, and for re-inspection …". | No |
| R32-TRI-03 | R32-PARTS-01 | doc | Minor | "The fitted 85 °C parts (MS5611, the AP6320x bucks, J430[, the U4 alternates])" is a definite list with no "include". It omits U3 (W25Q128JV "I": −40…+85 °C), Y1 (NX3225GA STD: −40…+85 °C), LED1 (−30…+85 °C), LED2 (−40…+85 °C) and the 16 fitted X5R MLCCs (Samsung code A, X5R: 85 °C). The same owner row 33 logs C6 / C7, C89, Y1 / U3 and names X7R as the remedy. | At R10_VALIDATION:2494, M3_R10:496 and parts_qualification.md:40: "The fitted 85 °C parts (among them MS5611, the AP6320x bucks, J430, U3, Y1, LED1 / LED2 and the 16 X5R MLCCs C6–C11, C19, C20, C22, C23, C28, C80, C89, C92, C95, C96; the U4 alternates if fitted) …". | No |

Sibling sweep: `git grep` for "0.56 mm" with R166 / C84 / courtyard, for "preheat", and for "MS5611, (the )?AP6320x" over the
tracked text. Every hit is listed above. No other bounding-box courtyard figure is quoted in the docs.

## Observations re-examined (not counted)
- Gate obs 2 (obligation 15). 166–196 V/s reproduces from SLVSEA3F Table 9-1: 780 × 100/470 = 166 V/s and
  92 × 1000/470 = 196 V/s. The citations are right. An unpinned sub-figure only lets an arbitrary edit through, which is not a gate miss.
- Parts obs 4. $85.26 in cost_check.json matches AGENTS, STATUS and ORDERING. The $85.60 figures are dated history (01:43:55Z).
- Mechanics obs 1 / 3: the contact list is not claimed complete; the stated h + t limits are conservative.
- Safety obs 9 / 10, power obs 4, routing obs 11, requirements obs 7 / 16 and MCU obs 15 fall into the classes the rules exclude:
  the stated board basis, rounding or shape approximation, an existing cited revision, or a method difference.
- The other 121 observations are reproductions that agree with the records, classes earlier rounds already ruled on, or disclosed residuals.
