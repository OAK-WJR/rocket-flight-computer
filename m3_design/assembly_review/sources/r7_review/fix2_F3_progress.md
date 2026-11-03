# F3 progress log (whole-board routing hygiene)

Running log so a successor can resume. Newest entries last.

- Start: board = F2's (SHA-256 0eceb770…8904), saved copy in scratchpad f3/f2_board.kicad_pcb.
  Previous F3 attempt left tools/route_check.py (gate scanner, 553 lines, empty ALLOWLIST) and
  m3_design/r7_hygiene.py (stages zero_length, dedupe, inside, trim_dangling, cover, merge, resolve_chains), both
  unreviewed; check.sh and r7_build.sh were NOT edited (no references). Copies of both partial files kept in
  scratchpad f3/.
- DC baseline on F2's board (tools/dc_solve.py, grid 0.1, 7.7 A; scratchpad f3/dc3.sh): RAW_ACT 3.96, BAT_IN 3.91,
  ACT_FET_S 1.36 mΩ (= R6, pass 2 and F1).
- tools/route_check.py rewritten on the partial one: added KiCad-anchor-rule connectivity graph (route_check.graph,
  pad_groups, dead, loops), categories dead_copper (stubs incl. closed micro-loops: PYRO1_COLD's 33 mm branch now
  found), track_loop (duplicate routes on nets without a pour), neck_down (width change at a plain node; T/via
  width changes are info `width_change_junction`). F2 board: 863 failing (before allowlist).
- m3_design/r7_hygiene.py rewritten: generic stages zero_length, dedupe, inside, near_dup (chain-level copies),
  dead (route_check.dead, strict joints; guarded by KiCad-rule pad groups), merge, chains, merge2, dead2.
  First trial (h2) 863 -> 238 failing; fixes since: via with only one pour counts as dead, strict joints, clean-end
  guard in near_dup, speed (one change per layer/net group per pass).
- Approach settled: HAND_PRE stages (explicit redraws of the messy R6 clusters, on F2's board: `replace()` deletes a
  counted set of tracks in a box and draws asserted 0/45/90 polylines checked by the Clearance model), then the
  generic stages, then (planned) HAND_POST for residue, gnd_vias, allowlist. Done so far: usb_limited, 3v3a,
  cam_io_3v3. route_check: pads whose copper overlaps are linked (U5's split pins); pour islands join pad groups
  (zoned groups also invariant); vias with one pour only are dead.
- HAND_PRE now: usb_limited, imu_cs (detour route removed: 2 RG-09 layer changes gone), 3v3a, cam_io_3v3,
  raw_protected (U11 feed 0.2 mm neck -> 0.5 mm), vlogic (C84->U2 0.2 mm neck -> 0.5 mm), vbus, 3v3 (incl. RG-10).
  route_check neck_down now exempts pad-entry necks (narrow side ends in a pad within 1 mm).
- HAND_PRE extended: camera_power, gnd, power_misc, pyro (RG-07 PYRO1_GATE v5 route; PYRO1_OUT trimmed inside Q124.5
  only), signals (slow nets' acute/fold/staircase). Group rule relaxed+documented: zoned pad groups identical; track-only
  groups may merge (TP80/BAT_IN), never split. Clearance model: Pyro G only inside PYRO_BLOCK (as the DRU).
- IMPORTANT for scratch runs: a board copy must have its .kicad_pro/.kicad_dru beside it (same basename) or pcbnew's
  zone fill ignores the project rules (GND F.Cu 48 islands instead of 39). r7_hygiene now refuses to run without the
  .kicad_dru and refills after every stage (pad-group check per stage).
- h11 (scratch f3/h11.kicad_pcb, full HAND_PRE+generic+gnd_vias): kicad-cli DRC 0 / unconnected 0 / parity 0;
  route_check 18 failing = 5 band/pyro staircases + QSPI_CLK jog (to allowlist, forced) + 12 critical vias with no
  legal GND spot (20 GND vias placed, 0.5 mm fallback). Next: DC solve, critical_reference, allowlist, tests,
  check.sh + r7_build.sh integration, real build.
- Build 1 (m3_design/r7_build.sh with r7_hygiene.py between r7_rework.py and r7_post.py): tools/check.sh exit 0
  (DRC 0 / unconnected 0 / parity 0 / ERC 0, audit, silk, R7 contract, routing hygiene 0 failing / 18 allowlisted,
  actuator contract, fit). Board SHA-256 68161fe803c2…94d8. Hidden designators 89 (F2 88). Next: second build for
  reproducibility, DC solve, critical_reference, reviewer scan, tests, fab regeneration, handoff.
- Build 1/2 were byte-identical (68161fe8…). Then: DC showed BAT_IN 3.91 -> 3.95 mOhm (two GND vias at (13.8, 93.95)
  / (13.8, 97.35) in the J1->Q120 BAT_IN In2 corridor) and ACT_FET_S 1.36 -> 1.37 (an R6 stub I deleted); fixed:
  gnd_vias keeps out of each heavy net's DC-terminal corridor, the ACT_FET_S stub stays (route_check's overlap-only
  test no longer counts a stub's own neighbour). Build 4: gate exit 0, routing hygiene 0 failing / 20 allowlisted,
  SHA a0c4b8ae…4ffd (scratch copy f3/final.kicad_pcb).
- Builds 5/6: build 5 = build 4 byte-identical; build 6 (critical-reference repairs: NRST In2 freed of the 3V3A diagonal,
  SWCLK In1 moved off U1.89's SPI1_SCK) gate exit 0, SHA f00ef157…7dd8. 4-decimal DC on build 6: RAW_ACT 3.9570 vs F2
  3.9567 mOhm (BAT_IN 3.9070 and ACT_FET_S 1.3619 equal F2). Copper diff: the VBUS F.Cu link I had widened to 0.4 mm
  pushed the RAW_ACT F.Cu pour back 0.09 mm²; narrowing it to R6's 0.2 mm on build 6 restores 3.9567 (scratch b6v).
  BAT_IN C80 link redrawn (build 7, stopped); vbus() link back to 0.2 mm; build 8 running.
- (attempt 3, 2026-10-17) Resumed. Found build 8 complete (scratch f3/build9.log; board SHA 51b749d6…f8ff = f3/b8rf):
  gate exit 0 (f3/gate_final.txt), routing hygiene 0 failing / 20 allowlisted, 4-decimal DC = F2 exactly (RAW_ACT 3.9567,
  BAT_IN 3.9070, ACT_FET_S 1.3619 mOhm; f3/dc4_b8.txt), critical reference vs R6: lost 603 (F2 524; +79 SPI1_MOSI F.Cu at
  its via, moved 0.26 mm up its own run: the track's antipad stretch moved with it). Attempt 2 was investigating a 3V3
  rise (L1.2 -> U1.75 13.99 -> 15.17 mOhm at 0.1 A): bisected to the 3v3 stage (via (24.9, 35.0) removed: one of three
  L1 -> In2 3V3 plane vias; +0.98) and the GND vias in the In2 3V3 pour (+0.21). Plan: put a via back on L1's diagonal
  at (24.9, 34.2); hand-fix the 22 non-critical hygiene residues (2 crossings, 2 micro segments, 4 necks, 14 jogs) in a
  new HAND_POST stage after gnd_vias; then builds, gate, DC, cref, scans, tests, handoff. Work dir scratch f4/.
- (attempt 3) r7_hygiene.py changes, tested on scratch f4/t2 (pre-hygiene board f3/pre + full hygiene) and f4/t1 (b8 +
  hand_post): 3v3 stage puts a via back on L1's diagonal at (24.8, 34.3) (ViaCheck refuses (24.9, 34.2): 0.1 mm from
  L1.2's pad); near_dup only on layers where the net has a pour (it removed the new L1.2 -> via link as a "copy": a short
  link between two wide features passes its test; in build 8 its only non-poured removals were debris that chains /
  the stricter joint rule now handle); clean_without needs pad joints >= 2 um inside the pad (build 8 left VLOGIC's
  U2.2 diagonal ending exactly on the pad outline); new stage inside2 after dead2 (chains left a SERVO4_MCU piece in
  D121.6); PYRO1_OUT branch now ends at (28.85, 91.73), wholly inside Q124.5's finger (it stopped 5 um inside the
  edge); PULLPIN one run at x 32.7; new stage hand_post (after gnd_vias): 2 crossings, LOGIC_SOURCE_ST hook, 4 necks,
  8 jogs (SWCLK, CAM_UART_OE, IMU_INT1 -2 vias, SERVO4_MCU, CAM_FAULT_N, CAM_TX_WIRE, USB_ILIM, ACT_EN), ACT_FET_S
  pour-only L joined R120.1 -> Q120.1. ACT_EN via move was reverted (it pinched BAT_IN's In2 neck: 3.9070 -> 3.9159).
  t2: DRC 0/0, route_check 0 failing / 20 allowlisted, tiny_jog 5 (4 forced, non-critical + QSPI_CLK allowlisted),
  DC RAW_ACT 3.9567, BAT_IN 3.9070, ACT_FET_S 1.3561 mOhm; 3V3 L1.2 -> U1.75 14.2549 (F2 13.9879, build 8 15.1736),
  -> FB31.1 13.6137 (F2 13.5963). Next: real build x2, gate, tests, DC/cref/scan on the final board, handoff.
- (attempt 3) Builds A and B (m3_design/r7_build.sh) byte-identical: board SHA-256 4ade560e5de05fb83000afde2fda43c65f7ae7347c5d7219bc766d273506e84b;
  both gates exit 0 (routing hygiene 0 failing / 20 allowlisted). Hidden designators 88 (F2 88). Scratch copy f4/A.kicad_pcb;
  analyses (f4/an.sh -> f4/an/A_*) running; next: export_fab.py, tests, handoff.
- (attempt 3) Build A's pour check (f4/fillxor.py, F2 -> A) found two GND losses on B.Cu: a 16 mm² finger beside J122's
  RAW_ACT pins (build 8 already: stage chains moved SERVO2_MCU's 12 mm run 0.1 mm west to drop a jog; the pour necked
  out) and a 4 mm² island west of the new IMU_INT1 run. hand_post now redraws SERVO2_MCU on R6's x 24.5 (0.1 mm step
  inside its via) and IMU_INT1 down x 26.3; both recovered (scratch f4/t4). Rebuilding (builds C, D).
- (attempt 3) DONE. Builds C, D and E (E after docstring-only edits) byte-identical: board SHA-256
  7660620cfa834e4d381d2a2638780e9a341341c9b93c6e6f526791204dc77c9c; gate exit 0 (routing hygiene 0 failing / 20
  allowlisted); tests OK (r5_repair known failure); DC 3.9567 / 3.9070 / 1.3561 mOhm; fab outputs and renders
  regenerated for this board. Record: fix2_F3_handoff.md.
