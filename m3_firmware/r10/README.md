# R10 sensor and voltage bench diagnostics

This is a separate, cross-built **bench diagnostic image** for the exact
M3-ASSY-R10 board in `binding.json`. It has not run on hardware. The R1 image,
its build script and its incompatible board binding remain unchanged.

The image records Cortex-M7 / device identity, MCU UID, raw sticky reset flags,
nominal HSI-derived ticks, a separate main-loop counter and best-effort exception
registers. The external record publishes once per nominal second. SysTick is
nominally 1 ms; main count advances per wake/loop, with sensor callback latency
not treated as a deterministic scheduling guarantee. A fault record is not a
complete crash backtrace. Early startup
failure, recursive faults and a damaged stack can prevent publication.

The [fitted IMU acquisition core](imu/README.md) and native SPI1 port are now
linked into the image. The [MS5611 barometer core and I2C1 port](baro/README.md)
are now linked too. The [voltage core and ADC1/ADC3 port](voltage/README.md)
are linked in ABI4. GPIO changes are limited to PB3/PB4/PB5 AF5, PB7 sensor CS,
PB8/PB9 AF4, and PA6/PB1 analog/no-pull inputs. Internal VREFINT and VBAT are
sampled on ADC3; ADC2 remains in deep power-down. No actuator/PWM, UART, USB or
storage driver is enabled. Flight state,
control and recovery logic remain unimplemented. This is bench diagnostics,
not the complete board firmware.

Voltage records retain the current partial raw batch and a separate last-good
sample, configuration, timestamps and nominal conversions. Initialization,
conversion and batch timeouts are bounded; failed cleanup stops retry. No rail
pass band or full physical uncertainty budget is claimed. Current failure,
error history, native port phase and its most recent CR/ISR/DR observations stay
visible even when the current data is invalid.

Sensor and voltage polling runs outside the publication critical section: IMU
every20 nominal ms, barometer and voltage state machines on each main-loop wake.
A missing or failed IMU leaves the MCU heartbeat running, with sensor state,
configuration, error history and last-good raw data retained in the record.
The SPI port uses a shared finite iteration budget independent of SysTick.
This does not bound a stalled CPU/MMIO bus. A 128-NOP post-EOT guard is an
unqualified engineering choice; real waveforms must establish timing.

## Build and verify offline

Provide Arm GNU Toolchain 15.2.1 at runtime; no dependency download, probe access
or flashing occurs. Use a fresh output directory each time:

```sh
python3 m3_firmware/r10/build.py \
  --toolchain-prefix /path/to/bin/arm-none-eabi- \
  --out m3_firmware/r10/build_local
python3 -B m3_firmware/r10/test_r10.py
```

The build checks the exact PCB, exported netlist, reviewed pin table and vendor
manifest hashes, then every pinned vendor file. A changed board is refused.
The build ID covers the firmware sources, linker, build code, binding, protocol,
vendor inputs, compiler banner and flags. ELF / HEX / BIN, symbols, disassembly,
stack-usage files and a hash manifest are emitted. Compiler/header paths in
debug artifacts are mapped to portable names. Two independent builds have
produced identical outputs on the development host; this does not establish
equivalence across different toolchain binaries claiming the same version.

The linker reserves the ordinary DTCM data/stack region and a distinct 1024-byte
AXI-SRAM mailbox at `0x24000000`. Startup configures the internal LDO and waits
for `ACTVOSRDY` in stack-free assembly **before any RAM write**, initializes
DTCM with 32-bit stores and the mailbox with aligned 64-bit stores. Its AXI range
comes from linker start/end symbols checked by the build, so record-size changes
cannot leave the new tail uninitialized. Startup then copies data,
then calls the pinned ST clock setup. No cache is enabled. The supply-ready
wait has no timeout; if supply initialization fails, no valid RAM record is
promised. The `r10_supply_wait` symbol is kept for subsequent startup diagnosis.
This startup expects a hardware reset into user flash, not an arbitrary jump
from another application's live state. Physical loads must be disconnected
for first-article bench work; leaving actuator GPIOs untouched is not a physical
fault barrier or evidence that an attached circuit is safe.

## Saved-record analysis

`protocol.json` defines 1024-byte `R10D/v4`; the saved-file decoder also supports
historical 512-byte v3 and 256-byte v1/v2 records. Image/record ABI declarations must agree. Its magic is distinct from every
legacy R1 record. Publication uses a reserved generation, an odd sequence while
writing, CRC-32 and an even sequence after the payload is complete. A terminal
exception receives a new generation even when it interrupts the last store of
an ordinary publication.

The decoder below accepts **saved files only**. It does not read MCU memory or
open a probe. A separate [bounded firmware readback path](../../diagnostics/R10_FIRMWARE.md)
now compares installed image bytes and acquires paired records. The existing
`diagnostics.r10_swd` path still permits system-register reads only.

```sh
python3 m3_firmware/r10/decode.py \
  --manifest m3_firmware/r10/build_local/manifest.json \
  --board m3_design/assembly_review/m3.kicad_pcb \
  --snapshot first.bin --second second.bin
```

Each snapshot must match its ABI: 1024 bytes for v4,512 for v3,256 for historical v1/v2. Invalid CRC, odd/zero sequence, wrong
build or board identity, legacy ABI, nonzero reserved fields and contradictory
runtime/fault states are rejected. Two matching records with advancing ticks,
main counter and generation show **observed progress in the supplied records**.
One saved record does not prove liveness. The decoder cannot establish capture
time, continuity through resets, authenticity of an unsigned manifest, or the
physical board surrounding the MCU. UID identifies the chip, not its assembly.

Ticks use the nominal HSI frequency; they do not measure oscillator accuracy,
HSE frequency or clock margin. Reset flags remain raw and sticky. MMFAR/BFAR
addresses are accompanied by their CFSR validity bits. No sensor or power-rail
pass is inferred from successful record decoding.

The IMU retains its v2 offsets in v3/v4: words 45–62 for U4 state/error, identity/status/validity/has-sample,
sample count/time, endpoint flags, ten signed raw channels, eight configuration
bytes, bus errors, nominal frequency, detailed failure and retry/history fields.
The host suppresses validity after 250 nominal ms even if the last core poll
still said READY. A wrapping sample counter of zero does not mean no sample.
Native XYZ values are uncalibrated, with no roll mapping or common sampling
instant. WHO_AM_I is not part authentication. MCU FAULT records withhold all
IMU fields because a fault may interrupt a sensor update. The host reports MCU
progress and reported IMU acquisition progress separately.

Barometer words 64–97 retain candidate/last-good values and separate calibration
banks. The host checks PROM CRC4 and independently repeats integer compensation.
Freshness starts before the D1 command and a subsequent poll checks age before
commit; callback latency cannot refresh old conversions. Core FAULT withholds
all sensor/voltage state. In v4, word63,words98–127 and193–254 stay zero;
CRC32 is word255. Historical v3 retains its original CRC at127.

Voltage words128–192 hold acquisition/error/cleanup state, counters, raw masks,
full32-bit pending and last-good values, each sample timestamp, both calibration
and clock configurations, nominal converted values and native driver evidence.
The host independently recomputes the last-good conversions. A failed batch
cannot promote retained values to current data. Freshness is evaluated at record
publication with an exclusive1000 nominal ms bound, not at file replay time.
Reported voltage acquisition progress is separate from MCU and sensor progress.
Internal VBAT/4 is a coarse3V3 observation, not a narrow rail acceptance test.

## Verification evidence and remaining work

The host suite compiles and executes the actual portable C publisher, injects
each of the 8192 possible single-bit changes into a record, tests random payloads
and counter wrap, and executes the actual `main.c` with scripted register and
exception responses under the host undefined-behavior sanitizer. Scripted
registers are not an STM32 emulator or a physical power-up test. Cross-build
checks inspect the actual vector table, stack address, mailbox symbol, double-
word store and memory barriers. No image has been flashed.

Next: qualify physical R10 rail measurements and add persistent diagnostic logs. Real reset, clock, supply, probe, sensor and
fault-injection checks remain first-article work.

## Primary references

- [ST RM0433](https://www.st.com/resource/en/reference_manual/rm0433-stm32h742-stm32h743753-and-stm32h750-value-line-advanced-armbased-32bit-mcus-stmicroelectronics.pdf),
  power startup / Run* restrictions, SRAM and Cortex-M7 register mapping.
- [ST AN5342, ECC initialization](https://www.st.com/content/st_com/en/technical-documents/an5342--how-to-use-error-correction-code-ecc-management-for-internal-memories-protection-on-stm32-mcus-stmicroelectronics_asset/chunk-003-topic-an5342-test-ecc-flash.html),
  initialize used SRAM before reading; AXI word size is 64 bits, DTCM banks 32 bits.
- [Pinned ST device source](https://github.com/STMicroelectronics/cmsis-device-h7/blob/8f922cdc7cc6de2344e75ddd657889f4ff761790/Source/Templates/system_stm32h7xx.c),
  HSI clock setup and internal LDO supply branch. Corresponding H743 header and
  CMSIS `SysTick_Config` source hashes are recorded in `vendor_manifest.json`.
