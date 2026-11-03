# R9 review pass 2: requirements traceability

Reviewer dimension: requirements traceability. I checked every REQUIREMENTS row (F1–F10 with F10's strip boundary,
P1–P3, M1–M3, "R9 acceptance") against the CAD, the gate and the records of review pass 1's fix-pass board. I also
checked:
- that every pass-1 finding in this dimension is closed or properly dispositioned, and what the fix pass changed;
- that the five owner decisions (`R9_OWNER_DECISIONS.md`) are honoured;
- the pin contract (U1's 100 pins against R8's `pin_table.tsv`, the connector pin maps, the binding note);
- the consistency of REQUIREMENTS, STATUS, ORDERING, MARGIN_PRESCRIPTION, FMEA_REDUNDANCY, AGENTS, README, M3_R9 and
  R9_VALIDATION;
- whether R9_VALIDATION's "R9 deviations for owner acceptance" (C1–C25, parts A–F) is complete, accurate,
  like-for-like and honest.

- **Board:** `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
  `4f841a0e44ebb1829ad7996dfe6320ed527fce1fdb1e5ff11658e0705b44ac14`; netlist `8b0e04ea565ecf1b…`; DRU
  `ea77b791eaa4026d…`; `check_actuators.py` `3f22b273…`. I checked these hashes before and after my runs. Every pcbnew
  measurement ran on a scratch copy with the same SHA. R8's board came from `git show 9c8179b:…` (`cc044ea0…`); the R8
  worktree was not touched.
- **Read-only:** this report is the only repository file I wrote; the board and schematic were never saved.
  `git status --porcelain` hashed `052b2785…` at the start and at the end; the board, netlist, DRU and check_actuators
  hashes were equal at the start and at the end, and the 15 sheets, the project file, the fab package and every record
  hashed the same mid-pass (after my gate run) and at the end. Scripts, board copies and outputs lived in
  `<scratchpad>/r9review/req2/` and were deleted at the end.
- **Labels:** "Inference" marks anything not measured and not taken from a maker document.

**Result: 0 Critical, 0 Major, 6 Minor.**
- **CAD:** every requirement row the CAD can show is met on `4f841a0e…`. `tools/check.sh` exits 0 on my run. My
  check_r9 report equals the bound `step10_evidence/gate/r9.json` rule for rule (all 40 rules' evidence identical, so the
  pass-1 determinism fix holds), and my route_check report equals the bound one but its two binding fields. U1's map
  equals R8's pin table pin for pin; the BOM differs from R8's only in the footprint column of two lines (three parts).
- **Pass 1 (this dimension):** all ten findings are closed or listed. Two have residuals, which are new findings here:
  REQUIREMENTS-05's like-for-like work stopped at the C rows (finding 03), and REQUIREMENTS-04's J122 exception was
  listed for all four pins although only one pin's relief causes the recorded side effect (finding 04).
- **New:**
  - **01:** ORDERING's first paragraph still says no review pass has run on R9.
  - **02:** the fix pass's C98 move changed the bottom support clearance (4.600 mm, R300.2 at (4, 4) → 4.483 mm,
    C98.1 at (42, 59.5)); M3_R9 "Mechanical" and ORDERING §7's sled row still give the old figure.
  - **05:** the binding note carries no z lever arm (null), while M3_R9 and R9_VALIDATION state z −2.06 mm and cite
    the note.
  - **06:** small inaccuracies (not worth a separate edit pass).

## 1. What I ran

| Run | Result |
|---|---|
| `tools/check.sh` (KiCad 10.0.6; GUI session logged in, no shim; `NUMPY_PY` = cfd venv) | **Exit 0** in 5 min 15 s: DRC 0, unconnected 0, parity 0, ERC 0; audit OK; silkscreen 0 points outside; fit OK (J9 mated 0.03 mm; nearest bottom support envelope **C98.1, 4.483 mm from (42.0, 59.5)**; top TP30.1 5.008 mm); plate f1 256.6 Hz (f1 table equal to the evidence); rule-H seeded suite OK; check_r9 OK on all 40 rules; route_check r9 0 failing, 0 allowlisted, 0 leftovers (14 bump windows); check_actuators OK. `r9.json`: every rule's evidence equal to `step10_evidence/gate/r9.json`; `route.json`: equal but `board_sha256` / `bound_by`; 114 information instances, categories as part E |
| pcbnew facts on a scratch copy (Appendix A 1–5) | Outline 46 × 102 mm; Edge.Cuts circles: M3 (4, 4), (42, 4), (4, 98), (42, 98), (42, 59.5), tie holes (15.6, 62), (30.8, 59); 0 local clearance overrides; 583 vias (345 at 0.5 / 0.3, 238 at 0.6 / 0.3; 430 GND); **no via hole within 0.1 mm of any pad opening** (mask expansion 0; nearest 0.107 mm, R63.2's GND via (16.82, 55.3)); test pads: nearest via holes 0.30 mm (TP120, (29.6, 79.6)) and 0.40 mm (TP120, (31.5, 78.2)); every pad inside its courtyard; U4 / U5 bodies: no via, 0 mm² of B.Cu fill (own pin escapes only); stackup F.Cu 0.035 / 0.203 (εr 4.4) / In1 0.030 / 1.03 / In2 0.030 / 0.203 / B.Cu 0.035, ENIG; 35 silkscreen texts all 1.0 mm; designators 139 shown / 110 hidden, the hidden set equal to M3_R9's list and `post_report.json`; no shown designator under 1.0 mm or 0.15 mm stroke |
| RF strip scan (y < 22.0) | Courtyards: 35 parts, all RF (deepest C300 21.955 mm); In1 / In2: GND fill only; F.Cu: GND and the RF, module supply and interface nets; B.Cu: the limiter nets under U30 and the RADIO_TXEN loop at x 25.25 and y 7.8 / 20.15, outside U31's body (x 25.61–35.61, y 9.0–19.0); no non-GND track or via end inside U31's pad hull; the 39 RF parts (strip + R306 / R310 / R313 / R315): no pin on a pyro, arming, actuator, RAW_ACT, BAT_IN, BOOT0 or NRST net |
| Pad maps and pin contract | U1 100 / 100 pads equal `pin_table.tsv` `r8_net` (SHA `bd4687a8…`, 0 differences); J121, J124, J122, J1, J2, J3, J9, J123 as in §5 |
| J122 GND relief trials (scratch copies, native refill with `pcbnew.ZONE_FILLER`; Appendix A 6) | Control (refill unchanged): every GND fill piece identical to the board's. **All four pins relieved:** a new F.Cu GND piece of **0.859 mm², 0 vias, x 18.15–19.13, y 62.61–64.31**, exactly C21's figure. **J122.6 / .9 / .12 relieved, J122.3 solid:** no new piece and no piece with ≤ 1 via; DRC 0 but the scratch folder's 199 `lib_footprint_issues`, 0 unconnected, no starved thermal; route_check r9 0 failing (no sliver or finger), the same 114 information instances; check_r9 K-copper, K-power-pyro, P-0, P-3, M-6 OK; per relieved pin 4 F.Cu and 2 B.Cu spokes (0.5 mm wide, 0.5 mm gap) and 4 In1 spokes (0.4 mm, 0.25 mm gap): about 0.043 mΩ per pin, so about 0.08 mV and 0.15 mW per pin at its 1.9 A (Calc: ρ 1.72e-8 Ω·m, 35 / 30 µm copper, spoke length = the relief gap). Servo GND return solved on the partial copy (`dc_solve`, 0.1 mm, `gnd_servo`'s terminals and window): **0.33 mΩ, 2.5 mV and 0.019 W at 7.7 A** (solid board 0.32 mΩ, 2.4 mV, 0.019 W), 152 vias carrying current, the largest 0.29 A (unchanged) |
| Build and fab bindings | The 15 sheets, netlist, DRU and both variant footprints equal `step10_evidence/build_sha256.txt`; `cost_check.json` `inputs_sha256` equals the BOM `ab3d8171…` and CPL `e879ae2a…` on disk ($109.38, 52 extended, checked 2026-10-26T01:00:11Z); `stock_check.json` bound to the BOM; R8 → R9 BOM diff: the footprint column of the J121 / J124 line (`_SW`) and the J122 line (`_MIR`) only |
| Record sweep | Every R9 figure the fix pass changed (`fix1_handoff.md` §2) searched in REQUIREMENTS, STATUS, ORDERING, M3_R9, R9_VALIDATION, AGENTS, README, MARGIN_PRESCRIPTION and FMEA; ORDERING's coordinates spot-checked (13 parts); evidence JSON keys read |

## 2. Previous pass in this dimension (pass 1 on `fc3d5b34…`)

| Finding | Status on `4f841a0e…` | Evidence |
|---|---|---|
| R9P1-REQUIREMENTS-01 (102 mm cause) | **Closed** | M3_R9 l.35–40, STATUS l.34–37, R9_VALIDATION l.89 and C1, the step-3 handoff l.5–8 name r9_plan's hard row X9 ≥ 5.94 mm, not F10's 5 mm; C1 offers 98 mm (reclassify) and 100 mm (relaxed hard row, F10 met, only the resistor spots shown, the rest Inference). `step3_evidence/option_98mm_f10.txt` supports option (a) (0 illegal parts with the four exempt) |
| -02 (Z4 reported met with vias in TP120) | **Closed** (copper) | No via hole meets any TP opening (nearest 0.30 mm); the scorecard counts every TP* pad (`r9_extra_metrics.py`); R9_VALIDATION l.83–85 restates step 9 as 33 / 17 |
| -03 (check_actuators against owner decision 2) | **Closed** | Part D row D-S1-02 (R9_VALIDATION l.239); "R9 acceptance" reworded (REQUIREMENTS l.122). `git diff 9c8179b`: 191 insertions / 13 deletions, the 15b containment test and the two pins, as the row says |
| -04 (two zone-connection exceptions unlisted) | **Listed**, scope residual | C20 (D30.2, D31.2 and the four DNP shunt lands, pad-level FULL: confirmed), C21 (J122's GND pins), M2's pointer. C21's measured side effect is real (my trial reproduces the 0.859 mm² piece) but it comes from J122.3 alone: finding 04 |
| -05 (R8 comparisons not like-for-like) | **Mostly fixed**, residual | Every C row has an R8 column and "worse" flags; C11 / C14 give 0.1396; C16 gained RAW_ACT → J124.2 and 3V3 → C100; F10 gives R8's 65.98 mm. Not done: part E's R8 figure, C15's routes, the summary's count, R-13 outside F10: finding 03 |
| -06 (C13 omits the thinnest margins) | **Closed** | C13 lists R-10 5.005, M-3 2.007, P-6 1.03, K-copper 0.005 and the via-ring classes; F10 quotes 5.005 mm |
| -07 (F10 swaps the stitching sides) | **Closed** | check_r9 R-7 now reports compass sides: GNSS east 2.38 / west 1.75, radio east 1.70 / west 2.405 (my run), as F10, R9_VALIDATION and C13 say; R8 GNSS east 2.34 / west 2.725 |
| -08 (IGN–BUS1 adjacency) | **Closed** | FMEA l.19 (R9 row, I-4 / V-16), ORDERING §7 l.203; pads OUT 70.73, IGN 75.81, BUS1 80.96, RAW 86.04 (5.08 / 5.15 / 5.08 mm), as written |
| -09 (stall test framing; BAT_IN neck) | **Closed** (one wording slip, finding 06) | F4, ORDERING §5 l.168, R9_VALIDATION l.145, MARGIN P1-9 R9 status and AGENTS say D12 is a CAD check only on R9; BAT_IN's box (29.86–31.06, 89.8–97.75) lies inside J1's courtyard and 0.245 mm from Q120's |
| -10 (stale lines (a)–(g)) | **Closed** | (a) P2 l.67; (b) "R8 acceptance" l.115–116; (c) In2 241.2 / 115.3 / 1037.1 mm², equal to the board's fills; (d) M1; (e) R9_VALIDATION l.148 uses 0.1107; (f) MARGIN R14 R9 clause; (g) M2's RAW_PROTECTED pour and K-legends |
| Observations (battery leads, P-0 tie labels, retired risk wording, X2d reach) | Closed or harmless | Harness text in ORDERING §7 / M3_R9; tie labels deterministic (my r9.json = evidence); "rule G and check_r9 P-0" in Accepted risks; X2d: scorecard 3 mm (X2's reach) and K-power-pyro 3.5 mm are two metrics, both met |

## 3. Requirement walk on `4f841a0e…`

Verdicts: **Pass** = shown in the CAD, the gate or the fab files; **Partial** = the CAD part passes, the rest is open;
**NV** = needs the bench, a flight or firmware.

| Row | Verdict | Evidence / remark |
|---|---|---|
| Sources (one CH1, isolated Blue Jay, 4 servos, on-board MAX-F10S / E22, uplink cannot arm) | Pass | Netlist `8b0e04ea…` unchanged since step 10 (R8's but three footprint fields); RF parts touch no forbidden net; check_actuators OK |
| F1–F3, F5 | Pass (parts), NV | U4 bottom, rotation 180, (12.0, 47.4); M-7 keys the rotation on the revision; roll = −gyro_Y in AGENTS, STATUS, M3_R9, ORDERING §5 and the binding note. The binding note's z lever arm is finding 05 |
| F4 | Pass (CAD, calc), NV | `dc005_*`: 0.80 / 0.16 / 0.26 mΩ; necks 7.89 / 8.15 / 5.18 mm on B.Cu; 12.6 / 12.1 / 20.4 °C; vias 0.47 / 0.61 / 0.22 A; GND return 0.32 mΩ, 2.4 mV; `r9_post_check.txt` holds D12 at 0.1 mm (12.6 / 12.1 / 20.8 °C). The stall test judges the FETs and J122 |
| F6 | Pass (CAD), NV | Circuit unchanged; the hold-up via (38.5, 69.6) is a listed single point (C25) |
| F7 | Pass (CAD, calc), NV | `fire_loop.txt`: 17.70 mΩ copper + 14.40 mΩ FETs = 32.1 mΩ; 7.4 / 4.4821 = 1.651 A ≥ 1.5 A |
| F8 | Pass (CAD), NV | DRU: nine pyro rules (A–G, A2, H), two LC-1 rules, eight fill-margin rules; 0 overrides; terminal pads and legends as M3_R9 (K-legends ownership ≥ 0.31 mm; "2:RAW" J124.2 2.64 / J1.4 3.45 mm); variants = base land with the numbers swapped (pin-1 square moves with pin 1); P-0, P-3, P-6, P-7, P-7b, P-11 OK |
| F9 | Pass (CAD), NV | F9-1: D8 5.22, C80 8.90, C96 5.72, C89 4.79, C95 4.69, R166 8.38, R167 5.59, U9 13.22 mm; J3 west edge |
| F10 strip boundary (owner decision 3) | Pass | Deepest strip courtyard 21.955 mm (C300); every courtyard below y 22.0 is an RF part; R306 / R310 / R313 / R315 outside (y 27.9–29.9) |
| F10 strip contents, RF, pins | Pass, NV | Layer scan above; fence 24 vias on y 22.2, openings 2.15 / 2.10 / 2.15 / 2.50 mm each with its lanes; R-10 6.04 / 5.005 mm; R-13 46.13 mm (U31 to Q124.5); U31's GND pins 0.20 / 0.35 / 0.35 mm of copper from a via (fix pass, `fix1_measure_4f841a0e.json`) |
| P1 | Pass (CAD); parent VEHICLE pending | 46 × 102 mm; holes as listed; VEHICLE row proposed in `fix1_handoff.md` §5, not applied (D-S10-11) |
| P2 | Pass (CAD), NV | Plate 256.6 / 362.9 / 434.8 / 614.9 Hz; supports 4.483 mm bottom (C98.1) / 5.008 mm top (≥ 3.5 / 3.8); M-3 channel 2.007 mm (R124); mode-1 exposure of U4 / U5 in part D. The 4.600 mm figure in two records is finding 02 |
| P3 | Pass | U4 / U5: no via, no B.Cu fill under the bodies; coating, staking and J2 procedure in ORDERING §5 |
| M1 | Pass | Stackup and ENIG as required; CPL 78 + 133 rebuilt, 8 placement-only; U4 40 in JLC stock (2026-10-26 00:59Z) |
| M2 (rules, vias, silkscreen, courtyards) | Pass, except one listing scope | No via hole within 0.1 mm of an opening; no via in a bare contact; 1.0 mm text; courtyards enclose pads. THT GND reliefs: J1.2, J3.1–4, J123.2 relieved; J122.3 / 6 / 9 / 12 solid (C21; finding 04) |
| M2 (clean routing, deviation list) | **Partial** | Gate clean; part A / B empty; the sweep counts equal part C / F (`m2_sweep.json`). Owner acceptance open; list residuals in findings 03 and 04 |
| M3 | Pass (2026-10-26 run) | $109.38 ≤ $126.41; 52 ≤ 52; bound to the current BOM and CPL; rerun within 24 h of ordering |
| R9 acceptance | Not met (as recorded) | Gate items, hard rows and fab binding met; review loop, owner acceptance, commit and the order-day runs open |

## 4. Owner decisions (R9_OWNER_DECISIONS.md)

| Decision | Honoured? | Evidence |
|---|---|---|
| 1. B-spine at 98 mm, fallback 100 / 102 mm "if placement fails"; pyro leads west, battery leads east | Yes, with the choice disclosed | 102 mm is the kill path's result under the plan's own hard row X9; C1 now states that and offers 98 mm and 100 mm. Pyro entries −x (P-11 6.353 mm); J1's entry +y with the leads along the east wall, as `plan_spine.md` l.85 / l.244 proposed and the owner accepted; ORDERING §7 adds that they run below the board and sled (J9's plug closes the top-side wall) |
| 2. Stricter pyro rules, renumbered J121 / J124 (same part and land; check_actuators unchanged) | Yes, with a listed departure | P-1b in rule G; P-3, P-7 (+ P-7b), strict pad rules and LC-1 gated; variants keep part, LCSC, land and nets per pad number; check_actuators' change is part D row D-S1-02 |
| 3. Strip y 0–22.0 (F10 text updated); ≈ 45 mm radio-to-pyro with the keyed-radio test | Yes | F10 text; R-1 21.955 mm; R-13 46.13 mm; ORDERING §5 makes the test a gate before flight |
| 4. Signal vias ≤ 70 with family budgets, stretch 55 | Yes | S4 57; budgets gated at step 7; stretch miss C11d |
| 5. J122 turned (reason recorded); mid support (42, 55.5) if the DC solve holds, else (4, 49.5) | Yes, with a listed agent decision | J122 turned (fit 0.50 against 0.71 mm, `plan_spine.md` §6); the support at (42, 59.5) is part D's D-S3-08 / D-S6-09 row with the mode-1 consequence and the alternatives |

## 5. Pin contract

- **U1:** 100 of 100 pads equal `pin_table.tsv` `r8_net` (0 differences); K-contract's loader-pin list equals the
  binding note's D5 list (PA6 / PA8 / PA9 / PA10 / PC9 / PC11 / PE13 NC).
- **Connectors (pad: net, position):** J124 1 PYRO1_BUS (10.1, 80.96), 2 RAW_ACT (10.1, 86.04); J121 1 PYRO1_OUT
  (10.1, 70.73), 2 PYRO1_IGN (10.1, 75.81); J122 1 / 4 / 7 / 10 SERVO1–4_OUT on y 59.46 west to east, 2 / 5 / 8 / 11
  RAW_ACT on y 62.0, 3 / 6 / 9 / 12 GND on y 64.54; J1 1 BAT_IN (27.62), 2 GND, 3 BAT_SW_SOURCE, 4 BAT_SW_RETURN (12.38);
  J2 1 3V3, 2 SWDIO, 3 NRST, 4 SWCLK, 5 GND, 6 NC; J9 1 CAM_5V, 2 GND, 3 CAM_RX_WIRE, 4 CAM_TX_WIRE; J123 1 PULLPIN_EXT,
  2 GND. Each matches ORDERING §7, the silkscreen legends and check_actuators 1 / 7.
- **Binding note** (`step10_evidence/r9_binding_note.json`): board `4f841a0e…`, netlist `8b0e04ea…`, pin table
  `bd4687a8…`, `changed_from_r8 {}`, R8's constraints, rotation 180, roll −gyro_Y, lever arm x −11.0 mm; z is null
  (finding 05).

No contradiction found in the pin map itself.

## 6. Findings

| ID | Sev. | Requirement | Finding | Evidence | Fix |
|---|---|---|---|---|---|
| R9P2-REQUIREMENTS-01 | Minor (worth fixing) | AGENTS §3 (records match the state, updated in place); "R9 acceptance" (status in STATUS / R9_VALIDATION); records consistency | **ORDERING's opening paragraph still says no review pass has run on R9.** ORDERING l.3: "**R9 is not yet orderable:** no independent review pass has run on it (`r9_plan.md` §5), the owner has not accepted its deviation list … and the worktree is uncommitted." Review pass 1 ran on `fc3d5b34…` and its fix pass made the current board; STATUS l.12–13, README l.5, AGENTS (manufacturing row), M3_R9 l.21–23 and R9_VALIDATION l.6–8 all say one pass has run and pass 2 is next. The conclusion (order R8) stands; the reason given is stale. The fix pass edited ORDERING throughout (l.29, l.61, l.100, l.103, l.115, l.203 name its changes) but not this sentence, which is the first thing read when ordering | ORDERING l.3 (file written by the fix pass, 2026-10-25 18:02 PDT); STATUS l.12–13; README l.5; R9_VALIDATION l.6–8 | "**R9 is not yet orderable:** review pass 1 (0 Critical; its one Major confirmed as Minor) and its fix pass made `4f841a0e…`, but `r9_plan.md` §5 needs two consecutive passes with no Critical or Major (pass 2 is next), the owner has not accepted its deviation list … and the worktree is uncommitted." |
| R9P2-REQUIREMENTS-02 | Minor (worth fixing) | P2 ("≥3.5 mm bottom part/pad clearance around each support"; positions re-derived on the final geometry); records match the board | **The fix pass's C98 move changed the nearest bottom item to a support, but two records still give step 10's figure, part and hole.** C98 now sits beside U11 at (39.275, 64.2) (D-F1-05), so fit_check's nearest bottom envelope is **C98.1, 4.483 mm from (42, 59.5)** (was R300.2, 4.600 mm from (4, 4)). R9_VALIDATION (hard gates l.76, fit row l.155, scorecard row l.348), the scorecard (F3 4.483) and the gate output say so. M3_R9 "Mechanical" l.310 still reads "support clearances 4.600 mm bottom (R300.2 at (4, 4))", and ORDERING §7's sled row l.211 "no bottom part within 3.5 mm of a hole centre: nearest 4.60 mm, R300.2 at (4, 4)". P2 is still met (≥ 3.5 mm); the sled designer is pointed at the wrong hole | My `check.sh`: "nearest bottom/pin envelope: C98.1, 4.483 mm from support (42.0, 59.5)"; `step10_evidence/gate/check_sh.txt` (same line); pcbnew: C98.1's pad 4.548 mm from (42, 59.5), R300.2's 4.682 mm from (4, 4) | M3_R9 l.310: "4.483 mm bottom (C98.1 at (42, 59.5); fc3d5b34 4.600 mm, R300.2 at (4, 4))". ORDERING l.211: "nearest 4.48 mm, C98.1 at (42, 59.5)" |
| R9P2-REQUIREMENTS-03 | Minor (worth fixing) | M2 (deviation list complete and like-for-like); R9_VALIDATION's own rule ("Every C row gives R8's figure on the same metric; **worse** marks a row where R9 is worse"); pass-1 R9P1-REQUIREMENTS-05 | **The like-for-like rewrite stopped at the C rows' first metric.** (a) Part E gives no R8 figure: R8 had 91 information instances (scorecard baseline C2; M2's R8 clause), R9 has 114 (+25 %); REQUIREMENTS-05 named this row. (b) C15's R8 column gives "routes 28 (Y3 / Y4)" against R9's 38 with no **worse** flag, and the owner summary's "worse" list omits it. (c) The owner summary says "in C16 four supply paths", but C16 flags five (RAW_PROTECTED → U7, USB_LIMITED, VLOGIC, RAW_ACT → J124.2, 3V3 → C100). (d) R-13's same-metric R8 figure (65.98 mm, U31 to R131.1) is in F10 only: R9_VALIDATION's R-13 row (l.123) and ORDERING §5's RF-immunity gate (l.158) still compare R9's 46.13 mm (U31 to Q124's drain pad) with "R7 / R8: U31 68.4 mm from J121", another metric | R9_VALIDATION l.181 (summary), l.218 (C15), l.219 (C16), l.246–251 (part E), l.123; ORDERING l.158; REQUIREMENTS F10 (l.60); `step10_evidence/r9_scorecard.md` (C2 114 / 91; Y4 38 / 28); `pass1_requirements.md` R9P1-REQUIREMENTS-05 | Part E: "(R8 91, **worse**)". C15: flag routes 38 / 28 **worse** and add it, with part E, to the summary's "worse" list. Summary: "five supply paths". R-13 row and ORDERING §5: "(R8 on the same metric 65.98 mm, U31 to R131.1; R7 / R8's records gave 68.4 mm from J121)" |
| R9P2-REQUIREMENTS-04 | Minor (worth fixing) | M2 ("Through-hole GND pins use thermal reliefs wherever their spokes are not starved", exceptions listed); deviation list accurate; owner priority 1 | **C21 keeps all four J122 GND pins solid, but its measured cause comes from J122.3 alone.** I reproduced C21's trial exactly: with all four pins on the pours' THT relief, J122.3's ring closes the F.Cu channel beside D120's 3V3 lane and leaves a 0.859 mm² GND piece with no via (x 18.15–19.13, y 62.61–64.31). With **J122.6 / 9 / 12 relieved and J122.3 solid**, no new piece and no piece with ≤ 1 via appear, DRC is clean (0 violations but the scratch folder's library-table items, 0 unconnected, no starved thermal), route_check r9 finds 0 failing instances and check_r9's K-copper, K-power-pyro, P-0, P-3 and M-6 pass, each relieved pin keeps 4 F.Cu, 4 In1 and 2 B.Cu spokes, and the servo GND return solves to **0.33 mΩ (2.5 mV, 0.019 W at 7.7 A) against 0.32 mΩ solid**, the largest GND via current unchanged at 0.29 A. So M2's rule can apply to three of the four pins, and the exception can shrink to J122.3. M2's R9 pointer gives "for the 7.7 A servo return" as the reason, which C21 does not measure (no return solve with reliefs was recorded). The solid pins also carry ORDERING §4's preheat and hole-fill instruction | Relief trials (§1, Appendix A 6): all four relieved: R9_GND_F 23 → 24 pieces, the new one 0.859 mm², 0 GND vias; 6 / 9 / 12 relieved: 23 → 23 pieces, no new small piece, `kicad-cli pcb drc` JSON, route_check 0 failing, `dc_solve` 0.33 mΩ (CG 4023 iterations, residual 9.9e-11); control refill identical to the board; `step10_evidence/dc/gnd_servo.txt` (0.32 mΩ); R9_VALIDATION C21 (l.224); REQUIREMENTS M2 (l.75); R9_DECISIONS D-F1-06; ORDERING §4 l.94 | Relieve J122.6 / 9 / 12 (`r9_pcb.py`'s RELIEVE for those three, the variant D-F1-06 already wrote), keep J122.3 solid; rebuild and re-run the gates (ground gate's islands and copper stages) and `gnd_servo`; shrink C21 and M2's pointer to J122.3 with its measured reason; drop 6 / 9 / 12 from ORDERING §4's hole-fill list. If the loop wants no copper change, put the partial option and these figures in C21 for the owner |
| R9P2-REQUIREMENTS-05 | Minor (worth fixing) | AGENTS §3 (a new binding is built from the binding note); M3_R9 "Firmware" (the note records what the R9 binding must carry); records match their cited evidence | **The binding note carries no z lever arm, although M3_R9 and R9_VALIDATION state one and cite the note.** M3_R9 l.358 and R9_VALIDATION l.160 give "lever arm x −11.0 mm, z −2.06 mm" with `step10_evidence/r9_binding_note.json` as evidence, but the note reads `"lever_arm_mm": {"x": -11.0, "z": null, "z_basis": "fit_check model-box centre (bottom face)"}`. `binding_note_r9.py` fills z only when `--fit` is given (l.65–71), and step 10's command (`r9_step10_handoff.md` l.58), which the fix pass re-ran (D-F1-11), omits it. The value is in the gate's fit report (U4's model box z −2.52…−1.60 mm → −2.06). The z term is small (about 0.22 g at 1850 °/s against 1.17 g in x, Calc), but the firmware binding is generated from this note | `r9_binding_note.json` `imu.lever_arm_mm`; `step10/binding_note_r9.py` l.65–71, l.90; `step10_evidence/gate/fit.json` U4 row `[10.500, 46.150, 13.500, 48.650, −2.520, −1.6]`; M3_R9 l.358; R9_VALIDATION l.160 | Re-run `binding_note_r9.py <board> <out> --fit step10_evidence/gate/fit.json`, re-bind it, and add `--fit` to the step-10 command in the handoff; or say in M3_R9 and R9_VALIDATION that the note carries x only |
| R9P2-REQUIREMENTS-06 | Minor (not worth a separate pass) | AGENTS §2.5 / §3 (records match the board) | **Small record inaccuracies.** (a) ORDERING §5 l.168 puts the RAW_ACT neck "(cut box x 28.65–35.55, y 78.13–79.63) inside Q121's courtyard"; the courtyard is x 30.035–35.425, y 78.555–85.845, so the box overlaps its aft edge but reaches 1.39 mm west, 0.13 mm east and 0.43 mm aft of it (`ordering_facts.json`: box_to_courtyard 0.0, touching). (b) MARGIN P1-9's R9 status (l.214) gives the servo GND return as "2.5 mV"; `gnd_servo.txt`, F4 and M3_R9 say 2.4 mV. (c) M3_R9 l.71 puts the four interface resistors "at y 28.8–29.2"; R313 is at y 29.45 (since D-S7-02). (d) C13 leaves out P-11's wire room, 6.353 mm against D-S1-16's 6.25 mm (margin 0.103 mm, as thin as R-7's 0.095 that C13 lists; R8 6.253), and M-4's J1 courtyard face, 1.855 mm from the forward edge against ≤ 2.0 mm (margin 0.145) | Each line cited; pcbnew courtyards and positions; `gate/r9.json` P-11 (`wire_room_mm` 6.353) | (a) "overlapping Q121's courtyard at its aft edge"; (b) 2.4 mV; (c) "y 28.8–29.45"; (d) add the two to C13, at the next records touch |

### Severity notes

- **None is Major.** Every requirement row the CAD can show is met, the gate passes and no safety rule is weakened;
  each finding is a stale or incomplete record, or a listed exception wider than its measured cause.
- **01–03 and 05 should be fixed before the owner is asked to accept the list:** they are what the owner, the person
  ordering and the firmware binding read. Each is a text edit (05: one script run with `--fit`).
- **04** changes copper (three pads' zone connection), so it needs the build, the gates and the evidence re-run; it is
  cheap in generator terms (the fix pass already wrote the RELIEVE variant of `r9_pcb.py`) and moves three of four pins
  into M2's rule. If the loop prefers no copper change, C21 should at least name the partial option for the owner.

## 7. Deviation list audit (R9_VALIDATION l.165–264)

| Part | Check | Result |
|---|---|---|
| A, B | My `route.json` | allowed 0, stale 0, leftovers 0, missing 0: match |
| E (114 instances) | My `route.json` | pad_end_offcentre 64, segment_inside_pad 11, passes_through_pad 9, width_change_junction 8, extra_bends 8, u_turn 7, power_via_no_gnd 7: match; no R8 figure (91; finding 03) |
| F | `m2_sweep.json` (bound) | chain_detour 18, adjacency 32, adjacency_pad 28, via_step 1, poured_hop 0, routes 38, pad_edge 5, via_fold 34, short_hop 7, bumps 1, margin-free 2 + 7: match |
| C1–C11d against the scorecard | `step10_evidence/r9_scorecard.md` | Rows and figures match; 34 met / 16 missed recounted from the table; every R8 figure equals the scorecard baseline |
| C12, C13 | My `r9.json` | As recorded. C13 could add P-11's wire room 6.353 mm against 6.25 (margin 0.103; R8 6.253) and M-4's J1 face 1.855 mm against ≤ 2.0 (finding 06) |
| C14, C11 | D-S8-20 | Tied together (0.1396 without the plane) |
| C16 | `dc_summary.txt`, M3_R9 table | Five paths flagged worse; the owner summary says four (finding 03) |
| C18 | pcbnew | No via in a bare contact: as stated |
| C19 | `fix1_measure_4f841a0e.json` | Five ACT_GATE / ACT_DRV pads at 0.151 mm from the GND pour: as stated |
| C20 | pcbnew | D30.2, D31.2, C303.2, C305.2, C313.2, C314.2 pad-level FULL: as stated |
| C21 | Relief trials | The 0.859 mm² single-spoke F.Cu piece is real and comes from J122.3's ring; J122.6 / 9 / 12 can take the relief without it (finding 04) |
| C22 | `fix1_measure_4f841a0e.json` | Six clusters 8.05–9.50 mm, J9.2 6.99 mm, the pad list and the thin-piece counts: match |
| C23–C25 | M3_R9 "Power", `fix1_measure` | As stated |
| D | R9_DECISIONS D-F1-01 … -11 | Every fix-pass decision with an owner-visible effect is listed (D-F1-02, -04, -05, -06, -07); D-F1-08 / -09 appear as C24 / C25 |
| New items from the fix pass | Diff of the records against `fix1_handoff.md` | The corridor exception, the copper-gate exceptions, the TP120 vias, C98 and TXEN are all listed or recorded; no unlisted new deviation found |

## 8. Consistency checked (no finding)

- **Identity.** Board `4f841a0e…`, netlist `8b0e04ea…`, DRU `ea77b791…` and check_actuators `3f22b273…` agree across
  STATUS, M3_R9, R9_VALIDATION, REQUIREMENTS, AGENTS, README, the binding note, `cost_check.json` and the gate.
- **Status wording.** "One review pass (0 Critical, its Major confirmed as Minor), pass 2 next, owner acceptance open,
  uncommitted, order R8" is the same in README, STATUS, AGENTS, M3_R9 and R9_VALIDATION; ORDERING l.3 is the exception
  (finding 01).
- **Fix-pass figures.** X5 5, Y1 30, P9 3.37, index 83.8, D_raw 0.80 mΩ / 7.89 mm / 12.6 °C, 583 vias (430 GND;
  345 + 238), USB_LIMITED 85.91 mΩ, RAW_ACT → J124.2 10.14 / 10.06 mΩ, In1 / In2 flashes 456 / 442 of 609 holes, the
  holes row's 4.55 mm (C98.1 pad edge 4.548 mm): equal to the evidence and the board wherever they appear, but
  finding 02's two lines.
- **ORDERING coordinates.** R311.1 (37.75, 14.0), R312.1 (26.55, 7.58), C24.1 (20.33, 50.6), C15.1 (24.2, 49.32),
  TP80 (36.0, 96.8), C88 (38.2, 90.23), TP74 (44.6, 73.0), TP88 (44.7, 75.6), C304 (9.6, 13.97), L1 (40.0, 76.6),
  TP122 (7.58, 63.5), C84 (37.0, 80.5), C121 (33.4, 66.6): all equal the board.
- **Assembly counts.** 76 SMD + 2 jacks + 5 THT = 83 top (J3 counted SMD, J2 no part), 136 bottom, 219 placed;
  14 + 10 test pads; `ordering_facts.json` agrees.
- **Hidden designators.** 110, set-equal to M3_R9's list.
- **Review pass 1 table.** 51 findings (0 Critical, 1 Major, 50 Minor), one row each, matching the nine reports.
- **F7 arithmetic** and the FMEA R9 row's pad sequence and spacings hold as stated.

## 9. Observations (not findings)

- **Does pass 1 count toward "two consecutive clean passes"?** The records say "1 Major (confirmed as Minor)" and
  "pass 2 is next" but not whether pass 1 is the first clean pass of the pair (r9_plan §5; "R9 acceptance"). A
  sentence in R9_VALIDATION "Open" 1 would remove the ambiguity before the owner relies on it.
- **Two metrics, two numbers.** The scorecard reports ACT_FET_S's rise as 20.5 °C (R8 21.5) from its own fit, the
  records and `dc005_fet.txt` 20.4 °C (R8 21.4); and its `check_r9_failing_rules` row is 1 because the survey runs
  check_r9 without the seeded-suite report (P-4), while the gate's run passes 40 / 40. Neither changes a verdict.
- **Progress log.** `fix1_progress.md` dates its last entry "2026-10-26 01:20Z", but the file was last written at
  01:11:51Z, and it gives 70 bound evidence files where `check_records.txt` says 69. The log is not an owner record.

## Appendix A: methods (scripts in the session scratchpad, deleted after the pass)

1. **Facts.** Edge.Cuts bounding box and circles; key footprints' position, rotation, side, FPID and courtyard; pad
   maps of J1, J2, J3, J9, J121, J122, J123, J124; U1's pad nets against `pin_table.tsv`; every footprint and pad
   `GetLocalClearance()`; via count and sizes; zones with filled area; pad and footprint zone-connection overrides;
   silkscreen texts; designator visibility and size.
2. **Vias and openings.** For every pad on F.Mask / B.Mask, the pad's effective polygon grown by its mask expansion,
   against every via hole within 4 mm (`SHAPE_POLY_SET.SquaredDistance`); test pads within 0.5 mm listed.
3. **Supports.** Pad-copper distance to each hole centre; fit_check's envelope figure from my gate run.
4. **MEMS.** Vias and B.Cu fill inside U4's and U5's pad hulls; B.Cu tracks crossing them.
5. **Strip.** Tracks, vias and zone fills below y 22.0 by layer and net; courtyards reaching below y 22.0; RF parts'
   pad nets; RADIO_TXEN's copper on R8 and R9.
6. **Relief trials.** J122.3 / 6 / 9 / 12 (and, separately, J122.6 / 9 / 12) set from FULL to inherited on scratch
   copies, zones refilled with `pcbnew.ZONE_FILLER`, saved in scratch; a refilled unmodified copy as control. GND fill
   pieces per layer with area and GND-via count; copper connections in a ring round each pin; `kicad-cli pcb drc` on the
   partial copy; `tools/dc_solve.py --net GND --source J122:3,6,9,12 --sink J1:2 --amps 7.7 --grid 0.1 --window
   0,50,46,102` on the partial copy, as `gnd_servo.txt`.
7. **Gate.** `tools/check.sh` in place (it only reads the board and writes to a `mktemp -d` folder); its reports
   copied to scratch and compared with `step10_evidence/gate/` key by key; the temporary report folder deleted.
