# R8 fix pass 2: progress log

Start board: SHA-256 6600ef9462b37ec58540e0dd7edd97577c3e778bda0d233d3c1dffc555ad5a8d (fix pass 1 final, reviewed by pass 2).
Scratch: <scratch>/fix2/

## Status per item
(updated as items land)
- Session 2 start (2026-10-20): no item had landed; board still 6600ef94. Pre-fix-2 snapshot of the 222 changed /
  untracked files: scratch fix2/pre_fix2_state.tgz, hashes fix2/pre_fix2_sha256.txt (INTEGRITY-03 stand-in; no commit).
- Generator edits made and staged-built to check.sh OK: r8_power (IN2_BAT_IN trim, SMALL_VIA for C75.2 / R78.2 (first written C76.2; fix pass 3, R8P3-INTEGRITY-01) / R72.2 / V_IN1), r8_place (R81 (39.6, 91.275, 90, B): r81w fails R5 L10 against J121), r8_route_status (BAT_ENABLE spine + R81.1 stub), r8_route_usb_swd (C83.2 link split; C83 +0.175 fails L10 against J3.1, U10 -0.175 lands U10.3 on V_D), r8_ground.relieve (J123.2), make_ground (relief model, pad stage: U9.8 via (44.65, 86.775)), r8_ground.tsv regenerated (201 rows), check_r8 battery_pyro drain + test, m2_sweep adjacency_pad, fix1 evidence SHA fields. Two full builds started.
- Two full builds identical (17 files): board 990c8040c5b8457bd2bd1717ed3e5c2725f32c1dda1cd7f826a0c2b458d28b18 (612 / 609 s; build DC gate RAW 5.90 mm 17.6 C, BAT 6.85 mm 14.8 C 0.45 mOhm, FET 4.80 mm 22.3 C). Copy in scratch fix2/fin. Analyses next.
- Analyses on 990c8040 done: DC 0.05 (RAW 1.45 mOhm 5.94 mm 17.5 C; BAT 0.45 / 6.99 / 14.5; FET 0.18 / 4.97 / 21.4; vias
  0.86 / 0.65 A), GND return 0.69 mOhm (DC_GND 0.1), supply paths equal to fix 1; scorecard index 15.3 (C2 93 -> 90);
  m2_sweep (29 track/via pairs, 10 at 0.150; 36 pad pairs, 4 fine); reference audit identical; requalify / pyro
  neighbours re-run; make_ground --built reproduces r8_ground.tsv; binding note regenerated; 272 tests + quality_audit 21
  OK; r8_fab.sh OK (CPL 25cfed69, only R81's row); check.sh standalone exit 0. Evidence step9/evidence/fix2_*.
- Records updated: R8_VALIDATION (review pass 2 section, part C C12/C12b/C15/C17/C19, E, F, pyro observations, owner
  summary, open items), M3_R8, R8_DECISIONS (D97-D105, D85/D87/D89/D6.8 corrections), ORDERING, REQUIREMENTS, STATUS,
  MARGIN, AGENTS, README. fix2_baseline_sha256.txt and fix2_generators.diff written. Scratch board copies deleted.
- DONE (not committed, per brief); handoff fix2_handoff.md.
