# R7 review pass 5: routing geometry and style (whole board)

Reviewer: independent, read-only. Dimension: routing geometry and style, every track and via on all four layers,
copper inherited from R6 included. Acceptance criterion: CLEAN ROUTING (AGENTS.md §3 plus the owner's list in
REQUIREMENTS M2), and for this pass in particular: is every remaining allowlist entry and every recorded non-critical
leftover reason measured and true?

- **Board reviewed:** `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
  `c6fe595cafb91b088ac0b2c812f409f9ca5b86ac45a651102e168b0a5d83c7c7` (the fix-pass-4 board of `fix4_F5_handoff.md`;
  unchanged at the end of this review). 1,809 tracks, 694 vias, no arcs, 4,505.6 mm of track: F.Cu 702 tracks /
  1,584.7 mm, B.Cu 811 / 1,897.6 mm, In2 293 / 1,019.6 mm, In1 3 / 3.7 mm.
- **Comparison boards:** pass-4 board `636a6bdc…7650` (1,836 tracks, 694 vias) and committed R6 `3b215ba` (+18 mm).
- **Gate on this board:** `tools/check.sh` exit 0: DRC 0, unconnected 0, schematic parity 0, ERC 0; metadata/3D OK;
  silkscreen 0; "R7 CAD contract: OK"; "routing hygiene: 0 failing, 37 allowlisted, 0 stale allowlist entries, 0
  out-of-date no-GND reasons, 34 leftovers recorded (0 unrecorded, 0 stale): OK"; actuator safety contract OK; fit
  OK. `tools/test_route_check.py`: 32 tests OK.
- Nothing in the repository was modified except this file. Scratch work, scripts, scratch board copies and images:
  `<scratch>/p5rg/`
  (below `<p5rg>`). Scratch copies were saved only under `<p5rg>/v_*`.

## 1. Verdict

Fix pass 4 closed P4-ROUTING_GEOMETRY-01 properly: the PYRO1_GATE_N GND via is on the board (0.6/0.3 mm at
(22.85, 89.63), 1.309 mm from the layer change), its allowlist entry is gone, and the new gated `nognd_audit` works.
For all 10 remaining no-GND entries my own probes (project rules, DRC-only rules, existing-via nudges) find no spot,
so those 10 reasons are true. The F5 copper (PYRO1_CONT plane-preserving route, CAM_UART_OE and NRST reroutes, band
edits, 10 debris redraws, the GND vias) is on 0/45/90° headings. My scan finds no off-angle segment, no segment under
50 µm, no fold-back, no crossing without a node, no duplicate or overlap-only copper, no off-centre via joint and no
dangling end or via anywhere on the board. The fix pass added no new instance of any gated category.

What is left:

- **One Major (P5-ROUTING_GEOMETRY-01): three gated critical-net allowlist entries rest on reasons that are not
  true.**
  - The QSPI_CLK tiny jog (A5) and the RADIO_BUSY / RADIO_MISO_MCU staircases (A1, A2) each say the instance is
    forced.
  - DRC-clean edits remove all three. QSPI_CLK's jog goes once RADIO_RXEN's lane moves onto its own via's column;
    that edit also removes RXEN's jog across the via (D12). The band staircases go with longer east chamfers.
  - Scratch copies `v_qspi` and `v_band`: DRC 0, unconnected 0 and parity 0, `check_r7` and `check_actuators` OK,
    and the only route_check results are the now-stale entries, plus one GND finger that `pour_trim` trims.
  - The records say "measured as forced" (R7_VALIDATION P4-DOCS-01, A1/A2/A5 rows) and "each with a measured
    reason that the gate re-checks" (M3_R7). The gate re-checks only the no-GND reasons.
- **Three Minors:**
  - **P5-02:** two of two "forced" non-critical tiny-jog leftovers (CAM_EN, CAM_FAULT_N) are not forced, and D13
    (CAM_RX_WIRE, from F5's own redraw) is removable. Scratch `v_jogs` removes all three. Also: four "no path"
    leftovers record no measurement, and the NRST length is misquoted.
  - **P5-03:** the ARM1_SENSE no-GND exceptions quote the superseded 35 µm model. Complying costs +0.04 mΩ (+0.9 %)
    on the current model, with DRC-clean vias.
  - **P5-04:** route_check residual soundness gaps.

No Critical. Nothing found is open, shorted or below a DRC rule.

## 2. Method

Scripts in `<p5rg>` (KiCad 10.0.6 Python; boards loaded read-only, scratch copies saved only under `<p5rg>/v_*`):

| Script | What it does |
|---|---|
| `scan5.py` | **Independent scan written for this pass**; no code from route_check, p4scan or scan.py. Segments per (layer, net). Nodes are end points clustered at 1 µm, typed end / plain / T / via / pad. Per segment: heading error, length, inside-one-pad/via test, through-pad and inside-pad. Per node: every branch-pair angle, with the acute wedge tested against the node's pad/via copper polygon, plus collinear-unmerged and neck-downs. Open ends are classed (track copper only / overlap-only / pour-only / dangling); off-centre via joints; pad entries (offset, distance to the pad edge). **Jogs by geometry at any node type:** P, S, Q with P ∥ Q and S turning off them, wherever P and Q attach. Jogs across a via; alternation runs (staircases) followed through any node. **Same-net copper redundancy by polygon booleans:** a track wholly inside the union of other same-net tracks. Crossings; same-net via-ring overlap; every via with same-net tracks/pads on ≥ 2 layers checked against the nearest GND via and GND PTH |
| `clr5.py` | Clearance probe: candidate polylines against other-net copper on the layer (tracks, every via, exact pad polygons, optionally other-net pour fills), and vias against every layer |
| `edit5.py` | Applies candidate edits to a copy, refills natively (`ZONE_FILLER`), saves `<p5rg>/v_<variant>/m3.kicad_pcb` with the project's `.kicad_pro` / `.kicad_dru` and the schematic sheets beside it |
| `probe.py` / `probe_drc.py`, `nudge.py` | The pass-3/4 GND-via probe at 0.025 mm with no margin (project rules), the same probe with only board DRC rules (no paste / GND-pad / bare-TP / Tag-Connect / mask extras), and the existing-GND-via move search |
| `gs5.py`, `gfit5.py` | The project's own `r7_hygiene.gnd_spots` / `GndFit`, imported read-only, on scratch copies |
| `p4scan.py`, `p4extra.py`, `rc_allpairs.py`, `scan_p2.py` (= `rg/scan.py`), `newinst.py`, `diff.py`, `render.py` | The pass-4 and pass-2 reviewers' scripts, unchanged, on the final and pass-4 boards |

I also ran `tools/route_check.py --report --routes`, `tools/check_r7.py`, `m3_design/check_actuators.py`,
`tools/dc_solve.py` and `kicad-cli pcb drc --severity-all --schematic-parity` on every scratch variant.

## 3. Pass-4 findings in this dimension: closure check

| ID | Pass 4 (skeptics) | R7_VALIDATION disposition | Verified on the final board |
|---|---|---|---|
| P4-RG-01 | Major → Minor (Minor ×2, Major), worked as Major | Fixed | **Closed.** GND via 0.6/0.3 mm at (22.85, 89.63); distance to the PYRO1_GATE_N layer change (23.0, 88.33) 1.3086 mm. The allowlist entry is gone (`route_check.py` lines 176–257). `r7_polish` reruns `gnd_vias` (fine 0.025 mm pass) after the last copper change and `gnd_vias2` after the strip stitching. `nognd_audit` (`route_check.py` lines 1695–1715) runs in `main()`, so in `check.sh`, and prints "0 out-of-date no-GND reasons". `_NOGND` no longer cites the pass-3 board. Records corrected: P3-RG-02 row "10 entries", M3_R7 line 430, STATUS line 77. My `probe.py`, `probe_drc.py` and `nudge.py` find no spot for any of the other 10 (§6) |
| P4-RG-02 | Minor | Not done (tools); instances recorded, deviation list D1–D9, D13, D18 | **Properly dispositioned** (a Minor recorded, not reworked). Every listed instance is still on the board: ACT_GATE wedge (5.9, 102.4) is still the one `rc_allpairs.py` failure; the GND C94.2 staircase; CAM_5V via jog; 3V3_RADIO FB31.2; GND (31.3, 53.7); CAM_FAULT_N In2; RAW_ACT pour tail (3.174 mm inside its fill); TP122; the three launch via pairs (0.5852 mm). New measurement for the record: **D3 and D13 are removable** (§7 P5-02, §8) |
| P4-RG-03 | Minor | Judgement recorded; tidy-ups not done (D10–D12) | **Properly dispositioned.** D10 (USB_LIMITED U11.7), D11 (VLOGIC U2.2, 0.5 mm inside the pad) and D12 (RXEN 0.318 mm jog across via (23.8, 39.45)) are still present. **D12 is removable** together with A5 (§7 P5-01) |

P4-DOCS-01 (Major, open for the owner) overlaps this dimension. Its record says fix pass 4 left "BUSY and MISO_MCU
measured as forced" and "CAM_EN, CAM_FAULT_N, both forced". This pass measures all four as not forced (§7 P5-01,
P5-02).

## 4. Counts

### 4.1 Gate (`route_check --report --routes`), final board

323 instances, 0 failing, 37 allowlisted, 0 stale, 0 out-of-date no-GND reasons, 34 leftovers recorded (0
unrecorded, 0 stale). This equals F5's handoff §3.

- **Gated or recorded categories, all (critical):**
  - staircase 2 (2);
  - critical_via_no_gnd 10 (10);
  - tiny_jog 6 (4);
  - short_segment 2 (2);
  - detour 22 (9);
  - extra_vias 29 (10);
  - pour_sliver / pour_finger / pad_pour_cut 0 / 0 / 0.
- **Information, all (critical):**
  - width_change_junction 30 (29);
  - pad_end_offcentre 93 (64);
  - segment_inside_pad 3 (2);
  - passes_through_pad 10 (10);
  - extra_bends 34 (12);
  - u_turn 25 (18);
  - short_layer_hop 21 (9);
  - power_via_no_gnd 36.

### 4.2 Independent scan (`scan5.py`), final vs pass-4 board, all (critical)

| Category | Pass-4 board | **Final** | Notes on the final board |
|---|---|---|---|
| off_angle / zero_length / arcs | 0 / 0 / 0 | **0 / 0 / 0** | |
| crossing (same net, both interiors) | 0 | **0** | |
| fold_back | 0 | **0** | |
| acute, wedge exposed | 1 (0) | **1 (0)** | ACT_GATE B.Cu at Q121.4 (5.9, 102.4), non-critical (D1) |
| collinear_unmerged | 0 | **0** | |
| end dangling / overlap-only / in track copper only | 0 / 0 / 0 | **0 / 0 / 0** | |
| end pour-only | 1 (1) | 1 (1) | RAW_ACT F.Cu (5.3, 82.17) (D7) |
| via_offcentre / via_dangling | 0 / 0 | **0 / 0** | |
| short (open, < max(w, 0.2 mm)) | 2 (2) | 2 (2) | SW_NODE ×2 (A7, A8) |
| jog_tiny (any node type) | 17 (9) | **11 (8)** | Gate's 6 (QSPI_CLK, RADIO_BUSY, RADIO_MISO_MCU, SW_NODE, CAM_EN, CAM_FAULT_N) plus 5 at T/via/pad corners: GND (36.16, 28.01), GND (31.3, 53.7), 3V3_RADIO FB31.2, CAM_5V via (39.35, 104.55), CAM_RX_WIRE T (44.09, 55.14) (D2–D5, D13) |
| staircase (alternation through any node) | – | 7 (4) | Gate's 2 (BUSY, MISO_MCU) plus GND C94.2 (D2), CAM_5V (D3), CAM_FAULT_N In2 (D6), CAM_RX_WIRE In2 (D13) |
| redundant track copper (polygon) | – | 1 (1) | CAM_5V B.Cu (38.925, 104.55)–(39.35, 104.55): 99.93 % covered by other CAM_5V tracks (the D3 jog) |
| jog across a via, tiny | – | 6 (1) | RADIO_RXEN (23.8, 39.45) 0.318/0.225 (D12); non-critical: PULLPIN_EXT, CAM_5V_SENSE, LOGIC_SOURCE_ST, BOOT0, CAM_RX_WIRE |
| via ring overlap (same net) | 3 | 3 | RF launch GND pairs at 0.5852 mm (D9) |
| critical layer change, no GND via ≤ 1.5 mm | 12 | **11** | Gate's 10 plus PYRO1_GATE → TP122's pad via (20.45, 92.4), 2.928 mm (D8) |
| pad_offcentre (> 0.1 mm, pad ≤ 2 mm) | – | 87 (61) | Critical ones within 0.05 mm of the pad edge: Appendix A1 |
| inside_pad / through_pad | 2 / 10 | 3 / 10 | +LED_YEL_A 0.55 mm inside LED2.1 (F5's redraw put its corner inside the pad, a tidy form) |
| neck (width change at a plain node) | 5 | 5 | All pad-entry necks into the pad they end in (≤ 1.4 mm) |

My 11 tiny jogs equal p4scan's 11 (8 critical) on the final board. My staircases and jogs equal the gate's within
the gate's grammar; the rest are the P4-RG-02 S2 instances.

### 4.3 Other scans

- **p4scan.py (pass 4, unchanged):** final 1,809 tracks; acute 12 (6); jog_tiny 11 (8); staircase 2 (2);
  crit_layer_change_no_gnd 11; leaf_stub 5 (the RAW_ACT tail run); via_overlap 3.
- **New since pass 4** (`newinst.py`):
  - two pad entries off centre: SERVO3_MCU into D121.4, 0.41 mm; LED_YEL_A into LED2.1, 0.55 mm;
  - PYRO1_CONT into R129.2, 0.18 mm off centre;
  - the CAM_RX_WIRE 0.228 mm T-jog;
  - RADIO_NRST's 0.141 mm segment inside its via (D14);
  - extra-bend runs on PYRO1_CONT and RADIO_SCK;
  - 3V3 via (30.4, 78.25) now 1.992 mm from a GND via: F5 removed the old PYRO1_CONT return via (29.28, 77.95);
    power, information.
- **Gone since pass 4:** 11 non-critical short segments and tiny jogs; the RADIO_NRST and RADIO_SCK staircases; the
  PYRO1_GATE_N no-GND instance; the PYRO1_CONT jog across a via.
- **Pass-2 `scan.py` (unchanged):** 958 instances (595 critical), equal to F5's figure.

## 5. route_check audit

### 5.1 The new allowlist-truth check (`nognd_audit`, lines 1695–1715)

- **What it does.** For every *allowed* critical_via_no_gnd instance it runs `r7_hygiene.gnd_spots(board, q, 1.5,
  first=True)`. That search is `GndFit` = `r7_route.ViaCheck` (board rules + 0.02 mm; hole to hole 0.27 mm; edge and
  supports; no via within 0.15 mm of a GND solder pad; paste; via keep-outs; In1 launch cut-outs) plus bare TP
  1.02 mm, Tag-Connect 0.528 mm, Pyro D 0.52 mm including pyro fills, and no via within 0.5 mm of a BAT_IN / RAW_ACT
  / ACT_FET_S pour inside its servo-current corridor. It tries 0.6 and 0.5 mm vias on a 0.025 mm grid, nearest first.
  The gate fails if a spot exists.
- **Sound for its scope.**
  - Its window is q ± 4.0 mm, and every candidate within 1.5 mm is ≥ 2.5 mm inside it; the copper `ViaCheck` sees is
    filtered by bounding box, which cannot drop an item that reaches the window.
  - The pyro and heavy pour fills are loaded unfiltered.
  - Its unit test runs the real search on a synthetic board, with and without a via keep-out.
  - On the final board it reports 0. My independent probes agree for all 10 entries (§6.1): the project-rule probe,
    the DRC-only probe and the existing-via nudge find no spot for the 8 radio entries; ARM1_SENSE's only spots are in
    the BAT_IN corridor.
- **What it cannot do:**
  - It covers no-GND reasons only. The staircase, tiny-jog and short-segment reasons in the allowlist, and every
    LEFTOVERS reason, are text that nothing re-measures. This pass found five of them untrue (P5-01, P5-02). M3_R7
    line 531 ("12 … each with a measured reason that the gate re-checks (`nognd_audit`)") overstates it: the gate
    re-checks 10 of the 12.
  - The corridor exclusion is policy, so the audit can never challenge the ARM1_SENSE entries (P5-03).
  - Pad-only layer changes are still not counted (S4: TP122).

### 5.2 LEFTOVERS record check (`leftover_check`, lines 1672–1692)

- **Correct as written.** Every non-critical detour / extra_vias / tiny_jog / short_segment instance needs an entry.
  An entry must match an instance (category, net, layer, position within 0.02 mm). The test cases cover a critical
  instance being skipped, a missing entry and a stale one. On the final board it gives 34 recorded, 0 missing, 0
  stale.
- **Gaps (P5-04):**
  - (a) Detour and extra_vias instances sit at the net's first pad. An entry for one therefore never goes stale when
    the route changes, and its quoted length, via count and search result can drift without failing. One already
    has: NRST "47 mm / 4 vias", while `--routes` gives 46.11 mm.
  - (b) `LEFTOVER_CATS` covers 4 of the 14 hygiene categories. A non-critical duplicate, overlap, crossing,
    overlap-only joint or neck-down would be counted and pass with no record. There are 0 on this board.

### 5.3 Remaining category gaps (P4-RG-02 S1–S5, unchanged in code)

| Gap | Code | Instances on the final board |
|---|---|---|
| S1: only the sharpest branch pair is tested | lines 1483–1506 | ACT_GATE (5.9, 102.4); `rc_allpairs.py`: "FAIL acute_angle ACT_GATE B.Cu (5.9, 102.4)" |
| S2: jogs and staircases only along plain-node chains | `plain()` line 1375; chains lines 1523–1594 | 5 tiny jogs and 4 staircases at T, via or pad corners (§4.2) |
| S3: pour stubs only as whole runs | lines 733–779 | RAW_ACT tail (5.3, 82.17), 3.174 mm inside its fill |
| S4: pad-only layer changes not counted | `critical_transitions` line 859 | PYRO1_GATE → TP122 (20.45, 92.4), 2.928 mm |
| S5: no same-net via overlap test | – | 3 launch pairs |

## 6. Allowlist (37) and leftovers (34): every entry checked

### 6.1 Allowlist

| Entries | Claim | Result on the final board |
|---|---|---|
| A1, A2 staircase RADIO_BUSY, RADIO_MISO_MCU | "…the east chamfers into the strip columns … are fixed by the same pitch: two 45 deg steps under 1 mm each … squaring the east corners instead collides" | **Not true** (P5-01). The chamfers are free in nested lanes. BUSY's can be 1.004 mm at an unchanged 0.25 mm minimum clearance; MISO_MCU's too, with its own and MOSI's steps 0.35–0.4 mm later. DRC-clean (`v_band`) |
| A3, A4 tiny_jog RADIO_BUSY, RADIO_MISO_MCU | Via rows 0.5 mm, lanes 0.4 mm; a 9.4-column lane keeps its row past the 10.0 column (0.475 mm needed) | **True.** Offsets 0.2 / 0.3 mm are set by rows 28.2 → lane 28.0 and 28.7 → 28.4. At 45° a 0.3 mm offset gives a 0.424 mm diagonal (< 0.5), and 0.2 mm < 0.25. BUSY at y 28.0 at x 10.0 would sit 0.025 mm into RADIO_NRST's via (10.0, 27.7). Both stay tiny in `v_band` |
| A5 tiny_jog QSPI_CLK | "straight on … passes the LED_YEL via … at 0.15 mm"; a non-tiny step "brings the clock within 0.196 mm of RADIO_RXEN" | **Not true as a reason it cannot be removed** (P5-01). Straight on, the clock in fact runs into QSPI_IO3's via (22.5, 40.3): −0.05 mm, a collision, not 0.15 mm. The 0.196 mm holds only with RXEN where it is, and RXEN can move to its via's column x 23.8 with ≥ 0.329 mm everywhere; the step then keeps 0.415 mm. DRC-clean (`v_qspi`) |
| A6–A8 SW_NODE | C7.2/C9.2 gap, U2 vias, every one-bend route collides | **True** (copper unchanged since pass 4, whose measurements stand; `diff.py` shows no SW_NODE change) |
| A9–A16 no-GND, radio (RXEN (23.8, 39.45); NRST (9.3, 50.0); BUSY (9.4, 28.2), (10.0, 49.5); MOSI (9.4, 29.2); DIO1 (10.0, 50.5); MISO_MCU (10.0, 28.7); MOSI_MCU (9.4, 48.5)) | No legal spot within 1.5 mm; slides open none | **True.** Nearest GND vias 2.230, 3.178, 1.649, 2.596, 1.649, 3.569, 2.110, 1.709 mm (= the entries). `probe.py` (project rules), `probe_drc.py` (board DRC only) and `nudge.py` (existing GND vias moved): NONE for all 8. Top blockers are the band and corridor lanes and holes (e.g. BUSY (9.4, 28.2): RADIO_NRST hole/track, RADIO_MOSI hole) |
| A17, A18 no-GND ARM1_SENSE (14.55, 94.15), (14.55, 97.55) | Legal spots only in the J1 → Q120 BAT_IN corridor; two vias raise the path 3.91 → 3.95 mΩ | **True, but the cost is quoted in the superseded model, and complying is DRC-clean** (P5-03). Probe spots (13.85, 97.525) / (13.975, 93.75) are both "heavy". With 0.6 mm vias at (13.8, 97.525) and (13.9, 93.775), `dc_solve` on the board's own stack-up gives 4.55 → 4.59 mΩ |
| A19–A28 R7 interface detours / vias, GNSS limiter | Lengths, vias, search results, keep-outs | **True as evidenced.** `--routes`: GNSS_RESET_N 59.34 mm / 2; RADIO_DIO1 69.09 / 4; RADIO_NRST 85.44 / 4; RADIO_NSS 58.40 / 4; RADIO_RXEN 51.88 / 4; RADIO_TXEN 25.17 / 2; GNSS_LNA_EN 7.45; GNSS_VCC_RF 6.20, all equal to the entries. Not re-routed (search outputs as verified in pass 4) |
| A29 extra_vias PYRO1_CONT | No route under 6 vias with every power pour whole and 1.0 mm to PYRO1_GATE_N | **True as evidenced**: `fx4/rt/pc7`–`pc9` best 49.21 mm / 6 vias, `pc6` NO PATH. Present route 47.53 mm (R168.1 → R129.2); `--routes` net total 53.33 mm with the divider legs. Every PYRO1_CONT layer change has a GND via ≤ 1.5 mm (none in my no-GND list) |
| A30–A37 ARM1_SENSE, QSPI_IO2 vias; VCAP1, VCAP2, VBUS ×2, RAW_PROTECTED, VLOGIC | Lengths / vias / pad lists | **True as evidenced**: 63.73 / 4; 33.26 / 3; 6.71 / 2 for 1.37; 12.67 / 1 for 3.00; VBUS 42.49 / 6; RAW_PROTECTED 143.53 / 7; VLOGIC 66.87 / 5 (unchanged copper) |

### 6.2 Leftovers

- **Present length and vias equal `--routes` for 33 of 34.** The exception is NRST: the entry says "47 mm / 4 vias";
  the board has 46.11 mm / 4 (also in R7_VALIDATION B24 and M3_R7 line 421).
- **The quoted search results match F5's router outputs** (`fx4/det/r3`, `r4`, `r5`, summed per pad edge):
  BAT_FAULT_N 31.41 / 2; BUZZ_OUT 21.69 / 1; CAM_EN 7.45 / 1; CAM_FAULT_N 78.87 / 7; CAM_MCU_RX 32.14 / 5;
  CAM_PWR_EN 59.09 / 8; CAM_UART_OE 33.10 / 5; LED_YEL 36.0 / 3; LOGIC_SOURCE_ST 55.48 / 10; NRST 45.43 / 5;
  RAW_ACT_SENSE 41.35 / 2; SERVO1_MCU 62.16 / 4; SERVO2_OUT 31.42 / 1; SERVO4_MCU 97.84 / 11; SERVO4_OUT 52.39 / 6;
  SWCLK 60.99 / 4; SWDIO 53.98 / 4; VBUS_SENSE 47.22 / 6; BAT_SW_RETURN 177.7 / 7; BAT_SW_SOURCE 124.85 / 6.
  I did not re-run the router.
- **B1 CAM_EN tiny jog, "forced": not true** (P5-02). The claim holds only for a single 45° run. A W–S–SW run clears
  everything by ≥ 0.209 mm (today: 0.184 mm).
- **B2 CAM_FAULT_N tiny jog, "forced": not true** (P5-02). One straight In2 run at y 103.938 keeps 0.161 / 0.162 mm,
  above the house 0.16 mm. The quoted "straight on at y 103.778 passes SERVO4_MCU 0.15 mm apart" is wrong: the edge
  gap there is 0.0012 mm.
- **B8–B11 (CAM_5V_SENSE ×2, LED_RED, SERVO2_MCU): the evidence is "no path".** The search cannot reproduce even the
  existing route, so these entries record no measurement of what forces the route.
  - Example, SERVO2_MCU (9 vias). Its F.Cu hairpin, vias (28.1, 58.6) and (30.1, 60.8), exists to hop the C13.2 GND
    tie: B.Cu (29.4, 57.82) → (29.4, 59.7) → (28.9, 60.2). A straight B.Cu run at y 58.6 overlaps it by −0.175 mm.
  - My `GndFit` search finds no legal GND via spot within 1 mm of C13.2 north of that row, so the hairpin may well be
    needed. The record should say this instead of "no path".

## 7. Findings

### P5-ROUTING_GEOMETRY-01 (Major): three gated critical-net allowlist entries (A1, A2, A5) rest on reasons that are not true; DRC-clean edits remove all three

**Requirement.**
- AGENTS.md §3: no staircases, a §3 rule gated on every net.
- REQUIREMENTS M2: no tiny jogs, gated on critical nets. "Every exception is an allowlist entry in that tool with a
  measured reason", and R7 acceptance needs the M2 routing check OK.
- The gate's OK for RADIO_BUSY (rfif), RADIO_MISO_MCU (spi) and QSPI_CLK (spi) rests on these three entries.

**A5, QSPI_CLK tiny jog at U1.36** (`route_check.py` lines 181–185):
- **Present:** (22.85, 45.95) → (22.85, 44.65) → 0.424 mm NE → lane x 23.15 → (23.15, 34.85) → NW diagonal.
- **What the reason gets wrong:**
  - Its first claim names the wrong obstacle. Straight on at x 22.85, the clock runs into the QSPI_IO3 via
    (22.5, 40.3), Ø0.6 mm: edge gap −0.05 mm, i.e. overlapping copper. The LED_YEL via (22.35, 41.35) at 0.15 mm is
    not the binding obstacle.
  - Its second claim ("a step long enough to leave the tiny-jog class … brings the clock within 0.196 mm of
    RADIO_RXEN") holds only with RXEN's lane at x 23.575. That lane jogs 0.225 mm into its own via (23.8, 39.45),
    which is deviation D12.
- **Measured** (`clr5.py`, then DRC):
  - RXEN's lane can run on its via's column: (22.575, 30.45) → (23.8, 31.675) → (23.8, 39.45). Minimum clearance to
    other copper 0.329 mm (GND via (23.92, 30.8)); 0.475 mm to today's clock lane; nothing else within reach.
  - QSPI_CLK can then step 0.36 mm (diagonal 0.509 mm, not tiny): (22.85, 44.65) → (23.21, 44.29) → (23.21, 34.91) →
    (21.65, 33.35). The NW diagonal keeps its line, x − y = −11.7. It keeps 0.415 mm to RXEN (today 0.25 mm), 0.25 mm
    to U1.35 and 0.325 mm to LED_YEL, as today.
  - **Scratch `<p5rg>/v_qspi`:**
    - `kicad-cli pcb drc --severity-all --schematic-parity`: 0 violations, 0 unconnected, 0 parity.
    - `check_r7`: "R7 CAD contract: OK". `check_actuators`: OK.
    - `route_check`: "FAIL stale allowlist entry … ('tiny_jog', 'QSPI_CLK', 'F.Cu', (22.85, 45.95))", plus one
      pour_finger: GND F.Cu 0.4 × 4.0 mm at (24.02–24.42, 35.97–39.97), between the moved RXEN and QSPI_IO2.
      `r7_polish.pour_trim` trims exactly this kind of piece automatically (its `TRIM_EXPECTED` count goes 21 → 22).
    - `scan5.py`: no new instance. Gone: the QSPI_CLK tiny jog and RXEN's tiny jog across its via (D12).
  - `gnd_spots` at RXEN's via on `v_qspi`: still none, so A9 is unchanged.

**A1, A2, RADIO_BUSY and RADIO_MISO_MCU staircases** (`_BAND`, lines 153–160):
- **The claim:** the east chamfers "are fixed by the same pitch" and squaring them collides.
- **Present chamfers:** BUSY (20.9, 28.0) → (21.2, 27.7), 0.424 mm; MISO_MCU (21.066, 28.4) → (21.6, 27.866),
  0.755 mm. The lanes are nested, so the chamfer lengths are free.
- **Measured** (`band5.py`):
  - **BUSY:** chamfer (20.49, 28.0) → (21.2, 27.29), 1.004 mm. Minimum clearance 0.25 mm (to MISO_MCU, the same as
    today) and 0.175 mm to GND via (20.0, 27.45) (unchanged).
  - **MISO_MCU:** run (10.0, 28.7) → (11.0, 28.7), step to (11.3, 28.4), chamfer (20.89, 28.4) → (21.6, 27.69),
    1.004 mm.
  - **MOSI:** step moved to (10.95, 29.2) → (11.35, 28.8). MISO's and MOSI's diagonals are 0.318 mm apart, centre
    line to centre line.
  - **Scratch `<p5rg>/v_band`:**
    - DRC 0 / 0 / 0 with parity; `check_r7` OK.
    - `route_check`: only "FAIL stale allowlist entry" ×2, for the two staircase entries. Both runs become
      extra_bends (information), exactly as F5 did for RADIO_SCK.
    - `scan5.py`: no new instance.
    - The tiny jogs A3/A4 stay; they are forced (§6.1).

**The records repeat the claims:**
- R7_VALIDATION P4-DOCS-01 "(BUSY and MISO_MCU measured as forced)", and the deviation-list rows A1, A2, A5 ("Why
  it cannot reasonably be removed").
- M3_R7 line 531 ("each with a measured reason that the gate re-checks (`nognd_audit`)").
- STATUS line 78.

**Why Major.**
- Gated M2 / §3 instances on critical nets have no valid exception, and the gate's OK depends on those entries.
- The deviation list would ask the owner to accept as forced three items that can be removed. This is the pattern of
  P4-RG-01, which was worked as Major.

**Counter-argument a skeptic may weigh.**
- All three are cosmetic: no DRC, DFM or electrical effect (Inference).
- The band "staircases" are a fan-in step plus an end chamfer on 10 mm lanes. The band edit changes the gate's
  classification more than the look, like F5's RADIO_SCK edit.
- The A5 reason does name "moves … the RXEN lane" as an alternative; it only never measured it.
- If graded Minor, the records still need correcting.

**Fix.**
1. In `r7_polish` (new stage or `band`): move RADIO_RXEN's lane onto x 23.8 and step QSPI_CLK 0.36 mm. Let
   `pour_trim` take the new finger, and update `TRIM_EXPECTED`. Delete A5. D12 closes with it.
2. For A1/A2, either apply the band edit and delete both entries, or reword `_BAND` to state they are fan-in steps
   that the gate's definition counts, and that they are not forced.
3. Correct R7_VALIDATION (P4-DOCS-01 text; A1, A2, A5, D12), M3_R7 line 531 and STATUS.

### P5-ROUTING_GEOMETRY-02 (Minor): non-critical leftover reasons that are not true or not measured; D13 removable; NRST length misquoted

**Requirement.** REQUIREMENTS M2 / AGENTS §3: "every counted non-critical leftover … carries a recorded measured
reason". The owner is asked to accept these as forced.

- **B1, CAM_EN B.Cu tiny jog** (LEFTOVERS line 269; "forced: x+y ≥ 122.63 vs ≤ 122.44"):
  - **Present:** (37.95, 85.16) → (37.1974, 85.16) → SW → (36.4333, 85.9241) → S 0.293 → SW → (36.05, 86.6) → W into
    via (35.75, 86.6).
  - The bounds are true for one 45° run only.
  - **Alternative:** (37.95, 85.16) → (36.9, 85.16) → (36.9, 85.75) → (36.05, 86.6). That is W, S, SW: no jog.
    Minimum clearance 0.209 mm (RAW_PROTECTED 0.4 mm track); today 0.184 mm (C71.1).
- **B2, CAM_FAULT_N In2 tiny jog** (line 273):
  - **Present:** y 103.9592 → 0.256 mm NE → y 103.7779.
  - The reason says "straight on at y 103.778 it passes SERVO4_MCU 0.15 mm apart". In fact the edge gap there is
    0.0012 mm: SERVO4_MCU's In2 run is at y 103.6268, centre lines 0.1511 mm apart.
  - Between the two bounds a single straight run exists at y 103.938, from (17.8304, 103.938) to
    (30.8998, 103.938). Both diagonals keep their lines (x − y = −86.1076; x + y = 134.8378).
  - Clearance 0.1612 mm to SERVO4_MCU and 0.162 mm to GND via (24.55, 104.475), both ≥ the house 0.16 mm.
- **D13, CAM_RX_WIRE In2 T-jog** (F5's own redraw; R7_VALIDATION says "removability not measured"):
  - One run at x 44.251, from (43.6626, 44.5468) → (44.251, 45.1352) to via (44.251, 63.1084), with the R100 branch
    squared at (44.251, 55.136).
  - Minimum 0.184 mm, to the same BAT_SW_SOURCE via (44.76, 61.1) as today.
- **Scratch `<p5rg>/v_jogs`** (all three):
  - DRC 0 / 0 / 0 with parity; `check_r7` OK; `check_actuators` OK.
  - `route_check`: only "FAIL stale LEFTOVERS entry" ×2 (CAM_EN, CAM_FAULT_N).
  - `scan5.py`: no new instance. Gone: 3 tiny jogs and the CAM_RX_WIRE staircase through its T.
- **"No path" entries** B8/B9 (CAM_5V_SENSE), B10 (LED_RED), B11 (SERVO2_MCU, 9 vias):
  - The only evidence is a search that cannot reproduce the existing route, so nothing measured explains the vias.
  - SERVO2_MCU, for example: the F.Cu hairpin exists to hop the C13.2 GND tie (−0.175 mm if straight on B.Cu at
    y 58.6), and no legal GND via spot lies within 1 mm of C13.2 north of that row (`gfit5.py`).
  - These facts, not "no path", are the reason to record.
- **NRST:** "47 mm / 4 vias" in LEFTOVERS line 338, R7_VALIDATION B24 and M3_R7 line 421; the board has 46.11 mm
  (`--routes`).

**Fix.**
1. Redraw CAM_EN, CAM_FAULT_N and CAM_RX_WIRE as above. Delete B1 and B2; mark D13 fixed.
2. Restate B8–B11 with the measured blocker.
3. Correct the NRST figure.
4. Update P4-DOCS-01's "both forced" and M3_R7 line 534.

### P5-ROUTING_GEOMETRY-03 (Minor): ARM1_SENSE no-GND exceptions quote a superseded resistance model; compliance costs 0.9 % and is DRC-clean

**Requirement.** AGENTS §3: a GND via within 1.5 mm of every layer change of a critical signal net, arming
included. Entries A17/A18 are the only exceptions on the arming net.

- **Measured.**
  - Scratch `<p5rg>/v_arm` adds GND vias 0.6/0.3 mm at (13.8, 97.525) and (13.9, 93.775), each 0.750 mm from its
    ARM1_SENSE via.
  - DRC 0 / 0 / 0 with parity; `check_r7` OK; `check_actuators` OK. `route_check`: only the two entries go stale.
  - `tools/dc_solve.py` (board stack-up), BAT_IN J1:1 → Q120:5–9 at a 0.1 mm grid: **4.55 → 4.59 mΩ** (+0.04 mΩ,
    +0.9 %). At 7.7 A the drop goes 35.0 → 35.3 mV and the loss 0.269 → 0.272 W. The In2 peak stays 6.17 / 6.16 A/mm
    at (10.45, 107.62).
- **The records.**
  - The allowlist reason (lines 197–202) and R7_VALIDATION A17 quote "3.91 → 3.95 mΩ", from the old 35 µm
    inner-copper model.
  - M3_R7 now quotes 4.55 mΩ as the baseline.
  - "A GND via there cuts the servo-current pour" overstates the effect: two antipads, +0.9 %.
- **Fix.** The owner's call, now with current numbers. Place the two vias (both arming-net §3 instances then comply),
  or restate the reason with 4.55 → 4.59 mΩ (+0.3 mV at 7.7 A).

### P5-ROUTING_GEOMETRY-04 (Minor): route_check residual soundness gaps

- (a) Only no-GND reasons are re-measured. Allowlist staircase / tiny-jog / short-segment reasons and LEFTOVERS
  reasons are not, and five were untrue (P5-01, P5-02).
- (b) Detour / extra_vias entries are keyed by the first pad's position, so they cannot go stale. Their quoted
  length, vias and search results can drift silently (NRST already). Store `len_mm` and `vias` in each entry and
  fail on a mismatch with `net_route()`.
- (c) `LEFTOVER_CATS` covers 4 of 14 hygiene categories; there are 0 instances of the other 10 on non-critical nets
  today.
- (d) P4-RG-02's S1–S5 are unchanged in code (§5.3; D18).

Fix: (b) and (c) are small code changes with tests. (a) can be partly automated for jog entries by a clearance probe
of the straight and non-tiny alternatives, as in §7. Otherwise keep it a review item and say so in M3_R7.

## 8. Notes (no finding)

- **F5 copper, checked segment by segment** (`diff.py`: 70 tracks and 16 vias added, 97 tracks and 16 vias
  removed):
  - Every new segment is on 0/45/90° and longer than its width, except RADIO_NRST's 0.141 mm segment wholly inside its
    via (D14).
  - New vias: PYRO1_CONT ×6 (0.5 mm), CAM_UART_OE ×4, NRST ×2, GND ×4. None dangles and none overlaps a same-net via.
  - Every PYRO1_CONT layer change has a GND via ≤ 1.5 mm.
- **The three "debris" jogs enlarged to 0.509 mm / 0.36 mm** (I2C1_SCL, LOGIC_ILIM, SERVO4_MCU) are forced; a
  straight run collides in each case:
  - I2C1_SCL at x 25.35: BOOT0 via (25.05, 62.85), −0.075 mm; at x 25.71 from the pin: U1.96, 0.059 mm.
  - LOGIC_ILIM: LOGIC_SOURCE_ST via (29.95, 30.55), 0.10 mm.
  - SERVO4_MCU at one x: CAM_FAULT_N track 0.110 mm or CAM_FAULT_N via −0.170 mm.
  - So the larger, non-tiny jog is the cleaner choice.
- **New pad entries (information):**
  - LED_YEL_A's corner moved inside LED2.1 (0.55 mm segment inside the pad: tidy);
  - SERVO3_MCU ends 0.41 mm off centre and 0.126 mm inside D121.4's edge;
  - PYRO1_CONT ends 0.18 mm off centre in R129.2 (recorded in C1).
- **D3 (CAM_5V jog into via (39.35, 104.55)) is removable.** One bend, horizontal to (38.725, 103.925) then 45° into
  the via centre, clears all other copper by ≥ 0.776 mm (R78.2). Its 0.425 mm segment is today 99.93 % covered by
  other CAM_5V copper.
- **D16 (CAM_TX_WIRE on In1, 3.67 mm):** the hop is boxed in on every other layer:
  - B.Cu: CAM_IO_3V3 at x 43.05;
  - In2: BAT_SW_SOURCE at x 42.76 and BAT_SW_RETURN at x 44.4;
  - F.Cu: CAM_RX_WIRE's diagonal from J9.3 crosses the direct path.
  - Removing it needs one of those moved (measured geometry; not routed). A non-critical UART wire.
- **BAT_IN In2 "neck" (10.45, 107.62)**, 6.17 A/mm in `dc_solve`: local crowding between the GND via (9.3, 107.6)
  and ACT_EN via (11.15, 107.61) antipads in a pour about 10 mm wide (`img/batin_in2.png`). It is not a conductor
  neck-down; IPC-2152 sizing is not judged here.
- **Radio band (A3/A4):** F5's "staircases 4 → 2" is partly definitional. RADIO_SCK has the same fan-in shape as
  BUSY/MISO_MCU; one of its runs passed 1 mm.

Images (`<p5rg>/img/`): `band.png`, `pyro1cont.png`, `uartoe.png`, `s2mcu.png`, `batin_in2.png`.

## Appendix A: every remaining instance on critical nets (final board)

Critical nets = route_check classes rf, pyro/arm, crystal, usb, spi, rfif and the power rails including GND.

### A1. Independent scan (`scan5.py`), critical nets

**crit_layer_change_no_gnd** (11): RADIO_RXEN via (23.8, 39.45) [gnd_via 2.23, by tracks]; RADIO_NRST via (9.3, 50.0) [gnd_via 3.178, by tracks]; ARM1_SENSE via (14.55, 97.55) [gnd_via 7.885, by tracks]; ARM1_SENSE via (14.55, 94.15) [gnd_via 5.112, by tracks]; PYRO1_GATE via (20.45, 92.4) [gnd_via 2.928, by tracks+pad/body]; RADIO_BUSY via (9.4, 28.2) [gnd_via 1.649, by tracks]; RADIO_BUSY via (10.0, 49.5) [gnd_via 2.596, by tracks]; RADIO_MOSI via (9.4, 29.2) [gnd_via 1.649, by tracks]; RADIO_DIO1 via (10.0, 50.5) [gnd_via 3.569, by tracks]; RADIO_MISO_MCU via (10.0, 28.7) [gnd_via 2.11, by tracks]; RADIO_MOSI_MCU via (9.4, 48.5) [gnd_via 1.709, by tracks]

**staircase_any** (4): GND B.Cu (35.1, 28.4) [segs [0.672, 0.554, 0.22, 1.344, 0.953]]; RADIO_BUSY F.Cu (9.4, 28.2) [segs [1.2, 0.283, 10.1, 0.424]]; RADIO_MISO_MCU F.Cu (21.6, 27.866) [segs [0.755, 10.166, 0.424, 0.6]]; CAM_5V B.Cu (33.8, 103.925) [segs [4.5, 0.884, 0.425, 1.344]]

**jog_tiny** (8): GND B.Cu (36.1634, 28.0083) [mid 0.22, off 0.155, kinds ['plain', 'T']]; GND B.Cu (31.3, 53.7) [mid 0.283, off 0.2, kinds ['via', 'via']]; 3V3_RADIO F.Cu (35.1, 20.85) [mid 0.43, off 0.304, kinds ['pad', 'plain']]; RADIO_BUSY F.Cu (10.6, 28.2) [mid 0.283, off 0.2, kinds ['plain', 'plain']]; QSPI_CLK F.Cu (22.85, 44.65) [mid 0.424, off 0.3, kinds ['plain', 'plain']]; RADIO_MISO_MCU F.Cu (10.6, 28.7) [mid 0.424, off 0.3, kinds ['plain', 'plain']]; CAM_5V B.Cu (38.925, 104.55) [mid 0.425, off 0.301, kinds ['plain', 'via']]; SW_NODE B.Cu (21.32, 35.25) [mid 0.4, off 0.283, kinds ['plain', 'plain']]

**short (open, not inside a pad/via)** (2): SW_NODE B.Cu (21.32, 35.25) [len 0.4, w 0.6, inside open]; SW_NODE B.Cu (17.92, 35.65) [len 0.5657, w 0.6, inside open]

**inside_pad** (2): QSPI_NCS F.Cu (26.97, 39.7) [pad R10.1, len 0.22]; VLOGIC B.Cu (18.0, 32.35) [pad U2.2, len 0.5]

**through_pad** (10): 3V3 F.Cu (12.049, 76.5412) [pad LS120.1]; GND F.Cu (26.0, 91.125) [pad Q124.2]; ARM1_SENSE F.Cu (17.28, 94.15) [pad R180.1]; PYRO1_OUT F.Cu (30.58, 90.0) [pad R173.1]; GNSS_RF_ANT F.Cu (12.85, 2.3) [pad L30.2]; GNSS_RF_ANT F.Cu (12.85, 2.3) [pad D30.1]; RAW_ACT B.Cu (8.7, 110.68) [pad Q121.5]; USB_DM F.Cu (5.7, 75.55) [pad J3.A7]; QSPI_NCS F.Cu (26.75, 40.45) [pad R10.1]; RADIO_RF_ANT F.Cu (31.54, 2.3) [pad D31.1]

**acute (wedge exposed)** (0): none

**end_pour_only** (1): RAW_ACT F.Cu (5.3, 82.17) [seg_len 1.7]

**redundant_track_copper** (1): CAM_5V B.Cu (38.925, 104.55) [len 0.425, end [39.35, 104.55]]

**via_ring_overlap** (3): GND via (32.79, 4.15) [other [32.99, 3.6], centres 0.5852]; GND via (11.4, 3.6) [other [11.6, 4.15], centres 0.5852]; GND via (30.29, 4.15) [other [30.09, 3.6], centres 0.5852]

**neck** (5): GND B.Cu (34.35, 78.05) [widths [0.2, 0.25], into_pad True, narrow_len 0.44]; BAT_IN F.Cu (9.8, 40.85) [widths [0.3, 0.5], into_pad True, narrow_len 1.4]; RAW_PROTECTED F.Cu (12.6, 40.35) [widths [0.3, 0.5], into_pad True, narrow_len 1.4]; RAW_PROTECTED B.Cu (27.35, 27.85) [widths [0.3, 0.5], into_pad True, narrow_len 1.175]; CAM_INPUT_LIMITED B.Cu (39.65, 87.6) [widths [0.3, 0.8], into_pad True, narrow_len 0.7]

**via_on_track_body** (1): GND via (6.85, 40.5) [layers ['F.Cu']]

**jog_across_via, tiny** (1): RADIO_RXEN F.Cu>B.Cu via (23.8, 39.45) mid 0.318 off 0.225

**pad_offcentre** (61; 8 end within 0.05 mm of the pad edge): 3V3 B.Cu C13.1 off 0.283 edge 0.05; GND F.Cu R81.2 off 0.354 edge 0.05; BAT_IN F.Cu C88.1 off 0.25 edge 0.05; RAW_PROTECTED B.Cu TP81.1 off 0.99 edge 0.05; USB_LIMITED B.Cu U10.6 off 0.5 edge 0.05; USB_LIMITED B.Cu U11.7 off 0.525 edge 0.0; VLOGIC B.Cu U2.2 off 0.55 edge 0.0; CAM_IO_3V3 B.Cu C93.1 off 0.483 edge 0.025

### A2. Gate (`route_check --report`) information categories, critical nets

**u_turn** (18): 3V3 B.Cu (36.94, 52.65) [path_mm 16.32]; GND F.Cu (14.3, 59.0) [path_mm 6.621]; GND F.Cu (16.35, 45.95) [path_mm 6.556]; GND F.Cu (6.31, 79.625) [path_mm 3.378]; GND B.Cu (13.7, 80.6) [path_mm 6.084]; RADIO_NRST B.Cu (9.3, 50.0) [path_mm 32.132]; RADIO_NSS B.Cu (9.3, 47.5) [path_mm 23.249]; PYRO1_CONT F.Cu (26.83, 87.9) [path_mm 3.61]; RADIO_TXEN B.Cu (31.13, 20.15) [path_mm 22.719]; RADIO_BUSY B.Cu (10.0, 49.5) [path_mm 30.575]; RADIO_DIO1 B.Cu (10.0, 50.5) [path_mm 33.889]; RAW_ACT F.Cu (10.4, 64.67) [path_mm 5.604]; RAW_ACT B.Cu (10.0, 90.78) [path_mm 31.294]; USB_LIMITED In2.Cu (29.1, 40.55) [path_mm 7.401]; RADIO_MISO_MCU B.Cu (10.7, 48.5) [path_mm 30.426]; USB_DM F.Cu (6.88, 74.55) [path_mm 7.28]; VCAP2 F.Cu (14.3, 58.5) [path_mm 11.067]; VLOGIC F.Cu (28.505, 29.85) [path_mm 13.158]

**extra_bends** (12): 3V3 F.Cu (14.5839, 75.5964) [seglens [1.336, 1.59, 5.457, 0.29]]; RADIO_NSS F.Cu (9.4, 30.2) [seglens [1.8, 0.849, 10.2, 1.697]]; PYRO1_CONT F.Cu (35.78, 60.65) [seglens [4.6, 5.657, 4.4, 1.556]]; RADIO_MOSI F.Cu (9.4, 29.2) [seglens [1.2, 0.566, 10.232, 1.086]]; RADIO_SCK F.Cu (10.0, 29.7) [seglens [1.05, 0.707, 9.848, 1.417]]; RAW_PROTECTED In2.Cu (19.15, 103.27) [seglens [10.041, 1.0, 9.758, 1.2, 0.566]]; USB_LIMITED B.Cu (16.8, 81.55) [seglens [3.394, 12.6, 13.435, 10.5, 0.566, 5.6]]; USB_LIMITED B.Cu (29.1, 40.55) [seglens [0.5, 1.131, 3.0, 2.404, 3.2]]; USB_LIMITED B.Cu (31.6, 34.55) [seglens [3.2, 1.131, 2.4, 0.424]]; 3V3A B.Cu (38.35, 50.15) [seglens [2.758, 8.76, 0.509, 2.496]]; SW_NODE B.Cu (18.32, 36.05) [seglens [2.2, 1.131, 0.4, 1.697]]; CAM_IO_3V3 B.Cu (44.55, 33.75) [seglens [4.7, 2.121, 6.2, 1.414]]

**short_layer_hop** (9): 3V3 F.Cu (27.35, 44.25) [hop_mm 2.93]; 3V3 In2.Cu (30.63, 31.3417) [hop_mm 2.404]; RADIO_NSS B.Cu (23.2, 17.3) [hop_mm 2.196]; PYRO1_CONT In2.Cu (35.78, 58.85) [hop_mm 1.8]; VBUS F.Cu (10.8, 79.95) [hop_mm 2.317]; 3V3A B.Cu (35.5, 76.54) [hop_mm 2.505]; USB_DP B.Cu (8.9, 74.75) [hop_mm 1.6]; CAM_5V F.Cu (43.3, 33.425) [hop_mm 2.414]; CAM_5V B.Cu (39.35, 104.55) [hop_mm 0.95]

**passes_through_pad** (10): 3V3 F.Cu (12.049, 76.5412) [pad LS120.1]; GND F.Cu (26.0, 91.125) [pad Q124.2]; ARM1_SENSE F.Cu (17.28, 94.15) [pad R180.1]; PYRO1_OUT F.Cu (30.58, 90.0) [pad R173.1]; GNSS_RF_ANT F.Cu (12.85, 2.3) [pad L30.2]; GNSS_RF_ANT F.Cu (12.85, 2.3) [pad D30.1]; RAW_ACT B.Cu (8.7, 110.68) [pad Q121.5]; USB_DM F.Cu (5.7, 75.55) [pad J3.A7]; QSPI_NCS F.Cu (26.75, 40.45) [pad R10.1]; RADIO_RF_ANT F.Cu (31.54, 2.3) [pad D31.1]

**segment_inside_pad** (2): QSPI_NCS F.Cu (26.97, 39.7) [pad R10.1, len_mm 0.22]; VLOGIC B.Cu (18.0, 32.35) [pad U2.2, len_mm 0.5]

**width_change_junction** (29): 3V3 F.Cu (36.0, 82.43) [widths [0.2, 0.25], at via]; 3V3 F.Cu (33.1, 81.73) [widths [0.2, 0.25], at T]; 3V3 B.Cu (12.6, 59.5) [widths [0.2, 0.3], at via]; 3V3 B.Cu (31.1, 54.5) [widths [0.25, 0.3], at via]; 3V3 B.Cu (30.17, 65.1) [widths [0.2, 0.25], at via]; 3V3 B.Cu (30.1, 55.32) [widths [0.2, 0.25], at T]; 3V3 B.Cu (27.35, 44.25) [widths [0.25, 0.3], at via]; GND F.Cu (24.55, 89.275) [widths [0.2, 0.45], at via]; GND B.Cu (31.5, 47.1) [widths [0.2, 0.25], at via]; GND B.Cu (33.95, 78.55) [widths [0.2, 0.25], at free]; GND B.Cu (34.35, 78.05) [widths [0.2, 0.25], at free]; GND B.Cu (31.5, 53.5) [widths [0.2, 0.25], at via]; PYRO1_OUT F.Cu (30.58, 90.0) [widths [0.2, 0.3], at T]; PYRO1_BUS F.Cu (16.17, 95.36) [widths [0.4, 1.0], at T]; BAT_IN F.Cu (9.3, 40.15) [widths [0.3, 0.5], at via]; BAT_IN F.Cu (9.8, 40.85) [widths [0.3, 0.5], at free]; RAW_PROTECTED F.Cu (12.6, 40.35) [widths [0.3, 0.5], at free]; RAW_PROTECTED B.Cu (26.225, 26.725) [widths [0.25, 0.5], at T]; RAW_PROTECTED B.Cu (15.7, 35.75) [widths [0.4, 0.6], at T]; RAW_PROTECTED B.Cu (27.35, 27.85) [widths [0.3, 0.5], at free]; RAW_PROTECTED B.Cu (15.075, 36.375) [widths [0.25, 0.6], at T]; VBUS F.Cu (11.325, 82.05) [widths [0.2, 0.3], at via]; USB_LIMITED B.Cu (24.125, 61.625) [widths [0.2, 0.4], at T]; 3V3A B.Cu (37.82, 76.94) [widths [0.2, 0.3], at T]; 3V3A B.Cu (35.9632, 69.9393) [widths [0.2, 0.25], at via]; 3V3A B.Cu (35.5, 76.54) [widths [0.2, 0.3], at via]; 3V3A B.Cu (38.35, 50.15) [widths [0.25, 0.3], at T]; CAM_5V B.Cu (39.35, 104.55) [widths [0.3, 0.8], at via]; CAM_INPUT_LIMITED B.Cu (39.65, 87.6) [widths [0.3, 0.8], at free]

**power_via_no_gnd** (36): 3V3 via (44.035, 77.92) [gnd_mm 2.639]; 3V3 via (29.9, 43.625) [gnd_mm 1.858]; 3V3 via (35.1, 45.025) [gnd_mm 1.5]; 3V3 via (7.9, 80.4) [gnd_mm 3.415]; 3V3 via (35.73, 27.3417) [gnd_mm 2.071]; 3V3 via (16.3, 90.525) [gnd_mm 1.88]; 3V3 via (38.1719, 37.8191) [gnd_mm 3.474]; 3V3 via (30.4, 78.25) [gnd_mm 1.992]; 3V3 via (30.63, 31.3417) [gnd_mm 2.329]; 3V3 via (28.33, 40.4) [gnd_mm 2.275]; 3V3 via (12.5, 89.2) [gnd_mm 5.838]; 3V3 via (36.94, 52.65) [gnd_mm 2.59]; 3V3 via (21.9, 96.125) [gnd_mm 6.564]; RAW_ACT via (13.1, 75.97) [gnd_mm 4.314]; RAW_ACT via (12.6, 81.27) [gnd_mm 1.939]; BAT_IN via (9.2, 36.05) [gnd_mm 2.812]; RAW_PROTECTED via (18.05, 102.87) [gnd_mm 6.695]; RAW_PROTECTED via (15.7, 32.4) [gnd_mm 4.433]; RAW_PROTECTED via (13.6, 37.85) [gnd_mm 1.9]; RAW_PROTECTED via (14.0, 33.3) [gnd_mm 5.59]; RAW_PROTECTED via (37.85, 54.7) [gnd_mm 2.362]; VBUS via (14.0, 73.23) [gnd_mm 2.746]; VBUS via (10.8, 79.95) [gnd_mm 3.356]; VBUS via (11.0, 76.35) [gnd_mm 2.201]; VBUS via (11.325, 82.05) [gnd_mm 2.067]; USB_LIMITED via (29.1, 40.55) [gnd_mm 1.762]; USB_LIMITED via (25.8, 37.15) [gnd_mm 2.623]; 3V3A via (31.1, 50.0) [gnd_mm 2.927]; 3V3A via (32.6, 50.2) [gnd_mm 3.154]; VCAP2 via (16.0, 62.4) [gnd_mm 2.236]; CAM_5V via (43.3, 33.425) [gnd_mm 1.935]; CAM_5V via (41.3, 32.425) [gnd_mm 2.387]; CAM_5V via (43.25, 35.625) [gnd_mm 2.869]; VLOGIC via (16.5, 33.15) [gnd_mm 3.634]; VLOGIC via (31.67, 35.5) [gnd_mm 2.306]; VLOGIC via (13.6, 36.35) [gnd_mm 2.989]

### A3. Allowlisted and recorded instances on critical nets (gate)

- staircase 2: RADIO_BUSY (9.4, 28.2), RADIO_MISO_MCU (10.0, 28.7). Both are A1/A2: removable (P5-01).
- tiny_jog 4: RADIO_BUSY (9.4, 28.2), RADIO_MISO_MCU (10.0, 28.7) (A3/A4: forced); QSPI_CLK (22.85, 45.95) (A5:
  removable, P5-01); SW_NODE (20.52, 36.05) (A6: forced).
- short_segment 2: SW_NODE (21.32, 35.25), (17.92, 35.65) (A7/A8: forced).
- critical_via_no_gnd 10: A9–A18 (§6.1). Gate-blind: PYRO1_GATE → TP122 (20.45, 92.4) (D8).
- detour 9 / extra_vias 10 on critical nets: A19–A37 (§6.1).

## Appendix B: reproduce

```
cd <p5rg>      # r7.kicad_pcb = m3.kicad_pcb (c6fe595c…), p4.kicad_pcb (636a6bdc…), r6.kicad_pcb; proj5/ = project files
PY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
CLI=/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli; R=<repo>
$PY scan5.py r7.kicad_pcb out/s5_r7.json; $PY scan5.py p4.kicad_pcb out/s5_p4.json     # independent scan
python3 newinst.py out/s5_p4.json out/s5_r7.json                                        # new since pass 4
$PY -I p4scan.py r7.kicad_pcb out/s4_r7.json; $PY -I p4extra.py r7.kicad_pcb; $PY -I rc_allpairs.py r7.kicad_pcb
$PY -I scan_p2.py r7.kicad_pcb r6.kicad_pcb out/scan2_r7.json                          # 958 (595)
$PY -I $R/tools/route_check.py r7.kicad_pcb --report out/rc_r7.json --routes
$PY -I probe.py r7.kicad_pcb 0.0 0.025; $PY -I probe_drc.py r7.kicad_pcb 0.0 0.025; $PY -I nudge.py r7.kicad_pcb 0.0 0.01
$PY jogs5.py; $PY qclk.py; $PY rx2.py; $PY band5.py; $PY cfn.py; $PY d3.py; $PY s2m.py; $PY gfit5.py r7.kicad_pcb
for v in base jogs arm qspi band; do rm -rf v_$v; cp -R proj5 v_$v; $PY edit5.py r7.kicad_pcb v_$v $v
  $CLI pcb drc --severity-all --schematic-parity --format json -o v_$v/drc.json v_$v/m3.kicad_pcb
  $PY -I $R/tools/route_check.py v_$v/m3.kicad_pcb; $PY -I $R/tools/check_r7.py v_$v/m3.kicad_pcb
  python3 $R/m3_design/check_actuators.py v_$v/m3.kicad_pcb; done
$PY -I $R/tools/dc_solve.py v_base/m3.kicad_pcb --net BAT_IN --source J1:1 --sink Q120:5,6,7,8,9 --grid 0.1   # 4.55
$PY -I $R/tools/dc_solve.py v_arm/m3.kicad_pcb  --net BAT_IN --source J1:1 --sink Q120:5,6,7,8,9 --grid 0.1   # 4.59
$PY gs5.py v_qspi/m3.kicad_pcb 23.8,39.45                                               # RXEN: still no spot
```
