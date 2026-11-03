# R7 review pass 2: hand redraw of the displaced R6 nets (F2 handoff)

Fix agent F2 (board, `m3_design` scripts, fab outputs). Worktree branch `m3-assy-r7`, uncommitted, on R6 commit
`3b215ba`, on top of F1's state (`fix2_F1_handoff.md`). Nothing committed, pushed or opened as a PR. I did not edit
`docs/*.md`, `STATUS.md` or `AGENTS.md`; §9 lists what the records need. Scope: RG-01..RG-04, RQ-04..RQ-06 and
REGRESSION-05, plus the QSPI reference regression my first redraw caused (§3).

**Final board SHA-256 `0eceb7702d08591c6ff11dc0e71326220246f09f08c0e032544ff2d1a2828904`** (F1:
`9371d0376d37…5047`). Two consecutive `m3_design/r7_build.sh` runs from the SHA-checked R6 board gave this same file,
and the saved board is that file. Schematic untouched (`m3.kicad_sch` `47057f7d97c7d748…`, as F1).

## 1. How the board is built now

`r7_build.sh`: `r7_pcb.py` → `r7_route.py` → `r7_rework.py` → `r7_post.py` → `tools/check.sh` (unchanged order).

- **The grid-router replay is retired.** `r7_reroute_session.json` is deleted. `r7_route.py` no longer has
  `--search/--order/--session` or the router/replay code (`reroute`, `replay_session`, `record_session`, `_connect`,
  `_force`, `_dedupe`, …). Its stage `redraw` calls the new **`m3_design/r7_redraw.py`**, and a new stage `finish`
  asserts that DRC finds no dangling R6 leftovers of the displaced nets (0) and gives GND islands a via
  (one: `(19.55, 27.05)`, the same via F1's board has).
- **`r7_redraw.py`** holds every displaced connection as explicit segment and via lists, in stages `orphans`,
  `bat_ilim`, `buzz_drv`, `bat_fault_n`, `cam_uart`, `leds`, `pullpin`, `pullpin_ext`, `vlogic_sense`, `bat_sw`.
  It runs on the board as `clean` + `stitch` leave it. Deletions match exact end points (0.6 µm, one to one) and
  assert the count, so a changed upstream board stops the build. New segments are asserted 0/45/90° and placed on
  rounded nm (not truncated). One width per net: 0.15 mm signals, BAT_ILIM 0.2 mm as R6, 3V3 0.25 mm as R6.
  Run log: 153 R6 items removed, 200 tracks/vias drawn.
- **`r7_rework.py`**: F1's `ilim`, `fault` and `buzz` stages moved into `r7_redraw.py`, with F1's geometry kept
  (BUZZ_DRV ≥ 1 mm from QSPI_IO1, off USB_DP's In2; BAT_FAULT_N In2 x 12.3 west of QSPI_IO0; TP89 on the bottom
  beside R84). `fb31` no longer deletes the old In2 3V3 U-turn; `vlogic_sense` does, before VLOGIC_SENSE crosses
  its place. Other stages are unchanged. Two of its searched GND vias land elsewhere because the copper around them
  changed (§7).
- `r7_build.sh`: comments only.

Files changed by me: `m3_design/r7_redraw.py` (new), `r7_route.py`, `r7_rework.py`, `r7_build.sh`;
`r7_reroute_session.json` (deleted); `m3.kicad_pcb`. Also `fab/m3_gerber.zip`, `m3_assembly_{top,bottom}.pdf` and
`m3_fab_manifest.json`, regenerated with `tools/export_fab.py` and bound to the final board.
`m3_bom_jlc.csv` and `m3_cpl_jlc.csv` are byte-identical to F1's, so `stock_check.json` and `cost_check.json`
still apply. `r7_top.png` and `r7_bottom.png` were re-rendered as F1 did (`--quality high --floor -w 1016 -h 2208`,
984 × 2184).

## 2. Changes per finding

All figures are measured on the final board. Lengths are copper centre-line lengths. "Path" is the pad-to-pad
shortest copper path.

| Finding | Fixed? | What was done (final board) |
|---|---|---|
| RG-01 / RQ-04 (PULLPIN) | Yes | One route U1.8 → F.Cu escape → via (35.17, 56.5) → In2 north beside SERVO1_MCU and past NRST's via → via (33.93, 35.85) → F.Cu into D122.3 from the south. It joins R6's D122.3/R160.2/R161.2/C160.1 tree, which is left as R6 drew it. No copy beside it, no overlap, no acute joint, no loop. The R6 dead end inside D122.3 is removed, and so is C160.2's GND trace that crossed the entry (the pad keeps its pour; the via stays as a stitch). Path U1.8→D122.3 **33.0 mm** (pass 2: 46.5 mm, 1.74×). Net 39.9 mm, **2 vias** (R6 45.9 / 2; pass 2 55.0 / 6) |
| RG-02 / RQ-05 (BAT_ILIM) | Yes | U9.9 → R84.1 is one 0.2 mm link that enters R84.1 square at its centre. TP89's branch tees off it at (9.875, 37.05): 0.2 mm, via (9.3, 37.05), B.Cu to TP89 (bottom, (8.1, 33.6)). No copy, no fold-back, no slot or loop, one width. Branch 4.5 mm; net 9.3 mm, **1 via** (pass 2 36.8 mm / 4 vias) |
| RG-03 / RQ-06 (other replayed nets) | Yes, except CAM_MCU_TX's length | Every replayed net is redrawn from explicit geometry (table §5). On the redrawn nets the scan finds no acute angle, hairpin, U-turn, staircase, tiny jog, overlap, duplicate, crossing without a node, off-angle rounding, collinear-unmerged joint or segment under 0.1 mm (one forced 0.2 mm segment, §4). LED_RED no longer runs under U1 or U-turns: **62.7 → 32.6 mm (1.46×)**. LED_YEL has **3 vias (was 6)**. VLOGIC_SENSE U1.17→R60.2 is **18.8 mm** (pass 2: 31.7 mm, 2.01×), 3 vias, no hairpin. BAT_SW_RETURN's hairpin and east F.Cu hop are gone; BAT_SW_SOURCE's loop east of its crossing is gone. **CAM_MCU_TX is still 65.6 mm (2.66×)**; see §8 |
| RG-04 | Yes | Removed: the floating GND F.Cu chain from D131.2 to C180.2 (4 segments); the GND stubs of C171.2, D131.6 and D130.2/C179.2 into the pour (their stitching vias stay); the dead In2 3V3 branch (17.57–15.0, 34.0–43.4) and the In2 link it left between two plane vias. The D130.5 junction (8–30 µm pieces, an acute T) is one Y. C179.1's corner and U1.11's via triangle are one 0.25 mm run. The R205.1 star (acute angle, 2–8 µm pieces) and its F.Cu path with 3 vias are gone: C90's 3V3 via reaches the FB31 lobe of the In2 plane directly, In2 0.2 mm (38.17, 37.82)→(38.0, 29.61)→(35.73, 27.34). `finish` asserts that no R6 leftover of the displaced nets is dangling |
| RQ-04 (BAT_SW_RETURN hook) | Yes | The R6 hook (11.2, 44.825)→(11.9, 44.125) and the R7 spur are gone. RETURN enters from its via (14.1, 46.425) with one F.Cu run to (9.7, 44.825) |
| RQ-05 (rest) | Yes | The PULLPIN 1.45 mm overlap and loop are gone. Micro-segments are gone: CAM_MCU_TX 3/5 µm, PULLPIN_EXT 30 µm, BUZZ_DRV 50 µm plus R6's doubled R162.1 stub, BAT_ILIM 25 µm. No segment under 0.1 mm remains on those nets. GNSS_RESET_N has no 0.4 mm stub; all its segments are 0.15 mm (verified, not my edit) |
| REGRESSION-05 | Yes (route) | PULLPIN_EXT R160.1 → via (33.875, 25.6) → B.Cu between C98 and C94 → via (34.15, 29.8) → F.Cu into J123.1 from the north. **11.1 mm, 2 vias** (pass 2 13.7 mm; R6 5.6 mm). Edge gap from the route's tracks and vias, every layer, including zone fills (KiCad shape collision, binary search): **CAM_5V 0.73 mm** (B.Cu), **VLOGIC_SENSE 0.72 mm** (F.Cu), ≥ 1.19 mm on the other layers. Not changed: J123.1's own pad is **0.20 mm** from CAM_5V B.Cu (34.23, 32.2)→(35.53, 33.5), 0.4 mm. That copper and the micro-segments at its end are the same on F1's board; it is a pad gap, not route copper. Decision for the owner or the next pass |

## 3. QSPI reference (R6 method, `tools/critical_reference.py`, R6 board moved +18 mm)

My first redraw ran three straight In2 lanes (LED_YEL y 41.2, LED_RED y 41.7, RX y 42.25) under QSPI_NCS's and
QSPI_IO3's B.Cu diagonals. On that board, NCS lost 404 samples and IO3 239 (lost total 1,127). Final geometry:

- **QSPI_NCS.** LED_RED and LED_YEL run as two In2 lanes 0.3 mm apart round the north of QSPI_NCS's via:
  (24.75/24.45 up, a 45° rise to y 39.15/38.85, down at x 27.35/27.65, east at 41.7/41.2 to their existing vias).
  They no longer pass under QSPI_NCS. CAM_MCU_RX crosses QSPI_NCS on R6's LED_YEL crossing (y 42.35; R6 42.25).
  It then hops to F.Cu on R6's LED_YEL hop (25.85 → 28.25) and returns to In2.
- **Why RX hops (measured).** Without the hop, the plane inside the LED bend is enclosed by the LED lanes and RX.
  Island removal then drops it, and NCS loses **442** samples (trial board, DRC clean). With the hop, NCS loses 38.
- **QSPI_IO3.** The LED vias moved to x + y = 63.7 (0.64 mm from IO3's centre line), so their In2 openings miss it.
  The RX via went from (21.15, 42.55) to (21.35, 42.35) for the same reason. TX now crosses IO3 at 90° where R6's
  TX did, from a via at (20.45, 43.4). That spot keeps a channel open from the plane west of the lanes to the
  south, and leaves room for RXEN's GND via within 1 mm.
- R6's GND via (26.45, 42.85), at the end of its B.Cu run, moved 0.05 mm south to (26.45, 42.9) to clear the RX hop.

| | Pass 2 | F1 | F2 first redraw | **F2 final** |
|---|---|---|---|---|
| R6-referenced samples lost on the candidate (R6 method) | 1,427 | 557 | 1,127 | **524** |
| … QSPI_IO0 F.Cu (R6 path R7 abandoned) / IO1 B.Cu / IO3 F.Cu | | 410 / 15 / 74 | 410 / 15 / 59 | 410 / 15 / 59 |
| … QSPI_IO1 F.Cu / IO2 F.Cu | | 12 / 32 | 0 / 0 | 0 / 0 |
| … QSPI_IO3 B.Cu / QSPI_NCS B.Cu | | 0 / 14 | 239 / 404 | **2 / 38** |
| Candidate samples unreferenced where R6 was referenced | 1,905 | 820 | 1,390 | **787** |
| Extended set: lost / candidate-new | 2,085 / – | 557 / 2,604 | – | **524 / 2,571** |

The 38 NCS samples are its corner at (24.45–24.68, 42.58–42.75), beside RX's lane opening. The 2 IO3 samples are at
IO3's own via. 410 + 15 + 59 are as F1 left them. IO3 F.Cu 74 → 59: F1's extra samples were at x 22.4, y 38.8, beside F1's TX via (21.85, 38.85), which is gone. IO1/IO2 F.Cu 12/32 → 0: those were beside the replayed LED_YEL vias (24.0, 42.3) and (25.8, 42.3), also gone.

## 4. Pass-2 routing scan, before and after (reviewers' `scan.py` categories, R7-era instances)

| Board | All R7-era | Redrawn 13 nets | GND / 3V3 | Other (interface, RF; not in my scope) |
|---|---|---|---|---|
| Pass 2 | 364 | – | – | – |
| F1 final | 269 | 138 | 22 | 109 |
| **F2 final** | **166** | **48** | **9** | 109 |

Redrawn nets + GND/3V3 by category, F1 → F2: pad_end_offcentre 27 → 4, dogleg 20 → 28, short_segment 15 → 1,
pad_entry_diagonal 12 → 0, chain_detour 11 → 4, short_layer_hop 9 → 3, net_length 8 → 8, acute_at_padvia 7 → 0,
end_in_zone_only 6 → 0, off_angle_rounding 6 → 0, u_turn 6 → 0, staircase 6 → 0, acute_angle 5 → 0,
collinear_unmerged 4 → 0, via_offcentre_joint 3 → 1, side_by_side_overlap 3 → 0, crossing_without_node 3 → 0,
tiny_jog 3 → 0, passes_through_pad 2 → 0, extra_bends 2 → 6, right_angle_corner 1 → 2, width_change_free 1 → 0.

What is left (57), and why:
- **dogleg 28.** The scan flags every A-B-A heading triple. All 28 are above its own tiny-jog limits (middle
  segment ≥ 0.5 mm, lateral offset ≥ 0.25 mm; tiny_jog 0). They are deliberate offsets round obstacles:
  - the LED bend round QSPI_NCS (4);
  - TX's IO3 crossing, its u1fan joint and R6's In2 north (3);
  - BUZZ_DRV round C96 and to the left edge (4, F1's path);
  - BAT_SW_RETURN/SOURCE band lanes (5), PULLPIN (3), PULLPIN_EXT (2), VLOGIC_SENSE (2), BAT_FAULT_N (1);
  - 3V3 (3: the C179.1 joint, F1's FB31 feed, C90's In2 link);
  - GND (1): the R6 B.Cu run to the via moved 0.05 mm.
- **extra_bends 6.** BAT_SW_RETURN's long F.Cu and In2 runs (4, inherent to its 160 mm path; R6 164 mm),
  LED_RED's F.Cu into R32.1 through J123's gap (1), CAM_MCU_TX's B.Cu into U12.5 (1).
- **short_layer_hop 3** (all forced, measured):
  - CAM_MCU_RX F.Cu 2.4 mm keeps the plane under QSPI_NCS joined (§3).
  - LED_RED B.Cu 2.35 mm crosses CAM_5V_SENSE's F.Cu (x 32.05) and VLOGIC_SENSE's In2 (x 32.44) at the same place.
  - BAT_SW_RETURN In2 1.3 mm (15.0 → 16.3, y 37.725) crosses QSPI_IO0 F.Cu (x 15.6) and RAW_PROTECTED B.Cu (x 15.7)
    at once; R6 had the same hop.
- **chain_detour 4.** The two LED In2 bends (12.7 / 9.1 mm and 11.6 / 8.1 mm) add 3.5–3.7 mm each; that is the price
  of the 404 QSPI_NCS samples in §3. Also BAT_SW_SOURCE's B.Cu under RETURN, and the 3V3 run from the D130.5 Y to
  U1.11's via (R6 parts' joint).
- **net_length 8.** Per-net ratios in §5.
- **pad_end_offcentre 4.**
  - BAT_FAULT_N ends 0.075 mm off R89.2's centre: U9.4 and R89.2 are 0.075 mm apart in x, and one straight run
    cannot centre on both.
  - C84.2 GND ×3: step-B U1-side surgery, not touched.
- **right_angle_corner 2.**
  - BAT_ILIM into R84.1's centre (RG-02 asked for a square entry).
  - BAT_SW_SOURCE at R80.2.
- **short_segment 1.** BAT_SW_SOURCE In2 0.2 mm at its via (43.36, 36.4). The direct diagonal comes 0.095 mm from
  CAM_5V's via (43.25, 35.625).
- **via_offcentre_joint 1.** 3V3 (27.9, 62.74), 0.051 mm; not my copper.

## 5. Redrawn nets (copper length / vias; path / octile for two-pad nets)

| Net | R6 | Pass 2 | F2 final | Path / octile (ratio) |
|---|---|---|---|---|
| LED_RED | 42.0 / 6 | 62.7 / 2 | 32.6 / 3 | 32.6 / 22.4 (1.46×) |
| LED_YEL | 28.8 / 6 | 33.2 / 6 | 36.3 / 3 | 36.3 / 25.2 (1.44×) |
| CAM_MCU_TX | 88.6 / 3 | 70.6 / 5 | 65.9 / 5 | 65.6 / 24.7 (**2.66×**) |
| CAM_MCU_RX | 40.4 / 4 | 40.6 / 4 | 32.8 / 6 | 32.8 / 26.4 (1.24×) |
| PULLPIN | 45.9 / 2 | 55.0 / 6 | 39.9 / 2 | U1.8→D122.3 33.0 |
| PULLPIN_EXT | 5.6 / 1 | 13.7 / 2 | 11.1 / 2 | 11.1 / 9.3 (1.19×) |
| VLOGIC_SENSE | 36.2 / 3 | 43.5 / 6 | 32.6 / 3 | U1.17→R60.2 18.8 |
| BAT_ILIM | 37.8 / 2 | 36.8 / 4 | 9.3 / 1 | U9.9→R84.1 4.75 |
| BUZZ_DRV | 67.0 / 6 | 64.1 / 5 | 59.8 / 3 | 59.8 / 48.3 (1.24×) |
| BAT_FAULT_N | 41.9 / 6 | 42.9 / 6 | 40.0 / 4 | – |
| BAT_SW_SOURCE | 128.6 / 9 | 128.9 / 7 | 129.2 / 7 | 128.7 / 87.3 (1.47×) |
| BAT_SW_RETURN | 164.3 / 9 | 161.5 / 7 | 160.4 / 5 | 160.4 / 76.3 (2.10×) |

CAM_MCU_RX's 6 vias are its two R6 vias at U12, its two lane vias and the 2 hop vias of §3. Before §3 it had 4.

## 6. DC solves (`tools/dc_solve.py`, grid 0.1 mm, 3V3 from L1.2)

| Path | F1 final | **F2 final** |
|---|---|---|
| 3V3 L1.2 → U1.75 | 13.77 mΩ | 13.99 mΩ |
| 3V3 L1.2 → FB31.1 (radio PA feed, RQ-03) | 12.22 mΩ | **13.60 mΩ** |
| 3V3 L1.2 → FB30.1 | 4.83 mΩ (F1 handoff) | 5.00 mΩ |
| 3V3 L1.2 → U1.27 | 5.80 mΩ | 6.20 mΩ |
| 3V3 L1.2 → U3.8 (QSPI flash) | 6.16 mΩ | 6.34 mΩ |

Every 3V3 path rose by 0.17–0.40 mΩ, and FB31's by 1.38 mΩ (+11 %; pass 2 was 29.3 mΩ). At 0.1 A, that is
0.14 mV more drop. Inference, not separated by a solve: the In2 lanes split the plane (§7). The largest single cause
is likely the D122.2 pocket, which on F1's board carried current alongside the path to FB31's lobe. BAT_IN,
RAW_ACT and the actuator paths share no copper with the redrawn nets; I did not re-solve them.

## 7. Side effects in the other stages and outputs

- `r7_rework.iface_returns` (F1's greedy GND-via search) places two vias differently because my copper changed:
  - RXEN's via (21.2, 44.45) now has its GND via at **(20.5, 44.15), 0.76 mm** (F1: (20.3, 43.65), 1.20 mm).
  - The NRST pour via moved from (35.7, 50.15) to **(35.75, 50.35)**: 1.84 → 1.93 mm from its two GND pads.
  - The other searched vias are where F1 had them: QSPI_IO0 (13.65, 44.6) and (15.75, 50.1); D9.2 (19.65, 30.55);
    C80.2 (6.3, 53.05); RXEN band (20.0, 27.45).
- **3V3 In2 plane:** 7 fill polygons (R6 11, F1 5). The main polygon is 436 mm² (F1 505), with 11 vias. Three pieces
  are separate, as they were on R6, and each is fed through its own vias; F1's board had the first two joined to the
  main polygon. DRC unconnected 0.
  - The R87/R88 area with the pocket round RXEN's via, x 22.5–28.7, y 36.3–41.0, 10.3 mm², 2 vias: (26.4, 36.6),
    (28.33, 40.4). R6 had this area, together with the plane west of it, as one separate 23.6 mm² piece on the same
    two vias. On the final board, the LED bend and the LED_YEL via close it off. No QSPI B.Cu track crosses it
    (B.Cu listing of the area); QSPI_IO3 ends at its via on the piece's west edge.
  - D122.2's pocket, x 29.7–34.5, y 30.2–37.0, 17.6 mm², 2 vias. It was separate on R6 too (35.5 mm²). On F1's
    board it held the R205 star's via (32.57, 35.0) and was part of the main polygon. On this board, VLOGIC_SENSE's
    In2 trunk and its diagonal to C60 (x 32.44, then (32.44, 34.2)→(35.04, 31.6)), with PULLPIN's In2 (x 33.93),
    bound it (seen on the fill render; not traced polygon by polygon).
  - x 29.1–32.5, y 51.0–56.5, 7.5 mm², 1 via (31.1, 54.5), the same 7.5 mm² piece R6 had.
- **Hidden designators: 88** (F1 92). Newly hidden: C14. Newly shown: C21, C24, R170, R60, R61. Full list, for the
  `M3_R7.md` silkscreen line: C100 C126 C127 C128 C13 C14 C15 C150 C151 C160 C25 C30 C302 C303 C305 C31 C311 C312
  C313 C314 C60 C7 C71 C74 C8 C88 C90 C92 C94 D120 D123 D30 D31 FB31 J123 L30 LED1 Q32 R10 R101 R102 R103 R104 R105
  R11 R125 R126 R127 R128 R129 R130 R131 R133 R156 R161 R162 R163 R164 R173 R178 R180 R301 R302 R303 R304 R311 R316
  R32 R62 R64 R74 R75 R8 R86 R88 R91 TP70 TP71 TP73 TP74 TP82 TP83 TP87 TP90 U11 U13 U7 Y1.
- **Not touched:** pyro, arming and actuator copper and rules; `m3.kicad_dru`; `check_actuators.py`. CH1 pyro copper
  and the pyro sentinel pins (no net) are as F1 left them; the actuator safety contract passes.

## 8. Residuals (not fixed, with reasons)

- **CAM_MCU_TX 2.66× (RQ-06 target ≤ 1.5×).** TX still goes north round U3, along the band and down the east
  (65.6 mm; R6 88.6). The direct way east is the corridor between U1's north row and the QSPI flash. It holds 3 In2
  lanes at most (LED_RED, LED_YEL, RX), and those lanes are already bent to keep QSPI_NCS/IO3 referenced (§3).
  Inference: a shorter TX needs a different U1 pin or a reorganised QSPI fan-out.
- **RQ-02 remainder.** TX's In2 band run at y 24.55 (x 28.55–38.75) still sits under NRST's B.Cu band run, inside the
  In2 GND strip. BAT_SW_SOURCE (In2 y 25.0) and BAT_SW_RETURN (In2 y 26.325) fill the band south of it. I found no
  free In2 lane for TX there.
- The scan items in §4 that are forced or deliberate. J123.1 pad to CAM_5V 0.20 mm (§2, REGRESSION-05).
- Not verified: anything physical, signal integrity or ESD coupling (REGRESSION-05's magnitudes were not computed),
  and RF behaviour. The critical-reference counts are the R6 sampling method, not a field solve.

## 9. For the records (docs agent / next pass)

- **Board SHA** `0eceb7702d08591c6ff11dc0e71326220246f09f08c0e032544ff2d1a2828904`. `fab/m3_fab_manifest.json`
  binds it; `test_fab_validation` passes.
- **Out-of-date text:**
  - `docs/M3_R7.md` line ~225 ("`r7_reroute_session.json`") and line ~248 ("redrawn by the house grid router").
  - `docs/R7_VALIDATION.md` line ~63 (session file).
  - `STATUS.md` routing line ("then the grid router for what it leaves").

  The 13 displaced R6 connections are now drawn from explicit geometry in `m3_design/r7_redraw.py` (stage `redraw`
  of `r7_route.py`). The session file is gone.
- **`M3_R7.md` silkscreen:** 88 hidden designators (§7 list).
- **Critical-reference record:** §3 table (lost 524; candidate-new 787; extended 524 / 2,571).

## 10. Verification

- `m3_design/r7_build.sh` twice, from the SHA-checked R6 board: identical board both times, and `tools/check.sh` exit 0:
  ```
  DRC violations 0  unconnected 0  schematic parity 0  ERC 0
  metadata / 3D model audit: OK
  silkscreen outside the board outline (46.00 x 118.00 mm): 0 stroke points
  R7 CAD contract: OK
  actuator safety contract: OK
  fit check: OK (CAD envelopes only)
  ```
- Tests, run as scripts with KiCad's Python: check_shell 2, fab_validation 23, fit_check 22, maze_clearances 10,
  procurement 15, r6_check 17, r7_check 28, all OK. quality_audit 21 OK (KiCad Python and python3). test_r5_repair:
  1 error, the known pre-existing `routing_lands_spacing` failure.
- Scan, critical reference and DC solve were run on the final board (§3–§6). The trials behind §3 were done on
  scratch copies with DRC; only the final geometry is in the build.
