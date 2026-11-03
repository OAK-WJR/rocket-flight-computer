# R10 IMU driver core

The ISM6HG256X acquisition/state layer and native H743 SPI1 port are implemented,
host-tested and linked into the independent R10 diagnostic image. ABI4 (with the retained v2/v3 IMU offsets) and
the host decoder expose configuration, raw native-axis samples, data age,
validity, error history and retries. No sensor or physical board has been
connected, and no flight/control functionality is implemented.

The fitted U4 is ST ISM6HG256XTR / C51931514. `verify.py` checks the native R10
netlist and pin-table hashes, source-part fields, eight MCU/sensor endpoint nets,
and the official driver/license hashes. Sources are pinned to ST commit
`842c809183352afbb6995729bc19f951bfee3db7`; the original BSD-3-Clause licence is
retained under `../vendor/ism6hg256x`. The `0x73` identity value is shared with
LSM6DSV320X and is not proof of the physical part's authenticity.

## Behaviour

The state machine performs nonblocking power-on and full sensor-reset waits,
then configures 120 Hz low-g acceleration/gyro and 480 Hz high-g acceleration.
Ranges are ±16 g, ±4000 dps and ±64 g; high-g code `001` is one of the codes shared
with the reviewed alternate. Configuration fields are read back on initialization
and before sampling. SPI framing is a read bit followed by deterministic dummy
bytes; only 1–32 register data bytes are accepted by the callback.

`CTRL4.DRDY_MASK` is set **before enabling ODRs** and is included in readback. A
separate 100 nominal ms startup floor follows activation: AN6353 gives 70 ms
gyro startup plus three samples at 120 Hz (95 ms). Hardware DRDY masking remains
the settling authority; the software floor and HSI tick accuracy are not physical
timing qualification.

All required low-g, gyro and high-g ready bits must be present. Both data bursts
must succeed before any new raw sample is committed. A partial transaction keeps
the last-good raw values but invalidates them. BDU protects each 16-bit axis pair;
it does **not** prove that all axes/channels were sampled simultaneously.
Temperature's validity bit is separate. Endpoint flags identify exact signed
code limits, not every possible physical saturation event.

Transient missing-ready bits retain a recent sample. A sample older than 250
nominal ms is marked stale; persistent no-data causes a new port/reset attempt
after one second, while data returning earlier recovers without a reset. Bus
failures latch further exchanges off until recovery, including follow-on calls
inside multi-operation vendor helpers. Last-good values, cumulative error/retry
counts and the last failure code/detail remain available. Freshness/retry
thresholds are bench diagnostic choices, not flight timing requirements.

The IO implementation must itself have finite polling bounds independent of a
running SysTick. The portable core cannot bound a callback that never returns.
Native SPI implementation requirements and unresolved hardware timing limits are
in [SPI_PORT_CONTRACT.md](SPI_PORT_CONTRACT.md).

## Verification

```sh
python3 -B m3_firmware/r10/imu/verify.py
python3 -B m3_firmware/r10/imu/test_imu_core.py
```

The tests compile and execute actual C plus ST's pinned driver under the host
undefined-behavior sanitizer. The scripted register model checks startup stages,
settling-mask ordering, signed raw values, eight configuration mutations,
transaction failures at every initialization exchange, stale/retry recovery,
partial-burst atomicity and tick/sample-counter wrap. Wrong fitted parts, swapped
native pins and changed driver files are rejected. AppleClang's predefined
Objective-C `__weak` qualifier is replaced by the function attribute on the test
compiler command line; vendor files are unchanged. The core and upstream driver
also cross-compile and link into the Cortex-M7 sensor diagnostic image.
The SPI register/FIFO model checks bounded transfer/failure cleanup and the
GPIO write boundary; actual main-loop tests check missing/failed sensors and
exception-time data withdrawal. These checks do not execute the ARM image.

These are software/register-model checks. They do not model sensor physics,
actual SPI waveforms, noise, bias, thermal or vibration behaviour, or prove the
absence of hardware faults.

## Primary references

- [ST DS15034](https://www.st.com/resource/en/datasheet/ism6hg256x.pdf), Rev1:
  pp.25–26 main SPI mode-3 protocol, p.66 identity, register descriptions. The
  manufacturer PDF copy read from LCSC is hashed in the vendor manifest; its
  page 25 timing diagram was visually checked.
- [ST AN6353](https://www.st.com/resource/en/application_note/DM01200980.pdf),
  pp.38–39 settling, pp.41–43 DRDY and masking, p.44 BDU/output data, p.68 reset.
- [ST driver at the pinned commit](https://github.com/STMicroelectronics/ism6hg256x-pid/tree/842c809183352afbb6995729bc19f951bfee3db7),
  register encodings, configuration helpers and raw-data ordering.
