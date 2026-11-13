# R12 vehicle integration handoff

**Status.** PCB `c9b9f0fa984123d38e96ceb578c020b1107eda4cb380008f9ef6513fb9d78770`, 46 × 86.85 × 1.6 mm (D-R12-174),
four layers, every part on the top face and assembled by JLC. R12 remains a CAD candidate, not accepted,
nothing ordered; R9 stays accepted. Current state: [M3_R12.md](M3_R12.md#current-state); owner items:
[R12_VALIDATION.md](R12_VALIDATION.md). No physical fit is claimed.

Coordinates are board mm: x east (0 … 46), y forward from the aft edge (0 … 86.85), top face F.
Current centres are `m3_design/r12_place.tsv` on `c9b9f0fa…` (Measured). All positions below are on this board.
J1's terminal set the 86.85 mm outline (D-R12-174); round 12 adds R118 without moving existing parts.

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
| J2 SWD, TC2030 pads (top, centre (32.8, 48.85), rotation 90) | — | 3V3 (33.435, 50.12) | SWDIO (32.165, 50.12) | NRST (33.435, 48.85) | SWCLK (32.165, 48.85) | GND (33.435, 47.58) | NC (32.165, 47.58) |

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
    6.1–6.6 V (TI SLVSD90B §7.3, D-R12-131). During a four-stall fire (U400 VIN about 5.4988 V) or on a 6.0 V pack
    (about 5.4206 V) it rests on U400's frequency foldback, an Inference (M3_R12 "Power"; bench item R12_VALIDATION row
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
- **J400 chatter (D-R12-183; Calculation / Inference).** BAT_IN is a network with J1.1,
  U9.5, Q120.3 and R80.1 terminals. EN is evaluated at R80.1, not J1. At the four-stall GAP-1 point,
  J1 is 5.71941 V and R80.1 is 5.70082 V (18.6 mV lower). Single drop-out immunity is
  7.967 / 7.446 ms initial / drift; periodic limits are 7.410 / 6.935 ms.
  Whole-current loading gives J1 5.70765 V, R80.1 5.68849 V, fire current 1.24573 A and the worst
  periodic limit **6.843 ms**. The 7 ms line fails both conventions. The bench pass rule is **under 6.7 ms
  total open time in every sliding 100 ms window**, recorded at **≥ 10 kS/s under flight-level vibration**,
  with **U9 on throughout at 5.72 V**. This supersedes D-R12-170's historical 6.9 ms rule; the margin to
  the worst model limit is 0.143 ms. `en.chatter_rule.bench_rule_ms` stores 6.7 and the gate checks both
  load conventions. Turn-on is 30.3–131.5 ms initial / 29.9–135.9 ms drift over C87 0.72–1.265 × 220 nF.
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
(−0.1258 / −0.1705 V below the trip top; Calculation / Inference), so this rule is required. A healthy
four-stall fire is +0.0270 V clear of the trip top at drift (Calculation / Inference). A PA6 trip outside
a fire pulse is battery loss as before (hold-up 0.471–1.897 ms unshed at drift, Calculation / Inference).
Firmware and bench qualification remain open.

## Pyro and per-flight checks

The e-match connects at J121's screw terminal: `E1+` to pin 2 (IGN), `E1−` to pin 1 (OUT). The match must be ≤ 2 Ω and its
leads ≤ 0.3 Ω (the fire budget's separate allowances). At four stalls the fire current is 1.24833 A at BAT_IN 5.71941 V against the
MJG J-Tek 1.125 A floor (Calculation / Inference).

**Per-flight checklist.** This is R10's list ([ORDERING §8.3](ORDERING.md#83-after-delivery-probes-coating-staking-and-bench-gates))
adapted to R12. Run it in order and stop at the first failure. Confirm the installed J400 switch/harness
has passed the R12 chatter bench rule: under 6.7 ms total open time in every sliding 100 ms window,
recorded at ≥ 10 kS/s under flight-level vibration with U9 on throughout at 5.72 V (D-R12-183).

0. **Plug identity and retention.**
   - **0b — plug identity:** before mating, identify every plug against its port legend. J400 takes only the switch
     lead. Give the switch and camera leads distinct tags. Repeat step 2 after any plug is moved.
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
- **U5 barometer** (MS5607) on the top face at (23.0, 32.25), rotation 180. Keep its port open and vented, under an opaque cover that
  does not press on it (R10's cover rule).
- **IMU.** U4 at (23.0, 45.45), rotation 180, on the roll axis (x = 23; lever arm x = 0, unchanged): roll = −gyro_Y,
  thrust −a_Y. U6 at (23.0, 38.25), rotation 180, is now on the roll axis too (x = 0); its axial channel is channel 1.
  The axis maps are D-R12-54's (Calculation / Inference: both rotations unchanged; inherited axis frames). A bench sign check is needed before flight ([M3_R12 IMU axis map](M3_R12.md#imu-axis-map)).
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
and U4/U5/U6 bodies. Keep J2 clear until after the final SWD session, then protect it with polyimide and
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
include PA9 (SERVO4), PB10 (QSPI_NCS), PB6/PB9 (barometer SCL/IMU_CS), PA8/PC9 (SERVO3/VBUS_SENSE),
PA6 (VLOGIC_SENSE), PC11 (camera UART) and PE13 (SD MISO); USB uses PA11/PA12. Physical loader checks
remain O-R12-23. NRST's filter capacitor C24
is at J2's end of the NRST run (26.6, 49.03) (D-R12-98). R10's dummy-load / no-e-match service procedure
applies: PC1 / PE4 locked low, camera EN low, SD_CS high and HG_CS high.

For the separate first-article dummy-fire check, use the fixed 2 Ω dummy / 0.3 Ω total leads and 7.4 V / 0.15 Ω
source with the budget converter loads and no servo stalls. Reject BAT_IN − RAW_ACT above **0.4 V**, overriding
R10 rule 4's 0.2 V line (D-R12-109). At R134's drift low end 1.9666 Ω, current is 1.52468 A and the drop
bound **0.27318 V**, including hot FETs, 29.975 mΩ loop copper and converter coupling through BAT_IN
(Calculation / Inference; D-R12-183). The body-diode case is 0.7–1.0 V (Inference). Qualify this line on the
first article; the per-flight closed-switch check does not command a fire.

## Cost

Parts + feeder **$62.50 / $43.16 per board at 2 / 5 boards**, against the $84.41 cap (Live
2026-11-13T10:35:38Z / 10:37:57Z): 60 BOM lines (24 Extended / 36 Basic), 185 JLC parts, 21 charged codes,
$30.27 parts per board and $64.47 feeder fees per order. There are 595 paste flashes and no owner BOM.
Stock 2026-11-13T10:34:51Z / 10:36:33Z: no line short or thin at either quantity. Orderable quantity is an
Inference about JLC's field. The 2026-11-11 all-in quote of $165.33 for two assembled boards before shipping
was for historical `1d7562d5…`; re-quote `c9b9f0fa…`, including X-ray, DFM and reflow acceptance. Nothing ordered.

See [M3_R12.md](M3_R12.md#cost-and-stock).
