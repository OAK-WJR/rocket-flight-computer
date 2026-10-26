# R9 build and validation

**Build steps 1–10 of `r9_plan.md` §4 made board `fc3d5b34…`; review pass 1 reviewed it, and its fix pass made the
current board `4f841a0e…` (46 × 102 mm) through the generators ("Review pass 1" below). `tools/check.sh` exits 0, every
hard row of r9_plan §2 is met, 34 done rows are met and 16 missed (each miss with a recorded cause, listed below), and every
qualification the clean sheet invalidated is re-derived on the current geometry (the requalification tables). Review
passes 1 and 2 found no confirmed Critical or Major (r9_plan §5's two consecutive clean passes; "Review pass 2" below).
On 2026-10-25 the owner accepted the R9 deviation list below, kept the board at 102 mm (option C1 (c)) and asked for it to be
committed and pushed. Before ordering: U4 in JLC stock or consigned, JLC's acceptance of the four tabs, and a cost and stock
run within 24 h. R8 (`cc044ea0…`, owner-accepted 2026-10-20) is the previous accepted revision.** This record approves no fabrication or flight
release. Design record: [M3_R9.md](M3_R9.md); plan and decisions: `m3_design/assembly_review/sources/r9_design/`
(`r9_plan.md`, `R9_OWNER_DECISIONS.md`, `R9_DECISIONS.md` D-S1-01 … D-S10-19 and D-F1-01 … D-F1-11, the step handoffs
`r9_step1_handoff.md` … `r9_step10_handoff.md`); review pass 1: `m3_design/assembly_review/sources/r9_review/`.

Evidence paths below are relative to `m3_design/assembly_review/sources/r9_design/`. Every file in `step10_evidence/`
is bound to the current board: its first line or its `board_sha256` field is `4f841a0e…` (step 10's scripts re-run by
the fix pass, D-F1-11; checked by `step10/check_records.py`, `step10_evidence/check_records.txt`). `step9_evidence/`
stays step 9's record of `fc3d5b34…`. **Inference** marks anything not measured or not taken from a requirement or a
maker document (AGENTS §2.5).

## Baseline and build summary

- **Baseline:** R8, commit 9c8179b, board SHA-256 `cc044ea0922ff826df19af9d9726d92c096ab2b127025b55d123d8772e5fb4a7`
  (owner-accepted 2026-10-20). Worktree `rocket-flight-computer-r9`, branch `m3-assy-r9`, committed and pushed at the
  accepted state on 2026-10-25.
- **Plan:** B-spine (r9_plan §1): the RF strip aft (y 0–22.0), U1 and the signals in the middle, the CH1 pyro column on
  the west edge as a dead end with both pyro terminals entering from −x, all power in the east column, a RAW_ACT spine on
  F.Cu, In2 and B.Cu. Clean sheet: nothing is copied rigidly from R7 / R8; every qualification is re-derived.
- **Owner decisions** (`R9_OWNER_DECISIONS.md`, 2026-10-20): B-spine at 98 mm with 100 / 102 mm fallbacks; the stricter
  pyro rules (P-1b, P-3, P-7, strict pad rules) and renumbered J121 / J124 pads; the RF strip y 0–22.0 and the ≈ 45 mm
  radio-to-pyro distance with the keyed-radio immunity test; signal vias ≤ 70 (stretch 55); J122 turned; mid support
  east.
- **Current board:** `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
  **`4f841a0e44ebb1829ad7996dfe6320ed527fce1fdb1e5ff11658e0705b44ac14`** (review pass 1's fix pass; step 10's board was
  `fc3d5b34a4bfbaecfbcb44bdf8144c87015fc71be7accf48354f23410e8d0f51`); netlist `8b0e04ea565ecf1b…` and design rules
  `ea77b791eaa4026d…`, both unchanged (`step10_evidence/r9_binding_note.json`, `requalify_r9.json` `inputs_sha256`); fab
  package bound to it by `tools/fab_manifest.py` (`step10_evidence/fab.txt`).
- **Reproducible:** `m3_design/r9_build.sh` (stages 0–38: R8's sources from 9c8179b → schematic and footprint variants →
  placement → RF strip → pyro block → power → ten routing families → ground → silkscreen → `tools/check.sh`, each stage
  with its gate). For the current board, two builds gave the same 15 sheets, netlist, DRU, both variant footprints and
  board, byte for byte: the fix pass's stage replay in the worktree and `r9_build.sh` run whole in a scratch clone
  (`step10_evidence/build_sha256.txt`; step 9's two builds of fc3d5b34: `step9_evidence/build_sha256.txt`).
  `m3_design/r9_fab.sh` makes and checks the fab package.
- **Environment:** steps 6–9 and step 10's first two sessions ran with no logged-in GUI session, so `kicad-cli pcb drc`
  needed a scratch shim (D-S6-14) and `tools/check.sh` a `KICAD_CLI` wrapper with `KICAD_PY` set (D-S9-06, D-S10-07).
  Step 10's last session, review pass 1 and its fix pass ran with a GUI session logged in: `tools/check.sh`, the tests
  and kicad-cli ran as they are (D-S10-15). Nothing in the repository depends on the shim or the wrapper.
- **Generator state:** committed on `m3-assy-r9` at the accepted state on 2026-10-25, at the owner's instruction; the commit
  that adds this line holds `4f841a0e…`.

| Step | What it produced | Board after it | Verification (as run; misses named) |
|---|---|---|---|
| 1 Gate first | `tools/check_r9.py` (LC-1, P-0…P-11, R-1…R-13, M-2…M-7, F9-1, T-1, K-rules), `pyro_probe.py`, `bridge_table.py`, `rule_h_seed.py`, `gcpw_solve.py`, `tab_windows.py`, `plate_model.py`, the R9 scorecard; D-S1-01…25 | R8 `cc044ea0…` | every rule fails on a seeded defect (52 tests); R8 fails 17 rules, each for an owner-adopted strictness or a real R8 fact; gcpw_solve within 0.34 Ω of pass 2 (`step1_evidence/`) |
| 2 Schematic, footprints | `r9_lib.py` (J121 / J124 / J122 variants), `r9_dru.py`, `r9_sch.py`, `r9_sch_check.py`; D-S2-01…13 | R8 | ERC 0; netlist diff = the three footprint fields; 52 / 52 extended codes; LC-1 clean (`step2_evidence/`) |
| 3 Placement | `r9_place.tsv`, `r9_legalise.py`, `r9_pcb.py`; 98 and 100 mm fail, 102 mm by the kill path (D-S3-03); D-S3-01…11 | `349c1477…` | 0 legaliser violations over 249 parts, DRC + parity, fit, plate, F9, F10, strict pad rules, tabs, MST 1468 mm (`step3_evidence/`) |
| 4 RF strip | `r9_rf.py` templates in each jack's / module's frame, `r9_rf_check.py`; D-S4-01…08 | `50a5af67…` | R-1…R-13; launches congruent with R7; 79 GCPW samples 50.16–51.08 Ω (`step4_evidence/`) |
| 5 Pyro block | `r9_pyro.py` (pad-referenced), `r9_pyro_check.py`, the DRU's zone fill margins; D-S5-01…15 | `a6454f78…` | margins ≥ max(R8, 0.2) but D-S5-13; 0 forbidden bridges; rule H live; GATE_N neighbours GND (`step5_evidence/`) |
| 6 Power | `r9_power.py` (four In2 regions, the 7.7 A spine), `r9_power_check.py`; D-S6-01…14 | `47fb298d…` | D12 limits, every rise ≤ R8, D_raw 0.79 mΩ, vias ≤ 1 A, D18 4.953 mm, F9 premise (`step6_evidence/`) |
| 7 Routing | ten family modules, `r9_route_check.py`; D-S7-01…19 | `8504c2c6…` | each family's template, DRC, route_check r9 (empty allowlist), budget; S4 57 ≤ 70 (`step7_evidence/`) |
| 8 Ground | `r9_ground.py` / `.tsv` (183 GND vias), the crystal's In2 plane, via pads only where connected; D-S8-01…20 | `89ddea8d…` | 12 gates; P9 3.45 mm; R6b 0.1022 (R8 0.1107) (`step8_evidence/`) |
| 9 Post and fab | `r9_post.py`, `r9_post_check.py`, `r9_fab.sh`, `tools/check.sh` as the build's last stage; D-S9-01…07 | **`fc3d5b34…`** | two byte-identical builds; `tools/check.sh` exit 0; 474 tests in 26 suites; $109.38 / board, 52 extended codes (`step9_evidence/`) |
| 10 Requalification, records | `step10/requalify_r9.py`, `run_dc_r9.sh`, `fire_loop_r9.py`, `tab_plan_r9.py`, `ordering_facts_r9.py`, `binding_note_r9.py`, `m2_sweep_r9.py`, `bind_report.py`, `check_records.py`; the records; D-S10-01…19 | `fc3d5b34…` (unchanged) | `tools/check.sh` exit 0; 474 tests in 26 suites; every invalidated item measured; records check OK (step 10's evidence of fc3d5b34, superseded by the fix pass's re-run in `step10_evidence/`) |
| Review pass 1 and its fix pass | eight reviewers and gate integrity on fc3d5b34 (`sources/r9_review/pass1_*.md`): 0 Critical, 1 Major (confirmed as Minor), 50 Minor; the fix pass through the generators and tables (QSPI_IO2, R7's module vias, TXEN at 0.2 mm, TP120's vias, C98, the RAW_ACT pour edge, the ground aid's copper stage and the C121 exception), check_r9 P-7b / R-5 / R-7 / R-8, pyro_probe, the scorecard's Z4, r9_ground_check's copper gate; D-F1-01…11 | **`4f841a0e…`** | two byte-identical builds; `tools/check.sh` exit 0 (`step10_evidence/gate/check_sh.txt`); 478 tests in 26 suites, none skipped (`step10_evidence/tests.txt`); step 10's requalification re-run (below); records check OK (`step10_evidence/check_records.txt`); "Review pass 1" lists every finding |

## Hard gates (r9_plan §2), on `4f841a0e…`

| Gate | Result | Evidence |
|---|---|---|
| `tools/check.sh` exit 0 (DRC incl. A–H / A2, ERC, parity, check_r9, route_check r9, fit) | **exit 0**: DRC 0 at every severity, unconnected 0, parity 0, ERC 0; metadata / 3D audit OK; silkscreen inside the outline; fit OK; plate model; seeded rule-H suite OK; check_r9 OK on all 40 rules; routing hygiene 0 failing, 0 allowlisted, 0 leftovers; check_actuators OK | `step10_evidence/gate/check_sh.txt`, `gate/r9.json`, `gate/route.json` |
| D12 neck limits at 0.05 mm | RAW_ACT 12.6 °C, BAT_IN 12.1 °C, ACT_FET_S 20.4 °C (≤ 20 / 20 / 30; fc3d5b34 12.7 / 12.1 / 20.4) | `step10_evidence/dc/dc005_{raw,bat,fet}.txt` |
| LC-1 (no local clearance override) | 0 overrides (R8 29) | `gate/r9.json` LC-1 |
| X2d battery-live to armed copper ≥ 2.5 mm | no BAT_IN / ACT_FET_S copper within 3.5 mm (the check's reach) of bus, igniter or drain copper on the same layer (D85; R8 1.089 mm); in plan view no foreign net within 3 mm of armed copper (X2b = 0) | `gate/r9.json` K-power-pyro; `requalify_r9.json` `pyro.armed` |
| X9 RF separation ≥ 5.94 mm | 6.04 mm (R313–U1) | `gate/r9.json` R-10 |
| X9c inner power to pyro ≥ 2.65 mm | 4.953 mm (In2 RAW_ACT to R131.1) | `gate/r9.json` K-power-pyro |
| S15 / S16 inner signal track | 0 / 0 mm | `gate/r9.json` K-inner; `step10_evidence/r9_scorecard.md` |
| F1 fit (worst top margin ≥ 0) | 0.028 mm (J9 mated, R8's floor) | `gate/check_sh.txt`, `gate/fit.json` |
| f1 ≥ 209 Hz | 256.6 Hz (R8 208.7) | `gate/plate.json` |
| Width, strip contents, S13, supports | 46.0 mm; 0 non-RF parts in the strip; 0 critical layer changes without a GND via; supports 4.483 mm bottom (C98.1 at (42, 59.5), moved by the fix pass) / 5.008 mm top (≥ 3.5 / 3.8) | `step10_evidence/r9_scorecard.md`, `gate/fit.json` |
| No rule weaker than R8 | the DRU-against-R8 check (r9_sch_check, `r9_dru.py --check`: only rule G's scope widens, plus the fill margins and the two LC-1 rules) and check_r9's strengthened rules, in both builds; the fix pass adds check_r9 P-7b and r9_ground_check's copper gate and makes R-8 stricter (D-F1-01, -03, -07) | `step2_evidence/dru_r8_r9.diff`, `step10_evidence/build.txt` |

## Scorecard: the done rows (r9_plan §2)

The fix pass's survey (`tools/run_r9_survey.sh` with the 0.05 mm DC and the gate, `step10_evidence/r9_scorecard.md`) on
`4f841a0e…`: 34 met, 16 missed, 3 "not measured" that are met by construction (X2c, Z1e, Z1f: no pair within reach);
index_r9 83.8 (R8 = 100, target ≤ 73). On step 10's `fc3d5b34…` step 9's scorecard counted Z4 from TP122 alone and
reported it met; counted over every test pad it was 2 (TP120's two RAW_ACT vias), so `fc3d5b34…` stood at 33 met and
17 missed (R9P1-REQUIREMENTS-02); the scorecard now counts every TP* pad and the fix pass's Z4 is 0.

| Group | Met | Missed (record) |
|---|---|---|
| Length | — | X1 102.0 mm ≤ 100 (D-S3-03: owner decision 1's 102 mm fallback, forced by r9_plan's hard row X9 ≥ 5.94 mm, not by F10's 5 mm; the owner's options, 98 mm or 100 mm, are C1) |
| Pyro | X2 = X2b = 0; X2c; Z1 A 0.23, B 0.32, C 0.277, D 0.251, G 0.27, H 0.225 (each ≥ max(R8, 0.2)); Z2r9 66.4 mm; Z4 = C6 = 0; Z5 2.354 mm; Z5b 1.03 mm | X2g 7 (bounding-box metric: 3V3A, ACT_GATE, SERVO1_MCU, SERVO1–3_OUT, SERVO4_MCU cross the CH1 parts' box over J122's west columns, none within 3 mm of armed copper; D-S6-13, steps 6–7) |
| Routing | C1 = C3 = 0; S1 1306.9, S6 1.152, S7 207.5, S12 18, S17 1367.5 (all ≤ R8); S4 57 ≤ 70; X5 5; X8c 0; Y6 0 | S8 / S9 2 (RADIO_TXEN, keep-out-forced, D-S4-06; RAW_ACT_SENSE_MCU 2.24 mm on a 0.90 mm MST, D-S7-12); S10b 260 > 231; Y1 30 > 10, Y1b 14, Y2c 11, Y7 1, Y5 34 > 10 (steps 4–7, `step8_evidence/step8_deltas.txt`) |
| Planes | P9 3.37 mm | P6 1479.4 mm > 900 (D-S6-13); P7 9 > 0 (D-S8-15); P10 7.32 mm > 7.0 (D-S8-16); R6b 0.1022 > 0.08 (D-S8-17; R8 0.1107) |
| Power | D_raw 0.80 mΩ; every rise ≤ R8 | — |
| RF | X3 20.5 mm; GCPW 50.165–50.514 Ω (straight-line samples) | X3f 291.8 mm > 250 (steps 4 and 7; R8 321.3) |
| Mechanical | f1 256.6 Hz ≥ 241; IMU lever arm 11.0 mm ≤ 11 | — |
| Composite | — | index_r9 83.8 > 73 (the composite of the misses) |
| Stretch | — | all nine stretch rows missed, among them S4 57 > 55 (D-S7-19) |

## Requalification on the final board (survey_constraints §8.4, §9.4, §11)

Every item below was measured on `4f841a0e…` by the gate's own code or by step 10's scripts (`step10/`; commands in
`r9_step10_handoff.md`; D-S10-01), re-run by review pass 1's fix pass on its board (D-F1-11; where a figure changed from
step 10's `fc3d5b34…`, the row gives both). Nothing is carried over from R7 or R8 except where the geometry is shown
congruent on this board (the RF launches and chains, below).

### Pyro (F7, F8, AGENTS §2)

| Item | Result on `4f841a0e…` | Evidence |
|---|---|---|
| Rules A–H, A2 (closest approach, geometric) | A 0.73 mm (margin 0.23; RAW_ACT via (27.45, 57.95) to the ARM1_SENSE lane, F.Cu); B 0.82 (0.32; Q124.5 drain to the gate run); C 0.577 (0.277; R131.1 OUT to the COLD track, tied with R173.1 OUT to the CONT_MID run); D 0.751 (0.251; GND fill to J121.1 OUT, tied with R131.1 / J124.1; pyro_probe now names the first of equal pairs by label, D-F1-03); G 0.412 (0.112; GATE_N's entry into U1.3 against the no-net sentinels U1.2 / U1.4: the one recorded exception, D-S5-13; every other G pair ≥ 0.5 mm); H 1.225 (0.225; Q124.5 to R129.2); E, F, A2: no pair within reach. Every margin ≥ max(R8, 0.2 mm) but G's | `step10_evidence/requalify_r9.json` `pyro.margins`; `gate/r9.json` P-0 |
| Strict pad rules (owner decision 2) | H+ 1.225 mm (margin 0.025 over 1.2); GS 1.68 mm (0.48; R128.1 GATE to C127.1 CONT); AG 1.334 mm (0.134; R121.1 ACT_GATE to C88.2 GND) | `step10_evidence/requalify_r9.json` `pyro.margins`; `gate/r9.json` P-0 |
| Rule H liveness (seeded suite) | three closest pairs (Q124.5–R129.2, R132.1–C129.1, R177.1–R124.2) × eight variants (seed at 0.95 mm, rule lowered / deleted / moved first / narrowed, RAW_ACT or ACT_GATE dropped, an armed-pad override): each caught by DRC, check_actuators, LC-1 or pyro_probe | `gate/seed.json`; `requalify_r9.json` `pyro.rule_h` |
| Solder-bridge table (R4 method) | 134 exposed pairs under 1.5 mm, **0 forbidden**; 19 under 1.0 mm, every one a tolerated class (a sense node or midpoint to GND: the ground refusal; a gate to GND: holds the FET off; a midpoint to its own node: one 5.1 k half shorted); the fires-class pairs are a part's own pads only (Q124's pins to its drain 0.52 mm, C128's pads 0.65 mm, U1.3 to U1.1 0.70 / U1.6 1.20 mm at the LQFP's pitch), none between two parts under 1.5 mm | `requalify_r9.json` `pyro.bridges` (with the full table); `gate/r9.json` P-5 |
| Divider-fault preconditions (F8) | each divider a split top of two separate 5.1 k parts and a parallel bottom of two 2 k parts: PYRO1_CONT R173 / R129 over R130 ‖ R178, ARM1_SENSE R132 / R175 over R133 ‖ R180, RAW_ACT_SENSE R177 / R124 over R125 ‖ R182; the 4.7 k at the MCU end, R168 / R170 / R172, with *_MCU lanes 2.86 / 2.12 / 2.24 mm (P-8 ≤ 3.0); no copper above the 3.3 V rail within 1.5 mm of any MCU side; on the node side the worst neighbour sources (bus, drain, RAW_ACT, VLOGIC) force at most (8.4 − 3.3) V / 4.7 k = 1.09 mA into the pin through the 4.7 k, F8's two-fault figure (Calc) | `requalify_r9.json` `pyro.divider` |
| Gate reset voltages (P-7, P-7b) | within 1.5 mm of PYRO1_GATE_N outside U1's courtyard: GND only (the guard); the gate nets' table: U1's own neighbouring pins at the pin entry (QSPI_IO2 0.833 mm, 3V3 1.305 mm: U1's pins excepted as P-1b does, D-S5-14); **P-7b, U1's gate pin pad U1.3 inside the courtyard** (D-F1-01): QSPI_IO2's escape 0.55 mm (fc3d5b34 0.250 mm; R8 0.75), 3V3 1.25, IMU_INT1 1.369 mm, each ≥ 0.5 mm; Q124.4 (the FET's own gate pin) to its drain copper 0.95 mm; PYRO1_GATE's via to C127.1 (CONT) 1.017 mm, 0.41 V in reset (≥ 0.5 mm, P-7's guard; the bridge table holds it at 1.68 mm pad to pad); GATE_N to the CONT run 2.855 mm, 0.37 V | `requalify_r9.json` `pyro.reset`; `gate/r9.json` P-7 |
| Block purity (X2 / X2b) | no foreign net within 3 mm of bus, igniter or drain copper, same layer or plan view (R8: 6 / 7 nets) | `requalify_r9.json` `pyro.armed` |
| Coating and leakage | bare pyro-gate pads to bare armed-live pads: 2.35–4.35 mm where any lies within 5 mm (R126.2 GATE to C128.1 OUT 2.354 mm the nearest; R8 1.027); no bare RAW_ACT or 3V3 pad of another part within 5 mm of any pyro gate pad, apart from U1's own pins: U1.6 (3V3) 1.20 mm and U1.1 (QSPI_IO2) 0.70 mm from U1.3 (PYRO1_GATE_N), with the no-net sentinels U1.2 / U1.4 between; GATE_N is held by R127's 1 kΩ (a 3V3 leak must be ≤ about 6.4 kΩ to put 0.4 V on it, Calc), so U1 is not coated (requalify_r9's `pyro.bare` leaves a part's own pads out; R9P1-PYRO-02); the masked F.Cu / B.Cu GND pours stand 0.151 mm (the board's zone clearance) from the bare pyro-gate pads R126.1 / .2, R127.1, R128.1, C126.1, Q124.4 (GND holds the gate off) and from the bare actuator-gate pads C120.2, R121.1, Q121.4 (ACT_GATE) and Q122.3, R121.2 (ACT_DRV), which a GND bridge turns on (C19; R8 D109's owner option); actuator-switch gate pads: no armed-live pad within 5 mm, always-live nearest R120.2 to C120.1 (ACT_FET_S) 1.03 mm (Z5b ≥ 1.0; R8 0.634); coat region = PYRO_BLOCK (x 1.2–28.4, y 54.2–89.8, by content) + J2, 5.526 mm from U4, no keep-off part and no test pad inside but TP122 (P-10); J2's NRST pad 0.483 mm from pads 1 (3V3), 4 and 5 (GND) | `requalify_r9.json` `pyro.bare`, `pyro.coat`; `gate/r9.json` P-6, P-10; `ordering_facts.json` `j2` |
| Exits (GATE_N, CONT, ARM1_SENSE, *_MCU) | GATE_N 11.97 mm, CONT 14.47 mm, ARM1_SENSE 40.0 mm, all F.Cu without a via (Z2r9 66.4 mm); *_MCU 2.86 / 2.12 / 2.24 mm (RAW_ACT_SENSE_MCU's one via on pin 34's line, D-S7-12); one pyro via in all (PYRO1_GATE (9.125, 61.955), GND partner 1.391 mm, P-9); D19 none under 0.5 mm; M-6 no bottom part within 1.0 mm of a pyro via | `requalify_r9.json` `pyro.exits` |
| GND vias in PYRO_BLOCK | 39; nearest armed copper 0.801 mm (R134.2 BUS), nearest other pyro / RAW_ACT copper 0.24 mm (the RAW bar's F.Cu edge, an ordinary power-to-GND gap) | `requalify_r9.json` `pyro.block_vias` |
| TP122 | bottom, (7.58, 63.5); no via in its pad (R8's A8 removed); the gate via's GND partner 1.391 mm | `requalify_r9.json` `pyro.tp122` |
| Wire room | J121 and J124 enter from −x (owner decision 1), 6.353 mm to the bore wall (P-11); 6.4–7.0 mm at 5 mm height (fit_check) | `requalify_r9.json` `pyro.wire_room`; `gate/check_sh.txt` |
| Fire loop on the final copper (F7) | board copper RAW_ACT → J124.2 10.06 mΩ, bus 2.41, igniter 2.42, drain 1.58 mΩ (0.05 mm), BAT_IN 0.16 and ACT_FET_S 0.26 mΩ (the 0.05 mm solves) and the GND return ≤ 0.81 mΩ (0.1 mm window, an upper bound): 17.7 mΩ of copper; with Q120 and Q121 (AON6403, ≤ 4.3 mΩ at Vgs −4.5 V; the gate sees −6.73 V at 7.4 V) and Q124 (AON7524, ≤ 5.8 mΩ at Vgs 2.5 V; the gate sees ≥ 2.77 V) at their data-sheet maxima, 32.1 mΩ on the board; F7's budget 7.4 V / (4.45 Ω + 0.0321 Ω) = 1.65 A (without the board 1.66 A) against 1.5 × 1 A all-fire: met on the final copper (1.65 × all-fire). The RAW bar, J124.2's 1.0 mm F.Cu track, is the largest copper term (R8's RAW_ACT → J124.2 0.44 mΩ); the harness's ≤ 0.3 Ω stays a bench item | `step10_evidence/dc/fire_*.txt`, `dc/fire_loop.txt`, `dc/dc005_{bat,fet}.txt`; D-S10-04, D-S10-16 |
| Radio to pyro (R-13) | 46.13 mm (U31 to Q124.5); ≥ 40 (R7 / R8: U31 68.4 mm from J121; owner decision 3 accepts about 45 mm, the keyed-radio immunity test is the evidence) | `gate/r9.json` R-13 |

### RF (F10)

| Item | Result on `4f841a0e…` | Evidence |
|---|---|---|
| GCPW field solve | 79 line samples (GNSS 30, radio 49), every one W 0.30 mm with F.Cu GND gaps 0.26–0.32 mm over In1: Z0 50.16–51.08 Ω coated (tools/gcpw_solve.py; the 0.31 / 0.32 mm pairs are the two bend samples, R-5's ≤ 0.55 mm bend rule); the solver reproduces pass 2's 50.3 Ω within 0.34 Ω | `requalify_r9.json` `rf.gcpw`; `step1_evidence/gcpw_validate.txt` |
| Launch | both jacks' eight launch vias at pass 2's spots within 0.02 mm, R7's 0.6 / 0.3 mm size, no foreign copper in the window, the In1 cut-out, F.Cu GND copper in the window equal to R7's J31 (XOR 0.0 mm²) and J30 = J31: R7 pass 2's 49.0 Ω launch carries over (this solver: 48.79 Ω) | `requalify_r9.json` `rf.launch`; `gate/r9.json` R-4 |
| Chains | every chain part at R7's place in its jack's frame but D30 (turned 180°) and C303 (at the bias node), the recorded deviations (D-S4-02); the radio chain exactly R7's | `requalify_r9.json` `rf.r7` |
| Return-loss cascade (Inference) | pass 2 §3.12's lossless cascade on the drawn sections (launch 48.79 Ω × 4.2 mm, 0.2 mm at 70 Ω, line 50.34 Ω, line pads 36.6 Ω solved, ESD 0.2 pF, choke 500 Ω, DNP stubs 0.94 mm, series 0.4 nH): GNSS \|S11\| 0.042–0.074, RL 22.6–27.6 dB over 1.176–1.61 GHz; radio 0.064–0.066, RL 23.6–23.9 dB at 902–928 MHz; mismatch loss ≤ 0.024 dB (R7 pass 2: 19–21 / 25 dB) | `requalify_r9.json` `rf.return_loss` (D-S10-02) |
| Stitching and fence | largest GND-via gaps along each line, by compass side (a line run from the jack forward): GNSS east 2.38 / west 1.75 mm, radio west 2.405 / east 1.7 mm (≤ 2.5; R8 on the same metric GNSS east 2.34 / west 2.725, radio east 1.70 / west 2.405; the radio's west gap ends at U31.7); fence of 24 vias on y 22.2 with four lane openings 2.10–2.50 mm (≤ 2.7, each crossed by its lanes); strip GND reach F.Cu 2.99 / B.Cu 3.57 mm (≤ 4.0; fc3d5b34 3.1 / 3.57); RF ground pads' vias ≤ 0.23 mm; **the radio module's GND pins U31.2 / U31.7 / U31.16 0.20 / 0.35 / 0.35 mm of copper from a GND via** (R7's three module-frame vias restored, D-F1-02; fc3d5b34 1.154 / 1.095 / 1.05; R7 0.20 / 0.35 / 0.35); strip GND coverage F.Cu 77.8 %, In1 95.1 %, In2 96.7 %, B.Cu 92.9 % | `requalify_r9.json` `rf.contract` R-7; `gate/r9.json` R-7; `sources/r9_review/fix1/fix1_measure.py` `module_gnd_pins` |
| Keep-outs and module ground | U30_KEEPOUT (F.Cu, In1) and U31_KEEPOUT (all four layers) cover the derived regions, 0 mm² uncovered; GND fill at all 2,601 samples under U31's whole body on In1 (sampled over the body since D-F1-03) and In2, 1,938 under U30's keep-out on In1 | `requalify_r9.json` `rf.contract` R-8; `gate/r9.json` R-8 |
| Chain topology | ESD 0.795 mm from each jack pad end; the bias cap 0.925 mm; shunt stubs 0.94 mm | `requalify_r9.json` `rf.contract` R-9; `gate/r9.json` R-9 |
| F10 separations | nearest RF part to a restricted part 6.04 mm (R313–U1); nearest fast-line pad 5.005 mm (R306–USB_DM); U30 ≥ 15.46 mm from U1, U31 ≥ 13.38 mm from C73; the logic buck U2 / L1 ≥ 49.99 mm from both modules; the camera buck U8 / L3 26.9 / 28.8 mm from U30 and 17.3 / 21.5 mm from U31 (courtyard to courtyard); fast copper ≥ 12.4 mm from U30 (USB_DM at D4.1), ≥ 16.8 mm from U31 | `rf.contract` R-10; `requalify_r9.json` `rf.separations` |
| Coexistence geometry | radio lines to U30's body: RXEN 5.2, BUSY 5.7, MISO_MCU 6.2, SPI ≥ 7.3, DIO1 16.85, NRST 19.26 mm (≥ 5.0, SPI ≥ 6.0); RF line to RF line 15.46 mm (R7 15.45); jacks 18.7 mm apart; module courtyards 7.67 mm | `requalify_r9.json` `rf.separations`; `rf.contract` R-11 |
| Supply | C311 1.97, C312 2.191, C310 3.639 mm from U31; C301 2.13, C300 2.556 mm from U30; GNSS VCC path 0.088 Ω (≤ 0.2) | `requalify_r9.json` `rf.contract` R-12; `gate/r9.json` R-12 |
| Limiter thermal | not re-solved: Q30's drain lead is 0.40 mm on B.Cu, R7's thermal bound kept (Inference, D-S4-03); the bench short test at −20 / +85 °C measures it | `R9_DECISIONS.md` D-S4-03 |

### DC, IPC-2152, reference planes

| Item | Result on `4f841a0e…` | Evidence |
|---|---|---|
| 7.7 A paths at 0.05 mm | RAW_ACT 0.80 mΩ, neck 7.89 mm on B.Cu, 12.6 °C; BAT_IN 0.16 mΩ, 8.15 mm B.Cu, 12.1 °C; ACT_FET_S 0.26 mΩ, 5.18 mm B.Cu, 20.4 °C (D12 20 / 20 / 30; R8 17.5 / 14.5 / 21.4; fc3d5b34 0.79 mΩ, 7.81 mm, 12.7 °C for RAW_ACT, the others equal); largest via barrel currents RAW_ACT 0.47 A, BAT_IN 0.61 A (5 vias over 0.5 A, none over 1 A), ACT_FET_S 0.22 A (RAW_ACT: 31 vias carry current, one fewer since D-F1-04). The RAW_ACT and ACT_FET_S necks lie at Q121 / Q120 and the BAT_IN neck wholly under J1, 0.24 mm from Q120's courtyard (`ordering_facts.json` `necks`): where the FETs' dissipation or J1's body dominates a thermal image, so on R9 D12's limits are a CAD check only and the stall test judges the FETs, the copper beside them and J122 (D-S10-06; R9P1-REQUIREMENTS-09) | `step10_evidence/dc/dc005_{raw,bat,fet}.txt` |
| Supply paths (26, 0.1 mm) | every output bound to the board; BAT_IN J1:1 → U9:5 2.32 mΩ (R8 17.26: U9 13.2 mm from J1.1); RAW_PROTECTED U9:6 → U7 77.11 mΩ (77 mV at 1 A, the largest drop at its load; R8 76.34) and → U11 16.22 mΩ (R8 47.29); USB_LIMITED U10:6 → U11:7 85.91 mΩ (43 mV at 0.5 A; R8 52.66: the trunk runs through U1's interior, D-S7-16; fc3d5b34 83.02, before C98 moved beside U11.7); VLOGIC C84 → U2 9.54 mΩ (R8 2.60, C16); every 3V3 path 1.18–44.85 mΩ, ≤ 4.5 mV at its load; CAM_5V to J9 2.88 mΩ; RAW_ACT → J124.2 10.14 mΩ (the fire row's 10.06 mΩ at 0.05 mm); every drop under 80 mV at its load (the full table: M3_R9 "Power") | `step10_evidence/dc/` (`dc_summary.txt`, one file per path); `step10/run_dc_r9.sh` |
| GND returns (0.1 mm, window x 0–46, y 50–102: upper bounds) | servo return 0.32 mΩ (J122's four GND pins → J1.2 at 7.7 A: 2.4 mV, 0.019 W; at mid-path In1.Cu 41 %, In2.Cu 29 %, B.Cu 21 %, F.Cu 9 %; 152 GND vias carry current, the largest 0.29 A, 0 over 0.5 A; R8 0.69 mΩ over its own window); fire-loop return 0.81 mΩ (Q124's source pins → J1.2, 2.3 mV at 2.8 A; at mid-path In1.Cu 71 %, F.Cu 29 %; the two GND vias beside Q124's source pins carry 1.23 and 1.00 A of the 2.8 A pulse for ≤ 20 ms, under 0.5 K by MARGIN_PRESCRIPTION P1-9's adiabatic pyro-trace figure scaled by the square of the current density, Inference; R8 recorded no fire-loop return); both upper bounds, the copper outside the window left out | `step10_evidence/dc/gnd_servo.txt`, `dc/fire_gnd.txt` |
| Critical-net reference (absolute) | R6 set 3,206 / 31,359 samples unreferenced (10.22 %), every one inside an own via antipad but one other-via sample (USB_DM's edge sample at CC1's via (7.85, 32.75)); extended set 3,931 / 83,715 (4.70 %), the same one other-via sample; no other cause (no sample over another net's fill, a split, a void or a keep-out); R8's accepted board on the same metric 0.1107 (5,186 of 46,845 samples, `tools/scorecard_r8_r9.json`; R8 kept the crystal's In2 keep-out, which R9's plane replaced, C14) | `step10_evidence/reference_audit.txt`, `reference_audit*.json` |

### Mechanical, hot-plug, IMU, firmware, fab

| Item | Result on `4f841a0e…` | Evidence |
|---|---|---|
| Vibration (plate model) | f1 256.6 Hz pinned, 362.9 / 434.8 / 614.9 Hz for the other support models, with the jacks only and the sled carrying the plugs (R8 208.7); 183.7 Hz pinned if the plugs hang on the jacks (P3 forbids it); under the 100 g quasi-static transverse load (D 5 pinned) the largest deflection is 0.66 mm at the west edge's mid-span (0, 54), beside the CH1 column (Inference inputs as R8's). Mode 1 peaks at (0.0, 52.5), where U4 sits at 0.76 and U5 at 0.89 of the peak amplitude (R8 0.18 / 0.18; R7 0.72 / 0.77); relative response at U4 18.1 g rms in mode 1, 18.8 over modes 1–6 (Miles, Q 10, 0.04 g²/Hz: a trend, Inference; R8 3.7 / 8.4): R9P1-MECHANICAL-01, part D | `gate/plate.json`, `gate/fit.json` (modes: R9P1-MECHANICAL-01's code on `plate_model.Plate`) |
| Fit (P2) | worst J9 mated 0.028 mm (R8's floor), J122 mated 0.50 (turned), J121 / J124 1.23, C84 1.37, worst bottom 2.37 (C72), deepest bottom part L1 4.62 mm below the top face (3.02 mm below the bottom face); supports 4.483 mm bottom (C98.1) / 5.008 mm top (TP30.1) (C98.1 at (42, 59.5), moved beside U11 by the fix pass; fc3d5b34 4.600 mm bottom, R300.2) | `gate/check_sh.txt`, `gate/fit.json` |
| Holes and washers | nearest pad to a hole centre 4.55 mm (C98.1, bottom, (42, 59.5), since the fix pass moved C98; fc3d5b34 4.62 mm, R83.1 at (42, 98)); GND on all four layers within each washer radius and no other net's fill; no pad within 6 mm of (4, 98) or (42, 4). Masked tracks of other nets do run under the hardware (R9P1-MECHANICAL-04): at (42, 59.5) RAW_PROTECTED (F.Cu, 0.40 mm) 2.15 mm from the centre (0.55 mm from the hole edge) under the top washer and BAT_FAULT_N 2.37 / LOGIC_SOURCE_ST 3.13 mm (B.Cu) under the standoff; at (42, 98) BAT_ENABLE (F.Cu, U9's enable node) 3.10 mm under the washer and BAT_FAULT_N 2.90 mm (B.Cu) under the standoff: nylon hardware only, no over-torque (ORDERING §7) | `requalify_r9.json` `mech.holes`; `sources/r9_review/fix1/fix1_measure.py` `hardware` |
| Tie holes | (15.6, 62) and (30.8, 59), centres 2.3 / 2.7 mm past J122's courtyard ends (M-3: 1–4 mm), the tie line within 0.71–2.21 mm of each plug's centre line; nearest bottom part to the channel R124 2.007 mm | `gate/r9.json` M-3; `ordering_facts.json` `parts` J122 |
| Tab windows and plan (T-1) | west y 0.5–7.25, 12.0–20.5, 53.5–101.5; east 0.5–27.0, 92.75–101.5 (both end thirds of both edges); four tabs, west y 0.5–5.5 and 96.5–101.5, east 8.75–13.75 and 96.5–101.5, each GND on all four layers and ≥ 5 mm from PYRO_BLOCK (D-S10-03) | `requalify_r9.json` `mech.tabs`; `step10_evidence/tab_plan.json` |
| Hot-plug premise (F9) | input protection 4.69–8.90 mm from J1.1 (≤ 10.6), U9 13.22 mm (≤ 27.07); R_b 2.32 mΩ (dc_solve), feed about 3.23 nH (estimate): U9 IN within 0.0021 V and × 1.028 slew of the input node (0.0036 V, × 1.037 at R8's 5 nH bound); R4's −14.6 V / 9.2 V/µs (M3_R4) become about −14.60 V / 9.46 V/µs at U9 IN, inside the TPS25947's −15 V / 10 V/µs (Inference inputs as R8 D76; D-S6-11) | `gate/r9.json` F9-1; `step10_evidence/hotplug_feed.json`; `dc/bat_u9.txt` |
| IMU axis map | U4 on the bottom at (12.0, 47.4), rotation 180 (D-S7-06): +X_imu = −x_board, +Y_imu = −y_board, +Z_imu out of the bottom face; **roll = −gyro_Y** (R5–R8 +gyro_Y), thrust reads −a_Y; lever arm x −11.0 mm, z −2.06 mm; centripetal 1.17 g at 1850 °/s, read as −a_X | `step10_evidence/r9_binding_note.json`; `gate/r9.json` M-7 |
| Firmware binding note | U1's map equals R8's pin table (0 pins changed, D-S1-07); R8's binding constraints carry over unchanged; board / netlist / pin-table hashes for a new R9 binding (AGENTS §3) | `step10_evidence/r9_binding_note.json` |
| ORDERING facts | assembly counts (top 76 SMD + 2 jacks + 5 THT + 14 test pads, bottom 136 + 10), edge distances, J3's legs, J2's pads, the coat parts, staking, U9's IN pin, the bottom pours, jack-to-ESD 0.5 mm, the necks against the FETs and J1, the THT pads' zone connections, the bare-contact vias (none since D-F1-04) | `step10_evidence/ordering_facts.json` (D-S10-06) |
| Fab, cost, stock (M1, M3) | 92 BOM lines, 219 placed parts, CPL verified (78 top + 133 bottom rebuilt, 8 placement-only), paste check OK, manifest bound; **$109.38 per board, 52 extended codes** (≤ $126.41 / 52), live JLC data 2026-10-26 00:57–01:00Z (valid 24 h); stock short none (U4 40, U30 34 in JLC stock); the CPL changed with C98, the BOM did not (`ab3d8171…`) | `step10_evidence/fab.txt`; `m3_design/assembly_review/fab/cost_check.json`, `stock_check.json` |

## R9 deviations for owner acceptance

Bound to `4f841a0e…` (review pass 1's fix pass; step 10's list was bound to `fc3d5b34…`). Each item stays a deviation
from REQUIREMENTS M2 (or from r9_plan's done rows) until the owner accepts this list, dated. **Accepted by the owner on
2026-10-25** for board `4f841a0e…`, including the agent decisions in part D, with the board length kept at 102 mm (C1, option
(c)). Every C row gives R8's
figure on the same metric (R8 `cc044ea0…`: `tools/scorecard_r8_r9.json`, check_r9 run on R8's committed board, or R8's
records); **worse** marks a row where R9 is worse than the accepted fallback.

### Owner summary

- **No gate exception.** route_check r9 has an empty allowlist and no leftover (A, B); check_r9 passes every rule.
- **Sixteen done rows missed** (C1–C11d), none a hard row or a safety rule: the length (102 mm, owner decision 1's
  fallback, kept by the owner on 2026-10-25 over C1's 98 mm and 100 mm options), X2g's bounding box, the two detour-ratio nets (S8 / S9), the bend
  count S10b, five routing-adjacency counts (Y1, Y1b, Y2c, Y7, Y5), four plane rows (P6, P7, P10, R6b), X3f and the
  composite index, plus the S4 stretch.
- **Where R9 is worse than R8 on the same metric:** X2g 7 / 6, S10b 260 / 231, Y1 / Y1b / Y2c 30 / 14 / 11 against
  27 / 8 / 4, Y5 34 / 26, P7 9 / 1, S4 57 / 55; R6b beats R8 only with the crystal plane (C11, C14); in C13 the fast-net
  pad, the tie channel and the via rings; in C16 four supply paths; C19–C25 as marked.
- **Geometric facts to accept:** rule G's 0.112 mm margin at U1.3's pin entry (C12), the thin but legal margins (C13),
  the crystal's local In2 ground plane in place of R5's void (C14), the actuator gate pads at the zone clearance from GND
  (C19), the solid RF and J122 GND joints (C20, C21), the unstitched GND copper and pad reach left after the copper stage
  (C22).
- **Improbable-fault and layout items:** the two far bypass capacitors (C23), the camera branch's soft-fault exposure
  (C24), seven single-via rail links (C25).
- **Agent decisions taken on the owner's behalf** (D): U4 turned 180° with a new axis map, the mid support at (42, 59.5)
  with the sensors on mode 1's antinode, 110 designators hidden, the four-tab panel plan, D30 / C303 placed off R7's spots,
  check_actuators changed against owner decision 2's wording, and the fix pass's TP120 via, C98, J122 relief and C121
  corridor decisions.

### A. `route_check` allowlist: none (`step10_evidence/gate/route.json`: allowed 0, stale 0)

### B. Non-critical leftovers: none (`gate/route.json`: leftovers 0, missing 0, stale 0)

### C. Review deviations the gate does not hold

| # | Item | R9 (`4f841a0e…`) | R8, same metric | Record |
|---|---|---|---|---|
| C1 | Board length X1 | 102.0 mm (done ≤ 100; plan 98) | 118.0 mm | D-S3-03. 98 and 100 mm fail only under r9_plan §2's hard row X9 ≥ 5.94 mm (RF parts from U1 / U3 / Y1: R8's measured R306–U1 distance), not under F10's 5 mm (R9P1-REQUIREMENTS-01). Owner options: (a) reclassify R306 / R310 / R313 / R315 out of F10's RF-part list and return to 98 mm (`step3_evidence/option_98mm_f10.txt`); (b) 100 mm with the four interface resistors 5.0–5.94 mm from U1, a relaxed hard row with F10 still met: `m3_design/r9_kill_path.py` with the part separation at 5.0 mm holds at 100 mm, total lane detour 6.96 mm against 2.62 mm at 102 (98 mm still fails); only the resistor spots are shown, the rest of a 100 mm board is Inference; (c) keep 102 mm, the board as built. **Owner decision 2026-10-25: (c), keep 102 mm** (R9_OWNER_DECISIONS item 6) |
| C2 | X2g (nets through the CH1 parts' box) | 7 | 6, **worse** | none within 3 mm of armed copper (X2 = X2b = 0); D-S6-13 (ACT_GATE to TP121), steps 6–7 |
| C3 | S8 / S9 (nets over 1.6 × / 2 × their MST) | 2 | 4 / 4 | RADIO_TXEN (the TXEN loop round U31's west side on B.Cu, R7 / R8's, keep-out-forced, D-S4-06); RAW_ACT_SENSE_MCU 2.24 mm on a 0.90 mm MST (1.34 mm excess, one via on pin 34's line, D-S7-12) |
| C4 | S10b signal bends | 260 (≤ 231) | 231, **worse** | steps 4–7 (`step8_evidence/step8_deltas.txt`) |
| C5 | Close pairs Y1 / Y1b / Y2c | 30 / 14 / 11 (≤ 10 / 0 / 0) | 27 / 8 / 4, **worse** | every pair DRC-legal (≥ 0.15 mm); the sweep lists each: 32 track / via pairs under 0.2 mm, 28 pad-to-copper pairs (`step10_evidence/m2_sweep.txt` adjacency, adjacency_pad; fc3d5b34 33 / 28) |
| C6 | Y7 via step | 1 | 1 | CC1's 0.113 mm track end inside its via (7.85, 32.75) stands for a 0.22 mm offset jog through the via on CC1, a non-critical CC pull-down: drawn straight from the via centre the run fails route_check's tiny-jog test; the DRC-clean alternatives tried in the J3 / D4 / USB_DM pocket (via 0.15 mm north with R7 moved, via at (8.1, 32.55)) are not clean (R9P1-ROUTING-03; `m2_sweep.txt` via_step); for the owner's acceptance |
| C7 | Y5 via folds | 34 (≤ 10) | 26, **worse** | layer changes whose two arms leave within 45° (escape vias beside U1, the servo and VBUS lanes; `m2_sweep.txt` via_fold) |
| C8 | P6 In2 perimeter | 1479.4 mm (≤ 900) | 1752.2 mm | inherent to four In2 regions, each boundary counted twice (Inference, D-S6-13) |
| C9 | P7 outer GND islands with ≤ 1 via | 9 | 1, **worse** | recorded pockets, no pour trims (D-S8-15); the fix pass added none (its copper stage refuses a via that would add one, D-F1-07) |
| C10 | P10 largest GND-via distance | 7.32 mm (≤ 7.0) | 9.65 mm | at (31.25, 91.25), the BAT_IN battery entry (D-S8-16) |
| C11 | R6b critical-reference share | 0.1022 (≤ 0.08) | 0.1107: R9 better only with C14's crystal plane; with R5's void restored R6b is 0.1396, **worse** | every sample inside an own antipad of the 12 critical layer-change vias but one; 0.08 needs fewer critical vias or smaller vias than the board's rules (D-S8-17) |
| C11b | X3f RF-interface track | 291.8 mm (≤ 250) | 321.3 mm | steps 4 and 7 |
| C11c | index_r9 | 83.8 (≤ 73) | 100 (by definition) | the composite of the misses above (fc3d5b34 84.8) |
| C11d | S4 stretch | 57 signal vias (done ≤ 70 met; stretch 55) | 55, **worse** | D-S7-19 |
| C12 | Rule G margin at U1.3 | 0.412 mm against 0.3 (margin 0.112 < the 0.2 floor) | 0.219 mm under the same P-1b scope (GATE_N's via to ARM1_SENSE, below 0.3); Z1g 0.0 under R8's own scope | GATE_N's straight entry into U1.3 between the no-net sentinel pins U1.2 / U1.4 (0.5 mm LQFP pitch); every other rule-G pair ≥ 0.5 mm; the scorecard's Z1g (whole segments in PYRO_BLOCK) 0.27 mm (D-S5-13); U1.3's pad itself keeps 0.55 mm from QSPI_IO2, the nearest passing net (P-7b, D-F1-01) |
| C13 | Thin, legal margins | H+ 1.225 mm (margin 0.025; Q124.5–R129.2); fit J9 mated 0.028 mm; R-7 radio west 2.405 / GNSS east 2.38 mm against 2.5; R-12 C301 2.13 mm; R-1 C300 21.955 / 22.0 mm; D120's 3V3 lane 0.39 mm from J122.2 (0.3 rule); R-10's nearest fast-net pad 5.005 mm against 5.0 (R306–USB_DM); M-3's tie channel 2.007 mm against 2.0 (R124); P-6's bare actuator-gate pad 1.03 mm against 1.0 (R120.2–C120.1); K-copper's via ring to a paste aperture 0.005 mm against 0 (GND via (42.0, 81.26) to C8.2's paste); own-net via rings closer to a pad opening than JLC's 0.10 mm mask web: 23 pairs at 20 vias, worst 0.005 mm (that via, C8.2 / C9.2), 0.007 mm (R63's GND via (16.82, 55.3)), 0.014 mm (D4's VBUS via (11.95, 34.1)), and 21 ring-to-paste pairs under 0.1 mm at 18 vias: every pair own-net, every hole ≥ 0.107 mm from its opening (M2 holds), tented; JLC cannot hold such a web, so the likely effect is a sliver of exposed ring and a smaller fillet (Inference) | H+ 1.025 (fails 1.2); J9 0.028; R-7 radio west 2.405 / GNSS east 2.34; R-12 C301 2.184; R-1 no strip boundary (FB30 25.645); fast-net pad 5.075, **worse**; tie channel 2.264, **worse**; P-6 0.634; via ring 0.025, **worse**; R8's class 12 pairs at 11 vias, worst 0.025 mm, **worse** | `gate/r9.json`; `sources/r9_review/fix1/fix1_measure.py` `via_openings`; D-S4-02, D-S5-05; R9P1-REQUIREMENTS-06, R9P1-DFM-04 (moving the three vias under 0.02 mm and tightening via_paste's ring check are optional, at the next copper change) |
| C14 | Crystal plane | R5's In2 void under Y1 is now its local GND plane (R9_GND_In2_Y1), bonded to In1 by nine vias (six with their centres inside, (16.0, 50.6), (19.69, 45.75) and (21.95, 47.0) overlapping its edge, each flashed on In2) (U1.10's VSS, the nearest MCU ground, about 1 mm of F.Cu from (16.0, 50.6); U4's GND pins return through (14.6, 47.4)); ST AN2867 §5.1's "distinct from the application PCB ground plane" is deliberately not followed (multi-point bonding to a solid In1, Inference); about +0.37 pF per HSE node (Inference; bench: HSE frequency by MCO) | the void (a keep-out) | D-S8-20 (the owner may restore the void at R6b 0.1396, worse than R8's 0.1107); R9P1-PLANES-04 |
| C15 | M2 review sweep (`m2_sweep_r9.py`: R8's sweep, profile r9) | chain detours on nets without a pour 18 (12 with no redraw; candidate redraws for VLOGIC, SERVO4_MCU, LED_RED, GNSS_ANT_GATE, RADIO_RXEN and USB_DP, which review pass 1 tried and keeps: GNSS_ANT_GATE's and VLOGIC_SENSE's are clean but marginal, LED_RED's, VLOGIC's and QSPI_IO3's are worse elsewhere, the rest add a sub-0.1 mm segment, bends, a diagonal pad entry or a minimum-clearance pass, R9P1-ROUTING-05); routes with ratio ≥ 1.25 or extra vias: 38 nets listed; pad-edge track ends 5 at 3 pads (C24.2, R102.1, R172.2; 0.013–0.025 mm inside the edge) and, at a 0.08 mm depth and corners (R9P1-ROUTING-04): C100.1 (two 3V3 tracks offset 0.055 mm through the pad), R162.2 (a corner graze, 0.067 mm), TP90.1 (a corner entry, its via pushed east by the corridor lanes), C91.1 (a corner end), C300.1 0.04, C94.1 0.05, L3.1 0.04 and U9.9 0.05 mm, all connected and DRC-clean (R173.1's and J2's are deliberate, D-S5-09, D-S7-11); short hops 7 (power vias with no GND via within 1.5 mm: 3V3 × 3, CAM_IO_3V3 × 2, 3V3A, CAM_5V; information, AGENTS §3 asks it of critical nets only); bumps on non-critical nets 1 (VLOGIC_SENSE, 0.54 mm shorter redraw); margin-free search 2 bump candidates (RADIO_SCK_MCU 0.21 mm shorter, VLOGIC_SENSE) and 7 chain-detour redraws at DRC's own threshold | chain detours 23, routes 28 (Y3 / Y4) | `step10_evidence/m2_sweep.txt`, `m2_sweep.json` (D-S10-12) |
| C16 | Earlier steps' Minors | RAW_PROTECTED → U7 77.11 mΩ (no limit; D-S8-09); USB_LIMITED U10:6 → U11:7 85.91 mΩ (43 mV at 0.5 A; fc3d5b34 83.02, before C98 moved; its trunk runs through U1's interior, D-S7-16); VLOGIC C84.1 → U2 9.54 mΩ (5 mV at 0.5 A, D-S6-13); RAW_ACT → J124.2 10.14 mΩ (the 1.0 mm RAW bar from the spine; the fire row's 10.06 mΩ at 0.05 mm, inside F7's budget); 3V3 L1:2 → C100.1 44.85 mΩ (≤ 4.5 mV at its load); CAM_FAULT_N one bend more (D-S8-07); the guard via 0.075 mm from C10.2 / C11.2 on B.Cu (same net, tented) | 76.34, **worse**; 52.66, **worse**; 2.60, **worse**; 0.44, **worse**; 18.36, **worse** | step handoffs 5, 6, 8; `step10_evidence/dc/` (R9P1-REQUIREMENTS-05) |
| C17 | Open inferences | the buzzer's 4 kHz drive 4.5 mm from the radio module's keep-out (D-S7-14); USB_LIMITED's 0.45 A limit from R8 D42 (not re-derived from R85); Q30's thermal bound (D-S4-03); the return-loss cascade's parasitics (D-S10-02) | — | bench items in ORDERING §5 |
| C18 | Vias in a bare contact | none: review pass 1 moved the two RAW_ACT vias that opened into TP120 (D-F1-04; D-S10-14's exception lapsed) | 1 (TP122's A8) | `ordering_facts.json` `vias_in_bare_contacts` (empty) |
| C19 | Actuator-switch gate pads to the GND pour | five bare B.Cu pads of ACT_GATE / ACT_DRV (C120.2, R121.1, Q121.4; Q122.3, R121.2) 0.151 mm from the masked GND pour (the zone clearance; R120.2 0.933, Q120.4 1.436, TP121 1.001 mm): a bridge needs a mask breach (the web is ≥ JLC's 0.10 mm, Inference) and turns Q120 / Q121 on with the power switch open (fail-on), which ORDERING §5's "RAW_ACT dead with the switch open" step screens; the pyro gate pads' 0.151 mm holds their gates off | the same class (R8 C12b #18) | REQUIREMENTS "Accepted risks" (retired for the pyro gate nets only); owner option, as R8 D109: a DRU zone rule keeping ACT_GATE / ACT_DRV pads ≥ 0.3 mm from GND zones (the fill changes, so the fill-dependent gates re-run); `sources/r9_review/fix1/fix1_measure.py` `gate_pads_to_gnd`; R9P1-DFM-02, R9P1-PYRO-02 |
| C20 | RF ground pads solid | D30.2 and D31.2 (the RF clamps' GND pads) and the DNP shunt lands C303.2, C305.2, C313.2, C314.2 join the GND pour solid (pad-level FULL), the house relief rule's RF exception (the shortest return beside the RF line; their vias ≤ 0.23 mm, R-7) | the same (R8 C16, R7 C13) | R9P1-REQUIREMENTS-04 |
| C21 | J122's GND pins solid | J122.3 / 6 / 9 / 12 join the GND pours solid on F.Cu, In1 and B.Cu (J122.3 also In2), for the 7.7 A servo return (≈ 1.9 A per pin). With the zones' THT relief the pins would not starve on R9 (DRC clean in the fix pass's build; 4 / 4 / 2 spokes by the reviewers' count), but J122.3's 0.5 mm relief ring closes the F.Cu channel between D120's 3V3 lane (x 17.9) and J122's west column and leaves a 0.86 mm² GND piece joined by one spoke (a new single-stitch island, P7), so the pins stay solid; ORDERING §4 asks for preheat and a hole-fill check | solid (R8 C17, whose reason, J122.3 starved on F.Cu, does not hold on R9) | D-F1-06; R9P1-POWER-04, -DFM-03, -REQUIREMENTS-04 |
| C22 | Unstitched GND copper and GND-pad reach | through-copper reach on the ground aid's 0.1 mm raster forward of the strip (r9_ground_check's copper gate holds GND pads of C / U / Q / J parts ≤ 5 mm and copper ≤ 8 mm of copper from a via, but these recorded exceptions, each a cluster the aid's copper stage found no legal via in): the strip between the RAW_ACT pour and VLOGIC's sense tap 9.50 mm at (37.45, 73.75) (In2's 3V3 finger under it takes no antipad, D-S8-02); D-S8-05's guard strip beside ARM1_SENSE 9.37 mm at (28.95, 68.35) and 8.61 mm at its north end (28.85, 59.95) (RAW_ACT on In2 and B.Cu under it); J9's GND piece 8.95 mm at (41.75, 48.45) and 8.05 mm at (39.85, 48.45); the piece over the FET pair 8.48 mm at (31.15, 87.75) (ACT_FET_S on B.Cu under it); GND pads beyond 3 mm: J9.2 6.99 mm (the camera return; recorded), R102.2 4.68, C87.2 4.25, R130.2 3.81, R103.2 3.74, C122.2 3.74, C28.2 3.69 mm; the worst outer copper F.Cu 9.50 mm, B.Cu 6.65 mm (p95 4.13 / 3.01 mm); thin outer GND pieces (route_check thin_pieces, ≥ 2 mm, ≥ 0.15 mm²) F.Cu 50 / 69 and B.Cu 59 / 86 narrower than 0.75 / 1.0 mm | F.Cu worst 15.36 mm; pads R123.2 12.98, Q122.2 12.42, U13.2 9.28, C93.2 7.24, J9.2 6.92 mm (R8 C15) | D-F1-07; `sources/r9_review/fix1/fix1_measure.py` `gnd_reach`, `thin_gnd`; `m3_design/r9_ground_check.py` COPPER_EXCEPT; R9P1-PLANES-01..03 (fc3d5b34: 28.41 mm at (37.45, 73.75), C121.2 16.10, R103.2 20.67, the forward strip 12.45 mm; now C121.2 1.50, the strip 6.04) |
| C23 | Power-IC bypass capacitors far from their pins | C83 (U10's 100 nF input bypass, with C28) on U10.3's EN branch, 11.64 mm of 0.3 mm track from U10.1 (TI SLVS841F pin table, §12.1; no legal spot on U10.1's run; USB is bench-only and D4 clamps VBUS); C82 (U9's only output capacitor) about 20 mm of copper from U9.6, 8.08 mΩ (TI SLVSFC9C §8.3.1, §8.4.1), with D9, the output clamp, 3.35 mm from U9.6 | C83 1.73 mm after R8 D88, **worse**; C82 8.1 mm, R8's recorded §8.4.1 deviation, **worse** (R7 2.25 mm); D9 7.3 mm | D-F1-05; R9P1-POWER-01 (C98 fixed: 1.94 mm of track from U11.7, was 5.29); M3_R9 "Power" |
| C24 | RAW_PROTECTED camera branch, soft-fault exposure | the 0.4 mm, 44 mm F.Cu branch to U7 rises 10.1 °C at U7's 1.24 A limit; a resistive fault on it drawing 1.5–3.96 A is limited by neither U7 (downstream) nor U9 (3.96–4.84 A with R84 = 750 Ω) and would heat it about 15–103 °C (IPC-2152, Calc): an improbable-fault item | the records sized R8's trunk against R5's 2.2 A limit | D-F1-08; M3_R9 "Power"; R9P1-POWER-02 |
| C25 | Single-via rail links | seven rail-carrying vias, each alone carrying its rail: the 3V3 feed, U11's battery input, the hold-up, the camera feed, CAM_5V, U1's VDDA / VREF+ hop, USB_LIMITED's two in series (barrel loads in M3_R9); accepted single points (MARGIN_PRESCRIPTION R15) | listed in M3_R8; U9.6's output was single there (two vias on R9) | D-F1-09; M3_R9 "Power"; R9P1-POWER-03 |

### D. Agent decisions taken on the owner's behalf

| Decision | What | Basis |
|---|---|---|
| D-S7-06 | U4 turned 180° (axis map roll = −gyro_Y; check_r9 M-7 keys the rotation on the revision); the firmware binding must carry it and a bench sign check precedes flight | the only routable IMU knot at the placed spot (survey 1.4: IMU rotation free with a recorded map) |
| D-S3-08, D-S6-09 | the mid support at (42, 59.5): owner decision 5's (42, 55.5) moved 4 mm forward with the forward block (102 mm); kept because the DC solves pass with it. **Consequence** (R9P1-MECHANICAL-01): with the west edge unsupported for 94 mm, mode 1 peaks at the west edge's mid-span (0, 52.5), where U4 and U5 sit (0.76 / 0.89 of the peak; R8 0.18 / 0.18), about 2.2 × R8's board-amplified vibration at U4 over modes 1–6 (a trend, Inference; R7's level). **Alternatives:** owner decision 5's fallback (4, 49.5), 248.8 Hz and about a third of the exposure, or a support near U4; each needs U5 and the west band re-placed. ORDERING §5's tap check measures U4's exposure | D-S3-03's length; R9_OWNER_DECISIONS item 5 ("if the DC solve holds"); M3_R9 "Mechanical" |
| D-S9-03 | 139 designators shown, 110 hidden and kept on F.Fab (R8: 168 / 81), listed in `step10_evidence/post_report.json` | AGENTS §3's hiding rule |
| D-S10-03 | four 5 mm panel tabs, each GND on all four layers, none beside the CH1 column (ORDERING §3) | T-1 windows; R8P3-POWER-05; MLCC crack risk |
| D-S4-02 | D30 turned and C303 at the bias node (deviations from R7's chain in the jack frame) | stitching spots on both sides of the line; the cascade re-run (C17) |
| D-S1-02 | `m3_design/check_actuators.py` changed, against owner decision 2's "check_actuators unchanged": contract rules 1–14 and 16 unchanged; rule 15b's fixed R4 rectangle became a content-based containment test (one area on all four layers, restricting nothing, containing every CH1 courtyard + 1 mm, all block-net copper and the exit copper within 3 mm; argued stricter, `test_check_actuators_15b_is_rule_based` seeds a notch and a restriction); DRU_SHA and rule G's PYRO_RULE_SHA re-pinned to the P-1b scope and the fill margins | forced by the B-spine geometry (the R4 rectangle cannot hold the west column) and by P-1b's DRU edit, which the file pins (D-S2-11, D-S5-12); R9P1-REQUIREMENTS-03 |
| D-F1-02 | RADIO_TXEN's loop at the 0.2 mm signal width (R7's 0.15 mm) and R7's three module-frame GND vias at U31's ground pins | R9P1-ROUTING-01, R9P1-RF-01 |
| D-F1-04 | TP120's row via (29.6, 78.2) dropped and (31.0, 78.2) moved to (31.5, 78.2): no via in the test pad, one RAW_ACT via fewer (the RAW_ACT solve unchanged within 0.01 mΩ) | R9P1-ROUTING-02 (moving TP120 is blocked) |
| D-F1-05 | C98 moved beside U11.7 / U11.6; C83 and C82 left where they are and recorded (C23) | R9P1-POWER-01 |
| D-F1-06 | J122's GND pins kept solid after the relief trial (C21) | R9P1-POWER-04 / -DFM-03 offered either |
| D-F1-07 | C121.2's exception to the 7.7 A corridor rule (a GND via may cut the RAW_ACT pours inside the box x 34.55–35.75, y 61.3–64.85, east of the pad and off the RAW_ACT path; the via at (35.6, 64.8) on the B.Cu pour's east edge), the ground aid's copper stage and the ground gate's copper exceptions (C22) | R9P1-PLANES-01 / -02; the RAW_ACT solve 0.80 mΩ, 12.6 °C |

### E. Information-only `route_check` instances (114; counted, never gated)

pad_end_offcentre 64, segment_inside_pad 11, passes_through_pad 9, width_change_junction 8, extra_bends 8, u_turn 7,
power_via_no_gnd 7 (`gate/route.json` instances; by class: power 62, other 33, rf / rfif 10, pyro 6, spi 1, usb 1,
actuator 1). Each is a pad entry or junction route_check reports and does not judge (AGENTS §3: the rest is checked in
review); none is a rule instance.

### F. M2 review coverage (swept on `4f841a0e…`)

| Category | Swept by | Result |
|---|---|---|
| Rule instances, hygiene, detours on critical nets, removable bumps | `tools/route_check.py` r9 (gate) | 0 failing |
| Chain detours on nets without a pour | `m2_sweep_r9.py` chain_detour | 18 (C15) |
| Adjacency under 0.2 mm (copper / pads) | adjacency, adjacency_pad | 32 / 28 (C5) |
| Via steps, poured hops, via folds | via_step, poured_hop, via_fold | 1 / 0 / 34 (C6, C7) |
| Route ratios and extra vias, every net without a pour | routes | 38 listed (C15) |
| Pad-edge track ends | pad_edge | 5 ends at 3 pads (C15) |
| Short hops (power vias without a GND via) | short_hop | 7 (C15) |
| Bumps on non-critical nets; margin-free search | bumps_all, margin_free | 1; 2 + 7 (C15) |

## Review pass 1

Eight independent reviewers (pyro and arming, requirements, RF, power, planes, routing, mechanical, manufacturability)
and a gate-integrity reviewer reviewed step 10's board `fc3d5b34…` on 2026-10-25
(`m3_design/assembly_review/sources/r9_review/pass1_*.md`). **Result: 0 Critical; 1 Major (R9P1-PLANES-01), which the
fix brief carried as a confirmed Minor; 50 Minor.** The fix pass (`sources/r9_review/fix1_progress.md`,
`sources/r9_review/fix1_handoff.md`; decisions R9_DECISIONS D-F1-01 … D-F1-11) changed the copper only through the R9
generators and tables (`m3_design/r9_build.sh` rebuilds the board), weakened no check and relaxed no pyro, arming or
actuator safety rule; it added three gate rules (check_r9 P-7b, r9_ground_check's copper gate, R-8 over U31's body) and
made two tools deterministic. Severity is the reviewer's; "brief" is the fix brief's verdict (every item it listed was
confirmed; the others were not passed to the fix pass). Dispositions: **fixed**, **listed** (a measured deviation for the
owner, part C / D), **not a defect**, or **open** (not in the brief; left for the next pass or the owner).

| Finding | Severity / brief | Disposition | What changed, measured on `4f841a0e…` unless noted |
|---|---|---|---|
| R9P1-PYRO-01 QSPI_IO2 0.25 mm in front of U1.3 (GATE_N) | Minor / confirmed | **Fixed** (copper, D-F1-01) | the east run on y 50.6: U1.3's pad 0.55 mm from QSPI_IO2 (fc3d5b34 0.250; R8 0.75), 3V3 1.25, IMU_INT1 1.369 mm; check_r9 P-7b holds U1's gate pin pad ≥ 0.5 mm from any non-U1, non-GND copper (seeded test) |
| R9P1-PYRO-02 coating record omits U1's own pins and the 0.151 mm pours | Minor / confirmed | **Fixed** (records) | the coating row below and ORDERING §5 name U1.6 (3V3) 1.20 mm and U1.1 0.70 mm from U1.3 and the pours at 0.151 mm from the bare gate pads; the actuator gate nets are C19 |
| R9P1-PYRO-03 JLC's pin-1 mark on our pad 2 (J121 / J124) | Minor / confirmed | **Fixed** (records) | ORDERING §4: an order remark and an expected DFM query (with R9P1-DFM-01) |
| R9P1-REQUIREMENTS-01 the 102 mm cause | Minor / confirmed | **Fixed** (records) | X9 ≥ 5.94 mm, not F10's 5 mm; C1 gains the 100 mm option (M3_R9, STATUS, the done-row table, C1, the step-3 handoff) |
| R9P1-REQUIREMENTS-02 Z4 reported met with two vias in TP120 | Minor / confirmed | **Fixed** (copper and tool, D-F1-04) | on fc3d5b34 Z4 = 2 (33 met, 17 missed); TP120's opening now holds no via (Z4 = 0); the scorecard counts vias in every TP* pad |
| R9P1-REQUIREMENTS-03 check_actuators changed against owner decision 2's wording | Minor / confirmed | **Fixed** (records) | part D row D-S1-02; "R9 acceptance" reworded |
| R9P1-REQUIREMENTS-04 two zone-connection exceptions unlisted | Minor / confirmed | **Listed** | C20 (D30.2 / D31.2 solid, the RF exception), C21 (J122's GND pins solid, with the relief trial, D-F1-06); M2's pointer |
| R9P1-REQUIREMENTS-05 R8 comparisons not like-for-like | Minor / confirmed | **Fixed** (records) | every C row gives R8's same-metric value, worse rows flagged; C11 / C14 say R6b is 0.1396 without the crystal plane; C16 gains RAW_ACT → J124.2 and 3V3 → C100; F10 compares R-13 with R8's 65.98 mm |
| R9P1-REQUIREMENTS-06 C13 omits the thinnest margins | Minor / confirmed | **Fixed** (records) | C13 lists R-10's fast-net pad, M-3's tie channel, P-6, the via-ring classes; F10 quotes the fast-net pad |
| R9P1-REQUIREMENTS-07 F10 swaps the stitching sides | Minor / confirmed | **Fixed** (records; R-7 reports compass sides, D-F1-03) | F10 and the RF table: GNSS east 2.38 / west 1.75, radio west 2.405 / east 1.70 mm (R8 GNSS east 2.34 / west 2.725) |
| R9P1-REQUIREMENTS-08 IGN–BUS1 wire-entry adjacency unanalysed | Minor / confirmed | **Fixed** (records) | FMEA_REDUNDANCY's R9 row (I-4 / V-16) and ORDERING §7: the entries 5.15 mm apart, a stray strand bypasses R134, checked at termination; D-S10-09 corrected |
| R9P1-REQUIREMENTS-09 the stall test's D12 framing; BAT_IN's neck not at an FET | Minor / confirmed | **Fixed** (records) | F4, ORDERING §5, the DC row, MARGIN P1-9 and AGENTS: on R9 D12 is a CAD check only; BAT_IN's neck lies under J1, 0.24 mm from Q120's courtyard and wholly under J1 |
| R9P1-REQUIREMENTS-10 stale record lines (a)–(g) | Minor / confirmed | **Fixed** (records) | P2, "R8 acceptance", the In2 areas, M1's U4, the R8 reference figure, MARGIN R14's R9 clause, M2's R9 pours and K-legends |
| R9P1-RF-01 the radio module's ground pins lost R7's vias | Minor / confirmed | **Fixed** (copper, D-F1-02) | R7's three module-frame vias: U31.2 / U31.7 / U31.16 0.20 / 0.35 / 0.35 mm of copper from a via (fc3d5b34 1.154 / 1.095 / 1.05 mm; R7 0.20 / 0.35 / 0.35) |
| R9P1-RF-02 stitching sides wrong; C303's stub text | Minor / confirmed | **Fixed** (records; R-7 evidence east / west) | F10, the RF table and ORDERING §4 |
| R9P1-RF-03 R-5's attribution nondeterministic | Minor / confirmed | **Fixed** (tool, D-F1-03) | nearest pad, sorted designators; R-5 equal in two runs (two separate gate runs on 4f841a0e give identical check_r9 reports, R-5's split and P-0's pairs included) |
| R9P1-POWER-01 three bypass capacitors regressed | Minor / confirmed | **Fixed** for C98 (copper, D-F1-05); **listed** C83, C82 (C23) | C98.1 1.94 mm of track from U11.7 (was 5.29); C83 11.64 mm (no legal spot on U10.1's run); C82 the TPS25947 §8.4.1 deviation with D9 3.35 mm from U9.6; D-S6-06's citation corrected |
| R9P1-POWER-02 U9's limit is 3.96–4.84 A | Minor / confirmed | **Fixed** (records, D-F1-08) | D-S6-05, the r9_power.py comment, M3_R9's RAW_PROTECTED IPC-2152 check at the coordinated limits; the camera branch's soft fault accepted as improbable (C24) |
| R9P1-POWER-03 single-via rail links undocumented | Minor / confirmed | **Fixed** (records, D-F1-09) | M3_R9 "Power" lists the seven, accepted single points (MARGIN R15) |
| R9P1-POWER-04 J122's GND pins solid, unlisted | Minor / confirmed | **Listed** (C21, D-F1-06) | the relief was built: DRC clean (4 / 4 / 2 spokes by the reviewers' count), but a new single-spoke 0.86 mm² F.Cu GND piece; kept solid |
| R9P1-POWER-05 the DRU's relief comment (0805 / 1206 pads on spokes) | Minor / not in the brief | **Fixed** (records) | one line in M3_R9 "Ground"; the DRU comment stays (check_actuators pins the file) |
| R9P1-PLANES-01 C121's GND return 11.98 mΩ through a 0.37 mm neck | Major / confirmed as Minor | **Fixed** (copper and gate, D-F1-07) | C121.2's return 1.38 mΩ, 87 % on In1 through the copper stage's via (35.6, 64.8) (fc3d5b34 11.98 mΩ; C150's 2.58, unchanged); C121.2's copper reach 1.50 mm (16.10), R103.2's 3.74 (20.67); RAW_ACT_F's 29.75 edge runs to y 76.6, so the guard strip's 0.37 mm neck is 0.72 mm; r9_ground_aid's copper stage and C121.2's corridor exception; r9_ground_check's copper gate (pads ≤ 5 mm, copper ≤ 8 mm of copper from a via, six clusters and J9.2 recorded, C22); the RAW_ACT solve 0.80 mΩ, 12.6 °C at 0.05 mm (fc3d5b34 0.79, 12.7) |
| R9P1-PLANES-02 the forward-edge GND strip 12.5 mm from a via | Minor / confirmed | **Fixed** (copper) | the copper stage's via (32.9, 99.85): the strip's worst point 6.04 mm of copper from a via (12.45; the reviewer's trial 6.00) |
| R9P1-PLANES-03 no record of unstitched pieces and pad reach | Minor / confirmed | **Fixed** (records and gate) | C22 (the method, the worst pieces and pads, their reasons); r9_ground_check's copper gate |
| R9P1-PLANES-04 the crystal plane's AN2867 "distinct" clause and via count | Minor / not in the brief | **Fixed** (records) | C14 and D-S8-20: nine bonding vias, the clause deliberately not followed |
| R9P1-PLANES-05 the reference gate samples only the R6 and extended nets | Minor / not in the brief | **Open** | a gate change for the next pass: sample route_check's SIGNAL_CRITICAL classes with the two 0.400 mm tangencies as REF_STRAY entries |
| R9P1-PLANES-06 M3_R9 gave step 6's In2 areas | Minor / not in the brief | **Fixed** (records) | the final board's areas (with REQUIREMENTS-10 (c)) |
| R9P1-ROUTING-01 RADIO_TXEN the only 0.15 mm net | Minor / confirmed | **Fixed** (copper, D-F1-02) | 0.2 mm; the grid via 0.05 mm west; five widths |
| R9P1-ROUTING-02 TP120's two in-pad vias | Minor / confirmed | **Fixed** (copper, D-F1-04) | see REQUIREMENTS-02; C18 lapsed |
| R9P1-ROUTING-03 CC1's via step hides a 0.22 mm jog | Minor / confirmed | **Fixed** (records) | C6 and D-S10-12 say so; no DRC-clean alternative (cc1b / cc1c / cc1d) |
| R9P1-ROUTING-04 pad-edge and corner entries missing from C15 | Minor / not in the brief | **Fixed** (records) | C15 lists them with their reasons |
| R9P1-ROUTING-05 C15's candidate redraws | Minor / not in the brief | **Fixed** (records) | C15 records that pass 1 reviewed them and keeps them |
| R9P1-MECHANICAL-01 the IMU and barometer on mode 1's antinode | Minor / confirmed | **Fixed** (records) and **listed** (part D) | M3_R9 "Mechanical", part D's D-S3-08 / D-S6-09 row, ORDERING §5's tap check (accelerometer at U4, U4 logged) |
| R9P1-MECHANICAL-02 bay stack and harness records | Minor / confirmed | **Fixed** (records) | M3_R9's bay paragraph; ORDERING §7 battery lead below the board and sled, the sled's forward end, the servo-lead dress; the VEHICLE row proposal in the fix handoff |
| R9P1-MECHANICAL-03 P2's stale R8 clause | Minor / confirmed | **Fixed** (records) | P2 |
| R9P1-MECHANICAL-04 hardware, staking and foam neighbours | Minor / confirmed | **Fixed** (records) | ORDERING §5 / §7 and the holes row: the masked tracks under the hardware, J30's and C121's staking limits, the foam off U4 |
| R9P1-MECHANICAL-05 the DB128L's stacking nubs unmodelled | Minor / not in the brief | **Open** | the reviewer's ORDERING THT remark and first-article check (J124 and J1 seat flat) are for the owner |
| R9P1-DFM-01 mirrored-numbering pin-1 mismatch, no order remark | Minor / confirmed | **Fixed** (records) | ORDERING §4 remark and query (with PYRO-03) |
| R9P1-DFM-02 actuator gate pads 0.15 mm from the GND pour; "retired" | Minor / confirmed | **Listed** (C19) | REQUIREMENTS "Accepted risks" retired for the pyro gate nets only; the owner option (a 0.3 mm DRU zone rule) recorded |
| R9P1-DFM-03 J122's GND pins solid, unlisted | Minor / confirmed | **Listed** (C21) | as POWER-04 |
| R9P1-DFM-04 own-net via rings under JLC's 0.10 mm mask web | Minor / confirmed | **Listed** (C13) | C13: 23 pairs at 20 vias under a 0.10 mm web, worst 0.005 mm, all own-net, every hole ≥ 0.107 mm from the opening; the optional via moves not taken |
| R9P1-DFM-05 M1's U4 clause | Minor / confirmed | **Fixed** (records) | M1 |
| R9P1-DFM-06 half of J1's pin legends on the bottom | Minor / not in the brief | **Open** | at the next forward-edge ground change |
| R9P1-DFM-07 two outlines within 0.15 mm of another part's opening | Minor / not in the brief | **Open** | JLC trims the ink (cosmetic) |
| R9P1-DFM-08 J2's NPTH 0.39 / 0.41 mm from GND vias | Minor / not in the brief | **Open** | at the next ground-table change (R7 was accepted with 0.39 mm) |
| R9P1-INTEGRITY-01 check_r9's report not reproducible | Minor / confirmed | **Fixed** (tools, D-F1-03) | R-5 and pyro_probe deterministic; D-S10-18 corrected |
| R9P1-INTEGRITY-02 R-8 sampled In1 only inside U31's pad ring | Minor / confirmed | **Fixed** (tool, D-F1-03) | In1 over the 10 × 10 mm body (seeded notch test); this board passes |
| R9P1-INTEGRITY-03 the test-pad rule's "never lowers a pyro rule" comment | Minor / not in the brief | **Open** | the DRU text is pinned by check_actuators' DRU_SHA; no rule is affected today (no zone on BUS / IGN / OUT, P-9) |
| R9P1-INTEGRITY-04 rule_h_seed cannot fail on a check_actuators regression | Minor / not in the brief | **Open** | the bound evidence shows check_actuators catching all six edits on all three pairs |
| R9P1-INTEGRITY-05 stale docstring and via count | Minor / not in the brief | **Fixed** | check_r9's M-7 docstring; M3_R9's GND via count |
| R9P1-INTEGRITY-06 quality_audit's tests depend on KICAD_PY | Minor (pre-existing) / not in the brief | **Open** (recorded since D-S10-18) | run with KICAD_PY unset |

**Scorecard against step 9's** (the same survey, `tools/run_r9_survey.sh` with the 0.05 mm DC; step 9's
`step9_evidence/r9_scorecard.md` on fc3d5b34 against the fix pass's `step10_evidence/r9_scorecard.md`):
| Row | Step 9 on `fc3d5b34…` | Fix pass on `4f841a0e…` | R8 |
|---|---:|---:|---:|
| Done rows met / missed | 34 / 16 as reported (33 / 17 with Z4 counted over every test pad) | 34 / 16 | — |
| Z4 vias in test pads | 0 as reported (2: TP120) | 0 | 1 |
| index_r9 / index_r8 | 84.8 / 95.4 | 83.8 / 95.2 | 100 |
| D_raw mΩ / neck mm / rise °C (0.05 mm) | 0.79 / 7.81 / 12.8 | 0.80 / 7.89 / 12.6 | 1.45 / 5.94 / 17.5 |
| X5 track widths | 6 | 5 | 11 |
| Y1 close pairs under 0.2 mm | 31 | 30 | 27 |
| P9 GND distance p95 mm | 3.45 | 3.37 | 4.47 |
| P8 GND stitching per cm² | 9.38 | 9.49 | 8.15 |
| P6 In2 perimeter mm | 1478.1 | 1479.4 | 1752.2 |
| S6 / S7 / S17 | 1.151 / 206.6 / 1365.5 | 1.152 / 207.5 / 1367.5 | 1.174 / 285.8 / 1638.9 |
| X7 vias (GND / other) | 579 (425 / 154) | 583 (430 / 153) | 609 (428 / 181) |
| F3 bottom support clearance mm | 4.600 | 4.483 (C98.1) | 4.452 |

Every other row is unchanged (`step10_evidence/r9_scorecard.md` against `step9_evidence/r9_scorecard.md`): no row
crossed its target. Measured outside the scorecard on the same boards (`sources/r9_review/fix1/fix1_measure.py`): the
worst outer GND copper 9.50 mm of copper from a via (28.41), C121.2 1.50 mm (16.10), U31's ground pins 0.20 / 0.35 /
0.35 mm (1.154 / 1.095 / 1.05), U1.3 to the nearest passing net 0.55 mm (0.250), vias in test pads 0 (2).

## Open

1. **Review Minors:** r9_plan §5 is met (pass 1 on `fc3d5b34…` and pass 2 on `4f841a0e…`, no confirmed Critical or
   Major). Open, recorded and not reworked: the pass-1 Minors not in the fix brief ("Review pass 1": PLANES-05,
   MECHANICAL-05, DFM-06 … 08, INTEGRITY-03 / -04 / -06) and pass 2's ("Review pass 2"), for a later polish pass.
2. **Owner:** accepted on 2026-10-25: this deviation list (M2), with C1's length kept at 102 mm and the crystal plane (C14), the
   actuator gate pads at the zone clearance (C19, no DRU zone rule), the solid J122 pins (C21) and the east mid support
   with the sensors on mode 1's antinode (part D) accepted as drawn.
3. **Before ordering R9:** U4 in JLC stock or consigned (40 in stock on 2026-10-26 00:59Z); JLC's acceptance of four
   tabs on a 102 mm board (Inference, ORDERING §3); `FAB_NET=1 m3_design/r9_fab.sh` within 24 h.
4. **Firmware:** an R9 binding from `step10_evidence/r9_binding_note.json` (the IMU map changes; the pins do not).
5. **Bench:** every ORDERING §5 item; R9-specific: the IMU sign check (roll = −gyro_Y), the keyed-radio pyro-immunity
   test at the 46 mm radio-to-pyro distance (owner decision 3), the HSE frequency with the crystal plane, the stall test
   with the FETs and J122 as the judged items (D12's limits are a CAD check only on R9), the tap check against 256.6 Hz
   with the accelerometer at U4 and U4 logged.
6. **Parent VEHICLE.md:** the stack row's board length, hole list, standoff height, the battery leads' U-turn and the
   harness sides (`sources/r9_review/fix1_handoff.md` §5), applied in the parent repository with R9's acceptance (2026-10-25).

## Review pass 2 (board `4f841a0e…`, 2026-10-25)

Nine independent reviewers (pyro and arming safety, requirements traceability, RF, power/thermal/hot-plug, planes and
return paths, routing simplicity, mechanical, manufacturability, gate and build integrity), with the three-skeptic check
for any Critical or Major finding. Reports: `m3_design/assembly_review/sources/r9_review/pass2_*.md`. Result: **0 Critical,
0 Major, 32 Minor** (23 marked worth fixing, mostly record and procedure items).
Every pass-1 finding is closed or properly dispositioned. With pass 1 (0 confirmed Critical or Major on `fc3d5b34…`),
this is the second consecutive clean pass, so r9_plan §5's stopping rule is met; the Minors below are recorded, not
reworked, and stay open for a later polish pass, except the stale ORDERING sentence the acceptance update rewrote
(R9P2-REQUIREMENTS-01, R9P2-DFM-03 (a)). The gate (`tools/check.sh`) exits 0 on `4f841a0e…` (coordinator re-run
2026-10-25).

| ID | Sev. | Worth fixing | Finding (first line) | Disposition |
|---|---|---|---|---|
| R9P2-PLANES-01 | Minor | yes | C22 and r9_ground_check COPPER_EXCEPT record the board's worst unstitched GND copper as having no via spot because 'In2's 3V3 finger takes no antipad (D-S8-02)'. This is the F.Cu east strip x 36.15-38.05, y 65.4-74.2 (9.50 mm of copper from a via at (37.45, 73.75)), and the same area also holds the … | Recorded, not reworked (review loop stopped after two consecutive clean passes); open Minor |
| R9P2-PLANES-02 | Minor | no | The reference gate (r9_ground_check reference, tools/reference_audit.py, R6b) still samples only critical_reference's R6 and extended net sets. PYRO*/ARM* nets and the non-SPI RADIO_* / GNSS_* nets are never sampled, so a later split crossing on one of them would pass the gate. | Recorded, not reworked (review loop stopped after two consecutive clean passes); open Minor |
| R9P2-PLANES-03 | Minor | no | The fix pass regenerated r9_ground.tsv with C98 in its new place, and the regeneration changed more than the three copper vias the records name. D-S8-02 and D-S8-16 still describe the step-8 table, including the reach via (38.75, 79.55), which no longer exists. The totals are unchanged (183 vias, 18… | Recorded, not reworked (review loop stopped after two consecutive clean passes); open Minor |
| R9P2-RF-01 | Minor | no | No gate holds R7 pass 3's module-ground qualification, so the U31 ground vias the fix pass restored (D-F1-02) can be lost again without notice. They, and the U30.1/10/12 grid vias, exist only as table rows in r9_rf.GND_MODULE / GRID. No checker refers to them. R-7's strip reach (≤ 4.0 mm) is the onl… | Recorded, not reworked (review loop stopped after two consecutive clean passes); open Minor |
| R9P2-MECHANICAL-01 | Minor | yes | The DB128L stacking nubs are on the forward end of J121 and J124, so J124's free-end nubs face J1's back face 0.25 mm away (nominal). | Recorded, not reworked (review loop stopped after two consecutive clean passes); open Minor |
| R9P2-MECHANICAL-02 | Minor | yes | Tightening J1's screws bends the board at the battery-input MLCCs C80 and C96, and no record tells the integrator to back the board. | Recorded, not reworked (review loop stopped after two consecutive clean passes); open Minor |
| R9P2-MECHANICAL-03 | Minor | yes | ORDERING's staking paragraph says "on all sides" and "the three screw terminals, J122 and J123", but names none of R9's close neighbours of those bodies. A base fillet of about 1–2 mm (Inference) would: | Recorded, not reworked (review loop stopped after two consecutive clean passes); open Minor |
| R9P2-MECHANICAL-04 | Minor | yes | Two records still give the bottom support clearance from before the fix pass. Fix decision D-F1-05 moved C98 to (39.275, 64.2), bottom, rotation 180. | Recorded, not reworked (review loop stopped after two consecutive clean passes); open Minor |
| R9P2-MECHANICAL-05 | Minor | yes | The proposed VEHICLE stack row names lateral sides in the board's KiCad view and leaves out J1's switch pair. | Recorded, not reworked (review loop stopped after two consecutive clean passes); open Minor |
| R9P2-PYRO-01 | Minor | yes | R9 puts J121 and J124 end to end on the west edge. They are the same black, end-stackable DB128L body, so the four wire positions read as one 4-way block: OUT, IGN, BUS1, RAW from aft to forward. The top face legends only the outer two positions; the middle IGN and BUS1 legends are on the bottom onl… | Recorded, not reworked (review loop stopped after two consecutive clean passes); open Minor |
| R9P2-PYRO-02 | Minor | yes | Three pyro statements are not true as written: | Recorded, not reworked (review loop stopped after two consecutive clean passes); open Minor |
| R9P2-ROUTING-01 | Minor | yes | The fix pass redrew USB_LIMITED's end after moving C98, but the trunk still steps down x 36.225. That column served C98.1's old spot; the trunk now leaves it with a 45-degree jog onto R87.1's column x 37.0. That is two needless bends on a power-class net. One diagonal does the same job at equal leng… | Recorded, not reworked (review loop stopped after two consecutive clean passes); open Minor |
| R9P2-ROUTING-02 | Minor | yes | R9_VALIDATION C5 lists the close pairs (Y1 30 / Y1b 14 / Y2c 11) only as 'every pair DRC-legal', with no reason they cannot be removed. Most are forced by geometry. One class is not: GND vias that join copper only through the pour (no track arms), placed at the DRC minimum. They come from the RF-str… | Recorded, not reworked (review loop stopped after two consecutive clean passes); open Minor |
| R9P2-ROUTING-03 | Minor | no | When D-F1-04 moved the via out of TP120, the RAW_ACT via row on y 78.2 over Q121's drain lost its regular pitch. (31.5, 78.2) and (32.2, 78.2) sit 0.7 mm apart with rings 0.1 mm apart and read as a doubled via. An even 1.0 mm row is DRC-clean and makes no difference to the DC solve. Cosmetic. | Recorded, not reworked (review loop stopped after two consecutive clean passes); open Minor |
| R9P2-ROUTING-04 | Minor | no | ACT_GATE's F.Cu hop ends in a 0.8 mm vertical plus a 1.13 mm diagonal into the via at (37.35, 89.0). That makes C7's 0.8 mm fold there. A single diagonal is DRC-clean, has one bend fewer and is 0.47 mm shorter. Optional and marginal. | Recorded, not reworked (review loop stopped after two consecutive clean passes); open Minor |
| R9P2-POWER-01 | Minor | yes | U2's regulation loop closes through two single vias that R8's loop did not have. U2 is the AP63203, a fixed 3.3 V part. The two vias are the FB sense via (37.3, 71.3) into the In2 3V3 finger and the single output feed via (37.6, 78.9). R8 (D40, r8_power.py l. 345–355) tapped FB on the B.Cu output tr… | Recorded, not reworked (review loop stopped after two consecutive clean passes); open Minor |
| R9P2-POWER-02 | Minor | yes | C21 / D-F1-06 keep all four J122 GND pins solid. Only J122.3's relief creates the 0.86 mm² single-spoke F.Cu piece; J122.6, .9 and .12 take the zones' THT relief with no new island. C21's current-based reason does not require solid pins either: relief costs about 0.04 mΩ and 0.16 mW per pin at 1.925… | Recorded, not reworked (review loop stopped after two consecutive clean passes); open Minor |
| R9P2-POWER-03 | Minor | yes | Fix pass 1 moved C98 (R9P1-POWER-01), which made C98.1 the bottom part nearest a support at 4.483 mm from (42, 59.5). Two records still name R300.2 at 4.60 mm from (4, 4): | Recorded, not reworked (review loop stopped after two consecutive clean passes); open Minor |
| R9P2-POWER-04 | Minor | yes | C17 lists 'USB_LIMITED's 0.45 A limit from R8 D42 (not re-derived from R85)' as an open inference. TI's own equation closes it: R85 = 66.5 kΩ gives U10's current-limit threshold as 354.8 / 396.7 / 444.5 mA (min / nom / max), and 351–449 mA with R85's 1 %. So 0.45 A is the maximum, and the supply row… | Recorded, not reworked (review loop stopped after two consecutive clean passes); open Minor |
| R9P2-POWER-05 | Minor | no | C24 says a resistive fault on the 0.4 mm, 44 mm camera branch 'drawing 1.5–3.96 A is limited by neither U7 nor U9 … about 15–103 °C'. But 3.96 A is U9's minimum threshold: | Recorded, not reworked (review loop stopped after two consecutive clean passes); open Minor |
| R9P2-REQUIREMENTS-01 | Minor | yes | ORDERING's opening paragraph (l.3) still says 'R9 is not yet orderable: no independent review pass has run on it'. Review pass 1 ran on fc3d5b34 and its fix pass made the current board 4f841a0e. Every other record says one pass has run and pass 2 is next. The conclusion (order R8) still stands, but … | Closed by the acceptance record update (2026-10-25: ORDERING l.3 rewritten) |
| R9P2-REQUIREMENTS-02 | Minor | yes | The fix pass moved C98 beside U11 (D-F1-05). That made C98.1 the nearest bottom item to a support: 4.483 mm from (42, 59.5). Before the move it was R300.2 at 4.600 mm from (4, 4). R9_VALIDATION, the scorecard and the gate all give the new value. Two records still give step 10's figure, part and hole… | Recorded, not reworked (review loop stopped after two consecutive clean passes); open Minor |
| R9P2-REQUIREMENTS-03 | Minor | yes | The like-for-like rewrite stopped at each C row's first metric. Four gaps remain. (a) Part E gives no R8 figure: R8 had 91 information instances, R9 has 114 (+25 %). REQ-05 named this row. (b) C15's R8 column gives routes 28 against R9's 38, but the row is not flagged 'worse' and is missing from the… | Recorded, not reworked (review loop stopped after two consecutive clean passes); open Minor |
| R9P2-REQUIREMENTS-04 | Minor | yes | C21 (with M2's R9 pointer) keeps all four J122 GND pins solid, but its measured cause comes from J122.3 alone. I reproduced C21's trial exactly: relieving all four pins leaves a 0.859 mm² F.Cu GND piece with no via. With J122.6, J122.9 and J122.12 relieved and J122.3 kept solid: | Recorded, not reworked (review loop stopped after two consecutive clean passes); open Minor |
| R9P2-REQUIREMENTS-05 | Minor | yes | M3_R9 l.358 and R9_VALIDATION l.160 state 'lever arm x −11.0 mm, z −2.06 mm' and cite step10_evidence/r9_binding_note.json. The note itself has lever_arm_mm {x: −11.0, z: null}. binding_note_r9.py fills z only when --fit is given. Step 10's command, which the fix pass re-ran (D-F1-11), omits --fit. … | Recorded, not reworked (review loop stopped after two consecutive clean passes); open Minor |
| R9P2-REQUIREMENTS-06 | Minor | no | Four small record inaccuracies: | Recorded, not reworked (review loop stopped after two consecutive clean passes); open Minor |
| R9P2-DFM-01 | Minor | yes | The R9P1-DFM-01 fix added an order remark (ORDERING l. 103) and an expected DFM query (l. 115) about JLC's pin-1 mark, but they name only J121, J124 and J122. J1 has the same mismatch: jlc_orient's +180° body correction for C2915641 puts JLC's pin 1 on our pin 4. Our square pad and the 1:BAT+ legend… | Recorded, not reworked (review loop stopped after two consecutive clean passes); open Minor |
| R9P2-DFM-02 | Minor | yes | C21 gives the owner two options: relieve all four J122 GND pins or keep all four solid. The fix pass tried relieving all four and found that J122.3's relief ring closes the F.Cu channel next to D120's 3V3 lane. That leaves a 0.86 mm² GND piece joined by a single spoke, so it kept all four solid. Onl… | Recorded, not reworked (review loop stopped after two consecutive clean passes); open Minor |
| R9P2-DFM-03 | Minor | yes | Three record statements are out of date after the fix pass. (a) ORDERING l. 3 says 'R9 is not yet orderable: no independent review pass has run on it'. Pass 1 has run (0 Critical, 1 Major confirmed as Minor) and pass 2 is due, as STATUS says. (b) ORDERING's §7 Sled row (l. 211) still gives step 10's… | (a) closed by the acceptance record update (2026-10-25: ORDERING l.3 rewritten); (b) and (c) recorded, not reworked; open Minor |
| R9P2-INTEGRITY-01 | Minor | yes | The step-8 stitch gate's outer-pour clause, r9_ground.foreign_fill, asks whether a table via's centre lies inside a non-GND F.Cu or B.Cu fill. It runs only after the native refill, and a refill always clears a GND via out of a foreign fill, so the clause can never fire. R8's equivalent tested the zo… | Recorded, not reworked (review loop stopped after two consecutive clean passes); open Minor |
| R9P2-INTEGRITY-02 | Minor | no | The fix pass added an exemption to the step-8 stitch gate. Any table via whose centre lies inside the box r9_ground_aid.CORRIDOR_EXCEPT['C121.2'] may now cut the In2 RAW_ACT region inside its 7.7 A corridor. The exemption is recorded and reasoned (D-F1-07 and part D), but four summaries say that no … | Recorded, not reworked (review loop stopped after two consecutive clean passes); open Minor |
| R9P2-INTEGRITY-03 | Minor | no | Five fix-pass record statements do not match what happened: | Recorded, not reworked (review loop stopped after two consecutive clean passes); open Minor |
