# R8 fix pass 4: progress log

Start board: SHA-256 c84f00b88f5fb9409de40f33b2d51a48fb29fb66c386c869b7f93ea791e37c54 (fix pass 3 final, reviewed by
pass 4, then the pass-4 records pass, which changed no build output).
Scratch: <scratch>/fix4/
Coordinator backup of the c84f00b8 state: scratch r8_backup_c84f00b8/ (tracked.diff, untracked.tgz). Pre-fix-4 hashes of
every changed / untracked file: scratch fix4/pre_fix4_sha256.txt (276 files); code / record snapshot
fix4/pre_fix4_code.tgz.

## Items
- R8P4-ROUTING-01 (copper): r8_route_rf.py trio below the fence 0.1 mm west, step 0.5 mm; make_ground.py FENCE_X
  20.00 / 22.10 -> 19.95 / 22.05, STRIP_STITCH (22.10, 26.70) -> (22.05, 26.70); r8_ground.tsv regenerated (stage A).
- R8P4-ROUTING-02 (copper): r8_power.py USB_LIMITED trunk through (32.2, 55.3), R87.1 branch a T drop.
- Text: RF-02 (ORDERING §5 camera-supply distances), POWER-02 (12 relief pads vs the DRU comment), DFM-02 (R70
  designator move), INTEGRITY-02 (r8_build.sh "seven pour trims").

## Status per item
- Session start (2026-10-20): read pass4_routing.md, fix3_handoff / progress, R8_VALIDATION's pass-4 section; no item
  landed yet.
- Generator edits: r8_route_rf.py (TRIO x 20.5 / 21.0 / 21.5, step y 22.500 / 22.707 / 22.914, TRIO_STEP 0.5;
  comments), step7/make_ground.py (FENCE_X 19.95 / 22.05, STRIP_STITCH (22.05, 26.70)), r8_power.py (USB_LIMITED
  trunk through (32.2, 55.3), R87.1 a T drop), r8_build.sh comment ("seven pour trims (D65, D90)", INTEGRITY-02);
  ORDERING §5 camera-buck distances (RF-02). The c84f00b8 board rebuilt in scratch (fix4/c84.kicad_pcb, SHA checked)
  from the coordinator backup for diffs.
- Stage A (scratch fix4/stageA.sh): every step gate OK (rf family 436.6 -> 436.9 mm of 445; power gate OK with the T);
  make_ground on the step-6 board: 201 rows, only the two fence vias and the stitch via moved as intended and one cover
  row (19.125, 25.875) reordered (same coordinates); installed as m3_design/r8_ground.tsv. Build 1 started.
- Build 1 (609 s): exit 0, every step gate and tools/check.sh OK; board cc044ea0922ff826df19af9d9726d92c096ab2b127025b55d123d8772e5fb4a7,
  netlist 0cc1ed69 unchanged; DC neck gate 0.1 mm RAW 5.90 / 17.6 C, BAT 6.85 / 14.8, FET 4.80 / 22.3 (= fix pass 3).
  Diff against c84f00b8 (r8p4rt/diff4.py): exactly the reviewer's rec4: RXEN / BUSY / MISO_MCU 3 tracks each, GND vias
  (20.0, 23.3) / (22.1, 23.3) / (22.1, 26.7) -> x 19.95 / 22.05 / 22.05, USB_LIMITED -4 +3 tracks; no footprint or
  designator moved (R70's reference (29.228, 31.621) unchanged); zones F GND +0.24, B GND +0.88 mm2, and the In2 3V3
  antipad round (22.05, 26.7), area unchanged (added after review pass 5, R8P5-INTEGRITY-02).
  measure4.py: RXEN-(19.95, 23.3), MISO_MCU and MOSI to (22.05, 23.3) / (22.05, 26.7) all 0.200 mm; fence openings
  1.75 / 2.10 / 2.10 mm; USB_LIMITED B.Cu 51.443 -> 49.586 mm; the 12 relief pads as the reviewer listed.
  p4scan (reviewer's): acute pairs 3 -> 2, gaps -4 (the four MISO / MOSI rows), +1 plain junction (the T), knees
  0.40 -> 0.50 mm; par.py: USB_LIMITED's 1.65 mm parallel run gone; gapnet USB_LIMITED within 0.6 mm identical.
- Build 2 started; DC 0.05 + GND 0.1 and m2_sweep running on scratch build1/ (project files copied beside it).
- Build 2 (769 s, sharing the CPU with the DC solves): exit 0; the 17 files (board, netlist, 15 sheets) identical to
  build 1: board cc044ea0922ff826df19af9d9726d92c096ab2b127025b55d123d8772e5fb4a7. Silkscreen identical to c84f00b8
  (silkdiff.py: 571 items, none changed). M2 sweep (build 1): chain 23, adjacency 53 -> 51 rows (the two MISO / MOSI
  fence-via rows), pad 33, via_step 1, poured_hop 2, routes 28 (USB_LIMITED 1.28 -> 1.23, RXEN +0.08 mm), pad_edge 0,
  folds 26, short_hop 9, bumps_all 1 (7 windows), margin_free 1 bump (29 windows) + 4 redraws: the rest equal.
- Records so far: R8_DECISIONS D110, D111, D42's branch correction, D33 / D37 fix-pass-3 coordinate pointers (pass-4
  routing §9 note). post.sh (check.sh, r8_fab.sh, tests, quality_audit, binding note, check_r8 report, make_ground
  --built, paste_check, route_check r7 on R7) running; DC 0.05 + GND still running.
- post.sh on the worktree board (cc044ea0): check.sh exit 0; r8_fab.sh exit 0 (CHECK none, BOM be711876 and CPL ef90bfa1
  unchanged, manifest bound to cc044ea0, renders regenerated); 272 tests in 17 suites OK after the fab step;
  quality_audit 21 x 2 OK; binding note regenerated (only board_sha256 changed); check_r8 report equal to fix pass 3's
  but the fence openings (19.95-22.05, 22.05-24.15 = 2.10 mm) and 1588 track ends (was 1590); make_ground --built
  reproduces r8_ground.tsv; paste_check OK; route_check r7 on R7 (with its .kicad_pro / .kicad_dru) OK.
- Evidence on build1 (= cc044ea0): route_check report (94 instances: + width_change_junction USB_LIMITED (32.2, 55.3));
  refaudit 11.07 % (equal), extended 5.80 % (102408 samples, +24 on RADIO_MISO_MCU, 5944 unreferenced, equal);
  requalify and pyro_neighbours equal to fix pass 3 but the SHA. DC 0.05: RAW / BAT / FET identical to fix pass 3's,
  line for line (1.45 / 0.45 / 0.18 mOhm, 5.94 / 6.99 / 4.97 mm, 17.5 / 14.5 / 21.4 C). Scorecard: index 15.3, 20 / 11
  (equal); moved C2 90 -> 91, S1 1497.6 -> 1497.9, S2 2088.8 -> 2087.2, S6 / S7 1.175 / 287.4 -> 1.174 / 285.8, S18
  795 -> 794, R7 ext samples. Evidence fix4_* written to step9/evidence (paths normalised, SHA added as fix pass 3 did).
- Records written: R8_DECISIONS D110 / D111 (+ D33 / D37 / D42 pointers); R8_VALIDATION header, baseline, step table,
  gates, scorecard, requalification rows, review-pass-4 dispositions (6 rows) and intro, owner summary, C12 summary and
  table (#5 / #6 removed, renumbered), C19, C21 removed, part E / F, "Open after fix pass 4"; M3_R8 header, copper,
  routing table and paragraph, ground (+ relief rule as built), checks, firmware SHA, manufacturing outputs (+ R70);
  STATUS, AGENTS, README, ORDERING (§1, §2 cost note, mark, tabs, §4), REQUIREMENTS (M2 counts, J2 sentence);
  fix3_handoff (R70 note). Pending: GND return solve and supply table, then DC records (M3_R8, R8_VALIDATION F4 row,
  STATUS, REQUIREMENTS F4, MARGIN_PRESCRIPTION), handoff, generators diff, baseline file.
- DC GND return (0.1) and supply table (0.1, every row) on cc044ea0: GND 0.69 mOhm, every line identical to fix pass 3's;
  supply rows equal but USB_LIMITED 52.62 -> 52.66 mOhm (D111). Evidence fix4_dc_* (5 files) written; 15 fix4_* files in
  all. DC records done (M3_R8, R8_VALIDATION F4 / necks, STATUS, REQUIREMENTS F4, MARGIN_PRESCRIPTION, D111).
- fix4_baseline_sha256.txt (276 files), fix4_generators.diff (5 files), fix4_handoff.md written. Final standalone
  tools/check.sh exit 0 on cc044ea0 after every record edit; files changed this pass match the list in the handoff.
  Scratch board copies deleted (fix4/ now logs, scripts, the pre-fix4 hash list and code snapshot).
- DONE (not committed, per brief).
