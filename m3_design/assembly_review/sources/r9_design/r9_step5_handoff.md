# R9 step 5 (pyro block): handoff

Step 5 of `r9_plan.md` §4. The CH1 pyro column's copper is built by `m3_design/r9_pyro.py` on the step-4 board and gated
by `m3_design/r9_pyro_check.py`; both run in `m3_design/r9_build.sh`. The built board (`m3_design/assembly_review/
m3.kicad_pcb`, SHA-256 `a6454f78…`, `step5_evidence/build_sha256.txt`) reproduces byte for byte (two full builds). The
step gate passes in full, as do the step-2, -3 and -4 gates in the same build. Nothing committed or pushed. Decisions:
`R9_DECISIONS.md` D-S5-01 … D-S5-15. Log: `r9_step5_progress.md`. Evidence: `step5_evidence/`.

## 1. What was produced

| File | What it is |
|---|---|
| `m3_design/r9_pyro.py` | The builder. Every point derived from pad centres and boxes (pad-referenced); the alignments it relies on are asserted (a moved part stops the build). Draws every CH1 net whole (D-S5-07): the fire loop (1.0 mm bars J124.1 = R134.2, R134.1 = J121.2, J121.1 into the drain), C128 on the drain's tab, the R173 / R131 OUT branch and the R132 BUS tap; the gate row and TP122 (gate via at the GATE run's knee, its partner Q124's source via); GATE_N to U1.3 with a GND guard; the CONT column, row and exit to R168, CONT_MCU to U1.15; COLD; the ARM divider and its lane to R170 and U1.33 (no via); Q124's source comb and vias; D120's 3V3 feed to a via. Re-derives PYRO_BLOCK. `PARTS`, `NETS`, `copper(Pads(board))` |
| `m3_design/r9_pyro_check.py` | The step gate (§2). Functions are importable (`gate_neighbours`, `gate_sense`, `gate_armed`, `gate_margins`, `gate_bridges` run on any later board) |
| `m3_design/r9_place.tsv` | 19 rows changed, 17 parts and the two tie holes (each basis names its D-S5): tie holes (15.6, 62) / (30.8, 59); C92, TP91, U13, C121 (turned 90); R170 (top); R126, C126, C127, R130, R178 (gate / CONT rows on y 61.23); R129, R173, R131, D120, C128, C129; TP122 |
| `m3_design/r9_legalise.py` | `block_area`: exit-net copper counted within check_actuators 15b's reach only (D-S5-11); step 3's area unchanged |
| `m3_design/r9_dru.py` → `assembly_review/m3.kicad_dru` | Eight zone fill-margin rules after rule A2 (D-S5-12); `fill_names`, `fill_block`, `without_fill`; verify extended. DRU sha16 `ea77b791eaa4026d` |
| `m3_design/check_actuators.py` | `DRU_SHA` re-pinned (only change); file sha256 `3f22b273…` |
| `tools/check_r9.py` | `CHECK_ACTUATORS_SHA` re-pinned (only change) |
| `m3_design/r9_sch_check.py` | Fill-equivalence test removes the fill block (`r9_dru.without_fill`) to isolate the LC-1 change; texts |
| `m3_design/r9_build.sh` | Step-5 stages appended: `r9_pyro.py`, `r9_pyro_check.py` |
| `tools/test_r9_pyro.py` | 19 tests: template holds / moved or turned part stops it / extra and moved copper caught; margins hold with the one recorded exception, a centre-ended divider track, GND inside D + 0.2 and a 3V3 track inside G + 0.2 caught; bridges hold, a fires-class pair at 1.12 mm caught (BT's 1.0 mm passes it); GATE_N neighbours GND only, a 3V3 / CONT track 1.2 mm off caught, GND not; X2 holds, 3V3 / BAT_IN near armed copper caught; route pending is only the step's copper; PYRO_BLOCK derived and off U1, exit copper counts only near its pads; the DRU fill margin live (GND fill 0.751 mm with, 0.501 without) |
| `tools/test_r9_sch.py`, `tools/test_r9_rf.py` | test_r9_sch: the fill rules expected, a new fill-rule test; test_r9_rf: the drawn-nets test reads the step-4 tables (D-S5-15) |
| `step5_evidence/` | `r9_pyro_check.{json,txt}`, `pyro_probe.{json,txt}`, `bridge_table.{json,txt}`, `rule_h_seed.{json,txt}`, `check_r9_full.{json,txt}`, `x_metrics.{json,txt}`, `requalify_pyro.json` (the scorecard's Z1 / A8 rows), `build.txt`, `build_sha256.txt`, `tests.txt` |

## 2. Verification (r9_plan §4 step 5, on board `a6454f78…`)

| Item | Result |
|---|---|
| pyro_probe margins >= max(R8, 0.2) | pyro_probe OK. Margins: A 0.32 (R8 0.001), B 0.32 (0.17), C 0.277 (0.077), D 0.27 (0.001), H 0.225 (0.025); E, F, A2 no pair within reach; strict H+ 0.025, GS 0.48, AG 0.162 (all >= 0). **One exception**: G 0.112 (R8 0.000) at GATE_N's entry into U1.3 against the no-net sentinel pins U1.2 / U1.4, bounded by the LQFP geometry (D-S5-13); every other G pair >= 0.5 mm. The scorecard's Z1 rows (requalify): A .32, B .32, C .277, D .27, G .27, H .225: every done floor met Pours: the DRU's fill margins hold rules A-G / A2 + 0.25 (E + 0.35) for every later pour (D-S5-12; measured 0.751 mm GND to armed copper) |
| bridge table, no fires-class bridge under 1.5 mm | 129 exposed pairs under 1.5 mm, 0 forbidden; no fires-class pair between two parts (the only ones listed are parts' own pads: Q124's source / gate pins to its drain, C128's two pads, U1's pins); R128.1 GATE to C127.1 CONT 1.68 mm (was 1.48) |
| rule H live | `rule_h_seed.py`: Q124.5 -- R129.2, R132.1 -- C129.1, Q121.9 -- R121.2 x 8 variants, every one caught (DRC on the seed, check_actuators, LC-1 on the override, pyro_probe on all) |
| every GATE_N neighbour GND or <= 0.2 V in reset | Within 1.5 mm of GATE_N outside U1's courtyard: GND only (the guard's via 0.89 mm). P-7 table: GATE to C127.1 (CONT, 0.41 V) 1.02 mm, to the C128 branch 0.95 mm, U1's pins at the pin entry (QSPI_IO2 0.83, 3V3 1.31 mm; P-7's 0.5 holds; U1's own pins excepted like P-1b, D-S5-14) |
| coating region | check_r9 P-10 OK: the coat region (derived PYRO_BLOCK, bbox 1.2-28.4 x 54.2-89.8, and J2) 5.53 mm from U4, no keep-off part, no test pad but TP122 |
| wire room | P-11 OK: J121 / J124 enter from -x, 6.353 mm to the bore wall |
| check_actuators | no finding (15b passes on the re-derived block; DRU and rule pins) |
| stricter pyro rules P-1b / P-3 / P-7 | check_r9 P-0 … P-11 all OK (P-1 incl. rule G's P-1b scope; P-3 no foreign net in the hull; P-7 OK) plus LC-1, M-6, R-13 (46.13 mm), K-power-pyro, K-copper, K-inner, K-actuators |
| beyond the list | X2 = X2b = X2g = 0 (no foreign net within 3 mm of armed copper), Z2r9 exit track 66.4 mm (<= 80), Z5 2.35 mm (>= 2.0), P-8 CONT_MCU 2.86 / ARM_MCU 2.12 mm, one pyro via (the gate's, partner 1.39 mm), A8 gone, DRC + parity clean (no CH1 net open), route_check r9 clean on the step's nets (pending: the step's 4 GND / 3V3 vias and their runs, §4) |
| full check_r9 | fails only M-2 (no plate report passed), K-contract's route-only items (C29, C100, C93) and K-legends (step 8): the step-4 set, P-4 now passing |
| reproducible, tests | two builds: board, sheets, netlist, DRU and variants byte-identical; 22 suites / 398 tests OK, quality_audit 21 OK under both pythons, audit_artifacts exit 0 (`tests.txt`) |

## 3. Reproduce

```bash
R=rocket-pcb/rocket-flight-computer-r9                                   # this worktree
KP=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
NUMPY_PY=/path/to/python3-with-numpy $R/m3_design/r9_build.sh            # steps 2-5 and their gates (about 2 min)
(cd $R && PYTHONUNBUFFERED=1 $KP -I -B m3_design/r9_pyro_check.py --report out.json)       # about 1 min
(cd $R && PYTHONUNBUFFERED=1 $KP -I tools/pyro_probe.py m3_design/assembly_review/m3.kicad_pcb)
(cd $R && PYTHONUNBUFFERED=1 $KP -I tools/bridge_table.py m3_design/assembly_review/m3.kicad_pcb)
(cd $R/tools && $KP -B -m unittest test_r9_pyro test_r9_sch test_r9_rf)
```
(The parent project's `cfd/venv/bin/python3` has numpy.)

## 4. What the next steps must know

**Pending items** (the step gate lists them; nothing else may be open): GND vias (10.425, 62.45) and (11.8, 62.45)
(Q124's source return; the first is TP122's partner), (13.5, 54.6) (the GATE_N guard; also C10 / C11's GND stitch),
and the 3V3 via (17.9, 56.3) (D120's feed). They dangle until step 8's In1 GND pour and step 6's In2 3V3 region.

**Step 6 (power).**
- In2 3V3 must reach (17.9, 56.3) (outside the CH1 hull + 1 mm; J122's In2 RAW region must clear the via).
- In1 / In2 inside the CH1 hull + 1 mm stay GND only (P-3); D18 keeps inner RAW_ACT / BAT_IN >= 2.65 mm (plan view)
  from bus / igniter / drain copper.
- J124.2's RAW branch: a clean F.Cu path runs along J124.2's line (y 86.04) east to the spine; width 1.0 mm (the board
  has six track widths now: 0.15, 0.2, 0.25, 0.3, 0.4, 1.0; X5 <= 6, so add none).
- The ARM1_SENSE lane is F.Cu at x 28.53 from y 75.6 down to R170 (47.0); F.Cu RAW_ACT keeps >= 0.7 mm from it (rule A
  + 0.2; the fill rule does this for pours); the J122 RAW mouth is fed on B.Cu / In2 under the lane (plan_spine §5.1).
  C121 now has its RAW_ACT pad forward (33.4, 69.9) and its GND pad aft (33.4, 63.3): turn or move it as the spine needs,
  keeping its pads >= 0.25 mm (GND) / 0.8 mm (RAW_ACT: rule A + 0.2, plus half the lane) from the lane's centre line
  and its body >= 5.008 mm from the (42, 59.5) support (M-5).
- The DRU's fill margins (D-S5-12) apply to every pour: RAW_ACT fills keep 0.75 mm from gate / sense copper and 1.35 mm
  from bus / igniter copper; other live fills 0.75 mm from armed copper.

**Step 7 (routing).**
- The "pyro" family is only the RAW_ACT_SENSE divider (R124, R125, R177, R182, C122, R172; D-S5-07).
- U1.27-U1.31's eastward nets (3V3, BAT_FAULT_N, LOGIC_SOURCE_ST, CAM_UART_OE) cross the ARM lane: B.Cu, vias in the
  1.6 mm between U1's pad ends (x 26.35) and the lane (x 28.43 edge) (D-S5-02). U1.34's escape to R172 (bottom) passes
  under the ARM_MCU track (y 47.0).
- Keep every non-GND copper of nets above 0.2 V in reset >= 1.5 mm from GATE_N outside U1's courtyard (the step's
  neighbour rule; P-7 alone asks 0.5 mm): in particular C10 / C11 / R164's 3V3A / 3V3 vias and U1.1 / U1.5-U1.9's
  outward escapes (QSPI and HSE escape inward, as in R8). Re-run `r9_pyro_check.gate_neighbours` on later boards.
- Pins 16-21's escapes west cross CONT_MCU (inherent: U1.15 lies between them and R168); R150.1 is 0.47 mm from
  CONT_MCU's diagonal.
- MCU sides (*_MCU) keep no above-logic copper within 1.5 mm (`gate_sense`).

**Step 8 (ground, silkscreen).**
- Pours get the fill margins automatically. The small parts' GND pads in the column (R127.2, C126.2's guard aside,
  R128.2, C127.2, R130.2, R178.2, C128.2, R133.2, R180.2, C129.2) need the F.Cu pour and stitching; the guard and the
  source comb become live once In1 GND exists (route_check dead() semantics checked: pad to pour island).
- The terminal legends (D92: "1:BUS1" / "2:RAW" beside J124's pads, "1:E1-" / "2:E1+" beside J121's; the pins are
  renumbered, D-S2-01) and every other K-legends item.

**Steps 9-10 (records).** F7's revalidation of the fire loop on the final copper (dc_solve on PYRO1_*; bars 3.15 / 4.96
/ 4.96 mΩ, Calc); the requalification's rule G scope (R8's requalify scopes G to PYRO_BLOCK and will not see
D-S5-13's pair; pyro_probe does); harness / FMEA / ORDERING text for the moved tie holes and TP122 (bottom, (7.58, 63.5),
probe access), R170 now on the top.

## 5. Open

- **Owner's deviation list (not unsafe):** rule G's margin as pyro_probe measures it (P-1b scope, gate copper clipped
  at U1's courtyard) is 0.112 mm at U1.3's pin stub against the no-net sentinel pins (D-S5-13); the floor of 0.2 is
  geometrically out of reach for any straight pin entry on the LQFP. The scorecard's own Z1g (requalify, whole segments
  touching PYRO_BLOCK) is 0.27 mm (`step5_evidence/requalify_pyro.json`), so the done row holds by its definition.
  Every other pyro pair meets its floor.
- Thin but legal (pass their rules): H+ 0.025 mm (Q124.5 drain to R129.2 CONT, 1.225 mm: R4's / R8's figure, held by
  the drain land and the west tie hole's edge clearance to R178), D120's 3V3 lane 0.39 mm from J122.2 and 0.6 mm from the
  west tie hole (0.3 / 0.5 rules).
- Minor: the guard via sits 0.075 mm from C10.2 / C11.2 on B.Cu (same net, tented; DRC and K-copper clean).
- No question for the owner arises from step 5 beyond the deviation above; nothing is unsafe and no requirement's intent
  changes (the DRU change only tightens zone clearances; check_actuators' rule texts are unchanged).
