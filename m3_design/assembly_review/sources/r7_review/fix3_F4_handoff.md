# R7 fix pass 3, agent F4 (board, tools): handoff

Worktree branch `m3-assy-r7`, uncommitted, on R6 commit `3b215ba`. Start: the fix-pass-2 board, SHA-256
`7660620cfa834e4d381d2a2638780e9a341341c9b93c6e6f526791204dc77c9c`. Nothing committed, pushed or opened as a PR. I did
not edit `docs/*.md`, `STATUS.md`, `AGENTS.md`, the schematic, `m3.kicad_dru` or `check_actuators.py`. Running log:
`fix3_F4_progress.md`. Scratch evidence: `<scratchpad>/fx3/` (router runs `det/`, `rt/`; analyses `an/`).

**Final board SHA-256 `636a6bdc7234586a659741a3da921335a47197648c29cd9612c8374733847650`.** Two clean
`m3_design/r7_build.sh` runs from the SHA-checked R6 board gave this same file; the saved board is that file. Fab
package regenerated with `tools/export_fab.py` and bound (`m3_fab_manifest.json`); BOM and CPL are byte-identical to
fix pass 2, so `stock_check.json` / `cost_check.json` still apply. `r7_top.png` / `r7_bottom.png` re-rendered.

## 1. Build chain

`r7_build.sh`: `r7_pcb` → `r7_route` (→ `r7_redraw`) → `r7_rework` → `r7_hygiene` → **`r7_polish` (new)** → `r7_post` →
`tools/check.sh`. The router replay (`r7_reroute_session.json`) is unchanged. Proof that the upstream output did not
move: the board after `r7_hygiene` in the new chain has exactly the old final board's tracks (1946), vias (709) and
zone fills (`fx3/cucompare.py`); `r7_hygiene`'s dead stage now calls `route_check.dead(nc, pour_islands=False)`, the
old semantics. `m3_design/r7_polish.py` follows `r7_hygiene`'s invariants (pad groups with pours identical after every
stage, by tracks only may merge; asserted deletions; every new segment and via checked by `r7_hygiene.Clearance`, vias
also by `r7_route.ViaCheck`; KIID seed 7601; asserted counts so a changed upstream board stops the build). Stages and
results (final build):

| Stage | Result |
|---|---|
| dead | 40 tracks under route_check's new pour-island rule (list in the build log) |
| neck | GND B.Cu (13.7, 80.6)–(14.6, 80.6) 0.25 → 0.2 mm (a T the dead stage removed) |
| swd | SWCLK 46 tracks / 14 vias → 16 / 4; SWDIO 32 / 11 → 12 / 4; 3V3 via (41.135, 77.92) → (41.0, 77.92) 0.5 mm; SERVO1_MCU via (34.6, 58.7) → (34.6, 58.5) |
| pyro_corners | PYRO1_GATE_N, PYRO1_COLD, GND C126.2–R128.2 redrawn |
| pyro1_cont | PYRO1_CONT 29 items (7 vias) → 12 segments, 4 vias; GND return vias (23.68, 69.55), (29.28, 77.95) |
| corners | C17.1, R164 branch, D9.1, J3 GND, C8.2 redrawn |
| l1_node | L1.2 node: 4 tracks and via (24.2, 35.3) removed, 4 segments drawn |
| gnd_moves | GND vias (19.65, 30.55) → (19.71, 30.51), (3.3, 50.4) → (3.26, 50.44); new GND via (35.5, 29.4) by C160.2 |
| dead2 | 1 track (3V3 In2 (15.2, 62.3)–(16.5, 61.0), in one island after SWDIO's In2 runs left) |
| pour_trim | 21 zone-fill keep-out rule areas `R7_POUR_TRIM_1…21` (F.Cu 7, B.Cu 14) |
| strip_stitch | 3 GND vias (0.5 mm): (11.975, 21.575), (9.025, 8.325), (25.025, 8.525) |
| pour_trim2 | 0 |

## 2. Per finding

| Finding | Done? | What |
|---|---|---|
| P3-RF-01 (Major) | Yes | The 15.2 mm RXEN/BUSY F.Cu sliver, the 5.9 mm SPI1 sliver and every other sliver / unstitched finger are kept out by `pour_trim` (generated from the fill scan after all copper changes, asserted count; no change to GND_F's minimum width). Whole-board scan: start board 6 slivers + 19 fingers → 0. Checks: `route_check` `pour_sliver` (< 0.25 mm, > 3 mm, every pour net) and `pour_finger` (GND, < 0.5 mm, > 3 mm, a point > 4 mm of copper from a GND via or plated GND hole), both gated; `check_r7.rf_gnd_reach`: every F.Cu / B.Cu GND copper point in the strip ≤ 4.0 mm of copper from a GND via (start board after the sliver fix: 4.99 / 4.87 mm; final 3 stitching vias, check OK). Tests in both suites. |
| P3-REQUIREMENTS-01 (Major), option (a) | Partly | **SWCLK** 117.2 mm / 14 vias / 19.5 mm on In1 → **62.7 mm / 4 vias, F/B only** (ratio 3.55 → 1.90); **SWDIO** 70.8 / 11 → **53.7 / 4** (1.95 → 1.48; 5.9 mm In2 hop between J122's rows and under the SPI1/I2C1 bundle: on F.Cu that run cut the RAW_ACT_F servo pour, which the pad-group guard caught). Neither touches In1 or the pyro block. Routes from a raster A* search (0.05 mm, every board clearance, power pours whole, crystal kept clear): two one-track corridors out of U1's SW corner exist (north under U1's body / NE corner; south past J122), nothing more direct on F/B. **PYRO1_CONT** rerouted: 59.9 mm / 7 vias (an In2 run inside the BAT_IN servo pour, up round J2, the staircase) → 47.6 / 4; staircase allowlist entry gone. **CAM_PWR_EN** not rerouted: no F/B path at all, and the search with the SWD lines moved and the power pours kept whole returns the present route (81.9 mm / 8 vias). **CAM_MCU_TX** not rerouted: the best candidate (50.8 mm / 3 vias, `fx3/rt/cmt_w1.json`) splits the 3V3 In2 plane at the buck output, L1.2 → U1.75 14.25 → 29.66 mΩ; with the buck and crystal kept clear it needs 8 vias. **VCAP2 / U12–C100 3V3** loops (P3-ROUTING_QUALITY-05) not changed: the search finds the same VCAP2 west loop (10.75 mm / 1 via); U12's 3V3 feed has no In2 plane there; both need part moves. |
| P3-ROUTING_QUALITY-03 | No | Tied to CAM_MCU_TX above (its In2 run under RADIO_NRST's B.Cu run stays). |
| P3-ROUTING_GEOMETRY-01 (a)–(d) | Yes (tool) | `route_check`: tiny-jog test on every A,B,A triple inside longer runs (13 instances on the start board, was 5); new gated `short_segment` (≥ 50 µm and < max(width, 0.2 mm), not wholly inside one same-net pad/via); the two GND vias moved (RXEN 1.553 → 1.50 mm, GNSS_RXD_MCU 1.556 → 1.50), their allowlist entries gone; QSPI_CLK and `_NOGND` reasons rewritten (true: straight on at x 22.85 leaves 0.15 mm, the DRC minimum, to the LED_YEL via; a longer step leaves 0.196 mm to RXEN). Board: PYRO1_GATE_N's 83 µm hook (the review's N/45°/N redraw is itself a tiny jog by the rule) → one straight run at x 21.9 into R126.1 (0.3 mm off its centre inside the 1.38 mm pad); 3V3 into C17.1 square into the centre; GND pyro corner one 45° step; SW_NODE allowlisted (forced, measured reason). |
| P3-ROUTING_GEOMETRY-03 | Yes | `graph(island_nodes=True)`: each pour island is one terminal; `dead()` flags copper touching only one island and stubs ending in a pour (a run from a pour-only end back to the first junction/pad/via whose removal leaves the zoned pad groups unchanged; bridges between two islands stay live). 40 + 1 tracks removed (incl. the floating 3V3 chain and the six protruding stubs). |
| P3-ROUTING_GEOMETRY-05 | Yes (tool) | `power_via_no_gnd` reported (information; 39 → 36). Detour / via-count checks: `detour` (net copper > 1.6 × octilinear MST of its pads and > 2 mm over) and `extra_vias` (layer-changing vias > need + 2, need 0 if all pads share a layer else 1), gated on critical nets, counted on all; `--routes` prints every net's length / MST / ratio / vias. |
| P3-ROUTING_GEOMETRY-04 | Yes | L1.2 node: tracks from the pad centre (45° to plane via (24.8, 34.3), C8.1 branch) and a vertical on C8.1's branch inside the pad to plane via (26.4, 36.6) (USB_LIMITED's via (25.8, 37.15) stops it moving under the centre line); C9.1 joins that vertical square at (26.4, 36.1); second via and hop removed. |
| P3-ROUTING_GEOMETRY-02 / P3-ROUTING_QUALITY-01 | Recorded | 11 critical layer changes left without a GND via ≤ 1.5 mm (band, corridor, PYRO1_GATE_N, ARM1_SENSE ×2), allowlisted with the corrected reasons. |
| P3-ROUTING_QUALITY-06 | Yes | PYRO1_GATE_N reason now states the 1.03 mm DRC-legal spot and why ViaCheck refuses it. |
| P3-REGRESSION-01 | No | Not feasible without moving three more vias: C121.1's corner forces MOSI to x − y ≥ −43.0; a 0.3 mm gap needs IMU_CS at ≥ −42.24 and I2C1_SCL at −41.76, which hits the SERVO1_MCU via (27.1, 68.2), the SERVO2_MCU via (26.3, 67.4) and leaves 0.002 mm on the 3V3 via (30.17, 71.17) (measured with `r7_hygiene.Clearance`). The 0.189 mm × 14.8 mm adjacency stays (DRC-legal); the GND sliver between MISO and MOSI is trimmed. |
| P3-REGRESSION-02 | Yes | GND via (35.5, 29.4) 0.7 mm from C160.2, joined by one 45° track; D122.1 reaches it over its existing link to C160.2 (≈ 2.5 mm of copper, was 5.62; C160.2 0.7, was 4.22). No legal spot nearer D122.1 (2.5 mm search). |
| P3-ROUTING_QUALITY-04 | Yes | PYRO1_COLD: R131.2 → north → 45° into D120.1 (0.48 mm to R131.1, rule C 0.3). check_actuators hashes the rules, not copper; it passes unchanged. |
| P3-ROUTING_QUALITY-02 | No | The 7 radio lines' In2 GND → BAT_IN crossings stay: moving them means cutting the In2 BAT_IN arm (U9's feed) at both corridor ends or moving the band / U1-side via columns onto In2 GND; stitching needs a new BAT_IN–GND capacitor (schematic and BOM change). Not a cheap fix; for the record / owner. |
| P3-REQUIREMENTS-06 | Yes | `check_r7.RF_PART` adds `Q3\d`; new `rf_part_coverage` fails any part with a radio/GNSS-net pad (U1 excepted) outside the filter (none). Tests. |
| P3-RF-04 | Yes | C304 in `check_r7.DNP`; `launch_reference` (In2 GND under each In1 launch cut-out ± 0.3 mm, 0.1 mm samples: 1025/1025 each); `module_ground` (In1 + In2 GND under U31's whole body, In1 under U30's keep-out, 0.2 mm samples: none missing); strip reach check (P3-RF-01). Tests. |
| P3-MECHANICAL-04 | Yes | `fit_check.check_board` adds exposed bottom pads of board features and DNP footprints to the standoff rule (NPTH tooling holes have none). Test with a bottom test pad and a DNP land inside 3.5 mm. Board result unchanged (nearest C76 4.150 mm). |
| P3-DFM-06 (a), (b) | Yes | `r7_post`: the SMA legends keep 0.2 mm from every via (0.25 / 0.35 found no spot) and nothing else is placed within 0.8 mm of them. GNSS now vertical beside J30 (≥ 0.22 mm from vias, was 0.18 by ink box); J31's designator moved off RADIO's end. (c), (d) not in my scope. Hidden designators 89 → 83: newly hidden C150, Q124, R312, TP81; newly shown D120, R155, R156, R157, TP70, TP73, TP76, TP82, TP87, TP88. Final list: C100 C126 C128 C129 C13 C14 C15 C150 C151 C160 C18 C25 C30 C302 C303 C305 C31 C311 C312 C313 C314 C60 C7 C71 C74 C8 C88 C90 C92 C94 D123 D30 D31 FB31 J123 L30 LED1 Q124 Q32 R10 R101 R102 R103 R104 R105 R11 R12 R125 R128 R129 R130 R133 R161 R162 R163 R164 R173 R178 R180 R301 R302 R303 R304 R311 R312 R316 R32 R64 R74 R75 R8 R86 R88 R91 TP71 TP74 TP81 TP83 TP90 U11 U13 U7 Y1. |

## 3. Counts before / after

### 3.1 `tools/route_check.py` — all (critical) / failing / allowlisted

| Category | Start board, pass-2 tool | Start board, new tool | Final board |
|---|---|---|---|
| critical_via_no_gnd | 14 (14) / 0 / 14 | 14 (14) / 0 / 14 | 11 (11) / 0 / 11 |
| dead_copper | 0 | 40 (40) / 40 / 0 | 0 |
| staircase | 5 (5) / 0 / 5 | 5 (5) / 0 / 5 | 4 (4) / 0 / 4 |
| tiny_jog | 5 (1) / 0 / 1 | 13 (5) / 4 / 1 | 13 (5) / 0 / 5 |
| short_segment | – | 19 (13) / 13 / 0 | 9 (3) / 0 / 3 |
| detour | – | 23 (9) / 9 / 0 | 22 (9) / 0 / 9 |
| extra_vias | – | 29 (10) / 10 / 0 | 29 (10) / 0 / 10 |
| pour_sliver | – | 6 / 6 / 0 | 0 |
| pour_finger | – | 19 / 19 / 0 | 0 |
| power_via_no_gnd (info) | – | 39 | 36 |
| extra_bends / u_turn / short_layer_hop (info) | 36 / 25 / 26 | same | 33 / 26 / 20 |
| pad_end_offcentre / width_change_junction (info) | 90 / 31 | same | 89 / 30 |
| **total** | **244 / 0 failing / 20 allowlisted** | **427 / 101 failing / 20** | **334 / 0 failing / 42 allowlisted** |

Non-critical hygiene left (counted, not gated): tiny jogs CAM_EN, SERVO2_MCU, SERVO4_MCU, CAM_5V_SENSE, CAM_FAULT_N,
I2C1_SCL, SERVO4_OUT, LOGIC_ILIM; short segments on CAM_EN, LED_YEL_A, SERVO2_MCU, SERVO3_MCU, CAM_5V_SENSE,
CAM_RX_WIRE; non-critical detours (CAM_PWR_EN 2.52, CAM_MCU_TX 2.67, SWCLK 1.90 …: `route_check --routes`).

### 3.2 Pass-2 reviewers' `scan.py` (unchanged), all (critical)

Start 1034 (647) → final **969 (595)**: end_in_zone_only 22 → 1, short_segment 44 (26) → 34 (19), short_layer_hop
26 → 20, critical_via_no_gnd 14 → 11, staircase 5 → 4, right_angle_corner 60 → 56, dogleg 156 → 151, chain_detour
64 → 62, acute_at_padvia 12 → 11, tiny_jog 5 (1) unchanged (its grammar does not test inner triples), u_turn 25 → 26,
width_change_at_pad 16 → 18 (full table: `fx3/scancount.py an/base_scan.json an/b2_scan.json`).

## 4. Allowlist (42 entries, `tools/route_check.py` ALLOWLIST; each carries its measured reason in the tool)

| Entries | Reason (short) |
|---|---|
| staircase ×4, tiny_jog ×3, short_segment ×1: RADIO_NRST / BUSY / MISO_MCU / SCK band (x 9.4–10.6, y 27.7–29.7) | band fan-in: two via columns on 0.5 mm rows, 0.4 mm lane pitch, BAT_SW_RETURN 0.175 mm south; only re-spacing the columns removes it |
| tiny_jog QSPI_CLK (22.85, 45.95) | straight on leaves 0.15 mm (DRC minimum) to the LED_YEL via; a step out of the tiny-jog class leaves 0.196 mm to RXEN |
| tiny_jog + 2 short_segment SW_NODE | 0.6 mm run must pass the 1.22 mm C7.2/C9.2 gap and keep 0.75 mm from U2's 3V3 and GND vias; every one-bend route collides (pass-3 review, measured) |
| critical_via_no_gnd ×8 radio band / corridor, PYRO1_GATE_N, ARM1_SENSE ×2 | no legal GND via spot (0.05 mm search with ViaCheck, TP 1.0 mm, Tag-Connect, Pyro D; pass-3 0.025 mm search and nudge search agree); PYRO1_GATE_N: the 1.03 mm DRC-legal spot is within 0.15 mm of GND pads C127.2/R127.2; ARM1_SENSE: legal spots only in the BAT_IN J1→Q120 corridor (3.91 → 3.95 mΩ) |
| detour / extra_vias GNSS_RESET_N, RADIO_DIO1 ×2, RADIO_NRST ×2, RADIO_NSS, RADIO_RXEN | R7 interface topology; the raster search finds shorter routes only through 18–40 mm In2 runs into the strip's GND-only In2, through the strip fence outside its openings, or straight under the buck (RXEN) |
| detour RADIO_TXEN | U31's pad field holds only GND on every layer; the search's 12.2 mm path crosses the keep-out |
| detour GNSS_LNA_EN, GNSS_VCC_RF | limiter on B.Cu under U30, F.Cu pads on its aft row, U30 keep-out |
| extra_vias PYRO1_CONT, ARM1_SENSE, QSPI_IO2 | the search finds no route with fewer vias (PYRO1_CONT 4, ARM1_SENSE 4, QSPI_IO2 3) |
| detour VCAP1, VCAP2 | search: 5.81 mm / 2 vias and 10.75 mm / 1 via at best (inherited R6; need C19 / C20 moved) |
| detour + extra_vias VBUS; extra_vias RAW_PROTECTED, VLOGIC | multi-pad power trees with interleaved F/B pads (pad lists in the reasons) |

## 5. Electrical evidence (final board vs start board)

- **Connectivity:** pad groups with pours identical for all 191 nets; no track-only split or merge; KiCad
  unconnected 0. **CH1 pyro copper** (PYRO1_BUS/IGN/OUT): 0.00000 mm² lost or gained on every layer, outside pads
  and in all copper. Pyro sentinel pins untouched; `check_actuators` OK.
- **DC** (`dc_solve`, 0.1 mm grid, 4 dp): RAW_ACT Q121→J122 3.9567 → 3.9567 mΩ, BAT_IN J1→Q120 3.9070 → 3.9070,
  ACT_FET_S 1.3561 → 1.3561, BAT_IN J1→U9 (1 A) 13.3883 → 13.3883. 3V3 from L1.2 (0.1 A): U1.75 14.2549 → 14.2487,
  FB31.1 13.6137 → 13.8039, FB30.1 5.0599 → 5.2594, U1.27 6.3262 → 6.4579, U3.8 6.4016 → 6.6041 mΩ (≤ +0.20 mΩ:
  the dead 3V3 In2 runs at L1 and the second L1 plane via; ≤ 0.02 mV at 0.1 A).
- **Critical reference** (`tools/critical_reference.py`, R6 moved +18 mm): R6 method lost 603 → **864**, candidate
  new 861 → **1122**: the +261 are one perpendicular crossing of PYRO1_CONT's new In2 hop under SPI1_SCK's B.Cu run
  (215 samples at (23.7–24.3, 67.1–67.8)) and its via's In1 antipad beside SPI1_MISO (46 at (24.1–24.5, 68.2–68.5)).
  The only PYRO1_CONT route keeping the 3V3 plane whole has 6 vias (`fx3/rt/pc_route2.json`); I kept the 4-via
  route. Extended set: lost 874 → 1440, candidate new 2659 → 4020 (the rerouted SWD copper counted against R6's
  positions), but the candidate's own unreferenced samples fell **71,607 / 245,913 → 55,956 / 224,208**; per net:
  SWCLK 14,945 → 2,512, SWDIO 11,310 → 7,831, SPI1_SCK 6,455 → 6,670, SPI1_MISO 2,770 → 2,816, others equal.

## 6. Gate and tests (final board)

```
DRC violations 0  unconnected 0  schematic parity 0  ERC 0
metadata / 3D model audit: OK
silkscreen outside the board outline (46.00 x 118.00 mm): 0 stroke points
R7 CAD contract: OK
routing hygiene: 0 failing, 42 allowlisted, 0 stale allowlist entries: OK
actuator safety contract: OK
  nearest bottom/pin envelope: C76, 4.150 mm from support (42.0, 114.4) (minimum 3.5 mm)
  nearest top hardware clearance: TP30.1 exposed top pad, 5.008 mm from support (4.0, 4.0) (minimum 3.8 mm)
fit check: OK (CAD envelopes only)
```

Tests (KiCad Python): check_shell OK, fab_validation OK, fit_check 23 OK (+1), maze_clearances OK, procurement 15 OK,
r6_check OK, r7_check 34 OK (+6), route_check 27 OK (+8); quality_audit OK (KiCad Python and python3).
test_r5_repair: 1 error, the known pre-existing `routing_lands_spacing` failure.

## 7. For the records (docs agent / next pass)

- M3_R7 build description: add `r7_polish.py` between `r7_hygiene.py` and `r7_post.py`; board SHA above; 83 hidden
  designators (list in §2); 21 `R7_POUR_TRIM_n` keep-out rule areas; route_check now 42 allowlisted with the new
  categories (§3.1, §4); check_r7 new checks (RF part coverage, launch In2 reference, module ground, strip GND
  reach); fit_check covers bare/DNP bottom pads.
- R7_VALIDATION: per-finding table §2; critical reference 864 / 1122 (R6 method) with the PYRO1_CONT explanation; DC
  §5; residuals: P3-REGRESSION-01, P3-ROUTING_QUALITY-02/-03/-05, CAM_PWR_EN / CAM_MCU_TX detours, the 42 allowlist
  entries (owner acceptance).
- REQUIREMENTS M2 wording already describes the gated detour / via-count checks (docs agent); the thresholds are in
  `route_check.py` (DETOUR_MAX 1.6, DETOUR_SLACK 2 mm, VIA_SLACK 2, SLIVER 0.25 / 3 mm, FINGER 0.5 / 3 mm / 4 mm).

## 8. Files changed by F4

`m3_design/r7_polish.py` (new), `m3_design/r7_build.sh`, `m3_design/r7_hygiene.py` (dead stage call only),
`m3_design/r7_post.py`, `tools/route_check.py`, `tools/test_route_check.py`, `tools/check_r7.py`,
`tools/test_r7_check.py`, `tools/fit_check.py`, `tools/test_fit_check.py`; `m3_design/assembly_review/m3.kicad_pcb`;
`fab/m3_gerber.zip`, `m3_assembly_{top,bottom}.pdf`, `m3_fab_manifest.json` (BOM/CPL rewritten byte-identical);
`r7_top.png`, `r7_bottom.png`; this file and `fix3_F4_progress.md`.
