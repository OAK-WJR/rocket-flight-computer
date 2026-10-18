# R7 review pass 2: whole-board routing hygiene (F3 handoff)

Fix agent F3 (board, `m3_design` scripts, `tools`). Worktree branch `m3-assy-r7`, uncommitted, on R6 commit `3b215ba`,
on top of F2's state (`fix2_F2_handoff.md`). Nothing committed, pushed or opened as a PR. I did not edit `docs/*.md`,
`STATUS.md`, `AGENTS.md`, `m3.kicad_dru`, `check_actuators.py` or the schematic. Scope: RG-06…RG-10, RG-15 (and
Appendix A), RQ-07, RQ-08: clean routing on the whole board, inherited R6 copper included, held by a gate. Three
attempts (the first two were cut off by authentication errors; `fix2_F3_progress.md` is the running log).

**Final board SHA-256 `7660620cfa834e4d381d2a2638780e9a341341c9b93c6e6f526791204dc77c9c`** (F2:
`0eceb7702d08…8904`). Three consecutive `m3_design/r7_build.sh` runs from the SHA-checked R6 board (the last one after
the final edit, docstrings only) gave this same file, and the saved board is that file; each run's gate exited 0.
Schematic untouched.

## 1. How the board is built and gated now

`r7_build.sh`: `r7_pcb.py` → `r7_route.py` → `r7_rework.py` → **`r7_hygiene.py` (new)** → `r7_post.py` →
`tools/check.sh`. `tools/check.sh` now runs **`tools/route_check.py`** (new) after `check_r7.py`.

### 1.1 `tools/route_check.py` (the gate; productised from the reviewers' `scan.py`)

- Copper is grouped per (layer, net); track ends within 1 µm are a node. Connectivity follows KiCad's anchor rule
  (an anchor of one item — track end, via or pad centre — inside the other's copper on a shared layer); pour
  islands join their pads.
- **§3 rule categories, gated on every net:** `off_angle` (> 0.1° or > 2 µm lateral), `staircase`, `acute_angle`
  (at a pad/via only when the wedge opens outside its copper), `fold_back`, `dead_copper` (copper on no path between
  two terminals, which also catches the dead branch a closed micro-loop hides from KiCad's dangling check),
  `dangling_via`, `critical_via_no_gnd` (critical signal via with tracks on ≥ 2 layers and no GND via centre within
  1.5 mm).
- **Hygiene categories, gated on critical nets** (RF, pyro/arm, HSE, USB data, SPI/QSPI/IMU_CS/radio SPI, other
  RADIO_*/GNSS_*, and the power rails incl. GND): `micro_segment` (< 50 µm), `tiny_jog`, `collinear_unmerged`,
  `duplicate_segment`, `collinear_overlap`, `side_by_side_overlap` (overlap or same-net slit < 0.1 mm),
  `crossing_without_node`, `overlap_only_joint`, `via_offcentre_joint`, `neck_down` (width change at a plain node,
  pad-entry necks within 1 mm of the pad exempt), `track_loop` (two routes between the same points on a net without
  a pour). Counted on every net, reported per layer and net class.
- **Information only:** `width_change_junction`, `pad_end_offcentre`, `segment_inside_pad`, `passes_through_pad`,
  `extra_bends`, `u_turn`, `short_layer_hop`.
- **Allowlist:** an explicit list in the file, each entry (category, net, layer, x/y within 0.02 mm, reason). An entry
  that matches nothing fails the gate (stale exceptions are removed, not kept). 20 entries (§5).
- Exit 1 on any failing instance or stale entry; `--report` writes every instance as JSON.
- Tests: `tools/test_route_check.py`, 19 synthetic boards (every category, the clean route, the pad-wedge and
  pad-entry exemptions, rule-vs-hygiene gating, allowlist matching and stale entries, a reason on every entry).
  `tools/test_check_shell.py` now also proves a `route_check` failure stops the gate (exit propagated through
  the `grep` pipe under `pipefail`).

### 1.2 `m3_design/r7_hygiene.py` (the clean-up; its module and stage docstrings hold every reason)

Invariants, enforced in code: the board's `.kicad_pro`/`.kicad_dru` must sit beside it (it refuses to run otherwise;
without them pcbnew fills with the wrong rules); pours are refilled after every stage; after every stage each net's
pad groups with the pours joining must be identical, and by tracks alone may only merge, never split (the run stops
on the first stage that breaks this); hand redraws delete an asserted count of tracks in a box (a changed upstream
board stops the build), draw asserted 0/45/90° polylines, and check every new segment and via against every other
net's copper (`m3.kicad_dru` incl. the pyro rules, bare test pads 1.0 mm, Tag-Connect 0.508 mm; vias also
`r7_route.ViaCheck`). Deterministic (KIID seed 7501).

| Stage | Final-build result |
|---|---|
| HAND_PRE (14 hand stages: usb_limited, imu_cs, 3v3a, cam_io_3v3, raw_protected, vlogic, vbus, 3v3, camera_power, gnd, power_misc, pyro, signals, spi) | 577 tracks and 12 vias of the doubled / tangled conductors removed, 325 segments and 8 vias drawn; reasons per item in the docstrings |
| dedupe | 6 exact duplicates, 15 contained collinear segments, 3 partial overlaps of two widths cut back |
| inside / inside2 | 227 + 1 segments wholly inside their own pad (2 µm margin) |
| near_dup | 37 copied runs, all GND on F.Cu (17) / B.Cu (20), where the GND pour fills what they bridged |
| dead | 9 tracks + 3 vias: PYRO1_COLD's 33 mm dead branch (a closed micro-loop hid it from KiCad) |
| merge | 17 collinear joints |
| chains | 37 chains with micro segments / acute turns / tiny jogs re-solved on their headings |
| acute_t | 1 acute T squared |
| gnd_vias | 18 GND vias (0.6/0.3 mm, 0.5/0.3 mm where 0.6 does not fit) beside critical layer changes |
| hand_post (new in attempt 3) | 18 hand redraws (71 tracks and 3 vias removed, 46 segments and 1 via drawn) of the residue: 2 crossings without a node, a micro hook, 4 neck-downs, 8 tiny jogs, a pour-only stub, SERVO2_MCU restored (§2) |

## 2. Changes per finding

| Finding | Fixed? | Final board |
|---|---|---|
| RG-06 / RQ-08 duplicated and overlapping copper | Yes | Duplicates, collinear and side-by-side overlaps, overlap-only joints, crossings without a node, track loops: **0** (route_check and scan.py). USB_LIMITED (three copies) is one 0.4 mm trunk; 3V3A, CAM_IO_3V3, RAW_PROTECTED, VLOGIC, VBUS, 3V3, CAM_5V, GND, NRST, CAM_FB, VBUS_SENSE, BAT_IN residue redrawn (`HAND_PRE`). ACT_FET_S's pour-only L (RG-06's last overlap-only joint) now runs R120.1 → Q120.1 (copper only added) |
| RG-07 PYRO1_GATE drawn twice | Yes | One 0.2 mm route (the pass-2 skeptic's v5): R126.2 centre, one 45° step, straight at y 91.85 through C126.1, R128.1 and Q124.4 with a node in each pad. check_actuators OK; DRC (pyro rules) 0 |
| RG-08 acute angles, staircases, micro-segments | Yes, 5 staircases allowlisted | Acute 0, fold-back 0, micro-segments 0, off-angle 0. Staircases 20 → 5 (4 radio band fan-in lanes, PYRO1_CONT: geometry, §5). Tiny jogs 50 → 5 (QSPI_CLK allowlisted; 4 non-critical, §7) |
| RG-09 23 R6 critical layer changes without a GND via | 19 of 23 | 3 vias went with their copper (PYRO1_COLD ×2 dead, IMU_CS detour), 16 now have a GND via ≤ 1.5 mm (QSPI_IO1 at exactly 1.50), **4 allowlisted with reasons**: ARM1_SENSE (14.55, 94.15) / (14.55, 97.55) (only legal spots cut BAT_IN's J1→Q120 pour: measured 3.91 → 3.95 mΩ), PYRO1_GATE_N (23.0, 88.33), PYRO1_CONT (41.1, 78.80) (no DRC-legal spot under the pyro rules). R7's own (RG-05 residue): 10 radio/GNSS interface vias allowlisted, same search |
| RG-10 off-angle 3V3 segment | Yes | (40.25, 58.55) → (41.55, 58.55) → (42.95, 57.15): one straight and one 45° |
| RG-15 minor style debt | Mostly | scan.py: width changes at free nodes 58 → 18, at vias 15 → 13, unmerged collinear 22 → 3 (all width changes at pad entries), segments < 0.2 mm 409 → 44, segments inside pads 69 → 2, off-centre pad ends 586 → 209, pour-only ends 24 → 22, close via pairs 24 → 23; the large slow-net detours (SWCLK, SWDIO, CAM_PWR_EN) were not rerouted |
| RQ-07 / RQ-08 | Yes | as RG-06/RG-08 |

Attempt-3 changes on top of attempt 2's build 8 (all in `r7_hygiene.py`):

- **3V3 plane vias at L1:** the 3v3 stage had removed one of the three vias from the buck output L1.2 into the In2
  3V3 plane (it hung off a doubled diagonal): L1.2 → U1.75 rose 13.99 → 15.17 mΩ. The via is back on L1's diagonal
  at (24.8, 34.3) (ViaCheck refuses (24.9, 34.2): 0.1 mm from L1.2's pad).
- **near_dup** now runs only on layers where the net has a pour. Its test cannot tell a copy from a short link
  between two wide features (pad and via 1–2 mm apart): it removed the new L1.2 → via link and put the buck output
  through one via. Its non-poured removals in build 8 were debris that chains and the stricter joint rule now handle.
- **clean_without** (joints left after a removal) needs a track end ≥ 2 µm inside a pad: build 8 left VLOGIC's U2.2
  diagonal ending exactly on the pad outline.
- **inside2** after dead2: chains left a SERVO4_MCU piece wholly inside D121.6.
- **PYRO1_OUT** branch trimmed inside Q124.5 now ends at (28.85, 91.73), its whole width inside the pad finger (it
  stopped 5 µm inside the finger's edge). CH1 copper outside pads is unchanged (§4).
- **PULLPIN** D122.3 → R160.2 is one run at x 32.7 (the only line between VLOGIC and CAM_5V_SENSE's via).
- **hand_post:** CAM_5V_SENSE and ACT_GATE crossings (both inside a pad), LOGIC_SOURCE_ST's In2 hook inside its via,
  USB_OVLO / LOGIC_SS / LOGIC_ILIM one width each (0.2 mm), tiny jogs on SWCLK, CAM_UART_OE, IMU_INT1 (B → F → B
  hop through two vias 1.8 mm apart round R6's removed RADIO_M0_MCU vias: now B.Cu only, two vias fewer),
  SERVO4_MCU, CAM_FAULT_N (one run at x 37.8875, between R77.2's 0.15 mm and J121.2's 0.5 mm pyro rule; its via
  moves 9 µm along its In2 diagonal), CAM_TX_WIRE, USB_ILIM, ACT_EN; ACT_FET_S's L. Two redraws were revised after
  measurement: ACT_EN's via move pinched BAT_IN's In2 neck (3.9070 → 3.9159 mΩ, reverted: the run leaves Q122.1
  48 µm off centre instead), and an IMU_INT1 run at x 27.25 cut off a 4 mm² B.Cu GND island (now at x 26.3).
- **SERVO2_MCU** (found by the pour comparison, §4): build 8's chains stage had moved its 12 mm B.Cu run beside
  J122's RAW_ACT pins 0.1 mm west to drop a jog, which necked out a **16 mm² B.Cu GND finger**. hand_post puts the
  run back on R6's x 24.5 with the 0.1 mm step inside its via's copper; the finger is back.

## 3. Counts before / after

### 3.1 `tools/route_check.py` (F2 board = F3's start; final board)

| Category | Kind | F2: all (critical) / failing | Final: all (critical) / failing / allowlisted |
|---|---|---|---|
| off_angle | §3 rule | 1 (1) / 1 | 0 (0) / 0 / 0 |
| staircase | §3 rule | 20 (12) / 15 | 5 (5) / 0 / 5 |
| acute_angle | §3 rule | 30 (23) / 30 | 0 / 0 / 0 |
| fold_back | §3 rule | 58 (49) / 58 | 0 / 0 / 0 |
| dead_copper | §3 rule | 20 (18) / 20 | 0 / 0 / 0 |
| dangling_via | §3 rule | 0 / 0 | 0 / 0 / 0 |
| critical_via_no_gnd | §3 rule | 35 (35) / 21 | 14 (14) / 0 / 14 |
| micro_segment | hygiene | 270 (164) / 164 | 0 / 0 / 0 |
| tiny_jog | hygiene | 50 (22) / 21 | 5 (1) / 0 / 1 |
| collinear_unmerged | hygiene | 18 (9) / 9 | 0 / 0 / 0 |
| duplicate_segment | hygiene | 6 (0) / 0 | 0 / 0 / 0 |
| collinear_overlap | hygiene | 60 (51) / 51 | 0 / 0 / 0 |
| side_by_side_overlap | hygiene | 77 (66) / 66 | 0 / 0 / 0 |
| crossing_without_node | hygiene | 42 (35) / 35 | 0 / 0 / 0 |
| overlap_only_joint | hygiene | 3 (3) / 3 | 0 / 0 / 0 |
| via_offcentre_joint | hygiene | 0 / 0 | 0 / 0 / 0 |
| neck_down | hygiene | 20 (15) / 15 | 0 / 0 / 0 |
| track_loop | hygiene | 58 (50) / 50 | 0 / 0 / 0 |
| width_change_junction | info | 53 (51) | 31 (30) |
| pad_end_offcentre | info | 196 (146) | 90 (64) |
| segment_inside_pad | info | 69 (60) | 2 (2) |
| passes_through_pad | info | 20 (19) | 10 (10) |
| extra_bends | info | 30 (9) | 36 (10) |
| u_turn | info | 38 (28) | 25 (17) |
| short_layer_hop | info | 25 (7) | 26 (10) |
| **total** | | **1199 / 559 failing** | **244 / 0 failing / 20 allowlisted** |

Every hygiene category is now 0 on every net, critical or not, except the 5 tiny jogs (1 allowlisted, 4 non-critical, §7).

### 3.2 Reviewers' `scan.py` (scratchpad `rg/scan.py`, unchanged), all instances (critical nets)

| Category | Pass-2 board (report §3.1, A+B+C) | F2 board | **Final** |
|---|---|---|---|
| off_angle | 1 (1) | 1 (1) | **0** |
| staircase | 26 (12) | 20 (12) | **5 (5)** |
| tiny_jog | 55 (24) | 50 (22) | **5 (1)** |
| acute_angle (outside pads/vias) | 35 (22) + 59 fold-back | 74 (58) | **0** |
| acute_at_padvia | 138 (75) | 122 (72) | 12 (7) |
| collinear_overlap | 66 (49) | 60 (47) | **0** |
| side_by_side_overlap | 75 (56) | 70 (56) | **0** |
| duplicate_segment | 7 (0) | 6 (0) | **0** |
| crossing_without_node | 46 (35) | 42 (34) | **0** |
| overlap_only_joint | 5 (5) | 5 (5) | **0** |
| via_offcentre_joint | 12 (8) | 8 (7) | **0** |
| collinear_unmerged | 32 (20) | 22 (12) | 3 (3) |
| short_segment (< 0.2 mm) | 468 (255) | 409 (239) | 44 (26) |
| segment_inside_pad | 80 (65) | 69 (57) | 2 (2) |
| pad_end_offcentre | 235 (154) | 586 (354)* | 209 (131) |
| width_change_free / at via | 66 (55) / 16 (16) | 58 (51) / 15 (15) | 18 (17) / 13 (13) |
| end_in_zone_only | 32 (32) | 24 (24) | 22 (22) |
| critical_via_no_gnd | 52 (52) | 35 (35) | **14 (14)** |
| short_layer_hop | 31 (7) | 25 (7) | 26 (10) |
| u_turn | 47 (31) | 38 (28) | 25 (17) |
| off_angle_rounding (< 2 µm, nm rounding) | 55 (16) | 48 (16) | 30 (16) |
| **total** | – | **2683 (1698)** | **1034 (647)** |

\* the report's §3.1 counted small pads only; the F2 and final columns are the script's own totals.
Remaining scan.py notes: collinear_unmerged 3 = width changes at pad entries (BAT_IN / RAW_PROTECTED at U9,
CAM_INPUT_LIMITED 0.3 → 0.8 mm out of U7.5); acute_at_padvia 12 = two tracks meeting at 45° inside a pad or via
(not an acid trap; route_check's pad-wedge rule clears them); end_in_zone_only 22 = GND/3V3 tracks ending in their own
pour (RG-15 style debt).

## 4. Safety of the clean-up (final board)

- **Connectivity.** Pad groups per net with the pours joining: identical to F2 for all 191 nets. By tracks alone: no
  group split; two merges where a redraw joins pads a pour already joined (BAT_IN: TP80 onto R167's run; ACT_FET_S:
  R120.1 → Q120.1). KiCad: unconnected 0 on both boards. The same check runs inside `r7_hygiene.py` after every stage.
- **DRC / parity / ERC 0**, `check_r7` OK, **check_actuators OK**, fit OK (gate output §6).
- **CH1 pyro copper** (PYRO1_BUS / IGN / OUT), F2 → final, copper outside pads: **0.00000 mm² lost or gained on every
  layer**; all copper: F.Cu −0.353 mm², all inside Q124.5 (the trimmed drain branch). Pyro sentinel pins: untouched
  (no net), check_actuators OK.
- **DC copper solves** (`tools/dc_solve.py`, grid 0.1 mm, 7.7 A; 4 decimals from a copy that prints `.4f`):

| Path | R6 / R7 pass 2 | F2 (start) | **Final** |
|---|---|---|---|
| RAW_ACT Q121 → J122 | 3.96 mΩ | 3.9567 mΩ | **3.9567 mΩ** |
| BAT_IN J1 → Q120 | 3.91 mΩ | 3.9070 mΩ | **3.9070 mΩ** |
| ACT_FET_S Q120 → Q121 | 1.36 mΩ | 1.3619 mΩ | **1.3561 mΩ** (R120–Q120 L) |

  `tools/dc_solve.py` as shipped prints 3.96 / 3.91 / 1.36 mΩ (30.5 / 30.1 / 10.4 mV, 0.235 / 0.232 / 0.080 W).
  Guards that protect these paths: `gnd_vias` keeps out of each heavy net's pour inside its DC-terminal corridor
  (measured: two GND vias there raised BAT_IN to 3.95 mΩ); a widened VBUS link was set back to R6's 0.2 mm (it pushed
  the RAW_ACT pour back: 3.9567 → 3.9570); ACT_EN's via stays (it pinched BAT_IN: 3.9159).
- **3V3** (not required; checked because a via went in attempt 2), 0.1 A, from L1.2:

| L1.2 → | F2 | Build 8 (attempt 2) | **Final** |
|---|---|---|---|
| U1.75 | 13.9879 | 15.1736 | **14.2549** mΩ |
| FB31.1 (radio PA feed) | 13.5963 | 14.6834 | **13.6137** |
| FB30.1 | 5.0030 | 6.0669 | **5.0599** |
| U1.27 | 6.1994 | 6.9661 | **6.3262** |
| U3.8 (QSPI flash) | 6.3406 | 7.3996 | **6.4016** |

  Still +0.02 … +0.27 mΩ (≤ 1.9 %) over F2: ≤ 0.03 mV at 0.1 A. Attempt 2's bisection put ~0.21 mΩ of the U1.75 rise
  on the GND return vias that sit in the In2 3V3 plane (their antipads); the rest is not separated (inference). The
  narrowest 3V3 copper of each path is not narrower than F2's (redraws keep the path's narrowest width).
- **Track widths.** No conductor narrower than the narrowest width of the path it replaced; necks widened:
  RAW_PROTECTED U11 feed 0.2 → 0.5 mm, VLOGIC C84 → U2 0.2 → 0.5 mm, RAW_PROTECTED camera feed and TP70 0.2 → 0.4 mm,
  LOGIC_SS / LOGIC_ILIM / USB_OVLO 0.15 → 0.2 mm. Narrowed, with reason in the docstrings: VCAP2 0.3 → 0.25 mm on a
  stretch (core-regulator capacitor pin, no supply current; 0.3 mm would leave 0.15 mm to USB_DP's via); USB_LIMITED's
  triple copy → its 0.4 mm trunk (the path's narrowest copper was already 0.4 mm). Via counts on power nets: VLOGIC
  two U11 vias → one (they only join C99 and the R60 sense line, 0.2–0.25 mm F.Cu, no load current); BAT_IN: the via that fed only
  TP80 went; 3V3, 3V3A, CAM_5V via counts kept.
- **Pours** (zone fills F2 → final): GND gained 71.2 / lost 10.1 mm² on B.Cu, 68.9 / 6.9 on F.Cu, 10.9 / 3.1 on In1
  (no lost region ≥ 2.3 mm²); 3V3 In2 +10.3 / −5.5; BAT_IN In2 −2.0 mm² by the USB connector (two GND vias outside
  the J1 → Q120 corridor; BAT_IN's DC unchanged); RAW_ACT F.Cu −0.05 mm² (DC unchanged).
- **Critical-net reference** (`tools/critical_reference.py`, R6 board moved +18 mm):

| | F2 | **Final** |
|---|---|---|
| R6 method: R6-referenced samples lost on the candidate | 524 | 603 |
| R6 method: candidate samples unreferenced where R6 was referenced | 787 | 861 |
| Extended set: lost / candidate-new | 524 / 2,571 | 874 / 2,659 |
| Candidate's own unreferenced samples, extended set (own fills) | 75,264 of 257,124 | **71,607 of 245,913** |

  The +79 (R6 method) is SPI1_MOSI's F.Cu end: its via moved 0.26 mm up its own run (spi stage, RG-08 staircase), so
  the stretch over the via's In1 antipad moved with it. SPI1_MOSI's own unreferenced samples fell 822 → 727. In the
  extended set, 256 "lost" samples belong to R6's IMU_CS In2 detour, which no longer exists (removed with two
  critical layer changes), and 15 to SWCLK's In1 run under its own F.Cu run at its via. Per net, every critical net's
  own unreferenced count is equal to or lower than F2's (IMU_CS 2,936 → 933, NRST 8,464 → 7,898, SWDIO 11,897 →
  11,310, SWCLK 15,177 → 14,945, QSPI_NCS 1,103 → 1,069, SPI1_SCK 6,578 → 6,455; others equal).

## 5. Allowlist (`tools/route_check.py` ALLOWLIST, 20 entries)

| # | Category | Net, place | Reason (measured) |
|---|---|---|---|
| 1–4 | staircase | RADIO_NRST (10.0, 27.7), RADIO_BUSY (9.4, 28.2), RADIO_MISO_MCU (10.0, 28.7), RADIO_SCK (10.0, 29.7), F.Cu | radio band fan-in: vias in two columns (x 9.4/10.0, 0.5 mm rows), lanes at 0.4 mm pitch; a lane must clear the other column before its row (0.075 mm otherwise), then the corner chamfer: two short segments. RG-11 Minor; only moving the via columns removes it |
| 5 | staircase | PYRO1_CONT (34.72, 84.72) F.Cu | R6 route threading SWDIO (0.17 mm) and R77.1 (0.26–0.29 mm): a straight run hits R77.1, a single step hits SWDIO (pass-2 skeptic, measured); meets every pyro rule |
| 6 | tiny_jog | QSPI_CLK (22.85, 45.95) F.Cu | U1.36's escape must step 0.3 mm east: x 22.85 passes LED_YEL's via at 0.10 mm; the 45° step is 0.42 mm (< 0.5 mm limit); a larger step brings the clock within 0.12 mm of RADIO_RXEN |
| 7–16 | critical_via_no_gnd | RADIO_RXEN (21.2, 30.45) 1.55 mm, (23.8, 39.45) 2.23; RADIO_NRST (9.3, 50.0) 3.18; RADIO_BUSY (9.4, 28.2) 1.65, (10.0, 49.5) 2.60; RADIO_MOSI (9.4, 29.2) 1.65; RADIO_DIO1 (10.0, 50.5) 3.57; RADIO_MISO_MCU (10.0, 28.7) 2.11; RADIO_MOSI_MCU (9.4, 48.5) 1.71; GNSS_RXD_MCU (2.2, 51.5) 1.56 | no DRC-legal GND via spot within 1.5 mm: `gnd_vias` searched a 0.05 mm grid with 0.6 and 0.5 mm vias under ViaCheck, bare test pads 1.0 mm, Tag-Connect 0.508 mm and the pyro rule (band via columns, left-edge corridor) |
| 17 | critical_via_no_gnd | PYRO1_GATE_N (23.0, 88.33), 1.82 mm | same search, pyro block; slow RC-filtered gate drive |
| 18 | critical_via_no_gnd | PYRO1_CONT (41.1, 78.80), 3.05 mm | same search; DC continuity-sense divider node |
| 19–20 | critical_via_no_gnd | ARM1_SENSE (14.55, 94.15) 5.11 mm, (14.55, 97.55) 7.89 mm | the only legal spots cut BAT_IN's In2 pour between J1 and Q120 (two such vias: 3.91 → 3.95 mΩ); DC arm-sense divider node |

## 6. Gate and tests (final board)

`tools/check.sh` exit 0 (fit table trimmed):

```
DRC violations 0  unconnected 0  schematic parity 0  ERC 0
metadata / 3D model audit: OK
silkscreen outside the board outline (46.00 x 118.00 mm): 0 stroke points
R7 CAD contract: OK
routing hygiene: 0 failing, 20 allowlisted, 0 stale allowlist entries: OK
actuator safety contract: OK
  nearest bottom/pin envelope: C76, 4.150 mm from support (42.0, 114.4) (minimum 3.5 mm)
  nearest top hardware clearance: TP30.1 exposed top pad, 5.008 mm from support (4.0, 4.0) (minimum 3.8 mm)
fit check: OK (CAD envelopes only)
```

Tests on the final board (KiCad's Python): check_shell 2, fab_validation 23, fit_check 22, maze_clearances 10,
procurement 15, r6_check 17, r7_check 28, **route_check 19**, all OK; quality_audit 21 OK (KiCad Python and python3).
test_r5_repair: 1 error, the known pre-existing `routing_lands_spacing` failure.

Fab outputs regenerated with `tools/export_fab.py` and bound to the final board (`m3_fab_manifest.json`); BOM and CPL
are byte-identical to F2's, so `stock_check.json` / `cost_check.json` still apply. `r7_top.png` / `r7_bottom.png`
re-rendered (`kicad-cli pcb render --quality high --floor -w 1016 -h 2208`, 984 × 2184). Hidden designators: 89 (F2
88; the 18 GND vias took spots): newly hidden C129, C18, R12, R155, R157, TP76, TP88; newly shown C127, C150, R126,
R127, R131, R62 (list in §8).

## 7. Residuals (not fixed, with reasons)

- **Tiny jogs on non-critical nets (4, counted, not gated):** CAM_EN at U7.2 (between U7.1's and C71.1's corners: no
  single 45° line clears both), SERVO2_MCU In2 at (29.05, 87.87) (threaded between the SERVO1_OUT, PYRO1_GATE_N,
  PYRO1_CONT and GND vias), CAM_5V_SENSE at U1.35 (U1.36's corner, then RAW_ACT_SENSE_MCU's via), LOGIC_ILIM at
  U11.10 (LOGIC_SOURCE_ST's via beside the pin). Each needs a via or part moved.
- **RG-09 / RG-05 vias without a legal GND spot:** 14 (allowlisted, §5).
- **Info categories** (not gated): 90 off-centre pad ends, 36 extra-bend runs, 25 U-turns, 26 short layer hops, 10
  tracks through a same-net pad; the large slow-net detours of RG-15 (SWCLK 118 mm / 14 vias, SWDIO, CAM_PWR_EN) and
  CAM_MCU_TX's length (F2 §8) were not rerouted.
- **3V3** paths 0.02–0.27 mΩ above F2 (§4).
- **One 3V3 via under L1's courtyard** at (24.8, 34.3) (R6's (24.9, 35.0) was at its edge); tented, on the 3V3 node.
- `r7_hygiene.py` has no unit tests of its own; it is checked end to end by the pad-group invariant per stage, the
  clearance asserts, DRC, route_check and the reproducible build.

## 8. For the records (docs agent / next pass)

- `docs/M3_R7.md` "R7 board" and the build description: add `r7_hygiene.py` between `r7_rework.py` and `r7_post.py`;
  `tools/check.sh` now includes `tools/route_check.py` (clean-routing gate, 20 allowlisted exceptions); board SHA above.
  Silkscreen line, 89 hidden designators: C100 C126 C128 C129 C13 C14 C15 C151 C160 C18 C25 C30 C302 C303 C305 C31
  C311 C312 C313 C314 C60 C7 C71 C74 C8 C88 C90 C92 C94 D120 D123 D30 D31 FB31 J123 L30 LED1 Q32 R10 R101 R102 R103
  R104 R105 R11 R12 R125 R128 R129 R130 R133 R155 R156 R157 R161 R162 R163 R164 R173 R178 R180 R301 R302 R303 R304
  R311 R316 R32 R64 R74 R75 R8 R86 R88 R91 TP70 TP71 TP73 TP74 TP76 TP82 TP83 TP87 TP88 TP90 U11 U13 U7 Y1.
- `docs/R7_VALIDATION.md`: route_check 0 failing / 20 allowlisted; DC 3.96 / 3.91 / 1.36 mΩ (4 dp: 3.9567 / 3.9070 /
  1.3561); critical reference 603 / 861 (R6 method) with the SPI1_MOSI explanation; RG-09 19 of 23.
- `STATUS.md` R7 row: routing hygiene done in CAD; verified: DRC/ERC/parity, route_check, actuator contract, DC solve,
  reference sampling, tests; not verified: anything physical.
- AGENTS.md §3 could name `tools/route_check.py` as the check behind the routing rule.

## 9. Files changed by F3

`m3_design/r7_hygiene.py` (new), `tools/route_check.py` (new), `tools/test_route_check.py` (new),
`tools/check.sh` (route_check stage, header), `tools/test_check_shell.py` (route_check in the stage sequence),
`m3_design/r7_build.sh` (hygiene step and comments); `m3_design/assembly_review/m3.kicad_pcb`; `fab/m3_gerber.zip`,
`m3_assembly_{top,bottom}.pdf`, `m3_fab_manifest.json` (and BOM/CPL rewritten byte-identical); `r7_top.png`,
`r7_bottom.png`; this file and `fix2_F3_progress.md`.
