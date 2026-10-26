# R9 review pass 1: fix agent progress log

Board at start: `fc3d5b34a4bfbaecfbcb44bdf8144c87015fc71be7accf48354f23410e8d0f51` (step 9/10).
Scratch: <scratch>/r9review/

## Session 1 (2026-10-25)

- Started; no earlier log. Reading the pass-1 reports and the build.
- Backup of the step-10 worktree state (325 changed / untracked files) in scratch `orig/worktree_before_fix1.tgz`.
- Checkers changed (stricter or deterministic only):
  - `tools/check_r9.py`: P-7b (U1's gate pin pad >= 0.5 mm from non-U1, non-GND copper; R9P1-PYRO-01 option);
    R-5 attribution to the nearest chain pad, sorted iteration (RF-03 / INTEGRITY-01); R-7 sides named east / west
    (RF-02 option); R-8 In1 GND sampled over U31's whole body (INTEGRITY-02); M-7 docstring (INTEGRITY-05).
  - `tools/pyro_probe.py`: sorted net names; closest pair = smallest (mm, labels) (INTEGRITY-01).
  - `tools/r9_extra_metrics.py` Z4 over every TP* pad; `tools/r9_scorecard.py` prefers it (REQUIREMENTS-02).
    Measured on fc3d5b34: Z4 = 2 (TP120's two RAW_ACT vias).
  - `tools/test_r9_check.py`: test_p7b_mcu_gate_pin, R-8 body notch, R-7 'GNSS west'. 5 targeted tests OK.
- Generators / tables changed:
  - `r9_rf.py`: W_TXEN = W_SIG (0.2); GRID (24.7, 10.45) -> (24.65, 10.45); GND_MODULE + R7's three U31 module-ground
    vias (+3.74, +1.27), (+1.27, -3.60), (-2.54, +3.60) (RF-01, ROUTING-01). `r9_route.py` WIDTHS drops 0.15.
  - `r9_route_imu_baro.py`: QSPI_IO2 east run on y 50.6 (PYRO-01).
  - `r9_power.py`: RAW_ACT_VIAS drops (29.6, 78.2), moves (31.0, 78.2) -> (31.5, 78.2) (ROUTING-02 option b: no via ring
    in TP120's opening, no 0.101 mm hole margin); RAW_ACT_F's 29.75 edge carried to y 76.6 (PLANES-01 neck); U9 limit comment.
  - `r9_pcb.py`: RELIEVE J122.3/6/9/12 (pad FULL -> inherited THT relief; POWER-04 preferred fix).
  - `r9_place.tsv` C98 -> (39.275, 64.2) rot 180 B (legaliser OK); `r9_route_power_ctl.py` USB_LIMITED end re-drawn
    (C98.1 1.94 mm of track from U11.7; POWER-01). C83: no cheap legal spot (seeds tried with the legaliser: north
    (11.45, 34.3) collides with V_D / USB_FAULT_N and the USB pair boxes V_D on F.Cu; west needs R7 / R9 moved, i.e. the
    CC1 knot) -> recorded, not moved. C82: recorded (TI 8.4.1 deviation as R8 did).
  - `r9_ground_aid.py`: legal(relax=BOX) for RAW_ACT only; CORRIDOR_EXCEPT {'C121.2': (34.55, 61.3, 35.75, 64.85)};
    final stage `copper`: (a) GND SMD pads of C/U/Q/J beyond 5 mm of copper, (b) copper beyond 8 mm (farthest legal
    spot in the same piece >= 2 mm out). `r9_ground_check.py`: stitch gate allows RAW_ACT corridor cuts only inside a
    CORRIDOR_EXCEPT box; new gate `copper` (pads <= 5, copper <= 8 mm or recorded exceptions).
- Records already edited (text only): FMEA (R9 I-4 / V-16 row), ORDERING (IGN-BUS1 adjacency, battery lead below the
  sled, sled forward end, foam off U4, staking limits at J30 / C121, mirrored-numbering DFM query + remark, C303 stub,
  coating paragraph), REQUIREMENTS (P2, R8 acceptance, M1 U4, M2 pours / K-legends / relief pointer / TP120, accepted
  risks, R9 acceptance wording), MARGIN R14 R9 clause.
- Staged build runner: scratch `stage_runner.sh START END` (replays r9_build.sh lines, saves stages/NN.kicad_pcb).
  Run 6..34 started 14:40.
- `sources/r9_review/fix1/fix1_measure.py` (module GND pin reach, via-ring openings, gate pads to GND fill, single vias,
  hardware, thin GND pieces, TP vias). On fc3d5b34: U31.2/7/16 1.154/1.095/1.05 mm; own-net ring-to-opening < 0.1 mm
  25 pairs at 22 vias (TP120's two 0.0 included); gate pads 0.151 mm from GND fill.

## Session 2 (2026-10-25, from 16:06)

- Resumed from the log. Verified every generator / tool change listed above against the backup (diffs as described).
- r9_power.py was saved at 14:42 after its stage ran: re-ran stage 13 on stage 12's board, output byte-identical to the
  saved 13.kicad_pcb (the later edit was the RP_VIAS comment only), so stages 14-34 stand.
- Worktree board restored to stage 34's (8b5b8249...; the step-7 board). Ground aid re-run on it (16:10) to regenerate
  the table with the copper stage (PLANES-01 / -02).
- Aid run 1 (16:10, 2 min): the copper stage's part (b) chose "the legal spot farthest along the copper in the same
  piece", but the outer F.Cu GND is one 8-connected piece, so it placed 12 vias far from the worst point. Rewritten:
  over-limit copper as 8-connected clusters (`over_clusters`), the via at the legal spot nearest the cluster's worst point
  along the copper (`rc.reach` from that point), candidates on the 0.05 mm lattice (a legal area can be smaller than a
  0.1 mm raster cell), cap 40 rounds; r9_ground_check `gate_copper` judges the same clusters (evidence `clusters_over`).
- Aid run 3 + stages 35-36: ground gate FAIL on two new weak islands: (1) B.Cu 1.34 mm2 sliver revived by the C121.2
  copper via (34.6, 61.5) between USB_LIMITED (y 60.72) and the RAW_ACT B pour; (2) F.Cu 0.86 mm2 piece between D120's
  3V3 lane (x 17.9) and J122's west column, joined only by one spoke to J122.3 once its pad took the THT relief (its
  ring closes the channel south). Fixes: aid `place_safe` (a copper-stage via must leave no new weak island; the next
  spot is tried); J122's relief reverted (r9_pcb.py restored; its RELIEVE kept in scratch aid/r9_pcb_relieve.py): the
  pins stay solid as R7 / R8, recorded as a C row with the relief trial's measured side effect (D-F1-06).
- C83: not moved (prior session's legaliser seeds; the VBUS-tee redraw would re-route the J3 / U10 / R9 knot); recorded.
- Stages 7-34 re-run from 16:40 (r9_pcb changed).
- Stages 7-34 re-run OK (16:31-16:51; every step gate passed: placement, RF, pyro, power, the ten route families).
- Aid v2 on stage 34 (16:52-16:57; scratch aid/aid_v2.log): every C121.2 spot inside the RAW_ACT B.Cu pour makes the via
  its own B.Cu island (a P7 pocket, like WEAK_EXCEPT's C150 entry), so place_safe rejected 60 spots and the pad stage
  logged "no legal spot"; the cluster stage then placed (35.6, 64.8) on the pour's east edge (joined to B.Cu GND), which
  serves C121.2 (1.50 mm of copper; was 16.10) and R103.2 (3.74; was 20.67). Copper rows: (35.6, 64.8), (32.9, 99.85)
  (the forward strip, PLANES-02), (41.4, 41.1). Table 187 rows (183 vias, 4 tracks), frozen as m3_design/r9_ground.tsv.
- Stage 36 first run: every ground gate OK but `copper` (the six logged clusters and J9.2 had no exception yet; islands
  OK with P7 9). Exceptions recorded in r9_ground_check.py (COPPER_PAD_EXCEPT J9.2 6.99; COPPER_EXCEPT six clusters,
  8.05-9.50 mm, layers under each measured); stages 36-39 re-run from 17:02; aid --check on a copy of stage 34 (with the
  project's pro / dru) in parallel.
- Final board `4f841a0e44ebb1829ad7996dfe6320ed527fce1fdb1e5ff11658e0705b44ac14` (stage replay 17:11); `tools/check.sh`
  exit 0 (stage 39 and a standalone run; the two check_r9 reports identical). Second build: `r9_build.sh` whole in a
  scratch clone (git clone --shared at 9c8179b + rsync), rc 0 in 45 min, every built file byte-identical.
- Evidence re-run on 4f841a0e into step10_evidence (D-F1-11): gate reports, 32 DC rows + 0.05 mm dc005 (survey),
  fire loop, requalify, tab plan, ORDERING facts, binding note, M2 sweep, reference audits, hot-plug, scorecard
  (34 met / 16 missed; index_r9 83.8), post report, build logs, fab (live JLC 2026-10-26 00:59Z: $109.38, 52 ext,
  U4 40), tests (478 in 26 suites OK; the first run failed test_fab_validation on the stale CPL and my new
  test_r9_ground test on a missing 'copper pad' row: the fab re-run and a test fix cured both), records check OK.
- Records: R9_VALIDATION (header, step table, done rows, requalification rows, the deviation list C1-C25 with R8's
  same-metric column, part D, "Review pass 1", Open), M3_R9, STATUS, REQUIREMENTS (F4, F10, M2, M3, P1), ORDERING,
  MARGIN P1-9, AGENTS, README, R9_DECISIONS (D-F1-01 ... D-F1-11 and corrections to D-S5-08, D-S6-05, D-S6-06, D-S8-20,
  D-S10-09, D-S10-11, D-S10-12, D-S10-14, D-S10-18), step-3 handoff; fix1_handoff.md written. Nothing committed.
- Scratch cleaned (2026-10-26 01:20Z): the clone, stage boards, aid / measurement / evidence working copies and run
  logs are deleted; kept `orig/worktree_before_fix1.tgz` (4 MB, the worktree before this pass) and the reviewers'
  `pyro/`, `planes/`, `skeptic_planes01_req/`. Every result the records cite is in `fix1/` or `step10_evidence/`.
  Board still `4f841a0e…`; nothing committed.
