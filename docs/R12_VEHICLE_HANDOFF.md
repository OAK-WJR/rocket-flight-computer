# R12 vehicle integration handoff

**Status.** PCB `82eddc69…` (M3-ASSY-R12, AVA re-layout D-R12-93 … -99; round 3 changed only C25 / C26, D-R12-107, round 4 only R166's footprint description, D-R12-113, the AVA polish pass only signal copper, D-R12-121 … -124, round 5's fix pass the fire-net copper, five pyro-cell parts, U6's lands and the J121 pours, D-R12-125 … -133, and round 6's fix pass added R136, R95 and D95, changed R131 to 5.1 kΩ and moved R132, R175 and R120, D-R12-134 … -143, and round 7's fix pass shrank the board to 46 × 88 mm, moving the forward port row, its cells, the port buck and the forward supports aft, D-R12-144 … -151), 46 × 88 × 1.6 mm, four
layers, every part on the top face and assembled by JLC. Branch `m3-assy-r12`. It is a CAD candidate: not accepted, nothing ordered, and no physical fit is claimed. R9 stays the
accepted board. The full state is in [M3_R12.md, "Current state"](M3_R12.md#current-state), and what the owner must
accept is in [R12_VALIDATION.md](R12_VALIDATION.md). The parent `../../docs/VEHICLE.md` is owned separately and is not
edited here.

All coordinates are board millimetres: x east (0 … 46), y forward from the aft edge (0 … 88), top face = F. Positions
below were read from the board file (Measured, pcbnew on `be81f40b…`, geometry unchanged on `66323cf0…`, `db1f0999…` and `68e6b650…` (no part moved in the polish pass); part centres are `m3_design/r12_place.tsv`). Round 5 moved five small pyro-cell parts and nothing this file positions otherwise (Measured on `6e874d4e…`, D-R12-125): TP122 (the PYRO1_GATE probe) to (14.8, 42.4), D120 to (6.6, 49.2) rotation 270, R131 turned to rotation 270 at (6.6, 46.6), R173 to (12.6, 46.1) and C13 to (17.4, 50.0) rotation 0. Round 6 added and moved small parts only, none that this file positions otherwise (`r12_place.tsv` on `f26dfef1…`): R136 (cold pull-up series resistor) new at (4.1, 50.2) rotation 0 and R131 now 5.1 kΩ at the same place (D-R12-134); R132 to (17.17, 32.2) rotation 0, R175 turned to rotation 270 at (17.6, 33.6), R120 to (6.53, 26.95) rotation 0 (D-R12-137); R95 new at (18.15, 22.89) rotation 270 and D95 new at (20.77, 24.27) rotation 180 (D-R12-138). TP81 and TP122 did not move. Round 7 (`r12_place.tsv` on `82eddc69…`, D-R12-144, -145) moved the forward port row J410 / J420 / J440 2 mm aft (y 84.35), their 1 k / 100 nF cells 1.85 mm (y 80.35), the port buck U400 / L400 / C400 / C402 / C406 / R400 / R401 / R404 2 mm, C407 to (16.75, 81.35), R111 / R112 to y 80.3, R104 0.2 mm east to (28.8, 7.6) and the forward supports to y 82.1; nothing else this file positions moved (J430, LS120, J121, J1, J2, U4, U5, U6, the LEDs).

## Harness pin map

Every contact of every port carries its own `n:NAME` legend, most of them on the **bottom** face along the contact's
column. The legends sit alternately inward and outward of the pad row (D-R12-80). **Wire from this table, and check
every lead's pin identity by continuity before first power.**

The SH contacts are numbered as on JST's SMnnB-SRSS-TB land (D-R12-31). The ports copy the MicoAir H743's SH port
orders, so one module lead fits either board. The source image did not mark the pin-1 end, and the owner's H743 may be
the v1, so the pin orders are an **Inference** until a real H743 lead is checked (O-R12-19).

| Port | Edge, mouth | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|---|
| J400 switch, SH-4 | aft, mouth aft; pin 1 at x 12.5, pin 4 at x 9.5 | SW (BAT_SW_SOURCE) | SW (BAT_SW_RETURN) | NC | NC | — | — |
| J122 servo signals, SH-6 | aft; pin 1 at x 24.1, pin 6 at x 19.1 | SERVO1 (S1) | SERVO2 | SERVO3 | SERVO4 | GND (signal reference) | NC |
| J9 camera, SH-6 | aft; pin 1 at x 36.0, pin 6 at x 31.0 | CAM_5V (5V4) | CAM_5V (5V4) | GND | GND | board RXI (camera TX here) | board TXO (to camera RX) |
| J420 radio by default, SH-4 | forward, mouth forward; pin 1 at x 10.0 | GND | 4V8 (PORT_4V8) | board TXO (to module RX) | board RXI (from module TX) | — | — |
| J410 GPS by default, SH-6 | forward; pin 1 at x 20.5 | GND | 4V8 | board TXO | board RXI | NC (the H743's SCL) | NC (SDA) |
| J440 AUX spare, SH-4 | forward; pin 1 at x 33.0 | GND | 4V8 | board TXO | board RXI | — | — |
| J2 SWD, TC2030 pads (top, centre (32.8, 45.0), rotation 90) | — | 3V3 (33.435, 46.27) | SWDIO (32.165, 46.27) | NRST (33.435, 45.0) | SWCLK (32.165, 45.0) | GND (33.435, 43.73) | NC (32.165, 43.73) |

Pin data: `tools/check_r12.py` `SH_PORTS` / `TERMINAL_PINS`, D-R12-29 … -31.

- **Pyro terminal J121.** A black DORABO DB125-3.5-2P screw terminal at (7.4, 37.0); the wires leave west (D-R12-29).
  - Pin 1 (7.4, 35.25) is PYRO1_OUT, `E1−` (the side Q124 switches to GND).
  - Pin 2 (7.4, 38.75) is PYRO1_IGN, `E1+` (fed through R134 from the bus).
  - Its face is 3.40 mm in from the edge, giving 5.00 mm of bare-bore wire room against R10's 4.95 mm floor
    (Calculation on CAD envelopes).
- **Battery pads J1** (`M3_WIREPAD_2P_P5`: 1.40 mm holes, 2.60 mm lands, 5.00 mm pitch; D-R12-30).
  - Pad 1 BAT_IN (3.5, 17.8), pad 2 GND (3.5, 12.8), legends `1:BAT+` / `2:GND`.
  - They take a tinned 16–20 AWG lead, or the pins of a later 5.0 mm two-position terminal (hole fit an Inference,
    O-R12-20).
  - A 10 × 8.2 mm keep-clear is reserved for that terminal body.
- **Directions.** On J410, J420 and J440, pin 3 "board TXO" is driven by the board (PD8, PB13, PC6): wire the module's
  RX to it. Pin 4 "board RXI" is received by the board (PD9, PB12, PC7): wire the module's TX to it. **J9 is
  different:** pin 5 is board RXI and pin 6 board TXO. `5V4` is the camera supply from U403 (5.22–5.69 V initial,
  Calculation, conditional on U403 VIN ≥ VO / 0.75; low-input dropout estimate in M3_R12 "Power").
- **J9 needs both supply contacts and both GND contacts wired**, so the 1 A camera allowance is 0.5 A per contact
  (Calculation / Inference: load allocation and equal current sharing) against SH's 1 A rating (JLC listing, Live 2026-11-04).
- **J410, J420 and J440 carry the same supply and UART pin order.** The firmware port map defaults to GPS J410, radio
  J420, AUX spare. A device on these ports must drive its TX high at no more than 3.6 V.
  - Under the 0.561 A budget the port pins stay at or above 4.563 V at the drift corner and at or below 4.972 V with no
    load (Calculation / Inference, D-R12-83): inside the LR900-F's 4.5–5.0 V (a project-record Inference; MicoAir's
    page gives only "5V DC") and the M100 Mini's 3.3–5 V. That holds while U400's input is at least VO / 0.75, about
    6.1–6.6 V (TI SLVSD90B §7.3, D-R12-131). During a four-stall fire (U400 VIN about 5.55 V) or on a 6.0 V pack
    (about 5.48 V) it rests on U400's frequency foldback, an Inference (M3_R12 "Power"; bench item R12_VALIDATION row
    15).
  - Before connecting a module, read PORT_4V8 at pin 2 of each port on pack power with the e-match disconnected. Expect
    4.60–4.94 V at room temperature (initial tolerance, Calculation).
- **Servo power from the harness (`SERVO + FROM HARNESS`).** J122 carries signals only: SERVO1–4 and one shared signal
  GND. Servo motor power and return run in the pack-star harness, never through the board (REQUIREMENTS F4). R12's
  board does not print this note (D-R12-81, owner acceptance pending), so label the harness itself.
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
- **J400 chatter** (R10's D-R25-01 rule; R12 figures in stageD_analysis.md §3). Record the contact state at
  ≥ 10 kS/s under flight-level vibration. It passes only if the total open time in every sliding 100 ms window is
  under 7 ms and U9 stays on throughout at the four-stall pack voltage of 5.72 V. The R12 worst-corner limit is
  7.56 ms (Calculation / Inference).

## Pyro and per-flight checks

The e-match connects at J121's screw terminal: `E1+` to pin 2 (IGN), `E1−` to pin 1 (OUT). The match must be ≤ 2 Ω and its
leads ≤ 0.3 Ω (the fire budget's separate allowances). At four stalls the fire current is 1.250 A against the
MJG J-Tek 1.125 A floor (Calculation / Inference).

**Per-flight checklist.** This is R10's list ([ORDERING §8.3](ORDERING.md#83-after-delivery-probes-coating-staking-and-bench-gates))
adapted to R12. Run it in order and stop at the first failure.

0. **Port retention (SH).** Seat each SH plug fully and fix it with an adhesive / RTV dab or a tie. Check each by a
   light pull (O-R12-18).
1. **ESD handling.** Touch the airframe or pad ground before touching J400's switch. Keep the screwdriver in contact
   with the grounded airframe before it meets the screw.
2. **Board off with J400 open, before any e-match.** With the pack connected and J400 open:
   - Confirm the board is off: no telemetry and no buzzer. With access, also check that RAW_PROTECTED at TP81
     (top, (22.2, 21.4)) and 3V3 at J2 pad 1 (33.435, 46.27) both read below 0.3 V.
   - Measure J121.2 (IGN) to GND with a floating meter: it must read below 0.1 V.
   - If the board is on, or J121.2 reads above 0.1 V, do not fit the e-match.
3. **Closed-switch check with a dummy load.** Fit a 2 Ω dummy in J121, then close J400.
   - The board powers up, the passive screen passes (PC0 and PC5 both in their healthy bands, D-R12-140, [M3_R12
     "Firmware"](M3_R12.md#firmware)) and firmware raises PC1.
   - Confirm the powered BUS / CONT readings.
   - Confirm PD10 (PORT_SENSE) reads **high** (ports powered) and PA6 = VLOGIC / 11.
   - Open J400. Within 1 s the board must be off and J121.2 below 0.1 V. Only then remove the dummy.
4. **Igniter resistance.** With J400 open, and no USB and no self-powered module attached, fit the e-match in J121.
   Measure across it on a meter whose test current is under 40 mA: about 1–2 Ω plus leads, not about 0 Ω and not open.
   Record it.
5. **Stay-off.** After closing the airframe and before carrying, and again just before closing J400 on the rail,
   confirm no telemetry and no buzzer. On closing J400, confirm a fresh power-up.
6. **If the bus may be live**, keep clear and disconnect the e-match (or the pack) before any other handling.
7. **Recovery order.** Open J400. Confirm the board is off. Confirm the match fired, or disconnect it. Disconnect the
   pack. Only then connect USB.

## Battery

- **J1** pads 1 BAT_IN (3.5, 17.8) and 2 GND (3.5, 12.8), on the west edge. The leads carry the fire pulse (about 4.2 A
  into a shorted igniter, R10 figure, Calculation / Inference), so use 16–20 AWG soldered, tied to the sled near the pads.
- **No battery-lead fuse** (R10 OQ-6).
- **Hot-plug.** The installed harness must measure ≥ 0.03 Ω and 0.1–2 µH, the hot-plug model's domain. On R12, with
  C79, every required case passes (Simulation / Inference, D-R12-78).
- **Pack.** A 3S pack is cut off by U9's OVLO (rising 9.80–10.71 V, Calculation). U9 auto-retries after a fault
  (D-R12-09).

## Board, supports and fit

- **Supports.** Four M3 supports, at (3.0, 5.9), (43.0, 5.9), (3.5, 82.1) and (42.5, 82.1) (D-R12-24, -99, -144). Use **nylon (or
  otherwise insulated) screws, nuts and washers at all four**. The aft pair is 3.0 mm in, so the aft SH row clears both
  washers.
- **One-sided board.** No parts on the bottom face; the bottom carries contact legends, designators and the revision
  legend `M3-ASSY-R12` only.
- **SH plugs on the short edges only.** The mouths sit 1.1 mm inside their edge (fit_check r12, CAD envelopes;
  Inference on the clone dimensions).
- **Every part is JLC-assembled (D-R12-85, owner 2026-11-05).** Nothing is fitted by hand after delivery:
  - C84 (Honor HV1E477M0810PZ, 470 µF 25 V polymer) at (36.0, 31.2), beside U2, is placed and reflowed by JLC.
  - LS120 (QMB-09B-03 THT buzzer) at (7.2, 67.4) and J121 are JLC THT assembly (hand-soldered by JLC after reflow).
    LS120's (+) lead goes in pad 1 (5.2, 67.4): JLC's own footprint prints its `+` beside pad 1 and the CPL puts that
    pad on ours (jlc_orient_r12, residual 0.0 mm, Measured), and the maker drawing marks the (+) lead (Datasheet). At
    incoming inspection, check the buzzer's `+` mark sits at pad 1.
- **microSD** J430 on the top face at (20.0, 69.0), rotation 180. Open the hinge only with the board off and its sources
  disconnected.
- **U5 barometer** (MS5607) on the top face at (23.0, 28.4), rotation 180. Keep its port open and vented, under an opaque cover that
  does not press on it (R10's cover rule).
- **IMU.** U4 at (23.0, 41.6), rotation 180, on the roll axis (x = 23; lever arm x = 0, unchanged): roll = −gyro_Y,
  thrust −a_Y. U6 at (23.0, 34.4), rotation 180, is now on the roll axis too (x = 0); its axial channel is channel 1.
  The axis maps are D-R12-54's (Calculation / Inference: both rotations unchanged; inherited axis frames). A bench sign check is needed before flight ([M3_R12 IMU axis map](M3_R12.md#imu-axis-map)).
- **LEDs.** LED1 red (8.0, 52.8) and LED2 yellow (8.0, 55.0), top face, west bay.
- **Length.** R12 is 88 mm (D-R12-144; 90 mm under D-R12-99), 38 mm longer than R11. `docs/VEHICLE.md` gives no internal bay or sled length (its
  stack row still budgets 102 mm for R9), so the fit could not be checked: check it against the bay and coupler and
  keep R10's rule that the board sits wholly forward of joint + 47 mm (O-R12-28). Real wires, plugs, sled and stack are
  unverified.

## Boot and programming

J2 (TC2030, top, (32.8, 45.0)) is the SWD port. Program with the e-match disconnected, and record and read back
BOOT_ADD0 and the boot settings. Among R12's moved functions, the ROM loader's pins are PB10, PB6, PE12–PE14, PA7,
PA8–PA10, PA15 and PC9–PC12 (`pin_table.tsv`'s AN2606 Rev 64 Table 119 column, read in R11: Inference); PB7 and PD2
are not H74x loader pins there. AN2606's H74x list must be re-read for them (O-R12-23). NRST's filter capacitor C24
is at J2's end of the NRST run (26.6, 45.18) (D-R12-98). R10's dummy-load / no-e-match service procedure
applies: PC1 / PE4 locked low, camera EN low, SD_CS high and HG_CS high.

For the separate first-article dummy-fire check, use the fixed 2 Ω dummy / 0.3 Ω total leads and 7.4 V / 0.15 Ω
source with the budget converter loads and no servo stalls. Reject BAT_IN − RAW_ACT above **0.4 V**, overriding
R10 rule 4's 0.2 V line (D-R12-109). The healthy budget current is 1.505875 A, with a drop bound of 0.264 V
including both hot FETs and conservatively all fire copper (Calculation / Inference: 70 °C hot factors, pack,
loads and copper model); the body-diode case is 0.7–1.0 V (Inference). Qualify the line on the first article;
see [M3_R12 firmware](M3_R12.md#firmware). The per-flight closed-switch check does not command a fire.

## Cost

M3 metric (parts + feeder per board): $64.86 at 2 boards and $45.52 at 5 boards, against the $84.41 cap (Live
2026-11-07T14:15:13Z / 14:16:33Z on `82eddc69…`). Minimum all-in $173.39 / $279.19 including U1-only X-ray ($3.28 / $8.20;
Calculation / Inference: X-ray count; the bare PCB is the Live 46 × 90 quote, $25.10, taken for the 88 mm board without a re-quote, an Inference), $3.39 over the $170 target at 2 boards.
Counting U1 / U4 / U5 / U6 / U9 gives $186.51 / $291.49–299.69, above $170 at 2 boards and straddling $295 at 5 boards (Calculation /
Inference: qualifying count and fee tier). Confirm the count and
tier, including possible D402 / Y1 fees, on JLC's quote (D-R12-105). No part is short or thin. See [M3_R12.md,
"Cost and stock"](M3_R12.md#cost-and-stock).
