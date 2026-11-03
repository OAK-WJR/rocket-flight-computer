# R10 round 11: placement and mechanics

Target: commit `21bc3b2`, native PCB SHA-256
`0c50b9fd0930f34edab7129fc21b8e71d0ee03bc079e1900b7e131cece6bfaf8`.
Result: **0 Critical, 0 Major, 3 Minor**. No implementation, Git or other-worktree changes.
This lens used the native PCB, current generators and binding, the required decision/requirement records,
the read-authorized parent `../../docs/VEHICLE.md`, maker drawings and current assembly renders.
No other round-11 report was read. Dimensions below are CAD measurements or explicitly labelled calculations,
not assembled-board measurements. Companion evidence: `round11_mechanics.json`.

## Findings

### R11-MEC-01 - Minor: the terminal envelope does not bound the pin-row tolerance chain

`m3_design/r10_parts.py:149`-152 gives every DB125 depth 7.7 mm centred at local y=-0.2;
the resulting native wire faces are x=3.350 / 42.650 mm, or 3.650 mm outside the pin row.
The original [DORABO T0-1, sheet 1](https://atta.szlcsc.com/upload/public/pdf/source/20251124/8C215F69B14C8E54AE0F8E5023D4AE9F.pdf)
dimensions depth 7.40 mm and row offset 3.90 mm. Its general tolerances are respectively
±0.30 and ±0.20 mm. With the footprint's stated front/back convention, the outward bound is
7.70-3.70=**4.000 mm**, 0.350 mm beyond the model. The pin-row-referenced depth union is
[-4.10,+4.00] mm. The rigid body still has **2.612560 mm** radial clearance including P2's wall
allowance and both transverse tolerances. This is a source-bound envelope defect, not a proved bore collision.

P-11 correctly calculates **4.953012 mm** from its present envelope. The conservative maker-chain face
instead gives sqrt(25.4²-5²)-20.0-0.3=**4.603012 mm**, 0.346988 below OQ-1's 4.95 mm reference.
That reference also deliberately uses a bare bore at z=5 mm; it is not a physical bend guarantee.
The finding remains Minor under the R9 mechanical-envelope precedent: the tight wire bend is already a
disclosed physical qualification and no rigid collision or impossible wire bend is demonstrated.
It must not be described as a passing maker-maximum wire-room calculation.

Concrete fixes: correct the generator/model to the pin-row-referenced bounds, carrying the interlock/end
datum as well; move west x=7 to 7.35 and east x=39 to 38.65 to recover the present wire-room bound, then
re-run placement/DRC, actual-feed hot-plug, fabrication, binding and review. Alternatively retain placement
and explicitly disposition the conservative 4.603 mm bound with demonstrated fitted 16-22 AWG/ferrule
bends under OQ-1. Do not silently replace its accepted threshold.

### R11-MEC-02 - Minor: a current assembly and mechanical worksheet is still missing

`docs/ORDERING.md:219`-238 explicitly supersedes its older snapshots, which prevents treating all the old
numbers as current. However the executable coating/probe/staking worksheet at lines 273-280 and 374-399
still depends on them. Examples from the native board:

| Subject | Older instruction | Current native evidence |
|---|---|---|
| ACT_GATE TP121 | Coat top; probe top (16.2,74.2) | **Bottom (10.5,71.5)** |
| NRST C24.1 | (25.33,49.1) | **Bottom (25.45,49.42)**; C24.2 GND (25.45,48.58) |
| RAW_ACT TP120 | (18,67.6) | **Bottom (18,68.6)** |
| C84 / LS120 staking | (38.5,74) / (20,17.5) | **Top (27.5,78.5) / (23,58.5)** |
| J400 | GH plug, explicitly not staked | **DB125-2 at (7,65.85)**; P3 requires all seven DB125 bodies staked |
| Nearest support obstacles | C88 / J400 | **C32.2 bottom 4.536177 mm; LED2.2 top 3.807887 mm**, both at (4,44.3) |

The historical `docs/M3_R10.md:374`-381 retention table still has the header/ties and GH bodies;
the current mass file correctly has five-contact J122 and seven DB125s. The parent vehicle candidate
mirror at `../../docs/VEHICLE.md:39` still specifies GH ports/J400 and the removed ARM terminal, whereas
AVA_LAYOUT supplies the new rows. Its accepted R9 stack is clearly distinguished, so this is not evidence
that a wrong R10 assembly has been built. No current assembly or flight release is claimed.

Concrete fix: publish one board-hash-bound current coat/probe/staking/retention and sled worksheet, replace
the obsolete operational rows, and give the parent repository the corrected candidate harness handoff.
Keep historical measurements under their named boards. Include the current plate figures below, all seven
staking positions, J430 retention, and actual support-copper inventory; preserve U4/U5 exclusions and the
sole controlled TP122 brush exception. This is a record/process gap; current P3 and the amendment already
state the governing obligations.

### R11-MEC-03 - Minor: removing the bay alone does not establish hinged-card service access

`docs/ORDERING.md:231` and REQUIREMENTS F5 say off/out of bay. J430 is bottom (24,24.3), with the closed
allocation x=17-31, y=18.3-33.8, z=-3.7 to -1.6 mm. A continuous default sled lies only 4 mm below the
PCB bottom. [Molex SD-47219-001 Rev G, sheet 1](https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/salesdrawingpdf/472/47219/472192001_sd.pdf)
shows a hinge at the socket's back and a 14.50 mm-long body, but does not dimension open angle, hinge
axis height, card seating or the operating sweep. A roughly 90-degree service opening has order-14.5 mm
depth below that hinge, exceeding the 4 mm sled gap (Inference); the closed-box fit cannot prove access.

Concrete fix: require unbolting the PCB from a continuous sled before card work, or verify a deliberately
sized nonconductive access window and the real lid/card/finger sweep. Keep insertion/removal off and out
of the bay. This is a service-instruction/qualification gap, not a flight collision: the closed envelope
clears the bore by **15.686423 mm**, every support by at least **16.710775 mm**, and its nearest bottom
neighbours C23/R460/R461 by **1.100 mm** in projection.

## Tested coverage and measured limits

Fresh read-only runs: `fit_check.py --profile r10` passes 200 model/envelope rows; selected `check_r10`
M-1/M-3/M-5/M-6/M-7/P-11/T-1 all pass. These runs do not replace root's fresh native all-severity DRC,
parity/ERC or complete build. The PCB hash was unchanged after all probes.

| Terminal | Native centre, top rotation | Wire entry | Body box x, mm |
|---|---|---|---|
| J121 IGN | (7,55.85), -90° | -x | 3.350-11.050 |
| J400 switch | (7,65.85), -90° | -x | 3.350-11.050 |
| J1 battery | (7,75.85), -90° | -x | 3.350-11.050 |
| J410 GPS | (39,15.5), +90° | +x | 34.950-42.650 |
| J420 radio | (39,31.5), +90° | +x | 34.950-42.650 |
| J9 camera | (39,47.5), +90° | +x | 34.950-42.650 |
| J122 servos | (39,71.5), +90° | +x | 34.950-42.650 |

All seven use 8.9 mm model height; current envelope radial margin 2.930873 mm. Current adjacent end gaps
are 2.700 mm west, 1.000 mm between the repeated east port bodies, and 7.250 mm camera-to-servo.
The original terminal drawing's **tail is 3.50±0.30 mm**; 3.90 mm is the depth-to-row offset, not pin length.
At 1.6 mm PCB thickness the tail extends at most 2.20 mm below the board before seating/solder allowances,
less than L1's model hang. Historical "3.90 mm pin stub" wording should be corrected with MEC-02.

Screwdriver check: under the explicit *inferred* proxy of vertical screw axes on pad centres and a 3 mm
shaft, nearest other tall-body distances are ≥3.250 mm at port-row ends, 4.600 mm west, 7.250 mm J122.
This supports assembling the harness off the sled/bay, with the board locally backed against clamp torque;
it is not tool certification. The maker does not dimension screwdriver swept volume. Actual blade, ferrule,
wire stiffness, 0.2 N·m maximum torque and adjacent assembled wires must be checked physically. Unkeyed
battery/switch/port identities, 28-16 AWG clamp limits and external strain relief remain mandatory.

The outline is 46×90 mm, with exactly five Ø3.2 mm supports (4,4), (42,4), (4,44.3), (3.7,86), (42,86).
No tie holes or sixth support exist. Global rigid-envelope bore minimum is J3, **0.886129 mm**; C84's current
8.5×8.5×10.8 mm allocation clears by **10.578251 mm**. The [MA-series supplier drawing, p2](https://atta.szlcsc.com/upload/public/pdf/source/20260306/24758A4FC016E80367B87853635CDCC1.pdf)
supports the latter dimensional bound; its derived land and manual post-reflow process remain unqualified.

All five washer discs were re-inventoried. Only (4,44.3) contains non-GND surface tracks/vias inside r=3.5:
3V3 via at (3.73,40.8), copper radius **3.260399 mm**; its F.Cu track **3.410399 mm**; NRST at the
(6.2021,41.5521) corner **3.421392 mm**. The former BAT_IN entry under (42,86) is gone. Nylon hardware,
covered ordinary vias and whole-face nonconductive insulation remain necessary; mask is not a wear test.
The top LED2.2 obstacle has only 0.007887 mm spare against the conservative 3.8 mm check, but a measured
7 mm maximum washer has 0.307887 mm nominal edge gap. Keep actual hardware and hole eccentricity checks.

For the recorded nut assumptions (6.35 mm across-corners, 2.4 mm thick, screw protrusion 0.4 mm), both
±0.3 mm centring tolerances reproduce h+t<5.365256 mm at x=3.7 and <6.018413 mm elsewhere. At h=4/t=1
the worst nut corner radius is 24.754608 mm, **0.145392 mm** below usable r24.9; plate corner radius is
24.300206 mm. These are inferred nominal hardware calculations, not a hardware-maxima fit qualification.
Program J2 before fitting the interfering middle support, as the existing worksheet correctly requires.

Optional current-mass plate calculation (70.3 g, assumed laminate/stiffness/masses): f1 **180.7/255.6 Hz**
pinned D5/D10, **287.0/405.9 Hz** clamped. Static 100 g maximum **1.24 mm at (46,45)**. A 9×9 sample over
current L1 B(25,74.6) gives max displacement 0.457566 mm; its 3.015825 mm model hang leaves 0.526609 mm at
the default 4 mm standoff, only 0.026609 mm at the 3.5 mm minimum (Inference; no dynamic amplification).
Keep the 4 mm default and physical qualification. Audit 2 explicitly removed the frequency release floor;
neither these results nor historical 280.9 Hz establish vibration survival.

## Sensors, coating, retention and installed stack

U4 is B180 at (17,45.9), pad1 offset (+1.21,-0.75) mm. The [original ST DS14623 Figure5, p9](https://www.st.com/resource/en/datasheet/lsm6dsv320x.pdf)
was visually checked in the [Rev1 distributor copy](https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/6722/LSM6DSV320XTR.pdf);
the official Rev3 cached figure agrees. The native pose and binding retain +Ximu=-xboard, +Yimu=-yboard,
+Zimu out the bottom; forward thrust=-aY, roll=-gyroY. Lever x=-6.000 mm, model-centre z=-2.059994 mm
(Inference). At 4000°/s the offset terms are 2.981984 g in x and 1.023814 g in z, total 3.152844 g using that
inferred z. Use the right-handed IMU frame for cross products; the documented board frame is left-handed.
Sign/temperature/vibration checks remain. M-7 found no prohibited via/fill in U4/U5 component-side regions.

U4 lies within U1's projected x=15-31/y=35-51 body box. [ST TN1383 Rev1 §§4.3-4.5, pp11-13](https://www.st.com/resource/en/technical_note/tn1383-pcb-design-guidelines-for-mems-sensors-stmicroelectronics.pdf)
supports keeping heat, resin and connector loads away; it supplies no guaranteed safe distance for this
specific assembly. Retained sensor-under-MCU placement therefore stays a thermal/mechanical bench item.
No adhesive/foam may load U4. U5 foam remains capped at outline+1 mm, ≥0.7 mm off U4's recorded outline,
without port pressure; at 4 mm standoffs its maker-max 1.1 mm height leaves 2.9 mm for the cover geometry.

Fresh coating geometry preserves C11/R13/R64 masks, whole-U5 tape and ≥3 mm from U5 body+pad union.
C10 conservative Fab/pad clearance is **3.333144 mm**, next listed whole-coated R164 **5.328270 mm**;
TP122 alone retains its **1.400 mm pad-gap** brush exception. TE's [06/2017 pp15/17](https://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocFormat=pdf&DocLang=English&DocNm=MS5611-01BA03&DocType=Data+Sheet&PartCntxt=MS561101BA03-50)
supports body/height and protecting the port/no-clean process, not a maker-certified 1 mm coat clearance.
Actual masking tolerances, venting, opaque-cover light testing and post-coating leakage tests remain open.

At 5×100 g, current inferred body+local-wire/card masses demand **19.61 N** each two-pole DB125,
**39.23 N** each four-pole, **49.03 N** J122, **4.58 N** socket+card, **14.71 N** C84, **1.47 N** LS120 and
**4.90 N** J3. No solder/clamp/hinge/adhesive holding-strength evidence establishes those margins. These
remain declared qualification obligations, with staking of all seven bodies and independently supported
wires. A visible AVA terminal row is placement inspiration, not retention evidence.

The parent vehicle record gives bulkplate top joint-44.6, battery bay ≈80, shroud joint+4 to +47 and
coupler r25.4 to joint+120. OQ-7 still requires PCB aft edge plus axial tolerance wholly forward of +47 in
every roll orientation. Keeping the historical 44-48 mm lead zone gives aft +79.4 to +83.4 and ≈32-36 mm
shroud margin; removing it entirely gives +35.4 and a conflict. Thus at least **11.6 mm plus axial tolerance**
must remain after the nominal 80 mm battery bay. At the minimum allowed position the PCB reaches +137,
past the coupler into the larger bore; testing the whole board in the smaller bore is conservative.
The newly allocated ≥2.6/4 Ah battery and external modules are not dimensioned in that 80 mm bay: pack,
full harness, reachable external arming switch, shroud and sled must be physically integrated. These
explicitly pending fits are not automatic Major findings and grant no fabrication or flight acceptance.
