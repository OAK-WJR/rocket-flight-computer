# R8 review pass 3: routing simplicity and geometry (whole board)

Reviewer: independent, read-only. Dimension: the geometry and simplicity of every track and via on all four layers, rigid
R7 copper included: AGENTS §3 rule instances, staircases, jogs and knees, local bumps, detours and extra vias, bus
tidiness, pad entries, width discipline, layer discipline (no signal on In1 / In2 except D70), adjacency, and, for every
remaining exception, whether a DRC-clean edit removes it. First the four pass-2 routing findings are re-checked, then fix
pass 2's copper changes, then the whole board.

- **Board reviewed:** `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
  `990c8040c5b8457bd2bd1717ed3e5c2725f32c1dda1cd7f826a0c2b458d28b18`. The SHA and `git status` were the same before and
  after this review.
- **Contents** (my scan): 795 tracks, 609 vias, no arcs.
  - F.Cu: 408 tracks, 1,225.7 mm. B.Cu: 386 tracks, 861.7 mm.
  - In2: 1 track, 3.4 mm (ARM1_SENSE at x 14.55, rigid, D70). **In1: none.**
  - Vias: 310 × 0.6 mm and 299 × 0.5 mm, all 0.3 mm drill, all through. GND: 428 (237 × 0.5, 191 × 0.6).
  - Copper identical to R7 (`c872a3d3…`, matched by net, layer, width and end points): 97 tracks; 189 vias also at R7's
    size (pass 2's figures, unchanged).
- **Fix pass 2's copper diff** (`6600ef94…` → `990c8040…`, pass 2's `diff.py`): 3 tracks removed and 4 added, 6 vias
  removed and 8 added, on 3 nets (§4).
- **Gate on this board** (`tools/check.sh`, run by me, exit 0): DRC 0, unconnected 0, parity 0, ERC 0; metadata / 3D OK;
  silkscreen 0; R8 CAD contract OK; route_check "0 failing, 3 allowlisted, … 0 removable local bumps on critical nets (22
  bump windows searched): OK"; actuators OK; fit OK.
- **Tests:** all 17 suites in `tools/` under KiCad's Python, 272 tests, OK.
- **`step9/m2_sweep.py`** re-run by me on a copy of the board: chain_detour 23, adjacency 54 rows (29 net pairs, 10 at
  0.150 mm), adjacency_pad 36 (32 listed), via_fold 26, routes 28 (12 over need), pad_edge 0, short_hop 9, bumps_all 1.
  Each equals R8_VALIDATION C11 / C12 / C12b / C13 / C14 / part F, row for row.
- **Repository changes:** none except this file.
- **Scratch:** `<scratch>/r8p3rt/` (the session scratchpad), called `<s>` below. Variant boards were written only under
  `<s>/v/<name>/` in a copy of the project and deleted after their results were logged (`<s>/logs/`).

## 1. Verdict

The R8 routing still reads as deliberate, simple and logical, and fix pass 2 closed all four pass-2 routing findings
without breaking that:
- **Segments:** no off-angle segment, arc, zero-length piece, staircase, exposed acute angle, stub, dangling end or via,
  same-net crossing without a node, collinear or side-by-side overlap. The shortest interior segment of any new chain is
  still 0.566 mm.
- **Buses:** the GNSS river, the radio bus, the servo bus, the pyro corridor, the QSPI / IMU fans and the SWD / USB lanes
  are unchanged parallel lanes at constant pitch.
- **Width and layers:** unchanged per-net width families; In1 carries no track, In2 only D70's rigid 3.4 mm.
- **Fix pass 2's edits** (R81 on a stub, C83.2's split link, four 0.5 mm vias, three step-7 vias) are clean (§4).

**No Critical and no Major.** No AGENTS §3 rule instance is new, and no critical net carries messy routing that a clean
edit removes: the gate's own bump search, my 4-segment redraw search and a margin-free run of the gate's searches find
nothing simpler on any critical net (§7).

Three Minor findings, all cheap and worth fixing. Each is an exception the record keeps ("pinned", "not cheap to open",
"not removed yet", "no redraw") that a DRC-clean, gate-clean edit of one or two numbers removes:

- **R8P3-ROUTING-01.** USB_LIMITED (5 V) runs 0.150 mm from CAM_PWR_EN (C12 #5) and 0.180 mm from both bare pads of R172,
  the 4.7 kΩ in series with PB0 (C12b #20 / #21). A 0.05 mm shift of the trunk and of R172 opens all three to ≥ 0.20 mm.
- **R8P3-ROUTING-02.** R165's BAT_ENABLE via is drawn with the 0.6 mm power via, 0.180 mm from Q120's bare BAT_IN drain pad
  (C12b #18, the latch class). The board's 0.5 mm signal via (same drill), already used for the net's other via, opens it
  to 0.23 mm. This is D98's one-argument fix again.
- **R8P3-ROUTING-03.** CAM_PWR_EN's lower leg (C11 #5) has a DRC-clean 3-segment redraw 1.98 mm shorter, ending in one 45°
  run into R74.1. The gate and the sweep miss it because RedrawCheck tests every candidate at the rule + 0.01 mm, so a
  candidate that keeps an existing 0.150 mm leg always fails.

The four recommended edits together (variant `rec`) are DRC 0 / 0 / 0 with parity, and route_check is identical except
one T's coordinate. check_r8 and check_actuators pass. In the M2 sweep:
- track / via net pairs under 0.2 mm go 29 → 28, and 0.150 mm pairs 10 → 9;
- pad rows go 36 → 33;
- CAM_PWR_EN's chain detour goes 22.12 → 20.15 mm;
- bumps_all still shows only the known BAT_ENABLE false positive.

The step-7 GND via 0.180 mm from R120.2 (ACT_GATE), fix pass 2's pass-3 candidate, is **not** worth moving: the B.Cu GND
pour already sits 0.1505 mm from R120.2 and C120.2 (§9).

## 2. Method

Every script is in `<s>/` and runs in KiCad 10.0.6's Python with boards loaded read-only. Variants were written only
under `<s>/v/`.

| Script | What it does |
|---|---|
| `p3scan.py` | **My independent scan, written for this pass.**<br>- Union-find node graph per (net, layer) at 1.5 µm, nodes typed pad / via / T (incl. ends on a body) / fill / dangling.<br>- Per segment: off-angle, zero length, inner-layer track, off-grid ends.<br>- Per (net, layer) pair: collinear and side-by-side overlaps, crossings without a node.<br>- Chains between non-plain nodes, and for each: detour (> 1.25 × octile and > 0.5 mm), knees (a return to an earlier heading within four segments), U-turns (≥ 179° same-sense), staircases, right angles, short interior and end segments.<br>- Acute pairs at plain, pad, via and T nodes.<br>- Vias: layers joined, folds, off-centre arms, via-to-via tracks, vias in SMD pads, the nearest GND via.<br>- Pad entries: offset, lateral offset, axial or not, exit point's distance to a pad corner.<br>- Per-net widths. R7-identical copper tagged |
| `../r8p2rt/p2scan.py`, `../r8p2rt/gaps.py`, `../r8p2rt/threads.py`, `../r8p2rt/diff.py`, `../r8p2rt/near.py` | Pass 2's scan, adjacency (track / via / pad, 0.2 and 0.3 mm), two-pad threading, copper diff and point query, re-run as cross-checks |
| `../rg/__pycache__/scan.cpython-39.pyc` | The earlier reviewers' `rg/scan.py`. Its source is gone; the cached bytecode was run as `scan.pyc` (R8 against R7, so its era columns are meaningless) |
| `corridor.py`, `zgap.py`, `gvact.py`, `thtx.py`, `tht_near.py`, `fp.py`, `zat.py` | Copper within d of a track, pad to zone-fill edge distance, GND via to named-net copper, layer changes through THT pads, courtyard to THT pads (R5 L10), footprint pads, zones at a point |
| `alt4.py` | 4-segment redraw search for every C11 run up to 7 mm, using route_check's own `alt_window`, `path_defects` and `RedrawCheck` (normal and strict), 0.05 mm bend grid |
| `bump0.py` | route_check's `bump_audit` (every net) and `alt_audit` (C11) with `r7_hygiene.rule_clearance` less 0.0105 mm, i.e. at DRC's own threshold |
| `variant.py`, `vrun.sh`, `rcdiff.py` | Pass 2's tools: apply an edit list to a copy of the board in a copy of the project, refill natively, then run `kicad-cli pcb drc --severity-all --schematic-parity`, `route_check --profile r8`, `check_r8` and `check_actuators`, and diff route_check instances against `base` (no edit). `base` gives DRC 0 / 0 / 0 and the gate's route_check result, so the refill reproduces the board |
| `render.py` | SVG of a window (F red, B blue, In2 green, pads, vias, fills), rasterised with `qlmanage` |

I rendered the whole board in 24 tiles of 16 × 16 mm, plus close-ups of the R81 / U9 area, C83 / U10, R120 / C120, C98,
Q123, J123, CAM_PWR_EN and the variants, and read each one.

## 3. Previous findings in this dimension (pass 2)

| Pass 2 | Disposition (R8_VALIDATION) | Checked on `990c8040…` | Closed? |
|---|---|---|---|
| R8P2-ROUTING-01: four 0.150 mm pairs open with a 0.5 mm via | Fixed (D98) | Vias (41.4, 47.8), (33.9, 45.2), (41.45, 32.6) GND and (35.25, 60.5) RAW_PROTECTED are 0.5 / 0.3 mm. Each is now 0.200 mm from CAM_5V, CAM_MCU_TX, the trunk and VLOGIC. C12's 0.150 mm pairs: 10, pairs under 0.2 mm: 29 (my `gaps.py` and `m2_sweep`) | **Closed** |
| R8P2-ROUTING-02: BAT_IN threads R81's pads at 0.170 / 0.180 mm | Fixed differently (D100) | R81 (39.6, 91.275, 90, B) on a 0.82 mm stub from the spine T at (40.42, 92.1); `threads.py` lists no part straddling BAT_IN. The feed's smallest gap to another net is 0.200 mm (U9.2, the RAW_PROTECTED stub). The stub enters R81.1 along its axis to the centre. The step-7 vias (38.85, 91.3) and (42.9, 91.45) are ≥ 0.235 mm from foreign copper | **Closed** |
| R8P2-ROUTING-03: sweep and C12 omit track / via-to-pad gaps | Fixed (D104) | `m2_sweep adjacency_pad`: 36 rows, the same as my `gaps.py` pad rows, pair for pair (4 fine-pitch own-part rows counted, 32 listed) | **Closed** (three of the "not removed yet" rows have a cheap fix: R8P3-ROUTING-01 / -02) |
| R8P2-ROUTING-04: 0.247 mm jog inside C83.2 | Fixed differently (D99) | B.Cu (11.1, 35.4) → (9.55, 35.4) ends in C83.2, 0.175 mm off its centre; the link (9.55, 35.225) → (9.55, 34.35) → (9.0, 33.8) leaves from the centre. No segment under 0.5 mm; route_check: one pad_end_offcentre C83.2 0.175 mm (E). Visually an L whose corner lies inside the pad | **Closed** |

## 4. Fix pass 2's copper changes, one by one

| Net | Change | Judgement |
|---|---|---|
| BAT_ENABLE | Spine x 40.42 split at (40.42, 92.1); stub (40.42, 92.1) → R81.1 (39.6, 92.1) | Clean: a T and a 0.82 mm axial stub, both 0.2 mm; no collinear overlap |
| GND (C83 / U10.2) | (9.725, 35.4) jog removed; U10.2 → (9.55, 35.4) | Clean (§3) |
| GND, RAW_PROTECTED | Four vias 0.6 → 0.5 mm in place | Clean (§3). RAW_PROTECTED now has 0.6 and 0.5 mm vias, and GND gains three more 0.5 mm ones; GND already mixed both sizes, so this is no discipline issue |
| GND (step 7) | (39.0, 91.3) → (38.85, 91.3); (43.0, 91.5) → (42.9, 91.45); new (13.5455, 74.2255) (island B) and (44.65, 86.775) (pad U9.8) | No new adjacency under 0.3 mm. The island via's coordinates are off the 0.025 mm grid (cosmetic) |

## 5. Whole-board scans

### 5.1 Independent scan (`p3scan.py`; new / rigid)

| Category | New | Rigid | Notes |
|---|---:|---:|---|
| off-angle (> 0.005°) / arcs / zero-length | 0 / 0 / 0 | 0 | `rg/scan.pyc`'s 5 "off_angle_rounding" are ≤ 0.00014° with 0 µm lateral error |
| collinear or side-by-side overlap / crossing without a node | 0 / 0 / 0 | 0 | |
| interior chain segment < 0.5 mm | 0 | 2 | TXEN's rigid 0.424 mm mitres |
| track end on a same-net track body | 4 | 2 | 3V3 (36.75, 70.4), 3V3A (26.5, 53.7), CAM_5V (40.75, 43.17), CAM_SW (39.95, 37.61); ordinary T joints, as in pass 2 |
| fill-only end / dangling end | 1 / 0 | 0 | BAT_IN B.Cu (41.25, 102.4) in its own pour (pour_stub gate) |
| acute pair at a node | 2 | 1 | Q30.2 (GNSS_ANT_SRC); C98.1 (USB_LIMITED T: the 0.4 mm diagonal and the 0.25 mm R87 branch meet at 45°, with the wedge apex 0.037 mm inside the pad edge, so route_check's rule holds); rigid R133.1 |
| right-angle corners | 56 | 3 | allowed by AGENTS §3 |
| knees | 57 | 1 | as pass 2 (§6.1) |
| U-turns | 6 | 2 | PYRO1_CONT corridor, 3V3A at U4, CAM_PWR_EN, USB_DM, SPI1_SCK, BAT_ENABLE; rigid TXEN, PYRO1_CONT |
| chain detours (> 1.25 ×, > 0.5 mm) | 20 | 3 | = C11, run for run |
| via folds | 21 | 5 | = C14's 26 |
| via-to-via tracks | 4 | 2 | 3V3 hop (D40), 3V3A hop, VBUS spine, USB_LIMITED hop; rigid ARM1_SENSE In2 and GND 0.9 mm |
| step inside a via / off-centre via arm | 0 | 1 / 1 | ARM1_SENSE (18.18, 91.3), rigid |
| critical-signal via without a GND via within 1.5 mm | 0 | 1 | A1 (PYRO1_GATE in TP122, the one via in an SMD pad) |
| critical-signal layer change through a THT pad (`thtx.py`) | 0 | 0 | no THT pad carries one net's tracks on two layers |
| width step at a plain node | 1 | 0 | CAM_INPUT_LIMITED (35.0, 31.65), U7.5's neck (E) |
| inner-layer track | 0 | 1 | C1 |

### 5.2 Adjacency

- **Track / via pairs** (`gaps.py` = `m2_sweep adjacency`): 29 net pairs under 0.2 mm, 10 at 0.150 mm. This equals C12.
- **Pad / copper rows:** 36, equal to C12b. My additions to that list:
  - **USB_LIMITED / MCU-pin nets:** C12 #5 (0.150 mm) and C12b #20 / #21 (0.180 mm) open with 0.05 mm shifts (R8P3-ROUTING-01).
  - **BAT_ENABLE via / Q120.9:** C12b #18 (0.180 mm) opens with the signal via (R8P3-ROUTING-02).
  - **Zone fills:** the outer GND pours keep 0.15 mm (zone clearance 0.15 on F / B; 0.25 on In1 / In2; 0.3 on the BAT_IN,
    RAW_ACT and ACT_FET_S pours). So a C12b row whose foreign net is GND is usually no closer than the pour beside the
    same pad. Two examples (`zgap.py`): R120.2 and C120.2 have GND fill at 0.1505 mm, and R166.1 at 0.1505 mm. Rows
    against non-GND copper (5 V, BAT_IN, RAW_PROTECTED) are the ones where a track or via is the nearest foreign copper of
    its class.

### 5.3 Widths, vias and layers

Unchanged from pass 2:
- **Widths:**
  - signals 0.2 mm;
  - actuator gate family, BAT_SW_* and CAM_FB 0.25 mm;
  - limiter 0.25 / 0.2 mm;
  - RF 0.3 mm;
  - rigid TXEN and one PYRO1_CONT piece 0.15 mm;
  - power nets per their D-numbers.
- **Width steps** only at pads, vias and T nodes, plus U7.5's neck.
- **Via sizes:** 0.5 mm for signals and step 7, 0.6 mm for power. The one exception is the BAT_ENABLE via (16.6, 104.5),
  a µA signal on the 0.6 mm power via while its other via (40.42, 93.5) is 0.5 mm (R8P3-ROUTING-02).
- **Layers:** In1 no track; In2 only D70's.

## 6. Topic by topic

### 6.1 Knees, jogs and staircases

No tiny jog (middle < 0.5 mm or offset < 0.25 mm) and no staircase. The sub-1 mm knees are pass 2's list, unchanged, each
with its recorded cause:
- radio trio RXEN / BUSY / MISO 0.40 mm;
- RADIO_DIO1 0.45 mm;
- SWCLK 0.50 mm;
- QSPI_IO3 0.50 mm;
- RADIO_SCK 0.60 mm;
- QSPI_IO0 0.63 mm;
- CAM_MCU_TX 0.75 mm.

The gate's bump search covers every critical one, with and without its margin (§7).

### 6.2 Folds, detours and extra vias

- C14's 26 folds are confirmed: the same vias and arms.
- C13's 12 nets with vias over their need are confirmed (`routes`): none is over need + 2, and no via sits on a one-layer
  run.
- C11's 23 chain detours are confirmed; their redraws are in §7.

### 6.3 Bus tidiness

Unchanged and good: nested lanes at constant pitch in the GNSS river (0.6 mm), the radio bus, the servo bus (0.5 mm), the
pyro corridor, the QSPI dive and the IMU fan. Fix pass 2 touched no bus.

### 6.4 Pad entries

- **Counts:** 550 new entries. 51 are non-axial, nearly all ending at the pad centre. 42 end more than 0.1 mm off centre:
  the 41 route_check instances in E, plus the U9.1 spine end 0.18 mm off. That end is also in E: the spine is pinned
  between R82's pads.
- **Corner exits:** 26 diagonal entries leave their pad within 0.05 mm of a corner vertex. Examples: R83.1, R84.1, R87.2,
  C85.1, R90.1, R91.2, C120.2 (pass 2 §9). Each is a 45° run into the pad centre, which route_check counts as tidy; it is
  a drawing style, not an untidy end.
- **Fix pass 2's changes:** U10.2 → C83.2 now ends 0.175 mm off centre, and R81.1's entry is axial.

## 7. Remaining exceptions: does a DRC-clean edit remove them?

**4-segment redraws** (`alt4.py`, every C11 run up to 7 mm, the chain-detour cap, pads and vias fixed):

| C11 run | Clean 4-segment redraws | Judgement |
|---|---:|---|
| #12 3V3A, #13 USB_DM, #17 PYRO1_CONT (rigid), #19 CC2 | 0 | "none" holds at 4 segments |
| #14 QSPI_CLK | 8 | Not simpler: one more bend, and the best (5.23 mm) runs its diagonal 0.166 mm from QSPI_IO3's via (27.75, 43.83), a new sub-0.2 mm pair |
| #15 / #16 SERVO1 / SERVO4 | ~490 | The best is the present E–NE–N shape with a larger chamfer (plus a 0.4 µm piece inside D121's pad). Same headings, so by route_check's P7-ROUTING-04 policy it moves the bends rather than removing the detour |
| #18 CAM_5V (C75.1 → U13) | 36 | 4 segments against 3: one more bend |
| #20 RXEN, #21 3V3_GNSS, #22 USB_DP, #23 CAM_5V | many | 0.05–0.35 mm pieces, as C11 says for their 3-segment ones |

**Margin-free search** (`bump0.py`: the gate's own `bump_audit` on every net and `alt_audit` on C11, with RedrawCheck at
DRC's threshold instead of the rule + 0.01 mm):
- **bump_audit:** 2 candidates in 28 windows.
  - CAM_PWR_EN is new, hidden only by the margin (R8P3-ROUTING-03).
  - BAT_ENABLE is part F's known false positive.
- **alt_audit:** 5 found. RXEN, 3V3_GNSS, USB_DP and CAM_5V #23 are C11's own "found".
  - The fifth is new: a 45° chamfer of USB_LIMITED's corner at (29.95, 37.25). It is not clean: its diagonal passes
    0.151 mm from the 3V3 via (29.25, 39.0), a new pair at the DRC minimum.
- **No critical net** gains a removable bump or detour.

**Adjacency rows** (variants on the board, each DRC 0 / 0 / 0 with parity, route_check identical to `base`, check_r8 OK,
actuators OK):

| Row | Edit | Effect | Worth it? |
|---|---|---|---|
| C12 #5 CAM_PWR_EN / USB_LIMITED 0.150 | `usbl`: USB_LIMITED trunk y 37.25 → 37.3 (x 16.35–29.95; TP82 tap from y 37.3) | 0.200 mm; no new pair under 0.2 (nothing else on B.Cu within 0.6 mm of that run) | **Yes** (R8P3-ROUTING-01) |
| C12b #20 / #21 R172 / USB_LIMITED 0.180 | `r172`: R172 → (30.65, 48.1); RAW_ACT_SENSE lane x 30.6 → 30.65; R172.2 stub to x 30.65 | 0.230 mm; one new pair at exactly 0.200 (the lane / USB_LIMITED's 0.6 mm hop via) | **Yes** (R8P3-ROUTING-01) |
| C12b #18 Q120.9 / BAT_ENABLE via 0.180 | `be5`: the via at 0.5 / 0.3 mm in place (or `be`: the 0.6 mm via 0.02 mm aft) | 0.23 mm (be: 0.20); BAT_ENABLE–BAT_IN minimum becomes 0.200 at U9.1 (pin pitch) | **Yes** (R8P3-ROUTING-02) |
| C11 #5 CAM_PWR_EN | `cpe`: (31.85, 36.8) → (28.25, 36.8) → (28.25, 30.025) → (30.775, 27.5) | 22.12 → 20.15 mm; no new gap under 0.3 mm | **Yes** (R8P3-ROUTING-03) |
| C12b #19 R120.2 / step-7 GND via 0.180 | `r120v`: via → (15.4, 107.4) | 0.58 mm; but the GND pour stays 0.1505 mm from R120.2 | No (§9) |
| C12b #11 / #12 R166 / RAW_PROTECTED 0.175 | `r166`: R166 y 101.7 → 101.725 | 0.200 mm; but R166.1 keeps GND fill at 0.1505 mm and the lane runs along the GND strip | No (§9) |
| C12b #3 Q123.3 / PULLPIN 0.170 | — | PULLPIN x 14.23 is pinned by R161.2, its via (0.198 mm from a GND via) and J123.2's relief; a Q123 shift needs its BUZZ_OUT / BUZZ_G stubs redrawn | Not cheap |
| C12 0.150 mm pairs #1–#4, #6–#10 | — | U1 / U4 / U12 pin pitch and the fence slot, as recorded | No cheap edit |

All six recommended-or-tested edits together (variant `all`, plus `cpe` = `all2`) are also DRC- and gate-clean. Variant
`rec` holds only the four recommended edits; its figures are in §1.

## 8. Findings

### R8P3-ROUTING-01 (Minor, worth fixing): USB_LIMITED sits 0.150 mm from CAM_PWR_EN and 0.180 mm from R172's bare pads; 0.05 mm shifts open all three

**Requirement.**
- REQUIREMENTS M2: adjacency on every net, and every review residual "with … why it cannot reasonably be removed".
- R8_VALIDATION C12 (l. 285: "not cheap to open (D91)"; #5, l. 331: "CAM_PWR_EN's run is pinned by TP73's 1.0 mm
  bare-pad zone").
- C12b #20 / #21 (l. 380–381: "not removed yet").
- Owner priority 2.

**Finding.**
- USB_LIMITED, the 5 V output of U10, is a 0.4 mm B.Cu trunk (`r8_power.py` l. 317 / 319): y 37.25 from x 16.3 to
  29.95, then north on x 29.95 to the hop via (29.95, 54.0).
- **CAM_PWR_EN.** Its lane at y 36.8 sits 0.150 mm from the trunk. The record treats the pair as fixed because CAM_PWR_EN
  cannot move, but the trunk can. On B.Cu nothing lies within 0.6 mm of the y 37.25 run on its south side (my
  `corridor.py`).
- **R172.** The x 29.95 run passes 0.180 mm from R172.1 (RAW_ACT_SENSE) and R172.2 (RAW_ACT_SENSE_MCU = U1.34, PB0, on the
  pin side of the 4.7 kΩ). It cannot move west: the ARM1_SENSE_MCU via (29.3, 47.5) is at exactly 0.200 mm. R172 can move
  east: nothing on B.Cu lies within 0.4 mm east of it or of its lane.

**Evidence.**
- **Variant `usbl`:** trunk to y 37.3; corner (16.3, 37.25) → (16.35, 37.3), keeping the 45° from (15.4, 36.35); TP82 tap
  from (19.4, 37.3).
  - DRC 0 / 0 / 0 with parity. route_check identical except the T moves (19.4, 37.25) → (19.4, 37.3). check_r8 OK,
    actuators OK.
  - CAM_PWR_EN / USB_LIMITED goes 0.150 → 0.200 mm, with no new pair under 0.2 (`gaps.py` diff).
- **Variant `r172`:** R172 → (30.65, 48.1); RAW_ACT_SENSE (30.0, 58.1) → (30.65, 57.45) → (30.65, 48.53); R172.2 stub
  (31.08, 47.67) → (30.65, 47.67).
  - DRC 0 / 0 / 0, gate as above.
  - Both R172 rows go 0.180 → 0.230 mm; one new pair sits at exactly 0.200 (the lane to USB_LIMITED's 0.6 mm hop via
    (31.25, 55.3)).
  - R172's courtyard stays 22.6 mm from any THT pad (R5 L10), and C7's L10 figure only grows.
- **Variant `rec`** (with -02 / -03): m2_sweep adjacency 54 → 53 rows, adjacency_pad 36 → 33. C11 #6 becomes 27.25 /
  21.07 mm (excess unchanged).

**Why Minor.**
- Every gap is DRC-legal and the copper is tented. A track-to-track short needs an etch defect, which JLC's electrical test
  screens, and a pad-to-track bridge needs a mask breach (Inference).
- PE12 (CAM_PWR_EN) is FT_h, so a short there switches the camera on from USB; it should not hurt the pin.
- R172.2's row is the board's only place where 5 V sits under 0.2 mm from an ADC-pin node with no series resistor. PB0 is
  FT_a (pin_table, DS12110 Table 9 p. 70); that it is not 5 V tolerant in analog mode is an Inference, as C12b says.

**Fix.**
- `r8_power.py` l. 317 / 319: (16.3, 37.25) → (16.35, 37.3), (19.4, 37.25) → (19.4, 37.3) and (29.95, 37.25) →
  (29.95, 37.3); update the l. 311 comment.
- `r8_place.tsv` l. 30: R172 x 30.6 → 30.65.
- `r8_route_pyro.py` l. 48 / 51 / 67: the lane (30.6, 57.5) → (30.65, 57.45) and (30.6, 48.53) → (30.65, 48.53); the
  stub end (30.65, 47.67); the pad table.
- Rebuild, re-run the gate and `m2_sweep.py`, and update C12 #5, C12b #20 / #21 and C11 #6. With the trunk moved, the
  sweep's bumps_all reports CAM_PWR_EN: apply R8P3-ROUTING-03 with it.

### R8P3-ROUTING-02 (Minor, worth fixing): R165's BAT_ENABLE via uses the 0.6 mm power via, 0.180 mm from Q120's bare BAT_IN drain pad; the board's 0.5 mm signal via opens it to 0.23 mm

**Requirement.**
- M2 adjacency.
- C12b #18 (l. 378): "not removed yet (a placement move in the band)".
- D98's rule that a close via takes the board's 0.5 / 0.3 mm via, with the same drill and barrel.
- Owner priority 2 (a robust design).

**Finding.**
- `r8_route_status.py` l. 91 draws `ENABLE_VIA` (16.6, 104.5) with `VIA_PWR` (0.6 / 0.3; l. 123–124), commented only
  "spike (c)'s size beside Q120's drain pour". BAT_ENABLE carries U9's EN divider current (µA). Its other via, V_BE2
  (40.42, 93.5), is drawn as a 0.5 mm signal via (l. 90).
- The 0.6 mm ring comes 0.180 mm from Q120.9, the bare BAT_IN drain pad. That is the closest BAT_ENABLE copper to battery
  copper anywhere on the board. A bridge there holds EN at pack voltage, so the switch cannot turn the board off (the
  latch class, as C12b and the pyro observations record).

**Evidence.**
- **Variant `be5`:** the via at 0.5 / 0.3 mm, same centre.
  - DRC 0 / 0 / 0 with parity, route_check identical, check_r8 OK, actuators OK.
  - Q120.9 / BAT_ENABLE goes 0.180 → 0.23 mm, and no BAT_ENABLE pair under 0.2 mm remains.
  - The BAT_ENABLE–BAT_IN minimum becomes 0.200 mm at U9.1, set by U9's pin pitch.
- **Variant `be`:** the 0.6 mm via 0.02 mm aft also gives 0.200 mm, DRC- and gate-clean.

**Why Minor.** The via is tented, so a bridge needs a mask breach; ORDERING §5's switch-off step screens the result.

**Fix.** Draw `ENABLE_VIA` with `VIA_SIG`: move it into `SIGNAL_VIAS` and drop it from the l. 123 loop. Rebuild; step 7
may shift a stitching via. Re-run the gate and the sweep, delete C12b #18, and update the pyro observations' BAT_ENABLE
row.

### R8P3-ROUTING-03 (Minor, worth fixing): CAM_PWR_EN's lower leg has a DRC-clean redraw 1.98 mm shorter, hidden from the gate's and the sweep's redraw searches by RedrawCheck's 0.01 mm margin

**Requirement.**
- M2 "no needless detours". C11 #5 (l. 303: redraw search "none"; "x 28.0; the run at y 36.8 is pinned by TP73's 1.0 mm
  zone").
- Part F (l. 452): "Local bumps on non-critical nets … 1 candidate … a false positive".
- Owner priority 2.

**Finding.**
- CAM_PWR_EN (B.Cu, `r8_route_camera.py` l. 101) runs (31.85, 43.0) → (31.85, 36.8) → (28.0, 36.8) → (28.0, 27.5) →
  (30.775, 27.5), 22.12 mm. It ends in an L and a 2.78 mm run into R74.1.
- The window from (31.85, 36.8) has a 3-segment redraw: (31.85, 36.8) → (28.25, 36.8) → (28.25, 30.025) →
  (30.775, 27.5). It is 13.95 mm against 15.93 mm, keeps the pinned y 36.8 leg, and replaces the corner and the stub with
  one 45° run into R74.1's centre.
- The gate's `bump_audit` (and `alt_audit`, which m2_sweep uses) test each candidate with `r7_hygiene.rule_clearance`,
  which adds 0.01 mm to every rule. The y 36.8 leg already sits 0.150 mm from USB_LIMITED (C12 #5), so every candidate
  that keeps it fails. The sweep therefore reports no bump here.

**Evidence.**
- **`bump0.py`** (the same `bump_audit` on every net at DRC's threshold) finds 2 candidates in 28 windows: this one and the
  BAT_ENABLE false positive. Its `alt_audit` adds only a USB_LIMITED chamfer, which passes 0.151 mm from the 3V3 via
  (29.25, 39.0) and so is not clean (§7).
- **Variant `cpe`:**
  - DRC 0 / 0 / 0 with parity, route_check identical, check_r8 OK, actuators OK.
  - No new gap under 0.3 mm: the nearest is the GND via (28.875, 32.875) at 0.275 mm.
  - C11 #5 becomes 20.15 / 15.95 mm (excess 6.18 → 4.20).
- **Variant `all`** (with R8P3-ROUTING-01's trunk move, which opens the 0.150 mm leg): m2_sweep's own bumps_all reports
  exactly this candidate. **Variant `all2` / `rec`** (with `cpe`): bumps_all is back to the one known false positive.

**Why Minor.** It is a non-critical static GPIO line, and the D37 loop round U7 stays. But it is a cheap edit that removes
a corner and a long stub, and the record's "none" and part F's sweep rest on a test that could not see it.

**Fix.**
- `r8_route_camera.py` l. 101 → `[V_PWR_EN, (31.85, 36.8), (28.25, 36.8), (28.25, 30.025), (30.775, 27.5)]`, then
  rebuild and update C11 #5.
- For the record and part F, either let RedrawCheck test only gaps that the window's present copper does not already have,
  or run the sweep's bump and redraw searches once at DRC's threshold and record what they find. The gate's own bump
  check stays unchanged: on the critical nets the margin-free run finds nothing.

## 9. Notes (no finding)

- **The step-7 GND via 0.180 mm from R120.2 (ACT_GATE)**, fix pass 2's "candidate for pass 3":
  - Variant `r120v`, the via at (15.4, 107.4), is DRC- and gate-clean.
  - But `zgap.py` measures the B.Cu GND fill 0.1505 mm from R120.2 and from C120.2 (the outer pours' 0.15 mm clearance),
    so ACT_GATE's nearest GND copper does not change.
  - C12b #19's consequence ("turns the actuator switch on") applies as much to the pour as to the via, and to every
    pad of the net. Not worth a change. The row's reason should name the pour (records; the pyro, power and integrity
    passes say the same).
- **R166 / RAW_PROTECTED (C12b #11 / #12, 0.175 mm):**
  - Variant `r166` (0.025 mm aft) is clean and opens both rows to 0.200 mm.
  - But R166.1 already has GND fill at 0.1505 mm, and a short from R166.1 to RAW_PROTECTED loads RAW_PROTECTED through
    R166's 0.33 Ω, the same consequence the GND strip beside the lane already carries at 0.15 mm. Not worth fixing.
- **QSPI_CLK, SERVO1 / SERVO4 and USB_LIMITED's corner:** clean redraws exist but are not simpler (§7): one more bend, a
  new pair under 0.2 mm, or the same headings with a larger chamfer.
- **C98.1's 45° T** (the USB_LIMITED diagonal against the 0.25 mm R87 branch): the wedge apex lies 0.037 mm inside the
  pad edge (exact, with the two widths), and route_check's averaged-width apex 0.053 mm inside. Legal; noted in pass 1.
- **D99's C83.2 joint** reads as an L with its corner inside the pad. One polyline through (9.55, 35.4) would trade the
  pad_end_offcentre for a corner inside the pad, so neither is better.
- **`rg/scan.py`'s source is gone** from the scratchpad. Only its Python 3.9 bytecode is left; I ran that (`scan.pyc`), and
  its counts agree with mine.

## Appendix: reproduce

```
cd <scratch>/r8p3rt        # r8.kicad_pcb = 990c8040…; ../p3rf/p2.kicad_pcb = 6600ef94…; ../p8rt/r7.kicad_pcb = c872a3d3…
PY=<KiCad 10.0.6 python3>
$PY -I ../r8p2rt/diff.py ../p3rf/p2.kicad_pcb r8.kicad_pcb               # fix pass 2's copper diff
$PY -I p3scan.py r8.kicad_pcb s3.json ../p8rt/r7.kicad_pcb               # independent scan
$PY -I ../r8p2rt/p2scan.py r8.kicad_pcb s2.json ../p8rt/r7.kicad_pcb     # cross-checks
$PY -I ../r8p2rt/gaps.py r8.kicad_pcb 0.2 gaps.json; $PY -I ../r8p2rt/threads.py r8.kicad_pcb ../p8rt/r7.kicad_pcb
(cd rgscan && $PY scan.pyc ../r8.kicad_pcb ../../p8rt/r7.kicad_pcb rg.json)
$PY -I <repo>/m3_design/assembly_review/sources/r8_design/step9/m2_sweep.py r8.kicad_pcb --json m2.json
$PY -I alt4.py r8.kicad_pcb m2.json 0.05 7.0          # 4-segment redraws
$PY -I bump0.py r8.kicad_pcb m2.json                  # bump / alt audit at DRC's threshold
$PY -I zgap.py r8.kicad_pcb R120.2,C120.2,R172.2,R166.1   # pad to GND fill
# variants (project copy in proj/, kilib symlinked): e_<name>.json, then
./vrun.sh base e_base.json; ./vrun.sh usbl e_usbl.json; ./vrun.sh r172 e_r172.json; ./vrun.sh be5 e_be5.json
./vrun.sh be e_be.json; ./vrun.sh cpe e_cpe.json; ./vrun.sh r120v e_r120v.json; ./vrun.sh r166 e_r166.json
./vrun.sh all e_all.json; ./vrun.sh all2 e_all2.json; ./vrun.sh rec e_rec.json
python3 rcdiff.py v/base/rc.json v/<name>/rc.json
```
