# R10 round 36 — mechanics lens (Claude)

Target `c3c4249`, board `a0ec075e…` (SHA-256 identical before and after).

**Totals: 0 Critical / 0 Major / 0 Minor real errors.**

## Checks
- `fit_check --profile r10` re-run (report in the probe directory): OK. J3 0.89 mm margin and 0.45 mm west overhang;
  all eight DB125 bodies 2.976 mm; L1 3.015825 mm below the bottom face; C32.2 4.536177 mm and LED2.2 3.807887 mm from
  (4,44.3); wire room 5.003 mm on all eight terminals; 27 tails, 7.558359 mm bore margin, 2.20 / 1.80 mm.
- Five Ø3.2 mm Edge.Cuts holes at the P1/P2 positions; top lands near (4,44.3): LED2.2 3.808, LED1.1 3.860,
  J2.1 3.880, J2.3 3.987 mm.
- Plate model re-run on the current fit report: 180.8 Hz pinned D5, 78.6 g; C431 / C421 gaps 0.261 / 0.320 mm at
  h = 4 mm; onsets C431 125 (250) g, C421 133 (265), C411 175 (351), L1 214 (428); h = 3.5 mm overlaps. All match.
- Nut bound h+t: 6.018 mm at x 4/42, 5.365 mm at x 3.7 (stated < 6.0 / < 5.3). Wall-allowance room 4.493 mm.
  Bend arithmetic recomputed. Relief pocket covers the three 1210 boxes.
- Compass (y 0 aft, y 90 forward) and every position in ORDERING 8.4 and the handoff agree with the board
  (J440 body end y 23.45, J3 y 25.3–36.3, J9–J122 gap 6.73 mm, east edge 82 mm / 34 g).

## Fix verification
- R34-TRI-01 is docs-only and outside this lens; round 34 made no mechanics correction.

## Observations (not counted): 2
- M3_R10 quotes the older board's D10/clamped modes and 1.24 mm deflection, labelled as such (current 255.6 / 287.8 /
  407.0 Hz, 1.27 mm).
- "J3 courtyard 1.67 mm" is the outer-edge courtyard gap; correct as stated.
