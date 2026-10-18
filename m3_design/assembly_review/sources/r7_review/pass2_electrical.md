# R7 pass 2: schematic and electrical correctness of the R7 change

Reviewer scope: the electrical design R7 adds or touches: U30 MAX-F10S (and the MAX-M10S drop-in),
U31 E22-900MM22S, the antenna-bias limiter, the RF ESD and pi networks, the ferrite-fed supplies,
the U1 pin contract (reset states, alternate functions, ROM bootloader, EXTI), the 3V3 budget, and
the parts removed from R6. Layout, DFM, procurement and requirement wording belong to the parallel
reviewers and appear only where an electrical conclusion depends on them. Read-only review: no
repository file other than this report was changed.

## Baseline and what was run

- Worktree `rocket-flight-computer-r7`, branch `m3-assy-r7`, uncommitted R7 work on R6 `3b215ba`.
  Board SHA-256 `03fe75720f46b1382d9d3216dbffd8ae642d0125722c04589ff97c964aa86d54` (checked before
  and after the review; unchanged).
- `tools/check.sh` (temporary copies): DRC 0, unconnected 0, parity 0, ERC 0, metadata/3D OK,
  silkscreen 0, R7 CAD contract OK, actuator contract OK, fit OK, exit 0.
- Netlist regenerated with `kicad-cli sch export netlist --format kicadxml` from `m3.kicad_sch`
  (scratch copy). R6 netlist regenerated the same way from `git archive 3b215ba
  m3_design/assembly_review` (scratch copy) and compared pin by pin.
- Board read with pcbnew (no save): placement, pad nets and coordinates of every R7 part, track
  widths/lengths on 3V3, 3V3_GNSS, 3V3_RADIO and the limiter nets, 3V3 In2 zone fill.
- Maker documents read from PDF text and rendered figures (list in "Sources"). Part values,
  tolerance and TCR of R300, S8550, BLM18KG221SN1D and ESD103 re-checked on the live JLC parts API
  (2026-10-15).
- Small-signal model of the limiter loop (pure Python, scratch only) for the stability question.

## 1. Summary

- **No Critical and no Major finding.** Every pin of U30 and U31 is connected as the maker
  documents require; every new MCU-driven line has a defined, harmless state in MCU reset and in
  the ROM bootloader; the radio is held in reset by R311 whenever PD9 is not driven; no radio or
  GNSS net reaches pyro, ARM, actuator, BOOT0 or NRST copper; nothing removed from R6 is used
  elsewhere.
- **The antenna-bias limiter works as intended by calculation**, inside a narrow window: 2.93 V at
  the antenna at 15 mA (typical VCC_RF only, 28 mV over F10's 2.9 V at the regulator's minimum),
  at most 48 mA into a short at −20 °C (F10: ≤ 50 mA), 25–38 mA at +85 °C. R300 must lie in 14.0–17.0 Ω
  to meet both F10 limits with the inferred VCC_RF and VEB; 15 Ω does. The loop's stability depends
  on VCC_RF's internal source impedance, which u-blox does not publish: phase margin 59–91° if it is
  stiff, down to about 12° if it is a bare ferrite (model, Inference). There is no footprint to
  compensate it if the bench shows ringing (ELECTRICAL-01).
- **Five Minor findings**: the limiter compensation provision (01), the bias-feed margins and the
  unstated antenna-current limit (02), EXTI/vector constraints missing from the pin contract (03),
  the higher GNSS ESD clamp versus pass 1's recommendation and its unrecorded trade-off (04), and an
  optimistic Q30 short-circuit temperature in M3_R7 (05).

## 2. Findings

| ID | Sev. | Req. | Finding | Evidence | Recommended fix |
|---|---|---|---|---|---|
| ELECTRICAL-01 | Minor | F10 (limiter), AGENTS §2.5 | The Q32/Q30 current-limit loop has no compensation element and no footprint for one. Its dominant pole is the gate node (R301 ∥ R302 ≈ 9.1 kΩ with the bootstrapped Q30 capacitances), and the crossover lands at 1.4–9.7 MHz. If VCC_RF is stiff the phase margin is 59–91°; if VCC_RF is fed inside the module by a bare ferrite (the IM says only "internally connected to VCC through a ferrite bead"), the bead inductance acts as extra source degeneration of Q30 and the margin falls to 12–22° in the worst parameter corners. The loop is active only in a short, a heavy overload or the antenna's charging inrush, so normal reception is unaffected | Model (scratch `loop.py`): Rg 4–12 Ω, Ciss 645 pF, Crss 55 pF (AO3401A DS Rev 3.1 p.2), gm30 0.3–1.4 S, gm32 2.7–9.7 mS (IC 0.07–0.25 mA), fT 15–50 MHz, Cob 13 pF (S8550 DS p.2), VCC_RF stiff / 0.5 µH bead / 1 µH bead + 1 nF. Worst PM 12° at 3.55 MHz. With 1 nF from GNSS_ANT_GATE to GND the worst PM is 62°, with 4.7 nF 83°. Nets: GNSS_ANT_GATE = Q30.1, Q32.3, R301.2, R302.1; parts on B.Cu under U30 at Q30 (10.75, 13.00), Q32 (5.00, 12.00), R302 (8.25, 16.00). MAX-F10S IM R01 Table 1 (VCC_RF row) | Add one 0402 footprint from GNSS_ANT_GATE to GND next to R302 (fit 1–2.2 nF, or DNP and fit on the bench result). Gate turn-on through R302 stays ≈ 17 µs with 1 nF; turn-off through R301 ≈ 0.17 ms. Keep the ORDERING §5 short test and add a pass criterion (no sustained oscillation at −20 °C and hot, scoped at GNSS_ANT_GATE and VCC_RF). If no board change is made, record the analysis and accept on the bench result |
| ELECTRICAL-02 | Minor | F10 (≥ 2.9 V at 15 mA; ≤ 50 mA), ORDERING §7 | Both F10 bias limits are met only on inferred values and with small margins. VCC_RF has only a typical value (VCC − 0.1 V), so at the AP63203 minimum (VFB 3.27 V) the antenna gets 2.928 V at 15 mA with R300 at +1 %: 28 mV over 2.9 V. The short-circuit current at −20 °C is up to 48 mA from the S8550's graph-read VEB (up to 0.71 V at 0.07–0.2 mA, with spread) over R300 −1 % and −0.45 % TCR. R300 must lie in 14.0–17.0 Ω for both limits. The hot limit is 25–38 mA at +85 °C, so an antenna drawing more than about 20 mA could be throttled when hot. F10 and ORDERING §7 specify no maximum antenna current | `docs/M3_R7.md:154,158`; F10S DS R03 Table 13 (VCC_RF typ only); AP63203 DS41326 VFB 3.27–3.33 V; JLC C22810: 15 Ω ±1 % ±100 ppm/K; JSCJ S8550 DS p.2 IC–VBE: 25 °C 0.62 V at 1 mA, 57 mV/decade; 100 °C 0.56 V at 1 mA. Calculation in §4.3 | State the antenna requirement on the antenna side: ≤ 20 mA (so it stays below the hot knee) and ≥ 2.7 V minimum supply, as the APARC2511X does, in F10 and in ORDERING §7's antenna/lead notes. Keep ORDERING §5's cold/hot short and 15 mA voltage measurements, which already exist, and record the measured VCC_RF drop. No hardware change |
| ELECTRICAL-03 | Minor | F10 (DIO1 "no conflict with EXTI0/1/4/6"), firmware binding contract | The pin contract checks only DIO1's EXTI line. BUSY on PD8 is EXTI8, which shares the EXTI9_5 vector that the existing firmware hard-codes to USB_FAULT_N (PD6, line 6). TIMEPULSE on PD14 is EXTI14, the same line as PULLPIN on PC14 (U1.8). Neither constraint is written down: BUSY must be polled (or the EXTI9_5 handler demultiplexed), and TIMEPULSE must use TIM4_CH3 input capture, not EXTI14, if PULLPIN is ever interrupt-driven | Netlist: U1.55 RADIO_BUSY (PD8), U1.61 GNSS_TP_MCU (PD14), U1.8 PULLPIN (PC14), U1.87 USB_FAULT_N (PD6). `m3_firmware/src/power_status_stm32.c:6` (irqs EXTI0/1/4/9_5) and `:42` (`EXTI9_5_IRQHandler(void){event(64U);}`). `docs/M3_R7.md:118,126` give no EXTI note | Add to the M3_R7 pin contract and F10's binding note: "BUSY polled (EXTI9_5 is USB_FAULT_N's); TIMEPULSE on TIM4_CH3 capture (EXTI14 is PULLPIN's line)". Documentation only |
| ELECTRICAL-04 | Minor | F10 ("ESD diode rated for the RF swing at each jack"), AGENTS §2.5 | D30 meets its ratings (VWM ±15 V against 3.2 V bias), but its clamp is much higher than the part pass 1 chose for the GNSS port: ESD103-B1-02EL clamps at 20 / 36 / 48 V at 1 / 8 / 16 A TLP. That residual goes to U30 RF_IN through R304 (0 Ω), whose ESD tolerance u-blox does not publish (RF_IN abs max is only ±5.5 V DC). The step-A swap (one code instead of two, at the 52-code limit) is recorded only in `r7_sch.py`'s docstring; M3_R7 gives only the working voltage | ESD103 DS v2.0 Tables 2, 4, 6; F10S DS Table 12 (V_DCrfin ±5.5 V; no RF_IN ESD figure; IM §5.1.1 asks for ESD measures where an antenna can be touched); `docs/M3_R7.md:170`; pass1_electrical E8 (TPD1E0B04 for the GNSS port); `m3_design/r7_sch.py:10–11` | Record the trade-off in M3_R7 §"RF chains" with an ESD handling rule for the GNSS lead: connect the antenna with the board unpowered on an ESD-safe bench; no hot-plug in the field. Hardware option if a code is freed: TPD1E0B04DPYR (C1975594) at D30, paid for by splitting R300 into basic 10 Ω + 4.7/5.1 Ω (M3_R7 §"Extended codes and cost") |
| ELECTRICAL-05 | Minor | AGENTS §2.5 (inferences labelled) | M3_R7 gives Q30's short-circuit rise as +14 K from AOS RθJA 125 °C/W, but AOS measures that on 1 in² of 2 oz copper. Q30 sits on B.Cu with 0.20 mm traces on all three pins. A realistic figure is 2–3× higher, +28–40 K (Inference), giving Tj ≈ 115–125 °C in an 85 °C bay. That is still below the 150 °C limit, so only the record is affected | `docs/M3_R7.md:160`; AO3401A DS Rev 3.1 p.1 (RθJA 100/125 °C/W, note A: 1 in² FR-4, 2 oz); board: GNSS_ANT_DC/SRC/GATE tracks 0.20 mm on B.Cu (§4.6). Dissipation 2.45 V × 46 mA ≈ 0.11 W | Correct the row to "≈ 0.11 W; +14 K on 1 in² copper, about +30–40 K on this layout (Inference); Tj < 150 °C" |

## 3. Pin-by-pin check

### 3.1 U30 MAX-F10S (and MAX-M10S): netlist against the data sheets

Sources: MAX-F10S DS R03 Table 10–14; MAX-F10S IM R01 Table 1, §3.2.3.4, §4.1; MAX-M10S DS R08
Tables 10–14. Board pad coordinates from pcbnew. Pins 1–9 run along y = 19.70 (x 6.01 → 14.81),
pins 10–18 along y = 10.20 (x 14.81 → 6.01), counter-clockwise from the top: this is DS Figure 2
rotated 90° clockwise, on F.Cu, not mirrored.

| Pin | Name | Net (members) | Maker requirement | Result |
|---|---|---|---|---|
| 1, 10, 12 | GND | GND | Connect to GND | OK |
| 2 | TXD | GNSS_TXD → R305 220 Ω → PC7 (USART6_RX) | Output; 2 mA VOH spec | OK; R305 at U30 (7.11, 22.45) |
| 3 | RXD | GNSS_RXD ← R306 220 Ω ← PC6 (USART6_TX) | Input, internal pull-up 8–40 kΩ (Table 11/14) | OK; idles high while PC6 is analog in MCU reset |
| 4 | TIMEPULSE | GNSS_TIMEPULSE → R307 1 kΩ → PD14 | Shared with SAFEBOOT_N via internal 1 kΩ; must not be low at start-up (DS note 14, IM Table 1 note) | OK: no pull-down anywhere; PD14 analog in reset; never enable PD14's pull-down (contract) |
| 5 | EXTINT | NC | "Leave open if not used" | OK |
| 6 | V_BCKP | NC | IM §4.1.3: "If the hardware backup mode is not used, leave the V_BCKP pin open" | OK |
| 7 | V_IO | 3V3_GNSS (tied to VCC) | 2.7–3.6 V with VIO_SEL open; ≤ VCC + 0.3 V; ramp 25–35 000 µs/V (Table 12) | OK: same node as VCC; 3V3 ramps over the AP63203's 4 ms soft start, about 1.2 ms/V |
| 8 | VCC | 3V3_GNSS (FB30, C300 10 µF, C301 100 nF) | 1.76–3.6 V; series R ≤ 0.2 Ω (IM §4.1.1); 100 mA inrush (DS §4.3) | OK: ≈ 0.07 Ω (§4.5) |
| 9 | RESET_N | GNSS_RESET_N ↔ PC8 (no pull, no C) | Internal 7–13 kΩ pull-up; ≥ 1 ms low to reset; leave open if unused | OK: PC8 open-drain, analog (released) in reset |
| 11 | RF_IN | GNSS_RF_IN ← R304 0 Ω ← GNSS_RF_ANT | 50 Ω, internally DC-blocked, ±5.5 V DC, 0 dBm RF abs max | OK: 3.2 V bias within ±5.5 V (u-blox Fig. 23 injects bias the same way) |
| 13 | LNA_EN | GNSS_LNA_EN → Q31 gate, R303 100 kΩ to GND | Output high in continuous mode; pull-down in software standby; pull-up in reset and safeboot (Table 11); also drives the internal LNA | OK: 33 µA load against 2 mA drive |
| 14 | VCC_RF | GNSS_VCC_RF → R300, Q32 emitter | VCC − 0.1 V typ; ≤ 50 mA operating; 200 mA abs max (M10S: 250 mA) | OK by calculation (§4) |
| 15 | VIO_SEL | NC | Open = 3.3 V I/O; GND = 1.8 V | OK: pad has its own unconnected net; DRC 0 means no copper touches it |
| 16, 17 | SDA, SCL | NC | "Leave open if not used" (internal pull-ups) | OK |
| 18 | SAFEBOOT_N | GNSS_SAFEBOOT_N → TP30 only | "Leave open"; low at start-up enters safeboot | OK: bare pad at (2.00, 9.60), no pull |

MAX-M10S drop-in: Table 10 (pins 1–18), Table 11 (pin states), Table 12–14 (limits) are identical
to the F10S apart from ICC_RF abs max 250 mA and the noise figure. The same circuit is correct for
it. L30 47 nH is u-blox's own L4 part for the F10S (IM Table 42: Murata LQG15HS47NJ02, > 500 Ω at
L1/L5, ≥ 300 mA); the record's 27 nH swap for an L1-only M10S is consistent with that.

### 3.2 U31 E22-900MM22S: netlist against EBYTE manual v1.3 ch. 3, §4–5 and SX1262 DS Rev 1.2

| Pin | Name | Net | Maker requirement | Result |
|---|---|---|---|---|
| 1 | VCC | 3V3_RADIO (FB31, C310 22 µF, C311 100 nF, C312 10 nF) | 1.8–3.7 V, abs 3.7 V; "≥ 3.3 V ensures output power" | OK; 3.26–3.33 V at the pin (observation in §6) |
| 2, 7, 16 | GND | GND | — | OK |
| 3 | NRST | RADIO_NRST: PD9, R311 2.0 kΩ to GND (at U31, (37.0, 14.43)) | Active low; SX1262 internal 50 kΩ pull-up; VIL_N ≤ 0.2 × VBAT; ≥ 100 µs (DS §8.1, Tables 3-10, 8-3) | OK: 0.13 V (0.30 V with a 20 kΩ pull-up) against 0.65 V; PD9 sources 1.67 mA to release |
| 4, 5, 8, 17 | NC | NC | NC | OK |
| 6 | ANT | RADIO_RF ← R316 0 Ω ← RADIO_RF_ANT | Stamp hole, about 50 Ω | OK |
| 9 | TXEN | RADIO_TXEN = pin 19 (DIO2) | "Connected to MCU IO or DIO2" (§4.2) | OK; DIO2 PD in reset, HIZ-PD at start-up and sleep (Table 8-3) |
| 10 | RXEN | RADIO_RXEN: PE15, R312 100 kΩ to GND | MCU IO, active high | OK: low in MCU reset |
| 11 | BUSY | RADIO_BUSY → PD8 | Output; PU in reset | OK |
| 12 | MISO | RADIO_MISO → R314 33 Ω (at U31) → PB14 | HIZ while NSS high or in reset | OK |
| 13 | MOSI | RADIO_MOSI ← R315 33 Ω ← PB15 | Input | OK |
| 14 | NSS | RADIO_NSS: PB12, R310 100 kΩ to 3V3_RADIO | Input | OK: high in MCU reset |
| 15 | SCK | RADIO_SCK ← R313 33 Ω ← PB13 | Input, mode 0 | OK |
| 18 | DIO3 | NC | Passive 32 MHz crystal: no TCXO control (§2.2, §4.2) | OK |
| 19 | DIO2 | RADIO_TXEN | SetDio2AsRfSwitchCtrl: 1 in TX, 0 otherwise (SX1262 §4) | OK |
| 20 | DIO1 | RADIO_DIO1 → PD10 | IRQ; PD in reset | OK |

The board pads follow the same numbering (U31 at (29.86, 14.00), rot 180°, pin 1 (34.81, 16.54),
counter-clockwise; matched to the EasyEDA land in step A).

### 3.3 U1 pins (DS12110 Rev 11 Table 9/10, §3.8; AN2606 Rev 70 Table 135)

| Pin | Port | Net | AF used | MCU-reset / bootloader state → line | Bootloader role | EXTI |
|---|---|---|---|---|---|---|
| 45 | PE15 | RADIO_RXEN | GPIO | analog → low (R312) | none | 15 |
| 51 | PB12 | RADIO_NSS | GPIO / AF5 SPI2_NSS | analog → high (R310) | none (bootloader SPI2 is on PI0–PI3, not in LQFP100) | 12 |
| 52 | PB13 | RADIO_SCK_MCU | AF5 SPI2_SCK | analog; radio in reset | none | — |
| 53 | PB14 | RADIO_MISO_MCU | AF5 SPI2_MISO | analog; in the bootloader **USART1_TX push-pull**: no contention, SX1262 MISO is HIZ (NSS high, in reset) | USART1 alt. TX | — |
| 54 | PB15 | RADIO_MOSI_MCU | AF5 SPI2_MOSI | analog; in the bootloader **USART1_RX input pull-up**: nothing drives the line, so it cannot capture the bootloader | USART1 alt. RX | — |
| 55 | PD8 | RADIO_BUSY | GPIO in | — | none | 8 (EXTI9_5 vector: ELECTRICAL-03) |
| 56 | PD9 | RADIO_NRST | GPIO out | analog → **low (R311): radio held in reset** | none | — |
| 57 | PD10 | RADIO_DIO1 | GPIO in, EXTI10 | — | none | 10 (no other user) |
| 61 | PD14 | GNSS_TP_MCU | AF2 TIM4_CH3 | analog: no load on TIMEPULSE | none | 14 (= PULLPIN PC14: ELECTRICAL-03) |
| 63 | PC6 | GNSS_RXD_MCU | AF7 USART6_TX | analog → high (module pull-up) | none | — |
| 64 | PC7 | GNSS_TXD_MCU | AF7 USART6_RX | analog; module streams into a high-Z pin | none | — |
| 65 | PC8 | GNSS_RESET_N | GPIO open-drain | analog → released | none | — |
| 31, 66–69 | PA7, PC9, PA8, PA9, PA10 | NC | — | — | SPI1_MOSI, I2C3_SDA/SCL, USART1 (left open: nothing can capture them) | — |

- All GPIOs except the debug pins are analog after reset (DS12110 §3.8, line "After reset, all
  GPIOs (except debug pins) are in Analog mode"). None of the new pins is a debug pin.
- PE4 (PYRO1_GATE_N) has no SPI2, USART6 or TIM4 alternate function (DS Table 10), and no radio
  or GNSS net shares copper with pyro, ARM, actuator, BOOT0 or NRST (netlist: every RF net's
  members listed in §5).
- Existing EXTI users (firmware): lines 0, 1, 4, 6. DIO1 on line 10 has no conflict.

## 4. Antenna-bias limiter (Q30–Q32, R300–R303, L30, C302)

### 4.1 Topology (netlist and board)

VCC_RF (U30.14) → R300 15 Ω → GNSS_ANT_SRC → Q30 AO3401A S→D → GNSS_ANT_DC (C302 10 nF) → L30 47 nH
→ GNSS_RF_ANT. Q32 S8550: E = VCC_RF, B = ANT_SRC, C = ANT_GATE, so its EB junction sits across R300.
R301 100 kΩ G–S (off by default), R302 10 kΩ G → Q31 AO3400A drain, Q31 gate = LNA_EN with R303
100 kΩ to GND. SOT-23 pinouts checked: AO3401A/AO3400A 1 G, 2 S, 3 D (AOS DS Rev 3.1 p.1), S8550
1 B, 2 E, 3 C (JSCJ DS p.1). Board: all on B.Cu under U30's west half (§2 coordinates).

### 4.2 LNA_EN states (DS Table 11, Table 14)

| U30 state | LNA_EN | Q31 | Antenna bias |
|---|---|---|---|
| Continuous | output high (≥ V_IO − 0.4 V) | on (AO3400A VGS(th) 0.65–1.45 V) | on; Q30 VGS ≈ −2.87 V (R302/R301 divider), RDS(on) ≤ 85 mΩ |
| Reset (RESET_N low) | input pull-up 8–40 kΩ against R303 100 kΩ → 2.36–3.06 V | on | on (harmless) |
| Software standby | input pull-down 21–180 kΩ, plus R303 | off | off (R301 holds Q30 off) |
| Safeboot | input pull-up | on | on |
| LNA_EN high-Z / module unpowered | R303 → 0 V | off | off |

### 4.3 Normal operation and short circuit

Antenna voltage, R300 at +1 % (15.15 Ω), Q30 85 mΩ, L30 0.72 Ω max, feed drop to VCC included,
VCC_RF = VCC − 0.1 V (typical only):

| AP63203 VFB | 5 mA | 15 mA | 20 mA |
|---|---|---|---|
| 3.27 V (min) | 3.088 V | **2.928 V** | 2.848 V |
| 3.30 V (typ) | 3.118 V | 2.958 V | 2.878 V |
| 3.33 V (max) | 3.148 V | 2.988 V | 2.908 V |

Q32 at 15–20 mA: VEB = 0.23–0.30 V, against 0.38–0.53 V for the 0.07 mA that starts to lift the gate
at +85 °C: IC ≲ 6 µA, a gate rise of ≲ 60 mV against |VGS| 2.87 V, so no throttling.

Short-circuit current = VEB(IC needed) / R300. IC needed = Vg/R302 − (Vs − Vg)/R301 with Vg = Vs −
|VGS(46 mA)|, |VGS| 0.6–1.7 V over AO3401A VGS(th) −0.5…−1.3 V and temperature: IC ≈ 0.07–0.2 mA.
From the JSCJ IC–VBE curves (read from the graph: 25 °C 0.62 V at 1 mA, 57 mV/decade; 100 °C
0.56 V at 1 mA), VEB at 0.07–0.2 mA is 0.54–0.58 V at 25 °C. With −0.84 mV/K (the curves) to
−2.2 mV/K (textbook) and ±0.03 V unit spread:

| Temperature | VEB | Isc (R300 15 Ω −1 %, TCR ±100 ppm/K) |
|---|---|---|
| −20 °C | 0.55–0.71 V | **37–48 mA** (F10 ≤ 50 mA) |
| +25 °C | 0.51–0.61 V | 34–41 mA |
| +85 °C | 0.38–0.56 V | 25–38 mA |

- R300 window for both F10 limits at VFB 3.27 V and VEB 0.70 V: 14.0 Ω ≤ R300 ≤ 17.0 Ω. 15 Ω is
  inside it; both edges rest on the inferred values (ELECTRICAL-02).
- Abs max: VCC_RF 200 mA (F10S) / 250 mA (M10S); R300 32 mW of 100 mW; L30 46 of 300 mA; Q32 VCE
  −1.3…−2.4 V (active), dissipation µW.
- Q30 in a short: VDS ≈ 2.45 V × 46 mA ≈ 0.11 W (ELECTRICAL-05 on its temperature).
- A sudden short: C302's 42 nJ discharges through L30 into the short (≈ 34 ns quarter period);
  before the gate moves, Q32's EB junction clamps the R300 drop and its collector current charges
  Q30's gate in roughly 0.1–0.2 µs, so the overcurrent from VCC_RF lasts a fraction of a
  microsecond (Inference; not a thermal stress).
- Turn-on into a short or a capacitive antenna: the gate falls with τ ≈ 10 kΩ × 0.7 nF ≈ 7 µs, so
  Q32 takes over before the current exceeds the limit.

### 4.4 Loop stability

Modelled as in ELECTRICAL-01. Crossover 1.4–9.7 MHz; the L30–C302 tank (7.3 MHz, ≤ 6.5 Ω) sits at
Q30's drain, where the saturated FET is a current source, so it barely enters the loop. The
uncertain element is VCC_RF's source impedance, which is common to Q32's emitter and R300 but adds
series impedance to Q30's source:

| VCC_RF model | Phase margin over the parameter corners |
|---|---|
| Stiff (internal capacitance ≥ 1 µF) | 59–91° |
| 0.5 µH bead, no capacitance | 22–85° |
| 1 µH bead + 1 nF | 12–78° |
| Any of these + 1 nF GNSS_ANT_GATE → GND | worst 62° (4.7 nF: 83°) |

### 4.5 Supplies and ferrites

- FB30/FB31 BLM18KG221SN1D: 220 Ω ±25 % at 100 MHz, 2.2 A (85 °C), DCR ≤ 0.050 Ω (Murata
  JENF243A-0003 §3; JLC C88980 "50mΩ").
- GNSS feed series resistance (u-blox IM §4.1.1: ≤ 0.2 Ω): FB30 0.050 + 3V3_GNSS tracks 9.9 mΩ
  (0.30 mm F.Cu, FB30.2 (11.58, 23.85) → U30.8 (13.71, 19.70)) + feed via and F.Cu 1.7 mΩ + In2
  plane (estimate) ≈ **0.07 Ω**. Meets ≤ 0.2 Ω.
- Radio feed: R161.1 → 0.40 mm F.Cu → via (35.73, 27.34) → 0.25 mm In2 detour (36.73, 28.34) →
  (36.73, 31.54) → (34.53, 31.34) into the In2 3V3 pour: about 25–35 mΩ + FB31 0.05 Ω → about 10 mV at
  119 mA. No limit applies.
- U30 VCC/V_IO: C301 100 nF ≈ 2.2 mm from pins 7/8, C300 10 µF at FB30. U31: C311/C312 at 1.8–2.0 mm,
  C310 22 µF at 3.3 mm (EBYTE §5.1 shows 10 µF + 10 nF). Adequate.
- Total effective 3V3 ceramic ≈ 45–50 µF (C8, C9 22 µF; C23 4.7 µF; C310 22 µF; C300 10 µF, DC-bias
  derated, Inference), inside the AP63203's "22–68 µF is sufficient" (DS41326 §12).

### 4.6 3V3 budget and U2 thermal (AP63203WU-7, θJA 89 °C/W, VFB 3.27–3.33 V, tSS 4 ms)

| Case | 3V3 load | U2 loss | ΔTj | Tj in 70 / 85 °C bay |
|---|---|---|---|---|
| Typical flight, radio transmitting | 0.35–0.41 A | ≈ 0.21 W | ≈ +19 K | ≈ 89 / 104 °C |
| Worst case (MCU 312 mA at Tj 125 °C, LEDs 15, flash 25, buzzer 100, GNSS 40, antenna short 47, radio TX 119, misc 6 mA) | 0.66 A | ≈ 0.35 W | ≈ +31 K | ≈ 101 / 116 °C |

The design limit is Tj ≤ 125 °C, with TSD at 160 °C. RF share: GNSS 24 mA (DS Table 15, 3.0 V), radio
118 mA at +22 dBm (SX1262 DS Table 3-6), antenna 10–15 mA. Capacity is 2 A; U11's minimum ILM is
1.0 A. USB-only remains limited by U10 (355 mA minimum), and the firmware's +14 dBm cap on USB
(pass1 E9) is still needed.

## 5. RF ESD, pi networks and removed parts

- **ESD103-B1-02EL (D30, D31)**: VWM ±15 V, Vtr 21 V typ, 0.09 pF at 1 GHz, IL ≤ 50 nA at 15 V (DS
  v2.0 Tables 2, 4–6). Radio: +22 dBm into 50 Ω is 3.98 V peak, 7.2 V at the SX1262's 10:1 VSWR limit,
  and 7.96 V fully reflected, all below VWM. GNSS: 3.2 V DC bias, below VWM. Clamp: ELECTRICAL-04.
- **Pi-network placement (board)**: J30.5 (12.85, 2.30) → D30.1 (12.85, 5.20) → L30.2 bias tap
  (12.85, 6.18) → C303.1 / R304.1 (11.91 / 12.85, 7.13) → R304.2 / C305.1 (13.71 / 14.65, 7.13) →
  U30.11 (13.71, 10.20). The bias is on the antenna side of the pi network, so R304 can become a
  series capacitor without cutting the feed. C303 and C305 both see the 3.2 V DC (R304 is 0 Ω), so
  anything fitted at either position must be a capacitor rated ≥ 6.3 V. The record says this for
  C303; C305 has the same constraint while R304 is 0 Ω, and pass1 §6.1 says so.
- **Radio chain**: J31.5 → D31.1 (31.54, 5.20) → C313.1 / R316.1 (7.60) → R316.2 / C314.1 → U31.6
  (32.40, 9.05). No DC bias, so either shunt position may also take an inductor.
- **Removed R6 parts**: the 37 references are gone. The only pins that changed on common references
  are U1 31, 45, 51–57, 61 and 63–69. 3V3 (39 other members), GND (153) and RAW_PROTECTED (12) keep
  exactly their R6 members. Every other net touched by the removed parts had only the removed parts
  and one freed U1 pin. Nothing removed is used elsewhere.

## 6. Observations (no finding)

- **Radio supply versus EBYTE's "≥ 3.3 V ensures the output power"**: 3.26 V at U31 with the AP63203
  at VFB minimum and the FB31 path. SX1262 TXDRP is 2 dB at 2.7 V (DS Table 3-9), so the loss at
  3.26 V should be a few tenths of a dB (Inference). Not a requirement.
- **Radio antenna port has no DC bleed** (EBYTE §5.1 shows L1 330 nH to GND; dropped in step A). D31
  still clamps static. If a DC-floating radiator is used, a 0402 inductor can go in C313's footprint
  (no bias on this line).
- **SPI/UART series resistors** R313/R315/R306 sit 10–12 mm of trace from U1 (step B deviation 7).
  At ≤ 8 MHz SPI and UART rates that is electrically short (Inference).
- **During MCU reset or the ROM bootloader**, PB13 (SCK) floats into the SX1262's SCK, which is HIZ
  while the chip is held in reset. Harmless; the firmware drives it once SPI2 is configured.
- **TP30 (SAFEBOOT_N)** is a bare 1.5 mm pad: a conductive short at power-up enters safeboot, and a
  RESET_N pulse from PC8 recovers. This is the intended service access.
- The record's statements on NRST (0.13 V), the reset states, the bootloader isolation, VIO_SEL /
  V_BCKP and the ferrite DCR are confirmed against the maker documents.

## 7. Sources

- u-blox MAX-F10S data sheet UBXDOC-963802114-12732 R03, §3.1–3.2 (Tables 10, 11), §4.1–4.3
  (Tables 12–16): https://content.u-blox.com/sites/default/files/documents/MAX-F10S_DataSheet_UBXDOC-963802114-12732.pdf
- u-blox MAX-F10S integration manual UBXDOC-963802114-12892 R01, Table 1, §3.2.3.4, §3.3.1, §4.1.1–4.1.3,
  §4.3.4 (Fig. 23), App. B (Fig. 30, 32; Table 38), App. C (Tables 41, 42, 45):
  https://content.u-blox.com/sites/default/files/documents/MAX-F10S_IntegrationManual_UBXDOC-963802114-12892.pdf
- u-blox MAX-M10S data sheet UBX-20035208 R08, Tables 10–14:
  https://content.u-blox.com/sites/default/files/MAX-M10S_DataSheet_UBX-20035208.pdf
- EBYTE E22-900MM22S user manual v1.3, ch. 2–5:
  https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2212192008_Chengdu-Ebyte-Elec-Tech-E22-900MM22S_C5333985.pdf
- Semtech SX1261/2 data sheet Rev 1.2 (June 2019), Tables 3-2, 3-6, 3-9, 3-10, 8-3, §4, §8.1–8.2
  (copy read: https://cdn.sparkfun.com/assets/6/b/5/1/4/SX1262_datasheet.pdf)
- ST DS12110 Rev 11, §3.8, Table 9 (LQFP100 pins 45, 51–57, 61, 63–65), Table 10:
  https://www.st.com/resource/en/datasheet/stm32h743vi.pdf
- ST AN2606 Rev 70, §60, Table 135 (pp. 320–323):
  https://www.st.com/resource/en/application_note/an2606-stm32-microcontroller-system-memory-boot-mode-stmicroelectronics.pdf
- AOS AO3401A DS Rev 3.1 (Dec 2023): https://www.aosmd.com/res/datasheets/AO3401A.pdf ; AO3400A DS Rev 3.1
  (Jul 2023): https://www.aosmd.com/res/datasheets/AO3400A.pdf
- JSCJ S8550 SOT-23 DS (D, Oct 2014), p.1 pinout and ratings, p.2 IC–VBE, Cob, fT curves:
  https://datasheet.lcsc.com/datasheet/pdf/e048f602aee74d95b954be40ef1dcefb.pdf?productCode=C105432
- Infineon ESD103-B1-02EL DS v2.0 (2022-03-15), Tables 2, 4–6: https://cdn.components.ru/media/PDF/8100385.pdf
- Murata BLM18 spec JENF243A-0003 §3 (BLM18KG221SN1D row):
  https://datasheet.lcsc.com/datasheet/pdf/2d503a4b167da9bb5d0eb4a3fa711314.pdf?productCode=C88980
- Murata LQG15HS spec JELF243B-0010 §3 (47 nH: 0.72 Ω, SRF ≥ 1000 MHz, 300 mA):
  https://datasheet.lcsc.com/datasheet/pdf/4fdc9bb2296ffef8346418b98de47ce9.pdf?productCode=C97998
- Diodes AP63200/01/03/05 DS41326: VFB 3.27–3.33 V, tSS 4 ms, θJA 89 °C/W, §12:
  https://www.diodes.com/assets/Datasheets/AP63200-AP63201-AP63203-AP63205.pdf
- JLC parts API (`selectSmtComponentList`, 2026-10-15): C22810 (15 Ω ±1 % ±100 ppm/K 100 mW),
  C105432 (S8550 PNP 120–200), C88980 (BLM18KG221SN1D 50 mΩ 2.2 A), C535146 (ESD103-B1-02EL 15 V 48 V).

## 8. Inferences (not measured, or not checkable against a primary source)

- **Limiter**: VCC_RF's minimum voltage and internal source impedance; S8550 VEB below 1 mA and its
  temperature coefficient (extrapolated from typical curves) and unit spread; AO3401A VGS at 30–50 mA,
  its gm and its capacitances at VDS ≈ −2.5 V; the loop-stability model and its phase margins; the
  turn-on and short-transient times; Q30's real RθJA on this layout.
- **Radio**: whether the E22 module adds its own pull-up on NRST or pull-ups/downs on TXEN/RXEN (the
  EBYTE basic circuit shows an external 100 kΩ NRST pull-up, which suggests none); the PA output at
  3.26 V.
- **Power**: AP63203 efficiency (0.85) and thermal resistance on this four-layer board; effective
  ceramic capacitance after DC-bias derating; the In2 plane resistance.
- **ESD**: the residual pulse reaching U30 RF_IN through ESD103, L30/C302 and R304, against an
  unpublished RF_IN ESD tolerance.
