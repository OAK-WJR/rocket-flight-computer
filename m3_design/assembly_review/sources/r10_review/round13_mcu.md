# Round13 MCU, reset, loader and external ports

Independent read-only lens5 on commit `fa897c81abac3026e75ca5cc88bef0c2659a7130`.
PCB before/after SHA256: `7355ae1aeb1fdfdf6f64317945a0bf114d94c2bb65fb04adfbcd5a2b8037b09c`.
U1 is STM32H743VIT6, LQFP100, F(23,43), rotation0.

**Result:0 Critical/0 Major/1 Minor (new documentation gap).** No package-pin,
assigned-AF, connected-loader or demonstrated reset-off hardware failure was found.
R12's PC14 correction and both R11 MCU record findings are closed. Totals exclude
closed findings and correctly disclosed pending qualification.

## R13-MCU-01: Minor, new - distinguish the UART operating pull condition

`docs/REQUIREMENTS.md:60`, `docs/ORDERING.md:454`, current `pin_table.tsv:52-53,64-65`,
`parts_qualification.md:34-35` and generated `r10_binding_note.json:582` use a4V
pull-disable threshold alongside the0-5V direct-UART envelope. This comes from
an absolute-stress note. The [ST DS12110 Rev11](https://www.st.com/resource/en/datasheet/stm32h743vi.pdf)
operating condition is stricter: Table112 note3 p210 requires pulls disabled
above the relevant supply+0.3V; Table147 note6 p242 also states this for FT_u.
Table109 note4 p208's4V boundary does not replace that operating condition.
At nominal3.3V the operating boundary is3.6V, or3.57V at3.27V. A3.8V endpoint
lies inside the published0-5V envelope while exceeding that pull condition.

Native RX paths are J420.4->R4501k->U1.51/PB12 at(29,35.45) and
J410.4->R4401k->U1.64/PC7 at(22.5,35.45); no external pull or translator intervenes.
The separate binding startup instruction already requires no pulls on these RX
pins. Thus this is a bounded record inconsistency, not a demonstrated failure of
the selected3.3V radio or an executed firmware configuration.

**Fix:** state that direct GPS/radio RX pulls stay disabled throughout operation;
include the relevant-supply+0.3V operating condition alongside the separate
absolute limit in current source/ordering/requirements and generated obligations.
Refresh binding provenance after source changes. No circuit/pin change is proved necessary.

## Fresh full-lens checks

The JSON retains all100 native pad coordinates/nets,100 independently traversed
schematic pins,28 selected AFs,32 NC checks,26 loader pins, exact relevant net
members and all four binding hashes.

| Check | Result |
|---|---|
| Maker package versus schematic/table |100/100 match ST Figure5 p55 |
| Native schematic wires/labels/NC versus XML |100/100 agree |
| PCB/XML/table/binding net map |100/100 agree;68 connected/32 NC |
| NC copper |Each has1 pad,0 tracks/vias/zones |
| Four binding SHA fields |All match actual file bytes |
| Assigned AFs |28/28 agree with ST Table10 pp89-94 |
| ADCs |PC0 ADC123_INP10;PC5 ADC12_INP8;PA6 ADC12_INP3;PB1 ADC12_INP5;PC3_C ADC3_INP1 |
| EXTI |PE1/1,PA4/4,PA5/5,PD6/6,PC8/8,PE12/12;5/6/8 share EXTI9_5 |
| Power |Five VDD+VBAT on3V3;VDDA/VREF+ on3V3A;VSS/VSSA GND;each VCAP has only its own2.2uF |
| Defaults |R5 BOOT0 down;C24 NRST;four PWM pulls;R460 SD_CS up |
| Firing controls |PC1->R1221k->Q122/R123100k down;PE4->R126220R->Q124 gate withR12810k/C126220nF;R1271k on MCU side |

Assigned groups cover all four TIM5 outputs, SPI1, SPI3/software SDCS, six QSPI
signals, GPS USART6, radio UART5, camera UART7, I2C1, USB and SWD. No pin conflict
was found. The two pyro ADC banks retain their split-top/parallel-bottom topology;
an independent1.45% resistor corner gives3.342171V at19.9V (Calculation).
The ordinary PA6/PB1 diagnostic single-fault damage cases remain disclosed residuals,
without a transferred pyro-style single-fault guarantee.

## Loader, trace and reset

The current official [AN2606 Rev70 Table135 pp320-323](https://www.st.com/resource/en/application_note/cd00167594-stm32-microcontroller-system-memory-boot-mode-stmicroelectronics.pdf)
accounts for26 package pins,14 connected/12 NC. Neither PC1/PE4 nor either direct
GPS/radio UART is a loader resource. Every connected loader net was inspected:
PA2/3 servo signals,PA4/5/PE12 status,PE11 held camera-off,PA6 diagnostic divider,
PB6 flash-select without its clock,PB9 barometer data,PA11/12 intended DFU, and
PC10-12 card bus with independent PD0/R460 deselection. Loader entry remains
bench-only with its recorded preparation before IWDG starts.

Non-debug GPIO analog reset mode, external bias and the two distinct control nets
support the static default-off intent. PC1/PE4 trace aliases and PE2 TRACECLK remain
forbidden in flight. Selected [RM0433 Rev8 lock/trace sections](https://www.st.com/resource/en/reference_manual/rm0433-stm32h742-stm32h743-753-and-stm32h750-value-line-advanced-armbased-32bit-mcus-stmicroelectronics.pdf)
and the [official H743 CMSIS definitions](https://raw.githubusercontent.com/STMicroelectronics/cmsis-device-h7/master/Include/stm32h743xx.h)
agree with the recorded configuration locks/readback and trace-clock bit20.
They do not prove that a lock defeats debugger override. The no-trace-debugger
with e-match rule and dummy-load experiment remain necessary. PA15 analog setup,
LSE-off for PC14, cold screen before enable and the watchdog/tail qualification stay open.

## Direct ports, camera and ESD

Both J410/J420 pin1 supplies are directly PORT_4V8. Four native UART paths have
only the retained1k resistor and connector-side ground ESD. No software power-cycle,
individual isolation or off-state pin protection is credited. [MicoAir](https://micoair.com/en/docs/telemetry/lr900/lr900-telemetry)
specifies3.3V LVTTL; [HGLRC](https://www.hglrc.com/products/hglrc-m100_mini-gps)
specifies supply/baud without a UART-level guarantee. GPS levels, unpowered behavior,
selected-baud edges and installed cable ESD/RF remain unqualified. No self-powered
port with the board off; no USB/self-powered back-feed source while connecting an e-match.

All8 U12,5 U13 and6 U402 pins and their biases were independently checked.
Camera TX is U1.38->U12.5/8->R101->J9.4; RX is
J9.3->R100->U12.1/4->U1.37. Only camera retains translator/switch isolation.
[TI TXU0202 pp4/20-23](https://www.ti.com/lit/ds/symlink/txu0202.pdf),
[TPS709 p13](https://www.ti.com/lit/ds/symlink/tps709.pdf) and
[TPS2553 RevG p7](https://www.ti.com/lit/ds/symlink/tps2553.pdf) support the
pin functions and their scoped power behavior. Enabled reverse blocking has
finite threshold/delay. Native circuitry does not establish installed back-feed immunity.

The [exact Infineon EL page](https://www.infineon.com/part/ESD103-B1-02EL)
specifies15V working and48V typical clamp at16A. That is not a qualified MCU-pin
voltage; component or EVM ESD ratings do not establish this installed interface's survival.
The current qualification record correctly states this, closing R11-MCU-01.

## Closure and limits

R12-MCU-01 closes: current source withdraws2.9mA and gives the proper resistor-only
3.3mA nominal/3.363636mA initial-tolerance bound, about0.306mA steady, without an
invented minimum driver resistance. R162 stays1k. R11-MCU-02's affected AF citations
and PC1 reset wording are corrected; binding hashes match.

No CLI, DRC/ERC, build/full gate, generator, GUI, git mutation or CAD edit was run.
No current-round peer report was read. Local ST downloads stalled/failed and were
stopped; web screenshots were unavailable. Official text/table excerpts supplied
source evidence; no complete local-page render verification is claimed. Only selected
RM0433 sections were freshly consulted. No firmware execution, reset/trace/back-feed
waveform, ADC accuracy, thermal, RF/ESD or physical test was performed. CAD agreement
and disclosed qualification obligations do not establish physical behavior.

Evidence: [round13_mcu.json](round13_mcu.json). Mandatory packet/context sources,
all110 decisions/newest amendments and the read-only vehicle reference were reviewed.
