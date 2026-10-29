# R9 review pass 1: routing simplicity and geometry (whole board)

Reviewer: independent, read-only. Dimension: the geometry and simplicity of every track and via on all four layers:
AGENTS §3 rule instances, staircases, jogs and multi-segment knees, local bumps, chain detours and extra vias (poured
nets included), bus tidiness, pad entries, width discipline (six widths), layer discipline, the 57 signal vias against
owner decision 4's 70 / 55, and, for every remaining exception, whether a DRC-clean edit removes it.

- **Board reviewed:** `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
  `fc3d5b34a4bfbaecfbcb44bdf8144c87015fc71be7accf48354f23410e8d0f51` (steps 9-10's board). The SHA was the same
  before and after this review. `git status --porcelain` showed the same 111 lines, apart from this new file.
- **Contents** (my scan): 861 tracks, 0 arcs, 579 vias.
  - F.Cu 432 tracks, 1094.96 mm; B.Cu 429 tracks, 755.32 mm; **In1 and In2: no track.**
  - Vias: 343 × 0.5 / 0.3 mm and 236 × 0.6 / 0.3 mm, all through. GND 425 (52 with track arms, 373 stitching);
    non-GND 154: 57 signal layer changes, 25 power layer changes, 24 track-to-pour, 48 pour-only.
  - Signal track 1306.9 mm, 260 bends at plain nodes on signal nets (the scorecard's S1 and S10b, reproduced).
- **Gate:** I ran `tools/check.sh` on the repository board (NUMPY_PY = the cfd venv; GUI session logged in, no shim):
  result in §8.
- **Repository changes:** none except this file. Scratch: `<scratch>/r9review/routing/` (deleted at the end).

## 1. Verdict

**No Critical, no Major, 5 Minor** (R9P1-ROUTING-01 … 05; three worth fixing, all cheap).

- **AGENTS §3 rule instances: none**, measured independently (§4.1): no off-angle segment, acute angle, fold-back,
  staircase, stub, dangling via or dead end; all 18 critical layer changes have a GND via within 1.5 mm (worst 1.391 mm,
  PYRO1_GATE).
- **The board reads as deliberate, simple and logical.** The B-spine partition holds in the copper: RF strip aft, U1
  fanning out on four faces, the CH1 column west, power east. Buses run as parallel lanes (radio and GNSS rivers,
  servo fan, QSPI / IMU escapes, the east-face box band and corridor). The servo fan is exactly mirror-symmetric
  (§5). The local complexity sits where the frozen pin map and the safety rules put it: U1's west knot (IMU, QSPI_IO2,
  LEDs, I2C), U1's interior used as a crossroads (USB_LIMITED, NRST, QSPI_IO3, BUZZ_DRV / PULLPIN), and the
  power_ctl lanes round U9 (BAT_FAULT_N, 75.9 mm). Each of these is recorded with its forcing cause, and my redraw
  trials found no DRC-clean simplification of them.
- **Exceptions with a DRC-clean removing edit** (each tried on a scratch copy: native refill, kicad-cli DRC 0,
  route_check r9 OK):
  - RADIO_TXEN, the only 0.15 mm net, can take the board's 0.2 mm signal width (01).
  - TP120's two in-pad RAW_ACT vias (C18) clear the pad when moved by 0.8 mm and 0.5 mm (02).
  - Several C15 candidate redraws are clean but not simpler (05).
- **Record accuracy:** C6's 0.113 mm "via step" on CC1 is what keeps a 0.22 mm offset jog through that via from being
  classified as a tiny jog (03). Several pad-edge and corner entries are not in C15's pad-edge list (04).

## 2. Method

Every script runs on a scratch copy of the board. Geometry was dumped once with KiCad 10.0.6's Python (read-only) and
analysed in plain Python; variants were made by a pcbnew edit script with native zone refill. A no-op pass of that
script reproduces the board byte for byte (SHA `fc3d5b34…`), so a variant's diff is its edit only.

| Script | What it does |
|---|---|
| `dump.py` | Board → JSON: every track, via (with per-layer flashing), pad (copper polygon per layer), zone fill, edge |
| `scan.py` | **Independent scan.** Angles; node graph per (net, layer), track ends merged at 1 µm and typed pad / via / tee / plain / end. Chains through plain nodes: detour (> 1.25 × octile and > 0.5 mm), U-turns, turns over 90°. Knees: a heading regained after 1-3 middle segments, with middle length and lateral offset. Alternating runs of ≥ 4 segments (staircases). Short interior segments. Acute and fold-back branch pairs at every node. Same-net parallel overlap and slits under 0.1 mm, crossings without a node. Vias: arms per layer, off-centre arms, folds (≤ 45°), kind (signal / power layer change, track-to-pad / pour, pour-only), nearest GND via. Width steps at plain nodes and junctions. Every track end in a pad (offset, depth inside the edge, entry angle, track vs pad width). |
| `cands.py` | Redraw candidates: every window of 2-5 segments that backtracks in x or y, redrawn by 1-2 octilinear segments (catches backtracking inside diagonals, which route_check's Manhattan "turns back" test does not) |
| `edit.py`, `trial.sh` | Apply an edit set (remove / add segments, move / remove vias, move footprints, change a net's width), refill, save; then kicad-cli DRC (`--severity-all`) and route_check r9 on the variant |
| `maskchk.py` | Via hole to every SMD pad's mask opening, with the gate's method (`GetEffectiveShape`, `GetSolderMaskExpansion`) |
| `near.py`, `render.py`, `cy.py` | Copper near a point; matplotlib renders per layer (tiles of the whole board and 3-13 mm zooms); courtyard boxes |
| reused | `tools/route_check.py --profile r9` (also on every variant); the step-10 sweep output `step10_evidence/m2_sweep.txt`; `tools/check.sh` |

The DRC on scratch copies flags only `lib_footprint_issues` (the scratch folder has no library table), which I ignore.
Two seeded variants proved the setup catches real faults: QSPI_IO3 pushed to 0.03 mm from QSPI_IO1's via (3 clearance
errors, plus route_check's acute_angle) and RADIO_TXEN at 0.6 mm (15 errors, shorts and hole clearance).

## 3. Previous findings in this dimension

- **None for R9:** this is R9's first review pass, and step 10 changed no copper (the board SHA equals step 9's).
- **R8:** R8's routing passes ended with none open (pass 5, board `cc044ea0…`). R9 is a clean sheet with no rigid
  copper, so no R8 routing item carries over. The one R8 note that could apply, "rigid R7 copper keeps 0.15 mm on
  RADIO_TXEN", is now a free choice, and it is 01 below.
- **Handed to the review loop by step 10** and dispositioned below:
  - C15's candidate redraws (VLOGIC, SERVO4_MCU, LED_RED, GNSS_ANT_GATE, RADIO_RXEN, USB_DP), its margin-free bump
    candidates (RADIO_SCK_MCU, VLOGIC_SENSE) and its seven chain-detour redraws: §6 and 05.
  - C18, TP120's in-pad vias ("or a review fix", R9_VALIDATION "Open" 2): 02.
  - D-S10-18's three gate observations are gate integrity's, not this dimension's.

## 4. Independent scan, whole board

### 4.1 AGENTS §3 rule instances (gated) and hygiene

| Check | Result |
|---|---|
| Off-angle (> 0.01° off a multiple of 45°), zero-length | 0 / 0 |
| Inner-layer tracks (layer discipline) | 0 |
| Acute branch pairs (0.5-89.5°) or fold-backs at any node, pads and vias included | 0 / 0 |
| Turns sharper than 90° inside a chain | 0 |
| Staircases (alternating runs of ≥ 4 segments with ≥ 2 under 1 mm) | 0 |
| Same-net crossings without a node; parallel same-net overlap or slit under 0.1 mm | 0 / 0 |
| Dangling vias (copper on fewer than two layers) | 0. All 579 vias join ≥ 2 layers through tracks, pads or own-net fill |
| Dead ends | 0. Three runs end in their own pour and lie ≤ 1.0 mm inside it: the RAW bar at (27.6, 86.04) 0.744 mm, RAW_PROTECTED F.Cu (40.2, 80.9) 0.353 mm, BAT_IN B.Cu (20.0, 96.3) 0.313 mm |
| Critical layer changes with a GND via ≤ 1.5 mm (centre to centre) | 18 / 18: GNSS_ANT_DC 0.814, GNSS_LNA_EN 0.743, GNSS_VCC_RF 0.695, HSE_IN 1.000, HSE_OUT 1.250, IMU_CS 1.110, PYRO1_GATE 1.391, QSPI_CLK 1.058, IO0 0.836, IO1 0.781, IO2 1.270, IO3 1.058, NCS 0.770, RADIO_TXEN 0.721 × 2, SPI1_MISO 1.005, MOSI 1.298, SCK 0.960 mm |
| Micro-segments (< 50 µm) | 0. Shortest segments outside a pad or via are the U4 GND T-straps, 0.25 mm |
| Via ends off a via centre | 1: CC1 at (7.85, 32.75), the 0.113 mm step (C6; 03) |
| Neck-downs away from pads | 0. The two plain-node width steps are pad-entry necks within 1 mm of the pad: SW_NODE (40.0, 73.9) 1.0 → 0.4 into U2.5, CAM_INPUT_LIMITED (35.4, 35.65) 1.0 → 0.25 into U7.5 |

### 4.2 Knees, staircase-like runs, U-turns, bumps

- **Knees:** 82 windows where a lane regains its heading after 1-3 middle segments. None meets route_check's tiny-jog
  test: the smallest middle is 0.509 mm, the smallest offset 0.36 mm. The small ones are all forced or recorded:

  | Net (class) | At | Middle / offset (mm) | Cause |
  |---|---|---|---|
  | IMU_INT1 (other) | (11.3, 49.5) | 0.509 / 0.36 | dips round U4's GND pin via (11.75, 49.1), which sits at the IMU body's no-via edge |
  | USB_DM (usb) | (8.15, 33.15) | 0.566 / 0.40 | J3.B7 is at y 33.55 and D4.1 at 33.15; D4 is aligned to DP. Recorded in D-S7-11 |
  | GNSS_ANT_DC (rfif) | (11.3, 6.94) | 0.622 / 0.44 | limiter template (D-S4-03) |
  | GNSS_RXD (rfif) | (8.95, 20.05) | 0.679 / 0.48 | passes between R305 and R307 |
  | QSPI_IO3 (spi) | (19.0, 38.45) | 0.707 / 0.50 | keeps 0.65 mm from QSPI_IO1's via (20.0, 38.9). A straight run is DRC-clean at exactly 0.150 mm (05) |
  | RADIO_NSS / SCK (spi) | (23.45, 25.35) / (24.65, 24.85) | 0.849-0.87 / 0.60-0.615 | group shift onto the MCU-end resistor row (R310 / R313) |
  | QSPI_IO0 (spi) | (20.5, 38.05) | 0.891 / 0.63 | steps round the GND partner (20.5, 39.5) |

  The larger knees are lane shifts that keep buses parallel. Examples: the radio trio's 1.1 mm offset round the
  resistor row (D-S7-04), the corridor's three-lane 0.75 mm jog between OE's via (33.9, 53.4) and the (30.8, 59)
  hole, and RAW_PROTECTED's bypass east of the (42, 59.5) support.
- **Alternating runs (≥ 4 segments, ≤ 1 under 1 mm; route_check's extra_bends, information):** 8, each explained.
  - SWDIO and SWCLK step twice between J3's shell tabs (y ≈ 38.6) and R32 / R33, a parallel two-lane channel into J2.
  - The radio trio and GNSS_RESET_N shift lanes (FB30, then the fence opening).
  - NRST B.Cu runs between U3's pads (E41.44).
  - BUZZ_DRV runs inward.
  - LOGIC_SOURCE_ST and USB_LIMITED make the corridor jog.
- **U-turns:** 7, each forced.
  - RADIO_NRST and RADIO_TXEN: U31's keep-out.
  - SWDIO: aft-face pin, west-edge connector.
  - V3V3_SENSE: 225°, hooked round the 3V3 via (15.2, 53.6) and C14 into R62.2.
  - BAT_FAULT_N: U9.4 is reachable only from +y.
  - USB_DM: J3's DN1 / DN2 join under the connector.
  - PULLPIN_EXT: TP70's 1.0 mm test-pad rule.
- **Bumps:** route_check's bump audit (14 windows on critical nets) and the sweep's all-net audit (21 windows) find
  only VLOGIC_SENSE. My backtracking search (`cands.py`, 137 windows) adds two kinds of window:
  - windows whose redraw crosses other copper, a keep-out or a pad row;
  - QSPI_IO3's one-pitch jog, which route_check's Manhattan "turns back" test cannot see because the backtrack is
    inside a diagonal.

  No new DRC-clean simplification came up (§6).

### 4.3 Detours and vias

- **Chain detours:** my 18 runs over 1.25 × octile and 0.5 mm are exactly the sweep's 18, all on nets without a pour.
  On poured nets: 0 chain detours and 0 hops in series (gate). The largest are recorded and forced:
  - BAT_FAULT_N +10.2 mm, the U-turn round U9's OVLO divider;
  - RADIO_TXEN +9.3 mm, U31's keep-out;
  - SWDIO +5.0 mm;
  - USB_LIMITED +4.6 mm, the corridor;
  - CAM_MCU_TX +3.9 mm;
  - PULLPIN_EXT +3.4 mm;
  - QSPI_IO2 +3.3 mm, the C round the IMU escape vias.
- **57 signal layer-change vias** (S4 done ≤ 70 met, stretch 55 missed by 2), counted independently. They match the
  family budgets of D-S7-19 exactly: qspi_hse 6, imu_baro 10, usb_swd 8, camera 7, status 5, power_ctl 7, servo 4,
  pyro 1, steps 4-6 9.
  - 43 are each the one via a net needs because its pads sit on both layers.
  - The 14 beyond need each have a recorded forcing cause:
    - RADIO_TXEN 2: keep-out loop.
    - CAM_MCU_RX 2: RX/TX crossing at U1 and at U12.
    - CAM_UART_OE 2: the pin-28..31 box walled by the ARM1_SENSE F.Cu lane.
    - NRST 2 extra: the B.Cu dive to J2.3, which is enclosed on F.Cu by J2.1 / J2.5 and SWCLK's entry into J2.4. The
      third NRST via, to the bottom NRST cap, is the one the net needs.
    - ACT_GATE 2: the FET gates sit at opposite corners.
    - BAT_ENABLE, BAT_FAULT_N, LOGIC_SOURCE_ST and VBUS_SENSE, 1 each: box vias, F.Cu test pads, the BAT_IN walls.
  - Reaching 55 would take placement changes (for example the NRST cap moved beside the dive via), not a routing
    edit. I found no removable via.
- **Via folds:** 34, as recorded (C7). They come from top and bottom pads that overlap in plan, which forces the via
  beside both, for example CAM_5V (40.75, 45.4) between J9.1 and L3.2. Test pads whose via must sit west of the pad
  (BAT_FAULT_N at TP85) and J2.3's edge via are the rest.

### 4.4 Widths, layers, pad entries, buses

- **Widths:** exactly six, each with one role.
  - 0.2 mm: signals.
  - 0.25-0.4 mm: rails and branches.
  - 1.0 mm: fire-loop bars, the RAW bar, the buck loops.
  - **0.15 mm: one net only, RADIO_TXEN** (7 segments, 25.17 mm; 01).
  - Multi-width nets are power nets with maker-layout branches (CAM_5V has five widths; RAW_PROTECTED, VLOGIC, GND)
    or pyro bars with 0.2 mm sense taps.
  - Five tracks are wider than the pad they enter, all maker or power layouts: U2.4 GND 1.0 mm (Diodes DS41326),
    U8.3 1.0 mm, U7.4 0.4 mm, U11.12 0.4 mm, Q124.5's drain 1.0 mm.
- **Layers:** no inner-layer track. B.Cu carries the power spine, the bottom parts' links and the interior crossings.
  Under U31 only GND (R-8); in the strip, B.Cu holds only the limiter nets and TXEN (R-2).
- **Pad entries (671 track ends in pads):**
  - Axial entries dominate.
  - Entries into fine-pitch pads (pitch ≤ 0.65 mm: U1, U4, U7, U9, U11, U12, J3, Q124, D31) that are not axial take one
    of two forms:
    - same-net pin-to-pin straps: U4.2 / 3, U4.6 / 7, U11.3 / 4, U7.3 / 4;
    - exits from row-end or corner pins: U1.100, U4.1 / 4 / 8 / 12, U11.6 / 9 / 12, U12.1 / 4 / 5 / 8.
  - No lane passes between two foreign pins. The closest same-part neighbours are the normal escape gaps of 0.15-0.25 mm.
  - Ends within 0.08 mm of a pad edge are listed in 04. Most are cosmetic; R173.1 and J2 are deliberate.
- **Bus pitch** (140 parallel different-net pairs, overlap > 1 mm, pitch ≤ 1.2 mm): 0.5 mm (40 pairs) and 1.0 mm (26)
  dominate. Irregular pitches all have a cause:
  - GNSS river: TXD_MCU to RXD 1.138 mm against RXD to TP_MCU 0.453 mm, with a GND via (10.75, 25.75) between.
  - Radio bus north of the resistors: 1.1 / 0.45 / 0.6 mm, with grid via (23.05, 17.4) between MISO_MCU and MOSI.
  - Corridor: 0.4 mm, then 0.35 / 0.4 mm after its corner, squeezed past C92.2 at 0.150 mm.

  These are cosmetic and need no change.

## 5. The board read area by area

Tiles of 23 × 17 mm on F.Cu and B.Cu, plus zooms.

- **RF strip (y 0-22):**
  - Short straight RF lines; the fence with its four lane openings.
  - The GNSS limiter on B.Cu under U30.
  - The radio bus in nested Ls off U31's west pads.
  - TXEN's loop round U31's west side.
  - GNSS_RESET_N's two steps round FB30 to its fence opening.
  - Tidy, template-regular.
- **Interface field (y 22-37):**
  - The GNSS river is three parallel diagonals; RXD and TP_MCU jog together through R306's row.
  - The radio trio offsets 1.1 mm round the MCU-end resistor row, symmetric and parallel.
  - DIO1 and RADIO_NRST share the x 33.15 / 33.65 line as outer fan lanes.
  - USB DM / DP on F.Cu with the standard under-connector U, and the VBUS tree on B.Cu.
- **U1:**
  - Aft face: the QSPI fan, staggered vias with a central GND partner.
  - West face: SPI and NCS turn inward and IMU_CS / BOOT0 outward at 45° to their vias. I2C is a parallel pair, and
    the SWD lanes run as a parallel two-lane channel to J2.
  - Forward face: the servo fan (next item) and the pyro lanes leave on parallel 45° lines: GATE_N with its GND
    guard at a uniform 1.24 mm, then CONT.
  - East face: nested Ls; the pin-28..31 box drops to a via column at x 26.75 into the B.Cu band.
  - Interior: NRST, USB_LIMITED and QSPI_IO3 run on parallel 45° lines. This is the board's busiest place but reads
    ordered.
- **Servo header:** exactly mirror-symmetric fan. S1 / S4 and S2 / S3 are mirror pairs. The 1 k parts are on the plug
  columns and the vias in the column gaps, the OUT lanes run straight into J122, and the B.Cu links to D121 and the
  pull-downs are planar. The best-looking block on the board.
- **CH1 column:**
  - 1.0 mm bars on the terminals' pin lines; the drain trunk with its 0.2 mm sense T.
  - The gate run with one via; the CONT column; ARM1_SENSE straight 40 mm on F.Cu.
  - Deliberate. The one visual oddity, PYRO1_OUT grazing R173.1, is the rule-C clearance of D-S5-09.
- **East column:**
  - The RAW_ACT field: a regular 1.8 mm grid, a row and two columns round Q121's drain.
  - TP120 overlaps that row's north-west corner (02).
  - RAW_PROTECTED on F.Cu bypasses the mid support; the U9 / U11 lanes are dense but square.
  - BAT_FAULT_N's loop is the board's longest and least elegant lane (75.9 mm, two vias, a U-turn). Its cause is
    recorded (FLT reachable only from +y; no F.Cu lane past the RAW_PROTECTED pour to the test-pad column).

## 6. Every remaining exception: does a DRC-clean edit remove it?

Variants: one edit set each on a scratch copy, refilled. "DRC 0" excludes `lib_footprint_issues`; route_check
is profile r9.

| Item (record) | Edit tried | Result | Disposition |
|---|---|---|---|
| RADIO_TXEN 0.15 mm, the sixth width (not recorded) | width 0.2 mm (`txen020`) | DRC 0, route_check unchanged; nearest gap 0.175 → 0.150 mm (GND grid via (24.7, 10.45)) | **01**: clean |
| same | width 0.2 mm and that grid via 0.05 mm west to (24.65, 10.45) (`txen020v`) | DRC 0, route_check OK; nearest gap 0.200 mm (better than today's 0.175) | **01**: recommended |
| C18 TP120's in-pad RAW_ACT vias | vias (29.6, 78.2) → (29.6, 77.4) and (31.0, 78.2) → (31.5, 78.2) (`tp120v2`) | DRC 0, route_check OK, nearest via hole 0.101 mm from TP120's opening (gate method), RAW_ACT stays 32 vias | **02**: clean |
| same | remove (29.6, 78.2), move (31.0, 78.2) → (31.5, 78.2) (`tp120v`) | DRC 0, route_check OK, 31 vias | 02: alternative |
| same | move TP120 instead: (33.8, 74.6), (33.5, 74.4), (34.0, 74.1) | courtyard overlap with C84 (F.CrtYd x 31.45-42.54, y 73.66-87.34) | rejected |
| same | TP120 to (30.2, 75.75) / (30.3, 75.8) | 0.82 / 0.92 mm to ARM1_SENSE against the 1.0 mm bare-test-pad rule, and a GND F.Cu island | rejected |
| C6 CC1 via step | B.Cu straight from the via centre (`cc1straight`) | DRC 0, but route_check: **FAIL tiny_jog CC1 F.Cu (7.55, 33.05)**, an unrecorded leftover | **03**: the step hides a 0.22 mm jog |
| same | via 0.15 mm north, R7 moved (`cc1b`, `cc1c`) | J3.B8 0.112 mm | rejected |
| same | via (8.1, 32.55), R7 moved (`cc1d`) | D4.1 0.122 mm, hole 0.222 mm | rejected |
| C15 GNSS_ANT_GATE chain detour | (8.05, 10.9) → (8.05, 11.5) → (9.6, 13.05) (`antgate`) | DRC 0, OK; 0.9 mm shorter, 90° → 45°, the 0.150 mm gap to GND via (8.5, 13.6) widens | 05: optional |
| C15 VLOGIC_SENSE bump | (21.0, 45.6) → (21.7, 46.3) → (24.05, 46.3) → (24.8, 45.55) (`vsense`) | DRC 0, OK; 0.54 mm shorter, square 0.825 mm step → 45° (same bend count) | 05: optional |
| C15 LED_RED | 5 → 3 segments (`ledred`) | DRC 0, OK; −2 bends, but a diagonal entry into R32.1 replaces today's axial one | 05: keep |
| C15 VLOGIC B.Cu L | east-diagonal-south (`vlogicL`) | DRC 0, OK; +2 pad-end-off-centre, −1 passes-through | 05: keep |
| C15 SERVO4_MCU, RADIO_RXEN, USB_DP; margin-free RADIO_SCK_MCU, CAM_MCU_TX | as listed in `m2_sweep.txt` | each adds a sub-0.1 mm segment, extra bends, a diagonal pad entry or a minimum-clearance pass | 05: keep |
| QSPI_IO3 one-pitch jog (not recorded) | straight x 19.5 into the same diagonal (`io3straight`) | DRC 0, OK; −2 bends, 0.414 mm shorter, but 0.150 mm from QSPI_IO1's via (Y1 +1) | 05: keep; trade-off |
| C100.1 / U12.3: two 3V3 tracks offset 0.055 mm through one pad | one straight track x 34.975 from (34.975, 41.08) into U12.3 (`c100`) | DRC 0, OK; pad-end-off-centre 64 → 62 | 04: optional |
| C3 S8 / S9 (TXEN; RAW_ACT_SENSE_MCU) | — (geometry only, not trialled) | TXEN: keep-out. RAW_ACT_SENSE_MCU: a via on U1.34's line (y 46.5) over R172.2 would put its hole inside R172.2's opening (edge y 46.37), so the via sits east at x 26.95 and folds back | keep |
| C4 S10b 260 | — | the clean edits above change it by ≤ 2 | keep |
| C5 adjacency, C7 via folds | — | forced (§4.3, §4.4) | keep |
| C11d S4 57 | — | no removable via (§4.3) | keep |
| C16 USB_LIMITED through U1 | — | no all-B.Cu route under 1.6 × MST (D-S7-16's search, 89-96 mm); none found here | keep |
| E information instances (114) | — | each read; none is a rule instance | keep |

## 7. Findings

### R9P1-ROUTING-01 (Minor, worth fixing): RADIO_TXEN is the board's only 0.15 mm track; 0.2 mm is clean

- **Requirement:** REQUIREMENTS M2 / owner priority 2 (width discipline; r9_plan §1 "six track widths"); AGENTS §3
  clean routing.
- **Evidence:**
  - `m3_design/r9_rf.py:51` sets `W_TXEN = 0.15`, used at lines 175-178.
  - All 7 RADIO_TXEN segments (25.17 mm) are 0.15 mm; no other net uses 0.15 mm
    (`m3_design/r9_route.py:47`: `WIDTHS = (0.15, 0.2, 0.25, 0.3, 0.4, 1.0)`).
  - R8 kept it as rigid R7 copper (R8 pass 1-5 routing notes); R9 regenerates the loop, and no R9 decision gives a
    reason for 0.15 mm (D-S4-06 covers the loop, not its width).
  - At 0.15 mm the nearest foreign copper is 0.175 mm (GND grid via (24.7, 10.45), B.Cu).
- **Trial:**
  - TXEN at 0.2 mm: kicad-cli DRC 0, route_check r9 unchanged; the nearest gap becomes the 0.150 mm minimum.
  - Also moving that one grid via 0.05 mm to (24.65, 10.45): DRC 0, route_check OK, TXEN's nearest gap **0.200 mm**
    to vias (24.65, 10.45), (28.94, 7.2) and (25.8, 17.6).
  - check_r9 R-2 limits TXEN's B.Cu length (22.72 mm), not its width.
- **Fix:**
  - `W_TXEN = W_SIG` (0.2) in `r9_rf.py`.
  - Move that grid via 0.05 mm west in `r9_rf.GRID`.
  - Drop 0.15 from `r9_route.WIDTHS` and D-S5-08's width list (X5 = 5).
  - Re-run R-7 (stitching gaps; a 0.05 mm move is negligible, Inference).

### R9P1-ROUTING-02 (Minor, worth fixing): TP120's two in-pad RAW_ACT vias (C18) can be moved out of the pad

- **Requirement:** REQUIREMENTS M2 (via holes ≥ 0.1 mm from pad openings; the bare-contact exception) and ORDERING §3 /
  §4 (an expected DFM query). R9_VALIDATION "Open" 2 offers the owner "C18, or a review fix".
- **Evidence:**
  - `m3_design/r9_power.py:73` places TP120 at (30.2, 78.4) (1.5 mm square, F.Cu).
  - `r9_power.py:287` puts the RAW_ACT via row on y 78.2, x 29.6 / 31.0 / … (Q121's drain row).
  - Via (29.6, 78.2) lies inside the pad; via (31.0, 78.2)'s hole crosses its east edge. maskchk: hole-to-opening 0.0.
- **Trial (scratch, refilled):**
  - Move (29.6, 78.2) → (29.6, 77.4) and (31.0, 78.2) → (31.5, 78.2).
  - Result: DRC 0, route_check r9 OK. The nearest via hole is **0.101 mm** from TP120's opening (the gate's
    `vias_in_smd_pads` geometry), so neither via is in the pad any more. RAW_ACT keeps 32 vias.
  - Removing the first instead of moving it is also clean (31 vias).
  - Moving TP120 fails: C84's courtyard to the east; the 1.0 mm test-pad rule to the ARM1_SENSE lane and a GND island
    to the west.
- **Fix:**
  - Edit the two entries in `RAW_ACT_VIAS` (r9_power.py).
  - Re-run the 0.05 mm RAW_ACT DC solve: the vias stay in the same row and column, so the change should be negligible
    (Inference).
  - Drop the C18 exception from M2, ORDERING and R9_VALIDATION.

### R9P1-ROUTING-03 (Minor, worth fixing, record): C6's 0.113 mm CC1 "via step" hides a 0.22 mm jog through the via

- **Requirement:** REQUIREMENTS M2 ("steps inside a via's copper", "tiny jogs", every review-only residual listed with
  its measured reason); the deviation list must describe each item accurately.
- **Evidence:** CC1's F.Cu path from J3.A5 runs east at y 33.05, then a 0.424 mm 45° run to via (7.85, 32.75). On B.Cu a
  0.113 mm segment inside the via ring ends at (7.93, 32.83), and the run goes east at y 32.83 to R7.1. The lane line
  moves 0.22 mm (33.05 → 32.83) across a 0.424 mm diagonal at the via: a tiny jog by route_check's thresholds
  (< 0.5 mm middle, < 0.25 mm offset).
- **Why it does not show:** route_check's through-node test (`tools/route_check.py`, "jogs and staircases through T,
  via and pad nodes", about lines 1921-1946) looks for a branch Q that leaves the via node on P's heading.
  - At CC1's via, the only B.Cu branch at the centre is the 0.113 mm segment. It heads 45°, not east, so it fails as
    Q; as a middle segment it is skipped as via copper (`inside_one`).
  - The east run starts at a separate node 0.113 mm off-centre.
  - So the test finds no hit.
  - Variant `cc1straight` (B.Cu straight east from the via centre, everything else equal): route_check r9 fails with
    "non-critical leftover without a recorded reason: tiny_jog CC1 F.Cu (7.55, 33.05)".
- **Alternatives tried:** none clean.
  - Via 0.15 mm north with R7 moved: 0.112 mm to J3.B8.
  - Via at (8.1, 32.55): 0.122 mm to D4.1, hole 0.222 mm.

  The CC1 via is boxed by J3's pads, USB_DM's jog and D4.
- **Fix (record only, cheap):** say in R9_VALIDATION C6 (and the sweep note of D-S10-12) that the step stands for a
  0.22 mm offset jog through the via on CC1. CC1 is a non-critical CC pull-down. No DRC-clean straight alternative
  exists in the J3 / D4 pocket (variants above), and the owner accepts it as such.

### R9P1-ROUTING-04 (Minor): pad-edge and corner entries missing from C15's pad-edge list

- **Requirement:** REQUIREMENTS M2 ("untidy pad entries"; review-only residuals listed with location and reason).
- **Evidence:** C15 lists "pad-edge track ends 5 at 3 pads (C24.2, R102.1, R172.2; 0.013-0.025 mm inside the
  edge)". With a 0.08 mm depth threshold, plus corner entries, these are also present. All are connected and
  DRC-clean.
  - **C100.1 (3V3, F.Cu):** the feed down x 34.975 ends 0.055 mm inside the pad's east edge, and a second 3V3 track
    leaves the same pad 0.055 mm to the west (x 34.92) into U12.3. One straight segment x 34.975 from (34.975, 41.08)
    into U12.3 is clean (variant `c100`: DRC 0, route_check OK, pad-end-off-centre 64 → 62).
  - **R162.2 (BUZZ_G, B.Cu):** R163.1's lead comes straight down x 26.6 and ends at (26.6, 25.6), 0.067 mm inside the
    pad's west edge, a corner graze. A second lead enters at y 25.95.
  - **TP90.1 (CAM_IO_3V3, F.Cu):** via (34.6, 57.4) is placed north of the pad's NE corner. The lead enters the exact
    corner (34.6, 57.9), then runs a 1.061 mm diagonal inside the pad to its centre. The via is pushed east by the
    B.Cu corridor lanes at x 33.07-33.87.
  - **C91.1 (CAM_5V, B.Cu):** a 0.4 mm lead ends in the pad's NW corner (40.2, 52.65), 0.805 mm off centre.
  - **Others:** C300.1 0.04 mm, C94.1 0.05 mm, L3.1 (CAM_SW) 0.04 mm, U9.9 0.05 mm (a fine-pitch pad end).
  - **Deliberate:** R173.1 (PYRO1_OUT, 0.053 mm: the D-S5-09 / rule-C offset) and J2's five 0.075 mm outer-half ends
    (the TC2030 keep-out, D-S7-11). Both are recorded.
- **Fix:** list them in C15 with their reasons; optionally tidy C100 / U12.3 as tried. Not worth a fix pass on its own
  (cosmetic, no electrical effect).

### R9P1-ROUTING-05 (Minor): the C15 candidate redraws reviewed; none is materially simpler

- **Requirement:** REQUIREMENTS M2 (review-only residuals dispositioned); the step-10 record hands these to the review
  loop.
- **Evidence:** §6 table, each variant on a scratch copy with DRC and route_check.
  - **Clean but marginal:** GNSS_ANT_GATE (0.9 mm shorter, one 90° corner becomes 45°) and VLOGIC_SENSE (0.54 mm
    shorter, same bend count).
  - **Clean but worse elsewhere:** LED_RED (diagonal pad entry), VLOGIC (+2 pad-end-off-centre) and QSPI_IO3's
    one-pitch jog (removing it puts IO3 0.150 mm from IO1's via).
  - **Not clean as proposed:** SERVO4_MCU, RADIO_RXEN, USB_DP, CAM_MCU_TX and RADIO_SCK_MCU (sub-0.1 mm segments,
    extra bends, diagonal pad entries or minimum-clearance passes).
- **Fix:** record in C15 that pass 1 reviewed these and keeps them. Optionally take GNSS_ANT_GATE's redraw, which is
  shorter and widens a 0.150 mm gap. Not worth a fix pass on its own.

## 8. Gate run and repository state

- `NUMPY_PY=<cfd venv> tools/check.sh` on the repository board (4 min 53 s): **exit 0**.
  - DRC 0, unconnected 0, parity 0, ERC 0; metadata / 3D OK; silkscreen 0; fit OK; rule-H seeded suite OK.
  - R9 CAD contract OK; actuator contract OK.
  - routing hygiene "0 failing, 0 allowlisted, … 0 leftovers … (14 bump windows searched): OK".
- Its `route.json` instances equal step 10's `step10_evidence/gate/route.json` exactly: 114 instances, the same detour
  baseline. My own route_check run on the scratch copy gave the same 114. So nothing has regressed since step 10.
- Board SHA-256 before and after: `fc3d5b34…` (unchanged). `git status --porcelain`: the same 111 lines before and
  after, plus this file.
- Scratch copies and variants were deleted at the end.
