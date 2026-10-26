# R9 survey: the R8 baseline a clean-sheet R9 must beat

Board measured: M3-ASSY-R8, `m3_design/assembly_review/m3.kicad_pcb` of worktree `rocket-flight-computer-r9`
(branch `m3-assy-r9`, commit `9c8179b` = the owner-accepted, pushed R8), SHA-256
`cc044ea0922ff826df19af9d9726d92c096ab2b127025b55d123d8772e5fb4a7`, 46 × 118 mm, 4 layers. Every run used a
byte-identical copy of the KiCad project (same SHA-256; after the runs `baseline/r8_board/` keeps only the board,
`.kicad_pro` and `.kicad_dru`, enough for every row but the gate, which needs the schematic and `kilib`: rerun the gate on
the repo's own folder); the repository was only read
(`git status --ignored` clean afterwards: the bytecode caches the repo's `python -I` runs leave were removed).

**Reproduced exactly** (fresh runs, not copied from the record): every scorecard row of `docs/R8_VALIDATION.md`
"Scorecard" (index 15.3 against R7, 20 met / 11 missed of r8_plan's 31 targets); `tools/check.sh` exit 0 (DRC 0,
unconnected 0, parity 0, ERC 0, audit, silkscreen, `check_r8` OK, `route_check` r8 "0 failing, 3 allowlisted",
`check_actuators`, `fit_check` OK); the 0.05 mm DC solves (RAW_ACT 1.45 mΩ, neck 5.94 mm F.Cu, 17.5 °C; BAT_IN 0.45 mΩ,
6.99 mm B.Cu, 14.5 °C; ACT_FET_S 0.18 mΩ, 4.97 mm B.Cu, 21.4 °C; largest via 0.86 A RAW_ACT, 0.65 A BAT_IN);
`reference_audit` 5,186 / 46,845 = 11.07 % (R6 set), 5,944 / 102,408 = 5.80 % (extended); `pyro_neighbours`,
`requalify`, `check_r8`'s evidence and the M2 sweep equal to `step9/evidence/fix4_*` (all but the board-hash field the evidence files add). The 0.1 mm quick DC grid gives 1.45 / 0.44 / 0.19 mΩ,
necks 5.90 / 6.85 / 4.80 mm, 17.6 / 14.8 / 22.3 °C (2 min 45 s).

## 1. How to rerun on any board

Folder: `<scratch>/r9_design/baseline/`
(below `$B`). The board must carry saved zone fills and the R7/R8 designators (Q120, Q121, J1, J122, CH1 parts, RF parts).

```bash
B=<scratch>/r9_design/baseline
# full: repo survey + gate + 0.05 mm DC (~19 min; the RAW_ACT solve dominates) + R9 rows, scored against R8
GATE_SH=/path/to/r9/tools/check.sh $B/tools/run_r9_survey.sh CANDIDATE.kicad_pcb OUTDIR
# iteration: quick DC grid, compared with R8's quick-grid baseline (~5 min with the gate)
DC_GRID=0.1 R8_BASE=$B/out/r8_quick $B/tools/run_r9_survey.sh CANDIDATE.kicad_pcb OUTDIR
# geometry only (~70 s)
NO_DC=1 NO_GATE=1 $B/tools/run_r9_survey.sh CANDIDATE.kicad_pcb OUTDIR
# re-score an existing OUTDIR
python3 -I -B $B/tools/r9_scorecard.py OUTDIR --baseline $B/out/r8 --md OUTDIR/r9_scorecard.md --json OUTDIR/r9_scorecard.json
```

| Script (`$B/tools/`) | What it runs |
|---|---|
| `run_r9_survey.sh BOARD OUTDIR` | repo `tools/run_survey.sh` (survey_metrics, route_check `--routes`, critical_reference ×2, `run_dc.sh` = `dc_solve.py --necks` ×3, gate), then `r9_extra_metrics.py`, `reference_audit.py` (both sets), `step9/requalify.py`, `step9/pyro_neighbours.py`, `step9/m2_sweep.py`, `fit_check.py`, `r9_scorecard.py`. Env: `REPO` (tools source, default the R9 worktree), `GATE_SH` (gate script, default repo `tools/check.sh`), `ROUTE_PROFILE`, `R8_BASE`, `NO_DC`, `NO_GATE`, `DC_GRID`, `NO_M2` |
| `r9_extra_metrics.py BOARD [--tools DIR] [--json]` | the X rows (section 3), reusing `check_r8` / `route_check` / `survey_metrics` definitions |
| `r9_scorecard.py OUTDIR [--baseline DIR\|JSON]` | repo `scorecard.build()` rows + X / Y / Z / F rows, `index_r8`, `index_r9`, and the R9 targets (hard / done / stretch); DC "done" rows switch to R8's quick values when the survey's grid is 0.1 mm |
| `gcpw_summary.py BOARD` | `check_r8.gcpw_profile` summarised: per RF track, F.Cu GND gap range each side |

Baselines: `$B/out/r8/` (complete: 0.05 mm DC and gate; `r9_scorecard.md/.json`, the repo `scorecard.md` against R7)
and `$B/out/r8_quick/` (same with 0.1 mm DC). On a re-placed board the repo's `check.sh` (R8 contracts) fails by
design (12 rigid digests, fixed coordinates, section 5) and route_check profile r8 reports its 3 allowlist entries as
stale: count instances (C1, C2), and gate with R9's own `check.sh` via `GATE_SH`.

## 2. The R9 scorecard

Kinds: **hard** = must hold (gate or requirement); **done** = R9 definition of done (a miss needs a measured cause that
cannot be removed without a priority-1 cost, as in r8_plan §4); **stretch** = clean-sheet ambition, reported. "Done"
takes every r8_plan target and, where R8 already beats it, R8's own value (no regression). R8's 11 misses are marked
**M**. The ratio index rows: `index_r8` = the repo's 12-row index (S1, S4, S7, S10b, S12, S15, C1, C2, R3, P7, P9,
D_min), R8 = 100; `index_r9` adds X1, X2, X2g, X5, X6c, P6, Y1. R8 itself scores hard 22/23 (S15), done 44/74.

### Gate, clean-routing exceptions, deviation list

| Row | R8 | r8_plan | R9 hard | R9 done | R9 stretch |
|---|---:|---|---|---|---|
| G gate exit (R9 `check.sh`: DRC incl. pyro A–H, unconnected, parity, ERC, audit, silk, check_r9, route_check r9, check_actuators, fit) | 0 | 0 | 0 | | |
| Two consecutive identical builds; DC D12 limits held in the build | yes | yes | yes | | |
| C1 gated-category instances | 3 (A2, A3, A8) **M** | ≤ 1 | | ≤ 1 | 0 |
| C3 allowlist entries | 3 **M** | ≤ 1 | | ≤ 1 (A8 only) | 0 |
| C2 information-only instances (pad_end_offcentre 41, width_change_junction 15, passes_through_pad 8, segment_inside_pad 7, u_turn 7, power_via_no_gnd 7, extra_bends 4, short_layer_hop 2) | 91 **M** | ≤ 80 | | ≤ 80 | ≤ 40 |
| C4 leftovers / C5 failures + stale | 0 / 0 | 0 / 0 | 0 / 0 | | |
| C6 AGENTS §3 rule instances | 1 (A8) | ≤ 1 | ≤ 1 | | 0 |
| Deviation list (R8_VALIDATION A + C) | 3 + 20 rows | — | | ≤ 1 + ≤ 8, each with a measured cause | 0 + ≤ 3 (by-design rows: C10 vibration, C16 RF ESD solid GND, C17 THT solid GND) |
| Rigid hash groups in the checker | 12 | — | **0** (replaced by rule checks, section 5) | | |

### Routing simplicity (S)

| Row | R8 | r8_plan | R9 hard | R9 done | R9 stretch |
|---|---:|---|---|---|---|
| S1 signal track, mm | 1497.9 | ≤ 2300 | | ≤ 1497.9 | ≤ 1300 |
| S4 signal layer-change vias | 55 | ≤ 75 | | ≤ 55 | ≤ 40 |
| S6 / S7 detour ratio / excess mm | 1.174 / 285.8 | ≤ 1.18 / ≤ 350 | | ≤ 1.174 / ≤ 285.8 | ≤ 1.12 / ≤ 180 |
| S8 / S9 nets over 1.6× / 2× MST (RAW_ACT_SENSE_MCU 3.62, GNSS_VCC_RF 2.37, RADIO_TXEN 2.30, GNSS_LNA_EN 2.06) | 4 / 4 **M** | 0 / 0 (keep-out-forced excepted) | | ≤ 1 / ≤ 1, only a keep-out-forced net on the D10 baseline | 0 |
| S10b signal bends | 231 | ≤ 400 | | ≤ 231 | ≤ 180 |
| S12 critical layer changes | 25 | ≤ 32 | | ≤ 25 | ≤ 18 |
| S13 … without a GND via ≤ 1.5 mm | 0 | 0 | 0 | | |
| S14 critical weighted ratio | 1.182 | — | | ≤ 1.182 | |
| S15 / S16 In2 signal / In1 track, mm | 3.4 **M** / 0 | 0 / 0 | **0 / 0** (no rigid exemption) | | |
| S17 placement MST, mm | 1638.9 | ≤ 1850 | | ≤ 1638.9 | ≤ 1450 |

### Planes, stitching, reference (P, R)

| Row | R8 | r8_plan | R9 hard | R9 done | R9 stretch |
|---|---:|---|---|---|---|
| P1 In1 GND coverage | 0.9051 | ≥ 0.90 | | ≥ 0.9051 | |
| P2 In1 GND islands | 1 | 1 | 1 | | |
| P3b In1 slots (via cluster beside U4 x 8.3–11.0 y 55.2–56.9; J3 legs ×2; J123.1/2) | 4 | ≤ 4 | | ≤ 4 | ≤ 2 |
| P4 In2 regions (3V3 1514 mm², GND 2687, RAW_ACT 2 × 346 total, BAT_IN 230) | 5 | ≤ 5 | | ≤ 5 | |
| P6 In2 perimeter, mm (3V3 750 with 117 voids, GND 752, RAW_ACT 140, BAT_IN 111) | 1752.2 **M** | ≤ 900 | | ≤ 900 | |
| P7 outer GND islands with ≤ 1 via (one F.Cu island, 2.9 mm²) | 1 **M** | 0 | | 0 | |
| P9 / P10 distance to nearest GND via, p95 / max, mm (max at (0.25, 88.25); bands y 70.8–94.4 p95 5.94, y 94.4–118 p95 5.69) | 4.47 / 9.65 **M** | ≤ 3.5 / ≤ 7 | | ≤ 3.5 / ≤ 7 | |
| P11 p95 inside outer GND pours, mm | 2.9 | — | | ≤ 2.9 | |
| R1 / R3 unreferenced length, mm | 2.9 / 2.9 | ≤ 5 / ≤ 15 | | ≤ 2.9 / ≤ 2.9 | |
| R4 reference-edge crossings | 28 | — | | ≤ 28 | |
| R6b critical_reference unreferenced share (own via antipads 3,592, Y1_In2_keepout 1,368, other vias 226 samples) | 0.1107 **M** | ≤ 0.08 | | ≤ 0.08 | ≤ 0.05 |

### 7.7 A servo feed (D; `run_dc.sh`, 0.05 mm qualification grid)

| Row | R8 | r8_plan / D12 | R9 hard | R9 done | R9 stretch |
|---|---:|---|---|---|---|
| D_raw: RAW_ACT Q121→J122, mΩ / neck / rise | 1.45 / 5.94 mm F.Cu / 17.5 °C | ≤ 20 °C | ≤ 20 °C | ≤ 17.5 °C, ≤ 1.45 mΩ | |
| D_bat: BAT_IN J1→Q120 | 0.45 / 6.99 mm B.Cu / 14.5 °C | ≤ 20 °C | ≤ 20 °C | ≤ 14.5 °C, ≤ 0.45 mΩ | |
| D_fet: ACT_FET_S Q120→Q121 (pad-limited) | 0.18 / 4.97 mm B.Cu / 21.4 °C (scorecard 21.5) | ≤ 30 °C | ≤ 30 °C | ≤ 21.5 °C, ≤ 0.19 mΩ | ≤ 20 °C (neck ≥ 5.28 mm) |
| Largest via barrel current, A | 0.86 (RAW_ACT), 0.65 (BAT_IN) | — | | ≤ 1.0 (report) | |

Quick-grid (0.1 mm) equivalents for iterations: 17.6 / 14.8 / 22.3 °C, 1.45 / 0.44 / 0.19 mΩ (`r9_scorecard.py`
switches automatically).

### Clean-sheet rows (X) — new in R9

| Row | R8 | R9 hard | R9 done | R9 stretch |
|---|---:|---|---|---|
| X1 board length, mm (outline; width 46) | 118.0 | ≤ 118 (P1 ≤ 120; no regression), width 46 | **≤ 110** | ≤ 104 |
| X1e aft overhang (SMA jacks), mm; envelope 127.8 | 9.79 | | ≤ 9.79 | |
| X2 foreign nets ≤ 3 mm of armed-live copper, same layer (BAT_ENABLE 0.70, ACT_FET_S 1.089, BAT_OVLO 1.92, RAW_PROTECTED 1.98, BAT_DAMP 2.45, ACT_GATE 2.52) | 6 | | ≤ 2 | 0 |
| X2b … plan view, any layer (+ BAT_IN 0.95) | 7 | | ≤ 3 | 0 |
| X2c nearest foreign copper to armed-live copper, same layer, mm (rule F floor 0.5) | 0.70 | ≥ 0.5 (DRC F) | ≥ 1.0 | ≥ 3 (X2 = 0) |
| X2d nearest battery-live (BAT_IN / ACT_FET_S) to bus/igniter/drain, same layer, mm | 1.089 | ≥ 1.0 (D85) | ≥ 2.5 | |
| X2e CH1 block bounding box (union of CH1_PARTS courtyards, x 4.46–41.55, y 81.31–99.17), mm²; courtyard fill 0.498 | 662.4 | | ≤ 662.4 | ≤ 500 |
| X2g foreign nets whose tracks/vias pass through that box (ACT_GATE, BAT_ENABLE, BAT_FAULT_N, BAT_IN, BAT_OVLO, RAW_PROTECTED; 28 items) | 6 | | ≤ 1 | 0 |
| X3 RF strip depth from the aft edge (STRIP_PARTS courtyards + RF-net copper), mm; area 696 mm² (13 %) | 21.39 | | ≤ 21.39 | |
| X3d non-RF parts in that box | 0 | 0 (F10) | | |
| X3f radio/GNSS interface (rfif) track, mm; RF lines 18.4 mm | 321.3 | | ≤ 321.3 | ≤ 250 |
| X3g/h RF zone (every RF_PART, incl. R306/R310/R313/R315 at the MCU end): depth / area | 30.5 mm / 1185 mm² | | report | |
| X4 parts (top / bottom), parts per cm²; courtyard sum / outline | 249 (99 / 150), 4.64; 0.584 | | report | |
| X4f parts off a multiple of 90° (rotations used: 0/90/180/270) | 0 | 0 | | |
| Q1 / Q2 / Q3 top / bottom courtyard utilisation; densest cell | 0.401 / 0.182 / 0.805 | Q3 ≤ 1.0 | report | |
| X5 distinct track widths, all / signal / power / GND | 11 / 7 / 8 / 7 | | ≤ 8 / ≤ 5 / ≤ 5 | ≤ 6 total |
| X5e via geometries (0.5/0.3 × 300, 0.6/0.3 × 309) | 2 | | ≤ 2 | |
| X6 bends per mm of signal track (S10b / S1); all nets 0.1365 | 0.1542 | | ≤ 0.1542 | ≤ 0.12 |
| X6c mean track segment, mm (S2 2087.2 / 794 segments) | 2.629 | | ≥ 2.629 | ≥ 3.5 |
| X7 vias total / GND / non-GND | 609 / 428 / 181 | | non-GND ≤ 181 | |
| X8 rule areas (19); of them pour-trim patches R8_POUR_TRIM_G1–G7, L1 | 19; 8 | | 0 pour trims | |
| X9 F10 separation: nearest RF part to restricted part / to fast-line copper, mm (R306→U1; R306→USB_DM) | 5.94 / 5.075 | ≥ 5.0 / ≥ 5.0 | ≥ 5.94 / ≥ 5.075 | |
| X9c inner RAW_ACT / BAT_IN to pyro live copper, plan view, mm (In2 BAT_IN → R134.1) | 2.65 | ≥ 2.5 (D18) | ≥ 2.65 | |
| X9d battery-live to ARM side, same layer, mm | 1.089 | ≥ 1.0 (D85) | (see X2d) | |

### Robustness (Y, from `step9/m2_sweep.py`) and safety margins (Z, from `step9/requalify.py`)

| Row | R8 | R9 hard | R9 done | R9 stretch |
|---|---:|---|---|---|
| Y1 unique different-net track/via pairs < 0.2 mm (51 layer rows) | 27 | | ≤ 10 | 0 |
| Y1b … at the 0.150 mm DRC minimum (CAM_FAULT_N/CAM_PWR_EN ×2, SPI1_SCK/IMU_CS, SPI1_SCK/MOSI, CAM_5V_SENSE/RAW_ACT_SENSE_MCU, CAM_IO_3V3/UART_OE, CAM_MCU_RX/TX, LED_YEL/USB_FAULT_N) | 8 | | 0 | |
| Y2 pad-to-foreign-copper < 0.2 mm (18 own-part fine-pitch escapes + 15 foreign) / at 0.150 | 33 (15) / 4 | | foreign ≤ 5 / 0 | |
| Y3 chain detours on unpoured nets (RAW_PROTECTED 11.8, BAT_ENABLE 10.9, RADIO_TXEN 9.3, PYRO1_CONT 9.3 mm excess …) | 23 | | ≤ 12 | |
| Y5 via fold-backs / Y6 poured hops / Y7 via steps | 26 / 2 / 1 | | ≤ 10 / 0 / 0 | |
| Z1 pyro DRC rule margins (closest same-layer pair − minimum), mm: A 0.001, B 0.170, C 0.077, D 0.001, E 0.300, F 0.200, G 0.000, H 0.025 | — | every rule ≥ 0 (DRC) | B ≥ 0.17, C ≥ 0.077, E ≥ 0.30, F ≥ 0.20, H ≥ 0.025 | H ≥ 0.2, G ≥ 0.05 |
| Z2 pyro exit lanes CH1 block → U1 (GATE_N 40.0, CONT 45.4, ARM1_SENSE 52.1), mm | 137.5 | | ≤ 137.5 | ≤ 80 |
| Z5 bare PYRO1_GATE pad to bare armed-live pad (R126.2 → R134.2; coating/leakage P3), mm | 1.027 | | ≥ 1.027 | ≥ 2.0 |
| Z5b bare gate pad to other always-live pad (Q121.4 ACT_GATE → C120.1 ACT_FET_S), mm | 0.634 | | ≥ 0.634 | |
| Z4 vias inside test pads (A8: TP122's PYRO1_GATE via) | 1 | M2: bare contacts only | ≤ 1 | 0 |
| Z3 IMU lever arm \|x − 23\| (U4 bottom, rot 0, at (10.0, 53.8)), mm | 13.0 | axis map unchanged or re-derived | ≤ 13.0 | ≤ 5 |
| F1 / F2 fit: worst top / bottom envelope margin (J9 mated / C91), mm | 0.028 / 2.357 | ≥ 0 (P2) | ≥ 0.028 / ≥ 2.357 | top ≥ 0.5 |
| F3 / F4 support clearance bottom / top hardware (R12.1 at (4, 64); TP30.1 at (4, 4)), mm | 4.452 / 5.008 | ≥ 3.5 / ≥ 3.8 (P2) | | |
| index_r8 / index_r9 (R8 = 100) | 100 / 100 | | ≤ 86 / ≤ 73 (every done row met exactly gives 85.2 / 72.4) | ≤ 60 / ≤ 50 |

**Why ≤ 110 mm (X1):** R8's top courtyards total 2156 mm² (bottom 979 mm², never limiting). At 46 mm width that is
top utilisation 0.401 at 118 mm, 0.426 at 110 mm (R7: 0.422) and 0.449 at 104 mm (R6, 46 × 100 mm without the RF
strip, which carried 0.449). So 110 mm needs no denser top than R7 already proved routable, and 104 mm R6's. Limits on
shortening: the RF strip (21.4 mm of parts, fence at y 23.3), the tall parts' bore bands (J122 mated 23.5 mm at
x 19–27, margin 0.71; the terminals at margin 1.15), five supports with 3.5 / 3.8 mm clearances, the J122 tie holes.
A shorter outline moves the forward supports, so VEHICLE.md's hole list, fit_check's `RETENTION_HOLES` and the
mechanical first-mode estimate (`step9/plate_model.py`; R8 f1 209–490 Hz, 6–8 % below R7) must be redone.

## 3. Definitions of the new rows

- **X1** outline from `GetBoardPolygonOutlines`; envelope = union of every courtyard bbox and the outline.
- **X2** armed-live copper = PYRO1_BUS / PYRO1_IGN / PYRO1_OUT (bus, igniter, drain: `check_r8.PYRO_LIVE`). Own nets
  = names starting PYRO or ARM, GND, RAW_ACT (the ARM break's source side). Foreign = any other net with a pad,
  track, via or fill within 3.0 mm edge to edge (`check_r8.min_gap`): same copper layer (as `step9/pyro_neighbours.py`)
  and plan view (any layer). No-connect pads (`unconnected-*`) are counted apart (R8: D120.2 at 2.21 mm). CH1 block =
  `check_r8.CH1_PARTS` courtyards; "through" = foreign tracks/vias whose bbox overlaps the block bbox (GND excluded).
- **X3** strip = bbox of `check_r8.STRIP_PARTS` courtyards (jacks, modules, RF-line parts, limiter) and RF_NETS copper,
  clipped to the outline; RF zone = every `check_r7.RF_PART`. rf / rfif = route_check classes.
- **X5** widths rounded to 1 µm, by route_check class (signal = not power, not GND). **X6** bends as survey S10
  (heading change at plain nodes), per mm of the same nets' copper. **X8** rule areas incl. keep-outs.
- **X9** `check_r8.rf_separation` / `inner_power_pyro` / `battery_pyro` nearest values (designator-based rules, no
  coordinates: reusable on R9).
- **Y** from `m2_sweep.json`: `adjacency` deduplicated over layers (a via-via pair counts once), `adjacency_pad`
  split own_part / foreign_part.
- **Z1** `requalify.pyro_rules` closest pair per rule; **Z2** `requalify.exits` new copper of the three exit nets;
  **Z5** `requalify.bare` (exposed pads on one face). **F** `fit_check --report`.

## 4. Where R8's complexity sits (what the clean sheet should attack)

1. **The rigid CH1 block sits in the battery/power-switch corridor.** Six foreign power-path nets within 3 mm of
   armed-live copper on the same layer, BAT_ENABLE 0.70 mm from R134.1 (it runs east on y 98.45 between the block and
   RAW_PROTECTED, the longest chain detour after RAW_PROTECTED's), the ACT_FET_S pour 1.089 mm from J124.1 (0.089 over
   D85), six foreign nets through the block's bbox, and 137.5 mm of exit lanes to U1 (ARM1_SENSE 52 mm, CONT 45 mm on
   B.Cu with a 9.3 mm chain detour, the rule-G 0.300 mm GATE_N–CONT pair). Rule margins A/D/G at 0.000–0.001 mm are
   pour clearances set to the rule (by construction); B 0.17, C 0.077, H 0.025 are real part-to-part margins.
2. **The 11 R8 misses:** C1/C3 = A2/A3, the limiter's GNSS_LNA_EN / GNSS_VCC_RF vias pushed off U30's paste
   (rigid strip, D51/D87) plus A8; C2 91 info instances (pad-entry offsets set by lane pitch vs pad pitch); S8/S9 the
   same two limiter nets, RADIO_TXEN's rigid loop round U31 and RAW_ACT_SENSE_MCU's one VLOGIC crossover at U1 pin 17;
   S15 the rigid In2 ARM1_SENSE link; P6 In2 split into 3V3 (117 voids) / GND / RAW_ACT / BAT_IN regions; P7 one F.Cu
   GND island on one via; P9/P10 the forward 47 mm (y 70.8–118: p95 5.9 / 5.7 mm, max 9.65 at the left edge
   (0.25, 88.25)) where pyro spacing and power pours keep GND vias out; R6b own-via antipads (3,592 samples) and the
   HSE lines over `Y1_In2_keepout` (1,368).
3. **RF strip** (y 0–23.5, fence 25 vias at y 23.3, four openings 2.0–2.6 mm): RF lines are 18.4 mm, but the interface
   is 321 mm of rfif copper; GNSS RF-line stitching gaps 3.9 mm (west) / 2.65 mm (east) are R7-accepted exceptions
   above `check_r7.STITCH_GAP` 2.5 mm (radio 1.55 / 1.55).
4. **Routing texture:** 11 track widths (signal 0.15 for 25.9 mm and 0.25/0.4 for short runs beside 0.2; power eight
   widths 0.2–0.8), 26 via fold-backs, 27 close pairs < 0.2 mm (8 at the 0.150 DRC minimum, all in the camera / U1 /
   IMU via fields), 8 pour-trim rule areas patching fills.

## 5. Rigid contracts and fixed coordinates R9 must replace with rules (at least as strict)

`check_r8.rigid` hashes 12 groups against R7: outline, m3_holes, j122_tie, j1, pyro_block_area, ch1_parts,
ch1_copper, strip_parts, strip_rf_copper, strip_gnd, strip_rule_areas, strip_gcpw. Fixed-coordinate constants that
encode R7/R8 geometry: `check_r7` JACKS (12.85 / 31.54), STRIP_Y 23.5, FENCE_Y 23.3 / FENCE_PITCH 2.0 /
FENCE_OPENINGS, U31_BODY and MODULE_GND boxes, STITCH_ACCEPTED (GNSS 4.0 / 2.7), CH1_PADS; `check_r8` EXIT_VIAS,
RIGID_IN2, RIGID_BASELINE; `route_check` ROUTE_FIGURES (A2/A3 at y 8.3), MODULE_BODIES; `fit_check`
RETENTION_HOLES (21.5, 68.6) / (27.0, 82.6). `m3.kicad_dru` is net-based except rule G's `PYRO_BLOCK` area and the
U30/U31 keep-out areas, which must be redrawn round the new parts. `check_actuators.py` is netlist-only and stays.

R8 values the rule-based replacements must hold or beat (from `check_r8` evidence and `gcpw_summary.py`):

| Property | Rule (source) | R8 measured |
|---|---|---|
| RF50 lines | width 0.30 mm exactly, GND gap ≥ 0.25 mm (DRU), SMA launch gap ≥ 0.30, pads ≥ 0.2 mm from the aft edge | 0.30 mm; F.Cu GND 0.26–0.28 mm on the straight runs, 0.31–0.38 at the corners |
| Strip contents | F10 per-layer net lists (`check_r7`), U31 pad field GND only, top two layers under U30 GND + own escapes | OK |
| Fence | GND vias ≤ 2.0 mm pitch, openings ≤ 2.7 mm crossed by a lane (D16) | 25 vias, openings 2.015 / 2.6 / 2.1 / 2.1 mm |
| RF-line stitching | GND vias beside each RF line, gap ≤ 2.5 mm (R7 accepted GNSS 4.0 / 2.7) | GNSS 3.9 / 2.65, radio 1.55 / 1.55 mm |
| Strip GND reach | ≤ 4.0 mm of copper to a GND via (`STRIP_GND_REACH`) | F.Cu 3.04, B.Cu 3.49 mm |
| RF clamp / pi-pad GND vias | ≤ 0.6 mm (`RF_GND_VIA`), solid (RF_SOLID_GND) | 0.16 mm each |
| Launch / module reference | In2 GND under each In1 launch cut-out (+0.3 mm); In1/In2 GND under U31 body, In1 under U30 keep-out | 0 samples missing |
| F10 separation | ≥ 5 mm courtyard (restricted parts) and plan (fast lines) | 5.94 / 5.075 mm |
| Pyro | DRU A–H, battery_pyro ≥ 1.0, inner_power_pyro ≥ 2.5, gate_servo ≥ 0.5, rule H pads ≥ 1.0 | margins in Z1, X9; gate_servo none under limit |
| CH1 copper | no foreign copper inside the block, exits via ≥ GND via within 1.5 mm (C6), In2 signal 0 | X2, X2g, Z2; S15 3.4 (rigid exemption) |
| Outline / holes | P1 46 × ≤ 120; five M3 supports, ≥ 3.5 / 3.8 mm clearances; J122 tie holes beyond J122's ends | 46 × 118; 4.452 / 5.008 mm |

## 6. Must be re-derived on the new geometry (never inherited)

Pyro rules A–H and the R4 solder-bridge analysis (Z1, rule H pads ≥ 1.0 mm, every exposed bus/igniter/drain/RAW_ACT
pad vs sense/gate pads, divider midpoints vs gate pads); coating and leakage distances (Z5/Z5b, J2.3 NRST 0.483 mm from
J2.1 3V3 is TC2030 geometry); divider fault tolerance and gate reset behaviour (the netlist is unchanged, so the
circuit analyses stand, but every pad pairing that a solder bridge could create must be re-listed); GCPW / launch /
fence / keep-outs / coexistence (section 5, R7 pass2_rf 3.9–3.11 distances in `requalify.rf`); the three DC solves at
0.05 mm; the GND return (`run_dc.sh` with `DC_GND=0.1`, about an hour; R8 record 0.69 mΩ, not re-run here); hot-plug feed; tab windows; P2 fit and the first-mode estimate; IMU
axis map and lever arm; the firmware pin binding (contract pins 3, 15, 22–25, 33, 34, 98 fixed by `check_r8`).

## 7. Caveats

- `python -I` ignores PYTHONDONTWRITEBYTECODE: the repo's own scripts write `tools/__pycache__` and
  `m3_design/__pycache__` (gitignored). `run_r9_survey.sh` uses `-B` for its own calls and removes caches it created.
- The repo gate on an R9 board fails on the rigid digests by design; use `GATE_SH`. route_check's ALLOWLIST/ROUTE_FIGURES
  are R8 coordinates: on R9, C1/C2 instance counts are comparable, verdicts are not.
- DC rows assume designators Q120, Q121, J1, J122; `requalify` and `m2_sweep` assume the CH1 / RF designators.
- The 0.1 mm grid differs from 0.05 mm by ≤ 0.9 °C and ≤ 0.17 mm of neck on these paths; compare like grids (the scorecard does).
- All distances are geometry; no field solve, no thermal model beyond the IPC-2152 fit without plane credit.
