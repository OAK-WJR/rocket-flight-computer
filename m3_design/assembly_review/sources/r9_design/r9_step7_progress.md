# R9 step 7 (routing families): progress log

Step 7 of `r9_plan.md` §4: family modules rf_if, qspi_hse, pyro, servo, usb_swd, imu_baro, camera, status, power_ctl
(with the USB_LIMITED corridor step 6 deferred) as deliberate bus primitives (no autorouter, no hand-patched copper),
then a constrained short-link stage (links). Verify after each family: connectivity, DRC, route_check r9 with an empty
allowlist, per-family length / via budgets (total signal vias <= 70, stretch 55), P-7, D19.

## Session 1

- No step-7 log existed: fresh start. Read r9_plan, owner decisions, R9_DECISIONS (D-S1 … D-S6), step 1-6 handoffs,
  plan_spine (layer plan, routes, section 9), survey_topology, R8's r8_route*.py families and gate.
- Board in the worktree = step 6's `47fb298d…` (checked). Environment unchanged: no GUI session, so kicad-cli DRC
  runs through step 6's scratch shim (`<scratch>/s6/inj/nomouse.dylib`, still present) and r9_build.sh's stages are
  replayed by `<scratch>/s6/tools/build.py` (D-S6-14).
- Open on the step-6 board (DRC): 321 unconnected items; signal nets of every family, the 3V3 taps (22 pads), 3V3A
  (13), VLOGIC (R60.1), CAM_5V (U13.1, R104.1, C91.1), RAW_ACT (R177.1); GND (120, step 8's pours).
- Forced layer changes (pads on both faces): about 41 signal vias (QSPI 6, HSE 2, BOOT0 1, IMU 5, I2C 2, CC 2,
  VBUS_SENSE, USB_FAULT_N, NRST, BUZZ_DRV, BUZZ_OUT, PULLPIN, PULLPIN_EXT, VLOGIC_SENSE, V3V3_SENSE, BAT_FAULT_N,
  LOGIC_SOURCE_ST, BAT_ENABLE, CAM_UART_OE, CAM_5V_SENSE, CAM_FAULT_N, CAM_PWR_EN, RAW_ACT_SENSE_MCU, SERVO 4) on top
  of the steps 4-6 signal vias: the 70 budget leaves about 20 for crossings.
- Framework written: `m3_design/r9_route.py` (FAMILIES, Draw with dry run, u1_pin, pad / width / octilinear asserts).
- Design aid (scratch only, `<scratch>/s7/aid/`): `export.py` (board geometry to JSON), `router.py` (clearance fields
  and an octilinear A* that proposes polylines; the family tables are written from proposals by hand and DRC judges).

## Session 2 (after a context reset)

- rf_if done and gated in the real build: `r9_route_rf_if.py` (15 nets, 333.6 mm, 0 signal vias, worst ratio 1.257,
  61 bends); R310 / R313 / R315 re-placed in one row at the MCU end (r9_place.tsv, D-S7-02).
- The fence: step 4's `FENCE_X` is back to the closed fence (every opening <= 2.0 mm, so the step-4 gate's R-7 holds
  before any lane exists); rf_if opens its lane gaps with the new `Draw.move_via` primitive (six fence vias moved, one
  added: `FENCE_MOVES` / `FENCE_ADD`) and adds the grid via (23.05, 17.4) between its MISO and MOSI lanes (R-7 reach).
  The four 0.5 mm grid patches at U31's west pins / FB31 stay in step 4's `GRID_SMALL` (step-4 gate passes with them).
- `m3_design/r9_route_check.py` written (template incl. moved vias, DRC + parity with pending GND vias and the rail pads a
  family joins, route_check r9 with an empty allowlist, the family budget, S4 <= 70 board signal vias, the step-5 pyro
  functions, check_r9 minus M-2 / K-legends with K-contract's camera-bypass items deferred to camera, check_actuators).
- r9_build.sh: step-7 header and the rf_if stage pair appended. Replay of stages 5-15 (scratch runner
  `<scratch>/s6/tools/build.py --from 5 --to 15`): placement, RF strip, pyro, power and rf_if gates all OK; board
  `8a29b7e2…` (step 6's board changes with the R310 / R313 / R315 re-placement and the GRID_SMALL patches).
- Scratch: `r9/base` now holds the rf_if board (the next families' design base); base6 / work deleted.
- West region (U4 under U1's west pins; SPI1 / IMU_CS / INT1 / I2C / BOOT0 / QSPI_NCS): the routing aid showed the knot
  needs the pull resistor column R5 / R11 / R12 / R13 re-placed (search: 8/8 nets only with them removed). Analysis
  in the handoff (open items).
- qspi_hse written (`r9_route_qspi_hse.py`): R8's dives moved by (-5, -0.5) for IO0 / IO1 / IO3 / CLK / HSE_IN / HSE_OUT
  (6 nets, 6 signal vias, 7 GND vias PENDING); C25.2's GND via moved north (R8's spot is on the IMU body, M-7).
  QSPI_NCS, QSPI_IO2 and BOOT0 moved to imu_baro (D-S7-05): IO2's natural path (x 12.25 straight down) crosses the
  IMU's corner and the bump audit flags any detour drawn round it before the IMU copper exists. Scratch build: DRC
  only pending via_dangling; route_check: only GND (pending) items. Not yet in r9_build.sh.
- West corner (U4 under U1's west pins) studied with the negotiated router (`<scratch>/s7/aid/west5.py`, variants
  va ... v180e; `ratios.py` gives route_check's detour test per net): at U4's placed spot and rotation 0 no variant
  gives every net within route_check's detour test with U4.2 / U4.3 (GND) reachable: IMU_INT1's pin (U1.98) is the
  north-most of the west-face SPI pins while its pad is the south-most of U4's west column, so a short INT1 route encloses
  the two GND pads, and an INT1 route round them fails the detour test (MST 3.0 mm); MISO / MOSI / CS / SCK need wraps
  (nested-lane order against the pad order). U4 can only move east by <= 1.97 mm (Y1's courtyard; south is U3, west /
  north are P-10's margins): U4 at (13.9, 47.4) still leaves CS / MISO / MOSI over the detour limit. U4 rotated 180 deg
  (same spot, R10 re-placed): INT1 3.5 mm, MISO / MOSI / NCS / GND clean, SCK and CS within reach with a south-band via
  and pad-end entries. A rotation changes the axis map (M-7, M3_R5 section 3, unchanged since R5): owner question.
- Forward face: the servo lanes (U1.22 -> R150 west) must cross north of pins 17-21, whose stubs must dive before
  y 53.5; B.Cu there is C21 / C22 (3V3A) with one via gap (x 20.2-20.89): C21 / C22 need re-placing with the 3V3A rail.
- qspi_hse in r9_build.sh (stage pair after rf_if); gate OK (43.5 mm, 6 signal vias, worst ratio 1.383; board signal
  vias 15). r9_route_check's joined-pad check skips GND (GND pads wait for step 8 like the pending vias).
- D-S7-06: survey_constraints 1.4 makes the IMU's rotation free in R9 with a recorded axis map, so U4 turns 180 deg
  (r9_place.tsv), check_r9 M-7 keys the rotation on the title-block revision (R7 / R8 0, R9 180; test added in
  test_r9_check), r9_pcb.py turns the IMU rule areas with the part. Rebuilt stages 5-17: placement, RF, pyro, power,
  rf_if and qspi_hse gates all OK; board `27104536…`. tools/test_r9_route.py (19 tests) OK; test_r9_rf's B.Cu corridor
  test now compares against the built board's own corridor findings (step 7's lanes are what the corridors are for);
  test_r9_place / test_r9_pyro / test_r9_power OK.
- Decisions D-S7-01 ... D-S7-06 written to R9_DECISIONS.md.
- Next: imu_baro on the turned IMU (plan in the handoff), then pyro, servo (C21 / C22 re-placement with 3V3A), usb_swd,
  camera, status, power_ctl, links.
- Second replay of stages 5-17: every gate OK and the board byte-identical (SHA-256 `2710453673e71947c0786e79342a7f31fa20d076a00a4535c48afd55bc8b1d79` both times).
- test_r9_check (52 tests): 51 OK without a GUI; test_rule_h_seeded_suite_end_to_end needs kicad-cli DRC and passes with the D-S6-14 shim (45 s). All step-7 work is uncommitted.

## Session 3 (imu_baro, pyro, servo)

- Read the session-2 log / handoff, D-S7-01 ... 06, steps 5 / 6 handoffs. Scratch (`<scratch>/s6`, `s7`, `r9/base`) survived;
  the worktree board = `r9/base` = `27104536…` (checked). New scratch pipeline `<scratch>/s7b/pipe.py` (R8 board ->
  r9_pcb --place -> r9_rf -> r9_pyro -> r9_power -> rf_if, qspi_hse cached per place-table hash, then the families,
  DRC through the D-S6-14 shim, route_check r9); a cached base rebuilds byte-identical to the worktree board.
- FAMILIES reordered: rf_if, qspi_hse, pyro, servo, imu_baro, usb_swd, ... (imu_baro before usb_swd so that this
  session's three families gate without a usb_swd module; pyro / servo keep their KIID seeds).
- Plans (details in the decisions): pyro = the RAW_ACT_SENSE divider re-placed as one B.Cu column at x 29.65 east of the
  ARM lane, RAW_ACT tapped from In2 by one via at its forward end (the battery-live copper 0.7 mm long instead of the
  9 mm R177 lane step 5 sketched), the SENSE node the long run (west on y 52.2, down x 26.0 under U1's east pad ends
  to R172 at U1.34; P-8 MCU side 2.2 mm); servo = F.Cu fan into R150-R153, one via per lane in the 1k columns' gaps
  (G1 18.05, G12 20.46, G34 25.54, G4 27.95), D121 turned 90 deg between the inner vias so the B.Cu links are planar
  (pins ccw S1 NW, S2 SW, S3 SE, S4 NE), pull-downs beside the vias; C21 / C22 off the forward face.
- pyro built and gated in scratch (D-S7-08): RAW_ACT tap via (27.45, 57.95) west of the ARM lane (east of it the tie
  hole's 0.5 mm Edge.Cuts clearance leaves no spot inside In2's RAW_ACT region y >= 57.0); R177 / R124 in a row on y
  56.6 (MID under the ARM lane on B.Cu), SENSE column x 30.07, run west on y 52.45 and down x 25.42 to R172 (rot 0,
  under U1's east pad ends, >= 1.0 mm from the R89 / R91 3V3 pads: P-5). Gate OK: 17.6 mm, 1 signal via.
- servo built and gated in scratch (D-S7-09): 48.5 mm, 4 signal vias, worst ratio 1.298, board signal vias 20.
- imu_baro plan (west knot; worked out by hand with the s7 router, `<scratch>/s7b/aid/knot.py`, and a via-spot map
  `spots.py`): SPI inward vias SCK (11.7, 44.6), MISO (12.5, 44.95), MOSI (12.5, 45.7) into U4's south row / pad 1
  from below; CS and BOOT0 west vias (9.05, 46.45) / (8.8, 47.18) by 45-degree stubs (the 0.5 mm pin pitch leaves a
  straight-stub via exactly 0.15 mm from the next pin's lane); NCS inward to (14.57, 45.4), straight B.Cu line U3.1 -
  via - R10.1 with R10 re-placed (rot 0, 15.0, 46.19; its old spot is where SCK / MISO need their vias: step-6 table
  edit); INT1 inward to (13.21, 49.15), into pad 4 from the north; QSPI_IO2 F.Cu from inside U1.1's pad east on y 50.9,
  down x 13.9 between INT1's via and pin 6's 3V3 via / C25.2's GND via, round NCS's via (x 15.1) and one 45-degree run
  to (12.5, 42.07) beside U3.3 (the only F.Cu corridor: pin 6's inward 3V3 stub bars any path east of x 14.4);
  3V3A: one B.Cu trunk R164.2 (R164 turned 180) - C10.1 - C11.1 - x 11.5 down to a "U" over U4's GND pads 6 / 7
  (pad 8 up x 10.79, crossbar y 49.95, pad 5 up x 12.5) with their GND via inside; C31 / C30 on the U; east along y
  51.7 under U1's forward pads to an inward via (22.0, 50.85) for U1.20 / 21 with C21 / C22 beside it; west from pad 8
  along y 48.15 to U5's 3V3A pads and C32. C18's GND via moves from (12.88, 49.85) to (13.1, 49.95) (step-6 table edit).
  I2C on F.Cu over LS120's interior (the router's only order-preserving path) to vias (2.75, 51.3) / (4.97, 53.0).
  Neighbour escapes kept open: LED_RED / LED_YEL west on F.Cu, USB_FAULT_N west via (about (9.25, 44.0)) and B.Cu south.
- imu_baro built in scratch; fixes on the way (each a table / placement change, recorded in D-S7-10): R164's 3V3 via off
  PYRO1_CONT_MCU's F.Cu run; INT1 rises to y 49.86 past the north-row GND via (11.75, 49.1); pin 20's stub enters the
  3V3A via from the bar's end (acute angle at the via); SCK's B.Cu jog removed by moving the MISO / MOSI vias to x 12.55;
  BOOT0 via (8.8, 47.1) with R5 at (8.0, 46.67); C31 onto the y 48.15 line (staircase through its T); C18.2's GND via to
  (13.2, 50.05) for INT1's diagonal; K-copper (via ring on paste) moved R11 and G_CS.
- The last failure was the detour test on IMU_CS (R11 under pins 90 / 91 on the run's T: 5.32 mm against MST 2.63,
  excess 2.69 > 2.0, budget ratio 2.02). Fixed by R11 at (9.2, 45.25) rot 90 on a branch south off the west step's corner
  (CS via (9.0, 46.4), B.Cu along y 46.2, one 45-degree run into pad 12): 4.90 mm against MST 3.12. R11's 3V3 via
  (8.45, 44.82); clearances to USB_FAULT_N's future west via and the LED_YEL lane worked out (D-S7-10).
- Scratch gates on the three-family board: imu_baro **OK** (64.0 mm, 10 signal vias, 6 critical layer changes, worst
  ratio 1.34; board signal vias 30). pyro / servo / rf_if / qspi_hse gates on that same board fail only on the later
  families' pending GND vias, as designed (each family's gate runs at its own stage in r9_build.sh).
- r9_build.sh: stage pairs for pyro, servo, imu_baro appended (stages 18-23 of the scratch runner).
- r9_build.sh replayed in full (stages 0-23) three times: every stage rc 0, every gate OK (place, rf, pyro, power and
  the five family gates), byte-identical outputs, board SHA-256 `efdb2518…4537d8d`.
- test_r9_power's built-board template test failed once on the final board: pyro's RAW_ACT tap (a PARTIAL net step 6
  owns) read as "extra". r9_power_check stays a step-6 gate (step-6 handoff section 4), so the test now expects exactly
  the copper a drawn family's table adds to a PARTIAL net it CONTINUES, and a new seeded test shows any other RAW_ACT
  copper still named extra (D-S7-08). Suites: route 19, rf 16, place 18, pyro 19, power 20, sch 21, check 52: 165 OK.
- route_check on the final board: only the 26 pending GND vias fail (72 instances); INFO on this session's nets:
  QSPI_IO2 pad_end_offcentre at U1.1 (deliberate), 3V3A power_via_no_gnd (22.0, 50.75) 2.62 mm (step 8).
- Docs: D-S7-07 ... D-S7-10, qspi_hse docstring (R10), handoff rewritten. Scratch caches removed. Nothing committed.

## Session 4 (usb_swd, camera, status): topology study

- Read the session 1-3 log, the handoff, D-S7-01 ... 10, the step-6 handoff. Scratch (`s6` shim and runner, `s7`/`s7b`
  aids) survived the reboot; the worktree board = `efdb2518...` (the imu_baro board, checked). New scratch work in
  `<scratch>/s7c/`: `chk.py` (edge-to-edge clearance of a family module's tables against an exported board, with the
  TP 1.0 / J2 0.508 / hole 0.25 / X2 3.0 / GATE 1.5 rules), `solo2.py` (one net, two points, the s7 A* aid), `neg.py`
  (negotiated routing of a net set on a modified geometry: moved / removed parts, dropped pads, fake terminals).
- Families' nets (decided): usb_swd = USB_DP, USB_DM, CC1, CC2, VBUS, VBUS_SENSE, USB_FAULT_N, USB_ILIM, SWDIO, SWCLK,
  NRST; camera = CAM_MCU_RX/TX, CAM_RX/TX_BUFFER, CAM_RX/TX_WIRE, CAM_UART_OE, CAM_IO_3V3, CAM_5V_SENSE, CAM_FAULT_N,
  CAM_PWR_EN and U7's network (CAM_EN, CAM_DVDT, CAM_FLT_RAW, CAM_ILIM: they hang on camera's R74 / R77 and lie in the
  camera block; the step-6 handoff had listed them under power_ctl), CONTINUES CAM_5V; status = LED_RED(_A),
  LED_YEL(_A), BUZZ_DRV, BUZZ_G, BUZZ_OUT, PULLPIN, PULLPIN_EXT, VLOGIC_SENSE, V3V3_SENSE, CONTINUES VLOGIC.
  power_ctl keeps BAT_*, LOGIC_*, USB_LIMITED, USB_OVLO, BAT_ENABLE.
- Findings on the placed board (router probes, 0.2 mm clearance + the pyro extras):
  - VLOGIC cannot reach R60.1: the sense box (R60-R63, C60 at x 15-16.5, y 54-59, bottom) is walled by 3V3A (west /
    south), the servo clamp lanes (east) and J122 / the pyro block (north). The VLOGIC divider must move east of U1.
  - Pins 7 / 8 (BUZZ_DRV, PULLPIN) can only leave inward between pin 6's 3V3 via (14.5, 50.65) and the GND via
    (16.0, 50.6) (0.15 mm each on the pin lines; 0.2 mm with the lanes 0.05 mm inward of the pad centres), then not
    south-west (QSPI_IO2's wall x 13.9-15.1 and R10's via (15.75, 45.3)): pin 7 goes east of R10's via, down x 16.4,
    to a via in U3's body region and one B.Cu lane west between U3's west pads (y 41.44: the only interior-to-west
    B.Cu lane while C23 stays).
  - NRST (pin 14, forward face) to J2 on the west edge must cross PULLPIN (pin 8 -> east) inside U1, and the only B.Cu
    under the crossing is Y1's: J2 west is not routable without moving imu_baro / qspi_hse copper. J2 moves east.
  - USB_FAULT_N (pin 87, between the LED pins) must cross BUZZ_DRV's west lane: it goes inward through the IMU pocket
    (C23's 3V3 via (11.7, 42.75) moves west) and down x 11.5 to a via at the south-west interior corner (11.5, 38.0)
    (pin 75's 3V3 via (12.0, 38.25) moves to (12.45, 38.15) on a 45-degree stub), then B.Cu south.

## Session 5 (usb_swd, camera, status): design

- Resumed from session 4's topology study. Scratch survived (shim `<scratch>/s6/inj/nomouse.dylib`, runner
  `<scratch>/s6/tools/build.py`, aids `s7/aid`, `s7b`, `s7c`); worktree board = `r9/base` = `efdb2518…` (checked).
  New scratch folder `<scratch>/s7d/` (win.py: copper in a window; vmap.py: via-feasibility map).
- Findings (measured on the imu_baro board):
  - LS120.2 (BUZZ_OUT) is unreachable where step 3 put the buzzer: imu_baro's I2C lanes cross LS120's footprint
    from its pad-free south-east corner to vias west / north of U5, so all three LS120 pads lie north of the I2C
    curve, inside a pocket closed by U1's west pins 97-100 and the PYRO_BLOCK edge (y 54.2). Any I2C route to U5's
    north row (SDA is an inner pad, reachable only from the north on B) crosses the buzzer's footprint, so the buzzer
    must move (or U5 / I2C be redone).
  - The U1 interior (F.Cu inside the pad ring) has B.Cu exits only between U3's pads: west at y 41.44 (U3.4 / U3.3),
    east at y 41.44 (U3.5 / U3.6, past C19.2 and the (24.25, 40.9) GND via) and y 43.97 (U3.7 / U3.8); no north or
    south exit (3V3A line y 51.7, Y1, the R9 / R110 divider). Pins 7 / 8 leave inward only through the 1.0 mm gap
    between pin 6's 3V3 via (14.5, 50.65) and the GND via (16.0, 50.6); NRST (pin 14) east of HSE_OUT.
  - Planarity: going south then west from the forward face, pin 7 / 8 lanes end north of NRST's, so a pin 7 / 8 net
    leaving west must have its target north of J2.3; USB_FAULT_N (pin 87 between the LED pins) must cross one LED lane
    and NRST's west lane.
  - R-10 / F10: USB_D[PM], SWDIO, SWCLK copper >= 5.0 mm (plan view) from RF parts (R306 courtyard at y <= ~29.7).
- More findings: VLOGIC_SENSE (U1.17) is sealed in the pocket north of the forward face (servo fan F, servo pull-downs
  / D121, the RAW_ACT_SENSE L-lane x 25.42 / y 52.45 and C122 on B, imu_baro's 3V3A rail, J122 and the RAW_ACT tap
  via): VLOGIC cannot reach a divider there and VLOGIC_SENSE cannot leave it, so U1.17 goes inward and leaves the
  interior by a fourth exit "E46.4" (a via at (21.0, 45.6), B.Cu y 46.375 between the GND via (19.69, 45.75) / C26 /
  (21.95, 47.0), down x 24.8 west of R172, y 45.4 under R172 and between R91 / R89 on y 45.95 to x 30.5).
  F order from the forward face (pins 7, 8, 14, 17 west to east) and the exits fix the interior plan: pins 7 / 8 dive to
  B.Cu under U3's north-east half (vias (17.3, 43.0) / (16.8, 44.6)) and leave east (E41.44 / E43.97) under NRST's F.Cu
  lane, NRST dives under U3's south-west half (via (17.5, 40.0)) and leaves west (W41.44) to J2; USB_FAULT_N goes inward
  on F.Cu (x 11.75) to a via at the interior's south-west corner (11.75, 40.55) and B.Cu south to TP86 / U10.4.
- Plan (topology, scratch `<scratch>/s7d/plans/`): buzzer LS120 + driver to the south-centre (LS120 top (29.0, 25.5),
  driver bottom), BUZZ_DRV by E41.44 and B.Cu x 25.0; PULLPIN by E43.97 to D122.3; C19 shifted 0.25 mm aft (E41.44),
  C23 off the west face (its via is in FAULT's lane); R9 (VBUS_SENSE top) to the VBUS side (9.95, 32.4), R7 (9.0, 32.4);
  VBUS tree without a loop; LEDs re-placed west of U1 (F.Cu) clear of the SWD lanes (SWDIO hooks round U1's corner,
  north on x 4.0, SWCLK north on x 4.5); V3V3 divider stays in the pocket; VLOGIC divider east of U1 near E46.4's end.
- Tools: `s7d/plan.py` (apply a plan module to the base board: moves, dropped copper, draft copper; export geometry),
  `s7d/chk2.py` (clearance of a plan's copper), `s7d/legal.sh` (the R9 legaliser on a scratch placement table).

## Session 6 (usb_swd, camera, status): a clean scratch plan of all three

- Scratch plan `<scratch>/s7d/p/{usb,st,cam}.py` (merged by `full.py`; `s7d/plan.py --save` builds a filled scratch board
  in `r9/t1`, DRC with `s6/tools/drc.sh`, route_check profile r9). State at this note: DRC clean on every net of the three
  families (no clearance / courtyard / short / mask / keepout item; only the pending GND vias dangle), none of their
  nets unconnected, route_check r9 clean apart from the pending GND vias (step 8).
- Topology decisions (to record as D-S7-11 ...):
  - usb_swd: D4 0.05 mm aft so its DP pins line up with J3's DP lane (DM jogs 0.4 mm on a 0.57 mm diagonal); D4's
    pin pairs bridged under the body (R8's way), D4.2's GND via under the body, VBUS by a via east of D4 (11.95, 34.1)
    to the B.Cu tree (no loop); R9 / R7 beside the VBUS side, R90 east of TP86's old spot, TP86 to (13.6, 25.9) south of
    U10 (its 1 mm keep-off clear of the VBUS copper); SWD lanes west on F.Cu at x 4.0 / 4.5 to J2 (track ends kept
    outside J2's keep-out rectangle), NRST by W41.44 (B.Cu) to J2.3 and C24; USB_FAULT_N inward to (11.75, 40.55).
  - status: LEDs re-placed west of U1 (R32 / R33 rot 180, LED1 / LED2 rot 0) clear of the SWD lanes; buzzer LS120 to the
    south-centre (29.0, 25.5) with its driver on B.Cu under it (the old spot is crossed by imu_baro's I2C); BUZZ_DRV by
    E41.44 and B.Cu x 25.1; PULLPIN by E43.97 to the R8-style clamp column x 27.0 and PULLPIN_EXT to J123 (y 29.1 / 27.0,
    1.05 mm from TP70); VLOGIC divider (R60 / R61 / C60) next to E46.4's exit on B.Cu (C60 at the ADC end) with VLOGIC
    brought down F.Cu x 30.4 from the hold-up via (38.2, 69.6) (VLOGIC stays 2.1 mm from ARM1_SENSE_MCU); V3V3 divider
    stays in the pocket (R62 rot 180), its lane by the pin-18 via (20.5, 53.3) and B.Cu y 52.75 / x 14.6.
  - camera: RX hops (the RX / TX crossing is inherent to the pinouts) under TX by B.Cu y 44.5 from a via beside U1.37;
    TX on F.Cu x 31.8; OE by a via in the pin-28..31 box and B.Cu y 48.4 to x 33.9 then up to R102 / U12.6 (TP91 on F.Cu
    beside it); CAM_5V_SENSE on F.Cu y 46.0 to a via (31.2, 46.0) and the divider R104 / R105 / C94 beside C76.1 (B.Cu);
    the LDO cluster U13 / C91 / C92 / C93 / R103 / TP90 on B.Cu under U12's north (U13 and C92 to the bottom);
    U12.3 / C100 3V3 by F.Cu x 35.0 to R76.1 and one In2 via (33.1, 42.65) (In2 3V3 ends at x ~33.4 here);
    eFuse controls R70 / TP73 re-placed; R89 / R91 (power_ctl's pull-ups) moved north into the box-exit band.
  - Table edits outside the three modules: r9_power C23 (to (22.8, 36.8), strap to C16.1), C19 0.25 mm aft (its GND via
    (24.25, 40.65)), R78's GND via (33.9, 49.2) -> (34.675, 50.15); r9_route_pyro V_MCU (26.95, 46.1) -> (26.95, 46.5)
    (F.Cu straight from U1.34; CAM_5V_SENSE passes under it at 0.15 mm).
- Next: write r9_route_{usb_swd,camera,status}.py from the plan, the placement / step-6 / pyro table edits, the build
  stages, then the real gates.
- Built (modules `r9_route_usb_swd.py`, `r9_route_camera.py`, `r9_route_status.py`; r9_place.tsv rows; r9_power C23 /
  C19 / R78-via edits; r9_route_pyro V_MCU; r9_build.sh stages 24-29). Iterations on the real gates, on a scratch copy of
  the stage-23 board (`s7d/fam.sh`):
  - r9_pcb's legaliser: the support (42, 59.5)'s M-5 disk (4.452 mm) refused C91 / C92 / TP90 east of U12's north, and
    touching courtyards (U13 / C91 / C92) count as overlaps: C91 to (42.15, 53.3), C92 bottom at (35.45, 57.72, 270),
    TP90 / R103 to F.Cu off one CAM_IO_3V3 via under C92's body.
  - usb_swd budget: NRST's ratio 1.495 is its inward route (a via at (18.2, 41.0) crossed QSPI_IO1's B.Cu diagonal and
    only reached 1.451), so the family's ratio budget is 1.50 (D-S7-11).
  - camera DRC: R76.1's 3V3 via moved between R76 and C74 (35.225, 40.83) (C74.1 clearance).
  - status budget: V3V3_SENSE measured 1.522 with the divider at R62 / R63's far spots; R62 / R63 to R60 / R61's old
    spots (15.85, 54.5 / 55.38) gives 1.494 (budget 1.50, D-S7-14).
  - K-copper (via rings off paste apertures): CAM_5V_SENSE's via (31.2, 46.25), R76's (35.225, 40.83), the VLOGIC
    divider's GND via (29.2, 47.75).
  - The buzzer driver's GND strap moved to y 23.9 so that B.Cu below y ~23.5 stays free (USB_LIMITED, D-S7-15).
- Result: usb_swd **OK** (11 nets, 135.5 mm, 8 signal vias, ratio 1.495, board 38), camera **OK** (15 nets + CAM_5V,
  107.1 mm, 7, 1.332, board 45), status **OK** (11 nets + VLOGIC, 129.8 mm, 5, 1.494, board 50; S4 stretch <= 55 met).
  `r9_build.sh` replayed twice in full (stages 0-29): every gate OK, byte-identical, board `5bcee3339ac5f2d2…`.
  route_check r9 on the three families' nets: no failing instance; INFO only (pad_end_offcentre at TP / pad entries,
  extra_bends on the long inward lanes, u_turns of J3's DM pair join, SWDIO, V3V3_SENSE and PULLPIN_EXT, the VBUS /
  CAM_IO_3V3 / VLOGIC / CAM_5V vias' power_via_no_gnd until step 8, width changes at step 6's VLOGIC / CAM_5V vias).

## Session 7 (power_ctl, links, the step-7 gate)

- Read the session 1-6 log, the handoff, D-S6-*, D-S7-01 ... 15. Scratch (`s6` shim and runner, `s7*` aids) is present;
  worktree board = `5bcee333…` (the status board, checked). New scratch `<scratch>/s7e/`: `build2.py` (the runner with
  `--only`), `draw.sh` (draw-only replay of stages 5-28 without the gates: 5 s, byte-identical to the full build),
  `solo3.py` (one-net A* with width / via cost), `pc/plan2.py` (s7d's plan applier exporting the board's live zones).
- Open after status (DRC): 3V3 (C90.1, R89.1, R91.1), BAT_DVDT, BAT_ENABLE, BAT_FAULT_N, BAT_ILIM, BAT_OVLO,
  LOGIC_ILIM, LOGIC_SOURCE_ST, LOGIC_SS, USB_LIMITED, USB_OVLO; GND (step 8).
- USB_LIMITED corridor (the open problem): measured on the status board,
  - the east perimeter (south band y 23.3 on B, up the east edge x 45.1) is the only all-B route, but its copper is
    89-96 mm against an octilinear MST of 51.5 mm: route_check's detour test (> 1.6 x MST) fails it on a power net;
  - the A* aid with a 50-mm via cost finds one two-via route of 48.8 mm (TP82 to C98.1): B under U1's aft row, F.Cu
    through U1's interior (NE diagonal clear of NRST / QSPI_IO3, north on x 23.1 between the interior vias, out at the
    NE corner gap between U1.25 and U1.26), a via in the pin-28..31 box, B.Cu east through the box's exit band and north
    up the x 32.6-34.2 corridor, east under the RAW_ACT pour to C98.1. Its B start needs 0.6 mm between R90.1 and the
    VBUS_SENSE via (0.525 now), and the corridor's top slot between C92.2 and the RAW_ACT B pour (0.93 mm) holds two
    of the three lanes (USB_LIMITED, LOGIC_SOURCE_ST, BAT_FAULT_N) that must pass it.
- Design (D-S7-16 / 17; the A* aid's interior route made concrete by hand, every table checked by DRC + route_check r9 on
  a draw-only replay, `s7e/it.sh` / `rc.sh`):
  - USB_LIMITED: B.Cu U10.6 -> C86.1 -> north between R90 (0.3 mm west) and VBUS_SENSE's via -> TP82 (re-placed under
    U1's aft row) -> via (18.25, 39.75); F.Cu through U1's interior -> via (26.05, 51.15) in the box; B.Cu band north
    lane, corridor west lane (jog past OE's via), slot under the RAW_ACT pour (its step raised 0.35 mm, step-6 table),
    C98.1 -> R87.1 -> U11.7. 0.3 mm, 51.9 mm, ratio 1.13; dc_solve 82.9 mOhm, 37 mV at 0.45 A.
  - LOGIC_SOURCE_ST / BAT_FAULT_N: box vias (crossing on F.Cu), band with R91 / R89 hanging off their lanes, corridor,
    round the mid support's north-west; LOGIC_SOURCE_ST into U11.9 and TP87 (column's south slot), BAT_FAULT_N up the
    east edge (x 45.25), T to TP85, round U9's north into U9.4.
  - BAT_ENABLE: F.Cu along the forward edge north of the BAT_IN pours through TP84 (re-placed on the lane), C87.1, a via
    inside BAT_FAULT_N's loop, B.Cu to U9.1 / R81.1. BAT_ILIM: U9.9 -> R84.1 -> TP89. U9.8 / U11.3/4/6 GND straps.
  - Fixes on the way: R89's 3V3 via off ARM1_SENSE's F.Cu lane (a short), hole clearance is Edge.Cuts' 0.5 mm (lanes
    shifted east past (30.8, 59), BAT_ENABLE's diagonal off (42, 98)), staggered corridor jogs (parallel 45-degree runs
    0.03 mm apart), a staircase (BAT_FAULT_N's short chamfers) and a tiny jog (its F.Cu via stub), BAT_OVLO's R82 -> R83
    link crossing BAT_ENABLE (EN fed from the east), T-1 (C87 moved within 5 mm of the east edge: kept at its spot),
    U11.6's GND via in C97.2's pad (C97 0.7 mm east, step-6 table).
- Draw-only replay + both families: DRC only the 32 pending GND vias' via_dangling (+ silk), unconnected only GND (112),
  route_check r9: only pending GND (dead_copper / dangling_via). Gates at their stages: links OK; power_ctl OK but its
  first length budget guess (170) -> 175.
- r9_build.sh: stages 30-33 (power_ctl, links and their gates). tools/test_r9_route.py: LinksStage (2 tests).
- Full replay (stages 0-33) #1: every gate OK (placement, RF, pyro, power with this session's step-6 table edits: DC
  unchanged; all ten family gates); board `96cf2736…`; 167 tests OK. check_r9 in full showed R89's 3V3 via ring touching
  R89.1's paste (0.0 mm, K-copper passes at 0 but no margin): via 0.05 mm west (29.05, 49.125); K-copper's nearest ring is
  now step 6's (42.0, 81.26) at 0.005 mm. Board `8504c2c6…` (draw-only replay + DRC + route_check clean as before).
- check_r9 in full on `8504c2c6…` (fit, plate, seeded rule-H): 39 rules OK, K-legends FAIL (step 8 silkscreen); M-2 f1
  256.6 Hz; T-1 east forward window 92.75-101.5. USB_LIMITED dc_solve 82.9 mOhm. Evidence copied (paths sanitised) to
  `step7_evidence/`. Decisions D-S7-16 … 19 written; handoff rewritten (complete).
- Full replays #1 and #2 (stages 0-33) on the final scripts: every gate OK in both; all 20 built files identical
  (`step7_evidence/build_sha256.txt`; board `8504c2c6c74b601b009f22d0f1dd41aa27e7035b44614282b9560a70cb0a0230`). The seven
  R9 suites on that board: 167 OK (`step7_evidence/tests.txt`). Step 7 complete; step 8 (GND stitching) is next.
