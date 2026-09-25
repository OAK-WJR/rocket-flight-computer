# Rocket Flight Computer v1 — Frozen Design Document (FROZEN)

Frozen 2026-09-03. This file is the **only** input to schematic capture. Anything not written here does not exist; anything written here may not be "optimized" during drawing.
Optimization target (stated explicitly and repeatedly in the requirements): **the fewer parts the better, the more robust the better.** When in doubt, delete it.

> Superseded in part: the board is now 46 mm wide for a 54.66 mm ID airframe (see `GEOMETRY_REV_G.md`), and the design has become the single-board M3 (see `../STATUS.md`). The electrical rationale below still applies unless a later document overrides it.

---

## 1. Change summary

| Item | Original spec | Changed to | Reason (one line) | Part delta |
|---|---|---|---|---|
| Board size | 40 × 85 mm | **50 × 110 mm** | No terminal arrangement fits a 40 mm edge (B1/B2); a 105 mm long axis has zero margin and three known 1–2 mm creeps (C4) | 0 |
| Stackup copper | 4 layers, 2 oz | **4 layers, 1 oz outer / 1 oz inner** (inner upgraded from JLC's default 0.5 oz) | 2 oz pushes min track/space to 0.15–0.20 mm and annular ring to 0.254 mm; LQFP100 pad gap is only 0.20 mm → the MCU footprint fails DRC. A 1 oz, 40 mm inner plane already carries 17.3 A per IPC-2221 > 12 A peak | 0 |
| Minimum airframe | 54 mm | **75 mm (3 in), coupler ID 72.87 mm** | The largest 40 mm-wide rectangle inside a 50.72 mm ID is only 31.19 mm tall; the stack is 41.6 mm — geometrically impossible (B5) | 0 |
| Power/switch terminals | 5 × 2-pos 5.08 mm screw terminals | **1 × 4-pos (BAT+/BAT−/SW/SW) + 1 × 6-pos (ARM/ARM/PYRO1/PYRO1/PYRO2/PYRO2)** | Five terminals need 50.8–63.5 mm; a 40 mm edge minus M3 holes leaves 26 mm | −3 |
| 6-pos terminal location | — | **Must be on the long edge, y ≈ 1–34 mm** (cannot share the 50 mm end edge with the 4-pos) | 4-pos + 6-pos = 50.8–55.9 mm > 50 mm, geometrically impossible (C4) | 0 |
| Servo interface | 4 × 3-pos 3.5 mm screw terminals | **1 × 3×4 2.54 mm straight pin header + 3 mm zip-tie hole** | Four terminals need 42–46 mm; servos already come with JR/Futaba female plugs | −3 |
| Servo header orientation | C4 asked for right-angle | **Straight (vertical)** | Every right-angle 3×4 header on LCSC is 0 stock / 300–442 MOQ; C4's 26.91 mm is the naive bound for a 50 mm flat plate — the true chord-height bound for an 11 mm connector is 45.4 mm, so straight pins + harness (23.5 mm) have 22 mm to spare | 0 |
| Servo header location | Opposite the battery | **Moved to the battery end, same corner as the BAT terminal and bulk cap** | The whole 12 A loop stays inside one 25 × 40 mm corner; no switched current crosses the board (R4) | 0 |
| Servo PWM | TIM3 CH1–4 = PC6/PC7/PB0/PB1 | **TIM5 CH1–4 = PA0/PA1/PA2/PA3 (AF2, pins 22–25)** | PB1 = TT_u (4.0 V hard limit, the worst pin to wire off-board); PE9 = TT_ha makes a TIM1 scheme equally fatal; PA0–PA3 is the only 4-in-a-row, all-FT, single-side-escape group in the package (C1 ruling) | 0 |
| Servo series resistor | 100R | **220R, 0805 (the package size is an electrical requirement)** | Under a sustained chafe short the resistor dissipates 69–84 mW = 111–134 % of an 0402 rating; 0805 is 55–67 % | 0 |
| Servo signal protection | None | **+1 SRV05-4 four-channel clamp array** (MCU side); order = MCU pin – [10k pull-down + clamp] – 220R – connector | H743 FT pins have **no** clamp diode to VDD, so a 100R series resistor protects nothing (S1). The C1 ruling's "array on the connector side" contradicts its own 20 mA calculation; corrected to array on the inside | +1 |
| Servo signal reset state | Floating | **10k pull-down per channel (inside the 220R)** | During reset / hang / MCU death the servo line is a defined low, so servos don't slam at power-up | +4 |
| microSD + CD + pull-up + ESD | Present | **All deleted**; logging goes to W25Q128 + USB CDC readback | Frees SDMMC1 and 210 mm²; neither the QSPI map nor TIM5 touches PC8–PC12/PD2, so the deletion is reversible | −6 |
| LSE 32.768 kHz + 2 load caps | Present | **All deleted**; VBAT tied directly to VDD | No backup-domain requirement (DS12110 §3.5 explicitly allows VBAT = VDD) | −3 |
| LoRa E22-900M + u.FL + matching | On board, not fitted | **All deleted**; only a 1×11 2.54 mm pad row remains (not fitted) | LoRa/GPS coexistence is short by 22–30 dB: SAM-M10Q out-of-band immunity is 0 dBm at the antenna port, so a +22.3 dBm transmitter needs ≥ 22.3 dB antenna isolation, which a 110 mm board cannot give (D3) | −3 |
| IMU | ICM-42688-P | **ICM-45686 (C22459454)** | The 42688 is out of stock at LCSC (API stockCount 54 / canPresale **−519**, oversold); same-name parts on sale are Tokmas / HXY relabels (±2048 dps, 1.5 KB FIFO ≠ TDK's ±2000 dps, 2 KB). The 45686 shares the LGA-14 land pattern, 20-bit FIFO hard-scaled ±32 g @ 16384 LSB/g, ±4000 dps | 0 |
| High-g accelerometer ADXL375 | Present | **Deleted** (with 2 decoupling caps + 1 CS pull-up) | Of 228 H–K motors in production, **0/228 exceed 200 g** peak on this airframe; within the range actually reached, the 45686's ±32 g has 803× finer resolution and 45× lower noise; saturation is self-reported and can be flagged in firmware | −4 |
| IMU ODR | 1 kHz | **800 Hz (1.25 ms loop)** | The 45686 low-noise ODR steps are 6.4k/3.2k/1.6k/800/400/… — **no 1000 Hz and no 500 Hz** | 0 |
| Barometer | MS5611 | **Keep MS5611** (not BMP390/DPS310) | Those two stop at 300 hPa (≈ 9.2 km); the MS5611 goes to 10 mbar (≈ 31 km) | 0 |
| GPS UART | USART1 (PA9/PA10) | **USART6 = PC6 (TX) / PC7 (RX), AF7, FT_h** | The ROM bootloader arms every interface at once and checks USB **last**; a GPS NMEA/UBX stream would hijack USB DFU (M4) | 0 |
| GPS peripherals | Backup battery/isolation diode, RESET_N pull-up + cap, SAFEBOOT_N pull-up, supply ferrite | **All deleted**; V_BCKP / RESET_N / SAFEBOOT_N / TIMEPULSE / SDA / SCL all left floating | The u-blox integration manual explicitly allows a minimal UART design with these floating; a capacitor on RESET_N "triggers a reset at every power-up" (harmful part); a ferrite's DCR often exceeds u-blox's 0.2 Ω supply series-resistance limit | −6 |
| Sensor supply | "LC filter or 3.3 V LDO" | **LC only** (LDO branch and its 2 caps deleted) | A 3.3 V LDO after a 3.3 V buck has no dropout margin and only ~26 dB rejection in dropout; the LC gives 77 dB @ 1.1 MHz (B6) | −3 |
| Bulk capacitors | 3 × 1000 µF electrolytic (2 servo + 1 logic) | **2 × 470 µF / 25 V SMD polymer (same part number)** | The 16SVPF1000M named by C4 has only 31 pcs and is effectively unbuyable; 470 µF is enough (2.6 mV droop at 12 A, 12 mJ = 18.2 ms logic hold-up); height 20 mm → **10.0 mm**, which was what made the original airframe not fit | −1 |
| Reverse protection / load switch | Single P-FET reverse protection, BAT→SW | **Back-to-back dual P-FET common-source load switch** (Q1 drain = BAT+, common source, Q2 drain = RAW), 100k gate-source, SW terminal pulls the gate to ground through **10k** | Turning the P-FET into a load switch (S6) **silently deleted the reverse protection** (body diode points RAW→BAT+); back-to-back blocks both ways with 0 new part numbers and 0 new footprints. The SW terminal only carries 76 µA, never arcs, and gives any reed/magnetic switch unlimited life | +1 |
| SW pull-down resistor | S6's second 100k | **10k** | 100k/100k gives Vgs = −Vbat/2, only −3.0 V at the 6.0 V end, while the AON6403's worst-case Vgs(th) is −2.2 V; 100k/10k gives −7.64 V @ 8.4 V and −5.45 V @ 6.0 V, fully in the 3 mΩ region | 0 |
| TVS | SMBJ12A (unidirectional) across RAW | **SMBJ12CA (bidirectional) across BAT+/GND, right at the terminal** | A unidirectional TVS becomes a forward-biased diode when the battery is reversed = a dead short across an unfused 25C LiPo; the bidirectional part does not conduct. Same package, same price | 0 |
| Pyro gate resistor | 100R | **470R** | With 10 nF it gives a 5.0 µs turn-on constant (4000× faster than the 20 ms pulse) and collapses the Miller kick to 94 mV | 0 |
| Pyro gate pull-down | 10k | **1k** | If the gate lands on an AF0 pin with a reset pull-up, 10k gives 0.55–0.825 V, squarely inside the AO3400A's 0.4–1.1 V threshold band; 1k gives 0.065–0.106 V | 0 |
| Pyro Miller protection | None | **10 nF gate-source capacitor per channel** | When the ARM link is inserted the drain goes 0→8.4 V; the Crss integral (1.01 nC) into Ciss (750 pF) = ΔVgs 1.34 V, so the FET **partially turns on** (S4). With 10 nF: 95 mV | +2 |
| Continuity-sense divider | 10k / 3.3k | **10k / 1k** | After a bridgewire burns open, lead inductance drives the drain into avalanche (≈ 36 V for a 30 V part); 3.3k would put **8.93 V** onto an ADC pin limited to 4.0 V; 1k gives only 3.27 V (3.64 V worst case at 40 V) — **the ratio alone keeps the node inside FT's 7.3 V, so these two lines no longer need clamp channels**. Bridgewire current 0.632→0.764 mA, still 327× below the MJG no-fire current | 0 |
| Clamp array channel count | C1 ruling wanted 6 channels | **4 channels (SRV05-4)** | 6-channel parts are not buyable at JLC (SP3012-06 = 0 stock, MOQ 9); after the ratio change the continuity nodes need no clamp; and 6 channels would force two sense lines onto long detours | 0 (saves one more expensive part number) |
| ARM state sense | None | **+10k/1k divider → PC5** | Without it, "armed but no igniter" and "not armed" both read 0 V and cannot be told apart on the pad | +2 |
| Pyro bus supply | Raw BAT | **Must come after SW (RAW)** | Otherwise plugging the ARM plug with the board off energizes the pyro bus, and 8.4 V hits an ADC pin with VDD = 0 V through 10k (S3). Zero part cost | 0 |
| Arming branch fuse | On board | **Fuse built into the removable arming plug (5 A blade)** | Zero parts on the board (S10) | 0 |
| Indicators | RGB LED (3 GPIO) | **Red + yellow single-colour LEDs (2 GPIO), sharing the 220R part number** | Every 4-pin RGB on LCSC has InGaN green/blue with Vf 2.6–3.4 V; at Vf = 3.4 V the current from a 3.3 V rail through **any** resistor is 0 mA. Red (1.6–2.6 V) / yellow (1.8–2.4 V) are AlInGaP and light in every bin | 0 (1 part → 2, saves 1 resistor) |
| Buzzer driver | NPN + base resistor | **AO3400A (reusing the pyro part number) + 470R + 1k pull-down + 1N5819WS freewheel** | A MOSFET has no base current and no Vce(sat), and it saves 2 part numbers; the freewheel diode is mandatory: the AO3400A datasheet has **no EAS avalanche rating at all**, and driving a magnetic coil at 2.7 kHz means 2700 unrated avalanches per second at 24–122 mW | +2 |
| BOOT0 button | Tactile switch | **Deleted**; BOOT0 = pin 6 of the SWD header, next to pin 5 (3V3); a jumper selects DFU | A button nobody can reach cannot bounce the MCU into the ROM bootloader in flight; also one less compliant mechanical part at 30 g | −1 |
| Reset button / reset supervisor / external NRST pull-up | Present | **All deleted**; only the 100 nF on NRST remains | NRST has a permanent internal 30/40/50 kΩ pull-up; the H7's internal POR/BOR covers the whole 1.71–3.6 V range | −3 |
| USB protection | D+/D− TVS + VBUS TVS | **One USBLC6-2SC6** (includes a VBUS channel) | Three parts become one. "USB FS needs < 1 pF per line" is refuted by primary sources: ST itself rates this 3.5 pF-max part for "USB 2.0 up to 480 Mb/s", and we only run 12 Mb/s | −2 |
| USB D+ 1.5k pull-up | Present | **Deleted** | OTG_FS has a software-controlled internal pull-up; an external one breaks re-enumeration | −1 |
| 5 QSPI series resistors + 2 WP/HOLD pull-ups | Present | **All deleted** | 20 mm trace = 140 ps one way; 2 × tprop = 280 ps against ≥ 1 ns edges, electrically short with > 3× margin; ringing is controlled with OSPEEDR. In 4-bit mode WP/HOLD are driven data lines, and the NCS pull-up already guarantees deselection | −7 |
| Separate VREF+ decoupling | 1 µF + 100 nF | **VREF+ tied straight to VDDA, sharing one pair** | Absolute accuracy is recovered in firmware by reading VREFINT against VREFIN_CAL (0x1FF1E860), at zero cost | −2 |
| Buck feedback divider | Adjustable part | **AP63203 fixed 3.3 V version** | Zero feedback resistors, zero chance of setting the MCU supply wrong | −2 (vs adjustable) |
| Buck EN network | Divider / pull-up | **EN copper-tied to VIN** | EN absolute max is +35 V vs our 8.4 V; removes a megohm-impedance floating node | −1 |
| 0 Ω current-sense jumper | Present | **Deleted** | Both of its jobs (measuring logic-branch current, lifting the branch to find a short) are already provided by the D-log SS34 in the same branch; it would only add a solder joint in series with the MCU's only supply path | −1 |
| Spare I2C header + spare ADC header | 2 | **Merged into 1 × 1×5 pad row, not fitted in build 1** (including 2 unfitted 4.7k pull-up positions) | Unfitted parts cannot fail, be counterfeit, go out of stock or be soldered wrong | −2 |
| 2.54 mm single-row headers | SWD 1×4 / LoRa 1×7 / spare / pull-pin, one part number each | **All cut from one 1×40 break-away header** (SWD becomes 1×6) | 4 connector part numbers → 1 | −3 (part numbers) |
| Pull-pin | GPIO straight to the connector | **10k pull-up + 1k series** | A bare wire into an MCU pin is exactly the topology the C1 ruling condemned | +1 |
| VBUS sense | None | **VBUS → 100k → PD15** (the only net addition, removable) | Lets firmware keep the USB stack completely disabled with no cable, so OTG interrupts never disturb the 800 Hz control loop | +1 |
| MCU part number | STM32H743VIT6 / C114409 | **STM32H743VIT6TR / C5271084** (same die, tape and reel) | C114409 was 0 stock on the C3 ruling date with canPresale −292; tape and reel is what JLC's SMT line wants. **Note: C114409 was restocked with 573 pcs on 2026-09-03; this only changes the fallback order, it does not overturn the ruling** | 0 |
| Core clock | 480 MHz | **200 MHz, VOS2/VOS3** | Saves 145 mA / 0.48 W; load is < 5 % either way; the LQFP100 has only the LDO | 0 |

**Net part count: about 51 parts deleted, 14 added → net reduction of about 37.**
**Final fitted count: 101 soldered parts (excluding 4 unfitted positions), 39 part numbers.** Of these, 20 are JLCPCB Basic (no feeder fee, almost never out of stock) and 19 are Extended.

---

## 2. Frozen architecture

### 2.1 Board and stackup
- **Outline 50.0 × 110.0 mm**, corner radius R1.0. Four layers, 1.6 mm thick.
- **Stackup**: L1 signals + top ground pour / L2 **solid ground plane (must not be broken by signals)** / L3 signals (sensor nets run here to keep L2 an unbroken reference for the GPS antenna) / L4 power pours + a few signals. **1 oz outer, 1 oz inner.**
- **Single-sided assembly**: all SMT on top; bottom left empty (no second placement setup, ~500 mm² in reserve).
- **Mounting holes**: 4 × M3 (Ø3.2 mm, washer Ø7.0 → treated as a 7.5 mm square keep-out). The two battery-end holes are in the corners; **the two nose-end holes move to the long edges at the SAM-M10Q's longitudinal centreline (x = 3.5 mm, y ≈ 94/99)** — there is no room in the nose-end corners. The mounting rectangle is therefore 43 × ~95 mm, not corner-to-corner.
- **Long-axis zones (y = 0 at the battery end)**: 0–8.2 BAT 4-pos terminal + 3×4 servo header side by side (20.32 + 11.0 = 31.3 of 50); 8.2–20 bulk caps / load switch / TVS; 20–34 buck + inductor + LC; 34–46 USB-C (side) + pyro FETs + buzzer + LEDs + SWD; 46–68 LQFP100 + decoupling ring (22 wide) | W25Q128 (12) | 25 MHz crystal (8); 68–74 sensor cluster; 74–84 **u-blox 10 mm rear keep-out (kept as empty solid copper)**; 84–99.5 SAM-M10Q; 99.5–110 nose margin (10.5 mm — the slack C4 bought by going from 105 to 110).
- **The 6-pos ARM/PYRO terminal is fixed on the long edge, y ≈ 1–34**, taking 9.8 mm of width. Usable width in the y 8.2–34 zones is therefore **40.2 mm, not 50 mm**.
- **Height rules**: any top-side part ≤ 26.9 mm (naive rectangle bound); **any part inside the u-blox 10 mm ring ≤ 3 mm** (the rule is "parts taller than 3 mm must be ≥ 10 mm from the antenna", not "nothing may be placed" — 0402/0603, IMU 0.91 mm, barometer 1.0 mm, SOIC-8 flash 2.15 mm may enter the ring; terminals 10–14 mm, 470 µF 10.0 mm, inductors 3.0 mm, buzzer 3.3 mm and USB-C 3.16 mm may not). Tallest fitted part today = screw terminal, 14.0 mm.
- **Buck-to-sensor spacing**: buck at y 20–34, IMU at y ≈ 70, GPS antenna at y ≥ 84 → 36 mm / 52 mm, i.e. 2.4× and 3.5× the 15 mm rule.
- Minimum airframe **3 in / 75 mm** (coupler ID 72.87 mm). Radial clearance above the board top is 45.79 mm by the chord-height model.

### 2.2 Power tree (the one authoritative chain — wire exactly this)
```
BAT terminal (+) ──┬── SMBJ12CA ── GND        (TVS right at the terminal, loop < 10 mm)
                   │
                   └── Q1(AON6403) D ── S ──common source── S ── Q2(AON6403) D ── RAW
                        Gate node GATE_SW:  GATE_SW ──100k── common source (= BAT+ side)
                                            GATE_SW ──10k──  SW terminal ── (external reed/magnetic switch) ── GND
                        (SW open → Vgs = 0 → off and blocking both ways; SW closed → Vgs = −7.64 V @ 8.4 V / −5.45 V @ 6.0 V; SW carries only 76 µA)

RAW ──┬── servo header V+ ×4  +  470 µF/25 V polymer  +  2 × 22 µF/25 V 0805
      ├── ARM terminal pin A ──(external arming plug with 5 A fuse)── ARM terminal pin B ── PYRO_BUS
      ├── 100k ── VBAT_SENSE ── 47k ── GND        (10 nF on VBAT_SENSE; → PC4)
      └── D-log (SS34) ──┐
USB VBUS ── D-usb (SS34) ─┴── VLOGIC ──┬── 470 µF/25 V polymer (18.2 ms hold-up)
                                        └── AP63203 VIN (EN copper-tied to VIN) + 2 × 22 µF/25 V
                        AP63203: BST ─100 nF─ SW ; SW ── 4.7 µH (SWPA4030S4R7MT) ── 3V3 ── 2 × 22 µF/25 V
3V3 ──┬── MCU VDD×5 / VBAT (pin 6) / W25Q128 / USB / SWD header / pull-pin pull-up / all CS pull-ups
      └── L-LC 4.7 µH (same part number) ── 3V3A ── 2 × 22 µF/25 V ──┬── ICM-45686 VDD & VDDIO
                                                                     ├── MS5611 VDD
                                                                     ├── SAM-M10Q VCC & V_IO (+ local 22 µF)
                                                                     └── MCU VDDA (pin 21) = VREF+ (pin 20)
PYRO_BUS ──┬── 10k ── ARM_SENSE ── 1k ── GND      (→ PC5)
           ├── PYRO1 terminal A ── (igniter) ── PYRO1 terminal B ── Q_PY1 drain
           └── PYRO2 terminal A ── (igniter) ── PYRO2 terminal B ── Q_PY2 drain
```
Key numbers: FET pair RDS(on) ≈ 6 mΩ, 86 mV drop and 0.52 W per package at 12 A. Hot-plug inrush is limited by battery internal resistance to 99 A / τ = 83 µs; of the total 34.6 mJ only 2.3 mJ lands in the FETs — **the load switch is not a soft start; its value is moving the inrush off every contact**. Buck ripple current 0.388 A at 8.4 V input. LC filter: fc = 12.8 kHz, **77.4 dB** at 1.1 MHz, Q ≈ 4.8 (+13.6 dB peaking, fully covered by the AP63203's 4 ms internal soft start; 4 ms = 51 LC periods). Sensor rail IR drop < 5 mV.

### 2.3 Subsystems (2–5 lines each)
**MCU**: STM32H743VIT6TR, LQFP100, 200 MHz VOS2/VOS3. 25 MHz HSE (CL = 8 pF + 2 × 10 pF C0G), no LSE, VBAT copper-tied to VDD. 5 × 100 nF (one per VDD pin) + 1 × 4.7 µF; VCAP pins 48 and 73 get **one 2.2 µF each** (never shared); VDDA/VREF+ tied together share 1 µF + 100 nF and are **fed from 3V3A**. BOOT0 needs a 10k pull-down to ground (VIH is only 0.17·VDD + 0.6 = 1.16 V; floating means ROM bootloader), and **no capacitor on BOOT0**. NRST gets only 100 nF.
**Storage**: W25Q128JVSIQ, QUADSPI 4-bit, CLK = PB2 / NCS = PB6 / IO0 = PD11 / IO1 = PD12 / IO2 = PE2 / IO3 = PD13. NCS **must** have a 10k pull-up (PB6 is the ROM bootloader's I2C1_SCL and is actively configured). SDMMC1 (PC8–PC12, PD2) is **kept entirely unassigned**, so the microSD deletion is reversible.
**USB**: USB-C 16P, CC1/CC2 each with its own 5.1k pull-down (never shared), one USBLC6-2SC6 covering D+/D−/VBUS, 4.7 µF on VBUS, VBUS through 100k to PD15 for insertion detect. FS only, DFU + CDC log readback.
**Sensors**: ICM-45686 on SPI1 (PB3/PB4/PB5 + CS = PB7), DRDY → PE10 interrupt, 800 Hz. MS5611 on I2C1 (PB8/PB9, 4.7k pull-ups), OSR = 4096, PS pin to VDD selects I2C, CSB **hard-tied** to VDD or GND to set the address (never floating). SAM-M10Q on USART6, **everything except VCC/V_IO/TXD/RXD/GND floating**. All three on 3V3A.
**Pyro ×2**: RAW → ARM terminal (external fused arming plug) → PYRO_BUS → igniter → AO3400A low side. Gate: 470R series + 1k pull-down + 10 nF gate-source. Continuity sense: 10k/1k divider from drain to ADC. ARM state: 10k/1k divider from PYRO_BUS to ADC.
**Servos ×4**: TIM5 CH1–4 (PA0–PA3) → [10k pull-down + SRV05-4 channel] → 220R 0805 → 3×4 header signal pins. Header +V straight to RAW, GND to ground. **Each header pin is rated 3 A → every servo's stall current must be ≤ 3 A**; this is a hard servo-selection constraint, not a copper or terminal constraint.
**Indication / interaction**: red LED (PE3) + yellow LED (PE7), each through 220R; MLT-8530 buzzer driven by an AO3400A low side (PE6, 470R gate resistor + 1k pull-down + 1N5819WS freewheel); pull-pin (PD14) 10k pull-up + 1k series; SWD/DFU 1×6 header.

---

## 3. Complete pin table (STM32H743VIT6, LQFP100)
Pin numbers are from the LQFP100 column of DS12110 Rev 7 Table 8. I/O structure classes (FT/FT_a/FT_h/FT_ha/FT_fh/TT_a/TT_u) marked **[verified]** were checked against the primary source; the rest are marked **unverified** — unverified pins are used only for on-board signals and never taken off the board.
FT-class VIN limit = Min(VDD, VDDA, VDD33USB, VBAT) + 4.0 = **7.3 V**; TT class = **hard 4.0 V**. All FT/TT pins have IINJ = −5/+0 mA — **positive injection is not allowed at all**.

### 3.1 Power and dedicated pins
| Pin | Port/name | Function | Peripheral/AF | 5 V tolerant | State after reset | Notes |
|---|---|---|---|---|---|---|
| 6 | VBAT | Backup-domain supply | — | — | — | **Copper-tied directly to VDD** (allowed by DS12110 §3.5). Local 1 × 100 nF. No LSE, no coin cell |
| 10 | VSS | Ground | — | — | — | |
| 11 | VDD | 3V3 | — | — | — | 1 × 100 nF right at the pin |
| 12 | PH0 / OSC_IN | HSE input | — | FT | Floating input | 25 MHz crystal + 10 pF C0G to ground |
| 13 | PH1 / OSC_OUT | HSE output | — | FT | Floating input | 25 MHz crystal + 10 pF C0G to ground. **REXT not fitted**; a cuttable top-layer bridge is reserved |
| 14 | NRST | Reset | — | — | Internal pull-up 30/40/50k | Only 1 × 100 nF to ground. **No external pull-up, no reset IC, no button.** Routed to SWD header pin 4 |
| 19 | VSSA | Analog ground | — | — | — | Joined to main ground at one point or as a whole plane (whole plane in this design) |
| 20 | VREF+ | ADC reference | — | — | — | **Tied directly to VDDA (pin 21)**, sharing 1 µF + 100 nF |
| 21 | VDDA | Analog supply | — | — | — | **From 3V3A (after the LC filter)**, not the raw buck output |
| 26 | VSS | Ground | — | — | — | |
| 27 | VDD | 3V3 | — | — | — | 1 × 100 nF |
| 48 | VCAP1 | Core LDO | — | — | — | **Its own** 1 × 2.2 µF X5R, ESR < 100 mΩ, never shared with pin 73 |
| 49 | VSS | Ground | — | — | — | |
| 50 | VDD | 3V3 | — | — | — | 1 × 100 nF |
| 73 | VCAP2 | Core LDO | — | — | — | **Its own** 1 × 2.2 µF X5R |
| 74 | VSS | Ground | — | — | — | |
| 75 | VDD | 3V3 | — | — | — | 1 × 100 nF |
| 94 | BOOT0 | Boot select | — | Structure B | **No internal pull** | **10k pull-down to ground, mandatory.** VIH is only 1.16 V; floating means ROM bootloader. **No capacitor allowed.** Routed to SWD header pin 6; jumper to pin 5 (3V3) for DFU |
| 99 | VSS | Ground | — | — | — | |
| 100 | VDD | 3V3 | — | — | — | 1 × 100 nF. Five VDD pins → decoupling is **5 × 100 nF + 1 × 4.7 µF**, not 4 and not 6 |
| — | PDR_ON / VDD33USB / VDDLDO | — | — | — | — | **Not present on LQFP100**, bonded internally. Consequence: VDD minimum is 1.71 V (not 1.62 V); the USB transceiver runs straight from VDD — no separate rail, no extra capacitor |

### 3.2 Servo PWM — C1 ruling, four consecutive pins escaping on one side
| Pin | Port | Function | Peripheral/AF | 5 V tolerant | State after reset | Notes |
|---|---|---|---|---|---|---|
| 22 | PA0 | SERVO1 | TIM5_CH1 / **AF2** | **FT_a [verified]** | Floating (no reset pull) | In the very first boot instructions drive push-pull LOW, then switch to AF2 |
| 23 | PA1 | SERVO2 | TIM5_CH2 / **AF2** | **FT_ha [verified]** | Floating | Same |
| 24 | PA2 | SERVO3 | TIM5_CH3 / **AF2** | **FT_a [verified]** | Floating | ROM bootloader USART2_TX; on v0x91 it only becomes an output after detection, and a servo never transmits → never detected. Bench-only risk, and with SW open the servo rail is dead |
| 25 | PA3 | SERVO4 | TIM5_CH4 / **AF2** | **FT_ha [verified]** | Floating | ROM bootloader USART2_RX (input) |
| — | — | — | — | — | — | **Three mandatory register rules**: PUPDR[PA0..3] = 00 (enabling a pull voids the 7.3 V FT rating); OSPEEDR[PA0..3] = 00 (Low); drive push-pull low immediately at boot. TIM2 shares the only all-FT four-channel map with it and must **never have a channel assigned**; it is only a free-running microsecond timebase |

### 3.3 ADC
| Pin | Port | Function | Channel | 5 V tolerant | State after reset | Notes |
|---|---|---|---|---|---|---|
| 15 | PC0 | PYRO1_CONT continuity sense | ADC123_INP10 | **FT_a [verified]** | Floating | Must be FT: when a burnt bridgewire avalanches, the 10k/1k holds this node to 3.27 V (3.64 V worst case at 40 V). Normal reading 0.764 V |
| 16 | PC1 | PYRO2_CONT continuity sense | ADC123_INP11 | **FT_a [verified]** | Floating | Same. Source impedance 909 Ω |
| 32 | PC4 | VBAT_SENSE battery divider | ADC12_INP4 | TT_a, **suffix unverified** | Floating | On-board node, 100k/47k: 8.4 V → 2.686 V, 6.0 V → 1.918 V, USB only → 1.487 V (free "no battery" detection). 10 nF across it (498 Hz corner) |
| 33 | PC5 | ARM_SENSE arming state | ADC12_INP8 | TT_a, **suffix unverified** | Floating | 10k/1k from PYRO_BUS: armed reads 0.764 V, disarmed 0 V. **TT is acceptable**: even with the SMBJ clamping at 19.9 V this node is only 1.81 V |
| 34 | PB0 | Spare ADC (pitot) | ADC12_INP9 | **FT_a [verified]** | Floating | Off-board signal, must be FT. Goes to the 1×5 spare pads. **Not fitted in build 1** |

### 3.4 SPI1 — ICM-45686
| Pin | Port | Function | Peripheral/AF | 5 V tolerant | State after reset | Notes |
|---|---|---|---|---|---|---|
| 89 | PB3 | IMU_SCK | SPI1_SCK / AF5 | FT, **suffix unverified** | JTDO, no reset pull | Using JTDO disables JTAG; **SWD (PA13/PA14) is unaffected** |
| 90 | PB4 | IMU_MISO | SPI1_MISO / AF5 | FT, **suffix unverified** | **NJTRST, internal pull-up** | Harmless as a MISO input |
| 91 | PB5 | IMU_MOSI | SPI1_MOSI / AF5 | FT, **suffix unverified** | Floating | |
| 93 | PB7 | IMU_CS | GPIO output (software CS) | FT, **suffix unverified** | Floating | **10k pull-up to 3V3, mandatory (M6).** SPI mode 0 or 3, ≤ 24 MHz |
| 40 | PE10 | IMU_INT1 / DRDY | EXTI10 | **FT_ha [verified]** | Floating | 800 Hz data-ready interrupt. **The IWDG is fed only in this ISR.** EXTI lines are shared by pin number; this is the only interrupt source on the board, no conflict |

### 3.5 QUADSPI — W25Q128 (bound pin map, do not change)
| Pin | Port | Function | Peripheral/AF | 5 V tolerant | State after reset | Notes |
|---|---|---|---|---|---|---|
| 36 | PB2 | QSPI_CLK | QUADSPI_CLK / AF9 | **FT_ha [verified]** | Floating | The **only** QUADSPI_CLK on LQFP100 |
| 92 | PB6 | QSPI_NCS | QUADSPI_BK1_NCS / AF10 | FT_f, **suffix unverified** | Floating | **10k pull-up, non-negotiable**: PB6 is the ROM bootloader's I2C1_SCL and is actively configured (open drain, compatible with the pull-up) |
| 58 | PD11 | QSPI_IO0 | QUADSPI_BK1_IO0 / AF9 | FT, **suffix unverified** | Floating | |
| 59 | PD12 | QSPI_IO1 | QUADSPI_BK1_IO1 / AF9 | FT_fh, **suffix unverified** | Floating | |
| 1 | PE2 | QSPI_IO2 | QUADSPI_BK1_IO2 / AF9 | FT, **suffix unverified** | Floating | The **only** BK1_IO2 on LQFP100 |
| 60 | PD13 | QSPI_IO3 | QUADSPI_BK1_IO3 / AF9 | FT_fh, **suffix unverified** | Floating | **No series resistor, no WP/HOLD pull-up**; ringing controlled with OSPEEDR |

### 3.6 I2C1 — MS5611 (+ the unfitted spare header)
| Pin | Port | Function | Peripheral/AF | 5 V tolerant | State after reset | Notes |
|---|---|---|---|---|---|---|
| 95 | PB8 | I2C1_SCL | I2C1_SCL / AF4 | FT_f, **suffix unverified** | Floating | 4.7k pull-up to 3V3 (not 10k: 4.7k gives an 85 ns rise, 3.5× margin to the 300 ns Fast-mode limit) |
| 96 | PB9 | I2C1_SDA | I2C1_SDA / AF4 | FT_f, **suffix unverified** | Floating | 4.7k pull-up. PB9 is the ROM bootloader's I2C1_SDA (open drain), harmless |
| — | — | Spare-header I2C | **Shares I2C1** | — | — | **Ruling (low confidence, may be overturned)**: the spare header hangs on I2C1 to keep SDMMC1 intact and avoid bootloader pins. The cost is that a hung external pitot sensor also takes out the barometer. Mitigation = firmware must implement an I2C1 bus reset (9 clocks + STOP) and slave-timeout degradation. If that is unacceptable, use I2C3 = PA8 (SCL, pin 67, FT_fha) / PC9 (SDA, pin 66), permanently giving up SDMMC1_D1 |

### 3.7 USART6 — SAM-M10Q
| Pin | Port | Function | Peripheral/AF | 5 V tolerant | State after reset | Notes |
|---|---|---|---|---|---|---|
| 63 | PC6 | GPS_TX (MCU → GPS RXD) | USART6_TX / AF7 | **FT_h [verified]** | Floating | **Never use USART1 (PA9/PA10)**: the ROM bootloader arms every interface at once and checks USB last, so the GPS stream would hijack DFU |
| 64 | PC7 | GPS_RX (GPS TXD → MCU) | USART6_RX / AF7 | **FT_h [verified]** | Floating | Neither PC6 nor PC7 is in the H743 bootloader list of AN2606 Table 113 |

### 3.8 USB FS + SWD
| Pin | Port | Function | Peripheral/AF | 5 V tolerant | State after reset | Notes |
|---|---|---|---|---|---|---|
| 70 | PA11 | USB_DM | OTG_FS_DM / AF10 | FT_u, **suffix unverified** | Floating | Differential pair, 90 Ω, straight through the USBLC6-2SC6 (pins 1/6 and 3/4, no stubs) |
| 71 | PA12 | USB_DP | OTG_FS_DP / AF10 | FT_u, **suffix unverified** | Floating | **No external 1.5k pull-up** (internal, software-controlled) |
| 72 | PA13 | SWDIO | SYS_JTMS-SWDIO / AF0 | FT, **suffix unverified** | **Internal pull-up** | That is the SWD idle state; no external resistor needed |
| 76 | PA14 | SWCLK | SYS_JTCK-SWCLK / AF0 | FT, **suffix unverified** | **Internal pull-down** | Same |

### 3.9 Pyro, indication, I/O — reset state is safety-critical here
| Pin | Port | Function | Peripheral/AF | 5 V tolerant | State after reset | Notes |
|---|---|---|---|---|---|---|
| 3 | PE4 | **PYRO1_GATE** | GPIO push-pull | Unverified (on-board) | **Floating, no reset pull** ← critical | Chosen precisely because it is **not** in the AN2606 Table 113 bootloader list and **not** an AF0 pin with a reset pull-up. The external 1k pull-down gives only 0.065–0.106 V against the worst internal pull-up, far below the AO3400A's minimum Vgs(th) of 0.4 V. **Never** put a pyro gate on PA13/PA15/PB4 (AF0 internal pull-up) or PA6/PC11/PE13/PH13 (ROM bootloader push-pull outputs) |
| 4 | PE5 | **PYRO2_GATE** | GPIO push-pull | Unverified (on-board) | **Floating** ← critical | Same |
| 5 | PE6 | BUZZ_GATE | GPIO push-pull (software or timer square wave ~2.7 kHz) | Unverified (on-board) | Floating | 470R gate resistor + 1k pull-down |
| 2 | PE3 | LED_RED | GPIO push-pull | Unverified (on-board) | Floating | Through 220R to the LED anode, 3.2–7.7 mA |
| 37 | PE7 | LED_YEL | GPIO push-pull | Unverified (on-board) | Floating | Through 220R, 4.1–6.8 mA |
| 61 | PD14 | PULLPIN launch detect | GPIO input | **FT_h [verified]** | Floating | 10k pull-up to 3V3 + 1k series to the connector. Pin inserted reads 0.30 V (3.2× margin to VIL ≈ 0.95 V), pulled reads 3.30 V |
| 62 | PD15 | VBUS_SENSE | GPIO input | **FT_h [verified]** | Floating | A single 100k series resistor, not a divider: 5 V is legal on an FT pin (limit 7.3 V) and FT has no diode to VDD, so it reads logic 1 with zero injection. The 100k only limits fault current |

### 3.10 Reserved / explicitly forbidden
| Pins | Ports | Status | Reason |
|---|---|---|---|
| 65, 66, 78, 79, 80, 83 | PC8, PC9, PC10, PC11, PC12, PD2 | **Reserved, never assigned** | SDMMC1 4-bit has no alternate map on LQFP100; keeping it free is what makes the microSD deletion (D1) reversible. Also one of the decisive reasons the TIM3/TIM8 servo schemes were rejected |
| 28, 29, 30, 31 | PA4, PA5, PA6, PA7 | **No signal that matters at reset** | ROM bootloader SPI1 NSS/SCK/MISO/MOSI; PA6 is **driven push-pull**; PA4/PA5 additionally have IINJ = −0/0 mA (no injection in either direction) |
| 41, 42, 43, 44 | PE11, PE12, PE13, PE14 | Avoid | ROM bootloader SPI4 block; PE13 is a push-pull MISO |
| 35 | PB1 | **Forbidden** | TT_u, hard 4.0 V limit, cannot be protected by any external clamp |
| 39 | PE9 | **Forbidden** | TT_ha, same (this is exactly why the TIM1 servo scheme was fatal) |
| 68, 69 | PA9, PA10 | Avoid | ROM bootloader USART1 |
| 46, 47 | PB10, PB11 | Avoid | ROM bootloader USART3; PB10 is a push-pull output |
| 77 | PA15 | Avoid | AF0 with internal pull-up + bootloader SPI3 |
| 81, 82, 55, 56 | PD0, PD1, PD8, PD9 | **Keep free** | Free on the H743, but on the H723 they are ROM bootloader FDCAN1 pins (PD1 driven push-pull). Leaving them free means an emergency swap to the H723 does not silently break DFU |

**GPIO usage**: 35 assigned (servo 4 + pyro gates 2 + buzzer 1 + LEDs 2 + pull-pin 1 + VBUS 1 + ADC 5 + SPI1 4 + I2C1 2 + USART6 2 + QSPI 6 + USB 2 + SWD 2 + interrupt 1), 6 reserved for SDMMC1, about 41 free. Plenty of budget.

---

## 4. Complete BOM

Stock and unit prices were **looked up on 2026-09-02/03 via the JLCPCB parts API or LCSC pages** and are only for ordering priority, not a commitment.
Rows marked **"no substitutes"** must say "no substitutes" in the JLC BOM — these are part numbers where relabelled clones are rampant on LCSC.
### 4.1 MCU / digital
| Ref | Function | MPN | LCSC | Package | JLC class | Stock | Unit @100 | Risk |
|---|---|---|---|---|---|---|---|---|
| U1 | Main MCU STM32H743 Cortex-M7 2 MB/1 MB, 200 MHz VOS2/VOS3 | STM32H743VIT6TR | C5271084 | LQFP-100 (14×14) | Extended | 443 | $10.06 | Low stock. Fallback order: ① C5271084 ② **C114409** (same die, restocked 573 pcs on 2026-09-03, $9.41 — deeper and cheaper than the primary; this only changes the fallback order, it does not overturn the C3 ruling) ③ C730183 H743VGT6 (1 MB flash, same DS12110 Rev 7, zero changes) ④ C730141 H723VET6 in an emergency only |
| U2 | 128 Mbit QSPI NOR flight log | W25Q128JVSIQ | C97521 | SOIC-8 208 mil | **Basic** | 95,692 | $1.80 | None |
| Y1 | 25 MHz HSE crystal, CL = 8 pF | NX3225GA-25.000M-STD-CRG-2 | C1985619 | SMD3225-4P (pins 2/4 NC, grounded) | Extended | 5,787 | $0.193 | Low stock. **The only Basic 25 MHz 3225 part is C9006 with CL = 12 pF; its gm_crit at C0 = 7 pF reaches 1.781 mA/V, above ST's 1.5 mA/V limit → Basic would cost robustness here, not used** |
| D-USB | USB ESD (D+/D−/VBUS in one) | USBLC6-2SC6 | C7519 | SOT-23-6L | Extended | 39,025 | $0.142 | **No substitutes** (8+ non-ST clones on sale, including C2687116/C2827654/C5261088) |
| J1 | USB-C receptacle (USB 2.0 only), 4 through-hole shield legs | TYPE-C-31-M-12 | C165948 | SMD 16P + 4 THT | Extended | 306,635 | $0.146 | None |
| J2 / J-PULLPIN | SWD+DFU 1×6 and pull-pin 1×2, **cut from the same 1×40 break-away header** | 2.54 mm 1×40 straight header | C2337 | THT 2.54 mm 1×40 | Extended | 87,572 | $0.132/strip | None. The same strip also yields the **unfitted** spare 1×5 and LoRa 1×11 |

### 4.2 Board-wide shared passives (the main source of part-number convergence)
| Ref | Function | MPN | LCSC | Package | JLC class | Stock | Unit @100 | Qty |
|---|---|---|---|---|---|---|---|---|
| C ×15 | 100 nF: MCU VDD ×5, VDDA/VREF+, VBAT, NRST, flash VCC, IMU VDD, IMU VDDIO, MS5611 VDD, GPS VCC, pull-pin RC, buck BST | CL05B104KO5NNNC 100 nF/16 V/X7R/±10 % | C1525 | 0402 | **Basic** | 34,639,020 | $0.0051 | 15 |
| C ×2 | 10 pF C0G crystal load (**must be C0G/NP0**; X7R drifts the oscillator with temperature) | CL05C100JB5NNNC 10 pF/50 V/C0G/±5 % | C32949 | 0402 | **Basic** | 1,581,171 | $0.0062 | 2 |
| C ×3 | 10 nF: pyro gate-source ×2 (the key S4 part), battery divider filter ×1 | 0603B103K500NT 10 nF/50 V/X7R | C57112 | 0603 | **Basic** | 9,523,426 | $0.0108 | 3 |
| C ×1 | 1 µF: VDDA/VREF+ combined-node bulk | CL10A105KB8NNNC 1 µF/50 V/X5R | C15849 | 0603 | **Basic** | 9,509,798 | $0.0058 | 1 |
| C ×2 | 2.2 µF: **one each** for VCAP1 (pin 48) and VCAP2 (pin 73), ESR < 100 mΩ | CL10A225KO8NNNC 2.2 µF/16 V/X5R | C23630 | 0603 | **Basic** | 4,068,738 | $0.0192 | 2 |
| C ×2 | 4.7 µF: VDD bulk ×1, USB VBUS ×1 | CL10A475KO8NNNC 4.7 µF/16 V/X5R | C19666 | 0603 | **Basic** | 4,449,690 | $0.025 | 2 |
| C ×9 | **22 µF/25 V, one part number doing four jobs**: buck Cin ×2, buck Cout ×2, servo header HF ×2, sensor LC output ×2, GPS local ×1 | CL21A226MAQNNNE 22 µF/25 V/X5R | C45783 | 0805 | **Basic** | 5,354,115 | $0.2572 | 9 |
| C-BULK ×2 | 470 µF/25 V aluminium polymer: servo bus ×1, logic hold-up ×1 (same part number) | MA25V470M8×10 (25 mΩ, 4.1 Arms) | C46550466 | SMD V-chip Ø8.0 × H10.0 | Extended | 142,265 | $0.2218 | 2 |
| R ×13 | 10k: BOOT0 pull-down, QSPI_NCS pull-up, IMU_CS pull-up, pull-pin pull-up, continuity/ARM divider upper arms ×3, servo signal pull-downs ×4, buzzer gate pull-down, SW gate pull | 0402WGF1002TCE 10k/1 % | C25744 | 0402 | **Basic** | 30,226,474 | $0.0031 | 13 |
| R ×6 | 1k: pyro gate pull-downs ×2, divider lower arms ×3, pull-pin series ×1 | 0402WGF1001TCE 1k/1 % | C11702 | 0402 | **Basic** | 12,442,809 | $0.0031 | 6 |
| R ×3 | 100k: FET gate-source, battery divider upper arm, VBUS sense series | 0402WGF1003TCE 100k/1 % | C25741 | 0402 | **Basic** | 13,184,469 | $0.0028 | 3 |
| R ×1 | 47k: battery divider lower arm | 0402WGF4702TCE 47k/1 % | C25792 | 0402 | **Basic** | 6,460,943 | $0.0029 | 1 |
| R ×2 | 5.1k: USB-C CC1 and CC2 **each with its own** (sharing one breaks orientation detection — the most common USB-C mistake) | 0402WGF5101TCE 5.1k/1 % | C25905 | 0402 | **Basic** | 8,220,351 | $0.0026 | 2 |
| R ×2 (+2 unfitted) | 4.7k: I2C1 pull-ups; spare-header I2C pull-up positions unfitted | 0402WGF4701TCE 4.7k/1 % | C25900 | 0402 | **Basic** | 20,101,997 | $0.0029 | 2 |
| R ×6 | **220R, must be 0805**: servo series ×4 (sustained 69–84 mW in a chafe fault = 111–134 % of an 0402 rating), LED current limit ×2 | 0805W8F2200T5E 220R/1 %/125 mW | C17557 | **0805** | **Basic** | 1,266,334 | $0.0058 | 6 |
| R ×3 | 470R: pyro gate resistors ×2, buzzer gate resistor ×1 | 0603WAF4700T5E 470R/1 % | C23179 | 0603 | **Basic** | 6,369,689 | $0.0028 | 3 |

### 4.3 Power
| Ref | Function | MPN | LCSC | Package | JLC class | Stock | Unit @100 | Risk |
|---|---|---|---|---|---|---|---|---|
| Q1, Q2 | Back-to-back common-source P-FETs: load switch + reverse blocking | AON6403 | C2760089 | DFN5×6-8 (S1/2/3, G4, D5/6/7/8) | Extended | 1,682 | $0.5111 ×2 | **Low stock + no substitutes.** 3.5 mΩ typ / 4.3 mΩ max @ Vgs = −4.5 V, meets S9. Fallback AON6407 C13899 (14,761 pcs, same package and pinout, no −4.5 V rating, ~5.5 mΩ at the actual −7.6 V). **Alpha & Omega brand only** (C5148668/C17702953/C7568979/C7603355/C54529452/C42412354 are all relabels; one claims 2.8 mΩ @ 10 V while the original maker only states < 4.5 mΩ — at least one datasheet is invented) |
| TVS1 | Bidirectional TVS across BAT+/GND, right at the terminal | SMBJ12CA (600 W, Vrwm 12 V, Vbr 13.3 V, Vc 19.9 V @ 30.2 A) | C83849 | SMB / DO-214AA | Extended | 29,699 | $0.1024 | None. Fallback C78407 (153,680 pcs, same ratings, half price) |
| D-LOG, D-USB2 | Diode OR: RAW→VLOGIC, VBUS→VLOGIC | SS34 (3 A/40 V, Vf ≈ 0.35 V @ 300 mA) | C8678 | SMA / DO-214AC | **Basic** | 5,404,194 | $0.0348 ×2 | None. 40 V is needed to block the 19.9 V TVS clamp level |
| U-BUCK | 3.3 V / 2 A synchronous buck, **fixed-output version**, 3.8–32 V input, 1.1 MHz, 4 ms internal soft start | AP63203WU-7 | C780769 | TSOT-23-6 | Extended | 17,723 | $0.8972 | **No substitutes** (Diodes Inc only). EN copper-tied to VIN (EN abs max +35 V). No true drop-in exists: every equivalent is adjustable and needs +2 resistors |
| L1, L2 | **One part number, two places**: buck output inductor + sensor LC series inductor | SWPA4030S4R7MT 4.7 µH ±20 %, shielded, DCR 78 mΩ, Isat 3.2 A / Irms 2 A | C57269 | SMD 4.0 × 4.0 × 3.0 | Extended | 56,383 | $0.0742 ×2 | **Maximum DCR unverified** (LCSC lists only typ 78 mΩ; Sunlord series tolerance is usually ±20–30 % → worst case ~95–100 mΩ, still inside u-blox's 0.2 Ω limit; the conclusion stands but margin drops from 2.6× to ~2×). Chosen because the u-blox integration manual strictly requires "supply-line series resistance no more than 0.2 Ω" — which rules out ferrite beads and most 10 µH parts. If bench testing shows buck saturation, switch to C48496 (5×5, 8,364 pcs) or C354606 (CENKER 5×5, published Isat/DCR) |

### 4.4 Sensors
| Ref | Function | MPN | LCSC | Package | JLC class | Stock | Unit @100 | Risk |
|---|---|---|---|---|---|---|---|---|
| U-IMU | 6-axis IMU, 20-bit FIFO hard-scaled ±32 g @ 16384 LSB/g, ±4000 dps @ 131.1 LSB/dps | ICM-45686 | C22459454 | LGA-14 2.5 × 3.0 × 0.81, 0.5 mm pitch | Extended | 5,496 (fell from 6,519 in one day) | $8.112 | **No substitutes.** Land drawn to D = 2.5 / E = 3.0 / W = 0.25 / L = 0.475 / e = 0.5 / D1 = 1.5 / E1 = 1.0 / SD = 0.25, **pins 2, 3, 7, 10, 11 all grounded** — so the same land also fits the ICM-42688-P; if TDK restocks, only firmware changes. ICM-42686-P (C19191783) is **not buyable** (0 stock, MOQ 442) |
| U-BARO | 24-bit barometer, 10–1200 mbar (≈ 31 km), ≈ 0.135 m RMS at OSR 4096 | MS561101BA03-50 | C15639 | QFN-8 5.0 × 3.0 × 1.0 | Extended | 3,911 | $5.0246 | **No substitutes + counterfeits common.** PS pin to VDD selects I2C; CSB **hard-tied** to VDD or GND sets the address, **never floating**. Zero-cost anti-counterfeit: verify the PROM CRC-4 at power-up and refuse to arm on failure — this also catches cracked dies and cold joints. Cost-hedge fallback MS560702BA03-50 C97627 (3,281 pcs, $2.62, **same land**, but half the resolution and a different PROM compensation formula — not a zero-firmware change) |
| U-GPS | GNSS module with 15 × 15 mm patch antenna | SAM-M10Q-00B | C5443880 | LGA-20 15.5 × 15.5 × 6.3 | Extended | **51** | $22.55 (no volume price) | **The most fragile and most expensive line on the board.** V_BCKP / RESET_N / SAFEBOOT_N / TIMEPULSE / SDA / SCL **all floating**. If out of stock: SAM-M8Q-0 C5447387 (142 pcs, $11.98); u-blox documents it as pin-to-pin compatible, **zero copper changes** (cost: 2.5 m vs 1.5 m accuracy, no BeiDou, 67 mA vs 10 mA) |

### 4.5 Pyro / servo / indication / connectors
| Ref | Function | MPN | LCSC | Package | JLC class | Stock | Unit @100 | Risk |
|---|---|---|---|---|---|---|---|---|
| Q-PY1, Q-PY2, Q-BUZ | Pyro low side ×2 + buzzer low side ×1 (third use of the same part number) | AO3400A | C20917 | SOT-23 | **Basic** | 1,030,807 | $0.0677 ×3 | **No substitutes — Alpha & Omega (C20917) only.** All of the S4 Miller calculations depend on its Vgs(th) of 0.4–1.1 V and Crss of 75 pF; a different die voids them, and this is the one circuit on the board that must never self-fire. **Do not raise BVDSS**: avalanche is the drain's only clamp; a 60 V part makes the inductive spike at bridgewire opening higher and worsens S2 |
| D-CLAMP | 4-channel rail clamp array, for the 4 servo signals only | SRV05-4.TCT | C13612 | SOT-23-6L | Extended | 69,877 | $0.1341 | None. **Pin 5 straight to 3V3**; clamp level = VCC + VF = 4.1–4.5 V, 1.62× margin to FT's 7.3 V. Sustained fault current 17.7–19.5 mA per line, only 22 mW each, tolerable indefinitely (a pure transient ESD part cannot do that) |
| D-BUZZ | Buzzer coil freewheel | 1N5819WS (1 A/40 V) | C191023 | SOD-323 | **Basic** | 6,001,571 | $0.0137 | None. **Mandatory**: the AO3400A datasheet gives no EAS at all, and driving a magnetic coil at 2.7 kHz = 2700 unrated avalanches per second |
| LED1 | Red status LED | NCD0805R1 (Vf 1.6–2.6 V) | C84256 | 0805 | **Basic** | 6,361,703 | $0.0134 | None |
| LED2 | Yellow status LED (armed/safe distinguishable at a glance) | KT-0805Y (Vf 1.8–2.4 V) | C2296 | 0805 | **Basic** | 634,369 | $0.0153 | None |
| LS1 | Electromagnetic buzzer, **passive, externally driven**, 2.7 kHz / 80 dB / 95 mA / 3.3 mm tall | MLT-8530 | C94599 | SMD 8.5 × 8.5 × 3.3 | Extended | 76,200 | $0.1628 | None. **The narrowest temperature range on the board: −20…+70 °C** (terminals −40/+105, resistors −55/+155, FETs −55/+150). It is the only status channel that works inside a closed airframe — the LEDs are usually invisible in flight configuration |
| J-BAT | 4-pos screw terminal: BAT+/BAT−/SW/SW, 5.08 mm, 16 A/300 V, M2.5 screws, −40…+105 °C, 14 mm tall | DB128V-5.08-4P-GN-S | C2915641 | 5.08 mm fixed screw terminal, THT | Extended | 103,677 | $0.336 | **Body length unverified** (LCSC only gives the 14 mm height). The KF128-5.08-4P (C5296490) named in the C4 ruling is **0 stock + MOQ 300, not buyable**, hence this series. Layout uses the conservative bound 5.08N + 2.54 = 22.86 mm; the end-edge budget 22.86 + 11.0 = 33.86 of 50 mm must hold |
| J-ARM | 6-pos screw terminal: ARM/ARM/PYRO1/PYRO1/PYRO2/PYRO2, same series | DB128V-5.08-6P-GN-S | C2915642 | Same | Extended | 49,168 | $0.4267 | Same. **Must go on the long edge**, cannot share the 50 mm end edge with J-BAT |
| J-SERVO | 3×4 servo header (signal / +RAW / GND rows), **straight pins** | HX PZ2.54-3×4P ZZ | C32713291 | 2.54 mm 3 rows × 4 columns THT gold square pins | Extended | 10,374 | $0.1482 | **3 A per pin → servo stall must be ≤ 3 A.** LCSC has no right-angle 3×4 on sale (all 7 listings are 0-stock JLC placeholders) |

### 4.6 Not fitted (pads/holes only)
| Ref | Content | Notes |
|---|---|---|
| J-LORA | 1×11 2.54 mm pads: SPI2 ×4 + BUSY + DIO1 + NRST + TXEN + RXEN + 3V3 + GND | No LoRa in build 1. 11 pins rather than D3's 7, because the E22-900M RF switch needs TXEN/RXEN; a 7-pin escape would be unusable |
| J-SPARE | 1×5 2.54 mm pads: 3V3 / GND / SCL / SDA / ADC (PB0) | Merges the original spec's "spare I2C" and "pitot ADC header" into one |
| R-SPARE ×2 | 4.7k pull-up positions for the spare-header I2C | Not fitted |

### 4.7 Totals
- **Part numbers (distinct lines) = 39**; **20 are JLCPCB Basic** (no feeder fee, effectively no stock risk), 19 Extended (3 of them through-hole, which take no SMT feeder slot).
- **Fitted parts = 101** (plus 4 unfitted positions).
- Through-hole: 4 connectors (4-pos terminal, 6-pos terminal, 3×4 header, SWD/pull-pin header) + the USB-C's 4 shield legs = about 30 THT joints. JLCPCB standard SMT **does not place through-hole parts**; it needs the extra THT service or hand soldering — at 1–5 boards hand soldering is faster and cheaper.
- Component cost about $60–65 per board @ qty 100, of which SAM-M10Q is $22.55, MCU $10.06, IMU $8.11, barometer $5.02 — four parts make up 75 %.

---

## 5. Netlist outline

This is what the drawing agent actually connects. Any connection not listed here is not made.

### 5.1 Power nets
| Net | From | To | Notes |
|---|---|---|---|
| BAT+ | J-BAT pin 1 | Q1 drain (D5–D8), TVS1 anode, one end of R-GS (100k) | Terminal-to-TVS loop < 10 mm |
| GND | J-BAT pin 2 | Whole-board ground plane L2 | One ground net, not split |
| FET_S | Q1 source (S1–S3) | Q2 source (S1–S3), other end of R-GS | Common-source node, connects only these three |
| GATE_SW | Q1 gate (G4) | Q2 gate (G4), R-GS, R-SW (10k) | Both FET gates tied together |
| SW_TERM | Other end of R-SW (10k) | J-BAT pins 3 and 4 | Both SW positions paralleled on one net; the external reed/magnetic switch goes across SW_TERM and GND. Carries only 76 µA |
| RAW | Q2 drain (D5–D8) | Servo header V+ row ×4, C-BULK1 (470 µF)+, 2 × 22 µF, J-ARM pin 1, R-DIV-HI (100k), D-LOG anode | 12 A main bus, copper ≥ 6.1 mm equivalent |
| VLOGIC | D-LOG cathode | D-USB2 cathode, C-BULK2 (470 µF)+, AP63203 VIN, AP63203 EN, 2 × 22 µF | Diode-OR output. EN on the same net as VIN |
| VBUS | J1 USB-C VBUS (A4/A9/B4/B9 all paralleled) | D-USB2 anode, USBLC6 pin 5, C 4.7 µF, R-VBUS (100k) | |
| SW_NODE | AP63203 SW | One end of L1 (4.7 µH), one end of C-BST (100 nF) | Buck switch node, minimize its area |
| BST | AP63203 BST | Other end of C-BST | |
| 3V3 | Other end of L1 | 2 × 22 µF, MCU VDD ×5, MCU VBAT (pin 6), W25Q128 VCC, (USBLC6 unused), top ends of all 10k/4.7k pull-ups, SRV05-4 pin 5, (LEDs unrelated), one end of L2 (4.7 µH), SWD header pin 5 | |
| 3V3A | Other end of L2 | 2 × 22 µF, MCU VDDA (pin 21) = VREF+ (pin 20), ICM-45686 VDD (pin 8) + VDDIO (pin 5), MS5611 VDD, SAM-M10Q VCC + V_IO (+ local 22 µF) | **VDDA and VREF+ are the same net** |
| PYRO_BUS | J-ARM pin 2 | J-ARM pin 3, J-ARM pin 5, R-ARMSENSE-HI (10k) | The arming plug (with 5 A fuse) goes across J-ARM pin 1 ↔ pin 2 |

### 5.2 Pyro chain (each channel fully symmetric)
| Net | From | To | Notes |
|---|---|---|---|
| PYRO1_OUT | J-ARM pin 4 | Q-PY1 drain | Igniter connects between J-ARM pin 3 (PYRO_BUS) and pin 4 |
| PYRO1_GATE_N | MCU PE4 (pin 3) | One end of R-GATE1 (470R) | |
| PYRO1_GATE | Other end of R-GATE1 | Q-PY1 gate, one end of R-PD1 (1k), one end of C-GS1 (10 nF) | |
| — | Other ends of R-PD1 and C-GS1 | GND / Q-PY1 source | Both the 1k pull-down and the 10 nF must return to the **source**, not to a remote ground |
| PYRO1_CONT | Q-PY1 drain → R-CONT1-HI (10k) → node | node → R-CONT1-LO (1k) → GND; node → MCU PC0 (pin 15) | Normal 0.764 V, avalanche worst case 3.64 V |
| PYRO2_* | Same, J-ARM pins 5/6, MCU PE5 (pin 4), MCU PC1 (pin 16) | | Exact mirror |
| ARM_SENSE | PYRO_BUS → 10k → node | node → 1k → GND; node → MCU PC5 (pin 33) | Distinguishes "armed, no igniter" from "not armed" |

### 5.3 Servo chain (×4, fully symmetric)
| Net | From | To | Notes |
|---|---|---|---|
| SERVOn_MCU | MCU PA0/PA1/PA2/PA3 (pins 22–25) | One end of R-PDn (10k), SRV05-4 channel n, one end of R-SERn (220R) | **Order must not be reversed**: pull-down and clamp on the MCU side, 220R on the outside |
| — | Other end of R-PDn | GND | Servo line is a defined low during reset/hang |
| SERVOn_OUT | Other end of R-SERn (220R) | J-SERVO signal row pin n | The 220R sets the fault current; sustained dissipation 69–84 mW |
| SRV05 pin 5 | 3V3 | | Clamps to 4.1–4.5 V |
| SRV05 GND | GND | | |
| J-SERVO +V row ×4 | RAW | | All paralleled |
| J-SERVO GND row ×4 | GND | | All paralleled |

### 5.4 Sensors and buses
| Net | From | To | Notes |
|---|---|---|---|
| SPI1_SCK | MCU PB3 (pin 89) | ICM-45686 pin 13 (AP_SCLK) | |
| SPI1_MISO | MCU PB4 (pin 90) | ICM-45686 pin 1 (AP_SDO) | Firmware must disable the 45686's internal pull-up: pads_ap_sdo_pe_trim_d2a[0] = 0 |
| SPI1_MOSI | MCU PB5 (pin 91) | ICM-45686 pin 14 (AP_SDI) | |
| IMU_CS | MCU PB7 (pin 93) | ICM-45686 pin 12 (AP_CS), 10k pull-up to 3V3 | |
| IMU_INT1 | ICM-45686 pin 4 (INT1) | MCU PE10 (pin 40) | 800 Hz DRDY; **the only IWDG feed point** |
| IMU unused pins | Pins 2, 3, 7, 10, 11 | GND | So the same land also fits the ICM-42688-P |
| IMU pin 9 (INT2/FSYNC/CLKIN) | Floating | | |
| I2C1_SCL | MCU PB8 (pin 95) | MS5611 SCLK, 4.7k → 3V3, J-SPARE (unfitted) | |
| I2C1_SDA | MCU PB9 (pin 96) | MS5611 SDA, 4.7k → 3V3, J-SPARE (unfitted) | |
| MS5611 PS | VDD | | Selects I2C mode |
| MS5611 CSB | **Hard-tied to VDD or GND** | | Sets the I2C address; **never floating** |
| GPS_TX | MCU PC6 (pin 63) | SAM-M10Q RXD | |
| GPS_RX | MCU PC7 (pin 64) | SAM-M10Q TXD | |
| Other SAM-M10Q pins | V_BCKP / RESET_N / SAFEBOOT_N / TIMEPULSE / SDA / SCL | **All floating** | A capacitor on RESET_N triggers a reset at every power-up; TIMEPULSE is internally connected to SAFEBOOT_N through 1 kΩ, and if it is pulled low at boot the module enters safeboot |

### 5.5 QSPI / USB / debug
| Net | From | To | Notes |
|---|---|---|---|
| QSPI_CLK | MCU PB2 (pin 36) | W25Q128 CLK (pin 6) | No series resistor |
| QSPI_NCS | MCU PB6 (pin 92) | W25Q128 /CS (pin 1), **10k pull-up to 3V3** | Mandatory |
| QSPI_IO0 | MCU PD11 (pin 58) | W25Q128 DI/IO0 (pin 5) | |
| QSPI_IO1 | MCU PD12 (pin 59) | W25Q128 DO/IO1 (pin 2) | |
| QSPI_IO2 | MCU PE2 (pin 1) | W25Q128 /WP/IO2 (pin 3) | No pull-up |
| QSPI_IO3 | MCU PD13 (pin 60) | W25Q128 /HOLD/IO3 (pin 7) | No pull-up |
| — | W25Q128 VCC (pin 8) = 3V3 + 100 nF, GND (pin 4) = GND | | |
| USB_DM | J1 A7 + B7 | Straight through USBLC6 pins 1/6 → MCU PA11 (pin 70) | 90 Ω differential, no stubs |
| USB_DP | J1 A6 + B6 | Straight through USBLC6 pins 3/4 → MCU PA12 (pin 71) | |
| CC1 | J1 A5 | 5.1k → GND | Its own resistor |
| CC2 | J1 B5 | 5.1k → GND | Its own resistor |
| USBLC6 pin 2 | GND | | |
| VBUS_SENSE | VBUS → 100k → MCU PD15 (pin 62) | | Single resistor, not a divider |
| SWDIO / SWCLK / NRST / 3V3 / BOOT0 / GND | MCU PA13 (72) / PA14 (76) / pin 14 / 3V3 / pin 94 / GND | J2 1×6: **1 = GND, 2 = SWCLK, 3 = SWDIO, 4 = NRST, 5 = 3V3, 6 = BOOT0** | Pin order must be printed on silkscreen. Jumper on 5–6 = enter DFU |
| BOOT0 | MCU pin 94 | 10k → GND, J2 pin 6 | No capacitor |
| PULLPIN | MCU PD14 (pin 61) | 10k → 3V3, 1k → J-PULLPIN pin 1 | J-PULLPIN pin 2 = GND |
| LED_RED | MCU PE3 (pin 2) | 220R → LED1 anode, LED1 cathode → GND | |
| LED_YEL | MCU PE7 (pin 37) | 220R → LED2 anode, LED2 cathode → GND | |
| BUZZ_GATE | MCU PE6 (pin 5) | 470R → Q-BUZ gate; gate → 1k → GND | |
| BUZZ_OUT | Q-BUZ drain | One end of LS1, D-BUZZ anode | Other end of LS1 = 3V3; D-BUZZ cathode = 3V3 |
| VBAT_SENSE | RAW → 100k → node | node → 47k → GND; node → 10 nF → GND; node → MCU PC4 (pin 32) | |
| HSE | MCU PH0 (12) / PH1 (13) | Y1 pin 1 / pin 3; each through 10 pF to GND; Y1 pins 2/4 to GND | |

---

## 6. Suggested schematic blocks (module frames + capture order)

Draw in this order, one module rectangle per block; later blocks only reference power net names already defined by earlier blocks.

1. **PWR-IN battery input and load switch** — J-BAT, TVS1, Q1/Q2, R-GS, R-SW, C-BULK1, servo 22 µF ×2. Contains the start of the RAW bus. Once this block is drawn, RAW/GND/SW_TERM are fixed.
2. **PWR-3V3 buck and filter** — D-LOG, D-USB2, C-BULK2, AP63203 + C-BST + Cin ×2 + L1 + Cout ×2, L2 + 22 µF ×2 (3V3A), battery divider 100k/47k/10 nF.
3. **MCU-CORE** — U1 + 5 × 100 nF + 4.7 µF + 2 × 2.2 µF (VCAPs drawn separately) + VDDA/VREF+ 1 µF + 100 nF + VBAT 100 nF + NRST 100 nF + BOOT0 10k + Y1 and two 10 pF. **Arrange the LQFP100 symbol by port, with the pin 1–25 side at the bottom of the frame** (matching the battery-end side on the PCB).
4. **DEBUG-USB** — J2 1×6 header, J1 USB-C, USBLC6, 2 × 5.1k, VBUS 4.7 µF, R-VBUS 100k.
5. **STORAGE** — W25Q128 + 100 nF + NCS 10k pull-up.
6. **SENSE-IMU-BARO** — ICM-45686 + 2 × 100 nF + CS 10k; MS5611 + 100 nF + 2 × 4.7k.
7. **SENSE-GPS** — SAM-M10Q + 100 nF + 22 µF; draw the other pins with explicit NC markers (do not leave them implicitly floating — they are easy to mis-wire).
8. **PYRO** — J-ARM, ARM_SENSE divider, two exactly mirrored AO3400A + 470R + 1k + 10 nF + 10k/1k sense dividers. **Place the two channels symmetrically one above the other for visual checking.**
9. **SERVO** — J-SERVO 3×4, SRV05-4, 4 × 220R, 4 × 10k pull-downs.
10. **IO-INDICATE** — LED1/LED2 + 2 × 220R, Q-BUZ + LS1 + D-BUZZ + 470R + 1k, J-PULLPIN + 10k + 1k.
11. **DNP-FOOTPRINTS** — J-LORA 1×11, J-SPARE 1×5 + 2 × 4.7k, all marked DNP. A separate block so they are never confused with fitted parts.

---

## 7. Constraints firmware must obey

Each of these replaces hardware or compensates for deleted hardware. They are not suggestions.

1. **The IWDG may only be fed in the IMU DRDY ISR**, timeout ≥ 2 s, ODR = 800 Hz (1.25 ms), 1600× margin. **Launch detection, apogee detection and fire decisions all run in ISR context.** The chain "main loop writes storage → main loop feeds the watchdog" is forbidden: SD/flash writes can block for a long time, and that is a lose-the-rocket chain.
2. **The first boot instructions**: set PA0–PA3 as push-pull outputs driven low, **then** switch to AF2/TIM5. PUPDR[PA0..3] = 00 (a pull voids the 7.3 V FT rating), OSPEEDR[PA0..3] = 00 (low speed). Drive PE4/PE5 (pyro gates) low equally early.
3. **Servo PWM**: TIM5, edge-aligned PWM mode 1, all four rising together at CNT = 0, CCRx = pulse width. **No phase staggering** (the servos' internal H-bridges free-run at 1–20 kHz, not locked to the 333 Hz command frame, so staggering command edges does not change load current). **Do not rely on TIM5's 32-bit counter** (16 bits still gives 20,000 steps in a 333 Hz frame, 5–60× finer than any servo's 3–5 µs dead band). TIM2 is permanently reserved as a free-running microsecond timebase; no channels assigned.
4. **Pyro**: pulse ≤ 20 ms, only one channel on at any time; default DISARM after power-up and reset; **never automatically re-arm after a reset** (requires an explicit ground command or a definite flight-phase condition). Before firing, read ARM_SENSE to confirm armed and PYRO*_CONT to confirm the bridgewire is present. (Superseded in flight by FMEA_REDUNDANCY.md F-10: in flight these readings are logged and annunciated only and never veto a fire command.)
5. **Logging**: records ≤ 64 bytes; 25–50 Hz on the pad, 500 Hz after launch detection; **never erase inline** (full-chip erase only after power-up on an explicit command). 16 MB at 64 B / 500 Hz is 524 s of continuous full-rate logging, enough for any H–K flight. The W25Q256 is **not** a drop-in for SOIC-8 208 mil (LCSC only has WSON-8 or SOIC-16); do not make design decisions on the assumption that it is "upgradeable".
6. **ICM-45686**: WHO_AM_I is register **0x72, expected 0xE9** (not the 42688's 0x75/0x47), and register access is **IREG indirect** (not BANK_SEL). Configure the **20-bit FIFO packet format** to get ±32 g @ 16384 LSB/g and ±4000 dps @ 131.1 LSB/dps at once; on the 16-bit UI path set ACCEL_UI_FS_SEL = 0 and GYRO_UI_FS_SEL = 0. **±32 g full-scale saturation flagging is mandatory**: inside a flagged interval stop trusting integrated acceleration for velocity, switch to the barometer or hold the last valid thrust estimate, and write the flag to the log. Expect roughly 1 in 4 motor choices to trigger it. Disable the AP_SDO internal pull-up.
7. **MS5611**: OSR = 4096 (8.22 ms typ / 9.04 ms max); pressure every cycle, temperature every 10th → ≈ 100 Hz. **Verify the PROM CRC-4 at power-up and refuse to arm on failure** (catches counterfeits, cracked dies and cold joints). Log it as its own record type. **Apogee detection must be barometer-primary**; the accelerometer must not be promoted to primary apogee source.
8. **SAM-M10Q**: dynamic model **Airborne < 4 g** (its plausibility check only looks at altitude: 80 km limit, 20,000 m/s; supersonic flight does not invalidate the fix). 10 Hz **is not available in the default multi-constellation configuration** — either enable only GPS + Galileo at 10 Hz or accept 5 Hz. GPS is only a descent/recovery and pad-lock aid, **not a flight-state source** (the patch antenna faces sideways on an axial sled, and the airframe rolls).
9. **ADC absolute scale**: calibrate by reading VREFINT against the factory constant VREFIN_CAL (0x1FF1E860–0x1FF1E861), in place of an uninstalled precision reference.
10. **Battery voltage**: the divider taps RAW = the servo bus; a 12 A stall pulls the reading down about 1.0 V. **Sample synchronously and take a rolling maximum**, or explicitly separate "instantaneous voltage" from "battery state" in firmware. On USB power alone this node reads ≈ 1.487 V — free "no battery" detection.
11. **USB**: with no VBUS (PD15 low), **do not enable the OTG stack at all**, so its interrupts never disturb the 800 Hz control loop.
12. **Clock**: SYSCLK 200 MHz, VOS2/VOS3. Do not run 480 MHz (saves 145 mA / 0.48 W, load < 5 % either way, and the LQFP100 has only the LDO).
13. **I2C1 must implement bus recovery** (9 clocks on SCL + STOP) and slave-timeout degradation — the necessary compensation for the spare header sharing the barometer's bus.
14. **Buzzer**: externally driven at ~2.7 kHz; sweep on the bench to find the real resonant peak. Encode arming state, both continuity states and GPS lock as distinguishable tones — this is the only status channel you can hear inside a closed airframe.

---

## 8. Still to be confirmed

| # | Open item | Why it matters | What the answer changes |
|---|---|---|---|
| 1 | **Airframe ID / coupler ID** — this design assumes 3 in / 75 mm (ID 72.87 mm) | Sets the top-side height budget. Tallest fitted part is the 14 mm screw terminal; naive rectangle bound 26.9 mm, true chord-height bound 45.79 mm | At 4 in everything loosens; for a 54 mm airframe **the design does not work** (B5 is a hard geometric result) and must become two narrow boards or change packages. *(Resolved later: ID 54.66 mm with a 46 mm board — see GEOMETRY_REV_G.md.)* |
| 2 | **Servo model, real voltage tolerance, stall current** | (a) The servo bus is **raw 2S = 8.4 V**, so the servos must be HV; (b) the 3×4 header is **3 A per pin**: four 2 A-stall servos are 67 % of rating, four 3 A-stall servos exactly 100 % | If stall is > 3 A, split across two 3×2 headers or go back to separate terminals (+3 parts); this is the board's only hard constraint on servo choice. *(Resolved later: MKS HV6120, stall 1.916 A @ 8.4 V.)* |
| 3 | **Motor class and peak axial g** | The ICM-45686 is ±32 g. Across 228 H–K motors in production: peak > 16 g for 68 %, > 32 g for **24 %**, > 200 g for **0 %** | If only < 32 g motors are flown, the saturation code can be simpler; if high-thrust motors such as J1799N/K2045/I1299/K2050/K2000 are common, **saturation flagging is mandatory, not optional** — it is the code that replaces the ADXL375 |
| 4 | **Igniter type (no-fire current, bridgewire resistance)** — currently computed for MJG-type, 1.0–2.0 Ω | The 0.764 mA continuity current gives 327× / 52× margin against MJG no-fire and 40 mA max test current; the 4.0–7.6 A fire current assumes 1.0–2.0 Ω | With low-resistance / low-no-fire igniters the 10k/1k divider may need to become 10k/470R or use a lower sense duty cycle; with high-resistance igniters recompute the AO3400A thermals |
| 5 | **Target altitude** | The MS5611 reaches 10 mbar ≈ 31 km, usable throughout; Altus Metrum's experience is that below 30 km baro + accel fusion "locks apogee within a few samples almost every time", and an accelerometer-only apogee source is only needed above 30 km | If the target is > 30 km (practically impossible for this airframe), the case for deleting the ADXL375 collapses and C2 must be reopened |
| 6 | **Is the pull-pin harness bundled with the servo/pyro harness?** | All 4 SRV05-4 channels are taken by the servos. The sensor review wanted 8 channels to cover the pull-pin; the pyro review gave 4. The pull-pin currently has only 1k series + 10k pull-up and **no clamp**: if its wire chafes onto 8.4 V the FT pin sees more than its 7.3 V limit | **Ruling (to be confirmed)**: the pull-pin must run < 150 mm of twisted pair to the airframe pin hole, **physically separate from the servo/pyro harness** (other side, different ties). If they must be bundled, add **+1 part** (another SRV05-4, or a BAT54S dual diode clamping to 3V3/GND) |
| 7 | **Order SAM-M10Q now, or switch to SAM-M8Q** | C5443880 has only **51 pcs**, $22.55, no volume price — the most fragile and most expensive line on the board | Order now → design unchanged. SAM-M8Q-0 (C5447387, 142 pcs, $11.98) → u-blox officially states pin-to-pin compatibility, **zero copper changes**, at the cost of 2.5 m vs 1.5 m accuracy, no BeiDou, 67 mA vs 10 mA. **Same land either way, so the board can be drawn first and decided later** |
| 8 | **One reverse-protection FET or two** | Two = full bidirectional protection, +1 placement, 0 new part numbers, +86 mV drop at 12 A. One = −1 part, but a reversed battery destroys the servo-bus capacitor and probably the servos (although with the bidirectional SMBJ12CA it **no longer shorts the pack**) | The only trade of "one more part for removing a failure that only happens on an assembly mistake"; under the delete-parts principle it cannot be decided unilaterally. Frozen as **two** by default |
| 9 | **MS5611 or MS5607** | Same land, same command set, half price ($2.62 vs $5.02), similar stock. The MS5607 has about half the resolution (≈ 0.27 m vs 0.135 m RMS) and a different PROM compensation formula | Copper unchanged, can be decided at order time; not a zero-firmware change |
| 10 | **Is USB hot-plug inrush acceptable?** | The logic hold-up capacitor shares the 470 µF part number with the servo-bus capacitor. Plugging USB with no battery charges 470 µF through the SS34: about 2.16 mC, ~9 A peak, τ ≈ 235 µs, **beyond the USB 2.0 10 µF bulk-capacitance guidance** | If a laptop port complains: replace C-BULK2 with a same-package 100 µF/25 V polymer (hold-up 18.2 ms → 3.9 ms, inrush 0.46 mC, **+1 part number**). Frozen at 470 µF because the failure it prevents (a momentary brown-out from boost vibration losing the rocket) is far worse than the one it causes (a host complaining on the bench) |

### Appendix: items still marked "unverified / low confidence"
- **Maximum DCR of the Sunlord SWPA4030S4R7MT** not verified from the maker's datasheet (LCSC gives only typ 78 mΩ). Worst case 95–100 mΩ is still inside u-blox's 0.2 Ω limit; the conclusion stands, margin drops from 2.6× to about 2×.
- **470 µF/25 V polymer (C46550466) has no maker datasheet**: 25 mΩ ESR and 4.1 Arms come only from the LCSC parameter table. Chosen because every brand-name SMD polymer of the same size is unbuyable on LCSC (KEMET 64 pcs, Nichicon 0, Panasonic 0, Vishay 0).
- **DB128V terminal body length unverified** (only the 14 mm on-board height is known). Layout uses the conservative bound 5.08N + 2.54.
- **SRV05-4 has no explicit continuous forward-current rating** (the datasheet gives only VF = 1.2 V @ 15 mA and curves). At 18–20 mA continuous fault current each channel dissipates 22 mW, thermally nowhere near a limit, but this is inferred from curves and package, not a rated value. **Bench check**: one channel with 8.4 V through 220R for one hour.
- **The meaning of Gm_critmax is derived, not cited** (AN2867 could not be reopened this round). Reasoning: if an extra 5× gain margin were also required, no 25 MHz crystal at any load capacitance would pass on the H743, yet ST's own H7 evaluation boards use a 25 MHz HSE — the inference holds but is an inference. **Check against AN2867 before release to fab.**
- **NDK does not publish C0 for the NX3225GA.** The 2.51× gm_crit margin assumes C0 = 3 pF; at a pessimistic C0 = 7 pF it is 1.35×, still passing.
- **The DS12110 copies checked were Rev 5 / Rev 7.** The I/O structure column is a silicon property fixed at tape-out and no erratum has changed it; still, before release to fab re-check PE9 = TT_ha and PB1 = TT_u in the current revision (the rulings do not depend on them; only the strength of the rejection does).
- **Several pins' exact FT_x suffixes were not individually checked** — see the markings in §3. Every pin marked "unverified" carries only on-board 3.3 V signals and is never taken off the board, so its 5 V tolerance class is not a risk.
- **Sharing I2C1 with the spare header is a low-confidence ruling** and may be overturned (see §3.6).
- **The MLT-8530 coil inductance is not published**; the 9–45 µJ per cycle freewheel energy is estimated for 2–10 mH. It only affects freewheel-diode margin (the 10× current margin holds regardless).
