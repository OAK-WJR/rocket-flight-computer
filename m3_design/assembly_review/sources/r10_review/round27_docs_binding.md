# Round 27 docs-binding review (Claude)

Target commit `816038c`; board SHA-256 `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c` before and after (unchanged).

**Totals: 0 Critical / 0 Major / 0 Minor.** No false current-board statement and no broken link or anchor was found.

## What was checked against `a0ec075e…`
- Board metrics (216 footprints, 1059 segments, 309 vias / 170 GND / 304-4-1 sizes, 1866.794 mm, 123 / 93 references, 44 legends, 2,369,507 bytes); the 93-name hidden list in M3_R10 is identical to the board.
- Part and probe coordinates (24 footprints, 13 probe pads, 5 mounting holes), terminal pad inner rings, silkscreen legends.
- 24 net-pair minima and 6 via-specific distances quoted in AGENTS, STATUS, M3_R10, R10_VALIDATION §1, FMEA and AVA_LAYOUT (pcbnew shape distance, all layers).
- pin_table `r10_net` vs U1 pads (100/100); binding-note hashes; fab CPL/BOM rows, cost and stock JSON against every cost/stock statement; parts_budget hash; check_r10 rule count (37); decision count (220 = 126 + 94).
- Link/anchor check over the ten Markdown files: 0 broken.
- EN drop-out recomputed at 5.713 V: 8.07 ms (matches).

## Fix verification
| Change | Verdict |
|---|---|
| D-R26-01 | Confirmed: vias at (7.4,16.5)/(7.4,20.0); 4P pins 3/4 carry no inner rings |
| D-R26-02 | Confirmed: PYRO1_OUT to 3V3 1.0500 mm, to 3V3A 1.0400 mm; moved parts and CPL rows match |
| D-R26-03 | Confirmed: 5.71 V, 8.07 ms, 7.50 ms, rule 8 corner in binding note and docs |
| D-R26-04 | Confirmed: gate nets 1.0585 / 1.065 / 1.145 / 1.600 mm from 3V3 / 3V3A; BUZZ_DRV-PYRO1_OUT 0.794 mm |

## Observations (not counted)
- M3_R10 line 997 (section headed historical) keeps C10 3.333 mm / C11 2.818 mm; current figure 3.017 mm is stated elsewhere.
- R10_VALIDATION §1 cites ARM1_SENSE segment (29.75,45.5)… on `5516eeec…`; now starts at 45.85 (chamfer); 0.150 mm minimum unchanged.
- BAT_FAULT_N's nearest 3V3 item is 0.175 mm (R89.2 to via (23,70)); docs quote a specific via (28.1,60.0) at 0.380 mm, which is correct.
- In2 3V3 / RAW_PROTECTED 0.300 mm is labelled to `0dc84776…`.
- C10 envelope method approximated, not re-implemented exactly.

Coverage limits: historical round sections not re-verified line by line; §6 detours, S-8 minima, plate and hot-plug figures not re-measured; datasheets not re-read. Probes: `.supervisor/r27_docs_binding/`.
