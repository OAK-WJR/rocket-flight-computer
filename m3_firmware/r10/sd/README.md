# R10 microSD metadata diagnostic transport

This module provides a C metadata codec, one-shot query, bounded wire parser
and native H743 SPI3 transport. It is not linked into the bench image. No target,
card or probe has been accessed. Image scheduling, shared clock/ownership policy,
capture serialization and host report integration remain to be implemented.

`verify.py` checks the exact J430 Molex 472192001 / C164170 socket, five 10 kOhm pull-ups,
the two bypass capacitors,30 native endpoints and four reviewed MCU pins:

| Signal | MCU | Socket |
|---|---|---|
| SD_SCK | U1.78 /PC10 AF6 SPI3_SCK | J430.5 |
| SD_MISO | U1.79 /PC11 AF6 SPI3_MISO | J430.7 |
| SD_MOSI | U1.80 /PC12 AF6 SPI3_MOSI | J430.3 |
| SD_CS | U1.81 /PD0 GPIO, high before output mode | J430.2; R460 to 3V3 |

DAT1/DAT2 have pull-ups but no MCU connection. The reviewed wiring has no
independent card-detect input. Missing/invalid replies cannot distinguish an
absent card from supply, contact, configuration or transaction faults.

## Codec contract

`r10_sd_metadata_frame` produces nine fixed initialization/register-read frames
with CRC7. It cannot emit arbitrary opcodes, media block reads, programs,
erasures, locks, formats or CRC-off commands. It only returns bytes.

CMD0 changes card protocol state and may terminate pending programming. Sending
it is not a passive observation. An integrating application must establish exclusive
cold-start ownership before initialization, observe supply settling/idle clocks,
and define bounded failure/cleanup behaviour. The codec provides no ownership
mechanism. The query requires an explicit exclusive-cold-start declaration and
does not automatically reset/retry after failure. That declaration does not
establish actual hardware ownership. The current R10 bench image does not
enable SPI3 or send any of these frames.

`r10_sd_metadata_decode` consumes a 5-byte R3 and two normalized 20-byte register
packets: R1, 0xFE, 16 CID/CSD bytes and two CRC16 bytes, MSB first. Idle bytes before
R1 or data tokens belong to the bounded wire transport and its raw evidence;
they must not be passed as part of these normalized packets. Partial prefixes
and declared counts are retained separately. Oversized/null inputs fail before
packet reads; inputs and output must not overlap. Output is cleared on every
call, so a failed observation cannot inherit a prior `metadata_valid` flag.

Transport CRC16 and the register CRC7/end bit are checked independently. CID
revision/date fields are decoded; OEM/product remain untrusted byte arrays and
must be escaped by a future renderer. OCR readiness and overlap with the nominal
3.2-3.4V window are screens, not supply measurements or full tolerance checks.
CSDv1/v2 sizes use 64-bit arithmetic; OCR addressing must match the CSD version.
R10's SDSC screen is capped at 2 GiB; SDUC/reserved CSD versions remain unsupported
in SPI. All raw packets survive these failures. Unsupported geometry is not
silently converted into another address mode.

`metadata_valid` means only that these specific packet/field checks passed.
Reported identity and capacity are not authenticated, measured or qualified;
this is not a complete SD conformance checker. SPI does not inherit a card's
advertised Speed Class guarantee, so logging throughput and latency need actual
tests on the selected card. No array integrity, write endurance, busy-tail,
reset/power-loss, retention or full-flight logging qualification is provided.

## Portable one-shot query

`query.c` orchestrates a normalized callback interface only. Its protocol model
decodes command frames independently and tracks idle/application/CRC state. The
query checks an all-FF preflight before CMD0, CMD8's voltage/check-pattern echo
or legacy illegal-command reply, CRC-on, CMD55/ACMD41, OCR and CID/CSD. It never
uses a CMD1 fallback or a media block/write/erase command. A missing response does not
establish that a socket is empty. The model does not reproduce electrical SPI
waveforms, shared kernel clocks, chip-select timing or a real card's behaviour.

All current and partial normalized bytes, actual counts, command times and
cleanup errors remain separate from completion. A successful cleanup callback
does not immediately set `valid`: the following poll checks its elapsed time
and timebase before accepting completion. Late or backwards-time completion
stops the query without repeating already-successful cleanup. A reproduced
regression had accepted metadata after a modeled 6000ms cleanup delay; actual-C
tests now reject it, as well as the final-command 200ms boundary.

Initialization 500 ms, transaction 200 ms, total 5000 ms and ACMD41 1500 ms are nominal
bench engineering policies. The pending-ACMD41 stopped-clock guard is 25 ms,
stricter than SDA section4.4's less-than-50-ms polling condition. These scheduling
guards are checked only at poll boundaries: they cannot preempt a callback
that never returns. The native adapter adds finite register budgets, continuous software CS and
bounded cancellation. These iteration budgets do not prove real wall-clock
execution limits. It preserves shared SPI1 clock selectors and never resets SPI1;
its electrical timing and interaction with concurrent users remain unqualified.

`valid` records that this one-shot acquisition completed, not that a card is
present or healthy now. Terminal queries do no further IO. No independent
card-detect, continuous monitoring, automatic reset recovery or logger is
provided. The historical ABI1-5 capture windows and image are unchanged.

## Wire and native SPI3 boundaries

`wire.c` consumes only the fixed metadata requests. Command, response and optional
CID/CSD packet share one CS-low interval across polling calls. It accepts R1/R3/R7,
scans idle FF bytes and the FE data token, then normalizes the packets. Bounds of
16 R1-prefix bytes, 16 data-token-prefix bytes and 16 received bytes per poll are
engineering policies, not a complete SD timing-conformance test. One idle FF byte
is sent after deselection. Invalid counts, short transfers, absent tokens and
cleanup faults remain distinct; none proves card absence.

`spi3_port.c` is the actual C register driver; `native_spi3.c` supplies volatile
byte/word MMIO and checks its addresses/masks against the pinned ST H743 header.
Initialization requires HSI64 system/HCLK, CKPER=HSI and SPI123SEL=CKPER. It checks
those selectors without writing them: the integrating image must establish the
shared policy before any sensor/SD transaction. It refuses enabled or reset SPI3.
A caller's cold-start declaration is not a resource lock, and no other core,
interrupt or task may use the same port during the query. RCC/GPIO setup and
cleanup also require serialized register updates across tasks/cores: masked
read-modify-write preserves stable neighbouring fields, not concurrent changes.

PD0 is preloaded high before output mode; PC10/11/12 use AF6. SPI3 is mode0,
8-bit, nominal250kHz (64MHz/256), with byte TXDR/RXDR accesses and no DMA/IRQ.
Bootstrap clocks ten FF bytes (80 clocks) with CS high. Each transfer is1..16
bytes with a combined TXP/RXP/EOT polling budget (default65536 iterations, maximum
configurable1000000). RX is drained and late error flags checked before a512-loop
post-EOT guard and disable/re-enable, following the reviewed ES0392 restrictions.
AFCNTR preserves configured master IO levels between chunks; transfer never writes
CS. The guard is an engineering starting point: SCK/CS setup/hold, no truncation
and actual execution time need logic-analyzer measurements.

Release touches only claimed resources: CS high, up to128 suspend polls, reset
and readback of SPI3, disable/readback of its clock, then PC10/11/12 analog without
pulls. It retains PD0 high and GPIOC/D clocks for their other users. Failure keeps
ownership nonzero and prevents successful completion. This is not a power cycle
of the card and cannot safely restart a live card or guarantee recovery.

The port retains clock/configuration/pin snapshots, ten bootstrap receive bytes
and separate primary/cleanup faults. The wire layer retains64-byte TX/RX prefixes
and accepted/received totals. Accepted means FIFO accepted, not measured wire
completion. Query `io_detail` is a layered summary that truncates high native
bits; capture integration must separately serialize `wire.detail`, native error
and native detail. No capture format has yet been added for these records.

## Sources and reproducible checks

The [SDA current public index](https://www.sdcard.org/downloads/pls/) lists the
v9.10 Physical Layer Simplified Specification dated 2023-12-01. The reviewed
manufacturer-authored document was retrieved from a public mirror; its exact
URL/hash and reviewed sections are in `provenance.json`. PDF bytes are not
redistributed here. The CRC definitions/known vectors and CID/CSD/OCR layouts
come from sections 4.5 / 5.1-5.3; SPI limits and register packets from 7.1 / 7.2.
[ADI AN-1443](https://www.analog.com/en/resources/app-notes/an-1443.html) Table 3
independently confirms the microSD pin roles. The
[Molex socket drawing](https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/salesdrawingpdf/472/47219/472192001_sd.pdf)
is the project's existing land/mechanics source; no land or model was changed.

```sh
python3 -B m3_firmware/r10/sd/verify.py
python3 -B m3_firmware/r10/sd/test_metadata.py
python3 -B m3_firmware/r10/sd/test_mutations.py
python3 -B m3_firmware/r10/sd/test_query.py
python3 -B m3_firmware/r10/sd/test_wire.py
python3 -B m3_firmware/r10/sd/test_spi3.py
python3 -B m3_firmware/r10/sd/test_transport_mutations.py
R10_ARM_GCC=arm-none-eabi-gcc python3 -B m3_firmware/r10/sd/test_native_build.py
```

The repository gate runs source verification and all seven SD test scripts;
its shell self-tests separately require each SD stage and propagate its failure.
Tests compile and execute the actual portable C with independent host polynomial
division/CRC calculations, randomized v1/v2 geometry, every register-packet bit
flip, partial counts, output/input guards, unsupported modes and source mutations.
Four deliberately compiled codec regressions must fail the independent behavioural
tests: CRC16 seed, capacity width, block-read opcode and a bypassed wire CRC.
Compilation errors do not count as detections. These are software checks, not
hardware test results. The query suite adds actual-C protocol-model runs for
legacy/v2 initialization, fragmented replies, time wrap and reversal, partial
failures, CRC/voltage/identity problems, deadlines and cleanup acceptance. The
four further compiled query regressions exercise premature completion, a missing
pending-clock guard, a nonexclusive cold declaration and repeated cleanup. Each
must compile and then fail its expected runtime assertion; compilation errors
are not detections. The wire suite has12 actual-C byte-peer tests and the native suite14 actual-C
register/FIFO-model tests. Ten further transport regressions must compile and fail
their expected runtime assertions. One initial late-error injection occurred too
early to detect a removed final status check; its timing was corrected and the
mutant is now rejected. A fixture error is not reported as a production defect.
The Arm test cross-builds all five C units and checks byte MMIO/barrier instructions
in the native bridge. It explicitly skips when no cross compiler is available;
use the pinned Arm GNU15.2.1 compiler for a fully exercised local gate. The
source/part binding checks the existing wiring and pinned register reference.
Scripted registers and compiled objects do not qualify the physical circuit.

Native behavior was reviewed against [ST RM0433](https://www.st.com/resource/en/reference_manual/rm0433-stm32h742-stm32h743753-and-stm32h750-value-line-advanced-armbased-32bit-mcus-stmicroelectronics.pdf)
Rev8 and [ES0392](https://www.st.com/resource/en/errata_sheet/es0392-stm32h742x743xig-st32h750xb-and-stm32h753xi-device-errata-stmicroelectronics.pdf)
Rev16 sections2.22.2/4/5/6. The reviewed versions, hashes and pages are in
`provenance.json`; they are the reviewed source baseline, not a promise that no
later revision exists. No PDF bytes are redistributed.
