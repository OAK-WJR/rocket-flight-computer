# R10 round 31 — mechanics lens (Claude)

Target commit `3366287`, board `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c` (SHA-256 identical before and after).

## Totals

Critical 0 / Major 0 / Minor 0. No real error found.

## Findings

None.

## Fix verification

- **R29-TRI-03** (R10_VALIDATION §8 tails): fit_check on `a0ec075e…` allocates 27 tails, minimum 7.5583594 mm; §8 states all 27 tails and 7.558359 mm — **confirmed**.
- **R29-TRI-01** (labelling of the plate model's 125 / 133 g): owner row 32 and ORDERING 8.4 label them Calculation / Inference; the re-run gives 124.7 / 132.4 g — **confirmed**.
- **R30-TRI-01 / -02**: outside this lens; no mechanical figure, position or mass changed — **not applicable**.

## Observations (not counted)

- fit_check (profile r10): OK, 0 issues. Every mechanical figure in P1 / P2, ORDERING 8.4, the handoff, M3_R10 and R10_VALIDATION §8 reproduces:
  - J3 0.886 mm, 0.45 mm past the west edge;
  - DB125 bodies 2.976 mm; 27 tails 7.558359 mm, 2.20 mm below the board, 1.80 mm to a 4 mm sled;
  - L1 3.015825 mm below the bottom face;
  - wire room 5.003–5.603 mm;
  - C32.2 4.536177 mm and LED2.2 3.807887 mm from (4,44.3).
- Exposed lands at (4,44.3): LED2.2 3.808, LED1.1 3.860, J2.1 3.880 and J2.3 3.987 mm, as recorded. No other support has an exposed pad within 5 mm. Nearby vias are tented, and fills stop 0.50 mm from the hole edges.
- Plate model re-run on `a0ec075e…`:
  - first mode 180.8 Hz (D5 pinned) and 78.6 g, both identical to the records;
  - at 100 g with 4 mm standoffs: 0.261 mm under C431 and 0.320 mm under C421;
  - contact onsets 125 / 133 / 175 / 214 g (D10: 250 / 265 / 351 / 428 g);
  - at 3.5 mm standoffs C431 and C421 overlap, L1 and C411 do not.
- Terminal tails reach a 4 mm sled at about 162 g (J9.3), before C411 (round 30 observation). Both recorded remedies still cover the 98–163 g landing range with the tails included: with the pocket, the first contact is J122.5 at 209 g; with 4.5 mm standoffs it is C431 at 173 g.
- Hardware arithmetic re-derived: plate-only h + t < 6.882 mm; with the nut, 6.0184 / 5.3653 mm. The standoff and washer gates, wire room, bend room, landing g and stack position (joint + 79.4–83.4 mm, matching VEHICLE.md) all reproduce.
- Compass (x east, y forward): every terminal centre, rotation, wire-entry side, pin order and top / bottom legend matches the records. So do these positions:
  - J440's forward body end at y 23.45;
  - J3 between J440 and (4,44.3);
  - the battery route round the forward edge;
  - the pocket window, which contains C411, C421 and C431;
  - D402, J430, L1 and U5 (1.100074 mm).
- J440–J3 and J430–C23 courtyard centre-line gaps are 1.73 and 0.46 mm. The records' 1.67 and 0.575 mm use other bases; the second was already round 29 observation 7.

## Checks executed

- `shasum -a 256` of the board before and after.
- `tools/fit_check.py --profile r10` (report in `.supervisor/r31_mechanics/`).
- `tools/plate_model.py --profile r10` with `masses.json`.
- Probe scripts `gaps.py`, `tails.py` and `probe1.py`–`probe5.py`: pads near supports, legends, vias and fills, courtyards and contact onsets.
- The placement history of J3, J440, C23 and J430.
- Hand arithmetic.

## Coverage limits

- CAD envelopes and the inferred plate model only; there is no physical fit, weighing or vibration evidence.
- No DRC or full gate on the canonical tree.
- Not reviewed: the ORDERING 8.3 procedures, the electrical figures in the 8.4 rows and the 8.1 tab plan.
