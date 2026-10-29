# R8 pass 2: RF layout, interface buses and coexistence review

Independent read-only review, 2026-10-19, of `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
`6600ef9462b37ec58540e0dd7edd97577c3e778bda0d233d3c1dffc555ad5a8d` (checked before and after this review, unchanged),
netlist `schematic.net.xml` `0cc1ed69…` (unchanged since pass 1). Dimension: RF (REQUIREMENTS F10, the RF parts of
M1 / M2 / P3, the rigid strip and its hashes, the U1-to-strip interface buses, F10's 5 mm separation, GND vias at layer
changes, the fence, coexistence paths and the reset states of the radio and GNSS lines). Vehicle-level choices and
firmware are out of scope. Every before/after comparison used the R7 board (`git show 431025d:…/m3.kicad_pcb`,
`c872a3d3…`), copied into the session scratchpad.

Coordinates: KiCad mm, y = 0 at the aft (SMA) edge.

## 1. Summary

**No Critical. No Major. One Minor (R8P2-RF-01, documentation, not worth fixing).**

- **Pass 1's RF findings are all closed:**
  - RF-01: the radio-bus finger is gone (trim G7).
  - RF-02: the R7 pass-4 note and rows C15 / C16 exist and match the board.
  - RF-03 / RF-04: the ORDERING §5 RF steps now probe PE9 / R311 / R312 and run the GNSS with the camera on.
- **Fix pass 1 changed four things in or near the RF area. None regressed RF:**
  - the limiter vias went back to R7's spot (D87);
  - trim G7 (D90);
  - the CAM_MCU_RX hop via moved 0.05 mm (D91);
  - USB_DM was redrawn (D91).
- **The rigid strip is R7's.** All 12 digests are equal to the R7 baseline. I recomputed them on both boards with
  `check_r8.rigid`, and the baseline constants reproduce on R7 itself. An independent item diff of y < 23.5 against R7
  shows only the classes D11 / D15 allow: the fence row, interface leads, limiter DC copper, feeds, the In2 zone and
  trim G5.
- **Unchanged from pass 1, and verified again:**
  - the 12 interface nets run on F.Cu over In1 GND, with no via;
  - the fence has 25 vias and 14 crossings, all on F.Cu; the widest opening is 2.60 mm;
  - F10's 5 mm separation holds (5.94 mm to a part, 5.075 mm to a fast line);
  - all 5 RF-family layer changes have a GND via within 1.011–1.221 mm;
  - every reset and bootloader state holds the radio in reset.

## 2. Previous pass in this dimension: closure

| Pass 1 finding | Fix pass 1 disposition | On `6600ef94…` |
|---|---|---|
| R8P1-RF-01 (Minor): unstitched 0.535 mm F.Cu GND finger between RADIO_NSS and RADIO_SCK, 15.06 mm from a GND via | Fixed: `step7/make_ground.py` trim R8_POUR_TRIM_G7 (D90) | **Closed.** G7 is F.Cu only, a fill-only rule area, outline (31.65, 38.722)–(32.25, 38.722)–(32.25, 37.85)–(25.1, 30.7)–(25.1, 30.3)–(23.228, 30.3), on the two lanes' centre lines. `route_check.pour_pieces` at FINGER_W 0.75 / 1.0 mm finds no GND piece between the lanes (6 / 14 pieces board-wide, none in the strip or the radio bus; pass 1 7 / 15). F.Cu GND reach in the bus region (y 28.5–50) is now 9.11 mm at (41.68, 41.93), by U12, 8 mm east of every RF lane (pass 1: 15.06 mm in the finger). No pad lost pour contact (DRC 0, `r8_ground_check` trims gate in the build). |
| R8P1-RF-02 (Minor): R7 pass-4 RF dispositions not carried into the R8 record | Fixed (records): R8_VALIDATION "R7 pass-4 RF items on R8", C15, C16 | **Closed.** Note at R8_VALIDATION l. 362–372. P4-RF-01 is open as C15 (gate method 6 / 14, re-measured here: equal). P4-RF-02 is closed in part. F.Cu GND under U31 is 79.771 mm² and under U30 75.679 mm², both equal to R7 (re-measured here). P4-RF-03 is closed on the copper, with C16 for D30.2 / D31.2. The optional module-ground gate extension was not added, with a reason: the rigid `strip_gnd` / `strip_parts` / `strip_gcpw` digests cover it. I accept that reason. |
| R8P1-RF-03 (Minor): radio-reset bench step probed PD9 | Fixed: ORDERING §5 | **Closed.** ORDERING l. 161 says PE9 (U1.39), RADIO_NRST at R311.1 < 0.66 V and RADIO_RXEN at R312.1 low, and repeats the check in the ROM bootloader after D6.8's preparation. No R7 pin name is left in ORDERING (grep for PC8 / PD10 / PD14 / PD15 / PE15 / PB10–PB13: no hit). |
| R8P1-RF-04 (Minor): coexistence step never ran the GNSS with the camera supply on | Fixed: ORDERING §5 | **Closed.** ORDERING l. 164 logs C/N0 in three conditions: radio idle with the MCU at flight clock writing QSPI and the camera powered; then radio keyed with the camera on; and the change from a camera-off run. |

## 3. Measurements on the final board

### 3.1 Rigid strip and its hashes

- `tools/check.sh` (run in this review): exit 0.
  - DRC 0 at every severity; unconnected 0; parity 0; ERC 0.
  - Audit OK; silkscreen OK; `check_r8` OK.
  - route_check r8: 0 failing, 3 allowlisted (A8, A2, A3), 0 leftovers.
  - Actuators OK; fit OK.
- `tools/test_r8_check.py`: 23 tests OK.
- **Rigid digests, computed independently** (`rigid7.py` imports `check_r8.rigid`): all 12 groups equal
  `RIGID_BASELINE` on R7 (`c872a3d3…`) and on R8. So the baseline really is R7's, and R8 matches it:

  | Group | Items | Digest (first 16) |
  |---|---|---|
  | `strip_parts` | 22 | `c71c1250c4f732ae` |
  | `strip_rf_copper` | 11 | `7a2598349ad81c5f` |
  | `strip_gnd` | 176 | `bfcbe417a3b45e12` |
  | `strip_rule_areas` | 5 | `d105af8bf59da746` |
  | `strip_gcpw` | 8 | `8b46f56919611ca6` |

  The other seven groups (outline, holes, J122 tie, J1, PYRO_BLOCK, CH1 parts and copper) are also equal.
- **Other `check_r8` evidence on this board:**
  - line stitching: GNSS west 3.90, east 2.65, radio 1.55 / 1.55 mm; In1 missing under RF copper 0.0 mm²;
  - launches: In2 1025 / 1025 samples each;
  - module ground: U31 In1 / In2 2601 / 2601, U30 In1 1976 / 1976;
  - RF GND pads 0.16 mm from a GND via (D30.2, D31.2, C303.2, C305.2, C313.2, C314.2);
  - strip GND reach: F.Cu 3.04, B.Cu 3.49 mm.
- **Item diff, y < 23.5, R7 → R8** (`stripdiff.py`: tracks, vias, footprints with pad nets and zone connections, zone
  outlines). 84 items removed and 84 added. Pass 1 counted 88 / 88: the limiter vias are now at R7's spot, and
  GNSS_VCC_RF's copper is now byte-equal to R7's. Every difference is in one of these classes:
  - **fence row:** 22 vias (0.6 / 0.3 mm) became 25 (0.5 / 0.3 mm) on y 23.3;
  - **interface leads** (RXEN, BUSY, MISO, MOSI, NSS, SCK, NRST, DIO1, GNSS TXD / RXD / TP / TIMEPULSE / RESET_N), all on
    F.Cu. NSS's and DIO1's B.Cu hops and their three vias are gone. GNSS_SAFEBOOT_N gains a 45° tail into TP30's centre;
  - **limiter:**
    - the two vias stay at R7's (11.51, 8.3) / (10.41, 8.3) but shrink from 0.6 to 0.5 mm;
    - GNSS_LNA_EN's B.Cu path is redrawn to R303.1's centre;
    - GNSS_ANT_SRC has a 0.03 mm end shift;
  - **parts:** R310 left the strip (D4); C300 moved 0.08 mm, R305 0.13 mm and R312 0.25 mm;
  - **feeds:** the 3V3_RADIO run R7's R310 needed is gone; the FB31 3V3 stub is 0.2 mm shorter;
  - **zones:** `R7_GND_In2_strip` became `R8_GND_In2`; `R7_POUR_TRIM_9` became `R8_POUR_TRIM_G5`.

  No RF track, RF-chain part, strip GND via (fence row excepted), module keep-out or launch cut-out differs.
- **GND fill XOR, R7 → R8** (`fillxor.py`, mm², R7 → R8 (lost / gained)):

  | Region | F.Cu | In1 | In2 | B.Cu |
  |---|---|---|---|---|
  | U31 body (24.86–34.86, 9–19) | 79.771 = | 100.000 = | 100.000 = | 100.000 = |
  | U30 body (5.56–15.26, 9.9–20) | 75.679 = | 97.970 = | 97.970 = | 77.120 → 77.139 (−0.128 / +0.147, limiter path) |
  | Radio line zone (28–36, 0–10) | 55.167 = | 67.820 = | 75.205 → 75.204 | 75.393 = |
  | GNSS line zone (10–17, 0–11) | +0.202 | +0.279 | +0.276 | +0.205 (smaller limiter-via antipads) |
  | Whole strip (y < 23.5) | 805.7 → 810.6 (−12.1 / +17.0) | +2.69, nothing lost | +2.69 (−0.003) | +3.87 (−0.128) |

  - **F.Cu losses in the strip** (11 pieces > 0.1 mm², `lost.py`) all lie on the re-routed leads:
    - west of U31 (x 20.75–25.35);
    - DIO1's lane (x 32.15–32.65, y 20.5–23.5);
    - NRST's lane (x 37.4–40.3).
  - None is under a module body (both equal above) or beside an RF line: `strip_gcpw` is equal, and so is the radio
    line zone.

### 3.2 Interface buses U1 → strip

`iface.py` (all tracks and vias of every RADIO_ / GNSS_ / 3V3_RADIO / 3V3_GNSS net, the RF lines excepted, and the
reference planes):

| Net | Copper | Vias |
|---|---|---|
| RADIO_SCK_MCU / RADIO_SCK | 15.73 + 13.19 mm F.Cu | 0 |
| RADIO_MOSI_MCU / RADIO_MOSI | 9.76 + 17.15 mm F.Cu | 0 |
| RADIO_MISO / RADIO_MISO_MCU | 1.48 + 27.90 mm F.Cu | 0 |
| RADIO_NSS | 32.21 mm F.Cu | 0 |
| RADIO_BUSY / RXEN / DIO1 / NRST | 32.01 / 40.02 / 25.04 / 41.04 mm F.Cu | 0 |
| GNSS_TXD / GNSS_TXD_MCU | 2.19 + 26.87 mm F.Cu | 0 |
| GNSS_RXD_MCU / GNSS_RXD | 9.16 + 19.36 mm F.Cu | 0 |
| GNSS_TP_MCU / GNSS_TIMEPULSE | 25.97 + 2.45 mm F.Cu | 0 |
| GNSS_RESET_N | 23.89 mm F.Cu | 0 |
| GNSS_SAFEBOOT_N | 4.26 mm F.Cu | 0 |
| RADIO_TXEN (R7's loop) | 25.17 mm F.Cu + B.Cu | 2 |
| GNSS_LNA_EN / GNSS_VCC_RF (limiter) | 7.65 / 6.20 mm F.Cu + B.Cu | 1 / 1 |
| GNSS_ANT_DC / SRC / GATE / PD | 10.97 / 8.57 / 6.92 / 3.44 mm (B.Cu; ANT_DC's rigid F.Cu tail) | 1 / 0 / 0 / 0 |

These lengths match pass 1 except where a fix pass 1 change moved copper (none of the interface nets moved). The
limiter's A2 / A3 figures (7.65 / 6.20 mm) match route_check's `ROUTE_FIGURES`.

- **Reference.** I sampled every F.Cu track against In1 GND and every B.Cu track against In2 GND, at the centre and
  ±0.2 mm, every 0.05 mm. GND is missing only:
  - inside the TXEN, limiter and ANT_DC via antipads, which are layer changes with GND partners (§3.4);
  - at the +x edge of RADIO_NRST at U1's east face (x 33.6, y 42.8–44.35, 28 samples). That run is 0.1 mm outside the
    0.2 mm lane, where two antipads meet: CAM_MCU_RX's hop via (33.95, 44.0) and a 3V3 via (34.0, 43.1).
    - A 0.01 mm raster (`in1probe.py`) shows In1 complete under the lane centre.
    - CAM_MCU_RX's antipad (radius 0.50 mm on In1) reaches x 33.45, 0.05 mm inside the lane's edge at 33.50, for about
      0.3 mm of length. The 3V3 antipad is tangent to the edge.
    - Pass 1 measured about 0.1 mm with the via at (33.9, 44.0); D91's 0.05 mm move halved it.
    - NRST is static after boot. This is an observation, not a finding (§5).
- **Proximity** (`aggr.py`, edge to edge, < 1.0 mm, every layer). The only close neighbours are:
  - U1's own pin pitch;
  - plan-view crossings with In1 (and In2) between: CAM_MCU_RX, CAM_FAULT_N, CAM_PWR_EN, USB_LIMITED, and U7's B.Cu pads
    under RADIO_NRST / DIO1. All are as pass 1 found them;
  - QSPI_CLK's escape (29.3, 46.0), 0.35 mm from the U1.39 (RADIO_NRST) pad inside U1's pin ring. It is a pin-field
    neighbour into a pin driven push-pull or held by R311's 2 kΩ, so the coupling is negligible (Inference).
- **Switching and fast nets** (`sw.py`, nearest to any RF-family copper, plan view, any layer):

  | Net | Nearest |
  |---|---|
  | CAM_SW / CAM_BST | 2.125 mm (C74, B.Cu, under RADIO_NRST's F.Cu lane, In1 between) |
  | USB_DM | 1.384 mm to GNSS_TXD_MCU (pass 1: 1.38) |
  | USB_DP | 2.006 mm |
  | HSE_OUT | 4.96 mm (C26.1 to the U1.39 pad) |
  | SWCLK | 6.11 mm |
  | SPI1_SCK | 9.48 mm |
  | SW_NODE / BST (logic buck) | > 20 mm |

  The D86 HSE_OUT redraw sits under U1, about 18 mm from the nearest RF part.
- **Bus geometry** (r8_route_rf.py, measured):
  - the GNSS lanes run at 0.6 mm pitch on their vertical sections;
  - the radio trio runs at 0.5 mm pitch;
  - MOSI and NSS run at 0.5 mm perpendicular pitch on their 45° runs (NSS is held low by a push-pull output during a
    transfer);
  - SCK is 1.04 mm from NSS on the diagonal and 1.9 mm from NSS above the fence; the F.Cu between NSS and SCK is now empty
    (G7);
  - the lanes have no layer change, no B.Cu or inner copper and no via.

### 3.3 F10 5 mm separation

`check_r8.rf_separation` (in the gate) and `fastrf.py`:

- **Parts:** the nearest restricted part is U1, 5.94 mm from R306. R310 / R313 / R315 are 6.04 mm from it. Then come
  FB31–U7 6.66 mm, C310–C73 7.86 mm and U31–U7 9.41 mm. All equal pass 1.
- **Fast lines:** R306–USB_DM 5.075 mm, at the redrawn track (15.39, 35.64). D91 kept the binding point. Next come
  R315–USB_DM 5.819 mm and R310 / R313–QSPI_IO3 / IO0 6.285 mm (U1 pads).
- **Module and RF-line figures in M3_R8 §RF, re-measured:**
  - U30 courtyard to USB_DM: 11.239 mm (D4.1);
  - U31 courtyard to CAM_BST: 15.761 mm (C74.2);
  - RF line to USB_DM: 21.493 mm (GNSS_RF_IN at U30.11).

  All three match the record after the USB_DM redraw.
- D17 sets the radio's own SPI and control lines outside the aggressor set (pass2_rf §3.10). Their distances to U30's
  body (RXEN 5.44 … SCK 8.94 mm, M3_R8) are R7's class or better.

### 3.4 GND vias at layer changes (RF-family nets)

`iface.py` / `gvia.py`, nearest GND via, centre to centre:

| Via | Nearest GND via | Next | R7 |
|---|---|---|---|
| GNSS_ANT_DC (11.45, 5.15), 0.6 mm, rigid | 1.011 mm (11.6, 4.15) | — | 1.011 |
| RADIO_TXEN (31.13, 20.15) | 0.721 (31.73, 20.55) | — | 0.721 |
| RADIO_TXEN (28.59, 7.80) | 0.721 (28.19, 7.2) | — | 0.721 |
| GNSS_LNA_EN (11.51, 8.30), 0.5 mm | **1.100** (12.61, 8.3) | 1.670 (10.37, 7.08) | 1.100 |
| GNSS_VCC_RF (10.41, 8.30), 0.5 mm | **1.221** (10.37, 7.08) | 1.385 (9.025, 8.325) | 1.221 |

- **Limiter vias.** The pass-1 margin case is gone: VCC_RF met the rule with 0.4 µm to spare at y 8.9, and now has
  0.28 mm. Both limiter vias are back at R7's figures.
- **Paste.** `check_r8.via_paste` passes. The rings are 0.15 mm from U30's T-shaped paste-only pads (y 8.70–10.10), and
  the board's nearest via ring to any paste aperture is 0.025 mm (C90.1, outside the strip).
- **Interface buses:** no layer change.
- **Feed vias:**
  - FB30's 3V3 via (12.33, 24.4): 1.100 mm;
  - FB31's (35.1, 24.4): 1.304 mm;
  - R310's 3V3 via (24.1, 28.45): 1.951 mm. It is a microamp pull-up joint on a power rail, outside AGENTS §3's
    critical-net list.

### 3.5 Fence and crossings

`cross.py`: 25 GND vias on y 23.3 at x 0.9, 2.9, 4.9, 6.4, 7.685, 9.7, 12.3, 14.2, 16.2, 18.2, 20.0, 22.1, 24.15, 26.0,
28.0, 30.0, 31.8, 33.0, 34.4, 35.8, 37.8, 39.4, 40.6, 42.6, 44.6. The edges are 0.9 and 1.4 mm away.

| Opening (gap > 2.0 mm) | Width | Lanes |
|---|---|---|
| 7.685–9.70 | 2.015 | GNSS_RXD, GNSS_TP_MCU |
| 9.70–12.30 | 2.600 | 3V3_GNSS |
| 20.00–22.10 | 2.100 | RXEN, BUSY, MISO_MCU |
| 22.10–24.15 | 2.050 | MOSI, NSS |

- **Crossings:** all 14 non-GND crossings are on F.Cu:
  - single-lane gaps 1.20–2.00 mm: DIO1 and NRST 1.20, 3V3 (FB31) 1.40, TXD_MCU 1.285, SCK 1.85 and RESET_N 2.00 mm;
  - lane edge to via ring ≥ 0.150 mm (MISO_MCU and MOSI against (22.1, 23.3), R8_VALIDATION C12 #8 / #9).
- **Planes:** no In1, In2 or B.Cu track lies within y 22.6–24.0. The only non-GND pour near the fence is In2 3V3, whose
  fill starts at y 24.0, forward of F10's strip (y ≤ 23.5).
- **GND reach through copper** (`route_check.gnd_reach`, limit 60 mm):

  | Region | F.Cu | B.Cu | In1 | In2 | Pass 1 |
  |---|---|---|---|---|---|
  | strip (y < 23.5) | 3.04 | 3.49 | 3.49 | 3.49 mm | equal |
  | band (y 23.5–28.5) | 5.20 | 5.20 | 3.17 | 3.02 mm | F 5.20 / B 6.06 |
  | bus (y 28.5–50) | 9.11 at (41.68, 41.93) | 11.63 at (30.33, 37.08) | 4.59 | 4.08 mm | F 15.06 (the finger) / B 11.63 |

  The B.Cu bus figure is a wide (≥ 1.0 mm) B.Cu GND piece at U1's aft-east corner. It is hemmed in by the CAM_PWR_EN /
  USB_LIMITED / CAM_FAULT_N B.Cu lanes, behind In1 GND from every RF lane. It is unchanged from pass 1 and outside this
  dimension (planes).

### 3.6 Coexistence paths

- **Unchanged (rigid):** the RF lines are 15.45 mm apart, the jacks 18.69 mm and the module courtyards 7.66 mm. Each
  module has its own ferrite (FB30 / FB31) and local bulk.
- **Supply:** both ferrites are fed from the In2 3V3 region, one via each, 22.8 mm apart.
- **Aggressor positions:** unchanged since pass 1.
  - The camera buck U8 is 13.49 mm from U31 and 24.81 mm from U30.
  - U1 is 15.06 mm from U30, and Y1 25.37 mm.
  - The logic buck is ≥ 43 mm away.

  The ORDERING §5 coexistence step now runs the camera-on, MCU-loaded and radio-keyed cases (RF-04 closed).
- **Shared paths between the chains:** the interface buses never come near the other module's RF copper. The radio
  lanes nearest U30's body are RXEN 5.44, BUSY 5.94 and MISO_MCU 6.44 mm, all ≥ 6.0 mm from the GNSS RF copper. No
  radio or GNSS lane changes layer or crosses the other chain's lanes.

### 3.7 Reset and bootloader states of the radio and GNSS lines

The netlist is unchanged (`0cc1ed69…`). Nodes (`schematic.net.xml`):

| Net | Nodes |
|---|---|
| RADIO_NRST | R311.1, U1.39 (PE9), U31.3 |
| RADIO_RXEN | R312.1, U1.56 (PD9), U31.10 |
| RADIO_NSS | R310.2, U1.47 (PB11), U31.14; R310.1 on 3V3 |
| RADIO_TXEN | U31.9, U31.19 (DIO2) |
| GNSS_RESET_N | U1.61 (PD14), U30.9 |
| GNSS_TP_MCU | R307.2, U1.62 (PD15) |
| GNSS_RXD_MCU / GNSS_TXD_MCU | R306.1 / R305.2, U1.63 / U1.64 (PC6 / PC7) |

U30.5 / 6 / 15 / 16 / 17 (EXTINT, V_BCKP, VIO_SEL, SDA, SCL) are unconnected, and U30.18 (SAFEBOOT_N) goes to TP30.
This matches F10.

The reset states are pass 1's table (§3.7 there), unchanged:
- **MCU in reset (or blank):**
  - PE9 is high-impedance and R311 (2 kΩ) holds NRST low: the SX1262 is in reset;
  - R312 holds RXEN low;
  - R310 holds NSS high;
  - SCK / MOSI / MISO / BUSY / DIO1 are high-impedance, or are module outputs into high-impedance inputs.
- **GNSS:** RESET_N is open drain with no capacitor, so the GNSS runs on its internal pull-up. TIMEPULSE goes through
  1 kΩ, never pulled down.
- **ROM bootloader:**
  - BOOT0 has only R5 to GND and is not on J2, so the bootloader is entered only by a firmware jump.
  - Binding constraint 8 (D6.8, regenerated `r8_binding_note.json` bound to `6600ef94…`) requires the SX1262 asleep
    and PE9 driven low, then returned to analog, before that jump. R311 then holds NRST low.
  - NSS stays high through R310 either way (D2 / D5), so USART3 is never detected.
- **Pins:** no radio or GNSS line is on PA13 / PA14 / PA15 / PB3 / PB4, and no RF-part pin is on a safety net
  (`check_r8` contract OK).

### 3.8 Fix pass 1 changes near the RF area: regression check

| Change | RF check | Result |
|---|---|---|
| D87 limiter vias at (11.51, 8.3) / (10.41, 8.3), 0.5 mm | GND partner, paste, U30_KEEPOUT, GNSS line ground, In1 under RF, `strip_gcpw` | GND partners 1.100 / 1.221 mm; rings 0.15 mm from paste; outside U30_KEEPOUT (y ≥ 11.25); GNSS line zone GND only gains (+0.2–0.28 mm² per layer); In1 missing under RF 0.0; gcpw digest equal; the VCC_RF via is 1.14 mm edge to edge from GNSS_ANT_DC's B.Cu run (as R7) |
| D90 trim G7 | Fill only on F.Cu GND, no pad cut, no new finger, In1 untouched | §2; no GND piece left between NSS and SCK; In1 complete under both lanes |
| D91 CAM_MCU_RX via (33.95, 44.0) | In1 under RADIO_NRST | antipad 0.05 mm inside the lane edge (was about 0.1 mm), centre covered (§3.2) |
| D91 USB_DM redraw | F10 fast-line distance | R306–USB_DM 5.075 mm, unchanged binding point |
| D86 HSE_OUT via (24.69, 47.5) | F10 crystal / fast line | ≥ 18 mm from every RF part; 4.96 mm from the U1.39 pad (MCU pin field) |
| D88 C83 (9.55, 36.0) B | proximity to GNSS lanes | ≥ 7.8 mm from the GNSS rows (y ≤ 28.2); not a fast net |
| `r8_route_rf` budget ratio 1.95 → 2.40, route_check A2 / A3 figures | Tool weakened? | No: the ratio rises because of the paste-clear via spot, which is R7's accepted geometry (R7 7.45 / 6.2 mm). `ROUTE_FIGURES` pins the exact routes (7.65 mm / 1 via, 6.20 mm / 1 via), so any change fails the gate. The other rf nets are unchanged |

## 4. Findings

| ID | Sev. | Requirement | Finding | Evidence | Fix |
|---|---|---|---|---|---|
| R8P2-RF-01 | Minor (not worth fixing) | AGENTS §3 (records match the board; GND via within 1.5 mm of a critical layer change) | **Two records give the GNSS_VCC_RF limiter via's GND partner as (9.025, 8.325) at 1.39 mm.** The nearest GND via is the rigid (10.37, 7.08), at 1.221 mm (R7's figure).<ul><li>The records are `docs/M3_R8.md` l. 369 ("GND partners 1.10 / 1.39 mm") and `tools/route_check.py` l. 243, the A3 allowlist reason ("rigid GND partner (9.025, 8.325) 1.39 mm away").</li><li>Both figures meet the 1.5 mm rule, and the gate measures the true nearest. So the record understates the margin; it does not hide a defect.</li></ul> | `gvia.py`: (10.41, 8.3) → (10.37, 7.08) 1.2207 mm, → (9.025, 8.325) 1.3852 mm. `near.py`: via GND (10.37, 7.08), 0.6 / 0.3 mm (rigid strip via). | Change the two texts to "1.22 mm ((10.37, 7.08))" when either file is next edited. route_check's reason string carries no figure the gate checks. |

## 5. Observations (no finding)

- **In1 under RADIO_NRST at U1's east face** (§3.2): CAM_MCU_RX's antipad comes 0.05 mm inside the lane's edge for about
  0.3 mm. The 3V3 via's antipad (34.0, 43.1) is tangent to it, and the centre is covered. NRST is static after boot and
  is driven push-pull or held by 2 kΩ. Moving either via a further 0.05 mm east would clear it, but this is not worth a
  rebuild.
- **F10 fast-line margin:** R306–USB_DM is 5.075 mm against 5.0 mm, unchanged by D91. The gate enforces it on every
  build.
- **Coexistence step:** ORDERING §5 records C/N0 deltas but sets no pass threshold for the camera-on case. F10 sets none
  for the keyed case either, and the GPS is tracking-only, so the owner judges the log. This is consistent with F10.
- **R313's position** (series 33 Ω on SCK): R313 sits 15.7 mm of copper from U1.46 and 13.2 mm from U31.15. For a
  29 mm line with STM32 GPIO edges (≥ about 1 ns), the line is electrically short (critical length about 85 mm at
  εeff ≈ 3, Inference), so where the resistor sits does not matter. It acts as edge damping.

## 6. Inferences (not measured, or not from a primary source)

- The coupling and critical-length estimates in §3.2 and §5 are arithmetic. I did not model them.
- AN2606 and DS12110 reset and loader states are taken from `pin_table.tsv`, R8_DECISIONS D2 / D5 / D6.8 and the
  binding note, which cite AN2606 Rev 70 Table 135 (pp. 320–323) and DS12110 §3.8 / Table 8. I did not re-read the
  documents for this pass, because the netlist and pin table are unchanged since pass 1.
- Isolation, pyro immunity and C/N0 under the R8 aggressors are bench items (F10, ORDERING §5).

## 7. Sources

- **u-blox MAX-F10S integration manual** UBXDOC-963802114-12892, §4.4 "Layout" (ground under the module on the top two
  layers; avoid ground stubs, or end them with a via):
  https://content.u-blox.com/sites/default/files/documents/MAX-F10S_IntegrationManual_UBXDOC-963802114-12892.pdf
- **EBYTE E22-900MM22S user manual** (via LCSC), §4.1 (no wiring under the module, top layer grounded) and the pin table
  (pin 3 NRST, 9 TXEN, 10 RXEN, 19 DIO2, 20 DIO1):
  https://datasheet.lcsc.com/datasheet/pdf/70331b0eaf0eedaea0129e9e66d9a011.pdf?productCode=C5333985
- **Project:**
  - `docs/REQUIREMENTS.md` F10, M2;
  - `AGENTS.md` §3;
  - `docs/M3_R8.md` §Signal routing, §Ground, §RF;
  - `docs/R8_VALIDATION.md` (Review pass 1, C12, C14–C16, "R7 pass-4 RF items on R8");
  - `docs/ORDERING.md` §5 l. 160–165;
  - R8_DECISIONS D2, D4, D6 (8), D11, D15–D17, D51, D86–D88, D90, D91;
  - `pin_table.tsv`; `step9/r8_binding_note.json`;
  - `tools/check_r8.py` (`rigid`, `rf_strip`, `fence`, `rf_line_stitching`, `rf_separation`, `via_paste`);
  - `tools/route_check.py` (`ALLOWLIST`, `ROUTE_FIGURES`, `pour_pieces`, `gnd_reach`);
  - `m3_design/r8_route_rf.py`;
  - `sources/r7_review/pass2_rf.md` §3.9–3.10;
  - `sources/r8_review/pass1_rf.md`, `fix1_handoff.md`.

## 8. Method (reproduction)

Every script ran under KiCad 10.0.6's Python (`-I`, `PYTHONDONTWRITEBYTECODE=1`) against the repository board, read
only, and against R7's board copied into the session scratchpad (`p2rf/`, deleted afterwards). Nothing in the
repository was written except this report.

- **Gate:** `KICAD_CLI=… tools/check.sh` (exit 0); `python -m unittest test_r8_check` (23 OK).
- **`rigid7.py`:** `check_r8.rigid` on R7 and R8, each digest compared with `RIGID_BASELINE`.
- **`stripdiff.py`:** sets of tracks (net, layer, sorted ends, width), vias (net, position, size, drill), footprints
  (position, rotation, side, pad nets and zone connections) and zone outlines with bounding-box top y < 23.5, R7 against
  R8.
- **`fillxor.py` / `lost.py`:** GND fill per layer, intersected with each region, R7 minus R8 and R8 minus R7; the lost
  pieces over 0.1 mm².
- **`iface.py`:** every RADIO_ / GNSS_ / 3V3_RADIO / 3V3_GNSS track and via (RF lines excepted), with lengths, vias and
  their nearest GND via. In1 (F.Cu) or In2 (B.Cu) GND point tests at the centre and ±0.2 mm every 0.05 mm, launch
  cut-outs excluded.
- **`in1probe.py`:** a GND fill raster of one layer, at 0.2 / 0.05 / 0.01 mm.
- **`gvia.py`, `near.py`, `pads.py`, `zones.py`:** nearest GND vias; the copper round a point; module pad nets; the trim
  outlines.
- **`cross.py`:** fence vias at y 23.3 ± 0.06, every non-GND track crossing y 23.3 with its gap and ring clearance,
  non-F.Cu tracks and non-GND fills near the fence.
- **`aggr.py`, `sw.py`, `fastrf.py`:** edge-to-edge distances (`check_r8.min_gap`, binary search on `SHAPE.Collide`)
  from RF-family copper to every other net (< 1.0 mm), to the switching / fast nets, and from the module courtyards and
  RF lines to the fast nets.
- **`fingers.py`:** `route_check.pour_pieces` with FINGER_W 0.5 / 0.75 / 1.0 mm (relief rings excluded, as the gate
  does), and `route_check.gnd_reach` per layer over x 0–46, y −1–75, limit 60 mm, by region.
- **Netlist:** `schematic.net.xml` nodes of every radio, GNSS, NRST and BOOT0 net; `pin_table.tsv` rows; ORDERING §5 and
  the R8 records by text.
