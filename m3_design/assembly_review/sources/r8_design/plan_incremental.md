# R8 Strategy A: incremental (fixed placement, pin swaps, nudges, clean re-route)

Planning note for the R8 synthesis step. Base board: R7 `m3_design/assembly_review/m3.kicad_pcb`, SHA-256 `c872a3d3…`
(branch m3-assy-r7, commit 431025d). The repository was only read; it is unchanged (git status clean, SHA re-checked).
Prototype work is in `r8_design/incremental/` (scripts, scratch boards `a1`–`a3`, DRC reports, images in `img/`).

**Inference** marks anything that is not measured on a board, taken from a requirement, or read from a maker document
(AGENTS §2.5).

## 1. Verdict in one paragraph

Under R7's placement, with the H0 pin map and about ten small part moves, the radio interface becomes one straight
F.Cu bundle with **no vias**. I built it on a scratch copy and DRC-checked it: 0 clearance, short or crossing
violations, and every radio net connected (section 7). That one move removes the worst R7 compromise: 20 of the
45 allowlist entries and all 8 layer changes that had no GND via. With In2 kept for power only and every
other signal family rerouted cleanly by explicit geometry, Strategy A can plausibly reach an **empty or
near-empty allowlist and leftover list**, about 85–110 signal vias (R7 217), no signal copper on In2 (R7 901 mm) and
continuous reference planes. It keeps every qualification bound to placement (holes, outline, fit, vibration, RF strip copper,
pyro block, sled and tab data, BOM and cost). What it **cannot** fix is the placement-caused signal flow:
- the servo chain still runs forward to the resistors in the pyro block and back to J122;
- the camera supply still loops forward and back;
- the battery input is still split between J1 and the aft input chain;
- QSPI still needs B.Cu hops, the GNSS still takes the left-edge corridor, and SWD still crosses the board;
- the 7.7 A path still has no one-corner layout.

The route lengths that come from placement (S17 ≈ 2650 mm against a target of ≤ 2400) are therefore unchanged. Strategy A gives a large,
low-risk simplification, about index 30–45 against R7's 100, but not the "logical placement and signal flow" half of
the owner's goal. It is the right choice if the owner values keeping R7's qualifications, or as a fallback or stepping stone.
It is not the "absolutely perfect" end state.

## 2. What is frozen and what changes

**Frozen (byte-identical where it matters):**
- the outline (46 × 118), five M3 supports, tie holes, tooling holes and tab windows;
- every connector (J1, J2, J3, J9, J121–J124, J30/J31), U1 (position and rotation), U4/U5, C84, C121, the bucks, U9–U13, Q120/Q121, both modules;
- the RF strip's qualified copper: both GCPW lines and launches, ESD, bias tap, pi networks, limiter, module-local copper,
  launch cut-outs, U30/U31 keep-outs;
- the CH1 pyro block and its internal copper (CH1_PADS and the PYRO_BLOCK rectangle unchanged);
- HSE copper; In1 as solid GND with no tracks;
- the BOM (no new or removed part, no new LCSC code: 52/52 extended unchanged).

**Changed:** the U1 pin map (section 3); about ten small parts moved by 0.3–3 mm or flipped/relocated locally (section 4); the In2 plan
(section 5); and every signal route outside the strip and the block, plus the power hookups and stitching (section 6).

## 3. Pin changes (U1, STM32H743VIT6 LQFP100)

H0 from the connectivity survey, plus the moves it forces. Alternate functions come from ST's CubeMX pin database (`connectivity/h743_af.json`).
Verify against DS12110 Table 10 before binding.

| U1 pin | Port | R7 net | Strategy A net | Why |
|---|---|---|---|---|
| 46 | PB10 | CAM_MCU_TX | RADIO_SCK_MCU (SPI2_SCK AF5) | radio lane order with 0 crossings |
| 47 | PB11 | CAM_MCU_RX | RADIO_NSS (GPIO) | NSS between SCK and MOSI |
| 53 | PB14 | RADIO_MISO_MCU | RADIO_MOSI_MCU (SPI2, IOSWP) | MOSI east of MISO at U31 |
| 54 | PB15 | RADIO_MOSI_MCU | RADIO_MISO_MCU (SPI2, IOSWP) | as above |
| 55 | PD8 | RADIO_BUSY | RADIO_BUSY | unchanged |
| 56 | PD9 | RADIO_NRST | RADIO_RXEN | lane order |
| 39 | PE9 | NC | RADIO_NRST | east-most lane; TT pin, on-board only |
| 45 | PE15 | RADIO_RXEN | RADIO_DIO1 (EXTI15) | lane order |
| 51, 52, 57 | PB12, PB13, PD10 | radio | NC | freed |
| 61 | PD14 | GNSS_TP_MCU | GNSS_RESET_N (open drain) | GNSS lane order |
| 62 | PD15 | VBUS_SENSE | GNSS_TP_MCU (TIM4_CH4 capture) | GNSS lane order |
| 63, 64 | PC6, PC7 | GNSS UART | unchanged (USART6) | — |
| 65 | PC8 | GNSS_RESET_N | NC | freed |
| 37 | PE7 | LED_YEL | CAM_MCU_RX (UART7_RX AF7) | the camera leaves the loader port USART3 |
| 38 | PE8 | LED_RED | CAM_MCU_TX (UART7_TX AF7) | as above |
| 28 | PA4 | NC | LED_YEL | LED lanes go straight aft-east to R33 |
| 31 | PA7 | NC | LED_RED | to R32 |
| 83 | PD2 | NC | VBUS_SENSE (EXTI2) | forward face, toward R9/R110 |
| 88 | PD7 | NC | BUZZ_DRV | forward face, toward Q123/R162 |
| 29 | PA5 | BUZZ_DRV | NC | freed |

**Optional moves** (each saves a B.Cu hop; decide during routing):
- BAT_FAULT_N PD0 → PE11 (41) and LOGIC_SOURCE_ST PD1 → PE12 (42). Both escape inward under U1's body to B.Cu.
  Their EXTI lines become 11 and 12, so the EXTI15_10 handler must check pending bits (a firmware binding note).

**Unchanged by contract:**
- pyro gate, continuity and arm-sense pins (3, 15, 33, 34) and the sentinels 2, 4, 5, 16, 32;
- servos PA0–PA3 (22–25);
- PE10 and PE0 stay NC, IMU_INT1 stays on PE1;
- QSPI, USB, SWD, HSE, NRST and BOOT0.

**Owner and record items:**
- the REQUIREMENTS F10 pin text;
- `check_r7.RF_MCU_PINS`, `FREED_NC` and `PULLS`;
- an exception to frozen-design §3.10 "avoid PB10/PB11", argued as for PB14/PB15 in R7 (the pin becomes an output only after
  USART3 is selected, which needs 0x7F on PB11 = NSS held high by its pull-up);
- the F10 EXTI note: DIO1 moves to EXTI15 and VBUS_SENSE leaves line 15;
- the firmware binding.

**SPI_CFG2.IOSWP is an Inference** (RM0433 not re-read). Without it, MOSI and MISO cross once at the SW corner. That costs one
2-via B.Cu hop with GND vias, or keeping R7's MOSI/MISO pin roles and accepting the crossing.

## 4. Part nudges (the whole list)

All moves are small, use parts already on the board, and need no new code.

| Ref | R7 | Strategy A | Reason |
|---|---|---|---|
| D9 (SMA, top) | (16.0, 31.2) | (15.2, 31.2) | widens the D9–U3 gap to 4.3 mm for the radio bundle |
| U3 flash (SOIC-8, top) | (24.6, 34.0) | (26.6, 34.3) | same gap; the +0.3 mm in y clears D122's courtyard |
| C29 (U3 VCC decoupling) | (19.2, 36.5) | (22.6, 38.15), at U3.8's north end | out of the bundle; still ≤ 2 mm from U3.8 with a direct route (`check_r7`) |
| C82 (1210, RAW_PROTECTED bulk) | top (14.95, 40.35) | bottom (15.0, 42.7) | frees the SW-corner merge; 2.7 mm deep, like the other bottom 1210s |
| R89 (BAT_FAULT_N pull-up) | top (12.8, 43.1) | top (14.0, 40.5), rot 90 | out of the wrap-lane corner |
| R313 (SCK 33 Ω) | bottom (5.7, 44.0), in the old corridor | top (19.6, 41.9), inline on SCK | driving end (`SERIES`); F.Cu, no vias |
| R315 (MOSI 33 Ω) | bottom (5.2, 42.0) | top (15.0, 44.3), inline on MOSI | as above |
| R310 (NSS 100 k pull-up) | top (24.2, 20.8), in the strip | top (18.4, 41.5), at the MCU end | removes 3V3_RADIO's run across U31's north side, which blocks DIO1 and NRST; **one-net schematic change: its rail becomes 3V3 instead of 3V3_RADIO** (same rail upstream of FB31) |
| R306 (GNSS RXD 220 Ω) | bottom (2.2, 47.5) | unchanged | stays in the GNSS corridor; nearer U1 than U30 |
| R120 (ACT_GATE pull-down, bottom) | (5.6, 96.0) | about 1 mm east | widens Q120's source-row neck (ACT_FET_S); keep rule H's 1.0 mm (ACT_GATE pads to live pads) |
| U1 pins 48–50 (copper only) | aft fan-out vias at y 44.25 | vias under U1's body at (15.85, 47.6), (16.85, 47.6), (16.35, 48.5), 0.5/0.3 mm | frees the strip under the aft face for the wrap lanes |

**Not moved:** the servo resistors R150–R157 and D121 (in the pyro block), U7/U8/L3, the input cluster
(U9/D8/C80/C96/damper), J2, the IMU and the QSPI flash's side. Moving them is placement work (section 13).

## 5. Layer plan

| Layer | Role in Strategy A | Change from R7 |
|---|---|---|
| F.Cu | Primary signal layer over In1. All critical buses run here where they can: radio, USB, QSPI CLK, IMU/I2C to the via, pyro gate exit, servo PWM to D121, the strip-side GNSS. Top-part power hookups. | Carries the radio bundle; no more band or corridor via columns. |
| In1 | Solid GND, **no tracks** (as R7). No via columns closer than 0.9 mm pitch, so no merged antipads. | The 16 slots (P3b) go to about 4–6: the band/corridor columns at x 9.4/10.0 are gone. |
| In2 | **Power only, 0 signal tracks.** Regions: GND in the strip (F10) and in a left-edge column x 0.5–6 under the GNSS corridor (y 23.5–60); a BAT_IN column x 6.5–12 from the J1/Q120 corner to U9/D8/C80/C96; a 3V3 core x 12.5–40, y 23.5–70 under U1, QSPI, IMU and every B.Cu critical run; a 3V3A island at C10/C11; a CAM_5V column x 40.5–45.5; local RAW_ACT under J122 and ACT_FET_S under Q120–Q121 (7.7 A paralleling); GND everywhere else. | R7 has 901 mm of signal track on In2 and only 51 % pour coverage. This turns In2 into real planes, with split edges only where no B.Cu critical run crosses. |
| B.Cu | Secondary signal layer: QSPI hops under U1, IMU and I2C runs to U4/U5, camera UART to U12, servo in the block, SWD under U1, pyro senses under U1, harness lines along the left edge. Bottom-part power. | Each B.Cu critical run lies over one In2 region (3V3 or GND), never across a split. |

## 6. Family-by-family routing

Lengths are R7 copper → Strategy A estimate (radio measured on the prototype).

| Family | R7 | Strategy A | Plan | Simple? |
|---|---|---|---|---|
| Radio, 10 nets | 510 mm / 24 vias (+8 layer changes with no GND via) | **366 mm / 0 vias (prototype, measured)** | One F.Cu bundle from the SW corner through the D9–U3 gap into the module gap; NRST round U31's east side, DIO1 down to pin 20 (section 7) | **Yes** |
| GNSS, 5 nets | 208 / 8 | 185–200 / 8, each with a GND via | H0 order (RESET_N, TP, RXD, TXD) under C84's body to vias at about (9–11.5, 44.6–46); 4-lane B.Cu corridor at x 1.5–4 over In2 GND; up to F.Cu at y about 25; peel off to R305, U30.3, R307 and U30.9. No crossings; vias spaced for GND vias | Clean, not direct |
| QSPI, 6 | 151 / 11 | 135–150 / 10 | CLK straight F.Cu from pin 36 into U3's north entrance (0 vias). IO0/IO1/IO3 (west face), IO2 (pin 1) and NCS (pin 92) each go down to B.Cu under U1 over the In2 3V3, then back up north of U3 and into the pad inner ends between U3's columns. B.Cu kept off the buck (L1 sits under U3) | Clean; 2 vias per line remain |
| IMU + baro, 7 | about 190 / 7 | 170–185 / 7 | One via per line just forward of U1's forward face (with GND vias), B.Cu to U4/U5 over the In2 3V3; the IMU and barometer no-copper rules kept. Fixes R7's 20.3 mm unreferenced SPI1_SCK | Yes |
| Servo, 8 | 435 / 28 (251 mm on In2) | 300–330 / 4 | Four F.Cu lanes from the east face, east then forward under C121's body (between its pads, x 30.2–35.6) to D121; one via each; B.Cu to R150–R157 in the block, then back to J122's THT pins | Clean; the overshoot stays (placement) |
| Camera, about 8 | 349 / 32 | 200–230 / 6–8 | UART7 pins 37/38 escape inward to B.Cu, then a straight run to U12 (bottom); CAM_PWR_EN and CAM_FAULT_N on F.Cu from the forward face; RAW_PROTECTED to U7 as a 1 mm B.Cu run; CAM_5V on the In2 column | Clean; the supply loop stays |
| Status and harness | about 530 / 40 | 330–380 / 10–14 | BAT_SW_SOURCE/RETURN as two straight B.Cu lines along the left edge (MST-bound, about 85 + 95 mm); LEDs, buzzer and VBUS_SENSE short after the pin swaps; PULLPIN and NRST take one B.Cu hop under the servo lanes | Clean; long lines stay |
| SWD + NRST | 163 / 12 | 125–140 / 6 | SWDIO/SWCLK go under U1 on B.Cu from the NW corner to its east side, then F.Cu forward to J2. Retires the J2.1 in-pad 3V3 via (an M2 named exception) | Clean; the crossing stays |
| Pyro exits, 6 | 253 / 18 (131 mm on In2) | 190–210 / 6–8 | PYRO1_GATE_N on F.Cu from pin 3 under C121, ≥ 0.5 mm from the servo lanes (review rule, Inference), entering the block at its R7 entry point. CONT, ARM1 and RAW_ACT senses on B.Cu under U1 with GND vias | Clean |
| USB | 70 / 7 | 55–60 / 2–4 | Pair on F.Cu over In1 from J3 to pins 70/71, with a via stub to D4 (bottom) per line. Fixes R7's 18 mm USB_DM over the In2 gap | Yes |
| Power hookups | 21 allowlist entries (chain detours, hops, VCAP detours) | 0 target | Straight hookups on the In2 regions; VCAP1/VCAP2 via under U1 (VCAP1 ≈ 3 mm, under the 2 mm detour slack) | Yes |
| 7.7 A corner | necks 3.00 / 2.65 / 3.82 mm, 38 / 44 / 30 °C | ≈ 10–20 °C each (**Inference**, IPC fit with an assumed layer share) | ACT_GATE off In2 (local B.Cu): the BAT_IN In2 arm widens to about 6 mm. In2 ACT_FET_S island with via fields at both source rows, and R120 nudged. In2 RAW_ACT island under J122, fed by a via field at the F.Cu arm. The F.Cu path stays | Better; P1-9's one-corner layout not met |

The GNSS corridor, QSPI hops, SWD crossing and servo overshoot are the costs of the fixed placement. None needs a
gated exception: each keeps its ratio under 1.6× MST and its vias at or below need + 2, and every critical layer change gets a GND via.

## 7. Key-move prototype: the radio interface under R7's placement

**Method.** These scripts are reproducible and run on a scratch copy only:
- `incremental/proto_lanes.py` applies the section 3 pin map and the section 4 nudges, rips the
  affected nets, re-escapes pins 48–50 inward and draws the U1-side bundle as explicit 0/45/90° geometry, 0.15 mm wide.
- `incremental/proto_strip.py` draws the strip-side lanes, moves R310 and re-feeds FB31 from a via at (35.1, 23.95). It
  also clears the 13 strip stitching vias that sat in the new lanes; the stitching stage re-places them.
- DRC: `kicad-cli pcb drc` on `incremental/a3/m3.kicad_pcb`.

**Geometry.**
- **Aft-face lanes.** NRST (pin 39) runs straight aft at x 21.35. DIO1, SCK and NSS jog east by 45° below the pins, and SCK
  passes through R313.
- **West-face lanes.** MOSI, MISO, BUSY and RXEN exit west under C84's body, turn aft at x 13.2–12.3, run east at
  y 44.3–42.6 (MOSI through R315) and drop at x 17.0–15.95.
- **Gap.** All eight converge by staggered parallel 45° jogs to a 0.35 mm pitch (x 18.9–21.35) through the D9–U3 gap.
  Clearances: RXEN 0.375 mm to D9.2, NRST 0.525 mm to U3.8.
- **Module gap.** SCK, NSS, MOSI, MISO (to R314) and BUSY turn east into U31's west pins as nested L's. RXEN runs to R312
  and pin 10 under the module's south edge.
- **North and east.** DIO1 turns east at y 24.6 to pin 20. NRST turns east at y 25.0, comes down at x 40.2 outside
  C310–C312, then goes west to R311 and pin 3.
- **Fence.** The radio crosses it in one 2.4 mm opening (x 18.6–21.0), plus single-lane openings at x 32.4 and 40.2.

**Result.**
- DRC on the prototype has 0 clearance, short, crossing, courtyard, hole or mask violations. All radio nets are connected
  (0 radio unconnected items).
- What is left is expected leftovers of the scratch rip-up: 3 dangling tracks, 2 dangling vias, and silk items on moved
  parts. The unconnected 3V3 items (C29, U3.8, R89, R310, FB31's new via) need the redrawn In2 3V3 plane.

| | R7 | Prototype |
|---|---|---|
| Radio interface copper (10 nets) | 510.4 mm | 365.7 mm |
| Vias | 24 (8 with no GND via) | **0** |
| Layers | F + B corridor + band | F.Cu only, over In1 |
| Longest line | NRST 85.4 mm / 4 vias | RXEN 59.0 mm, NRST 55.5 mm |

Images: `incremental/img/r7_radio.png` (R7: west escape, left-edge B.Cu corridor, F.Cu band) and
`incremental/img/a3_radio_wide.png` / `a3_radio.png` (Strategy A).

**Not prototyped:**
- the GNSS corridor (R7 already carries 12 lanes there; 4 in order is easier);
- QSPI, IMU, servo, camera, SWD and the 7.7 A corner.

**Tried and abandoned:**
- A Freerouting F/B-only run of the whole ripped board (`incremental/fr/`) stalled at 120–131 unrouted with 353
  "violations". Most come from GND pads that lost their outer-pour connection and from the router's pyro class
  clearance against the fixed copper. It is a setup artefact, not evidence about routability, so it is not used here.

## 8. Expected metrics against the R7 baseline

Estimates come from the family table (section 6), the prototype and the survey's MST data. Ranges show the uncertainty.

| ID | Metric | R7 | Proposed target | Strategy A (expected) | Met? |
|---|---|---|---|---|---|
| G | gate (DRC, parity, ERC, route_check, check_r7/actuators, fit) | 0 | 0 | 0 | yes |
| C1 | route_check instances in gated categories | 74 | 0 | 0–2 | likely |
| C2 | information-only instances | 252 | ≤ 100 | 90–130 | borderline |
| C3 | allowlist entries | 45 | 0 | 0–1 (A8 only, unless the TP122 edit is approved) | likely |
| C4 | leftovers | 29 | 0 | 0–4 | likely |
| C6 | AGENTS §3 instances | 9 | 0 | 0–1 (A8) | likely |
| S1 | signal track | 3355 mm | ≤ 2700 | 2500–2750 | borderline / likely |
| S4 | signal layer-change vias | 217 | ≤ 110 | 85–110 | likely |
| S6 | detour ratio, length-weighted | 1.396 | ≤ 1.20 | 1.12–1.18 | likely |
| S7 | excess over MST | 1081 mm | ≤ 450 | 350–450 | likely |
| S8 / S9 | nets > 1.6× / > 2.0× | 23 / 12 | 0 / 0 | 0–2 / 0 | likely |
| S10b | signal bends | 648 | ≤ 400 | 420–480 | not quite |
| S12 / S13 | critical layer changes / with no GND via | 73 / 8 | ≤ 35 / 0 | 31–36 / 0 | yes / borderline |
| S15 | signal track on In2 | 901 mm | ≤ 300 | 0–30 | yes |
| S16 | track on In1 | 0 | 0 | 0 | yes |
| S17 | Σ MST (placement) | 2727 mm | ≤ 2400 | about 2650 (pins only) | **no** |
| P1 / P3b | In1 coverage / slots | 0.880 / 16 | ≥ 0.90 / ≤ 4 | 0.89–0.90 / 4–6 | borderline |
| P4 / P6 | In2 regions / split edge | 8 / 1581 mm | ≤ 5 / ≤ 900 | 7–8 / 950–1100 | **no** (more power regions, fewer voids) |
| P7 | outer GND islands on ≤ 1 via | 32 | 0 | 0–4 | likely |
| P9 / P10 | GND-via distance p95 / max | 6.1 / 13.8 mm | ≤ 4 / ≤ 8 | 4.0–4.5 / 8–10 | borderline |
| R1 / R3 | unreferenced critical length | 60 / 116 mm | ≤ 5 / ≤ 15 | ≤ 5 / ≤ 15 | likely |
| R5 | `critical_reference` unreferenced | 27.9 % | ≤ 10 % | 8–12 % (own antipads count) | borderline |
| D_min | smallest 7.7 A neck / 20 °C width | 0.50 | ≥ 1.0 | 0.9–1.1 (Inference) | borderline |
| Index | simplicity index (R7 = 100) | 100 | — | 30–45 | — |

## 9. Requirements and safety rules at risk, and how each is protected

**Pyro and arming (AGENTS §2.1–2.4, F8, DRC A–H)**
- The block and its internal copper are untouched, so `CH1_PADS`, the PYRO_BLOCK rectangle, `DRU_SHA` and `PYRO_RULE_SHA` stay
  valid.
- The exits are rerouted. Re-measure rule F (R7: 0.503 mm against SERVO4_MCU's via, which goes away) and rules B, C and E.
- Keep PYRO1_GATE_N ≥ 0.5 mm from servo PWM over its shared run under C121. This is a review rule, not a DRC rule (Inference).
- A8 (TP122's in-pad gate via) stays unless the owner approves a small edit inside the block: a gate via 1.5 mm from TP122 with its
  own GND via, a B.Cu stub to the pad, then local DRC and leakage re-measurement.
- No test pad on BUS, IGN or OUT; TP122 stays on the bottom.

**Actuator switch (§2.2, `check_actuators` ACT_NETS)**
- Every net is unchanged. ACT_GATE moves off In2 to local B.Cu.
- Keep ACT_GATE/ACT_DRV pads ≥ 1.0 mm from live pads (rule H) when R120 moves.

**MCU pin contracts**
- The pyro, servo and sentinel pins and PE10/PE0 are unchanged. `check_actuators` re-runs unchanged.
- F10's radio/GNSS pin text, `check_r7` RF_MCU_PINS / FREED_NC / PULLS (R310's rail) and the EXTI note change. All need
  owner sign-off, plus the PB10/PB11 §3.10 exception and the IOSWP check.
- No RF-part pin touches a safety net: the move adds no such connection (`check_r7` pad-level test).

**F10 RF strip**
- GCPW, launches, limiter and module copper are kept, so no field-solve rerun is needed.
- The strip still holds only allowed nets on F.Cu. `STRIP_B` / `STRIP_VIA` can be **tightened**: RADIO_DIO1, RADIO_NSS and
  RADIO_TXEN drop out of the regex, except TXEN's strip-internal B.Cu hop, which stays unless redrawn.
- `FENCE_OPENINGS` change: one 2.4 mm radio opening (narrower than R7's 4.4 mm), one-lane openings at x 32.4 and 40.2, and the
  GNSS entry. Re-run `rf_stitching`, `rf_gnd_reach` (4 mm) and `module_ground`. The 13 removed stitching vias are re-placed beside
  the lanes.
- The radio SPI lanes sit in the module gap as in R7: SCK is 5.2 mm from U30's edge, data lines 4.1–4.8 mm, quasi-static lines
  3.4 mm. Re-measure against the 5 mm "fast digital line" rule and pass2_rf §3.10's quasi-static carve-out; MISO/MOSI may need
  that argument or a 0.5 mm shift east.
- The bundle crosses over the bottom-side 3V3 buck with In1 in between. Acceptable (Inference); record it for review.

**Other requirements**
- **M2 clean routing:** the target is an empty allowlist and empty leftovers. The J2.1 named exception retires; TP122's in-pad
  via stays (a bare contact).
- **F4 7.7 A:** a new DC solve and neck analysis are required. The rise is improved but P1-9 is not fully met, so it needs an
  owner threshold or acceptance (section 10).
- **P2 fit and supports:** holes and heavy parts are unchanged. The moved parts are low; C82 on the bottom is 2.7 mm (≤ 3.0 mm
  sled rule). Re-run `fit_check`, which changes nothing material.
- **P3:** IMU and barometer no-copper rules kept, so the IMU B.Cu runs approach U4 from outside its areas. Coating mask
  unchanged.
- **M1 / M3:** no new part or code; the BOM is unchanged except R310's net. Re-run `jlc_cost.py` only for the fab refresh.
- **Hot-plug model (F9, M3_R4 X1/Y1):** still strained, because the input parts stay 70–85 mm from J1. Narrowing BAT_IN to an In2
  column changes the path inductance slightly. Add the board path to the model (Inference) or rely on the bench hot-plug test.

## 10. Requalification

| Item | Needed? | What |
|---|---|---|
| F4 DC solve (`tools/dc_solve.py`) | Yes | All three 7.7 A paths and the logic, camera and 3V3 rows, on the R8 board. About 40 min at 0.05 mm; quick mode `DC_GRID=0.1` |
| IPC-2152 neck estimate | Yes | Rebuild the cut analysis (the survey's `baseline/dc_neck.py` already reproduces R7's necks). Get a new owner decision, or a requirement threshold such as ≤ 20 °C at the baseline fit |
| Critical-reference sampling | Yes, new metric | The "lost vs R6 + 18 mm" metric is meaningless. Use an absolute metric on R8 (survey R1/R3 + `critical_reference.py` self); target ≤ 10 % unreferenced, list every unreferenced run |
| Pyro spacing | Partly | DRC A–H and `check_actuators` re-run; re-measure exit clearances. Internal block distances and ORDERING's coating and leakage figures unchanged (unless the A8 edit is made) |
| Fit (`fit_check`) | Automatic | Unchanged in substance |
| RF | Partly | `check_r7` with edited fence openings and tightened regexes; stitching and reach review around the new lanes; separation review (section 9). No field solve, VNA model or S21 geometry change |
| Mechanical / vibration | No | Holes, outline and heavy parts unchanged (moved parts < 0.1 g, Inference) |
| ORDERING | Small edits | DFM query list (J2.1 via gone); bottom-part list (C82); probe points, tabs, tooling holes, sled and washer data unchanged |
| REQUIREMENTS / VEHICLE | Text edits | F10 pin contract and EXTI note; F4 (R8 solve); M2 (exceptions, acceptance line); P1 unchanged; VEHICLE unchanged |
| Firmware binding | Yes | New pin table (H0, IOSWP, UART7 camera, LED/buzzer/VBUS_SENSE pins, EXTI map) |
| Deviation list | Rebuilt | From empty; whatever remains needs a dated owner acceptance |
| Review loop | Yes | Independent passes until 0 Critical / 0 Major with the gate at zero (project rule) |

## 11. Implementation in the scripted build

**Recommendation:** a new chain that starts from the committed R7 board, as R7 started from R6. Do not stack stages
on top of `r7_build.sh`'s patch chain: most of R7's routing stages would build copper that R8 then deletes.

```
m3_design/r8_build.sh
  git restore R7 board (431025d, SHA check c872a3d3)
  r8_sch.py     U1 pin nets (section 3), R310 rail; schematic and PCB kept in sync (parity)
  r8_place.py   the section 4 moves, as an explicit table (fixed KIIDs)
  r8_rip.py     delete every non-frozen signal and power-hookup track and via (keep list: strip RF copper, block internals,
                HSE, In1); one explicit keep-list, asserted by SHA of the kept copper
  r8_route_*.py one module per family (rfif, gnss, qspi, imu, servo, camera, status, swd, pyro_exits, usb, power),
                explicit lane geometry like proto_lanes.py/proto_strip.py, connectivity checked after each module
  r8_power.py   In2 region polygons, 7.7 A paralleling islands and via fields, ACT_GATE local route
  r8_stitch.py  GND vias at every critical layer change (reuse r7_hygiene.gnd_spots), pour-island stitching, strip
                fence and stitching re-cut (reuse r7_route's fence code with new openings)
  r8_post.py    silkscreen and legends (reuse r7_post), refill, save
  tools/check.sh with check_r8.py (check_r7 + new constants), route_check with empty ALLOWLIST/LEFTOVERS
```

**Determinism:** fixed geometry, fixed KIID seeds, no autorouter, as in R7. Every stage is byte-reproducible.

**Check-code edits,** each a reviewed and recorded change:
- `check_r7`: RF_MCU_PINS, FREED_NC, PULLS (R310), STRIP_B/STRIP_VIA, FENCE_OPENINGS;
- `route_check`: ALLOWLIST/LEFTOVERS emptied;
- `check_actuators` and `fit_check`: no change.

**Measurement:** `r8_design/baseline/run_survey.sh` gives the scorecard and index on each candidate. Run it with
`NO_DC=1 NO_GATE=1` during iteration and in full before review.

## 12. Effort

| Phase | Work | Agent-days |
|---|---|---|
| 0 | Owner decisions: H0, the PB10/PB11 exception, IOSWP check, R310 rail, nudge list, In2 power-only plan, 7.7 A threshold | owner checkpoint |
| 1 | `r8_sch.py`, check-code edits, binding notes | 0.5 |
| 2 | `r8_place.py`, `r8_rip.py` with keep-list asserts | 0.5 |
| 3 | Family routing: radio (prototype exists), GNSS, QSPI, IMU, servo, camera, status, SWD, pyro exits, USB, power hookups | 3–5 |
| 4 | In2 plan, 7.7 A paralleling, stitching, fence | 1 |
| 5 | Gate to zero, DC solve and necks, critical reference, scorecard | 1 |
| 6 | Independent review passes (2–3) and fixes | 2–3 |
| 7 | Records (M3_R8, R8_VALIDATION, REQUIREMENTS edits, ORDERING, STATUS), fab export and binding | 1 |
| | **Total** | **about 9–12 agent-days**, 2–3 weeks with owner checkpoints |

**Risk to schedule.** The most likely trouble spots are the U1-underside B.Cu traffic (QSPI, SWD, senses, camera UART and pins
48–50 all under U1, among the bottom decoupling caps) and the east-face crossing set (servo wall against PULLPIN, NRST and
SWD). Both are local and have fallbacks of one extra via each.

## 13. What remains (honest list) and where Strategy A stops

**Compromises that remain** (none gated, all placement-caused):
1. **Servo overshoot.** R150–R157 sit in the pyro block (y 89–101) while J122 is at y 72–80, so about 150 mm of extra copper.
2. **Camera supply loop.** RAW_PROTECTED runs forward to U7 (about 90 mm) and CAM_5V back to J9 (about 60 mm, In2 column).
3. **Split battery input.** The BAT_SW lines (about 180 mm) and the full-length BAT_IN column remain; the hot-plug premise stays strained.
4. **GNSS corridor.** It goes through the left-edge B.Cu corridor with 8 vias, not a straight F.Cu path.
5. **QSPI hops.** Two vias on 5 of 6 lines: the flash is aft and IO0/1/3 are on the west face.
6. **SWD.** It crosses the board to J2 with 2 vias per line.
7. **7.7 A.** No one-corner layout; P1-9 (≥ 10 mm equivalent, mirrored on L1/L4) not met. The necks improve to about ≤ 20 °C (Inference).
8. **Mechanical items unchanged.** The forward-rail dependency for panel tabs (no long-edge window forward of y 71.5), the IMU
   13 mm off the roll axis, and the board length of 118 mm.
9. **A8** (TP122 in-pad gate via), unless the small in-block edit is approved.
10. **In2 regions.** More power regions (7–8) than the ≤ 5 target, because power cannot move to shorter paths.

**Optional "A+" moves** cut items 1–3. They are placement moves of passive or small parts, outside "keep every footprint", with the RF strip,
pyro block, holes and connectors still fixed. They are Strategy B's territory:
- R150–R157 and D121 to between U1's east face and J122: saves about 150 mm and makes servo flow straight;
- U7/U8/L3 and their capacitors beside J9: removes the camera loop;
- the input cluster (U9, D8, C80/C96, damper, R80/R165) beside J1: restores the hot-plug premise, shortens the BAT_SW lines
  to a few mm, removes the full-length BAT_IN, and frees the aft band;
- the QSPI flash on the bottom under U1: one via per line.

With them, S17 approaches the survey's 1329–1381 mm floorplans (E/D), which strict Strategy A cannot reach.

## 14. Checks before binding anything

- DS12110 Table 10: PB10 SPI2_SCK AF5, PB11, PD15 TIM4_CH4, PE7/PE8 UART7 AF7, PE9 (TT), PA4/PA7 LED drive.
- RM0433: SPI_CFG2.IOSWP.
- AN2606 Table 135: PB10/PB11 loader behaviour with NSS held high by its pull-up.
- R310 on 3V3 instead of 3V3_RADIO: confirm NSS stays high while the MCU is in reset and the radio is powered (same rail upstream
  of FB31; Inference).
- pass2_rf §3.10: MISO/MOSI at 4.1–4.8 mm from U30 (section 9).

## Files

- `r8_design/plan_incremental.md`: this plan.
- `r8_design/incremental/proto_lanes.py`, `proto_strip.py`: the radio key-move prototype (pin map, nudges, lanes).
- `r8_design/incremental/proto_rip.py`, `fr/`: the abandoned whole-board Freerouting feasibility attempt.
- `r8_design/incremental/a3/m3.kicad_pcb`, `a3/drc.json`: prototype board and DRC report (scratch only).
- `r8_design/incremental/img/`: renders (`r7_radio.png`, `a3_radio_wide.png`, `a3_radio.png`, `a2_band.png`, the power-corner
  layers `pc_F/B/In2.png`, `east_F.png`).
- `r8_design/incremental/render.py`, `netlen.py`, `crt.py`, `pads_in.py`, `chan.py`, `u1map.py`: helper scripts (KiCad Python, read-only on the input board).
