# R10 round 31: docs_binding lens

Target commit `3366287`, board `a0ec075e…` (SHA-256 `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c`
before and after). Binding note `c5cd0fa3…`, budget `4267634…`. Strict real-error rule (`.supervisor/r31_review_brief.md`).

**Totals: 0 Critical / 0 Major / 0 Minor real errors.** No false statement, broken link or broken anchor found.

## What was checked
- Board facts (pcbnew, read-only): 216 footprints, 1059 segments, 309 vias (170 GND; 304 / 4 / 1 by size), 1866.794 mm,
  2,369,507 bytes, 123 visible / 93 hidden references, 44 legends; all as M3_R10 "The board" and AVA_LAYOUT.
- Every `<ref> F/B(x,y)` statement in the ten docs against the board: 31 regex mismatches, all dated history
  or a via / track coordinate, none a current claim.
- 184 relative links / anchors: 0 broken.
- Binding note and `pin_table.tsv`: 100 / 100 U1 nets match; hashes of board, pin table and circuit match; the
  firmware obligations' board facts (second ACT_GATE barrels, dividers, pull-ups, C85, U5 address straps) match.
- Copper distances (own polygon dump): PYRO1_OUT to GND / BUZZ_DRV / 3V3 / 3V3A, gate nets to 3V3 / 3V3A, EN-node
  pairs, In2 rings, mid-support lands: all agree with the records within the 5 µm polygon approximation.
- Fab package and supplier evidence: BOM 81 / 45 Extended, CPL 206 (70 / 136), C535146 × 9, manifest bound to
  `a0ec075e…`; cost arithmetic and the eight-line price movement between runs reproduce.
- Review-round tables (rounds 24–30 per-lens counts, 108 / 107 observations) and decision counts (126 + 103 = 229).

## Fix verification
- R30-TRI-01: confirmed (own solve 2.205 / 2.191 V, 0.107 / 0.109 mA; EN load 5.6 kΩ).
- R30-TRI-02: confirmed in every listed place; residual "LS120 ≤ 70 °C" text is quoted history with the pointer.
- Round 30 records and D-R29 binding note: confirmed.

## Observations (not counted)
7, in the JSON: dated positions (R101, R173) in history paragraphs; a conservative U4 coating outline; R62 / R63
absent as stated; legend hyphen typography; provenance probe-file names; polygon-approximation offsets.

## Coverage limits
Check-run records were not re-run (read-only); datasheet pages not re-opened; not every history sentence re-derived.
