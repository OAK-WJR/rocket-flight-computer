# Round 20: mechanics (Claude)

Target commit `6628488`. Board SHA-256 before and after: `50a39de5…cbd976` (unchanged). Totals: **0 Critical, 0 Major, 2 Minor**.

## Findings

- **R20-MEC-01** (Minor, new): no lead path is given for the J440 (AUX) harness on the shared west edge.
  - **Where the leads can go.** J440's wires leave at x 3.40, y 11.0–21.5, in the aft-west corner.
  - **Forward:** they would cross the USB-C plug zone (about y 24.6–37.0), ride over the (4,44.3) support head (which covers the whole edge strip at y 40.5–48.1), and then run beside the J121 igniter and J400 switch exits. ORDERING 8.4's dressing rules forbid that: the J400 pair stays on its own ties, and the radio harness stays away from the CH1 cell.
  - **Aft:** they would enter the battery-lead and camera-shroud zone right at the OQ-7 boundary (joint + 47).
  - **Fix:** a docs row in ORDERING 8.4 and the handoff. Run J440 leads aft over or around the (4,4) nylon head, stay south of y 23.5, and leave past the aft edge on the side away from the shroud, tied to the sled. Never run them forward along x = 0. The same route applies if the GPS or radio is moved to J440.
- **R20-MEC-02** (Minor, new): the plate-model figures predate J440.
  - **Re-run on `50a39de5`:** f1 is 180.8 Hz (pinned, D5), against 181.1 in the records. Modelled mass is 78.6 g, against 70.5 g. At 100 g the C431 gap to a 4 mm standoff plane is 0.261 mm (records: 0.271); C421 is 0.320 mm. Peak strain is 1184 µε at J440 and 1121 µε at C445.
  - **Second stale statement:** ORDERING 8.4 says the 2.976 mm body/bore margin was "measured before J440". fit_check now gives 2.98 mm for J440 as well.
  - **Fix:** refresh these numbers in the docs.

## Round 19 fix verification

| D-ID | Verdict | Measurement |
|---|---|---|
| D-R19-14 placement | Confirmed | J440 envelope is 3.93 mm from the (4,4) washer. Courtyard to J3 is 1.73 mm (the record says 1.67). Wire room 5.003 mm, bore margin 2.98 mm, M-6 2.45 mm. |
| D-R19-08 | Confirmed | Smallest ink-to-envelope distance is 0.133 mm (inner east column). Every top legend is outside the envelopes. |
| D-R19-12 | Confirmed | Terminal designators reach 0.060–0.087 mm under their envelope edges. J122's designator is 0.67 mm clear. |
| D-R19-11 | Confirmed | U4 land, pose and position are identical to the previous board. DS15034 p9 Figure 5 matches DS14623 p9. Roll = −gyro_Y, lever arm x = −6.0 mm. |
| D-R19-07 | Confirmed | C84 lands have no paste. The land ends stick out 0.75 mm for the iron; R166 is 1.15 mm away. |
| D-R19-03 | Confirmed | TP121 is gone, so one fewer bare bottom pad sits under the sled. |
| R19-MEC-01 / -02 docs | Confirmed | ORDERING 8.3 has the continuity check and 8.2 has the C84 heat limit. |

**Fix now (CAD):** none.

## Closed or rejected

- **J440 3:TXO bottom legend:** it sits 0.5 mm toward pin 2. The gate metric assigns it to pin 3, and the continuity check covers it anyway.
- **Bottom legends under the sled:** covered by the same continuity check.
- **Panel tab at J440's exit:** ORDERING already says to file tab stubs flush.
- **Supports:** nylon hardware is required at all five. J440 adds no exposed copper within 3.8 mm of any support.
- **Tallest parts, screwdriver access, microSD hinge, U5 venting, C445 flex:** unchanged, or already covered by documented physical qualifications.

## Coverage limits

No physical harness, sled or tool fit was done. The USB-C overmold size is an Inference. The microSD open-lid sweep was not re-measured. No 3D render was made; legend checks are ink-polygon measurements. Probe scripts and outputs are in `.supervisor/r20_mechanics/`.
