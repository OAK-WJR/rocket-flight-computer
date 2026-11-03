# R10 round 29: mechanics lens

Target commit `09a564e`, board `a0ec075e…` (SHA-256 the same before and after). Reviewer: claude.

**Totals:** 0 Critical, 0 Major, 1 Minor.

## Finding

**R29-MECHANICS-01 (doc, Minor).** R10_VALIDATION section 8 (lines 2923–2928) says "all 23 tails of the seven earlier terminals have separate fit allocations" and "J440's four tails were not added to that tail allocation (not re-run)".
- That is false. `tools/fit_check.py --profile r10` adds a tail box for every plated pin of every DB125 terminal (lines 446–454), and `tools/check.sh` runs it on every gate run.
- On `a0ec075e…` it reports 27 tails, J440.1–.4 included, at 7.558 mm each. The minimum is still 7.558359 mm.
- The handoff (line 84) says "all 27 solder tails". Both sentences were written in commit 6628488, when the tool already had this loop.
- Fix (text only): say "all 27 tails of the eight terminals" and delete the "not added / not re-run" sentence.

## What was checked and holds

- **Fit check (re-run).** OK on `a0ec075e…`:
  - all eight DB125 bodies 2.976 mm from the 24.9 mm bore;
  - wire room 5.003–5.603 mm at every terminal;
  - J3 0.89 mm, overhanging the west edge by 0.45 mm;
  - L1 is 3.015825 mm below the board, leaving 0.984175 mm at 4 mm standoffs;
  - C32.2 is 4.536177 mm and LED2.2 3.807887 mm from (4,44.3);
  - J2.1 is 3.880 mm and J2.3 3.987 mm (exact circles).
- **Supports.** Five Ø3.2 mm Edge.Cuts holes at the recorded centres, on a 46 × 90 mm outline.
- **Terminals.** Every terminal's pose, rotation, pin net, colour and bottom-legend side matches the handoff table. D402 is at B(4.45,65.9), between J400's pins (y 64.1 / 67.6).
- **Compass.** Directions follow the records' compass (north = smaller y = aft):
  - the J440 leads stay aft of y 23.5 (envelope ends at y 23.45);
  - the battery leads go round the forward edge, and the J1 / J400 / J121 / (4,44.3) / J3 order is correct;
  - the TP122 coating stays "south/east only", away from U5;
  - the pocket x 31.5–41, y 20–60 contains C411 / C421 / C431 with the ±0.3 mm tolerance.
- **Arithmetic.**
  - Wire room: 3.9 / 4.1 / 5.1 / 5.7–6.5 mm needed, against 4.493 mm with the wall allowance.
  - Nut-inclusive h + t: exact limits 6.018 mm at x 4 / 42 and 5.365 mm at x 3.7, stated as < 6.0 and < 5.3 mm.
  - J9 to J122 at x 42: 6.73 mm.
  - East column: 34 g.
- **Plate model, re-run** (masses.json, profile r10):
  - first modes 180.8 Hz (pinned) and 255.6 Hz (D10); clamped 287.8 / 407.0 Hz; 78.6 g;
  - gaps at 4 mm standoffs: C431 0.261 mm, C421 0.320 mm;
  - contact onset C431 125 g, C421 133 g, C411 175 g, L1 214 g (D10 250 / 265 / 350.5 / 428 g);
  - C128 strain 991 µε.

  All match the records.

## Fix verification

- **D-R28-01 … -04:** no mechanical content.
- **Audit B #17** (34 g east edge, labelled Inference): confirmed.
- **Audit B #3** (R166 courtyard 0.56 mm from C84's): confirmed.
- **Audit B's §8.4 rows and the handoff's sled-pocket box:** confirmed.
- **R27-TRI-06** (J440 leads aft of y 23.5): confirmed.

## Observations (not counted): 8

1. The plate model on `a0ec075e…` is identical to the recorded figures.
2. The records say the model was "not re-run" on the last three boards; review probes did re-run it, with the same figures.
3. The 632a9ad3-labelled 256.1 Hz and 1.24 mm figures differ slightly from the current 255.6 Hz and 1.27 mm.
4. The J9 / J420 tails reach the sled at 162–176 g, inside the pocket; this was already ruled.
5. The C128 and east-edge strains reproduce.
6. The h + t limits are conservative.
7. "C23 courtyard gap 0.575 mm" is measured from J430's envelope; courtyard to courtyard it is 0.45 mm.
8. The J440 to J3 courtyard gap of 1.67 mm is a line-centre figure; polygon to polygon it is 1.73 mm.

Probe files are in `.supervisor/r29_mechanics/` (fit.json, plate.json, defl.py, strain.py).
