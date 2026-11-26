# R12 vehicle integration handoff

**Status.** PCB `a9595a21953ed256c5652a7af35a12fc61a49039c90d9d8a3cdd6c84c2d4d3aa` (**SimpleFlight v1.0**: the M3-ASSY-R12 board, named on its silkscreen, D-R12-221, 2026-11-25; silkscreen-only change), 46 × 86.85 × 1.6 mm (D-R12-174; J122 a single-servo SH-4 since D-R12-195; round 13 fix pass D-R12-199 … -204; round 14 final fix pass D-R12-205 … -209: the J400 chatter bench rule is now **under 6.6 ms**; the Standard PCBA rebuild D-R12-211 … -219, 2026-11-24: U4 ISM6HG256X, U5 MS5611, U6 / C33 not fitted, the `RADIO` / `GPS` legends moved, copper identical to `c8b0412d…`),
four layers, every fitted part on the top face and assembled by JLC on **Standard** PCBA (D-R12-211; Economic before). R12 remains a CAD candidate, not accepted,
nothing ordered; R9 stays accepted. The rebuild's focused review (Fable 5.2, 2026-11-24: 0 Critical / 1 Major / 8 Minor, R12STD-REV-01 … -09) is corrected by D-R12-220 and its records pass; the Major was U4's axis map (now roll = **+gyro_Y**, see Board below); the full gate is pending. Current state: [M3_R12.md](M3_R12.md#current-state); owner items:
[R12_VALIDATION.md](R12_VALIDATION.md). No physical fit is claimed.

Coordinates are board mm: x east (0 … 46), y forward from the aft edge (0 … 86.85), top face F.
Current centres are `m3_design/r12_place.tsv` on `0c681ad6…` (Measured; placement unchanged since `96207d2e…`, the round
13 fix pass moved copper only: SERVO1_OUT / SERVO2_MCU at D121 and three second vias near C60 / C94, D-R12-199, -200;
the round 14 fix pass too: a GND via by R110 and a strap along U1's F row, D-R12-205; the Standard rebuild changed no
copper or placement, D-R12-211 … -219).
All positions below are on this board; figures labelled `c9b9f0fa…` were measured on round 12's board, whose copper and
placement differ from this one only at J122, the servo cells and those vias (D-R12-192, -195, -199, -200).
J1's terminal set the 86.85 mm outline (D-R12-174); round 12 adds R118 without moving existing parts.

## Harness pin map

Every contact of every port carries its own `n:NAME` legend, most of them on the **bottom** face along the contact's
column. The legends sit alternately inward and outward of the pad row (D-R12-80). **Wire from this table, and check
every lead's pin identity by continuity before first power.**

The SH contacts are numbered as on JST's SMnnB-SRSS-TB land (D-R12-31). The ports copy the MicoAir H743's SH port
orders, so one module lead fits either board; J122 copies its 4-pin UART port order (D-R12-195), so one servo lead
(signal and GND only; see the 5 V rule below) fits both boards. No source marks a pin-1 end: MicoAir's port images and
wiring diagrams (v1 and v2 agree) put GND at the same mouth-relative end of the GPS, UART / TELEM and ESC ports, and R12
makes that end pin 1. The orders stay an **Inference** until a real H743 lead is checked (O-R12-19).

| Port | Edge, mouth | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|---|
| J400 switch, SH-4 | aft, mouth aft; pin 1 at x 12.5, pin 4 at x 9.5 | SW (BAT_SW_SOURCE) | SW (BAT_SW_RETURN) | NC | NC | — | — | — | — |
| J122 servo signals, SH-4 (H743 UART order) | aft; pin 1 at x 26.1, pin 4 at x 23.1 | GND (signal reference; H743 GND) | NC (H743 **5 V**: must be empty on R12) | SERVO1 (S1; H743 TX position) | SERVO2 (S2, spare; H743 RX position) | — | — | — | — |
| J9 camera, SH-6 | aft; pin 1 at x 36.0, pin 6 at x 31.0 | CAM_5V (5V4) | CAM_5V (5V4) | GND | GND | board RXI (camera TX here) | board TXO (to camera RX) | — | — |
| J420 radio by default, SH-4 | forward, mouth forward; pin 1 at x 10.0 | GND | 4V8 (PORT_4V8) | board TXO (to module RX) | board RXI (from module TX) | — | — | — | — |
| J410 GPS by default, SH-6 | forward; pin 1 at x 20.5 | GND | 4V8 | board TXO | board RXI | NC (the H743's SCL) | NC (SDA) | — | — |
| J440 AUX spare, SH-4 | forward; pin 1 at x 33.0 | GND | 4V8 | board TXO | board RXI | — | — | — | — |
| J2 SWD, TC2030 pads (top, centre (32.8, 48.85), rotation 90) | — | 3V3 (33.435, 50.12) | SWDIO (32.165, 50.12) | NRST (33.435, 48.85) | SWCLK (32.165, 48.85) | GND (33.435, 47.58) | NC (32.165, 47.58) | — | — |

Pin data: `tools/check_r12.py` `SH_PORTS` / `TERMINAL_PINS`, D-R12-29 … -31.

- **Pyro terminal J121.** A black DORABO DB125-3.5-2P screw terminal at (7.4, 40.85); the wires leave west (D-R12-29).
  - Pin 1 (7.4, 39.1) is PYRO1_OUT, `E1−` (the side Q124 switches to GND).
  - Pin 2 (7.4, 42.6) is PYRO1_IGN, `E1+` (fed through R134 from the bus).
  - Its face is 3.40 mm in from the edge, giving 5.00 mm of bare-bore wire room against R10's 4.95 mm floor
    (Calculation on CAD envelopes).
- **Battery terminal J1** (D-R12-174): a blue Cixi Kefa **KF301-5.0-2P** screw terminal (LCSC C474881), 5.0 mm
  pitch, JLC THT assembly, at (7.4, 14.85), rotation 90; the wires leave **west**, as at J121.
  - Pin 1 (7.4, 17.35) is **BAT_IN (`1:BAT+`)**, pin 2 (7.4, 12.35) is **GND (`2:GND`)**; the contact legends and `BAT` are on
    the bottom; top `BAT+` / `GND` polarity words are beside their contacts (D-R12-181).
  - Its wire face is 3.60 mm in from the edge (x 3.6), giving 5.20–5.80 mm of bare-bore wire room against the 4.95 mm
    floor (fit_check r12, Calculation on CAD envelopes; the wire face's side is an Inference from the drawing's
    projection). Holes 1.30 mm finished for the 1.00 mm pins (Kefa drawing KF301-5.0 rev A: hole 1.20 +0.10).
  - The strip in front of the wire face (x < 3.6, y 9.7–20.0) holds no part.
- **Directions.** On J410, J420 and J440, pin 3 "board TXO" is driven by the board (PD8, PB13, PC6): wire the module's
  RX to it. Pin 4 "board RXI" is received by the board (PD9, PB12, PC7): wire the module's TX to it. **J9 is
  different:** pin 5 is board RXI and pin 6 board TXO. `5V4` is the camera supply from U403 (5.22–5.69 V initial,
  Calculation, conditional on U403 VIN ≥ VO / 0.75; low-input dropout estimate in M3_R12 "Power").
- **J9 needs both supply contacts and both GND contacts wired**, so the 1 A camera allowance is 0.5 A per contact
  (Calculation / Inference: load allocation and equal current sharing) against SH's 1 A rating (JLC listing, Live 2026-11-04).
- **J410, J420 and J440 carry the same supply and UART pin order.** The firmware port map defaults to GPS J410, radio
  J420, AUX spare. A device on these ports must drive its TX high at no more than 3.6 V.
  - Under the 0.561 A budget the port pins stay at or above 4.565075 V at the drift corner and at or below 4.972 V with no
    load (Calculation / Inference, D-R12-83): inside the LR900-F's 4.5–5.0 V (a project-record Inference; MicoAir's
    page gives only "5V DC") and the M100 Mini's 3.3–5 V. That holds while U400's input is at least VO / 0.75, about
    6.1–6.6 V (TI SLVSD90B §7.3, D-R12-131). During a four-stall fire (U400 VIN about 5.4893 V) or on a 6.0 V pack
    (about 5.4103 V) it rests on U400's frequency foldback, an Inference (M3_R12 "Power"; bench item R12_VALIDATION row
    15).
  - Before connecting a module, read PORT_4V8 at pin 2 of each port on pack power with the e-match disconnected. Expect
    4.60–4.94 V at room temperature (initial tolerance, Calculation).
- **Servo power from the harness (`SERVO + FROM HARNESS`).** J122 carries signals only: SERVO1 on pin 3, the spare
  SERVO2 on pin 4 and the signal GND on pin 1 (D-R12-195: one servo on flight 1; SERVO3 / SERVO4 are deleted). Servo motor power and return run in the pack-star harness, never through the board (REQUIREMENTS F4). R12's
  board does not print this note (D-R12-81, owner acceptance pending), so label the harness itself.
- **The servo lead is two wires, signal and ground; J122's position 2 is empty (D-R12-196).** J122.2 is the H743's 5 V
  position; R12 leaves it unconnected, 0.4 mm from GND (pin 1) and SERVO1 (pin 3). A lead built for an H743 UART port
  with its 5 V wire fitted would put the H743's 5 V there: one solder or debris bridge then shorts that 5 V through the
  lead (limited only by the H743's BEC; Inference), or pushes ≤ 2.05 mA into SERVO1's clamp (board on) / ≤ 5.3 mA
  through R150 (PA15 low, or board off) and loses servo 1's command (Calculation / Inference: 5.25 V assumed). So on
  R12: **crimp only GND (position 1) and the servo signal (position 3; position 4 only for a second servo); extract
  any 5 V contact, or cut its wire back and insulate it at both ends, joined to nothing.** The servo's own power stays
  in the pack-star harness. D-R12-193's VBAT rule for the SH-8 is superseded.
- **The same lead on the MicoAir H743 (D-R12-197).** Plug it into the H743's **UART4** port (west edge, GND / 5V / TX /
  RX on v1 and v2): position 3 is PA0, which our H743 firmware drives as **TIM5_CH1** (AF2; or TIM2_CH1, AF1), and
  position 4 is PA1, TIM5_CH2 / TIM2_CH2 for a second servo (DS12110 Rev 8 Table 10; pin map from ArduPilot's
  MicoAir743 / MicoAir743v2 hwdef). UART1 (PA9 TIM1_CH2 / PA10 TIM1_CH3) and UART6 (PC6 / PC7, TIM3 or TIM8) also work;
  on v2 UART5 (PB6 TIM4_CH1 / PB5 TIM3_CH2). Not UART3, UART7 or UART8. The ports' pin orders are read from MicoAir's
  images (Inference, O-R12-19).
- **SH harness.** These are SH 1.0 mm clones (Megastar ZX-SH1.0, D-R12-31). They have **no latch**: retention is
  friction only, accepted by the owner with the per-flight retention step below (O-R12-18). Mating with JST SH housings
  is an Inference until a sample check (O-R12-04).

## Power, arming and USB

R10's single-switch scope applies. The external screw switch on J400 is the power and pad-arming device, reachable on
the rail: on last, off first.

- Connect the e-match only with no USB and no self-powered module (GPS, radio, AUX or camera) attached.
- USB bench work needs the pack or the e-match disconnected.
- The ports are fed from the battery path, so they are off on USB-only power. PD10 (PORT_SENSE) reads low then.
- USB-only power needs at least 4.45 V at J3 (a host port or a powered hub, O-R12-03).

Further rules:

- **J400 is an SH-4 plug to the external switch**, using pins 1–2. D402 at (10.6, 7.8) clamps J400.2 to GND at the
  connector. Touching the airframe or pad ground before J400 stays the second ESD layer.
- **Dress the J400 pair** twisted, on its own ties, away from the battery leads and from J9's and J122's leads, which
  leave the same aft edge (R10's chafe rule).
- **J400 chatter (D-R12-183, -207; Calculation / Inference).** BAT_IN is a network with J1.1,
  U9.5, Q120.3 and R80.1 terminals. EN is evaluated at R80.1, not J1. At the four-stall GAP-1 point,
  with D-R12-219's unshed load (U2 input 2.4214 W; 2.4126 W under D-R12-207, 2.225 W before), J1 is 5.71364 V and R80.1 is
  5.69476 V (18.9 mV lower; 5.71390 / 5.69504 V before D-R12-219). Single drop-out immunity is 7.917 / 7.397 ms initial /
  drift; periodic limits are 7.365 / 6.890 ms (7.919 / 7.399 and 7.367 / 6.892 ms before D-R12-219).
  Whole-current loading gives J1 5.70141 V, R80.1 5.68194 V, fire current 1.24435 A and the worst
  periodic limit **6.794 ms** (6.796 ms before D-R12-219). The 7 ms line fails both conventions. The bench pass rule is **under 6.6 ms
  total open time in every sliding 100 ms window** (**6.7 ms before D-R12-207**: at 6.796 ms the 6.7 ms line is
  only 0.096 ms under the limit, inside the generator's 0.10 ms allowance), recorded at **≥ 10 kS/s under
  flight-level vibration**, with **U9 on throughout at 5.71 V** (5.72 V before; the four-stall J1). This supersedes
  D-R12-183's 6.7 ms and D-R12-170's historical 6.9 ms rules; the margin to the worst model limit is 0.194 ms (0.196 ms
  before D-R12-219; the rule is unchanged).
  `en.chatter_rule.bench_rule_ms` stores 6.6 and the gate checks both load conventions. Turn-on is 30.3–131.5 ms initial / 29.9–135.9 ms drift over C87 0.72–1.265 × 220 nF.
  C87's X7R allowance, leakage corners, pack/load and drift are Inference.

READY voltage is an R12 override of R10 rule 9: PA6 reads VLOGIC behind D5. Compare the corrected pack
estimate with 7.4 V, or VLOGIC with 7.4 V minus the pad-load U9/copper and D5 drops, reserving measured
ADC/divider error. D5 VF 0.25–0.45 V is Inference until pad-load calibration; do not label raw VLOGIC as pack
voltage (D-R12-157; M3_R12 “Firmware”, owner row 45).

**Rule 4 extension (D-R12-164, amended by -172; PA6, VLOGIC sense).** The PA6 trip threshold is
0.425 V falling / 0.455 V band top (R60 / R61 0.1 % 25 ppm/K; window 4.6274–5.0546 V VLOGIC at the drift
corner, Calculation / Inference). A PA6 trip that begins during a commanded fire pulse (from PE4 high
to the end of the ≤ 20 ms pulse plus its tail) is logged with its time and the PA6 reading. It is not
treated as battery loss: no battery-loss shutdown, shed or state change follows from it, and the fire
pulse is not cut short by it. A shorted match (or match and leads) still trips PA6 at the drift corner
(−0.1356 / −0.1804 V below the trip top; Calculation / Inference), so this rule is required. A healthy
four-stall fire is +0.0174 V clear of the trip top at drift (Calculation / Inference). A PA6 trip outside
a fire pulse is battery loss as before (hold-up 0.433–1.897 ms unshed at drift, Calculation / Inference; D-R12-207, -219).
Firmware and bench qualification remain open.

## Pyro and per-flight checks

The e-match connects at J121's screw terminal: `E1+` to pin 2 (IGN), `E1−` to pin 1 (OUT). The match must be ≤ 2 Ω and its
leads ≤ 0.3 Ω (the fire budget's separate allowances). At four stalls the fire current is 1.24705 A at BAT_IN 5.71364 V (D-R12-219; 1.24711 A / 5.71390 V under D-R12-207) against the
MJG J-Tek 1.125 A floor (Calculation / Inference).

**Per-flight checklist.** This is R10's list ([ORDERING §8.3](ORDERING.md#83-after-delivery-probes-coating-staking-and-bench-gates))
adapted to R12. Run it in order and stop at the first failure. Confirm the installed J400 switch/harness
has passed the R12 chatter bench rule: **under 6.6 ms** total open time in every sliding 100 ms window (6.7 ms before
D-R12-207), recorded at ≥ 10 kS/s under flight-level vibration with U9 on throughout at 5.71 V (D-R12-183, -207).

0. **Plug identity and retention.**
   - **0b — plug identity:** before mating, identify every plug against its port legend. J400 takes only the switch
     lead. Give the switch, servo, camera, radio and AUX leads distinct tags: the switch lead (J400) and the servo lead
     (J122) are both two-contact SH-4 plugs on the aft edge and fit either port (a swap leaves the board off, which step 3
     catches; Inference, D-R12-204). The radio and AUX leads (J420 / J440) are four-contact SH-4 plugs and also fit J400:
     there a module's GND lands on J400.1 and its supply pin on J400.2, and a module that conducts from GND to its supply
     (a regulator's substrate diode or an input TVS; Inference) can close the EN divider and turn the board on with no
     switch; step 2 catches it (D-R12-209). Repeat step 2 after any plug is moved.
   - **0d — J122 position 2 empty (D-R12-196; done before the retention step 0c):** confirm the servo lead has no contact
     in position 2 (the H743's 5 V, beside GND) and only GND and the servo signal(s) fitted. On the first
     article, and after any rework near J122, also meter J122.2 to J122.1 and to J122.3 on the unpowered board (both
     open) and inspect the J122 row at 10× for bridges or debris.
   - **0c — retention:** Seat each SH plug fully and fix it with an adhesive / RTV dab or a tie. Check each by a
     light pull (O-R12-18).
1. **1a — ESD handling.** Touch the airframe or pad ground before touching J400's switch. Keep the screwdriver in contact
   with the grounded airframe before it meets the screw.
   **1b — J1 pigtail:** with the pack unplugged at its keyed connector, J400 open and no e-match in J121,
   use an insulated driver to check J1's screws (≤ 0.4 N·m), then tug-test the leads. J1's leads are permanent;
   never loosen them to disconnect the pack. Reconnect the pack only after the screwdriver is clear.
2. **Board off with J400 open, before any e-match.** With the pack connected and J400 open:
   - Confirm the board is off: no telemetry and no buzzer. With access, also check that RAW_PROTECTED at TP81
     (top, (22.2, 25.25)) and 3V3 at LS120 pin 1 (3.8, 70.25), the buzzer's through-hole joint, both read below 0.3 V (J2 is covered after
     the final SWD session, so it is not a probe point).
   - Measure J121.2 (IGN) to GND with a floating meter: it must read below 0.1 V.
   - If the board is on, or J121.2 reads above 0.1 V, do not fit the e-match.
3. **Closed-switch check with a dummy load.** Fit a 2 Ω dummy in J121, then close J400.
   - The board powers up, the passive screen passes (PC0 and PC5 both in their healthy bands, D-R12-140, [M3_R12
     "Firmware"](M3_R12.md#firmware)) and firmware raises PC1.
   - Confirm the powered BUS / CONT readings.
   - Confirm PD10 (PORT_SENSE) reads **high** (ports powered) and PA6 = VLOGIC / 11.
   - With a 10 MΩ DMM, confirm NRST at C24.1 ≥ 0.90 × 3V3 at LS120 pin 1 (coating checks below).
   - Open J400. Within 1 s the board must be off and J121.2 below 0.1 V. Only then remove the dummy.
4. **Igniter resistance.** With J400 open, and no USB and no self-powered module attached, fit the e-match in J121.
   Measure across it on a meter whose test current is under 40 mA: about 1–2 Ω plus leads, not about 0 Ω and not open.
   Record it.
5. **Stay-off.** After closing the airframe and before carrying, and again just before closing J400 on the rail,
   confirm no telemetry and no buzzer. On closing J400, confirm a fresh power-up.
6. **If the bus may be live**, keep clear and disconnect the e-match (or the pack) before any other handling.
7. **Recovery order.** Open J400. Confirm the board is off. Confirm the match fired, or disconnect it. Disconnect the
   pack at its keyed connector. Only then connect USB. J1 screws are touched only in step 1b’s state.

## Battery

- **J1** is the KF301-5.0-2P screw terminal (D-R12-174): pin 1 BAT_IN (7.4, 17.35), pin 2 GND (7.4, 12.35), wire
  entry on the west edge. Fit a permanent pigtail to a keyed pack connector. Use **20 AWG (22 AWG acceptable)**
  stranded wire, insulation OD ≤ 1.8 mm; 18 AWG only with OD ≤ 2.2 mm and its bend checked against J1's
  5.20 mm wire room. The terminal takes 22–14 AWG, strip 4–5 mm (Datasheet); installed bend room sets the limit.
  - **Ferrules.** Use bare strands or an uninsulated ferrule protruding ≤ 0.5 mm from the wire face; never tinned.
  - **Torque.** Tighten each M2.5 screw to at most **0.4 N·m** (Kefa drawing KF301-5.0 rev A; Datasheet).
  - **Polarity.** Pack + to pin 1 (`1:BAT+`, forward), pack − to pin 2 (`2:GND`, aft). Check by meter before the
    first connection: a reversed pack is the reverse hot-plug case the model covers (Simulation / Inference), not a
    supported state, top BAT+ / GND legends now identify the contacts.
  - **Strain relief.** Tie both leads to the sled within about 20 mm of the terminal, so no lead load reaches the
    clamp or the solder joints, and dress them apart from the J400 pair.
  - **Pre-flight.** Follow step 1b: pack unplugged at its connector, J400 open, no e-match, insulated driver.
    Only in that state re-tighten to ≤ 0.4 N·m and tug-test. Screw retention under vibration is unqualified.
- **Storage: unplug the pack (D-R12-216).** R167 (10 kΩ, BAT_IN to GND, the hot-plug bleed) draws about **0.84 mA**
  from a connected 2S pack even with J400 open (8.4 V / 10 kΩ; 0.74 mA at 7.4 V; Calculation; the board's other
  switch-open loads are microamps, Calculation / Inference). A 1500 mAh pack left connected is flat in about
  1500 mAh / 0.84 mA ≈ 1800 h, roughly **75 days from full**, and below a safe 3.0 V per cell sooner, about a month from
  a storage charge (Calculation / Inference on the pack's usable capacity). **Unplug the pack at its keyed connector
  whenever the vehicle is not being prepared for flight.**
- **No battery-lead fuse** (R10 OQ-6).
- **Hot-plug.** The installed harness must measure ≥ 0.03 Ω and 0.1–2 µH, the hot-plug model's domain. On R12, with
  C79, every required case passes (Simulation / Inference, D-R12-78).
- **Pack.** A 3S pack is cut off by U9's OVLO (rising 9.80–10.71 V, Calculation). U9 auto-retries after a fault
  (D-R12-09).

## Board, supports and fit

- **Supports.** Four M3 supports, at (3.0, 5.9), (43.0, 5.9), (3.5, 80.95) and (42.5, 80.95) (D-R12-24, -99, -144, -162, -171). Use **nylon (or
  otherwise insulated) screws, nuts and washers at all four**. The aft pair is 3.0 mm in, so the aft SH row clears both
  washers.
- **One-sided board.** No parts on the bottom face; the bottom carries contact legends, designators and the revision
  legend `M3-ASSY-R12` only.
- **SH plugs on the short edges only.** The mouths sit 1.1 mm inside their edge (fit_check r12, CAD envelopes;
  Inference on the clone dimensions).
- **Every part is JLC-assembled (D-R12-85, owner 2026-11-05).** Nothing is fitted by hand after delivery:
  - C84 (Honor HV1E477M0810PZ, 470 µF 25 V polymer) at (36.0, 35.05), beside U2, is placed and reflowed by JLC.
  - LS120 (QMB-09B-03 THT buzzer) at (5.8, 70.25) and J121 are JLC THT assembly (hand-soldered by JLC after reflow).
    LS120's (+) lead goes in pad 1 (3.8, 70.25): JLC's own footprint prints its `+` beside pad 1 and the CPL puts that
    pad on ours (jlc_orient_r12, residual 0.0 mm, Measured), and the maker drawing marks the (+) lead (Datasheet). At
    incoming inspection, check the buzzer's `+` mark sits at pad 1.
- **microSD** J430 is the Molex 104031-0811 push-pull socket (C585350) on the east side, mouth east.
  With the board off, sources disconnected and board unbolted, insert/remove the card east–west.
  Tape over the seated card as a retention backup. The inserted card stays inside the board edge
  (mated envelope x 30.30–45.90 mm, board x ≤ 46; Measured CAD envelope, installed fit unverified).
  Card-detect contacts are NC. This replaces the hinged socket by owner decision 2026-11-07 (D-R12-162).
- **U5 barometer** (MS5611-01BA03 since D-R12-214; MS5607 before) on the top face at (23.0, 32.25), rotation 180. Keep its port open and vented, under an opaque cover that
  does not press on it (R10's cover rule).
- **IMU.** U4 (ST ISM6HG256X since D-R12-212: gyroscope, low-g and high-g accelerometer in one part) at (23.0, 45.45),
  rotation 180, on the roll axis (x = 23; lever arm x = 0, unchanged): +X_imu west, +Y_imu forward, roll = **+gyro_Y**,
  thrust **+a_Y** (D-R12-220, correcting D-R12-54's −gyro_Y; Calculation from DS15034 Figure 5 and the board pads). **U6 is not fitted** (D-R12-213): its empty land at (23.0, 38.25) and C33's
  stay for a later hand-fit of a second high-g sensor (its axial channel would be channel 1, an Inference). A bench sign
  check is needed before flight ([M3_R12 IMU axis map](M3_R12.md#imu-axis-map)).
- **LEDs.** LED1 red (8.0, 56.65) and LED2 yellow (8.0, 58.85), top face, west bay.
- **Length.** R12 is 86.85 mm (D-R12-174: 3.85 mm added at the aft end for J1's terminal; 83 mm under D-R12-171, 85 mm under D-R12-162, 88 mm under D-R12-144), 36.85 mm longer than R11. `docs/VEHICLE.md` gives no internal bay or sled length (its
  stack row still budgets 102 mm for R9), so the fit could not be checked: check it against the bay and coupler and
  keep R10's rule that the board sits wholly forward of joint + 47 mm (O-R12-28). Real wires, plugs, sled and stack are
  unverified.

## Coating and leakage checks

After inspection and the final SWD session, apply the mandatory local conformal coat (REQUIREMENTS P3 / F8).
Coat Q120, Q121, Q122, Q124, R118–R123, R126–R134, R136, R173, R175, R178, R180, C120, C123,
C126–C129 and D120. Their pad envelope on `c9b9f0fa…` is **x 3.387–19.313, y 29.980–54.550 mm**
(Measured from transformed pad bounds). Coat U9, R80, R81, R165 and C87 (pad envelope
**x 13.925–19.475, y 10.875–20.400 mm**), plus the BAT_ENABLE / BAT_SW_SOURCE / BAT_SW_RETURN tracks
and vias, including the switch-side layer changes near J400. The envelopes locate the parts; cover their
exposed joints and associated copper, not the keep-off items below.

Keep coat off J1/J121 wire entries and screws, all SH mouths, J3, J430 contacts and card path, U5's port,
U4 / U5 bodies and U6 / C33's empty lands (kept solderable for a hand-fit, D-R12-213). Keep J2 clear until after the final SWD session, then protect it with polyimide and
acrylic per P3. Keep the barometer vent open.

TP122, the bare PYRO1_GATE test pad at (14.8, 46.25), lies inside the pyro envelope: leave it bare while the rest is
coated. After cure, repeat the gate leakage reading there (REQUIREMENTS P3): board on through J400 with a 2 Ω dummy in
J121 and no e-match, NRST held low (short C24.1 to GND, so PE4 is high-impedance), 10 MΩ DMM from TP122 to GND. It
must read under 5 mV: 5 mV across R126 + R127 (1.22 kΩ) is about 4 µA, which is about 2 MΩ or less to a pack-voltage
net or 0.8 MΩ or less to 3V3 (Calculation; R10's limit); at 5 mV or more, clean and coat again. Then coat TP122 and
repeat per-flight step 3.

After coating, at each installation and before each flight, check NRST-to-GND leakage ≥ 250 kΩ.
With a 10 MΩ DMM on the powered board, require **NRST at C24.1 (26.6, 49.45) ≥ 0.90 × 3V3 at
LS120 pin 1 (3.8, 70.25)**; both are on F and stay uncoated (Measured; J2.1 is 3V3 too, but J2 is covered). Do the powered check in per-flight step 3,
with the dummy load and no e-match. A failed check refuses flight. Follow the source-disconnection and
J400 rules when attaching probes; these checks do not replace the cold screen.

## Boot and programming

J2 (TC2030, top, (32.8, 48.85)) is the SWD port. Program with the e-match disconnected, and record and read back
BOOT_ADD0 and the boot settings. The round-12 records lens read AN2606 Rev 71 Table 145: loader outputs
include PA9 (NC since D-R12-195), PB10 (QSPI_NCS), PB6/PB9 (barometer SCL/IMU_CS), PA8/PC9 (NC / VBUS_SENSE),
PA6 (VLOGIC_SENSE), PC11 (camera UART) and PE13 (SD MISO); USB uses PA11/PA12. Physical loader checks
remain O-R12-23. NRST's filter capacitor C24
is at J2's end of the NRST run (26.6, 49.03) (D-R12-98). R10's dummy-load / no-e-match service procedure
applies: PC1 / PE4 locked low, camera EN low, SD_CS high and HG_CS high.

For the separate first-article dummy-fire check, use the fixed 2 Ω dummy / 0.3 Ω total leads and 7.4 V / 0.15 Ω
source with the budget converter loads and no servo stalls. Reject BAT_IN − RAW_ACT above **0.4 V**, overriding
R10 rule 4's 0.2 V line (D-R12-109). At R134's drift low end 1.9666 Ω, current is 1.52369 A and the drop
bound **0.27305 V** (0.27318 V before D-R12-207), including hot FETs, 29.975 mΩ loop copper and converter coupling through BAT_IN
(Calculation / Inference; D-R12-183). The body-diode case is 0.7–1.0 V (Inference). Qualify this line on the
first article; the per-flight closed-switch check does not command a fire.

## Cost

**Standard PCBA (D-R12-211 … -219, 2026-11-24; current).** Taken on `0c681ad6…`; the BOM and CPL of `a9595a21…` (D-R12-221) are byte-identical, so it was not re-run. `FAB_NET=1 m3_design/r12_fab.sh` on `0c681ad6…`, Live
2026-11-24T21:21:13Z / 21:22:43Z (`fab/cost_check_2.json` / `_5.json`, `jlc_cost.py --tier standard --profile r10`):
59 BOM lines (23 Extended / 36 Basic), 179 JLC parts, 566 paste flashes, no owner BOM; parts **$38.83 per board**;
feeder $1.53 × 59 codes = **$90.27 per order** (Standard charges every code). REQUIREMENTS M3 metric (parts + feeder)
**$83.96 / $56.88 per board at 2 / 5 boards**, under the $84.41 cap ($0.45 under at two boards). Against the Economic
figures ($62.44 / $43.10 per board, 2026-11-15) that is **+$21.52 / +$13.78 per board, +$43.04 / +$68.90 per order**;
the per-board parts rose $8.63 (U4 ISM6HG256XTR $14.32 and U5 MS5611 $6.14 for the LSM6DSVE, MS5607 and FXLS90322).
Fixed fees outside the metric: Standard one side $50.19 per order (setup $25.56, stencil $8.21, fixture $16.42; JLC may
add a $14.93 handling fee) against Economic's $9.71, +$40.48 per order; edge rails / panel for the 46 mm board, PCB,
joints, X-ray and shipping are not in these figures (Calculation / Inference). Stock 2026-11-24T21:20:23Z / 21:21:57Z
(`fab/stock_check_2.json` / `_5.json`): **U4 (ISM6HG256XTR, C51931514) is short at 5 boards** (stock 5,
`canPresaleNumber` 2, orderable 2 < 5) and thin at 2 boards (2 orderable for 2, no spare); every other line is
orderable (U5 C15639 4299 / 4142; U9 C3662799 4421 / 4189; D402 C535146 70 / 50). The FAB_NET run exits 1 on that U4
line at 5 boards, as expected; it is recorded, not hidden. Orderable = min(stockCount, canPresaleNumber), an
Inference about JLC's field. On order day confirm U4 in the JLC cart, else consign franchised ISM6HG256XTR (as R10's
records, `docs/ORDERING.md` §8.1) or order two boards. Nothing ordered.

**Economic records below are history (before D-R12-211).**

Parts + feeder **$62.44 / $43.10 per board at 2 / 5 boards**, against the $84.41 cap (Live
2026-11-15T02:20:48Z / 02:22:13Z, after D-R12-195's SH-4 J122 and the SERVO3 / SERVO4 deletion): 60 BOM lines
(24 Extended / 36 Basic), 181 JLC parts, 21 charged codes, $30.20 parts per board and $64.47 feeder fees per order
(was $64.03 / $43.77 with 22 codes on `876733fe…`). There are 585 paste flashes and no owner BOM. Stock
2026-11-15T02:20:03Z / 02:21:31Z: **U9 (TPS259470ARPWR, C3662799) reads short at both quantities** (stock 175,
orderable 0 by JLC's `canPresaleNumber`, minimum purchase 7: a supplier change since 2026-11-14, not D-R12-195); no
other line short or thin. Orderable quantity is an Inference about JLC's field: confirm U9 in the JLC cart on order
day. The 2026-11-11 all-in quote of $165.33 for two assembled boards before shipping was for historical `1d7562d5…`;
re-quote the current board, including X-ray, DFM and reflow acceptance. Nothing ordered.

See [M3_R12.md](M3_R12.md#cost-and-stock).
