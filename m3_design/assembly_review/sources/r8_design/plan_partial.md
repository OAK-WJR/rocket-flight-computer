# R8 Strategy B: partial re-placement and a full signal re-route

Board under study: R7 (`m3_design/assembly_review/m3.kicad_pcb`, SHA-256 `c872a3d3…`, branch `m3-assy-r7` @ `431025d`).
The repository was only read. All prototype work is in `r8_design/partial/`.

## 0. Verdict

**Strategy B is feasible, and it removes almost all of R7's structural compromises.** Three changes do most of the work:

1. **Turn U1 by −90° (KiCad rotation 0).** Pins 51–75 then face the RF strip, pins 1–25 face forward (servos, pyro gate and continuity), pins 26–50 face east (camera, LEDs, status), and pins 76–100 face west (IMU, barometer, SWD).
2. **Move the RF pins to the H0 map.** With the turned MCU, the radio and GNSS lanes leave U1 already in the order the modules need.
3. **Give every block a home on the face of U1 it talks to,** and route everything from scratch on a stated layer plan: In1 solid GND, In2 planes only, F.Cu for signals, B.Cu for crossovers and the bottom parts.

The fixed items all stay exactly where they are, and so do their check constants: the RF strip (modules, jacks, RF chains, limiter, fence), the CH1 pyro block, J1, J122, the five M3 holes and the two tie holes. **`check_actuators.py` needs no edit at all** (pyro, servo and sentinel pins, the `PYRO_BLOCK` rectangle and the `CH1_PADS` geometry are unchanged), and `fit_check.RETENTION_HOLES` and VEHICLE's hole coordinates stay valid.

**Evidence from the prototype, on a scratch copy of R7 (§11):**
- **Placement:** all 249 parts placed legally. The only courtyard or keep-out flags left are two that R7 already carries (J9's body edge, J122 to its tie hole). `tools/fit_check.py` passes, and C84's bore margin rises from 0.11 to 1.37 mm.
- **Ratsnest:** the octilinear MST of the non-pour nets drops from 2727 mm (R7) to **1785 mm (−35 %)**.
- **RF interface:** routed as two buses (GNSS 4 lanes, radio 8 lanes; the first chip-select layout came out at 0.2 mm lanes on a 0.6 mm pitch).
  - Copper: **≈ 370 mm with one new signal via** (the NSS pull-up tap). R7: ≈ 720 mm, 32 vias, of which 8 have no GND via.
  - It is DRC-clean under the project's `m3.kicad_dru`.
  - route_check finds only cosmetic artefacts of the quick script (§11).
- **RF separation:** every RF part stays ≥ 5.04 mm from U1's courtyard (R313 and R315) and ≥ 5.39 mm from switching-regulator parts (R313 to C73; FB31 to L3, 5.57 mm).

**What remains** is a short, honest list (§6):
- one inherent strip item (RADIO_TXEN's loop round U31);
- two inherited limiter detours, which disappear if the limiter's DC copper is redrawn;
- the part-limited ACT_FET_S pad neck at 7.7 A;
- a handful of layer changes that the topology forces, each with a GND via: ARM1_SENSE under U1, the USB-C pair join, the servo crossover, the QSPI and HSE dives, the sensors on the bottom.

**Owner decisions required:**
- the new MCU orientation and pin map (F10's pin contract text, `check_r7` RF contract, firmware binding);
- the frozen §3.10 "avoid" list for PB10/PB11 and PE14 (or PE9);
- optionally, two label-only contract edits that save servo vias (§5.4).

**Effort:** about 10–16 agent-days to a gated, reviewed board (§10).

## 1. What stays fixed and why

| Item | Kept as | Why | Check code affected |
|---|---|---|---|
| RF strip, y 0–23.5 | Rigid copy of R7: J30/J31, both modules, ESD, bias tee, pi networks, limiter under U30, GCPW lines, launch cut-outs, keep-outs, stitching beside the RF lines | Keeps the pass-2 field solve (50.3 Ω, launch 49 Ω), the stitching gaps quoted in F10 and the S21 isolation geometry | `JACKS`, `U31_BODY`, `MODULE_GND`, `STITCH_ACCEPTED` unchanged |
| Module interface leads inside the strip | Redrawn from the strip mouth to the module pads. These are control and data lines, not RF lines | They must match the new lane positions | `FENCE_OPENINGS` (new: GNSS x ≈ 6.5–15.3, radio gap x ≈ 20–25, DIO1 x ≈ 32.4–33.0, NRST x ≈ 40). `STRIP_B`/`STRIP_VIA`: drop RADIO_DIO1, add 3V3_RADIO (R310's feed); RADIO_NSS stays, for the R310 tap |
| CH1 pyro block | Rigid **and unmoved**: J124, J121, Q124, R126–R134, R173, R175, R178, R180, C126–C129, D120, TP122, their copper and their exit vias | Keeps R4's tuned spacing (rule H 1.025 mm, rule F 0.503 mm), `CH1_PADS`, the `PYRO_BLOCK` rectangle and ORDERING's coating rationale | None (`check_actuators` 15b passes as is) |
| J1 (23, 110.4) rot 180 | Unchanged | Owner's 25 mm battery and CH1 grouping; entry faces forward | None |
| J122 (23, 75.7) rot 90, tie holes (21.5, 68.6) and (27, 82.6) | Unchanged | Axis band; `fit_check.RETENTION_HOLES` | None |
| Five M3 holes | Unchanged | VEHICLE stack row, sled, vibration model | None |
| IMU U4 and barometer U5 | Bottom side, rotation 0 | R5 axis map (roll = +gyro_Y) | None (the `IMU_*`/`BARO_*` rule areas move with the parts) |
| Outline 46 × 118 mm, stack-up, BOM | Unchanged; no new part | M1, M3 (52/52 extended codes) | None |

## 2. Floorplan

Board coordinates: x 0 is the left long edge, y 0 is the aft edge (SMA jacks), y 118 is the forward edge (J1). Every
position below is taken from the legalised prototype (`partial/b0_place_final.tsv`, which seeds an `r8_place.tsv`).

```
y 118 ┌──────────────────────────────────────────────┐
      │ D8 C89/C95 (B) R166(T) │ J1 (T)  │ C80/C96 D9 C82 (B) │  battery band (In2 BAT_IN)
      │ gate drive Q122.. (B)  │ Q120/Q121 (B, stacked) │ U9 + network, TPs (B)
y  84 │ J124 ─────── CH1 pyro block (T, rigid) ─────── J121 │
      │ C121 (T)               │ J122 (T)│ R150–153 (B)  │  servo/pyro zone (In2 RAW_ACT)
      │ J123, LS120 (T)        │         │ RAW_ACT_SENSE div (B) │
      │ U5, U4 (B)             │ D121 + pull-downs (T), servo vias │ C84 (T) / U11, U2, L1 (B)
y  54 │ J2 (T)                 │  U1 rot 0 (T), U3 flash + Y1 under it (B) │ LEDs (T), U13 (B)
      │ J3 USB-C + U10 (T/B)   │                         │ J9 (T), U12 (T), camera supply (B)
y  24 │ ── GNSS lanes ──>      │ ── radio bus into the module gap ──  │ NRST/DIO1
y   0 │ U30  GNSS chain  J30   │      U31  radio chain  J31            │  RF strip (rigid)
      └──────────────────────────────────────────────┘
```

The bands, from the aft edge forward:
- **RF strip:** rigid.
- **MCU band:** U1 sits on the axis, rotated, with the flash and the crystal directly under it.
- **Servo/pyro zone:** J122, the servo interface, the pyro exits and the RAW_ACT plane.
- **Battery band:** J1, the actuator switch and the whole input chain.

The power and camera supplies sit in an east column next to J9 and C84. USB, SWD and the sensors sit in a west column next to the MCU faces that drive them.

### 2.1 Placement table (key parts; full list in `partial/b0_place_final.tsv`)

| Block | Parts and positions (x, y, rotation, side) | Rationale |
|---|---|---|
| MCU | U1 (23.0, 45.0, 0°, T). U3 flash (22.6, 43.2, 90°, B), under U1. Y1 (22.6, 49.9, B) under U1's forward face, with C25/C26 beside it. | All six QSPI signals become short inward dives; the crystal sits right under HSE pins 12/13; In2 keep-out under Y1 only |
| Decoupling | A row of 0402 caps along the bottom, just forward of U1 (C18, C14, C24, R168, C21 at y 54.6). C13, C15, C16, C17 at the four corners. C19/C20 (VCAP) at pins 48/73. C22, R164, C10, C11 (3V3A) at x 21–26, y 56–64. | Each at its pins; the servo via field (x 27–31, y 54–58) is kept clear |
| Sense dividers | R60/R61/C60 and R62/R63 under U1, next to pins 17/18. R168 at pin 15. R170 and R172 at pins 33/34 (B). | Divider nodes stay short; the long run is the low-impedance rail |
| RF interface resistors | R313 (SCK) (30.1, 30.4), R315 (MOSI) (28.9, 30.4), R306 (GNSS RXD) (18.9, 29.8), all F, 90°, inline in their lanes | ≥ 5.04 mm from U1's courtyard, still nearer U1 than the module (`check_r7.SERIES` passes) |
| USB and SWD (west) | J3 (4.6, 33.6, −90°, T). D4 flow-through ESD (11.0, 33.6, T). R7/R8 beside the CC pins. U10 and its network on the bottom at x 9–17, y 26–40. J2 (9.5, 42.6, −90°, T). | USB (pins 70/71) and SWDIO (72) leave U1's SW corner; SWCLK (76) is the W face's aft end |
| IMU and barometer | U4 (10.0, 53.8, 0°, B) and U5 (10.6, 60.2, 0°, B) with R11–R13, R64, C30–C32 | Nearest the W face's forward half (SPI1, CS, INT1, I2C1); far from the bucks. 13 mm off the roll axis, the same magnitude as R7 (see option O5) |
| West-forward | LS120 (11.8, 67.9, T). J123 (12.2, 75.4, T) with its network (B). C121 (13.0, 83.1, T), next to J124.2 (RAW_ACT). | Buzzer and pull-pin driven from W-face pins through a via each (their drivers are bottom parts anyway); C121 sits on the In2 RAW_ACT plane |
| Servo interface | D121 (T) and R154–R157 pull-downs (T) as dead-end taps at (26–31, 57–62). R150–R153 1k series (B) beside J122's east column (x 30, y 71.9–79.5). | Servo pins 22–25 point straight at J122 (§5.4) |
| Logic power (east) | C84 (37.0, 63.2, 90°, T), centre x within 7.4–38.6. U11 mux, U2 buck and L1 on the bottom underneath, with C5–C9 and R86–R91. | 3V3 enters In2 through a via field; ≥ 30 mm from the IMU and ≥ 5.5 mm from the strip |
| Camera (east) | J9 (42.7, 44.2, −90°, T). U12 (34.6, 45.4, T) right at UART7 pins 37/38, with R100/R101 (T) to J9. U7, U8, L3, C70–C77 (B) in signal-flow order, aft of J9. U13 LDO and C90–C92 (B) forward of J9. | Supply loop beside its connector (R7: CAM_5V ran y 33–107 on In2); UART buffer 4 mm from the MCU |
| LEDs | LED1/LED2 (43.6, 51.2 / 54.6, T) with R32/R33 | East face, top side |
| Actuator switch | Q120 (29.0, 103.9, 0°, B) and Q121 (29.0, 96.5, 180°, B), stacked between J1.1 and J122, sources facing each other. Q122, R120–R123, C120, TP121 west of them (B). | 7.7 A path J1.1 → Q120 → Q121 → In2 RAW_ACT → J122 is about 30 mm long (R7: ≈ 70 mm round the left edge) |
| Battery input | D8 (4.6, 105, B), C89/C95 (B) and R166 (8.0, 104.6, T) forward-west. C80/C96, D9, C82, R92, R167 (B) forward-east. U9 and its network at (39–45, 85–97, B). R80/R165 (T) at J1.3/J1.4. | All within ≈ 30 mm of J1, tied by the In2 BAT_IN band. This restores the R4 hot-plug model's premise (R7 had these parts 70–85 mm from J1) |
| Tooling holes TH1–TH3 | Removed | Standard PCBA does not need them; frees tab-rule space (ORDERING and the fit_check board-feature list are updated) |

**Panel tabs.** A tab-window scan of the prototype (1.5 / 5 / 2 mm rules) finds the whole left edge clear from y 41.5 to 117.5 and the right edge clear from y 0.5 to 25. That allows three left tabs (for example y 45, 75 and 100) and two right tabs aft. R7 found nothing forward of y 71.5 and needed JLC's forward rail.

Moving the forward-east test-pad column (TP80–TP89) 3 mm inboard would also open a right-edge window around y 73–84, and is planned. **Inference:** JLC accepts 3 + 2 tabs for a 118 mm board; check this at quote.

## 3. MCU orientation and pin map

**U1 turned to KiCad rotation 0** (checked in pcbnew): pin 1 at (−6, +7.55), pin 51 at (+6, −7.55), pin 76 at (−7.55, −6).
- **Forward face:** pins 1→25, west to east.
- **East face:** pins 26→50, forward to aft.
- **Aft face:** pins 51→75, east to west.
- **West face:** pins 76→100, aft to forward.

| Signal | R7 pin | R8 pin (port) | Face | Change | Flags |
|---|---|---|---|---|---|
| RADIO_SCK_MCU | 52 PB13 | **46 PB10** (SPI2_SCK AF5) | E (aft end) | yes | Frozen §3.10 "avoid PB10/PB11" (USART3 loader). Same no-contention argument as R7's PB14/PB15: PB10 drives only after USART3 is detected, which needs 0x7F on PB11, held idle-high by R310 |
| RADIO_NSS | 51 PB12 | **47 PB11** | E | yes | As above |
| RADIO_MOSI_MCU | 54 PB15 | **53 PB14** | Aft | swap | Needs SPI_CFG2.**IOSWP** (Inference, check RM0433). Without it, one MOSI×MISO crossing costs 2 vias |
| RADIO_MISO_MCU | 53 PB14 | **54 PB15** | Aft | swap | As above |
| RADIO_BUSY | 55 PD8 | 55 PD8 | Aft | – | Polled (EXTI8 shared, as F10 already allows) |
| RADIO_RXEN | 45 PE15 | **56 PD9** | Aft | yes | Low in reset (R312) |
| RADIO_NRST | 56 PD9 | **44 PE14** (or 39 PE9) | E | yes | PE14 is loader SPI4 MOSI, an input under the loader, so R311 keeps the radio in reset. PE9 is TT, which is fine on-board. Either sits on a frozen "avoid" line |
| RADIO_DIO1 | 57 PD10 | **45 PE15** (EXTI15) | E | yes | VBUS_SENSE leaves PD15/EXTI15 |
| GNSS_RESET_N | 65 PC8 | **61 PD14** | Aft | yes | Open drain |
| GNSS_TP_MCU | 61 PD14 | **62 PD15** (TIM4_CH4 AF2) | Aft | yes | Check DS12110; capture, never EXTI |
| GNSS_RXD_MCU / TXD_MCU | 63 PC6 / 64 PC7 | unchanged | Aft | – | USART6 kept |
| CAM_MCU_TX / RX | 46 PB10 / 47 PB11 | **38 PE8 / 37 PE7** (UART7 AF7) | E | yes | Leaves a loader port; removes the camera's DFU-hijack path |
| VBUS_SENSE | 62 PD15 | **65 PC8** (or 66 PC9) | Aft (SW) | yes | Goes west with the USB lanes; EXTI8 then serves VBUS and BUSY is polled |
| USB_FAULT_N | 87 PD6 | 66 PC9 or 81 PD0 | Aft/W | yes | Toward U10 at J3 |
| LOGIC_SOURCE_ST, BAT_FAULT_N | 82 PD1, 81 PD0 | 28 PA4, 29 PA5 | E (forward end) | yes | Toward U11 (east) and U9 (along the east edge); PA4/PA5 are inputs, "no signal that matters at reset" |
| CAM_UART_OE, CAM_PWR_EN, CAM_FAULT_N | 7 PC13, 84 PD3, 85 PD4 | 31 PA7, 41 PE11, 42 PE12 | E | yes | Pull-downs hold OE and PWR_EN off in reset; PE11/PE12 are loader inputs only |
| LED_YEL / LED_RED | 37 PE7 / 38 PE8 | 39 PE9 / 43 PE13 (or 30 PA6) | E | yes | A loader-driven pin can only blink an LED during DFU |
| BUZZ_DRV, PULLPIN | 29 PA5, 8 PC14 | 88 PD7, 86 PD5 (FT) | W | yes | Toward Q123 and J123, west-forward |
| Unchanged (contract) | | PE4/3 gate, PC0/15 continuity, PC5/33 arm sense, PB0/34 RAW_ACT sense, PA0–PA3/22–25 servos, sentinels 2/4/5/16/32, PE1/98 INT1, PE10/40 and PE0/97 NC, QSPI, USB, SWD, HSE, NRST, BOOT0, SPI1 PB3–5, IMU_CS PB7, I2C1 PB8/9, sense ADCs 17/18/35 | | – | `check_actuators` untouched |

**Topology result (annulus model of the connectivity survey, `partial/model/bplans.py`):**
- this map with this floorplan: **51 crossings, 932 mm of flylines, 0 RF-internal crossings**;
- R7: 351 crossings, 1652 mm;
- the survey's best variant E (R7 orientation, re-placed blocks): 117 crossings, 1329 mm.

The survey's own +90° run (171–192 crossings) kept R7's IMU, servo and pyro destinations. With the blocks re-homed to match the turned MCU, the turn wins clearly.

**Checks before binding:** DS12110 Table 10 for PB10 AF5, PD15 AF2, and PE7/PE8 AF7; RM0433 for IOSWP; AN2606 for PB10/PB11 with NSS held high and for the PE14 state; EXTI-line sharing; F10's EXTI note, rewritten.

## 4. Layer plan

| Layer | Content | Rules |
|---|---|---|
| F.Cu (L1) | Top parts. All critical buses: RF interface, USB, SWD, camera UART, IMU SPI up to its drop vias, pyro and servo lanes near U1. Short power stubs. GND fill, stitched. | Referenced to In1. 0.2 mm signal lanes at a 0.5–0.6 mm pitch where space allows (R7 used 0.15/0.15): robustness margin |
| In1 (L2) | **Solid GND, no copper of any other net**: antipads only, no via columns | Target coverage ≥ 0.90, ≤ 4 slots |
| In2 (L3) | **Planes only, no signal track:** GND under the strip (y 0–23.6) with In2 GND under the launch cut-outs; **3V3** from y 23.9 to ≈ 66.8 (MCU, sensors, interface, camera logic; In2 keep-out under Y1); **RAW_ACT** from y ≈ 67.2 to 102.2, x 5.5–36.5 (J122, C121, J124.2, Q121's drain via field); **BAT_IN** band y ≈ 102.6–117.7 under J1 (Q120's drain, D8, damper, C80/C96, U9, R80). GND in the forward corners outside these. | 4–5 regions with straight splits, no B.Cu critical signal crossing a split. Pyro vias through the RAW_ACT plane keep rule A (0.5 mm) or E (1.0 mm) antipads |
| B.Cu (L4) | Bottom parts. Crossovers: QSPI and HSE dives under U1, NRST dive, ARM1_SENSE dive, the pyro exits from the block's vias, the servo crossover, IMU/barometer drops. Medium-current power: RAW_PROTECTED and BAT_FAULT_N along the east edge, VBUS/USB_LIMITED, VLOGIC. GND fill, stitched. | Under U1, B.Cu runs over a continuous In2 3V3 reference |

Rules that apply to every layer:
- **GND vias:** every critical layer change gets a GND via within 1.5 mm, placed by the generator (§9).
- **Stitching:** a GND stitching grid at a ≤ 4 mm pitch outside the parts, so that every outer GND island has at least 2 vias.

**7.7 A copper:**
- **BAT_IN:** J1.1 to Q120's drain on B.Cu, a few mm, plus the In2 band.
- **ACT_FET_S:** Q120 S to Q121 S, about 1.6 mm apart, flooded on B.Cu.
- **RAW_ACT:** Q121's drain into a field of ≥ 30 vias (0.3 mm) to In2 RAW_ACT (MARGIN P1-9's fallback: a parallel via field confined to the battery corner). The plane carries the current to J122. J122's THT pins join In2 directly, so the column-neck problem of R7 (2.9–3.0 mm between pin columns) goes away; F.Cu and B.Cu column strips add to it.

## 5. Routing plan: what becomes simple

All numbers marked **(proto)** are measured on `partial/proto/m3_b0R.kicad_pcb`; the rest are estimates.

### 5.1 RF interface (proto)

**GNSS:**
- 4 lanes from aft-face pins 61–64 run straight aft, take one 45° fan to x ≈ 18.3–20.1, go aft, then turn west at y 25.9–27.7 and drop into R307, U30.3, R305 and U30.9.
- RESET_N 23.8 mm (ratio 1.10), RXD 8.9 + 19.9 mm (R306 inline), TP 26.0 mm, TXD 27.2 mm.
- **0 vias** (R7: 208 mm, 8 vias, a left-edge B.Cu corridor).

**Radio:**
- 4 aft-face lanes and 2 east-face lanes (NSS, SCK) merge into one 6-lane bus at a 0.6 mm pitch, with R313 and R315 inline. The bus takes one 45° run into the gap between the modules (lanes at x 20.6–23.6) and peels off east into U31.15→11. RXEN continues round the south edge.
- DIO1 goes straight down to U31.20, and NRST round the east to U31.3 through R311.
- Total 259 mm, max ratio 1.30.
- **1 signal via:** the NSS tap to R310, which moves to B.Cu under the lane; its 3V3_RADIO side becomes a B.Cu run to FB31, so DIO1 can stay on F.Cu.
- R7: 512 mm, 24 vias, 8 without a GND via.

The FB30 and FB31 3V3 feeds take one via each into In2 3V3.

### 5.2 QSPI flash, crystal and debug

- **QSPI:** six inward dives (pad, then F.Cu under the body, then a via, then B.Cu to U3), 5–9 mm each: about 50 mm and 6 vias. R7: 151 mm, 11 vias. The QSPI no longer encloses any outward bus.
- **HSE:** 2 dives to Y1 directly under pins 12/13 (< 4 mm each).
- **NRST:** a dive to C24, then B.Cu under U1's NW quadrant to J2.3. **SWDIO and SWCLK:** F.Cu 6–9 mm to J2, 0 vias. R7: 163 mm, 12 vias for SWD.
- **USB:** pins 70/71 run to D4 (flow-through) and J3, about 14 mm. 2 vias are inherent to the USB-C A6/B6 and A7/B7 pin interleave.

### 5.3 Sensors

IMU (SPI1, CS, INT1) and barometer (I2C1) run from the W face to drop vias next to U4 and U5: 5 + 2 vias, the minimum for a top MCU and bottom sensors. 3V3A runs on F.Cu along the forward face from R164/C10/C11 at the VDDA pins to U4/U5 (the W-face pins that go forward are all west of it).

### 5.4 Servo

Pins 22–25 point at J122. The lanes are about 4 × 25–30 mm (R7: 435 mm, 28 vias, 251 mm on In2).

**Topology facts, checked on the prototype:**
1. U1 numbers its pins anticlockwise and J122 numbers rows 1/4/7/10 anticlockwise along the outer column, so any single-layer bundle between them must fully reverse (R7's crossings are inherent).
2. A top-side SRV05-4 has the wrong handedness for dead-end taps from the U1-ordered bundle.

**Options:**
- **(a) No contract edit:** F.Cu from the pins, a staggered 4-via crossover onto B.Cu (the series resistors are on the bottom, so each net needs a via anyway), plus D121's taps through 4 more vias. **8 vias.**
- **(b) Recommended:** relabel D121's four identical I/O channels (`check_actuators` pass-5 line "pins 1/3/4/6 on SERVO1–4"). D121 and the pull-downs become planar dead-end taps on F.Cu: **4 vias.**
- **(c)** Additionally reverse the J122 row mapping (`check_actuators` rule 7 and the silkscreen numbers): everything on F.Cu, **0 vias.** Not recommended: it adds churn for 4 vias.

### 5.5 Pyro

The block exits stay as they are (rigid): the GATE_N via (23.0, 88.33), the CONT via (28.4, 88.61) and the ARM1_SENSE via (18.18, 91.30).
- **GATE_N and CONT:** B.Cu lanes west of J122 (x ≈ 16.8–18.4, clear of the aft tie hole) to vias at pins 3 and 15, each with a GND via.
- **ARM1_SENSE (pin 33, east face):** it is the one inherent crossover. B.Cu under U1 (a dive) to R170, 2–3 vias.
- **RAW_ACT_SENSE:** the divider sits on the RAW_ACT plane east of J122; a short sense lane runs to R172 at pin 34.
- **Total:** about 150 mm and 7–8 vias (R7: 253 mm, 18 vias), every layer change with a GND via.

### 5.6 Camera, power and status

- **Camera UART:** U1 → U12 → R100/R101 → J9, all top side, < 12 mm, 0 vias (R7: CAM_MCU_TX 66 mm, 5 vias).
- **Camera power:** CAM_PWR_EN and CAM_FAULT_N take one drop each to U7. CAM_5V stays local to J9 (R7: an In2 strip from y 33 to 107). RAW_PROTECTED runs from U9 down the east edge to the power and camera blocks: about 60 mm, straight (R7: a 120 mm tree with a 153 mΩ arm).
- **Battery switch:** BAT_SW_SOURCE and BAT_SW_RETURN shrink from 129/160 mm to a few mm (R80/R165 at J1.3/J1.4). BAT_ENABLE runs about 25 mm on F.Cu under J1's body to U9.
- **Status lines:** USB_FAULT_N and VBUS_SENSE are short (west); LOGIC_SOURCE_ST is short (east); BAT_FAULT_N is ≈ 60 mm, straight along the east edge.

## 6. Compromises that remain, with reasons

| Item | Status | Can it go away? |
|---|---|---|
| RADIO_TXEN loop round U31 on B.Cu (25 mm against a 10.9 mm MST; 2 vias) | Inherent | No. Pins 9 (south) and 19 (north) must be joined, and nothing may cross U31's pad field. The east route is as long. **One allowlist entry** |
| GNSS_LNA_EN and GNSS_VCC_RF detours (2.0×, 2.37×) | Inherited with the rigid limiter copper | Yes, by redrawing the limiter's B.Cu DC copper under U30 (not RF lines; field solve unaffected). **0–2 entries** |
| NSS → R310 tap via; 3V3_RADIO B.Cu hop in the strip | Forced by U31's pinout (DIO1/TXEN on the north edge between the SPI pins and pin 1) | No, but each is a legal layer change, with a GND via for NSS. `STRIP_B` edit |
| ARM1_SENSE crossover (pin 33 east, ARM exit west) | Contract pins plus the rigid block | Only by moving the ADC pin (a contract and sentinel change, not proposed) |
| USB-C pair join, 2 vias | Connector pinout | No |
| Servo crossover, 8 / 4 / 0 vias | Contract mapping | Option (b) or (c), §5.4 |
| ACT_FET_S neck at Q120/Q121's source pad rows (≈ 3.5–4.5 mm; B.Cu only, no other layer can join) | Part-limited (AON6403 PDFN source row) | No. Estimated rise ≈ 25–35 °C by the conservative no-plane-credit fit, against 44 °C in R7 (Inference until the DC/IPC rerun); still needs the owner's acceptance of the C1-type rise |
| IMU 13 mm off the roll axis (now on the west side; the lever-arm sign flips for any compensation) | Kept in the default | Option O5 (U4 near (23, 61)): about 0–2 mm, but it costs routing around the pyro lanes; prototype first |
| Pyro block exits keep their vias; the block's internal ARM1_SENSE In2 link (3.4 mm) stays on In2 | Rigid block | Redrawing that link on B.Cu is a block-internal copper change, kept out of scope |
| Long but straight lines: RAW_PROTECTED (≈ 60 mm) and BAT_FAULT_N (≈ 60 mm) | Geometry: J1 at the forward edge, U1 mid-board | No (ratio ≈ 1.1, not a detour) |

Expected exception count: **ALLOWLIST 1–3, LEFTOVERS 0, AGENTS §3 instances 0.** R7: 45 / 29 / 9–10.

## 7. Expected metrics against the baseline scorecard

The prototype measures placement and RF; every other number is an estimate from the floorplan and the per-family plan in §5.

| ID | Metric | R7 | B (expected) | R8 target | Basis |
|---|---|---:|---:|---:|---|
| C1 | Gated route_check instances | 74 | 1–3 | 0 | §6 |
| C2 | Info-only instances | 252 | ≈ 40–80 | ≤ 100 | Generator ends tracks on pad centres, merges collinear runs |
| C3 / C4 | Allowlist / leftovers | 45 / 29 | 1–3 / 0 | 0 / 0 | §6 |
| C6 / S13 | AGENTS §3 (no-GND critical layer changes) | 9 / 8 | 0 / 0 | 0 | GND vias by construction |
| S17 | Placement MST (non-pour nets) | 2727 | **1785 (proto)** | ≤ 2400 | b0_check.py |
| S6 | Detour ratio | 1.396 | 1.12–1.18 | ≤ 1.20 | RF proto: 1.06–1.30 |
| S7 | Detour excess | 1081 mm | ≈ 250–320 mm | ≤ 450 | MST × S6 |
| S1 | Signal track | 3355 mm | ≈ 1900–2200 mm | ≤ 2700 | |
| S4 | Signal layer-change vias | 217 | ≈ 50–70 | ≤ 110 | Family counts in §5 |
| S12 | Critical-signal layer changes | 73 | ≈ 26–32 | ≤ 35 | RF 3–6, QSPI 6, HSE 2, USB 2, IMU 5, pyro 7–8 |
| S10b | Signal bends | 648 | ≈ 300–400 | ≤ 400 | Buses: 3–5 bends per lane |
| S8 / S9 | Nets > 1.6 / > 2.0 ratio | 23 / 12 | 1–3 / 1–3 | 0 / 0 | TXEN, plus the limiter nets if not redrawn |
| S15 / S16 | In2 signal track / In1 track | 901 / 0 mm | ≈ 3 / 0 mm | ≤ 300 / 0 | In2 planes only (block-internal link) |
| P1 / P3b | In1 coverage / slots | 0.880 / 16 | ≥ 0.90 / ≤ 4 | ≥ 0.90 / ≤ 4 | No via columns; about 40 % fewer vias |
| P4 / P6 | In2 regions / split edge | 8 / 1581 mm | 4–5 / ≈ 600–900 mm | ≤ 5 / ≤ 900 | Straight splits |
| P7 | Outer GND islands held by ≤ 1 via | 32 | 0 | 0 | Stitching pass |
| P9 / P10 | Distance to nearest GND via, p95 / max | 6.1 / 13.8 mm | ≤ 3.5 / ≤ 6 mm | ≤ 4 / ≤ 8 | Grid at a ≤ 4 mm pitch |
| R3 | Extended set unreferenced | 115.9 mm | ≤ 15 mm | ≤ 15 | In2 3V3 continuous under all B.Cu critical runs |
| R5/R6 | `critical_reference` unreferenced share | 27.9 % | ≈ 5–8 % | ≤ 10 % | Own antipads only |
| D_raw | RAW_ACT neck | 3.00 mm | ≥ 6 mm (In2 plane ≥ 10 mm wide, plus B.Cu) | ≥ 5.3 | |
| D_bat | BAT_IN neck | 3.82 mm | ≥ 6 mm (In2 band plus B.Cu) | ≥ 5.6 | |
| D_fet | ACT_FET_S neck | 2.65 mm | ≈ 3.5–4.5 mm (part-limited) | ≥ 5.3 | §6 |
| — | RF separation (min) | 5.87 mm | **5.04 mm** to the MCU, 5.39 mm to a switching-regulator part (proto) | ≥ 5 | |
| — | C84 bore margin | 0.11 mm | **1.37 mm (proto)** | ≥ 0 | fit_check |
| — | Cost / extended codes | $105.98 / 52 | unchanged / 52 | ≤ $126.41 / 52 | BOM unchanged |

Simplicity index (geometric mean of the twelve I rows, R7 = 100): roughly 25–35. This is an estimate; it is recomputed with `baseline/run_survey.sh` on the built board.

## 8. Requirements and safety rules at risk, and how they are protected

| Rule | Risk under B | Protection |
|---|---|---|
| AGENTS §2.1 ARM break / F8 rules A–H | New neighbours of the block: Q120/Q121, RAW_ACT and BAT_IN copper under it (bottom and In2); pyro lanes rerouted | Block geometry unmoved (`CH1_PADS`, `PYRO_BLOCK`, `check_actuators` unchanged); DRC rules A–H on every layer including In2 antipads; exits re-measured (rule F was 0.503 mm against a SERVO4_MCU via: that via disappears). Coating and leakage distances re-measured, including the bottom face around TP122 (2.0 mm part keep-out kept) |
| §2.2 pyro bus after the load switch | None: nets unchanged | `check_actuators` 1–2 |
| §2.4 gate network | None: parts unmoved | — |
| Rule H for the actuator gate nets | Gate drive now next to the FETs and RAW_ACT pads | DRC rule H (1.0 mm); placement keeps the ACT_GATE pads off the drain side |
| F10 RF contract | Pin map rewritten; fence openings and `STRIP_B` change; R310 moves to B.Cu | Owner text edit of F10 and `check_r7` (RF_MCU_PINS, FREED_NC, FENCE_OPENINGS, STRIP_B/VIA). Strip RF copper rigid. Reset-hold (R311 on NRST) unchanged and re-argued for PE14 under the loader. No RF pin on a safety net (pad-level test re-run) |
| F10 ≥ 5 mm from switching parts, MCU, crystal and fast lines | Interface resistors near U1; camera buck aft-east | Checked on the prototype (≥ 5.04 mm to U1, ≥ 5.39 mm to the buck parts); USB lanes routed at y ≥ 35.8 so they stay ≥ 5 mm from R306 |
| F6 servo low in reset; F8 nothing fires at reset | Pin changes for LEDs, OE, PWR_EN, NRST | Every output that matters keeps its pull-down; loader-driven pins (PA6, PE13) only drive LEDs; contract pins unchanged |
| F9 hot-plug model | R7 violated its premise | Restored: TVS, damper, input caps and U9 tied to J1 by the In2 BAT_IN band. Bench test unchanged |
| P2 fit, supports, tie path | C84, J3 and J9 moved | fit_check OK on the prototype; holes and tie holes unchanged; bottom parts ≤ 3.0 mm deep (L1/L3 as before) |
| P3 no copper or vias under the MEMS on their side | Sensors moved | `IMU_*`/`BARO_*` rule areas move with U4/U5 (done in the prototype) |
| M1 / M3 | None | BOM unchanged; tooling holes removed (not BOM items) |
| M2 J2.1 in-pad via exception | — | Retired (no via in J2's pads) |

## 9. Implementation: a new reproducible build, not more patch stages

Patching R7's copper is what produced about 90 compromises, so R8-B is a fresh build from the R7 board and the netlist.

**Branch `m3-assy-r8b` from 431025d. `m3_design/r8_build.sh` runs:**
1. **`r8_sch.py`:** the MCU-sheet label edits for the §3 pin map (and the D121 relabel, if accepted); export the netlist; parity check.
2. **`r8_pcb.py`:**
   - restore R7 from git and check its SHA;
   - delete all copper except the frozen islands (strip RF copper, CH1 block interior) and all zones except the named rule areas;
   - apply `r8_place.tsv` (seeded from `partial/b0_place_final.tsv`);
   - run `r8_legalize.py` (a deterministic spiral legaliser, prototype in `partial/legalize.py`);
   - update footprint pad nets from the netlist;
   - In2 plane outlines, sensor rule areas, tooling-hole removal.
3. **`r8_route.py`:** deterministic copper from tables.
   - `bus(centerline, lanes, pitch)` with miter offsets (prototype in `partial/rf_route.py`);
   - explicit per-net polylines for the rest;
   - pad-centre endings and merged collinear runs, by construction;
   - a GND-via placer for every critical layer change;
   - power shapes and via fields; a stitching grid with keep-outs; zone fill.
4. **`r8_post.py`:** silkscreen (legends within 6 mm, designators), refill.
5. **`tools/check.sh`:**
   - `check_r8.py` (derived from `check_r7` with the constants above);
   - route_check with an empty allowlist plus the 1–3 measured inherent entries;
   - `check_actuators` unchanged; `fit_check` unchanged; DRC / ERC / parity.

**Non-gating report:** port `baseline/run_survey.sh` (with `survey_metrics.py`, `scorecard.py`, `dc_neck.py`) into `tools/` and run it after every build.

**Iteration loop (per the memory rules):**
- build → gate → scorecard → independent review, with a dedicated routing reviewer;
- every fix goes into the tables or the generator and the board is rebuilt; copper is never hand-patched afterwards;
- stop when there is no Critical or Major finding and the gate is at zero; record Minor items.

## 10. Requalification and effort

| Item | What to redo | Effort |
|---|---|---|
| Pin map | DS12110 / RM0433 / AN2606 checks, F10 text, `check_r7` contract, firmware binding notes | 0.5–1 day |
| Schematic, netlist, parity | `r8_sch.py` | 0.5 day |
| Placement detail | Under-U1 bottom (flash, Y1, 6 dives, decoupling vias, R170, dividers), servo interface, power block, silkscreen space | 1–1.5 days |
| Routing generator and tables | 135 signal nets, buses, stitching, pours, via fields | 3–5 days |
| Gate integration | `check_r8`, route_check entries, scorecard port | 0.5–1 day |
| **F4 DC solve and IPC-2152 necks** | `dc_solve.py` plus the survey's `dc_neck.py` (put into the repo): RAW_ACT, BAT_IN, ACT_FET_S and the logic rows. New C1-type owner acceptance for the part-limited ACT_FET_S neck | 0.5 day (≈ 45 min of compute) |
| Critical reference | Absolute metric on R8 itself (the R6 base is meaningless now) | 0.25 day |
| Pyro spacing | DRC A–H; exits; coating and leakage distances incl. the bottom face; R4 interior unchanged | 0.5 day |
| RF | `check_r7`/`check_r8` re-run; RF-part separations; control-line distances to U30 (lanes now enter U30's north edge directly); field solve and S21 unchanged (rigid strip) | 0.25 day |
| Fit and mechanical | fit_check (auto); vibration plate model re-run (C84, J3 and J9 moved; holes unchanged) | 0.5 day |
| ORDERING, REQUIREMENTS, VEHICLE text | Tab windows (forward rail no longer needed), probe points (NRST via C24.1 and its new neighbour, TP80, TP74/TP88), sled data, washer clearances, C121 staking sides, R8 coordinates in F4/F10/M2/M3/P1. The VEHICLE stack row is unchanged | 1 day |
| Review passes | 3–5 independent rounds to 0 Critical/Major | 2–4 days |
| **Total** | | **≈ 10–16 agent-days** |

Topology-based bench gates survive unchanged. The firmware binding is always new (AGENTS §3).

## 11. Prototype evidence (scratch only: `r8_design/partial/`)

**Files:**
- `model/bplans.py`: annulus/flyline model for U1 rotation and floorplan variants (the R7 baseline reproduces 351 / 1652).
- `b0_place.py`: placement table → `proto/m3_b0.kicad_pcb`.
- `legalize.py`: deterministic legaliser → `m3_b0L`.
- `b0_check.py`: courtyards, edges, R5 L10 keep-outs, RF separation, MST.
- `rf_route.py`: H0 pin map plus both RF buses → `m3_b0R`.
- `d121.py`: SRV05-4 tap handedness. `tabs.py`: tab-window scan.

**Results:**
- **Placement:** 0 new issues; R7-identical J9 body-edge and J122/tie-hole flags. `fit_check` OK: J9 mated 0.03 mm (unchanged), C84 1.37 mm, worst bottom 1.73 mm, nearest support clearances 4.70 mm (bottom) and 4.97 mm (top).
- **MST:** 2727 → 1785 mm (135 nets, before the pin swap; 1763 mm on the final routed copy, where the two LED nets have not been re-pinned yet). RF 557 → 371, servo 299 → 125, QSPI 131 → 47, IMU 157 → 92, USB/SWD 330 → 199, camera 325 → 200, pyro 212 → 219 (no gain: rigid exits plus the ARM crossover), other 714 → 531.
- **RF interface DRC** with the project rules: 0 copper violations on RF-interface nets. The one "unconnected" item is the 3V3_GNSS strip segment from C300 to FB30, which the copy filter dropped.
- **Placement polish left for the build's legaliser:**
  - KiCad's courtyard test flags 7 small touches that the prototype's area threshold ignored;
  - 12 test pads break their 1.0 mm local pad clearance;
  - one rule-H pair in the RAW_ACT_SENSE divider (C122 to R177).

  These are local nudges: the r8 legaliser models TP pad clearance and rule H.
- **route_check on the RF nets, quick-script artefacts that the generator removes by construction:**
  - collinear pieces not merged at the bus/peel-off joints;
  - one 0.1 mm miter segment (GNSS_TXD), which route_check counts as a short segment and a staircase;
  - a 0.15/0.2 mm width step against inherited strip copper;
  - the NSS tap via needs its GND via (room exists after R310 shifts 0.3 mm);
  - NRST takes a diagonal exit instead (route_check's redraw gives 33.8 instead of 36.6 mm).

**Not prototyped (risks):**
- the under-U1 bottom routing (flash, crystal and dives together);
- the servo crossover geometry;
- the pyro exits, ARM1_SENSE's dive, the power pours and the stitching;
- the DC numbers.

Each is argued in §5–§7 and is the first thing the build has to prove.

## 12. Owner decisions needed

1. **U1 at rotation 0 and the §3 pin map.** It rewrites F10's pin contract and `check_r7`, and needs exceptions to frozen §3.10 for PB10/PB11 and PE14 (or PE9). It also relies on IOSWP (if that fails: +2 vias).
2. **Servo option (b):** relabel D121's I/O channels (4 vias) instead of (a) with 8 vias. Option (c), the J122 row reversal, is not recommended.
3. **Remove the tooling holes.** Tab plan: 3 left plus 2 right, no forward rail.
4. **The allowed temperature rise at the part-limited ACT_FET_S neck**, after the DC and IPC rerun.
5. **Optional O5:** roll-axis IMU, if worth the routing cost; prototype first.
6. **Optional:** redraw the limiter's DC copper under U30, to remove the two inherited detour entries.
