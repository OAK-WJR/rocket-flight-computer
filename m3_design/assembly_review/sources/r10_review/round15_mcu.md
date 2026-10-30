# Round15 MCU and interfaces

Full independent lens5 on commit `789f4d516251991bdf1518254d537ff7b41f65bb`.
PCB SHA256 before and after:
`7866d6b895573eb10c14d0227ee4bdde8b4fba6145529786cd554cdb80121783`.

**Result: 0 Critical / 0 Major / 1 Minor.** One new capacitor-qualification
evidence gap is below. Its possible Major interpretation is preserved for a
separate fresh verifier; no regulator failure or safety-section violation was
demonstrated. [Structured evidence](round15_mcu.json) includes all100 pins.

## R15-MCU-01: Minor, new, VCAP qualification does not close the maker window

Native C19 B(28.35,37.65) and C20 B(19.8,37.3), on separate U1.48/U1.73
VCAP nets, are Samsung CL10A225KO8NNNC,2.2uF/16V/X5R/+/-10%.
`sources/r10_design/parts_qualification.md:187` inventories their nominal value;
it does not reconcile effective capacitance with the MCU requirement.
[ST DS12110 Rev11](https://www.st.com/resource/en/datasheet/stm32h743vi.pdf)
Table114 p211 specifies2.2uF typical,+/-20% tolerance and ESR<100milliohm.
An effective-in-circuit interpretation is1.76..2.64uF per external capacitor
in internal-regulator mode. The fitted nominal2.2uF+/-10% satisfies the nominal
selection window. Table114 does not explicitly specify the capacitance test
conditions or resolve nominal versus combined-condition interpretation; that
interpretation also needs fresh verification. Figure66 p206 supports the
separate capacitors.

Fresh [Samsung exact-part data](https://product.samsungsem.com/mlcc/CL10A225KO8NNN.do)
give typical interpolated changes of-9.724665% at70C and-3.968011% at1.0V.
Multiplying these independent curve factors and the permitted-10% initial
tolerance gives **1.716525uF**,0.043475uF below1.76uF, without aging.
At1.05V the same calculation gives1.706002uF.
This is **Inference**, not a guaranteed combined corner: the zero-bias TCC
and25C DC-bias curves are separate typical data,1kHz/1Vrms test settings; their
correlation and the AC test-level dependence at VCAP are unqualified. Samsung
explicitly calls its page data typical design references. Its combined-bias
TCC example uses8V and cannot substitute for a VCAP measurement.

The project bay scope is-20..70C (`REQUIREMENTS.md:88`);70C capacitor temperature
is a sensitivity within that scope, not a measured local temperature. ST
Table112 pp209-210 gives VOS3 core0.95..1.05V,nominal1.0V; higher regulator
scales extend to1.4V. Fitted silicon revision is unidentified; these are the
conditional RevV electrical limits. The200MHz flight-clock obligation does not constitute an
implemented/measured VOS selection. Even the0.95V example gives1.726245uF
under the same unproved combination. VCAP voltage, local temperature, effective
C/ESR and regulator stability have not been measured.

**Concrete fix:** add the explicit CEXT/ESR window to C19/C20 qualification and
close it with maker-supported combined-condition bounds or actual biased,
temperature/aging/process qualification at the selected regulator modes. If it
fails, qualify a replacement against both capacitance limits and ESR. Do not
equate a larger nominal capacitor with compliance. This review changes no part.

**Major candidate narrowed:** the calculation exposes missing qualification,
but separate typical curves do not prove an installed capacitor violates a
hard limit or that the regulator fails a required function. Preserve this
candidate for root's fresh verification rather than calling it a demonstrated
hardware failure.

## Fresh complete checks

| Executed check | Result |
|---|---|
| Maker package transcription versus native board/schematic/XML/table/binding |100/100 port identities and nets agree;68 connected/32 NC |
| Native schematic wire graph and NC markers |100 pins resolved independently of XML |
| Assigned alternate functions |28/28 agree; complete TIM5,SPI1,SPI3,QSPI,UART,USB,SWD,I2C groups |
| NC copper |Each NC net has one U1 pad and zero tracks,vias,zones |
| ADC and interrupts |Five ADC assignments correct;six distinct EXTI lines;5/6/8 share a vector |
| Current loader resources |26 LQFP100 pins;14 connected/12 NC;PC1/PE4 and direct GPS/radio UARTs excluded |
| Supplies/defaults |Five VDD plus VBAT on3V3;VDDA/VREF+ on3V3A;six100nF core/VBAT caps;separate VCAPs;BOOT0 down;NRST100nF |
| Interface topology |Four direct1k GPS/radio paths,ground clamps;camera U12/U13/U402 pin maps and biases agree |
| Provenance |Board,netlist,pin-table,circuit SHA fields all match |

Current maker package source is DS12110 **Figure5 p55**,Table9; Table10
pp89-94 supplies AF checks. Current official
[AN2606 Rev70](https://www.st.com/resource/en/application_note/an2606-stm32-microcontroller-system-memory-boot-mode-stmicroelectronics.pdf)
Table135 pp320-323 supplies loader resources. SD_CS/PD0 has its independent
10k pull-up; PC11's loader drive reaches the card bus,not a firing control.
PA6 reaches only its diagnostic divider. Servo3's loader UART levels remain a
bench containment obligation,not a new pyro path.

PC1 reaches R1221k/Q122 with R123100k down. PE4 reaches R126220R,R1271k down
and Q124's R12810k/C126220nF network. Static default-off topology is present;
waveforms and actual current tails are unqualified. The
[official CMSIS header](https://raw.githubusercontent.com/STMicroelectronics/cmsis-device-h7/master/Include/stm32h743xx.h)
and [HAL GPIO lock implementation](https://raw.githubusercontent.com/STMicroelectronics/stm32h7xx-hal-driver/master/Src/stm32h7xx_hal_gpio.c)
support the recorded trace-clock field and configuration-lock/readback procedure,
without proving debugger override behavior. The
[official DMA header](https://raw.githubusercontent.com/STMicroelectronics/stm32h7xx-hal-driver/master/Inc/stm32h7xx_hal_dma.h)
has separate requests for the selected peripherals. No DMA stream,cache/memory
placement,priority or real-time firmware schedule is implemented or qualified.

## Ports, limits and closures

Direct GPS/radio pins are FT digital paths. Their RX pulls remain disabled
throughout operation; operating pull restrictions and analog-mode stress limits
are separate. There is no powered-off isolation or positive-injection allowance.
No self-powered module with board off; no back-feed source while connecting the
e-match. These current owner constraints are retained.

The [radio maker](https://micoair.com/en/docs/telemetry/lr900/lr900-telemetry)
specifies3.3V LVTTL. The [GPS maker](https://www.hglrc.com/products/hglrc-m100_mini-gps)
specifies supply/baud without a reviewed UART VOH/VOL guarantee. The
[fitted Infineon ESD part](https://www.infineon.com/part/ESD103-B1-02EL)
lists15V working/48V typical clamp at16A. A ground clamp plus1k does not prove
MCU-pin clamping or cable ESD survival. Current records correctly retain those
qualification limits.

Only camera keeps [TXU0202 isolation](https://www.ti.com/lit/ds/symlink/txu0202.pdf),
[TPS709 IO supply](https://www.ti.com/lit/ds/symlink/tps709.pdf) and
[TPS2553 switching](https://www.ti.com/lit/ds/symlink/tps2553.pdf).
The power switch has finite enabled reverse threshold/delay; UART isolation
does not prove power-pin isolation. J400 opening has no independent sensor.

Independent arithmetic reproduces the conditional pyro-bank3.342171V
single-resistor corner,9.107us nominal filtering, PA6/PB1 nominal0.763636/
0.496V, PC8's4.62V nominal VBUS-high boundary, IWDG28.571..32.653ms,
34.853ms fault allocation and48.653ms first-neutral allocation. These are
calculations. PA6/PB1 single-fault overstress, PC14 dynamics, HSE startup/drive,
SD/QSPI latency/power loss and timing remain disclosed qualification limits.

R14-MCU-01 closes:current circuit and native telemetry notes cite Rev11
Table10 p91/p92 and keep direct RX pulls disabled. R13/R12 pull/current-bound
corrections remain present. Earlier explicitly identified Rev10 sources are
historical compatible evidence,not substitutes for this current-limit review.
The record-only R10 note matches the board; executable firmware binding and
v0.8.1/diagnostics remain R1-bound. No R10 firmware result is claimed.

## Scope and method

AGENTS,packets,requirements,all116 decision IDs/22 owner mandates with current
amendments,AVA/M3/validation records,R9 severity precedents and read-only VEHICLE
context were consulted. Pending firmware or physical qualification alone was
not promoted to a demonstrated required-function failure. Prior MCU reports
were context only,read after fresh native checks; no peer round15 report/probe
was read or finding shared with a peer.

Only own new MD/JSON and ignored probes were written. No CLI,DRC/ERC,build/full
gate,generator,GUI,git action or canonical change ran. Native API probes exited0
after correcting probe assumptions about PCx_C names and named NC nets; KiCad
printed a nonfatal wx diagnostic. Direct ST downloads timed out; web screenshots
returned metadata only. Current ST limits were read from official Rev11 text,
not the cached Rev8 PDF. RM0433 exceeded the web size limit. Cached DS14623 Rev1
p17 was independently rendered/read for SPI timing; the current online IMU PDF
also exceeded the fetch limit,so its latest revision was not verified here.
No firmware,electrical,thermal,RF/ESD,assembly,physical or flight test ran.
