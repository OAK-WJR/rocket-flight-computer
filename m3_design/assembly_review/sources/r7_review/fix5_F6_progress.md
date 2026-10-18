# Fix pass 5, agent F6 (board, tools): running log

Start board SHA-256 c6fe595cafb91b088ac0b2c812f409f9ca5b86ac45a651102e168b0a5d83c7c7 (fix pass 4 final).
Scratch: <scratch>/fx5/
(base.kicad_pcb = start board copy).

## Log
- [1] No previous progress file; started fresh. Read pass-5 reports (routing_geometry, routing_quality, regression,
  docs), pass5_verdicts.json, fix4_F5_handoff/progress, R7_VALIDATION deviation list A-D.
- [2] route_check extended (tools/route_check.py, uncommitted; F5 copies in scratch fx5/*_f5.py): tiny_jog through
  T/via/pad nodes (side branches off a straight run excluded), staircase followed through T/via/pad nodes on one layer,
  acute_angle on every branch pair, pour_stub (pour-only end, > 1.0 mm of its run inside its own fill), via-into-pad
  layer changes count for critical_via_no_gnd, via_overlap (same-net rings), LEFTOVER_CATS = all HYGIENE. Base board:
  14 new gated failures (RAW_ACT pour_stub, ACT_GATE acute, 4 node jogs, 4 node staircases, PYRO1_GATE TP122 no-GND,
  3 launch via overlaps) + 5 unrecorded non-critical node jogs.
- [3] Probed every redraw on checkpoint fx5/ck1 (polish --stop reroutes) with fx5/probe.py (Clearance + ViaCheck).
  Forced (measured): PULLPIN_EXT across-via jog (B.Cu lane x 34.4 between C94.1/C94.2; via column x 34.15: C160.2 F.Cu,
  C60.2 B.Cu, CAM_5V B.Cu); I2C1_SCL step (any BOOT0 via between IMU_CS x 24.35 and SCL x 25.35 collides: needs 1.095
  mm, channel 1.0); PYRO1_GATE at TP122 (GND via within 1.5 mm is within 1.02 mm of the bare pad; GndFit finds 0);
  REG-03 GND via (28.55,87.21): 5 legal spots within 1.45 mm of PYRO1_CONT's via, none >= 0.25 mm from the sense pads.
- [4] r7_polish: PYRO1_CONT F.Cu run S/SE/S (RQ-02); new stages band5, qspi5, jogs5, tidy5, arm_gnd, band_end after
  reroutes. Ran on ck1 copy (t1): all stages pass the pad-group check.
- [5] Stages added/extended: band5, qspi5, jogs5 (CAM_EN, CFN+SERVO4_MCU, LOGIC_ILIM, CAM_RX/TX_WIRE off In1 + GND via
  move, LOGIC_SOURCE_ST, CAM_5V_SENSE In2, PULLPIN_EXT, LED_RED F.Cu hop, BOOT0), tidy5 (D1, D2, D3, D4, D7, D9, D10,
  D11), arm_gnd, band_end, edge_stitch (14 vias, D15), gnd_pieces (4 second vias, REG-02); npth_ok added to via checks
  (an edge via first violated TH3's copper-to-hole 0.25). r7_post: courtyard test on every visible designator (8 hidden:
  C301 D120 R155 R172 R80 R83 R88 TP84). TRIM_EXPECTED 23.
- [6] route_check: measured_check (ROUTE_FIGURES per net) and alt_audit (1-3 segment redraws, Clearance, keep-outs, edge;
  slack 1.1x+0.2 mm, power rails 1.0x) gated; LEFTOVERS rewritten (31 -> 30 entries, honest search wording); allowlist
  A1/A2/A5/A17/A18 gone, PYRO1_GATE TP122 added (nognd_audit re-checks). Dev board fx5/d4 (SHA 55ce88e7...): DRC 0/0/0,
  routing hygiene OK (0 failing, 33 allowlisted, 30 leftovers, 0 figures, 0 removable), check_r7 OK, actuators OK.
- [7] Tests: test_route_check 41 OK (9 new). Analyses on d4 vs start: pad groups identical (191 nets), CH1 pyro copper
  XOR 0.00000 mm2 on every layer, critical reference vs start 51 lost (IMU_CS: BOOT0's moved via antipad) -> BOOT0 move
  reverted; vs R6 603 -> 654 (51 IMU_CS) / candidate-new 861 -> 933 (+21 QSPI_CLK at RXEN's via antipad, accepted).
  Pass-2 scan.py 958 (595) -> 947 (591). Single-via GND pieces 40 -> 36.
- [8] First full r7_build.sh run aborted after r7_hygiene (I edited the script's comments while bash was reading it);
  post-hygiene SHA dfca97c4... = fx4/hyg.kicad_pcb (upstream unchanged). Rerunning the real script untouched.
- [9] DC (final vs start) showed the first edge_stitch placed vias inside the J1 -> Q120 corridor (BAT_IN +0.10 mOhm):
  stitch_region / gnd_pieces now use the full GndFit test (corridor policy). Final: BAT_IN J1->Q120 4.55 -> 4.58 (ARM
  vias only), J1->U9 15.14 -> 15.18, USB_LIMITED 72.37 -> 72.32, every other path unchanged.
- [10] DONE. r7_build.sh (unmodified, from R6) exit 0, check.sh passed; board SHA
  1ffc2585cbbb2a49623a5010b2792500849f06989cf43e48fb3e56068cddf9df. Fab regenerated (BOM/CPL identical, manifest OK,
  verify-cpl OK); renders regenerated (984 x 2184). Tests 168 + quality_audit 21 x2 OK (r5_repair known error).
  Handoff: fix5_F6_handoff.md.
