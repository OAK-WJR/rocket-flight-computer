# R7 pass 3: board-wide regression versus R6 and versus the pass-2 board

Read-only review, 2026-10-17. Dimension: every copper change the pass-2 fix agents made (F1, F2, F3), judged against
the R6 board and the pass-2 board. Focus areas:
- QSPI return path and the critical-reference sampling;
- BUZZ_DRV, BAT_FAULT_N and BAT_ILIM;
- the F2 redrawn nets;
- the F3 hygiene canonicalisation of R6 copper, including PYRO1_GATE and the power nets;
- ground returns of QSPI, HSE, SPI1/IMU, USB and SWD;
- the 3V3 plane, the high-current copper and its DC solve;
- the pyro block rules and the arming break.

| Item | Value |
|---|---|
| Final board | `m3_design/assembly_review/m3.kicad_pcb`, SHA-256 `7660620cfa834e4d381d2a2638780e9a341341c9b93c6e6f526791204dc77c9c`. Checked before and after this review: unchanged |
| Pass-2 board | SHA-256 `03fe75720f46…aa86d54` (reviewers' read-only copy, `scratchpad/rg/r7.kicad_pcb`) |
| R6 board | `git show 3b215ba:m3_design/assembly_review/m3.kicad_pcb`, SHA-256 `184a87e8…c856680`, compared moved +18 mm in y |
| Tools | KiCad 10.0.6 `pcbnew` (read-only scripts on scratch copies); `tools/critical_reference.py`, `tools/dc_solve.py`, `tools/route_check.py`; `tools/check.sh` |
| Gate (rerun here) | `tools/check.sh` exit 0: DRC 0, unconnected 0, parity 0, ERC 0; audit OK; silk 0; R7 contract OK; routing hygiene 0 failing, 20 allowlisted, 0 stale; actuator contract OK; fit OK |
| Tests (rerun here, KiCad Python) | test_route_check 19, test_r7_check 28, test_check_shell 2, test_fab_validation 23, test_r6_check 17: all OK |
| Fills | Saved fills used throughout. The build scripts refill natively. |

## 1. Summary

**No Critical and no Major findings.** The fix pass closes every pass-2 regression finding in substance.
- **7.7 A copper:** RAW_ACT 3.96, BAT_IN 3.91 and ACT_FET_S 1.36 mΩ, reproduced, equal to R6.
- **CH1 pyro copper** (bus, igniter, drain) is unchanged outside its pads. The arming break is intact.
- **DRC rules:** `m3.kicad_dru` is byte-identical to the pass-2 board.
- **QSPI and USB:** every QSPI and USB critical via now has a GND via within 1.5 mm. QSPI_IO0/IO1 lose their
  reference only at their own via antipads. USB_DP's In2 reference is restored.
- **3V3 to U1.75:** 42.85 → 14.25 mΩ (R6 21.93).
- **Local GND returns:** the three pass-2 returns are now better than R6.

The F3 hygiene stage removed 1,388 tracks and 74 vias and added 557 tracks and 84 vias. It introduced no electrical
regression larger than a few mΩ or a few tenths of a millimetre. Five Minor items remain:

| ID | Severity | One line |
|---|---|---|
| P3-REGRESSION-01 | Minor | F3's SPI1_MOSI straightening puts it 0.189 mm from IMU_CS for 14.8 mm. Before: 0.366 mm for about 12 mm, 0.189 mm for 2.5 mm |
| P3-REGRESSION-02 | Minor | F2 removed C160.2's GND trace. The pull-pin clamp's GND return (D122.1) went from 3.32 to 5.62 mm. Not recorded |
| P3-REGRESSION-03 | Minor | Stale records: J123.1 to CAM_5V is now 0.350 mm, not 0.20 mm (R7_VALIDATION, STATUS). The "603 lost, all at vias" wording is imprecise |
| P3-REGRESSION-04 | Minor | dc_solve's 0.1 mm grid swings ±10 % on 0.2 mm tracks. The records quote 4-decimal deltas below that. Changed power nets other than 3V3 have no recorded solve |
| P3-REGRESSION-05 | Minor | The off-board BAT_SW_RETURN harness line runs 5.9 mm parallel at 0.232 mm to QSPI_IO0 (since step B). Neither pass 2 nor the records mention it |

## 2. Pass-2 findings in this dimension: closure check

| Pass-2 ID | Disposition in R7_VALIDATION | Verified on the final board |
|---|---|---|
| REGRESSION-01 (Major → Minor ×3) | Fixed; 603 lost | **Closed.** Details below the table |
| REGRESSION-02 | Fixed | **Closed.** Details below the table |
| REGRESSION-03 | Fixed | **Closed.** Details below the table |
| REGRESSION-04 | Fixed | **Closed.** `route_check` reports 0 failing. The BAT_SW_RETURN hook, VLOGIC_SENSE wedge, PULLPIN hook, BAT_ILIM double path and CAM_MCU_TX micro-segments are all gone |
| REGRESSION-05 | Partly fixed; "J123.1 pad 0.20 mm from CAM_5V, open" | **Route closed; record stale (P3-REGRESSION-03).** Details below the table |
| REGRESSION-06 | Partly fixed; 10 allowlisted | No change found by this review; owned by the routing reviewers |
| REGRESSION-07 | Fixed | **Closed.** Reproduced 3.96 / 3.91 / 1.36 mΩ (§4.5) |
| REGRESSION-08 | Fixed | **Closed.** Details below the table |

**REGRESSION-01 (QSPI_IO0/IO1 return path):**
- GND vias at the layer changes:
  - QSPI_IO0 (12.9, 44.4) and (15.55, 50.85): nearest GND via 0.78 mm each (pass 2: 3.55 / 1.61);
  - QSPI_IO1 (13.0, 51.5): 1.50 mm (pass 2: 3.64; R6: 2.22).
- BAT_FAULT_N runs on In2 at x 12.3, y 42.1–56.2, west of IO0's B.Cu at x 12.9, and no longer crosses under IO0 or
  IO1.
- BUZZ_DRV is 1.098 mm (edge) from QSPI_IO1. The two B.Cu diagonals have centre lines x+y = 69.9 and 68.1, 1.27 mm
  apart, and run side by side for about 4.3 mm.
- Centre-line sampling: QSPI_IO0 and IO1 are unreferenced only within 0.28 mm of their own vias (antipads).
- The R6-method numbers reproduce exactly: 603 lost and 861 candidate-new; extended set 874 / 2,659.
- Residual (not raised separately):
  - IO0's B.Cu west edge (x 12.8) is 0.175 mm from the edge of the In2 3V3 slot that BAT_FAULT_N leaves
    (x 11.975–12.625). Inference: about 20 % of a B.Cu trace's return-current spread lies beyond 0.275 mm at
    h = 0.203 mm. This is the position pass 2 asked for (x ≤ 12.4).

**REGRESSION-02 (USB_DP, U1.75, NRST):**
- USB_DP B.Cu (11.95, 58.45–59.91) is referenced again: the centre-line stretch is gone.
- 3V3 L1.2 → U1.75: 14.25 mΩ, reproduced (pass 2: 42.85).
- NRST's In2 run: 0 lost samples in the extended set (pass 2: 658). It has GND via (35.75, 50.35).
- USB_DM's inherited plane-gap crossing is recorded in M3_R7.

**REGRESSION-03 (local GND returns):** in-layer copper path from the pad to the nearest GND via or THT GND pad, from
this review's 0.05 mm geodesic search:

| Pad | R6 | Pass 2 | Final |
|---|---:|---:|---:|
| D9.2 | 2.09 mm | 8.89 mm | **0.20 mm** |
| C6.2 | 0.27 | 1.59 | **0.53** |
| C80.2 | 2.90 | 7.91 | **1.01** |
| R167.2 | 3.68 | 3.68 | **0.45** |

**REGRESSION-05 (PULLPIN_EXT):**
- The route is 11.1 mm with 2 vias, and its tracks keep ≥ 0.72 mm from CAM_5V and VLOGIC_SENSE.
- J123.1's pad is now **0.350 mm** from CAM_5V B.Cu (pass 2: 0.201 mm). F3 narrowed the R104.1 tap from 0.4 to 0.2 mm.
- J123.1's other neighbours: LED_RED F.Cu 0.225 mm and PULLPIN F.Cu 0.295 mm. R6's J123.1 was 0.172 mm from
  CAM_MCU_TX (In2) and 0.18 mm from BAT_SW_SOURCE, so this is no regression.

**REGRESSION-08 (BAT_ILIM):**
- U9.9 → R84.1 is one 0.2 mm F.Cu link. TP89 sits on B.Cu at (8.1, 33.6) with 1 via.
- Nearest approach to QSPI_IO0 is about 3.15 mm (BAT_ILIM (10.975, 39.7) to IO0 (12.9–13.5, 41.9–42.5)).

## 3. Findings

| ID | Severity | Requirement | Finding | Evidence (final-board coordinates, mm) | Fix |
|---|---|---|---|---|---|
| P3-REGRESSION-01 | Minor | AGENTS.md §3 (SPI is a critical net); robustness margin | F3's `spi` stage removed a staircase by straightening SPI1_MOSI onto the line nearest IMU_CS. The two SPI1 lines now run 14.8 mm side by side at 0.189 mm edge gap. Only `r7_hygiene.py`'s docstring records it; M3_R7 does not | SPI1_MOSI F.Cu (23.35, 66.3)→(34.55, 77.5), centre line x−y = −42.95. IMU_CS F.Cu (24.35, 66.75)→(37.2, 79.6), x−y = −42.4. Both are 0.2 mm wide, centres 0.389 mm apart, edge gap 0.189 mm, over In1 GND (h = 0.203 mm, board stackup). Parallel run within 0.2 mm: R6 2.47 mm, pass 2 2.47 mm, final 14.81 mm. R6 and pass 2 had the rest of the run at x−y = −43.2 (0.366 mm), 14.67 mm within 0.4 mm. In return SPI1_MOSI–SPI1_MISO dropped from 13.35 to 5.25 mm at 0.3 mm. Inference: backward crosstalk is of order a few % of 3.3 V on a driven CS line (coupling about 1/(1+(D/h)²) ≈ 0.2, scaled by the 14.8 mm coupled length against nanosecond edges). MOSI toggles only while CS is low (the IMU is SPI1's only device), so a functional effect is improbable | Move IMU_CS's diagonal about 0.18 mm away (x−y ≈ −42.2) if DRC allows; or step MOSI back to x−y = −43.2 with its C121.1 clearance step at the via end. Otherwise record the 0.189 mm × 14.8 mm adjacency in M3_R7 §Routing hygiene |
| P3-REGRESSION-02 | Minor | AGENTS.md §3 (return paths); F9 (pull-pin input ESD robustness); M3_R7 return-path records | F2's PULLPIN redraw removed C160.2's GND trace to GND via (32.75, 32.30): "the pad keeps its pour; the via stays as a stitch". The pull-pin clamp D122's GND pin and its filter capacitor now return only through the F.Cu pour, by a longer path. No record states the cost | In-layer copper path to the nearest GND via or THT GND pad (0.05 mm geodesic search over fills, tracks and pads), R6 / pass 2 → final: **D122.1 (33.45, 28.6) F.Cu 3.32 / 3.32 → 5.62 mm**; C160.2 (34.9, 28.92) 3.71 / 3.71 → 4.22 mm. Removed: F.Cu (34.9, 28.92)→(34.9, 30.15)→(32.75, 32.30), 0.2 mm. The via (32.75, 32.30) remains. Of 173 SMD GND pads, 23 got shorter and 8 longer (> 0.2 mm) against pass 2. D122.1 is the largest increase. The rest are ≤ 0.5 mm: C11.2 0.47 → 0.97, C7.2 0.54 → 0.84, C32.2 0.26 → 0.47, plus RF-strip pads U30.10, U30.12 and R303.2 (DFM-07 via removal). Inference: R160 (1 kΩ) limits the clamp current, so a few nH of extra return mainly raises the clamp level during a harness ESD event | Add a GND via within about 1 mm of D122.1/C160.2 at a DRC-legal spot (F.Cu pour east of D122.1), or route a GND link that does not cross PULLPIN's entry. Record the change in M3_R7 §Return paths |
| P3-REGRESSION-03 | Minor | AGENTS.md §3 ("update STATUS … what was verified"); record accuracy | The records describe REGRESSION-05's residual with the pass-2 number, and the R6-method summary is imprecise | (a) R7_VALIDATION REGRESSION-05 row ("J123.1's own pad is 0.20 mm from CAM_5V B.Cu (pad gap, unchanged since step B)"), its "Open after pass 2" bullet, and STATUS.md l.109: the final board gives **0.350 mm**. KiCad shape distance from J123.1 (35.0, 34.6), 1.4 mm pad, to CAM_5V B.Cu (34.23, 32.2)→(35.48, 33.45). That track is now 0.2 mm (pass 2: 0.4 mm, 0.201 mm gap). F2's handoff also says 0.20 mm. (b) R7_VALIDATION REGRESSION-01 says the 603 lost samples are "all at vias or on R6 paths R7 abandoned". The 38 QSPI_NCS B.Cu samples (24.45–24.68, 42.58–42.75) sit at CAM_MCU_RX's In2 crossing under NCS. That crossing is R6's LED_YEL crossing moved 0.1 mm: R6 centre stretch (24.62–25.27), final (24.53–25.17), both about 0.9 mm. M3_R7 §Return paths states it correctly | Update R7_VALIDATION and STATUS: J123.1–CAM_5V 0.35 mm, and decide whether REGRESSION-05 is closed (J123.1's other gaps, LED_RED 0.225 and PULLPIN 0.295 mm, are no worse than R6's 0.17–0.18 mm). Reword the 603 summary as M3_R7 has it |
| P3-REGRESSION-04 | Minor | REQUIREMENTS F4 ("independently solve the final copper"); dc_solve docstring ("refine the grid to check accuracy"); record accuracy | `tools/dc_solve.py` at the records' 0.1 mm grid is sensitive to track alignment on 0.2 mm tracks. A 0.2 mm track centred on a cell edge is modelled one cell (0.1 mm) wide. The records quote 4-decimal 3V3 values and attribute sub-percent changes to specific causes. The records also give no DC solve for the other power nets F3 rewrote | Same solver, same boards: RAW_PROTECTED U9.6 → TP81 (camera eFuse feed): **0.1 mm grid: pass 2 129.67 → final 144.67 mΩ (+11.6 %)**, peak 10.0 A/mm at (37.85, 56.8), the one-cell-wide image of the 0.2 mm run at x 37.85. **0.05 mm grid: 128.30 → 122.28 mΩ (−4.7 %).** The geometry agrees: the run widened 0.2 → 0.4 mm at (38.05, 49.8–54.5) and the moved segment kept its width. U9.6 → U7.3,4 at 0.1 mm: R6 138.58, pass 2 138.39, final 153.60 mΩ (artefact as above). Other power nets F3 rewrote, pass 2 → final: USB_LIMITED U10.6 → U11.7 69.54 → **74.31 mΩ (+7 %, 0.05 mm grid)**, from removing its parallel copies; CAM_5V L3.2 → J9.1 23.85 → 24.95 mΩ (0.1 mm; R6 28.70). Better: RAW_PROTECTED U9.6 → U11.2 46.11 → 35.39; VLOGIC C84.1 → U2.2,3 53.94 → 36.54; VLOGIC U11 → U2 9.40 = 9.40. F3 §4 claims "+0.02 … +0.27 mΩ (≤ 1.9 %)" on 3V3, and 4-decimal values appear in M3_R7 §DC solve. All changes are a few mV at their loads | In M3_R7 §DC solve, record the grid used and its accuracy, and solve paths with ≤ 0.25 mm tracks at 0.05 mm. Add a short table for RAW_PROTECTED (U11, U7), VLOGIC, USB_LIMITED and CAM_5V on the final board. Optionally make `dc_solve.py` warn when a track's modelled width differs from its drawn width by more than one cell |
| P3-REGRESSION-05 | Minor | F9 (off-board lines: "a chafed power-switch wire … must not damage the board"); AGENTS.md §3 (critical QSPI net) | QSPI_IO0's step-B F.Cu path runs side by side with BAT_SW_RETURN. That net is the harness side of the power switch: J1.4 → R165 470 kΩ, the whole 160 mm on-board run is unprotected. F2 redrew BAT_SW_RETURN and kept the adjacency. Pass 2's REGRESSION-01 listed IO0's neighbours as BAT_FAULT_N and BAT_ILIM only, and no record mentions this one | BAT_SW_RETURN F.Cu (19.5, 32.425)→(15.0, 36.925), 0.15 mm, against QSPI_IO0 F.Cu (15.6, 36.9)→(20.4, 32.1), 0.2 mm: centre lines x+y = 51.925 and 52.5, edge gap 0.232 mm, parallel 5.92 mm (pass 2 the same). R6: closest approach 0.251 mm to an IO0 track and 0.176 mm to U3.5, with no parallel run ≥ 1 mm within 0.35 mm. The same harness line also passes RADIO_NSS F.Cu (11.2–22.0, 29.6) at 0.175 mm over about 1.2 mm. BAT_SW_RETURN nets: J1.4, R165.1 (470 k, M3_R4 V3). Inference: an ESD event on the switch wiring would couple onto the QSPI data line through about 0.3 pF (about 0.05 pF/mm), and IO0 edges would couple onto a harness lead. Both are improbable with a sealed reed or magnetic switch | Move IO0's diagonal, or BAT_SW_RETURN's, to ≥ 0.5 mm edge gap over the run, if a DRC-legal lane exists. Otherwise record the adjacency, with the BAT_SW_RETURN–RADIO_NSS one, as an accepted exception in M3_R7 |

## 4. Measurements

### 4.1 What the fix pass changed (exact track and via geometry, pass 2 → final)

- **Totals:** tracks −1,388 / +557; vias −74 / +84.
- **Largest per-net churn:** GND −150 / +29 tracks and −12 / +50 vias; 3V3 −142 / +58 tracks and −5 / +2 vias;
  RAW_PROTECTED −56 / +27; 3V3A −54 / +27; VBUS −41 / +22; USB_LIMITED −38 / +5.
- **Pads:** outside the RF strip, every pad keeps its net, position and size, except TP89, which moved to B.Cu at
  (8.1, 33.6). C304 is new in the strip.
- **GND vias removed outside the strip:** none. (26.45, 42.85) moved 0.05 mm. The other removed GND vias are the
  strip lattice (F1, RF).
- **3V3 vias removed:**
  - (24.9, 35.0), re-added at (24.8, 34.3);
  - (32.57, 35.0) and (32.87, 34.3), the R205 star and the D122.2 pocket;
  - (34.663, 36.105);
  - (30.1, 71.17), moved 0.07 mm.
- **C9.1** (buck output, 22 µF) connects straight to L1.2 by 0.6 mm B.Cu, so its plane via distance (0.73 → 2.31 mm)
  does not matter.
- **IMU_CS:** R6 and pass 2 had two complete routes, a loop: the F.Cu diagonal and an In2 detour. The final board
  keeps the F.Cu diagonal only, with one via. IMU_CS's own unreferenced samples fell 2,936 → 933 (F3).

### 4.2 Critical-net reference (R6 method, `tools/critical_reference.py`, R6 moved +18 mm)

| | Final (reproduced) | F3 record |
|---|---:|---:|
| R6-referenced samples lost on the candidate | 603 (410 IO0 abandoned F.Cu path, 79 SPI1_MOSI F.Cu, 59 IO3 F.Cu, 38 NCS B.Cu, 15 IO1 B.Cu, 2 IO3 B.Cu) | 603 |
| Candidate samples unreferenced where R6 was referenced | 861 | 861 |
| Extended set, lost / candidate-new | 874 / 2,659 | 874 / 2,659 |

Centre-line unreferenced stretches of 3 or more samples (0.03 mm and longer) on the final board, compared with R6 and
pass 2:
- QSPI_IO0 and IO1: only at their own vias, ≤ 0.55 mm each.
- QSPI_IO3 B.Cu (19.93–20.38, 42.42–42.87), 0.65 mm: at CAM_MCU_TX's In2 crossing, which F2 restored to R6's place.
  Present on R6, absent on pass 2.
- QSPI_NCS B.Cu about 0.9 mm at CAM_MCU_RX's crossing: as on R6, moved 0.1 mm.
- USB_DM B.Cu x 10.05: inherited from R6.
- Everything else (SPI1 at the bottom-side IMU, QSPI_IO2, HSE at its vias) equals R6.

Which In2 polygon carries the B.Cu critical runs (sampled every 0.05 mm):
- QSPI_NCS/IO0/IO1/IO3 sit over the main 3V3 polygon (434.8 mm², 11 vias).
- HSE_IN sits over the 72.2 mm² island fed by 4 vias, as on pass 2.
- No critical B.Cu run lies over the two islands F2 split off.
- R6's protected HSE checkpoints, (16.5, 61.0) and (15.95, 65.93), lie inside the 3V3 fill.

### 4.3 Layer changes of critical nets: nearest GND via (centre to centre)

| Net (via) | R6 | Pass 2 | Final |
|---|---:|---:|---:|
| QSPI_IO0 (12.9, 44.4) / (15.55, 50.85) | — | 3.55 / 1.61 | 0.78 / 0.78 |
| QSPI_IO1 (13.0, 51.5) | 2.22 | 3.64 | 1.50 |
| QSPI_IO1/IO2/IO3/NCS, other 8 vias | 0.75–0.92 | same | same |
| HSE_IN (27.9, 54.4) / HSE_OUT (23.2, 53.9) | 0.90 / 1.20 | same | same |
| USB_DP (8.9, 74.75) / (8.9, 76.35) / (12.5, 57.9) | 3.33 / 2.95 / 0.81 | same | 1.25 / 0.80 / 0.81 |
| USB_DM (10.05, 76.3) / (11.2, 56.5) | 3.86 / 1.39 | same | 1.39 / 1.39 |
| SPI1_SCK / SPI1_MOSI / SPI1_MISO | 2.19 / 1.43 / 4.02 | same | 0.78 / 0.85 / 1.38 |
| IMU_CS (37.2, 80.07) | 3.45 (+2 detour vias) | same | 1.20 (detour removed) |
| SWDIO / SWCLK / NRST | 11 / 14 / 6 vias | same | each via equal or closer; e.g. SWDIO (33.8, 83.9) 1.62 → 0.78, SWCLK (41.45, 76.65) 2.53 → 0.98 |

Every critical-net via is equal to or closer than in R6 and pass 2.

### 4.4 Local GND returns (all 173 SMD GND pads)

Measured as the in-layer copper path to the nearest GND via or THT GND pad, on a 0.05 mm geodesic grid.
- **Against pass 2:** 23 pads are more than 0.2 mm shorter and 8 are longer (P3-REGRESSION-02).
- **No GND pour island** on F.Cu or B.Cu is without a GND via or THT GND pad, on either board.
- **Fill polygon counts:** GND_F 46 → 39, GND_B 35 → 32. GND_In1 is still one polygon (4,686.8 mm²).

### 4.5 DC solves (`tools/dc_solve.py`, 35 µm, 20 µm plating, 20 °C; grid 0.1 mm unless noted)

| Path | R6 | Pass 2 | Final |
|---|---:|---:|---:|
| RAW_ACT Q121:5–9 → J122:2,5,8,11 (7.7 A) | 3.96 | 3.96 | **3.96 mΩ** (30.5 mV, 0.235 W) |
| BAT_IN J1:1 → Q120:5–9 (7.7 A) | 3.91 | 3.91 | **3.91 mΩ** (30.1 mV, 0.232 W) |
| ACT_FET_S Q120:1–3 → Q121:1–3 (7.7 A) | 1.36 | 1.36 | **1.36 mΩ** (10.4 mV, 0.080 W; peak 6.15 A/mm B.Cu) |
| BAT_IN J1:1 → U9:5 | — | 10.48 (F1 record) | 13.39 mΩ (= record) |
| 3V3 L1:2 → U1:75 | 21.93 (pass 2) | 42.85 | 14.25 mΩ (= record) |
| 3V3 L1:2 → FB31:1 | — | 29.3 | 13.61 mΩ (= record) |
| RAW_PROTECTED U9:6 → U11:2 | — | 46.11 | 35.39 mΩ |
| RAW_PROTECTED U9:6 → TP81:1 (0.05 mm grid) | — | 128.30 | 122.28 mΩ (0.1 mm grid: 129.67 → 144.67, artefact; P3-REGRESSION-04) |
| RAW_PROTECTED U9:6 → U7:3,4 (0.1 mm grid) | 138.58 | 138.39 | 153.60 mΩ (same artefact) |
| VLOGIC U11:1,8 → U2:2,3 | — | 9.40 | 9.40 mΩ |
| VLOGIC C84:1 → U2:2,3 (hold-up) | — | 53.94 | 36.54 mΩ (0.2 mm neck widened to 0.5 mm) |
| USB_LIMITED U10:6 → U11:7 (0.05 mm grid) | — | 69.54 | 74.31 mΩ |
| CAM_5V L3:2 → J9:1 | 28.70 | 23.85 | 24.95 mΩ |

### 4.6 Pyro block, arming break and DRC rules

- **`m3.kicad_dru`:** byte-identical between pass 2 and final. Lines 1–10 are identical to R6. `check_actuators` (pinned
  rule hashes, PYRO_BLOCK area, CH1 nets and pinned parts) passes in the gate.
- **Copper outside pads, pass 2 → final** (polygon XOR, tracks and vias minus the net's pads):
  - PYRO1_BUS, PYRO1_IGN and PYRO1_OUT: **0 mm² lost or gained on every layer.** The removed PYRO1_BUS, IGN and OUT
    segments lay wholly inside J124.1, R132.1, R134.2, J121.1/2, Q124.5 and C128.1.
  - PYRO1_GATE: −0.451 mm² (R6's 0.3 mm run is now a single 0.2 mm route).
  - PYRO1_CONT: In2 +0.215 mm² (0.15 → 0.2 mm).
  - PYRO1_COLD: its 33 mm dead branch with 3 vias removed. It was R6 inheritance: R6 had 14 tracks and only two pads,
    D120.1 and R131.2.
  - ARM1_SENSE: two collinear In2 segments merged.
  - RAW_ACT and ACT_*: ≤ 0.12 mm² each. ACT_FET_S gains its R120.1 → Q120.1 link.
- **Clearance from PYRO1_BUS/IGN/OUT copper to every other net's copper (≤ 1.2 mm), pass 2 → final:**
  - identical, except CAM_FAULT_N track 0.519 → 0.513 mm (rule ≥ 0.5), CAM_FAULT_N via 0.583 → 0.581, and PYRO1_GATE
    0.621 → 0.672;
  - GND copper stays ≥ 0.50 mm.
- **Arming break:** PYRO1_BUS = {J124.1, R132.1, R134.2} and RAW_ACT reaches J124.2 only, unchanged. No test point
  was added on the bus or igniter nets.

### 4.7 Close parallel coupling on critical nets (same layer, edge gap ≤ 0.35 mm, run ≥ 1 mm)

| Pair | R6 | Pass 2 | Final |
|---|---|---|---|
| IMU_CS – SPI1_MOSI F.Cu | 2.47 mm @ 0.189 | 2.47 @ 0.189 | **14.81 @ 0.189** (P3-REGRESSION-01) |
| SPI1_MOSI – SPI1_MISO F.Cu | 13.35 @ 0.295 | 13.35 @ 0.295 | 5.25 @ 0.30 |
| QSPI_IO1 – QSPI_NCS B.Cu | 6.22 @ 0.224 | 6.22 @ 0.224 | none |
| QSPI_IO1 – BUZZ_DRV B.Cu | — | 1.95 @ 0.275 | none |
| QSPI_CLK – RADIO_RXEN F.Cu | — | 4.3 @ 0.175 | 4.38 @ 0.25 |
| QSPI_IO0 – BAT_SW_RETURN F.Cu | — | 5.92 @ 0.232 | 5.92 @ 0.232 (P3-REGRESSION-05) |

HSE neighbours within 1.5 mm of HSE_IN/OUT copper and Y1/C25/C26: identical on pass 2 and final.

## 5. Checked and not raised

- **3V3 In2 plane:** 7 polygons, 564.1 mm² (pass 2: 6, 608.2; R6: 11, 479.1).
  - The USB-pair island is now part of the main polygon.
  - F2's LED lanes split off two islands, R87/R88 (10.3 mm²) and the D122.2 pocket (17.6 mm²). Each has 2 vias, as
    on R6. No critical B.Cu run is over them.
  - An 8.54 mm² island with no via inside (27.4–31.6, 67.9–70.2) exists unchanged on pass 2 and final.
- **VCAP2** (U1.73 → C20.1): F3 narrowed it 0.3 → 0.25 mm, which F3 recorded. The 12.7 mm U-shaped path for a
  2.9 mm pin-to-capacitor distance is R6's. It is listed in pass2_routing_geometry and is the routing reviewers'
  item.
- **BAT_FAULT_N In2 (x 12.3)** against QSPI_IO0 B.Cu (x 12.9), adjacent layers, 0.6 mm centre offset over 6 mm.
  Inference: below 0.1 V of coupling onto a pulled-up flag.
- **TPS25947 ILM node** (SLVSFC9C §8.4.1, https://www.ti.com/lit/ds/symlink/tps25947.pdf): about 4.75 mm link plus a
  4.5 mm branch to TP89 with 1 via. Capacitance is far below 50 pF (Inference). No fast neighbour within 3 mm.
- **ORDERING §7 mounting note:** consistent with the final board. TP89 is no longer near a hole. BUZZ_DRV at x 1.55 is
  0.78 mm from the (4, 64) hole edge under the nylon hardware.
- **Pyro-block GND vias added by F3**, (18.18, 90.55) and (33.92, 84.67): DRC passes under the pyro rules.
- **J123.1 neighbours:** see §2, REGRESSION-05.

## 6. Sources

- `docs/REQUIREMENTS.md` F4, F8, F9, M2; `AGENTS.md` §2–3; `docs/M3_R7.md` §Return paths, §DC solve, §Routing hygiene;
  `docs/R7_VALIDATION.md`; `STATUS.md`; `docs/M3_R4.md` V3 (R165 470 k on BAT_SW_RETURN).
- `sources/r7_review/pass2_regression.md`, `pass2_main_verdicts.json`, `fix2_F1/F2/F3_handoff.md`,
  `m3_design/r7_hygiene.py` (spi-stage docstring, ll. 1514–1531).
- Board stackup (`m3.kicad_pcb`): dielectric 1 and 3 are 0.203 mm, core 1.03 mm.
- TI TPS25947 datasheet SLVSFC9C §8.4.1 (https://www.ti.com/lit/ds/symlink/tps25947.pdf), as cited in pass 2.

## 7. Inferences (not measured, or not checked against a primary source)

- Every crosstalk, ESD-coupling and return-current-spread magnitude in P3-REGRESSION-01/02/05 and §2 is an
  order-of-magnitude estimate. None comes from a field solve or a bench measurement.
- The DC values assume 35 µm copper, 20 µm via plating, 20 °C, and no pad or contact resistance (dc_solve docstring).
- The reference-coverage counts are the R6 sampling method, not a field solve.
