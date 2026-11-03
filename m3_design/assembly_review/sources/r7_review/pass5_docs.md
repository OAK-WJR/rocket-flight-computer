# R7 review pass 5: requirements conformance, documents and fab package

Reviewer: independent, pass 5, dimension "requirements conformance, documents and fab package".

- **Board reviewed:** `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
  `c6fe595cafb91b088ac0b2c812f409f9ca5b86ac45a651102e168b0a5d83c7c7`, the fix-pass-4 board that
  `fix4_F5_handoff.md`, M3_R7, R7_VALIDATION and STATUS name. The SHA and `git status` were the same before and after
  this review.
- **Other inputs:**
  - schematic `47057f7d97c7d748…` and `m3.kicad_dru` `1674d58be79ae428…`, both unchanged since pass 4;
  - fab outputs as bound in `fab/m3_fab_manifest.json` (`6ee0415c…`): BOM `3a0c2f12…`, CPL `c68dc2cb…`, Gerber zip
    `11f9f1dc…`, assembly PDFs `3022219f…` / `0ad69955…`;
  - `fab/cost_check.json` (2026-10-18T08:29:23Z) and `fab/stock_check.json` (08:28:14Z).
- **Comparison:** the pass-4 board `636a6bdc…` as described in `pass4_*.md`, `pass4_verdicts.json` and
  `fix4_F5_handoff.md`; the pass-4 docs reviewer's Gerbers (`p4docs/gerb`) for the layers fix pass 4 did not touch.
- **Method:** read-only. Measurements on a scratch copy of `assembly_review/` (board, project, rules, sheets, `kilib`)
  with KiCad 10.0.6 pcbnew, kicad-cli and the repository tools; bytecode writing off. `jlc_orient.py --verify-cpl` and
  `export_fab.py --out` were run on scratch copies so that no repository file was rewritten. Scratch:
  `<scratchpad>/p5docs/`. The only repository file written is this report.

## 1. Summary

**The gate, the tests and the fab package reproduce on the final board.**
- `tools/check.sh` exits 0:
  - DRC 0, unconnected 0, parity 0, ERC 0; audit OK; silkscreen outside the outline 0; R7 contract OK;
  - routing hygiene "0 failing, 37 allowlisted, 0 stale allowlist entries, 0 out-of-date no-GND reasons, 34 leftovers
    recorded (0 unrecorded, 0 stale)"; actuator contract OK;
  - fit OK (J9 mated 0.03 mm, C84 0.11 mm, nearest bottom envelope C76 4.150 mm, nearest top hardware TP30.1
    5.008 mm).
- **Tests:** check_shell 2, dc_solve 3, fab_validation 23, fit_check 23, maze_clearances 10, procurement 15,
  r6_check 17, r7_check 34 and route_check 32 pass (159), and quality_audit passes 21 under both Pythons (180, as
  STATUS says).
- **Fab package:**
  - The manifest verifies (5 outputs, bound to `c6fe595c…`).
  - A fresh `kicad-cli` Gerber and drill export of the scratch copy matches all 14 zip members, apart from
    timestamps. The new GND via (22.85, 89.63) is in the PTH drill file.
  - `export_fab.py --out <scratch>` writes a BOM and CPL byte-identical to the bound ones (92 lines, 219 rows; DNP
    C303/C304/C305/C313/C314; no missing code or correction).
  - `--verify-cpl` (scratch copy): 92 top and 119 bottom rows rebuilt, worst 0.491 mm, 8 placement-only, no errors;
    the corrections file comes out byte-identical.
  - The job file carries the JLC041611-7628 stack: 0.035 / 0.203 / 0.030 / 1.03 / 0.030 / 0.203 / 0.035, ENIG.
- **Cost and stock:** `cost_check.json` gives $77.83 + 92 × $1.53 / 5 = $105.98 per board with 52 extended codes,
  bound to the current BOM and CPL. Stock: short U4 only, thin none (U30 159, U31 462, J30/J31 3,299). REQUIREMENTS
  M3, ORDERING §1, M3_R7 and STATUS all quote these figures.
- **DC:** `dc_solve.py`, now reading the stack-up, gives BAT_IN J1 → Q120 **4.55 mΩ** (35.0 mV, 0.269 W) and RAW_ACT
  **3.95 mΩ** at 0.1 mm on the final board, as M3_R7 records.

**Pass-4 findings in this dimension (section 2).** P4-DOCS-02, -03 and -05 are closed. P4-DOCS-04 is properly
dispositioned as an open Minor: deviation item D17, with seven designators, which I reproduce. **P4-DOCS-01 (Major) is
partly fixed and still open**, as R7_VALIDATION itself says.

**Findings in pass 5:** 1 Major, 3 Minor.

- **Major P5-DOCS-01 (carries P4-DOCS-01): REQUIREMENTS M2 is not met on the final board, and the deviation list put
  up for the owner's acceptance is not yet complete or like-for-like.** Owner acceptance of the list as written would
  therefore not close M2.
  - **No owner acceptance** is recorded.
  - **Part D's 18 items are neither removed nor reasoned.** They include AGENTS §3 rule instances that the gate cannot
    see: an acute wedge, a staircase, a stub, a critical layer change with no GND via, and an In1 detour in the GND
    plane.
  - **The list leaves out review-only residuals that M2 requires it to include:**
    - all 72 information-only `route_check` instances on non-critical nets, among them three that fix pass 4's own
      redraws introduced;
    - residuals that earlier reviews recorded as "kept" (RQ-09, RQ-11, RG-12, RG-14, the BAT_IN overlap at C96.1).
  - **The "measured reasons" for the non-critical leftovers come from a search that may not enter any power pour.**
    Yet the present routes of 21 of the 24 leftover nets run 1–26 mm inside another net's power-pour outline. Rows
    such as B8, B10 and B11 ("no path … the present route is the only one found") therefore overstate what was
    shown.
- **Minor P5-DOCS-02:** M2 and AGENTS §3 require IPC-2152 sizing of high-current copper. R7 has no such evidence at
  the ordered 30 µm inner copper: M3_R7 says it "was not re-derived", and the deviation list does not mention it.
- **Minor P5-DOCS-03:** pass-1 E11 (add U30/U31 to MARGIN_PRESCRIPTION's 85 °C list) was dropped from open-item
  tracking. MARGIN's 85 °C row still names the SAM-M10Q.
- **Minor P5-DOCS-04:** small record inaccuracies:
  - PYRO1_CONT's length basis;
  - NRST 47 mm, where the gate measures 46.11 mm;
  - the placeholder clearances, 0.30 / 0.34 mm recorded against 0.274 / 0.317 mm measured;
  - D16's "not examined by any review".

**R7 acceptance (REQUIREMENTS, last section):**
- Met: `check.sh` and its contracts; M3 ($105.98, 52 of 52, snapshot 08:29Z); the fab binding.
- Not met: no open Critical or Major (P5-DOCS-01, plus any Major from the other pass-5 dimensions); M1 stock (U4
  consignment, documented).

## 2. Closure of the pass-4 findings in this dimension

| Pass-4 ID | Sev. | R7_VALIDATION disposition | Pass-5 check on `c6fe595c…` | Verdict |
|---|---|---|---|---|
| P4-DOCS-01 | Major | Partly fixed; open until the owner decides (l.441) | Done:<ul><li>staircases 4 → 2 and no-GND vias 11 → 10 (route.json: staircase 2, critical_via_no_gnd 10, all allowlisted);</li><li>non-critical tiny jogs and short segments 14 → 2 (CAM_EN, CAM_FAULT_N, both recorded);</li><li>34 LEFTOVERS entries, gate-checked;</li><li>a consolidated list (R7_VALIDATION l.489–632).</li></ul>Not done: the owner's dated acceptance. New in this pass: the list is incomplete and its B-reasons are not like-for-like (section 4) | **Open**, carried as P5-DOCS-01 |
| P4-DOCS-02 | Minor | Fixed (l.442) | `dc_solve.py` reads the board stack-up. It printed F.Cu 35 µm at 0.0175 mm, In1/In2 30 µm at 0.2530 / 1.3130 mm and B.Cu 35 µm at 1.5485 mm, so the barrels are 0.236 / 1.060 / 0.236 mm. BAT_IN 4.55 mΩ and RAW_ACT 3.95 mΩ reproduce. `test_dc_solve` passes 3. "Equal to R6" is now called a same-model comparison (M3_R7 l.618–620, l.654) | Closed (the IPC-2152 part of the pass-4 note is new P5-DOCS-02) |
| P4-DOCS-03 | Minor | Fixed (records) (l.443) | M3_R7 l.387–393 gives F → B → In2 → B → F, In2 13.73 mm and the 2.58 mm B.Cu hop. Fix pass 4 did not touch SWDIO (route.json 53.72 mm, 4 vias) | Closed |
| P4-DOCS-04 | Minor | Not done (board change); listed for the next board pass (l.444), deviation D17 | Ink-polygon-to-courtyard test on every visible designator of the final board (`meas5.py`): exactly 7 sit nearer another part's courtyard than their own, all on the same side: D120 (0.472 / C121 0.225), R155 (0.579 / R151 0.560), R80 (0.786 / D8 0.521), R172 (0.962 / Y1 0.878), TP84 (0.416 / C84 0.376), R83 (0.362 / C84 0.000) and C301 (0.165 / U30 0.117). Nine more designators sit on the side opposite their part, all inside their own part's courtyard ("under the part", allowed). Hidden designators: 84, identical to M3_R7 l.718–721 | Properly dispositioned (open Minor) |
| P4-DOCS-05 | Minor | Fixed (records) (l.445) | M3_R7 l.799–800 says "account for most of"; no "1.84 mm" remains in any document | Closed |

Other open items in this dimension, unchanged and correctly recorded open (R7_VALIDATION "Open after fix pass 4",
STATUS):
- P3-DFM-06(c): the BOM comment "915MHZ ANT SMA" is still on BOM line 36;
- P3-ELECTRICAL-01/-02(a): the sheet-15 notes "27-46 mA" and "capacitive only" are still at `telemetry.kicad_sch`
  l.1674 / l.1681;
- U4 consignment; JLC's forward-rail confirmation; the stale renders `r7_top.png` / `r7_bottom.png`.

## 3. Findings

| ID | Sev. | Requirement | Finding | Evidence | Fix |
|---|---|---|---|---|---|
| P5-DOCS-01 | Major | REQUIREMENTS M2 (owner clean-routing criterion over the whole board, and its "Deviations awaiting the owner's acceptance" clause: *every* allowlist entry, recorded leftover and *review-only residual* listed with location, rule, measured reason and why it cannot reasonably be removed); AGENTS §3; REQUIREMENTS "R7 acceptance"; carries P4-DOCS-01 / P3-REQUIREMENTS-01 | **M2 is not met on the final board.** The list the documents name as the instrument for closing it, R7_VALIDATION "R7 deviations for owner acceptance", is incomplete, and part of its reasoning is not like-for-like. So the owner's acceptance of the list as written would not make M2 true. See section 4 for the full audit. (a) No owner acceptance. (b) Part D: 18 items with no measured reason. Several are AGENTS §3 rule instances, which no list entry can turn into "forced". (c) The list leaves out 72 information-only instances on non-critical nets, although M2 names "layer hops and pad-entry tidiness on every net" as review items. It also leaves out residuals that earlier passes recorded as "kept". (d) Part B's "why it cannot reasonably be removed" rests on a raster search that may not enter any power pour, while most present routes do enter one. | **(a)** R7_VALIDATION l.503 "Owner acceptance: none recorded"; REQUIREMENTS l.75 "until then M2, and so R7 acceptance, is not met. No acceptance is recorded"; STATUS l.17–20.<br>**(b)** Re-measured on the final board (pcbnew):<ul><li>**D1**: ACT_GATE B.Cu (7.5, 102.4)→(5.9, 102.4) and (7.08, 101.22)→(5.9, 102.4) meet at 45° at Q121.4 (scan.py `acute_at_padvia`).</li><li>**D2**: GND B.Cu (35.1, 28.4)→(35.7717, 28.4)→(36.1634, 28.0083)→(36.3833, 28.0083)→(37.3336, 27.058), segments 0.672 / 0.554 / 0.22 / 1.344 mm, a staircase through R103.2's T.</li><li>**D7**: RAW_ACT F.Cu (7.0, 82.17)→(5.3, 82.17) ends touching only its own pour (scan.py `end_in_zone_only`, 1.7 mm).</li><li>**D8**: PYRO1_GATE F.Cu → TP122 pad via (20.45, 92.4); nearest GND via 2.928 mm.</li><li>**D16**: CAM_TX_WIRE runs F.Cu → via (42.133, 43.8675) → In1 hump 3.67 mm in the GND plane → via (44.933, 43.9675) → B.Cu, so two vias and an In1 run for a single F→B change.</li></ul>R7_VALIDATION l.610: "None of these has a measured reason for staying".<br>**(c)** `route.json` (this pass's gate run) has 72 information-only instances on non-critical nets: `pad_end_offcentre` 29, `extra_bends` 22, `short_layer_hop` 12, `u_turn` 7, `width_change_junction` 1, `segment_inside_pad` 1. C1 (l.594) covers only critical nets (64 / 29 / 18 / 12 / 10 / 9 / 2, which match). Examples:<ul><li>introduced by fix pass 4's own redraws: SERVO3_MCU 0.41 mm off-centre into D121.4 (32.95, 83.96); LED_YEL_A's 0.55 mm segment inside LED2.1; CAM_UART_OE's 2.7 mm In2 hop (34.0, 60.7);</li><li>SERVO4_MCU U-turn over 70.2 mm (27.40, 99.14); LOGIC_SOURCE_ST layer hops 0.9 / 1.99 / 2.47 / 2.97 mm; CAM_ILIM end 0.955 mm off TP73.1.</li></ul>Residuals recorded "kept" in earlier passes but absent from A–D:<ul><li>RQ-11: the 0.212 mm QSPI_IO0 jog into via (15.4, 51.0)→(15.55, 50.85), present on the final board, on a critical SPI net; RXEN's 90° at (18.35, 44.75); the via-column and fan-pitch irregularities;</li><li>RQ-09: the NSS hop in the strip, B.Cu (23.2, 17.3)→(23.2, 15.67)→(23.6, 15.27), present;</li><li>RG-12 (0.155 mm corridor resistors); RG-14 (R307/C301 off-axis, TP30);</li><li>pass-4 RG §7: BAT_IN B.Cu 0.5 mm runs (6.0, 54.475)→(8.2, 54.475)→(9.3, 53.375) and (8.3, 54.525)→(9.2, 54.525), 0.05 mm apart, side by side in C96.1 (present).</li></ul>"Detours on nets with a pour" (an M2 review item) is reviewed only for U12/C100 (C7).<br>**(d)** Present copper inside another net's power-pour outline on the same layer (`inpour.py`; the fill is cleared round the track):<ul><li>21 of the 24 B-list nets: BAT_FAULT_N 25.0 mm (In2 3V3), LOGIC_SOURCE_ST 25.8, RAW_ACT_SENSE 24.7, SERVO4_MCU 24.5, CAM_5V_SENSE 24.1, SERVO4_OUT 20.4 (3V3A 12.9 + 3V3 7.5), VBUS_SENSE 19.6, BAT_SW_RETURN 19.5 mm F.Cu in the BAT_IN crossbar (BAT_IN fill on both sides at (23, 106.8) and (23, 107.85)) + 1.3, CAM_MCU_TX 15.5, LED_RED 12.7, LED_YEL 11.6, CAM_FAULT_N 10.5, SERVO2_MCU 10.3, CAM_PWR_EN 7.9, NRST 7.7, CAM_MCU_RX 7.6, BUZZ_OUT 5.9 (B.Cu BAT_IN), SERVO1_MCU 4.1, CAM_UART_OE 2.7, SWDIO 1.5, BAT_SW_SOURCE 1.0;</li><li>only CAM_EN, SERVO2_OUT and SWCLK have none;</li><li>the allowlisted ARM1_SENSE (26.9 mm) and QSPI_IO2 (13.3 mm) do the same.</li></ul>The B-list search "blocks every power pour" (l.498–501; F5 handoff §4: "a 'no path' means no route that keeps the pours whole, not that the present route is optimal"). Yet:<ul><li>B8, B10 and B11 say "no path … the present route is the only one found", and B12/B22/B28/B29/B33/B34 say "already the shortest/best found";</li><li>A19, A25 and B17 reject alternatives because they "cut the 3V3 plane".</li></ul> | <ol><li>Complete the list:<ul><li>add the 72 non-critical information-only instances (one C row, with the counts and the introduced ones named);</li><li>add the earlier "kept" residuals (RQ-09, RQ-11, RG-12, RG-14, the C96.1 overlap);</li><li>either reconcile scan.py's categories or state that they are out of scope.</li></ul></li><li>For each B row whose present route runs inside a power pour, state that length. Then either rerun the search under the rule the board itself follows (In2 signal runs allowed where they split no island), or reword "cannot reasonably be removed" to "no route found under the stricter rule".</li><li>Redraw the cheap part-D items, at least D1, D2, D7 and D16; measure D8 for a legal GND via spot. Or give each a measured reason.</li><li>Then put the owner's dated acceptance on record. Until then M2 and R7 acceptance stay unmet.</li></ol> |
| P5-DOCS-02 | Minor | REQUIREMENTS M2 / AGENTS §3 ("high-current copper sized per IPC-2152"); REQUIREMENTS F4 ("Size and independently solve the final copper") | **The IPC-2152 sizing of the 7.7 A copper is not shown for R7 at the ordered 30 µm inner copper, and the deviation list does not record it.** The DC solve covers the resistance only. M3_R7 says the IPC-2152 sizing "was not re-derived here, and the bench thermal-camera stall test (F4) is the check". Two facts make the gap visible:<ul><li>the BAT_IN J1 → Q120 path is single-layer at mid-path (100 % In2, 30 µm);</li><li>RAW_ACT has had no In2 pour since R6 (100 % F.Cu at mid-path), so MARGIN_PRESCRIPTION P1-9's "≥ 10 mm equivalent, mirrored and stitched" is not met either and is not recorded for R7.</li></ul> | This pass's `dc_solve` on the final board: BAT_IN "In2.Cu carries 100 % at mid-path; peak 6.17 A/mm at (10.45, 107.62)"; RAW_ACT "F.Cu carries 100 % … peak 5.75 A/mm at (19.15, 84.52); In2.Cu 0 %". RAW_ACT zones on the final board: F.Cu `R6_RAW_ACT_F` 241.7 mm² and `RAW_ACT_F` 109.2 mm², B.Cu `RAW_ACT_B` 47.5 mm², and no In2 zone (the same on R6 `3b215ba`). M3_R7 l.660–663. MARGIN_PRESCRIPTION l.181 (P1-9). R7_VALIDATION l.489–632 has no IPC-2152 row. The peak values are grid-dependent local necks, not conductor widths (the records' caveat). | Record an IPC-2152 estimate for the BAT_IN In2 path and the RAW_ACT F.Cu ring at 30 / 35 µm: the narrowest cross-section from the solver's current map, the 7.7 A stall duty and the plane-credit assumption, labelled Inference where needed. Or add a deviation row: "IPC-2152 not shown; F4 bench stall test is the check; P1-9 mirroring not met since R6". |
| P5-DOCS-03 | Minor | Document consistency (MARGIN_PRESCRIPTION, R7_VALIDATION open items); AGENTS §2.5 | **Pass-1 E11 has dropped out of the open-item tracking.** E11 asks to add U30 and U31 to MARGIN_PRESCRIPTION's 85 °C list. R7_VALIDATION l.56–58 lists it as still open after step C, but neither "Open after fix pass 4" (l.634–672) nor STATUS's open items carry it. MARGIN's "85 °C temperature wall (9 part classes)" row still names the SAM-M10Q, which R7 does not carry, and omits the MAX-F10S and the E22. | MARGIN_PRESCRIPTION l.57. MAX-F10S data sheet UBXDOC-963802114-12732 R03, Table 13: "Topr Operating temperature −40 … +85 °C". EBYTE E22-900MM22S user manual §2.1/§2.2: operating and working temperature −40 … 85 °C. BOM lines 91–92 (U30, U31). | Add U30 and U31 to the MARGIN 85 °C row, or mark it as the rev-G baseline with an R7 note, as R14 (R7) does. Carry E11 in R7_VALIDATION's open list until it is done. |
| P5-DOCS-04 | Minor | Document accuracy (R7_VALIDATION, M3_R7, ORDERING) | Small record inaccuracies:<ol type="a"><li>**PYRO1_CONT's length uses mixed bases.** A29 gives "6 vias, 47.53 mm", the rerouted chain, where the other A rows quote the gate's net copper; the gate measures 53.33 mm for the net. The P3-REQUIREMENTS-01 row still reads "47.6 / 4 … 6 vias since fix pass 4".</li><li>**NRST** is recorded as "47 mm / 4 vias" (B24, M3_R7 l.421); the gate measures 46.11 mm.</li><li>**The JLC placeholder clearances** are recorded as 0.30 mm to the via and 0.34 mm to the pad opening; ink polygon to via ring measures 0.274 mm and to R157.2 0.317 mm (still clear).</li><li>**D16** says CAM_TX_WIRE was "not examined by any review yet", but `pass4_routing_geometry.md` §7 noted it.</li></ol> | (a) route.json PYRO1_CONT `len_mm` 53.33, `vias` 6, `pads` 5; R7_VALIDATION l.537, l.337.<br>(b) route.json NRST `len_mm` 46.11.<br>(c) B.SilkS "JLCJLCJLCJLC" at (23.65, 103.15), ink (18.624, 102.530)–(28.724, 103.680); via RAW_PROTECTED (18.05, 102.87), Ø0.6, so the ring edge is at x 18.35; R157.2 at (26.1, 101.93), 0.566 × 0.54 mm, mask margin 0; R7_VALIDATION l.333, M3_R7 l.712–714, ORDERING l.60.<br>(d) R7_VALIDATION l.630; pass4_routing_geometry.md l.391. | Quote one basis: net copper from `route_check`, with the rerouted chain named as such. Use 46.1 mm for NRST. Restate the placeholder clearances, or name the measurement method. Reword D16. |

## 4. Audit of "R7 deviations for owner acceptance" (R7_VALIDATION l.489–632)

**Part A (37 entries)** matches `route_check.ALLOWLIST` entry for entry. The gate run allows exactly these 37
instances:
- 2 staircases, 4 tiny jogs (critical) and 2 short segments;
- 10 `critical_via_no_gnd`, at 1.649 / 1.649 / 1.709 / 2.11 / 2.23 / 2.596 / 3.178 / 3.569 / 5.112 / 7.885 mm, as
  listed;
- 9 detours and 10 extra_vias, whose lengths and via counts match `route.json` (e.g. VLOGIC 66.87 mm / 5,
  RAW_PROTECTED 143.53 mm / 7, VBUS 42.49 mm / 6).

`nognd_audit` reports 0 out-of-date reasons. Rows A17/A18 are honest that the ARM1_SENSE spots are excluded by design
(the 7.7 A corridor), so the audit cannot fail them by construction; the trade-off is the owner's.

**Part B (34 entries)** matches `LEFTOVERS`: 13 detour, 19 extra_vias and 2 tiny_jog. The lengths and via counts match
`route.json`, except NRST (P5-DOCS-04(b)). The search results are F5's (`fx4/det/r3…r5`). I did not re-run them. The
problem is the basis (P5-DOCS-01(d)):
- the search blocks every power pour on every layer, while 21 of the 24 present routes run inside one;
- so a "no path" or "already the shortest found" result shows only that no route exists under a stricter rule than
  the board follows;
- the B8/B10/B11 wording ("the present route is the only one found") is not what was shown, because the search could
  not have found those routes either;
- whether any present In2 run actually splits a 3V3 island was not measured here: the BAT_IN F.Cu crossbar crossed by
  BAT_SW_RETURN, for example, stays one piece of 229 mm² (Inference for the others).

**Part C (13 entries)** is accurate where checked:
- C1's critical-net counts match `route.json`;
- C12, the J2.1 via: 3V3 (44.035, 77.92) is unchanged;
- C8's distances are taken from the records.

What is missing is listed under P5-DOCS-01(c).

**Part D (18 entries)** is accurate where checked (D1, D2, D7, D8 and D16 re-measured, section 3). These are not
deviations with a reason. They are known items that have not been removed, and four of them are AGENTS §3 rule types.

**Completeness against M2's own definition:**

| M2 element | In the list? |
|---|---|
| Allowlist entries | Yes (A) |
| Recorded non-critical leftovers | Yes (B), but the reasons are not like-for-like |
| Review-only residuals, critical nets | Yes (C1, from the pass-4 judgement on the fix-pass-3 board) |
| Review-only residuals, non-critical nets: layer hops, pad entries, U-turns, extra bends (72 instances) | **No** |
| Residuals recorded as kept in passes 2–4 (RQ-09, RQ-11, RG-12, RG-14, BAT_IN overlap in C96.1) | **No** |
| Detours on poured nets (an M2 review item) | Only U12/C100 (C7); not swept |
| IPC-2152 sizing (AGENTS §3) | **No** (P5-DOCS-02) |
| The pass-2 scanner's categories (958 instances, 595 critical; e.g. `pad_entry_diagonal` 173, `dogleg` 148, `chain_detour` 62, `right_angle_corner` 55, `width_change_free` 17) | Not reconciled; the list says nothing about them |

## 5. Requirement walk (final board `c6fe595c…`)

Verdicts:
- **Pass:** shown in the CAD, schematic, gate or fab files.
- **Fail:** not met.
- **NV:** needs the bench, flight or firmware.
- **Partial:** the CAD part passes and the rest is open.

### Sources and owner decisions

| Item | Verdict | Evidence |
|---|---|---|
| One primary pyro channel; isolated Blue Jay | Pass | `check_r7`, `check_actuators` OK |
| 4-servo limit | Pass | J122 3 × 4; `check_actuators` OK |
| On-board MAX-F10S and E22-900MM22S, JLC-assembled | Pass | BOM lines 91–92 (C30005563, C5333985, SMT); CPL top |
| Uplink never arms or fires | Pass (CAD) | R7 contract OK (pad-level RF-part net check, `rf_part_coverage`); ARM is the physical J124 link |

### Functional

| ID | Verdict | Evidence / remark |
|---|---|---|
| F1–F3, F5 | Pass (parts) | Unchanged |
| F4 | Partial | `check_actuators` OK. DC solve on the final board with the board's stack-up reproduced (4.55 / 3.95 mΩ). IPC-2152 sizing not shown (P5-DOCS-02). Stall test is bench |
| F6, F7, F9 | Pass (CAD) | Unchanged circuits |
| F8 | Pass (CAD) | DRC 0 under the nine pyro rules; legends; bench gates NV |
| F10 | Pass (CAD), bench NV | R7 contract OK; C302.2 now on relief (`thermal_policy`), D30.2/D31.2 solid by recorded decision, ORDERING §5 inspection line present (l.137) |

### Physical

| ID | Verdict | Evidence |
|---|---|---|
| P1 | Pass | 46 × 118 mm (`fit_check`) |
| P2 | Pass (CAD) | 5 supports; nearest bottom envelope C76 4.150 mm; TP30.1 5.008 mm; vibration estimate carried over from the pass-2 board (Inference, recorded) |
| P3 | Pass (record/procedure) | Unchanged |

### Manufacturing and cost

| ID | Verdict | Evidence |
|---|---|---|
| M1 | Pass, except U4 stock (allowed exception, open) | Job file JLC041611-7628, ENIG; CPL 219 rows (96 top, 123 bottom); test pads 2 top (TP30, TP84) and 22 bottom, as ORDERING §4 says; CPL check reproduced |
| M2, JLC rules / via-in-pad / paste / silk | Pass, with Minors P4-DOCS-04 (D17) and P5-DOCS-04(c) | DRC 0. `vias_in_smd_pads` in the R7 contract. Silk: no visible text under 1.0 mm or stroke under 0.15 mm (`silkw.py`, 0 found). F/B paste and mask Gerbers are identical to pass 4's (fix pass 4 changed no pad), so pass 4's paste parse stands |
| M2, clean routing | **Fail** | P5-DOCS-01 |
| M3 | Pass | $105.98 per board, 52 / 52, bound to the current BOM/CPL (08:29Z) |

### R7 acceptance

| Condition | Status |
|---|---|
| `check.sh` zero; actuators, fit and `route_check` OK | Met (reproduced) |
| Independent review with no open Critical or Major | **Not met** (P5-DOCS-01, plus any Major of the other pass-5 dimensions) |
| M3 on a ≤ 24 h snapshot | Met at review time (08:29Z on 2026-10-18); rerun before ordering |
| M1 stock, U4 by consignment | Open (documented) |
| Fab outputs regenerated and bound | Met (manifest OK; Gerbers, BOM and CPL re-exported and compared) |

## 6. Document consistency (beyond the findings)

These agree with one another and with the board:
- **Board SHA** `c6fe595c…` in STATUS l.12, M3_R7 l.4 / l.281, R7_VALIDATION l.22, AGENTS §1 and the manifest.
- **Gate line:** STATUS l.52–53, M3_R7 l.736–737 and R7_VALIDATION l.453–454 match this run's gate output.
- **Test counts:** 159 + 21 = 180 (STATUS l.65–67, M3_R7 l.816–819, R7_VALIDATION l.458–461).
- **Cost and stock:**
  - $105.98, parts $77.83, $77.83 with minimum purchases, 52 extended; short U4 only;
  - U30 159, U31 462, C530661 3,299;
  - stated in REQUIREMENTS M3, ORDERING §1 l.28/l.32, M3_R7 l.793–808, R7_VALIDATION l.472–475 and STATUS l.95.
  - The U4 consignment arithmetic ($109.4–114.5 per board) checks.
- **Counts on the board:**
  - track count 1,809 and vias 694 (M3_R7 l.433);
  - In1 signal copper: only CAM_TX_WIRE's three segments, 3.67 mm;
  - pour trims F.Cu 8 / B.Cu 13 (M3_R7 l.333);
  - hidden designators 84 (list identical);
  - placeholder position (23.65, 103.15) in ORDERING §3 l.60.
- **Requirement and tool wording:** REQUIREMENTS M2's "What the gate enforces" against `route_check.py` (categories,
  scopes, thresholds, allowlist, stale rule, `nognd_audit`, `LEFTOVERS` check); AGENTS §3 against M2.
- **Unchanged rows:** MARGIN R14 (R7) and FMEA I-11/V-19 (unchanged since pass 4, still accurate); ORDERING §4/§5 (the
  D30/D31/C302 seating inspection now exists).
- **Pass tallies:**
  - pass 1: 16 Major;
  - pass 2: 26 Major / 51 Minor;
  - pass 3: 3 / 36;
  - pass 4: 2 / 16.
- **Stale figures:** "42 allowlisted", "83 hidden", "3.91 mΩ" and "$105.96" appear only in contexts marked
  historical.

Not raised again (already recorded open):
- P3-RF-02 is closed. The P3-ELECTRICAL notes, P3-DFM-06(c), P4-RF-01, P4-RF-02 and P4-ROUTING_GEOMETRY-02 stay open.
- `procurement_catalog.json` LS120 reflow; `test_r5_repair`.
- The stale renders; the forward rail; U4 consignment.

## 7. Measurements and reproductions

All in `<scratchpad>/p5docs/`:
- **Gate:** `tools/check.sh`, exit 0 (`gate.log`). Reports copied to `gate/`: `route.json`, `r7.json`, `fit.json`,
  `drc.json`, `erc.json`, `audit.json`.
- **Tests:** every suite under KiCad Python with `PYTHONDONTWRITEBYTECODE=1` (`tests.txt`, plus a rerun from `tools/`
  for the suites that import siblings).
- **Fab:**
  - `fab_manifest.verify_manifest` → 5;
  - fresh kicad-cli Gerber and drill export (`gerb_new/`) against the zip (`gerb_old/`), timestamps ignored: 14 of 14
    identical;
  - `export_fab.py <scratch board> --out fabnew/`: BOM and CPL byte-identical;
  - `jlc_orient.py --verify-cpl` in `orient/`;
  - pass-4 Gerber comparison for paste, mask and silk.
- **DC:** `dc_batin.txt`, `dc_rawact.txt` (`tools/dc_solve.py`, 0.1 mm grid).
- **Board scripts:**
  - `dump.py`: track and via dumps;
  - `near.py` / `pads.py`: pads and vias near a point;
  - `inpour.py` / `zonecross.py` / `fillat.py`: present copper inside other nets' pour outlines, and fills beside it;
  - `meas5.py` (pass-4 method) and `meas5b.py`: designator-to-courtyard distances;
  - `silk.py` / `allvis.py`: hidden-designator list;
  - `silkw.py`: silkscreen sizes;
  - `jlc2.py`: placeholder clearances.
- **Scans:** F5's `fx4/an/d2_scan.json` (pass-2 `scan.py` on the final board) for the scanner's categories.
- **Datasheets:** MAX-F10S DS R03 Table 13 and the E22-900MM22S manual §2.1/§2.2, read from the copies in the session
  scratchpad (`dl_max/`, `dl_e22/e22b.pdf`).

## 8. Sources

- Repository documents, by line:
  - REQUIREMENTS (F4 l.54, M2 l.75, M3 l.76, R7 acceptance l.105), ORDERING, M3_R7, R7_VALIDATION, STATUS, AGENTS,
    MARGIN_PRESCRIPTION (l.57, l.181, R14 (R7)), FMEA_REDUNDANCY;
  - `fix4_F5_handoff.md`, `fix4_F5_progress.md`, `pass4_*.md`, `pass4_verdicts.json`, `pass2_routing_quality.md`
    (RQ-09, RQ-11), `pass2_routing_geometry.md` (RG-12, RG-14), `pass4_routing_geometry.md` §7;
  - `tools/route_check.py` (ALLOWLIST l.176, LEFTOVERS l.268, `gated()` l.1647, `leftover_check` l.1672),
    `tools/dc_solve.py`, `tools/fab_manifest.py`, `tools/export_fab.py`.
- u-blox MAX-F10S data sheet UBXDOC-963802114-12732 R03, Table 13 (Topr −40 … +85 °C):
  https://content.u-blox.com/sites/default/files/documents/MAX-F10S_DataSheet_UBXDOC-963802114-12732.pdf
- EBYTE E22-900MM22S user manual §2.1 "Limit parameters" and §2.2 "Working parameters" (−40 … 85 °C):
  https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2212192008_Chengdu-Ebyte-Elec-Tech-E22-900MM22S_C5333985.pdf
- JLC parts data as captured in `fab/cost_check.json` and `fab/stock_check.json` (source "jlcpcb.com
  selectSmtComponentList", 2026-10-18T08:28–08:29Z).

## 9. Inferences (not checked against a primary source)

- **P5-DOCS-01(d):** "inside a power-pour outline" is measured. Whether a given present In2 run splits a 3V3 or 3V3A
  island, or merely slots it, was not measured, except for the F.Cu BAT_IN crossbar (one piece). Whether a
  like-for-like search would find shorter routes is not shown either way.
- **P5-DOCS-01(b):** "cheap" for D1, D2, D7 and D16 is judged from their geometry (a redundant 45° branch, a staircase
  inside its own pour, a tail inside its own pour, two vias where one suffices). No candidate redraw was
  clearance-probed in this pass.
- **P5-DOCS-02:** the significance of the missing IPC-2152 estimate is not quantified. The quoted peaks are local and
  grid-dependent, and the 7.7 A load is a four-servo stall, not a continuous load.
- **The scanner's categories** (`pad_entry_diagonal`, `dogleg`, …) may be benign by M2's wording. They are listed as
  unreconciled, not as defects.
