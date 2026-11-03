# R10 round 35 — mechanics lens (Claude)

Target commit `c3c4249`; board SHA-256 `a0ec075e…2e733c` before and after.

**Totals: 0 Critical / 0 Major / 0 Minor real errors.**

## Checks
- `tools/fit_check.py --profile r10` (probe copy of the report): OK. All eight DB125 terminals 2.976 mm bore margin;
  wire room 5.003 mm on all eight; C32.2 4.536177 mm from (4,44.3); LED2.2 3.807887 mm; L1 3.015825 mm below the
  bottom face; tails 7.558359 mm; J3 −0.45 mm; J440 body to y 23.45; J430 15.05 × 15.70 × 2.10 mm.
- Exposed pads at (4,44.3): LED2.2 3.808, LED1.1 3.860, J2.1 3.880, J2.3 3.987 mm (GND, GND, 3V3, NRST); none within
  5 mm of the other four supports. Five Ø3.2 Edge.Cuts supports at the stated centres; outline 46 × 90 × 1.6.
- ORDERING 8.4 and the handoff: every terminal centre, rotation and wire side, D402, J430, L1, the east 1210 pocket,
  the battery and J440 lead routes, checked against the board with aft = low y, forward = y 90, west = x 0.
- Arithmetic: wire room, 0.5 mm wall (4.493), bend budgets, landing 98–163 g, h + t bounds.
- Plate model re-run (`tools/plate_model.py --profile r10`): 180.8 / 255.6 / 287.8 / 407.0 Hz, 78.6 g, identical to
  the record. Landing loads at a 0.1 mm raster: 125 / 132 / 174 / 213 g (D5), within raster of the recorded figures.

## Findings
None.

## Observations (not counted)
1. Landing and gap figures differ from the record only by raster (0.257 vs 0.261 mm; 132 vs 133 g etc.).
2. h + t < 5.3 mm at x 3.7 computes to 5.365 mm (6.018 at x 4 / 42): conservative rounding.
3. C431 courtyard reaches y 60.045; its body ends at 59.5, inside the y 20–60 pocket.
4. "Not re-run on a0ec075e" refers to recorded evidence (round 29 triage); this re-run matches.
5. r10_place.tsv's (3.7,86) basis comment about J400 is historical.

## Fix verification
R34-TRI-01 is outside this lens; no round 34 correction touched mechanics.
