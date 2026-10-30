# Round 17 - placement and mechanics

Fresh full independent lens 6 on commit `ac483f40d38db6e0424227bd32d2a5d5f9f60c3e`.
PCB before/after: `632a9ad36c19426ede219b6ff6b0d638955665cac1b4704d3392a6afdbe03982`.
All 1,966 frozen files remain byte-identical. Result: **0 Critical, 0 Major,
4 Minor** (three carried groups, one new source-attribution correction).
Detailed measurements, source hashes, all 122 decision IDs/23 owner scopes and
closed hypotheses are in [round17_mechanics.json](round17_mechanics.json).

AGENTS was read first. Current requirements, all R10 decisions through
D-R16-03, AVA handoff, M3/validation/ordering records, plan and read-only
`../../docs/VEHICLE.md` were considered under their amendments. This is a whole
mechanics review, not transfer of prior review conclusions. D-R16-03 retains
the board for Minors; no design change or optimization search was performed.

## Findings

**R17-MEC-01 - Minor, carried: remaining component-side MEMS stress departure.**
Exact segment/rectangle clipping on the native B.Cu geometry, subtracting U4's
lands, gives these nominal-body portions:

| Net | Coordinates / portion outside lands, mm |
|---|---|
| IMU_CS | (15.500,44.700)-(16.260,44.700):0.760000; then to(16.325,44.765):0.091923882 |
| SPI1_MISO | x18.210,y44.650-44.975:0.325000 |
| IMU_INT1 | x18.210,y46.825-47.150:0.325000 |
| 3V3A | x15.790,y46.825-47.150:0.325000 |

The signal widths are 0.20 mm and supply 0.25 mm. These depart from
[ST TN1383 Rev1 pp7-9](https://www.st.com/resource/en/technical_note/tn1383-pcb-design-guidelines-for-mems-sensors-stmicroelectronics.pdf)
outside-body, pad-axis and equal-width stress guidance. Fresh geometry confirms
the four GND escapes now leave along individual pad axes and join outside the
body; their 0.0025 mm straight land-to-body boundary portions are distinct from
the transverse under-body routes above. No under-body via/fill failure was found.
This is an advisory offset/stress risk, not demonstrated failed sensing. Fix:
retain the measured deviation and first-article bias/temperature/vibration and
process qualification; preserve CAD/generators under D-R16-03.

**R17-MEC-02 - Minor, carried: stale vehicle candidate row.**
`../../docs/VEHICLE.md:39` still names GH ports, ARM/IGN terminals, GH-2 J400
at(10.5,85.5) and 0.03 mm mated clearance. Native J400 is F(7.4,65.85), -90deg;
all seven wired connectors are DB125, with no ARM link/GH/header/tie holes.
Current [vehicle handoff](../../../../docs/R10_VEHICLE_HANDOFF.md) and
[ORDERING section8](../../../../docs/ORDERING.md) correctly supersede that row.
Fix: apply the handoff through the separately authorized vehicle workflow,
preserving R9 history; do not edit that other worktree in this review. This is
integration ambiguity, not proof of an installed collision or section2 failure.

**R17-MEC-03 - Minor, carried residual with a fresh metric correction.**
The complete native courtyard walk reproduces 16 graphic stroke-overlap pairs
(6 top/10 bottom), with separate native polygons by 0.010-0.040 mm and nominal
body-model gaps >=0.499938 mm. All pairs/coordinates are in the JSON. For
example C421/U12 at B(32.6875,38.350) has 0.010 mm polygon gap. Both native
graphic widths are 0.050 mm, giving 0.040 mm graphic penetration. The active
R10_VALIDATION section7 table reports 0.050 mm there; its penetration cells
consistently use a 0.060 mm combined-width convention, 0.010 mm greater than
the current native stroke calculation. Fix the numeric values or label that
inflated convention, and retain all pairs for owner/assembler first article.
No modeled body collision is demonstrated; no Minor placement change is proposed.

**R17-MEC-04 - Minor, new: U5 height source attribution.**
[ORDERING:545](../../../../docs/ORDERING.md) calls 1.1 mm the U5 maker maximum.
The complete [TE MS5611-01BA03 06/2017 p15 Fig18](https://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocFormat=pdf&DocLang=English&DocNm=MS5611-01BA03&DocType=Data+Sheet&PartCntxt=MS561101BA03-50)
shows 1.0 mm +0/-0.10. The native model at B(10.6,49.1) allocates
1.100074 mm below the PCB. This overstatement is conservative: the retained
2.9 mm cover allowance at h4 is smaller than the package-only 3.0 mm gap.
Fix the attribution, retaining 1.1 mm as a conservative model allocation if
desired. Actual solder seating, foam compression, venting and light rejection
remain unqualified; no CAD/model change is needed.

## Fresh geometry and source checks

[DORABO T0-1 sheet1,2022-11-26](https://atta.szlcsc.com/upload/public/pdf/source/20251124/8C215F69B14C8E54AE0F8E5023D4AE9F.pdf)
was inspected as a complete rendered page. It gives depth7.40, rear datum3.90,
interlock0.42, N*3.5 length, height8.60 and tail3.50+/-0.30 mm. Applying the
sheet's general tolerance bands independently reproduces the conservative
local unions (mm):

| Positions | Local x | Local y | Height |
|---|---|---|---|
| 2 | -4.62..3.70 | -4.10..4.00 | 8.90 |
| 4 | -8.32..7.20 | -4.10..4.00 | 8.90 |
| 5 | -10.07..8.95 | -4.10..4.00 | 8.90 |

For example the maximum wire face is7.70-3.70=4.00 mm, not the rear datum.
These are unions of distinct tolerance corners, not one body's dimensions.
Independent native-pose transforms match the model bounds within quantization.
All seven outward terminals give bare-bore wire room
sqrt(25.4^2-5^2)-19.6-0.3 = **5.003011866 mm**, 0.053011866 above OQ-1's
4.95 mm floor. Maximum adjacent 4P bodies retain0.480 mm axial gap;
west 2P bodies retain1.680 mm. Body/bore clearance is2.976268566 mm after
the0.5 mm wall allowance and both0.3 mm centring tolerances.

The wire-room benchmark is separate from P2's complete installed fit: using
usable radius24.9 and worst z5.3 gives4.429406 mm at that illustrative height.
An ideal vertical ray above the screw row has only9.962463 mm above the
8.9 mm body before the usable bore. Neither calculation qualifies an actual
ferrule, wire bend, screwdriver, staking fillet or tightening method. Maker
28-16 AWG,4-5 mm strip and0.2 N*m maximum do not supply those envelopes.

All23 native contacts have 1.90 mm lands/1.30 mm drills and independent
3.80 mm tail allocations in fit, conservatively using pad XY boxes. Minimum
tail/bore clearance7.558359 mm; projection below1.60 mm PCB2.20 mm, leaving
1.80 mm to a nominal h4 sled. This is an allocation, not solder/seating/form
or insertion-process qualification. The conditional pin/hole tolerance and
fabricated S-8 allocation remain explicitly open; no insertion failure is proved.

The outline is46x90x1.6 mm with the exact five specified supports, no sixth
support/tie holes. Fresh minima are bottom C32.2 to(4,44.3):4.536177 mm and
top LED2.2:3.807887 mm against3.5/3.8 mm. The smallest bottom-courtyard/THT
pad gap is C83 to J3.4:1.510 mm against1.5 mm. All modeled body AABB pairs
are separate. These boxes are simplified envelopes, not comprehensive physical
part/placement/tolerance certification.

With the stated6.35 mm across-corners nut,2.4 mm nut thickness and0.4 mm
screw protrusion, the nut-inclusive equation independently gives h+t<6.018413
at x4/42 and <5.365256 at x3.7. Retain conservative <6.0/<5.3 and selected
h4/t<=1, nut below sled/head above PCB. At h4/t1 the radial reserve is only
0.145392 mm at x3.7. Actual hardware maxima, hole eccentricity, staking and
strength remain open. J2 service still requires removing the adjacent mid support.

J430 B(24,24.3),0deg has the [Molex SD-47219-001G sheet1](https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/salesdrawingpdf/472/47219/472192001_sd.pdf)
15.05x15.70x2.10 mm closed allocation including nails and general tolerances.
Fresh world box is x16.475..31.525,y18.300..34.000,z-3.700..-1.600.
It clears the bore by15.210798 mm and C23's native courtyard polygon by0.605
mm (0.580 mm after its actual0.025 mm half stroke). Common seating/card front
remain inference. The drawing does not dimension the complete open sweep;
the current unpowered off-sled/unbolted service instruction or a qualified
access window is necessary. No in-sled hinge access is claimed.

The fresh optional plate calculation reproduces70.497599 g estimated mass,
181.1/256.1 Hz pinned D5/D10 and287.9/407.1 Hz clamped; maximum100 g static
deflection1.24 mm. Local h4 gaps are C4310.270913,C4210.345385,L10.522577 mm;
h3.5 overlaps C431/C421. No209 Hz release floor applies. D/stiffness,
point supports, density/box masses, rigid sled and loading are inferences;
no dynamic amplification or holding strength is established. The explicit
connector masses include pins, so the23 collision-only tail rows add no mass.

[MA supplier sheet p2](https://atta.szlcsc.com/upload/public/pdf/source/20260306/24758A4FC016E80367B87853635CDCC1.pdf)
supports C84's8.5x8.5 base and10.8 mm conservative height (10+0.5 plus inferred
0.3 projection). The complete Sunlord SWPA shape table p2 gives L1's
4.0+/-0.2 mm XY and3.0 mm maximum height; the model's3.015825 mm hang is
not a solder-seating guarantee. [LS120 maker p2 item9](https://datasheet.lcsc.com/datasheet/pdf/23f5c6599ed9cb614c21ac31ad2b1106.pdf?productCode=C94598)
confirms nominal0.5 g. Fivefold100 g holding allocations are19.61 N per2P
body/local-wire allowance,39.23 N per4P,49.03 N J122,14.71 N C84,2.45 N LS120,
4.90 N J3 and4.58 N socket/card. No actual holding capacity or installed mass
was proved. Stake/support all required bodies/leads and qualify the assembly.

VEHICLE's physics gives bulkplate joint-44.6, approximate80 mm battery bay,
shroud joint+4..47 and18.4 mm intrusion radius. Reusing its old44-48 mm
lead/coax allowance gives board aft joint+79.4..83.4, but R10 has no coax and
the actual2.6/4 Ah pack, external modules, harness and access geometry are
unmodeled. OQ-7's whole-board-plus-axial-tolerance forward of joint+47 rule
remains controlling at every roll angle; freed length remains slack.

## Independent IMU sign derivation

The original [ST DS14623 Rev1 p9 Fig5 and p187 Fig32](https://www.st.com/resource/en/datasheet/lsm6dsv320x.pdf)
were inspected as complete rendered pages. The bottom-view pin order1-4 on
the right,5-7 below,8-11 left and12-14 above matches actual native U4 pads;
pad1 is(18.21,45.15), offset(+1.21,-0.75) from(17,45.9). Combining that
handed view with Fig5's top-view axes and the underside normal gives
Ximu=-xboard,Yimu=-yboard,Zimu out of bottom. Therefore forward-axis roll is
**-gyro_Y**, forward thrust **-a_Y**. This derivation does not use M-7's
rotation lookup as its source. The drawn board frame is left-handed;
cross products/rotations belong in the right-handed IMU frame.

Signed x lever is17-23=-6 mm. z=-2.059994 mm is the model centroid only,
not measured sensitive-element location. At4000 deg/s the x lever contributes
-2.981984 g on imu X; the inferred z contributes about-1.023811 g on imu Z.
U4 lies beneath U1's body projection (centres6.664083 mm apart); the nearest
support centre is13.098091 mm away. Temperature/load, board strain, reflow,
coating/foam and first-article sensor-sign/bias/vibration checks remain open.

The coating walk respects ORDERING's sensor exclusions, rather than treating
selected parts as unconditional whole-body coating. Maximum J121 body projection
is only0.080 mm from U5 pad-union extent, so its local mask must retain that
exclusion. C10 whole envelope clears U5 by3.333144 mm; selected R126 by3.174468
mm; nearest selected U4 envelope C14 clears4.294374 mm. No physical coating
operation is qualified and TP122 retains its sole controlled exception.

## Execution and limits

Executed: native KiCad10.0.6 API fit; seven named mechanical rules; independent
geometry;31 fit regressions (all pass/no skips); fresh supplied-NumPy plate and
local gap calculations; Poppler complete-page inspection of the cited cached
maker drawings and both current assembly pages. The first probe's print-only
dictionary error and isolated test-import error were corrected and rerun;
the nonfatal wxApp diagnostic is disclosed. No target save occurred.

Current ST web text identifies DS14623 Rev3, but its binary/figures could not
be fetched. TN1383 Rev1 current extracted text was read; binary/page images
were unavailable. No inspection of those unavailable images is claimed. Original
Rev1 axis/package drawings, DORABO and Molex cached maker binaries were inspected.
No CLI DRC/full gate/build, GUI retry, Git action, other-worktree write, peer
round17 report/probe read, subagent or physical/firmware test was performed.
Closed C/M hypotheses and their exact limits remain in the JSON; none is deferred.
