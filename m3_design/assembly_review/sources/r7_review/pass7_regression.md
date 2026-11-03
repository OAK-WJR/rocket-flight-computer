# R7 pass 7: board-wide regression and electrical integrity (fix pass 6)

Read-only review, 2026-10-18. Dimension: every copper and schematic change of fix pass 6 (agent F7, `m3_design/r7_polish.py`
stages `qspi6`, `sw6`, `logic_ss6`, `servo_fault6`, `v3v3_6`, `raw_act6`, `ties6`, `bat_in_f6`; `r7_sch.py` J31 value),
judged against the pass-6 board and, where useful, against R6. Focus:
- input capacitors C89 / C95 on BAT_IN_F;
- the buck hot loop and SW_NODE;
- ground returns and critical-reference sampling;
- power feeds and the DC solve, and the IPC-2152 record;
- actuator and pyro rules and the arming break;
- parity after the J31 value change;
- the fab package's binding to the board.

| Item | Value |
|---|---|
| Final board | `m3_design/assembly_review/m3.kicad_pcb`, SHA-256 `4673c0a0f9fd290af694d6ca5a97e99b3b225466882ba5c6e57a9ad856b96ebd`. It matches `fix6_F7_handoff.md`, M3_R7, R7_VALIDATION, STATUS, AGENTS and the fab manifest (`inputs_sha256/cad/m3.kicad_pcb`). Unchanged before and after the gate and the tests |
| Pass-6 board ("base") | SHA-256 `1ffc2585cbbb2a49623a5010b2792500849f06989cf43e48fb3e56068cddf9df` (F7's start copy `scratchpad/fx6/base.kicad_pcb`, SHA re-checked) |
| R6 board | `git show 3b215ba:m3_design/assembly_review/m3.kicad_pcb`, compared moved +18 mm in y |
| Schematic / rules | `schematic.net.xml` differs from the pass-6 copy (`scratchpad/fx5/proj/schematic.net.xml`, SHA `963c6369…`) in exactly one line, l.7333 `<value>915MHZ ANT SMA</value>` → `RADIO ANT SMA`. `telemetry.kicad_sch` `6615ba08…` → `f5e1df83…` (l.5286, J31 Value). `m3.kicad_sch` `47057f7d…` and `m3.kicad_dru` `1674d58b…` unchanged |
| Gate (rerun here) | `tools/check.sh` exit 0: DRC 0, unconnected 0, parity 0, ERC 0; audit OK; silk 0; R7 contract OK; routing hygiene 0 failing, 43 allowlisted, 0 stale, 0 out-of-date no-GND reasons, 30 leftovers recorded (0 unrecorded, 0 stale), 0 out-of-date route figures, 0 removable exceptions; actuator contract OK; fit OK |
| Tests (rerun here, KiCad Python) | test_route_check 45 OK, test_dc_solve 3 OK, test_r7_check 34 OK, test_fab_validation 23 OK. `git status --short` identical before and after (87 lines) |
| Tools | KiCad 10.0.6 `pcbnew` read-only scripts on SHA-checked copies in `scratchpad/p7reg/`; `tools/critical_reference.py`; `tools/dc_solve.py`; `kicad-cli pcb export gerbers` (scratch); `tools/fab_manifest.verify_manifest`; the pass-6 regression scripts (`dump.py`, `diff.py`, `detail.py`, `geo_export.py`, `neigh.py`, `newgap.py`, `isl_all.py`, `gexport.py` / `gpath.py`, `couple.py`, `batf.py`) and new `viaconn2.py`, `viaall.py`, `fillxor.py`, `zoneneigh.py`, `lobe.py`, `pairnet.py`, `netarea.py`, `gainu4.py`, `fps.py` |
| Fills | Saved fills throughout (the build fills natively) |

## 1. Summary

**No Critical and no Major findings.** Fix pass 6 did what `fix6_F7_handoff.md` says on every net it names, and all three
pass-6 findings in this dimension are closed or properly dispositioned (§2).

What holds:
- **Netlist, parts, rules.**
  - All 819 pads keep their net, position, size, layer and zone connection.
  - Of 252 footprints, only J31's Value field changed.
  - The netlist change is that one value. Parity 0, ERC 0, and `m3.kicad_dru` is unchanged.
- **Copper changed on 11 nets**, every one named in the handoff (§4.1): tracks 1,777 → 1,747 (64 removed, 34 added),
  vias 706 → 708 (+2 BAT_IN). Pour trims 23 → 22 (the B.Cu trim by the 3V3A hop is gone; the rest are renumbered).
- **C89 / C95 (P6-REGRESSION-01).**
  - Both new BAT_IN vias are joined to the BAT_IN_F fill (0.249 mm² of 0.283 mm² ring each) and to the In2 BAT_IN fill
    (0.225 / 0.249 mm²).
  - The edge via (9.2, 36.05) now sits wholly in BAT_IN_F (0.030 → 0.280 mm²).
  - DC, solved here on both boards: C89.1 → U9.5 10.35 → 7.05 mΩ, C95.1 → U9.5 7.37 → 5.60 mΩ, and unrecorded
    improvements D8.1 → U9.5 12.79 → 10.36 and J1.1 → C89.1 19.75 → 16.45 mΩ.
- **Buck.** SW_NODE copper changed only between C5.1 and L1.1: 9.661 → 9.839 mm², track 7.294 → 7.660 mm. The input
  loop C7 / U2.2-3 / U2.4 and every GND return are untouched. The new copper's only neighbours within 0.6 mm are the GND
  pour, C7.2 (0.245 mm), the 3V3 via (18.70, 35.28) (0.170 → 0.213 mm) and C5.2 (0.29 mm).
- **Critical reference.**
  - Base → final: 0 samples lost and 0 candidate-new, by both the R6 method (69,925 referenced) and the extended
    method (168,989).
  - R6 → final: 603 lost / 882 new (R6 method) and 2,312 / 4,325 (extended), identical to pass 6.
- **GND returns.**
  - No via of any net lost or gained a fill join on any layer, except the BAT_IN vias above (708 vias compared).
  - No SMD GND pad's return to a GND via or plated GND hole changed by more than 0.05 mm (173 pads).
  - GND F/B single-via pieces 35 → 34, as C14 states: the 39.9 mm² B.Cu piece that the RAW_ACT duplicate fenced off
    merged into the main piece.
- **Pyro and actuator.**
  - No track, via, pad or fill of any PYRO1_* or ARM1_* net changed.
  - The arming break widened on B.Cu: RAW_ACT to PYRO1_BUS (J124.1) 1.10 → 2.483 mm. The deleted duplicate was the
    nearest B.Cu RAW_ACT copper. F.Cu stays at rule E's 1.0 mm.
  - RAW_ACT → J124.2 is 1.47 → 1.50 mΩ.
  - DRC passes rules A–H and A2, and `check_actuators` is OK.
- **IPC-2152 record.** The three 7.7 A paths and their peaks are unchanged at 0.1 mm, except RAW_ACT's +0.03 mΩ:
  - RAW_ACT Q121 → J122 3.95 → 3.98 mΩ, peak 5.75 A/mm at (19.15, 84.52) on both boards;
  - BAT_IN J1 → Q120 4.58 / 4.58 mΩ, peak 6.17 A/mm at (10.45, 107.62);
  - ACT_FET_S 1.36 / 1.36 mΩ.

  So the record's "fix pass 6 changed none of the three necks" holds.
- **Fab package.**
  - `verify_manifest` OK: 173 inputs bound to `4673c0a0…`, 5 outputs.
  - A fresh `kicad-cli` export of F.Cu, In1, In2 and B.Cu equals the packaged Gerbers line for line (date lines
    excluded).
  - The PTH drill's T1 (Ø0.300) has 708 hits, matching the board's 708 vias within 2 µm, including (9.7, 31.75) and
    (9.7, 35.5).
  - The BOM differs from F7's pre-fix copy only in line 36 (J31 comment), and the CPL is byte-identical.

Three Minor findings:

| ID | Severity | One line |
|---|---|---|
| P7-REGRESSION-01 | Minor | Unrecorded pour change. Deleting RAW_ACT's B.Cu duplicate (`raw_act6`) let BAT_IN_B fill a 24.2 mm² lobe (x 7.17–13.6, y 82.54–94.4) that holds no BAT_IN pad or via and joins the old fill only along about 2.9 mm south-east of J124.2. It replaces 27.9 mm² of GND B.Cu and puts battery voltage 0.30 mm from 3V3, RAW_ACT, USB_ILIM, BUZZ_* and SERVO2_OUT copper that GND used to border (ARM1_SENSE 2.15 → 0.65 mm). The handoff, M3_R7 and R7_VALIDATION do not mention it |
| P7-REGRESSION-02 | Minor | `ties6` redrew the 3V3A B.Cu hop in the same NE / E / SE shape with the E leg 0.121 mm lower. That halves its gap to the GND via (36.5, 76.54), 0.34 → 0.169 mm, and makes the run 4 µm shorter than `chain_detour`'s pass limit (2.4043 against 2.4083 mm). The detour stays, so the metric passes without cleaner copper. C15's failure mode ("fails the IMU's analog supply") understates a 3V3A–GND short: 3V3A also feeds U1 VDDA / VREF+ and the barometer through R164 (2.2 Ω, 0603), which would take about 1.5 A / 5 W |
| P7-REGRESSION-03 | Minor | The "fix pass 6's copper" adjacency list (M3_R7, C15, F7 §5), which claims every edge gap under 0.2 mm of added copper, omits SERVO4_MCU's redrawn In2 diagonal (16.005, 101.627)–(18.005, 103.627) at 0.192 mm from RAW_PROTECTED's via (18.05, 102.87). The geometry is unchanged since R6 (same line, same gap), but a short there, unlike the listed ones, puts the 8.4 V protected battery rail on PA3 and, through D121, onto 3V3. It is internal-layer copper, so only a fabrication defect, which E-test screens |

## 2. Pass-6 findings in this dimension: closure check

| Pass-6 ID | Disposition in R7_VALIDATION (l.612–614) | Verified on the final board |
|---|---|---|
| P6-REGRESSION-01 (BAT_IN_F without its own stitch) | Fixed (`bat_in_f6`) | **Closed.** BAT_IN_F outline (4.4, 25.7)…(9.0, 31.4), (9.9, 31.4), (9.9, 36.9), (4.4, 36.9); fill 37.397 → 41.816 mm², one piece, 3 vias (was 0). Via ring ∩ fill (`viaconn2.py`): (9.7, 31.75) F.Cu 0.249 / In2 BAT_IN 0.225 mm²; (9.7, 35.5) 0.249 / 0.249; (9.2, 36.05) 0.280 / 0.280 (F.Cu was 0.030). C95.1's 0.2 mm track now has 0.451 mm² of overlap with the fill. DC (0.1 mm, both boards solved here): C89:1 → U9:5 **10.35 → 7.05**, C95:1 → U9:5 **7.37 → 5.60** mΩ, matching F7 and M3_R7 l.825. Both vias keep 0.25 mm from the In2 GND strip and 0.251 mm from 3V3_In2, and 0.15 mm from GND_B. The radio corridor has no B.Cu copper within 1 mm of them (nearest: BAT_ILIM B.Cu 0.979 mm). Critical reference 0 / 0. The BAT_IN_F fill's foreign neighbours all stay at its 0.3 mm zone clearance; new ones are BAT_ILIM's F.Cu run (9.875, 36.475)–(10.65, 36.475) and R84.1 (0.30 / 0.362 mm). That is DC copper beside the ILM node TI asks to keep away from *switching* signals (SLVSFC9C §8.4.1, p. 61), so it is not a concern. Note: C89 / C95 return through BAT_DAMP and R166 (0.33 Ω, 2512) to GND (netlist), so they are a damped bulk / snubber network. The mΩ of copper is about 2 % of that series resistance, and the electrical effect of the old one-via dependency was always small (Inference) |
| P6-REGRESSION-02 (SERVO4_MCU / CAM_FAULT_N 22.9 mm at 0.165 mm) | Fixed (`servo_fault6`) | **Closed.** Proximity length on In2 (0.01 mm sampling, tracks and vias), base → final: ≤ 0.2 mm **30.45 → 6.59**, ≤ 0.3 31.26 → 7.33, ≤ 0.5 36.16 → 12.03 mm (CAM_FAULT_N side; SERVO4 side 30.53 → 6.76). Parallel-pair table (`couple.py`) 33.24 → 9.61 mm. The minimum stays 0.161 mm (the base's E runs at y 103.63 / 103.94, recorded). The new CAM_FAULT_N step (14.641, 91.85) → (15.19, 92.399) and the x 15.19 run keep CAM_PWR_EN's via at 0.165 mm (inherited; recorded). ARM1_SENSE's vias are at 0.265 mm. CAM_FAULT_N keeps 0.341 mm to the In2 BAT_IN fill (unchanged). Lengths CAM_FAULT_N 95.621 → 95.072 mm, SERVO4_MCU 96.38 → 96.38 mm |
| P6-REGRESSION-03 (two unrecorded adjacencies) | Recorded (C15, M3_R7 l.563–568) | **Properly dispositioned.** Re-measured: GND via (35.85, 53.275) – NRST via (35.80, 53.95) 0.177 mm edge (hole to hole 0.377 mm), – NRST B.Cu (33.45, 51.6)–(35.8, 53.95) 0.188 mm; CAM_FAULT_N In2 (y 103.938) – GND vias (24.55 / 25.45, 104.475) 0.162 mm. C15 states the failure modes as the pass-6 report did |

Related items from other dimensions that touch this focus:
- **P6-ROUTING_GEOMETRY-01 (SW_NODE).** Closed electrically (§4.3).
- **P6-ROUTING_QUALITY-01 (QSPI_IO3).** One F.Cu segment (22.5, 40.3)–(22.5, 35.4):
  - 24.055 → 21.655 mm;
  - 0.208 mm to U3.8 (3V3);
  - 0 reference samples lost.
  - It now runs beside QSPI_CLK (x 23.21) at a 0.51 mm edge gap for 4.9 mm (was 3.9 mm), with solid In1 GND 0.2 mm
    below. Immaterial at the firmware's 8 MHz QSPI clock (Inference).
- **P6-DOCS-01.** Its copper (3V3 dip, RAW_ACT duplicate, the `ties6` runs) is reviewed in §4. Two side effects are
  findings 01 and 02.

## 3. Findings

| ID | Severity | Requirement | Finding | Evidence (final-board coordinates, mm) | Fix |
|---|---|---|---|---|---|
| P7-REGRESSION-01 | Minor | AGENTS.md §3 / REQUIREMENTS M2 (records state what was verified; review of every copper change); `fix6_F7_handoff.md` §3 ("every polish stage keeps the pad groups with the pours", fills "equal `fx6/d4`") | `raw_act6` deleted RAW_ACT's 0.2 mm B.Cu run J124.2 → Q121.9, whose docstring notes that 11.65 mm of it lay inside the BAT_IN_B outline. Its SE leg (10.0, 90.78) → (12.5, 93.28) had fenced off the outline's north-east part, so that part was an island of BAT_IN_B (removed by the filler) and GND_B filled it. With the leg gone, BAT_IN_B now fills it: a **24.2 mm² lobe** (outline box x 7.17–13.6, y 82.54–94.4) that holds **no BAT_IN pad or via**. It joins the old fill only along about 2.9 mm at x 10.71–12.1, y 92.19–94.4, the old leg's clearance edge south-east of J124.2. **GND_B loses 27.9 mm²** there (x 7.02–13.98, y 82.11–94.71; part of the main B.Cu GND piece, no via in it). In that area, copper that used to face GND at 0.15 mm now faces battery voltage at the 0.3 mm zone clearance. The lobe carries no current: J1 → Q120 4.58 / 4.58 mΩ, J1 → U9 15.18 / 15.18 mΩ. Nothing in the handoff, the `raw_act6` docstring, M3_R7 or R7_VALIDATION records the BAT_IN_B or GND_B fill change. The handoff lists only DC and pad-group effects, and R7_VALIDATION A45 (l.812) and M3_R7 l.747 still cite "the BAT_IN_B pour from y 80.9" only as a routing blocker. Inference on the electrical effect: small. No GND via lost a join; no SMD GND pad return moved; critical reference 0 / 0; DRC passes (rule F keeps BAT_IN 0.5 mm from J124.1 as before). The new BAT_IN neighbours are shorts that only fabrication defects or a scratched mask could make, which E-test screens. Still, they put the unswitched battery next to: RAW_ACT (bypassing the actuator switch Q120 / Q121); 3V3 (an overvoltage on the logic rail); USB_ILIM (TPS2553 ILIM); and ARM1_SENSE (it would read "armed" with the plug out, the opposite of C15's "reads disarmed" kind) | `fillxor.py` (fill gained / lost per zone, base → final): BAT_IN_B +25.35 mm² outline (24.21 mm² net of pad holes), box 7.17–13.6 × 82.54–94.4; GND_B −27.892 mm², box 7.02–13.98 × 82.11–94.71; GND_B +10.476 mm², box 7.51–12.75 × 94.71–110.93 (where the duplicate ran). `isl_all.py`: BAT_IN_B 69.839 → 94.049 mm², box x 0.6–12.1 → 0.6–13.6, still 12 vias (all at x 1.1 / 6.8). `lobe.py`: no BAT_IN pad or via inside the gained region; contact with the old fill x 10.71–12.1, y 92.19–94.4, about 2.92 mm. `zoneneigh.py` (BAT_IN_B fill to foreign copper, base → final): USB_ILIM (7.83, 82.80)–(9.03, 81.60) none → 0.30 and R85.1 → 0.30; BUZZ_OUT (9.60, 82.90)–(12.40, 85.70) → 0.30, Q123.3 → 0.301; BUZZ_G (7.17, 84.23)–(7.17, 81.87) → 0.30; RAW_ACT C150.1 → 0.30, RAW_ACT via (12.80, 87.00) → 0.30, track (14.0, 87.0)–(12.8, 87.0) → 0.35; 3V3 via (12.50, 89.20) (A43's In2 feed) → 0.30; GND via (13.95, 93.75) → 0.30; SERVO2_OUT R151.2 → 0.334. `pairnet.py`: BAT_IN – ARM1_SENSE on B.Cu 2.151 → 0.654 mm (via (14.55, 94.15)). DC (`dc_solve.py` 0.1 mm, both boards): BAT_IN J1:1 → Q120:5–9 4.58 → 4.58, peak 6.17 A/mm at (10.45, 107.62) on both; free cells 108,269 → 111,182. Netlist: R85 66.5k USB_ILIM–GND (U10.5 ILIM); C150 22 µF RAW_ACT–GND; Q123.3 BUZZ_OUT | Either record it (M3_R7 `raw_act6` bullet and R7_VALIDATION P6-DOCS-01 row: BAT_IN_B +24.2 mm² dead-end lobe, GND_B −27.9 mm², the new 0.3 mm BAT_IN neighbours with their short consequences), or restore the GND there by cutting BAT_IN_B's outline back to its old fill. For example, end the outline along the old leg's clearance edge (the line through (10.71, 92.19)–(12.1, 94.4)) or at x ≈ 10.7 north of y 92.2. The deletion stays, BAT_IN's DC is unchanged (the lobe carries no current), and GND_B refills the area. A rebuild then needs the gate, critical reference and DC re-run |
| P7-REGRESSION-02 | Minor | AGENTS.md §3 (clean routing judged on the copper, not the metric; records complete); REQUIREMENTS M2; C15 failure-mode statement | `ties6` "fixed" the chain_detour of the 3V3A B.Cu hop between vias (35.5, 76.54) and (37.4, 76.52) round the GND via (36.5, 76.54). It kept the same NE / E / SE shape and lowered the E leg from y 75.8 to y 75.9213. The run is 2.5048 → 2.4043 mm against an octilinear distance of 1.9083 mm. `route_check` flags a chain when L − oct > 0.5 mm **and** L > 1.25 × oct, so the pass limit is 2.4083 mm and the redraw passes by 4.0 µm (excess 0.4960 mm). The detour round the GND via is as much a detour as before, so the gate no longer sees it but the copper is no cleaner. The price is the hop's edge gap to that GND via: **0.34 → 0.169 mm** (`newgap.py`). C15 and M3_R7 record the gap, but give the failure mode as "fails the IMU's analog supply at bring-up". The netlist says more: 3V3A = U4.5 / U4.8 (IMU), **U1.20 VREF+ and U1.21 VDDA**, U5.1 / U5.2 (MS5611 barometer) and C10 / C11 / C21 / C22 / C30–C32, fed from 3V3 through **R164 2.2 Ω 1 % 0603** (C22939). A hard short draws about 3.3 V / 2.2 Ω ≈ 1.5 A, about 5 W in an 0603 resistor (Inference: it would burn open). The MCU ADC reference, the IMU and the barometer are lost. Not a pyro-safety case (the gates are defined off), and E-test screens it (Inference). Here the change made a recorded margin worse to satisfy a threshold | Lengths from the drawn points: base (35.5, 76.54)–(36.24, 75.8)–(36.68, 75.8)–(37.4, 76.52) 2.5048 mm; final (35.5, 76.54)–(36.1187, 75.9213)–(36.8013, 75.9213)–(37.4, 76.52) 2.4043 mm; oct = 1.9 + 0.4142 × 0.02 = 1.9083 mm; `tools/route_check.py` l.1786–1794 (`CHAIN_DETOUR_MAX` 1.25, `CHAIN_DETOUR_SLACK` 0.5, l.176–177). Gap: `newgap.py` 0.169 mm (3V3A (36.119, 75.921)–(36.801, 75.921) to via (36.50, 76.54), 0.6 mm GND via); base 0.34 mm (F7 §5). Netlist `schematic.net.xml` net 3V3A (listed left); R164 in `fab/m3_bom_jlc.csv` l.73 | Restore the 0.34 mm drawing and add a `chain_detour` allowlist entry whose measured reason is the GND via on the straight line (or move that GND via, if a legal spot exists). Otherwise correct C15 / M3_R7's failure mode to "3V3A–GND loads 3V3 through R164 (≈ 1.5 A, R164 burns open); IMU, barometer and MCU VDDA / VREF+ lost at bring-up" and state that the redraw was sized to the gate's threshold |
| P7-REGRESSION-03 | Minor | AGENTS.md §3 (records complete); M3_R7 l.570–577 "fix pass 6's copper (F7, `newgap.py` on every added track and via)" and C15 | `servo_fault6` replaced SERVO4_MCU's end diagonal with a shorter one on the same line (x − y = −85.622): (16.005, 101.627)–(18.005, 103.627), so it is added copper by the diff. It passes RAW_PROTECTED's 0.6 mm via (18.05, 102.87) at **0.192 mm**. The list of fix-pass-6 copper names that via only as a blocker ("pinned by RAW_PROTECTED's via") and lists 0.161–0.194 mm gaps to CAM_FAULT_N and 3V3A / LOGIC_SS gaps, not this one. It is the pair with the most consequential short. RAW_PROTECTED is U9's protected battery output (to 8.4 V). SERVO4_MCU is PA3 (U1.25) itself, with D121 (SRV05-4) IO4 and R157 10k / R153 1k. C15's closing sentence ("none can fire a channel or put RAW_ACT on an MCU pin") does not cover RAW_PROTECTED. The gap is not a regression: R6 and the pass-5 and pass-6 boards have it at the same 0.192 mm. And both items are on In2, so a short can only be a laminate defect (Inference: E-test screens it) | `newgap.py`: (0.192, SERVO4_MCU In2 (16.005, 101.627)–(18.005, 103.627), RAW_PROTECTED via (18.05, 102.87)). History (`dump.py`): R6 (+18) diagonal (15.7548, 101.3766)–(18.005, 103.6268), 0.192; pass-5 board (15.8384, 101.4602)–…, 0.192; pass-6 board (15.505, 101.1268)–…, 0.192. Netlist: SERVO4_MCU = D121.6, R153.1, R157.1, U1.25 (PA3); RAW_PROTECTED = U9.6 output | Add it to the fix-pass-6 list and C15 with its failure mode (RAW_PROTECTED on PA3 / D121 → 3V3 overvoltage; internal layer, inherited from R6), or say that the list covers only gaps that fix-pass copper newly creates |

## 4. Measurements

### 4.1 What changed (base → final; `dump.py`, `diff.py`, `detail.py`)

Tracks 1,777 → 1,747 (64 removed, 34 added). Vias 706 → 708. Zones 54 → 53 (rule areas: R7_POUR_TRIM_12 B.Cu at
(36.4–36.6, 75.1) removed, TRIM_13…23 renumbered 12…22 with identical outlines). Pads: none changed. Footprints: J31
Value only.

| Net | Tracks −/+ | Vias −/+ | Stage and check |
|---|---|---|---|
| GND | 23 / 10 | 0 / 0 | `ties6`: J1.2 → via (24.55, 108.05) one N run from inside J1.2 (1.18 mm from its centre); J3.4 → A1B12, J3.1 → B1A12 (F.Cu, 0.9 mm each); J3.1 → R85.2 and → C28.2 (B.Cu); R130.2 → R178.2 (F.Cu, chamfered L) |
| RAW_ACT | 9 / 0 | 0 / 0 | `raw_act6`: the B.Cu duplicate J124.2 → Q121.9 (31.29 mm), deleted; P7-REGRESSION-01 |
| SW_NODE | 5 / 5 | 0 / 0 | `sw6` (§4.3) |
| QSPI_IO3 | 5 / 1 | 0 / 0 | `qspi6` |
| 3V3 | 5 / 2 | 0 / 0 | `v3v3_6`: (31.1, 54.5) → (33.65, 54.5) → (36.5, 51.65), 0.25 mm |
| LOGIC_SS | 5 / 2 | 0 / 0 | `logic_ss6`: (28.95, 29.35) → (28.95, 29.65) → (27.55, 31.05) |
| 3V3A | 3 / 3 | 0 / 0 | `ties6`: hop E leg y 75.8 → 75.9213; P7-REGRESSION-02 |
| CAM_FAULT_N / SERVO4_MCU | 3 / 5, 2 / 4 | 0 / 0 | `servo_fault6` |
| ACT_FET_S | 4 / 2 | 0 / 0 | `ties6`: R120.1 → (5.17, 94.64) → Q120.1, 0.4 mm, inside ACT_FET_S_B (fill unchanged) |
| BAT_IN | 0 / 0 | 0 / 2 | `bat_in_f6`: (9.7, 31.75), (9.7, 35.5), 0.6 / 0.3 mm |

Fills (`fillxor.py`, saved fills; areas in mm²):
- BAT_IN_F +4.419 (x 8.89–9.9, y 31.39–36.57).
- **BAT_IN_B +25.35 / GND_B −27.89** (P7-REGRESSION-01).
- GND_B +10.48 (the old duplicate's corridor, merging a 39.9 mm² single-via piece) and +6.03 at the 3V3A hop / U4 (the
  removed trim; +0.245 inside U4's courtyard, where 1.185 already lay).
- GND_F −4.41 (BAT_IN_F growth), +4.11 / −2.03 (3V3 redraw), +1.89 (QSPI_IO3 bump gone).
- GND_In1 −0.96 / −0.76 (the two new antipads).
- R6_BAT_IN_In2 760.271 → 760.307 (one piece, from y 31.5).
- R7_GND_In2_strip −0.042 (the via (9.7, 31.75) notch).
- 3V3_In2 −0.037.
- No pyro, RAW_ACT, ACT_FET_S, 3V3A or CAM_5V fill changed.

### 4.2 New copper and its neighbours (`newgap.py`, every added track and via, edge gap < 0.25 mm; pours at their zone clearance omitted)

| Gap | New item | Neighbour | Status |
|---:|---|---|---|
| 0.161 | SERVO4_MCU In2 diagonal (16.005, 101.627)–(18.005, 103.627) | CAM_FAULT_N In2 E run y 103.94 | base geometry; recorded |
| 0.164 | SERVO4_MCU In2 x 15.505 | CAM_FAULT_N via (16.04, 67.46) | base; recorded |
| 0.165 | CAM_FAULT_N In2 x 15.19 (92.40–101.30) | CAM_PWR_EN via (14.65, 92.95) | base; recorded |
| 0.169 | 3V3A B.Cu hop E leg | GND via (36.50, 76.54) | new (was 0.34); recorded; P7-REGRESSION-02 |
| 0.183 / 0.187 | LOGIC_SS diagonal | U11.12 (GND) / GND via (28.13, 31.30) | new / base minimum; recorded |
| 0.192 | SERVO4_MCU In2 diagonal | RAW_PROTECTED via (18.05, 102.87) | R6 geometry; **not recorded** (P7-REGRESSION-03) |
| 0.194 | SERVO4_MCU diagonal and x 16.005 run | CAM_FAULT_N end diagonal | recorded |
| 0.206 | BAT_IN vias (F.Cu) | GND_F fill | the via pad crosses the BAT_IN_F outline by 0.1 mm at x 10.0; DRC-clean |
| 0.208 | QSPI_IO3 x 22.5 | U3.8 (3V3) | recorded (0.206) |
| 0.213 | SW_NODE (17.92, 35.65)–(18.52, 36.25) | 3V3 via (18.70, 35.28) | recorded (was 0.170) |
| 0.245 | SW_NODE gap pieces | C7.2 (GND) | recorded |

With a 0.8 mm search, the only pyro / actuator neighbours of new copper are:
- GND (25.97, 87.2–87.9) at 0.297 mm from PYRO1_CONT's F.Cu run (26.83, 88.42)–(25.22, 88.42). It ends at R130.2's
  centre as before, so the gap is unchanged; a short reads "no continuity".
- The chamfer, 0.587 mm from R130.1.
- ACT_FET_S at 0.377 mm from R120.2 (ACT_GATE), the same x as the base, unchanged.
- CAM_FAULT_N at 0.265 mm from ARM1_SENSE's vias (14.55, 94.15 / 97.55), inherited.

Parallel coupling of the changed nets (`couple.py` and an all-nets variant, same layer, edge ≤ 0.6 mm), base → final:
- CAM_FAULT_N – SERVO4_MCU 33.24 → 9.61 mm;
- QSPI_IO3 – QSPI_CLK 3.9 → 4.9 mm at 0.51 mm;
- LOGIC_SS – LOGIC_ILIM 0.96 mm at 0.224 → 0.90 mm at 0.30;
- 3V3 – PULLPIN (2.63 mm at 0.224) and 3V3 – SWCLK gone;
- RAW_ACT – ACT_EN B.Cu (2.49 mm at 0.477) gone.

### 4.3 Buck converter (U2 AP63203, L1, C5, C7, C9)

- The input hot loop is untouched: C7 (VLOGIC–GND, B.Cu (20.8, 33.0)) to U2.2 / U2.3 (VIN) and U2.4 (GND), and
  C84 / C9. So is U2.5 → C5.1 (0.4 mm).
- SW_NODE C5.1 → L1.1: SE 0.849, E 1.70, NE 1.414, E 0.70, NE 1.697 (0.6 mm, B.Cu), ending at (23.12, 34.05) inside
  L1.1 (x 22.1–23.7, y 31.25–34.75).
- Node copper 9.661 → 9.839 mm² (+1.8 %), track 7.294 → 7.660 mm (`netarea.py`).
- Neighbours within 0.6 mm (`neigh.py`): GND (pour 0.15, C7.2 0.245), 3V3 via (18.70, 35.28) 0.170 → 0.213, BST C5.2
  0.29 (unchanged). No new net.
- The QSPI F.Cu lines in the area (QSPI_IO0, QSPI_CLK, QSPI_IO3) are shielded by the solid In1 GND plane (critical
  reference 0 / 0).
- The +0.18 mm² of switching-node copper is a small step against the AP63203 data sheet's "keep the SW node small"
  layout advice (Diodes AP63200/AP63201/AP63203/AP63205 data sheet, Layout section). It is the price of removing
  allowlist A3–A5 and is recorded (Inference: EMI effect negligible).

### 4.4 GND returns and pieces

- **Via joins** (`viaall.py`: every via's ring ∩ its own net's fill on F.Cu, In1, In2 and B.Cu, both boards): identical
  for all 706 common vias except BAT_IN (9.2, 36.05) F.Cu 0.030 → 0.280. The two new vias are as in §2.
- **SMD GND pad returns** (`gexport.py` / `gpath.py`, 0.05 mm geodesic over F.Cu / B.Cu GND copper to a GND via or
  plated GND hole): no change above 0.05 mm on any of 173 pads. That includes C88.2 (U9's 100 nF), C7.2 and C9.2 (the
  buck), C28.2 and R85.2 (redrawn ties), and R130.2 / R178.2.
- **Pieces** (`isl_all.py`): 96 → 95.
  - Via-less pieces: BAT_IN_F gone; ACT_FET_S_B (inherited) remains.
  - GND F/B pieces 78 → 77; single-via 35 → 34 (C14 states 34 of 77).
  - The GND B.Cu piece round via (36.5, 76.54) is now 0.630 mm² (box 35.87–37.04 × 76.22–76.91).

### 4.5 Critical-net reference (`tools/critical_reference.py`)

| Comparison | Lost | Candidate-new |
|---|---:|---:|
| Base → final, R6 method | **0** (69,925 referenced) | **0** |
| Base → final, extended | **0** (168,989 referenced) | **0** |
| R6 (+18 mm) → final, R6 method | 603 | 882 |
| R6 (+18 mm) → final, extended | 2,312 | 4,325 |

The R6 rows equal pass 6's, and the candidate total fell by 735 samples, which is QSPI_IO3's 2.4 mm. The new BAT_IN
vias' In1 antipads and the In2 strip notch touch no critical copper.

### 4.6 DC solves (`tools/dc_solve.py`, board stack-up 35 / 30 / 30 / 35 µm, 0.1 mm grid; both boards solved here)

| Path (mΩ) | Base | Final | F7 / M3_R7 |
|---|---:|---:|---:|
| RAW_ACT Q121:5–9 → J122:2,5,8,11 (7.7 A) | 3.95 | **3.98** (peak 5.75 A/mm at (19.15, 84.52) on both; F.Cu 100 % at mid-path on both) | 3.98 |
| RAW_ACT Q121:5–9 → J124:2 (pyro bus feed) | 1.47 | **1.50** | 1.50 |
| RAW_ACT Q121:5–9 → R177:1 (sense tap) | 86.54 | **86.57** | 86.57 |
| BAT_IN J1:1 → Q120:5–9 (7.7 A) | 4.58 | **4.58** (peak 6.17 A/mm at (10.45, 107.62) on both) | 4.58 |
| ACT_FET_S Q120:1–3 → Q121:1–3 (7.7 A) | 1.36 | **1.36** | 1.36 |
| BAT_IN J1:1 → U9:5 | 15.18 | **15.18** | 15.18 |
| BAT_IN C89:1 → U9:5 | 10.35 | **7.05** | 7.05 |
| BAT_IN C95:1 → U9:5 | 7.37 | **5.60** | 5.60 |
| BAT_IN D8:1 → U9:5 (TVS) | 12.79 | **10.36** | not given |
| BAT_IN J1:1 → C89:1 | 19.75 | **16.45** | not given |
| BAT_IN C88:1 → U9:5 (100 nF at the pin) | 2.61 | **2.61** | — |
| 3V3 L1:2 → U1:75 / FB31:1 / U1:100 | 15.64 / 14.66 / 78.23 | **15.64 / 14.66 / 73.46** | same |
| 3V3 L1:2 → FB30:1 / U1:27 / U3:8 / C9:1 (M3_R7's † rows, "not re-solved") | 5.53 / 6.85 / 6.76 / 2.48 | **5.53 / 6.85 / 6.76 / 2.48** | 5.53 / 6.85 / 6.76 / 2.48 (now confirmed) |
| 3V3A U4:5 → C31:1 / U4:8 → C31:1 | 5.86 / 3.32 | **5.84 / 3.32** | 5.84 / — |
| SW_NODE U2:5 → L1:1 (0.05 mm grid) | 5.14 | **5.37** | — |
| SW_NODE C5:1 → L1:1 (0.05 mm grid) | 3.89 | **4.11** | — |

- Every F7 figure reproduces.
- The two unrecorded BAT_IN rows (D8, J1 → C89) improved.
- The SW_NODE rise (+0.23 mΩ) is about 0.2 mW at the converter's ≤ 1 A load (Inference).
- The BAT_IN_B lobe (P7-REGRESSION-01) adds 2,913 free cells to the BAT_IN solve but no conductance on any path.
- GND J1.2 → J122 was not solved (§5).

### 4.7 Pyro block, arming break, actuator switch

- `m3.kicad_dru` unchanged (`1674d58b…`, equal to the manifest); DRC 0 with rules A–H and A2; `check_actuators` OK.
- **Arming break** (rule E, RAW_ACT to PYRO1_BUS / PYRO1_IGN ≥ 1.0 mm; `pairnet.py`):
  - B.Cu 1.10 → 2.483 mm (the duplicate's x 12.5 run was 1.10 mm from J124.1);
  - F.Cu 1.000 (R6_RAW_ACT_F to J124.1) unchanged;
  - PYRO1_IGN 6.956 mm unchanged.
  - BAT_IN to PYRO1_BUS 0.500 mm on B.Cu and In2 (rule F) unchanged.
- **Actuator switch:** ACT_FET_S_B's fill is identical, and Q120 / Q121 / R120 pads are unchanged. The R120.1 tie is a
  µA gate-pull-down path.
- **RAW_ACT paths:** RAW_ACT reaches J124.2 only through the F.Cu pour now (a plated hole in R6_RAW_ACT_F's single
  fill island): 1.47 → 1.50 mΩ. The B.Cu share of Q121 → J122 at mid-path was already 0 % on the base (§4.6). The
  current now enters F.Cu wholly through the via field beside Q121, which M3_R7 already lists as "not covered" by the
  IPC-2152 estimate.

### 4.8 Schematic, netlist, fab package

- Netlist: one line (J31 value). Board: J31's Value property only (`fps.py`, 252 footprints). Parity 0, ERC 0.
- Manifest: against F7's pre-fix copy (`scratchpad/fx6/fab_before/`), the inputs changed are `cad/m3.kicad_pcb` and
  `cad/telemetry.kicad_sch`, and the outputs `m3_gerber.zip`, `m3_bom_jlc.csv` and the two assembly PDFs.
  `verify_manifest` on the repository: OK (5 outputs).
- Gerbers: a fresh `kicad-cli pcb export gerbers` of F.Cu, In1.Cu, In2.Cu and B.Cu from the final board equals the zip's
  copper layers (0 differing lines, header dates excluded).
- Drill: `m3-PTH.drl` T1 Ø0.300 708 hits, each within 2 µm of a board via, none missing or extra.
- BOM l.36 "GNSS ANT SMA; RADIO ANT SMA" (was "915MHZ ANT SMA"); CPL byte-identical.

## 5. Checked and not raised

- **LOGIC_SS** (C85 470 nF soft-start of U11 TPS2121): the diagonal leaves U11.11 at its pad edge; 0.183 mm to U11.12
  (GND), DRC-legal at the 0.15 mm default and recorded. A short holds soft-start at 0 V: the power mux does not ramp,
  so the board is dead at bring-up.
- **3V3 redraw:** minimum gap 0.47 mm (F7). 3V3 L1 → U1:100 is in §4.6.
- **GND ties at J3 (USB-C):** the shell-to-contact runs stay inside GND copper. GND J3.1 → C28.2 is 0.267 mm from J3's
  locating NPTH (5.81, 78.19) against the 0.25 mm board rule (DRC hole clearance passes).
- **U4 (IMU) area:** GND B.Cu under U4's courtyard 1.185 → 1.430 mm² after trim 12 went. GND copper under the part
  already existed; no signal was added.
- **BAT_IN_F growth:** it took 4.4 mm² of signal-free GND F.Cu from the piece (8.71–20.66, 29.83–41.33). That piece keeps
  3 vias and is one piece (46.84 mm²).
- **J1.2 tie:** the new run ends inside J1.2's 2.6 mm pad, a plated GND hole joined on all layers. The battery-return
  current does not use this 0.2 mm tie.
- **GND DC (J1.2 → J122 GND pins):** not solved. The GND net's four-layer pour exceeds the solver's practical size at the
  0.1 mm grid that its 0.2 mm tracks require. The `ties6` GND changes are 0.2–0.25 mm local ties beside plated holes and
  pads already in the pours (Inference: no effect on the servo return).

## 6. Reproduction

All in `scratchpad/p7reg/`:
- Boards: `base.kicad_pcb`, `final.kicad_pcb` and `r6.kicad_pcb`, each SHA-checked. `base/` and `final/` hold
  `m3.kicad_pcb` plus the project and rules copies for `dc_solve`.
- Diff: `dump.py` → `base.json` / `final.json`; `diff.py`; `detail.py` → `detail.txt`; `fps.py` → `fp_*.json`;
  `ra.py` (zone outlines); `fillxor.py` (fill changes).
- Fill analysis: `lobe.py` (the BAT_IN_B lobe), `zoneneigh.py` (fill neighbours), `isl_all.py` → `isl_*.json`,
  `viaall.py` → `via_*.json`, `viaconn2.py`, `batf.py`.
- Gaps: `geo_export.py` → `geo_*.json`; `newgap.py` (THR env), `neigh.py`, `pairnet.py`, `couple.py`, `netarea.py`,
  `gainu4.py`.
- GND returns: `gexport.py` / `gpath.py` → `gdist.json`.
- Reference: `cr.sh` → `cr_*.txt`. DC: `dc.sh` / `dcjobs.txt` / `rundc.sh` → `dc_out.txt`.
- Fab: `gerb/` (zip contents) and `gfresh/` (re-export).
- Gate and tests: `gate.txt`, `tests.txt`, `status_before.txt` / `status_after_tests.txt`.
- Datasheet: TI SLVSFC9C text in `scratchpad/p6reg/ds/tps25947.txt` (§8.3.1 p. 60–61, §8.4.1 p. 61).
