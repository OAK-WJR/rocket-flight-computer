# R10 round 26: docs binding lens (Claude)

Target commit `3d8e845`, board SHA-256 `92c3ad59174afe1ffe206f6384c8cd9a8962e09647ccd6a8c418b95b5312056f` before and
after (unchanged). Read-only; probes in `.supervisor/r26_docs_binding/`.

## Totals

0 Critical / 0 Major / 0 Minor. No false current-board statement and no broken link or anchor found.

## What was measured against the documents

- **Board** (read-only pcbnew): 216 footprints, 1057 segments, 307 vias (168 GND; 302 / 4 / 1 by size), 1867.046187 mm
  track, 2,363,951 bytes, 46 × 90 × 1.6 mm, four layers; 124 visible / 92 hidden references (hidden set identical to
  the M3_R10 list), 44 legends. Five support circles at the stated centres.
- **Positions:** every `Ref F/B(x,y)` and bare `(x,y)` in AGENTS §1, the handoff, ORDERING §8, the current M3_R10
  sections, FMEA's R10 section and REQUIREMENTS was matched to a footprint, pad, via or track end. The only
  non-matches are before → after records or sit under headings that name older boards.
- **Nets and pinouts:** all terminals, D402, the U9 EN cell, the Q120–Q124 gate networks, the sense banks, LS120 and the
  sensors. `pin_table.tsv` `r10_net` matches all 100 U1 pads. The binding note's board hash and IMU pose match.
- **Legends:** every terminal pin legend's text, side and pin as in the handoff table.
- **S-8 and holes:** 12 barrels on 6 nets; plated pad holes are at least 0.5505 mm from inner copper.
- **Gaps:** U9.1 to BAT_IN 0.200 mm; EN via to BAT_FAULT_N 0.200 mm; ACT_EN to BAT_ENABLE 0.330 mm; J440.1's In2 ring
  to 3V3 0.2505 mm. Mid-support lands are 3.808–3.987 mm from (4,44.3).
- **Fab package:**
  - BOM 81 lines (45 Extended / 36 Basic); CPL 206 rows (70 / 136); paste 249 / 381.
  - The manifest binds the board and all six outputs.
  - Cost $85.60: parts $60.81, feeder fees $24.79, fixed $16.79 per board, with minimum purchases $86.14.
  - Stock: U4 9 / 2; U9 28 / −83 / 7; C535146 201 / 194 against 45.
  - The run timestamps match every document that quotes them.
- **Gate and tests:**
  - check_r10 has 37 rules.
  - Test methods: shell 11, fab_validation 34, fit 33, paste 16, r10_parts 5, route 71, R10 263.
  - R10_DECISIONS has 216 unique IDs, 90 of them after the ledger.
  - The `parts_budget.json` hash matches.
  - Round 25 totals: 14 raw findings; the triage kept 10 real errors and 72 raw observations.
- **Links:** every relative link and anchor in the in-scope files resolves to a tracked target.

## Fix verification

| Change | Verdict |
|---|---|
| D-R24-18 BAT_FAULT_N chamfer (0.200 mm to the EN via; segment ends as AVA_LAYOUT states) | confirmed |
| D-R24-20 M-8, exactly six short-edge DFM queries at the recorded distances | confirmed |
| D-R24-21 BOOT0 second via cited as D-R24-03 | confirmed |
| D-R24-22 S-5 names J400.1 / J400.2 | confirmed |
| D-R24-23 round24_board_cad CPL 70 + 136 | confirmed |
| D-R24-11 D402 pose, nets, 4.114 mm tap, GND via, 9 per board in the BOM and supplier files | confirmed |

## Observations (not counted)

- R10_VALIDATION §6 keeps R19-RTE-04's list of vias under part bodies (R403 F(31.4,14.4), removed by D-R24-09). It sits
  under a heading that names `a3144b15…`, so it is history.
- The silkscreen prints `E1-` (hyphen) where the docs write `E1−` (minus). Same legend.
- M3_R10 puts the $85.36 → $85.60 step down to D402 alone, while ORDERING also cites price movement. Both agree with the
  files to rounding.
- `PYRO1_GATE_N` is active high; every document already says the `_N` is historical.

## Coverage limits

- R10_VALIDATION and REQUIREMENTS were swept by pattern (coordinates, counts, hashes, cost, stock, links), not read line
  by line.
- Calculated figures (EN timing, hold-up, chatter, plate, wire room, hot-plug) were checked for cross-document
  consistency only.
- Test counts are method counts; no test run.
