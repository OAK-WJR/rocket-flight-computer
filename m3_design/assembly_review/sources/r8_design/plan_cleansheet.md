# R8 Strategy C: clean-sheet re-placement and re-route

Plan for re-laying out the R7 flight computer from its netlist. Only the true hard constraints stay fixed. Everything else is placed for signal flow, routed as planned buses on an assigned layer stack, and built by a new deterministic script chain instead of R7's patch stages.

All work happened on scratch copies in `r8_design/cleansheet/`. The repository was only read, and the R7 board (`c872a3d3…`) is unchanged. Numbers marked **measured** come from the prototype boards described in §13. They are CAD-model results: a fully placed board, a drawn RF interface, and solved 7.7 A pours. None of it is a finished routed board. Numbers marked **estimate** are projections, and **Inference** follows AGENTS §2.5.

## 0. Verdict

**Strategy C is feasible, and it is the only strategy that removes the causes of R7's compromises rather than their symptoms.**

The prototype placed all 252 footprints legally (DRC, bore fit) and showed three things:
- The radio/GNSS interface becomes 12 straight F.Cu lanes with no vias.
- The 7.7 A feed drops from 7.96 to 2.23 mΩ, with its narrowest track section 2.7× wider.
- The board's flyline length falls by a third and its crossing proxy by 58 %.

**Cost:** a full requalification (DC, references, RF stitching, vibration, ORDERING, firmware binding, review loop), and a pin-map change in F10 that the owner must approve.

**What does not reach a literal zero:**
- **The radio's own TXEN loop.** It must cross either the SPI bundle or the RF line because nothing may cross the module's pad field.
- **TP122's in-pad gate via, inside the frozen CH1 block.**

Both are geometry-forced. Each needs either a reviewed rule refinement or one recorded entry. Section 7 gives the honest list.

**Headline comparison (R7 → R8):**

| Item | R7 | R8 (prototype or estimate) |
|---|---|---|
| Σ octilinear MST of nets without a pour, the placement measure (S17) | 2727 mm | **1842 mm measured** |
| MST-edge crossing proxy, same script on both boards | 527 | **223 measured** |
| Radio interface, 8 MCU chains: copper / vias | 512 mm / 24, plus 8 no-GND layer changes | **234 mm / 0 measured**; the module-local TXEN loop adds 36 mm / 2 vias |
| GNSS interface copper / vias | 208 mm / 8 | **100 mm / 0 measured** |
| 7.7 A path, RAW_ACT + BAT_IN + ACT_FET_S, 0.1 mm grid | 3.74 + 3.03 + 1.19 = 7.96 mΩ | **1.88 + 0.21 + 0.14 = 2.23 mΩ measured** |
| RAW_ACT narrowest section | 2.95 mm, F.Cu only | **7.87 mm over three layers, measured**; the remaining necks are FET pad rows |
| Signal track on In2 | 901 mm | **0 by design** |
| Allowlist / leftovers / AGENTS §3 instances | 45 / 29 / 9 | **1–2 / 0 / 1 estimate** (§7) |
| Fit margins: J9 mated, C84 | 0.03 / 0.11 mm | **0.12 / 1.86 mm measured** |
| Long-edge tab window forward of y 72 | none (a forward rail requested) | **yes, on both edges, measured scan** |

## 1. What stays fixed, and what R8 deliberately keeps at R7 coordinates

### Fixed by requirement or safety text
- **Outline and fit (P1, P2):** 46 mm wide, ≤ 120 mm long; bore fit; bottom parts ≤ 3.0 mm.
- **Supports (P2):** five M3 supports with 3.5 / 3.8 mm clearances, plus two J122 tie holes and a 4 mm tie channel.
- **RF strip (F10):** at y 0–23.5, with:
  - In1 and In2 GND only;
  - module keep-outs;
  - GCPW W 0.30 / G 0.25 mm;
  - the limiter on B.Cu under U30;
  - both modules on top;
  - RF parts ≥ 5 mm from the bucks, the MCU, the crystal and fast digital lines.
- **SMA jacks:** on the aft edge, rotation 0, ≥ 12 mm apart.
- **CH1 block:** rigid (`CH1_PADS`).
- **J1:** within 25 mm of both CH1 terminals, entry forward.
- **Sensors:** IMU and barometer on the bottom, no copper under them on their side.
- **MCU pins:** the pyro, servo and sentinel pins, and the PE10/PE0 NC pins (`check_actuators`, `check_r7`).
- **Bottom parts:** SMD only; TP122 on the bottom; bottom keep-outs (THT pins 1.5 mm, M3 3.5 mm, TP122 2 mm).
- **BOM:** unchanged, with no new part (52/52 extended codes).

### Kept at R7 coordinates by choice
None of these is required. Each saves a requalification and costs nothing in routing.

| Item | Why keep it |
|---|---|
| **Outline 46 × 118 mm and the five M3 supports** at (4, 4), (42.3, 4), (4, 64), (4, 114.4) and (42, 114.4) | The VEHICLE stack row, the sled drawing and the washer sizing stay valid. The prototype leaves free area, so a shorter board is possible (Inference: about 6 mm out of y 48–66), but it would spend the routing room that buys simplicity. This is an owner option, not part of this plan. |
| **RF chains, jack to module RF pin, as a rigid copy:** J30, J31, D30, D31, L30, C302–C305, R304, R316, C313, C314, U30, U31, limiter Q30–Q32 / R300–R303 / C304 | The pass-2 field solve (50.3 Ω), the launch (49 Ω) and the isolation geometry stay valid. Only the module-side interface passives, the fence and the stitching are redrawn (§6.1). |
| **CH1 block with its copper and its three entry vias,** and the `PYRO_BLOCK` rule area unchanged at (4, 84)–(42, 114.4) | `CH1_PADS` passes trivially. The rectangle pinned in `check_actuators` 15b needs no edit, and the R4 spacing work and ORDERING's coating and leakage distances survive. R8 enters the block from B.Cu through R7's own entry vias (R7 entered from In2 through the same vias). |
| **J1 at (23, 110.4), rotation 180** | Its fit and the 25 mm rule hold as today. |
| **J122 on the axis** (moved only 4.2 mm aft) | It stays in the bore-fit band and keeps the R7 mated margin of 0.71 mm. |

## 2. Floorplan: signal flow aft to forward

```
 y 118 ┌────────────────────────────────────────────────┐  forward edge: J1 entry faces +y
       │ [M3]        J1 (BAT+ GND SW SW)          [M3]  │
       │ bot: U9 net, R165/R80 | D8 C80 C96 damper | Q120|Q121 + gate drive   (battery corner)
 y 100 │ J124 ARM  [ CH1 block: R7 copper, unchanged ]  J121 IGN ║ RAW_ACT spine
       │ bot: U7 U8 L3 (camera supply)  TP122               ║ F + In2 + B, x 39.8-45.6
 y  81 │ C84 (top)   bot: U2 L1 U11      ══ feed (F + In2) ═╝  C121 (top)
       │ [M3]  tie hole   J122 (axis)   tie hole          ┃ B.Cu corridor x 35-39:
 y  64 │ J9 camera (left edge)  J2 SWD   IMU, baro (bottom, ┃ servo x4 + pyro x4
       │ bot: U12 U13             axis)                    ┃
 y  48 │ J3 USB-C ── D4 ── U1 MCU (flash, crystal under it) ┃ sense dividers / 3V3A
 y  31 │ GNSS lanes ╲     radio bus ╲   NRST ─────────┐  LEDs  J123  LS120
 y23.5 │─ ─ ─ ─ ─ fence (3 openings) ─ ─ ─ ─ ─ ─ ─ ─ ─│─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│
       │  U30 GNSS + limiter (B.Cu)        U31 radio   │                         │
 y   0 └──────J30──────────────────────────J31─────────────────────────────────┘  aft edge
```

**Principles**
- **U1 sits right forward of the strip.** The radio and GNSS pins (pin map H0) face the modules across a clean 7 mm band, with nothing but quiet parts in between.
- **The power section lives at the battery entry.** J1, the hot-plug input parts (TVS, input caps, damper, bleed, eFuse) and the actuator switch sit together, which restores the R4 hot-plug model's premise.
- **The 7.7 A path is a battery corner:** J1.1, then Q120 and Q121 side by side (sources facing), a three-layer spine down the right edge, and J122. The battery-switch harness lines are a few millimetres long.
- **Left column (USB side):**
  - USB, SWD, camera (J9 + translator + supply) and logic power (C84 / U11 / U2);
  - RAW_PROTECTED runs down the left edge from U9 to the camera and logic power;
  - USB_LIMITED stays local.
- **Right column:**
  - the radio, the pull-pin / LED / buzzer cluster just aft of U1's east face, and the sense dividers;
  - the **B.Cu corridor** carrying the four servo and four pyro lanes north to J122 and the block;
  - the RAW_ACT spine.
- **Centre:** U1, the flash and crystal under it, the IMU and barometer on the bottom 0.6 mm off the roll axis (R7: 13 mm), J122, then the block and J1.

## 3. Placement

Coordinates come from prototype v2 (`cleansheet/place_r8.py`). The DC test (§13) re-placed the actuator FETs. Every part not listed sits at its anchor by the deterministic placer: decoupling at its pin, series resistors at the driving end, dividers at their ADC pin.

### Major parts

| Ref | x, y, rotation, side | Note |
|---|---|---|
| U1 | (23.0, 39.5), 90, top | R7 orientation kept. The courtyard is 5.65 mm from FB30, the nearest RF part (R7's closest RF separation was 5.87 mm, FB30 to C6). Every other RF part is ≥ 8.7 mm away. |
| U3 flash | (21.4, 39.5), 0, bottom | Under U1; six short inward QSPI dives (F5 unchanged) |
| Y1 | (28.6, 40.0), 90, bottom | Under U1's east row at HSE pins 12/13; In2 keep-out under it (R5 V1). C25/C26 beside it. |
| U4 IMU | (23.6, 51.9), 0, bottom | Rotation and side unchanged, so the axis map (roll = +gyro_Y) holds. 0.6 mm off the axis, so centripetal acceleration falls from about 6.5 g to about 1.2 g at 4000 dps (Inference). |
| U5 baro | (28.8, 52.8), 0, bottom | At I2C1 pins 95/96 |
| J3 USB-C | (4.6, 43.0), −90, top, left edge | DP/DM are level with U1 pins 70/71: two straight F.Cu lines through D4. J3 margin 0.89 mm, as R7. |
| D4 | (10.9, 43.25), 90, top | In line (flow-through) |
| J9 camera | (3.4, 54.0), 90, top, left edge | Same edge distance as R7, mirrored. Mated margin **0.12 mm** (R7 0.03). |
| J2 TC2030 | (11.4, 53.0), 90, top | At U1's NW corner. The J2.1 in-pad via exception (M2) is retired. |
| C84 OS-CON | (9.6, 74.0), 0, top | Margin **1.86 mm** (R7 0.11). Stake on the sides away from J122. |
| U2 / L1 / U11 | (5.0, 72.6) / (9.7, 72.6) / (14.6, 72.6), bottom | Under C84. 3V3 goes straight into the In2 3V3 tongue. |
| U10 | (9.6, 43.1), bottom | At J3 |
| U12 / U13 | (8.6, 55.6) / (13.6, 58.6), bottom | At J9 |
| U7 / U8 / L3 | (7.4, 84.0) / (12.6, 84.6) / (19.2, 85.4), bottom | Camera supply forward-left, clear of J124's pin tails and TP122 |
| J122 | (23.0, 71.5), 90, top | Rows along y. RAW_ACT is fed into the middle column at its forward end. |
| Tie holes | (27.0, 64.4) aft, (19.0, 78.4) forward | Mirrored from R7, because the feed now comes from the east. Edit `fit_check.RETENTION_HOLES`. |
| C121 | (34.6, 71.6), 0, top | RAW_ACT bulk at the feed |
| D121, R154–R157, R150–R153 | Bottom, at the J122 fan-out east of the tie channel | On the B.Cu servo lanes, which run at 2.54 mm pitch there: direct taps, with the 1 k resistors in line |
| Q120 | (34.5, 104.5), 270, bottom | Drain faces J1.1 at 3.9 mm |
| Q121 | (42.0, 104.5), 90, bottom | Sources face Q120's sources (ACT_FET_S is a 1 mm bridge); drain over the spine |
| Q122, R120–R123, C120, TP121 | Bottom, around (31–38, 97–101) | Gate drive. ACT_GATE / ACT_DRV pads ≥ 1.0 mm from live pads (rule H). |
| D8 | (26.6, 103.4), bottom | TVS at the entry |
| C80, C96, C89, C95, R166, R167, TP80 | Bottom, x 11–30, y 98–111 | Input caps, damper (R166 2512), bleed and probe pad at J1 (F9 hot-plug) |
| U9, R81–R84, C81, C87, C88, R89, TP84, TP89 | Bottom, around (11, 104) | eFuse at J1.3/J1.4 |
| R80 / R165 | (23.2, 113.9) / (13.1, 113.9), bottom | The 470 kΩ legs right at J1.3 / J1.4 (R7: 86 mm away) |
| D9, C82, R92 | Bottom, around (15, 99) | At U9's output |
| LED1 / LED2 / J123 / LS120 | Top, aft-east, y 25.3–32.8 (from the drawn test, §13) | Driven from aft-face east pins 28–31; clear of NRST's run at y 24.6 |
| Q123 | (42.0, 32.6), bottom | Buzzer driver |
| R60–R63, R164, C10, C11, C21, C22, R168, R170, R172 | At their U1 pins, east face / aft-east, west of the corridor | R170/R172 at pins 33/34 under U1 (the lanes dive there) |
| TH1–TH3 | Relocated, for example (44.6, 40), (1.4, 34), (44.6, 52) | Standard PCBA does not need them. Removing them (schematic) is an owner option. |

### Interface passives (from the drawn RF test)

| Ref | Position | Role |
|---|---|---|
| R313 | (19.0, 29.6), rotation 90 | SCK series at the MCU end |
| R315 | (13.85, 32.6), rotation 90 | MOSI series at the MCU end |
| R306 | (13.3, 39.5), rotation 180 | GNSS RXD series at the MCU end |
| R314 | (23.0, 12.73) | MISO at U31, as R7 |
| R311 | Moved onto NRST's lane at pin 3 | NRST pull-down |
| R310 | Proposed at the MCU end on 3V3 (O-4) | NSS pull-up |
| 3V3_RADIO cluster (FB31, C310–C312) | Compacted west of x 36.5, north of pin 1 | §7 item 3 |

### What the prototype checks (measured)
- **DRC** (kicad-cli, project `m3.kicad_dru`): no courtyard overlap, no pad clearance, hole or NPTH violation. Only silkscreen and library notices remain.
- **`fit_check`** (copy, with the new tie holes): **OK**.
  - J9 mated 0.12, J122 mated 0.71, J3 0.89, terminals 1.15, C84 1.86 mm.
  - Wire entry 6.3–6.9 mm, as R7.
  - Nearest bottom envelope to a support 3.95 mm; nearest top hardware 4.76 mm.
- **Density:** top 92 parts at 0.40 courtyard share; bottom 160 parts at 0.21 (R7: 106 / 0.42 and 146 / 0.16).
- **Long-edge 5 mm tab windows** (1.5 mm from parts, 5 mm from capacitors): left y 0–6 and 93.5–117.5; right y 0–22.5, 58–95.5 and 108.5–117.5. The forward-rail request in ORDERING §3 becomes unnecessary.

## 4. U1 pin changes

The proposed map: H0 from the connectivity survey for the radio and GNSS, plus moves for the camera, LEDs, pull-pin and USB status that the floorplan needs. There are 17 signal moves.

| Signal | R7 pin | R8 pin | Function | Why |
|---|---|---|---|---|
| RADIO_SCK_MCU | PB13 / 52 | **PB10 / 46** | SPI2_SCK AF5 | Lane order: no crossing at U31 |
| RADIO_NSS | PB12 / 51 | **PB11 / 47** | GPIO | Same |
| RADIO_MOSI_MCU | PB15 / 54 | **PB14 / 53** | SPI2 with IOSWP (MISO/MOSI swap) | Same. IOSWP is **Inference** from RM0433: verify. Without it, MOSI/MISO swap pins and need a one-via crossover. |
| RADIO_MISO_MCU | PB14 / 53 | **PB15 / 54** | SPI2 with IOSWP | Same |
| RADIO_BUSY | PD8 / 55 | PD8 / 55 | — | Unchanged |
| RADIO_RXEN | PE15 / 45 | **PD9 / 56** | GPIO, low in reset (R312) | Lane order |
| RADIO_NRST | PD9 / 56 | **PE9 / 39** | GPIO (TT pin; on-board only) | Outermost lane, east |
| RADIO_DIO1 | PD10 / 57 | **PE15 / 45** | EXTI15 | Lane order |
| GNSS_RESET_N | PC8 / 65 | **PD14 / 61** | Open drain | Innermost GNSS lane |
| GNSS_TP_MCU | PD14 / 61 | **PD15 / 62** | TIM4_CH4 capture (never EXTI) | Lane order |
| GNSS_RXD_MCU / GNSS_TXD_MCU | PC6 / 63, PC7 / 64 | Unchanged | USART6 | — |
| CAM_MCU_TX / RX | PB10 / 46, PB11 / 47 (USART3, a ROM-loader port) | **PC12 / 80, PD2 / 83** | UART5 AF8 | Camera on the left. Removes the loader-port DFU-hijack path that U12's OE guards today. |
| CAM_UART_OE | PC13 / 7 | **PC10 / 78** | GPIO (R102 pull-down) | Left-going |
| LED_YEL / LED_RED | PE7 / 37, PE8 / 38 | **PA4 / 28, PA6 / 30** | GPIO | Aft-east cluster. PA6 is a loader SPI1 pin: the LED may flicker in the loader (harmless, Inference). |
| PULLPIN | PC14 / 8 | **PA7 / 31** | GPIO, EXTI7 | Aft-east, next to J123. Check FT for the off-board input in DS12110. |
| USB_FAULT_N | PD6 / 87 | **PA8 / 67** (polled) | GPIO | Beside U10 |
| VBUS_SENSE | PD15 / 62 | **PC9 / 66** | EXTI9 | Beside U10. EXTI15 is now DIO1. |
| Unchanged | — | — | — | Pyro gate PE4 / 3, CONT PC0 / 15, ARM PC5 / 33, RAW PB0 / 34, sentinels, servos PA0–PA3, QSPI, SPI1, I2C1, IMU_CS / INT1, USB, SWD, HSE, BOOT0, VLOGIC / V3V3 / CAM_5V senses, BAT_FAULT_N PD0, LOGIC_SOURCE_ST PD1, CAM_PWR_EN PD3, CAM_FAULT_N PD4, BUZZ_DRV PA5 |

**Freed (no connect):** PB12, PB13, PD10, PC8, PC13, PC14, PE7, PE8, PD6, PA15, PC11, PD5, PD7 and PE11–PE14. PE10 and PE0 stay no-connect (contract). PA9 and PA10 stay unconnected.

**EXTI map after R8:**
- EXTI0 BAT_FAULT_N, EXTI1 LOGIC_SOURCE_ST, EXTI4 CAM_FAULT_N.
- EXTI7 PULLPIN, EXTI8 BUSY (polled or handled), EXTI9 VBUS_SENSE: all on the EXTI9_5 vector, so the handler checks pending bits, as R7 already documents for BUSY.
- EXTI15 DIO1.
- TIMEPULSE on TIM4_CH4 capture.

**Contract impact:**
- The F10 pin text, and `check_r7.RF_MCU_PINS` / `FREED_NC` in a new `check_r8`.
- Camera notes; firmware binding.
- The frozen design's "avoid PB10/PB11" (USART3) needs a written exception. The argument is the one pass 2 accepted for PB14/PB15: RADIO_NSS is held high by R310, so 0x7F never arrives on PB11, and R311 holds the radio in reset.

**Checks before binding** (survey §7):
- DS12110 Table 10 for PB10, PB11, PD15, PC12, PD2, PC10, PA7 and PA8.
- RM0433 SPI_CFG2.IOSWP.
- AN2606 Table 135 for PB10/PB11 and PC12.

**Servo channel order** stays as contracted (SERVO1 on J122.1). The reversal from U1's pin order is made by the F.Cu escape stubs crossing over the B.Cu lanes near U1 (§6.3), with no extra via and no schematic change.

## 5. Layer plan

| Layer | Role | Rules |
|---|---|---|
| **F.Cu (L1)** | Top parts and local routing. Carries the RF interface buses, both GCPW lines, USB, SWD, status / camera fan-out on the left, the F.Cu third of the RAW_ACT spine, the J122 feed and the GND pour. | Every F.Cu signal is referenced to In1. Crossings happen only F over B, never on one layer. |
| **In1 (L2)** | **Solid GND.** No track, no split, no via column. | Only antipads, THT holes and the two F10 SMA launch cut-outs. Target coverage ≥ 0.92 (R7 0.880); slots ≤ 4 (R7 16). |
| **In2 (L3)** | **Power layer, no signal tracks at all** (R7: 901 mm of signal). Regions: GND under the strip (F10), under the CH1 block and under the whole B.Cu corridor; **3V3** under U1, the IMU and the left column, with a tongue to U2 and tongues to FB30/FB31's feed vias just outside the strip; **BAT_IN** across the forward end; **RAW_ACT** under the right spine and the J122 feed. | About 4–5 regions. No B.Cu signal crosses a region edge: the corridor sits wholly over GND; QSPI, SPI1, NRST and the sense taps sit wholly over 3V3. Y1's keep-out is the only hole inside the 3V3 region. |
| **B.Cu (L4)** | Bottom parts. Carries: the **corridor** (servo ×4 and pyro ×4, north–south, x 35–39); the under-U1 dives (QSPI, NRST, the two pyro senses); the IMU / baro links; left-column local power (RAW_PROTECTED, USB_LIMITED, CAM_5V); the BAT_IN, ACT_FET_S and RAW_ACT pours at the battery corner; the GND pour. | References In2, GND or 3V3 according to the region map. |

**On the brief's "orthogonal signal layers":**
- Strict Manhattan-per-layer is not adopted. The board is long and narrow, so almost all flow runs fore and aft.
- Instead each bus is assigned a layer:
  - F.Cu for radial escapes and short runs;
  - B.Cu for the long north–south corridor and the dives under U1;
  - In2 for power only.
- Every crossing is then F over B, with In1 and In2 between. That gives orthogonality's benefits (no same-layer conflicts, solid references) with fewer vias.

## 6. Routing architecture: what becomes simple

### 6.1 Radio and GNSS interface (measured, `route_rf2.py`)
- **Path:** eight radio lanes leave U1's SW corner as one 0.5 mm-pitch bus. They take a single 45° jog into the gap between the modules and enter U31's west pins straight. RXEN continues under U31's south row.
- **NRST** runs outermost: along y 24.6, north of FB31's 3V3 via, then down the east side.
- **GNSS:** four lanes wrap the corner and drop into U30's north row. RESET_N passes east of FB30's feed and the others pass west.
- **Layer and vias:** everything is on F.Cu over In1, with **zero vias** on the 12 MCU-side lanes. The only layer change is **TXEN** (U31 pin 19 ↔ pin 9), a 2-via B.Cu underpass in the gap. Each via has room for a GND via within 1.5 mm.
- **Separation:**
  - SPI lanes run ≥ 5.2 mm from U30's courtyard in the gap. MISO comes to 4.87 mm at U30's corner diagonal; a 0.2 mm shift clears it.
  - BUSY and RXEN are quasi-static (F10 / `pass2_rf` §3.10).
- **Lengths:**

| Family | Copper | Lane ratios (to octilinear distance) |
|---|---|---|
| Radio | 269 mm, including TXEN 35.6 | BUSY 1.17, RXEN 1.30, DIO1 1.26 |
| GNSS | 100 mm | — |
| Every lane except TXEN and NRST | — | ≤ 1.4× |

  NRST was drawn at 40.6 mm (1.61×). Compacting the 3V3_RADIO cluster west of x 36.5 brings it to about 34 mm (1.4×) (§7).
- **Fence:** three openings (GNSS x ≈ 6.5–15.3, radio x ≈ 19.5–25, NRST x ≈ 37). The GNSS opening takes two GND vias between its lane groups, so no continuous gap exceeds about 2.7 mm (R7 accepted 4.27 mm).
- **Gate impact:** R7's B.Cu NSS hop, the DIO1 B.Cu lead and the band and corridor via columns all disappear. `STRIP_B` / `STRIP_VIA` tighten to the limiter nets plus RADIO_TXEN only, which retires 20 of the 45 allowlist entries.

### 6.2 7.7 A servo feed (measured, `dc_proto.py` + baseline `run_dc.sh` at 0.1 mm)
- **BAT_IN:** a 5 mm pour from J1.1 straight to Q120's drain, on B.Cu (no series via) plus In2.
- **ACT_FET_S:** a bridge between the facing source rows.
- **RAW_ACT:** a three-layer spine (F.Cu, In2, B.Cu; x 39.8–45.6; stitched every 2 mm) beside J121. It is then fed into J122 by an F.Cu + In2 band (y 76.3–81, 4.7 mm), with B.Cu joining west of the corridor.
- **Results** (R7 in brackets):

| Net | Resistance | Narrowest section |
|---|---|---|
| RAW_ACT | 1.88 mΩ (3.74) | 7.87 mm summed over three layers, at Q121's drain-pad edge (2.95 mm single layer). The measured pours started at x 38.6 (F.Cu, In2) / 39.4 (B.Cu); the recommended 2.5 mm keep-off from J121 (x ≥ 39.8) adds roughly 0.1–0.2 mΩ (Inference). |
| BAT_IN | 0.21 mΩ (3.03) | Q120's drain pad row, 4.27 mm |
| ACT_FET_S | 0.14 mΩ (1.19) | The source pad row, 2.76 mm. R7's neck was the same pad row. |

- **IPC-2152 at the RAW_ACT neck:** about 14 °C on the B.Cu share (4.1 A in 2.42 mm, same fit as R7, no plane credit; Inference), against R7's 38 / 30 / 44 °C. MARGIN P1-9 is met in substance: the battery corner, ≥ 10 mm equivalent along the run, pad necks only.
- **The one P1-9 nuance:** the B.Cu corridor must pass under the feed. So the feed has no B.Cu between x 35 and 39, and RAW_ACT changes layer through the spine's via farm (§7).
- **Spacing:** the spine keeps **≥ 2.5 mm** from J121's IGN and OUT pads. That is 2.5× rule E, chosen because RAW_ACT next to IGN is the same ARM-bypass class as RAW next to BUS. The coating covers the gap.

### 6.3 Servo and pyro corridor (estimate, by construction)
- **Escapes from U1:**
  - Servo pins 22–25 escape east on short F.Cu stubs to staggered vias, then run north on B.Cu. The staggering reverses the lane order with no extra via, so the contracted J122 pin map holds.
  - Gate (pin 3) and CONT (pin 15) escape the same way.
  - ARM / RAW senses (pins 33/34) dive under U1 at R170 / R172 and run east under the aft pad row.
- **Corridor order, west to east:** SERVO4…SERVO1, ARM, GATE_N, CONT, RAW_SENSE.
- **Servo lanes** turn west into J122's east column at 2.54 mm pitch, with R150–R153 in line and D121 / pull-downs tapping on the bottom.
- **Pyro lanes** pass east of J122 and under the F.Cu + In2 feed, then turn west at y 82–86 to the block's entry vias:
  - GATE_N at (23.0, 88.33);
  - CONT at (28.4, 88.61);
  - ARM at (18.18, 91.30).
  RAW_SENSE ends at its divider beside the feed (R177 / R124 / R125 / R182 / C122, about (25–30, 80–82), top).
- **Lengths and vias:** servo about 4 × 50 mm with 4 vias (R7: 435 mm / 28 vias / 251 mm on In2). Pyro about 290 mm with 8 vias (R7: 253 mm / 18 vias). The pyro lanes are **longer** because U1 is aft, but they run on one reference (In2 GND), with each via at a planned GND-via spot. The terminals stay ≥ 68 mm from the radio (pass-1 rationale).

### 6.4 Everything else

| Family | R8 route | R7 (survey) |
|---|---|---|
| USB | Two straight F.Cu lines of about 8 mm, J3 → D4 → U1, 0 vias, over In1 | 18 mm of USB_DM unreferenced |
| SWD | J2 at U1's NW corner: SWDIO and SWCLK about 8 mm on F.Cu; NRST about 18 mm under U1 on B.Cu (1–2 vias) | 163 mm / 12 vias |
| QSPI | Six dives to the flash under U1, about 50 mm / 6 vias, each with a GND via, over In2 3V3 | 151 mm / 11 vias |
| IMU / baro | SPI1, CS, INT1 and I2C dive at U1's forward row to U4 / U5, about 5–8 mm each | 157 mm flyline |
| Camera | Left-local: UART5 lanes (forward-face west pins 80/83) to U12; PWR_EN / FAULT to U7; CAM_5V as a short B.Cu strip from L3 to J9 | 349 mm / 32 vias |
| Status and harness | BAT_SW legs at J1 (a few mm); BAT_FAULT_N from U9 about 60 mm on B.Cu at x ≈ 17 (≥ 2.4 mm from TP122); LOGIC_SOURCE_ST and USB lines local | BAT_SW lines 129 / 160 mm |
| Sense taps | VLOGIC and CAM_5V reach their east and aft-east ADC pins by two thin B.Cu lanes over the 3V3 region. ADC pins exist only there. | — |
| Power rails | 3V3 from L1 into the In2 tongue; RAW_PROTECTED down the left edge from U9 (camera and U11 on the same side); VLOGIC local | RAW_PROTECTED 153 mΩ to the camera |

## 7. Compromises that remain (honest list)

1. **TXEN loop** (radio-internal, pin 19 ↔ pin 9): 2 vias, about 35 mm for an 11 mm span. EBYTE's pad-field rule makes it unavoidable: any single-layer path crosses the SPI bundle, RXEN or the RF line. It is F10-legal (the module's own interface traces). `route_check` still flags the detour, so the owner picks one:
   - (a) a reviewed `route_check` refinement: the detour baseline becomes the shortest octilinear path that respects the module keep-outs;
   - (b) one allowlist entry with the measured reason.
2. **TP122's in-pad gate via** (AGENTS §3 instance A8, already a named M2 exception). There is no legal GND-via spot within 1.5 mm without moving the via out of the pad, and that is an interior change to the frozen block, which would mean a new R4-style spacing pass. It stays as an inherited, recorded item unless the owner orders the block interior reworked.
3. **NRST and the 3V3_RADIO feed point.**
   - Topologically, NRST must pass north of FB31's In2 via: pin 1 (3V3) lies north of pin 3 (NRST) on the same module edge.
   - The fix is to compact FB31, C310, C311 and C312 west of x 36.5, north of pin 1, and to move R311 onto the lane. That gives about 34 mm (1.4×).
   - R7's module-side passive positions are not part of the qualified RF chain, but the stitching review covers the move.
4. **R310 (NSS pull-up to 3V3_RADIO).** 3V3_RADIO exists only east of U31, and NSS enters from the west, so the pull-up crosses the bundle. The owner picks one:
   - (a) move R310 to the MCU end with its rail on 3V3: a net change in `check_r7.PULLS`. Same DC behaviour, because 3V3_RADIO is 3V3 through a ferrite (Inference);
   - (b) keep 3V3_RADIO with a 2-via B.Cu hop, which is F10-legal ("each module's own supply").
5. **Interface series resistors near U1.** R313 / R315 / R306 sit about 1–3 mm outside U1's courtyard, at the driver, where source termination belongs. If a reviewer counts R3xx interface resistors as "RF parts" under F10's 5 mm rule, they move to y ≈ 25.5 in their lanes. They still pass `check_r7.SERIES`, but narrowly (13.8 against 14.6 mm centre distance). This is a rule-interpretation item for review.
6. **P1-9 "ideally zero series vias".** RAW_ACT goes from the B.Cu spine to the F.Cu + In2 feed through a via farm, because the corridor needs B.Cu under the feed. The about 40 parallel 0.3 mm vias add tens of µΩ (Inference). The alternative: the feed takes B.Cu + In2, and the four pyro lanes take one extra via each to cross over on F.Cu. The owner picks; the plan recommends the via farm.
7. **Pyro lanes are longer** (about 290 mm against 253) because the MCU now sits aft. They are DC and filtered (4.7 kΩ at the MCU; RC at the block), stripline-referenced to In2 GND, and ≥ 68 mm of terminal-to-radio distance is kept. F10's pyro-immunity bench test decides.
8. **Two analogue sense taps** (VLOGIC, CAM_5V) cross from the left column to the east and aft-east ADC pins. No ADC pin exists on the west or forward faces. Both are non-critical, short (about 25–30 mm) and over 3V3.
9. **Camera connector moves to the left edge.** The cable leaves the opposite side from R7. The bay orientation is still open (operating assumption "Board position"), so the owner confirms it together with the coax-loop side.
10. **Fence openings rise to three** (GNSS, radio bus, NRST). With interior GND vias the continuous gaps stay ≤ about 2.7 mm. `check_r7.FENCE_OPENINGS` and F10's quoted gaps change.

Nothing else is expected to need an exception.
- **USB and HSE:** no layer changes.
- **QSPI, SPI1, CS, pyro:** every layer change sits at a planned GND-via spot.
- **In2:** no signal.
- **In1:** no via columns.
- **Hygiene:** scripted octilinear buses don't create the R7 hygiene classes (tiny jogs, staircases, hops, local bumps).

## 8. Expected metrics against the baseline scorecard

| ID | Metric | R7 | R8 (how obtained) | Proposed target |
|---|---|---|---|---|
| G | Gate | 0 | 0 (required) | 0 |
| C1 | Gated route_check instances | 74 | 2–3 estimate (TXEN detour, A8, possibly the NRST ratio if not compacted) | 0 |
| C2 | Information instances | 252 | ≤ 80 estimate (pad-end offcentre at module pads, power-via counts) | ≤ 100 |
| C3 | Allowlist entries | 45 | 0–2 (TXEN, A8; 0 with the tool refinement and an owner-ordered TP122 fix) | 0 |
| C4 | Leftovers | 29 | 0 estimate | 0 |
| C6 | AGENTS §3 instances | 9 | 1 (A8, inside the rigid block) | 0 |
| S1 | Signal track | 3355 mm | about 2100–2300 estimate (S17 × 1.15–1.25) | ≤ 2700 |
| S4 | Signal layer-change vias | 217 | about 80–100 estimate (top-IC ↔ bottom-part links, 6 QSPI, 7 IMU/baro, 8 pyro, 4 servo, 2 TXEN) | ≤ 110 |
| S6 | Detour ratio | 1.396 | about 1.15–1.2 estimate | ≤ 1.20 |
| S7 | Excess over MST | 1081 mm | about 300–400 estimate | ≤ 450 |
| S8 / S9 | Nets over 1.6 / 2.0 | 23 / 12 | 1 / 1 (TXEN) | 0 / 0 |
| S12 | Critical layer changes | 73 | about 25–30 estimate | ≤ 35 |
| S13 | … without a GND via | 8 (9) | 0, plus A8 inside the block | 0 |
| S15 | Signal on In2 | 901 mm | **0 by design** | ≤ 300 |
| S16 | Track on In1 | 0 | 0 | 0 |
| S17 | Σ MST, nets without a pour | 2727 mm | **1842 measured** | ≤ 2400 |
| — | MST-edge crossing proxy | 527 | **223 measured** | — |
| P1 / P3b | In1 coverage / slots | 0.880 / 16 | ≥ 0.92 / ≤ 3 estimate | ≥ 0.90 / ≤ 4 |
| P4 / P6 | In2 regions / split-edge length | 8 / 1581 mm | 4–5 / about 700 mm estimate | ≤ 5 / ≤ 900 |
| P7 | Outer GND islands on one via | 32 | 0 (stitching grid at ≤ 4 mm) | 0 |
| P9 / P10 | GND-via distance p95 / max | 6.1 / 13.8 mm | ≤ 3.5 / ≤ 7 by grid design | ≤ 4 / ≤ 8 |
| R1 / R3 | Unreferenced critical length | 60 / 116 mm | about 0 beyond own antipads estimate (no B.Cu critical run crosses an In2 edge; USB on F.Cu) | ≤ 5 / ≤ 15 |
| R5 | `critical_reference` unreferenced share | 27.9 % | < 5 % estimate (antipads only) | ≤ 10 % |
| D_raw / D_bat / D_fet | 7.7 A resistance, 0.1 mm grid | 3.74 / 3.03 / 1.19 mΩ | **1.88 / 0.21 / 0.14 measured** | ≤ 3.7 / 3.0 / 1.2 |
| D_min | Smallest neck / 20 °C width | 0.50 | ≥ 1.0 estimate (track sections ≥ 7.9 mm summed; only FET pad rows narrower) | ≥ 1.0 |
| Radio (8 chains) / GNSS (4 chains) | Copper / vias | 512 / 24 and 208 / 8 | **234 / 0 (+ TXEN 36 / 2) and 100 / 0 measured** | — |
| Fit | J9 mated / C84 | 0.03 / 0.11 mm | **0.12 / 1.86 measured** | ≥ 0 |
| Simplicity index | R7 = 100 | 100 | about 35–45 estimate | — |

These estimates assume the implementation keeps every bus as drawn in §6. The scorecard script (`baseline/run_survey.sh`) re-measures them on the real R8.

## 9. Requirements and safety rules at risk, and how they are protected

| Rule | Risk in a clean sheet | Protection |
|---|---|---|
| AGENTS §2.1 ARM break / F8 rule E | The RAW_ACT spine and feed run near the block | Block copper unchanged. The spine is ≥ 2.5 mm from J121's pads (rule E is 1.0). The feed is ≥ 0.5 mm from gate and sense copper by DRC (`m3.kicad_dru` unchanged, hashes valid). `check_actuators` unchanged, including the 15b rectangle. Coating mask unchanged (part-based). |
| §2.2 pyro bus after the load switch | — | Netlist unchanged; `check_actuators` 1–8 pass |
| §2.4 gate network | — | Rigid block. The exits change layer (B.Cu instead of In2) through the same entry vias. |
| F8 pyro DRC rules A–H | New neighbours of the block's exits | DRC on every build. Re-measure rule B / F margins at the exits; R7's tightest, 0.503 mm to the SERVO4_MCU via, disappears. |
| F10 strip content, keep-outs, GCPW, limiter, top-side modules | Interface redrawn | RF chains rigid. `check_r8`: per-layer net lists, with `STRIP_B` tightened to the limiter nets plus TXEN; `module_ground`, `launch_reference`, `rf_grounds`, `rf_stitching`, `rf_gnd_reach` re-run; 5 mm separations re-measured and recorded (FB30 ↔ U1 courtyard 5.65 mm on the prototype). |
| F10 pin contract and radio reset hold | Pins move | R311 kept on NRST at the module; R312 on RXEN; R310 per O-4. F10 text rewritten for H0 and the EXTI table. No RF-part pin on a safety net (pad-level check, independent of placement). Firmware binding notes updated. |
| F10 pyro immunity / coexistence | U1 and the pyro lane origins closer to the radio | Terminals ≥ 68 mm from U31; pyro lanes on B.Cu under In2 GND; bench tests unchanged and mandatory |
| F9 reverse hot-plug | — (improved) | The input parts sit within about 5–25 mm of J1 (R7: 70–85 mm), restoring the R4 model's premise. Bench hot-plug test still required. |
| F4 7.7 A copper | New copper | Re-solve at 0.05 mm on the final board, plus the IPC cut analysis (rebuild `dc_ipc` from `baseline/dc_neck.py`). Prototype shown in §6.2. |
| F1 / F2 IMU | Moves | Bottom side, rotation 0, so the axis map is unchanged. No via or fill under it (rule areas recreated). Away from staked parts. 3 mm coating-free zone. |
| F3 baro | Moves | Bottom, port to the sled, no tracks between its pad rows (BARO areas recreated) |
| F5 flash | Moves under U1 | Same part; C29 ≤ 2 mm from U3.8 (`check_r7`) |
| F6 failsafe | — | Servo pull-downs and the clamp unchanged (taps on the B.Cu lanes); neutral-at-reset unaffected |
| P1 / P2 fit and supports | Tall parts and tie holes move | `fit_check` (new `RETENTION_HOLES`) passes with larger margins. Supports unchanged. Tie channel kept clear of bottom parts (enforced in the placer). |
| P3 staking / coating / retention | C84 and C121 move; J2 moves | Staking sides re-specified (C84 away from J122; C121 away from the feed); J2 coating procedure unchanged. Mated retention unchanged (J122 tie, J123 RTV). |
| M1 assembly | — | Same parts, same sides policy (THT top, SMD both), same reflow notes |
| M2 clean routing | The goal itself | `route_check` with an empty allowlist and leftovers from the start. The J2.1 in-pad via exception is retired. TP122 per §7. |
| M3 cost / codes | — | BOM unchanged: $105.98, 52 extended codes. No new part (O-4(a) changes a net, not a part). |

## 10. What must be requalified

| Item | Action |
|---|---|
| **F4 DC solve and IPC-2152** | Full 0.05 mm solve (about 40 min) of the three paths plus the about 20 logic / camera / 3V3 rows; neck cuts; new F4 line; owner closes C1 (expected met, not "accepted as estimated"). |
| **Critical-reference sampling** | Replace the "lost vs R6 + 18" comparison with an absolute metric on R8 itself: every 0.01 mm sample of the critical and extended sets, listing every unreferenced sample (target: own antipads only). |
| **Pyro spacing** | No geometry change inside the block, so `CH1_PADS`, the rectangle, the DRU hashes and ORDERING's leakage distances stand. Re-measure the exits' margins and record them. |
| **Fit** | `fit_check` on the final board; update the numbers quoted in REQUIREMENTS, ORDERING and VEHICLE (J9 0.12, C84 1.86, the washer's nearest pads). |
| **RF** | Chains rigid, so the field solve and launch stand. Redo the fence and stitching review (three openings, new gap figures into F10), the 5 mm separation table, the nearest-copper isolation geometry (unchanged chains, new interface) and the shunt-trace VNA model (unchanged). |
| **Bench and procedure (ORDERING §3–§7)** | Regenerate: tab windows (no forward rail), tooling holes, order-number mark, NRST / TP80 / GND probe points, coating mask (J2 position), C84 / C121 staking sides, sled bottom pours (now at the forward-right), wire room, washer data. |
| **Mechanical** | Re-run the plate model: C84 and C121 move, J3 and J9 sit on the left, supports unchanged. Tap-check target. |
| **Firmware binding** | New binding from `assembly_binding.py` with the new pin table and EXTI map (AGENTS §3) |
| **IMU axis map** | Unchanged (rotation 0, bottom); bench sign check as always |
| **Documents** | REQUIREMENTS F10 (pins, gaps), M2 (J2.1 exception removed), F4, P1 / P3 numbers; VEHICLE stack row (only the J9 side and the tie holes change); M3_R8 record; R8_VALIDATION with a deviation list of 0–2 entries. |
| **Review** | A new independent review loop, stopping at no Critical or Major with the gate at zero (memory rule), with a dedicated routing reviewer (memory: PCB clean routing). |

## 11. Implementation: a new build from the netlist

R8 should not stack on R7's patch chain. About 5,300 lines across `r7_route`, `r7_redraw`, `r7_rework`, `r7_hygiene` and `r7_polish` exist only to repair inherited copper. `r8_build.sh` builds the board from the R7 board file (for footprints, library data and the two rigid copper groups at their unchanged coordinates) plus the updated schematic, as follows.

1. **`r8_sch.py`:** the 17 pin moves as net-label edits on the MCU, telemetry, camera_uart, pullpin_buzzer and usb_sense sheets, plus R310's rail (O-4). Export the netlist; ERC and parity.
2. **`r8_pcb.py`:**
   - SHA-check R7.
   - Delete every track, via and zone **except** the RF-chain copper (`STRIP_RIGID` net list: GNSS_RF_ANT / RF_IN, RADIO_RF / RF_ANT, the limiter nets) and the CH1 block copper (block nets inside the rectangle, entry vias included).
   - Update nets from the netlist.
   - Place every footprint from **`r8_place.tsv`**: one row per footprint, reviewed, the prototype's v2 table promoted after cleanup.
   - Tie holes, stackup.
   - Rule areas: module keep-outs, PYRO_BLOCK (same rectangle), IMU / BARO, U31 body, a tie-channel courtyard keep-out.
   - Zones by the §5 region map.
3. **`r8_route.py`:** named, explicit bus geometry in the style of `route_rf2.py`, each stage asserting its own lengths, vias and ratios:
   - `rf_iface` (from the prototype);
   - `rf_fence` (fence and stitching);
   - `corridor` (servo and pyro, with the escape-stub reversal);
   - `servo_fanout`;
   - `usb_swd`;
   - `qspi_dives`;
   - `imu`;
   - `camera_left`;
   - `status`;
   - `sense_taps`;
   - `power` (battery corner, spine, feed, via farm, BAT_IN, ACT_FET_S, left RAW_PROTECTED, CAM_5V strip, 3V3 tongue feeds, VLOGIC);
   - `locals`: the remaining two- and three-pin passive links via the repo's `r5_maze`, as a copy or module, with an acceptance test of ratio ≤ 1.3 and 0 extra vias per net, failing the build otherwise.
4. **`r8_ground.py`:**
   - a GND via within 1.5 mm of every critical layer change (the deterministic spot search R7 already has, from `r7_hygiene.gnd_vias`);
   - a stitching grid at ≤ 4 mm;
   - no single-via islands;
   - refill.
5. **`r8_post.py`:** silkscreen and legends (reuse `r7_post` logic), order-number mark, refill; then `tools/check.sh`.
6. **Gate changes:**
   - **`check_r8.py`**, a copy of `check_r7` with new constants: `RF_MCU_PINS`, `FREED_NC`, `FENCE_OPENINGS`, `STITCH_ACCEPTED`, tightened `STRIP_B` / `STRIP_VIA`, PULLS for R310. `JACKS`, `U31_BODY`, `MODULE_GND` and `CH1_PADS` are unchanged.
   - **`check_actuators`:** unchanged (rectangle and pin contract the same).
   - **`fit_check`:** `RETENTION_HOLES`.
   - **`route_check`:** empty `ALLOWLIST` / `LEFTOVERS`, plus the optional keep-out-aware detour baseline (O-6).
   - Add `baseline/scorecard.py` thresholds as a soft report in `check.sh`.
7. **Determinism:** fixed KIIDs and no random search. Freerouting is not used. Two clean builds must give the same SHA (as R7).

## 12. Effort and sequence

| Phase | Content | Effort (focused agent days) |
|---|---|---|
| 0 | Owner decisions O-1…O-8 below; DS12110 / RM0433 / AN2606 checks | 0.5 |
| 1 | Schematic pin map, `check_r8` contracts, binding notes | 1 |
| 2 | Placement table finalised (from prototype v2), `r8_pcb.py`, zones, rule areas; DRC and fit at zero | 1.5 |
| 3 | Scripted routing, bus by bus (RF interface already prototyped; about 140 nets) | 4–6 |
| 4 | Ground vias, stitching, silkscreen, fab outputs, gate at zero | 1.5 |
| 5 | Requalification: 0.05 mm DC and IPC, absolute critical references, RF stitching review, vibration model, ORDERING / REQUIREMENTS / VEHICLE / M3_R8 | 2–3 |
| 6 | Independent review loop: 2–4 passes with fixes (stop rule from memory) | 3–5 |
| **Total** | | **About 14–19 agent days** |

That is several times an incremental pass, which is the price of fixing causes rather than symptoms.

**Main schedule risk:** Phase 3. Mitigation: the bus geometry is planned here, and the prototype already proves the hardest family (the RF interface) and the hardest copper (the 7.7 A feed).

**Owner decisions needed before Phase 1**
- **O-1:** Approve pin map H0 plus the moves in §4 (F10 text, and the PB10/PB11 exception to the frozen "avoid" list).
- **O-2:** Accept the clean-sheet requalification scope (§10).
- **O-3:** Camera connector on the left edge (cable side and bay orientation).
- **O-4:** R310 rail: (a) 3V3 at the MCU end, or (b) a 2-via 3V3_RADIO hop.
- **O-5:** P1-9 treatment at the spine-to-feed transition: via farm (recommended), or 4 extra pyro vias.
- **O-6:** TXEN detour: `route_check` keep-out-aware baseline (recommended), or 1 allowlist entry.
- **O-7:** TP122 / A8: keep as the inherited named exception (recommended), or order a block-interior requalification.
- **O-8:** Tooling holes: relocate (recommended) or remove from the schematic.

## 13. Prototype evidence (scratch, reproducible)

All work is in `r8_design/cleansheet/`, run with KiCad 10.0.6's Python. Inputs: a byte-identical copy of R7's `assembly_review` board and rules.

| Script | Output | What it shows |
|---|---|---|
| `place_r8.py` | `proto/r8p2.kicad_pcb`, `proto/r8p2.json`, render `proto/r8p2.svg.png` | All 252 footprints placed: rigid groups at R7 coordinates, majors explicit, passives by an anchored deterministic search with keep-outs (supports, tie holes and channel, THT tails, NPTH, TP122, strip, 1 mm around bare test pads). DRC clean of courtyard, clearance and hole errors; `fit_check` OK. |
| `pinmap.py`, `metrics.py` | — | S17 2727 → 1842 mm; MST-edge crossings 527 → 223 (the same script reproduces R7's 2727 exactly) |
| `route_rf2.py` | `proto/r8p2_rf2.kicad_pcb`, `proto/rf2_lengths.txt`, render `proto/svgout/rf2_zoom.svg.png` | The full radio and GNSS interface as explicit octilinear buses with pin map H0. DRC clean; 0 vias on the MCU-side lanes; TXEN 2 vias. |
| `route_rf.py` | — | A greedy single-net maze (`r5_maze`) **fails** on the same task (4 nets unrouted, NSS at 42 mm). Evidence that R8 needs planned bus geometry, not autorouting. |
| `dc_proto.py` + `../baseline/run_dc.sh` (0.1 mm grid) | `proto/r8p2_dc2.kicad_pcb`, `proto/dc2/dc_*.txt` | 7.7 A copper: RAW_ACT 1.88, BAT_IN 0.21, ACT_FET_S 0.14 mΩ; RAW_ACT narrowest cut 7.87 mm over three layers |
| `tools_copy/` | — | Copies of `fit_check.py` (tie holes edited) and `r5_maze.py`. The repository itself was never written. |

**Limits of the evidence:**
- No GND pours, stitching, silkscreen or full routing.
- The corridor, USB, SWD, QSPI, camera and status routes are by-construction estimates, not drawn.
- The DC pours have no competing copper.
- The crossing proxy is a straight-line MST count, not the topological annulus model of the connectivity survey.
