# R10 round 28: mechanics lens (Claude)

- **Target:** commit `19dd0b5`. Board SHA-256 `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c` before and after (unchanged).
- **Method:** read-only. Probes are in `.supervisor/r28_mechanics/`. Machine-readable copy: `round28_mechanics.json`.

## Totals

**0 real errors: 0 Critical / 0 Major / 0 Minor.**

## What was checked

- **Bore fit (P2).** fit_check `--profile r10` passes on the committed board.
  - J3 margin 0.886 mm. Each DB125 body has 2.976 mm.
  - 27 tails, with at least 7.558 mm of bore clearance.
  - Wire room is 5.003–5.603 mm on all eight terminals. That is √(25.4² − 5²) − 19.6 − 0.3. With the 24.9 mm radius it is 4.493 mm.
  - The bend arithmetic (3.9 / 4.1 / 5.1 / 5.7–6.5 mm) and the 3 mm-height figures (5.32 / 4.82 mm) reproduce.
- **Supports and keep-outs.** The five supports are as recorded.
  - Nearest bottom part: C32.2 at 4.536177 mm. Nearest top part: LED2.2 at 3.807887 mm.
  - LED1.1 is 3.860 mm away. J2.1 is 3.880 mm and J2.3 is 3.987 mm (exact circular lands). The washer-edge margin is 0.31–0.49 mm.
  - (4,4) to J440's envelope is 3.93 mm. The nut-inclusive h + t bounds are 6.018 and 5.365 mm, against the stated 6.0 and 5.3 mm.
  - L1 hangs 3.015825 mm below the board, leaving 0.984 mm at 4 mm. U5 leaves 2.9 / 3.0 mm.
  - J9 and J122 are 6.73 mm apart. The retention N figures match.
- **P1.** The board is 46 × 90 mm, and J3 overhangs by 0.45 mm.
- **P3.** The landing load from 6.2–8.0 m/s works out at 98.0–163.2 g.
- **Compass, ORDERING 8.4 and the handoff.** Every direction and coordinate matches the board (north = smaller y = aft; west = small x). This covers:
  - the terminal centres and rotations, pin order and nets, and wire-entry faces;
  - D402 B(4.45,65.9);
  - the bottom / top legend list;
  - the J440 route (aft of y 23.5; J3 at y 26.3–35.3, J121 / J400 further forward);
  - the battery route (round the y 90 forward edge, into J1 from the west);
  - the relief-pocket window, which contains C411 / C421 / C431.
- **Plate model (re-run on `a0ec075e…`).**
  - Modes: 180.8 Hz pinned D5, 78.6 g.
  - Gaps at 100 g: C431 0.261 mm, C421 0.320 mm.
  - Contact loads: 125 / 133 / 175 / 214 g (D5) and 250 / 265 / 351 / 428 g (D10). Every recorded figure reproduces.

## Fix verification

| Item | Verdict |
|---|---|
| R27-TRI-06: J440 leads "aft of y 23.5 (y < 23.5 …)" in ORDERING 8.4 and the handoff, with errata in round20_mechanics / round19_fix_docs | Confirmed |
| D-R26-01 GND vias under J440 | Confirmed: no fit change |
| D-R26-02 / -04 bottom moves (C10, C11, R164, R173) | Confirmed: support clearances and plate unchanged |

## Observations (7, not counted)

1. The plate re-run reproduces every recorded figure. "Not re-run on `a0ec075e…`" is true of the records.
2. The maximum deflection is now 1.27 mm and D10 is 255.6 Hz. The records' 1.24 mm / 256.1 Hz are labelled as `632a9ad3…` figures.
3. The east-column strain values (1221–1489 µε) are now available. No requirement sets a limit.
4. The J9 / J420 tails touch at 162–176 g (D5). The round 25 / 26 triage already judged this; they sit inside the pocket window.
5. Two historical sections, M3_R10:1009 and R10_VALIDATION:3124, still give C10 as 3.333144 mm. The current ORDERING 8.3 gives 3.016596 mm.
6. Three gate seeds were tried: LED2 −0.1 mm, C32 −1.1 mm and J440 −0.5 mm. The gates catch all three (fit_check, fit_check, and check_r10 P-11).
7. The U4 body crossings re-measure as recorded.
