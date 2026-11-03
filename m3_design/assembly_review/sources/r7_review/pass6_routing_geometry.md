# R7 review pass 6: routing geometry and style (whole board)

Reviewer: independent, read-only. Dimension: routing geometry and style of every track and via on all four layers,
copper inherited from R6 included, against AGENTS.md §3 and the owner's clean-routing list (REQUIREMENTS M2). For this
pass in particular: are the pass-5 findings closed, is `tools/route_check.py` (and its new reason audits) sound, and
does any remaining allowlist entry, leftover or deviation-list item have a DRC-clean edit that removes it?

- **Board reviewed:** `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
  `1ffc2585cbbb2a49623a5010b2792500849f06989cf43e48fb3e56068cddf9df` (the fix-pass-5 board of `fix5_F6_handoff.md`;
  the same SHA before and after this review). 1,777 tracks, 706 vias, no arcs, 4,503.4 mm of track: F.Cu 694 /
  1,583.0 mm, B.Cu 799 / 1,894.2 mm, In2 284 / 1,026.1 mm, **In1 0**.
- **Comparison boards:** the pass-5 board `c6fe595c…c7c7` (1,809 tracks, 694 vias) and committed R6 `3b215ba` (+18 mm).
- **Gate on this board:** `tools/check.sh` exit 0 (run by me): DRC 0, unconnected 0, schematic parity 0, ERC 0;
  metadata/3D OK; silkscreen 0; "R7 CAD contract: OK"; "routing hygiene: 0 failing, 33 allowlisted, 0 stale allowlist
  entries, 0 out-of-date no-GND reasons, 30 leftovers recorded (0 unrecorded, 0 stale), 0 out-of-date route figures, 0
  removable jog / staircase / short-segment exceptions: OK"; actuator contract OK; fit OK.
  `tools/test_route_check.py`: 41 tests OK.
- Nothing in the repository was modified except this file. Scratch work (scripts, scratch board copies, logs):
  `<scratch>/r7p6geo/`
  (below `<p6>`). Scratch boards were saved only under `<p6>/v_*`.

## 1. Verdict

Fix pass 5 closed all four pass-5 findings in this dimension (§3). On the final board no AGENTS §3 geometry rule is
broken anywhere:

- no off-angle segment, arc or zero-length piece;
- no staircase, also when followed through T, via and pad nodes;
- no exposed acute angle (10 45° pairs, every wedge inside pad or via copper);
- no stub, dangling end, dangling via or same-net via-ring overlap.

The only §3 rule instances left are the 9 allowlisted critical layer changes without a GND via (A6–A14) and the
IPC-2152 item C1. My own GND-via probes agree that the 9 have no legal spot.

The new `route_check` detections work. I ran the final tool on the pass-5 board, and it finds every pass-5 blind-spot
instance (S1–S5), the node jogs and staircases, and the stale route figures and unrecorded leftovers.

What is left is three Minor findings. Each comes with a DRC-verified scratch edit or a measured record error:

- **P6-01:** the three SW_NODE allowlist entries (A3 tiny jog, A4 and A5 short segments) are not "forced by the buck's
  placement" and need no "power-stage re-layout", as the deviation list says.
  - One redraw removes all three. It is DRC-clean, `check_r7` and `check_actuators` pass, and `route_check` reports
    only the three now-stale entries.
  - It costs +0.37 mm of switching-node track (about +0.22 mm², roughly 2 % of the node's copper).
  - `alt_audit` cannot see this redraw: it has 5 segments, spans both windows, and its end moves inside L1.1's
    3.5 mm pad.
  - So keeping these entries is a length trade-off for the owner, not a forced one.
- **P6-02:** `route_check` (and every earlier scan) is blind to jogs whose middle is two segments.
  - The one tiny instance on the board is a LOGIC_SS knee: two SW diagonals 0.141 mm apart, joined by S 0.35 and
    W 0.55.
  - It is not counted and not recorded, and a DRC-clean redraw removes it (0.32 mm shorter).
- **P6-03:** the deviation list is not complete, and parts of it are inaccurate.
  - C17 names 4 "steps wholly inside a via" and C16 names BOOT0's. The board has at least 13: 8 are listed nowhere, and
    five of those are on critical power nets (RAW_PROTECTED ×2, VBUS, USB_LIMITED, GND).
  - Leftovers of R6 micro-segment debris are not listed: 17–25 µm lap offsets inside D8.1 and R90.2, and the ACT_GATE
    knot at via (7.7, 102.2).
  - C19's "deleting it would change no connection" is not true as stated.
  - D7's 0.5 mm measures 0.62–0.63 mm.

No Critical and no Major. Nothing found is open, shorted or below a DRC rule.

## 2. Method

Scripts in `<p6>` (KiCad 10.0.6 Python; boards loaded read-only; scratch variants saved under `<p6>/v_*` with the
project's `.kicad_pro`, `.kicad_dru` and schematic sheets beside them):

| Script | What it does |
|---|---|
| `scan6.py` | **Independent scan written for this pass** (no code from route_check, scan.py or scan5.py). Segments are grouped per (layer, net), and nodes are end points clustered at 1 µm, typed end / plain / T / via / via-copper / pad. **Segments:** heading error (0.02° or 0.5 µm lateral), micro and short pieces with an inside-one-pad/via test, through-pad and inside-pad. **Ends:** dangling, overlap-only, pour-only (the run's centre line inside its own fill), and off-centre via joints. **Angles:** every branch pair at every node, with the acute wedge apex tested against the node's pad and via copper. **Collinear joints:** unmerged and width-changing, and necks at plain nodes. **Jogs at any node type**, across vias too (S between P and Q on the same heading), graded tiny (middle < 0.5 mm or offset < 0.25 mm), small (offset < 0.5 mm) or plain dogleg, with side-branch and inside-via flags. **Staircases** through any node on one layer. **Same-net copper:** parallel overlaps, crossings, and a polygon-boolean coverage of every track by the other same-net copper. **Vias:** copper layers, critical and power layer changes against the nearest GND via, same-net ring overlap, via on a track body. U-turns and short hops |
| `extra6.py` | Jogs whose middle is 2–3 segments (P, M1..Mk, Q, with Q on P's heading and ΣM < 1 mm), along plain chains; and collinear width changes through T, via and pad nodes |
| `padedge6.py` | Off-centre pad entries, with the distance from the track end to the pad outline |
| `diff6.py` | Copper diff between two boards (tracks and vias added or removed per net) |
| `ctx6.py` | All copper within a radius of a point |
| `edit6.py`, `vrun.sh` | Apply an edit list to a copy of the final board, refill zones natively, save `v_<name>/m3.kicad_pcb`, then run `kicad-cli pcb drc --severity-all --schematic-parity`, `route_check`, `check_r7` and `check_actuators` on it. Variant `base` (no edit): DRC 0/0/0 and every check OK, so the refill matches the gate |
| `scan.py` (= `rg/scan.py`), `scan5.py`, `p4scan.py`, `p4extra.py`, `rc_allpairs.py`, `probe.py`, `probe_drc.py`, `nudge.py`, `gs5.py`, `clr5.py` | The pass-2, -4 and -5 reviewers' scripts, unchanged. `gs5.py` runs the project's own `r7_hygiene.gnd_spots` |

I also ran `tools/route_check.py --report --routes` on the final board and on the pass-5 board, and
`tools/test_route_check.py`.

## 3. Pass-5 findings in this dimension: closure check

| ID | Pass 5 (skeptics) | R7_VALIDATION disposition | Verified on the final board |
|---|---|---|---|
| P5-RG-01 | Major → Minor (Minor ×3), worked as Major | Fixed | **Closed.** BUSY's east chamfer is (20.49, 28.0) → (21.2, 27.29) and MISO_MCU's is (20.89, 28.4) → (21.6, 27.69), both 1.004 mm. MISO_MCU's step is now at (11.0, 28.7) → (11.3, 28.4) and MOSI's at (10.95, 29.2) → (11.35, 28.8). RXEN runs (22.575, 30.45) → (23.8, 31.675) → (23.8, 39.45), with no jog into its via. QSPI_CLK steps (22.85, 44.65) → (23.21, 44.29), 0.509 mm with a 0.36 mm offset (C16). My scan finds **0 staircases** anywhere, and the gate's A1/A2/A5 entries are gone. RXEN's no-GND (A6) still has no spot (§6). The extra QSPI_CLK reference samples are recorded in C2 |
| P5-RG-02 | Minor | Fixed | **Closed.** CAM_EN runs W / S / SW: (37.95, 85.16) → (36.9, 85.16) → (36.9, 85.75) → (36.05, 86.6). CAM_FAULT_N has one In2 run at y 103.938. CAM_RX_WIRE has one In2 lane at x 44.251. CAM_5V_SENSE's F.Cu hop and 2 vias are gone, and LED_RED is on F.Cu with 2 vias. B7 and B22 are restated with measured blockers. NRST is 46.11 mm (`ROUTE_FIGURES`, gated by `measured_check`) |
| P5-RG-03 | Minor | Fixed (board) | **Closed.** GND vias 0.5 mm at (13.95, 93.75) and (13.95, 97.15), 0.7211 mm from ARM1_SENSE's vias (14.55, 94.15) and (14.55, 97.55). No ARM1_SENSE layer change is without a GND via (my scan, scan5, p4scan) |
| P5-RG-04 | Minor | Fixed (tools) | **Closed for (a)–(d) as dispositioned.** On the **pass-5 board**, the final `route_check` reports 18 failing, 9 unrecorded and 6 out-of-date figures. That includes: acute_angle ACT_GATE (5.9, 102.4) (S1); node staircases for GND, CAM_5V, CAM_FAULT_N and CAM_RX_WIRE (S2); node tiny jogs for RXEN, GND, 3V3_RADIO and CAM_5V (S2); pour_stub RAW_ACT (5.3, 82.17), 3.186 mm (S3); TP122's pad layer change counted (S4); via_overlap ×3 (S5); and stale figures for VLOGIC, CAM_5V_SENSE, CAM_EN, CAM_FAULT_N and LOGIC_SOURCE_ST. So each new check fires on the copper it was written for. Residual limits are in §5 and P6-01 / P6-02 |
| P5-RQ-04 / -05 (related) | Minor | 2 of 3 removed, 1 forced / closed | LOGIC_ILIM now runs S / SW / SE: (29.45, 29.35) → (29.45, 29.95) → (28.925, 30.475) → (30.7, 32.25). SERVO4_MCU is straight down x 15.505. I2C1_SCL's 0.36 mm step stays (C16) |

New copper from fix pass 5 (`diff6.py`: tracks +63 −95, vias +25 −13), checked segment by segment:

- every new segment is on 0/45/90° and joins at a node;
- the only new tiny-class instances are PULLPIN_EXT's 0.25 mm step inside its via (C17) and MISO_MCU's moved step
  (A2);
- the only new small jogs are QSPI_CLK (C16) and RADIO_MOSI's moved band step (0.566 mm, 0.4 mm offset);
- one new off-centre pad entry: 3V3_RADIO into C310.1, 0.304 mm off centre, 0.49 mm inside a 1.41 × 1.35 mm pad
  (a tidy D4 fix);
- RAW_ACT's tail ends 0.62–0.63 mm inside its own fill (D7).

## 4. Counts

### 4.1 Gate (`route_check --report --routes`, final board)

312 instances, 0 failing, 33 allowlisted, 30 leftovers recorded, and every audit at 0. This equals F6's handoff §4.

- **Gated or recorded categories, all (critical):**
  - critical_via_no_gnd 9 (9);
  - tiny_jog 3 (3): A1, A2, A3;
  - short_segment 2 (2): A4, A5;
  - detour 22 (9) and extra_vias 27 (10);
  - staircase, acute_angle, fold_back, dead_copper, pour_stub, dangling_via, off_angle, every other hygiene category
    and every pour category: **0**.
- **Information, all (critical):**
  - pad_end_offcentre 93 (64);
  - power_via_no_gnd 35;
  - width_change_junction 31 (30);
  - u_turn 25 (18);
  - extra_bends 32 (12);
  - passes_through_pad 10 (10);
  - short_layer_hop 20 (9);
  - segment_inside_pad 3 (2).
  - Total 249 (180), which equals part E.

### 4.2 Independent scan (`scan6.py`), final board, all (critical = route_check's critical classes)

| Category | Count | Notes |
|---|---|---|
| off_angle / arcs / micro (< 50 µm) | **0 / 0 / 0** | |
| short (< max(w, 0.2 mm)) | 30 (23) | 28 lie wholly inside a via (via-entry pieces); 2 are open, SW_NODE A4/A5 |
| staircase (any node, one layer) | **0** | |
| acute (0.5–89.5°), exposed | 10 (6), **0 exposed** | all 45° pairs at pads or vias |
| fold_back / crossing / dangling end / overlap-only end / via off-centre | **0 / 0 / 0 / 0 / 0** | |
| pour-only end | 1 (1) | RAW_ACT F.Cu (7.6, 81.57): run 7.11 mm, 0.628 mm of centre line inside its fill (D7; p4extra 0.621) |
| collinear unmerged (same width) / collinear width change | **0** / 3 (3) | the 3 are pad-entry necks: BAT_IN → U9.5, RAW_PROTECTED → U9.6, CAM_INPUT_LIMITED → U7.5 |
| neck at a plain node | 5 (5) | all run into the pad they end in, at ≤ 1.4 mm |
| parallel overlap (same net) | 2 (1) | BAT_IN B.Cu inside D8.1 and USB_FAULT_N B.Cu inside R90.2: two collinear runs offset laterally by 17.7 µm and 25 µm, joined only by the pad (R6 micro-segment debris whose joining pieces were deleted; P6-03) |
| covered track (≥ 98 % under other same-net copper) | 36 (21) | pad/via entry pieces, including C19 (BAT_IN C96.1) and PYRO1_BUS R132.1 → 1.0 mm trunk (the pad already overlaps the trunk by 0.073 mm) |
| jog_tiny (middle < 0.5 mm or offset < 0.25 mm) | 14 (9) | A1 BUSY, A2 MISO_MCU, A3 SW_NODE; BAT_FAULT_N (11.9, 42.1), a side branch at a T (not a jog); **10 wholly inside a via** (P6-03) |
| jog_small (offset 0.25–0.5 mm, middle ≥ 0.5 mm) | 23 (17) | not tiny by the project's definition; 6 have a middle of exactly 0.50–0.51 mm (Appendix A3) |
| compound jog (2–3 segment middle < 1 mm, `extra6.py`) | 2 (1) | **LOGIC_SS (offset 0.141 mm; P6-02)**; GND B.Cu (6.07, 75.79), offset 0.73 mm, into C28.2 |
| other doglegs (offset ≥ 0.5 mm) | 305 (139) | information |
| via ring overlap / dangling via | **0 / 0** | |
| critical layer change without GND via ≤ 1.5 mm | **9** | = A6–A14 (Appendix A1) |
| power layer change without GND via | 35 | = route_check's power_via_no_gnd |
| via on a track body | 1 | GND (6.85, 40.5) |
| pad off-centre (> 0.1 mm, pad ≤ 2 mm) | 87 (61) | 12 end within 0.06 mm of the pad edge (`padedge6.py`), e.g. USB_LIMITED U10.6 and CAM_IO_3V3 C93.1; the U11.7 one of pass 5 is gone (D10) |
| through pad / inside pad | 10 / 3 | as part E |

### 4.3 Reference scans (unchanged scripts, final board)

- **Pass-2 `scan.py`:** 945 instances (591 critical) — equal to F6's figure.
- **Pass-5 `scan5.py`:**
  - jog_tiny 4: GND (31.3, 53.7) inside a via, BUSY, MISO_MCU, SW_NODE;
  - staircase 0, acute exposed 0, crit_layer_change_no_gnd 9;
  - jog_across_via tiny 1 (BOOT0, C16).
- **Pass-4 `p4scan.py`:** jog_tiny 4, crit_layer_change_no_gnd 9, acute 10 (critical 6), leaf_stub 4 (the RAW_ACT tail).
- **`p4extra.py`:**
  - 12 tiny jogs across a via. These are the 10 inside-via steps above, plus BOOT0 (C16) and BAT_FAULT_N's side
    branch.
  - RAW_ACT pour-only run: 0.621 mm inside its fill.
- **`rc_allpairs.py`** (the pass-5 copy of the pass-4-era gate; it has no PAD_RING exclusion):
  - only stale entries of its own old allowlist;
  - three GND pour_finger hits that the current gate's PAD_RING exclusion drops (§5.4).

## 5. route_check audit

### 5.1 New detections (P5-RG-04 (c), (d))

All are sound for what they claim; I checked each against the pass-5 board (§3):

- the jog test through T, via and pad nodes, with the fan-out and side-branch exemption (lines 1706–1735);
- the staircase test through nodes (1736–1771);
- every acute pair (1600–1615);
- `pour_stub` (1500–1503);
- a layer change into a pad counted (1788–1793);
- `via_overlap` (1794–1800);
- `LEFTOVER_CATS = HYGIENE` (285).

The one stated exemption that matters is "S wholly inside one pad or via is that copper, not a jog" (line 1710,
`cu.inside_one`). It is defensible, but it hides at least 13 in-via steps, of which the records list only 5 (P6-03).

### 5.2 Reason audits (P5-RG-04 (a), (b))

- **`nognd_audit`** (1892–1912): sound for its scope. My `probe.py` (project rules, 0.025 mm grid) also finds no spot
  for any of the 8 radio entries. The top blockers are the band and corridor lanes and holes.
- **`measured_check`** (1919–1935): exact via count, length within 0.05 mm. I compared the `--routes` output with
  `ROUTE_FIGURES` for all 39 nets: no mismatch. The quoted search results are not re-run, as stated.
- **`alt_audit`** (1997–2210): it correctly tries every 1–3 segment octilinear redraw between the window's two end
  points. Its "0 removable" is weaker than the records read it, for three reasons:
  - (a) The window's end points are the existing track ends, even where an end lies inside a large same-net pad and
    could move within it without moving the pad. For SW_NODE, w1 = (22.92, 34.05) sits inside L1.1, which is
    1.6 × 3.5 mm. The docstring states only that "pads and vias stay put".
  - (b) Each instance is audited alone, so a redraw that fixes two adjacent windows at once is never tried.
  - (c) 4+ segment redraws are not searched (stated).

  On a power rail it also accepts no redraw longer than the present window (`ALT_SLACK_POWER = (1.0, 0.0)`, line 1943).
  That is a policy, not a measurement, and no requirement sets it. P6-01 is a 5-segment, two-window redraw that the
  audit cannot see.
- **`leftover_check`**: correct. It reports 30 recorded, 0 missing and 0 stale.

### 5.3 Remaining blind spot

**A jog whose middle is two or more segments** (an "A, B, C, A" knee) is neither a tiny_jog (one-segment middle only)
nor a staircase (not alternating). No scan used in any pass detects it. One tiny instance exists (P6-02).

### 5.4 Pour fingers (information, for the RF review)

`pour_pieces` subtracts each GND pad's ring (outline + 0.75 mm) before it measures a finger. On the final board this
drops three thin GND B.Cu pieces that the older gate copy reports:

| Piece at | Length | Cells beyond the 4 mm reach |
|---|---:|---:|
| (14.96, 86.76) | 4.57 mm | 688 |
| (39.26, 77.25) | 3.4 mm | 613 |
| (20.92, 33.38) | 4.44 mm | 73 |

They are mostly pad-relief copper, and C11 / P4-RF-01 covers fingers of this kind. I did not judge their RF effect.

## 6. Allowlist (33), leftovers (30) and deviation list: removal attempts

| Items | Claim | Result |
|---|---|---|
| A1, A2 band fan-in tiny jogs | "cannot be avoided without re-spacing the via columns or rows … a re-layout of the interface band" | **True in substance.** Lane k sits at 27.2 + 0.4k and via row k at 27.2 + 0.5k, so the offsets are 0.2 (BUSY) and 0.3 (MISO_MCU), tiny at any step length. BUSY at y 28.0 would hit RADIO_NRST's via (10.0, 27.7). Putting every lane on its via row (0.5 mm pitch) removes all the fan-in steps, but NSS's lane at y 30.2 would come 0.025 mm from D9.1/D9.2's pads (top edge y 30.3) and overlap GND via (19.71, 30.51): a band re-layout. A 54 µm shift of MISO_MCU's lane would only relabel its step (middle 0.5 mm, offset 0.354 mm). Wording: the binding obstacles to on-row lanes, D9's pads and that GND via, are not named (P6-03) |
| **A3–A5 SW_NODE** | "forced by the buck's placement; a power-stage re-layout" | **Not true:** one DRC-clean redraw removes all three (P6-01) |
| A6, A7, A9–A14 radio no-GND | no legal spot within 1.5 mm | **True.** `probe.py` (project rules) finds NONE for all 8, and so does `gs5.py` (`gnd_spots`). For RXEN I also slid the via along its own copper: x 23.8 from y 39.0 to 41.05 and down its B.Cu diagonal. There is no spot until (22.2, 42.65), and that point lies beyond QSPI_CLK's F.Cu lane (x 23.21), which F.Cu cannot cross. The QSPI F.Cu lanes at x 22.5 / 23.21 / 24.6 / 25.2 (0.6–0.71 mm apart) leave no via-sized gap |
| A8 PYRO1_GATE into TP122 | a GND via within 1.5 mm of the pad centre breaks the 1.0 mm bare-pad keep-out | **True.** Every point within 1.5 mm of the centre lies inside the 1.5 mm pad grown by 1.0 mm. Inference, not built: the layer change could move out of the pad to a via with a B.Cu leg to TP122, since `gnd_spots` finds legal GND spots near such sites (e.g. (20.25, 90.375) for a via at (20.45, 90.95)). That would add a U-turn or stub, so it is not clearly cleaner. Not a finding |
| A15–A33 detours / extra vias | figures and search results | Figures equal `--routes` (gate). The searches were not re-run (as pass 5). For the maker keep-outs (A16, A18, A27), the geometry is as stated; I did not re-check the datasheets |
| B1–B30 | figures and search results | Figures equal `--routes` (gate). B7 (CAM_5V_SENSE) proves its box-in only "within 1 mm of U1.35". A via on the near side at about 1.4 mm, with In2 running north of RAW_ACT_SENSE_MCU's via (23.05, 47.65), was not tried, and would trade the F.Cu wrap for more In2 3V3 void. That is a judgement; not a finding |
| C16 forced non-tiny steps | forced by neighbours | **CAM_RX_WIRE confirmed:** BAT_SW_RETURN's In2 lane at x 44.4 (y 39.725–44.525) blocks the via at x 44.251, and J9's pad (y 45.225–46.225) blocks F.Cu further south. QSPI_CLK: as pass 5. I2C1_SCL and BOOT0: F6's measurements, not re-run |
| C17 in-via steps | 4 listed (plus BOOT0 in C16) | **Incomplete:** at least 13 on the board, 8 of them unlisted (P6-03) |
| C19 BAT_IN run inside C96.1 | "deleting it would change no connection" | **Inaccurate** (P6-03) |
| C11, C14, C20 (pour stitching) | | Not re-examined (RF and regression scope) |
| D1–D18 | status | Verified on the board:<br>• D1: no exposed acute.<br>• D2, D6: no staircase.<br>• D3: CAM_5V runs (32.4, 105.325) → (33.175, 104.55) → (39.35, 104.55).<br>• D4: one diagonal FB31.2 → C310.1.<br>• D9: no via-ring overlap.<br>• D10: USB_LIMITED is a corner plus a square branch.<br>• D11: runs end at the U2.2 / U2.3 centres; the 0.55 mm piece inside U2.2 is information.<br>• D12, D13: removed.<br>• D16: no In1 track on the board.<br>• D7: measures 0.62–0.63 mm, not 0.5 (P6-03) |

## 7. Findings

### P6-ROUTING_GEOMETRY-01 (Minor): the three SW_NODE allowlist entries are removable by one DRC-clean redraw; "forced by the buck's placement / a power-stage re-layout" is not true

**Requirement.** REQUIREMENTS M2 lists every deviation with "why it cannot reasonably be removed". AGENTS §3: every
exception is an allowlist entry with a measured reason. SW_NODE is a critical (power) net, so its hygiene items are
gated.

**Present copper** (B.Cu, 0.6 mm): C5.1 (17.92, 35.65) → SE 0.566 → (18.32, 36.05) → E 2.2 → (20.52, 36.05) → NE
1.131 → (21.32, 35.25) → E 0.4 → (21.72, 35.25) → NE 1.697 → (22.92, 34.05), inside L1.1. L1.1 is 1.6 × 3.5 mm at
(22.9, 33.0). The two pieces are A5 (the 0.566 mm drop), A4 (the 0.4 mm step) and A3 (the jog the step makes).

**The records:**
- R7_VALIDATION A3 (line 625), "Why it cannot reasonably be removed": "forced by the buck's placement (U2, C5, C7, C9,
  L1); a power-stage re-layout". A4 and A5 say "as A3".
- `route_check._SW` (lines 183–190): "(inherited R6, forced by U2/C5/C7/C9/L1 placement)".
- The same rows also say that `alt_audit` found two-bend redraws, one per window, at +11–13 % each.

**Measured** (scratch `<p6>/v_sw`, `edit6.py` variant `sw`):
- **Redraw:** C5.1 (17.92, 35.65) → SE 0.849 → (18.52, 36.25) → E 1.70 → (20.22, 36.25) → NE 1.414 → (21.22, 35.25) →
  E 0.70 → (21.92, 35.25) → NE 1.697 → (23.12, 34.05), inside L1.1. The new end is 0.22 mm east of the present one.
- **Clearances** (`clr5.py`, minimum per segment to other-net copper):
  - redraw: 0.213 mm (3V3 via (18.7, 35.28)), 0.370, 0.245 (C7.2), 0.245 (C7.2), 0.375 mm (C9.2);
  - present: 0.213, 0.170 (3V3 via), 0.230 (C9.2), 0.245 (C7.2), 0.259 mm (C7.2);
  - the redraw's overall minimum (0.213 mm) is larger than the present copper's (0.170 mm).

- **Checks on `v_sw`:**
  - `kicad-cli pcb drc --severity-all --schematic-parity`: 0 violations, 0 unconnected, 0 parity.
  - `check_r7`: "R7 CAD contract: OK". `check_actuators`: OK.
  - `route_check`: only "FAIL stale allowlist entry" for ('tiny_jog', SW_NODE, (20.52, 36.05)), ('short_segment',
    SW_NODE, (21.32, 35.25)) and ('short_segment', SW_NODE, (17.92, 35.65)). No new instance.
  - `scan6.py`: tiny jogs 14 → 13, shorts 30 → 28. The gap piece is now 0.70 mm, a non-tiny jog with a 0.495 mm offset.
- **Cost:**
  - C5.1 → L1.1 run 5.994 → 6.360 mm (+0.366 mm, +6.1 %).
  - +0.22 mm² of B.Cu on the switching node. The node's copper is about 10.6 mm² (tracks about 4.1 mm², L1.1 5.6,
    C5.1 0.27, U2.5 0.6), so this is about 2 % (Inference: area estimated from pad and track sizes; no EMI measurement).
- **Why the gate misses it:** `alt_audit` audits each window alone, keeps the window's end points (including the
  track end inside L1.1), and searches 1–3 segments only. This redraw spans both windows, has 5 segments and moves
  the end within L1.1 (§5.2).

**Why Minor.**
- All three are M2 hygiene items, not AGENTS §3 rules. Removing them buys no electrical benefit and costs a little
  switching-node copper.
- The records do disclose that redraws exist.
- The fault is in the "why" column: it states a forced placement constraint where there is a length trade-off.
- This is the pattern of P5-RG-01: the skeptics re-graded that to Minor ×3, and I calibrate to that.

**Fix.** Either apply the redraw and delete A3–A5, or restate the "why" in R7_VALIDATION A3–A5 and in `_SW`. The
restatement would say: "removable by a redraw costing +0.37 mm (+0.22 mm²) of switching-node copper; kept by choice
(no requirement sets the node length)". Optionally, document `alt_audit`'s fixed window end points in its docstring.

### P6-ROUTING_GEOMETRY-02 (Minor): jogs with a two-segment middle are invisible to route_check; one tiny instance (LOGIC_SS) is unrecorded and removable

**Requirement.**
- REQUIREMENTS M2: no tiny jogs on any net. On a non-critical net every hygiene item must be counted and carry a
  recorded reason.
- AGENTS §3 / M2: "the rest is checked in review".

**Present copper**, LOGIC_SS B.Cu 0.2 mm, from U11.11 (28.95, 29.35):
- the path is S 0.5 → SW 0.707 → (28.45, 30.35) → S 0.35 → (28.45, 30.7) → W 0.55 → (27.9, 30.7) → SW 0.495 →
  (27.55, 31.05) → S 2.35;
- the two SW diagonals lie on x + y = 58.8 and x + y = 58.6, 0.141 mm apart;
- S 0.35 and W 0.55 join them, a knee dodging the GND via (28.13, 31.3);
- in route_check's grammar this is neither a tiny_jog (that test takes a one-segment middle) nor a staircase (the run
  does not alternate);
- `extra6.py` finds it, and one GND B.Cu instance at (6.07, 75.79) with a 0.73 mm offset (not tiny). There are no
  others on the board.

**Measured** (scratch `<p6>/v_lss`):
- **Redraw:** U11.11 centre (28.95, 29.35) → S 0.3 to the pad edge (28.95, 29.65) → one SW diagonal 1.98 →
  (27.55, 31.05) → the existing S run.
- **Clearances:** 0.183 mm to U11.12 (GND), 0.187 mm to GND via (28.13, 31.3). The present path's minimum is 0.187 mm.
- **Checks on `v_lss`:**
  - DRC 0/0/0 with parity; `check_r7` OK; `check_actuators` OK;
  - `route_check` OK (no instance added or removed);
  - `extra6.py`: the knee is gone.
- **Length:** 2.60 → 2.28 mm (−0.32 mm), and the S / SW / S jog at the pad goes too.

**Why Minor.** It is cosmetic, on a slow non-critical soft-start node, and it is the only tiny instance. But it is an
M2 item that is not recorded anywhere, because no tool counts it.

**Fix.**
- Redraw LOGIC_SS as above.
- Optionally, add a "jog with a 2–3 segment middle" test to `route_check`: P and Q on the same heading, middle under
  1 mm or offset under 0.25 mm. This is counted on non-critical nets.

### P6-ROUTING_GEOMETRY-03 (Minor): deviation list incomplete or inaccurate (in-via steps, R6 micro-debris left inside pads, C19, D7, A1/A2 obstacle)

**Requirement.** REQUIREMENTS M2: "every review-only residual is listed, with location, rule, measured reason". The
owner accepts the list as complete.

- **(a) C17 lists 4 "steps wholly inside a via's copper"** (GND (31.3, 53.7), RADIO_NRST, PULLPIN_EXT, QSPI_IO0), and
  C16 lists BOOT0. The board has at least 8 more (13 in all), each a 45° piece inside the via joining a lane that arrives 0.07–0.2 mm
  off the via centre (`scan6.py`, `p4extra.py`):

  | Net | Layer | Step | Offset / length |
  |---|---|---|---|
  | RAW_PROTECTED | F.Cu | (38.05, 54.5) → via (37.85, 54.7) | 0.2 mm |
  | RAW_PROTECTED | F.Cu | (25.85, 40.6) → via (25.85, 40.5) | 0.071 mm |
  | VBUS | In2 | (11.0, 79.75) → via (10.8, 79.95) | 0.2 mm |
  | USB_LIMITED | F.Cu | via (25.8, 37.15) → (26.0, 37.35) | 0.2 mm |
  | GND | B.Cu | (36.4, 76.54) → via (36.5, 76.54) | 0.1 mm |
  | SERVO1_MCU | In2 | (27.1, 71.5) → via (26.9, 71.7) | 0.2 mm |
  | CAM_PWR_EN | In2 | (17.35, 89.65) → via (17.55, 89.85) | 0.2 mm |
  | SERVO3_OUT | B.Cu | via (29.14, 98.33) → (29.34, 98.13) | 0.2 mm |

  The first five are on critical power nets. All are DRC-legal and exempt from the gate by design (line 1710). I did
  not attempt their removal.
- **(b) R6 micro-segment debris whose joining pieces were deleted but whose misalignment stayed.** In R6 these joints
  carried 20–35 µm micro-segments:
  - BAT_IN B.Cu: (13.375, 31.85) → (11.875, 33.35) ends 25 µm off D8.1's centre. The outgoing run starts at the centre;
    the lines are 17.7 µm apart and joined only by the pad.
  - USB_FAULT_N B.Cu: (17.15, 66.85) → (17.15, 70.05) ends 25 µm east and 50 µm south of R90.2's centre, while the other
    run ends at (17.125, 70.0).
  - ACT_GATE B.Cu: the 0.15 mm run (7.54, 102.36) → (9.32, 104.14) Ts onto the 0.283 mm diagonal (7.7, 102.2) →
    (7.5, 102.4), 0.057 mm from its end and inside via (7.7, 102.2)'s copper. With the new D1 vertical T at
    (7.08, 102.4), that makes four nodes within 0.5 mm.
  - All are cosmetic and none is listed.
- **(c) C19** says "deleting it would change no connection (Inference)". The 0.9 mm run (8.3, 54.525) → (9.2, 54.525)
  is the first leg of C96.1's link to BAT_IN via (9.7, 54.025), through (9.2, 54.525) → (9.7, 54.025). Deleting it would
  leave that leg's end exactly on C96.1's pad edge (x 9.2 = the pad's right edge), so the joint would rest on an
  edge touch. The clean fix is to redraw the leg from inside the pad (e.g. one diagonal ending inside C96.1), not to
  delete the run.
- **(d) D7** says "the run ends 0.5 mm inside its fill". It measures 0.628 mm (`scan6.py`) and 0.621 mm (`p4extra.py`):
  still under the 1.0 mm `pour_stub` limit.
- **(e) A1/A2's "why"** names RADIO_DIO1's lane and BAT_SW_RETURN as what fixes the 0.4 mm pitch. For lanes on their via
  rows (the only way to drop the fan-in steps), the binding obstacles over most of the length are D9.1/D9.2's pads
  (top edge y 30.3) and the GND via (19.71, 30.51). The conclusion (a band re-layout) stands.

**Fix.** Add (a) and (b) to C17 or a new C row, correct C19 and D7, and name the binding obstacles in A1/A2. Optional
tidy-ups: re-centre the 8 in-via lanes, align the D8.1 and R90.2 runs, and redraw the ACT_GATE knot.

## 8. Notes (no finding)

- **Small jogs.** 23 jogs have an offset of 0.25–0.5 mm, 17 of them on critical nets. They pass the tiny-jog test
  only because their middle is ≥ 0.5 mm, and 6 of the middles are exactly 0.50–0.51 mm (Appendix A3). This is the
  definitional matter of P5-RQ-04, which was dispositioned (an offset-only test was optional and not done). Most are
  inherited or forced (band fan-in, QSPI_CLK, I2C1_SCL).
- **Via-entry pieces.** 28 short pieces lie wholly inside their via (via-entry pieces). They are counted neither by
  the gate nor here.
- **USB_DP's 1.6 mm B.Cu hop** (8.9, 74.75) is the inherited R6 USB-C A6/B6 crossover.
- **CAM_5V's 0.95 mm "hop"** (39.35, 103.6)–(39.35, 104.55) is a pair of current vias.
- **3V3_RADIO into C310.1:** the end is 0.304 mm off centre but 0.49 mm inside the 1.41 × 1.35 mm pad (D4 fix): tidy.

## Appendix A: remaining instances

### A1. Every remaining AGENTS §3 rule instance (any net)

| # | Instance | Nearest GND via | Allowlist |
|---|---|---:|---|
| 1 | RADIO_RXEN via (23.8, 39.45) | 2.230 mm | A6 |
| 2 | RADIO_NRST via (9.3, 50.0) | 3.178 mm | A7 |
| 3 | PYRO1_GATE → TP122 pad via (20.45, 92.4) | 2.928 mm | A8 |
| 4 | RADIO_BUSY via (9.4, 28.2) | 1.649 mm | A9 |
| 5 | RADIO_BUSY via (10.0, 49.5) | 2.596 mm | A10 |
| 6 | RADIO_MOSI via (9.4, 29.2) | 1.649 mm | A11 |
| 7 | RADIO_DIO1 via (10.0, 50.5) | 3.569 mm | A12 |
| 8 | RADIO_MISO_MCU via (10.0, 28.7) | 2.110 mm | A13 |
| 9 | RADIO_MOSI_MCU via (9.4, 48.5) | 1.709 mm | A14 |
| 10 | IPC-2152 high-current copper | — | C1 (not a geometry check here) |

Off-angle 0, staircases 0, exposed acute angles 0, stubs / dead copper / dangling vias 0.

### A2. Gate instances on critical nets

- Allowlisted:
  - tiny_jog: RADIO_BUSY (9.4, 28.2) A1, RADIO_MISO_MCU (10.0, 28.7) A2, SW_NODE (20.52, 36.05) A3;
  - short_segment: SW_NODE (21.32, 35.25) A4, (17.92, 35.65) A5;
  - critical_via_no_gnd: the 9 instances in A1 above;
  - detour 9 and extra_vias 10: A15–A33.
- Information (critical): as §4.1. The full lists are in the gate's `route.json` (copy at `<p6>/gate_route.json`).

### A3. Small jogs (offset 0.25–0.5 mm, middle ≥ 0.5 mm), `scan6.py`

**Critical nets:**

| Net | Layer | At | Middle / offset |
|---|---|---|---|
| 3V3 | F.Cu | (36.5, 51.65) | 0.622 / 0.44 |
| 3V3A | B.Cu | (36.4, 60.86) | 0.509 / 0.36 |
| 3V3A | In2, across a via | (35.5, 76.54) | 0.655 / 0.463 |
| BAT_IN | B.Cu | (9.845, 53.375) | 0.545 / 0.385 |
| CAM_5V | B.Cu | (34.23, 31.6) | 0.6 / 0.424 |
| GND | F.Cu | (23.97, 90.7) | 0.523 / 0.37 |
| GND | B.Cu | (42.05, 53.18) | 0.523 / 0.37 |
| GND | B.Cu | (19.03, 89.0) | 0.542 / 0.383 |
| PYRO1_CONT_MCU | B.Cu, across a via | (31.4, 52.5) | 0.566 / 0.4 |
| QSPI_CLK | F.Cu | (22.85, 44.65) | 0.509 / 0.36 |
| QSPI_IO0 | F.Cu | (13.5, 41.9) | 0.5 / 0.354 |
| RADIO_MOSI | F.Cu | (10.95, 29.2) | 0.566 / 0.4 |
| RAW_ACT | B.Cu, across a via | (12.7, 75.57) | 0.566 / 0.4 |
| RAW_PROTECTED | F.Cu | (33.75, 46.9) | 0.5 / 0.354 |
| RAW_PROTECTED | B.Cu | (38.5, 84.175) | 0.566 / 0.4 |
| USB_LIMITED | B.Cu | (28.7, 46.55) | 0.566 / 0.4 |
| VBUS | B.Cu | (13.05, 78.65) | 0.5 / 0.354 |

**Non-critical nets:**

| Net | Layer | At | Middle / offset |
|---|---|---|---|
| BAT_ILIM | F.Cu | (10.575, 38.9) | 0.5 / 0.354 |
| BAT_SW_RETURN | F.Cu | (23.6, 28.025) | 0.5 / 0.354 |
| I2C1_SCL | F.Cu | (25.35, 62.25) | 0.509 / 0.36 |
| SERVO2_MCU | In2, across a via | (20.95, 89.05) | 0.64 / 0.452 |
| VBUS_SENSE | B.Cu | (16.6, 68.0) | 0.566 / 0.4 |
| VBUS_SENSE | In2 | (13.15, 59.75) | 0.66 / 0.467 |

## Appendix B: reproduce

```
cd <p6>    # r7.kicad_pcb = final (1ffc2585…), p5board.kicad_pcb = pass-5 (c6fe595c…), r6.kicad_pcb; proj/ = project copy
PY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
R=.
$PY -I scan6.py proj/m3.kicad_pcb out/s6_r7.json; $PY -I scan6.py p5board.kicad_pcb out/s6_p5.json
$PY -I extra6.py r7.kicad_pcb; $PY -I padedge6.py r7.kicad_pcb; $PY -I diff6.py p5board.kicad_pcb r7.kicad_pcb
$PY -I scan.py r7.kicad_pcb r6.kicad_pcb out/scan2_r7.json            # 945 (591)
$PY -I scan5.py r7.kicad_pcb out/s5_r7.json; $PY -I p4scan.py r7.kicad_pcb out/s4_r7.json; $PY -I p4extra.py r7.kicad_pcb
$PY -I $R/tools/route_check.py projp5/m3.kicad_pcb --report out/rc_p5.json    # new detections on the pass-5 board
$PY -I probe.py proj/m3.kicad_pcb 0.0 0.025                              # no-GND probe: NONE for the 8 radio vias
$PY -I gs5.py proj/m3.kicad_pcb 23.8,39.45 23.8,41.05 22.6,42.25          # RXEN slide: none
./vrun.sh base; ./vrun.sh sw; ./vrun.sh lss                               # variants: DRC + parity, route_check, check_r7, actuators
$PY -I clr5.py v_sw/m3.kicad_pcb SW_NODE B.Cu 0.6 17.92,35.65 18.52,36.25 20.22,36.25 21.22,35.25 21.92,35.25 23.12,34.05
```
