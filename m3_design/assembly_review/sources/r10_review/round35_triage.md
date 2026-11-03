# R10 round 35 triage

Target commit `c3c4249`, board `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c` before and after (unchanged).

**Verdict: round 35 is clean. 0 real errors (0 Critical / 0 Major / 0 Minor), 0 not reproducible.** All ten lenses reported 0 findings; no observation was promoted.

## Observations re-examined (not counted)

- **DOCS_BINDING obs 0 (R173 at B(16.87,59.70))**: M3_R10:1340 is in 'Board history: interim boards'; R10_VALIDATION:1549 is the round 18 ledger row; :2837 is item (d') explicitly scoped to the measured state on a3144b15 (intro line 2825). Board has B(16.87,59.05), moved by D-R26-02 and recorded in M3_R10 'What the round 26 fix pass changed'. Dated records, true when written; not a current-board statement.
- **DOCS_BINDING obs 3 (adjacency_a3144b15.json, detour.py not tracked)**: Dated method/provenance citations; same class ruled by round 28 triage (untracked_citations sweep); no procedure requires running them.
- **GATE obs 3 (C10 3 mm coat distance has no automated gate)**: ORDERING 8.3 hand-procedure figure, not an AGENTS/REQUIREMENTS design rule; board value 3.017 mm (M3_R10) is above 3 mm; no gate is required to bind it.
- **GATE obs 0 / obs 1 (budget figures and binding-note figures not pinned)**: Classes ruled not a gate miss in rounds 26/28; no stated rule binds every budget or note figure to a check; hand-edited stale budget is caught (rc 1).
- **GATE obs 2 (C80.2 right-angle seed not flagged)**: Corner and its inner corner lie inside C80.2 pad copper, which the right_angle rule exempts; correct behaviour.
- **POWER obs 9 / obs 10, DOCS_BINDING obs 1 / obs 2, SAFETY obs 5 / obs 9, MCU obs 8, REQUIREMENTS obs 14**: Repeats of classes ruled observations in rounds 27-34; nothing new shown.
- **MECHANICS obs 0-4**: Raster differences, conservative rounding, body-vs-courtyard pocket coverage, dated statements, historical placement-basis comment: none false.
- **MANUFACTURING obs 0-4**: JLC 1:6 silkscreen ratio is a preference; U4 outline and D402 M-6 figures consistent with their stated metrics; keep-off list range not contradicted; stackup matches ORDERING section 3.
- **PARTS obs 9 (M3_R10:1047 L1/C88.1 inventory)**: Labelled as the R4-MEC-03 inventory on 877d0199; dated record.
- **SAFETY obs 0-4, 6-8, 10; POWER obs 0-8, 11-16; ROUTING obs 0-3; MCU obs 0-7, 9-14; PARTS obs 0-8, 10; REQUIREMENTS obs 0-13**: Confirmations that reproduce records, or INFO/AUD-2/AUD-10 items already disclosed; no contradiction with a record or rule. MCU obs 14 (AN2606 not re-read) is a coverage limit.
- **Triage own sweep: 'current' pointers**: git grep for 'current results/figures/state/placement' in tracked .md: AGENTS:34, STATUS:9/17/22, AVA_LAYOUT:3-7 reading guide (names Round 26 fix pass for a0ec075e), hotplug.md:3, parts_qualification:13/978/1037/1062 all point to current sources; parts_qualification:970 round 10 USB-only figures recomputed (514.1 uF x 4.7 V = 2.416 mC, 5.33-6.95 ms; 516.1 uF 2.426 mC, 5.35-6.98 ms at 347.7-453.0 mA) and still match the board's capacitor inventory. AVA_LAYOUT:16 'Round 21 ... current CAD candidate' is a dated banner under the newer round 26 banner.

## Triage spot checks (all match)

- PCB SHA-256 a0ec075e... before and after (shasum)
- 216 footprints, 1059 segments, 309 vias (170 GND; 304 0.5/0.3, 4 0.6/0.3, 1 1.0/0.5), 1866.794 mm track (M3_R10 'The board')
- file size 2,369,507 bytes
- 123 visible / 93 hidden references; 44 board silkscreen legends
- positions J1 F(7.4,75.85), J400 F(7.4,65.85), J121 F(7.4,55.85), J9 F(38.6,47.5), J410/J420/J440/J122, U9 B(18.5,81.6), R166 F(23.5,86.3), U4 B(17,45.9) rot 180, U5 B(10.6,49.1), D402 B(4.45,65.9), LS120 F(23,58.5), U1 F(23,43) (AGENTS table)
- R173 B(16.87,59.05), C11 B(17.5,51.45), C10 B(17.5,53.5), R164 B(17.325,55.25) (M3_R10 round 26 table)
- mounting holes (4,4), (42,4), (4,44.3), (3.7,86), (42,86)
- cost_check.json $85.26 / parts $60.47 / feeder $123.93 / min-purchase $61.01 (about $85.80): AGENTS, STATUS, ORDERING 8.1, REQUIREMENTS, handoff, R10_VALIDATION row 14 agree
- ORDERING 8.1 'the $0.34 is JLC price movement on eight lines': diff of f2b8251 vs current cost_check gives exactly 8 lines, -0.3374 USD
- stock_check.json 12:43:17Z: U4 9 stock / 2 orderable; U9 30 / -81, min 7: AGENTS, STATUS, M3_R10, ORDERING 8.1, handoff, R10_VALIDATION agree (ORDERING:720-721 -83 at 01:42:53Z are dated superseded-board rows)
- EN divider 8.4 x 300/(470+470+300) = 2.032 V
- GAP-5 bound 32.653 + 0.2 + 0.5 + 1.5 = 34.853 ms < 36 ms

## Method
Read-only. Board measured with the KiCad pcbnew API on a copy in `.supervisor/r35_triage/`; cost and stock from the committed fab JSON and its git history; prior rulings checked in rounds 27-34 triage JSON. No tracked file changed.
