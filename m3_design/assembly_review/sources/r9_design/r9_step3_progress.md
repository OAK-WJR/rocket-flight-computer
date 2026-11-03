# R9 step 3 (placement freeze): progress log

Brief: r9_plan.md §4 step 3. Build m3_design/r9_legalise.py and m3_design/r9_place.tsv (aft cluster U1/U3/U4/U5/R10
first) and the fresh-board start of m3_design/r9_build.sh / r9_pcb.py (new 46 x 98 mm outline, five supports per P2
with the mid support per owner decision 5, parts placed from the table). Verify: 0 legaliser violations over all parts;
fit_check; the plate model (f1); F9 input-protection distance; F10 5 mm separations; the strict pad rules; J1 within
25 mm of both CH1 terminals; tab windows; MST <= 1639 mm. Kill: if 98 mm cannot legalise, 100 then 102 mm, recorded.

Handoffs of steps 1 and 2 read. No step-3 log existed at start: fresh start.

## Plan

1. [x] Dump R8 placement data (positions, courtyards, pads) and the spine prototype / S98 model positions.
2. [x] m3_design/r9_legalise.py: r8_legalise generalised to R9's DRU and rules (outline / holes / tie holes derived,
       rule G P-1b scope, RAW_ACT pin and test-pad rules, strict pad rules, P-3 hull purity for pads, R-1 strip, F10
       5.94 / 5.0, M-5 support floors, P-10 coat keep-offs, J1 front corridor).
3. [x] m3_design/r9_pcb.py: R8 board -> variants, overrides cleared, all copper / zones / old outline gone, the 46 x L
       outline, five supports, J122 tie holes, placement from r9_place.tsv, PYRO_BLOCK derived, native fill, save.
4. [x] m3_design/r9_place.tsv: aft cluster first, then RF strip, forward half; iterate to 0 violations.
5. [x] m3_design/r9_place_check.py: the step gate (legaliser, DRC + parity, fit, plate f1, F9-1, R-10, strict pad
       rules / P-5 / P-6, M-4, T-1, MST, check_r9 placement rules, check_actuators).
6. [x] r9_build.sh stages; reproducibility (two builds, same SHA); R9_DECISIONS D-S3-*; handoff.

## Log
- Tools drafted: m3_design/r9_legalise.py (R8 legaliser generalised: outline / supports / tie holes read from the board,
  R9 DRU clearances incl. rule G P-1b scope, RAW_ACT PTH 0.3, TP 1.0, strict pad rules H+/GS/AG, P-6, P-5 classes,
  R-1, R-10 (5.94 / 5.0), M-5 support floors 4.452 / 5.008 and fit floors, M-6 bottom keep-outs, M-3 tie channel, P-3
  pad purity, P-10 coat region on the derived PYRO_BLOCK, M-4 J1 front corridor; block_area() derives PYRO_BLOCK),
  m3_design/r9_pcb.py (R8 board -> variants, LC-1, netlist check (761 pads, 0 changed), clean sheet, outline / holes
  from '@' rows, placement, PYRO_BLOCK, fill, save; --draft / --out / --propose). Seed table (scratch: R8 strip,
  prototype forward half, R8 U1 block -5/-5.5, S98 model for the rest) runs end to end: 121 parts illegal (expected).
- Renderer (scratch step3/plot.py via geo_dump.py, cfd venv matplotlib) for top / bottom views.
- FINDING 1 (feasibility, needs the owner): the four MCU-end interface resistors R306, R313, R315 (series) and R310
  (NSS pull) are RF parts (F10 R8 note; RF_PART regex), so R-10 keeps them >= 5.94 mm (courtyards) from U1 / U3 / Y1
  and >= 5.0 mm from fast pads, while K-contract SERIES / PULL_END wants each nearer U1's centre than its module's
  centre. U1's centre lies 8.595 mm inside its courtyard, so on any lane between U1 and the strip a resistor sits
  >= 14.95 mm from U1's centre; U31's centre (29.86, 14.0) and U30's (~10.4-11.0, 14.05) are nearer than that to every
  natural spot at the strip mouth. Calc (polygon courtyards): natural lanes need U1's centre at y >= 42.2 for R306
  and >= ~44.5-45.3 for R313 / R315 / R310 (plan: 39.5) -> a ~104 mm board (beyond the 98 / 100 / 102 kill path);
  within 98 mm only U-turn placements are legal (radio resistors east of U1 at x >= 33, y >= 31.5; R306 in an east
  bulge of the GNSS bus at x >= 21.7), i.e. long, detoured interface lanes. Prior plans' models never applied SERIES.
- FINDING 2 (first note; superseded below, D-S3-04): y_f 22.0 vs R-12 (C301 <= 2.18, C300 <= 3.02 mm from U30's VCC pins) vs
  R-1. With polygon courtyards the GNSS decoupling fits forward of U30 only with U30 0.9 mm aft (y 14.05); that kills
  R8's LNA_EN / VCC_RF escape-via row west of the line, so the GNSS chain is R7's mirrored (shunts and tap east of the
  jack line, module line west; C305 west of the short module segment), congruent by reflection. U30.18's exposed pad
  then needs the aft-west support at (4, 3.5) (M-5 top floor 5.008); T-1 (west aft-third tab) needs U30's courtyard
  >= 5 mm from the west edge -> U30 x >= 11.0.
- FINDING 1, measured (supersedes the ~104 mm estimate above): m3_design/r9_kill_path.py rebuilds the table at each
  length and searches top-side, lane-ordered spots legal under the gate's legaliser with SERIES / PULL_END margin
  >= 0.25 mm, 0.2 mm R-10 slack and <= 6 mm lane detour: 98 mm no R306 spot; 100 mm no lane-ordered arrangement;
  101 mm holds (5.53 mm); 102 mm holds (2.62 mm). Kill path (r9_plan "if 98 fails, go to 100"; owner decision 1
  "fallback 100 / 102"): 102 mm (D-S3-03). Bottom-side / out-of-order spots legal at 98 / 100 need crossing lanes or
  layer hops on critical nets (M2). Owner option recorded, not a blocker: at 98 mm only R-10 between the four MCU-end
  resistors and U1 / U3 / U7 / C76 fails; with them outside F10's RF-part list the legaliser reports 0.
- FINDING 2, resolved within owner decision 3 (y_f 22.0): an in-memory study showed the GNSS row fits forward of U30
  with U30 at (11.15, 14.05): R305 / R307 / C300 / C301 / FB30 in one band in U30's pin order (planar), C301 2.13 and
  C300 2.556 mm from the VCC pins, U30.18 5.012 mm from the (4, 4) support; FB31 turned forward of U31. Moving J30 and
  the chain east with U30 failed R-11 (14.71 < 15.0 mm), so they keep R8's place (D-S3-04). An intermediate note that
  y_f 22.0 needed the owner was wrong and was not acted on.
- Built: r9_place.tsv (102 mm), r9_build.sh step-3 stages; two builds byte-identical (board 349c1477...); step gate
  r9_place_check OK on the built board (legaliser 0 / 249, DRC + parity 0, fit, f1 252.1 Hz, F9, F10, pyro pads,
  M-4, T-1, MST 1468.0 mm, contract, check_actuators, areas).
- Tests: tools/test_r9_place.py (18, seeded defects per rule); R8-era suites read R8's committed board through
  tools/r8_record.py (they failed only because the worktree board is now R9's). Evidence in step3_evidence/.

