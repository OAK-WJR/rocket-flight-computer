# R9 step 5 (pyro block): progress log

Step 5 of `r9_plan.md` §4: `m3_design/r9_pyro.py`, the CH1 column pad-referenced (terminals, Q124, R134 bars, gate
network with a GND guard beside GATE_N, the dividers, the 4.7 kΩ at the MCU end, TP122 with a GND partner via).
Verify: pyro_probe margins (every A–H / A2 margin ≥ max(R8, 0.2 mm)), bridge table with no fires-class bridge under
1.5 mm, rule H seeded suite live, every GATE_N neighbour GND or ≤ 0.2 V in reset, coating region, wire room,
check_actuators, P-1b / P-3 / P-7.

## Session 1

- No step-5 log existed: fresh start. Read r9_plan, owner decisions, step 1–4 handoffs, R9_DECISIONS, survey §9,
  plan_spine §1–5 / §10, plan_flowline §7, the spine / flowline prototypes, check_r9 P-rules, pyro_probe, bridge_table,
  rule_h_seed, r9_rf.py (builder style), route_check categories.
- Scratch: `…/scratchpad/s5/` (renders, dumps), tools `…/scratchpad/s5tools/` (geo_export / geo_plot from s4, pads.py).

### Findings on the step-3 placement (before any copper)

1. **ARM1_SENSE has no east corridor.** The lane must pass J122's east end: rule A + 0.2 mm margin to J122.11
   (RAW_ACT) needs the lane centre at x ≥ 28.41; the east tie hole (29.9, 59) needs x ≤ 27.95 there, and C121's GND
   pad (x ≥ 28.295 at y 66–67.2) blocks x > 28.05. A 45° dogleg between the disks clears J122.10 by 0.04 mm only.
   West of J122 the lane would cross the servo fan and the CH1 block. Fix (placement): east tie hole to (30.6, 59)
   (M-3 holds), C92 / TP91 0.6 / 0.5 mm east to clear it, C121 0.6 mm east; the lane runs straight at x 28.53.
   (Final, after the edge clearance of 0.5 mm and M-5 were measured: hole (30.8, 59), C92 / TP91 0.9 / 1.1 mm east, C121
   turned 90 degrees instead of moved; see the log.)
2. **R170 on the bottom forces two ARM vias** (and M-6 keeps every ARM via ≥ 1.0 mm from R170 / R177 / C15 / C90:
   no legal spot found by hand). On the top at (28.1, 47.0) rot 180 the whole ARM1_SENSE path is F.Cu with no via;
   R170.2 must stay ≥ 1.0 mm from U1.34 (P-5: RAW_ACT_SENSE_MCU on ARM1_SENSE_MCU is forbidden < 1.0 mm), so x 28.1.
3. **Rule C margins on the 0402 dividers:** a track ending at an 0402 pad's centre comes 0.477 mm (w 0.2) from the
   part's other pad; rule C + 0.2 needs 0.5. Tracks enter R132.1, R173.1, R131.1 / R131.2, R173.2 from their outer
   ends and end 0.1 mm past the centre, outward.
4. **COLD route:** R131 as placed (OUT north, COLD south) sends COLD back past its own OUT pad; R131 rot 0 (OUT west,
   COLD east) with D120 on its 45° line gives one straight COLD run.
5. **R128.1 (GATE) to C127.1 (CONT) 1.48 mm** is a fires-class bridge (0.41 V on the gate in reset) under the step's
   1.5 mm: the CONT row moves 0.2 mm east.
6. **D120's 3V3** can only leave the block on F.Cu through J122's west end (P-3: In1 / In2 GND only in the hull);
   the west tie hole leaves a 0.04 mm window there: hole to (15.4, 62) (M-3 holds) gives a lane at x 17.67.
   (Final: (15.6, 62) with the lane at x 17.9, since R178.1 needs 0.5 mm to the hole's edge; see the log.)

## Plan

1. [x] Placement edits in r9_place.tsv (findings 1–6), legaliser and step-3 / step-4 gates still pass.
2. [x] m3_design/r9_pyro.py (pad-referenced copper) + build stage.
3. [x] m3_design/r9_pyro_check.py (step gate) + build stage.
4. [x] Iterate to all margins; route_check on the step's nets.
5. [x] tools/test_r9_pyro.py (seeded defects), reproducibility (two builds), decisions D-S5-*, handoff.

## Log

- Placement (r9_place.tsv, each row's basis names its D-S5): east tie hole (30.8, 59), C92 / TP91 east, C121 turned 90
  (moving it east broke M-5's support top floor: 4.539 < 5.008), U13 0.5 east, R170 top (28.1, 47.0) rot 180, the gate
  and CONT rows on y 61.23, the CONT / COLD cluster (R129, R173, R131 rot 0, D120), C128 on the drain tab line, C129,
  west tie hole (15.6, 62), TP122 (7.58, 63.5). Legaliser clean; the step-3 gate passes.
- r9_pyro.py: pad-referenced template (every point from pad centres / boxes; alignments asserted). First draws found:
  rule D margin 0.16 (OUT bar ending at the drain centre: cap 0.66 from the sources) -> the bar ends 0.6 mm inside the
  drain's forward edge; rule G 0.253 at U1's pins because block_area pulled PYRO_BLOCK out along GATE_N's bounding box
  -> r9_legalise.block_area counts exit copper only within 15b's reach (D-S5-11); C128's branch beside the land's tab
  was an overlap-only joint (the AON7524 land is a custom pad) -> C128 on the tab line; float via coordinates gave
  track_not_centered_on_via -> rounded.
- Gate r9_pyro_check.py: template, margins (floors max(R8, 0.2)), bridges (fires-class >= 1.5), rule_h, gate_n
  (1.5 mm), sense, armed (X2), contract, actuators, DRC, route (pending only the step's GND / 3V3 items).
- Found by the gate's evidence and fixed: ARM lane 0.52 mm from U13's CAM_5V pad (U13 east), D120's 3V3 lane 0.4 mm
  from D120.1 (now drops to D120.1's line first, 0.73) and 2.75 mm from R131.1 (X2b; R131 / D120 west / forward: none
  within 3 mm now).
- DRU fill margins (D-S5-12): r9_dru.py, check_actuators DRU_SHA, check_r9 CHECK_ACTUATORS_SHA, r9_sch_check's
  fill-equivalence (without_fill), test_r9_sch. Verified live: GND pour 0.751 mm from armed copper with, 0.501 without.
- One exception recorded (D-S5-13): rule G margin 0.112 at U1.3's entry against the no-net sentinel pins (geometry).
- tools/test_r9_pyro.py 19 tests; test_r9_rf's drawn-nets test reads the step-4 tables (D-S5-15).
- Verified: r9_build.sh twice, every file byte-identical (board a6454f78…); all four step gates OK in the build; 22
  suites / 398 tests OK; quality_audit 21 OK under both pythons; audit_artifacts exit 0; full check_r9 fails only M-2
  (plate input not passed), K-contract's route-only items and K-legends (later steps). Evidence: step5_evidence/.
- Scratch boards deleted (renders and logs kept in …/scratchpad/s5/).

## Done
