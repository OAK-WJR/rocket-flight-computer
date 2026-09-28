# M3-ASSY-R2 first power-up (bench)

Do these steps in order on each new board. **Stop at the first step that fails**, and record the reading with the board ID. Nothing in this document needs R2 firmware. The MCU is blank from the factory. **Do not flash v0.8.1** (it is R1 firmware).

Equipment:
- current-limited bench supply
- multimeter
- USB-C cable with a current meter
- ST-LINK (or any SWD probe)

For the first power-ups, have **no igniter, no arming plug, no servo, no camera** connected.

Test-point positions (x, y in mm, top view, origin at the J1 battery end):

| Test point | Net | Position |
|---|---|---|
| TP80 | BAT_IN | 8.5, 8.5 |
| TP84 | BAT_ENABLE | 7, 18 |
| TP85 | BAT_FAULT_N | 7, 23 |
| TP88 | GND | 7, 28 |
| TP87 | LOGIC_SOURCE_ST | 10, 30 |
| TP82 | USB_LIMITED | 42, 12 |
| TP86 | USB_FAULT_N | 42, 17.5 |
| TP83 | VLOGIC | 41, 20 |
| TP89 | BAT_ILIM | 24, 13.5 |
| TP81 | RAW_PROTECTED | 23, 31 |
| TP121 | ACT_GATE | 16.8, 35.5 |
| TP120 | RAW_ACT | 42.5, 36.4 |
| TP123 | PYRO2_GATE | 26.6, 49.1 |
| TP124 | GND | 17.9, 58 |
| TP122 | PYRO1_GATE | 26.6, 64 |
| TP71 | CAM_INPUT_LIMITED | 29, 101 |
| TP72 | CAM_5V | 33, 121 |
| TP90 | CAM_IO_3V3 | 17, 146 |
| TP92 | VBUS_SENSE | 18, 180.5 |

3V3 is on **J2 pin 5**; J2 pin 1 is GND.

## 0. Unpowered

Measure resistance to GND on each rail:

| Rail | Measure at | Expected |
|---|---|---|
| BAT_IN | TP80 | no short, above about 1 kΩ (TVS and dividers) |
| VLOGIC | TP83 | no short |
| 3V3 | J2.5 | no short |
| RAW_ACT | TP120 | no short, about 15 kΩ (R124 + R125) |

A reading under about 10 Ω on any rail: **stop**. Look for solder bridges and parts placed the wrong way round (preview checklist, `ORDERING.md` §4).

## 1. USB only (battery disconnected)

Plug USB-C in through the current meter. With a blank MCU, expect a small draw. **Above 200 mA: unplug.**

| Point | Expected | Derivation |
|---|---|---|
| TP92 VBUS_SENSE | ≈ 3.09 V | 5.0 V × 10k / (6.2k + 10k) |
| TP82 USB_LIMITED | ≈ 5.0 V | TPS2553 on |
| TP86 USB_FAULT_N | ≈ 3.3 V (high = no fault) | pull-up |
| TP83 VLOGIC | ≈ 4.9–5.0 V | TPS2121 selects USB |
| J2.5 3V3 | 3.30 V ± 3 % | AP63203 fixed 3.3 V |
| TP81 RAW_PROTECTED, TP120 RAW_ACT | ≈ 0 V | no battery |
| TP122 / TP123 pyro gates | 0 V | pull-downs, MCU blank |
| TP72 CAM_5V, TP90 CAM_IO_3V3 | 0 V | camera off by default |

## 2. SWD

Connect the probe to J2: pin 1 GND, pin 5 3V3 reference, SWDIO/SWCLK, NRST on pin 4, BOOT0 on pin 6. Leave BOOT0 open.

Read the device ID:

```sh
pyocd cmd -t stm32h743xx -c "read32 0x5C001000"
```

Expected: DBGMCU_IDCODE `0x...450`, the H743 device ID. This proves the MCU, its supply, reset, VCAP and debug path are working.

## 3. Battery input (USB unplugged)

- Bench supply at **7.4 V, current limit 0.3 A**, into J1 BAT+/GND.
- External switch **open** (J1.3–J1.4 not bridged):

  | Point | Expected |
  |---|---|
  | TP80 BAT_IN | 7.4 V |
  | TP84 BAT_ENABLE | 0 V |
  | TP81 RAW_PROTECTED | 0 V |
  | TP120 RAW_ACT | 0 V |
  | TP121 ACT_GATE | ≈ 6.8 V (gate held near the source) |
  | Supply current | ≈ tens of µA |

- **Bridge J1.3–J1.4** (switch closed):

  | Point | Expected | Derivation |
  |---|---|---|
  | TP84 BAT_ENABLE | ≈ 1.62 V | 7.4 × 280k / 1.28M; UVLO rising at 1.20 V ↔ 5.49 V battery |
  | TP81 RAW_PROTECTED | ≈ 7.4 V | |
  | TP83 VLOGIC | ≈ 7.4 V | highest-voltage source |
  | J2.5 3V3 | 3.30 V | |
  | TP85 BAT_FAULT_N | ≈ 3.3 V | |
  | TP121 ACT_GATE | ≈ 0.67 V | 7.4 × 10k / 110k; the actuator switch is on |
  | TP120 RAW_ACT | ≈ 7.4 V | |

- **UVLO check:** lower the supply slowly. RAW_PROTECTED must switch off at about 5.0 V (falling threshold 1.09 V ↔ 4.98 V). Raise it again; it comes back at about 5.5 V.
- **Reverse polarity check** (optional, only with a current-limited supply): set −7.4 V at 0.1 A. The current must stay near zero and nothing may warm.

## 4. With firmware (R2 bring-up image — to be written)

1. ADC readings compared with the multimeter:
   - VLOGIC_SENSE, V3V3_SENSE, RAW_ACT_SENSE, VBUS_SENSE, CAM_5V_SENSE (PB1, ÷11);
   - PYRO1/2_CONT and ARM1/2_SENSE, plug out. Expected plug-out values are in `m3_design/sim_r2/RESULTS.md` §E:

     | State | Ratiometric reading |
     |---|---|
     | Shorted FET | 0 mV |
     | Good igniter | 95–100 mV |
     | Open igniter | 141–148 mV |

2. IMU WHO_AM_I, barometer PROM CRC, flash JEDEC ID, GNSS NMEA on USART6, USB CDC enumeration.
3. Camera branch: enable CAM_PWR_EN; CAM_5V should read ≈ 5.25 V and CAM_IO_3V3 ≈ 3.3 V.
4. Actuators, in this order and **only with dummy loads**:
   1. Servo PWM with one servo.
   2. Buzzer.
   3. Pull-pin input.
   4. Pyro:
      - use 1 Ω / 5 W dummy loads, not igniters;
      - insert the arming plug last;
      - fire 20 ms per channel;
      - watch that BAT_IN stays above 5 V (`M3_ACTUATOR_MERGE.md` §4 lists the full bench list: plug-insertion test ×20, cold pull-up table, stall thermal).

Record every reading in the board's log. Only after all of this is a board a candidate for anything beyond the bench.
