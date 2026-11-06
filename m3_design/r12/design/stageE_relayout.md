# R12 AVA re-layout: placement, zone routing, the 90 mm outline and the re-run analyses (2026-11-06)

Decisions D-R12-93 … D-R12-99 are in `R12_DECISIONS.md`. Branches: `r12-relayout-int` (the 100 mm re-layout, gated at
`4686580`, board `ef3194c0…`), `r12-relayout-90` (the 90 mm board, `871f77a`, board `be81f40b…`) and
`r12-relayout-docs` (this record). Nothing is ordered. Labels (AGENTS §2.5): **Measured** = read from the CAD or a tool
run on it; **Calculation** = arithmetic on CAD copper and datasheet values; **Simulation** = the numerical hot-plug
model; **Inference** = anything resting on an unmeasured or estimated input; **Live** = JLC's public component API with
its UTC timestamp. No physical test was run. Coordinates are board mm (x east, y forward from the aft edge).

**Board hash and routing metrics.** Every board hash and routing metric in this file is the final board's
(`be81f40b…`), built after the signal-only AVA cleanup `871f77a` (no power, pyro or placement change; §2). The analyses
in §4 were run on the pre-cleanup board `cc5b66db…` and re-run on `be81f40b…`; the recorded files and figures are
`be81f40b…`'s (§4).

## 1. Result

| Item | Value |
|---|---|
| Board | `m3_design/r12/m3.kicad_pcb` SHA-256 `be81f40be9d5b5ea60b3f1484324dab4dc999446dd75f493dd41e7f6982ddae8`, 46 × 90 × 1.6 mm, built twice by `m3_design/r12_build.sh` with the same hash (Measured) |
| 100 mm fallback | `ef3194c01c7d77952fd88685080caf5ba1581a37cda45f79f8f362f0a32c0a02` on `r12-relayout-int` `4686580` (gated), the same copper except the forward zone |
| Copper | 1061 tracks, 318 vias, replayed from `m3_design/r12_routes.tsv` (Measured) |
| KiCad DRC | 0 violations, 0 unconnected, 0 parity (Measured) |
| `fit_check --profile r12` | OK; board 46 × 90 mm against the 100 mm R12 ceiling |
| `tools/check_r12.py` | every rule OK in the strict tier: S-1 … S-9, K-reference, K-region, K-plane, K-fill, K-neighbours, M-7, K-legends |
| `route_check --profile r12` | 0 failing, 3 allowlisted (3V3A, SPI1_MISO, QSPI_CLK; D-R12-96), 0 stale, 11 non-critical leftovers (informational; listed in `docs/R12_VALIDATION.md` "M2 routing deviations") |
| Fab | JLC BOM 58 lines, 178 JLC parts = 178 CPL rows (174 rebuilt from JLC footprints, 4 placement-only), F paste 579 flashes; manifest bound. The BOM and CPL are byte-identical to `871f77a`'s; the Gerbers and PDFs differ only by export timestamps |
| `tools/check.sh` | exit 0 on this tree (§7) |

## 2. How the copper is built now (D-R12-96)

* **Zones.** `m3_design/r12_aid/zones/zones.json` defines five work zones: W1 aft power / pyro / camera / servo, W2 east
  power / USB / J2 / RAW trunk, W3 the U1 escape and core, W4 the sensor stack and the CA corridor, W5 the ports, port
  buck, buzzer and LEDs. The W1 / W2 border is y 17.0–17.6, so the moved 3V3 buck cell lies in W2.
* **Fragments.** Each zone's copper is its own table, `zones/r12_routes_W1.tsv` … `_W5.tsv`. `zones/merge.py` merges them
  in order into `m3_design/r12_routes.tsv` (an exact duplicate row or a via placed twice is an error), and
  `m3_design/r12_route.py` replays that table in the build as before; nothing searches in the build.
* **Frozen sources.** The stage C copper is kept as `r12_aid/r12_routes_f1.tsv`. The battery entry, the bus switch and
  fire path, the camera-buck internals, SERVOn_OUT, PE4's gate run, PYRO1_CONT, HSE and the port-cell internals were
  reused verbatim (S-3 / S-8 / S-9 = 0, Measured); D-R12-96 lists the runs that were redrawn.
* **Tools (not run by the build).** `zone_check.py` (a fragment stays inside its zone and hand-offs meet),
  `zone_guard.py` (reports frozen rows outside their zone: 6–7 frozen pyro rows sit outside W1, exempt by the plan),
  `export_geom.py` (pads and keep-outs for drafting), `kref.py` (K-reference diagnostic), `draw.py` (renders),
  `score.py` (the plan's metrics), `escape_W3.tsv` (U1's escape and the zone hand-offs).
* **Joins.** 21 of route_check's 31 review-only collinear nodes are at the zone joins y 17.5 and y 45.4, where two
  fragments meet (Measured).

**Metrics (Measured; plan "now" → 100 mm → 90 mm, target).** Total vias 414 → 320 → **318** (≤ 290); GND vias 182 →
150 → **149** (≤ 140); signal vias 175 → 100 → **100** (≤ 95); 3V3 vias 41 → 36 → **36**; diagonal share 36 % → 16.4 % →
**17.1 %** (≤ 15 %); signal track 2168 → 2053.9 → **1947.6 mm** (≤ 2050); In2 track 239 → 137.4 → **137.4 mm** (≤ 130);
worst routed / MST LED_RED 1.97 → **NRST 1.96** (then QSPI_CLK 1.63, USB_DM 1.57, QSPI_IO0 1.57, CC2 1.54) (≤ 1.35);
most vias on one signal net SERVO2 11 → **VLOGIC_SENSE 4** (≤ 3). The misses are open item O-R12-29.

**Signal-only AVA cleanup (`871f77a`, board `cc5b66db…` → `be81f40b…`; Measured).** W3: the AUX pair now drops beside U3
at (37.9, 54.4) / (38.9, 53.6) with one GND partner at (37.9, 52.95), and its B lanes run at 1.0 mm pitch, turning
together to the existing vias (35, 79.7) / (36, 80); the GND via (42.2, 53.6) is removed. W1: SERVO3's B run to R152.1
continues west along y 7.6, down x 22.6 and through a via at (22.1, 13.75) into the pad. AUX_TX / AUX_RX routed / MST
1.51 / 1.49 → 1.32 / 1.33, SERVO3 1.31. Diagonal share 16.9 % → 17.1 %, signal track 1959.8 → 1947.6 mm (score.py;
all track 2116.7 mm), 1062 → 1061 tracks; via counts, In2 length and the top five ratios are unchanged. Why 15 % and
the ratio targets are not reachable in signal-only scope: route_check's tiny_jog and local_bump rules block trading
signal diagonals for orthogonal runs, and only about 176 of the 360 mm of diagonal copper is signal copper (the cleanup
agent's measurement). route_check: still 0 failing, 3 allowlisted, the same 11 leftovers.

## 3. Post stage on the 90 mm board (Measured on `be81f40b…`)

50 legends (every contact legend, the connector words, J2's SWD rows, the revision, pin-1 dots); 111 designators shown
(45 on the bottom under their part) and 76 hidden, kept on F.Fab:
C13 C16 C17 C18 C21 C22 C26 C81 C83 C94 C120 C129 C410 C420 C432 C433 C444 D121 D402 R12 R14 R33 R61 R81 R83 R84 R89
R92 R93 R94 R100 R101 R104 R105 R106 R110 R111 R119 R120 R122 R123 R126 R127 R128 R129 R130 R133 R151 R153 R154 R155
R156 R157 R162 R163 R164 R165 R167 R175 R178 R180 R400 R401 R431 R433 R434 R435 R440 R441 R460 R461 R462 R464 R470
R471 U4. Library-graphics notes (r12_post's contract): D120's circle 0.10 mm from R130.1, U403's and U400's pin-1
circles 0.092 mm from C433.2 / C400.2 (under JLC's 0.15 mm; JLC clips silkscreen at openings, Inference). J122's harness
note stays optional (D-R12-81).

## 4. Analyses re-run on the 90 mm board (`be81f40b…`)

Run on a zone-filled copy whose SHA-256 equals the board's (the saved fill matched a native refill, Measured):
`PYTHONHASHSEED=0 <KiCad python3> -I -B m3_design/r12_stageD.py FILLED --source-board m3_design/r12/m3.kicad_pcb`
(about 50 min now: two nets are solved on the whole board, below) → `stageD_budget.json`;
`<KiCad python3> -I -B tools/r12_hotplug.py --extract FILLED`, then `<python3 with numpy> -I -B tools/r12_hotplug.py` →
`hotplug_inputs_r12.json` / `hotplug_results_r12.json`. "Before" is the round-1 board `f60d8239…` (100 mm, stage C
copper). Labels as in `stageD_analysis.md`. Both analyses were then re-run on the final board `be81f40b…` (after the
signal-only cleanup): `stageD_budget.json` and the hot-plug files committed are that run's. Against the `cc5b66db…` run
only the RAW_PROTECTED solves moved (U9 → U400 / U403 / D5 +0.08 mΩ each: SERVO3's new via (22.1, 13.75) sits in the
In2 RAW island's west piece, Inference from the 3-cell drop in the solve), the PA6 margins by ≤ 0.2 mV and the 3V3 solves by ≤ 0.002 mΩ; the hot-plug network,
electrical SHA `c1492655…` and every hot-plug figure are identical (Measured, file comparison).

**Script inputs changed for the new copper (`m3_design/r12_stageD.py`).**
* `FULL_BOARD_NETS = ('RAW_PROTECTED', '3V3')`: the DC solve of these nets uses the whole board instead of the terminals'
  box plus a margin. RAW_PROTECTED's two In2 island pieces join only at y 0–7.6 (D-R12-95), aft of every terminal box,
  and the port buck is reached by the 57.6 mm × 0.6 mm B.Cu trunk along x 45.2 (Measured). For 3V3, the box solve
  (+ 6 mm, and + 12 mm) found L1's and U6's copper in two separate pieces (Measured: no conductance between them), so
  the In2 plane path between them leaves the box. Both are still upper bounds on R (copper outside the board is none).
* The port-supply docstring now describes the 90 mm feed: R400's 0.15 mm sense run joins the 1.0 mm feed at
  (39.4, 79.3), 3.2 mm from L400.2, and the feed drops through C406's vias into the forward In2 PORT_4V8 island.
* Everything else reads the board as before (fire paths, terminals, rails, gate copper, IMU placement).

**Round 2 fix pass (R12F2-TRI-06 / -07 / -08, 2026-11-06; script changes, the board is unchanged).** `r12_stageD.py`
was changed and re-run on the same zone-filled copy of `be81f40b…` (its SHA-256 equals the board's):
* **U400 IN starts at VIN only (TRI-06).** TPS563208 (DDC) pin 3 is VIN and pin 5 is EN; on R12 EN is tied to VIN, and
  the 0.25 mm F.Cu stub U400.5 → U400.3 ((42.6, 69.3) → (42.6, 70.2) → (43.55, 71.15), 2.24 mm) ends at the VIN pad's
  edge and carries only EN's µA input current. Stage D started the path at both pins, so it rated the stub at the
  2.05 A port-buck input and added its 4.41 mΩ to the path's series copper. The path and the U9 → U400 DC solve now use
  pin 3 alone (the solve is unchanged at 59.63 mΩ: the two pins were one sink).
* **RAW_PROTECTED load paths end at the In2 island (TRI-07).** A load path now ends at the vias whose In2 pad touches
  the RAW_PROTECTED fill, (44.5, 16.4) and (45.2, 16.4) for the trunk, where the current enters; ending at every via made
  both U400 IN and D5 IN take the whole 57.6 mm trunk. A track on more than one load path is rated at the summed current
  (`stageD_budget.json` `rails_shared`), with the RAW budget currents at the four-stall fire point beside it.
* **Q120 / Q121 VGS from ACT_FET_S (TRI-08).** The gate divider (R119 / R120 / C120) hangs on ACT_FET_S, the common
  source node, which sits I_fire × RDS(Q120) below BAT_IN during the fire. At four stalls: 1.250 A × 73.5 mΩ = 91.9 mV,
  ACT_FET_S 5.629 V, **VGS −4.576 V** (was −4.652 V from BAT_IN), **0.076 V** beyond the AO3401A's −4.5 V RDS(on) row
  (was 0.152 V); during a fire at BAT_IN 6.0 / 7.4 / 8.4 V −4.80 / −5.94 / −6.76 V; with the bus on before the fire
  (no fire current) −4.88 / −6.04 / −6.87 V, and the enable times 27.4 / 14.7 / 11.4 ms and the 14.41 V ±12 V corner
  are unchanged. With a shorted match at four stalls |VGS| is 4.40 V (4.35 V with the leads shorted too), below the
  −4.5 V row, so the shorted-match FET figures use an RDS(on) under the real one (a fault case, not the fire budget).
  Calculation / Inference: the Q120 hot factor (60 mΩ × 1.225) and the 0.1 V Q122 drop are Inference. No fire-current
  figure changes (the loop already counts Q120 / Q121 at 73.5 mΩ each).
* Every other figure in `stageD_budget.json` is unchanged (file comparison).

**Hot-plug (Simulation / Inference).** `tools/r12_hotplug.py` models BAT_IN / BAT_DAMP as an extracted copper network
and RAW_PROTECTED as one lumped node (the retained-output inventory), so the RAW trunk has no topology to update in this
tool. The BAT_IN / BAT_DAMP copper is frozen (D-R12-96): the 12-edge network is identical to round 1's (Measured on the
extract; the electrical SHA changes to `c1492655…` only because moved parts' pad positions are in it). Result:
**0 / 2304 required cases fail; minimum U9 IN −14.255 V (0.1 µH corner) against −15.0 V; steepest fall
9.254 V/µs against 10; rise 5.402 V/µs**; cold limit, convergence, C88 topology and component checks pass;
retained-output bound 5.585 V at 1419.8 µF (2 s). Identical to round 1. The six variant runs (`hotplug_variants_r12.json`)
were not re-run: they depend only on that unchanged network and the parts.

| Figure | Before (`f60d8239…`) | 90 mm (`be81f40b…`) | Label |
|---|---|---|---|
| Fire loop / four-stall current | 4.726699 Ω; 1.250000 A at BAT_IN 5.7209 V (+11.1 % over 1.125 A) | **unchanged** (fire copper frozen) | Calculation / Inference |
| GND fire return Q124 → J1.2 (DC solve) | 2.594 mΩ | **2.585 mΩ** (< 5 mΩ allowance; the loop keeps 5 mΩ) | Calculation |
| EN / chatter | single drop-out 8.13 ms at 5.7209 V; bench-rule worst-corner limit 7.56 ms; turn-on 27–114 ms | **unchanged** (same parts and four-stall point) | Calculation / Inference |
| Hold-up from a battery break / from the PA6 trip | 2.23–6.12 ms unshed, 6.68–11.43 ms shed / 0.47–1.72 ms | **unchanged** (constant-power model) | Calculation / Inference |
| C84 → U2 copper (DC solve, not in the hold-up model) | 47.8 mΩ | **4.14 mΩ** (C84 beside U2, D-R12-94) | Calculation |
| RAW_PROTECTED U9 → U400 / U403 / D5 | 5.79 / 7.45 / 5.33 mΩ | **59.63 / 10.81 / 23.53 mΩ** (the port buck and D5 hang off the B trunk) | Calculation |
| VLOGIC D5 → U2 / D6 → U2 | 13.87 / 30.51 mΩ | **6.43 / 8.47 mΩ** | Calculation |
| PA6 margin to the trip top, four stalls (× 11 / with 1 % divider): healthy | +0.200 / +0.109 V | **+0.158 / +0.068 V** | Calculation / Inference |
| … match shorted | +0.051 / −0.040 V | **+0.008 / −0.083 V** | Calculation / Inference |
| … match and leads shorted | +0.007 / −0.084 V | **−0.036 / −0.127 V** (now in the band at the nominal ratio too) | Calculation / Inference |
| PORT_4V8 L400 → J410 / J420 / J440 | 73.6 / 74.8 / 69.6 mΩ | **11.50 / 13.07 / 6.88 mΩ** | Calculation |
| Ports under 0.561 A (J420 lowest), initial / drift | ≥ 4.561 / 4.529 V | **≥ 4.596 / 4.563 V** (J410 4.597 / 4.564, J440 4.599 / 4.567); at R10's 1.9 A design current ≥ 4.578 / 4.546 V | Calculation / Inference |
| Ports at no load (ceiling 5.0 V) | ≤ 4.938 / 4.972 V | unchanged (regulator window) | Calculation / Inference |
| U6 VCC at U2's 1 A (O-R12-22) | ≥ 3.258 / 3.228 V | **≥ 3.253 / 3.223 V**, margin 118 / 88 mV over 3.135 V ((12.53 + 4.85) mΩ × 1 A) | Calculation / Inference |
| CAM_5V L401 → J9 | 9.51 mΩ | unchanged (camera cell frozen) | Calculation |
| PD10 PORT_SENSE | (PA4) 3.10–3.39 V / 3.07–3.43 V | 3.100–3.392 V initial, 3.064–3.430 V drift, ≤ 0.036 V off | Calculation; drift Inference |

**Port window floor (D-R12-83 / A-8).** With the local 90 mm feed the copper bound is 3.9–7.3 mV at the 0.561 A budget
(was 39–42 mV on the 72–75 mΩ east-edge trunk), so the lowest port pin is ≥ 4.596 V initial and ≥ 4.563 V at the drift
corner, 63 mV over the LR900-F's 4.5 V (a project-record Inference). R401 stays 0.1 % (D-R12-83): the copper was never the whole problem, since the
stage D divider (1 % R401, R404 4.7k) put the regulator window's own drift minimum at 4.489 V, and D-R12-83 found no 1 %
pair that holds 4.5–5.0 V there (stageD_analysis.md §10, Calculation / Inference),
under 4.5 V before any copper drop. The integrator's estimate (Calculation / Inference from a squares count: J420 13.9,
J410 12.6, J440 8.6 mΩ) agrees with the DC solve to within 1.7 mΩ.

**PA6 during a fire (O-R12-07).** D5 now takes RAW_PROTECTED from the trunk via (45.2, 29.2), 23.5 mΩ from U9, so at
four stalls VLOGIC sits about 41 mV lower than before. A fire into a shorted match with shorted leads can now reach
PA6's trip band at the nominal divider ratio too (−0.036 V), and with the 1 % divider a match short alone does
(−0.083 V). Not a fire-path hazard (the fire current is unchanged); the firmware rule stands: a PA6 trip during the
20 ms pulse is logged, not treated as a battery loss.

**IPC-2152 (Calculation on CAD widths; the rise is the long-conductor fit with no plane credit, an upper bound,
Inference).** Paths over 30 °C at R10's design currents:
* U9 IN 0.4 mm pin entry 1.3 mm, 55.2 °C at 2.9 A; U9 OUT 0.3 mm 1.6 mm 76.8 °C and 0.45 mm via stubs 1.0 mm 48.2 °C
  (each stub carries about half): unchanged frozen pin-entry copper.
* J410 / J420 / J440 pin-2 feeds 0.3 mm, 1.9 / 1.9 / 0.6 mm, 33.0 °C at the 1.9 A design current (negligible at the
  0.561 A budget): unchanged port-cell copper.
* **The shared RAW trunk (R12F2-TRI-07, O-R12-31):** the 0.6 mm B.Cu run (45.2, 16.4) → (45.2, 29.2), 12.8 mm, and
  the 0.6 mm F.Cu link (44.5, 16.4) → (45.2, 16.4), 0.7 mm, carry U400's and D5's currents together. At the summed
  design inputs, 2.054 + 1.294 = 3.348 A, the rise is **46.1 °C**; at U9's own 2.9 A path current, which the sum
  exceeds, 34.6 °C; at the board's fire-time budget, 0.605 A (ports 3.463 W) + 0.413 A (logic 1.4 W, microSD 0.825 W,
  D5 0.135 W) = 1.018 A at the four-stall 5.721 V, **4.3 °C** (IPC-2152 upper bound; Calculation / Inference: the
  load allocations, 80 % efficiency and D5's drop are Inference). 0.87 mm would hold 30 °C at 3.35 A. The F link
  joins two In2-joined vias, so the island carries part of its current in parallel. 30 °C is this list's threshold, not
  a gate rule: widen in a later copper pass or accept (O-R12-31); no copper change here.
* **Withdrawn (R12F2-TRI-06):** stage E's "U400 IN 0.25 mm F.Cu link U400.5 → U400.3, 2.24 mm, 47.5 °C at 2.05 A" was a
  mis-attribution: that link is the EN-to-VIN stub (above), which carries no load current.
* The rest of the trunk, (45.2, 29.2) → (45.2, 74.0), and U400.3's 0.6 mm feed through C400.1 carry U400's current
  alone: 17.4 °C at 2.05 A. U400 IN's series copper from VIN to the In2 drop is **50.37 mΩ** (was 54.8 mΩ with the
  stub's 4.41 mΩ; the parallel C400 links are summed in series, an upper bound); with D5's current in the shared
  11.06 mΩ it drops about 0.12 V at the design inputs and about 35 mV at the budget (Calculation / Inference). D5 IN
  is now D5.2 → (45.2, 29.2) → the shared trunk: 12.37 mΩ (stage E's 50.5 mΩ took the trunk to C400 as well), 6.9 °C
  on its own 1.294 A.
* Everything else is under 30 °C: VLOGIC D5 → U2 1.0 mm 3.8 °C, U2 OUT 0.6 mm 16.5 °C at 2.0 A, U400 OUT 0.8 / 1.0 mm
  10.7 / 8.3 °C at 1.9 A, CAM_5V ≤ 8.9 °C.

**IMU placement (Calculation on CAD).** U4 (23.0, 41.6) and U6 (23.0, 34.4), both top, rotation 180: lever arm to the
roll axis x = 0.000 mm for both (U6 was +4.5 mm). D-R12-54's axis maps are unchanged.

**Firmware binding.** The repository has no R12 binding note or executable binding (`m3_firmware/assembly_binding.py`
and `build.py` carry none for R12; grep `r12_binding`: no match), so there is nothing to regenerate. `pin_table.tsv`
column `r12_net` is the reviewed pin map.

## 5. Cost and stock (Live; `FAB_NET=1 m3_design/r12_fab.sh` on `be81f40b…`)

`m3_design/r12/fab/cost_check_2.json` / `_5.json` 2026-11-06T10:07:00Z / 10:08:18Z; `stock_check_2.json` / `_5.json`
10:06:21Z / 10:07:40Z. 58 codes (22 Extended / 36 Basic), **none short and none thin** at 2 or 5 boards (orderable =
min(stock, canPresaleNumber), an Inference about JLC's field). Parts $32.78 per board; feeder 22 × $3.07 = $67.54 per
order. **REQUIREMENTS M3 metric: $66.55 at 2 boards, $46.29 at 5 boards** against the $84.41 cap.

All-in (Calculation on the Live figures; setup / stencil $9.71; SMT joints $0.0016 × 579 pasted pads per board; THT
$0.0164 × 4 joints per board plus $3.58 labour per order; bare PCB $25.10, the 46 × 100 mm quote of cost_study.md, Live
2026-11-04: that 90 mm costs no more is an Inference; X-ray below; shipping, tax and attrition excluded):

| Order | JLC parts | Feeder | Setup + stencil | SMT joints | THT joints + labour | Bare PCB | X-ray, U1 only | **Total** | Per board |
|---|---|---|---|---|---|---|---|---|---|
| 2 boards | $65.56 | $67.54 | $9.71 | $1.85 | $3.71 | $25.10 | $3.28 | **$176.75** | $88.38 |
| 5 boards | $163.90 | $67.54 | $9.71 | $4.63 | $3.91 | $25.10 | $8.20 | **$282.99** | $56.60 |

Was $173.39 / $274.59 (2026-11-05) and $173.47 / $274.79 before the X-ray line (R12F2-TRI-13): JLC price movement and
the X-ray fee only, the BOM is unchanged.

**X-ray inspection (R12F2-TRI-13; JLC PCBA price page https://jlcpcb.com/help/article/pcb-assembly-price, read
2026-11-06).** "X-ray inspection is required for components such as BGA, QFN, and other leadless packages" whose joints
are not visible after SMT, charged per component piece: $1.64 / pc for 1–10 pcs, $0.82 / pc for 11–50 pcs, the same for
Economic and Standard PCBA, no waiver listed. Which R12 parts JLC counts is decided on its quote:

* **Certain (BGA, named by JLC): U1** STM32H743VIH6 TFBGA-100, 1 per board: 2 / 5 pcs, **$3.28 / $8.20** per order
  (Calculation), the line in the table above.
* **Probable (leadless ICs with joints under the body; that JLC counts them is an Inference): U4** LSM6DSVE LGA-14,
  **U5** MS5607 (8 pads under the body), **U6** FXLS90322 HLQFN-16, **U9** TPS259470A VQFN-HR (RPW). With U1 that is 5
  per board: 10 pcs, **$16.40** at 2 boards (total $189.87, $94.94 per board); 25 pcs at 5 boards, **$20.50** if the
  11–50 price applies to all 25 or **$28.70** if the first 10 are at $1.64 (how JLC applies its tiers is an Inference;
  total $295.29–303.49, $59.06–60.70 per board).
* **Possible (Inference): D402** ESD103 TSLP-2 and **Y1** 3225 ceramic crystal, also leadless with pads under the body:
  7 per board, at most $22.96 / $57.40 per order with every piece at $1.64.

Against the plan's targets (≤ $170 at 2 boards, ≤ $295 at 5; `docs/M3_R12.md` "Cost and stock"): the 2-board order is at
least **$6.75** over with U1 alone (was quoted as $3.47 over) and $19.87 over with the five probable parts; the
5-board order stays under $295 with U1 alone ($282.99) and reaches $295.29–303.49 with the five (Calculation; the count
is an Inference until JLC's quote). Confirm the X-ray count on JLC's quote before ordering.

## 6. Hashes (Measured, SHA-256; final board)

| File | SHA-256 |
|---|---|
| m3_design/r12/m3.kicad_pcb | be81f40be9d5b5ea60b3f1484324dab4dc999446dd75f493dd41e7f6982ddae8 |
| m3_design/r12_legends.tsv | 882188a1a5af503cd41aae5cf37f7695161e95ab99d856b7a80f7b931d61fc69 |
| m3_design/r12_routes.tsv | 1faf23700fdce206be2c0779a9c64c87cb62fa36260bdc1f8c31230fac127e92 |
| m3_design/r12_place.tsv | 282d169a07f5ed799da9a87ffe0ffb5cf42555499f65f694bb3e0c76442129fa |
| m3_design/r12/fab/m3_bom_jlc.csv | 1dc4be76ea1e8650ceac6da423585439f51d4ad01f321a283d65393fa8eb44c2 |
| m3_design/r12/fab/m3_cpl_jlc.csv | c9a2aa28514cf4c16fe70be2da92050baa1ae44f37c9577175a7fe637e9a40e1 |
| m3_design/r12/fab/m3_fab_manifest.json | b225ac70cea8bb8c218a2bf3d8d27809d8cf30c715d629906ef7d550d674345f |
| m3_design/r12/fab/m3_gerber.zip | 889a38ed582f14fe2a200bd961bbb5a9eedc660e922f5d4b0f2abd1aa7ecaf7c |
| m3_design/r12/fab/cost_check_2.json | 573c9b78387a501144605bbb5fbbbc9dcf9f2035ad008cd8d9b8cf71e2a0297a |
| m3_design/r12/fab/cost_check_5.json | fbbbf0fa947b0535483020a6ca76dd04f57153ad0287a250faf71691a8a8fb4f |
| m3_design/r12/fab/stock_check_2.json | 88aecb3ee80a0a032ab4596fbb74c5e03d7472a013b6ead68e6007256a635535 |
| m3_design/r12/fab/stock_check_5.json | c561d4ea0a91d58a070b97da350c013dd3c98b52350c088e017df963badbb2e9 |

The Gerbers and assembly PDFs carry their creation date, so they change on every export; the manifest binds them.

## 7. Gate and what is not verified

`PYTHONHASHSEED=0 tools/check.sh` on this tree (NUMPY_PY with numpy, so the hot-plug numerics self-tests ran): **exit 0** (Measured, 2026-11-06; the only change after it was this sentence). Round 2 fix lanes A / B (R12F2-TRI-03,
-06, -07, -08, -10, -11, -13, branch `r12f2-AB`): two builds gave the same board `be81f40b…` and unchanged schematic and
netlist hashes, `tools/test_r12_stageD.py` passed (8 tests) and `PYTHONHASHSEED=0 tools/check.sh` exited 0 (Measured,
2026-11-06; no numpy interpreter, so the hot-plug numerics self-tests skipped, as did 6 tests in each of two self-test
runs; the hot-plug files did not change). Not verified: any physical, electrical or firmware test;
JLC DFM; the vehicle fit of the 90 mm board (O-R12-28); AN2606 (O-R12-23); a stage F review of the re-layout. After any
later copper change: re-run the legend aid if needed, then `m3_design/r12_stageD.py` and `tools/r12_hotplug.py`.
