# M3 requirements and implementation status

> Repository note: the complete projects and review packages of the historical candidates (CORE / PWR / UART / USB / GNSS / PDIAG) are not included. The repository holds the current M3-ASSY-R5 KiCad project (generated from the R4 board in git; R4 itself was generated from the R3 files), plus the R1 board under `reference/m3_assy_r1/` that the v0.8.1 firmware is bound to. The older candidates are mentioned below only as the evolution record.

Last updated 2026-10-12. Governing requirements: M1/M2 merged into one board, easy to diagnose, at most three PCB iterations; "10× redundancy" means independent protection layers, not a blanket 10× component derating. **M3-ASSY-R2 was the first candidate with every hardware function in the requirements; R3 dropped the GNSS (owner decision); R4 is R3 with its validation fixes; M3-ASSY-R5 (R4's circuit on a two-sided 46 × 100 mm board) is the current one. All are CAD designs with a manufacturing package, not measured or flown boards.**

## Current candidate: M3-ASSY-R5 (two-sided re-layout, 46 × 100 mm)

Design record: [docs/M3_R5.md](docs/M3_R5.md); requirements: [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md); ordering: [docs/ORDERING.md](docs/ORDERING.md). R5 is R4's schematic and BOM, unchanged, on a new board: generated from the R4 board by `m3_design/r5_build.sh` (`r5_pcb.py`, `r5_routes.py`, `r5_maze.py`, `r5_route.py` with the Freerouting session in git, `r5_finish.py`, `r5_post.py`). **232 footprint positions / 205 fitted parts / 24 test pads / 3 tooling holes**, as R4.

What changed (details and reasons in M3_R5 §1):
- **Board:** 46 × 100 mm (R4: 46 × 193 mm), parts on both sides: top 89 (80 SMD, 9 through-hole) and 2 test pads; bottom 116 SMD parts and 22 test pads. Five M3 holes (the corners and mid-span at (4, 46)); two Ø3.2 tie holes for J122's plug tie.
- **Floorplan:** power entry at the aft edge, the MCU behind it, USB-C, the servo header and SWD in the middle, the pyro block (R4's, moved as one rigid group) at the forward end; the IMU and barometer on the bottom (the IMU's Y and Z axes flip: roll is +gyro_Y, the opposite sign to R4).
- **Routing:** critical nets scripted on a grid router (0/45/90°); the rest by Freerouting v2.4.1, then the grid router for what it leaves.
- **Requirements changed:** P1 (length and position in the bay), P2 (sled: five standoffs, the corners and mid-span, plate clear of the bottom parts), F4 (DC solve), M3 (two-sided fixed fees).

Verification, stated separately:
- **CAD checks (done)**: `tools/check.sh`: DRC 0 (pyro spacing rules included), unconnected 0, schematic parity 0, ERC 0; audit OK; no silkscreen outside the outline. `m3_design/check_actuators.py`: OK. `tools/fit_check.py`: OK (worst margin 0.11 mm, C84 on the top; deepest bottom part L1 at 4.62 mm, bottom margin ≥ 2.34 mm). `tools/export_fab.py`: 84 lines, 205 placed, nothing missing; `tools/jlc_orient.py --verify-cpl`: 84 top and 112 bottom rows rebuilt, exit 0.
- **Independent evaluation (CAD, datasheets):** two passes of six independent reviews (pyro, power, signal integrity, DFM, fit, silkscreen) against REQUIREMENTS.md. Pass 1: no Critical, nine Majors, fixed or recorded (M3_R5 §1b). Pass 2, on the re-routed board: no Critical, three Majors, all fixed: a via in J9.3's through-hole pad, the IMU's roll sign in the record (it is +gyro_Y), and bottom-side designators beside other parts (M3_R5 §1c). Pass 3 (one reviewer) confirmed the three fixes and found no new Critical or Major. A robustness round then kept live copper 1 mm from the bare gate test pads and re-routed (M3_R5 §1d); pass 4 (six reviewers from first principles, on robustness) found no Critical and two Majors, fixed: an overlap-only PULLPIN joint and corner-only mounting (a fifth, mid-span hole) (M3_R5 §1e). Pass 5 (two reviewers) confirmed both fixes; no open Critical or Major. The pyro block is R4's to the micrometre (41 footprints, the same .kicad_dru, the same solder-bridge spacings); its DRC rules were shown live on the new copper.
- **Calculation:** servo feed DC solve (Q121 → J122, 0.05 mm grid) 4.82 mΩ, 37.1 mV and 0.29 W at 7.7 A, all of it on the In2 RAW_ACT strip at mid-path (R4: 5.05 mΩ, 0.30 W); the reverse hot-plug model is R4's (same circuit).
- **Cost and stock (2026-10-12)**: Standard PCBA: $55.14 parts + 81 codes × $1.53 feeder fee / 5 = $79.93 per board (target ≤ $84.41); 47 unique extended codes (target ≤ 48). **Two-sided fixed fees $83.96 per order** (setup, stencil, fixture; one side: $50.19; JLC may add a $14.93 handling fee). No shortage; U4 is thin (5 in stock for 5 boards).
- **Simulation**: none (the circuit is R4's).
- **Firmware**: none for R5; the board binding in `m3_firmware/build.py` must be redone (M3_R5 §3: IMU axes).
- **Physical tests**: none. The sled fit is not physically verified.

Open owner decisions: as R4 (below), plus the sled design (REQUIREMENTS P2).

Minor findings recorded for the next revision (not reworked; M3_R5 §1b–1c):
- MCU-side pyro sense/gate vias 0.28–0.88 mm from bottom parts (R168, R171, C23), against L10's 1.0 mm wording.
- Jogs of 0.3–0.5 mm on QSPI_CLK/IO0/IO2/NCS and SPI1_SCK, QSPI_NCS's R10 branch drawn beside the main trace, a USB_DM
  hairpin at its via.
- C150/C151 (RAW_ACT bulk, bottom) have their nearest GND vias 6–8 mm away; the camera supply trunk (RAW_PROTECTED) is
  0.4 mm for about 78 mm (about +10 °C at 1.24 A); U9 OUT and the camera feed change layer on single vias.
- The RAW_ACT In2 strip has two necks at J3's shell slots (2.75 mm), not one; covered by the bring-up stall test.
- Silkscreen: J1's BAT+/GND legends sit beside D9; bottom igniter labels crowd unlabelled test pads; R32's label sits
  under R33; J122's bottom "2" 1 mm off its row; no SWD pin legends at J2; TP122's label is nearer R76 (top) than TP122; J1's "SW" legend and the U1/U3/J3
  designators sit under package bodies (their footprints have no F.Fab outline); some hidden designators could be
  placed by a second pass; the bottom-face instructions (fuses, ARM plug) face the sled.
- ORDERING's 5 mm tab clearance names only MLCCs: TP76, R100, R101, U12, D123 and R162 sit closer to a tab.
- R81's designator sits 0.44 mm from R83.1 (in R81's row, above R83); J1's designator is nearer C89 than J1.
- Servo cable-side nets (SERVO*_OUT, before the 1 kΩ) run 72–81 mm unclamped through the pyro block; put the series
  resistors or a clamp back at J122.
- Decoupling farther from its pins than R4: C29 5.9 mm from U3 VCC, U12's VCCA 9.4 mm, U10 and U11 11–35 mm; C121
  (470 µF) on one 0.5 mm track to J122.8; C80/C96 11.5–15.4 mm from U9's input.
- GND pour 0.15 mm from the RAW_ACT through-hole pins (R4: 0.25 mm); give them a 0.3 mm local clearance.
- 84 small passives have one pad in a GND pour without thermal relief (tombstoning risk; 43 are 0402).
- The second reflow of two-sided assembly is not yet checked against U5, C84 and LS120's cycle limits; the edge-rail
  tab windows could move clear of TP76/R100/R101 and add corner support; BAT_IN on the bottom within the washer
  radius at hole (4, 4) (nylon hardware required); 1210s C76/C92 about 4 mm from corner standoffs.
- Leftover routing fragments: LOGIC_SS/LOGIC_ILIM 0.14 mm overshoots at (28.35/29.15, 12.45), a redundant LOGIC_SOURCE_ST
  diagonal on In2 near (25.9, 17.6); `close_joints` pairs only end to end (an end grazing a track's side is not caught).
- IMU_INT1 vias at (20.85, 32.55) and (27.45, 41.75) have their nearest GND via 1.8 and 1.5 mm away.

## Previous candidate: M3-ASSY-R4 (R3 validation fixes, new IMU, thirteen evaluation passes)

Design record: [docs/M3_R4.md](docs/M3_R4.md); requirements: [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md); R3 findings: [docs/R3_VALIDATION.md](docs/R3_VALIDATION.md); ordering: [docs/ORDERING.md](docs/ORDERING.md). R4 is generated from the R3 files by `m3_design/r4_build.sh` (`r4_lib.py`, `r4_sch.py`, `r4_pcb.py`). **232 footprint positions / 205 fitted parts / 24 test pads / 3 tooling holes**, 14 schematic sheets.

What changed (details and reasons in M3_R4 §1–1m):
- **IMU:** U4 is the ST LSM6DSV320X (adds a ±32–320 g channel; flight 2 reaches ~37 g).
- **Input protection:** D8 SMBJ12CA (a wrong 3S pack no longer destroys it); 470 kΩ on each side of the external contact; UVLO lowered to 4.45–4.61 V; C87 switch-bounce ride-through; OVLO release above a full pack; 2 × 10 µF at the input plus an RC damper (2 × 22 µF + 0.33 Ω) and a 10 kΩ input bleed, so a reverse hot-plug stays inside U9's input limits even soon after an unplug (modelled with measured DC-bias curves); USB OV trip raised to 5.66–6.37 V.
- **Pyro safety:** black ARM and orange igniter 2-position terminals with top labels; TP122/TP123 on the bottom; nine pyro spacing rules in DRC (RAW_ACT ≥ 1.0 mm from the buses and ≥ 0.5 mm from every pyro control net; bus/igniter/drain ≥ 0.5 mm from gates, other live nets and GND, ≥ 0.3 mm from sense nets; gate nets ≥ 0.3 mm from other live nets inside the pyro block; exposed live pads ≥ 1.0 mm from sense and gate pads, against one solder bridge); soft-termination drain capacitors; every sense divider's top split into two 5.1 kΩ in series (pass 11) and its bottom into two 2 kΩ in parallel (pass 12), so one shorted or open resistor leaves its MCU pin at ≤ 1.4 V and an igniter at ≤ 1.4 mA, plus a 4.7 kΩ series resistor at each ADC pin (R168–R172, passes 9–10) as a second layer; mandatory local coating of the pyro block and J2.
- **Servo feed:** one continuous In2 RAW_ACT pour under the F.Cu ring (47 stitching vias).
- **Debug header:** J2.6 unconnected; BOOT0 ends at its pull-down (pass 9: the run under J2's base passed 0.18–0.19 mm from 3V3 and NRST).
- **Sensors:** full-body copper/via keep-outs under the IMU and MS5611; direct decoupling; RC (not LC) 3V3A filter; MS5611 paste on TE's land size.
- **Fit and assembly:** JST PH pull-pin header; JLC placement corrections incl. the DB128V terminals' 180° body correction; USB-C legs pin-in-paste plus hand finishing; AON6403 windowpane paste; R166 on UNI-ROYAL's land; printable silkscreen marks kept inside the outline (gate check); order-number placeholder; JLC tooling holes; ENIG stackup in the job file; ORDERING pins green mask, plugged vias, single-board delivery, the paste layer as supplied and no washing; the order is Standard PCBA (240 ± 5 °C reflow, tab-routed edge rails) because U5, LS120 and C84 allow only a 250 °C peak, below Economic's 255 ± 5 °C.
- **Stock and cost:** U8 → AP63301WU-7 (the AP63300 had 5 in stock); Basic parts for the 100 nF and 10 k lines that carried minimum-purchase or 0.1 % premiums.

Verification, stated separately:
- **CAD checks (done)**:
  - `tools/check.sh`: DRC 0 (including the pyro spacing rules), unconnected 0, schematic parity 0, ERC 0; audit OK; no silkscreen outside the outline.
  - `m3_design/check_actuators.py`: OK; it pins the safety parts by LCSC code and checks every spacing rule's content; 78 seeded faults each make it or DRC fail (passes 9–12 added the load-switch nets, the sense series resistors and the split dividers; the final iteration rule H).
  - `tools/export_fab.py`: 84 lines, 205 placed, nothing missing, every placement rotation verified; an assembly drawing from the fab layers (every designator, hidden ones included).
- **Independent evaluation (CAD, datasheets):** pass 1 by six reviewers, passes 2 and 3 by five each, pass 4 by two focused reviewers (input protection; DFM, assembly and fit), pass 5 by five reviewers from first principles, pass 6 by two focused reviewers, passes 7 and 8 by one each, pass 9 by five reviewers from first principles, pass 10 by one focused reviewer, against REQUIREMENTS.md. Pass 10 found no Critical or Major issue; it added R172 on PB0 (for the arming option where the board powers up armed), corrected what the record claimed about the pins in a resistor-short fault, and tidied four designators (M3_R4 §1k). Pass 11 then closed the one gap pass 10 had kept: every sense divider's top is now two resistors in series, so no single shorted resistor drives an MCU pin past its ratings (M3_R4 §1l). Pass 12 (one focused reviewer) found no Critical or Major issue; its fixes make the divider bottoms two parallel resistors (so an open is tolerated too), widen the ARM stack's facing bus/sense pad gaps to 0.94 mm, un-shadow pyro rule B, and hide twelve designators that had no unambiguous spot (M3_R4 §1m). Pass 13 (one focused reviewer) found no Critical or Major issue; it measured four more single-solder-bridge paths past a divider (0.65–0.82 mm), seven neighbouring designators that missed the label rule, and document nits (M3_R4 §1n). A final CAD iteration fixed them: the ARM stack became two vertical columns, five parts moved, and DRC rule H now keeps every exposed live pad 1.0 mm from every sense and gate pad (M3_R4 §1o). Pass 14 (one focused reviewer) found no Critical or Major issue in that iteration; its findings were fixed in it: R143 moved clear of the actuator switch's gate pad and rule H covers that gate, the label rule measures to pad edges, the assembly drawing shows every designator, and the record no longer claims rule H covers 3V3 next to a gate (the cold test shows that case). Pass 9's Major (a single shorted 0402 divider resistor put armed drain or bus copper on an MCU analog pin, with the igniter in the drain-side path) is fixed on the board with R168–R171, and BOOT0 no longer runs to J2; its other findings are procedure, checker and document fixes (M3_R4 §1j). Pass 8 found no board or tool defect; its bench-procedure findings (safe probing of the armed pyro gates) are fixed in ORDERING §5 (M3_R4 §1i). Pass 7's Major (a pyro bench gate that a healthy board could not pass) is fixed in ORDERING §5 (M3_R4 §1h). Pass 6's Majors (owner-fitting the barometer against TE's no-hand-soldering rule, now Standard PCBA instead; no armed-not-firing gate; the remote-plug fuse location; F6's claim about FMEA F-1) are fixed (M3_R4 §1g). Pass 5's Majors (JLC's reflow above two parts' limits; the control window and the watchdog rule contradicting the project and the FMEA; a TIM15 instruction in the record that could fire a channel) are fixed (M3_R4 §1f). Pass 4's Major (a reversed pack plugged in while the input still held charge) is fixed with the input bleed; pass 3's board Major (reverse hot-plug margin) is fixed; its other two Majors are the open owner decisions below. Pass 1's Majors (3S TVS, J1/J9 entry direction) and pass 2's (ARM/igniter terminals interchangeable; coating made optional against the margin prescription; post-brownout behaviour unspecified; U8 stock) are fixed or recorded; the Minor findings are fixed or recorded as deviations (M3_R4 §1b–1f, §2).
- **Calculation:** servo feed DC solve 5.05 mΩ / 0.30 W at 7.7 A; reverse hot-plug harness model with Samsung's measured DC-bias curves (0.1–2 µH, ≥ 0.03 Ω): U9 IN ≥ −14.6 V and ≤ 9.2 V/µs at every corner from the ≤ 2.0 V the bleed leaves within 0.73 s of an unplug with the switch open, about 1.3 s with it closed (pass 9; hence the 2 s rule) (≥ −13.0 V from an empty input up to 1 µH).
- **Cost and stock (2026-10-09)**: Standard PCBA: $55.22 parts + 81 codes × $1.53 feeder fee / 5 = $80.00 per board (R3: $84.41 at Economic's fees); Standard's fixed fees $50.19 per order (setup, stencil, fixture; JLC may add a $14.93 handling fee; Economic: $9.71); no shortages, no line under twice its order.
- **Simulation**: no SPICE (ngspice not installed).
- **Firmware**: none for R4; the board binding in `m3_firmware/build.py` must be redone (firmware consequences: M3_R4 §3).
- **Physical tests**: none.

Open owner decisions:
- ARM link physical form and reachability (FMEA H-6, V-18): how the links go in on the pad (REQUIREMENTS F8). The link fuses cannot sit at the terminals inside the coupler (ORDERING §7).
- Flight 2's servos: stall current within F4's 1.92 A per servo, and hinge moments above M1.2 (the CFD sweep stops there).
- External switch part.
- Servo-fault containment (recorded as an accepted risk; per-servo inline fuses recommended for flight 2).
- The control window's exact start and stop points (a flight parameter; the board supports any window, and F7 requires the servos at neutral ≥ 200 ms before any fire). Tab-to-neutral within 50 ms of a hang is allocated to firmware in REQUIREMENTS F6 (IWDG ≤ 32 ms fed only by the 100 Hz safety task, bounded roll-interrupt run time, neutral first after reset; about 48 ms with NRST release); the board supports it as built.
- The camera model (it must not back-feed its 5 V input).

## Previous candidate: M3-ASSY-R3 (GNSS removed, 46 × 193 mm, cost-down)

Design record: [docs/M3_R3.md](docs/M3_R3.md). R3 is R2 with the GNSS (U6, C33, C34, GPS nets, its 3V3A branch) removed and the board cut from 238 to **193 mm** so it fits the main-section electronics bay. The forward M3 pair moved to y = 189. **No remaining track, via or footprint moved** (checked against R2 by UUID and geometry). **205 footprint positions / 180 fitted parts / 25 test pads**, 14 schematic sheets. The 1 k 1 % resistors moved to a JLC Basic part.

Verification, stated separately:
- **CAD checks (done)**:
  - `tools/check.sh`: DRC 0, unconnected 0, schematic parity 0, ERC 0; audit OK.
  - `m3_design/check_actuators.py`: OK.
  - `quality_audit` unit tests: 12/12.
  - `tools/export_fab.py`: 75 lines, 180 placed, nothing missing.
  - Pre-fab pin-mux audit against DS12110 Rev 11: no wrong assignment (`docs/M3_R3.md` §6).
- **Cost and stock (2026-10-05)**:
  - Parts: $54.94 per board at 5 boards, 48 unique extended codes; all-in about $100–110 per board.
  - The $75 target is not reachable without giving up robustness (`docs/M3_R3.md` §4).
  - **U4 ICM-45686 is out of stock at JLC**; it needs Global Sourcing or consignment.
- **Simulation**: not re-run (ngspice not installed). The actuator band is unchanged.
- **Firmware**: none for R3 yet (plan in `docs/superpowers/plans/`).
- **Physical tests**: none.

Open owner decisions:
- PB0 4.0 V FT_a limit (R125 → 3.3 k option).
- PE4/PE5 trace-pin risk, accepted procedurally.
- `PYRO*_GATE_N` naming.
- Cost relaxations.
- U4 sourcing.

## Previous candidate: M3-ASSY-R2 (actuator merge)

Design record: [docs/M3_ACTUATOR_MERGE.md](docs/M3_ACTUATOR_MERGE.md). One 46 × **238** mm four-layer board: R1 plus a 52 mm actuator band inserted between the battery/logic-power block and the camera block. **208 footprint positions / 183 fitted parts / 25 test pads**, 14 schematic sheets.

Added in R2 (all from the frozen M1 design as corrected by `MARGIN_PRESCRIPTION.md`, `FMEA_REDUNDANCY.md` and `CIRCUIT_REVIEW.md`):
- **Actuator power switch**: back-to-back AON6403 load switch from the battery input, gated by the logic path so the single external switch still controls everything; 470 µF bulk; RAW_ACT sense/bleed.
- **Dual pyro, single-deploy redundancy (owner ruling 2026-09-25)**: two AON7524 low-side channels on **two independently fused buses** (FMEA H-5); 4-position ARM terminal (two-fuse plug) and a separate 4-position igniter terminal on opposite long edges; per-bus arm sense, per-channel continuity, cold pull-up for plug-out FET-short detection (H-1), gate networks per P0-1/P0-2, PE3/PE6 sentinels.
- **Four servos**: 3×4 header on the centreline, 1.0 k series (P0-5), 10 k pull-downs, SRV05-4 clamp, zip-tie holes.
- **Pull-pin** (BAT54S-clamped, PC14) and **buzzer** (MLT-8530 on PA5; the §3.4 pad-pairing question is closed from the maker's specification).
- **Backup altimeter: fully isolated by ruling** — no interface on this board.
- Manufacturing package: `tools/export_fab.py` → Gerber/drill zip, JLC BOM and CPL in `m3_design/assembly_review/fab/`.

Verification, stated separately:
- **CAD checks (done)**: `tools/check.sh` = DRC 0 / unconnected 0 / schematic parity 0 / ERC 0, metadata and 3D-model audit OK; `quality_audit/verify_board.py` (refilled zones) PASS; `m3_design/check_actuators.py` (arming break, gate networks, sentinels, servo chain, buzzer/pull-pin mapping read from the PCB copper netlist) OK, with negative tests that break the ARM break and a sentinel.
- **Software tests**: `quality_audit` unit tests pass; **no R2 firmware exists** and v0.8.1 must not run on R2 (see `m3_firmware/README.md`).
- **Simulation**: ngspice suite for the R2 actuator band in `m3_design/sim_r2/` (`FINDINGS.md`): every case for the current design passes (switch, fire, fired-into-short, plug insertion, sense states, chafe). The shorted-igniter brown-out found in the merged R2 is fixed by R134/R135 (`docs/M3_ACTUATOR_MERGE.md` §2.6).
- **Physical tests**: none. No board has been built.

What changed in R1 copper, for reviewers: everything below y = 34 mm moved +52 mm unchanged; seven tracks that crossed the cut continue as straight B.Cu lanes; LED_RED was re-routed to PE8; the CAM_PWR_EN and CAM_FAULT_N routes under U1's top-left corner were re-routed to free the servo/continuity escape; U12 gained its missing LCSC code (C5186957).

Still open before a fab order (details in the design record §4): real-board power-up and fire tests into dummy loads, servo stall current vs. the 2.6 mm feed neck (≈ 7.7 A all-stalled is an inference, not measured), the in-line 15 A battery fuse and 5 A fast plug fuses as vehicle hardware, JLC rotation/THT review of the CPL, R84/R86/R9 sourcing, sled/enclosure fit of the 238 mm board.

## Previous candidate: M3-ASSY-R1

[Assembly and footprint review](m3_design/assembly_review/ASSEMBLY_REVIEW.md), [v0.8.1 bench diagnostics](m3_firmware/ASSEMBLY_DIAGNOSTICS.md). One 46 × 186 mm four-layer board, 135 footprint positions / 115 nominally fitted parts / 20 test points. The two LEDs have separate lands, cathode silkscreen and 3D orientation corrected against each manufacturer's drawing; U3's 208 mil package choice was confirmed. All 2201 existing tracks/vias were kept; native DRC, unconnected items, schematic parity and ERC are all zero. Functionally it provides ordinary power, acquisition, ~1 Hz diagnostic logging, USB, GNSS and the camera interface; **it is not a finished product with every rocket function, and there is no real-board or manufacturing-release evidence**.

M3-PDIAG-R1 and firmware v0.8 remain as the previous baseline; their input FAULT/ST signals and history carry over. The new firmware binds to the exact ASSY-R1 board, and the host tools reject a mismatched board ID or build identity. Active attitude control, servo/pyro actuation and a complete recovery backup are **not** implemented in this revision and must not be counted as delivered.

The host side has a [unified triage entry point and test-point map](diagnostics/TRIAGE.md): the network and location of the 20 test pads and 10 auxiliary test points are cross-checked against native KiCad data; failed or partial USB captures still produce a report linking faults to a branch and the next test point. The independent-instrument template starts empty, so power, device and whole-board stability have **no** physical PASS from it.

## Evolution record (not in the repository)

| Candidate | What it added | Evidence at the time |
|---|---|---|
| PWR-R3 | Battery / USB logic supply, acquisition core and camera branch on a provisional 46 × 168 mm board; 121 positions, 17 test pads, U6 GNSS not fitted, 103 fitted parts, 8 schematic sheets | 91 software/CAD regression tests and 5 passive hold-up simulations bound to that revision; no board measurements |
| UART-R1 | Camera UART transmit/receive, a separate camera logic supply, a reset-default-off enable and two test points; 133 positions, 113 fitted, 9 sheets | DRC/ERC/parity zero; 10 wrong-wiring / version-identity tests passed |
| USB-R1 | Corrected the ordinary-GPIO USB cable-detect divider, added R110 and TP92; 135 positions, 114 fitted, 10 sheets | 16 USB negative / numeric tests passed; 3 passive RC simulations matched the analytic results, one deliberately showing detection fails under strong back-feed |
| GNSS-R1 | U6 changed from DNP to fitted; corrected the receiver-area ground plane, distance to flash layer changes, stencil and 3D envelope | 238 software regression tests and 10 CAD error-input checks passed |
| PDIAG-R1 | Battery, USB and camera FAULT inputs and the source-select ST signal with current/historical evidence | Firmware v0.8 |

Firmware history: v0.2 bench acquisition (ADC3 voltages, MS5611, HSE / IMU / flash identity, SWD readback of 2–30 records to JSON/JSONL); v0.3 camera UART query; v0.4 raw IMU observations; v0.5 on-board diagnostic log with single/quad-line write verification; v0.6 USB CDC (pinned TinyUSB 0.21.0, HSE/PLL3 48 MHz USB clock, PD15 software VBUS detect); v0.7 GNSS receive / 1024-byte log / USB export; v0.8 power status; v0.8.1 binding to ASSY-R1. All are compiled and software-tested only; **none has run on a real board**. Older firmware images cannot be used as compatibility evidence for a newer board.

## Requirement status

> Historical table (R1–R2 era), kept for its evidence trail. The current requirements and their verification are in [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md) and the R5 and R4 records above; where a row below still says GNSS, 46 × 186 mm or an LC filter, R3/R4 superseded it.

| Requirement | Current evidence / implementation | Still needed for the complete M3 |
|---|---|---|
| Merge the two boards into one | M3-ASSY-R1 is a single-board candidate for power + core + camera supply/UART + USB + GNSS; 10 schematic sheets consistent with the PCB | Other interfaces not all merged; this does not equal all functions of the old two boards |
| Fits the bay (Ø54.6 mm bore, Ø50.8 mm inside the coupler), installable / maintainable | R5: 46 × 100 mm with parts on both sides, top face on the bore axis (REQUIREMENTS P1/P2; R3/R4: 46 × 193 mm). Historical: core baseline 46 × 96 mm; candidate provisionally 46 × 186 mm; height envelope for the 14.5 mm terminals / 12.8 mm C84 capacitor | All connectors, plugs, harnesses, fasteners, sled, clearances and a physical coupon; final length not frozen |
| 2S supply, switch, reverse protection, logic hold-up | PWR-R3 added U9 battery protection, U10 USB current limit, U11 source selection and 330 µF hold-up; contacts are low-current enables | Start-up / switchover / back-feed / thermal / USB current and coordination with external protection must be measured; the 100 µs typical switchover time is not a maximum |
| Stable sensor supply | Core has the AP63203, L2 and sensor supply | Start-up, input capacitance / USB load, LC damping, tolerance / bias and measurements |
| STM32H743, USB, SWD, crystal | CORE schematic/PCB reconciled, DRC/ERC zero | Real power-up, clocks, buses, and running without a probe |
| USB connection and download | USB-R1 hardware; v0.6 implements the 48 MHz PLL3, CDC stack, descriptors, GPIO plug detection, snapshot / log download and identity checks; software fault tests pass | Real clock accuracy, enumeration / suspend / cross-platform behaviour, throughput, power / back-feed / inrush and signal integrity; development VID/PID and current compliance unresolved |
| IMU / barometer recording | Core circuit; pressure/temperature acquisition; v0.4 adds raw IMU samples with timestamps / configuration / error diagnostics | Continuous storage chain, real interrupt line, built-in self-test, real liveness / noise / accuracy; scripted software tests do not replace measurements |
| QSPI logging and export | Diagnostic append at up to 1 Hz with single/quad-line write-back verification; v0.7 records the full 1024 bytes including GNSS/USB; recovers older prefixes; software fault tests | Real quad-line operation, throughput / capacity, power-loss consistency, real USB download; model tests are not board passes |
| GNSS | U6 fitted in the candidate; 9600 baud USART6 receive, read-only identity / PVT queries, raw bytes / errors / freshness diagnostics, full log and USB export; software tests pass | Real UART / power / cold and warm start, antenna / enclosure / structure / accuracy; currently ~1 Hz bench observation, not a mission validation |
| Camera 4-position terminal, 5 V / GND / UART × 2 | UART hardware routed; v0.3 implements one device-information query with raw bytes / CRC / timeout diagnostics, off by default | Camera logic levels, power-down isolation, real protocol communication, recording and the full camera application still to be verified; the old v0.2 does not drive this UART |
| Servos and actuation interface | R2: four channels routed (3×4 header, 1 k series, pull-downs, SRV05-4), actuator rail switched with the logic path | Stall-current / thermal check of the header feed, servo firmware (TIM5, quiet-before-fire), real-servo test |
| Recovery backup and physical interlocks | R2: single deploy with two independently fused on-board channels; commercial backup altimeter kept **fully isolated** (ruling 2026-09-25); ARM plug is a complete break of both buses (PCB-netlist check) | Recovery firmware, ARM-plug hardware (two 5 A fast fuses, locking connector), ground ejection tests; the backup altimeter's own installation |
| Pull-pin, buzzer / indicators, spare interfaces | R2: clamped pull-pin (PC14) and driven buzzer (PA5) routed; LED_RED moved to PE8 | Firmware, audibility inside the closed airframe, pull-pin harness |
| Automated diagnosis and fault localisation | SWD register readback, voltage / pressure acquisition, camera UART and raw IMU bytes / errors; sequence numbers / bound hashes and JSONL evidence; v0.8 input FAULT/ST sampling and history | Real-board probing, instrument capture and a fixture still to be done; no real measurements |
| Trustworthy footprints / 3D | R2: all 99 BOM lines / 205 positions checked against manufacturer datasheets (pinout, land pattern, polarity, part number, 3D orientation); every issue found was fixed (`docs/R2_VERIFICATION.md` §3) | Physical fit of harness, plugs and sled; envelopes are not physical proof |
| Clean manual layout and routing | CORE and camera copper kept; new power paths and fine-pitch escapes hand-routed, support nets searched with constraints then straightened; native checks pass | Remaining critical nets and return paths on the full board; the old M2 is not final |
| Simulation and reliability study | The power candidate has 5 ngspice passive hold-up cases bound to the PCB hash, cross-checked analytically | No complete regulator / current-limit / thermal model or measured correlation yet; RC simulation does not prove whole-board stability |
| ≤ 3 iterations, replaceable / decoupled | Traceable engineering revisions, a diagnostic evidence framework; legacy coupon files | Quantified exit criteria before each fab, reworkable design, assembly strategy and revisions after measurement |
| Manufacturing package and cost | R2: BOM / CPL / Gerbers from `tools/export_fab.py`; every line has an LCSC code and JLC stock for 5 boards except U6 (consign, DigiKey); CPL orientation corrected per LCSC footprint; how to order: `docs/ORDERING.md` | Quote for the shipping destination; nothing ordered; bench-prototype only |

Items from the original requirements (ADXL375, microSD, LoRa, board width / copper weight, etc.) have been through several rounds of trade-offs. This table does not silently restore old configurations, nor silently drop unimplemented items; they must be closed with the final functions and verification evidence of the unified version. The frozen two-board architecture has been superseded by the single-board requirement (see `docs/HISTORY.md`).

**Priority**: on the routed power / acquisition candidate, add continuous acquisition and on-board logging, USB, real camera communication, purchasing and mounting constraints and dynamic board evidence; keep listing every unimplemented requirement explicitly. Every acceptance must distinguish software tool tests, design-rule checks, simulation and physical tests.

**R2 additions**: five 22 µF capacitors changed to the real Murata 1210 package, C82 moved 0.5 mm; 10 references (precision resistors, inductors, etc.) bound to specific part numbers, with maker and supplier evidence kept in the package. Exact bias capacitance and total cost are still open.

**R3 additions**: 28 more references given part numbers; corrected C70's minimum capacitance, C70/C81 unified as 4.7 nF C0G; D9 set to B340A-13-F. Added wrong-value / wrong-part-number / wrong-wiring negative tests and resistor TCR corner estimates. No selection has real-board dynamic, cold, assembly or stock verification yet.
