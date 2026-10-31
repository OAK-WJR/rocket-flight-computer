# Round 18 MCU pin map and interfaces review (Claude)

Target `dcbb6c8f040b7012f78934e1caf1b401db84d356`. PCB SHA-256 before and after:
`632a9ad36c19426ede219b6ff6b0d638955665cac1b4704d3392a6afdbe03982` (unchanged).
**0 Critical / 0 Major / 4 Minor (3 new, 1 carried).** This is a CAD and record review, not
firmware or bench evidence. The full evidence is in `round18_mcu.json`.

## Findings

### R18-MCU-01 (Minor, new): PC1's pull-down does not override an internal pull-up

U1.16 PC1 drives R122 1 kΩ to the gate of Q122 (AO3400A); R123 100 kΩ pulls that gate to GND.
If PC1's internal pull-up (30–50 kΩ, DS12110 Table 157 p246) were ever enabled, the Q122 gate
would sit at 2.19–2.52 V (2.75 V at 3.6 V). That is above the AO3400A's 1.45 V maximum threshold,
so Q122 would turn on, Q120/Q121 would switch on and RAW_ACT would be live.

PE4 does hold off: R127 1 kΩ at the pin keeps the Q124 gate at ≤0.104 V, below the AON7524's
0.4 V minimum threshold. After reset all GPIOs are analog with no pull (§3.8 p32), so AGENTS §2.4
is met.

The risk is a single firmware or debug mistake. Examples are a pull-up set before the
GPIOC_LCKR lock, or the RTC_TAMP3 or PWR wakeup function on PC1. Whether those two functions
apply a pull is an Inference, because RM0433 was not re-read. Firing would still need PE4.

**Fix:** change R123 to 2 kΩ, using C4109 (0402WGF2001TCE), which is already on the BOM as
R130/R133/R178/R180. It keeps the same land at F(20.6,70.66) and needs no copper change. With it:

- If the pull-up is ever enabled, the gate stays ≤0.218 V.
- With PC1 high, the gate gets 2.2 V and PC1 sources 1.1 mA.

Also add a firmware rule: never enable a pull-up, TAMP3 or the wakeup function on PC1.

### R18-MCU-02 (Minor, new): on USB power alone, the MCU back-drives the unpowered GPS and radio

PORT_4V8 has only one source, U400 on RAW_PROTECTED. TPS2121 U11 blocks reverse current, so on
USB-only power (which D-AUD-09 keeps for bench work and log download) the MCU runs while both
ports are off. The binding note nevertheless requires PC6/PB13 TX idle-high. The records also
say the ports are "powered whenever the board is on" and that the GPS/radio "stay powered".

Each TX line therefore pushes about 2.7 mA through 1 kΩ into an unpowered module's RX pin. The
same happens during C84 hold-up after the switch opens. u-blox (MAX-M10S Integration Manual
UBX-20053088 R05 §3.6.3.1 p46) says host processors must not drive the module's PIOs while V_IO
is unsupplied, and calls for buffers if that cannot be avoided. AUD-8 had required "OE low
whenever its port is off"; that rule was lost when the GPS/radio translators were removed.

**Fix (records and firmware only):**

- Keep PC6/PB13 analog, with the UARTs disabled, unless PA4 (TPS2121 ST) shows IN1 selected,
  plus a settling delay.
- Park PC6/PB13 when PA4 falls or when the PA6 shedding trigger fires.
- Correct the "always powered" wording to exclude USB-only power and hold-up.
- Add an ORDERING §8.3 USB-only step: disconnect the module leads, or verify J410.3/J420.3 stay
  near 0 V.
- Optional future CAD: a PORT_4V8 divider into the spare PA7 or PC4.

### R18-MCU-03 (Minor, new): the PE4 record is the least explicit in the MCU map

In pin_table.tsv the pin 3 entry reads `PYRO1_GATE_N`, mode `GPIO out`, reset contract "as R7".
The binding note's u1_pins["3"] matches. The `_N` suffix reads as active-low, as BAT/USB/CAM_FAULT_N
are on this board. In fact PE4 high turns Q124 on, i.e. it fires. PC1's entry says "initialise low
before output mode"; PE4's does not.

**Fix (text only):** state "ACTIVE-HIGH fire; ODR low before output mode; LCKR lock" and the
current R127/R126/R128/C126 contract in both files, then refresh provenance. Rename the net at the
next CAD change.

### R18-MCU-04 (Minor, carried from R17-MCU-01): VCAP capacitors not qualified in operation

C19/C20 are CL10A225KO8NNNC (2.2 µF ±10% X5R), one per VCAP pin, at 2.44 mm and 2.15 mm. The
nominal value meets Table 124 p216 (2.2 µF ±20%, ESR <100 mΩ). Only stacked tolerance,
temperature and ageing corners fall to about 1.68 µF. No CAD change; keep D-R15-02.

## Verified clean

- **Netlists:** a fresh kicad-cli 10.0.7 netlist matches the native PCB on 651/651 pad nets.
  pin_table r10_net and the binding u1_pins match on 100/100 pins, and the binding hashes match.
- **Pinout:** U1 symbol names match DS12110 Rev 8 Figure 5 on 100/100 pins. The footprint is
  counter-clockwise at 0.5 mm with pin 1 at F(17.0,50.55). LCSC C5271084 is STM32H743VIT6TR in
  LQFP-100.
- **Alternate functions (Tables 10–14):**
  - USART6 PC6/PC7 AF7, UART5 PB13/PB12 AF14, UART7 PE8/PE7 AF7
  - SPI3 PC10/11/12 AF6, SPI1 PB3/4/5 AF5
  - QUADSPI PB2/PD11/PD12/PE2/PD13 AF9 and PB6 AF10
  - I2C1 PB8/PB9 AF4, OTG_FS PA11/PA12 AF10, TIM5 PA0–PA3 AF2, SWD PA13/PA14 AF0
- **ADC channels:** PC0 ADC123_INP10, PC5 ADC12_INP8, PA6 ADC12_INP3 (the ADC1/2 watchdog is
  feasible), PB1 ADC12_INP5, PC3_C ADC3_INP1.
- **NC pins:** all 32 NC pads are isolated.
- **Back-feed into an unpowered MCU:** none. PC7 (FT_h) and PB12 (FT_u) at 3.3 V with VDD = 0 are
  under the 4.0 V limit (Table 119 p212), and Table 120 note 3 (p213) gives 0 mA positive
  injection. Leakage is at the µA level, so VDD cannot rise.
  - This state recurs for tens of ms at every battery power-up, because U11's 470 nF soft-start
    makes 3V3 lag PORT_4V8 (Inference).
  - It stays within limits as long as the module's output high level is ≤3.6–4.0 V.
- **PE4 drive:** inrush ≤18.7 mA against the 20 mA limit. The gate holds ≥2.84 V while firing and
  discharges in 0.5 ms after reset.
- **Crystal:** with 10 pF/10 pF loads, CL is 8–10 pF (the crystal is 8 pF). gm_crit is
  0.49–0.71 mA/V against 1.5 mA/V. Observation: drive level could reach about 242 µW at worst-case
  ESR and swing, so add an OSC_IN amplitude check on the bench.
- **Supplies and control pins:** decoupling matches Figure 68 p211. BOOT0 has 10 kΩ (≤0.15 V) and
  NRST has 100 nF. VBUS/2 is guaranteed to read high for VBUS ≥ 3.6 V. ESD topologies are
  correct.
- **Closed:** R17-MCU-02 (BOOT_ADD0 wording is fixed).

## Limits

st.com timed out, so the allowed cached DS12110 Rev 8 was used. AN2606, RM0433, AN4938 and AN2867
were not re-read, and behaviour that depends on them is labelled Inference. The module internals
are unknown. No DRC/ERC, check.sh, build, firmware or bench work was done. Other round18 reports
were not opened.
