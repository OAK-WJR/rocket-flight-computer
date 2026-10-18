# R7 review pass 7: routing geometry and quality (whole board)

Reviewer: independent, read-only. Dimension: routing geometry and quality of every track and via on all four layers,
R6-inherited copper included, against AGENTS.md §3 and the owner's clean-routing list (REQUIREMENTS M2): §3 rule
instances, jogs (multi-segment knees included), staircases, detours and extra vias (poured nets included), bumps,
split crossings, overlap-only joints; the soundness of `tools/route_check.py` and its reason audits; for every remaining
exception, whether a DRC-clean edit removes it; and whether the fix-pass-6 (F7) changes are clean.

- **Board reviewed:** `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
  `4673c0a0f9fd290af694d6ca5a97e99b3b225466882ba5c6e57a9ad856b96ebd` (F7's final board; the same SHA before and after
  this review). 1,747 tracks, 708 vias, no arcs: F.Cu 681 / 1,571.8 mm, B.Cu 778 / 1,858.3 mm, In2 288 / 1,025.6 mm,
  **In1 0**.
- **Comparison boards:** the pass-6 board `1ffc2585…cdf9df` (F7's `fx6/base.kicad_pcb`, SHA checked) and committed R6
  `3b215ba` (`184a87e8…`, +18 mm in y).
- **Gate on this board** (`tools/check.sh`, run by me, exit 0): DRC 0, unconnected 0, schematic parity 0, ERC 0;
  metadata/3D OK; silkscreen 0; "R7 CAD contract: OK"; "routing hygiene: 0 failing, 43 allowlisted, 0 stale allowlist
  entries, 0 out-of-date no-GND reasons, 30 leftovers recorded (0 unrecorded, 0 stale), 0 out-of-date route figures, 0
  removable jog / staircase / short-segment / chain-detour exceptions: OK"; actuator contract OK; fit OK.
  `tools/test_route_check.py`: 45 tests OK.
- Nothing in the repository was modified except this file. Scratch work (scripts, variant boards, logs, renders):
  `<scratch>/r7p7geo/`
  (below `<p7>`). Variant boards were saved only under `<p7>/v7_*`.

## 1. Verdict

All pass-6 findings in this dimension are closed or properly dispositioned (§3), and every F7 copper change is clean
on its own terms (§4). On the final board no AGENTS §3 geometry rule is broken anywhere: no off-angle segment or arc,
no staircase (also through T / via / pad nodes), no exposed acute angle, no stub, dangling end or dangling via, no
crossing without a node; the only §3 instances are the 9 allowlisted critical layer changes without a GND via
(A6–A14) and the IPC-2152 item C1, as recorded.

What remains is in the owner's wider M2 list (needless detours / extra vias, overlap-only joints). My sub-chain bump
probe (§5.3), which the gate and the records' chain-detour sweep do not have, found DRC-clean edits that the deviation
list does not mention:

- **P7-ROUTING-01 (Major).** Needless local bumps and an extra via on critical power nets, each removed by a DRC-clean
  edit that adds no `route_check` instance and loses no reference sample, are in no deviation-list entry: a 1.22 mm
  eastward bulge on 3V3A (B.Cu), a 0.88 mm V-dip on CAM_5V (B.Cu), a 0.60 mm peak on VLOGIC (F.Cu), 1.81 mm of A34's
  3V3 detour (whose "why" is therefore untrue and also names the wrong parts), and a second 3V3 via plus a 0.81 mm
  T-stub at (30.4, 70.25) joined to its neighbour via only by copper overlap. The gate cannot see these: `chain_detour`
  judges a whole run between junctions, and `alt_audit` accepts a redraw only if it ends the detour.
- **P7-ROUTING-02 (Minor).** On non-critical nets, B7 (CAM_5V_SENSE) and B23 (SERVO2_OUT) have DRC-clean shorter
  redraws that contradict their recorded reasons. CAM_5V_SENSE's present In2 route also fences a 17.64 mm² piece of
  the 3V3_In2 plane off from the main plane; the redraw rejoins it (5 → 4 pieces).
- **P7-ROUTING-03 (Minor).** F7's new BAT_IN via (9.7, 35.5) sits on the body of the B.Cu BAT_IN track, 35 µm off its
  centre line, with no track end in it: an overlap-only joint that fix pass 6 created. It is not recorded, and
  `route_check` has no test for a via joined to a track only by overlap.
- **P7-ROUTING-04 (Minor).** F7's 3V3A-hop "fix" is a threshold artefact: the run still turns back, now passing the gate
  by 4 µm, and its gap to the GND via is halved, from 0.34 to 0.169 mm. C23's "the first via in the 3V3A_In2 fill" is
  false, since both vias sit in one 28.17 mm² island. Two smaller record inaccuracies are listed in the finding.

No Critical. Nothing found is open, shorted or below a DRC rule.

## 2. Method

My scripts (KiCad 10.0.6 Python, boards loaded read-only; `<p7>`):

| Script | What it does |
|---|---|
| `scan7.py` | **Independent scan written for this pass** (no code from route_check, scan.py or scan6.py). Per (layer, net) node graph (ends clustered at 1 µm; node = ends / pads / vias / T / overlap). Segments: heading error (0.02° or 0.5 µm), zero / micro / short with an inside-pad-or-via test. Nodes: dangling, overlap-only, fill-only ends, off-centre via joints, every branch pair's angle with the inner-edge apex tested against pad / via copper, fold-backs, collinear and width-changing plain nodes. Chains: jogs with 1–4 segment middles (offset, middle length), staircases, U-turns. Through-node jogs (P into one node, S, Q out of the other on P's heading, vias joining layers). Same-net duplicates, parallel overlaps, interior crossings. Vias: copper layers, ring overlaps, critical / power layer changes against the nearest GND via. Layer-agnostic runs through plain nodes and pure layer-change vias: run detours, series vias, hops, and every **minimal sub-window** whose length exceeds the octilinear distance of its ends by > 0.4 mm and > 1.2× ("bumps"). Pad entries (offset, distance to the pad outline) |
| `probe7.py` | Every minimal single-layer window of a chain (> 0.3 mm and > 1.15× over the octilinear distance of its ends), on every net, handed to the project's own redraw machinery (`route_check.alt_window` / `alt_candidates`, `r7_hygiene.Clearance`, keep-outs, NPTH 0.26 mm, edge 0.3 mm) with the cap "at least 0.15 mm shorter than the window" instead of `alt_audit`'s "must end the detour" |
| `mkedit.py`, `edit7.py`, `vrun7.sh` | Turn a candidate into an edit list, apply it to a copy of the final board, refill zones natively, save `v7_<name>/m3.kicad_pcb`, then run `kicad-cli pcb drc --severity-all --schematic-parity`, `route_check`, `check_r7`, `check_actuators` and a pour piece / area comparison (`pourstat.py`). Variant `base` (no edit): DRC 0/0/0 and every check OK, so the refill matches the gate |
| `diff7.py`, `gaps.py`, `viatrk.py`, `viaovl.py`, `island.py`, `islands.py`, `ctx7.py`, `fillnear.py`, `zonesat.py` | Copper diff between boards; edge gaps of added copper to other-net copper; vias on same-net track bodies; overlap-only via joints; fill islands; local copper / fill context |
| `scan2.py` (= `rg/scan.py`), `render.py` (= `rg/render.py`) | The pass-2 reviewers' scan and renderer, unchanged |

I also ran `tools/critical_reference.py --extended` (variants against the refilled base, `--dy 0`), the final
`route_check` on the pass-6 board, and `tools/test_route_check.py`.

## 3. Pass-6 findings: closure check

| ID | Pass 6 (skeptics) | R7_VALIDATION disposition | Verified on the final board |
|---|---|---|---|
| P6-ROUTING_GEOMETRY-01 SW_NODE | Minor | Fixed (`sw6`), A3–A5 deleted | **Closed.** B.Cu 0.6 mm: (17.92, 35.65) → (18.52, 36.25) → (20.22, 36.25) → (21.22, 35.25) → (21.92, 35.25) → (23.12, 34.05), the reviewer's redraw exactly (`diff7.py`). Min gap 0.213 mm (3V3 via (18.7, 35.28)). No SW_NODE entry in `ALLOWLIST`; my scan finds no short or tiny piece on SW_NODE. The final `route_check` run on the pass-6 board fires on the three old SW_NODE instances |
| P6-ROUTING_GEOMETRY-02 two-segment jogs | Minor | Fixed (tool + `logic_ss6`) | **Closed.** LOGIC_SS: U11.11 → (28.95, 29.65) (pad edge) → SW diagonal → (27.55, 31.05); 0.183 mm to U11.12 (GND). The new compound test fires on the pass-6 board's LOGIC_SS knee (`FAIL … tiny_jog LOGIC_SS B.Cu (28.95, 29.85)`). My 1–4-segment-middle chain test finds only IMU_INT1 (26.3, 66.3), offset 0.25 mm at 4 decimals (records: 0.2503, not tiny) |
| P6-ROUTING_GEOMETRY-03 records | Minor | Fixed (records) | **Closed, one nit.** C17 lists 12 in-via steps; my through-node scan finds exactly those 12 plus GND (36.4, 76.54). The records say that one "is no longer a step" because "fix pass 6's 3V3A redraw left a NE diagonal arriving 0.071 mm off the via centre". The GND copper there is identical on the pass-6 and final boards: (36.0, 76.94) → (36.4, 76.54) → (36.5, 76.54), so the stated cause is wrong (P7-04). C21 (D8.1, R90.2 debris, ACT_GATE knot), C19, A41 (0.628 mm) and the A1/A2 obstacle text are as stated |
| P6-ROUTING_QUALITY-01 QSPI_IO3 | Major → Minor (2:1) | Fixed (`qspi6`) | **Closed.** One F.Cu segment (22.5, 40.3) → (22.5, 35.4), 0.205 mm to U3.8 (the gap the run already had); the NW diagonal into U3.7 unchanged |
| P6-ROUTING_QUALITY-02 / -03 | Minor | Records | **Closed** (C5 per-line figures; C15 adjacencies; C22 NRST stacking) |
| P6-REGRESSION-01 BAT_IN_F vias | Minor | Fixed (`bat_in_f6`) | **Closed for the stitching**: BAT_IN_F is one 41.82 mm² piece (outline (4.4, 25.7)–(9.0, 31.4)–(9.9, 31.4)–(9.9, 36.9)–(4.4, 36.9)), and both new vias lie in the F.Cu and In2 BAT_IN fills. But via (9.7, 35.5) lands on a B.Cu track body: **P7-03** |
| P6-REGRESSION-02 SERVO4_MCU / CAM_FAULT_N | Minor | Fixed (`servo_fault6`) | **Closed.** Parallel runs 0.714 mm apart (`gaps.py`); the steps are 45° and parallel. CAM_FAULT_N at x 15.19 is 0.165 mm from CAM_PWR_EN's via (14.65, 92.95), inherited from fix pass 5 and recorded (M3_R7 l.555) |
| P6-REGRESSION-03 | Minor | Records | **Closed** (C15) |
| P6-DOCS-01 poured-net detours / hops | Major (2:1) | Gate + records; owner decision open | **Gate part closed as specified**: `chain_detour` / `pour_net_hop` fire on every start-board instance (the final tool on the pass-6 board lists the 3V3 dip, the J3 / J1 GND ties, RAW_ACT's duplicate, the 3V3A hop and ACT_FET_S). **Residual scope gap:** whole-run windows plus the "end the detour" cap miss local bumps and partial reductions on poured nets (**P7-01**) |

The five items the records list as "removable but not removed" (C24 ARM1_SENSE; C25 CAM_FAULT_N, LED_RED, I2C1_SDA;
C26 ACT_EN) are still on the board. My probe independently re-finds four of them (ARM1_SENSE −0.31 mm, CAM_FAULT_N
−3.85 mm, LED_RED, I2C1_SDA −0.38 mm); ACT_EN's hop is a layer hop, which the probe does not test. They remain an open
owner decision (P6-DOCS-01), so I raise no new finding for them.

## 4. F7 copper changes: segment-by-segment

`diff7.py` pass-6 board → final board: tracks 1,777 → 1,747, vias 706 → 708; 11 nets changed.

| Net / stage | New copper | Check |
|---|---|---|
| QSPI_IO3 `qspi6` | F.Cu (22.5, 40.3) → (22.5, 35.4) | clean; 0.205 mm to U3.8 |
| 3V3 `v3v3_6` | F.Cu (31.1, 54.5) → (33.65, 54.5) → (36.5, 51.65) | clean; gaps 0.469 mm (E run) and **0.314 mm** (diagonal, GND via (35.85, 53.275)); the handoff's "0.47 mm min gap" covers only the E run (P7-04 nit) |
| 3V3A `ties6` | B.Cu (35.5, 76.54) → (36.1187, 75.9213) → (36.8013, 75.9213) → (37.4, 76.52) | geometry legal; 0.169 mm to GND via (36.5, 76.54); a threshold artefact (**P7-04**) |
| ACT_FET_S `ties6` | B.Cu (5.17, 96.0) → (5.17, 94.64) → (5.91, 93.9) | clean; 0.377 mm to R120.2 |
| BAT_IN `bat_in_f6` | vias (9.7, 31.75), (9.7, 35.5); BAT_IN_F zone | (9.7, 35.5) is on a B.Cu track body (**P7-03**); gaps 0.58 / 0.53 mm |
| CAM_FAULT_N / SERVO4_MCU `servo_fault6` | In2 SE steps (14.6414, 91.85) → (15.19, 92.3986) and (15.505, 91.3) → (16.005, 91.8) | clean; the steps are `extra_bends` information, forced by CAM_PWR_EN's via and the 3V3 via (16.3, 90.525) |
| GND `ties6` | J3.1 → C28.2 B.Cu SW / S / SE; J3.1 → R85.2 B.Cu S; J3 shell → A1B12 / B1A12 F.Cu S runs; J1.2 → via F.Cu S; R130.2 → R178.2 F.Cu N / NE / E | clean; J3 peg (NPTH) 0.261–0.267 mm (rule 0.25); R130.2 → R178.2 keeps 0.297 mm to PYRO1_CONT (the octilinear diagonal would be legal at 0.17 mm; the 0.30 mm margin to a pyro sense net is a sound choice) |
| LOGIC_SS `logic_ss6` | B.Cu (28.95, 29.35) → (28.95, 29.65) → (27.55, 31.05) | clean; 0.183 mm to U11.12 |
| RAW_ACT `raw_act6` | 9 B.Cu segments deleted | no stub left (my scan: 0 dangling ends; the gate: 0 dead copper) |
| SW_NODE `sw6` | as §3 | clean |

My scan, pass-6 board → final: nothing new in acute, short, staircase, dangling, overlap or crossing; new pad-entry
information only at LOGIC_SS / U11.11 (the deliberate in-pad exit); U-turns 21 → 19; series-via runs 49 → 48.

## 5. Whole-board scans

### 5.1 Independent scan (`scan7.py`, final board)

| Category | Count | Notes |
|---|---|---|
| off-angle / arcs / zero / micro (< 50 µm) | **0 / 0 / 0 / 0** | |
| short (< max(w, 0.2 mm)) | 28 | all wholly inside a via or pad (via-entry pieces) |
| staircase (chains and through nodes) | **0** | |
| acute (0.5–89.5°), exposed | 10, **0 exposed** | all 45° pairs at pads / vias |
| fold-back / crossing without node / dangling end / overlap-only end / off-centre via joint | **0 / 0 / 0 / 0 / 0** | |
| fill-only end | 1 | RAW_ACT (7.6, 81.57), A41 |
| collinear unmerged / collinear width change | **0** / 3 | the 3 pad-entry necks of part F |
| width change at a plain node | 5 | all run straight into the pad they end in, ≤ 1.4 mm |
| same-net parallel overlap | 2 | C21 debris (BAT_IN in D8.1, USB_FAULT_N in R90.2) |
| tiny chain jogs (1–4 segment middle) | 2 | A1, A2 |
| tiny through-node jogs | 13 + 2 | 12 = C17 (11 inside a via; BOOT0 across its via, C16), GND (36.4, 76.54) inside its via (P7-04), BAT_FAULT_N's side branch at a T (not a jog) |
| critical layer change without GND via ≤ 1.5 mm | **9** | = A6–A14 |
| power layer change without GND via | 35 | = `power_via_no_gnd` |
| via ring overlap / dangling via | 0 / 1 | the "dangling" BAT_IN via (9.955, 44.25) is joined to the In2 BAT_IN fill through its ring (fill edge 0.055 mm from its centre): a false positive of my centre-only test |
| **via on a same-net track body** | 2 | GND (6.85, 40.5) (inherited; noted in pass 6's scan, not recorded) and **BAT_IN (9.7, 35.5), new** (P7-03) |
| **overlap-only via joints** (no track end in the via on that layer, track copper overlapping it) | 9 | 6 GND vias inside their own fill (benign); **3V3 (30.17, 71.17) ↔ In2 run and (30.4, 70.25) ↔ B.Cu run** (P7-01); **BAT_IN (9.7, 35.5)** (P7-03) |

### 5.2 Reference scans

- **Pass-2 `scan.py`** (unchanged, vs R6): **918 instances (559 critical)**, equal to F7's figure; chain_detour 50
  (30 critical).
- **Final `route_check`** on this board: 323 instances (chain_detour 8, pour_net_hop 5, tiny_jog 2,
  critical_via_no_gnd 9, detour 22, extra_vias 27; information 250), 0 failing; equal to the handoff.

### 5.3 Sub-chain bump probe (`probe7.py`)

152 minimal windows on all nets. For 44 of them the project's own redraw machinery finds a 1–3 segment redraw at least
0.15 mm shorter that clears every other net's copper. I split these by whether the present window **backtracks** (is
longer than the Manhattan distance of its ends, i.e. a real bump rather than an L or Z shape that a diagonal would
shorten). I then tried 22 variants with DRC, refill, pour pieces, `route_check`, `check_r7` and `check_actuators`:

| Variant | Net (class) | Present → redraw (mm) | Result |
|---|---|---|---|
| `v3am` | **3V3A** (power), B.Cu | 10.77 → 9.55, backtracks | **clean**: DRC 0/0/0, `route_check` identical, critical_reference 0 lost (P7-01) |
| `cam5v` | **CAM_5V** (power), B.Cu | 7.50 → 6.62, backtracks | **clean**, `route_check` identical (P7-01) |
| `a34both` | **3V3** (power), B.Cu, A34 | chain 16.32 → 14.52 | **clean**; only A34's quoted figure changes (P7-01) |
| `vlogic` | **VLOGIC** (power), F.Cu | 6.61 → 6.01, backtracks | **clean**; only A33's quoted figure changes (P7-01) |
| `v3pair` | **3V3** (power), via pair | −1 via, −0.81 mm F.Cu stub | **clean**, `route_check` identical (P7-01) |
| `c5s` | CAM_5V_SENSE, In2 | 12.43 → 10.89, backtracks | **clean**; 3V3_In2 5 → 4 pieces; B7 goes stale (P7-02) |
| `s2o` | SERVO2_OUT, In2 | 8.38 → 6.25, backtracks | **clean**; only B23's figure changes (P7-02) |
| `bss` | BAT_SW_SOURCE, F.Cu | 12.81 → 11.01, backtracks | clean, but gap 0.725 → 0.187 mm; the edge route buys clearance on a harness line: judged not needless |
| `usbdm` | USB_DM, F.Cu | 6.53 → 5.83 | clean, but it only trims the A7/B7 crossover hook by 0.35 mm: judged not needless (C24 stands) |
| `qspi0`, `cmt`, `ledy`, `s4m`, `v3j2` | QSPI_IO0, CAM_MCU_TX, LED_YEL, SERVO4_MCU, 3V3 (A42) | −0.6 … −1.5 | DRC-clean, but monotone L / Z routes (no backtrack), so not detours |
| `pgn`, `buzz` | PYRO1_GATE_N, BUZZ_DRV | −4.2, −4.9 | **rejected by DRC**: copper-to-edge at the tie hole (27.0, 82.6) and at the M3 hole (4, 64). The present routes go round those holes |
| `qspi2`, `lss`, `usbl` | QSPI_IO2, LOGIC_SOURCE_ST, USB_LIMITED | | rejected: 3V3 connectivity cut, 3V3_In2 split or starved GND thermal (A20, C24 and C25 stand) |
| `dio1` | RADIO_DIO1 band lane | −1.70 | DRC-clean, but GND_F 43 → 44 pieces and it breaks the lane pattern: not taken |
| `ledr`, CAM_FAULT_N, ARM1_SENSE, I2C1_SDA | | | already recorded removable (C24 / C25) |
| RADIO_TXEN | | | crosses `U31_KEEPOUT` (C24 stands) |

`alt_audit`'s board-edge test uses the outline's bounding box plus 0.3 mm. The board's copper-to-edge rule is 0.5 mm,
and the internal Edge.Cuts holes are not tested at all. So the audit can call a redraw removable when DRC rejects it
(the `pgn` and `buzz` cases). That fails safe (a false "removable" fails the gate), so it is a note, not a finding.

### 5.4 Split crossings and references

critical_reference (`--extended`) from the refilled base to each clean variant (`v3am`, `cam5v`, `a34both`, `vlogic`,
`v3pair`, `c5s`, `s2o`, `bss`): **0 lost, 0 new** for all eight (`v3am` gains 429 referenced samples). F7's own result (pass-6 board → final: 0 lost, 0 new) I did not re-run on the whole
board, but the copper diff (§4) touches no critical signal net except QSPI_IO3, whose new segment follows the old line
exactly at the ends. The 7 recorded U1-end split crossings (C5) are unchanged.

## 6. Remaining exceptions: can a DRC-clean edit remove them?

| Items | Result |
|---|---|
| A1, A2 (band fan-in tiny jogs) | not re-searched beyond pass 6 (copper unchanged); my probe finds no clean redraw |
| A6–A14 (no GND via) | gate's `nognd_audit` passes; my scan agrees the 9 have no GND via within 1.5 mm; F7 only added copper near the band, which cannot open a spot |
| A15–A33 (detour / extra vias) | figures match the gate. **A33 (VLOGIC)**: a 0.60 mm local peak is removable (P7-01). **A42**'s F.Cu run can be 1.1 mm shorter as a diagonal (monotone, not a detour) |
| **A34** (3V3 chain detour) | **partly removable:** 16.32 → 14.52 mm by two DRC-clean 3-segment redraws with more clearance than now (0.173 mm against 0.157 mm). Its "why" ("a shorter feed needs U12's 3V3 re-tapped with C19 / C20 moved (respin)") is untrue, and C19 / C20 are the VCAP capacitors at (18.9, 45.9) / (16.7, 60.8), 20 mm away (P7-01) |
| A35–A41 (GND / RAW_ACT chain detours) | probe: no clean shorter redraw |
| A42–A46 (series hops) | blockers as stated (not re-probed beyond the probe's windows) |
| B7 (CAM_5V_SENSE), B23 (SERVO2_OUT) | **reasons untrue** (P7-02) |
| B5 (BAT_SW_SOURCE), B12 (CAM_MCU_TX), B17 (LED_YEL), B24 (SERVO4_MCU) | DRC-clean shortenings exist, but they trade clearance or are not detours (§5.3): no finding |
| C17 (12 in-via steps), C21 (debris) | as recorded. Re-centring is an optional tidy-up |
| C23 (poured-net hops the gate excludes) | the 3V3A entry's fill statement is false (P7-04) |

## 7. Findings

### P7-ROUTING-01 (Major): needless local bumps and an extra via on critical power nets, each removed by a DRC-clean edit, are in no deviation-list entry; the gate's chain test cannot see them

**Requirement.**
- REQUIREMENTS M2: no needless detours, extra vias or layer hops, and no overlap-only joints, over the whole board,
  inherited copper included.
- Every review-only residual must be listed with a measured reason, and the owner accepts that list as complete.
- AGENTS §3: every exception carries a measured reason.

**Finding.** The deviation list holds all 50 pass-2 chain detours and says each is gated (A34–A41) or judged (C24 /
C25). The gate's `chain_detour` test, though, measures a whole run between two junctions. `alt_audit` accepts a redraw
only if it *ends* the detour (cap `min(L, max(1.25·o, o + 0.5))`, `route_check.py` l.2344–2346). Nets without a pour get
only the net-level test. So neither the gate nor the records' sweep can see a bump inside a longer run, or a redraw
that removes part of a detour. On the final board that leaves these critical-net items, all R6-inherited except the
VLOGIC peak:

1. **3V3A, B.Cu**, from via (35.9632, 69.9393) to (36.4, 60.86). The run bulges east:
   (35.9632, 69.9393) → (37.8632, 68.0393) → (37.8632, 65.5392) → (36.04, 63.716) → (36.04, 61.22) → (36.4, 60.86),
   10.77 mm.
   - **Redraw** (`v3am`): (35.9632, 69.9393) → (35.6096, 69.5857) → (35.6096, 61.6504) → (36.4, 60.86), 9.55 mm (−1.22 mm).
   - **Gaps:** min 0.212 mm (PYRO1_CONT via (35.78, 60.65)) and 0.225 mm. The present copper's are 0.208 mm (NRST via) and
     0.212 mm.
2. **CAM_5V, B.Cu**, from U13 (40.2, 32.45) to (34.23, 31.6). The run dips south and comes back:
   … (37.0, 32.45) → (36.0, 33.45) → (35.48, 33.45) → (34.23, 32.2) …, 7.50 mm.
   - **Redraw** (`cam5v`): (40.2, 32.45) → (34.575, 32.45) → (34.23, 32.105) → (34.23, 31.6), 6.62 mm (−0.88 mm).
   - **Gaps:** min 0.271 mm (C60.1). The present copper's is 0.320 mm.
3. **3V3, B.Cu, A34.** Two 3-segment redraws cut the chain from 16.32 to 14.52 mm (−1.81 mm, `a34both`):
   - (36.94, 53.0) → (37.19, 53.0) → (38.45, 54.26) → (38.45, 56.75);
   - (42.95, 57.15) → (42.95, 55.75) → (41.58, 54.38) → (41.58, 53.9).

   Min gap 0.173 mm (CAM_RX_WIRE via) and 0.175 mm (RAW_PROTECTED via), against the present copper's 0.157 mm to that
   RAW_PROTECTED via. A34's "why" is therefore untrue, and it names C19 / C20, which are the VCAP capacitors 20 mm away.
4. **VLOGIC, F.Cu (A33's tree)**, C99.1 (28.505, 29.85) → (31.355, 27.0) → (32.27, 27.915) → (32.27, 29.2): a peak,
   6.61 mm.
   - **Redraw** (`vlogic`): (28.505, 29.85) → (30.555, 27.8) → (32.27, 27.8) → (32.27, 29.2), 6.01 mm (−0.60 mm).
   - **Gaps:** min 0.172 mm, the same as now.
   - This one is R7 copper, not in R6.
5. **3V3 via pair.** The F.Cu diagonal (27.85, 68.85) → (30.17, 71.17) ends in via A (30.17, 71.17), which carries the
   B.Cu run (30.17, 65.1–73.7).
   - A 0.81 mm F.Cu T-stub leaves that diagonal at (29.825, 70.825) for via B (30.4, 70.25), 0.95 mm away. Via B starts
     the In2 run (30.4, 70.25) → (30.4, 78.25).
   - The In2 run overlaps via A's ring by 0.195 mm, and the B.Cu run overlaps via B's ring by 0.195 mm, with no track end
     in either via on those layers. These are overlap-only joints, and the two runs are stacked on B.Cu / In2 for
     about 3.4 mm.
   - **Redraw** (`v3pair`): delete via B and the stub, and start the In2 run at via A: (30.17, 71.17) → (30.4, 71.4) →
     (30.4, 78.25). This saves one via and the stub; In1 GND gains 0.75 mm².

**Electrical effect:** none expected; the changes are lengths of 0.6–1.8 mm and one via (Inference). The fault is that
these M2 items are absent from the list the owner is asked to accept as complete, and that A34's reason is untrue.

**Why Major (calibration).** This is the P6-DOCS-01 pattern (upheld Major 2:1): a category of M2 residual that the
list's sweep cannot see. Here it holds several concrete critical-net instances, including a needless extra via and
two overlap-only via joints on 3V3. The counter-argument is P6-ROUTING_QUALITY-01: a single inert bump was re-graded
Minor 2:1, because M2 acceptance is already open. A skeptic may apply that argument here.

**Evidence.**
- Board `4673c0a0…`. Variants `<p7>/v7_v3am`, `v7_cam5v`, `v7_a34both`, `v7_vlogic`, `v7_v3pair`; edit lists
  `<p7>/e_*.json`; logs `<p7>/logs/*.log`.
- Each variant: `kicad-cli pcb drc --severity-all --schematic-parity` 0 / 0 / 0. `check_r7` OK; `check_actuators` OK.
- `route_check` instance list identical to the refilled base (`v3am`, `cam5v`, `v3pair`), or only A34's / A33's quoted
  figure out of date (`a34both`, `vlogic`). No pour piece count changes.
- critical_reference `--extended` 0 lost, 0 new.
- Present / redraw gaps from `gaps.py`. Renders `<p7>/img/{v3a,v3a_v,cam5v,cam5v_v,vlogic,vlogic_v,v3v3pair}.png`.
- R6 origin checked on `3b215ba` (3V3A x 37.8632 run, CAM_5V dip, 3V3 via pair at y − 18). Records searched: no entry
  for any of 1, 2, 4 and 5; A34 as quoted.

**Fix.** Apply the five redraws in `r7_polish`. For 3V3A, merge the last segment as in `v3am`. Update the A33 / A34
figures, correct A34's "why" (or delete the entry if the remaining run is judged acceptable), rebuild with
`r7_build.sh` and rerun the gate.

Then close the method gap: either add a sub-chain test to `route_check` (a minimal window with more than 0.3–0.5 mm
of excess that backtracks, i.e. is longer than the Manhattan distance of its ends; every net), or let `alt_audit`
accept any strictly shorter clean redraw of a chain detour.

If any item is kept, list it in part C with a measured reason.

### P7-ROUTING-02 (Minor): B7 and B23 reasons are untrue; CAM_5V_SENSE's In2 detour fences a 17.64 mm² 3V3_In2 piece off the main plane

**Requirement.** M2: every non-critical leftover carries a true measured reason ("why it cannot reasonably be
removed").

**Finding and evidence.**

**CAM_5V_SENSE (B7)**
- **Present In2 route:** (32.05, 37.55) → (29.35, 34.85) → (29.35, 30.35) → (29.85, 29.85) → (33.25, 29.85), 12.43 mm.
  It runs 2.7 mm west, then 3.4 mm back east to its via.
- **Redraw** (`c5s`): (32.05, 37.55) → (30.3353, 35.8353) → (34.7853, 31.3853) → (33.25, 29.85), 10.89 mm.
  - DRC 0 / 0 / 0; check_r7 OK; actuators OK; critical_reference 0 lost.
  - `route_check`: B7's net-level `detour` instance disappears, and nothing is added.
  - 3V3_In2 goes from **5 to 4 pieces**: the 17.64 mm² piece (bbox (29.68, 30.18)–(34.50, 37.01), the one holding C23's
    3V3 In2 run) joins the 455.3 mm² main plane (474.5 mm² after).
  - Gaps: min 0.182 mm, against 0.191 mm now.
- **Reasons this contradicts:**
  - B7: "a shorter route was not found under the stricter rule";
  - C25's CAM_5V_SENSE In2 (33.25, 29.85) row: "no 1–3 segment redraw" (true only under the gate's "end the detour"
    cap).

**SERVO2_OUT (B23)**
- **Present In2 route:** (18.0132, 93.1) → (18.0132, 96.7) → (22.0987, 96.7) → (22.5903, 96.2084), then N.
- **Redraw** (`s2o`): (18.0132, 93.1) → (21.5841, 96.6709) → (22.1278, 96.6709) → (22.5903, 96.2084).
  - Net 37.07 → 34.94 mm, still 1 via. DRC 0 / 0 / 0; pours unchanged.
  - `route_check`: only B23's figure changes, with no tiny jog or short segment.
  - Gaps: 0.171 mm, against 0.172 mm now.
- **Reason this contradicts:** B23's "shorter only with tiny jogs or two more vias, under the stricter rule".

**Why Minor.** Non-critical nets, no electrical effect. The 3V3_In2 merger is a small plane-integrity gain (Inference).

**Fix.** Apply the two redraws (and drop B7 if it goes stale), or restate B7 / B23 as choices with these measured
figures.

### P7-ROUTING-03 (Minor): F7's new BAT_IN via (9.7, 35.5) sits on a B.Cu track body, joined only by overlap; the gate has no test for it

**Requirement.** M2: no overlap-only joints, no untidy pad / via entries. Fix-pass changes must not add new residuals
without recording them.

**Finding.**
- The via sits 0.0354 mm off the centre line of the B.Cu BAT_IN track (11.9, 33.35) → (9.2, 36.05), w 0.2 mm, at
  neither of its ends. Its 0.6 mm ring overlaps the track body by 0.365 mm. The track ends 0.74 mm away, in via
  (9.2, 36.05).
- It was created by `bat_in_f6`; the pass-6 board has no such via.
- Records mention it only as "in the F.Cu and In2 BAT_IN fills". The other centre-in-track via, GND (6.85, 40.5), was
  noted in pass 6's scan table but is not recorded either.
- `route_check` tests track ends (`overlap_only_joint`, `via_offcentre_joint`) but not a via joined to a same-net
  track only by overlap. My `viaovl.py` finds 9 such vias: 6 GND vias inside their own fill (benign), the 3V3 pair of
  P7-01, and this BAT_IN via.

**Evidence.**
- `ctx7.py` at (9.7, 35.5).
- `viatrk.py` / `viaovl.py` on the final and pass-6 boards.
- Variant `v7_batvia`: via moved to (9.725, 35.525) on the track's line and the track split there. DRC 0 / 0 / 0;
  `route_check` adds only a `short_layer_hop` information instance (0.74 mm to via (9.2, 36.05)).

**Why Minor.** It has no electrical effect: the joint is solid copper (Inference). It is a cosmetic, fix-pass-created
residual.

**Fix.** Do one of these:
- centre the via on the track and split the track there (`v7_batvia`);
- move the via clear of the track inside BAT_IN_F (F7's `viaspot.py` constraints);
- record it in C21 with the GND (6.85, 40.5) case.

Optionally add a "via on a same-net track body / overlap-only via joint" category to `route_check`, counted on every
net and excluding vias inside their own fill.

### P7-ROUTING-04 (Minor): the 3V3A-hop "fix" is a threshold artefact; C23 and two other records statements are inaccurate

**3V3A hop (`ties6`)**
- **New copper:** B.Cu (35.5, 76.54) → (36.1187, 75.9213) → (36.8013, 75.9213) → (37.4, 76.52).
- **Measure:** L = 2.4043 mm, octile = 1.9083 mm, so L / o = 1.26 (still above `CHAIN_DETOUR_MAX` 1.25).
  L − o = 0.496 mm, under `CHAIN_DETOUR_SLACK` 0.5 by **4 µm**.
- **The shape is unchanged:** the run still turns back round the GND via (36.5, 76.54), now 0.169 mm from it (it was
  0.34 mm), to save 0.10 mm. The handoff and the P6-DOCS-01 disposition count it among the 10 chain detours fixed.
- **The fill is wrong in the records:** both vias, (35.5, 76.54) and (37.4, 76.52), lie in the same 28.17 mm²
  3V3A_In2 island (`island.py`). C23's "the first via in the 3V3A_In2 fill" is false, and the hop parallels a
  connection the fill already makes.
- **Deleting the hop** (`v7_3v3a`): DRC 0 / 0 / 0; `route_check` drops a `short_layer_hop` and a
  `width_change_junction` and adds nothing. U4.5 would then reach C30 / C31 through two vias and In2 (Inference: about
  1 nH more on VDDIO decoupling), so keeping the hop is a defensible choice. But C23 should say so, and the 0.34 mm
  geometry was the better one.

**Other records nits**
- **C17 / part F, GND (36.4, 76.54):** the records say the step "is no longer a step" because "fix pass 6's 3V3A
  redraw left a NE diagonal". The GND copper is byte-identical on the pass-6 and final boards (`diff7.py` lists no
  change at that via), so the reclassification has no copper cause.
- **3V3 `v3v3_6`:** the handoff's "0.47 mm min gap" is the E run's. The new diagonal (33.65, 54.5) → (36.5, 51.65)
  passes the GND via (35.85, 53.275) at 0.314 mm.

**Why Minor.** These are records accuracy and cosmetic: all copper is DRC-legal, and a 3V3A–GND short would fail
bring-up, not create a hazard (Inference).

**Fix.**
- Restore the 0.34 mm hop and list it as a measured allowlist or part-C item (ratio 1.32), or delete the hop with a
  stated decoupling judgement.
- Correct C23's fill statement and C17's GND note.
- Quote the diagonal's 0.314 mm in M3_R7.

## 8. Notes (no finding)

- **`alt_audit` edge model.** It uses the outline's bounding box plus 0.3 mm, while the board's copper-to-edge rule is
  0.5 mm, and it ignores internal Edge.Cuts holes (tie holes, M3 holes drawn on Edge.Cuts). It can report a redraw as
  removable when DRC rejects it, as `pgn` and `buzz` show. That fails safe.
- **A42.** The 3V3 F.Cu run (36.0, 82.43) → (41.0, 77.92) can be a diagonal 1.1 mm shorter, DRC-clean (`v3j2`). It is
  monotone, so it is not a detour.
- **ACT_EN's hop (C26).** It is the one recorded removable item with an electrical benefit (BAT_IN J1 → Q120 −15 %).
  It stays an owner decision.
- **PYRO1_GATE_N's In2 L round the tie hole (27.0, 82.6)** and **BUZZ_DRV's edge run round the M3 hole (4, 64)** are
  forced by board-edge clearance (`pgn` and `buzz` fail DRC). They are fine as they are.

## Appendix: reproduce

```
cd <p7>   # r7.kicad_pcb = final (4673c0a0…), base6.kicad_pcb = pass-6 (1ffc2585…), r6.kicad_pcb (184a87e8…), proj_base/ = project copy
PY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
R=.
$PY -I scan7.py r7.kicad_pcb out/s7_r7.json; $PY -I scan7.py base6.kicad_pcb out/s7_base.json
$PY -I scan2.py r7.kicad_pcb r6.kicad_pcb out/scan2_final.json          # 918 (559)
$PY -I diff7.py base6.kicad_pcb r7.kicad_pcb; $PY -I gaps.py base6.kicad_pcb r7.kicad_pcb
$PY -I probe7.py r7.kicad_pcb out/probe7.json                          # 152 windows, 44 clearance-legal shorter
$PY -I viatrk.py r7.kicad_pcb; $PY -I viaovl.py r7.kicad_pcb; $PY -I island.py r7.kicad_pcb 3V3A In2.Cu 35.5,76.54 37.4,76.52
./vrun7.sh base e_base.json; ./vrun7.sh v3am e_v3am.json; ./vrun7.sh cam5v e_cam5v.json; ./vrun7.sh a34both e_a34both.json
./vrun7.sh vlogic e_vlogic.json; ./vrun7.sh v3pair e_v3pair.json; ./vrun7.sh c5s e_c5s.json; ./vrun7.sh s2o e_s2o.json
./vrun7.sh batvia e_batvia.json; ./vrun7.sh 3v3a e_3v3a.json
$PY -I $R/tools/critical_reference.py v7_base/m3.kicad_pcb v7_v3am/m3.kicad_pcb --dy 0 --extended
$PY -I $R/tools/route_check.py base6.kicad_pcb --report out/rc_base6.json   # new detections fire on the pass-6 board
```
