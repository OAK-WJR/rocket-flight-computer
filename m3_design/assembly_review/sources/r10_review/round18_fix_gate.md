# Round 18 fix pass: gate lane (hand-back)

Scope: R18-GATE-02..09, R18-MEC-01 and R18-MEC-03, checks only. Edited: `tools/check.sh`, `tools/check_r10.py`,
`tools/fab_manifest.py`, `tools/export_fab.py`, `tools/fit_check.py`, `tools/plate_model.py`, `m3_design/r10_fab.sh`
and the tests `tools/test_check_shell.py`, `tools/test_fab_validation.py`, `tools/test_r10_check.py`,
`tools/test_fit_check.py`. No CAD, generator or docs edit; no git state change (the CAD pass was committed by the root
as `acba196` while this lane ran; everything here is unstaged on top of it). Machine-readable twin:
`round18_fix_gate.json`.

**Board unchanged:** PCB SHA-256 `a3144b151b58daf8ba5747def50decc4d1751ad35be478fafc89ef53aa533918` before and after.

**Fab package rebound.** `export_fab.py` and `fab_manifest.py` are manifest inputs, so `m3_design/r10_fab.sh` was run
(KiCad CLI / Python 10.0.7): S-4 BOM / CPL, CPL rebuild (worst pad residual 0.491 mm) and paste (F 245 / B 371) pass
inside `--bind`, then the manifest binds 6 outputs. BOM, owner BOM, CPL and `tools/jlc_corrections.json` are byte
identical; the Gerber zip, both assembly PDFs and the manifest changed (Gerber diff: creation dates only). Stage these
with the gate changes. Renders went to `.supervisor/r10_renders/`.

**Gate:** `KICAD_CLI=<10.0.7> NUMPY_PY=.supervisor/venv/bin/python tools/check.sh` exit 0 on the canonical tree (run twice, the second after the last test edit):
DRC 0 / unconnected 0 / parity 0 / ERC 0, audit OK, silk 0, r10_parts current, fit OK, **check_r10 full 35 rules OK**
(33 + K-power + K-lands), route_check 0 failing, **fab content checks 3/3 OK + manifest 6 outputs**. Self-tests: shell
10 (was 7), procurement 20, **fab_validation 34 (newly in the gate)**, fit 33 (was 31), paste 16, r10_parts 5, route 67,
**R10 201 (was 187; 5 NumPy skips under KiCad Python)**, NumPy `HotplugNumerics Plate` 5 (was 2).

## Per gap

| Gap | Check added | Seed that now fails | Tests |
|---|---|---|---|
| 1 R18-GATE-05 | `check.sh` recognises the repository board by `[[ "$BOARD" -ef "$CANON" ]]` (device + inode); the `R10_SKIP_FAB_MANIFEST` branch and its `unset` are gone; a missing board fails before any stage | the canonical board through a symlinked folder, a `..` spelling and (case-insensitive volume) `M3_DESIGN/...`; `R10_SKIP_FAB_MANIFEST=1` / `yes`; a missing board path. The old `check.sh` fails 8 of the 10 new shell tests | `test_check_shell`: `test_repository_board_is_recognised_by_identity`, `test_skip_flag_no_longer_skips_the_package`, `test_missing_board_fails_before_any_stage`; `test_explicit_build_stage_skips_manifest_only` retired |
| 2 R18-GATE-04 | `export_fab.py` never writes the manifest (deletes any old one; `--pending RECORD` records the export). `fab_manifest.py --bind RECORD` runs `content_checks` (check_r10 S-4 `--bom/--cpl`, `jlc_orient --verify-cpl`, `paste_check`) and writes the manifest only if all pass and neither inputs nor outputs changed since the export. `r10_fab.sh` = export `--pending` then `--bind`. `check.sh` canonical branch runs `fab_manifest.py --content` (binding + the same three checks) | s17-class: D9's CPL row turned 180 deg (verify-cpl: `('D9', ...)`); s18: R134 BOM code C3013496 -> C25744 (S-4: `R134 LCSC Part #`); B_Paste removed from the zip (paste); each failing check leaves the package unbound; an output or input edited after the export refuses to bind; a standalone export leaves no manifest; `check.sh` without `--content` fails | `test_fab_validation`: `Binding` (7, including the `--bind` / `--content` command lines with a stand-in KiCad Python), `ContentChecks` (4 on a copy of the real package); `test_check_shell.test_repository_package_needs_its_content_checks` (+ stub refuses a call without `--content`); `FabScript.test_r10_fab_checks_required_fitted_on_the_exported_lists` (rewritten) |
| 3 R18-GATE-02 / -03 | New rule **K-power**: `path_graph` (fire_path's pruned graph, start component only, end = pads or every via of the net). U9 IN (J1.1 -> U9.5, must pass C88.1) floor 1.0 mm (BAT_IN's S-9 floor); U9 OUT (U9.6 -> its In2 vias) floor 0.7 mm; only six named, exactly matched `POWER_NARROW` entries (two 0.3 mm bar entries, three C88-local 0.7 mm runs, the 0.4 mm via link); stale entries fail. Vias: IN >= 1 of >= 1.0 / 0.5 mm; OUT >= 2 of >= 0.5 / 0.3 mm joined to the In2 RAW_PROTECTED fill. `FIRE_RETURN`: Q124 source pads 1-3 -> tracks >= 0.3 mm -> >= 2 In1 GND vias >= 0.5 / 0.3 mm, every source pad on a return track | s03 (OUT 0.7 mm runs at 0.31), s03c (IN F.Cu 1.0 mm runs at 0.31), a C88-local run at 0.6, s11 (via (21.1, 79.1) + link removed: 1 via), s11b (IN via 0.5 / 0.3), s26 (Q124 bar + stubs at 0.15), a return via removed; synthetic: plane-less vias, small drill, a feed that skips C88, missing source pad, stale entry | `R18Gate` (5 synthetic), `RealBoardSeeds.test_r18_u9_power_path_seeds`, `test_r18_q124_fire_return_seeds` |
| 4 R18-GATE-06 | `PRO_FLOORS` += `min_text_height` 1.0, `min_text_thickness` 0.15, `min_silk_clearance` 0.15, `min_resolved_spokes` 2 (current .kicad_pro values; DRC's text checks then hold every silkscreen text) | each floor lowered (0.5 / 0.08 / 0.05 / 1) fails K-rules | `RealBoardSeeds.test_r18_k_rules_silkscreen_text_floors` |
| 5 R18-GATE-07 | M-3 pins the five Edge.Cuts circle centres to `SUPPORTS_R10` (4, 4), (42, 4), (4, 44.3), (3.7, 86), (42, 86) within 0.01 mm; any other circle fails | s15b (4, 44.3) -> (3.5, 46.8); (42, 86) -> (40, 84) | `RealBoardSeeds.test_r18_support_centres_are_pinned` |
| 6 R18-GATE-08 | K-legends `word_legends`: each of IGN, BAT, SWITCH, CAM, SWD, SERVO, GPS, RADIO exactly once (visible silkscreen text or text box) and nearer its own connector's courtyard box than any other connector on its face by > 0.01 mm; only named `WORD_SEAMS` ties; stale seams fail | s16c (BAT / IGN exchanged), BAT / SWITCH exchanged, GPS / RADIO exchanged, SWITCH removed, RADIO lifted 1 mm off its seam | `R18Gate.test_word_legends_identity_seam_and_count`, `test_word_legend_face_and_subject_map`, `RealBoardSeeds.test_r18_word_legends_are_beside_their_own_terminal` |
| 7 R18-GATE-09 | New rule **K-lands**: fp-lib-table is exactly `rocket` -> `${KIPRJMOD}/kilib/rocket.pretty`; every board footprint is from it and is either r10_parts-generated (9, pinned by `r10_parts --check`) or in `FOOTPRINT_SHA256` (37 files); unpinned and stale entries fail | s25 (Q124 gate pad 0.08 mm in `M3_AON7524_DFN3x3A.kicad_mod`), an unpinned footprint (R0402), a stale pin, a second library | `RealBoardSeeds.test_r18_unpinned_land_edit_fails` |
| 8 R18-MEC-01 / -03 | `plate_model.STRAIN_PARTS` += J410, J420, J9, J400, C431, C421, C411. `fit_check.wire_rooms()`: profile r10 reports and prints every DB125 terminal (report key `wire_room_mm`) | the old STRAIN_PARTS fails the strain test; the old printout listed J1 / J121 / J9 only | `Plate.test_r18_east_edge_terminals_and_capacitors_in_the_strain_table` (NumPy; `check.sh` now runs `HotplugNumerics Plate`), `test_fit_check`: `test_r10_wire_room_lists_every_db125_terminal`, `test_real_r10_board_reports_seven_wire_rooms` |
| 9 | `test_connector_mechanical_tabs_are_independently_checked` now shifts R10's J3 USB-C shell tabs (C165948 pads 1-2) and J430 microSD nails (C164170 pads 9-10); the R9 GH J9 (C161692) case is retired (not on R10). `test_fab_validation.py` runs in `check.sh` | shifted tabs fail `--verify-cpl` naming J3 / J430 | the file: 34 tests (was 23, 1 failing) |

Real-board measurements: all seven DB125 terminals 5.003-5.603 mm wire room (P-11 floor 4.95 mm); U9 IN path 15
segments (1.0 / 0.7 / 0.3 mm), feed via (17.5, 87.3) 1.0 / 0.5 mm; U9 OUT 5 segments (0.7 / 0.4 / 0.3 mm), vias
(20.3, 79.1) and (21.1, 79.1) 0.5 / 0.3 mm on the In2 fill; Q124 return 3 tracks of 0.3 mm to (15.85, 57.695) and
(15.85, 58.345), 0.5 / 0.3 mm.

## Not done, and things to know

- **SWITCH is not in `WORD_LEGENDS_R10`:** `m3_design/r10_post.py` builds its word list from `WORD_LEGENDS_R10` plus its
  own `('J400', 'SWITCH')`, so adding it there would make the next build place SWITCH twice. The identity check uses
  `WORD_SUBJECTS_R10 = WORD_LEGENDS_R10 + SWITCH`. A generator-lane follow-up can make one list the source.
- **RADIO sits on the J410 / J420 seam (measured):** its ink box is 0.000 mm from both courtyard boxes (the courtyards
  are 0.09 mm apart; by courtyard polygon or pad distance it is about 0.02 mm nearer J410). It heads J420 at its
  top-left corner like SERVO heads J122, so it is the one named `WORD_SEAMS` entry, accepted only while the tie holds.
  A legibility call for review. J430 (bottom SMD microSD under RADIO) is not ranked against top-side legends.
- **U9 IN floor 1.0 mm, not the adversary's 0.7:** the designed width upstream of C88 is 1.0 mm (S-9's BAT_IN floor),
  so the three 0.7 mm C88-local runs are named entries instead; stricter than a single 0.7 mm floor.
- Not in the brief, not done: R150-R155 (also named in R18-MEC-01) are not in STRAIN_PARTS; no width floor for
  VLOGIC / PORT_5V3 / CAM_5V / PORT_4V8 / 3V3 (R18-GATE-02 "other rails"); no real-board seed for an OUT via without
  In2 fill (synthetic only).
- `m3_design/r8_fab.sh` / `r9_fab.sh` (historic, not edited) now stop at their manifest check because the export no
  longer binds: they fail closed.
- For the docs lane: AGENTS.md section 5 (`python3 tools/export_fab.py` alone leaves the package unbound; use
  `m3_design/r10_fab.sh`); R10_DECISIONS D-R8-03 (`R10_SKIP_FAB_MANIFEST` removed); check_r10 now 35 rules; check.sh
  self-test counts above; check.sh also runs the fab content checks and `test_fab_validation.py`.
