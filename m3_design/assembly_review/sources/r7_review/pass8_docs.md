# R7 review pass 8: requirements conformance and the owner deviation list

Reviewer: independent, pass 8, dimension "requirements conformance and owner deviation list".

- **Board reviewed:** `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
  `c872a3d30509cccf5f78b64cde48ef722ee85c7be23c4848b07ce4082a852de3` (fix pass 7, `fix7_F8_handoff.md`). Root
  schematic `47057f7d…`, `telemetry.kicad_sch` `f5e1df83…`, `m3.kicad_dru` `1674d58b…`, netlist `a9095ac4…`. These
  hashes and `git status` were the same before and after this review.
- **Documents read:** REQUIREMENTS, ORDERING, MARGIN_PRESCRIPTION (P1-9), FMEA_REDUNDANCY (R7 rows), AGENTS, M3_R7,
  R7_VALIDATION, STATUS; `fix7_F8_handoff.md`; `pass7_docs.md`, `pass7_routing.md`, `pass7_verdicts.json`.
- **Method:** read-only. The gate ran on a scratch copy of `assembly_review/` (`<scratchpad>/p8docs/ar/`, same SHA),
  the test suites on a scratch copy of the worktree (`p8docs/repo/`), bytecode writing off. Comparison board: F8's
  start board `f8/sb/m3.kicad_pcb` (SHA `4673c0a0…`, the pass-7 board), copied to `p8docs/p7board.kicad_pcb`. Only
  this report was written in the repository.

## 1. Summary

**Reproduced on the final board:**
- `tools/check.sh` exit 0: DRC 0, unconnected 0, parity 0, ERC 0; audit OK; silkscreen 0; R7 contract OK; routing
  hygiene "0 failing, 45 allowlisted, 0 stale …, 29 leftovers recorded (0 unrecorded, 0 stale), 0 out-of-date route
  figures, 0 removable … exceptions, 1 removable local bumps on critical nets (82 bump windows searched): OK";
  actuators OK; fit OK (J9 mated 0.03 mm, C84 0.11 mm, C76 4.150 mm, TP30.1 5.008 mm).
- Tests (run from each suite's directory): check_shell 2, dc_solve 3, fab_validation 23, fit_check 23,
  maze_clearances 10, procurement 15, r6_check 17, r7_check 35, route_check 50 = 178 OK; quality_audit 21 OK under
  KiCad Python and python3; `test_r5_repair` 1 known error (`routing_lands_spacing`). As STATUS says (199).
- Fab: `fab_manifest.verify_manifest` → 5 outputs bound to `c872a3d3…` (173 inputs); BOM `be711876…`, CPL
  `c68dc2cb…`; `cost_check.json` 2026-10-18T22:02:23Z, $105.98, 52 extended, bound to that BOM/CPL;
  `stock_check.json` 22:03:23Z, short U4 only (U30 159, U31 460, J30/J31 3,299); `check_procurement --cost-only` OK,
  full check fails on U4, as recorded.
- Board counts: 1,724 tracks, 710 vias (`scan.py` 755 + 867 + 102 / 337 + 373); 23 pour trims (F 9, B 13, In2 1);
  3V3_In2 4 pieces (474.53 / 74.51 / 10.33 / 7.46 mm²); 3V3A_In2 one 28.17 mm² island; BAT_IN_B 70.85 mm²; GND_F 41
  and GND_B 34 pieces, 32 held by a single via, none by none (C14); unstitched GND fingers 23 < 0.75 mm / 48 < 1.0 mm
  (C11; the same method gives 21 / 47 on the pass-7 board); 90 hidden designators, the same list as M3_R7; JLC
  placeholder at (22.9, 86.15) on B.SilkS.
- **Deviation list counts reproduce:** A = `ALLOWLIST` 45 (extra_vias 10, chain_detour 9, critical_via_no_gnd 9,
  detour 9, pour_net_hop 5, tiny_jog 2, local_bump 1), every quoted length equal to `route.json` (A34 14.368, A47
  2.505, A48 4.346 / 3.004 mm; A33 66.37 mm / 5 vias); B = `LEFTOVERS` 29 (detour 12, extra_vias 17), every figure
  equal; E = 252 (179 critical: 63 / 34 / 30 / 16 / 12 / 8 / 8 / 6 / 2; 73 non-critical: 31 / 23 / 10 / 6 / 2 / 1);
  the named u_turn, short_layer_hop, passes_through_pad and via_on_track_in_fill instances match location by location.
  C's 25 rows sum to the stated 225; 45 + 29 + 225 = 299.
- **Pass-2 `scan.py` (unchanged) gives 904 instances**, and its 47 chain detours (30 critical) map one to one onto
  A34–A41 + A47 (9), C24 (21) and C25 (17), lengths matching. `route_check --bumps-all` (223 windows) gives exactly
  C27's two `local_bump_review` items plus A48. A route_check diff pass-7 board → final board shows only the removals
  and additions the handoff and part E name.
- **Poured-net hop sweep** (every M → L → M chain between vias with a two-track end, all seven poured nets):
  only A42, A43 (with its 10.71 mm In2 leg), A46 and C23's 3V3 crossing. Nothing unlisted.

**Pass-7 findings in this dimension (section 2):** P7-DOCS-01 (Major) is closed in copper and in the gate:
- via (30.4, 70.25) and its stub are gone;
- `via_on_track` is gated (0 on the final board, 6 in-fill GND instances as information);
- the In2 crossing is listed in C23.

P7-DOCS-02 and P7-DOCS-03 are closed, apart from small residues raised in P8-DOCS-02 (a stale 8.00 mm figure, and a
cost-run list one run short). Owner acceptance is, as recorded, still open.

**Findings in pass 8: 0 Critical, 0 Major, 3 Minor.**
- **P8-DOCS-01 (Minor):** C15 is incomplete. Its stated scope is every sub-0.2 mm gap that fix-pass copper created.
  Fix pass 7's copper made two that are listed nowhere:
  - BAT_IN via (9.45, 109.8) to R123.2 (GND), 0.188 mm on B.Cu. A short would short the pack to GND.
  - CAM_5V_SENSE In2 to the 3V3 via (32.33, 33.042), 0.190 mm.

  The owner summary's "for your attention" list and M3_R7's fix-pass-7 adjacency list miss them too.
- **P8-DOCS-02 (Minor):** records figures and summary claims that are not exact:
  - the 3V3 crossing is quoted at 8.00 mm; it is now 7.18 mm;
  - "299 instances, one per location" counts USB_LIMITED's hump twice (A48 and C24);
  - the owner-summary row for A overstates what the gate re-measures;
  - the C1 summary says the necks cannot be moved by a bounded rework, but two of them are set by ACT_GATE routing
    that was out of scope and was not searched;
  - ORDERING §1 lists one of the two $105.96 runs;
  - M3_R7's "Not covered" for via fields omits the six new crossbar vias, which carry 3.2 A of the 7.7 A.
- **P8-DOCS-03 (Minor, cosmetic):** `legend_subjects` measures the nearest bounding-box gap, so a legend passes if one
  corner is within 6 mm. Two cases follow:
  - J124's fuse note runs 14.5 mm past J124. It ends inside J1's courtyard, 1.1 mm from "J1 BAT LEAD: 15A FUSE".
  - J2's pin table is split across the two faces.

**R7 acceptance (REQUIREMENTS, last section):**
- Met: `check.sh` and its contracts; M3 ($105.98, 52 of 52, 22:02Z, bound); the fab binding; no open Critical or
  Major from this dimension.
- Not met: M1 stock (U4 consignment, documented open); M2 (no owner acceptance; the list is now complete for every
  M2-named routing category I could test, see section 4, but C15 lacks two adjacencies, P8-DOCS-01).

## 2. Closure of the pass-7 findings in this dimension

| Pass-7 ID | Sev. | R7_VALIDATION disposition (l.720–722) | Pass-8 check on `c872a3d3…` | Verdict |
|---|---|---|---|---|
| P7-DOCS-01 | Major | Fixed (F8 `v3pair7`, `route_check`); no owner acceptance | **Copper:** no via at (30.4, 70.25); the F.Cu diagonal (27.85, 68.85)–(30.17, 71.17) is one segment (no stub, no split); In2 (30.17, 71.17)→(30.4, 71.4)→(30.4, 78.25). Both overlap-only joints are gone. **Gate:** the `via_on_track` category exists and is gated on critical nets. It found 3 on the pass-7 board (3V3 ×2, BAT_IN (9.7, 35.5)) and finds 0 on the final board, plus 6 `via_on_track_in_fill` GND instances (the five of P7-DOCS-01 plus (6.85, 40.5)), all information in E. **Records:** C23 lists the crossing with its blockers, neither via in a 3V3 fill (measured: true; (30.17, 71.17) is a junction). Part F's `via_pair_close` text is corrected (22 pairs; the 3V3 pair gone). STATUS and M3_R7 are reworded. The poured-net hop sweep finds nothing else. The stale "8.00 mm" figure is P8-DOCS-02(a) | **Closed** |
| P7-DOCS-02 | Minor | Fixed | (a) C23's fill facts: CAM_5V both vias in CAM_5V_In2, BAT_IN both in BAT_IN_F and R6_BAT_IN_In2, 3V3 neither (measured). (b) Both 3V3 duplicates are deleted (diff: F.Cu (27.35, 44.25)→(29.9, 43.625) incl. the 0.206 mm piece, In2 (30.63, 31.34)→(32.33, 33.04)). Their four vias remain, and the remaining via (27.35, 44.25) is a junction (F.Cu to its pad, two B.Cu runs), not a hop. (c) "Removable but not removed" is re-derived; `--bumps-all` confirms C27. (d) The size is stated like for like (99 entries and rows, 299 instances), with one double count (P8-DOCS-02(b)) | **Closed** (residue Minor) |
| P7-DOCS-03 | Minor | Fixed (records) | (a) The P4-RF-01 row (l.440) now gives the fix-pass-4 board's 23 / 49 and refers to C11; C11's 23 / 48 reproduces. (b) The same-result runs (08:29Z, 12:36Z, 15:30Z, 15:51Z) now agree between ORDERING §1 and REQUIREMENTS M3. The $105.96 runs still differ: P8-DOCS-02(e) | **Closed** (residue trivial) |
| P6-DOCS-04(d) | Minor | Fixed (F8 `r7_post`, `legend_subjects`) | The UART legend is deleted. "J124: 5A FAST / 2S" now starts beside J124, on B.SilkS at x 12.24–13.94, y 97.36–112.95. `check_r7` OK. The measure's weakness and the new placements are P8-DOCS-03 | Closed (cosmetic residue P8-DOCS-03) |

Items still recorded open and not raised again:
- the owner's acceptance (M2) and the IPC-2152 rise limit (C1);
- P4-RF-01 / -02;
- U4 consignment; the forward rail;
- the pass-2-board vibration estimate;
- `test_r5_repair`; the LS120 catalogue entry.

## 3. Findings

| ID | Sev. | Requirement | Finding | Evidence | Fix |
|---|---|---|---|---|---|
| P8-DOCS-01 | Minor | REQUIREMENTS M2 ("every review-only residual is listed, with location, rule, measured reason …"; "What review checks: … adjacency on every net"); R7_VALIDATION C15's own scope (l.1011: "the edge gaps under 0.2 mm that fix-pass copper created or a review raised; 40 instances") | **Two sub-0.2 mm gaps made by fix pass 7's copper are in no list.**<ol><li>**BAT_IN via (9.45, 109.80)**, one of `necks7`'s six crossbar vias (0.6 / 0.3 mm), is **0.188 mm** edge to edge from **R123.2 (GND)** on B.Cu. R123 is ACT_EN's 100 kΩ pull-down, 0402, bottom side; pad (10.22, 110.10), 0.566 × 0.54 mm. A short puts BAT_IN (J1.1, the pack behind the external 15 A fuse) on GND: the board and the servo feed go down until the fuse opens. It cannot fire the channel. Etch shorts are screened by E-test, and the via is plugged and masked, so a solder bridge from R123.2 is improbable (Inference). The via ring also reaches 0.02 mm into R123's courtyard (x 9.73).</li><li>**CAM_5V_SENSE In2 diagonal (30.335, 35.835)–(34.785, 31.385)** (`sense7`) is **0.190 mm** from the 3V3 via (32.33, 33.042). That via is the one `dup7` kept when it deleted the In2 duplicate. A short ties the camera-5V sense ADC line to 3.3 V (a wrong reading). It is on In2, so only a laminate defect can make it.</li><li>Neither is in C15 (#1–#40), in M3_R7's "fix pass 7's copper" list (l.638–642) or in F8's `newgap` list (handoff §3). The owner summary's "New in fix pass 7, for your attention" (l.840) names three gaps where a short would put a higher rail on 3V3 or an MCU pin. It does not name this BAT_IN–GND gap, the only fix-pass-7 gap where a short would put the pack across GND.</li></ol>Every other sub-0.2 mm gap from fix-pass-7 copper is listed (#18, #35–#40). IMU_INT1's 0.191 mm to the SERVO1/2_MCU vias is on R6's line (the new segment lies on the old one), so it is not new | **Scan:** `p8docs/newgap.py p7board.kicad_pcb ar/m3.kicad_pcb 0.25` (every track and via on the final board that is not on the pass-7 board, against all other-net tracks, vias and pads; `GetEffectiveShape().Collide` bisection to 0.5 µm). Output lines `0.188 BAT_IN via (9.450,109.800) B.Cu GND pad R123.2` and `0.190 CAM_5V_SENSE track (30.335,35.835)-(34.785,31.385) In2.Cu 3V3 via (32.330,33.042)`. The same run reproduces C15's #18 0.169, #37 0.171, #38 0.172, #36 0.173, #35 0.175, #39 0.175 and #40 0.182.<br>**Hand check:** R123.2's west edge at x 9.937. Centre-to-edge distance √(0.487² + 0.03²) = 0.488, minus the 0.3 mm ring = 0.188. Diagonal to the via centre: \|(1.9947)(−0.7071) − (−2.7936)(0.7071)\| = 0.565, minus 0.3 and 0.075 = 0.190.<br>**Parts:** netlist R123 100k C25741 (ACT_EN / GND); `fpside.py`: R123 on B, crtyd x 9.73–11.56. Diff (`diff.txt`): `+V ('BAT_IN', 9.45, 109.8, 0.6, 0.3)` | Add both to C15 (42 instances; C 227, total 301), to M3_R7's fix-pass-7 list and to the owner summary, with the BAT_IN–GND failure mode. Optionally move the via about 0.07 mm west (x ≤ 9.39) for 0.25 mm, if it stays inside both fills. Extend the records agent's re-measurement from "the key pairs" to F8's whole added set (the pass-7 board as the reference) |
| P8-DOCS-02 | Minor | Document accuracy; the owner summary as the decision record (M2: "measured reason"; "like for like", P7-DOCS-02(d)) | **Several figures and summary claims are not exact.**<ol type="a"><li>**3V3 crossing length.** C23 (l.1019) says "3V3 In2 run via (30.17, 71.17) → via (30.4, 78.25), 8.00 mm", and the P7-DOCS-01 disposition (l.720) and M3_R7 (l.543) also say 8.00 mm. On the final board the run is 0.325 + 6.85 = **7.18 mm**. 8.00 mm was the deleted run from (30.4, 70.25).</li><li>**Double count.** "299 instances counted one per named location" (l.802) counts USB_LIMITED's B.Cu hump C98.1 (33.1, 26.15) → (30.8, 27.85) twice: as A48 and as C24's last row (l.1114).</li><li>**Row A of the summary table** (l.797): "its reason re-measured on every run (except A42–A46's probed blockers and A48's GND reason)". The gate re-measures only the figures of A15–A33. The raster-search results in their reasons are not re-run (l.866; M3_R7 "Reason audits"), and neither is the module-keep-out reasoning of A16 / A18 / A27.</li><li>**C1 in the summary** (l.824): "Each neck is now set by something a bounded rework cannot move: … Q120's gate pad and R120; ACT_GATE's In2 crossing". C1's own row and F8 §4 say that moving the actuator gate routing "was outside fix pass 7". ACT_GATE's In2 run (1.1, 93.9)–(7.7, 100.5) is routing, not a part, and was not searched. The summary states impossibility where the record says out of scope.</li><li>**Cost runs.** REQUIREMENTS M3 lists two $105.96 runs (2026-10-17 21:01Z and 2026-10-18 02:59Z). ORDERING §1 lists only "the 02:59Z run".</li><li>**Via fields.** M3_R7 "High-current copper … Not covered" (l.1027) names only the FET via fields. The six new crossbar vias are also a 7.7 A layer change. This review's solve puts 3.21 A (42 %) through them: (9.95, 104.05) 1.28 A, (10.2, 107.8) 0.57 A, (9.45, 109.8) 0.45 A, (9.45, 111.3) 0.39 A, (9.45, 112.8) 0.28 A, (9.45, 114.3) 0.24 A. The FET field's highest is 1.53 A at (6.8, 91.0). That is comparable and not alarming (Inference: a 0.3 mm via with 20 µm plating has about the cross-section of a 0.6 mm 1 oz track), but it is not stated.</li></ol> | (a) `p8docs/near.py ar/m3.kicad_pcb 30.2 71.0 2.0 3V3`: `In2 (30.17,71.17)-(30.4,71.4) len 0.325`, `In2 (30.4,71.4)-(30.4,78.25) len 6.850`. `hops.py`: `3V3 … In2.Cu hop 7.18 mm (30.17, 71.17) … -> (30.4, 78.25)`.<br>(b) `route.json`: `local_bump USB_LIMITED B.Cu (33.1, 26.15) path 4.346`; `scan.py` chain_detour at the same run (ids 753, 751, 765, 750).<br>(c) R7_VALIDATION l.797 against l.866.<br>(d) l.824 against l.998 (C1 row) and `fix7_F8_handoff.md` §4 ("moving actuator gate routing was out of scope").<br>(e) REQUIREMENTS l.76; ORDERING l.28.<br>(f) `p8docs/dcv/dc_via.py` is `tools/dc_solve.py` plus a per-via barrel-current print. `--net BAT_IN --source J1:1 --sink Q120:5,6,7,8,9 --grid 0.1` gives R = 3.03 mΩ (equal to the records), then the via list above (`dcv/bat.txt`) | (a) Write 7.18 mm. (b) Count the hump once, or note the overlap. (c) Add "and the raster-search and keep-out reasons of A15–A33" to the exception. (d) Say "set by ACT_GATE's routing and Q120 / R120, not searched in fix pass 7". (e) Align ORDERING. (f) Name the crossbar vias and their currents in "Not covered" |
| P8-DOCS-03 | Minor (cosmetic) | REQUIREMENTS M2 ("a legend about a part within 6 mm of that part's courtyard"); AGENTS §3 silkscreen; F8 ("unambiguous pin legends") | **`legend_subjects` checks the nearest gap between bounding boxes, so a long legend passes when one corner is near its part. Two of fix pass 7's placements read across neighbouring parts.**<ol><li>**"J124: 5A FAST / 2S"**, B.SilkS, 90°, mirrored. Ink x 12.24–13.94, y 97.36–112.95; J124's courtyard ends at y 98.44, so 14.5 mm of the legend lies beyond it. Read from the bottom it starts at the J124 end. Its "… 5A FAST / 2S" tail lies inside J1's courtyard (x 11.90–34.09, y 104.86–116.14), 1.4 mm from J1.4 (15.38, 110.4) and about 1.1 mm above "J1 BAT LEAD: 15A FUSE" (x 9.70–27.90, y 114.08–115.77). So the two fuse ratings stand side by side at J1's corner. Each names its part, so this is a reading aid, not an error.</li><li>**J2's pin table** (a top-side TC2030 pattern) is split across the faces: "J2 1:3V3 2:SWDIO" on B.SilkS (x 39.58–41.27, y 59.62–73.35) directly under "J2 3:NRST 4:SWCLK" on F.SilkS (x 39.58–41.27, y 58.29–73.30), and "J2 5:GND 6:NC" on F.SilkS runs from beside J2 (y 79.76) to y 91.20, 2.2 mm from J121's courtyard (J2's courtyard ends at y 80.19). Before fix pass 7 all three rows were on B.SilkS.</li></ol>P6-DOCS-04(d)'s substance is fixed: no legend now names a missing part, and each lies near its part. What remains is that M2's "within 6 mm" holds only under the nearest-point reading | `p8docs/silk.py`, `silkang.py`: text, layer, angle, mirror and bounding boxes, with the pass-7 board compared (`silk_p7.txt` against `silk_final.txt`). `fpside.py`: courtyards of J1, J2, J9, J121, J122 and J124. `tools/check_r7.py` l.831–858 (`_box_gap(ink, box)`, `LEGEND_REACH` 6.0) | State the measure in M2 / `check_r7` (for example the legend's anchor or whole ink within 6 mm), or accept the nearest-gap reading explicitly. Put J124's fuse note horizontally beside J124, and keep J2's rows on J2's face. No copper change |

Counter-arguments considered:
- **P8-DOCS-01:** DRC-legal at 0.15 mm, E-test-screened, and C15 says inherited R6 gaps are not listed one by one.
  But both gaps are new copper of fix pass 7, inside C15's stated scope. One has the worst short consequence of any
  fix-pass gap (battery to GND). Minor, not Major: adjacency is a review item, not one of M2's named
  routing defects. The gaps are legal, and a bridge onto a plugged via is improbable.
- **P8-DOCS-02 / -03:** documentation and cosmetic. No item changes a decision the owner must make.

## 4. Audit of "R7 deviations for owner acceptance" (R7_VALIDATION l.786–1223)

| Part | Check | Result |
|---|---|---|
| Owner summary | Counts; the 10 §3 items / 12 instances; removable list; ordering prerequisites | Counts and the §3 list are accurate. A6–A14 have no GND via within 1.5 mm (`nognd_audit` 0 out of date); A8; C1's necks match M3_R7. The removable list matches `--bumps-all`, C23 and the cosmetic items. The "for your attention" list misses the BAT_IN–GND gap (P8-DOCS-01). Wording residues: P8-DOCS-02(b)–(d) |
| A (45) | Entry by entry against `ALLOWLIST` / `route.json` | Match. A34's new reason checked against the geometry: 3V3A's B.Cu x 40.1 run into C11.1 closes the north side. A47's both vias lie in the 28.17 mm² 3V3A_In2 island. A48's redraw candidate `[[33.1,26.15],[33.1,26.9],[32.15,27.85],[30.8,27.85]]` equals the gate's |
| B (29) | Against `LEFTOVERS` | Match; B7 gone; B9 92.46, B23 34.94 mm |
| C (25 rows, 225) | C11, C14, C15, C23, C24, C25, C27 against independent scans | C11 23 / 48 and C14 32 of 75 reproduce. C23's facts are true (one stale length, P8-DOCS-02(a)). C24 / C25 are complete against `scan.py` (21 + 17). C27 is exact. **C15 is missing 2 (P8-DOCS-01)** |
| D (18) | Status line | Unchanged; holds |
| E (252) | Counts and attributions against `route.json` | Match, category by category and critical / non-critical. The pass-7 → final instance diff shows only the named changes: the 3V3A hop's chain detour, its x 35.61 extra bends, BUZZ_DRV's extra bends, USB_LIMITED's power via and BAT_IN's 0.74 mm hop added; the 4 bumps, 3 `via_on_track`, ACT_EN's hop, 2 3V3 hops and their 2 power vias, CAM_FAULT_N's U-turn and ARM1_SENSE's pass-through removed |
| F | `scan.py` reproduced (904, 549 critical) | Counts and the category list match. Chain detours 47 = A34–A41 + A47 (9) + C24 (21) + C25 (17), by location and length. The `via_pair_close` statement holds |

**Would acceptance make M2 true?**
- **Yes, for M2's named routing categories:**
  - every gated instance is allowlisted with figures the gate re-measures;
  - every chain detour, poured-net hop and local bump an independent scan finds is in A, C23, C24, C25 or C27;
  - the gate now holds the two classes pass 7 found missing (`local_bump`, `via_on_track`).
- **No for adjacency:** the review item C15 omits two fix-pass-7 adjacencies (P8-DOCS-01). The owner would accept
  a C15 that understates fix pass 7's adjacencies.
- **Not a gap:** single crossings within `VIA_SLACK` on nets without a pour are judged by M2's own definition, as
  pass 7 noted.

## 5. Requirement walk (final board `c872a3d3…`)

Verdicts:
- **Pass:** shown in the CAD, gate or fab files.
- **Partial:** the CAD part passes and the rest is open.
- **NV:** needs the bench, flight or firmware.

| Item | Verdict | Evidence / remark |
|---|---|---|
| Sources: one primary pyro channel, isolated Blue Jay, 4-servo limit | Pass | `check_actuators` OK; `check_r7` OK |
| Sources: on-board MAX-F10S / E22-900MM22S, JLC-assembled; uplink cannot arm | Pass (CAD) | BOM C30005563 / C5333985; `rf_part_coverage` and pad-level net check OK; no schematic change since fix pass 6 |
| F1–F3, F5 | Pass (parts) | Circuits unchanged (root schematic `47057f7d…`) |
| F4 | Partial | DC solve on the final board: RAW_ACT 3.74, BAT_IN 3.03 (reproduced here: 3.03 mΩ), ACT_FET_S 1.19 mΩ. IPC-2152 necks 3.00 / 2.65 / 3.82 mm, rises 38 / 44 / 30 °C (no plane), recorded. No rise limit is set (C1, owner). The stall test is bench work. Crossbar via currents are not recorded (P8-DOCS-02(f)) |
| F6, F7, F9 | Pass (CAD), bench NV | Circuits unchanged. Pyro copper unchanged: the diff touches no PYRO1_* track; ARM1_SENSE is only split at R180.1's centre (17.28, 93.55), and that pad is ARM1_SENSE |
| F8 | Pass (CAD), bench NV | DRC 0 under the nine pyro rules. ARM / IGN / BAT / CAM / SWD / SERVO / PULL / GNSS / RADIO legends present; J1 "1:BAT+ 2:GND 3:SW 4:SW" on top. Legend placement residue: P8-DOCS-03 (cosmetic) |
| F10 | Pass (CAD), bench NV | R7 contract OK (fence 21 vias, line-side gaps 3.9 / 2.65 / 1.55 / 1.55 mm, launches 1025 / 1025, module ground complete, strip reach 3.14 / 3.49 mm). Nothing in fix pass 7's diff lies in the RF strip (y < 23.5) |
| P1 | Pass | 46 × 118 mm |
| P2 | Pass (CAD) | 5 supports; C76 4.150 mm; TP30.1 5.008 mm. BUZZ_DRV's new B.Cu run passes the mid-span hole (4, 64) 0.517 mm from its edge (a track, not a part; the old run was 0.775 mm away on the other side). The vibration estimate is from the pass-2 board (Inference, recorded) |
| P3 | Pass (procedure) | Unchanged |
| M1 | Pass, except U4 stock (the allowed exception, open) | Stock short U4 only |
| M2: JLC rules, via-in-pad, silkscreen, courtyard | Pass | DRC 0 (all severities). In-pad vias only at TP122 and J2.1 (`check_r7`). All legends 1.0 mm / 0.15 mm. `legend_subjects` OK under its nearest-gap measure (P8-DOCS-03) |
| M2: clean routing | **Not met (owner acceptance)** | The list is complete for the named routing categories. C15 is short by two (P8-DOCS-01) |
| M3 | Pass | $105.98, 52 of 52, 2026-10-18 22:02:23Z, bound to BOM `be711876…` / CPL `c68dc2cb…`. Rerun within 24 h of ordering |
| R7 acceptance | Not met | M2 (owner) and U4 consignment. No open Critical or Major in this dimension |

## 6. Document consistency (beyond the findings)

These agree with one another and with the board:
- **Board SHA** `c872a3d3…`: STATUS l.18, M3_R7 l.4 / l.296, R7_VALIDATION baseline and l.788, AGENTS §1, the fab
  manifest.
- **Gate line and test counts:** STATUS, M3_R7 "Checks on the final board" and R7_VALIDATION "Final-board results"
  match this run (178 + 21 = 199).
- **Counts:**
  - 1,724 / 710; 23 trims (9 / 13 / 1); 90 hidden;
  - 45 / 29 / 25 rows (225) / 252 (179 + 73);
  - 99 and 299; 10 §3 items / 12 instances.

  STATUS, M3_R7 l.7 and R7_VALIDATION agree.
- **REQUIREMENTS M2 "What the gate enforces"** against `route_check.py`:
  - `local_bump`: BUMP_EXCESS 0.3, BUMP_RATIO 1.15, BUMP_BACK 0.05, BUMP_SAVE 0.15, BUMP_MAXSEG 8, the strict
    `RedrawCheck` extras;
  - `via_on_track` in the hygiene list;
  - the same-heading rule;
  - the true outline and holes at 0.5 mm;
  - `legend_subjects` 6 mm.

  AGENTS §3 agrees.
- **MARGIN P1-9:** the R7 status line carries the fix-pass-7 necks and rises (2.65–3.82 mm; 38 / 30 / 44 °C).
- **ORDERING:**
  - §1: cost and stock as the JSONs; U30 159;
  - §3: placeholder (22.9, 86.15), present on the board;
  - §4: 96 top + 123 bottom = 219 placed parts.
- **FMEA:** I-11 / V-19, unchanged.
- **M3_R7:**
  - the DC table and the fix-pass-7 stage list match the handoff and the diff;
  - the hidden-designator list matches the board exactly (R121, R123 and U13 hidden; C151, R157 and TP88 shown).
- **STATUS** "Open items" match R7_VALIDATION "Open after fix pass 7".

## 7. Measurements and reproductions

All in `<scratchpad>/p8docs/` (scratchpad = `<scratch>`):
- **Gate:** `gate.log`, `gate/` (`route.json`, `r7.json`, `fit.json`, `drc.json`, `erc.json`, `audit.json`).
- **Tests:** `runtests2.sh` → `tests2.txt`. (`tests.txt` is a first run from the wrong working directory; ignore it.)
- **Scans:**
  - `scan_final.json` (pass-2 `scan.py`, unchanged, vs `rg/r6.kicad_pcb`);
  - `route_bumps.json` (`--bumps-all`);
  - `route_p7.json` (the final tool on the pass-7 board, for the instance diff).
- **Board diffs and gaps:**
  - `diff.py` → `diff.txt` (copper diff, pass-7 → final);
  - `newgap.py` (foreign gaps of the added copper);
  - `near.py`, `zones.py` (fill membership, pour pieces, trims);
  - `fingers.py` → `fingers.txt` (C11 at 0.75 / 1.0 mm, relief rings not excluded);
  - `gndpieces.py` (C14);
  - `hops.py` (poured-net M → L → M sweep);
  - `silk.py`, `silkang.py`, `fpside.py` (legends, hidden designators, courtyards).
- **DC:** `dcv/dc_via.py` (copy of `tools/dc_solve.py` with a per-via current print) → `dcv/bat.txt`.
- **State:** `status_before.txt` / `status_after.txt` identical; board, schematic, rules and netlist hashes unchanged.
