# Round16 independent MCU/interface review

Target commit `b1b8658d5bf541795b7e7636c09f2e886ea8c67a`. PCB SHA256 before/after: `632a9ad36c19426ede219b6ff6b0d638955665cac1b4704d3392a6afdbe03982`.
Full lens5 result: **0 Critical / 0 Major / 1 Minor**; **0 new,1 carried**.
This is current-board review evidence,not firmware,assembly or flight approval.

## R16-MCU-01 - Minor,carried active: VCAP operating C/ESR remains unclosed

Native C19 B(28.35,37.65) and C20 B(19.8,37.3) are exactly Samsung
CL10A225KO8NNNC/C23630,2.2uF16VX5R+/-10%,each solely on its MCU VCAP net and GND.
Initial1.98-2.42uF meets nominal selection. [ST DS12110Rev11 Table114 p211](https://www.st.com/resource/en/datasheet/stm32h743vi.pdf)
gives2.2uF typical,+/-20% tolerance and ESR<100mOhm without the measurement
conditions needed to close actual combined operation. The freshly downloaded
[exact Samsung specification](https://product.samsungsem.com/part/download.do?masterKey=CL10A225KO8NNN&type=specsheet) (issued2024-05-08;PDF2/12/16/17 inspected)
uses1kHz/1Vrms after heat treatment/recovery and requires consideration of actual
DC/AC,temperature,aging and impedance. The [maker product page](https://product.samsungsem.com/mlcc/CL10A225KO8NNN.do)
identifies typical data only. Multiplying initial tolerance and the entire X5R
TCC allowance gives1.683-2.783uF (Calculation); that is not a supported joint
operating corner or an observed failure. No regulator-instability claim follows.

**Closure:** resolve ST's conditions and actual silicon/regulator modes; obtain
combined maker bounds or qualify exact fitted capacitors after process/rework/
aging at actual local temperature,bias and relevant ripple/frequency,checking
both C limits,ESR,startup and load/clock transients. A larger nominal capacitor
alone is not qualified. D-R15-02 and current parts_qualification already disclose
this bounded gap; it remains Minor rather than a demonstrated required-function
failure.

## Fresh reconstruction and source checks

- Followed all100 native U1 schematic pin endpoints through wires/global labels
  or no-connect markers. Native PCB,storedXML,fresh10.0.7XML,r10_net and binding
  agree100/100. All32 NC pins have no other pad,track,via or zone on their net.
- Fresh/stored exports agree on all651 unique reference-pin mappings. Fresh
  official10.0.7 export exited0 under root reservation; no DRC/ERC/full gate was
  run by this lens. Native API10.0.6 focused S-3/K-contract/K-loader each pass.
- Independently transcribed current maker LQFP100 order from DS12110Rev11
  Figure5 p55 and checked28 assigned AFs plus5 ADC channels in Tables9/10.
  Package/function/type/reset evidence for every pin is in the JSON and table
  below. PC2_C/PC3_C are explicitly preserved; no GPIO-only interpretation is
  applied to V3V3_SENSE on PC3_C.
- Read the mandatory requirements/decisions/AVA/M3/validation/vehicle authority,
  all119 D IDs and22 owner scopes under their amendments. No removed ARM link,
  pull-pin,GH connector,GPS/radio switch/translator or duplicate bus bank is
  restored as a current requirement. AGENTS section2 stays authoritative.

The [current STM32 datasheet](https://www.st.com/resource/en/datasheet/stm32h743vi.pdf) was checked for GPIO analog reset (p32),
FT/TT/USB-supply structures (pp63-88),AFs (pp89-94),supplies and pin limits
(pp206-211),LSI (p233),I/O/injection/PC14/NRST (pp240-248). Its operating FT
pull-off condition,relevant supply+0.3V,is distinct from absolute stress.
PC0/PC5 analog banks,PA6/PB1 diagnostic faults and PC8's VBUS threshold retain
those separate scopes.

The [current AN2606Rev70](https://www.st.com/resource/en/application_note/an2606-stm32-microcontroller-system-memory-boot-mode-stmicroelectronics.pdf) H74x Table135 pp320-323 confirms loader roles.
PC1 and PE4 are absent. PA6 can drive only its diagnostic divider; PE11 remains
an input held low by camera EN's100k. PA2/PA3 servo loader behavior is a bench
condition; PB6 flash CS and PB9 barometer SDA containment remain. PC11 can be
loader SPI3_MISO,while independent PD0/R460 keeps SD CS high. Loader software
entry must quiesce interfaces/CS and leave both firing controls locked low.
No actual loader/debug-transition test is claimed.

Native PC1->R1221k/Q122/R123100k and separate PE4->R126220R/Q124 with
R1271k/R12810k/C126220nF preserve the reviewed off-state topology. Q120/Q121
retain their gate network/C120. Trace functions on PE2/PC1/PE4 remain forbidden;
GPIO locks/readback and actual debugger-override behavior still need firmware/
dummy-load qualification. No present AGENTS section2 violation was demonstrated.

GPS PC6/PC7 and radio PB13/PB12 reach their terminals through1k and ground-only
ESD. They have no isolation or power-cycle API. Powered digital levels and pulls
must meet FT operating limits,including startup/shutdown; no self-powered module
is allowed with the board off. The camera alone retains [TXU0202](https://www.ti.com/lit/ds/symlink/txu0202.pdf) U12,
TPS709 U13 and TPS2553 U402,with hardware OE/EN pull-downs. Its UART board RX/TX
order differs from GPS/radio as labelled. InfineonRev1.3 printedp6 tables3-5
show15V working and typical20/36/48V TLP clamp levels; these do not demonstrate
installed MCU ESD survival. All these waveform/endpoint/ESD/back-feed obligations
are accurately pending,not newly demonstrated failures.

The R10 note's board/netlist/table/circuit hashes all match. Native U4 remains
B180 at(17,45.9),roll=-gyro_Y,lever x=-6mm;z=-2.06mm remains an inference.
`m3_firmware/assembly_binding.py` returns M3-ASSY-R1 and `build.py` selects legacy
protocol/review hashes. The R10 note expressly says record-only: no executable
R10 binding,firmware or SD latency/power-loss approval exists. It cannot qualify
this PCB. Independent arithmetic reproduces28.571-32.653ms IWDG,
34.853ms intact-hardware fault allocation and48.653ms neutral-command allocation;
reset/tail/startup assumptions remain unmeasured. PC14's1k resistor-only initial
corner3.363636mA does not establish a hard3mA violation; current Table149 is an
output-drop characterization. Keep4kHz and LSE disabled.

## Complete U1 reconstruction

Every row below agrees across all six representations. I/O structures and AF
pages are current DS12110Rev11; NC means an explicit native no-connect.

| Pin | Maker port | Native net | Structure / assigned function |
|---:|---|---|---|
|1|PE2|QSPI_IO2|FT_h / AF9 QUADSPI_BK1_IO2|
|2|PE3|NC|FT_h / NC|
|3|PE4|PYRO1_GATE_N|FT_h / GPIO|
|4|PE5|NC|FT_h / NC|
|5|PE6|NC|FT_h / NC|
|6|VBAT|3V3|Supply / Supply|
|7|PC13|NC|FT / NC|
|8|PC14|BUZZ_DRV|FT / GPIO|
|9|PC15|NC|FT / NC|
|10|VSS|GND|Supply / Supply|
|11|VDD|3V3|Supply / Supply|
|12|PH0|HSE_IN|FT / HSE|
|13|PH1|HSE_OUT|FT / HSE|
|14|NRST|NRST|RST / RST|
|15|PC0|PYRO1_CONT|FT_a / ADC123_INP10|
|16|PC1|ACT_EN_MCU|FT_ha / GPIO|
|17|PC2_C|NC|TT_a / NC|
|18|PC3_C|V3V3_SENSE|TT_a / ADC3_INP1|
|19|VSSA|GND|Supply / Supply|
|20|VREF+|3V3A|Supply / Supply|
|21|VDDA|3V3A|Supply / Supply|
|22|PA0|SERVO1_MCU|FT_a / AF2 TIM5_CH1|
|23|PA1|SERVO2_MCU|FT_ha / AF2 TIM5_CH2|
|24|PA2|SERVO3_MCU|FT_a / AF2 TIM5_CH3|
|25|PA3|SERVO4_MCU|FT_ha / AF2 TIM5_CH4|
|26|VSS|GND|Supply / Supply|
|27|VDD|3V3|Supply / Supply|
|28|PA4|LOGIC_SOURCE_ST|TT_a / GPIO|
|29|PA5|BAT_FAULT_N|TT_ha / GPIO|
|30|PA6|VLOGIC_SENSE|FT_a / ADC12_INP3|
|31|PA7|NC|TT_a / NC|
|32|PC4|NC|TT_a / NC|
|33|PC5|ARM1_SENSE|TT_a / ADC12_INP8|
|34|PB0|NC|FT_a / NC|
|35|PB1|CAM_5V_SENSE|TT_a / ADC12_INP5|
|36|PB2|QSPI_CLK|FT_ha / AF9 QUADSPI_CLK|
|37|PE7|CAM_MCU_RX|TT_ha / AF7 UART7_RX|
|38|PE8|CAM_MCU_TX|TT_ha / AF7 UART7_TX|
|39|PE9|CAM_UART_OE|TT_ha / GPIO|
|40|PE10|NC|FT_ha / NC|
|41|PE11|CAM_PWR_EN|FT_ha / GPIO|
|42|PE12|CAM_FAULT_N|FT_h / GPIO|
|43|PE13|NC|FT_h / NC|
|44|PE14|NC|FT_h / NC|
|45|PE15|NC|FT_h / NC|
|46|PB10|NC|FT_f / NC|
|47|PB11|NC|FT_f / NC|
|48|VCAP|VCAP1|Supply / Supply|
|49|VSS|GND|Supply / Supply|
|50|VDD|3V3|Supply / Supply|
|51|PB12|RADIO_RX_MCU|FT_u / AF14 UART5_RX|
|52|PB13|RADIO_TX_MCU|FT_u / AF14 UART5_TX|
|53|PB14|NC|FT_u / NC|
|54|PB15|NC|FT_u / NC|
|55|PD8|NC|FT_h / NC|
|56|PD9|NC|FT_h / NC|
|57|PD10|NC|FT_h / NC|
|58|PD11|QSPI_IO0|FT_h / AF9 QUADSPI_BK1_IO0|
|59|PD12|QSPI_IO1|FT_fh / AF9 QUADSPI_BK1_IO1|
|60|PD13|QSPI_IO3|FT_fh / AF9 QUADSPI_BK1_IO3|
|61|PD14|NC|FT_h / NC|
|62|PD15|NC|FT_h / NC|
|63|PC6|GPS_TX_MCU|FT_h / AF7 USART6_TX|
|64|PC7|GPS_RX_MCU|FT_h / AF7 USART6_RX|
|65|PC8|VBUS_SENSE|FT_h / GPIO|
|66|PC9|NC|FT_fh / NC|
|67|PA8|NC|FT_fha / NC|
|68|PA9|NC|FT_u / NC|
|69|PA10|NC|FT_u / NC|
|70|PA11|USB_DM|FT_u / AF10 OTG_FS_DM|
|71|PA12|USB_DP|FT_u / AF10 OTG_FS_DP|
|72|PA13|SWDIO|FT / AF0 SWDIO|
|73|VCAP|VCAP2|Supply / Supply|
|74|VSS|GND|Supply / Supply|
|75|VDD|3V3|Supply / Supply|
|76|PA14|SWCLK|FT / AF0 SWCLK|
|77|PA15|NC|FT / NC|
|78|PC10|SD_SCK|FT_ha / AF6 SPI3_SCK|
|79|PC11|SD_MISO|FT_h / AF6 SPI3_MISO|
|80|PC12|SD_MOSI|FT_h / AF6 SPI3_MOSI|
|81|PD0|SD_CS|FT_h / GPIO|
|82|PD1|NC|FT_h / NC|
|83|PD2|NC|FT_h / NC|
|84|PD3|NC|FT_h / NC|
|85|PD4|NC|FT_h / NC|
|86|PD5|LED_RED|FT_h / GPIO|
|87|PD6|USB_FAULT_N|FT_h / GPIO|
|88|PD7|LED_YEL|FT_h / GPIO|
|89|PB3|SPI1_SCK|FT / AF5 SPI1_SCK|
|90|PB4|SPI1_MISO|FT / AF5 SPI1_MISO|
|91|PB5|SPI1_MOSI|FT / AF5 SPI1_MOSI|
|92|PB6|QSPI_NCS|FT_f / AF10 QUADSPI_BK1_NCS|
|93|PB7|IMU_CS|FT_fa / GPIO|
|94|BOOT0|BOOT0|B / B|
|95|PB8|I2C1_SCL|FT_fh / AF4 I2C1_SCL|
|96|PB9|I2C1_SDA|FT_fh / AF4 I2C1_SDA|
|97|PE0|NC|FT_h / NC|
|98|PE1|IMU_INT1|FT_h / GPIO|
|99|VSS|GND|Supply / Supply|
|100|VDD|3V3|Supply / Supply|

## Rejected/narrowed C/M candidates and limits

The JSON preserves seven candidate assessments: a package/AF remap failure,
loader firing-control drive,general5V-port incompatibility,proven VCAP failure,
hard3mA PC14 failure,R1 firmware approval confusion and diagnostic-versus-pyro
single-fault conflation. None establishes a current Critical/Major defect.
The VCAP candidate retains the carried Minor above. Existing diagnostic damage,
port/back-feed/ESD and firmware obligations remain in the deviation inventory.

Current ST PDFs were read as primary web text. Direct downloads failed
(HTTP/2 code92;one HTTP/1 timeout25s); screenshot calls provided text references
without image payload. **No current ST visual page QA is claimed.** The allowed
st_h743 cache is Rev8 and was not substituted for current limits. Samsung's
fresh38-page exact specification SHA256 is
`7ad029052a9bd944e0fd77e7d8e814676dfb7285a5e18b8760a538d5a978e49e`;
complete relevant PDF pages were rendered/inspected. TIRevA pp7/20 and
InfineonRev1.3 printedpp6/7 were independently inspected from the allowed cache.
ST IMU current web PDF exceeded the tool's size limit; allowed DS14623Rev1
text confirms10MHz SPI,40ms gyro startup and active-high/push-pull defaults.
The allowed Winbond cache is RevG; no newer flash-revision visual audit is claimed.

Only the assigned new reports and ignored own probes were written. No canonical
build/edit,git action,subagent,other-worktree write or current-round peer report/
probe access occurred. The initial own NC normalization and PC2_C/PC3_C display
corrections are probe issues,not board findings. Successful native reads emitted
a nonfatal wxApp assertion; export emitted Fontconfig/cache warnings. No physical,
firmware,regulator,SD,timing,trace/current-tail,ESD/RF,harness or flight test was run.
Earlier review/gate results are context only and earn no fresh lens credit.
