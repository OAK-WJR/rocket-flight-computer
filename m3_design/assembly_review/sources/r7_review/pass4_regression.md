# R7 pass 4: board-wide regression and electrical integrity (fix pass 3)

Read-only review, 2026-10-17. Dimension: every copper change of fix pass 3 (agent F4, `m3_design/r7_polish.py`),
judged against the pass-3 board and, where useful, against R6. Focus areas:
- ground returns and the critical-reference sampling;
- the 3V3 and VCAP copper;
- the DC solve of the 7.7 A paths;
- the pyro block rules and the arming break;
- anything that changed electrically and should not have;
- the schematic and netlist.

| Item | Value |
|---|---|
| Final board | `m3_design/assembly_review/m3.kicad_pcb`, SHA-256 `636a6bdc7234586a659741a3da921335a47197648c29cd9612c8374733847650`. Matches `fix3_F4_handoff.md`, M3_R7 and the fab manifest. Checked before and after this review: unchanged |
| Pass-3 board | SHA-256 `7660620cfa834e4d381d2a2638780e9a341341c9b93c6e6f526791204dc77c9c` (F4's start copy, `scratchpad/fx3/base.kicad_pcb`, SHA re-checked) |
| R6 board | `git show 3b215ba:m3_design/assembly_review/m3.kicad_pcb`, compared moved +18 mm in y |
| Schematic | `m3.kicad_sch` SHA-256 `47057f7d…` (the value the pass-3 reports cite). All sheets and `schematic.net.xml` are dated 2026-10-16 01:31, before pass 3. `m3.kicad_dru` SHA-256 `1674d58b…`, dated 2026-10-15, equal to the manifest's input |
| Gate (rerun here) | `tools/check.sh` exit 0: DRC 0, unconnected 0, parity 0, ERC 0; audit OK; silk 0; R7 contract OK; routing hygiene 0 failing, 42 allowlisted, 0 stale; actuator contract OK; fit OK |
| Tests (rerun here, KiCad Python) | test_route_check 27 OK, test_r7_check 34 OK, test_check_shell 2 OK, test_fit_check 23 OK |
| Tools | KiCad 10.0.6 `pcbnew` read-only scripts on scratch copies (`scratchpad/p4reg/`); `tools/critical_reference.py`, `tools/dc_solve.py`; the pass-3 reviewer's `gexport.py` / `gpath.py` / `islands.py` / `xor.py` (read-only copies in `scratchpad/p3reg/`) |
| Fills | Saved fills used throughout (the build scripts refill natively) |

## 1. Summary

**No Critical and no Major findings.**

What holds:
- **Netlist and parts:** unchanged. All 760 pad entries match the pass-3 board: net, position, size and zone
  connection. All 254 footprints match: FPID, position, rotation, layer, attributes, DNP, value and fields. The
  board setup header, design settings and net classes are byte-identical, and the schematic is untouched.
- **7.7 A copper:** unchanged. RAW_ACT 3.96, BAT_IN 3.91 and ACT_FET_S 1.36 mΩ on both boards (0.1 mm grid).
  BAT_IN J1 → U9 is 13.39 mΩ on both.
- **Pyro block:**
  - PYRO1_BUS, PYRO1_IGN, PYRO1_OUT, RAW_ACT, ACT_*, ARM1_* and BAT_IN copper is unchanged outside pads
    (0.0000 mm² lost or gained).
  - The arming break is intact: PYRO1_BUS = {J124.1, R132.1, R134.2}, and RAW_ACT reaches J124.2 only.
  - The SWD lines (15 + 5 tracks, 6 + 2 vias) no longer pass through the PYRO_BLOCK area.
- **GND returns:** of the 173 SMD GND pads, none is more than 0.2 mm farther (in copper) from a GND via or plated
  GND hole. Seven are nearer:
  - C160.2 4.22 → 0.24 mm, D122.1 5.62 → 1.68, C127.2 5.87 → 2.26, C60.2 3.36 → 0.37, C94.2 3.35 → 0.44,
    R127.2 4.41 → 4.12, C300.2 1.84 → 1.64.
  - In1 GND is still one polygon and grew by 31.2 mm², because SWCLK's In1 run is gone.

Fix pass 3 changed copper on nine nets only:

| Net | Tracks removed / added | Vias removed / added |
|---|---|---|
| SWCLK | 46 / 16 | 14 / 4 |
| GND | 43 / 10 | 2 / 8 |
| SWDIO | 32 / 12 | 11 / 4 |
| PYRO1_CONT | 22 / 12 | 7 / 4 |
| 3V3 | 22 / 9 | 2 / 1 |
| SERVO1_MCU | 3 / 3 | 1 / 1 |
| PYRO1_GATE_N | 4 / 1 | 0 / 0 |
| PYRO1_COLD | 2 / 2 | 0 / 0 |
| RAW_PROTECTED | 2 / 1 | 0 / 0 |

It also added the 21 `R7_POUR_TRIM_n` zone-fill keep-outs. Copper was **not** changed for:
- CAM_PWR_EN, CAM_MCU_TX, RADIO_NRST and the other corridor nets (no corridor stitching was added);
- VCAP1 and VCAP2, and the U12/C100 3V3 feed;
- SPI1_MOSI / IMU_CS (still 0.189 mm).

This matches `fix3_F4_handoff.md` §2 and R7_VALIDATION.

Four Minor items remain:

| ID | Severity | One line |
|---|---|---|
| P4-REGRESSION-01 | Minor | PYRO1_CONT's new In2 run splits the 3V3 In2 island under HSE_IN and U1.100 into 41.9 mm² (3 vias) and a 22.7 mm² fragment on 1 via. Six B.Cu nets cross the split; only SPI1_SCK's 215 samples are recorded. The new route also runs 7.4 mm beside SPI1_SCK at 0.195 mm and passes PYRO1_GATE_N's via at 0.191 mm. Not recorded |
| P4-REGRESSION-02 | Minor | The pour-trim keep-outs took all pour contact from five GND pads: C7.2 (the AP63203 buck's input capacitor), C150.2, C30.2, C31.2 and R64.2. Each keeps its track and its copper path to a GND via is unchanged, but C7.2 lost the parallel pour around the buck's input loop. `r7_polish`'s invariant (pad groups) cannot see this. Not recorded |
| P4-REGRESSION-03 | Minor | Side effects of the SWD reroute, not recorded. SWCLK's via is now 1.10 mm from the crystal's HSE_OUT pad (was 2.16), and its B.Cu run passes 0.74 mm from Y1's courtyard on Y1's own layer. The new SWD copper splits the B.Cu GND pour: 32 → 39 polygons, and the crystal / U1 region becomes a separate 133 mm² island. All pieces are via-stitched and SWD is idle in flight, so the effect is negligible (Inference) |
| P4-REGRESSION-04 | Minor | Record precision, three items. (a) P3-REGRESSION-05's "0.232 mm" is the parallel-run gap; the closest approach is 0.200 mm (BAT_SW_RETURN via to QSPI_IO0), unchanged since pass 3. (b) P3-REGRESSION-02's "about 2.5 mm" for D122.1 measures 1.68 mm. (c) M3_R7 says the L1.2 node redraw is within the DC method's resolution, but it lengthened C9's (buck output capacitor) connection: L1.2 → C9.1 goes from 1.67 to 2.48 mΩ |

## 2. Pass-3 findings in this dimension: closure check

| Pass-3 ID | Disposition in R7_VALIDATION | Verified on the final board |
|---|---|---|
| P3-REGRESSION-01 (SPI1_MOSI 0.189 mm × 14.8 mm beside IMU_CS) | Recorded deviation (three more vias would have to move) | **Properly dispositioned.** Copper unchanged; the gap is still 0.189 mm. Recorded in M3_R7 §"Close adjacencies kept" with F4's measured reason. The GND sliver between MISO and MOSI is gone (`R7_POUR_TRIM_4`, F.Cu (23.08–29.21, 66.5–72.68)) |
| P3-REGRESSION-02 (D122.1 / C160.2 GND return) | Fixed | **Closed.** GND via (35.5, 29.4), Ø0.5 / 0.3 mm, joined to C160.2 by F.Cu (34.98, 28.88)→(35.5, 29.4), 0.2 mm. Copper path to a GND via: C160.2 4.22 → **0.24 mm**, D122.1 5.62 → **1.68 mm**. The record says "about 2.5 mm" (P4-REGRESSION-04) |
| P3-REGRESSION-03 (stale records) | Fixed (record) | **Closed.** J123.1 to CAM_5V B.Cu (34.23, 32.2)→(35.48, 33.45) measures 0.350 mm. R7_VALIDATION, M3_R7 §"Return paths" and STATUS l.82 give the 864 lost samples and where they are |
| P3-REGRESSION-04 (DC grid accuracy, missing power-net table) | Fixed (record) | **Closed.** M3_R7 §"DC solve" gives the grid, its resolution and the power-net table. Spot checks agree with the table to its quoted digits (§4.4). The optional width-mismatch warning in `dc_solve.py` was not added, as recorded |
| P3-REGRESSION-05 (QSPI_IO0 / RADIO_NSS beside BAT_SW_RETURN) | Recorded deviation | **Properly dispositioned.** Copper unchanged: QSPI_IO0 0.232 mm over about 6 mm, RADIO_NSS 0.175 mm. The closest IO0 approach is 0.200 mm at BAT_SW_RETURN's via, not 0.232 (P4-REGRESSION-04) |

## 3. Findings

| ID | Severity | Requirement | Finding | Evidence (final-board coordinates, mm) | Fix |
|---|---|---|---|---|---|
| P4-REGRESSION-01 | Minor | AGENTS.md §3 (SPI/IMU is critical; return paths); M3_R7 §"Return paths" record accuracy; FMEA F-18 (SPI1 is "the one bus that can kill the vehicle") | F4 kept a 4-via PYRO1_CONT route whose In2 diagonal cuts the 3V3 In2 island under the MCU and IMU area in two, and recorded only the 261 lost R6-method samples. Three effects are not recorded. (a) The island that HSE_IN references shrinks from 72.15 mm² with 4 vias to 41.93 mm² with 3, and a 22.69 mm² fragment is left on a single via. (b) Five more B.Cu nets cross the cut. (c) There are three new close adjacencies on critical nets. F4 rejected the CAM_MCU_TX candidate for splitting the 3V3 plane, and the 6-via PYRO1_CONT route that keeps this island whole (`fx3/rt/pc_route2.json`) exists. Inference: at SPI1's 12.5 MHz (MARGIN_PRESCRIPTION) and with SPI1_SCK already 21.6 mm over In2 voids, the SI cost is small. A PYRO1_CONT–PYRO1_GATE_N fabrication short would put at most about 0.9 V on the gate at the 19.9 V clamp (divider Thevenin 0.91 kΩ against R127 1 kΩ, then R126/R128), and JLC's E-test would catch the short. Rule G covers gate nets only inside PYRO_BLOCK, by design | **In2 run:** PYRO1_CONT In2 (29.93, 61.55)→(23.98, 67.5)→(23.98, 68.65), 0.15 mm; vias (29.93, 61.55), (23.98, 68.65). 3V3_In2 fill: pass-3 7 polygons / 564.07 mm², final 6 / 555.51 mm². The island at (22.10–31.69, 51.24–70.20), 72.15 mm², vias (27.9, 56.3), (27.85, 62.75), (30.7, 57.18), (30.17, 65.1), becomes (22.10–31.69, 51.24–67.91) 41.93 mm² with 3 vias, plus (24.31–31.55, 59.48–68.62) 22.69 mm² with only via (30.17, 65.1). **Crossings** (B.Cu centre-line stretches referenced to In2 GND/3V3/3V3A on the pass-3 board, unreferenced on the final, 0.02 mm sampling): SPI1_SCK 0.68 (23.82, 67.22)–(24.29, 67.69) (recorded); IMU_INT1 0.92 at x 26.30, y 64.74–65.64; SERVO1_MCU 0.78 at x 28.50, y 62.66–63.43; SERVO2_MCU 0.92 at x 25.70, y 65.34–66.24; I2C1_SDA 4 stretches totalling 0.50 at x 29.05, y 61.89–62.93. **Adjacencies:** PYRO1_CONT B.Cu (24.68, 68.65)→(27.48, 71.45)→(27.48, 76.9) runs beside SPI1_SCK B.Cu (22.25, 65.65)→(27.85, 71.25)→(27.85, 74.85) for 7.36 mm at 0.195–0.228 mm edge gap (pass 3: none within 0.35 mm). PYRO1_CONT F.Cu (33.98, 57.95)→(30.38, 61.55) passes the PYRO1_GATE_N via (31.90, 59.23) at 0.191 mm. The PYRO1_CONT via (23.98, 68.65) is 0.194 mm from SPI1_MISO F.Cu (22.85, 66.75)→(28.55, 72.45). Critical reference, pass-3 → final: 261 lost (SPI1_SCK B.Cu 215, SPI1_MISO F.Cu 46); R6 → final 864 / 1,122, reproduced | Take the 6-via route that keeps the island whole, or another path that does not split the island. Its former In2 run, at x 34.0–34.5 beside CAM_5V_In2, did not split it. Otherwise record in M3_R7 §"Return paths" and §"Close adjacencies kept": the island split and its one-via fragment, the five extra crossings, the 7.4 mm SPI1_SCK adjacency and the 0.191 mm PYRO1_GATE_N approach, with the 4-versus-6-via trade-off |
| P4-REGRESSION-02 | Minor | AGENTS.md §3 / M2 (pads connect per the house thermal-relief policy, `m3.kicad_dru` "Small GND pad thermal relief"); Diodes AP63203 layout guidance (input capacitor tight to VIN/GND, Inference: datasheet not re-read in this pass); `r7_polish` invariant claims | `pour_trim` makes each keep-out from a whole fill piece found by the sliver/finger scan. Where that piece also carried a pad's thermal spokes, the pad lost all pour contact. KiCad reports nothing, because the pour no longer reaches the pad; it is not a starved thermal. The build's invariant (pad groups with pours unchanged) holds because every such pad also has a track. Five GND pads on B.Cu lost all pour contact (none on other layers or nets). The worst is **C7.2**, GND of C7, the 22 µF input capacitor of U2 (AP63203WU-7, 1.1 MHz buck), in the converter's hot loop. Its direct 0.5 mm track to U2.4 is unchanged, so the main loop path and the pad-to-via copper distance (0.84 mm) are the same, but the pour that ran beside the loop and joined C7.2 to U2.4 a second way is gone. The others: C150.2 (22 µF RAW_ACT bulk), C30.2 and C31.2 (3V3A 100 nF at U4/U5), and R64.2. Their copper path to a GND via changed by ≤ +0.02 mm. Inference: the electrical effect is small (a parallel return lost; the direct paths remain). It is unrecorded, and the trim generator has no per-pad guard | Fill contact within 0.05 mm of the pad outline (outside the pad), pass-3 → final: C7.2 0.060 → 0, C150.2 0.060 → 0, C30.2 0.015 → 0, C31.2 0.030 → 0, R64.2 0.030 → 0 mm². There are 261 pad/layer entries with a same-net fill. Of the other 256, all but three change by < 0.002 mm²; the three are J122.3 In1 (+0.037), C127.2 F.Cu (+0.015) and U1.26 F.Cu (−0.006). Trims involved: `R7_POUR_TRIM_21` B.Cu (19.87–21.97, 31.39–35.37), whose outline follows C7.2's spoke ring at x 20.63/20.97, y 33.07–34.94; `R7_POUR_TRIM_8` B.Cu (12.96–16.96, 85.60–87.93); `R7_POUR_TRIM_11` B.Cu (35.84–39.97, 75.08–78.82). GND_B fill in (19.0–23.0, 30.5–36.0): the piece holding U2.4 and C7.2 goes from 7.428 to 3.329 mm², and C7.2 drops out of the island (pass-3 island #27 {U2.4, C7.2}, via (19.5, 35.2); final #35 {U2.4}). Tracks: GND B.Cu (20.6, 34.2)→(19.0, 34.2) 0.5 mm, VLOGIC B.Cu (20.6, 31.8)→(19.0, 31.8) 0.5 mm, unchanged | Make `pour_trim` subtract a ring around every same-net pad (for example, the pad plus thermal gap plus spoke length) from each keep-out, and add a gated check that no pad with a THERMAL or SOLID zone connection loses its last pour contact (test: a finger carrying a pad's spokes). Regenerate. Or record the five pads in M3_R7 with the measured numbers |
| P4-REGRESSION-03 | Minor | AGENTS.md §3 (crystal is a critical net; GND returns); ST AN2867 crystal-layout practice (signals kept away from the oscillator; Inference, not re-read this pass); `fix3_F4_handoff.md` "crystal kept clear" | The SWD reroute moved SWCLK closer to the HSE crystal and split the B.Cu GND pour. In flight SWCLK/SWDIO are idle (no debugger; PA14 pull-down, PA13 pull-up), so a coupling effect is limited to bench debugging (Inference). The splits leave all pieces stitched to the solid In1 GND, so the returns are unchanged (§4.2). Neither the crystal distance nor the pour split is recorded; the handoff says "crystal kept clear" without a number | **Crystal:** the SWCLK via (24.70, 50.95) is 1.10 mm (edge to edge) from Y1.3 (HSE_OUT); on the pass-3 board the nearest SWCLK copper was 2.16 mm from HSE_OUT. The SWCLK B.Cu run (20.5, 52.95)→(22.5, 50.95)→(24.7, 50.95) is on Y1's layer (Y1 is on B.Cu at (25.6, 53.75)), 0.74 mm from Y1's courtyard (y 51.76) and about 0.43 mm from C26's (HSE_OUT load capacitor). HSE_IN and HSE_OUT copper and their In2 reference samples are unchanged (0 lost). **Pour:** GND_B goes from 32 polygons / 3207.06 mm² to 39 / 3212.92 mm². The main B.Cu pour (pass 3: 1588.5 mm², 263 vias) breaks into 1127.5 mm² (213 vias), 242.9 mm² (21 vias; C16.2, C19.2 = VCAP1) and 133.2 mm² (27 vias; Y1.2, Y1.4, C26.2, C15.2, C85.2, D4.2), plus small pieces. Several of those pieces are 1-via, for example (30.25–31.07, 59.86–61.54) and (18.78–22.89, 61.80–66.37). GND_F goes from 39 to 43 polygons; the F.Cu pour under U1 loses a 13.5 mm² piece, (20.67–23.60, 52.96–60.18), 3 vias. No GND polygon is without a via or plated GND hole. **Other new SWCLK neighbours:** NRST via (30.82, 46.19) 0.22 mm; QSPI_NCS F.Cu 0.251 mm from SWCLK via (20.5, 52.95); BUZZ_DRV via 0.177 mm | Record in M3_R7 §"Rerouted in fix pass 3": SWCLK's distance to Y1/C26 and the B.Cu pour split. Optionally keep SWCLK's crystal-side segment on F.Cu, or move its via (24.7, 50.95) ≥ 2 mm from Y1.3 |
| P4-REGRESSION-04 | Minor | AGENTS.md §3 (records state what was verified); R7_VALIDATION and M3_R7 accuracy | Two pass-3 dispositions quote numbers that differ from the board. M3_R7 §"DC solve" also files the L1.2 node redraw under "within the method's resolution", although it lengthened the buck output capacitor C9's connection by about half. None changes a conclusion (Inference for (c): about 1 nH more in series with C9, while C8 stays on L1.2's pad) | (a) P3-REGRESSION-05 and M3_R7 §"Close adjacencies kept" give QSPI_IO0 at "0.232 mm" from BAT_SW_RETURN. That is the parallel F.Cu run. QSPI_IO0 F.Cu (15.6, 36.9)→(15.6, 40.3) also passes between BAT_SW_RETURN's vias (15.0, 37.725) and (16.3, 37.725), both Ø0.6 mm, where BAT_SW_RETURN crosses beneath on In2, at **0.200 / 0.300 mm**. The In2 crossing keeps In1 GND under IO0. Unchanged since pass 3. (b) P3-REGRESSION-02 / M3_R7 §"Return paths": "D122.1 … about 2.5 mm of copper, C160.2 … 0.7 mm". The copper path from the pad outline to the via, 0.05 mm geodesic over F.Cu GND copper, is **1.68 mm** and **0.24 mm**; 0.7 mm is the C160.2 centre-to-via distance. (c) M3_R7 §"DC solve": "Fix pass 3's 3V3 changes (the L1.2 node, dead 3V3 runs) are within the method's resolution". The same-grid (0.1 mm) solve gives 3V3 L1:2 → C9:1 **1.67 → 2.48 mΩ** (pass-3 → final). Pass-3 board: C9.1 (24.1, 36.6) → 45° 0.6 mm B.Cu straight into L1.2's pad at (26.0, 34.7). Final: (24.1, 36.6)→(25.2, 36.6)→(25.7, 36.1)→(26.4, 36.1), then up the vertical (26.4, 36.6)→(26.4, 33.3) to the pad. That is about 3.9 mm of track to the pad edge, against about 2.6 mm before. The load paths change by ≤ +0.20 mΩ (§4.4). The pass-3 report's "C9.1 connects straight to L1.2" no longer holds | Quote 0.200 mm (via) beside 0.232 mm (run) for (a). For (b), state the method, or quote 1.68 / 0.24 mm. For (c), state in M3_R7 that the redraw lengthened C9's connection (L1.2 → C9.1 1.67 → 2.48 mΩ, 0.1 mm grid). Optionally give C9.1 a direct 45° link into L1.2's pad again, if the tidiness rule allows a pad entry off the centre line |

## 4. Measurements

### 4.1 What changed (pass-3 board → final, exact track and via geometry)

- Tracks 1946 → 1836 (176 removed, 66 added); vias 709 → 694 (37 removed, 22 added); zones 31 → 52 (the 21
  `R7_POUR_TRIM_n` rule areas, zone fills only, F.Cu 7 and B.Cu 14).
- **3V3:**
  - L1.2 node: two B.Cu 0.6 mm links and the via (24.2, 35.3) removed. C9.1 now joins the vertical
    (26.4, 33.3)→(26.4, 36.6) at (26.4, 36.1), instead of entering L1.2's pad directly.
  - Five dead In2 3V3 runs removed; all lie inside the 3V3 plane, and the pad groups are unchanged.
  - C17.1 square; the R164 branch merged; the J2.1 feed via (41.135, 77.92) Ø0.6 becomes (41.0, 77.92) Ø0.5.
- **GND:**
  - 43 tracks removed, all dead under the pour-island rule (both ends in one island). None was the shortest path
    for any pad (§4.2).
  - New vias: (35.5, 29.4) at C160; (23.68, 69.55) and (29.28, 77.95) for PYRO1_CONT; three strip stitches at
    (11.975, 21.575), (9.025, 8.325) and (25.025, 8.525). Two vias nudged: (19.65, 30.55) → (19.71, 30.51) and
    (3.3, 50.4) → (3.26, 50.44).
  - Neck: B.Cu (13.7, 80.6)–(14.6, 80.6) 0.25 → 0.2 mm.
- **RAW_PROTECTED:** D9.1's 45° exit moved from the pad centre (14.0, 31.2) to (14.5, 31.2), inside the pad, and
  the short horizontal was removed (0.6 mm, same via).
- **SERVO1_MCU:** via (34.6, 58.7) → (34.6, 58.5).
- **PYRO1_GATE_N:** one straight F.Cu run at x 21.9, (21.9, 88.83)→(21.9, 90.4). Outside-pad copper −0.098 /
  +0.066 mm².
- **PYRO1_COLD:** R131.2 → north → 45° into D120.1. Copper −0.119 / +0.072 mm².
- **SWCLK, SWDIO, PYRO1_CONT:** rerouted (M3_R7 §"Rerouted in fix pass 3"; lengths not re-measured here).

### 4.2 GND returns

Method: the copper path from each SMD GND pad's outline to the nearest GND via or plated GND hole. It is a 0.05 mm
geodesic search over F.Cu or B.Cu GND copper (fills, tracks, pads), the same script the pass-3 reviewer used.

- **173 pads:** none longer by more than 0.2 mm; seven shorter (§1).
- **U1 decoupling and VCAP pads, unchanged:**
  - C19.2 0.89, C20.2 2.90, C13.2 2.02, C14.2 1.89, C15.2 1.15, C16.2 0.90, C17.2 0.35, C18.2 1.15, C21.2 2.56;
  - C100.2 0.94, U12.2 2.05;
  - crystal C25.2 1.49, C26.2 0.25;
  - buck C7.2 0.84, C8.2 0.46, C9.2 0.65, U2.4 0.28 mm.
- **GND pour pieces:** every piece on F.Cu and B.Cu holds at least one GND via. On the pass-3 board two F.Cu
  pieces held only J122's GND pins; on the final board none is via-less. Splits: P4-REGRESSION-03.
- **Pour contact per pad:** P4-REGRESSION-02.

### 4.3 Critical-net reference (`tools/critical_reference.py`)

| Comparison | Lost (base-referenced samples unreferenced on the candidate) | Candidate-new |
|---|---:|---:|
| R6 (+18 mm) → final, R6 method | 864 | 1,122 |
| R6 (+18 mm) → final, extended | 1,440 | 4,020 |
| Pass-3 → final, R6 method | 261 (SPI1_SCK B.Cu 215 at (23.74–24.34, 67.14–67.84); SPI1_MISO F.Cu 46 at (24.14–24.46, 68.18–68.50)) | 261 |
| Pass-3 → final, extended | 947 (adds 320 SWCLK F.Cu and 366 SWDIO In1 samples on copper that no longer exists) | 2,303 (new SWD copper over via antipads and In2 voids) |

- F4's numbers reproduce exactly.
- **In2 polygon under the critical B.Cu runs:**
  - HSE_IN 3.2 mm over the reduced 41.9 mm² island (P4-REGRESSION-01);
  - QSPI_NCS / IO0 / IO1 / IO3 over the main 3V3 polygon (455.5 mm², 11 vias), as on pass 3;
  - USB_DP 16.76 mm over the main polygon, unchanged.
- **Unreferenced F/B lengths per net, pass-3 → final (0.02 mm sampling):**
  - Better: SWCLK B 12.70 → 4.54, SWCLK F 6.61 → 2.29, SWDIO F 3.18 → 1.18, USB_FAULT_N F 5.42 → 1.13,
    BAT_FAULT_N F 2.66 → 1.70 (In1 restored where SWCLK's In1 run was).
  - Worse: SPI1_SCK B 20.86 → 21.56, IMU_INT1 B 16.04 → 16.96, SERVO1_MCU B +0.80, SERVO2_MCU B +1.28,
    I2C1_SDA B 11.43 → 14.26.
  - I2C1_SDA's increase includes 2.26 mm over the 8.54 mm² via-less 3V3 island at (27.43–31.55, 67.93–70.20),
    which the pass-3 review noted. It is gone on the final board. A via-less island is no real reference, so that
    part is no loss.
- **Layer changes of the rerouted nets** (nearest GND via, centre to centre):
  - PYRO1_CONT (23.98, 68.65) 0.95, (33.98, 57.95) 1.19, (29.23, 78.65) 0.70, (29.93, 61.55) 1.49: all ≤ 1.5 mm,
    as the gate requires.
  - SWCLK 1.74–2.57 and SWDIO 1.71–5.50: the SWD nets are not in the AGENTS §3 critical list.

### 4.4 DC solves (`tools/dc_solve.py`, 35 µm, 20 µm plating, 20 °C)

| Path | Grid | Pass-3 board | Final | M3_R7 table (final) |
|---|---|---:|---:|---:|
| RAW_ACT Q121:5–9 → J122:2,5,8,11 (7.7 A) | 0.1 | 3.96 | **3.96** (30.5 mV, 0.235 W) | 3.96 |
| BAT_IN J1:1 → Q120:5–9 (7.7 A) | 0.1 | 3.91 | **3.91** (30.1 mV, 0.232 W) | 3.91 |
| ACT_FET_S Q120:1–3 → Q121:1–3 (7.7 A) | 0.1 | 1.36 | **1.36** (10.4 mV, 0.080 W) | 1.36 |
| BAT_IN J1:1 → U9:5 (1 A) | 0.1 | 13.39 | 13.39 | 13.4 |
| RAW_PROTECTED U9:6 → U11:2 | 0.05 | 36.33 | 36.35 | 36.4 |
| CAM_5V L3:2 → J9:1 | 0.1 | 24.95 | 24.74 | 24.7 |
| 3V3 L1:2 → U1:75 | 0.1 | 14.25 | 14.25 | 14.2 |
| 3V3 L1:2 → FB31:1 (radio feed) | 0.1 | 13.61 | 13.80 (+1.4 %) | 13.8 |
| 3V3 L1:2 → FB30:1 (GNSS feed) | 0.1 | 5.06 | 5.26 (+4 %) | 5.26 |
| 3V3 L1:2 → U1:27 | 0.1 | 6.33 | 6.46 (+2 %) | 6.46 |
| 3V3 L1:2 → U3:8 (QSPI flash) | 0.1 | 6.40 | 6.60 (+3 %) | 6.60 |
| **3V3 L1:2 → C9:1** (buck output capacitor, 0.6 mm tracks) | 0.1 | 1.67 | **2.48 (+49 %)** | not given |

Values in mΩ. Same-grid differences between the two boards are the meaningful ones; M3_R7 gives the grid
resolution (about ±2 % on pours, ±5 % on track-limited paths).
- The 3V3 load paths move by at most +0.20 mΩ, about 0.02 mV at their currents. They agree with F4's
  four-decimal values (FB30 5.0599 → 5.2594, U1.27 6.3262 → 6.4579, FB31 13.6137 → 13.8039).
- The L1:2 → C9:1 rise comes from the L1.2 node redraw: C9.1 no longer enters L1.2's pad directly (§4.1). It is
  well outside the grid's resolution (P4-REGRESSION-04 (c)).
- 0.05 mm solves were not repeated here; M3_R7 lists them for the final board.

### 4.5 Pyro block, arming break and DRC rules

- `m3.kicad_dru` is unchanged (2026-10-15, SHA equal to the manifest's input). `check_actuators` passes in the
  gate. The DRC passes all nine pyro rules.
- **Copper outside pads, pass-3 → final** (polygon XOR of tracks and vias minus the net's pads):
  - PYRO1_BUS, PYRO1_IGN, PYRO1_OUT, RAW_ACT, ACT_FET_S, ACT_GATE, ACT_DRV, ARM1_SENSE, ARM1_SENSE_MID,
    PYRO1_CONT_MID, RAW_ACT_SENSE(_MID), PYRO1_GATE and BAT_IN: **0 mm²**.
  - PYRO1_GATE_N and PYRO1_COLD: the redraws above.
- **Arming break:** PYRO1_BUS = {J124.1, R132.1, R134.2}, PYRO1_IGN = {J121.2, R134.1}, and RAW_ACT reaches J124.2
  only. All unchanged; no test point was added.
- **New pyro-net neighbours (≤ 1.0 mm):**
  - PYRO1_COLD to PYRO1_OUT (R131.1) 0.477 mm (rule C 0.3); PYRO1_COLD to GND 0.151 → 0.62 mm.
  - PYRO1_CONT to PYRO1_OUT 0.751 and to PYRO1_CONT_MID 0.477 mm, unchanged; no RAW_ACT within 1.0 mm (rule A
    0.5).
  - PYRO1_CONT to PYRO1_COLD 0.315 mm (no rule between two sense nets).
  - New digital neighbours of PYRO1_CONT outside the block: P4-REGRESSION-01.
- **Nets with copper inside PYRO_BLOCK** (4.0–42.0, 84.0–114.4): unchanged, except that SWCLK and SWDIO left the
  block, and PYRO1_CONT, PYRO1_GATE_N and GND have fewer items there.

### 4.6 Close parallel coupling (same layer, edge gap ≤ 0.35 mm, run ≥ 1 mm; critical, SWD and pyro nets)

| Pair | Pass-3 board | Final |
|---|---|---|
| PYRO1_CONT – SPI1_SCK B.Cu | — | 7.36 mm @ 0.195 (P4-REGRESSION-01) |
| BUZZ_DRV – SWCLK F.Cu | — | 2.76 @ 0.274 |
| SWCLK – SWDIO F.Cu | 3.96 @ 0.204 | — |
| CAM_FAULT_N – SWCLK F.Cu | 5.7 @ 0.216 | — |
| PYRO1_CONT – SWDIO F.Cu | 0.68 @ 0.172 | — |

Every other pair from the pass-3 table is identical: SPI1_MOSI–IMU_CS 14.81 @ 0.189, QSPI_IO0–BAT_SW_RETURN
5.92 @ 0.232, QSPI_CLK–RADIO_RXEN 4.38 @ 0.25.

## 5. Checked and not raised

- **SWDIO's In2 run between J122's rows** ((18.55, 73.1)→(26.7, 73.1)) passes J122.11, a RAW_ACT pin (Ø1.6 mm pad,
  1.1 mm drill, flashed on In2), at a 0.335 mm copper gap (hole wall about 0.59 mm), and J122.8 (RAW_ACT) at
  0.455 mm.
  - It is DRC-legal and inner-layer, and the pads are flashed. An inner short would need a fabrication defect that
    JLC's E-test screens.
  - Recorded here because SWDIO is a direct MCU pin (PA13).
  - The run also cuts the main 3V3 In2 polygon near its south edge without splitting it; the main polygon grew from
    434.8 to 455.5 mm² by absorbing the HSE-checkpoint island.
- **The L1.2 node redraw:**
  - C9.1 (22 µF output capacitor) now reaches L1.2's pad over about 3.9 mm of 0.6 mm track (was about 2.6 mm,
    direct into the pad). L1:2 → C9:1 goes from 1.67 to 2.48 mΩ (§4.4); the record gap is P4-REGRESSION-04 (c).
  - Inference: the buck's hot loop is on the input side (C7 to U2 pins 3 and 4, P4-REGRESSION-02). The output
    capacitor carries the inductor's continuous current, and C8 stays on L1.2's pad, so about 1 nH more in series
    with C9 is immaterial.
- **The 3V3 J2.1 via, now 0.5 mm:** carries only the debugger's VTref.
- **The RF strip's three new stitching vias:** GND only, inside the strip's GND-only In1/In2. The RF effect is the RF
  reviewer's.
- **The new PYRO1_CONT GND return vias** (23.68, 69.55) and (29.28, 77.95) lie outside PYRO_BLOCK and pass DRC.
- **Fab package:** the manifest binds `636a6bdc…` and DRU `1674d58b…`; BOM `3a0c2f12…` and CPL `c68dc2cb…` as
  F4 states.
- **Inconsistencies in `fix3_F4_handoff.md`:**
  - It says the router replay `r7_reroute_session.json` is "unchanged", but the file does not exist, and M3_R7 and
    `r7_build.sh` correctly say no session is replayed.
  - It says "In2 run inside the BAT_IN servo pour" for PYRO1_CONT's old route. The R6_BAT_IN_In2 fill is unchanged
    (770.761 mm²); the old In2 runs lay in CAM_5V_In2, which grew 138.35 → 139.26 mm².
  - Neither is a controlled record.

## 6. Sources

- `docs/REQUIREMENTS.md` F4, F8, M2; `AGENTS.md` §2–3; `docs/M3_R7.md` §"R7 board", §"Rerouted in fix pass 3",
  §"Close adjacencies kept", §"Routing hygiene", §"Return paths", §"DC solve"; `docs/R7_VALIDATION.md` (pass-3
  rows); `STATUS.md`.
- `sources/r7_review/fix3_F4_handoff.md`, `fix3_F4_progress.md`, `fix3_docs_handoff.md`, `pass3_regression.md`,
  `pass3_verdicts.json`.
- `docs/MARGIN_PRESCRIPTION.md` (SPI1 12.5 MHz); `docs/FMEA_REDUNDANCY.md` F-18; BOM `fab/m3_bom_jlc.csv`
  (U2 AP63203WU-7 C780769, C7 22 µF CL21A226MAQNNNE, Q124 AON7524, U4 LSM6DSV320X).
- Board stackup (`m3.kicad_pcb`): In1 0.203 mm below F.Cu, In2 1.03 mm core below In1 (`dc_solve.py` Z table).

## 7. Inferences (not measured, or not checked against a primary source)

- Every SI, crosstalk and loop-inductance remark in P4-REGRESSION-01/02/03 and §5 is an order-of-magnitude
  estimate, with no field solve and no bench data.
- The AP63203 and ST AN2867 layout guidance is cited from general knowledge and was not re-read in this pass.
- The PYRO1_CONT–PYRO1_GATE_N bridge voltage uses schematic values (R129 + R173 = 10.2 kΩ, R130 ∥ R178 = 1 kΩ,
  R127 1 kΩ, R126 220 Ω, R128 10 kΩ). The AON7524 threshold was not re-read.
- That SWD is idle in flight assumes firmware leaves PA13/PA14 in their reset SWD function with no debugger
  attached.
