# R7 pass 8: board-wide regression and electrical integrity (fix pass 7)

Read-only review, 2026-10-18. Dimension: every copper and silkscreen change of fix pass 7 (agent F8,
`m3_design/r7_polish.py` stages `bumps7`, `v3pair7`, `acten7`, `arm1_7`, `tidy7`, `sense7`, `bat_via7`, `v3a_hop7`,
`bat_in_b7`, `dup7`, `review7`, `necks7`; `m3_design/r7_post.py` `label_near`), judged against the pass-7 board.
Focus:
- the 7.7 A neck widening and the IPC-2152 / DC figures;
- BAT_IN and ACT_EN;
- ground returns and critical-reference sampling;
- power feeds;
- actuator and pyro rules and the arming break;
- legends next to their subjects;
- parity;
- the fab package's binding to the board.

| Item | Value |
|---|---|
| Final board | `m3_design/assembly_review/m3.kicad_pcb`, SHA-256 `c872a3d30509cccf5f78b64cde48ef722ee85c7be23c4848b07ce4082a852de3`. It matches `fix7_F8_handoff.md`, M3_R7, R7_VALIDATION and the fab manifest (`inputs_sha256/cad/m3.kicad_pcb`). It was the same before and after the gate and the tests |
| Pass-7 board ("base") | SHA-256 `4673c0a0f9fd290af694d6ca5a97e99b3b225466882ba5c6e57a9ad856b96ebd` (F8's start copy `scratchpad/f8/sb/m3.kicad_pcb`, SHA re-checked; same `.kicad_pro` and `.kicad_dru` as the final board) |
| R6 board | `git show 3b215ba:m3_design/assembly_review/m3.kicad_pcb` (SHA `184a87e8…`), compared moved +18 mm in y |
| Schematic / rules | Unchanged since fix pass 6: `telemetry.kicad_sch` `f5e1df83…`, `m3.kicad_sch` `47057f7d…`, `m3.kicad_dru` `1674d58b…`; `schematic.net.xml` (`a9095ac4…`), and every `.kicad_sch`, were last written at 07:43 today, before F8 started. `m3.kicad_pro` is identical to the base copy |
| Gate (rerun here) | `tools/check.sh` exit 0. DRC 0, unconnected 0, parity 0, ERC 0. Audit OK; silk 0; R7 contract OK (with `legend_subjects`). Routing hygiene: 0 failing, 45 allowlisted, 0 stale, 29 leftovers recorded, 1 removable local bump (A48, allowlisted). Actuator contract OK; fit OK |
| Tests (rerun here, KiCad Python, from `tools/`) | test_r7_check 35 OK, test_route_check 50 OK, test_fab_validation 23 OK, test_dc_solve 3 OK. `git status --short` was identical before and after (87 lines) |
| Tools | KiCad 10.0.6 `pcbnew` read-only scripts on SHA-checked copies in `scratchpad/p8reg/`: `dump.py` / `diff.py` (full item diff); `gaps.py` (every new track and via against every other-net track, via, pad and fill, all neighbours ≤ 0.5 mm); `pairs.py` (per-layer minimum gap between safety net pairs); `zoneneigh.py`; `gndpieces.py` / `piece.py` (GND pour pieces and what each touches); `silk.py` / `desig.py` (legend ink against courtyards); `dc_via.py` (= `tools/dc_solve.py` plus per-via barrel currents) and `dc_gnd.py` (the same at a coarse grid for the GND net). Also `tools/critical_reference.py`, `tools/dc_solve.py`, `tools/fab_manifest.py` and `kicad-cli pcb export gerbers/drill` (scratch output) |
| Fills | The saved fills throughout (the build fills natively) |

## 1. Summary

**No Critical and no Major findings.** Fix pass 7 changed what `fix7_F8_handoff.md` says it changed and nothing
else (§4.1). All three pass-7 findings in this dimension are closed or properly dispositioned (§2). The DC, neck and
IPC-2152 figures in the records reproduce.

What holds:
- **Netlist, parts, rules.**
  - All 819 pads keep their net, position, size and zone connection.
  - No footprint moved. Only designator visibility and position changed: C151, R157 and TP88 are now shown; R121,
    R123 and U13 are now hidden; C70, C86, C91, J124, R122, R72, TH2 and TP121 have moved designators.
  - Parity 0, ERC 0; the schematic and `m3.kicad_dru` are unchanged.
- **Copper changed on 14 nets**, every one named in the handoff (§4.1):
  - tracks 1,747 → 1,724 (66 removed, 43 added);
  - vias 708 → 710 (−3V3 1, −ACT_EN 2, −GND 1; BAT_IN −1 +7);
  - zone outlines changed on BAT_IN_B and ACT_FET_S_B, plus one added pour trim (B.Cu 35.84–38.66, 75.08–77.10, at
    the 3V3A hop). The other trims are renumbered with identical outlines.
- **Pass-7 regression items.**
  - BAT_IN_B is back to one 70.85 mm² piece with its fill's east edge at x 12.45. Its foreign neighbours are again
    only RAW_ACT (J124.2), BUZZ_DRV, BUZZ_G and the TH2 hole.
  - The B.Cu gaps that pass 7 raised are restored: BAT_IN to ARM1_SENSE 0.654 → 1.800 mm, and BAT_IN to USB_ILIM
    0.300 → 2.600 mm.
  - BAT_IN to 3V3 on B.Cu is 0.301 → 1.429 mm.
  - The 3V3A hop's minimum gap is 0.201 mm, on the SE diagonal; F8's 0.200 holds.
- **Critical reference** (`tools/critical_reference.py`):
  - base → final: 0 samples lost and 0 new, by both the R6 method (69,190 referenced) and the extended method
    (168,254);
  - R6 → final: 603 / 882 (R6 method) and 2,312 / 4,325 (extended), identical to pass 7.
- **Pyro and actuator.**
  - No PYRO1_* copper changed. ARM1_SENSE only gained a node at R180.1's centre (17.28, 93.55); the union of its copper
    is identical.
  - Arming break: RAW_ACT to PYRO1_BUS is 1.000 mm on F.Cu (rule E) and 2.482 mm on In1, In2 and B.Cu, unchanged.
  - Every pyro net-pair minimum is unchanged (`pairs.py`). No new BAT_IN via comes nearer a pyro net than J124.1's
    0.500 mm, also unchanged.
  - DRC rules A–H and A2 pass; `check_actuators` OK.
- **DC** (`tools/dc_solve.py`, 0.1 mm, re-solved here):

  | Path | Base | Final | F8 / M3_R7 |
  |---|---:|---:|---:|
  | RAW_ACT Q121 → J122 | 3.98 mΩ | 3.74 mΩ, peak 5.78 A/mm at (21.55, 81.12) | 3.74 mΩ, 5.78 A/mm |
  | BAT_IN J1 → Q120 | 4.58 mΩ | 3.03 mΩ | 3.03 mΩ |
  | ACT_FET_S | 1.36 mΩ | 1.19 mΩ | 1.19 mΩ |
  | RAW_ACT → J124:2 | 1.50 mΩ | 1.50 mΩ | 1.50 mΩ |
  | CAM_5V U13 → R104 | 24.37 mΩ | 19.52 mΩ | 19.52 mΩ |
  | 3V3A U4:5 → C31 | — | 5.86 mΩ | 5.86 mΩ |

  Also on the final board: BAT_IN J1 → U9:5 13.64 mΩ, 3V3 L1:2 → C100:1 74.81 mΩ and → R164:1 12.66 mΩ, as F8
  and M3_R7 give. VLOGIC U11 → C99 is 7.41 mΩ on the base board; its copper did not change.
- **Crossbar vias** (new; `dc_via.py`): at 7.7 A the six vias carry 1.28, 0.57, 0.45, 0.39, 0.28 A and less (about
  3.1 A together). That is below the 1.53 A of the busiest existing BAT_IN via (6.8, 91.0) beside Q120. The via field
  added no hotter barrel than the path already had (Inference about the via's rating: no via current limit is
  specified).
- **IPC-2152 figures.** I recomputed C1's baseline rises from Brooks & Adam's coefficients as quoted in M3_R7:
  - RAW_ACT: 215.3 · 7.7² · 118.1^−1.15 · 1.378^−1 = 38.3 °C;
  - ACT_FET_S: 44.2 °C;
  - BAT_IN (internal): 200 · 7.7^1.9 · 150.4^−1.10 · 1.181^−1.52 = 30.2 °C;
  - the 20 °C widths are 5.28 mm and 5.56 mm.

  All match the record.
- **Servo GND return** (new here; M3_R7 says it "was not analysed"). `dc_gnd.py`, GND J122:3,6,9,12 → J1:2, at a
  0.25 mm grid (coarse, so for comparison only):
  - base 0.81 mΩ, final 0.80 mΩ;
  - In1 carries 88 → 82 % at mid-path and B.Cu 10 → 16 %, the refilled lobe helping;
  - peak 3.86 A/mm at (24.43, 111.33) beside J1.2 on both boards.

  The six new In1 antipads and the deleted GND via did not degrade the servo return.
- **Fab package.**
  - `fab_manifest.py` OK: 5 outputs bound to `c872a3d3…`, 173 inputs.
  - A fresh `kicad-cli` Gerber and drill export with `export_fab.py`'s options equals the packaged files line for line,
    every layer and both drill files (creation-date lines excluded).
  - PTH T1 (Ø0.300) has 710 hits, matching 710 vias.
  - BOM `be711876…` and CPL `c68dc2cb…` are byte-identical to F8's pre-fix copies.
- **Legends.** Each part legend is now within 0.0–0.03 mm of its subject's courtyard (`silk.py`). The "UART 3V3 /
  RX-TX AT MODULE" legend is gone. Every visible moved or newly shown designator is nearer its own part than any other
  part on its face (`desig.py`). The 90 hidden designators on the board are exactly M3_R7's list.

Three Minor findings:

| ID | Severity | One line |
|---|---|---|
| P8-REGRESSION-01 | Minor | F8's `newgap.py` crashed at the first via, so none of the seven new or moved vias was gap-checked. It also reports only each track's nearest neighbour. Four sub-0.2 mm gaps made by fix-pass-7 copper are therefore missing from C15, against C15's stated scope. The new BAT_IN crossbar vias also became neighbours of all three actuator-switch control nets. None of this is recorded |
| P8-REGRESSION-02 | Minor | The records say C86 "keeps its GND through its thermal joint to GND_F (J122.3, 2.4 mm away)". That is untrue. With its own GND via gone (`necks7`), C86.2's only ground is a 14.88 mm² F.Cu island, shared with C83.2, whose single via is (13.075, 83.15), 5.30 mm away. J122.3 is not on that copper |
| P8-REGRESSION-03 | Minor | `label_near` split J2's pin table across the two faces. Rows "1:3V3 2:SWDIO" (B.SilkS) and "3:NRST 4:SWCLK" (F.SilkS) are printed back to back at the same spot, and row 5–6 sits on F.SilkS 9 mm away on the other side of J2. Three placed legends also overlap a courtyard: J124's arming note over J3's, J2's row 5–6 over J2's own, and J9's row 1–2 over C91's |

## 2. Pass-7 findings in this dimension: closure check

| Pass-7 ID | Disposition in R7_VALIDATION (l.717–719) | Verified on the final board |
|---|---|---|
| P7-REGRESSION-01 (BAT_IN_B lobe) | Fixed (`bat_in_b7`) | **Closed.**<br>• BAT_IN_B outline as `BAT_IN_B_FENCED` (`r7_polish.py` l.1299): fill 94.049 → 70.850 mm², 1 piece, box x 0.60–12.45, y 80.90–94.40.<br>• Foreign neighbours of the fill (`zoneneigh.py`): base 3V3 via (12.5, 89.2), GND via (13.95, 93.75), RAW_ACT C150.1, BUZZ_OUT Q123.3, BUZZ_DRV, USB_ILIM R85.1, BUZZ_G and SERVO2_OUT R151.2 (0.30–0.334 mm); final only TH2's hole (0.251), RAW_ACT J124.2, BUZZ_DRV R162.1 and BUZZ_G R162.2 (0.301).<br>• Net pairs on B.Cu (`pairs.py`): BAT_IN–ARM1_SENSE 0.654 → 1.800, BAT_IN–USB_ILIM 0.300 → 2.600, BAT_IN–3V3 0.301 → 1.429 mm.<br>• The lobe point (12.8, 88.0) is in the main GND_B piece (1,089 mm², 45 vias). GND_B +31.73 mm², still 34 pieces |
| P7-REGRESSION-02 (3V3A hop "fixed" by the threshold) | Fixed as P7-ROUTING-04 | **Closed.**<br>• The hop is the fix-pass-5 drawing, (35.5, 76.54)–(36.24, 75.8)–(36.68, 75.8)–(37.4, 76.52), 0.3 mm wide.<br>• Gaps to the GND via (36.5, 76.54): NE 0.257, E 0.290, SE 0.201 mm. The minimum is 0.201 mm (F8 0.200). Pass 7's "0.34 mm" was not this drawing's minimum.<br>• It is allowlisted (A47). C15 #33 and M3_R7 give the R164 burn-open failure mode |
| P7-REGRESSION-03 (SERVO4_MCU – RAW_PROTECTED via 0.192 mm) | Recorded (C15 #34, M3_R7) | **Properly dispositioned.** Copper unchanged. C15 now states its scope: sub-0.2 mm gaps that fix-pass copper created or a review raised. It gives the failure mode (8.4 V on PA3 and through D121 on 3V3). The scope statement is what P8-REGRESSION-01 measures against |

Related items:
- **C24 (ARM1_SENSE):** the split adds a node only; no pyro gap moved (`pairs.py` unchanged).
- **C26 (ACT_EN):** the new B.Cu run has no other-net copper within 0.5 mm except GND_B (0.151 mm). BAT_IN no longer
  borders ACT_EN on F.Cu or In2 (the old 0.301 mm via and run in the BAT_IN fills are gone), but see
  P8-REGRESSION-01 for B.Cu.

## 3. Findings

| ID | Severity | Requirement | Finding | Evidence (final-board coordinates, mm) | Fix |
|---|---|---|---|---|---|
| P8-REGRESSION-01 | Minor | R7_VALIDATION C15 scope ("the edge gaps under 0.2 mm that fix-pass copper created … listed below"); AGENTS §2.5 / REQUIREMENTS M2 (records state what was verified); `fix7_F8_handoff.md` §3 ("New copper gaps (`newgap.py`, every added track / via, < 0.25 mm)") | **The new copper was not fully gap-checked.** F8's `newgap.py` builds a via's shape as `SHAPE_CIRCLE`, whose `Collide` does not accept a pad's shape. It threw a `TypeError` at the first new via, after the last track. So none of the seven new or moved vias (six crossbar vias, `bat_via7`'s via) was measured. Where the script did run, it printed only each track's nearest neighbour. The records agent re-measured "the key pairs" from that list, so C15 lacks four sub-0.2 mm gaps made by fix-pass-7 copper:<br>(a) **BAT_IN crossbar via (9.45, 109.8) – R123.2 (GND), B.Cu, 0.188 mm.** It is new (no BAT_IN copper there before). It is the most serious short pair on the list: the unswitched pack straight onto GND, behind only the external 15 A fuse;<br>(b) CAM_5V_SENSE's new In2 diagonal – 3V3 via (32.33, 33.042), 0.190 mm (was 1.87 mm). A short makes the PB1 camera-5V reading full-scale;<br>(c)–(d) IMU_INT1's new B.Cu SW leg – SERVO1_MCU via (27.1, 68.2) and SERVO2_MCU via (26.3, 67.4), 0.191 mm each. Same line as before, so the same gaps; redrawn copper, as in P7-REGRESSION-03.<br>The same blind spot hides new BAT_IN neighbours of **all three actuator-switch control nets** on B.Cu, where BAT_IN had none within 3 mm (ACT_DRV) or 0.461 mm (ACT_GATE) before:<br>• via (10.2, 107.8), under Q122's body: 0.349 mm from Q122.1 (ACT_EN) and 0.400 mm from Q122.3 (ACT_DRV);<br>• via (9.95, 104.05): 0.262 mm from ACT_GATE's track (9.32, 104.14)–(9.32, 105.1).<br>A BAT_IN–ACT_EN short turns Q122 on with the power switch open (ACT_EN otherwise comes only from RAW_PROTECTED through R122). That powers RAW_ACT, the servos and the ARM-plug side of the pyro bus with the board switched off; the pyro gate stays defined off. This is the "powers RAW_ACT with the power switch open" case that rule H guards for pads. A BAT_IN–ACT_DRV short puts the pack across Q122 whenever it conducts. A BAT_IN–ACT_GATE short holds Q120/Q121 off (servos unpowered). (Inference on each consequence, from the netlist: ACT_EN = Q122.1 / R122.2 / R123.1; ACT_DRV = Q122.3 / R121.2; ACT_GATE = Q120.4 / Q121.4 / R120.2 / R121.1 / C120.2 / TP121.1.)<br>**Calibration:** all of these are DRC-legal (≥ 0.15 mm), and every via is tented on both sides. So a short needs a laminate or mask defect, which JLC's electrical test screens (Inference). The BAT_IN–ACT_EN class existed before: ACT_EN's old via sat at 0.301 mm in the BAT_IN F.Cu and In2 fills. Nothing here is a new hazard class beyond the record. That makes it Minor | `f8/newgap_final.txt`: its last line before the traceback is the last VLOGIC track; then `TypeError: in method 'SHAPE_CIRCLE_Collide', argument 2 of type 'SEG const &'` (newgap.py l.39, l.78). `p8reg/gaps.py` (vias as zero-length `SHAPE_SEGMENT`; every neighbour ≤ 0.5 mm) on the final board: `+ via BAT_IN (9.45, 109.8)`: B.Cu 0.151 GND_B fill, **0.188 GND R123.2**, 0.400 GND Q122.2; `(10.2, 107.8)`: B.Cu 0.322 GND via (9.3, 107.6), **0.349 ACT_EN Q122.1**, **0.400 ACT_DRV Q122.3**, 0.439 GND Q122.2; `(9.95, 104.05)`: B.Cu **0.262 ACT_GATE trk (7.54, 102.36)–(9.32, 104.14) and (9.32, 104.14)–(9.32, 105.1)**, 0.480 ACT_DRV R121.2; CAM_5V_SENSE In2 (30.335, 35.835)–(34.785, 31.385): 0.182 VLOGIC_SENSE (C15 #40), **0.190 3V3 via (32.330, 33.042)**; IMU_INT1 B.Cu (26.55, 67.95)–(26.936, 67.564): **0.191 SERVO1_MCU via, 0.191 SERVO2_MCU via**. `pairs.py`, base → final, B.Cu: BAT_IN–ACT_DRV > 3.0 → 0.400; BAT_IN–ACT_GATE 0.461 (Q120.4) → 0.262; BAT_IN–ACT_EN F.Cu / In2 0.301 → B.Cu 0.349. C15 (R7_VALIDATION l.1011, l.1023–1062) and M3_R7 l.638–643 list none of these. Vias tented: board setup `(tenting (front yes) (back yes))` | Add the four gaps and the three actuator-net neighbours to C15 and M3_R7 with their failure modes, or state that vias and second-nearest neighbours were not measured. Fix `newgap.py` (vias as zero-length segments; print every neighbour under the threshold) and re-run it on fix-pass-7 copper. Optionally drop or move (9.45, 109.8). It carries 0.45 A of 7.7 A, and the solve says 0.28–1.28 A per crossbar via, so the five others take it with little change in J1 → Q120 (Inference). Also move (10.2, 107.8) out from under Q122, which keeps BAT_IN off ACT_EN's pad. Either change needs DRC, the fills, critical reference and DC re-run |
| P8-REGRESSION-02 | Minor | AGENTS §2.5 (no inference written as fact) / records accuracy; REQUIREMENTS M2 (ground returns are part of the review) | `necks7` deleted C86.2's own GND via (18.975, 83.85) and its 0.3 mm F.Cu track to clear the RAW_ACT neck. The `necks7` docstring (`r7_polish.py` l.1395), M3_R7 l.575 and l.1014, and R7_VALIDATION C1 (l.998) justify it: "C86 keeps its GND through its thermal connection to GND_F (J122.3, a plated GND pin, 2.4 mm away)". **Untrue.** C86.2's F.Cu copper is a 14.88 mm² GND_F island, box x 12.10–18.61, y 76.90–83.44, that holds C83.2, C86.2, two GND tracks and one via, (13.075, 83.15), 5.30 mm from C86.2. J122.3 (pad x 19.66–21.26) is not on it. So C86 (1 µF, U10 TPS2553's USB_LIMITED output) now shares one GND via 5.3 mm away with C83 (VBUS input). Before, it had its own via 1.7 mm away plus that one. The island existed before, with the same single via; what changed is that C86.2's private path left. Effect: a longer decoupling loop on a bench-only USB rail and one more two-capacitor single-via dependency. Electrically negligible (Inference: a few nH). R7_VALIDATION Part E (`power_via_no_gnd`, l.1163) records only that the nearest GND via to USB_LIMITED's via is now 4.85 mm away. The cause is a false fact in the records, not the copper | `piece.py` (GND_F, F.Cu, at C86.2 (18.275, 82.15)): base piece 8 and final piece 7, both 14.88 mm², box 12.10–18.61 × 76.90–83.44. On both boards it holds tracks (13.875, 83.15)–(13.075, 83.15) and (14.875, 82.15)–(13.875, 83.15), via (13.075, 83.15) "5.30 mm from the point", pads C83.2 and C86.2. The base also has track (18.275, 82.15)–(18.975, 82.85), the deleted one. `gndpieces.py`: base has a separate 0.87 mm² GND_F piece with 1 via (box 18.34–19.27, 82.65–84.14), the deleted via, which C86.2 reached through that track; it is gone on the final board. J122.3 = (20.46, 79.51), Ø1.6 mm. Netlist: C86 1 µF 25 V on USB_LIMITED (U10.6 OUT, U11.7, C98, R87, TP82); C83 100 nF on VBUS | Correct the docstring, M3_R7 (l.575, l.1014) and C1 (l.998): C86.2 and C83.2 share the single via (13.075, 83.15), 5.3 mm from C86.2, and J122.3 is not on that copper. Optionally give C86.2 a GND via on the island's north side, outside the RAW_ACT band (not searched) |
| P8-REGRESSION-03 | Minor | AGENTS §3 silkscreen ("a legend about a part sits within 6 mm of that part's courtyard"; legible legends); REQUIREMENTS F8 (connector legends) | `label_near` (bottom face first, then the other face) placed each row of a pin table separately. **J2 (TC2030, top side, programmed from the top):** "J2 1:3V3 2:SWDIO" is on B.SilkS and "J2 3:NRST 4:SWCLK" on F.SilkS, at the same spot on opposite faces. "J2 5:GND 6:NC" is on F.SilkS on the far side of J2, 9 mm south. Someone at the top face sees rows 3–6 but not row 1–2. Before, all three rows were on B.SilkS, also scattered. The cable is keyed, so the risk is a confusing legend, not a mis-mated plug. Three placed inks also overlap a courtyard (the gate tests only the distance to the subject):<br>• "J124 2-FUSE-1: ARM LAST" over J3's (USB-C) F courtyard;<br>• "J2 5:GND 6:NC" over J2's own courtyard;<br>• "J9 1:5V 2:GND" over C91's B courtyard.<br>DRC finds no silk over copper. Cosmetic | `silk.py` (ink polygons, final): F.SilkS 'J2 3:NRST 4:SWCLK' x 39.76–40.95, y 58.53–73.11; B.SilkS 'J2 1:3V3 2:SWDIO' x 39.80–40.95, y 59.81–73.11; F.SilkS 'J2 5:GND 6:NC' x 44.01–45.16, y 80.00–91.00 (J2 at (43.0, 76.65), F.Cu). Courtyard overlaps: 'J124 2-FUSE-1: ARM LAST' F.SilkS x 3.06–4.25, y 80.59–101.41 over J3 (0.16 mm²); 'J2 5:GND 6:NC' over J2 (0.14 mm²); 'J9 1:5V 2:GND' B.SilkS x 44.41–45.55, y 27.96–38.73 over C91 (0.18 mm²). Base: all three J2 rows on B.SilkS at (32.0, 66.4), (40.0, 66.9) and (26.0, 86.15) | Keep a connector's pin table on one face, preferably the connector's, as one block. Add a same-face courtyard keep-out to `label_near` and `legend_subjects` |

## 4. Measurements

### 4.1 What changed (base → final; `dump.py`, `diff.py -v`)

| Net | Tracks −/+ | Vias −/+ | Stage; check |
|---|---|---|---|
| 3V3 | 14 / 7 | 1 / 0 | `bumps7` (A34 ends), `v3pair7` (via (30.4, 70.25) and stub; In2 run from (30.17, 71.17)), `dup7` (F.Cu hop (27.35, 44.25)–(29.9, 43.625), In2 run (30.63, 31.34)–(32.33, 33.04)) |
| 3V3A | 8 / 6 | — | `bumps7` (bulge → x 35.6096), `v3a_hop7` (fix-pass-5 drawing) |
| ACT_EN | 5 / 2 | 2 / 0 | `acten7`: R122.2 → (11.75, 107.95) → Q122.1, 0.15 mm, both ends on pad centres |
| ARM1_SENSE | 1 / 2 | — | `arm1_7`: split at R180.1 (17.28, 93.55), no geometry change |
| BAT_IN | 1 / 2 | 1 / 7 | `bat_via7` (via (9.7, 35.5) → (9.725, 35.525), run split); `necks7` crossbar vias (9.45, 109.8 / 111.3 / 112.8 / 114.3), (9.95, 104.05), (10.2, 107.8) |
| BUZZ_DRV, IMU_INT1 | 7 / 3, 2 / 3 | — | `review7` |
| CAM_5V, VLOGIC | 5 / 3, 3 / 3 | — | `bumps7` |
| CAM_5V_SENSE, SERVO2_OUT | 4 / 3, 3 / 3 | — | `sense7` |
| CAM_FAULT_N, I2C1_SDA | 7 / 3, 4 / 3 | — | `tidy7` |
| GND | 2 / 0 | 1 / 0 | `necks7`: C86.2's track and via (18.975, 83.85) |

Widths are unchanged on every redrawn run (3V3 0.25, 3V3A 0.25 / 0.3, CAM_5V 0.2, VLOGIC 0.25, signals 0.15 mm).
No neck-down was introduced.

Fills (saved), mm²:
- 3V3_In2 565.25 → 566.82, 5 → 4 pieces;
- ACT_FET_S_B 37.40 → 43.14 (outline x 1.3 → 0.6; fill edge at x 0.60, inside the 0.5 mm board-edge rule);
- BAT_IN_B 94.05 → 70.85;
- GND_B 3,225.60 → 3,257.32 (34 pieces);
- GND_F 2,983.87 → 2,985.36, 43 → 41 pieces;
- GND_In1 4,727.99 → 4,724.91 (six new BAT_IN antipads, less the three removed vias');
- R6_BAT_IN_In2 760.31 → 763.98 (ACT_EN's void closed);
- R6_BAT_IN_crossbar_F 229.69 → 231.97;
- RAW_ACT_F 109.22 → 110.99.

The foreign neighbours of the ACT_FET_S_B and RAW_ACT_F fills are the same nets at the same 0.301 mm as before
(`zoneneigh.py`). GND single-via pieces on F/B: 34 → 32 (F 20 → 18, B 14 → 14). None is via-less.

### 4.2 New copper and its neighbours (`gaps.py`, every added track and via, every other-net item ≤ 0.5 mm; pours at their zone clearance omitted)

Sub-0.25 mm gaps:

| Gap | New item | Neighbour | In C15? |
|---:|---|---|---|
| 0.169 | CAM_FAULT_N In2 x 18.144 | SERVO4_MCU In2 x 17.825 | yes (#18) |
| 0.171–0.172 | SERVO2_OUT In2 | 3V3 via (21.9, 96.125) | yes (#37) |
| 0.172 / 0.175 | VLOGIC F.Cu | C99.2 (GND) / D122.2 (3V3) | yes (#38 / #39) |
| 0.173 | 3V3 B.Cu NW diagonal | CAM_RX_WIRE via (42.175, 55.82) | yes (#36) |
| 0.175 | 3V3 B.Cu x 38.45 | RAW_PROTECTED via (37.85, 54.7) | yes (#35) |
| 0.182–0.184 | CAM_5V_SENSE In2 | VLOGIC_SENSE In2 | yes (#40) |
| **0.188** | **BAT_IN via (9.45, 109.8)** | **R123.2 (GND), B.Cu** | **no** (P8-REGRESSION-01) |
| **0.190** | **CAM_5V_SENSE In2 diagonal** | **3V3 via (32.33, 33.042)** | **no** |
| **0.191 ×2** | **IMU_INT1 B.Cu SW leg** | **SERVO1_MCU / SERVO2_MCU vias** | **no** (unchanged line) |
| 0.191 | CAM_5V_SENSE In2 | GND via (31.5, 37.8) | the 0.175 mm piece (#23) is unchanged |
| 0.200 | 3V3 B.Cu x 38.45 | RAW_PROTECTED track (37.85, 56.75)–(40.2, 59.1) | at the scope's edge |
| 0.201 | 3V3A hop SE diagonal | GND via (36.5, 76.54) | yes (#33) |
| 0.212 | 3V3A NE diagonal | PYRO1_CONT via (35.78, 60.65) | yes (#8) |
| 0.225 | 3V3A x 35.61 | GND via (35.01, 62.2) | — |
| 0.231 | CAM_FAULT_N In2 E run | USB_FAULT_N via (17.15, 66.85) | — |

New BAT_IN neighbours on B.Cu: ACT_GATE 0.262, ACT_EN 0.349 and ACT_DRV 0.400 mm (P8-REGRESSION-01). On F.Cu,
`bat_via7`'s via is 0.181 mm from the GND_F fill (its ring crosses BAT_IN_F's outline at x 9.9, as in pass 7, 25 µm
further) and 0.251 mm from 3V3_In2 on In2.

### 4.3 Safety net pairs (`pairs.py`, per-layer minimum, base → final)

Unchanged:
- RAW_ACT to PYRO1_BUS (F 1.000; In1, In2, B 2.482), PYRO1_GATE_N (1.041), PYRO1_CONT (0.950) and ARM1_SENSE (F 2.729,
  In2 2.682);
- BAT_IN to PYRO1_BUS (In2 / B 0.500) and BAT_IN to ARM1_SENSE on In2 (0.319);
- GND to PYRO1_BUS, PYRO1_IGN and PYRO1_OUT (0.500–0.501);
- RAW_ACT to ACT_GATE (F 0.301, B 0.660).

Changed:
- BAT_IN–ARM1_SENSE on B.Cu 0.654 → 1.800;
- BAT_IN–USB_ILIM 0.300 → 2.600;
- BAT_IN–3V3 on B.Cu 0.301 → 1.429;
- 3V3–RAW_PROTECTED on B.Cu 0.158 → 0.175;
- BAT_IN–ACT_EN F / In2 0.301 → B.Cu 0.349;
- BAT_IN–ACT_GATE on B.Cu 0.461 → 0.262;
- BAT_IN–ACT_DRV > 3.0 → 0.400.

### 4.4 Ground returns

- **GND vias.** One was removed, C86.2's (P8-REGRESSION-02). No other GND via was added or removed. Every new or
  moved BAT_IN via sits in its two BAT_IN fills (F.Cu crossbar or BAT_IN_F, and In2). On In1 each takes a 1.1 mm GND
  antipad, 0.251 mm clear of its ring.
- **Crossbar via fence.** The four vias at x 9.45, y 109.8–114.3, at 1.5 mm pitch, leave 0.4 mm In1 webs between
  their antipads. They lie west of J1.4 (x 15.38), outside the J122 → J1.2 servo return corridor (x 20–26).
- **Servo return:** 0.81 → 0.80 mΩ at 0.25 mm (§1); the peak beside J1.2 is unchanged.
- **Critical reference:** 0 / 0 (§1). No critical net has a sample over the changed In1, In2 or B.Cu areas that lost
  its reference.

### 4.5 Neck widening and IPC-2152 (C1)

- **RAW_ACT.** The neck moved from C86.2's via and the notch (2.18 mm) to the F.Cu arm under J122 (3.00 mm at
  0.05 mm). The dc_solve peak is 5.78 A/mm at (21.55, 81.12), on that arm.

  The solver holds J122.2, 5, 8 and 11 at one potential, so the copper between the RAW_ACT pins carries nothing in the
  model. In reality the strip between pins 2 and 5 carries three servos (5.8 A) at about the same 2.9 mm width,
  between J122's GND and signal columns. So the 7.7 A cut below pin 2 is indeed the worst one (Inference).
- **ACT_FET_S.** The fill's west edge is at x 0.60 (board-edge rule 0.5 mm). The neck is 2.65 mm at Q120's source row.
  Its only foreign neighbour is still ACT_GATE (C120.2) at 0.301 mm. The GND B.Cu edge strip that was there had no via
  and no pad. The fit model has a non-conductive sled, and no tab window lies at y 93–103 (ORDERING §3).
- **BAT_IN.** J1 → Q120 3.03 mΩ. The F.Cu crossbar now carries about 3.1 A into In2 through the six vias. At
  mid-path 100 % is on In2, and the neck is 3.82 mm on the In2 arm at ACT_GATE's crossing.
- **Baseline rises.** Recomputed from the quoted coefficients, they match C1: 38, 44 and 30 °C at the necks; 20 °C
  width 5.3 / 5.6 mm.
- **Not verified.** M3_R7 l.995 says these are Brooks & Adam's fits "as KiCad's track-width calculator implements
  them". The KiCad 10.0.6 PCB Calculator plug-in's strings name only "IPC 2221" (`strings _pcb_calculator.kiface`), so
  I could not confirm that attribution. The coefficients themselves give the recorded numbers. This dates from fix
  pass 5's records, not fix pass 7, so it is not raised as a finding.

### 4.6 Silkscreen and designators

| Legend | Face | Ink box | Subject, gap to its courtyard | Same-face courtyard overlap |
|---|---|---|---|---|
| J124: 5A FAST / 2S | B | 12.42–13.86 × 97.56–112.70 | J124 (F), 0.0 | — |
| J124 2-FUSE-1: ARM LAST | F | 3.06–4.25 × 80.59–101.41 | J124 (F), 0.03 | J3 0.16 mm² |
| J1 BAT LEAD: 15A FUSE | B | 9.94–27.70 × 114.31–115.45 | J1 (F), 0.0 | — |
| J122 1:S 2:+ 3:GND | B | 23.32–38.56 × 65.72–66.88 | J122 (F), 0.03 | — |
| J2 1:3V3 2:SWDIO | B | 39.80–40.95 × 59.81–73.11 | J2 (F), 0.03 | — |
| J2 3:NRST 4:SWCLK | F | 39.76–40.95 × 58.53–73.11 | J2 (F), 0.03 | — |
| J2 5:GND 6:NC | F | 44.01–45.16 × 80.00–91.00 | J2 (F), 0.0 | J2 0.14 mm² |
| J9 1:5V 2:GND | B | 44.41–45.55 × 27.96–38.73 | J9 (F), 0.0 | C91 0.18 mm² |
| J9 3:TX 4:RX | B | 31.63–41.25 × 41.63–42.83 | J9 (F), 0.0 | — |
| JLCJLCJLCJLC | B | 17.87–27.97 × 85.53–86.68 | — | — (C151's designator 0.30 mm away, as M3_R7 records) |

Designators (`desig.py`; ink to own courtyard / nearest other courtyard on the same face, mm):

| Designator | Own | Nearest other |
|---|---:|---|
| C151 | 0.23 | 0.88 (C150) |
| R157 | 0.21 | 1.29 (TP88) |
| TP88 | 0.36 | 1.18 (R157) |
| C70 | 0.00 | 0.29 (R70) |
| C86 | 0.07 | 0.44 (J122) |
| C91 | 0.58 | 1.42 (C90) |
| J124 | 0.10 | 2.62 (R175) |
| R122 | 0.19 | 1.14 (R121) |
| R72 | 0.06 | 0.38 (J121) |
| TH2 | 0.00 | 2.65 (J3) |
| TP121 | 0.26 | 1.61 (Q121) |

Each is nearer its own part.

## 5. Not checked

- Physical behaviour (bench, thermal camera), as everywhere in this record.
- DC rows I did not re-solve on the final board: 3V3 L1 → U1:75 / FB31 / U1:100 / U1:27, BAT_IN C89 / C95 → U9.5,
  VLOGIC (copper unchanged) and 3V3A U4:8 → C31. The others are re-solved above. The GND return was solved only at a
  coarse grid (0.25 mm, with `tools/dc_solve.py`'s grid check bypassed in the scratch copy).
- RF: no fix-pass-7 copper lies in the RF strip (y < 23.5).
