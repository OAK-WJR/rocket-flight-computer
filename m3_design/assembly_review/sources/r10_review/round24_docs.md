# R10 round 24 docs pass (docs lane, 2026-11-01)

Brief: `.supervisor/r24_docs_brief.md`. Board read from the working tree: PCB
`1407e8506efbac0f664b3aeb65568c32ae9670c9b45b502a465cba1130de522e`, 2,363,869 bytes, 46 × 90 × 1.6 mm. Every count,
part, cost and stock figure was read from the board, `fab/`, `R10_DECISIONS.md` (D-R24-01 … D-R24-17, 207 unique D IDs)
and `round24_board_cad.md` / `.json` (builds C and D). Docs only: no generator, check, CAD, fab or decision file was
edited, and no git state was changed. AGENTS.md section 2 is byte-identical to HEAD (md5 of the section
`5549c80b6abf5f5b5a93fbd61698e178`, both). No local absolute paths were added. Every relative link and anchor in the
ten touched files resolves (scripted check, 0 bad).

## Measured by the docs lane (read-only, KiCad 10.0.7 pcbnew on the working-tree board)

- Hidden references: 92 hidden / 124 visible; the list matches `round24_board_cad.md`.
- S-8 barrels: 12 on 6 nets (two new ACT_GATE barrels from D-R24-02; there were 10 on `5516eeec…`). Wall to foreign
  In1 / In2 copper: 1.021 mm at the PYRO1_OUT via, 1.050 mm at every other protected via and at J121.1 / J400.2, and
  2.1–2.2 mm at the PYRO1_GATE via and J121.2. The 1.0 mm floor holds.
- Residual clearances, unchanged from `5516eeec…`:
  - PYRO1_CONT_MID 0.250 mm to R134.2 and 0.175 mm to Q123.1;
  - PYRO1_OUT 0.177 / 0.180 mm to the GND vias;
  - ACT_EN 0.330 mm to BAT_ENABLE at R123.1;
  - BAT_FAULT_N 0.180 mm to the GND via (27.9,64.25) and 0.380 mm to both 3V3 vias (28.1,60.0) / (28.1,59.4).
- fit_check (profile r10): the nearest bottom envelope is C32.2 at 4.536 mm and the nearest top one is LED2.2 at
  3.808 mm. Both are unchanged.
- Hot-plug rows: 2304; minimum −14.807373 V, steepest fall 8.994764 V/µs, rise 5.087664 V/µs. The R166 extremes
  (579.049 W, 2.979359 mJ) and the retained bound (5.914 V at 1643.90 µF) are unchanged.
- `parts_budget.json` SHA-256 `f734dff7…`: only its board hash changed.
- Supplier-evidence bindings:
  - cost: JLC BOM `00af5358…`, owner BOM `c48868b3…`, CPL `7984d2cb…`;
  - stock: the two BOMs.
- Detour table (fork B, the round 21 lens's method): 116 non-pour nets, 1501.8 / 1237.8 mm, 1.213×.

## Files and statements changed

**AGENTS.md** (§1 rows, the status paragraph, §3; §2 untouched)
- R10 status paragraph:
  - board `1407e850…`;
  - rounds 22 / 23 were the closing pair on `5516eeec…`;
  - the round 24 board pass changed the board;
  - rounds 24 / 25 review it under the strict rule;
  - $85.60, $1.19 over the cap.
- Battery-input row: D402 at J400.2, ahead of R165.
- External-switch row: D402 on BAT_SW_RETURN; EN shift at most 5.7 mV.
- Pad-arming row: D402 is the first layer and the handling rule the second.
- Manufacturing row: 206 placed parts, CPL 67 / 125 + 14, paste 249 / 381, C535146 9 per board, cost, and stock
  (U9 28 / −83 / minimum 7; U4 2 against 5).
- Pyro row: S-8 holds at 12 plated barrels (was 10).
- Mounting row: plate model not re-run on `1407e850…`.
- §3, routing: every bend 45°; route_check `right_angle` fails any 90° bend (D-R24-17).
- §3, silkscreen allowlist: JLC's order-number placeholder dropped (D-R24-13).

**STATUS.md**
- Status lines: `1407e850…`, the closing pair on `5516eeec…`, cost and stock.
- New "Round 24 board pass (2026-11-01)" row, with separate bullets for tests, DRC / CAD gate, simulation and physical.
- 207 decisions.

**docs/M3_R10.md**
- Summary and board table (hash, bytes, contents, silkscreen 124 / 92 / 44, fab package).
- New "What the round 24 board pass changed" table. The round 21 heading now names `0dc84776…` → `5516eeec…`.
- Review table: rows "24 board pass" and "24 and 25 | Planned". The closing-pair paragraph is rewritten.
- New round 24 checks bullet. The fab package is bound to `1407e850…`.
- Hot-plug bullet: new extremes; the "every row unchanged" text is removed.
- Plate model: not re-run on `1407e850…`.
- Cost and stock:
  - 2026-11-02T01:42:53Z / 01:43:55Z, with the new input hashes;
  - $85.60 (parts $60.81 + feeder $24.79); about $86.14 / $102.39 / $105.38;
  - fails by $1.19 ($85.36 before D402);
  - U9 28 / −83 / minimum 7; C535146 201 / 194 against 45.
- Retained deviations:
  - the residual clearances are marked re-measured;
  - row 22 feeds kept (D-R24-06);
  - U9 EN re-measured (D-R24-05; respin with the OVLO divider);
  - IC grounds: U402.2 and the monitor taps fixed, U10.2 / R7.2 / R85.2 and R8.2 still single;
  - J400 ESD closed by D402 (5.7 mV, about 14 mV on C87, failure modes, handling as the second layer);
  - more single points: BOOT0, VCAP2 and Q120 / Q121 fixed; VCAP1 and U4.6 / U4.7 kept;
  - "Next board change" rewritten from the D-R24 kept items, with a "fixed in round 24" list;
  - tabs: D-R24-14's measured reason and owner rows 16 / 28.
- CH1 pyro: S-8 on `1407e850…`, 12 barrels, the re-measured wall figures. Fire budget bound to `1407e850…`.
- Power:
  - C88's new place;
  - D402 in the switch network;
  - R92 F(31,86.7) and C82's second via (21.1,78.25);
  - the C82 / D9 path figures labelled as round 11–14 measurements;
  - hot-plug extremes.
- Routing evidence:
  - new current `1407e850…` paragraph: `right_angle`, PARALLEL_VIAS, 5 leftovers, the U401 FB T residual at 0.075 mm
    inside R402.1 with its two alternatives, detour 1.213×;
  - `5516eeec…` becomes "Previous".
- Silkscreen: counts and the 92-reference hidden list.
- Open items: rounds 24 / 25 under the strict rule; OQ-3 at $85.60 and the new stock figures.
- Evidence: 207 D IDs; round 24 records.
- Board history: new `5516eeec…` entry (2,336,572 bytes, 215 / 983 / 300 (167), 1871.611826 mm, 122 / 93 / 45,
  $85.37).

**docs/ORDERING.md** (fork A)
- Line 33 and §8 / 8.1:
  - counts, cost and stock (lines 226–302);
  - the order-mark remark dropped, and Mark on PCB "None" (D-R24-13);
  - 307 vias;
  - D402 keep-off;
  - DFM queries (D-R24-15).
- §8.3:
  - probe points;
  - the ESD text rewritten (D402 first, handling second);
  - the `5516eeec…` history row.

**docs/R10_VEHICLE_HANDOFF.md** (fork A)
- Board identity, D402 / J400 network, cost and stock (lines 8, 23, 55, 60, 123–125).
- Plate line: not re-run on `1407e850…`.

**docs/REQUIREMENTS.md** (fork A)
- F8: the pad set {J400.2, R165.1, D402.1}.
- F9: ESD closed by D402.
- M2: the 45° rule and `right_angle`.
- Status lines 82, 132, 135.

**docs/FMEA_REDUNDANCY.md** (fork A)
- D402 as the first ESD layer (lines 10, 36, 41, 86).

**docs/R10_VALIDATION.md** (fork B, plus the S-8 count)
- Head and review-round log rows. New "Round 24 board pass" section.
- Owner preamble.
- Owner rows:
  - rows 14 / 16 / 20 / 22 / 27 / 28 / 29 updated;
  - row 35 closed (D-R24-13);
  - the decision rows for D-R24-01 … -17.
- R22-REQUIREMENTS-03 / R23-SAFETY-06 dispositions closed by D-R24-11.
- §6: `right_angle`, 5 leftovers, the FB T residual, the detour table re-run.
- §7: silkscreen; §9 / §10: cost and stock.
- S-8 paragraph: 12 barrels.
- Not re-measured by the forks: row 9's S-8 figures (the docs lane measured them above: unchanged) and row 30's
  partner-via figures.

**parts_qualification.md**
- Status line: `1407e850…`, the closing pair, rounds 24 / 25.
- New "Round 24 component amendment" with:
  - a D402 row: part, place, tap, leakage with the Infineon product-page URL, 5.7 mV, the Inference labels, the survey
    and the cost;
  - the board totals, cost and stock;
  - C88 / R402 / R403 / R92 / TP88.
- The round 19 cost line is marked superseded.
- `parts_budget.json` bound to `1407e850…` (SHA `f734dff7…`).
- The ESD list includes D402.

**AVA_LAYOUT.md**
- The reading guide points to "Round 24 board pass".
- New section at the end:
  - board identity;
  - a change table checked against the `r10_place.tsv` diff (C88, R402, R403, R92, TP88, D402) and D-R24-02 … -17;
  - the kept items;
  - silkscreen.

## Not done or not verified

- The plate model and row 30's partner-via figures were not re-run on `1407e850…`.
- The C82 / D9 loop paths were not re-measured.
- No review of `1407e850…` exists yet. Rounds 24 and 25 are planned.
