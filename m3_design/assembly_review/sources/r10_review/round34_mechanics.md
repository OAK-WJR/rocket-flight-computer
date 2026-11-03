# R10 round 34: mechanics lens

Target `c2a11fd`, board `a0ec075e…` (SHA-256 before and after `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c`).

**Totals: 0 Critical / 0 Major / 0 Minor.** No real errors found.

## Checks
- fit_check --profile r10 on a probe copy: OK. Terminal body/bore margin 2.98 mm (all eight), J3 0.89 mm, shell 0.45 mm past the west edge, tail clearance 7.56 mm, worst bottom margin 5.60 mm.
- Wire room 5.003 mm (4.493 mm with the wall allowance), recomputed by hand.
- L1 3.016 mm below the bottom face; 0.984 mm at 4 mm standoffs.
- Support distances from (4,44.3): C32.2 4.536, LED2.2 3.808, J2.1 3.880, J2.3 3.987 mm.
- Plate model re-run on `a0ec075e…`: 180.8 Hz pinned D5, 78.6 g; gaps at 100 g C431 0.261, C421 0.320 mm; contact at 125 / 133 / 175 / 214 g (D10 250 / 265 / 351 / 428 g). All match.
- Compass (+y forward) and every position in ORDERING 8.4 and the handoff (J440 forward end 23.45, J3 y 26.3–35.3, west-row order, pocket x 31.5–41 / y 20–60) match the board.
- h + t limits (< 6.0 / < 5.3 mm) are conservative against a hand bound of about 6.02 / 5.37 mm.

## Fix verification
- R33-TRI-01: U9 pads 5 / 6 and 9 measured; 0.15–0.25 mm exposure as now stated. Confirmed.

## Observations
11, in the JSON; none counted.
