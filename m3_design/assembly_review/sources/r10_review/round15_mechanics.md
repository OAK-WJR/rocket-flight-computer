# Round15 independent placement/mechanics review

Target commit `789f4d516251991bdf1518254d537ff7b41f65bb`; PCB SHA256
`7866d6b895573eb10c14d0227ee4bdde8b4fba6145529786cd554cdb80121783` before and after.
**0 Critical /0 Major /3 active Minor: two new, one carried.** No current C/M failure
was established. Closed/rejected candidates and disclosed qualification obligations
are separated in [the structured evidence](round15_mechanics.json).

This is a complete fresh mechanical lens. AGENTS was read first; both review packets,
requirements, all116 decision IDs through D-R14-03 and22 owner-mandate scopes,
current AVA/M3/validation/ordering/vehicle records were considered. Fresh native and
maker evidence below supplies the conclusions; older reports were context only.
No current-round peer reports/probes, canonical writes/builds, native KiCad CLI,
Git mutations, GUI or other-worktree edits occurred. No hidden AVA copper is inferred.

## Active findings

**R15-MEC-01 - Minor, new: specifically disposition U4's component-side GND straps
under the package.** Native B.Cu has0.20mm straps from U4.2(18.21,45.65) through
(18.21,45.9) to U4.3(18.21,46.15), with the midpoint branch to(19.6,45.9).
At(18.21,45.9), copper is inside the nominal maker body
x15.50..18.50/y44.65..47.15, outside either0.575x0.350mm land. The land-to-land
interval is0.150mm. U4.6/U4.7 similarly join at(16.75,46.86), then escape to
(16.75,47.6). Native source: `m3.kicad_pcb` lines50090/50130/50234/50314/50530.

[ST TN1383 Rev1, August2023](https://www.st.com/resource/en/technical_note/tn1383-pcb-design-guidelines-for-mems-sensors-stmicroelectronics.pdf),
p7 section3.2 says “All traces should flow outside the component”; p8 section3.3/
Figure5 says “Never place any routing or via on the top side under the device”.
P9 section3.5/Figure7 also illustrates an inward trace as undesirable. Here the
component side is B.Cu, so applying the top-mounted illustration requires that
face transformation. These shared pad-row straps are a specific departure from
that stress guidance, not proof of bias, damage or lost required performance.
M-7 correctly passes its narrower via/fill/inset-interior checks; AGENTS P3's
no-via/no-fill rule is met. Existing generic thermal/vibration caveats do not name
these straps.

**Fix:** record their geometry as a retained stress-guidance deviation and include
it in first-article zero/bias/temperature/vibration evaluation. Alternatively,
route each GND escape outward and join outside the package through generators.
That short GND-only redraw is **not prequalified low risk**: it still needs native
DRC, fast-reference/antipad/clearance checks and sensor-stress consideration.
No alternative was executed or claimed passing in this read-only lens.

**R15-MEC-02 - Minor, new: current vehicle handoff retains an old plate-clearance
value.** `docs/R10_VEHICLE_HANDOFF.md:39` says0.274mm under C431 at4mm standoffs.
Fresh current native-fit/D5/pinned100g calculation, with maker0.5g LS120,
gives C431 at B(39.3,57.75) deflection1.029087mm and remaining gap0.270913mm.
Current `docs/M3_R10.md:343` and `docs/R10_VALIDATION.md:1564` already agree.
The handoff's overstatement is about0.003mm and changes no physical conclusion.
The [MLT-5020 maker sheet](https://datasheet.lcsc.com/datasheet/pdf/23f5c6599ed9cb614c21ac31ad2b1106.pdf?productCode=C94598),
2021-05-27 p2 item9, confirms0.5g nominal; fitted mass is unweighed.
**Fix:** use0.271mm(or0.270913mm) in the current handoff, retaining all inference
labels; preserve historical0.274363mm receipts at their original board/mass scope.

**R15-MEC-03 - Minor, carried R14-MEC-02/R13-MEC-02: parent vehicle mirror remains
stale.** `../../docs/VEHICLE.md:40` still gives GH ports, an ARM terminal, GH2
J400(10.5,85.5) and0.03mm mated clearance. Native J400 is DB125-2 at(7.4,65.85),
19.893026mm from that old centre. All seven wired terminals are DB125,23 contacts;
J124/J123/GH/header/tie-hole hardware is absent. The current in-worktree handoff
explicitly warns of the mismatch, bounding this record defect. **Fix:** replace
only the parent R10 candidate entry in its separately authorized workflow using
the corrected handoff; preserve R9 history. No parent-worktree edit was made.

## Fresh fit, wire, card and hardware evidence

`fit_check --profile r10` exits0 with223 rows:199 bodies,23 separately allocated
tails and one closed card allocation. Selected M-1/M-3/M-5/M-6/M-7/P-11 all pass.
The outline is46x90x1.6mm. All209 footprint courtyards were measured; all199 model
bodies were screened pairwise with no AABB overlap. No terminal tail intersects
another body. Exactly five diameter3.2mm supports remain at
(4,4),(42,4),(4,44.3),(3.7,86),(42,86), with no tie holes.

The complete [DORABO T0-1 p1,2022-11-26](https://atta.szlcsc.com/upload/public/pdf/source/20251124/8C215F69B14C8E54AE0F8E5023D4AE9F.pdf)
was rendered and inspected fresh. Its tolerances/end datum/interlock independently
give local x unions[-4.62,3.70]/[-8.32,7.20]/[-10.07,8.95]mm for2/4/5poles,
y[-4.10,4.00], maximum height8.90mm and tail3.50+/-0.30mm below seating.
The maximum wire face is7.70-3.70=4.00mm from the pin row. Current model unions
match to VRML quantization; the original R11 envelope Major is closed on this target.

| Terminal | Native pose | Entry | Contacts | Bare-bore wire room mm |
|---|---|---|---:|---:|
| J1 | F(7.4,75.85),-90deg | west | 2 | 5.003012 |
| J121 | F(7.4,55.85),-90deg | west | 2 | 5.003012 |
| J400 | F(7.4,65.85),-90deg | west | 2 | 5.003012 |
| J410 | F(38.6,15.5),90deg | east | 4 | 5.003012 |
| J420 | F(38.6,31.5),90deg | east | 4 | 5.003012 |
| J9 | F(38.6,47.5),90deg | east | 4 | 5.003012 |
| J122 | F(38.6,71.5),90deg | east | 5 | 5.003012 |

Independent room formula is `sqrt(25.4^2-5^2)-abs(face-23)-0.3`.
Every terminal exceeds OQ-1's4.95mm benchmark by0.053012mm. Terminal-body radial
margin under24.9mm usable radius/both0.3mm transverse tolerances is2.976269mm;
adjacent maximum4P bodies retain0.480001mm. A separate diagnostic at z5.3 with
usable radius24.9 gives4.429406mm to the wall. This is not OQ-1's bare-bore
benchmark and does not demonstrate failure of an actual wire. Actual16-22AWG
bends/ferrules,28-16AWG clamp compatibility,4-5mm strip,<=0.2Nm torque,
screwdriver/hand access and staking envelopes remain unqualified.

All23 tails use native pad XY AABBs and z=-3.80..-1.60mm: minimum bore margin
7.558359mm, projection below the1.60mm PCB2.20mm and nominal4mm plate gap1.80mm.
Pad-box transverse allocation is conservative Inference, not a seated pin/solder
model. Seating, solder fillets and bent leads still require first-article inspection.

The complete [Molex SD-47219-001G p1](https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/salesdrawingpdf/472/47219/472192001_sd.pdf)
was inspected fresh, including nails and general tolerances. Width
(13.60+0.15)+2(0.50+0.15)=15.05mm; current local union is
x+/-7.525,y[-9.70,+6.00],height2.10mm at J430 B(24,24.3),0deg.
The native transformed box is approximatelyx16.475..31.525,y18.300..34.000,
z-3.700..-1.600, with15.210798mm bore margin. Common seating/centring and the
undimensioned card-front allocation remain Inference. The maker does not bound
full lid sweep. Current ORDERING8.4 correctly requires board removal/unbolting
from a continuous sled before unpowered service, or a physically qualified hinge
window. Closed fit proves neither open access nor card/lid shock retention.

Nearest bottom support obstacle is C32.2 at4.536177mm from(4,44.3), floor3.5mm;
nearest exposed top pad is LED2.2 at3.807887mm, floor3.8mm. J3's model reaches
x=-0.449880mm and has0.886129mm calculated bore margin; its complete Hroparts
RevA2020-12-08 p1 drawing was inspected. Nominal foreign copper under the3.5mm
hardware discs is confined to3V3/NRST at(4,44.3): minimum radii3.260399mm(via),
3.410399mm(3V3 track),3.421392mm(NRST). Nylon hardware, via covering and whole-face
insulation remain necessary. J2 is programmed before fitting that support or with
it removed, as currently instructed.

Independent nut-stack arithmetic includes both0.3mm transverse tolerances:
6.35mm across-corners/2.4mm nut,0.4mm screw projection and usable radius24.9mm
produce h+t bounds6.018413mm atx4/42 and5.365256mm atx3.7. The conservative
<6.0/<5.3mm instructions and4mm standoff/<=1mm plate default follow. Actual
hardware maxima, hole eccentricity, coating, strength and loaded sled remain open.

Read-only VEHICLE dimensions give conditional aft edge
-44.6+80+(44..48)=joint+79.4..83.4mm,32.4..36.4mm forward of the shroud limit.
That retained lead-zone arithmetic is Inference. OQ-7 still requires the complete
board plus axial mounting tolerance forward of joint+47mm at every roll angle.
No selected2.6/4Ah pack, module/antenna, harness, recovery or installed sled/shroud
stack was physically qualified; freed length remains slack.

## Courtyards, sensors and optional plate

Fresh raw-perimeter and native collision-polygon checks reproduce16 courtyard
stroke overlaps(6F/10B), penetration0.020..0.050mm and positive native polygon
gaps0.010..0.040mm. All16 now appear in validation section7, closing R14-MEC-01's
missing-inventory complaint. Their smallest nominal model-body gap is0.499938mm;
overlapping ink is not body collision. The structured report preserves all16
pairs/measurements as retained owner/assembler inspection deviations.

Native U4 is B(17,45.9),180deg,pad1(18.21,45.15),offset(+1.21,-0.75).
The complete original ST DS14623Rev1 p9/Figure5 and p187/Figure32 were inspected;
official indexed Rev3 p9/210 and p185/210 retain the same axes/pins/dimensions.
The current ST download failed, so no complete Rev3 visual review is claimed.
Bottom flip/180deg agrees with +Ximu=-xboard,+Yimu=-yboard,+Zimu=-zboard,
roll=-gyroY and forward thrust=-aY. Lever x=-6mm; z=-2.059994mm is model-centre
Inference. At4000deg/s, centripetal acceleration is2.981984g toward+xboard,
therefore negative aX. The board frame is left handed; use the IMU frame for
cross products. Fresh maximum-body samples find no via-ring/fill intersection;
M-7 passes. Pad-row routing guidance is separately R15-MEC-01.

TE MS5611 06/2017 complete p15/p17 confirm the low sensor height and no-clean/
protected-port handling. U5's conservative1.1mm height leaves2.9mm nominal cover
space at h4; foam stays within outline+1mm without pressure or adhesive near U4.
The native U4/U5 centres are13.098091/8.160882mm from the nearest support. U4
projects under U1's west side. Installed cover opacity/venting, coating masks,
MCU-load temperature coupling and bias/vibration remain unmeasured; LEDs remain
dark in flight until the cover test passes. No sensor/process qualification is
inferred from the drawings or the generous coat-selection exits.

Fresh optional plate calculation uses all19 explicit mass keys and excludes23
collision-only tails: total70.497599g,181.1/256.1Hz pinned D5/D10 and287.9/407.1Hz
clamped. Maximum100g/D5 static deflection is1.24mm at(46,45). Current C431 h4/h3.5
gaps are0.270913/-0.229087mm; C4210.345385/-0.154615mm; L1 h4 gap0.523098mm.
Murata p1 confirms C411/C421/C431 maximum2.70mm thickness; Sunlord SWPA p2 gives
L1 maximum3.0mm height, covered by its3.015825mm model hang. Maker LS1200.5g and
Molex socket0.434g do not qualify installed mass or retention. First-mode relative
amplitudes at U4/U5 are0.335/0.174 under this ideal model. Assumed stiffness,
laminate, point supports, wire allowances and a rigid sled do not establish real
shock, vibration, clearance or five-times100g retention. No modal release floor
exists. The3.5mm sensitivity is not a demonstrated physical collision;4mm is the
current default and actual assembly qualification remains open.

## Execution limits

Both current canonical assembly PDF pages and the complete relevant maker drawing
pages were independently Poppler-rendered and inspected. Primary PDF content hashes
and exact versions are in the JSON. TN1383 primary text was inspected through the
web tool; ST downloads failed and no local TN drawing raster is claimed. Final
read-only native probes/selected contracts exited0; an initial probe API mismatch
and a transposed preliminary U4 box were corrected before using results. Native
Python emitted its usual wxApp diagnostic on import. No full check.sh/DRC,
procurement, physical, firmware, factory or flight test is claimed by this lens.
