# R10 round 29, manufacturing lens (Claude)

Target commit `09a564e`; board SHA-256 `a0ec075e…` before and after (unchanged).

**Totals: 0 Critical / 0 Major / 0 Minor real errors.**

## What was checked
- **DRC:** kicad-cli 10.0.7 on a probe copy, all severities, exclusions and schematic parity, gave 0 / 0 / 0. A run with `--refill-zones` (not saved) gave 0 / 0, and the copy's hash did not change. No severity is set to ignore, and there are no exclusions.
- **Gerber and drill:** regenerated with `export_fab.py`'s options. All 14 files match the zip apart from their dates. Drill tools:
  - PTH: 0.3 × 308, 0.5 × 1, 0.6 × 4 (J3 slots), 1.3 × 27;
  - NPTH: 0.6 × 2, 0.991 × 3;
  - Edge.Cuts: five 3.2 mm routed holes.
- **JLC capabilities (re-read 2026-11-02).** Each limit, with the board's worst case:

  | JLC limit | Board |
  |---|---|
  | Via hole-to-hole 0.2 mm | 0.259 mm |
  | Pad hole-to-hole 0.45 mm | 3.593 mm pad to pad, 0.700 mm pad to via |
  | NPTH ≥ 0.5 mm | 0.6 mm |
  | Plated slot ≥ 0.35 mm | 0.6 mm |
  | PTH annular ring ≥ 0.20 mm | 0.20–0.30 mm |
  | Silkscreen 0.15 mm lines / 1.0 mm text | met |
  | Mask web 0.10 mm | 0.150 mm (U4) |
  | Inner-layer PTH hole to copper | 0.55 mm rule, DRC 0 |

- **REQUIREMENTS M2:**
  - Every via hole is at least 0.125 mm from a soldered pad's opening, except the two GAP-3 U401 vias.
  - Courtyards enclose their pads.
  - The six GND THT contacts carry zone_connect = 1.
- **Package content:** the manifest verifies, and S-4, `jlc_orient --verify-cpl` (67 + 125 reconstructed, 14 placement-only, residual 0.491 mm) and paste_check (249 / 381) all pass on the committed files. The BOM and CPL agree with the board:
  - 206 rows (70 top / 136 bottom), 81 codes (45 Extended / 36 Basic);
  - LCSC and MPN fields match the board;
  - C84 appears only on the owner BOM;
  - TP* and J2 are excluded.
- **Assembly PDFs:** every footprint's designator is present on its side.
- **ORDERING 8.1 / 8.2 figures, all reproduced:**
  - vias 309 = 304 + 4 + 1;
  - 93 hidden designators;
  - 14 parts without a Fab body;
  - 13 bottom pin legends;
  - the terminal table and the confirm-list poses;
  - L400's land and C84's lands;
  - U4's mask web and its 88.4 % paste;
  - the hand-solder list, which is complete (the next part, R405, is at 2.243 mm);
  - the J3 slot list;
  - the J440 partner vias at 0.300 mm;
  - the six short-edge DFM parts;
  - the tab nearest-part gaps of 3.155 mm;
  - the cost arithmetic and the stock rows.
- **ORDERING 8.3:** every probe-worksheet coordinate and net, and TP122's box, reproduced.

## Fix verification
- **Round 28 fix pass:** the BOM, CPL and owner BOM are byte-identical to round 27, and the manifest is re-bound to `a0ec075e…`. D-R28-01 … -04 have no effect on the fab package. Confirmed.
- **Audit B:**
  - #2 (3.155 mm): confirmed.
  - #3 (C84 to R166, 0.560 mm): confirmed.
  - #4 (TP83, 411–617 µF against 35–53 µF): confirmed.
  - #5 (8.739 / 13.390 mm): confirmed.
  - #10 (ESD test with a dummy load and no e-match): confirmed.
  - #11 (Q120 probe points and nets): confirmed.
  - #13 (step 4 rule): confirmed.

## Observations (not counted): 12
They are listed in the JSON:
- method confirmations;
- pdftotext merging two Fab reference pairs, whose ink boxes are 0.26–0.28 mm apart;
- J3's courtyard extending 1.035 mm past the edge, against the shell's disclosed 0.45 mm;
- merged BOM comment strings;
- the gbrjob stackup thicknesses, which are informational.

## Coverage limits
- No live JLC DFM run, quote or supplier query.
- The capability numbers come from a page summary.
- The PDFs were checked by text extraction, not by raster inspection.
- The stackup name was not checked.
- §8.4 and the handoff were checked only for the audit B items.
