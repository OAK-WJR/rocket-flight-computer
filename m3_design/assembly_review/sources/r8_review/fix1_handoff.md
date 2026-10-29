# R8 fix pass 1: handoff

Fix pass 1 implements R8 review pass 1 (`pass1_*.md`, board `429b6db4…`: 0 Critical, 1 Major, 38 Minor) through the
R8 generators, tables and tools only; `m3_design/r8_build.sh` reproduces the result. Nothing is committed (AGENTS: the
owner asks for commits). Log: `fix1_progress.md`. Decisions: `sources/r8_design/R8_DECISIONS.md` D85–D96. Dispositions of
every finding: `docs/R8_VALIDATION.md` "Review pass 1".

- **Final board:** `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
  `6600ef9462b37ec58540e0dd7edd97577c3e778bda0d233d3c1dffc555ad5a8d`; netlist `0cc1ed69…` (unchanged). Two consecutive
  `r8_build.sh` runs gave identical boards, netlists and all 15 sheets (17 files compared).
- **Gate:** `tools/check.sh` exit 0 (in both builds and standalone): DRC 0 at every severity, unconnected 0, parity 0,
  ERC 0; audit OK; silk OK; `check_r8` OK (with the three new gates); route_check r8 0 failing, 3 allowlisted (A8, A2,
  A3), 0 leftovers; `check_actuators` OK; `fit_check` OK. The build's new DC gate (0.1 mm) passes.
- **Tests:** 272 in 17 suites (KiCad Python), quality_audit 21 under both Pythons; `route_check --profile r7` still
  reproduces R7's verdict on `c872a3d3…` with R7's project files beside it (0 failing, 45 allowlisted, 29 leftovers).
- **Fab:** `m3_design/r8_fab.sh` exit 0: CHECK none; BOM `be711876…` byte-identical to R7's; CPL `c0ee08ae…` (only C83's
  row changed); CPL verify 85 top + 126 bottom, worst 0.491 mm; paste check OK; manifest bound to `6600ef94…`; renders
  regenerated. `cost_check.json` / `stock_check.json` were not re-run (no network run in this pass): they still bind the
  step-9 CPL; refresh with `FAB_NET=1 m3_design/r8_fab.sh` (due within 24 h of ordering anyway).

## What changed, per item

| Item | Change (generator / table / tool) | Result on `6600ef94…` |
|---|---|---|
| R8P1-REQUIREMENTS-01 (Major) | `step9/m2_sweep.py` (new, D96); R8_VALIDATION part C rows C11–C18 with tables, part F coverage, owner summary recounted; REQUIREMENTS M2 / STATUS counts; copper where cheap (D91): BUZZ_DRV lane y 60.45 (`r8_route_status.py`), I2C1_SCL exit x 14.243 (`r8_route_imu.py`), CAM_MCU_RX hop via (33.95, 44.0) (`r8_route_camera.py`), VLOGIC sense via 0.5 mm; chain-detour redraws: VLOGIC sense run, ACT_GATE stub (`r8_power.py`), USB_DM out of D4 (`r8_route_usb_swd.py`); CAM_5V's U13.1 chamfer built and reverted (pad-entry instances) | 23 chain detours (pass 1: 27), 32 close net pairs (14 at 0.150 mm), 12 nets with vias over need (none over need + 2), 26 via folds, every M2 category with a "swept" line |
| PYRO-01 | `r8_power.py` R8_ACT_FET_S_B corner (11.4, 97.6) → (12.4, 97.6); `check_r8.battery_pyro` + test | J124.1 1.089 mm (was 0.501); ACT_FET_S neck 4.97 mm, 21.4 °C at 0.05 mm |
| PYRO-02 | `r8_power.py` R8_RAW_ACT_F corner (21.3, 88.0) → (21.3, 87.3), (20.6, 88.0); (b) not applied (benign, 0.22 mm of neck) | R127.1 1.115 mm (was 0.696); RAW_ACT neck 5.94 mm, 17.5 °C at 0.05 mm (unchanged) |
| PYRO-03, REQUIREMENTS-04 | records: M3_R8 sentence corrected; R8_VALIDATION pyro observations table; ORDERING §5 switch cycles and the H-6(b) step require the board off with the link in | — |
| PYRO-04 | recorded; ORDERING static gate repeated warm where convenient | — |
| REQUIREMENTS-02 | D6.8, `step9/binding_note.py` constraint (note regenerated), F10 text, ORDERING bootloader reset check | — |
| REQUIREMENTS-03 | `r8_post.py` own-cell legend placement (0.25 mm margin; J123 0.9 mm), J1 2/3/4 in the forward strip; `check_r8.terminal_legends` + test; step gates defer it to r8_post | 10 of 10 legends nearest their own pin |
| REQUIREMENTS-05…09 | ORDERING (PE9, "west of U1", J2 hole / pads), M3_R8 / D76 (3.9–10.6 mm), AGENTS (two passes), STATUS (R7 pass 8), README (R8 / R7), REQUIREMENTS P2 note and M2 poured nets | — |
| RF-01, PLANES-01 | `step7/make_ground.py` TRIMS + R8_POUR_TRIM_G7; `r8_ground.tsv` regenerated (two-pass `--built` identical) | the 15.1 mm radio-bus finger is gone; fingers 6 / 14 (gate method), 11 / 17 (R7's, F / B) |
| RF-02 | records: "R7 pass-4 RF items on R8", C15, C16 (module-ground gate extension not added: strip digests already hold it) | — |
| RF-03, RF-04 | ORDERING §5 RF reset step (PE9 / R311 / R312) and coexistence step (camera on, MCU at flight load) | — |
| POWER-01, PLANES-04, REQUIREMENTS-10 | `dc_solve.py` `--window`, `--via-currents`, SHA first line, docstring; `run_dc.sh` via currents and DC_GND row | GND return 0.72 mΩ (5.6 mV and 0.043 W at 7.7 A); via maxima 0.86 A / 0.67 A |
| POWER-02 | ORDERING §5 "7.7 A stall test" | — |
| POWER-03 | `r8_place.tsv` C83 (9.55, 36.0, 90, B); `r8_route_usb_swd.py` VBUS through C83.1, U10.2 GND through C83.2; D42 corrected | C83 beside U10.1 / U10.2; VBUS's V_B lost its return GND via (C8: 2.06 mm) |
| POWER-04 / -05 / -06 | recorded (M3_R8 Power); dc_solve docstring corrected | — |
| ROUTING-01 | `r8_route_qspi_hse.py` HSE_OUT via (24.69, 47.5), GND (24.69, 46.25) | HSE_OUT 7.38 mm (was 9.27); keep-out samples 1,710 → 1,368 |
| ROUTING-02 | `r8_power.py` U9.5 to centre, C75.2 stub on its centre row; `r8_route_links.py` BAT_DVDT from U9.7's inner rectangle; C75.1 recorded (C18); m2_sweep `pad_edge` | no track end within 0.03 mm of any pad edge |
| ROUTING-03 | VLOGIC sense via 0.5 mm (`r8_power.py`) | 0.20 mm from SERVO1_MCU |
| ROUTING-04 | records (C14); m2_sweep `via_fold` | — |
| PLANES-02 / -03 | records (M3_R8 Return paths, Power) | — |
| DFM-01 | `r8_route_rf.py` limiter vias y 8.3; V_VLOGIC (35.65, 66.6); `check_r8.via_paste` + test; route_check A2 / A3 figures (7.65 / 6.20 mm) and rf budget ratio 2.40 re-measured (D87) | no via ring on a paste aperture (nearest 0.025 mm, C90.1) |
| DFM-02 | `r8_place_check.TAB_PLAN` left (112.5, 117.5); ORDERING §3 table, remark | Q121 8.08 mm, C120 12.64, J1 11.90 mm |
| DFM-03 | `r8_pcb.py` THERMAL_PADS (J3.1, J3.4); J123.2 kept solid (DRC starved_thermal); ORDERING §4 | C17 |
| DFM-04 | ORDERING (J2, C84 / J121 margins, U4), D35 / D39 marked step-4 | — |
| INTEGRITY-01 | R8_VALIDATION step table, hard gates; AGENTS / F10 / M3_R8 strip wording; D5 / D10 (and D12, D68, D87, D89) in the owner summary | — |
| INTEGRITY-02 | `r8_build.sh` runs `tools/run_dc.sh … 0.1` after `r8_ground_check.py`; dc_solve prints the board SHA | gate passed in both builds |
| INTEGRITY-03 | **not done** (owner action: commit or tag) | — |

## Scorecard (`tools/run_survey.sh`, DC at 0.05 mm, against step 8 / 9)

Index **15.3** (R7 = 100; step 8 16.0 at the same 0.05 mm DC grid). Rows that moved (step 8 / 9 → fix pass 1):
S1 signal track 1500.1 → 1498.8 mm; S6 / S7 1.18 / 295.5 → 1.176 / 288.8 mm; S9 nets over 2× 2 → 4 (the limiter's
GNSS_LNA_EN 2.06 / GNSS_VCC_RF 2.37, whose vias moved clear of U30's paste, D87); S10b bends 234 → 231; S17 MST 1642.9 →
1638.7 mm; S18 segments 797 → 794; P1 In1 coverage 0.9065 → 0.9054; P3b In1 slots 1 → 3 (J3's legs' new thermal-relief
rings, D89; target ≤ 4 met); P6 In2 perimeter 1788.7 → 1782.9 mm; R1 / R3 4.7 → 2.9 mm; R6b 0.1157 → 0.1107; the 7.7 A
necks unchanged (17.5 / 14.5 / 21.4 °C). Unchanged: S4 55, S8 4, S12 25, C1 / C3 3, C2 93, C6 1, P7 1, P9 / P10
4.48 / 9.65 mm. Targets: 20 met, 11 missed (step 9's quick run: 17 met, 11 missed, the three DC rows not measured); each miss has its row in R8_VALIDATION part C.

## Not done, and why

- **R8P1-INTEGRITY-03 (commit / tag):** owner action; the brief said not to commit.
- **PYRO-02 (b)** (C127.1 to 1.0 mm): a RAW_ACT–CONT bridge does not fire, and the step moves the RAW_ACT neck to 5.72 mm.
- **Signal gaps not opened:** SPI1_SCK between the IMU vias (U4's 0.5 mm pitch, no via under the body), CAM_FAULT_N /
  CAM_PWR_EN (adjacent pins' staggered vias), CAM_PWR_EN / USB_LIMITED (TP73's zone), and the other 0.150 mm pairs of C12:
  none opens with one table edit.
- **Optional gates not added:** route_check categories for pad-edge ends and via folds (the M2 sweep measures both; an
  information category would change C2 for no gate), the F.Cu module-ground extension (the strip digests hold it), the
  reference audit's `--agents3` set (pass 1's full-set sampling recorded instead).
- **Not re-run:** the plate model and the hot-plug script (numpy, not in KiCad's Python; fix pass 1 moved only C83 and
  U9.5's entry, neither in their inputs); the live cost / stock run (network).
- **Inherited open items:** review pass 2 (and 3), the owner's acceptance of the deviation list and of the decisions it
  names, C10's vibration ruling, U4 consignment, JLC's tab acceptance, the firmware binding, every bench item.

## Reproduce

```
m3_design/r8_build.sh                       # twice; compare the board SHA-256 (6600ef94…)
KICAD_PY=<KiCad python3> tools/check.sh
PY=<KiCad python3>; D=m3_design/assembly_review/sources/r8_design/step9
$PY -I $D/m2_sweep.py m3_design/assembly_review/m3.kicad_pcb --json /tmp/m2.json     # part C / F inputs (~20 s)
$PY -I m3_design/assembly_review/sources/r8_design/step7/make_ground.py m3_design/assembly_review/m3.kicad_pcb /tmp/g.tsv --built  # = r8_ground.tsv
tools/run_dc.sh m3_design/assembly_review/m3.kicad_pcb /tmp/dc 0.05             # ~40 min
DC_GND=0.1 tools/run_dc.sh m3_design/assembly_review/m3.kicad_pcb /tmp/dcg 0.1  # GND return, ~30 min
NO_GATE=1 tools/run_survey.sh m3_design/assembly_review/m3.kicad_pcb /tmp/survey
(cd tools && for t in test_*.py; do $PY -m unittest ${t%.py}; done)
m3_design/r8_fab.sh
```
