# Spike 3(c) battery band: progress log

Resume from the last entry. Brief: r8_plan §3 step 3(c): input protection at J1, the 7.7 A copper (RAW_ACT, BAT_IN,
ACT_FET_S) with In2 islands, rule H and DRC A-H intact, dc_solve at 0.1 mm and the D12 neck widths. Kill: strategy
C's battery corner. Work only here and in `$SCRATCH/r8_design/spike_c_battery/`.

## Log

1. Read r8_plan, step 0-2 handoffs, R8_DECISIONS D1-D28, plan_partial, plan_cleansheet (battery corner), survey
   constraints (rules A-H, CH1 block, F9). Seed: `partial/b0_place_final.tsv` (Q120 (29,103.9,0,B), Q121 (29,96.5,180,B)).
2. base.py (this folder) builds the scratch base: R7 + R8 netlist + rigid copper only + seed placement (rigid parts
   kept at R7's exact position; the seed TSV rounds to 0.01 mm). Scratch: `$SC/base/m3.kicad_pcb`. Note: in this
   KiCad build `BOARD.Remove` corrupts later SWIG proxies; use `BOARD.Delete`.
3. Finding: B's seed (Q121 under the CH1 block, In2 RAW_ACT plane under J122 and the block) is illegal under D18
   (In2 power >= 2.5 mm from BUS/IGN/OUT) and "In2 GND under pyro/servo lanes"; J122's RAW_ACT middle column is
   reachable on outer layers only from its forward end (x 19.6-25.1, y 80.4-86.4), boxed by the pyro exit lanes
   (west, B.Cu x 16.7-20), the servo lanes (east) and the tie hole. Chosen primary: "west chain" - FETs side by side
   in the forward band west of J1 (Q121 rot 270 at (8,103) drain west, Q120 rot 90 at (16.38,101.72) drain east),
   RAW_ACT down the west strip past J124 (x<=7.4 outer, <=6.0 In2) into a west region (J124.2, C121), an F.Cu-only
   bridge over the pyro corridor into the J122 box (F + B + In2 finger). ACT_GATE: 2-via F.Cu hop (gates sit at
   opposite corners of the facing-row bridge; In2 is power-only, D20).
4. fet_exp.py experiment (scratch): facing source rows, aligned (offset d = -1.28), pad-edge gap 1.5 mm
   (xb = xa + 8.38): ACT_FET_S neck 5.51 mm B.Cu, 19.1 C (gap 0.5 mm: 4.80 mm, 22.3 C). D12 needs >= 3.71 mm.
5. battery.py (this folder) + drc_filter.py + verify.py. Pitfall: the base keeps R7's stale fills, and
   BuildConnectivity re-nets new vias from them (RAW_ACT vias became GND) -> battery.py UnFill()s first.
   v1 (`$SC/v1`): DRC 0 on spike nets (one seed C8/C9 overlap outside the band's parts), 0 unconnected; route_check
   0 failures on spike nets (fixed a GND B.Cu finger between the CONT lane and the box: box west edge 19.65);
   rigid hashes 12/12 OK; D18 0 (nearest 2.65 mm BAT_IN In2 to R134.1); run_dc.sh 0.1 mm: RAW_ACT 1.48 mOhm, neck
   5.69 mm F.Cu 18.4 C; BAT_IN 0.37 mOhm, 8.25 mm B.Cu 12.0 C; ACT_FET_S 0.20 mOhm, 4.34 mm B.Cu 25.0 C. All D12 OK.
   Observation (not spike copper): D20 flags the rigid CH1 ARM1_SENSE In2 link (3.4 mm) - step-1 conflict.
6. Iterations v2-v4 (scratch): ACT_FET_S bridge extended aft past via B (neck 4.34 -> 4.77 mm); gate drive mirrored
   to the top side east of the ACT_GATE hop (RAW_PROTECTED reaches R122 from the east); reservation lanes for
   BAT_ENABLE / RAW_PROTECTED on the top strip (R166 raised to y 101.7, BAT_IN vias to x 21.25, D8/C80/C96 spread);
   F.Cu box raised to y 88.0 for x <= 21.3 and box vias from x 20.6 (RAW_ACT neck 5.69 -> 5.88 mm). A further step
   under R127 (6.17 mm) starved C127.2 / R127.2 thermals: reverted. KIID seed 8301 makes battery.py byte-identical.
   Guard added: battery.py asserts no via is re-netted by connectivity (caught a GND via in Q121's drain pad).
7. FINAL `$SC/final` (SHA 15e33b31c377ee15): DRC 0 / unconnected 0 on spike nets; route_check 0; rigid 12/12; D18 0
   (2.65 mm); M2/TP checks 0; check_actuators OK; fit OK; margins.py all rules met; run_dc 0.1 mm: RAW_ACT 1.44 mOhm
   5.88 mm 17.7 C, BAT_IN 0.40 mOhm 7.15 mm 14.1 C, ACT_FET_S 0.19 mOhm 4.77 mm 22.5 C. RESULT.md written.
   0.05 mm run in background (`$SC/final/dc05`): ACT_FET_S 4.97 mm 21.5 C; RAW_ACT / BAT_IN pending.
8. 0.05 mm (`$SC/final/dc05`): RAW_ACT 1.44 mOhm 5.93 mm 17.5 C; BAT_IN 0.41 mOhm 7.22 mm 14.0 C; ACT_FET_S 0.18 mOhm
   4.97 mm 21.5 C. RESULT.md final. SPIKE 3(c) COMPLETE: primary (adapted B battery band, "west chain") passed.
