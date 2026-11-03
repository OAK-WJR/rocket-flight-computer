# R8 review pass 2: requirements traceability

Reviewer dimension: requirements traceability. I checked every REQUIREMENTS row (F1–F10, P1–P3, M1–M3, R8 acceptance)
against the CAD, the gate and the records. I also checked the R8 pin contract against F10 and R8_DECISIONS, the
consistency of REQUIREMENTS, STATUS, ORDERING, MARGIN_PRESCRIPTION, AGENTS, M3_R8, R8_VALIDATION and README, and whether
the R8 deviation list is complete and honest after fix pass 1.

- **Board:** `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
  `6600ef9462b37ec58540e0dd7edd97577c3e778bda0d233d3c1dffc555ad5a8d`; netlist `0cc1ed69…`. I checked the hash before and
  after my runs.
- **Read-only:** no repository file changed except this report. The board was never saved, and `git status` was the same
  before and after. My scripts and outputs were in the session scratchpad and were deleted afterwards.
- **Labels:** Inference marks anything not measured and not taken from a maker document.

**Result: 0 Critical, 0 Major, 6 Minor.** Every pass-1 finding in this dimension is closed or properly dispositioned. The
pass-1 Major (R8P1-REQUIREMENTS-01) is closed: the deviation list now covers every M2 review category, and my own run of
the sweep reproduces its figures exactly. What remains is a scope gap inside the adjacency category (finding 01) and record
wording.

## 1. What I ran

| Run | Result |
|---|---|
| `tools/check.sh` (KiCad 10.0.6) | **exit 0**: DRC 0, unconnected 0, parity 0, ERC 0. Audit OK; silk inside the outline; `check_r8` OK (no issues, no notes). route_check r8: 0 failing, 3 allowlisted, 0 stale, 0 leftovers, 0 removable. `check_actuators` OK. `fit_check` OK (J9 mated 0.03 mm, C84 1.37 mm, R12.1 4.452 mm from (4, 64)) |
| `check_r8` evidence | battery_pyro 1.089 mm (ACT_FET_S to J124.1); via_paste 705 pairs, nearest 0.025 mm (C90.1); terminal_legends 10 of 10 nearest their own pin; loader pins per D5; fence 25 vias, openings 2.015 / 2.60 / 2.10 / 2.05 mm |
| route_check `route.json` | 96 instances = 3 allowed (A8, GNSS_LNA_EN 7.65 / 3.72 mm, GNSS_VCC_RF 6.20 / 2.61 mm) + 93 information (42 / 14 / 9 / 8 / 7 / 7 / 4 / 2). This matches part E |
| `step9/m2_sweep.py` on `6600ef94…` | 23 chain detours (17 critical, 6 non-critical; 19 no redraw, 4 found), 32 net pairs under 0.2 mm (14 at 0.150), 12 nets over their via need, 26 via folds, 1 via step, 2 poured hops, 1 bump candidate, 0 pad-edge ends. **Every category is identical to the recorded `step9/evidence/fix1_m2_sweep.json`** |
| Tests | 17 suites, 272 tests OK (KiCad Python); quality_audit 21 OK |
| `fab_manifest.py` / `jlc_orient --verify-cpl` | manifest OK, 5 outputs; CPL 85 top + 126 bottom rebuilt, worst 0.491 mm, 8 placement-only, 219 rows |
| `cost_check.json` / `stock_check.json` | $106.00, 52 extended, `checked_utc 2026-10-19T23:51:04Z` (stock 23:50:07Z); short U4. Not re-run (network); bound to the step-9 CPL, as the records say |
| DC evidence `step9/evidence/fix1_dc_*.txt` | each first line is `6600ef94…`. RAW_ACT 1.45 mΩ, 5.94 mm, 17.5 °C; BAT_IN 0.42 mΩ, 7.00 mm, 14.5 °C, vias over 0.5 A: **4**; ACT_FET_S 0.18 mΩ, 4.97 mm, 21.4 °C; GND 0.72 mΩ |
| My scans (pcbnew; Appendix A) | 249 footprints: 94 F / 131 B non-TP, TP 5 F / 19 B, 5 DNP. 80 hidden designators (equal to M3_R8's list), 169 shown. Terminal legend boxes. J2 nearest via 0.915 mm (NRST (0.8, 42.75)). Pours: GND ×4, RAW_ACT F/In2/B, BAT_IN F/In2/B, ACT_FET_S B, 3V3 In2. THT GND pads solid only at J122.3/6/9/12 and J123.2. No via inside the U4 / U5 courtyards. Part positions cited in ORDERING. **Pad-to-copper gaps (finding 01)** |
| Render | `r8_top.png` (fix pass 1) inspected for the terminal legends |

## 2. Closure of pass 1 in this dimension (`pass1_requirements.md`, board `429b6db4…`)

| Pass-1 ID | Item | On `6600ef94…` |
|---|---|---|
| R8P1-REQUIREMENTS-01 (Major) | Deviation list omitted whole M2 review categories | **Closed.** Part C has C11 (23 chain detours), C12 (32 net pairs), C13 (12 nets with extra vias), C14 (26 via folds), C15–C18. Part F gives a "swept" line for every category of M2's "What review checks". The owner summary is recounted. My sweep reproduces every count and row, and C11's per-class split (17 / 6) and C13's 12 nets match. **Residual:** the adjacency sweep covers track and via pairs only. Pad-to-copper gaps are not swept, although R7 C15 (whose convention C12 cites) listed them. See finding 01 |
| R8P1-REQUIREMENTS-02 | "Radio held in reset in the bootloader" rests on firmware | **Closed.** D6.8; binding note constraint 12 (board `6600ef94…`, pin table `bd4687a8…` = file); F10 text; ORDERING §5 RF step repeated in the bootloader |
| R8P1-REQUIREMENTS-03 | J1 legends read across neighbours | **Closed.** `check_r8.terminal_legends` passes with each legend nearest its own pin. J1's 2/3/4 now sit at y 116.8 over x 15.38 / 20.46 / 25.54. Smallest own-versus-next margin 0.48 mm ("1:BAT+", "2:RAW"; §8) |
| R8P1-REQUIREMENTS-04 | BAT_ENABLE crosses PYRO_BLOCK, unrecorded | **Closed.** M3_R8 corrected ("One signal net still crosses the block"). R8_VALIDATION "Pyro review observations" covers it. ORDERING §5 switch cycles now require the board to turn off with the link in |
| R8P1-REQUIREMENTS-05 | Stale facts | **Closed.** ORDERING l.161 PE9; l.147 "west of U1"; l.140 hole 0.84 / pads 1.32 mm (measured: hole x 1.334 Ø0.99 → 0.839; pad 1.715 − 0.394 → 1.32); 3.9–10.6 mm in M3_R8, STATUS, D76 |
| R8P1-REQUIREMENTS-06 | AGENTS one-pass gate | **Closed** (AGENTS l.22: two consecutive passes). It still omits the 24 h cost run (finding 06(b)) |
| R8P1-REQUIREMENTS-07 | STATUS R7 contradiction | **Closed** (pass-8 line, stale open item dropped) |
| R8P1-REQUIREMENTS-08 | README presented R4 | **Closed, with a regression:** the rewrite dropped the coupler bore (finding 05) |
| R8P1-REQUIREMENTS-09 | P2 premise, M2 poured nets | **Closed.** P2 points to C10. M2 names R8's pours (GND, 3V3, BAT_IN, RAW_ACT, ACT_FET_S), which equal the board's zones |
| R8P1-REQUIREMENTS-10 | Via-field currents | **Closed.** F4 / M3_R8: 0.86 A (RAW_ACT), 0.67 A (BAT_IN) = evidence. The MARGIN note miscounts BAT_IN's vias over 0.5 A (finding 06(a)) |
| Pass-1 §6 observation | C2 (93 vs ≤ 80) has no "cannot be removed" cause | **Not acted on**: finding 04 |

## 3. Requirement walk on `6600ef94…`

Verdicts: **Pass** (shown in the CAD, gate or fab files), **Partial** (the CAD part passes, the rest is open), **NV**
(needs the bench, flight or firmware).

| Row | Verdict | Evidence / remark |
|---|---|---|
| Sources (one CH1, isolated Blue Jay, 4 servos, on-board MAX-F10S / E22, uplink cannot arm) | Pass | `check_actuators` OK (SHA asserted by `check_r8`). Netlist unchanged since pass 1 (`0cc1ed69…`) |
| F1–F3, F5 | Pass (parts), NV | Circuit unchanged. U4 bottom, rotation 0, at (10.0, 53.8): lever arm x −13.0 mm, as the binding note says |
| F4 | Pass (CAD, calc), NV | Necks 5.94 / 7.00 / 4.97 mm, 17.5 / 14.5 / 21.4 °C, within D12. Via maxima 0.86 / 0.67 A. GND return 0.72 mΩ. The build holds the necks at 0.1 mm (D95). Stall test written in ORDERING §5 |
| F6 | Pass (CAD), NV | Unchanged circuit; C24 at (25.75, 51.1) on NRST |
| F7 | Pass (CAD), NV | RAW_ACT Q121 → J124.2 0.44 mΩ (M3_R8 supply table) |
| F8 | Pass (CAD), NV | DRC 0 under the unchanged `m3.kicad_dru`. ARM / IGN / BAT / CAM / GNSS / RADIO legends present. Terminal pin legends gated. Battery-live copper ≥ 1.0 mm from BUS / IGN (`battery_pyro`, not yet named in F8: finding 06(d)) |
| F9 | Pass (CAD), NV | Protection 3.9–10.6 mm from J1.1; C83 now beside U10 (D88); hot-plug model inputs unchanged (C83 / U9.5 entry only) |
| F10 | Pass (CAD), NV | Pin contract (section 4); strip rigid; fence ≤ 2.0 mm with openings ≤ 2.7 mm; F10 5 mm separation 5.94 mm; D6.8 recorded |
| P1 | Pass | 46 × 118 mm; parent VEHICLE stack row still names R7 (D84 proposed; correct while R7 is the revision to order) |
| P2 | Pass (CAD), NV | Five supports; nearest bottom pad 4.452 mm; tie path 2.2 mm (R150); C10 open |
| P3 | Pass | No via inside the U4 / U5 courtyards. Only pad escapes and inter-pad GND links enter the nominal bodies, plus a 0.05 mm² GND_B corner sliver at U4 (§8). Coating list unchanged |
| M1 | Pass, except U4 stock | Stock short U4 only. CPL verified (85 + 126, worst 0.491 mm). C83 stays bottom (B side, same part) |
| M2 (rules, via-in-pad, silk) | Pass | DRC 0; J2 nearest via 0.915 mm; via_paste gate; THT reliefs everywhere but the 5 pins in C17. The thermal-relief exception pointer in M2 still names only M3_R4 §2 (finding 06(c)) |
| M2 (clean routing, deviation list) | **Partial** | The list is complete in category but not in adjacency scope (finding 01). Owner acceptance open |
| M3 | Pass (on the step-9 run) | $106.00, 52 / 52; BOM unchanged; rerun within 24 h of ordering |
| R8 acceptance | Not met (as recorded) | Two clean passes (2 and 3), owner acceptance, U4 consignment, 24 h cost run. R8_VALIDATION words the pass condition wrongly in two places (finding 02) |

## 4. R8 pin contract against F10 and the decisions

- **Unchanged since pass 1.** The netlist SHA is unchanged (`0cc1ed69…`). `check_r8` asserts U1's map 100/100 against
  `pin_table.tsv` (`bd4687a8…`), and the binding note was regenerated on `6600ef94…`.
- **F10 text against the binding note.** These agree:
  - SPI2: PB10 SCK (AF5); PB11 NSS as a GPIO, R310 to 3V3; PB14 / PB15 with IOSWP;
  - BUSY on PD8, polled; NRST on PE9; DIO1 on PE15 (EXTI15); RXEN on PD9;
  - GNSS RESET_N on PD14; TIMEPULSE on PD15 (TIM4_CH4);
  - camera UART on UART7 (PE8 TX, PE7 RX);
  - EXTI9_5 shared by lines 5 / 6 / 8, EXTI15_10 by lines 11 / 14 / 15.
- **D6.8 (new constraint 12).** It names the only bootloader entry (a firmware jump; BOOT0 tied low, not on J2), and puts
  PE9 low then analog before the jump.
  - The alternative it names, resetting GPIOE through RCC_AHB4RSTR, also resets PE4 (PYRO1_GATE_N) and its lock. That is
    benign, because the gate's external pull-down holds it off. **Inference;** it is a binding note for the firmware, not
    a finding.
- **No contradiction found** between F10, D2–D6, the pin table and the board.

## 5. Findings

| ID | Sev. | Requirement | Finding | Evidence | Fix |
|---|---|---|---|---|---|
| R8P2-REQUIREMENTS-01 | Minor (worth fixing) | M2 (l.75): "What review checks: … adjacency on every net"; "every review-only residual is listed"; R8_VALIDATION C12 (l.223) says it follows "R7 C15's convention" | **C12's adjacency sweep leaves out pad-to-copper gaps, which R7 C15 listed. Two pairs R7 listed are dropped although the copper is unchanged.** `m2_sweep.items()` collects tracks and vias only, so no pad is measured. C12's scope line excludes only "pad-to-track gaps at fine-pitch pins" | (a) **34 pad / foreign-net pairs under 0.2 mm on parts of pitch > 0.65 mm** (Appendix B), most of them in R8-new copper. (b) **R7 C15 #1 and #6 are dropped from R8's list.** GND via (28.55, 87.21) – R129.1 (PYRO1_CONT_MID) 0.170 mm (R7: 0.170; "about 1.6 mA then flows through an armed igniter via R173"), and PYRO1_CONT via (28.4, 88.61) – R129.1 0.193 mm (R7: 0.193). Both are present on R8 at the same figures. (c) **Power-switch latch class at 0.18 mm, unrecorded anywhere.** Q120.9 (BAT_IN, bare, bottom) to the BAT_ENABLE via (16.6, 104.5) is 0.180 mm. R81.1 (BAT_ENABLE, bare) is 0.180 mm from the BAT_IN B.Cu track x 41.25, y 88.9–94.6, which also passes R81.2 (GND) at 0.170 mm. A bridge holds U9's EN at the pack voltage, so the switch cannot turn the board off (Inference). The pyro-observation table cites R7's BAT_IN at 0.35–0.40 mm from Q122 as this class's precedent. (d) Also: R166.1 / R166.2 both 0.175 mm from the RAW_PROTECTED track y 99.75; Q123.3 (BUZZ_OUT) 0.170 mm from the PULLPIN track x 14.23; U5.3 / U5.4 (GND) 0.175 mm from the 3V3A track y 57.85. All are DRC-legal (0.15 mm). None fires a channel or puts RAW_ACT on an MCU pin (Inference from the netlist) | Add pads to `m2_sweep.items()` (pad effective shape per copper layer, unflashed inner THT layers skipped; exclude only same-footprint pairs at fine pitch). Re-run, and add the pad pairs to C12 with what a short does, as R7 C15 did. At least restore R7 C15 #1 / #6 and give the BAT_ENABLE–BAT_IN pairs a row in "Pyro review observations" (latch class), with ORDERING §5's switch-off step named as the screen. Or, if pads stay out, say so in C12 and part F and drop "R7 C15's convention" |
| R8P2-REQUIREMENTS-02 | Minor (worth fixing) | REQUIREMENTS "R8 acceptance" (l.112: "two consecutive independent review passes … find no open Critical or Major"); r8_plan §4 | **R8_VALIDATION says one more clean pass is needed, but two are.** Pass 1 found a Major, so there is no clean pass yet, and passes 2 and 3 must both be clean | R8_VALIDATION l.7: "Not yet done: a second consecutive review pass with no Critical or Major". l.114 (Review history): "a second consecutive pass … is needed". Its own l.403–404 ("passes 2 and 3 at least"), STATUS l.10 / open items ("Review pass 2 (and 3 …)") and AGENTS l.22 state it correctly | l.7 and l.114: "two consecutive review passes with no Critical or Major (passes 2 and 3 at least, since pass 1 found a Major)" |
| R8P2-REQUIREMENTS-03 | Minor (worth fixing) | M2 owner acceptance; honest owner summary (R8P1-INTEGRITY-01's fix) | **The owner summary is inconsistent about which decisions relax plan gates.** (a) The hard-gates table calls D5 an "owner decision", while the summary lists it as an agent decision for the owner to accept. R8_DECISIONS' header says every decision was "taken on the owner's behalf". (b) D70 relaxes the plan's hard gate "S15 = S16 = 0" (r8_plan §2) by an exemption named in `check_r8.RIGID_IN2`, but it is missing from the summary's list (D5, D10, D12, D68, D87, D89). C1 does list the 3.4 mm link as a deviation row | R8_VALIDATION l.56: "(D5 relaxes it: owner decision)". l.189–194: "Agent decisions in this list that relax a plan gate or an owner criterion … D5 …". R8_DECISIONS l.3–4 and D70 (l.1662–1676) | l.56: "D5 relaxes it (agent decision on the owner's behalf; accepted with the list)". Add "D70 (S15: the rigid ARM1_SENSE In2 link exempt by name, C1)" to the summary's decision list |
| R8P2-REQUIREMENTS-04 | Minor (worth fixing) | r8_plan §4 stop rule: "each remaining miss … has a measured cause that cannot be removed without a priority-1 cost"; REQUIREMENTS "R8 acceptance" (cites §4) | **The C2 scorecard miss (93 information instances against ≤ 80) has no stated cause, as pass 1 observed.** R8_VALIDATION's scorecard row points to part E, which describes the categories but says nothing on removability. fix1_handoff says "each miss has its row in R8_VALIDATION part C", but C2 has none | R8_VALIDATION scorecard l.76 "no (E below)". Part E l.328–339: pad_end_offcentre 42 ("off the centre, by up to 0.85 mm … elsewhere ≤ 0.5 mm"), width_change_junction 14, segment_inside_pad 8, … with no removal reason. pass1_requirements §6 "Scorecard misses"; fix1_handoff l.61 | Add a part-C row for C2: per category, the measured reason it stays (forced by pad geometry or rigid copper), or "not removed yet" with the count that a redraw search could clear. Without it the stop rule cannot be met |
| R8P2-REQUIREMENTS-05 | Minor (worth fixing) | REQUIREMENTS P1 / P2 ("Fit the Ø50.8 mm coupler along the complete board length"); README as front page (AGENTS §1) | **The README fix (R8P1-REQUIREMENTS-08) dropped the coupler.** README now says the board "fits the main-section bay (Ø54.6 mm bore)". The design bore is the Ø50.8 mm coupler (VEHICLE: "Bore Ø50.8 up to joint + 120 (coupler), Ø54.6 above"; the board sits from about joint +80). `fit_check` uses radius 24.9 mm = 50.8 / 2 − 0.5 mm | README l.3; `git diff README.md`: the old text had "its aft ~70 mm sits inside the Ø50.8 mm coupler". `fit_check` output "radius 24.9 mm" | "(it fits the Ø50.8 mm coupler bore along its whole length; REQUIREMENTS P1 / P2)" |
| R8P2-REQUIREMENTS-06 | Minor (worth fixing) | Document consistency (AGENTS §1 / §3; REQUIREMENTS F8 / M2) | **Small record inconsistencies after fix pass 1** (each is a one-line edit) | (a) MARGIN_PRESCRIPTION l.196 says BAT_IN's vias have "5 over 0.5 A". `fix1_dc_bat.txt` l.9 says "vias over 0.5 A: 4" (0.67 / 0.62 / 0.61 / 0.55; the fifth is 0.49), and M3_R8 l.187 says 4. (b) AGENTS l.22's R8 ordering gate omits the cost and stock run within 24 h that REQUIREMENTS "R8 acceptance" and STATUS list. (c) REQUIREMENTS M2 (l.75) still says THT-GND relief exceptions are "listed in M3_R4 §2"; R8's are R8_VALIDATION C17 (J122.3/6/9/12, J123.2; measured: the only FULL overrides). (d) F8 (l.58) gives the ARM-break spacing as RAW_ACT-only; R8 also gates BAT_IN / ACT_FET_S ≥ 1.0 mm from BUS / IGN (`check_r8.battery_pyro`, D85), not named in the requirement. (e) ORDERING l.166 gives the stall pass criterion as "ACT_FET_S 21.5 °C"; F4, M3_R8 and the evidence say 21.4 °C. (f) STATUS l.5 "Last updated 2026-10-19", but l.10 "fix pass 1 (2026-10-20)" (the files are dated 2026-10-19 local); STATUS l.100 links R7's ordering to `docs/ORDERING.md`, which on this branch is R8's, one line after "its project and ORDERING live there" | (a) "4 over 0.5 A". (b) Add "and a cost and stock run within 24 h (REQUIREMENTS M3)". (c) "(exceptions listed in M3_R4 §2; R8: R8_VALIDATION C17)". (d) Append to F8's spacing list: "R8: BAT_IN and ACT_FET_S also ≥ 1.0 mm from bus and igniter copper on the same layer (`check_r8.battery_pyro`, D85)". (e) 21.4 °C. (f) One date convention; point the R7 link at branch `m3-assy-r7` |

### Severity notes

- **01 is Minor, not Major.**
  - The pass-1 Major was a categorical omission that included one of M2's named routing defects (needless detours).
  - Here the category is listed and swept, and its scope is stated (tracks and vias). The gap is pad-to-copper pairs
    inside that category.
  - The R7 precedent for missing adjacencies is P8-DOCS-01, rated Minor. Every pair is DRC-legal. None is a fire path.
  - It is worth fixing because owner acceptance should cover what the owner accepted on R7 (the two R129.1 pairs),
    because the BAT_ENABLE–BAT_IN latch pairs are recorded nowhere, and because the fix is a script edit and table rows.
- **02–06** are record wording, cheap and safe. 04 matters only for the stop rule.

## 6. Deviation list audit (R8_VALIDATION l.168–360)

| Part | Check | Result |
|---|---|---|
| Owner summary counts | 3 / 0 / 18 rows / 93 | Match the gate, `route.json` and the sweep. C's instance counts (23 / 32 / 12 / 26 / 17 / 2 / 5 / 1) match the sweep, `pour_pieces` (records) and my THT scan (5 FULL pins) |
| A (3) | Against `route.json` `allowed` | A1 = A8 (2.717 mm); A2 7.65 / 3.72; A3 6.20 / 2.61; reasons re-measured each run. Naming: part A numbers it A1, but the summary, hard gates and STATUS call it A8. Same item; cosmetic |
| B | LEFTOVERS | Empty; gate OK |
| C1–C18 | Rows against the board | C8 = route_check's 7 `power_via_no_gnd` (VBUS (7.95, 36.0) 2.061 since D88). C11 = sweep (23 rows, reasons and redraw status match). C12 = sweep (32 pairs) **but no pad pairs** (finding 01). C13 = sweep `routes` (12 nets). C14 = sweep (26 vias). C17 = my scan |
| E (93) | Categories | 42 / 14 / 9 / 8 / 7 / 7 / 4 / 2: match |
| F | One line per M2 review category | Present for every category of M2 l.75's "What review checks"; poured hops (2), via step (1) and the bump false positive carry location and reason in F |
| Hard gates | Against r8_plan §2 | Honest overall: route_check "not met until the owner accepts A1–A3"; the D5 row's "owner decision" is finding 03 |
| Scorecard misses | r8_plan §4 | S8 / S9, S15, C1 / C3, P6, P7, P9 / P10 and R6b carry causes. C2 does not (finding 04) |

## 7. Document consistency checked (no finding)

- **Board, netlist, BOM and CPL identity.** Board `6600ef94…`, netlist `0cc1ed69…`, BOM `be711876…` and CPL `c0ee08ae…`
  are consistent in STATUS, M3_R8, R8_VALIDATION, REQUIREMENTS (F4 / M2), ORDERING, AGENTS, the binding note and the
  manifest. ORDERING and M3 honestly say the cost reports name the step-9 CPL.
- **Counts.**
  - Top: 89 placed (82 SMD + 2 SMA + 5 THT) plus 5 TP. Bottom: 130 placed plus 19 TP. 219 CPL rows; DNP C303 / C304 /
    C305 / C313 / C314.
  - 80 hidden designators (the list equals M3_R8's), 169 shown. 272 tests / 17 suites; quality_audit 21.
- **ORDERING coordinates on `6600ef94…`.** These match the board:
  - C24.1 (25.33, 51.1) and C15.1 (29.2, 49.82);
  - TP122 (20.45, 92.4) and U4 (10.0, 53.8, B);
  - C84 (37.0, 63.2), C121 (12.0, 83.8) and L1 (42.7, 66.6);
  - Q120 (16.38, 101.72), Q121 (8.0, 103.0) and U9 (41.5, 85.5, B);
  - In2 3V3 at (4, 64) and at J123.2, and In2 BAT_IN at (42, 114.4) and at J1.2.
- **F4 / M3_R8 / MARGIN / ORDERING DC figures** equal the evidence files, except 06(a) and (e).
- **F10's R8 statements** equal `check_r8` evidence (fence, separations, strip gaps) and the binding note (D6, D6.8).
- **AGENTS §1 table** (R8 rows) agrees with M3_R8: the neck widths, U4 13 mm west, UART7, PC13, the tooling holes removed.

## 8. Observations (not findings)

- **Legend margins.** Every terminal legend is nearest its own pin (gate). The two smallest margins are both 0.48 mm:
  - "1:BAT+" (30.63, 104.2): 5.35 mm from J1.1 and 5.83 mm from J1.2. It sits aft of J1, while 2/3/4 are on the forward
    edge.
  - "2:RAW" (6.2, 82.98): 6.21 mm from J124.2 and 6.69 mm from J123.1. It sits between J124 and the pull-pin connector.

  Unambiguous on the render (J123 carries "PULL"), but loose. A cosmetic tidy, if silkscreen is touched again, is to put
  1:BAT+ in the forward strip with the other three J1 legends.
- **U4 corner sliver.** GND_B fill reaches about 0.1 mm inside U4's nominal 2.5 × 3.0 mm outline at its forward-east corner
  (x 10.75–11.25, y 55.195–55.3; 0.05 mm²). The outline comes from the datasheet package size centred on the footprint,
  not from a body drawing. This is inside LGA body tolerance (Inference). P3's intent is met.
- **C12 #17, ARM1_SENSE–GND 0.171 mm,** is called "read disarmed: the safe direction". A false "disarmed" annunciation
  with the link in is safe against an inadvertent ground fire (a hard refusal), but not obviously safe for personnel who
  read the annunciator. This is for the pyro reviewer; the ARM link itself remains the physical indicator.
- **D16's four fence openings** (two adjacent pairs) against r8_plan §1's "three fence openings": the rule (gaps ≤ 2.7 mm)
  is met, and D16 fixes the gap, not the count. No issue.
- **The parent VEHICLE.md** has uncommitted vehicle-level edits. Its board stack row still names R7, consistent with D84
  and P1.

## Appendix A: methods (scripts in the session scratchpad, deleted after the pass)

- **Pad-to-copper gaps (01).**
  - For every footprint pad and every copper layer it is on (THT inner layers only where flashed), each foreign-net track
    or via on that layer is tested with `SHAPE.Collide`, and the gap is bisected to 0.5 µm. Pairs under 0.2 mm are kept,
    one row per (pad, net).
  - Pitch is the footprint's smallest pad-centre spacing. "Coarse" means > 0.65 mm.
  - "rigid" is taken from `r8_power_check.rigid_items`. It does not include every rigid strip or block item, so the
    new / rigid split in Appendix B is indicative.
- **THT GND connection.** `PAD.GetLocalZoneConnection()` (FULL = 2 on J122.3/6/9/12 and J123.2; inherited elsewhere);
  zone pad connection THT_THERMAL on GND_F / GND_B / R8_GND_In2, THERMAL on GND_In1.
- **MEMS bodies.** Nominal outlines centred on the footprint: U4 2.5 × 3.0 mm (LSM6DSV320X LGA-14), U5 5.0 × 3.0 mm
  (MS5611). B.Cu fill and tracks inside, with the pads subtracted.
- **Legends.** `check_r8.terminal_legends` evidence, plus text bounding boxes against the pad centres.

## Appendix B: pad / foreign-copper pairs under 0.2 mm (coarse-pitch parts, `6600ef94…`)

| Gap mm | Layer | Pad (net) | Foreign copper (net) | Copper |
|---:|---|---|---|---|
| 0.152 | F | R130.2 (GND) | PYRO1_CONT track (26.83–25.22, 88.42) | rigid CH1 |
| 0.155 | F | R305.2 (GNSS_TXD_MCU) | GND fence via (7.68, 23.3) | new |
| 0.170 | B | Q123.3 (BUZZ_OUT) | PULLPIN track x 14.23, y 61.0–71.4 | new |
| 0.170 | B | R81.2 (GND) | BAT_IN track x 41.25, y 88.9–94.6 | new |
| 0.170 | F | R129.1 (PYRO1_CONT_MID) | GND via (28.55, 87.21) | R7 C15 #1 |
| 0.171 | B | R162.1 (BUZZ_DRV) | GND via (15.4, 62.8) | new |
| 0.172 | F | FB30.2 (3V3_GNSS) | 3V3 via (12.33, 24.4) | new |
| 0.175 | B | C82.1 (RAW_PROTECTED) | GND via (40.88, 76.62) | new |
| 0.175 | B | Q30.2 (GNSS_ANT_SRC) | GND via (3.0, 13.0) | strip |
| 0.175 | B | R83.1 (BAT_OVLO) | GND via (39.0, 87.7) | new |
| 0.175 | B | R84.1 (BAT_ILIM) | GND via (42.9, 87.6) | new |
| 0.175 | B | U5.3 / U5.4 (GND) | 3V3A track y 57.85, x 9.97–12.95 | new |
| 0.175 | F | C84.1 (VLOGIC) | GND via (38.38, 68.38) | new |
| 0.175 | F | LS120.2 (BUZZ_OUT) | GND via (15.2, 70.9) | new |
| 0.175 | F | R166.1 (BAT_DAMP), R166.2 (GND) | RAW_PROTECTED track y 99.75, x 20.3–45.2 | new |
| 0.180 | B | C13.1 (3V3) | GND via (14.8, 51.6) | new |
| 0.180 | B | **Q120.9 (BAT_IN)** | **BAT_ENABLE via (16.6, 104.5)** | new |
| 0.180 | B | R120.2 (ACT_GATE) | GND via (15.0, 107.3) | new |
| 0.180 | B | R172.1 (RAW_ACT_SENSE), R172.2 (RAW_ACT_SENSE_MCU) | USB_LIMITED track x 29.95, y 37.25–54.0 | new |
| 0.180 | B | R301.2 (GNSS_ANT_GATE), R302.2 (GNSS_ANT_PD) | GND vias (6.0, 15.0), (8.0, 15.0) | strip |
| 0.180 | B | **R81.1 (BAT_ENABLE)** | **BAT_IN track x 41.25, y 88.9–94.6** | new |
| 0.182 | F | LED2.1 (LED_YEL_A) | GND via (8.12, 42.88) | new |
| 0.183 | F | R11.2 (3V3) | GND via (10.6, 57.0) | new |
| 0.189 | B | J1.4 (BAT_SW_RETURN) | GND via (14.7, 112.0) | new |
| 0.190 | B | Q120.8 (BAT_IN) | GND via (19.6, 104.4) | new |
| 0.190 | F | R178.1 (PYRO1_CONT) | GND via (28.55, 87.21) | R7 block |
| 0.193 | B | Q32.3 (GNSS_ANT_GATE) | GND via (8.0, 15.0) | strip |
| 0.193 | F | R129.1 (PYRO1_CONT_MID) | PYRO1_CONT via (28.4, 88.61) | R7 C15 #6 |
| 0.196 | F | C300.1 (3V3_GNSS) | GND fence via (12.3, 23.3) | new |
| 0.197 | F | FB30.2 (3V3_GNSS) | GND fence via (12.3, 23.3) | new |

There are 34 (pad, net) pairs; rows with two pads count twice. There are 4 more on fine-pitch parts (≤ 0.65 mm), which
C12's scope line already excludes. Every pair is DRC-legal at 0.15 mm. Vias are tented and pads bare, so a bridge needs a
mask defect, and JLC's electrical test screens hard shorts (Inference).
