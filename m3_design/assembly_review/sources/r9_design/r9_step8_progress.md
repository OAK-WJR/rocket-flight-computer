# R9 step 8 (ground): progress log

Brief: r9_plan.md §4 step 8. Build `m3_design/r9_ground.py`: GND vias at every critical layer change, stitching
<= 2.5 mm where the plan says, the fence, pour hygiene (no slivers, no unstitched fingers, no pour trims if avoidable).
Verify: P7 = 0, P9 <= 3.5, P10 <= 7 (or a measured, recorded cause), R6b <= 0.08, route_check r9, check_r9.

## Session 1

- Started. Scratch shim and runner from step 6 (`<scratch>/s6/inj/nomouse.dylib`, `<scratch>/s6/tools/build.py`) are
  present. Read the plan, owner decisions, step 6 / 7 handoffs.
- Wrote `m3_design/r9_ground.py` (builder: grows the strip's F / B / In1 GND pours to the board, draws
  `m3_design/r9_ground.tsv`) and `m3_design/r9_ground_aid.py` (design aid generating the table: return, pad, grid,
  cover, island, finger stages; R8 make_ground.py's legality with R9 changes).
- First measurements (step-7 board + pours only): route_check r9 fails 1 pour_sliver + 7 pour_finger; DRC 4
  starved_thermal + 7 unconnected; P7 25, P9 13.1, P10 21.8, R6b 0.1732.
- R6b analysis (`<scratch>/s8/cref_an.py`): 5430 / 31359 unreferenced; own-via antipads of step 7's 12 critical vias
  ~3,880 samples (151 per via side), Y1_In2_keepout 917, other vias' antipads ~330. Step 8 adds none. Floor even with
  the board-minimum inner clearance: ~0.092 (own antipads alone). R6b <= 0.08 is not reachable by step-8 means.
- P9 / P10 floor (`<scratch>/s8/floor.py`, every legal spot used, no spacing): p95 3.42, max 7.04 at (30.73, 93.73),
  the BAT_IN entry pours (F / B / In2), where a GND via would cut the 7.7 A path.
- After the aid's first passes (pours + 146-161 vias): P9 3.57-3.76, P10 7.33, P7 15-17; the fingers / sliver are
  geometric (two parallel tracks or a track beside a power pour 0.45-0.8 mm apart), no via can serve them.
- Planned table edits in earlier steps (each recorded as D-S8-*): E1 NRST diagonal 0.04 mm east (usb_swd), E2 RAW_ACT
  F pour over the RAW bar's east end (step 6), E3 RAW_ACT F west edge 29.75 beside the ARM lane (step 6), E4
  RAW_PROTECTED F pour narrowed to x 41.3 for y 72-84.2 (step 6; joins TP74 / TP88 and the C6 / C7 / C8 GND vias to the
  F GND), E5 CAM_FAULT_N bend at x 28.669 (camera), E6 BAT_ENABLE x 44.7 (power_ctl), E7 VLOGIC hold-up via x 38.5
  (step 6).
- Rebuilt steps 3-7 with the table edits (all their gates pass): NRST (usb_swd), RAW_ACT F pour (west edge 29.75 by
  the ARM lane; over the RAW bar's east end, the bar ending at 27.6), RAW_PROTECTED F pour narrowed to x 41.3 (y 72-84.2),
  VLOGIC hold-up via x 38.5 (+ status tap), CAM_FAULT_N bend at 28.669 (camera), BAT_FAULT_N edge lane x 45.15
  (power_ctl; the first try, BAT_ENABLE east, broke power_ctl's length budget by 0.2 mm), east test-pad column
  reordered (TP81 70.4, TP74 73.0, TP88 75.6; TP81 a T off the camera branch), TP90 (33.85, 58.65), R105 turned
  (31.94, 47.55, 180), R182 0.2 mm forward (54.6).
- Aid stages now: return, pad, grid, cover (may revive a removed island if the island stage gives it a second via),
  island, patch (P9 radius 3.45, SPACING_ISLAND 0.6), finger, strap (C17.2, C24.2: DRC starved_thermal otherwise), reach.
  Legality: In2 guard only under critical / reference B.Cu tracks; no antipad in an In2 power region's narrow outline part
  (the 3V3 finger: a first try split it, DRC unconnected 3V3); EDGE 0.8; corridor margin 0.3 + r + 0.05.
- Result (scratch, table `m3_design/r9_ground.tsv`, 186 rows: 182 vias, 4 strap tracks): DRC clean but silk, 0
  unconnected; route_check r9 0 failing; P9 3.45, P10 7.32 (BAT_IN entry, floor 7.04), P7 9 (recorded pockets), R6b
  0.1732 (unchanged from step 7). `m3_design/r9_ground_check.py` passes on it (2.5 min).
- Full build 1 started (stages 0-35).
- Last fixes before the full builds: TP90 at (33.85, 58.65) (its first try at 58.9 overlapped R103's courtyard), R105
  turned, R182 0.2 mm forward (C122.2's second spoke), patch / reach stages, survey-consistent board box in the aid,
  WEAK_EXCEPT (9 pockets) and P10 <= 7.35 (recorded cause) in the gate, the In2 gate and test_r9_ground.py.
- Full builds 1 and 2 (stages 0-35, every gate OK, the step-8 gate included): byte-identical, board 95d59a54...
- Tests: 25 suites, 451 tests OK, none skipped (test_r9_rf's board class detects the strip by step 8's pour name too;
  test_r9_pyro's pending-route seed moved into J124.1's barrel: with In1 GND a GND via elsewhere is not dangling);
  quality_audit 21 OK under both pythons; audit_artifacts exit 0.
- Scorecard (0.1 mm DC): step-8 rows P9 3.45 (met), P10 7.32 (recorded cause), P7 9 (miss, recorded pockets), R6b
  0.1732 (miss, not reachable in step 8), X8c 0 (met). Other misses are steps 3-7's (step8_deltas.txt: unchanged).
- Evidence in step8_evidence/; handoff written. Verification not met in full: P7 = 0 and R6b <= 0.08 (owner).

## Session 2 (continuation: R6b rework; coordinator: P7's 9 pockets accepted as recorded items, R6b must beat R8's 0.1107)

- Read the session-1 log, handoff, D-S8-*, step-7 handoff and decisions. Scratch shim / runner (`<scratch>/s6`) still present;
  no GUI session. Board at start: 95d59a54... (matches the handoff).
- R6b breakdown on the built board (`<scratch>/s8b/an.py`, per via side): 12 critical layer-change vias, one per net, each
  151-173 own-antipad samples per side (antipad r 0.50 = via r 0.25 + In1 / In2 clearance 0.25); double sides: HSE_OUT B
  334 (via between Y1.3 and C26.1), QSPI_NCS B 316 (U3.1 and R10.1 branches), IMU_CS B 246 (T 0.28 mm off the via);
  gap 992 = HSE_IN B 753 + HSE_OUT B 164 (Y1_In2_keepout) + QSPI_NCS B 75 (R10.1 inside the keep-out); other vias 293.
- JLC capabilities (https://jlcpcb.com/capabilities/pcb-capabilities, fetched 2026-10-23): inner-layer via hole to copper
  0.2 mm, via hole to track 0.2 mm, preferred min via hole 0.2 mm, 0.2 / 0.25 mm holes with < 0.45 mm via diameter cost
  more. The board's own rules (min via 0.5 / hole 0.3, DRU hole clearance 0.25) are R8's and stay (no rule weaker than R8).
- What-ifs on a scratch copy (`<scratch>/s8b/exp2.py`, `<scratch>/r9/x1`):
  - unconnected inner via pads removed (KiCad: remove unconnected layers, keep start and end; R4 E4-F1's precedent),
    every via: 0.1396 (own 3,386, gap 992, other 1); antipad r 0.40 = hole r 0.15 + 0.25 hole / zone clearance;
  - plus an In2 GND plane under the crystal in place of the void (AN2867 Rev 10 section 5.1, "a dedicated underneath
    ground plane"): 0.1022 (own 3,205, other 1, gap 0);
  - plus 0.45 / 0.2 critical vias (not adopted: weaker than the board's 0.5 / 0.3 minimum): 0.0888.
- Floor with 12 vias at r 0.40: 24 sides x ~119 = 2,856 samples = 0.091 > 0.08: R6b <= 0.08 is out of reach by the board
  rules (fewer than 12 critical vias needs U3 / Y1 / U4 off the bottom, under U1; a smaller antipad needs a hole < 0.3 mm
  or a hole clearance < 0.25 mm). Rule-preserving routing changes without the crystal plane reach ~0.12 at best (HSE's
  crystal-to-cap B.Cu runs lie inside the keep-out by definition): the crystal plane is the one lever past R8.
- Decided (D-S8-19 / 20): via pads removal on every via and the crystal's In2 GND plane, both in r9_ground.py (step 8);
  step-7 tables unchanged (the remaining second branches: HSE_OUT's in-line via, D86; NCS's R10 branch and IMU_CS's T,
  boxed in the IMU knot by QSPI_IO2's diagonal and BOOT0's via).
- Built (repo): r9_ground.py `xtal_plane` (rule area -> In2 track keep-out; R9_GND_In2_Y1, GND, priority 11, the area's
  outline, R9_GND_In2's settings) and `strip_via_pads` (every via REMOVE_EXCEPT_START_AND_END); r9_ground_check: table
  gate also checks both, new `xtal` gate, reference gate now fails any sample outside its own via antipad (REF_STRAY:
  USB_DM's edge at CC1's via, 1 sample) and holds REF_UNREF_MAX 3,206; r9_power_check.gate_in2 accepts IN2_LATER
  (R9_GND_In2_Y1); step8_evidence/unground.py undoes both; test_r9_ground +5 tests (17).
- First gate run (step-7 board from unground.py + new r9_ground.py): stitch FAIL on cover via (25.65, 59.95): inside the
  In2 RAW_ACT region 0.05 mm south of its corridor box; with the via's In2 ring gone its antipad (r 0.45) no longer hides
  the corridor fill from the gate's 0.55 mm test (before, the 0.55 mm antipad made the test blind to vias inside a
  region). Fixed at the cause: the aid also forbids (fill in the corridor) grown by 0.3 + r + margin; table regenerated
  (187 rows; 5 rows differ, all round that via). xtal FAIL on 0.0007 mm2 of 3V3: U1.6's 3V3 via ring (14.5, 50.65), 0.05 mm
  across the area's edge (as before): the gate now subtracts flashed via pads. Second run: all 12 gates OK; R6b 0.1022
  (3,206 / 31,359), P9 3.45, P10 7.32, P7 9, route 0 failing, DRC clean but silk.
- Decisions written: D-S8-17 (replaced), D-S8-19, D-S8-20, D-S8-02 (session-2 note).
- Full build 1 started (runner stages 0-33, snapshot of the step-7 board, then 34-35).
- Full builds 1 and 2 (session 2, no notch): byte-identical, board cca2b99c...; aid --check reproduced the table from the
  build's own stage-33 board; 457 tests OK. The survey's extended reference audit then showed NRST's B.Cu run to C24.1
  (y 50.5-50.7, 0.05 mm forward of the crystal area) 0.33 mm over the gap between the plane and the 3V3 fill (the 3V3 edge
  moved from the area's edge to 0.25 mm beyond it): a new extended-set crossing. Tried a full 0.25 mm inset of the plane's
  forward edge: NRST fixed, but the 3V3 fill then met the area's edge exactly (0.001 mm2 of arc slivers at U1.6's 3V3 via,
  xtal gate FAIL). Settled on r9_ground.xtal_outline: one notch per critical-reference B.Cu track lying wholly outside
  the area within reach (box + half width + 0.3 mm): one notch under NRST (x 18.9-20.73, y 50.2-50.45). Gate: all OK,
  R6b 0.1022, extended set 3,931 unreferenced (own antipads but USB_DM's one sample), no foreign fill under the crystal.
  The reference gate now also checks the extended set; REF_UNREF_MAX 3,206; +1 test (the notch / outline).
- m2_sweep: adjacency 39 -> 33 (six via-to-via pairs on In1 / In2 gone with the rings); scorecard P6 1533.3 -> 1484.0,
  P1 0.8973 -> 0.9094, P3b 8 -> 4, index_r9 85.6 -> 84.8; Y1 / Y1b / Y2c unchanged.
- Full builds 3 and 4 (with the notch): every stage rc 0; build 3's hash list was lost (zsh did not split the file list),
  build 4's board 89ddea8d...; aid --check reproduced the table from build 3's stage-33 board (identical to build 1's).
  On build 4's board: 458 tests OK (none skipped); fit OK; plate f1 256.6 Hz; rule-H seeded suite OK; check_r9 39 OK,
  K-legends FAIL (22, step 9); survey (0.1 mm DC) R6b 0.1022, P7 9, P9 3.45, P10 7.32, X8c 0; audit_artifacts exit 0.
- Full build 5 started (second replay with the notch) to confirm byte identity with build 4.
- Full build 5: byte-identical to build 4 (sheets, netlist, DRU, variants, board 89ddea8d...). Final gate report, reference
  causes, refaudit, scorecard, check_r9 / seed / fit, tests, audit and deltas written to step8_evidence/ (paths
  sanitised); handoff rewritten for session 2. Scratch boards (`<scratch>/r9/s7`, `x1`) and the downloaded AN2867 copy
  deleted; `<scratch>/s8b` keeps only throwaway scripts and logs.
- Result: every step-8 gate passes; R6b 0.1022 (floor better than R8 met; 0.08 out of reach by the board rules, causes
  per class in D-S8-17); P9 3.45; P10 7.32 (recorded cause); route_check 0 failing; X8c 0; P7 9 (coordinator: recorded).
