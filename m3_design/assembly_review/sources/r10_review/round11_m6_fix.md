# Round 11 M-6 and port-return implementation receipt

Scope: the 16 bottom-part clearance failures exposed by moving the seven DB125 bodies inward, plus companion C92 placement. This is generated-copy validation, not an independent clean review or canonical release. Root owns R13/core and the servo worker owns the servo slice; the port repair owns the 12 port rows and their local routing/fanout companions.

The prototype starts from frozen native `419a8f49f39ea748a1622ecb5858ba060d1eb2fac7df7e3cca37a72dc6d8fd15`, applies the current placement table, removes the old copper/generated zones and regenerates all six routing families. Inherited generated Fab-reference helper texts are reset before post to avoid seeded UUID duplication on this already post-processed input. All 209 poses, all 973 track segments and all 295 vias match the current placement/dry routing generators. The prototype is not expected to reproduce a fresh netlist-import build byte for byte.

Final post-processed prototype SHA-256: `6b6589254b879dfa66760c550c63b94358ff43b6bcd22057366779b1c7d4d6e6`. The [JSON receipt](round11_m6_fix.json) records all source/output hashes and complete focused-rule evidence. This agent did not write the canonical PCB, run the full build/gate, export a new fab package or perform Git actions.

## Final poses and clearance

All positions are bottom-side KiCad millimetres. The 1.5 mm bottom courtyard/PTH-pad floor is unchanged. Gaps are the project M-6 polygon collision measurements at 0.001 mm resolution, not physical tolerance qualification.

| Ref | x,y | Rotation | Nearest foreign PTH pad | M-6 gap mm |
|---|---|---:|---|---:|
| C411 | 34.2,22.75 | 90° | J410.1 | 1.855 |
| C421 | 33.8,36.75 | 180° | J420.1 | 1.605 |
| C431 | 39.3,57.75 | 90° | J9.1 | 1.805 |
| C91 | 34.95,53.9 | -90° | J9.1 | 1.555 |
| C92 | 32.35,52.5 | 0° | J9.1 | 3.955 |
| D400 | 35.75,43.7 | -90° | J9.4 | 1.586 |
| D401 | 35.75,47.2 | -90° | J9.3 | 1.586 |
| D410 | 35.75,12.3 | -90° | J410.3 | 1.586 |
| D411 | 35.75,8.7 | -90° | J410.4 | 1.620 |
| D420 | 35.75,31.2 | -90° | J420.3 | 1.586 |
| D421 | 35.75,27.7 | -90° | J420.4 | 1.586 |
| R102 | 35.4,39.7 | 0° | J9.4 | 1.561 |
| R13 | 10.25,52.55 | -90° | J121.1 | 1.580 |
| R150 | 34.6,75.9 | 0° | J122.2 | 1.581 |
| R151 | 34.7,72.77 | 0° | J122.3 | 1.536 |
| R152 | 34.7,70.23 | 0° | J122.3 | 1.536 |
| R153 | 34.6,68 | 0° | J122.4 | 1.575 |

The repaired-part minimum is 1.536 mm at R151/R152. The complete-board built-courtyard scan has its inherited minimum of 1.510 mm at C83 versus J3.4. C91’s gate gap is 1.555 mm; its conservative courtyard bounding envelope clears J9.1 by 1.505 mm. The conservative bounding envelopes of C91/C92 and C91/U13 clear by 0.010/0.035 mm; KiCad polygon-collision gaps are 0.110/0.135 mm. These are distinct measurements, both recorded in JSON.

C411 turns 90° and moves forward to clear the SD courtyard and its existing GND via. C431 turns 90° into the free region below J9, clear of TP74. C91 moves forward into the local U13 pocket; C92 moves 0.25 mm west so its pad 1 is centred on the existing x31.65 CAM_IO trunk. U13 and R103 stay in place. C91.1 to U13.1 is 4.092142 mm pad-to-pad with 5.035660 mm of direct 0.4 mm copper. The original-y obstruction is U13/C92’s east courtyard envelope at x33.995, which prevents the required inboard C91 move at that y.

## Routing and return choices

- C411’s PORT_4V8 plane via is (36,23.35) on the direct terminal diagonal; the terminal entry is centred. Its GND via is (34.2,19.75). C421’s supply/GND vias are (35.3,35.25)/(33.8,36.75).
- C431’s GND via is (39.3,55.25). The camera output feed passes below R430 with a 0.4 mm route through (34.2,60.85)/(37.7,60.85), then enters C431.1. Its terminal branch passes west of the capacitor’s GND land through x37.75 and avoids TP74.
- C91’s return is (36.65,55.375); C92’s is (32.8,53.3). The original CAM sense-supply via (34.2,49.325) is preserved.
- D400/D401 return at (34.95,44.025)/(34.95,47.525), west of the F.Cu camera control/supply lanes. D410/D411 return at (36.45,12.625)/(36.45,9.025); their B.Cu wire branches approach pad 1 around the GND pad. D420/D421 return at (35.75,32.225)/(35.75,28.725).
- R405 retains its original local GND via (35.95,15.625). C60/R103 share the new local return (33.2,55). The former (34.9,44.5) coverage stitch is removed because D400’s moved return covers it and otherwise overlaps its ring.
- U1.49’s return moves to (31.85,38.25), clear of C421 paste and the CAM_MCU_TX reference corridor. R102’s return is (37.05,39.7). R431’s return is (37.1,57.875), clear of C431.1.
- C92’s companion status via moves from (31,51.8) to (30.85,51.8), with its two local LOGIC_SOURCE_ST stubs redrawn. A full foreign F/B shape probe at the retained 0.15 mm copper/0.25 mm hole limits found no collision at the new via.
- All retained tracks are octilinear. No rule, allowlist, copper-width floor, part, model, process limit or AGENTS §2 constraint changes. Servo return and centred terminal-entry details are in the servo worker’s receipt.

## Validation actually run

| Check | Result |
|---|---|
| KiCad 10.0.7 native DRC, all severities/all track errors | 0 violations, 0 unconnected; no schematic parity or ERC claimed here |
| Final post | Required 40 legends placed; copper/zones/pads/poses preserved after its initial fill; final saved refill verified |
| M-5/M-6/M-7/P-11/F9-2 | All pass |
| K-legends/K-copper/K-reference/K-region/K-fill/K-retained | All pass |
| Full routing hygiene, R10 profile, exact final prototype hash | 0 blockers, 0 allowlists, 0 stale entries, 0 removable critical bumps; 25 bump windows |
| Current-source dry/native comparison | All 209 poses and all 973 tracks/295 vias match |

Nine noncritical routing leftovers remain informational, with every location retained in JSON: BAT_OVLO short segment; V3V3_SENSE, BAT_FAULT_N, BUZZ_DRV, I2C1_SDA and BAT_ENABLE tiny-jog instances; USB_ILIM detour. None is a newly open port implementation blocker. The full review/deviation record still owns their disposition.

No scoped implementation blocker remains in this prototype. The small conservative courtyard margins above and all electrical/THT/thermal/harness/coating/retention behavior remain physical qualification items. Root’s fresh integrated builds, whole gate, final board/hash binding, hot-plug extraction, reproducibility and fabrication outputs are separate evidence; this receipt credits none of them. R10 remains unaccepted and unordered.
