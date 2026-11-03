# Round14 MCU, reset, loader and external ports

Independent full lens5 on target commit `f5e4a5a94013514edb952fd328325341b63a98df`.

- `board_sha256_before`: `e0e3ad841654128792b32ab778ca19e4a71e596fa89864074ec4e91e6a5ccfc6`
- `board_sha256_after`: `e0e3ad841654128792b32ab778ca19e4a71e596fa89864074ec4e91e6a5ccfc6`
- Native target: 2,259,597bytes;209 footprints/966 segments/296 vias.

**Result:0 Critical/0 Major/1 Minor.** The active Minor is a residual citation
defect at a newly located current source note. No package-pin, assigned-AF,
connected-loader or demonstrated reset-off hardware failure was found. Totals
exclude closed findings and correctly disclosed pending qualification.

## R14-MCU-01: Minor, active, carried citation defect

`sources/r10_design/circuit.json:1376`, `/notes/telemetry/1`, cites DS12110
Rev11 Tables11/12 pp90-92 for GPS/radio UART alternate functions. The generated
`telemetry.kicad_sch:2472` repeats it at schematic(20.32,20.32)mm.
The [current ST datasheet](https://www.st.com/resource/en/datasheet/stm32h743vi.pdf)
puts these AFs in Table10:p91 for PB12/PB13,p92 for PC6/PC7. Its Tables11/12
are voltage/current ratings on pp103/104. The cited AF values themselves agree
with all four native MCU pins:U1.51/52 at(29/28.5,35.45)mm and U1.63/64
at(23/22.5,35.45)mm. This is an evidence/navigation defect, without a proven
wrong pin or firmware behavior. R11-MCU-02's corrected pin-table scope does
not correct this separate current circuit note.

**Fix:** cite Rev11 Table10 pp91-92 in the circuit source and regenerate its
schematic note. In adjacent `/notes/telemetry/2` (`circuit.json:1377`, schematic
note(20.32,25.4)), align the compatible but narrower “for5V input” wording with
authorized D-R13-03: direct RX pulls stay off throughout operation, with the
relevant-I/O-supply+0.3V operating condition separate from absolute stress.
That alignment is a clarification within this one correction, not a second
finding. Refresh generated evidence provenance through the reviewed workflow;
verify the PCB remains exactly `e0e3ad84…`. No canonical file was edited here.

## Fresh checks

The [JSON evidence](round14_mcu.json) retains all100 native/schematic pin
positions and nets,32 NC copper checks,26 package loader resources, interface
parts, exact net members, binding hashes, source locations and coverage limits.

| Check actually executed | Result |
|---|---|
| Independent maker package transcription versus table/embedded symbol |100/100 agree |
| Independent schematic wire graph, labels and NC markers versus XML/PCB/table/binding |100/100 agree;68 connected/32 NC |
| Native NC assigned copper |Each has oneU1 pad,zero tracks/vias/zones |
| Assigned alternate functions |28/28 agree with official tables |
| ADC instances and EXTI ownership |Five ADC inputs correct;six distinct EXTI lines;5/6/8 share EXTI9_5 |
| Current official AN2606 loader resources |26 package pins;14 connected/12 NC;native connected members inspected |
| Native core/defaults |FiveVDD+VBAT on3V3;VDDA/VREF+ on3V3A;two separate2.2uF VCAPs;BOOT0 down,NRST100nF,PWM downs,SD_CS up |
| External ports and camera |Four direct1k paths/ground ESD;19 U12/U13/U402 pins and camera biases agree |
| Binding provenance |Board/netlist/pin-table/circuit SHA256 all match |
| Pyro ADC resistor corner |3.342170829V calculated at19.9V with the stated1.45% corner;not a measured ADC result |

The full assigned groups include TIM5,SPI1,SPI3/software SDCS,QSPI,GPS USART6,
radio UART5,camera UART7,I2C1,USB,SWD,HSE,reset,boot and diagnostics. The
[current official AN2606](https://www.st.com/resource/en/application_note/an2606-stm32-microcontroller-system-memory-boot-mode-stmicroelectronics.pdf)
Rev70 Table135 pp320-323 excludes both direct GPS/radio UARTs and PC1/PE4.
Connected loader resources remain the recorded servo/status/diagnostic,
camera-enable,flash-select,barometer,DFU and card-bus cases. Independent PD0/R460
deselects the card;PA6 reaches only its diagnostic divider. Loader entry remains
bench-only with both firing controls low and its preparation before IWDG starts.

Native PC1 reaches R1221k/Q122 with R123100k down;PE4 reaches R126220R with
R1271k down and Q124's R12810k/C126220nF gate network. P-FET R120/R121/C120 remain.
This supports the static default-off intent,not measured reset/current-tail
behavior. GPIO configuration locks/readback and disabled synchronous trace remain
firmware obligations. The [official H743 CMSIS definitions](https://raw.githubusercontent.com/STMicroelectronics/cmsis-device-h7/master/Include/stm32h743xx.h)
and [HAL lock implementation](https://raw.githubusercontent.com/STMicroelectronics/stm32h7xx-hal-driver/master/Src/stm32h7xx_hal_gpio.c)
support the recorded register fields;they do not prove debugger-override behavior.

## Ports and retained limits

J410/J420 power contacts directly join PORT_4V8. Their four UART paths have
only the retained series resistor and connector-side ground clamp. No individual
power-cycle,FAULT,OE or powered-off isolation is credited. The
[radio maker](https://micoair.com/en/docs/telemetry/lr900/lr900-telemetry) specifies
3.3V LVTTL;the [GPS maker](https://www.hglrc.com/products/hglrc-m100_mini-gps)
gives a3.3-5V supply without an inspected UART-level guarantee. Actual levels,
edges,unpowered behavior and installed immunity remain unqualified.

Camera TX is U1.38->U12.5/8->R101->J9.4;RX is
J9.3->R100->U12.1/4->U1.37. Only camera retains U12/U13/U402 isolation/control.
[TXU0202](https://www.ti.com/lit/ds/symlink/txu0202.pdf) and
[TPS709](https://www.ti.com/lit/ds/symlink/tps709.pdf) support the pin functions;
the latter permits its EN to float enabled.
[TPS2553 RevG p7](https://www.ti.com/lit/ds/symlink/tps2553.pdf) retains finite
enabled reverse threshold/delay,95-190mV/3-7ms. That is not instantaneous
back-feed isolation. Onward reverse power through U401/U400 remains an Inference.
No self-powered GPS/radio with board off;no USB/self-powered back-feed source
while connecting the e-match. J400 opening is not independently observable.

The [exact Infineon EL page](https://www.infineon.com/part/ESD103-B1-02EL)
lists15V working and48V typical TLP clamp at16A. It does not establish a safe
receiving-pin voltage or installed cable ESD survival. Current records correctly
disclaim that qualification. The page's Datasheet link opened an ELS variant;
it was not substituted for the fitted EL part.

PA6/PB1 ordinary diagnostic single-fault pin-damage cases remain disclosed
residuals,distinct from the two pyro banks. Native100k/10k and10k/1k dividers
normally yield0.763636V at8.4V and0.496V at5.456V. A shorted top/open bottom
can still overstress those diagnostic inputs. PC8's nominal4.62V VBUS detection
boundary remains a disclosed diagnostic limit:lowPC8 never proves USB absent.
NRST's powered>=0.90 ratio criterion with a10M meter remains stricter than the
250k leakage floor. None is a newly demonstrated normal-function failure.

## Closures and scope

R13-MCU-01 closes:current direct-RX instructions keep pulls off throughout
operation and distinguish the operating condition from the absolute-stress note.
The separate PA6-fault paragraph's4V statement is valid absolute-stress context;
it does not cancel the direct-RX instruction. R12-MCU-01 also remains closed:
the unsupported2.9mA proof is withdrawn and actual PC14 dynamics remain unmeasured.
R11-MCU-01's installed-ESD evidence qualification is corrected. These closures
were checked against current sources/native topology,not inferred from prior totals.

The record-only R10 evidence binding is current. `m3_firmware/assembly_binding.py`
still selects R1,and `build.py` enforces protocol/profile/board identities.
No executable R10 firmware binding or firmware qualification exists. Launch and
ground/in-flight policy,cold screening,trace locks,20ms physical pulse/36ms fault
guard,PA6 shedding and bounded storage/UART handling remain implementation and
bench obligations. No R1 firmware result qualifies this PCB.

Mandatory source context and current amendment scope were consulted,including
all113 decision IDs/22 owner records and the read-only vehicle source. Historical
port switches,ARM terminal and circuit-only stop entries were not restored.
No current-round peer report was read or finding shared with a peer.

Only read-only shell/Python/native API probes ran;no CLI,DRC/ERC,build/full gate,
generator,GUI,git mutation or canonical edit ran. Native probes exited0 with
a nonfatal wx initialization diagnostic. Local ST PDF downloading timed out and
web screenshots supplied metadata only;complete PDF-page visual verification is
not claimed. RM0433 exceeded the web size limit,so fresh lock evidence is limited
to the official sources named above. No firmware,physical,electrical,thermal,
RF/ESD,first-article or flight test ran. CAD agreement conveys no owner acceptance
or ordering readiness.
