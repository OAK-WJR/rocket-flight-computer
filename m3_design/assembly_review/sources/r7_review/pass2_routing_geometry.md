# R7 review pass 2: routing geometry and style (whole board)

Reviewer: independent, read-only. Dimension: routing geometry and style, every track and via on all four layers.
Acceptance criterion: CLEAN ROUTING (AGENTS.md §3 plus the owner's clean-routing list).

- Board reviewed: `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
  `03fe75720f46b1382d9d3216dbffd8ae642d0125722c04589ff97c964aa86d54` (the step B board; unchanged at the end of
  this review). No arcs on the board; 2777 tracks, 699 vias.
- Baseline: committed R6 board `git show 3b215ba:m3_design/assembly_review/m3.kicad_pcb` (SHA-256 `184a87e8…`),
  compared after the +18 mm y translation.
- Nothing in the repository was modified except this file; the board was loaded from scratch copies and never saved.

## 1. Verdict

The gate passing (DRC 0, unconnected 0) does not make the board clean. Against the clean-routing criterion it fails
on both R7 copper and inherited R6 copper:

- **R7 copper:** the hand-scripted parts are mostly tidy. That covers the RF lines, the U1 escape, the left-edge
  corridor and the band, which run as parallel buses at a constant 0.5 mm (B.Cu) and 0.4 mm (F.Cu) pitch with
  nested 45° corners. The problems are in other places:
  - The grid-router session left autorouter debris on the 13 redrawn R6 nets: duplicated routes that run side by
    side with the R6 copper they should have joined (PULLPIN, BAT_ILIM), hairpins with 45° acute angles,
    staircases, a six-via layer-hopping route and a 2.8× detour.
  - Deleting the R6 port parts left dead copper and stubs in the GND/3V3 pours.
  - 29 of the 39 layer changes on the new radio/GNSS interface (and the rerouted QSPI_IO0) have no GND via within
    1.5 mm.
- **Untouched R6 copper** is worse in volume:
  - 247 overlap-debris instances (duplicate segments, collinear overlaps, side-by-side overlapping copper, crossings
    without a node, fold-backs), mostly on power nets and including the PYRO1_GATE route.
  - 27 acute 45° junctions, 15 staircases, 274 segments shorter than 50 µm.
  - 23 critical-net layer changes (pyro, USB, SPI) with no nearby GND via.
  - The documented off-angle 3V3 segment.

Major findings: 10 (5 on R7 copper or R7 edits, 5 on inherited R6 copper). Minor findings: 5. No Critical finding:
nothing found is electrically open or shorted (the gate's DRC and connectivity results stand). The R6 debris is
held together electrically by overlap and by the pours.

## 2. Method

All scripts are in the scratch directory
`<scratch>/rg/`. They are
run with KiCad 10.0.6's Python (`pcbnew`) on scratch copies `r7.kicad_pcb` and `r6.kicad_pcb`.

| Script | What it does |
|---|---|
| `scan.py r7 r6 out.json` | Main scan. Enumerates every PCB_TRACK/PCB_ARC/PCB_VIA, builds per-(layer, net) node graphs (endpoint coincidence 1 µm, as `check_r7`), and computes every metric below on both boards |
| `table.py`, `appendix.py` | Count table (§3) and the critical-net instance listing (Appendix A) from `out.json` |
| `orphan.py`, `walk.py` | R6-origin copper whose endpoint sat in a pad or via that R7 deleted; walks each chain to its next real junction |
| `netstats.py` | Per-net length/segment/via counts, R6 against R7 |
| `clear.py`, `cand.py` | Edge-to-edge clearance of every track to other-net tracks, vias and pads (pours excluded); clearance check of the proposed replacement routes |
| `render.py` + `r.sh` | Vector renderer: tracks with centrelines and end dots, vias, pads; option to fade R6 copper. PDF, rasterised with `pdftocairo` |

**Copper origin.** An R7 track is *untouched R6* if a track with the same layer, width and endpoints exists on the
R6 board after +18 mm in y: 2327 tracks. Six more are R6 tracks trimmed by R7 (collinear sub-segment). The other
**444 tracks (1337 mm) are R7-new**. Vias: 422 R6, 277 R7.

**Instance attribution.** Each detected instance is put in one of three columns:

- **A**: it involves at least one R7-new or trimmed track or via.
- **B**: it involves only R6 copper, but it is new in R7, so it does not appear at the same translated place in the
  same scan of the R6 board. These are R6 copper whose context R7 changed, for example a pad R7 removed.
- **C**: untouched R6, present identically on the R6 board.

**Metric definitions.** Angles are rounded to the 45° class for chain analysis.

- **Off-angle:** heading more than 0.1° from a multiple of 45°, or more than 2 µm lateral error. Smaller deviations
  are reported separately as nm rounding.
- **Acute angle:** two branches at a node, outside any pad or via, meeting at less than 89.5°. 45° and 0° (fold-back
  or overlap) are reported separately. Nodes inside a pad or via are counted apart.
- **Chain:** a maximal run through plain bends, meaning nodes with exactly two track ends and no pad, via or T.
- **Staircase:** an alternating heading run A,B,A,B,… of at least 4 segments with at least 2 shorter than 1 mm.
  The same run with long segments counts as *extra bends*.
- **Tiny jog:** A,B,A with the middle segment under 0.5 mm or a lateral offset under 0.25 mm.
- **Collinear unmerged:** a plain node at 180°.
- **Overlap tests (same layer and net):**
  - collinear overlap: centrelines within 1 µm and projections overlapping by more than 1 µm;
  - exact duplicate;
  - side-by-side overlap: parallel, offset under half the sum of the widths, overlapping by more than half a width;
  - crossing without a node: an interior intersection.
- **Endpoint classes:** pad, via centre, track joint (end-to-end or T within 1 µm), via off centre, overlap-only
  (touches same-net copper only by width), held only by a same-net pour, or dangling.
- **Pad entry:** end offset from the pad centre, and heading relative to the pad axes. All 455 non-axial entries are
  at exactly 45°; no entry is at any other angle.
- **Width change:** branches of different width meeting at a free node or at a via.
- **GND via at layer change:** for every via that carries tracks on two or more layers of a critical signal net,
  the centre distance to the nearest GND via. The flag is set above 1.5 mm.
  - Critical signal nets are RF, pyro/arm, HSE, USB_DP/DM, QSPI/SPI1/IMU_CS/radio SPI, and the other RADIO_*/GNSS_*
    nets.
  - Critical power nets are the rails and GND.
- **Detours:**
  - chain path more than 1.25× the octile distance and more than 0.5 mm longer;
  - U-turn: cumulative heading change of 180° or more in one chain;
  - net-level: shortest track path between the two pads of every two-pad net without its own pour, against the
    octile distance;
  - short layer hop: a chain under 3 mm between two vias of the same net.

**Limitations.**

- Pours are not treated as track copper in the overlap tests. An end that touches only a pour is reported as
  "held only by the pour".
- 45° pad entries and 90° corners are allowed by the §3 rule. They are counted as style, not as violations.
- The staircase and detour heuristics flag candidates. The R7 instances named in §4, and representative R6 instances
  (USB_LIMITED, CAM_IO_3V3, PYRO1_GATE, SPI1_MOSI, PYRO1_CONT), were checked on zoomed renders.
- High-current sizing (IPC-2152) is not re-assessed here. The new 3V3_RADIO (0.3/0.4 mm) and 3V3_GNSS (0.3 mm)
  feeds are well above what 119 mA needs (Inference).

## 3. Metrics

### 3.1 Counts per category

Format: total instances (of which on critical nets). Columns A/B/C as in §2.

| Category | R7-new copper (crit.) | R6 copper, new in R7 (crit.) | untouched R6 (crit.) |
|---|---|---|---|
| Off-angle segment (not 0/45/90) | 0 (0) | 0 (0) | 1 (1) |
| Off-angle by coordinate rounding only (<2 um lateral) | 5 (0) | 0 (0) | 50 (16) |
| Staircase (>=4 alternating segs, >=2 under 1 mm) | 11 (4) | 0 (0) | 15 (8) |
| Extra bends (4+ alternating long segs) | 6 (2) | 0 (0) | 23 (5) |
| Tiny jog (A-B-A, middle <0.5 mm or offset <0.25 mm) | 3 (0) | 1 (1) | 51 (23) |
| Acute 45 deg junction (outside pads/vias) | 6 (0) | 2 (2) | 27 (20) |
| Fold-back 0 deg junction (overlapping branches) | 2 (0) | 0 (0) | 57 (43) |
| Acute junction inside a pad/via | 12 (3) | 0 (0) | 126 (72) |
| Segment < 0.2 mm (all) | 26 (5) | 0 (0) | 442 (250) |
|   of which < 0.05 mm | 5 (0) | 0 (0) | 274 (156) |
|   of which mid-route jog (both ends plain joints) | 9 (1) | 0 (0) | 110 (71) |
|   of which wholly inside one pad | 10 (4) | 0 (0) | 232 (109) |
| Collinear consecutive segments not merged | 4 (3) | 4 (4) | 24 (13) |
| Exact duplicate segment | 0 (0) | 0 (0) | 7 (0) |
| Collinear overlapping segments | 1 (0) | 0 (0) | 65 (49) |
| Side-by-side overlapping copper (parallel, offset < width) | 5 (0) | 0 (0) | 70 (56) |
| Same-net crossing without a node | 3 (0) | 0 (0) | 43 (35) |
| Overlap-only joint (end touches copper, not centreline/pad/via) | 0 (0) | 0 (0) | 5 (5) |
| Track end inside via but off its centre | 1 (1) | 3 (1) | 8 (6) |
| Dangling track end (no copper at all) | 0 (0) | 0 (0) | 0 (0) |
| Track end held only by a same-net pour (stub into pour) | 0 (0) | 6 (6) | 26 (26) |
| Via connected on <= 1 layer | 0 (0) | 0 (0) | 0 (0) |
| Via whose tracks are all on one layer | 0 (0) | 0 (0) | 0 (0) |
| Track end in small pad > 0.1 mm off centre | 41 (27) | 3 (2) | 191 (125) |
| Track entering a non-round pad at 45 deg to its axes | 38 (25) | 2 (0) | 415 (237) |
| Segment wholly inside its pad (>= 0.2 mm) | 9 (8) | 1 (1) | 70 (56) |
| Track passing through a same-net pad without ending | 5 (3) | 0 (0) | 17 (16) |
| Width change at a free node (no pad/via) | 5 (1) | 1 (1) | 60 (53) |
| Width change at a via | 0 (0) | 0 (0) | 16 (16) |
| 90 deg corner (allowed by rule; style) | 6 (4) | 0 (0) | 79 (58) |
| Critical-signal layer change, no GND via within 1.5 mm | 29 (29) | 0 (0) | 23 (23) |
| Short layer hop (< 3 mm between two vias of the net) | 10 (1) | 0 (0) | 21 (6) |
| Chain detour (path > 1.25x octile and +0.5 mm) | 22 (14) | 2 (1) | 52 (32) |
| U-turn (cumulative heading change >= 180 deg) | 14 (8) | 0 (0) | 33 (23) |
| Same-net signal vias < 1.2 mm apart | 0 (0) | 0 (0) | 26 (24) |

Read with care:

- R7's 11 staircases include the 4 band lanes (RADIO_NRST, BUSY, SCK, MISO_MCU). Their "steps" are the fan-in jog
  from the 0.5 mm via stagger to the 0.4 mm lane pitch, followed by the corner chamfer (RG-11).
- Six of the other 7 are on the rerouted nets (RG-01, RG-03). The last is the VBUS_SENSE In2 joint (RG-11).

### 3.2 Rerouted R6 nets (grid-router session) and the new interface: per-net figures

R6 length is the same net on the R6 board. Path/octile applies only to two-pad nets.

| Net | Pads | R6 mm / vias | R7 mm / vias | R7-new segs | Path / octile (mm) |
|---|---|---|---|---|---|
| LED_RED | 2 | 42.0 / 6 | 62.7 / 2 | 29 | 62.7 / 22.4 (**2.80×**) |
| LED_YEL | 2 | 28.8 / 6 | 33.2 / 6 | 14 | 33.1 / 25.2, **6 vias** |
| CAM_MCU_TX | 2 | 88.6 / 3 | 70.6 / 5 | 24 | 70.3 / 24.7 (2.85×) |
| PULLPIN_EXT | 2 | 5.6 / 1 | 13.7 / 2 | 13 | 13.4 / 9.3 |
| PULLPIN | 5 | 45.9 / 2 | 55.0 / 6 | 19 | – |
| VLOGIC_SENSE | 4 | 36.2 / 3 | 43.5 / 6 | 18 | – |
| BAT_ILIM | 3 | 37.8 / 2 | 36.8 / 4 | 17 | – |
| BAT_SW_RETURN | 2 | 164.3 / 9 | 161.5 / 7 | 23 | 161.3 / 76.3 (2.1×) |
| BAT_SW_SOURCE | 2 | 128.6 / 9 | 128.9 / 7 | 14 | 128.4 / 87.3 |
| BUZZ_DRV | 2 | 67.0 / 6 | 64.1 / 5 | 19 | 63.3 / 48.3 |
| RADIO_DIO1 | 2 | – | 69.1 / 4 | 14 | 69.1 / 39.0 (1.77×) |
| RADIO_BUSY | 2 | – | 66.7 / 2 | 13 | 66.7 / 42.4 (1.57×) |
| RADIO_MISO_MCU | 2 | – | 61.9 / 2 | 14 | 61.9 / 39.2 (1.58×) |
| GNSS_RESET_N | 2 | – | 60.3 / 2 | 9 | 59.3 / 35.0 (1.70×) |
| RADIO_TXEN | 2 | – | 25.2 / 2 | 7 | 25.2 / 11.0 (documented loop round U31) |
| QSPI_IO0 | 2 | 27.6 / 0 | 26.8 / 2 | 12 | 26.6 / 21.7 |

### 3.3 Clearance use

Edge-to-edge distance from each track to other-net tracks, vias and pads (pours excluded):

| Copper | Segments with min clearance < 0.17 mm | < 0.20 mm |
|---|---|---|
| R7-new | 6 of 450 | 109 of 450 |
| Untouched R6 | 48 of 2327 | 315 of 2327 |

- All six R7 cases are corridor lanes passing an inline resistor's pads at 0.155 mm (RG-12).
- The R7 interface lanes otherwise run at 0.175 mm gaps (0.4 mm pitch) by design.

### 3.4 GND vias at critical-signal layer changes

Distance from each transition via to the nearest GND via:

| Copper | Transition vias | ≤ 1.0 mm | 1.0–1.5 mm | 1.5–2.5 mm | > 2.5 mm |
|---|---|---|---|---|---|
| R7-new | 39 | 5 | 5 | 6 | **23** |
| R6 | 40 | 12 | 5 | 8 | 15 |

## 4. Findings

| ID | Sev. | Copper | Finding (short) |
|---|---|---|---|
| RG-01 | Major | R7 | PULLPIN redrawn as a second F.Cu route on top of the R6 one: side-by-side overlap, 3 crossings without node, 45° acute, 7.9 µm stub, staircase |
| RG-02 | Major | R7 | BAT_ILIM test-pad branch drawn as a duplicate of the U9.9 to R84.1 link: collinear and side-by-side overlap, 0° fold-backs, 45° acute T's, width changes 0.15/0.2 |
| RG-03 | Major | R7 | Grid-router debris on the other rerouted nets: acute hairpins, staircases, six-via LED_YEL, 2.8× LED_RED detour |
| RG-04 | Major | R7 edit (R6 copper) | Dead copper and stubs left where R7 deleted R6 port parts |
| RG-05 | Major | R7 | 29 interface/QSPI_IO0 layer changes with no GND via within 1.5 mm (23 beyond 2.5 mm) |
| RG-06 | Major | R6 | Widespread duplicated/overlapping copper on power nets |
| RG-07 | Major | R6 | PYRO1_GATE drawn twice (0.3 mm trunk plus 0.2 mm doglegs) through C126/R128 pads |
| RG-08 | Major | R6 | 27 acute 45° junctions, 15 staircases, 51 tiny jogs, 274 segments < 50 µm in R6 copper, many on critical nets |
| RG-09 | Major | R6 | 23 critical-net layer changes without a GND via within 1.5 mm |
| RG-10 | Major | R6 | Off-angle 3V3 B.Cu segment (41.35, 58.55)–(42.95, 57.15), 3.81° off |
| RG-11 | Minor | R7 | Band fan-in jogs, mid-run neck-down and mixed widths, 90° corners, RXEN parallel to QSPI_CLK at 0.175 mm |
| RG-12 | Minor | R7 | Corridor C-loop wider than needed; lanes pass inline-resistor pads at 0.155 mm with free B.Cu beside them |
| RG-13 | Minor | R7 | GNSS limiter: ANT_SRC U-loop (placement-driven crossing), jogs inside pads |
| RG-14 | Minor | R7 | Untidy pad entries in the strip (C310.1 fold, U30.7/8 H-link, TP30, R310 corner) |
| RG-15 | Minor | R6 | Widespread minor style debt (width changes, unmerged segments, segments inside pads, SWD detours) |

### RG-01: PULLPIN duplicated route (Major, R7)

**Evidence** (F.Cu, 0.15 mm, net PULLPIN; `img/pullpin.png`).

The R6 tree already joins D122.3 (32.5, 30.6), R160.2 (32.9, 27.03), R161.2 (34.17, 26.8) and C160.1 (34.9, 28.08).
The session added a second path from D122.3 to the new In2 via (37.4675, 30.8404) instead of branching at C160.1.
The new path is these segments, in order:

- (32.5, 30.9404)→(32.1675, 30.9404), 0.333 mm, entering D122.3 0.34 mm off centre
- (32.1675, 30.9404)→(32.6675, 30.4404)
- (32.6675, 30.4404)→(32.6675, 28.1404)
- (32.6675, 28.1404)→(32.9675, 27.8404)
- (32.9675, 27.8404)→(33.8675, 27.8404)
- (33.8675, 27.8404)→(33.9675, 27.9404), 0.141 mm
- (33.9675, 27.9404)→(36.4675, 27.9404)
- (36.4675, 27.9404)→(37.4675, 28.9404)
- (37.4675, 28.9404)→(37.4675, 30.8404)

Measured defects:

- **Side-by-side overlapping copper:**
  - (32.6675, 28.14–30.44) against R6 (32.76, 27.70–29.59): offset 0.0925 mm, 1.45 mm long;
  - against R6 (32.2, 30.9)–(32.5, 30.6): offset 0.006 mm;
  - (33.97–36.47, 27.9404) against R6 (34.38–34.9, 28.08): offset 0.14 mm.
- **Crossings without a node:** at (32.76, 28.0479), (32.6675, 29.6858) and (34.3848, 27.9404). The last is the R6
  C160 stub (34.3848, 27.53–28.08).
- **Acute 45°** at (32.1675, 30.9404).
- **7.9 µm stub:** (32.2, 30.9079)→(32.2, 30.9), a `_pad_joints` patch T-ing onto the diagonal.
- **Staircase:** headings 225/180/225/180, lengths 1.414/2.5/0.141/0.9 mm.
- The track passes through C160.1 without ending.
- The leftover R6 segment (32.2, 30.9)–(32.5, 30.6) now lies wholly inside D122.3.

**Fix.**

1. Delete the nine R7 F.Cu segments above, except the last one (37.4675, 28.94–30.84), together with the 7.9 µm
   stub and the R6 orphan (32.2, 30.9)–(32.5, 30.6).
2. Join the via from C160.1: (34.9, 28.08)→(36.6075, 28.08)→(37.4675, 28.94), then the kept segment down to
   (37.4675, 30.8404).

`cand.py` clearance of the new segments to other-net tracks, vias and pads: ≥ 0.18 mm. The pours refill.

### RG-02: BAT_ILIM duplicated link (Major, R7)

**Evidence** (F.Cu; `img/batilim.png`). The R6 0.2 mm link U9.9→R84.1 runs (10.975, 39.7)→(10.975, 39.3)→
(10.575, 38.9)→(10.075, 38.9)→(9.875, 38.7)→(9.875, 37.3)→(10.675, 36.5)→R84.1 (10.65, 36.475). The session drew
the TP89 branch as a 0.15 mm copy of the same link:

- (10.975, 39.3)→(10.475, 38.8)
- →(10.075, 38.8)
- →(9.875, 38.6)
- then from (9.875, 37.6)→(11.075, 36.4)→(11.575, 36.4), to the via, In2, and on to TP89

Measured defects:

- **Collinear overlap:** 0.566 mm, (10.975, 39.3)–(10.475, 38.8) over the R6 (10.975, 39.3)–(10.575, 38.9).
- **Side-by-side overlaps:** offset 0.1 mm over 0.4 mm, and offset 0.071 mm over 0.21 mm.
- The copy re-uses the R6 x = 9.875 run.
- **Fold-back 0° junctions** at (10.975, 39.3) and (10.575, 38.9).
- **45° acute T's** at (9.875, 38.6) and (9.875, 37.6).
- **Width changes 0.15/0.2** at four free nodes.
- It enters R84.1 0.43 mm off centre, at (11.075, 36.4).

**Fix.**

1. Delete the four copy segments (10.975, 39.3)–(10.475, 38.8), (10.475, 38.8)–(10.075, 38.8),
   (10.075, 38.8)–(9.875, 38.6) and (9.875, 37.6)–(11.075, 36.4).
2. Start the branch at the R84.1 centre: (10.65, 36.475)→(11.575, 36.475).
3. Move the via 0.075 mm to (11.575, 36.475). Clearance ≥ 0.35 mm.

### RG-03: grid-router debris on the remaining rerouted nets (Major, R7)

These instances violate §3 (acute angles, staircases) or the clean-routing list (needless vias and hops,
detours). All are R7-new copper from `m3_design/r7_reroute_session.json`.

**Acute hairpins.**

- **BAT_SW_RETURN F.Cu (11.9, 44.125), 45°.** The R6 diagonal (11.2, 44.825)→(11.9, 44.125) ran to an R6 via that
  R7 removed. The session then restarts there and goes back south: (11.9, 44.125)→(11.9, 45.025)→
  (13.3, 46.425)→(14.1, 46.425).
  - Fix: (11.2, 44.825)→(11.7, 44.825)→(13.3, 46.425)→(14.1, 46.425). Clearance ≥ 0.21 mm (`cand.py`).
- **VLOGIC_SENSE B.Cu (35.1, 32.2467), 45°** (`img/vlogic.png`). The B.Cu leg runs (35.1, 32.2467)→ via
  (36.0, 31.3467). From that via an F.Cu leg runs straight back over the same line to the via (34.3, 33.2467): a
  1.27 mm hairpin across two layers on one alignment, plus a needless via.
  - Fix: one B.Cu link from (35.1, 32.2467) toward (34.3, 33.2467), and delete the via (36.0, 31.3467).
- **BUZZ_DRV F.Cu (1.55, 59.95), 45°.** A 1.84 mm diagonal stops 0.05 mm short of the via (1.55, 60.0), and a 0.05
  mm stub doubles back: a waypoint overshoot. Fix: end the diagonal at the via centre.

**Staircases.**

- **LED_RED F.Cu (34.15, 35.55)→(33.75, 32.65):** segments 0.283/1.6/0.283/0.9 mm.
- **LED_RED F.Cu (24.75, 50.25)→(32.65, 46.45):** six alternating segments of 2.97/0.2/1.84/2.6/0.57/1.3 mm.
- **PULLPIN_EXT B.Cu (33.8, 25.57)→(34.5, 30.87)→(36.2, 30.77):** 1.7/0.849/2.9/0.141 mm, then a 0.1 mm jog of
  1.2/0.141/0.4 mm.
- **BAT_SW_RETURN F.Cu (21.0, 29.925)→(15.0, 37.725):** 2.12/1.0/6.36/0.8 mm.
- **CAM_MCU_TX B.Cu at (36.55, 46.85):** 4.7 µm and 2.9 µm segments where the session joined a trimmed R6 track.

**Layer hopping.**

- **LED_YEL** (`img/ledyel.png`) has 6 vias and the layer sequence F→B→In2→F→In2→B→F between (36.6, 37.2) and
  (22.4, 43.9). The In2 and F hops are 1.2–2.4 mm long, at vias (30.0, 41.7), (28.2, 42.3), (25.8, 42.3) and
  (24.0, 42.3).
  - The F.Cu start also hooks south to y 39.3 and back up to y 37.2.
  - The R6 route had the same 6 vias but no hook.
- **VLOGIC_SENSE** hops via the pair (35.7, 53.3)/(34.0, 51.6), 2.4 mm.
- **PULLPIN** hops via (33.5675, 44.3404)/(33.5675, 42.2404), 2.1 mm, and B.Cu 2.75 mm.
- **BAT_SW_RETURN** hops on In2 for 1.3 mm at (15.0, 37.725)/(16.3, 37.725).

**Detours.**

- **LED_RED, U1.38→R32.1** (`img/ledred.png`): 62.7 mm for a 22.4 mm octile distance; R6 was 42.0 mm. The route
  leaves U1's aft edge forward and runs round the east of U1 to y 57. It then comes back aft along x 39.45 to
  R32, with 585° of cumulative turning.
- **PULLPIN_EXT:** 13.4 mm against 9.3 mm octile; R6 was 5.6 mm.

**Off-centre via joint.** The VLOGIC_SENSE In2 track ends 0.2275 mm off the centre of the via at (35.8044, 32.8066).
This is R6 copper, newly exposed.

**Fix.** Hand-route these nets, or rerun the router with bend and via costs and follow it with a clean-up pass:
merge collinear segments, remove hairpins and overshoots, and drop vias whose two legs overlap. Then re-check with
`scan.py`. Priority:

1. BAT_SW_RETURN hairpin
2. VLOGIC_SENSE hairpin
3. LED_YEL (one via instead of six)
4. LED_RED (aim for about 25–30 mm)
5. PULLPIN_EXT
6. CAM_MCU_TX and BUZZ_DRV micro-joints

### RG-04: dead copper and stubs where R7 deleted R6 parts (Major, R7 edit on R6 copper)

`orphan.py` found R6 track endpoints that sat in a pad R7 removed. R7's clean-up only deletes copper that KiCad
calls dangling, and a track ending in a same-net pour is not dangling, so these stayed (`img/v3_5056.png`):

- **GND F.Cu floating chain** (36.5, 63.65)→(36.5, 64.3)→(37.25, 65.05)→(37.275, 65.075)→(37.275, 66.0), 2.67 mm.
  It ran from the removed D131.2 to the removed C180.2. Both ends now sit in the pour; it touches no pad and no via.
- **GND F.Cu stubs ending in the pour:**
  - (25.5, 27.5)–(26.4, 28.4), 0.4 mm wide, removed C171.2;
  - (35.55, 61.35)–(35.55, 61.66)–(35.01, 62.2), removed D131.6;
  - (36.5, 53.65)→(36.5, 54.8)→(37.275, 55.575)→(37.275, 56.0)→(37.275, 56.615)→ via (36.99, 56.9), removed D130.2
    and C179.2. The last also has a 0.2/0.25 mm width change and an unmerged collinear node at (37.275, 56.0).
- **3V3 F.Cu star at the removed R205.1 (33.57, 35.0).** Three branches meet in free space, to (32.57, 35.0),
  (32.87, 34.3) and (33.17, 35.4), with a **45° acute angle** between the first two.
- **3V3 F.Cu junction at the removed D130.5 (36.43–36.5, 51.35–51.75):**
  - segments of 8 µm (36.429, 51.721–51.729), 21 µm and 30 µm;
  - a 45° acute T at (36.429, 51.721);
  - unmerged collinear nodes at (36.5, 51.35) and (36.45, 51.75).
- **Former GND 0.4 mm track (14.8, 18.85)–(14.8, 19.8), now wholly inside U30.9 and re-netted GNSS_RESET_N.** Its
  R6 GND via and C172.2 were removed. It sits 10 µm off the pad axis.
- **3V3 In2 stub** (17.58, 34.0)→(17.58, 36.5)→(17.57, 36.5), with a 10 µm jog, ending in the In2 3V3 pour. R7
  removed its R6 continuation (21.78, 29.8)–(17.58, 34.0).
- **3V3 F.Cu FB31 link split at (35.1, 25.1)** (2.95 + 1.5 mm, collinear, unmerged), where the dropped In2 band via
  was.

**Fix.** Delete the floating chain, the four GND stubs (keeping the stitching vias), the U30.9 leftover and the In2
stub. Collapse the R205.1 and D130.5 junctions to single clean nodes. Merge the FB31 link. Add a clean-up step to
`r7_pcb.py` that removes R6 copper whose only purpose was a deleted pad, even when a pour holds its end.

### RG-05: interface layer changes without adjacent GND vias (Major, R7)

AGENTS.md §3 asks for "ground vias next to layer changes". Of the 39 R7 transition vias on critical signal nets,
29 have no GND via within 1.5 mm, and 23 have none within 2.5 mm. Each entry is net, via centre (mm), and distance
to the nearest GND via (mm):

**U1-side columns:**

| Net | Via | Nearest GND via |
|---|---|---|
| RADIO_NRST | (9.3, 50.0) | 3.41 |
| RADIO_BUSY | (10.0, 49.5) | 3.07 |
| RADIO_DIO1 | (10.0, 50.5) | 4.03 |
| RADIO_MISO_MCU | (10.7, 48.5) | 2.55 |
| RADIO_MOSI_MCU | (9.4, 48.5) | 1.94 |
| RADIO_SCK_MCU | (10.0, 48.0) | 1.72 |

**Band-side columns:**

| Net | Via | Nearest GND via |
|---|---|---|
| RADIO_DIO1 | (9.4, 27.2) | 4.92 |
| RADIO_NRST | (10.0, 27.7) | 5.01 |
| RADIO_BUSY | (9.4, 28.2) | 5.75 |
| RADIO_MISO_MCU | (10.0, 28.7) | 5.91 |
| RADIO_MOSI | (9.4, 29.2) | 6.62 |
| RADIO_SCK | (10.0, 29.7) | 6.84 |
| RADIO_NSS | (9.4, 30.2) | 7.52 |

**GNSS corridor head:**

| Net | Via | Nearest GND via |
|---|---|---|
| GNSS_TP_MCU | (2.7, 51.0) | 7.68 |
| GNSS_RXD_MCU | (2.2, 51.5) | 8.38 |
| GNSS_TXD_MCU | (1.7, 52.0) | 9.08 |
| GNSS_RESET_N | (1.2, 52.5) | 9.78 |

**GNSS strip entry:**

| Net | Via | Nearest GND via |
|---|---|---|
| GNSS_RXD | (8.21, 25.2) | 2.69 |
| GNSS_TP_MCU | (9.31, 25.75) | 3.88 |
| GNSS_TXD_MCU | (7.11, 24.65) | 1.57 |

**Radio in or near the strip:**

| Net | Via | Nearest GND via |
|---|---|---|
| RADIO_NSS | (23.2, 17.3) | 3.28 |
| RADIO_NSS | (23.6, 15.27) | 3.61 |
| RADIO_TXEN | (31.13, 20.15) | 3.09 |
| RADIO_DIO1 | (32.4, 20.15) | 1.97 |
| RADIO_RXEN | (21.2, 30.45) | 2.74 |
| RADIO_RXEN | (23.8, 39.45) | 2.23 |
| RADIO_RXEN | (21.2, 44.45) | 3.61 |

**QSPI_IO0 surgery:**

| Net | Via | Nearest GND via |
|---|---|---|
| QSPI_IO0 | (15.55, 50.85) | 1.61 |
| QSPI_IO0 | (12.9, 44.4) | 3.55 |

**Fix.** Add a GND via within about 1 mm of each transition. One via can serve two adjacent signal vias. Possible
places:

- the U1-side columns: x ≈ 8.7 and 11.3 between rows 48–50.5;
- the band-side columns: x ≈ 8.7 at y 27.7, 28.7, 29.7. B.Cu x 6.3–9.0 is free apart from five GND vias (`obst.py`);
- the GNSS head: y ≈ 53.2 beside x 1.2–2.7;
- the radio vias in the strip: fill the lattice gaps beside them;
- the QSPI_IO0 vias.

Inference: under the B.Cu corridor, In2 is the BAT_IN plane. The B.Cu legs therefore reference BAT_IN, and a GND
via only serves the F.Cu/In1 side. That is the reason to keep the vias close.

### RG-06: duplicated and overlapping copper in R6 (Major, R6, widespread)

The untouched R6 copper contains 247 overlap-debris instances in column C:

- 7 exact duplicate segments;
- 65 collinear overlaps (49 on critical nets);
- 70 side-by-side overlaps (56 critical);
- 43 crossings without a node (35 critical);
- 57 fold-back 0° junctions (43 critical);
- 5 overlap-only joints.

Their nets: USB_LIMITED 60, 3V3 26, 3V3A 26, RAW_PROTECTED 20, CAM_IO_3V3 13, VLOGIC 12, GND 10, CAM_5V 9, NRST 8,
VBUS 8, CAM_FB 7, CAM_5V_SENSE 6, BAT_IN 5, and others. Worst cases:

- **USB_LIMITED B.Cu, x 28.7–31.6, y 27.85–46.55** (`img/usblim.png`). Drawn twice, at 0.4 mm and 0.3 mm, offset
  0.025–0.05 mm, with a split loop between x 30.8 and x 31.525/31.6 for y 28.15–34.6.
- **CAM_IO_3V3 B.Cu** (43.05, 39.95–46.15) against (42.925, 39.8–46.9): offset 0.125 mm, 6.2 mm long. Also
  (44.525, 33.8–38.2) against (44.55, 33.75–38.45), offset 0.025 mm (`img/camio.png`).
- **3V3 F.Cu** (27.8, 62.77–68.87) against (27.9, 62.75–67.75): offset 0.1 mm, 4.98 mm long (`img/v3_27.png`).
- **RAW_ACT_SENSE In2** (14.63, 73.0–78.0) lies wholly inside (14.63, 57.7–78.0).
- **NRST In2** (30.535, 47.25–50.55) against (30.4, 46.6–50.1): offset 0.135 mm, 2.85 mm long.
- **CAM_5V_SENSE F.Cu exact duplicates** (23.35, 45.95–46.75) and (23.05, 47.05)–(23.35, 46.75).
- **Overlap-only joints:**
  - GND F.Cu (11.7, 38.575) to the via (12.0, 38.875);
  - GND F.Cu (21.9265, 87.6298) to R127.2;
  - GND B.Cu (17.3498, 59.9256);
  - RAW_ACT F.Cu (5.3, 82.2);
  - ACT_FET_S B.Cu (6.45, 94.7).

**Fix.** Net by net, keep one conductor of the required width (IPC-2152 where it carries current) and delete the
copies. Then rerun `scan.py` until the overlap categories are zero. Actuator and pyro nets touched here need
`check_actuators` re-baselined.

### RG-07: PYRO1_GATE drawn twice (Major, R6, pyro)

**Evidence** (`img/pyrogate.png`). F.Cu, net PYRO1_GATE, between TP122.1 (20.45, 92.4), R126.2 (21.6, 92.4),
C126.1 (23.4, 92.1), R128.1 (24.7, 91.93) and Q124.4 (26.0, 91.775).

There is a 0.3 mm trunk (26.0, 91.9)–(21.6, 91.9). It passes through C126.1 and R128.1 and ends 0.5 mm off the
centre of R126.2 and 0.125 mm off the centre of Q124.4. Beside it is a second, 0.2 mm chain:

- (21.6, 92.4)→(22.2483, 92.4)→(22.5483, 92.1)→(23.4, 92.1)
- (24.7, 91.93)→(25.2217, 91.93)→(25.3767, 91.775)→(26.0, 91.775)

The two copies overlap side by side at offsets 0.125, 0.2 and 0.03 mm, cross without a node at (25.2517, 91.9),
and form a 0.219 mm tiny jog.

**Fix.** Keep a single centred chain (TP122→R126.2→C126.1→R128.1→Q124.4) at one width. Delete the 0.3 mm trunk or
the 0.2 mm doglegs. Re-baseline `check_actuators` afterwards.

### RG-08: acute angles, staircases and micro-segments in R6 copper (Major, R6)

**Genuine 45° acute junctions outside pads: 27 in column C, 20 of them on critical nets.**

| Net | Layer | Junction(s) |
|---|---|---|
| PYRO1_COLD | F.Cu | (29.3629, 85.7429) |
| PYRO1_COLD | B.Cu | (18.95, 112.3), (18.92, 112.3) |
| IMU_CS | F.Cu | (24.35, 66.75), (37.35, 79.75) |
| CAM_5V | B.Cu | (35.4939, 33.4639), (35.53, 33.5) |
| 3V3A | B.Cu | (38.68, 77.8) |
| GND | B.Cu | (27.94, 55.3), (14.6, 80.1) |
| 3V3 | F.Cu | (31.15, 54.55), (7.9, 80.6902) |
| 3V3 | B.Cu | (27.82, 62.8) |
| BAT_IN | F.Cu | (9.35, 40.17) |
| RAW_PROTECTED | B.Cu | (37.2, 83.6), (37.2, 83.575) |
| VBUS | B.Cu | (9.3, 70.7) |
| USB_LIMITED | B.Cu | (24.1272, 61.6228) |
| CAM_INPUT_LIMITED | B.Cu | (34.3, 93.5), (34.5, 93.5) |

Most of them are 20–150 µm hooks at a segment end. Examples: VBUS (9.3, 70.7) ends a 1.56 mm diagonal with a 0.02 mm
segment back; IMU_CS (37.35, 79.75) ends an 18.4 mm diagonal with a 0.15 mm segment back.

**Staircases:** 15 in total, 8 on critical nets.

| Net | Layer | Run | Segments (mm) |
|---|---|---|---|
| SPI1_MOSI | F.Cu | (30.25, 73.2)→(34.56, 80.96) | 2.475/0.25/3.606/3.2/0.014 |
| SPI1_SCK | B.Cu | (22.25, 65.65)→(34.35, 81.65) | – |
| PYRO1_CONT | F.Cu | (34.72, 84.72)→(42.22, 82.52) | 0.849/2.5/0.566/2.8/1.697 |
| VBUS | In2 | (9.28, 70.7)→(11.0, 76.35) | – |
| CAM_5V | B.Cu | (40.2, 32.45)→(35.49, 33.46) | – |
| 3V3 | In2 | (27.85, 62.75) | – |
| 3V3 | F.Cu | (30.63, 31.34) | – |
| GND | B.Cu | (42.85, 51.75) | – |

The R6 staircase render is `img/r6stairs.png`.

**Small segments:** 51 tiny jogs, 110 mid-route jogs under 0.2 mm, and 274 segments shorter than 50 µm (156 of them
on critical nets).

All instances are listed in Appendix A.

**Fix.** Redraw each hook and staircase as a single straight or one-bend route ending at the pad or via centre.
Start with the pyro, SPI and IMU_CS ones.

### RG-09: R6 critical-net layer changes without a GND via (Major, R6)

23 vias carry a critical signal across layers with no GND via within 1.5 mm. Distances are to the nearest GND via:

**Pyro and arm sense:**

| Net | Via | Layers | Nearest GND via (mm) |
|---|---|---|---|
| PYRO1_COLD | (18.85, 102.7) | B/In2 | 5.97 |
| PYRO1_COLD | (28.72, 84.5) | – | 4.28 |
| ARM1_SENSE | (25.28, 47.3) | – | 3.61 |
| ARM1_SENSE | (18.18, 91.3) | – | 6.68 |
| ARM1_SENSE | (14.55, 97.55) | – | 11.34 |
| ARM1_SENSE | (14.55, 94.15) | – | 11.10 |
| PYRO1_GATE_N | (31.9, 59.23) | – | 1.61 |
| PYRO1_GATE_N | (23.0, 88.33) | – | 1.82 |
| PYRO1_CONT | (41.1, 78.80) | – | 5.00 |
| PYRO1_CONT | (34.72, 84.72) | – | 1.85 |
| PYRO1_CONT | (34.52, 64.32) | – | 2.18 |
| PYRO1_CONT | (37.22, 67.02) | – | 2.16 |
| PYRO1_CONT | (41.0, 75.0) | – | 3.77 |
| PYRO1_CONT | (34.02, 57.92) | – | 3.14 |
| ARM1_SENSE_MCU | (24.35, 44.65) | – | 1.85 |

**USB:**

| Net | Via | Nearest GND via (mm) |
|---|---|---|
| USB_DM | (10.05, 76.3) | 5.84 |
| USB_DP | (8.9, 76.35) | 6.12 |
| USB_DP | (8.9, 74.75) | 4.62 |

**SPI and QSPI:**

| Net | Via | Nearest GND via (mm) |
|---|---|---|
| QSPI_IO1 | (13.0, 51.5) | 3.64 |
| SPI1_SCK | (22.25, 65.65) | 2.19 |
| SPI1_MISO | (28.55, 74.25) | 4.02 |
| IMU_CS | (37.2, 80.07) | 3.45 |
| IMU_CS | (25.1, 66.77) | 2.37 |

**Fix.** Add a GND via within about 1 mm of each. In the pyro block, respect the pyro clearance rules in
`m3.kicad_dru`.

### RG-10: off-angle 3V3 segment (Major, R6)

B.Cu, 3V3, 0.25 mm, (41.35, 58.55)→(42.95, 57.15): heading 318.81°, 3.81° off 45°, 0.141 mm lateral error over
2.126 mm.

- It is the only segment on the board outside 0/45/90. The other 55 deviations are nm rounding below 2 µm.
- The step B handoff (§4 item 13) records it as inherited. It still breaks the §3 rule.

**Fix.** Redraw it as a 45° segment plus a straight. Δx 1.6, Δy −1.4 gives, for example, a 1.4 mm diagonal and a
0.2 mm horizontal.

### RG-11: band fan-in jogs, width consistency, corners, clock proximity (Minor, R7)

**Fan-in jogs.** Each band lane has a 45° jog right after its via. The jogs take the lanes from the 0.5 mm via
stagger (x 9.4/10.0) to the 0.4 mm lane pitch. Lateral offsets: NRST 0.1 mm (0.141 mm diagonal), BUSY 0.2, MISO
0.3, MOSI 0.4, SCK 0.5, NSS 0.6 mm. The jog is followed by the chamfer of the turn north.

- The staircase heuristic flags NRST, BUSY, SCK and MISO_MCU.
- The reviewer reads them as a deliberate bus compaction, not steps, so they are Minor. The NRST 0.1 mm offset is a
  tiny jog by any definition.
- Fix: put the band-side vias on the 0.4 mm lane rows, or run the band at 0.5 mm pitch.

**Width.**

- RADIO_RXEN necks down from 0.2 to 0.15 mm mid-run at (20.6, 25.4), at a free node.
- The interface class mixes widths: 0.2 mm legs in the strip (RXEN, NRST, DIO1, GNSS_TP/TXD_MCU leads) against
  0.15 mm in the corridor.

**Unmerged collinear segments:** RADIO_DIO1 at (10.6, 27.2) (1.2 + 7.5 mm) and RADIO_RXEN at (20.6, 25.4).

**90° corners where a chamfer fits:**

- RADIO_RXEN F.Cu (18.35, 44.75)
- QSPI_IO0 B.Cu (12.9, 50.85)
- VBUS_SENSE In2 (15.65, 53.2), which joins R6 by a 0.2 mm leg and a 0.54 mm diagonal

**Clock proximity.** RADIO_RXEN F.Cu (23.5, 32.75–39.15) runs beside QSPI_CLK (23.15, 34.85–44.35) for 4.3 mm at a
0.175 mm edge gap (`img/rxen.png`).

### RG-12: corridor wider than needed; lanes squeeze the inline resistors (Minor, R7)

The radio lanes leave the vias at x 9.3–10.7 and go out to columns x 3.2–6.2. They run 17–19 mm south, then come
back east to vias at x 9.4/10.0 (`img/corridor_b.png`). Each lane goes 3.1–6.8 mm west of its via columns, each way.

Meanwhile B.Cu x 6.3–9.0, y 30.6–47.0 holds only GND vias: (8.35, 38.73), (6.85, 40.5) and C84's three at x 9.0
(`obst.py`). The path/octile ratios of the radio lines are 1.57–1.77.

The lanes pass the pads of the inline R313, R315 and R306 at 0.155 mm:

| Lane | Position | Passes |
|---|---|---|
| NSS | x 6.2 | R313 |
| SCK | x 5.7 | R315 |
| MISO_MCU | x 4.7 | R315 |
| GNSS_TP_MCU | x 2.7 | R306 |
| GNSS_TXD_MCU | x 1.7 | R306 |

These are the only R7 tracks below 0.17 mm clearance. The bus itself is clean: 0.5 mm pitch, nested chamfers
(`img/corner_top.png`, `img/corner_bot.png`).

**Fix.** Move the column block about 2.5 mm east, with the two stitching vias and R313/R315/R306, so the lanes clear
the resistor pads by ≥ 0.25 mm. This saves about 5 mm per radio lane.

### RG-13: GNSS limiter routing (Minor, R7)

B.Cu, under U30 (`img/limiter.png`).

**ANT_SRC loop.** GNSS_ANT_SRC runs from Q32.1 (6.0, 11.05) to R300.2 (8.25, 11.825) in 6.63 mm for a 2.64 mm
distance. It goes south round Q32.2 with 180° of turning, because the VCC_RF sense line (R300.1→Q32.2) crosses it
topologically. The fix is placement: rotate or re-pin Q32 or R300 so the sense pair does not cross.

**Pad-internal jogs:**

- VCC_RF has a 0.285 mm horizontal inside R300.1 between two offset diagonals.
- ANT_SRC's three-way junction sits 0.175 mm off the R300.2 centre, with a 45° acute angle inside the pad.
- GNSS_ANT_GATE has 0.14 mm and 0.12 mm stubs inside R301.2 and R302.1.

### RG-14: pad entries in the strip (Minor, R7)

- **3V3_RADIO at C310.1** (`img/radio3v3.png`): it enters at (36.35, 19.6), goes to the centre (36.78, 19.6) and
  folds back 45° to (36.58, 19.4) before running north. The trunk at x 36.58 misses the pad centre by 0.2 mm.
- **3V3_GNSS:** an H-link (12.61→13.71, 20.3) joins U30.7 and U30.8 0.6 mm from their centres.
- **GNSS_SAFEBOOT_N** enters TP30 at 45°, 0.85 mm off centre.
- **3V3_RADIO** has a 90° corner at (24.2, 21.6) into R310.

In R7 copper, 41 track ends sit more than 0.1 mm off the centre of a small pad (27 on critical nets). The ones not
named here are the long LCC pads of U30/U31, where an outer-end entry is normal.

### RG-15: R6 minor style debt (Minor, R6)

- 60 width changes at free nodes (53 critical) and 16 at vias.
- 24 unmerged collinear joints.
- 232 sub-0.2 mm segments wholly inside pads; 191 track ends more than 0.1 mm off the centre of a small pad.
- 26 track ends held only by a same-net pour (GND 18, 3V3 7, ACT_FET_S 1).
- 26 same-net signal via pairs closer than 1.2 mm.
- Large detours on slow nets:
  - SWCLK J2.4→U1.76: 118 mm and 14 vias for 33 mm;
  - SWDIO: 70.5 mm and 11 vias for 36 mm;
  - CAM_PWR_EN: 81.5 mm and 8 vias for 32.6 mm;
  - SERVO2_OUT: 37 mm for 16.9 mm.
- U9.10 (ITIMER, no connect) carries a 0.25 mm track joining its two pad halves. It is harmless.

## 5. Worst ten elsewhere (non-critical nets)

Each item gives copper origin, net, layer, location and measurement:

1. R6, RAW_ACT_SENSE, In2: the segment (14.63, 73.0–78.0) lies wholly inside (14.63, 57.7–78.0). 5.0 mm collinear
   overlap.
2. R6, CAM_IO_3V3, B.Cu: (43.05, 39.95–46.15) against (42.925, 39.8–46.9). Side-by-side, offset 0.125 mm, 6.2 mm
   long.
3. R6, CAM_IO_3V3, B.Cu: (44.525, 33.8–38.2) against (44.55, 33.75–38.45). Offset 0.025 mm, 4.4 mm long.
4. R7, LED_RED, F.Cu/B.Cu: U1.38 to R32.1 is 62.7 mm against a 22.4 mm octile distance (2.8×), with two staircases.
5. R7, PULLPIN, F.Cu: the duplicate route of RG-01. PULLPIN is the launch-detect input.
6. R7, LED_YEL: 6 vias and F/B/In2 hops of 1.2–2.4 mm between (30.0, 41.7) and (22.4, 43.9).
7. R6, NRST, In2: (30.535, 47.25–50.55) against (30.4, 46.6–50.1). Offset 0.135 mm, 2.85 mm long, plus two
   crossings without a node.
8. R6, SWCLK: 118 mm and 14 vias for a 33 mm connection.
9. R6, CAM_FB, F.Cu: (44.525, 93.9)–(42.325, 96.1) against (43.675, 94.5)–(41.975, 96.2). Offset 0.177 mm, 2.1 mm
   long, plus a collinear overlap at (42.075, 96.2).
10. R6, CAM_5V_SENSE, F.Cu: exact duplicate segments (23.35, 45.95–46.75) and (23.05, 47.05)–(23.35, 46.75).

## 6. Images

Scratch directory `…/scratchpad/rg/img/`, rendered by `render.py`:

- Tracks in layer colours: F red, In1 green, In2 orange, B blue.
- Black centrelines and end dots.
- Vias: GND green, other nets yellow.
- Faded copper is either not the highlighted net or, with `--r7only`, R6 copper.

| File | Shows |
|---|---|
| overview_r7.png, overview_r7_top.png | Whole board and the aft 60 mm, R7-new copper saturated |
| rerouted.png | The 13 rerouted nets, labelled |
| pullpin.png | RG-01 tangle |
| batilim.png | RG-02 duplicate link |
| vlogic.png, ledyel.png, ledred.png | RG-03 hairpin, hops, detour |
| v3_5056.png | RG-04 D130.5/C179 remnants |
| u30pins.png | U30 lower pins, the re-netted 0.4 mm track in U30.9 |
| corridor_b.png, corner_top.png, corner_bot.png | Corridor bus and nested corners (RG-12, RG-05) |
| band.png | F.Cu band and fan-in jogs (RG-11) |
| u1fan.png | U1 left-side escape (clean) |
| strip_f.png, strip_b.png | RF strip, F and B (the RF lines are clean) |
| limiter.png | RG-13 |
| radio3v3.png | RG-14 C310.1 fold |
| rxen.png | RXEN beside QSPI_CLK |
| usblim.png, camio.png, v3_27.png | RG-06 double-drawn power conductors |
| pyrogate.png | RG-07 |
| r6stairs.png | RG-08 SPI1_MOSI kink and PYRO1_CONT steps |

## 7. What is clean

- **RF lines:** each of the four is two straight 0.30 mm F.Cu segments, centred on the SMA centre pin, the 0 Ω pad
  and the module pin.
  - D30.1, D31.1 and L30.2 sit on the line by design ("passes through pad" is intended here).
  - Their DNP shunt stubs are 0.94 mm, as recorded.
- **U1 escape:** straight, at pad centres.
- **Corridor and band buses:** constant pitch, nested 45° corners. Their only defects are the GND vias (RG-05), the
  fan-in jogs (RG-11) and the resistor squeeze (RG-12).
- **No dangling ends** (open track ends with no copper) and **no vias connected on fewer than two layers**, on either
  board.

## Appendix A: every instance on a critical net

- Column letter: A = R7-new copper, B = R6 copper new in R7, C = untouched R6.
- Critical nets are the RF, pyro/arm, HSE, USB_DP/DM, QSPI/SPI/IMU_CS/radio-SPI and other RADIO_*/GNSS_* nets, and
  the power rails and GND.
- 45° pad entries (262 on critical nets) and 90° corners (62) are counted in §3 but not listed: the rule allows them.
- Coordinates are in mm, on the R7 board.

### Off-angle segments (1)

- C 3V3 B.Cu (41.35, 58.55): to (42.95, 57.15), 3.814 deg off, lateral 0.1414 mm

### Staircases (12)

- A RADIO_BUSY F.Cu (9.4, 28.2): to (21.2, 27.7), segs [1.2, 0.283, 10.1, 0.424]
- A RADIO_MISO_MCU F.Cu (10, 28.7): to (21.6, 27.866), segs [0.6, 0.424, 10.166, 0.755]
- A RADIO_NRST F.Cu (10, 27.7): to (19, 27.1), segs [0.6, 0.141, 7.8, 0.707]
- A RADIO_SCK F.Cu (10, 29.7): to (22.4, 28.198), segs [0.6, 0.707, 10.298, 1.417]
- C 3V3 In2.Cu (27.85, 62.75): to (28.9421, 56.6579), segs [2.306, 0.243, 0.304, 1.302, 2.389]
- C 3V3 F.Cu (30.63, 31.3417): to (31.55, 28.6), segs [0.566, 1.8, 0.028, 0.022, 0.707]
- C CAM_5V B.Cu (40.2, 32.45): to (35.4939, 33.4561), segs [3.2, 1.414, 0.5, 0.009]
- C GND B.Cu (42.85, 51.75): to (44.65, 54.95), segs [0.99, 0.3, 1.556, 1.1]
- C PYRO1_CONT F.Cu (34.72, 84.7217): to (42.22, 82.5217), segs [0.849, 2.5, 0.566, 2.8, 1.697]
- C SPI1_MOSI F.Cu (30.25, 73.2): to (34.56, 80.96), segs [2.475, 0.25, 3.606, 3.2, 0.014]
- C SPI1_SCK B.Cu (22.25, 65.65): to (34.35, 81.65), segs [7.92, 3.6, 8.627, 0.3, 0.566]
- C VBUS In2.Cu (9.28, 70.7): to (11, 76.35), segs [2.404, 3.9, 0.028, 0.03]

### Extra-bend runs (7)

- A RADIO_MOSI F.Cu (9.4, 29.2): to (22, 28.032), segs [1.2, 0.566, 10.232, 1.086]
- A RADIO_NSS F.Cu (9.4, 30.2): to (23.2, 28.4), segs [1.2, 0.849, 10.8, 1.697]
- C RAW_PROTECTED In2.Cu (19.15, 103.27): to (33.55, 86.67), segs [10.041, 1.0, 9.758, 1.2, 0.566]
- C SW_NODE B.Cu (18.32, 36.05): to (22.92, 34.05), segs [2.2, 1.131, 0.4, 1.697]
- C USB_LIMITED B.Cu (16.8, 81.55): to (28.7, 46.55), segs [3.394, 12.6, 13.435, 10.5]
- C USB_LIMITED B.Cu (28.7, 57): to (31.6, 34.5), segs [10.5, 0.283, 4.5, 1.414, 4.6, 2.404]
- C USB_LIMITED B.Cu (28.725, 57): to (31.525, 28.9), segs [10.5, 0.566, 6.1, 1.131, 3.0, 2.263, 5.7]

### Tiny jogs (24)

- B 3V3 In2.Cu (17.57, 40.83): to (17.58, 34), segs [4.33, 0.01, 2.5]
- C 3V3 B.Cu (15.88, 45.9): to (15.85, 44.25), segs [1.6, 0.042, 0.02]
- C 3V3 B.Cu (27.38, 45.9): to (27.35, 44.25), segs [1.6, 0.042, 0.02]
- C 3V3 F.Cu (27.8, 43.625): to (27.375, 44.25), segs [0.566, 0.2, 0.035]
- C 3V3 F.Cu (34.9, 53.05): to (34.925, 56), segs [2.9, 0.035, 0.025]
- C 3V3 F.Cu (36.5, 51.65): to (34.9, 53.05), segs [1.556, 0.2, 0.424]
- C 3V3A B.Cu (36.3632, 52.1393): to (36.4632, 60.8393), segs [7.0, 0.141, 1.6]
- C CAM_INPUT_LIMITED B.Cu (38.95, 87.6): to (40.3, 87.4), segs [0.7, 0.283, 0.45]
- C GND B.Cu (17.4, 60.8): to (17.3498, 59.9256), segs [0.722, 0.071, 0.102]
- C GND B.Cu (32.2, 100.73): to (32.4, 103.675), segs [0.555, 0.283, 2.19]
- C GND B.Cu (39.52, 77.5): to (39.63, 76.2), segs [0.542, 0.156, 0.648]
- C IMU_CS F.Cu (25.1, 66.77): to (24.35, 66.75), segs [0.7, 0.028, 0.03]
- C PYRO1_GATE F.Cu (26, 91.775): to (24.7, 91.93), segs [0.623, 0.219, 0.522]
- C QSPI_CLK F.Cu (22.85, 45.95): to (23.15, 34.85), segs [1.3, 0.424, 9.5]
- C QSPI_NCS B.Cu (20.15, 47.35): to (26.75, 40.45), segs [6.223, 0.3, 3.111]
- C RAW_ACT F.Cu (12.6, 81.27): to (11.1, 79.37), segs [1.697, 0.4, 0.424]
- C RAW_PROTECTED B.Cu (36.8, 83.975): to (37.3, 83.5), segs [0.566, 0.025, 0.141]
- C SPI1_MISO B.Cu (34.79, 79.05): to (33.55, 79.25), segs [0.49, 0.283, 0.55]
- C SPI1_MOSI F.Cu (23.35, 66.55): to (32, 74.95), segs [9.405, 0.25, 2.475]
- C VBUS B.Cu (13.7, 79.65): to (12.2, 77.75), segs [0.849, 0.4, 1.273]
- C VBUS F.Cu (6.88, 77.7): to (9.88, 77.8), segs [1.0, 0.141, 1.9]
- C VBUS In2.Cu (9.88, 77.8): to (11, 76.38), segs [1.556, 0.3, 0.028]
- C VCAP2 F.Cu (12.6, 58.6): to (11.1, 58.5), segs [1.2, 0.141, 0.2]
- C VCAP2 F.Cu (14.3, 58.5): to (11.4, 58.6), segs [1.6, 0.141, 1.2]

### Acute 45 deg junctions outside pads/vias (22)

- B 3V3 F.Cu (33.57, 35): 45.0 deg, 3 branches
- B 3V3 F.Cu (36.429, 51.721): 45.0 deg, 3 branches
- C 3V3 B.Cu (27.82, 62.8): 45.0 deg, 2 branches
- C 3V3 F.Cu (31.15, 54.55): 45.0 deg, 2 branches
- C 3V3 F.Cu (7.9, 80.6902): 45.0 deg, 2 branches
- C 3V3A B.Cu (38.68, 77.8): 45.0 deg, 3 branches
- C BAT_IN F.Cu (9.35, 40.17): 45.0 deg, 2 branches
- C CAM_5V B.Cu (35.4939, 33.4639): 45.0 deg, 3 branches
- C CAM_5V B.Cu (35.53, 33.5): 45.0 deg, 2 branches
- C CAM_INPUT_LIMITED B.Cu (34.3, 93.5): 45.0 deg, 2 branches
- C CAM_INPUT_LIMITED B.Cu (34.5, 93.5): 45.0 deg, 3 branches
- C GND B.Cu (14.6, 80.1): 45.0 deg, 3 branches
- C GND B.Cu (27.94, 55.3): 45.0 deg, 2 branches
- C IMU_CS F.Cu (24.35, 66.75): 45.0 deg, 3 branches
- C IMU_CS F.Cu (37.35, 79.75): 45.0 deg, 2 branches
- C PYRO1_COLD B.Cu (18.92, 112.3): 45.0 deg, 2 branches
- C PYRO1_COLD B.Cu (18.95, 112.3): 45.0 deg, 2 branches
- C PYRO1_COLD F.Cu (29.3629, 85.7429): 45.0 deg, 3 branches
- C RAW_PROTECTED B.Cu (37.2, 83.575): 45.0 deg, 2 branches
- C RAW_PROTECTED B.Cu (37.2, 83.6): 45.0 deg, 2 branches
- C USB_LIMITED B.Cu (24.1272, 61.6228): 45.0 deg, 3 branches
- C VBUS B.Cu (9.3, 70.7): 45.0 deg, 2 branches

### Fold-back (0 deg) junctions (43)

- C 3V3 B.Cu (24.9, 34.2): 0.0 deg, 4 branches
- C 3V3 F.Cu (27.88, 62.75): 0.0 deg, 6 branches
- C 3V3 F.Cu (27.89, 62.75): 0.0 deg, 4 branches
- C 3V3 F.Cu (31.125, 54.5): 0.0 deg, 2 branches
- C 3V3 F.Cu (31.15, 54.525): 0.0 deg, 4 branches
- C 3V3 B.Cu (31.5, 45.225): 0.0 deg, 4 branches
- C 3V3 F.Cu (33.1, 82): 0.0 deg, 4 branches
- C 3V3 F.Cu (33.1, 82.0389): 0.0 deg, 3 branches
- C 3V3 F.Cu (34.6647, 36.1053): 0.0 deg, 4 branches
- C 3V3 F.Cu (34.67, 36.1): 0.0 deg, 2 branches
- C 3V3A B.Cu (31.6, 50): 0.0 deg, 4 branches
- C 3V3A B.Cu (37.88, 76.7): 0.0 deg, 2 branches
- C 3V3A B.Cu (37.91, 76.73): 0.0 deg, 4 branches
- C 3V3A B.Cu (39.2632, 51.1393): 0.0 deg, 4 branches
- C 3V3A B.Cu (40.0632, 51.9393): 0.0 deg, 3 branches
- C BAT_IN F.Cu (9.3, 40.85): 0.0 deg, 3 branches
- C BAT_IN F.Cu (9.8, 40.85): 0.0 deg, 3 branches
- C CAM_5V B.Cu (39.6, 104.8): 0.0 deg, 4 branches
- C GND B.Cu (39.1533, 45.4): 0.0 deg, 4 branches
- C RAW_PROTECTED F.Cu (12.6, 40.35): 0.0 deg, 3 branches
- C RAW_PROTECTED B.Cu (15.68, 32.4): 0.0 deg, 4 branches
- C RAW_PROTECTED B.Cu (15.7, 32.35): 0.0 deg, 2 branches
- C RAW_PROTECTED B.Cu (15.7, 35.75): 0.0 deg, 4 branches
- C RAW_PROTECTED B.Cu (27.7, 27.85): 0.0 deg, 4 branches
- C USB_LIMITED B.Cu (28.7, 46.55): 0.0 deg, 4 branches
- C USB_LIMITED B.Cu (28.7, 57): 0.0 deg, 4 branches
- C USB_LIMITED B.Cu (29.1, 46.15): 0.0 deg, 3 branches
- C USB_LIMITED B.Cu (29.9, 36.25): 0.0 deg, 4 branches
- C USB_LIMITED B.Cu (29.9, 39.25): 0.0 deg, 4 branches
- C USB_LIMITED B.Cu (30.5, 27.85): 0.0 deg, 4 branches
- C USB_LIMITED B.Cu (30.5, 27.9): 0.0 deg, 4 branches
- C USB_LIMITED B.Cu (30.8, 28.15): 0.0 deg, 3 branches
- C USB_LIMITED B.Cu (30.8, 28.2): 0.0 deg, 4 branches
- C USB_LIMITED B.Cu (30.8, 30.5): 0.0 deg, 4 branches
- C USB_LIMITED B.Cu (31.6, 31.35): 0.0 deg, 4 branches
- C USB_LIMITED B.Cu (31.6, 34.5): 0.0 deg, 4 branches
- C VBUS In2.Cu (11, 76.33): 0.0 deg, 4 branches
- C VBUS In2.Cu (11, 76.38): 0.0 deg, 4 branches
- C VBUS In2.Cu (12, 79.95): 0.0 deg, 4 branches
- C VBUS In2.Cu (12.6, 80.55): 0.0 deg, 2 branches
- C VLOGIC F.Cu (27.57, 27.2): 0.0 deg, 2 branches
- C VLOGIC F.Cu (27.57, 28.6): 0.0 deg, 4 branches
- C VLOGIC B.Cu (27.825, 28.55): 0.0 deg, 5 branches

### Acute junctions inside a pad or via (75)

- A 3V3_RADIO F.Cu (36.78, 19.6): 45.0 deg at pad
- A GNSS_ANT_GATE B.Cu (8.25, 15.57): 45.0 deg at pad
- A GNSS_ANT_SRC B.Cu (8.25, 12): 45.0 deg at pad
- C 3V3 B.Cu (26.1, 33): 0.0 deg at pad
- C 3V3 B.Cu (26.4, 33.3): 0.0 deg at pad
- C 3V3 F.Cu (27.85, 62.75): 0.0 deg at via
- C 3V3 F.Cu (27.9014, 39.7703): 44.92 deg at pad
- C 3V3 F.Cu (27.9014, 39.7714): 45.0 deg at pad
- C 3V3 In2.Cu (30.63, 31.3417): 45.0 deg at via
- C 3V3 F.Cu (32, 82.03): 45.0 deg at pad
- C 3V3 B.Cu (32.3, 46.025): 0.0 deg at pad
- C 3V3A B.Cu (29.4, 50): 0.0 deg at pad
- C 3V3A B.Cu (29.4, 50.02): 0.0 deg at pad
- C 3V3A B.Cu (31.1, 50): 0.0 deg at via
- C 3V3A B.Cu (32.3, 49.3): 45.0 deg at pad
- C 3V3A B.Cu (40.0632, 54.6393): 45.0 deg at pad
- C ARM1_SENSE F.Cu (17.28, 92.4): 45.0 deg at pad
- C ARM1_SENSE B.Cu (24.38, 46.4): 0.0 deg at pad
- C ARM1_SENSE B.Cu (24.4, 46.42): 0.0 deg at pad
- C BAT_IN B.Cu (11.875, 33.35): 45.0 deg at pad
- C BAT_IN B.Cu (11.9, 33.35): 45.0 deg at pad
- C CAM_5V B.Cu (33.5, 107.5): 0.0 deg at pad
- C CAM_5V B.Cu (33.5, 107.525): 0.0 deg at pad
- C CAM_5V B.Cu (40.3, 105.45): 0.0 deg at pad
- C CAM_5V B.Cu (40.3, 105.5): 0.0 deg at pad
- C CAM_5V B.Cu (40.3, 105.525): 0.0 deg at pad
- C CAM_5V F.Cu (40.75, 40.125): 45.0 deg at pad
- C CAM_5V F.Cu (40.775, 40.1): 45.0 deg at pad
- C CAM_INPUT_LIMITED B.Cu (40.3, 90.1): 45.0 deg at pad
- C CAM_INPUT_LIMITED B.Cu (40.7, 94.4): 0.0 deg at pad
- C CAM_INPUT_LIMITED B.Cu (40.7, 94.45): 0.0 deg at pad
- C GND B.Cu (19.03, 89): 45.0 deg at pad
- C GND B.Cu (20.6, 34.2): 0.0 deg at pad
- C GND B.Cu (20.8, 34): 0.0 deg at pad
- C GND B.Cu (36.93, 71.175): 45.0 deg at pad
- C GND B.Cu (40.1, 45.4): 0.0 deg at pad
- C GND F.Cu (6.775, 41.3): 45.0 deg at pad
- C HSE_OUT B.Cu (23.2, 53.9): 45.0 deg at via
- C IMU_CS B.Cu (36.5, 80.77): 45.0 deg at pad
- C PYRO1_CONT_MCU B.Cu (32.17, 52.9): 0.0 deg at pad
- C PYRO1_CONT_MCU B.Cu (32.2, 52.9): 0.0 deg at pad
- C QSPI_CLK F.Cu (21.05, 33.35): 45.0 deg at pad
- C QSPI_IO0 F.Cu (21.07, 32.1): 0.0 deg at pad
- C QSPI_IO0 F.Cu (21.1, 32.1): 0.0 deg at pad
- C RAW_ACT F.Cu (23, 74.4): 45.0 deg at pad
- C RAW_ACT B.Cu (4, 105.98): 45.0 deg at pad
- C RAW_ACT B.Cu (9, 86.98): 45.0 deg at pad
- C RAW_PROTECTED F.Cu (13.1, 40.35): 0.0 deg at pad
- C RAW_PROTECTED F.Cu (14, 31.2): 45.0 deg at pad
- C RAW_PROTECTED B.Cu (15.7, 32.4): 0.0 deg at via
- C RAW_PROTECTED B.Cu (28.5, 27.85): 0.0 deg at pad
- C RAW_PROTECTED B.Cu (28.525, 27.85): 0.0 deg at pad
- C RAW_PROTECTED B.Cu (35.7, 85.675): 45.0 deg at pad
- C RAW_PROTECTED B.Cu (35.75, 85.67): 45.0 deg at pad
- C RAW_PROTECTED B.Cu (38.5, 83.475): 0.0 deg at pad
- C RAW_PROTECTED B.Cu (38.5, 83.5): 0.0 deg at pad
- C RAW_PROTECTED B.Cu (38.925, 85.7): 0.0 deg at pad
- C RAW_PROTECTED B.Cu (38.95, 85.7): 0.0 deg at pad
- C RAW_PROTECTED B.Cu (39.5, 80.975): 0.0 deg at pad
- C RAW_PROTECTED B.Cu (39.5, 81): 0.0 deg at pad
- C USB_LIMITED B.Cu (16.3, 81.55): 0.0 deg at pad
- C USB_LIMITED B.Cu (16.325, 81.55): 0.0 deg at pad
- C USB_LIMITED B.Cu (29.1, 40.55): 0.0 deg at via
- C USB_LIMITED B.Cu (29.825, 27.9): 45.0 deg at pad
- C USB_LIMITED B.Cu (29.875, 27.85): 45.0 deg at pad
- C USB_LIMITED B.Cu (29.9, 27.9): 0.0 deg at pad
- C VBUS In2.Cu (11, 76.35): 0.0 deg at via
- C VBUS B.Cu (13.725, 81.55): 45.0 deg at pad
- C VLOGIC B.Cu (18.1, 29.5): 0.0 deg at pad
- C VLOGIC B.Cu (18.12, 29.48): 0.0 deg at pad
- C VLOGIC B.Cu (20.8, 32): 45.0 deg at pad
- C VLOGIC B.Cu (28.505, 28.55): 0.0 deg at pad
- C VLOGIC B.Cu (28.525, 28.55): 0.0 deg at pad
- C VLOGIC B.Cu (29.875, 28.55): 0.0 deg at pad
- C VLOGIC B.Cu (29.925, 28.55): 0.0 deg at pad

### Segments shorter than 0.2 mm (255)

- A 3V3_GNSS F.Cu (12.61, 21.75): to (12.74, 21.88), 0.1838 mm, inside_pad
- A GNSS_ANT_GATE B.Cu (7.07, 14.39): to (7.07, 14.25), 0.14 mm, inside_pad
- A GNSS_ANT_GATE B.Cu (8.25, 15.45): to (8.25, 15.57), 0.12 mm, inside_pad
- A GNSS_ANT_SRC B.Cu (8.25, 12): to (8.25, 11.825), 0.175 mm, inside_pad
- A RADIO_NRST F.Cu (10.6, 27.7): to (10.7, 27.6), 0.1414 mm, jog
- C 3V3 F.Cu (12.23, 77.8): to (12.25, 77.78), 0.0283 mm, inside_pad
- C 3V3 F.Cu (12.25, 77.78): to (12.25, 77.75), 0.03 mm, inside_pad
- C 3V3 F.Cu (12.5, 89.2): to (12.5, 89.225), 0.025 mm, via-joint
- C 3V3 B.Cu (12.6, 59.48): to (12.6, 59.5), 0.02 mm, joint-via
- C 3V3 B.Cu (14.5, 59.88): to (14.6, 59.78), 0.1414 mm, inside_pad
- C 3V3 B.Cu (14.6, 59.58): to (14.5, 59.48), 0.1414 mm, jog
- C 3V3 B.Cu (14.6, 59.78): to (14.6, 59.58), 0.2 mm, pad-joint
- C 3V3 B.Cu (15.4721, 69.9971): to (15.475, 70), 0.0041 mm, inside_pad
- C 3V3 B.Cu (15.85, 44.27): to (15.85, 44.25), 0.02 mm, joint-via
- C 3V3 B.Cu (15.88, 44.3): to (15.85, 44.27), 0.0424 mm, jog
- C 3V3 In2.Cu (17.58, 36.5): to (17.57, 36.5), 0.01 mm, jog
- C 3V3 In2.Cu (24.85, 35): to (24.9, 35), 0.05 mm, joint-via
- C 3V3 B.Cu (27.35, 44.27): to (27.35, 44.25), 0.02 mm, joint-via
- C 3V3 F.Cu (27.375, 44.25): to (27.35, 44.25), 0.025 mm, joint-via
- C 3V3 B.Cu (27.38, 44.3): to (27.35, 44.27), 0.0424 mm, jog
- C 3V3 F.Cu (27.4, 44.025): to (27.4, 44.225), 0.2 mm, jog
- C 3V3 F.Cu (27.4, 44.225): to (27.375, 44.25), 0.0354 mm, jog
- C 3V3 F.Cu (27.8, 62.77): to (27.82, 62.75), 0.0283 mm, jog
- C 3V3 F.Cu (27.82, 62.75): to (27.85, 62.75), 0.03 mm, joint-via
- C 3V3 B.Cu (27.82, 62.8): to (27.85, 62.77), 0.0424 mm, jog
- C 3V3 B.Cu (27.85, 62.77): to (27.85, 62.75), 0.02 mm, joint-via
- C 3V3 F.Cu (27.85, 62.78): to (27.85, 62.75), 0.03 mm, joint-via
- C 3V3 F.Cu (27.88, 62.75): to (27.85, 62.75), 0.03 mm, joint-via
- C 3V3 F.Cu (27.89, 62.75): to (27.85, 62.75), 0.04 mm, joint-via
- C 3V3 F.Cu (27.9, 56.5): to (27.9, 56.3), 0.2 mm, joint-via
- C 3V3 F.Cu (27.9, 62.73): to (27.88, 62.75), 0.0283 mm, free-joint
- C 3V3 F.Cu (27.9, 62.74): to (27.89, 62.75), 0.0141 mm, free-joint
- C 3V3 F.Cu (27.9, 62.75): to (27.85, 62.75), 0.05 mm, joint-via
- C 3V3 F.Cu (27.9014, 39.7703): to (27.9014, 39.7714), 0.0012 mm, inside_pad
- C 3V3 F.Cu (27.93, 39.7417): to (27.9014, 39.7703), 0.0404 mm, inside_pad
- C 3V3 F.Cu (28.33, 40.2): to (28.33, 40.4), 0.2 mm, joint-via
- C 3V3 B.Cu (28.375, 40.4): to (28.33, 40.4), 0.045 mm, joint-via
- C 3V3 F.Cu (31.03, 29.1417): to (31.05, 29.1217), 0.0283 mm, jog
- C 3V3 F.Cu (31.05, 29.1): to (31.05, 29.1217), 0.0217 mm, jog
- C 3V3 F.Cu (31.125, 54.5): to (31.15, 54.525), 0.0354 mm, jog
- C 3V3 F.Cu (31.15, 54.525): to (31.15, 54.55), 0.025 mm, jog
- C 3V3 F.Cu (31.15, 54.55): to (31.1, 54.5), 0.0707 mm, joint-via
- C 3V3 F.Cu (32, 82.03): to (32, 82), 0.03 mm, inside_pad
- C 3V3 B.Cu (32.3, 46.125): to (32.3, 46.025), 0.1 mm, inside_pad
- C 3V3 F.Cu (33.1, 82): to (33.1, 82.0389), 0.0389 mm, jog
- C 3V3 F.Cu (34.65, 36.1): to (34.6553, 36.1053), 0.0075 mm, free-joint
- C 3V3 F.Cu (34.6553, 36.1053): to (34.6631, 36.1053), 0.0078 mm, joint-via
- C 3V3 F.Cu (34.6647, 36.1053): to (34.6631, 36.1053), 0.0016 mm, joint-via
- C 3V3 F.Cu (34.67, 36.1): to (34.6647, 36.1053), 0.0075 mm, jog
- C 3V3 F.Cu (34.9, 55.95): to (34.925, 55.975), 0.0354 mm, jog
- C 3V3 F.Cu (34.925, 55.975): to (34.925, 56), 0.025 mm, jog
- C 3V3 In2.Cu (35.1, 45.05): to (35.1, 45.025), 0.025 mm, joint-via
- C 3V3 F.Cu (35.4, 52.75): to (35.2, 52.75), 0.2 mm, jog
- C 3V3 F.Cu (36.025, 82.43): to (36, 82.43), 0.025 mm, joint-via
- C 3V3 F.Cu (36.035, 82.42): to (36.025, 82.43), 0.0141 mm, jog
- C 3V3 F.Cu (36.429, 51.729): to (36.429, 51.721), 0.0081 mm, jog
- C 3V3 F.Cu (36.45, 51.75): to (36.429, 51.729), 0.0297 mm, jog
- C 3V3 B.Cu (41.55, 53.87): to (41.58, 53.9), 0.0424 mm, inside_pad
- C 3V3 F.Cu (43.85, 77.92): to (44.035, 77.92), 0.185 mm, pad-via
- C 3V3A B.Cu (29.4, 49.975): to (29.4, 50.02), 0.045 mm, inside_pad
- C 3V3A B.Cu (29.4, 50): to (29.4, 50.02), 0.02 mm, inside_pad
- C 3V3A B.Cu (31.1, 50.02): to (31.1, 50), 0.02 mm, joint-via
- C 3V3A B.Cu (32.3, 49.3): to (32.3, 49.4), 0.1 mm, inside_pad
- C 3V3A B.Cu (32.3, 49.4): to (32.4, 49.5), 0.1414 mm, inside_pad
- C 3V3A B.Cu (35.48, 76.5): to (35.5, 76.52), 0.0283 mm, jog
- C 3V3A B.Cu (35.5, 76.52): to (35.5, 76.54), 0.02 mm, joint-via
- C 3V3A B.Cu (36.3632, 59.1393): to (36.4632, 59.2393), 0.1414 mm, jog
- C 3V3A B.Cu (37.88, 76.7): to (37.91, 76.73), 0.0424 mm, jog
- C 3V3A B.Cu (37.91, 76.73): to (37.91, 76.75), 0.02 mm, joint-via
- C 3V3A B.Cu (38.2632, 48.1393): to (38.2632, 48.1), 0.0393 mm, jog
- C 3V3A B.Cu (40.0632, 54.6393): to (40.1, 54.6025), 0.052 mm, inside_pad
- C 3V3A B.Cu (40.1, 54.6): to (40.1, 54.6025), 0.0025 mm, inside_pad
- C ARM1_SENSE F.Cu (18.18, 91.5): to (18.18, 91.3), 0.2 mm, joint-via
- C ARM1_SENSE B.Cu (24.38, 46.4): to (24.4, 46.42), 0.0283 mm, inside_pad
- C ARM1_SENSE B.Cu (24.4, 46.42): to (24.4, 46.43), 0.01 mm, inside_pad
- C ARM1_SENSE_MCU B.Cu (24.35, 45.55): to (24.37, 45.57), 0.0283 mm, inside_pad
- C ARM1_SENSE_MCU B.Cu (24.37, 45.57): to (24.4, 45.57), 0.03 mm, inside_pad
- C BAT_DAMP F.Cu (2.4, 35.275): to (2.4, 35.3), 0.025 mm, inside_pad
- C BAT_DAMP F.Cu (2.4, 35.325): to (2.4, 35.3), 0.025 mm, inside_pad
- C BAT_IN B.Cu (11.875, 33.35): to (11.9, 33.35), 0.025 mm, inside_pad
- C BAT_IN F.Cu (7.1, 36.05): to (7.1, 36.075), 0.025 mm, inside_pad
- C BAT_IN F.Cu (9.33, 40.15): to (9.3, 40.15), 0.03 mm, joint-via
- C BAT_IN F.Cu (9.35, 40.17): to (9.33, 40.15), 0.0283 mm, jog
- C BST B.Cu (17.05, 35.6): to (17.08, 35.63), 0.0424 mm, inside_pad
- C BST B.Cu (17.08, 35.63): to (17.08, 35.65), 0.02 mm, inside_pad
- C CAM_5V B.Cu (33.5, 107.525): to (33.5, 107.5), 0.025 mm, inside_pad
- C CAM_5V B.Cu (35.4939, 33.4561): to (35.4939, 33.4639), 0.0078 mm, jog
- C CAM_5V B.Cu (35.5, 33.45): to (35.4939, 33.4561), 0.0086 mm, jog
- C CAM_5V B.Cu (35.53, 33.5): to (35.53, 33.45), 0.05 mm, jog
- C CAM_5V B.Cu (40.2, 32.425): to (40.2, 32.45), 0.025 mm, inside_pad
- C CAM_5V B.Cu (40.3, 105.5): to (40.3, 105.45), 0.05 mm, inside_pad
- C CAM_5V B.Cu (40.3, 105.525): to (40.3, 105.5), 0.025 mm, inside_pad
- C CAM_5V F.Cu (40.775, 40.1): to (40.75, 40.125), 0.0354 mm, inside_pad
- C CAM_5V B.Cu (43.25, 34.525): to (43.3, 34.525), 0.05 mm, inside_pad
- C CAM_BST B.Cu (44.7, 95.35): to (44.7, 95.375), 0.025 mm, inside_pad
- C CAM_INPUT_LIMITED B.Cu (34.3, 93.5): to (34.4, 93.6), 0.1414 mm, jog
- C CAM_INPUT_LIMITED B.Cu (40.7, 94.45): to (40.7, 94.4), 0.05 mm, inside_pad
- C CAM_SW B.Cu (41.8, 97.7): to (41.8, 97.75), 0.05 mm, inside_pad
- C CAM_SW B.Cu (42.9, 94.425): to (42.9, 94.4), 0.025 mm, inside_pad
- C GND F.Cu (11.37, 65.57): to (11.45, 65.65), 0.1131 mm, joint-via
- C GND B.Cu (14.5, 60.72): to (14.6, 60.82), 0.1414 mm, inside_pad
- C GND B.Cu (14.6, 60.82): to (14.6, 60.92), 0.1 mm, inside_pad
- C GND B.Cu (14.6, 60.92): to (14.5, 61.02), 0.1414 mm, pad-joint
- C GND B.Cu (17.3498, 59.9256): to (17.3498, 60.0281), 0.1025 mm, free-joint
- C GND B.Cu (17.3498, 60.0281): to (17.4, 60.0783), 0.071 mm, jog
- C GND B.Cu (17.3757, 55.9992): to (17.4202, 55.9992), 0.0445 mm, via-free
- C GND B.Cu (19, 34.2): to (18.95, 34.2), 0.05 mm, inside_pad
- C GND B.Cu (19.05, 47.35): to (19.05, 47.1717), 0.1783 mm, via-joint
- C GND B.Cu (19.6, 35.2): to (19.5, 35.2), 0.1 mm, joint-via
- C GND F.Cu (21.9, 87.97): to (21.9265, 87.9435), 0.0375 mm, inside_pad
- C GND B.Cu (23.3, 52.66): to (23.3, 52.7), 0.04 mm, joint-via
- C GND F.Cu (23.9677, 90.7): to (23.9677, 90.8794), 0.1794 mm, jog
- C GND B.Cu (23.97, 63.6): to (23.97, 63.8), 0.2 mm, inside_pad
- C GND B.Cu (24.53, 89.3): to (24.55, 89.28), 0.0283 mm, jog
- C GND B.Cu (24.55, 89.275): to (24.55, 89.28), 0.005 mm, via-joint
- C GND F.Cu (26.4, 28.4): to (26.5, 28.4), 0.1 mm, joint-via
- C GND B.Cu (26.98, 62.58): to (27.05, 62.65), 0.099 mm, joint-via
- C GND B.Cu (27.54, 57.1): to (27.54, 56.9), 0.2 mm, inside_pad
- C GND F.Cu (27.645, 29.85): to (27.65, 29.85), 0.005 mm, joint-via
- C GND F.Cu (27.645, 30.05): to (27.645, 29.85), 0.2 mm, jog
- C GND B.Cu (27.94, 55.3): to (27.9, 55.3), 0.04 mm, joint-via
- C GND B.Cu (28.15, 44.25): to (28.22, 44.32), 0.099 mm, via-joint
- C GND B.Cu (28.4533, 31.6233): to (28.6, 31.6233), 0.1467 mm, jog
- C GND B.Cu (28.6, 32.6): to (28.6, 32.625), 0.025 mm, inside_pad
- C GND F.Cu (29.345, 29.95): to (29.345, 30.05), 0.1 mm, inside_pad
- C GND B.Cu (31.5, 47.1): to (31.3565, 47.1), 0.1435 mm, via-joint
- C GND B.Cu (32.2, 28.67): to (32.0887, 28.67), 0.1113 mm, inside_pad
- C GND B.Cu (33.95, 78.55): to (33.9, 78.5), 0.0707 mm, joint-via
- C GND F.Cu (34.3583, 28.92): to (34.3583, 28.9116), 0.0084 mm, jog
- C GND B.Cu (35.7, 84.125): to (35.8, 84.025), 0.1414 mm, inside_pad
- C GND B.Cu (36.4, 76.54): to (36.5, 76.54), 0.1 mm, joint-via
- C GND B.Cu (37.25, 25.35): to (37.3, 25.3), 0.0707 mm, joint-via
- C GND F.Cu (37.25, 65.05): to (37.275, 65.075), 0.0354 mm, jog
- C GND B.Cu (37.755, 70.375): to (37.73, 70.375), 0.025 mm, joint-via
- C GND F.Cu (38.1829, 28.3217): to (38.3, 28.3217), 0.1171 mm, jog
- C GND B.Cu (39.52, 76.9583): to (39.63, 76.8483), 0.1556 mm, jog
- C GND B.Cu (39.585, 75.6583): to (39.63, 75.6583), 0.045 mm, jog
- C GND B.Cu (40.9, 85.85): to (41.05, 85.85), 0.15 mm, jog
- C GND B.Cu (43.775, 47.6): to (43.825, 47.55), 0.0707 mm, inside_pad
- C GND F.Cu (44.525, 92.175): to (44.525, 92), 0.175 mm, inside_pad
- C GND F.Cu (6.725, 41.35): to (6.775, 41.3), 0.0707 mm, inside_pad
- C GND F.Cu (6.75, 41.3): to (6.775, 41.3), 0.025 mm, inside_pad
- C GND F.Cu (7.6317, 79.625): to (7.7217, 79.535), 0.1273 mm, jog
- C GND B.Cu (9.2, 108.6): to (9.3, 108.5), 0.1414 mm, inside_pad
- C IMU_CS F.Cu (24.38, 66.75): to (24.35, 66.75), 0.03 mm, jog
- C IMU_CS F.Cu (24.4, 66.77): to (24.38, 66.75), 0.0283 mm, jog
- C IMU_CS F.Cu (37.35, 79.75): to (37.2, 79.75), 0.15 mm, jog
- C PYRO1_BUS F.Cu (19.238, 95.36): to (19.385, 95.36), 0.147 mm, inside_pad
- C PYRO1_COLD B.Cu (18.92, 112.3): to (18.935, 112.285), 0.0212 mm, jog
- C PYRO1_COLD B.Cu (18.92, 112.3): to (18.95, 112.3), 0.03 mm, jog
- C PYRO1_COLD B.Cu (18.95, 112.3): to (18.85, 112.2), 0.1414 mm, jog
- C PYRO1_COLD B.Cu (28.75, 84.5): to (28.72, 84.5), 0.03 mm, joint-via
- C PYRO1_COLD F.Cu (29.35, 85.7): to (29.3629, 85.7129), 0.0182 mm, jog
- C PYRO1_COLD F.Cu (29.3629, 85.7129): to (29.3629, 85.7429), 0.03 mm, jog
- C PYRO1_CONT B.Cu (33.02, 52.9217): to (33.03, 52.9117), 0.0141 mm, inside_pad
- C PYRO1_CONT B.Cu (33.03, 52.9117): to (33.03, 52.9), 0.0117 mm, inside_pad
- C PYRO1_CONT_MCU B.Cu (32.2, 52.9): to (32.17, 52.9), 0.03 mm, inside_pad
- C PYRO1_CONT_MID F.Cu (28.73, 87.9): to (28.85, 87.9), 0.12 mm, inside_pad
- C PYRO1_CONT_MID F.Cu (28.85, 87.9): to (28.95, 87.8), 0.1414 mm, inside_pad
- C PYRO1_GATE_N F.Cu (21.6, 89.5818): to (21.6829, 89.5818), 0.0829 mm, jog
- C PYRO1_GATE_N F.Cu (29.4, 58.53): to (29.4, 58.5), 0.03 mm, inside_pad
- C PYRO1_GATE_N F.Cu (31.9, 59.23): to (31.9, 59.03), 0.2 mm, via-joint
- C PYRO1_IGN F.Cu (35.875, 95.8): to (35.975, 95.9), 0.1414 mm, inside_pad
- C PYRO1_IGN F.Cu (35.975, 95.9): to (36, 95.875), 0.0354 mm, inside_pad
- C PYRO1_IGN F.Cu (36, 95.875): to (36, 95.86), 0.015 mm, inside_pad
- C PYRO1_OUT F.Cu (27.42, 90.78): to (27.4, 90.8), 0.0283 mm, inside_pad
- C PYRO1_OUT F.Cu (28.68, 91.9): to (28.6887, 91.9087), 0.0123 mm, inside_pad
- C PYRO1_OUT F.Cu (28.6887, 91.9087): to (28.7, 91.9087), 0.0113 mm, inside_pad
- C PYRO1_OUT F.Cu (28.775, 93.85): to (28.7, 93.85), 0.075 mm, inside_pad
- C PYRO1_OUT F.Cu (35.98, 90.8): to (36, 90.78), 0.0283 mm, inside_pad
- C QSPI_CLK F.Cu (21.05, 33.35): to (21.07, 33.37), 0.0283 mm, inside_pad
- C QSPI_IO0 F.Cu (21.1, 32.1): to (21.07, 32.1), 0.03 mm, inside_pad
- C QSPI_IO1 F.Cu (28.1, 34.6): to (28.13, 34.63), 0.0424 mm, inside_pad
- C QSPI_IO2 F.Cu (28.1, 33.4): to (28.13, 33.37), 0.0424 mm, inside_pad
- C QSPI_IO3 F.Cu (21.1, 34.6): to (21.07, 34.63), 0.0424 mm, inside_pad
- C QSPI_NCS F.Cu (28.13, 35.93): to (28.13, 35.9), 0.03 mm, inside_pad
- C QSPI_NCS F.Cu (28.15, 35.95): to (28.13, 35.93), 0.0283 mm, inside_pad
- C RAW_ACT F.Cu (23, 74.4): to (23, 74.43), 0.03 mm, inside_pad
- C RAW_ACT B.Cu (4, 105.98): to (4, 105.99), 0.01 mm, inside_pad
- C RAW_ACT F.Cu (5.3, 82.17): to (5.3, 82.2), 0.03 mm, joint-free
- C RAW_ACT B.Cu (9, 86.98): to (9, 87), 0.02 mm, inside_pad
- C RAW_PROTECTED F.Cu (13.15, 40.35): to (13.1, 40.35), 0.05 mm, inside_pad
- C RAW_PROTECTED B.Cu (15.65, 32.37): to (15.68, 32.4), 0.0424 mm, free-joint
- C RAW_PROTECTED B.Cu (15.65, 32.4): to (15.7, 32.4), 0.05 mm, joint-via
- C RAW_PROTECTED B.Cu (15.68, 32.4): to (15.7, 32.4), 0.02 mm, joint-via
- C RAW_PROTECTED B.Cu (15.7, 32.35): to (15.7, 32.4), 0.05 mm, joint-via
- C RAW_PROTECTED F.Cu (25.85, 40.6): to (25.85, 40.5), 0.1 mm, joint-via
- C RAW_PROTECTED B.Cu (27.375, 27.875): to (27.4, 27.85), 0.0354 mm, jog
- C RAW_PROTECTED B.Cu (28.5, 27.85): to (28.525, 27.85), 0.025 mm, inside_pad
- C RAW_PROTECTED B.Cu (35.745, 85.675): to (35.7, 85.675), 0.045 mm, inside_pad
- C RAW_PROTECTED B.Cu (35.75, 85.67): to (35.745, 85.675), 0.0071 mm, inside_pad
- C RAW_PROTECTED B.Cu (35.75, 85.77): to (35.75, 85.67), 0.1 mm, inside_pad
- C RAW_PROTECTED B.Cu (37.2, 83.6): to (37.2, 83.575), 0.025 mm, jog
- C RAW_PROTECTED B.Cu (37.3, 83.5): to (37.2, 83.6), 0.1414 mm, jog
- C RAW_PROTECTED B.Cu (37.85, 54.7): to (37.95, 54.7), 0.1 mm, via-joint
- C RAW_PROTECTED F.Cu (37.95, 49.7): to (38.05, 49.8), 0.1414 mm, jog
- C RAW_PROTECTED B.Cu (37.95, 54.7): to (37.95, 54.7154), 0.0154 mm, joint-free
- C RAW_PROTECTED B.Cu (38, 54.7): to (37.95, 54.7), 0.05 mm, jog
- C RAW_PROTECTED B.Cu (38.5, 83.475): to (38.5, 83.5), 0.025 mm, inside_pad
- C RAW_PROTECTED B.Cu (38.9, 85.675): to (38.925, 85.7), 0.0354 mm, inside_pad
- C RAW_PROTECTED B.Cu (38.925, 85.7): to (38.95, 85.7), 0.025 mm, inside_pad
- C RAW_PROTECTED B.Cu (39, 85.7): to (38.95, 85.7), 0.05 mm, inside_pad
- C RAW_PROTECTED B.Cu (39.5, 80.975): to (39.5, 81), 0.025 mm, inside_pad
- C SPI1_MOSI F.Cu (34.55, 80.95): to (34.56, 80.96), 0.0141 mm, jog
- C SPI1_MOSI F.Cu (34.56, 80.96): to (34.6, 80.96), 0.04 mm, joint-via
- C SPI1_SCK F.Cu (22.35, 65.55): to (22.25, 65.65), 0.1414 mm, joint-via
- C SPI1_SCK B.Cu (35.74, 80.56): to (35.72, 80.54), 0.0283 mm, jog
- C SPI1_SCK B.Cu (35.75, 80.56): to (35.74, 80.56), 0.01 mm, jog
- C SPI1_SCK B.Cu (35.75, 80.75): to (35.75, 80.56), 0.19 mm, jog
- C SW_NODE B.Cu (17.9, 35.6): to (17.92, 35.62), 0.0283 mm, inside_pad
- C SW_NODE B.Cu (17.92, 35.62): to (17.92, 35.65), 0.03 mm, inside_pad
- C SW_NODE B.Cu (18, 34.2): to (17.9, 34.3), 0.1414 mm, inside_pad
- C SW_NODE B.Cu (22.9, 33.03): to (22.9, 33), 0.03 mm, inside_pad
- C SW_NODE B.Cu (22.92, 33.05): to (22.9, 33.03), 0.0283 mm, inside_pad
- C USB_LIMITED B.Cu (16.325, 81.55): to (16.3, 81.55), 0.025 mm, inside_pad
- C USB_LIMITED F.Cu (17.725, 83.15): to (17.925, 83.15), 0.2 mm, joint-via
- C USB_LIMITED B.Cu (24.1, 61.6): to (24.1228, 61.6228), 0.0322 mm, jog
- C USB_LIMITED B.Cu (24.1228, 61.6228): to (24.1272, 61.6228), 0.0045 mm, jog
- C USB_LIMITED F.Cu (25.975, 38.1519): to (25.9981, 38.1519), 0.0231 mm, inside_pad
- C USB_LIMITED F.Cu (25.9981, 38.1519): to (26, 38.15), 0.0026 mm, inside_pad
- C USB_LIMITED B.Cu (28.725, 57): to (28.7, 57), 0.025 mm, jog
- C USB_LIMITED B.Cu (29.825, 27.9): to (29.875, 27.85), 0.0707 mm, inside_pad
- C USB_LIMITED B.Cu (29.875, 27.875): to (29.875, 27.85), 0.025 mm, inside_pad
- C USB_LIMITED B.Cu (29.9, 27.85): to (29.875, 27.85), 0.025 mm, inside_pad
- C USB_LIMITED B.Cu (29.9, 27.9): to (29.875, 27.875), 0.0354 mm, inside_pad
- C VBUS In2.Cu (10.98, 76.3): to (11, 76.32), 0.0283 mm, jog
- C VBUS In2.Cu (10.98, 76.4): to (11, 76.38), 0.0283 mm, jog
- C VBUS In2.Cu (11, 76.32): to (11, 76.35), 0.03 mm, joint-via
- C VBUS In2.Cu (11, 76.33): to (11, 76.35), 0.02 mm, joint-via
- C VBUS In2.Cu (11, 76.38): to (11, 76.35), 0.03 mm, joint-via
- C VBUS F.Cu (11.3, 82.05): to (11.325, 82.05), 0.025 mm, joint-via
- C VBUS F.Cu (13.325, 82.15): to (13.225, 82.05), 0.1414 mm, inside_pad
- C VBUS B.Cu (13.725, 81.55): to (13.7, 81.55), 0.025 mm, inside_pad
- C VBUS B.Cu (14, 73.03): to (14, 73.23), 0.2 mm, joint-via
- C VBUS B.Cu (6.8, 76.3): to (6.9, 76.3), 0.1 mm, inside_pad
- C VBUS F.Cu (7.88, 77.7): to (7.98, 77.8), 0.1414 mm, jog
- C VBUS F.Cu (9.18, 70.7): to (9.28, 70.7), 0.1 mm, joint-via
- C VBUS B.Cu (9.3, 70.7): to (9.28, 70.7), 0.02 mm, joint-via
- C VBUS B.Cu (9.88, 77.77): to (9.88, 77.8), 0.03 mm, joint-via
- C VBUS B.Cu (9.9, 77.75): to (9.88, 77.77), 0.0283 mm, jog
- C VCAP1 In2.Cu (16.9, 44.3): to (16.85, 44.25), 0.0707 mm, joint-via
- C VCAP2 F.Cu (11.1, 58.5): to (11.3, 58.5), 0.2 mm, jog
- C VCAP2 F.Cu (11.4, 58.6): to (11.3, 58.5), 0.1414 mm, jog
- C VCAP2 F.Cu (12.6, 58.6): to (12.7, 58.5), 0.1414 mm, jog
- C VLOGIC B.Cu (18, 31.85): to (18, 31.8), 0.05 mm, inside_pad
- C VLOGIC B.Cu (18.1, 29.5): to (18.12, 29.48), 0.0283 mm, inside_pad
- C VLOGIC B.Cu (19, 31.8): to (18.95, 31.8), 0.05 mm, inside_pad
- C VLOGIC B.Cu (20.8, 31.975): to (20.8, 32), 0.025 mm, inside_pad
- C VLOGIC B.Cu (20.825, 31.85): to (20.825, 31.95), 0.1 mm, inside_pad
- C VLOGIC B.Cu (20.825, 31.95): to (20.8, 31.975), 0.0354 mm, inside_pad
- C VLOGIC B.Cu (27.825, 28.555): to (27.825, 28.55), 0.005 mm, jog
- C VLOGIC B.Cu (27.87, 28.6): to (27.825, 28.555), 0.0636 mm, jog
- C VLOGIC B.Cu (28.505, 28.55): to (28.525, 28.55), 0.02 mm, inside_pad
- C VLOGIC F.Cu (28.505, 29.95): to (28.505, 29.85), 0.1 mm, inside_pad
- C VLOGIC B.Cu (29.925, 28.55): to (29.875, 28.55), 0.05 mm, inside_pad

### Unmerged collinear segments (20)

- A 3V3 F.Cu (35.1, 25.1): lens [2.95, 1.5]
- A RADIO_DIO1 F.Cu (10.6, 27.2): lens [7.5, 1.2]
- A RADIO_RXEN F.Cu (20.6, 25.4): lens [1.65, 16.05]
- B 3V3 F.Cu (36.45, 51.75): lens [0.693, 0.03]
- B 3V3 F.Cu (36.5, 51.35): lens [0.3, 1.2]
- B GND F.Cu (37.275, 56): lens [0.615, 0.425]
- B RAW_PROTECTED B.Cu (14.5, 27): lens [1.131, 0.707]
- C 3V3 F.Cu (10.5, 78.0902): lens [3.677, 2.191]
- C 3V3 F.Cu (36.035, 82.42): lens [3.677, 0.014]
- C 3V3 B.Cu (42.95, 55.85): lens [1.3, 1.35]
- C 3V3 B.Cu (43.235, 77.92): lens [0.8, 2.1]
- C ARM1_SENSE In2.Cu (16.18, 78): lens [11.3, 7.2]
- C GND F.Cu (37.25, 65.05): lens [0.035, 1.061]
- C GND B.Cu (40.9, 85.85): lens [1.2, 0.15]
- C GND B.Cu (8.2755, 53.0617): lens [0.849, 0.212]
- C PYRO1_BUS F.Cu (16.17, 95.6): lens [0.24, 0.47]
- C PYRO1_CONT F.Cu (38.52, 72.1217): lens [0.398, 3.8]
- C PYRO1_CONT F.Cu (41.72, 79.4217): lens [0.877, 0.707]
- C RAW_PROTECTED F.Cu (37.95, 49.7): lens [0.141, 2.546]
- C USB_LIMITED B.Cu (24.1, 61.6): lens [1.556, 0.032]

### Collinear overlapping segments (49)

- C 3V3 B.Cu (26.1, 33): to (24.2, 34.9) vs [26.1, 33.0, 24.9, 34.2], overlap 1.6971 mm
- C 3V3 B.Cu (27.7, 34.6): to (26.1, 33) vs [26.1, 33.0, 26.4, 33.3], overlap 0.4243 mm
- C 3V3 F.Cu (27.89, 62.75): to (27.85, 62.75) vs [27.88, 62.75, 27.85, 62.75], overlap 0.03 mm
- C 3V3 F.Cu (27.9, 62.75): to (27.85, 62.75) vs [27.89, 62.75, 27.85, 62.75], overlap 0.04 mm
- C 3V3 F.Cu (27.9, 62.75): to (27.85, 62.75) vs [27.88, 62.75, 27.85, 62.75], overlap 0.03 mm
- C 3V3 B.Cu (32.3, 46.025): to (29.9, 43.625) vs [32.3, 46.025, 31.5, 45.225], overlap 1.1314 mm
- C 3V3 F.Cu (32.625, 56): to (31.125, 54.5) vs [31.125, 54.5, 31.15, 54.525], overlap 0.0354 mm
- C 3V3 F.Cu (33.1, 82.35): to (33.1, 80.95) vs [33.1, 82.0, 33.1, 82.0389], overlap 0.0389 mm
- C 3V3 F.Cu (34.07, 36.7): to (34.67, 36.1) vs [34.67, 36.1, 34.6647, 36.1053], overlap 0.0075 mm
- C 3V3A B.Cu (29.4, 50): to (29.4, 50.02) vs [29.4, 49.975, 29.4, 50.02], overlap 0.02 mm
- C 3V3A B.Cu (31.6, 50): to (29.4, 50) vs [31.9, 50.0, 29.4, 50.0], overlap 2.2 mm
- C 3V3A B.Cu (37.2632, 49.1393): to (40.0632, 51.9393) vs [40.0632, 51.9393, 39.2632, 51.1393], overlap 1.1314 mm
- C 3V3A B.Cu (37.88, 76.7): to (37.91, 76.73) vs [38.68, 77.5, 37.88, 76.7], overlap 0.0424 mm
- C ARM1_SENSE B.Cu (25.28, 47.3): to (24.38, 46.4) vs [24.38, 46.4, 24.4, 46.42], overlap 0.0283 mm
- C BAT_IN F.Cu (9.8, 40.85): to (9.3, 40.85) vs [11.2, 40.85, 9.3, 40.85], overlap 0.5 mm
- C CAM_5V B.Cu (33.5, 106.425): to (33.5, 107.525) vs [33.5, 107.525, 33.5, 107.5], overlap 0.025 mm
- C CAM_5V B.Cu (40.3, 105.45): to (40.3, 108.9) vs [40.3, 105.5, 40.3, 105.45], overlap 0.05 mm
- C CAM_5V B.Cu (40.3, 105.5): to (39.6, 104.8) vs [40.3, 105.5, 39.5, 104.7], overlap 0.9899 mm
- C CAM_5V B.Cu (40.3, 105.525): to (40.3, 105.5) vs [40.3, 105.45, 40.3, 108.9], overlap 0.025 mm
- C CAM_INPUT_LIMITED B.Cu (40.7, 93.45): to (40.7, 94.45) vs [40.7, 94.45, 40.7, 94.4], overlap 0.05 mm
- C GND B.Cu (20.8, 34): to (19.6, 35.2) vs [20.8, 34.0, 20.6, 34.2], overlap 0.2828 mm
- C GND B.Cu (40.1, 45.4): to (39.1533, 45.4) vs [40.1, 45.4, 39.15, 45.4], overlap 0.9467 mm
- C PYRO1_CONT_MCU B.Cu (31.8, 52.9): to (32.2, 52.9) vs [32.2, 52.9, 32.17, 52.9], overlap 0.03 mm
- C QSPI_IO0 F.Cu (21.1, 32.1): to (21.07, 32.1) vs [20.4, 32.1, 21.1, 32.1], overlap 0.03 mm
- C RAW_PROTECTED F.Cu (11.2, 40.35): to (13.1, 40.35) vs [12.6, 40.35, 13.1, 40.35], overlap 0.5 mm
- C RAW_PROTECTED B.Cu (15.65, 32.4): to (15.7, 32.4) vs [15.68, 32.4, 15.7, 32.4], overlap 0.02 mm
- C RAW_PROTECTED B.Cu (15.7, 35.75): to (15.7, 32.35) vs [15.7, 39.025, 15.7, 32.4], overlap 3.35 mm
- C RAW_PROTECTED B.Cu (15.7, 35.75): to (15.7, 32.35) vs [15.7, 32.35, 15.7, 32.4], overlap 0.05 mm
- C RAW_PROTECTED B.Cu (27.4, 27.85): to (28.525, 27.85) vs [28.5, 27.85, 28.525, 27.85], overlap 0.025 mm
- C RAW_PROTECTED B.Cu (27.4, 27.85): to (28.525, 27.85) vs [27.7, 27.85, 28.5, 27.85], overlap 0.8 mm
- C RAW_PROTECTED B.Cu (38.45, 85.7): to (38.95, 85.7) vs [38.925, 85.7, 38.95, 85.7], overlap 0.025 mm
- C RAW_PROTECTED B.Cu (38.5, 83.475): to (38.5, 83.5) vs [38.5, 84.175, 38.5, 83.475], overlap 0.025 mm
- C RAW_PROTECTED B.Cu (39.5, 80.975): to (39.5, 81) vs [39.5, 82.475, 39.5, 80.975], overlap 0.025 mm
- C USB_LIMITED B.Cu (16.3, 81.55): to (16.8, 81.55) vs [16.325, 81.55, 16.3, 81.55], overlap 0.025 mm
- C USB_LIMITED B.Cu (28.7, 57.05): to (28.7, 46.55) vs [28.7, 57.0, 28.7, 46.5], overlap 10.45 mm
- C USB_LIMITED B.Cu (29.1, 40.55): to (29.1, 46.15) vs [29.1, 46.15, 29.1, 40.05], overlap 5.6 mm
- C USB_LIMITED B.Cu (29.9, 40.8): to (29.9, 36.2) vs [29.9, 39.25, 29.9, 36.25], overlap 3.0 mm
- C USB_LIMITED B.Cu (30.5, 27.9): to (29.9, 27.9) vs [30.525, 27.9, 29.825, 27.9], overlap 0.6 mm
- C USB_LIMITED B.Cu (30.8, 28.15): to (30.5, 27.85) vs [30.4, 27.75, 30.8, 28.15], overlap 0.4243 mm
- C USB_LIMITED B.Cu (30.8, 30.55): to (30.8, 28.15) vs [30.8, 30.5, 30.8, 28.2], overlap 2.3 mm
- C USB_LIMITED B.Cu (31.6, 34.5): to (31.6, 31.3) vs [31.6, 34.55, 31.6, 31.35], overlap 3.15 mm
- C VBUS In2.Cu (11, 76.32): to (11, 76.35) vs [11.0, 76.33, 11.0, 76.35], overlap 0.02 mm
- C VBUS In2.Cu (11, 76.38): to (11, 76.35) vs [11.0, 78.95, 11.0, 76.35], overlap 0.03 mm
- C VBUS In2.Cu (12.6, 80.55): to (12, 79.95) vs [12.6, 80.55, 11.0, 78.95], overlap 0.8485 mm
- C VLOGIC B.Cu (18.2, 29.4): to (18, 29.6) vs [18.1, 29.5, 18.12, 29.48], overlap 0.0283 mm
- C VLOGIC F.Cu (27.57, 27.2): to (27.57, 28.6) vs [27.57, 27.2, 27.57, 28.9], overlap 1.4 mm
- C VLOGIC B.Cu (27.805, 28.55): to (28.505, 28.55) vs [28.525, 28.55, 27.825, 28.55], overlap 0.68 mm
- C VLOGIC B.Cu (28.525, 28.55): to (29.925, 28.55) vs [29.925, 28.55, 29.875, 28.55], overlap 0.05 mm
- C VLOGIC B.Cu (28.525, 28.55): to (27.825, 28.55) vs [28.505, 28.55, 28.525, 28.55], overlap 0.02 mm

### Side-by-side overlapping copper (56)

- C 3V3 B.Cu (26.1, 34.6): to (26.1, 33) vs [26.4, 33.3, 26.4, 36.6], overlap 1.3 mm, offset 0.3
- C 3V3 F.Cu (27.8, 68.87): to (27.8, 62.77) vs [27.9, 67.75, 27.9, 62.75], overlap 4.98 mm, offset 0.1
- C 3V3A B.Cu (29.4, 50.02): to (31.1, 50.02) vs [31.6, 49.975, 29.4, 49.975], overlap 1.7 mm, offset 0.045
- C 3V3A B.Cu (31.6, 50): to (29.4, 50) vs [29.4, 50.02, 31.1, 50.02], overlap 1.7 mm, offset 0.02
- C 3V3A B.Cu (31.6, 50): to (29.4, 50) vs [31.6, 49.975, 29.4, 49.975], overlap 2.2 mm, offset 0.025
- C 3V3A B.Cu (31.9, 50): to (29.4, 50) vs [29.4, 50.02, 31.1, 50.02], overlap 1.7 mm, offset 0.02
- C 3V3A B.Cu (31.9, 50): to (29.4, 50) vs [31.6, 49.975, 29.4, 49.975], overlap 2.2 mm, offset 0.025
- C 3V3A B.Cu (32.4, 49.5): to (31.9, 50) vs [33.5, 48.1, 31.6, 50.0], overlap 0.7071 mm, offset 0.2121
- C 3V3A B.Cu (33.2, 48.375): to (31.6, 49.975) vs [32.4, 49.5, 31.9, 50.0], overlap 0.7071 mm, offset 0.2298
- C 3V3A B.Cu (33.2, 48.375): to (31.6, 49.975) vs [33.5, 48.1, 31.6, 50.0], overlap 2.2627 mm, offset 0.0177
- C 3V3A B.Cu (37.2632, 49.1393): to (40.0632, 51.9393) vs [40.1, 51.9, 37.7, 49.5], overlap 3.3941 mm, offset 0.0538
- C 3V3A B.Cu (38.68, 77.5): to (37.88, 76.7) vs [38.68, 77.8, 36.68, 75.8], overlap 1.1314 mm, offset 0.2121
- C 3V3A B.Cu (39.4, 48.1): to (33.5, 48.1) vs [37.6632, 48.1393, 38.2632, 48.1393], overlap 0.6 mm, offset 0.0393
- C 3V3A B.Cu (40.0632, 51.9393): to (40.0632, 54.6393) vs [40.1, 54.6, 40.1, 51.9], overlap 2.6607 mm, offset 0.0368
- C 3V3A B.Cu (40.0632, 51.9393): to (39.2632, 51.1393) vs [40.1, 51.9, 37.7, 49.5], overlap 1.1296 mm, offset 0.0538
- C BAT_IN B.Cu (6, 54.475): to (8.2, 54.475) vs [4.2, 54.8, 9.7, 54.8], overlap 2.2 mm, offset 0.325
- C BAT_IN B.Cu (8.2, 54.475): to (9.3, 53.375) vs [8.3, 54.525, 8.8, 54.025], overlap 0.7071 mm, offset 0.1061
- C CAM_5V B.Cu (38.7, 103.925): to (40.3, 105.525) vs [40.3, 105.5, 39.6, 104.8], overlap 0.9899 mm, offset 0.0177
- C CAM_5V B.Cu (38.7, 103.925): to (40.3, 105.525) vs [40.3, 105.5, 39.5, 104.7], overlap 1.1314 mm, offset 0.0177
- C GND B.Cu (39.15, 45.4): to (38.95, 45.6) vs [38.3933, 46.16, 39.1533, 45.4], overlap 0.2828 mm, offset 0.0023
- C PYRO1_GATE F.Cu (23.4, 92.1): to (22.5483, 92.1) vs [26.0, 91.9, 21.6, 91.9], overlap 0.8517 mm, offset 0.2
- C PYRO1_GATE F.Cu (26, 91.775): to (25.3767, 91.775) vs [26.0, 91.9, 21.6, 91.9], overlap 0.6233 mm, offset 0.125
- C PYRO1_GATE F.Cu (26, 91.9): to (21.6, 91.9) vs [24.7, 91.93, 25.2217, 91.93], overlap 0.5217 mm, offset 0.03
- C RAW_PROTECTED B.Cu (15.65, 35.6): to (15.65, 32.4) vs [15.7, 39.025, 15.7, 32.4], overlap 3.2 mm, offset 0.05
- C RAW_PROTECTED B.Cu (15.7, 35.75): to (15.7, 32.35) vs [15.65, 35.6, 15.65, 32.4], overlap 3.2 mm, offset 0.05
- C RAW_PROTECTED B.Cu (27.1, 27.25): to (27.7, 27.85) vs [25.7, 26.2, 27.375, 27.875], overlap 0.6364 mm, offset 0.2475
- C USB_LIMITED B.Cu (28.7, 46.55): to (29.1, 46.15) vs [28.725, 46.5, 29.125, 46.1], overlap 0.5127 mm, offset 0.0177
- C USB_LIMITED B.Cu (28.7, 46.55): to (29.1, 46.15) vs [28.7, 46.5, 28.9, 46.3], overlap 0.2828 mm, offset 0.0354
- C USB_LIMITED B.Cu (28.725, 46.5): to (29.125, 46.1) vs [28.7, 46.5, 28.9, 46.3], overlap 0.2652 mm, offset 0.0177
- C USB_LIMITED B.Cu (28.725, 57): to (28.725, 46.5) vs [28.7, 57.05, 28.7, 46.55], overlap 10.45 mm, offset 0.025
- C USB_LIMITED B.Cu (28.725, 57): to (28.725, 46.5) vs [28.7, 57.0, 28.7, 46.5], overlap 10.5 mm, offset 0.025
- C USB_LIMITED B.Cu (29.1, 40.55): to (29.1, 46.15) vs [29.125, 46.1, 29.125, 40.0], overlap 5.55 mm, offset 0.025
- C USB_LIMITED B.Cu (29.1, 40.55): to (29.1, 46.15) vs [28.9, 46.3, 28.9, 41.8], overlap 4.35 mm, offset 0.2
- C USB_LIMITED B.Cu (29.1, 46.15): to (29.1, 40.05) vs [29.125, 46.1, 29.125, 40.0], overlap 6.05 mm, offset 0.025
- C USB_LIMITED B.Cu (29.1, 46.15): to (29.1, 40.05) vs [28.9, 46.3, 28.9, 41.8], overlap 4.35 mm, offset 0.2
- C USB_LIMITED B.Cu (29.125, 40): to (29.925, 39.2) vs [29.1, 40.05, 29.9, 39.25], overlap 1.0783 mm, offset 0.0177
- C USB_LIMITED B.Cu (29.125, 46.1): to (29.125, 40) vs [28.9, 46.3, 28.9, 41.8], overlap 4.3 mm, offset 0.225
- C USB_LIMITED B.Cu (29.9, 36.2): to (31.6, 34.5) vs [29.9, 36.25, 31.6, 34.55], overlap 2.3688 mm, offset 0.0354
- C USB_LIMITED B.Cu (29.925, 36.2): to (31.525, 34.6) vs [29.9, 36.2, 31.6, 34.5], overlap 2.2627 mm, offset 0.0177
- C USB_LIMITED B.Cu (29.925, 36.2): to (31.525, 34.6) vs [29.9, 36.25, 31.6, 34.55], overlap 2.2627 mm, offset 0.0177
- C USB_LIMITED B.Cu (29.925, 39.2): to (29.925, 36.2) vs [29.9, 40.8, 29.9, 36.2], overlap 3.0 mm, offset 0.025
- C USB_LIMITED B.Cu (29.925, 39.2): to (29.925, 36.2) vs [29.9, 39.25, 29.9, 36.25], overlap 2.95 mm, offset 0.025
- C USB_LIMITED B.Cu (30.5, 27.85): to (29.9, 27.85) vs [30.5, 27.9, 29.9, 27.9], overlap 0.6 mm, offset 0.05
- C USB_LIMITED B.Cu (30.5, 27.85): to (29.9, 27.85) vs [30.525, 27.9, 29.825, 27.9], overlap 0.6 mm, offset 0.05
- C USB_LIMITED B.Cu (30.8, 28.15): to (30.5, 27.85) vs [30.8, 28.2, 30.5, 27.9], overlap 0.3889 mm, offset 0.0354
- C USB_LIMITED B.Cu (30.8, 28.15): to (30.5, 27.85) vs [31.525, 28.9, 30.525, 27.9], overlap 0.3712 mm, offset 0.0177
- C USB_LIMITED B.Cu (30.8, 28.2): to (30.5, 27.9) vs [31.525, 28.9, 30.525, 27.9], overlap 0.4066 mm, offset 0.0177
- C USB_LIMITED B.Cu (30.8, 28.2): to (30.5, 27.9) vs [30.4, 27.75, 30.8, 28.15], overlap 0.3889 mm, offset 0.0354
- C USB_LIMITED B.Cu (31.525, 28.9): to (30.525, 27.9) vs [30.4, 27.75, 30.8, 28.15], overlap 0.3712 mm, offset 0.0177
- C USB_LIMITED B.Cu (31.525, 34.6): to (31.525, 28.9) vs [31.6, 34.55, 31.6, 31.35], overlap 3.2 mm, offset 0.075
- C USB_LIMITED B.Cu (31.6, 31.35): to (30.8, 30.55) vs [31.6, 31.3, 30.8, 30.5], overlap 1.096 mm, offset 0.0354
- C USB_LIMITED B.Cu (31.6, 34.5): to (31.6, 31.3) vs [31.525, 34.6, 31.525, 28.9], overlap 3.2 mm, offset 0.075
- C VBUS In2.Cu (10.98, 76.7): to (10.98, 76.4) vs [11.0, 78.95, 11.0, 76.35], overlap 0.3 mm, offset 0.02
- C VLOGIC B.Cu (27.57, 28.9): to (27.87, 28.6) vs [27.825, 28.55, 27.125, 29.25], overlap 0.4243 mm, offset 0.0672
- C VLOGIC B.Cu (27.57, 28.9): to (27.87, 28.6) vs [26.905, 29.45, 27.805, 28.55], overlap 0.4137 mm, offset 0.0813
- C VLOGIC B.Cu (27.825, 28.55): to (27.125, 29.25) vs [26.905, 29.45, 27.805, 28.55], overlap 0.9758 mm, offset 0.0141

### Same-net crossings without a node (35)

- C 3V3 F.Cu (27.9, 62.83)
- C 3V3 B.Cu (30.17, 71.24)
- C 3V3 F.Cu (32.03, 82)
- C 3V3 F.Cu (33.1, 81.73)
- C 3V3 F.Cu (36.429, 51.721)
- C 3V3A B.Cu (32.5, 49.5)
- C 3V3A B.Cu (34.62, 71.175)
- C 3V3A B.Cu (37.6239, 49.5)
- C 3V3A B.Cu (37.91, 77.03)
- C CAM_5V B.Cu (39.575, 104.8)
- C CAM_5V F.Cu (40.75, 40.1)
- C GND F.Cu (24.32, 108.05)
- C GND B.Cu (37.38, 70.725)
- C GND B.Cu (37.88, 70.5)
- C IMU_CS F.Cu (37.2, 79.6)
- C PYRO1_GATE F.Cu (25.2517, 91.9)
- C PYRO1_OUT F.Cu (28.7, 91.88)
- C RAW_PROTECTED B.Cu (15.7, 35.65)
- C RAW_PROTECTED B.Cu (15.7, 35.65)
- C RAW_PROTECTED B.Cu (26.75, 27.25)
- C USB_LIMITED B.Cu (28.725, 46.525)
- C USB_LIMITED B.Cu (29.1, 41.6)
- C USB_LIMITED B.Cu (29.1, 41.6)
- C USB_LIMITED B.Cu (29.1, 46.125)
- C USB_LIMITED B.Cu (29.1, 46.125)
- C USB_LIMITED B.Cu (29.125, 40.025)
- C USB_LIMITED B.Cu (29.125, 41.575)
- C USB_LIMITED B.Cu (29.9, 39.225)
- C USB_LIMITED B.Cu (29.9, 39.225)
- C USB_LIMITED B.Cu (29.925, 36.225)
- C USB_LIMITED B.Cu (30.8, 28.175)
- C USB_LIMITED B.Cu (31.525, 31.225)
- C USB_LIMITED B.Cu (31.525, 31.275)
- C USB_LIMITED B.Cu (31.525, 34.575)
- C VLOGIC B.Cu (27.105, 29.25)

### Overlap-only joints (5)

- C ACT_FET_S B.Cu (6.45, 94.7): to track 5.100,95.000-6.450,95.000
- C GND F.Cu (11.7, 38.575): to via (12.000,38.875)
- C GND B.Cu (17.3498, 59.9256): to track 17.400,60.800-17.400,60.078
- C GND F.Cu (21.9265, 87.6298): to R127.2
- C RAW_ACT F.Cu (5.3, 82.2): to track 7.000,82.170-5.300,82.170

### Track ends inside a via, off centre (8)

- A BAT_IN B.Cu (9.3, 53.38): 0.005 mm off
- B 3V3 F.Cu (27.9, 62.74): 0.051 mm off
- C 3V3 F.Cu (27.9, 62.73): 0.0539 mm off
- C 3V3 F.Cu (34.65, 36.1): 0.0141 mm off
- C GND B.Cu (17.4202, 55.9992): 0.0445 mm off
- C GND F.Cu (24.25, 108.05): 0.3 mm off
- C RAW_PROTECTED B.Cu (15.65, 32.37): 0.0583 mm off
- C RAW_PROTECTED B.Cu (37.95, 54.7154): 0.1012 mm off

### Track ends held only by the pour (stubs) (32)

- B 3V3 In2.Cu (17.58, 34): segment 2.5 mm
- B GND F.Cu (25.5, 27.5): segment 1.273 mm
- B GND F.Cu (35.55, 61.35): segment 0.31 mm
- B GND F.Cu (36.5, 53.65): segment 1.15 mm
- B GND F.Cu (36.5, 63.65): segment 0.65 mm
- B GND F.Cu (37.275, 66): segment 0.925 mm
- C 3V3 In2.Cu (15.2, 62.3): segment 1.838 mm
- C 3V3 In2.Cu (16.25, 31.1): segment 4.7 mm
- C 3V3 In2.Cu (16.5, 61): segment 1.838 mm
- C 3V3 In2.Cu (18.7, 51.9): segment 0.424 mm
- C 3V3 In2.Cu (19.6, 51.6): segment 0.6 mm
- C 3V3 In2.Cu (26.4, 38.47): segment 1.87 mm
- C 3V3 In2.Cu (28.9421, 56.6579): segment 2.389 mm
- C ACT_FET_S B.Cu (5.1, 95): segment 1.35 mm
- C GND F.Cu (11.75, 37.025): segment 1.556 mm
- C GND B.Cu (12.43, 78.6): segment 2.0 mm
- C GND B.Cu (13.7, 78.8): segment 0.5 mm
- C GND B.Cu (21.9783, 98.2): segment 0.867 mm
- C GND B.Cu (28.12, 108.8618): segment 2.305 mm
- C GND B.Cu (30.317, 25.15): segment 1.267 mm
- C GND B.Cu (30.7985, 27.3798): segment 1.825 mm
- C GND B.Cu (31.1812, 100.4232): segment 1.257 mm
- C GND B.Cu (33.0298, 27.6798): segment 0.616 mm
- C GND B.Cu (35.1, 27.6798): segment 0.72 mm
- C GND F.Cu (35.83, 59.6): segment 0.5 mm
- C GND F.Cu (37.7633, 28.7413): segment 0.593 mm
- C GND F.Cu (37.7633, 31.5): segment 0.937 mm
- C GND B.Cu (38.18, 70.8): segment 0.601 mm
- C GND B.Cu (38.3933, 46.16): segment 1.075 mm
- C GND B.Cu (43.775, 48.5621): segment 0.962 mm
- C GND B.Cu (44.65, 54.95): segment 1.1 mm
- C GND B.Cu (8.4255, 53.2117): segment 0.212 mm

### Track ends > 0.1 mm off the centre of a small pad (154)

- A 3V3 F.Cu (35.1, 26.6): R161.1, 0.2119 mm
- A 3V3_GNSS F.Cu (12.61, 20.3): U30.7, 0.6 mm
- A 3V3_GNSS F.Cu (12.61, 20.3): U30.7, 0.6 mm
- A 3V3_GNSS F.Cu (12.61, 20.3): U30.7, 0.6 mm
- A 3V3_GNSS F.Cu (12.61, 21.75): C301.1, 0.1838 mm
- A 3V3_GNSS F.Cu (12.61, 21.75): C301.1, 0.1838 mm
- A 3V3_GNSS F.Cu (13.71, 20.3): U30.8, 0.6 mm
- A 3V3_GNSS F.Cu (13.71, 20.3): U30.8, 0.6 mm
- A 3V3_RADIO F.Cu (36.35, 19.6): C310.1, 0.43 mm
- A 3V3_RADIO F.Cu (36.35, 19.6): C310.1, 0.43 mm
- A 3V3_RADIO F.Cu (36.58, 19.4): C310.1, 0.2828 mm
- A 3V3_RADIO F.Cu (36.58, 19.4): C310.1, 0.2828 mm
- A BAT_IN B.Cu (10.62, 52.6): C80.1, 0.5 mm
- A BAT_IN B.Cu (10.62, 52.6): C80.1, 0.5 mm
- A GNSS_ANT_GATE B.Cu (7.07, 14.39): R301.2, 0.14 mm
- A GNSS_ANT_GATE B.Cu (7.07, 14.39): R301.2, 0.14 mm
- A GNSS_ANT_GATE B.Cu (8.25, 15.45): R302.1, 0.12 mm
- A GNSS_ANT_GATE B.Cu (8.25, 15.45): R302.1, 0.12 mm
- A GNSS_ANT_SRC B.Cu (8.25, 12): R300.2, 0.175 mm
- A GNSS_ANT_SRC B.Cu (8.25, 12): R300.2, 0.175 mm
- A GNSS_ANT_SRC B.Cu (8.25, 12): R300.2, 0.175 mm
- A GNSS_ANT_SRC B.Cu (9.525, 11.825): Q30.2, 0.3182 mm
- A GNSS_ANT_SRC B.Cu (9.525, 11.825): Q30.2, 0.3182 mm
- A GNSS_SAFEBOOT_N F.Cu (2.6, 10.2): TP30.1, 0.8485 mm
- A GNSS_SAFEBOOT_N F.Cu (2.6, 10.2): TP30.1, 0.8485 mm
- A GNSS_VCC_RF B.Cu (8.535, 10.175): R300.1, 0.285 mm
- A GNSS_VCC_RF B.Cu (8.535, 10.175): R300.1, 0.285 mm
- B GNSS_RESET_N F.Cu (14.8, 18.85): U30.9, 0.8501 mm
- B GNSS_RESET_N F.Cu (14.8, 19.8): U30.9, 0.1005 mm
- C 3V3 F.Cu (13.925, 43.4): R89.1, 0.4243 mm
- C 3V3 F.Cu (13.925, 43.4): R89.1, 0.4243 mm
- C 3V3 B.Cu (14.6, 59.78): C17.1, 0.1414 mm
- C 3V3 B.Cu (14.6, 59.78): C17.1, 0.1414 mm
- C 3V3 B.Cu (16.85, 31.6): U2.1, 0.2828 mm
- C 3V3 B.Cu (16.85, 31.6): U2.1, 0.2828 mm
- C 3V3 F.Cu (19.38, 35.9): C29.1, 0.2546 mm
- C 3V3 F.Cu (19.38, 35.9): C29.1, 0.2546 mm
- C 3V3 B.Cu (20.8, 97.525): R76.1, 0.3 mm
- C 3V3 B.Cu (20.8, 97.525): R76.1, 0.3 mm
- C 3V3 F.Cu (27.9014, 39.7703): R10.2, 0.1002 mm
- C 3V3 F.Cu (27.9014, 39.7703): R10.2, 0.1002 mm
- C 3V3 F.Cu (27.9014, 39.7714): R10.2, 0.101 mm
- C 3V3 F.Cu (27.93, 39.7417): R10.2, 0.1083 mm
- C 3V3 F.Cu (27.93, 39.7417): R10.2, 0.1083 mm
- C 3V3 B.Cu (29.6, 57.18): C13.1, 0.2828 mm
- C 3V3 B.Cu (29.6, 57.18): C13.1, 0.2828 mm
- C 3V3 B.Cu (32, 83.15): D121.5, 0.4 mm
- C 3V3 B.Cu (32, 83.15): D121.5, 0.4 mm
- C 3V3 B.Cu (32, 83.95): D121.5, 0.4 mm
- C 3V3 B.Cu (32.1, 54.5): C23.1, 0.2828 mm
- C 3V3 B.Cu (32.1, 54.5): C23.1, 0.2828 mm
- C 3V3 F.Cu (32.3, 81.73): D120.3, 0.4036 mm
- C 3V3 F.Cu (32.3, 81.73): D120.3, 0.4036 mm
- C 3V3 F.Cu (43.85, 77.92): J2.1, 0.215 mm
- C 3V3A B.Cu (32.4, 49.5): C22.1, 0.2236 mm
- C 3V3A B.Cu (32.4, 49.5): C22.1, 0.2236 mm
- C 3V3A B.Cu (32.4, 49.5): C22.1, 0.2236 mm
- C 3V3A B.Cu (32.6, 49.6): C22.1, 0.4243 mm
- C 3V3A B.Cu (32.6, 49.6): C22.1, 0.4243 mm
- C 3V3A B.Cu (34.62, 71.7): U5.1, 0.2828 mm
- C 3V3A B.Cu (34.62, 71.7): U5.1, 0.2828 mm
- C BAT_IN B.Cu (4.2, 54.8): TP80.1, 0.5657 mm
- C BAT_IN B.Cu (4.2, 54.8): TP80.1, 0.5657 mm
- C BAT_IN B.Cu (8.2, 54.475): C96.1, 0.1118 mm
- C BAT_IN B.Cu (8.2, 54.475): C96.1, 0.1118 mm
- C BAT_IN B.Cu (8.8, 54.025): C96.1, 0.7071 mm
- C BAT_IN B.Cu (8.8, 54.025): C96.1, 0.7071 mm
- C BAT_IN F.Cu (9.35, 39.47): C88.1, 0.2828 mm
- C BAT_IN F.Cu (9.35, 39.47): C88.1, 0.2828 mm
- C CAM_5V F.Cu (40.175, 40.1): J9.1, 0.5755 mm
- C CAM_5V F.Cu (40.175, 40.1): J9.1, 0.5755 mm
- C CAM_SW B.Cu (42.5, 94.4): U8.5, 0.4 mm
- C CAM_SW B.Cu (42.5, 94.4): U8.5, 0.4 mm
- C GND B.Cu (14.1, 80.6): U10.2, 0.4 mm
- C GND B.Cu (14.1, 80.6): U10.2, 0.4 mm
- C GND B.Cu (14.6, 60.82): C17.2, 0.1414 mm
- C GND B.Cu (14.6, 60.82): C17.2, 0.1414 mm
- C GND B.Cu (14.6, 60.92): C17.2, 0.2236 mm
- C GND B.Cu (14.6, 60.92): C17.2, 0.2236 mm
- C GND F.Cu (18.9274, 90.7274): C129.2, 0.3855 mm
- C GND F.Cu (18.9274, 90.7274): C129.2, 0.3855 mm
- C GND B.Cu (20.6, 34.2): C7.2, 0.2828 mm
- C GND B.Cu (20.6, 34.2): C7.2, 0.2828 mm
- C GND B.Cu (22.8, 52.66): C26.2, 0.2828 mm
- C GND B.Cu (22.8, 52.66): C26.2, 0.2828 mm
- C GND B.Cu (23.97, 63.8): R5.2, 0.2 mm
- C GND B.Cu (23.97, 63.8): R5.2, 0.2 mm
- C GND B.Cu (27.54, 56.9): C25.2, 0.2 mm
- C GND B.Cu (27.54, 56.9): C25.2, 0.2 mm
- C GND B.Cu (29.5, 47): C24.2, 0.1281 mm
- C GND B.Cu (32, 80.85): D121.2, 0.4 mm
- C GND B.Cu (32, 80.85): D121.2, 0.4 mm
- C GND B.Cu (32.0887, 28.67): R105.2, 0.1113 mm
- C GND B.Cu (32.0887, 28.67): R105.2, 0.1113 mm
- C GND B.Cu (35.8, 84.025): C71.2, 0.1414 mm
- C GND B.Cu (35.8, 84.025): C71.2, 0.1414 mm
- C GND B.Cu (38.9, 86.65): U7.9, 0.7 mm
- C GND B.Cu (38.9, 86.65): U7.9, 0.7 mm
- C GND F.Cu (43.85, 75.38): J2.5, 0.215 mm
- C GND F.Cu (44.525, 92.175): R72.2, 0.175 mm
- C GND F.Cu (44.525, 92.175): R72.2, 0.175 mm
- C GND B.Cu (6.0062, 82.8312): R85.2, 0.2387 mm
- C GND B.Cu (6.0062, 82.8312): R85.2, 0.2387 mm
- C GND F.Cu (6.425, 41.35): R81.2, 0.3536 mm
- C GND F.Cu (6.425, 41.35): R81.2, 0.3536 mm
- C GND F.Cu (6.75, 39.9): C87.2, 0.2828 mm
- C GND F.Cu (6.75, 39.9): C87.2, 0.2828 mm
- C GND B.Cu (7.675, 52.4612): C80.2, 0.3612 mm
- C GND B.Cu (7.675, 52.4612): C80.2, 0.3612 mm
- C GND B.Cu (9.3, 108.5): Q122.2, 0.1414 mm
- C GND B.Cu (9.3, 108.5): Q122.2, 0.1414 mm
- C HSE_OUT B.Cu (23.9, 52.9): Y1.3, 0.6 mm
- C HSE_OUT B.Cu (23.9, 52.9): Y1.3, 0.6 mm
- C IMU_CS B.Cu (36.7, 80.97): R11.1, 0.2828 mm
- C PYRO1_CONT_MID F.Cu (28.85, 87.9): R129.1, 0.12 mm
- C PYRO1_CONT_MID F.Cu (28.85, 87.9): R129.1, 0.12 mm
- C PYRO1_CONT_MID F.Cu (28.95, 87.8): R129.1, 0.2417 mm
- C PYRO1_CONT_MID F.Cu (28.95, 87.8): R129.1, 0.2417 mm
- C PYRO1_GATE F.Cu (21.6, 91.9): R126.2, 0.5 mm
- C PYRO1_GATE F.Cu (22.2483, 92.4): R126.2, 0.6483 mm
- C PYRO1_GATE F.Cu (22.2483, 92.4): R126.2, 0.6483 mm
- C PYRO1_GATE F.Cu (26, 91.9): Q124.4, 0.125 mm
- C QSPI_NCS F.Cu (26.75, 39.7): R10.1, 0.22 mm
- C RAW_PROTECTED B.Cu (35.75, 85.77): C71.1, 0.1074 mm
- C RAW_PROTECTED B.Cu (35.75, 85.77): C71.1, 0.1074 mm
- C RAW_PROTECTED B.Cu (38.5, 83.475): TP70.1, 0.275 mm
- C RAW_PROTECTED B.Cu (38.5, 83.475): TP70.1, 0.275 mm
- C RAW_PROTECTED B.Cu (38.5, 83.475): TP70.1, 0.275 mm
- C RAW_PROTECTED B.Cu (38.5, 83.5): TP70.1, 0.3 mm
- C RAW_PROTECTED B.Cu (38.5, 83.5): TP70.1, 0.3 mm
- C RAW_PROTECTED B.Cu (40.2, 80.3): TP81.1, 0.9899 mm
- C RAW_PROTECTED B.Cu (40.2, 80.3): TP81.1, 0.9899 mm
- C SW_NODE B.Cu (17.9, 34.3): U2.5, 0.1414 mm
- C SW_NODE B.Cu (17.9, 34.3): U2.5, 0.1414 mm
- C USB_LIMITED B.Cu (16.8, 81.55): U10.6, 0.5 mm
- C USB_LIMITED B.Cu (16.8, 81.55): U10.6, 0.5 mm
- C USB_LIMITED B.Cu (30.4, 27.75): U11.7, 0.5344 mm
- C USB_LIMITED B.Cu (30.4, 27.75): U11.7, 0.5344 mm
- C USB_LIMITED B.Cu (33.1, 26.15): C98.1, 0.3 mm
- C USB_LIMITED B.Cu (33.1, 26.15): C98.1, 0.3 mm
- C VBUS F.Cu (13.225, 82.05): C83.1, 0.1414 mm
- C VBUS F.Cu (13.225, 82.05): C83.1, 0.1414 mm
- C VBUS B.Cu (13.3, 81.55): U10.1, 0.4 mm
- C VLOGIC B.Cu (18, 29.6): C6.1, 0.2828 mm
- C VLOGIC B.Cu (18, 29.6): C6.1, 0.2828 mm
- C VLOGIC B.Cu (18, 32.35): U2.2, 0.55 mm
- C VLOGIC B.Cu (18, 32.35): U2.2, 0.55 mm
- C VLOGIC B.Cu (18.1, 29.5): C6.1, 0.1414 mm
- C VLOGIC B.Cu (18.1, 29.5): C6.1, 0.1414 mm
- C VLOGIC B.Cu (18.12, 29.48): C6.1, 0.1131 mm
- C VLOGIC B.Cu (20.6, 31.8): C7.1, 0.2828 mm
- C VLOGIC B.Cu (20.6, 31.8): C7.1, 0.2828 mm
- C VLOGIC B.Cu (20.825, 31.85): C7.1, 0.1521 mm
- C VLOGIC B.Cu (20.825, 31.85): C7.1, 0.1521 mm

### Segments wholly inside their pad (>= 0.2 mm) (65)

- A 3V3_GNSS F.Cu (12.61, 19.7): U30.7, 0.6 mm
- A 3V3_GNSS F.Cu (13.71, 20.3): U30.8, 0.6 mm
- A 3V3_RADIO F.Cu (36.35, 19.6): C310.1, 0.43 mm
- A 3V3_RADIO F.Cu (36.58, 19.4): C310.1, 0.283 mm
- A BAT_IN B.Cu (10.62, 52.1): C80.1, 0.5 mm
- A GNSS_ANT_SRC B.Cu (9.525, 11.825): Q30.2, 0.318 mm
- A GNSS_SAFEBOOT_N F.Cu (2.6, 10.2): TP30.1, 0.849 mm
- A GNSS_VCC_RF B.Cu (8.535, 10.175): R300.1, 0.285 mm
- B GNSS_RESET_N F.Cu (14.8, 19.8): U30.9, 0.95 mm
- C 3V3 F.Cu (12.53, 78.1): LS120.1, 0.424 mm
- C 3V3 F.Cu (13.625, 43.1): R89.1, 0.424 mm
- C 3V3 B.Cu (17.05, 31.8): U2.1, 0.283 mm
- C 3V3 F.Cu (19.38, 35.9): C29.1, 0.255 mm
- C 3V3 B.Cu (20.8, 97.825): R76.1, 0.3 mm
- C 3V3 B.Cu (26.1, 33): L1.2, 0.424 mm
- C 3V3 B.Cu (26.1, 34.6): L1.2, 1.6 mm
- C 3V3 B.Cu (29.4, 56.98): C13.1, 0.283 mm
- C 3V3 B.Cu (32, 83.55): D121.5, 0.4 mm
- C 3V3 B.Cu (32, 83.55): D121.5, 0.4 mm
- C 3V3 B.Cu (32.3, 54.3): C23.1, 0.283 mm
- C 3V3 F.Cu (32.3, 81.73): D120.3, 0.424 mm
- C 3V3A B.Cu (32.3, 49.3): C22.1, 0.424 mm
- C 3V3A B.Cu (34.42, 71.9): U5.1, 0.283 mm
- C BAT_DAMP F.Cu (2.4, 34.575): R166.1, 0.7 mm
- C BAT_IN B.Cu (3.8, 54.4): TP80.1, 0.566 mm
- C BAT_IN B.Cu (8.3, 54.525): C96.1, 0.707 mm
- C BAT_IN F.Cu (9.15, 39.27): C88.1, 0.283 mm
- C CAM_5V F.Cu (40.175, 40.1): J9.1, 0.6 mm
- C CAM_INPUT_LIMITED B.Cu (40.3, 90.8): C72.1, 0.566 mm
- C CAM_SW B.Cu (42.9, 94.4): U8.5, 0.4 mm
- C GND B.Cu (11.9, 29.05): D8.2, 0.8 mm
- C GND B.Cu (13.7, 80.6): U10.2, 0.4 mm
- C GND F.Cu (18.9274, 90.7274): C129.2, 0.386 mm
- C GND B.Cu (20.8, 34): C7.2, 0.283 mm
- C GND B.Cu (22.6, 52.46): C26.2, 0.283 mm
- C GND B.Cu (32, 81.25): D121.2, 0.4 mm
- C GND F.Cu (36.5, 76): C121.2, 0.849 mm
- C GND B.Cu (38.2, 86.65): U7.9, 0.7 mm
- C GND B.Cu (6.0062, 82.8312): R85.2, 0.239 mm
- C GND F.Cu (6.425, 41.35): R81.2, 0.3 mm
- C GND F.Cu (6.55, 39.7): C87.2, 0.283 mm
- C GND B.Cu (7.675, 52.4612): C80.2, 0.361 mm
- C HSE_OUT B.Cu (23.9, 52.9): Y1.3, 0.6 mm
- C IMU_CS B.Cu (36.5, 80.77): R11.1, 0.283 mm
- C PYRO1_BUS F.Cu (10, 95.86): J124.1, 0.5 mm
- C PYRO1_BUS F.Cu (19.385, 95.36): R134.2, 0.622 mm
- C PYRO1_GATE F.Cu (21.6, 92.4): R126.2, 0.648 mm
- C PYRO1_OUT F.Cu (28.4, 90.78): Q124.5, 0.98 mm
- C QSPI_CLK F.Cu (21.65, 33.35): U3.6, 0.6 mm
- C QSPI_IO0 F.Cu (20.4, 32.1): U3.5, 0.7 mm
- C QSPI_IO1 F.Cu (27.5, 34.6): U3.2, 0.6 mm
- C QSPI_IO2 F.Cu (27.5, 33.4): U3.3, 0.6 mm
- C QSPI_IO3 F.Cu (21.7, 34.6): U3.7, 0.6 mm
- C QSPI_NCS F.Cu (26.97, 39.7): R10.1, 0.22 mm
- C RAW_ACT F.Cu (29.3, 75.4): C121.1, 0.424 mm
- C RAW_PROTECTED F.Cu (13.1, 40.35): C82.1, 0.707 mm
- C RAW_PROTECTED F.Cu (13.45, 40.35): C82.1, 0.3 mm
- C RAW_PROTECTED B.Cu (39.5, 81): TP81.1, 0.99 mm
- C SW_NODE B.Cu (22.92, 34.05): L1.1, 1.0 mm
- C USB_LIMITED B.Cu (16.3, 81.55): U10.6, 0.5 mm
- C USB_LIMITED B.Cu (33.1, 26.45): C98.1, 0.3 mm
- C VBUS B.Cu (13.7, 81.55): U10.1, 0.4 mm
- C VLOGIC B.Cu (18, 32.35): U2.2, 0.5 mm
- C VLOGIC B.Cu (18.2, 29.4): C6.1, 0.283 mm
- C VLOGIC B.Cu (20.8, 32): C7.1, 0.283 mm

### Tracks passing through a same-net pad (19)

- A GNSS_RF_ANT F.Cu (12.85, 2.3): D30.1, to (12.85, 7.13)
- A GNSS_RF_ANT F.Cu (12.85, 2.3): L30.2, to (12.85, 7.13)
- A RADIO_RF_ANT F.Cu (31.54, 2.3): D31.1, to (31.54, 7.6)
- C 3V3 F.Cu (12.049, 76.5412): LS120.1, to (10.5, 78.0902)
- C 3V3A B.Cu (33.2, 48.375): C22.1, to (31.6, 49.975)
- C 3V3A B.Cu (33.5, 48.1): C22.1, to (31.6, 50)
- C 3V3A B.Cu (34.62, 71.7): U5.1, to (34.62, 70.5)
- C 3V3A B.Cu (38.68, 77.8): C31.1, to (36.68, 75.8)
- C ARM1_SENSE F.Cu (17.28, 94.15): R180.1, to (17.28, 92.4)
- C BAT_IN B.Cu (4.2, 54.8): C96.1, to (9.7, 54.8)
- C BAT_IN B.Cu (4.2, 54.8): R167.1, to (9.7, 54.8)
- C GND F.Cu (26, 91.125): Q124.2, to (26, 89.825)
- C GND B.Cu (36.93, 71.9): U5.3, to (36.93, 70.5)
- C PYRO1_GATE F.Cu (26, 91.9): R128.1, to (21.6, 91.9)
- C PYRO1_GATE F.Cu (26, 91.9): C126.1, to (21.6, 91.9)
- C PYRO1_OUT F.Cu (30.58, 90): R173.1, to (30.58, 86.1)
- C QSPI_NCS F.Cu (26.75, 40.45): R10.1, to (26.75, 37.35)
- C RAW_ACT B.Cu (8.7, 110.68): Q121.5, to (4, 105.98)
- C USB_DM F.Cu (5.7, 75.55): J3.A7, to (10.05, 75.55)

### Width changes at free nodes (55)

- A RADIO_RXEN F.Cu (20.6, 25.4): [0.15, 0.2]
- B GND F.Cu (37.275, 56): [0.2, 0.25]
- C 3V3 F.Cu (10.5, 78.0902): [0.2, 0.25]
- C 3V3 In2.Cu (17.57, 36.5): [0.2, 0.3]
- C 3V3 B.Cu (30.1, 55.32): [0.2, 0.25]
- C 3V3 F.Cu (35.03, 27.3417): [0.2, 0.25]
- C 3V3A B.Cu (34.62, 70.5): [0.25, 0.3]
- C 3V3A B.Cu (38.2632, 48.1): [0.25, 0.3]
- C 3V3A B.Cu (38.68, 77.8): [0.2, 0.3]
- C BAT_IN F.Cu (9.3, 40.85): [0.3, 0.5]
- C BAT_IN F.Cu (9.8, 40.85): [0.3, 0.5]
- C CAM_5V B.Cu (35.4939, 33.4639): [0.2, 0.4]
- C CAM_5V B.Cu (35.53, 33.5): [0.2, 0.4]
- C CAM_INPUT_LIMITED B.Cu (34.3, 93.5): [0.2, 0.3]
- C CAM_INPUT_LIMITED B.Cu (34.5, 93.5): [0.2, 0.3]
- C CAM_INPUT_LIMITED B.Cu (39.65, 87.6): [0.3, 0.8]
- C GND B.Cu (14.6, 80.1): [0.2, 0.25]
- C GND B.Cu (33.95, 78.55): [0.2, 0.25]
- C GND B.Cu (34.35, 78.05): [0.2, 0.25]
- C GND B.Cu (39.1533, 45.4): [0.2, 0.25]
- C PYRO1_BUS F.Cu (16.17, 95.36): [0.4, 1.0]
- C PYRO1_COLD B.Cu (18.92, 112.3): [0.15, 0.2]
- C PYRO1_COLD B.Cu (18.95, 112.3): [0.15, 0.2]
- C PYRO1_COLD F.Cu (29.3629, 85.7429): [0.15, 0.2]
- C PYRO1_CONT In2.Cu (32.42, 88.4217): [0.15, 0.2]
- C PYRO1_OUT F.Cu (30.58, 90): [0.2, 0.3]
- C RAW_PROTECTED F.Cu (12.6, 40.35): [0.3, 0.5]
- C RAW_PROTECTED B.Cu (14.5, 27): [0.2, 0.6]
- C RAW_PROTECTED B.Cu (15.68, 32.4): [0.25, 0.4]
- C RAW_PROTECTED B.Cu (15.7, 35.75): [0.25, 0.6]
- C RAW_PROTECTED B.Cu (27.4, 27.85): [0.3, 0.6]
- C RAW_PROTECTED B.Cu (27.7, 27.85): [0.25, 0.3]
- C RAW_PROTECTED B.Cu (37.2, 83.575): [0.2, 0.4]
- C RAW_PROTECTED F.Cu (37.95, 49.7): [0.2, 0.4]
- C RAW_PROTECTED B.Cu (38.9, 84.575): [0.2, 0.4]
- C USB_LIMITED B.Cu (24.1272, 61.6228): [0.2, 0.4]
- C USB_LIMITED B.Cu (28.7, 46.55): [0.3, 0.4]
- C USB_LIMITED B.Cu (28.7, 57): [0.3, 0.4]
- C USB_LIMITED B.Cu (29.1, 46.15): [0.2, 0.4]
- C USB_LIMITED B.Cu (29.9, 36.25): [0.3, 0.4]
- C USB_LIMITED B.Cu (29.9, 39.25): [0.3, 0.4]
- C USB_LIMITED B.Cu (30.5, 27.85): [0.25, 0.4]
- C USB_LIMITED B.Cu (30.8, 28.15): [0.25, 0.4]
- C USB_LIMITED B.Cu (30.8, 28.2): [0.3, 0.4]
- C USB_LIMITED B.Cu (30.8, 30.5): [0.3, 0.4]
- C USB_LIMITED B.Cu (31.6, 31.35): [0.3, 0.4]
- C USB_LIMITED B.Cu (31.6, 34.5): [0.3, 0.4]
- C VBUS In2.Cu (12, 79.95): [0.2, 0.4]
- C VBUS In2.Cu (12.6, 80.55): [0.2, 0.4]
- C VCAP2 F.Cu (11.3, 58.5): [0.25, 0.3]
- C VLOGIC B.Cu (11, 38.65): [0.2, 0.5]
- C VLOGIC F.Cu (27.57, 27.2): [0.2, 0.25]
- C VLOGIC F.Cu (27.57, 28.6): [0.2, 0.25]
- C VLOGIC B.Cu (27.825, 28.55): [0.2, 0.25, 0.5]
- C VLOGIC F.Cu (31.27, 27): [0.2, 0.25]

### Width changes at vias (16)

- C 3V3 B.Cu (12.6, 59.5): [0.2, 0.3]
- C 3V3 B.Cu (27.35, 44.25): [0.25, 0.3]
- C 3V3 B.Cu (30.17, 65.1): [0.2, 0.25]
- C 3V3 B.Cu (31.1, 54.5): [0.25, 0.3]
- C 3V3 F.Cu (36, 82.43): [0.2, 0.25]
- C 3V3A B.Cu (35.5, 76.54): [0.2, 0.3]
- C 3V3A B.Cu (35.9632, 69.9393): [0.2, 0.25]
- C 3V3A B.Cu (37.91, 76.75): [0.2, 0.3]
- C BAT_IN F.Cu (9.3, 40.15): [0.3, 0.5]
- C GND F.Cu (24.55, 89.275): [0.2, 0.45]
- C GND B.Cu (29.05, 25.15): [0.2, 0.25]
- C GND B.Cu (31.5, 47.1): [0.2, 0.25]
- C GND B.Cu (31.5, 53.5): [0.2, 0.25]
- C RAW_PROTECTED B.Cu (15.7, 32.4): [0.25, 0.4, 0.6]
- C USB_LIMITED B.Cu (29.1, 40.55): [0.2, 0.4]
- C VBUS F.Cu (11.325, 82.05): [0.2, 0.3]

### Critical-signal layer changes with no GND via within 1.5 mm (52)

- A GNSS_RESET_N via (1.2, 52.5): nearest GND via 9.78 mm, B.Cu/F.Cu
- A GNSS_RXD via (8.21, 25.2): nearest GND via 2.694 mm, B.Cu/F.Cu
- A GNSS_RXD_MCU via (2.2, 51.5): nearest GND via 8.382 mm, B.Cu/F.Cu
- A GNSS_TP_MCU via (2.7, 51): nearest GND via 7.684 mm, B.Cu/F.Cu
- A GNSS_TP_MCU via (9.31, 25.75): nearest GND via 3.881 mm, B.Cu/F.Cu
- A GNSS_TXD_MCU via (1.7, 52): nearest GND via 9.08 mm, B.Cu/F.Cu
- A GNSS_TXD_MCU via (7.11, 24.65): nearest GND via 1.574 mm, B.Cu/F.Cu
- A QSPI_IO0 via (12.9, 44.4): nearest GND via 3.553 mm, B.Cu/F.Cu
- A QSPI_IO0 via (15.55, 50.85): nearest GND via 1.614 mm, B.Cu/F.Cu
- A RADIO_BUSY via (10, 49.5): nearest GND via 3.068 mm, B.Cu/F.Cu
- A RADIO_BUSY via (9.4, 28.2): nearest GND via 5.745 mm, B.Cu/F.Cu
- A RADIO_DIO1 via (10, 50.5): nearest GND via 4.026 mm, B.Cu/F.Cu
- A RADIO_DIO1 via (32.4, 20.15): nearest GND via 1.97 mm, B.Cu/F.Cu
- A RADIO_DIO1 via (9.4, 27.2): nearest GND via 4.92 mm, B.Cu/F.Cu
- A RADIO_MISO_MCU via (10, 28.7): nearest GND via 5.909 mm, B.Cu/F.Cu
- A RADIO_MISO_MCU via (10.7, 48.5): nearest GND via 2.55 mm, B.Cu/F.Cu
- A RADIO_MOSI via (9.4, 29.2): nearest GND via 6.619 mm, B.Cu/F.Cu
- A RADIO_MOSI_MCU via (9.4, 48.5): nearest GND via 1.942 mm, B.Cu/F.Cu
- A RADIO_NRST via (10, 27.7): nearest GND via 5.012 mm, B.Cu/F.Cu
- A RADIO_NRST via (9.3, 50): nearest GND via 3.413 mm, B.Cu/F.Cu
- A RADIO_NSS via (23.2, 17.3): nearest GND via 3.276 mm, B.Cu/F.Cu
- A RADIO_NSS via (23.6, 15.27): nearest GND via 3.61 mm, B.Cu/F.Cu
- A RADIO_NSS via (9.4, 30.2): nearest GND via 7.524 mm, B.Cu/F.Cu
- A RADIO_RXEN via (21.2, 30.45): nearest GND via 2.742 mm, B.Cu/F.Cu
- A RADIO_RXEN via (21.2, 44.45): nearest GND via 3.61 mm, B.Cu/F.Cu
- A RADIO_RXEN via (23.8, 39.45): nearest GND via 2.23 mm, B.Cu/F.Cu
- A RADIO_SCK via (10, 29.7): nearest GND via 6.835 mm, B.Cu/F.Cu
- A RADIO_SCK_MCU via (10, 48): nearest GND via 1.72 mm, B.Cu/F.Cu
- A RADIO_TXEN via (31.13, 20.15): nearest GND via 3.092 mm, B.Cu/F.Cu
- C ARM1_SENSE via (14.55, 94.15): nearest GND via 11.098 mm, F.Cu/In2.Cu
- C ARM1_SENSE via (14.55, 97.55): nearest GND via 11.339 mm, F.Cu/In2.Cu
- C ARM1_SENSE via (18.18, 91.3): nearest GND via 6.684 mm, F.Cu/In2.Cu
- C ARM1_SENSE via (25.28, 47.3): nearest GND via 3.612 mm, B.Cu/In2.Cu
- C ARM1_SENSE_MCU via (24.35, 44.65): nearest GND via 1.851 mm, B.Cu/F.Cu
- C IMU_CS via (25.1, 66.77): nearest GND via 2.374 mm, F.Cu/In2.Cu
- C IMU_CS via (37.2, 80.07): nearest GND via 3.452 mm, B.Cu/F.Cu
- C PYRO1_COLD via (18.85, 102.7): nearest GND via 5.97 mm, B.Cu/In2.Cu
- C PYRO1_COLD via (28.72, 84.5): nearest GND via 4.28 mm, B.Cu/F.Cu
- C PYRO1_CONT via (34.02, 57.9217): nearest GND via 3.141 mm, B.Cu/In2.Cu
- C PYRO1_CONT via (34.52, 64.3217): nearest GND via 2.178 mm, B.Cu/In2.Cu
- C PYRO1_CONT via (34.72, 84.7217): nearest GND via 1.846 mm, F.Cu/In2.Cu
- C PYRO1_CONT via (37.22, 67.0217): nearest GND via 2.157 mm, B.Cu/F.Cu
- C PYRO1_CONT via (41, 75): nearest GND via 3.769 mm, F.Cu/In2.Cu
- C PYRO1_CONT via (41.1, 78.8017): nearest GND via 5.003 mm, F.Cu/In2.Cu
- C PYRO1_GATE_N via (23, 88.33): nearest GND via 1.815 mm, F.Cu/In2.Cu
- C PYRO1_GATE_N via (31.9, 59.23): nearest GND via 1.613 mm, F.Cu/In2.Cu
- C QSPI_IO1 via (13, 51.5): nearest GND via 3.64 mm, B.Cu/F.Cu
- C SPI1_MISO via (28.55, 74.25): nearest GND via 4.019 mm, B.Cu/F.Cu
- C SPI1_SCK via (22.25, 65.65): nearest GND via 2.193 mm, B.Cu/F.Cu
- C USB_DM via (10.05, 76.3): nearest GND via 5.836 mm, B.Cu/F.Cu
- C USB_DP via (8.9, 74.75): nearest GND via 4.615 mm, B.Cu/F.Cu
- C USB_DP via (8.9, 76.35): nearest GND via 6.121 mm, B.Cu/F.Cu

### Short layer hops (< 3 mm) (7)

- A RADIO_NSS B.Cu (23.2, 17.3): to (23.6, 15.27), 2.196 mm
- C 3V3 F.Cu (29.9, 43.625): to (27.35, 44.25), 2.926 mm
- C 3V3 In2.Cu (30.63, 31.3417): to (32.33, 33.0417), 2.404 mm
- C 3V3 B.Cu (44.035, 77.92): to (41.135, 77.92), 2.9 mm
- C CAM_5V F.Cu (43.3, 33.425): to (41.3, 32.425), 2.414 mm
- C USB_DP B.Cu (8.9, 74.75): to (8.9, 76.35), 1.6 mm
- C VBUS F.Cu (10.8, 79.95): to (11.325, 82.05), 2.332 mm

### U-turns (31)

- A 3V3 F.Cu (36.5, 50.15): to (31.15, 54.525), path 11.097 mm, peak turn 315
- A GNSS_ANT_SRC B.Cu (6, 11.05): to (8.25, 12), path 6.631 mm, peak turn 180
- A RADIO_BUSY B.Cu (10, 49.5): to (9.4, 28.2), path 30.575 mm, peak turn 180
- A RADIO_DIO1 B.Cu (10, 50.5): to (9.4, 27.2), path 33.889 mm, peak turn 180
- A RADIO_MISO_MCU B.Cu (10.7, 48.5): to (10, 28.7), path 30.426 mm, peak turn 225
- A RADIO_NRST B.Cu (9.3, 50): to (10, 27.7), path 32.132 mm, peak turn 180
- A RADIO_NSS B.Cu (9.3, 47.5): to (9.4, 30.2), path 23.249 mm, peak turn 180
- A RADIO_TXEN B.Cu (31.13, 20.15): to (28.59, 7.8), path 22.719 mm, peak turn 180
- C 3V3 B.Cu (14.6, 59.78): to (12.6, 59.5), path 2.261 mm, peak turn 180
- C 3V3 B.Cu (27.82, 61): to (27.85, 62.75), path 1.862 mm, peak turn 180
- C 3V3 F.Cu (33.57, 35): to (34.6647, 36.1053), path 3.446 mm, peak turn 180
- C 3V3 B.Cu (36.94, 52.65): to (41.58, 53.9), path 16.266 mm, peak turn 270
- C 3V3A B.Cu (38.68, 77.5): to (37.91, 76.73), path 1.174 mm, peak turn 180
- C 3V3A B.Cu (38.68, 77.8): to (35.5, 76.54), path 4.367 mm, peak turn 180
- C 3V3A B.Cu (39.2632, 51.1393): to (35.9632, 69.9393), path 23.147 mm, peak turn 180
- C GND F.Cu (14.3, 59): to (11.3, 59.3), path 6.621 mm, peak turn 225
- C GND F.Cu (16.35, 45.95): to (16.35, 43.55), path 6.556 mm, peak turn 270
- C GND F.Cu (25.17, 109.8): to (25.37, 107.9), path 4.09 mm, peak turn 180
- C GND F.Cu (29.345, 30.05): to (27.65, 29.85), path 2.319 mm, peak turn 225
- C GND B.Cu (42.05, 52.55): to (44.65, 54.95), path 5.428 mm, peak turn 180
- C GND F.Cu (6.31, 79.625): to (6.88, 78.5), path 3.326 mm, peak turn 180
- C PYRO1_COLD B.Cu (18.935, 112.285): to (18.85, 102.7), path 9.693 mm, peak turn 270
- C RAW_ACT B.Cu (10, 90.78): to (4, 105.98), path 31.294 mm, peak turn 180
- C RAW_ACT F.Cu (10.4, 64.67): to (13.7, 65.37), path 5.604 mm, peak turn 180
- C RAW_PROTECTED B.Cu (15.7, 35.75): to (15.7, 32.4), path 3.45 mm, peak turn 180
- C SPI1_SCK B.Cu (22.25, 65.65): to (36, 79.26), path 24.409 mm, peak turn 225
- C USB_DM F.Cu (6.88, 74.55): to (10.05, 76.3), path 7.28 mm, peak turn 180
- C USB_LIMITED B.Cu (28.7, 57): to (29.825, 27.9), path 31.399 mm, peak turn 180
- C USB_LIMITED In2.Cu (29.1, 40.55): to (25.8, 37.15), path 7.401 mm, peak turn 180
- C VCAP2 F.Cu (14.3, 58.5): to (16, 62.4), path 11.15 mm, peak turn 180
- C VLOGIC F.Cu (27.57, 28.9): to (27.57, 28.6), path 3.1 mm, peak turn 180

### Chain detours (47)

- A 3V3 F.Cu (36.5, 50.15): to (31.15, 54.525), 11.097 vs 7.162 mm
- A GNSS_ANT_SRC B.Cu (6, 11.05): to (8.25, 12), 6.631 vs 2.644 mm
- A RADIO_BUSY B.Cu (10, 49.5): to (9.4, 28.2), 30.575 vs 21.549 mm
- A RADIO_BUSY F.Cu (9.4, 28.2): to (24.91, 11.46), 31.781 vs 23.164 mm
- A RADIO_DIO1 B.Cu (10, 50.5): to (9.4, 27.2), 33.889 vs 23.549 mm
- A RADIO_MISO_MCU F.Cu (10, 28.7): to (22.57, 12.73), 27.876 vs 21.177 mm
- A RADIO_MISO_MCU B.Cu (10.7, 48.5): to (10, 28.7), 30.426 vs 20.09 mm
- A RADIO_MOSI F.Cu (9.4, 29.2): to (24.91, 14), 29.85 vs 21.806 mm
- A RADIO_NRST B.Cu (9.3, 50): to (10, 27.7), 32.132 vs 22.59 mm
- A RADIO_NSS B.Cu (9.3, 47.5): to (9.4, 30.2), 23.249 vs 17.341 mm
- A RADIO_NSS F.Cu (9.4, 30.2): to (23.2, 17.3), 25.646 vs 19.143 mm
- A RADIO_SCK F.Cu (10, 29.7): to (24.91, 16.54), 27.014 vs 20.361 mm
- A RADIO_SCK_MCU B.Cu (10, 48): to (5.7, 44.43), 7.523 vs 5.779 mm
- A RADIO_TXEN B.Cu (31.13, 20.15): to (28.59, 7.8), 22.719 vs 13.402 mm
- B RAW_PROTECTED B.Cu (14, 33.3): to (28.525, 27.85), 21.568 vs 16.782 mm
- C 3V3 In2.Cu (30.63, 31.3417): to (35.73, 27.3417), 11.211 vs 6.757 mm
- C 3V3 B.Cu (31.5, 45.225): to (35.1, 45.025), 5.521 vs 3.683 mm
- C 3V3 F.Cu (33.57, 35): to (34.6647, 36.1053), 3.446 vs 1.559 mm
- C 3V3 B.Cu (36.94, 52.65): to (41.58, 53.9), 16.266 vs 5.158 mm
- C 3V3A B.Cu (32.3, 44.475): to (29.4, 49.975), 8.736 vs 6.701 mm
- C 3V3A B.Cu (34.62, 71.7): to (32.72, 71.9), 3.68 vs 1.983 mm
- C 3V3A B.Cu (40.0632, 51.9393): to (38.2632, 48.1), 5.765 vs 4.585 mm
- C ARM1_SENSE F.Cu (14.55, 94.15): to (17.28, 92.4), 4.48 vs 3.455 mm
- C GND F.Cu (14.3, 59): to (11.3, 59.3), 6.621 vs 3.124 mm
- C GND B.Cu (14.6, 80.1): to (11.6, 83.15), 5.684 vs 4.293 mm
- C GND F.Cu (16.35, 45.95): to (16.35, 43.55), 6.556 vs 2.4 mm
- C GND F.Cu (25.17, 109.8): to (25.37, 107.9), 4.09 vs 1.983 mm
- C GND F.Cu (29.345, 30.05): to (27.65, 29.85), 2.319 vs 1.778 mm
- C GND B.Cu (32.3, 55.7): to (31.5, 53.5), 4.014 vs 2.531 mm
- C GND B.Cu (42.05, 52.55): to (44.65, 54.95), 5.428 vs 3.594 mm
- C GND F.Cu (6.31, 70.975): to (6.88, 72.1), 2.758 vs 1.361 mm
- C GND F.Cu (6.31, 79.625): to (6.88, 78.5), 3.326 vs 1.361 mm
- C GND B.Cu (6.31, 79.625): to (6.8, 74.9), 7.297 vs 4.928 mm
- C GND B.Cu (6.31, 79.625): to (6.0062, 82.8312), 4.95 vs 3.332 mm
- C PYRO1_CONT F.Cu (34.72, 84.7217): to (41.1, 78.8017), 12.595 vs 8.832 mm
- C QSPI_IO3 F.Cu (21.7, 34.6): to (22.5, 40.3), 8.431 vs 6.031 mm
- C RAW_ACT B.Cu (10, 90.78): to (4, 105.98), 31.294 vs 17.685 mm
- C RAW_ACT F.Cu (10.4, 64.67): to (13.7, 65.37), 5.604 vs 3.59 mm
- C SPI1_SCK B.Cu (22.25, 65.65): to (36, 79.26), 24.409 vs 19.387 mm
- C USB_DM F.Cu (6.88, 74.55): to (10.05, 76.3), 7.28 vs 3.895 mm
- C USB_DP B.Cu (8.9, 76.35): to (11.95, 75.15), 5.24 vs 3.547 mm
- C USB_LIMITED In2.Cu (29.1, 40.55): to (25.8, 37.15), 7.401 vs 4.767 mm
- C USB_LIMITED B.Cu (33.1, 26.15): to (30.4, 27.75), 4.411 vs 3.363 mm
- C VBUS In2.Cu (11, 76.35): to (12, 79.95), 5.711 vs 4.014 mm
- C VCAP2 F.Cu (14.3, 58.5): to (16, 62.4), 11.15 vs 4.604 mm
- C VLOGIC F.Cu (27.57, 28.6): to (31.67, 35.5), 13.857 vs 8.598 mm
- C VLOGIC F.Cu (27.57, 28.9): to (27.57, 28.6), 3.1 vs 0.3 mm
