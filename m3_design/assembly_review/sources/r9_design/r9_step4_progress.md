# R9 step 4 (RF strip): progress log

Step 4 of `r9_plan.md` §4: `m3_design/r9_rf.py`, the RF chains, modules and jacks by template, the strip boundary
y ≤ 22.0, the limiter on B.Cu under U30 with the shunts east of the GNSS line, fence and stitching. Verify R-1 … R-13,
launch congruence, GCPW 50 ± 2.5 Ω at every sample, no allowlist entry.

## Session 1

- Read r9_plan, owner decisions, step 1–3 handoffs, survey §8, check_r9 R-rules, R8's strip copper
  (`r8_route_rf.py`, R8 board dump), F10.
- Scratch: `…/scratchpad/s4/` (R8 board copy, dumps, renders), tools in `…/scratchpad/s4tools/`
  (geo_export.py / geo_plot.py: matplotlib renders from the cfd venv).

### Finding 1: the step-3 strip placement cannot take an R7-congruent GNSS chain and straight limiter escapes

U30 sits 0.9 mm aft and 0.74 mm east of R8 (D-S3-04): U30.11 (RF_IN) at (14.45, 9.3), pads y 8.4–10.2, u-blox
T-shaped paste to y 7.8. R7's chain (rows D30 y 5.2, L30 y 6.18, pi row C303–R304–C305 y 7.13, pads to 7.40) puts one
pi shunt west of the line in the pi row whichever way R304 jogs:
- R7 orientation translated (+0.74): C303 pads x 11.56–12.90 at y 6.86–7.40, right under U30.13 (LNA_EN, x 12.25);
- mirrored: C305 pads x 12.42–13.76, under U30.12 / U30.13.
A limiter via straight aft of pin 13 must sit at y ≤ 7.55 (via_paste: ring off the paste) and ≥ 7.80 (0.15 mm from
the pi-row pads): no spot. U30 cannot move forward (C300's 1.49 mm courtyard needs U30's courtyard top ≤ 20.51 for
y_f 22.0) or west (M-5: U30.18 4.70 mm from the (4, 4) support against 5.008).
Also R-11 (GNSS RF to radio RF copper ≥ 15.0): the translated chain puts C305.1 at x 15.64 (edge) against the radio's
C313.1 at 30.35: 14.71 mm (step 3 measured the same).

Design taken (D-S4-01, D-S4-02): GNSS chain "E+": R7's chain translated +0.74 mm (J30 x 13.59, R304 jog east onto
U30.11), with the pi's antenna-side shunt C303 moved to the east side of the line at the bias-tap row (stub 0.94 from
L30's line pad, the same node GNSS_RF_ANT): every pi shunt east of the line, nothing west of the line above the L30 row,
so LNA_EN / VCC_RF drop straight aft to vias at y 7.4. Radio: the whole radio group translated east (U31, J31, its chain
and module parts) for R-11 margin.

### Finding 2: R-7 (2.5 mm side stitching) decides the GNSS chain's sides

R7's rows (D30 5.2, L30 6.18, pi 7.13) are courtyard-packed (D30 abuts J30's courtyard), U30's pads end at y 8.4,
so the line (4.86 mm with R304's jog) needs a GND via on each side in the middle of the chain. With R304 jogging east
the pi row's east side is taken (R304.2, C305); a bias-row element on the east would leave the east side 3.5 mm without
a via. So: L30's cold end west (R7), C303 at the bias row on the east turned 90 degrees with its GND end aft (a via
fits beyond it at offset 1.75), D30 turned 180 (GND pad west: the east row-1 spot stays free; a west via still fits
beyond D30.2). Measured: GNSS side gaps 2.38 / 1.75, radio 1.70 / 2.41 mm (limit 2.5).

### Finding 3: the limiter cluster

Vias V1 (VCC_RF, 45-degree escape to (10.4, 7.4)), V3 (ANT_DC, (11.3, 7.4), fed from C302.1), V2 (LNA_EN, straight
aft (12.25, 7.4)) in that order west to east, so the B.Cu cluster is planar with each net entering at the pad nearest
its via: R300 west of V1 at the via row, Q30 (rotation -90, drain aft) straight forward of V3, R303 / Q31 east of V2.
Detour check (route_check, profile r9): no instance.

### Session 1, later: integration and verification

- Grid redone as a regular 2.5 mm rectangular lattice (118 vias + patches, `m3_design/r9_rf_aid.py`, which reproduces
  the frozen table exactly); vias kept 0.5 mm from the holes (copper_edge_clearance), out of the launch windows and
  the corridors; corridor entries at U31's west pads narrowed to a lane and its clearance (vias between pad rows).
- C301.2 boxed (one-spoke thermal): own 0.3 mm lead to a GND via north of it (thermal_policy keeps the pad THERMAL).
- 3V3_GNSS staircase removed: pins 7 / 8 joined under their T-paste (y 19.95), C300 off pin 7 by one 45-degree run.
- LNA_EN tiny jog removed (R303.1 -> 0.52 mm north -> 45 degrees to Q31.G; Q31 at x 14.38), C304 moved off the gate
  trunk (0.5 mm stub), Q30's drain lead 0.40 mm.
- Launch vias at R7's built y 3.58 (0.6 mm rings clear the 4.15 pair); radio (+1.25, 4.75) via dropped.
- Repo: r9_place.tsv (28 strip rows), r9_build.sh (step-4 stages), r9_rf.py, r9_rf_check.py, r9_rf_aid.py,
  tools/test_r9_rf.py; decisions D-S4-01 … 08; handoff written.
- Verified: build twice byte-identical (board 50a5af67…), step-3 gate OK in the build, step-4 gate OK, 21 suites / 378
  tests OK, quality_audit 21 OK; full check_r9 fails only P-4 / M-2 (inputs not passed), K-contract route-only items
  and K-legends (later steps).
- Scratch boards deleted (renders and logs kept in `…/scratchpad/s4/`).

## Done
