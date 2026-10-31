# Round 19 fix pass: gate lane (hand-back)

Scope: the brief `.supervisor/r19_fix_gate_brief.md`, checks only. It covers R19-GATE-01, -02, -03, -04 (rest), -05,
-06 (rest) and -07, R19-REQ-10, R19-RTE-01's gate note, R18-MEC-01 (rest) and the AUX feed via (the CAD hand-back's
open item).
- Edited: `tools/check_r10.py`, `tools/critical_reference.py`, `tools/plate_model.py`,
  `m3_design/check_actuators.py` and `tools/test_r10_check.py`.
- Appended: D-R19-15 at the end of `R10_DECISIONS.md`.
- Not touched: `tools/route_check.py`, since the CAD lane's `PARALLEL_VIAS_R10` (D-R19-09) is already the
  measured-reason list R19-GATE-05 asks for.
- No CAD, generator or docs edit, and no git state change. HEAD is `6628488`, the CAD pass; everything here is
  unstaged.
- Machine-readable twin: `round19_fix_gate.json`.

**Board unchanged:** the PCB SHA-256 is `50a39de5b76dec3cb58bbb1b0ab528fd4d65098de9dfe8f89f49e2e7adcbd976` before and
after.

**Fab package not rebound:** no manifest input changed (`export_fab.py`, `jlc_orient.py`, `jlc_corrections.json`,
`jlc_easyeda/pads.json`, `fab_manifest.py`, `quality_audit/sexpr.py` and the CAD files). check.sh's
`fab_manifest.py --content` passes on the bound package: content checks 3 / 3, 6 outputs.

**Gate:** `KICAD_CLI=<10.0.7> NUMPY_PY=.supervisor/venv/bin/python tools/check.sh` exits 0 on the canonical tree,
after the last edit. Results: DRC 0, unconnected 0, parity 0, ERC 0; audit OK; silk 0; r10_parts current; fit OK;
**check_r10 full, 35 rules, OK** (no new rule; six titles now name the round 19 checks); route_check 0 failing; **fab
content checks 3 / 3 OK and the manifest's 6 outputs**. Self-tests: shell 10, procurement 20, fab_validation 34, fit
33, paste 16, r10_parts 5, route 68, **R10 234** (212 before this lane, 22 new; 6 NumPy skips under KiCad Python), and
NumPy `HotplugNumerics Plate` **6** (5 before). check.sh ran twice, the second time after the last edit (a docstring
line); both exited 0 and the board hash was the same before and after.

## Per gap

| Gap | Check added | Seed that now fails | Tests |
|---|---|---|---|
| 1 R19-GATE-01 | K-lands `land_overrides`: each placed footprint's paste margin, paste ratio and mask margin must equal its library copy (`pcbnew.FootprintLoad` on `kilib/rocket.pretty`), and so must each pad's local paste margin, paste ratio, mask margin and paste / mask layers. Pads are paired by number and local position (2 µm, mirrored when flipped). Zone-connection and clearance overrides stay with K-copper / LC-1. Board: 701 pads, 0 differences. C84 needs no exception, because its paste removal is the library variant (D-R19-07) | b19a (Q124 pads at a -0.1 mm board paste margin: "Q124.4: pad paste margin -0.100 mm, library none"); a U9 IN / OUT bar paste ratio of -0.6 (the library's is -0.047); an R134 footprint mask margin of 0.05 mm; Q124.1 without F.Paste | `RealBoardSeeds.test_r19_board_paste_and_mask_overrides_fail_k_lands` |
| 2 R19-GATE-02 | check_actuators r10 pins R131 = 10k / C25744 / 0402WGF1002TCE / `rocket:R0402` and C127, C129 = 10nF 50V X7R 10% / C57112. S-4 `mpn_values` decodes every fitted R / C Manufacturer Part. That is the field the JLC BOM is exported from, and S-4 `--bom` holds the BOM's code, MPN and footprint to it. The decoded value must equal the Value field, and so must any tolerance, voltage or dielectric the Value states. Board: 157 decoded in 11 families; C84 (aluminium polymer) is listed as not decoded, with its reason | b08e (R131 set to C11702 / 0402WGF1001TCE, Value still 10k): K-actuators "R10 R131 must be the 10k 0402 cold pull-up …" and S-4 "R131: Value '10k' but 0402WGF1001TCE (UNI-ROYAL) is 1000 ohm"; C127 or C129 set to C15195 fails K-actuators | `RealBoardSeeds.test_r19_r131_recode_fails_k_actuators_and_s4`, `R19GateFix.test_mpn_values` |
| 3 R19-GATE-03 | K-plane `plane_necks`: each non-GND inner fill is unfractured and deflated by 0.25 mm (PLANE_LINK_W / 2). A landing-via cluster that the deflation cuts off from the largest piece is a split piece and needs >= 2 outer links of >= 0.5 mm. Necks under 1.0 mm are reported, located by bisection. Calibration is in the real-board list below | b10b on the post-CAD board (an In2 keep-out leaving a 0.30 mm neck on the 3V3 buck finger): "via (23.100, 78.100) join(s) the main fill only through a neck under 0.5 mm …" | `RealBoardSeeds.test_r19_plane_neck_seed`, `R19GateFix.test_plane_neck_counts_as_a_split`, `test_plane_neck_over_half_a_millimetre_passes` |
| 4 R19-GATE-04 rest | K-power: every path names its design current, with its basis in the code. The floor must be >= `ipc2152.ipc_width(30 C, layer, amps)`, or the table fails. New paths: VLOGIC trunk (U11 -> U2 through C99), CAM_5V out (U402.6 -> J9.1 through C431), J410 feed and J420 feed (PORT_4V8, one In2 via each). U401's two 0.25 mm pin links are new exact POWER_NARROW entries (8 in all; stale entries fail). The via entries the CAD lane added (D-R19-09) are kept as they were | a 0.2 mm run on VLOGIC trunk, U400 OUT (PORT_5V3), CAM_5V out, J410 feed (PORT_4V8), U2 OUT (3V3) and U401 IN (PORT_5V3): "{path}: {net} track 0.200 mm wide …"; synthetic: a floor below its IPC width | `RealBoardSeeds.test_r19_rail_runs_at_0_2_mm_fail_k_power`, `R19GateFix.test_power_floor_must_hold_the_ipc_width` |
| 5 R19-GATE-05 | `track_graph` + `simple_path_edges` (biconnected blocks along the block-cut tree between the terminal hubs) now sit under `fire_path` and `path_graph`. Only copper on simple paths between the terminal sets is kept, so a terminal-free loop on one cut vertex is dropped, not only leaves. U9 IN needs >= 1 via of >= 1.0 / 0.5 mm, and any further via >= 0.5 / 0.3 mm. route_check keeps the CAD lane's measured `PARALLEL_VIAS_R10`, with no generic exemption. Board: all 6 fire paths and every earlier K-power path are identical (segment and via UUIDs, joined, pads); the J440 feed changed only by gap 11 | c01 / c01b now **pass** (see "c01 / c01b"); the adversary's c01 drawing keeps BAT_IN's fire and budget copper; synthetic: a side-branch loop off a cut vertex, a second via under 0.5 / 0.3 mm, no sized via | `RealBoardSeeds.test_r19_second_u9_in_via_passes`, `test_r19_adversary_c01_drawing_keeps_fire_and_budget_copper`, `R19GateFix.test_simple_paths_drop_a_side_branch_loop`, `test_u9_in_one_sized_via_and_board_minimum_parallel_vias`; `test_r18_u9_power_path_seeds` (expectation updated to "U9 IN: 0 via(s) of at least 1.0 / 0.5 mm on the path") |
| 6 R19-GATE-06 rest | K-legends `word_legends` gives each word a `centre_margin`: how much nearer the ink-box centre is to its own courtyard than to any other. It must be >= 1.0 mm for `WORD_CENTRE_BLOCKING` (GPS, RADIO, AUX, IGN, SERVO, CAM, SWD, all of which clear it on the board). BAT and SWITCH are reported only | RADIO moved 4.2 mm north, toward J410: "… must be nearer its own by 1.0 mm (R19-GATE-06)"; synthetic ties | `RealBoardSeeds.test_r19_word_centre_margins`, `R19GateFix.test_word_centre_margin_blocks_named_words_only` |
| 7 R19-GATE-07 | K-legends `silk_allowlist`: every visible silkscreen text must be a designator or an allowed legend. That covers board text, text boxes and footprint text and fields, on both faces. Allowed legends: a TERMINAL_PINS_R10 pin, a word, a PORT_LEGENDS_R10 row, SERVO_HARNESS_NOTE, a PINNED_TEXTS entry or the JLC mark `JLCJLCJLCJLC`. Board: 39 legends, 6 port rows, 121 designators | b21b ("BATT+" on F.Silkscreen at (1.55, 55.4) beside J121); R134's Value field shown on F.Silkscreen | `RealBoardSeeds.test_r19_silk_text_allowlist`, `R19GateFix.test_silk_allowlist` |
| 8 R19-REQ-10 | critical_reference drops V3V3_SENSE. R10's extended set is `EXTENDED_R10` = SWDIO / SWCLK / NRST; `EXTENDED` keeps the radio SPI names for the R7-R9 record tools. The dead CAM_TX_MCU / CAM_RX_MCU names are dropped from `R10_PORT_UART` / `R10_PORT_NETS`. `r10_stale_names` feeds K-reference, which fails on any listed name that is no board net. **Decision (D-R19-15):** the port UART nets stay under the strict partner-via and one-region rules | V3V3_SENSE put back in `R10_SLOW_RETURN_NETS`: "stale critical_reference.R10_SLOW_RETURN_NETS entry 'V3V3_SENSE' …" | `RealBoardSeeds.test_r19_stale_critical_reference_name_fails_k_reference`, `CriticalReferenceNames.test_r10_lists_hold_only_live_names_and_stale_ones_fail` |
| 9 R19-RTE-01 note | K-copper `pour_debris`: every zone fill piece, of any size, must hold a via of its net or touch >= 2 of its net's pads. Only exact, measured `POUR_DEBRIS` entries are excepted, and an entry fails as stale once its piece is gone | U1.19's pour connection restored, as on the round 18 board: "1.693 mm^2 piece at (26.13, 52.34) with no via and only U1.19"; the real U1.74 piece without its entry | `RealBoardSeeds.test_r19_pour_debris_seed`, `R19GateFix.test_pour_debris` |
| 10 R18-MEC-01 rest | `plate_model.STRAIN_PARTS` += R150-R155 | the old table fails the test | `Plate.test_r19_servo_resistors_in_the_strain_table` (NumPy) |
| 11 AUX feed | The `J440 feed` path is held to F.Cu (`layers=('F.Cu',)`). Its two In2 vias, (29.75, 9.95) and (30.5, 9.95), are pinned for count and size. The via (29.75, 12.6), behind them on U401's B.Cu run, no longer counts | via (30.5, 9.95) removed: "J440 feed: 1 via(s) on the path; at least 2 required" | `RealBoardSeeds.test_r19_aux_feed_second_via` |

## c01 / c01b

The seeds were applied to a full copy of the post-CAD tree (`git archive 6628488` plus this lane's tool files). The
second via goes at the F.Cu feed node (17.5, 88.891), joined on B.Cu by 1.0 mm straight to the IN via (17.5, 87.3), so
the two barrels are in parallel. The legitimate fix's one-line update is a `PARALLEL_VIAS_R10` entry. Each copy then
got the regeneration `m3_design/r10_build.sh` runs after the board:
- `r10_parts --budget-only`;
- `r10_hotplug --extract` and the **real NumPy solve**;
- `jlc_orient`, `export_fab --pending`, `fab_manifest --bind`, verify;
- the binding note.
After that, every `check.sh` checker step ran with the copy's own tools: DRC (all severities, with parity), ERC,
`verify_board`, `silk_check`, `r10_parts --check`, `fit_check`, check_r10 full with `--fit`, route_check and
`fab_manifest --content`. The gate lens's own scripts (`regen.sh`, `gate.sh`) did these steps.

| Copy | Board | Regeneration | Every checker step | Notes |
|---|---|---|---|---|
| control (no seed) | `50a39de5…` | all exit 0 | all exit 0 | regeneration reproduces the BOM, owner BOM, CPL, corrections, budget, hot-plug inputs / results and binding note byte for byte; only the timestamped Gerber zip, PDFs and manifest differ |
| c01, 1.0 / 0.5 mm | `d5e584e5…` | all exit 0 | all exit 0 | K-power U9 IN vias (17.5, 87.3) and (17.5, 88.891); S-9 evidence identical to the control (BAT_IN fire path 1 segment); K-power changes only U9 IN, 15 -> 16 segments, by the new B.Cu run; `parts_budget.json` differs only in `board_sha256`; hot-plug `passed: true`, qualification pass; route_check 0 failing (the clean drawing adds two counted short_layer_hop instances and one power_via_no_gnd, none gated) |
| c01b, 0.6 / 0.3 mm | `b8404e05…` | all exit 0 | all exit 0 | the same as c01 |
| adversary c01 drawing, 1.0 / 0.5 mm | `16199359…` | all exit 0 (the budget no longer refuses) | route_check fails, everything else exits 0 | V2 at (18.9, 88.891), a 0.707 mm B.Cu diagonal, then north to (19.4, 85.4), with the `PARALLEL_VIAS_R10` line at V2. track_loop is admitted; three faults of the drawing remain: short_segment (0.7071 mm at (18.9, 88.891)), acute_angle (45 deg at the free node (19.4, 85.4)), and a BAT_IN net detour (64.67 mm of copper > 1.6 x the 38.99 mm MST = 62.38 mm; the base board has 59.57 mm and the clean drawing 61.16 mm) |
| adversary c01b drawing, 0.6 / 0.3 mm | `6c711d82…` | all exit 0 | route_check fails, everything else exits 0 | the same three route_check faults |

These copies are under the session scratchpad, `r19/gp/` (`scripts/run.sh`; logs in `out/<copy>/`). They are not
in the repository.

## Real-board measurements (post-CAD board)

- K-lands: 701 pads compared against the library, 0 paste or mask differences.
- S-4 MPN values: 157 decoded, all equal to their Value fields; C84 is the only part not decoded.
- K-plane necks under 1.0 mm, all In2 3V3: 0.549 mm at the (18.8, 60.25) / (22.6, 52.15) / (19.05, 55.9) cluster,
  0.549 mm at the (23.1, 78.1) / (23.0, 70.0) / (23.2, 68.6) cluster, 0.589 mm at (9.2, 52.98) and 0.706 mm at
  (19.5, 49.15). PORT_4V8, PORT_5V3 and RAW_PROTECTED have none. Before unfracturing, the fracture slits gave a false
  0.474 mm reading.
- K-power has 14 paths. Each floor against the IPC-2152 width at a 30 C rise:
  - U9 IN 1.0 and U9 OUT 0.7 mm vs 0.680 mm at 2.9 A;
  - U401 IN / OUT and the J410 / J420 / J440 feeds 0.4 vs 0.326 mm at 1.9 A;
  - U400 OUT 0.4 vs 0.299 mm at 1.81 A;
  - U2 OUT 0.4 vs 0.356 mm at 2.0 A;
  - C84 hold-up and the VLOGIC trunk 0.4 vs 0.167 mm at 1.294 A;
  - U402 IN and CAM_5V out 0.4 vs 0.157 mm at 1.249 A.
  U401 EN has a 0.2 mm floor and no design current (it is an enable input). The J440 feed's vias are (29.75, 9.95)
  and (30.5, 9.95).
- Word centre margins (mm): AUX 14.465, GPS 13.178, IGN 5.265, SERVO 3.764, RADIO 3.716, CAM 3.451, SWD 2.853;
  reported only: BAT 0.080, SWITCH 0.040.
- Silkscreen texts: 39 legends, 6 port rows and 121 designators, every one on the allowlist.
- Pour pieces: 35; one is debris, GND F.Cu 0.282 mm^2 at (17.50, 34.48), touching only U1.74 (the named entry). The
  round 18 board `a3144b15…` had 36 pieces and two debris pieces: U1.19 at 1.693 mm^2 and the same U1.74 piece.
- critical_reference: every listed R10 name is a net of the board.

## Not done, and things to know

- **U1.74 pour debris is a real finding (R19-RTE-01 class), measured, not fixed.** On F.Cu GND, a 0.282 mm^2 piece at
  U1.74's pin tip (17.50, 34.48) touches only that pin and has no via. It is admitted by the one exact
  `POUR_DEBRIS` entry so the gate can pass without a CAD edit. CAD fix: a board pad override `ZONE_CONNECTION_NONE` on
  U1.74, as D-R19-05 did for U1.19, then delete the entry (it then fails as stale).
- **BAT and SWITCH word centre margins (0.080 / 0.040 mm) are below 1.0 mm**, so they are reported, not blocking, as
  the brief allows. `test_r19_word_centre_margins` fails if either later clears 1.0 mm, which prompts moving it into
  `WORD_CENTRE_BLOCKING`.
- **The adversary's literal c01 drawing still fails route_check**, on its own short segment, its 45 deg junction and
  the BAT_IN copper-length detour. Those are M2 drawing faults, not gate false positives. The same via drawn cleanly
  passes every stage with one `PARALLEL_VIAS_R10` line.
- MPN decode reads the board's `Manufacturer Part` field, the JLC BOM's source; S-4 `--bom` already holds each BOM
  row's code, MPN and footprint to the board. An undecodable family is listed by name with its reason, not failed.
  Only C84 is listed.
- `check_procurement --cost-only` still fails ($85.35 against $84.41). That is an owner decision, outside check.sh,
  and was not touched.
- K-actuators' docstring line said check.sh also ran check_actuators on its own. It does not, so the line now says
  check.sh runs it only through this rule.

## For the docs lane

- check_r10 is still **35 rules**. The S-4, K-legends, K-copper, K-reference, K-lands and K-power titles now name the
  round 19 checks.
- check.sh self-test counts are as above: R10 234 (6 NumPy skips) and NumPy `HotplugNumerics Plate` 6. The other
  suites are unchanged.
- K-power has 14 paths, each with a design current and its IPC-2152 width, and 8 `POWER_NARROW` entries. The camera
  and logic rails (CAM_5V out, VLOGIC trunk) and the J410 / J420 feeds are new paths.
- D-R19-15 records the gate changes and the R19-REQ-10 decision: the port UARTs stay under the strict rules.
- The U1.74 pour piece is a CAD item for the next board change.

## Round 20 follow-up (2026-10-31)

These came from the coordinator after the round 19 hand-back. The board is still `50a39de5…`, the index is untouched
and nothing is ordered.
- Edited: `tools/jlc_stock.py`, `tools/test_procurement.py`, `tools/check_r10.py`, `tools/test_r10_check.py`,
  `m3_design/r7_post.py` and `m3_design/r8_post.py`.
- Refreshed: `m3_design/assembly_review/fab/stock_check.json`.
- Not touched: the coordinator's `m3_design/r10_sch_check.py` and `r10_binding_note.json` edits.

- **R20-BOM-01 (stock).** `tools/jlc_stock.py` takes min(`stockCount`, `canPresaleNumber`) as the
  orderable quantity when both are present and stockCount alone otherwise; an unreadable value fails closed. Each line
  reports `jlc_stock`, `jlc_presale` and `orderable`. Reading canPresaleNumber this way is an inference: JLC
  documents neither field. Seeded test: `test_presale_number_caps_the_orderable_quantity`, which fails on the old
  tool because U4's 9 / 2 read thin there; procurement goes 20 -> 21. The live refresh of `fab/stock_check.json`
  (10:13Z) reports **U4 C51931514 short: orderable 2 (stockCount 9, canPresaleNumber 2) < 5**, and nothing is thin.
  Neither file is a fab-manifest input or output, so there is no rebind; the manifest is OK and BOM / CPL are
  untouched.
- **R20-MFG-02 (designator courtyards).** The generator's courtyard test (`m3_design/r7_post.courtyard_offenders`
  and `r8_post.courtyard_fails`) now tests courtyards of any size. It used to test only courtyards whose box centre lay
  within 8 mm of the ink. Now it skips a courtyard only when that courtyard's box is at least as far from the ink's box
  as the designator's own gap, and a polygon is never nearer than its box. This is a generator edit, made at the
  coordinator's request, and it affects only the next build. On the current board, both helpers now find exactly the
  three designators the review named; before, they found none.
  - New K-legends check `designator_courtyards`, independent of the generator. It tests every courtyard on the
    text's face against r7_post's measure (ink polygon to courtyard polygon). On the board: 121 designators and
    215 courtyards.
  - Exact, stale-failing `DESIGNATOR_COURTYARD_R20` entries (other part, own gap, overlap):
    - C400: J440, 0.082 mm, 0.151 mm^2;
    - C94: U1, 0.142 mm, 0.266 mm^2;
    - R461: J430, 0.018 mm, 0.306 mm^2.
  - The CAD polish pass moves these three; the entries then fail as stale and are deleted. None of them is in
    `r10_post.FIXED_REFS`.
- **R20-MFG-03 (Fab references).** New K-legends check `fab_ref_crossings`: a footprint's `${REFERENCE}` text on its
  Fab layer must not intersect that footprint's own Fab shapes (0.002 mm polygons). 210 Fab references are checked.
  The exact, stale-failing `FAB_REF_CROSSINGS_R20` table holds these measured overlaps (mm^2):
  - C445 0.1915, D440 0.0479, D441 0.0479 and C123 0.0013 (new);
  - R119 0.6935 (carried, reads "R1119");
  - **R173 0.011**: a sixth crossing the brief did not list. It is carried from round 18; its R13 entry (0.1, 0.0,
    0.4) still leaves the crossing.
  The CAD fix goes in `r10_post.FAB_REFERENCE_CLEARANCES_R13`, then the entry is deleted.
- **R20-SAF-02 (S-6).** `PORT_NET` gains `AUX_`. `SAFE_NET` gains `BAT_ENABLE` and `BAT_SW_`, which covers
  BAT_SW_SOURCE and BAT_SW_RETURN. The real board passes. The S-6 and S-8 header lines and s8's docstring now
  describe the current rules: S-8 has 11 barrel nets, and GND is a hazard for ACT_GATE, ACT_DRV and PYRO1_OUT.
  FMEA I-11 (docs) still claims BAT_IN / NRST / BOOT0 protection that S-6 does not implement; that is for the
  docs lane.
- **Tests (RealBoardSeeds), each failing on the old code:**
  - `test_r20_designators_inside_a_large_neighbours_courtyard` fails if any of these breaks: the generator helpers,
    the three entries, an inexact entry, R165's designator moved into U1's far corner (ink centre 8.1 mm from U1's
    courtyard centre in x and y) or C400's designator hidden (stale).
  - `test_r20_fab_reference_crosses_its_own_fab_outline` fails if any of these breaks: R165's Fab text at R119's
    1.0 mm, R119 at 1.2 mm (inexact) or C445 at 0.2 mm (stale).
  - `test_r20_s6_sees_aux_and_the_switch_enable_chain` seeds three tracks, each 0.100 mm from a protected run: the
    reviewer's AUX_TX_WIRE beside PYRO1_OUT, then a GPS track beside BAT_ENABLE and another beside BAT_SW_RETURN. It
    also seeds two part joins: R165 given an AUX pad next to BAT_ENABLE, and R80 joining a GPS net to
    BAT_SW_SOURCE.
    With the old `PORT_NET` or the old `SAFE_NET`, it fails.
- **Final gate:** `tools/check.sh` exits 0 on the canonical tree after every edit above. The board SHA-256 is
  `50a39de5…` before and after; DRC, ERC and parity are 0; check_r10 has 35 rules, all OK; route_check has 0 failing;
  the fab content checks pass 3 / 3 with 6 outputs. Self-tests: shell 10, procurement 21, fab_validation 34,
  fit 33, paste 16, r10_parts 5, route 68, R10 237 (6 NumPy skips) and NumPy `HotplugNumerics Plate` 6.
