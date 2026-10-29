# R8 survey: connectivity and routing pressure

Board surveyed: R7 `m3_design/assembly_review/m3.kicad_pcb` (SHA-256 `c872a3d3…`, branch m3-assy-r7 @ 431025d), read only.
Scripts, data and logs are in `r8_design/connectivity/`. The main ones are `netstats.py`, `logical.py`, `model.py`/`annulus.py`
(rat's nest and crossings), `pinopt.py`/`annopt*.py` (pin-map search), `maze.py`/`seqmaze.py`/`seqscen*.py` (2-layer maze),
`h743_af.json` (the AF table) and `floorplans.py`.

**Status of the numbers.** Everything below is a CAD-model estimate. Crossings come from a topological model and lengths from
octilinear flylines. Routability comes from a crude grid maze on F/B only. None of it is a routed board.
- The alternate functions come from ST's machine-readable pin database (STM32_open_pin_data `STM32H743VITx.xml` +
  `GPIO-STM32H747_gpio_v1_0_Modes.xml`, the CubeMX data). The project's own CIRCUIT_REVIEW used the same database.
  Check every pin chosen for R8 against DS12110 Table 10 before binding.
- ROM-bootloader roles come from the project's records of AN2606 Rev 70 Table 135 (pass1/pass2_electrical, frozen §3.10).
- **Inference:** `SPI_CFG2.IOSWP` (MISO/MOSI swap) is from memory of RM0433 and has not been re-read here.

## 1. Net graph and where the pressure is

- **Size of the board:** 142 nets (135 signal nets, plus pours on GND, 3V3, 3V3A, BAT_IN, RAW_ACT, CAM_5V and ACT_FET_S);
  252 parts (106 on top, 146 on the bottom); 1724 track segments of 4428 mm; 710 vias (378 GND, 332 signal or power).
- **U1 pins:** 57 carry signals and 27 are NC.
- **Detour on signal nets** (no pour): routed 3808 mm against a 2727 mm octilinear MST, ×1.40. Their 242 vias compare
  with roughly 40 that pad layers would force.
- **In2 is a third signal layer.** It carries 901 mm of signal track (only 112 mm of power track), so the In2 planes
  are perforated:

  | Family | Signal track on In2 |
  |---|---:|
  | Servo | 251 mm |
  | Camera | 197 mm |
  | Pyro sense/gate | 131 mm |
  | Status | 131 mm |
  | BAT_SW harness | 111 mm |
  | SWD | 32 mm |
  | LEDs | 24 mm |

**Excess by family.** Each U1 connection is traced through its series parts to its real endpoint (the "chain"). The
R7 copper is compared with an obstacle-aware single-net maze on the R7 placement, which is a lower bound for that
placement with no congestion.

| Family | R7 chain copper | R7 vias | Maze lower bound | Maze vias | Main cause |
|---|---:|---:|---:|---:|---|
| servo (4) | 435 mm | 28 | 121 mm | 0 | R150–R157 sit in the pyro block (y 89–101) while J122 is at y 72–80 and D121 at y 82, so every line overshoots and comes back. PA0–PA3 are at the **aft** end of U1's east face |
| camera (5) | 349 | 32 | 161 | 6 | The camera UART is on PB10/PB11 at the **west** end of the aft face, but U12/J9 are east. The camera eFuse and buck (U7/U8/L3) are forward (y 86–100) while J9 is at y 42, so CAM_5V runs y 33–107 on In2 and CAM_PWR_EN/CAM_FAULT_N run 82–96 mm |
| radio (8) | 512 | 24 (+8 layer changes with no GND via) | 331 | 14 | The radio is on U1's **west** face (pins 51–57) but U31 is east-aft. C84 walls off the west face. The radio lanes are enclosed by the QSPI bus. Lane order is wrong (19 RF crossings, §3) |
| pyro (4) | 253 | 18 | 158 | 8 | The ARM/RAW_ACT senses (PC5/PB0) are on the **aft** face but the pyro block is forward. PYRO1_CONT detours |
| status (9) | 213 | 26 | 123 | 9 | The BAT_SW harness: J1 is at the forward edge but U9/R80/R165 are aft, giving 129 + 160 mm lines and a full-length BAT_IN In2 pour |
| gnss (4) | 208 | 8 | 144 | 8 | RESET_N is on the wrong end of the group (pin 65), and VBUS_SENSE (pin 62) sits inside the group |
| swd (3) | 163 | 12 | 107 | 0 | SWDIO/SWCLK are at U1's NW corner but J2 is on the east edge |
| qspi (6) | 151 | 11 | 141 | 6 | BK1 spreads over all four faces (pins 1, 36, 58–60, 92) |

**The R7 deviation list by family.** The route_check allowlist has 45 entries: 20 RF interface (8
critical_via_no_gnd, 6 detour, 4 extra_vias, 2 tiny_jog), 17 power/GND chain detours or hops, 3 pyro, 3 status/USB, 1
QSPI and 1 camera. The 29 non-critical leftovers are 9 camera, 9 status/harness/USB, 6 servo, 4 SWD and 1 pyro.
R7_VALIDATION C5/C6/C18/C24 (split crossings, band and corridor runs, chain detours) are almost all RF interface.
**Roughly two thirds of the ~90 compromises trace back to five placement/pin-map causes** (Inference from the counts above):
1. **The RF interface on U1's west face behind C84.** C84 is the OS-CON hold-up cap, courtyard 11 × 13.6 mm, only
   0.16 mm from U1's west courtyard. C80/C96 (BAT_IN bulk) sit on the bottom under the same face. The west power
   cluster (U9, D8, D9, BAT_IN_F, damper, R80/R165) and the aft power cluster (U2, L1, U3 flash, D9) close both direct
   paths to the strip. That leaves only the left-edge B.Cu corridor plus the band.
2. **The QSPI enclosure.** With the flash aft, CLK (PB2, pin 36) and IO0/IO1/IO3 (pins 58–60) bracket pins 37–57. Any
   aft-going bus on those pins, here the radio, must cross the QSPI bus. The topological model counts 17 qspi×radio
   crossings.
3. **Servo chain placement.** The series and pull-down resistors are in the pyro block, and the servo pins are on the
   aft end of the east face.
4. **Camera split across the board.** Power is forward-east, the connector is mid-east and the UART pins are aft-west.
5. **Battery entry forward, input protection aft.** This creates the harness lines, the full-length BAT_IN on In2 and
   the RAW_PROTECTED tree.

## 2. Topological facts that drive the pin plan

- **Rotating U1 alone never removes a crossing.** Crossings depend only on the cyclic order of pins against the cyclic
  order of destinations, and rotation preserves that order. The annulus model gives 351 for R7 at all four
  orientations. Rotation changes only lengths, wraps and which block each face meets: flyline length is 1652 mm at the
  current rotation, 1690 at +90° (51–75 aft), 2069 at 180° and 2056 at −90°. **Pin reassignment and block placement
  are the levers.**
- **The board shape sets the budget.** At 46 mm wide with U1 centred, the east and west faces have about 14 mm to the
  edge, so almost everything is fore or aft. U1's signals split about 25 going aft (RF 12, QSPI 6, power-section
  status/LED/pull-pin) and about 25 going forward (servo 4, pyro 4, IMU/baro 7, SWD/USB 5, camera power 2, buzzer).
  The pin plan must keep each face's aft-going pins contiguous at its aft end and its forward-going pins at its
  forward end. Any interleaving costs a crossing; R7's VBUS_SENSE at pin 62 inside the GNSS group is one example.
- **Package order.** Pin numbers increase anticlockwise seen from the top: east face 1→25 runs forward to aft, aft
  face 26→50 east to west, west face 51→75 aft to forward, forward face 76→100 west to east. A bundle leaving the aft
  face therefore has its lanes **east→west in increasing pin number**. That order continues around the SW corner onto
  the west face.
- **The lane order the modules force at the strip mouth (y 23.5), east to west:**
  - Radio: **NRST, DIO1** go round the north of U31 to pins 3 and 20. **SCK, NSS, MOSI, MISO, BUSY** go down the gap
    into U31's west-edge pins 15, 14, 13, 12, 11. **RXEN** goes down the gap and under the south edge to pin 10. U31's
    RF pin fixes the module's orientation, and F10 forbids any lane across U31's pad field.
  - GNSS, straight down into U30's north edge: **RESET_N (pin 9), [3V3_GNSS feed], TIMEPULSE (4), RXD (3), TXD (2)**.
  - Radio lanes must all be east of GNSS lanes.
- **Every SPI on LQFP100 has SCK < MISO < MOSI in consecutive pins** (PA5–7, PB3–5, PB13–15, PC10–12, PE12–14). U31
  needs MOSI east of MISO, and NSS between SCK and MOSI. With adjacent pins that costs at least 2 crossings, unless:
  - `IOSWP` swaps the MISO/MOSI roles, which removes one crossing (**Inference**, RM0433 not re-read); and
  - SCK uses a non-adjacent alternate pin, which removes the NSS one: SPI2_SCK on **PB10 (pin 46)** with NSS on PB11
    (47) and MOSI/MISO on PB14/PB15 (53/54).

## 3. RF-interface pin maps (crossings between the 12 RF nets, topological)

The current block placement is used throughout. "Strict" respects every recorded rule: E2 (no radio SPI with an AF on
PE4), the PE10/PE0 NC contract, frozen §3.10, and the EXTI 5–9 avoidance.

| Map | Radio | GNSS | RF crossings | RF flyline | Rules |
|---|---|---|---:|---:|---|
| R7 | SPI2 PB12–15, BUSY PD8, NRST PD9, DIO1 PD10, RXEN PE15 | TP PD14, PC6/PC7, RESET PC8 | **19** | 487 mm | as built |
| **H0 (recommended)** | **SCK PB10/46 (SPI2 AF5), NSS PB11/47, MOSI PB14/53 + MISO PB15/54 via IOSWP, BUSY PD8/55, RXEN PD9/56, NRST PE9/39 (or PE8), DIO1 PE15/45 (EXTI15)** | **RESET_N PD14/61, TP PD15/62 (TIM4_CH4), RXD-line PC6/63, TXD-line PC7/64** | **0** | 467 mm | strict except one needed exception: PB10/PB11 are on frozen §3.10's USART3 "Avoid" list (see below) |
| H1 | SPI2 PB13 SCK, NSS PB12, IOSWP, BUSY PD8, RXEN PD9, NRST PE7, DIO1 PE15 | as H0 | 1 (NSS×SCK) | 476 | strict |
| H3 | SPI4 PE12–14 + IOSWP, NSS PE9, NRST PE7, DIO1 PE8, BUSY PE15, RXEN PB12 | as H0 | 1 | 437–442 | relaxed: SPI4 has SPI4_NSS on PE4 (pass1 E2, Major); PE11–14 are loader SPI4 pins; DIO1 on EXTI8 (or PE10, a contract edit) |
| H2 | SPI6 (or SPI1) PA5–7 + IOSWP, NSS PA4 | as H0 | 2–3 | 437–453 | strict, but NRST has no east-side GPIO (the free east pins are PC13–15, backup domain, no sourcing) and PA4–7 are loader SPI1 |

**H0 bootloader and safety check** (from project AN2606 records, partly Inference):
- **PB10/PB11 (USART3 in the ROM loader).** PB10 becomes push-pull only after USART3 is selected (frozen design, PA2 row:
  on loader v0x91 a USART TX becomes an output only after detection). Selection needs 0x7F on PB11, which is RADIO_NSS held high by R310, so the line stays idle. This is the same
  argument pass2 accepted for PB14/PB15 (USART1 alt) in R7.
- **The radio is held in reset by R311 whenever the loader runs.** MISO is high-Z then.
- **The camera leaves USART3** for UART7 PE8 (TX) / PE7 (RX), which is not a loader port. That removes the camera's
  DFU-hijack path that U12's OE currently guards.
- **No AF path to a pyro, ARM or servo pin.** SPI2's other AF pins are PC1 (sentinel), PC2_C/PC3_C (senses), PD3,
  PB9, PA9/PA11/PA12 and PB4. UART7's are PA8, PA15, PB3 and PB4. TIM4's are PB6–9 and PD12–15.
- **EXTI after H0:**
  - 0, 1, 4 and 6 stay as they are (PD0, PD1, PD4, PD6);
  - 14 stays PULLPIN;
  - 15 becomes DIO1, so VBUS_SENSE leaves PD15 for a forward pin (PD2 → EXTI2, or polled);
  - TIMEPULSE uses TIM4_CH4 capture, never EXTI.
- **PE9 is TT (4.0 V).** That is fine for an on-board 3V3 line; the frozen design forbids it only off-board.
- **Freed:** PB12, PB13, PD10 and PC8, plus PE7/PE8 from the LEDs.

**H0 in the 2-layer maze (F/B only, sequential, no In2), current placement:** all 12 RF nets route. Radio is 329 mm
with 8 vias and GNSS 161 mm with 4, against R7 pins on the same model: one radio net unrouted and 12 radio vias. With
the placement edits of §5 (S10): radio 312 mm with 4 vias, GNSS 147 mm with 2. Each radio line is 32–49 mm, against
52–85 mm in R7. The leftover vias are artefacts of the model's net order; the topology needs none.

## 4. MCU pin-assignment freedom (every U1 signal)

Notation is port/pin. "Contract" means the pin is pinned by `check_actuators.py` or REQUIREMENTS F10 text. Moving it
needs a reviewed contract edit and the new firmware binding (none exists for R7 anyway).

| Signal | Now | Legal alternatives (same function) | Constraint / verdict |
|---|---|---|---|
| PYRO1_GATE_N | PE4/3 | — | **Fixed** (contract U1.3; DESIGN_ASSURANCE: never re-derive). Sentinels PE3/2, PE5/4, PE6/5 stay NC |
| PYRO1_CONT_MCU | PC0/15 (ADC123_INP10) | ADC pins only | **Fixed** (contract U1.15). PC1/16 sentinel |
| ARM1_SENSE_MCU, RAW_ACT_SENSE_MCU | PC5/33, PB0/34 | other ADC pins (PC2_C/PC3_C would put them on the east face) | **Fixed** (contract U1.33/34). PC4/32 sentinel. They dive under U1 to R170/R172; keep that |
| SERVO1–4_MCU | PA0–PA3/22–25 (TIM5 CH1–4) | TIM4 PD12–15 or PB6–9; TIM3/TIM8 PC6–9; TIM3 PA6/7, PB0/1, PB4/5; TIM1 PE9/11/13/14 (PE9 TT, banned off-board) | **Keep** (contract and frozen C1). Every alternative collides with QSPI, GNSS, IMU or I2C, or a TT/loader rule |
| HSE_IN/OUT, NRST, BOOT0, USB_DM/DP, SWDIO, SWCLK | PH0/PH1, 14, 94, PA11/12, PA13, PA14 | — | Fixed by silicon |
| QSPI_CLK | PB2/36 | — (only QUADSPI_CLK) | Fixed: always on the 26–50 face |
| QSPI_IO2 | PE2/1 | BK2 only (PE9) | Fixed for BK1 |
| QSPI_IO0 / IO1 / IO3 | PD11/58, PD12/59, PD13/60 | IO0 PC9/66; IO1 PC10/78; IO3 PA1 (servo, ✗) | PC9/PC10 are loader I2C3/SPI3 pins |
| QSPI_NCS | PB6/92 (AF10) | PB10/46 (AF9) | 10 k pull-up. BK2 option: IO0–3 PE7–PE10/37–40 + CLK PB2 (contiguous on the aft face) + NCS PC11/79 (loader push-pull pin; PE10 contract) |
| RADIO SCK / MISO / MOSI | PB13/52, PB14/53, PB15/54 (SPI2) | SPI2 SCK PB10/46, PD3, PA9, PA12; MISO PC2_C; MOSI PC3_C, PC1 (sentinel). SPI1/6 PA5–7 (+PA4 NSS). SPI3 PC10–12 or PB3–5. SPI4 PE12–14 (E2 ✗) | IOSWP swaps the roles. **H0: SCK PB10** |
| RADIO_NSS | PB12/51 | any GPIO not loader-driven, not PA14 (reset pull-down) | pull-up R310 |
| RADIO_NRST | PD9/56 | GPIO; not PC13–15 (no sourcing into R311 2 k), not PA6/PB10/PB14/PC11/PE13 (loader-driven), not PA13/PA15/PB4 (reset pull-up) | **H0: PE9** |
| RADIO_BUSY | PD8/55 | any GPIO input not loader-driven | H0 keeps it |
| RADIO_DIO1 | PD10/57 (EXTI10) | GPIO with a free EXTI line (2, 3, 10–13; 5–9 share EXTI9_5 with USB_FAULT_N; 15 if VBUS_SENSE moves) | **H0: PE15** |
| RADIO_RXEN | PE15/45 | GPIO, low in reset (R312); same exclusions as NRST | **H0: PD9** |
| GNSS UART | PC6/63, PC7/64 (USART6, the only map) | UART7 PE8/PE7; UART5 PB13/PB12 or PC12/PD2; USART3 PD8/PD9 (if the camera leaves it); USART2 PD5/PD6; UART4 PD1/PD0. **Never** USART1 (PA9/10, PB14/15), USART2 PA2/3 or USART3 PB10/11 (loader ports, F10) | keep USART6 |
| GNSS_TP_MCU | PD14/61 (TIM4_CH3) | timer CH inputs: PD12–15, PB6–9, PC6–9, PB0/1, PB4/5, PA6/7, PE9/11/13/14, PB10/11, PB3, PA15, PB14/15. Not TIM5 (servos) | **H0: PD15 (TIM4_CH4)**. Never pulled down |
| GNSS_RESET_N | PC8/65 | open-drain GPIO; not PA14, not loader-driven | **H0: PD14** |
| VBUS_SENSE | PD15/62 (EXTI15) | any FT GPIO input | move to the forward face (PD2/83) |
| CAM_MCU_TX/RX | PB10/46, PB11/47 (USART3, a loader port) | UART7 PE8/PE7; UART4 PB9/PB8, PD1/PD0, PC10/PC11; USART2 PD5/PD6; UART5 PB13/PB12, PC12/PD2; USART3 PD8/PD9 | **H0: UART7 PE8/PE7** |
| CAM_UART_OE, CAM_PWR_EN | PC13/7, PD3/84 | GPIO out, low in reset (pull-downs) | flexible |
| CAM_FAULT_N, BAT_FAULT_N, LOGIC_SOURCE_ST, USB_FAULT_N | PD4/85, PD0/81, PD1/82, PD6/87 | GPIO inputs, distinct EXTI lines (bench firmware 4/0/1/6) | flexible; best on the face toward their part |
| PULLPIN | PC14/8 (EXTI14) | FT GPIO (off-board through R160/D122) | flexible |
| LED_YEL / LED_RED | PE7/37, PE8/38 | any GPIO that can source about 8 mA (not PC13–15) | **must move for H0** (to PA4/PA7, "no signal that matters at reset", or forward/east pins with the LEDs relocated) |
| BUZZ_DRV | PA5/29 (TIM2_CH1) | any GPIO, low in reset (R163); a software square wave is allowed (frozen) | move toward Q123 (forward-west): PD7/88 or PD2 |
| VLOGIC_SENSE, V3V3_SENSE, CAM_5V_SENSE | PC2_C/17, PC3_C/18, PB1/35 | ADC pins: PA4/PA7 (PA6 loader-driven ✗); 17↔18 swap | little freedom; dividers can sit anywhere |
| SPI1 (IMU) | PB3–5/89–91 | SPI3 PB3–5 (AF6/6/7) or SPI6 (AF8) on the same pins; SPI1/6 PA5–7; SPI2 PB13–15; SPI3 PC10–12 | keep PB3–5 at the current rotation |
| IMU_CS | PB7/93 | GPIO out + 10 k pull-up | flexible |
| IMU_INT1 | PE1/98 | any GPIO (polled) | **contract** U1.98 (PE10/PE0 must stay NC) |
| I2C1 (baro) | PB8/95, PB9/96 | I2C1 PB6/PB7; I2C4 PB6–9 (AF6) or PD12/PD13; I2C2 PB10/PB11; I2C3 PA8/PC9 (loader) | flexible |

## 5. Candidate placements: crossings and rat's-nest length

The annulus model counts pairwise inversions of pin order against destination angle, minimised over the cut. It
overcounts destinations stacked radially, so compare rows, not absolute values. Lengths are octilinear flylines
wrapped around U1's body. Signals that dive inward (QSPI under U1, NRST, pyro senses) are excluded from the crossings.
Non-RF pins in the optimised rows come from a local search, so they are indicative only.

**Floorplans compared:**
- **fp_k0** = the R7 positions with four changes: the QSPI flash on B.Cu under U1 (six inward dives), J2 moved to the
  west edge beside J3, the camera eFuse and buck moved beside J9, and the LEDs moved to the east edge (fp_k0b).
- **fp_k0c** = fp_k0b with the IMU/baro block moved west-forward (x 11–16, y 64–70).
- **fp_k1b** = fp_k0b with U1 rotated +90° (pins 51–75 aft), J3/J2 on the west edge beside U1's aft-west corner, and
  IMU_INT1 movable (a contract edit).

| # | U1 | Pins | Floorplan | Crossings (all U1 nets) | RF crossings | Flyline | 2-layer maze, unrouted / vias (all U1 nets) |
|---|---|---|---|---:|---:|---:|---|
| A | as R7 | R7 | R7 | 351 | 19 | 1652 mm | 15 / 73 |
| B | as R7 | H0 only | R7 | 320 | 0 | 1612 | 9 / 83, all RF routed |
| B′ | as R7 | H0 + optimised rest | R7 | 274 | 0 | 1576 | — |
| C | as R7 | R7 | fp_k0 | 220 | 19 | 1469 | 11 / 73, radio 1 unrouted, 12 vias (S6) |
| D | as R7 | H0 + optimised | fp_k0b | 133 | 0 | 1381 | 8 / 64; radio 4 vias, GNSS 2 (S10) |
| **E** | **as R7** | **H0 + optimised** | **fp_k0c** | **117** | **0** | **1329** | — |
| F | +90° | H0/H1 + optimised | fp_k1b | 171–192 | 0–1 | 1231–1360 | — |
| G | as R7 | H3 (SPI4) + optimised | fp_k0b | 111 | 1 | 1330 | — |

**Reading the table:**
- **Pins alone are not enough.** B/B′ cut crossings by 9–22 % and fix the RF order, but the forward tangle remains:
  imu×servo 20, camera×servo 20, camera×pyro 16, imu×pyro 15.
- **Placement alone is not enough either.** C still has 19 RF crossings, and in the maze the radio still needs its
  vias.
- **Together they cut crossings by 62–67 % and flyline length by 16–20 %** (D/E).
- **The +90° rotation (F)** gives the shortest flylines. It puts the servos and pyro pins forward, the camera UART
  east, and R7's SPI2/USART6/QSPI-IO pins aft. It costs relocating USB-C and the SWD pattern to the aft-west edge,
  moving IMU_INT1 (a contract edit) and re-homing the baro, and it showed **no crossing advantage** in these runs. The
  current orientation is the better base.

## 6. Recommendations (connectivity view, for the placement and pin plan)

1. **Keep U1's orientation.** Put the whole RF interface on U1's SW corner with **pin map H0** (0 RF crossings, strict
   except one exception). This needs:
   - the SPI2 SCK alternate on PB10 and NSS on PB11 (exception to frozen §3.10 PB10/PB11 "Avoid", argued in §3);
   - IOSWP;
   - NRST PE9, DIO1 PE15, BUSY PD8 and RXEN PD9;
   - GNSS RESET_N PD14 and TP PD15;
   - camera UART to UART7 PE8/PE7;
   - LEDs, VBUS_SENSE and the buzzer moved off PE7/PE8, PD15 and PA5.

   REQUIREMENTS F10's pin text, check_r7's RF contract and the binding notes must change with it. If IOSWP is
   unavailable, this costs 1 crossing.
2. **Open a straight path from U1's SW corner to the strip mouth.**
   - Move C84 and C80/C96 off the west face.
   - Move the west input cluster (U9, D8, D9, the damper, BAT_IN_F, R80/R165) next to J1. This also shrinks the BAT_SW
     harness lines from 129/160 mm to a few mm and removes the full-length BAT_IN on In2.
   - Move U2/L1/U3/D9 out of the x 14–25, y 24–45 column.

   That gives radio lanes of about 32–49 mm going straight into the inter-module gap (x 16.4–24.9) and GNSS lanes of
   about 36–38 mm straight into U30's north edge, all on F.Cu over In1, with no corridor, band or split crossings.
3. **Take the QSPI flash out of the aft topology.** On the bottom under U1, six short inward dives never cross an
   outward bus. Check the fit against Y1, the VCAP caps and the decoupling; a WSON-8 W25Q128 is smaller. BK1 cannot
   gather CLK and IO2 elsewhere on LQFP100.
4. **Untangle the forward zone by block order, not pins.** The servo pins are pinned at the aft end of the east face,
   and the IMU bus is on the forward face.
   - Put the IMU/baro west-forward of the servo header, or the header and D121 east-forward of the IMU (E: −16
     crossings).
   - Put R150–R157 and D121 between U1's east face and J122.
   - Put U7/U8/L3 beside J9.
   - Move J2 west beside J3; NRST dives under U1.
5. **Contiguity rule for the layout and the pin plan:** on each face, aft-going pins sit at the aft end and
   forward-going pins at the forward end, in the destination order of §2. VBUS_SENSE inside the GNSS group (R7) is the
   pattern to avoid.
6. **Not recommended:**
   - SPI4 for the radio (E2 hazard), unless the owner accepts a GPIOE_LCKR-before-SPI4 rule. Geometrically it is no
     better than H0.
   - Moving the servo or pyro pins.
   - Rotating U1 for its own sake.

## 7. Open checks (before any binding)

- Re-read DS12110 Table 10 for PB10 SPI2_SCK AF5, PB11, PD15 TIM4_CH4 and PE7/PE8 UART7 AF7.
- Re-read RM0433 for SPI_CFG2.IOSWP.
- Re-read AN2606 Table 135 for the PB10/PB11 loader behaviour with NSS held high.
- Check the flash-under-U1 fit and the decoupling impact.
- The maze is F/B-only with no power copper or lane-order awareness. Treat its via counts as relative.
