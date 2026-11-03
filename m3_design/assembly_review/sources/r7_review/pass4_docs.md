# R7 review pass 4: requirements conformance, documents, DFM and mechanical records

Reviewer: independent, pass 4, dimension "requirements conformance, documents, DFM and mechanical records".

- **Board reviewed:** `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
  `636a6bdc7234586a659741a3da921335a47197648c29cd9612c8374733847650`: the fix-pass-3 board that R7_VALIDATION,
  STATUS, M3_R7 and `fix3_F4_handoff.md` name. The SHA was the same before and after this review.
- **Other inputs:** schematic `47057f7d97c7d748…`, `m3.kicad_dru` `1674d58be79ae428…`, fab BOM `3a0c2f12…`, CPL
  `c68dc2cb…`, Gerber zip `3b16d03e…` (all as bound in `fab/m3_fab_manifest.json`), `fab/cost_check.json`
  (2026-10-18T02:59:14Z) and `fab/stock_check.json` (03:00:28Z).
- **Comparison:** the pass-3 board `7660620c…` as described in `pass3_*.md`, `fix3_F4_handoff.md` and
  `fix3_docs_handoff.md`.
- **Method:** read-only. Measurements on a scratch copy of the board with KiCad 10.0.6 pcbnew; scripts and outputs in
  the session scratchpad `p4docs/`. Bytecode writing was off. `jlc_orient.py --verify-cpl` was run from a scratch copy
  of the tool, because the repository copy rewrites `tools/jlc_corrections.json`. The only repository file written is
  this report.

## 1. Summary

**Gate, tests and fab binding reproduce on the final board.** `tools/check.sh` exits 0:
- DRC 0, unconnected 0, schematic parity 0, ERC 0; metadata/3D audit OK; 0 silkscreen points outside the outline;
- R7 CAD contract OK; routing hygiene "0 failing, 42 allowlisted, 0 stale"; actuator contract OK;
- fit OK (J9 mated 0.03 mm, C84 0.11 mm; nearest bottom envelope C76 4.150 mm; nearest top hardware TP30.1 5.008 mm).

All suites pass: test_check_shell 2, test_fab_validation 23, test_fit_check 23, test_maze_clearances 10,
test_procurement 15, test_r6_check 17, test_r7_check 34, test_route_check 27, quality_audit 21 (172, as STATUS
says). `tools/fab_manifest.py`: "OK; 5 outputs match". The CPL check reproduces exactly: 92 top and 119 bottom rows
rebuilt, worst residual 0.491 mm, 8 placement-only, no errors, and the corrections file comes out byte-identical.

**Pass-3 findings in this dimension** (requirements, DFM, mechanical; section 2): every one is closed or
dispositioned in R7_VALIDATION, except **P3-REQUIREMENTS-01 (Major), which R7_VALIDATION itself records as "Partly
fixed; open"**. Its fixes check out: SWCLK 62.7 mm with 4 vias on F/B only, PYRO1_CONT 47.6 mm with 4 vias, M2's
"What the gate enforces" matches `tools/route_check.py` line by line, and the J2.1 via, C304 and TP89 records are right.

**New in pass 4:** 1 Major and 4 Minor findings.

- **Major P4-DOCS-01 (carries P3-REQUIREMENTS-01): M2 is still not met on the final board, so R7 acceptance is not
  met.** The gate is honest now, but:
  - its 42 allowlist entries include 15 AGENTS §3 rule instances (4 staircases, 11 critical layer changes with no GND
    via);
  - 46 non-critical residuals carry no measured reason: 13 detours, 19 nets over the via count, 8 tiny jogs and 6
    short segments. R7_VALIDATION nevertheless lists them under "Recorded deviations (measured and reasoned)".
  - Some are plain debris that a two-segment route removes. LED_YEL_A, for example, has 5 segments including a 99 µm
    one, and a 2-segment route clears by ≥ 0.45 mm.
  - No owner acceptance exists ("None is accepted yet").
- **Minor P4-DOCS-02:** the F4 DC solve uses 35 µm copper on the inner layers, against the ordered stackup's
  0.030 mm. With the board's own stackup, BAT_IN J1 → Q120 comes out 4.55 mΩ, not the recorded 3.91 mΩ (+16 %).
- **Minor P4-DOCS-03:** SWDIO's rerouted In2 run is recorded as a "5.9 mm In2 hop". It is 13.73 mm on In2, followed
  by a 2.58 mm B.Cu hop between two vias.
- **Minor P4-DOCS-04:** fix pass 3 newly showed designators D120 and R155. Each sits nearer another part's courtyard
  than its own (AGENTS §3), and the records list only R80, R172 and TP84.
- **Minor P4-DOCS-05:** two small arithmetic or number mismatches in M3_R7.

**R7 acceptance (REQUIREMENTS, last section):**
- Met: the gate; M3 ($105.96 per board, 52 of 52 extended codes, snapshot 2026-10-18 02:59Z); the fab binding.
- Not met: "no open Critical or Major" (P4-DOCS-01); M1 stock (U4 consignment, documented); JLC's written forward-rail
  confirmation (documented pre-order gate).

## 2. Closure of the pass-3 findings in this dimension

| Pass-3 ID | Sev. | R7_VALIDATION disposition | Pass-4 check on `636a6bdc…` | Verdict |
|---|---|---|---|---|
| P3-REQUIREMENTS-01 | Major | Partly fixed; open | Measured: SWCLK F.Cu 54.14 + B.Cu 8.56 = 62.70 mm, 4 vias, no In1 or In2; SWDIO 53.72 mm, 4 vias; PYRO1_CONT 47.60 mm, 4 vias; CAM_PWR_EN 81.90 mm, 8 vias and CAM_MCU_TX 65.87 mm, 5 vias unchanged. M2's "What the gate enforces" (REQUIREMENTS l.75) matches `route_check.py`: `RULE`/`POUR` gated on every net, `HYGIENE` (incl. `detour` 1.6× / 2 mm, `extra_vias` need + 2) on `CRITICAL` = signal classes ∪ power (l.104–129, `gated()` l.1379). AGENTS §3 uses the same scope. No owner acceptance recorded | **Open** → P4-DOCS-01 |
| P3-REQUIREMENTS-02 | Minor | Fixed (record) | REQUIREMENTS P1, M3_R7 l.290, R7_VALIDATION l.208/215/218, STATUS open items all cite parent `43af048`; parent VEHICLE.md l.39 is the R7 row | Closed |
| P3-REQUIREMENTS-03 | Minor | Fixed | M3 and ORDERING §1 match `cost_check.json`: parts $77.8071, 92 codes, 52 extended, $105.96, $77.81 with minimum purchases; U4 $8.3896, U30 $17.3782, U31 $6.5203, J30/J31 $0.7184; the other R7 lines sum to $1.05; U4-consigned $109.44–114.53. Stock: short U4 only, thin none; U30 159, U31 462, C530661 3,299 | Closed |
| P3-REQUIREMENTS-04 | Minor | Fixed | ORDERING l.25 lists C303, C304, C305, C313, C314; §4: top TP30 and TP84, 22 bottom test pads (measured); `check_r7.DNP` includes C304 (l.65); C304 at (7.74, 16.90) B as ORDERING says | Closed |
| P3-REQUIREMENTS-05 | Minor | Documented | Via 3V3 (44.035, 77.92), drill 0.30 mm, 0.400 mm from J2.1's centre; hole edge 0.144 mm inside the Ø0.787 mm opening. M2 names it. ORDERING §3 l.58, §4 l.100 and l.117 list it. My whole-board scan (via hole to every pad mask opening, THT included) finds only this via and TP122's | Closed |
| P3-REQUIREMENTS-06 | Minor | Fixed | `RF_PART` includes `Q3\d` (l.104); `rf_part_coverage` (l.489) is in the passing contract | Closed |
| P3-REQUIREMENTS-07 | Minor | Fixed | (a) AGENTS §3 and M2 agree (scope above). (b) P2 says "owner-delegated decision". (c) F10 and M3_R7 l.146–148: netlist U1.57 RADIO_DIO1 PD10, U1.8 PULLPIN PC14, U1.62 VBUS_SENSE PD15. The other lines-10–15 pins are outputs, AF or capture (PC13 CAM_UART_OE, PD14 TIM4 capture, PD11–13 QSPI, PB10–15 UART/SPI2, PE15 RXEN) | Closed |
| P3-DFM-01 | Minor | Fixed | As P3-REQUIREMENTS-04 | Closed |
| P3-DFM-02 | Minor | Fixed | As P3-REQUIREMENTS-03 | Closed |
| P3-DFM-03 | Minor | Fixed | `JLCJLCJLCJLC` B.SilkS at (23.9, 90.4); ink box (18.87, 89.78)–(28.97, 90.93), as ORDERING l.60 says; nearest via edge 0.176 mm (SERVO2_MCU (18.4, 89.8)); nearest label TP73's 0.154 mm; nearest mask opening R155.2 0.51 mm; no overlap | Closed |
| P3-DFM-04 | Minor | Documented | As P3-REQUIREMENTS-05 | Closed |
| P3-DFM-05 | Minor | Not done; open | Recorded open in R7_VALIDATION l.330, l.427 and STATUS | Properly dispositioned (open Minor) |
| P3-DFM-06 | Minor | (a)(b) fixed; (c)(d) open | GNSS ink 0.22 mm and RADIO 0.225 mm from the nearest via edge; J31's designator off RADIO's end. (d): newly shown D120 and R155 add to it (P4-DOCS-04) | (a)(b) closed; (d) incomplete |
| P3-MECHANICAL-01 | Minor | Fixed (documents) | Kinghelm KH-SMA-KE8-G datasheet p. 1 (LCSC C530661 PDF), "Recommended mating torque 0.8～1.13 N·m": confirmed. REQUIREMENTS P3, ORDERING §5/§7, MARGIN R14 (R7) and M3_R7 agree | Closed |
| P3-MECHANICAL-02 | Minor | Fixed (documents) | MARGIN R14 (R7): "⚠ ≥ 5× rests on the staking (Inference)". Moments 45 / 190 / 370 N·mm follow from 1.8 g / half / 5.5 g at 5 × 100 g (5.5 g × 981 m/s² × 5 = 27 N, × 14 mm ≈ 378 N·mm). ORDERING §7 saddle on the plug axis; M3_R7 l.573–580 | Closed |
| P3-MECHANICAL-03 | Minor | Fixed (record) | As P3-REQUIREMENTS-02. The proposed VEHICLE additions are with the coordinator | Closed |
| P3-MECHANICAL-04 | Minor | Fixed (tools) | `fit_check.check_board` l.300–307 adds exposed B.Cu/B.Mask, non-tented pads of board features and DNP parts. Bottom pads nearest a support: C76.2 4.423 mm and TP92.1 4.596 mm (pad box to hole centre), as ORDERING §7 says; the C76 body envelope (4.150 mm) stays the nearest | Closed |

## 3. Findings

| ID | Sev. | Requirement | Finding | Evidence | Fix |
|---|---|---|---|---|---|
| P4-DOCS-01 | Major | REQUIREMENTS M2 (owner clean-routing criterion over the whole board: AGENTS §3, plus no needless detours, extra vias or layer hops, micro-segments or tiny jogs, autorouter debris); REQUIREMENTS "R7 acceptance" (independent review with no open Critical or Major); carries P3-REQUIREMENTS-01 | **M2 is still not met on the final board, and P3-REQUIREMENTS-01 stays open.** Fix pass 3 made the gate honest: M2 now says what the gate enforces and what review checks, and STATUS says "M2 itself is not met". The requirement itself is still unmet in three ways. **(1) AGENTS §3 rule instances are allowlisted, not removed or accepted.** Of the 42 entries, 15 are §3 rule categories: 4 staircases and 11 critical-signal layer changes with no GND via within 1.5 mm. **(2) 46 non-critical residuals have no measured reason.** M2's own list covers them ("over the whole board"), and review was to check them. R7_VALIDATION's heading calls them "measured and reasoned", but only CAM_MCU_TX and CAM_PWR_EN carry a reason. Some are plain debris that a simpler route clears. **(3) No owner acceptance is recorded**, and M2 counts every allowlisted or review-only item as a deviation until there is one. | **Gate run** (`route.json`, 2026-10-17): 334 instances, 0 failing, 42 allowed, 0 stale. Allowlisted §3 rules: staircases RADIO_NRST (10.0, 27.7), RADIO_BUSY (9.4, 28.2), RADIO_MISO_MCU (10.0, 28.7), RADIO_SCK (10.0, 29.7); 11 `critical_via_no_gnd` at 1.65–7.89 mm (`route_check.py` ALLOWLIST l.159 ff.).<br>**Non-critical, counted not gated** (`route.json`): `detour` 13 (CAM_MCU_TX 2.67, BUZZ_OUT 2.57, CAM_PWR_EN 2.52, SERVO2_OUT 2.19, BAT_SW_RETURN 2.10 (160.3 mm, 5 vias), SWCLK 1.90, SERVO4_OUT 1.83, CAM_EN 1.81, BAT_FAULT_N 1.78, CAM_FAULT_N 1.77, SERVO4_MCU 1.71, CAM_5V_SENSE 1.66, RAW_ACT_SENSE 1.62); `extra_vias` 19 nets (e.g. LOGIC_SOURCE_ST 11 vias, SERVO2_MCU 9, BAT_SW_SOURCE 7); `tiny_jog` 8; `short_segment` 6. R7_VALIDATION l.355 heading "(measured and reasoned; owner acceptance pending)"; l.372–374 lists them with no reason. M3_R7 l.441–444 likewise.<br>**Debris examples** (pcbnew; candidate clearance with the pass-2 reviewers' `cand.py` method, other-net tracks, vias and pads, fills ignored):<ul><li>**LED_YEL_A** (F.Cu, LED2.1 (40.35, 26.5) → R33.2 (42.7, 29.4)): 5 segments, (40.35, 26.5)→(40.35, 27.4467)→**(40.4492, 27.4467) [99 µm]**→(41.8868, 28.8843)→(41.8868, 29.4) [0.516 mm jog]→(42.7, 29.4). The 2-segment route (40.35, 26.5)→(40.35, 27.05)→(42.7, 29.4), 0.15 mm wide, clears all other-net copper by ≥ 0.452 mm (R33.1) and 0.65 mm (CAM_MCU_TX).</li><li>**CAM_RX_WIRE** In2: the vertical run steps 0.16 mm in x (44.0895 → 44.251) across its T at (44.05, 55.14), through a 58 µm and a 0.287 mm segment.</li><li>**CAM_EN** B.Cu (U7.2 → via (35.75, 86.6)): 7 segments, including a 61 µm segment (37.95, 85.2033)→(37.9067, 85.16) and a 0.293 mm jog. My naive 2-segment candidate collides with U7.9 and CAM_DVDT, so this one may be forced (not shown either way).</li></ul>**No acceptance:** R7_VALIDATION l.357–358 "None is accepted yet"; l.425 lists P3-REQUIREMENTS-01 as open; STATUS l.17 "Do not order yet … P3-REQUIREMENTS-01 (Major) is only partly fixed", l.93 "M2 itself is not met until the owner accepts them". P3-ROUTING_GEOMETRY-04 (review of the information-only instances on critical nets: 140, plus 36 power vias) is also open (R7_VALIDATION l.346).<br>**Severity:** the pass-4 rubric makes an unmet requirement, including AGENTS §3 clean routing on any net, Major. The documents agree it is unmet. The cheap debris shows that part of the residual is not forced. | <ol><li>Remove the cheap non-critical debris: short segments and tiny jogs on LED_YEL_A, CAM_RX_WIRE, CAM_5V_SENSE, SERVO3_MCU, LOGIC_ILIM and the rest of `route.json`'s 14. Or give each a measured reason, as the allowlist does.</li><li>Give each of the 13 non-critical detours and 19 over-via nets a measured reason (a raster-search result, as F4 did for CAM_PWR_EN), or reroute it. Change R7_VALIDATION's heading to say which items are reasoned.</li><li>Put the owner's decision on record. Either a dated owner acceptance of a named deviation list (the allowlist plus the residuals), referenced from M2 the way M2 already points at M3_R4 §2 for thermal reliefs, or an instruction to reroute further. Until then R7 acceptance is not met, as STATUS already says.</li></ol> |
| P4-DOCS-02 | Minor | REQUIREMENTS F4 ("independently solve the final copper … recorded in M3_R7 §DC solve"); M1 stackup (JLC041611-7628, 1 oz inner); AGENTS §2.5 | **The F4 DC solve models the inner layers with the wrong copper thickness and an older stackup's via barrels.** The records quote its In2 paths to ±2 %. `dc_solve.py` uses 35 µm on every layer and via barrel lengths "JLC04161H-7628". The board's own stackup, the job file, ORDERING §3 and M3_R7 give JLC041611-7628 with **0.030 mm inner copper**; JLC's calculator gives 1 oz internal as 1.2 mil, about 30.5 µm. Paths carried on In2 are therefore under-estimated by about 15–17 %. Paths on F.Cu/B.Cu are, if anything, over-estimated: JLC's external 1 oz is 1.6 mil. Comparisons with R6 hold, since both used the same model. The absolute In2 values and the "±2 %" claim do not. No F4 limit is numeric, so this is a record error, not a failure. | `tools/dc_solve.py` l.29 `T_CU = 35e-6  # 1 oz, every layer (M1)`, l.31 `Z = {… In1 0.245, In2 1.345, B 1.59}  # mm, JLC04161H-7628`, l.247 `gs = T_CU / RHO` for all layers. `m3.kicad_pcb` stackup l.65–79: In1.Cu and In2.Cu thickness 0.03, core 1.03. Job file: In1/In2 0.03 mm. ORDERING l.52: "0.030 mm inner copper". JLC impedance-calculator user guide, "Calculation Parameters Used": internal copper 1 oz 1.2 mil, external 1 oz 1.6 mil (https://jlcpcb.com/help/article/user-guide-to-the-jlcpcb-impedance-calculator).<br>**Rerun** (scratch copy of `dc_solve.py`: inner 30 µm, barrel Z from the 0.035/0.203/0.030/1.03 stack; BAT_IN J1:1 → Q120:5–9, 0.1 mm grid): **R = 4.55 mΩ**, 35.0 mV and 0.269 W at 7.7 A, 100 % In2 at mid-path, peak 6.17 A/mm at (10.45, 107.62). The unmodified tool on the same scratch board gives **R = 3.91 mΩ**, 30.1 mV and 0.232 W (reproducing the record), so the stackup correction alone is +16 %. M3_R7 l.526 records 3.91 / 3.87 mΩ; l.517–521 claims "the others to about ±2 %". | Make `dc_solve.py` read each layer's copper thickness and the dielectric stack from the board stackup (or set In1/In2 to 30 µm and fix the Z comment). Rerun the F4 table and restate M3_R7 §DC solve. Call "equal to R6" a same-model comparison. Optionally note the In2 peak current density at 30 µm for the IPC-2152 sizing in AGENTS §3. |
| P4-DOCS-03 | Minor | Document accuracy (M3_R7 record of the fix-pass-3 reroute); M2 records | **SWDIO's reroute is misrecorded.** M3_R7 and the F4 handoff say SWDIO runs "with a 5.9 mm In2 hop between J122's rows". The board has 13.73 mm on In2, then a 2.58 mm B.Cu hop between two vias before it rises to F.Cu, so the route is F → B → In2 → B → F. The In2 run crosses no In2 pour (no fill at the sampled points beside it), so this is a record error, not a plane split. | SWDIO tracks: In2 (18.55, 73.1)→(26.7, 73.1) 8.15 mm, →(30.15, 69.65) 4.88 mm, →(30.85, 69.65) 0.70 mm; B.Cu (30.85, 69.65)→(33.43, 69.65) 2.58 mm; vias (19.55, 55.55), (18.55, 73.1), (30.85, 69.65), (33.43, 69.65). Per layer F 18.41, B 21.58, In2 13.73 mm (total 53.72, matching the records). M3_R7 l.366; `fix3_F4_handoff.md` l.44. | State the actual layer sequence and In2 length in M3_R7 (and the handoff if it is kept as a record). Say whether the 2.58 mm B.Cu hop is forced: an In2 run on to (33.43, 69.65) would save one via. |
| P4-DOCS-04 | Minor | AGENTS §3 silkscreen ("never next to another part"; a designator with no spot nearer its own part than any other is hidden and listed); M3_R7 §Silkscreen; P3-DFM-06(d) | **Fix pass 3 showed designators D120 and R155 again without the courtyard test.** Measured ink to courtyard, each is nearer another part's courtyard than its own. M3_R7 says the ink-box courtyard test "runs only for FB31" and lists only R80, R172 and TP84. D120 is the pyro-block diode, and its legend's north end reaches toward C121 (the 470 µF can). | Ink polygon to courtyard polygon (pcbnew, `meas5.py`): **D120** F.SilkS text at (29.5, 81.73), vertical: own courtyard 0.472 mm, **C121's 0.225 mm**. **R155** B.SilkS at (19.56, 87.48): own 0.579 mm, **R151's 0.560 mm**. Recorded ones reproduce: TP84 own 0.416 / C84 0.376; R80 0.786 / D8 0.521; R172 0.962 / Y1 0.878. The other newly shown designators (R156, R157, TP70, TP73, TP76, TP82, TP87, TP88) are nearest their own part. M3_R7 l.596–599; R7_VALIDATION l.331. | Run `r7_post`'s courtyard test on every visible designator. Move or hide D120 and R155 (and R80, R172, TP84) and list them in M3_R7 §Silkscreen. |
| P4-DOCS-05 | Minor | Document accuracy (M3_R7) | **Two small number mismatches.** (a) M3_R7 says "U4 (−$2.82) and U30 (−$2.40) account for the difference" between $110.93 and $105.96. They sum to $5.22, against a $4.97 difference, so other lines moved too. (b) M3_R7 gives the left tab 1.84 mm from J3, while ORDERING and M3_R7's next sentence say 1.83 mm. | M3_R7 l.663, l.673, l.676; ORDERING l.66, l.72. | (a) "account for most of the difference". (b) Use one figure. |

## 4. Requirement walk (final board `636a6bdc…`)

Verdicts:
- **Pass:** shown in the CAD, schematic, gate or fab files.
- **Fail:** not met.
- **NV:** needs the bench, flight or firmware.
- **Partial:** the CAD part passes and the rest is open.

### Sources and owner decisions

| Item | Verdict | Evidence |
|---|---|---|
| One primary pyro channel; isolated Blue Jay | Pass | `check_r7` REMOVED set; no backup interface |
| 4-servo limit | Pass | J122 3 × 4; `check_actuators` OK |
| On-board MAX-F10S and E22-900MM22S, JLC-assembled | Pass | BOM C30005563 / C5333985 (SMT); CPL top |
| Uplink never arms or fires | Pass (CAD) | `check_r7` safety-net check with `rf_part_coverage` (Q30–Q32 now covered); ARM is the physical J124 link |
| Parent CLAUDE.md / VEHICLE.md | Pass | VEHICLE.md l.39 (R7 row, `43af048`); CLAUDE.md avionics paragraph consistent (≤ 120 mm: 118) |

### Functional

| ID | Verdict | Evidence / remark |
|---|---|---|
| F1–F3, F5 | Pass (parts) | Unchanged from R6 |
| F4 | Partial | Outputs pass (`check_actuators`). Solve recorded, but inner copper mis-modelled (P4-DOCS-02). Stall test: bench |
| F6, F7 | Pass (CAD) | Unchanged circuits; `check_actuators` OK |
| F8 | Pass (CAD) | DRC 0 under the pyro rules (PYRO1_CONT's new In2 run included); legends ARM/IGN/GNSS/RADIO; bench gates NV |
| F9 | Pass (CAD part) | Unchanged |
| F10, strip and pin contract | Pass | `check_r7` OK: strip net lists, pin map (netlist U1.45/51–57/61–65 checked), keep-outs, `launch_reference`, `module_ground`, `rf_gnd_reach`. 3 new strip GND vias (0.5/0.3 mm) at the recorded coordinates |
| F10, distances | Pass | Nearest fast-digital copper (QSPI/SPI1/USB/HSE/IMU_CS/SWD) to any RF-part courtyard: 6.49 mm (QSPI_IO0 to R313, a corridor series resistor); to the modules and RF chain, farther. SWD after the reroute > 13 mm |
| F10, binding constraints | Pass (record) | EXTI9_5 and EXTI15_10 notes complete against the netlist |
| F10, bench clauses | NV | ORDERING §5 |

### Physical

| ID | Verdict | Evidence |
|---|---|---|
| P1 | Pass | 46 × 118 mm (`fit_check`); parent VEHICLE row recorded; board position open (Onshape) |
| P2 | Pass (CAD) | 5 supports; bottom/pad standoff rule now includes bare and DNP pads (nearest C76 4.150 mm); mated envelopes J9, J122, J123, J30, J31 present; span estimate carried over (copper-only changes, Inference recorded) |
| P3 | Pass (record/procedure) | Torque sourced (Kinghelm p. 1, confirmed); R14 (R7) "⚠ rests on staking (Inference)"; MEMS keep-outs `IMU_body_B`, `BARO_body_B` (vias and fill excluded); new GND via (29.28, 77.95) is outside the IMU body |

### Manufacturing and cost

| ID | Verdict | Evidence |
|---|---|---|
| M1 | Pass, except U4 stock (allowed) | Job file: 4 layers, 1.6 mm, ENIG, 0.035/0.203/0.030/1.03/0.030/0.203/0.035; CPL 219 rows (96 top, 123 bottom; 4 + 4 placement-only); CPL check reproduced; stock short U4 only |
| M2, JLC rules, via-in-pad, paste, silk | Pass, with Minor P4-DOCS-04 | DRC 0. Via scan: only TP122 and the named J2.1 exception. Paste Gerbers: no flash in any J30/J31 pad or the C303/C304/C305/C313/C314 lands; one per pad on R304, R316 and C302. No visible text under 1.0 mm or 0.15 mm, no silk stroke under 0.15 mm |
| M2, clean routing | **Fail** | P4-DOCS-01 |
| M3 | Pass | $105.96, 52 / 52, bound to the current BOM/CPL |

### R7 acceptance

| Condition | Status |
|---|---|
| `check.sh` zero; actuators, fit and `route_check` OK | Met (reproduced) |
| Independent review with no open Critical or Major | **Not met** (P4-DOCS-01, and any Major from the other pass-4 dimensions) |
| M3 on a ≤ 24 h snapshot | Met at the time of review (02:59Z); rerun before ordering |
| M1 stock, U4 by consignment | Open (documented) |
| Fab outputs regenerated and bound | Met (`fab_manifest.py` OK; manifest binds `636a6bdc…`) |

## 5. Document consistency (beyond the findings)

These agree with one another and with the board:
- REQUIREMENTS M2 against `route_check.py`: categories, scopes, thresholds, allowlist rule, stale-entry rule;
- AGENTS §3 against M2: critical-signal scope, pointer to the gate;
- the R7_VALIDATION counts against `route.json`:
  - 13 / 19 / 8 / 6 non-critical;
  - 63 / 29 / 18 / 10 / 10 / 8 / 2 info-only on critical nets;
  - 36 power vias;
- the gate output against STATUS, M3_R7 and R7_VALIDATION;
- the test counts (151 + 21 = 172);
- the hidden-designator list: 83 on the board, identical to M3_R7 l.593–596 and `fix3_F4_handoff.md` §2;
- ORDERING §3 placeholder and via rows, §4 assembly split and DNP list, §7 hardware distances;
- MARGIN R14 (R7); FMEA I-11 and V-19 (unchanged, still accurate); AGENTS §1 manufacturing row;
- the parent VEHICLE row; the pass-1/2/3 tallies in STATUS against R7_VALIDATION.

Not raised again (already recorded open):
- P3-RF-02 / P3-DFM-05 (C302 thermal; tombstone check);
- P3-ELECTRICAL-01/-02(a) (sheet-15 notes);
- P3-DFM-06(c) ("915 MHz" wording);
- P3-ROUTING_GEOMETRY-04;
- `procurement_catalog.json` LS120 reflow;
- U4 consignment path;
- the forward rail;
- `test_r5_repair`.

## 6. Measurements and reproductions

Scratchpad `p4docs/`:
- **Gate:** `tools/check.sh`, 2026-10-17 21:2x PDT, exit 0. Reports copied to `gate/`: `route.json`, `fit.json`, `r7.json`.
- **Tests:** each suite under KiCad Python with `PYTHONDONTWRITEBYTECODE=1` (counts in §1).
- **Fab:**
  - `fab_manifest.py` OK;
  - BOM/CPL SHA-256 equal to `cost_check.json` `inputs_sha256`;
  - CSV counts;
  - paste flashes parsed from `m3-F_Paste.gbr` (370) and `m3-B_Paste.gbr` (337) against pad boxes (`s/paste.py`,
    `s/paste2.py`);
  - CPL check from a scratch copy of `jlc_orient.py`.
- **Board scripts:**
  - `s/nets.py`: route_check classes per net;
  - `s/meas1.py`: placeholder, J2.1 via, hidden designators, test-pad sides, rule areas, new vias;
  - `s/meas2.py`: placeholder ink clearances;
  - `s/meas3.py`: pads near supports;
  - `s/meas4.py` / `s/meas5.py`: silkscreen sizes and designator-to-courtyard distances;
  - `s/meas6.py`: via hole to every pad mask opening;
  - `s/meas7.py`: fast nets to RF parts;
  - `s/meas8.py`: SMA legends;
  - `s/meas9.py`: In2 fill beside SWDIO;
  - `s/netlay.py`, `s/dump.py`: per-layer lengths and track dumps;
  - `s/cand4.py`: candidate-route clearance;
  - `s/dc_solve_r7stack.py`: `dc_solve.py` with per-layer thickness.
- **Netlist:** `schematic.net.xml` U1 pins (F10 binding).
- **Datasheet:** Kinghelm KH-SMA-KE8-G p. 1 (LCSC C530661 PDF), read as an image.

## 7. Sources

- Repository documents, by line:
  - REQUIREMENTS, ORDERING, M3_R7, R7_VALIDATION, STATUS, AGENTS, MARGIN_PRESCRIPTION, FMEA_REDUNDANCY;
  - `fix3_F4_handoff.md`, `fix3_docs_handoff.md`, `pass3_*.md`, `pass3_verdicts.json`;
  - `tools/route_check.py`, `tools/check_r7.py`, `tools/fit_check.py`, `tools/dc_solve.py`.
- Kinghelm KH-SMA-KE8-G datasheet:
  https://datasheet.lcsc.com/datasheet/pdf/35ad22a9bea57e53d493009a20c931ef.pdf?productCode=C530661 (p. 1:
  recommended mating torque 0.8～1.13 N·m; assembly torque ≥ 0.5 N·m; wave-solder resistance 240～250 °C, 5 s).
- JLCPCB impedance-calculator user guide, "Calculation Parameters Used": internal copper 0.5 oz 0.6 mil, 1 oz 1.2 mil;
  external 1 oz 1.6 mil. https://jlcpcb.com/help/article/user-guide-to-the-jlcpcb-impedance-calculator
- JLC parts data as captured in `fab/cost_check.json` / `stock_check.json` (source "jlcpcb.com
  selectSmtComponentList", 2026-10-18T02:59–03:00Z).

## 8. Inferences (not checked against a primary source)

- **P4-DOCS-02:** the 30 µm inner copper rests on the project's recorded stackup and on JLC's calculator parameter.
  JLC's template page for JLC041611-7628 itself was not found online (the public impedance page shows only
  JLC04161H-7628). The 15–17 % figure applies to paths carried on In2.
- **P4-DOCS-01:** "cheap" is shown for LED_YEL_A only, by a clearance probe that ignores zone fills; the pour would
  refill around the new route. CAM_RX_WIRE's offset is judged from its geometry, not probed. CAM_EN may be forced.
- **P4-DOCS-04:** the courtyard-nearness test uses ink polygons and courtyard polygons. `r7_post`'s own ink-box test
  may rank R155 (0.560 against 0.579 mm) differently.
