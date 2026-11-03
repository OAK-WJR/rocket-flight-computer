# R7 review pass 3: routing geometry and style (whole board)

Reviewer: independent, read-only. Dimension: routing geometry and style, every track and via on all four layers,
including copper inherited from R6. Acceptance criterion: CLEAN ROUTING (AGENTS.md §3 plus the owner's list,
written into REQUIREMENTS M2).

- **Board reviewed:** `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
  `7660620cfa834e4d381d2a2638780e9a341341c9b93c6e6f526791204dc77c9c` (the F3 final board named in
  `docs/R7_VALIDATION.md`; unchanged at the end of this review). 1,946 tracks, 709 vias, no arcs, 4,659.7 mm of track.
- **Comparison boards:** pass-2 board `03fe7572…6d54` (2,777 tracks, 699 vias) and committed R6 `3b215ba` (+18 mm in y).
- **Gate on this board:** `tools/check.sh` exit 0 (DRC 0, unconnected 0, parity 0, ERC 0, R7 contract OK,
  "routing hygiene: 0 failing, 20 allowlisted, 0 stale", actuator contract OK, fit OK). `kicad-cli pcb drc
  --severity-all` on a refilled scratch copy: 0 violations of any severity (so also 0 `track_dangling`,
  `via_dangling`, `track_not_centered_on_via`, `copper_sliver`, `isolated_copper`).
- Nothing in the repository was modified except this file. All work was on scratch copies in
  `<scratch>/p3rg/`.

## 1. Verdict

The fix pass did what it claimed for the pass-2 Majors. On the final board my own scan finds **no off-angle
segment, no exposed acute angle, no fold-back, no duplicate, collinear-overlapping or side-by-side-overlapping
copper, no crossing without a node, no overlap-only joint, no off-centre via joint, no dangling end or via, no
segment under 50 µm, and no hairpin.** The redrawn R6 nets (RG-01…RG-04) are clean, and the inherited R6 debris
(RG-06…RG-10) is gone. Against pass 2 the board went from 302 sub-50 µm segments, 129 fold-backs, 103 acute
junctions and 458 same-net contacts without a node to 0, 0, 12 (all buried inside a pad or via) and 42 (all inside a
pad or via, or the corners listed below).

What is left:

- **One Major (P3-ROUTING_GEOMETRY-01): the gate that is meant to enforce M2 is not sound, and M2 is not met at a
  few places on critical nets that the gate cannot see.**
  - `route_check` drops a tiny jog when it sits inside a run of four or more alternating segments: it calls the run
    `extra_bends`, which is information only. The 50 µm micro-segment limit also lets through 58–99 µm segments
    in open routing.
  - So these reach the board unflagged: a tiny jog on SW_NODE (critical power), an 83 µm corner segment on
    PYRO1_GATE_N (pyro), a 0.134/0.185 mm kink into C17.1 on 3V3, and 0.18 mm corner segments on GND in the pyro
    block. There are also five tiny jogs and three 58–99 µm segments on non-critical nets.
  - Two allowlist reasons ("no DRC-legal GND via spot") are false. A 0.06–0.07 mm move of an existing GND via
    closes each one, with DRC 0 and `check_r7` OK on a scratch copy. One more allowlist reason (QSPI_CLK) is stale.
  - M3_R7 says "every hygiene category is 0 on every net except 5 tiny jogs" and R7_VALIDATION says "tiny jogs 50 →
    5". By the gate's own definition there are 13.
  - Each instance on its own is cosmetic and quick to fix. The Major is that the acceptance evidence ("route_check
    OK ⇒ M2 met") does not hold.
- **Four Minors:**
  - P3-02: the GND-via residual. 12 critical layer changes really have no legal new-via spot (independently
    confirmed). They need owner acceptance or a corridor re-space.
  - P3-03: tracks that end only in their own pour, including one floating chain in the 3V3 plane. The gate cannot
    see them because it counts pour contacts as terminals.
  - P3-04: owner-list items the gate only reports as information (detours, extra vias and layer hops, untidy pad
    entries), with their remaining critical-net instances. These include the reworked L1 3V3 node.
  - P3-05: the scope and wording of the GND-via rule and of M2's "Enforced by".

No Critical finding. Nothing found is open, shorted or below a DRC rule.

## 2. Method

Scripts (scratch `p3rg/`, KiCad 10.0.6 Python, boards loaded read-only, never saved):

| Script | What it does |
|---|---|
| `p3scan.py` | **Independent scan written for this pass.** Per (layer, net) node graph at 1 µm. Off-angle, length classes (< 50/100/200 µm, each tagged as inside a pad, inside a via, or open), every track end classified (joined / via off-centre / overlap-only / pour-only / dangling), and **general same-net copper contact without a node at any angle** (centre-line distance < half-width sum, pairs not sharing a node and not T-joined). Also: angles at every node with a wedge-apex test at pads and vias, a **per-segment jog test** (parallel neighbours on both sides, middle < 1 mm, which works across run boundaries), staircases, U-turns, detours, short hops, width changes by node type, via connectivity per layer, critical and power layer changes against the nearest GND via, and pass-through pads |
| `refine.py`, `segpour.py`, `inpour.py` | Whether each contact lies inside same-net pad or via copper; how much of a short segment or pour-ended track lies outside its own pour fill |
| `origin.py`, `new_in_fix.json` | Segment origin (R6 / pass-2 / fix pass) and instances new since the pass-2 board |
| `probe.py` | **Independent GND-via spot search** for each critical layer change with no GND via within 1.5 mm. 0.025 mm grid, 0.5/0.3 and 0.6/0.3 mm vias. Rules: 0.15 mm copper, 0.25 mm hole clearance and hole-to-hole, RF 0.25 mm, Pyro D 0.5 mm (incl. fills), J2 0.508 mm, bare TP 1.0 mm, edge and supports 0.5 mm, rule-area keep-outs, 0.15 mm from GND solder pads, 0.1 mm from paste and from SMD mask openings. The BAT_IN/RAW_ACT/ACT_FET_S servo corridor is reported separately |
| `nudge.py`, `nudge_apply.py` | The same rules for moving an existing GND via (≤ 0.5 mm) so that it serves the layer change without leaving any it already serves; apply, refill and run DRC on a scratch copy |
| `cand3.py`, `swscan.py` | Edge gap of a candidate replacement polyline to other-net copper (KiCad shape collision, binary search) |
| `ctx.py`, `render.py`, `r.sh` | Local listings and vector renders (`p3rg/img/*.png`) |

I also ran the gate's own `tools/route_check.py --report` and the pass-2 `scan.py` unchanged on the final board.
Both reproduce F3's handoff tables exactly (route_check 244 instances / 0 failing / 20 allowlisted; scan.py 1,034
instances).

## 3. Pass-2 findings in this dimension: closure check

| ID | Pass-2 | Disposition in R7_VALIDATION | Verified on the final board |
|---|---|---|---|
| RG-01 PULLPIN copy | Major | Fixed | **Closed.** One route, 2 vias, no overlap, loop or acute joint. One 0.5 mm-offset dogleg (F.Cu (32.0, 56.0)); entries 0.2 mm off D122.3/R160.2 centre (run at x 32.7, info) |
| RG-02 BAT_ILIM copy | Major | Fixed | **Closed.** One 0.2 mm link, TP89 branch 1 via. The R6 link's 0.5 mm dogleg at (10.575, 38.9) remains (not tiny) |
| RG-03 router debris | Major | Fixed (CAM_MCU_TX length residual) | **Closed for geometry.** On the 12 redrawn nets: no hairpin, staircase, acute angle, micro-segment or overlap. Only doglegs ≥ 0.5 mm and forced hops. CAM_MCU_TX 2.66× is RQ-06 (routing-quality dimension) |
| RG-04 dead copper at removed parts | Major | Fixed | **Closed.** No track end or via lies in a removed R6 pad except the collapsed D130.5 3V3 Y at (36.5, 51.65), which is a clean three-way node. R7-new lanes cross the area of the removed parts, as intended |
| RG-05 interface layer changes, no GND via | Major | Partly fixed, 10 allowlisted, open for pass 3 / owner | **Not closed.** 8 of the 10 are confirmed to have no legal new-via spot (P3-02). For 2, the allowlist reason is false (P3-01) |
| RG-06 R6 duplicates and overlaps | Major | Fixed | **Closed.** My general contact scan: 0 duplicate, 0 collinear overlap, 0 crossing, 0 overlap-only. The remaining 42 contacts and 20 parallel near-touches are inside same-net pads or vias, or are the sub-200 µm corners and sub-width jogs listed under P3-01 |
| RG-07 PYRO1_GATE twice | Major | Fixed | **Closed.** One 0.2 mm chain R126.2 → C126.1 → R128.1 → Q124.4 at y 91.85, a node in each pad. It starts at (22.1, 92.4), 0.5 mm off R126.2's centre but inside the 1.38 × 1.13 mm pad (info) |
| RG-08 acute, staircases, micro | Major | Fixed, 5 staircases allowlisted | **Mostly closed.** Exposed acute 0, fold-back 0, < 50 µm 0, off-angle 0. Residual tiny jogs and 58–99 µm segments that the gate cannot see: P3-01 |
| RG-09 R6 layer changes, no GND via | Major → Minor | 19/23; 4 allowlisted | **Dispositioned.** The 4 confirmed: ARM1_SENSE ×2 has legal spots only inside the BAT_IN servo corridor; PYRO1_GATE_N and PYRO1_CONT have none (P3-02) |
| RG-10 off-angle 3V3 | Major → Minor | Fixed | **Closed.** 0 off-angle segments. 30 sub-2 µm rounding deviations (16 critical), none above 0.5 µm lateral |
| RG-11 band fan-in, widths, corners | Minor | Partly fixed | **Dispositioned.** RXEN–QSPI_CLK gap is 0.25 mm. The 4 band staircases are allowlisted; the reason is incomplete (note in §5.1) |
| RG-12 corridor | Minor | Accepted | Dispositioned |
| RG-13 limiter loop | Minor | Fixed | **Closed.** No U-loop. Q30/Q32/R301 entries at 45° (info) |
| RG-14 strip pad entries | Minor | Mostly fixed | Dispositioned. A residual 3V3_GNSS bar detour of 2.15 vs 1.54 mm (13.71, 19.7) |
| RG-15 R6 style debt | Minor | Mostly fixed | Dispositioned. Residual counts in §4 |

## 4. Counts

### 4.1 Independent scan (`p3scan.py`), all instances (critical nets in brackets)

Critical nets are the route_check classes: RF, pyro/arm, HSE, USB data, SPI/QSPI/IMU_CS/radio SPI, other
RADIO_*/GNSS_*, and the power rails including GND. I checked that every net with a pour, or with a track ≥ 0.3 mm, is
in a critical class.

| Category | Pass-2 board | **Final board** |
|---|---|---|
| off_angle (> 0.1° or > 2 µm) | 1 (1) | **0 (0)** |
| seg_lt_50um | 302 (176) | **0 (0)** |
| seg_lt_100um (50–100 µm) | 64 (28) | 15 (8). **Open routing: 4** (PYRO1_GATE_N, CAM_EN, LED_YEL_A, CAM_RX_WIRE); 11 wholly inside a via |
| seg_lt_200um (100–200 µm) | 102 (57) | 29 (18). **Open routing: 10** (3V3 ×2, GND ×4, RADIO_NRST, SERVO2_MCU, SERVO3_MCU, CAM_5V_SENSE); 19 inside a via |
| fold_back (0° at a node) | 129 (92) | **0** |
| acute_angle (< 89.5°) | 103 (53) | 12 (7), **all at a pad or via with the wedge inside its copper** |
| adjacent_foldback_overlap | 60 (41) | **0** |
| collinear_overlap / crossing_without_node | 13 / 45 | **0 / 0** |
| contact_without_node (any angle) | 458 (339) | 42 (29): inside a same-net pad/via, or a short-segment corner (§5.1) |
| parallel_overlap (no node) | 221 (147) | 20 (15): inside a pad/via, or a sub-width jog (SW_NODE, RADIO_NRST, SERVO2_MCU) |
| end_overlap_only / end_via_offcentre / end_dangling | 3 / 12 / 0 | **0 / 0 / 0** |
| end_in_pour_only | 34 (34) | 22 (22) (P3-03) |
| jog (parallel in/out, middle < 1 mm) | 122 (54) | 53 (26); **13 tiny** (middle < 0.5 mm or offset < 0.25 mm) |
| hairpin | 1 | **0** |
| staircase (≥ 4 alternating, ≥ 2 < 1 mm) | 24 (10) | 5 (5), all allowlisted |
| alt_bends (≥ 4 alternating, < 2 short) | 28 (10) | 34 (9) |
| collinear_unmerged | 30 (19) | 3 (3), all width steps 0.5→0.3 / 0.8→0.3 mm into U9 / U7 pads |
| wchange plain / T / via / pad | 28 / 38 / 16 / 59 | 5 / 13 / 13 / 16. The 5 plain ones are pad-entry necks ≤ 1.4 mm long |
| crit_via_no_gnd (signal, > 1.5 mm) | 52 | 14, all allowlisted (P3-01, P3-02) |
| power_trackvia_no_gnd (info, > 1.5 mm) | 42 | 38 (P3-05) |
| short_layer_hop (< 3 mm) / u_turn / chain_detour | 24 / 35 / 75 | 25 / 25 / 63 |
| pad_end_offcentre (> 0.1 mm, pad ≤ 2 mm) / pad_entry_45 | 236 / 474 | 90 (64) / 180 (127) |
| passes_through_pad / seg_inside_pad | 22 / 80 | 10 (10) / 2 (2) |
| via_on_track_body (same-net via touching a passing track) | 65 | 39 (24) |
| right_angle (allowed) | 71 | 60 (41) |

### 4.2 Gate (`tools/route_check.py`) on the final board

244 instances. Failing 0, allowlisted 20 (5 staircase, 1 tiny_jog, 14 critical_via_no_gnd), stale 0. Information
only: width_change_junction 31, pad_end_offcentre 90, segment_inside_pad 2, passes_through_pad 10, extra_bends 36,
u_turn 25, short_layer_hop 26. tiny_jog 5 (1 critical, allowlisted).

### 4.3 Pass-2 `scan.py` on the final board

1,034 instances (647 critical), identical to F3's table. It has the same run grammar as route_check, so it also
reports only 5 tiny jogs.

## 5. Findings

### P3-ROUTING_GEOMETRY-01 (Major): the M2 gate is not sound; M2 residue on critical nets passes it

REQUIREMENTS M2 requires, over the whole board, "no … micro-segments or tiny jogs …", and says this is "Enforced
by `tools/route_check.py` in `tools/check.sh`". The R7 acceptance condition lists "the M2 routing check
(`tools/route_check.py`) OK". The gate has three defects that let instances of gated categories, on critical nets,
pass.

**(a) Tiny jogs inside longer alternating runs are never reported.** `route_check.scan()` lines 855–877 look for
runs of alternating headings. A run of 3 (A,B,A) is tested as a tiny jog. A run of 4 or more is classified only as
`staircase` (two or more segments < 1 mm) or `extra_bends` (fewer), and the tiny-jog test is never applied to its
middle segments. `extra_bends` is information only. `test_route_check.py` has no case for a tiny jog inside a run
of four (lines 70–79, 136–143). On this board, using the gate's own definition (middle < 0.5 mm or lateral offset
< 0.25 mm), there are 13 tiny jogs, not 5:

| Net (class) | Where | Middle / offset | route_check reports it as |
|---|---|---|---|
| **SW_NODE (power)** | B.Cu (21.32, 35.25)→(21.72, 35.25), 0.6 mm wide | 0.40 mm / 0.283 mm, less than half the track width, so the two parallel halves' copper overlaps | `extra_bends` [2.2, 1.131, 0.4, 1.697], info (`img/swnode.png`) |
| RADIO_NRST (rfif) | F.Cu (10.6, 27.7)→(10.7, 27.6) | 0.141 / 0.10 mm (sub-width, 0.15 mm track) | allowlisted `staircase` |
| RADIO_BUSY, RADIO_MISO_MCU | F.Cu (10.6, 28.2), (10.6, 28.7) | 0.283/0.2, 0.424/0.3 | allowlisted `staircase` |
| QSPI_CLK (spi) | F.Cu (22.85, 44.65) | 0.424 / 0.3 | allowlisted `tiny_jog` |
| SERVO4_MCU, CAM_FAULT_N, I2C1_SCL, SERVO4_OUT | In2 (15.75, 91.17); In2 (20.45, 103.96); F.Cu (25.35, 62.35); In2 (26.1, 68.4) | 0.391/0.276; 0.256/0.181; 0.424/0.3; 0.30/0.212 | `extra_bends`, info (not counted in M3_R7) |
| CAM_EN, SERVO2_MCU, CAM_5V_SENSE, LOGIC_ILIM | the 4 non-critical residuals of F3 §7 | | `tiny_jog`, counted, not gated |

The SW_NODE jog is inherited R6 copper, and it is placement-driven. `swscan.py` searched every
"east-then-one-diagonal" route from (18.32, 36.05) into L1.1 (e 1.5–3.0 mm, diagonal 0.5–2.0 mm, 0.025 mm steps):
none clears C7.2, C9.2, the 3V3 via (18.7, 35.28) and the GND via (19.5, 35.2) by 0.15 mm. It is still a tiny jog
by the gate's own definition, and the gate should report it so that it is fixed or allowlisted with a reason.

**(b) Micro-segments of 50–200 µm in open routing pass.** `MICRO = 0.05` (line 70) is the only short-segment test.
These open-routing segments (not inside a same-net pad or via) are shorter than their own track width:

| Net (class) | Segment | Length / width | Origin | Clean alternative (measured) |
|---|---|---|---|---|
| **PYRO1_GATE_N (pyro)** | F.Cu (21.6, 89.5818)→(21.6829, 89.5818), in the path R126.1 → N → **E 83 µm** → NE 0.307 → N → R127.1 | 0.083 / 0.20 mm | untouched R6 | N to 89.6647, NE 0.424 to (21.9, 89.3647), N: same worst gap, 0.477 mm to R127.2 (`cand3.py`; `img/pyrogaten.png`) |
| **3V3 (power)** | B.Cu (12.6, 59.5)→(14.505, 59.5)→**(14.6, 59.595)**→(14.6, 59.78) into C17.1 | 0.134 + 0.185 / 0.30 mm; ends 0.10 mm off C17.1's centre; 0.74 mm² of it outside any 3V3 pour | R6 shape, trimmed by F3 | (14.5, 59.5)→C17.1 centre (14.5, 59.88), or a 45° (14.12, 59.5)→(14.5, 59.88): worst gap 0.40 mm (USB_DP) and 0.44 mm (C17.2) (`img/c17.png`) |
| GND (power), pyro block | F.Cu (23.9677, 90.7)→(23.9677, 90.8794)→SE→R128.2 | 0.179 / 0.20 mm; 0.18 mm² outside the GND fill (Pyro D keeps the pour back) | R6 | one 45° from the T at (23.9677, 90.7) |
| GND (power) ×3 | F.Cu (7.6317, 79.625) 0.127; F.Cu (38.1829, 28.3217) 0.117; B.Cu (28.4533, 31.6233) 0.147 | buried in the GND fill (≤ 0.014 mm² outside) | R6 | cosmetic only |
| CAM_EN, LED_YEL_A, CAM_RX_WIRE, SERVO2_MCU, SERVO3_MCU, CAM_5V_SENSE (non-critical) | B.Cu (37.95, 85.2033) 61 µm; F.Cu (40.35, 27.4467) 99 µm; In2 (44.0481, 55.136) 58 µm; In2 (24.5847, 87.871) 119 µm; B.Cu (32.8098, 84.1) 190 µm; F.Cu (22.85, 47.05) 200 µm | | | |

**(c) Allowlist entries whose measured reason is false or stale.** `route_check.ALLOWLIST` line 104 gives the
reason "no DRC-legal GND via spot within 1.5 mm … searched a 0.05 mm grid". That search placed new vias only. It
did not consider moving an existing GND via a few tens of µm:

| Entry | Move | Result |
|---|---|---|
| RADIO_RXEN (21.2, 30.45), nearest GND via 1.553 mm | GND via (19.65, 30.55) (F1's D9.2 return via) → (19.71, 30.51), 0.072 mm | ≤ 1.5 mm |
| GNSS_RXD_MCU (2.2, 51.5), nearest 1.556 mm | GND via (3.3, 50.4) → (3.26, 50.44), 0.057 mm | ≤ 1.5 mm |

`nudge.py` found both with every rule plus a 0.02 mm margin. Each moved via still serves every critical layer
change it served before. I applied both on a scratch copy (`p3rg/nudge/`), refilled the pours natively and ran
`kicad-cli pcb drc --schematic-parity`: 0 violations, 0 unconnected. `tools/check_r7.py` on that copy: "R7 CAD
contract: OK". `tools/route_check.py` on it reports those two entries as stale. The base copy refilled the same way
also gives DRC 0.

The QSPI_CLK entry (line 114) says a larger step "brings the clock within 0.12 mm of RADIO_RXEN (x 23.5)". F1 moved
RXEN to x 23.575. A 0.354 mm step, which is a 0.5 mm diagonal and so not a tiny jog, leaves 0.196 mm to RXEN, which
is DRC-legal (`cand3.py`). The real trade-off is F1's deliberate 0.25 mm clock gap, and the reason should say so.

**(d) The records repeat the gate's undercount.**
- M3_R7 §"Counts": "Every hygiene category is 0 on every net except 5 tiny jogs".
- R7_VALIDATION RG-08: "tiny jogs 50 → 5".
- fix2_F3 §3.1: "Every hygiene category is now 0 on every net, critical or not, except the 5 tiny jogs".

All three are wrong, for the reasons in (a) and (b).

**Why Major:** M2 is a requirement, and its own text names the gate as the enforcement. M2 is not met at three
visible places on critical nets: the SW_NODE tiny jog, the PYRO1_GATE_N 83 µm corner and the 3V3 kink into C17.1.
The gate is structurally unable to report them, and the documents certify the opposite. On their own the
instances are cosmetic, with no electrical, DFM or DRC effect. A skeptic may reasonably weigh that.

**Fix (small):**
1. In `route_check.scan()`, apply the tiny-jog test to every A,B,A triple, including those inside longer runs.
2. Add a gated "open-routing segment shorter than its own width (or 0.2 mm)" category on critical nets, with segments
   wholly inside a same-net pad or via exempt. Add tests for both.
3. Redraw the PYRO1_GATE_N corner and the 3V3 C17.1 entry (alternatives above, both measured). Then redraw or
   allowlist, with a reason, the SW_NODE jog (forced by C7.2/C9.2 and the two vias) and the GND pyro-block corner.
4. Make the two GND via moves (or allowlist them with a true reason), and update the QSPI_CLK reason.
5. Correct M3_R7, R7_VALIDATION and the counts.

### P3-ROUTING_GEOMETRY-02 (Minor): 12 critical layer changes still have no GND via within 1.5 mm

AGENTS §3: "add ground vias next to layer changes". The project uses 1.5 mm, centre to centre (M3_R5). After the
two moves in P3-01(c), 12 allowlisted layer changes remain.

R7 interface, 8:
- RADIO_RXEN (23.8, 39.45): 2.23 mm
- RADIO_NRST (9.3, 50.0): 3.18 mm
- RADIO_BUSY (9.4, 28.2): 1.65 mm; RADIO_BUSY (10.0, 49.5): 2.60 mm
- RADIO_MOSI (9.4, 29.2): 1.65 mm
- RADIO_DIO1 (10.0, 50.5): 3.57 mm
- RADIO_MISO_MCU (10.0, 28.7): 2.11 mm
- RADIO_MOSI_MCU (9.4, 48.5): 1.71 mm

R6, 4:
- PYRO1_GATE_N (23.0, 88.33): 1.82 mm
- PYRO1_CONT (41.1, 78.80): 3.05 mm
- ARM1_SENSE (14.55, 94.15): 5.11 mm; ARM1_SENSE (14.55, 97.55): 7.89 mm

My independent `probe.py` (no margin, 0.025 mm grid, ≈ 7 min) confirms that **no legal 0.5 or 0.6 mm new GND via
spot exists within 1.5 mm for any of the 12**, except ARM1_SENSE. For ARM1_SENSE the only spots are inside the
BAT_IN J1→Q120 servo corridor, at (13.85, 97.525) and (13.975, 93.75); F3 measured that corridor vias raise that
path from 3.91 to 3.95 mΩ. The main blockers are the band and corridor via columns themselves (hole-to-hole and
the lane copper), plus GNSS_TP_MCU and 3V3. `nudge.py` finds no existing GND via that could move to serve them.

- Only 3 of the 12 are SPI, the class AGENTS §3 names: RADIO_MOSI 1.65, RADIO_MOSI_MCU 1.71 and RADIO_MISO_MCU
  2.11 mm. The rest are quasi-static control lines, UART, or the DC pyro sense and gate-drive nets.
- The corridor's B.Cu runs reference In2 GND (F1: 98.6 % of samples), so a GND via joins two GND references.
  Inference, not measured: the return-path detour of ≤ 3.6 mm is electrically insignificant at these edge rates.
- R7_VALIDATION marks this "Open for pass 3 / owner acceptance". I recommend accepting it as a recorded deviation,
  with a respin note to re-space the band and corridor via columns, rather than reworking now.

### P3-ROUTING_GEOMETRY-03 (Minor): pour-ended tracks and floating copper are invisible to the gate

`route_check.graph()` turns every contact with a same-net pour island into a terminal edge to the hub (lines
379–396). `dead()` therefore counts any track that touches a pour as live. 22 track ends touch only their own pour
(P3 appendix, `end_in_pour_only`):

- **Floating copper:** 3V3 In2 (18.7, 51.9)→(19.0, 51.6)→(19.6, 51.6), two segments. They touch no pad, via or other
  track, and lie entirely inside one 3V3 In2 fill island (0.000 mm² outside). This is redundant CAD copper that the
  gate calls live. By contrast, 3V3 In2 (15.2, 62.3)→(16.5, 61.0) also touches only the pour, but it joins two
  separate 3V3 islands (0.062 mm² outside the fill), so it has a function.
- **Six pour-ended tracks stand outside their own fill,** so they show in the copper as stubs:

| Net | Layer | Track | Area outside the fill |
|---|---|---|---|
| GND | F.Cu | (11.75, 37.025)–(10.65, 38.125) | 0.168 mm² |
| GND | B.Cu | (12.43, 78.6)–(10.43, 78.6) | 0.215 mm² |
| GND | B.Cu | (30.80, 27.38)–(32.09, 28.67) | 0.065 mm² |
| GND | B.Cu | (33.03, 27.68)–(32.59, 28.12) | 0.006 mm² |
| 3V3 | In2 | (26.4, 36.6)–(26.4, 38.47) | 0.022 mm² |
| 3V3 | In2 | (16.25, 31.1)–(20.95, 31.1) | 0.028 mm² |

- The other 15 are buried inside their fill (0.000 mm² outside).
- All are R6 copper except GND B.Cu (44.65, 53.55–54.95) and (17.35, 59.93–60.8), which come from the fix pass.

There is no electrical effect: DRC and the pad-group invariant hold. **Fix:** in `dead()`, count a track run whose
only terminals are contacts with one pour island as dead. Delete the floating chain, and trim or justify the six
visible stubs.

### P3-ROUTING_GEOMETRY-04 (Minor): owner-list items judged only by review

M2 also lists:
- needless detours, extra vias or layer hops;
- untidy pad entries;
- width changes away from pads.

`route_check` reports detours, extra vias, layer hops and pad entries as information only, by design (its
docstring). R7_VALIDATION does not record that a reviewer judged each one. What remains on critical nets (full
list in the appendix):

- **The L1 3V3 output node, reworked by F3** (`img/l1.png`), at L1.2 (26.1, 33.0):
  - Four 0.6 mm B.Cu tracks meet the 1.6 × 3.5 mm pad at different points.
  - R6's vertical starts off-centre at (26.4, 33.3).
  - F3's C9.1 diagonal (24.1, 36.6)→(26.0, 34.7) ends 0.05 mm inside the pad edge. Its copper merges with the
    vertical's for about 0.15 mm outside the pad (y 34.75–34.9), a contact without a node.
  - F3's via (24.8, 34.3) feeds a second via (24.2, 35.3) over a 1.25 mm B.Cu hop, with a new 0.95 mm In2 link.
  - Functionally fine, since it keeps three plane vias (F3 §2). It is the untidiest new copper on the board.
- **Short layer hops on critical nets: 10.** New since pass 2:
  - 3V3 (24.8, 34.3)→(24.2, 35.3), 1.25 mm;
  - CAM_5V via pair (39.35, 104.55)/(39.35, 103.6), 0.95 mm (deliberate via doubling);
  - VBUS (10.8, 79.95)→(11.325, 82.05), 2.32 mm;
  - 3V3A (35.5, 76.54)→(37.4, 76.52), 2.51 mm.
- **U-turns on critical nets: 17.** These are the R7 corridor radio lanes (documented RG-12/RQ-02), R6 GND and
  power runs, and VLOGIC F.Cu (28.505, 29.85) (13.2 vs 7.0 mm). The VLOGIC route is inherited, and `cand3.py` shows
  the direct routes are blocked by 3V3 (x 31.04), C99.2 and LOGIC_SOURCE_ST.
- **Pad entries more than 0.1 mm off centre on critical nets: 64**, 15 of them new. Examples: PYRO1_GATE at R126.2
  0.5 mm (inside the large pad), RAW_PROTECTED at TP70.1 0.325 mm, USB_LIMITED at U11.7 0.525 mm.
- **Tracks through a same-net pad on critical nets: 10.** The RF ones (GNSS_RF_ANT over L30.2 and D30.1,
  RADIO_RF_ANT over D31.1) are deliberate stub-free RF shunt placement.

**Fix:** tidy the L1.2 node. Bring both 0.6 mm tracks to the pad centre, and either drop the second via or put it
beside the first on the pad. State in M2 and M3_R7 which owner items the gate holds and which a reviewer judges, and
record that judgement for the remaining critical-net instances.

### P3-ROUTING_GEOMETRY-05 (Minor): scope of the GND-via rule and of "Enforced by"

- AGENTS §3 names power as a critical net class. `route_check.critical_transitions()` checks signal classes only.
  38 power-net vias with tracks on two layers have no GND via within 1.5 mm. One is new: 3V3 (24.2, 35.3), 3.95 mm.
  For plane-fed rails this is reasonable engineering (Inference). The scope choice should still be written into
  AGENTS §3 or M2, so that the rule and the gate agree.
- M2 says the whole board, but route_check gates its hygiene categories only on critical nets. On this board that
  leaves 9 tiny jogs and 3 micro-segments of 58–99 µm on non-critical nets (P3-01).
- **Fix:** documentation only. Alternatively, gate the hygiene categories on every net and allowlist the forced ones.

### 5.1 Notes (no finding)

- **The band staircase allowlist** (4 entries) says "only moving the via columns removes it". That is incomplete.
  The band is also boxed in on the south by BAT_SW_RETURN, at 0.175 mm from RADIO_NSS's lane (`cand3.py`; NSS
  shifted 0.1 mm south leaves 0.075 mm). So a non-uniform pitch that would drop the NRST 0.1 mm jog does not fit
  either. The grammatical "staircase" is in fact a fan-in jog plus a corner chamfer (`img/band.png`). I accept the
  allowlist; the reason text could name BAT_SW_RETURN.
- **The PYRO1_CONT staircase allowlist** is verified. The route threads between SWDIO (0.172 mm) and R77.1
  (0.261 mm). A single long diagonal from (37.82, 84.12) hits SWDIO's via (41.5, 80.0) (gap 0.0). Visually it is
  an escape chamfer, one 0.4 mm dogleg and a corner (`img/pyrocont.png`).
- **Width.** No neck-down away from a pad: the 5 plain-node width changes are pad-entry necks of ≤ 1.4 mm into U9,
  U11, U7 and U4. Critical signal nets with two widths: PYRO1_CONT (0.15/0.2), PYRO1_OUT, PYRO1_BUS and
  GNSS_ANT_DC. All change at a via, T or pad.
- **Not re-assessed here:** IPC-2152 sizing. F3's DC solves are in M3_R7 and DRC is clean.
- **Origin of copper on the final board:** 1,200 segments untouched R6, 193 kept from the pass-2 board, 553 drawn by
  the fix pass.

## 6. Images (scratch `p3rg/img/`)

`swnode.png` (SW_NODE jog), `pyrogaten.png` (PYRO1_GATE_N 83 µm corner), `c17.png` (3V3 kink into C17.1),
`l1.png` (L1.2 3V3 node), `pyrogate.png` (RG-07 fix), `pyrocont.png` (PYRO1_CONT allowlist), `band.png` (band
fan-in), `rxen_gnd.png` and `gnss_gnd.png` (GND via move spots), `vlogic.png`, `v3det.png`, `cam5v.png`,
`usblim.png`.

## Appendix A: every remaining instance on critical nets (final board, `p3scan.py`)

† marks an instance that is new since the pass-2 board (no same category, net, layer and position within 0.05 mm
on `03fe7572…`). `jog` is any run with the same heading in and out and a middle segment under 1 mm; the 13 tiny
ones are in P3-01(a). `pad_entry_45` and `right_angle` are allowed by the §3 rule and listed for completeness.
"inside_via" short segments lie wholly within same-net via copper.

**staircase** (5; † = new since the pass-2 board)
PYRO1_CONT F.Cu (34.72, 84.7217) segs 0.849/2.5/0.566/2.8/1.697; RADIO_BUSY F.Cu (9.4, 28.2) segs 1.2/0.283/10.1/0.424; RADIO_MISO_MCU F.Cu (10.0, 28.7) segs 0.6/0.424/10.166/0.755; RADIO_NRST F.Cu (10.0, 27.7) segs 0.6/0.141/7.8/0.707; RADIO_SCK F.Cu (10.0, 29.7) segs 0.6/0.707/10.298/1.417

**jog** (26; † = new since the pass-2 board)
3V3 B.Cu (31.5, 44.8714) mid 0.946 lat 0.669†; 3V3 F.Cu (34.5, 81.73) mid 0.99 lat 0.7†; 3V3 F.Cu (35.1, 24.6) mid 0.891 lat 0.63†; 3V3A B.Cu (36.4, 60.86) mid 0.509 lat 0.36†; CAM_5V B.Cu (34.23, 31.6) mid 0.6 lat 0.424; CAM_5V B.Cu (38.3, 103.925) mid 0.884 lat 0.625†; GND B.Cu (35.7717, 28.4) mid 0.554 lat 0.392; GND B.Cu (38.2863, 27.058) mid 0.908 lat 0.642; GND B.Cu (42.05, 53.18) mid 0.523 lat 0.37†; PYRO1_CONT F.Cu (37.82, 84.1217) mid 0.566 lat 0.4; PYRO1_CONT In2.Cu (34.52, 59.4217) mid 0.707 lat 0.5; QSPI_CLK F.Cu (22.85, 44.65) mid 0.424 lat 0.3; QSPI_IO0 F.Cu (13.5, 41.9) mid 0.5 lat 0.354; RADIO_BUSY F.Cu (10.6, 28.2) mid 0.283 lat 0.2; RADIO_MISO_MCU F.Cu (10.6, 28.7) mid 0.424 lat 0.3; RADIO_MOSI F.Cu (10.6, 29.2) mid 0.566 lat 0.4; RADIO_NRST F.Cu (10.6, 27.7) mid 0.141 lat 0.1; RADIO_NSS F.Cu (10.6, 30.2) mid 0.849 lat 0.6; RADIO_SCK F.Cu (10.6, 29.7) mid 0.707 lat 0.5; RAW_ACT B.Cu (11.2, 106.78) mid 0.849 lat 0.6; RAW_PROTECTED B.Cu (38.5, 84.175) mid 0.566 lat 0.4†; RAW_PROTECTED F.Cu (33.75, 46.4) mid 0.5 lat 0.354†; SW_NODE B.Cu (21.32, 35.25) mid 0.4 lat 0.283; USB_LIMITED B.Cu (28.7, 46.55) mid 0.566 lat 0.4; VBUS B.Cu (13.05, 78.65) mid 0.5 lat 0.354†; VLOGIC F.Cu (32.27, 29.2) mid 0.849 lat 0.6

**seg_lt_100um** (8; † = new since the pass-2 board)
GND B.Cu (26.98, 62.58) 0.099 mm inside_via; GND B.Cu (28.15, 44.25) 0.099 mm inside_via; GND B.Cu (33.95, 78.55) 0.0707 mm inside_via; GND B.Cu (36.4, 76.54) 0.1 mm inside_via; GND B.Cu (37.25, 25.35) 0.0707 mm inside_via; PYRO1_GATE_N F.Cu (21.6, 89.5818) 0.0829 mm open; RAW_PROTECTED F.Cu (25.85, 40.6) 0.1 mm inside_via; VCAP1 In2.Cu (16.9, 44.3) 0.0707 mm inside_via

**seg_lt_200um** (18; † = new since the pass-2 board)
3V3 B.Cu (14.505, 59.5) 0.1344 mm open†; 3V3 B.Cu (14.6, 59.595) 0.185 mm open; 3V3 F.Cu (27.9, 56.5) 0.2 mm inside_via; 3V3 F.Cu (28.33, 40.2) 0.2 mm inside_via; 3V3 F.Cu (43.85, 77.92) 0.185 mm inside_via; ARM1_SENSE F.Cu (18.18, 91.5) 0.2 mm inside_via; GND B.Cu (19.05, 47.35) 0.1783 mm inside_via; GND B.Cu (28.4533, 31.6233) 0.1467 mm open; GND B.Cu (31.5, 47.1) 0.1435 mm inside_via; GND F.Cu (7.6317, 79.625) 0.1273 mm open; GND F.Cu (23.9677, 90.7) 0.1794 mm open; GND F.Cu (27.65, 29.85) 0.2 mm inside_via†; GND F.Cu (38.1829, 28.3217) 0.1171 mm open; PYRO1_GATE_N F.Cu (31.9, 59.23) 0.2 mm inside_via; RADIO_NRST F.Cu (10.6, 27.7) 0.1414 mm open; SPI1_SCK F.Cu (22.35, 65.55) 0.1414 mm inside_via; USB_LIMITED F.Cu (17.725, 83.15) 0.2 mm inside_via; VBUS B.Cu (14.0, 73.23) 0.2 mm inside_via†

**crit_via_no_gnd** (14; † = new since the pass-2 board)
ARM1_SENSE via (14.55, 94.15) GND 5.112 mm; ARM1_SENSE via (14.55, 97.55) GND 7.885 mm; GNSS_RXD_MCU via (2.2, 51.5) GND 1.556 mm; PYRO1_CONT via (41.1, 78.8017) GND 3.052 mm; PYRO1_GATE_N via (23.0, 88.33) GND 1.815 mm; RADIO_BUSY via (9.4, 28.2) GND 1.649 mm; RADIO_BUSY via (10.0, 49.5) GND 2.596 mm; RADIO_DIO1 via (10.0, 50.5) GND 3.569 mm; RADIO_MISO_MCU via (10.0, 28.7) GND 2.11 mm; RADIO_MOSI via (9.4, 29.2) GND 1.649 mm; RADIO_MOSI_MCU via (9.4, 48.5) GND 1.709 mm; RADIO_NRST via (9.3, 50.0) GND 3.178 mm; RADIO_RXEN via (21.2, 30.45) GND 1.553 mm; RADIO_RXEN via (23.8, 39.45) GND 2.23 mm

**acute_angle** (7; † = new since the pass-2 board)
3V3 B.Cu (26.4, 33.3) 45.0 at pad, wedge inside copper†; ARM1_SENSE F.Cu (17.28, 92.4) 45.0 at pad, wedge inside copper; CAM_INPUT_LIMITED B.Cu (40.3, 90.1) 45.0 at pad, wedge inside copper; GNSS_ANT_SRC B.Cu (3.8, 12.75) 45.0 at pad, wedge inside copper†; HSE_OUT B.Cu (23.2, 53.9) 45.0 at via, wedge inside copper; IMU_CS B.Cu (36.5, 80.77) 45.0 at pad, wedge inside copper; RAW_PROTECTED F.Cu (14.0, 31.2) 45.0 at pad, wedge inside copper

**contact_without_node** (29; † = new since the pass-2 board)
3V3 B.Cu (14.6, 59.595) vs (12.6, 59.5, 14.505, 59.5); 3V3 B.Cu (24.1, 36.6) vs (26.4, 33.3, 26.4, 36.6); 3V3 B.Cu (26.4, 33.3) vs (26.1, 33.0, 24.8, 34.3)†; 3V3 F.Cu (27.35, 45.95) vs (27.35, 44.0437, 27.7687, 43.625); 3V3 F.Cu (27.83, 39.7) vs (28.83, 38.8417, 27.93, 39.7417); 3V3_GNSS F.Cu (12.61, 20.75) vs (12.74, 21.88, 12.0, 22.62)†; BAT_DAMP F.Cu (4.9, 35.325) vs (5.9, 31.075, 2.4, 34.575); BAT_IN B.Cu (8.2, 54.475) vs (8.3, 54.525, 9.2, 54.525); CAM_5V B.Cu (39.35, 104.55) vs (38.3, 103.925, 38.925, 104.55)†; GND B.Cu (28.13, 31.3) vs (28.6, 32.6, 28.6, 31.6233); GND B.Cu (28.6, 32.6) vs (28.6, 32.625, 29.4, 32.625); GND B.Cu (32.3, 47.9) vs (31.3565, 47.1, 29.7982, 48.6583); GND B.Cu (34.79, 78.55) vs (34.35, 78.05, 33.9, 78.5); GND B.Cu (36.5, 77.34) vs (36.0, 76.94, 36.4, 76.54); GND F.Cu (6.31, 79.625) vs (7.7217, 79.535, 7.7217, 78.5); GND F.Cu (23.9677, 90.8794) vs (23.4, 90.7, 23.9677, 90.7); GND F.Cu (23.9677, 90.8794) vs (23.9677, 89.8573, 23.9677, 90.7); GND F.Cu (37.7633, 28.7413) vs (38.3, 27.65, 38.3, 28.3217); PYRO1_GATE_N F.Cu (21.6829, 89.5818) vs (21.6, 90.4, 21.6, 89.5818); PYRO1_OUT F.Cu (30.58, 90.0) vs (28.7, 93.85, 28.7, 91.5)†; RAW_ACT B.Cu (9.0, 87.0) vs (10.0, 87.98, 9.0, 86.98); RAW_PROTECTED B.Cu (38.5, 83.2) vs (38.175, 83.2, 35.7, 85.675)†; SW_NODE B.Cu (17.9, 34.3) vs (17.92, 35.65, 18.32, 36.05); USB_LIMITED B.Cu (16.8, 81.55) vs (17.925, 83.15, 16.325, 81.55); USB_LIMITED B.Cu (30.8, 28.15) vs (30.4, 26.95, 30.4, 27.85); VLOGIC B.Cu (18.0, 29.6) vs (16.0, 29.5, 18.1, 29.5); VLOGIC B.Cu (18.0, 31.8) vs (18.0, 32.35, 18.0, 31.85); VLOGIC B.Cu (20.6, 31.8) vs (23.425, 29.25, 20.825, 31.85); VLOGIC B.Cu (27.825, 28.55) vs (26.905, 29.25, 23.425, 29.25)

**parallel_overlap** (15; † = new since the pass-2 board)
3V3 B.Cu (41.55, 52.55) vs (41.58, 53.9, 41.58, 54.5); BAT_IN B.Cu (8.3, 54.525) vs (6.0, 54.475, 8.2, 54.475)†; BAT_IN B.Cu (11.9, 33.35) vs (13.375, 31.85, 11.875, 33.35); CAM_5V B.Cu (40.3, 105.5) vs (38.3, 103.925, 38.925, 104.55); CAM_5V B.Cu (41.3, 32.425) vs (40.2, 32.45, 37.0, 32.45); CAM_5V B.Cu (43.25, 35.625) vs (43.3, 34.525, 43.3, 33.425); CAM_INPUT_LIMITED B.Cu (40.7, 91.2) vs (40.3, 87.6, 40.3, 90.8)†; GND B.Cu (39.63, 76.2) vs (39.52, 77.5, 39.52, 78.8)†; GND B.Cu (43.775, 48.5621) vs (43.825, 47.55, 43.825, 45.7); GNSS_LNA_EN B.Cu (11.51, 11.6) vs (12.25, 12.18, 13.0, 12.93)†; RADIO_NRST F.Cu (10.7, 27.6) vs (10.0, 27.7, 10.6, 27.7)†; RAW_PROTECTED B.Cu (35.7, 85.82) vs (38.175, 83.2, 35.7, 85.675)†; SW_NODE B.Cu (21.72, 35.25) vs (20.52, 36.05, 21.32, 35.25); VLOGIC B.Cu (18.0, 31.8) vs (20.6, 31.8, 19.0, 31.8); VLOGIC B.Cu (18.0, 32.35) vs (18.0, 29.6, 18.0, 31.8)

**via_on_track_body** (24; † = new since the pass-2 board)
3V3 B.Cu (24.2, 35.3) cl 0.4; 3V3 B.Cu (30.4, 70.25) cl 0.23; 3V3 B.Cu (36.94, 52.65) cl 0.35; 3V3 F.Cu (33.1, 82.35) cl 0.35; 3V3 In2.Cu (30.17, 71.17) cl 0.23†; BAT_IN B.Cu (9.3, 53.375) cl 0.545; CAM_5V B.Cu (39.35, 104.55) cl 0.425†; GND B.Cu (10.7, 70.5) cl 0.3; GND B.Cu (24.97, 64.4) cl 0.4; GND B.Cu (28.45, 25.85) cl 0.3; GND B.Cu (29.05, 25.15) cl 0.4243; GND B.Cu (41.3, 85.6) cl 0.3536; GND B.Cu (43.5, 89.0) cl 0.2; GND F.Cu (6.85, 40.5) cl 0.1; GND F.Cu (18.18, 90.55) cl 0.1774†; GND F.Cu (27.05, 62.65) cl 0.4243; GND F.Cu (27.9, 55.3) cl 0.4243; RADIO_RXEN F.Cu (23.8, 39.45) cl 0.3182†; RAW_ACT B.Cu (6.8, 108.5) cl 0.198; RAW_PROTECTED F.Cu (15.7, 32.4) cl 0.5; USB_LIMITED B.Cu (29.1, 40.55) cl 0.5; VBUS F.Cu (9.28, 70.7) cl 0.5; VBUS In2.Cu (11.0, 76.35) cl 0.4; VLOGIC F.Cu (13.6, 36.35) cl 0.5†

**end_in_pour_only** (22; † = new since the pass-2 board)
3V3 In2.Cu (15.2, 62.3) to (16.5, 61.0) 1.838 mm; 3V3 In2.Cu (16.25, 31.1) to (20.95, 31.1) 4.7 mm; 3V3 In2.Cu (16.5, 61.0) to (15.2, 62.3) 1.838 mm; 3V3 In2.Cu (18.7, 51.9) to (19.0, 51.6) 0.424 mm; 3V3 In2.Cu (19.6, 51.6) to (19.0, 51.6) 0.6 mm; 3V3 In2.Cu (26.4, 38.47) to (26.4, 36.6) 1.87 mm; 3V3 In2.Cu (28.9421, 56.6579) to (28.9421, 59.0473) 2.389 mm; GND B.Cu (12.43, 78.6) to (10.43, 78.6) 2.0 mm; GND B.Cu (13.7, 78.8) to (14.2, 78.8) 0.5 mm; GND B.Cu (17.3498, 59.9256) to (17.3498, 60.8) 0.874 mm†; GND B.Cu (21.9783, 98.2) to (21.9783, 99.0675) 0.867 mm; GND B.Cu (28.12, 108.8618) to (26.4898, 107.2316) 2.305 mm; GND B.Cu (30.7985, 27.3798) to (32.0887, 28.67) 1.825 mm; GND B.Cu (31.1812, 100.4232) to (31.1812, 99.1665) 1.257 mm; GND B.Cu (33.0298, 27.6798) to (32.5943, 28.1153) 0.616 mm; GND B.Cu (43.775, 48.5621) to (43.775, 47.6) 0.962 mm; GND B.Cu (44.65, 54.95) to (44.65, 53.55) 1.4 mm; GND F.Cu (11.75, 37.025) to (10.65, 38.125) 1.556 mm; GND F.Cu (35.83, 59.6) to (36.33, 59.6) 0.5 mm; GND F.Cu (37.7633, 28.7413) to (38.1829, 28.3217) 0.593 mm; GND F.Cu (37.7633, 31.5) to (38.7, 31.5) 0.937 mm; RAW_ACT F.Cu (5.3, 82.17) to (7.0, 82.17) 1.7 mm

**collinear_unmerged** (3; † = new since the pass-2 board)
BAT_IN F.Cu (9.8, 40.85) †; CAM_INPUT_LIMITED B.Cu (39.65, 87.6) †; RAW_PROTECTED F.Cu (12.6, 40.35) †

**wchange_plain** (5; † = new since the pass-2 board)
BAT_IN F.Cu (9.8, 40.85) 0.3/0.5†; CAM_INPUT_LIMITED B.Cu (39.65, 87.6) 0.3/0.8; GND B.Cu (34.35, 78.05) 0.2/0.25; RAW_PROTECTED B.Cu (27.35, 27.85) 0.3/0.5; RAW_PROTECTED F.Cu (12.6, 40.35) 0.3/0.5†

**wchange_T** (12; † = new since the pass-2 board)
3V3 B.Cu (30.1, 55.32) 0.2/0.25; 3V3 F.Cu (33.1, 81.73) 0.2/0.25†; 3V3A B.Cu (37.82, 76.94) 0.2/0.3†; 3V3A B.Cu (38.35, 50.15) 0.25/0.3†; GND B.Cu (14.6, 80.6) 0.2/0.25†; GND B.Cu (33.95, 78.55) 0.2/0.25; PYRO1_BUS F.Cu (16.17, 95.36) 0.4/1.0; PYRO1_OUT F.Cu (30.58, 90.0) 0.2/0.3; RAW_PROTECTED B.Cu (15.075, 36.375) 0.25/0.6†; RAW_PROTECTED B.Cu (15.7, 35.75) 0.4/0.6; RAW_PROTECTED B.Cu (26.225, 26.725) 0.25/0.5†; USB_LIMITED B.Cu (24.125, 61.625) 0.2/0.4

**wchange_via** (13; † = new since the pass-2 board)
3V3 B.Cu (12.6, 59.5) 0.2/0.3; 3V3 B.Cu (27.35, 44.25) 0.25/0.3; 3V3 B.Cu (30.17, 65.1) 0.2/0.25; 3V3 B.Cu (31.1, 54.5) 0.25/0.3; 3V3 F.Cu (36.0, 82.43) 0.2/0.25; 3V3A B.Cu (35.5, 76.54) 0.2/0.3; 3V3A B.Cu (35.9632, 69.9393) 0.2/0.25; BAT_IN F.Cu (9.3, 40.15) 0.3/0.5; CAM_5V B.Cu (39.35, 104.55) 0.3/0.8†; GND B.Cu (31.5, 47.1) 0.2/0.25; GND B.Cu (31.5, 53.5) 0.2/0.25; GND F.Cu (24.55, 89.275) 0.2/0.45; VBUS F.Cu (11.325, 82.05) 0.2/0.3

**wchange_pad** (12; † = new since the pass-2 board)
3V3A B.Cu (34.42, 71.175) 0.2/0.3†; CAM_5V B.Cu (32.4, 105.325) 0.2/0.3; CAM_INPUT_LIMITED B.Cu (40.3, 90.1) 0.3/0.8; CAM_INPUT_LIMITED B.Cu (40.7, 93.45) 0.5/0.8; CAM_IO_3V3 B.Cu (42.8, 32.45) 0.2/0.25†; GND B.Cu (19.03, 89.0) 0.2/0.25; RAW_PROTECTED B.Cu (38.5, 83.2) 0.2/0.4†; RAW_PROTECTED B.Cu (38.9, 85.7) 0.3/0.4; USB_LIMITED B.Cu (30.4, 27.85) 0.25/0.4†; VLOGIC B.Cu (18.0, 31.8) 0.4/0.5; VLOGIC B.Cu (28.525, 28.55) 0.4/0.5; VLOGIC F.Cu (28.505, 29.85) 0.2/0.25†

**seg_inside_pad** (2; † = new since the pass-2 board)
QSPI_NCS F.Cu (26.97, 39.7) R10.1; VLOGIC B.Cu (18.0, 32.35) U2.2

**passes_through_pad** (10; † = new since the pass-2 board)
3V3 F.Cu (12.049, 76.5412) LS120.1; ARM1_SENSE F.Cu (17.28, 94.15) R180.1; GND F.Cu (26.0, 91.125) Q124.2; GNSS_RF_ANT F.Cu (12.85, 2.3) L30.2; GNSS_RF_ANT F.Cu (12.85, 2.3) D30.1; PYRO1_OUT F.Cu (30.58, 90.0) R173.1; QSPI_NCS F.Cu (26.75, 40.45) R10.1; RADIO_RF_ANT F.Cu (31.54, 2.3) D31.1; RAW_ACT B.Cu (8.7, 110.68) Q121.5; USB_DM F.Cu (5.7, 75.55) J3.A7

**short_layer_hop** (9; † = new since the pass-2 board)
3V3 B.Cu (24.8, 34.3) 1.249 mm to (24.2, 35.3)†; 3V3 B.Cu (44.035, 77.92) 2.9 mm to (41.135, 77.92); 3V3 In2.Cu (30.63, 31.3417) 2.404 mm to (32.33, 33.0417); 3V3A B.Cu (35.5, 76.54) 2.505 mm to (37.4, 76.52)†; CAM_5V B.Cu (39.35, 104.55) 0.95 mm to (39.35, 103.6)†; CAM_5V F.Cu (43.3, 33.425) 2.414 mm to (41.3, 32.425); RADIO_NSS B.Cu (23.2, 17.3) 2.196 mm to (23.6, 15.27); USB_DP B.Cu (8.9, 74.75) 1.6 mm to (8.9, 76.35); VBUS F.Cu (10.8, 79.95) 2.317 mm to (11.325, 82.05)†

**u_turn** (17; † = new since the pass-2 board)
3V3 B.Cu (36.94, 52.65) 16.32/5.158 mm to (41.58, 53.9); GND B.Cu (42.05, 52.55) 5.428/3.594 mm to (44.65, 54.95); GND F.Cu (6.31, 79.625) 3.326/1.361 mm to (6.88, 78.5); GND F.Cu (14.3, 59.0) 6.621/3.124 mm to (11.3, 59.3); GND F.Cu (16.35, 45.95) 6.556/2.4 mm to (16.35, 43.55); RADIO_BUSY B.Cu (10.0, 49.5) 30.575/21.549 mm to (9.4, 28.2); RADIO_DIO1 B.Cu (10.0, 50.5) 33.889/23.549 mm to (9.4, 27.2); RADIO_MISO_MCU B.Cu (10.7, 48.5) 30.426/20.09 mm to (10.0, 28.7); RADIO_NRST B.Cu (9.3, 50.0) 32.132/22.59 mm to (10.0, 27.7); RADIO_NSS B.Cu (9.3, 47.5) 23.249/17.341 mm to (9.4, 30.2); RADIO_TXEN B.Cu (31.13, 20.15) 22.719/13.402 mm to (28.59, 7.8); RAW_ACT B.Cu (10.0, 90.78) 31.294/17.685 mm to (4.0, 105.98); RAW_ACT F.Cu (10.4, 64.67) 5.604/3.59 mm to (13.7, 65.37); USB_DM F.Cu (6.88, 74.55) 7.28/3.895 mm to (10.05, 76.3); USB_LIMITED In2.Cu (29.1, 40.55) 7.401/4.767 mm to (25.8, 37.15); VCAP2 F.Cu (14.3, 58.5) 11.067/4.604 mm to (16.0, 62.4); VLOGIC F.Cu (28.505, 29.85) 13.158/6.961 mm to (31.67, 35.5)†

**alt_bends** (9; † = new since the pass-2 board)
3V3A B.Cu (38.35, 50.15) segs 2.758/8.76/0.509/2.496†; CAM_IO_3V3 B.Cu (44.55, 33.75) segs 4.7/2.121/6.2/1.414†; RADIO_MOSI F.Cu (9.4, 29.2) segs 1.2/0.566/10.232/1.086; RADIO_NSS F.Cu (9.4, 30.2) segs 1.2/0.849/10.8/1.697; RAW_PROTECTED In2.Cu (19.15, 103.27) segs 10.041/1.0/9.758/1.2/0.566; SW_NODE B.Cu (18.32, 36.05) segs 2.2/1.131/0.4/1.697; USB_LIMITED B.Cu (16.8, 81.55) segs 3.394/12.6/13.435/10.5/0.566/5.6; USB_LIMITED B.Cu (29.1, 40.55) segs 0.5/1.131/3.0/2.404/3.2†; USB_LIMITED B.Cu (31.6, 34.55) segs 3.2/1.131/2.4/0.424†

**chain_detour** (43; † = new since the pass-2 board)
3V3 B.Cu (31.3232, 45.0482) 5.418/3.786 mm to (35.1, 45.025)†; 3V3 B.Cu (36.94, 52.65) 16.32/5.158 mm to (41.58, 53.9); 3V3 F.Cu (31.1, 54.5) 9.436/6.581 mm to (36.5, 51.65)†; 3V3A B.Cu (35.5, 76.54) 2.505/1.908 mm to (37.4, 76.52)†; 3V3_GNSS F.Cu (13.71, 19.7) 2.15/1.535 mm to (12.61, 20.75)†; ACT_FET_S B.Cu (5.17, 96.0) 3.604/2.407 mm to (5.91, 93.9)†; ARM1_SENSE F.Cu (14.55, 94.15) 4.48/3.455 mm to (17.28, 92.4); GND B.Cu (6.31, 79.625) 7.297/4.928 mm to (6.8, 74.9); GND B.Cu (6.31, 79.625) 4.95/3.332 mm to (6.0062, 82.8312); GND B.Cu (14.6, 80.6) 5.184/4.056 mm to (11.6, 83.15)†; GND B.Cu (32.3, 55.7) 4.014/2.531 mm to (31.5, 53.5); GND B.Cu (33.0298, 27.6798) 2.092/1.098 mm to (32.2, 27.033)†; GND B.Cu (42.05, 52.55) 5.428/3.594 mm to (44.65, 54.95); GND F.Cu (6.31, 70.975) 2.758/1.361 mm to (6.88, 72.1); GND F.Cu (6.31, 79.625) 3.326/1.361 mm to (6.88, 78.5); GND F.Cu (14.3, 59.0) 6.621/3.124 mm to (11.3, 59.3); GND F.Cu (16.35, 45.95) 6.556/2.4 mm to (16.35, 43.55); GND F.Cu (25.17, 109.8) 3.073/2.007 mm to (24.55, 108.05); GND F.Cu (25.97, 87.9) 2.19/1.581 mm to (27.01, 86.75)†; PYRO1_CONT F.Cu (34.72, 84.7217) 12.595/8.832 mm to (41.1, 78.8017); QSPI_IO3 F.Cu (21.7, 34.6) 8.431/6.031 mm to (22.5, 40.3); RADIO_BUSY B.Cu (10.0, 49.5) 30.575/21.549 mm to (9.4, 28.2); RADIO_BUSY F.Cu (9.4, 28.2) 31.781/23.164 mm to (24.91, 11.46); RADIO_DIO1 B.Cu (10.0, 50.5) 33.889/23.549 mm to (9.4, 27.2); RADIO_MISO_MCU B.Cu (10.7, 48.5) 30.426/20.09 mm to (10.0, 28.7); RADIO_MISO_MCU F.Cu (10.0, 28.7) 27.876/21.177 mm to (22.57, 12.73); RADIO_MOSI F.Cu (9.4, 29.2) 29.85/21.806 mm to (24.91, 14.0); RADIO_NRST B.Cu (9.3, 50.0) 32.132/22.59 mm to (10.0, 27.7); RADIO_NSS B.Cu (9.3, 47.5) 23.249/17.341 mm to (9.4, 30.2); RADIO_NSS F.Cu (9.4, 30.2) 25.646/19.143 mm to (23.2, 17.3); RADIO_SCK F.Cu (10.0, 29.7) 27.014/20.361 mm to (24.91, 16.54); RADIO_SCK_MCU B.Cu (10.0, 48.0) 7.523/5.779 mm to (5.7, 44.43); RADIO_TXEN B.Cu (31.13, 20.15) 22.719/13.402 mm to (28.59, 7.8); RAW_ACT B.Cu (10.0, 90.78) 31.294/17.685 mm to (4.0, 105.98); RAW_ACT F.Cu (10.4, 64.67) 5.604/3.59 mm to (13.7, 65.37); RAW_ACT F.Cu (12.6, 81.27) 9.657/7.673 mm to (5.3, 82.17)†; RAW_PROTECTED B.Cu (14.0, 33.3) 18.781/14.948 mm to (26.225, 26.725); USB_DM F.Cu (6.88, 74.55) 7.28/3.895 mm to (10.05, 76.3); USB_DP B.Cu (8.9, 76.35) 5.24/3.547 mm to (11.95, 75.15); USB_LIMITED B.Cu (33.1, 26.15) 4.511/3.404 mm to (30.4, 27.85); USB_LIMITED In2.Cu (29.1, 40.55) 7.401/4.767 mm to (25.8, 37.15); VCAP2 F.Cu (14.3, 58.5) 11.067/4.604 mm to (16.0, 62.4); VLOGIC F.Cu (28.505, 29.85) 13.158/6.961 mm to (31.67, 35.5)†

**pad_end_offcentre** (64; † = new since the pass-2 board)
3V3 B.Cu (14.6, 59.78) C17.1 0.141; 3V3 B.Cu (16.85, 31.6) U2.1 0.283; 3V3 B.Cu (20.8, 97.525) R76.1 0.3; 3V3 B.Cu (29.6, 57.18) C13.1 0.283; 3V3 B.Cu (32.0, 83.15) D121.5 0.4; 3V3 B.Cu (32.1, 54.5) C23.1 0.283; 3V3 F.Cu (13.925, 43.4) R89.1 0.424; 3V3 F.Cu (19.38, 35.9) C29.1 0.255; 3V3 F.Cu (27.93, 39.7417) R10.2 0.108; 3V3 F.Cu (43.85, 77.92) J2.1 0.215; 3V3A B.Cu (32.6, 49.6) C22.1 0.424; 3V3_GNSS F.Cu (12.61, 21.75) C301.1 0.184; BAT_IN B.Cu (8.2, 54.475) C96.1 0.112; BAT_IN B.Cu (8.2, 54.475) C96.1 0.112; BAT_IN B.Cu (10.62, 52.6) C80.1 0.5; BAT_IN F.Cu (9.3, 39.47) C88.1 0.25; CAM_5V F.Cu (40.175, 40.1) J9.1 0.576; CAM_IO_3V3 B.Cu (37.8, 27.975) R103.1 0.2; CAM_IO_3V3 B.Cu (40.75, 34.5) TP90.1 0.25†; CAM_IO_3V3 B.Cu (42.05, 47.15) C93.1 0.483; CAM_IO_3V3 B.Cu (42.05, 47.6) C93.1 0.175†; CAM_IO_3V3 B.Cu (43.25, 32.45) U13.5 0.45; CAM_SW B.Cu (42.5, 94.4) U8.5 0.4; GND B.Cu (6.0062, 82.8312) R85.2 0.239; GND B.Cu (20.6, 34.2) C7.2 0.283; GND B.Cu (23.97, 63.8) R5.2 0.2; GND B.Cu (27.54, 56.9) C25.2 0.2; GND B.Cu (32.0, 80.85) D121.2 0.4; GND B.Cu (32.0887, 28.67) R105.2 0.111; GND B.Cu (32.4, 100.73) R156.2 0.2†; GND B.Cu (38.9, 86.65) U7.9 0.7; GND B.Cu (39.63, 77.5) C31.2 0.11†; GND B.Cu (40.975, 37.475) C90.2 0.175†; GND F.Cu (6.425, 41.35) R81.2 0.354; GND F.Cu (6.75, 39.9) C87.2 0.283; GND F.Cu (18.9274, 90.7274) C129.2 0.386; GND F.Cu (43.85, 75.38) J2.5 0.215; GND F.Cu (44.525, 92.175) R72.2 0.175; GNSS_ANT_SRC B.Cu (7.925, 12.25) Q32.1 0.125†; GNSS_LNA_EN B.Cu (12.09, 12.18) R303.1 0.16†; GNSS_SAFEBOOT_N F.Cu (2.6, 10.2) TP30.1 0.849; GNSS_VCC_RF B.Cu (9.575, 12.25) Q32.2 0.125†; HSE_OUT B.Cu (23.9, 52.9) Y1.3 0.6; PYRO1_CONT_MID F.Cu (28.95, 87.8) R129.1 0.242; PYRO1_GATE F.Cu (22.1, 92.4) R126.2 0.5†; PYRO1_GATE F.Cu (23.4, 91.85) C126.1 0.25†; PYRO1_GATE F.Cu (23.4, 91.85) C126.1 0.25†; QSPI_NCS F.Cu (26.75, 39.7) R10.1 0.22; RAW_PROTECTED B.Cu (35.7, 85.82) C71.1 0.145; RAW_PROTECTED B.Cu (38.175, 83.2) TP70.1 0.325†; RAW_PROTECTED B.Cu (40.2, 80.3) TP81.1 0.99; SW_NODE B.Cu (17.9, 34.3) U2.5 0.141; USB_LIMITED B.Cu (16.8, 81.55) U10.6 0.5; USB_LIMITED B.Cu (30.4, 27.85) U11.7 0.525†; USB_LIMITED B.Cu (33.1, 26.15) C98.1 0.3; VBUS B.Cu (13.55, 79.65) U10.3 0.15†; VBUS F.Cu (6.98, 77.8) J3.B4A9 0.141†; VBUS F.Cu (13.225, 82.05) C83.1 0.141; VLOGIC B.Cu (18.0, 29.6) C6.1 0.283; VLOGIC B.Cu (18.0, 32.35) U2.2 0.55; VLOGIC B.Cu (18.0, 32.35) U2.2 0.55; VLOGIC B.Cu (18.1, 29.5) C6.1 0.141; VLOGIC B.Cu (20.6, 31.8) C7.1 0.283; VLOGIC B.Cu (20.825, 31.85) C7.1 0.152

**power_trackvia_no_gnd** (38; † = new since the pass-2 board)
3V3 via (7.9, 80.4) GND 3.415 mm; 3V3 via (12.5, 89.2) GND 5.838 mm; 3V3 via (16.3, 90.525) GND 1.88 mm; 3V3 via (21.9, 96.125) GND 6.702 mm; 3V3 via (24.2, 35.3) GND 3.954 mm†; 3V3 via (26.4, 36.6) GND 3.16 mm; 3V3 via (28.33, 40.4) GND 2.275 mm; 3V3 via (29.9, 43.625) GND 1.858 mm; 3V3 via (30.4, 78.25) GND 1.992 mm; 3V3 via (30.63, 31.3417) GND 2.329 mm; 3V3 via (35.73, 27.3417) GND 2.576 mm; 3V3 via (36.94, 52.65) GND 2.59 mm; 3V3 via (38.1719, 37.8191) GND 3.474 mm; 3V3 via (41.135, 77.92) GND 2.172 mm; 3V3 via (44.035, 77.92) GND 2.639 mm; 3V3A via (31.1, 50.0) GND 2.927 mm; 3V3A via (32.6, 50.2) GND 3.154 mm; BAT_IN via (9.2, 36.05) GND 2.812 mm; CAM_5V via (41.3, 32.425) GND 2.387 mm; CAM_5V via (43.25, 35.625) GND 2.869 mm; CAM_5V via (43.3, 33.425) GND 1.935 mm; RAW_ACT via (12.6, 81.27) GND 1.939 mm; RAW_ACT via (13.1, 75.97) GND 4.314 mm; RAW_PROTECTED via (13.6, 37.85) GND 1.9 mm; RAW_PROTECTED via (14.0, 33.3) GND 5.59 mm; RAW_PROTECTED via (15.7, 32.4) GND 4.362 mm; RAW_PROTECTED via (18.05, 102.87) GND 6.695 mm; RAW_PROTECTED via (37.85, 54.7) GND 2.362 mm; USB_LIMITED via (25.8, 37.15) GND 2.623 mm; USB_LIMITED via (29.1, 40.55) GND 1.762 mm; VBUS via (10.8, 79.95) GND 3.356 mm; VBUS via (11.0, 76.35) GND 2.201 mm; VBUS via (11.325, 82.05) GND 2.067 mm; VBUS via (14.0, 73.23) GND 2.746 mm; VCAP2 via (16.0, 62.4) GND 2.236 mm; VLOGIC via (13.6, 36.35) GND 2.989 mm; VLOGIC via (16.5, 33.15) GND 3.634 mm; VLOGIC via (31.67, 35.5) GND 2.306 mm

**pad_entry_45** (127; † = new since the pass-2 board)
3V3 B.Cu (20.8, 97.525) R76.1; 3V3 B.Cu (24.1, 36.6) C9.1; 3V3 B.Cu (26.0, 34.7) L1.2†; 3V3 B.Cu (26.1, 33.0) L1.2; 3V3 B.Cu (26.1, 33.0) L1.2; 3V3 B.Cu (29.075, 38.6) R91.1; 3V3 B.Cu (31.77, 75.3) R13.2; 3V3 B.Cu (32.0, 83.15) D121.5; 3V3 B.Cu (32.3, 46.025) R164.1; 3V3 F.Cu (19.2, 36.08) C29.1; 3V3 F.Cu (27.83, 39.7) R10.2; 3V3 F.Cu (27.93, 39.7417) R10.2; 3V3 F.Cu (31.55, 28.6) D122.2; 3V3A B.Cu (32.3, 44.475) R164.2; 3V3A B.Cu (32.3, 49.3) C22.1; 3V3A B.Cu (32.3, 49.3) C22.1; 3V3A B.Cu (32.72, 71.9) C32.1; 3V3A B.Cu (37.21, 77.55) U4.8†; 3V3A B.Cu (40.1, 47.4) C10.1; 3V3_GNSS F.Cu (12.74, 21.88) C301.1; 3V3_RADIO F.Cu (24.2, 21.25) R310.1†; 3V3_RADIO F.Cu (35.1, 20.85) FB31.2; 3V3_RADIO F.Cu (36.78, 19.6) C310.1; ACT_FET_S B.Cu (5.91, 93.9) Q120.1†; ARM1_SENSE B.Cu (24.38, 46.4) R170.1; ARM1_SENSE F.Cu (17.28, 92.4) R133.1; BAT_DAMP F.Cu (2.4, 34.575) R166.1; BAT_DAMP F.Cu (5.9, 31.075) C89.2; BAT_DAMP F.Cu (7.1, 33.125) C95.2; BAT_IN B.Cu (8.2, 54.475) C96.1; BAT_IN B.Cu (10.62, 52.6) C80.1; BAT_IN B.Cu (11.875, 33.35) D8.1; BAT_IN B.Cu (11.9, 33.35) D8.1; BAT_IN B.Cu (15.475, 24.45) R80.1; BAT_IN F.Cu (9.455, 43.25) R82.1; CAM_5V B.Cu (32.4, 105.325) R78.1; CAM_5V B.Cu (32.4, 105.325) R78.1; CAM_5V B.Cu (40.3, 105.5) C75.1; CAM_5V B.Cu (40.3, 105.5) C75.1; CAM_5V F.Cu (40.175, 40.1) J9.1; CAM_INPUT_LIMITED B.Cu (32.5, 95.5) TP71.1; CAM_INPUT_LIMITED B.Cu (40.3, 90.1) C72.1; CAM_IO_3V3 B.Cu (37.8, 27.975) R103.1; CAM_IO_3V3 B.Cu (40.75, 34.5) TP90.1†; CAM_IO_3V3 B.Cu (42.05, 47.15) C93.1; CAM_IO_3V3 B.Cu (42.7, 27.7) C92.1; CAM_IO_3V3 B.Cu (42.8, 32.45) U13.5; CAM_IO_3V3 B.Cu (42.8, 32.45) U13.5; CAM_IO_3V3 B.Cu (43.25, 32.45) U13.5; CAM_SW B.Cu (42.5, 94.4) U8.5; CAM_SW B.Cu (44.7, 93.825) C74.1; GND B.Cu (10.03, 79.0) R8.2; GND B.Cu (19.03, 89.0) R155.2; GND B.Cu (23.97, 63.8) R5.2; GND B.Cu (27.54, 56.9) C25.2; GND B.Cu (28.45, 29.35) U11.12; GND B.Cu (28.95, 27.05) U11.4; GND B.Cu (29.4, 54.48) C14.2; GND B.Cu (30.7, 33.925) R86.2; GND B.Cu (32.0, 80.85) D121.2; GND B.Cu (32.0887, 28.67) R105.2; GND B.Cu (32.3, 47.9) C22.2; GND B.Cu (32.3, 55.7) C23.2; GND B.Cu (34.65, 26.45) C98.2; GND B.Cu (36.93, 71.175) U5.3; GND B.Cu (37.8, 29.425) R103.2; GND B.Cu (38.9, 86.65) U7.9; GND B.Cu (42.9, 93.45) U8.4; GND B.Cu (43.9, 87.4) C73.2; GND F.Cu (4.525, 43.25) R83.2; GND F.Cu (6.425, 41.35) R81.2; GND F.Cu (6.88, 72.1) J3.A1B12; GND F.Cu (10.65, 38.125) R84.2; GND F.Cu (14.875, 82.15) C83.2; GND F.Cu (18.275, 82.15) C86.2; GND F.Cu (26.0, 89.825) Q124.1; GND F.Cu (27.85, 45.95) U1.26; GND F.Cu (29.345, 30.05) C99.2; GND F.Cu (44.525, 92.175) R72.2; GNSS_ANT_GATE B.Cu (5.7, 12.75) Q30.1†; GNSS_ANT_PD B.Cu (11.0, 14.25) Q31.3†; GNSS_ANT_SRC B.Cu (3.8, 12.75) Q30.2†; GNSS_ANT_SRC B.Cu (5.32, 14.27) R301.1†; GNSS_LNA_EN B.Cu (12.09, 12.18) R303.1†; GNSS_LNA_EN B.Cu (12.25, 12.18) R303.1†; GNSS_TIMEPULSE F.Cu (9.0, 22.02) R307.1; HSE_OUT B.Cu (22.6, 53.3) C26.1; HSE_OUT B.Cu (23.9, 52.9) Y1.3; IMU_CS B.Cu (36.5, 80.77) R11.1; PYRO1_COLD F.Cu (29.72, 86.1) R131.2; PYRO1_COLD F.Cu (31.05, 84.0) D120.1; PYRO1_CONT B.Cu (33.02, 52.9217) R168.1; PYRO1_CONT_MID F.Cu (28.95, 87.8) R129.1; PYRO1_GATE F.Cu (22.1, 92.4) R126.2†; PYRO1_OUT F.Cu (28.85, 91.73) Q124.5†; QSPI_CLK F.Cu (21.65, 33.35) U3.6; QSPI_IO0 F.Cu (20.4, 32.1) U3.5; QSPI_IO1 F.Cu (27.5, 34.6) U3.2; QSPI_IO2 F.Cu (27.5, 33.4) U3.3; QSPI_IO3 F.Cu (21.7, 34.6) U3.7; QSPI_NCS F.Cu (28.15, 35.95) U3.1; RAW_ACT B.Cu (4.0, 105.98) Q121.9; RAW_ACT B.Cu (9.0, 86.98) TP120.1; RAW_PROTECTED B.Cu (14.4, 40.325) R92.1; RAW_PROTECTED B.Cu (25.7, 27.25) C97.1†; RAW_PROTECTED B.Cu (35.7, 85.675) C71.1; RAW_PROTECTED B.Cu (35.7, 85.82) C71.1; RAW_PROTECTED B.Cu (38.175, 83.2) TP70.1†; RAW_PROTECTED B.Cu (38.5, 83.2) TP70.1†; RAW_PROTECTED F.Cu (14.0, 31.2) D9.1; SPI1_MISO B.Cu (34.79, 79.06) U4.1†; SW_NODE B.Cu (17.92, 35.65) C5.1; SW_NODE B.Cu (22.92, 34.05) L1.1; USB_LIMITED B.Cu (16.325, 81.55) U10.6; USB_LIMITED B.Cu (16.8, 81.55) U10.6; USB_LIMITED B.Cu (23.0, 60.5) TP82.1; USB_LIMITED B.Cu (33.1, 26.15) C98.1; USB_LIMITED F.Cu (16.725, 82.15) C86.1; VBUS B.Cu (6.9, 76.3) C28.1; VBUS B.Cu (13.55, 79.65) U10.3†; VBUS B.Cu (13.7, 81.55) U10.1; VBUS B.Cu (14.5, 72.53) R9.1; VLOGIC B.Cu (18.0, 32.35) U2.2; VLOGIC B.Cu (20.825, 31.85) C7.1; VLOGIC F.Cu (7.5, 55.65) C84.1; VLOGIC F.Cu (28.505, 29.85) C99.1; VLOGIC F.Cu (28.505, 29.85) C99.1

**right_angle** (41; † = new since the pass-2 board)
3V3 B.Cu (38.45, 56.75) ; 3V3 B.Cu (39.13, 54.19) ; 3V3 B.Cu (41.58, 54.5) ; 3V3 B.Cu (42.95, 54.5) ; 3V3 F.Cu (38.635, 77.92) ; 3V3_GNSS F.Cu (13.71, 20.75) †; ACT_FET_S B.Cu (5.17, 95.0) †; ACT_FET_S B.Cu (6.45, 95.0) ; ARM1_SENSE F.Cu (17.28, 94.15) ; BAT_IN F.Cu (9.3, 40.85) †; GND B.Cu (4.9883, 79.625) ; GND B.Cu (6.8, 75.5717) ; GND B.Cu (7.6317, 79.625) ; GND B.Cu (11.6, 82.5533) ; GND B.Cu (23.0, 99.5783) ; GND B.Cu (28.6, 31.6233) ; GND B.Cu (29.4, 48.6583) ; GND B.Cu (32.2, 28.1153) †; GND F.Cu (7.6317, 70.975) ; GND F.Cu (7.7217, 78.5) ; GND F.Cu (25.97, 86.75) ; GND F.Cu (34.9, 28.6) †; GND F.Cu (38.3, 28.3217) ; PYRO1_COLD F.Cu (29.335, 85.715) ; PYRO1_CONT F.Cu (26.83, 88.4217) ; PYRO1_CONT In2.Cu (32.42, 88.4217) ; PYRO1_GATE_N F.Cu (21.6, 89.5818) ; PYRO1_GATE_N In2.Cu (23.0, 86.03) ; PYRO1_GATE_N In2.Cu (30.2, 86.03) ; QSPI_IO3 F.Cu (21.3, 36.7) ; QSPI_IO3 F.Cu (21.3, 37.7) ; QSPI_IO3 F.Cu (22.5, 36.7) ; QSPI_IO3 F.Cu (22.5, 37.7) ; RADIO_RXEN F.Cu (18.35, 44.75) ; RAW_ACT F.Cu (11.4, 79.37) †; SPI1_SCK B.Cu (34.65, 81.65) †; USB_DM F.Cu (5.7, 74.55) ; USB_DM F.Cu (5.7, 75.55) ; USB_DM F.Cu (10.05, 75.55) ; USB_DP B.Cu (11.95, 77.05) ; VLOGIC F.Cu (31.355, 27.0) †

## Appendix B: reproduce

```
cd <scratch>/p3rg            # r7.kicad_pcb (= m3.kicad_pcb, SHA 7660620c…), r7.kicad_pro/.kicad_dru, p2.kicad_pcb, r6.kicad_pcb
PY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
$PY -I p3scan.py r7.kicad_pcb s3_r7.json          # independent scan (also p2/r6)
$PY -I <repo>/tools/route_check.py r7.kicad_pcb --report rc_r7.json
$PY -I probe.py r7.kicad_pcb 0.0 0.025            # GND via spots for the 14 allowlisted layer changes
$PY -I nudge.py r7.kicad_pcb 0.02 0.01            # existing-GND-via moves
$PY -I nudge_apply.py r7.kicad_pcb nudge/m3.kicad_pcb move   # then kicad-cli pcb drc / tools/check_r7.py / route_check
$PY -I cand3.py r7.kicad_pcb PYRO1_GATE_N F.Cu 0.2 "21.6,90.4 21.6,89.6647 21.9,89.3647 21.9,88.83"
```
