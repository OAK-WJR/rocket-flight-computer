# R7 fix pass 7, agent F8 (board, tools): handoff

Worktree branch `m3-assy-r7`, uncommitted, on R6 commit `3b215ba`. Start: F7's board, SHA-256
`4673c0a0f9fd290af694d6ca5a97e99b3b225466882ba5c6e57a9ad856b96ebd`. Nothing committed, pushed or opened as a PR. I did
not edit `docs/*.md`, `STATUS.md`, `AGENTS.md`, `m3.kicad_dru` or `check_actuators.py`. Running log:
`fix7_F8_progress.md`. Scratch: `<scratchpad>/f8/` (`pre.sh` builds R6 -> polish `--stop bat_in_f6`; `dev.sh` polishes
from `bumps7` and posts; `gate.sh`; `gap.py`, `newgap.py`, `ctx.py`, `zat.py`; `dc_ipc.py` = `tools/dc_solve.py` plus
the equipotential-cut neck analysis; `dcall.sh` the DC table; `sb/` = the start board with its project files).

**Final board SHA-256 `c872a3d30509cccf5f78b64cde48ef722ee85c7be23c4848b07ce4082a852de3`.** `m3_design/r7_build.sh`,
run unmodified from the SHA-checked R6 board, produced it twice byte for byte (`f8/build5.log`, `build6.log`, 16 min
each), and its `tools/check.sh` exited 0 both times. A separate `tools/check.sh` run on the saved board also exited 0
(`f8/check_final.txt`).

## 1. Per item

| # | Item | Done? | What changed (all copper in `m3_design/r7_polish.py`, new stages between `bat_in_f6` and `gnd_vias`) |
|---|---|---|---|
| 1 | P7-ROUTING-01 bumps | **Yes** | stage `bumps7`. **3V3A** B.Cu bulge round NRST's via: NW, N on x 35.6096, NE (10.77 -> 9.55 mm; min gap 0.212 mm, PYRO1_CONT's via (35.78, 60.65); 0.315 mm to the NRST via). **CAM_5V** B.Cu V-dip: W at y 32.45, 45 deg down x 34.23 (7.50 -> 6.62 mm; 0.272 mm, C60.1). **VLOGIC** F.Cu peak: NE, E at y 27.8, S (6.61 -> 6.02 mm; 0.172 mm, C99.2, as before). **A34** (3V3 C100 feed): west end from the via one SE diagonal and S on x 38.45 (better than the reviewer's 4-segment redraw: it also drops the via's 0.35 mm S piece), east end N, NW, N into C100.1: chain 16.32 -> **14.37 mm** (0.175 / 0.173 mm). |
| 1 | P7-ROUTING-01 item 5 / P7-DOCS-01 | **Yes** | stage `v3pair7`: via (30.4, 70.25) and its 0.81 mm F.Cu stub deleted; the In2 run now starts at via (30.17, 71.17): SE 0.325 mm (a fan-out: the B.Cu run goes straight on through the via), S on x 30.4 to (30.4, 78.25). One via less; both overlap-only joints and the 8.00 mm hop's second via are gone (`via_on_track` 0). The 8 mm In2 run itself stays (records: forced by the SPI/I2C fan on both outer layers; not re-searched). |
| 1 | A34 record | **Yes** | allowlist entry: 14.368 mm, true reason (north side closed by 3V3A's B.Cu run into C11.1; a run between C11's pads not taken; the C19 / C20 / respin text was wrong and is gone). |
| 2 | C26 ACT_EN | **Yes** | stage `acten7`: both vias and the In2 run deleted; one B.Cu run R122.2 -> S on x 11.75 -> SW into Q122.1's centre (3.84 mm for 6.12 mm + 2 vias; 0.50 mm to R122.1). **BAT_IN J1 -> Q120 4.58 -> 3.90 mOhm** on its own (dev board, 0.1 mm), as the records predicted; with item 6 3.03 mOhm. |
| 2 | C24 ARM1_SENSE | **Yes (differently)** | stage `arm1_7`: the F.Cu vertical is **split at R180.1's centre** instead of the records' redraw. The records' redraw at x 16.975 would leave R180.1 (the divider's second top resistor, same net) joined to the run only by 0.065-0.08 mm of copper overlap with no node; the split gives nodes in both pads, removes the pass-through and the chain detour (via -> R180.1 3.33 mm for 2.98) and moves no pyro copper (CH1 geometry and every pyro gap unchanged). |
| 2 | C25 CAM_FAULT_N | **Yes** | stage `tidy7`: In2 E, N, NE (10.52 -> 7.90 mm). It runs 0.169 mm from SERVO4_MCU's In2 piece at x 17.825 (y 63.5-64.8), 7 um further than the R6 run it replaces (same x). |
| 2 | C25 I2C1_SDA | **Yes** | `tidy7`: N 1.05, NE 0.99, E 1.25 into the via (3.47 -> 3.29 mm); min gap 0.275 mm (the records' N, E, NE keeps only 0.175 to U1.97/98). |
| 2 | C25 LED_RED | **No — not removable** | the records' straight In2 run (build #1) cut the 3V3_In2 reference under **QSPI_NCS**'s B.Cu run (25.0-26.4, 40.9-42.0): `critical_reference` lost 465 samples (both methods). Reverted; the bump goes round that piece of plane. Reason in `tidy7`'s docstring; C25's "removable" is wrong. |
| 3 | P7-ROUTING-02 B7 CAM_5V_SENSE | **Yes** | stage `sense7`: the reviewer's In2 redraw NW, NE, NW (12.43 -> 10.89 mm; 0.182 mm to VLOGIC_SENSE's parallel run). **3V3_In2 5 -> 4 pieces** (the 17.6 mm2 piece rejoined). LEFTOVERS B7 (CAM_5V_SENSE detour) deleted: the net-level detour is gone. |
| 3 | P7-ROUTING-02 B23 SERVO2_OUT | **Yes** | `sense7`: the reviewer's In2 redraw (net 37.07 -> 34.94 mm, 1 via, 0.171 mm as before); LEFTOVERS reason rewritten (present route; `--bumps-all` finds no shorter clean redraw; the raster search's 31.4 mm needs the jogs). |
| 3 | P7-ROUTING-03 BAT_IN via | **Yes** | stage `bat_via7`: no spot clear of the B.Cu run is legal (TP89's 1.0 mm keep-out west, via (9.2, 36.05) and BAT_ILIM's F.Cu east), so the via moves 35 um onto the run's line, (9.725, 35.525), and the run is split there (a node). Still inside the BAT_IN_F and In2 fills (asserted). Adds a `short_layer_hop` information instance (0.74 mm to via (9.2, 36.05)). |
| 3 | route_check via-on-track test | **Yes** | new hygiene category `via_on_track` (gated on critical nets): a via on a same-net track's body (centre line through the via centre, no track end in it), or a track whose copper overlaps a via on a layer where the via has no node; in the via's own fill: `via_on_track_in_fill` (information). Start board: 3 = the reviewer's (3V3 pair x2, BAT_IN) + 6 in-fill GND = the reviewer's 6; final: 0 + 6. Test added. |
| 3 | P7-ROUTING-04 / P7-REGRESSION-02 3V3A hop | **Recorded truthfully (restored)** | stage `v3a_hop7`: F7's E-leg-lowered drawing is replaced by the fix-pass-5 drawing (NE, E at y 75.8, SE; 2.505 mm). Measured: its minimum gap to the GND via (36.5, 76.54) is **0.200 mm** (set by the SE diagonal into the east via's centre, whose line the two via positions fix), F7's was 0.169; **the reviewers' "0.34 mm" is wrong** (my gap scan and a hand calculation agree on 0.200). No non-detour drawing exists without moving vias (any drawing that passes the chain metric is the same shape pulled closer). New allowlist entry `chain_detour 3V3A B.Cu (35.5, 76.54)`, 2.505 mm, reason: GND via on the line, IMU GND ties south, hop kept for U4.5's decoupling path (Inference ~1 nH). `alt_audit` now rejects a same-heading "fix" of a chain detour (test added), so the threshold artefact cannot pass again. `pour_trim` 22 -> **23** (the GND B.Cu finger by the hop is back, kept out as before). |
| 3 | P7-REGRESSION-01 BAT_IN_B lobe | **Yes** | stage `bat_in_b7`: a 0.1 mm notch in BAT_IN_B's outline along the deleted RAW_ACT leg's line, from the south edge into J124.2's clearance void, fences the lobe off again: BAT_IN_B 94.0 -> 70.8 mm2 (pass 5: 69.84; +1.0 mm2 where the leg and its clearance ran, west of the notch), one piece, fill east edge <= x 12.46 (asserted); GND_B refills (+31.7 mm2, still 34 pieces). Battery voltage no longer borders 3V3 / RAW_ACT / USB_ILIM / BUZZ_* / ARM1_SENSE there. |
| 3 | P7-REGRESSION-03 | **Records only** | SERVO4_MCU's In2 diagonal (16.005, 101.627)-(18.005, 103.627) – RAW_PROTECTED via (18.05, 102.87): 0.192 mm, inherited R6 geometry. It cannot move SW (CAM_FAULT_N's parallel diagonal and E run at 0.161-0.194 mm, pinned by GND vias (24.55 / 25.45, 104.47)). Failure mode for C15: RAW_PROTECTED (U9 output, to 8.4 V) on PA3 (U1.25) and through D121 (SRV05-4) onto 3V3; internal layer, a laminate defect only (E-test screens it, Inference). |
| 4 | route_check local-bump test | **Yes** | `bump_audit` (category `local_bump`, gated on critical nets incl. poured nets): every window of 2-8 segments of every run that turns back (> 0.05 mm over the Manhattan distance of its ends) and exceeds the octilinear distance by > 0.3 mm and 1.15 x is searched with the project redraw machinery (`alt_candidates`, cap = window - 0.15 mm, shortest first) through a new shared `RedrawCheck`: Clearance (pyro rules, test pads, Tag-Connect), track keep-outs **and the U30/U31 module keep-outs for non-GND nets**, NPTH 0.26 mm, **the true board outline and Edge.Cuts circles at 0.5 mm** (alt_audit used bbox + 0.3); strict extras: no entry into another net's power-pour fill, not between a two-pad part's pads, no same-net copper but the end branches, and on B.Cu / In2 **no nearer a critical signal track on the paired layer than the window** (its reference). Same-heading squeezes are rejected. `--bumps-all` adds the non-critical nets as information (`local_bump_review`). Start board: 5 bumps (3V3 A34-west, 3V3A, CAM_5V, VLOGIC, USB_LIMITED); final: 1 (USB_LIMITED, allowlisted: its redraws cut R105.2 off GND, measured with the pad-group check). 82 windows on critical nets, +18 s on route_check (43 s total). Tests: `test_local_bump_is_gated_and_a_walled_one_is_not_removable`, `test_a_bump_redraw_may_not_cut_a_critical_lines_reference`, `test_alt_audit_does_not_take_a_tighter_copy_of_a_chain_detour_as_its_fix`, `test_redraw_check_keeps_the_edge_clearance_at_an_edge_cuts_hole`, `test_a_via_joined_to_a_track_only_by_overlap`. `scan()`'s node/chain building moved to `topology()` (instances identical on the start board, 324 = 324). |
| 4+ | non-critical bumps (`--bumps-all`) | **2 applied** | stage `review7`: BUZZ_DRV B.Cu (21.10 -> 16.22 mm, S, SW past the M3 hole (4, 64)'s east side at 0.517 mm from its edge against the 0.5 mm rule, asserted; the old run passed its west side at 0.775 mm; merged with the run below) and IMU_INT1 B.Cu (2.33 -> 2.07 mm, same 0.191 mm). **Not applied (recorded):** SERVO2_MCU's zigzag (its redraw cut QSPI_IO2's In2 reference: 179 samples, `--extended`), VLOGIC_SENSE In2 (-0.33 mm but 0.165 mm from a GND via, was 0.199), BAT_SW_SOURCE F.Cu (-1.80 mm at 0.187 mm on a harness line, was 0.725; the pass-7 reviewer's judgement). The last two are the final `local_bump_review` list. |
| 4+ | P7-DOCS-02 (b) C23 duplicates | **Yes** | stage `dup7`: the 3V3 F.Cu hop (27.35, 44.25) -> (29.9, 43.625) (incl. its 0.206 mm piece) and the 3V3 In2 run (30.63, 31.34) -> (32.33, 33.04) deleted; all four vias stay in the 3V3_In2 plane (asserted); the stage splits 3V3's track-only groups by design (`SPLIT_OK`, groups with the pours unchanged, asserted). DC: L1.2 -> U1:27 6.85 -> 7.07, -> R164:1 12.50 -> 12.66 mOhm. |
| 5 | Silkscreen | **Yes** | `r7_post.py`: `label_near` places a part's legend within 6 mm of its courtyard (both angles, bottom face first); used for the J124 fuse notes, J1's, J122's and the J2 / J9 pin tables. "J124: 5A FAST / 2S" B.SilkS x 12.2-13.9, y 97.4-112.9 beside J124 (was 65.7 mm away at the RF strip); "J124 2-FUSE-1: ARM LAST" F.SilkS x 2.9-4.6, y 80.4-101.6 (was 16.0 mm away); J122's row 19.7 -> < 6 mm; J2's rows 10.8 / 6.6 -> < 6 mm. R6's "UART 3V3 / RX-TX AT MODULE" deleted. New gated check `tools/check_r7.legend_subjects` (start board: 5 far legends; final: 0) + test. Labels 35 -> 34; hidden designators 90 -> 90 (newly hidden R121, R123, U13; newly visible C151, R157, TP88: the M3_R7 hidden list needs updating). |
| 6 | C1 IPC-2152 (bounded) | **Partly** | stage `necks7`, no part moved: **RAW_ACT** C86.2's GND via (18.975, 83.85) and its track out of the neck (C86 keeps its thermal joint to GND_F, J122.3 2.4 mm away; the zone notch stays, it keeps RAW_ACT off the pyro block); **ACT_FET_S** pour west edge 1.3 -> 0.6 (only a GND edge strip was there); **BAT_IN** six 0.6/0.3 mm vias stitching R6's unused F.Cu crossbar (232 mm2, joined before only through J1.1's barrel) to In2 (each ring inside both fills, asserted). Necks and rises in §4. |

## 2. `route_check` counts (final tool unless noted)

| | Start board | **Final board** |
|---|---|---|
| F7's tool | 323 instances, 0 failing, 43 allowlisted, 30 leftovers | — |
| F8's tool: instances (critical) | 337 (233): 7 failing (3 via_on_track, 4 local_bump), USB_LIMITED bump unlisted | **326 (224), 0 failing, 45 allowlisted, 29 leftovers**, 0 stale / out-of-date / unrecorded, 0 removable alt_audit exceptions |
| local_bump / via_on_track | 5 / 3 (+6 in fill) | **1 (allowlisted) / 0** (+6 in fill) |
| chain_detour / pour_net_hop / tiny_jog / critical_via_no_gnd | 8 / 5 / 2 / 9 | 9 (+3V3A hop) / 5 / 2 / 9 |
| detour / extra_vias | 22 / 27 | 21 / 27 |
| info changes | | passes_through_pad 9 -> 8 (R180.1), u_turn 23 -> 22 (CAM_FAULT_N), short_layer_hop 20 -> 18 (ACT_EN, 3V3 x2 gone, BAT_IN split +1), power_via_no_gnd 35 -> 34 (USB_LIMITED via (17.925, 83.15) now without a GND via within 1.5 mm after C86.2's via left; two 3V3 vias gone), extra_bends 34 -> 35 (3V3A x 35.61 run, BUZZ_DRV; one 3V3A gone) |
| `--bumps-all` review list | — | VLOGIC_SENSE, BAT_SW_SOURCE (both judged, above) |

**Allowlist 43 -> 45:** + `chain_detour 3V3A B.Cu (35.5, 76.54)` (2.505 mm), + `local_bump USB_LIMITED B.Cu (33.1, 26.15)`
(R105.2 GND isolation, measured); A34 14.368 mm + new reason; VLOGIC extra_vias 66.97 -> 66.37 mm.
**Leftovers 30 -> 29:** - CAM_5V_SENSE detour; CAM_FAULT_N detour / extra_vias 95.07 -> 92.46 mm; SERVO2_OUT 37.07 ->
34.94 mm with a new reason. `ROUTE_FIGURES` updated accordingly.

**Pass-2 `scan.py`** (unchanged, vs R6): **918 (559) -> 904 (549)**: chain_detour 50 -> 47 (critical 30 -> 30: the
whole-run measure still sees A34 and the 3V3A hop), dogleg 137 -> 134, right_angle_corner 43 -> 40, short_layer_hop 20 ->
18, passes_through_pad 9 -> 8, via_pair_close 23 -> 22, u_turn 23 -> 22, short_segment 28 -> 27, pad_end_offcentre 209 ->
208; up: extra_bends 34 -> 35, off_angle_rounding 27 -> 28 (1 nm `FromMM` truncation, as F7 noted; `route_check`
off_angle 0).

## 3. Electrical evidence

- **DRC / connectivity:** DRC 0, unconnected 0, parity 0, ERC 0; every stage keeps pad groups with the pours (asserted;
  `dup7` splits only 3V3's track-only groups, asserted). GND F/B pieces: no via-less piece; single-via 34 -> 32; GND_F
  43 -> 41 pieces. Pyro: ARM1_SENSE only split at R180.1 (no copper moved); no PYRO1_* copper changed; `m3.kicad_dru`
  untouched; `check_actuators` OK. Nearest new copper to a pyro net: 3V3A 0.212 mm from PYRO1_CONT's via (35.78, 60.65)
  (was 0.212 / 0.208 on the bulge); a short reads "continuity present" on the ADC (sense node at 3.3 V; Inference: not a
  fire path, gates defined off).
- **New copper gaps** (`newgap.py`, every added track / via, < 0.25 mm): 0.169 CAM_FAULT_N – SERVO4_MCU In2 (R6 geometry
  +7 um), 0.171-0.172 SERVO2_OUT – 3V3 via (21.9, 96.125) (as before), 0.172 VLOGIC – C99.2, 0.173 3V3 – CAM_RX_WIRE via,
  0.175 3V3 – RAW_PROTECTED via (37.85, 54.7) / VLOGIC – D122.2 / CAM_5V_SENSE's 0.182 – VLOGIC_SENSE, 0.191 IMU_INT1 /
  CAM_5V_SENSE, 0.201 3V3A hop – GND via, 0.212 3V3A – PYRO1_CONT via, 0.225 / 0.230 / 0.231 / 0.235 others. All >= the
  0.15 mm rule. 3V3 – RAW_PROTECTED short: RAW_PROTECTED (to 8.4 V) onto 3V3 (overvoltage; B.Cu, tented via; Inference:
  E-test screens it).
- **Critical reference** (`tools/critical_reference.py`, start -> final): **0 lost / 0 new**, R6 method (69,190
  referenced) and extended (168,254). R6 (+18) -> final: 603 / 882 and 2,312 / 4,325, identical to F7's. (Build #1 lost
  465 QSPI_NCS samples to the LED_RED straightening and a dev build 179 QSPI_IO2 samples to a SERVO2_MCU redraw; both
  reverted, and `bump_audit` now refuses such redraws.)
- **DC** (`tools/dc_solve.py`, 0.1 mm, mOhm, start -> final; `f8/dc_start`, `f8/dc_final`):

  | Path | Start | Final |
  |---|---:|---:|
  | RAW_ACT Q121:5-9 -> J122 (7.7 A) | 3.98 | **3.74** (peak 5.78 A/mm, arm under J122) |
  | RAW_ACT -> J124:2 / -> R177:1 | 1.50 / 86.57 | 1.50 / 86.57 |
  | BAT_IN J1:1 -> Q120:5-9 (7.7 A) | 4.58 | **3.03** (ACT_EN 3.90, crossbar vias; In2 peak 6.13 -> 4.72 A/mm) |
  | ACT_FET_S Q120 -> Q121 (7.7 A) | 1.36 | **1.19** |
  | BAT_IN J1:1 -> U9:5 / C89:1 -> U9:5 / C95:1 -> U9:5 | 15.18 / 7.05 / 5.60 | **13.64** / 7.05 / 5.60 |
  | CAM_5V U13:1 -> R104:1 | 24.37 | **19.52** |
  | VLOGIC U11:1 -> C99:1 | 7.41 | 7.41 |
  | 3V3 L1:2 -> U1:75 / FB31:1 / U1:100 | 15.64 / 14.66 / 73.46 | 15.62 / **12.88** / 73.63 |
  | 3V3 L1:2 -> U1:27 / R164:1 / C100:1 | 6.85 / 12.50 / 77.98 | 7.07 / 12.66 / **74.81** |
  | 3V3A U4:5 -> C31:1 / U4:8 -> C31:1 | 5.84 / 3.32 | 5.86 / 3.32 |

## 4. C1: neck widths and IPC-2152 estimate (equipotential cuts, `f8/dc_ipc.py`; reproduces the records' 0.05 mm necks on the start board exactly)

| Path, layer | Start neck (0.05 mm) | **Final neck** | Final place | Median cut | dT at 7.7 A, neck (Brooks & Adam baseline / with plane + FR-4 credit, Inference) |
|---|---|---|---|---|---|
| RAW_ACT, F.Cu | 2.18 mm at C86.2's via / notch | **3.00 mm** | the arm under J122 (21.55-24.45, y 80.6-81.0), between J122's GND and signal pin columns | 5.31 -> 5.64 | 55 -> **38 °C** / 25 -> 18 °C |
| ACT_FET_S, B.Cu | 2.15 mm at C120.2 | **2.65 mm** | Q120's source row (2.75-5.3, y 94.6-95.0), between Q120.4 (ACT_GATE) and R120 | 2.65 -> 3.07 | 56 -> **44 °C** / 26 -> 20 °C |
| BAT_IN, In2 | 3.71 mm beside J1.2 | **3.82 mm** | the In2 arm (7.25-13.45, y 96.6-99.4), where ACT_GATE's In2 run (1.1, 93.9)-(7.7, 100.5) crosses it | 5.80 -> 7.98 | 31 -> **30 °C** / 20 -> 20 °C |

Median rises: 20 -> 19, 44 -> 37, 19 -> 13 °C. 0.1 mm grid: 2.02 -> 2.95, 2.10 -> 2.64, 3.61 -> 3.66 mm. One RAW_ACT
cut at 97 % of the drop (0.5 mm, a contour round Q121's via field) is not counted, as the records' "via fields not
covered". **Stopped there:** RAW_ACT's arm cannot widen between J122's pin columns, and the notch protects the pyro block;
ACT_FET_S is now set by Q120's gate pad and R120 (ACT_GATE); BAT_IN by ACT_GATE's In2 crossing (moving actuator gate
routing was out of scope). P1-9 (>= 10 mm) stays unmet; no requirement sets the allowed rise (owner).

## 5. Gate and tests (final board `c872a3d3…`)

```
DRC violations 0  unconnected 0  schematic parity 0  ERC 0
metadata / 3D model audit: OK
silkscreen outside the board outline (46.00 x 118.00 mm): 0 stroke points
R7 CAD contract: OK
routing hygiene: 0 failing, 45 allowlisted, 0 stale allowlist entries, 0 out-of-date no-GND reasons, 29 leftovers recorded (0 unrecorded, 0 stale), 0 out-of-date route figures, 0 removable jog / staircase / short-segment / chain-detour exceptions, 1 removable local bumps on critical nets (82 bump windows searched): OK
actuator safety contract: OK
fit check: OK (CAD envelopes only)
```
(`tools/check.sh` exit 0.) Tests (KiCad Python): check_shell 2, dc_solve 3, fab_validation 23, fit_check 23,
maze_clearances 10, procurement 15, r6_check 17, **r7_check 35** (+1), **route_check 50** (+5): 178 OK;
quality_audit 21 OK under KiCad Python and python3 (run without `-I`); test_r5_repair 1 error, the known
`routing_lands_spacing`.

**Fab:** `tools/export_fab.py` regenerated the package; BOM and CPL byte-identical to F7's; manifest bound to
`c872a3d3…` (`verify_manifest` 5 outputs OK); `jlc_orient.py --verify-cpl`: 92 top + 119 bottom rows, worst 0.491 mm, no
errors. BOM unchanged, so stock / cost were not re-queried. Renders `r7_top.png` / `r7_bottom.png` regenerated (984 x 2184,
`kicad-cli pcb render --side top|bottom -w 1016 -h 2208 --quality high`).

## 6. For the records (docs agent)

- Deviation list: A34 (14.37 mm, new reason), A33 (66.37 mm), new A entries for the 3V3A hop chain_detour and the
  USB_LIMITED local_bump; B7 deleted; B9 (CAM_FAULT_N) 92.46 mm; B23 34.94 mm and new reason; C1 (§4 numbers, the three
  reworks, where each neck now sits); C15 (+ SERVO4_MCU – RAW_PROTECTED via 0.192 mm with its failure mode; 3V3A hop
  0.200 mm, not 0.169 / 0.34; 3V3A – PYRO1_CONT 0.212 mm; 3V3 – RAW_PROTECTED 0.175 mm); C17's GND (36.4, 76.54) note
  (copper unchanged since pass 6, P7-04); C21 / Part F: the GND via (6.85, 40.5) and five other GND vias on track bodies
  inside their own fill are `via_on_track_in_fill` (information); Part F's via_pair_close sentence (the 3V3 pair is gone;
  BAT_IN (9.725, 35.525) / (9.2, 36.05) is now a split run, 0.74 mm hop); C23 (3V3 hops gone, the 3V3A hop now an
  allowlist entry, the CAM_5V doubling stays); C24 (ARM1_SENSE resolved by the split, not the records' redraw); C25
  (CAM_FAULT_N / I2C1_SDA done; **LED_RED not removable**: QSPI_NCS reference); C26 done; the owner summary's
  "Removable but not removed" list is now empty except the judged VLOGIC_SENSE / BAT_SW_SOURCE / SERVO2_MCU items.
- REQUIREMENTS M2 "what the gate enforces": add `via_on_track`, `local_bump` (critical nets, strict redraw test incl.
  the reference rule), the alt_audit same-heading rule and its true edge model, and `check_r7.legend_subjects`.
- M3_R7: BAT_IN_B notch, ACT_FET_S_B outline, crossbar vias, C86.2's via removal, pour trims 22 -> 23, hidden
  designators (R121, R123, U13 hidden; C151, R157, TP88 visible), the UART legend's removal, DC table (§3), necks (§4),
  board SHA.
- Not done: owner acceptance; a review pass on `c872a3d3…`.

## 7. Files changed by F8

`m3_design/r7_polish.py` (stages `bumps7`, `v3pair7`, `acten7`, `arm1_7`, `tidy7`, `sense7`, `bat_via7`, `v3a_hop7`,
`bat_in_b7`, `dup7`, `review7`, `necks7`; `TRIM_EXPECTED`, `SPLIT_OK`, docstring), `m3_design/r7_post.py`
(`label_near`, legends), `m3_design/r7_build.sh` (comments), `tools/route_check.py`, `tools/test_route_check.py`,
`tools/check_r7.py`, `tools/test_r7_check.py`; `m3_design/assembly_review/m3.kicad_pcb`; `fab/m3_gerber.zip`,
`m3_assembly_{top,bottom}.pdf`, `m3_fab_manifest.json` (BOM / CPL rewritten byte-identical); `r7_top.png`,
`r7_bottom.png`; this file and `fix7_F8_progress.md`.
