# Round 22: docs binding lens (Claude)

Commit `ec8cb98`; board SHA-256 `5516eeec5b9e79b49d157146baf6f7652cc0fb0fdb9f1c3c13921c26f9d315a1`, the same before
and after the review. Machine-readable twin: `round22_docs_binding.json`.

**Totals: 0 Critical / 0 Major / 4 Minor (all new, all text only).**

## What agrees with the board

- **Identity and counts.** 46 × 90 × 1.6 mm, 2,336,572 bytes; 215 footprints, 983 segments, 0 arcs, 300 vias (167 GND;
  295 / 4 / 1 by size), 1871.611826 mm of track, 122 visible and 93 hidden references, 45 legends. These match
  AGENTS, STATUS, M3_R10, ORDERING 8.1 (VIPPO paragraph), R10_VALIDATION and AVA_LAYOUT. The M3_R10 hidden list
  matches the board's 93 exactly.
- **Parts and positions.** R81 F(18.8482,80.0) and C87 F(18.7232,81.8768) at U9's end of the EN run, and every
  terminal, U1, U4, U5, U9, R166 and LS120 pose, match the board and the CPL. The nine D-R21-09 designator spots match.
- **Pin map and binding.** U1's pad nets, `pin_table.tsv` `r10_net` and `r10_binding_note.json` agree on all 100 pins.
  The note binds `5516eeec…`, and its netlist hash is unchanged from `accfff4`. The IMU pose and lever arm agree in every
  record. The connector pad nets and all 45 silkscreen legends match the handoff terminal table and the port map.
- **Fab and supplier.** The cost, stock and manifest input hashes equal the current BOM, owner BOM (C84 only) and CPL
  (72 top / 133 bottom). $85.37 = $60.58 + $123.93 / 5. The stock check fails on U4 (2 against 5) and U9 (−69, minimum 7).
- **Owner list.** Rows 1–30 are all present and bound to `5516eeec…`. All 172 / 126 / 46 decision IDs reproduce. All 35
  round 21 IDs (6 carried) have a disposition. In the §6 detour table, BAT_ENABLE is 25.58 mm with 3 vias, as on the board.
- **Row 30 and the circuit-check line.** The GND-partner distances 1.866 / 1.875 / 2.902 / 7.467 mm reproduce, as does
  1.423 mm on `0dc84776…`. Single opens between U9.1 and R81 go from 13 (3 vias) to 4 (1 via). The other checks also
  reproduce: 31 3V3 vias, 701 pads, a 0.5505 mm fill gap at J1.2 / J400.2, and EN at 2.063 V with 1 % parts.

## Findings

| ID | Title | Key number |
|---|---|---|
| R22-DOCS_BINDING-01 | Stale supplier figures left after the 23:23Z refresh | R10_VALIDATION §10 gives $102.14 / $105.13 where the other records give $102.16 / $105.15. The ORDERING U4 row cites stock_check 10:13Z (now 23:23Z). DB125-4 stock is given as 37,827 (now 37,757) |
| R22-DOCS_BINDING-02 | parts_qualification's U4 rows predate R21-BOM-02 | They say "9 in stock for 5 (thin: buy at once)" and "consign the LSM only if the ISM stock is gone" |
| R22-DOCS_BINDING-03 | REQUIREMENTS lags two round 21 facts | The acceptance criterion names only U4 (U9 is now short too), and the no-fuse list leaves out C88 (D-R21-03 names it) |
| R22-DOCS_BINDING-04 | "EN never exceeds 2.03 V" is written as an absolute in 7 records | The same files also say ≤ 2.06 V (2.063 V with 1 % parts). Both figures hold only while R81 is intact. parts_qualification also has an ambiguous "8 % of rating" |

## Fix verification

| Item | Verdict |
|---|---|
| D-R21-01 | Confirmed: every plated hole is ≥ 0.5505 mm from inner copper. Row 9's "J400.2 1.050 / 1.050" figures are the S-8 In2 values; In1 GND is 0.550 mm and exempt |
| D-R21-02 | Confirmed (records) |
| D-R21-03 | Partly: the sheet notes are confirmed, but REQUIREMENTS line 101 lags (-03) |
| D-R21-04 | Confirmed: AUD-2 list, AGENTS §3 and row 30 |
| D-R21-05 | Confirmed: poses, one via, 13 → 4, row 24 pairs unchanged. Wording issue in -04 |
| D-R21-06 … -08 | Confirmed (records) |
| D-R21-09 | Confirmed |
| Round 21 docs Minors | Confirmed for DOC-01 … -08, SAF-03 / -04, MEC-01, MFG-02, REQ-03 / -05 / -06 and MCU-01. BOM-02 is partly fixed: parts_qualification still lags (-02) |
| Board binding, rows 1–30, circuit-check line | Confirmed, as far as reproduced |

## Fix now (all text only)

1. R10_VALIDATION §10: change $102.14 / $105.13 to $102.16 / $105.15. In the ORDERING U4 row, change 10:13Z to 23:23Z.
   In ORDERING and R10_VALIDATION, change the DB125-4 stock to 37,757 (36,979 orderable, 23:23Z).
2. parts_qualification U4 rows: 2 orderable for 5. Consign franchised ISM6HG256XTR first; the LSM6DSV320X is only a
   second fallback and is unavailable.
3. REQUIREMENTS line 124: "every short part (now U4 and U9) in JLC stock or consigned". Line 101: add C88 and the Q120
   / R134 path.
4. Seven places: "2.03 V nominal (≤ 2.06 V with 1 % parts, at 8.4 V; Calculation) while R81 is intact". In
   parts_qualification: "8 % of C87's 25 V rating".

## Coverage limits

No datasheet or JLC page was re-fetched. Inner-layer distances are centre-distance approximations. Owner row 8's
21-of-25 count, S-8's 1.021 mm and the §1 surface inventory were not re-derived.
