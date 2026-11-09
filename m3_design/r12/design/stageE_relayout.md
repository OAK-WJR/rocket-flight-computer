# R12 AVA re-layout: placement, zone routing, the 90 mm (now 83 mm) outline and the re-run analyses (2026-11-06)

Decisions D-R12-93 … D-R12-99 are in `R12_DECISIONS.md`. Branches: `r12-relayout-int` (the 100 mm re-layout, gated at
`4686580`, board `ef3194c0…`), `r12-relayout-90` (the 90 mm board, `871f77a`, board `be81f40b…`) and
`r12-relayout-docs` (this record). Nothing is ordered. Labels (AGENTS §2.5): **Measured** = read from the CAD or a tool
run on it; **Calculation** = arithmetic on CAD copper and datasheet values; **Simulation** = the numerical hot-plug
model; **Inference** = anything resting on an unmeasured or estimated input; **Live** = JLC's public component API with
its UTC timestamp. No physical test was run. Coordinates are board mm (x east, y forward from the aft edge).

**Reading guide.** Current board: `a1e65bb4…` (round 10, D-R12-170 … -173). §1, §3, §5 and §6 give current
facts; dated round paragraphs preserve their historical values. The original re-layout metrics were
`be81f40b…`'s, built after the signal-only AVA cleanup `871f77a` (no power, pyro or placement change; §2). The analyses
in §4 were run on the pre-cleanup board `cc5b66db…` and re-run on `be81f40b…`; those original figures are
`be81f40b…`'s (§4), superseded by the current round 10 block. **Round 3 fix pass (R12F3-TRI-05):** C25 / C26 became 15 pF (C1548), so that round produced
`66323cf0…`: the only change against `be81f40b…` is those two parts' Value, Datasheet, LCSC and Manufacturer Part
properties (8 lines; copper, placement, legends and zones identical, Measured by file comparison). Routing metrics were unchanged in that round; the analyses, hot-plug run, fab package and cost were re-run on `66323cf0…` (§4 "Round 3", §5).
**Round 4 fix pass (R12F4-TRI-06):** R166's footprint description now names its real part (25121WF360LT4E, C168925,
0.36 Ω) through an R12-only override in `r12_parts.py`, so that round produced `db1f0999…`: the only change against
`66323cf0…` is that one `descr` line (copper, placement, fields, legends and zones identical; BOM and CPL byte-identical;
Gerbers identical except their creation date; Measured by file comparison). Stage D and the hot-plug model were re-run
on it to bind the hash (§4 "Round 4"). **AVA polish pass (D-R12-121 … -124, branch `r12-polish`):** a signal-only
routing polish (port UART bundle, NRST under J2, three leftover fixes, two redundant GND vias) made `68e6b650…`; its
metrics are §2 "AVA polish pass". **Round 5 fix pass (D-R12-125 … -133, R12F5-TRI-01 … -22):** the fire-net copper,
five pyro-cell parts, U6's corner lands, GPS_TX's pad exit and the J121 pours changed, making `6e874d4e…` (§2 "Round 5",
§4 "Round 5"). **Round 6 fix pass (D-R12-134 … -143, R12F6-TRI-01 … -17, verifier V-1 … V-5, PACK_FLT):** R136 (the
cold pull-up's series resistor), R95 and D95 (U9's FLT to PC13) were added, R131 became 5.1 kΩ, R132 / R175 / R120
moved, three GND vias moved and the pours pulled back from the pack-energy nets, making `f26dfef1…` (§2 "Round 6", §4
"Round 6"). **Round 7 fix pass (D-R12-144 … -151, R12F7-TRI-01 … -17):** the outline shrank to 46 × 88 mm (the port
row, its cells and the port buck 1.85–2 mm aft, forward supports at y 82.1), the FMEA I-5 copper moved (the RAW_PROTECTED
In2 island, R104, four vias, a camera UART lane), U9's two in-pad debris segments went and PYRO1_GATE got one entry into
Q124.1, making `82eddc69…` (§2 "Round 7", §4 "Round 7"). Round 8 made `418e5ea9…` (D-R12-152 … -160). Round 9 makes `a02a6181…`, and lane C's J430 bypass (D-R12-169) `ae22387d…`; round 10 makes `a1e65bb4…` (D-R12-171). §1, §3, §4, §5 and §6 describe the current board. The metrics
paragraph and the cleanup paragraph of §2 keep `be81f40b…`'s figures as history.

## 1. Result

| Item | Value |
|---|---|
| Board | `m3_design/r12/m3.kicad_pcb` SHA-256 `a1e65bb4109ba5db7821cc1ec8b1ae6c3db88d5f9bd1f1700eb0cb182721e59a`, 46 × 83 × 1.6 mm. Lane P reports two byte-identical builds (Measured, `b20de30`); D-R12-171 |
| 100 mm fallback | `ef3194c01c7d77952fd88685080caf5ba1581a37cda45f79f8f362f0a32c0a02` on `r12-relayout-int` `4686580` (gated), the same copper except the forward zone |
| Copper | 1093 tracks, 348 vias (162 GND) on `a1e65bb4…` (Measured from saved board text); round 9 `ae22387d…` had 1088 / 345 / 160 |
| KiCad DRC | 0 violations, 0 unconnected, 0 parity (Measured) |
| `fit_check --profile r12` | OK; board 46 × 83 mm against the 100 mm R12 ceiling |
| `tools/check_r12.py` | Every rule OK (lane P); S-10 has 80 connected victims plus 45 unconnected IC-pin nets, 199 exceptions: 51 fire-net, 114 BAT_IN, eight VLOGIC_SENSE, 26 IC-pin pairs. K-power ten exceptions; U5 GND / R13.2 / VSSA doubled, R12.2 / C30.1 recorded. M-8 seven DFM queries (C407 2.305 mm added) |
| `route_check --profile r12` | 0 failing, 2 allowlisted (3V3A, SPI1_MISO), 0 stale; no pad_debris / pad_slit. Current M2 recount: 41 review residuals and eight noncritical leftovers, R12_VALIDATION |
| Fab | 59 JLC BOM lines, 183 parts / CPL rows, no owner BOM; 593 F-paste flashes (Measured from Gerber). Manifest bound, lane P content checks pass; cost §5 |
| `tools/check.sh` | Exit 0 reported by lanes P `b20de30` / A `3d96eb5`; not run by this records lane (§7) |

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
* **Tools (not run by the build).** `zone_check.py` (builds a scratch board from the fragments and sorts its DRC /
  parity, route_check and check_r12 findings into zones by position through `zone_guard.inside`; it does not test
  containment), `zone_guard.py` (lists each fragment row with a track end or via outside its zone's polygon and owned
  strips, or outside the board outline; current counts on `a1e65bb4…`, D-R12-171: **W1 6 / W2 0 /
  W3 9 / W4 0 / W5 0**, Measured. W3's nine are BAT_FAULT_N ×3, GND ×2 at (25.99, 44.76),
  ARM1_SENSE, ACT_EN_MCU ×2 and BUZZ_DRV hand-offs. The 85 mm fragments were 6 / 0 / 37 / 0 / 8;
  C460 / C461's eight rows now belong to W3, and zones match the J430 bay / 83 mm outline).
  `test_zone_check` asserts these counts and is now run by `check.sh` (10 tests OK, lane P).
  `export_geom.py` (pads and keep-outs for drafting), `kref.py` (K-reference diagnostic), `draw.py` (renders),
  `score.py` (the plan's metrics), `escape_W3.tsv` (U1's escape and the zone hand-offs).
* **Joins.** 21 of route_check's 30 review-only collinear nodes are at the zone joins y 17.5 and y 45.4, where two
  fragments meet (Measured on `82eddc69…`; this bullet said 31 until D-R12-151, R12F7-TRI-11: the count went 31 → 30 in
  round 6).

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

**AVA polish pass (D-R12-121 … -124, 2026-11-06, branch `r12-polish`; board `db1f0999…` → `68e6b650…`; Measured).**
Signal copper only, edited in the zone fragments W2 / W3 / W4 and merged by `merge.py`; no frozen row, power copper or
placement changed. Each step was checked with `zone_guard.py` and `zone_check.py` (DRC, route_check, check_r12) before
the next. Renders: `draw.py` before / after (the owner's view).
* **Port UART bundle (D-R12-121).** RADIO_TX / RADIO_RX / GPS_TX / GPS_RX run straight on B at x 24.3 / 24.8 / 25.29 /
  25.8; GPS_TX's via (25.65, 58.8) → (25.29, 59.41) removes GPS_RX's 0.8 mm zig-zag; the RADIO west run is y 78.6 / 79.1.
* **NRST under J2 (D-R12-122).** The 12.0 mm F loop round J2's north is replaced by a 3.4 mm B run under the TC2030
  pads between vias (30.8, 44.85) and (34.2, 44.85) (the footprint keeps tracks off F between its pads). NRST 35.37 →
  28.20 mm, routed / MST 1.96 → 1.56, vias 2 → 4.
* **Leftovers and GND vias (D-R12-123).** CC1's and LED_YEL's tiny jogs and I2C1_SDA's neck are gone (11 → 8
  leftovers); the redundant GND vias (19.6, 65.0) and (21.6, 59.6) are removed (every nearby signal via keeps a
  partner within 1.5 mm).
* **Not changed (D-R12-124):** C24's position (no 0402 site with a GND via near E1), QSPI_CLK / IO0, the USB pair, CC2,
  VLOGIC_SENSE and the In2 sense lanes, with the measured reasons there.

| Metric (plan target) | `db1f0999…` | `68e6b650…` |
|---|---|---|
| Vias (≤ 290) | 318 | 318 |
| GND vias (≤ 140) | 149 | 147 |
| Signal vias (≤ 95) | 100 | 102 |
| Diagonal share of all track (≤ 15 %) | 17.06 % (361.2 / 2116.7 mm) | 16.95 % (357.4 / 2109.2 mm) |
| In2 track (≤ 130 mm) | 137.4 mm | 137.4 mm |
| Non-plane track (score.py) | 1947.6 mm | 1940.1 mm |
| Tracks | 1061 | 1053 |
| Worst routed / MST (≤ 1.35) | NRST 1.96, QSPI_CLK 1.63, USB_DM 1.57, QSPI_IO0 1.57, CC2 1.54 | QSPI_CLK 1.63, USB_DM 1.57, QSPI_IO0 1.57, NRST 1.56, 3V3A 1.55, CC2 1.54 |
| Most vias on one signal net (≤ 3) | VLOGIC_SENSE 4 | VLOGIC_SENSE 4, NRST 4 |
| route_check non-critical leftovers | 11 | 8 |

**Round 5 fix pass (D-R12-125 … -133, 2026-11-06; board `68e6b650…` → `14b82d39…` (lane P) → `6e874d4e…` (lane P2);
Measured).** Fire-net copper and parts, in the fragments W1 / W3, `r12_place.tsv` and the DRU generator (D-R12-125):
PYRO1_GATE leaves In2 (TP122 to (14.8, 42.4) on F; both gate vias, the In2 run and their two GND partners removed),
R131 turned, D120 moved below it with a new 3V3 via (5.65, 51.2), PYRO1_OUT re-run north of D120 and its J121.1 → Q124
trunk 0.15 mm west to x 5.45, R173 0.1 mm forward with CONT_MID redrawn, C13 turned at (17.4, 50.0) with new vias
(17.82, 49.2) / (15.05, 50.45); every pour ≥ 0.5 mm from J121.1 / J121.2. U6's eight corner lands chamfered (D-R12-129).
GPS_TX leaves K9 in two segments (D-R12-130). check_r12 S-10 gates the fire-net gaps (D-R12-126). Metrics (score.py
and a track count): vias 318 → **314** (GND 147 → 145, signal 102 → 100, 3V3 36); diagonal share 16.95 → **16.69 %**
(351.3 / 2104.1 mm); In2 track 137.4 → **132.0 mm**; non-plane track 1940.1 → 1932.9 mm; tracks 1053 → 1050; the worst
routed / MST ratios (QSPI_CLK 1.63 …) and the most vias on one signal net (VLOGIC_SENSE, NRST 4) are unchanged.
route_check: 0 failing, 3 allowlisted, 8 leftovers, `pad_end_offcentre` 292 → 285, every other count unchanged.
`zone_guard` with W3 / W5 brought to the 90 mm layout (D-R12-132): W1 6 rows, W3 8, W2 / W4 / W5 none.

**Round 6 fix pass (D-R12-134 … -143, 2026-11-07; board `6e874d4e…` → `3f9579fa…` (lane P) → `6a1c99e0…` (lane P3) →
`f26dfef1…` (lane P4); Measured).** In the W1 fragment and `r12_place.tsv`: R136 at (4.1, 50.2) with its own 3V3 via
(2.65, 50.2), the D120.1 3V3 track and via (5.65, 51.2) removed (D-R12-134); R132 at (17.17, 32.2) rotation 0 with a
new feed (15.4, 32.2)–(16.74, 32.2), R175 turned to 270° with ARM1_SENSE re-routed down x 18.1, R120 at (6.53, 26.95)
with ACT_FET_S / ACT_GATE re-routed, the pours pulled back 1.04 mm from the pack nets (D-R12-137); R95 at (18.15, 22.89)
rotation 270 with vias (18.15, 21.65) / (18.15, 24.1), D95 at (20.77, 24.27) rotation 180 with its 3V3 via (21.77,
25.1), and three GND vias nudged ((11.5, 9.6) → (11.55, 9.6), (12.2, 8.1) → (12.12, 8.1), (15.3, 16.75) → (15.3, 16.8);
D-R12-138). Metrics (score.py and a track count, this records lane): vias 314 → **317** (GND 145, 3V3 36 → 37, signal
100 → 102); diagonal share 16.69 → **16.59 %** (349.4 / 2106.2 mm); In2 track **132.0 mm** (unchanged); non-plane track
1932.9 → 1934.1 mm; tracks 1050 → 1057; the worst routed / MST ratios (QSPI_CLK 1.63 …) and the most vias on one signal
net (VLOGIC_SENSE, NRST 4; U9_FLT 3) are unchanged. route_check: 0 failing, 3 allowlisted, 8 leftovers (BAT_FAULT_N's
`extra_vias` entry is now U9_FLT's), `pad_end_offcentre` 285 → 276, review-only collinear nodes 31 → 30 (43 residuals),
every other count unchanged. `zone_guard` on the committed fragments: W1 6 rows, W3 8, W2 / W4 / W5 none (D-R12-142
counts each row once).

**Round 7 fix pass (D-R12-144 … -147, 2026-11-07; board `f26dfef1…` → `82eddc69…`, lane P `bc7af8b`; Measured).**
`shrink88.patch` (place, routes, planes, legends; synced into the W2 / W3 / W5 fragments, `merge.py` reproduces
`r12_routes.tsv`): 46 × 88 mm, the port row and its cells 1.85–2 mm aft, the port buck 2 mm, the PORT_4V8 In2 island
y 80.6–87.5, the forward supports (3.5, 82.1) / (42.5, 82.1) (D-R12-144). The I-5 copper (D-R12-145): the RAW_PROTECTED
In2 island `22.3,0 46,0 46,16.8 32.6,16.8 32.6,7.0 26.15,7.0 26.15,23.4 19.8,23.4 19.8,14.6 22.3,14.6`, C8's 3V3 via to
(42.6, 19.0), R89's to (20.6, 13.45), R104 to (28.8, 7.6), the CAM_MCU_RX B lane to x 31.0, R431.2's GND via to (31.75,
11.85). In W1: the two U9 in-pad rows deleted and PYRO1_GATE's R126.2 run one 45° track (11, 44.1)–(10.2, 43.3) into
R128.1 (D-R12-147). Metrics (score.py and a track count, the records lane): vias 317 → **316** (GND 145, 3V3 37,
signal 102); diagonal share 16.59 → **16.64 %** (347.8 / 2090.4 mm); In2 track **132.0 mm**; signal track 1918.6 mm
(score.py); tracks 1057 → 1048; the worst routed / MST ratio (QSPI_CLK 1.63) and the most vias on one signal net
(VLOGIC_SENSE, NRST 4) unchanged. route_check: 0 failing, 3 allowlisted, the same 8 leftovers, `pad_end_offcentre`
276 → 267, `power_via_no_gnd` 12 → 13, the 43 review-only residuals (30 collinear, 13 in-pad) unchanged, and the new
`pad_debris` / `pad_slit` rules clean. `space.py`: 82.1 % of 1 mm cells occupied; the east pocket (x 40.25–44.75,
y 51.5–64.25, 57.4 mm²) stays empty for the reason in `r12_place.tsv`'s `@OUTLINE` row (D-R12-144).

**Round 8 copper and layout (D-R12-152 … -155, -159; Measured on `418e5ea9…`).**
LS120 moves **(7.2, 67.4) → (5.8, 66.4)**; BUZZ_OUT **11.448 → 9.048 mm**, 2.40 mm shorter,
no added via; fit_check passes (Measured, lane P). The west-forward pocket after the move is
**x 0–9.5, y 71.25–78.25, ≈ 66.5 mm² usable** on `418e5ea9…` (R12F9-TRI-14 correction):
bounded by LS120 at y 71.19, TP88 at x 9.55 and the support's 3.8 mm hardware zone. The former 96.0 mm²
rectangle included support space; `space.py`'s 112 mm² rectangle below also includes the support.
No cell routes through that corner, and board length is set by the x 20–24 column measured in round 7;
no part was moved into the pocket. The earlier 43.5 mm² reason is withdrawn (D-R12-144 amended).
`space.py` reports **82.1 % occupied**, west strip x 0–4 **36.9 %** (was 33.8 %), largest empty
rectangle **112 mm² at (0, 72, 6, 87)** (Measured). W3 / W5 notches and W5's boundary now match 88 mm;
W5 has zero rows outside (was 31), and `test_zone_check` asserts the 46 × 88 outline and W5 containment.
W1 / W3 retain six / eight pre-existing outside rows; zone_guard was not added to check.sh (lane P).
R15 / D9 / C32 designators moved to B under their parts, C84's east, LS120's Fab text with its body.

I-5 victims, measured gaps and CAM_EN protection: D-R12-152 / -153. K-power, doubled taps and
remaining six single vias: D-R12-154, owner rows 42–44. Current counts are in §1; prior-round routing
statistics below retain their original board bindings.

**Round 9 layout (D-R12-162, lane L `3ccb3a53…`; geometry unchanged on `a02a6181…`; lane C, D-R12-169, then moves U3 and its fan 0.15 mm west to (38.35, 54.45) and C460 / C461 into the east strip).**
U3 is (38.5, 54.45), J430 (36, 65.15), both rotation 90. U3 takes the pocket east of U1 under J3;
the push-pull socket sits south, mouth east. The buck takes J430's old bay. SD and QSPI pin ordering
made the originally proposed south-U3 placement require more crossings. QSPI_CLK is **12.94 mm, 0 vias**
(19.40 mm before); its allowlist entry is removed. SD SCK / MOSI / MISO / CS are
**27.41 / 25.96 / 26.26 / 33.64 mm**, **0 / 0 / 2 / 2 vias** (Measured). CS/MISO B hops are under the socket;
masked F copper and tented vias under it are an Inference (drawing has no keep-out).
Forward row and supports move 3 mm aft: outline **46 × 85 mm**, supports y **79.1**.
**Round-10 correction:** the alleged divider/C22 **0.22 mm** limit was false: actual gaps to
R400 / R401 **0.690 mm**, R404 **0.820 mm** (Measured on `ae22387d…`). D-R12-171 reaches 83 mm;
C407/L400 **0.110 mm** remains, while J410/L400 **0.385 mm** sets the new length limit. Card envelope x **30.30–45.90 mm**, inside the edge (Measured).
RAW trunk ends at (45.2, 71.1) / (44.2, 72.1), then 1.0 mm F along y 72.1 west to C400.
`space.py` with support-hardware zones: **90.2 %** occupied (3528 / 3910), largest empty rectangle
**36 mm²** at x 0–2, y 33–44 (Measured, lane L). The 66.5 mm² pocket above is 88 mm-board history.

**Round 10 layout (`a1e65bb4…`, D-R12-171; Measured, lane P).** Forward ports/cells/supports move
another **2 mm aft**, ports **y 79.35**, supports **(3.5, 77.1) / (42.5, 77.1)**. C406 moves **2.5 mm aft**
to **(13.1, 70.825)** into the empty pocket x 10.75–14.75, y 61.5–70.25; the proposed 1.5 mm move
left C406.1 touching the relocated RADIO_RX via, while 2.5 mm gives **1.000 mm**. L400 **0.3 mm west**
to **(17.8, 73.2)**, TP88 **0.5 mm west** to **(9.7, 73.0)**. AUX / PORT_SENSE / TP74 vias are re-seated
clear of the RAW F run (edge y 72.6). C406 feed/sense join **(14.9, 72.3)**; island vias
**(14.9, 76.2) / (14.9, 77.0)**, In2 PORT_4V8 island **y 75.6–82.5**.
Courtyard gaps: J410–L400 **0.385 mm** (length limit without moving the buck column), L400–C410
**0.040**, L400–C407 **0.110**, C406–R450 / R451 **1.265**, C406–L400 **1.21**, C406–TP88 **1.16**,
TP88–LS120 **0.763**, J420 / J410–C407 **0.36 mm**. Seven short-edge DFM queries, with C407 added at
**2.305 mm** from the forward edge; port courtyards max y **82.42**, gap **0.58 mm**. No new
whole-board density or largest-empty-rectangle measurement is claimed; the 90.2 % figure above belongs to 85 mm.

## 3. Post stage on the 83 mm board (Measured on `a1e65bb4…`)

50 legends; 107 designators shown, 85 hidden on F.Fab:

C123 C126 C127 C129 C13 C15 C16 C17 C18 C19 C21 C22 C25 C26 C29 C410 C420 C432 C433 C444 C460 C81 C83 C94 D121 D402 D436 R10 R100 R101 R104 R105 R106 R110 R111 R12 R120 R122 R123 R126 R128 R129 R130 R133 R136 R14 R151 R153 R154 R155 R156 R157 R162 R163 R164 R165 R167 R175 R178 R180 R401 R404 R431 R433 R434 R435 R436 R440 R441 R450 R451 R464 R470 R471 R61 R81 R83 R84 R89 R92 R93 R94 R95 TP74 U4.

Moved-part legends were re-placed using the drafting aid's functions; the full aid could not place U9's
pin-1 dot and four contact legends. Round 10 shifts forward legends 2 mm aft, then AUX +0.8 mm, RADIO +1.78 mm and GPS +1.5 mm in y to clear pads / preserve ownership; J410 is now on B at (18.125, 80.54).
J2 6:NC is on the bottom at (30.85, 43.93). K-legends passes (lane P). The hidden set changed by
+C15, C19, C29, R10, R136, R404, R451 and −R460, R461, R462 (D-R12-162). Lane C (D-R12-169) hides C460 (no legal
spot in the east strip), puts C461's designator on the bottom under its part and moves U3's pin-1 dot to (43.36, 55.91).

## 4. Analyses re-run on the 90 mm board (`be81f40b…`)

**Current round 10 (`a1e65bb4…`, 46 × 83 mm; D-R12-170 … -173).** Stage D's board and source
SHA-256 both equal `a1e65bb4109ba5db7821cc1ec8b1ae6c3db88d5f9bd1f1700eb0cb182721e59a`, using the
as-saved fills. Lane P re-ran the DC solves and hot-plug; lane A changed the PA6 leakage and branch-current
model, leaving those DC solves unchanged. Hot-plug electrical SHA `ebc5fa57…`: **2304 / 2304 pass**,
minimum **−14.255 V**, every result row unchanged (Simulation / Inference). Lane A reports 42 stage-D
tests and the full gate passing; lane P reports two byte-identical builds (Measured, reports).

- **PA6 during a fire (Calculation / Inference; D-R12-164, -172).** R60 100k / R61 10k are
  0.1 % 25 ppm/K (C852472 / C190095); the band stays **0.425–0.455 V**. The model includes PA6's
  ±250 nA FT_xx leakage through R60 ∥ R61 (DS12110 Rev 8 Table 60; applying the digital-input row
  to analog mode is an Inference), U9 RON **45 mΩ** maximum, 70 °C feed/copper bounds and D5's
  self-consistent current. SS34 VF 0.25–0.45 V, pack/load, temperature and drift remain Inference.
  Healthy margins to the trip top, nominal / initial / drift: **+0.0497 / +0.0405 / +0.0251 V**.
  Shorted-match / match-and-leads margins at drift: **−0.1264 / −0.1708 V**.
  Four-stall VLOGIC ranges: healthy **5.0797–5.2797 V**, match shorted **4.9282–5.1282 V**,
  match and leads shorted **4.8838–5.0838 V**. Trip windows, nominal / initial / drift:
  **4.650–5.030 / 4.6415–5.0392 / 4.6274–5.0546 V**; trip bottom above U9 turn-off through D5:
  **+0.0979 / +0.0894 / +0.0264 V**. Drift band room is **0.4226–0.4573 V (34.7 mV)**;
  the adopted band fits. O-R12-17's trip-bottom calculation stays closed; READY calibration remains open.
  Rule 4 logs any trip beginning during a commanded fire without battery-loss shutdown, shed,
  state change or pulse truncation.

Fire loop **4.726884 Ω**, four-stall **1.249586 A at 5.71921 V**, margin **11.07 %** over 1.125 A;
GND return **2.672 mΩ** (Calculation / Inference: pack/load and hot factors; DC return Calculation).
Q120 / Q121 VGS **−4.5675 / −4.5584 V**. D5 current equals U2 input current **0.4380 A**;
D5 loss **0.1971 W**, other converter load **13.015 W**. Healthy converter current **2.3523 A**,
BAT_IN → D5 drop **0.1861 V**, RAW share **0.0572 V** (Calculation / Inference).

- **EN timing and chatter (Calculation / Inference; D-R12-150, -156, -170, -172).** At four-stall
  BAT_IN **5.71921 V**, single drop-out immunity is **8.116 / 7.595 ms** initial / drift; the
  worst-corner periodic limit is **7.548 / 7.072 ms**. C87's X7R allowance, leakages and drift are Inference.
  R12's bench pass rule is **under 6.9 ms total open time in every sliding 100 ms window**, recorded at
  **≥ 10 kS/s under flight-level vibration**, with **U9 on for the whole run at 5.72 V** (D-R12-170).
  The retained converter-power-at-BAT_IN convention gives the figures above. Charging the pack the full
  solver current, including U9 and copper losses, gives **5.7073 V / 1.24699 A** and an EN limit of
  **6.984 ms** at drift (`fire.pack_load_sensitivity`, Calculation / Inference), below the former 7 ms
  line; the 6.9 ms line covers both conventions with margin. This is a Minor stacked-corner margin,
  with no circuit change. The JSON's `en.bench_rule` and `margin_over_7ms_line_ms` retain the old
  7 ms comparison; D-R12-170 supersedes the procedural string.
  Turn-on remains **30.3–131.5 ms initial / 29.9–135.9 ms drift** over C87 0.72–1.265 × 220 nF.

PA6-trip hold-up unshed, nominal / initial / drift: **0.486–1.854 / 0.480–1.870 / 0.471–1.897 ms**;
shed at drift **1.410–3.545 ms**. Battery-break unshed **2.226–6.099 ms**, unchanged
(Calculation / Inference: constant-power loads, D5 VF, C84 allowance, 3.8 V endpoint, leakage, drift).

RAW DC solves at 20 °C: U9 → U400 / D5 / U403 **74.58 / 25.93 / 15.67 mΩ** (Calculation on CAD).
Shared B trunk budget **1.0680 A / 4.69 °C** IPC rise; U400 feed budget drop **45.78 mV**,
design **147.49 mV** unchanged (Calculation / Inference: allocations, temperature, IPC upper bound).
U400 VIN **5.4964 / 5.4157 V** at four stalls / 6.0 V pack; 580 kHz held outputs **4.464 / 4.749 V**
and **4.398 / 4.678 V**, 200 kHz **5.106 / 5.204 V** and **5.030 / 5.127 V** (310 / 220 ns).
U403 VIN **5.5462 V**, drop **0.1730 V**, camera-pin estimate **4.9016 / 4.9996 V**
(Calculation / Inference: pack/load, 70 °C copper, foldback, DCR/hot FETs, harness/transients).
The 75 % recommended-duty conditions remain; omitted losses can lower the camera estimate.

Ports at 0.561 A, 20 °C copper: drift J410 / J420 / J440 minima **4.566698655060775 /
4.567065345619674 / 4.56552353384164 V** (`stageD_budget.json` `port_supply`; Calculation / Inference:
module floor, regulator drift, load; harness excluded). L400-to-port resistances **6.954 / 6.301 /
9.049 mΩ**, sense **33.31 mΩ** (Calculation on CAD); U400 OUT F copper **5.1 mm** (Measured).
U6 VCC drift minimum **3.20722 V** at 1 A (Calculation / Inference), L1 → U6 **12.43 mΩ**.
Dummy-fire upper bound **0.26770 V** at R134 **1.9666 Ω**, current **1.5259032555635084 A**,
below 0.4 V (Calculation / Inference: hot factors, pack/load, copper model, drift).

**Historical method and runs below (`be81f40b…` and the dated later boards), superseded by the round 10 block above.**
Run on a zone-filled copy whose SHA-256 equalled that board's (saved fill matched a native refill then, Measured):
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
  figure changes (the loop already counts Q120 / Q121 at 73.5 mΩ each). *Superseded by round 5 (R12F5-TRI-03,
  D-R12-131): with the J1 → Q120 and Q120 → Q121 copper drops, Q120 −4.569 V and Q121 −4.560 V, margins 69 / 60 mV;
  shorted match 4.39 / 4.37 V (4.33 / 4.32 V with the leads).*
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
  *Corrected in round 5 (R12F5-TRI-05, D-R12-131): with R126 / R128 at the project's ±1.67 % drift ends both give
  **2.777 V**.*
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
  end, within Table 158's 4 mA row (Calculation / Inference: drift). Q124 VGS ≥ 2.778 V is unchanged (2.777 V at the
  drift ends since round 5, D-R12-131).
* `r12_windows.json`'s gate note now scopes the |VGS| > 12 V case to the whole time the bus is on, from the on-rail
  check until switch-off (Inference that no transient above 14.4 V occurs while it is on, pad or flight; it said "only
  enabled in flight"), and quotes PE4's load as about 3.6 mA (≤ 3.9 mA).
* Hot-plug (Simulation / Inference): re-extracted on `db1f0999…`; the electrical SHA is unchanged (`dfba47cd…`), only
  the inputs' board hash and so the inputs SHA changed (`1064def3…`, was `db6e6b21…`); every row and figure is identical
  (file comparison).

**AVA polish pass (D-R12-121 … -124; board `68e6b650…`).** Stage D and the hot-plug model were re-run on the rebuilt
board (zone-filled by the build's post stage; the file's SHA-256 is the board's). Against the `db1f0999…` run,
`stageD_budget.json` differs only in the board hashes, the three 3V3 DC solves (L1 → U6 12.5274 → 12.5286 mΩ, R14 → U6
13.6427 → 13.6441 mΩ, L1 → R14 +0.00002 mΩ; U6 VCC ≥ 3.253 / 3.223 V at U2's 1 A, unchanged at that precision) and the
order of two GND vias at equal distance in the fire-return list (file comparison; Calculation / Inference as before).
Hot-plug: electrical SHA `dfba47cd…` unchanged, inputs SHA `8cf8f9bd…` (was `1064def3…`); every row and figure is
identical (Simulation / Inference; file comparison).

**Round 5 fix pass (D-R12-125, -131; boards `14b82d39…` (lane A) and `6e874d4e…` (lane P2)).** `r12_stageD.py` and
`r12_budget.py` were changed (lane A, R12F5-TRI-02 … -05, -16, -17) and stage D and the hot-plug model re-run on a
zone-filled copy whose SHA-256 equals the board's. Against the `68e6b650…` run (file comparison; Calculation /
Inference as before):
* **Copper.** The PYRO1_OUT trunk moved (lane P, then 0.15 mm west in lane P2): fire loop 4.726699 → **4.726884 Ω**,
  four-stall current 1.250000 → **1.249952 A** (+11.1 %), PYRO1_OUT copper 5.855 → 6.010 mΩ, fire copper 23.76 /
  28.43 mΩ at 20 / 70 °C, idle current 1.505875 A; GND return Q124 → J1.2 2.585 → **2.607 mΩ**. PYRO1_GATE is
  **9.55 mm of F.Cu, no via, L ≤ 4.33 nH** (was 7.20 mm F + 5.37 mm In2, 2 vias, 7.3 nH); PYRO1_GATE_N unchanged
  (17.38 mm F, no via, 10.2 nH). C13's move: L1 → U6 12.529 → **12.047 mΩ**, R14 → U6 13.644 → **13.162 mΩ**, L1 → R14
  4.85 mΩ; U6 VCC at U2's 1 A ≥ **3.2535 / 3.2232 V**, margin 118.5 / 88.2 mV. PA6, EN, hold-up, rails, RAW / VLOGIC /
  PORT_4V8 / CAM solves and ports unchanged.
* **Q120 / Q121 VGS per FET (TRI-03):** the BAT_IN (6.096 mΩ) and ACT_FET_S (6.054 mΩ) copper drops at 70 °C give Q120
  −4.569 V and Q121 −4.560 V at four stalls, margins 69 / 60 mV (was −4.576 V / 76 mV for both); during a fire at
  6.0 / 7.4 / 8.4 V −4.80 / −5.93 / −6.75 V and −4.79 / −5.92 / −6.73 V; shorted match 4.39 / 4.37 V, match and leads
  4.33 / 4.32 V.
* **Q124 VGS ≥ 2.777 V (TRI-05)** at the ±1.67 % drift ends (stage A and D alike).
* **PORT_4V8 input (TRI-02):** `port_supply.window_holds_for` and `u400_input`: U400 VIN 5.552 V at four stalls and
  5.486 V on a 6.0 V pack against VO / 0.75 = 6.09–6.63 V; highest held output 4.51 / 4.80 V at 580 kHz, 5.16 /
  5.26 V with the ~200 kHz foldback (D-R12-131).
* **PD10 (TRI-16 / -17):** ±250 nA, PORT_SENSE 3.103–3.388 / 3.068–3.426 V, ≤ 0.025 V off, VIH 2.402 / 2.425 V.
* **Hot-plug:** electrical SHA `6b54be98…` (C13's pad positions), inputs bound to `6e874d4e…`; every row and figure is
  identical: 0 / 2304 required cases fail, minimum −14.255 V, fall 9.254 V/µs, rise 5.402 V/µs (Simulation /
  Inference).

**Round 6 fix pass (D-R12-137 … -140; boards `3f9579fa…` (lane P), `6a1c99e0…` (lane P3), `f26dfef1…` (lane P4)).**
`r12_budget.py` takes the 3V3 window from TI SLUSDW3A §7.8's PFM band (lane A, R12F6-TRI-03) and adds the cold-screen
bands (`r12_windows.json` `cold_screen`, D-R12-140); stage D and the hot-plug model were re-run on a zone-filled copy of
each board with `--source-board` (Calculation / Inference as before):
* **3V3 window** 3.2539–3.4824 V initial, 3.2237–3.5156 V drift (was 3.2704–3.4314 / 3.2401–3.4641 V). U6 VCC at U2's
  1 A ≥ **3.2370 / 3.2068 V**, margin 102.0 / 71.8 mV; Q124 VGS ≥ **2.761 V**; PE4's load 3.539 mA, ≤ **3.925 mA**;
  PORT_SENSE VIH 2.438 / 2.461 V (D-R12-139).
* **Copper.** Only the plane solves moved: 3V3 cells 302216 → 301771, GND cells 113142 → 111584; GND return Q124 → J1.2
  2.607 → **2.672 mΩ** (< 5 mΩ allowance); L1 → U6 12.053 mΩ, R14 → U6 13.169 mΩ, L1 → R14 4.85 mΩ. Fire loop
  **4.726884 Ω**, four-stall current **1.249952 A** at BAT_IN 5.7209 V (+11.1 %), idle 1.505875 A, fire copper 23.76 /
  28.43 mΩ: unchanged. ACT_GATE F.Cu 11.54 mm after R120's move.
* **Hot-plug:** electrical SHA `3a599c52…` (U9.4's net is now U9_FLT), inputs bound to `f26dfef1…`; every row and
  figure is identical: 0 / 2304 required cases fail, minimum −14.255 V, fall 9.254 V/µs (Simulation / Inference). C81's
  inrush slope is not in this model (D-R12-143, R12F6-TRI-13).

**Round 7 fix pass (D-R12-144 … -151; board `82eddc69…`).** Stage D was re-run on a zone-filled copy with
`--source-board` by lane P and again by the records lane after its own changes (D-R12-149 labels, D-R12-150's C87
range); the then-recorded `stageD_budget.json` was bound to `82eddc69…` (Calculation / Inference as before):
* **Unchanged:** fire loop **4.726884 Ω**, four-stall **1.249952 A** at BAT_IN 5.7209 V, idle 1.505875 A, fire copper
  23.76 / 28.43 mΩ, GND return **2.672 mΩ**, EN chatter (8.13 ms single drop-out, 7.56 ms bench limit), hold-up, the
  shared RAW trunk run (45.2, 16.4) → (45.2, 29.2) and its IPC figures, VLOGIC D5 → U2 / D6 → U2 6.43 / 8.47 mΩ,
  CAM_5V L401 → J9 9.51 mΩ.
* **Moved (the 88 mm outline and the I-5 copper):** RAW_PROTECTED U9 → U400 / U403 / D5 **59.24 / 12.22 / 24.78 mΩ**
  (was 59.63 / 10.81 / 23.53); the B trunk 55.6 mm and U400 IN series copper **48.73 mΩ** (was 57.6 mm, 50.37 mΩ);
  PA6 corners (× 11 / 1 % divider, lower bounds) healthy **+0.171 / +0.080 V**, match shorted **+0.021 / −0.069 V**,
  match and leads shorted **−0.022 / −0.113 V**, healthy VLOGIC 5.121–5.321 V; PORT_4V8 L400 → J410 / J420 / J440
  **11.22 / 13.29 / 8.26 mΩ**, port pins under 0.561 A ≥ 4.596 / 4.563 V (J420 lowest; J410 4.597 / 4.564, J440
  4.598 / 4.566); U400 VIN 5.550 V at four stalls and 5.484 V on a 6.0 V pack, held output 4.51 / 4.80 V at 580 kHz
  (4.45 / 4.74 V) and 5.16 / 5.26 V with foldback (5.09 / 5.19 V); 3V3 L1 → U6 12.17 mΩ, L1 → R14 4.90 mΩ, R14 → U6
  13.24 mΩ, U6 VCC at U2's 1 A ≥ 3.2368 / 3.2066 V, margin 101.8 / 71.6 mV (Calculation / Inference (3V3 window,
  D-R12-139)); PYRO1_GATE 8.11 mm, L ≤ 3.68 nH; U2 OUT (C8's moved via) 5.25 mΩ series.
* **EN turn-on** 30.3–131.5 ms over C87 0.72–1.265 × (was 27–114 ms; D-R12-150).
* **Hot-plug** (lane P): electrical SHA `9750b961…` (moved pad positions), inputs bound to `82eddc69…`; every row and
  figure identical: 0 / 2304 required cases fail, minimum −14.255 V (Simulation / Inference).

**Historical round 8 analyses on `418e5ea9…` (D-R12-156; superseded by the current round 10 block).**
The board and source hashes in `stageD_budget.json` are `418e5ea9…`; lane A re-ran the zone-filled scratch
copy and its refill reproduced the source hash. The fire loop **4.726884 Ω**, four-stall **1.249952 A** at
BAT_IN **5.7209 V**, and GND return **2.672 mΩ** are unchanged (Calculation / Inference: hot factors, pack/load
allocations; DC return a Calculation). U9 RON is **45 mΩ**, TI SLVSFC9C §6.5 maximum, 2.7–23 V, 3 A,
−40…125 °C (Datasheet), replacing the 40 mΩ estimate.

EN (1 % → drift; Calculation / Inference: X7R allowance, leakage bounds, drift): single drop-out at 5.7209 V
**8.13 → 7.61 ms**, bench limit **7.56 → 7.08 ms**, margin above the 7 ms rule **0.56 → 0.08 ms**;
the 7 ms line holds to **5.647 → 5.710 V**, a 10 ms single drop-out needs **5.956 → 6.025 V**;
at 6.0 V immunity is **10.35 → 9.81 ms**. Turn-on **30.3–131.5 → 29.9–135.9 ms**.

PA6 trip window (nominal / 1 % / drift) **4.62–4.95 / 4.537–5.041 / 4.482–5.103 V**.
Four-stall margins to its top, in the same order: healthy **+0.162 / +0.071 / +0.009 V**;
match shorted **+0.012 / −0.079 / −0.141 V**; match and leads shorted **−0.032 / −0.123 / −0.184 V**.
VLOGIC in those three load cases is **5.112–5.312 / 4.962–5.162 / 4.918–5.118 V**.
These are Calculation / Inference: DC-solve upper bounds on drop; SS34 VF, loads, pack model and drift inferred.
D-R12-21's trip-bottom comparison is **+0.068 / −0.015 / −0.119 V**, so it fails at 1 % and drift;
a 0.1 % divider or threshold change is open under O-R12-17, not adopted. The threshold bottom needed before
other margins is **0.4214 / 0.4311 V** at 1 % / drift (Calculation / Inference: D5 VF and drift).

Hold-up from the battery break: **2.23–6.10 ms unshed, 6.66–11.40 ms shed**. From the PA6 trip
(nominal / 1 % / drift): **0.467–1.718 / 0.415–1.873 / 0.382–1.980 ms unshed**, and
**1.40–3.21 / 1.24–3.50 / 1.14–3.70 ms shed** (Calculation / Inference: constant-power loads, D5 VF,
C84 allowance, 3.8 V endpoint, drift). The range spans the divider tolerance.

`u403_input`: VIN **5.574 V**, drop **0.1465 V**, U9 → U403 **11.53 mΩ**; optimistic camera-pin estimates
**4.93 / 5.03 V** at 310 / 220 ns off-time and 200 kHz (Calculation / Inference: converter losses,
foldback, harness and transient allowances). The stage-A U403 estimate is **5.619 V**, not a CAD feed solve.
U400 VIN is **5.541 V** at four stalls and **5.474 V** on the 6.0 V pack; held output estimates
**4.501 / 4.787 V** at 580 kHz, **5.147 / 5.246 V** with foldback (6.0 V pack: **4.446 / 4.729 V** and
**5.085 / 5.182 V**, respectively; Calculation / Inference). U9 → U400 / D5 are **59.24 / 23.28 mΩ**
(Calculation on CAD); RAW drop at D5 **38.1 mV** at the healthy four-stall allocation (Calculation / Inference).
`u400_feed_drop`: **0.121 V** design / **36.1 mV** budget, using **50.78 mΩ** series copper and D5's
1.294 A over shared **10.48 + 2.62 mΩ** runs (Calculation on CAD; currents Inference).
OVLO at 5.71 V: **5.71 × 133 / 1133 = 0.670 V**, **0.6585–0.6822 V** at 1 % and
**0.6508–0.6903 V** at drift, inside 0.5–1.5 V (Calculation; drift Inference).

Hot-plug inputs/results are rebound to `418e5ea9…`, electrical SHA `9750b961…` unchanged:
**2304 / 2304 pass**, minimum **−14.255 V**, steepest fall **9.254 V/µs** (Simulation / Inference; lane P).
Lane A reports all **34 stage-D tests** passing and `tools/check.sh` exit 0 at `c5c695e`; the records lane
has not run KiCad or `check.sh` in its sandbox.

**Historical re-layout analysis below (`be81f40b…`, with explicitly dated later amendments).** The old
EN, PA6, hold-up and feed-drop values are not current bounds; use the current round 10 block above.

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
| Fire loop / four-stall current | 4.726699 Ω; 1.250000 A at BAT_IN 5.7209 V (+11.1 % over 1.125 A) | **unchanged** (fire copper frozen); 4.726884 Ω, 1.249952 A on `6e874d4e…` (round 5 moved the PYRO1_OUT trunk) | Calculation / Inference |
| GND fire return Q124 → J1.2 (DC solve) | 2.594 mΩ | **2.585 mΩ** (< 5 mΩ allowance; the loop keeps 5 mΩ); 2.607 mΩ on `6e874d4e…` (round 5); 2.672 mΩ on `f26dfef1…` (round 6) | Calculation |
| EN / chatter | single drop-out 8.13 ms at 5.7209 V; bench-rule worst-corner limit 7.56 ms; turn-on 27–114 ms | **unchanged** (same parts and four-stall point); turn-on 30.3–131.5 ms since D-R12-150 (C87 0.72–1.265 ×) | Calculation / Inference |
| Hold-up from a battery break / from the PA6 trip | 2.23–6.12 ms unshed, 6.68–11.43 ms shed / 0.47–1.72 ms | **unchanged** (constant-power model) | Calculation / Inference |
| C84 → U2 copper (DC solve, not in the hold-up model) | 47.8 mΩ | **4.14 mΩ** (C84 beside U2, D-R12-94) | Calculation |
| RAW_PROTECTED U9 → U400 / U403 / D5 | 5.79 / 7.45 / 5.33 mΩ | **59.63 / 10.81 / 23.53 mΩ** (the port buck and D5 hang off the B trunk) | Calculation |
| VLOGIC D5 → U2 / D6 → U2 | 13.87 / 30.51 mΩ | **6.43 / 8.47 mΩ** | Calculation |
| PA6 margin to the trip top, four stalls (× 11 / with 1 % divider; lower bounds, per-branch drop since R12F3-TRI-09): healthy | +0.200 / +0.109 V | **+0.174 / +0.083 V** (+0.158 / +0.068 V with the lumped drop) | Calculation / Inference |
| … match shorted | +0.051 / −0.040 V | **+0.025 / −0.066 V** (lumped +0.008 / −0.083 V) | Calculation / Inference |
| … match and leads shorted | +0.007 / −0.084 V | **−0.019 / −0.110 V** (lumped −0.036 / −0.127 V; in the band at the nominal ratio too) | Calculation / Inference |
| Q124 VGS minimum (PE4 VOH ≥ VDD − 0.4 V, R12F3-TRI-06; PE4 load about 3.56 mA, ≤ 3.87 mA, within the 4 mA row, R12F4-TRI-02) | ≥ 3.17 V (VOH = VDD) | **≥ 2.777 V** at the ±1.67 % drift ends (2.5 V row; 2.778 V before R12F5-TRI-05); **≥ 2.761 V** on the PFM 3V3 window (round 6, D-R12-139; PE4 load ≤ 3.925 mA) | Calculation / Inference |
| PORT_4V8 L400 → J410 / J420 / J440 | 73.6 / 74.8 / 69.6 mΩ | **11.50 / 13.07 / 6.88 mΩ** | Calculation |
| Ports under 0.561 A (J420 lowest), initial / drift | ≥ 4.561 / 4.529 V | **≥ 4.596 / 4.563 V** (J410 4.597 / 4.564, J440 4.599 / 4.567); at R10's 1.9 A design current ≥ 4.578 / 4.546 V; valid while U400 VIN ≥ VO / 0.75 (D-R12-131) | Calculation / Inference |
| Ports at no load (ceiling 5.0 V) | ≤ 4.938 / 4.972 V | unchanged (regulator window) | Calculation / Inference |
| U6 VCC at U2's 1 A (O-R12-22) | ≥ 3.258 / 3.228 V | **≥ 3.253 / 3.223 V**, margin 118 / 88 mV over 3.135 V ((12.05 + 4.85) mΩ × 1 A on `6e874d4e…`; 12.53 mΩ before round 5); **≥ 3.237 / 3.207 V**, margin 102 / 72 mV on the PFM 3V3 window (`f26dfef1…`, D-R12-139) | Calculation / Inference |
| CAM_5V L401 → J9 | 9.51 mΩ | unchanged (camera cell frozen) | Calculation |
| PD10 PORT_SENSE | (PA4) 3.10–3.39 V / 3.07–3.43 V | 3.103–3.388 V initial, 3.068–3.426 V drift, ≤ 0.025 V off (±250 nA FT_xx leakage, R12F5-TRI-16; VIH 2.402 / 2.425 V, 2.438 / 2.461 V on the PFM window, D-R12-139) | Calculation; drift Inference |

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

## 5. Cost and stock (round 9; D-R12-165)

Live parts: `m3_design/r12/fab/cost_check_2.json` / `_5.json`, **2026-11-09T00:10:43Z / 00:12:01Z**,
board `a02a6181…` (BOM unchanged on `a1e65bb4…`; the saved CPL hash belongs to the earlier placement). Stock files: **2026-11-09T00:10:04Z / 00:11:22Z**, 59 codes
(23 Extended / 36 Basic), none short or thin; orderable quantity is an Inference about JLC's field.
JLC assembles **183 parts**, no owner BOM. R60 adds C852472; R61 joins C190095. J430 is C585350.
D8 C19077532, D121 C85364 and C37704 are Preferred Extended, fee-exempt on Economic.

Parts **$32.7060 per board unrounded** (sum of JSON line prices), feeder **20 × $3.07 = $61.40 per order**;
REQUIREMENTS M3 metric **$63.41 / $44.99 per board at 2 / 5 boards**, under the $84.41 cap.

All-in is Calculation / Inference: Live parts above; setup/stencil **$9.71**; SMT **593 pasted pads per board
× $0.0016** (Measured from `m3_gerber.zip` F_Paste); THT J121 / LS120 **4 joints × $0.0164 per board + $3.58**
labour per order. Bare PCB **$25.10** is cost_study.md §2.1's Live 46 × 90 mm ENIG / 0.5 oz quote (2026-11-04),
used for 83 mm without a re-quote (**Inference**). Shipping, tax and attrition excluded. X-ray qualifying count
and tier application are **Inference** pending JLC's quote (D-R12-105).

| Order | JLC parts | Feeder | Setup + stencil | SMT joints | THT joints + labour | Bare PCB | X-ray (U1 only) | Total | Per board |
|---|---|---|---|---|---|---|---|---|---|
| 2 boards | $65.41 | $61.40 | $9.71 | $1.90 | $3.71 | $25.10 | $3.28 | **$170.51** | $85.26 |
| 5 boards | $163.53 | $61.40 | $9.71 | $4.74 | $3.91 | $25.10 | $8.20 | **$276.59** | $55.32 |

Totals and per-board values are rounded independently from unrounded sums **$170.5108 / $276.5920**;
rounded columns need not sum exactly. U1-only totals are **$0.51 above $170** at two boards and below $295 at five.
Counting U1 / U4 / U5 / U6 / U9 gives X-ray **$16.40 / $20.50–28.70** and all-in
**$183.63 / $288.89–297.09** (**$91.82 / $57.78–59.42 each**), $13.63 over at two boards and straddling $295
at five (Calculation / Inference: qualifying count and tier). D402 / Y1 may also count; seven parts per board
at $1.64 each would be at most $22.96 / $57.40 X-ray per order (Inference). D95 / D436 have visible SOT-23 leads.
Confirm JLC's count, tier, DFM and reflow acceptance on the quote. Nothing ordered. Re-run
`FAB_NET=1 m3_design/r12_fab.sh` on order day; its metric does not include X-ray.

## 6. Hashes (Measured, SHA-256; final board)

| File | SHA-256 |
|---|---|
| m3_design/r12/m3.kicad_pcb | a1e65bb4109ba5db7821cc1ec8b1ae6c3db88d5f9bd1f1700eb0cb182721e59a |
| m3_design/r12/m3.kicad_dru | 8974a6cd6a7ec43c865b85350bb37e7f9aecc963dc2d2f6a3abf61574958c5de |
| m3_design/r12_fire.py | c2d2954607e29080706d06c2f45bdbea04ebf09a0fdf83a03758d9455aa85822 |
| m3_design/r12_legends.tsv | de594b398cde5950913774fe7661a358baa9157cbf721aed386d68c7a9b19092 |
| m3_design/r12_routes.tsv | 869ab108b14048c79dc601c223567bd255313ce96f8ad8d373e94af0e07e63c5 |
| m3_design/r12_place.tsv | 225ab7f80603292670e1210a0229f1570f8a0bba228fbfcd2ee26ce1918373a3 |
| m3_design/r12/fab/m3_bom_jlc.csv | 0452b1cc5d4be49441b24dfe00f714cceff74c638261b8c64cf0fe87cd242a53 |
| m3_design/r12/fab/m3_cpl_jlc.csv | 021a244e49a09a1e9ca9d217ebe494de1dccd2bb51b49e73d79bbfcaefcd0f11 |
| m3_design/r12/fab/m3_fab_manifest.json | fc0e427288e6d7b0dd6f042d6e09140c7594f7fb5f1850abc98d670bb907b84a |
| m3_design/r12/fab/m3_gerber.zip | 470727aab5cb32cec3d19cd7dd9c887828f6730e8fc605ddf97bcdd1d7848967 |
| m3_design/r12/fab/cost_check_2.json | 5864c8ed9cf084a02a7468d421528b9ed1b0c4770666e72906bcefaeece472af |
| m3_design/r12/fab/cost_check_5.json | 0b101aa1456480389c982abaa37331dafd384ce85be58a29f0bbcaa9c0eaedb0 |
| m3_design/r12/fab/stock_check_2.json | 21a545dfa32e16c350f38496f0c512b11fb920cb37c682e3be48121485e6e80a |
| m3_design/r12/fab/stock_check_5.json | f75b7289ed09b2567c480af968fc8f4f0ba62b3c3a7dfd46d034e403e0f178cd |

The Gerbers and assembly PDFs carry their creation date, so they change on every export; the manifest binds them.

## 7. Gate and what is not verified

**Current round 10:** lane P (D-R12-171) reports two identical `a1e65bb4…` builds, all build checks
and `tools/check.sh` exit 0 (lane S `6403f0a` had reported the same for `a02a6181…`). Lane A reports 42 stage-D tests and full gate exit 0. This records lane runs no KiCad or full gate.
Round 9 reviewed `418e5ea9…` (four Opus and five Astra lenses) and found **14 real errors
(0 Critical / 2 Major / 12 Minor)**. D-R12-161 … -166 record the fixes: every IC pin in I-5,
direction/rating guards, probe clearances, doubled power taps, 70 °C copper and the dummy-fire bound,
plus the owner-requested push-pull socket / 85 mm layout, the orchestrator's 0.1 % PA6 divider and
0.425–0.455 V band, the Preferred D8 / D121 swaps and lane C's J430 local bypass (D-R12-169).
Round 10 reviewed `ae22387d…` (four Opus and five Astra lenses) and found **16 Minor real errors,
0 Critical / 0 Major** (R12F10-TRI-01 … -16): **CLEAN under D-R12-167, the first of the clean pair**.
The fixes produce **`a1e65bb4…`, 46 × 83 mm** (D-R12-170 … -173). Lane P (`b20de30`) reports two
byte-identical builds and the full gate exit 0; lane A (`3d96eb5`) reports the full gate exit 0 and
42 stage-D tests passing. Round 11 must review the fixed board; it has not run.

**Owner stop rule (2026-11-08, D-R12-167):** stop after two consecutive full rounds with zero Critical
and zero Major real errors. Fix Minor real errors each round; they do not reset the count. This supersedes
the zero-real-error rule for R12. Round 10 is clean and is the first of the pair; round 11 is next on `a1e65bb4…`.
Then obtain JLC DFM and a quote; the owner orders. The severity scale is in D-R12-167.
Judge layout against both BPS.space AVA and LEVIA-H7 (owner, D-R12-168).

**Historical gate reports:**

**Round 8:** lane P `33ce766` reports two identical `418e5ea9…` builds, DRC / unconnected / parity / ERC 0,
check_r12 every rule OK including K-power, route_check 0 failing / 3 allowlisted, fit / legends / fill OK,
fab manifest bound, hot-plug 2304 / 2304 pass (Simulation / Inference). Lane A `c5c695e` reports 34 stage-D
tests and test_r12_check passing, full check.sh exit 0; P also reports exit 0. The records lane did not run
KiCad / check.sh in its sandbox. No physical or firmware tests, JLC DFM or owner acceptance. Round 8
found 19 real errors and did not satisfy the then-current stop rule. **Historical gate runs follow.**

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
sentence). AVA polish pass (D-R12-121 … -124, branch `r12-polish`): two builds gave the same board `68e6b650…`; stage D
and the hot-plug model re-run on it; the fab package re-exported and bound; `test_r12_stageD` 13 / 13;
`PYTHONHASHSEED=0 tools/check.sh` with NUMPY_PY exited 0 (Measured, 2026-11-06; the only change after it was this
sentence and STATUS.md's polish paragraph). Round 5 fix lanes P, A / C and P2 (R12F5-TRI-01 … -06, -13, -14, -16,
-17, -21; branches `r12f5-P`, `r12f5-AC`, `r12f5-P2`): two builds gave the same board `6e874d4e…`, unchanged by a zone
refill; DRC / unconnected / parity 0; check_r12 every rule OK with S-10; route_check 0 failing, 3 allowlisted; the fab
package re-exported and bound; stage D and the hot-plug model re-run; `test_r12_check` 74 / 74, `test_r12_stageD` 19 / 19, `test_paste_check` 17 / 17; `PYTHONHASHSEED=0 tools/check.sh` with NUMPY_PY exited 0
(lane P2). The records lane (branch `r12f5-E`) then updated the records and ran `tools/check.sh` again: exit 0 (§1;
STATUS.md "Round 5 fix pass"). Round 6 fix lanes P, A / B, P3 and P4 (R12F6-TRI-01 … -05, -09, -15 … -17, verifier
V-1 … V-5, PACK_FLT; branches `r12f6-P`, `r12f6-AB`, `r12f6-P3`, `r12f6-P4`): three builds gave the same board
`f26dfef1…`; DRC / unconnected / parity / ERC 0; check_r12 every rule OK with S-10's fire-state, pack and FLT guards;
route_check 0 failing, 3 allowlisted; the fab package re-exported, priced Live and bound; stage D and the hot-plug model
re-run; `test_r12_check` 89, `test_r12_stageD` 23, `test_r12_fab` 15; `PYTHONHASHSEED=0 tools/check.sh` with NUMPY_PY
exited 0 in each lane (twice in P3). The records lane (branch `r12f6-E`) then updated the records and ran
`tools/check.sh` again: exit 0 (STATUS.md "Round 6 fix pass"). Round 7 fix lanes P and AE (R12F7-TRI-01 … -17;
branches `r12f7-P`, `r12f7-AE`): two builds gave the same board `82eddc69…`; DRC / unconnected / parity / ERC 0;
check_r12 every rule OK with S-10's I-5 classes; route_check 0 failing, 3 allowlisted, `pad_debris` / `pad_slit`
clean; the fab package re-exported, priced Live and bound; stage D re-run (both lanes) and the hot-plug model re-run
(lane P); `test_r12_check` 94 (no skip), `test_r12_stageD` 25, `test_r12_fab` 15, `test_route_check` 87;
`PYTHONHASHSEED=0 tools/check.sh` with NUMPY_PY exited 0 in lane P and again after the records lane (STATUS.md
"Round 7 fix pass"). Not verified: any physical, electrical or firmware test; JLC DFM; the vehicle fit of the current 83 mm
board (O-R12-28); AN2606 (O-R12-23); two consecutive full stage F rounds with zero Critical and zero Major real errors (D-R12-167; Minor errors are fixed but do not reset the count). Historically, round 2 found 16 real
errors, round 3 14, round 4 8, round 5 22, round 6 17 and round 7 17 (R12F7-TRI-01 … -17). After any
later copper change: re-run the legend aid if needed, then `m3_design/r12_stageD.py` and `tools/r12_hotplug.py`.
