# R10 round 12: placement and mechanics

Target: provided commit `d57b216c365fc8d18896bceba37f63caf20d52a4`, PCB SHA-256 `0ad0135cb9ff1f6ace7ef9d5ba9006b727b293d7b5224bb97dad47859b91238d`, independently matched before and after.

**Current findings: 0 Critical / 0 Major / 1 Minor, carried; no new defect.** No demonstrated required mechanical function failure. Three prior mechanics items are closed or partly closed by fresh evidence below. CAD and calculations do not establish physical qualification. Structured measurements: [round12_mechanics.json](round12_mechanics.json).

## Current finding

**R12-MEC-01 - Minor, carried from R11-MEC-02 / R11-m03: stale vehicle candidate mirror.** `../../docs/VEHICLE.md`, Dimensions / Main-section stack, still describes R10 GH-4 GPS/radio, GH-2 J400 at (10.5,85.5), an ARM terminal and a 0.03 mm GH-mating margin. Native CAD instead has west DB125 centres x7.4 at y55.85/65.85/75.85 (IGN/switch/battery), east x38.6 at y15.5/31.5/47.5/71.5 (GPS/radio/camera/servos), all wires outward. [DORABO T0-1 sheet 1](https://atta.szlcsc.com/upload/public/pdf/source/20251124/8C215F69B14C8E54AE0F8E5023D4AE9F.pdf) is the actual terminal family; [Molex SD-47219-001 G sheet 1](https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/salesdrawingpdf/472/47219/472192001_sd.pdf) describes the bottom hinged card.

Concrete fix: separately update the parent candidate subentry to these seven terminal rows, no ARM/GH/header/tie-hole or SMA-coax assumptions, current wire-room and OQ-7 limits, and board-removal/qualified-window card access. Preserve its accepted R9 subentry. This review leaves that separately owned file untouched. Current ORDERING section 8 already gives the corrected local instructions; no wrong built assembly is demonstrated.

## Fresh geometry

Independent reconstruction from the complete rendered DORABO sheet used its depth 7.40 +/-0.30, rear datum 3.90 +/-0.20, end datum 1.75 +/-0.20, interlock 0.42 +/-0.20, and applicable length tolerances. Maximum pin-row-referenced unions are:

| Contacts | Local x union (mm) | Local y union (mm) | Height max (mm) |
|---|---|---|---:|
| 2 | -4.62 to +3.70 | -4.10 to +4.00 | 8.90 |
| 4 | -8.32 to +7.20 | -4.10 to +4.00 | 8.90 |
| 5 | -10.07 to +8.95 | -4.10 to +4.00 | 8.90 |

Current model extents agree within 0.000002 mm. All seven defined OQ-1 rooms are `sqrt(25.4^2-5^2)-19.6-0.3 = 5.003011866 mm`, above 4.95. Terminal body radial margin is 2.976269 mm using usable radius 24.9 and both +/-0.3 centring tolerances. Maximum adjacent four-contact body unions clear by 0.480 mm; west two-contact bodies by 1.680 mm; camera/servo by 6.730 mm. No maximum terminal body intersects another fitted top courtyard. Nearest such gap is 0.255 mm, IGN-to-Q124 and battery-to-C80. Drawing tail length is 3.50 +/-0.30 mm, not 3.90: nominal full seating leaves at most 2.20 mm beyond the 1.6 mm PCB bottom, before actual solder/lead geometry.

The wire-room number is a **bare-bore benchmark at fixed z5**, not a modeled wire/ferrule bend. Adding a further 0.3 mm vertical displacement at the same reference height gives 4.940894 mm diagnostically. This does not change OQ-1's defined benchmark or prove an impossible physical bend. The maker specifies 28-16 AWG, 4-5 mm strip and 0.2 N m maximum; the selected leads/ferrules, insulation, bend and screwdriver shaft/handle are unmeasured. No actual tool-clearance pass is claimed.

All 199 project model envelopes were independently transformed and checked radially. The minimum body margin is USB J3,0.886129 mm, with shell x=-0.449880; every body margin is positive. [HRO's current product page](https://en.krhro.com/Product-Details/726.html) gives nominal 8.94 x 7.35 x 3.16 mm; its full tolerance drawing was unavailable, so the inherited detailed USB model is not newly certified against every maker tolerance.

The native outline is 46 x90 x1.6 mm. Exactly five 3.2 mm cutouts occur at the required supports; no servo tie holes remain:

| Support (mm) | Nearest bottom body/pad (mm) | Nearest top body/exposed pad (mm) |
|---|---|---|
| 4,4 | R462.2 15.406770 | C400.2 6.612111 |
| 42,4 | J410.4 6.164950 | J410 body 4.299999 |
| 4,44.3 | C32.2 4.536177 | LED2.2 3.807887 |
| 3.7,86 | R83.2 6.375048 | TP80.1 5.543014 |
| 42,86 | J122.1 7.284683 | J122 body 4.430001 |

These pass bottom 3.5/top 3.8 mm limits. The all-bottom native courtyard-to-THT minimum is 1.535488 mm at R151/R152 to J122.3, above 1.5. The (4,44.3) nominal washer disc still includes ordinary 3V3 via copper at radius 3.260399 mm and masked 3V3/NRST tracks at 3.410399/3.421392 mm; no non-GND surface track/via enters the other four discs. Nylon hardware, covering and full underside insulation remain required.

## Card, sled and stack

The complete rendered Molex G sheet gives 13.60 x 14.50 x 1.90 mm with +/-0.15 general tolerance. Native pads/pose and the conservative inferred closed socket/card allocation give x17-31,y18.3-33.8,z-3.7 to-1.6 mm. Its bore margin is15.686423 mm and nearest support16.710775 mm. Maker G does not dimension the open sweep or card seating. ORDERING 8.4 now explicitly requires PCB removal from a continuous sled or a physically qualified access window: **R11-MEC-03 closed as an instruction gap**, not a lid test.

L1 B(25,74.6) is the deepest model: 3.015825 mm below the PCB bottom. [Sunlord Rev11 Table 4-1 p4](https://www.alfatec.de/fileadmin/productfiles/datasheets/sunlord_swpa4030s_series.pdf) specifies 3.0 mm maximum body height; the model is conservative in height. Four-millimetre standoffs give 0.984175 mm nominal model-to-plate gap. Retained nut/screw assumptions independently reproduce h+t<6.018413 mm at x4/42 and<5.365256 at x3.7; the conservative <6.0/<5.3 worksheet and default h=4/t<=1 fit those nominal assumptions. Default worst nut corner retains 0.145392 mm radial margin. Actual hardware maxima, hole eccentricity, plate strength, solder tails and tolerances remain unmeasured.

Fresh optional D5 point-pinned modeling with current 70.297599 g mass allowance reproduces 181.306095 Hz. At 100 g, the maximum sampled deflection over the actual bottom body extents leaves 0.274406 mm under C431, 0.348172 under C421 and 0.524648 under L1 at h=4. The h=3.5 sensitivity has model overlap at C431/C421. Use the selected 4 mm starting stack and physically qualify the installed assembly; neither 3.5 mm alone nor this inferred model establishes 100 g clearance, and no frequency release threshold is reinstated.

Read-only VEHICLE gives shroud end joint+47, bulkplate top-44.6, about 80 mm battery and old 44-48 mm lead zone: the inherited stack arithmetic places the aft edge +79.4 to +83.4, 32.4-36.4 mm beyond the shroud. These are estimates. Enforce OQ-7 including axial tolerance; the actual pack, external modules, wires, sled and rail-accessible switch are not fitted evidence.

## IMU and closure

Original ST [DS14623](https://www.st.com/resource/en/datasheet/lsm6dsv320x.pdf), rendered Rev 1 Figure 5 p9 and Figure 32 p187, was inspected from its maker-document mirror after the current full download failed. The indexed official Rev 3 p9 agrees on pin map. Native U4 is B180 at (17,45.9), pad 1 (18.21,45.15). The maker bottom-view pattern gives +X_imu=-x_board,+Y_imu=-y_board,+Z_imu outward from the bottom: roll=-gyro_Y and forward thrust=-a_Y agree with the binding. Lever x=-6.0 mm; model-centre z=-2.059994 rounds to the explicitly inferred -2.06 mm. Use the right-handed IMU frame for cross products; physical sign/die-centre measurements are pending.

No component-side via or saved fill intersects an intentionally conservative 3.2 x 2.7 mm U4 guard, larger than maker 3.05 x 2.55 maxima, or the U5 nominal body. No new axes/lever discrepancy was found. All seven terminal masses/wire allowances and the card remain in the current retention worksheet; actual 5x100 g clamp/joint/hinge strength, vibration, staking and U4/U5 thermal behavior remain unqualified.

**R11-MEC-01 / R11-BOM-01 closed** by fresh source reconstruction and placed geometry. **R11-MEC-02 local worksheet portion closed** by current ORDERING 8; only the parent mirror remains carried above.

Executed: independent native extraction/body/support/via/fill measurements; `fit_check --profile r10` exit 0; selected `check_r10` M-1/M-3/M-5/M-6/M-7/P-11 all pass; fresh optional plate/local-gap calculation; source PDF visual inspection; PCB SHA before/after unchanged. No DRC, full gate, build, CAD save, Git mutation, GUI retry, implementation or other-worktree write was performed. Other existing part models were geometrically surveyed, not exhaustively re-certified to original maker tolerances. No current-round peer reports were read.
