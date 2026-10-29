# R8 review pass 3: requirements traceability

Reviewer dimension: requirements traceability. I checked every REQUIREMENTS row (F1–F10, P1–P3, M1–M3, R8 acceptance)
against the CAD, the gate and the records. I also checked:
- the R8 pin contract against F10, R8_DECISIONS (D2–D6, D6.8) and the binding note;
- the consistency of REQUIREMENTS, STATUS, ORDERING, MARGIN_PRESCRIPTION, AGENTS, M3_R8, R8_VALIDATION and README;
- whether the R8 deviation list is complete and honest after fix pass 2.

- **Board:** `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
  `990c8040c5b8457bd2bd1717ed3e5c2725f32c1dda1cd7f826a0c2b458d28b18`; netlist `0cc1ed692fb99dd2…`. I checked the hash
  before my runs, and every measurement ran on a scratch copy with that hash.
- **Read-only:** this report is the only repository file I changed. The board was never saved, and `git status
  --porcelain` matched before and after. My scripts, the board copies and all outputs were in the session scratchpad
  (`p3req/`) and were deleted afterwards. This includes a copy of the R7 board, read for precedent; R7's worktree was
  not touched.
- **Labels:** "Inference" marks anything not measured and not taken from a maker document.

**Result: 0 Critical, 0 Major, 4 Minor (all worth fixing, all record-only).** Every pass-2 finding in this dimension is
closed. The requirement walk finds no row that the CAD fails. The four findings are record gaps:
- **01:** ORDERING §5 lacks three bench checks that STATUS attributes to it. The important one: since fix pass 2 (D6.8),
  the pyro gate must be held low in the ROM bootloader, and no bench step checks it.
- **02:** the records misdescribe the actuator-gate-to-GND item that fix pass 2 left as a "candidate for pass 3".
- **03:** the owner summary's list of decisions that relax a plan gate leaves out D51.
- **04:** two wording slips.

## 1. What I ran

| Run | Result |
|---|---|
| `tools/check.sh` (KiCad 10.0.6) | **Exit 0.** DRC 0, unconnected 0, parity 0, ERC 0. Metadata / 3D audit OK; no silkscreen outside the outline; `check_r8` OK (no issues, no notes). route_check r8: 0 failing, 3 allowlisted, 0 stale, 0 leftovers, 0 removable (22 bump windows). `check_actuators` OK. `fit_check` OK (J9 mated 0.03 mm, C84 1.37 mm, R12.1 4.452 mm from (4, 64), TP30.1 5.008 mm) |
| `check_r8` evidence | 12 / 12 rigid digests. battery_pyro 1.089 mm (ACT_FET_S to J124.1). via_paste: 709 pairs, nearest ring 0.025 mm (C90.1). inner_power_pyro 2.65 mm. terminal_legends: all 10 nearest their own pin. Loader pins as D5. Fence: 25 vias, openings 2.015 / 2.60 / 2.10 / 2.05 mm, every other gap ≤ 2.000 mm (from `r8_ground.tsv`). rf_stitching 3.90 / 2.65 / 1.55 / 1.55 mm. rf_separation: R306–U1 5.94 mm, R306–USB_DM 5.075 mm |
| route_check `route.json` | 93 instances: 3 allowed (A8; GNSS_LNA_EN 7.65 / 3.72 mm; GNSS_VCC_RF 6.2 / 2.61 mm) and 90 information (41 / 14 / 8 / 7 / 7 / 7 / 4 / 2). This matches part E and C19 |
| `step9/m2_sweep.py` on `990c8040…` | 23 chain detours; 54 adjacency rows giving 29 net pairs, 10 of them at 0.150 mm; 36 pad rows (4 fine, own part); 28 route rows (12 nets over their via need); 26 via folds; 1 via step; 2 poured hops; 9 short_hop rows (2 hops and 7 power_via_no_gnd); 0 pad-edge ends; 1 bump candidate. **Every key is equal to the recorded `step9/evidence/fix2_m2_sweep.json`.** C12's 29 rows match the sweep pair by pair, and C12b's 32 rows match it row by row |
| Tests | 17 suites, 272 tests OK (KiCad Python); quality_audit 21 OK |
| `fab_manifest.py` / `jlc_orient --verify-cpl` | Manifest OK, 5 outputs, bound to `990c8040…`. BOM `be711876…`; CPL `25cfed69…`. CPL rebuilt: 85 top + 126 bottom rows, worst 0.491 mm, 8 placement-only, 219 rows |
| `cost_check.json` / `stock_check.json` | $106.00, 52 extended, `checked_utc 2026-10-19T23:51:04Z` (stock 23:50:07Z, `ok: false`, short U4). The cost report binds BOM `be711876…` and the **step-9 CPL `d26572d3…`**. Not re-run (needs the network) |
| `route_check --profile r7` on a copy of R7 `c872a3d3…` | OK (0 failing, 45 allowlisted, 29 leftovers). This confirms `check.sh`'s comment that the shared tool still passes R7 after fix pass 2's edit |
| DC evidence `step9/evidence/fix2_dc_*.txt` | The first line of each is `990c8040…`. RAW_ACT 1.45 mΩ, 5.94 mm, 17.5 °C, largest via 0.86 A. BAT_IN 0.45 mΩ, 6.99 mm, 14.5 °C, largest via 0.65 A, 4 vias over 0.5 A. ACT_FET_S 0.18 mΩ, 4.97 mm, 21.4 °C. GND return 0.69 mΩ; largest via 0.26 A, and the second, 0.24 A, is the step-7 via at (15.0, 107.3) (finding 02). Not re-run (60 min) |
| My pcbnew scans (Appendix A) | Placement: 249 footprints (94 F / 131 B non-TP; TP 5 F / 19 B; DNP C303 / C304 / C305 / C313 / C314). 81 designators hidden, set-equal to M3_R8's list; 168 shown; 203 visible silk texts (168 + 35 legends), none under 1.0 mm high or 0.15 mm stroke. THT GND pads: only J122.3 / 6 / 9 / 12 FULL, the rest inherit relief. TP122 holds the only in-pad via. J2's nearest via 0.915 mm (NRST (0.8, 42.75)). U4 / U5 bodies: no via, no pour, only pad escapes and inter-pad GND links. Different-part pad-to-pad gaps under 0.2 mm: none. Copper gaps: ACT_GATE / ACT_DRV and BAT_ENABLE neighbours, the drain's nearest battery copper (3.562 mm, R82.1–J121.1). Pour extents. U1 pin map and pulls from the netlist |

## 2. Closure of pass 2 in this dimension (`pass2_requirements.md`, board `6600ef94…`)

| Pass-2 ID | Item | On `990c8040…` |
|---|---|---|
| R8P2-REQUIREMENTS-01 | The adjacency sweep left out pad-to-copper gaps | **Closed.** `m2_sweep.adjacency_pad` (D104). The C12b rows equal my run row for row (32 listed, 4 fine-pitch counted). R7 C15 #1 and #6 are restored as #4 / #30; I re-measured them on R7: 0.170 / 0.1925 mm, the same as R8. The BAT_ENABLE–BAT_IN latch pair (Q120.9, 0.180 mm) is in the pyro observations. R81's two pairs are gone (D100). Part F and the scope sentence are updated |
| R8P2-REQUIREMENTS-02 | "A second consecutive pass" understated the condition | **Closed** (R8_VALIDATION l.8–10, l.133; STATUS l.11–13; AGENTS §1) |
| R8P2-REQUIREMENTS-03 | D5 called an owner decision; D70 missing from the list | **Closed** (hard-gate rows l.66–67; summary l.251–256). D51 is still missing (finding 03) |
| R8P2-REQUIREMENTS-04 | The C2 miss had no cause | **Closed.** C19 gives each category's measured reason and states that up to 71 R8-new instances are "not removed yet" beyond the one-segment search. The counts match `route.json` |
| R8P2-REQUIREMENTS-05 | README dropped the coupler | **Closed** (README l.3: "Ø50.8 mm coupler bore along its whole length; REQUIREMENTS P1/P2") |
| R8P2-REQUIREMENTS-06 | Six record mismatches | **Closed:** (a) MARGIN "4 over 0.5 A"; (b) AGENTS includes the 24 h run; (c) M2 points to C17; (d) F8 names `battery_pyro` and the drain; (e) ORDERING's stall test uses 21.4 °C as information; (f) STATUS dates and the R7 ORDERING branch |
| Pass-2 observation: C12 #17 (now #13) "the safe direction" | Pointed to the pyro reviewer | **Not acted on** (finding 04(a)) |
| Pass-2 observation: J1 `1:BAT+` legend | Cosmetic | Accepted as R8P2-DFM-02 |

## 3. Requirement walk on `990c8040…`

Verdicts:
- **Pass:** shown in the CAD, the gate or the fab files.
- **Partial:** the CAD part passes and the rest is open.
- **NV:** needs the bench, a flight or firmware.

| Row | Verdict | Evidence / remark |
|---|---|---|
| Sources (one CH1, isolated Blue Jay, 4 servos, on-board MAX-F10S / E22, uplink cannot arm) | Pass | `check_actuators` OK, its SHA asserted by `check_r8`; netlist unchanged since pass 1 (`0cc1ed69…`) |
| F1–F3, F5 | Pass (parts), NV | Circuit unchanged. U4 on the bottom, rotation 0, at (10.0, 53.8); lever arm x −13.0 mm, as in the binding note |
| F4 | Pass (CAD, calc), NV | Every figure in F4 equals the `fix2_dc_*` evidence: 1.45 / 0.45 / 0.18 mΩ; necks 5.94 / 6.99 / 4.97 mm; 17.5 / 14.5 / 21.4 °C; vias 0.86 / 0.65 A; GND 0.69 mΩ. All are within D12, and the build holds D12 at 0.1 mm (D95). The stall test (D105) is in ORDERING §5 |
| F6 | Pass (CAD), NV | Circuit unchanged; C24 at (25.33, 51.1) on NRST |
| F7 | Pass (CAD), NV | RAW_ACT Q121 → J124.2 0.44 mΩ (M3_R8 supply table) |
| F8 | Pass (CAD), NV | DRC 0 under the unchanged `m3.kicad_dru` (rules A–H). `battery_pyro` covers bus, igniter and drain; the drain's nearest battery copper is 3.562 mm (re-measured). Terminal legends are gated. Gate-net-to-GND spacing outside the block is the accepted-risk default (finding 02) |
| F9 | Pass (CAD), NV | Protection parts 3.9–10.6 mm from J1.1, unchanged by fix pass 2. Since D97 the U9 feed lane runs over In2 GND, a negligible change to the hot-plug model (Inference) |
| F10 | Pass (CAD), NV | Pin contract (section 4); strip rigid; fence gaps ≤ 2.0 mm, openings ≤ 2.6 mm; 5 mm separation (5.94 mm part, 5.075 mm line); every RF part including R314 is in the separation check. D6.8 now drives PE4 low first, but **the bench check of it is missing** (finding 01) |
| P1 | Pass | 46 × 118 mm. Parent VEHICLE's stack row still names R7 (D84 proposed; correct while R7 is the revision to order) |
| P2 | Pass (CAD), NV | Five supports. Nearest bottom pad 4.452 mm; tie path clearance 2.2 mm (R150). C10 open. The hole at (42, 114.4) is now GND on all four layers (D97; ORDERING §7 updated) |
| P3 | Pass | No via and no pour inside U4's or U5's body on their component side (B.Cu); only pad escapes and inter-pad GND links. U5's 3V3A trunk at y 57.85 lies outside its body (pads at y 58.375–62.025; body y 58.7–61.7). Coating and staking lists unchanged |
| M1 | Pass, except U4 stock | Stock short U4 only (consignment). CPL verified |
| M2 (rules, via-in-pad, silk) | Pass | DRC 0. TP122 has the only in-pad via (A8). J2's nearest via 0.915 mm. THT GND reliefs everywhere but C17's 4 pins. Silk ≥ 1.0 mm / 0.15 mm |
| M2 (clean routing, deviation list) | **Partial** | The list is complete in category and matches the sweep. Owner acceptance is open. Findings 02–04 are record fixes inside it |
| M3 | Pass (step-9 run) | $106.00, 52 / 52 extended codes, BOM unchanged. The CPL binding is stale (finding 04(b)); rerun within 24 h of ordering |
| R8 acceptance | Not met (as recorded) | Needs this pass clean (pass 2 was), the owner's acceptance of the list, U4 consigned and the 24 h cost run. The records state this correctly |

## 4. R8 pin contract against F10 and the decisions

- **The netlist agrees with F10.** I read each pin from `schematic.net.xml`:

  | Pin | Net |
  |---|---|
  | U1.3 PE4 | PYRO1_GATE_N (R126 220 Ω series; R127 1 kΩ to GND) |
  | U1.46 PB10 | RADIO_SCK_MCU |
  | U1.47 PB11 | RADIO_NSS (R310 100 kΩ to 3V3) |
  | U1.53 PB14 / U1.54 PB15 | RADIO_MOSI_MCU / RADIO_MISO_MCU |
  | U1.55 PD8 | RADIO_BUSY |
  | U1.56 PD9 | RADIO_RXEN (R312 100 kΩ to GND) |
  | U1.39 PE9 | RADIO_NRST (R311 2 kΩ to GND) |
  | U1.45 PE15 | RADIO_DIO1 |
  | U1.61 PD14 | GNSS_RESET_N (no capacitor) |
  | U1.62 PD15 | GNSS_TP_MCU (R307 1 kΩ, no pull-down) |
  | U1.63 PC6 / U1.64 PC7 | GNSS UART |
  | U1.37 PE7 / U1.38 PE8 | CAM_MCU_RX / CAM_MCU_TX |
  | U1.7 PC13 | BUZZ_DRV |
  | U1.65 PC8 | VBUS_SENSE |

- **The other records agree with each other.** `check_r8` asserts all 100 pins against `pin_table.tsv`. The table's
  SHA-256 `bd4687a8…` equals the binding note's, and the note is bound to `990c8040…` and `0cc1ed69…`.
- **D6.8 on PE4 is consistent** across F10, D6.8, the binding note (constraint 12) and M3_R8 "Firmware". All four say:
  drive PE4 low first, or reset GPIOE through RCC_AHB4RSTR, which returns PE4 to analog so that R127 holds the gate off.
  RM0433 §11.4.8 makes a peripheral reset clear the GPIOE_LCKR lock that constraint 7 sets. Only ORDERING §5 lags
  (finding 01).
- **Loader-mode pins.** The pin table's AN2606 Table 135 column gives these roles:
  - PA3 (SERVO4_MCU) is USART2_RX; PB11 (NSS, held high) is USART3_RX; PB15 is USART1_RX.
  - PA4 / PA5 / PA7 are SPI1 slave inputs; PE11 / PE12 are SPI4 slave inputs.

  None of these carries a source that could send the loader's 0x7F. Every pin the loader drives carries only a D5 net or
  is NC. **No contradiction found.**

## 5. Findings

| ID | Sev. | Requirement | Finding | Evidence | Fix |
|---|---|---|---|---|---|
| R8P3-REQUIREMENTS-01 | Minor (worth fixing) | F8 ("nothing fires … while armed with the MCU … booting or idle (bench gates …, ORDERING §5)"); F10 / D6.8 (since fix pass 2: PE4 low before any bootloader jump); STATUS l.86–90 ("Needs the bench … (ORDERING §5): … the camera buck's remote sense at J9.1 under a load step (D41), the IMU signs with the new lever-arm sign, … and the radio held in reset and the pyro gate low in the ROM bootloader (D6.8)") | **ORDERING §5 lacks three bench checks that STATUS attributes to it.** (a) The safety one: fix pass 2 added PE4 to D6.8, F10 and the binding note (R8P2-PYRO-03), but did not update ORDERING. ORDERING's only bootloader step still names the preparation as "SX1262 asleep, PE9 returned to analog" and measures only RADIO_NRST at R311.1 and RXEN at R312.1. No step shows that PYRO1_GATE stays low in the bootloader. That is the property D6.8 exists for: "a jump made with PE4 high would hold an armed gate on for as long as the bootloader runs" (binding note constraint 12). (b) D41's camera-buck remote-sense stability ("an Inference, a bench item", M3_R8 l.90–91) has no ORDERING step. (c) The IMU sign check with the flipped lever arm is in M3_R8's "IMU axis map" ("Confirm the signs on the bench") but not in ORDERING; this one is a firmware bring-up item (M3_R5 §3) | ORDERING l.161: "Repeat once in the ROM bootloader entered by the firmware's jump, after the binding's preparation (SX1262 asleep, PE9 returned to analog: R8_DECISIONS D6.8)". ORDERING §5 has no match for PE4, PYRO1_GATE_N, "load step", "J9.1", "gyro" or "lever". fix2_handoff's PYRO-03 row lists `binding_note.py`, D6.8 and F10, not ORDERING. STATUS l.86–90 | (a) ORDERING l.161: "… after the binding's preparation (PE4 driven low or GPIOE reset first, SX1262 asleep, PE9 returned to analog: D6.8); also read PYRO1_GATE at TP122 below 0.1 V there (ARM link out), and run the static pyro gate once with the board in the bootloader". (b) Add a camera-supply step: CAM_5V at J9.1 under a 0.1 → 1 A load step, settling without ringing and inside AP63301's regulation (D41). (c) Either add an IMU sign step to ORDERING §5 (rotate the board about +y_board: roll reads +gyro_Y; the centripetal a_X sign per M3_R8), or point STATUS at M3_R8 "IMU axis map" / M3_R5 §3 instead of ORDERING §5 |
| R8P3-REQUIREMENTS-02 | Minor (worth fixing) | M2 (each review residual "with … measured reason and why it cannot reasonably be removed (or that it has not been removed yet)"); REQUIREMENTS "Accepted risks" (gate-net spacing outside the pyro block is the 0.15 mm default); `m3.kicad_dru` rule H's reason ("a bridge pulling ACT_GATE down powers RAW_ACT with the power switch open") | **The records present the 0.180 mm step-7 GND via at bare R120.2 (ACT_GATE) as the exposure, and fix pass 2 offers a via-only change as the pass-3 remedy. The GND pours already sit at their 0.150 mm clearance from the same pad and from every other bare actuator-gate pad, as on the owner-accepted R7. Moving the via alone changes nothing.** The screen the records cite is a conditional step. The step that always runs is the 20-cycle switch test | On `990c8040…` (scratch copy, `SHAPE.Collide` bisection): GND_B fill 0.150 mm from R120.2 and C120.2 (ACT_GATE, B.Cu). Collide is false at 0.149 mm and true at 0.151 mm against R120.2, and GND_B's local clearance is 0.15 mm. GND_F fill is also 0.150 mm from R121.1 (ACT_GATE) and R121.2 / Q122.3 (ACT_DRV). The via (15.0, 107.3) is 0.180 mm from R120.2; it is a step-7 `grid` via (`r8_ground.tsv`) and carries 0.24 A of the servo GND return, the second largest (`fix2_dc_gnd.txt`). R7 `c872a3d3…`: GND_B fill is 0.150 mm from Q121.4, R121.1 / .2 and Q122.3, and the nearest GND via / track / pad to ACT copper is 0.425 mm (Q122.3, via (9.3, 107.6)). No GND pad lies within 0.5 mm of any ACT_GATE / ACT_DRV pad on either board. Records: R8_VALIDATION C12b #19 (l.379) gives only the generator cause as "why it stays"; the pyro-observation ACT_GATE row (l.492); "Open after fix pass 2" (l.517–519); fix2_handoff l.61 ("candidate for pass 3: give `make_ground.clearance` the actuator gate nets"). Each cites "ORDERING §5's 'RAW_ACT dead with the switch open' step", which ORDERING l.159 runs only "If the power switch is the pad arming device". The unconditional screen is ORDERING l.156's 20 power-switch cycles with the link in, with RAW_ACT below 1 V between cycles | Re-word C12b #19, the ACT_GATE observation row and the open item. State that the GND pours stand at 0.150 mm from the bare ACT_GATE / ACT_DRV pads, as on R7; that this class is REQUIREMENTS' accepted gate-net spacing outside the pyro block; and that ORDERING l.156's switch cycles screen it. Drop the via-only "candidate for pass 3". If the owner wants the class closed instead, the remedy is a GND keep-back from ACT_GATE / ACT_DRV copper on the pours (a zone clearance rule like rule D) plus `make_ground.clearance`. That remedy would need a DC_GND re-solve, since the via carries 0.24 A |
| R8P3-REQUIREMENTS-03 | Minor (worth fixing) | M2 owner acceptance; r8_plan §2 hard gate "route_check C1/C3/C4/C6 = 0, except owner-accepted inherent items (TXEN, A8)"; R8P2-REQUIREMENTS-03's fix (a complete decision list) | **The owner summary's "Agent decisions in this list that relax a plan gate or an owner criterion" omits D51.** D51 allowlists A2 / A3, the limiter's two detours, as inherent items beyond the plan's named TXEN and A8. D11 itself records that "the DoD allows only TXEN and A8 as inherent items", and A2 / A3 are why the hard gate stays "not met until the owner accepts" | R8_VALIDATION l.251–256 lists D5, D10, D12, D68, D70 and D87. D87 relaxes a family budget ratio for the same vias, not the allowlisting. The hard-gate row (l.62) names "D51, re-measured D87" and "D11's agreed fallback". R8_DECISIONS D11: "the DoD allows only TXEN and A8 as inherent items"; D51: "D11's agreed fallback (two allowlist entries)" | Add to l.251–256: "D51 (A2, A3: the GNSS limiter's two detours allowlisted as inherent, beyond the plan's TXEN and A8; D11's fallback)" |
| R8P3-REQUIREMENTS-04 | Minor (worth fixing) | Honest owner summary (M2); REQUIREMENTS M3's binding statement | **Two wording slips.** (a) C12 #13 says an ARM1_SENSE–GND bridge would "read disarmed: the safe direction". On the ground it is a hard refusal to fire, which is safe against ignition. It is also a false "disarmed" annunciation with the link in, which is not safe for whoever reads the annunciator. Pass 2 raised this as an observation; it was not acted on. (b) REQUIREMENTS M3's R8 sentence says the $106.00 run is "bound to the R8 BOM / CPL in … cost_check.json". The report binds the step-9 CPL, not the current one. ORDERING, STATUS, M3_R8 and R8_VALIDATION all say so; M3 does not | (a) R8_VALIDATION l.339 (C12 #13, 0.171 mm, vias (14.55, 97.55) / (13.95, 97.15)); pass2_requirements §8. (b) REQUIREMENTS l.76; `cost_check.json` `inputs_sha256`: CPL `d26572d3…`; current CPL `25cfed69…` (manifest) | (a) "(… reads disarmed with the link in: a ground fire is refused, but the annunciation is false; the ARM link is the physical indicator)". (b) Append to M3's R8 sentence: "(the report names the step-9 CPL, `d26572d3…`; the next `FAB_NET=1` run rebinds it)" |

### Severity notes

- **None of these is Major.** The CAD meets every requirement row; each finding is a record or procedure gap.
- **01** comes closest to safety. It leaves a firmware-dependent safety constraint without its bench check, while
  STATUS says the check exists. It stays Minor for three reasons:
  - the hazard needs a firmware fault, an armed link and a DFU jump together;
  - a DFU jump is a USB bench operation, and the armed bench gates run with USB unplugged;
  - the fix is a few lines in ORDERING.
- **02** saves the next fix pass from a generator change that cannot remove the class it targets.
- **03 and 04** are one-line edits.

## 6. Deviation list audit (R8_VALIDATION l.230–503)

| Part | Check | Result |
|---|---|---|
| Owner summary counts | 3 / 0 / 19 rows / 90 | Match the gate, `route.json` and the sweep. C's counts (23 / 29 / 32 + 4 / 12 / 26 / 17 / 2 / 4 / 1) match my sweep and scans |
| A (3) | Against `route.json` `allowed` | A1 = A8 (2.717 mm); A2 7.65 / 3.72; A3 6.20 / 2.61. A1 is still called A8 in the summary and hard gates (cosmetic, as in pass 2) |
| B | LEFTOVERS | Empty; gate OK |
| C1–C19 | Rows against the board | C11: 23 = sweep. C12: 29 net pairs, every gap equal to the sweep. C12b: 32 rows equal to the sweep (36 with the 4 fine). C13: 12 nets = sweep `routes`. C14: 26. C17: J122.3 / 6 / 9 / 12, the only FULL zone connections. C19 counts = `route.json`. C12b #19's framing is finding 02 |
| E (90) | Categories | 41 / 14 / 8 / 7 / 7 / 7 / 4 / 2: match |
| F | One line per M2 review category | Present for every category in M2's "What review checks". The short_hop key's 9 rows = 2 hops + C8's 7 power vias, as part F states |
| Decision list | Plan-gate relaxations | D5, D10, D12, D68, D70, D87 present; **D51 missing** (finding 03). D59 (C9: polylines instead of r5_maze) changes the method but keeps the plan's ≤ 1.3×, no-via constraint, so it is not a relaxation |
| Hard gates / scorecard misses | r8_plan §2 / §4 | Honest. 11 misses = S8, S9, S15, C1, C3, C2, P6, P7, P9, P10, R6b, each with its row |

## 7. Document consistency checked (no finding)

- **Identity.** Board `990c8040…`, netlist `0cc1ed69…`, BOM `be711876…` and CPL `25cfed69…` agree across STATUS,
  M3_R8, R8_VALIDATION, REQUIREMENTS (F4 / M2), AGENTS, MARGIN, the binding note and the manifest. Earlier hashes
  (`429b6db4…`, `6600ef94…`) appear only as labelled history.
- **Counts.**
  - Top: 89 placed (82 SMD + 2 SMA + 5 THT) plus 5 TP. Bottom: 130 placed plus 19 TP. 219 CPL rows.
  - 81 hidden designators, set-equal to M3_R8's list (R84 added by D102); 168 shown; 35 legends.
  - `r8_ground.tsv`: 193 vias, 201 rows. 272 tests / 17 suites; quality_audit 21.
- **Pours.** The ORDERING §7 sled row's bottom-pour boxes equal the board: RAW_ACT 0.5–16.5 × 81.8–108 and
  19.85–25.1 × 70.9–86.9; ACT_FET_S 9.6–14.78 × 97.6–106.63; BAT_IN 15.02–41.3 × 98.6–112.6. In2 BAT_IN is
  12.4–33.5 × 100.3–112.6, 229.6 mm², as D97 says.
- **ORDERING coordinates on `990c8040…`.** All match the board: C24.1 (25.33, 51.1), C15.1 (29.2, 49.82), TP122
  (20.45, 92.4), U4 (10.0, 53.8, B), C84 (37.0, 63.2), C121 (12.0, 83.8), L1 (42.7, 66.6), Q120 (16.38, 101.72),
  Q121 (8.0, 103.0), U9 (41.5, 85.5, B), R81 (39.6, 91.275, 90°, B), J1.2 (25.54, 110.4), U1.39 / R311.1 / R312.1.
- **DC figures.** F4, M3_R8, MARGIN, STATUS and ORDERING all equal the `fix2_dc_*` evidence.
- **Pyro observations.** Re-measured: BAT_ENABLE's 0.70 mm to R134; R81.1 1.825 mm to J121.1 (bare to bare); Q120.9
  0.180 mm to the BAT_ENABLE via.

## 8. Observations (not findings)

- **Commit precondition.** STATUS and R8_VALIDATION ask the owner to commit or tag the generator state "before review
  pass 3". The worktree is still uncommitted (HEAD `431025d`), so this pass reviews the state identified by
  `990c8040…`, `fix2_baseline_sha256.txt` and `fix2_generators.diff`. This is the build-integrity reviewer's subject
  (R8P2-INTEGRITY-03).
- **"Not removed yet" items.** r8_plan §4's stop rule asks each remaining Minor item to have "a measured cause that
  cannot be removed without a priority-1 cost". Several listed items do not claim that:
  - C12b #3, #11, #12, #18, #20, #21 are marked "not removed yet";
  - C11 has 4 rows with a found but rejected redraw;
  - C19 says up to 71 instances are "not removed yet" beyond the one-segment search.

  Each row says so honestly, and the owner's standing rule (record Minors, don't rework) governs. The owner summary
  could still give one count of "not removed yet" items beside "cannot be removed", since that is what its "accept, or
  send back for more work" question turns on.
- **D97's wording.** D97 says the In2 BAT_IN island now ends "where the outer BAT_IN pours do" (x ≤ 33.5). The F.Cu
  BAT_IN pour does end there, but the B.Cu pour reaches x 41.3 to feed U9's lane. The effect is as recorded: the trimmed
  area carried no through current.
- **U4's body outline.** The pad geometry suggests the 3.0 mm side lies along board x: 4-pad columns at x ± 1.21 and
  3-pad rows at y ± 0.96, both 0.29 mm inside a 3.0 × 2.5 mm body. Inference: ST's drawing is not read here. In that
  orientation no GND_B fill enters the body. In pass 2's 2.5 × 3.0 orientation a 0.05 mm² sliver did. P3 passes either
  way.

## Appendix A: methods (scripts in the session scratchpad, deleted after the pass)

- **Gaps.** For each pair of items:
  - shapes from `GetEffectiveShape(layer)` for pads (THT inner layers only where flashed), tracks and vias, or
    `GetFilledPolysList(layer)` for zones;
  - the gap bisected with `SHAPE.Collide` to about 0.2 µm.

  Pairs measured:
  - ACT_GATE / ACT_DRV against GND (items and fills), on R8 and on a scratch copy of R7 `c872a3d3…`;
  - BAT_ENABLE against BAT_IN, ACT_FET_S, RAW_ACT, pyro, ACT_EN / ACT_DRV, RAW_PROTECTED and BAT_SW_RETURN;
  - PYRO1_OUT against BAT_IN / ACT_FET_S;
  - PYRO1_CONT_MID against GND / PYRO1_CONT (R7 C15 #1 / #6);
  - different-part pad pairs under 0.2 mm on every copper layer.
- **MEMS bodies.** Nominal rectangles centred on the footprint, in both orientations (U4 2.5 × 3.0 mm, U5
  5.0 × 3.0 mm). Measured inside them on B.Cu: tracks, vias and GND fill, with the pads subtracted.
- **Inventory.** Footprints per side, `IsDNP`, `Reference().IsVisible()`, and silk text height / stroke on F / B.SilkS.
  THT GND pads read by `GetLocalZoneConnection()`; zone clearances by `GetLocalClearance()`. TP / J2 pads tested
  against via holes and rings.
- **Netlist.** `schematic.net.xml` parsed for U1's F10 pins and the pull resistors (R127, R311, R310, R312, R307).
- **Tools (read-only).** `tools/check.sh`; `step9/m2_sweep.py --json` to the scratchpad; the 17 test suites and
  quality_audit; `fab_manifest.py` (verify); `jlc_orient.py --verify-cpl`; `route_check.py --profile r7` on the R7
  copy.
