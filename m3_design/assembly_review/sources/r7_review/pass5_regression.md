# R7 pass 5: board-wide regression and electrical integrity (fix pass 4)

Read-only review, 2026-10-18. Dimension: every copper change of fix pass 4 (agent F5, `m3_design/r7_polish.py`),
judged against the fix-pass-3 board and, where useful, against R6. Focus areas:
- the PYRO1_CONT route, the new GND vias and the pour-trim pad contacts;
- SWCLK near the crystal, the band and debris redraws, and C302 / D30 / D31;
- ground returns and the critical-reference sampling;
- the 3V3 and power feeds, and the DC solve with the corrected stack-up;
- the pyro block rules and the arming break;
- the schematic and netlist.

| Item | Value |
|---|---|
| Final board | `m3_design/assembly_review/m3.kicad_pcb`, SHA-256 `c6fe595cafb91b088ac0b2c812f409f9ca5b86ac45a651102e168b0a5d83c7c7`. This matches `fix4_F5_handoff.md`, M3_R7 and the fab manifest (`inputs_sha256/cad/m3.kicad_pcb`). I checked it before and after this review: unchanged |
| Pass-4 board | SHA-256 `636a6bdc7234586a659741a3da921335a47197648c29cd9612c8374733847650` (F5's start copy `scratchpad/fx4/base.kicad_pcb`, SHA re-checked). Called "base" below |
| Fix-pass-2 board | SHA-256 `7660620c…7c77c9c` (`scratchpad/fx3/base.kicad_pcb`), for pad contacts and the critical reference |
| R6 board | `git show 3b215ba:m3_design/assembly_review/m3.kicad_pcb` (SHA-256 `184a87e8…`), compared moved +18 mm in y |
| Schematic | `m3.kicad_sch` SHA-256 `47057f7d…`, the same as in pass 4 and in the manifest. Every sheet and `schematic.net.xml` is dated 2026-10-16 01:31, before passes 3–5. `m3.kicad_dru` SHA-256 `1674d58b…`, dated 2026-10-15, equal to the manifest |
| Gate (rerun here) | `tools/check.sh` exit 0: DRC 0, unconnected 0, parity 0, ERC 0; audit OK; silk 0; R7 contract OK; routing hygiene 0 failing, 37 allowlisted, 0 stale, 0 out-of-date no-GND reasons, 34 leftovers recorded (0 unrecorded, 0 stale); actuator contract OK; fit OK |
| Tests (rerun here, KiCad Python) | test_dc_solve 3 OK, test_route_check 32 OK, test_r7_check 34 OK, test_check_shell 2 OK |
| Tools | KiCad 10.0.6 `pcbnew` read-only scripts on scratch copies (`scratchpad/p5reg/`); `tools/critical_reference.py`; `tools/dc_solve.py`; the earlier reviewers' `dump.py`, `geo_export.py`, `neigh.py`, `couple2.py`, `gexport.py`, `gpath.py` and `padcontact.py` (read-only copies); new `isl_all.py`, `ctx.py`, `stack.py`, `unref.py`, `viaconn.py`, `gfar.py` and `trims.py` |
| Fills | Saved fills used throughout (the build scripts refill natively) |

## 1. Summary

**No Critical and no Major findings.** Fix pass 4 did what its handoff says, and I found no electrical regression.

What holds:
- **Netlist and parts:** unchanged.
  - All 819 pad entries match the base board in net, position, size and layer. The only change is C302.2's
    zone connection, from solid (2) to thermal (1), which was intended.
  - All 252 footprints match in FPID, position, rotation, layer, attributes, DNP, value and fields. Design
    settings and net classes are identical. The schematic is untouched.
- **Copper changed on 17 nets only** (§4.1), all of them named in the handoff: PYRO1_CONT, CAM_UART_OE and NRST
  rerouted; 10 debris redraws; 3 radio-band step moves; 4 GND vias added and 2 removed.
- **PYRO1_CONT** is on the plane-preserving route: 47.53 mm, 6 vias.
  - All six layer changes have a GND via within 1.5 mm: 1.112, 0.721, 1.014, 0.728, 0.764 and 1.408 mm.
  - The In2 3V3 island under U1/U4 is one piece again: 74.51 mm² with 4 vias.
  - No SPI1 copper is within 2 mm. PYRO1_GATE_N tracks and vias are ≥ 1.285 mm away (the 1.08 mm pad gap is
    R6's). PYRO1_OUT is 0.715 mm away (rule C asks 0.3 mm). RAW_ACT is ≥ 1.322 mm away.
  - None of its In2 runs lies inside any In2 zone outline, so it cuts no plane.
- **Critical reference:** fully restored. The R6 method gives 603 lost and 861 candidate-new, as F5 reports, and
  0 lost against both the base and the fix-pass-2 board. The fix-pass-2 board referenced 69,916 samples; the final
  board references 69,916.
- **GND returns:** of the 173 SMD GND pads, none got farther in copper from a GND via by more than 0.1 mm. C126.2
  (1.05 → 0.58 mm) and R63.2 (1.30 → 1.07 mm) got nearer.
- **Pad pour contact:** C7.2, C150.2, C30.2, C31.2 and R64.2 are back to their fix-pass-2 values (0.060, 0.060,
  0.015, 0.030, 0.030 mm²). The 40 pads with no pour contact are the same 40 as on the fix-pass-2 board.
- **DC with the board's stack-up** (35 µm outer, 30 µm inner): F5's table reproduces (RAW_ACT 3.95, BAT_IN J1 → Q120
  4.55, ACT_FET_S 1.36, J1 → U9 15.14, 3V3 L1 → U1.75 15.64, FB31 14.66, FB30 5.53, CAM_5V 27.79 mΩ at 0.1 mm).
  JLC lists 1 oz internal copper as 1.2 mil (0.030 mm). Fix pass 4 moved no power path beyond the method's
  resolution.
- **Pyro block:**
  - No track or via of PYRO1_BUS, IGN, OUT, GATE, RAW_ACT, ACT_*, ARM1_* or BAT_IN changed, and no fill of those
    nets changed.
  - The arming break is intact: PYRO1_BUS = {J124.1, R132.1, R134.2}, and RAW_ACT reaches J124.2 only.
  - DRC passes every pyro rule, and `check_actuators` is OK.
- **Fab package:** bound to this board. The PTH drill file holds the board's 694 vias (only 0.001 mm rounding on
  three), including the 4 new GND vias and none of the 2 removed ones.

Four Minor items:

| ID | Severity | One line |
|---|---|---|
| P5-REGRESSION-01 | Minor | The records say NRST's new In2 run has "about 1.8 mm" without B.Cu GND under PYRO1_CONT / 3V3A copper. The 545 extended-set samples behind that figure lie near U1, not on the x 36.3 run. The x 36.3 run is 10.35 mm with no B.Cu GND beneath any of it, 7.2 mm of that directly under the 3V3A track. Net effect: better than before, 20.6 → 14.7 mm of NRST In2 without B.Cu GND |
| P5-REGRESSION-02 | Minor | Fix pass 4's reroutes left four GND pour pieces stitched by a single via, none of them recorded. The largest is a 13.3 mm² F.Cu piece beside J2, between NRST's new diagonal and PYRO1_CONT's x 39.78 run, whose far copper is 7.95 mm from its via. Single-via GND pieces: F.Cu 20 → 22, B.Cu 19 → 18 |
| P5-REGRESSION-03 | Minor | New close neighbours of the new copper, all DRC-legal and not recorded. The new GND via (28.55, 87.21) is 0.17 mm from R129.1 (PYRO1_CONT_MID) and 0.19 mm from R178.1 (PYRO1_CONT). PYRO1_CONT's vias are 0.175 mm from CAM_UART_OE and 0.191 mm from SWCLK. NRST's In2 run is 0.195 mm from a PYRO1_CONT via. Every failure mode is fail-safe or benign (§3) |
| P5-REGRESSION-04 | Minor | Record precision. M3_R7 places PYRO1_CONT's B.Cu run "east of U4"; it is beside R168, east of U1, about 20 mm from U4. It places the F.Cu run "east of the IMU"; that run is north of the IMU and east of the barometer U5. Also unrecorded: the last In2 run crosses under PYRO1_OUT's F.Cu (x 30.58), with In1 GND in between, which is benign |

## 2. Pass-4 findings in this dimension: closure check

| Pass-4 ID | Disposition in R7_VALIDATION | Verified on the final board |
|---|---|---|
| P4-REGRESSION-01 (PYRO1_CONT's In2 cut split the 3V3 island; 7.4 mm beside SPI1_SCK; 0.191 mm to PYRO1_GATE_N's via) | Fixed (plane-preserving route) | **Closed.** 3V3_In2 is 5 polygons (was 6); the island at (22.10–32.15, 51.24–70.20) is 74.512 mm² with 4 vias (was 41.93 / 3 + 22.69 / 1). PYRO1_CONT has no SPI1_SCK, MOSI or MISO copper within 2.0 mm on any layer (was 0.195 mm over 7.36 mm). Its nearest PYRO1_GATE_N copper is 1.285 mm away (F.Cu track (24.6, 87.2)–(24.6, 87.8) to via (23.0, 88.33)); the In2 gap is > 2 mm. Critical reference against the base: 0 lost. Against the fix-pass-2 board: 0 lost. The 6 vias are allowlisted with a measured reason (A29), so this is a deviation awaiting owner acceptance |
| P4-REGRESSION-02 (pour trims took the last pour contact from five GND pads) | Fixed | **Closed.** Contact (fill within 0.05 mm of the pad outline), fix-pass-2 → base → final: C7.2 0.060 → 0 → 0.060, C150.2 0.060 → 0 → 0.060, C30.2 0.015 → 0 → 0.015, C31.2 0.030 → 0 → 0.030, R64.2 0.030 → 0 → 0.030 mm². Zero-contact pads: 40, the same set as on the fix-pass-2 board. The trims that caused it are gone: `R7_POUR_TRIM_21` (C7.2) and the old `_8` (C30/C31/R64). The old `_11` shrank from 2.853 to 1.158 mm². New trims: F.Cu (36.14–40.42, 65.18–69.40) and B.Cu (26.92–27.62, 70.84–74.98). The gated `pad_pour_cut` reports 0 |
| P4-REGRESSION-03 (SWCLK via 1.10 mm from Y1.3; B.Cu GND split) | Recorded, no copper change | **Properly dispositioned.** No SWCLK, SWDIO, BUZZ_DRV, HSE or Y1/C25/C26 copper is in the fix-pass-4 diff, so the 1.10 mm stands. GND_B is 35 polygons (was 39). The crystal/U1 island is 133.20 mm² with 27 vias, unchanged. Recorded in M3_R7 "Rerouted in fix pass 3" and as deviation C8/C9, with F5's measured routing constraints |
| P4-REGRESSION-04 (three record precisions) | Fixed (records) | **Closed.** (a) M3_R7 l.440 and the P3-REGRESSION-05 row give 0.200 mm at the via beside 0.232 mm on the run. (b) The P3-REGRESSION-02 row and M3_R7 give 1.68 / 0.24 mm, with the method. (c) M3_R7 "DC solve" states L1.2 → C9.1 1.67 → 2.48 mΩ. Here: 3V3 L1:2 → C9:1 2.48 mΩ at 0.1 mm (§4.4) |

Related items from other dimensions that touch this focus:
- **P4-ROUTING_GEOMETRY-01:** closed. A GND via 0.6/0.3 mm at (22.85, 89.63) is 1.309 mm from PYRO1_GATE_N's layer
  change (23.0, 88.33). It is joined to GND on F.Cu, In1 and B.Cu (fill overlap 0.324 / 0.324 / 0.324 mm²).
- **P4-DOCS-02:** closed. `dc_solve.py` reads the board's own stack-up and prints it ("F.Cu 35 um at 0.0175 mm,
  In1.Cu 30 um at 0.2530 mm, In2.Cu 30 um at 1.3130 mm, B.Cu 35 um at 1.5485 mm").
  - The inner value matches JLC's impedance-calculator parameters: "Internal copper thickness (1 oz) 1.2 mil", that
    is 0.030 mm ([JLCPCB, User Guide to the JLCPCB Impedance Calculator, "Calculation Parameters Used"](https://jlcpcb.com/help/article/User-Guide-to-the-JLCPCB-Impedance-Calculator)).
  - The 0.203 mm prepreg and 1.03 mm core of JLC041611-7628 are as ORDERING §3 states. I could not re-read them on
    JLC's public impedance page, which shows only JLC04161H-7628: 0.2104 / 1.065 mm, 15.2 µm inner copper
    (https://jlcpcb.com/impedance). They set only the via barrel lengths, a sub-percent effect on these paths
    (Inference).
- **P4-RF-03 (C302):** closed. C302.2 (the GNSS bias-tap cold end, GND) is on thermal relief, with pour contact
  0.1115 → 0.045 mm². DRC reports no starved thermal (min_resolved_spokes 2). D30.2 and D31.2 stay solid by
  decision; their pads, nets and contact are unchanged.

## 3. Findings

| ID | Severity | Requirement | Finding | Evidence (final-board coordinates, mm) | Fix |
|---|---|---|---|---|---|
| P5-REGRESSION-01 | Minor | AGENTS.md §3 (records state what was verified); M3_R7 §"Return paths" / §"Rerouted in fix pass 4"; R7_VALIDATION deviation C10 | Three places record "about 1.8 mm" of NRST's new In2 run (x 36.3) under PYRO1_CONT / 3V3A B.Cu instead of GND: M3_R7 l.420–422 and l.591–595, and deviation C10. The 545 extended-set "new" samples behind that figure are not on the x 36.3 run. They lie at (30.73–36.09, 51.41–54.31): mostly where the new J2 branch's own B.Cu run (30.8, 53.1)→(30.8, 52.3)→(31.5, 51.6) sits over NRST's own In2 segments near U1, plus the (35.8, 53.95)→(36.3, 54.45) diagonal. The x 36.3 run itself has no B.Cu GND beneath any of its 10.35 mm, and 7.23 mm of it lies directly under the 3V3A B.Cu track at x 36.4. That is inherited: the base's x 36.435 run had 13.38 of 14.0 mm unreferenced, R6's the same. So the reroute improved the net, but the recorded figure and location are wrong. NRST is not in the AGENTS §3 critical list. It is a slow reset input with C24 at U1, and the J2 branch is a programming stub; In1 GND stays 1.06 mm above the run. Inference: the electrical effect is negligible. The broadside overlap with 3V3A is about 0.2 pF over 7.2 mm of 0.203 mm prepreg | `unref.py` (NRST In2 centre line against B.Cu GND fill, 0.02 mm): R6 36.13 mm total / 23.12 unreferenced; base 29.79 / 20.59; **final 18.72 / 14.66**, of which (36.30, 54.45)–(36.30, 64.80) is 10.35 / 10.35 and (35.80, 53.95)–(36.30, 54.45) 0.71 / 0.71. `stack.py`: B.Cu 3V3A (36.4, 52.1)→(36.4, 60.86), 0.25 mm, over the NRST In2 run for 7.23 mm. `critical_reference.py --extended`: R6 → final new "NRST In2.Cu 545, box [30.73, 51.41, 36.09, 54.31]"; base → final lost NRST In1 478 and In2 444, new NRST In2 626 | Restate C10 and the two M3_R7 places: the x 36.3 In2 run (10.35 mm) has no B.Cu GND beneath it (7.2 mm under the 3V3A track), as R6's x 36.435 run did not; NRST In2 without B.Cu GND fell from 20.6 to 14.7 mm; In1 GND is above. Optional, at a respin: run NRST's In2 lane where B.Cu GND covers it |
| P5-REGRESSION-02 | Minor | REQUIREMENTS M2 ("unstitched GND pour fingers"; review beyond the gate's 0.5 mm finger width); AGENTS.md §3 return paths; records completeness | The new PYRO1_CONT, NRST and CAM_UART_OE copper and the removed fix-pass-3 GND via cut four GND pour pieces down to a single via. Every GND piece still holds at least one via, and the gate's finger and sliver checks pass, because the pieces are wider than 0.5 mm. The records say only "every piece holds vias"; neither the new single-via pieces nor their reach is recorded. Inference: no critical net uses these pieces as its reference (F.Cu and B.Cu signals reference In1 GND and the In2 planes), so the electrical effect is negligible. This is a pour-tidiness item of the P4-RF-01 / deviation C11 kind | `isl_all.py` + `gfar.py` (0.05 mm geodesic over the fill to the via edge). (1) **F.Cu 13.32 mm²** (40.01–45.07, 69.19–76.11), via (44.75, 75.38) only, farthest copper 7.95 mm at (40.03, 69.42). Before: part of a 153.78 mm² / 12-via piece (33.53–45.50, 57.84–76.42). Bounded by NRST F.Cu (36.3, 64.8)→(45.3, 73.8), PYRO1_CONT F.Cu x 39.78 (69.25–73.65) and J2. (2) **B.Cu 15.20 mm²** (32.89–37.90, 48.40–53.61), via (35.75, 50.35) only. Before: 37.92 mm² / 3 vias; cut by NRST B.Cu (31.5, 51.6)→(33.45, 51.6)→(35.8, 53.95). (3) **B.Cu 14.28 mm²** (27.13–33.09, 74.78–82.99), via (31.0, 80.15) only. Before: 11.41 mm² / 2 vias; fix pass 3's GND via (29.28, 77.95) left with the old PYRO1_CONT route. (4) **F.Cu 2.71 mm²** (31.81–35.52, 56.24–58.43), via (35.17, 57.92). Before: 6.36 mm² / 2 vias; cut by CAM_UART_OE F.Cu (31.65, 56.5)→(33.15, 58.0). Single-via GND pieces, base → final: F.Cu 20 (123.1 mm²) → 22 (139.1 mm²); B.Cu 19 (154.9) → 18 (174.0). On the other side: the main F.Cu piece's farthest copper fell from 17.21 to 10.66 mm, and the B.Cu piece at (29.28–31.34, 63.09–75.40), 10.05 mm, merged away | Search for a legal GND via in piece (1) (the J2 side, about 4–5 mm from (44.75, 75.38)) and in (2) with `r7_hygiene.gnd_spots`; add one if legal. Otherwise list the four pieces in R7_VALIDATION part C beside C11 with these numbers |
| P5-REGRESSION-03 | Minor | AGENTS.md §3 / `m3.kicad_dru` pyro rules A–H (spacing intent: a bridge to a sense net reads wrong, a bridge to a gate fires); JLC DFM (pads next to vias; vias tented per board setup) | Fix pass 4 put new copper close to some neighbours. All of it is DRC-legal at the 0.15 mm default, and none of it is recorded. Checked by failure mode: (a) GND via (28.55, 87.21), 0.5 mm, is 0.170 mm from R129.1 (PYRO1_CONT_MID) and 0.190 mm from R178.1 (PYRO1_CONT), 0402 pads on F.Cu inside PYRO_BLOCK. No rule covers GND to sense nets: rule D covers only bus, igniter and drain. A short reads "no continuity" (CONT to GND reads 0 V; CONT_MID to GND loads PYRO1_OUT with R173's 5.1 kΩ, about 1.6 mA through an armed igniter, far below any no-fire current). Both are fail-safe. (b) GND via (22.85, 89.63) is 0.297 mm from R126.1 (PYRO1_GATE_N). Rule G excludes GND by design: a GATE_N-to-GND short holds the FET off. (c) PYRO1_CONT via (35.78, 60.65) is 0.175 mm from CAM_UART_OE F.Cu (38.0, 60.15)→(34.55, 60.15) and 0.171 mm from GND via (35.18, 61.05). PYRO1_CONT via (35.78, 58.85) is 0.191 mm from SWCLK F.Cu (35.75, 58.15)→(33.3, 60.6). PYRO1_CONT via (28.40, 88.61) is 0.193 mm from R129.1 (its own divider midpoint, the shorted-half case the pass-11 split tolerates). (d) NRST's In2 run is 0.195 mm from PYRO1_CONT via (35.78, 60.65); NRST via (35.80, 53.95) is 0.202 mm from SWCLK via (35.75, 54.65). Board setup tents both via sides (`(tenting (front yes) (back yes))`), so a via-to-pad solder bridge needs a mask defect. Inference: every short is screened by JLC's electrical test, and none can fire a channel or put RAW_ACT on an MCU pin | `neigh.py` on `geo_final.json` (edge gaps, mm). GND via (28.55, 87.21): R129.1 0.170, R178.1 0.190, R129.2 0.328. GND via (22.85, 89.63): SERVO1_OUT In2 0.175, SERVO2_MCU In2 0.203, R126.1 0.297. PYRO1_CONT: CAM_UART_OE 0.175, SWCLK 0.191, R129.1 0.193, NRST 0.195, 3V3A B.Cu 0.212, CAM_EN (R75.1) 0.225, PULLPIN via 0.235, PYRO1_OUT (Q124.5) 0.715 (rule C 0.3), RAW_ACT 1.322 (rule A 0.5). M2 via-hole rule: the hole edge of via (28.55, 87.21) is 0.27 mm from the R129.1 pad (≥ 0.1 mm) | Record (a) and (b) in M3_R7 §"Close adjacencies kept" with the fail-safe reasoning, or nudge the GND via (28.55, 87.21) if a legal spot ≥ 0.25 mm from R129.1 / R178.1 still keeps PYRO1_CONT's via (28.4, 88.61) within 1.5 mm |
| P5-REGRESSION-04 | Minor | AGENTS.md §3 (records state what was verified); M3_R7 §"Rerouted in fix pass 4" | M3_R7 l.411–412 describes the new PYRO1_CONT route as "B.Cu east of U4, a 1.8 mm In2 hop, F.Cu east of the IMU, an In2 hop under the SWD diagonals, F.Cu to the pyro block, In2 into R129.2". Two of the locations are wrong. (a) The B.Cu run (33.03, 52.9)→(35.78, 55.65)→(35.78, 58.85) starts at R168.1 beside U1's east side. U4 (the IMU) is at (36.0, 78.3), about 20 mm south. (b) The F.Cu run (35.78, 60.65)→(35.78, 65.25)→(39.78, 69.25)→(39.78, 73.65) lies north of the IMU and east of the barometer U5 (36.3, 73.0). The "In2 hop under the SWD diagonals" is right: In2 (41.63, 75.5–78.85) crosses under SWCLK's and SWDIO's F.Cu diagonals at y 76.65 and 77.85. Not recorded: the last In2 run (30.82, 88.61)→(28.40, 88.61) crosses under PYRO1_OUT's F.Cu vertical (x 30.58, y 86.1–90.0), with solid In1 GND between them (checked at x 30.30–30.85). That is benign, and the pyro rules are same-layer. No conclusion changes | `fp_final.json`: U1 (21.85, 53.5), U4 (36.0, 78.3), U5 (36.3, 73.0), R168 (32.6, 52.9). Segment intersections of the PYRO1_CONT In2 tracks with every other track: (41.63, 75.5)–(41.63, 78.85) × SWCLK F.Cu at (41.63, 76.65), SWDIO F.Cu at (41.63, 77.85), 3V3 B.Cu at (41.63, 77.92); (30.82, 88.61)–(28.40, 88.61) × PYRO1_OUT F.Cu at (30.58, 88.61), SERVO1/3/4_MCU B.Cu; GND_In1 fill present at (30.30–30.85, 88.61) | Correct the two locations ("B.Cu east of U1 from R168", "F.Cu north of the IMU, east of the barometer"), and add the shielded PYRO1_OUT crossing to the PYRO1_CONT entry |

## 4. Measurements

### 4.1 What changed (base → final, exact track and via geometry)

Tracks 1836 → 1809 (97 removed, 70 added); vias 694 → 694 (16 removed, 16 added); zones 52 → 52.

| Net | Tracks −/+ | Vias −/+ | Change |
|---|---|---|---|
| CAM_UART_OE | 20 / 10 | 6 / 4 | rerouted, 44.11 → 30.68 mm; 2.7 mm In2 hop (34.0, 58.0–60.7) in a pre-existing void of 3V3_In2 (the main polygon's area is unchanged at 455.47 mm²) |
| PYRO1_CONT | 12 / 14 | 4 / 6 | plane-preserving route, 47.53 mm |
| NRST | 15 / 10 | 4 / 2 | J2 branch: off In1, new B.Cu → In2 (x 36.3) → F.Cu diagonal; total drawn 54.33 → 46.11 mm |
| GND | 0 / 0 | 2 / 4 | removed (23.68, 69.55), (29.28, 77.95) (fix pass 3's PYRO1_CONT returns); added (22.85, 89.63) Ø0.6, (28.55, 87.21) Ø0.5, (35.18, 61.05) Ø0.6, (40.93, 78.65) Ø0.6 |
| SERVO2_MCU, SERVO4_MCU, SERVO3_MCU, SERVO4_OUT, CAM_RX_WIRE, I2C1_SCL, LOGIC_ILIM, LED_YEL_A, CAM_EN, CAM_5V_SENSE | 41 / 28 | 0 | debris redraws (tiny jogs and short segments merged; same end points) |
| RADIO_NRST, RADIO_SCK, RADIO_NSS | 9 / 8 | 0 | band steps (NRST's 0.141 mm 45° segment inside its 0.5 mm via; SCK after 1.05 mm; NSS 0.6 mm later) |
| C302.2 | — | — | pad zone connection solid → thermal |

- **Fills:**
  - 3V3_In2: 6 → 5 polygons, 555.51 → 565.40 mm².
  - CAM_5V_In2: 139.26 → 139.60 mm².
  - GND_B: 39 → 35 polygons, 3212.92 → 3226.13 mm².
  - GND_F: 43 → 43 polygons, 2981.77 → 2986.68 mm².
  - GND_In1: 1 polygon, 4718.02 → 4722.40 mm², 359 → 361 vias inside.
  - Every other fill is unchanged: R6_BAT_IN_In2, 3V3A_In2, RAW_ACT and the R7 strip GND.
- **In1 signal copper:** only CAM_TX_WIRE's three inherited R6 segments; NRST's three In1 segments are gone.
- **Rule areas:** 21 `R7_POUR_TRIM_n`, renumbered (§2, P4-REGRESSION-02). No other rule area changed.

### 4.2 GND returns and pour pieces

- **SMD GND pads** (0.05 mm geodesic from the pad outline to the nearest GND via or plated GND hole, over F.Cu or
  B.Cu GND copper; the pass-3 reviewer's `gexport.py` / `gpath.py`):
  - 173 pads on both boards; none farther by more than 0.1 mm.
  - Nearer: C126.2 1.05 → 0.58 mm, R63.2 1.30 → 1.07 mm.
- **New GND vias:** each is joined to the GND fill on F.Cu, In1 and B.Cu (`viaconn.py`). In2 is not GND at any of
  them; they pass through In2 voids or other nets' antipads.
- **Pour pieces:** every GND piece on F.Cu and B.Cu holds at least one via or plated GND hole. The only via-less
  copper pour piece on the board is ACT_FET_S_B (37.40 mm², SMD-to-SMD between Q120 and Q121), unchanged.
  Single-via pieces: P5-REGRESSION-02.
- **Pour contact per pad** (`padcontact.py`, 261 pad/layer entries, three boards): only these changed by more than
  0.002 mm² against the fix-pass-2 board:
  - the five restored pads (§2);
  - C302.2 0.1115 → 0.045 mm² (intended);
  - C127.2 F.Cu 0.030 → 0.045, J122.3 In1 0.222 → 0.259, U1.26 F.Cu 0.184 → 0.179 (all from fix pass 3, unchanged
    in fix pass 4).

### 4.3 Critical-net reference (`tools/critical_reference.py`)

| Comparison | Lost | Candidate-new |
|---|---:|---:|
| R6 (+18 mm) → final, R6 method | **603** (QSPI_IO0 F 410, SPI1_MOSI F 79, QSPI_IO3 F 59 / B 2, QSPI_NCS B 38, QSPI_IO1 B 15) | **861** |
| R6 (+18 mm) → final, extended | 2,312 (adds IMU_CS In2 256, NRST In1 373, NRST In2 760, SWCLK F 320) | 4,304 (adds NRST In2 545 at (30.73–36.09, 51.41–54.31), the radio SPI, SWCLK / SWDIO) |
| Base → final, R6 method | **0** | **0** |
| Fix-pass-2 board → final, R6 method | **0** (69,916 referenced on both) | **0** |
| Base → final, extended | 986 (NRST In1 478 and In2 444: removed or rerouted copper; SWCLK F 64 at (35.13–35.63, 58.37–58.74)) | 690 (NRST In2 626; SWCLK F 64) |

- F5's numbers reproduce exactly.
- **SWCLK's 64 samples:** the new PYRO1_CONT via (35.78, 58.85) sits 0.191 mm from SWCLK's F.Cu diagonal, and its
  In1 antipad takes about 0.2 mm of In1 GND from under SWCLK. SWCLK is not in the AGENTS §3 list and is idle in
  flight. Not raised.
- **Unreferenced length of the rerouted nets** (centre line, 0.02 mm sampling; `unref.py`):
  - PYRO1_CONT: F.Cu 32.16 mm with 2.52 over antipads (base 20.00 / 1.53); B.Cu 7.09 / 7.09 over an In2 void (base
    18.03 / 18.03); In2 14.09 / 6.27 without B.Cu GND, under solid In1 GND (base 9.56 / 4.31).
  - NRST In2: P5-REGRESSION-01.
  - PYRO1_CONT is a DC sense line filtered by C127 at the divider, so reference continuity is immaterial
    (Inference). The B.Cu share it runs over a void fell from 18 to 7 mm.

### 4.4 DC solves (`tools/dc_solve.py`, board stack-up: 35 / 30 / 30 / 35 µm, 20 µm plating, 20 °C, 0.1 mm grid)

| Path | Base | Final | F5 / M3_R7 (final) |
|---|---:|---:|---:|
| RAW_ACT Q121:5–9 → J122:2,5,8,11 (7.7 A) | 3.95 (F5) | **3.95** (30.4 mV, 0.234 W; F.Cu 100 %, peak 5.75 A/mm at (19.15, 84.52)) | 3.95 |
| BAT_IN J1:1 → Q120:5–9 (7.7 A) | 4.55 (F5) | **4.55** (35.0 mV, 0.269 W; In2 100 %, peak 6.17 A/mm at (10.45, 107.62)) | 4.55 |
| ACT_FET_S Q120:1–3 → Q121:1–3 (7.7 A) | 1.36 (F5) | **1.36** (10.4 mV, 0.080 W; B.Cu, peak 6.15 A/mm) | 1.36 |
| BAT_IN J1:1 → U9:5 (1 A) | 15.14 (F5) | **15.14** | 15.14 |
| CAM_5V L3:2 → J9:1 (1 A) | **27.88** | **27.79** | 27.79 |
| 3V3 L1:2 → U1:75 | **15.64** | **15.64** | 15.64 |
| 3V3 L1:2 → FB31:1 (radio feed) | 14.66 (F5) | **14.66** | 14.66 |
| 3V3 L1:2 → FB30:1 (GNSS feed) | 5.53 (F5) | **5.53** | 5.53 |
| 3V3 L1:2 → U1:27 | 6.85 (F5) | **6.85** | 6.85 |
| 3V3 L1:2 → U3:8 (QSPI flash) | 6.76 (F5) | **6.76** | 6.76 |
| 3V3 L1:2 → C9:1 (buck output capacitor) | 2.48 (F5) | **2.48** | 2.48 |
| 3V3 L1:2 → U1:50 | **7.19** | **7.19** | not given |
| 3V3 L1:2 → U1:100 (island-side VDD) | **78.86** | **78.23** (R6, 35 µm model: 97.28) | not given |
| 3V3 L1:2 → U1:6 (island-side VDD) | **78.06** | **78.05** | not given |
| 3V3 L1:2 → J2:1 (Tag-Connect 3V3, bench only) | **172.98** | **162.24** | not given |

Values in mΩ. Bold base values are solved here. The others are F5's base values (`fix4_F5_handoff.md` §5.1); I did
not re-solve them because none of those nets has a track, via or fill change in the diff (§4.1).
- **Fix pass 4 changed no power path:** no track or via of any power net moved. The only power-fill changes are
  3V3_In2 (the island merge) and CAM_5V_In2 (+0.34 mm²). CAM_5V moves −0.3 %, inside the method's resolution.
- **The merged 3V3 island** feeds U1.100 and U1.6 through its four vias and 0.2–0.25 mm tracks. Those pins see
  about 78 mΩ from L1.2 on both boards (−0.8 % / 0 %). R6 had 97 mΩ to U1.100 in its own 35 µm model, so this is
  inherited and better than R6. At 50 mA per pin it is 3.9 mV, and U1.75 (15.6 mΩ), U1.50 and U1.27 (about 7 mΩ)
  carry the bulk in parallel through the die's VDD (Inference). Not raised. J2.1's 3V3 (bench only) fell 173 →
  162 mΩ; 3V3 has no track or via change, so this comes from the 3V3_In2 fill (the island merge).
- **Stack-up:** the tool's mid-plane depths follow the board's `(stackup …)` block: F↔In1 0.2355, In1↔In2 1.0600,
  In2↔B 0.2355 mm. The +16 % on BAT_IN J1 → Q120 against the old 35 µm model is the inner-copper ratio (35/30 =
  1.17) on a path that is 100 % In2 at mid-path, as expected.
- **Not raised:** the In2 BAT_IN neck at 6.17 A/mm (≈ 206 A/mm² in 30 µm). It is unchanged copper, recorded in
  M3_R7 "DC solve" as not re-derived against IPC-2152, with the bench thermal-camera stall test (F4) as the check.
  Inference, first principles as in GEOMETRY_REV_G: J²ρ at 206 A/mm² is (2.06 × 10⁸)² × 1.72 × 10⁻⁸ ≈ 7.3 × 10⁸
  W/m³. That is about 22 mW per mm² of neck area in 30 µm copper, spread into the surrounding pour and both planes,
  so the local rise is small. The whole path dissipates 0.27 W in the 7.7 A all-stall case.

### 4.5 Pyro block, arming break and DRC rules

- **Rules:** `m3.kicad_dru` is unchanged (SHA equal to the manifest's input). DRC passes every pyro rule (A–H, A2),
  and `check_actuators` passes in the gate.
- **Copper of the live and gate nets:** PYRO1_BUS, PYRO1_IGN, PYRO1_OUT, PYRO1_GATE, PYRO1_GATE_N, RAW_ACT,
  ACT_FET_S / ACT_GATE / ACT_DRV, ARM1_SENSE(_MID), PYRO1_CONT_MID, PYRO1_COLD, RAW_ACT_SENSE(_MID) and BAT_IN have
  no track or via in the diff, and none of their fills changed.
- **Arming break:** PYRO1_BUS = {J124.1, R132.1, R134.2}, PYRO1_IGN = {J121.2, R134.1}, and RAW_ACT reaches J124.2
  only (J124.1 is BUS). Unchanged.
- **New copper inside PYRO_BLOCK** (4.0–42.0, 84.0–114.4):
  - PYRO1_CONT: F.Cu (35.73, 84.75)–(34.68, 84.75) and the tail into R129.2; In2 (34.68, 84.75)→(30.82, 88.61)→(28.40,
    88.61); vias (34.68, 84.75) and (28.40, 88.61);
  - GND vias (22.85, 89.63) and (28.55, 87.21);
  - redraws of SERVO2_MCU In2 (y 87.87), SERVO4_MCU In2 (x 15.478 → 15.838 jog), SERVO3_MCU B.Cu and CAM_EN B.Cu.
- **Nearest pyro-rule distances of the new copper:**
  - PYRO1_CONT to PYRO1_OUT 0.715 mm (C 0.3), to RAW_ACT 1.322 mm (A 0.5), to PYRO1_GATE_N ≥ 1.285 mm;
  - SERVO2_MCU In2 to PYRO1_GATE_N In2 0.316 mm (G 0.3; that diagonal is unchanged);
  - no new GND copper within 0.5 mm of BUS, IGN or OUT (D).
- **Stacked crossings:**
  - PYRO1_CONT In2 passes under B.Cu SERVO1/3/4_MCU (0.15 mm each, perpendicular) and CAM_DVDT. Inference: 333 Hz
    servo edges into a C127-filtered sense line are immaterial.
  - PYRO1_CONT In2 also crosses under PYRO1_OUT's F.Cu at (30.58, 88.61). Solid In1 GND lies between them
    (P5-REGRESSION-04), and no rule covers cross-layer pairs.

### 4.6 Close parallel coupling (same layer, edge gap ≤ 0.5 mm, run ≥ 0.8 mm; changed nets and critical nets)

| Pair | Base | Final |
|---|---|---|
| PYRO1_CONT – SPI1_SCK B.Cu | 7.36 mm @ 0.283 (centre-line method; pass 4 measured 0.195 at the closest) | — |
| PYRO1_CONT – SERVO1_MCU B.Cu | 2.47 @ 0.477 | — |
| BAT_SW_SOURCE – CAM_UART_OE F.Cu | 4.70 @ 0.238 | — |
| CAM_FAULT_N – SERVO4_MCU In2 | 20.11 @ 0.237 | 10.10 @ 0.237 |
| RADIO_MOSI – RADIO_SCK F.Cu | 23.36 @ 0.279 | 22.56 @ 0.325 |
| RADIO_NSS – RADIO_SCK F.Cu | 11.29 @ 0.279 | 11.25 @ 0.325 |
| NRST – PYRO1_CONT In2 | — | 1.80 @ 0.445 |
| NRST – SWCLK B.Cu | — | 3.08 @ 0.455 |
| SERVO2_MCU – SERVO4_OUT In2 | 1.98 @ 0.279 | 2.40 @ 0.491 |

Every other pair is identical or slightly shorter: SPI1_MOSI–IMU_CS, I2C1_SCL–IMU_CS 9.11 @ 0.266, RADIO_BUSY–
RADIO_NRST and QSPI_IO0–BAT_SW_RETURN. Fix pass 4 removed more coupling than it added, and none of what it added
involves a fast aggressor.

## 5. Checked and not raised

- **The band and debris redraws:**
  - All end on the same pads and vias. DRC unconnected is 0, and route_check reports no dangling copper.
  - Widths are kept (0.15 mm; LOGIC_ILIM 0.2 mm).
  - New smallest gaps (DRC-legal):
    - CAM_5V_SENSE F.Cu x 22.45 to U1.37 (LED_YEL) 0.236 mm (was 0.45);
    - I2C1_SCL to the IMU_INT1 via (26.30, 62.65) 0.265 mm (was 0.325), and to BOOT0 0.261 mm (was 0.191, better);
    - LOGIC_ILIM to LOGIC_SS 0.26 mm (was 0.30);
    - RADIO_SCK / NSS / MOSI band lanes 0.31–0.35 mm.
  - RADIO_NRST's 0.141 mm entry segment lies inside its via copper (end 0.216 mm from the via centre against
    0.25 mm radius). It is recorded as deviation D14.
- **CAM_UART_OE's In2 hop** (34.0, 58.0–60.7): it is inside the 3V3_In2 outline but in a void that existed before;
  the main 3V3 polygon is 455.47 mm² on both boards. Its vias are 1.173 and 1.231 mm from GND vias.
- **SWCLK and the crystal:** no copper change (§2). M3_R7 l.379–383 records the distances.
- **NRST via (35.80, 53.95):** 3.18 mm from the nearest GND via. NRST is not a critical signal net under AGENTS §3,
  so the 1.5 mm rule does not apply.
- **Fab outputs:** BOM and CPL byte-identical to fix pass 3 per F5. All five output hashes match the manifest, and the
  drill file matches the board (§1).
- **Renders:** `r7_top.png` / `r7_bottom.png` are stale (fix-pass-3 copper), as the handoff says. That is records,
  not copper.

## 6. Reproduction

Scratch directory `scratchpad/p5reg/` (`base.kicad_pcb`, `final.kicad_pcb`, `p3.kicad_pcb`, `r6.kicad_pcb`, each
SHA-checked):
- `dump.py` + `diff.py`: the per-net diff (§4.1);
- `isl_all.py`: fill pieces with via counts (`isl_*.json`);
- `ctx.py` / `stack.py`: pour context and stacked copper of the rerouted nets;
- `neigh.py` on `geo_*.json`: edge gaps;
- `couple.py`: parallel runs;
- `gexport.py` / `gpath.py`: GND pad returns (`gdist.json`);
- `gexp2.py` / `gfar.py`: farthest fill copper from a via;
- `padcontact.py`: pad pour contact (`pc_*.json`);
- `cr.sh`: critical reference (`cr_*.txt`);
- `dc.sh` / `dcjobs.txt`: DC (`dc_out.txt`);
- `trims.py`: rule areas;
- `viaconn.py`: GND via joins;
- gate log `gate.txt`, tests `tests.txt`.
