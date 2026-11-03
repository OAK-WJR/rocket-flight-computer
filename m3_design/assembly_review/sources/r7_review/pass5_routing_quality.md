# R7 review pass 5: routing quality of critical and new nets

Reviewer scope: electrical routing quality of the critical and new nets against the owner's clean-routing criterion
(REQUIREMENTS M2, AGENTS.md §3) and reference continuity. Nets: PYRO1_CONT and the other pyro nets, SPI1 (IMU),
SWD near the crystal, the radio/GNSS interface, the camera UART and enable, QSPI, USB and the power feeds. For each I
measured detour ratio, vias and layer hops, bus tidiness, reference-plane continuity and split crossings, and asked
whether a cleaner route fits.

Board reviewed: `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
`c6fe595cafb91b088ac0b2c812f409f9ca5b86ac45a651102e168b0a5d83c7c7` (fix pass 4 final, the hash bound in
`docs/R7_VALIDATION.md`). The hash was the same before and after this review. References: the pass-4 board
`636a6bdc…7650`, R6 `3b215ba` (moved +18 mm in y).

The review was read-only. Boards were copied to a scratch directory and never saved in the repository; the only
repository file written is this report. One scratch experiment (§6, P5-ROUTING_QUALITY-01) saved a modified copy in
the scratch folder only.

## 1. Method

1. **Gate.** `tools/check.sh` on the repository board: exit 0. DRC 0, unconnected 0, parity 0, ERC 0; audit OK;
   silk 0; R7 contract OK; `routing hygiene: 0 failing, 37 allowlisted, 0 stale allowlist entries, 0 out-of-date
   no-GND reasons, 34 leftovers recorded (0 unrecorded, 0 stale): OK`; actuator contract OK; fit OK.
   `tools/test_route_check.py`: 32 tests OK. `tools/route_check.py --report` and `--routes` on the final and the
   pass-4 board.
2. **Copper diff.** Every track and via of the pass-4 board against the final board, per net (`diffp3.py`). Changed
   nets: PYRO1_CONT, NRST, CAM_UART_OE, RADIO_NRST / RADIO_NSS / RADIO_SCK (band), GND (4 vias added, 2 removed) and
   the 10 "debris" nets (LED_YEL_A, SERVO3_MCU, CAM_5V_SENSE, SERVO4_OUT, SERVO2_MCU, CAM_EN, LOGIC_ILIM, I2C1_SCL,
   SERVO4_MCU, CAM_RX_WIRE). Every other net's copper is identical, including SPI1, QSPI, USB, HSE, SWD, the RF lines,
   the radio/GNSS corridor and every power net. Tracks 1,836 → 1,809, vias 694 → 694, 52 zones.
3. **Per-net metrics** (`route_check --routes`, octilinear MST ratio, vias, layer lengths).
4. **Reference planes.** The pass-3/4 `refscan.py` (0.05 mm samples, reference F→In1, In1→F, In2→B, B→In2) with the
   pattern extended to IMU_INT1, I2C1_*, SERVO*_MCU and the camera wires, on both boards, compared event by event.
   `tools/critical_reference.py` R6 → final (R6 method) and pass-4 → final (`--extended`).
5. **Islands.** In2 3V3 fill islands under U1/U4 on both boards.
6. **Neighbours.** Every other-net item within 0.45 mm of the rerouted nets' copper on the same layer (`nbr.py`,
   `SHAPE::Collide` bisection), adjacent-layer overlaps (`broad.py`), exact net-to-net gaps (`mind.py`).
7. **Candidate routes.** `probe2.py`: minimum edge gap of candidate copper to every other-net track, via and pad with
   the applicable rule (0.15 mm; J2 0.508 mm; bare TP 1.0 mm; pyro rules A/C for sense nets; hole-to-hole 0.25 mm)
   and the power-zone outlines it would cross. F5's router outputs (`fx4/rt/pc7–pc9`) were read, not re-run.
8. **GND-via spots.** The pass-4 geometry reviewer's independent probe (`probe.py`, board DRC rules, no margin,
   0.025 mm grid) on the final board, for every critical layer change without a GND via.
9. **Experiment.** In2 GND over the band end of the BAT_IN arm (P5-ROUTING_QUALITY-01): modified scratch copy, native
   `ZONE_FILLER` refill, `kicad-cli pcb drc --schematic-parity`, `route_check`, `check_r7`, `check_actuators`,
   `dc_solve`.
10. **Renders** (`render_pdf.py` + `pdftocairo`): the via cluster east of U1 (`img/hub_pdf.png`).

## 2. Pass-4 findings in this dimension: closure

| Pass 4 | Disposition in R7_VALIDATION | Checked on the final board | Verdict |
|---|---|---|---|
| P4-ROUTING_QUALITY-01 (Minor): PYRO1_CONT in the SPI1/servo bundle, In2 3V3 island split, 0.191 mm to a PYRO1_GATE_N via | Fixed (6-via plane-preserving route) | In2 3V3 island under U1/U4 one piece, 74.51 mm²; probe points (23.7, 67.1) and (24.4, 67.8) in the same island (pass-4 board: 41.93 + 22.69 mm²). PYRO1_CONT copper gaps: SPI1_SCK 2.750 mm, SPI1_MOSI 3.323, SPI1_MISO none within 5 mm, IMU_CS 1.895, PYRO1_GATE_N 1.079 (F.Cu, inherited divider pad C127.1 to the gate via), PYRO1_GATE 3.078, PYRO1_OUT 0.715 (rule C 0.3). Every layer change has a GND via within 1.5 mm: 1.112, 0.721, 1.014, 0.728, 0.764, 1.408 mm. PYRO1_CONT referenced length 50 % → 70 %. R6-method critical reference: 603 lost / 861 candidate-new (pass-4 board 864 / 1,122) | **Closed.** Residual tidiness and records in P5-ROUTING_QUALITY-02 |
| P4-ROUTING_QUALITY-02 (Minor): SWD side effects, SWDIO In2 length | Fixed (records); C8, C9 | M3_R7 "Rerouted in fix pass 3" gives SWCLK–Y1.3 1.10 mm, the measured constraints, SWDIO F → B → In2 → B → F with 13.73 mm on In2. The voids C9 quotes "not re-measured after fix pass 4" are unchanged on the final board: ARM1_SENSE In2 (16.6, 70.4)→(19.5, 67.4) 4.205 mm, CAM_PWR_EN 4.7 mm (x 17.35) and 5.265 mm | **Closed** (properly dispositioned; C9's figures now confirmed on the final board) |
| P4-ROUTING_QUALITY-03 (Minor): disposition texts | Fixed (records) | (a) R7_VALIDATION P3-RQ-02 row and C5 name the band-end option as "Inference, not attempted"; **M3_R7 l.445–447 still says "Moving them cuts U9's In2 BAT_IN arm; stitching would need a BAT_IN–GND capacitor"** without the band-end distinction. (b) Corridor trade-off stated in M3_R7 and R7_VALIDATION. (c) The `r7_polish.pyro1_cont` docstring ("every power pour on every layer kept whole") is true of the new route: its In2 runs lie where In2 has no pour (zone query at (35.78, 59–63), (41.63, 77), (30–33, 86–88.6)) | **(b), (c) closed; (a) partly**: the band-end option is in fact feasible (P5-ROUTING_QUALITY-01) |
| P4-REGRESSION-01 / -03 (overlap with this dimension) | Fixed / recorded | as row 1 / as row 2 | Closed |
| P4-ROUTING_GEOMETRY-01 (PYRO1_GATE_N GND via) | Fixed | GND via (22.85, 89.63) 0.6/0.3 mm, 1.309 mm from via (23.0, 88.33); `nognd_audit` 0; my independent no-margin probe (§5.3) | Closed |
| P4-DOCS-01 (Major; routing part (1)–(2)) | Partly fixed; owner decision | Staircases 4 → 2, critical no-GND 11 → 10, non-critical tiny jogs / short segments 14 → 2 by the tool's count; three of the twelve "removed" jogs are the same jogs lengthened past the tool's threshold (P5-ROUTING_QUALITY-04) | Owner acceptance remains the open item (records dimension) |

## 3. What fix pass 4 changed (copper diff, pass-4 board → final)

| Net | Removed | Added | Notes |
|---|---|---|---|
| PYRO1_CONT | 12 tracks, 41.80 mm, 4 vias | 14 tracks, 47.53 mm, 6 vias | B.Cu 7.09 / In2 14.09 / F.Cu 32.16 mm (net incl. local copper 53.33 mm); B → In2 (1.8 mm) → F → In2 (4.41 mm) → F → In2 (7.88 mm) → F into R129.2 |
| NRST (J2 branch) | 15 tracks (3.24 mm on In1), 4 vias | 10 tracks, 2 vias | net 54.33 → 46.11 mm, 6 → 4 vias, In1 0; B.Cu → In2 x 36.3 (10.35 mm) → one F.Cu diagonal to J2.3 |
| CAM_UART_OE | 20 tracks, 6 vias | 10 tracks, 4 vias | 44.11 → 30.68 mm (ratio 1.49 → 1.04); a 2.7 mm In2 hop under SWCLK's F.Cu diagonal |
| RADIO_NRST / NSS / SCK | band fan-in steps | redrawn | NRST's step inside its via; SCK's and NSS's later |
| GND | vias (29.28, 77.95), (23.68, 69.55) | vias (35.18, 61.05) 0.6, (40.93, 78.65) 0.6, (28.55, 87.21) 0.5, (22.85, 89.63) 0.6 | PYRO1_CONT returns and PYRO1_GATE_N; all four land where In2 has no pour |
| 10 debris nets | short pieces | redrawn | P5-ROUTING_QUALITY-04 |

## 4. Per-net metrics, final board

Changed (pass-4 board → final; `route_check --routes`): PYRO1_CONT 47.60 mm / 1.17× / 4 vias → 53.33 / 1.31 / 6;
NRST 54.33 / 1.57 / 6 → 46.11 / 1.33 / 4; CAM_UART_OE 44.11 / 1.49 / 6 → 30.68 / 1.04 / 4. Debris nets within
±0.6 mm.

Unchanged (identical copper to pass 4): SPI1_SCK 28.73 mm / 1.20 / 1 via, SPI1_MOSI 1.12, SPI1_MISO 1.04, IMU_CS
1.08; QSPI_CLK 1.00 / 0 vias, QSPI_IO0..3 1.16–1.25 (2–3 vias), QSPI_NCS 1.13; USB_DP / DM 30.57 / 30.86 mm (3 / 2
vias); HSE_IN 1.00, HSE_OUT 1.18; SWCLK 62.70 / 1.90 / 4, SWDIO 53.72 / 1.48 / 4; radio NSS 1.59, SCK 1.28, MOSI 1.28,
MISO_MCU 1.58, BUSY 1.57, DIO1 1.77, NRST 1.83, RXEN 1.21, TXEN 2.30; GNSS TXD_MCU 1.39, RXD_MCU 1.15, TP_MCU 1.47,
RESET_N 1.69; CAM_MCU_TX 2.67 / 5, CAM_MCU_RX 1.24 / 6, CAM_PWR_EN 2.52 / 8; 3V3_RADIO 1.02, 3V3_GNSS 1.14; VCAP1
4.89, VCAP2 4.22 (recorded); RF lines 1.00, no via.

Critical-net vias and nearest GND via (final): PYRO1_CONT as §2; PYRO1_GATE_N 0.750 / 1.309; ARM1_SENSE 0.776,
0.750, 7.885, 5.112 (the last two allowlisted, A17/A18); HSE_IN 0.900, HSE_OUT 1.204; USB_DP 0.802 / 1.250 / 0.806,
USB_DM 1.393 / 1.390; SPI1_SCK 0.781, SPI1_MOSI 0.849, SPI1_MISO 1.379, IMU_CS 1.204; the 8 allowlisted radio vias
1.65–3.57 mm (A9–A16).

## 5. Reference planes and split crossings

### 5.1 refscan, pass-4 board → final

| Net | Change |
|---|---|
| PYRO1_CONT | void 23.89 → 16.08 mm of 53.3 (50 % → 30 %); the B.Cu start (33.03, 52.9)→(35.78, 58.85), 7.2 mm, is over In2 with no pour (In1 GND 1.26 mm below); every In2 run has B.Cu GND above except 0.4–1.6 mm at B.Cu crossings |
| SPI1_SCK, SPI1_MISO | the 215 + 46 samples fix pass 3 took are back (R6 method) |
| NRST | void 26.63 → 25.55 mm; the new In2 run x 36.3 has no B.Cu fill above for its full 10.35 mm (In1 GND below for 9.85 mm); the old J2 branch had 13.4 mm of In2 in the same state |
| CAM_UART_OE | void 19.24 → 12.66 mm |
| PULLPIN | In2 x 35.17: B.Cu void above 0.60 → 2.35 mm (NRST's and PYRO1_CONT's B.Cu diagonals cross over it); a DC switch input, not in the critical classes |
| SERVO1_MCU, SERVO3_MCU, I2C1_SDA, IMU_INT1, ARM1_SENSE, PYRO1_GATE_N, QSPI_IO2 | ±0.3–2.4 mm of B.Cu GND above In2 runs (new B.Cu crossings; trim regeneration); none is a plane-net change |
| RADIO_*, GNSS_*, QSPI_*, SPI1_MOSI, IMU_CS, USB_D*, HSE_*, SWDIO | no change |

`critical_reference.py --extended`, pass-4 board → final: lost 986 (NRST In1 478 and In2 444, whose copper is gone;
SWCLK F.Cu 64 at (35.13–35.63, 58.37–58.74)), new 690 (NRST In2 626; the same 64 SWCLK samples). The SWCLK samples
are PYRO1_CONT's via (35.78, 58.85) antipad under SWCLK's F.Cu diagonal; against R6 they do not show (the record's
"the fix-pass-4 rise is all NRST" is an R6-based statement and holds as such).

### 5.2 Split crossings

- **In2 3V3 island under U1/U4:** one piece again (§2). No B.Cu critical net crosses a 3V3 split there.
- **Radio corridor (C5):** 7 lines cross In2 GND → In2 BAT_IN at each corridor end; measured on the final board:
  12.08 mm of radio B.Cu over BAT_IN at the band end (y < 35) and 12.18 mm at the U1 end. The band-end half is
  removable (P5-ROUTING_QUALITY-01).

### 5.3 GND vias at critical layer changes

My independent probe (`gndprobe.py`, the pass-4 reviewer's `probe.py`: board DRC rules with **no** margin,
0.025 mm grid, 0.5/0.3 and 0.6/0.3 mm GND vias, check_r7 and ViaCheck placement rules) on the final board
reports exactly the 10 allowlisted layer changes and no other: RADIO_RXEN (23.8, 39.45), RADIO_NRST (9.3, 50.0),
RADIO_BUSY ×2, RADIO_MOSI, RADIO_DIO1, RADIO_MISO_MCU and RADIO_MOSI_MCU have no DRC-legal spot within 1.5 mm even
without the project's +0.02 mm margin; both ARM1_SENSE vias have spots only inside the 7.7 A BAT_IN corridor
((13.85, 97.525) and (13.975, 93.75)), as A17/A18 state. So the `nognd_audit` result does not depend on its margin,
and the band redraw freed no spot. PYRO1_CONT and PYRO1_GATE_N are not in the list (all ≤ 1.5 mm).

## 6. Findings

No Critical, no Major. Five Minor.

| ID | Sev. | New in fix pass 4 | Finding |
|---|---|---|---|
| P5-ROUTING_QUALITY-01 | Minor | no (records) | The band-end half of the 14 radio split crossings (C5) is removable by a zone-outline edit; demonstrated with every gate clean. C5 and M3_R7 still present it as not removable / not attempted |
| P5-ROUTING_QUALITY-02 | Minor | yes | PYRO1_CONT's new route: an S/SE/S/SE F.Cu run where S/SE/S fits, and close approaches on the new copper (0.175–0.22 mm to CAM_UART_OE, SWCLK, NRST, 3V3A, PYRO1_CONT_MID) not in the records |
| P5-ROUTING_QUALITY-03 | Minor | yes | NRST's new J2 branch: the records' "about 1.8 mm under PYRO1_CONT / 3V3A B.Cu" is wrong (10.35 mm with no B.Cu fill above; 3V3A, not PYRO1_CONT, overlies it); its B.Cu branch is stacked on its own In2 branch for about 1.5 mm |
| P5-ROUTING_QUALITY-04 | Minor | yes | Three "debris" redraws (LOGIC_ILIM, I2C1_SCL, SERVO4_MCU) only lengthened a forced 45° step from below to just above route_check's 0.5 mm tiny-jog threshold; the records count them as removed |
| P5-ROUTING_QUALITY-05 | Minor | no (records) | The QSPI_CLK allowlist reason (A5) names the wrong obstacle: straight on, the clock would overlap QSPI_IO3's via, not pass LED_YEL's at 0.15 mm |

### P5-ROUTING_QUALITY-01 (Minor): the band-end split crossings can be removed

**Records.** R7_VALIDATION C5 (part C, "why it cannot reasonably be removed"): "at the band end a layout-only
pull-back of the BAT_IN arm to about y 34.5 appears possible (Inference, not attempted)". P3-ROUTING_QUALITY-02 row:
the same. M3_R7 l.445–447 ("Close adjacencies kept"): "Moving them cuts U9's In2 BAT_IN arm; stitching would need a
BAT_IN–GND capacitor (schematic change)" — the pass-4 correction did not reach this bullet.

**Geometry (final board).** In2 zones: `R6_BAT_IN_In2` (priority 6) arm x 7.2–9.9 from y 26.0; `R7_GND_In2_strip`
(priority 7) arm x 0.3–6.9 from y 25.9 to 53.1. The radio lines leave the corridor at x 3.2–6.2 and run east on
B.Cu at y 27.2–30.2 to the band vias (x 9.4 / 10.0), so each crosses GND → BAT_IN about 2.5–3.2 mm before its via.
North of U9 (U9.5 at (11.2, 40.85)) the arm serves C89.1 (5.9, 28.125) and C95.1 (7.1, 36.075) — both BAT_DAMP RC
dampers (22 µF in series with R166 to GND), not BAT_IN–GND decouplers — and the BAT_IN vias (7.6, 26.6), (8.8, 26.6).
No In2 track lies in x 6.9–9.9, y 25–31.3.

**Experiment** (scratch `p5rq/bandend/mod.py`, never in the repository): extend `R7_GND_In2_strip`'s outline over
x 6.9–9.9, y 25.0–31.3 (it out-prioritises BAT_IN there), delete the two BAT_IN vias at y 26.6, refill with
`ZONE_FILLER`.
- `kicad-cli pcb drc --severity-all --schematic-parity`: **0 violations, 0 unconnected, 0 parity** (C89.1 now reaches
  BAT_IN through the F.Cu BAT_IN pour and via (9.2, 36.05), as the pass-4 reviewer inferred).
- `route_check`: `0 failing, 37 allowlisted, 0 stale …, 34 leftovers recorded (0 unrecorded, 0 stale): OK`
  (no new pour sliver, finger or dangling via). `check_r7`: OK. `check_actuators`: OK.
- Radio B.Cu length over In2 BAT_IN (`bandspan.py`): band end **12.08 → 0 mm** (all 7 crossings gone: BUSY 1.64,
  DIO1 1.64, MISO_MCU 1.86, MOSI 1.65, NRST 1.85, NSS 1.60, SCK 1.84 mm); U1 end 12.18 mm, unchanged. refscan: RADIO_SCK
  and RADIO_MOSI become wholly GND- or void-referenced (BAT_IN 1.85 / 1.66 → 0 mm).
- DC (`tools/dc_solve.py`, the board's stack-up, 0.1 mm grid): BAT_IN J1:1 → U9:5 **15.14 mΩ on both** the final
  board and the experiment (100 % In2 at mid-path, same peak density); the removed copper carries no U9 current.

**Impact (inference).** Radio SPI is at most 10 MHz (E22, A13); a 1.6–1.9 mm excursion over a plane whose nearest
AC tie to GND is an RC damper is a small loop-inductance increase, not a functional risk. The point is that a recorded
deviation listed as "cannot reasonably be removed" has a cheap, gate-clean removal.

**Fix.** Apply the outline edit in the build (e.g. an `r7_polish` stage after `pour_trim`, or in `r7_pcb`'s zone
set), delete the two BAT_IN vias, rerun the gate; reduce C5 to the U1 end (7 crossings), and correct M3_R7 l.445–447.
If it is not applied, move C5's band-end half to part D ("not yet removed") with this measured option.

### P5-ROUTING_QUALITY-02 (Minor): PYRO1_CONT — one cheap tidy-up, and unrecorded close approaches

The new route closes P4-ROUTING_QUALITY-01 (§2). Two residuals on the new copper:

1. **Extra bends where a simpler drawing fits.** F.Cu (35.78, 60.65)→(35.78, 65.25)→(39.78, 69.25)→(39.78, 73.65)→
   (40.88, 74.75): S 4.6, SE 5.657, S 4.4, SE 1.556 mm (route_check `extra_bends`, information; new; R7_VALIDATION C1
   lists it for acceptance). The three-segment drawing with the same end points and the same length,
   (35.78, 65.25)→(40.88, 70.35)→(40.88, 74.75), clears every board rule (`probe2.py`: nearest NRST via 0.361 mm,
   NRST track 0.536, J2 NPTH 0.534 mm against 0.508, GND via 0.639; no power-zone outline crossed). The router's
   output was hand-tidied only at J2.
2. **Close approaches on the new copper, DRC-legal, not in M3_R7 / R7_VALIDATION** (which quote only the SPI1 and
   pyro gaps): via (35.78, 60.65) to CAM_UART_OE's F.Cu (34.55–38.0, 60.15) **0.175 mm**; via (35.78, 58.85) to SWCLK's
   F.Cu diagonal **0.191 mm**; F.Cu x 35.78 to NRST's via (36.3, 64.8) and via (35.78, 58.85) to NRST's In2 x 36.3
   **0.195 mm** each; via (28.40, 88.61) to R129.1 (PYRO1_CONT_MID) **0.193 mm**; via (35.78, 60.65) to 3V3A's B.Cu
   0.212 mm; R168.1 to SWCLK's B.Cu diagonal 0.220 mm; via (34.68, 84.75) to R75.1 (CAM_EN) 0.225 mm. PYRO1_CONT's
   B.Cu vertical x 35.78 (55.65–58.85) sits 0.03 mm off SWCLK's F.Cu vertical x 35.75 (54.65–58.15) on the opposite
   face, and its B.Cu diagonal runs 0.536 mm (edge) beside SWCLK's for 3.2 mm. Its via (35.78, 58.85) takes 64 SWCLK
   In1 reference samples (§5.1).
3. **Context, not a defect:** east of U1 the route joins SWCLK, NRST and CAM_UART_OE in a 4 × 7 mm cluster with seven
   signal vias and two side-by-side short In2 hops (PYRO1_CONT 1.8 mm at x 35.78, CAM_UART_OE 2.7 mm at x 34.0;
   `img/hub_pdf.png`). Each hop is forced given the others: a B.Cu continuation of PYRO1_CONT collides with R63.2
   (GND, B.Cu) and its F.Cu path is crossed by CAM_UART_OE's run at y 60.15 (`fitprobe.py`). No joint search of
   CAM_UART_OE and PYRO1_CONT was run by F5 or by me.

**Impact.** None functional: PYRO1_CONT is the divider output (≤ about 3.3 V; R168 4.7 kΩ at the ADC pin), and the
neighbours are idle SWD, an enable, a reset and a quiet analog rail. The finding is a cheap tidy-up on a pyro net and
incomplete disclosure.

**Fix.** Redraw the run as S/SE/S (above) in `r7_polish.PYRO1_CONT_ROUTE`; add the approaches in item 2 to M3_R7
"Close adjacencies kept" (or the PYRO1_CONT bullet) and to R7_VALIDATION's P4-REGRESSION-01 row.

### P5-ROUTING_QUALITY-03 (Minor): NRST's new J2 branch — record wrong, own-net stacking

**Evidence.** NRST J2 branch: B.Cu (30.8, 53.1)→(30.8, 52.3)→(31.5, 51.6)→(33.45, 51.6)→(35.8, 53.95), via, In2
(35.8, 53.95)→(36.3, 54.45)→(36.3, 64.8), via, F.Cu (36.3, 64.8)→(45.3, 73.8)→(45.3, 75.6)→(44.25, 76.65)→(43.85, 76.65).
- **Reference.** M3_R7 l.421–422 and "Return paths" (l.593–595): the new In2 run "has about 1.8 mm under PYRO1_CONT /
  3V3A B.Cu rather than GND (about 1.8 mm unreferenced)". Measured (B.Cu fill sampled every 0.05 mm along the run):
  **no B.Cu fill above any of the 10.35 mm** (In1 GND, 1.03 mm away across the core, below 9.85 mm of it). The B.Cu
  copper over it is 3V3A's track (36.40, 52.10)→(36.40, 60.86), 0.1 mm off-centre, broadside for about 6.4 mm; PYRO1_CONT
  is not above it (nearest: its In2 via (35.78, 58.85), 0.195 mm beside). The 1.8 mm is `critical_reference`'s
  "candidate-new vs R6" count (545 samples), i.e. the part that was referenced on R6, not the unreferenced length. Not a
  regression: the old J2 branch had 13.4 mm of In2 in the same state (pass-4 refscan).
- **Stacked own-net copper.** The new B.Cu branch leaves via (30.8, 53.1) north on x 30.8 for 0.8 mm directly over
  NRST's own In2 branch (30.8, 53.1)→(30.8, 52.2), then NE (30.8, 52.3)→(31.5, 51.6) parallel to the In2 diagonal
  (31.3, 51.7)→(30.8, 52.2) 0.07 mm off — about 1.5 mm of the net on top of itself on adjacent layers before the
  branches part (the geometry scan also flags this run as a chain detour, 7.06 mm for 5.35 octile, round
  PYRO1_CONT_MCU's via (31.4, 52.5), 0.191 mm away, and R168).

**Impact.** NRST has C24 at U1 and is slow; no functional effect. Record accuracy and a cosmetic duplicate.

**Fix.** Correct both M3_R7 sentences (10.35 mm with no B.Cu fill above, 3V3A's track over about 6.4 mm, no
PYRO1_CONT). Optionally start the B.Cu branch east of the via so it does not shadow the In2 branch.

### P5-ROUTING_QUALITY-04 (Minor): three "debris" jogs were lengthened past the tool's threshold, not removed

**Evidence** (pass-4 board → final; `route_check` tiny_jog = an A,B,A chain whose middle segment is < 0.5 mm or
offsets the line by < 0.25 mm, `tools/route_check.py` l.35, l.1567–1568):

| Net | Pass-4 step | Final step | Neighbour gaps (pass-4 → final, `mind.py`) |
|---|---|---|---|
| LOGIC_ILIM, B.Cu out of U11.10 | 0.283 mm diagonal, 0.2 mm offset | (29.45, 30.0)→(29.09, 30.36): 0.509 mm, 0.36 mm offset | LOGIC_SS 0.300 → 0.260 mm; LOGIC_SOURCE_ST 0.240 → 0.300 mm |
| I2C1_SCL, F.Cu out of U1.95 | 0.424 mm, 0.3 mm offset | (25.35, 62.25)→(25.71, 62.61): 0.509 mm, 0.36 mm | IMU_INT1 via 0.325 → 0.265 mm; BOOT0 0.191 → 0.200 mm |
| SERVO4_MCU, In2 | 0.391 mm, 0.276 mm offset | (15.4784, 90.85)→(15.8384, 91.21): 0.509 mm, 0.36 mm | — |

Each is still a single 45° step between two collinear runs, just 0.06–0.16 mm larger, so it now passes the 0.5 mm
middle-segment test by 9 µm. The steps are forced: for LOGIC_ILIM a jog-free drawing (29.40, 29.35)→(29.40, 31.0)→
(30.65, 32.25) clears LOGIC_SOURCE_ST's via by exactly 0.150 mm (`probe2.py`), below the project's +0.02 mm redraw
margin; I2C1_SCL's step is set by U1.95's pad and the BOOT0 / IMU_INT1 vias. The handoff and R7_VALIDATION (P4-DOCS-01
(2)) count all three among the "14 → 2" removed tiny jogs. RADIO_SCK's staircase became `extra_bends` the same way (its
first run 0.6 → 1.05 mm, past the 1 mm staircase threshold), though its shape (one west step, one east chamfer 9.85 mm
apart) was never a staircase in the plain sense.

**Impact.** Non-critical nets; cosmetic. The issue is that the owner's list ("no … tiny jogs") is judged by review
beyond the tool, and the records present threshold-tuned copper as removed.

**Fix.** Record LOGIC_ILIM, I2C1_SCL and SERVO4_MCU as forced jogs with their measured reasons (as CAM_EN and
CAM_FAULT_N are in `LEFTOVERS`) and correct the "14 → 2" count to "14 → 2 by the tool; 3 of the 12 lengthened past the
threshold". Optionally test jogs on offset only (< 0.4 mm, say) so the gate cannot be met by lengthening.

### P5-ROUTING_QUALITY-05 (Minor): the QSPI_CLK allowlist reason names the wrong obstacle

**Evidence.** A5 / `tools/route_check.py` l.181–185: "straight on at the pin column x 22.85 it passes the LED_YEL via
(22.35, 41.35, 0.5 mm) at 0.15 mm, the DRC minimum". QSPI_CLK is 0.2 mm wide; straight on at x 22.85 it would run
0.35 mm (centre) from QSPI_IO3's Ø0.6 mm via (22.5, 40.3): **edge gap −0.05 mm, an overlap** (`probe2.py`:
"VIOLATION QSPI_IO3 VIA gap 0.000"). The LED_YEL figure is right (0.15 mm) but is not the binding one. The second
clause (a non-tiny step comes within 0.196 mm of RADIO_RXEN at x 23.575) checks out.

**Impact.** None: the conclusion (the step is needed) is stronger than stated.

**Fix.** Name QSPI_IO3's via (22.5, 40.3) in the reason and in R7_VALIDATION A5.

## 7. What is clean

- **SPI1 / IMU:** copper identical to pass 4; PYRO1_CONT ≥ 2.75 mm away; the In2 3V3 reference under SPI1_SCK whole
  again; R6-method reference back to 603 / 861.
- **Pyro nets:** PYRO1_CONT ≥ 1.079 mm from PYRO1_GATE_N on every shared layer (asserted in the build), 0.715 mm from
  PYRO1_OUT (rule C 0.3), no RAW_ACT / PYRO1_BUS / PYRO1_IGN copper within 5 mm on a shared layer; every PYRO1_CONT
  layer change ≤ 1.408 mm from a GND via; PYRO1_GATE_N's layer change now 1.309 mm; its In2 runs under the pyro
  block sit where In2 has no pour, with In1 GND between them and the block's F.Cu power copper; its six vias are the
  search minimum with every power pour whole (A29, F5's `fx4/rt/pc7–pc9`; the first In2 hop is forced by R63.2 on B.Cu
  and CAM_UART_OE on F.Cu, measured).
- **SWD near the crystal:** unchanged; SWCLK–Y1.3 1.10 mm recorded with measured constraints (C8).
- **Radio / GNSS interface:** corridor copper unchanged; band fan-in now uniform 45° steps (NRST inside its via, SCK
  and NSS later; BUSY and MISO_MCU allowlisted); no reference event changed on any RADIO_* / GNSS_* net.
- **Camera UART:** CAM_UART_OE 44.1 → 30.7 mm and 6 → 4 vias (ratio 1.04); CAM_MCU_TX / RX unchanged (recorded B16–B18).
  D16 (CAM_TX_WIRE's three inherited In1 segments, "not examined"): like-for-like layer swaps collide — B.Cu with
  CAM_IO_3V3's track and a GND via, In2 with BAT_SW_SOURCE / BAT_SW_RETURN (`probe2.py`); the only F.Cu track over the
  In1 cut is CAM_RX_WIRE's diagonal (one crossing, a 115 kbaud camera line). So it is not removable by a simple layer
  change; leave in part D with this note.
- **QSPI, USB, HSE, power feeds, RF lines:** copper identical to pass 4, no reference event changed.
- **NRST:** off In1 (the GND plane is free of NRST copper), 6 → 4 vias.
- **New GND vias:** all four land where In2 has no pour and tie F/B/In1 GND; none adds a void under a critical net
  (refscan, critical_reference).

## 8. Scripts and outputs (scratch, not in the repository)

`<scratch>/p5rq/`:

- **Boards:** `r7.kicad_pcb` (`c6fe595c…`), `p4.kicad_pcb` (`636a6bdc…`), `r6.kicad_pcb`; dumps `r7.json`, `p3.json`
  (the pass-4 board), `r6.json`.
- **Gate and route_check:** `check.log`; `route_r7.json`, `route_r7.txt`, `routes_r7.txt`, `routes_p4.txt`;
  `scan_r7.json`, `scan_p4.json` (pass-2 geometry scan).
- **Reference:** `ref_r7.json`, `ref_p3.json`, `refcmp.py`, `refscan.py` (pattern extended); `cref_r6_r7.json`,
  `cref_p4_r7_ext.json`.
- **New scripts:** `nbr.py` (same-layer neighbours), `broad.py` (adjacent-layer overlaps), `zq.py` (zones at points),
  `probe2.py` (candidate copper against rules and power zones), `bandspan.py` (radio B.Cu over In2 BAT_IN); the pass-4
  `diffp3.py`, `islands.py`, `mind.py`, `fitprobe.py`, `render.py`; `render_pdf.py` (pass-2); `gndprobe.py` (pass-4
  geometry reviewer's `probe.py`), output `gndprobe.txt`.
- **Experiment:** `bandend/` (`mod.py`, the modified scratch board `m3.kicad_pcb`, `drc.json`, `route.json`,
  `r7.json`, `ref.json`); `dc_bandend.txt`.
- **Renders:** `img/hub_pdf.png` (via cluster east of U1), `img/pc_n.svg.png`, `img/pc_s.svg.png`.
