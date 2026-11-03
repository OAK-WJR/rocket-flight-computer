# R10 round 11: MCU, alternate functions, back-feed and ESD

Read-only independent review, 2026-10-29. Target commit `21bc3b2`, PCB SHA-256
`0c50b9fd0930f34edab7129fc21b8e71d0ee03bc079e1900b7e131cece6bfaf8`.
U1 is STM32H743VIT6/TR, LQFP100, top at (23,43), rotation 0.

**Result: 0 Critical, 0 Major, 2 Minor record findings.** No pin-assignment or
normal powered UART-level violation was found. Existing owner-approved topology
and pending firmware/bench work are not counted again as new findings.

## Findings

### R11-MCU-01 — Minor: ESD explanation still assumes removed translators

`sources/r10_design/parts_qualification.md:504–512` groups all six port clamps,
says their series resistors feed TXU0202 B-side cells, and places the MCU behind
the A side. This remains true for the camera only. Native PCB and XML show
J410.4 → R440 1k → U1.64, J410.3 → R441 1k → U1.63,
J420.4 → R450 1k → U1.51 and J420.3 → R451 1k → U1.52.
No translator or rail clamp intervenes. J410/J420 are at (39,15.5)/(39,31.5).
The opening amendment describes this correctly, but the later protection
justification still relies on parts that are absent.

The [exact Infineon EL product page](https://www.infineon.com/part/ESD103-B1-02EL)
gives ±15 V working voltage and 48 V typical TLP clamp at 16 A. These are clamp
device conditions, **not** demonstrated MCU-pin voltages. ST's powered digital
FT ceiling and zero positive-injection allowance cannot be replaced by a
calculation assuming an unspecified internal avalanche clamp. Nor does a
component HBM rating establish installed cable ESD survival. No ESD waveform,
device failure or requirement violation was demonstrated here; the owner kept
the direct 1k/ESD architecture and qualification remains open.

**Fix:** scope the translator explanation to D400/D401/U12, state the actual
direct GPS/radio paths, and preserve the existing handling/installed-test
qualification limits without claiming resistor-only pin protection. Count this
once, including the inherited R3-MCU-05 qualification gap.

### R11-MCU-02 — Minor: maker references and PC1 reset description need correction

`sources/r10_design/pin_table.tsv:52–53,64–65,79–81` explicitly cites DS12110
Rev11 but calls its UART/SPI AF tables Table11/12. The current January-2026
Rev11 uses **Table10**, PB12/PB13 on p91 and PC6/PC7/PC10–12 on p92.
The seven selected AFs themselves are correct. The same old table numbers are
used in `parts_qualification.md:20–21`.

At `pin_table.tsv:17`, PC1's source text says “floating input at reset.” Current
DS12110 §3.8 p32 instead specifies analog reset mode for non-debug GPIOs. Its
external R123 pull-down still holds Q122 off in either description; the error
does not change the reset-off circuit or require a different GPIO allocation.

**Fix:** correct those current citations and PC1's reset terminology against
[ST DS12110 Rev11](https://www.st.com/resource/en/datasheet/stm32h743vi.pdf),
then regenerate the pin-table binding provenance. Historical Rev10 citations
can remain explicitly historical. This is one source-record group, not seven
electrical defects.

## Tested coverage

The independent probe used native `pcbnew.LoadBoard`, schematic XML, symbol pin
names, `pin_table.tsv` and `r10_binding_note.json`. Unconnected native KiCad nets
were normalized to NC. [round11_mcu.json](round11_mcu.json) retains all 100
per-pin comparisons, pad coordinates, exact relevant net members and hashes.

| Check | Coverage/result |
|---|---|
| Physical U1 pin names | 100/100 match maker Fig5 p55 and the schematic symbol |
| Four pin/net maps | 100/100 PCB/XML/table/binding agree; 68 connected, 32 NC |
| NC copper | All 32 NC nets have one pad only and no track/via |
| Binding hashes | PCB, XML, pin table and circuit: all four match |
| Assigned AFs | 28/28 checked against current ST Table10 pp89–94 |
| ADC allocation | All five checked; PA6 uses ADC1/2 watchdog, PC3_C uses ADC3 |
| EXTI allocation | Six unique lines: PE1=1, PA4=4, PA5=5, PD6=6, PC8=8, PE12=12 |
| Loader exposure | 26 package pins; 14 connected and explicitly contained, 12 NC |
| Direct UART paths | Four complete resistor/ground-ESD paths, both connectors and all four FT pads |
| Camera | All 8 U12, 5 U13 and 6 U402 pins, both UART directions and control biases |

Assigned groups are TIM5 CH1–4 on PA0–3 AF2; SPI1 PB3–5 AF5;
SPI3 PC10–12 AF6 with PD0 software CS; QSPI PE2/PB2/PD11–13 AF9
plus PB6 AF10; UART7 PE7/8 AF7; USART6 PC6/7 AF7; UART5 PB12/13 AF14;
I2C1 PB8/9 AF4; PA11/12 USB AF10; PA13/14 SWD AF0. No assigned peripheral
requires conflicting physical pins. The ADC channels recorded in the binding
are consistent with maker Table9: PC0 channel10, PC5 channel8, PA6 channel3,
PB1 channel5 on the stated ADC instances, and PC3_C ADC3 channel1.

## Controls, loader and reset

PC1/U1.16 reaches only R122.1; R122 1k reaches ACT_EN/Q122.1, with R123 100k
to GND. PE4/U1.3 reaches R126 220R and R127 1k to GND; the separate gate has
R128 10k and C126 220nF to GND. Native copper preserves the two separate MCU
controls. The required passive cold screen, discharge wait and ≥100ms bus
settling are firmware/bench obligations, not evidence of implemented behavior.

Current [AN2606 Rev70 Table135 pp320–323](https://www.st.com/resource/en/application_note/an2606-stm32-microcontroller-system-memory-boot-mode-stmicroelectronics.pdf)
has the same relevant loader set as the project's Rev64 source: neither PC1
nor PE4, USART6 PC6/7, nor UART5 PB12/13 is a loader pin. Of the 14 connected
loader pads, PA2/3 touch servo signals; PA4/5 and PE12 are status inputs;
PE11 is held off by R431; PA6 drives only its diagnostic divider; PB6 can select
the flash without its clock; PB9 is open-drain on the barometer bus; PA11/12
are intended DFU; PC10–12 touch the SD interface. PC11 is a loader MISO output,
while independent PD0/R460 keeps the card deselected. No loader path reaches
a firing-control net. Loader GPIO changes still require the stated bench-only
entry sequence and low, locked controls.

PC1/PE4 are trace-data alternatives and PE2 is TRACECLK. The no-trace restriction
and dummy-load test are necessary. Official [ST H743 CMSIS definitions](https://raw.githubusercontent.com/STMicroelectronics/cmsis-device-h7/master/Include/stm32h743xx.h)
confirm TRACECKEN bit20, GPIO LCKK bit16 and the PC1/PE4 lock bits. This validates
the named registers; it does **not** prove a lock defeats debugger trace override.
PA15's debug reset exception and LSE-disabled requirement for the PC14 buzzer
are retained. Boot0 has R5 10k to GND; VCAP1/2 each have their separate 2.2µF cap.

## UART voltage, power states and camera

PC6/7 are FT_h and PB12/13 FT_u. In UART use the latter use VDD, per ST Table9
note7 p88. At the powered board's supplies the digital absolute ceiling is 6 V;
pulls must be disabled above 4 V and positive injection allowance is zero
(Tables109/110 pp207–208). The bound 0–5 V digital source condition is therefore
consistent with those limits. Those stress limits do not qualify every
powered-off or supply-transition state. Native direct paths have no external
pulls. TX idle-high and RX pulls-disabled are explicit firmware obligations.

[MicoAir's current manual](https://micoair.com/en/docs/telemetry/lr900/lr900-telemetry)
specifies 3.3 V LVTTL. [HGLRC's M100 Mini page](https://www.hglrc.com/products/hglrc-m100_mini-gps)
specifies 3.3–5 V supply and 115200 baud without a UART-level guarantee.
GPS logic level and endpoint thresholds therefore remain qualification items.
Unplugged direct RX can float/noise; the binding already requires bounded
DMA/IDLE/error handling. No new isolation, fault flag or software power-cycle
capability is inferred. The no-self-powered-device/board-off restriction also
covers the direct supply-pin back-feed path.

Camera routing is correctly directional: U1.38 → U12.5/8 → R101 → J9.4;
J9.3 → R100 → U12.1/4 → U1.37. U12.3 is main3V3, U12.7 is U13's
CAM_IO_3V3, and U12.6 has R102 10k to GND. U402 EN has R431 100k to GND;
FAULT is open drain with R432 10k to main3V3. U13's open EN is permitted by
[TPS709 §7.4 p13](https://www.ti.com/lit/ds/symlink/tps709.pdf).

[TXU0202 SCES942A pp4,8,20–23](https://www.ti.com/lit/ds/symlink/txu0202.pdf)
supports the pin directions, OE-low isolation and specified partial-power-down
behavior. Both local supply bypasses and the CAM_IO bleed remain. U12's
intermediate supply ramp is not qualified merely by its off-state specification;
OE-before-EN shutdown/settling obligations remain. [TPS2553 SLVS841G pp7,13–14](https://www.ti.com/lit/ds/symlink/tps2553.pdf)
distinguishes disabled reverse blocking from enabled reverse-threshold/trip
behavior. The retained switch is useful isolation but does not eliminate the
documented no-back-feed/e-match operating restriction.

## microSD and limits

Native J430 has 3V3/GND on4/6, SPI CS/CMD/CLK/DAT0 on2/3/5/7,
10k pulls on CS/CMD/DAT0–2, all four shell contacts grounded, and local
100nF/22µF bypass. Firmware must establish CS high before AF setup, perform the
recorded low-speed initialization, cap default speed at25MHz and keep card
busy/error handling out of the safety path. Card-specific ≤200mA write/≤30mA
idle allocation, power-loss behavior and retention remain unmeasured.

No direct KiCad CLI, full gate or build was run by this lens; root owns the
fresh baseline service. Historical build results are not represented as fresh
tests. Maker PDF text was read from ST's official current documents; direct
ST downloads timed out. TI's U12 pin page was locally rendered and visually
checked. Full RM0433 web retrieval failed on document size, so no fresh full-RM
reading is claimed. Firmware, GPIO-lock/trace override, power-transition tails,
UART edges/ESD, SD current/latency and installed flight performance are pending.
