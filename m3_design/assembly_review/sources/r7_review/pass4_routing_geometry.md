# R7 review pass 4: routing geometry and style (whole board)

Reviewer: independent, read-only. Dimension: routing geometry and style, every track and via on all four layers,
copper inherited from R6 included. Acceptance criterion: CLEAN ROUTING (AGENTS.md §3 plus the owner's list in
REQUIREMENTS M2).

- **Board reviewed:** `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
  `636a6bdc7234586a659741a3da921335a47197648c29cd9612c8374733847650` (the fix-pass-3 final board named in
  `docs/R7_VALIDATION.md` and `fix3_F4_handoff.md`; unchanged at the end of this review). 1,836 tracks, 694 vias,
  no arcs, 4,522.4 mm of track (F.Cu 711, B.Cu 821, In2 298, In1 6 tracks).
- **Comparison boards:** pass-3 board `7660620c…7c9c` (1,946 tracks, 709 vias) and committed R6 `3b215ba`
  (+18 mm in y).
- **Gate on this board:** `tools/check.sh` exit 0: DRC 0, unconnected 0, schematic parity 0, ERC 0; metadata/3D OK;
  silkscreen 0; "R7 CAD contract: OK"; "routing hygiene: 0 failing, 42 allowlisted, 0 stale allowlist entries: OK";
  actuator safety contract OK; fit OK. `tools/test_route_check.py`: 27 tests OK.
- Nothing in the repository was modified except this file. All work was on scratch copies in
  `<scratch>/p4rg/`.

## 1. Verdict

Fix pass 3 did what it said for the pass-3 routing findings. The F4 copper (SWCLK, SWDIO, PYRO1_CONT reroutes, the
pyro-block and pad-entry corners, the L1.2 node, the dead-copper sweep) is geometrically clean. On the final board
my own scan finds **no off-angle segment, no segment under 50 µm, no fold-back, no crossing without a node, no
duplicate or collinear-overlapping copper, no overlap-only joint, no off-centre via joint, no dangling end or via,
and no open short segment on a critical net** other than the three allowlisted ones. Against the pass-3 board it
introduces no new instance of any gated category. The floating 3V3 chain and the six protruding pour stubs of P3-03
are gone, and the C17.1, PYRO1_GATE_N and GND pyro corners are redrawn as asked.

What is left:

- **One Major (P4-ROUTING_GEOMETRY-01): the PYRO1_GATE_N allowlist entry is false on the final board.**
  - The entry says there is no legal GND via spot within 1.5 mm of the pyro gate-drive layer change at (23.0, 88.33).
  - F4's SWCLK reroute freed one: a 0.5/0.3 mm GND via at (22.9, 89.555), 1.23 mm away, or 0.6/0.3 mm at
    (22.85, 89.63), 1.31 mm away.
  - Both spots pass the project's own placement rules: `r7_route.ViaCheck` plus every extra rule of
    `r7_hygiene.gnd_vias`.
  - On a refilled scratch copy with either via added: DRC 0 at every severity, unconnected 0, parity 0;
    `check_r7`, `check_actuators` and `fit_check` all OK.
  - `route_check` then reports the PYRO1_GATE_N entry as stale.
  - Cause: the build runs the GND-via search in `r7_hygiene.py`, before `r7_polish.py` changed the copper. Nothing
    re-measures the "no legal spot" reasons after that.
- **Two Minors:**
  - **P4-02: route_check soundness gaps.** The gate still cannot see:
    - an exposed acute angle that ties with a buried one at the same node (ACT_GATE at Q121.4);
    - jogs and staircases whose corner holds a T, a via or a pad (four critical tiny jogs; a GND staircase buried
      in its pour; a CAM_5V jog into a via);
    - a redundant pour-buried tail on a needed run (RAW_ACT, 3.17 mm);
    - a critical layer change to a pad (TP122);
    - overlapping same-net vias.
  - **P4-03: the information-only critical-net instances.** R7_VALIDATION left their one-by-one review open for
    this pass. They are judged in §6 and Appendix A: accept them, apart from five cheap tidy-ups listed there.

No Critical finding. Nothing found is open, shorted or below a DRC rule.

## 2. Method

Scripts (scratch `p4rg/`, KiCad 10.0.6 Python, boards loaded read-only, never saved; scratch copies saved only
under `p4rg/base`, `p4rg/viatest`, `p4rg/viatest6`):

| Script | What it does |
|---|---|
| `p4scan.py` | **Independent scan written for this pass.** Per (layer, net) node clusters at 1 µm; every node typed (plain / T / via / pad). Off-angle; length classes (< 50, < 100, < 200 µm, < own width), each tagged inside-via, inside-pad or open; angles of **every** branch pair at every node, with the wedge-apex test at pads and vias; **per-segment jog test at any node type**; staircases; any-angle same-net copper contact between segments with no shared node and no T; same-net slits < 0.1 mm; every track end typed (joined / T / via / via off-centre / pad / overlap-only / pour-only / dangling); stubs by iterative leaf pruning, with a pour contact not counted as a connection; same-net via–via overlap; vias on a passing track's body; critical layer changes (track **or pad** layers) against the nearest GND via and plated GND hole; width changes per node type; pad entries; U-turns |
| `p4extra.py` | What a plain-node chain grammar cannot see: alternating runs followed through T, via and pad nodes; jogs across a via (a short approach segment whose other neighbour is parallel to the continuation on another layer); the length of a pour-ended run that lies inside its own fill |
| `rc_allpairs.py` | Scratch copy of `tools/route_check.py` whose angle test checks every branch pair instead of the smallest one, all else unchanged |
| `probe.py`, `nudge.py` | Pass-3 GND-via spot probe (0.025 mm grid, board rules, bare TP 1.0 mm, Pyro D, paste/mask, GND-pad 0.15 mm) and existing-GND-via move search, rerun **on the final board** with no margin |
| `projfit.py` | The project's own legality test for a new GND via: `r7_route.ViaCheck.ok()` plus `r7_hygiene.gnd_vias`'s extras (bare TP 1.02 mm, J2 0.528 mm, Pyro D 0.52 mm incl. fills, heavy-current corridors), on 0.025 and 0.05 mm grids |
| `addvia.py` | Adds a GND via to a scratch copy, refills natively (`ZONE_FILLER`), saves the copy; then `kicad-cli pcb drc --severity-all --schematic-parity`, `check_r7`, `route_check`, `check_actuators`, `fit_check` on that copy |
| `gap.py`, `infill.py`, `island.py`, `ctx.py`, `padent.py`, `origin.py`, `diff.py`, `newinst.py` | Edge gaps between nets; track copper outside its own fill; pour islands; local listings; pad-entry characterisation; origin (R6 / pass-3 / F4) of instances; track/via diff and new-instance diff against the pass-3 board |
| `render.py` (+ zone fills), `r.sh` | Vector renders, `p4rg/img/*.png` |

I also ran the gate's own `route_check.py --report --routes` and the pass-2 reviewers' `scan.py` unchanged on the
final board.

## 3. Pass-3 findings in this dimension: closure check

| ID | Pass 3 (skeptics) | R7_VALIDATION disposition | Verified on the final board |
|---|---|---|---|
| P3-RG-01 | Major → Minor (3/3) | Fixed | **(a) Closed in code.** `route_check.scan()` lines 1301–1308 test every inner A,B,A triple; `test_tiny_jog_inside_a_longer_run` added. The gate counts 13 tiny jogs (5 critical, all allowlisted), the same 13 my scan finds at plain nodes. **Residual:** jogs at T, via or pad corners are still untested (P4-02). **(b) Closed.** `short_segment` gated (line 1144). My scan: no open short segment on a critical net except the three allowlisted ones (RADIO_NRST 0.141 mm; SW_NODE 0.4 and 0.566 mm). The PYRO1_GATE_N hook is now one run at x 21.9 into R126.1, 0.3 mm off centre inside the 1.38 mm pad. The C17.1 entry is square into the pad centre (14.5, 59.88). The GND pyro corner is T (23.9677, 90.7) → 45° 0.523 mm → 0.362 mm into R128.2's centre; its middle segment is just over the 0.5 mm tiny-jog limit. **(c) Closed for the two moves:** RXEN (21.2, 30.45) to GND via (19.71, 30.51) 1.491 mm; GNSS_RXD_MCU (2.2, 51.5) to (3.26, 50.44) 1.499 mm. Both entries removed. The new QSPI_CLK reason is true (measured: 0.15 mm to the LED_YEL via at x 22.85; 0.196 mm to RXEN after a 0.354 mm step; 0.25 / 0.45 mm with the 0.3 mm step). **But** a new false reason exists: P4-01. **(d) Closed.** M3_R7's count table equals the gate output (334 / 0 / 42) |
| P3-RG-02 | Minor | Recorded deviation, 11 entries | **Not right as recorded.** `probe.py` (0.025 mm, no margin) and `nudge.py` (no margin) on the final board confirm no legal spot for 10 of the 11. For ARM1_SENSE ×2 the only spots are in the BAT_IN heavy corridor, which matches the reason. **PYRO1_GATE_N now has legal spots** (P4-01) |
| P3-RG-03 | Minor | Fixed | **Closed.** `dead(pour_islands=True)` makes each island a terminal and adds `_pour_stubs`. The floating 3V3 In2 chain (18.7, 51.9)–(19.6, 51.6) and all six protruding stubs are removed (track diff against `7660620c`). My leaf pruning finds one remaining pour-ended run: RAW_ACT F.Cu via (12.6, 81.27) → (5.3, 82.17). It is a needed run, but 3.17 mm of it lies inside its own fill (P4-02, gap S3) |
| P3-RG-04 | Minor | Partly fixed; review of information-only instances open for the next pass | **L1.2 node closed** (`img/l1.png`). Both 0.6 mm diagonals leave the pad centre (26.1, 33.0). The vertical to plane via (26.4, 36.6) T's off the C8.1 diagonal inside the pad: a 45° wedge, apex inside L1.2's copper. C9.1 joins the vertical with an E / NE 0.707 / E jog, forced by USB_LIMITED's via (25.8, 37.15): a straight run at y 36.6 would pass that via at 0.55 mm centre-to-line against the 0.75 mm it needs. The second via and its hop are gone. **One-by-one review done in this pass** (§6, P4-03) |
| P3-RG-05 | Minor | Fixed (tool, documents) | **Closed.** AGENTS §3 and M2 state the GND-via scope (critical signal nets) and that hygiene is gated on critical nets. `power_via_no_gnd` is information (36). Residual scope gap: pad-only layer changes (P4-02, gap S4) |

## 4. Counts

### 4.1 Gate (`tools/route_check.py --report --routes`) on the final board

334 instances, failing 0, allowlisted 42, stale 0. Allowlisted: critical_via_no_gnd 11, extra_vias 10, detour 9,
tiny_jog 5, staircase 4, short_segment 3.

Information only (all nets / critical nets):
- width_change_junction 30 / 29
- pad_end_offcentre 89 / 63
- segment_inside_pad 2 / 2
- passes_through_pad 10 / 10
- extra_bends 33 / 10
- u_turn 26 / 18
- short_layer_hop 20 / 8
- power_via_no_gnd 36

All per-net lengths and via counts quoted in the allowlist reasons equal `--routes`. For example: GNSS_RESET_N
59.34 mm / 2 vias, RADIO_NRST 85.44 / 4, RADIO_TXEN 25.17 / 2, VCAP1 6.71 for 1.37, VCAP2 12.67 for 3.00,
RAW_PROTECTED 143.53 / 7, VLOGIC 66.87 / 5, VBUS 42.49 / 6.

### 4.2 Independent scan (`p4scan.py`), all instances (critical nets), final board vs pass-3 board

| Category | Pass-3 board | **Final board** | Notes on the final board |
|---|---|---|---|
| off_angle | 0 | **0** | |
| short < 50 µm | 0 | **0** | |
| short 50–100 µm | 15 (8) | 14 (7) | **Open: 3, all non-critical** (CAM_EN 61 µm, LED_YEL_A 99 µm, CAM_RX_WIRE 58 µm); 11 wholly inside a via |
| short 100–200 µm | 29 (18) | 20 (12) | Open: RADIO_NRST (allowlisted), SERVO2_MCU, SERVO3_MCU, CAM_5V_SENSE; 16 inside a via |
| short ≥ 0.2 mm but < own width | 10 (10) | 7 (7) | Open: SW_NODE ×2 (allowlisted); 5 inside a via |
| fold_back | 0 | **0** | |
| acute (every branch pair) | 13 (7) | 12 (6) | All wedges inside pad/via copper **except one pair at ACT_GATE Q121.4** (non-critical net; P4-02, gap S1) |
| crossing_without_node | 0 | **0** | |
| contact_without_node (any angle) | 62 (44) | 54 (36) | 46 inside a same-net pad or via. 8 open: the two allowlisted jogs (RADIO_NRST, SW_NODE); USB_LIMITED's T at U11.7's edge (§6); five short corners on non-critical nets |
| same-net slit < 0.1 mm | 9 (6) | 9 (6) | All at short corners or inside pads; GND (36.27, 28.01) is buried in the pour |
| end overlap-only / via off-centre / dangling | 0 / 0 / 0 | **0 / 0 / 0** | |
| end pour-only | 22 (22) | **1 (1)** | RAW_ACT F.Cu (5.3, 82.17) (gap S3) |
| leaf stubs (pour contact not a connection) | 46 (46) | 5 (5) | The five segments of that one RAW_ACT run |
| tiny jog (any node type) | 17 (9) | 17 (9) | 13 at plain nodes = the gate's 13. **4 critical at T/via/pad nodes the gate cannot see** (gap S2) |
| jog, not tiny | 49 (27) | 47 (26) | |
| staircase (plain-node runs) | 5 (5) | 4 (4) | = the gate's 4, allowlisted (radio band) |
| staircase through a T or via (`p4extra.py`) | – | 3 places | GND C94.2 (buried in pour), CAM_5V into via (39.35, 104.55), CAM_FAULT_N In2 (non-critical) (gap S2) |
| collinear unmerged / width steps | 0 / 3 | **0** / 3 | Width steps are pad-entry necks into U9 / U7 |
| width change: plain / T / via / pad | 5 / 11 / 15 / 16 | 5 / 10 / 15 / 18 | Plain ones are pad-entry necks (≤ 1 mm to the pad) |
| dangling via | 0 | **0** | |
| same-net via–via overlap | 3 | 3 | RF strip GND pairs at 0.585 mm centres (gap S5) |
| via on a passing same-net track | 39 (24) | 36 (23) | |
| critical layer change, no GND via ≤ 1.5 mm | 15 | **12** | The gate's 11 plus PYRO1_GATE → TP122 (pad layer; gap S4) |
| power layer change, no GND via | 39 | 36 | = gate |
| pad end off-centre / through a pad / inside a pad | 90 / 10 / 2 | 89 (63) / 10 / 2 | §6 |
| u_turn | 25 (17) | 26 (18) | |

**New since the pass-3 board** (instances with no counterpart within 0.05 mm on `7660620c`, `newinst.py`). None is
in a gated category.
- Two buried pad contacts: GND at C160.2, and RAW_PROTECTED at D9.1.
- Two non-tiny jogs:
  - 3V3 C9.1 branch: middle 0.707 mm, offset 0.5 mm;
  - GND pyro corner: middle 0.523 mm, offset 0.37 mm.
- PYRO1_GATE_N's 0.3 mm off-centre entry into R126.1.
- The 3V3 via moved to (41.0, 77.92).
- Eight SWCLK/SWDIO vias (a non-critical net).
- Three U-turn chains, revealed when dead branches were removed.
- 3V3 via (26.4, 36.6) on the C9.1 T.
- Two width changes at pads.

### 4.3 Pass-2 reviewers' `scan.py` (unchanged) on the final board

969 instances (595 on critical nets), identical to the F4 handoff's figure.

## 5. route_check audit (soundness against its stated categories) and allowlist verification

### 5.1 Category by category

| Category (docstring) | Implementation | Sound? |
|---|---|---|
| off_angle, micro_segment, short_segment | Per segment (lines 1140–1154) | Yes. My scan agrees exactly |
| acute_angle, fold_back | Per node, **only the smallest-angle branch pair** (lines 1215–1238) | **No** (S1). With a tie, or a smaller buried pair, an exposed acute is missed. Shown by `rc_allpairs.py` |
| staircase, tiny_jog, extra_bends, u_turn | Chains through `plain()` nodes only (lines 1107, 1255–1323) | **Partly** (S2). Runs whose corner holds a T, via or pad are not tested; staircase is a §3 rule gated on every net |
| dead_copper | Biconnected blocks with pour islands as terminals; `_pour_stubs` removes **whole** runs back to the first junction (lines 585–662) | **Partly** (S3). A needed run's redundant tail inside its own pour is not seen |
| dangling_via | Copper layers per via | Yes |
| critical_via_no_gnd | Layers with a **track end** in the via (line 742) | **Partly** (S4). A layer change to a pad is not counted |
| collinear_unmerged, duplicate, collinear/side-by-side overlap, crossing, overlap-only joint, via_offcentre_joint, neck_down, track_loop | Pairwise per (layer, net), node and end typing | Yes for tracks. **No via–via test** (S5): same-net overlapping vias are not "duplicate or overlapping copper" to the tool |
| detour, extra_vias | Net copper vs octile MST; layer-changing via count | Yes as documented (weak for multi-pad trees, as stated) |
| pour_sliver, pour_finger | Fill opening, raster reach | Not re-audited in depth (RF dimension). On this board 0 / 0 |
| ALLOWLIST / stale test | An entry fails only if it matches no instance | **Cannot detect a false reason** (S6). An entry keeps matching while its measured reason goes out of date (P4-01) |

### 5.2 Allowlist: every entry checked

| Entries | Claim checked | Result |
|---|---|---|
| Band ×8 (staircase ×4, tiny_jog ×3, short_segment ×1) | Vias in columns x 9.4 / 10.0 on 0.5 mm rows (y 27.2…30.2); lanes at 0.4 mm pitch (y 27.6…29.6); BAT_SW_RETURN 0.175 mm from RADIO_NSS's lane; 0.075 mm at 0.4 mm row spacing | **True**. Measured 0.1751 mm at (22.0–23.2, 29.6) vs BAT_SW_RETURN (21.0–22.2, 29.925). The "staircases" are fan-in chamfers at each end of 7.8–10.8 mm lanes (`img/band.png`) |
| QSPI_CLK tiny_jog | 0.15 mm to the LED_YEL via at x 22.85; 0.196 mm to RXEN (x 23.575, y 31.45–39.225) after a 0.354 mm step; 0.25 / 0.45 mm with 0.3 mm | **True** (geometry recomputed; QSPI_CLK–RXEN 0.2500 mm measured). The choice is a preference for 0.25 mm over a DRC-legal 0.196 mm, and the reason now states both numbers |
| SW_NODE ×3 | C7.2/C9.2 gap 1.22 mm (pad edges y 34.705 / 35.925), centre line y 35.16–35.48; 0.75 mm from vias (18.7, 35.28) and (19.5, 35.2); no one-bend route | **True**. A single 45° line through the gap needs 0.636 mm (0.45√2) of clearance from both pad corners (corner sums 56.18 and 57.32), which leaves no feasible line. The 0.566 mm drop out of C5.1 is needed because the run must sit at y ≥ 36.03 below the vias and C5.1's pad ends at y 35.92 (`img/swnode.png`) |
| critical_via_no_gnd: 8 radio band / corridor, RXEN (23.8, 39.45) | Nearest GND 1.65–3.57 mm; no legal spot; no nudge | **True on the final board.** Distances equal my scan; `probe.py` NONE and `nudge.py` NONE for all 8 |
| critical_via_no_gnd: ARM1_SENSE ×2 | Legal spots only in the J1 → Q120 BAT_IN corridor | **True.** Probe: (13.85, 97.525) and (13.975, 93.75), both flagged heavy |
| critical_via_no_gnd: PYRO1_GATE_N (23.0, 88.33) | "No legal GND via spot within 1.5 mm … pass-3 0.025 mm search found none … no existing GND via can move"; a 1.03 mm spot at (22.45, 87.455) refused for 0.10 / 0.114 mm to C127.2 / R127.2 | **False** (P4-01). The (22.45, 87.455) numbers are true (measured 0.1001 / 0.1136 mm), but project-legal spots exist at 1.23–1.31 mm |
| detour / extra_vias, R7 interface (GNSS_RESET_N, RADIO_DIO1 ×2, RADIO_NRST ×2, RADIO_NSS, RADIO_RXEN, RADIO_TXEN) | Lengths, vias and raster-search results | **True as evidenced.** `--routes` equals the quoted numbers. The search outputs in F4's scratch (`fx3/det/*.txt`) show exactly the quoted alternatives: DIO1 47.95 mm / 2 vias with a 39.8 mm In2 run ending at (28.05, 17.75), inside the strip; RXEN 43.76 / 2 with an 18.2 mm In2 run at x 19.6–20.65; NSS 40.57 / 3; NRST 51.29 / 4; GNSS_RESET_N 39.32 / 2 with F.Cu at x 14.8; TXEN 12.16 / 0 through the keep-out. U31.9 (28.59, 9.05) and U31.19 (31.13, 18.95) are on opposite sides; `U31_KEEPOUT` covers the body on all layers. I did not rerun the raster router |
| detour GNSS_LNA_EN, GNSS_VCC_RF | U30.13 / U30.14 are F.Cu pads on the aft row (y 10.2); both leave 1.9 mm aft to vias at y 8.3, outside the module body (y ≥ 8.53), and return on B.Cu | **True** |
| extra_vias PYRO1_CONT, ARM1_SENSE, QSPI_IO2 | 4 / 4 / 3 vias; search finds no fewer | **True as evidenced** (`fx3/det`: 44.2 / 4, 51.79 / 4, 31.85 / 3). PYRO1_CONT: every layer change ≤ 1.5 mm from a GND via (not in my 12) |
| detour VCAP1, VCAP2 | 5.81 / 2 and 10.75 / 1 at best | **True as evidenced** |
| VBUS ×2, RAW_PROTECTED, VLOGIC | Pad lists and layers | **True.** VBUS: J3.A4B9 / B4A9 on F.Cu 4.8 mm apart, C83 F; C28, D4, R9, U10 ×2 on B. RAW_PROTECTED: 3 F (U9.6, C82.1, D9.1) + 9 B. VLOGIC: 2 F + 8 B |

## 6. Findings

### P4-ROUTING_GEOMETRY-01 (Major): the PYRO1_GATE_N "no legal GND via spot" allowlist entry is false; the §3 rule can be met

**Requirement.**
- AGENTS.md §3: "put a GND via within 1.5 mm (centre to centre) of every layer change of a critical signal net
  (… pyro and arming …)". REQUIREMENTS M2 adopts it.
- M2 also says "each exception is an allowlist entry in the tool with a measured reason". The R7 acceptance needs
  "the M2 routing check (`tools/route_check.py`) OK".

**Instance.** PYRO1_GATE_N changes F.Cu → In2 at via (23.0, 88.33), 0.6/0.3 mm. The nearest GND via is 1.815 mm
away. `route_check.ALLOWLIST` (tools/route_check.py lines 184–187) excuses it with `_NOGND` (lines 149–152), which
claims three things:
- `r7_hygiene.gnd_vias` found no legal spot;
- "the pass-3 review's 0.025 mm search found none either";
- no existing GND via can move to serve it.

**Measured on the final board** (`img/pyrogaten.png`):
- `probe.py` (pass-3 rules, 0.025 mm, no margin): legal 0.5/0.3 mm at (22.925, 89.53), 1.202 mm; 0.6/0.3 mm at
  (22.875, 89.58), 1.256 mm.
- `projfit.py`, the project's own rules: `r7_route.ViaCheck.ok()` with its +0.02 mm margins, plus
  `r7_hygiene.gnd_vias`'s bare-TP 1.02 mm, J2 0.528 mm, Pyro D 0.52 mm including pyro fills, and heavy corridors.
  - 0.025 mm grid: 0.5 mm at **(22.9, 89.555), 1.229 mm**; 0.6 mm at (22.85, 89.605), 1.284 mm.
  - On `gnd_vias`'s own 0.05 mm grid: 0.5 mm at (22.9, 89.58), 1.254 mm; **0.6 mm at (22.85, 89.63), 1.309 mm**.
    `gnd_vias` tries 0.6 mm first at this reach, so it would have placed this via.
- The spot lies in open GND F.Cu pour.
  - Nearest copper to the 0.5 mm spot: PYRO1_GATE_N In2 track 0.20 mm. It is a GND via, so Pyro G (0.3 mm) does
    not apply.
  - The pyro bus, igniter and drain are well beyond Pyro D's 0.5 mm.
- **Scratch copies.**
  - Applied: `p4rg/viatest` (0.5 mm at (22.9, 89.555)) and `p4rg/viatest6` (0.6 mm at (22.85, 89.63)). Each was
    refilled natively.
  - `kicad-cli pcb drc --severity-all --schematic-parity`: **0 violations, 0 unconnected, 0 parity** for both.
  - The base copy, refilled the same way, also gives 0.
  - `tools/check_r7.py`: "R7 CAD contract: OK".
  - `m3_design/check_actuators.py`: OK. `tools/fit_check.py`: OK.
  - `tools/route_check.py`: "FAIL stale allowlist entry (matches nothing): ('critical_via_no_gnd', 'PYRO1_GATE_N',
    'via', (23.0, 88.33))". The board then has 10 critical layer changes without a GND via.
- **Cause.**
  - On the pass-3 board the spot was occupied by the old SWCLK route: a via at (22.85, 89.85) and F.Cu
    (22.85, 89.45)–(23.85, 88.45).
  - F4's `swd` stage moved SWCLK out of the pyro block.
  - The GND-via search runs only in `r7_hygiene.py` (stage `gnd_vias`, line 1735), before `r7_polish.py`.
    `r7_polish`'s `gnd_moves` stage only nudges the two vias and adds the C160.2 via.
  - The `_NOGND` text was carried over from the pass-3 board. The gate cannot tell: an entry goes stale only when it
    stops matching an instance, not when its reason stops being true.
- **The records repeat it.**
  - R7_VALIDATION P3-ROUTING_GEOMETRY-02 / P3-ROUTING_QUALITY-01 "11 critical layer changes … no legal site", under
    "Recorded deviations (owner acceptance pending)".
  - M3_R7 §"Routing hygiene", allowlist row "PYRO1_GATE_N … the same search".
  - The owner would be asked to accept as forced a deviation that is not forced.

**Why Major.**
- An AGENTS §3 rule instance on a pyro (critical) net is unmet.
- Its only exception rests on a false measured reason.
- The gate's OK, which the acceptance condition relies on, depends on that entry.

**Counter-argument a skeptic may weigh.** PYRO1_GATE_N is a slow, RC-filtered gate drive
(docs/M3_ACTUATOR_MERGE.md). The return-path benefit of moving from 1.815 to about 1.23–1.31 mm is negligible
(Inference, not measured). Pass-3 skeptics graded the analogous P3-01(c) Minor, but there the gain was 53–56 µm at
the threshold. Here the rule goes from unmet to met, and the claim of impossibility is simply wrong.

**Fix (small).**
1. In `r7_polish.py` (or a stage after the last copper change), add the GND via:
   - 0.6/0.3 mm at (22.85, 89.63), the spot `gnd_vias` would choose;
   - or 0.5/0.3 mm at (22.9, 89.555).
2. Delete the PYRO1_GATE_N allowlist entry.
3. Re-run `gnd_vias` after `r7_polish`'s copper stages, or move it there. Better: add a check, in the build or in
   `route_check`, that runs the project-legal spot search for every allowlisted critical_via_no_gnd entry and fails
   if a spot exists.
4. Correct R7_VALIDATION (P3-RG-02 / P3-RQ-01: 10, not 11), M3_R7's allowlist row and STATUS. Drop "the pass-3
   review's 0.025 mm search found none" from `_NOGND`, or date it.

### P4-ROUTING_GEOMETRY-02 (Minor): route_check soundness gaps that still hide gated-category instances

Each gap with its instances on this board. All instances are cosmetic: no DRC, DFM or electrical effect.

- **S1. Acute angles: only the smallest pair per node is tested.**
  - Code: route_check.py lines 1215–1222 keep the first minimum; line 1236 tests only its wedge.
  - Instance: ACT_GATE B.Cu at Q121.4 (5.9, 102.4) (`img/actgate.png`). Three tracks meet at the pad centre.
    - The E 0.25 mm track from via (7.7, 102.2) and the NE 0.25 mm diagonal from TP121's vertical (7.08, 101.22)
      meet at 45°. Their wedge apex is at (6.202, 102.275), **0.012 mm outside the pad's right edge (x 6.19)**.
    - The other 45° pair (with the 0.2 mm N track from C120) is buried.
  - `rc_allpairs.py` (identical except all pairs): "FAIL acute_angle ACT_GATE B.Cu (5.9, 102.4)". It is the only
    new failure.
  - acute_angle is a §3 rule gated on every net. The geometry is inherited from R6, cleaned of its micro-segments in
    fix pass 2.
  - Tidy-up: bring TP121's vertical straight down to the E track at (7.08, 102.4) as a square T.
- **S2. Jogs and staircases are tested only along plain-node chains.**
  - Code: `plain()` line 1107; chains lines 1255–1281. A corner that holds a T branch, a via or a pad breaks the
    run.
  - Critical-net instances the gate cannot see (`p4scan.py` jog test and `p4extra.py`):
    - **GND B.Cu C94.2 → LED1 run (35.1, 28.4):** E 0.672 / NE 0.554 / E 0.22 / NE 1.344 / E 0.953 mm. That is five
      alternating segments, four under 1 mm: **a staircase by the gate's own definition** (a §3 rule, gated on
      every net), split by R103.2's T at (36.3833, 28.0083). Its 0.22 mm middle segment is also a tiny jog (offset
      0.155 mm). R6 copper. It lies wholly inside the GND B.Cu fill (`infill.py`: 0.000 mm² outside), so it does not
      show in the finished copper (`img/gnd_c94.png`).
    - **CAM_5V B.Cu (33.8, 103.925):** E 4.5 / SE 0.884 / E 0.425 / via (39.35, 104.55) / SE 1.344 mm (0.8 mm wide,
      to C75.1). Staircase by the grammar, and a 0.425 mm tiny jog (offset 0.30 mm) into the via. Fix-pass-2 copper,
      visible (`img/cam5v.png`), though its copper merges with the 0.8 mm track.
    - **3V3_RADIO F.Cu FB31.2 (35.1, 20.85):** 0.43 mm E between two NE diagonals through the pad. In effect a
      pad-exit stub; acceptable.
    - **GND B.Cu (31.3, 53.7) → (31.5, 53.5):** a 0.283 mm 45° step into via (31.5, 53.5) between tracks at y 53.7
      and y 53.5. R6.
  - Non-critical: CAM_FAULT_N In2 (15.22, 91.40), 0.816 / 11.929 / 0.842 / 1.234 mm through a via. Two
    0.8 mm doglegs between long runs. It is a staircase by the grammar, and staircase is gated on every net.
- **S3. Pour-ended runs: only whole runs are tested.**
  - Code: `_pour_stubs` lines 637–661.
  - Instance: RAW_ACT F.Cu via (12.6, 81.27) → (11.4, 80.07) → (11.4, 79.37) → (9.8, 79.37) → (7.0, 82.17) →
    (5.3, 82.17), 0.2 mm wide (`img/rawact.png`). The run is needed: it ties the RAW_ACT sense line (In2/B.Cu) to
    the R6_RAW_ACT_F pour around J124.2.
    - But **3.17 mm of its centre line lies inside that fill**. The 1.7 mm tail to (5.3, 82.17) ends touching
      nothing but the pour (`p4extra.py`).
    - That is P3-03's "stub ending in a pour", left because the removal test is applied to the whole run back to
      the via.
    - The U-shape north is forced by VBUS's F.Cu hop via (10.8, 79.95).
    - R6 copper.
  - Tidy-up: end the diagonal just inside the pour edge (about (7.5, 81.67)) and delete the tail.
- **S4. Critical layer changes: only track ends count.**
  - Code: line 742.
  - Instance: PYRO1_GATE, R126.2 F.Cu → TP122 B.Cu via (20.45, 92.4) in TP122's pad, nearest GND via 2.93 mm. The
    rule text says "every layer change", but this is a test-pad stub that carries no through-signal. Inference: the
    §3 purpose does not apply.
  - Count it and allowlist it with that reason, or write the pad exemption into M2 / AGENTS §3.
- **S5. No same-net via–via overlap test.** Three GND pairs in the RF strip sit 0.585 mm apart with 0.6 mm rings,
  so the rings overlap by 15 µm. They are DRC-legal: hole to hole 0.285 mm ≥ 0.25 mm. The pairs are
  (32.79, 4.15)/(32.99, 3.6), (11.4, 3.6)/(11.6, 4.15) and (30.29, 4.15)/(30.09, 3.6).
- **S6. The stale test cannot catch a false reason.** See P4-01.
- **Records.** M3_R7 says "On critical nets, every gated category is 0 except the 42 allowlisted entries". That is
  true only within the gate's grammar; it is false for the S2 / S3 instances above.
- `tools/test_route_check.py` has no case for:
  - a tied acute pair;
  - a jog or staircase through a T or via;
  - a pour tail on a needed run;
  - a pad-only layer change.

**Fix.**
1. Test every branch pair for acute_angle and fold_back.
2. Run the alternation and jog tests across T, via and pad nodes (choose the continuation with the right heading),
   or add a per-segment jog test like `p4scan.py`'s.
3. In `_pour_stubs`, trim a run's portion inside its own island beyond the first pour contact.
4. Count pad layers in `critical_transitions`.
5. Optionally, a same-net via-overlap check.
6. Add a test for each.
7. Then redraw, or allowlist with measured reasons: ACT_GATE, the C94.2 staircase (or delete that run if the pads'
   pour joints suffice; it is buried), CAM_5V, CAM_FAULT_N, and the RAW_ACT tail.

### P4-ROUTING_GEOMETRY-03 (Minor): one-by-one judgement of the information-only critical-net instances (P3-RG-04's open item)

R7_VALIDATION leaves the one-by-one review of these information-only instances "for the next pass" ("not yet judged
one by one"). I judged each instance (Appendix A lists them all; origin from `origin.py`, `padent.py`). My
recommendation: **accept** all but the five tidy-ups below, as recorded deviations.

- **U-turns (18):**
  - 6 are the R7 interface lanes (RADIO_BUSY / DIO1 / MISO_MCU / NRST / NSS corridor, RADIO_TXEN round U31): topology,
    already allowlisted detours.
  - 12 are R6: VCAP2 (allowlisted); the U12/C100 3V3 feed loop at (36.94, 52.65), 16.32 mm (P3-ROUTING_QUALITY-05,
    recorded); VLOGIC, USB_DM, USB_LIMITED, RAW_ACT ×2, PYRO1_CONT divider; and GND ×4.
  - The GND U-turns lie inside the GND pour. For example, U10.2 → Q123.2 is 0.000 mm² outside the fill.
  - Accept.
- **Extra-bend runs (10):** long alternating runs, not sawtooth: band lanes, USB_LIMITED / RAW_PROTECTED / 3V3A /
  CAM_IO_3V3 trees, SW_NODE (allowlisted). Accept.
- **Short layer hops (8):** R6 3V3 ×2, 3V3A, CAM_5V, USB_DP, VBUS; the fix-pass-2 CAM_5V via doubling (0.95 mm,
  deliberate); RADIO_NSS (23.2, 17.3) into the strip. Accept.
- **Tracks through a same-net pad (10):** the three RF ones (L30.2, D30.1, D31.1) are deliberate stub-free shunts;
  the other seven are R6 (LS120.1, Q124.2, R180.1, R173.1, R10.1, Q121.5, J3.A7). Accept.
- **Segments inside a pad (2):** QSPI_NCS in R10.1, 0.22 mm; VLOGIC in U2.2, 0.5 mm. Both R6. VLOGIC: see the
  tidy-ups.
- **Width changes at junctions (29):** all are a narrower branch at a T, a layer change at a via, or a pad-entry neck
  (the five "free" ones are ≤ 1 mm from the pad they neck into). None is a neck-down inside one conductor. Accept.
- **Off-centre pad ends (63):**
  - 54 end at least 0.06 mm inside the pad copper, entering on or near a pad axis. Accept.
  - **9 end within 0.05 mm of the pad edge:** VLOGIC U2.2 ×2 (0.00 mm, R6); USB_LIMITED U11.7 (0.00 mm, fix-pass-2
    copper); CAM_IO_3V3 C93.1 (0.025); USB_LIMITED U10.6, GND R81.2, BAT_IN C88.1 (fix pass 2), 3V3 C13.1,
    RAW_PROTECTED TP81.1 (0.05 each).
- **Power-rail layer changes without a GND via (36):** plane-fed rails. Accept as documented (P3-RG-05).

**Tidy-ups recommended** (cheap; none is a defect):
1. **USB_LIMITED at U11.7** (`img/usblim.png`). The 0.25 mm branch from (30.4, 26.95) ends at (30.4, 27.85): on
   the pad's right edge, and on the 0.4 mm feed 0.1 mm short of its corner node (30.5, 27.85). End it at the corner
   node or at the pad centre.
2. **VLOGIC at U2.2 / C7 / C6** (R6). A 0.5 mm segment inside U2.2 from its edge (18.0, 32.35); two tracks ending
   on the pad boundary; five contacts without a node inside U2.2 / C7.1 / C6.1 (Appendix A). Redraw the node.
3. **PYRO1_CONT** (new F4 copper). F.Cu diagonal → 0.45 mm W → via (29.93, 61.55) → In2 diagonal parallel to the
   F.Cu one, offset 0.318 mm: a tiny jog in plan across the via (`p4extra.py`). Re-align the via onto one of the
   diagonals if clearance allows. Not measured.
4. **RADIO_RXEN** (fix pass 2). F.Cu lane x 23.575 → 0.318 mm 45° → via (23.8, 39.45) → B.Cu at x 23.8: a 0.225 mm
   jog across the via. It came from F1 moving the lane for the 0.25 mm clock gap. The via could sit on the lane if
   RAW_PROTECTED / QSPI_IO3 allow. Not measured.
5. **The four T/via jogs and the ACT_GATE wedge** in P4-02.

**Fix:** record this judgement in R7_VALIDATION, closing P3-RG-04's open item, and do the tidy-ups or list them as
accepted deviations.

## 7. Notes (no finding)

- **F4 copper, checked line by line.** All 66 added tracks are on 0/45/90° headings and none is shorter than its
  width. Each new via:
  - SWD: 8 vias, a non-critical net, so no GND-via rule;
  - PYRO1_CONT: 4 vias, each within 1.5 mm of a GND via;
  - SERVO1_MCU: 1 via.

  SWCLK's F.Cu U-turn (24.7, 50.95) → (29.4, 45.6) → (33.25, 52.15), 16.8 mm, and the two B.Cu dives are the
  raster router's way round U1's NE corner and the 3V3 / PULLPIN F.Cu runs at y 56.05–56.5. SWDIO's 2.58 mm B.Cu
  hop (30.85 → 33.43, 69.65) crosses the In2 PYRO1_GATE_N (x 31.9) and SERVO3_MCU (x 32.85) lanes. All of these are
  P3-REQUIREMENTS-01 detour residue, on a non-critical net (requirements / routing-quality dimension).
- **In1 copper:** 6 tracks, NRST (36.4–38.5, 65.05–67.2) and CAM_TX_WIRE (42.1–44.9, 42.9–44.0), both R6. F4
  removed SWCLK's 19.5 mm In1 run.
- **Pass-3 information items unchanged by F4:** BAT_IN's two parallel tracks offset 0.05 mm, meeting in C96.1; the
  SW_NODE U2.5 → C5.1 0.4 mm track at x 17.9 (pad centres x 18.0 / 17.92). Both R6, buried in pads.
- **Not re-assessed:** IPC-2152 sizing (DC solves in M3_R7), pour sliver/finger thresholds (RF dimension).

## 8. Images (scratch `p4rg/img/`)

`pyrogaten.png` (P4-01: the PYRO1_GATE_N via and the legal GND via spot in open GND pour), `actgate.png` (S1),
`gnd_c94.png` (S2 hidden staircase, buried), `cam5v.png` (S2), `rawact.png` (S3), `usblim.png`, `l1.png`,
`swnode.png`, `band.png`, `swclk.png`, `gnd_u10.png`, `v3u.png`.

## Appendix A: every remaining instance on critical nets (final board, `p4scan.py`)

Critical nets are the route_check classes: RF, pyro/arm, HSE, USB data, SPI/QSPI/IMU_CS/radio SPI, other
RADIO_*/GNSS_*, and the power rails including GND. "inside via" / "inside pad" short segments lie wholly within
same-net via or pad copper. Gate-allowlisted instances are included.

**crit_layer_change_no_gnd** (12)
ARM1_SENSE via (14.55, 94.15) GND 5.112 mm; ARM1_SENSE via (14.55, 97.55) GND 7.885 mm; PYRO1_GATE via (20.45, 92.4) GND 2.928 mm; PYRO1_GATE_N via (23, 88.33) GND 1.815 mm; RADIO_BUSY via (9.4, 28.2) GND 1.649 mm; RADIO_BUSY via (10, 49.5) GND 2.596 mm; RADIO_DIO1 via (10, 50.5) GND 3.569 mm; RADIO_MISO_MCU via (10, 28.7) GND 2.11 mm; RADIO_MOSI via (9.4, 29.2) GND 1.649 mm; RADIO_MOSI_MCU via (9.4, 48.5) GND 1.709 mm; RADIO_NRST via (9.3, 50) GND 3.178 mm; RADIO_RXEN via (23.8, 39.45) GND 2.23 mm

**staircase** (4)
RADIO_BUSY F.Cu (9.4, 28.2) segs 1.2/0.283/10.1/0.424; RADIO_MISO_MCU F.Cu (10, 28.7) segs 0.6/0.424/10.166/0.755; RADIO_NRST F.Cu (10, 27.7) segs 0.6/0.141/7.8/0.707; RADIO_SCK F.Cu (10, 29.7) segs 0.6/0.707/10.298/1.417

**jog_tiny** (9)
3V3_RADIO F.Cu (35.1, 20.85) mid 0.43 off 0.304 nodes pad/plain; CAM_5V B.Cu (38.925, 104.55) mid 0.425 off 0.301 nodes plain/via; GND B.Cu (31.3, 53.7) mid 0.283 off 0.2 nodes via/via; GND B.Cu (36.1634, 28.0083) mid 0.22 off 0.155 nodes plain/T; QSPI_CLK F.Cu (22.85, 44.65) mid 0.424 off 0.3 nodes plain/plain; RADIO_BUSY F.Cu (10.6, 28.2) mid 0.283 off 0.2 nodes plain/plain; RADIO_MISO_MCU F.Cu (10.6, 28.7) mid 0.424 off 0.3 nodes plain/plain; RADIO_NRST F.Cu (10.6, 27.7) mid 0.141 off 0.1 nodes plain/plain; SW_NODE B.Cu (21.32, 35.25) mid 0.4 off 0.283 nodes plain/plain

**jog** (26)
3V3 B.Cu (25.2, 36.6) mid 0.707 off 0.5 nodes plain/plain; 3V3 F.Cu (34.5, 81.73) mid 0.99 off 0.7 nodes plain/plain; 3V3 F.Cu (35.1, 24.6) mid 0.891 off 0.63 nodes plain/plain; 3V3 F.Cu (36.5, 51.65) mid 0.622 off 0.44 nodes T/plain; 3V3A B.Cu (36.4, 60.86) mid 0.509 off 0.36 nodes plain/plain; BAT_IN B.Cu (9.845, 53.375) mid 0.545 off 0.385 nodes plain/via; CAM_5V B.Cu (34.23, 31.6) mid 0.6 off 0.424 nodes plain/plain; CAM_5V B.Cu (38.3, 103.925) mid 0.884 off 0.625 nodes plain/plain; GND B.Cu (19.03, 89) mid 0.542 off 0.383 nodes pad/plain; GND B.Cu (19.05, 47.1717) mid 0.778 off 0.55 nodes via/plain; GND F.Cu (23.9677, 90.7) mid 0.523 off 0.37 nodes T/plain; GND B.Cu (35.7717, 28.4) mid 0.554 off 0.392 nodes plain/plain; GND B.Cu (38.2863, 27.058) mid 0.908 off 0.642 nodes plain/plain; GND B.Cu (42.05, 53.18) mid 0.523 off 0.37 nodes plain/plain; PYRO1_CONT F.Cu (26.83, 87.9) mid 0.522 off 0.522 nodes pad/plain; QSPI_IO0 F.Cu (13.5, 41.9) mid 0.5 off 0.354 nodes plain/plain; RADIO_MOSI F.Cu (10.6, 29.2) mid 0.566 off 0.4 nodes plain/plain; RADIO_NSS F.Cu (10.6, 30.2) mid 0.849 off 0.6 nodes plain/plain; RADIO_SCK F.Cu (10.6, 29.7) mid 0.707 off 0.5 nodes plain/plain; RAW_ACT B.Cu (11.2, 106.78) mid 0.849 off 0.6 nodes plain/plain; RAW_PROTECTED F.Cu (33.75, 46.9) mid 0.5 off 0.354 nodes plain/plain; RAW_PROTECTED B.Cu (38.5, 84.175) mid 0.566 off 0.4 nodes plain/plain; USB_LIMITED B.Cu (28.7, 46.55) mid 0.566 off 0.4 nodes plain/plain; VBUS B.Cu (13.05, 78.65) mid 0.5 off 0.354 nodes plain/plain; VLOGIC B.Cu (27.825, 28.55) mid 0.99 off 0.7 nodes plain/via; VLOGIC F.Cu (32.27, 29.2) mid 0.849 off 0.6 nodes plain/plain

**short_lt100** (7)
GND B.Cu (26.98, 62.58) 0.099 mm (w 0.25) inside via; GND B.Cu (28.15, 44.25) 0.099 mm (w 0.2) inside via; GND B.Cu (33.95, 78.55) 0.0707 mm (w 0.25) inside via; GND B.Cu (36.4, 76.54) 0.1 mm (w 0.2) inside via; GND B.Cu (37.25, 25.35) 0.0707 mm (w 0.25) inside via; RAW_PROTECTED F.Cu (25.85, 40.6) 0.1 mm (w 0.4) inside via; VCAP1 In2.Cu (16.9, 44.3) 0.0707 mm (w 0.3) inside via

**short_lt200** (12)
3V3 F.Cu (27.9, 56.5) 0.2 mm (w 0.25) inside via; 3V3 F.Cu (28.33, 40.2) 0.2 mm (w 0.25) inside via; 3V3 F.Cu (43.85, 77.92) 0.185 mm (w 0.25) inside via; ARM1_SENSE F.Cu (18.18, 91.5) 0.2 mm (w 0.2) inside via; GND B.Cu (19.05, 47.35) 0.1783 mm (w 0.2) inside via; GND F.Cu (27.65, 29.85) 0.2 mm (w 0.2) inside via; GND B.Cu (31.5, 47.1) 0.1435 mm (w 0.2) inside via; PYRO1_GATE_N F.Cu (31.9, 59.23) 0.2 mm (w 0.2) inside via; RADIO_NRST F.Cu (10.6, 27.7) 0.1414 mm (w 0.15) OPEN; SPI1_SCK F.Cu (22.35, 65.55) 0.1414 mm (w 0.2) inside via; USB_LIMITED F.Cu (17.725, 83.15) 0.2 mm (w 0.3) inside via; VBUS B.Cu (14, 73.23) 0.2 mm (w 0.25) inside via

**short_lt_w** (7)
3V3 F.Cu (27.35, 44.25) 0.2062 mm (w 0.25) inside via; RAW_PROTECTED F.Cu (38.05, 54.5) 0.2828 mm (w 0.4) inside via; SW_NODE B.Cu (17.92, 35.65) 0.5657 mm (w 0.6) OPEN; SW_NODE B.Cu (21.32, 35.25) 0.4 mm (w 0.6) OPEN; VBUS In2.Cu (11, 79.75) 0.2828 mm (w 0.4) inside via; VLOGIC B.Cu (13.3, 36.35) 0.3 mm (w 0.5) inside via; VLOGIC B.Cu (27.125, 29.25) 0.22 mm (w 0.5) inside via

**acute** (6)
3V3 B.Cu (26.4, 33.3) 45.0 at pad wedge inside copper; ARM1_SENSE F.Cu (17.28, 92.4) 45.0 at pad wedge inside copper; CAM_INPUT_LIMITED B.Cu (40.3, 90.1) 45.0 at pad wedge inside copper; GNSS_ANT_SRC B.Cu (3.8, 12.75) 45.0 at pad wedge inside copper; HSE_OUT B.Cu (23.2, 53.9) 45.0 at via wedge inside copper; IMU_CS B.Cu (36.5, 80.77) 45.0 at pad wedge inside copper

**contact_without_node** (36)
3V3 B.Cu (26.25, 33.15) overlap 0.1757 mm inside pad/via; 3V3 F.Cu (27.35, 44.1469) overlap 0.0437 mm inside pad/via; 3V3 F.Cu (27.9154, 39.7563) overlap 0.2088 mm inside pad/via; 3V3 B.Cu (41.565, 53.885) overlap 0.2076 mm inside pad/via; 3V3_GNSS F.Cu (12.675, 21.815) overlap 0.1162 mm inside pad/via; BAT_DAMP F.Cu (2.4, 34.95) overlap 0.05 mm inside pad/via; BAT_IN B.Cu (8.25, 54.5) overlap 0.3882 mm inside pad/via; BAT_IN B.Cu (8.2625, 54.4875) overlap 0.3939 mm inside pad/via; BAT_IN B.Cu (11.8812, 33.3562) overlap 0.1823 mm inside pad/via; CAM_5V B.Cu (39.1375, 104.55) overlap 0.125 mm inside pad/via; CAM_5V B.Cu (39.1375, 104.55) overlap 0.125 mm inside pad/via; CAM_5V B.Cu (40.2, 32.4375) overlap 0.175 mm inside pad/via; CAM_5V B.Cu (43.275, 34.525) overlap 0.15 mm inside pad/via; CAM_INPUT_LIMITED B.Cu (40.5, 91) overlap 0.2343 mm inside pad/via; GND B.Cu (31.4282, 47.1) overlap 0.0815 mm inside pad/via; GND B.Cu (33.925, 78.525) overlap 0.1543 mm inside pad/via; GND F.Cu (34.94, 28.88) overlap 0.12 mm inside pad/via; GND B.Cu (36.45, 76.54) overlap 0.1 mm inside pad/via; GND B.Cu (39.575, 77.5) overlap 0.09 mm inside pad/via; GNSS_LNA_EN B.Cu (12.17, 12.18) overlap 0.04 mm inside pad/via; PYRO1_OUT F.Cu (28.775, 91.73) overlap 0.25 mm inside pad/via; RADIO_NRST F.Cu (10.65, 27.65) overlap 0.0086 mm OPEN; RAW_ACT B.Cu (9.005, 86.995) overlap 0.1859 mm inside pad/via; RAW_PROTECTED F.Cu (14.25, 31.2) overlap 0.1 mm inside pad/via; RAW_PROTECTED B.Cu (35.7, 85.7475) overlap 0.155 mm inside pad/via; RAW_PROTECTED B.Cu (38.3375, 83.2) overlap 0.075 mm inside pad/via; SW_NODE B.Cu (17.91, 35.625) overlap 0.4461 mm inside pad/via; SW_NODE B.Cu (21.52, 35.25) overlap 0.2 mm OPEN; USB_LIMITED B.Cu (16.6812, 81.6688) overlap 0.0141 mm inside pad/via; USB_LIMITED B.Cu (30.45, 27.85) overlap 0.225 mm OPEN; VLOGIC B.Cu (18, 29.55) overlap 0.25 mm inside pad/via; VLOGIC B.Cu (18, 31.825) overlap 0.4 mm inside pad/via; VLOGIC B.Cu (18, 31.825) overlap 0.45 mm inside pad/via; VLOGIC B.Cu (18.975, 31.8) overlap 0.4 mm inside pad/via; VLOGIC B.Cu (20.7125, 31.825) overlap 0.2695 mm inside pad/via; VLOGIC B.Cu (27.015, 29.25) overlap 0.28 mm inside pad/via

**slit_lt_0.1** (6)
3V3 F.Cu (33.1, 81.865) slit 0.045 mm; 3V3_RADIO F.Cu (35.315, 20.85) slit 0.03 mm; BAT_IN B.Cu (9.5725, 53.375) slit 0.045 mm; GND B.Cu (31.4, 53.6) slit 0.0578 mm; GND B.Cu (36.2734, 28.0083) slit 0.0199 mm; RAW_PROTECTED B.Cu (38.3375, 83.2) slit 0.025 mm

**end_pour_only** (1)
RAW_ACT F.Cu (5.3, 82.17) (segment 1.7 mm)

**leaf_stub** (5)
RAW_ACT F.Cu (7, 82.17) to (5.3, 82.17) 1.7 mm; RAW_ACT F.Cu (9.8, 79.37) to (7.0, 82.17) 3.96 mm; RAW_ACT F.Cu (11.4, 79.37) to (9.8, 79.37) 1.6 mm; RAW_ACT F.Cu (11.4, 80.07) to (11.4, 79.37) 0.7 mm; RAW_ACT F.Cu (12.6, 81.27) to (11.4, 80.07) 1.697 mm

**via_overlap_same_net** (3)
GND via (11.4, 3.6) and (11.6, 4.15), 0.585 mm apart; GND via (30.29, 4.15) and (30.09, 3.6), 0.585 mm apart; GND via (32.79, 4.15) and (32.99, 3.6), 0.585 mm apart

**collinear_widthstep** (3)
BAT_IN F.Cu (9.8, 40.85) 0.3/0.5; CAM_INPUT_LIMITED B.Cu (39.65, 87.6) 0.3/0.8; RAW_PROTECTED F.Cu (12.6, 40.35) 0.3/0.5

**wchange_plain** (5)
BAT_IN F.Cu (9.8, 40.85) 0.3/0.5; CAM_INPUT_LIMITED B.Cu (39.65, 87.6) 0.3/0.8; GND B.Cu (34.35, 78.05) 0.2/0.25; RAW_PROTECTED F.Cu (12.6, 40.35) 0.3/0.5; RAW_PROTECTED B.Cu (27.35, 27.85) 0.3/0.5

**wchange_T** (10)
3V3 B.Cu (30.1, 55.32) 0.2/0.25; 3V3 F.Cu (33.1, 81.73) 0.2/0.25; 3V3A B.Cu (37.82, 76.94) 0.2/0.3; 3V3A B.Cu (38.35, 50.15) 0.25/0.3; PYRO1_BUS F.Cu (16.17, 95.36) 0.4/1.0; PYRO1_OUT F.Cu (30.58, 90) 0.2/0.3; RAW_PROTECTED B.Cu (15.075, 36.375) 0.25/0.6; RAW_PROTECTED B.Cu (15.7, 35.75) 0.4/0.6; RAW_PROTECTED B.Cu (26.225, 26.725) 0.25/0.5; USB_LIMITED B.Cu (24.125, 61.625) 0.2/0.4

**wchange_via** (14)
3V3 B.Cu (12.6, 59.5) 0.2/0.3; 3V3 B.Cu (27.35, 44.25) 0.25/0.3; 3V3 B.Cu (30.17, 65.1) 0.2/0.25; 3V3 B.Cu (31.1, 54.5) 0.25/0.3; 3V3 F.Cu (36, 82.43) 0.2/0.25; 3V3A B.Cu (35.5, 76.54) 0.2/0.3; 3V3A B.Cu (35.9632, 69.9393) 0.2/0.25; BAT_IN F.Cu (9.3, 40.15) 0.3/0.5; CAM_5V B.Cu (39.35, 104.55) 0.3/0.8; GND F.Cu (24.55, 89.275) 0.2/0.45; GND B.Cu (31.5, 47.1) 0.2/0.25; GND B.Cu (31.5, 53.5) 0.2/0.25; GND B.Cu (33.95, 78.55) 0.2/0.25; VBUS F.Cu (11.325, 82.05) 0.2/0.3

**wchange_pad** (14)
3V3A B.Cu (34.42, 71.175) 0.2/0.3; CAM_5V B.Cu (32.4, 105.325) 0.2/0.3; CAM_INPUT_LIMITED B.Cu (40.3, 90.1) 0.3/0.8; CAM_INPUT_LIMITED B.Cu (40.7, 93.45) 0.5/0.8; CAM_IO_3V3 B.Cu (42.8, 32.45) 0.2/0.25; GND B.Cu (19.03, 89) 0.2/0.25; GND B.Cu (28.6, 32.6) 0.2/0.25; PYRO1_CONT F.Cu (27.87, 86.75) 0.15/0.2; RAW_PROTECTED B.Cu (38.5, 83.2) 0.2/0.4; RAW_PROTECTED B.Cu (38.9, 85.7) 0.3/0.4; USB_LIMITED B.Cu (30.4, 27.85) 0.25/0.4; VLOGIC B.Cu (18, 31.8) 0.4/0.5; VLOGIC F.Cu (28.505, 29.85) 0.2/0.25; VLOGIC B.Cu (28.525, 28.55) 0.4/0.5

**alt_bends** (9)
3V3A B.Cu (38.35, 50.15) segs 2.758/8.76/0.509/2.496; CAM_IO_3V3 B.Cu (44.55, 33.75) segs 4.7/2.121/6.2/1.414; RADIO_MOSI F.Cu (9.4, 29.2) segs 1.2/0.566/10.232/1.086; RADIO_NSS F.Cu (9.4, 30.2) segs 1.2/0.849/10.8/1.697; RAW_PROTECTED In2.Cu (19.15, 103.27) segs 10.041/1.0/9.758/1.2/0.566; SW_NODE B.Cu (18.32, 36.05) segs 2.2/1.131/0.4/1.697; USB_LIMITED B.Cu (16.8, 81.55) segs 3.394/12.6/13.435/10.5/0.566/5.6; USB_LIMITED B.Cu (29.1, 40.55) segs 0.5/1.131/3.0/2.404/3.2; USB_LIMITED B.Cu (31.6, 34.55) segs 3.2/1.131/2.4/0.424

**u_turn** (18)
3V3 B.Cu (36.94, 52.65) chain 16.32 mm; GND F.Cu (6.31, 79.625) chain 3.378 mm; GND B.Cu (13.7, 80.6) chain 6.084 mm; GND F.Cu (14.3, 59) chain 6.621 mm; GND F.Cu (16.35, 45.95) chain 6.556 mm; PYRO1_CONT F.Cu (26.83, 87.9) chain 3.61 mm; RADIO_BUSY B.Cu (10, 49.5) chain 30.575 mm; RADIO_DIO1 B.Cu (10, 50.5) chain 33.889 mm; RADIO_MISO_MCU B.Cu (10.7, 48.5) chain 30.426 mm; RADIO_NRST B.Cu (9.3, 50) chain 32.132 mm; RADIO_NSS B.Cu (9.3, 47.5) chain 23.249 mm; RADIO_TXEN B.Cu (31.13, 20.15) chain 22.719 mm; RAW_ACT B.Cu (10, 90.78) chain 31.294 mm; RAW_ACT F.Cu (10.4, 64.67) chain 5.604 mm; USB_DM F.Cu (6.88, 74.55) chain 7.28 mm; USB_LIMITED In2.Cu (29.1, 40.55) chain 7.401 mm; VCAP2 F.Cu (14.3, 58.5) chain 11.067 mm; VLOGIC F.Cu (28.505, 29.85) chain 13.158 mm

**passes_through_pad** (10)
3V3 F.Cu (12.049, 76.5412) LS120.1; ARM1_SENSE F.Cu (17.28, 94.15) R180.1; GND F.Cu (26, 91.125) Q124.2; GNSS_RF_ANT F.Cu (12.85, 2.3) L30.2; GNSS_RF_ANT F.Cu (12.85, 2.3) D30.1; PYRO1_OUT F.Cu (30.58, 90) R173.1; QSPI_NCS F.Cu (26.75, 40.45) R10.1; RADIO_RF_ANT F.Cu (31.54, 2.3) D31.1; RAW_ACT B.Cu (8.7, 110.68) Q121.5; USB_DM F.Cu (5.7, 75.55) J3.A7

**seg_inside_pad** (2)
QSPI_NCS F.Cu (26.97, 39.7) R10.1; VLOGIC B.Cu (18, 32.35) U2.2

**via_on_track_body** (23)
3V3 B.Cu (26.4, 36.6) centre-line distance 0.5 mm; 3V3 In2.Cu (30.17, 71.17) centre-line distance 0.23 mm; 3V3 B.Cu (30.4, 70.25) centre-line distance 0.23 mm; 3V3 F.Cu (33.1, 82.35) centre-line distance 0.35 mm; 3V3 B.Cu (36.94, 52.65) centre-line distance 0.35 mm; BAT_IN B.Cu (9.3, 53.375) centre-line distance 0.545 mm; CAM_5V B.Cu (39.35, 104.55) centre-line distance 0.425 mm; GND F.Cu (6.85, 40.5) centre-line distance 0.1 mm; GND B.Cu (10.7, 70.5) centre-line distance 0.3 mm; GND F.Cu (18.18, 90.55) centre-line distance 0.177 mm; GND B.Cu (24.97, 64.4) centre-line distance 0.4 mm; GND F.Cu (27.05, 62.65) centre-line distance 0.424 mm; GND F.Cu (27.9, 55.3) centre-line distance 0.424 mm; GND B.Cu (28.45, 25.85) centre-line distance 0.3 mm; GND B.Cu (29.05, 25.15) centre-line distance 0.424 mm; GND B.Cu (41.3, 85.6) centre-line distance 0.354 mm; GND B.Cu (43.5, 89) centre-line distance 0.2 mm; RADIO_RXEN F.Cu (23.8, 39.45) centre-line distance 0.318 mm; RAW_ACT B.Cu (6.8, 108.5) centre-line distance 0.198 mm; USB_LIMITED B.Cu (29.1, 40.55) centre-line distance 0.5 mm; VBUS F.Cu (9.28, 70.7) centre-line distance 0.5 mm; VBUS In2.Cu (11, 76.35) centre-line distance 0.4 mm; VLOGIC F.Cu (13.6, 36.35) centre-line distance 0.5 mm

**pad_end_offcentre** (63)
3V3 F.Cu (13.925, 43.4) R89.1 0.424; 3V3 B.Cu (16.85, 31.6) U2.1 0.283; 3V3 F.Cu (19.38, 35.9) C29.1 0.255; 3V3 B.Cu (20.8, 97.525) R76.1 0.3; 3V3 F.Cu (27.93, 39.7417) R10.2 0.108; 3V3 B.Cu (29.6, 57.18) C13.1 0.283; 3V3 B.Cu (32, 83.15) D121.5 0.4; 3V3 B.Cu (32.1, 54.5) C23.1 0.283; 3V3 F.Cu (43.85, 77.92) J2.1 0.215; 3V3A B.Cu (32.6, 49.6) C22.1 0.424; 3V3_GNSS F.Cu (12.61, 21.75) C301.1 0.184; BAT_IN B.Cu (8.2, 54.475) C96.1 0.112; BAT_IN B.Cu (8.2, 54.475) C96.1 0.112; BAT_IN F.Cu (9.3, 39.47) C88.1 0.25; BAT_IN B.Cu (10.62, 52.6) C80.1 0.5; CAM_5V F.Cu (40.175, 40.1) J9.1 0.576; CAM_IO_3V3 B.Cu (37.8, 27.975) R103.1 0.2; CAM_IO_3V3 B.Cu (40.75, 34.5) TP90.1 0.25; CAM_IO_3V3 B.Cu (42.05, 47.15) C93.1 0.483; CAM_IO_3V3 B.Cu (42.05, 47.6) C93.1 0.175; CAM_IO_3V3 B.Cu (43.25, 32.45) U13.5 0.45; CAM_SW B.Cu (42.5, 94.4) U8.5 0.4; GND B.Cu (6.0062, 82.8312) R85.2 0.239; GND F.Cu (6.425, 41.35) R81.2 0.354; GND F.Cu (6.75, 39.9) C87.2 0.283; GND F.Cu (18.9274, 90.7274) C129.2 0.386; GND B.Cu (20.6, 34.2) C7.2 0.283; GND B.Cu (23.97, 63.8) R5.2 0.2; GND B.Cu (27.54, 56.9) C25.2 0.2; GND B.Cu (32, 80.85) D121.2 0.4; GND B.Cu (32.4, 100.73) R156.2 0.2; GND B.Cu (38.9, 86.65) U7.9 0.7; GND B.Cu (39.63, 77.5) C31.2 0.11; GND B.Cu (40.975, 37.475) C90.2 0.175; GND F.Cu (43.85, 75.38) J2.5 0.215; GND F.Cu (44.525, 92.175) R72.2 0.175; GNSS_ANT_SRC B.Cu (7.925, 12.25) Q32.1 0.125; GNSS_LNA_EN B.Cu (12.09, 12.18) R303.1 0.16; GNSS_SAFEBOOT_N F.Cu (2.6, 10.2) TP30.1 0.849; GNSS_VCC_RF B.Cu (9.575, 12.25) Q32.2 0.125; HSE_OUT B.Cu (23.9, 52.9) Y1.3 0.6; PYRO1_CONT_MID F.Cu (28.95, 87.8) R129.1 0.242; PYRO1_GATE F.Cu (22.1, 92.4) R126.2 0.5; PYRO1_GATE F.Cu (23.4, 91.85) C126.1 0.25; PYRO1_GATE F.Cu (23.4, 91.85) C126.1 0.25; PYRO1_GATE_N F.Cu (21.9, 90.4) R126.1 0.3; QSPI_NCS F.Cu (26.75, 39.7) R10.1 0.22; RAW_PROTECTED B.Cu (35.7, 85.82) C71.1 0.145; RAW_PROTECTED B.Cu (38.175, 83.2) TP70.1 0.325; RAW_PROTECTED B.Cu (40.2, 80.3) TP81.1 0.99; SW_NODE B.Cu (17.9, 34.3) U2.5 0.141; USB_LIMITED B.Cu (16.8, 81.55) U10.6 0.5; USB_LIMITED B.Cu (30.4, 27.85) U11.7 0.525; USB_LIMITED B.Cu (33.1, 26.15) C98.1 0.3; VBUS F.Cu (6.98, 77.8) J3.B4A9 0.141; VBUS F.Cu (13.225, 82.05) C83.1 0.141; VBUS B.Cu (13.55, 79.65) U10.3 0.15; VLOGIC B.Cu (18, 29.6) C6.1 0.283; VLOGIC B.Cu (18, 32.35) U2.2 0.55; VLOGIC B.Cu (18, 32.35) U2.2 0.55; VLOGIC B.Cu (18.1, 29.5) C6.1 0.141; VLOGIC B.Cu (20.6, 31.8) C7.1 0.283; VLOGIC B.Cu (20.825, 31.85) C7.1 0.152

**power_layer_change_no_gnd** (36)
3V3 via (7.9, 80.4) GND 3.415 mm; 3V3 via (12.5, 89.2) GND 5.838 mm; 3V3 via (16.3, 90.525) GND 1.88 mm; 3V3 via (21.9, 96.125) GND 6.702 mm; 3V3 via (28.33, 40.4) GND 2.275 mm; 3V3 via (29.9, 43.625) GND 1.858 mm; 3V3 via (30.63, 31.3417) GND 2.329 mm; 3V3 via (35.1, 45.025) GND 1.5 mm; 3V3 via (35.73, 27.3417) GND 2.071 mm; 3V3 via (36.94, 52.65) GND 2.59 mm; 3V3 via (38.1719, 37.8191) GND 3.474 mm; 3V3 via (41, 77.92) GND 2.171 mm; 3V3 via (44.035, 77.92) GND 2.639 mm; 3V3A via (31.1, 50) GND 2.927 mm; 3V3A via (32.6, 50.2) GND 3.154 mm; BAT_IN via (9.2, 36.05) GND 2.812 mm; CAM_5V via (41.3, 32.425) GND 2.387 mm; CAM_5V via (43.25, 35.625) GND 2.869 mm; CAM_5V via (43.3, 33.425) GND 1.935 mm; RAW_ACT via (12.6, 81.27) GND 1.939 mm; RAW_ACT via (13.1, 75.97) GND 4.314 mm; RAW_PROTECTED via (13.6, 37.85) GND 1.9 mm; RAW_PROTECTED via (14, 33.3) GND 5.59 mm; RAW_PROTECTED via (15.7, 32.4) GND 4.433 mm; RAW_PROTECTED via (18.05, 102.87) GND 6.695 mm; RAW_PROTECTED via (37.85, 54.7) GND 2.362 mm; USB_LIMITED via (25.8, 37.15) GND 2.623 mm; USB_LIMITED via (29.1, 40.55) GND 1.762 mm; VBUS via (10.8, 79.95) GND 3.356 mm; VBUS via (11, 76.35) GND 2.201 mm; VBUS via (11.325, 82.05) GND 2.067 mm; VBUS via (14, 73.23) GND 2.746 mm; VCAP2 via (16, 62.4) GND 2.236 mm; VLOGIC via (13.6, 36.35) GND 2.989 mm; VLOGIC via (16.5, 33.15) GND 3.634 mm; VLOGIC via (31.67, 35.5) GND 2.306 mm

## Appendix B: reproduce

```
cd <scratch>/p4rg        # r7.kicad_pcb (= m3.kicad_pcb, SHA 636a6bdc…), p3.kicad_pcb (7660620c…), r6.kicad_pcb
PY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
$PY -I p4scan.py r7.kicad_pcb s4_r7.json               # independent scan (also p3.kicad_pcb)
$PY -I p4extra.py r7.kicad_pcb                         # runs through T/via, jogs across vias, pour tails
$PY -I <repo>/tools/route_check.py r7.kicad_pcb --report rc_r7.json --routes
$PY -I rc_allpairs.py r7.kicad_pcb                     # all-pairs acute test -> ACT_GATE (5.9, 102.4)
$PY -I probe.py r7.kicad_pcb 0.0 0.025                 # PYRO1_GATE_N: legal spots; the other 10: NONE
$PY -I nudge.py r7.kicad_pcb 0.0 0.01
$PY -I projfit.py r7.kicad_pcb 23.0 88.33 0.025 1.5    # project rules: 0.5 at (22.9, 89.555) 1.229 mm
$PY -I projfit.py r7.kicad_pcb 23.0 88.33 0.05 1.5     # 0.6 at (22.85, 89.63) 1.309 mm
$PY -I addvia.py r7.kicad_pcb viatest/m3.kicad_pcb 22.9,89.555,0.5     # (project files copied beside it)
kicad-cli pcb drc --severity-all --schematic-parity --format json -o viatest/drc.json viatest/m3.kicad_pcb
$PY -I <repo>/tools/check_r7.py viatest/m3.kicad_pcb; $PY -I <repo>/tools/route_check.py viatest/m3.kicad_pcb
python3 <repo>/m3_design/check_actuators.py viatest/m3.kicad_pcb
```
