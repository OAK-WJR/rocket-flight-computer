# Round16 independent placement/mechanics review

Target commit `b1b8658d5bf541795b7e7636c09f2e886ea8c67a`; PCB SHA256
`632a9ad36c19426ede219b6ff6b0d638955665cac1b4704d3392a6afdbe03982` before and after.
**0 Critical / 0 Major / 2 active Minor: one new, one carried.** No required
mechanical function or AGENTS section2 violation was demonstrated. This is a fresh
complete mechanical lens, not a fix-only review. [Structured evidence](round16_mechanics.json)
preserves measurements, closed/rejected candidates and actual execution limits.

AGENTS was read first. Both review packets, steer, REQUIREMENTS, all119 D-* IDs
through D-R15-03 and22 owner scopes/amendments, AVA_LAYOUT, M3_R10,
R10_VALIDATION, R9 severity precedents, ORDERING, component qualification,
R10_VEHICLE_HANDOFF and read-only parent VEHICLE were considered. Historical
reports supplied disposition context only; current conclusions use fresh native
and original-maker evidence. No current-round peer report/probe was read.

## Active findings

**R16-MEC-01 - Minor, new: remaining component-side U4 traces need a specific
stress-guidance disposition.** The R15 GND straps are gone; individual GND
escapes join outside the package. Other native B.Cu paths still pass under the
nominal maker body x15.50..18.50/y44.65..47.15, outside U4's pad union:

| Net | Native segment endpoints, mm | Centreline under body outside lands, mm |
|---|---|---:|
| IMU_CS | (14.2,44.7) to (16.26,44.7) | 0.7596 |
| IMU_CS | (16.26,44.7) to U4.12(16.5,44.94) | 0.0918 |
| SPI1_MISO | (18.21,44.16) to U4.1(18.21,45.15) | 0.3257 |
| IMU_INT1 | (18.21,47.65) to U4.4(18.21,46.65) | 0.3250 |
| 3V3A | U4.8(15.79,46.65) to (15.79,47.6) | 0.3257 |

Lengths use a0.001mm midpoint sampling diagnostic; endpoints, widths and body
coordinates come from native geometry and [ST DS14623 Rev1 p187](https://www.st.com/resource/en/datasheet/lsm6dsv320x.pdf).
The first four paths are0.20mm wide; 3V3A is0.25mm.
[ST TN1383 Rev1 pp7-9](https://www.st.com/resource/en/technical_note/tn1383-pcb-design-guidelines-for-mems-sensors-stmicroelectronics.pdf)
recommends symmetric, pad-axis escapes outside the component and avoiding routing
under it. Its component-side illustration applies here to B.Cu. These retained
paths are a specific advisory departure, not proof of offset error, damage or
failed flight performance. M-7 passes its narrower inset-interior/via/fill checks;
P3's no-via/no-fill constraint is met. Generic incomplete-TN1383 qualification
language does not identify these particular signal/supply paths.

**Fix:** explicitly retain and qualify these paths in the sensor stress deviation,
including first-article bias/temperature/vibration measurements, or redraw each
escape along its pad axis outside the body before turning/joining. Any generator
change needs fresh native DRC, reference/region, clearance/fill and reproducibility
coverage; no alternative is prequalified by this review.

**R16-MEC-02 - Minor, carried R15-MEC-03/R14-MEC-02: the parent vehicle mirror
still names removed hardware.** `../../docs/VEHICLE.md:40` describes GH ports,
an ARM terminal, GH2 J400(10.5,85.5) and0.03mm mated clearance. Fresh native J400
is DB125-2 F(7.4,65.849999),19.893026mm from that old centre. All seven wired
connectors are DB125; J124/J123/GH/header/tie-hole hardware is absent. The current
in-worktree handoff warns of this mismatch, bounding the documentation defect.
**Fix:** replace only the parent's R10 candidate entry through its separately
authorized workflow using `docs/R10_VEHICLE_HANDOFF.md`; preserve R9 history.
No other-worktree edit was made.

## Fresh complete geometry checks

Native KiCad API10.0.6 reads209 footprints,951 segments and296 vias. Fit has223
rows:199 bodies,23 separately allocated terminal tails and one closed-card row.
All199 model boxes were screened pairwise: no3D AABB collision; no terminal tail
intersects another body. Selected M-1/M-3/M-5/M-6/M-7/P-11/T-1 all pass.
Outline is46x90x1.6mm. Exactly five diameter3.2mm supports remain at
(4,4),(42,4),(4,44.3),(3.7,86),(42,86), with no servo tie holes.

The complete [DORABO T0-1 sheet1,2022-11-26](https://atta.szlcsc.com/upload/public/pdf/source/20251124/8C215F69B14C8E54AE0F8E5023D4AE9F.pdf)
was independently rendered and inspected. From the last-pin datum, length
tolerance and0.42mm interlock, the2/4/5-pole maximum local x unions are
[-4.62,3.70]/[-8.32,7.20]/[-10.07,8.95]mm. All use y[-4.10,4.00],
height8.90mm, tail3.50+/-0.30mm; maximum wire face is7.70-3.70=4.00mm.
Current model unions agree to VRML quantization.

| Terminal | Native centre / rotation | Entry | Contacts | Wire room mm |
|---|---|---|---:|---:|
| J121 | F(7.4,55.85),-90deg | west | 2 | 5.003012 |
| J400 | F(7.4,65.849999),-90deg | west | 2 | 5.003012 |
| J1 | F(7.4,75.85),-90deg | west | 2 | 5.003012 |
| J410 | F(38.6,15.5),90deg | east | 4 | 5.003012 |
| J420 | F(38.6,31.5),90deg | east | 4 | 5.003012 |
| J9 | F(38.6,47.5),90deg | east | 4 | 5.003012 |
| J122 | F(38.6,71.5),90deg | east | 5 | 5.003012 |

Independent OQ-1 benchmark: `sqrt(25.4^2-5^2)-19.6-0.3=5.003011866mm`,
0.053012mm above4.95mm. This bare-bore benchmark is not an actual wire/tool
envelope. Terminal-body margin is2.976269mm using24.9mm usable radius and
both0.3mm transverse tolerances; adjacent4P body unions retain0.480mm.
With24.9mm radius and a5.3mm vertical diagnostic the wire-face room is4.429406mm;
that is a different metric, not a demonstrated OQ-1 or physical-wire failure.
All23 native pads are diameter1.90mm with nominal1.30mm drills at3.50mm pitch.
Separately allocated tails have7.558359mm minimum bore margin and2.20mm maximum
projection below the PCB, leaving1.80mm to a nominal4mm plate. Real seating,
fillets, lead form and insertion/fabrication allocation remain unqualified.

The complete [Molex SD-47219-001G sheet1](https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/salesdrawingpdf/472/47219/472192001_sd.pdf)
confirms nails/general tolerances. Width(13.60+0.15)+2(0.50+0.15)=15.05mm;
current local union is x+/-7.525,y[-9.70,6.00],height2.10mm. Native J430 is
B(24,24.3),0deg; closed box approximatelyx16.475..31.525,y18.30..34.00,
z-3.70..-1.60, with15.210798mm bore margin. Common seating/centring and the
undimensioned card front remain Inference. The drawing does not bound full lid
travel. ORDERING8.4 correctly requires unpowered, off-bay and off-continuous-sled
service or a qualified hinge window; closed fit does not certify open access.

Nearest bottom support obstacle C32.2 is4.536177mm from(4,44.3), floor3.5mm;
nearest exposed top pad LED2.2 is3.807887mm, floor3.8mm. J3's model reaches
x=-0.449880mm and has0.886129mm bore margin. Its complete Hroparts
TYPE-C-31-M-12 RevA2020-12-08 sheet1 was inspected
([exact supplier part](https://www.lcsc.com/product-detail/C165948.html)).
All209 courtyards were screened: sixteen pairs have0.010..0.040mm native polygon
gaps within their rendered stroke widths, already explicitly inventoried in
validation section7; no body collision follows from that ink. Two additional
pairs have0.060mm polygon gaps. Nylon hardware, covering/insulation and programming
J2 before installing its adjacent support remain necessary.

## Independent signed sensor-frame derivation

This derivation uses the complete original [ST DS14623 Rev1 p9 Figure5 and
p187 Figure32](https://www.st.com/resource/en/datasheet/lsm6dsv320x.pdf), not the
M-7 rotation lookup. Figure5's axis picture is a **top view**; its numbered
contact drawing is a **bottom view**. The native U4 contact pattern, as seen in
the PCB top-view XY frame, matches that maker bottom view: pins1-4 occupy the
east edge, pins12-14 the -PCB-y edge. Native pin1 is(18.21,45.15),
(+1.21,-0.75) from B(17,45.9); native rows give vectors(-2.42,0) from the
pins1/4 edge to pins11/8, and(0,-1.92) from pins5/7 to pins12/14.

Use a right-handed local assembly frame **E=PCB+x/east, F=PCB+y/forward/nose,
D=outward normal of the bottom face**. The maker +Y direction is toward pins12-14,
so +Yimu=-F; +Zimu exits the package top, hence +Zimu=D on this bottom assembly.
The maker right-handed axes then give +Ximu=(-F)xD=-E. The physical rotation
matrix is `diag(-1,-1,+1)` in(E,F,D), determinant+1. Consequently positive
rotation about forward +F reads **-gyro_Y**, and forward acceleration maps to
**-a_Y**. This also reproduces the stated B.Cu flip/180deg result directly from
actual pads, rather than applying a second mirror to the maker bottom view.

The documentation frame(E,F,N=-D) is left handed. Its lever(-6,.,-2.06)mm becomes
(+6,.,+2.06)mm in the IMU frame. The z value is the model centre
-2.059994mm, an Inference. At4000deg/s,6mm radial offset contributes2.981984g
centripetal acceleration toward+E, hence negative a_X. This defines a local board
frame only; parent VEHICLE defines no fixed lateral vehicle axes. Actual assembly
orientation, sensor signs, bias, thermal/vibration and firmware behavior still
require the stated bench tests. M-7 independently passes no-via/no-fill/inset
interior constraints; R16-MEC-01 is the wider advisory routing residual.

## Hardware, stack and retained qualification limits

Fresh nut-stack arithmetic with24.9mm usable radius,6.35mm across-corners/2.4mm
nut,0.4mm screw projection and both0.3mm centring tolerances gives h+t bounds
6.018413mm atx4/42 and5.365256mm atx3.7. Current conservative <6.0/<5.3mm and
measured4mm standoffs/plate<=1mm follow. Actual hardware maxima, eccentricity,
wear, strength and loaded sled remain unqualified.

Fresh optional D5/pinned100g calculation uses all19 explicit mass keys,
excludes23 collision-only tails and gives70.497598846g,181.1Hz; D10/clamped
sensitivities are256.1/287.9/407.1Hz. Maximum deflection is1.24mm at(46,45).
C431 h4/h3.5 gaps are0.270913/-0.229087mm; C4210.345385/-0.154615mm.
L1 hangs3.015825mm below the PCB and retains0.522577mm in this0.1mm local
sampling diagnostic at h4. C431's current handoff value agrees, closing
R15-MEC-02. These stiffness/mass/point-support/rigid-sled calculations are
Inference; no modal floor or physical shock/vibration qualification follows.

Read-only vehicle arithmetic gives aft edge-44.6+80+(44..48)=joint+79.4..83.4mm,
32.4..36.4mm forward of the shroud's+47mm limit under that inherited lead-zone
assumption. OQ-7 still requires the complete board plus axial mounting tolerance
forward of+47mm at every roll orientation. Actual2.6/4Ah pack, modules, antennas,
harness, external arming-switch access, recovery and sled/shroud stack remain
unmeasured; freed length stays slack. Retention forces including local wires are
19.6133N per2P terminal,39.2266N per4P and49.0333N for J122 at5x100g;
C8414.7100N, LS1202.45166N, J34.90333N and socket/card4.57971N. Maker
[LS120 p2 item9](https://datasheet.lcsc.com/datasheet/pdf/23f5c6599ed9cb614c21ac31ad2b1106.pdf?productCode=C94598)
and [Molex](https://www.molex.com/en-us/products/part-detail/472192001) provide
nominal0.5/0.434g respectively; other masses/local wire/card allowances are
Inference. Capacity, clamp/body/staking/hinge strength and installed masses are
not proved. U5's whole-port mask/no-clean handling, opaque cover and U4 stress
exclusions remain required; the complete TE06/2017 pp15/17 were inspected.

## Closed/rejected C/M candidates and execution limits

The corrected terminal maximum unions close the old R11 envelope Major. Maker
contact/axis views support the current signed map, so a wrong-roll-map Major is
not established. Current off-sled card-service instructions defeat a claim that
closed fit promises lid access. OQ-7 avoids the stated shroud window. The h3.5
modeled overlap is a disclosed sensitivity with h4 selected, not measured damage.
Conditional DB125 sharp-pin/fabricated-hole corners remain a bounded process
qualification item; the maker's metal profile/pattern limits are unresolved, so
no actual insertion failure is inferred. All are preserved in the JSON.

Complete current top/bottom assembly PDF pages and relevant DB125, Molex, ST,
Hroparts, MA, LS120 and TE pages were Poppler-rendered and visually inspected.
TN1383 primary text was freshly read through the web tool. Its screenshot calls
returned text references without image content; official ST binary downloads
failed. No TN1383 raster QA or complete latest-revision LSM PDF review is claimed.
The initial selected-contract probe lacked `fit_given`; rebuilding its context
through the real R10 factory fixed the probe. A preliminary transposed U4 box
was corrected before the final measurement; final body is3.0x2.5mm. KiCad Python
emitted its usual nonfatal wxApp diagnostic. No native KiCad CLI, full check.sh,
DRC, build, Git action, GUI retry, canonical edit, physical/firmware/factory/flight
test or other-worktree write was performed.
