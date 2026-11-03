# R8 survey: baseline quality metrics of the accepted R7 board

Board measured: `rocket-flight-computer-r7/m3_design/assembly_review/m3.kicad_pcb`, branch `m3-assy-r7`, commit
`431025d`, SHA-256 `c872a3d30509cccf5f78b64cde48ef722ee85c7be23c4848b07ce4082a852de3` (owner-accepted R7, 46 × 118 mm).
All runs used a byte-identical copy (`baseline/r7_board/`); the repository was not touched (`git status` clean after).
R6 final (`184a87e8…`, 46 × 100 mm, no RF strip) was surveyed the same way for context only.

Everything below can be reproduced on any filled board with one command (section 5). Lower is better unless a row
says otherwise. Values marked † come from the repo's own tools; wherever `docs/R7_VALIDATION.md` or `docs/M3_R7.md` quote the same
quantity (gate, route_check counts, DC at both grids, necks, critical-reference losses against R6) they match exactly.

## 1. Scorecard (the numbers a new layout must beat)

The **simplicity index** is the geometric mean of the twelve rows marked **I**, each as new/baseline (inverted for
"higher is better"; counts +1 so zero stays finite). By definition R7 = 100; lower is simpler. On the rows it can be
computed for, R6 scores 143 against R7. The proposed R8 targets are a suggestion for the synthesis step, not a decision.

### Correctness gate and clean-routing exceptions

| ID | Metric (definition) | R7 | R6 | Proposed R8 target |
|---|---|---:|---:|---|
| G | `tools/check.sh` exit; DRC / unconnected / parity / ERC | 0; 0/0/0/0 † | — | 0 (hard) |
| C1 **I** | route_check instances in gated categories (§3 rule + hygiene + pour + removable bumps), allowlisted or not | 74 † | — | 0 |
| C2 **I** | route_check information-only instances | 252 † | — | ≤ 100 |
| C3 | ALLOWLIST entries that match (gated exceptions) | 45 † | — | 0 (hard: "no exceptions needed") |
| C4 | LEFTOVERS (non-critical hygiene, recorded) | 29 † | — | 0 |
| C5 | failures + unrecorded leftovers + stale entries | 0 † | — | 0 (hard) |
| C6 | AGENTS §3 rule-category instances (all are `critical_via_no_gnd`) | 9 † | — | 0 (hard) |

C1 breakdown: critical_via_no_gnd 9, tiny_jog 2, detour 21, extra_vias 27, chain_detour 9, pour_net_hop 5, local_bump 1.
C2 breakdown: pad_end_offcentre 94, extra_bends 35, power_via_no_gnd 34, width_change_junction 31, u_turn 22,
short_layer_hop 18, passes_through_pad 8, via_on_track_in_fill 6, segment_inside_pad 4.
The 45 allowlist entries: radio/GNSS interface 20 (no-GND layer changes 8, detours 6, extra vias 4, tiny jogs 2);
power and poured nets 21 (GND chain detours 5, 3V3 chain detour + 3 series hops, RAW_ACT 2 chain detours + 1 hop,
CAM_5V hop, 3V3A chain detour, VBUS detour + extra vias, RAW_PROTECTED and VLOGIC extra vias, VCAP1 and VCAP2
detours, USB_LIMITED local bump); pyro 3 (ARM1_SENSE and PYRO1_CONT extra vias, PYRO1_GATE's change into TP122);
QSPI_IO2 extra vias 1. The 29 leftovers (`extra_vias` 17, `detour` 12) are camera, power-switch and harness lines
(BAT_SW_*, CAM_*, LOGIC_SOURCE_ST, BAT_FAULT_N, BUZZ_OUT), servo lines (SERVO1/2/4), SWD (SWCLK, SWDIO, NRST) and three
sense/LED nets. For scale, R7_VALIDATION's owner-accepted deviation list holds 99 entries and rows (A 45, B 29, C 25
review rows = 299 named instances, plus the 252 information instances); an R8 that needs "no exceptions" empties A, B
and C.

### Routing simplicity

| ID | Metric (definition) | R7 | R6 | Proposed R8 target |
|---|---|---:|---:|---|
| S1 **I** | signal track length, mm (every net except GND and the route_check `power` class) | 3355 | 3705 | ≤ 2700 |
| S2 | all track length, mm | 4428 | 5179 | ≤ 3600 |
| S3 | signal vias (non-GND, non-power nets) | 218 | 332 | — |
| S4 **I** | signal layer-change vias (same-net tracks on ≥ 2 layers at the via) | 217 | 330 | ≤ 110 |
| S5 | power-rail vias (non-GND) | 114 | 117 | — |
| S6 | detour ratio, length-weighted: Σ copper / Σ octilinear MST of pad centres (136 nets without a pour, ≥ 2 pads) | 1.396 | 1.636 | ≤ 1.20 |
| S7 **I** | detour excess, mm: Σ (copper − MST) over those nets | 1081 | 1658 | ≤ 450 |
| S8 | nets with ratio > 1.6 | 23 | 38 | 0 |
| S9 | nets with ratio > 2.0 | 12 | 22 | 0 |
| S10 | bends per 10 mm of signal track (heading changes at plain nodes) | 1.93 | 2.91 | — |
| S10b **I** | signal bends, total (R7: 619 × 45°, 29 × 90°, 0 acute) | 648 | 1078 | ≤ 400 |
| S11 | bends per two-pad signal route (mean) | 5.05 | 6.59 | ≤ 3 |
| S12 **I** | critical-signal layer changes (vias joining a critical signal net's tracks on ≥ 2 layers) | 73 | 86 | ≤ 35 |
| S13 | … of which no GND via centre within 1.5 mm (survey count; route_check's 9 adds PYRO1_GATE's change into TP122) | 8 | 54 | 0 (hard) |
| S14 | critical-signal nets, length-weighted detour ratio | 1.314 | 1.445 | ≤ 1.15 |
| S15 **I** | signal track on In2, mm | 901 | 1221 | ≤ 300 |
| S16 | track on In1 (the GND reference plane), mm | 0 | 114 | 0 (hard) |
| S17 | placement: Σ octilinear MST of every routed net without a pour, mm (a ratsnest-length proxy) | 2727 | 2608 | ≤ 2400 |
| S18 | track segments | 1724 | 3125 | — |

### Planes, return paths and stitching

| ID | Metric (definition) | R7 | R6 | Proposed R8 target |
|---|---|---:|---:|---|
| P1 | In1 GND fill area / board outline area | 0.880 | 0.830 | ≥ 0.90 |
| P2 | In1 GND islands | 1 | 1 | 1 |
| P3 | In1 voids ≥ 5 mm² (R7: 6 mounting / tie holes, 9 connector-pin voids, 3 via clusters) | 18 | 27 | holes and pins only |
| P3b | In1 slots: voids ≥ 2.5 mm long and < 1.6 mm mean width (merged via antipads, pad rows) | 16 | 23 | ≤ 4 |
| P4 | In2 pour regions (islands of all nets) | 8 | 14 | ≤ 5 |
| P5 | nets poured on In2 | 5 | 4 | — |
| P6 | In2 pour perimeter, mm (outlines + voids: the length of every In2 split edge) | 1581 | 1440 | ≤ 900 |
| P7 **I** | outer-layer GND pour islands stitched by ≤ 1 GND via / plated GND hole (F 18, B 14) | 32 | 61 | 0 |
| P8 | GND vias + plated GND holes per cm² of board | 7.22 | 3.17 | — |
| P9 **I** | distance from a board point to the nearest GND via, p95, mm (0.5 mm raster) | 6.12 | 9.03 | ≤ 4.0 |
| P10 | … maximum, mm (R7: left edge at (0.25, 95.25), the actuator-FET corner) | 13.8 | 15.3 | ≤ 8 |
| P11 | … p95 inside the outer GND pours, mm | 5.09 | 7.95 | ≤ 3.5 |

### Reference continuity of critical signals

| ID | Metric (definition) | R7 | R6 | Proposed R8 target |
|---|---|---:|---:|---|
| R1 | R6 net set (USB, HSE, QSPI, SPI1, IMU_CS), R6 mapping (F.Cu→In1 GND, B.Cu→In2 GND/3V3/3V3A): unreferenced centre-line length, mm, excluding 0.7 mm round the net's own vias (antipads) | 60.3 of 318.6 | 61.2 of 345.4 | ≤ 5 |
| R2 | … referenced share of all its length (own antipads count as unreferenced; R7 antipads 25.6 mm = 8 %) | 0.730 | 0.749 | ≥ 0.90 |
| R3 **I** | extended set (+ SWD, NRST, radio SPI) and mapping (+ In1→F GND, In2→B GND), unreferenced mm, as R1 | 115.9 of 733.6 | 152.2 of 614.2 | ≤ 15 |
| R4 | reference-edge crossings along critical tracks (extended) | 116 | 145 | ≤ 40 |
| R5/R6 | `critical_reference.py` R6 method on the board itself: samples / unreferenced (0.01 mm, centre + both edges) | 95,979 / 26,789 (27.9 %) † | 104,232 / 27,363 (26.3 %) | unreferenced ≤ 10 % |
| R7/R8 | same, `--extended` | 220,968 / 52,285 (23.7 %) † | 185,427 / 67,301 (36.3 %) | ≤ 10 % |
| — | R6 → R7 losses (`--dy 18`): lost / candidate-new; extended | 603 / 882; 2,312 / 4,325 † | — | report only |

### 7.7 A servo-feed copper (REQUIREMENTS F4; `dc_neck.py`, board stack-up)

Final grid 0.05 mm (the M3_R7 record's grid); the 0.1 mm column is the 5-minute quick mode for iterations.

| ID | Path | R, mΩ (0.05 / 0.1 mm) | Neck at 0.05 mm (layer, where) | Neck 0.1 mm | ΔT at neck (IPC-2152 fit) | 20 °C width | Proposed R8 target |
|---|---|---:|---|---:|---:|---:|---|
| D_raw | RAW_ACT Q121:5–9 → J122:2,5,8,11 | 3.71 / 3.74 † | 3.00 mm F.Cu, arm under J122 (x 21.55–24.45, y 80.6–81.0) † | 2.95 | 38 °C | 5.3 mm | R ≤ 3.7, neck ≥ 5.3 mm |
| D_bat | BAT_IN J1:1 → Q120:5–9 | 3.03 / 3.03 † | 3.82 mm In2, the arm where ACT_GATE's In2 run crosses (x 7.25–13.45, y 96.6–99.4) † | 3.66 | 30 °C | 5.6 mm | R ≤ 3.0, neck ≥ 5.6 mm |
| D_fet | ACT_FET_S Q120:1–3 → Q121:1–3 | 1.16 / 1.19 † | 2.65 mm B.Cu, Q120's source row (x 2.75–5.3, y 94.6–95.0) † | 2.64 | 44 °C | 5.3 mm | R ≤ 1.2, neck ≥ 5.3 mm |
| D_min **I** | smallest neck / its 20 °C width | 0.50 (ACT_FET_S) | | | | | ≥ 1.0 (MARGIN P1-9 asks ≥ 10 mm equivalent) |

Median cuts at 0.05 mm: RAW_ACT 5.64 mm, ACT_FET_S 3.07 mm, BAT_IN 7.98 mm. Current share at mid-path: RAW_ACT 100 %
F.Cu, BAT_IN 100 % In2, ACT_FET_S 100 % B.Cu (no layer shares the load). ΔT uses Brooks & Adam's fit to the IPC-2152
charts with no plane credit (an upper bound; about half with the In1 plane credit, Inference, M3_R7).

### Placement density

| ID | Metric | R7 | R6 |
|---|---|---:|---:|
| Q1 | top: courtyard area / board area (sum of courtyards); parts | 0.422; 106 | 0.449; 116 |
| Q2 | bottom: same | 0.163; 146 | 0.183; 134 |
| Q3 | densest 11.5 × 11.8 mm cell (courtyards clipped to the cell) | 0.97 (top, U1's cell) | 0.98 |

## 2. Where the complexity sits (R7 pressure points)

1. **Radio/GNSS interface** (30 nets RADIO_*/GNSS_*): 811 mm of copper for 557 mm of MST (+254 mm), 37 layer
   changes; all 8 survey no-GND layer changes, 20 of the 45 allowlist entries, the four longest critical routes
   (RADIO_NRST 85 mm / 4 vias, RADIO_DIO1 69 / 4, RADIO_BUSY 66 / 2, RADIO_MISO_MCU 62 / 2). Cause (R7 records):
   U1's free pins face the power section, so the interface runs in a left-edge B.Cu corridor with two via columns at
   x 9.4 / 10.0 whose merged antipads cut In1 slots at (8.8–11.2, y 47–51) and (8.9–10.5, y 26.7–30.7).
2. **Camera / power-switch / harness lines** (BAT_SW_RETURN 160 mm, BAT_SW_SOURCE 129, CAM_FAULT_N 92,
   CAM_PWR_EN 82 / 8 vias, CAM_MCU_TX 66 / 5, LOGIC_SOURCE_ST 11 vias, …): 10 nets, 699 mm for 394 mm of MST
   (+305 mm), 56 vias, 15 of the 29 leftovers. The `other` class carries 522 mm of excess length, half the board's.
3. **Servo lines**: 435 mm for 299 mm MST, 28 vias, 94 bends, 251 mm on In2; SERVO4_MCU alone 96 mm (+40 mm).
4. **In2 is a mixed layer, not a plane**: 1013 mm of tracks (901 mm signal, 39 nets: servo, harness, ARM1_SENSE
   52 mm, PYRO1_GATE_N 37 mm, sense lines), only 51 % of its area poured (3V3 10.6 %, BAT_IN 14.2 %, GND 23 %
   all in the RF strip, CAM_5V 2.6 %, 3V3A 0.5 %), 8 regions and 1581 mm of split edge. Consequence: B.Cu critical
   runs lose their reference over unpoured In2 — SPI1_SCK 20.3 of 24.1 mm, USB_DM 18.0 of 20.3, SWDIO 16.0 of 21.6,
   NRST 7.6 (B) + 11.5 (In2), SPI1_MISO 7.7 of 8.4 mm. Of the extended set's 116 mm, 72 mm lie over In2 gaps with no
   copper at all, 17 mm over In2 tracks, 7 mm over In2 BAT_IN, 20 mm (In2 tracks referencing B.Cu) over B.Cu
   tracks or voids. F.Cu runs over In1 are clean apart from their own antipads (0.8 mm elsewhere).
5. **GND stitching is concentrated in the RF strip**: 197 of 388 GND vias / plated GND holes sit in y 0–23.6
   (fence); the other 94 mm of board have 191. p95 distance to a GND via: 2.3 mm in the strip, 5.3 / 4.1 / 7.4 /
   7.8 mm in the next four 23.6 mm bands. 32 outer GND islands hang on one via; F.Cu GND is 41 islands, B.Cu 34.
6. **7.7 A necks** are 50–68 % of the 20 °C width; each is set by a part or a crossing (J122's pin columns and the
   pyro-block notch; Q120's gate pad and R120; ACT_GATE's In2 crossing), so only placement can widen them.
7. **Inherited from R6 and still there**: VCAP1 6.7 mm / 2 vias for 1.4 mm (4.9×), VCAP2 12.7 mm for 3.0 (4.2×),
   ARM1_SENSE_MCU 2.2 mm for 0.4 (5.5×) — tiny nets with huge ratios (a placement or pin-escape issue).

R7 already beats R6 on almost every row (the seven fix passes removed 114 signal vias, 577 mm of excess length,
46 no-GND layer changes, all In1 tracks and 1400 track segments). R8 has to beat R7, mainly through placement and
the layer plan rather than more local rework.

Regional density (y bands of 23.6 mm from the aft edge; top / bottom parts and courtyard share; GND-via p95):

| Band (y, mm) | Contents (R7) | Top parts, util | Bottom parts, util | GND vias, p95 distance |
|---|---|---|---|---|
| 0–23.6 | RF strip: J30/J31, U30, U31, limiter | 27, 0.37 | 8, 0.04 | 197, 2.3 mm |
| 23.6–47.2 | bucks U2/L1, U3 flash, U9 eFuse, U11, U13, J9 camera, J123 | 34, 0.38 | 39, 0.22 | 57, 5.3 mm |
| 47.2–70.8 | U1 MCU, Y1, U12 | 7, 0.36 | 37, 0.14 | 70, 4.1 mm |
| 70.8–94.4 | J3 USB, J122 servo, LS120, J2, U4/U5 (bottom), U7, Q124, J121/J124 | 32, 0.50 | 37, 0.24 | 39, 7.4 mm |
| 94.4–118 | Q120/Q121 (bottom), U8/L3, J1 battery | 6, 0.35 | 25, 0.18 | 25, 7.8 mm |

## 3. Definitions and conventions

- **Net classes** are route_check's `CLASSES` (rf, pyro, crystal, usb, spi, rfif, power, actuator; anything else
  `other`), with GND split out as `gnd`. "Signal" = every class but `power` and `gnd`. "Critical signal" =
  route_check `SIGNAL_CRITICAL` (rf, pyro, crystal, usb, spi, rfif).
- **Route metrics** come from route_check `net_route` (nets without a pour, ≥ 2 distinct pad points): copper =
  every track of the net (branches included); MST = octilinear minimum spanning tree of the pad centres (a Steiner
  tree can be shorter, so a multi-pad net can score below 1.0). Layer-changing via = a via where same-net tracks
  end on ≥ 2 layers.
- **Via classes**: `gnd_stitch` (GND, only pour fills attached: 338), `gnd_track` (GND with a GND track or pad: 40),
  `power_*` (114: layer change 57, pour-only 31, track-to-pour 25, other 1), `signal_*` (218: layer change 217,
  track-to-pad 1). All 710 vias are 0.3 mm drill (588 × 0.6 mm, 122 × 0.5 mm).
- **Bends**: heading change at a plain node (exactly two track ends of one net on one layer, no pad, via or T there):
  45°, 90°, acute (> 90°), collinear (< 0.5°, e.g. a width change). Turns inside pads and vias are not counted.
- **Planes**: zone fills as saved, unfractured, unioned per (net, layer). Void = hole in a fill; slot = void ≥ 2.5 mm
  long with mean width (area / length) < 1.6 mm. Perimeter counts outlines and voids.
- **Reference (survey, R1–R4)**: centre line sampled every 0.05 mm; a sample is referenced when it lies in the
  mapped reference fill; samples within 0.7 mm of the net's own via / PTH centre are its antipad, reported apart
  (R7: R6 set 25.6 mm, extended 53.1 mm). The repo tool (R5–R8) samples every 0.01 mm on the centre and both edges
  and counts antipads as unreferenced; use it for R6-method continuity, the survey for where and why.
- **Stitching distance**: Euclidean, 0.5 mm raster over the outline, to the nearest GND via or plated GND hole.
- **DC / IPC-2152**: `dc_neck.py` = `tools/dc_solve.py` (R7) + the fix-pass-7 equipotential-cut analysis (375 cuts,
  3–97 % of the drop); ΔT = K·I^a·W^b·Th^c (W, Th in mil; external 215.3/2.0/−1.15/−1.0, internal 200/1.9/−1.10/−1.52;
  35 µm outer, 30 µm inner). Assumes the R7 designators Q120, Q121, J1, J122 (kept by any re-layout of this schematic).
- **Placement density**: footprint courtyards (F/B.CrtYd) clipped to y bands (board height / 5) and a 4 × 10 grid.

## 4. Caveats

- The survey's no-GND count (S13 = 8) and route_check's `critical_via_no_gnd` (9) differ by PYRO1_GATE's layer change
  into TP122's pad, which the survey (tracks only) does not see. Gate on C6.
- route_check on a new board must use the R7 tools for like-for-like instance counts (C1, C2): its ALLOWLIST will
  match nothing there, so the instances show as failures and stale entries; count instances, not verdicts. A new
  repo's own route_check gives that board's gate verdict (G, C3–C5).
- R6 numbers are context: R6 is 18 mm shorter and has no RF strip.
- The DC rows need the board's stack-up block and filled zones. KiCad's Python has no numpy, so the pure-Python CG is
  slow: at 0.05 mm BAT_IN (438k cells, 7615 CG iterations) takes about 35–40 minutes, RAW_ACT about 15, ACT_FET_S 1;
  at 0.1 mm all three take 5 minutes (`DC_GRID=0.1`) and agree with 0.05 mm within 3 % (necks within 0.01–0.16 mm).
- Distances and coverages are geometry only; no field solve.

## 5. How to rerun on any board

Scripts (in `r8_design/baseline/`; KiCad 10 Python, no numpy; read-only on the board):

| Script | What it does |
|---|---|
| `run_survey.sh BOARD OUTDIR [BASE_BOARD]` | Everything below, then `scorecard.py` against `out/r7` |
| `survey_metrics.py BOARD [--tools DIR] [--json OUT] [--step 0.05]` | tracks, vias, routes, detours, bends, critical nets, buses, planes, reference, stitching, parts; prints the S/P/R/Q rows |
| `run_dc.sh BOARD OUTDIR [GRID]` | the three 7.7 A DC solves + neck cuts with `dc_neck.py` (default grid 0.05 mm) |
| `dc_neck.py` | `tools/dc_solve.py` of R7 with the equipotential-cut neck analysis (F8's `dc_ipc.py`) |
| `scorecard.py OUTDIR [--baseline DIR] [--md] [--json]` | assembles the scorecard from OUTDIR, ratios and the simplicity index vs a baseline |

```bash
cd <scratch>/r8_design/baseline
./run_survey.sh /path/to/candidate.kicad_pcb out/candidate r7_board/m3.kicad_pcb    # ~45 min (DC at 0.05 mm, gate)
DC_GRID=0.1 ./run_survey.sh /path/to/candidate.kicad_pcb out/cand_q                 # ~8 min: quick DC, gate
NO_DC=1 NO_GATE=1 ./run_survey.sh /path/to/candidate.kicad_pcb out/quick            # ~1 min: geometry + route_check
python3 scorecard.py out/candidate --baseline out/r7                                # table + index only
```

Environment: `TOOLS` (default the R7 worktree's `tools/`, keep it for comparable counts), `KICAD_PY`, `KICAD_CLI`,
`NO_DC`, `NO_GATE`, `DC_GRID`, `BASELINE` (default `out/r7`; `out/r7_quick` when `DC_GRID=0.1`, so DC rows are compared
on like grids). The board must be filled (zone fills saved) and keep
the R7 designators for the DC rows. Outputs per board: `survey.json` (full detail: per-net route table, critical-net
table, bus table, every pour, In1 voids and slots, reference by net and layer, stitching bands, density grids),
`route.json/.txt`, `cref_self*.json`, `cref_vs_base*.json`, `dc_*.txt`, `gate.txt`, `scorecard.md/.json`.

Baseline outputs: `baseline/out/r7/` (R7, complete, DC at 0.05 mm, with `scorecard.md/.json`), `baseline/out/r7_quick/`
(the same with DC at 0.1 mm) and `baseline/out/r6/` (R6, survey only, `scorecard_vs_r7.md`). `baseline/r7_board/` and
`baseline/r6_board/` are the surveyed copies of the two boards' `assembly_review` folders.
