# R10 round 24: parts lens (claude)

Target `f2b8251`, board SHA-256 `1407e850…` before and after (unchanged).

**Totals: 0 Critical / 0 Major / 0 Minor.** No real error found.

## Fix verification
- **D-R24-11 (D402): confirmed.** ESD103-B1-02EL E6327 / C535146 / M3_TSLP_2_20 agree across the schematic, circuit.json,
  place.tsv, board, BOM (line 8 → 9, still 81 codes) and CPL (B(4.45,65.9), CPL 90, same relation as the other eight
  TSLP clamps). Land matches Infineon Rev 1.3 Fig. 14 (copper 0.35 × 0.6 at 0.65 mm, stencil 0.28 × 0.45 at 0.66 mm);
  B.Paste flashes present. Ratings: VRWM ±15 V against J400.2 = 5.216 V nominal (5.256 V with 1 % parts; 7.8 V for a
  wrong 3S pack); IEC contact ±10 kV; −55…125 °C. EN shift 5.69 mV (= 25 nA at the 227 kΩ EN Thevenin) and C87's 14.3 mV
  recomputed and correct.
- **C88 (D-R24-17): confirmed.** C307331 100 nF 50 V X7R 0402, B(18.67,83.56), CPL 180; within rating on BAT_IN.
- **R402 / R403 (D-R24-09): confirmed.** 49.9 k / 10 k 0.1 % on B.Cu, CPL 180 / 0; Vout 0.8 × (1 + 4.99) = 4.792 V;
  paste 249 / 381.
- **R92 / TP88 (D-R24-15): confirmed.** R92 3.3 k 0603 at 21 mW against 0.1 W; TP88 stays out of BOM and CPL.
- **D-R24-12: confirmed.** No land or Fab change to the 14 parts.

## Checks
Full BOM ↔ board check (all 81 lines: footprint, LCSC, MPN, Qty; only merged comments differ on the C25744 / C21190
lines), full CPL ↔ board check (206 rows, 70 / 136; only J3 / J430's documented offsets), JLC model ↔ MPN for all 82
stock lines, cost arithmetic ($85.60, $16.79), datasheet tables and figures, paste Gerber, docs counts.

## Observations (8, not counted)
See the JSON: merged BOM comments, uniform CPL rotation families, M-6 gap re-measure (1.762 / 1.802 mm by my estimate
vs 1.768 / 1.808 recorded), tap geometry, hotplug.md bound to the round 11 board, cost arithmetic.

Coverage limits: unchanged lines' LCSC pages and lands not re-read; no live supplier fetch.
