# R7 pass 2: board-wide regression versus R6

Read-only review, 2026-10-15. Dimension: every copper change outside the RF strip (y > 23.5) that R7 made to the
R6 board, judged against the checks the R6 reviews used: reference and return continuity of the critical nets,
3V3 supply resistance, the 7.7 A copper, the pyro block, and routing style on the new and redrawn copper.

| Item | Value |
|---|---|
| R7 board | `m3_design/assembly_review/m3.kicad_pcb`, SHA-256 `03fe7572…6aa86d54` (checked before and after; unchanged) |
| R6 board | `git show 3b215ba:m3_design/assembly_review/m3.kicad_pcb`, SHA-256 `184a87e8…c856680`, compared translated by +18.000 mm in y |
| Tools | KiCad 10.0.6 `pcbnew` Python (read-only scripts in the reviewer's scratch directory), `tools/dc_solve.py`, `tools/check.sh` |
| Gate | `tools/check.sh` rerun by this reviewer: DRC 0, unconnected 0, parity 0, ERC 0, audit, silk, R7 contract, actuator contract, fit: all OK, exit 0 |
| Fills | Saved fills used throughout. A fresh in-memory `ZONE_FILLER` refill with the project files present reproduces every zone's filled area exactly on both boards (0 zones differ), so the saved fills are current |

## 1. Summary

R7 leaves the 7.7 A copper and the pyro-block copper exactly as R6 had them, and every R6 DRC rule is
byte-identical (the RF rules sit before the pyro rules). On the whole R7 improves R6's planes: In1 is now
free of the R6 port signals, and the In2 3V3 plane has fewer, larger islands. The regressions are local, and
most come from the step-B surgery near U1 and from the slow nets the grid router redrew:

- **Major (1).** The QSPI_IO0/IO1 return path at U1 got worse than R6 in four ways, none of them recorded:
  - BAT_FAULT_N's new In2 leg cuts the 3V3 reference under both lines.
  - QSPI_IO0's two new layer changes have no GND via within 1.5 mm (3.55 and 1.61 mm).
  - Removing the stitching via at (12.7, 53.7) moved QSPI_IO1's nearest GND via from 2.22 to 3.64 mm.
  - BUZZ_DRV now runs 3.9 mm beside QSPI_IO1 with a 0.275 mm gap.

  R6's gates were zero lost critical-reference samples and a GND via at every critical layer change (or a
  recorded exception, M3_R5). R7 fails both.
- **Minor (7):**
  - BUZZ_DRV's In2 leg cuts USB_DP's reference and doubles the 3V3 feed to U1.75 (21.9 → 42.9 mΩ). The
    LED_RED/VLOGIC_SENSE reroute removed a B.Cu GND island under NRST.
  - U9's current-limit node (BAT_ILIM) now runs 8.4 mm beside QSPI_IO0, against TI's layout guidance.
  - Three local GND returns got longer when R6 vias and tracks were removed: D9.2 3.7 → 10.7 mm, C80.2
    3.9 → 8.8 mm, C6.2 1.3 → 2.6 mm.
  - Routing-style defects on the redrawn copper.
  - The J123 move more than doubled the unprotected PULLPIN_EXT run.
  - Many new layer changes have no nearby GND via.
  - The F4 requirement text still says R7's copper has not been solved. It has been solved here, and the
    values are unchanged.
- **No Critical.**

## 2. Findings

| ID | Severity | Requirement | Finding | Evidence (R7 coordinates, mm) | Fix |
|---|---|---|---|---|---|
| REGRESSION-01 | Major | AGENTS.md §3 routing (critical nets; GND vias at layer changes); R6 acceptance: zero lost critical-reference samples (M3_R6 §"final"; `sources/r6-independent-routing-reference-review-20261013.json`); M3_R5 §"Inherited return-path exceptions" (1.5 mm criterion, exceptions recorded) | QSPI_IO0/IO1 lost reference and return continuity at U1 compared with R6. Nothing in stepB_handoff or M3_R7 records it | (a) BAT_FAULT_N In2 0.15 mm, via (15.6, 50.0) → (13.0, 52.6) → (13.0, 55.4) via. It passes under QSPI_IO0 B.Cu (y 50.85) at x 14.75 and under QSPI_IO1 B.Cu (y 51.5) at x 14.1. New unreferenced centre length on In2 3V3: QSPI_IO0 (14.29–15.0, 50.85) ≈ 0.71 mm beyond its own via antipad; QSPI_IO1 (13.55–14.56, 51.5) 1.01 mm (R6 0). (b) QSPI_IO0 new vias: (12.9, 44.4) is 3.55 mm and (15.55, 50.85) 1.61 mm from the nearest GND via. In R6 every QSPI via had one within 0.92 mm except IO1's recorded 2.22 mm. (c) GND via (12.7, 53.7) removed, so QSPI_IO1's via (13.0, 51.5) goes from 2.22 to 3.64 mm. (d) QSPI_IO1 B.Cu (13.0–16.6, 51.5) runs 3.55 + 0.35 mm beside BUZZ_DRV B.Cu (17.95, 51.95)–(14.65, 51.95)–(11.65, 54.95), edge gap 0.275 mm. (e) QSPI_IO0 B.Cu x 12.9 runs 3.4 mm beside BAT_FAULT_N (gap 0.425) and 2.5 mm beside BAT_ILIM (gap 0.45). Each layer change of QSPI_IO0 also swaps its reference between In1 GND and In2 3V3 | 1. Take BAT_FAULT_N's In2 leg out from under the QSPI B.Cu runs, for example by keeping it at x ≤ 12.4 or y ≥ 52.2 under U1's west row. 2. Restore a GND via near (12.7, 53.7) and add GND vias within 1 mm of (12.9, 44.4) and (15.55, 50.85), each at a DRC-checked spot. 3. Move BUZZ_DRV's (14.65–17.95, 51.95) leg ≥ 0.5 mm from QSPI_IO1. 4. Rerun the R6 critical-reference sampling. Whatever remains goes in M3_R7 as a recorded exception, as M3_R5 did |
| REGRESSION-02 | Minor | Same R6 reference criterion (USB, SWD/NRST); AGENTS.md §3 (hand-routed power) | Two redrawn slow nets removed reference under critical lines. One of them also doubled the 3V3 feed resistance to U1's VDD pin 75 | USB_DP B.Cu x 11.95 loses In2 3V3 reference over (11.95, 58.45–59.91), 1.47 mm, R6 0. The cause is BUZZ_DRV In2 (13.05, 56.45)–(13.05, 58.25)–(11.85, 59.45)–(10.75, 60.65), which crosses under USB_DP at (11.95, 59.35). The same slot cuts the 3V3 In2 island under the USB pair (x 10.2–13.5, y 58.6–75.5; one via, (12.6, 59.5)) off the main plane. U1.75 and its decoupler C17 now draw 3V3 through the 0.2 mm B.Cu track (15.95, 65.93)–(12.6, 62.58)–(12.6, 59.5): dc_solve L1:2 → U1:75 gives 21.93 mΩ (R6, 100 % In2 at mid-path) → **42.85 mΩ** (R7, 100 % B.Cu at mid-path). Every other U1, U3 and R164 feed improved (§4.4). NRST In2 (37.13, 47.8–50.4) and (36.44–37.13, 50.4–51.0) loses its B.Cu GND reference, 2.2 mm (R6 0). The LED_RED via (33.45, 51.05) and its B.Cu track, with the VLOGIC_SENSE vias (34.0, 51.6) and (35.7, 53.3), cut the neck of R6's B.Cu GND island (33–38, 49.8–52.5), and the filler then dropped the island. Not a regression: USB_DM B.Cu x 10.05 already runs 18.6 mm over the In2 gap between BAT_IN (x ≤ 9.9) and 3V3 (x ≥ 10.2) in R6. The R6 metric counted only new losses, so it never flagged this | Move BUZZ_DRV's In2 leg off the USB pair (it can stay on B.Cu west of x 9.5, or cross the pair at a GND via), and give the NRST region's B.Cu GND a via, or move the LED_RED via. Record USB_DM's inherited split crossing in M3_R7 |
| REGRESSION-03 | Minor | AGENTS.md §3 (return paths); R6 local-return reviews (`r6-independent-routing-reference-review` items 6, 10, 13) | Removing R6 GND copper lengthened three local GND returns. stepB_handoff §4.10 lists only the vias it added | In-layer copper path from the pad to the nearest GND via or THT GND pad (0.05 mm grid search over saved fills, tracks and pads), R6 → R7: **D9.2** (18.0, 31.2) F.Cu, the TPS259470 output Schottky's anode: 3.72 → **10.7** mm. Its R6 F.Cu track and via (18.0, 31.2) → (19.85, 28.25) are gone. **C80.2** (7.675, 52.1) B.Cu, BAT_IN input cap: 3.90 → 8.82 mm (vias (11.0, 53.55) and (12.7, 53.7) removed; the new radio/GNSS B.Cu bus fences its pour). **C6.2** (20.2, 29.4) B.Cu, U2 input bulk cap: 1.29 → 2.62 mm (the new via (19.55, 27.05) replaces (19.85, 28.25)). U2's primary input cap C7 and the switch loop did not change. Of 95 SMD GND pads in y 23.5–62, these 3 got worse and 5 got better (C84.2 8.05 → 1.64, C97.2 2.15 → 1.00, R105.2 6.69 → 1.65, C20.2, D8.2). TI asks for the opposite at D9 (SLVSFC9C §8.4.1, p. 63): "minimize the loop area formed by the Schottky diode/bypass-capacitor connection, the OUT pin and the GND terminal of the IC" (also §8.3.1, "Connect a Schottky diode from the OUT pin [to] ground to absorb negative spikes"). D9.1 already sat 9.6 mm from U9.6 (OUT) in R6 | Add a GND via beside D9.2 (the F.Cu pour east of the pad, between the pad and the diagonals at x ≈ 19.5) and one at C80.2 (B.Cu pour south-west of the pad). Record both in M3_R7 |
| REGRESSION-04 | Minor | AGENTS.md §3 (0/45/90°, no staircases, acute angles or stubs) | Style defects in the redrawn R6-net copper. No off-angle segment was found | Acute 45° turns outside pads: BAT_SW_RETURN F.Cu (11.2, 44.825) → (11.9, 44.125) → (11.9, 45.025), a 0.7 mm hook that reverses in free copper. VLOGIC_SENSE B.Cu T at (35.1, 32.2467), a 45° wedge 0.2 mm outside C60.1. PULLPIN F.Cu (32.6675, 30.4404) → (32.1675, 30.9404) → (32.5, 30.9404), a hook 7.5 µm outside D122.3, plus an 8 µm segment (32.2, 30.9079)–(32.2, 30.9). BAT_ILIM: a new 0.15 mm path retraces R6's 0.2 mm path near U9/R84 with an offset of 0.1 mm, overlapping on (10.975, 39.3)–(9.875, 38.6), and runs (9.875, 37.6)–(11.075, 36.4) parallel to R6's (9.875, 37.3)–(10.675, 36.5) with a **37 µm same-net gap over about 1.1 mm** (etch sliver, acid trap). Overlap: VLOGIC_SENSE (32.53, 36.483–37.0) and (32.53, 36.5–37.0) on B.Cu. Micro-segments: CAM_MCU_TX B.Cu 3 and 5 µm at (36.55, 46.85). 6 new 45° jogs ≤ 0.3 mm (RADIO_NRST, RADIO_BUSY, PULLPIN, PULLPIN_EXT (35.7, 30.87), LED_RED, CAM_MCU_TX). R6 had 81 of the same kind, so this pattern is not new in kind. LED_RED went from 42 mm (24 F.Cu, 14 B.Cu, 4 In2) to 62.7 mm (58.2 F.Cu), snaking under U1's body (21.75, 45.85) → (23.75, 50.85) → (28.35, 46.85) | Redraw these few links by hand: remove the hooks and the BAT_ILIM double path (keep R6's 0.2 mm path and branch to the test pad from R84.1), merge the overlaps, and drop the micro-segments |
| REGRESSION-05 | Minor | F9/F8 robustness of off-board lines (ESD); AGENTS.md §3 | Moving J123 to (36.0, 34.6) more than doubled the unprotected part of the pull-pin input, the copper between the connector and the 1 kΩ R160 and the D122 clamp | PULLPIN_EXT: R6 5.64 mm (0.77 F.Cu, 4.87 In2). R7 13.72 mm (4.83 F.Cu, 8.89 B.Cu), 2 vias (37.3, 31.87) and (33.8, 25.57). It runs at 0.40–0.43 mm edge gap beside CAM_5V (0.1–0.25 mm of run) and VLOGIC_SENSE (about 1.5 mm) on B.Cu. The rest of the pull-pin chain is unchanged (R160 1 k, R161 10 k, C160 100 nF, D122 BAT54S) | Either accept and record it in M3_R7, or route J123.1 → R160 with ≥ 0.5 mm to the CAM_5V/VLOGIC_SENSE copper. Inference: a 1 k + BAT54S chain still clamps at the MCU side; the longer run mainly adds coupling into neighbours |
| REGRESSION-06 | Minor | AGENTS.md §3 (GND vias at layer changes); stepB_handoff §4.9 | Many of R7's new layer changes have no GND via nearby | Of 75 new non-GND vias outside the strip, 53 have no GND via or THT GND pad within 1.5 mm. Redrawn R6 nets: BUZZ_DRV (1.55, 60.0) 7.57 mm, BAT_SW_RETURN (16.3, 37.725) 4.08 mm, VLOGIC_SENSE (35.7, 53.3) 3.82 mm. For these 13 nets the aggregate matches R6 (R6 49/68 vias > 1.5 mm, R7 45/71), so they are no regression. New interface nets: the GNSS corridor vias (1.2–2.7, 51.0–52.5) are 7.7–9.8 mm from a GND via, the radio SPI vias (9.4/10.0, 27.2–30.2) 4.9–7.5 mm. Their B.Cu corridor (x 1.2–6.2) runs over the In2 BAT_IN plane. The handoff names this only for the 13 redrawn nets | Add GND vias at the corridor turns (x 9.4–10.0, y 27–30.5; x 1.2–2.7, y 51–52.5) where DRC allows, or record them as exceptions (the interface reviewer may own the corridor) |
| REGRESSION-07 | Minor | REQUIREMENTS F4 ("independently solve the final copper of R7") | F4 and the R7 record still say R7's 7.7 A copper has not been solved. It now has been, and nothing changed | `tools/dc_solve.py`, 0.1 mm grid, 7.7 A, R7 SHA `03fe7572…`: RAW_ACT Q121:5–9 → J122:2,5,8,11 **3.96 mΩ** (30.5 mV, 0.235 W). BAT_IN J1:1 → Q120:5–9 **3.91 mΩ** (30.1 mV, 0.232 W). ACT_FET_S Q120:1–3 → Q121:1–3 **1.36 mΩ** (10.5 mV, 0.081 W). All equal R6's values, which this reviewer also reproduced. The In2 BAT_IN cut at the aft end lies off the J1 → Q120 path. Peak current densities: RAW_ACT 5.75 A/mm F.Cu, BAT_IN 6.17 A/mm In2 (R6 6.37), ACT_FET_S 6.14 A/mm B.Cu | Update F4 and M3_R7 with the R7 solve and its SHA. The bench thermal test stays open |
| REGRESSION-08 | Minor | TI TPS25947 datasheet SLVSFC9C §8.4.1 Layout Guidelines, p. 62–63, on the ILM traces: "These traces must not have any coupling to switching signals on the board" and "the PCB routing of this node must be kept away from any noisy (switching) signals" | U9's current-limit node BAT_ILIM (U9 is a TPS259470**L**: active current limit, latch-off, ITIMER open, so the fastest response) now runs beside fast digital copper it did not have in R6. The cause is the QSPI_IO0 surgery and the redrawn test-pad branch | Same- or adjacent-layer neighbours within 0.6 mm edge gap (In2 counted with the B.Cu above it). **R7:** QSPI_IO0 8.4 mm (5.70 In2-under-B.Cu, 2.70 on B.Cu, gap 0.45): BAT_ILIM B.Cu (12.275, 42.2–46.6) and In2 (12.275, 46.6–55.1) under QSPI_IO0 B.Cu x 12.9. Also BUZZ_DRV 2.75 mm crossing over the In2 run, BAT_FAULT_N 3.05 mm, QSPI_IO1 0.55 mm, USB_DM 1.02 mm, GNSS_RESET_N 0.80 mm. **R6:** VLOGIC (DC), BAT_SW_RETURN, TLM_PWR_EN (slow) and BUZZ_DRV 0.30 mm only. R6's QSPI_IO0 ran on F.Cu, shielded from BAT_ILIM's In2 run by In1 GND. Capacitance stays far below TI's 50 pF limit (Inference: about 5–6 pF for 36.8 mm of 0.15 mm trace, 4 vias and TP89) | Keep BAT_ILIM's test-pad branch away from QSPI_IO0 and BUZZ_DRV (≥ 3 × the dielectric height, or behind a GND plane). Fixing REGRESSION-01 by returning QSPI_IO0 to F.Cu would do it. check_actuators' R84 message also asks for fault qualification whenever the BAT_ILIM copper is revised |

## 3. What changed outside the RF strip

Track/via inventory (exact geometry match after the +18 mm translation): R6 3699 items, R7 3469. 885 R6
items outside the strip were removed and 434 added.

| Group | Removed | Added | Note |
|---|---|---|---|
| R6 port nets (GPS_*, RADIO_* of the harness ports, TLM_*) | 626 | 0 | The ports and their supply are gone. This includes 19 GPS_TX_MCU items inside PYRO_BLOCK (4 vias, 2 In1 segments) |
| RAW_PROTECTED (telemetry feed only) | 16 | 0 | The remaining RAW_PROTECTED copper is unchanged |
| 3V3 | 12 | 5 | Stubs to the removed C179/C180/D131 trimmed. The In2 diagonal (17.58, 34)–(21.78, 29.8) inside the plane was removed, leaving a 2.5 mm In2 3V3 stub that ends inside the plane. New: FB30 feed via (11.58, 26.2), FB31 0.4 mm F.Cu feed |
| GND | 35 | 11 | See REGRESSION-01/03. Removed vias: (11.0, 53.55), (12.7, 53.7), (19.3, 25.4), (22.5, 25.4), (19.85, 28.25), (22.7, 28.8), (37.7, 34.7) (J123.2's THT pin replaces it), (5.975, 40.6) (moved to (6.85, 40.5)) and three in the old port area |
| BAT_IN | 2 | 3 | C80's via (9.425, 52.1) now shares C96's via (9.3, 53.38) through a 2.1 mm, 0.5 mm-wide B.Cu link |
| QSPI_IO0 | 7 | 7 | R6: 27.64 mm all on F.Cu, 0 vias. R7: 26.84 mm (17.74 F.Cu, 9.10 B.Cu), 2 vias. The QSPI data-lane length span is unchanged (IO3 24.70 to IO2 33.91 mm) |
| VBUS_SENSE | 4 | 5 | Inward escape via (15.65, 53.0) and an In2 link under U1's west row |
| The 13 "redrawn" nets | 183 | 244 | BUZZ_DRV, BAT_FAULT_N, BAT_SW_SOURCE, BAT_SW_RETURN, LED_RED, LED_YEL, CAM_MCU_TX/RX, PULLPIN, PULLPIN_EXT, VLOGIC_SENSE and BAT_ILIM changed. LOGIC_SOURCE_ST's copper is identical to R6's |
| New R7 interface nets (GNSS_*, RADIO_* SPI/control, 3V3_GNSS) | 0 | 159 | The left corridor, the F.Cu band and U1's west escapes |
| Pyro, arming, RAW_ACT, ACT_*, SERVO*, HSE, USB, SPI1, SWD, QSPI except IO0 | 0 | 0 | No item changed |

Footprints: every R6 footprint that stays in R7 has the same position, rotation, side and pad geometry after the
translation, with two exceptions: J123 (34.5, 21.8) → (36.0, 34.6), and U1's pin nets for the new radio and GNSS
pins (PB14/PB15/PD8/PD10 assigned; PA8/PA10 freed). 37 refs were removed and 38 added (stepB_handoff §1).

Zones changed: R6_BAT_IN_In2 lost (0.3–15, 18.3–32.6) and (0.3–9.9, 18.3–26), and its fill dropped from
1080.7 to 956.8 mm². 3V3_In2 gained the FB30 lobe (9.9–14, 23.9–27) and the area the BAT_IN pour vacated;
its fill grew from 479.1 to 608.2 mm². GND_F, GND_B and GND_In1 were extended to y 0.3, and R7_GND_In2_strip
was added.

## 4. Measurements

### 4.1 Critical-net reference coverage (R6 method, extended)

Method: the centre line and both edges of every track of the critical nets were sampled every 0.01 mm. The
nets are USB_DP/DM, HSE_IN/OUT, QSPI_CLK/NCS/IO0–3, SPI1_SCK/MOSI/MISO, IMU_CS, plus SWDIO, SWCLK and NRST.
Each sample was tested against the adjacent reference fill, using the saved fills:

| Track layer | Reference fill |
|---|---|
| F.Cu | In1 GND |
| B.Cu | In2 GND, 3V3 or 3V3A (as R6) |
| In1 | F.Cu GND |
| In2 | B.Cu GND |

Totals: R6 185,445 samples, 67,286 unreferenced. R7 185,175 samples, 67,726 unreferenced. These absolute
numbers include R6's inherited unreferenced runs (via antipads, the In2 gaps under U1 noted in M3_R5 §"pass 2",
USB_DM on the In2 split). Only the location-matched delta is a regression.

Centre samples (0.01 mm each) that are unreferenced in R7 but referenced at the same place in R6:

| Net / layer | Samples | Where | Cause |
|---|---|---|---|
| QSPI_IO0 B.Cu | 183 | (12.9, 44.4–44.95); (14.29–15.55, 50.85) | 2 × the new via antipads (inherent), plus about 0.71 mm under the BAT_FAULT_N In2 slot |
| QSPI_IO0 F.Cu | 117 | (12.9, 43.85–44.4); (15.03–15.55, 50.85–51.0) | The new via antipads on In1 |
| QSPI_IO1 B.Cu | 101 | (13.56–14.56, 51.5) | The BAT_FAULT_N In2 slot |
| USB_DP B.Cu | 175 | (11.95, 58.45–59.91) and the 45° lead | The BUZZ_DRV In2 slot |
| USB_DM B.Cu | 54 | (10.05, 64.51–65.99) | The 3V3 island edge moved; DM is already on the split in R6 |
| NRST In2 | 219 | (36.44–37.13, 49.8–51.67) | B.Cu GND island removed |
| QSPI_IO2 B.Cu | 14 | (25.9, 46.6–47.1) | Fill-edge shift |
| Others | ≤ 12 each | SWDIO, SWCLK, QSPI_NCS/IO3, SPI1, IMU_CS | Fill-edge noise |

Places where R6 was unreferenced and R7 is referenced (improvements, 592 samples): SWDIO In2 (18.5–23.3,
55.2–86.1), SWCLK F.Cu (15.75–44.15, 69.5–99.6), QSPI_IO3 B.Cu (19.9–20.4, 42.4–42.9), NRST B.Cu/In1/In2,
QSPI_CLK F.Cu (109 → 15 samples), QSPI_NCS B.Cu.

HSE and SPI1/IMU: no change (HSE_IN/OUT and SPI1_* sample counts are identical). The R6 protected In2 3V3
checkpoints ("HSE reference keeper" R6 (16.5, 43) and "feeder" (15.95, 47.93), translated +18) are still
inside the 3V3 fill. No net other than the removed port nets comes within 1.5 mm of HSE copper or Y1's pads
any closer than in R6. LED_RED is a new neighbour at about 1.3 mm, on the other layer (approximate).

### 4.2 Layer changes of critical nets: nearest GND via or THT GND pad

| Via | R6 | R7 |
|---|---|---|
| QSPI_IO0 (12.9, 44.4), new | — | **3.55 mm** |
| QSPI_IO0 (15.55, 50.85), new | — | **1.61 mm** |
| QSPI_IO1 (13.0, 51.5) | 2.22 mm (M3_R5 exception) | **3.64 mm** |
| QSPI_IO1 (25.2, 42.9), IO2 ×3, IO3 ×2, NCS ×2 | 0.75–0.92 mm | unchanged |
| All critical vias, median / count > 1.5 mm | 1.57 mm / 24 of 47 | 1.60 mm / 26 of 49 |

### 4.3 Plane connectivity

| Fill | R6 | R7 |
|---|---|---|
| GND_In1 | 1 polygon, 3771.7 mm² | 1 polygon, 4660.3 mm². The R6 In1 port signals (GPS/RADIO/TLM, 79 mm) are gone; In1 now carries only CAM_TX_WIRE, NRST, SWCLK and SWDIO, as R6 did besides the ports |
| 3V3_In2 | 11 polygons, 479.1 mm², largest 202.3 | 6 polygons, 608.2 mm², largest 470.0 (15 vias). The island under the USB pair (10.2–13.5, 58.6–75.5) is 31.1 mm² with 1 via (R6: a 91.8 mm² island, also 1 via) |
| GND_F / GND_B | 61 / 48 polygons | 46 / 35 polygons (more area, fewer islands) |
| F.Cu GND under U1 (15.2–28.5, 46.8–60.2) | 90.98 mm² in 11 polygons | 98.93 mm² in 6 polygons. LED_RED's new path under U1 did not reduce it |

### 4.4 3V3 supply resistance (DC, `tools/dc_solve.py`, source L1:2, grid 0.1 mm)

| Sink | R6 | R7 |
|---|---|---|
| U1 all VDD (6, 11, 27, 50, 75, 100) | 4.41 mΩ | 3.58 mΩ |
| U1.50 (15.85, 45.95), west side near the surgery | 6.83 mΩ | 6.16 mΩ |
| U1.75 (14.30, 59.50), above BUZZ_DRV's In2 cut | 21.93 mΩ | **42.85 mΩ** |
| U1.27 | 16.85 mΩ | 5.76 mΩ |
| U1.6 | 96.57 mΩ | 79.24 mΩ |
| U1.100 | 97.34 mΩ | 79.14 mΩ |
| U3.8 (QSPI flash VCC) | 6.38 mΩ | 6.16 mΩ |
| R164.1 (feed to 3V3A: IMU, barometer, VDDA) | 26.70 mΩ | 11.33 mΩ |
| FB30.1 (GNSS ferrite feed) | — | 4.81 mΩ |
| FB31.1 (radio ferrite feed: R161.1, then a 7.3 mm In2 0.25 mm trace to the plane) | — | 29.33 mΩ (3.5 mV at the radio's 119 mA; the handoff estimated about 33 mΩ) |

The board-wide 3V3 network is better than R6's. The parallel feed to all six VDD pins fell from 4.41 to
3.58 mΩ, and R164 (the 3V3A feed) from 26.7 to 11.3 mΩ. The band cut of stepB_handoff §4.8 is a cut against an
intermediate step-B layout, not against R6: compared with R6 the In2 3V3 plane gained area. U1.75 is the one
exception, with its resistance doubled (REGRESSION-02). U1.6 and U1.100 (about 80–97 mΩ in both revisions)
are fed by thin R6 tracks that this review did not change. All values are DC copper only and exclude
high-frequency impedance (Inference: the per-pin 100 nF decouplers carry the high-frequency current).

### 4.5 Pyro block, arming break, DRC rules

- **Copper.** No track or via of PYRO1_*, ARM1_*, RAW_ACT*, ACT_*, SERVO* or the CH1 parts changed (exact
  geometry match). Inside PYRO_BLOCK (x 4–42, y 84–114.4) R7 drops 19 copper items of R6's GPS_TX_MCU port
  net. It redraws one BUZZ_DRV B.Cu segment 0.05 mm shorter at (4.25, 71.2–85.0); that run is unchanged from
  R6. The only fill changes inside the block are added GND fill where those port items were.
- **XOR of all copper inside the block, R6-only area:** F.Cu 0.005 mm², In1 0.034, B.Cu 0.0001 (rounding), and
  In2 0.956 mm². The In2 figure is the removed GPS_TX_MCU segment.
- **Footprints.** J121, J124, Q124, R134 and the rest of the CH1 and actuator parts keep their positions and pads.
  check_r7's CH1 pad-spacing contract passes. The PYRO_BLOCK rule area is translated exactly (x 4–42,
  y 84–114.4), as check_actuators asserts.
- **m3.kicad_dru.** R6's lines 1–10 and 11–end are byte-identical in R7 (diff of the tail: identical). R7 adds
  33 lines of RF and module rules **before** the pyro rules. In KiCad's rule order a later matching rule takes
  precedence, so none of them can override a pyro rule, and none names a pyro, arming or actuator net.
  check_actuators' per-rule hashes (PYRO_RULE_SHA) are unchanged and pass. The whole-file DRU_SHA was updated
  for the R7 additions.
- **Arming break and sentinels** (check_actuators, rerun in the gate):
  - PYRO1_BUS = {J124.1, R134.2, R132.1}; PYRO1_IGN = {J121.2, R134.1}.
  - No test point on the bus or igniter nets.
  - Sentinel pins U1.2, U1.4, U1.5, U1.16 and U1.32 carry `unconnected-…` nets; PE10 (U1.40) and PE0 (U1.97) stay NC.
  - check_actuators lost only its R6 telemetry clauses (J130/J131/U14–U16), whose parts were removed.

### 4.6 High-current copper

RAW_ACT, BAT_IN and ACT_FET_S: REGRESSION-07, all unchanged at 3.96 / 3.91 / 1.36 mΩ. The input path near U9
did not change: the D8 TVS feed, C89/C95 and the BAT_IN_F pour. C84 (OS-CON hold-up) GND improved from an 8 mm
diagonal to three vias at x 9.0 (path 1.64 mm).

### 4.7 Routing style (new copper outside the strip: 352 tracks, 82 vias)

| Check | Result |
|---|---|
| Off-angle segments | 0 |
| Acute joints | 12 candidates: 8 are inside pads or are pad-entry stubs of 0.025–0.071 mm, 4 are real (REGRESSION-04) |
| Tiny segments (< 0.1 mm) | 8 |
| Jogs | 6 (R6 board: 81) |
| Exact duplicate tracks | 0 new (the 7 in R7 are all inherited from R6, for example BUZZ_DRV at R162.1) |
| New collinear overlaps | BAT_ILIM 0.566 mm, VLOGIC_SENSE 0.5 mm, BAT_FAULT_N In2 0.024 mm |
| Free ends | DRC 0 dangling. 2 BAT_ILIM ends T-join onto the R6 track body (9.875, 38.6) and (9.875, 37.6) |
| GND vias at layer changes | REGRESSION-06 |

## 5. Not regressions (checked)

- **J123 at (36.0, 34.6).** The GND THT pin replaces the R6 GND via (37.7, 34.7). Fit and DRC pass.
- **VBUS_SENSE escape.** A slow net. Its In2 link (13.99–15.65, 53.2) crosses no critical B.Cu run.
- **Removed In2 3V3 diagonal** (17.58, 34)–(21.78, 29.8). It was plane-to-plane; both ends are inside the 3V3 fill
  in both revisions.
- **Router vias of the 13 nets.** Their GND-via distances match R6 in aggregate.
- **Inherited off-angle segment.** The 3V3 B.Cu segment (41.35, 58.55)–(42.95, 57.15) is unchanged from R6
  (stepB_handoff §4.13).

## 6. Sources

- `docs/REQUIREMENTS.md` F4, F7–F10; `AGENTS.md` §2–3; `docs/M3_R5.md` §"Inherited return-path exceptions" (the
  1.5 mm criterion) and "pass 2"; `docs/M3_R6.md` (R6 DC values, the "104,241 critical reference samples" gate).
- `m3_design/assembly_review/sources/r6-independent-routing-reference-review-20261013.json`: method, critical-net
  list, protected checkpoints. `sources/r6_final_dc.json`: R6 dc_solve commands, reproduced exactly.
- `sources/r7_review/stepB_handoff.md` §4 (deviations 8–10) and `stepB_progress.md` §3–5.
- KiCad custom-rule precedence: KiCad 10.0 PCB Editor manual, "Custom design rules" → "Custom rule syntax":
  "Rules are evaluated in reverse order, meaning the last rule in the file is checked first". Once a matching
  rule is found, no further rules are checked (https://docs.kicad.org/10.0/en/pcbnew/pcbnew.html). The same
  convention is documented in `check_actuators.py` pass 7.
- TI TPS25947 datasheet SLVSFC9C (revised May 2026), https://www.ti.com/lit/ds/symlink/tps25947.pdf. Used here:
  - §4 Device Comparison Table: TPS259470LRPW is the active-current-limit, latch-off variant.
  - §7.3.5.3: the ITIMER pin left open gives the minimum delay.
  - §6.6: scalable and fixed fast-trip response 500 ns.
  - §8.3.1 Transient Protection: Schottky from OUT to ground.
  - §8.4.1 Layout Guidelines, p. 62–63: ILM away from switching signals, ILM capacitance < 50 pF, and the
    Schottky/OUT/GND loop minimized.

  D9's role (U9 OUT → D9) is from `docs/M3_R5.md` L7.

## 7. Inferences (not measured or not checked against a primary source)

- Electrical impact of REGRESSION-01: at the firmware's present QSPI clock (8 MHz, `m3_firmware/research/STORAGE_ACQUISITION.md`)
  and about 27 mm lines, the extra return detour (about 1–4 mm past the slot end at the via (15.6, 50.0)) and
  the 3.9 mm BUZZ_DRV coupling are unlikely to corrupt transfers. The GPIO edges (about 1–2 ns at a high
  OSPEEDR) set the coupling, not the clock rate. The finding rests on R6's stated acceptance criteria and AGENTS.md,
  not on a demonstrated failure. M3_R5 already asks for a QSPI write and read-back while the servos sweep.
- REGRESSION-02: USB full-speed edges (4–20 ns) make a 1.5 mm reference gap electrically small. NRST is a slow
  line filtered at the MCU.
- REGRESSION-03: the D9 return path is still continuous F.Cu pour, about 10 mm long. The added inductance (a few nH) mainly raises
  the negative clamp level during a U9 fast trip; it was not computed.
- REGRESSION-05: ESD coupling magnitudes were not computed.
- REGRESSION-08: by a rough mutual-capacitance estimate (about 0.05 pF/mm × 8 mm against about 5 pF on the node,
  R84 750 Ω), a QSPI_IO0 edge puts a spike of order 0.1–0.3 V lasting a few ns on ILM. That is far shorter than
  the 500 ns fast-trip response, so a nuisance trip is improbable but not excluded. A trip would latch the logic
  supply off (latch-off variant). Not measured and not simulated.
- All DC values assume 35 µm copper, 20 µm via plating and 20 °C, with no pad or contact resistance (dc_solve
  docstring).
