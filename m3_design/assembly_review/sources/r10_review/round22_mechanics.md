# Round 22: mechanics (Claude)

Target commit `ec8cb98`. Board SHA-256 before and after: `5516eeec…f9d315a1` (unchanged). Totals: **0 Critical, 0 Major, 1 Minor**.

## Finding

- **R22-MECHANICS-01** (Minor, new; it completes R21-MEC-01): ORDERING 8.2's list of hand-solder keep-offs for each terminal leaves out four bottom parts that fall inside the 1.76–2.17 mm range the bullet itself states.
  - **What was measured.** B.Cu pad edge to THT pad edge for every bottom pad. Every listed figure re-measures exactly.
  - **Missing from the list:**
    - C410, 2.011 mm from J410;
    - C420, 2.011 mm from J420;
    - R102, 2.001 mm from J9 (and 2.299 mm from J420);
    - C431, 2.055 mm from J9.
  - **Just outside the range, also unlisted (2.2–2.5 mm):** R405 and C411 at J410; C128 at J121; C83 at J440; R440/R441, R450/R451 and R100/R101.
  - **J1 and J400.** J1 has no bottom pad within 3 mm. J400's nearest is R131, at 2.85 mm.
  - **Impact.** An assembler following the list could heat or bridge these parts. The damage would be found at first-article inspection; there is no fire or function hazard.
  - **Fix (docs only).** Add C410 to J410's entry, C420 to J420's, and R102 and C431 to J9's. Optionally, add a check that rebuilds the list from the board.

## Fix verification

| Item | Verdict | Measurement |
|---|---|---|
| D-R21-05 R81 / C87 | Confirmed | **Pose diff `0dc84776` → `5516eeec`.** Only R81 and C87 moved, both on top, 0603, rotation 0. Holes, outline and supports are unchanged. **Supports.** The nearest is 15.6 mm away. **C84.** The courtyards are 2.58 mm from C84's courtyard and more than 4 mm from its lands; R166, at 1.15 mm, is still the nearest. **Height.** 0.8 mm. **Strain at 100 g.** About 1.0 millistrain, against 1.15–1.17 at the old spot (Inference). |
| D-R21-01 | Confirmed | Fills only. Wire room is 5.00–5.60 mm on all eight terminals (5.003 nominal) and the bore margin is 2.98 mm. |
| D-R21-09 | Confirmed | R81's designator is about 1.2 mm west of C84's courtyard and not on the can. |
| R21-MEC-01 docs | Partly | The hand-solder rule, the U5 port mask and the TSLP inspection are present. Four parts are missing from the list (finding 01). |
| D-R19-11 U4 | Confirmed | B(17,45.9), rotation 180, pads identical to round 21. Sensor +X = −x and +Y = −y, so roll = −gyro_Y. Lever arm −6.0 mm. |
| Plate model | Confirmed, holds | **Re-run on `5516eeec`.** First mode 180.8 Hz (pinned, D5). Mass 78.58 g. Clearance at 100 g: C431 0.261 mm, C421 0.320 mm, L1 0.524 mm. Identical to round 20. |

## Fix now

- **R22-MECHANICS-01.** Text only: the three list additions in ORDERING 8.2.
- **Record currency (no finding).** Where the records say the plate figures were "re-run on `50a39de5…`", add that round 22 re-ran them on `5516eeec…` with the same results.

## Closed

- **Tallest parts.**
  - Top: C84 at 10.8 mm sits near the axis. The DB125s have a 2.98 mm bore margin; J3 has 0.886 mm, the tightest.
  - Bottom: L1 hangs 3.02 mm below the board, leaving 0.984 mm to a 1 mm plate on 4 mm standoffs. Then come the 2.7 mm capacitors.
  - None of these moved.
- **Supports.** LED2.2 is 3.808 mm from (4,44.3), against the 3.8 mm gate, and C32.2 is 4.536 mm away. Nylon hardware is still required at all five supports.
- **Screwdriver access and microSD.** Both unchanged. Wire the terminals out of the bore, and open the microSD hinge only with the PCB unbolted from the sled.
- **U5 venting.** U5 is unchanged and faces a 2.9 mm gap. The bay must be vented (REQUIREMENTS "Static ports"). Sizing the vehicle static ports for Mach 1.9 is outside the board's scope.
- **Flight loads.**
  - Boost (28–37 g) and recovery shock act in the board's plane, as shear on C84, the DB125s, J3 and LS120. That is covered by the open P3 staking and retention qualification.
  - The transverse 100 g case gives the disclosed 0.261 mm gap under C431.
  - The round 21 fix pass changes neither.

## Coverage limits

- No physical harness, sled, tool, nozzle or hinge test was done, and no DRC was run.
- The plate model uses allowance masses.
- The microSD open-lid sweep was not re-measured; nothing near J430 moved.
- Probes are in `.supervisor/r22_mechanics/`.
