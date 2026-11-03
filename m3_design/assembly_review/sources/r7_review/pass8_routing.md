# R7 review pass 8: routing geometry and quality (whole board)

Reviewer: independent, read-only. Dimension: routing geometry and quality of every track and via on all four layers,
R6-inherited copper included, against AGENTS.md §3 and the owner's clean-routing list (REQUIREMENTS M2). Scope: §3 rule
instances, jogs and knees, staircases, local bumps, detours and extra vias, vias on track bodies, split crossings,
`tools/route_check.py` and its reason audits, whether a DRC-clean edit removes each remaining exception, and whether
every fix-pass-7 (F8) change is clean.

- **Board reviewed:** `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
  `c872a3d30509cccf5f78b64cde48ef722ee85c7be23c4848b07ce4082a852de3` (F8's final board; the same SHA before and after
  this review). 1,724 tracks, 710 vias, no arcs: F.Cu 675 / 1,565.3 mm, B.Cu 768 / 1,849.9 mm, In2 281 / 1,013.1 mm,
  **In1 0**.
- **Comparison boards:** the pass-7 board `4673c0a0…96ebd` (F8's start board `f8/sb/m3.kicad_pcb`, SHA checked) and
  committed R6 `3b215ba` (`184a87e8…`, R7 y = R6 y + 18).
- **Gate on this board** (`tools/check.sh`, run by me, exit 0): DRC 0, unconnected 0, schematic parity 0, ERC 0;
  metadata/3D OK; silkscreen 0; R7 CAD contract OK; "routing hygiene: 0 failing, 45 allowlisted, 0 stale allowlist
  entries, 0 out-of-date no-GND reasons, 29 leftovers recorded (0 unrecorded, 0 stale), 0 out-of-date route figures, 0
  removable jog / staircase / short-segment / chain-detour exceptions, 1 removable local bumps on critical nets (82 bump
  windows searched): OK"; actuator contract OK; fit OK. `tools/test_route_check.py`: 50 tests OK.
- Nothing in the repository was modified except this file. Scratch (scripts, variant boards, logs):
  `<scratch>/p8rt/` (below
  `<p8>`). Variant boards were saved only under `<p8>/v/<name>/`.

## 1. Verdict

All four pass-7 findings in this dimension are closed (§3). Every F8 copper change is geometrically clean, keeps every
DRC rule, and matches the handoff's figures (§4). On the final board no AGENTS §3 geometry rule is broken: no
off-angle segment or arc, no staircase, no exposed acute angle, no stub, dangling end or dangling via, no crossing
without a node. The only §3 instances are the 9 allowlisted critical layer changes without a GND via (A6–A14) and
IPC-2152 item C1. My own GND-via spot search, with looser rules than the gate's `GndFit`, finds no spot for any of
the nine. My own bump probe (own window enumeration, candidate generator and clearance model, mixed widths included)
finds on every net exactly what the gate and the records hold: A34's between-the-pads redraw (judged), A48 (whose
reason I confirmed by DRC), and C27's two. critical_reference from the pass-7 board to the final board gives
0 lost / 0 new by both methods.

What I found is Minor: M2 items the records miss, and two fix-pass adjacencies a trivial edit avoids.

- **P8-ROUTING-01 (Minor).** Three tracks lie wholly inside their own power pour: 3V3A on In2 (5.4 mm), ACT_FET_S on
  B.Cu (2.4 mm, fix-pass-6 copper) and BAT_IN on F.Cu (2.1 mm). Each is duplicate copper, the class F8's `dup7` deleted
  for 3V3. C23's "not examined" 0.74 mm BAT_IN B.Cu hop piece also turns out to be removable. Each comes out with a
  DRC-clean edit that leaves the fills byte-equal in area and adds no `route_check` instance. Only the hop piece is in
  the records, and the gate has no test for a run inside its own pour between two junctions.
- **P8-ROUTING-02 (Minor).** Fix pass 7 made two sub-0.2 mm supply adjacencies that a trivial DRC-clean edit avoids.
  - A new BAT_IN crossbar via (9.45, 109.8) sits 0.188 mm from R123.2 (GND). It is not in C15: F8's gap scan crashed
    on the first via, so none of the seven new vias was measured. Moving the via 0.1 mm west gives 0.288 mm.
  - The VLOGIC redraw cut VLOGIC–D122.2 (3V3) from 0.225 to 0.175 mm. With its E run at y 27.7 instead of 27.8, the
    gap is 0.270 mm, for 0.14 mm more length.
- **P8-ROUTING-03 (Minor).** BAT_IN via (9.955, 44.25), R82.1's tap (inherited from R6), reaches the In2 BAT_IN plane
  only through its ring. Its centre lies 0.055 mm outside the zone outline (x 9.9), and the joint is 0.108 mm² of
  overlap. It is the only such via on the board, it is not recorded, and `via_on_track` tests tracks only. A DRC-clean
  move exists.
- **P8-ROUTING-04 (Minor).** Compound knees through a via node are neither gated nor recorded. F8's `bumps7` made one
  on 3V3A at the via (35.9632, 69.9393): N, NE 0.41 mm, via, NW 0.50 mm, N, the run resuming 0.06 mm off its
  incoming line. The gate's compound-knee and bump tests stop at via nodes. The inherited instances are forced or are
  pad terminals (§5.4).

No Critical, no Major. Nothing found is open, shorted or below a DRC rule.

## 2. Method

My scripts (KiCad 10.0.6 Python; boards loaded read-only; `<p8>`):

| Script | What it does |
|---|---|
| `geo8.py`, `scan8.py` | **Independent scan written for this pass** (no code from route_check, scan.py or the pass-6/7 scans). Per (layer, net) node graph (ends clustered at 1 µm; T = end on another segment's centre line; overlap = end inside another segment's copper). Segments: off-angle (> 0.1° or > 2 µm lateral, plus a 0.5 µm information level), zero / micro / short with an inside-pad-or-via test. Nodes: dangling, overlap-only, fill-only ends, off-centre via joints, every branch pair's angle with the inner-edge apex tested against pad and via copper, fold-backs, collinear and width-changing plain nodes. Chains: 1–4 segment-middle jogs and knees, staircases, U-turns, chain detours. Through-node single-segment jogs (vias join layers). Vias: copper layers (tracks, fills, pads), dangling, fill-only, on a same-net track body or overlapped by its copper, ring overlaps, critical / power layer changes without a GND via ≤ 1.5 mm. Same-net duplicates, collinear and side-by-side overlaps, interior crossings; foreign-net overlaps. Pad passes, pad-edge-only joints, off-centre pad ends. Short layer hops |
| `probe8.py` (`probe8s.py`) | **Own bump probe**: every 2–10 segment window of every single-layer chain (mixed widths included) that turns back (> 0.05 mm over Manhattan) and exceeds the octilinear distance by > 0.2 mm and 1.10× (looser than the gate's 0.3 mm / 1.15×), searched shortest-first with my own 1–3 segment octilinear generator (0.025 mm bends, cap L − 0.10 mm) and my own clearance model: every other-net track, via and pad (pyro pairs at 0.505 mm, RF–GND 0.255, J2 0.508, otherwise 0.155), no entry into another net's power-pour fill (`probe8s`: allowed and reported), U30 / U31 keep-outs, NPTH 0.255 mm, the true outline and Edge.Cuts circles at 0.505 mm, no same-net copper but the end branches, and path defects (acute, fold, short, tiny jog or knee, staircase) with the end branches |
| `knee8.py` | Compound knees whose middle passes **through** a via, T or pad node (P, M1..Mk, Q, Q on P's heading; middle < 0.5 mm or Q < 0.25 mm off P's line), both directions, up to 4 segments each side |
| `infill.py`, `viaedge.py`, `nearends.py` | Tracks lying inside their own net's fill on the same layer; vias joined to an own-net fill only by ring overlap; same-net track ends 1–150 µm apart |
| `gap8.py`, `padvia.py`, `ringfill.py`, `viaspot8.py`, `gndspot8.py`, `vinfo.py`, `ctx8.py`, `zinfo.py`, `fillat.py`, `diff8.py` | Edge gaps of every track and via new on the final board (vias included); via spot searches (own net, or GND within 1.5 mm of each no-GND layer change, 0.5 and 0.45 mm vias, 0.025 mm grid); via, fill and copper context; copper diff |
| `variant8.py`, `vrun8.sh` | Apply an edit list to a copy of the final board inside a copy of the project, refill natively, save `v/<name>/m3.kicad_pcb`, run `kicad-cli pcb drc --severity-all --schematic-parity`, `route_check`, `check_r7`, `check_actuators`. Variant `base` (no edit): DRC 0/0/0, `route_check` identical to the gate, so the refill matches |
| `rg/scan.py` | The pass-2 reviewers' scan, unchanged |

I also ran `tools/critical_reference.py` (both methods) from the pass-7 board to the final board and from `base` to
each variant, and `rcdiff.py` (route_check instance diff, `base` → variant).

## 3. Pass-7 findings: closure check

| ID | Pass 7 (skeptics) | R7_VALIDATION disposition | Verified on the final board |
|---|---|---|---|
| P7-ROUTING-01 | Major, upheld 2/2 | Fixed (`bumps7`, `v3pair7`; gate `local_bump`) | **Closed.** `diff8.py` p7 → final shows the five redraws exactly as recorded: 3V3A (35.9632, 69.9393) → (35.6096, 69.5857) → (35.6096, 61.6504) → (36.4, 60.86), 9.553 mm (was 10.77); CAM_5V (40.2, 32.45) → (34.575, 32.45) → (34.23, 32.105) → (34.23, 31.6), 6.618 mm; VLOGIC (28.505, 29.85) → (30.555, 27.8) → (32.27, 27.8) → (32.27, 29.2), 6.014 mm; A34 14.368 mm; via (30.4, 70.25) and its stub gone, In2 starting at via (30.17, 71.17). Gaps (`gap8.py`): 0.212 (PYRO1_CONT via), 0.271 (C60.1), 0.172 (C99.2) / **0.175 (D122.2, P8-02)**, 0.175 / 0.173 mm, as recorded. The method gap is closed: `bump_audit` gates removable local bumps on critical nets. My probe, with a looser window threshold, mixed widths and my own clearance model, finds nothing more on critical or poured nets (§5.3) |
| P7-ROUTING-02 | Minor | Fixed (`sense7`) | **Closed.** CAM_5V_SENSE In2 (32.05, 37.55) → (30.3353, 35.8353) → (34.7853, 31.3853) → (33.25, 29.85), 0.182 mm to VLOGIC_SENSE; B7 gone; 3V3_In2 4 pieces. SERVO2_OUT In2 (18.0132, 93.1) → (21.5841, 96.6709) → (22.1278, 96.6709) → (22.5903, 96.2084), 0.171 mm to the 3V3 via; B23's new reason holds: my all-nets probe finds no shorter clean window of it |
| P7-ROUTING-03 | Minor | Fixed (`bat_via7`, gate `via_on_track`) | **Closed.** Via (9.725, 35.525) is on the run's line, which is split there (B.Cu (11.9, 33.35) → (9.725, 35.525) → (9.2, 36.05)); my scan finds no via on a same-net track body except the in-fill GND ones and benign entry-piece adjacencies. The 0.74 mm piece it leaves is removable (P8-01) |
| P7-ROUTING-04 | Minor | Fixed (`v3a_hop7`, A47) | **Closed.** (35.5, 76.54) → (36.24, 75.8) → (36.68, 75.8) → (37.4, 76.52), 2.505 mm; gaps to the GND via (36.5, 76.54): NE 0.257, E 0.290, **SE 0.201 mm** (the minimum, as F8 says; no leg is at 0.34). A47's figures and blockers check out. C23's fill statement and C17's GND note are now correct: the GND joint there is a NE diagonal arriving 0.0707 mm off the via centre with a 0.1 mm piece inside it |
| P7-DOCS-01 (routing part) | Major, upheld 3/3 | Fixed (`v3pair7`) | **Closed** for the extra via and the two overlap-only joints. The new In2 start (30.17, 71.17) → (30.4, 71.4) is a 0.325 mm fan-out off the straight B.Cu run, which the gate exempts by design. It leaves the In2 and B.Cu runs side by side 0.23 mm apart (edges overlapping 0.02 mm in plan) for 2.3 mm (note §8) |

## 4. F8 copper changes: segment by segment

`diff8.py` pass-7 board → final: tracks 1,747 → 1,724, vias 708 → 710, 14 nets changed. Zone changes: the BAT_IN_B
notch, ACT_FET_S_B's west edge, and the pour trims (one new, at the 3V3A hop; the rest renumbered).

| Net / stage | New copper | Check |
|---|---|---|
| 3V3A `bumps7` | as §3 | clean. It makes a compound knee through the via (35.9632, 69.9393) (P8-04). The run narrows a GND B.Cu finger, recorded in C11 |
| 3V3A `v3a_hop7` | as §3 | clean; A47 |
| CAM_5V `bumps7` | as §3 | clean |
| VLOGIC `bumps7` | as §3 | geometry clean; 0.175 mm to D122.2 is avoidable (P8-02) |
| 3V3 A34 `bumps7` | (36.94, 52.65) → (38.45, 54.16) → (38.45, 56.75); (42.95, 57.15) → (42.95, 55.75) → (41.58, 54.38) → (41.58, 53.9) | clean; 0.175 RAW_PROTECTED via, 0.173 CAM_RX_WIRE via (C15 #35, #36) |
| 3V3 `v3pair7` | In2 (30.17, 71.17) → (30.4, 71.4) → (30.4, 78.25) | clean (fan-out, note §8) |
| 3V3 `dup7` | F.Cu hop and In2 run deleted | clean. The vias left behind are fine: (27.35, 44.25) has F.Cu, B.Cu and the In2 fill; (29.9, 43.625) has B.Cu and In2; (30.63, 31.34) and (32.33, 33.04) have F.Cu and In2. No dangling via or end |
| ACT_EN `acten7` | B.Cu R122.2 (11.75, 105.03) → (11.75, 107.95) → Q122.1 (11.1, 108.6) | clean; both ends at pad centres; vias and In2 run gone |
| ARM1_SENSE `arm1_7` | F.Cu vertical split at R180.1 (17.28, 93.55) | clean; no pyro copper moved |
| CAM_FAULT_N `tidy7` | In2 (16.0438, 67.4556) → (18.1438, 67.4556) → (18.1438, 64.0238) → (19.8205, 62.3471) | clean; 0.169 mm to SERVO4_MCU (C15 #18) |
| I2C1_SDA `tidy7` | F.Cu (25.85, 61.05) → (25.85, 60.0) → (26.55, 59.3) → (27.8, 59.3) | clean; 0.275 mm |
| CAM_5V_SENSE, SERVO2_OUT `sense7` | as §3 | clean |
| BAT_IN `bat_via7` | via (9.725, 35.525), run split | clean; the 0.74 mm piece is removable (P8-01) |
| BUZZ_DRV `review7` | B.Cu (7.0, 56.15) → (7.0, 64.1) → (4.3, 66.8) → (4.3, 85.1) | clean; 0.517 mm from the M3 hole (4, 64) edge (rule 0.5). The SW kink before it is forced by C96.2 |
| IMU_INT1 `review7` | B.Cu (26.3, 66.3) → (26.9364, 66.9364) → (26.9364, 67.5636) → (26.55, 67.95) | clean; 0.191 mm to the SERVO1/2_MCU vias. It is still a non-critical bump window, and no shorter clean redraw exists |
| GND `necks7` | via (18.975, 83.85) and its track deleted | no dangling copper. USB_LIMITED via (17.925, 83.15) is now `power_via_no_gnd` (information); no critical layer change lost its GND via (same 9 as before) |
| BAT_IN `necks7` | six vias (9.45–10.2, 104.05–114.3) stitching the F.Cu crossbar to In2 | each ring wholly inside both fills (`ringfill.py`). **(9.45, 109.8) is 0.188 mm from R123.2 (GND)** (P8-02) |
| zones `bat_in_b7`, `necks7` | BAT_IN_B 0.1 mm notch; ACT_FET_S_B west edge 1.3 → 0.6 mm | BAT_IN_B one piece, 70.85 mm², bbox x ≤ 12.45; ACT_FET_S_B one piece, 43.14 mm². No sliver or finger (gate) |

`scan8.py`, pass-7 board → final board, category by category:
- New instances: the 3V3A hop chain detour (A47), extra-bend runs on 3V3A and BUZZ_DRV (information), the 3V3
  fan-out (§8), six fill-only BAT_IN stitching vias, one power-via-no-GND (USB_LIMITED) and the BAT_IN short hop.
- Gone: ARM1_SENSE's pass-through and chain detour, CAM_FAULT_N's and I2C1_SDA's chain detours, CAM_5V_SENSE's chain
  detour, three 3V3 vias on track bodies or hops, the ACT_EN hop, two in-via 0.08–0.21 mm pieces.

## 5. Whole-board scans

### 5.1 Independent scan (`scan8.py`, final board)

| Category | Count | Notes |
|---|---|---|
| off-angle / arcs / zero / micro (< 50 µm) | **0 / 0 / 0 / 0** | also 0 at the 0.5 µm information level |
| short (< max(w, 0.2 mm)) in open routing | **0** | 31 short pieces, all wholly inside a via or pad |
| staircase (chains) | **0** | 33 extra-bend runs (information) |
| tiny jog / knee in chains | 2 | A1, A2 |
| through-node single-segment jogs | 2 open + 10 inside a via (each counted from both ends) | the 2 open ones are fan-outs, which the gate exempts: 3V3 In2 at (30.17, 71.17) and BAT_FAULT_N at (11.9, 42.1). The 10 inside a via are 10 of C17's 12 steps |
| through-node compound knees (`knee8.py`) | 8 | P8-04 / §5.4 |
| acute (0.5–89.5°), exposed | 10, **0 exposed** | all 45° pairs at pads or vias |
| fold-back / crossing without node / foreign overlap | **0 / 0 / 0** | |
| dangling / overlap-only / fill-only ends | **0 / 0 / 1** | RAW_ACT (7.6, 81.57), A41 |
| collinear unmerged / duplicate / collinear overlap / side-by-side | **0 / 0 / 0 / 0** | |
| width change: collinear / plain node | 3 / 2 | pad-entry necks within 1 mm of their pad (part F), unchanged since pass 7 |
| off-centre via ends without a track at the centre | **0** | 63 off-centre ends, all in via-entry pieces with a track at the centre |
| critical layer change without a GND via ≤ 1.5 mm | **9** | A6–A14 exactly |
| power layer change without a GND via | 34 | = `power_via_no_gnd` |
| dangling via | 1 | BAT_IN (9.955, 44.25): a centre-only false positive, but the joint really is a ring-edge overlap (P8-03) |
| via on a same-net track body, not in its own fill | 16 | every one is an entry-piece neighbour whose copper grazes the via ring, with a track at the via centre on that layer. None is a body-through via |
| tracks inside their own non-GND pour | 3 (+1 pour entry) | P8-01 |

### 5.2 Reference scans

- **Pass-2 `scan.py`** (unchanged, vs R6): **904 instances (549 critical)**, from 918 (559) on the pass-7 board.
  chain_detour 50 → 47 (critical 30 → 30), equal to F8's figure.
- **`route_check`** on this board: 326 instances (chain_detour 9, pour_net_hop 5, tiny_jog 2, critical_via_no_gnd 9,
  detour 21, extra_vias 27, local_bump 1, information 252), 0 failing; equal to the handoff and part E.

### 5.3 Bump probes (`probe8.py`)

- **Critical and poured nets:** 83 windows (the gate: 82). Found: USB_LIMITED B.Cu (A48), and 3V3 A34 (38.45, 54.16)
  → (41.58, 54.38) through C11's 0.65 mm pad gap (3V3 between a 3V3A and a GND pad). A34's reason names that drawing
  and rejects it, a judgement I share.
- **All nets:** 258 windows. Found: those two, plus VLOGIC_SENSE In2 (10.896 → 10.562) and BAT_SW_SOURCE F.Cu
  (12.81 → 11.01), which are C27's two (judged).
- **Pours allowed (`probe8s.py`).** Two more critical candidates, both tried as variants:
  - USB_LIMITED In2 (29.1, 40.55) → (25.8, 37.15), 7.40 → 4.81 mm: DRC 0/0/0 and 0 lost, but 3V3_In2 goes 4 → 5
    pieces. C24's "splits the pour" judgement stands.
  - QSPI_IO2 In2: DRC reports C13.1's 3V3 cut off.
  - So the gate's strict pour test hides no removable bump on this board.

The A48 reason checks out on a variant. Applying `bump_audit`'s 3.444 mm redraw gives "Missing connection: R105 pad 2
[GND]" and a starved thermal at R105.2 (`v/a48`). `gndspot8`/`viaspot8` find no legal GND via spot near R105.2 that
could replace the cut copper.

### 5.4 Through-node compound knees (`knee8.py`)

Eight places where a run turns off its heading at a via, T or pad node and comes back onto it (Q < 0.25 mm off P's
line). Neither the gate's compound test (plain chains only) nor its through-node test (single middle segment) sees
these.

| Node | Net | Shape (Q off P's line) | Judgement |
|---|---|---|---|
| via (35.9632, 69.9393) | **3V3A** (F8 `bumps7`) | U5.2 N → NE 0.415 → via → NW 0.500 → N (0.060 mm) | new; reasonable (the via is the In2 feed and NRST's via (36.3, 64.8) blocks x 35.96), but unrecorded (P8-04) |
| via (30.17, 71.17) | 3V3 (F8 `v3pair7`) | B.Cu S → via → In2 SE 0.325 → S (0.23 mm) | a fan-out off the straight B.Cu run (gate exemption); note |
| via (16.5, 33.15) | VLOGIC (R6) | F.Cu NE → N 0.8 → via → B.Cu E 0.7 → NE (0.071 mm) | forced: the NE redraw of the B.Cu leg shorts U2.1 (3V3) (`v/vlk`: DRC shorting_items) |
| via (44.76, 61.1) | BAT_SW_SOURCE (R6) | F.Cu S x 45.4 → SW → via → B.Cu SE → S x 45.26 (0.14 mm) | forced by the 0.5 mm edge rule (a via on the x 45.3 line would sit 0.45 mm from the edge) |
| via (18.4785, 59.6799) | LOGIC_SOURCE_ST (R6) | (0.05 mm) | non-critical; part of B18's 11-via route |
| C8.2, C87.1, R101.2 | GND, BAT_ENABLE, CAM_TX_WIRE | V into a pad centre | pad terminals, not jogs |

### 5.5 Split crossings and references

critical_reference from the pass-7 board to the final board: **0 lost, 0 candidate-new** for both the R6 method
(69,190 referenced) and the extended method (168,254), which reproduces F8's figures. Variants `batpiece`, `c95`,
`afs`, `a3in2s`, `xvia`, `r82via`, `vl277` and `dup8` (all of P8-01..03 combined) each lose 0 samples against `base`
(`dup8` checked with `--extended`). The 7 recorded U1-end split crossings (C5) are unchanged.

## 6. Remaining exceptions: can a DRC-clean edit remove them?

| Items | Result |
|---|---|
| A1, A2 | copper unchanged since pass 6; `alt_audit` re-searches them every run (no redraw); not re-probed |
| A6–A14 | **confirmed**: my own GND-via search (0.5 and 0.45 mm vias, 0.025 mm grid, 0.155 mm to all copper, test pads 1.02, J2 0.528, pyro bus 0.52, edge 0.5, and no 7.7 A corridor policy, which makes it looser than `GndFit`) finds no spot within 1.5 mm of any of the nine. It finds thousands at control points (30, 100), (20, 22), (38, 70), so the search works |
| A15–A33 (net-level detour / extra vias) | figures match (`measured_check` passes); the raster-search results are F5's (not re-run, as the records say); my probes find no removable window on these nets |
| A34 | only the C11 between-the-pads redraw, rejected by judgement (shared); a C100.1 via into 3V3_In2 is not available, because no 3V3 In2 fill reaches C100 (`fillat.py`) |
| A35–A41, A47 | no clean shorter 1–3 segment redraw (probe; gate `alt_audit`) |
| A42–A46 | blockers as recorded (F7 probes; copper unchanged by F8); not re-probed |
| A48 | reason confirmed by DRC (§5.3) |
| B1–B30 | my all-nets probe finds no removable window except C27's two |
| C23 BAT_IN 0.74 mm piece ("not examined") | **removable** (P8-01) |
| C17, C19, C21, C22 ("not attempted") | not attempted here either; cosmetic, listed. `nearends.py` also finds about ten more R6 pad entries where two same-net ends sit 20–54 µm apart inside one pad (I2C1_SCL U5.8, RAW_ACT TP120.1, SERVO2_MCU R155.1, CAM_5V U13.1 / C91.1, 3V3 C100.1, BAT_OVLO R82.2, SW_NODE C5.1, I2C1_SCL R12.1). All are joined by the pad; no finding |
| C27 | judged as recorded |
| C1 | owner decision; RAW_ACT_F is 3.01 mm wide at y 80.6–81.0 (my raster), as F8 states |

## 7. Findings

### P8-ROUTING-01 (Minor): three tracks lie wholly inside their own power pour, and C23's BAT_IN hop piece is removable; all come out with DRC-clean edits, and only the hop piece is in the records

**Requirement.**
- REQUIREMENTS M2 forbids duplicate copper and needless layer hops over the whole board, inherited copper included.
- Every review residual is listed with a measured reason why it cannot reasonably be removed.
- F8's `dup7` deleted two 3V3 runs of exactly this class for P7-DOCS-02(b).

**Finding** (`infill.py`, `ctx8.py`, `zinfo.py`; final board):

1. **3V3A In2** (35.9632, 69.9393) → (35.9632, 76.0768) → (35.5, 76.54), w 0.2 mm, inherited from R6.
   - From y 70.6 on, it lies inside the 28.17 mm² 3V3A_In2 fill, and so does its second segment: 6.1 mm in all.
   - Only the first 0.66 mm, from the via, which sits outside the zone outline (31.0–38.6, 70.6–83.6), is needed. The
     variant keeps the first 1.36 mm and removes 5.4 mm.
2. **ACT_FET_S B.Cu** R120.1 (5.17, 96.0) → (5.17, 94.64) → Q120.1 (5.91, 93.9), w 0.4 mm, fix pass 6's `ties6`.
   - It lies inside ACT_FET_S_B, and both pads are solid to that pour. Only 0.084 mm² of the track lies outside the
     fill, under R120.1.
3. **BAT_IN F.Cu** via (9.2, 36.05) → C95.1 (7.1, 36.05), w 0.2 mm, R6 copper.
   - Fix pass 6 grew BAT_IN_F to x 9.9, so the whole track now lies inside BAT_IN_F.
   - C95.1 is solid to that pour, and the via sits inside both BAT_IN fills.
4. **BAT_IN B.Cu** piece (9.725, 35.525) → (9.2, 36.05), 0.742 mm. Both vias lie wholly inside the BAT_IN_F and In2
   fills, so the piece parallels the pours. C23 and the owner summary call it "not examined".

**Evidence** (variants, each against `base`):

| Variant | Edit | DRC (with parity) | `route_check` | Fills |
|---|---|---|---|---|
| `a3in2s` | 3V3A In2 run replaced by its first 1.36 mm (to y 71.3) | 0/0/0 | identical | 3V3A_In2 28.17 mm², 1 piece, 230 points, as before |
| `afs` | ACT_FET_S tie deleted | 0/0/0 | identical | ACT_FET_S_B 43.14 mm², 1 piece |
| `c95` | BAT_IN F.Cu track deleted | 0/0/0 | −1 `power_via_no_gnd` | BAT_IN_F 41.82 mm², 1 piece |
| `batpiece` | 0.742 mm B.Cu piece deleted | 0/0/0 | −`short_layer_hop`, −`power_via_no_gnd` | — |
| `dup8` | all four, plus P8-02's via move | 0/0/0, every check OK | as above | as above; critical_reference `--extended` 0 lost / 0 new |

- Deleting the whole 3V3A run (`a3in2d`) does fail: via_dangling, and U5.2 is cut from U4. The 0.66 mm feed is
  therefore needed.
- `route_check` has no test for this class. `pour_stub` judges only a track end that touches nothing but its pour;
  these runs join two junctions.

**Electrical effect.** None (Inference): the fills already cover the copper, so the fabricated copper of items 1–3
is unchanged. Item 4 removes 0.74 mm of B.Cu that parallels two vias, each inside both BAT_IN fills.

**Why Minor.** These are CAD-database duplicates with no fabricated-copper or electrical effect (items 1–3), plus a
disclosed hop piece. It is the same class as P7-DOCS-02(b), which pass 7 graded Minor. The P7-ROUTING-01 Major
pattern (removable M2 items on critical nets missing from the list) argues for more, but nothing here changes the
board as built.

**Fix.**
- Apply the `dup8` edits in `r7_polish` (or record each item in C23).
- Delete C23's "not examined" sentence.
- Consider a gate test: a track whose centre line lies more than about 90 % inside its own net's fill on its layer,
  on a non-GND net.

### P8-ROUTING-02 (Minor): two sub-0.2 mm supply adjacencies made by fix pass 7 can be avoided by trivial DRC-clean edits; one is not recorded because F8's gap scan never measured the new vias

**Requirement.**
- C15's stated scope: every edge gap under 0.2 mm that fix-pass copper created is listed with what a short would do.
- The handoff (§3) claims a gap scan of "every added track / via".
- M2 and robustness: do not trade clearance on supply nets without need.

**Finding.**

1. **BAT_IN crossbar via (9.45, 109.8) (`necks7`), 0.188 mm from R123.2 (GND, B.Cu).**
   - Measured with `padvia.py` from R123.2's polygon, and confirmed with `gap8.py`.
   - F8's `newgap.py` stopped with `TypeError: in method 'SHAPE_CIRCLE_Collide'` at the first via
     (`<scratch>/f8/newgap_final.txt`, last lines). None of the seven new vias was measured, and this pair is absent
     from C15 and from the handoff's gap list.
   - A short there connects the battery input to GND.
2. **VLOGIC F.Cu (`bumps7`), 0.175 mm from D122.2 (3V3); it was 0.225 mm.**
   - C15 #39 records it as the cost of the redraw: a short would put pack voltage on every 3V3 part.
   - The records do not say that a drawing with the E run 0.1 mm further north keeps more clearance.

**Evidence.**
- `v/xvia`: via moved to (9.35, 109.8).
  - Gap to R123.2 0.288 mm, ring still wholly inside the crossbar F.Cu fill and the In2 fill (`ringfill.py`).
  - DRC 0/0/0; `route_check` instance list identical.
- `v/vl277`: VLOGIC (28.505, 29.85) → (30.655, 27.7) → (32.27, 27.7) → (32.27, 29.2).
  - DRC 0/0/0. VLOGIC–D122.2 0.270 mm (the S leg; the E run gives 0.275). C99.2 stays at 0.172 mm (same diagonal
    line), PULLPIN at 0.230 mm, and the GND via (32.2, 27.033) at 0.296 mm.
  - Length 6.014 → 6.15 mm. `route_check`'s only change is A33's quoted figure (66.37 → 66.51 mm), which
    `measured_check` flags until it is updated.
- Both variants lose 0 critical_reference samples.

**Why Minor.** Both gaps are DRC-legal (0.15 mm), the via is tented, and electrical test screens etch shorts
(Inference). The fault is an unrecorded, avoidable clearance on the board's highest-energy net and an avoidable 3V3
over-voltage adjacency, both created by the fix pass.

**Fix.**
- Move the via to (9.35, 109.8).
- Draw VLOGIC's E run at y 27.7 and update A33's figure. Otherwise record both in C15 with these options.
- Fix `newgap.py` (use `SHAPE_SEGMENT` / `pt_seg` for vias) and re-measure the seven vias.

### P8-ROUTING-03 (Minor): BAT_IN via (9.955, 44.25) reaches its In2 plane only through ring overlap, with its centre outside the zone outline

**Requirement.** M2: no overlap-only joints; vias joined cleanly to what they serve.

**Finding.** R82.1's (BAT_IN) F.Cu tap ends in the via (9.955, 44.25), whose only other copper is the In2 BAT_IN plane
(`viafill.py`, `vinfo.py`):
- The R6_BAT_IN_In2 outline edge is x 9.9, so the via centre lies 0.055 mm outside the outline.
- Fill and ring overlap by 0.108 mm² of the ring's 0.283 mm².
- It is inherited from R6, at the same place minus 18 mm.
- `viaedge.py` finds no other via on the board joined to an own-net fill this way.
- KiCad's connectivity and DRC accept it, because the plane edge passes inside the drill radius. It is not in the
  records, and `route_check`'s `via_on_track` tests tracks only.

**Evidence.**
- `v/r82via`: via moved to (9.8, 44.15), inside the fill, with the F.Cu tap redrawn (9.455, 43.25) → (9.8, 43.595) →
  (9.8, 44.15).
- DRC 0/0/0; `viaedge.py` 0; `route_check` adds two information instances (pad_end_offcentre and segment_inside_pad
  at R82.1). A neater tap from R82.1's bottom edge is possible.
- `viaspot8.py` lists the legal in-fill spots at (9.65–9.8, 44.0–44.15).

**Why Minor.** It is electrically sound: the plane reaches the barrel (Inference). It is a cosmetic, unrecorded joint
on a µA divider tap.

**Fix.** Move the via into the fill (or extend the outline locally), or record it in C21. Optionally let the gate flag
a via whose centre lies outside every own-net fill that its ring overlaps, on a layer where it has no track.

### P8-ROUTING-04 (Minor): compound knees through a via node are neither gated nor recorded, and F8's 3V3A redraw created one

**Requirement.** M2: no tiny jogs. The gate's tiny_jog covers compound knees (fix pass 6) in plain chains only, and
single-segment middles through T / via / pad nodes (fix pass 5). The records present every jog as gated or listed
(A1, A2, C16, C17).

**Finding.**
- 3V3A B.Cu, U5.2 (35.67, 71.175) → (35.67, 70.2325) → NE 0.415 → via (35.9632, 69.9393) → NW 0.500 →
  (35.6096, 69.5857) → N.
- The run dents 0.29 mm east to touch the via (the In2 feed of the 3V3A island) and resumes 0.0604 mm off its
  incoming line. In a plain chain this would be a gated compound tiny jog (Q < 0.25 mm off P's line).
- It is new in `bumps7`; the pass-7 drawing left the via NE and was monotone (`knee8.py`: 6 knees on the pass-7 board,
  8 on the final board).
- The other through-node knees (§5.4) are forced (VLOGIC by U2.1, BAT_SW_SOURCE by the edge), non-critical
  (LOGIC_SOURCE_ST) or pad terminals.

**Evidence.** `knee8.py` on both boards. The non-V drawing (via → N on x 35.9632 to y ≥ 65.27, NW 0.5, N) is the same
length with one more bend, and it would move the dogleg next to NRST's via. So I do not claim a better drawing, only an
unlisted instance.

**Why Minor.** It is cosmetic: 0.6 mm of 0.25 mm 3V3A track, DRC-legal, with no electrical effect (Inference).

**Fix.** List the 3V3A knee, and the forced VLOGIC one, in C16 with their blockers. Optionally extend the compound
test across via and T nodes, with the gate's existing fan-out exemption, which excludes the 3V3 In2 start.

## 8. Notes (no finding)

- **3V3 In2 fan-out at (30.17, 71.17).** The 0.325 mm SE piece leaves the via 0.025 mm beyond its ring before turning
  S, and the In2 run then lies 0.23 mm (centre to centre) beside the B.Cu run (30.17, 71.17–73.7) for 2.3 mm. These
  are own-net branches to different loads (R12 / R13 on B.Cu, D120.3 via In2), not duplicates. The alternative (In2
  straight down x 30.17 under the B.Cu run, stepping to x 30.4 at the far via) only moves the step.
- **3V3 A34's inherited SE diagonal** (38.45, 56.75) → (40.25, 58.55) runs 0.199 mm beside RAW_PROTECTED's parallel
  diagonal (37.85, 56.75) → (40.2, 59.1) for about 2.5 mm. It is R6 copper, so outside C15's scope by its own
  definition. A short would put up to 8.4 V on 3V3, like C15 #35.
- **BUZZ_DRV** now passes the M3 hole (4, 64) at 0.517 mm against the 0.5 mm edge rule (it was 0.775 mm on the west
  side). It is masked copper under the support footprint, as before; fit_check treats masked routing as no hardware
  obstacle.
- **`bump_audit`** skips windows of mixed track width (`bump_windows`, "one width"), while the records say it searches
  "every 2–8 segment window". My probe includes mixed widths and finds nothing more on this board, but the records
  should state the limit. The strict pour test hides nothing removable here (§5.3).
- **C86.2's GND via removal (`necks7`)** leaves C86 (RAW_ACT decoupling) on GND_F thermal spokes, with J122.3 2.4 mm
  away as the nearest stitch. That is an electrical trade for the neck, recorded in C1; not a routing defect.

## Appendix: reproduce

```
cd <p8>   # r7.kicad_pcb = final (c872a3d3…), p7.kicad_pcb = pass-7 (4673c0a0…), r6.kicad_pcb (184a87e8…), proj/ = project copy
PY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
R=.
$PY scan8.py r7.kicad_pcb s8_final.json; $PY scan8.py p7.kicad_pcb s8_p7.json
$PY -I ../rg/scan.py r7.kicad_pcb r6.kicad_pcb scan2_final.json                 # 904 (549)
$PY diff8.py p7.kicad_pcb r7.kicad_pcb; $PY gap8.py p7.kicad_pcb r7.kicad_pcb
$PY probe8.py r7.kicad_pcb pr8_crit.json; $PY probe8.py r7.kicad_pcb pr8_all.json all; $PY probe8s.py r7.kicad_pcb pr8_soft.json soft
$PY knee8.py r7.kicad_pcb; $PY infill.py r7.kicad_pcb; $PY viaedge.py r7.kicad_pcb; $PY nearends.py r7.kicad_pcb
$PY gndspot8.py r7.kicad_pcb 23.8,39.45 9.3,50.0 20.45,92.4 9.4,28.2 10.0,49.5 9.4,29.2 10.0,50.5 10.0,28.7 9.4,48.5
./vrun8.sh base e_base.json; ./vrun8.sh dup8 e_dup8.json; ./vrun8.sh vl277 e_vl277.json; ./vrun8.sh r82via e_r82via.json
./vrun8.sh a48 e_a48.json; ./vrun8.sh usbl e_usbl.json; ./vrun8.sh vlk e_vlk.json      # (and batpiece, afs, c95, a3in2s, a3in2d, xvia, qio2)
python3 rcdiff.py v/base/rc.json v/dup8/rc.json
$PY -I $R/tools/critical_reference.py p7.kicad_pcb r7.kicad_pcb --dy 0 [--extended]
$PY -I $R/tools/critical_reference.py v/base/m3.kicad_pcb v/dup8/m3.kicad_pcb --dy 0 --extended
```
