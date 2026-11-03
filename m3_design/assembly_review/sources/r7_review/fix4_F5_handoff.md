# R7 fix pass 4, agent F5 (board, tools): handoff

Worktree branch `m3-assy-r7`, uncommitted, on R6 commit `3b215ba`. Start: the fix-pass-3 board, SHA-256
`636a6bdc7234586a659741a3da921335a47197648c29cd9612c8374733847650`. Nothing committed, pushed or opened as a PR. I did
not edit `docs/*.md`, `STATUS.md`, `AGENTS.md`, the schematic, `m3.kicad_dru` or `check_actuators.py`. Running log:
`fix4_F5_progress.md`. Scratch evidence: `<scratchpad>/fx4/` (router searches `det/r1`…`r5` and `rt/`, analyses `an/`,
board-edit snippets `snip/`, dev builds `d1/`, `d2/`, logs `build2.log`).

**Final board SHA-256 `c6fe595cafb91b088ac0b2c812f409f9ca5b86ac45a651102e168b0a5d83c7c7`.** A clean
`m3_design/r7_build.sh` from the SHA-checked R6 board gave exactly this file and exited 0 (its gate passed); my dev
chain (post-hygiene board → `r7_polish` → `r7_post`, `fx4/d2`) gave the same bytes. The saved board is that file. Fab
package regenerated with `tools/export_fab.py` and bound to it (`m3_fab_manifest.json`); BOM and CPL are
byte-identical to fix pass 3 (no part moved), so `stock_check.json` / `cost_check.json` still apply. The renders
`r7_top.png` / `r7_bottom.png` were **not** re-rendered (my kicad-cli settings did not reproduce F4's image size).

## 1. Build chain

`r7_build.sh`'s steps are unchanged (`r7_pcb` → `r7_route` → `r7_rework` → `r7_hygiene` → `r7_polish` → `r7_post` →
`tools/check.sh`); every fix-pass-4 board change is in `m3_design/r7_polish.py`. `r7_hygiene.py`'s output does not move:
its `gnd_vias` legality became a class (`GndFit`, same tests) plus `gnd_spots` (the 0.025 mm search) and a `fine=`
option that only `r7_polish` uses. Verified: the post-hygiene board I rebuilt (`fx4/hyg.kicad_pcb`) run through the
*old* `r7_polish` and `r7_post` gave the start SHA `636a6bdc…` byte for byte. `r7_pcb.py`, `r7_route.py`, `r7_rework.py`
and the router replay (`r7_reroute_session.json`) are untouched (C302's relief is changed late, in `r7_polish`, so the
upstream output does not move; `r7_lib.RF_SOLID_GND` keeps C302 for the upstream "GND via beside the pad" and says so).

`r7_polish` stages, final build (fix-pass-4 changes in bold):

| Stage | Result |
|---|---|
| dead, neck, swd, pyro_corners | as fix pass 3 (40 dead tracks; SWCLK 62.7 mm / 4 vias, SWDIO 53.7 mm / 4) |
| **pyro1_cont** | PYRO1_CONT 29 items (7 vias) → the plane-preserving route, 14 segments, 47.53 mm, 6 vias; GND return vias (35.18, 61.05) 0.6, (40.93, 78.65) 0.6, (28.55, 87.21) 0.5 mm; copper gap to PYRO1_GATE_N 1.080 mm (asserted ≥ 1.0 mm) |
| corners, l1_node, gnd_moves, dead2 | as fix pass 3 |
| **band** | RADIO_NRST's step moved inside its via; RADIO_SCK / RADIO_NSS steps 0.45 / 0.6 mm later |
| **debris** | 10 redraws: LED_YEL_A, SERVO3_MCU, CAM_5V_SENSE, SERVO4_OUT, SERVO2_MCU, CAM_EN, LOGIC_ILIM, I2C1_SCL, SERVO4_MCU, CAM_RX_WIRE |
| **reroutes** | CAM_UART_OE 22 tracks / 6 vias / 44.11 mm → 12 / 4 / 30.68 mm; NRST's J2 branch 15 tracks (3 on In1) / 4 vias → 10 segments / 2 vias |
| **rf_relief** | C302.2 solid → thermal relief |
| **gnd_vias** | `r7_hygiene.gnd_vias(fine=0.025)` on the final signal copper: one GND via, 0.6/0.3 mm at (22.85, 89.63) |
| pour_trim | 21 keep-out rule areas (set regenerated; a pad's relief ring is never kept out); every pad that touched its pour before the stage still touches it (asserted) |
| strip_stitch | 3 GND vias, as before |
| **gnd_vias2** | the GND-via search again after the last copper change: 0 added (asserted) |
| pour_trim2 | 0 |

Board totals: 1,809 tracks (was 1,836), 694 vias (694), 3 tracks on In1 (was 6: NRST's 3 are gone; CAM_TX_WIRE's 3
inherited R6 In1 tracks remain, not in my list — an observation for the next review).

## 2. Per finding

| Finding | Done? | What changed, or why not |
|---|---|---|
| **P4-ROUTING_GEOMETRY-01** (Major) | **Yes** | GND via 0.6/0.3 mm at (22.85, 89.63), 1.309 mm from PYRO1_GATE_N's layer change (23.0, 88.33) (was 1.815 mm); the PYRO1_GATE_N allowlist entry is deleted. The GND-via search now runs again in `r7_polish` after the last signal-copper change (`gnd_vias`, with the fine 0.025 mm pass) and after the strip stitching (`gnd_vias2`, 0 added). New gated check `route_check.nognd_audit`: for every allowlisted `critical_via_no_gnd` it runs the project-legal search (`r7_hygiene.gnd_spots`: `GndFit` = `r7_route.ViaCheck` + bare-TP 1.02 mm, Tag-Connect 0.528 mm, Pyro D 0.52 mm incl. fills, the 7.7 A corridors; 0.6 and 0.5 mm vias; 0.025 mm grid; ≤ 1.5 mm) on the board being checked and fails if a spot exists. On the start board it reports exactly the review's spot (0.5 mm at (22.9, 89.555), 1.229 mm) and nothing else; on the final board 0. Unit test (real search on a synthetic board, with and without a via keep-out). `_NOGND` rewritten: the pass-3 sentence is gone; it cites the gated audit and the slide search. |
| AGENTS §3 instances (task 2) | Partly | **Staircases 4 → 2:** RADIO_NRST (step inside its via; its tiny jog and 0.141 mm short segment go too) and RADIO_SCK (run before the step 1.05 mm) are clean; RADIO_BUSY and RADIO_MISO_MCU stay allowlisted with a measured reason (§4: a 9.4-column lane must keep its row until past the 10.0-column vias, the lane pitch is fixed at 0.4 mm by RADIO_DIO1 and BAT_SW_RETURN, and squaring the east corners collides with the next lane's chamfer — each tried, measured). **Critical layer changes without a GND via: 11 → 10** (PYRO1_GATE_N fixed). For the other 10: the fine search finds no spot (gated audit), and sliding each signal via along its tracks' axis by up to ±0.6 mm in 0.05 mm steps (moved via and dragged tracks checked, then the spot search) opens none (`fx4/snip/slide.py`); the corner vias (RXEN (23.8, 39.45), ARM1_SENSE ×2, MOSI_MCU (9.4, 48.5)) cannot slide without bending a track off 0/45/90; ARM1_SENSE's only spots are in the BAT_IN J1→Q120 7.7 A corridor (unchanged reason). |
| **P4-ROUTING_QUALITY-01 / P4-REGRESSION-01** (F4's open decision) | **Yes** | PYRO1_CONT on the plane-preserving route (§1). Measured on the final board: In2 3V3 island under U1/U4 one piece again, 74.51 mm² with 4 vias (start board: 41.93 mm² / 3 vias + 22.69 mm² / 1 via); PYRO1_CONT copper gap to SPI1_SCK ≥ 2.75 mm (was 0.195 mm over 7.4 mm), no SPI1_MISO / SPI1_MOSI copper within 3 mm on a shared layer; to PYRO1_GATE_N ≥ 1.080 mm on F.Cu (R6's divider pad C127.1, unchanged) and 2.088 mm on In2 (was 0.191 mm); every PYRO1_CONT layer change has a GND via ≤ 1.5 mm (1.112, 0.721, 1.014, 0.728, 0.764, 1.408 mm). No In2 run in a 3V3/3V3A/BAT_IN/RAW_ACT pour (the search blocks them). Pyro rules: DRC 0, `check_actuators` OK; PYRO1_OUT is 0.716 mm away (rule C 0.3). Critical reference: back to 603 (§5). Cost: 6 vias instead of 4 and one 1.8 mm In2 hop (short_layer_hop, information). |
| **P4-REGRESSION-02** | **Yes** | `r7_polish.pour_trim` leaves the ring (pad outline + `route_check.PAD_RING` 0.75 mm) of every same-net pad with a thermal or solid connection out of every keep-out, and asserts that every pad touching its pour before the stage still touches it. New gated category `route_check.pad_pour_cut` (POUR): a pad with a thermal/solid connection, inside its pour's outline, that touches the fill when the board is refilled with its pour-trim keep-outs (`R7_POUR_TRIM_*`) switched off but not as saved (design keep-outs — J2 contacts, IMU/BARO bodies, SMA launches — are intended and not counted). Start board: exactly the review's 5 pads; final: 0. Pour contact (fill within 0.05 mm of the pad), final = pass 3: C7.2 0.060, C150.2 0.060, C30.2 0.015, C31.2 0.030, R64.2 0.030 mm²; zero-contact pads 40, the same 40 as pass 3 (none lost). `pour_finger` now leaves those pad rings out before measuring (a pad's spokes are not a finger): after ring protection the only "fingers" left round C150.2 and C30/C31/R64 were the spokes themselves, with no legal GND stitch spot (0 GndFit spots near C150; none of the 40 nearest near C30 removed the piece). Unit tests for both (+ the design-keep-out case). |
| **P4-REGRESSION-03** | No copper change | SWCLK's B.Cu hop stays: no F/B route keeps its vias ≥ 2 mm from Y1.3 (router, also with In2 and with BUZZ_DRV's copper removed); measured constraints: U1's NE exit between U1.25/U1.26 is the line x+y = 75; SERVO4_MCU's via (25.30, 50.51) needs ≥ 0.72 mm, ARM1_SENSE's In2 run (x 25.88) caps a via at x ≤ 25.36, RAW_ACT_SENSE's via (23.03, 49.3) forces a B.Cu run north of the crystal to y ≥ 49.835, so the only spots, (25.25, 49.75) / (25.3, 49.7), are reachable only by a 0.14–0.21 mm jog; moving SERVO4_MCU's via onto its In2 line is refused by ARM1_SENSE (0.105 mm); BUZZ_DRV then has no path. **Distances (final board):** SWCLK–HSE_OUT copper gap 1.10 mm on B.Cu (via (24.7, 50.95) to Y1.3), 2.20 mm on F.Cu, 2.31 mm on In1/In2; the inherited BUZZ_DRV via (24.15, 50.25) is 1.75 mm from HSE_OUT on B.Cu. **B.Cu GND pour:** 39 → 35 polygons (my reroutes joined pieces south of U1); the crystal/U1 island is unchanged, 133.2 mm² with 27 vias; every piece holds vias. |
| **P4-DOCS-01** (Major) | Partly (board side) | (1) Debris: the 14 non-critical short segments / tiny jogs → 2 tiny jogs (CAM_EN, CAM_FAULT_N), each forced (measured reason in `route_check.LEFTOVERS`); 10 nets redrawn (`debris`). (2) Detours / over-via nets: CAM_UART_OE and NRST rerouted (`reroutes`; NRST no longer runs on In1); every other non-critical detour / extra_vias instance (13 + 19) carries a raster-search result in the new machine-readable `route_check.LEFTOVERS` (34 entries), and the gate now fails if a non-critical detour / extra_vias / tiny_jog / short_segment instance has no entry or an entry matches nothing. (3) Owner acceptance of the allowlist + leftovers: open (the owner's). |
| **P4-RF-03 / P3-RF-02 / P3-DFM-05** | **Yes** (board) | C302.2 back on the house thermal relief (`rf_relief`; contact 0.111 → 0.045 mm², spokes); `check_r7.RF_SOLID_GND` drops C302.2, so `thermal_policy` now requires its relief; its GND via stays. **Decision on D30.2 / D31.2: keep solid.** The RF reviewer's argument holds (the ESD clamp's return inductance matters at the jack; a thermal spoke adds it), while the tombstoning risk is a general-practice inference with no maker figure (pass-3 DFM) and is caught at first-article inspection; the DFM fix asked for that inspection, not for a relief. For the records (docs agent): ORDERING §5 needs "D30, D31, C302 seated flat (no tombstone or skew)". |
| **P4-DOCS-02** | **Yes** | `tools/dc_solve.py` reads each copper layer's thickness and the dielectric stack from the board file's `(stackup …)` block (KiCad 10's Python does not expose the stack-up), raises if it is missing, uses per-layer sheet conductance and mid-plane-to-mid-plane barrel lengths, and prints the stack it used. New `tools/test_dc_solve.py` (3 tests). Results §5. |

## 3. `tools/route_check.py` counts — all (critical) / failing / allowlisted [/ leftovers recorded]

| Category | Start board, F4's tool | Start board, final tool | Final board |
|---|---|---|---|
| staircase | 4 (4) / 0 / 4 | 4 (4) / 2 / 2 | **2 (2) / 0 / 2** |
| critical_via_no_gnd | 11 (11) / 0 / 11 | 11 (11) / 1 / 10 | **10 (10) / 0 / 10** |
| tiny_jog | 13 (5) / 0 / 5 | 13 (5) / 1 / 4 / 2 | **6 (4) / 0 / 4 / 2** |
| short_segment | 9 (3) / 0 / 3 | 9 (3) / 1 / 2 | **2 (2) / 0 / 2** |
| detour | 22 (9) / 0 / 9 | 22 (9) / 0 / 9 / 13 | 22 (9) / 0 / 9 / 13 |
| extra_vias | 29 (10) / 0 / 10 | 29 (10) / 0 / 10 / 19 | 29 (10) / 0 / 10 / 19 |
| pad_pour_cut (new) | – | 5 (5) / 5 / 0 | **0** |
| pour_sliver / pour_finger | 0 / 0 | 0 / 0 | 0 / 0 |
| nognd_audit (new, gated) | – | (PYRO1_GATE_N fails as a plain instance once its entry is gone) | **0** |
| power_via_no_gnd (info) | 36 | 36 | 36 |
| extra_bends / u_turn / short_layer_hop (info) | 33 / 26 / 20 | same | 34 / 25 / 21 |
| pad_end_offcentre / width_change_junction / segment_inside_pad (info) | 89 / 30 / 2 | same | 93 / 30 / 3 |
| **total** | **334 / 0 failing / 42 allowlisted** | 339 / 10 failing / 37 / 12 leftovers unrecorded | **323 / 0 failing / 37 allowlisted / 0 stale / 0 audit / 34 leftovers recorded, 0 unrecorded** |

Information deltas (instance diff, start → final): pad_end_offcentre +3 (PYRO1_CONT into R129.2 0.18 mm off centre,
SERVO3_MCU into D121.4 0.41 mm off, LED_YEL_A's 0.55 mm drop inside LED2.1); segment_inside_pad +1 (that drop);
extra_bends +RADIO_SCK (E 1.05 / NE / E / NE: one segment under 1 mm, so no longer a staircase), +PYRO1_CONT's F.Cu run
east of the IMU, −SERVO4_OUT; short_layer_hop +CAM_UART_OE's 2.7 mm In2 hop, +PYRO1_CONT's 1.8 mm In2 hop,
−CAM_UART_OE's old F.Cu hop; u_turn −NRST (its old J2 approach).

**Pass-2 reviewers' `scan.py` (unchanged), all (critical):** start 969 (595) → final **958 (595)**: staircase 4 → 2,
tiny_jog 5 (1) → 2 (1), short_segment 34 (19) → 28 (19), critical_via_no_gnd 11 → 10, dogleg 151 → 148,
off_angle_rounding 27 → 26, right_angle_corner 56 → 55, u_turn 26 → 25, width_change_at_pad 18 → 17; up: extra_bends
33 (9) → 34 (11), short_layer_hop 20 (8) → 21 (9), pad_end_offcentre 206 → 208, pad_entry_diagonal 170 → 173,
segment_inside_pad 2 → 3 (`fx4/an/base_scan.json`, `d2_scan.json`).

## 4. Final allowlist (37 entries, `route_check.ALLOWLIST`) and non-critical leftovers (34, `route_check.LEFTOVERS`)

Each entry carries its measured reason in the tool; summary:

| Entries | Reason (short) |
|---|---|
| staircase + tiny_jog RADIO_BUSY, RADIO_MISO_MCU (4) | band fan-in: 0.5 mm via rows vs 0.4 mm lanes fixed by RADIO_DIO1 and BAT_SW_RETURN; a 9.4-column lane must keep its row past the 10.0 column (0.475 mm needed); the east chamfers are fixed by the 0.4 mm strip-column pitch; squaring them collides (measured); NRST and SCK fixed this pass |
| tiny_jog QSPI_CLK (22.85, 45.95) | unchanged (straight on: 0.15 mm to the LED_YEL via; a non-tiny step: 0.196 mm to RXEN) |
| tiny_jog + 2 short_segment SW_NODE | unchanged (C7.2/C9.2 gap and U2's vias; every one-bend route collides) |
| critical_via_no_gnd ×10: RADIO_RXEN (23.8, 39.45), RADIO_NRST (9.3, 50.0), RADIO_BUSY ×2, RADIO_MOSI, RADIO_DIO1, RADIO_MISO_MCU, RADIO_MOSI_MCU, ARM1_SENSE ×2 | no legal spot within 1.5 mm on the final board (gated `nognd_audit`, 0.025 mm, 0.6/0.5 mm vias); via slides ±0.6 mm open none; ARM1_SENSE: spots only in the 7.7 A BAT_IN corridor (3.91 → 3.95 mΩ measured) |
| detour / extra_vias R7 interface (GNSS_RESET_N, RADIO_DIO1 ×2, RADIO_NRST ×2, RADIO_NSS, RADIO_RXEN, RADIO_TXEN), GNSS_LNA_EN, GNSS_VCC_RF | unchanged (F4's searches; nets unchanged) |
| extra_vias PYRO1_CONT | new reason: search with every power pour kept whole, 1.0 mm to PYRO1_GATE_N, finds no route under 6 vias (`fx4/rt/pc8`, via cost 15); the 4-via route cut the 3V3 island |
| extra_vias ARM1_SENSE, QSPI_IO2; detour VCAP1, VCAP2; VBUS ×2, RAW_PROTECTED, VLOGIC | unchanged |

Leftovers (non-critical; detour / extra_vias / tiny_jog; each with its search result in the tool; `_S` = raster search
on the final board, F/B/In2 at 0.05 mm, every power pour kept whole, multi-pad nets summed over their pad MST):

| Net | Present | Search | Verdict |
|---|---|---|---|
| CAM_EN tiny_jog / detour | 6.77 mm / 1 via | 7.45 / 1 | forced 0.293 mm step between C71.1 and U7.1 (x+y ≥ 122.63 vs ≤ 122.44) |
| CAM_FAULT_N tiny_jog / detour / vias | 95.09 / 5 | 78.9 / 7 | step forced by SERVO4_MCU's In2 run and a GND via; shorter search route has 2 more vias |
| BAT_FAULT_N | 39.97 / 4 | 31.4 / 2 | search route needs a forced 0.125 mm jog (VLOGIC vs QSPI_IO0's via) and a via hairpin at U1.81; kept |
| BAT_SW_RETURN | 160.34 / 5 | 177.7 / 7 (0.1 mm grid) | longer |
| BAT_SW_SOURCE | 129.2 / 7 | 124.9 / 6 (0.1 mm grid) | one via less for six F/B hops along the strip edge |
| BUZZ_OUT | 22.55 / 1 | 21.7 / 1 | the present route |
| CAM_5V_SENSE | 36.91 / 4 | legs as present; no path into U1.35 | only route found |
| CAM_MCU_RX | 32.81 / 6 | 32.1 / 5 | one via less for two more In2 hops and grid jogs |
| CAM_MCU_TX | 65.87 / 5 | 66.0 / 5 | the present route |
| CAM_PWR_EN | 81.9 / 8 | 59.1 / 8 | as many vias, nine layer hops through the pyro block; owner trade-off (P3-REQUIREMENTS-01 (b)) |
| CAM_UART_OE | **30.68 / 4** (rerouted, was 44.11 / 6) | 33.1 / 5 | rerouted |
| LED_RED | 32.59 / 3 | no path | only route found |
| LED_YEL | 36.26 / 3 | 36.0 / 3 | the present route |
| LOGIC_SOURCE_ST | 58.5 / 11 | 55.5 / 10 | one via less for 21 mm of In2 |
| NRST | **47 / 4** (J2 branch rerouted, was 54.33 / 6, off In1) | 45.4 / 5 | rerouted |
| RAW_ACT_SENSE | 38.93 / 2 | 41.4 / 2 | longer |
| SERVO1_MCU | 65.32 / 5 | 62.2 / 4 | one via less for 14.6 mm of In2 |
| SERVO2_MCU | 76.72 / 9 | no path into U1.23 | only route found |
| SERVO2_OUT | 37.07 / 1 | 31.4 / 1 with 0.15 / 0.55 mm jogs; 32.3 / 3 with segments ≥ 0.6 mm | kept |
| SERVO4_MCU | 96.4 / 3 | 97.8 / 11 | longer |
| SERVO4_OUT | 46.92 / 3 | 52.4 / 6 | longer |
| SWCLK | 62.7 / 4 | 61.0 / 4 | same corridor |
| SWDIO | 53.72 / 4 | 54.0 / 4 | the present route |
| VBUS_SENSE | 43.13 / 4 | 47.2 / 6 | longer |

The search model blocks every power pour on every layer and knows nothing of the RF strip's fence openings; a "no
path" means no route that keeps the pours whole, not that the present route is optimal in every sense.

## 5. Electrical evidence (final board against the start board)

- **Connectivity:** pad groups with pours identical for all 191 nets; no track-only split or merge; KiCad unconnected
  0 (`fx4/an/d2_groups.txt`). **CH1 pyro copper** (PYRO1_BUS / IGN / OUT): 0.00000 mm² lost or gained on every
  layer, in all copper and outside pads (`d2_pyro_xor.txt`). Pyro sentinel pins untouched; `check_actuators` OK;
  `m3.kicad_dru` untouched.
- **Critical reference** (`tools/critical_reference.py`, R6 board +18 mm): R6 method lost **864 → 603**, candidate new
  **1,122 → 861** (target ≤ 603 met: the 215 SPI1_SCK + 46 SPI1_MISO samples PYRO1_CONT's In2 cut took are back).
  Against the start board directly: 0 lost. Extended set: lost 1,440 → 2,312 and candidate-new 4,020 → 4,304, all from
  NRST: 760 + 373 "lost" samples are R6's NRST In2/In1 copper that no longer exists, and 545 new samples are the new
  NRST In2 run (x 36.3) where B.Cu above it is PYRO1_CONT / 3V3A copper rather than GND (≈ 1.8 mm unreferenced; NRST
  is a slow reset line, and its 3.2 mm on In1, which cut the GND plane, is gone).
- **Pad pour contact:** §2 P4-REGRESSION-02.
- **DC** (`tools/dc_solve.py`, now with the board's stack-up: outer 35 µm, inner 30 µm; mΩ): §5.1.

### 5.1 DC solve

`tools/dc_solve.py` with the board's own stack-up (F.Cu / B.Cu 35 µm, In1 / In2 30 µm; barrels 0.3 mm + 20 µm plating
between copper mid-planes: F↔In1 0.236, In1↔In2 1.060, In2↔B 0.236 mm), 20 °C, pad / contact / component resistance
not included (`fx4/an/dc*`). Old model = 35 µm on every layer and the JLC04161H barrel lengths (M3_R7's table, 0.1 mm
grid). Same-grid comparisons are the meaningful ones; the 0.1 mm grid resolves pours to about ±2 % and paths through
0.15–0.25 mm tracks to about ±5 % at the finest grid quoted (fix-pass-3 records: 0.1 → 0.05 mm moved pours about −1 %,
3V3 paths −3 … +3.5 %, track-limited paths −16 … +3 %), so only the first two significant figures of a track-limited
value carry information.

| Path (mΩ) | Old model, 0.1 mm (M3_R7) | Start board, 0.1 mm | **Final, 0.1 mm** | Final, 0.05 mm | At load (final) |
|---|---:|---:|---:|---:|---|
| RAW_ACT Q121:5–9 → J122:2,5,8,11 (F4, 7.7 A) | 3.96 | 3.95 | **3.95** | 3.91 | 30 mV, 0.23 W; 100 % F.Cu at mid-path |
| BAT_IN J1:1 → Q120:5–9 (7.7 A) | 3.91 | 4.55 | **4.55** | 4.51 | 35 mV, 0.27 W; 100 % In2 at mid-path |
| ACT_FET_S Q120:1–3 → Q121:1–3 (7.7 A) | 1.36 | 1.36 | **1.36** | 1.33 | 10 mV, 0.08 W; B.Cu |
| BAT_IN J1:1 → U9:5 (1 A) | 13.4 | 15.14 | **15.14** | 15.02 | 15 mV |
| 3V3 L1:2 → U1:75 | 14.2 | 15.64 | **15.64** | — | 0.1 A: 1.6 mV |
| 3V3 L1:2 → FB31:1 (radio feed) | 13.8 | 14.66 | **14.66** | — | 0.1 A: 1.5 mV |
| 3V3 L1:2 → FB30:1 (GNSS feed) | 5.26 | 5.53 | **5.53** | — | 0.1 A: 0.6 mV |
| 3V3 L1:2 → U1:27 | 6.46 | 6.85 | **6.85** | — | 0.1 A: 0.7 mV |
| 3V3 L1:2 → U3:8 | 6.60 | 6.76 | **6.76** | — | 0.1 A: 0.7 mV |
| 3V3 L1:2 → C9:1 (buck output capacitor) | 2.48 | 2.48 | **2.48** | 2.30 | — |
| RAW_PROTECTED U9:6 → U11:2 | 35.4 | 35.23 | **35.23** | — | 0.5 A: 18 mV |
| RAW_PROTECTED U9:6 → U7:3,4 | 154 | 153.45 | **153.45** | — | 1 A: 0.15 V (0.025 mm: about 125, fix-pass-3 records) |
| RAW_PROTECTED U9:6 → TP81:1 | 145 | 144.52 | **144.52** | — | 1 A: 0.14 V |
| VLOGIC C84:1 → U2:2,3 | 36.5 | 36.39 | **36.39** | — | 0.5 A: 18 mV |
| USB_LIMITED U10:6 → U11:7 | 72.4 | 72.37 | **72.37** | — | 0.5 A: 36 mV |
| CAM_5V L3:2 → J9:1 | 24.7 | 27.88 | **27.79** | — | 1 A: 28 mV |

- **Fix pass 4 changed no power path beyond the method's resolution:** every path is identical, start → final, at the
  same grid, except CAM_5V (27.88 → 27.79 mΩ, −0.3 %, the In2 GND / CAM_5V boundary moved where NRST's and
  CAM_UART_OE's old In2 runs went).
- **The stack-up correction matters for the paths carried on In2:** BAT_IN J1 → Q120 3.91 → 4.55 mΩ (+16 %), J1 → U9
  13.4 → 15.1 (+13 %), CAM_5V +12 %, 3V3 L1 → U1.75 +10 %, the other 3V3 paths +2 … +6 %; F.Cu / B.Cu paths (RAW_ACT,
  ACT_FET_S, RAW_PROTECTED, VLOGIC, USB_LIMITED) are unchanged within 0.5 %. "Equal to R6" in the records is a
  same-model comparison (both boards at 35 µm); the absolute In2 values are the ones above. At 7.7 A the BAT_IN path
  drops 35 mV and dissipates 0.27 W (was 30 mV / 0.23 W on the 35 µm model). Peak current density on In2 at 7.7 A:
  6.2 A per mm of width at the BAT_IN In2 neck (10.45, 107.62) at 0.1 mm, i.e. about 206 A/mm²
  in 30 µm copper there (grid-dependent; the neck the hygiene record names by ACT_EN's via; IPC-2152 sizing is for the
  records).
- **Values to quote** (finest grid run, with the method's resolution): RAW_ACT 3.9 mΩ, BAT_IN J1 → Q120 4.5 mΩ,
  ACT_FET_S 1.33 mΩ, BAT_IN J1 → U9 15.0 mΩ (pours, ±2 %); 3V3 L1.2 → C9.1 2.3 mΩ (0.6 mm tracks; 0.1 → 0.05 mm moved
  it −7 %, ±5 %); the 0.1 mm-only rows ±2 % (pours) or ±5 … 16 % (track-limited rows: RAW_PROTECTED, VLOGIC,
  USB_LIMITED — the fix-pass-3 records' 0.025 mm values for those still apply, the copper being unchanged).

## 6. Gate and tests (final board)

```
DRC violations 0  unconnected 0  schematic parity 0  ERC 0
metadata / 3D model audit: OK
silkscreen outside the board outline (46.00 x 118.00 mm): 0 stroke points
R7 CAD contract: OK
routing hygiene: 0 failing, 37 allowlisted, 0 stale allowlist entries, 0 out-of-date no-GND reasons, 34 leftovers recorded (0 unrecorded, 0 stale): OK
actuator safety contract: OK
  nearest bottom/pin envelope: C76, 4.150 mm from support (42.0, 114.4) (minimum 3.5 mm)
  nearest top hardware clearance: TP30.1 exposed top pad, 5.008 mm from support (4.0, 4.0) (minimum 3.8 mm)
fit check: OK (CAD envelopes only)
```
(`tools/check.sh` exit 0, run by `r7_build.sh` on the built board; `fx4/build2.log`.)

Tests (KiCad Python): check_shell 2 OK, dc_solve 3 OK (new), fab_validation 23 OK, fit_check 23 OK, maze_clearances
10 OK, procurement 15 OK, r6_check 17 OK, r7_check 34 OK, route_check 32 OK (+5: relief ring is not a finger,
pad_pour_cut with trim vs design keep-out, nognd_audit with injected and real search, leftover record, leftover
reasons); quality_audit 21 OK under KiCad Python and python3. test_r5_repair: 1 error, the known pre-existing
`routing_lands_spacing`.

## 7. For the records (docs agent / next pass)

- M3_R7 build description: `r7_polish` now also runs band, debris, reroutes, rf_relief, gnd_vias, gnd_vias2; board SHA
  above; 21 `R7_POUR_TRIM_n` rule areas; route_check 37 allowlisted + 34 leftovers, new gated checks (nognd_audit,
  pad_pour_cut, leftover record) and the pour_finger relief-ring rule; `dc_solve` reads the stack-up.
- Hidden designators 83 → 84 (r7_post on the new copper): newly hidden R157, R63, TP88; newly shown C18, Q124. Full
  list: C100 C126 C128 C129 C13 C14 C15 C150 C151 C160 C25 C30 C302 C303 C305 C31 C311 C312 C313 C314 C60 C7 C71 C74
  C8 C88 C90 C92 C94 D123 D30 D31 FB31 J123 L30 LED1 Q32 R10 R101 R102 R103 R104 R105 R11 R12 R125 R128 R129 R130 R133
  R157 R161 R162 R163 R164 R173 R178 R180 R301 R302 R303 R304 R311 R312 R316 R32 R63 R64 R74 R75 R8 R86 R88 R91 TP71
  TP74 TP81 TP83 TP88 TP90 U11 U13 U7 Y1. (P4-DOCS-04's courtyard test was not in my list.)
- R7_VALIDATION: P4-ROUTING_GEOMETRY-01's record corrections (P3-RG-02 / P3-RQ-01 now 10 entries, M3_R7's allowlist
  row, STATUS); the PYRO1_CONT trade-off is resolved (6-via route); C302 relief and the D30/D31 decision; ORDERING §5
  inspection line; DC table restated with the 30 µm inner copper (§5.1; "equal to R6" is a same-model comparison).
- Renders `r7_top.png` / `r7_bottom.png` are stale (fix-pass-3 copper).

## 8. Files changed by F5

`m3_design/r7_polish.py`, `m3_design/r7_hygiene.py` (GndFit / gnd_spots / fine pass; output unchanged),
`m3_design/r7_lib.py` (comment only), `m3_design/r7_build.sh` (comment only), `tools/route_check.py`,
`tools/test_route_check.py`, `tools/check_r7.py` (RF_SOLID_GND), `tools/dc_solve.py`, `tools/test_dc_solve.py` (new);
`m3_design/assembly_review/m3.kicad_pcb`; `fab/m3_gerber.zip`, `m3_assembly_{top,bottom}.pdf`, `m3_fab_manifest.json`
(BOM / CPL rewritten byte-identical); this file and `fix4_F5_progress.md`.
