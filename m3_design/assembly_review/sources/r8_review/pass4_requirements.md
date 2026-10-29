# R8 review pass 4: requirements traceability

Reviewer dimension: requirements traceability. I checked every REQUIREMENTS row (F1–F10, P1–P3, M1–M3, R8 acceptance)
against the CAD, the gate and the records on fix pass 3's final board. I also checked:
- the R8 pin contract against F10, R8_DECISIONS D2–D6 / D6.8 and the binding note;
- the consistency of REQUIREMENTS, STATUS, ORDERING, MARGIN_PRESCRIPTION, AGENTS, M3_R8, R8_VALIDATION and README;
- whether the R8 deviation list is complete and honest after fix pass 3.

- **Board:** `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
  `c84f00b88f5fb9409de40f33b2d51a48fb29fb66c386c869b7f93ea791e37c54`; netlist `0cc1ed692fb99dd2…` (unchanged since
  pass 1). I checked the hash before my runs, and every pcbnew measurement ran on a scratch copy with that hash.
- **Read-only:** this report is the only repository file I changed. The board was never saved. `git status --porcelain`
  was identical before and after my runs, and no repository file had a newer mtime than my start marker. Scripts, board
  copies and outputs lived in the session scratchpad (`p4req/`) and were deleted afterwards.
- **Labels:** "Inference" marks anything not measured and not taken from a maker document.

**Result: 0 Critical, 0 Major, 4 Minor (all worth fixing, all record-only).** Every pass-3 finding in this dimension is
closed. Fix pass 3's three copper edits break no requirement row. Every figure it claims re-measures equal on
`c84f00b8…`, and the M2 sweep reproduces `fix3_m2_sweep.json` key for key. The four findings are record gaps:
- **01:** the new bootloader pyro-gate check sits in ORDERING §5's RF bullet. It is outside the pyro-gate list that is
  "repeated after any firmware change", although the property it checks is set by firmware. It also points to the static
  gate "below" when that gate is above.
- **02:** three records call the pull-pin a "launch detect". F9 and FMEA F-7 make it an advisory pad witness that is
  ignored after launch.
- **03:** six figures and labels went stale or ambiguous in fix pass 3.
- **04:** README and ORDERING state R8's review status differently from STATUS / AGENTS / R8_VALIDATION.

## 1. What I ran

| Run | Result |
|---|---|
| `tools/check.sh` (KiCad 10.0.6) | **Exit 0.** DRC 0, unconnected 0, parity 0, ERC 0. Metadata / 3D audit OK; 0 silkscreen points outside the outline; `check_r8` OK; route_check r8: 0 failing, 3 allowlisted, 0 stale, 0 leftovers, 0 removable (22 bump windows). `check_actuators` OK. `fit_check` OK (J9 mated 0.03 mm, C84 1.37 mm, R12.1 4.452 mm from (4, 64), TP30.1 5.008 mm) |
| `check_r8` evidence | battery_pyro 1.089 mm (ACT_FET_S to J124.1); via_paste 709 pairs, nearest ring 0.025 mm (C90.1); inner_power_pyro 2.65 mm; terminal_legends 10 / 10 nearest their own pin. Loader pins as D5 (PA2, PA11 / PA12, PB6, PB9, PB10, PB14; PA6 / PA8 / PA9 / PC9 / PC11 / PE13 NC). Fence: 25 vias, openings 2.015 / 2.60 / 2.10 / 2.05 mm. rf_stitching 3.90 / 2.65 / 1.55 / 1.55 mm; strip GND reach F 3.04 / B 3.49 mm |
| route_check `route.json` | 93 instances: 3 allowed (PYRO1_GATE in TP122; GNSS_LNA_EN 2.06×; GNSS_VCC_RF 2.37×) and 90 information (pad_end_offcentre 41, width_change_junction 14, passes_through_pad 8, segment_inside_pad 7, u_turn 7, power_via_no_gnd 7, extra_bends 4, short_layer_hop 2). This matches part E, C19 and the owner summary |
| `step9/m2_sweep.py` on `c84f00b8…` | 23 chain detours; 53 adjacency rows giving 28 net pairs, 9 of them at 0.150 mm; 33 pad rows (4 fine-pitch, own part); 28 route rows; 26 via folds; 1 via step; 2 poured hops; 9 short_hop rows; 0 pad-edge ends; bumps_all 1 candidate in 7 windows. margin_free: 29 windows, 1 bump, 4 redraws. **Every key equals the recorded `step9/evidence/fix3_m2_sweep.json`.** C12's 28 rows equal the sweep pair by pair, and C12b's 29 rows row by row |
| Tests | 17 suites, 272 tests OK (KiCad Python, run after the fab step as the handoff says); quality_audit 21 OK under both Pythons |
| `fab_manifest.py` / `jlc_orient --verify-cpl` (on a copy) | Manifest OK, 5 outputs, bound to `c84f00b8…`. BOM `be711876…`; CPL `ef90bfa1…`, R172's row `30.6500mm,-48.1000mm,Bottom,90`. Verify: 85 top + 126 bottom rows, worst 0.491 mm, 8 placement-only, 219 rows |
| `cost_check.json` | $106 / 52 extended codes, `checked_utc 2026-10-19T23:51:04Z`, CPL `d26572d3…` (step 9). Not re-run (needs the network); REQUIREMENTS M3 now states the stale binding |
| Evidence bindings | `step9/r8_binding_note.json` board `c84f00b8…`, netlist `0cc1ed69…`, pin table `bd4687a8…` (= `pin_table.tsv`). All 15 `step9/evidence/fix3_*` files start with or carry `c84f00b8…` |
| My pcbnew scans (Appendix A) | Gaps of every item of the five nets fix pass 3 touched (and R172's pads) to all foreign copper on each layer. Placement inventory, hidden designators, U1 pin map, R172's courtyard to the ARM1_SENSE_MCU via, J122's pad extents against the stall-test window, and F9's pad-edge distances. Netlist pulls, BOOT0 and J2 |

## 2. Closure of pass 3 in this dimension (`pass3_requirements.md`, board `990c8040…`)

| Pass-3 ID | Item | On `c84f00b8…` |
|---|---|---|
| R8P3-REQUIREMENTS-01 | ORDERING §5 lacked three bench checks STATUS attributes to it | **Closed in substance.** ORDERING l.161 adds the bootloader pyro gate (TP122 below 0.1 V, ARM link out; then the static gate in the bootloader). l.167 adds the camera-supply load step: CAM_5V at J9.1 (J9.1 = CAM_5V, J9.2 = GND in the netlist), 0.1 → 1 → 0.1 A. l.168 adds the IMU signs, consistent with M3_R8 "IMU axis map" and the binding note. STATUS l.99–104 now matches. Where the bootloader step sits is finding 01 |
| R8P3-REQUIREMENTS-02 | ACT_GATE item misdescribed; conditional screen cited | **Closed.** C12b #18, the pyro-observation ACT_GATE row, M3_R8 l.370–381 and D109 give the pour at 0.151 mm from the five bare pads (I measured 0.1505 mm on the pours beside every touched net, the same zone clearance), and name the always-run screens: l.156's 20 switch cycles and l.170's hot RAW_ACT check. `fix2_handoff.md` l.61–62 carries a marked correction |
| R8P3-REQUIREMENTS-03 | D51 missing from the owner summary's decision list | **Closed** (R8_VALIDATION l.310–311) |
| R8P3-REQUIREMENTS-04 | (a) C12 #13 "safe direction"; (b) M3's CPL binding | **Closed:** (a) C12 #12, l.398; (b) REQUIREMENTS l.76 names `d26572d3…` and the rebinding run |
| Pass-3 observation: "not removed yet" count | Owner summary | **Acted on:** "Removable or not" paragraph (l.302–307) |
| Pass-3 observation: D97 wording | B.Cu BAT_IN pour reaches x 41.3 | **Acted on** (D97 l.2047–2048) |

## 3. Requirement walk on `c84f00b8…`

Verdicts:
- **Pass:** shown in the CAD, the gate or the fab files.
- **Partial:** the CAD part passes and the rest is open.
- **NV:** needs the bench, a flight or firmware.

| Row | Verdict | Evidence / remark |
|---|---|---|
| Sources (one CH1, isolated Blue Jay, 4 servos, on-board MAX-F10S / E22, uplink cannot arm) | Pass | `check_actuators` OK (SHA asserted by `check_r8`); netlist unchanged |
| F1–F3, F5 | Pass (parts), NV | U4 bottom, rotation 0, (10.0, 53.8); binding note's IMU block: lever arm x −13.0 mm |
| F4 | Pass (CAD, calc), NV | `fix3_dc_*.txt` bound to `c84f00b8…`: 1.45 / 0.45 / 0.18 mΩ; necks 5.94 / 6.99 / 4.97 mm; 17.5 / 14.5 / 21.4 °C; GND 0.69 mΩ. These equal F4, M3_R8, MARGIN and STATUS. Stall-test window y 83.35–86.25 is 3.04 mm from the nearest J122 pad (pads end at y 80.31, measured), as ORDERING l.166 states |
| F6 | Pass (CAD), NV | C24 on NRST; circuit unchanged |
| F7 | Pass (CAD), NV | Q121 → J124.2 0.44 mΩ (M3_R8 supply table; RAW_ACT copper untouched) |
| F8 | Pass (CAD), NV | DRC 0 under the unchanged `m3.kicad_dru` (nine pyro rules A, A2, B–H). battery_pyro 1.089 mm. R165's BAT_ENABLE via is now 0.5 / 0.3 mm, 0.230 mm from Q120.9 (measured), and BAT_ENABLE's nearest BAT_IN copper is U9.1's own pitch, 0.200 mm. The bootloader state now has a bench gate; where it is listed is finding 01 |
| F9 | Pass (CAD), NV | Protection parts: edge 1.906 (R167) … 7.817 mm (C96); centre 3.86 … 10.6 mm (measured, = M3_R8 / STATUS / D76). The pull-pin is "an advisory pad-arming witness … the pin never starts the roll reference, the control window or flight logging"; three records say otherwise (finding 02) |
| F10 | Pass (CAD), NV | Pin contract (section 4); strip rigid (12 / 12 digests); fence and stitching as F10 quotes. D6.8's new order is consistent across F10, D6.8, the binding note, M3_R8 and ORDERING |
| P1 | Pass | 46 × 118 mm (fit_check) |
| P2 | Pass (CAD), NV | Five supports; R12.1 4.452 mm; tie path unchanged. C10 open |
| P3 | Pass | Fix pass 3's copper lies away from U4 / U5 (the moved cover via is at (29.125, 32.625)); coating and staking lists unchanged |
| M1 | Pass, except U4 stock | CPL verify as above; stock not re-run |
| M2 (rules, via-in-pad, silk) | Pass | DRC 0; TP122 the only in-pad via; silk gate OK; 81 hidden designators, set-equal to M3_R8's list |
| M2 (clean routing, deviation list) | **Partial** | The list matches the gate and the sweep (section 6). Owner acceptance is open. Findings 02 and 03 are record fixes in it |
| M3 | Pass (step-8 run) | $106.00, 52 / 52; BOM unchanged; the stale CPL binding is now stated in M3 itself |
| R8 acceptance | Not met (as recorded) | Owner acceptance, U4 consignment and the 24 h cost run are open. The review-count clause is met on reviewed boards, and this pass reviews the final one. Status wording: finding 04 |

**Fix pass 3's copper against the requirements (measured).**
- CAM_PWR_EN–USB_LIMITED: 0.2000 mm (B.Cu, at the (28.25, 36.8) corner).
- R172.1 and R172.2 to USB_LIMITED: 0.2301 mm.
- RAW_ACT_SENSE (x 30.65) to USB_LIMITED's hop via (31.25, 55.3): 0.2000 mm, as D106 states.
- USB_LIMITED to the ARM1_SENSE_MCU via: 0.2000 mm (unchanged run).
- R172's courtyard to the ARM1_SENSE_MCU via: 0.685 mm (= `L10_EXCEPT`, C7).
- Every pair under 0.2 mm on these nets is either a pour at the 0.15 mm zone clearance or one of C12's existing rows (#1, #2).
- The old cover via (28.875, 32.875) is gone and the new one (29.125, 32.625) is present.

No new pair under 0.2 mm, and no requirement row affected.

## 4. R8 pin contract against F10 and the decisions

- **The board's U1 pads agree with F10 and the netlist** (read from `m3.kicad_pcb` pads and `schematic.net.xml`):

  | Pin | Net / pull |
  |---|---|
  | U1.3 PE4 | PYRO1_GATE_N (R126 220 Ω to PYRO1_GATE; R127 1 kΩ to GND) |
  | U1.46 / .47 | RADIO_SCK_MCU (R313 33 Ω) / RADIO_NSS (R310 100 kΩ to 3V3) |
  | U1.53 / .54 | RADIO_MOSI_MCU (R315 33 Ω) / RADIO_MISO_MCU |
  | U1.55 / .56 | RADIO_BUSY / RADIO_RXEN (R312 100 kΩ to GND) |
  | U1.39 PE9 | RADIO_NRST (R311 2 kΩ to GND) |
  | U1.45 PE15 | RADIO_DIO1 |
  | U1.61 / .62 | GNSS_RESET_N (direct to U30.9, no capacitor) / GNSS_TP_MCU (R307 1 kΩ, no pull-down) |
  | U1.63 / .64 | GNSS UART (R306 / R305 220 Ω) |
  | U1.37 / .38 | CAM_MCU_RX / CAM_MCU_TX |
  | U1.7 / .65 | BUZZ_DRV / VBUS_SENSE |
  | U1.94 BOOT0 | R5 10 kΩ to GND |
  | J2.6 | NC |

- **D6.8 against GPIOE's other pins.** A GPIOE reset in step 3 returns all of GPIOE to analog. The other GPIOE pins are:
  - PE2 QSPI_IO2;
  - PE3 and PE13 NC;
  - PE7 / PE8, the camera UART behind U12;
  - PE11 CAM_FAULT_N;
  - PE12 CAM_PWR_EN, which R74 1 kΩ / R75 10 kΩ to GND then hold off;
  - PE15 DIO1;
  - PE1 IMU_INT1.

  None needs a driven state in the bootloader. No contradiction found.
- **Records agree.** The binding note is regenerated on `c84f00b8…`, and its constraint 12 states the new order. F10,
  D6.8, M3_R8 "Firmware" and ORDERING l.161 state the same order:
  1. drive PE4 low;
  2. put the SX1262 to sleep and drive PE9 low;
  3. reset GPIOE last, or keep PE4 low and return PE9 to analog.
- **The pin table is unchanged** (SHA-256 `bd4687a8…`), and `check_r8` asserts U1's 100 pins against it.

## 5. Findings

| ID | Sev. | Requirement | Finding | Evidence | Fix |
|---|---|---|---|---|---|
| R8P4-REQUIREMENTS-01 | Minor (worth fixing) | F8 ("nothing fires … while armed with the MCU … booting or idle (bench gates …, ORDERING §5)"); D6.8 (a firmware-defined jump preparation); ORDERING l.153 ("Pyro gates … run with the flight firmware image (record its hash) and repeated after any firmware change") | **The bootloader pyro-gate check fix pass 3 added is outside the pyro-gate list that firmware changes re-trigger, and it points the wrong way.** What it verifies (PE4 low before the jump, D6.8) is set by the firmware's jump code, and every later re-flash is planned by that DFU jump (ORDERING l.145). Yet the check sits as a clause of the RF bullet's radio-reset step (l.161), which runs "before any flight", not in the l.153–159 list that is re-run after any firmware change. A later firmware revision can therefore change the jump's preparation without the procedure requiring the bootloader gate again. The step also says "run the static pyro gate below", but the static gate is l.154, above it. And it does not confirm the board is still in the bootloader after USB is unplugged ("the bootloader keeps running on the bench supply, Inference"). If the MCU restarted, the gate would silently test the application instead | ORDERING l.153 (pyro-gate list, firmware-repeat rule), l.154 (static gate), l.161 ("…run the static pyro gate below once with the board in the bootloader"), l.145 (re-flash by USB DFU via the firmware's jump); R8_DECISIONS D6.8 ("Bench check: ORDERING §5's bootloader repeat of the radio-reset step also reads PYRO1_GATE at TP122 and runs the static pyro gate there") | Add a sub-bullet to the l.153 pyro-gate list: "**Bootloader:** after the firmware's jump (D6.8), ARM link out, PYRO1_GATE at TP122 below 0.1 V; unplug USB, confirm the board is still in the bootloader (RADIO_NRST at R311.1 still below 0.66 V; Inference: the application releases NRST when it starts the radio, binding constraint 2), then run the static gate armed". Have l.161 point to it, and change "below" to "above". D6.8's bench sentence then names the pyro-gate list |
| R8P4-REQUIREMENTS-02 | Minor (worth fixing) | F9 ("Pull-pin input: an advisory pad-arming witness (FMEA F-7), ignored after launch; launch itself is detected by the accelerometer (FMEA F-6), so the pin never starts the roll reference, the control window or flight logging"); M2 (each deviation row with what it does); FMEA_REDUNDANCY F-7 / V-12 | **Three records give the pull-pin a launch-detect role that F9 removed.** C12b #3's consequence column says a Q123.3–PULLPIN bridge would cause "false launch detects while the buzzer sounds". D101 says an open J123.2 joint "would read as a pulled pin, a false launch detect". AGENTS §1's block row is titled "Pull-pin (launch detect), buzzer". Under F9 / F-7 such a fault gives a false or toggling advisory witness: it can disturb the ground PAD_ARMED → READY gate or raise a fault code, and it is ignored after launch. The board side is right (BUZZ_OUT swings 0–3.3 V: LS120.1 on 3V3, Q123 drain; PULLPIN to PC14 with R161 10 kΩ to 3V3, R160 1 kΩ, D122 clamp: no overvoltage). The owner's acceptance row, however, states a consequence the requirements exclude | R8_VALIDATION l.422 (C12b #3); R8_DECISIONS l.2100–2101 (D101); AGENTS.md l.19; REQUIREMENTS l.59 (F9); FMEA_REDUNDANCY l.64 (V-12), l.361 (F-7); netlist: BUZZ_OUT = {D123.2, LS120.2, Q123.3}, LS120.1 = 3V3; PULLPIN = {C160.1, D122.3, R160.2, R161.2, U1.8 PC14} | C12b #3: "PULLPIN follows the buzzer drain: a false or toggling pull-pin witness (advisory only, F9 / FMEA F-7: it can upset the ground PAD_ARMED → READY gate, never a launch detect); no fire path". D101: "…would read as a pulled pin (a false advisory witness, F9)". AGENTS: "Pull-pin (advisory pad witness, F9), buzzer" |
| R8P4-REQUIREMENTS-03 | Minor (worth fixing) | M2 (the deviation list "bound to the final board's SHA-256"); records match the board (AGENTS §3) | **Six figures or labels went stale or ambiguous in fix pass 3.** (a) M3_R8 l.54 gives "1499.6 mm of signal track … 1382.0 mm of it drawn by the nine planned family modules" as current. l.148 of the same file says 1497.6 mm and its family table totals 1379.9 mm (fix pass 3 shortened CAM_PWR_EN 1.98 mm). (b) R8_VALIDATION's scorecard column is headed "R8 (fix pass 2)" but holds fix pass 3's values, with fix pass 2's in parentheses. (c) C4 gives P6 = 1752.5 mm; the scorecard row and `fix3_scorecard.md` give 1752.2. (d) The owner summary's C row says "29 close pad / copper pairs (4 fine-pitch own-part pairs counted)". C12 and part F say 33 pairs, 29 listed + 4 counted. (e) REQUIREMENTS M2's J2 sentence stops at "fix passes 1 and 2 moved no via near J2". (f) ORDERING §4's CPL verification is labelled "(R8 board, step 8)"; fix pass 3 re-ran it with the same figures | M3_R8 l.54 vs l.145–148; R8_VALIDATION l.83, l.85 (1497.6 (1499.6)), l.98 (P6 1752.2 (1752.5)), l.336 (C4 "1752.5 mm"), l.296, l.344, l.515; `fix3_scorecard.md` (S1 1497.6, P6 1752.2); REQUIREMENTS l.75; ORDERING l.107; fix3_handoff l.28–29 | (a) "1497.6 mm of signal track (… fix pass 2 1499.6) … 1379.9 mm of it drawn by the nine family modules". (b) Header "R8 (fix pass 3)". (c) "1752.2 mm (… fix pass 2 1752.5 …)". (d) "33 close pad / copper pairs (29 listed, 4 fine-pitch own-part escapes counted)". (e) "fix passes 1–3 moved no via near J2". (f) "(R8 board, fix pass 3; the same figures since step 8)" |
| R8P4-REQUIREMENTS-04 | Minor (worth fixing) | REQUIREMENTS "R8 acceptance" (two consecutive clean passes); honest status records (AGENTS §3 "stating clearly what was verified and what was not") | **README and ORDERING state R8's review status differently from STATUS, AGENTS and R8_VALIDATION.** README says "two consecutive independent review passes found no Critical or Major" and leaves out that fix pass 3's final board `c84f00b8…` was not itself reviewed. ORDERING's opening says "an independent review loop … [is] open". STATUS l.12–14, AGENTS l.22 and R8_VALIDATION l.567–570 say the count condition is met on the reviewed boards and the final board's edits are unreviewed, with a re-check offered. This pass is that re-check, so all five need one consistent sentence after it | README l.5; ORDERING l.3; STATUS l.12–16; AGENTS l.22 (manufacturing-package row); R8_VALIDATION l.3–13, l.143, l.567–570 | After pass 4, one sentence in all five records: "passes 2 and 3 found no Critical or Major; pass 4 re-checked fix pass 3's board `c84f00b8…` (result); still open: the owner's acceptance of the deviation list, U4 consigned, JLC's tab acceptance and a cost and stock run within 24 h" |

### Severity notes

- **None is Major.** The CAD meets every requirement row, and fix pass 3's copper changes none of them.
- **01** comes closest to safety. It is Minor because:
  - the hazard needs a firmware fault in the jump code, an armed link and a DFU jump together;
  - a DFU jump is a USB bench operation, and armed gates run with USB unplugged;
  - the fix is a few lines in ORDERING.
- **02, 03 and 04** are wording. 02 matters because an owner's acceptance row should not state a consequence the
  requirements exclude.

## 6. Deviation list audit (R8_VALIDATION l.281–563)

| Part | Check | Result |
|---|---|---|
| Owner summary counts | 3 / 0 / 20 rows / 90 | Match the gate, `route.json` and the sweep. The pad-pair count's wording is finding 03(d) |
| A (3) | Against `route.json` `allowed` | A1 = PYRO1_GATE in TP122; A2 GNSS_LNA_EN 2.06×; A3 GNSS_VCC_RF 2.37×. D51 is now in the decision list |
| B | LEFTOVERS | Empty; gate OK |
| C1–C20 | Rows against the board | C5: RAW_ACT_SENSE_MCU 3.62× (0.71 mm MST after R172's move). C7: R172 0.685 mm (measured). C11: 23 rows equal to the sweep, CAM_PWR_EN 20.146 / 15.945 mm, USB_LIMITED (19.4, 37.3)–(29.95, 54.0). C12: 28 net pairs, 9 at 0.150 mm, every gap equal to the sweep. C12b: 29 rows equal to the sweep row for row. C13: 12 nets. C14: 26. C19 counts = `route.json`. C20 recorded. C4's figure is finding 03(c) |
| E (90) | Categories | 41 / 14 / 8 / 7 / 7 / 7 / 4 / 2: match |
| F | One line per M2 review category | Present for every category, plus margin_free (29 windows, 1 bump = the BAT_ENABLE false positive, 4 redraws = C11 #20–#23), reproduced |
| Decision list | Plan-gate relaxations | D5, D51, D10, D12, D68, D70, D87. Fix pass 3's D106–D109 relax nothing: D107 tightens the camera budget 1.55 → 1.40, and D106 tightens `L10_EXCEPT` 0.635 → 0.685 mm |
| Honesty | "Not removed yet" items | Named with a count (C12b #3, #11 / #12, C11's four "found", up to 71 C19 instances; C20 cosmetic). Fix pass 3's three removals are stated |
| Consequence column | C12 / C12b "a short would …" | Correct, except C12b #3 (finding 02) |

## 7. Document consistency checked (no finding)

- **Identity.** Board `c84f00b8…`, netlist `0cc1ed69…`, BOM `be711876…` and CPL `ef90bfa1…` agree across STATUS,
  M3_R8, R8_VALIDATION, REQUIREMENTS (F4 / M2), AGENTS, MARGIN, the binding note, the manifest and every `fix3_*`
  evidence file. `990c8040…` appears only as labelled history.
- **Decisions.** D1–D109 are cited consistently (STATUS l.26, M3_R8 l.6, R8_VALIDATION l.15).
- **Placement inventory.** 249 footprints:
  - top: 94 non-TP (89 placed + 4 DNP + J2's pattern) plus 5 TP;
  - bottom: 131 non-TP (130 + C304) plus 19 TP;
  - DNP C303 / C304 / C305 / C313 / C314; 219 CPL rows.

  This matches ORDERING §4.
- **Hidden designators.** 81, set-equal to M3_R8's list.
- **Bench list.** STATUS l.99–104's bench list now maps one-to-one onto ORDERING §5:
  - hot-plug at U9 IN, l.170;
  - camera load step, l.167;
  - IMU signs, l.168;
  - tap check, l.169;
  - stall test, l.166;
  - turn-off with the link in, l.156;
  - C/N0 per band, l.164;
  - bootloader reset and pyro gate, l.161.
- **F9 pad-edge figures.** R167 1.906, D8 3.80, C95 5.339, C80 5.703, R166 5.75, C89 6.702, C96 7.817 mm (measured).
  These equal M3_R8 l.485.
- **MARGIN_PRESCRIPTION's R8 block.** Bound to `c84f00b8…`; its figures equal the DC evidence.

## 8. Observations (not findings)

- **Commit precondition.** The worktree is still uncommitted (HEAD `431025d`). This pass reviews the state identified by
  `c84f00b8…`, `fix3_baseline_sha256.txt` and `fix3_generators.diff`. That is the build-integrity reviewer's subject
  (R8P3-INTEGRITY-04, owner action).
- **D5's PA2 (SERVO3_MCU) as USART2_TX in the ROM bootloader.** In the bootloader the servo 3 line can sit at the UART's
  idle high instead of F6's "defined low". It is inside D5's owner-accepted-on-acceptance list. I note it only because
  the new bootloader bench step (finding 01) is a natural place to also observe servo 3 in the bootloader (a servo should
  hold or go limp, not move; Inference).

## Appendix A: methods (scripts in the session scratchpad, deleted after the pass)

- **Gaps.** For each item of USB_LIMITED, CAM_PWR_EN, RAW_ACT_SENSE, RAW_ACT_SENSE_MCU and BAT_ENABLE, and for R172's
  pads, I compared every different-net track, via, flashed pad and zone fill on each copper layer. Shapes came from
  `GetEffectiveShape(layer)` and `GetFilledPolysList(layer)`, and each gap was bisected with `SHAPE.Collide` to 0.2 µm.
- **Other pcbnew reads.** BAT_ENABLE via sizes; step 7's moved cover via; R172's position, and its B.CrtYd against the
  ARM1_SENSE_MCU via; footprint sides, `IsDNP` and `Reference().IsVisible()`. U1's pads for the F10 pins. J122's pad
  bounding boxes, and a rectangle x 20.25–21.8, y 83.35–86.25 against J122's F.Cu pad shapes. J1.1's B.Cu shape against
  each protection part's pads.
- **Netlist.** `schematic.net.xml` parsed for the pulls (R5, R74 / R75, R126–R128, R305–R307, R310–R313, R315), BOOT0,
  J2, J9, TP122, C24, C15, and the BUZZ_OUT / PULLPIN nets.
- **Tools (read-only).** `tools/check.sh`; `step9/m2_sweep.py --json` on the scratch copy, compared key by key with
  `fix3_m2_sweep.json`, and C12 / C12b parsed from R8_VALIDATION and compared with it. The 17 test suites and
  quality_audit; `fab_manifest.py` (verify); `jlc_orient.py --verify-cpl` on a copy of the CPL.
