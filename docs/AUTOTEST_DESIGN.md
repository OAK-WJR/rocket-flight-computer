> 2026-09-07 implementation status: limited SWD register capture and interpretation of external DC measurements are implemented; see [diagnostics/README.md](../diagnostics/README.md). The rest of this document is the older M1/M2 test design and has not been executed. The current implementation does not treat a fixed CPUID, the reset flags or a single voltage reading as proof of an exact chip or a unique fault; sensor, storage, watchdog and actuator functional tests are not complete. Full M3 status: [STATUS.md](../STATUS.md).

# AI-driven automated fault localisation — design (TEST-1, 2026-09-03)

> This is not excerpted from another report; it was designed new for requirement 3 (automated fault localisation), expressed in the same change schema so it can be merged with the four other lists.
> Baseline: 101 soldered parts / 39 part numbers / 78 nets / 370 connections. Net addition in this document: **5 parts, 0 new part numbers, 2 GPIOs** (FMEA H-1's +3 parts / +1 part number is also adopted but belongs to H-1; do not double-count when merging).

---

## 0. One-sentence conclusion

**Today the board's visibility into its own power chain is: RAW visible, 3V3A visible (for free), everything else blind.** Add **two dividers (5 parts, 0 new part numbers, two free ADC pins PC2/PC3)** plus FMEA's already-proposed H-1, and the whole chain `BAT+ → load switch → RAW → diode OR → buck → LC → sensor rail` has a digital reading at every stage boundary; together with **a RAM-resident self-test program loaded over SWD that does not depend on the flight firmware**, an AI agent can plug in a probe and say within 90 seconds "which stage is broken, what it reads, and what the criterion is".

---

## 1. What the board cannot see today (node by node)

The power chain and every diagnosis-relevant node, checked against the as-drawn netlist and frozen §3.

| Node | Visible today? | Means | Consequence of the blind spot |
|---|---|---|---|
| **BAT+** (upstream of the switch) | ❌ Blind | — | "Battery flat / reed switch not closed / cold joint on J1's SW pin / Q1-Q2 dead" cannot be told apart. The J1 SW cold joint is the killer named in DESIGN_ASSURANCE Tier 2 item 5: perfect continuity on the bench (only 76 µA, no self-heating, no voltage drop), pulled open by vibration = whole-board power loss |
| **FET_S** (common source) | ❌ Blind | — | Cannot tell which of the back-to-back pair is not conducting (but RAW would be 0, merging with the row above) |
| **RAW** | ✅ | `R3/R4` 100k/47k → PC4 (ADC12_INP4) | Existing. 8.4 V → 2.686 V |
| **VLOGIC** | ❌ Blind | — | **The most expensive blind spot**: `D2 (SS34, RAW → VLOGIC)` is the **only** path from the battery to the logic rail. On the bench USB is always plugged in, so with D2 cold-soldered/open everything looks fine; the moment USB is unplugged (i.e. the moment it goes into the rocket) the board dies. No test today can find it |
| **3V3** | ❌ Blind | — | Indistinguishable from 3V3A: with VDDA = 1.8 V, "buck output at 1.8 V" and "L2 cracked, 3V3 fine" give the same reading, and the H743 **still runs** at VDD = 1.8 V, so both faults look like "MCU alive, all sensors dead" |
| **3V3A / VDDA** | ✅ **zero parts** | Solve from VREFINT against `VREFIN_CAL (0x1FF1E860)` | See §1.1 |
| **MCU pin 6 (VBAT)** | ✅ zero parts | Internal ADC `VBAT/4` channel (set `ADC3_CCR.VBATEN`) | Reads near zero if the pin is open. The **only** way to verify that joint without poking a probe onto 0.5 mm pitch |
| **Die temperature** | ✅ zero parts | Internal `VSENSE` + `TS_CAL1/2` | Used for the three-temperature cross-check |
| **PYRO_BUS / ARM state** | ✅ | `R14/R15` → PC5 | Existing |
| **Both pyro drains** | ⚠️ Half blind | `R18/R19`, `R22/R23` → PC0/PC1 | Sees only the drain potential: **the gate chain (470R, 1k, gate bond, FET body, MCU pin configuration) is 100 % uncovered**, so a dead channel is certified healthy by the self-test (DESIGN_ASSURANCE Tier 2 item 8). And with the ARM plug out, healthy FET / shorted FET / open igniter / no igniter **all read 0 V** (FMEA I-1) |
| **Servo outputs (after the 220R)** | ❌ Blind | — | See §3.3; ruled an **accepted blind spot** |
| **Buzzer branch** | ❌ Blind | — | See T-16 in §5; measured indirectly through a 3V3 load step |
| **Both LEDs** | ❌ Blind | — | Not electrically testable; accepted |
| **Pull-pin** | ✅ digital | PD14 | Open = "pulled = permitted", failing toward armed. Compensated by a firmware latch (ruled in DESIGN_ASSURANCE) |
| **VBUS** | ✅ digital | PD15 (only really usable with FMEA H-4's 100k pull-down) | Before H-4 the pin is a floating CMOS input and its reading is meaningless |

### 1.1 What VREFINT does and doesn't prove

Frozen §3.1 ties pin 20 (VREF+) directly to pin 21 (VDDA), both fed from **3V3A**. So `VDDA = VREF+ = 3V3A`, and since VREFINT is converted relative to VREF+ → `VDDA = 3.3 V × VREFIN_CAL / VREFINT_raw`. **Zero parts, zero pins, zero area.**

- **Proves**: the absolute value of 3V3A, to about ±0.5 % (dominated by the factory accuracy of VREFIN_CAL). It therefore also shows the buck is broadly regulating (only 30 mA × 78 mΩ ≈ 2.3 mV across L2, so normally 3V3A ≡ 3V3). It is the **only free detector** for FMEA V-4 (L2 open — a 3 mm wirewound inductor in single string ahead of every sensor and the whole ADC scale); FMEA F-12 already made it a rule, merged here rather than duplicated.
- **Does not prove**: (a) 3V3 itself — once L2 degrades (not open, but a 20–100 Ω cracked joint), VDDA sags to 1.8 V while the buck output is still 3.30 V, and VREFINT reports "3V3A low" without saying which stage; (b) **it fails itself when L2 is fully open** — with VDDA ≈ 0 the ADC does not work at all and readings are meaningless. So VREFINT's output must first pass a plausibility gate (raw code not 0, not full scale, VDDA ∈ 2.0–3.8 V); outside it, report `ANALOG_SUBSYSTEM_DEAD` rather than a voltage.
- **Every other ADC channel's absolute scale is parasitic on it**: with VDDA wrong, PC0/PC1/PC4/PC5 are all wrong **yet mutually consistent** (FMEA V-4's own words). So every criterion in this design is written as a **ratio** or a **VREFINT-calibrated voltage**, never an absolute millivolt window (the same discipline as FMEA §6.3 item 4's `ARM_SENSE / (VBAT_SENSE × 147/47) = 1/11 ± 15 %`).

---

## 2. Minimum sensing set (+5 parts, 0 new part numbers)

Pin choice: CIRCUIT_REVIEW §6 checked all 55 used LQFP100 pins against ST's machine-readable pin data (STM32_open_pin_data / STM32H743VITx.xml) and confirmed along the way that **pins 17/18 = PC2_C/PC3_C are unused in this design**. They are in none of frozen §3.10's reserved/avoid tables, and not in the H743 bootloader pin set of AN2606 Table 113 (the bootloader uses PA9/PA10, PA2/PA3, PB10/PB11, PB6/PB9, PA8/PC9, PA4–PA7, PA15/PB3–PB5, PE11–PE14, PD0/PD1, PA11/PA12). They sit right next to VSSA/VREF+/VDDA (19/20/21), the best analog corner on the board.

> **Mandatory firmware note**: on LQFP100 these two pads are merged `_C` pads. The `PC2SO/PC3SO` bits of `SYSCFG_PMCR` reset to 0 = analog switch closed = the pin is ordinary PC2/PC3 (GPIO + ADC12). **No initialisation code may set these two bits**, or both rail senses silently fail. This must go into the specification — it is exactly the trap "someone copies an H7 template in future" will fall into.

### 2.1 AT-1 · VLOGIC sense → PC2 (pin 17, ADC12_INP12) — +3 parts

`VLOGIC ──R-VL1 (100k)──┬── PC2 ;  ┴ R-VL2 (10k) to GND ;  ┴ C-VL (10 nF) to GND`

| Condition | VLOGIC | PC2 node (÷11) | 16-bit code @ VDDA = 3.3 |
|---|---|---|---|
| USB only (VBUS 5.00, D3 Vf 0.32 @ 120 mA) | 4.68 V | **425.5 mV** | 8452 |
| USB only, worst (VBUS 4.75) | 4.43 V | 402.7 mV | 7999 |
| Battery full (8.4 V, D2 Vf 0.33 @ 150 mA) | 8.07 V | **733.6 mV** | 14571 |
| Battery at LVC (6.0 V) | 5.67 V | 515.5 mV | 10239 |
| TVS clamp transient (BAT+ 19.9 V) | 19.55 V | **1777 mV** | — |

- **The 1/11 ratio rather than 47/147 is deliberate**: 1/11 keeps the worst TVS clamp transient at 1.78 V, safely inside the 4.0 V hard limit PC2 would have if it is TT_a class (the existing `VBAT_SENSE` uses 100k/47k and would put 6.36 V on PC4 in the same event — an existing exposure none of the four reports mentioned; this document simply doesn't copy it). And 100k and 10k are both existing part numbers (C25741 / C25744): **0 new part numbers**.
- **Quiescent current** 73 µA @ 8.07 V / 43 µA on USB. **The node is after the load switch and the diode OR, so it is 0 V with the board off** → zero battery drain in storage, and no path for "external voltage forward-injecting into an ADC pin while VDD = 0", which the frozen document explicitly forbids.
- **The 10 nF is required**: with the 9.09 kΩ source it forms a 1.75 kHz pole, giving ~56 dB rejection of the AP63203's 1.1 MHz input ripple and suppressing coupling from the 12 A servo bus onto RAW/VLOGIC. This channel only needs DC accuracy, not transient bandwidth.

**What it buys** (by value):
1. **D2 open / cold joint — a single-point fatal fault that is completely untestable today.** With battery + switch closed and USB unplugged, `V_RAW − V_VLOGIC` must fall within 0.25–0.45 V (the SS34's forward drop at 100–200 mA). ≈ 0 = D2 shorted; V_VLOGIC ≈ 0 with RAW normal = **D2 open: this board dies the moment USB is unplugged**.
2. **D2 shorted / USB back-feeding RAW.** On USB power alone PC4 must read ≤ 0.15 V (DESIGN_ASSURANCE correction (f) showed D2 is then reverse-biased and RAW near 0). If PC4 reads ~1.49 V, a shorted D2 is putting USB's 5 V onto **the servo header and the ARM terminal** — a safety-relevant fault that today only a person with a meter can find.
3. Buck input headroom and supply-source identification (USB / battery / both) — the denominator for every rail criterion after T-14.

### 2.2 AT-2 · 3V3 sense → PC3 (pin 18, ADC12_INP13) — +2 parts

`3V3 ──R-33A (10k)──┬── PC3 ;  ┴ R-33B (10k) to GND` (**no capacitor**, reason below)

- Node **1.650 V** nominal, **165 µA** quiescent (only while the board is powered), 5.0 kΩ source impedance. Both C25744, 0 new part numbers.
- Worst case: a high-side buck short making 3V3 = 8 V puts 4.0 V on the node — but then VDD = 8 V and the MCU is already dead, so sizing the ratio for that case is pointless. In normal operation and every survivable fault the node is ≤ 1.80 V.
- **The key criterion is a ratio, not a voltage**: `k = V_3V3 / V_VDDA`. Normally **k = 1.000** (2.3 mV across L2).
  - k high (> 1.05) → **the L2 / 3V3A stage**: a cracked inductor joint, a local short on the sensor rail. A 50 Ω crack gives k = 1.83.
  - k normal but both low → **the buck stage** (AP63203, L1, Cout, VLOGIC input).
  - Exactly the pair of faults that is indistinguishable today, separated with two 0402s.
- **Deliberately no capacitor**: T-16 (buzzer load step) measures the **transient dip** of 3V3 under a 95 mA step (about 40 mV deep, recovering in hundreds of microseconds), and a 10 nF would smear it out. A 5 kΩ source needs under 0.4 µs of 16-bit ADC sampling time, so it can run at ~1 MSPS and capture the transient directly. "Each node's filtering is set by the quantity it has to measure", not copied.

### 2.3 AT-3 · The zero-part pieces (internal channels + per-board calibration)

- Enable all three internal channels VREFINT / VBAT4 / VSENSE and log them (merged with FMEA F-12).
- **Per-board divider calibration**: 1 % resistors give ±1.4 % uncertainty in divider ratio, while D2's drop is only 0.35 V — uncalibrated, §2.1 item 1 can only catch gross faults like "open", not "degraded". Method: after assembly, apply a known 8.000 V to the BAT terminal from a bench supply (its own display is the reference), record the PC4/PC2 codes, and write them with the VREFINT-calibrated 3V3 divider ratio into the configuration block. **5 minutes per board, once, zero parts**; criteria then tighten from ±1.4 % to ±0.2 %, and the `V_RAW − V_VLOGIC` window from ±0.16 V to ±0.03 V. An uncalibrated board may still run, but the corresponding checks are downgraded to `DEGRADED (uncalibrated)` in the report.

### 2.4 Three "do not add"s stated once

- **No BAT+ divider.** Any divider measuring the battery upstream of the switch is a **permanently live** path; with the board off VDD = 0 while that node sits at 2.7 V, forward-injecting about 77 µA through the ADC pin's ESD structure into the unpowered VDD rail and holding the MCU in an undefined half-powered state — exactly the class of path the frozen document closed when it stopped taking the pyro bus from raw BAT, and a violation of the FT pins' own "no positive injection at all" rule. **The cost, stated plainly**: with the switch open, the battery is invisible to firmware. **The free substitute**: with the switch closed PC4 reads the battery voltage, so the only remaining blind spot is the single "switch open" state, where a two-state test is possible (see T-15), and the residual four-way choice {battery / reed switch / J1 joint / Q1-Q2} is closed by the instrument-free action "swap in a known-good battery pack".
- **No 3V3 current sensing.** See §3.
- **No servo output readback.** See §3.3.

---

## 3. Is current sensing worth it? (a conclusion, not options)

**Conclusion: no.** No shunt and no INA-class current-sense amplifier on the 3V3 rail. Three reasons, any one sufficient:

1. **It puts two new solder joints in series with the MCU's only supply path.** That was the core reason the frozen document deleted the 0 Ω sense jumper, and DESIGN_ASSURANCE re-checked and reinforced it ("adding links to a single-point-failure chain"). Requirement 2 asks for **independent protection layers**, not more links in the critical path.
2. **The only extra fault it catches is bounded.** Correct voltage with abnormal current can only be "a partially shorted decoupling capacitor": the rail stays in spec and the board still works; the consequence is heat and endurance, not mission failure. A short that really kills the mission always pulls the rail down, which is visible as voltage.
3. **A better zero-part substitute already exists, measuring a more useful quantity**: **use the buzzer as a calibrated 95 mA step load and measure 3V3's transient dip and recovery time on PC3** (T-16). In one go it gives the buck's load-transient response, whether the output capacitors are present, whether the inductor saturates, and whether the buzzer branch itself conducts — none of which one steady-state current number provides.

**Companion procedure item (0 parts)**: DESIGN_ASSURANCE already mandates "first power-up is always USB first, then a current-limited bench supply", and that supply's own ammeter is the absolute reading. Give it a numeric criterion in the procedure: **at 200 MHz / VOS3 idle with all sensors on and GPS locked, the 3V3 branch draws 128–184 mA; the whole board (VLOGIC side) draws 75–120 mA at 8.4 V**; outside that, stop. This turns "current" from a permanent board-level liability into a one-time assembly acceptance reading.

---

## 4. Links: how the AI actually connects

### 4.1 Primary link = SWD (ST-LINK / CMSIS-DAP + pyOCD or OpenOCD)

**It is the primary link because it needs no cooperation from the flight firmware.** The probe can halt the core, read and write any memory, program flash, and — the core technique of this design — **load a RAM-resident self-test program (AT-7) into AXI SRAM and run it directly**. The whole test suite therefore **does not depend on whether the firmware under test exists, is correct, or has hung**. That is the only form that works for "an agent plugs into a freshly soldered board".

- The 1×6 header J2 already exists, and DESIGN_ASSURANCE has ruled it **must be fitted, never DNP**; this document adds one more reason: it is the main test port.
- Automation: the Python API or CLI of `pyocd`/`openocd`, fully scriptable, zero manual steps. SEGGER RTT drains a RAM ring buffer over SWD for a bidirectional console with **zero pins and zero parts** (SWO cannot be brought out — PB3 is SPI1_SCK, settled in DESIGN_ASSURANCE §4.6).
- **Can diagnose**: power rails (through ADC registers), the core, the clock tree (RCC registers), every bus and device, flash, the pyro chain, the watchdog, reset causes.
- **Cannot diagnose**: the USB peripheral itself, the USB-C connector and D+/D− routing, and "the firmware's autonomous behaviour without a probe attached".
- **Needs a $10–20 probe** — the only barrier.

### 4.2 Backup link = USB CDC

- **It is only available once a lot already works**: the MCU running, HSE correct, PLL locked, USB PHY and connector intact, firmware running far enough to enumerate. So it **is not suitable as the primary link** — it carries the least diagnostic information exactly when you need diagnosis most.
- **Its irreplaceable value**: (a) it is the **only** thing that verifies the USB path itself; (b) it is the download path for the 16 MB flight log (RTT can do it too, but at 100 kB/s 16 MB takes 160 s); (c) it provides the board's **only ppm-class clock reference** — a USB SOF every 1.000 ms, derived from the host's crystal (see T-22); (d) no probe needed.
- When the firmware is completely dead, the ROM bootloader's DFU uses the same connector. **Note the conflict with DESIGN_ASSURANCE's J2 reorder**: after the reorder a 2.54 mm jumper physically cannot select DFU, so entering DFU needs a fly wire or tweezers. With SWD available that cost is acceptable, but it must be recorded.

### 4.3 The installed reality (GEOMETRY_REV_G)

- `GEOMETRY_REV_G §3.4`: USB-C is on the starboard long edge with only **3.80 mm** of radial room at the board edge; the USB plug shell does not fit → **"on-board USB is bench-only; data download / flashing requires pulling the sled"**, already promoted to mechanical rule ④.
- The same document computes, for J2 (x = 41, y 57.0–72.24), a maximum crimp housing of 16.75 mm against 18.633 mm of clearance there, **1.88 mm spare ✓**.
- Ruling: **when installed, J2 is (geometrically) the only possible service port, with only 1.88 mm of margin** → SWD cables must use **fly leads / low-profile right-angle housings**, not standard shielded ribbon housings. **And stated honestly**: the terminals cannot be tightened inside the airframe (§7.2 mechanical rule ③), so any re-termination already means pulling the sled; in practice "testing the complete rocket" = testing with the sled pulled out and the rest of the harness still connected. **No USB pigtail** — that would be a new connector, live in flight and chafing on the airframe wall, doing what an existing port already does.

---

## 5. Test suite (ordered, with numeric criteria; the first failure localises)

Three configurations, loaded in stages. Every item states its `prerequisite` (if not met, it is skipped and marked `SKIPPED(prereq)`), so **the first FAIL is the stage that has been localised**. All criteria use VREFINT-calibrated voltages or ratios.

### CFG-A Bare board + USB, nothing else connected (about 90 s, fully automatic)

| ID | Check | Criterion | FAIL localises to |
|---|---|---|---|
| T-01 | SWD DP IDCODE | Exactly `0x6BA02477` | 3V3 not up / NRST held / SWDIO-SWCLK open or shorted |
| T-02 | CPUID `0xE000ED00` | `0x411FC271` (Cortex-M7 r1p1) | Relabelled or wrong MCU |
| T-03 | DBGMCU_IDC / flash size / UID | Device ID = 0x450; flash size @ `0x1FF1E880` = 2048 KB; UID @ `0x1FF1E800` three words non-zero and not all F | Swapped for an H743VG (1 MB) or H723; UID all F = unreadable |
| T-04 | `RCC_RSR` | PORRSTF expected on first power-up; IWDG1RSTF / low-power reset flags = FAIL | Previous run was abnormal; this is the evidence for "charge didn't go vs computer refused to fire" |
| T-05 | AXI SRAM march (64 KB, 0x5A5A / 0xA5A5 / address patterns) | 0 mismatches | Core / bus / VCAP decoupling (pins 48/73, 2.2 µF each) |
| T-10 | VDDA (VREFINT) | **3.135–3.465 V**; raw code not 0 and not full scale | Low = buck or LC (T-11 separates them); high = buck out of control; out of range = analog subsystem dead (L2 fully open) |
| T-11 | 3V3 (PC3) and ratio k | V = **3.135–3.465 V**; **k = V3V3 / VDDA = 0.95–1.05** (0.99–1.01 calibrated) | k high → **the L2 / 3V3A stage**; k normal with both low → **the buck stage** |
| T-12 | MCU pin 6 (internal VBAT/4) | **0.784–0.866 V** | Pin 6 cold joint (reads near zero) |
| T-13 | Die temperature | **15–60 °C** at cold start | Local short (hot at power-up) |
| T-14a | VLOGIC (PC2), USB only | **4.20–4.85 V** | Low → D3 open / high-resistance, or USB supply collapse |
| T-14b | RAW (PC4), USB only | **≤ 0.15 V** | High (~1.49 V) → **D2 shorted**; USB 5 V is already on the servo header and ARM terminal |
| T-20 | RCC status | HSERDY = 1, PLL1RDY = 1, SWS = PLL1, CSS not triggered | 25 MHz crystal / load capacitors / soldering |
| T-21 | Clock vs IMU | Mean of 8192 DRDY intervals **1250 µs ± 3 %**, jitter σ < 5 µs | Wrong HSE frequency (wrong crystal or wrong CL), or the IMU not on the 800 Hz step (a relabelled 42688 has no 800 Hz step) |
| T-22 | Clock vs USB SOF (when USB is enumerated) | SOF interval **1000.0 µs ± 0.05 %** | The board's only ppm-class clock criterion |
| T-30 | QSPI identity + **quad-line proof** | JEDEC = `EF 40 18`; after setting QE, write 256 B of LFSR to a scratch page in 1-4-4 and read back in 4-4-4 with **0 byte errors** | ID fails → NCS/CLK/IO0/IO1 or VCC; **ID passes but quad fails → PE2 (IO2) or PD13 (IO3) open** (a single-line ID read still returns a perfect EF 40 18 with both open) |
| T-31 | IMU WHO_AM_I | `0xE9` | SPI1 routing / CS / 3V3A |
| T-32 | IMU IREG indirect-register loopback | Written value reads back | Relabelled part (the 42688 has no IREG path) |
| T-33 | **IMU noise floor and liveness** | 2048 samples at rest: \|a\| = **1.000 ± 0.05 g**; per-axis gyro σ ∈ **[0.010, 0.30] °/s**; per-axis accel σ ∈ **[0.5, 8.0] mg**; **≤ 2 identical consecutive samples** | σ = 0 → data path frozen / cracked die / DMA stuck (exactly the case where WHO_AM_I passes while the device is dead); σ too large → cracked joint or dirty supply |
| T-34 | IMU DRDY interrupt count | **780–820 edges** in 1.000 s | PE10 open — and the IWDG's only feed point hangs on it |
| T-35 | MS5611 address probe | Probe 0x76 and 0x77; **exactly one ACKs** | Neither → I2C1 / pull-ups / 3V3A / PS pin |
| T-36 | MS5611 PROM | CRC-4 passes; no 0x0000/0xFFFF in C1..C6, not all six equal | Counterfeit / cracked die / cold joint |
| T-37 | **Barometer noise floor** | 100 samples at rest at OSR4096: σ ∈ **(0.002, 0.020] mbar**; absolute value within ± 40 mbar of the site pressure supplied by the agent | σ ≈ 0 → data frozen; σ > 0.020 → relabelled MS5607 or bad joint |
| T-38 | Three-temperature cross-check | \|T_die − T_baro\| ≤ 15 °C; \|T_imu − T_baro\| ≤ 5 °C | One of them is lying |
| T-39 | GPS UART | Send UBX-MON-VER; a UBX response with a correct checksum within 1.2 s | PC6/PC7 swapped, module supply, dead module. **Open-sky sub-item** (INFO, not FAIL): ≥ 4 satellites with C/N₀ ≥ 35 dB-Hz within 120 s |
| T-3A | I2C1 bus health | With drivers released, SCL and SDA both read high; the 9-clock + STOP bus-recovery sequence completes | Missing 4.7k pull-up or a stuck slave |
| **T-40** | **Pyro gate pull-down integrity (zero parts)** | Configure the gate pin as input with the **internal pull-up** (~40k) and read: must read **0** (the external 1k pull-down holds the node at 0.080 V) | R17/R21 missing, tombstoned or cold-soldered — the only thing holding the pyro gate down at power-up, with no means of observation today short of a meter. **FAIL → the board must refuse to arm** |
| **T-41** | **Pyro cold four-state (needs H-1)** | ARM plug out, both gates low; read PC5/PC0/PC1 together and interpret per the FMEA table (nominal 40.5 / 31.4 / 56.9 mV, scaled down ~6 % after a one-time bench calibration of the BAT54A Vf) | Both < 5 mV → **FET drain-source short or drain shorted to ground → hard stop, refuse everything, do not touch the ARM plug**; any > 100 mV → pull-up network or divider damaged |
| **T-42** | **Pyro active conduction (needs H-1)** | Plug out, no igniters: drive each gate high for 10 ms in turn; that channel's CONT must collapse to **< 8 mV** and recover within 2 ms | No collapse → 470R open / gate bond broken / FET open / MCU pin not driving. **The only way in the whole design to verify the firing path's switching element end to end**; bridgewire current ≈ 70 µA (from the other channel's pull-up), genuinely zero energy |
| T-52 | VBUS detect (needs H-4) | Cable in reads 1 (node 2.50 V); cable out reads 0 within 200 ms | R9 or the H-4 pull-down missing |
| T-60 | Log round trip | Write 4 KB of records, read back with matching CRC32; readback throughput over the chosen link ≥ 50 kB/s | Flash sector / driver / link |
| T-62 | Firmware image CRC32 | Matches the constant written at link time | Interrupted download → refuse to leave DISARMED |

### CFG-B Add battery + external switch (about 30 s, including one manual switch flip)

| ID | Check | Criterion | FAIL localises to |
|---|---|---|---|
| T-15 | RAW two-state | Switch open: **≤ 0.15 V**; switch closed: **6.00–8.45 V** | Still 0 when closed → {battery / reed switch / **J1 SW pin cold joint** / Q1-Q2}; 3.0–5.5 V → one of the back-to-back pair not fully on, or a deeply discharged battery |
| **T-14c** | **D2 check** (USB out, switch closed) | **V_RAW − V_VLOGIC = 0.25–0.45 V** (± 0.03 V calibrated; uncalibrated, widen to 0.05–0.70 and guarantee only open detection) | ≈ 0 → D2 shorted; V_VLOGIC ≈ 0 with RAW normal → **D2 open: this board dies the moment USB is unplugged**. Untestable today |
| T-16 | **Rail load step (buzzer as a calibrated 95 mA load)** | ① first a 200 µs pulse; Δ3V3 must be **< 0.30 V**, otherwise abort immediately; ② then 5 ms DC, capturing the transient on PC3 at ~1 MSPS: dip **15–120 mV**, recovery **< 200 µs**, VDDA never below 3.10 V | Dip **< 3 mV** → buzzer branch open (Q5 / coil / wrong pad pairing) — **a mute buzzer detected without listening**; dip > 250 mV or no recovery → **D6 reversed** (a forward-biased diode from 3V3 to ground), shorted coil, or missing buck output capacitors / saturating inductor |
| T-22′ | Repeat T-10/T-11 on battery power | Same criteria | The buck behaves differently at 8.4 V input than at USB's 5 V |

### CFG-C Full vehicle configuration (about 3 min, with explicit manual steps)

| ID | Check | Criterion | FAIL localises to |
|---|---|---|---|
| T-43 | Arming state | With the ARM plug inserted, `ARM_SENSE / (VBAT_SENSE × 147/47) = 1/11 ± 15 %` | Plug not seated / 5 A fuse blown / R14 open |
| T-44 | Continuity with igniters | Each CONT = `RAW/11 ± 10 %` (0.700–0.830 V at 8.4 V); ~57 mV with no igniter, 13× separation | Open bridgewire / terminal not clamped. **Note**: a "short" clamped onto bare wire is indistinguishable from a good bridgewire (see §6) |
| T-50 | Servo outputs | **Register level only**: TIM5 CCR, GPIO MODER/AFR/ODR as expected | Proves only the MCU side. No electrical coverage on the board side (§3.3) |
| T-51 | Pull-pin | Reads 0 with the pin in; after the agent prompts "pull the pin", a clean 0 → 1 transition within 50 ms with < 3 bounces; the firmware latch requires having seen 0 first | Reads 1 at t = 0 → pin not inserted **or wire broken** (indistinguishable, which is exactly why the latch exists) |
| T-61 | **Watchdog proof** | Deliberately stop feeding; the IWDG must reset within **380–480 ms**, and after reset `RCC_RSR.IWDG1RSTF = 1` | The watchdog was never enabled — the difference between "a watchdog" and "a comment", which almost nobody tests |
| T-64 | Live pulse into a dummy load | Replace the igniter with a 1 Ω dummy load, 20 ms pulse: CONT < 100 mV during the pulse, RAW dip < 1.5 V, pulse width 19–21 ms (policed by the TIM2 hardware timeout) | The only test of the real firing-energy path |
| **T-65** | **Bay venting (zero parts; turns an "untestable" into a testable)** | Close the bay and warm it gently by hand/lamp for 5 min, logging P and T together: **\|dP/dT\| < 0.5 mbar/K** | An unvented sealed bay gives, by the ideal gas law, `P/T = 1013/293 = 3.46 mbar/K`, 7× separation. **FAIL = the bay has no vent or it is blocked**, and apogee detection would follow bay temperature rather than altitude |
| T-66 | Battery / harness resistance trend | Step all four servos together and record the RAW dip; compare with the baseline recorded at build, **warn if it changes > 30 %** | Battery ageing, loose terminals, bad harness crimps. The absolute value is unavailable (no current sensing), the trend is |

---

## 6. What still cannot be tested (the honest list)

| Item | Why it cannot be measured electrically | What covers it |
|---|---|---|
| **Control-loop signs** (gyro Z sign × servo direction × board mounting orientation) | With the board still, feedback is zero; completely silent on the bench. DESIGN_ASSURANCE's number-one killer; all four servos get the same wrong sign | **A mandatory manual step**: in closed loop, roll the airframe by hand; all four fins must deflect to resist, and log "command vs measured" sign. Plus a laminated card and the silkscreened coordinate triad |
| **Servo linkages, fin angles, fin freedom** | The board cannot see the linkages | Manual fin sweep, visually (the same action as above, no extra time) |
| **Servo output channel electrical integrity** (220R open, one SRV05-4 channel dead) | No readback path after the 220R | Unpowered DC signature: each J5A pad reads **10.22 kΩ** to ground (R24 + R28; nothing else on the connector reads that value) + the mandatory manual sweep above. **Ruling: no 5-part readback network for it (§3.3)** |
| **Whether the igniter is really buried in the charge, and whether the charge is damp** | Continuity only proves the bridgewire, not position or powder | Checklist + loading photos |
| **Terminal clamped onto bare wire vs a good bridgewire** | Same order of resistance (CIRCUIT_REVIEW 2.9) | No electrical means. Procedure: ferrules + visual check after termination + torque stripes |
| **Absolute battery internal resistance** | No current sensing, ΔI unknown | T-66's trend criterion (± 30 % of baseline) |
| **Whether the two LEDs light** | Not electrically testable | Eyes; and they are invisible in flight configuration anyway — the buzzer is the status channel in a closed bay, and T-16 covers it electrically |
| **VCAP decoupling (pins 48/73, 2.2 µF each)** | No observation node | Unpowered `VCAP1–VCAP2 = OL` (proves they are separate) + T-05's SRAM march (degradation shows up first as bus errors) |
| **Vibration / heat-soak behaviour in flight** | Does not exist on the bench | DESIGN_ASSURANCE §6.2's tap test and car heat soak, reusing this suite's criteria |

---

## 7. Machine-readable output

**Two layers, the same data, two independent paths.**

**Layer 1 — a RAM result block (most robust, independent of any serial protocol).** The self-test writes its results into a struct at a fixed AXI SRAM address: magic `"RKTP"` + version + monotonic sequence number + an array of check records. The agent **reads memory directly over SWD** to collect it, without needing any serial protocol to work. The sequence number increments after each completed check, so **even if the self-test hangs at some step, the agent knows which step it died on**.

**Layer 2 — streamed line output (RTT or USB CDC), sent as it runs, not buffered.** One line per check:

```
#T-11 3V3_RAIL 3.2910 V [3.1350,3.4650] PASS stage=BUCK
#T-14c D2_DROP 0.0090 V [0.2500,0.4500] FAIL stage=OR_DIODE_D2
```

**Streaming rather than batching is a key criterion**: the most informative failure is the one that hangs and never returns, and only streamed output can pin it to a specific check.

**Final report (JSON, for the agent)**:

```json
{ "schema":"rktfc.selftest/1", "board_uid":"...", "fw_sha":"...", "link":"swd",
  "config":"CFG-B", "utc":"2026-09-03T…", "cal":"calibrated",
  "verdict":"FAIL", "first_fail":"T-14c", "failed_stage":"OR_DIODE_D2",
  "checks":[ {"id":"T-11","name":"3V3_RAIL","stage":"BUCK","prereq":["T-10"],
              "value":3.2910,"unit":"V","band":[3.135,3.465],"verdict":"PASS",
              "raw":{"adc_code":32690,"vdda":3.3012},
              "localises":"AP63203 / L1 / Cout"} , … ] }
```

Three rules:
1. **Every check carries a `stage`** (a physical stage: `LOAD_SWITCH` / `OR_DIODE_D2` / `BUCK` / `LC_3V3A` / `SPI1` / `PYRO_CH1_GATE` …) — the agent wants "which stage is broken", not the check's name.
2. **Every check carries `raw`** (raw ADC codes, VDDA, register values), so the agent can recompute rather than trust the firmware's conversion.
3. **The same JSON is written into the flight log header as record type `0x02`**, right after DESIGN_ASSURANCE's `0x01` header. When downloading the log from a board that came back in pieces, the first thing visible is "how the board saw itself before launch".

---

## 8. Net impact

| Item | Count |
|---|---|
| New soldered parts | **+5** (100k × 1, 10k × 3, 10 nF × 1) → 101 → 106 (+4.95 %) |
| New part numbers | **0** |
| GPIOs used | **2** (PC2 pin 17, PC3 pin 18), both outside §3.10 and AN2606; about 38 left free |
| New quiescent current | **+238 µA** while running (0.17 % of the ~140 mA budget); **+0 µA in storage** |
| Board area | 5 × 0402/0603, about 4 mm², in the MCU analog corner (near pins 15–21) |
| Adopted from other lists | FMEA **H-1** (+3 parts / +1 part number) — a prerequisite for automated pyro-chain testing, irreplaceable; FMEA **H-3** (QSPI pull-ups, prerequisite for T-30) and **H-4** (VBUS pull-down, prerequisite for T-52) |
| Explicitly rejected | DESIGN_ASSURANCE's **R-ARMBYP** (it removes the arming plug's status as a "complete electrical break" — a whole independent protection layer — while H-1 provides the same cold-test capability for +3 parts **without touching the break**, and fails in the safe direction); 3V3 current sensing; the servo output readback network (5 parts); a BAT+ divider |

**If nothing is added**: D2 cold joints, L2 degradation vs buck undervoltage, pyro FET shorts and open pyro gate chains — all four classes pass the bench silently, and two of them are INJURY or VEHICLE_LOSS class. That is what these 5 parts (+ H-1's 3) buy.

### Summary

Today the board is almost blind to its own power chain: RAW is visible and 3V3A is visible for free through VREFINT, while BAT+, VLOGIC and 3V3 are invisible, so "D2 cold joint", "L2 cracked joint" and "buck output low" look like the same reading to firmware, or like no reading at all. Two dividers (5 × 0402/0603 in total, 0 new part numbers, two free ADC pins PC2/PC3, +238 µA running, +0 µA in storage) turn VLOGIC and 3V3 into numbers; together with three zero-part internal channels (VREFINT / VBAT4 / die temperature) and per-board divider calibration, the whole chain BAT+ → load switch → RAW → diode OR → buck → LC gets a reading at every stage boundary. The V_RAW − V_VLOGIC term in particular catches an open D2 — a single-point fault completely invisible on a bench where USB is always plugged in, which kills the board the moment it goes into the rocket. Automated pyro-chain testing adopts FMEA H-1 (BAT54A + 2 × 47k, +3 parts), turning "FET short" from something you can only discover by inserting the plug and watching it fire into a cold four-state reading with the plug out, plus a zero-part active-pulse test that covers the gate chain for the first time; DESIGN_ASSURANCE's R-ARMBYP is explicitly rejected because it removes the arming plug as a complete electrical break, a whole independent protection layer. The link ruling makes SWD primary (the RAM-resident self-test does not depend on the flight firmware existing or being correct, and GEOMETRY shows USB is unreachable once installed while J2 still has 1.88 mm) and USB CDC backup (the only thing that verifies USB itself, the only ppm-class SOF clock reference, and the log download path). The suite gives about 40 ordered checks with numeric criteria across three configurations CFG-A/B/C, including noise-floor criteria (σ = 0 means frozen data, closing the hole where WHO_AM_I still passes on a cracked joint), a QSPI quad-line proof, a watchdog proof, and a rail-transient test using the buzzer as a calibrated 95 mA load — which also replaces the rejected 3V3 current sensing and detects a mute buzzer without listening. Electrical readback of the servo channels (5 parts) and a BAT+ divider (positive injection into an unpowered pin) are ruled out, with the costs recorded. Output is a SWD-readable RAM result block + streamed lines + JSON (each check with stage/band/raw), written into the flight log header as record type 0x02.

## Change items

### [AT-1] netlist
- Parts: +3 | Part numbers: 0 | Complexity: low | Confidence: reasoned
- Add VLOGIC rail sensing: R-VL1 100k (C25741) from VLOGIC to a new net VLOGIC_SENSE; R-VL2 10k (C25744) from VLOGIC_SENSE to GND; C-VL 10 nF (C57112) from VLOGIC_SENSE to GND; VLOGIC_SENSE to U1 pin 17 (PC2, ADC12_INP12). Ratio 1/11: full battery 8.07 V → 733.6 mV, USB only 4.68 V → 425.5 mV, TVS clamp 19.55 V → 1777 mV (inside the TT 4.0 V limit).
- Prevents: D2 (SS34, RAW → VLOGIC) open or cold-soldered — the only path from the battery to the logic rail, completely invisible on a bench where USB is always plugged in, killing the board the moment USB is unplugged (i.e. put in the rocket); also catches a shorted D2 back-feeding USB 5 V onto the servo header and ARM terminal
- New failure: a shorted R-VL1 (100k) puts the full VLOGIC voltage (worst case the 19.55 V TVS clamp) directly onto PC2, above the TT class's 4.0 V hard limit, damaging the MCU analog front end; very low probability, but add VLOGIC_SENSE–GND = 10.0 kΩ and VLOGIC–VLOGIC_SENSE = 100 kΩ to the unpowered signature table. Also adds 73 µA of running current

### [AT-2] netlist
- Parts: +2 | Part numbers: 0 | Complexity: low | Confidence: reasoned
- Add 3V3 rail sensing: R-33A 10k (C25744) from 3V3 to a new net V3V3_SENSE; R-33B 10k (C25744) from V3V3_SENSE to GND; to U1 pin 18 (PC3, ADC12_INP13). Node 1.650 V nominal, 5.0 kΩ source, 165 µA. Deliberately no capacitor — T-16 must capture 3V3's sub-millisecond transient dip under a 95 mA step.
- Prevents: separates "buck output low" from "L2 / 3V3A stage degraded": the criterion is the ratio k = V3V3 / VDDA, normally 1.000, 1.83 with a 50 Ω crack in L2. Today, with VDDA = 1.8 V, the two faults read identically, and the H743 still runs at VDD = 1.8 V, both appearing as "MCU alive, all three sensors dead"
- New failure: 165 µA running current (0.17 % of budget). No capacitor means the channel is sensitive to switching noise on 3V3, so absolute criteria must use hardware oversampling (≥ 64×), or noise will cause false FAILs

### [AT-3] firmware
- Parts: 0 | Part numbers: 0 | Complexity: none | Confidence: verified
- Enable and log three zero-part internal ADC channels: VREFINT against VREFIN_CAL (0x1FF1E860) to solve VDDA (= 3V3A); VBAT/4 after ADC3_CCR.VBATEN to verify MCU pin 6's joint; VSENSE against TS_CAL1/2 for die temperature. Every ADC criterion is written as a ratio or a VREFINT-calibrated voltage; absolute millivolt windows are forbidden. Merged with FMEA F-12, not listed twice.
- Prevents: an open L2 (a 3 mm wirewound inductor in single string ahead of every sensor and the whole ADC scale) silently killing three sensors while four ADC channels read wrong together and consistently; and a cold joint on MCU pin 6 — today the only way to verify it is poking a probe onto a 0.5 mm-pitch leg
- New failure: if VDDA itself fails, the VREFINT reading fails with it, so it must first pass a plausibility gate (raw code not 0, not full scale, VDDA ∈ 2.0–3.8 V), reporting ANALOG_SUBSYSTEM_DEAD rather than a voltage when out of range. Otherwise it outputs a plausible-looking false number

### [AT-3b] procedure
- Parts: 0 | Part numbers: 0 | Complexity: low | Confidence: reasoned
- Per-board divider calibration: after assembly apply a known 8.000 V to the BAT terminal from a bench supply and record the PC4/PC2 ADC codes; record the PC3 divider ratio using the VREFINT-calibrated VDDA. Write the three coefficients into the configuration block, covered by its CRC32. Once per board, about 5 minutes, zero parts. An uncalibrated board may still run, but the related checks are downgraded to DEGRADED(uncalibrated) in the report.
- Prevents: 1 % resistors give ±1.4 % divider-ratio uncertainty while D2's forward drop is only 0.35 V — uncalibrated, AT-1 can only catch a fully open D2, not "a degrading cold joint" (a few ohms of contact resistance). Calibrated, the window tightens from ±0.16 V to ±0.03 V
- New failure: the calibration itself might be taken on a board that is already faulty (e.g. L2 already degrading), freezing the fault in as "normal". Mitigation: calibrate only after the whole unpowered DC signature table has passed, and apply a plausibility window to the calibration values themselves (reject writing a divider ratio more than 3 % off nominal)

### [AT-4 (= FMEA H-1)] component
- Parts: +3 | Part numbers: +1 | Complexity: medium | Confidence: reasoned
- Adopt FMEA H-1 as is: 3V3 → BAT54A common anode; cathode 1 → 47k (C25792) → PYRO1_OUT; cathode 2 → 47k → PYRO2_OUT. +2 × 47k 0603 + 1 × BAT54A SOT-23. Belongs to H-1; do not double-count against the FMEA list when merging.
- Prevents: pyro FET drain-source short (FMEA I-1) — today, with the ARM plug out, healthy FET / shorted FET / open igniter / no igniter all read 0 V, and the only "test" is inserting the plug and seeing it fire; with the plug in, a shorted FET has already fired the charge. H-1 turns it into a cold four-state measurement before the plug goes in
- New failure: a shorted 47k pull-up is an INJURY-class path (with ARM inserted the drain is clamped to 3.3 V, 5.1 V across the bridgewire → 5.1 A, immediate fire); the BAT54A is there to block exactly that; a shorted BAT54A plus a shorted resistor is a double fault. An open BAT54A = cold test reads all zeros = false "FET short" = scrub, the safe direction. The three ADC nodes become one simultaneous resistor network and must be read jointly, not channel by channel

### [AT-5] firmware
- Parts: 0 | Part numbers: 0 | Complexity: low | Confidence: reasoned
- Pyro gate pull-down integrity self-test (zero parts): temporarily configure the PYRO1/2_GATE pins as inputs with the internal pull-up enabled (30/40/50 kΩ on the H7) and read the level. The external 1k pull-down holds the node at 3.3 × 1/41 = 80 mV, so it must read 0. Reading 1 means R17/R21 missing or open: the board refuses to arm and sounds a dedicated tone code. Must run with the ARM plug out.
- Prevents: R17/R21 (the pyro gate 1k pull-downs) tombstoned or cold-soldered — the only thing holding the pyro gates down at power-up, while 0402 tombstoning is JLC's most common assembly defect and the node has no means of observation today short of a meter
- New failure: during the test the gate is lifted to 80 mV (8.1× margin against the AO3400A's corrected Vgs(th) min of 0.65 V, safe); but this code is the only place allowed to configure a pyro gate as an input, so it must live in the same file as pyro_may_fire() under the same CI grep, or it becomes a second writer bypassing the single choke point

### [AT-6] firmware
- Parts: 0 | Part numbers: 0 | Complexity: medium | Confidence: reasoned
- Pyro active-conduction self-test (zero parts, needs H-1): with the ARM plug out and no igniters, drive each gate high for 10 ms in turn; that channel's PYRO*_CONT must collapse to < 8 mV and recover within 2 ms. The request must go through a PYRO_TEST request type of pyro_may_fire(), with preconditions ARM_SENSE < 20 mV and VBUS present and state == SELFTEST, and the pulse width capped at 10 ms in hardware by a TIM2 output compare.
- Prevents: the whole gate chain (470R series, gate bond, FET body, MCU pin configuration) is 100 % uncovered today — with an open anywhere, PYRO*_CONT still reads a normal 0.764 V and the self-test certifies a dead channel as healthy (DESIGN_ASSURANCE Tier 2 item 8)
- New failure: it is the only code path in the project that drives a pyro gate high outside flight. If the preconditions are wrong or the SELFTEST state can be entered by mistake, it is a self-fire path. It must share the same function and CI constraints as pyro_may_fire(), and the TIM2 hardware timeout must be loaded on the same gate rising edge. Bridgewire current is about 70 µA (from the other channel's pull-up), not zero

### [AT-7] firmware
- Parts: 0 | Part numbers: 0 | Complexity: medium | Confidence: reasoned
- A standalone RAM-resident self-test program (< 8 KB, linked at AXI SRAM 0x24000000), loaded and run over SWD by pyOCD/OpenOCD, depending only on the core + RAM + clocks + ADC, not on whether the flight firmware exists, is correct or has hung. Results go into a struct at a fixed address (magic 'RKTP' + version + monotonic sequence + an array of check records), read directly from memory by the agent.
- Prevents: the scenario "an agent plugs into a freshly soldered board with no firmware yet" is not possible today; nor is self-testing once the firmware has hung — exactly when a self-test is needed most
- New failure: the self-test and the flight firmware are two code bases whose criteria may drift apart (the self-test says PASS while the flight code refuses to arm on a different threshold). Mitigation: both must share one criteria header, the criteria table is the single source of truth, and CI checks consistency between the two

### [AT-8] procedure
- Parts: 0 | Part numbers: 0 | Complexity: none | Confidence: verified
- Link ruling: SWD (J2) primary, USB CDC backup. J2 must be fitted, never DNP (consistent with DESIGN_ASSURANCE §4.6; one more reason here: it is the main test port). SWD cables must be fly leads or low-profile right-angle housings, not standard shielded ribbon housings — GEOMETRY_REV_G gives only 1.88 mm of crimp-housing margin at J2. Explicitly no USB pigtail.
- Prevents: USB CDC only works once a lot already works (oscillation, HSE, PLL, PHY, connector, firmware enumeration); making it primary means it carries the least information exactly when diagnosis is most needed; and GEOMETRY_REV_G §3.4 has already ruled that the USB plug shell cannot reach the board once installed (only 3.80 mm radial at the edge)
- New failure: needs a $10–20 probe, and DESIGN_ASSURANCE's J2 reorder makes it physically impossible for a 2.54 mm jumper to select DFU — entering DFU needs a fly wire or tweezers. SWD cannot diagnose the USB peripheral, the USB-C connector or D+/D− routing at all; those are covered only by T-22/T-60

### [AT-9] test
- Parts: 0 | Part numbers: 0 | Complexity: medium | Confidence: reasoned
- About 40 ordered automatic checks with numeric criteria, in three levels: CFG-A (bare board + USB, about 90 s, fully automatic) / CFG-B (+ battery + switch, about 30 s) / CFG-C (full vehicle, about 3 min including explicit manual steps). Each carries a prereq and is marked SKIPPED(prereq) if unmet, so the first FAIL is the localised stage. Full table in §5.
- Prevents: unactionable conclusions like "something is wrong somewhere". Today no board-level acceptance test with numeric criteria exists at all (MARGIN_PRESCRIPTION P1-14 only says one must)
- New failure: windows written too wide miss faults; too narrow and part tolerance and temperature produce false FAILs, and a test that rejects good boards is worse than none (DESIGN_ASSURANCE gave the same lesson on incoming screening). Mitigation: measured values from the first 5 boards are written back into the criteria table, and AT-3b's per-board calibration shrinks the windows from component tolerance to device tolerance

### [AT-10] document
- Parts: 0 | Part numbers: 0 | Complexity: low | Confidence: reasoned
- Machine-readable output specification: ① a SWD-readable RAM result block (magic + sequence, localising even a hang to one specific check); ② streamed line output (RTT or CDC), sent as it runs, not buffered; ③ a final JSON with id/name/stage/prereq/value/unit/band/verdict/raw/localises per check and verdict/first_fail/failed_stage at the top level; ④ the same JSON written into the flight log header as record type 0x02, right after the already-defined 0x01 header.
- Prevents: an agent parsing prose; the most informative failure — "the self-test hung and never returned" — being unlocatable (batched output swallows it whole); and being unable to tell afterwards, from a board that came back in pieces, how the board saw itself before launch
- New failure: once fixed, the stage enumeration is what agents act on, and renaming it silently breaks their handling logic — the enumeration must be versioned (the schema field) and only ever extended, never changed

### [AT-11] firmware
- Parts: 0 | Part numbers: 0 | Complexity: low | Confidence: reasoned
- Rail load-step test (zero parts): the buzzer as a calibrated 95 mA load. ① first a 200 µs pulse, aborting immediately if Δ3V3 ≥ 0.30 V; ② then 5 ms DC, capturing the transient on PC3 at about 1 MSPS: dip 15–120 mV, recovery < 200 µs, VDDA never below 3.10 V. A dip < 3 mV means the buzzer branch is open; > 250 mV or no recovery means D6 reversed / shorted coil / missing buck output capacitors or saturating inductor.
- Prevents: a mute buzzer (the only working status channel inside a closed airframe) can today only be judged by ear; a reversed D6 pulls the 3V3 rail down once per 2.7 kHz cycle the first time the buzzer sounds; and the buck's load-transient response is not measured at all today
- New failure: this code deliberately digs a 95 mA hole in the 3V3 rail during self-test; if the 200 µs pre-check's abort logic is wrong, a board with a reversed D6 is shorted for 5 ms. The pre-check must act first at the hardware level, and the abort path must not depend on any interrupt

### [AT-12] firmware
- Parts: 0 | Part numbers: 0 | Complexity: low | Confidence: verified
- QSPI quad-line proof (adopting DESIGN_ASSURANCE §4.4): read JEDEC ID = EF 40 18 → set QE → write a 256-byte LFSR pattern to a reserved scratch page in 1-4-4 → read back in 4-4-4 and compare byte by byte, 0 byte errors. ID passing while quad fails localises to PE2 (IO2) or PD13 (IO3) open.
- Prevents: a 0x9F ID read runs in 1-1-1 mode using only IO0/IO1 and still returns a perfect EF 40 18 with PE2 and PD13 completely disconnected — and the design deliberately removed the WP/HOLD pull-ups, so those lines float when open. The flight log would fail only in flight
- New failure: writing one page every boot consumes the scratch page's endurance (W25Q128 about 100k cycles; 10 boots a day lasts 27 years — acceptable, but the scratch sector must be physically separate from the log area, and a write failure must not block boot)

### [AT-13] firmware
- Parts: 0 | Part numbers: 0 | Complexity: low | Confidence: reasoned
- Sensor noise-floor criteria (zero parts): IMU 2048 samples at rest, \|a\| = 1.000 ± 0.05 g, per-axis gyro σ ∈ [0.010, 0.30] °/s, per-axis accel σ ∈ [0.5, 8.0] mg, ≤ 2 identical consecutive samples; MS5611 100 samples at rest at OSR4096, σ ∈ (0.002, 0.020] mbar; three-temperature cross-check \|T_die − T_baro\| ≤ 15 °C, \|T_imu − T_baro\| ≤ 5 °C.
- Prevents: WHO_AM_I still passes on a cracked joint, a cracked die or a stuck DMA — σ = 0 is the only signature of a frozen data path; the σ upper limit also discriminates a relabelled MS5607 (datasheet RMS resolution 0.024 vs 0.012 mbar) and degrading joints
- New failure: σ criteria are sensitive to the environment — a vibrating bench or people walking around produces false FAILs. The criteria must define "at rest", and on failure retest once before judging, so false rejections don't make people abandon the whole discipline

### [AT-14] test
- Parts: 0 | Part numbers: 0 | Complexity: low | Confidence: verified
- Watchdog proof test: in CFG-C deliberately stop feeding; the IWDG must reset within 380–480 ms, and RCC_RSR.IWDG1RSTF must be 1 afterwards.
- Prevents: a watchdog that was never enabled, or silently disabled by some refactor — the difference between "a watchdog" and "a comment", and FMEA ruled the IWDG chain the most important ruling on this board
- New failure: this test really resets the board, so it must be the last item of every self-test sequence and must not run with the ARM plug inserted (after the reset, rule 4 powers up DISARMED — the safe direction — but it would interrupt other tests in progress)

### [AT-15] test
- Parts: 0 | Part numbers: 0 | Complexity: low | Confidence: reasoned
- Vent test (zero parts): close the bay and warm it gently for 5 minutes, logging the MS5611's P and T together; criterion \|dP/dT\| < 0.5 mbar/K. An unvented sealed bay gives, by the ideal gas law, P/T = 1013/293 = 3.46 mbar/K, a 7× separation.
- Prevents: the static port has no specification at all (DESIGN_ASSURANCE Tier 3 item 11: an unvented bay = the barometer reads bay pressure; sealed at 20 °C and sun-heated to 60 °C it reads about 14 % high by the ideal gas law), while the barometer is the mandatory primary apogee source
- New failure: the test turns a mechanical/assembly property into an electrical criterion and may lead people to think "tested once, vented forever" — vents get blocked by residue, tape or coating, so it must be a routine item after every airframe closure, not a one-time acceptance item

### [AT-16] firmware
- Parts: 0 | Part numbers: 0 | Complexity: low | Confidence: reasoned
- Three clock criteria (zero parts): ① RCC registers HSERDY = 1 / PLL1RDY = 1 / SWS = PLL1 / CSS not triggered (proves the HSE oscillates); ② mean of 8192 IMU DRDY intervals 1250 µs ± 3 %, jitter σ < 5 µs (cross-checks against the IMU's own oscillator, also discriminating a relabelled 42688 with no 800 Hz step); ③ with USB enumerated, SOF interval 1000.0 µs ± 0.05 % (the board's only ppm-class reference, derived from the host crystal).
- Prevents: the HSE oscillating at the wrong frequency (wrong crystal or wrong CL) — RCC registers prove oscillation, not frequency; a wrong 25 MHz breaks USB enumeration, log timestamps and every integrated quantity at once
- New failure: criterion ② depends on the IMU's internal oscillator accuracy (a few percent), so a 3 % window only catches gross errors; criterion ③ is only available with USB present. With both unavailable only the RCC bits remain, which the report must mark DEGRADED, not PASS

### [AT-17] netlist
- Parts: 0 | Part numbers: 0 | Complexity: none | Confidence: reasoned
- Reject DESIGN_ASSURANCE's R-ARMBYP (RAW to PYRO_BUS through two 47k in series). Not implemented.
- Prevents: keeps the arming plug's status as a complete electrical break — a whole independent protection layer (layers, not margin, are what requirement 2 asks for). The zero-energy pyro-chain test capability R-ARMBYP offers is provided by FMEA H-1 for +3 parts without touching the break at all, and H-1 fails in the safe direction (BAT54A open → cold test reads all zeros → false "FET short" → scrub)
- New failure: none. But two entries in DESIGN_ASSURANCE §4.2's unpowered signature table were written assuming R-ARMBYP is fitted (J4.4–GND ≈ 10.5 kΩ, ARM_SENSE–GND becoming safety-critical); after the rejection they must revert to 11.0 kΩ and non-safety-critical, or the next reader will stop work over the wrong table

### [AT-18] component
- Parts: 0 | Part numbers: 0 | Complexity: none | Confidence: reasoned
- Reject 3V3 rail current sensing (shunt + current-sense amplifier). Not added. Replaced by two zero-part substitutes: AT-11's load-step transient test, and numeric criteria in the procedure for the bench supply's own ammeter (at 200 MHz / VOS3 idle with all sensors on and GPS locked, the 3V3 branch draws 128–184 mA; the whole board 75–120 mA at 8.4 V; outside that, stop).
- Prevents: putting two new solder joints in series with the MCU's only supply path — the same reason the frozen document deleted the 0 Ω sense jumper and DESIGN_ASSURANCE refused to add it back. The only extra fault current sensing catches (a partially shorted decoupling capacitor with the rail still in spec) costs heat and endurance, not the mission
- New failure: accepted blind spot: a partially shorted 3V3 decoupling capacitor (say 50 Ω) draws an extra 66 mA without moving the rail, invisible to firmware. It shortens endurance and warms the buck but changes no mission criterion. Caught once at assembly by the bench-supply current criterion

### [AT-19] component
- Parts: 0 | Part numbers: 0 | Complexity: none | Confidence: reasoned
- Reject the servo output readback network (4 × 100k from each SERVO*_OUT summed to one node + 1 × 100k to ground → one free ADC pin, 5 parts total). Not added.
- Prevents: bringing an off-board signal (the servo signal line) into a new ADC pin through 100k — when a J5 numbering error or harness chafe puts 8.4 V on a servo signal line, that path forward-injects about 50 µA into the pin, exactly the class of path this design keeps closing; and the candidate ADC pins PA4/PA5 have IINJ of 0/0 mA. Also, the servo channels already need one unavoidable manual step (sweep the fins to confirm the sign, the number-one killer), so automating the electrical half buys little
- New failure: accepted blind spot: an open 220R or a dead SRV05-4 channel is invisible to firmware. Covered by the unpowered signature table (each J5A pad reads 10.22 kΩ to ground = R24 + R28; nothing else on the connector reads that value) and the mandatory manual sweep. T-50 does register-level checks only and the report says honestly "no board-side electrical coverage"

### [AT-20] component
- Parts: 0 | Part numbers: 0 | Complexity: none | Confidence: reasoned
- Reject a BAT+ (upstream of the load switch) divider. Not added. Replaced by T-15's two-state reading: on USB power with the MCU alive, RAW ≤ 0.15 V with the switch open and 6.00–8.45 V with it closed.
- Prevents: a permanently live divider path — with the board off VDD = 0 while the node sits at 2.7 V, forward-injecting about 77 µA through the ADC pin's ESD structure into the unpowered VDD rail and holding the MCU in an undefined half-powered state; exactly the class the frozen document closed when it stopped taking the pyro bus from raw BAT, and a violation of the FT pins' own "no positive injection at all" rule. It also saves 57 µA of battery drain in storage
- New failure: accepted blind spot: with the switch open the battery is invisible to firmware, so when T-15 fails {flat battery / reed switch / J1 SW cold joint / Q1-Q2} remain indistinguishable. Closed by an instrument-free action — swap in a known-good battery pack and test again; failing twice localises to the board (switch terminal or load switch)

### [AT-21] firmware
- Parts: 0 | Part numbers: 0 | Complexity: none | Confidence: reasoned
- A mandatory note, checked in CI: LQFP100 pins 17/18 are the merged PC2_C/PC3_C pads, and SYSCFG_PMCR's PC2SO/PC3SO reset to 0 (analog switch closed = the pin is ordinary PC2/PC3 + ADC12_INP12/INP13). No initialisation code may set these two bits. ADC1 scans the six external channels (PC0/PC1/PC2/PC3/PC4/PC5), ADC3 the three internal ones.
- Prevents: copying an H7 template that sets PC2SO/PC3SO to 1 and silently disabling both new rail senses — the failure looks like a plausible number, not a missing reading
- New failure: no new hardware failure. It introduces a firmware convention that must be followed; the mitigation is reading back SYSCFG_PMCR at self-test start and writing its raw value into the report's raw field

### [AT-22] firmware
- Parts: 0 | Part numbers: 0 | Complexity: low | Confidence: unverified
- Battery / harness resistance trend criterion (zero parts): step all four servos together, record the RAW dip on PC4, compare with the baseline recorded at build, and warn on a change > 30 %. The absolute value is unavailable (no current sensing); the trend is.
- Prevents: battery ageing, loose screw terminals and degrading harness crimps — all three invisible in static voltage, while deployment shock pulls directly on the DB128V screw clamps (DESIGN_ASSURANCE lists the connector/harness interface as the board's number-two environmental enemy)
- New failure: the baseline was taken with one particular battery and is void after a pack change — the criterion must be stored per (board UID, battery pack ID) pair, or it produces floods of false warnings and people learn to ignore it. The servo step really moves the fins, so it must only run after confirming the fins are unobstructed

### [AT-23] test
- Parts: 0 | Part numbers: 0 | Complexity: low | Confidence: verified
- Pull-pin test and firmware latch (adopting DESIGN_ASSURANCE's ruling; no pin change): maintain pin_was_seen_installed, set only after PD14 has read low continuously for 500 ms; the READY gate requires the latch true and PD14 currently high. Automated part: after the agent prompts "pull the pin", poll; the criterion is a clean 0 → 1 transition within 50 ms with < 3 bounces.
- Prevents: the pull-pin interlock fails toward armed — open = 3.30 V = "pulled, permitted", so cold joints, broken wires and corrosion all read as permitted, and the final flight-enable interlock silently does not exist
- New failure: residual: a wire that breaks after boot but before the pin is pulled is still indistinguishable from a pull (a property of any pull-pin interlock). The operating cost is that the pin must be physically inserted before every power-up, or the board never reaches READY — exactly the discipline wanted. Must be paired with FMEA H-10 (BAT54S clamp), otherwise a pull-pin wire chafing onto 8.4 V lifts PD14 to 7.94 V, above the 7.3 V absolute limit
