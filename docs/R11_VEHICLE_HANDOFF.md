# R11 vehicle integration handoff

**Status.** PCB `3bb83272…` (M3-ASSY-R11), 46 × 50 × 1.6 mm, six layers, branch `m3-assy-r11`; a CAD candidate, not
accepted, nothing ordered, no physical fit claimed. R9 stays the accepted board. The full state is in
[M3_R11.md, "Current state"](M3_R11.md#current-state); what the owner must accept is in
[R11_VALIDATION.md](R11_VALIDATION.md). The parent `../../docs/VEHICLE.md` is separately owned and is not edited here.

All coordinates are board millimetres: x east (0 … 46), y forward from the aft edge (0 … 50), top face = F. Pad
positions below were read from the board file (Measured, pcbnew on `3bb83272…`).

## Harness pin map

R11's silkscreen labels each GH port only by its designator, pin 1 and the last pin (the R11 legend set, D-R11-83,
owner acceptance pending), so **this table is the pin map: wire from it, and check every lead's pin identity by
continuity before first power**. GH contacts are numbered as JST's SM0xB-GHS-TB drawing; pin 1 is the end marked by the
pin-1 dot and the `1:` legend.

| Port | Edge, mouth | Pin 1 | 2 | 3 | 4 | 5 | 6 | Silkscreen |
|---|---|---|---|---|---|---|---|---|
| J122 servo signals, GH-5 (SM05B) | aft, mouth aft; pin 1 at x 23.9, pin 5 at x 18.9 | SERVO1 | SERVO2 | SERVO3 | SERVO4 | GND (signal reference) | — | J122, 1:S1, 5:GND |
| J9 camera, GH-6 (SM06B) | aft, mouth aft; pin 1 at x 35.925, pin 6 at x 29.675 | CAM_5V (5V4) | CAM_5V (5V4) | GND | GND | board RXI (camera TX here) | board TXO (to camera RX) | J9, 1:5V4, 5:RXI, 6:TXO |
| J400 switch, GH-2 (SM02B) | aft, mouth aft; pin 1 at x 11.625, pin 2 at x 10.375 | SW (BAT_SW_SOURCE) | SW (BAT_SW_RETURN) | — | — | — | — | SWITCH, 1:SW, 2:SW (bottom) |
| J420 radio by default, GH-4 (SM04B) | forward, mouth forward; pin 1 at x 10.525 | 4V8 (PORT_4V8) | GND | board TXO (to module RX) | board RXI (from module TX) | — | — | J420, 1:4V8, 4:RXI |
| J410 GPS by default, GH-4 | forward, mouth forward; pin 1 at x 21.125 | 4V8 | GND | board TXO | board RXI | — | — | J410, GPS, 1:4V8, 4:RXI |
| J440 AUX spare, GH-4 | forward, mouth forward; pin 1 at x 31.725 | 4V8 | GND | board TXO | board RXI | — | — | J440, 1:4V8, 4:RXI |
| J2 SWD, TC2030 pads (top, centre (32.9, 39.6)) | — | 3V3 (31.63, 40.235) | SWDIO (31.63, 38.965) | NRST (32.9, 40.235) | SWCLK (32.9, 38.965) | GND (34.17, 40.235) | NC (34.17, 38.965) | J2, 1:3V3, 2:SWDIO |

Pin data: [`m3_design/r11/design/parts_r11.md`](../m3_design/r11/design/parts_r11.md) §6, stageD2.md §6, D-R11-05.

- **Wire pads** (`M3_WIREPAD_2P_AWG20`: finished hole 1.30 mm, land 2.50 mm, pitch 3.80 mm, plated through; parts_r11.md
  §6), on the west edge, top-side legends:

  | Pair | Pad 1 | Pad 2 | Silkscreen |
  |---|---|---|---|
  | J1 battery | (2.3, 14.3) BAT_IN | (2.3, 10.5) GND | 1:BAT+, 2:GND, BAT |
  | J121 pyro | (2.3, 24.7) PYRO1_OUT, `E1−` (the side Q124 switches to GND) | (2.3, 20.9) PYRO1_IGN, `E1+` (fed through R134 from the bus) | 1:E1−, 2:E1+, IGN |

- **Directions.** On J410, J420 and J440, "board TXO" (pin 3) is a line the board drives (PD8, PB13, PC6): wire the
  module's RX to it; "board RXI" (pin 4) is a line the board receives on (PD9, PB12, PC7): wire the module's TX to it.
  **J9 is different**: pin 5 is board RXI (the camera's TX goes there) and pin 6 board TXO (to the camera's RX). `5V4`
  abbreviates the nominal 5.456 V camera supply through U402.
- **J9 needs both supply contacts and both GND contacts wired**: the 1 A camera allowance is 0.5 A per contact against
  GH's 1.0 A rating with AWG 26 (D-R11-05; JST eGH p. 1).
- **J410, J420 and J440 are electrically identical** (D-R19-14): the GPS or the radio may use any of them if the firmware
  port map is changed to match; the default is GPS J410, radio J420, AUX spare. AUX may draw at most 100 mA at 4.8 V
  (resting on the U401 thermal Inference until a first-article test, D-R11-80). A device on these ports must drive its
  TX high at no more than 3.6 V (R20-MCU-02). Before connecting any module, check PORT_4V8 at pin 1 of each port reads
  4.71–4.87 V on pack power, e-match disconnected (R10's R20-PWR-02 range; same circuit, D-R11-01; not re-derived for R11).
- **J122** carries signals only: SERVO1–4 and a shared signal GND. Servo motor power and return run in the pack-star
  harness, as R10 (REQUIREMENTS F4).
- **GH harness.** GH crimps take AWG 30–26, insulation 0.76–1.0 mm (JST eGH p. 1; parts_r11.md §6). Plugs latch; seat
  each one fully and pull-test it. The JLC listing gives −25 to +85 °C for these headers against JST's −40 to +105 °C
  (Inference: a distributor's generic range).

## Power, arming and USB

R10's single-switch scope applies (AGENTS, "R10 single-switch scope"). The external screw switch on J400 is the power
and pad-arming device, reachable on the rail: on last, off first. Connect the e-match (at the field terminal, below)
only with no USB and no self-powered module (GPS, radio, AUX or camera) attached. USB bench work needs the pack or the
e-match disconnected. The GPS, radio and AUX ports are fed from the battery path, so they are off on USB-only power:
during a USB-only session disconnect their leads or check that pin 3 of J410, J420 and J440 stays near 0 V.

- **J400 is a GH-2 plug to the external switch**, about 7 µA through its contacts (D-R11-05). D402 (B(9.2, 5.2)) clamps
  J400.2 to GND at the connector; touching the airframe or pad ground before J400 stays the second ESD layer.
- **Dress the J400 pair** twisted, on its own ties, away from the battery leads and from J9's and J122's leads, which
  leave the same aft edge. A chafe from a supply or TX conductor onto J400.2 can hold U9's EN on with the switch open
  (R10's arithmetic: 1.87 V from 4.79 V, above the 1.116 V threshold; for CAM_5V on J9 the same divider gives a higher
  EN, Inference by R10's divider). The per-flight switch-off check below screens it.
- **J400 chatter** (R10's D-R25-01 rule, same EN circuit, stageD_analysis.md §3): record the J400 contact state at
  ≥ 10 kS/s under flight-level vibration; pass only if the total open time in every sliding 100 ms window is under
  7 ms and U9 stays on for the whole run at 5.71 V.

## Pyro pigtail and per-flight checks

**The e-match is never connected at the board** (D-R11-05). J121's pads carry a permanent pigtail (AWG 20, soldered) to
the bay's field terminal at the forward bulkhead; the pigtail runs forward from the west edge (D-R11-13). Keep `E1+`
(J121.2, IGN) and `E1−` (J121.1, OUT) identifiable at the field terminal by its own label. The pigtail plus the
e-match leads must stay inside the fire budget's lead allowance (≤ 0.3 Ω leads, REQUIREMENTS "Igniters"; the fire
budget keeps a 0.010 Ω terminal allowance for the soldered pads, Inference).

**At installation (once per pigtail).** Solder the pigtail, tie it to the sled within 20 mm of the pads (D-R11-05),
and continuity-check it end to end: field-terminal `E1+` to J121.2 (2.3, 20.9), `E1−` to J121.1 (2.3, 24.7), and no
continuity between them or to GND with no match fitted. Record the pigtail's loop resistance (two-wire, meter test
current under 40 mA) on the flight card; the per-flight igniter reading is compared against match + pigtail.

**Per-flight checklist** (R10's numbered list, [ORDERING §8.3](ORDERING.md#83-after-delivery-probes-coating-staking-and-bench-gates),
adapted to R11; run in order, stop at the first failure):

1. **ESD handling.** Touch the airframe or pad ground before touching J400's switch, and keep the screwdriver in contact
   with the grounded airframe before it meets the screw. This is the second layer behind D402.
2. **Board off with J400 open, before any e-match.** With the pack connected and J400 open, confirm the board is off:
   no telemetry and no buzzer, or, with access, RAW_PROTECTED at TP81 (bottom, (7.4, 34)) and 3V3 at J2 pad 1 (top, (31.63, 40.235)) both below 0.3 V. Measure
   **the field terminal's `E1+` contact (J121.2, IGN) to GND** with a floating meter (never an earthed instrument ground on
   an igniter terminal): below 0.1 V. A board that is on means a leak or bridge at the EN network or a chafed J400.2
   lead; a reading above 0.1 V means Q120 / Q121 or their gate bias has failed on. Either way do not fit the e-match.
3. **Closed-switch check with a dummy load.** Fit a 1–2 Ω dummy across the field terminal, then close J400. The board
   powers up, the passive screen passes and firmware raises PC1. Confirm the powered BUS / CONT readings (BUS at least
   0.96 × the VLOGIC_SENSE-derived pack voltage, M3_R10 "Firmware" rule 4; CONT about equal to BUS through the dummy and
   the pigtail) and the PA6 / PA4 log (PA6 = VLOGIC / 11 within tolerance, PA4 low). Open J400: within 1 s the board
   must be off and `E1+` below 0.1 V. Only then remove the dummy. If the modules are not wired yet, also check PORT_4V8
   at pin 1 of J410, J420 and J440 (4.71–4.87 V).
4. **Igniter resistance.** With J400 open, and no USB and no self-powered module attached, fit the e-match at the field
   terminal and measure across it on a meter whose test current is under 40 mA: the selected match's resistance plus
   the recorded pigtail resistance (about 1–2 Ω plus leads), not about 0 Ω and not open. Record it.
5. **Stay-off.** After closing the airframe and before carrying, and again just before closing J400 on the rail,
   confirm no telemetry and no buzzer; on closing J400 confirm a fresh power-up. A board already running means J400 has
   been bypassed: open J400, keep clear, and treat the vehicle as armed.
6. **If the bus may be live** (a cold-screen "bus live" refusal, or a board that stays on with J400 open): keep clear
   and disconnect the e-match at the field terminal (or the pack) before any other handling.
7. **Recovery order.** J400 open; confirm the board is off; confirm the match fired, or disconnect it at the field
   terminal; disconnect the pack; only then connect USB.

**Per-installation check (board off the sled).** Powered NRST must read ≥ 0.90 × 3V3 with a 10 MΩ DMM (R10's
retained ≥ 250 kΩ leakage requirement). On R11, NRST is J2 pad 3 (32.9, 40.235) and 3V3 is J2 pad 1 (31.63, 40.235),
both on the top face (Measured pad positions).

## Battery

- **J1** wire pads: pad 1 BAT_IN (2.3, 14.3), pad 2 GND (2.3, 10.5). The board's battery current includes the fire
  pulse (about 4.2 A into a shorted igniter, 8.4 V / 2 Ω; R10 figure, same circuit), so the pads take AWG 20 (D-R11-05).
- **Route.** The pack is aft of the board; the leads come forward along the west side and turn into J1 from the west
  (D-R11-13). Tie them to the sled within 20 mm of the pads (D-R11-05). Keep them apart from the J121 pigtail, which
  leaves the same edge forward of J1 and runs forward.
- **No battery-lead fuse** (R10 OQ-6): strain relief, no chafe points, soldered leads. The installed harness must
  measure ≥ 0.03 Ω and 0.1–2 µH for the hot-plug model's domain; on R11 every required case passes (Simulation /
  Inference, D-R11-79).

## Board, supports and fit

- **Supports.** Four M3 supports, 3.2 mm holes, at (3.5, 3.5), (42.5, 3.5), (3.5, 46.5) and (42.5, 46.5), pinned in the
  gate data (D-R11-10, -32). Use **nylon (or otherwise insulated) screws, nuts and washers at all four**. Nearest bottom
  envelope J430 3.55 mm from a support centre (≥ 3.5), nearest top body J1.2's wire allowance 3.95 mm (≥ 3.8)
  (Measured, fit_check at stage B). Standoffs ≥ 4 mm as R10 (stageB.md §4).
- **Plate.** Unsupported spans 39 × 43 mm between centres, shorter than any R10 span; the plate model has no r11
  profile and was not run, so stiffness is an Inference (D-R11-10). Require a first-article vibration and shock check.
- **Fit (Measured at stage B, CAD envelopes only; stageB.md §5, §11).** Width 46 mm in the Ø50.8 mm coupler bore, top
  face on the axis. GH mouths sit 1.1 mm inside their edge and the mated GH envelopes stay in the bore; the wire-pad
  allowances (fit_check's 1.8 mm OD model) clear the bore by 0.36 mm (the worst bore margin); the deepest bottom part,
  C421, reaches 2.7 mm below the board. J3's USB-C shell is 0.45 mm proud of the east edge. These figures were not
  re-recorded after the later placement changes (C80 moved to the bottom in D-R11-79, among others); the gate runs
  fit_check on the final board. Real wires, plugs, sled and stack are unverified.
- **GH plugs on the short edges only** (D-R11-12): a plug entering across a long edge would leave the bore.
- **microSD.** J430 is on the bottom at the east edge (37.5, 13.05); open the hinge only with the PCB unbolted from the
  sled, board off and sources disconnected (as R10).
- **U5 (barometer)** is on the bottom at (9.0, 40.0), port facing the sled: the sled must leave it open and vented, with
  an opaque cover that does not press on it (D-R11-14; R10's cover rule).
- **IMU.** U4 on the bottom at (23.0, 20.5) on the roll axis (x = 23); roll = −gyro_Y, thrust −a_Y; bench sign check
  before flight ([M3_R11 IMU axis map](M3_R11.md#imu-axis-map)).
- **Position in the stack.** R10's rule stands: the board wholly forward of joint + 47 mm at every roll orientation
  (OQ-7). R11 is 40 mm shorter than R10; the freed length is not used to move it aft.

## Boot and programming

J2 (TC2030, top) is the SWD port; program with the e-match disconnected. Future programming must record and read back
BOOT_ADD0 and the boot settings, then verify reset reaches the application. With BOOT0 high the ROM loader runs, and
its pins on R11 include PB9 (IMU_CS, held high by R11), PA2 (servo 4), PA15 (servo 2, held low by R155) and PB10 / PB11
(U5's I2C) (stageC1b.md §8.4, §9, D-R11-85; Inference). Keep R10's dummy-load / no-e-match, before-IWDG, PC1 / PE4 locked-low, camera EN / OE low and SD_CS high
service procedure.

## Cost

$79.80 per board (parts + feeder fees, 5 boards, 2026-11-04T01:15:03Z) against the $84.41 cap; U9, U4 and U2 short at
JLC. See [M3_R11.md, "Cost and stock"](M3_R11.md#cost-and-stock).
