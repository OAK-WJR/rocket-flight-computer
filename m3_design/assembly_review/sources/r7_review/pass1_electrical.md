# R7 pass 1: electrical review (on-board GNSS and telemetry radio)

Reviewer scope: the KiCad electrical design that the F10 change touches (power tree, MCU pin map,
telemetry sheet) and the electrical design of the on-board MAX-F10S and E22-900MM22S.
Layout, procurement and cost belong to the parallel reviewers and are only mentioned where an
electrical choice depends on them.

Baseline examined: worktree `rocket-flight-computer-r7`, branch `m3-assy-r7`, commit `3b215ba`
plus the uncommitted F10/P1/M3 changes in `docs/REQUIREMENTS.md`. The netlist was regenerated from
`m3_design/assembly_review/m3.kicad_sch` with `kicad-cli sch export netlist` (2026-10-15), and
the U1 pad coordinates were read from `m3.kicad_pcb` with pcbnew (no file saved). `tools/check.sh`
on the baseline: DRC 0, unconnected 0, parity 0, ERC 0, R6 contract OK, actuator contract OK, fit OK.
Board coordinates below are KiCad coordinates, which equal board coordinates (y = 0 aft edge,
y = 100 forward edge).

## 1. Summary

- **F10 is not met** (expected). The CAD is still the external-module R6 design: J130/J131 on
  USART6/USART1 and the reset-off 4.8 V port supply U16 → U14 → U15. None of the GNSS, radio, SMA,
  bias-feed, pi-network or RF ESD circuitry exists yet.
- **3V3 has plenty of capacity.** U2 (AP63203WU-7, 2 A) carries a worst-case total of about
  0.69 A with the radio transmitting, the GNSS running and the antenna shorted. That is 2.9× margin.
  The upstream limit (U11 TPS2121, at least 1.0 A) is not reached either. The RF loads add
  0.15–0.17 A while transmitting, which raises U2's junction temperature by about 9 K.
- **Recommendation: option (a).** Put the radio and GNSS on the main 3V3 through two low-DCR
  ferrite branches with local bulk. Define every new line's reset state in hardware: radio NRST
  held low, NSS high, RXEN low. Delete U14, U15, U16, J130, J131 and their passives. Option (b),
  the switchable rail, has three costs. The GNSS cold-starts (about 28 s) after every MCU or watchdog
  reset. Firmware must keep its GPIOs off the unpowered modules, because driving them back-powers
  the modules. And a forced-PWM 500 kHz buck stays next to the RF strip.
- **Pin map.** The radio goes on SPI2: PB12 (NSS), PB13, PB14 and PB15, then PD8 BUSY, PD9 NRST,
  PD10 DIO1 on EXTI10, and PE15 RXEN. These all sit at the aft-left corner of U1. TXEN is driven by
  DIO2 on the module. The GNSS goes on USART6 (PC6/PC7), with PC8 for RESET_N and PD14
  (TIM4_CH3) for TIMEPULSE. Two alternatives are rejected for safety or recoverability:
  - SPI4, the only aft-side SPI: SPI4_NSS is also an alternate function of PE4, the pyro gate.
  - GNSS on USART1: its pins are ROM-bootloader inputs, and an always-on GNSS stream can capture
    the bootloader.
- **Bias feed.** u-blox's reference values (R8 = 10 Ω) let a shorted antenna pull about 0.3 A from
  VCC_RF, above its 200 mA absolute maximum, until firmware configures short detection. Use the
  active limiter in §6.1 instead: about 45–70 mA into a short, with no firmware involved.
- **RF ESD** at each SMA:
  - Radio: Infineon ESD103-B1-02EL (±15 V, 0.09 pF at 1 GHz). A 3.6 V TVS would conduct on the
    +22 dBm RF peaks.
  - GNSS: TI TPD1E0B04DPYR (±3.6 V, 0.15 pF), which is compatible with the 3.2 V antenna bias.
- **The MAX-M10S fits the same pads and circuit.** Its pinout and dimensions match. Fit the 47 nH
  F10S bias inductor for both modules.
- **Correct F10's isolation figure.** The current MAX-M10S manual gives −17 dBm immunity at
  915 MHz, not −12 dBm, so at least 39.3 dB of isolation is needed, not 34 dB.

## 2. Findings

| ID | Sev. | Req. | Finding | Evidence | Recommended fix |
|---|---|---|---|---|---|
| E1 | Major | F10 | The CAD still has the external-port design: J130 (SH7) and J131 (SH4), U16 TPS259570 → U14 AP63301 (4.8 V) → U15 TPS2553, D130/D131 SRV05-4, R190–R206, C170–C180, L4 and TP130. There is no GNSS, radio, SMA, bias feed, pi network or RF ESD. | Regenerated netlist: U1.63–69 = RADIO_TX/RX/M0/M1/AUX_MCU and GPS_TX/RX_MCU; U1.51 = TLM_PWR_EN; U1.31 = TLM_FAULT_N; `telemetry.kicad_sch` parts. | Implement §5 and §6. Delete the parts in §6.3. These tools hard-code the R6 port design and must be updated in the same change, or `tools/check.sh` fails: `tools/check_r6.py` (FOOTPRINTS, SIGNALS, TLM checks at lines 24–39 and 283–296), `tools/fit_check.py` (J130/J131 envelopes, lines 42–47 and 325) and `m3_design/check_actuators.py` (LCSC map, lines 137–141). Create a new firmware binding (AGENTS §3). |
| E2 | Major | F10 "radio can never fire", AGENTS §2 | SPI4 (PE11–PE14) is the only SPI whose pins all sit on U1's aft side, but SPI4_NSS is also AF5 on **PE4 = PYRO1_GATE_N (U1.3)**. One wrong GPIO initialisation, such as a default SPI4 pin set of PE2/PE4/PE5/PE6, would put the radio peripheral's NSS onto the pyro gate. With hardware NSS output enabled and the bus idle, NSS sits high. PE11–PE14 are also the ROM bootloader's SPI4 block, with PE13 driven push-pull. The frozen design marks these pins "Avoid". | DS12110 Rev 11 Table 9 (PE4 row, p.64) and Table 10 (AF5); AN2606 Rev 70 Table 135 (SPI4, p.323); `docs/ROCKET_FC_FROZEN_DESIGN.md` §3.10 | Put the radio on **SPI2: PB12/PB13/PB14/PB15**. None of SPI2's alternate pins is a pyro or servo pin. Keep PE4 locked with GPIOE_LCKR as a GPIO output, as `docs/M3_R3.md` P1 already does for TRACED1. If SPI4 is ever used, lock PE4 before SPI4 is initialised. |
| E3 | Major | F10/F9 (USB recovery) | On always-on 3V3 the GNSS streams from power-up. **USART1 (PA9/PA10, and PB14/PB15)** is a ROM-bootloader interface. The bootloader takes the first USART that receives 0x7F and checks USB last, so a UBX binary stream on PA10 or PB15 can capture it and block USB DFU. R6 only got away with GPS on USART1 because the port supply was off while the MCU was in reset. | AN2606 Rev 70 Table 135 (USART1 on PA9/PA10 and on PB14/PB15) and Figure 77 (p.324); frozen design pin table (PC6/PC7: "Never use USART1") | Put the GNSS on **USART6: PC6 TX / PC7 RX (AF7)**. Neither pin is a bootloader interface, and the legacy GNSS driver already uses USART6. |
| E4 | Major | F10 (defined, harmless state during reset), F6 | The new radio lines need hardware-defined reset states. All STM32 GPIOs are analog/high-Z after reset. EBYTE's basic circuit (100 kΩ pull-up and 100 nF on NRST, TXEN and RXEN to MCU IOs) leaves the SX1262 running its last command while the MCU is in reset, booting or in the ROM bootloader. That includes a continuous-wave or infinite-preamble transmission, which F10's isolation bench test needs. RXEN and TXEN would float. | DS12110 §3.8 ("After reset, all GPIOs (except debug pins) are in Analog mode"); SX1262 DS Table 8-3 (NRESET has an internal 50 kΩ pull-up) and §8.2; EBYTE E22-900MM22S manual §5.1 | Use the parts in §6.2: **RADIO_NRST 2.0 kΩ to GND**, which holds the SX1262 in reset whenever the MCU is not driving the pin (0.13 V against VIL_N ≤ 0.66 V); **NSS 100 kΩ to 3V3_RADIO**, which keeps MISO high-Z; **RXEN 100 kΩ to GND**; TXEN from DIO2, which is pulled down inside the SX1262 in reset. Firmware drives NSS high before releasing NRST. |
| E5 | Major | F10 "bias feed … with current limiting" | u-blox's reference bias network (Figures 23 and 32: VCC_RF → T1 → R8 10 Ω → L4) limits a shorted antenna only to about 0.27–0.32 A (3.2 V into about 10–12 Ω). That is above the MAX-F10S VCC_RF absolute maximum of 200 mA (50 mA operating), and puts about 1 W into a 0.25 W R8. The receiver shuts the feed down only when SHORTDET and PWRDOWN are configured. Both are off by default and, with V_BCKP open, are lost at every power cycle. | F10S DS Table 12 (ICC_RF ≤ 200 mA abs.), Table 13 (≤ 50 mA); IM §3.3.1.4, Table 38, Table 41 (R8 10 Ω, 0.25 W) | Use the **active limiter** in §6.1: S8550 PNP across a 10 Ω sense resistor, clamping an AO3401A switched by LNA_EN through an AO3400A. Into a short it passes about 45–70 mA (Inference) with no firmware involved. At 15 mA the antenna still sees about 3.0 V; the APARC2511X-SG3L5 needs at least 2.7 V. |
| E6 | Major | F10 (isolation figure) | F10 says the MAX-M10S "tolerates about −12 dBm" at 915 MHz, giving ≥ 34 dB. MAX-M10S Integration Manual R05 Table 43 gives **−17 dBm** at 915 MHz (low-gain mode), so ≥ **39.3 dB** is needed from a +22.3 dBm port. The MAX-F10S has no published out-of-band immunity. Both modules have a 0 dBm absolute maximum at RF_IN. | M10S IM R05 §4.3.2, Table 43 (p.79); F10S IM §4.3.2 ("immunity data are currently not available"); F10S/M10S DS Table 12 | Change F10 to ≥ 39.3 dB for the MAX-M10S variant, with ≥ 22.3 dB as the absolute floor. Keep the bench test (radio keyed, C/N0 logged) as acceptance for the F10S. The antenna's pre-LNA filter at 902–928 MHz (already in F10) is the main lever. |
| E7 | Minor | F10 (implementation note) | If PC8 is reused for GNSS RESET_N, **R203 (10 kΩ to GND, the old RADIO_M0 default) must go**. Against the module's internal 7–13 kΩ pull-up it would leave RESET_N at about 1.4–1.9 V, between VIL 0.63 V and VIH 2.24 V. TIMEPULSE must have no pull-down: SAFEBOOT_N is tied to TIMEPULSE inside the module, so a low at start-up enters safeboot. RESET_N must have no capacitor. | Netlist (R203 on RADIO_M0_MCU / U1.65); F10S DS Table 14, note 14; IM §3.2.3.1 and §3.2.3.3 | Delete R196–R205 with J130/J131. Drive RESET_N open-drain with no external pull. Never enable PD14's internal pull-down. Give TIMEPULSE a 1 kΩ series resistor. |
| E8 | Minor | F10 (RF ESD) | A low-voltage RF TVS must not go on the radio port. +22.3 dBm into 50 Ω is 4.1 V peak, and about 7.5 V at the SX1262's 10:1 VSWR limit. That exceeds TPD1E0B04's 3.6 V working voltage and 6.7 V snapback, so the part would conduct, snap back and distort. | SX1262 DS Table 3-3 (VSWR ≤ 10:1); TPD1E0B04 SLVSDG9C §5.6; ESD103-B1-02EL DS v2.0 Tables 4–6 | Radio SMA: **ESD103-B1-02EL** (±15 V, 0.09 pF at 1 GHz, C535146). GNSS SMA: **TPD1E0B04DPYR** (±3.6 V, at least the 3.2 V bias; 0.15/0.18 pF, C1975594). |
| E9 | Minor | F9 (USB bench) | On USB alone, U10 (TPS2553, R85 = 66.5 kΩ) limits at 355–445 mA, about 0.43 A available at 3V3. The worst-case 3V3 load at room temperature reaches about 0.41 A at 200 MHz and about 0.56 A at 400 MHz, with the radio transmitting, the buzzer on and the flash programming. U10 then current-limits and VLOGIC droops. | TPS2553 SLVS841F §9.5.1 eq. (1); DS12110 Table 120 | No hardware change. When LOGIC_SOURCE_ST (PD1) shows USB, firmware caps transmit power at +14 dBm (45 mA with optimal settings) or disables it, and keeps the buzzer off. |
| E10 | Minor | F6 (text) | While the radio transmits, the C84 ride-through for a break in the battery lead shrinks from about 5–15 ms to about 3–6 ms (3V3 load +0.17 A; §4.4). | Calculation, §4.4 | Update the F6 text. No hardware change. |
| E11 | Minor | Operating assumptions (temperature) | The MAX-F10S/M10S, E22 and SX1262 are rated to +85 °C ambient. The 85 °C unshaded bay leaves no margin, and heat from U1 and U2 raises the local temperature further. | F10S/M10S DS Tables 12–13; EBYTE §2.1–2.2; SX1262 DS Table 3-3 | Add both modules to the 85 °C list in MARGIN_PRESCRIPTION. The ≤ 70 °C shaded bay is required for the RF parts. Keep the modules away from U1, U2 and L1 (layout reviewer). |
| E12 | Minor | F10 (power text) | "About 0.15 A more" should read 0.15–0.17 A steady in transmit (118–119 mA radio, 21–24 mA GNSS, 10–15 mA antenna), plus up to 100 mA GNSS inrush at start-up. | §4.2 | Update the F10 text. Capacity is ample (§4.3). |
| E13 | Minor | F10 (noise) | Several noise sources on the shared 3V3 reach the RF branches and 3V3A: AP63203 PFM bursts at light load; LS120, about 100 mA at about 4 kHz straight off 3V3 with no series resistor; and the PA step from 0 to 119 mA. The beads are transparent at kHz, and the 3V3A RC corner is about 2.4 kHz. | AP63203 DS §2 (PFM); MLT-5020 listing (100 mA); SX1262 DS §9.6.1 | Firmware: PA RampTime ≥ 200 µs (Inference), and no buzzer during GNSS acquisition or flight. Bench: scope 3V3 and 3V3A at TX key, and log C/N0 with the buzzer on and TX keyed. Keep total effective 3V3 ceramic within AP63203 §12's 22–68 µF. |
| E14 | Minor | F8 (text; overlaps the requirements reviewer) | F8 still says "Radio SH7 and GPS SH4 are keyed and share a separate edge block", which is obsolete under F10. | REQUIREMENTS F8 | Delete the sentence. |
| E15 | Minor | F10 (interface contract) | The E22-900MM22S uses a **passive 32 MHz crystal**, not a TCXO, so DIO3 is unused and TCXO control must not be enabled. TX into an unselected RF switch (TXEN low) or into an open port exceeds the 10:1 VSWR limit. | EBYTE §2.2 ("Passive crystal oscillator"), §4.2; SX1262 DS Table 3-3 | Firmware contract in §5.4. Never key TX without an antenna or 50 Ω load. |

No Critical finding: nothing in the touched area of the present CAD is unsafe or unbuildable. E2
and E4 would become safety defects if the R7 implementation ignored them.

## 3. Existing power tree touched by the change

| Item | Implementation (netlist) | Datasheet limits |
|---|---|---|
| 3V3 source | **U2 AP63203WU-7** (C780769), fixed 3.3 V synchronous buck, TSOT-26, bottom side at (18.0, 15.0). EN tied to VIN. L1 4.7 µH SWPA4030S4R7MT (Isat 3.2 A, 2 A rated, 78 mΩ; JLC C57269). Output: C8/C9 22 µF 0805, C23 4.7 µF, 11 × 100 nF | 2 A continuous; HS peak limit 2.5/2.8/3.1 A, hiccup after 2 ms; VFB 3.27–3.33 V (CCM); fSW 1.1 MHz ±6 % spread; 4 ms soft start; PWM/PFM (COMP clamp at 450 mA peak); θJA 89 °C/W (single-layer test board); TA −40…+85 °C; design Tj ≤ 125 °C (DS41326 Rev 3-2, pp. 4–5, §2, §8, §12) |
| Its input | VLOGIC: C84 330 µF OS-CON, C6/C7 22 µF; from U11 TPS2121 (R86 80.6 kΩ). IN2 = RAW_PROTECTED (U9 TPS259470L, R84 750 Ω); IN1 = USB_LIMITED (U10 TPS2553, R85 66.5 kΩ) | U11 ILM 1.0/1.5/2.0 A at R = 80 kΩ (1.49 A from eq. 2), fast trip 2.4 × ILM (SLVSEA3F §7.5, §9.3.2–9.3.3); U9 3.96–4.84 A (SLVSFC9C §6.5); U10 IOS 355/397/445 mA (SLVS841F eq. 1) |
| 3V3A | R164 2.2 Ω from 3V3; C10/C11 22 µF, C22 1 µF, C21/C30–C32 100 nF; feeds VDDA/VREF+, U4 IMU, U5 barometer | RC corner about 2.4 kHz with about 30 µF effective (Inference: X5R DC-bias derating) |
| Port chain to delete | U16 TPS259570 (R195 4.42 kΩ: 0.46–0.52 A, SLVSE57C §7.5) → U14 AP63301 (4.8 V, 500 kHz forced PWM) → U15 TPS2553 (355–445 mA) → TLM_5V on J130.6 and J131.1 | No defect found in these parts. They are removed in option (a). |

No electrical defect was found in the existing 3V3, VLOGIC or telemetry circuits. The issues above
concern the new design and stale requirement text.

## 4. Power analysis

### 4.1 Present 3V3 loads (from the netlist)

| Load | Typical | Worst case | Source |
|---|---|---|---|
| U1 STM32H743 @ 200 MHz VOS3, flash with cache on, all peripherals on | 75 mA (25 °C) | 173 / 232 / **312 mA** at Tj 85 / 105 / 125 °C | DS12110 Rev 11 Table 120 (rev V, p.216) |
| U1 @ 400 MHz VOS1 (allowed only with Tj throttling, REQUIREMENTS) | 175 mA | 336 / 424 / 544 mA | Same table |
| Loads U1 sources: LED1/LED2 (220 Ω), servo-line pull-downs (4 × 10 kΩ), pyro gate drive (brief) | ≈ 1 mA (LEDs dark in flight) | 15 mA | Ohm's law; LED Vf ≈ 2 V (Inference) |
| U3 W25Q128JV | 0.01 mA standby | 25 mA program/erase (ICC5–7) | Winbond W25Q128JV Rev I, DC characteristics |
| U4 LSM6DSV320X (3V3A) | 0.8 mA | ≈ 1.5 mA (Inference) | ST LSM6DSV320X DS, IddHPC9 |
| U5 MS5611 (3V3A) | 0.01 mA average | 1.4 mA peak during conversion | TE MS5611-01BA03 DS (LCSC copy) |
| LS120 MLT-5020 buzzer, straight across 3V3 | 0 | 100 mA while sounding | JLC/LCSC C94598 (2–4 V, 100 mA) |
| Pull-ups and dividers (R62/R63, fault pull-ups, I2C, pull-pin, D120/R131 cold pull-up) | 0.5 mA | 3 mA | Ohm's law |
| U12 TXU0202 VCCA | µA | < 0.1 mA | Inference |
| (Removed) R205, D130/D131 | — | — | — |

### 4.2 New loads

| Load | Typical | Worst case | Source |
|---|---|---|---|
| MAX-F10S, VCC + V_IO | 21 + 3 = 24 mA acquisition, 16 + 3 mA tracking (at 3.0 V) | No maximum published; budget 40 mA (Inference); **inrush up to 100 mA** at start-up | F10S DS R03 §4.3, Table 15 and note |
| Active antenna (APARC2511X-SG3L5 example) | 10 mA at 3.3 V | 15 mA (brief); ≈ 45–70 mA into a short with the §6.1 limiter (Inference) | Abracon DS (supply 2.7/3.3/5.0 V) |
| E22-900MM22S | 6.8–10 mA RX; sleep 180 nA | **118–119 mA TX at +22 dBm** | SX1262 DS Table 3-6 (118 mA at 3.3 V); JLC C5333985 listing (119 mA); EBYTE §2.2 (100 mA "instantaneous") |
| **Added in TX (steady)** | ≈ 0.15 A | ≈ 0.17 A | |

### 4.3 Capacity, current limits and thermal at 6.0–8.4 V and a 70–85 °C bay

- **Totals.** Typical in flight, hot bay (MCU 173–232 mA, flash, sensors, GNSS, antenna, radio
  transmitting): about **0.35–0.42 A**. Worst case (MCU Tj 125 °C at 200 MHz, LEDs, buzzer, flash
  programming, radio transmitting, antenna shorted): 312 + 15 + 25 + 3 + 100 + 3 + 40 + 70 + 119 ≈
  **0.69 A**. The same at 400 MHz is about 0.92 A.
- **AP63203.** 2 A continuous, HS peak limit at least 2.5 A, so the margin is 2.9× (2.2× at
  400 MHz). Capacity is not the issue.
- **AP63203 input current** (P_out ÷ ηV_in, η ≈ 0.85, Inference) at the 0.69 A worst case: 0.32 A
  at 8.4 V, 0.36 A at 7.4 V, 0.45 A at a 6.0 V pack (VLOGIC about 5.9 V), and 0.58 A at the
  4.58 V brownout corner from MARGIN_PRESCRIPTION. All are below U11's minimum ILM of 1.0 A and
  far below U9's 3.96 A minimum (U9 also carries the camera, at most 0.77 A). USB is the
  exception (E9).
- **Thermal.** IC loss is about P_out(1/η − 1) minus the L1 DCR loss: 0.40 − 0.04 W ≈ 0.36 W at the
  worst case. At 89 °C/W that is ΔTj ≈ 32 K, so Tj ≈ 102 °C in a 70 °C bay and ≈ 117 °C in an 85 °C
  bay, under the 125 °C design limit (DS §8) and the 160 °C TSD. Typical (0.4 A): about +18 K. The
  RF share while transmitting is about +0.10 W, or **+9 K**. The 89 °C/W figure is for a
  single-layer, 2 oz test board; this 4-layer board should do better (Inference). The AP63203's own
  rated ambient is 85 °C, an existing condition.
- **Ripple and transients.** The AP63203 is in PFM below roughly 0.2 A, depending on input
  voltage (Inference from the 450 mA COMP clamp). Typical totals of 0.15–0.25 A with the RF parts
  idle sit near the PFM/PWM boundary, so expect mode-hopping ripple. Keep total effective 3V3
  ceramic within the 22–68 µF the datasheet recommends (§12). With the §6 parts, the estimate is
  about 50–55 µF effective (Inference).

### 4.4 VLOGIC hold-up (F6)

C84 (330 µF) plus C6/C7 holds about ½ × 360 µF × (7.4² − 3.5²) V² ≈ 7.6 mJ (6.2 mJ at −20 %).
- Without RF: the AP63203 draws 0.6–1.4 W, so a break in the battery lead is ridden through for
  about 5–13 ms. This matches F6's "5–15 ms".
- With the radio transmitting (+0.17 A at 3V3): 1.2–2.0 W, so **about 3–6 ms**. This is a
  calculation (Inference for η and capacitor derating) and only changes F6's text (E10).

### 4.5 Option (a) on main 3V3 versus option (b) on the retuned TLM chain

| Aspect | (a) Main 3V3 + bead/bulk per module (recommended) | (b) U16 → U14 retuned to 3.3 V, MCU-switched (PB12), reset-off |
|---|---|---|
| Capacity | AP63203 2 A, worst case 0.69 A (2.9×) | U16 0.46–0.52 A at RAW gives at least 2.7 W, about 0.7 A at 3.3 V; AP63301 3 A |
| Retune | — | R190 100 kΩ, R206 not fitted, R191 31.6 kΩ (0.1 %): 0.8 × (1 + 100/31.6) = 3.33 V ±1.1 % (VFB 792–808 mV, DS42002). This holds the SX1262 at or above the 3.3 V it needs for +22 dBm (SX1262 DS Figures 5-3/5-4 note) |
| During an MCU reset | GNSS keeps tracking: RESET_N released, BBR intact. Radio held in reset by the NRST pull-down, so no transmission; RF switch lines low | Both modules unpowered (R193 pulls TLM_EN low): harmless. But the **GNSS cold-starts** after every reset (27–28 s TTFF, F10S DS Tables 2–3), and F6 uses ≤ 32 ms IWDG resets as its fault response |
| Back-powering | Not possible: the modules share the MCU's rail | **Real hazard.** While the rail is off and the MCU runs (deliberate power-cycle, sequencing), every high MCU output (NSS idle, UART TX idle, NRST, RXEN) and every pull-up to 3V3 feeds the module through its I/O clamps. u-blox forbids driving IOs with VCC/V_IO absent (IM App. A.1 Table 36; DS §3.2). Pull-ups would have to go to the RF rail, and firmware must tri-state lines around every switch, as R6 already requires |
| PA step on IMU/barometer/MCU analog rails | The step lands on 3V3 and reaches 3V3A below about 2.4 kHz. Estimated droop 5–15 mV (Inference, from loop bandwidth and C_out), smaller with RampTime ≥ 200 µs. VREF+ moves ≤ 0.5 %, negligible for the sense thresholds. Bench check required | Better: the step lands on RAW_PROTECTED, where the servos already cause larger steps |
| Switchers near the RF strip | One fewer: U14 removed | Keeps a **500 kHz forced-PWM buck** (U14 at (21.5, 5.5), 5.5 mm from the aft edge) next to the RF strip; it would need moving to keep F10's ≥ 5 mm rule |
| Fault containment | A shorted module or decoupling capacitor takes down 3V3, like any 3V3 load. An antenna short is contained by the §6.1 limiter | Better: a module fault cannot brown out the MCU |
| Parts, space, codes | Removes about 30 parts and the aft-end space the RF strip needs; adds 2 beads + 4 capacitors | Keeps U14, U16, L4, C170–C178, R190–R195 in the aft area |
| Firmware complexity | Low: reset states are in hardware | High: power sequencing and GPIO tri-state rules; GNSS re-acquisition after each rail cycle |

**Recommendation: (a).** Its one weakness is the PA step on 3V3. Three things mitigate it: the
radio's own bead and bulk, a slow PA ramp, and the existing 3V3A RC filter. Bench measurement
confirms it (E13). Option (b) is only worth choosing if a measured analog-rail disturbance proves
unacceptable. In that case, also feed V_BCKP from the always-on 3V3 so the GNSS keeps BBR (hot start
in about 1 s), and pull every module-side resistor up to the RF rail.

### 4.6 Safety: the uplink can never arm or fire

- **No shared copper.** The radio nets reach only U1 pins 45, 51–57 and 61 (§5.2). None shares a
  net with PYRO1_GATE(_N), the ARM/BUS nets or BOOT0/NRST. Arming stays the physical J124 break.
- **No alternate-function path.** SPI2, USART6 and TIM4 have no alternate function on PE4 (DS12110
  Table 9, PE4 row: TRACED1, SAI1_D2, DFSDM1_DATIN3, TIM15_CH1N, **SPI4_NSS**, SAI1_FS_A, SAI4_FS_A,
  SAI4_D2, FMC_A20, DCMI_D4, LCD_B0). So no radio-peripheral configuration error can drive the gate.
- **No neighbouring pins.** None of the new pins is next to PE4 (pin 3), PC0 (15), PC5 (33) or PB0
  (34). The five sentinel pins that `check_actuators.py` requires (U1.2, U1.4, U1.5, U1.16, U1.32)
  stay without a net.
- **Hardware reset states.** In any MCU reset the radio is held in reset, so it cannot transmit, and
  its switch lines are low (E4).

## 5. MCU pin map (U1 STM32H743VIT6, LQFP100, rotated 90°, top side)

U1 sits at (21.85, 35.5). Pad rows: **aft side** (pins 26–50) at y = 27.95; **left side** (51–75)
at x = 14.30, from y = 29.50 (pin 51, aft corner) upward; right side (1–25) at x = 29.40; forward
side (76–100) at y = 43.05.

### 5.1 Free and freed pins (netlist and PCB pad nets agree)

| Pin | Port | Side, pad (x, y) | Present net | Note |
|---|---|---|---|---|
| 31 | PA7 | aft (25.35, 27.95) | TLM_FAULT_N (freed) | ROM-bootloader SPI1_MOSI. Leave unconnected |
| 51 | PB12 | left (14.30, 29.50) | TLM_PWR_EN (freed; R192/R193 go) | → RADIO_NSS |
| 63 / 64 | PC6 / PC7 | left (14.30, 35.50 / 36.00) | RADIO_TX/RX_MCU (freed) | → GNSS USART6 |
| 65 | PC8 | left (14.30, 36.50) | RADIO_M0_MCU (freed; **R203 pull-down goes**) | → GNSS_RESET_N |
| 66 | PC9 | left (14.30, 37.00) | RADIO_M1_MCU (freed) | ROM-bootloader I2C3_SDA. Leave unconnected |
| 67 | PA8 | left (14.30, 37.50) | RADIO_AUX_MCU (freed) | ROM-bootloader I2C3_SCL. Leave unconnected |
| 68 / 69 | PA9 / PA10 | left (14.30, 38.00 / 38.50) | GPS_TX/RX_MCU (freed) | ROM-bootloader USART1. Leave unconnected (E3) |
| 9, 28, 30, 39–45, 52–57, 61, 77–80, 83, 86, 88, 97 | PC15, PA4, PA6, PE9–PE15, PB13–PD10, PD14, PA15, PC10–PC12, PD2, PD5, PD7, PE0 | various | no net | PA4/PA6 (SPI1), PE11–PE14 (SPI4), PA15/PC10–PC12 (SPI3) are ROM-bootloader pins; PC15 is in the backup domain (low drive) |
| 2, 4, 5, 16, 32 | PE3, PE5, PE6, PC1, PC4 | — | no net | **Pyro sentinels: must stay without a net** (`check_actuators.py` §5) |

Existing EXTI users (firmware `src/power_status_stm32.c`): EXTI0 on PD0, EXTI1 on PD1, EXTI4 on PD4
and EXTI6 on PD6. The EXTI9_5 handler assumes only line 6 is active, so new interrupts avoid lines
5–9. IMU_INT1 on PE1 is polled.

### 5.2 Proposed assignments

Sources: DS12110 Rev 11 Table 9 (pin types, function after reset, pp. 64–88) and Table 10
(alternate functions, pp. 89–98); §3.8 (all GPIOs in analog mode after reset); AN2606 Rev 70
Table 135 (bootloader pins).

| Signal (direction) | Port / pin | Side, pad (x, y) mm | Function / AF | Reset state on U1 → resulting line state | Bootloader role (AN2606 T135) | External parts |
|---|---|---|---|---|---|---|
| RADIO_RXEN (out) | PE15 / 45 | aft (18.35, 27.95) | GPIO push-pull | analog → **low** (pull-down) | none | 100 kΩ to GND |
| RADIO_NSS (out) | PB12 / 51 | left (14.30, 29.50) | GPIO (software NSS; AF5 SPI2_NSS possible) | analog → **high** (pull-up) | none | 100 kΩ to 3V3_RADIO |
| RADIO_SCK (out) | PB13 / 52 | left (14.30, 30.00) | AF5 SPI2_SCK | analog; radio held in reset | none | 33 Ω series at U1 |
| RADIO_MISO (in) | PB14 / 53 | left (14.30, 30.50) | AF5 SPI2_MISO | analog; SX1262 MISO high-Z while NSS high | USART1_TX alternate pin (push-pull in bootloader): no contention because MISO is high-Z | 33 Ω series at U31 |
| RADIO_MOSI (out) | PB15 / 54 | left (14.30, 31.00) | AF5 SPI2_MOSI | analog | USART1_RX alternate pin (input with pull-up): nothing drives the line | 33 Ω series at U1 |
| RADIO_BUSY (in) | PD8 / 55 | left (14.30, 31.50) | GPIO input, polled | SX1262 BUSY pulled up in reset | none | — |
| RADIO_NRST (out) | PD9 / 56 | left (14.30, 32.00) | GPIO push-pull | analog → **low** (radio held in reset) | none | **2.0 kΩ to GND** |
| RADIO_DIO1 (in, IRQ) | PD10 / 57 | left (14.30, 32.50) | GPIO input, **EXTI10** rising | SX1262 DIO1 pulled down in reset | none | — |
| TXEN (module) | — | U31 pin 9 ← U31 pin 19 (DIO2) | SetDio2AsRfSwitchCtrl | DIO2 pulled down in reset → low | — | Local trace only |
| GNSS_TIMEPULSE (in) | PD14 / 61 | left (14.30, 34.50) | AF2 TIM4_CH3 input capture | analog: no load, so no safeboot | none | 1 kΩ series; **never a pull-down** |
| GNSS_RXD (U1 TX) | PC6 / 63 | left (14.30, 35.50) | AF7 USART6_TX | analog → GNSS RXD's internal pull-up holds it high | none | 220 Ω series at U1 |
| GNSS_TXD (U1 RX) | PC7 / 64 | left (14.30, 36.00) | AF7 USART6_RX | analog; module drives it | none | 220 Ω series at U30 |
| GNSS_RESET_N (out) | PC8 / 65 | left (14.30, 36.50) | GPIO **open-drain** | analog → released (internal 7–13 kΩ pull-up) | none | none: no capacitor, delete R203 |
| GNSS_EXTINT (optional) | not connected | — | — | internal pull-up | — | If time-mark is wanted later: PE10/40 aft (20.85, 27.95), GPIO output |

How the choices were made:
- **Radio on SPI2.** SPI1 serves the IMU. SPI3 sits on the forward side and is a bootloader
  interface. SPI6 needs PA5 (the buzzer). SPI4 is excluded by E2.
- **SPI2 placement.** PB12–PB15 and PD8–PD10 are the first eight pins of the left side, 1.5–4.6 mm
  from the aft row. They are as short a route to an aft RF strip as the aft-side pins.
- **PD8/PD9 reservation is void.** The frozen design reserved them for an H723 FDCAN bootloader.
  That reservation is already void because PD0/PD1 are in use, and the fallback flight computer is
  an H743 board.
- **DIO1 on EXTI10.** It has its own EXTI15_10 vector, unused today.
- **GNSS on USART6.** It is the only USART6 mapping on LQFP100, so no alternate pin set can be
  configured by mistake.
- **SDMMC1 reservation is void.** The frozen-design reservation of PC8–PC12 was already used up in
  R6.

Alternative only if layout demands it: radio on SPI4 (PE11 NSS, PE12 SCK, PE13 MISO, PE14 MOSI,
aft side, x = 20.35…18.85) with BUSY on PE10, DIO1 on PD10 and RXEN on PE15. This needs PE4
locked (GPIOE_LCKR) before any SPI4 initialisation, and accepts the bootloader SPI4 overlap (PE13
push-pull in bootloader; harmless only because NSS is pulled up).

### 5.3 What each MCU reset leaves behind

When U1 is in reset or in the ROM bootloader:
- SX1262 held in reset, so nothing is transmitted.
- RF switch lines low.
- SPI lines idle; MISO high-Z.
- GNSS running and streaming into a high-Z pin.
- RESET_N released.
- Antenna bias on (LNA_EN high, or internal pull-up during GNSS reset).
- No pin left floating that could drive a module input to a harmful state.

### 5.4 Firmware binding contract (for the new binding; no firmware is implemented here)

1. **GNSS:**
   - USART6 PC6/PC7 AF7, 9600 8N1 default.
   - PC8 open-drain. Pulse it ≥ 1 ms low only for recovery: it clears BBR, so a cold start follows.
     Use UBX-CFG-RST otherwise.
   - PD14 on TIM4_CH3 input capture, with no internal pull. Never drive it low at GNSS start.
   - Set CFG-HW-RF_LNA_MODE: bypass if the external gain is above 30 dB (IM §4.3.1).
2. **Radio, bring-up order:**
   - Set PB12 high, then configure SPI2 (mode 0, ≤ 8 MHz recommended, 16 MHz maximum per SX1262
     §8.2).
   - Configure PE15 low.
   - Release PD9 and wait for BUSY low.
   - Send SetDio2AsRfSwitchCtrl(1).
   - Never use SetDIO3AsTCXOCtrl (passive crystal).
   - Use RampTime ≥ 200 µs.
3. **Radio, operation:**
   - Keep RXEN low whenever transmitting.
   - Never transmit without an antenna or 50 Ω load.
   - On USB power, transmit at ≤ +14 dBm.
4. **Never** configure SPI4, TIM15, SAI1/4, FMC or TRACE on PE2–PE6. Lock PE4. The radio
   command parser has no path to arm or fire logic (F10).

## 6. Application circuits

New designators use the 3xx block so they do not collide with R6.

### 6.1 GNSS: U30 MAX-F10S (alternate MAX-M10S)

Nets (one line per net):

| Net | Connections |
|---|---|
| 3V3 | FB30.1 |
| 3V3_GNSS | FB30.2, U30.8 VCC, U30.7 V_IO, C300.1, C301.1 |
| GND | U30.1, U30.10, U30.12, C300.2, C301.2, C302.2, Q31.S, R303.2, D30.2, C303.2 (not fitted), C305.2 (not fitted), J30 ground legs |
| GNSS_VCC_RF | U30.14 VCC_RF, R300.1, Q32.E |
| GNSS_ANT_SRC | R300.2, Q30.S, Q32.B, R301.1 |
| GNSS_ANT_GATE | Q30.G, R301.2, Q32.C, R302.1 |
| GNSS_ANT_PD | R302.2, Q31.D |
| GNSS_LNA_EN | U30.13 LNA_EN, Q31.G, R303.1 |
| GNSS_ANT_DC | Q30.D, C302.1, L30.1 |
| GNSS_RF_ANT | J30 centre, D30.1, L30.2, C303.1 (not fitted), R304.1 |
| GNSS_RF_IN | R304.2, C305.1 (not fitted), U30.11 RF_IN |
| GNSS_TXD | U30.2 TXD, R305.1; R305.2 → GNSS_TXD_MCU → U1.64 (PC7) |
| GNSS_RXD | U30.3 RXD, R306.2; R306.1 ← GNSS_RXD_MCU ← U1.63 (PC6) |
| GNSS_TIMEPULSE | U30.4, R307.1; R307.2 → GNSS_TP_MCU → U1.61 (PD14) |
| GNSS_RESET_N | U30.9, U1.65 (PC8) |
| GNSS_SAFEBOOT_N | U30.18, bare test pad (service/safeboot access, IM §3.2.3.2) |
| Not connected | U30.5 EXTINT, U30.6 V_BCKP (IM §4.1.3: leave open without a backup supply), U30.15 VIO_SEL (open = 3.3 V I/O; **never ground it**), U30.16 SDA, U30.17 SCL |

Bill of materials:

| Ref | Value / part | Package | LCSC (JLC stock 2026-10-15) | Why |
|---|---|---|---|---|
| U30 | u-blox MAX-F10S-00B (alt. MAX-M10S-00B) | LCC-18, 10.1 × 9.7 mm | C30005563 (18, ext.) / C4153167 (1136, ext.) | F10 |
| FB30 | Murata BLM18KG221SN1D, 220 Ω @ 100 MHz, 2.2 A, ≤ 0.05 Ω | 0603 | C88980 (62 476, ext.) | VCC series resistance must be ≤ 0.2 Ω (IM §4.1.1). The basic GZ1608D601TF (0.45 Ω) is **not** acceptable here |
| C300 | 10 µF 10 V X5R | 0603 | C19702 (basic) | Local bulk (Inference: u-blox shows no value) |
| C301 | 100 nF 16 V X7R | 0402 | C1525 (basic) | HF bypass at pins 7/8 |
| R300 | 10 Ω 1 %, 100 mW | 0603 | C22859 (basic) | Current sense; u-blox R8 value (IM Table 41) |
| Q32 | S8550 PNP (JCET) | SOT-23 | C105432 (basic) | Current limit: conducts when I·R300 ≥ V_EB, about 45–70 mA (Inference) |
| Q30 | AO3401A P-MOSFET | SOT-23 | C15127 (basic) | Antenna switch (u-blox T1); short-circuit dissipation ≤ 0.2 W |
| R301 | 100 kΩ | 0402 | C25741 (basic) | Gate to source: off by default (u-blox R7) |
| R302 | 10 kΩ | 0402 | C25744 (basic) | Gate drive; lets Q32 override |
| Q31 | AO3400A N-MOSFET | SOT-23 | C20917 (basic) | Driven by LNA_EN, high = on (u-blox T2) |
| R303 | 100 kΩ | 0402 | C25741 (basic) | Defines the gate if LNA_EN is high-Z |
| C302 | 10 nF 50 V X7R | 0402 | C15195 (basic) | u-blox C14 (10 nF X7R, Table 40) |
| L30 | Murata LQG15HS47NJ02D, 47 nH ±5 %, SRF ≥ 1.0 GHz, 300 mA, ≤ 0.72 Ω | 0402 | C97998 (24 540, ext.) | u-blox L4 for L1 and L5 (IM Table 42: impedance > 500 Ω at L1 and L5) |
| D30 | TI TPD1E0B04DPYR, ±3.6 V working, 0.15/0.18 pF | X1SON-2 0.6 × 1.0 | C1975594 (872, ext.) | RF ESD at the SMA; stands off the 3.2 V bias |
| R304 | 0 Ω | 0402 | C17168 (basic) | Pi-network series element (fitted) |
| C303, C305 | not fitted | 0402 | — | Pi-network shunts |
| R305, R306 | 220 Ω | 0402 | C25091 (basic) | UART edge and IO isolation (u-blox App. A.1 "external IO isolation") |
| R307 | 1 kΩ | 0402 | C11702 (basic) | TIMEPULSE contention limit |
| J30 | 50 Ω edge-launch SMA | — | procurement reviewer (C3173345 had 2 in stock) | F10 |

Bias-feed numbers:
- **Antenna voltage.** VCC_RF = VCC − 0.1 V (DS Table 13), about 3.17–3.23 V. At 15 mA the antenna
  sees about 3.2 − 0.15 (R300) − 0.01 (L30) ≈ **3.0 V**. The antenna must accept 2.9 V or less;
  the APARC2511X-SG3L5 minimum is 2.7 V.
- **Short circuit.** ≈ V_EB(on)/10 Ω ≈ 45–70 mA over −20…+85 °C (Inference). That is below the
  200 mA absolute maximum and about at the 50 mA operating limit in a fault. Q30 dissipates
  ≤ (3.2 − 0.6) × 0.07 ≈ 0.18 W.
- **Tighter limit.** If the short-circuit current must stay ≤ 50 mA even when cold, use R300 =
  15 Ω (0603, C22810, extended). That adds 0.07 V of drop.
- **Bench check.** Short the SMA with the GNSS running. Verify the current, check there is no
  oscillation in the Q32 loop (Inference), and confirm VCC_RF stays within spec.

RF chain order is **SMA → D30 → L30 bias tee → pi network (C303 shunt, R304 series, C305 shunt) →
RF_IN**. The bias sits on the antenna side so that R304 can later become a series capacitor without
cutting the antenna feed. RF_IN has an internal DC block (DS note 18) and tolerates ±5.5 V DC
(Table 12). Three rules for future filters:
- C303 sits on the DC bias node, so it must be capacitive.
- C305 must also be capacitive unless R304 is replaced by a series capacitor.
- A shunt inductor in either position shorts the antenna feed. The limiter makes that harmless,
  but the antenna goes dark.

0402 is a standard size for 1.2–1.6 GHz matching parts. An LC filter in this footprint can give
useful 915 MHz rejection for the L1-only MAX-M10S. For the F10S, 1176 MHz is only 22 % above
915 MHz, so a 3-element filter would buy little rejection for some L5 loss (Inference).

**MAX-M10S drop-in.** It uses the same pads and circuit.
- Pinout: pins 1–18 identical, VIO_SEL on pin 15 in both (M10S DS R08 Table 10, F10S DS R03 Table
  10).
- Mechanical: identical (Table 21 in both).
- MSL: 4 for both.

The differences are electrical, not pins:

| | MAX-F10S | MAX-M10S |
|---|---|---|
| Bands | L1 + L5 | L1 only |
| Front end | SAW–LNA–SAW | LNA–SAW with an LTE B13 notch; an external SAW "may be required" next to other radios |
| Noise figure | 3.5 dB L1 / 3.0 dB L5 | 1.5 dB |
| ICC_RF absolute maximum | 200 mA | 250 mA |
| Typical current | 21 mA | about 11 mA |
| 915 MHz immunity | not published | −17 dBm |
| Recommended bias inductor | 47 nH (L1 + L5) | 27 nH (L1) |

The 47 nH part meets u-blox's > 500 Ω criterion at L1, so it serves both modules. Default
constellations differ (firmware).

### 6.2 Radio: U31 EBYTE E22-900MM22S

Pinout from the EBYTE manual v1.3 §3:

| Pins | Function |
|---|---|
| 1 | VCC (1.8–3.7 V) |
| 2, 7, 16 | GND |
| 3 | NRST (input, active low) |
| 4, 5, 8, 17 | NC |
| 6 | ANT (stamp hole, about 50 Ω) |
| 9 | TXEN (input, RF-switch TX, active high) |
| 10 | RXEN (input, RF-switch RX, active high) |
| 11 | BUSY |
| 12 | MISO |
| 13 | MOSI |
| 14 | NSS |
| 15 | SCK |
| 18 / 19 / 20 | DIO3 / DIO2 / DIO1 |

The RF switch is **not** controlled inside the module. TXEN and RXEN must be driven. §4.2: "DIO2
can be connected with TXEN … used to control the RF switch". The §5.1 basic circuit drives TXEN and
RXEN from MCU IOs.

| Net | Connections |
|---|---|
| 3V3 | FB31.1 |
| 3V3_RADIO | FB31.2, U31.1, C310.1, C311.1, C312.1, R310.1 |
| GND | U31.2, U31.7, U31.16, C310.2, C311.2, C312.2, R311.2, R312.2, D31.2, L31.2, J31 ground legs |
| RADIO_RF | U31.6 ANT, 50 Ω GCPW, J31 centre, D31.1 (at J31), L31.1 |
| RADIO_TXEN | U31.19 DIO2, U31.9 TXEN (local trace) |
| RADIO_NSS | U31.14, R310.2, U1.51 (PB12) |
| RADIO_SCK | U31.15, R313.2; R313.1 ← U1.52 (PB13) |
| RADIO_MISO | U31.12, R314.1; R314.2 → U1.53 (PB14) |
| RADIO_MOSI | U31.13, R315.2; R315.1 ← U1.54 (PB15) |
| RADIO_BUSY | U31.11, U1.55 (PD8) |
| RADIO_NRST | U31.3, R311.1, U1.56 (PD9) |
| RADIO_DIO1 | U31.20, U1.57 (PD10) |
| RADIO_RXEN | U31.10, R312.1, U1.45 (PE15) |
| Not connected | U31.4, .5, .8, .17, .18 (DIO3: passive crystal, no TCXO) |

| Ref | Value / part | Package | LCSC (JLC stock 2026-10-15) | Why |
|---|---|---|---|---|
| U31 | EBYTE E22-900MM22S (alt. E22-900M22S, different footprint) | 10 × 10 × 2.5 mm, 20 stamp-hole pads | C5333985 (462, ext.) / C411293 | F10 |
| FB31 | BLM18KG221SN1D | 0603 | C88980 (ext.) | 6 mV drop at 119 mA; keeps VBAT near the 3.3 V the SX1262 needs for full +22 dBm |
| C310 | 22 µF 25 V X5R | 0805 | C45783 (basic) | EBYTE C1 (10 µF), raised for the PA step (Inference) |
| C311 | 100 nF | 0402 | C1525 (basic) | Bypass |
| C312 | 10 nF | 0402 | C15195 (basic) | EBYTE C2 |
| R310 | 100 kΩ | 0402 | C25741 (basic) | NSS high in reset |
| R311 | 2.0 kΩ | 0402 | C4109 (basic, already on the BOM) | Holds the radio in reset (E4); ≤ 0.3 V even with a 20 kΩ internal pull-up |
| R312 | 100 kΩ | 0402 | C25741 (basic) | RXEN low in reset |
| R313–R315 | 33 Ω | 0402 | C25105 (basic) | SPI edge damping near the RF strip. EBYTE §4.1 recommends series resistors on host lines (200 Ω on UART lines); 33 Ω is chosen here for SPI timing (Inference) |
| D31 | Infineon ESD103-B1-02EL, ±15 V working, 0.09 pF @ 1 GHz, Vcl 20 V @ 1 A TLP | TSLP-2-20 (1.0 × 0.6) | C535146 (221, ext.) | RF ESD; stands off the RF peaks (E8) |
| L31 | 330 nH (EBYTE §5.1 L1, shunt at ANT), e.g. Sunlord SDCL1005CR33JTDF | 0402 | C89954 (5465, ext.) — optional | DC path to GND for static. Even above its SRF, its shunt impedance at 915 MHz is several hundred ohms or more, so the loss is < 0.05 dB (Inference). Leave unfitted to save a code |
| J31 | 50 Ω edge-launch SMA | — | procurement reviewer | F10 |

Supply and RF notes:
- Supply 1.8–3.7 V, absolute maximum 3.7 V, "≥ 3.3 V can ensure the output power" (EBYTE §2.1–2.2).
  SX1262: 3.9 V absolute maximum; +10 dBm absolute maximum RF input (Table 3-2).
- The antenna pin is "about 50 ohms" with no matching required. An optional not-fitted pi network
  on the radio line would allow VNA tuning against the in-airframe dipole.
- If the module has an IPEX connector (the feature list is shared with the M22S family), leave it
  unused.
- **Land pattern.** EBYTE gives only the module drawing: 10.0 mm square, 1.27 mm pitch, pin-1
  centre 2.46 mm from the edge, bottom pad 0.80 wide × 0.75 deep with a 0.40 mm half hole. There is
  no recommended land, so derive one from the drawing and check it against the LCSC/EasyEDA
  footprint for C5333985 (layout reviewer).
- EBYTE: no high-frequency digital, analog or power routing under the module on its own layer.

### 6.3 Parts removed from R6 (option a)

- **Connectors and port supply:** J130, J131, U14, U15, U16, L4, TP130.
- **Capacitors:** C170–C178, plus C179/C180 (the D130/D131 bypass capacitors).
- **Resistors:** R190–R206.
- **ESD arrays:** D130, D131.
- **Nets:** TLM_*, RADIO_*_MCU (old), RADIO_*, GPS_*.

Each of U14, U15 and U16 shares its LCSC code with U8, U10 or U7, and L4 shares one with L3, so
removing them frees placements but no extended codes.

**Extended-code check (for the procurement reviewer).** This design adds MAX-F10S, E22, L30,
FB30/FB31 (one code), D30, D31, the SMA and optionally L31: 7–8 new extended codes. Removing
J130/J131 (and R195, if it is extended) frees 2–3. R6 was at 48 against the new limit of 52, so
the limit is tight. Fallbacks:
- Leave L31 unfitted.
- Use ESD103 at both SMAs (one code, but a higher clamp voltage on the GNSS port).
- Connect the GNSS directly to 3V3 without FB30, as in u-blox Figure 30, if a code is needed.

## 7. Sources (maker documents; page or section cited in the text)

- ST DS12110 Rev 11 (Jan 2026), STM32H742xI/G-H743xI/G: https://www.st.com/resource/en/datasheet/stm32h743vi.pdf. §3.8; Table 9 (pp. 64–88); Table 10 (pp. 89–98); Table 15; Table 120 (p.216).
- ST AN2606 Rev 70 (Feb 2026), §60, Table 135 (pp. 320–323), Figure 77 (p.324): https://www.st.com/resource/en/application_note/an2606-stm32-microcontroller-system-memory-boot-mode-stmicroelectronics.pdf
- u-blox MAX-F10S Data sheet UBXDOC-963802114-12732 R03 (Tables 10–15, 21; §4.3): https://content.u-blox.com/sites/default/files/documents/MAX-F10S_DataSheet_UBXDOC-963802114-12732.pdf
- u-blox MAX-F10S Integration manual UBXDOC-963802114-12892 R01 (§1.3, §2.1.2, §3.2.3, §3.3.1, §4.1, §4.3, Figures 23/30/32, App. A.1, App. C Tables 40–45): https://content.u-blox.com/sites/default/files/documents/MAX-F10S_IntegrationManual_UBXDOC-963802114-12892.pdf
- u-blox MAX-M10S Data sheet UBX-20035208 R08 (Tables 10–15, 21): https://content.u-blox.com/sites/default/files/MAX-M10S_DataSheet_UBX-20035208.pdf
- u-blox MAX-M10S Integration manual UBX-20053088 R05 (§4.3, Table 43 p.79, Table 54): https://content.u-blox.com/sites/default/files/MAX-M10S_IntegrationManual_UBX-20053088.pdf
- EBYTE E22-900MM22S user manual v1.3 (2023-12-13), via JLC/LCSC C5333985 (§2–§5): https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2212192008_Chengdu-Ebyte-Elec-Tech-E22-900MM22S_C5333985.pdf; part page https://jlcpcb.com/partdetail/Chengdu_Ebyte_ElecTech-E22900MM22S/C5333985
- Semtech SX1261/2 data sheet Rev 1.2 (June 2019), DS.SX1261-2.W.APP. Read from the copy at https://cdn.sparkfun.com/assets/6/b/5/1/4/SX1262_datasheet.pdf (Tables 3-1/3-2/3-3/3-6/3-9, Figures 5-3/5-4, §8.2, §8.3.1, Table 8-3, §9.6.1)
- Diodes AP63200/01/03/05 DS41326 Rev 3-2: https://www.diodes.com/assets/Datasheets/AP63200-AP63201-AP63203-AP63205.pdf. AP63300/01 DS42002 Rev 3-2: https://www.diodes.com/assets/Datasheets/AP63300-AP63301.pdf
- TI TPS2121 SLVSEA3F: https://www.ti.com/lit/ds/symlink/tps2121.pdf. TPS25947 SLVSFC9C: https://www.ti.com/lit/ds/symlink/tps25947.pdf. TPS2595 SLVSE57C: https://www.ti.com/lit/ds/symlink/tps2595.pdf. TPS2553 SLVS841F: https://www.ti.com/lit/ds/symlink/tps2553.pdf. TPD1E0B04 SLVSDG9C §5.6: https://www.ti.com/lit/ds/symlink/tpd1e0b04.pdf
- Infineon ESD103-B1-02EL data sheet v2.0 (2022-03-15), Tables 4–6. Read from the copy at https://cdn.components.ru/media/PDF/8100385.pdf
- Murata LQG15HS spec JELF243B-0010 (47 nH: SRF ≥ 1000 MHz, 0.72 Ω, 300 mA), via LCSC C97998: https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/1811081515_Murata-Electronics-LQG15HS47NJ02D_C97998.pdf
- Winbond W25Q128JV Rev I: https://www.winbond.com/resource-files/W25Q128JV%20RevI%2008232021%20Plus.pdf. ST LSM6DSV320X: https://www.st.com/resource/en/datasheet/lsm6dsv320x.pdf. TE MS5611-01BA03 (LCSC copy, C15639).
- Abracon APARC2511X-SG3L5 (supply 2.7/3.3/5.0 V, LNA 28 ± 3 dB): https://www.kyohritsu.com/eclib/PDF/A/APARC2511X-SG3L5.pdf
- JLCPCB parts API (stock, library type, attributes, checked 2026-10-15) for C88980, C15127, C20917, C105432, C22859, C1975594, C535146, C97998, C89954, C57269, C94598 and the basic passives.

## 8. Inferences (not measured or not checked against a primary source)

- **Efficiency and capacitance:** AP63203 efficiency (0.85); its PFM/PWM boundary (about 0.2 A);
  its load-step droop (5–15 mV); effective capacitance after DC-bias derating.
- **3V3A and junction temperature:** the 3V3A RC corner (about 2.4 kHz); U2's junction
  temperature on this 4-layer board.
- **Limiter:** the S8550's V_EB(on) and therefore the short-circuit current (45–70 mA); loop
  stability with Q30/C302.
- **GNSS:** steady current budget (40 mA, no maximum published); whether a RESET_N restart counts as
  "startup" for safeboot via TIMEPULSE.
- **Radio:** the E22's internal RF-switch state with TXEN = RXEN = 0 (assumed isolation); the
  benefit of RampTime on supply droop.
- **Margins and losses:** the TVS insertion losses; the L31 loss at 915 MHz; the F6 hold-up times
  in §4.4; the USB-path margins in E9.
- **Datasheet values not opened:** the beads' and MOSFETs' figures are taken from JLC listings, not
  the makers' PDFs.
