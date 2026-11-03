# R8 review pass 2: routing simplicity and geometry (whole board)

Reviewer: independent, read-only. Dimension: the geometry and simplicity of every track and via on all four layers, rigid
R7 copper included. Covered: AGENTS §3 rule instances, staircases, jogs and knees, local bumps, detours and extra vias,
bus tidiness, pad entries, width discipline, layer discipline (no signal on In1 / In2 except D70), adjacency, and, for
every remaining exception, whether a DRC-clean edit removes it. First the four pass-1 routing findings are re-checked,
then the fix-pass-1 copper changes, then the whole board.

- **Board reviewed:** `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
  `6600ef9462b37ec58540e0dd7edd97577c3e778bda0d233d3c1dffc555ad5a8d`. The SHA and `git status` were the same before and
  after this review.
- **Contents:** 794 tracks, 607 vias (426 GND; 314 × 0.6 mm and 293 × 0.5 mm, all 0.3 mm drill), no arcs.
  - F.Cu: 408 tracks, 1,225.7 mm. B.Cu: 385 tracks, 860.9 mm.
  - In2: 1 track, 3.4 mm (ARM1_SENSE at x 14.55, rigid, D70). **In1: none.**
- **Copper identical to R7** (`c872a3d3…`, matched by net, layer, width and end points): 97 tracks and 189 vias. Pass 1
  counted 93 tracks; the four extra are the limiter tracks that fix pass 1 put back on R7's coordinates (DFM-01: GNSS_LNA_EN
  and GNSS_VCC_RF vias at R7's y 8.3).
- **Fix pass 1's copper diff** (`429b6db4…` → `6600ef94…`, my `diff.py`): 44 tracks removed and 41 added, 14 vias removed
  and 13 added, on 15 nets (§4).
- **Gate on this board** (`tools/check.sh`, run by me, exit 0): DRC 0, unconnected 0, parity 0, ERC 0; metadata / 3D OK;
  silkscreen 0; R8 CAD contract OK; route_check "0 failing, 3 allowlisted, … 0 removable local bumps on critical nets (22
  bump windows searched): OK"; actuators OK; fit OK.
- **Tests:** all 17 suites in `tools/` under KiCad's Python, 272 tests, OK.
- **`step9/m2_sweep.py`** re-run by me on a copy of the board: its output equals R8_VALIDATION C11 (23 runs), C12 (32
  pairs), C13 (12 nets), C14 (26 vias), pad_edge 0, and the bumps_all candidate.
- **Repository changes:** none except this file.
- **Scratch:** `<scratch>/r8p2rt/` (the session scratchpad), called `<s>` below. Variant boards were saved only under
  `<s>/v/<name>/`, in a copy of the project, and deleted after their results were logged (`<s>/logs/`).

## 1. Verdict

The R8 routing still reads as deliberate, simple and logical, and fix pass 1 closed every pass-1 routing finding without
breaking that:
- **Segments:** no off-angle segment, arc, zero-length piece, staircase, exposed acute angle, stub, dangling end or via,
  same-net crossing without a node, collinear overlap or unmerged run on new copper. The shortest interior segment of any
  new chain is still 0.566 mm (a 0.4 mm 45° mitre).
- **Buses:** the GNSS river, the radio bus, the servo bus, the pyro corridor, the QSPI / IMU fans and the SWD / USB lanes
  are parallel lanes at constant pitch, nested so that nothing crosses.
- **Width and layers:** every new signal track is 0.2 mm, except the actuator gate family, CAM_FB and the limiter (0.25 mm,
  each consistent within itself). In1 carries no track; In2 carries only D70's rigid 3.4 mm.
- **Records:** my independent scans reproduce C11 (23 chain detours), C12 (32 track / via pairs under 0.2 mm), C14 (26 via
  folds) and E (93 information instances) exactly, number for number.

**No Critical and no Major.** Four Minor findings, all cheap, all worth fixing:

- **R8P2-ROUTING-01.** Four of C12's 0.150 mm pairs open to 0.20 mm by giving an `r8_power.py` via the board's
  0.5 mm size, with the same 0.3 mm drill. Three of the four involve supply nets. This is one argument per via, but the
  record says these gaps are "not cheap to open" and the handoff says "none opens with one table edit". Variant `via5`
  is DRC-clean and gate-clean.
- **R8P2-ROUTING-02.** The 0.5 mm BAT_IN feed threads between R81's pads. It passes 0.170 mm from the GND pad and
  0.180 mm from the BAT_ENABLE pad. BAT_IN is battery-live, with no fuse or current limit on the board, and the board keeps
  every BAT_IN pour 0.3 mm from other nets. Flipping R81 to the west of the EN spine is copper-DRC-clean and gate-clean
  (variant `r81w`).
- **R8P2-ROUTING-03.** The adjacency sweep and C12 leave out track and via gaps to pads, but C12 says only "fine-pitch
  pins" are left out. 23 track/via-to-pad net pairs sit under 0.2 mm, and about 15 are R8 routing choices, not footprint
  geometry, for example:
  - BAT_IN / GND 0.170 mm;
  - PULLPIN / BUZZ_OUT 0.170 mm;
  - USB_LIMITED to R172.2 (U1.34's ADC net) 0.180 mm.
- **R8P2-ROUTING-04.** Fix pass 1 placed C83 0.175 mm off U10.2's row. This left a 0.247 mm diagonal hook inside C83.2 on
  GND, which adds two pad_end_offcentre instances and one segment_inside_pad instance. Moving C83 0.175 mm forward removes
  all three (variant `c83y`, DRC-clean and gate-clean).

None of the four is an AGENTS §3 rule instance, and none is on the armed pyro copper. All four variants combined (`all`)
are copper-DRC-clean, route_check-clean and check_r8-clean; the only DRC items are R81's and R82's designators, which
`r8_post.py` places.

## 2. Method

Every script is in `<s>/` and runs in KiCad 10.0.6's Python with boards loaded read-only. Variants were written only
under `<s>/v/`.

| Script | What it does |
|---|---|
| `diff.py` | Track and via diff between two boards, per net (pass-1 board `429b6db4…` → this board) |
| `p2scan.py` | **My independent scan, written for this pass.**<br>- A node graph per (net, layer) at 1 µm, with node types pad / via / T / end, tracks ending on another track's body, fill-only and dangling ends.<br>- Chains between non-plain nodes, and for each: length against the octilinear distance of its ends (chain detour at > 1.25 × and > 0.5 mm); knees (a return to an earlier heading within four segments, with lateral offset and middle length); U-turns (≥ 179° of same-sense turning); staircases; right-angle, acute and collinear plain nodes; width steps; interior segments < 0.5 mm.<br>- Vias: the layers joined by track, pad or fill; fold-backs (arms on two layers within 45°); off-centre arms; via-to-via tracks; a GND via within 1.5 mm.<br>- Pad entries: offset from the centre, direction against the pad axes.<br>- Per-net widths. R7-identical copper tagged |
| `gaps.py` | Different-net edge gaps under a threshold on each copper layer: track / via against track / via **and against pads** (pad-to-pad pairs skipped), exact segment and polygon distances |
| `threads.py` | Tracks and vias passing between the two pads of any two-pad SMD part |
| `near.py` | Copper and pads around a point |
| `../rg/scan.py` | The earlier reviewers' scan (reused as a cross-check) |
| `variant.py`, `vrun.sh` | Apply an edit list (tracks, vias, footprint moves, designator moves) to a copy of the board in a copy of the project, refill natively, save to `v/<name>/`, then run `kicad-cli pcb drc --severity-all --schematic-parity`, `route_check --profile r8`, `check_r8` and `check_actuators`.<br>Variant `base` (no edit): DRC 0/0/0 and route_check identical to the gate, so the refill reproduces the board |
| `rcdiff.py` | route_check instance diff, full content, base → variant |

I also rendered the whole board in twelve 24 × 20 mm tiles at 40 px/mm, plus close-ups of U1's core and east face, the
GNSS river, the radio leads, the limiter, C83 / U10, C75 / U13, U9 and the band (`rg/render.py`), and read each one.

## 3. Previous findings in this dimension (pass 1)

| Pass 1 | Disposition (R8_VALIDATION) | Checked on `6600ef94…` | Closed? |
|---|---|---|---|
| R8P1-ROUTING-01 HSE_OUT fold | Fixed (D86) | F.Cu (23.0, 52.55) → (23.0, 49.19) → via (24.69, 47.5); B.Cu via → Y1.3 (23.7, 47.5) and via → C26.1 (25.33, 47.5). 7.38 mm (5.75 + 0.99 + 0.64), was 9.27. The F.Cu arm leaves at 135° and the B.Cu arm to Y1.3 at 180°, with no plan overlap. GND via (24.69, 46.25) 1.25 mm away. The via is now a T between the two pads | **Closed** |
| R8P1-ROUTING-02 untidy large-pad entries | Fixed U9.5, C75.2, U9.7 (D94); C75.1 recorded (C18) | U9.5's BAT_IN ends at the pad centre (41.25, 85.5). C75.2's stub starts on its centre row (41.4, 46.07), 0.10 mm off its axis, the via being pinned at x 41.4 (but see R8P2-ROUTING-01). U9.7 ends in its inner rectangle. `m2_sweep pad_edge` and my scan find no track end on a pad edge | **Closed** |
| R8P1-ROUTING-03 VLOGIC sense via 0.6 mm at 0.151 mm from SERVO1_MCU | Fixed (D91): 0.5 mm | Via (26.95, 60.5) 0.5 mm; 0.200 mm to SERVO1_MCU's lane, 0.195 mm to its GND partner (26.6, 61.1) (C12 #30) | **Closed.** The same one-argument fix applies to four more vias (R8P2-ROUTING-01) |
| R8P1-ROUTING-04 via folds unlisted | Fixed in the records (C14; m2_sweep `via_fold`) | My `p2scan` finds the same 26 folds (23 new, 3 rigid), with the same arms, angles and folds as C14, row for row | **Closed** |

## 4. Fix pass 1's copper changes, one by one

| Net | Change | Judgement |
|---|---|---|
| HSE_OUT | Via between Y1.3 and C26.1 | Clean (§3) |
| USB_DM | One 45° run from D4.6's outer end (12.6, 32.85) to (15.39, 35.64), replacing four segments | Clean. Starting the diagonal at the pad centre would pass D4.5 (VBUS) at about 0.04 mm, so the outer-end start is right. segment_inside_pad D4.6 0.45 mm (E) |
| VLOGIC sense | B.Cu (26.95, 60.5) → (32.1, 65.65) → (34.75, 65.65), one 45° run | Clean |
| VLOGIC via | (35.5, 66.6) → (35.65, 66.6), clear of C7.1's paste | A T: the B.Cu runs through to U2 and the F.Cu stub goes into C84.1. Recorded (C14) |
| ACT_GATE | B.Cu (10.9, 104.9) → (10.9, 105.56) → (12.5, 107.16), replacing an L | The chain detour is gone. The 45° run now enters C120.2 through its inner (C120.1-facing) edge, 0.05 mm from that edge's corner, where the old one entered along the pad's row. Tidy by route_check's measure, since it ends at the centre. Note only (§9) |
| BUZZ_DRV | Lane y 60.5 → 60.45, via with it | Clean; opens BUZZ_DRV / PULLPIN to 0.20 mm |
| I2C1_SCL | Exit x 14.45 → 14.243 | Clean; an off-grid coordinate, cosmetic |
| CAM_MCU_RX | Hop via (33.9, 44.0) → (33.95, 44.0) | Clean (E short_layer_hop) |
| GNSS_LNA_EN / GNSS_VCC_RF | Vias back to R7's y 8.3 (paste clear) | A2 / A3 re-measured (7.65 / 6.20 mm); the folds are 1.90 / 0.83 mm (C14). Forced (§7) |
| BAT_IN | U9.5 entry to the pad centre | Clean |
| BAT_DVDT | U9.7 entry into the inner rectangle | Clean |
| GND (C75.2) | Stub from the centre row | Clean |
| VBUS | C83 moved beside U10: (7.95, 36.775) → C83.1 → (10.675, 36.775) → U10.1 (45° into the pad centre) | The diagonal entry into U10.1 was already there before fix pass 1 |
| GND (C83 / U10.2) | Via (9.0, 33.8) → (9.55, 34.35) → C83.2 (9.55, 35.225) → **(9.725, 35.4)** → U10.2 (11.1, 35.4) | **A 0.247 mm diagonal inside C83.2**, from the 0.175 mm offset between C83.2's row and U10.2's: R8P2-ROUTING-04 |
| GND vias | Step 7 re-ran: 7 out, 6 in | Gate-clean; no new adjacency under 0.2 mm except C12's listed ones |

## 5. Whole-board scans

### 5.1 Independent scan (`p2scan.py`; new / rigid)

| Category | New | Rigid | Notes |
|---|---:|---:|---|
| off-angle (> 0.01°) / arcs / zero-length | 0 / 0 / 0 | 0 | |
| interior chain segment < 0.5 mm | **0** | 2 | the shortest new one is 0.566 mm; the rigid ones are TXEN's 0.424 mm mitres |
| same-net crossing without a node / collinear overlap | 0 / 0 | 0 | |
| track ending on a same-net track body (T without a split) | 4 | 2 | 3V3 (36.75, 70.4), 3V3A (26.5, 53.7), CAM_5V (40.75, 43.17), CAM_SW (39.95, 37.61): ordinary T joints, none overlap-only |
| fill-only ends | 1 | 0 | BAT_IN B.Cu (41.25, 102.4) in its own pour (gated by pour_stub) |
| acute corners at plain nodes | 0 | 0 | one 45° pair at a pad, Q30.2, where the wedge lies inside the pad (route_check's rule) |
| right-angle corners | 56 | 3 | allowed by AGENTS §3 (pass 1: 59 + 3) |
| knees (the run returns to its heading) | 57 | 1 | §6.1 (pass 1: 61 + 1) |
| U-turns (≥ 179° of same-sense turning) | 6 | 2 | PYRO1_CONT corridor, 3V3A at U4, CAM_PWR_EN, USB_DM, SPI1_SCK, BAT_ENABLE; rigid TXEN and PYRO1_CONT. route_check's u_turn (its own definition) has 7, all in E |
| chain detours (> 1.25 ×, > 0.5 mm) | 20 | 3 | = C11, run for run |
| via folds | 23 | 3 | = C14 |
| via-to-via tracks | 5 | 1 | 3V3 hop (D40), 3V3A hop (C13), VBUS spine, USB_LIMITED hop (E), rigid ARM1_SENSE In2 (C1), rigid GND 0.9 mm |
| step inside a via's copper / off-centre via arm | 0 | 1 / 1 | ARM1_SENSE (18.18, 91.3), rigid (F) |
| critical-signal via without a GND via within 1.5 mm | 0 | 1 | A1 (PYRO1_GATE, TP122) |
| width step at a plain node | 1 | 0 | CAM_INPUT_LIMITED (35.0, 31.65), at U7.5's neck (E) |
| inner-layer signal | 0 | 1 | C1 |

### 5.2 Adjacency (`gaps.py`, 0.2 mm)

- **Track / via against track / via:** 32 net pairs under 0.2 mm, 14 of them at 0.150 mm. This equals C12, pair for pair
  and value for value.
- **Track / via against a pad** (left out of the sweep, see R8P2-ROUTING-03): 38 (pad, net) pairs under 0.2 mm, 23 net
  pairs not already in C12.
  - My classifier marks 15 of the 38 as a track or via of a net that has a pad on the same footprint, which is close to the
    "fine-pitch pins" C12 means. Examples: CAM_ILIM beside U7.8, SWDIO past U1.73–75's toes at 0.1507 mm, and a part's own
    GND via beside its other pad.
  - The other 23 instances are routing beside a foreign part's pad. 7 of them are rigid R7 copper. The 16 R8-new ones,
    with the 0.17–0.18 mm stitching vias beside small pads counted in, are:

| Gap (mm) | Layer | Pad (net) | Track / via (net) | Note |
|---:|---|---|---|---|
| 0.155 | F | R305.2 (GNSS_TXD_MCU) | fence via (7.685, 23.3) (GND) | the fence row (D16) |
| **0.170** | B | **R81.2 (GND)** | **BAT_IN 0.5 mm feed x 41.25** | threads between R81's pads (R8P2-ROUTING-02) |
| **0.170** | B | **Q123.3 (BUZZ_OUT)** | **PULLPIN lane x 14.23** | the launch-detect input beside the buzzer FET's drain; fix pass 1 opened the BUZZ_DRV / PULLPIN track pair (D91), but not this pad pair |
| 0.171 | B | R162.1 (BUZZ_DRV) | GND via (15.4, 62.8) | stitching (rules + 0.02) |
| 0.174 | F | LS120.2 (BUZZ_OUT) | GND via (15.2, 70.9) | stitching |
| **0.175** | F | **R166.1 (BAT_DAMP)** / R166.2 (GND) | **RAW_PROTECTED y 99.75** | R122's 0.25 mm feed past the damper's pads |
| 0.180 | B | R120.2 (ACT_GATE) | GND via (15.0, 107.3) | stitching |
| **0.180** | B | **R172.2 (RAW_ACT_SENSE_MCU = U1.34)** / R172.1 | **USB_LIMITED 0.4 mm x 29.95** | 5 V beside an MCU ADC pin's net; a bridge puts 5 V straight onto PB0 (U1.34, FT_a, used as an analog input) with no resistor between. That a pin in analog mode is not 5 V tolerant is an Inference from the FT_a class; I did not re-read ST's datasheet |
| **0.180** | B | **Q120.9 (BAT_IN)** | **BAT_ENABLE via (16.6, 104.5)** | the R165 via (D30); a bridge holds U9's EN at the pack voltage (the latch class of the pyro observations table, which does not list this neighbour) |
| 0.180 | B | R81.1 (BAT_ENABLE) | BAT_IN feed | as R81.2 |
| 0.183 | F | R11.2 (3V3) | GND via (10.6, 57.0) | stitching |
| 0.190 | B | Q120.8 (BAT_IN) | GND via (19.6, 104.4) | power-return via |
| 0.197 | F | FB30.2 (3V3_GNSS) | GND via (12.3, 23.3) | fence |

Every one of these is DRC-legal (≥ 0.15 mm), and the track or via in each is tented. A bridge needs a mask breach
(Inference, as C12 judges its own pairs).

### 5.3 Two-pad parts with copper between their pads (`threads.py`)

| Part (pad nets) | Copper between the pads | Smallest gap |
|---|---|---|
| **R81 (BAT_ENABLE / GND)** | **BAT_IN 0.5 mm** | **0.170 mm** (R8P2-ROUTING-02) |
| R82 (BAT_IN / BAT_OVLO) | BAT_ENABLE 0.2 mm (the EN spine, D36) | 0.32 mm |
| R85 (USB_ILIM / GND) | USB_FAULT_N 0.2 mm | 0.225 mm |
| R90 (3V3 / USB_FAULT_N) | USB_FAULT_N, with a T into its own pad | 0.325 mm |
| C84 (VLOGIC / GND; pads 4.3 mm apart) | RAW_PROTECTED 0.4 mm | wide; normal under a large capacitor |
| L3 (CAM_SW / CAM_5V; 2.9 mm apart) | J9.1's CAM_5V via and its 0.8 mm bar | wide |
| C120, FB30, R76, R84, R87, R110 | a diagonal entering one pad across the inter-pad gap's corner (R76: CAM_FAULT_N through R76.2, E) | ≥ 0.2 mm |

D36 records "R82 straddles the feed lane … EN passes under R82's body between its pads, and R81 straddles the feed
lane". Only R81's gap is below the 0.2 mm adjacency convention, and only R81's involves battery-live copper.

### 5.4 Widths, vias and layers

- **Signals:** 0.2 mm. The actuator gate family (ACT_GATE, ACT_EN, ACT_DRV, BAT_SW_*) and CAM_FB are 0.25 mm. Limiter:
  GNSS_VCC_RF 0.25 mm, GNSS_ANT_DC 0.25 / 0.2 mm (rigid). Rigid R7 copper keeps 0.15 mm on RADIO_TXEN and on one
  PYRO1_CONT piece.
- **Power:** follows the D-numbers (RAW_PROTECTED 0.5 mm trunk with 0.25–0.4 mm branches; USB_LIMITED 0.4 mm; VLOGIC
  0.4–0.5 mm; 3V3A 0.3 / 0.25 / 0.2 mm). Width steps occur only at pads, vias and T junctions (E, 14), plus one pad neck.
- **The rigid fire loop:** PYRO1_IGN (R134.1 → J121.2, 10.9 mm) and PYRO1_OUT (J121.1 → Q124, 5.7 mm) are 0.2 mm
  F.Cu, against a 1.0 mm PYRO1_BUS. It is R7's accepted copper; the adiabatic check is in §9.
- **Via sizes:** 0.5 mm (signals, step-7 GND) and 0.6 mm (`r8_power.py`'s default `VIA`, power and some returns), all
  0.3 mm drill. 194 of the 426 GND vias are 0.6 mm.
- **Layers:** In1 has no track; In2 has only D70's rigid 3.4 mm (C1).

## 6. Topic by topic

### 6.1 Knees and jogs

My scan finds no tiny jog: no middle under 0.5 mm, no lateral offset under 0.4 mm. Pass 1's knees under 1 mm lateral
remain, minus HSE_OUT's, which is gone:
- the radio trio RXEN / BUSY / MISO_MCU: 0.40 mm, at the fence slot;
- RADIO_DIO1: 0.45 mm;
- SWCLK: 0.50 mm;
- QSPI_IO3: 0.50 mm;
- RADIO_SCK: 0.60 mm;
- QSPI_IO0: 0.63 mm;
- CAM_MCU_TX: 0.75 mm.

Each was checked in pass 1 against its cause, and QSPI_IO3's is now recorded in C14. My scan's one "staircase" is
CAM_MCU_TX's D56 knee followed by its 90° turn into U12.5: four segments at 1.75 / 1.06 / 1.40 / 1.35 mm, which is not
route_check's staircase (≥ 2 segments under 1 mm). It is the recorded knee.

### 6.2 Folds, detours and extra vias

- **Folds:** C14's 26, confirmed (§3). The new folds since pass 1 are T-junctions: the VLOGIC via, and HSE_OUT's,
  which has no plan overlap.
- **The limiter's GNSS_LNA_EN entry into R303.1** (B.Cu: diagonal to (12.03, 12.18), 0.22 mm inside the pad to its
  centre, 0.37 mm out, diagonal to Q31.1; E segment_inside_pad R303.1 and pad_end_offcentre R303.1) looks like a hook.
  Variant `lim` drew one diagonal into the centre instead. It fails DRC: 0.117 mm to R303.2 (GND), plus a route_check
  tiny jog. The drawn path is therefore the clean one.
- **Chain detours:** C11's 23, confirmed. The redraw search behind "none" uses 1–3 segments with pads and vias fixed.
  I probed the ones on critical nets by hand: QSPI_CLK is held by QSPI_IO3's dive via directly in the diagonal's way, and
  CC2, SERVO1/4 and USB_DP are plain Ls or tees. None has a simpler DRC-clean shape that I could find.
- **Extra vias:** C13's 12 nets, confirmed. No one-layer via, and no via on a same-net track body.

### 6.3 Bus tidiness

Unchanged from pass 1 and still good:
- the GNSS river: four lanes at 0.6 mm pitch, nested Ls with R306 inline in its own lane;
- the radio leads into U31: nested Ls;
- the servo bus: four F.Cu lanes at 0.5 mm pitch with identical 45° turns;
- the pyro corridor: three B.Cu lanes;
- the QSPI dive under U1: one via per net;
- the IMU fan: parallel 45° lanes.

One style note. The radio leads at U31's west row mix 90° corners (RXEN, BUSY, MISO) with 45° chamfers (MOSI, NSS) in one
nested group. This is AGENTS-legal, and each turn is forced by a GND via or R314.

### 6.4 Pad entries

- **Totals:** 551 new pad entries. 53 have a non-axial (45°) track direction, nearly all ending at the pad centre; 31 end
  more than 0.1 mm off-centre on pads up to 2 mm (E's pad_end_offcentre, all recorded).
- **Since pass 1:** new are C83.2's hook (R8P2-ROUTING-04) and ACT_GATE's corner entry into C120.2 (§9). Gone are U9.5,
  C75.2 and U9.7's edge ends.

## 7. Remaining exceptions: does a DRC-clean edit remove them?

| Item | Result |
|---|---|
| A1 (A8, TP122 via) | Rigid CH1 copper; nearest GND via 2.717 mm; not re-probed (D9) |
| A2 / A3 (limiter vias) | Forced: U30_KEEPOUT from y 11.25, the 1.1 mm pad pitch, and U30's paste extension to y 8.6. The vias at R7's y 8.3; folds 1.90 / 0.83 mm |
| C5, C9, C1 | As pass 1 |
| C11 (23 runs) | As §6.2; no simpler clean redraw found |
| **C12 (32 pairs; 14 at 0.150 mm)** | **Four 0.150 mm pairs open with a via-size argument** (variant `via5`, R8P2-ROUTING-01): #1 CAM_5V / GND, #6 CAM_MCU_TX / GND, #10 GND / RAW_PROTECTED (the pair's minimum becomes 0.171 mm, at a step-7 via elsewhere), #13 RAW_PROTECTED / VLOGIC. The other ten are 0.5 mm vias at U1's 0.5 mm pitch, at U4's pitch, at the fence row, or at TP73's zone; I found no cheap edit for them |
| C14 (26 folds) | All forced or T-junctions (§6.2) |
| C18 (C75.1 straddle) | As recorded |
| E (93) | Re-counted equal. C83.2's three instances are removable (variant `c83y`, R8P2-ROUTING-04). R303.1's two are forced (variant `lim` fails DRC) |
| BAT_IN in R81 (not listed) | Removable (variant `r81w`, R8P2-ROUTING-02) |

**Variant results** (`<s>/logs/`):

| Variant | Edit | DRC | route_check | check_r8 / actuators | Effect |
|---|---|---|---|---|---|
| base | none | 0 / 0 / 0 | identical to the gate | OK / OK | the refill reproduces the board |
| via5 | vias (41.4, 47.8), (33.9, 45.2), (41.45, 32.6) GND and (35.25, 60.5) RAW_PROTECTED: 0.6 → 0.5 mm, same position and drill | 0 / 0 / 0 | identical (96 = 96) | OK / OK | C12 pairs at 0.150 mm 14 → 10; pairs under 0.2 mm 32 → 29 |
| r81w | R81 to (39.595, 91.0), rotation 180 (pad 1 stays at (40.42, 91.0) on the EN spine, pad 2 GND to (38.77, 91.0)); step-7 via (39.0, 91.3) → (38.2, 92.0) | copper 0; 1–4 silkscreen items from R81's and R82's designators (R82's spot is taken by R81.2; `r8_post.py` re-places or hides them) | identical | OK / OK | BAT_IN no longer threads a part; BAT_IN / GND 0.170 mm gone (BAT_IN–R81.1 0.18 mm stays); R81.2 1.07 mm from J121.1's edge (rule D 0.5 mm) |
| c83y | C83 to (9.55, 36.175); GND (9.0, 33.8) → (9.55, 34.35) → (9.55, 35.4) → U10.2; VBUS row at y 36.95 through C83.1's centre, 45° into U10.1 | 0 / 0 / 0 | 96 → 93: two pad_end_offcentre C83.2 and the segment_inside_pad C83.2 removed, nothing added | OK / OK | the hook is gone |
| all | via5 + r81w + c83y | copper 0 (silk as r81w) | 96 → 93, as c83y | OK / OK | the edits coexist |
| lim | GNSS_LNA_EN one diagonal into R303.1 | **1**: 0.117 mm to R303.2 | tiny_jog FAIL; A2 out of date | — | the drawn path is forced |

## 8. Findings

### R8P2-ROUTING-01 (Minor, worth fixing): four of C12's 0.150 mm pairs open to 0.20 mm with a one-argument via-size change, contrary to the record

**Requirement.**
- REQUIREMENTS M2 ("adjacency on every net"; every review residual "with … why it cannot reasonably be removed").
- R8_VALIDATION C12 (`docs/R8_VALIDATION.md` l. 223) states that the remaining 0.150 mm pairs are "not cheap to open
  (D91)". `fix1_handoff.md` l. 69 says "none opens with one table edit".
- This is the R7 P8-ROUTING-02 class and the class fix pass 1 fixed for the VLOGIC sense via (R8P1-ROUTING-03, D91).

**Finding.**
- Four C12 pairs at the 0.150 mm DRC minimum each come from a 0.6 mm via that `r8_power.py` draws with its default
  `VIA = (0.6, 0.3)` (l. 46).
- The board's 0.5 mm via has the same 0.3 mm drill. It is the step-7 GND via (D62: "0.5 / 0.3 mm … for every step-7
  via"; 232 GND vias on the board are 0.5 mm) and is already defined in the file as `SMALL_VIA = (0.5, 0.3)` (l. 399).

  | C12 # | Pair | Via (generator line) | Recorded reason | With 0.5 mm |
  |---|---|---|---|---|
  | 1 | CAM_5V / GND | C75.2's GND via (41.4, 47.8), `CAMERA_GND` l. 462 | "pinned at x 41.4 by the RAW_PROTECTED trunk" | 0.20 mm (and 0.20 mm to the trunk) |
  | 6 | CAM_MCU_TX / GND | C76.2's GND via (33.9, 45.2), l. 463 | "TX lifted past C76.2's GND via" | 0.20 mm |
  | 10 | GND / RAW_PROTECTED | R72.2's GND via (41.45, 32.6), l. 476 | "beside the east-edge trunk" | 0.20 mm (the pair's minimum becomes 0.171 mm at step-7 via (42.55, 25.0)) |
  | 13 | RAW_PROTECTED / VLOGIC | U11's IN1 via `V_IN1` (35.25, 60.5), l. 269 / 295 | "U11's pin pitch" | 0.20 mm |

- Three of the four involve supply nets, and #6 is an MCU UART pin. The geometric reasons recorded for them do not hold:
  at the same position, the smaller ring clears.

**Evidence.**
- Variant `via5`: the four vias at 0.5 / 0.3 mm, same centres.
- Result: DRC 0 / 0 / 0 with parity; route_check identical to base (96 instances, 0 failing); check_r8 OK; actuators OK.
- `gaps.py`: C12's 0.150 mm pairs 14 → 10, and pairs under 0.2 mm 32 → 29 (`<s>/logs/via5.gaps.txt`).

**Why Minor.**
- Every gap is DRC-legal and tented, and JLC's electrical test screens etched shorts (Inference).
- The barrel, and so the current capacity, is unchanged. The annular ring falls from 0.15 to 0.10 mm, as on the board's
  293 other 0.5 mm vias.
- Still, it is a cheap, safe edit that the record says does not exist.

**Fix.**
- In `r8_power.py`, pass `SMALL_VIA` for the three `camera()` GND vias (a per-entry size in `CAMERA_GND`, and R72.2's).
- `V_IN1` is a power tap carrying U11's IN1 current. With the same drill it can take `SMALL_VIA` too; or keep it at
  0.6 mm and record why.
- Rebuild (step 7 may move a stitching via near these), re-run the gate and `m2_sweep.py`, and update C12 / D91.

### R8P2-ROUTING-02 (Minor, worth fixing): the battery-live BAT_IN feed threads between R81's pads, 0.170 mm from GND

**Requirement.**
- M2 adjacency; owner priority 2 (a robust design).
- The board's own convention for battery-live copper: every BAT_IN pour keeps 0.3 mm from other nets (zone clearance
  0.300 on F.Cu, B.Cu and In2).
- route_check's redraw rule refuses a path that "threads between the pads of [a] two-pad part".

**Finding** (`r8_place.tsv` l. 148 `R81 41.245 91 0 B D36`; D36):
- The B.Cu BAT_IN feed, 0.5 mm wide, runs (41.25, 94.6) → (41.25, 88.9) through the 0.85 mm gap between R81.1
  (BAT_ENABLE, x 40.42) and R81.2 (GND, x 42.07).
- Its edges are 0.180 mm and 0.170 mm from those pads. This is BAT_IN copper's smallest gap to another net on the board.
  The next smallest are 0.18 / 0.19 mm vias beside Q120.9 / Q120.8.
- BAT_IN is J1.1 itself after the TVS. Nothing on the board limits current before U9's input (netlist: J1.1, D8, C80,
  C89, C95, C96, Q120.5–9, R80, R82, R167, TP80, U9.5).
- **A single bridge:**
  - at R81.2, shorts the pack through board copper;
  - at R81.1, holds U9's EN at the pack voltage, so the switch cannot turn the board off (the latch class of the pyro
    observations table).
- D36 records the straddle, but no deviation row lists it (see R8P2-ROUTING-03).

**Evidence.**
- Variant `r81w`: R81 at (39.595, 91.0), rotation 180, so pad 1 stays on the EN spine at (40.42, 91.0) and pad 2 (GND)
  goes to (38.77, 91.0) in the B.Cu GND pour. The step-7 via (39.0, 91.3) moves to (38.2, 92.0). No track changes.
- Result: copper DRC 0, unconnected 0, parity 0; route_check identical (96, 0 failing); check_r8 OK; actuators OK.
  The remaining DRC items are R81's and R82's designators, which moved with the part or now sit over R81.2's pad;
  `r8_post.py` places designators and AGENTS §3 lets a crowded one be hidden.
- After it, BAT_IN threads no part. BAT_IN / GND at R81 is gone; BAT_IN–R81.1 stays at 0.18 mm.
- R81.2 sits 1.07 mm from J121.1's (PYRO1_OUT) pad edge, against rule D's 0.5 mm.

**Why Minor.** The gap is DRC-legal and the track is tented. A bridge needs a mask breach under the part, so it is
improbable, and JLC's test screens bare-board shorts (Inference). It is still the weakest spot on unfused battery copper,
and one placement row removes it.

**Fix.** Move R81 as in `r81w` (`r8_place.tsv`), rebuild, let `r8_post.py` place R81 / R82's designators, and re-run the
gate. Or keep it and list it in C12 with its reason.

### R8P2-ROUTING-03 (Minor, worth fixing): the adjacency sweep and C12 omit track/via-to-pad gaps, and C12's scope statement is inaccurate

**Requirement.**
- M2: "What review checks: … adjacency on every net". Every review residual must be listed.
- C12's scope (l. 223): "every track and via of the board on every layer; pad-to-track gaps at fine-pitch pins are the
  footprints' and are not listed".
- Part F (l. 357): "Adjacency on every net | different-net track / via pairs on one layer".

**Finding.**
- `step9/m2_sweep.py adjacency` (l. 16, l. 95) compares tracks and vias with tracks and vias only. So every gap to a pad
  is left out, not only the fine-pitch ones.
- `gaps.py` finds 38 (pad, net) pairs under 0.2 mm, which is 23 net pairs not in C12. About 15 of these are R8-new
  routing next to a foreign part's pad (table §5.2), for example:
  - BAT_IN / GND 0.170 mm (R81.2; R8P2-ROUTING-02);
  - PULLPIN / BUZZ_OUT 0.170 mm (Q123.3), the launch-detect input beside the buzzer FET's drain. Fix pass 1 opened the
    BUZZ_DRV / PULLPIN track pair (D91), but not this pad pair;
  - RAW_PROTECTED / BAT_DAMP and / GND 0.175 mm (R166);
  - USB_LIMITED / RAW_ACT_SENSE_MCU 0.180 mm (R172.2, on U1.34 directly, with no series resistor between it and the pin);
  - BAT_ENABLE / BAT_IN 0.180 mm (the R165 via beside Q120.9);
  - SWDIO 0.1507 mm past U1.73–75's toes (VCAP2, GND, 3V3).
- C12's "why it stays" column, the "Pyro review observations" neighbour table (which lists BAT_ENABLE's neighbours but not
  Q120.9) and the owner summary's "32 close net pairs" all rest on the narrower scope.

**Evidence.** `<s>/gaps.py` (exact segment–polygon distances on pads from `TransformShapeToPolygon`, 1 µm), with output in
§5.2, cross-checked against `near.py`. The track / via part reproduces C12's 32 pairs exactly.

**Why Minor.** It is a gap in the record, not a defect in the copper. Every pair is DRC-legal and tented (Inference: a
bridge needs a mask breach). Pass 1's Major was a whole missing category; here the category is present, with a scope that
is stated but wrong.

**Fix.**
- Extend `m2_sweep.py adjacency` to track / via against pad on one layer. Leave out only a track or via that leaves its own
  pad beside a same-footprint neighbour (true fine-pitch escape) and a part's own via beside its other pad, or list those
  as a counted class.
- Add the rows to C12 with reasons, correct the scope sentence and the part F line, and add Q120.9 to the pyro
  observations' BAT_ENABLE row.

### R8P2-ROUTING-04 (Minor, worth fixing): fix pass 1's C83 placement leaves a 0.247 mm hook inside C83.2; a 0.175 mm shift removes it

**Requirement.**
- M2: no micro-segments or tiny jogs, tidy pad entries, inherited and new copper alike.
- Owner priority 2.
- This is a regression of fix pass 1 (POWER-03 / D88).

**Finding.**
- `r8_place.tsv` l. 81 puts C83 at (9.55, 36.0, 90, B), so C83.2's centre is (9.55, 35.225). U10.2 is at (11.1, 35.4).
- `r8_route_usb_swd.py` l. 87 therefore draws GND (11.1, 35.4) → (9.725, 35.4) → **(9.55, 35.225)** → (9.55, 34.35) →
  (9.0, 33.8). The middle piece is a 0.247 mm 45° jog inside C83.2.
- route_check reports it as two pad_end_offcentre C83.2 (0.2475 mm) and one segment_inside_pad C83.2 (0.247 mm). E records
  these, but it is the one micro-jog fix pass 1 added to a critical net. It sits on the D4.2-pocket link (C2), which is
  GND's only track joint there.

**Evidence.**
- Variant `c83y`: C83 at (9.55, 36.175), so C83.2's row is U10.2's (y 35.4).
- GND is redrawn (9.0, 33.8) → (9.55, 34.35) → (9.55, 35.4) → (11.1, 35.4), through C83.2's centre.
- The VBUS spine tee moves to (7.95, 36.95) and the row to y 36.95, through C83.1's centre, then 45° into U10.1 as now.
- Result: DRC 0 / 0 / 0 with parity; route_check 96 → 93 (exactly those three removed, none added); check_r8 OK; actuators
  OK. C83 stays beside U10.1 / U10.2 (D88's intent).

**Why Minor.** It is cosmetic and electrically irrelevant. The 0.175 mm offset comes from C83's 1.55 mm pad pitch against
U10's 0.95 mm, which no rotation removes, but a shift moves the offset onto the VBUS diagonal that already exists.

**Fix.** Apply `c83y` in `r8_place.tsv` (C83 y 36.175) and in `r8_route_usb_swd.py` (`T_U10` y 36.95, the VBUS row, the
GND link and the l. 106 pad table). Rebuild and re-run the gate.

## 9. Notes (no finding)

- **ACT_GATE's new 45° entry into C120.2** (fix pass 1, D91) crosses the pad's inner edge 0.05 mm from its corner, from
  the side facing C120.1 (ACT_FET_S, 0.58 mm away). The old run entered along the pad's row.
  - It ends at the pad centre, so route_check calls it tidy, and the chain detour it replaced is gone.
  - Fix pass 1 reverted CAM_5V's chamfer for "an untidy pad entry". By that standard this one is borderline, but a
    chamfered L that keeps the axial entry (1.16 × octile) would add a bend. Neither shape is clearly better.
- **The rigid fire loop at 0.2 mm** (PYRO1_IGN 10.9 mm, PYRO1_OUT J121.1 → Q124).
  - Adiabatic estimate, 1 oz, 20 ms pulse (Inference): about 16 K at 2.8 A (a 1 Ω igniter behind R134's 2 Ω) and about
    36 K at 4.2 A (a shorted igniter). R134 limits the current; MARGIN_PRESCRIPTION's "treat pyro traces adiabatically"
    applies.
  - It is R7's accepted, hash-asserted CH1 copper. I note it for the pyro and power reviewers, not as a routing item.
- **The camera LDO cluster** (U13 / C75 / C91) carries five recorded instances (C11 #18 and #23, C12 #1, C18, E
  pad_end_offcentre C91.1 0.375 mm).
  - CAM_5V runs under U13's body between its pad columns and between U13.4 and U13.5 to reach C91.1.
  - Only a re-placement (U13 / C91) would clear the cluster. C12 #1 opens with R8P2-ROUTING-01.
- **The radio leads' mixed corner styles** at U31 (§6.3): legal; each turn is forced.
- **The other threadings** (R82, R85, R90; §5.3) are ≥ 0.22 mm. D36 records R82's.

## Appendix: reproduce

```
cd <scratch>/r8p2rt        # copy of 6600ef94… as r8.kicad_pcb; ../p8rt/r7.kicad_pcb = c872a3d3…; ../r8p1rt/r8.kicad_pcb = 429b6db4…
PY=<KiCad 10.0.6 python3>
$PY -I diff.py ../r8p1rt/r8.kicad_pcb r8.kicad_pcb                   # fix pass 1's copper diff
$PY -I p2scan.py r8.kicad_pcb s.json ../p8rt/r7.kicad_pcb            # independent scan (R7-rigid tagging)
$PY -I gaps.py r8.kicad_pcb 0.2 gaps.json                            # track / via / pad adjacency
$PY -I threads.py r8.kicad_pcb ../p8rt/r7.kicad_pcb                  # copper between two-pad parts
$PY -I <repo>/m3_design/assembly_review/sources/r8_design/step9/m2_sweep.py r8.kicad_pcb --json m2.json
# variants: project copy in proj/ (kilib symlinked), then
./vrun.sh base e_base.json; ./vrun.sh via5 e_via5.json; ./vrun.sh r81w e_r81w.json; ./vrun.sh c83y e_c83y.json
./vrun.sh all e_all.json; ./vrun.sh lim e_lim.json; python3 rcdiff.py v/base/rc.json v/<name>/rc.json
```
