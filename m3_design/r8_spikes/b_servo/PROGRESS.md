# Spike 3(b) servo bus: progress log

Running log so a successor can resume. Scratch: `$SCRATCH/r8_design/spike_b_servo/` (session scratchpad).

- Read: r8_plan §3 step 3, step 0–2 handoffs, R8_DECISIONS D7/D14/D15/D18/D19/D26, plan_partial §5.4, AGENTS.md,
  check_actuators rule 7, check_r8 rigid groups.
- Folder created.
- Geometry facts (seed U1 rot 0 at (23,45)): U1.22–25 SERVO1–4 at x 27.5/28.0/28.5/29.0, y 52.55 (forward face);
  J122 signal column x 25.54: SERVO1 y 79.51, SERVO2 76.97, SERVO3 74.43, SERVO4 71.89. Tie channel
  (21.5,68.6)->(27,82.6), 4 mm wide, bottom parts >= 2 mm (perpendicular) from its centre line.
- Topology: B.Cu D121 lands U1-ordered lanes (S1..S4 counter-clockwise, y-up view); both mid pins (2 GND, 5 3V3)
  always sit between lanes, so each takes a via. Chosen design "E" (matches D7's wording):
  F.Cu straight from each pin to its J122 row, 45 deg turn east, pull-down pad on the row, via at x 32.4;
  B.Cu row via -> R(149+i) (rot 180, x 30.2) -> J122 pin, crossing under the F.Cu lanes = the full reversal;
  D121 B.Cu rot 180 at (34.2, 75.70) tapped from the 4 vias (west fan-in); GND via N of pin 2, 3V3 via S of pin 5.
  In2 under rows/D121: 3V3 tongue (D121.5's via needs 3V3); RAW_ACT island only under J122's middle column.
- Next: scripts make_base.py (scratch board), servo_route.py (geometry), verify.py, run.sh.
- Scripts written: make_base.py, servo_route.py, verify.py, run.sh (scratch from git 431025d, ~6 s).
- Fixes on the way: pcbnew Remove() of zones breaks SWIG (use Delete()); save rewrites .kicad_pro (run.sh restores
  R7's); rigid parts must not be re-placed from the 0.01 mm-rounded seed TSV; tongue zone needs its own priority;
  fp-lib-table + kilib symlink for DRC; RAW_ACT_SENSE divider moved east keeping rule H.
- strip_gcpw: deleting R7's four F.Cu power pours together flips 13 GCPW samples by 0.01 mm (fill noise); kept them
  in the scratch base (R7_FCU_POURS); servo copper itself changes no digest (checked with the pours dropped too).
- Interface shifted +0.2 mm east (R column x 30.4) for tie-path margin (R150 2.20 mm).
- Default In2 = GND under the rows, 3V3 tongue only under D121 (r8_plan §1); full-tongue variant also passes.
- DONE: primary approach passes (rigid hashes, DRC 0 on spike items, route_check 0 on spike nets, check_actuators OK,
  byte-identical rebuild 96c48e02...). RESULT.md and result_summary.json written. Scratch cleaned.
