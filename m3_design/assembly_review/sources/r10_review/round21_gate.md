# R21 gate adversary (Claude)

Target `accfff4`; PCB SHA-256 `0dc847761de94a45cf68b1c82ec91f38e9d4ebb7297abc7108e3df9a454940d3` before and after (verified). **0 Critical / 0 Major / 5 Minor**, all gate gaps shown on probe copies or with the gate's own functions; the committed board passes every stage and the complete check.sh on an unmodified copy (self-tests included) exits 0. Probe material: `.supervisor/r21_gate/` (ignored). Machine-readable twin: [round21_gate.json](round21_gate.json).

## Method

Each seed is an APFS clone of `git archive accfff4`. One fault is applied with KiCad 10.0.7 pcbnew (zones refilled) or a file edit, then the post-board regeneration r10_build.sh runs (budget, hot-plug extract and solve or base-solve reuse, jlc_orient, export_fab --pending, fab_manifest --bind / verify, binding note) and every check.sh checker command with the copy's own tools (DRC all severities + parity, ERC, verify_board, silk_check, r10_parts --check, fit_check, check_r10 full, route_check, fab_manifest --content). For the misses the copy's complete check.sh was run. The seed library leaks removed items (KiCad 10 SWIG otherwise crashes the seed and leaves the copy unseeded), and a failed seed is never gated.

## Findings

**R21-GATE-01 (Minor, new): Single-via sense taps are gated for one pad only (SINGLE_OPEN_TAPS = R402.1): the gate's own single_via_opens finds U2.1, the 3V3 buck's output-sense pin, hanging on one via, and the board passes.** The class D-R20-02 made a gate rule (a regulator losing its sense through one cracked via barrel) is checked for one pad. On the board as committed the 3V3 buck's only output-sense connection is the via (23.20, 68.60): open, U2.1 is left on 0.85 mm of track. With its sense gone the AP63203 loop no longer sees the output; whether it then runs to VLOGIC (up to about 8.4 V) or trips its 0.6 V UVP comparator is not specified by the maker (Inference), and the STM32H743, IMU and barometer on 3V3 are 4.0 V absolute-maximum parts. U401.3 (PORT_LDO_FB) and R87.1 (USB OV sense) are the same class with milder outcomes (PORT_4V8 open-loop as R20-PWR-02; USB over-voltage cut-off disabled); the ILIM opens fail low. A manufacturing / vibration defect path, not a design error on intact copper: Minor, as R20-PWR-02 was. *Fix:* CAD: give U2.1 a second barrel, e.g. the f01b run (24.05, 68.95)-(23.0, 70.0) on B.Cu (or a centred entry the routing lane prefers); a second PORT_LDO_FB via beside (29.75, 13.60) where room allows. Gate: add ('3V3', 'U2.1', ('L1.2',)) and ('USB_LIMITED', 'R87.1', ('U10.6',)) to SINGLE_OPEN_TAPS, and hold every regulator FB / OV / EN tap through a named list whose remaining single points (U401.3 until respin, D-R20-01 R81 / C87, and the fail-low ILIM legs R85 / R430) are exact entries with a measured reason that fail as stale, as POUR_DEBRIS does.

**R21-GATE-02 (Minor, new): The project DRU (hole_clearance 0.25 mm) is looser than JLC's inner-layer PTH-pad hole-to-copper 0.3 mm: D-R20-05's ring removal left J400.2 and J1.2 at 0.251 mm and every check.sh stage passes.** REQUIREMENTS M2 asks for design rules within JLC's limits. Two 1.3 mm terminal holes now sit 0.05 mm inside the published inner-layer limit: J1.2 (battery GND) against In2 RAW_PROTECTED and J400.2 (BAT_SW_RETURN) against In1 GND. Drill wander or smear there gives a RAW_PROTECTED-GND short behind U9 (U9 limits, board dead) or holds EN low (board will not turn on): no hazardous direction, but a yield / DFM-hold risk the gate cannot see because DRC uses the project rule and S-8 exempts these nets. D-R20-05's record states the 0.25 mm but not that it is below the fab limit. *Fix:* Add the f02 DRU rule (inner layers, PTH pads, hole_clearance 0.3 mm), refill (the fill steps back to 0.301 mm at both barrels), re-pin DRU_SHA256 in tools/check_r10.py, rebuild and rebind. Optionally pin the JLC table (via 0.2 / PTH 0.3 inner, PTH 0.28 outer, pad hole-to-hole 0.45) in K-rules so a later DRU edit cannot drop below it.

**R21-GATE-03 (Minor, new): The D-R20-08 west-aft tab keep-out is not held: deleting it returns 12.498 mm^2 of In2 3V3 under the tab band and the complete check.sh exits 0.** The one panel-tab mitigation the polish pass made can be lost in any later regeneration without a signal; the east-tab residuals (RAW_PROTECTED 7.497, PORT_5V3 3.077, RAW 12.244 mm^2) are recorded only in prose, so a regression there is invisible too. The tab plan itself is an open owner decision. *Fix:* K-region (or K-plane): pin each TAB_KEEPOUTS rule area by name, layer and outline, and hold the non-GND inner copper inside each recorded tab band to its recorded figure (west aft 0; east as measured), failing on growth and as stale when a figure improves.

**R21-GATE-04 (Minor, new): The D-R20-09 ESD clamp placement is not held: D440 moved back to F(13.9, 17.2), 6.2 mm of track from J440.3, passes the complete check.sh.** The port ESD clamps (D410 / D411 / D440 / D441, and the camera port's) are effective only near the connector pin; the gate checks their nets and parts (K-contract, S-6) but not where they sit on the path, so the polish improvement can regress silently. *Fix:* K-ports / K-contract: for each port clamp, the copper path from the connector pin to the clamp pad (track_graph) must be <= a recorded bound (e.g. 3.5 mm; current 3.157-3.194 mm on J440, measure J410 / J420 / J9) and must not pass the series resistor first.

**R21-GATE-05 (Minor, new): Fab references are checked only for crossing their own outline: a deleted, mistyped, 0.1 mm or misplaced Fab designator (assembly PDF) passes every stage.** m3_assembly_top / _bottom.pdf are bound fab outputs and the hand-fit / rework reference (C84 is fitted by hand); a missing or wrong designator on the fire-path parts reaches the package unseen. JLC places from the CPL, so the placement itself is unaffected. *Fix:* Extend fab_ref_crossings: every footprint carries exactly one visible Fab text equal to ${REFERENCE} (LS120 "+" / "-" allowlisted), height >= 0.3 mm, and its polygon crosses no other footprint's Fab outline or reference. The committed board passes all three as measured.

Key evidence:

- R21-GATE-01: `single_via_opens` on 26 taps. Single points: U2.1 via (23.20, 68.60); U401.3 via PORT_LDO_FB (29.75, 13.60); R87.1 vias USB_LIMITED (16.00, 28.00) / (22.00, 62.25); R85.1 (14.82, 26.00), R85.2 GND (9.00, 27.84), R430.2 GND (32.30, 59.50); R81 / C87 (recorded). Fix probe f01b closes U2.1 with DRC 0 and route_check 0 failing.
- R21-GATE-02: J400.2 In1 GND 0.251 mm, J1.2 In2 RAW_PROTECTED 0.251 mm hole-to-copper (JLC 0.3 mm). Fix probe f02: 0.301 mm, DRC 0, only the DRU pin and binding need refreshing.
- R21-GATE-03 / -04 / -05: d07, d08, d06a exit 0 through the complete check.sh; d06b / d06d / d06e pass every checker step.

## Polish and round 19 fixes in this lens

| Fix | Verdict | Evidence |
|---|---|---|
| D-R20-02 | confirmed | d01a (FB-tap via dropped, stub left) and d01b (via and stub dropped): K-power "R402.1 ... opening via PORT_4V8 (29.75, 12.60) cuts it off"; d01a also DRC track_dangling and route_check |
| D-R20-02 (scope) | partly | one tap listed; U2.1, U401.3, R87.1 hang on one via on the committed board (R21-GATE-01) |
| D-R20-03 | confirmed | d03: K-copper "0.282 mm^2 piece at (17.50, 34.48) with no via and only U1.74"; POUR_DEBRIS = [] |
| D-R20-04 | confirmed (board); gate incidental | d04b (TP82 1.556 mm further, one segment): M-6 0.86 mm to J440 + silk; d04c (two-bend spur to (11.2, 17.6)): K-legends / DRC silk; d04d (dangling 2.12 mm stub): DRC track_dangling, route_check dead_copper; d04a (stub ending inside the 1.5 mm square pad): passes, not a stub. No rule holds the spur shape; the lengthened spurs are caught only through their neighbours |
| D-R20-05 | confirmed (S-8); partly (fab limit) | d02a: S-8 GND In1 / In2 0.750 and 3V3 In2 0.761 mm from the J121.1 ring; d02b: RAW_PROTECTED In2 0.750 mm from the J400.2 ring; both also DRC lib_footprint_mismatch. Side effect: J400.2 and J1.2 now 0.251 mm hole-to-copper, below JLC 0.3 mm (R21-GATE-02) |
| D-R20-06 | confirmed | d05a (C400 back at F(9.743, 6.048)): "nearer J440's courtyard (0.000 mm, overlap 0.151 mm^2) than its own (0.082 mm)"; d05b (inside J440): overlap 2.907 mm^2 + DRC silk_overlap |
| D-R20-07 | partly | own-outline crossings are covered by test_r20_fab_reference_crosses_its_own_fab_outline (passes in the control check.sh); deletion, wrong text, 0.1 mm text and a neighbour crossing pass (R21-GATE-05) |
| D-R20-08 | confirmed (board); not gated | committed board 0 mm^2 in the band; d07 restores 12.498 mm^2 and passes the complete check.sh (R21-GATE-03) |
| D-R20-09 | confirmed (board); not gated | committed board D440 B(4.45, 19.45); d08 (back at 6.2 mm) passes the complete check.sh (R21-GATE-04) |
| R19-GATE-01..07 / R19-REQ-10 (D-R19-15) | confirmed | 69 round 19 seeds re-run on 0dc84776: 63 caught, 6 pass by design (b09c boundary, b12c, b16d, c02 / c02b legitimate RADIO placements, c03 legitimate third OUT via). The round 19 misses are now caught: b19a (R19-GATE-01, K-lands), b08e (-02, K-actuators / S-4 / fab), b10b (-03, K-plane), b17b / b17c (-04, K-power), c01 / c01b adversary drawing (-05, route_check on its own M2 faults), b21b (-07, K-legends silk allowlist) |

## Polish / new-class seeds

| Seed | Result | First failures |
|---|---|---|
| `c00_control` | passes every step; complete check.sh exit 0 |  |
| `d01a_fbtap_via_drop` | caught: drc, audit, r10, route | DRC: track_dangling / Track has unconnected end / ['Track [PORT_4V8] on F.Cu, length 1.0000 mm']; FAIL K-power: R402.1 (U401's feedback divider top (R20-PWR-02)) hangs on one via: opening via PORT_4V8 (29.75, 12.60) cuts |
| `d01b_fbtap_via_stub_drop` | caught: r10 | FAIL K-power: R402.1 (U401's feedback divider top (R20-PWR-02)) hangs on one via: opening via PORT_4V8 (29.75, 12.60) cuts it off from U401.1/U401.2 |
| `d02a_j121_ring_board` | caught: drc, audit, r10 | DRC: lib_footprint_mismatch / Footprint 'M3_DB125_2P_BK' does not match copy in library 'rocket' / ['Footprint J121']; FAIL S-8: 3V3 copper on In2.Cu is 0.761 mm from the J121.1 inner ring of PYRO1_OUT (minimum 1.0 mm) |
| `d02b_j400_ring_board` | caught: drc, audit, r10 | DRC: lib_footprint_mismatch / Footprint 'M3_DB125_2P_GN' does not match copy in library 'rocket' / ['Footprint J400']; FAIL S-8: RAW_PROTECTED copper on In2.Cu is 0.750 mm from the J400.2 inner ring of BAT_SW_RETURN (min |
| `d02x_j121_outer_ring_removed` | caught: drc, audit (first ring seed (REMOVE_ALL dropped the B.Cu ring flash): caught) | DRC: solder_mask_bridge / Rear solder mask aperture bridges items with different nets / ['PTH pad 1 [PYRO1_OUT] of J121', "Zone 'R10_GND_B' [GND] on B.Cu, priority 0"]; DRC: lib_footprint_mismatch / Footprint 'M3_DB125_2 |
| `d03_u174_pour` | caught: r10 | FAIL K-copper: pour debris: GND fill R10_GND_F on F.Cu has a 0.282 mm^2 piece at (17.50, 34.48) with no via and only U1.74 of its net (R19-RTE-01) |
| `d04a_tp82_dangling` | passes every step (not a fault: the run ends inside the 1.5 mm square pad (d04d is the stub)) |  |
| `d04b_tp82_further` | caught: drc, audit, r10 | DRC: silk_overlap / Silkscreen clearance (board setup constraints silk clearance 0.1500 mm; actual 0.0952 mm) / ['Segment of TP82 on B.Silkscreen', 'Reference field of R463']; DRC: silk_over_copper / Silkscreen clipped b |
| `d04c_tp82_bend` | caught: drc, audit, r10 | DRC: silk_overlap / Silkscreen clearance (board setup constraints silk clearance 0.1500 mm; actual 0.0952 mm) / ['Reference field of R463', 'Segment of TP82 on B.Silkscreen']; DRC: silk_over_copper / Silkscreen clipped b |
| `d04d_tp82_dangling_long` | caught: drc, audit, route | DRC: track_dangling / Track has unconnected end / ['Track [USB_LIMITED] on B.Cu, length 2.1213 mm']; route_check FAIL dead_copper USB_LIMITED B.Cu (9.7, 19.2) {'len_mm': 2.1213} |
| `d05a_c400_ref_r19` | caught: r10 | FAIL K-legends: designator C400 is nearer J440's courtyard (0.000 mm, overlap 0.151 mm^2) than its own (0.082 mm) (R20-MFG-02, AGENTS.md section 3) |
| `d05b_c400_ref_in_j440` | caught: drc, audit, r10 | DRC: silk_overlap / Silkscreen clearance (board setup constraints silk clearance 0.1500 mm; actual 0.0000 mm) / ['Reference field of C400', 'Rectangle of J440 on F.Silkscreen']; FAIL K-legends: designator C400 is nearer  |
| `d06a_fab_ref_deleted` | passes every step; complete check.sh exit 0 |  |
| `d06b_fab_ref_literal` | passes every step |  |
| `d06d_fab_ref_on_neighbour` | passes every step |  |
| `d06e_fab_ref_tiny` | passes every step |  |
| `d07_tab_keepout_drop` | passes every step; complete check.sh exit 0 |  |
| `d08_d440_back` | passes every step; complete check.sh exit 0 |  |
| `f01_u2_fb_second_via` | caught: drc, audit (first fix-probe spot was illegal (GND via at (22.825, 67.825)); no conclusion) | DRC: shorting_items / Items shorting two nets (nets 3V3 and GND) / ['Via [3V3] on F.Cu - B.Cu', 'Via [GND] on F.Cu - B.Cu']; DRC: shorting_items / Items shorting two nets (nets 3V3 and GND) / ['Via [3V3] on F.Cu - B.Cu', |
| `f01b_u2_fb_diagonal` | passes every step (fix probe for R21-GATE-01: passes, U2.1 survives every single via open) |  |
| `f02_dru_pth_inner` | caught: r10 (fix probe for R21-GATE-02: only the DRU pin and binding refresh fail, as designed) | binding-note regen: AssertionError: binding note requires a passing schematic contract; FAIL K-binding: saved board_sha256 differs from native binding-note regeneration |

## Round 19 seeds replayed on 0dc84776

| Seed | Result | First failure |
|---|---|---|
| `a03_rawprot_neck` | caught: r10 | FAIL K-power: U9 OUT: RAW_PROTECTED track 0.310 mm wide, 0.778 mm long on B.Cu (18.75, 79.8)-(19.3, 79.25); minimum 0.7 mm |
| `a03b_batin_neck` | caught: r10, route (regen: hotplug_solve) | FAIL F9-1: C88 local bypass path exceeds qualified R_ohm |
| `a03c_batin_upstream` | caught: r10, route | FAIL K-power: U9 IN: BAT_IN track 0.310 mm wide, 2.687 mm long on B.Cu (17.5, 87.3)-(19.4, 85.4); minimum 1.0 mm |
| `a04_actgate_3v3` | caught: r10 | FAIL K-copper: pour debris: 3V3 fill R19_SEED_3V3_CORRIDOR on In2.Cu has a 7.351 mm^2 piece at (19.94, 73.30) with no via and no pad of its net (R19-RTE-01) |
| `a05_move_pad` | caught: drc, audit, r10 | DRC: lib_footprint_mismatch / Footprint 'M3_AON7524_DFN3x3A' does not match copy in library 'rocket' / ['Footprint Q124'] |
| `a06_pyrogate_3v3` | caught: drc, audit, r10 | DRC: isolated_copper / Isolated copper fill / ["Zone 'R19_SEED_3V3_PATCH' [3V3] on In2.Cu, priority 3"] |
| `a07_del_gnd_partner` | caught: route | route_check FAIL critical_via_no_gnd PYRO1_GATE via (14.4, 53.3) {'gnd_mm': 1.901, 'into_pad': False} |
| `a08_silk_over_pad` | caught: drc, audit, r10 | DRC: silk_over_copper / Silkscreen clipped by solder mask / ["PCB text 'X' on B.Silkscreen", 'Pad 1 [PYRO1_IGN] of R134 on B.Cu'] |
| `a11_rawprot_single_via` | caught: r10 | FAIL K-power: U9 OUT: 1 via(s) on the path; at least 2 required |
| `a11b_batin_via_shrink` | caught: r10 | FAIL K-power: U9 IN: 0 via(s) of at least 1.0 / 0.5 mm on the path; 1 required (further vias >= 0.5 / 0.3 mm) |
| `a12_swap_gate_nets` | caught: drc, audit, r10, route (regen: binding) | binding-note regen: AssertionError: U1.3: board pin differs |
| `a13_dnp_pulldown` | caught: drc, audit, r10, fab (regen: fab_bind, fab_verify) | fab bind: Fab manifest: FAIL: content checks failed (S-4 BOM / CPL, paste openings): the package is not bound |
| `a14_shrink_fire` | caught: r10 | FAIL S-9: PYRO1_IGN fire-path track 0.400 mm wide, 2.425 mm long on B.Cu (11.5, 64.0)-(13.93, 64.0); minimum 0.5 mm (AUD-6) |
| `a15_support_move` | caught: drc, audit, fit, r10 | DRC: silk_edge_clearance / Silkscreen clipped by board edge (board setup constraints silk clearance 0.1500 mm; actual 0.0000 mm / ['Circle on Edge.Cuts', "PCB text 'IGN' on F.Silks |
| `a15b_support_move_legal` | caught: drc, audit, r10 | DRC: silk_edge_clearance / Silkscreen clipped by board edge (board setup constraints silk clearance 0.1500 mm; actual 0.0000 mm / ['Circle on Edge.Cuts', "PCB text 'IGN' on F.Silks |
| `a16_legend_swap` | caught: drc, audit, r10 | DRC: silk_overlap / Silkscreen clearance (board setup constraints silk clearance 0.1500 mm; actual 0.0000 mm) / ["PCB text '1:BAT+' on F.Silkscreen", "PCB text 'SWITCH' on F.Silksc |
| `a16c_legend_swap_bat_ign` | caught: r10 | FAIL K-legends: J1: word legend 'BAT' at (1.310, 48.330) is 1.505 mm from J121 and 21.505 mm from its own connector J1: it must sit beside J1 (nearer it by more than 0.01 mm) |
| `a17_stale_correction` | caught: fab | Fab manifest: FAIL: [Errno 2] No such file or directory: '.supervisor/r21_gate/seeds/a17_stale_correction/m3_design/assembly_review/fab/m3_fab_manifest.json |
| `a18_bom_edit` | caught: fab | Fab manifest: FAIL: content checks failed: S-4 BOM / CPL |
| `a19_stale_fab` | caught: parts, r10, fab | FAIL K-binding: saved board_sha256 differs from native binding-note regeneration |
| `a19b_stale_model` | caught: fab | Fab manifest: FAIL: fabrication package does not match current CAD/export inputs; regenerate it |
| `a20_binding_hash` | caught: r10 | FAIL K-binding: saved board_sha256 differs from native binding-note regeneration |
| `a21_plane_split` | caught: r10 | FAIL K-reference: 1459 critical signal samples lack adjacent reference copper outside their own via antipads, e.g. [('AUX_RX_MCU', 'F.Cu', 22.5, 30.3), ('AUX_RX_MCU', 'F.Cu', 22.6, |
| `a22_rule_severity` | caught: audit, r10, fab | FAIL K-rules: DRC rule severities set to ignore: ['lib_footprint_mismatch'] |
| `a23_text_floor` | caught: r10 | FAIL K-rules: .kicad_pro design rule min_text_height = 0.5, floor 1.0 mm |
| `a23b_text_shrink_only` | caught: drc, audit | DRC: text_thickness / Text thickness out of range (board setup constraints silk text thickness min thickness 0.1500 mm; ac / ['Reference field of R134'] |
| `a25_land_edit` | caught: r10 | FAIL K-lands: M3_AON7524_DFN3x3A (Q124) library file SHA-256 5a8e0db754194fbb4aa6ad071698c3fc742dcf5bd5d53108229013c7069c805a is not the pinned 4442bf5999c46d815f38f6a5e2c163bb656b |
| `a26_q124_return` | caught: r10 | FAIL K-power: Q124 fire return: GND track 0.150 mm wide on F.Cu (15.300, 58.345)-(15.850, 58.345); minimum 0.3 mm |
| `b02_r127_r128_swap` | caught: audit, r10 (regen: binding) | binding-note regen: AssertionError: binding note requires a passing schematic contract |
| `b05_del_r119` | caught: drc, audit, r10, route, fab (regen: fab_bind, fab_verify) | fab bind: Fab manifest: FAIL: content checks failed (S-4 BOM / CPL): the package is not bound |
| `b06_del_r123` | caught: drc, audit, r10, route, fab (regen: fab_bind, fab_verify) | fab bind: Fab manifest: FAIL: content checks failed (S-4 BOM / CPL): the package is not bound |
| `b07_r123_value` | caught: r10 (regen: binding) | binding-note regen: AssertionError: binding note requires a passing schematic contract |
| `b07b_r123_lcsc_only` | caught: r10, fab (regen: fab_bind, fab_verify, binding) | binding-note regen: AssertionError: binding note requires a passing schematic contract |
| `b08_r119_lcsc` | caught: r10, fab (regen: fab_bind, fab_verify, binding) | binding-note regen: AssertionError: binding note requires a passing schematic contract |
| `b08b_r119_value_1k` | caught: r10 (regen: binding) | binding-note regen: AssertionError: binding note requires a passing schematic contract |
| `b08c_r119_lcsc_board_only` | caught: drc, audit, r10, fab (regen: fab_export, fab_bind, fab_verify) | fab bind: Fab manifest: FAIL: [Errno 2] No such file or directory: '.supervisor/r21_gate/out/b08c_r119_lcsc_board_only/export_record.json' |
| `b08d_r131_lcsc` | caught: r10, fab (regen: fab_bind, fab_verify, binding) | binding-note regen: AssertionError: binding note requires a passing schematic contract |
| `b08e_r131_lcsc_source` | caught: r10, fab (regen: fab_bind, fab_verify) | fab bind: Fab manifest: FAIL: content checks failed (S-4 BOM / CPL): the package is not bound |
| `b09a_keepout_actgate_shrink` | caught: r10 | FAIL S-8: GND copper on In1.Cu is 0.300 mm from the via (16.200, 73.300) barrel of ACT_GATE (minimum 1.0 mm) |
| `b09b_keepout_batenable_delete` | caught: r10 | FAIL S-8: RAW_PROTECTED copper on In2.Cu is 0.251 mm from the via (17.100, 82.800) barrel of BAT_ENABLE (minimum 1.0 mm) |
| `b09c_keepout_actgate_edge` | passes (boundary control: keep-out at 1.16 mm still holds S-8 1.0 mm, passes as intended) |  |
| `b10a_3v3_finger_split` | caught: r10 | FAIL K-plane: 3V3 on In2.Cu fills as 2 pieces; the 14.43 mm^2 piece at (22.85, 77.25) has 0 link(s) of >= 0.5 mm outer copper (minimum 2) |
| `b10b_3v3_finger_neck` | caught: r10 | FAIL K-plane: 3V3 on In2.Cu: via (23.100, 78.100) join(s) the main fill only through a neck under 0.5 mm and 0 link(s) of >= 0.5 mm outer copper (minimum 2; R19-GATE-03) |
| `b11_support_radius` | caught: fit, r10 | FAIL M-1: Edge.Cuts circle at (4, 44.3) is not a 3.2 mm hole |
| `b12a_pin_legend_e1` | caught: drc, audit, r10 | DRC: silk_overlap / Silkscreen clearance (board setup constraints silk clearance 0.1500 mm; actual 0.1219 mm) / ["PCB text '1:E1-' on F.Silkscreen", 'Reference field of J121'] |
| `b12b_pin_legend_bat` | caught: drc, audit, r10 | DRC: silk_overlap / Silkscreen clearance (board setup constraints silk clearance 0.1500 mm; actual 0.1048 mm) / ['Rectangle of J1 on F.Silkscreen', "PCB text '2:GND' on F.Silkscree |
| `b12c_word_ign_to_bottom` | passes (by design (THT terminal legends may sit on either face), as round 19) |  |
| `b13a_bom_nonsafety_csv` | caught: fab | Fab manifest: FAIL: content checks failed: S-4 BOM / CPL |
| `b14a_cpl_d9_rot` | caught: fab | Fab manifest: FAIL: content checks failed: CPL rebuilt from JLC footprints |
| `b15a_owner_bom_edit` | caught: fab | Fab manifest: FAIL: content checks failed: S-4 BOM / CPL |
| `b16a_hotplug_hash` | caught: r10 | FAIL F9-1: stale board-derived model inputs |
| `b16b_budget_hash` | caught: parts | parts: r10_parts: stale: parts_budget.json |
| `b16c_manifest_hash` | caught: fab | Fab manifest: FAIL: fabrication package does not match current CAD/export inputs; regenerate it |
| `b16d_docs_hash` | passes (by design: documents are outside check.sh; the gated bindings fail on a forged hash (a20, b16a-c)) |  |
| `b17a_q124_return_via` | caught: r10 | FAIL K-power: Q124 fire return: 1 via(s) on the path; at least 2 required |
| `b17b_port5v3_second_via` | caught: r10 | FAIL K-power: U400 OUT: 1 via(s) on the path; at least 2 required |
| `b17c_3v3_second_via` | caught: r10 | FAIL K-power: U2 OUT: 1 via(s) on the path; at least 2 required |
| `b18a_generated_land_edit` | caught: parts | parts: r10_parts: stale: M3_DB125_2P_BK.kicad_mod |
| `b19a_q124_paste_board_only` | caught: r10 | FAIL K-lands: Q124.1: pad paste margin -0.100 mm, library none (R19-GATE-01: a stencil / mask change goes in the reviewed library land) |
| `b19b_u9_paste_ratio_board_only` | caught: r10, fab (regen: fab_bind, fab_verify) | fab bind: Fab manifest: FAIL: content checks failed (paste openings): the package is not bound |
| `b20_global_mask_expansion` | caught: r10 | FAIL K-copper: via hole at (23.8, 62.95) (GND) is within 0.1 mm of C97.2's mask opening |
| `b21_misleading_legend` | caught: drc, audit, r10 | DRC: silk_overlap / Silkscreen clearance (board setup constraints silk clearance 0.1500 mm; actual 0.1153 mm) / ['Rectangle of J121 on F.Silkscreen', "PCB text 'BATT+' on F.Silkscr |
| `b21b_misleading_legend_clear` | caught: r10 | FAIL K-legends: silkscreen text 'BATT+' (F.Silkscreen, 1.55, 55.40) is not a designator or an allowed legend (R19-GATE-07, AGENTS.md section 3) |
| `c01_second_in_via` | caught: route (the round 19 adversary drawing; its own M2 faults (short segment, 45 deg free node, detour) fail route_check, as round 19) | route_check FAIL short_segment BAT_IN B.Cu (18.9, 88.891) {'len_mm': 0.7071, 'width': 1.0, 'end': (19.4, 88.391)} |
| `c01b_second_in_via_std` | caught: route (as c01) | route_check FAIL short_segment BAT_IN B.Cu (18.9, 88.891) {'len_mm': 0.7071, 'width': 1.0, 'end': (19.4, 88.391)} |
| `c02_radio_legend_move` | passes (legitimate placement inside J420's span; passes since the round 19 WORD_SEAMS entry is gone) |  |
| `c02b_radio_legend_move3` | passes (as c02: legitimate placement passes (not too tight)) |  |
| `c03_third_out_via` | passes (legitimate-fix control: a third U9 OUT via passes (not too tight)) |  |
| `c04_fire_return_third_via` | caught: drc, audit, r10 | DRC: shorting_items / Items shorting two nets (nets GND and PYRO1_OUT) / ['Via [GND] on F.Cu - B.Cu', 'Track [PYRO1_OUT] on B.Cu, length 1.9375 mm'] |

## Fix now

- R21-GATE-02: m3.kicad_dru: add (rule "JLC inner-layer PTH pad hole to copper" (layer inner) (condition "A.Type == 'Pad' && A.Pad_Type == 'Through-hole'") (constraint hole_clearance (min 0.3mm))); refill; re-pin DRU_SHA256; rebuild / rebind. *fills only; seeded f02: DRC 0, route 0, J400.2 / J1.2 0.251 -> 0.301 mm*
- R21-GATE-01: B.Cu 3V3 0.3 mm (24.05, 68.95)-(23.0, 70.0) (or an equivalent centred second link) and SINGLE_OPEN_TAPS += ('3V3', 'U2.1', ('L1.2',)), ('USB_LIMITED', 'R87.1', ('U10.6',)) once R87 has a second path, plus named measured exceptions for U401.3, R81 / C87 and the ILIM legs. *seeded f01b: DRC 0, route 0 failing, U2.1 survives every single via open; gate-only part is checks only*
- R21-GATE-03 / -04 / -05: checks only: pin TAB_KEEPOUTS and tab-band copper; bound port clamp pin-to-clamp copper length; Fab reference presence / text / height / neighbour crossing. *the committed board passes each as measured; seeds d07, d08, d06a/b/d/e fail them*

## Closed or rejected

- d06c (hide a Fab reference): a footprint user text has no hide flag in KiCad 10; the seed left the board byte-identical. Not a representable state.
- d04a (TP82 spur continued 1.0 mm): its end lies inside the 1.5 mm square pad: not a stub; d04d (outside the pad) is caught by DRC track_dangling and route_check dead_copper.
- d02x (first ring seed: SetKeepTopBottom(False) put J121.1 in REMOVE_ALL, dropping its B.Cu ring): caught: DRC lib_footprint_mismatch and solder_mask_bridge.
- JLC classes other than inner PTH hole-to-copper: measured inside JLC limits: PTH outer hole-to-copper none < 0.35 mm, pad hole-to-hole none < 0.6 mm, PTH annular min 0.30 mm, via inner hole-to-copper min 0.250 mm (JLC 0.2), copper-to-edge 0.5 mm, silkscreen 0.15 / 1.0 mm; mask web has no DRC rule (carried from round 19 b20, still caught incidentally by K-copper).
- ILIM opens (R85, R430): TPS2553 current limit follows the ILIM current, so an open leg lowers the limit: fail-safe (Inference), listed inside R21-GATE-01 only as exception candidates.
- R81 / C87 EN chain on three vias: recorded D-R20-01 respin residual; not refiled.

## Limits

- No canonical edit, build, git state change or canonical check.sh; seeded faults only on copies in .supervisor/r21_gate/.
- r10_build.sh / r10_fab.sh not executed; their post-board steps replicated with explicit copy paths. Seeds are post-generation board edits; generators were not re-run (a generator-level reversal would be caught by the same checker steps, plus r10_parts --check where libraries change).
- Hot-plug: the base solve is reused when the extracted electrical signature is unchanged; otherwise the real NumPy solve ran.
- The AP63203 / TPS7A91 behaviour with an open sense pin is an Inference: neither maker specifies it.
- JLC capability figures are the live web page, not a DFM report on this Gerber set.
- Seeding harness: KiCad 10 SWIG deletes a removed item; seedlib now leaks removed items (as RealBoardSeeds.drop) and the pipeline refuses to gate a copy whose seed script failed.
- Other round 21 reports and probe directories were not read.
