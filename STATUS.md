# M3 requirements and implementation status

> Repository note: the complete projects and review packages of the historical candidates (CORE / PWR / UART / USB / GNSS / PDIAG) are not included; only the current M3-ASSY-R1 is. They are mentioned below only as the evolution record.

Last updated 2026-09-08. Governing requirements: M1/M2 merged into one board, easy to diagnose, at most three PCB iterations; "10× redundancy" means independent protection layers, not a blanket 10× component derating. **The complete M3 is not implemented yet; no candidate so far is the finished product.**

## Current candidate: M3-ASSY-R1

[Assembly and footprint review](m3_design/assembly_review/ASSEMBLY_REVIEW.md), [v0.8.1 bench diagnostics](m3_firmware/ASSEMBLY_DIAGNOSTICS.md). One 46 × 186 mm four-layer board, 135 footprint positions / 115 nominally fitted parts / 20 test points. The two LEDs have separate lands, cathode silkscreen and 3D orientation corrected against each manufacturer's drawing; U3's 208 mil package choice was confirmed. All 2201 existing tracks/vias were kept; native DRC, unconnected items, schematic parity and ERC are all zero. Functionally it provides ordinary power, acquisition, ~1 Hz diagnostic logging, USB, GNSS and the camera interface; **it is not a finished product with every rocket function, and there is no real-board or manufacturing-release evidence**.

M3-PDIAG-R1 and firmware v0.8 remain as the previous baseline; their input FAULT/ST signals and history carry over. The new firmware binds to the exact ASSY-R1 board, and the host tools reject a mismatched board ID or build identity. Active attitude control, servo/pyro actuation and a complete recovery backup are **not** implemented in this revision and must not be counted as delivered.

The host side has a [unified triage entry point and test-point map](diagnostics/TRIAGE.md): the network and location of the 20 test pads and 10 auxiliary test points are cross-checked against native KiCad data; failed or partial USB captures still produce a report linking faults to a branch and the next test point. The independent-instrument template starts empty, so power, device and whole-board stability have **no** physical PASS from it.

## Evolution record (not in the repository)

| Candidate | What it added | Evidence at the time |
|---|---|---|
| PWR-R3 | Battery / USB logic supply, acquisition core and camera branch on a provisional 46 × 168 mm board; 121 positions, 17 test pads, U6 GNSS not fitted, 103 fitted parts, 8 schematic sheets | 91 software/CAD regression tests and 5 passive hold-up simulations bound to that revision; no board measurements |
| UART-R1 | Camera UART transmit/receive, a separate camera logic supply, a reset-default-off enable and two test points; 133 positions, 113 fitted, 9 sheets | DRC/ERC/parity zero; 10 wrong-wiring / version-identity tests passed |
| USB-R1 | Corrected the ordinary-GPIO USB cable-detect divider, added R110 and TP92; 135 positions, 114 fitted, 10 sheets | 16 USB negative / numeric tests passed; 3 passive RC simulations matched the analytic results, one deliberately showing detection fails under strong back-feed |
| GNSS-R1 | U6 changed from DNP to fitted; corrected the receiver-area ground plane, distance to flash layer changes, stencil and 3D envelope | 238 software regression tests and 10 CAD error-input checks passed |
| PDIAG-R1 | Battery, USB and camera FAULT inputs and the source-select ST signal with current/historical evidence | Firmware v0.8 |

Firmware history: v0.2 bench acquisition (ADC3 voltages, MS5611, HSE / IMU / flash identity, SWD readback of 2–30 records to JSON/JSONL); v0.3 camera UART query; v0.4 raw IMU observations; v0.5 on-board diagnostic log with single/quad-line write verification; v0.6 USB CDC (pinned TinyUSB 0.21.0, HSE/PLL3 48 MHz USB clock, PD15 software VBUS detect); v0.7 GNSS receive / 1024-byte log / USB export; v0.8 power status; v0.8.1 binding to ASSY-R1. All are compiled and software-tested only; **none has run on a real board**. Older firmware images cannot be used as compatibility evidence for a newer board.

## Requirement status

| Requirement | Current evidence / implementation | Still needed for the complete M3 |
|---|---|---|
| Merge the two boards into one | M3-ASSY-R1 is a single-board candidate for power + core + camera supply/UART + USB + GNSS; 10 schematic sheets consistent with the PCB | Other interfaces not all merged; this does not equal all functions of the old two boards |
| Fits a 54.66 mm ID, installable / maintainable | Core baseline 46 × 96 mm; candidate provisionally 46 × 186 mm; height envelope for the 14.5 mm terminals / 12.8 mm C84 capacitor | All connectors, plugs, harnesses, fasteners, sled, clearances and a physical coupon; final length not frozen |
| 2S supply, switch, reverse protection, logic hold-up | PWR-R3 added U9 battery protection, U10 USB current limit, U11 source selection and 330 µF hold-up; contacts are low-current enables | Start-up / switchover / back-feed / thermal / USB current and coordination with external protection must be measured; the 100 µs typical switchover time is not a maximum |
| Stable sensor supply | Core has the AP63203, L2 and sensor supply | Start-up, input capacitance / USB load, LC damping, tolerance / bias and measurements |
| STM32H743, USB, SWD, crystal | CORE schematic/PCB reconciled, DRC/ERC zero | Real power-up, clocks, buses, and running without a probe |
| USB connection and download | USB-R1 hardware; v0.6 implements the 48 MHz PLL3, CDC stack, descriptors, GPIO plug detection, snapshot / log download and identity checks; software fault tests pass | Real clock accuracy, enumeration / suspend / cross-platform behaviour, throughput, power / back-feed / inrush and signal integrity; development VID/PID and current compliance unresolved |
| IMU / barometer recording | Core circuit; pressure/temperature acquisition; v0.4 adds raw IMU samples with timestamps / configuration / error diagnostics | Continuous storage chain, real interrupt line, built-in self-test, real liveness / noise / accuracy; scripted software tests do not replace measurements |
| QSPI logging and export | Diagnostic append at up to 1 Hz with single/quad-line write-back verification; v0.7 records the full 1024 bytes including GNSS/USB; recovers older prefixes; software fault tests | Real quad-line operation, throughput / capacity, power-loss consistency, real USB download; model tests are not board passes |
| GNSS | U6 fitted in the candidate; 9600 baud USART6 receive, read-only identity / PVT queries, raw bytes / errors / freshness diagnostics, full log and USB export; software tests pass | Real UART / power / cold and warm start, antenna / enclosure / structure / accuracy; currently ~1 Hz bench observation, not a mission validation |
| Camera 4-position terminal, 5 V / GND / UART × 2 | UART hardware routed; v0.3 implements one device-information query with raw bytes / CRC / timeout diagnostics, off by default | Camera logic levels, power-down isolation, real protocol communication, recording and the full camera application still to be verified; the old v0.2 does not drive this UART |
| Servos and actuation interface | The old M1/M2 had these; the current candidate does not | **Must be designed and verified**; not counted as delivered |
| Recovery backup and physical interlocks | The original requirements call for a commercial altimeter backup; older reports conflict | Independence / common-cause boundaries and the complete recovery chain still to be settled; software comments are not hardware redundancy |
| Pull-pin, buzzer / indicators, spare interfaces | CORE has only two LEDs; the rest were on the old boards | Decide the configuration for the unified version, interface protection, maintainability and schematic / fitted-part consistency |
| Automated diagnosis and fault localisation | SWD register readback, voltage / pressure acquisition, camera UART and raw IMU bytes / errors; sequence numbers / bound hashes and JSONL evidence; v0.8 input FAULT/ST sampling and history | Real-board probing, instrument capture and a fixture still to be done; no real measurements |
| Trustworthy footprints / 3D | New power and camera parts, C84, J1/J9 checked against drawings; ASSY-R1 added dedicated LED lands / cathodes / models and confirmed U3's 208 mil package; native checks pass | Remaining parts, purchased part numbers, harness / plug / mechanical fit still to be verified; envelopes are not physical proof |
| Clean manual layout and routing | CORE and camera copper kept; new power paths and fine-pitch escapes hand-routed, support nets searched with constraints then straightened; native checks pass | Remaining critical nets and return paths on the full board; the old M2 is not final |
| Simulation and reliability study | The power candidate has 5 ngspice passive hold-up cases bound to the PCB hash, cross-checked analytically | No complete regulator / current-limit / thermal model or measured correlation yet; RC simulation does not prove whole-board stability |
| ≤ 3 iterations, replaceable / decoupled | Traceable engineering revisions, a diagnostic evidence framework; legacy coupon files | Quantified exit criteria before each fab, reworkable design, assembly strategy and revisions after measurement |
| Manufacturing package and cost | GNSS-R1 per-reference list, 115 nominal parts; R9 has a maker part number but no LCSC code; purchasing limits on R84/R86 kept. The review package is not a manufacturing release | Consistent BOM / CPL / Gerbers, remaining identity and footprint verification, a quote for the actual shipping destination; nothing ordered yet |

Items from the original requirements (ADXL375, microSD, LoRa, board width / copper weight, etc.) have been through several rounds of trade-offs. This table does not silently restore old configurations, nor silently drop unimplemented items; they must be closed with the final functions and verification evidence of the unified version. The frozen two-board architecture has been superseded by the single-board requirement (see `docs/HISTORY.md`).

**Priority**: on the routed power / acquisition candidate, add continuous acquisition and on-board logging, USB, real camera communication, purchasing and mounting constraints and dynamic board evidence; keep listing every unimplemented requirement explicitly. Every acceptance must distinguish software tool tests, design-rule checks, simulation and physical tests.

**R2 additions**: five 22 µF capacitors changed to the real Murata 1210 package, C82 moved 0.5 mm; 10 references (precision resistors, inductors, etc.) bound to specific part numbers, with maker and supplier evidence kept in the package. Exact bias capacitance and total cost are still open.

**R3 additions**: 28 more references given part numbers; corrected C70's minimum capacitance, C70/C81 unified as 4.7 nF C0G; D9 set to B340A-13-F. Added wrong-value / wrong-part-number / wrong-wiring negative tests and resistor TCR corner estimates. No selection has real-board dynamic, cold, assembly or stock verification yet.
