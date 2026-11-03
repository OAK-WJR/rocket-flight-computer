# Round17 independent MCU/interface review

Target `ac483f40d38db6e0424227bd32d2a5d5f9f60c3e`; PCB before/after
`632a9ad36c19426ede219b6ff6b0d638955665cac1b4704d3392a6afdbe03982`.
**0 Critical / 0 Major / 2 Minor: one new, one carried.** All1,966 frozen
paths match before and after. This is a full lens review, not firmware or flight approval.

## R17-MCU-01: Minor, carried active - VCAP operating conditions

C19 B(28.35,37.65) and C20 B(19.8,37.3) are exact Samsung
CL10A225KO8NNNC/C23630,2.2uF16VX5R10%, separately on U1.48/VCAP1 and U1.73/VCAP2
to GND. Nominal selection passes. [ST DS12110 Rev11 Table114 p211](https://www.st.com/resource/en/datasheet/stm32h743vi.pdf)
and the [exact Samsung specification](https://product.samsungsem.com/part/download.do?masterKey=CL10A225KO8NNN&type=specsheet)
leave combined operating C/ESR qualification open. Samsung PDF1/2/12/16/17 were
freshly downloaded, rendered and inspected. Initial tolerance is1.98-2.42uF;
initial tolerance times the full X5R TCC allowance is1.683-2.783uF (Calculation),
not a guaranteed joint corner or observed failure. No regulator-instability claim follows.

Close ST measurement conditions and actual regulator modes; obtain supported joint
bounds or qualify exact fitted parts after assembly/rework/aging at actual local
temperature,bias and ripple/frequency. Check both C limits,ESR,startup and load/clock
transients. Retain the existing D-R15-02 deviation; no Minor CAD change.

## R17-MCU-02: Minor, new active - BOOT0-low overstatement

The active `pin_table.tsv` line25,U1.24/PA2 F(28.5,50.55), says ROM runs only after
a firmware jump because BOOT0 is tied low. Native R5 B(13,45.17) is10k from
BOOT0/U1.94 F(15.45,46.0) to GND. [AN2606 Rev70 Table2 Pattern10 p35](https://www.st.com/resource/en/application_note/an2606-stm32-microcontroller-system-memory-boot-mode-stmicroelectronics.pdf)
also permits ROM boot with BOOT0=0 when BOOT_ADD0=0x1FF0. Its Table135 p321 shows
PA2 as USART2_TX: the10k servo pull-down does not hold a driven output low.

Qualify that statement with the required BOOT_ADD0 user-flash setting and carry
boot-address recording/readback into future R10 programming acceptance. Refresh
table/binding provenance after the text correction; change no PCB or circuit generator.
No actual option bytes were read or programmed; no R10 firmware exists. This is
a source/procedure defect, not a demonstrated boot or firing failure. PC1/PE4
remain absent from the ROM-loader pin list; boot-tone/readiness refusal still applies.

## Executed reconstruction

- One root-reserved official10.0.7 schematic netlist export exited0. Fresh/saved
  XML and native10.0.6 PCB agree on all651 reference-pin pairs and209 components.
- All100 U1 pins match `r10_net`, native schematic/PCB and saved binding.
  Independent current maker Figure5 transcription,28 assigned AFs and5 ADC
  channels agree. All32 NC pads have no other pad,track,via or zone on their net.
- Native K-contract,S-3 and K-loader helpers return zero issues. PC1->R1221k/
  Q122/R123100k and separate PE4->R126220R/Q124 with R1271k/R12810k/C126220nF
  retain default-off networks. Actual reset/loader/debug behavior is unmeasured.
- The saved record equals native regeneration. On owned copies,the binding
  helper passes its positive and rejects separately a zero board hash,wrong
  firing-pin net and reversed roll sign. This is helper coverage,not fullcheck.sh.
- Current ST pin/domain/ADC/AF,operating versus absolute FT limits,reset,VCAP,
  LSI,PC14 and NRST tables were inspected. Five VDDs/VBAT use3V3, VSS/VSSA GND,
  VDDA/VREF+3V3A; each VCAP has its own capacitor. The JSON retains all100 pin
  coordinates/functions and actual native loader/gate evidence.

GPS PC6/PC7 and radio PB13/PB12 have1k plus ground-only ESD and no isolation or
power-cycle API. Powered FT digital conditions,disabled RX pulls and zero positive
injection allowance remain distinct from analog limits. Endpoint levels,back-feed,
startup/shutdown and installed ESD remain unqualified. The camera retains
[TXU0202](https://www.ti.com/lit/ds/symlink/txu0202.pdf) U12,U13 and U402 with OE/EN
pull-downs. The permitted [Infineon source](https://www.infineon.com/part/ESD103-B1-02EL)
Rev1.3 printedp6 has typical20/36/48V TLP values; those are no MCU survival proof.
TI7/20 and Infineon PDF5/6 complete pages were rendered/inspected.

Loader PA6 reaches only its diagnostic divider; PE11 is input held low; independent
PD0/R460 deselects SD during PC11 loader drive. PA2/PA3 servo behavior,PB6 flash CS
and PB9 barometer SDA retain explicit bench containment. PC0/PC5 use the two-bank
filtered sense map; PA6/PB1 diagnostic fault damage is a separately disclosed scope.

Independent arithmetic gives28.571-32.653ms IWDG,34.853ms fault allocation and
48.653ms neutral allocation. These remain conditional on qualified silicon/LSI,
reset,startup,current tail and firmware. PC14's resistor-only initial corner is
3.363636mA; Table149 is output-voltage characterization,not a hard driver-current
proof. Nominal steady current is0.300mA; retain4kHz and LSE disabled. IMU40ms Ton
is typical. SPI/EXTI,QSPI QE/nonblocking erase,SD buffering/current/power-loss,
UART error bounds,no-trace/locks and200MHz budget remain firmware obligations.

Native U4 is bottom180 at(17,45.9),roll=-gyro_Y,leverx=-6mm;z=-2.06mm remains
Inference. The saved R10 note is correct record-only evidence.
`assembly_binding.py` remains R1; `build.py` selects legacy protocols/review hashes.
No executable R10 firmware or approval exists.

## Limits and disposition

Eight rejected/narrowed Critical/Major hypotheses are preserved in the JSON.
No present AGENTS section2 violation was demonstrated. All122 decision IDs and
23 owner scopes were considered under amendments,including D-R16-03's unchanged
PCB rule. Prior round16 MCU text was read only for carried-status reconciliation
after fresh native/current-maker evidence; prior results earn no fresh proof.

Current ST sources were primary web text. Binary downloads failed and screenshot
calls returned references without images: no current ST raster QA is claimed.
The permitted STM32 cache is Rev8 and was not used for current limits. RM0433's
current fetch was over-size; no new trace-register/override proof is claimed.
Allowed IMU Rev1 and Winbond RevG texts support only their stated scope; no
newer flash-revision visual audit. Samsung exact PDF SHA256:
`7ad029052a9bd944e0fd77e7d8e814676dfb7285a5e18b8760a538d5a978e49e`.

No canonical build/edit,DRC/ERC/fullcheck,firmware or physical test; no Git
mutation,subagent,other-worktree write or current-round peer report/probe access.
Native reads emitted nonfatal wxApp/debug notices; export emitted Fontconfig
warnings. Only assigned new reports and own ignored probes were written.
