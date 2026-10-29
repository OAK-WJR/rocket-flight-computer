# R7 pass 6: board-wide regression and electrical integrity (fix pass 5)

Read-only review, 2026-10-18. Dimension: every copper change of fix pass 5 (agent F6, `m3_design/r7_polish.py` /
`r7_post.py`), judged against the fix-pass-4 board that pass 5 reviewed and, where useful, against R6. Focus areas:
- ground returns and the critical-reference sampling;
- power feeds and the DC solve;
- the IPC-2152 record;
- the actuator and pyro safety rules and the arming break;
- the schematic and netlist (unchanged except documentation fields);
- the fab package and its binding to the board.

| Item | Value |
|---|---|
| Final board | `m3_design/assembly_review/m3.kicad_pcb`, SHA-256 `1ffc2585cbbb2a49623a5010b2792500849f06989cf43e48fb3e56068cddf9df`. This matches `fix5_F6_handoff.md`, M3_R7, R7_VALIDATION, STATUS and the fab manifest (`inputs_sha256/cad/m3.kicad_pcb`). I checked it before and after the gate and the test runs: unchanged |
| Pass-5 board ("base" below) | SHA-256 `c6fe595cafb91b088ac0b2c812f409f9ca5b86ac45a651102e168b0a5d83c7c7` (F6's start copy `scratchpad/fx5/base.kicad_pcb`, SHA re-checked) |
| R6 board | `git show 3b215ba:m3_design/assembly_review/m3.kicad_pcb` (SHA-256 `184a87e8…`), compared moved +18 mm in y |
| Schematic | `m3.kicad_sch` SHA-256 `47057f7d…` and `schematic.net.xml` `963c6369…`, both dated 2026-10-16 01:31, unchanged since pass 5. One sheet changed: `telemetry.kicad_sch` (`c75fb738…` → `6615ba08…`, 2026-10-18 05:51). The diff against F6's pre-fix copy (`scratchpad/fx5/proj/telemetry.kicad_sch`) is two `(text …)` notes only (§4.8). `m3.kicad_dru` `1674d58b…`, unchanged |
| Gate (rerun here) | `tools/check.sh` exit 0: DRC 0, unconnected 0, parity 0, ERC 0; audit OK; silk 0; R7 contract OK; routing hygiene 0 failing, 33 allowlisted, 0 stale, 0 out-of-date no-GND reasons, 30 leftovers recorded (0 unrecorded, 0 stale), 0 out-of-date route figures, 0 removable exceptions; actuator contract OK; fit OK |
| Tests (rerun here, KiCad Python) | test_dc_solve 3 OK, test_route_check 41 OK, test_r7_check 34 OK, test_fab_validation 23 OK. `git status` was the same before and after |
| Tools | KiCad 10.0.6 `pcbnew` read-only scripts on SHA-checked scratch copies (`scratchpad/p6reg/`); `tools/critical_reference.py`; `tools/dc_solve.py`; `kicad-cli pcb export gerbers` (scratch); pass-5 reviewers' `dump.py`, `geo_export.py`, `neigh.py`, `couple.py`, `isl_all.py`, `viaconn.py`, `gexport.py` / `gpath.py` (read-only copies); new `detail.py`, `newgap.py`, `groups.py`, `ra.py`, `pairmin.py`, `batf.py`, `probe_bat.py`, `overbat.py`, `vianeigh.py` |
| Fills | Saved fills throughout (the build scripts fill natively) |

## 1. Summary

**No Critical and no Major findings.** Fix pass 5 did what `fix5_F6_handoff.md` says. I found no electrical
regression that affects function or safety, and every pass-5 finding in this dimension is closed.

What holds:
- **Netlist, parts, rules:** unchanged.
  - All 819 pads match the base board in net, position, size, layer and zone connection.
  - Pad-connectivity groups are identical on all 191 nets, and KiCad reports 0 unconnected.
  - The schematic change is two text notes on sheet 15. The netlist is unchanged and `m3.kicad_dru` is unchanged.
- **Copper changed on 24 nets** (§4.1), every one named in the handoff:
  - tracks 1,809 → 1,777 (95 removed, 63 added);
  - vias 694 → 706 (GND −4 / +22: 18 new and 4 moved; signal −6: CAM_5V_SENSE −2, CAM_TX_WIRE −1, LED_RED −1, BAT_IN −2);
  - In1 now carries no signal track;
  - rule areas 21 → 23 trims, renumbered (§4.1).
- **Pyro and actuator safety:**
  - No track, via, pad or fill of PYRO1_BUS, PYRO1_IGN, PYRO1_OUT, PYRO1_GATE(_N), ARM1_SENSE(_MID), PYRO1_CONT_MID or ACT_FET_S changed.
  - PYRO1_CONT's F.Cu redraw has no pyro, SPI1 or RAW_ACT copper within 3 mm.
  - The arming break is intact, DRC passes every pyro rule, and `check_actuators` is OK.
  - ACT_GATE (one B.Cu corner at Q121.4) and RAW_ACT (a 0.2 mm sense-branch tail inside its own pour) changed, with no electrical effect (§4.6).
- **Critical reference:**
  - Against the base: 0 samples lost (R6 method and extended).
  - Against R6: 603 lost, 882 candidate-new. F6's +21 QSPI_CLK samples reproduce (an edge 0.01 mm over the RXEN via's In1 antipad).
- **GND returns:**
  - Every new GND via is joined to the GND fill on F.Cu, In1 and B.Cu.
  - Of the 173 SMD GND pads, one return got longer by more than 0.1 mm: R102.2, a 10 kΩ pull-down, 2.31 → 3.14 mm.
  - The four pieces in P5-REGRESSION-02 now hold 2 vias each.
  - Radio B.Cu over In2 BAT_IN fell from 24.26 to 12.18 mm. The band end is gone; the U1 end stays as deviation C5.
- **DC (0.1 mm grid; the base and final boards were solved here):**
  - RAW_ACT 3.95 → 3.95 mΩ; BAT_IN J1 → Q120 4.55 → 4.58 mΩ; ACT_FET_S 1.36 mΩ; J1 → U9.5 15.14 → 15.18 mΩ; USB_LIMITED 72.37 → 72.32 mΩ.
  - 3V3_RADIO, VLOGIC and CAM_5V (L3 → J9) are unchanged. The 3V3 rows equal F6's (solved on the final board only).
  - All of these match F6. The D3 / D1 redraws move only local branch resistances (CAM_5V → R78 15.05 → 13.06; ACT_GATE R120 → Q121.4 11.86 → 12.96 mΩ, a µA gate net).
  - One unrecorded change: P6-REGRESSION-01.
- **IPC-2152 record (P5-DOCS-02):**
  - Computed on the final board.
  - The Brooks & Adam arithmetic reproduces: RAW_ACT neck 2.18 mm → 55 °C; BAT_IN In2 neck 3.71 mm → 31 °C.
  - The necks lie away from fix pass 5's copper.
- **Fab package:**
  - Bound to `1ffc2585…`; all 173 inputs and 5 outputs match the manifest.
  - The PTH drill file holds exactly the board's 706 vias.
  - A fresh `kicad-cli` export of F.Cu, In1, In2 and B.Cu from the final board equals the packaged Gerbers, except for the header date lines.
  - BOM and CPL are byte-identical to the pre-fix copies.

Three Minor items:

| ID | Severity | One line |
|---|---|---|
| P6-REGRESSION-01 | Minor | `band_end` removed the two BAT_IN vias of the BAT_IN_F pour. That pour holds the 2 × 22 µF input capacitors C89 and C95 (TPS25947 input, TI §8.3.1), and it now joins BAT_IN only through C95.1's 0.2 mm × 2.1 mm track and a 0.030 mm² touch on via (9.2, 36.05). C89.1 → U9.5 rose from 6.91 to 10.35 mΩ (+50 %) and C95.1 → U9.5 from 6.57 to 7.37 mΩ. The records say only "J1 → U9 +0.3 %". Electrically small (Inference), but it is a one-via dependency, not recorded, and a legal-looking via spot exists |
| P6-REGRESSION-02 | Minor | `jogs5` straightened SERVO4_MCU (x 15.505) and CAM_FAULT_N (x 15.19) into side-by-side In2 runs at a 0.165 mm edge gap over 22.92 mm. Their coupled length at ≤ 0.2 mm went from 6.28 to 29.54 mm. The records list only the 0.162–0.166 mm gap, not the length. Benign: a 10 kΩ-pulled-up fault flag and a servo PWM (Inference) |
| P6-REGRESSION-03 | Minor | M3_R7's "fix pass 5's copper" adjacency list (every edge gap under 0.2 mm) misses two new ones. GND via (35.85, 53.275) is 0.177 mm from NRST's via (35.80, 53.95) on all four layers and 0.188 mm from NRST's B.Cu diagonal. CAM_FAULT_N's In2 run at y 103.938 is 0.162 mm from GND vias (24.55, 104.47) and (25.45, 104.47) (base ≥ 0.2 mm). Both are fail-safe or benign |

## 2. Pass-5 findings in this dimension: closure check

| Pass-5 ID | Disposition in R7_VALIDATION | Verified on the final board |
|---|---|---|
| P5-REGRESSION-01 (NRST "about 1.8 mm" misplaced) | Fixed (records) | **Closed.** M3_R7 l.441 and l.696 and deviation C10 now state the x 36.3 In2 run: 10.35 mm with no B.Cu GND fill above it, 3V3A's B.Cu track over 6.4–7.2 mm of it, no PYRO1_CONT above. NRST copper is not in the fix-pass-5 diff, and the extended critical reference against the base loses 0 samples |
| P5-REGRESSION-02 (four single-via GND pieces) | Fixed (`gnd_pieces`) | **Closed.** (1) F.Cu by J2: now 8.085 mm² (41.11–45.07, 70.29–76.11; PYRO1_CONT's x 40.88 run reshaped it), vias (44.75, 75.38) and (41.375, 70.625). (2) B.Cu east of U1: 15.197 mm², (35.75, 50.35) and (35.85, 53.275). (3) B.Cu by U4: 14.282 mm², (31.0, 80.15) and (27.4, 76.4). (4) F.Cu by CAM_UART_OE: 2.705 mm², (35.17, 57.92) and (34.05, 57.025). Each new via is joined on F.Cu, In1 and B.Cu (0.232 / 0.206–0.232 / 0.232 mm² ring overlap). Single-via GND pieces on F.Cu and B.Cu: 40 → 35 (`isl_all.py`), as C14 states |
| P5-REGRESSION-03 (close neighbours unrecorded) | Recorded; no nudge | **Properly dispositioned.** (a)–(d) are in M3_R7 "Close adjacencies kept" (l.508–515) and deviation C15 with the fail-safe reasoning. F6 measured that the GND via (28.55, 87.21) has no spot ≥ 0.25 mm from R129.1 and R178.1 within 1.45 mm of PYRO1_CONT's via, and it is unchanged. The list of fix-pass-5 copper is incomplete: P6-REGRESSION-03 |
| P5-REGRESSION-04 (PYRO1_CONT locations) | Fixed (records) | **Closed.** M3_R7 l.426: "From R168.1, B.Cu east of U1 … F.Cu north …", with the shielded PYRO1_OUT crossing recorded. The new S / SE / S drawing has the same end points and length: (35.78, 65.25) → (40.88, 70.35) → (40.88, 74.75), 11.612 mm against 11.613 mm |

Related items from other dimensions that touch this focus:
- **P5-ROUTING_GEOMETRY-03 (ARM1_SENSE GND vias).** Closed. GND vias (13.95, 93.75) and (13.95, 97.15), 0.5 / 0.3 mm:
  - 0.721 mm from the layer changes, 0.171 mm edge gap to ARM1_SENSE's vias;
  - 0.30 mm from the In2 BAT_IN fill (its zone clearance);
  - joined to GND on F.Cu, In1 and B.Cu.
  - BAT_IN J1 → Q120 4.55 → 4.58 mΩ, reproduced here on both boards.
- **P5-ROUTING_QUALITY-01 (band end).** Closed: the In2 GND strip covers x 6.9–9.9, y 25.0–31.3, and radio B.Cu over In2 BAT_IN fell from 24.26 to 12.18 mm. Side effect: P6-REGRESSION-01.
- **P5-DOCS-02 (IPC-2152).** Closed (records); checked in §4.5.

## 3. Findings

| ID | Severity | Requirement | Finding | Evidence (final-board coordinates, mm) | Fix |
|---|---|---|---|---|---|
| P6-REGRESSION-01 | Minor | AGENTS.md §3 (records state what was verified; power-path sizing); TI TPS25947 data sheet SLVSFC9C §8.3.1 (p. 60–61: CIN "to absorb the energy and dampen the transients", Eq. 24) and §8.4.1 (p. 63: protection capacitors "physically close to the device … routed with short traces to reduce inductance") | `band_end` deleted BAT_IN vias (7.6, 26.6) and (8.8, 26.6). Those were the BAT_IN_F pour's own stitches into In2 BAT_IN. BAT_IN_F (F.Cu, 37.40 mm², x 4.4–9.0, y 25.7–36.9) carries C89.1 and C95.1, the two 22 µF / 25 V input capacitors (C12891) at U9 (TPS259470) IN. The pour is now a via-less piece; the only other one on the board is ACT_FET_S_B. It joins the rest of BAT_IN only at its north end: through C95.1's 0.2 mm F.Cu track (9.2, 36.05) → (7.1, 36.05), 2.1 mm, which lies inside the pour, and a 0.030 mm² sliver where the fill touches via (9.2, 36.05). That via also carries D8's (SMBJ12CA) 0.2 mm B.Cu feed. C89 sits 8 mm farther south. The band-end docstring and R7_VALIDATION P3-ROUTING_QUALITY-02 say C89 and C95 "reach BAT_IN through the F.Cu pour and via (9.2, 36.05)". That is true, but the records quote only J1 → U9.5 (+0.3 %), not the capacitors' own path. Inference: the electrical effect is small. C88 (100 nF, the data sheet's ≥ 0.1 µF decoupler) is beside U9.5 and unchanged; 3.4 mΩ added in series with a 22 µF X5R adds damping; the battery-lead inductance (hundreds of nH) dwarfs a few nH. JLC's netlist test screens an open in the single joint | `batf.py` (fill ∩ copper, F.Cu): base: track 0.395 mm², via (9.2, 36.05) 0.030, via (8.8, 26.6) 0.249, via (7.6, 26.6) 0.280 mm². Final: the track and the 0.030 mm² via sliver only. `isl_all.py`: BAT_IN_F nvias 2 → 0. `dc_solve.py`, 0.1 mm, base → final: **C89:1 → U9:5 6.91 → 10.35 mΩ**; C95:1 → U9:5 6.57 → 7.37 mΩ; J1:1 → C89:1 16.27 → 19.75 mΩ; J1:1 → U9:5 15.14 → 15.18 mΩ; D8:1 → U9:5 12.78 → 12.79 mΩ (D8's own feed unchanged). Netlist: BAT_IN = C80, C88, C89, C95, C96, D8, J1.1, Q120.5–9, R167, R80, R82, TP80, U9.5. `probe_bat.py` (coarse probe, 0.2 mm grid: a 0.6 mm disc inside both the BAT_IN_F and In2 BAT_IN fills, with no other-net copper within 0.45 mm on F.Cu, B.Cu or In2 and 0.85 mm hole pitch) finds 10 candidate spots, e.g. (8.4, 32.0), (8.6, 32.2), (7.6, 36.2). Not checked against `r7_hygiene` GndFit/ViaCheck: Inference | Add one BAT_IN via (0.6 / 0.3 mm) in BAT_IN_F north of the strip, e.g. near (8.4, 32.0), after a `ViaCheck` legality check, so the capacitors keep a direct stitch into In2 BAT_IN. Otherwise record in M3_R7 "DC solve" and the P5-ROUTING_QUALITY-01 row: BAT_IN_F has no via of its own, and C89 → U9.5 is 6.91 → 10.35 mΩ |
| P6-REGRESSION-02 | Minor | AGENTS.md §3 / REQUIREMENTS M2 (records state what was verified; review of new copper); pass-5 coupling table (§4.6 of `pass5_regression.md`) | `jogs5` drew SERVO4_MCU straight down In2 at x 15.505 (y 67.15 → 101.13) and CAM_FAULT_N straight down at x 15.19 (y 78.21 → 101.30). The two 0.15 mm tracks now run side by side at a 0.165 mm edge gap for 22.92 mm. On the base, the facing runs were 0.47 mm apart (x 15.22 / 15.84) or more (x 14.64 / 15.48). With the diagonal and the y 103.6 / 103.9 pair, the coupled length at ≤ 0.2 mm went from 6.28 to 29.54 mm. M3_R7 l.516 and C15 list the "0.162–0.166" gap but not the 23 mm length or any coupling estimate. Inference: benign. CAM_FAULT_N is the camera eFuse fault flag: U7.6 → R77 1 kΩ → U1.85 (PD4), pulled up by R76 10 kΩ. A 3.3 V servo edge coupled through about 0.5–1 pF into roughly 10–15 pF of victim gives a glitch of about 0.1–0.3 V. That is far from the STM32 input threshold, and SERVO4 is a 50–333 Hz PWM | `pairlen` (same layer, parallel, edge gap ≤ 0.2 mm), base: 3.06 @ 0.194, 2.29 @ 0.182, 0.80 @ 0.162, 0.13 @ 0.191 (6.28 mm). Final: **22.92 @ 0.165**, 3.54 @ 0.194, 2.29 @ 0.161, 0.80 @ 0.162 (29.54 mm). Tracks: SERVO4_MCU In2 (15.505, 67.150)–(15.505, 101.127); CAM_FAULT_N In2 (15.190, 78.209)–(15.190, 101.298). Neighbours that block a wider gap: CAM_PWR_EN via (14.65, 92.95) 0.165 mm west of CAM_FAULT_N; ARM1_SENSE In2 x 16.18 (y 70.8–89.3) 0.50 mm east of SERVO4_MCU. Netlist: R76 10k 3V3–CAM_FAULT_N; R77 1k CAM_FAULT_N–CAM_FLT_RAW (U7.6); R157 10k SERVO4_MCU–GND; R153 1k to SERVO4_OUT; D121.6 | Record the run (22.9 mm at 0.165 mm, with the coupling estimate) in C15 / M3_R7 "Close adjacencies kept". Moving SERVO4_MCU east trades this coupling for coupling to ARM1_SENSE, and moving CAM_FAULT_N west is blocked by the CAM_PWR_EN via, so recording it is the proportionate fix. At a respin, give the two lanes ≥ 0.3 mm |
| P6-REGRESSION-03 | Minor | AGENTS.md §3 (records complete); M3_R7 "Close adjacencies kept" claims to list every fix-pass-5 edge gap under 0.2 mm | Two new sub-0.2 mm adjacencies of fix-pass-5 copper are missing from M3_R7 l.516–523 and C15. (a) GND via (35.85, 53.275), 0.5 mm, added by `gnd_pieces`, is 0.177 mm from NRST's 0.5 mm via (35.80, 53.95) on all four layers and 0.188 mm from NRST's B.Cu diagonal (33.45, 51.60)–(35.80, 53.95). The list gives only its 0.176 mm to 3V3A. (b) CAM_FAULT_N's new In2 run (17.83 → 30.90, y 103.938) passes 0.162 mm from GND vias (24.55, 104.47) and (25.45, 104.47). The base run at y 103.778 kept > 0.2 mm. Failure modes: an NRST–GND short holds the MCU in reset, so the board is dead at bring-up, the pyro gates are defined off (AGENTS §2.4) and the radio is held in reset; this is not unsafe. A CAM_FAULT_N–GND short reads "camera fault". Both vias are tented and plugged (ORDERING §3), and JLC's electrical test screens shorts (Inference) | `newgap.py` / `pairmin.py` (edge gaps, geometry export of saved copper). NRST–GND: base none < 0.2 mm; final 0.177 (via–via, F / In1 / In2 / B), 0.188 (B.Cu diagonal). CAM_FAULT_N–GND (non-pour): base none < 0.2 mm; final 0.162 to both vias. Also new at exactly 0.200 mm, outside the "< 0.2" list: GND via (27.4, 76.4) to RAW_ACT's 0.5 mm F.Cu feed (29.0, 75.7)–(24.3, 75.7) (RAW_ACT tracks already run 0.15 mm from GND pours board-wide) | Add (a) and (b) to the fix-pass-5 adjacency list in M3_R7 and C15 with their failure modes |

## 4. Measurements

### 4.1 What changed (base → final, exact track and via geometry; `dump.py` + `detail.py`)

Tracks 1,809 → 1,777 (95 removed, 63 added). Vias 694 → 706 (13 removed, 25 added). Zones 52 → 54 (two more pour
trims). Pads: no change in net, position, size, layer or zone connection on any of 819 pads.

| Net | Tracks −/+ | Vias −/+ | Change (handoff stage) |
|---|---|---|---|
| GND | 6 / 4 | 4 / 22 | 2 ARM vias, 12 forward-edge vias, 4 `gnd_pieces` vias; stitching via (43.7, 43.5) → (42.2, 43.25); 3 jack-leg vias 20 µm aft (11.4 / 30.09 / 32.99, 3.6 → 3.58); C94.2 B.Cu run redrawn (`tidy5` D2) |
| CAM_RX_WIRE, CAM_TX_WIRE | 16 / 8 | 4 / 3 | `jogs5`: RX one In2 run at x 44.251; TX off In1, straight F.Cu to one via (45.141, 43.875) |
| CAM_FAULT_N, SERVO4_MCU | 15 / 9 | 0 | `jogs5` straight runs (P6-REGRESSION-02) |
| CAM_5V_SENSE | 7 / 2 | 2 / 0 | F.Cu hop removed; In2 run inside a 3V3_In2 void (3V3_In2 −0.115 mm², the trim beside SERVO4_MCU) |
| RADIO_BUSY / MISO_MCU / MOSI, QSPI_CLK, RADIO_RXEN | 17 / 16 | 0 | `band5`, `qspi5` |
| PYRO1_CONT | 3 / 2 | 0 | `pyro1_cont` S / SE / S, same end points |
| USB_LIMITED, VLOGIC, CAM_5V, 3V3_RADIO | 13 / 9 | 0 | `tidy5` D3, D4, D10, D11; widths kept (0.4 / 0.25, 0.5, 0.3, 0.4 mm) |
| ACT_GATE, RAW_ACT | 4 / 2 | 0 | `tidy5` D1, D7 (§4.6) |
| BAT_IN | 0 / 0 | 2 / 0 | `band_end` (P6-REGRESSION-01) |
| CAM_EN, LOGIC_ILIM, LOGIC_SOURCE_ST, PULLPIN_EXT, LED_RED | 14 / 11 | 1 / 0 | `jogs5` debris redraws; LED_RED's hop on F.Cu |

- **Zones:**
  - R7_GND_In2_strip outline: (9.6, 25.0)…(6.9, 25.9) → (9.9, 25.0), (9.9, 31.3), (6.9, 31.3).
  - Pour trims 21 → 23 (`ra.py`, by outline): new F.Cu (24.04–24.41, 35.95–40.1), between RXEN and QSPI_IO2; new In2 (14.995–15.2, 66.96–70.2); TRIM_6 reshaped along QSPI_CLK's new step. The rest are renumbered and unchanged.
- **Fills:**
  - GND_B +12.10 mm²; GND_F −2.19 (43 pieces); GND_In1 +7.30; R7_GND_In2_strip +12.53.
  - R6_BAT_IN_In2 770.76 → 760.27 mm² (one piece, now from y 31.61); 3V3_In2 −0.115 (5 pieces).
  - Every pyro, RAW_ACT, ACT_FET_S, 3V3A, CAM_5V and BAT_IN F.Cu / B.Cu fill keeps the same area (to 0.001 mm²) and piece count. F6's XOR of the CH1 pyro copper is 0.00000 mm².
- **In1 signal copper:** none (CAM_TX_WIRE's three R6 segments are gone).

### 4.2 GND returns and pour pieces

- **New GND vias** (`viaconn.py`, ring ∩ GND fill):
  - all 18 new and 4 moved vias are joined on F.Cu, In1 and B.Cu: 0.232 / 0.206–0.232 / 0.232 mm² for 0.5 mm vias, 0.324 mm² for 0.6 mm vias;
  - the three jack-leg vias are joined on In2 GND too.
- **SMD GND pad returns** (`gexport.py` / `gpath.py`, 0.05 mm geodesic over F.Cu / B.Cu GND copper to a GND via or plated GND hole; 173 pads):
  - Changed by more than 0.1 mm: C23.2 2.35 → 1.64, R180.2 (ARM1_SENSE divider foot) 3.37 → 2.00, R102.2 2.31 → 3.14 mm.
  - R102 is the 10 kΩ CAM_UART_OE pull-down: the stitching via moved from (43.7, 43.5) to (42.2, 43.25) for CAM_TX_WIRE. Immaterial.
- **Pour pieces** (`isl_all.py`):
  - 96 pieces on both boards.
  - Via-less pieces: ACT_FET_S_B (inherited) and, new, BAT_IN_F (P6-REGRESSION-01). Every GND piece holds a via.
  - GND F/B single-via pieces 40 → 35.
  - Fix pass 5 split the F.Cu piece (22.34–32.53, 26.4–45.08; 52.7 mm², 10 vias) at the new RXEN / QSPI_IO2 trim into 36.6 mm² (6 vias) and 12.95 mm² (4 vias).
- **Band end:** radio and GNSS B.Cu over In2 BAT_IN 24.26 → 12.18 mm; over In2 GND 377.71 → 392.48 mm (`overbat.py`, 0.02 mm samples).

### 4.3 Critical-net reference (`tools/critical_reference.py`)

| Comparison | Lost | Candidate-new |
|---|---:|---:|
| Base → final, R6 method | **0** (69,916 referenced) | **0** |
| Base → final, extended | **0** (166,465 referenced) | **0** |
| R6 (+18 mm) → final, R6 method | 603 (QSPI_IO0 F 410, SPI1_MOSI F 79, QSPI_IO3 F 59 / B 2, QSPI_NCS B 38, QSPI_IO1 B 15) | 882 (= pass 5's 861 + 21 QSPI_CLK F.Cu at (23.31, 39.35–39.55)) |
| R6 (+18 mm) → final, extended | 2,312 | 4,325 |

- The 21 QSPI_CLK samples are the outer copper edge of the 0.2 mm clock at x 23.21 (edge 23.31), which grazes the In1 antipad of RXEN's via (23.8, 39.45) over 0.2 mm. They count against R6 only: the via and its antipad were already on the base. This is recorded (C2). Negligible at the firmware's 8 MHz QSPI clock (Inference).
- QSPI_CLK – RADIO_RXEN F.Cu coupling improved: 4.38 mm at 0.25 mm → 4.54 mm at 0.415 mm.

### 4.4 DC solves (`tools/dc_solve.py`, board stack-up 35 / 30 / 30 / 35 µm, 0.1 mm grid; both boards solved here)

| Path | Base | Final | F6 / M3_R7 |
|---|---:|---:|---:|
| RAW_ACT Q121:5–9 → J122:2,5,8,11 (7.7 A) | 3.95 | **3.95** | 3.95 |
| RAW_ACT Q121:5–9 → J124:2 (pyro bus feed via the ARM plug) | 1.47 | **1.47** | — |
| RAW_ACT Q121:5–9 → R177:1 (sense branch; D7 tail) | 86.54 | **86.54** | — |
| BAT_IN J1:1 → Q120:5–9 (7.7 A) | 4.55 | **4.58** (35.2 mV, 0.271 W) | 4.58 |
| ACT_FET_S Q120:1–3 → Q121:1–3 (7.7 A) | — | **1.36** | 1.36 |
| BAT_IN J1:1 → U9:5 | 15.14 | **15.18** | 15.18 |
| BAT_IN C89:1 → U9:5 | 6.91 | **10.35** | not given |
| BAT_IN C95:1 → U9:5 | 6.57 | **7.37** | not given |
| BAT_IN J1:1 → C89:1 | 16.27 | **19.75** | not given |
| BAT_IN D8:1 → U9:5 (TVS feed, through the same via (9.2, 36.05)) | 12.78 | **12.79** | — |
| CAM_5V L3:2 → J9:1 | 27.79 | **27.79** | 27.79 |
| CAM_5V L3:2 → R78:1 (`tidy5` D3) | 15.05 | **13.06** | — |
| ACT_GATE R120:2 → Q121:4 (0.05 mm grid; `tidy5` D1; µA gate net) | 11.86 | **12.96** | — |
| 3V3 L1:2 → U1:75 / FB31:1 / U1:100 | — | **15.64 / 14.66 / 78.23** | 15.64 / 14.66 / 78.23 |
| USB_LIMITED U10:6 → U11:7 | 72.37 | **72.32** | 72.32 |
| VLOGIC C84:1 → U2:2,3 | 36.39 | **36.39** | 36.39 |
| 3V3_RADIO FB31:2 → C310:1 | 1.27 | **1.27** | 1.27 |

Values in mΩ.
- Fix pass 5 moved no 7.7 A path beyond the method's resolution, apart from the ARM vias' +0.7 % on BAT_IN, which is recorded.
- The only unrecorded change is C89 / C95 (P6-REGRESSION-01).

### 4.5 IPC-2152 record (P5-DOCS-02)

- M3_R7 "High-current copper: IPC-2152 estimate" (l.784–830) was computed on `1ffc2585…`, the board reviewed here.
- I recomputed its baseline figures from the stated fits, ΔT = K · I^a · W^b · Th^c (W, Th in mil):
  - RAW_ACT neck, 2.18 mm (85.8 mil) of 35 µm, external (215.3, 2.0, −1.15, −1.0) at 7.7 A: 55.4 °C. Median 5.24 mm: 20.2 °C.
  - BAT_IN In2 neck, 3.71 mm (146.1 mil) of 30 µm, internal (200, 1.9, −1.10, −1.52): 31.2 °C.
  - Both match the record (55 / 20 / 31 °C).
- Attribution: KiCad's `panel_track_width.cpp` (gitlab master) says it uses "the IPC-2152 based Brooks & Adam" calculation via `TRACK_WIDTH_CALCULATIONS`. The installed 10.0.6 help (§2.7) still says IPC-2221. I did not re-derive the constants from the Brooks & Adam paper.
- The necks lie away from fix pass 5's copper: RAW_ACT at (19.5–20.95, 84.3–85.8); BAT_IN beside J1 at (25.25–25.85, 108.6–115.5); ACT_FET_S between the FETs at y 100.1. ACT_FET_S's fill is unchanged.
- The ARM vias' antipads lie in the J1 → Q120 corridor at x 13.95: +0.03 mΩ, peak density unchanged (6.17 A/mm per F6).
- The record correctly calls these upper-bound estimates and leaves the rise limit to the owner (deviation C1).

### 4.6 Pyro block, arming break, actuator switch

- **Rules:**
  - `m3.kicad_dru` is unchanged (SHA equal to the manifest). DRC passes every pyro rule (A–H, A2), and `check_actuators` is OK.
  - Pyro-sentinel and arming pads are unchanged (pad table identical).
- **Arming break:** PYRO1_BUS = {J124.1, R132.1, R134.2}; RAW_ACT reaches J124.2 only. No PYRO1_BUS, PYRO1_IGN or PYRO1_OUT track, via or fill changed. RAW_ACT → J124.2 is 1.47 mΩ on both boards.
- **PYRO1_CONT** (`pyro1_cont`):
  - Same end points, 11.612 mm against 11.613 mm.
  - No PYRO1_*, ARM1_*, RAW_ACT, SPI1_* or IMU_CS copper within 3 mm of the redrawn F.Cu run (`segneigh.py`).
  - New GND via (41.375, 70.625) 0.170 mm away: a short reads "no continuity" (fail-safe; recorded).
- **ARM1_SENSE vias:**
  - Gaps: ARM1_SENSE's vias 0.171 mm (recorded; a short reads "disarmed"); In2 BAT_IN 0.30 mm; CAM_PWR_EN 0.513 mm.
  - No PYRO1_BUS, PYRO1_IGN or PYRO1_OUT copper within 0.6 mm (rule D satisfied by DRC).
- **ACT_GATE (D1):**
  - The diagonal (5.9, 102.4)–(7.08, 101.22) is replaced by (7.08, 98.86)–(7.08, 102.4), which ends on the existing (7.5, 102.4)–(5.9, 102.4) run into Q121.4.
  - Its only neighbour within 0.25 mm is the GND_B pour (0.15 mm); ACT_FET_S's fill is identical.
  - Rule H (pad pairs) is unaffected.
- **RAW_ACT (D7):**
  - The 0.2 mm tail of the R177 sense branch, (9.8, 79.37) → (7.6, 81.57), is a sub-segment of the old (9.8, 79.37) → (7.0, 82.17) → (5.3, 82.17) and ends inside R6_RAW_ACT_F.
  - Its 0.21 mm gap to the 3V3 track and via (7.9, 80.4) is inherited (same line).
  - R177 and J122 path resistances are unchanged.
- **New GND copper near RAW_ACT:** via (27.4, 76.4) is 0.200 mm from RAW_ACT's 0.5 mm F.Cu feed and 0.291 mm from C121.1. RAW_ACT tracks already run 0.15 mm from GND pours in 37 places on the base, so this is not new in kind.

### 4.7 Coupling and close copper of the new tracks

| Pair (same layer, edge gap ≤ 0.5 mm) | Base | Final |
|---|---|---|
| CAM_FAULT_N – SERVO4_MCU In2 | 20.11 mm (6.28 mm ≤ 0.2) | 33.24 mm (**29.54 mm ≤ 0.2**, 22.92 @ 0.165): P6-REGRESSION-02 |
| CAM_5V_SENSE – VLOGIC_SENSE In2 | 5.46 @ 0.204 | 9.58 @ 0.204 (two ADC sense lines, filtered; Inference: immaterial) |
| RADIO_MISO_MCU – RADIO_MOSI F.Cu | 25.20 (min 0.204) | 25.06 (min 0.168 at the moved fan-in steps; lanes keep 0.25) |
| RADIO_BUSY – RADIO_MISO_MCU F.Cu | 25.76 (min 0.204) | 25.34 (min 0.250) |
| QSPI_CLK – RADIO_RXEN F.Cu | 4.38 @ 0.25 | 4.54 @ 0.415 |
| QSPI_CLK – QSPI_IO3 F.Cu | 3.90 @ 0.45 | — |
| ARM1_SENSE – SERVO4_MCU In2 | 3.82 (others 0.527) | 22.32 (18.5 mm at 0.500, was 0.527: a 0.027 mm shift across the 0.5 mm threshold, not a real change) |

All new copper keeps ≥ 0.15 mm (`newgap.py`). The sub-0.2 mm pairs not in M3_R7's list are P6-REGRESSION-03.

### 4.8 Schematic and netlist

- `telemetry.kicad_sch` (sheet 15): the diff against F6's start copy is two `(text …)` notes, and `r7_sch.py` l.308–309 carries the same strings:
  - the Q32 antenna-bias limit text: "about 27-46 mA over -20..+85 C" → "about 37-48 mA at -20 C and 25-38 mA at +85 C (Inference, bench check)";
  - the RF-chain DNP note.
- No symbol, field, wire or label changed. ERC 0, parity 0, and `schematic.net.xml` is unchanged (2026-10-16).

### 4.9 Fab package

- `m3_fab_manifest.json`: against F6's pre-fix copy (`scratchpad/fx5/fab_before/`), only `cad/m3.kicad_pcb`, `cad/telemetry.kicad_sch` and the Gerber / PDF outputs changed. All 173 input and 5 output hashes match the current files.
- PTH drill: tool T1 Ø0.300 has 706 hits, exactly the board's via positions (0.002 mm match, none missing, none extra).
- Fresh `kicad-cli pcb export gerbers` of F.Cu, In1.Cu, In2.Cu and B.Cu from the final board equals the zip's copper Gerbers, except for the header date lines.
- `m3_bom_jlc.csv` and `m3_cpl_jlc.csv` are byte-identical to the pre-fix copies. `cost_check.json` and `stock_check.json` were re-fetched (live stock and price fields).

## 5. Checked and not raised

- **Forward-edge stitching vias:**
  - The 12 new 0.5 mm GND vias sit at y ≤ 117.225: copper 0.525 mm inside the edge (board rule 0.50 mm; ORDERING §3: "filled copper starts 0.50 mm inside").
  - Two lie inside the requested forward tab windows: (8.575, 117.225) in x 6–11, (39.775, 117.225) in x 35–40.
  - JLC's mouse-bite guidance asks 0.30–0.50 mm from the last hole to copper and 1.5 mm to components, solder pads and critical traces ([JLC, PCB mouse bites](https://jlcpcb.com/blog/pcb-mouse-bites)). A tented stitching via is none of these, and a cracked barrel there is electrically redundant.
  - Three vias lie within 3.8 mm of an M3 support: (4.275, 117.225) at 2.84 mm and (0.775, 112.925) at 3.55 mm from (4, 114.4); (39.775, 117.225) at 3.60 mm from (42, 114.4). The hardware is nylon (ORDERING §7 "Mounting hardware"), the vias are plugged (ORDERING §3), and the pours already reach 0.5–0.9 mm from the hole edges.
- **NPTH:** every new via keeps ≥ 0.27 mm of copper from the non-plated holes (`npth_ok`), and DRC hole clearance passes.
- **CAM_RX_WIRE / CAM_TX_WIRE:**
  - TX's single via (45.141, 43.875) and RX's via (43.75, 42.625) are 0.15 mm from the GND pours.
  - CAM_TX_WIRE is 0.191 mm from R101.1 (its own series resistor's other net, CAM_TX_BUFFER).
  - Camera UART at 115 kbit/s; In1 is now a solid GND plane there.
- **CAM_5V_SENSE** runs in a pre-existing 3V3_In2 void. 3V3_In2 changed only by the 0.115 mm² trim beside SERVO4_MCU and keeps 5 pieces.
- **The radio band moves:** RADIO_BUSY is 0.175 mm from GND via (20.0, 27.45) and RADIO_MOSI 0.175 mm from the MISO_MCU and SCK vias. Both are in the recorded "band lanes 0.168–0.176".
- **D9 jack-leg vias** moved 20 µm aft. They stay joined on all four layers (0.324 mm² each).
- **Renders and silkscreen:** outside this dimension (gate: silk 0).

## 6. Reproduction

Scratch directory `scratchpad/p6reg/` (`base.kicad_pcb`, `final.kicad_pcb`, `r6.kicad_pcb`, each SHA-checked; `base/` and
`final/` hold `m3.kicad_pcb` plus the project and rules copies for `dc_solve`):
- `dump.py` → `base.json` / `final.json`, `diff.py` and `detail.py`: the per-net diff (§4.1); `ra.py`: zone and rule-area outlines;
- `groups.py`: pad-connectivity groups (`grp_*.json`, identical);
- `geo_export.py` → `geo_*.json`; `newgap.py`: gaps of every new item; `pairmin.py` / `pairmin2.py`: pair minimums; `vianeigh.py`: neighbours of the new GND vias; `segneigh.py`: PYRO1_CONT;
- `couple.py` (all nets in `critlist.txt`) and an inline `pairlen` for the CAM_FAULT_N / SERVO4_MCU lengths;
- `isl_all.py` → `isl_*.json`: pour pieces; `viaconn.py`: GND via joins; `gexport.py` / `gpath.py` → `gdist.json`: GND pad returns;
- `batf.py`: BAT_IN_F joins; `probe_bat.py`: candidate BAT_IN via spots; `overbat.py`: radio B.Cu over In2 BAT_IN;
- `cr.sh` → `cr_*.txt`: critical reference; `dc.sh` / `dcjobs.txt` / `rundc.sh` → `dc_out.txt`: DC;
- `gerb/` (zip contents) and `gfresh/` (re-export): fab comparison; `gate.txt`, `tests.txt`: gate and tests;
- `ds/tps25947.txt`: TI SLVSFC9C text (§8.3.1, §8.4.1).
