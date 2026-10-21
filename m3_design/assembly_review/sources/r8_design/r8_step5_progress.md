# R8 step 5 progress log: power

Running log so a successor can resume. Newest entries at the bottom. Scratch: `$SCRATCH/r8_step5/` (session
scratchpad).

## 2026-10-19 start
- Read r8_plan, step 0/1/2/4 handoffs (no step-3 handoff; spike RESULT.md files are the step-3 record), R8_DECISIONS
  D1-D39, spike (c) RESULT/battery.py, make_keepclear.py, r8_pcb.py, r8_build.sh, check_r8 / check_r7 strip checks.
- Board at start: step 4's placement board, SHA-256 40e516fa... (r8_build.sh output).

## Placement amendments for the power stages (r8_place.tsv; to record as D40-D42)
- Finding: step 4's buck placements do not follow the makers' layouts. 3V3 buck: U2's VIN/GND end faced L1 (no room for
  the input cap), C6/C7 4 mm away, C5 (BST) on the far side of the package. Camera buck: L3's SW pad was the far end
  (8.5 mm SW path past its own 5V pad), Cin C72 not across VIN/GND, C74's pads crossed (BST vs SW).
- Datasheets read (session scratchpad ds/): Diodes DS41326 Rev 3-2 (AP63203) Layout + Figure 25; DS42002 Rev 3-2
  (AP63301) Layout items 2-9 + Figure 39 (item 6: 2nd and 3rd layers GND); TI SLVSEA3F (TPS2121) 12.1; SLVSFC9C
  (TPS25947) 8.4.1; TPS2595 11.1; TPS2553 12.1.
- D40 3V3 buck: U2 rot 90 at (37.95, 66.6): SW east 0.6 mm from L1.1, VIN/GND aft; C6 across VIN/GND (0.8 mm straps),
  C7 vertical west of U2, C5 forward between BST and L1.1, Cout C8/C9 aft of L1 on its 3V3 end; TP83 west.
- D41 camera buck: U8 rot -90 at (39.95, 34.95) (SW forward), L3 rot -90 moved to (39.95, 40.82) forward of U8 (SW strap
  1.0 mm), C72 vertical across VIN/GND at U8's east end, C73 aft of it (VIN pads adjacent), C74 west at BST, C75 forward
  of L3's 5V pad, C76 west of it, feedback network R71/R72/C77 on the top above U8 (FB via west of U8); TP71/TP72/R78
  re-homed; camera-wire TP75/TP76 to the top beside R100/R101/J9 (bottom had no legal spot with the 1.0 mm TP rule).
- D42 mux U11 rot 90: IN2 (USB_LIMITED) south-west, IN1 (RAW_PROTECTED) north-west, OUT north-east; C98 on the IN2 feed,
  R87/R88 west at OVLO, C97 at IN1, C99 on OUT, R86/C85/R91 east at ILIM/SS/ST, TP87 east.
- USB_LIMITED route (power, step 5): B.Cu U10.6 -> y 37.25 under U1's aft pad row -> x 30.0 north -> F.Cu hop y 54.6
  over the RAS lane -> via (35.25, 54.6) -> C98.1 -> U11.7. ~42 mm, 2 vias (step 4 handoff left it open).
- Trial pipeline: $SCRATCH/r8_step5/trial.sh TABLE --gate (fresh R7 copy in $SCRATCH/r8_step5/proj, r8_pcb --draft,
  r8_place_check). Final trial t4: all 11 placement gates OK, MST 1601.5 mm (step 4: 1632.5), fit/tabs/F10 unchanged.
- r8_place.tsv updated (backup of step 4's table: $SCRATCH/r8_step5/r8_place_step4.tsv).
- More placement nudges for straight power copper (r8_place.tsv, all placement gates OK): C120 y 106.46 (gate bus on
  R120.2 at y 107.16), C88 x 41.67 (BAT_IN feed through C88.1's centre), C6 x 37.75 / C99 x 37.17 (VLOGIC column
  x 36.75 through C99.1, C6.1, U2.3, U2.2), C7 (34.75, 64.4), C97 rot 180 (34.55, 61.6) (RAW_PROTECTED pad by the IN1
  via), R87/R88 x 32.2, C5 (39.57, 69.4) (BST straight north of U2.6), C74 (36.1, 36.83) (BST straight west of U8.6,
  SW straight east into L3.1), C76 y 40.66, TP71 on the CAM_INPUT_LIMITED line (36.6, 31.65), TP72 (44.2, 43.17),
  R78 rot 180 (35.5, 45.2), C90 (35.6, 52.9), C10/C11 rot 180 at x 23.025 (3V3A column x 24.025 through R164.2),
  TP87 (44.75, 57.7).
- r8_power.py started (In2 + band port): DRC clean on the band (only the expected via_dangling and the then-unfed
  3V3 In2 zone).
- Scope decision (to record): step 5 = In2, 7.7 A, via fields, supply trunks and power stages (RAW_PROTECTED, VLOGIC,
  3V3 buck + 3V3 out to In2, USB_LIMITED, 3V3A trunk + corridor hop, U1 decoupling of spike a, camera eFuse power
  path, camera buck, CAM_5V to J9.1, feedback); family-local power inside signal clusters (VBUS at J3/D4/U10, the
  sensors' 3V3A, U13 LDO cluster, pull-up/bypass 3V3 taps over In2 3V3, eFuse/mux control pins) -> step 6 families.

## Power copper finished, gate, build integration
- route_check fixes on r8_power.py: one CAM_5V via (40.75, 41.4); VLOGIC 45° into C99.1 and one via to C84.1 (no loop),
  on to TP83 (33.0, 67.75); R122's segment to the trunk 0.25 mm; 3V3 output diagonal off L1.2; R91 rot 90 at
  (44.3, 58.8) straight under C9.1, TP87 (42.0, 58.5); C72's GND via straight; L1.2 pour trim (B.Cu rule area).
- RAW_PROTECTED without its B.Cu pour (D46): column x 41.75 under U9.6 (0.3 mm out of the pad, then 0.5), D9 / C82
  branches, 45° into TP81; R92 on the top (43.3, 82.6) (D46). C7 (34.75, 64.65) so C7.1 is on the VLOGIC branch.
  A straight diagonal for R122's lane was tried and shorted R123.1 / cleared a BAT_IN via by less than the rule: kept
  spike (c)'s lane (extra_bends, information).
- make_keepclear.py: D45 chamfer; BUILT_BOARD filter (D48): 510 -> 324 rows. Its overlay found C76.2's GND via on
  RADIO_NRST (moved to (34.4, 38.27)) and the 3V3 spine across D121.2's GND via (spine steps to x 35.2).
- In2 GND outline = board minus the other regions (no GND rings round vias in them: 17 -> 1 islands). Note: ZONE.
  SetOutline() with a Python-made poly set corrupted the zone (fill became one 14 mm² island); subtracting in place on
  z.Outline() works. J122 finger forward edge 86.4 -> 86.2 (0.5 mm plan view from C127's pads).
- New gate m3_design/r8_power_check.py (rigid, drc, complete, pyro, inner, in2, route, reserved + stale rows); tests
  tools/test_r8_power.py (7 seeded defects, OK); r8_build.sh appends r8_power.py + the gate.
- Build twice: identical, board SHA-256 907e689a7762bbeb...; all gates OK; test_r8_place / r8_check / route_check /
  fit_check / check_shell / r7_check OK.
- DC 0.1 mm (final board): RAW_ACT 5.89 mm F.Cu 17.7 C, 1.44 mOhm; BAT_IN 6.87 mm B.Cu 14.8 C, 0.41 mOhm; ACT_FET_S
  4.78 mm B.Cu 22.5 C, 0.19 mOhm. Path R (0.1 mm): RAW_PROTECTED U9->U11 47.3, U9->U7 76.3, U9->TP81 9.8; VLOGIC
  C84->U2 3.0, U11->C99 1.9; USB_LIMITED 55.1; CAM_5V L3->J9 2.7; BAT_IN J1->U9 17.3 mOhm. 0.05 mm running.
- Decisions D40-D48 written; D49 (verification figures) after the 0.05 mm solve.

## Feasibility of the U9 / U11 status lanes (D50), final figures
- Found while writing the handoff: step 4's suggested BAT_FAULT_N path (F.Cu x 43.0) crosses RAW_PROTECTED's U11
  branch (y 62.6) and the 3V3 line (y 82.0); every other way was walled by step-5 copper. Fix: USB_LIMITED's F.Cu hop
  shortened to one 45° over the RAS lane (via (31.25, 55.3), B.Cu y 55.3 into C98.1), then BAT_FAULT_N (B.Cu under the
  3V3 line, F.Cu x 33.6 to pin 28) and LOGIC_SOURCE_ST (B.Cu y 57.27, via (38.6, 57.27), F.Cu to pin 29) reserved as
  family s5 in make_keepclear (343 rows); overlay clean, placement gate clean.
- 0.05 mm DC: RAW_ACT 5.93 mm F.Cu 17.5 C 1.44 mOhm; BAT_IN 7.00 mm B.Cu 14.5 C 0.41; ACT_FET_S 4.97 mm B.Cu 21.5 C
  0.18. The snapshot's 7.7 A geometry digest equals the final board's (only USB_LIMITED changed after it).
- USB_LIMITED path 52.6 mOhm after the change; 3V3 L1 -> U1.75 15.6 mOhm.
- Final board SHA-256 1818b05f43af53ec...; builds 4-7 identical; all test suites OK; check_r8 21 later-step findings.
- Decisions D40-D50 and the handoff written.
