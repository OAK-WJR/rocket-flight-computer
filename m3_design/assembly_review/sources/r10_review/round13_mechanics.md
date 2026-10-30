# Round13 independent placement/mechanics review

Target commit `fa897c81abac3026e75ca5cc88bef0c2659a7130`; PCB SHA-256 before and after: `7355ae1aeb1fdfdf6f64317945a0bf114d94c2bb65fb04adfbcd5a2b8037b09c`.

**0 Critical / 0 Major / 2 Minor (1 new, 1 carried).** Fresh full lens of the saved placement, mechanics and integration instructions. No implementation changes, peer current-round reads or child agents. Every physical/firmware qualification below stays separate from CAD. No AGENTS section2 violation established by this lens.

## Findings

### R13-MEC-01 - Minor, new: pin-tail fit representation is overstated

`tools/fit_check.py` `R10_MODEL_BOXES` pins every DB125 insulating-body envelope to z approximately0..8.90mm. Its through-hole `pad_box()` spans only z=-1.6..0mm. All four DB125 WRLs contain one body box, with no tail geometry. `docs/R10_VEHICLE_HANDOFF.md` nevertheless says complete maximum bodies/tails are modeled; `docs/R10_VALIDATION.md` section8 says the tails are included.

[DORABO T0-1 sheet1/1](https://atta.szlcsc.com/upload/public/pdf/source/20251124/8C215F69B14C8E54AE0F8E5023D4AE9F.pdf), visually checked at the front-view dimension, gives3.50+/-0.30mm below the seating plane. Thus the saved fit walk never evaluates the maximum endpoint z=-3.80mm.

This is a bounded evidence/prospective coverage defect, not a demonstrated collision. Independently allocating all23 pin tails at their native centres, with conservative1.05mm square transverse bounds and both0.3mm sled tolerances, leaves >=7.971012mm to the24.9mm usable bore radius and no overlap with a bottom model box. Maximum projection below the1.6mm PCB is2.2mm, leaving1.8mm nominal plate clearance at4mm standoffs (1.3mm at3.5mm); actual solder and seating are unmeasured.

**Fix:** add explicit maker-derived tail rows or a separate calculated-tail section and regression to the fit report, preserving the insulating-body normalized contract. Until then, state that tails were checked separately instead of claiming they are modeled. No immediate board move is indicated by this calculation.

### R13-MEC-02 - Minor, carried: parent vehicle mirror remains stale

Read-only `../../docs/VEHICLE.md`, Dimensions / Main-section stack candidate R10 clause, still describes GH-4 ports with0.03mm mated margin, ARM/IGN terminals and GH-2 J400 at(10.5,85.5). The target has seven DB125s, J400 F(7.4,65.85), no J124/ARM link, no wired GHs and no servo tie holes. This is the existing R12-m02 discrepancy. The exact current `docs/R10_VEHICLE_HANDOFF.md` replacement facts and current ORDERING section8 mitigate it; no parent edit is authorized in this task.

**Fix:** synchronize that separately owned document through its own authorized workflow, preserving accepted R9 history and OQ-7. Use the current in-worktree handoff for construction. This is not a newly proven whole-stack failure.

## Independent coverage and results

- Verified worktree HEAD/ref by file reads and the exact PCB hash. Native inventory is209 footprints/973 segments/296 vias. Fresh native `fit_check --profile r10` exits0 with200 model/card rows; outline46x90x1.6mm and exactly five supports(4,4),(42,4),(4,44.3),(3.7,86),(42,86). Fresh selected M-1/M-3/M-5/M-6/M-7/P-11 all exit0. These are API checks; no CLI/DRC/full-build pass is claimed.
- Independently transformed maker maximum2/4/5P body unions into the saved terminal poses. All seven wire rooms are5.003011866mm versus the accepted4.95mm floor, with only0.053011866mm spare. Maximum model endpoint discrepancy is1.49e-6mm. Terminal body/bore margin is2.976269mm; minimum adjacent4P body gap0.48mm. All terminal pairs and terminal/top-model pairs clear. Global modeled bore minimum remains J3 at about0.89mm.
- OQ-1 uses a bare-bore, nominal5mm-height benchmark. Applying P2's0.5mm wall allowance and both transverse tolerances at that nominal height instead gives about4.429mm wire room. Neither number qualifies insulation, ferrule, minimum bend radius, screwdriver or staking access. Those are correctly open in current instructions.
- Support clearances reproduce4.536177mm bottom(C32.2) and3.807887mm top exposed pad(LED2.2) at(4,44.3), against3.5/3.8mm. Exact support count, bottom THT keep-outs and MEMS placement rules pass. J2 is correctly programmed before installing its adjacent support or with that support removed.
- Independent nut arithmetic reproduces h+t maxima6.018412896mm at x4/42 and5.365255834mm at x3.7, including both0.3mm offsets and the stated6.35mm across-corners/2.4mm nut/0.4mm protrusion assumptions. Selected h4+t1 gives a worst nominal nut radial margin0.145392mm. Actual hardware maxima, eccentricity and tolerances remain unqualified.
- Fresh optional plate run reproduces181.3/256.4Hz pinned D5/D10,288.1/407.5Hz clamped,70.3g and1.24mm maximum100g static deflection. An additional all-bottom-part raster including exact envelope endpoints gives C431 gap0.274406347mm at h4; at h3.5 C431/C421 overlap by0.225594/0.151828mm. This matches disclosed sensitivity; no release-frequency floor exists. Rigid sled, mass, laminate stiffness and point restraints remain assumptions.
- Recomputed5x100g load allocations: DB1252P plus local wire19.6133N;4P39.2266N;5P49.0333N; C8414.7100N; J430 socket/card4.5797N; LS1201.4710N; J34.9033N. These are required loads, not proven holding capacities. Current instructions stake all seven terminal bodies and tall parts, back the board while tightening and independently support leads. No retention capacity is established by inspection.
- [Molex SD-47219-001 RevG sheet1](https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/salesdrawingpdf/472/47219/472192001_sd.pdf) complete page confirms the hinge mechanism and closed-body drawing. Its [product record](https://www.molex.com/en-us/products/part-detail/472192001) gives0.434g. Saved J430 B(24,24.3),0deg uses a conservative14x15.5x2.1mm closed socket/card union. The drawing does not dimension a full open sweep. Current off/disconnected/out-of-bay instructions explicitly require unbolting/removing the PCB from a continuous sled or a qualified access window; closed-card fit supplies no open-lid or flight-retention credit.
- Native U4 is B(17,45.9),180deg, pad1(+1.21,-0.75)mm; x lever=-6.0mm and model-centre z=-2.059994mm(inference). [ST DS14623 Figure5,p9](https://www.st.com/resource/en/datasheet/lsm6dsv320x.pdf) pin/axis figure supports the retained bottom/180 pose: roll=-gyroY and forward thrust=-aY. The board drawing's x/y/z convention is left-handed, so use the right-handed IMU frame for cross products. At4000deg/s, x-only centripetal contribution is2.981984g; including inferred z gives3.152844g. Physical axes and lever calibration remain required.
- [ST TN1383 pp8-13](https://www.st.com/resource/en/technical_note/tn1383-pcb-design-guidelines-for-mems-sensors-stmicroelectronics.pdf) component-side via/routing and stress/thermal guidance was checked against current U4/U5 exclusions and procedures. U4 under U1's west pin row, inferred stress/modal exposure and U4/U5 thermal effects remain correctly disclosed bench items.
- Read-only vehicle source gives50.8mm coupler bore,54.6mm above joint+120,595mm free axial length and camera shroud joint+4..47. OQ-7 keeps the entire board plus axial tolerance forward of+47 in every roll orientation; minimum nominal board front is+137. Reusing the historical44-48mm lead zone would put the aft edge+79.4..83.4 and leave92..96mm stack slack for80mm battery,90mm board,25mm charge/hardware and260mm recovery. Those estimates do not allocate the actual2.6/4Ah pack, external GPS/radio/antennas, terminal bends, sled or recovery hardware. No current complete assembly CAD or physical fit is claimed.

## Closed prior items and pending qualifications

R11-BOM-01/MEC-01 is independently closed for this target by the maximum-body/row/room calculations. R11-MEC-02 current probe/staking/hardware instructions are corrected. R11-MEC-03 is corrected by explicit PCB removal/window requirements. Parent mirror R12-MEC-01 remains carried above.

Physical bore/stack/sled/shroud fit, real pack/module/harness volume, screw/ferrule/tool access,5x100g retention, clamp/dry-contact reliability, coating/staking, shock/vibration/modal response, U4/U5 bias/thermal behavior, locked-card retention and actual lid-access remain pending qualifications, not new demonstrated hardware failures.

## Executed checks and limits

`fit_check.py --profile r10`; selected `check_r10.py` M-1/M-3/M-5/M-6/M-7/P-11; independent native maker-union/tail/pair/nut/retention/stack probes; optional `plate_model.py --profile r10`; exact-endpoint local plate fields; read-only source/procedure comparison; primary-source browsing and PDF visual inspection. Structured results, source-document hashes and detailed coverage limits are in `round13_mechanics.json`; compact reproducible probes are ignored under `.supervisor/r13_mechanics/`.

Direct Molex and ST downloads timed out. Visual work used the original maker documents from the recorded mirrors: Molex RevG sheet1 and ST Rev1 p9; current ST official Rev3 p9 indexed source was also checked. No complete latest-ST revision comparison is claimed. Temporary downloaded PDFs/rasters were removed after inspection. No native CLI, full check.sh, canonical build, GUI, CAD save, git command/mutation or other-worktree edit was performed.
