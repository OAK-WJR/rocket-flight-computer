# Round14 independent placement/mechanics review

Target commit `f5e4a5a94013514edb952fd328325341b63a98df`, PCB `e0e3ad841654128792b32ab778ca19e4a71e596fa89864074ec4e91e6a5ccfc6`. Before and after SHA256 are identical. **0 Critical /0 Major /2 Minor active groups**: one expanded drawing/inventory residual and one carried vehicle-record mismatch. Four historical rows are closed and excluded from totals. No C/M candidate was found.

All113 D IDs and22 owner-mandate records were considered under current amendment scope. This is the full assigned mechanical lens,including the complete terminal population,not a change-only review. Earlier reports supplied context; current results below were remeasured from native CAD and primary drawings. Canonical files stayed read-only. No peer current-round findings were read.

## Active findings

**R14-MEC-01 - Minor,new inventory extension: retain all16 courtyard-stroke overlaps.** Fresh native perimeter measurements cover all209 footprint courtyards,including the seven represented by four segments. There are6 top and10 bottom stroked-rectangle overlaps; the active `docs/R10_VALIDATION.md` section7 names only C421/U12,R151/D121,R152/D121. The13 additional pairs belong in the final deviation inventory. Segment-to-segment distance confirms the ink penetration below; this is not merely overlap of filled bounding rectangles.

| Pair | Side | Overlap centre x,y mm | Stroke penetration mm | Native collision-polygon gap mm |
|---|---|---|---:|---:|
| C97/D123 | F | 23.560,63.310 | 0.030000 | 0.030 |
| R400/L400 | F | 21.040,2.540 | 0.030000 | 0.030 |
| R32/LED1 | F | 10.465,42.120 | 0.020000 | 0.040 |
| LED2/R33 | F | 10.065,45.545 | 0.040000 | 0.020 |
| C60/R60 | F | 33.200,58.165 | 0.020000 | 0.040 |
| R121/D8 | F | 14.500,72.745 | 0.040000 | 0.020 |
| C85/R86 | B | 27.900,64.987 | 0.035001 | 0.025 |
| C421/U12 | B | 32.688,38.350 | 0.050000 | 0.010 |
| R152/D121 | B | 33.215,70.260 | 0.040000 | 0.020 |
| R64/U5 | B | 11.230,51.405 | 0.040000 | 0.020 |
| U4/C31 | B | 15.135,46.875 | 0.020000 | 0.040 |
| D121/R151 | B | 33.215,72.740 | 0.040000 | 0.020 |
| C22/C26 | B | 26.435,45.935 | 0.020000 | 0.040 |
| C83/C28 | B | 11.690,24.900 | 0.030000 | 0.030 |
| Y1/R10 | B | 20.885,44.705 | 0.020000 | 0.040 |
| C18/C30 | B | 17.475,49.140 | 0.040000 | 0.020 |

The native collision polygons remain separate by0.010-0.040mm; the smallest nominal model-body gap among these16 pairs is0.499938mm. No required-function failure,physical body collision or manufactured-clearance waiver follows. **Fix:** add the full16-pair count/location table to the current owner-deviation inventory. If cleaning the drawing,adjust reviewed CrtYd graphics through library/generator sources only after checking pad/body containment,then rerun native DRC/fit; preserve pads,parts and fit limits. This is native drawing evidence,so no maker numerical page limit is asserted.

**R14-MEC-02 - Minor,carried (`R13-MEC-02`): parent vehicle candidate mirror remains stale.** `../../docs/VEHICLE.md` still specifies GH4 ports,an ARM terminal,GH2 J400 at(10.5,85.5) and0.03mm mating clearance. Native J400 is DB125-2 at(7.4,65.85),19.893026mm from that old centre; seven DB125s supply23 contacts,and J124/J123/GH ports/tie holes are absent. `docs/R10_VEHICLE_HANDOFF.md` correctly provides current construction facts and warns of the mismatch. **Fix:** replace the R10 candidate portion in the separately authorized parent-document workflow using that handoff,preserving accepted R9 history. The warning already bounds the risk; this review makes no other-worktree edit. This is a record mismatch,not a package-limit violation.

## Fresh geometry and access evidence

Native outline is46x90x1.6mm,with exactly five diameter3.2mm supports at(4,4),(42,4),(4,44.3),(3.7,86),(42,86). No tie holes remain. `fit_check --profile r10` returns0 with223 rows:199 bodies,23 separate terminal-tail allocations and one closed card allocation. Selected native M-1/M-3/M-5/M-6/M-7/P-11 all pass. Current nearest bottom/support gap is C32.2,4.536177mm at(4,44.3),against3.5mm; nearest exposed top pad is LED2.2,3.807887mm against3.8mm. J3's model shell reachesx=-0.449880mm and has0.886129mm bore margin under the stated usable radius/tolerances. These are CAD distances.

The complete [DORABO T0-1 p1](https://atta.szlcsc.com/upload/public/pdf/source/20251124/8C215F69B14C8E54AE0F8E5023D4AE9F.pdf) was independently rendered and inspected. Maximum front face is7.70-3.70=4.00mm from the pin row,height8.90mm and tail length3.80mm below seating. Independent x unions are[-4.62,3.70],[-8.32,7.20],[-10.07,8.95]mm for2/4/5 poles,y[-4.10,4.00]. Native models agree to VRML quantization.

| Terminal | Native pose | Contacts | Bare-bore wire benchmark mm |
|---|---|---:|---:|
| J1 | F(7.4,75.85),-90deg | 2 | 5.003012 |
| J121 | F(7.4,55.85),-90deg | 2 | 5.003012 |
| J400 | F(7.4,65.85),-90deg | 2 | 5.003012 |
| J410 | F(38.6,15.5),90deg | 4 | 5.003012 |
| J420 | F(38.6,31.5),90deg | 4 | 5.003012 |
| J9 | F(38.6,47.5),90deg | 4 | 5.003012 |
| J122 | F(38.6,71.5),90deg | 5 | 5.003012 |

Wire room is `sqrt(25.4^2-5^2)-abs(face-23)-0.3`:5.003012mm,0.053012mm above OQ-1's4.95mm benchmark at every terminal. Minimum terminal body/bore clearance is2.976268mm; adjacent4P bodies retain0.480001mm. All23 tails use their native pad XY boxes andz=-3.8..-1.6mm; minimum tail/bore margin is7.558359mm,projection2.20mm below the PCB,nominal4mm plate gap1.80mm. Pad-AABB tail width,seating,solder fillets/bent leads are explicit inferences. Screwdriver/ferrule/bend/RTV and actual clamp retention remain unqualified. A separate wall/vertical-tolerance opening diagnostic gives4.660131mm; it is not the owner-approved bare-bore benchmark or a demonstrated wire failure.

The complete [Molex SD-47219-001G p1](https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/salesdrawingpdf/472/47219/472192001_sd.pdf) confirms fitting nails and general tolerances. The fresh closed J430 union is15.05x15.70x2.10mm at B(24,24.3):local x+/-7.525,y[-9.70,+6.00],z[0,2.10]. Width is(13.60+0.15)+2(0.50+0.15). Board box is approximatelyx16.475..31.525,y18.300..34.000,z-3.700..-1.600. Bore margin15.210798mm; nearest C23 stroked courtyard gap0.575002mm. Common seating,centring,undimensioned card front and actual fitted maximum remain Inference. Maker drawing does not dimension the complete lid sweep. Current ORDERING8.4 explicitly requires the unpowered PCB to be unbolted/removed from a continuous sled before hinge service,or a physically qualified access window. Closed fit gives no open-hinge qualification.

Independent nut-stack arithmetic includes both0.3mm transverse tolerances,usable radius24.9mm,6.35mm across-corners/2.4mm nut and0.4mm protrusion. Combined h+t bounds reproduce6.018413mm atx4/42 and5.365256mm atx3.7,justifying conservative<6.0/<5.3mm instructions. At h4/t1 nominal nut/bore margin is0.421119mm atx4/42 and0.145392mm atx3.7. Actual maxima,eccentricity,coating and strength remain unqualified. J2 must be programmed before the adjacent mid support is installed,or with it removed.

Read-only vehicle dimensions give conditional aft placement -44.6+80+(44..48)=joint+79.4..83.4mm,32.4..36.4mm forward of the shroud's+47mm limit. This retained lead-zone arithmetic is an Inference. OQ-7 still requires the entire board plus axial mounting tolerance forward of+47mm in every roll orientation. Actual2.6/4Ah pack,module/antenna/harness/sled/tool fit has no physical proof; freed length remains slack.

## Sensor frame and optional plate diagnostic

Independent native U4 is B(17,45.9),180deg,pad1=(18.21,45.15),offset(+1.21,-0.75). [ST DS14623 Figure5,p9](https://www.st.com/resource/en/datasheet/lsm6dsv320x.pdf) was visually inspected using the manufacturer-authored Rev1 [DigiKey mirror](https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/6722/LSM6DSV320XTR.pdf) after official download failures; official indexed Rev3 p9 text was crosschecked. The bottom flip/180deg pose preserves +Ximu=-xboard,+Yimu=-yboard,+Zimu=-zboard,roll=-gyroY and forward thrust=-aY. Lever x=-6mm and model-centre z=-2.059994mm (z Inference) agree with the binding note. At4000deg/s,6mm offset produces2.981984g centripetal acceleration toward+xboard,therefore negative aX. Board coordinates are left handed; cross products must use the right-handed IMU frame. Native M-7 also passes the component-side MEMS via/fill exclusions. Actual bench sign,bias,temperature and vibration are unqualified.

Fresh optional plate calculation reproduces70.297599g estimated mass,181.3/256.4Hz pinned D5/D10 and288.1/407.5Hz clamped. Maximum100g/D5/pinned static deflection is1.24mm at(46,45). All19 explicit mass keys are represented; collision-only tail rows add no mass. Independent mass-matrix check agrees within1.4e-17kg. Local0.25mm body raster including endpoints gives C431 peak1.025637mm at(40.65,56),leaving0.274363mm at h4 and-0.225637mm at h3.5; C421 h4/h3.5 gaps0.348129/-0.151871mm. L1's nominal h4 gap0.984175mm becomes0.524631mm under this diagnostic. Those already disclosed sensitivities do not prove actual contact or flight qualification. Ideal supports,assumed D/laminate/masses,rigid sled and quasistatic100g do not qualify shock,vibration or the required5x100g retention. No modal release floor exists.

## Closed rows and limits

- R11-BOM-01/R11-MEC-01: corrected maximum terminal unions and5.003012mm OQ-1 result close the prior envelope Major on this exact target.
- R13-MEC-01: all23 tails now have separate collision allocations; real solder/seating remains open.
- R13-BOM-02: current closed socket/card allocation includes nails/tolerances; actual assembly/card datum remains open.
- R11-MEC-03: current off-sled/unbolted service procedure closes the former access-record omission; no open-lid fit is claimed.

Complete native top/bottom assembly PDFs were manifest-checked against this PCB and independently rendered/inspected. Maker-page visual QA followed the PDF skill. Native read-only probes emitted the known create-wxApp diagnostic but returned0. An initial rule selection incorrectly included optional M-2; the tool rejected that scope before CAD construction. The corrected six-rule run passed,and plate ran separately. No native CLI,full check.sh,GUI retry,git action,build or CAD/source mutation occurred.

This report does not certify all-part manufactured maxima,physical bore/stack/tool/card/clamp/hinge/coat/retention,firmware,full DRC/ERC/parity or an assembler process. Correctly disclosed pending qualification is not counted as a demonstrated hardware failure. R9 remains accepted; no R10 acceptance or order follows. Compact numeric source/coordinate evidence,all16 residuals and exact hashes are in `round14_mechanics.json`.
