# R7 fix pass 6, agent F7 (board, tools): handoff

Worktree branch `m3-assy-r7`, uncommitted, on R6 commit `3b215ba`. Start: the fix-pass-5 board, SHA-256
`1ffc2585cbbb2a49623a5010b2792500849f06989cf43e48fb3e56068cddf9df` (copy `<scratchpad>/fx6/base.kicad_pcb`). Nothing
committed, pushed or opened as a PR. I did not edit `docs/*.md`, `STATUS.md`, `AGENTS.md`, `m3.kicad_dru`,
`check_actuators.py` or `check_r7.py`. Running log: `fix6_F7_progress.md`. Scratch evidence: `<scratchpad>/fx6/`
(`dev.sh` / `from.sh` / `gate.sh`, `d4/` = the final copper, `final.kicad_pcb` = the built board, `dc4/` DC solves,
`dcout/` the BAT_IN_F variants, `cr_*.txt` critical reference, `scan2_*.txt` the pass-2 scan, `altall*.txt` redraw
searches, `probe.py`, `viaspot.py`, `newgap.py`, `pairlen.py`).

**Final board SHA-256 `4673c0a0f9fd290af694d6ca5a97e99b3b225466882ba5c6e57a9ad856b96ebd`.** `m3_design/r7_build.sh`,
run unmodified from the SHA-checked R6 board, produced it and exited 0 (its `tools/check.sh` passed; `fx6/build1.log`,
13 min 48 s). A second unmodified run reproduced the same SHA byte for byte (`fx6/build2.log`, 12 min 23 s). The dev pipeline from the F5 post-hygiene board (`fx4/hyg`, SHA `dfca97c4…`, which predates the
J31 value change) gives a board that differs from it only in J31's Value line (`fx6/d5`), so every copper change is in
`r7_polish.py` and the post-hygiene copper is unchanged.

## 1. Per item

| # | Item | Done? | What changed (all in `m3_design/r7_polish.py` unless named) |
|---|---|---|---|
| 1 | P6-ROUTING_QUALITY-01 QSPI_IO3 bump | **Yes** | stage `qspi6`: the five F.Cu segments (N/W/N/E/N) → one segment (22.5, 40.3) → (22.5, 35.4); 0.206 mm to U3.8 (the gap the run beside U3.8 already had), DRC 0. QSPI_IO3 24.06 → 21.66 mm. critical_reference base → final: 0 lost, 0 new (both methods) |
| 2 | P6-REGRESSION-01 BAT_IN_F vias | **Yes** (path changed, not the old spots) | stage `bat_in_f6`. The old spots (7.6 / 8.8, 26.6) lie under the band-end In2 GND strip (they would bring the split crossings back). Inside BAT_IN_F the only legal spot reaching In2 BAT_IN (which now starts at y 31.61) is (8.75, 35.65), 0.60 mm from the existing via: TP89's 1.0 mm bare-pad keep-out and the radio corridor's B.Cu close the rest (`fx6/viaspot.py`; the reviewer's (8.4, 32.0) fails on TP89). So BAT_IN_F grows east to x 9.9 over y 31.4–36.9 (signal-free GND F.Cu; it now takes the edge via (9.2, 36.05) whole) and gets two 0.6/0.3 mm BAT_IN vias (9.7, 31.75) and (9.7, 35.5), both in the F.Cu and In2 BAT_IN fills (asserted), outside the GND strip (y < 31.3). No radio line crosses BAT_IN again (critical_reference 0 lost / 0 new; the vias sit under the BAT_IN_F pour). DC (0.1 mm grid): **C89.1 → U9.5 10.35 → 7.05 mΩ** (6.91 before band_end), **C95.1 → U9.5 7.37 → 5.60 mΩ** (6.57); J1 → U9.5 15.18 → 15.18. Variants measured (C89 / C95): one via at (8.75, 35.65) 8.66 / 5.75; zone + (9.7, 35.5) 7.78 / 5.84; chosen two vias 7.05 / 5.60; three vias 6.88 / 5.30 (rejected: its third via's ring touches (9.2, 36.05), 0.602 mm centres) |
| 3 | P6-REGRESSION-02 SERVO4_MCU / CAM_FAULT_N | **Yes** for the parallel runs | stage `servo_fault6`. CAM_FAULT_N: one SE diagonal out of its F.Cu via onto x 14.6414, straight through its via (14.6414, 90.8244) (the 0.549 mm stub gone) to y 91.85, one SE 0.776 mm step onto x 15.19 (0.40 mm from CAM_PWR_EN's via, which fixes x 15.19 below it). SERVO4_MCU: x 15.505 to y 91.3 (past the 3V3 via (16.3, 90.525)), one SE 0.707 mm step onto x 16.005, old end diagonal. Parallel-run edge gap 0.165 → **0.714 mm** (upper) / **0.665 mm** (lower); the steps run parallel 0.85 mm apart. CAM_FAULT_N within ≤ 0.2 mm of SERVO4_MCU: 30.45 → 6.59 mm (≤ 0.3: 31.26 → 7.33; ≤ 0.5: 36.16 → 12.03; `pairlen.py`). Left (the base's own geometry, 0.161–0.194 mm): the parallel end diagonals and E runs into y 103.63 / 103.94 (SERVO4's E run cannot move north: RAW_PROTECTED's via (18.05, 102.87) and In2 run, probed; CAM_FAULT_N's cannot move south: GND vias (24.55 / 25.45, 104.47)) and SERVO4_MCU's 0.164 mm pass of CAM_FAULT_N's via (16.0438, 67.4556) (fix pass 5). Lengths: CAM_FAULT_N 95.62 → 95.07 mm, SERVO4_MCU 96.38 (same); LEFTOVERS / `ROUTE_FIGURES` updated. Two new `extra_bends` information instances (non-critical) |
| 4 | P6-ROUTING_GEOMETRY-01 SW_NODE | **Yes** | stage `sw6`: the reviewer's redraw (SE 0.849, E 1.70, NE 1.414, E 0.70, NE 1.697, ending 0.2 mm further inside L1.1's 1.6 × 3.5 mm pad). Allowlist A3, A4, A5 (and `_SW`) **deleted**. Minimum gap 0.213 mm (was 0.170). Buck geometry: only SW_NODE copper changed; U2.5 → C5.1 (0.4 mm), the input capacitor C7 / VLOGIC, C9 and every GND return are untouched; SW_NODE copper (tracks + pads) 9.661 → 9.840 mm² (+0.18 mm², +1.9 %; `netarea.py`). 3V3 DC: L1:2 → U1:75 15.64 → 15.64, → FB31:1 14.66 → 14.66 mΩ (→ U1:100 78.23 → 73.46, from item 6's 3V3 redraw) |
| 5 | P6-ROUTING_GEOMETRY-02 two-segment jogs | **Yes** | `tools/route_check.py`: `tiny_jog` now also covers a chain window P, M1..Mk (k ≥ 2), Q with Q back on P's heading and every middle segment off it, tiny when Σmiddle < 0.5 mm or Q runs < 0.25 mm off P's line (`compound=k`); `path_defects` (alt_audit's candidate vetting) tests the same. Whole board: the only instance was LOGIC_SS (offset 0.141 mm), now redrawn (stage `logic_ss6`: pad edge 0.3 mm S, one SW diagonal; 0.183 mm to U11.12 GND, −0.32 mm). Nothing else on the board matched (the next nearest, IMU_INT1 B.Cu (26.3, 66.3), runs 0.2503 mm off its line: not tiny). Test `test_a_jog_with_a_two_segment_middle_is_a_tiny_jog` |
| 6 | P6-DOCS-01 poured-net detours / extra vias | **Yes** (gated) | `tools/route_check.py`, two hygiene categories on nets with a pour (GND, 3V3, 3V3A, BAT_IN, RAW_ACT, CAM_5V, ACT_FET_S; all critical, so gated): **`chain_detour`** (a run between junctions longer than 1.25 × the octilinear distance of its ends and by > 0.5 mm, the pass-2 scan's measure) and **`pour_net_hop`** (two or more pure layer-change vias in series: a via joining exactly two of the net's track ends, on two layers, at its centre, with no pad, no other track and no fill of its own pour on any layer). Every entry carries its run's measured length (and via count) as a sixth element, checked by `measured_check`; every `chain_detour` entry is also re-searched by `alt_audit` (1–3 segment redraws that end the detour). Found on the start board: 18 chain detours (the reviewer's 17 plus the 3V3A hop) and 5 hops. **Fixed (10):** the 3V3 C179 dip (stage `v3v3_6`, 9.44 → 6.58 mm, 0.47 mm min gap); RAW_ACT's B.Cu duplicate deleted (stage `raw_act6`); in stage `ties6` GND J1.2 → via, J3.4 → J3.A1B12, J3.1 → J3.B1A12, J3.1 → R85.2 (one straight run each from inside the big pad), J3.1 → C28.2 (NW/N/NE, 7.30 → 5.90 mm), R130.2 → R178.2 (L with a chamfer; the octilinear line would pass R130.1 / PYRO1_CONT at 0.170 mm, this keeps 0.30), the 3V3A hop round GND via (36.5, 76.54) (2.505 → 2.404 mm) and ACT_FET_S R120.1 → Q120.1 (3.60 → 2.41 mm). **Kept with measured reasons in `ALLOWLIST` (13):** 8 chain detours (C7's 3V3 feed to C100, GND U1.74 / U1.49 / C99.2 / U10.2 / C23.2 ties, the RAW_ACT sense tap's two F.Cu ends) and 5 hops (3V3 into J2.1, the 3V3 In2 feed over the CAM_FAULT_N / SERVO4 lanes, 3V3 B → In2 → F at (35.1, 45.0), the RAW_ACT sense tap, CAM_5V U13.1 → C91.1), each naming its probed blockers (§4). **RAW_ACT sense tap:** not shortened. A via beside R177.1 collides with VBUS_SENSE's F.Cu diagonal and USB_DM / USB_DP's B.Cu at x 10.05; F.Cu toward the pour is closed by LS120.1, D123.1 and 3V3's runs, B.Cu by the BAT_IN_B pour from y 80.9; the end via is boxed by VBUS's F.Cu run and C83.1 (its 0.5 mm² fill fragment joins nothing), so the F.Cu tail round VBUS's via is the shortest legal end (all probed, `fx6/p_tap.json`, `altall_base.txt`). RAW_ACT duplicate DC: Q121 → J124:2 1.47 → 1.50 mΩ; **Q121 → J122 (7.7 A) 3.95 → 3.98 mΩ** (+0.8 %, +1.8 mW; the B.Cu run carried a little of it), peak 5.75 A/mm and the IPC-2152 neck unchanged, so the IPC-2152 capacity is not reduced (Inference from the unchanged neck width and peak density). Tests `test_chain_detour_on_a_poured_net_is_gated_and_measured`, `test_two_pure_layer_changes_in_series_on_a_poured_net` |
| 7 | P6-ROUTING_QUALITY-03 / P6-REGRESSION-03 adjacencies | **Recorded** (§5) | no copper change |
| 8 | J31 value | **Yes** | `m3_design/r7_sch.py` J31 Value "915MHZ ANT SMA" → **"RADIO ANT SMA"** (the board's jack legend is RADIO; J30 is "GNSS ANT SMA"); `r7_sch.py --netlist` rerun on the repository project changed exactly `telemetry.kicad_sch` l.5286 and `schematic.net.xml` l.7333; the board takes it from the netlist in `r7_pcb.py`. Parity 0; BOM line 36 now "GNSS ANT SMA; RADIO ANT SMA" |

Also changed in `route_check.py` (found while doing item 6): `alt_audit` did not know the 0.25 mm copper-to-hole rule at
non-plated holes (Clearance sees no copper there), so it reported a redraw 0.16 mm from J3's locating peg as removable
and DRC rejected it. Candidates must now keep `NPTH_CLEAR` = 0.26 mm from every NPTH hole; `r7_polish.draw` asserts the
same for every hand-drawn segment (board minimum before this pass 0.47 mm, so no earlier stage is affected). Test
`test_alt_audit_keeps_the_copper_to_hole_rule_at_non_plated_holes` (it fails without the check). The LEFTOVERS comment
now matches `LEFTOVER_CATS` (P6-DOCS-04(b)). `r7_polish.run` lets exactly one stage (`raw_act6`) split a track-only pad
group, and that stage asserts the split (J124.2 leaves Q121's track group; groups with the pours unchanged).
`TRIM_EXPECTED['pour_trim']` 23 → 22 (the GND B.Cu finger by the 3V3A hop is gone). The summary line now ends
"… removable jog / staircase / short-segment / chain-detour exceptions".

## 2. `route_check` counts — before / after

All (critical) / failing / allowlisted / leftovers:

| | Start board, F6's tool | Start board, F7's tool | **Final board** |
|---|---|---|---|
| total | 312 / 0 / 33 / 30 | 336 / 23 failing + 1 unrecorded / 33 / 30 | **323 / 0 / 43 / 30** |
| chain_detour | – | 18 (18) | **8 (8)**, all allowlisted |
| pour_net_hop | – | 5 (5) | **5 (5)**, all allowlisted |
| tiny_jog | 3 (3) | 4 (3) (+ LOGIC_SS compound) | **2 (2)** (A1, A2 band fan-in) |
| short_segment | 2 (2) | 2 (2) | **0** |
| critical_via_no_gnd | 9 | 9 | 9 |
| detour / extra_vias | 22 (9) / 27 (10) | same | 22 (9) / 27 (10) |
| info: pad_end_offcentre / width_change_junction / segment_inside_pad / passes_through_pad / extra_bends / u_turn / short_layer_hop / power_via_no_gnd | 93 / 31 / 3 / 10 / 32 / 25 / 20 / 35 | same | 94 / 31 / 4 / 9 / 34 / 23 / 20 / 35 |

New information instances: `pad_end_offcentre` + `segment_inside_pad` LOGIC_SS at U11.11 (the 0.3 mm straight exit
inside the 0.2 × 0.6 mm pad, then the diagonal from its edge), `extra_bends` CAM_FAULT_N and SERVO4_MCU (×2, the steps)
and SW_NODE (moved). Gone: R85.2's off-centre end, RAW_ACT's pass through Q121.5, two U-turns.

Final allowlist (43): band fan-in tiny jogs A1/A2; 9 critical layer changes without a GND via (8 radio + PYRO1_GATE
into TP122; `nognd_audit` 0 out of date); 19 detour / extra_vias entries (unchanged); **8 chain_detour + 5
pour_net_hop entries (new)**. Leftovers 30 (13 detour + 17 extra_vias; CAM_FAULT_N and SERVO4_MCU reasons and figures
updated). Gate audits: 0 out-of-date no-GND reasons, 0 out-of-date route figures, 0 removable exceptions.

Pass-2 `scan.py` (unchanged, `rg/scan.py`, vs R6), all (critical): **945 (591) → 918 (559)** — chain_detour 61 (41) →
50 (30), dogleg 147 → 137, right_angle_corner 57 → 43, u_turn 25 → 23, passes_through_pad 10 → 9; up: extra_bends
32 → 34, pad_end_offcentre 205 → 209 (runs that now end inside the big pads J1.2 / J3.1 / J3.4 / L1.1 off centre, and
U11.11), off_angle_rounding 25 → 27 (SERVO4_MCU's step: 1 nm from `pcbnew.FromMM` truncation, as the other 25),
segment_inside_pad 3 → 4, via_pair_close 22 → 23 (the new BAT_IN via 0.74 mm from (9.2, 36.05)).

## 3. Electrical evidence (final board; its copper and fills equal `fx6/d4`, where the solves ran)

- **Connectivity:** every polish stage keeps the pad groups with the pours (asserted); KiCad unconnected 0, parity 0.
  CH1 pyro copper (PYRO1_BUS / IGN / OUT, PYRO1_GATE(_N), ARM1_SENSE(_MID)) untouched; pyro sentinel pins untouched;
  `m3.kicad_dru` untouched; `check_actuators` OK. The nearest new copper to a pyro net is the R130.2 → R178.2 GND
  chamfer, 0.30 mm from R130.1 (PYRO1_CONT).
- **Critical reference** (`tools/critical_reference.py`): start → final **0 lost, 0 candidate-new** (R6 method: 69,925
  referenced; extended: 168,989 referenced). R6 (+18 mm) → final: 603 lost / 882 candidate-new, identical to R6 →
  start board.
- **DC** (`tools/dc_solve.py`, board stack-up, 0.1 mm grid, mΩ, start → final):

  | Path | Start | Final |
  |---|---:|---:|
  | RAW_ACT Q121:5–9 → J122:2,5,8,11 (7.7 A) | 3.95 | **3.98** (peak 5.75 A/mm unchanged) |
  | RAW_ACT Q121:5–9 → J124:2 (pyro bus feed) | 1.47 | **1.50** |
  | RAW_ACT Q121:5–9 → R177:1 (sense tap) | 86.54 | 86.57 |
  | BAT_IN J1:1 → Q120:5–9 (7.7 A) | 4.58 | 4.58 (peak 6.17 A/mm unchanged) |
  | ACT_FET_S Q120:1–3 → Q121:1–3 (7.7 A) | 1.36 | 1.36 |
  | BAT_IN J1:1 → U9:5 | 15.18 | 15.18 |
  | BAT_IN C89:1 → U9:5 | 10.35 | **7.05** |
  | BAT_IN C95:1 → U9:5 | 7.37 | **5.60** |
  | 3V3 L1:2 → U1:75 / FB31:1 / U1:100 | 15.64 / 14.66 / 78.23 | 15.64 / 14.66 / **73.46** |
  | 3V3A U4:5 → C31:1 | 5.86 | 5.84 |

  (`fx6/dc4/*.txt`; start values from F6's handoff and the pass-6 regression review, C89 / C95 / J1 → U9 / J1 → C89
  re-solved here on the start board.) USB_LIMITED, VLOGIC, CAM_5V, 3V3_RADIO copper unchanged. IPC-2152 necks unchanged.

## 4. Measured reasons of the new allowlist entries (blockers probed with `fx6/probe.py` / `altall.py`)

- chain_detour 3V3 B.Cu (36.94, 52.65), C7, 16.32 mm: both octilinear two-segment routes cross 3V3A's B.Cu x 40.1.
- chain_detour GND F.Cu (14.3, 59.0) U1.74 → via (11.3, 59.3), 6.62 mm: 3V3 F.Cu run and via (12.6, 59.5).
- chain_detour GND F.Cu (16.35, 45.95) U1.49 → via 2.4 mm above: straight run passes 3V3 via (15.85, 44.25) at 0.075 mm.
- chain_detour GND F.Cu (27.65, 29.85) → C99.2, 2.31 mm: VLOGIC's diagonal; clean 3-segment redraws 2.53 mm.
- chain_detour GND B.Cu (13.7, 80.6) U10.2 → Q123.2, 6.08 mm: U10.1 (VBUS) and RAW_ACT's via (12.6, 81.27).
- chain_detour GND B.Cu (32.3, 55.7) C23.2 → via, 4.01 mm: 3V3's B.Cu run to C23.1; clean redraws 4.05 mm.
- chain_detour RAW_ACT F.Cu (10.4, 64.67) and (12.6, 81.27): the sense tap's two ends (item 6).
- pour_net_hop 3V3 (41.0, 77.92): F.Cu into J2.1 crosses SWDIO's diagonal into J2 and J2's contact rule.
- pour_net_hop 3V3 (12.5, 89.2): In2 crosses the BAT_IN In2 fill and the CAM_FAULT_N / SERVO4_MCU lanes.
- pour_net_hop 3V3 (35.1, 45.025): B.Cu crosses 3V3A (36.9–39.4, y 48.1), F.Cu RAW_PROTECTED's diagonal.
- pour_net_hop RAW_ACT (13.1, 75.97): the sense tap (item 6).
- pour_net_hop CAM_5V (41.3, 32.425): B.Cu U13.1 → C91.1 crosses CAM_IO_3V3's diagonal and U13.5.

## 5. Close adjacencies (for the records; all ≥ the 0.15 mm rule, DRC 0)

New in this pass (edge gap < 0.2 mm, `newgap.py` on every added track and via):
- 3V3A B.Cu hop (ties6) – GND via (36.5, 76.54): **0.169 mm** (was 0.34). A short ties the IMU's analog supply to GND:
  the board fails its bring-up / JLC electrical test, not a safety case (Inference).
- LOGIC_SS (logic_ss6) – U11.12 (GND): 0.183 mm (the old route's minimum was 0.187 to the GND via (28.13, 31.3)).
- SERVO4_MCU lower vertical – CAM_FAULT_N's end diagonal: 0.194 mm at its bottom corner (the end diagonals' own,
  base geometry).
- Not copper: GND J3.1 → C28.2 is 0.267 mm from J3's non-plated peg hole (rule 0.25).

Carried from pass 6 (P6-ROUTING_QUALITY-03, P6-REGRESSION-03), unchanged by this pass, re-measured on the final board:
- GND via (35.85, 53.275) (gnd_pieces) – NRST via (35.80, 53.95): **0.177 mm** edge on all four layers (hole to hole
  0.377 mm); – NRST's B.Cu diagonal (33.45, 51.60)–(35.80, 53.95): 0.188 mm; – 3V3A B.Cu: 0.175 mm. Failure mode of an
  NRST–GND short: the MCU is held in reset, so the board is dead at bring-up; the pyro gates are defined off (AGENTS §2.4)
  and the radio is held in reset by hardware. Not unsafe, but not of the "reads no continuity / disarmed" kind C15
  describes. Both vias tented and plugged (ORDERING §3); JLC's electrical test screens shorts (Inference).
- CAM_FAULT_N In2 E run (y 103.938) – GND vias (24.55, 104.47) and (25.45, 104.47): 0.162 mm (base ≥ 0.2). A short
  reads "camera fault" (the eFuse flag, 10 kΩ pull-up R76).
- CAM_FAULT_N – SERVO4_MCU: now 6.59 mm within 0.2 mm (item 3; base 6.28), the 22.9 mm run at 0.165 mm is gone.
  Coupling estimate for what is left (Inference): a 3.3 V SERVO4 PWM edge through ≲ 0.5 pF into CAM_FAULT_N's ~15 pF
  gives ≲ 0.1 V, far from the STM32 input thresholds.
- NRST's own-net stacking (B.Cu (30.8, 53.1) → (30.8, 52.3) → (31.5, 51.6) over its own In2 branch, ~1.5 mm):
  unchanged; for deviation part C or D.

## 6. Gate and tests (final board)

```
DRC violations 0  unconnected 0  schematic parity 0  ERC 0
metadata / 3D model audit: OK
silkscreen outside the board outline (46.00 x 118.00 mm): 0 stroke points
R7 CAD contract: OK
routing hygiene: 0 failing, 43 allowlisted, 0 stale allowlist entries, 0 out-of-date no-GND reasons, 30 leftovers recorded (0 unrecorded, 0 stale), 0 out-of-date route figures, 0 removable jog / staircase / short-segment / chain-detour exceptions: OK
actuator safety contract: OK
  nearest bottom/pin envelope: C76, 4.150 mm from support (42.0, 114.4) (minimum 3.5 mm)
  nearest top hardware clearance: TP30.1 exposed top pad, 5.008 mm from support (4.0, 4.0) (minimum 3.8 mm)
fit check: OK (CAD envelopes only)
```
(`tools/check.sh` exit 0, run by `r7_build.sh`.) Tests (KiCad Python): check_shell 2, dc_solve 3, fab_validation 23,
fit_check 23, maze_clearances 10, procurement 15, r6_check 17, r7_check 34, **route_check 45** (41 → 45) — 172 OK;
quality_audit 21 OK under KiCad Python and python3 (193); test_r5_repair 1 error, the known `routing_lands_spacing`.

**Fab:** `tools/export_fab.py` regenerated the package and its manifest (bound to `4673c0a0…`; `verify_manifest` 5
outputs OK). BOM changes in line 36 only (J31's comment); CPL byte-identical; `jlc_orient.py --verify-cpl`: 92 top +
119 bottom rows rebuilt, worst 0.491 mm, no errors. Because the BOM changed, `jlc_stock.py` and `jlc_cost.py` were
rerun live (2026-10-18 15:30Z): $105.98 per board, 52 of 52 extended codes, cost targets met
(`check_procurement.py --cost-only` OK); stock short only U4 (0 < 5), as before. Renders `r7_top.png` /
`r7_bottom.png` regenerated (984 × 2184, `kicad-cli pcb render --side top|bottom -w 1016 -h 2208 --quality high`).

## 7. For the records (docs agent)

- R7_VALIDATION part A: A3–A5 (SW_NODE) gone; add the 8 chain_detour and 5 pour_net_hop entries (§4; they replace
  C7 and D7's tail, and Part E's "held by the detour test" rationale for U-turns / layer hops on poured nets: those are
  now gated by `chain_detour` / `pour_net_hop`; Part F's chain detours on poured nets likewise). Allowlist 33 → 43.
- Deviation C17-style records: P6-RG-03's in-via steps, D8.1 / R90.2 debris, ACT_GATE knot, C19 and D7 wording were
  not in my scope and are unchanged (D7's tail is now allowlist entry chain_detour RAW_ACT F.Cu (12.6, 81.27),
  7.108 mm).
- M3_R7: DC table (§3), board SHA, `route_check`'s new categories and the NPTH rule in `alt_audit`, pour trims 23 → 22
  (F.Cu 9 / B.Cu 12 / In2 1), BAT_IN_F outline, J31 value, close adjacencies (§5).
- REQUIREMENTS M2 "what the gate enforces": add compound tiny jogs, `chain_detour` and `pour_net_hop` on poured nets
  with measured figures and the chain-detour `alt_audit`.
- Not done here: owner acceptance; a review pass on `4673c0a0…`; P6-DOCS-02/-03/-04 (records).

## 8. Files changed by F7

`m3_design/r7_polish.py`, `m3_design/r7_sch.py`, `m3_design/r7_build.sh` (comments only), `tools/route_check.py`,
`tools/test_route_check.py`; `m3_design/assembly_review/m3.kicad_pcb`, `telemetry.kicad_sch`, `schematic.net.xml`;
`fab/m3_gerber.zip`, `m3_bom_jlc.csv` (line 36), `m3_assembly_{top,bottom}.pdf`, `m3_fab_manifest.json`,
`stock_check.json`, `cost_check.json` (`m3_cpl_jlc.csv` rewritten byte-identical); `r7_top.png`, `r7_bottom.png`; this
file and `fix6_F7_progress.md`.
