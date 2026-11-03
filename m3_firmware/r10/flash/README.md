# R10 read-only flash diagnostics

This module contains a bounded acquisition core and a native QUADSPI transport
for U3, the fitted **W25Q128JVSIQ / C97521**. It is linked into the ABI5 bench image, with raw
observations, ages, configuration and errors decoded by the host. Its84 logical
words use spare positions in the existing1024-byte record, preserving the
sensor/voltage offsets and all historical record boundaries. It has not run on
hardware; read-only identity/status checks do not qualify the storage array.

`verify_flash.py` binds the source part, NCS pull-up, all16 relevant endpoints,
six MCU pin/alternate-function rows and pinned ST register references. A changed
part, pin, AF, supply, pull-up, bus fan-out or reference source requires review.
This checks CAD/source agreement, not the assembled device or pin continuity.

## Fixed acquisition sequence

Each batch reads SR1 (`05`), SR2 (`35`), SR3 (`15`), JEDEC ID (`9F`), the8-byte
SFDP header (`5A`), quad ID (`94`), JEDEC ID again and SR1 again. The fitted IQ
part's expected responses are `EF4018` and repeated quad ID `EF17EF17`. Quad ID
uses the Figure41 frame: one-line instruction, four-line24-bit zero address,
four-line8-bit `F0` mode, four dummy clocks and four-line data. This diagram's
ordering differs from the nearby prose; the implementation follows the diagram.
The current test checks the SFDP signature only, without parsing parameter tables.

SR1 busy, SR2 suspended or QE clear stops the batch; the driver never writes QE.
Only a complete, consistent batch replaces the last-good sample. Current partial
bytes, transfer counts, per-command timestamps, error history and cleanup errors
remain separate. Initialisation has a500ms bound, each transfer20ms, each
batch150ms and retries1000ms. The post-initialisation power guard is1nominal ms.
Freshness is strictly under3000ms from the last-good batch's start. These are
bench diagnostic policies, not manufacturer timing guarantees.

No-response can mean an unpowered, sleeping, disconnected or otherwise unavailable
device. Read-only diagnosis does not reset or wake the flash. Passing ID/SFDP/quad
ID does not prove authenticity, array integrity, writeability, endurance or safe
recovery after loss of power.

## Native transport

The adapter requires the explicit HSI64/HCLK64 clock policy and an unowned
QUADSPI peripheral, and uses a nominal1MHz serial clock. It preserves unrelated
RCC/GPIO fields. Only PB2/PB6, PD11/PD12/PD13 and PE2 are configured; PB6 uses
AF10 and the other five AF9. NCS ODR is high before changing its mode. Sensor,
ADC and all other GPIO fields remain untouched. No actuator output is configured.

The ES0392 Rev16 section2.7.4 timing sequence runs while NCS is driven high and
the clock/data pins are parked. The native primitive masks interrupts around
consecutive CCR/CCR/CR stores; an Arm disassembly test checks that sequence.
Section2.7.3's clear-CCR hazard receives an explicit EN clear/set before AF pins
are exposed. Every normal transfer has an instruction, finite DLR and indirect
read mode; no DMA, interrupt, auto-poll or memory-mapped mode is enabled. The
even /64 prescaler also addresses the applicable2.7.6 clock-duty-cycle condition.

Reads consume at most eight FIFO bytes per callback. A full FIFO result without
transfer-complete/idle is still pending. Stale flags, failed writes, configuration
drift, excessive/short data and post-read errors are rejected. Cleanup raises
NCS, parks the other pins, resets only the owned peripheral and checks reset/idle
before releasing ownership. An inability to certify cleanup stops retries.

These bounded software paths cannot bound a stalled CPU or MMIO bus. Neither
object-code order nor the scripted model proves the workaround's actual kernel
clock deadline, real waveforms, GPIO voltage or silicon behaviour.

## Offline tests

```sh
python3 -B -m unittest discover -s m3_firmware/r10/flash -p 'test_*.py'
```

Set `R10_ARM_GCC` to Arm GNU Toolchain15.2.1's compiler for the native object and
disassembly check. Without it that specific check is skipped, not passed.
The core and transport C run under AddressSanitizer/UBSan against scripted
responses. Tests cover partial/error transfers, deadlines, wrap, recovery, stale
history, ownership, pin/clock/register drift, ignored writes, FIFO faults and
cleanup. Selected core/driver regressions must compile and then fail runtime
assertions. No test enumerates a probe or touches physical hardware. See
`provenance.json` for document versions, links and reviewed limits.
