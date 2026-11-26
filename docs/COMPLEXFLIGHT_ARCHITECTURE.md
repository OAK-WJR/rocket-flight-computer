# ComplexFlight v1.0: requirements and architecture (stage 1)

Status: **proposal for the owner to read. Nothing is designed yet: no schematic, no board, nothing ordered.**
Written 2026-11-25 on branch `complexflight`, which starts from SimpleFlight v1.0 (M3-ASSY-R12, commit `9c5a40d`,
board `0c681ad6...`). SimpleFlight's files (`m3_design/r12*`, `tools/check_r12.py`, the R12 docs) are not changed on
this branch.

Evidence labels (AGENTS section 2.5): **Datasheet** (read from the maker's document, cited), **Calculation**,
**Inference** (not yet checked against a datasheet or a measurement), **Live** (JLCPCB's public part search, with its
UTC time). Nothing here is measured on hardware.

## 1. What ComplexFlight is

ComplexFlight is SimpleFlight's circuit with more outputs, servo power on the board, the GPS and the radio on the
board, and every wired connection on a screw terminal. It keeps the 46 mm width for the 54 mm airframe and is longer.

| | SimpleFlight v1.0 | ComplexFlight v1.0 (proposed) |
|---|---|---|
| Outline | 46 x 86.85 mm | **46 x about 128 mm** (estimate; ceiling 140 mm) |
| Layers, sides | 4 layers, parts on one side | 4 layers, **parts on both sides** |
| MCU | STM32H743VIH6, TFBGA-100, 82 I/O | **STM32H743ZIT6, LQFP-144, 114 I/O** (same chip, larger package) |
| Servo outputs | 2, signal and ground only | **8, each with signal, power and ground** |
| Servo power | off the board | **own input terminal pair, four protected pairs of outputs** |
| Pyro channels | 1 | **4** |
| GPS | external module on a port | **u-blox MAX-F10S on the board**, antenna on an SMA jack |
| Radio | external module on a port | **EBYTE E22-900MM22S (SX1262) on the board**, antenna on an SMA jack |
| Expansion | one AUX serial port | **two serial ports (one also I2C), CAN, four analog inputs with a 5 V sensor supply** |
| Camera port | yes | yes |
| Wired connections | SH 1.0 mm ports, two screw terminals | **screw terminals only (59 positions)** |
| IMU, barometer, flash, microSD, USB-C, buzzer | ISM6HG256X, MS5611, W25Q128, push-pull socket, yes, yes | unchanged |
| Assembly | JLC Standard PCBA | JLC Standard PCBA |

The counts are my proposals. Section 3 says why each was chosen, and section 13 lists what the owner may want to
change before stage 2 starts.

## 2. Requirements

From the owner (2026-11-25), in the owner's words where quoted:

| ID | Requirement | Source |
|---|---|---|
| C1 | Named ComplexFlight, with the name and a version on the silkscreen (`ComplexFlight v1.0`) | owner |
| C2 | "more servo ports", "more servo outputs, servo power on the board" | owner |
| C3 | Servo power from "It's own servo power input": a separate terminal pair, usable jumpered to the main battery or from a second pack, with the logic and pyro supplies protected from servo stalls in both cases | owner |
| C4 | "I do want more pyro channels." Every channel obeys AGENTS section 2 in full | owner; AGENTS section 2 |
| C5 | "on board GPS and radio", antennas off the board. The radio uplink can never arm or fire a pyro. GPS is for tracking only | owner; parent project decisions |
| C6 | "fully screw terminal IO": battery, servo power, switch, every pyro channel, every servo (signal, power, ground), camera, expansion ports. USB-C, SWD, microSD and the antenna jacks are not terminal IO | owner |
| C7 | "i want similar width, but longer": 46 mm for the 50.8 mm coupler bore; under about 150 mm | owner; parent `docs/VEHICLE.md` |
| C8 | "will likely support any sort of future rocketry project" | owner |
| C9 | Start from SimpleFlight and add to it; take nothing from the R9, R10 or R11 boards | owner |
| C10 | JLC Standard PCBA; lowest reasonable cost without losing function; cost per board at 2 and 5 boards from live JLC reads | owner |

Carried from SimpleFlight without change: every rule of AGENTS section 2 and section 3, and SimpleFlight's functional
requirements in `docs/REQUIREMENTS.md` (F1 to F12, P2, P3, M1, M2) wherever this file does not say otherwise.
What changes: F4 (servos), F7 and F8 (four channels), F10 (GPS and radio on the board), P1 (length), M3 (cost cap, see
section 12).

## 3. The counts, and why

| Item | Count | Why this number | What one more or one fewer costs |
|---|---|---|---|
| Servo outputs | **8** | Flight 2 may need four control surfaces; a later project may add an air brake, a two-axis gimbal or a payload. Eight is two full four-channel timers, so the two halves can run at different frame rates (for example 333 Hz digital and 50 Hz analog servos) | Each servo is three terminal positions: 8.2 mm of board edge. Six servos would save about 8 mm of length |
| Servo power pairs | **4** (two servos each) | One shorted or stalled servo takes down only its partner, not all eight. Each pair has its own current-limited switch | Two banks of four would save two small parts, but a bank of four flight servos could not all stall without tripping (section 6) |
| Pyro channels | **4** | Dual deploy takes two; two are left for staging, an air start or a backup charge. Four two-position terminals are 28 mm and fill the forward edge between the corner supports | Six would not fit the forward edge, and each channel adds its own safety spacing on the copper |
| Serial expansion ports | **2** | AUX1 is a UART. AUX2 can be a UART or an I2C bus on the same two pins. Either can take an external radio or GPS if the on-board one is not used | 10.8 mm of edge each |
| CAN port | **1** | The usual bus between avionics boxes, smart servos and ground equipment. It costs one small transceiver and three terminal positions | 8.2 mm of edge |
| Analog inputs | **4**, with a switched 5 V sensor supply | Pressure transducers, load cells, thermistors, break wires: what a hybrid motor, a static test or a payload needs. They read 0 to 5 V and survive a pack-voltage miswire | 15.8 mm of edge for the six-position block |
| Camera port | 1 | Kept from SimpleFlight | |
| Supports | **6** M3 (four corners and a middle pair) | A 128 mm board spans about 60 mm between supports; SimpleFlight's 86.85 mm board spans 75 mm | |

Left out on purpose: a second IMU or barometer, a magnetometer (useless next to servo current; an external one fits
AUX2), an on-board servo voltage regulator (the servo rail passes through whatever the servo input is fed), a separate
pyro battery input, Ethernet, a second CAN. Each can be argued for; none is needed by C1 to C10.

## 4. Block diagram in words

Power enters at two terminal pairs. **BAT** (the logic and pyro pack, 2S) goes through SimpleFlight's entry (TVS,
damper, the TPS259470A eFuse U9 that also blocks a reversed or 3S pack, and the screw-switch enable chain) to
RAW_PROTECTED. From there SimpleFlight's three converters run: the 3.3 V logic supply (through the diode-OR with USB and
the 470 uF hold-up capacitor), the 4.8 V port rail and the switched 5.4 V camera rail. **SERVO PWR** (the same pack,
jumpered at the terminals, or a second pack) feeds only the servo outputs, through four eFuses.

The pyro bus is SimpleFlight's: it leaves BAT through the P-FET load switch (enabled by the MCU) and then splits into
four channels, each a copy of SimpleFlight's channel 1.

The MCU has SimpleFlight's sensors and storage. New around it: eight servo PWM outputs, the GPS (UART) and the radio
(SPI) on their own quiet 3.3 V supply at the aft end, a CAN transceiver, four protected analog inputs, and current and
voltage monitors on the servo rail.

Along the board, aft to forward (provisional; placement is stage 3): **RF** (two SMA jacks on the aft edge, GPS and
radio modules) | **power** (battery, servo power and switch terminals, eFuses, converters) | **servos** (four servo
terminals on each long edge) | **MCU and sensors** (USB-C, microSD, analog and CAN terminals on the edges) |
**expansion and pyro** (AUX terminals; the four pyro terminals on the forward edge, wires leaving forward toward the
charge wells). The radio and the pyro circuits are at opposite ends on purpose.

## 5. Power tree

```
BAT terminal (2S) -- TVS, damper -- U9 eFuse (reverse / 3S / 4 A limit; enabled by the screw switch) -- RAW_PROTECTED

RAW_PROTECTED --+-- D5 --+-- VLOGIC -- C84 470 uF -- U2 buck -- 3V3 (MCU, sensors, flash, microSD, CAN)
                |        +-- D6 -- USB limit switch -- USB-C VBUS
                +-- U400 buck -- PORT_4V8 --+-- RF regulator (MCU-switched) -- 3V3_RF (GPS, radio, antenna bias)
                |                           +-- limit switch -- AUX1 5 V
                |                           +-- limit switch -- AUX2 5 V
                |                           +-- limit switch (MCU-switched) -- sensor 5 V
                +-- U403 buck (MCU-switched) -- limit switch -- camera 5.4 V

BAT terminal -- Q120 / Q121 load switch (PC1) -- RAW_ACT pyro bus --+-- 2 ohm -- PYRO 1 terminal -- fire FET -- GND
                                                                    +-- 2 ohm -- PYRO 2 terminal -- fire FET -- GND
                                                                    +-- 2 ohm -- PYRO 3 terminal -- fire FET -- GND
                                                                    +-- 2 ohm -- PYRO 4 terminal -- fire FET -- GND

SERVO PWR terminal -- TVS, damper --+-- eFuse A -- servo 1, 2 power
(jumper from BAT, or a second pack) +-- eFuse B -- servo 3, 4 power
                                    +-- eFuse C -- servo 5, 6 power
                                    +-- eFuse D -- servo 7, 8 power
```

Kept from SimpleFlight: everything on the BAT side down to the three converters and the load switch. New: the servo
side, the RF regulator, the limit switches, and the pyro bus fan-out. As on SimpleFlight, the load switch takes the
battery input ahead of U9; with the screw switch open the logic is unpowered and the load switch is held off.

## 6. Servo power (C2, C3)

- **Input.** A two-position 5.0 mm screw terminal beside the battery terminal (Kefa KF301-5.0-2P, SimpleFlight's
  battery terminal part; JLC lists 17 A and 14 to 22 AWG, Live 2026-11-26T02:30Z; the maker's rating is a stage 2
  check). One pack: a short jumper from BAT+ to SERVO+ (the grounds are joined on the board). Two packs: the servo pack
  wires here and shares only ground with the logic pack.
- **Four pairs, each behind its own eFuse.** Proposed part: the TPS259470A that SimpleFlight already uses as U9, so no
  new part type and a land that is already checked. From TI SLVSFC9C (Datasheet): 2.7 to 23 V, 28 milliohm, reverse
  polarity and reverse current blocked, adjustable current limit, under-voltage and over-voltage thresholds, a fault
  flag and a current-monitor output. With a 549 ohm limit resistor the limit is 5.40 to 6.60 A (datasheet section 6.5),
  above two stalled flight servos (2 x 1.92 A = 3.84 A, REQUIREMENTS F4) with 40 % to spare (Calculation).
- **Voltage range.** The servo terminals carry what the input is fed. Designed for a 2S pack (the MKS HV6120 is rated to
  8.4 V); the over-voltage cut-off is set like U9's (9.8 to 10.7 V), so a 3S pack on the servo input is refused instead
  of killing the servos. A solder jumper lowers the under-voltage threshold for a 5 to 6 V servo supply.
- **How the logic and pyro supplies are protected from stalls.**
  - *Two packs:* servo current never flows in the logic pack. A dead short on a servo lead trips that pair's eFuse and
    nothing else notices.
  - *One pack, jumpered:* three layers. (1) Each pair is current-limited, so a short cannot hold the pack down.
    (2) The servo eFuses switch off when the servo input falls below about 5.5 V (proposed; stage 2 sets it), which is
    above the 4.8 V where U9 turns the logic off: if stalled servos sag the pack, the servos are shed first and the
    logic and the pyro bus keep their voltage. The eFuses retry by themselves. (3) SimpleFlight's diode and 470 uF
    hold-up capacitor still carry the logic through short dips.
  - The fire budget in one-pack mode is then taken at the shed voltage, not at a guessed number of stalled servos:
    a hardware bound that SimpleFlight, with servo power off the board, does not have. Rough check (Inference, scaled
    from SimpleFlight's 1.247 A at 5.71 V): about 1.20 A at 5.5 V against the 1.125 A floor. The margin is thin;
    stage 2 computes it properly and may raise the shed voltage.
- **Monitoring.** The MCU reads the servo input voltage and each pair's current, sees a common fault flag and has one
  line that switches all four pairs off (after landing, or on the bench). The pairs are **on by default** with the MCU
  in reset, so a reset does not drop servo power; the PWM signals are held low through reset as on SimpleFlight.
- **Design current.** 15.4 A (eight flight servos stalled) through the input terminal for the length of a stall, about
  8 A continuous (Inference: stage 2 sets the figures and sizes the copper per IPC-2152). The eFuses sit at the input
  terminal and the servo terminals are next to them, so the heavy copper is short.
- **Each servo terminal** is three positions in servo-plug order: signal, power, ground. The signal keeps
  SimpleFlight's 1 kilohm series resistor, pull-down and clamp, so a strand bridging power to signal (8.4 V) passes
  about 5 mA into the clamp and does no damage (Calculation).

## 7. Pyro (C4)

- **Bus.** One load switch (SimpleFlight's Q120 / Q121 with its driver Q122, enabled by PC1) makes the RAW_ACT bus
  from the battery input. The bus is never taken straight from the battery terminal (AGENTS 2.2). One bus-voltage
  sense (PC5), as on SimpleFlight. The screw switch stays the one pad arming device: every channel is treated as
  live whenever the board is on (AGENTS 2.1).
- **Four identical channels.** Each is a copy of SimpleFlight's channel 1: its own 2 ohm series resistor (so a shorted
  igniter on one channel cannot collapse the bus for another, and cannot brown out the logic), its own two-position
  black screw terminal, its own low-side fire FET with the full gate network (series resistor, pull-down at the MCU
  pin, gate-source resistor and capacitor: off in reset and unpowered, AGENTS 2.4), its own cold pull-up and
  continuity divider to its own ADC pin.
- **Fire pins on the MCU.** Four pins on two GPIO ports (E and F), with the bus enable on a third (C): no single
  port write can both enable the bus and fire. On the LQFP each fire pin sits between a ground pin and a pin left
  unconnected, or between two unconnected pins, so a solder bridge to a neighbour cannot drive it high (section 9).
- **Continuity** is read on the ground as a hard refusal and in flight is only logged: it never vetoes a fire
  (AGENTS 2.3). Firmware never fires before launch detection (AGENTS 2.1).
- **One channel fires at a time** (firmware rule; simultaneous events are spaced by tens of milliseconds). The fire
  budget is therefore per channel, with the new loads (radio transmit, GPS, expansion ports) and, in one-pack mode, at
  the servo shed voltage (section 6). The hardware must survive two channels at once; stage 2 checks the load switch
  for that.
- **Radio next to pyro copper (C5).** The 900 MHz transmitter is 22 dBm (158 mW). An e-match's no-fire current of
  0.30 A is 90 mW in a 1 ohm bridge (an assumed resistance), so the leads must never pick up more than a small
  fraction of the transmitted power (Calculation; the real coupling is not known). Measures:
  1. the radio is at the aft end and the pyro block at the forward end, with the pyro leads leaving forward;
  2. every fire-FET gate keeps its capacitor to source, so RF on a gate trace cannot turn a FET on;
  3. each channel's terminal pair gets an RF filter at the terminal (capacitors to ground, and a ferrite bead in each
     leg if the fire budget can carry its resistance; stage 2);
  4. the radio's lines go only to MCU pins on the far side of the package from the pyro pins, and SimpleFlight's
     spacing rule (fire nets at least 1.04 mm from other nets, with its listed exemptions) applies to them too;
  5. firmware: the radio command parser has no arm or fire command and the pyro state machine takes no input from the
     radio task. Arming stays the physical switch;
  6. owner bench test before any flight: radio keyed continuously at full power, antenna in its flight position, an
     inert bridge on every channel; gates, continuity readings and bridge temperature recorded (it goes on the
     validation list).

## 8. GPS and radio (C5)

The parts are the parent project's choices. The facts below were read from the makers' documents on 2026-11-25.

**GPS: u-blox MAX-F10S** (L1 + L5; the MAX-M10S fits the same pads with the same pin functions). Data sheet
UBXDOC-963802114-12732 R03 and integration manual UBXDOC-963802114-12892 R01 (Datasheet):
- Supply 1.76 to 3.6 V; 21 mA acquiring, up to 100 mA inrush. UART at 9600 baud by default.
- The module contains a SAW filter, an LNA and a second SAW stage for both bands; a passive or an active antenna works.
  An active antenna is fed from the module's VCC_RF pin through a bias tee (10 ohm, 47 nH, 10 nF in u-blox's design).
  ComplexFlight fits the bias tee behind a current limit, because VCC_RF may supply only 50 mA and a passive antenna
  that is a DC short would otherwise overload it.
- Limits: 80 km, 500 m/s, 4 g. As the parent project already records, expect no fix near peak speed.
- Its I/O supply must ramp at between 25 us and 35 ms per volt, and its inputs must not be driven while it is
  unpowered. So the RF supply has a controlled ramp, and the MCU parks the GPS lines when the RF supply is off.
- Reflow: 245 C peak, **one upright reflow only** (plus one rework). With parts on both sides the module therefore
  goes on the top, and the top is soldered last (a stage 3 manufacturing rule to confirm with JLC).
- **u-blox publishes no out-of-band immunity data for this module**, and the absolute maximum at its RF input is
  0 dBm. A 22 dBm transmitter a few centimetres away needs more than 22 dB of isolation between the two antenna ports
  just to stay under that. The board gives a filter position in the GPS antenna line and keeps the two RF paths apart;
  the rest is antenna placement in the vehicle and a bench test (key the radio, watch the GPS signal levels).

**Radio: EBYTE E22-900MM22S** (SX1262, 10 x 10 mm). Ebyte E22-M series manual V1.5 and product specification v1.3,
and Semtech's SX1261/2 data sheet Rev 2.2 (Datasheet):
- Supply 1.8 to 3.7 V (3.3 V or more for full power); 118 mA transmitting at 22 dBm, about 5 to 10 mA receiving.
- SPI to 10 Mbit/s, plus NRST, BUSY and DIO1. **The antenna switch is not automatic:** the host must drive TXEN and
  RXEN (TXEN may instead be wired to the chip's DIO2). ComplexFlight wires TXEN to DIO2, so the chip itself switches
  to transmit with the right timing, and gives RXEN to the MCU.
- It uses a plain 32 MHz crystal, not a TCXO (enough for the 500 kHz LoRa channel the project plans; Inference).
- The maker gives no harmonic figures, no land pattern drawing, no moisture level and no reflow count. ComplexFlight
  gives a low-pass filter position between the module and its SMA jack; the land comes from the maker's dimensioned
  outline drawing, checked against Ebyte's own footprint file in stage 2.

**Antennas** are off the board on two edge-launch SMA jacks at the aft edge, overhanging it by about 9.5 mm, as the
vehicle's stack already allows for (parent `docs/VEHICLE.md`, "RF coax loop zone"). Each RF line is a short 50 ohm
grounded coplanar line over an unbroken ground layer.

**RF supply.** The GPS and the radio get their own low-noise 3.3 V regulator from the 4.8 V port rail, switched by
the MCU. They are therefore off on USB-only power, like SimpleFlight's ports, and the radio's 118 mA bursts stay off
the MCU's supply. Stage 2 sets the regulator so that MCU-driven highs stay inside the modules' input limits at both
supplies' corners.

## 9. Pin budget on the STM32H743

**The TFBGA-100 does not have enough pins.** It has 82 I/O; SimpleFlight uses 48. ComplexFlight needs 86 (table
below). The same chip in LQFP-144 (STM32H743ZIT6) has 114 I/O (DS12110 Rev 8, Table 9), leaves 28 spare, and makes the
fire-pin rule easy: a pin on a quad flat pack has two neighbours, a ball in a grid has eight. JLC stock on
2026-11-26T02:28Z (Live): STM32H743ZIT6 C114408, 1476 in stock, $9.73; SimpleFlight's STM32H743VIH6 C964146, 279 in
stock (47 orderable), $8.16. The LQFP is 22 x 22 mm over its leads, which a 46 mm board holds easily.

| Function | I/O | Peripheral and pins (LQFP-144 pin numbers in brackets) |
|---|---|---|
| Crystal, SWD | 4 | PH0, PH1 (23, 24); PA13, PA14 (105, 109) |
| USB | 3 | PA11, PA12 (103, 104); VBUS sense PA9 (101) |
| QSPI flash | 6 | PF8 IO0, PF9 IO1 (AF10); PF7 IO2, PF6 IO3, PF10 CLK (AF9) (18 to 22); PB10 NCS (AF9) (69) |
| IMU | 5 | SPI1 PB3, PB4, PB5 (AF5) (133 to 135); chip select PG10, interrupt PG11 (125, 126) |
| Barometer | 2 | I2C1 PB8 SCL, PB9 SDA (AF4) (139, 140) |
| microSD | 4 | SPI4 PE12, PE13, PE14 (AF5), chip select PE11 (64 to 67) |
| GPS | 4 | USART3 PD8 TX, PD9 RX (AF7) (77, 78); reset PD10 (79); time pulse PA15 TIM2_CH1 (AF1) (110) |
| Radio | 9 | SPI2 PB13, PB14, PB15 (AF5), chip select PB12 (73 to 76); BUSY PD11 (80); DIO1, NRST, TXEN sense, RXEN on PG2 to PG5 (87 to 90) |
| RF supply enable | 1 | PG6 (91) |
| Servo PWM | 8 | TIM4 CH1 to CH4 on PD12 to PD15 (AF2) (81, 82, 85, 86); TIM3 CH1 to CH4 on PC6 to PC9 (AF2) (96 to 99) |
| Servo power | 7 | input voltage PA5; four pair currents PA7, PC4, PB0, PB1 (all ADC); fault PF14; off PF15 |
| Pyro | 10 | bus enable PC1 (27); bus sense PC5 (45); fire PE4, PF5, PF12, PE9 (3, 15, 50, 60); continuity PC0, PC2_C, PC3_C, PA0 (26, 28, 29, 34) |
| Supply monitors | 5 | VLOGIC PA6 (42); battery fault PC13; port rail PF13; camera rail PF3; camera enable PC12 |
| Camera | 2 | UART4 PC10 TX, PC11 RX (AF8) (111, 112) |
| AUX1 | 2 | USART6 PG14 TX, PG9 RX (AF7) (129, 124) |
| AUX2 | 2 | PB6, PB7 (136, 137): USART1 TX / RX (AF7) or I2C4 SCL / SDA (AF6) |
| CAN | 3 | FDCAN1 PD0 RX, PD1 TX (AF9) (114, 115); standby PD2 |
| Analog inputs | 4 | PA1, PA2, PA3, PA4 (ADC1 INP17, 14, 15, 18) (35, 36, 37, 40) |
| Port power | 2 | common fault PD3; sensor 5 V enable PD4 |
| LEDs, buzzer | 3 | PG7, PG8; PE6 TIM15_CH2 (AF4) |
| **Total** | **86** | of 114; 28 spare, of which 5 are the fire pins' unconnected neighbours |

- **Sources.** Pin numbers are from KiCad 10's `STM32H743ZITx` symbol, spot-checked against DS12110 Rev 8 Table 9
  (PE4 3, PF5 15, PF12 50, PG8 93). Alternate-function numbers are from DS12110 Rev 8 Tables 10 to 16 (pages 89 to
  99), read from a text extraction of the datasheet. The map shows that a conflict-free assignment exists. **It is
  provisional:** stage 2 writes the binding `pin_table.tsv`, checks every row against Table 9 and against the ROM
  bootloader's pin list (AN2606), and stage 3 may swap pins within a peripheral's alternatives to suit the placement.
- **Kept from SimpleFlight** so its firmware rules carry over: PE4 (fire, active high), PC1 (bus enable), PC0
  (continuity), PC5 (bus sense), PA6 (VLOGIC and its analog watchdog), PC13, PC12, USART3 for the GPS, UART4 for the
  camera, SPI1 for the IMU, SPI4 for the card.
- **Fire-pin neighbours.** PE4 (3) sits between PE3 and PE5, both unconnected. PF5 (15) between PF4 (unconnected) and
  VSS. PF12 (50) between PF11 (unconnected) and VSS. PE9 (60) between PE8 (unconnected) and VSS. PC1 (27) between PC0
  and PC2_C, both continuity inputs with no driven-high state (SimpleFlight accepts the same kind of neighbour). None
  of the four fire pins has a role in the ROM bootloader (Inference, from memory of AN2606; stage 2 reads it).
- Never enable synchronous trace (PE4 is TRACED1). VREF+ (pin 32, bonded out on this package) is tied to the filtered
  analog supply and the internal reference buffer stays off, as on SimpleFlight.
- The firmware clock limit stays 200 MHz (SimpleFlight's thermal and 3V3 budget; stage 2 re-runs it).

## 10. Terminals and the board edge

All terminals are side-entry screw terminals whose wires leave over a board edge.

| Terminal | Positions | Part (JLC code; Live 2026-11-26T02:30Z) | Length on the edge | Edge |
|---|---|---|---|---|
| BAT | 2 | Kefa KF301-5.0-2P, blue (C474881) | 10.3 mm | long, aft half |
| SERVO PWR | 2 | Kefa KF301-5.0-2P (C474881; another colour if one is stocked) | 10.3 mm | long, beside BAT |
| SWITCH | 2 | DORABO DB125-2.54-2P (C918120) | 5.7 mm | long, beside BAT |
| SERVO 1 to 8 | 8 x 3 | DORABO DB125-2.54-3P (C918121) | 8 x 8.2 mm | four on each long edge |
| CAM | 4 | DORABO DB125-2.54-4P (C918122) | 10.8 mm | long |
| AUX1, AUX2 | 2 x 4 | DORABO DB125-2.54-4P (C918122) | 2 x 10.8 mm | long |
| CAN | 3 | DORABO DB125-2.54-3P (C918121) | 8.2 mm | long |
| ANALOG | 6 | DORABO DB125-2.54-6P (C918124) | 15.8 mm | long |
| PYRO 1 to 4 | 4 x 2 | DORABO DB125-3.5-2P, black (C52993880; SimpleFlight's pyro terminal) | 4 x 7.0 mm | **forward edge**, wires leave forward |
| **Total** | **59** | six part codes | 148 mm on the long edges, 28 mm on the forward edge | |

Not terminals: USB-C (9 mm of a long edge), microSD (14 mm of a long edge), two SMA jacks (aft edge), the SWD
contact pattern (no edge).

The DB125-2.54 family is 2.54 mm pitch, 18 to 26 AWG, 8.4 mm tall and 7 A in JLC's listing (Live); its lengths above
are estimates (positions x 2.54 mm plus end walls) until the maker's drawing is read in stage 2. The 3.5 mm pyro
terminal and the 5.0 mm battery terminal are SimpleFlight's parts and lands.

**Edge count (Calculation).** Long-edge items: 148 mm of terminals + 9 (USB-C) + 14 (microSD) + about 8 mm of gaps =
about 179 mm, so 90 mm on each long edge. Each long edge also loses about 20 mm at the aft end (SMA jacks, the RF
block and the aft support), 9 mm at the forward end (the pyro row and the forward support) and 8 mm at the middle
support. 90 + 20 + 9 + 8 = **about 127 mm**. The estimate is therefore **46 x about 128 mm**, to be fixed by the
stage 3 placement, with 140 mm as the ceiling.

**Why parts go on both sides (Inference from part sizes).** The terminal rows and their wire-exit strips take about
11 mm along each long edge. What is left on the top face, after the supports, is about 4000 mm2 at 128 to 140 mm
long. The non-terminal parts need about 3300 mm2 of courtyard: SimpleFlight's 1650 mm2 plus about 1700 mm2 for the
larger MCU, the RF block, three more pyro channels, the servo power parts and the new ports. That is over 80 % full;
SimpleFlight routes at about 50 %. With small parts on the bottom the board is about 35 to 40 % full. A one-sided
ComplexFlight would be about 180 mm long. So the MCU, modules, connectors, tall parts and every fire-path part go on
top; decoupling and other small passives go on the bottom, none taller than the sled clearance. Two-sided Standard
assembly costs $33.77 more per order than one-sided ($83.96 against $50.19 in fixed fees, REQUIREMENTS M3).

## 11. Fit in the vehicle

From the parent repository's `docs/VEHICLE.md` (Calculation on its figures; its recovery length is an estimate):

- **Width.** 46 mm in the 50.8 mm coupler bore, top face on the bore axis, as SimpleFlight. The terminals are
  8.4 to 8.6 mm tall and their outer top corner sits about 19.6 mm from the axis: 21.4 mm from the centre against a
  24.6 mm limit (bore radius less 0.5 mm wall allowance and 0.3 mm sled tolerance).
- **Wire exit.** Wire faces sit at least 3.35 mm inside the board edge, as SimpleFlight's pyro terminal does for its
  4.95 mm wire room in the bare bore. The pyro leads leave the forward edge axially and need no bend room.
- **Length.** Main-section free length 595 mm: battery bay about 80, battery-lead and coax zone about 48 (this
  already holds the SMA plugs), **board 128**, eyebolt nut and charge wiring about 25, recovery about 260. That leaves
  about 54 mm of slack (42 mm at the 140 mm ceiling). The board's aft edge sits near joint + 80 mm, wholly forward of
  the camera shroud (joint + 4 to + 47 mm); its first 40 mm or so are in the 50.8 mm coupler bore and the rest in the
  54.6 mm tube.
- **Open vehicle items.** Where a second (servo) pack goes; whether 24 servo wires, split 12 per side, fit between the
  terminal faces and the tube wall on their way aft (about 4 x 10 mm of channel on each side; a CAD or mock-up check);
  the sled's clearance under bottom-side parts.

## 12. Manufacturing and cost

- JLC Standard PCBA, both sides, four layers, 1.6 mm, ENIG, SimpleFlight's design rules (0.10 mm track and gap,
  0.3 / 0.45 mm through vias, none in a soldered pad). The MCU is a 0.5 mm pitch LQFP: no BGA. The RF lines need JLC's
  JLC04161H-7628 stack-up for their 50 ohm width (parent report "Compact rocket GPS and radio").
- A board longer than 100 mm leaves JLC's cheapest four-layer price step (SimpleFlight's cost study). Inner copper
  weight (0.5 oz as SimpleFlight, or 1 oz for the servo current) is a stage 2 decision.
- **Cost, rough (Inference; the stage 3 live run replaces it).** SimpleFlight is $83.96 / $56.88 per board at 2 / 5
  boards for parts and feeder fees. ComplexFlight adds about $17.39 (MAX-F10S), $6.54 (E22-900MM22S), $1.57 (LQFP
  instead of BGA), $4.60 (four eFuses), $6 (terminals), $8 (other parts), and about 20 more part codes at $1.53 each
  per order. That gives roughly **$143 per board at 2 boards and $107 at 5**, plus JLC's fixed fees ($83.96 per order
  for two sides) and the bare boards. Unit prices are Live reads of 2026-11-26T02:28Z to 02:46Z.
- That is above REQUIREMENTS M3's cap ($84.41 per board at 5), which was written for the one flight computer. The cap
  cannot hold for a board with a $17 GPS and a $7 radio on it; ComplexFlight needs its own target from the owner
  (section 13).
- Stock today (Live, same reads): MAX-F10S C30005563 114; E22-900MM22S C5333985 220; STM32H743ZIT6 1476;
  TPS259470ARPWR C3662799 4122; every terminal in the table above in the thousands except the black DB125-3.5-2P
  (1145).

## 13. Decisions taken, and what the owner may want to change

Each is my call under "decide from the requirements, flight physics and the exemplars". None is built yet, so each is
cheap to change now and expensive after stage 3.

| ID | Decision | Alternative |
|---|---|---|
| D-CF-01 | 8 servos, 4 pyro channels, 2 serial ports, 1 CAN, 4 analog inputs (section 3) | Any count; fewer servos or no analog block shortens the board by 8 to 16 mm |
| D-CF-02 | MCU package LQFP-144 (section 9) | Keep the TFBGA-100 and cut to about 6 servos, 2 pyro channels, no CAN and no analog inputs |
| D-CF-03 | Parts on both sides, about 128 mm long (section 10) | One side at about 180 mm, which does not fit under 150 mm |
| D-CF-04 | Servo power as four eFuse-protected pairs from one input; servos shed first in one-pack mode (section 6) | One bank with a larger switch; no shedding |
| D-CF-05 | Pyro terminals on the forward edge, radio at the aft end (sections 4, 7) | |
| D-CF-06 | GPS and radio on their own switched 3.3 V regulator, off on USB-only power (section 8) | Run them from the logic 3.3 V |
| D-CF-07 | Protections put back that SimpleFlight left out: USB data ESD and a USB current limit, ESD on every terminal signal, a current limit on each 5 V output and on the camera supply. Not put back: camera UART isolation (a series resistor and a clamp are enough; the rule against self-powered devices stays) | |
| D-CF-08 | Antenna jacks are edge-launch SMA on the aft edge | U.FL on the board |
| D-CF-09 | Names: design directory `m3_design/cf1/` (KiCad project `m3.kicad_pcb` inside it, as R12's), generators `m3_design/cf1_*.py`, decision record `m3_design/cf1/design/CF1_DECISIONS.md` (IDs D-CF-nn, continuing this table), gate `tools/check_cf1.py` with a `cf1` profile in `fit_check`, `route_check` and `tools/check.sh`, records `docs/COMPLEXFLIGHT.md`, `docs/COMPLEXFLIGHT_VALIDATION.md` and `docs/COMPLEXFLIGHT_VEHICLE_HANDOFF.md` | |

Questions for the owner (work continues on the defaults above if there is no answer):

1. Are 8 servos and 4 pyro channels the counts you want?
2. Are a CAN port and a four-input analog block worth about 24 mm of board edge to you?
3. One pack or two for flight 2? One-pack mode works, but it sheds the servos when the pack sags below about 5.5 V.
4. Should the servo input also take a 5 to 6 V supply (the solder jumper), or 2S only?
5. What cost per board is acceptable? The rough figure is $107 at 5 boards for parts and feeder fees.

## 14. What is reused and what is new

| Reused from SimpleFlight (circuit, part and safety network unchanged) | New in ComplexFlight |
|---|---|
| Battery entry: terminal, TVS, damper, U9 eFuse, screw-switch enable chain | MCU package (LQFP-144) and its whole pin map |
| VLOGIC diode-OR, 470 uF hold-up, PA6 trip | Servo power input, four eFuses, servo rail monitors |
| 3.3 V, 4.8 V and camera converters | Servo outputs 3 to 8 (copies of SimpleFlight's output cell) |
| Pyro load switch and channel 1, with every gate network | Pyro channels 2 to 4 (copies), bus fan-out, RF filters at the pyro terminals |
| IMU, barometer, QSPI flash, microSD, crystal, SWD, USB-C, buzzer, LEDs | MAX-F10S, E22-900MM22S, their regulator, RF lines and SMA jacks |
| Servo output cell (1 kilohm, pull-down, clamp) | CAN transceiver; analog inputs; 5 V limit switches; ESD parts |
| The generators' structure, `check_r12.py`'s rules, the fire, hold-up and hot-plug models | Every terminal except BAT and PYRO 1; placement and all copper |

Every carried rule is checked again on ComplexFlight's own copper: nothing is assumed to hold because it held on
SimpleFlight. No circuit, placement or copper comes from R9, R10 or R11.

## 15. Open risks

1. **Radio beside e-match leads and beside the GPS.** No coupling figure exists until it is measured. u-blox gives no
   out-of-band immunity data for the MAX-F10S, and its input limit is 0 dBm. Both end in owner bench tests.
2. **Board area.** The 128 mm estimate rests on part-size estimates and on parts fitting on the bottom. If stage 3
   cannot close it, the length grows toward 140 mm before any function is cut.
3. **One-pack mode.** Protecting the logic by shedding the servos is sound, but the fire-current margin at the shed
   voltage is thin (about 1.20 A against 1.125 A, Inference), and the port and camera converters are near drop-out
   there, as they are on SimpleFlight at four stalls. Stage 2 may have to raise the shed voltage, which makes one-pack
   flights shed sooner.
4. **Servo current on a 46 mm four-layer board.** 15 A through one terminal pair, and four 2 x 2 mm eFuses at about
   0.4 W each with two servos stalled (Calculation from 28 milliohm typical; hot resistance is higher). Copper and
   thermal budgets are stage 2 work; 1 oz inner copper or a larger switch are the fall-backs.
5. **Four fire channels under SimpleFlight's spacing rules.** Each fire net needs about 1 mm to every other net over
   its whole run. SimpleFlight's spacing check carries 203 measured exceptions, 51 of them on its one channel's fire
   nets; the count for four channels is unknown until the copper exists.
6. **Wire volume in the 50.8 mm bore** (section 11): 59 screw positions, 24 of them servo wires.
7. **Two-sided assembly** with modules that allow one reflow (section 8) and through-hole terminals over bottom-side
   parts: JLC's process order and soldering clearances must be confirmed before placement is frozen.
8. **E22-900MM22S documentation gaps:** no harmonic data, no maker land pattern, no moisture level.
9. **Cost** is above the present cap, and the GPS module is a single-source $17 part with 114 in stock.
10. **Firmware does not exist** for either board, and ComplexFlight's pin map differs from SimpleFlight's wherever
    the package forced it.

## 16. Stages

| Stage | Output | Done when |
|---|---|---|
| 1 (this file) | Requirements and architecture | Committed and pushed; the owner reads it |
| 2 | Circuit, parts from datasheets with sources, pin table, budgets (fire, hold-up, 3V3, servo rail, thermal), schematic checks, `CF1_DECISIONS.md` | ERC and netlist contracts pass; budgets close |
| 3 | Placement, hand routing, `tools/check_cf1.py` with every carried SimpleFlight rule on the real copper, fab package, live cost and stock | Two identical builds; `tools/check.sh` exits 0 |
| 4 | Review rounds until two consecutive full rounds have zero Critical and zero Major, fix passes, records and the owner validation list | Not accepted, nothing ordered; the owner decides |

## Sources

- STM32H742xI/G, STM32H743xI/G datasheet, DS12110 Rev 8 (ST): Table 9 (pin definitions), Tables 10 to 16 (alternate
  functions). https://www.st.com/resource/en/datasheet/stm32h743zi.pdf
- TPS25947xx datasheet, SLVSFC9C (TI): features, section 6.5. https://www.ti.com/lit/ds/symlink/tps25947.pdf
- MAX-F10S data sheet UBXDOC-963802114-12732 R03 and integration manual UBXDOC-963802114-12892 R01 (u-blox):
  https://content.u-blox.com/sites/default/files/documents/MAX-F10S_DataSheet_UBXDOC-963802114-12732.pdf and
  https://content.u-blox.com/sites/default/files/documents/MAX-F10S_IntegrationManual_UBXDOC-963802114-12892.pdf
- E22-M series user manual V1.5 and E22-900MM22S product specification v1.3 (Ebyte):
  https://www.cdebyte.com/products/E22-900MM22S and https://jlcpcb.com/partdetail/C5333985
- SX1261/2 data sheet DS.SX1261-2.W.APP Rev 2.2 (Semtech), read from a mirror; Semtech's own copy is to be re-read in
  stage 2.
- Parent repository: `docs/VEHICLE.md`, `reports/Compact rocket GPS and radio.md`, `docs/AGENT_POLICY.md`.
- This repository: `docs/REQUIREMENTS.md`, `docs/M3_R12.md`, `m3_design/r12/design/pin_table.tsv`,
  `m3_design/r12/design/r12_plan.md`, `m3_design/r12/design/cost_study.md`.
- JLCPCB public part search (Live), 2026-11-26T02:28Z to 02:46Z.
