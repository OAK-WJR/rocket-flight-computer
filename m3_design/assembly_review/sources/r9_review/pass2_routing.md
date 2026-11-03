# R9 review pass 2: routing simplicity and geometry (whole board)

Reviewer: independent, read-only. Dimension: the geometry and simplicity of every track and via on all four layers:
AGENTS §3 rule instances, staircases, jogs and multi-segment knees, local bumps, chain detours and extra vias (poured
nets included), bus tidiness, pad entries, width discipline, layer discipline, the 57 signal vias against owner
decision 4's 70 / 55, and, for every remaining exception, whether a DRC-clean edit removes it.

- **Board reviewed:** `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
  `4f841a0e44ebb1829ad7996dfe6320ed527fce1fdb1e5ff11658e0705b44ac14` (review pass 1's fix pass). The SHA was the same
  before and after this review. `git status --porcelain` showed the same 113 lines before and after; the untracked
  `sources/r9_review/` folder is one of them, so this new file adds no line.
- **Contents** (my scan): 862 tracks, 0 arcs, 583 vias.
  - F.Cu 432 tracks, 1094.96 mm; B.Cu 430 tracks, 758.13 mm; **In1 and In2: no track.**
  - Vias: 345 × 0.5 / 0.3 mm and 238 × 0.6 / 0.3 mm, all through. GND 430 (52 with track arms, 378 pour-only);
    non-GND 153: 57 signal layer changes, 25 power layer changes, 24 track-to-pour, 47 pour-only.
  - Five track widths (0.2 / 0.25 / 0.3 / 0.4 / 1.0 mm); 260 bends at plain nodes on signal nets (S10b, reproduced).
- **Gate:** `NUMPY_PY=<cfd venv> tools/check.sh` on the repository board (GUI session logged in, no shim): exit 0 (§9).
- **Repository changes:** none except this file. Scratch: `<scratch>/r9review/routing2/` (deleted at the end).

## 1. Verdict

**No Critical, no Major, 4 Minor** (R9P2-ROUTING-01 … 04; 01 and 02 worth fixing, both cheap).

- **Pass 1's five routing findings are closed** (§3): TXEN is 0.2 mm and the board has five widths; TP120 holds no via;
  C6, C15 carry the records pass 1 asked for. I re-tried a straight CC1 variant and got pass 1's result (the step still
  stands for a tiny jog that has no DRC-clean alternative).
- **AGENTS §3 rule instances: none**, measured independently (§4.1). All 18 critical layer changes have a GND via
  within 1.5 mm (worst 1.391 mm, PYRO1_GATE). No off-angle segment, acute or fold-back branch pair, staircase, stub,
  dangling via, crossing without a node or same-net overlap.
- **The fix pass's copper is clean but for one leftover** (§5). QSPI_IO2, TXEN, the U31 module vias, the TP120 vias
  and the ground stage's vias add no rule or hygiene instance; the route_check report is identical to step 10's. The one
  leftover is in USB_LIMITED's redrawn end. The trunk still steps down x 36.225, the column of C98.1's old spot, then
  jogs onto R87.1's column x 37.0. One diagonal removes two bends at the same length, DRC-clean (**01**).
- **The board reads as deliberate, simple and logical.** I agree with pass 1's area-by-area reading. The fix pass did
  not change the picture.
- **Remaining exceptions with a DRC-clean removing edit.** Each trial ran on a scratch copy with native refill:
  kicad-cli DRC 0 at every severity and route_check r9 OK. Where the edit could touch them, check_r9's rule sets and the
  ground gate were re-run, unchanged:
  - USB_LIMITED's vestigial step (01).
  - C5's close pairs (02). C5 gives no reason why they cannot be removed. 13 pour-joined GND vias, each moved 0.05 mm
    (table edits only), remove 8 of the sweep's 32 copper rows and 6 of its 28 pad rows: Y1b 14 → 12, Y2c 11 → 7.
    Most of the rest are forced by the 0.5 mm pin pitch, and I give the classes.
  - Cosmetic only, not worth a fix pass on their own: an even RAW_ACT via row after D-F1-04 (03, DC-neutral), and a
    one-diagonal ACT_GATE F.Cu hop (04, one bend and 0.47 mm less).
- **S4 = 57** (done ≤ 70 met, stretch 55 missed by 2). Every one of the 14 vias beyond the pads' need has a forcing
  cause, and, like pass 1, I found no removable via (§4.3).

## 2. Method

Every script ran on scratch copies. Geometry was dumped with KiCad 10.0.6's Python (read-only) and analysed in plain
Python. Variants came from a pcbnew edit script with native zone refill. A no-op pass of that script reproduces the board
byte for byte (SHA `4f841a0e…`), so a variant's diff is its edit only.

| Script | What it does |
|---|---|
| `dump.py` | Board → JSON: tracks, vias (per-layer flashing), pads (copper polygon per layer), zone fills, rule areas, courtyards, Edge.Cuts (the five M3 and two tie holes are Edge.Cuts circles) |
| `scan.py` | **Independent scan.** Inventory, widths, angles; node graph per (net, layer) with ends merged at 1 µm and typed pad / via / tee / plain / end. Chains through plain nodes: turns, U-turns, chain detours (> 1.25 × octile and > 0.5 mm), knees (a heading regained after 1–3 middle segments, with middle length and lateral offset), alternating runs, short segments, collinear joints. Branch-pair angles at every node, pads and vias included. Same-net overlaps and crossings. Vias: arms per layer, off-centre arms, tracks passing over a via, kind, need per net, nearest GND via of critical changes, folds. Pad entries (depth, axial or not, lateral offset, width vs pad). Width changes. Bus pitch. Net length vs octile MST. Knees through two-arm vias |
| `adj.py`, `ycount.py`, `yrows.py` | Different-net copper pairs on one layer closer than 0.2 mm (tracks as capsules, vias only where flashed, pads as polygons); the sweep's rows (one per layer and net pair; one per pad and foreign net) and their diff between boards |
| `nudge.py` | For every via within 0.2 mm of foreign copper: the smallest move (0.05 / 0.1 mm, eight directions) that takes all its gaps to ≥ 0.2 mm, and whether the via has track arms |
| `cands.py` | Redraw candidates: every window of 2–4 segments inside a chain (T nodes split) replaced by the 1–2-segment octilinear paths between its ends. Kept if ≥ 0.15 mm shorter, or equal with fewer bends, and ≥ 0.2 mm from other nets' copper, non-GND fills, keep-outs, holes and the edge. Tagged where it would make an axial pad entry diagonal or add a segment under 0.2 mm |
| `edit.py`, `trial.sh` | Apply an edit set (remove / add segments, move vias), refill, save; then kicad-cli DRC `--severity-all` and route_check r9 on the variant; check_r9 `--only` rule sets where the edit could touch them |
| `render.py`, `near.py` | Matplotlib renders per layer (24 tiles of 24 × 20 mm, both outer layers, labelled; zooms); copper near a point |
| reused | `tools/route_check.py --profile r9`, `tools/check_r9.py --only …`, `tools/dc_solve.py` (RAW_ACT, 0.1 mm), `m3_design/r9_ground_check.py`, `step10_evidence/m2_sweep.txt`, `tools/check.sh` |

## 3. Previous findings in this dimension (pass 1 on `fc3d5b34…`)

| Pass-1 finding | Disposition in the fix pass | Checked on `4f841a0e…` | Status |
|---|---|---|---|
| R9P1-ROUTING-01 RADIO_TXEN the only 0.15 mm net | copper (D-F1-02): `r9_rf.py:52` `W_TXEN = W_SIG`; grid via (24.7, 10.45) → (24.65, 10.45); `r9_route.py:47` five widths | All 7 TXEN segments are 0.2 mm (25.17 mm). The board's widths are 0.2 / 0.25 / 0.3 / 0.4 / 1.0 mm. No TXEN track is within 0.2 mm of foreign copper. TXEN's two vias stay 0.171 mm from GND vias (28.94, 7.2) and (32.48, 20.55), as on step 9's board; see 02 | **closed** |
| R9P1-ROUTING-02 TP120's two in-pad RAW_ACT vias | copper (D-F1-04): `r9_power.py:291`, (29.6, 78.2) dropped, (31.0, 78.2) → (31.5, 78.2) | No via in any TP pad. (31.5, 78.2)'s ring is 0.25 mm from TP120.1's copper (hole 0.40 mm). RAW_ACT has 31 vias. K-copper OK. The row's new pitch is 03 | **closed** |
| R9P1-ROUTING-03 CC1's via step hides a 0.22 mm jog | records: C6, D-S10-12 | C6 says so. Re-trial `cc1a` (B.Cu drawn straight from the via centre at y 32.75): DRC 0, but route_check FAILs `tiny_jog CC1 F.Cu (7.55, 33.05)` (middle 0.424 mm, offset 0.30 mm; a middle under 0.5 mm suffices, `route_check.py:48`) | **closed** |
| R9P1-ROUTING-04 pad-edge and corner entries missing from C15 | records: C15 | C15 lists them. My scan: 19 track ends within 0.08 mm of a pad edge, at the same pads | **closed** |
| R9P1-ROUTING-05 C15's candidate redraws | records: C15 | C15 says pass 1 reviewed them and keeps them. GNSS_ANT_GATE's optional redraw comes up again in my search (§6) | **closed** |

The fix pass's copper changes in this dimension (my diff of `fc3d5b34…` against `4f841a0e…`):

- **Tracks:** 16 removed, 17 added.
  - QSPI_IO2: three segments, east run y 50.9 → 50.6.
  - RADIO_TXEN: seven segments, 0.15 → 0.2 mm.
  - USB_LIMITED: six segments → seven, C98 moved.
- **Vias:** 8 removed, 12 added.
  - The TXEN grid via moved 0.05 mm.
  - R7's three U31 module-ground vias, at (34.35, 15.27), (31.88, 10.40) and (28.07, 17.60).
  - Three copper-stage GND vias, at (35.6, 64.8), (32.9, 99.85) and (41.4, 41.1).
  - (38.75, 79.55) removed.
  - Four GND vias re-placed round C98.
  - The two RAW_ACT changes.
- **Footprints:** C98 (37.0, 62.8, rot 0) → (39.275, 64.2, rot 180), B.Cu.
- **Zones:** R9_RAW_ACT_F's outline.

## 4. Independent scan, whole board

### 4.1 AGENTS §3 rule instances and hygiene

| Check | Result |
|---|---|
| Off-angle (> 0.01° off a multiple of 45°), zero-length | 0 / 0 |
| Inner-layer tracks | 0 |
| Acute (0.5–89.5°) or fold-back branch pairs at any node, pads and vias included | 0 / 0 |
| Turns sharper than 90° inside a chain | 0 (turn histogram: 270 × 45°, 61 × 90°, 2 × 0° at the two pad-entry width steps) |
| Staircases | 0. Eight alternating runs of ≥ 4 segments (route_check's extra_bends), each with at most one segment under 1 mm |
| Same-net crossings without a node; parallel same-net overlap or slit under 0.1 mm | 0 / 0 |
| Dangling vias | 0. Every via joins copper on ≥ 2 layers (tracks, pads or own-net fill): 107 on two, 128 on three, 348 on four |
| Dead ends | 0. Three runs end inside their own pour: RAW_ACT (27.6, 86.04) 0.54 mm, RAW_PROTECTED (40.2, 80.9) 0.35 mm, BAT_IN (20.0, 96.3) 0.30 mm. Five more ends lie on another same-net track's centre line: T joints whose through-track is not split in the file. They are ACT_GATE (26.6, 85.1) and (29.35, 85.1), GND (41.9, 73.0), RADIO_NSS (23.45, 29.23) and RAW_PROTECTED (42.45, 70.4), each at 0.000 mm. route_check treats them as T nodes, and the copper is the same as a split track |
| Critical layer changes with a GND via ≤ 1.5 mm | 18 / 18: worst PYRO1_GATE 1.391, SPI1_MOSI 1.298, QSPI_IO2 1.270, HSE_OUT 1.250 mm |
| Off-centre via joints | 1: CC1 (7.85, 32.75), the 0.113 mm step (C6) |
| Neck-downs away from pads | 0. The two plain-node width steps are pad-entry necks: SW_NODE (40.0, 73.9) 1.0 → 0.4 into U2.5, CAM_INPUT_LIMITED (35.4, 35.65) 1.0 → 0.25 into U7.5 |
| Short segments (< max(w, 0.2)) | 5: four pad-to-pad straps (3V3 in L1.2, BAT_DAMP, 3V3_RADIO, C24.2's GND) and CC1's via step |

Information, outside the gated classes: RAW_ACT_SENSE_MCU's one layer change, (26.95, 46.5), is 2.574 mm from the
nearest GND via (R8's equivalent via was 2.804 mm). route_check classes the net `other`: its pyro regex `^(PYRO|ARM)` covers
PYRO1_CONT_MCU and ARM1_SENSE_MCU, which have no via on R9. It is a DC sense line behind R172's 4.7 kΩ.

### 4.2 Knees, U-turns, bumps

- **Knees:** 83. That is pass 1's 82 plus USB_LIMITED's new one (01). None meets route_check's tiny-jog test; the
  smallest middle is 0.509 mm (IMU_INT1 at U4's GND via). The small knees are pass 1's, with the same causes.
- **Knees through two-arm vias** (not in pass 1's scan; route_check tests this pattern for tiny jogs only): 9 with a
  middle under 1 mm, all ≥ 0.5 mm, so none is a tiny jog.
  - 3V3 (24.25, 38.5): middle 0.537 mm. CC2 (7.95, 36.05): 0.537 mm. Both 0.38 mm offset.
  - BAT_FAULT_N (27.95, 49.9), BOOT0 (8.8, 47.1) and CAM_UART_OE (26.75, 48.0): 0.566 mm.
  - CAM_IO_3V3 (34.6, 57.4) and CAM_MCU_RX (26.75, 45.0): 0.500 mm, exactly at route_check's limit.
  - HSE_IN (17.0, 50.6): 0.707 mm. USB_FAULT_N (11.75, 40.55): 0.778 mm.

  Each is a pin escape to a via offset by 0.38–0.55 mm. CC1 is the one structure where a short segment inside the via
  hides a jog below the limit (C6).
- **U-turns:** 7, the same as pass 1 and each forced: RADIO_NRST, RADIO_TXEN, SWDIO, V3V3_SENSE (225°), BAT_FAULT_N,
  USB_DM and PULLPIN_EXT.
  - I looked again at V3V3_SENSE's hook round the 3V3 via (15.2, 53.6). The via's strap to C14.1 at y 53.6 crosses
    every straight approach to R62.2 (15.42, 54.5).
  - I measured the obvious re-placements on the dump; I did not trial them in KiCad. A via north of C14.1, at
    (15.98, 52.95), comes 0.10 mm from U1.9's pad end. A via west of the lane makes its strap cross the lane.
- **Bumps:** route_check's audit (14 windows on critical nets) and the sweep (21 windows) find only VLOGIC_SENSE (C15).

### 4.3 Detours and vias

- **Chain detours:** 18, all on nets without a pour, equal to `m2_sweep.txt`. USB_LIMITED's run now starts at the T
  (37.0, 63.2): L 21.199 mm, excess +4.613 mm, as before. On poured nets: 0 chain detours, 0 hops in series.
- **57 signal layer-change vias**, counted per net. They equal D-S7-19's family budgets: 43 needed by pads on both
  layers, 14 beyond need. The 14 are:
  - TXEN 2 (U31's keep-out on every layer);
  - CAM_MCU_RX 2 (RX / TX order is crossed between U1.37 / 38 and U12.4 / 5, a topological crossing);
  - CAM_UART_OE 2, BAT_FAULT_N 1, LOGIC_SOURCE_ST 1 (the pin-28..31 box behind the ARM1_SENSE F.Cu lane, a pyro lane
    kept via-free);
  - NRST 2 (J2.3 is boxed by J2.1 / J2.5 and SWCLK's entry: 0.483 mm between TC2030 pads, under the 0.5 mm a 0.2 mm
    lane needs);
  - ACT_GATE 2 (the 7.7 A pours own B.Cu between the FETs);
  - BAT_ENABLE 1, VBUS_SENSE 1 (U10 sits between R9.2 and R110 / TP92 on B.Cu).

  Reaching 55 needs a placement change, such as C24 beside NRST's dive via, which is pass 1's example. Like pass 1, I
  found no routing edit that removes a via.
- **Via folds:** 34 at 33 vias, the same list as the sweep (C7).

### 4.4 Widths, layers, pad entries, buses

- **Widths:** five, each with one role. 0.2 mm signals (617 segments); 0.25 mm gates, switch lines, the limiter's DC
  copper and branch rails (72); 0.3 / 0.4 mm rails (84 / 67); 1.0 mm bars and buck loops (22). The five tracks wider
  than their pad are pass 1's maker or power layouts.
- **Layers:** no inner-layer track. Under U31 only GND (the three new vias are GND).
- **Pad entries:** 670 track ends in pads. Non-axial entries: 68. R87.1's diagonal entry is gone, and C98.1's
  diagonal exit toward U11.7 is new; it leaves from the pad centre. The 19 ends within 0.08 mm of a pad edge are C15's
  list.
- **Bus pitch** (parallel different-net pairs, overlap > 1 mm, pitch ≤ 1.2 mm): 0.5 mm (39) and 1.0 mm (26) dominate.
  The 0.495 mm pairs are diagonal lanes at 0.7 mm spacing. The irregular pitches are pass 1's: the GNSS river, the radio
  bus and the east corridor.

### 4.5 Adjacency (C5)

- My segment-level count: 65 different-net track / via pairs under 0.2 mm (27 at ≤ 0.151 mm) and 30 pad-to-copper
  pairs (11 at ≤ 0.151 mm).
- Reduced the sweep's way (one row per layer and net pair; one per pad and foreign net) they equal `m2_sweep.txt`:
  32 / 14 copper rows and 28 / 11 pad rows (the scorecard's Y1 30 merges the F.Cu and B.Cu rows of two via pairs).
- The east corridor accounts for most segment pairs. BAT_FAULT_N, LOGIC_SOURCE_ST and USB_LIMITED run 0.15 mm apart
  for about 15 mm, beside OE's via and through the slot between C92.2 and the RAW_ACT pour (D-S7-16: three lanes
  at 0.15 mm in 1.48 mm). That is one row per net pair.
- Classes of the 14 Y1b rows:

| Class | Rows | Removable? |
|---|---|---|
| A 0.5 mm via on a pin line between two lanes at 1.0 mm pitch: 1.0 − 0.5 − 0.2 = 2 × 0.15 exactly | 8. U9.8's GND via (40.1, 88.4) against BAT_DVDT and BAT_ILIM. RAW_ACT_SENSE_MCU (26.95, 46.5) against ARM1_SENSE_MCU and CAM_5V_SENSE. LOGIC_SOURCE_ST (26.75, 49.0), CAM_MCU_RX (26.75, 45.0), CAM_IO_3V3 (35.45, 51.95), 3V3 (14.5, 50.65) | no. Each via has track arms, and a 0.05 mm move trades the gap for a jog or an off-centre pad entry |
| East corridor and pin-28..31 band | 2 (BAT_FAULT_N / LOGIC_SOURCE_ST, LOGIC_SOURCE_ST / USB_LIMITED); with pads C92.2, R89.1 / .2 and R91.1 / .2 (6 Y2c rows) | not by an edit (D-S7-16: the corridor beside OE's via and the C92.2 / RAW_ACT slot hold three lanes only at 0.15 mm; R89 and R91 sit between the band's lanes) |
| A via under a lane | 1. CAM_MCU_RX (33.15, 44.5) under RADIO_NRST | no (the B.Cu run would jog) |
| C6's pocket | 1. CC1 (7.85, 32.75) | no (pass 1's trials) |
| **Pour-joined GND via at the DRC minimum** | 2. GNSS_ANT_GATE against grid vias (8.5, 13.6) and (11.0, 13.6); PULLPIN against (16.0, 50.6); with pads U30.18, U30.9, U31.11 and U31.5 (4 Y2c rows) | **yes, 0.05 mm each (02)** |
| Fine-pitch own part | U9.10 against BAT_ILIM (a Y2c row) | no |

Cause of the last class: the strip's stitching aid places vias at the rule clearance. `r9_rf_aid.py` docstring:
"clear of every non-GND copper item by its rule clearance (0.15; …)". The ground aid keeps 0.2 mm (R9_DECISIONS D-S8-02:
"MARGIN 0.05: no new Y1 / Y1b close pair").

## 5. The fix pass's copper, looked at for regressions

- **QSPI_IO2 (PYRO-01):** the east run on y 50.6 keeps 0.551 mm from U1.3 / U1.4, 0.252 mm from U1.6's 3V3 via and
  0.200 mm from C18.2's GND via (13.2, 50.05), which was 0.50 mm. That is above 0.2, so it adds no close pair. The C
  round the IMU vias keeps its shape and its knees (middle 1.9 mm, legs 0.95 / 3.5 mm). Clean.
- **TXEN at 0.2 mm, grid via 0.05 mm west:** no new pair under 0.2 mm. R-7's evidence is unchanged. Clean.
- **U31 module-ground vias:** each sits off the pads, 0.16–0.30 mm ring to its own GND pad and ≥ 0.64 mm from foreign
  pads, under the module where only GND may go (R-8 OK). Clean.
- **Copper-stage GND vias:** (35.6, 64.8) is flashed on F.Cu, In1 and B.Cu, inside C121.2's recorded corridor box.
  (32.9, 99.85) and (41.4, 41.1) keep ≥ 0.26 mm from foreign copper. Clean.
- **TP120 vias:** the RAW_ACT row is now x 31.5 / 32.2 / 33.4 / 34.6 / 35.5 at y 78.2 (pitch 0.7 / 1.2 / 1.2 / 0.9 mm).
  The first pair's rings are 0.1 mm apart. DRC-legal, and the holes are 0.40 mm apart (≥ the project's 0.25). Cosmetic: 03.
- **C98 and USB_LIMITED's end (POWER-01):** the decoupling loop is tight. C98.1 is 1.94 mm of track from U11.7. C98.2
  sits over U11.6, and the two share the GND via (38.5, 65.2). The hook east to C98.1 (x 40.05) and back to U11.7
  (x 39.3) is the cap-first feed, so it is purposeful. One leftover: from (35.825, 60.72) the trunk still runs
  (36.225, 61.12) → (36.225, 62.425) → (37.0, 63.2). x 36.225 is the column of C98.1's old spot (36.225, 62.8). That
  step no longer serves anything: 01.
- **Ground re-placements round C98:** the patch via (38.55, 58.95) sits 0.608 mm from (38.45, 58.35), a 0.108 mm ring
  gap. That is within the aid's 0.6 mm later-stage spacing (D-S8-02). The board had 22 same-net via pairs under 0.75 mm
  before and after (the launch pairs at 0.004 mm are R7's). This belongs to the planes dimension; no finding here.
- **route_check:** the 114 instances (103 distinct) equal `step10_evidence/gate/route.json` exactly.

## 6. Every remaining exception: does a DRC-clean edit remove it?

"DRC 0" means kicad-cli DRC at every severity, no violation and no unconnected item (library-table items excluded on the
scratch copies). route_check is profile r9, compared instance by instance with the unmodified copy.

| Item (record) | Edit tried | Result | Disposition |
|---|---|---|---|
| USB_LIMITED end, the step down x 36.225 (not recorded) | (35.825, 60.72) → (37.0, 61.895) → (37.0, 63.2) replaces three segments (`usbB`) | DRC 0. route_check OK, the same 114 instances. check_r9 P-0, P-1, P-2, P-3, P-5, P-6, P-7, P-9, K-power-pyro, K-copper, LC-1 and K-inner unchanged; ground gate OK. Length equal (2.967 mm); the lane step loses 2 of its 4 bends, and the trunk runs straight down R87.1's column into the T. The new diagonal keeps the 0.15 mm to LOGIC_SOURCE_ST that the segment it replaces had, so no new close-pair row | **01**: clean, recommended |
| C5 close pairs: the pour-joined GND vias at 0.15–0.195 mm | 13 vias moved 0.05 mm (`nudge2`): (5.95, 8.5) → (5.9, 8.5); (8.5, 13.6) → (8.5, 13.65); (11.0, 13.6) → (11.0, 13.65); (16.0, 50.6) → (16.05, 50.6); (16.35, 18.5) → (16.4, 18.5); (25.9, 10.56) → (25.9, 10.51); (35.9, 10.56) → (35.9, 10.51); (11.3, 10.66) → (11.3, 10.71); (13.61, 13.78) → (13.61, 13.83); (28.94, 7.2) → (28.89, 7.2); (32.48, 20.55) → (32.53, 20.55); (10.75, 6.8) → (10.7, 6.75); (13.8, 45.4) → (13.75, 45.4) | DRC 0. route_check OK, the same instances. check_r9 R-1…R-13, K-copper, P-0, P-7, P-9, K-power-pyro and LC-1 OK, every evidence field equal but K-copper's via-paste pair count. **Copper rows 32 → 24**, of which at ≤ 0.151 mm 14 → 12. **Pad rows 28 → 22**, of which at ≤ 0.151 mm 11 → 7. Removed rows: B.Cu GND / GNSS_ANT_GATE 0.15, GND / GNSS_VCC_RF 0.195, GND / RADIO_TXEN 0.171; F.Cu GND / GNSS_ANT_DC 0.193, GND / GNSS_VCC_RF 0.195, GND / PULLPIN 0.15, GND / QSPI_NCS 0.194, GND / RADIO_TXEN 0.171; pads U30.18, U30.9, U31.11, U31.5 0.15, U30.14 0.16, R302.2 0.164. Ground gate OK, all 13 gates, figures unchanged (§9) | **02** |
| same: (12.8, 6.9) → (12.85, 6.95) | (in a first set, `nudge`) | DRC: clearance 0.207 mm < 0.25 mm 'R7 RF50 coplanar gap' to R304.1 | rejected, so L30.1's 0.195 mm row stays |
| RAW_ACT via row after D-F1-04 (not recorded) | (32.2, 33.4, 34.6) → (32.5, 33.5, 34.5) at y 78.2, so the row is 31.5…35.5 at 1.0 mm pitch (`rawrow`) | DRC 0, route_check unchanged. RAW_ACT at 0.1 mm: 0.80 mΩ (base 0.80), neck 7.93 mm (7.92), 12.5 °C (12.6), largest barrel current 0.50 A at (31.5, 78.2) (0.49), none over 1 A | **03**: cosmetic option |
| ACT_GATE F.Cu hop (via (37.35, 89.0): C7's fold, S10b) | (26.6, 87.4) → (35.75, 87.4) → (37.35, 89.0) replaces three segments (`actg`) | DRC 0. route_check OK, the same instances. check_r9 P-0, P-1, P-2, P-3, P-5, P-6, P-7, P-9, K-power-pyro, K-copper, LC-1 and K-inner unchanged; ground gate OK. One bend and 0.47 mm less; the fold at the via becomes 45° (still in Y5) | **04**: optional |
| C6 CC1 via step | B.Cu from the via centre straight at y 32.75 into R7.1 (`cc1a`) | DRC 0, route_check FAIL tiny_jog CC1 (middle 0.424 mm) | keep (pass 1's other trials stand) |
| C15 candidates (pass 1) | my search, `cands.py` | GNSS_ANT_GATE again (0.9 mm shorter, gap 0.41 mm). The others turn an axial pad entry diagonal, add a segment under 0.2 mm, or trade two 45° bends for one 90° corner (VLOGIC F.Cu, GNSS_RESET_N, LED_RED, CAM_RX / TX_WIRE, whose current S-curves are mirror pairs) | keep, as pass 1 |
| C3 S8 / S9, C11d S4, C16 USB_LIMITED through U1, C7 folds | — | forced (§4.3); no removable via or redraw found | keep |
| E information instances (114) | — | each read; none is a rule instance | keep |

## 7. Findings

### R9P2-ROUTING-01 (Minor, worth fixing): USB_LIMITED's redrawn end keeps a step that served C98's old spot

- **Requirement:** REQUIREMENTS M2 (no needless detours or jogs; clean routing over the whole board); owner priority 2.
- **Evidence:**
  - `m3_design/r9_route_power_ctl.py:65-66` draws the trunk `… (X_U2 + 0.4, S_U), (35.825, S_U), (36.225, S_U + 0.4),
    (36.225, 62.425), (37.0, Y_C98)` with `S_U = 60.72` (line 53) and `Y_C98 = 63.2` (line 58).
  - On the board, B.Cu at 0.3 mm: (35.825, 60.72) → (36.225, 61.12) → (36.225, 62.425) → (37.0, 63.2), then the T to
    C98.1 / U11.7 and R87.1.
  - Before the fix pass, C98.1 sat at (36.225, 62.8) (`fc3d5b34…`; old `r9_place.tsv` row `C98 37 62.8 0 B`), so the
    trunk ran down that column on purpose.
  - The fix moved C98 to (39.275, 64.2) rot 180 (C98.1 at (40.05, 64.2)) and redrew the end, but kept the column.
    It now ends in a 45° jog onto R87.1's column x 37.0. My knee scan flags the new window: a middle of 1.305 mm and
    0.923 mm offset.
  - USB_LIMITED is a critical class in route_check (power), but the gate's bump audit looks only at windows that turn
    back, so this lane step passes it.
- **Trial** (`usbB`): one diagonal (35.825, 60.72) → (37.0, 61.895), then straight down x 37.0 to the T at (37.0, 63.2).
  - DRC 0 at every severity; route_check r9 OK with the same 114 instances.
  - check_r9 P-0, P-1, P-2, P-3, P-5, P-6, P-7, P-9, K-power-pyro, K-copper, LC-1 and K-inner unchanged; the
    ground gate passes (§9).
  - Equal length (2.967 mm); two bends fewer.
  - No new close pair: the diagonal keeps 0.15 mm to LOGIC_SOURCE_ST, as the segment it replaces does.
  - The R87.1 branch then continues the trunk's line.
- **Fix:** in `r9_route_power_ctl.py:66`, replace `(36.225, S_U + 0.4), (36.225, 62.425), (37.0, Y_C98)` with
  `(37.0, S_U + 1.175), (37.0, Y_C98)`, then rebuild with `r9_build.sh`.
  - The ground gate passes on the variant (§9).
  - The ground aid's `--check` should still be re-run in the build, since the GND fill between the RAW_ACT pour and the
    trunk changes shape.

### R9P2-ROUTING-02 (Minor, worth fixing): C5's close pairs have no "why not removable"; 13 GND-via moves remove 14 rows

- **Requirement:** REQUIREMENTS M2: every review-only residual is listed "with location, rule, measured reason and why it
  cannot reasonably be removed (or that it has not been removed yet)". r9_plan §2 done rows: Y1 ≤ 10, Y1b = Y2c = 0.
- **Evidence:**
  - R9_VALIDATION C5 gives counts (30 / 14 / 11) and "every pair DRC-legal (≥ 0.15 mm)", with no reason per row or class.
  - Step 9's decision (R9_DECISIONS, the done-row list after step 9) says only "steps 4–7's routing".
  - My classification of the 14 Y1b rows and 11 Y2c rows is in §4.5.
    - Most are geometry-forced. A 0.5 mm via on a pin line between lanes at 1.0 mm pitch leaves exactly 0.15 mm a side.
      Also: the east corridor and band, a via under RADIO_NRST, C6's pocket, U9's fine pitch.
    - One class is not forced: pour-joined GND vias at the DRC minimum. They come from the strip's stitching aid, which
      places vias at the rule clearance (`r9_rf_aid.py` docstring, lines 10–13), whereas the ground aid keeps 0.2 mm
      (D-S8-02).
  - `nudge.py` finds a 0.05 mm move for each of 14 such vias. One, (12.8, 6.9), breaks the 0.25 mm RF coplanar rule
    and is dropped.
- **Trial** (`nudge2`; the 13 moves are listed in §6):
  - DRC 0; route_check unchanged; check_r9 R-1 … R-13, K-copper, P-0, P-7, P-9, K-power-pyro and LC-1 OK, with R-7's
    stitching evidence equal.
  - Copper rows 32 → 24 (scorecard Y1 30 → 24, Y1b 14 → 12); pad rows 28 → 22 (Y2c 11 → 7).
  - Every listed gap goes from 0.15–0.195 mm to ≥ 0.2 mm.
  - The ground gate passes on the variant, all 13 gates (§9). Reach p95 3.37 / max 7.32 mm, P7 9 and R6b 0.1022 are
    unchanged.
  - Where the moved vias come from:
    - eight are `r9_rf.GRID` rows (`r9_rf.py:229-245`): (5.95, 8.5), (8.5, 13.6), (11.0, 13.6), (16.35, 18.5),
      (25.9, 10.56), (35.9, 10.56), (11.3, 10.66) (the aid's hand seed) and (13.61, 13.78);
    - three are strip-template partners: J31 frame (−3.35, 7.2) "partner TXEN" (`r9_rf.py:208`), U31 frame
      (1.87, 6.55) "partner TXEN" (`r9_rf.py:214`), and U30 frame (−0.4, −7.25) "partner V1 / V3" (`r9_rf.py:212`).
      Each stays well within 1.5 mm of its signal via;
    - two are routing-family partners: `r9_route_qspi_hse.py:50` (16.0, 50.6), HSE_IN's partner, then 0.95 mm from its
      via; and `r9_route_imu_baro.py:51` `G['A']` (13.8, 45.4).
  - The rows at the DRC minimum all come from the GRID and routing-family vias. If the RF owner prefers to keep the
    template vias at R7's spots, 10 moves still give Y1b 12 and Y2c 7.
- **Fix:**
  - Records (cheap): give C5 the classes and counts of §4.5, with the reason each forced class cannot be removed.
  - Copper (optional, table edits): either take the 13 moves, or make `r9_rf_aid.py` keep the ground aid's 0.05 mm
    margin and re-freeze GRID.
  - With the moves, C14's list of crystal-plane bonding vias changes ((16.0, 50.6) → (16.05, 50.6)).
  - Severity: Minor. The pairs are DRC-legal and well above JLC's spacing limit; the gain is margin and two done rows
    moving toward target.

### R9P2-ROUTING-03 (Minor): the RAW_ACT via row lost its regular pitch when the TP120 via moved

- **Requirement:** owner priority 2 (layout reads as deliberate); REQUIREMENTS M2 (tidiness).
- **Evidence:**
  - `r9_power.py:291`: the y 78.2 row is x 31.5, 32.2, 33.4, 34.6, 35.5.
  - (31.5, 78.2) and (32.2, 78.2) sit 0.7 mm apart with rings 0.1 mm apart, so they read as a doubled via over Q121's
    drain row. The other pitches are 1.2 mm and 0.9 mm.
  - Before D-F1-04 the row was 29.6 / 31.0 / 32.2 / 33.4 / 34.6 / 35.5 at 1.4 / 1.2 / 1.2 / 1.2 / 0.9 mm.
- **Trial** (`rawrow`): 31.5 / 32.5 / 33.5 / 34.5 / 35.5 at 1.0 mm.
  - DRC 0; route_check unchanged.
  - RAW_ACT at 0.1 mm: 0.80 mΩ (equal), neck 7.93 mm (7.92), 12.5 °C (12.6).
  - Largest barrel current 0.50 A (0.49), none over 1 A.
- **Fix:** optional, at the next copper change: three entries of the row in `r9_power.RAW_ACT_VIAS`, then the 0.05 mm
  RAW_ACT solve. Not worth a fix pass on its own.

### R9P2-ROUTING-04 (Minor): ACT_GATE's F.Cu hop can be one diagonal

- **Requirement:** REQUIREMENTS M2 (no needless jogs, via folds); r9_plan S10b (signal bends; ACT_GATE is counted).
- **Evidence:**
  - ACT_GATE F.Cu runs: via (26.6, 87.4) → (36.55, 87.4) → (37.35, 88.2) → via (37.35, 89.0).
  - The last two segments, 0.8 mm vertical and 1.13 mm diagonal, make the via's F.Cu arm leave parallel to its B.Cu
    arm to R121.1. That is C7's fold at (37.35, 89.0), 0.8 mm.
- **Trial** (`actg`): (26.6, 87.4) → (35.75, 87.4) → (37.35, 89.0).
  - DRC 0; route_check unchanged; check_r9's pyro and copper rules unchanged; the ground gate passes (§9).
  - One bend and 0.47 mm less (S10b 260 → 259). The fold becomes a 45° one, so it still counts in Y5 (C7 counts arms
    within 45°).
- **Fix:** optional. In `r9_power.py:357` (`gate()`), replace the F.Cu polyline
  `[vw, (ve[0] - 0.8, yh), (ve[0], yh + 0.8), ve]` with `[vw, (ve[0] - (ve[1] - yh), yh), ve]`, which gives
  (35.75, 87.4). Not worth a fix pass on its own.

## 8. The board read again

I read the 24 labelled tiles of both outer layers and zooms, and agree with pass 1's reading.

- The RF strip is template-regular.
- The interface field's rivers run parallel.
- U1 fans out on four faces, with its interior used as a crossroads in an ordered way.
- The servo fan is mirror-symmetric.
- The CH1 column has 1.0 mm bars on its terminals' lines.
- The east column's power lanes are dense but square.

The fix pass's changes are small and local. C98's decoupling loop is better than before; the camera UART wires are mirror
S-curves. The longest and least elegant lanes are as recorded, each with its forcing cause:

- BAT_FAULT_N, 75.9 mm: U9.4 exits only toward +y, on the wrong side for the east edge.
- RADIO_TXEN's loop, keep-out-forced.
- NRST's B.Cu dive.
- USB_LIMITED's trunk through U1's interior (C16).

## 9. Gate run and repository state

- `NUMPY_PY=<cfd venv> tools/check.sh` on the repository board (about 5 min): **exit 0**.
  - DRC 0, unconnected 0, parity 0, ERC 0; metadata / 3D OK; silkscreen 0; fit OK; rule-H seeded suite OK.
  - All 40 check_r9 rules OK; actuator contract OK.
  - routing hygiene "0 failing, 0 allowlisted, … 0 leftovers … (14 bump windows searched): OK".
  - Its `route.json` equals `step10_evidence/gate/route.json`.
- I ran the ground gate (`m3_design/r9_ground_check.py`, all 13 gates, DRC with parity) on scratch copies that carry
  the schematic.
  - Copies: the repository board, `nudge2` (02), `usbB` (01) and `actg` (04).
  - Result: **R9 ground gate: OK** on all four.
  - Reach p95 3.37 mm / max 7.32 mm at (31.25, 91.25), P7 9 and R6b 0.1022 (3,206 / 31,359) are the same on all four.
- Variants `rawrow` (03) and `cc1a` (C6) had DRC and route_check only, plus the RAW_ACT DC solve for `rawrow`.
- Board SHA-256 before and after: `4f841a0e…` (unchanged). `git status --porcelain`: the same 113 lines before and
  after; this file sits in the untracked `sources/r9_review/` folder. Scratch copies, variants and my gate run's
  temporary report folder were deleted at the end.
