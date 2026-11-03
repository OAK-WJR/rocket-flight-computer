# R8 review pass 5: routing simplicity and geometry (whole board)

Reviewer: independent, read-only. Dimension: the geometry and simplicity of every track and via on all four layers,
rigid R7 copper included: AGENTS §3 rule instances, staircases, jogs and knees, local bumps, detours and extra vias, bus
tidiness, pad entries, width discipline, layer discipline (no signal on In1 / In2 except D70), and, for every remaining
exception, whether a DRC-clean edit removes it. This is a confirming pass on fix pass 4's board. Order: pass 4's two
routing findings, then fix pass 4's board diff against `c84f00b8…` (including a check that nothing else changed), then
the whole board.

- **Board reviewed:** `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
  `cc044ea0922ff826df19af9d9726d92c096ab2b127025b55d123d8772e5fb4a7`. The SHA and `git status --porcelain` (89 lines)
  were the same before and after this review.
- **Contents** (my scan `scan5.py`): 794 tracks, 609 vias, no arcs.
  - F.Cu: 408 tracks, 1,225.96 mm. Pass 4 had 1,225.71 mm; the +0.25 mm is the trio's three steps at +0.082 mm each.
  - B.Cu: 385 tracks, 857.81 mm. Pass 4 had 386 tracks and 859.67 mm; the −1.86 mm is USB_LIMITED's branch.
  - In2: 1 track, 3.4 mm (ARM1_SENSE at x 14.55, rigid, D70). **In1: none.**
  - Vias: 309 × 0.6 mm and 300 × 0.5 mm, all 0.3 mm drill, all through. GND: 428 (237 × 0.5, 191 × 0.6). Counts and
    sizes are the same as pass 4's.
- **Pass-4 board rebuilt for the diff:** `c84f00b8…` = HEAD's board plus the `m3.kicad_pcb` hunk of the coordinator's
  `r8_backup_c84f00b8/tracked.diff`. Its SHA-256 matched `c84f00b8…` exactly.
- **Gate:** I ran `tools/check.sh` on the repository board (KiCad Python): exit 0.
  - DRC 0, unconnected 0, parity 0, ERC 0. Metadata / 3D OK, silkscreen 0, R8 CAD contract OK, actuators OK, fit OK.
  - route_check: "0 failing, 3 allowlisted, … 0 removable local bumps on critical nets (22 bump windows searched): OK".
    It has 94 instances: pass 4's 93 plus one `width_change_junction` at the new USB_LIMITED T (32.2, 55.3), 0.25 /
    0.4 mm (`rcdiff.py`).
  - `check_r8`'s report equals pass 4's except for four things: the board SHA, fence openings [2] / [3] (now x 19.95–22.05
    and 22.05–24.15, both 2.10 mm), and `track_endpoints_checked` 1590 → 1588.
- **Tests:** `tools/test_route_check.py`, 57 tests, OK under KiCad's Python.
- **`step9/m2_sweep.py`** re-run on a copy. Its JSON output is **identical** to the recorded
  `step9/evidence/fix4_m2_sweep.json`:
  - chain_detour 23; adjacency 51 rows (26 net pairs, 7 at 0.150 mm); adjacency_pad 33.
  - via_step 1, poured_hop 2, routes 28, pad_edge 0, via_fold 26, short_hop 9.
  - bumps_all 1 (7 windows); margin_free 1 bump (29 windows) + 4 redraws.
- **Repository changes:** none except this file.
- **Scratch:** `<scratch>/r8p5rt/` (the session scratchpad), `<s>` below. The board copies were deleted at the end.

## 1. Verdict

**No Critical, no Major, no Minor.**

- **Pass 4's findings:** both are closed exactly as trialled (variant `rec4`), measured on the board (§3).
- **Fix pass 4's diff is what it should be:**
  - Copper: the three radio-trio lanes, USB_LIMITED's trunk and branch, and three GND vias each moved 0.05 mm.
  - Fill: the GND fill in those two windows changed, and so did the In2 3V3 plane's antipad round the moved stitch via.
  - Nothing else in the file changed: footprints, zone definitions, graphics and settings are identical.
- **No regression:**
  - None of my categories gained an instance.
  - The rg scan, route_check and the M2 sweep each changed only in the expected rows.
  - No new different-net pair under 0.35 mm involves the new copper, apart from RXEN at 0.300 mm from GNSS_RESET_N
    (the bus's own 0.5 mm pitch; it was 0.400 mm).
- **Whole board:**
  - It reads as deliberate, simple and logical.
  - Buses: the GNSS river, the radio bus (now centred in its fence openings), the servo, pyro-corridor, QSPI / IMU fans
    and SWD / USB lanes all run as parallel lanes at constant pitch. I read 20 tiles (24 × 26 mm, F and B separately).
  - The remaining exceptions (C11–C14, part E) are exactly the ones pass 4 dispositioned. My own searches found no
    DRC-clean edit that removes any of them.

## 2. Method

Every script is in `<s>/` and runs in KiCad 10.0.6's Python with the boards loaded read-only. Variant boards were not
needed: no candidate edit came up.

| Script | What it does |
|---|---|
| `scan5.py` | **Independent scan, written for this pass.**<br>- Per segment: angle off 0 / 45 / 90° by more than 0.01°, zero length, inner-layer tracks.<br>- Node graph per (net, layer), endpoints clustered at 1 µm. Each node is typed: pad (inside the pad's effective polygon), via (inside a same-net ring), tee (end on a same-net segment's body), fill-only, plain, junction or dangling.<br>- Acute pairs (under 90°) at every node.<br>- Chains between non-plain nodes: detour (over 1.25 × octile and over 0.5 mm), acute and right corners, knees (a heading regained after 1–2 segments, with middle length and offset), staircases, U-turns, interior segments under 0.5 mm.<br>- Same-net pairs: collinear or side overlap, crossing without a node, copper touch without a node.<br>- Vias: arms per layer, one-layer vias, off-centre arms, folds (≤ 45°), vias in SMD pads, via-to-via tracks, critical-net vias with no GND via within 1.5 mm.<br>- Widths and via sizes per net, width steps at plain nodes, pad entries ending more than 0.1 mm off centre.<br>- Different-net edge gaps under 0.2 mm (track, via, pad polygon, per layer). |
| `diff5.py` | Object diff of two boards: tracks, vias (with type, layers and lock), footprints (pose, FPID, attributes, fields, pads with zone connection, graphics), zones (settings, outline, fill area per layer), drawings, design settings |
| `sexpdiff.py` | Multiset diff of the files' top-level s-expressions, ignoring uuid / tstamp and `filled_polygon` |
| `filldiff.py` | XOR of every zone's fill between two boards: area and bounding box of each changed island; island counts |
| `par5.py` | Same-net, same-layer parallel runs within 1.5 mm laterally that overlap by more than 0.8 mm (doubled copper) |
| `padw.py` | Track ends wider than the pad they end in (track width against the pad's minor dimension) |
| `near.py`, `sdiff5.py` | Copper in a window; a category-by-category diff of two `scan5` outputs |
| reused | Pass 4's `gapnet.py` (different-net gaps for named nets, with `p4scan` helpers), `retap.py` (re-tap search), `render.py` + `qlmanage` (tiles and windows), `rcdiff.py`; `rgscan/scan.pyc` = the earlier reviewers' `rg/scan.py` (source gone; its `scan.cpython-39.pyc` run as passes 3 and 4 did); the repository's `m2_sweep.py` and `test_route_check.py` |

## 3. Previous findings in this dimension (pass 4)

| Pass 4 | Disposition (R8_VALIDATION, D110 / D111) | Checked on `cc044ea0…` | Closed? |
|---|---|---|---|
| R8P4-ROUTING-01: radio trio off-centre in its fence opening; MISO and MOSI 0.150 mm from the fence via and the stitch via | Fixed (D110) | Trio below the fence at x 20.5 / 21.0 / 21.5, 0.5 mm pitch. The step segments are (21.0, 22.0)→(20.5, 22.5), (21.5, 22.207)→(21.0, 22.707) and (22.0, 22.414)→(21.5, 22.914): one lane pitch, on parallel 45° lines 0.500 mm apart. The 45° runs to U1 stay on x − y = −9.9 / −9.193 / −8.486. GND vias at (19.95, 23.3), (22.05, 23.3) and (22.05, 26.7). RXEN, MISO and MOSI are each 0.200 mm from them (`gapnet.py`); they were 0.250 / 0.150 / 0.150 mm. The slot via sits exactly midway between MISO (21.5) and MOSI (22.6). Fence openings 1.75 (no lane), 2.10 and 2.10 mm (`check_r8` fence OK). | **Closed** |
| R8P4-ROUTING-02: USB_LIMITED's branch to R87.1 left C98.1 at 45° to the trunk and ran 2.55 mm back under it | Fixed (D111) | Trunk (31.25, 55.3)→(32.2, 55.3)→(34.35, 55.3)→(35.25, 56.2)→(35.25, 57.925), 0.4 mm. The branch is one T drop, (32.2, 55.3)→(32.2, 57.775), 0.25 mm, entering R87.1 (0603, 0.95 × 0.8 mm) axially from the north to its centre. Acute pairs 3 → 2; the remaining two are R133.1 and Q30.2, both rigid R7 copper. USB_LIMITED B.Cu 51.443 → 49.586 mm. The 1.65 mm same-net parallel run is gone (`par5.py` 6 → 5 pairs). `retap.py`'s R87.1 candidate (1.86 mm gain) is gone, and no new candidate appeared. | **Closed** |

## 4. Fix pass 4's board diff against `c84f00b8…`, item by item

### 4.1 What changed (and that nothing else did)

- **`diff5.py`: tracks and vias.**
  - 13 tracks removed and 12 added, on four nets: RADIO_RXEN, RADIO_BUSY, RADIO_MISO_MCU (3 / 3 each) and USB_LIMITED
    (4 / 3).
  - 3 GND vias moved: (20.0, 23.3) → (19.95, 23.3), (22.1, 23.3) → (22.05, 23.3) and (22.1, 26.7) → (22.05, 26.7).
    They keep 0.5 / 0.3 mm, are through and unlocked, as before.
  - USB_LIMITED gained no via.
- **`diff5.py`: everything else is identical.** 249 footprints (pose, FPID, fields, pads, zone connection, graphics);
  33 zones (settings and outlines; only F.Cu and B.Cu GND fill areas differ); 52 drawings; design settings.
- **`sexpdiff.py`:** the only top-level items that differ are those 13 / 12 segments and 3 / 3 vias. Every other item in
  the file is identical once uuids and fill polygons are set aside.
- **`filldiff.py`:** the fill changed only in three places.
  - F.Cu GND: −0.460 / +0.696 mm² inside x 20.11–22.13, y 21.85–30.01 (the trio window).
  - B.Cu GND: −0.369 / +1.245 mm² inside x 31.84–34.67, y 55.65–56.86 (the freed wedge at C98.1).
  - In2 3V3: ±0.050 mm² at x 21.55–22.60, y 26.2–27.2. The 3V3 plane's clearance ring round the stitch via
    (22.05, 26.7) moved west with the via. This follows directly from moving a through GND via under the In2 3V3 region;
    I note it because it is not strictly "GND fill". Its shape and area are unchanged.
  - Island counts are the same on every zone and layer.
- **Matches the brief:** only the two items' copper and the regenerated GND vias and fill differ.

### 4.2 The radio trio (R8P4-ROUTING-01)

- **Geometry:** as in §3, render `<s>/img/trio_r8.svg.png` (and `trio_p4` for the old one).
  - Each lane is still one mitred step, a straight run, one 45° run and a square module-end corner.
  - The step is now exactly one lane pitch (0.5 mm), so the trio's knee reads as a one-pitch shift. It was a 0.4 mm
    odd-pitch shift.
  - The rg scan's `dogleg` rows for the trio change only in their numbers: middle 0.566 → 0.707 mm, step 0.40 → 0.50 mm.
  - Net lengths +0.082 mm each: RXEN 40.106, BUSY 32.092, MISO_MCU 27.982 mm.
- **Clearances** (`gapnet.py` at 0.35 mm, both boards):
  - Four rows left the list: MISO / MOSI against (22.1, 23.3) and (22.1, 26.7), all 0.150 mm. The new values are
    0.200 mm.
  - One row joined it: RXEN at x 20.5 is 0.300 mm from GNSS_RESET_N's x 20.0 lane and its 45° end
    (20.0, 31.65)→(20.0, 27.0)→(19.4, 26.4). This is 0.5 mm centre to centre, the bus pitch; it was 0.400 mm with RXEN
    at x 20.6. RXEN now runs at the same pitch as its neighbour, which is tidier, not a defect.
  - MISO's step is 0.312 mm from (22.05, 23.3); it was 0.347 mm.
  - Nothing else within 0.35 mm changed.
- **Bus tidiness through the fence row (y 23.3):** the trio has 0.200 mm on each side of its opening. MOSI and NSS
  (x 22.6 / 23.2) have 0.200 and 0.600 mm in theirs. SCK (25.1) is 0.600 / 0.550 mm from its vias. Every lane crossing
  the row has ≥ 0.2 mm, and the openings are 1.75–2.10 mm, within D16's 2.7 mm.

### 4.3 USB_LIMITED's R87.1 T (R8P4-ROUTING-02)

- The T is drawn as a split trunk: a plain three-way junction at (32.2, 55.3), now one of 39 on the board. This is the
  board's convention for a T.
- The width step 0.4 → 0.25 mm at the T is the allowed `width_change_junction` (C19 / part E now count 15). A 0.25 mm
  branch is the board's convention for a sense or divider tap: the OVLO divider draws microamps.
- No different-net copper within 0.35 mm of the drop. The nearest are the trunk's existing neighbours: the
  RAW_ACT_SENSE lane (x 30.65) is 0.300 mm from the trunk segment (31.25–32.2, 55.3) and 0.200 mm from the hop via
  (31.25, 55.3). Both are unchanged; pass 4's §3 measured them.
- B.Cu −1.86 mm (B.Cu total 859.67 → 857.81 mm). `retap.py` lists no cheaper tap for R87.1 or C98.1 (its two new rows
  are the trunk's own neighbours, gain 0).

### 4.4 The three GND vias

They sit in `r8_ground.tsv` at their new coordinates, 0.5 / 0.3 mm as before. `fix4_generators.diff` shows those three
rows plus one cover row reordered (same coordinates). No other GND via on the board moved, appeared or disappeared, so
step 7 placed nothing new in the freed B.Cu, as D111 says.

## 5. Whole-board scans

### 5.1 Independent scan (`scan5.py`), `c84f00b8…` → `cc044ea0…`

| Category | `c84f00b8…` | `cc044ea0…` | Notes |
|---|---:|---:|---|
| off-angle / arcs / zero-length | 0 / 0 / 0 | 0 / 0 / 0 | |
| inner-layer track | 1 | 1 | ARM1_SENSE In2 (14.55, 94.15–97.55), D70, rigid |
| dangling end / one-layer via | 0 / 0 | 0 / 0 | |
| collinear or side overlap (same net) | 0 | 0 | |
| crossing without a node | 6 | 6 | all six are Ts (an end on the other segment's body): 3V3 (36.75, 70.4), GNSS_ANT_DC (11.45, 6.18), PYRO1_BUS (16.17, 95.36), 3V3A (26.5, 53.7), CAM_5V (40.75, 43.17) and CAM_SW (39.95, 37.61), the last two ending inside pads; = pass 4's six Ts |
| copper touch without a node | 10 | 10 | two tracks of one net meeting inside one pad (C100.1, C72.2 / C73.1, C83.2, C75.1 / L3.2) or rigid R7 copper (PYRO1_OUT at Q124.5, 3V3_GNSS at C301.1); = pass 4's list |
| plain three-way junctions | 38 | 39 | + USB_LIMITED (32.2, 55.3), the new T |
| acute pair at a node | 3 | **2** | − C98.1 (USB_LIMITED); left: R133.1 (ARM1_SENSE) and Q30.2 (GNSS_ANT_SRC), rigid |
| right-angle corners | 58 | 58 | same corners (the trio's square module-end corners re-measured) |
| knees | 51 | 51 | the trio's six change only in their numbers (§4.2) |
| staircases | 0 | 0 | |
| U-turns (cumulative 180°) | 9 | 9 | route_check's 7 plus C11 #2 (BAT_ENABLE) and #4 (PYRO1_CONT's corridor) |
| chain detours | 23 | 23 | = C11, run for run |
| interior segments < 0.5 mm | 2 | 2 | RADIO_TXEN's rigid 0.424 mm mitres |
| via folds (non-GND, any layer pair) | 27 | 27 | C14's 26 + the rigid ARM1_SENSE via (18.18, 91.3), whose In2 arm C14 does not count |
| via-to-via tracks | 7 | 7 | 3V3 hop (D40), 3V3A hop, VBUS spine, USB_LIMITED hop; rigid GND 0.9 mm and ARM1_SENSE (0.2 mm F.Cu step in its ring, and In2) |
| off-centre via arm / via in SMD pad | 2 / 1 | 2 / 1 | ARM1_SENSE (18.18, 91.3) rigid; TP122.1's PYRO1_GATE (A8, rigid) |
| critical-net via, no GND via within 1.5 mm | 1 | 1 | PYRO1_GATE (20.45, 92.4), A8 (2.717 mm) |
| width step at a plain node | 1 | 1 | CAM_INPUT_LIMITED (35.0, 31.65), U7.5's pad-entry neck (U7.6 is another net 0.5 mm away) |
| end in a fill only | 1 | 1 | BAT_IN (41.25, 102.4), the pour stub |
| pad entries ending > 0.1 mm off centre | 60 (46 pads) | 60 (46 pads) | identical entry for entry |
| different-net gaps < 0.2 mm, track / via | 55 | **51** | − the four MISO / MOSI rows; = m2_sweep adjacency 51 rows, 26 net pairs, 7 at 0.150 mm |
| different-net gaps < 0.2 mm, pad rows | 33 | 33 | = C12b + the 4 counted fine-pitch rows |

`sdiff5.py` (category by category, item by item): besides the rows named above, the only differences are rows reordered
by segment order (the 3V3A and CAM_SW Ts, CAM_5V / CAM_INPUT_LIMITED touches, the VLOGIC and 3V3A right corners), with
identical content.

### 5.2 `rgscan/scan.pyc` (the earlier reviewers' scan)

Counts on `cc044ea0…`: acute_at_padvia 2, chain_detour 23, collinear_unmerged 1, dogleg 39, end_in_zone_only 1,
extra_bends 4, net_length 67, off_angle_rounding 5 (≤ 0.00014°, 0 µm lateral), pad_end_offcentre 85,
pad_entry_diagonal 52, passes_through_pad 8, right_angle_corner 58, segment_inside_pad 7, short_layer_hop 2,
short_segment 2, u_turn 7, width_change_at_pad 11, width_change_at_via 4, width_change_free 11.

Diffed against pass 4's `rg.json` (segment ids ignored), only these rows changed:
- **Removed:** acute_at_padvia and width_change_at_pad at C98.1.
- **Added:** width_change_free at (32.2, 55.3).
- **Re-measured:** six trio `dogleg` rows and two `net_length` rows. RADIO_BUSY's route ratio went 1.192 → 1.195 and
  RADIO_MISO_MCU's 1.043 → 1.046.

### 5.3 Widths, via sizes, layers

- **Width histogram** (track count by width): 0.15 (8), 0.2 (559), 0.25 (56), 0.3 (84), 0.4 (33), 0.45 (3), 0.5 (32),
  0.6 (13), 0.7 (1), 0.8 (4), 1.0 (1).
- **Signal nets:** all 0.2 mm except the 0.25 mm actuator-gate / BAT_SW / CAM_FB family, the 0.3 mm RF lines, and
  0.15 mm on rigid RADIO_TXEN and one rigid PYRO1_CONT piece.
- **Power nets:** each width matches its D-number. Steps occur only at pads, vias and Ts, plus U7.5's neck.
- **Via sizes:** unchanged. 0.5 mm for signals and step 7, 0.6 mm for power. Seven R8-new signal vias are 0.6 mm
  (pass 4 §5.3 / §9): SERVO1–4_MCU's T-vias, CAM_FB and ACT_GATE × 2.
- **Layers:** In1 carries no track. In2 carries only D70's rigid 3.4 mm. Every critical-net layer change has a GND via
  within 1.5 mm except A8.

### 5.4 Adjacency

- **Track / via pairs** (`m2_sweep adjacency` = my scan): 26 net pairs under 0.2 mm, 7 of them at 0.150 mm. This equals
  R8_VALIDATION C12, renumbered 1–26.
- **The seven 0.150 mm pairs:** four U1 escape vias on their own pin row beside the neighbour pin's lane (#1, #2, #4,
  #6), U12's (#3) and U4's (#5, #7). All are bound by pad pitch.
- **Pad rows:** 33, equal to C12b plus the 4 counted fine-pitch rows.

## 6. Topic by topic

- **Knees, jogs, staircases:** no staircase. No knee with a middle segment under 0.5 mm, apart from RADIO_TXEN's rigid
  0.424 mm mitres (`short_interior`).
- **The sub-1 mm knees** are the list passes 3 and 4 dispositioned, each with its cause; I re-checked the cause where I
  could see it:
  - Radio trio: 0.50 mm offset (was 0.40).
  - RADIO_DIO1: 0.45 mm at (32.4→32.85, 30.45–30.9). It must clear RADIO_SCK_MCU's x 32.25 lane (y 37.85–41.0) before
    pin 45; I measured this.
  - SWCLK 0.50, QSPI_IO3 0.50 (C14), RADIO_SCK 0.60, QSPI_IO0 0.63, CAM_MCU_TX 0.75 mm.
- **Detours, folds, extra vias:** C11's 23 runs, C14's 26 folds and C13's 12 nets over need (none over need + 2) are
  unchanged.
  - The margin-free search finds only part F's BAT_ENABLE false positive (its candidate skips TP84.1 / C87.1, which the
    net must pass through) and C11's four "found" redraws (#20–#23), each recorded as not simpler.
  - `retap.py`'s remaining real candidates are pass 4's, all blocked or not better: VBUS → R9.1, U11's IN1 feed, VLOGIC
    → TP83, and the C11 runs round PYRO_BLOCK and the rigid strip.
- **Same-net parallel runs** (`par5.py`, 5):
  - 3V3A's two U1 pins (26.5 / 27.0, 52.55) joined by a T below the pad row.
  - The rigid 3V3_GNSS U30.7 / U30.8 (C11 #21).
  - USB_DM's inner U and USB_DP's tee (C11 #13 / #22, D53).
  - VLOGIC's two branches from U2.3 and U2.2 (y 65.65 to C7.1, y 66.6 to the C84 / TP83 via; C14's T).
  - Each joins two pins of one net or serves two different loads. None is doubled copper.
- **Pad entries:** identical to pass 4 apart from R87.1's, which is axial to the centre.
  - `padw.py` lists the track ends wider than their pad's narrow side. All are power entries along the pad's long
    axis to its centre: RAW_PROTECTED 0.5 mm into U7.4 (0.25 mm wide; U7.3 beside it is the same net), SW_NODE 0.8 mm
    into U2.5 (0.55 mm; 0.275 mm from U2.4 / U2.6), VLOGIC 0.5 mm into U11.1 (0.4 mm; 0.25 mm from U11.2's copper).
    Rigid Q124 (GND 0.45 / PYRO1_OUT 0.6 mm) is the same pattern.
  - The overhang lies wholly under the solder mask: the pads' effective mask expansion is 0 (board
    `pad_to_mask_clearance 0`, no local margin on U7 / U2 / U11), so the solderable land stays the pad itself.
  - Where the neighbour pin is another net, the generator necks instead (U7.5 → 0.25 mm, because U7.6 is 0.5 mm away).
    That is consistent and deliberate. Noted, no finding.
- **Bus tidiness:** improved. The radio trio now sits centred in its opening, and its lanes run at the same 0.5 mm pitch
  as GNSS_RESET_N beside them.

## 7. Remaining exceptions: does a DRC-clean edit remove them?

- **C11 (23 runs):** `margin_free`'s four "found" rows are not simpler; the other 19 have no 1–3 segment redraw. No
  copper of these runs changed, so pass 3's 4-segment search still covers them.
- **C12, the seven 0.150 mm pairs:**
  - Each needs a via off its pin row (a jog), a moved lane under U1's pad row, or a smaller via than the board's
    0.5 mm. That is pass 4's §7 reasoning, which I re-derived for #4. CAM_MCU_TX's lane must cross RX's pin row
    east of RX's hop via, so the via cannot move east, and y ≠ 45.5 means a jog.
  - #2 stays whatever the via's x: FAULT_N's F.Cu lane passes under PWR_EN's via on pin 42's row, and its B.Cu x 32.35
    lane runs 0.5 mm from the via.
  - Not removable cheaply; unchanged.
- **C12b:** no pad or copper there changed. Pass 3's trials still apply (R166 0.025 mm; R120.2's via gains nothing
  against the pour).
- **Acute pairs:** the remaining two are rigid R7 copper.
- **C14, E:** unchanged except E's new `width_change_junction`, which is the allowed category. Pass 4 judged the
  trade (one information instance against a wedge, a corner, 1.86 mm and a doubled run) a gain, and I agree.

## 8. Findings

None. No Critical, Major or Minor.

## 9. Notes (no finding)

- **In2 3V3 antipad.** Moving the stitch via (22.05, 26.7) moved the In2 3V3 plane's clearance ring with it (±0.05 mm²).
  The brief allowed only "GND fill / vias" to differ, but this change is a direct consequence of the GND via move.
  Nothing else on In2 changed.
- **C19 wording (records nit).** C19's width_change_junction reason ends: "equal widths would put the wide width into a
  narrow pad (a gated neck-down) or narrow the trunk". Two parts of this are loose:
  - route_check gates a neck only when it lies more than 1 mm from the pad (`neck_down`'s pad-entry exception,
    `tools/route_check.py` l. 67–69).
  - For the new R87.1 T a 0.4 mm drop would fit R87.1's 0.95 × 0.8 mm pad with no neck at all.
  - The width is really set by C19's first reason, "each width set by its own load" (a divider tap), which is correct.
  - Too small to list as a finding. It could be tidied at the next records pass.
- **0.6 mm signal vias:** unchanged since pass 4 (§5.3). None has foreign copper within 0.3 mm, so a smaller ring would
  gain nothing.
- **Not re-run:** the DC solves, the scorecard, the reference audit and the fab package. Fix pass 4's evidence covers
  them, and my M2 sweep output is byte-for-byte the recorded one on the same SHA.

## Appendix: reproduce

```
cd <scratch>/r8p5rt
PY=<KiCad 10.0.6 python3>; R=<repo>
cp $R/m3_design/assembly_review/m3.kicad_pcb r8.kicad_pcb                 # cc044ea0…
# p4.kicad_pcb = c84f00b8…: `git show HEAD:m3_design/assembly_review/m3.kicad_pcb` into a/m3_design/assembly_review/,
# then `git apply` the m3.kicad_pcb hunk of ../r8_backup_c84f00b8/tracked.diff (SHA-256 checked)
KICAD_PY=$PY $R/tools/check.sh                                            # exit 0
$PY -I diff5.py p4.kicad_pcb r8.kicad_pcb; python3 sexpdiff.py p4.kicad_pcb r8.kicad_pcb
$PY -I filldiff.py p4.kicad_pcb r8.kicad_pcb
$PY -I scan5.py r8.kicad_pcb s5.json; $PY -I scan5.py p4.kicad_pcb s5_p4.json; python3 sdiff5.py s5_p4.json s5.json
$PY -I gapnet.py r8.kicad_pcb 0.35 RADIO_RXEN,RADIO_BUSY,RADIO_MISO_MCU,RADIO_MOSI,USB_LIMITED 17 20 36 60
$PY -I par5.py r8.kicad_pcb 1.5 0.8; $PY -I retap.py r8.kicad_pcb 0.8; $PY -I padw.py r8.kicad_pcb
(cd rgscan && $PY scan.pyc ../r8.kicad_pcb ../../p8rt/r7.kicad_pcb rg.json)
$PY -I $R/m3_design/assembly_review/sources/r8_design/step9/m2_sweep.py r8.kicad_pcb --json m2.json
python3 ../r8p4rt/rcdiff.py ../r8p4rt/route.json route.json             # route_check vs pass 4
(cd $R/tools && $PY -m unittest test_route_check)                         # 57 OK
```
