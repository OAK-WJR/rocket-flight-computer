# R8 fix pass 3: progress log

Start board: SHA-256 990c8040c5b8457bd2bd1717ed3e5c2725f32c1dda1cd7f826a0c2b458d28b18 (fix pass 2 final, reviewed by pass 3).
Scratch: <scratch>/fix3/
Coordinator backup of the 990c8040 state: scratch r8_backup_990c8040/ (tracked.diff, untracked.tgz). Pre-fix-3 hashes of
every changed / untracked file: scratch fix3/pre_fix3_sha256.txt; code / record snapshot fix3/pre_fix3_code.tgz.

## Status per item
- Session start (2026-10-20): read all eight pass3_*.md; no item landed yet.
- Generator edits (copper): r8_power (USB_LIMITED trunk y 37.25 -> 37.3, ROUTING-01), r8_place R172 x 30.6 -> 30.65,
  r8_route_pyro (RAW_ACT_SENSE lane / R172.2 stub x 30.65, pad table), r8_route_camera (CAM_PWR_EN (28.25, 36.8) ->
  (28.25, 30.025) -> R74.1, ROUTING-03; camera budget ratio 1.55 -> 1.40, worst now 1.375), r8_route_status (ENABLE_VIA
  as a 0.5 mm signal via, ROUTING-02). Stage A (build to step 6 + make_ground on the step-6 board): every step gate OK;
  r8_ground.tsv regenerated: one cover via (28.875, 32.875) -> (29.125, 32.625) and one cover row reordered; 201 rows.
- Records so far: binding_note.py / D6.8 / F10 / M3_R8 bootloader order (RF-01); ORDERING §5 (PE4 / TP122 and static gate
  in the bootloader, camera remote-sense load step, IMU signs, L5 spur + UBX-NAV-SIG, stall-test neck forward part and
  J122 contacts), ORDERING §3 left middle tab In2 3V3; D98 / D87 / r8_power comment / fix2 records C76.2 -> R78.2;
  fix2_handoff reproduce order + ACT_GATE note; test_fab_validation docstring; REQUIREMENTS M3 CPL sentence; C12 #13;
  owner summary D51; P3b row; m2_sweep margin_free category (ROUTING-03 record ask).
- Two full builds identical (17 files): board c84f00b88f5fb9409de40f33b2d51a48fb29fb66c386c869b7f93ea791e37c54, netlist
  0cc1ed69 unchanged (611 / 769 s; the second shared the CPU with the DC solves). Build DC gate (0.1 mm): RAW 5.90 mm
  17.6 C, BAT 6.85 mm 14.8 C, FET 4.80 mm 22.3 C. Every step gate OK (camera budget 1.40 holds at 1.375; L10_EXCEPT R172
  0.685 measured and set before build 2).
- Measured on c84f00b8 (scratch fix3/measure3.json): CAM_PWR_EN-USB_LIMITED 0.200, R172.1/.2-USB_LIMITED 0.230,
  Q120.9-BAT_ENABLE 0.23 (via 0.5 mm), BAT_ENABLE-BAT_IN min 0.200 at U9.1; F9 pad edges R167 1.905 ... C96 7.817;
  J122 pads y 78.71-80.31; GND pour 0.151 at R120.2 / C120.2 / R121.1 / R121.2 / Q122.3 / J1.4 / J123.1; ViaCheck 12
  pairs / 11 vias; Q123 dot 0.012 mm2. m2_sweep: chain 23, adjacency 53 rows (28 pairs, 9 at 0.150), pad 33,
  routes 28, margin_free 1 bump (BAT_ENABLE FP) + 4 C11 "found". Survey (quick): S1 1497.6, S6/S7 1.175 / 287.4,
  P1 0.9051, P6 1752.2; requalify / pyro_neighbours / refaudit equal to fix 2 but the USB_LIMITED coordinate.
- Records written: R8_VALIDATION review-pass-3 table, C5/C7/C11/C12/C12b/C20, part F, owner summary, pyro observations;
  D106-D109 (+ D6.8, D76, D87, D98, D105 corrections); M3_R8 routing / pyro / power / RF / F9; ORDERING §3 / §5;
  REQUIREMENTS F10 / M3. Running: DC 0.05 + GND, check.sh / r8_fab.sh / tests / binding note / check_r8 / make_ground
  --built / paste_check (scratch fix3/post.sh).
- Gate standalone exit 0; r8_fab.sh exit 0 (CPL ef90bfa1, only R172's row; BOM be711876); 272 tests / 17 suites OK after
  the fab step; quality_audit 21 x 2 OK; binding note regenerated; check_r8 report equal but SHA; make_ground --built
  reproduces r8_ground.tsv; paste_check OK; route_check r7 on R7 (with its project files) OK.
- DC 0.05 + GND 0.1 on c84f00b8: every figure equal to fix pass 2's (RAW 1.45 / 5.94 / 17.5; BAT 0.45 / 6.99 / 14.5;
  FET 0.18 / 4.97 / 21.4; GND 0.69 mOhm); supply usb 52.62, BAT_IN rows equal. Scorecard index 15.3, 20 / 11.
- Evidence step9/evidence/fix3_* (15 files); fix3_baseline_sha256.txt, fix3_generators.diff, fix3_handoff.md written.
  Records done (R8_VALIDATION, M3_R8, D106-D109 + corrections, ORDERING, REQUIREMENTS, MARGIN, STATUS, AGENTS, README).
- Last edit: r8_place.tsv R172 basis "D33 D106" (unused column); build 3 started to confirm the final generator state
  still gives c84f00b8.
- Build 3 on the final generator state: identical (17 files, c84f00b8), gate OK; fab manifest still verifies.
  fix3_generators.diff regenerated (11 files). Scratch board copies deleted (fix3/ now logs and scripts only, 2.5 MB).
- DONE (not committed, per brief); handoff fix3_handoff.md.
