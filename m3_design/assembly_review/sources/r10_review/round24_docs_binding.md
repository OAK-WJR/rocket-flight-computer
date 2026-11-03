# R10 round 24 review: docs binding lens

Target commit `f2b8251`; board SHA-256 `1407e8506efbac0f664b3aeb65568c32ae9670c9b45b502a465cba1130de522e` before and
after (read-only). Reviewer: Claude. Scope: STATUS.md, AGENTS.md §1, the six R10 docs, parts_qualification.md,
AVA_LAYOUT.md, pin_table.tsv, r10_binding_note.json and the round 24 records, checked against the board (pcbnew) and the
fab package.

**Totals: 0 Critical / 0 Major / 5 Minor** (all kind doc).

## Findings

| ID | Severity | What is false | Evidence | Fix |
|---|---|---|---|---|
| R24-DOCS_BINDING-01 | Minor | BAT_ENABLE via (17.1,82.8) to BAT_FAULT_N is stated as 0.200 mm, "re-measured … unchanged" (M3_R10 292, 306–307), "not changed" (R10_VALIDATION 2252), row 24 (2092), FMEA H-6 (36), ORDERING coating (570) | F.Cu chamfer segment (16.55,82.99)–(16.91,83.35), 0.2 mm wide, is **0.173 mm** from the via on `1407e850…`; 0.200 mm on `5516eeec…` (D-R24-17 chamfer) | Write 0.173 mm in the five places; drop "unchanged" / "not changed" for this pair |
| R24-DOCS_BINDING-02 | Minor | ORDERING 416: "14 pin legends are on the bottom" | Its own list has 13; B.Silkscreen has 13 terminal pin legends (14 top + 13 bottom = 27) | "13 pin legends" |
| R24-DOCS_BINDING-03 | Minor | R10_VALIDATION 2659 (§9 C84 row): "paste F 253 / B 375" | Gerbers and PASTE_TOTALS: 249 / 381 on `1407e850…` | Update to 249 / 381 |
| R24-DOCS_BINDING-04 | Minor | round24_board_cad.md 56 and .json `cpl.sides`: "Rows per side go from 69 top + 122 bottom to 67 + 125" | CPL rows are 72 + 133 → 70 + 136; 69 + 122 → 67 + 125 are the orientation-reconstructed parts (+ 14 placement-only) | State both |
| R24-DOCS_BINDING-05 | Minor | STATUS.md 5: "Last updated 2026-10-31 (R10 candidate section …)" | The R10 section's status and round 24 entries are dated 2026-11-01 (lines 10, 16) | 2026-11-01 |

## Fix verification (D-R24 changes in this lens)

- D-R24-02 docs (S-8 12 barrels on 6 nets, ACT_GATE vias, walls 1.050 / 1.021 / 2.1 / 2.2 mm): confirmed.
- D-R24-03 / -04 / -07 / -08 / -10 via positions, SINGLE_OPEN_EXCEPTIONS 11: confirmed.
- D-R24-09 R402 / R403 on B.Cu, three vias gone, OUT via (29.75,11.65): confirmed.
- D-R24-11 D402 pose, nets, 4.114 mm tap, 0.7 mm return, BOM 9 per board, 5.7 mV and 14 mV arithmetic, Infineon 50 nA / 21 V: confirmed.
- D-R24-13 no order mark (44 legends): confirmed. D-R24-15 R92 / TP88: confirmed.
- D-R24-17 counts (216 / 1057 / 307 (168; 302 / 4 / 1) / 1867.022756 mm), C88, 0 plain 90° bends: confirmed; but the
  chamfer's BAT_FAULT_N clearance change is not carried into the docs (finding 01): **partly**.
- Fab and supplier docs (81 lines / 45 Extended, CPL 206 = 70 + 136, orientation 67 + 125 + 14 by a read-only
  `jlc_orient --verify-cpl`, paste 249 / 381, manifest hashes, $85.60 / $86.14 / $102.39 / $105.38, U4 / U9 / C535146 /
  C2757925 stock): confirmed.

Also matched: every footprint pose vs `5516eeec…` (only C88, R402, R403, R92, TP88 changed; D402 added), the 92-reference
hidden list, U1's 100 pins vs `pin_table.tsv`, the binding note's four hashes, five supports, test counts, 0 broken links.

## Observations (not counted): 7

U10 island "holds two vias" (one GND + one VBUS_SENSE) wording; the board-pass JSON's "67 + 125, 206 rows"; RAW_ACT–USB_OVLO
0.177 mm and ACT_GATE–BAT_SW_SOURCE 0.663 mm now (docs give labelled older-board figures); 35 pad / via 90° nodes
(routing lens); D402.1 not named in the coating list (suggestion); row 24's 0.5205 / 0.5008 mm vs 0.5197 / 0.500 measured.
Full text in the JSON.

## Coverage limits

Docs-binding only; historical sections of R10_VALIDATION and M3_R10 were sampled, not read line by line; plate, hot-plug
and route_check not re-run; supplier figures checked against the committed JSON only.
