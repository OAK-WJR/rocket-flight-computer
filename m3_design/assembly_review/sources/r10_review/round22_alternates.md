# R10 procurement alternates for U9 and U4 (round 22, board 5516eeec, commit ec8cb98)

Read-only research for the owner. Nothing here is adopted. Every BOM change below is a recommendation.
Labels: **Datasheet** (read this session, page given), **Live** (supplier figure with UTC time), **Calculation**,
**Inference** (not measured, not in a datasheet).

## 0. Summary

| Part | Rank | Candidate | Same land / pins | Live stock (UTC 2026-11-01) | Main change |
|---|---|---|---|---|---|
| U9 | 1 | **TPS259470ARPWR** (LCSC C3662799) | Yes. Same RPW0010A and same pin functions (FLT, AUXOFF, OVLO, ILM) | JLC 2547 in stock / 2349 orderable, min 1 (01:37Z); TI store 12 277 (01:39Z) | Auto-retry instead of latch-off, only after thermal shutdown or an ILM-pin fault |
| U9 | 2 | TPS259474LRPWR (C2864845) | Same land. Pin 3 is PG and pin 4 is PGTH (an input), not FLT | JLC 3597 / 3480, min 1 (01:37Z); TI store 98 180 (01:39Z) | Keeps latch-off, but it is a **circuit breaker**: any overcurrent after start-up trips it and it stays off. BAT_FAULT_N becomes a dead input |
| U9 | — | TPS259472x, TPS25946x | Same package, but not usable | — | 472x: pin 2 is OVCSEL, so no 9.8 V OVLO. 25946x: IN absolute minimum is −0.3 V, so no reverse-battery protection |
| U4 | 1 | **LSM6DSV320XTR** (C26633007; already the recorded alternate) | Yes. Same drawing DM01021587_2, pins, axes and all 285 register addresses | ST eStore "In stock" (~01:45Z); JLC 0 / −20 (01:39Z) | Consign it to JLC. Firmware rule unchanged (FS_XL_HG 001 / 010). Top 85 °C |
| U4 | 2 | **LSM6DSV80XTR** (C46898862) | Yes. Same drawing, pins (10 / 11 are NC) and axes. WHO_AM_I is also 0x73 | ST eStore "In stock", $8.31 at 1–4 (~01:45Z); JLC 0 / −3 (01:39Z) | Consign. Firmware may use only FS_XL_HG **001 (±64 g)**: code 010 means ±80 g here and ±128 g on the ISM. Gyro specs are typical only |
| U4 | — | LSM6DSV32X / LSM6DSV16X / ICM-45686 | Land-compatible (ICM is an Inference) | JLC 133 / 14 659 / 5181 orderable | All fail F2: no ≥ ±64 g channel. Firmware rewrite. Last resort only |

**Partial order:** placing U4 and U9 by hand after a DNP build is possible but a poor choice for these packages
(§3). Consigning franchised parts to JLC is better: JLC still places them, and the stock is now real for
TPS259470A / TPS259474L at TI and for LSM6DSV320X / LSM6DSV80X at ST.

Distributor coverage: DigiKey returned HTTP 403. Mouser, Arrow, Newark and Octopart timed out or returned 403.
The Chrome connector did not respond. **So no DigiKey, Mouser, Arrow, Avnet or Newark figure was obtained this
session.** Check them by hand before ordering. The DigiKey figures in the brief (TPS259470L 0, 3000 due 14-Dec-2026;
ISM6HG256X 0, 5000 due 22-Mar-2027; LSM6DSV320X 0, 24 weeks) are the caller's and were not re-checked.

---

## 1. U9: TPS259470LRPWR replacements

### 1.1 The board's U9 network (read from `m3.kicad_pcb` pad nets and `battery_entry.kicad_sch`)

| U9 pin | 470x function | Board net / part |
|---|---|---|
| 1 EN/UVLO | EN/UVLO | BAT_ENABLE: R80 + R165 470 kΩ each (through J400) from BAT_IN, R81 300 kΩ and C87 220 nF to GND |
| 2 OVLO | OVLO | BAT_OVLO: R82 2 MΩ from BAT_IN, R83 280 kΩ to GND. Calculation: 1.20 V × 2280 / 280 = 9.77 V nominal OVLO |
| 3 AUXOFF | AUXOFF (open drain) | Not connected |
| 4 FLT | FLT (open drain) | BAT_FAULT_N: R89 10 kΩ to 3V3, to MCU PA5 (EXTI5) |
| 5 / 6 | IN / OUT | BAT_IN (fed through C88) / RAW_PROTECTED (C82, D9, R92 3.3 kΩ bleed) |
| 7 DVDT | DVDT | C81 4.7 nF |
| 8 | GND | GND |
| 9 ILM | ILM | R84 750 Ω. Datasheet: 4.452 A typical, 3.960–4.840 A ([SLVSFC9C p9](https://www.ti.com/lit/ds/symlink/tps25947.pdf)); R_ILM = 3334 / I_LIM (Eq. 7, p32) |
| 10 ITIMER | ITIMER | Not connected (open = minimum blanking time; pp31, 33) |

### 1.2 TPS25947 family ([SLVSFC9C, Rev C, May 2026](https://www.ti.com/lit/ds/symlink/tps25947.pdf))

Datasheet facts that hold for **all six** TPS25947 variants:
- Same RPW0010A package. TI's orderable addendum (pp68–71) lists all six as VQFN-HR (RPW), 10 pins, 3000-piece reel, pin-1 quadrant Q2. The drawing is pp72–74. So the land and the CPL rotation are the same (the rotation is an Inference until JLC's placement preview confirms it).
- Same ratings. IN is rated max(−15 V, VOUT − 21 V) to 28 V, with input slew ≤ 100 V/µs rising and ≤ 10 V/µs falling (p7). The reverse hot-plug model therefore carries over.
- Same thresholds. EN/UVLO rises at 1.183 / 1.20 / 1.223 V and falls at 1.076 / 1.09 / 1.116 V. VSD(F) is 0.45 V min, 0.74 V typical. EN leakage is ±0.1 µA. OVLO thresholds are the same as EN's (p9).
- Same current limit with R84 = 750 Ω: 3.96–4.84 A (p9). Same 28.2 mΩ typical / 45 mΩ max on-resistance (p9). Same IMON gain, 165–200 µA/A on ILM (p10).
- Same reverse current blocking: −36.45…−22.3 mV in, 83–125 mV out (p10). Same TSD, 154 °C with 10 °C hysteresis (p10).

| Variant | Pin 2 | Pin 3 | Pin 4 | Overcurrent response | After a fault (p4 table) |
|---|---|---|---|---|---|
| 470L (fitted) | OVLO | AUXOFF | FLT | Active current limit (p31–32) | Latch-off |
| **470A** | OVLO | AUXOFF | FLT | Active current limit | Auto-retry, tRST = 110 ms (p11) |
| 474L | OVLO | PG | PGTH (input) | Circuit breaker: off after ITIMER (p30–31) | Latch-off |
| 474A | OVLO | PG | PGTH | Circuit breaker | Auto-retry |
| 472L / 472A | OVCSEL (3.8 / 5.7 / 13.8 V clamp) | PG | PGTH | Active current limit | Latch / retry |

What is latched (Table 7-3, p38). In the 470x, a persistent overcurrent is **not** latched: the device keeps
current-limiting and FLT goes low. Only over-temperature and an ILM-pin short latch. So the 470L "latch-off" is
"current-limit until thermal shutdown, then stay off". To clear a latched fault, VIN must go to 0 V or EN must go
below VSD(F). Pulling EN just below UVLO does nothing (p38).

### 1.3 Candidate 1: TPS259470ARPWR (auto-retry)

- **Pins:** identical to the fitted part (Table 5-1, pp5–6). No BOM value or copper change apart from U9's own fields.
- **EN / UVLO, OVLO, ILIM, IMON, reverse blocking, voltage ratings:** identical (p9–p10). D-R19-10 and D-R20-11 hold unchanged: turn-on 30–129 ms; drop-out immunity 10.6 / 20.5 / 26.4 ms at 6.0 / 7.4 / 8.4 V, 8.5 ms at 5.73 V; the 5.92 V pack floor for 10 ms. These depend only on the UVLO thresholds and the EN leakage, which are the same.
- **Shorted load (difference).** Both variants current-limit at 3.96–4.84 A, with lower foldback below VOUT 1.9 V (p10, p32), until TSD.
  - 470L stays off until J400 is opened.
  - 470A cools by 10 °C, waits 110 ms and turns on again (p37–38). It repeats this cycle while J400 stays closed. RAW_PROTECTED, and with it the logic, comes up and drops out once per cycle, so the MCU reboots repeatedly and FLT pulses low. The pack sees a low-duty pulse of about 4.4 A (Inference: TSD is reached in ms against the 110 ms off time).
  - The fire path is unaffected: Q120's drain is on BAT_IN, ahead of U9. Firmware refuses to fire without a latched lift-off, and lift-off detection restarts on each reboot.
- **Transient short or chafe (difference, in 470A's favour).** 470L kills the primary computer for the rest of the flight. 470A brings it back after about 110 ms plus the dVdt ramp and the boot time (Inference). F6 says no failure may "repeatedly reset". A persistent RAW_PROTECTED short already ends the primary computer's flight with either variant. Only the pad behaviour differs: a board cycling about every 0.1 s instead of a dead board.
- **EN switch-timing network.** No threshold change. One difference: the latch-off part needs EN below VSD(F) to clear a latch. Calculation for J400 opened, EN discharged through R81 only (R81 ±1 %, C87 0.72–1.27 × 220 nF, +0.1 µA leakage held at the worst sign): EN falls from 1.45 / 1.79 / 2.03 V to 0.45 V in **57–103 / 67–121 / 73–132 ms** at 6.0 / 7.4 / 8.4 V. M3_R4's "hold the switch open ≥ 1.5 s after a fault" (written for the old 2.2 µF C87) still covers it. With 470A that wait is not needed, because the part clears its own fault. Opening J400 still turns the board off normally.
- **Stock (Live):** JLC C3662799 2547 in stock, 2349 orderable, minimum 1, $1.2943 (2026-11-01T01:37Z). TI store 12 277 (01:39Z, `ti.com/storeservices/cart/opninventory`). JLC labels its package "QFN-10(2x2)" where the fitted part says "VQFN-10-HR(2x2)". Check JLC's EasyEDA footprint and rotation for C3662799 before relying on it.
- **Risks:** repeated reboots into a hard short; a pad-side short shows up as a cycling board, not a dead one. The owner must accept that "latch-off" is gone.

### 1.4 Candidate 2: TPS259474LRPWR (latch-off circuit breaker)

- **Pins:** pins 1, 2 and 5–10 are the same. **Pin 3 is PG** (open drain). It is NC on the board, so that is harmless.
- **Pin 4 is PGTH**, an analog input (rated ≤ 5 V; absolute max 6.5 V; leakage −0.1…+0.3 µA; p7–p10). On the board it sits on BAT_FAULT_N, pulled to 3V3 by R89. That is electrically safe, but **the MCU loses the fault flag**: PA5 just reads 3V3. Firmware must ignore PA5, and the binding note and pin table must say so.
- **Overcurrent:** circuit breaker. With ITIMER open, the HFET turns off at minimum delay once the current exceeds I_LIM and **latches** (p30–31, Table 7-3). The start-up inrush is still actively limited (Note 3, p33).
- **Main risk (Inference, not modelled).** The board expects battery-contact interruptions (M3_R10 "battery-break ride-through": ports on 0.55–1.0 ms). During a break, VIN and VOUT sag together through the 28 mΩ switch, so the part does not see a start-up. When the pack contact returns, the recharge of C84 (470 µF) and the rest of RAW_PROTECTED exceeds 4.45 A at once. The 470x simply limits this (about 0.4 ms for 500 µF and 3.6 V, Calculation). **The 474L would trip and stay off for the rest of the flight.** Blue Jay remains the only deployment. No ITIMER capacitor can be added without copper (pin 10 has no pad network).
- **EN network:** thresholds are identical, so the timing is unchanged. Clearing the latch has the same ≥ ~0.13 s J400-open requirement as the 470L.
- **Stock (Live):** JLC C2864845 3597 in stock / 3480 orderable, minimum 1, $1.2877 (01:37Z). TI store 98 180 (01:39Z).

### 1.5 Rejected

- **TPS259472L/A** (JLC 39 / 37 and 1924 / 1836; TI 16 817 / 91 395). Pin 2 is OVCSEL, which has only three valid states: GND, open, or 390 kΩ (p9). The R82 / R83 divider gives an undefined setting. The best BOM-only fix (DNP R82, R83 = 390 kΩ) gives a 13.2–14.5 V output clamp (p9) instead of the 9.77 V lockout, so a wrong 3S pack (12.6 V) would pass through. Pin 4 is PGTH as in the 474. Not acceptable.
- **TPS25946x** ([SLVSGA8B](https://www.ti.com/lit/ds/symlink/tps25946.pdf)). Same RPW pinout (p4), but IN is rated −0.3 V minimum (p5): **no reverse-battery protection**. Its FETs are also bidirectional when on, so C84 would back-feed the input. Rejected.
- **TPS25948x**: DSBGA / WCSP-12, a different land. **TPS2595x**: WSON-8. **TPS25982**: QFN-24.

### 1.6 Ranked U9 recommendation

1. **TPS259470ARPWR**, if the owner accepts auto-retry after thermal shutdown. It is the only option with identical protection, current-limit and FLT behaviour, and it is in stock at JLC and TI.
2. **Wait for or consign TPS259470LRPWR.** The TI store had 0 at 01:39Z. Use only TI or franchised stock. Broker stock has an authenticity risk for a power-path part.
3. **TPS259474LRPWR**, only if latch-off is mandatory and the nuisance-trip risk above is accepted. Bench-test a 1 ms pack interruption under load first.

---

## 2. U4: ISM6HG256XTR replacements

### 2.1 Flight loads (Inference: no K850DM / L1000W mass budget exists yet, VEHICLE.md "Mass and CG")

Motor data (thrustcurve.org, read 2026-11-01):
- K850DM: 1869 Ns, 922 N average, 1094 N max, 2.0 s burn, 2041 g loaded, 1224 g propellant.
- L1000W: 2714 Ns, 1000 N average, 1261 N max, 2.7 s burn, 2194 g loaded, 1400 g propellant.

Vehicle mass: the earlier L1000W estimate is 3.7–4.9 kg at liftoff (REQUIREMENTS line 32). That gives 1.5–2.7 kg without the motor.

| Case | Mass | Specific force |
|---|---|---|
| L1000W, burnout | 2.3–3.5 kg | 1261 N max thrust → 36.7–**55.9 g** (upper bound: max thrust at burnout mass, no drag) |
| K850DM, burnout | 2.32–3.52 kg | 1094 N → 31.7–48.1 g |
| L1000W, average over the burn | — | about 25–35 g, consistent with the recorded 28–37 g |
| Coast at Mach 1.9 (~650 m/s, Cd 0.45–0.6, ρ 1.0–1.1 kg/m³, A = 2.62 × 10⁻³ m²) | burnout | about −11 to −16 g |

What that means for each channel:
- The **±16 g low-g channel saturates through the whole boost on every candidate.** Even the liftoff ratio, 922 N / 4.74 kg, is 19.8 g. It may also touch −16 g just after burnout on flight 2. The high-g channel must carry boost. That is already the design (F2).
- A **±64 g** high-g range clears the 55.9 g upper bound by 1.14×. ±80 g gives 1.43× and ±128 g gives 2.3×. F2's stated floor is ±64 g.
- Gyro: F1 needs ±4000 dps. All ST options below meet it.

### 2.2 Candidate 1: LSM6DSV320XTR (recorded consigned alternate, D-R19-11)

- **Land and pins:** [DS14623 Rev 1](https://www.st.com/resource/en/datasheet/lsm6dsv320x.pdf) (copy obtained through JLC C26633007). The drawing is DM01021587_2, LGA-14L 2.5 × 3.0 × 0.83 mm, 14 × 0.475 × 0.25 mm pads, p187. The pin map and axis figure are on p9 (pins 10 / 11 are SDO_aux / OCS_aux, unconnected on the board). These match the ISM6HG256X per D-R19-11.
- **Registers:** ST's `lsm6dsv320x-pid` and `ism6hg256x-pid` headers (GitHub, master) share all 285 register addresses with no difference, and WHO_AM_I is 0x73 on both. FS_XL_HG codes 001 = ±64 g and 010 = ±128 g are the same on both, so the existing binding-note rule holds.
- **Electrical:** gyro ±4000 dps; low-g ±16 g; high-g up to ±320 g. Zero-rate ±1 dps and ±0.006 dps/°C, **typical only** (DS14623 Table 3). The F1 budget currently uses the ISM's guaranteed maxima. **Top is −40…+85 °C** (the ISM is −40…+105 °C); the bay limit used elsewhere is 70 °C.
- **Stock:**
  - Live: ST eStore "In stock", $10.06 at 1–4 (~01:45Z; no quantity shown).
  - Live: JLC 0 in stock, −20 orderable (01:39Z).
  - Brief (not re-checked): DigiKey 0, 24-week lead time.
- **Change:** BOM fields only (Value / Manufacturer Part / LCSC → C26633007), as a consigned part. Firmware: none beyond the existing rule. Records: D-R19-11 and the F1 budget (typical vs maximum specifications).

### 2.3 Candidate 2: LSM6DSV80XTR

- **Datasheet:** [DS14764 Rev 1, March 2025](https://www.st.com/resource/en/datasheet/lsm6dsv80x.pdf), read from JLC's copy for C46898862.
- **Land:** p159, the same drawing DM01021587_2: 2.50 × 3.00 × 0.83 mm and 14 × 0.475 × 0.25 mm pads, identical to the 320X's p187.
- **Pins:** Table 2, p11.

| Pin | LSM6DSV80X | Board | OK? |
|---|---|---|---|
| 1 | SDO / TA0 | SPI1_MISO | yes |
| 2 | SDx: "Connect to VDDIO or GND" | GND | yes |
| 3 | SCx: same | GND | yes |
| 4 | INT1 | IMU_INT1 → PE1 | yes |
| 5 | VDDIO | 3V3A | yes (1.08–3.6 V, p15) |
| 6, 7 | GND | GND | yes |
| 8 | VDD | 3V3A | yes (1.71–3.6 V, p15) |
| 9 | INT2 | NC | yes |
| 10, 11 | NC: "Leave pin electrically unconnected and soldered to PCB" | unconnected | yes |
| 12 | CS | IMU_CS | yes |
| 13 | SCL / SPC | SPI1_SCK | yes |
| 14 | SDA / SDI | SPI1_MOSI | yes |

- **Axes:** Figure 5 (p9) is identical to the 320X's p9, so roll stays −gyro_Y.
- **Interface:** SPI 4-wire, modes 0 and 3, ≤ 10 MHz (p17). IF_CFG H_LACTIVE / PP_OD default to active-high push-pull (p49), so the INT1 configuration is unchanged.
- **Ranges** (p12): gyro ±250…±4000 dps; low-g ±2…±16 g; **high-g ±32 / ±64 / ±80 g**.
- **Register compatibility.** ST's `lsm6dsv80x-pid` header shares 239 register addresses with the ISM header, all at the same addresses. It lacks only the OIS / EIS / IF2 auxiliary-interface registers. The high-g outputs are at the same 0x34–0x39 (named UI_OUTx_A_HG, without "OIS"), and CTRL1_XL_HG is the same 0x4E layout. WHO_AM_I is **0x73** (p55), the same as the ISM and the 320X, so firmware **cannot tell them apart**.
- **FS_XL_HG** (Table 138, p81): 000 = 32 g, 001 = 64 g, **010 = 80 g**, 011 / 100 reserved. The binding note's "use 001 or 010" is therefore **unsafe**: with 010, firmware would scale ±80 g data as ±128 g, a 1.6× error. The rule must become **"use only 001 (±64 g)"**, which means the same on all three parts. High-g ODR 480 Hz–7.68 kHz (Table 137, p81).
- **Other differences:**
  - Gyro zero-rate ±1 dps and ±0.006 dps/°C, typical only (p12).
  - Top −40…+85 °C (p15).
  - Gyro Ton 40 ms (p15), the same rule as now.
  - 20 000 g for 0.2 ms absolute (p20).
- **Stock:**
  - Live: ST eStore "In stock", $8.31 at 1–4 (~01:45Z; no quantity shown).
  - Live: JLC C46898862 0 in stock, −3 orderable, minimum 2 (01:39Z).
- **Change:**
  - BOM fields (C46898862) and `tools/verified_part_metadata.json` / `tools/jlc_easyeda/pads.json` entries.
  - Binding-note IMU text: 001 only; WHO_AM_I cannot identify the part.
  - F1 budget note (typical specifications); F2 margin 1.14× on the 55.9 g bound.
  - A new D-entry beside D-R19-11.

### 2.4 Degraded fallbacks (fail F2; listed for completeness)

| Part | Land | Ranges | Registers | JLC (01:39Z) |
|---|---|---|---|---|
| LSM6DSV32XTR C22461202 | Same ST LGA-14L family (drawing not re-read) | ±32 g, ±4000 dps, **no high-g channel** | WHO_AM_I 0x70; no CTRL1_XL_HG; different FS codes (4000 dps = 0xC) | 339 / 133 |
| LSM6DSV16XTR C5267406 | Same | ±16 g, ±4000 dps | As 32X | 15 193 / 14 659 |
| TDK ICM-45686 C22459454 | Earlier boards used it on this land. CIRCUIT_REVIEW lists pins 2 / 3 / 7 / 10 / 11 as RESV (NC, VDDIO or GND): Inference, DS-000489 not re-read here | ±32 g, ±4000 dps | Completely different map and axes | 5295 / 5181 |

All of them clip during boost (upper bound 45–56 g). Use one only with a separate high-g accelerometer, which would be a copper change. Not recommended.

### 2.5 Ranked U4 recommendation

1. **LSM6DSV320XTR, consigned** (ST eStore stock). It is already reviewed, has full register identity, and needs no firmware rule change.
2. **LSM6DSV80XTR, consigned** (ST eStore stock; cheapest). Firmware must use FS_XL_HG = 001 only.
3. ISM6HG256XTR: take the 2 orderable at JLC and consign 3 more if any franchised stock appears. Otherwise ST and DigiKey cannot supply it until about March 2027 (brief).

Common risk: none of these is in JLC's own stock, so each needs a consignment purchase. ST eStore order limits and real quantities were not visible. Confirm in the cart.

---

## 3. Partial JLC order with U4 / U9 left unfitted (DNP), then hand-fitted

JLC assembles whatever is in the uploaded BOM / CPL. Omitting U4 and U9 is mechanically easy. Hand-fitting them is
the hard part:

- **U9 (RPW VQFN-HR, 2 × 2 mm, 0.45 mm pitch, two long IN / OUT bars, no exposed pad; [SLVSFC9C pp72–74](https://www.ti.com/lit/ds/symlink/tps25947.pdf)), on the bottom at B(18.5, 81.6).**
  - Needs a mini-stencil or careful paste and hot air on an already double-side-reflowed board. Top parts opposite U9 can reflow too.
  - It is the battery power path and reverse-polarity element. A bad IN / OUT joint is a flight-critical fault that a visual check cannot fully see.
  - Feasible for a skilled person with a preheater. Not preferred.
- **U4 (LGA-14L 2.5 × 3 mm, 0.5 mm pitch, 0.475 × 0.25 mm pads, no side fillets), on the bottom at B(17, 45.9).**
  - Joints cannot be inspected without X-ray. Hand reflow risks shorts and opens, and adds stress or offset to a MEMS part that already has an open first-article qualification (copper under the body departs from ST TN1383).
  - A functional check (WHO_AM_I, self-test, bias) finds opens but not marginal joints.
  - **Not recommended.**
- **Practical alternative:** JLC parts consignment (buy from the TI store / ST eStore, ship to JLC's parts inventory before ordering). JLC then reflows them with everything else. This adds lead time for shipping and receipt (Inference: about 1–2 weeks). It is the route R20-BOM-01 already names.
- If DNP is used anyway, the board is still USB-powerable for bench work without U9: U10 / U11 feed the logic. Without U4 it cannot fly.

---

## 4. What adoption would change (for whichever option the owner picks)

- **Schematic fields** in the KiCad project (`battery_entry.kicad_sch` U9 or `sensors.kicad_sch` U4): Value / Manufacturer Part / LCSC, kept consistent per AGENTS §3, with the U9 sheet note text ("TPS259470L … thermal latch").
  - Field changes propagate to the PCB, so the **board hash changes** and `m3_firmware/assembly_binding.py` provenance needs refreshing (AGENTS §3).
- **Tools:**
  - `tools/verified_part_metadata.json`, `tools/jlc_corrections.json`, `tools/jlc_easyeda/pads.json` (new EasyEDA footprint and rotation entry), `tools/jlc_easyeda/supplier_snapshot.json`.
  - `m3_design/check_actuators.py` (references C3662793) and `m3_design/r10_sch_check.py` (references C51931514).
  - Re-run `m3_design/r10_fab.sh`, then the cost and stock checks.
- **Firmware / binding note** (`r10_binding_note.json`, pin table):
  - U9 = 474L: PA5 / BAT_FAULT_N carries no information.
  - U9 = 470A: FLT pulses during auto-retry.
  - U4 = 80X: FS_XL_HG 001 only.
- **Records:**
  - New D-R22 entries.
  - REQUIREMENTS F1 (typical vs maximum gyro specifications; 85 °C), F2 (margin), F9 (U9 part and fault behaviour), M1 (stock text).
  - M3_R10 "Cost and stock", ORDERING §8.1 table, R10_VALIDATION owner table item 14, and the AGENTS.md block table rows for U9 / U4.

## 5. Sources and check times (UTC)

- JLC component API (the `tools/jlc_stock.py` endpoint), keyword queries:
  - TPS2594x / TPS2595 / TPS25982: 2026-11-01T01:37Z.
  - IMUs: 01:39Z.
- TI store inventory endpoint, 01:39Z: TPS259470LRPWR 0, TPS259470ARPWR 12 277, TPS259474LRPWR 98 180, TPS259474ARPWR 90, TPS259472LRPWR 16 817, TPS259472ARPWR 91 395.
- ST eStore product pages, ~01:45Z: LSM6DSV80XTR in stock; LSM6DSV320XTR in stock; ISM6HG256XTR out of stock; ISM6HGK256XTR "Coming soon" (another ±16 / ±256 g industrial part, not orderable).
- Datasheets:
  - [TPS25947 SLVSFC9C](https://www.ti.com/lit/ds/symlink/tps25947.pdf), pp4–11, 30–38, 68–74.
  - [TPS25946 SLVSGA8B](https://www.ti.com/lit/ds/symlink/tps25946.pdf), pp1, 4–6.
  - LSM6DSV80X DS14764 Rev 1, pp9, 11, 12, 15, 17, 20, 49, 55, 81, 159.
  - LSM6DSV320X DS14623 Rev 1, pp9, 187.
  - The ST copies came through JLC's datasheet links because st.com timed out.
- ST register headers: github.com/STMicroelectronics/{ism6hg256x,lsm6dsv320x,lsm6dsv80x,lsm6dsv32x,lsm6dsv16x}-pid.
- Motors: thrustcurve.org K850DM and HP-L1000W pages.
- Not reached: DigiKey (403), Mouser, Arrow, Newark, Octopart (timeout / 403), Avnet (not tried); the Chrome connector did not respond.
