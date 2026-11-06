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
`be81f40b…`'s (§4). **Round 3 fix pass (R12F3-TRI-05):** C25 / C26 became 15 pF (C1548), so the board is now
`66323cf0…`: the only change against `be81f40b…` is those two parts' Value, Datasheet, LCSC and Manufacturer Part
properties (8 lines; copper, placement, legends and zones identical, Measured by file comparison). Every routing metric
below is unchanged; the analyses, hot-plug run, fab package and cost were re-run on `66323cf0…` (§4 "Round 3", §5).
**Round 4 fix pass (R12F4-TRI-06):** R166's footprint description now names its real part (25121WF360LT4E, C168925,
0.36 Ω) through an R12-only override in `r12_parts.py`, so the board is now `db1f0999…`: the only change against
`66323cf0…` is that one `descr` line (copper, placement, fields, legends and zones identical; BOM and CPL byte-identical;
Gerbers identical except their creation date; Measured by file comparison). Stage D and the hot-plug model were re-run
on it to bind the hash (§4 "Round 4").

## 1. Result

| Item | Value |
|---|---|
| Board | `m3_design/r12/m3.kicad_pcb` SHA-256 `db1f09992fc257b85eeaa6c2f22c04455e17dadec1d4ac732a9f955305dd45ee` (round 4, R166 footprint description; `66323cf0…` in round 3 with C25 / C26 15 pF, `be81f40b…` before), 46 × 90 × 1.6 mm, built twice by `PYTHONHASHSEED=0 m3_design/r12_build.sh` with the same hash (Measured) |
| 100 mm fallback | `ef3194c01c7d77952fd88685080caf5ba1581a37cda45f79f8f362f0a32c0a02` on `r12-relayout-int` `4686580` (gated), the same copper except the forward zone |
| Copper | 1061 tracks, 318 vias, replayed from `m3_design/r12_routes.tsv` (Measured) |
| KiCad DRC | 0 violations, 0 unconnected, 0 parity (Measured) |
| `fit_check --profile r12` | OK; board 46 × 90 mm against the 100 mm R12 ceiling |
| `tools/check_r12.py` | every rule OK in the strict tier: S-1 … S-9, K-reference, K-region, K-plane, K-fill, K-neighbours, M-7, K-legends |
| `route_check --profile r12` | 0 failing, 3 allowlisted (3V3A, SPI1_MISO, QSPI_CLK; D-R12-96), 0 stale, 11 non-critical leftovers (informational; listed in `docs/R12_VALIDATION.md` "M2 routing deviations") |
| Fab | JLC BOM 58 lines, 178 JLC parts = 178 CPL rows (174 rebuilt from JLC footprints, 4 placement-only), F paste 579 flashes; manifest bound, with S-4 (`check_r12.py --only S-4 --bom --cpl`) among its content checks since R12F3-TRI-03. Round 3 changed the BOM's C25 / C26 line only (C1548 0402CG150J500NT 15 pF); the CPL is byte-identical to `871f77a`'s |
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

**Round 3 fix pass (R12F3-TRI-05 / -06 / -09, 2026-11-06; C25 / C26 15 pF, board `66323cf0…`).** `r12_budget.py` and
`r12_stageD.py` were changed; the board was rebuilt twice (same hash), and stage D and the hot-plug model were re-run on a
zone-filled copy whose SHA-256 equals the board's. Against the `be81f40b…` run, `stageD_budget.json` differs only in the
board hashes, Q124's gate bound and the PA6 corners (file comparison); every fire, EN, hold-up, rail, DC-solve, port,
U6 and IMU figure is unchanged.
* **HSE load capacitors 18 pF → 15 pF (TRI-05; design decision, cost-neutral).** AN2867: gm_crit = 4·ESR·(2πf)²·(C0 +
  CL)² against DS12110 Rev 8 Table 141's Gm_critmax 1.5 mA/V (startup, max). Y1 X322525MOB4SI (C9006), YXC YSX321SL
  sheet (LCSC's PDF, Datasheet): CL 12 pF (the C9006 listing: 12 pF, ±10 ppm, ±20 ppm over −40 … 85 °C), ESR ≤ 50 Ω
  (16–31 MHz), C0 ≤ 3 pF, drive level 10–200 µW; no motional capacitance is given. Circuit CL = C25·C26 / (C25 + C26) +
  stray 2–5 pF (AN2867's typical range, Inference). With 18 pF ±5 % (0402CG180**J**) CL was 10.55–14.45 pF and gm_crit
  **0.906–1.5027 mA/V: the +5 % / 5 pF corner exceeded 1.5** (the old "0.97–1.43, ok" took the nominal 18 pF only).
  With **15 pF ±5 % (C1548 FH 0402CG150J500NT, C0G)** CL is 9.125 / 11.0 / 12.875 pF (low / nominal 3.5 pF stray / high)
  and gm_crit **0.726–1.244 mA/V, 17.1 % under 1.5** (Calculation on the Datasheet maxima; stray Inference).
  Frequency: the load moves at most −2.9 / +0.9 pF from the crystal's 12 pF; with an assumed motional capacitance ≤ 10 fF
  and C0 0.5–3 pF (Inference: neither is on the sheet) the pulling is −26 … +120 ppm; with the ±10 ppm tolerance, ±20 ppm
  over temperature and 5 years at ±3 ppm / year the total stays under ±165 ppm against USB full speed's ±2500 ppm
  (12 Mb/s ±0.25 %) and far inside UART baud tolerance (Calculation / Inference). Drive level falls with the lower load.
  C1548 is JLC Basic, "Economic and Standard", 1.22 M in stock (Live 2026-11-06); its LCSC datasheet is byte-identical
  to C1549's (FH 0402CG series: C0G 0 ± 30 ppm/°C, resistance to soldering heat 265 ± 5 °C), so economic_parts' "OK"
  carries over. Price $0.0026 vs $0.0018 each (+$0.0016 per board; the parts total stays $32.78 per board). Same
  0402 land and nets: no copper change. The hot-plug inventory (`tools/r12_hotplug.py` DISCHARGE_PARTS) now names
  C1548 at 15 pF.
* **Q124 gate (TRI-06).** PE4's VOH is guaranteed only ≥ VDD − 0.4 V (DS12110 Rev 8 Table 158 p. 247, |IIO| 4 mA at
  1.62–3.6 V or 8 mA at 2.7–3.6 V). PE4's steady load is R127 1k plus R126 220R + R128 10k: about **3.56 mA** at the
  3V3 drift minimum, ≤ 3.87 mA at the drift maximum 3.4641 V with every resistor at its −1.67 % drift end, within the
  4 mA row (R12F4-TRI-02; this item first gave 0.32 mA, which left out R127). Q124 VGS ≥
  (3.2401 − 0.4) V × 9.9k / (9.9k + 222.2) = **2.778 V** at the 3V3 drift minimum with R126 / R128 1 % at their worst
  ends (was 3.170 V with VOH = VDD; Calculation / Inference: drift), still above the
  AO3400A's 2.5 V RDS(on) row (VGS(th) ≤ 1.45 V). `r12_windows.json`'s stage A placeholder: 2.761 V (from 3.222 V).
* **PA6 corners per branch (TRI-09).** The drop to D5 charged the whole converter current (2.264 A healthy) at U9 → D5's
  23.53 mΩ, but the camera buck U403 (1.243 A at four stalls) takes RAW_PROTECTED 10.81 mΩ from U9 and shares at most
  that much with D5's path. Each branch is now charged at min(its own, D5's) resistance from U9.6 (the mutual
  resistance of two sinks fed from one node is at most the smaller point resistance: maximum principle and
  reciprocity): U403 10.81 mΩ, U400 23.53 mΩ (its own is 59.63 mΩ), D5 + R92 23.53 mΩ. The RAW drop at D5 is 37.5 /
  38.4 / 38.7 mV (healthy / match shorted / match and leads shorted), so the whole drop is 15.8 / 16.2 / 16.4 mV smaller
  than the lumped figure, and is an upper bound (the margins below are lower bounds; Calculation on the DC solves /
  Inference: U9 RON, SS34 VF, load allocations).
* **Hot-plug (Simulation / Inference).** Re-extracted and re-run on `66323cf0…`: only C25 / C26's identity changed in the
  inputs (electrical SHA `dfba47cd…`, was `c1492655…`); the retained-output inventory falls by 8.3 pF to 1419.818 µF,
  bound 5.585 V unchanged; every row, failure count, minimum and slew figure is identical (0 / 2304 fail, minimum
  −14.255 V, fall 9.254 V/µs, rise 5.402 V/µs; file comparison).

**Round 4 fix pass (R12F4-TRI-02 / -03 / -06, 2026-11-06; board `db1f0999…`).** `r12_stageD.py` and `r12_budget.py`
were changed, and stage D and the hot-plug model were re-run on a zone-filled copy of the rebuilt board. Against the
`66323cf0…` run:
* `stageD_budget.json` differs only in the board hashes and Q124's gate-drive basis: PE4 (PYRO1_GATE_N) sources R127 1k
  to GND as well as R126 220R + R128 10k, so its steady load is **3.557 mA** at the 3V3 drift minimum 3.2401 V (was
  0.317 mA, which left out R127) and **≤ 3.868 mA** at the drift maximum 3.4641 V with every resistor at its −1.67 % drift
  end, within Table 158's 4 mA row (Calculation / Inference: drift). Q124 VGS ≥ 2.778 V is unchanged.
* `r12_windows.json`'s gate note now scopes the |VGS| > 12 V case to the whole time the bus is on, from the on-rail
  check until switch-off (Inference that no transient above 14.4 V occurs while it is on, pad or flight; it said "only
  enabled in flight"), and quotes PE4's load as about 3.6 mA (≤ 3.9 mA).
* Hot-plug (Simulation / Inference): re-extracted on `db1f0999…`; the electrical SHA is unchanged (`dfba47cd…`), only
  the inputs' board hash and so the inputs SHA changed (`1064def3…`, was `db6e6b21…`); every row and figure is identical
  (file comparison).

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
| PA6 margin to the trip top, four stalls (× 11 / with 1 % divider; lower bounds, per-branch drop since R12F3-TRI-09): healthy | +0.200 / +0.109 V | **+0.174 / +0.083 V** (+0.158 / +0.068 V with the lumped drop) | Calculation / Inference |
| … match shorted | +0.051 / −0.040 V | **+0.025 / −0.066 V** (lumped +0.008 / −0.083 V) | Calculation / Inference |
| … match and leads shorted | +0.007 / −0.084 V | **−0.019 / −0.110 V** (lumped −0.036 / −0.127 V; in the band at the nominal ratio too) | Calculation / Inference |
| Q124 VGS minimum (PE4 VOH ≥ VDD − 0.4 V, R12F3-TRI-06; PE4 load about 3.56 mA, ≤ 3.87 mA, within the 4 mA row, R12F4-TRI-02) | ≥ 3.17 V (VOH = VDD) | **≥ 2.778 V** (2.5 V row) | Calculation / Inference |
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
four stalls VLOGIC sits lower than before (about 26 mV with the per-branch drop of R12F3-TRI-09; the lumped figure was
41 mV). A fire into a shorted match with shorted leads can now reach PA6's trip band at the nominal divider ratio too
(−0.019 V), and with the 1 % divider a match short alone does (−0.066 V); healthy +0.174 / +0.083 V (lower bounds,
Calculation / Inference). Not a fire-path hazard (the fire current is unchanged); the firmware rule stands: a PA6 trip during the
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

## 5. Cost and stock (Live; `FAB_NET=1 m3_design/r12_fab.sh` on `66323cf0…`; the JLC BOM and CPL are byte-identical on `db1f0999…`, so the figures carry over)

`m3_design/r12/fab/cost_check_2.json` / `_5.json` 2026-11-06T17:55:07Z / 17:56:22Z; `stock_check_2.json` / `_5.json`
17:54:30Z / 17:55:45Z. 58 codes (22 Extended / 36 Basic), **none short and none thin** at 2 or 5 boards (orderable =
min(stock, canPresaleNumber), an Inference about JLC's field). Parts $32.78 per board. Feeder **21 × $3.07 = $64.47** per
order: `tools/jlc_cost.py` now exempts JLC Preferred Extended codes on Economic PCBA (R12F3-TRI-08; JLC PCBA FAQ 7,
fetched 2026-11-06: Preferred Extended parts "are exempt from the Feeders Loading fee for Economic PCB assembly"); the one
such code is D120's BAT54C C37704 (`preferredComponentFlag` true, Live), so 22 → 21 charged codes (the old run charged
it: $67.54). **REQUIREMENTS M3 metric: $65.02 at 2 boards, $45.68 at 5 boards** against the $84.41 cap (was $66.55 /
$46.29).

All-in (Calculation on the Live figures; setup / stencil $9.71; SMT joints $0.0016 × 579 pasted pads per board; THT
$0.0164 × 4 joints per board plus $3.58 labour per order; bare PCB $25.10, the 46 × 100 mm quote of cost_study.md, Live
2026-11-04: that 90 mm costs no more is an Inference; X-ray below; shipping, tax and attrition excluded):

| Order | JLC parts | Feeder | Setup + stencil | SMT joints | THT joints + labour | Bare PCB | X-ray, U1 only | **Total** | Per board |
|---|---|---|---|---|---|---|---|---|---|
| 2 boards | $65.57 | $64.47 | $9.71 | $1.85 | $3.71 | $25.10 | $3.28 | **$173.69** | $86.84 |
| 5 boards | $163.91 | $64.47 | $9.71 | $4.63 | $3.91 | $25.10 | $8.20 | **$279.93** | $55.99 |

Was $176.75 / $282.99 (2026-11-06T10:07Z, 22 charged codes), $173.39 / $274.59 (2026-11-05) and $173.47 / $274.79
before the X-ray line (R12F2-TRI-13): JLC price movement, the X-ray fee and the Preferred Extended waiver; the only BOM
change is C25 / C26 (C1548, +$0.0016 per board).

**X-ray inspection (R12F2-TRI-13; JLC PCBA price page https://jlcpcb.com/help/article/pcb-assembly-price, read
2026-11-06).** "X-ray inspection is required for components such as BGA, QFN, and other leadless packages" whose joints
are not visible after SMT, charged per component piece: $1.64 / pc for 1–10 pcs, $0.82 / pc for 11–50 pcs, the same for
Economic and Standard PCBA, no waiver listed. Which R12 parts JLC counts is decided on its quote:

* **Certain (BGA, named by JLC): U1** STM32H743VIH6 TFBGA-100, 1 per board: 2 / 5 pcs, **$3.28 / $8.20** per order
  (Calculation), the line in the table above.
* **Probable (leadless ICs with joints under the body; that JLC counts them is an Inference): U4** LSM6DSVE LGA-14,
  **U5** MS5607 (8 pads under the body), **U6** FXLS90322 HLQFN-16, **U9** TPS259470A VQFN-HR (RPW). With U1 that is 5
  per board: 10 pcs, **$16.40** at 2 boards (total $186.81, $93.40 per board); 25 pcs at 5 boards, **$20.50** if the
  11–50 price applies to all 25 or **$28.70** if the first 10 are at $1.64 (how JLC applies its tiers is an Inference;
  total $292.23–300.43, $58.45–60.09 per board).
* **Possible (Inference): D402** ESD103 TSLP-2 and **Y1** 3225 ceramic crystal, also leadless with pads under the body:
  7 per board, at most $22.96 / $57.40 per order with every piece at $1.64.

Against the plan's targets (≤ $170 at 2 boards, ≤ $295 at 5; `docs/M3_R12.md` "Cost and stock"): the 2-board order is at
least **$3.69** over with U1 alone (was $6.75 before the waiver) and $16.81 over with the five probable parts; the
5-board order stays under $295 with U1 alone ($279.93) and is $292.23–300.43 with the five, so under $295 at the low
tier reading and over it at the high one (Calculation; the count and tier are Inferences until JLC's quote). Confirm
the X-ray count on JLC's quote before ordering.

## 6. Hashes (Measured, SHA-256; final board)

| File | SHA-256 |
|---|---|
| m3_design/r12/m3.kicad_pcb | db1f09992fc257b85eeaa6c2f22c04455e17dadec1d4ac732a9f955305dd45ee |
| m3_design/r12_legends.tsv | 882188a1a5af503cd41aae5cf37f7695161e95ab99d856b7a80f7b931d61fc69 |
| m3_design/r12_routes.tsv | 1faf23700fdce206be2c0779a9c64c87cb62fa36260bdc1f8c31230fac127e92 |
| m3_design/r12_place.tsv | 282d169a07f5ed799da9a87ffe0ffb5cf42555499f65f694bb3e0c76442129fa |
| m3_design/r12/fab/m3_bom_jlc.csv | 1cb9bd250235e853dd73ff9940c7c1bbc53f3b7674bbdd121c5de651a6ea4d7f |
| m3_design/r12/fab/m3_cpl_jlc.csv | c9a2aa28514cf4c16fe70be2da92050baa1ae44f37c9577175a7fe637e9a40e1 |
| m3_design/r12/fab/m3_fab_manifest.json | 730f619ef800a2977610bd5b4d07b4f28285044152c9248802ea0fb3375c9ea2 |
| m3_design/r12/fab/m3_gerber.zip | f4306259a96cdc35245e82a4c26e27aee61a457c77127b940a709cea2ffbaef6 |
| m3_design/r12/fab/cost_check_2.json | 6db6c43439203205fa37eab6fc82b59fb0e82c953ea7fece7633af6a297b9828 |
| m3_design/r12/fab/cost_check_5.json | 0d2760e94c29d50628ecd60182006255d586b98f17ca4376eb03951ba82eb722 |
| m3_design/r12/fab/stock_check_2.json | 6d7987faa472f648f3458466cfee417476857e87b97117b16b159e0f8f1a5dda |
| m3_design/r12/fab/stock_check_5.json | 700d9a86cd596ef2896630a56ca215487fcaade222e4fea2a0aea169060bdb05 |

The Gerbers and assembly PDFs carry their creation date, so they change on every export; the manifest binds them.

## 7. Gate and what is not verified

`PYTHONHASHSEED=0 tools/check.sh` on this tree (NUMPY_PY with numpy, so the hot-plug numerics self-tests ran): **exit 0** (Measured, 2026-11-06; the only change after it was this sentence). Round 2 fix lanes A / B (R12F2-TRI-03,
-06, -07, -08, -10, -11, -13, branch `r12f2-AB`): two builds gave the same board `be81f40b…` and unchanged schematic and
netlist hashes, `tools/test_r12_stageD.py` passed (8 tests) and `PYTHONHASHSEED=0 tools/check.sh` exited 0 (Measured,
2026-11-06; no numpy interpreter, so the hot-plug numerics self-tests skipped, as did 6 tests in each of two self-test
runs; the hot-plug files did not change). Round 3 fix lanes A–D (R12F3-TRI-03, -04, -05, -06, -08, -09, -13, branch
`r12f3-AD`): C25 / C26 15 pF; two builds gave the same board `66323cf0…` (copper unchanged); stage D and the hot-plug
model re-run on it; the fab package re-exported and re-bound with S-4 in its content checks, and priced with the
Preferred Extended waiver (one `FAB_NET=1` run); `tools/test_r12_stageD.py` passed (11 tests) and
`PYTHONHASHSEED=0 tools/check.sh` exited 0 (Measured, 2026-11-06). Round 4 fix lanes A–D (R12F4-TRI-01, -02, -03,
-04, -06, -07, -08, branch `r12f4-fix`): R166's footprint description (board `db1f0999…`, two builds with the same hash,
only that line changed); the drift bounds in `pin_table.tsv`, `circuit.json`'s pin notes, PE4's load and the gate note;
stage D and the hot-plug model re-run; `tools/test_r12_fab.py` (15 tests) and `tools/test_r12_stageD.py` (13 tests) now
run in `check.sh`; `zones.json` W5 closed at y 90 and `zone_guard.py` refuses geometry outside Edge.Cuts;
`PYTHONHASHSEED=0 tools/check.sh` with NUMPY_PY exited 0 (Measured, 2026-11-06; the only change after it was this
sentence). Not verified: any physical, electrical or firmware test;
JLC DFM; the vehicle fit of the 90 mm board (O-R12-28); AN2606 (O-R12-23); two consecutive clean stage F rounds on the
re-layout (round 2 found 16 real errors and round 3 found 14, R12F3-TRI-01 … -14). After any
later copper change: re-run the legend aid if needed, then `m3_design/r12_stageD.py` and `tools/r12_hotplug.py`.
