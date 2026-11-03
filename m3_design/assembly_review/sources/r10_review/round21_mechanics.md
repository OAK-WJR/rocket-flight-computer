# Round 21: mechanics (Claude)

Target commit `accfff4`. Board SHA-256 before and after: `0dc84776…454940d3` (unchanged). Totals: **0 Critical, 0 Major, 1 Minor**.

## Finding

- **R21-MEC-01** (Minor, new): the R10 THT remark allows selective soldering and names no bottom-side keep-offs.
  - **What the board has.** On the bottom face, which is the THT solder side, U5's open pressure port and every port ESD clamp sit 1.76–2.17 mm (B.Cu pad edge to THT pad edge) from DB125 holes:
    - J121: R13 1.763 mm, U5.8 2.172 mm. U5's lid is 5.94 mm from J121.1.
    - J440: D440 1.867 mm, D441 1.905 mm, R90 1.956 mm, TP82 2.105 mm.
    - J410: D410 1.774 mm, D411 1.812 mm.
    - J420: D420 / D421 1.774 mm, C421 1.855 mm.
    - J9: D400 / D401 1.774 mm, C91 1.805 mm.
    - J122: R150–R153 1.83–1.90 mm.
  - **Gate.** M-6 (≥ 1.5 mm) passes.
  - **The gap.** ORDERING 8.2 says "Hand/selective solder, not wave" but lists no keep-offs, as R9's J3 note did. "Protect U5's open pressure ports" appears only in the no-washing bullet. TE (MS5611-01BA03, Cleaning) asks that the opening be protected from particles and that the board not be cleaned.
  - **Impact.** Typical selective-nozzle keep-outs are 3–6 mm (Inference, from forum guidance; no JLC figure was found). If JLC uses selective soldering, the TSLP clamps can shift or bridge, and spatter can reach U5's port. With no wash, it cannot be removed.
  - **Fix (docs only).** Ask for hand soldering of the DB125 bodies unless JLC confirms a nozzle keep-out under 1.7 mm. Add the keep-off list above. Mask U5's port during J121's soldering. Inspect the TSLP clamps after THT.

## Fix verification

| D-ID | Verdict | Measurement |
|---|---|---|
| D-R20-09 D440/D441 | Confirmed | Only D440, D441 and TP82 moved relative to `50a39de5`. The clamps hang 0.32 mm below the bottom face (bore margin 5.60 mm) and are more than 4.5 mm from every support. They are 4.15 mm from the west-aft tab corner. Their new GND vias are tented. DRC: 0 violations, 0 unconnected. |
| D-R20-04 TP82 | Confirmed | 2.105 mm (copper edge) from J440.4 and 3.9 mm from J430's courtyard, so it is outside the hinge window. It sits under the non-conductive sled. |
| D-R20-02 via | Confirmed | Tented; no mechanical effect. |
| D-R20-06 3:TXO | Confirmed | 3.14 mm to pin 3 against 4.31 mm to pin 2. |
| D-R19-14 | Confirmed | fit_check: wire room 5.003 mm on all eight terminals; DB125 body margin 2.976 mm; J3 0.886 mm; terminal tails 7.56 mm (1.80 mm to a 4 mm standoff plane); LED2.2 3.808 mm against the 3.8 mm gate. |
| D-R19-11 U4 | Confirmed | Pad centroids give sensor +X = −x, +Y = −y, +Z = −z, and the pad nets match DS15034 p9 Fig. 5. Roll = −gyro_Y; lever arm −6.0 mm. |
| D-R19-07 C84 | Confirmed | No F.Paste on either land; nothing moved near C84. |
| D-R19-03 | Confirmed | TP121 is absent. |
| R20-MEC-01 / -02 | Confirmed | The docs carry the J440 route row and the refreshed plate figures. |

**Fix now:** R21-MEC-01 (ORDERING 8.2 text only).

## Closed

- D441 against J3's shell legs: no J3 copper within 2.3 mm.
- The 3:TXO / R463 ink gap of 0.203 mm: already recorded.
- Tallest parts, microSD hinge, U5 venting, C84 access and screwdriver access: nothing in these zones moved.
- Plate model: the clamp move changes the mass negligibly (Inference).

## Coverage limits

- No physical harness, sled or nozzle check.
- The plate model and the microSD open-lid sweep were not re-run.
- Probes are in `.supervisor/r21_mechanics/`.
