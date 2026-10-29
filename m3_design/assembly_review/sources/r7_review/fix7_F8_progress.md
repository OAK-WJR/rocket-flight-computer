# R7 fix pass 7, agent F8: running log

Start board SHA-256 4673c0a0f9fd290af694d6ca5a97e99b3b225466882ba5c6e57a9ad856b96ebd (F7 final).
Scope: items 1-6 of the F8 brief (P7-ROUTING-01..04, P7-DOCS-01, P7-REGRESSION-01..03, C24-C26 removables,
route_check sub-chain bump test + via-on-track-body test, silkscreen legends, C1 neck widening).

## Log
- Read pass-7 reports/verdicts, F7 handoff.
- Dev pipeline: scratch f8/pre.sh builds R6 -> ... -> polish --stop bat_in_f6 (pre7.kicad_pcb, 9 min); f8/dev.sh runs
  polish --start bumps7 + post (4 min); f8/gate.sh runs the check.sh steps (check_r7 duplicate-UUID findings are --start
  artefacts).
- r7_polish.py: fix-pass-7 stages bumps7 (3V3A, CAM_5V, VLOGIC, A34 x2, USB_LIMITED), v3pair7, acten7, arm1_7 (split at
  R180.1 instead of the records' redraw, which would leave R180.1 joined by overlap), tidy7 (CAM_FAULT_N, LED_RED,
  I2C1_SDA), sense7 (CAM_5V_SENSE, SERVO2_OUT), bat_via7 (centre + split), v3a_hop7 (restore fix-pass-5 drawing,
  min gap 0.200 mm measured; reviewers' 0.34 was wrong), bat_in_b7 (0.1 mm outline notch along the deleted leg).
  TRIM_EXPECTED 22 -> 23 (the 3V3A finger is back). First dev run: DRC 0/0/0, actuators OK, fit OK.
- route_check: topology() factored out of scan (instances identical on the start board, 324 = 324); via_on_track
  (hygiene) + via_on_track_in_fill (info); RedrawCheck (shared by alt_audit and bump_audit: true outline at 0.5 mm,
  Edge.Cuts circles exact, module keep-outs for non-GND nets; strict: no other power-pour fill, not between a two-pad
  part's pads, no same-net copper but the end branches); bump_audit (local_bump, gated on critical nets; same-heading
  squeezes rejected). Start board: 7 local bumps, 3 via_on_track (= reviewer's), 6 in-fill GND.
- USB_LIMITED C98.1 redraw dropped: it cuts R105.2 off GND (pad-group check); allowlisted as local_bump with that reason.
- route_check allowlist: A34 14.368 mm + true reason; new chain_detour 3V3A hop (2.505 mm, gap 0.200 mm); local_bump
  USB_LIMITED; VLOGIC 66.37; LEFTOVERS: CAM_5V_SENSE deleted, CAM_FAULT_N 92.46, SERVO2_OUT 34.94. alt_audit and
  bump_audit reject same-heading squeezes. Tests: route_check 49 OK (4 new), r7_check 35 OK (legend_subjects new).
- r7_post: label_near (legends within 6 mm of their part, bottom face first); UART legend deleted; check_r7
  legend_subjects gates it (start board: 5 far legends; dev: 0). Hidden designators 90 -> 90.
- C1: f8/dc_ipc.py (dc_solve + equipotential cuts) reproduces the records' 0.1 mm necks (2.02 / 3.61 / 2.10).
  necks7: C86.2's GND via out of the RAW_ACT neck (2.02 -> 2.95), ACT_FET_S_B west edge to 0.6 (2.10 -> 2.64), six
  crossbar stitching vias (BAT_IN J1->Q120 3.90 -> 3.03 mOhm, neck 3.61 -> 3.66 moved to the In2 arm).
- dup7 (C23 3V3 plane duplicates: F.Cu hop and In2 run) added, SPLIT_OK for its 3V3 track-only split.
- Build #1 (r7_build.sh): gate OK, board fc241505... BUT critical_reference start -> build#1 lost 465 QSPI_NCS B.Cu
  samples (25.0-26.4, 40.9-42.0): the LED_RED In2 straightening cut the 3V3_In2 reference under QSPI_NCS. LED_RED
  redraw reverted (its bump has a reason; the records' "removable" was wrong). Build #3 running.
- SERVO2_MCU non-critical redraw dropped (cut QSPI_IO2's In2 reference, 179 samples); RedrawCheck strict now refuses
  redraws nearer a paired-layer critical track than the window (test). review7: BUZZ_DRV, IMU_INT1.
- Builds #5 and #6 (r7_build.sh, unmodified): c872a3d30509cccf5f78b64cde48ef722ee85c7be23c4848b07ce4082a852de3 both,
  check.sh exit 0. critical_reference start -> final 0/0 (both methods). Tests 178 OK + quality_audit 21 x2; r5_repair
  known error. Fab regenerated (BOM/CPL identical, manifest bound), renders regenerated.
- Handoff written: fix7_F8_handoff.md. DONE.
