# R19 gate adversary (Claude)

Target `1e60441`; PCB SHA-256 `a3144b151b58daf8ba5747def50decc4d1751ad35be478fafc89ef53aa533918` before and after (verified). **0 Critical / 0 Major / 7 Minor**, all gate gaps or tightness issues shown on seeded probe copies; the current board passes every stage and the complete check.sh on an unmodified copy (self-tests included) exits 0. 60 other seeds (every round 18 seed again plus the new classes) are caught or are not faults. No canonical edit, build, git state change or canonical check.sh. Probe material: `.supervisor/r19_gate/` (ignored).

## Method

Each seed is an APFS clone of `git archive 1e60441` (tracked files, fab package included; no round-19 reports). One fault is applied with KiCad 10.0.7 pcbnew (zones refilled), a schematic / circuit.json text edit, or a fab / record file edit. Board seeds then get the regeneration m3_design/r10_build.sh runs after the board, with explicit copy paths (r10_build.sh / r10_fab.sh cd to the git top level): r10_parts --budget-only, r10_hotplug --extract and the NumPy solve, jlc_orient, export_fab --pending, fab_manifest --bind, fab_manifest, the binding note. Where the extracted hot-plug electrical signature is unchanged the base solve is reused with its inputs digest re-pointed (exploratory shortcut); every seed that changes the U9 input feed (a03b, a03c, a11b, c01, c01b) ran the real solve. Then the exact check.sh checker commands run one by one against the copy's own tools (DRC all severities + parity, ERC, verify_board, silk_check, r10_parts --check, fit_check, check_r10 full with --fit, route_check, fab_manifest --content). Controls: the unmodified copy and a regeneration-only copy pass every stage, regeneration reproduces BOM, owner BOM, CPL, corrections, budget, hot-plug inputs / results and binding note byte for byte, and the complete check.sh (self-tests included) exits 0 on the unmodified copy. For the misses the copy's complete check.sh was run.

## Findings

**R19-GATE-01 (Minor, new) — Board-instance pad paste overrides bypass the land pins: Q124 (pyro FET) stencil apertures cut to 26 % pass every check.sh stage.** Seed b19a gives Q124's pads a board-only paste margin of -0.1 mm (library untouched). The exported m3-F_Paste.gbr apertures go from 0.500 x 0.350 to 0.300 x 0.150 mm (25.7 % of the land) and the drain polygon shrinks a further 0.04 mm per side, yet DRC reports no lib_footprint_mismatch, K-lands passes (library hash unchanged) and paste_check passes (it counts openings, not area). Only a reduction that removes an opening is caught (b19b, U9 -60 %). Current board: 0 paste / mask differences from the library (91 thermal-zone and 9 test-pad clearance overrides, governed by K-copper / LC-1). Complete check.sh (self-tests included) on the seeded copy (b19a: exit 0). *Impact:* The R18-GATE-09 chain (library file hash-pinned, placed copy held to it by DRC) does not cover pad-local paste or mask overrides, so a stencil change on a safety land reaches the bound package unseen. A quarter-volume paste deposit on the fire FET's source and gate lands is a solder-joint defect risk in the fire-current path (Inference; no assembly test). *Fix:* tools/check_r10.py K-lands: load each footprint's library copy (pcbnew.FootprintLoad on kilib/rocket.pretty) and require every placed pad's local paste margin, paste ratio and mask margin, and the footprint-level paste / mask overrides, to equal the library's; leave zone connection and clearance overrides to K-copper / LC-1. The current board passes (0 differences of those kinds). Regression seed: b19a.

**R19-GATE-02 (Minor, new) — LCSC codes are checked only by per-part pins: a source-level re-code of R131 (FMEA H-1 cold pull-up) to a 1 kohm part passes the complete gate and erases the ground continuity margin.** Seed b08e re-codes R131 at the generator source (circuit.json replacement, r10_sch.py regeneration, board fields): Value stays "10k", LCSC C11702 is the UNI-ROYAL 0402WGF1001TCE 1 kohm part. The binding note regenerates and every stage passes: check_actuators pins R131's value only and S-4 compares the BOM with the board. With the budget's own divider model the healthy CONT band (207.2-270.2 mV) then overlaps the open band (224.7-291.7 mV); designed: 87.0-115.2 vs 129.2-168.0 mV (Calculation). Pinned parts are caught (R119, R123, R126-R128: b07, b07b, b08, b08b, b02); C127 / C129 have no value or code pin. Complete check.sh (self-tests included) on the seeded copy (b08e: exit 0). *Impact:* The part JLC places is the LCSC code, but outside the per-part pins nothing relates a code to the part value or role, so a wrong code entered at the reviewed source passes. With R131 at 1 kohm the ground continuity reading can no longer separate an intact e-match from an open one, although AGENTS section 2 rule 3 makes that reading a hard ground refusal (Calculation on the seeded board; current board correct). *Fix:* m3_design/check_actuators.py r10 block: pin R131 = C25744 / 0402WGF1002TCE and C127 / C129 = C57112 (value and code); optionally decode the UNI-ROYAL / Yageo resistor MPN value field against the Value for every resistor in the BOM. Regression seed: b08e.

**R19-GATE-03 (Minor, new) — K-plane counts fill pieces, not necks: the 3V3 buck-output finger joined by a 0.30 mm In2 neck passes, where a split piece would need two >= 0.5 mm links.** Seed b10b narrows the In2 3V3 finger that carries the AP63203 output via (23.1, 78.1) to a 0.30 mm neck (deflation bottleneck 1.00 -> 0.30 mm); the fill stays one piece, so K-plane passes, while the full cut b10a fails K-plane for want of two 0.5 mm links. Bounded: the east path (0.54 mm neck) remains. Complete check.sh (self-tests included) on the seeded copy (b10b: exit 0). *Impact:* D-R18-06 / R18-RTE-01 exist because 3V3 islands were joined only by thin copper; a fill neck thinner than one required link passes the rule that demands two 0.5 mm links for a split. Bounded: 3V3 also reaches the plane through the east path; no current-density failure is demonstrated. *Fix:* K-plane: also deflate each non-GND inner fill by PLANE_LINK_W / 2 and treat any landing-via cluster that the deflation separates from the largest piece as a split piece needing the two links (calibrate against the current 0.54 mm east neck before adopting). Regression seed: b10b.

**R19-GATE-04 (Minor, carried, R18-GATE-02 / R18-GATE-03) — Other power rails still have no via (or width) floor: halving the PORT_5V3 buck output vias or removing the 3V3 buck output via passes every stage.** Seed b17b removes one of the two PORT_5V3 buck-output vias ((26.0, 8.0) and its link): the AP63201 output (fault case 1.71 A, camera limit up to 1.25 A, parts_budget.json) reaches In2 through one 0.5 / 0.3 mm via. Seed b17c removes the 3V3 buck's direct In2 via (23.1, 78.1). Both pass every stage: K-power covers only U9 and Q124. Carried from R18-GATE-02 / -03 (D-R18-11 lists the missing width floors, not the vias). Complete check.sh (self-tests included) on the seeded copy (b17b: exit 0). *Impact:* The R18-GATE-03 class (current-carrying layer transitions) is fixed for U9 and Q124 only; the camera / port buck output can lose half its plane transition unnoticed (Inference: one 0.3 mm via at 1.7 A fault current is not shown to fail). *Fix:* Add POWER_PATHS entries for the PORT_5V3 buck output (L400.2 -> its In2 vias, >= 2) and the 3V3 buck output (L1.2 -> In2, naming the F/B-only via (26.4, 79.26) leg as measured), plus width floors from tools/ipc2152.py for the rails D-R18-11 lists. Regression seeds: b17b, b17c.

**R19-GATE-05 (Minor, new) — A legitimate second U9 IN via cannot pass with a one-line update: fire_path keeps the dangling loop as BAT_IN fire copper (r10_parts budget refuses), route_check r10 has no exception list, and K-power is stricter than its record.** Seeds c01 / c01b add a second U9 IN via in parallel with (17.5, 87.3). K-power and F9-1 (real re-solve) accept the 1.0 / 0.5 mm via, but r10_parts' native budget refuses ("BAT_IN: series layer change requires a via-resistance model") because check_r10.fire_path prunes only leaves, so the loop hanging off J1.1 becomes BAT_IN fire copper (1 -> 15 segments, F.Cu + B.Cu); route_check r10 reports track_loop and a 1.66 detour ratio and its profile admits no exception (ALLOWLIST = []); a board-standard 0.6 / 0.3 mm via fails K-power although D-R18-11 records "at least one via of >= 1.0 / 0.5 mm". A third U9 OUT via (c03) passes; moving RADIO (c02 / c02b) costs one WORD_SEAMS entry. *Impact:* The fix R18-GATE-03 points toward (more feed vias) needs gate code changes, and the S-9 / native-budget path identification is wrong for any loop on a fire net's side branch (the budget would also sum non-fire copper if it accepted the layer change). *Fix:* check_r10.fire_path / path_graph: after leaf pruning, drop every block that contains no terminal and meets the rest at one cut vertex (keep only copper on simple paths between the terminal sets); K-power: require >= 1 IN via of >= 1.0 / 0.5 mm and the others >= the 0.5 / 0.3 mm board minimum, as recorded; route_check r10: a measured-reason exception list (or treat parallel power-feed vias as not a loop). The current board's S-9 / K-power evidence is unchanged (no loops). Regression seeds: c01, c01b.

**R19-GATE-06 (Minor, new) — Word-legend identity rests on box gaps with a 0.01 mm tie: RADIO lies in J410's span and passes only through a named seam; BAT and SWITCH pass by 0.040 mm.** RADIO's ink box (30.153, 22.905)-(34.255, 24.055) lies inside J410's courtyard y-span (8.055-24.065) and touches J420 (24.055-40.065) only along its top edge; the gate admits it through the named WORD_SEAMS tie, and by centre distance it is 0.079 mm nearer J410. J410 and J420 are identical terminals with identical pin legends, so the word is their only identity cue. BAT and SWITCH pass by 0.040 mm each (sitting in the 1.19 mm gaps between DB125 courtyards). r10_post places words by nearest gap (label_near), not with its 1.0 mm SUBJECT_MARGIN. *Impact:* A harness assembler can read RADIO as the lower end of the GPS block; swapped GPS / radio harnesses are electrically compatible but defeat telemetry or GPS until found at the pad check. The gate accepts the placement by construction. *Fix:* CAD (r10_post.py): place RADIO inside J420's span, e.g. anchor (32.18, 26.53) (c02b), and delete the WORD_SEAMS entry; gate: compare centre distances with a legibility margin (e.g. 1.0 mm, as SUBJECT_MARGIN) for the GPS / RADIO pair at least.

**R19-GATE-07 (Minor, new) — No silkscreen text allowlist: a contradictory "BATT+" legend beside the igniter terminal passes.** Seed b21b adds a vertical "BATT+" on F.Silkscreen 0.76 mm west of the black J121 igniter terminal; every stage passes. K-legends checks the words and pin legends that should exist, not the absence of others, although AGENTS section 3 limits silkscreen to designators and the named legends. Complete check.sh (self-tests included) on the seeded copy (b21b: exit 0). *Impact:* A legend that names the battery at the igniter terminal (or any other contradicting word) reaches the fab package; R18-GATE-08 pinned the words that exist but not the absence of others. *Fix:* K-legends: every visible silkscreen text (board, footprint text and fields) must be a designator, a TERMINAL_PINS_R10 legend, a word of WORD_SUBJECTS_R10, a PORT_LEGENDS_R10 row, SERVO_HARNESS_NOTE, PINNED_TEXTS or the JLC placeholder; the current board's 40 board texts and 120 visible designators all are. Regression seed: b21b.

## Round 18 fixes in this lens

| Fix | Verdict | Evidence |
|---|---|---|
| D-R18-11 (R18-GATE-05) | confirmed | tools/check.sh: [[ "$BOARD" -ef "$CANON" ]], no skip flag (only tests and records mention it). a19b changes only a fab-manifest input (a 3D-model file), so every earlier stage passes: the copy's check.sh run through a case-variant (M3_DESIGN/...) and through a symlinked folder both reach the fab stage and exit 1 ("fab package unbound, bound to a different board or failing its content checks"); a19 (stale fab after a board nudge) is stopped earlier by r10_parts, F9-1 and K-binding |
| D-R18-11 (R18-GATE-04) | confirmed | a17 (D9 correction +180 deg, CPL 90 -> 270): bind refused, no manifest; a18 (R134 BOM code + hand-written manifest): --content S-4 fails; b13a (C8 / C9 code), b14a (D9 CPL row), b15a (owner BOM C84), b19b (paste) all fail; but aperture size is not checked (R19-GATE-01) |
| D-R18-11 (R18-GATE-02 / -03, K-power) | partly | baseline evidence: IN 15 segments, via (17.5, 87.3) 1.0 / 0.5; OUT 5 segments, vias (20.3, 79.1) and (21.1, 79.1) 0.5 / 0.3 on In2; return 3 x 0.3 mm to (15.85, 57.695) / (15.85, 58.345). Caught: a03, a03b, a03c, a11, a11b, a26, b17a. Not covered: other rails (R19-GATE-04); IN via rule stricter than recorded (R19-GATE-05) |
| D-R18-11 (R18-GATE-06) | confirmed | a23 (floors lowered) fails K-rules; a23b (R134 reference 0.6 / 0.10 mm, floors kept) fails DRC text_height and text_thickness |
| D-R18-11 (R18-GATE-07) | confirmed | a15 (3 mm), a15b (2.55 mm) fail M-3; b11 (radius 1.6 -> 1.4 mm) fails M-1 and fit |
| D-R18-11 (R18-GATE-08) | partly | a16, a16c, b12a, b12b caught; RADIO admitted only by the named seam, BAT / SWITCH by 0.040 mm (R19-GATE-06); extra free text not covered (R19-GATE-07) |
| D-R18-11 (R18-GATE-09) | partly | a25 (Q124 land, library + board) fails K-lands; b18a (generated J121 land) fails r10_parts --check; b19a (board-only paste margins) passes everything (R19-GATE-01) |
| D-R18-11 (R18-MEC-01 / -03) | confirmed | fit output lists J1, J121, J122, J400, J410, J420, J9 at 5.00-5.60 mm; the Plate self-test passes in the complete check.sh of the unmodified copy; R150-R155 not added (disclosed) |
| D-R18-04 (R18-GATE-01, S-8) | confirmed | measured wall gaps: ACT_GATE (16.2, 73.3) and (11.14, 71.7) In1 GND 1.050, In2 RAW_PROTECTED 1.050; BAT_ENABLE In2 RAW / 3V3 1.050 at all three vias; J400.2 In2 1.050, In1 GND 0.551 (kept). a04 (In2 3V3 corridor) is held at 1.050 mm by the keep-out; b09a (keep-out shrunk) fails S-8 (GND 0.300 mm), b09b (BAT_ENABLE keep-out removed) fails S-8 (0.251 mm); b09c (keep-out at 1.01 mm) passes as intended |
| D-R18-06 (K-plane) | partly | baseline 3V3 1466.52 mm2 one piece; b10a split fails; b10b 0.30 mm neck passes (R19-GATE-03) |
| D-R18-02 / D-R18-01 (S-3, K-actuators) | confirmed | b05 (R119 deleted) fails S-3 / S-4 / parity; b06 (R123 deleted), b07 (100 k), b07b (code only) fail S-3 / K-actuators; b08 / b08b (R119 code / value) fail K-actuators (check_actuators.py:513) |
| D-R18-09 (MANUAL_FIT C84) | confirmed | b15a (owner row re-coded, manifest hand-written) fails --content S-4 |

## Fix now

- R19-GATE-01: tools/check_r10.py K-lands: compare each placed pad's paste margin / ratio and mask margin (and footprint-level overrides) with pcbnew.FootprintLoad(kilib/rocket.pretty) and fail on any difference; seed b19a as a regression. *checks only; current board has 0 such differences*
- R19-GATE-02: m3_design/check_actuators.py r10 block: pin R131 C25744 / 0402WGF1002TCE and C127, C129 C57112 (code and value); seed b08e. *checks only; current board meets them*
- R19-GATE-05: tools/check_r10.py: fire_path / path_graph drop terminal-free blocks hanging off one cut vertex; K-power IN vias: >= 1 of >= 1.0 / 0.5 mm, others >= 0.5 / 0.3 mm (the D-R18-11 wording); seeds c01 / c01b. *checks only; current board evidence unchanged (no loops)*
- R19-GATE-07: tools/check_r10.py K-legends: silkscreen text allowlist (designators, TERMINAL_PINS_R10, WORD_SUBJECTS_R10, PORT_LEGENDS_R10, SERVO_HARNESS_NOTE, PINNED_TEXTS, JLC placeholder); seed b21b. *checks only; the current 40 board texts and 120 visible designators all qualify*
- R19-GATE-06: m3_design/r10_post.py: place RADIO inside J420's span (anchor about (32.18, 26.53), as seed c02b) and delete the WORD_SEAMS entry in tools/check_r10.py. *silkscreen-only CAD change (board hash changes; rebuild and rebind); gate cost one entry, as c02 / c02b show*

## Seeds the gate caught or that are not faults

| Seed | Caught by | Note |
|---|---|---|
| `a03_rawprot_neck` | K-power |  |
| `a03b_batin_neck` | F9-1, K-power, route_check local_bump |  |
| `a03c_batin_upstream` | K-power, route_check neck_down |  |
| `a04_actgate_3v3` | passes | R18 s04 again: the In2 3V3 corridor is held 1.050 mm from the ACT_GATE barrel by the D-R18-04 keep-out (S-8 near: none); the seed can no longer create the fault (closed: CAD fix works) |
| `a05_move_pad` | DRC lib_footprint_mismatch, verify_board |  |
| `a06_pyrogate_3v3` | S-8, K-reference, K-region, K-plane, DRC isolated_copper |  |
| `a07_del_gnd_partner` | route_check critical_via_no_gnd |  |
| `a08_silk_over_pad` | K-legends, DRC silk_over_copper, verify_board |  |
| `a11_rawprot_single_via` | K-power |  |
| `a11b_batin_via_shrink` | K-power |  |
| `a12_swap_gate_nets` | S-3, K-contract, K-actuators, DRC shorting_items, DRC solder_mask_bridge |  |
| `a13_dnp_pulldown` | S-4, fab --bind (S-4 BOM / CPL, paste openings), fab --bind, DRC footprint_symbol_mismatch, fab manifest (unbound) |  |
| `a14_shrink_fire` | S-9 |  |
| `a15_support_move` | M-3, M-5, M-6, fit_check |  |
| `a15b_support_move_legal` | M-3 |  |
| `a16_legend_swap` | K-legends, DRC silk_edge_clearance, DRC silk_overlap, verify_board |  |
| `a16c_legend_swap_bat_ign` | K-legends |  |
| `a17_stale_correction` | fab manifest (unbound) | R18 s17 again (D9 correction +180 deg; exported CPL row 90 -> 270 deg): fab_manifest --bind runs jlc_orient --verify-cpl, which fails, so no manifest is written and the fab stage fails |
| `a18_bom_edit` | S-4, fab --content (S-4 BOM / CPL) | R18 s18 again (R134 BOM code C3013496 -> C25744, manifest rewritten by hand): fab_manifest --content S-4 fails ("R134 LCSC Part # 'C25744' differs from native fitted part 'C3013496'") |
| `a19_stale_fab` | F9-1, fab manifest (stale inputs), r10_parts --check (parts_budget.json), K-binding |  |
| `a20_binding_hash` | K-binding |  |
| `a21_plane_split` | K-reference |  |
| `a22_rule_severity` | K-rules, fab manifest (stale inputs), verify_board |  |
| `a23_text_floor` | K-rules |  |
| `a23b_text_shrink_only` | DRC text_thickness, DRC text_height, verify_board |  |
| `a25_land_edit` | K-lands |  |
| `a26_q124_return` | K-power |  |
| `b02_r127_r128_swap` | K-actuators, binding-note regeneration refused, K-binding, verify_board |  |
| `b05_del_r119` | S-3, S-4, K-actuators, fab --bind (S-4 BOM / CPL), fab --bind |  |
| `b06_del_r123` | S-3, S-4, K-actuators, fab --bind (S-4 BOM / CPL), fab --bind |  |
| `b07_r123_value` | S-3, K-actuators, binding-note regeneration refused, K-binding |  |
| `b07b_r123_lcsc_only` | K-actuators, binding-note regeneration refused, K-binding |  |
| `b08_r119_lcsc` | K-actuators, binding-note regeneration refused, K-binding | R119 re-coded to C11702: K-actuators (check_actuators.py:513) and K-binding fail; the R119 identity hypothesis is refuted |
| `b08b_r119_value_1k` | K-actuators, binding-note regeneration refused, K-binding |  |
| `b08c_r119_lcsc_board_only` | K-actuators, fab --bind, DRC footprint_symbol_field_mismatch, fab manifest (unbound), verify_board |  |
| `b08d_r131_lcsc` | binding-note regeneration refused, K-binding | direct schematic + board re-code of R131: caught only through K-binding (the binding-note writer replays circuit.json and refuses, leaving a stale board hash); the source-level b08e is R19-GATE-02 |
| `b09a_keepout_actgate_shrink` | S-8 |  |
| `b09b_keepout_batenable_delete` | S-8 |  |
| `b09c_keepout_actgate_edge` | passes | boundary control: keep-out shrunk to an inscribed 1.16 mm, fill stays >= 1.0 mm from the barrel and S-8 passes, as intended |
| `b10a_3v3_finger_split` | K-plane |  |
| `b11_support_radius` | M-1, M-5, fit_check |  |
| `b12a_pin_legend_e1` | K-legends, DRC silk_overlap, verify_board |  |
| `b12b_pin_legend_bat` | K-legends |  |
| `b12c_word_ign_to_bottom` | passes | IGN moved to B.Silkscreen beside the through-hole J121: passes by design (THT terminals are on both faces); a legibility review item at most, not filed |
| `b13a_bom_nonsafety_csv` | S-4, fab --content (S-4 BOM / CPL) |  |
| `b14a_cpl_d9_rot` | fab --content (CPL rebuilt from JLC footprints) |  |
| `b15a_owner_bom_edit` | S-4, fab --content (S-4 BOM / CPL) |  |
| `b16a_hotplug_hash` | F9-1 |  |
| `b16b_budget_hash` | r10_parts --check (parts_budget.json) |  |
| `b16c_manifest_hash` | fab manifest (stale inputs) |  |
| `b16d_docs_hash` | passes | STATUS.md / AGENTS.md / docs/M3_R10.md board hash replaced: passes; documents are outside check.sh by design, while the gated bindings (fab manifest, binding note, hot-plug, budget) all fail on a forged hash (a20, b16a-c) |
| `b17a_q124_return_via` | K-power |  |
| `b18a_generated_land_edit` | r10_parts --check (M3_DB125_2P_BK.kicad_mod) |  |
| `b19b_u9_paste_ratio_board_only` | fab --bind (paste openings), fab --bind, fab manifest (unbound) |  |
| `b20_global_mask_expansion` | K-copper | board-level mask expansion 0 -> 0.04 mm (U4 webs 0.150 -> 0.070 mm) caught incidentally by K-copper (via hole (23.8, 62.95) within 0.1 mm of the C97.2 / C98.2 mask openings; 0.125 mm at 0 mm expansion): that margin (0.025 mm) equals U4's web margin to JLC's 0.10 mm, so no web below 0.10 mm passes on this board; no direct mask-web rule exists |
| `b21_misleading_legend` | DRC silk_overlap, verify_board | first placement clipped J121's silkscreen (DRC silk_overlap 0.115 mm); the clean placement b21b is R19-GATE-07 |
| `c02_radio_legend_move` | K-legends | tightness probe for R19-GATE-06: only "stale WORD_SEAMS entry" fails (one-entry update) |
| `c02b_radio_legend_move3` | K-legends | as c02 at 3.0 mm: only "stale WORD_SEAMS entry" fails |
| `c03_third_out_via` | passes | legitimate-fix control: a third U9 OUT via on a 0.7 mm run passes every stage (not too tight) |
| `c04_fire_return_third_via` | S-2, DRC shorting_items | legitimate-fix probe drawn on an illegal spot (its via shorted the PYRO1_OUT B.Cu diagonal: DRC shorting_items, S-2): no conclusion; by reading, FIRE_RETURN accepts any extra legal via |

## Limits

- No canonical-tree edit, build, git state change or canonical check.sh; complete check.sh runs only on probe copies.
- m3_design/r10_build.sh and r10_fab.sh were not executed (they cd to the git top level); their post-board steps were replicated with explicit probe paths. r10_sch.py ran once inside a copy (b08e). r10_pcb.py / r10_route.py / r10_post.py were not run: seeds are post-generation edits.
- Exploratory runs reused the base hot-plug solve when the extracted electrical signature was unchanged (digest re-pointed); seeds touching the U9 input feed ran the real NumPy solve.
- KiCad CLI / pcbnew 10.0.7 throughout (the installed 10.0.6 was not used); one kicad-cli process at a time.
- Temperatures, currents and continuity bands are calculations or inferences from the cited project models and maker data, not measurements; seeded misses are prospective gate gaps, not current-board defects.
- Not seeded: pad-local solder-mask margin overrides (same class as R19-GATE-01), In1 GND splits under non-critical copper (R18 s21, by design), supplier-side pad numbering of polarised parts in tools/jlc_easyeda/pads.json (trusted input), stale cost / stock files (outside check.sh by design).
- Other round-19 lenses were not read (independence rule); overlap with them is possible.

Per-seed descriptions, exit codes, seeded-board hashes, first failures and log hashes: [round19_gate.json](round19_gate.json).
