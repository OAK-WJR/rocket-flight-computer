# R10 barometer diagnostics

The fitted U5 is TE MS561101BA03-50 / C15639. `verify.py` checks the native
R10 netlist/pin-table hashes, source part and sixteen endpoints: PB8/PB9 to
SCL/SDA, PS/VDD on 3V3A, both CSB pads on GND, SDO through R64 to GND, and
R12/R13 pull-ups to **3V3**, a distinct rail. CSB low selects seven-bit `0x77`.

The portable acquisition core and [native I2C1 port](I2C_PORT_CONTRACT.md) are
linked into the bench diagnostic image. Only PB8/9 are configured for this port;
SPI1's PB3/4/5/7 and other GPIO fields are preserved. The port checks its clock
contract without rewriting shared selectors. Polling and cleanup have finite
iteration budgets independent of SysTick. A blocked bus is reported, with no
silent GPIO bit-bang recovery. A stalled CPU/MMIO bus is outside that bound.

## Acquisition and retained evidence

After an initial 10 nominal ms power guard, the core resets U5, waits five
nominal ms for PROM reload, reads all eight words and checks CRC4. Zero/floating
calibration banks fail independently of CRC4. It then takes sequential D1 and D2
conversions at OSR4096. The manufacturer's conversion maximum is 9.04 ms; the
engineering guard is 12 nominal ms and starts on a poll **after** each command
callback has returned. These waits are not measured timing qualifications.

Compensation uses the repository's existing pure integer MS5611/CRC functions,
not the legacy firmware's pin map or executable binding. No altitude, flight
state or control output is calculated. D1/D2 zero or all-ones and out-of-range
results remain diagnostic failures, with raw observations retained.

Candidates and last-good samples are separate. A complete pair is committed
only on a subsequent poll, using its new timestamp after all callbacks and
compensation. Pair age starts before the D1 command, not at final read/commit.
A pair older than 250 nominal ms is rejected as `PAIR_STALE`; it cannot replace
last-good values. Both delayed polling and callbacks crossing the age boundary
are covered by C tests. The calibration bank belonging to the last-good pair
is retained separately from a later partial or failed PROM read.

Errors invalidate current data and retain message detail, cumulative message
errors, retry count and last error. Reinitialization occurs after one nominal
second; a transport failure latches further messages off until then. MCU
heartbeat and IMU diagnostics continue independently. A core FAULT record
withholds both sensors because an exception can interrupt their updates.

## Record and host view

ABI v3 is 512 bytes, CRC32 at byte508. Words64–97 hold phase/error, flags,
counts, acquisition/read/commit times, candidate and last-good raw D1/D2,
pressure in Pa, temperature in 0.01 °C, current/sample PROM banks, PROM CRC4,
message errors, nominal bus frequency and recovery history. Other documented
reserved words remain zero. The host independently checks calibration CRC4 and
integer compensation, keeps stale values visible with validity zero, and
reports MCU/IMU/barometer acquisition progress separately. CRC4/CRC32 and source
binding are integrity checks, not physical-part authentication or qualification.

Historical 256-byte v1/v2 records remain readable. The current readback grants
only the v3 image's exact 512-byte range after image/reset-boot/supply checks;
original register-only and legacy R1 read permissions are unchanged.

```sh
python3 -B m3_firmware/r10/baro/test_baro.py
python3 -B m3_firmware/r10/test_r10.py
```

The tests run actual C under a host undefined-behavior sanitizer with scripted
sensor/register responses. They cover the published compensation/CRC examples,
partial messages/PROM, callback latency, old candidates, retained calibration,
error recovery and timer/counter wrap. They do not execute the ARM image or
model physical pressure, port capacitance, installed timing, bias, thermal,
vibration, moisture or airframe venting. No physical board has been tested.

## Primary sources

- [TE MS5611 B3 datasheet, 06/2017](https://www.mouser.com/datasheet/2/418/6/ENG_DS_MS5611_01BA03_B3-1134567.pdf),
  p3 conversion limits, pp7–13 protocol/calibration/compensation. The table was
  visually checked using the manufacturer PDF copy recorded in `provenance.json`.
- [MEAS AN520_004](https://www.amsys-sensor.eu/sheets/amsys.fr.an520_e.pdf), p12:
  CRC calculation clears the low byte of PROM word7; published CRC example.
- [I2C port source and timing contract](I2C_PORT_CONTRACT.md), primary ST
  register/errata sources and explicit unmeasured timing assumptions.
