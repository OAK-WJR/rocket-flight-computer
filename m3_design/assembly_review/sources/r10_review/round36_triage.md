# R10 round 36 triage

Target commit `c3c4249`, board `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c` before and after (unchanged, shasum).

**Verdict: round 36 is clean. 0 real errors (0 Critical / 0 Major / 0 Minor), 0 not reproducible.** All ten lenses reported 0 findings; no observation meets the definition, so none is promoted. With round 35, this is the second consecutive clean round on `a0ec075e…`.

## Observations re-examined (not counted)

- **DOCS_BINDING obs 0 (adjacency_a3144b15.json, detour.py in R10_VALIDATION:2751 / :3033)**: dated method citations in dated sections, not links, and no procedure requires running them; the class ruled an observation in rounds 28 and 35.
- **DOCS_BINDING obs 1 (rounds 35 / 36 named as the planned closing pair)**: true at the commit.
- **R173 at B(16.87,59.70) (root flag)**: no round 36 lens reported it. The dated records (M3_R10 interim boards, R10_VALIDATION round 18 row and item d' on `a3144b15…`) are true when written; board B(16.87,59.05) re-measured, as M3_R10's round 26 table states. Same ruling as round 35.
- **C10 3 mm coat distance with no gate (root flag)**: no round 36 lens reported it; ORDERING 8.3 hand-procedure figure, not a design rule a gate must bind (round 35 ruling).
- **GATE obs A1 / A2, K-binding**: hand-edited budget / binding note caught (rc 1); the shared port_A figure is not pinned by a stated rule (rounds 26 / 28 / 29 / 35 class).
- **GATE B1–B7, D-R26-01 / -02 / -04, D-R27-03, right_angle seeds, baseline**: seeds caught; confirmations.
- **MECHANICS obs 0 (632a9ad3 mode figures)**: labelled as the older board's figures; current re-run within rounding.
- **MECHANICS obs 1 (J3 courtyard 1.67 mm)**: consistent with the stated metric (outer-edge gap).
- **PARTS obs 0–3**: J430 CPL offset intended (jlc_corrections); the session-context AGENTS copy is stale, the committed AGENTS.md is current; R166 band reproduced (0.3378672–0.3825072 Ω, multiplicative 1 % and 800 ppm/K × 65 K); historical R166 section labelled.
- **POWER obs 0–5**: 0.22–0.31 encloses 0.2229–0.3048; U11.2 single via, R167 bleed disclosed; VLOGIC doubled tap; a comment in an unadopted option; IPC-2152 steady-state.
- **ROUTING obs 0–9**: T junctions are not bends; two-end 90° junctions inside pad copper; AUD-2 / power exemptions; routing_inventory binding ruled in round 24.
- **SAFETY obs 0–11**: reproductions of the records; BUZZ_G 0.510 mm not fire-capable (behind 1 k / 10 k); the R120.2 probe single open caught by the same step's BAT_IN − RAW_ACT criterion; S-8 J400.2 0.250 mm row labelled as the round 19 / 20 measurement; single faults under owner rows 1, 2 and 24.
- **MCU obs 0–11, MANUFACTURING obs 0–15, REQUIREMENTS obs 0–19**: confirmations that reproduce records, or prior rulings (U4 outline, stackup, F1 30 s window).

## Triage own sweep

- 'current' / 'latest' / 'newest' pointers in AGENTS, STATUS, M3_R10, ORDERING, handoff, REQUIREMENTS, AVA_LAYOUT and parts_qualification: AGENTS:34 (r10_place.tsv, AVA_LAYOUT), STATUS:22, M3_R10:1291 / 1293, ORDERING:499, parts_qualification:351 all point to current sources. `r10_place.tsv`: all 216 rows match the board positions (0 mismatches).
- Every `Ref F(x,y)` / `B(x,y)` in AGENTS, STATUS, ORDERING, handoff, M3_R10, R10_VALIDATION, REQUIREMENTS and FMEA parsed against the board: all current statements match (pad coordinates re-checked at pad level); the residual mismatches are dated change rows (M3_R10 round 19–24 tables, R10_VALIDATION §6 R19 items) or via positions.
- Owner row 20: 126 indexed decisions (r10_final_deviations.json agent_decisions) + 103 later rows = 229; the 103 table IDs equal the 103 D-R18 … D-R29 headings in R10_DECISIONS exactly; 23 owner mandates.

## Triage spot checks (all match)

1. PCB SHA-256 a0ec075e… before and after; commit c3c4249.
2. 1059 track segments, 309 vias.
3. Eight DB125 terminals, 27 contacts; centres, rotations and pin nets of all eight match the handoff terminal table.
4. Silkscreen: 44 legends (26 F / 18 B); the top / bottom legend split in the handoff (J121 2:E1+, J400 2:SW, J440 2–4, J410 / J420 / J9 pins 2–3, J122 pins 2 and 4 on the bottom) matches.
5. ORDERING 8.3 probe worksheet: C88.1 (18.25,83.56), C82.1 (19.3,78.25), R84.1 (20.775,81.825), R119.1 (11.14,71.1), R120.2 (18.5,73.03), C120.2 (17.1,73.3), R120.1 (18.5,72.17), C24.2 (25.45,48.58), C15.1 (29.05,47.82), TP88 F(35.5,86.4), C84.1 VLOGIC (27.5,81.75): pads and nets match.
6. EN via (17.10,82.80) on BAT_ENABLE; R81 F(18.848,80.0), C87 F(18.723,81.877).
7. Values: R80 / R165 470 k, R81 300 k, C87 220 nF, R166 0.36 Ω, R134 2 Ω, R167 10 k, R126 220 Ω, R128 10 k, C126 220 nF, R127 1 k; D402 B(4.45,65.9) C535146.
8. Vias: J440 GND partners (7.4,16.5) / (7.4,20.0), BAT_IN 1.0 / 0.5 at (17.5,87.15), U401.11 GND (27.3,13.6) / (27.9,13.6), R164 3V3 (19.55,55.825), C126 GND (15.8,59.425), U11.2 RAW_PROTECTED (24.3,66.0), C84 VLOGIC (29.8,81.15), four ACT_GATE barrels, LOGIC_SOURCE_ST (30.45,51.4), 3V3 (28.1,60.0) / (28.1,59.4).
9. Fab: JLC BOM 81 lines, 206 designators, C535146 × 9; CPL 206 rows, 70 Top / 136 Bottom.
10. Cost: 60.47 + 123.93 / 5 = 85.26; + 83.96 / 5 = 102.05; + 14.93 / 5 = 105.04; 85.36 + 0.2306 = 85.59 → $85.60; $0.85 over the $84.41 cap (STATUS, M3_R10, ORDERING, handoff agree with cost_check.json 12:44:13Z; stock 12:43:17Z U4 9 / 2, U9 30 / −81).
11. Calculations: EN 8.4 × 300 / 1240 = 2.032 V; PE4 hold-off 3.6 × 0.9109 / 30.9109 = 0.1061 V pin, 0.1038 V gate; PC1 3.6 × 2 / 33 = 0.218 V; storage 1 Ah / 0.84 mA = 49.6 days; R166 band reproduced; four-stall 5.71 V / 7.50 ms consistent across AGENTS, STATUS, REQUIREMENTS F6, ORDERING 8.3, handoff (7.63 ms only as the labelled 5.73 V figure).

## Method
Read-only. Board measured with the KiCad pcbnew API on a copy in `.supervisor/r36_triage/`; fab CSV / JSON parsed with NumPy's venv Python; documents read at the commit. No tracked file changed; no background job left running.
