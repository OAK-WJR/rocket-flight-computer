# R10 round 26 fix pass: docs lane (2026-11-02)

Brief: `.supervisor/r26_fix_docs_brief.md`, including the root's notes after the CAD lane. After this lane's first
hand-back the root sent a follow-up: bring the docs to the final board after D-R26-04 (R10_DECISIONS, and the updated
`round26_fix_cad.md` / `.json`). The base is `3d8e845`; the CAD lane's working-tree changes were in place when this lane
started. This file describes the final state. The first hand-back described the intermediate `4108e6fa…`; D-R26-04
fixed its two findings on the board.

## Board

The final PCB is `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c`, 2,369,507 bytes, 46 × 90 × 1.6 mm.
Its SHA-256 was checked at the start and the end of the follow-up, and this lane did not change it. The lane measured it
with KiCad 10.0.7 pcbnew, read-only, on copies in its scratch area (Calculation on native geometry):

| Measure | `a0ec075e…` (final) | `4108e6fa…` (intermediate) | `92c3ad59…` (HEAD) |
|---|---|---|---|
| Footprints / segments | 216 / 1059 | 216 / 1058 | 216 / 1057 |
| Vias | 309 (170 GND; 304 at 0.5 / 0.3, 4 at 0.6 / 0.3, 1 at 1.0 / 0.5 mm) | 309 (170 GND) | 307 (168 GND; 302 / 4 / 1) |
| Track length | 1866.794 mm (1866.79397) | 1866.0265 mm | 1867.046 mm |
| References | 123 visible / 93 hidden (C18 added), 44 legends; 167 visible texts | same | 124 / 92 / 44 |
| Copper diff against `92c3ad59…` | 11 segments removed, 13 added; GND vias (7.4,16.5) / (7.4,20.0) added; four vias and C10, C11, R164, R173 moved (as `round26_fix_cad.md` lists) | 11 removed, 12 added | — |
| 3V3 / 3V3A to Q124's gate nets, every layer | PYRO1_GATE_N 1.065 mm (R127.1; R126.1 1.081 mm) and PYRO1_GATE 1.0585 mm (R128.1), both to R164's 3V3 via (19.55,55.825); 3V3A to PYRO1_GATE 1.145 mm (C10.1) | R126.1 to the 3V3 via 0.3306 mm | 0.835 / 0.676 mm; 1.151 mm |
| PYRO1_OUT to 3V3 / 3V3A | 1.0500 mm (J121.1's F.Cu run to R13's via; R173.1–D120.3 1.0511 mm) / 1.0400 mm | same | 0.5135 / 0.5662 mm |
| BUZZ_DRV / PYRO1_OUT | 0.7935 mm (R173.1 to R162.1, B.Cu) | not measured | 0.964 mm (net minimum, a track to R162.1); R173.1–R162.1 0.9939 mm |
| R164's new via, other neighbours | BUZZ_DRV's diagonal 0.2335 mm, LS120.3 (no net) 0.206 mm, R162.2 0.997 mm | — | — |
| PYRO1_CONT_MID to BUZZ_G / RAW_ACT | 0.175 / 0.250 mm (the run); the diagonal 0.2005 mm from Q123.1, 0.386 mm from R134.2 | diagonal 0.165 mm | 0.175 / 0.250 mm |
| C10 to the U5 coat union (Fab / pad envelope; pads alone) | 3.016596 / 3.449036 mm | 2.994136 / 3.425033 mm | 3.333144 / 3.777016 mm |
| Detour (round 21 method) | 116 nets, 1500.8 / 1236.6 mm, 1.214×; 23 nets ≥ +3.5 mm; PYRO1_CONT_MID 10.57 / 6.81 mm (+3.8) | PYRO1_CONT_MID 10.55 / 6.81 mm | 1501.8 / 1237.8 mm, 1.213×; 22 nets |
| Layer-change returns (triage `caps.py`) | 25 vias, 21 over an In2 rail, 13 beyond 4 mm; J440.3 / J440.4 partners 1.500 mm | same | 25 / 21 / 13 |
| Under-body 0603 vias | five (R86, R89, R91, R101, R401) | five | five |
| C84 lands, J3 slots (triage `c84.py`, `j3.py`) | identical output | identical | — |
| S-8 (check_r10 `s8` at 2.3 mm) | minima 1.021 / 1.050 mm; J121.1 to In1 3V3 1.575 mm (1.320 on `92c3ad59…`) | same | — |
| route_check r10 (on a copy) | 0 failing, 0 allowlisted, 5 unrecorded leftovers, 28 bump windows | same categories | — |
| `fab_manifest.py --content` (read-only; the fab files' SHA-256 unchanged) | OK: S-4, 67 + 125 rows rebuilt, worst residual 0.491 mm, 14 placement-only, paste 249 / 381 | OK | — |
| CPL | 206 rows (70 top + 136 bottom), SHA-256 `1f899750…`; C10, C11, R164 and R173 moved | 206 | 206 |
| Drill file `m3-PTH.drl` | 0.300 mm tool: 308 holes | 308 | 306 |
| `parts_budget.json` SHA-256 | `5204280e…` (only its board hash changed) | `706c85a9…` | `f92611a8…` |

Supplier evidence (read from `fab/cost_check.json` and `stock_check.json`, bound to the final BOM, owner BOM and CPL):
- Cost, 2026-11-02T12:44:13Z: $85.26 per board (parts $60.47), $0.85 over the $84.41 cap; about $85.80 with JLC minimum
  purchases (parts $61.01). Fixed fees $83.96 per order ($16.79 per board), plus a $14.93 handling fee JLC may add.
- Stock, 12:43:17Z: U4 9 in stock, 2 orderable against 5; U9 30 / −81, minimum 7; C535146 196 / 189 against 45.

Other figures come from `round26_triage.md` / `.json`, `round26_fix_cad.md` / `.json`, D-R26-01 … -04 (220 IDs; 94
after the ledger) and the regenerated binding note.

Constraints kept: docs only (the ten files below plus this hand-back); no CAD, generator, tool, record or git change.
AGENTS §2 is byte-identical to HEAD (md5 of the text from "## 2." to "## 3.": `e3bdcdaa…`, both). No local absolute
paths were added. Links and anchors: 164 relative links checked in the ten files, 0 bad, plus 147 across `docs/*.md` and
README.md, 0 bad (scripted, GitHub slugs). No link points at the renamed M3_R10 or AVA_LAYOUT round 26 headings.

## Findings

1. **PE4's net next to a 3V3 via (first hand-back; resolved by D-R26-04).** On the intermediate, D-R26-02 had put
   R164's 3V3 via 0.331 mm from R126.1 (PYRO1_GATE_N) on F.Cu. D-R26-04 moved it to (19.55,55.825), so every 3V3 / 3V3A
   item is now at least 1.0585 mm from both gate nets on every layer. The docs describe the fixed state: R10_VALIDATION
   §1 (table and summary) and owner rows 1, 2 and 27; M3_R10's retained deviations; FMEA I-2 / H-2; STATUS; AGENTS.
   `4108e6fa…` now appears only in the round 26 fix-pass history.
2. **C10 against the U5 coat exclusion (first hand-back; resolved by D-R26-04).** C10's envelope is 3.016596 mm from
   the U5 union. ORDERING 8.3 no longer gives the clipping instruction, and C10's whole-part selection stands, with the
   new figure.
3. **D-R26-04's audit pairs.** BUZZ_DRV / PYRO1_OUT at 0.794 mm is disclosed:
   - in R10_VALIDATION §1 (a new row, the paragraph and the summary sentence) and owner rows 1 and 27;
   - in M3_R10 (a new retained-deviation bullet and the next-board item), FMEA, AGENTS, STATUS and AVA_LAYOUT.

   A bridge there may fire an enabled match (Inference), and the cold screen refuses one present at power-up. No
   document claims that every fire-capable pair outside the GND class is at least 1.0 mm. The new via's non-pyro
   neighbours (0.2335 / 0.206 mm) are listed where the docs list the moved items' adjacencies.
4. **Pair figures corrected during the follow-up (this lane's own text).** M3_R10 and R10_VALIDATION §1 had quoted
   "PYRO1_OUT to 3V3 0.5135 → 1.0511 mm" as a net figure. The net minimum on `a0ec075e…` is 1.0500 mm: J121.1's F.Cu
   run to R13's moved 3V3 via, 0.620 mm on `92c3ad59…`. R173.1–D120.3 is 1.0511 mm. Four places had also attached
   `92c3ad59…`'s 0.964 mm to R173.1–R162.1, but 0.964 mm is the BUZZ_DRV / PYRO1_OUT net minimum; R173.1–R162.1 itself
   was 0.9939 mm. Both are corrected (M3_R10, R10_VALIDATION, FMEA). `round26_fix_cad.md` lists the pairs correctly.
5. **Round 26 triage observation (TCR), unchanged.** The 7.31 / 7.18 ms at 70 °C were computed at 5.73 V and not re-run
   at the corrected 5.71 V; the index says so.

## Files and statements changed

### AGENTS.md (outside §2)
- §1 battery row: 8.1 ms at the four-stall 5.71 V; bench run at 5.71 V, limit 7.50 ms, 0.50 ms margin (TRI-02).
- §1 pyro row:
  - D-R26-01's rings;
  - PYRO1_OUT ≥ 1.040 mm and Q124's gate nets ≥ 1.0585 mm from 3V3 / 3V3A;
  - the GND pairs fire by themselves, and BUZZ_DRV at 0.794 mm may (Inference).
- §1 mounting row: the plate was not re-run on `a0ec075e…`.
- §1 manufacturing row: $85.26 / $0.85 over (12:44:13Z), U9 30 / −81 / 7 (12:43:17Z).
- Status paragraph: `a0ec075e…`; D-R26-01 … -04 and the follow-up history; the closing pair is now rounds 27 and 28;
  the cost.
- §3 routing rule: the port UART nets (D-R19-15) and a plated pin's layer change (D-R26-01).

### STATUS.md
- Last-updated date and status lines (board, rounds 27 / 28, 5.71 V figures, cost and stock).
- New "Round 26 review and fix pass" entry with a D-R26-04 bullet. It reports these separately:
  - software tests (R10 267, route 72);
  - DRC / gate (builds A and B, standalone check.sh);
  - simulation;
  - physical tests (none).
- Round 25 entry annotated (5.71 V); 220 decisions.

### docs/R10_VALIDATION.md
- Head, latest review and current PCB; review-round log rows 26, 27 and 28.
- "Round 26: ten lenses" index (TRI-01 and TRI-07 annotated for D-R26-04).
- "Round 26 fix pass": the intermediate's history, the copper diff, final counts and tests, and the docs-lane
  measurement on `a0ec075e…`.
- Owner rows: 1 (gate nets; BUZZ_DRV may fire), 2, 8, 9, 14 (cost), 20 (220 / 94), 21, 24, 25 and 27 (the D-R26-04 fix;
  BUZZ_DRV made nearer and not restored).
- Row 2 residuals; decision rows D-R26-01 … -04; inventory basis; ledger 94 IDs.
- §1: the "On `a0ec075e…`" paragraph (all pair changes and the audit) and the corrected summary sentence. Table rows:
  - the corridor, and BUZZ_G at 0.175 mm with the 0.2005 mm diagonal;
  - the 3V3 / 3V3A rows;
  - a gate-net row ("Closed by D-R26-04");
  - R173.1–R162.1 0.794 mm and R173.2–R162.1 1.133 mm;
  - R173.1–Q124 source via 0.500 mm and R173.2–D120.3 0.415 mm.
- §1 also: S-8 and ring notes.
- §5 QSPI board list; §6 (pad layer-change gate, detour table on `a0ec075e…`, 13 of 21, J440 returns); §7 (123 / 93 /
  167, C18); §8 (plate, 4.493 mm, C84 joints); §9; §10 (cost and stock); §12 (220).

### docs/M3_R10.md
- Summary and board table; "What the round 26 fix pass changed (`92c3ad59…` → `a0ec075e…`)" with a D-R26-04 row and
  C10's before / after pose.
- Review rows, closing paragraph and 220 IDs. Checks bullet: builds 2 and 3 gave the intermediate, and builds A and B
  the final board. Also the fab bullet, hot-plug, switch network and plate notes.
- Cost and stock ($85.26).
- Retained deviations:
  - CONT_MID (0.2005 / 0.386 mm; 1.133 mm to R162.1);
  - PYRO1_OUT;
  - new: PYRO1_OUT to BUZZ_DRV;
  - "Q124's gate nets to 3V3 / 3V3A (closed by D-R26-04)", which replaces the respin bullet;
  - BAT_FAULT_N.
- Next board change; CH1; power; routing evidence (detour 10.57 mm); silkscreen; open items; board history.

### docs/ORDERING.md
- Status; positions (C10 B(17.5,53.5), C11, R164, R173); hole rule and D-R26-01.
- Supplier snapshot (12:43:17Z / 12:44:13Z, CPL `1f899750…`), cost table, U4 / U9 / DB125 / ESD rows; 309 vias (308
  holes in the 0.300 mm tool).
- §8.2: package, 93 hidden, C84 joints with C8, J3 slots with R7, J440 via note.
- §8.3: probe worksheet basis; BAT_FAULT_N board list; C10 3.016596 mm with its whole-part selection; chatter at 5.71 V.
- History row for `92c3ad59…`; closing sentence (`a0ec075e…`).

### docs/REQUIREMENTS.md
- F4 (TRI-06), F6 (TRI-02 / -03 / -04) and F7 (board).
- M1 (stock 12:43:17Z), M2 ("0 failing on `a0ec075e…`") and M3 ($85.26, $0.85 over, about $85.80).
- Tab-reboot bullet, OQ-3 and the status line.

### docs/R10_VEHICLE_HANDOFF.md
- Status (`a0ec075e…`, D-R26-01 … -04); chatter rule (5.71 V, 7.50 ms); plate note.
- Cost and stock ($85.26, 12:44:13Z / 12:43:17Z). The price history now separates D402 from price movement.

### docs/FMEA_REDUNDANCY.md
- H-6 and I-11 name `a0ec075e…`; I-5 (TRI-01's third route).
- I-2 / H-2: the gate nets to 3V3 / 3V3A (D-R26-04, closed) and PYRO1_OUT to BUZZ_DRV (0.794 mm, Inference).

### m3_design/assembly_review/sources/r10_design/parts_qualification.md
- Status line (`a0ec075e…`, D-R26-01 … -04); D402 row (5.71 V figures).
- Supplier evidence ($85.26; U9 30 / −81; C535146 196 / 189); budget bound to `a0ec075e…`.
- Budget SHA-256 `5204280e…`, with its history.

### m3_design/assembly_review/sources/r10_design/AVA_LAYOUT.md
- Reading guide and status note: `a0ec075e…`, D-R26-01..04.
- "Round 26 fix pass (new PCB; D-R26-01..04)" rewritten:
  - identity, and the intermediate's history;
  - copper rows (C10 B(17.5,53.5), R164's via and strap, the C10.2 stub, the CONT_MID path), 11 removed / 13 added;
  - gate nets ≥ 1.0585 mm; the new via's neighbours; BUZZ_DRV 0.794 mm.

## Completeness sweep

A scripted search ran over the ten docs-lane files for every value or phrase replaced in either pass. `git grep -n` then
checked the rest of the repository. Residual hits in the ten files:

| Old value or phrase | Residual hits | Why each stays |
|---|---|---|
| `4108e6fa` | STATUS 1, FMEA 1, M3_R10 3, R10_VALIDATION 6, AVA_LAYOUT 1 | Each names the intermediate in the round 26 fix-pass history (D-R26-02, then D-R26-04) |
| `0.331` (`0.3306` 0), `2.994`, `0.165` | 12, 4, 2 (R10 files) | The same history; the other `0.165` hits are R5 / R7 / R9 boards |
| `1866.026`, `1058` | 1, 1 | AVA_LAYOUT's intermediate sentence. `1866.03`, `2,368,017` and "12 added" (R10 sense): 0 |
| `3.425` | 0 in R10 files | R7_VALIDATION's coordinates (coincidental) |
| `0.491` | current and older boards | The CPL's worst orientation residual (R134), the same on `a0ec075e…`; GEOMETRY_REV_G's 0.4914 mΩ |
| "respin item" in the PE4 sense | 0 | The remaining hits are U9's west cell, U11.2 / 3V3A, closed D-R24-02 items and TRI-01's history |
| `85.30`, `$0.89`, `10:03`, `10:02`, `37ec0e45`, `61.06`, `85.85`, `102.09`, `105.08`, `60.52`, `35,891`, `35,048`, `706c85a9` | 0 (`$0.89`: 1) | ROCKET_FC_FROZEN_DESIGN's $0.8972 unit price, coincidental |
| `R10 266`, `60.77`, `17.9,61.8`, `10.55 mm`, `0.362`, "through D-R26-03", "D-R26-01 … -03" | 0 | — |
| `219` | R7–R9 only | R7–R9's 219 placed parts |
| `53.45` | M3_R10 2, R10_VALIDATION 3, AVA_LAYOUT 2 (lines) | C10.2's via y (current), the intermediate's C10 in history, or the U1.19 GND fragment's y extent (R10_VALIDATION, coincidental); the other hits are R7 / R8 figures (153.45 mΩ) |
| `1.0511`, `0.964` | 3, 9 | `1.0511` is always R173.1–D120.3 (pair-specific); `0.964` is always the BUZZ_DRV / PYRO1_OUT net minimum on `92c3ad59…` |
| `92c3ad59` | many | Each names the board of rounds 25 / 26, a round history or a "before" figure; none states it as current |
| `$85.60`, `$1.19`, `01:43:55`, `01:42:53`, `−83`, `60.81` | history and comparisons | Board-history entries, the round 24 sections, the earlier stock row of U9 and "it was $85.60 at 01:43:55Z on the same BOM" |
| first-pass phrases (`5.73 V`, `8.2 ms`, `7.63 ms`, `5.37 V`, "six" vias, "None of the pairs below …", etc.) | as in the first pass | Unchanged since the first hand-back: deliberate comparisons, dated history and the round 26 index |

Outside the docs-lane files the hits are records or generated text, left as they are:
- R10_DECISIONS (dated decisions, D-R26-02 annotated by D-R26-04);
- `round26_fix_cad.md` / `.json` (the CAD lane's history of `4108e6fa…`);
- `r10_binding_note.json`, `parts_budget.json`, the fab manifest and the hot-plug inputs (all bound to `a0ec075e…`);
- sealed reviews and earlier hand-backs.

## Not done or not verified

- No board, generator, check or record change by this lane.
- BUZZ_DRV / PYRO1_OUT (0.794 mm) stays a disclosed deviation; D-R26-04 records why it was not restored. Whether a
  bridge there fires is an Inference.
- The EN model, the late-block train, the fire corner and D-R26-04's audit are the CAD lane's and the root's
  Calculations. Not re-run here: the TCR limits at 5.71 V, and the plate model on `a0ec075e…`.
- No review of `a0ec075e…` exists yet; rounds 27 and 28 are planned. No physical test.
