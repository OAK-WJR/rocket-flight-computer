# R8 review pass 4: routing simplicity and geometry (whole board)

Reviewer: independent, read-only. Dimension: the geometry and simplicity of every track and via on all four layers, rigid
R7 copper included: AGENTS §3 rule instances, staircases, jogs and knees, local bumps, detours and extra vias, bus
tidiness, pad entries, width discipline, layer discipline (no signal on In1 / In2 except D70), adjacency, and, for every
remaining exception, whether a DRC-clean edit removes it. First the three pass-3 routing findings are re-checked, then
fix pass 3's copper changes one by one, then the whole board.

- **Board reviewed:** `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
  `c84f00b88f5fb9409de40f33b2d51a48fb29fb66c386c869b7f93ea791e37c54`. The SHA and `git status` were the same before
  and after this review.
- **Contents** (my scan): 795 tracks, 609 vias, no arcs.
  - F.Cu: 408 tracks, 1,225.7 mm. B.Cu: 386 tracks, 859.7 mm (pass 3: 861.7 mm; −1.98 mm CAM_PWR_EN, −0.05 mm
    RAW_ACT_SENSE / USB_LIMITED).
  - In2: 1 track, 3.4 mm (ARM1_SENSE at x 14.55, rigid, D70). **In1: none.**
  - Vias: 309 × 0.6 mm and 300 × 0.5 mm, all 0.3 mm drill, all through (pass 3: 310 / 299; R165's BAT_ENABLE via).
    GND: 428 (237 × 0.5, 191 × 0.6), unchanged.
- **Fix pass 3's copper diff** (`990c8040…` → `c84f00b8…`): the `990c8040…` board was rebuilt in scratch from the
  coordinator's backup (R7's committed board plus the m3.kicad_pcb hunk of `r8_backup_990c8040/tracked.diff`; its SHA-256
  matched `990c8040…` exactly). 11 tracks removed and 11 added, 2 vias removed and 2 added, one footprint moved (R172
  x 30.6 → 30.65), on 6 nets (§4). Nothing else changed.
- **Gate** (`tools/check.sh`, run by me on the repository board, exit 0): DRC 0, unconnected 0, parity 0, ERC 0;
  metadata / 3D OK; silkscreen 0; R8 CAD contract OK; route_check "0 failing, 3 allowlisted, … 0 removable local bumps on
  critical nets (22 bump windows searched): OK"; actuators OK; fit OK.
- **Tests:** `tools/test_route_check.py` (57 tests) OK under KiCad's Python (the fix pass ran all 272).
- **`step9/m2_sweep.py`** re-run by me on a copy: chain_detour 23, adjacency 53 rows (28 net pairs, 9 at 0.150 mm),
  adjacency_pad 33, via_step 1, poured_hop 2, routes 28, pad_edge 0, via_fold 26, short_hop 9, bumps_all 1 (7 windows),
  margin_free 1 bump (29 windows) + 4 redraws. Each equals R8_VALIDATION C11 / C12 / C12b / C13 / C14 / part F.
- **Repository changes:** none except this file. **Scratch:** `<scratch>/r8p4rt/` (the session scratchpad), `<s>` below.
  Variant boards were written only under `<s>/v/<name>/` in a copy of the project and deleted after their results were
  logged (`<s>/logs/`). The board copies (`r8.kicad_pcb`, `p3.kicad_pcb`) were deleted at the end too; the appendix says
  how to recreate them.

## 1. Verdict

The R8 routing reads as deliberate, simple and logical, and fix pass 3's three copper edits are clean:
- **Segments:** no off-angle segment, arc, zero-length piece, staircase, dangling end or via, same-net crossing without a
  node, collinear or side-by-side overlap. Every same-net "touch" without a shared node is two tracks meeting inside one
  pad (C18 / D99 class) or R7's rigid PYRO1_OUT copper.
- **Buses:** the GNSS river, the radio bus, the servo bus, the pyro corridor, the QSPI / IMU fans and the SWD / USB lanes
  are parallel lanes at constant pitch. I read all 48 tiles (16 × 16 mm, F and B separately).
- **Width and layers:** per-net width families unchanged; In1 carries no track, In2 only D70's rigid 3.4 mm.
- **Fix pass 3:** all three pass-3 routing findings are closed as measured (§3), and the edits introduce no new
  category instance in any of my scans or in `rg/scan.pyc` (§4, §5).

**No Critical and no Major.** No AGENTS §3 rule instance is new, and the gate's own bump search, the sweep's margin-free
search and my re-tap search find no removable bump or detour on a critical net.

Two Minor findings, both cheap and DRC- / gate-clean in trial. Each removes a recorded exception that the record calls
fixed in place:
- **R8P4-ROUTING-01.** RADIO_MISO_MCU and RADIO_MOSI sit 0.150 mm from two GND vias in their fence slot (C12 #5 / #6,
  recorded "not cheap to open"). The radio trio below the fence is off-centre in its opening (0.25 mm west, 0.15 mm east):
  a 0.1 mm west shift of the trio's lanes there (its in-strip step 0.4 → 0.5 mm, one lane pitch) and 0.05 mm moves of three
  GND vias open both pairs to 0.200 mm.
- **R8P4-ROUTING-02.** USB_LIMITED's 0.25 mm branch to R87.1 (the OVLO divider top) leaves C98.1 at 45° to the trunk's own
  diagonal (the board's only R8-new acute branch pair) and runs 2.55 mm back west under the trunk before turning south.
  A straight T drop from the trunk at x 32.2 is 1.86 mm shorter and removes the wedge, a corner and the doubled copper.

The two together (variant `rec4`) are DRC 0 / 0 / 0 with parity; route_check differs by one information instance (a
width step at the new T, an allowed category); check_r8 and check_actuators pass. M2 sweep: track / via net pairs under
0.2 mm 28 → 26, pairs at 0.150 mm 9 → 7; everything else equal.

## 2. Method

Every script is in `<s>/` and runs in KiCad 10.0.6's Python with boards loaded read-only.

| Script | What it does |
|---|---|
| `p4scan.py` | **My independent scan, written for this pass.**<br>- Per segment: off-angle (> 0.01°), zero length, inner-layer track, off-grid ends.<br>- Node graph per (net, layer) by end clustering (1 µm); each node typed pad (exact `GetEffectivePolygon`), via, T (end on a same-net body), fill (`HitTestFilledArea`), plain, junction or dangling.<br>- Chains between non-plain nodes: length, octile, detour (> 1.25 × and > 0.5 mm), acute and right corners, knees / jogs (heading regained within 1–2 segments, middle length and lateral offset), staircases, U-turns, short interior segments.<br>- Same-net pairs: parallel overlap, crossing without a node, copper touch without a node.<br>- Vias: arms per layer, one-layer vias, via-to-via tracks, steps inside a ring, off-centre arms, folds (≤ 45°), vias in SMD pads, critical-signal vias with no GND via within 1.5 mm.<br>- Widths and via sizes per net; width steps at plain nodes; pad entries (offset, axial, lateral offset); different-net edge gaps < 0.2 mm (track, via, pad polygon, per copper layer) |
| `diff4.py` | Track / via / footprint / zone-area diff between two boards |
| `par.py`, `retap.py` | Same-net parallel runs (lateral < 1.5 mm, overlap > 0.8 mm); branches whose far end lies nearer (octile) to another point of the same net's copper on the layer than the branch is long (a re-tap search, candidates read one by one) |
| `gapnet.py`, `q.py`, `cross.py`, `rigid.py`, `vias06.py` | Gaps under T for named nets; point query; copper crossing a line; R7-identical tracks; 0.6 mm vias on signal nets |
| `rgscan/scan.pyc` | The earlier reviewers' `rg/scan.py` (source gone; its cached bytecode run as pass 3 did) |
| `../r8p3rt/render.py` | SVG / PNG of a window (F red, B blue, In2 green, pads, vias, fills) |
| `variant.py`, `vrun.sh`, `rcdiff.py` | Pass 2 / 3's tools: apply an edit list to a copy of the board in a copy of the project, refill natively, then `kicad-cli pcb drc --severity-all --schematic-parity`, `route_check --profile r8`, `check_r8`, `check_actuators`, and diff route_check instances against `base` (no edit). `base` reproduces DRC 0 / 0 / 0 and the gate's route_check result |
| `m2_sweep.py` (repository) | Run on the board and on variant `rec4` |

## 3. Previous findings in this dimension (pass 3)

| Pass 3 | Disposition (R8_VALIDATION) | Checked on `c84f00b8…` | Closed? |
|---|---|---|---|
| R8P3-ROUTING-01: USB_LIMITED 0.150 mm from CAM_PWR_EN, 0.180 mm from R172's bare pads | Fixed (D106) | Trunk on y 37.3 ((15.4, 36.35) → (16.35, 37.3) 45°, → (29.95, 37.3) → (29.95, 54.0)); TP82 tap from (19.4, 37.3). CAM_PWR_EN–USB_LIMITED 0.200 mm (three segments, `gapnet.py`); R172 at (30.65, 48.1); R172.1 / R172.2–USB_LIMITED 0.230 mm; the RAW_ACT_SENSE lane x 30.65 is exactly 0.200 mm from USB_LIMITED's 0.6 mm hop via (31.25, 55.3), as pass 3 predicted. No new pair under 0.2 mm | **Closed** |
| R8P3-ROUTING-02: R165's BAT_ENABLE via drawn 0.6 mm, 0.180 mm from Q120.9 | Fixed (D108) | Via (16.6, 104.5) 0.5 / 0.3 mm; Q120.9–via 0.230 mm; BAT_ENABLE's nearest BAT_IN copper U9.1 / feed 0.200 mm (U9's pitch). BAT_ENABLE now has only 0.5 mm vias | **Closed** |
| R8P3-ROUTING-03: CAM_PWR_EN's lower leg, hidden 1.98 mm redraw | Fixed (D107) | (31.85, 43.0) → (31.85, 36.8) → (28.25, 36.8) → (28.25, 30.025) → (30.775, 27.5): 20.146 mm against a 15.945 mm octile (excess 4.20, C11 #9); the last run is 45° into R74.1's centre. Net ratio 1.38 (`routes`). The moved step-7 cover via (29.125, 32.625) is 0.525 mm (edge) from the lane; CAM_PWR_EN's nearest new copper > 0.3 mm. `margin_free` finds only part F's BAT_ENABLE false positive and C11's four "found" redraws | **Closed** |

## 4. Fix pass 3's copper changes, one by one (`diff4.py`)

| Net | Change | Judgement |
|---|---|---|
| USB_LIMITED | 5 tracks −/+ : corner (16.3, 37.25) → (16.35, 37.3), trunk y 37.25 → 37.3, TP82 tap from (19.4, 37.3) | Clean: the 45° from (15.4, 36.35) is kept, the TP82 T (0.4 / 0.3 mm) moved with the trunk (E width_change_junction, same count) |
| RAW_ACT_SENSE, RAW_ACT_SENSE_MCU; R172 | lane x 30.6 → 30.65 with its 45° (30.0, 58.1) → (30.65, 57.45); R172.2 stub now 0.43 mm (was 0.48) | Clean: axial entries to both pad centres; C5's net figure 2.58 mm / 0.71 mm (3.62 ×), C14's fold (31.75, 47.0) unchanged |
| CAM_PWR_EN | 3 tracks −/+ (above) | Clean: one right angle and one U-turn fewer (`p4scan` right corners 58 → 57, U-turns 8 → 7; `rg/scan.pyc` right angles 59 → 58, diagonal pad entries 51 → 52) |
| BAT_ENABLE | via 0.6 → 0.5 mm in place | Clean |
| GND (step 7) | cover via (28.875, 32.875) → (29.125, 32.625) | Clean: 0.525 mm from CAM_PWR_EN; no new gap under 0.3 mm |

Zone areas moved by < 1.4 mm² (B.Cu GND +1.4 mm², the freed CAM_PWR_EN corridor). The scan diff `s4_p3.json` →
`s4.json` changes only these items (chain_detour, knee, pad_entry, right_corner, u_turn rows of the nets above, and 6 gap
rows removed: the three USB_LIMITED / CAM_PWR_EN segment pairs, both R172 pad rows and Q120.9 / BAT_ENABLE).

## 5. Whole-board scans

### 5.1 Independent scan (`p4scan.py`)

| Category | Count | Notes |
|---|---:|---|
| off-angle / arcs / zero-length | 0 / 0 / 0 | |
| inner-layer track | 1 | C1 (D70, rigid) |
| dangling end / one-layer via | 0 / 1 | the via is TP122's PYRO1_GATE (A1, rigid; it lies in its own test pad) |
| crossing without a node / parallel overlap | 0 / 0 | |
| copper touch without a shared node | 9 | all are two tracks of one net meeting inside one pad (C100.1, C83.2, C72.2, C75.1, L3.2, C73.1 / C72.1) or rigid R7 copper (PYRO1_OUT at Q124.5, 3V3_GNSS at C301.1) |
| track end on a same-net body (T) | 6 | 3V3 (36.75, 70.4), CAM_5V (40.75, 43.17), CAM_SW (39.95, 37.61), 3V3A (26.5, 53.7); rigid GNSS_ANT_DC, PYRO1_BUS |
| plain 3-way junctions | 37 | Ts drawn as split trunks (USB_LIMITED (19.4, 37.3) moved with the trunk) |
| acute pair at a node | 3 | all at pads: rigid R133.1 (ARM1_SENSE) and Q30.2 (GNSS_ANT_SRC); **C98.1 (USB_LIMITED, R8-new): R8P4-ROUTING-02** |
| right-angle corners | 57 | allowed |
| knees (heading regained after 1–2 segments) | 51 | the sub-1 mm ones are pass 3's list, unchanged: radio trio RXEN / BUSY / MISO 0.40 mm (R8P4-ROUTING-01 makes it 0.50), DIO1 0.45, SWCLK 0.50, QSPI_IO3 0.50, RADIO_SCK 0.60, QSPI_IO0 0.63, CAM_MCU_TX 0.75 |
| staircases | 0 | |
| U-turns | 7 | PYRO1_CONT ×2 and RADIO_TXEN (rigid / C11), 3V3A at U4, USB_DM, SPI1_SCK, BAT_ENABLE (C11) |
| chain detours | 23 | = C11, run for run |
| short interior segments < 0.5 mm | 2 | RADIO_TXEN's rigid 0.424 mm mitres |
| via folds (non-GND) | 26 | = C14 |
| via-to-via tracks | 6 | 3V3 hop (D40), 3V3A hop, VBUS spine, USB_LIMITED hop; rigid GND 0.9 mm and ARM1_SENSE In2 |
| step inside a via / off-centre via arm | 1 / 1 | ARM1_SENSE (18.18, 91.3), rigid |
| critical-signal via, no GND via within 1.5 mm | 1 | A1 |
| width step at a plain node | 1 | CAM_INPUT_LIMITED (35.0, 31.65), U7.5's neck (E) |
| pad entries ending > 0.1 mm off centre | 63 (48 pads) | equal to the `990c8040…` board, entry for entry (includes pads > 2 mm, which route_check's 41 omit) |

`rgscan/scan.pyc` agrees: acute_at_padvia 3 (the same three), collinear_unmerged 1 (U7.5's neck), short_segment 2
(rigid), end_in_zone_only 1 (BAT_IN pour stub); its other counts equal pass 3's except the CAM_PWR_EN changes above.

### 5.2 Adjacency

- Track / via pairs (`m2_sweep adjacency` = my scan): 28 net pairs under 0.2 mm, 9 at 0.150 mm = C12.
- Pad rows: 33 = C12b.
- **C12 #5 / #6 have a second 0.150 mm instance each** that the table does not name: spike (d)'s stitch via (22.1, 26.7)
  sits in the same MISO–MOSI slot as the fence via (22.1, 23.3), 0.150 mm from both lanes (R8P4-ROUTING-01).

### 5.3 Widths, vias and layers

- **Widths:** unchanged families (signals 0.2; actuator gate family, BAT_SW_*, CAM_FB 0.25; RF 0.3; rigid TXEN and one
  PYRO1_CONT piece 0.15; power per D-number). Width steps only at pads, vias and Ts, plus U7.5's neck.
- **Via sizes:** 0.5 mm for most signals and step 7, 0.6 mm for power. Pass 3 called BAT_ENABLE the one signal exception;
  it was not the only one. Seven R8-new signal vias use the 0.6 mm via by generator choice: the servo T-vias SERVO1–4_MCU
  at x 32.6 (`r8_route_servo.py` imports only `VIA_PWR`), CAM_FB (38.25, 33.1) and ACT_GATE (13.48, 98.95) / (13.48,
  107.16) (`r8_power.py`'s default). None has foreign copper within 0.3 mm (`gapnet.py`), so a smaller ring gains nothing;
  noted, no finding.
- **Layers:** In1 no track; In2 only D70's.

## 6. Topic by topic

- **Knees, jogs, staircases:** no tiny jog (middle < 0.5 mm or offset < 0.25 mm), no staircase. The sub-1 mm knees are
  §5.1's list, each with its recorded cause.
- **Folds, detours, extra vias:** C14's 26 folds, C13's 12 nets over need (none over need + 2) and C11's 23 detours are
  confirmed. The re-tap search (`retap.py`, 0.8 mm gain threshold) lists, after removing chains whose "tap" is their own
  neighbour, these real candidates: R87.1's branch (1.86 mm, clean: R8P4-ROUTING-02); VBUS → R9.1 (2.15 mm; the 45° tap
  off the VBUS diagonal overlaps R110.1, not clean); U11's IN1 feed along y 62.6 (2.1 mm; a y 60.5 lane hits C84.2, the
  y 62.6 lane runs between C84's pads, D46); VLOGIC → TP83 (1.03 mm, would tap a sense line: not better); the rest are
  C11 runs whose redraw is blocked (RAW_PROTECTED round PYRO_BLOCK, the rigid RF strip).
- **Bus tidiness:** unchanged and good. The one irregularity is the radio trio's position in its fence opening
  (R8P4-ROUTING-01).
- **Pad entries:** unchanged from pass 3 apart from R74.1 (now a 45° entry to the centre) and R172's (axial, to the
  centres). R172.2's lateral stub from the via's 45° is 0.43 mm (was 0.48), ending at the centre; it is RAW_ACT_SENSE_MCU,
  a non-critical net, and route_check is silent.

## 7. Remaining exceptions: does a DRC-clean edit remove them?

- **C11 (23 runs):** the margin-free search on this board finds only the 4 "found" rows (#20–#23), each not simpler
  (pass 3's 4-segment search covered the others; only CAM_PWR_EN's run changed, now covered by `margin_free`).
- **C12 0.150 mm pairs (9):**
  - **#5 / #6 (GND / RADIO_MISO_MCU, GND / RADIO_MOSI):** removable (variant `fence2`, R8P4-ROUTING-01).
  - **#1, #4, #8:** an escape via on its own pin's row 0.5 mm from the neighbour pin's lane. 0.2 mm needs the via off the
    pin row, so a jog; not cheap (as recorded).
  - **#2:** the F.Cu pair (FAULT_N's y 43.5 lane under PWR_EN's via on pin 42's row) stays whatever the via's x.
  - **#3, #7, #9:** U12 / U4 pad pitch (a via moved outward breaks its stub's angle).
- **C12b:** pass 3's trials still apply (R166 0.025 mm and the R120.2 via: clean but no gain against the pour). No
  copper there changed.
- **Acute pairs:** C98.1 removable (variant `r87`, R8P4-ROUTING-02); R133.1 and Q30.2 are rigid R7 copper.
- **E and C14:** unchanged; no new instance.

| Variant | Edit | DRC / parity | route_check vs `base` | check_r8 / actuators | Effect |
|---|---|---|---|---|---|
| `base` | none | 0 / 0 / 0 | — (gate's result) | OK / OK | reproduces the board |
| `fence` | trio below the fence −0.1 mm (x 20.5 / 21.0 / 21.5), fence vias (20.0, 23.3) → (19.95, 23.3), (22.1, 23.3) → (22.05, 23.3) | 0 / 0 / 0 | identical | OK / OK | MISO 0.200 mm; MOSI still 0.150 mm from the stitch via (22.1, 26.7) |
| `fence2` | `fence` + stitch via (22.1, 26.7) → (22.05, 26.7) | 0 / 0 / 0 | identical | OK / OK | RXEN, MISO, MOSI each 0.200 mm from the moved vias; C12 #5 / #6 gone |
| `r87` | USB_LIMITED trunk split at (32.2, 55.3); R87.1 branch (32.2, 55.3) → (32.2, 57.775) replaces (35.25, 56.2) → (32.7, 56.2) → (32.2, 56.7) → (32.2, 57.775) | 0 / 0 / 0 | + 1 width_change_junction (T, 0.4 / 0.25) | OK / OK | acute pairs 3 → 2; B.Cu −1.86 mm; USB_LIMITED clearances within 0.6 mm identical |
| `rec4` | `fence2` + `r87` | 0 / 0 / 0 | as `r87` | OK / OK | M2 sweep: adjacency 53 → 51 rows, net pairs 28 → 26, 0.150 mm pairs 9 → 7; pad rows 33, chain 23, folds 26, routes 28, bumps_all 1, margin_free 1 + 4: unchanged |

## 8. Findings

### R8P4-ROUTING-01 (Minor, worth fixing): the radio trio sits off-centre in its fence opening, leaving MISO and MOSI 0.150 mm from two GND vias; a 0.1 mm shift and three 0.05 mm via moves open both to 0.200 mm

**Requirement.**
- REQUIREMENTS M2: adjacency on every net is a review item, and every residual must say "why it cannot reasonably be
  removed".
- R8_VALIDATION C12 #5 / #6 ("the fence via in the MISO–MOSI slot (D16's ≤ 2.7 mm openings)"), and C12's reason column:
  "… or the strip fence via in the radio bus's MISO–MOSI slot (D16); not cheap to open (D91 …)".
- RADIO_MISO_MCU and RADIO_MOSI are critical signal nets (AGENTS §3: "the other RADIO_* / GNSS_* nets").
- Owner priority 2 (robust design).

**Finding.**
- Below the fence (F.Cu, `r8_route_rf.py` l. 77–86) the trio runs at x 20.6 / 21.1 / 21.6 (0.5 mm pitch) in the opening
  between fence vias (20.0, 23.3) and (22.1, 23.3). It is off-centre: RXEN is 0.25 mm from the west via, MISO 0.150 mm
  from the east one.
- MOSI at x 22.6 is 0.150 mm from the same via. Spike (d)'s stitch via (22.1, 26.7) (`make_ground.STRIP_STITCH`) sits in
  the same slot, also 0.150 mm from both lanes; C12 names only the fence via.
- The record treats the slot as fixed. It is not: the trio's in-strip x (21.0 / 21.5 / 22.0, which keeps no GND finger
  between MISO and MOSI inside the strip) need not change. Only the below-fence lanes and the step change: the 45° runs
  to U1 lie on the same lines (x − y = −9.9 / −9.193 / −8.486), only 0.14 mm longer. The step becomes 0.5 mm, exactly one
  lane pitch.

**Evidence.**
- Measured on `c84f00b8…` (`cross.py` at y 23.3, `gapnet.py`): fence vias 18.2, 20.0, 22.1, 24.15, 26.0; lanes RXEN 20.6,
  BUSY 21.1, MISO 21.6, MOSI 22.6, NSS 23.2, SCK 25.1. MISO–(22.1, 23.3) 0.150, MISO–(22.1, 26.7) 0.150,
  MOSI–(22.1, 23.3) 0.150, MOSI–(22.1, 26.7) 0.150, RXEN–(20.0, 23.3) 0.250 mm.
- **Variant `fence2`:**
  - The edit: RXEN (21.0, 22.0) → (20.5, 22.5) → (20.5, 30.4) → (26.5, 36.4); BUSY (21.5, 22.207) → (21.0, 22.707) →
    (21.0, 30.193) → (27.0, 36.193); MISO (22.0, 22.414) → (21.5, 22.914) → (21.5, 29.986) → (27.5, 35.986). GND vias
    (20.0, 23.3) → (19.95, 23.3), (22.1, 23.3) → (22.05, 23.3), (22.1, 26.7) → (22.05, 26.7).
  - DRC 0 / 0 / 0 with parity. route_check identical to `base` (93 instances, 0 failures). check_r8 OK, its fence (D16)
    and rf_separation (F10) checks included; actuators OK.
  - RXEN–(19.95, 23.3), MISO–(22.05, 23.3) / (22.05, 26.7), MOSI–(22.05, 23.3) / (22.05, 26.7): all 0.200 mm. No new pair
    under 0.2 mm; the trio's own pitch stays 0.5 mm (0.3 mm gaps).
  - Fence openings 18.2 → 19.95 = 1.75 mm (no lane: ≤ 2.0 mm ✓), 19.95 → 22.05 = 2.10 mm and 22.05 → 24.15 = 2.10 mm
    (openings ≤ 2.7 mm ✓). The rf family grows 0.25 mm (build 3's gate: 436.6 of 445 mm).
- **Variant `rec4`** (with R8P4-ROUTING-02), m2_sweep: net pairs under 0.2 mm 28 → 26, 0.150 mm pairs 9 → 7; the two pairs
  that leave are exactly GND / RADIO_MISO_MCU and GND / RADIO_MOSI.

**Why Minor.**
- Every gap is DRC-legal and tented. A short needs an etch defect, which JLC's electrical test screens (Inference).
- Its effect is a radio that cannot talk (MISO or MOSI held low), found on the bench, not a safety path.
- But these are the only 0.150 mm pairs on the board that are not bound by a part's pad pitch, and the record says they
  cannot cheaply be opened.

**Fix.**
- `m3_design/r8_route_rf.py` l. 84–86: TRIO x 20.6 / 21.1 / 21.6 → 20.5 / 21.0 / 21.5; step y 22.400 / 22.607 / 22.814 →
  22.500 / 22.707 / 22.914; TRIO_STEP 0.4 → 0.5 (the in-strip x stays 21.0 / 21.5 / 22.0). Update the l. 77–80 comment
  ("a 1.1 mm slot", "steps 0.5 mm").
- `sources/r8_design/step7/make_ground.py` l. 92–94: FENCE_X 20.00 → 19.95 and 22.10 → 22.05; STRIP_STITCH
  (22.10, 26.70) → (22.05, 26.70).
- Regenerate `r8_ground.tsv` from the step-6 board (fix pass 3's stage A), rebuild twice, run the gate and the sweep.
- Records: delete C12 #5 / #6 and the "fence slot" clause of C12's reason, the trio's sub-1 mm knee figure (0.40 → 0.50),
  D16 / D91 notes.

### R8P4-ROUTING-02 (Minor, worth fixing): USB_LIMITED's branch to R87.1 doubles back under its own trunk from a 45° wedge at C98.1; a straight T drop is 1.86 mm shorter

**Requirement.**
- AGENTS §3: no acute angles.
- REQUIREMENTS M2: no needless detours, duplicate copper or untidy entries.
- R8_DECISIONS D42 ("Branches go to C86, TP82 and R87.1 (the OVLO divider top)").
- Owner priority 2.

**Finding.**
- `r8_power.py` l. 324 draws the R87.1 branch ('B', 0.25 mm) from C98.1's centre: (35.25, 56.2) → (32.7, 56.2) →
  (32.2, 56.7) → (32.2, 57.775), 4.33 mm.
- The trunk reaches C98.1 on a 45° from (34.35, 55.3). The branch leaves the same node heading west, so it makes a 45°
  wedge with the trunk. That is the board's only R8-new acute branch pair: the other two, R133.1 and Q30.2, are rigid R7
  copper.
- It then runs back west for 2.55 mm, 0.9 mm under the y 55.3 trunk that has just come east (1.65 mm of parallel same-net
  copper, `par.py`), before turning south to R87.1.
- R87.1 lies directly below the trunk at x 32.2, so one vertical T drop, (32.2, 55.3) → (32.2, 57.775), is 2.475 mm.
- Electrically the same node: the OVLO divider would tap the 0.4 mm trunk 3.4 mm upstream of C98.1. At the 0.45 A limit
  that is a few millivolts (Inference: about 4 mΩ of trunk).
- route_check accepts the present wedge: its apex lies 0.037 mm inside C98.1's edge (pad x 34.805–35.705; apex x 34.842).
  The drawing is a fold-back nonetheless.

**Evidence.**
- `p4scan.py` acute_at_node: USB_LIMITED B.Cu (35.25, 56.2) pad C98.1, 45.0°; `rgscan/scan.pyc` acute_at_padvia: the same.
- **Variant `r87`:**
  - DRC 0 / 0 / 0 with parity. check_r8 OK, actuators OK. route_check: no failure; one information instance more,
    width_change_junction at the new T (USB_LIMITED, 0.4 / 0.25 mm), the allowed category C19 lists ("a narrower branch
    leaving a wider trunk at a T").
  - Every USB_LIMITED clearance within 0.6 mm is identical to the board's (`gapnet.py`). B.Cu −1.86 mm. Acute pairs
    3 → 2. R87.1's entry stays axial from the north, to the centre.
- Render: `<s>/img/r87b.svg.png` (board), `<s>/img/r87v.svg.png` (variant).

**Why Minor.** Cosmetic and simplicity only: no clearance or current changes. The trade is one more information instance
(C2's count 90 → 91, a category AGENTS §3 / M2 allows) against a wedge, a corner, 1.86 mm and a doubled run.

**Fix.**
- `r8_power.py` l. 322: ('B', 0.4, [V_USB[1], (32.2, 55.3), (34.35, 55.3), (35.25, 56.2), (35.25, 57.925)]).
- l. 324: ('B', 0.25, [(32.2, 55.3), (32.2, 57.775)]), # R87.1 (OVLO divider top), a T off the trunk.
- Rebuild; step 7 may move a stitching via in the freed B.Cu area. Re-run the gate and the sweep. Update part E /
  C19 (width_change_junction 14 → 15) and D42's branch sentence.

## 9. Notes (no finding)

- **Decision log coordinates:** R8_DECISIONS D33 (l. 859–860: lane x 30.6, R172 (30.6, 48.1)), D37 (l. 956: CAM_PWR_EN
  "x 28.0") and D42 (l. 1065 / 1067: "y 37.25", "x 30.6") still give the pre-fix-3 figures. They carry no pointer to D106 /
  D107, which hold the change, though fix passes elsewhere add a "Correction (fix pass N)" line. A records nit.
- **R8_VALIDATION C14's heading** says "unchanged by fix pass 2"; it is also unchanged by fix pass 3 (same 26 vias and
  arms).
- **0.6 mm signal vias:** see §5.3 (7 R8-new, none with foreign copper within 0.3 mm).
- **CAM_PWR_EN's new run:** nearest foreign copper to the lane > 0.3 mm. R74.1's 0.258 mm to the GND via (31.5, 26.75)
  is pad-to-via and pre-existing.
- **Not re-run:** pass 3's 4-segment redraw search (only CAM_PWR_EN's run changed, and `margin_free` covers it), the DC
  solves and the scorecard (no copper of a power path changed; fix pass 3's evidence stands).

## Appendix: reproduce

```
cd <scratch>/r8p4rt     # ../p8rt/r7.kicad_pcb = c872a3d3…
PY=<KiCad 10.0.6 python3>
cp <repo>/m3_design/assembly_review/m3.kicad_pcb r8.kicad_pcb           # c84f00b8…
# p3.kicad_pcb = 990c8040…: `git show HEAD:m3_design/assembly_review/m3.kicad_pcb` into a/m3_design/assembly_review/,
# then `git apply` the m3.kicad_pcb hunk of ../r8_backup_990c8040/tracked.diff (SHA-256 checked)
KICAD_PY=$PY <repo>/tools/check.sh                                     # exit 0
$PY -I diff4.py p3.kicad_pcb r8.kicad_pcb                              # fix pass 3's copper diff
$PY -I p4scan.py r8.kicad_pcb s4.json; $PY -I p4scan.py p3.kicad_pcb s4_p3.json; python3 sdiff.py s4_p3.json s4.json
$PY -I par.py r8.kicad_pcb 1.5 0.8; $PY -I retap.py r8.kicad_pcb 0.8
$PY -I gapnet.py r8.kicad_pcb 0.3 CAM_PWR_EN,USB_LIMITED,RAW_ACT_SENSE,RAW_ACT_SENSE_MCU
$PY -I cross.py r8.kicad_pcb 23.3 17 27 F.Cu
(cd rgscan && $PY scan.pyc ../r8.kicad_pcb ../../p8rt/r7.kicad_pcb rg.json)
$PY -I <repo>/m3_design/assembly_review/sources/r8_design/step9/m2_sweep.py r8.kicad_pcb --json m2.json
# variants (proj/ = a copy of the project, kilib symlinked)
./vrun.sh base e_base.json; ./vrun.sh fence e_fence.json; ./vrun.sh fence2 e_fence2.json
./vrun.sh r87 e_r87.json; ./vrun.sh rec4 e_rec4.json; python3 rcdiff.py v/base/rc.json v/<name>/rc.json
$PY -I <repo>/m3_design/assembly_review/sources/r8_design/step9/m2_sweep.py v/rec4/m3.kicad_pcb --json logs/rec4.m2.json
```
