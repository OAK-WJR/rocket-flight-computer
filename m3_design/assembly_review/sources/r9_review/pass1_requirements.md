# R9 review pass 1: requirements traceability

Reviewer dimension: requirements traceability. I checked every REQUIREMENTS row (F1–F10 with F10's new strip
boundary, P1–P3, M1–M3, "R9 acceptance") against the CAD, the gate and the records of the board built by R9 steps
1–10. I also checked:
- that the five owner decisions (`R9_OWNER_DECISIONS.md`) are honoured;
- the pin contract (U1's 100 pins against R8's `pin_table.tsv`, F10's bindings, the binding note);
- the consistency of REQUIREMENTS, STATUS, ORDERING, MARGIN_PRESCRIPTION, FMEA_REDUNDANCY, AGENTS, README, M3_R9 and
  R9_VALIDATION;
- whether R9_VALIDATION's "R9 deviations for owner acceptance" is complete, accurate, like-for-like and honest.

- **Board:** `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
  `fc3d5b34a4bfbaecfbcb44bdf8144c87015fc71be7accf48354f23410e8d0f51`; netlist `8b0e04ea565ecf1b…`; DRU
  `ea77b791eaa4026d…`. I checked these hashes before and after my runs. Every pcbnew measurement ran on a scratch copy
  with the same SHA. R8's board came from `git show 9c8179b:…` (SHA `cc044ea0…`); the R8 worktree was not touched.
- **Read-only:** this report is the only repository file I wrote. The board and schematic were never saved.
  `git status --porcelain` hashed the same before and after all runs. Scripts, board copies and outputs lived in
  `<scratchpad>/r9review/req/` and were deleted at the end.
- **Labels:** "Inference" marks anything not measured and not taken from a maker document.

**Result: 0 Critical, 0 Major, 10 Minor (all record-level, all cheap to fix).**
- **CAD:** every requirement row the CAD can show is met on `fc3d5b34…`. `tools/check.sh` exits 0 on my run, and the
  M2 sweep reproduces the step-10 evidence key for key. The U1 pin map equals R8's pin table pin for pin. The R8 → R9
  netlist diff is the three footprint fields and the 15 sheet revisions only.
- **Records:** the findings are about the records the owner is asked to accept. Four of them change what that
  acceptance means, so they should be fixed before the owner is asked:
  - **01:** the cause given for the 102 mm length is wrong. 100 mm fails only under the plan's own X9 ≥ 5.94 mm hard
    row, not under F10's 5 mm.
  - **02:** done row Z4 is reported as met, but TP120 has two vias inside its pad.
  - **03:** check_actuators was changed although owner decision 2 says "check_actuators unchanged", and the change is
    not on the owner's list.
  - **04:** two zone-connection exceptions to M2 that R7 and R8 listed for the owner are missing. On R9's copper, R8's
    reason for one of them no longer holds.
- **The other six:**
  - **05:** the R8 comparisons in the list are not like-for-like.
  - **06:** C13's list of thin margins is incomplete.
  - **07:** F10 swaps the west and east stitching sides.
  - **08:** FMEA was not updated for the new terminal adjacency.
  - **09:** the stall test's D12 framing is inaccurate.
  - **10:** a set of stale or inconsistent record lines.

## 1. What I ran

| Run | Result |
|---|---|
| `tools/check.sh` (KiCad 10.0.6; GUI session logged in, no shim; `NUMPY_PY` = cfd venv) | **Exit 0** in 219 s: DRC 0, unconnected 0, parity 0, ERC 0; audit OK; silkscreen 0 points outside; fit OK (J9 mated 0.03 mm); plate f1 256.6 Hz; rule-H seeded suite OK; check_r9 OK on all 40 rules; route_check r9: 0 failing, 0 allowlisted, 0 leftovers (14 bump windows); check_actuators OK. My `r9.json` equals `step10_evidence/gate/r9.json` except for R-5's window split (D-S10-18) and the label of P-0's rule-D closest pair (a 0.751 mm tie; see §8) |
| `step10/m2_sweep_r9.py` on a scratch copy | Every key equals `step10_evidence/m2_sweep.json`: adjacency 33, adjacency_pad 28, chain_detour 18, routes 38, via_fold 34, via_step 1, poured_hop 0, pad_edge 5, short_hop 7, bumps_all, margin_free |
| `check_r9.py --only R-13,M-3,R-7,R-10` on R8's committed board (like-for-like baselines) | R-13 nearest 65.98 mm (U31 to R131.1 PYRO1_OUT); R-10 part 5.94 mm, line 5.075 mm (R306–USB_DM); M-3 tie channel 2.264 mm (R150); R-7 GNSS left 2.34 / right 2.725 mm, radio 1.70 / 2.405 mm |
| `m3_design/r9_kill_path.py` re-run with `r9_legalise.RF_SEP_PART` patched from 5.94 to F10's 5.0 mm (wrapper in scratch, `--lengths 98 100`) | **98 mm: no clean arrangement (R306 0 spots); 100 mm: holds**, total detour 6.96 mm: R306 (18.9, 27.4) rot 90, R315 (19.9, 27), R310 (20.9, 27), R313 (21.9, 27.4) rot 90. The recorded run at 5.94 mm (`step3_evidence/kill_path.txt`) fails 98 and 100 and holds at 101 / 102 |
| Thermal-relief test on a scratch copy | J122.3 / 6 / 9 / 12 set from FULL to inherited (the GND pours' THT thermal), zones refilled natively, `kicad-cli pcb drc`: **0 starved_thermal**, 0 unconnected (only 199 `lib_footprint_issues`, from the scratch folder's missing library table). GND fill in a 1.2–1.6 mm ring round each pad drops from 0.69–0.97 to 0.32–0.67 (F / B), so the reliefs were applied |
| pcbnew scans (Appendix A) | Outline, holes, key parts, terminal pad maps, U1 pin map, local clearances, RF-strip contents by layer, via holes against pad openings, MEMS bodies, designators, silkscreen texts, zone connections, In2 areas, courtyard extents, U4 pad 1 |
| Netlist diff R8 (9c8179b) → R9 | 84 diff lines: 15 sheet `<rev>` lines plus J121 / J124 (`M3_DB128L_2P_BK_SW`) and J122 (`…_MIR`) footprint fields; nothing else |
| Fab / cost bindings | `cost_check.json` `inputs_sha256` equals the BOM `ab3d8171…` and CPL `eee180fb…` on disk; $109.38 per board, `extended_codes` 52, checked 2026-10-24 21:03:45Z; stock: U4 40, U30 34 |

## 2. Previous pass in this dimension

R9 has had no review pass before this one. The last requirements review was R8 pass 4
(`r8_review/pass4_requirements.md`). Its four Minors were fixed in R8 and carry into R9's rewritten records:
- **R8P4-01:** the bootloader step is a sub-bullet of ORDERING §5's pyro-gate list (l.155), and the RF step points to
  it (l.161).
- **R8P4-02:** the pull-pin is called an "advisory pad witness" in AGENTS l.19. No R9 record calls it a launch detect.
- **R8P4-03:** R8-era figures; nothing carried over.
- **R8P4-04:** README, ORDERING, STATUS, AGENTS, M3_R9 and R9_VALIDATION all say the same thing: no review pass has
  run on R9, and R8 is the board to order.

The step-10 handoff (§5) names one R8-era line it left as written: P2's "sixth support open" sentence. It is part of
finding 10.

## 3. Requirement walk on `fc3d5b34…`

Verdicts:
- **Pass:** shown in the CAD, the gate or the fab files.
- **Partial:** the CAD part passes and the rest is open.
- **NV:** needs the bench, a flight or firmware.

| Row | Verdict | Evidence / remark |
|---|---|---|
| Sources (one CH1, isolated Blue Jay, 4 servos, on-board MAX-F10S / E22, uplink cannot arm) | Pass | Netlist unchanged from R8 but the footprint fields; check_actuators OK |
| F1–F3, F5 | Pass (parts), NV | U4 bottom, rotation 180, (12.0, 47.4). Pad 1 is at (+1.21, −0.75) mm from the centre, R8's (−1.21, +0.75) turned 180°. Roll = −gyro_Y appears the same way in AGENTS, STATUS, M3_R9, ORDERING §5 and the binding note; M-7 keys the rotation on the revision |
| F4 | Pass (CAD, calc), NV | `dc005_*.txt`: 0.79 / 0.16 / 0.26 mΩ; necks 7.81 / 8.15 / 5.18 mm on B.Cu; 12.7 / 12.1 / 20.4 °C; vias 0.46 / 0.61 / 0.22 A. GND return 0.32 mΩ (`dc/gnd_servo.txt`). `r9_post_check.py` holds D12 at 0.1 mm (l.17–19). The stall-test wording is finding 09 |
| F6 | Pass (CAD), NV | Circuit unchanged (netlist diff) |
| F7 | Pass (CAD, calc), NV | `dc/fire_loop.txt` and `dc_summary.txt`: 10.06 + 2.41 + 2.42 + 1.58 + 0.16 + 0.26 + 0.81 = 17.70 mΩ; FETs 2 × 4.3 + 5.8 = 14.4 mΩ; 7.4 / 4.4821 = 1.651 A ≥ 1.5 A. With R134 at its 1 % maximum (2.02 Ω) the budget is still 1.644 A (Calc) |
| F8 | Pass (CAD), NV | DRC 0 under the DRU: nine pyro rules, two LC-1 rules and eight fill-margin rules (+0.25; E +0.35, checked in the file). LC-1: 0 pad or footprint overrides (pcbnew). J121.1 OUT (10.1, 70.73), J121.2 IGN (10.1, 75.81), J124.1 BUS (10.1, 80.96), J124.2 RAW (10.1, 86.04): numbers keep their nets, pin 2 forward. Legends on the board: ARM, IGN, top 2:RAW / 1:E1−, bottom 1:BUS1 / 2:E1+ (K-legends ownership ≥ 0.31 mm). P-0 / P-3 / P-6 / P-7 / P-11 OK. The new terminal adjacency is finding 08 |
| F9 | Pass (CAD), NV | F9-1: D8 5.22, C80 8.90, C96 5.72, C89 4.79, C95 4.69, R166 8.38, R167 5.59, U9 13.22 mm (≤ 10.6 / 27.07). J3 on the west edge |
| F10 strip boundary (owner decision 3) | Pass | Deepest strip courtyard C300 21.955 mm. Every courtyard reaching y < 22.0 belongs to an RF part (35 parts: J30, J31, U30, U31, the chains, the limiter, the module supply and interface parts, TP30). The four MCU-end resistors (R306 / R310 / R313 / R315) are outside it (D-S1-03) |
| F10 strip contents | Pass | Below y 22.0: In1 and In2 carry GND only (R9_GND_In1, R9_GND_In2_strip). F.Cu carries GND, the four RF nets, 3V3 / 3V3_GNSS / 3V3_RADIO module feeds, the GNSS / radio interface nets and unconnected module pads. B.Cu carries GND, the limiter nets under U30 (GNSS_ANT_* / VCC_RF / LNA_EN) and the RADIO_TXEN loop west of U31's body (x 25.25 < 25.61) |
| F10 RF / pins | Pass, NV | Jacks 18.7 mm apart; fence 24 vias on y 22.2 with openings 2.15 / 2.1 / 2.15 / 2.5 mm, each crossed by its lanes; GCPW and launch per R9_VALIDATION; R-13 46.13 mm. The stitching side labels are swapped (finding 07); the 5.005 mm fast-line figure is left out (finding 06) |
| P1 | Pass (CAD); parent VEHICLE pending | Outline 46 × 102 mm. M3 holes (4, 4), (42, 4), (4, 98), (42, 98), (42, 59.5); tie holes (15.6, 62), (30.8, 59) (Edge.Cuts circles). VEHICLE row proposed, not applied (D-S10-11; R9 not accepted) |
| P2 | Pass (CAD), NV | Plate model pinned 256.6 / 362.9 Hz, clamped 434.8 / 614.9 Hz (D5 / D10). Support clearances 4.600 / 5.008 mm. M-3 tie channel 2.007 mm against 2.0 (finding 06). Stale R8 sentence (finding 10) |
| P3 | Pass | U4 / U5 bodies: B.Cu fill under them ≤ 3 × 10⁻⁶ mm² (polygon-edge slivers), no via. Coating, staking and J2 procedure in ORDERING §5 |
| M1 | Pass | Stackup F.Cu 35 µm / 0.203 prepreg / In1 30 µm / 1.03 core / In2 30 µm / 0.203 / B.Cu 35 µm; ENIG. CPL verify 78 + 133 + 8. U4 in JLC stock (40). M1's U4 sentence is finding 10 |
| M2 (rules, vias in pads, silkscreen) | Pass, except a listing gap | The only via holes within 0.1 mm of a pad opening are TP120's two, M2's named R9 exception. Text 1.0 mm. 139 designators shown and 110 hidden, set-equal to M3_R9's list. Thermal-relief exceptions are unlisted (finding 04) |
| M2 (clean routing, deviation list) | **Partial** | The gate is clean and the sweep reproduces. Owner acceptance is open. The list needs findings 01–06 |
| M3 | Pass (2026-10-24 run) | $109.38 ≤ $126.41; 52 ≤ 52; bound to the current BOM and CPL; rerun within 24 h of ordering |
| R9 acceptance | Not met (as recorded) | Review loop, owner acceptance, commit, U4 / tabs / cost run open. "check_actuators.py (pinned to its reviewed R9 version)" is finding 03 |

## 4. Owner decisions (R9_OWNER_DECISIONS.md)

| Decision | Honoured? | Evidence |
|---|---|---|
| 1. B-spine at 98 mm, fallback 100 / 102 mm "if placement fails"; pyro leads west, battery leads east | Partly | B-spine, pyro entries −x (P-11) and battery leads along the east wall to J1's forward entry (plan_spine §3, ORDERING §7) are honoured. **102 mm:** placement fails at 100 mm only under the plan's X9 ≥ 5.94 mm hard row, not under F10. The records say F10 (finding 01) |
| 2. Stricter pyro rules (P-1b, P-3, P-7, strict pad rules); renumbered J121 / J124 on the same part and land, "check_actuators unchanged" | Partly | P-1b is in the DRU's rule G; P-3, P-7, P-0 (H+ / GS / AG) and P-6 are in check_r9; LC-1 holds. Variants keep land, part, LCSC and nets per pad number. **check_actuators.py changed:** 191 insertions, 13 deletions against 9c8179b (finding 03) |
| 3. Strip y 0–22.0; about 45 mm radio-to-pyro accepted with the keyed-radio immunity bench test | Yes | R-1 21.955 mm; F10 text updated; R-13 46.13 mm; ORDERING §5 makes the test a required gate before flight |
| 4. Signal vias ≤ 70 with per-family budgets, stretch 55 | Yes | S4 57; family budgets gated at step 7 (D-S7-18 / 19); the stretch miss is C11d |
| 5. J122 turned (reason recorded); mid support (42, 55.5) if the DC solve holds, else (4, 49.5) | Yes, with a listed agent decision | The turn's reason (about 6–8 mm of length; fit 0.50 against 0.71 mm) is in plan_spine §3 / §6 (l.62, 218). The support moved +4 mm with the forward block to (42, 59.5); listed in part D (D-S3-08 / D-S6-09) |

## 5. Pin contract

- **U1:** 100 of 100 pads equal `pin_table.tsv`'s `r8_net` (SHA `bd4687a8…`; 0 differences). Spot checks:
  - PE4 PYRO1_GATE_N; PC0 PYRO1_CONT_MCU; PC5 ARM1_SENSE_MCU; PB0 RAW_ACT_SENSE_MCU;
  - PE7 / PE8 CAM_MCU_RX / TX; PE9 RADIO_NRST; PE15 RADIO_DIO1;
  - PB10 / PB11 / PB14 / PB15 RADIO_SCK_MCU / NSS / MOSI_MCU / MISO_MCU; PD8 BUSY; PD9 RXEN;
  - PD14 GNSS_RESET_N; PD15 GNSS_TP_MCU; PC6 / PC7 GNSS UART;
  - PC13 BUZZ_DRV; PC14 PULLPIN; PC8 VBUS_SENSE; BOOT0; PE1 IMU_INT1; PE10 NC.
- **Loader pins:** K-contract's list (PA2, PA11 / PA12, PB6, PB9, PB10, PB14; NC PA6 / PA8 / PA9 / PC9 / PC11 / PE13)
  equals R8's.
- **Binding note:** names board `fc3d5b34…`, netlist `8b0e04ea…`, pin table `bd4687a8…`, `changed_from_r8 {}`, R8's
  constraints, and the IMU map (rotation 180, roll −gyro_Y, lever arm −11.0 mm). F10's R8 binding constraints apply to
  R9 unchanged.
- **Connector pin order:** J122 pad 1 SERVO1_OUT at (19.19, 59.46), the west end. Signal row aft, RAW_ACT middle, GND
  forward. The plug legend 1–4 runs west to east.

No contradiction found.

## 6. Findings

| ID | Sev. | Requirement | Finding | Evidence | Fix |
|---|---|---|---|---|---|
| R9P1-REQUIREMENTS-01 | Minor (worth fixing) | P1 ("target length as short as possible"); owner decision 1 ("fallback 100 / 102 mm if placement fails"); M2 (each deviation with its measured reason) | **The records blame F10's 5 mm rule for the 102 mm length. The real cause is the plan's own X9 hard row, and the owner is offered only part of the choice.** M3_R9 l.32–33, STATUS l.30–31 and R9_VALIDATION l.80 and C1 (l.179) say 98 and 100 mm "cannot legalise the four MCU-end interface resistors against F10's 5 mm rule and the SERIES rule". The search behind that (D-S3-03, `r9_kill_path.py` through `r9_legalise`) holds those resistors' courtyards ≥ 5.94 mm from U1 / U3 / Y1. That is r9_plan §2's hard row X9 ≥ 5.94, R8's measured R306–U1 distance, not F10's limit. I re-ran the same script with the part separation at F10's 5.0 mm. **100 mm holds**, with a clean lane-ordered arrangement and a total detour of 6.96 mm; 98 mm still fails. C1's only owner option is "reclassify the four out of F10's RF-part list and return to 98 mm" | `step3_evidence/kill_path.txt` (5.94 mm: 98 / 100 no arrangement, 102 holds); `m3_design/r9_legalise.py` l.65 (`RF_SEP_PART = C9.RF_SEP_PART`); `tools/check_r9.py` l.178 (`RF_SEP_PART, RF_SEP_LINE = 5.94, 5.0`); r9_plan l.34 (hard row X9 ≥ 5.94); D-S1-13; my re-run with `LG.RF_SEP_PART = 5.0`: "100 mm … holds, total detour 6.96 mm: R306 (18.9, 27.4) rot 90, R315 (19.9, 27) rot 90, R310 (20.9, 27) rot 90, R313 (21.9, 27.4) rot 90" | Correct the cause in M3_R9, STATUS, R9_VALIDATION (Length row, C1) and the step-3 summary: "100 mm fails only under r9_plan's X9 ≥ 5.94 mm (R8's measured R306–U1); under F10's 5 mm, the kill path holds at 100 mm (detour 6.96 mm against 2.62 mm at 102)". Add it as a second owner option in C1 (100 mm with the four interface resistors at 5.0–5.94 mm from U1, a relaxed hard row, F10 still met). Note that the full 100 mm board is not built: only the resistor spots are shown (Inference for the rest) |
| R9P1-REQUIREMENTS-02 | Minor (worth fixing) | r9_plan §2 done row "Z4 = C6 = 0"; M2 (deviation list accurate); REQUIREMENTS "R9 acceptance" | **Done row Z4 ("vias inside test pads") is reported as met, but TP120 has two vias inside its pad. So 17 done rows are missed, not 16.** survey_baseline l.156 defines Z4 as vias inside test pads, with TP122's A8 as R8's one instance. The scorecard counts only `requalify['a8']['vias']`, that is, TP122. It reports Z4 = 0 ("R8 1 (A8)"), and R9_VALIDATION l.81 lists "Z4 = C6 = 0" as met. Yet C18 in the same file, M2's R9 clause and ORDERING §3 / §4 name two RAW_ACT vias inside TP120. My scan finds them: the hole of (29.6, 78.2) has its centre inside the pad, and the hole of (31.0, 78.2) crosses the east edge. TP120 is a 1.5 mm pad at (30.2, 78.4), courtyard x 29.16–31.25, y 77.36–79.44, on the 7.7 A via row y 78.2. C6 = 0 is correct, because RAW_ACT is not a critical signal net | `tools/r9_scorecard.py` l.65–66; `step9_evidence/r9_scorecard.md` (Z4 0, yes); R9_VALIDATION l.3–4, l.74, l.81, l.163, C18 l.199; `ordering_facts.json` `vias_in_bare_contacts`; D-S10-14 ("found by step 10", after the scorecard ran) | Record Z4 = 2 (missed, cause C18), so 33 met and 17 missed in R9_VALIDATION, STATUS and M2. Make the scorecard count vias in every `TP*` pad. Or (the review loop's call, D-S10-14) move TP120 about 1.5 mm off the via row onto the same RAW_ACT pour (no foreign copper there): Z4 back to 0, C18 and the expected DFM query gone |
| R9P1-REQUIREMENTS-03 | Minor (worth fixing) | Owner decision 2 ("renumber J121/J124 pads (same part, same land; check_actuators unchanged)"); r9_plan §3 item 2; REQUIREMENTS "R9 acceptance" | **check_actuators.py was changed against owner decision 2's wording, and the owner's list does not say so.** Against 9c8179b: 191 insertions and 13 deletions. Rule 15b's fixed rectangle became a content-based containment test (D-S1-02), and DRU_SHA and rule G's PYRO_RULE_SHA were re-pinned twice (D-S2-11, D-S5-12). D-S2-02 still cites "check_actuators unchanged" as its basis. The change was forced by two other owner choices: the B-spine geometry, and P-1b's DRU edit, which the file pins. Rules 1–14 and 16 are unchanged, and the new 15b is argued to be stricter. M3_R9 l.50–51 records it. But part D lists only D-S7-06, D-S3-08 / D-S6-09, D-S9-03, D-S10-03 and D-S4-02. And "R9 acceptance" (l.122) calls the file "pinned to its reviewed R9 version" before any review has run (R8 acceptance said "byte-identical to R7's") | `git diff --stat 9c8179b -- m3_design/check_actuators.py`; file SHA `3f22b273…` = check_r9 `CHECK_ACTUATORS_SHA` (l.111); R9_OWNER_DECISIONS l.6; R9_DECISIONS D-S1-02 (l.21–37), D-S2-02 (l.265), D-S2-11 (l.360–367), D-S5-12 (l.785–786); R9_VALIDATION part D l.201–209 | Add a part-D row: "owner decision 2 said check_actuators unchanged. Its contract rules (1–14, 16) are unchanged; 15b is now content-based (stricter, D-S1-02), and the DRU / rule-G pins follow P-1b and the fill margins (D-S2-11, D-S5-12)", for the owner to accept. Reword "R9 acceptance" to "pinned to its R9 version (reviewed in the R9 review loop)" until a gate-integrity pass has signed it off |
| R9P1-REQUIREMENTS-04 | Minor (worth fixing) | M2 ("Through-hole GND pins use thermal reliefs wherever their spokes are not starved (exceptions listed in M3_R4 §2; R8: R8_VALIDATION C17)"); M2's deviation list ("every review-only residual is listed") | **Two zone-connection exceptions that R7 and R8 listed for the owner are missing from R9's list. On R9's copper, R8's reason for one of them is gone.** On the R9 board, J122.3 / 6 / 9 / 12 (GND, THT) are ZONE_CONNECTION_FULL, inherited from R8's instances by D-S2-03, and so are D30.2 and D31.2 (the RF clamps' GND pads, an exception to the house relief rule). R8 listed these as C17 (because J122.3 "would be starved on F.Cu") and C16 (R7 C13). R9's C1–C18 has neither, and M2 points only to M3_R4 §2 and R8 C17. I gave J122's four GND pins the pours' THT relief on a scratch copy and refilled: KiCad DRC reports **no starved_thermal**. So on R9 the solid joints rest only on the 7.7 A servo return. That may well be a good reason, but it is not recorded or accepted. ORDERING §4 already asks for preheat and a hole-fill check on these pins | pcbnew zone-connection scan: FULL on D30.2, D31.2, C303.2, C305.2, C313.2, C314.2, J122.3 / 6 / 9 / 12 (R8 the same); R8_VALIDATION (9c8179b) C16 l.493, C17 l.494; scratch DRC JSON: 0 starved_thermal; ORDERING §4 l.94 | Add two C rows. J122's GND pins solid on F.Cu / In1 / B.Cu (J122.3 also In2): reason the 7.7 A return; KiCad finds no starvation with reliefs on R9, so it is a current choice, not a starvation exception. D30.2 / D31.2 solid: the RF exception, R7 C13 / R8 C16. Or apply the THT relief to J122's GND pins and re-solve `gnd_servo`. Add "R9: R9_VALIDATION C…" to M2's exception pointer |
| R9P1-REQUIREMENTS-05 | Minor (worth fixing) | M2 (the deviation list honest and like-for-like); owner priority 2 (simple, robust layout) | **The list compares R9 with the accepted R8 only where R9 wins, so the owner cannot see where R9 is worse than the board it would replace.** R8's figure appears in C11 (R6b 0.1022 against 0.1107) and C11b (X3f 291.8 against 321.3), both better. It is missing from every row where R9 is worse. R8 values from `tools/scorecard_r8_r9.json`, bound to `cc044ea0…`: X2g 6 → 7; S10b 231 → 260; Y1 27 → 31; **Y1b 8 → 14** and **Y2c 4 → 11** (pairs at the DRC minimum); Y5 26 → 34; **P7 1 → 9**; S4 55 → 57; information instances 91 → 114. Three more like-for-like gaps: (a) R6b beats R8 only through C14's crystal plane, and with R5's void restored it is 0.1396, worse than R8 (D-S8-20 says so; C11 and C14 do not tie the two together); (b) C16 lists USB_LIMITED and VLOGIC but leaves out RAW_ACT → J124.2, 0.44 → 10.06 mΩ (23×), and 3V3 → C100, 18.36 → 44.85 mΩ, which M3_R9 l.153–156 lists as "Higher than R8"; (c) F10 compares R9's 46.13 mm to the nearest armed copper with R8's 68.4 mm to J121; on the same metric R8 is 65.98 mm (my check_r9 R-13 run) | `tools/scorecard_r8_r9.json` (source line names `cc044ea0…`); `step9_evidence/r9_scorecard.md`; R9_VALIDATION C2, C4, C5, C7, C9, C11, C11b, C11d, C14, C16, part E; R9_DECISIONS D-S8-15 ("R8 1, with 8 trims"), D-S8-17, D-S8-20 (l.1724–1725); `dc_summary.txt` | Give every C row R8's value from the same metric, and mark the rows where R9 is worse. In C11 / C14 say "without the crystal plane R6b is 0.1396, worse than R8's 0.1107". Add the two supply-path rows to C16. Give F10's R-13 comparison R8's 65.98 mm on the same metric. Count the S10b row in the owner summary's list |
| R9P1-REQUIREMENTS-06 | Minor (worth fixing) | M2 (deviation list complete); F10 ("RF parts ≥ 5 mm from … fast digital lines"); P2 (4 mm tie path); P-6 (owner decision 2) | **C13, "thin, legal margins", leaves out the thinnest ones.** C13 lists H+ 0.025, J9 0.028, R-7, R-12 C301, R-1 C300 and D120's lane. It does not list: (a) R-10's nearest fast-net pad, **5.005 mm** against F10's 5.0 (R306 to USB_DM; R8 5.075); (b) M-3's tie channel, **2.007 mm** against 2.0 (R124's courtyard; R8 2.264); (c) P-6's bare actuator-gate pad, **1.03 mm** against 1.0 (R120.2 to C120.1), an owner-adopted strict rule like H+, which C13 does list; (d) K-copper's via ring to a paste aperture, **0.005 mm** against 0 (GND via (42.0, 81.26) to C8.2's paste; R8 0.025). F10's R9 clause (l.60) quotes only "nearest 6.04 mm, R313 to U1", which reads as a margin of more than 1 mm | My `gate/r9.json`: R-10 `nearest_line [5.005, R306, USB_DM]`, M-3 `channel_nearest [2.007, R124]`, P-6 `R120.2 [1.03, C120.1]`, K-copper `via_paste.nearest_ring_mm [0.005, …C8.2]`; check_r9 l.178 `RF_SEP_LINE = 5.0`, l.196 `TIE_CHANNEL = 2.0`; R8 values from my check_r9 run on 9c8179b and R8 pass 4 ("nearest ring 0.025 mm (C90.1)") | Add the four to C13. In F10's R9 clause add "nearest fast-net pad 5.005 mm (R306–USB_DM)" |
| R9P1-REQUIREMENTS-07 | Minor (worth fixing) | F10 (R9 stitching figures); records match the board | **F10 swaps the west and east stitching gaps on both RF lines.** It says "2.38 / 1.75 mm on the GNSS west / east sides and 1.70 / 2.405 mm on the radio sides". check_r9 R-7 labels a side "left" when `d > 0` in `beside()`, with d = (p − a)·u_y − (p − a)_y·u_x, along a path that runs from the jack pad to the module (+y). So "left" is +x, east. Cross-check: D-S1-05 calls R8's 2.73 mm path gap the GNSS **west** gap, and check_r9 on R8's board reports it as `GNSS_right_largest_gap_mm 2.725`. So right is west. My explicit recompute on R9 gives GNSS east 2.38 / west 1.75 and radio east 1.70 / west 2.405 | `tools/check_r9.py` l.1166–1181 (`beside`), l.1395–1406 (`label = 'left' if side > 0`), l.1031–1033 (path from the jack); `gate/r9.json` R-7; R9_DECISIONS D-S1-05; REQUIREMENTS l.60 | Change F10 to "1.75 / 2.38 mm on the GNSS west / east sides and 2.405 / 1.70 mm on the radio west / east sides". Label R9_VALIDATION's "GNSS 2.38 / 1.75, radio 2.405 / 1.70" east / west, and the radio pair is then in the other order. Ideally R-7 reports compass sides |
| R9P1-REQUIREMENTS-08 | Minor (worth fixing) | F8 / AGENTS §2 (pyro terminals and harness); r9_plan §6 risk row "Renumbered footprints → pad-role check; legends; harness and FMEA text"; D-S10-09 | **R9 creates a new wire-entry adjacency at the pyro terminals, and no record analyses it. FMEA was not touched, although D-S10-09 says FMEA text names pads by role.** In R8, J121 at (36.0, 93.3) took wires from the east edge and J124 at (10.0, 93.3) from the west, 26 mm apart. In R9 both are at x 10.1, rotation 90, wires from −x, courtyards touching at y 78.39. The entries run OUT 70.73, IGN 75.81, **BUS1 80.96**, RAW 86.04. So J121's IGN wire and J124's BUS1 wire enter 5.15 mm apart, like adjacent positions of one four-way terminal. Those are R134's two ends. A stray strand there shorts R134, the shorted-igniter current limit (AGENTS §1), and continuity / arm sensing cannot see it. As a single fault, the fire current into a 1 Ω e-match rises to about 5.8 A at 8.4 V (Inference). With a shorted igniter as a second fault, the fire is a dead short and the logic browns out, which is R134's whole purpose. ORDERING §7's termination rule (ferrules or tinned solid wire) covers both terminals, but it names only the RAW–BUS strand (I-4). `docs/FMEA_REDUNDANCY.md` last changed in R7 (431025d) | R8 and R9 pad positions from pcbnew (§6 of Appendix A); ORDERING §7 l.201–202 ("route and label the two harnesses so that they cannot be swapped"); r9_plan l.117; R9_DECISIONS D-S10-09 (l.1988); `git log -- docs/FMEA_REDUNDANCY.md` | Add a line to FMEA (I-4 / V-16 class) and to ORDERING §7: "R9 puts J121 and J124 end to end on the west edge. IGN (J121.2) and BUS1 (J124.1) enter 5.15 mm apart. A stray strand there bypasses R134 and is invisible to the board's sensing. The ferrule rule covers it: check it at termination." Correct D-S10-09's FMEA claim, or write the FMEA text it promises |
| R9P1-REQUIREMENTS-09 | Minor (worth fixing) | F4 ("Perform a thermal-camera stall test"; R9 clause "all three necks lie at an FET"); ORDERING §5 ("the check on R8_DECISIONS D12's IPC-2152 estimates") | **R9's stall test checks no D12 estimate, yet ORDERING still calls it that check. And the BAT_IN neck is not at an FET.** R8 had one copper-only pass point: the RAW_ACT neck ≤ 17.5 °C, 12 mm from either FET. R9 makes every neck reading information only and judges the copper beside the FETs at about 29 °C (D-S10-06). So the CAD's D12 limits are never bench-checked on R9, but ORDERING l.167 still frames the test as their check. Separately, F4, R9_VALIDATION l.135, MARGIN P1-9 (l.207) and AGENTS l.16 say every neck lies at an FET. The BAT_IN neck's cut box (x 29.86–31.06, y 89.8–97.75) is 0.24 mm outside Q120's courtyard (x 31.30–36.70, y 87.86–95.14). It reaches 2.6 mm beyond it in y and lies wholly inside J1's courtyard (x 8.90–31.09, y 88.86–100.14). So "each FET's own dissipation dominates" is not shown there, and that neck gets 29 °C instead of D12's 20 °C | `ordering_facts.json` `necks` (BAT_IN box_to_courtyard Q120 0.24, J1 0.0); courtyards measured with pcbnew; ORDERING l.167; REQUIREMENTS F4 l.54; R8's ORDERING (9c8179b) stall-test pass line | Say plainly in F4 and ORDERING that on R9 the D12 limits are a CAD check only, or add one copper-only pass point: the BAT_IN neck against D12's 20 °C, or a RAW_ACT spine point ≥ 5 mm from both FETs and J122 with its own IPC figure. Change "each at an FET" to "RAW_ACT and ACT_FET_S at Q121 / Q120; BAT_IN under J1, 0.24 mm from Q120" |
| R9P1-REQUIREMENTS-10 | Minor (worth fixing) | AGENTS §3 (records match the board; update in place); records consistency | **Stale or inconsistent lines in the records the owner reads.** (a) P2 (l.67) still says the owner's ruling on R8's sixth support is open, while M2 (l.75) records R8's list accepted on 2026-10-20 "including the C10 vibration item" (handoff §5 left it as written). (b) "R8 acceptance" (l.115–116) still ends "Until R8 is accepted, R7 … is the revision to order". (c) M3_R9 l.107–108 gives the In2 regions as RAW_ACT 244.5 and 3V3 1098.9 mm². Those are step 6's figures (`step6_evidence/r9_power_check.json`). The final board has 241.9 / 1037.1 mm², which is what ORDERING §3 (l.50) and `ordering_facts.json` give. (d) M1 (l.74) still says U4 is "out of JLC stock, it is bought … and consigned … before ordering". On 2026-10-24 JLC had 40, and "R9 acceptance" says "U4 in JLC stock or consigned". (e) R9_VALIDATION's reference row (l.138) uses "R8 step 9: 5,525 / 47,769" (11.6 %) as R8's figure, while C11, STATUS and the scorecard use the accepted board's 0.1107. (f) MARGIN_PRESCRIPTION R14 (R7) (l.306) ends with "R8: unchanged (the jacks, their pads and the strip copper are R7's, rigid and hash-asserted)" and has no R9 clause. Its basis does not hold on R9, where the strip is regenerated and congruent by R-4. (g) M2's per-revision lists (nets with a pour "on R8: …", the legend check "run by `tools/check_r8.py` for R8") name no R9 entry. R9 adds a RAW_PROTECTED F.Cu pour, and the legend check runs as check_r9 K-legends | Each line cited; pcbnew zone fills (R9_3V3_In2 1037.13, R9_RAW_ACT_In2 241.89 mm²); `stock_check.json` (U4 `jlc_stock` 40); `tools/scorecard_r8_r9.json` (R6b 0.1107) | (a) "accepted 2026-10-20 with C10". (b) "R8 was accepted on 2026-10-20". (c) 241.9 / 1037.1 mm². (d) "when U4 is short in JLC stock, it is bought … and consigned". (e) use R8's accepted board, 0.1107 of 46,845 samples (`tools/scorecard_r8_r9.json`). (f) add "R9: the same jack and land, launch congruent with R7's (check_r9 R-4); the staking and sled rules unchanged". (g) add R9's pour list and K-legends |

### Severity notes

- **None is Major.** Every requirement row the CAD can show is met, the gate passes, and no safety rule is weakened.
  Each finding is a record error, a missing record, or a comparison that is not like-for-like.
- **01–04 should be fixed before the owner is asked to accept the list.** They change what is being accepted:
  - **01:** the real cause and price of 102 mm;
  - **02:** a done row reported as met that is missed;
  - **03:** a departure from an owner decision's wording;
  - **04:** two M2 exceptions the owner accepted for R7 and R8 and is not shown for R9.
- **08 comes closest to safety.** It is Minor because:
  - the hazard needs a termination defect, and the existing ferrule rule prevents it;
  - its single-fault outcome is a higher fire current, not an unwanted fire;
  - only a second fault (a shorted igniter) gives a brownout, and the isolated backup altimeter covers recovery.

## 7. Deviation list audit (R9_VALIDATION l.155–229)

| Part | Check | Result |
|---|---|---|
| A (allowlist), B (leftovers) | My `route.json` | allowed 0, stale 0, leftovers 0, missing 0: match |
| E (114 information instances) | My `route.json` | pad_end_offcentre 64, segment_inside_pad 11, passes_through_pad 9, width_change_junction 8, extra_bends 8, u_turn 7, power_via_no_gnd 7; classes power 62, other 33, rf / rfif 10, pyro 6, spi / usb / actuator 1 each: match (no R8 comparison: finding 05) |
| F (sweep coverage) | My m2_sweep re-run | Key for key equal to the evidence |
| C1–C11d against the scorecard | `step9_evidence/r9_scorecard.md` | Rows and figures match. Z4 is missing (finding 02). C1's cause is wrong (finding 01). R8 comparisons are selective (finding 05) |
| C12 (rule G at U1.3) | My `r9.json` P-0 / P-7 | 0.412 mm to U1.2 / U1.4 (NC sentinels, 0 V in reset); QSPI_IO2 0.833 mm and 3V3 1.305 mm, ≥ P-7's 0.5 mm: as recorded |
| C13 (thin margins) | My `r9.json` | Four thinner margins missing (finding 06) |
| C14 / C11 | D-S8-17 / 20 | The coupling is not stated (finding 05) |
| C16 | `dc_summary.txt`, M3_R9 table | Two regressions missing (finding 05) |
| C18 | pcbnew | Two vias as stated |
| D (agent decisions) | R9_DECISIONS | D-S1-02 (check_actuators) is missing (finding 03). Observation: D-S8-19 (unconnected inner via pads removed on every via, which changes the inner Gerbers, ORDERING §2) is an agent decision with fab effect and could be listed |
| Missing categories against R8's list | R8_VALIDATION C16 / C17 | Zone-connection exceptions (finding 04) |

## 8. Consistency checked (no finding)

- **Identity.** Board `fc3d5b34…`, netlist `8b0e04ea…`, DRU `ea77b791…` and check_actuators `3f22b273…` agree across
  STATUS, M3_R9, R9_VALIDATION, REQUIREMENTS, the binding note, `cost_check.json` (BOM / CPL hashes equal the files)
  and the gate.
- **Status wording.** "No review pass yet, owner acceptance open, uncommitted, order R8" is the same in README, STATUS,
  AGENTS, ORDERING l.3, M3_R9 and R9_VALIDATION.
- **AGENTS §1 R9 entries.** Every figure checked: positions, F9-1 distances, necks, J122 orientation and plug 1, the
  holes, f1, $109.38 / 52.
- **ORDERING R9 coordinates.** Spot-checked: TP80 (36.0, 96.8) B BAT_IN; TP74 / TP88; C88 (38.2, 90.23); C24 pads
  (20.33 / 21.17, 50.6); C15.1 (24.2, 49.32); R311.1 (37.75, 14.0); R312.1 (26.55, 7.58); TP122 (7.58, 63.5);
  C304 (9.6, 13.97); L1 (40.0, 76.6). Also the assembly counts (83 top, 136 + 10 bottom, 219), via counts (343 + 236 =
  579) and In2 areas: all equal the board.
- **Silkscreen.** 35 board texts, all 1.0 mm. The four terminal pin legends sit as M3_R9 says. M3-ASSY-R9 is at B
  (24.4, 97.9) and JLCJLCJLCJLC at B (23.65, 76.4). "TP30 SAFEBOOT" is inherited from R8, where it was accepted.
- **Hidden designators.** 110, set-equal to M3_R9's list.
- **F7 arithmetic.** It holds as stated. The FET terms change the budget by under 1 %, so the AOS data-sheet maxima
  quoted do not decide the verdict.

## 9. Observations (not findings)

- **Owner decision 1's "battery leads the east edge".** J1 takes its wires from the forward edge (entry +y) at x
  12.4–27.6, with BAT+ at the east end. The records read the decision as plan_spine does: the leads run along the east
  wall to J1's forward entry (D-S1-16, ORDERING §7). Worth a sentence to the owner when the list is presented.
- **P-0's closest pair is not deterministic for equal distances.** Rule D's 0.751 mm is attributed to R131.1
  (requalify), J124.1 (step-10 gate) and J121.2 (my run). The figure is stable, the label is not. Same class as
  D-S10-18's R-5 note; for the gate-integrity reviewer.
- **The retired accepted risk.** "Gate-net spacing outside the pyro block … retired for R9, whose rule G covers every
  gate-net item outside U1's courtyard". In KiCad, rule G exempts any whole segment that touches U1's courtyard
  (D-S1-20). The pin-entry stub is held by check_r9 P-0's clipped measure (0.412 mm). Both are in the gate, so the
  retirement holds, but the sentence could say "rule G and check_r9 P-0".
- **The scorecard's hard row X2d is "not measured".** It is met by K-power-pyro finding no BAT_IN / ACT_FET_S copper
  within its 3.5 mm reach. D-S9-07 says "3 mm reach", R9_VALIDATION "3.5 mm". Either way it is above 2.5 mm.

## Appendix A: methods (scripts in the session scratchpad, deleted after the pass)

1. **Facts.** Edge.Cuts bounding box and circles. Key footprints' position, rotation, side and FPID. Pad maps of J1,
   J2, J3, J9, J121, J122, J123, J124. U1 pad nets against `pin_table.tsv`. Every pad and footprint
   `GetLocalClearance()` (none). Via count 579.
2. **Strip.** For y < 22.0, every track, via and pad by layer and net, plus zone fills intersected with the strip
   polygon (SHAPE_POLY_SET). Every footprint whose courtyard top is below 22.0.
3. **Zones.** Name, net, layers, priority and filled area for every zone. Zone connection of every pad with a
   non-inherited setting, on R9 and on R8's committed board.
4. **Vias in pads.** For every pad on F.Cu / B.Cu, a binary search with `SHAPE.Collide` between the via hole circle and
   the pad's effective shape, less the mask expansion. Only TP120's two vias are within 0.1 mm.
5. **MEMS.** B.Cu fill intersected with U4 / U5's body boxes (M-7's), and vias inside them.
6. **Terminals.** J121, J124, J1, J122, R134 and Q124 courtyards and pads on R8 (9c8179b) and R9.
7. **Stitching.** check_r9's own `Ctx`, `rf_path` and `beside` on the R9 board, with each via's side labelled by the
   sign of x relative to the path.
8. **Relief test and kill path.** As in §1, on scratch copies, with TMPDIR in the scratchpad. The kill-path wrapper
   patched `r9_legalise.RF_SEP_PART` in memory only; no repository file was edited.
