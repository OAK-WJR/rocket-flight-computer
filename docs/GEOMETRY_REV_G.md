# Rocket Flight Computer v1 — Geometry Re-freeze (REV-G, 2026-09-03)

> This document supersedes **every geometry-related item** in `ROCKET_FC_FROZEN_DESIGN.md` (outline, zoning, connector positions, height budget, copper widths, mounting holes). The electrical architecture, pin table, netlist and firmware constraints still follow the original document, patched only by the list in §8.
> Wherever a checker overturned an analysis agent, the checker wins; that is already merged below.
> Historical note: the current single-board M3 is 46 × 186 mm (see `../STATUS.md`); the 46 mm width and the envelope model below still apply.

---

## 1. Ruling

**A 40 mm-wide board can close, but 40 mm itself is the product of a wrong model — formally frozen at 46.0 × 120.0 mm.**

The brief's 40 mm came from the naive inscribed-rectangle model (`2·√(27.33²−25²) = 22.08` tall, minus sled 3.0 + PCB 1.6 + LiPo 17.0 = 21.6, leaving only 0.48 mm). That model forces a 17 mm-thick battery, a 40 mm sled and the top-side parts into the same rectangle; three of the four analysis agents' checkers independently found it self-contradictory. Recomputing with the chord-height model (the battery sits at its own best height): the lower edge of a 35 mm-wide battery lands at `y = −√(26.83²−17.5²) = −20.337`, so the PCB top face is at `−20.337 + 21.6 = +1.263`, and top-side clearance is `h(x) = √(719.8489−x²) − 1.263`, **independent of board width**. What actually limits board width is the tallest edge component: with the true bevelled outline from the DORABO drawing (the 14.00 mm top face is set back 2.61 mm from the wire-entry face), the width limit is `2·(√(719.8489−15.763²) + 2.61) = 48.64 mm`; with the most pessimistic straight-walled box model it is 43.42 mm.

Chose **46.0 mm**: 2.64 mm of model margin against the true outline, and it also (a) lifts the GNSS ground plane from u-blox's stated 40 × 40 mm degradation threshold (zero margin) to 15 % above it, (b) turns the frozen document's own 42 mm MCU band (LQFP100 21.0 + flash 10.0 + header lane) from 2.0 mm over to 3.4 mm spare, and (c) makes the nose-end M3 corner holes legal. **The only thing that still does not close is "4-pos terminal + 3×4 servo header side by side on the end edge"** — it is 1.99 mm over under any width assumption, and the servo header must sit near the centreline anyway (see §7), so moving it inboard to the centreline is the right choice, not a concession.

---

## 2. Outline

| Item | Value | Basis |
|---|---|---|
| Outline | **46.0 (x) × 120.0 (y) mm**, corner radius R1.0 | §1 ruling; length solved from nose-corner hole legality, below |
| Origin | **x = 0 = port long edge, x = 46 = starboard long edge; y = 0 = aft (battery) end edge, y = 120 = forward (GNSS) end edge.** Top face = component side | — |
| Stackup | 4 layers, 1.6 mm, **1 oz outer / 1 oz inner** (unchanged) | Frozen document §2.1 |
| Single-sided assembly | Everything on top; the bottom has only L4 copper, silkscreen and through-hole pin tails | JLCPCB Economic PCBA = single-sided placement (re-checked 2026-09-03). What actually forbids the bottom is not the JLC tier but the 3.0 mm sled gap |
| Copper pull-back from board edge | ≥ 0.3 mm (JLC minimum 0.2 mm, but ±0.2 mm routing tolerance would eat it) → actual pour width 45.4 mm | jlcpcb.com/capabilities/pcb-capabilities |

### 2.1 M3 mounting holes

Hole Ø3.2 (ISO 273 fine); DIN 125A washer OD 7.0 → **obstacle radius 3.5 mm** (larger than an M3 hex nut across corners, 6.35, or a pan head, ~6.0). Hole centres inset **4.0 mm** (washer 0.5 mm from the edge, FR4 web 4.0 − 1.6 = 2.40 mm).

| Ref | Centre (x, y) | Keep-out | Notes |
|---|---|---|---|
| H1 | **(4.000, 4.000)** | Circle R = 3.5 mm | Aft port corner |
| H2 | **(42.000, 4.000)** | R = 3.5 mm | Aft starboard corner |
| H3 | **(4.000, 116.000)** | R = 3.5 mm | Forward port corner, **nylon hardware** |
| H4 | **(42.000, 116.000)** | R = 3.5 mm | Forward starboard corner, **nylon hardware** |

- Corner keep-out reach along the end edge = 4.0 + 3.5 = **7.50 mm**; usable span of the aft edge = 46 − 2 × 7.50 = **31.00 mm**.
- **Board length solved from H3/H4**: module corner at (15.25, 107.5); requiring the washer edge ≥ 10 mm from the module, i.e. hole centre ≥ 13.5 mm away → `(L−4−107.5)² ≥ 13.5² − 11.25² = 55.688` → `L ≥ 118.962`. Take **L = 120.0**, giving `√(11.25² + 8.5²) = 14.100 mm` and **10.600 mm** washer-edge clearance, with only **1.04 mm** of length margin.
- This supersedes frozen §2.1 "move the two nose-end holes to the long edges at x = 3.5, y ≈ 94/99" — on a 46 mm board those holes are only 11.75 mm (centre) / 8.25 mm (washer edge) from the module, non-compliant under a strict reading, and they degrade the mounting rectangle into single-edge support with a 36 mm overhanging GNSS end.
- **H3/H4 use nylon M3 pan heads + nylon washers** (head height ~2.0 mm, non-conductive, not a "tall part"). This satisfies both conflicting readings of the u-blox integration manual, §4.3 (parts with h > 3 mm ≥ 10 mm from the antenna) and §4.4 (any object ≥ 10 mm); the cost is one different bag of fasteners.

---

## 3. Perimeter allocation

All connector dimensions are taken at **maximum material** (DORABO drawing, GB/T 14486-2008 general tolerances: 10–30 mm → ±0.50, 30–60 mm → ±0.70) **including the 0.57 mm dovetail** (checker measurement: the dovetail lies outside the `N × 5.08` dimension line; front view 25 px / 44.36 px·mm⁻¹ = 0.564 mm, matching the drawing's 0.57).

DB128V-5.08 body length = **exactly N × 5.08** (4P = 20.32, 6P = 30.48). Frozen §4.5's "body length unverified / draw with conservative 5.08N + 2.54 bound" is **closed**; the MKDS bound does not apply. The same drawing confirms: body depth 10.20, pin row 5.00 from the wire-entry face, 14.00 tall on the board, PCB hole Ø1.60, pin 0.80 × 1.00, tail 3.50 ± 0.30, strip length 6–7, M2.5 / 0.4 N·m, −40…+105 °C, UL group B 16 A/300 V, IEC 24 A, 22–12 AWG.

### 3.1 J-BAT — DB128V-5.08-4P (C2915641), aft end edge

```
Body length envelope = 20.32 + 0.50 (tolerance) + 0.57 (dovetail) = 21.39 ~ 21.59 (max material 21.59)
Usable span 31.00 − 21.59 = 9.41 mm → 4.705 mm per side
```

| Item | Value |
|---|---|
| Body | **x 12.205 … 33.795** (centred on x = 23.000, dovetail toward +x), **y 0.000 … 10.700** |
| Pins | y = **5.000**; x = **15.380 / 20.460 / 25.540 / 30.620** (5.08 pitch, 15.24 span centred), hole Ø1.60 |
| Nets (port → starboard) | **SW / BAT+ / BAT− / SW** |
| Clearance to corner keep-outs | **4.705 mm** per side (4.135 mm on the dovetail side) |
| Height | 14.00 (max 14.50); ceiling there `h(10.795) = √(719.8489 − 116.53) − 1.263 = 23.300` → **8.80 mm spare** |
| Current | 4 × 1.916 + 0.2 = **7.862 A / 16 A = 49.1 %** |

> This net order **supersedes** the frozen BAT+/BAT−/SW/SW: BAT± adjacent and straddling the centreline lets the RAW pour fan out symmetrically to the starboard servo corner and the port pyro corner with minimum loop area; SW carries only 76.4 µA (8.4 V ÷ 110 kΩ), so its position is free.

### 3.2 J-SERVO — HX PZ2.54-3×4P ZZ (C32713291), **moved inboard to the board centreline** (not on the end edge)

```
End-edge side-by-side check: 31.00 usable vs 21.59 (4P) + 1.00 (gap) + 10.40 (header lane) = 32.99 → 1.99 mm over
Even with the nominal body, zero gap and the most aggressive 3.5 mm inset (33.00 usable) it needs 30.72, leaving 2.28,
but then the header centre is ≥ 10 mm from the board centreline, outside the ±5.13 mm placement window below → no solution.
```

| Item | Value |
|---|---|
| Lane | **x 17.800 … 28.200** (10.40; four 0.1" crimp housings side by side are 4 × 2.54 = 10.16, 0.20 wider than the body, so the lane is drawn at 10.4), **y 12.400 … 20.400** (8.00) |
| Body | 10.16 × 7.62 (**conservatively the nominal 2.54 grid**; the 7-page LCSC PDF is an approval spec with no dimension drawing, so 9.96 × 7.50 is unverified) |
| Pins | Columns x = **19.190 / 21.730 / 24.270 / 26.810**; rows y = **13.860 / 16.400 / 18.940**, hole Ø1.02 |
| Row assignment | y = 13.860 **GND** (shortest return straight to BAT−) / y = 16.400 **RAW** / y = 18.940 **SIG** (toward the MCU) |
| Spacing | **1.70 mm** from the J-BAT body (y = 10.70); **2.10 mm** from the J-ARM body (x = 15.70) |
| Hard placement rule | With servo plugs inserted and wires bent 90° it needs **23.50 mm** (2.50 insulator + 14.00 ± 0.25 crimp housing + ~7.0 bend). Solving `√(719.8489 − x²) − 1.263 ≥ 23.50` → **\|x − 23\| ≤ 10.327 mm**; the housing block itself is ±5.20 → **the header centre must lie in x ∈ [17.87, 28.13]**. Current centre x = 23.000, 5.13 mm spare each side |
| Clearance | There `h(5.2) = √692.8089 − 1.263 = 25.058` vs 23.50 needed → **1.55 mm spare** (**the tightest height item on the board**) |
| Current | One servo per column, **1.916 A / 3 A = 63.9 %** per pin |

**Straight vs right-angle pins, decided by geometry rather than supply**: a right-angle header's crimp housings lie flat and stick out past the long edge by the full 14.00 mm housing length, while the radial space outside a 46 mm board's long edge, `√(719.8489 − (1.263 + h)²) − 23`, is only **3.80 mm** at board level, 2.15 mm at 8 mm height and already negative at 14 mm — **right-angle on the long edge is geometrically impossible**; right-angle on the end edge has no axial limit but the end edge is already full with J-BAT. The frozen document reached the correct straight-pin conclusion on the grounds that "every right-angle 3×4 on LCSC is 0 stock / MOQ 300–442", but **the reason must be geometry**, otherwise a restock one day would silently overturn it.

### 3.3 J-ARM — DB128V-5.08-6P (C2915642), port long edge, **inset 5.00 mm**

```
Body length envelope = 30.48 + 0.70 (tolerance) + 0.57 (dovetail) = 31.75 ~ 31.95 (take 31.95)
Start y = 8.500 (H1 washer y upper bound 7.500 + 1.000 gap) → end y = 40.450
```

| Item | Value |
|---|---|
| Body | **x 5.000 … 15.700** (depth 10.70, wire-entry face at x = 5.000, wires exit toward −x), **y 8.500 … 40.450** |
| Pins | x = **10.000**; y = **11.040 / 16.120 / 21.200 / 26.280 / 31.360 / 36.440** |
| Nets (aft → forward) | **PYRO1_B / PYRO1_A / PYRO2_B / PYRO2_A / ARM_A / ARM_B** |
| Height check | Top outer corner at \|x − 23\| = 18.00 − 2.61 = **15.39**, height 1.263 + 14.50 = 15.763 → radius `√(15.39² + 15.763²) = 22.03` vs R_eff 26.83 → **4.80 mm spare** |
| Wire-exit check | Wire axis height **2.8–4.9 mm** (read off the drawing's front-view scale, not a dimensioned value; the dimensioned hole is only 1.31 mm tall and is the clamp position, not the opening). Worst case 4.9: `√(719.8489 − (1.263 + 4.9)²) − 18 = 26.113 − 18 = 8.113 mm`; a 22 AWG (≈ 1.7 OD) 90° bend at 4 mm radius needs 4.85 → **3.26 mm spare**; at 5 mm radius needs 5.85 → 2.26 mm spare |
| Current | 4.0–9.84 A per channel, ≤ 20 ms, capped by the external 5 A fuse; 16 A UL / 24 A IEC → **pass** (three earlier connector audits missed this item) |

> **The 5.00 mm inset is a hard requirement, not an option.** Flush with the edge, the radial room at the wire exit is only `√(719.8489 − (1.263 + 4.9)²) − 23 = 3.11 mm`, not enough for the bend. Wires exit **above** the board face, so the strip outside the board is no obstacle; every millimetre of inset buys a millimetre of bend room. The cost is 5.00 mm of board width, taken out of Z2's 46 mm.
> **This pin order supersedes the frozen ARM/ARM/PYRO1/PYRO1/PYRO2/PYRO2**: the two switched nodes (PYRO*_B → AO3400A drains) must be at the battery end, otherwise the pyro switching loop climbs to y ≈ 51 and crosses the buck zone. ARM_A/ARM_B are DC dividers and are harmless at the forward end.

### 3.4 Other connectors

| Ref | Location | Span | Check |
|---|---|---|---|
| **J1 USB-C** TYPE-C-31-M-12 (C165948) | Starboard long edge | Body **x 38.650 … 46.000** (depth 7.35), **y 45.500 … 54.440** (width 8.94) | Height 3.16 vs `h(23) = 12.552` ✓. **Only 3.80 mm of radial room at the board edge; a USB plug shell cannot get in → on-board USB is bench-only; data download / flashing requires sliding the sled out** (the 46 mm board is worse than the 40 mm one here: 6.80 → 3.80 mm). Width 8.94 and height 3.16 carried over from the frozen document, not independently re-checked this round |
| **J2 SWD 1×6** (C2337 break-away) | Starboard lane, along y | Pin centres **x = 41.000**, **y 57.000 … 72.240** (body 15.24) | Crimp housing max 16.75 vs `h(18) = 18.633` → 1.88 spare ✓ |
| **J-PULLPIN 1×2** | Same lane, along y | Pin centres **x = 41.000**, **y 76.000 … 81.080** | **Opposite side** from the pyro harness (pyro is on port), satisfying frozen §8 item 6 |
| **J-LORA 1×11 (unfitted)** | Port lane | Pin centres **x = 3.000**, **y 44.000 … 71.940** | 3.55 mm from J-ARM ✓ |
| **J-SPARE 1×5 (unfitted)** | Port lane | Pin centres **x = 3.000**, **y 75.000 … 87.700** | 3.06 mm from J-LORA; 11.05 mm from the module edge ✓ |

> **General crimp-housing rule**: any header that may one day take a 0.1" crimp housing must have its pin centre within `\|x − 23\| ≤ 18.0` (i.e. **x ∈ [5.0, 41.0]**), because `h(18) = 18.633 ≥ 16.75`. The port DNP lane at x = 3.000 (\|x − 23\| = 20.0, `h = 16.621`) is **0.13 mm short** — both rows are unfitted pads, so build 1 is unaffected; if LoRa is ever fitted the housing must be shortened or the wires soldered straight out.
> The checker overturned "merge the 1×11 and 1×5 into a 1×14": that is 35.56 mm and would hit the relocated M3 hole. Both rows now sit on the port long edge because, with the corner holes back in the nose corners, port y 40.45 … 112.50 is **72.05 mm** of continuous free edge.

---

## 4. Long-axis zoning (y from 0 at the battery end to 120 at the nose)

| y range | Content | Used | Lateral margin / notes |
|---|---|---|---|
| **0 – 10.70** | Z1 **J-BAT** body (10.70 deep at max material) | 10.70 | 31.00 of end edge usable vs 21.59 → **+9.41** |
| **10.70 – 29.70** | Z2 **high-current corner**: J-SERVO (centreline), J-ARM pin section, Q1/Q2 AON6403, C-BULK1, SMBJ12CA, Q-PY1/Q-PY2 | 19.00 | **⚠ Tightest zone on the board.** 46 − 15.70 (J-ARM inner edge) − 10.40 (header lane) = 19.90, split into x 15.70–17.80 (2.10) and x 28.20–46.00 (**17.80**). Q1 (6.0) + Q2 (6.0) + TVS (5.6) in one starboard row = 17.60 → **only +0.20**, so they **must be in two rows along y**, with the RAW bus (6.0 mm) on top of that |
| **29.70 – 43.70** | Z3 buck AP63203 + 4.7 µH + LC + C-BULK2 | 14.00 | For y < 40.45 usable x 15.70–46.00 = 30.30; for y > 40.45 full width 46.00 |
| **43.70 – 54.70** | Z4 USB-C (side) + MLT-8530 buzzer + LEDs ×2 + pyro/buzzer gate networks | 11.00 | 46 − 7.35 = 38.65 |
| **54.70 – 75.70** | Z5 LQFP100 block **21.00** (x 6.0–27.0, die centre (16.5, 65.20)) \| W25Q128 + 25 MHz crystal lane **10.00** (x 29.0–39.0, centre x = 34.0) \| SWD/pull-pin lane 3.2 | 21.00 | Uses up to x = 42.60 of 46 → **+3.40**. (On a 40 mm board this zone is **2.00 mm over** — bought back directly by the width change) |
| **75.70 – 82.00** | Z6 sensor cluster: **ICM-45686 (23.000, 78.850)**, **MS5611 (32.000, 78.850)** | 6.30 | The IMU must be on the centreline (≥ 41.8 mm from any M3 hole, 39.1 mm from the nearest terminal) |
| **82.00 – 92.00** | Z7 **u-blox 10 mm rear keep-out**: kept as solid copper, only parts ≤ 3 mm tall, **no signal vias and no signal tracks** | 10.00 | GND stitching vias **must** fill it (the integration manual p. 62 requires it explicitly) — they are required, not forbidden |
| **92.00 – 107.50** | Z8 **SAM-M10Q**: x **15.250 … 30.750**, y **92.000 … 107.500**, centre (23.000, 99.750) | 15.50 | **15.25 mm** from each long edge; the 10 mm ring closes with 5.25 mm per side (5.00 at A1 max 16.0) |
| **107.50 – 120.00** | Z9 nose: H3/H4 + solid copper | 12.50 | These 12.50 mm are the price of legal nose corner holes; true free margin is only **1.04 mm** (L_min = 118.962) |
| **Total** | | **120.00** | **Zero free margin** on the long axis; Z9 is already the margin pool |

**Separation rule checks (all pass)**

| Rule | Measured | Multiple |
|---|---|---|
| Buck switch node + L1 centroid **(31.0, 36.0)** ↔ IMU (23.0, 78.85) | `√(8² + 42.85²)` = **43.60 mm** | 2.91× (≥ 15) |
| Buck ↔ GNSS antenna centre (23.0, 99.75) | `√(8² + 63.75²)` = **64.15 mm** | 4.28× |
| IMU ↔ nearest M3 hole H3 (4.0, 116.0) | **41.80 mm** | 4.18× (≥ 10; that rule is labelled an **assumption**, not any datasheet clause) |
| IMU ↔ nearest screw-terminal corner (15.70, 40.45) | **39.09 mm** | 3.91× |
| Switched current ↔ IMU | All at y ≤ 28.0 → **≥ 50.85 mm** | — |

---

## 5. Copper and current

### 5.1 Design currents

| Level | Value | Source |
|---|---|---|
| Cruise (continuous) | **1.50 A** (0.374 A per servo) | **Labelled assumption**: 20 % of the time moving at 40 % stall, 80 % holding at 15 % stall. MKS only publishes stall current |
| Transient (all four at full effort) | **4.49 A** | Assumes 60 % of stall |
| **Fault (design value)** | **7.66 A** | The HV6120's four stall points (1.1 A @ 3.7 / 1.37 @ 6.0 / 1.69 @ 7.4 / 1.87 @ 8.2) solve to a constant **4.385 Ω** above 6 V; the bus is raw 2S **8.4 V** → 8.4 / 4.385 = **1.916 A per servo**. The brief's 7.48 A is the 8.2 V point, not this board's voltage |
| (Out of scope) 2S LiHV 8.70 V | 7.94 A | **Explicitly excluded**; if ever required, recompute all copper widths at 5.234 mm |

### 5.2 IPC-2221 derivation (**10 °C** rise; `A = (I/(k·ΔT^0.44))^(1/0.725)`, external k = 0.048, internal k = 0.024, 1 oz = 1.378 mil)

| Case | 10 °C rise | 20 °C rise |
|---|---|---|
| 7.48 A external 1 oz | 4.820 mm | 3.165 mm |
| **7.66 A external 1 oz (design value)** | **4.981 mm** | 3.270 mm |
| 7.66 A internal 1 oz | 12.85 mm | 8.44 mm |

**As drawn: RAW bus minimum neck 6.00 mm, never below 5.00 mm anywhere.** 6.00 / 4.981 = **1.20×** (10 °C), 1.83× against 20 °C. The 25 % extra width absorbs the holes punched in the pour by via antipads and through-hole pads.

**The primary evidence is a first-principles thermal check, not the IPC curve**: 35 µm copper sheet resistance `1.72e-8 / 35e-6 = 0.4914 mΩ/□`; a 40 × 40 mm square at 7.66 A dissipates `7.66² × 0.4914 m = 28.8 mW`, spread over 1600 mm² with natural convection on both sides (h = 15 W/m²K, labelled assumption) → **0.60 °C** rise. **Copper is thermally invisible on this board and is not a design driver.**
> The IPC-2221 fitted curve tops out around 700 mil²; a 40 mm × 1 oz plane is 2170 mil², a 3× extrapolation — neither the frozen document's 17.3 A nor another round's "corrected" 9.5 A (which was actually 10.49 A for 40 mm × **0.5 oz** internal) **should be quoted as plane ampacity**. IPC-2152 has further shown the 50 % internal-layer derating goes the wrong way.

### 5.3 Layer assignment and stitching

- **Main RAW pour on L4**, **mirrored at the same width on L1** inside the high-current corner (no signal tracks in that corner).
- **≥ 8 × Ø0.30 mm vias** at every L1↔L4 transition. Per via: `π × 0.3 = 0.942 mm` wide × 25 µm plating = 36.5 mil² → 1.794 A @ 10 °C; 7.66 / 1.794 = 4.27 vias → 8 give **1.87×** and halve the parallel inductance.
- **L2 is a solid ground plane not broken by signals** (as in the frozen document). Return vias for the servo GND row must land inside the same corner.
- **L3 no longer carries the sensor nets** (supersedes frozen §2.1): SPI1 (PB3/PB4/PB5/PB7) and I2C1 (PB8/PB9) run **entirely on L1 with zero vias**, MCU pad straight to sensor pad. This satisfies both u-blox's "no layer changes within 20 mm of the module edge" and "keep L2 whole", and is simpler than the original L3 scheme.

### 5.4 High-current corner boundary (coordinates)

```
High-current corner = x 5.000 … 41.000 , y 0.000 … 28.000   (36.0 × 28.0 = 1008 mm²)
```
The frozen document targeted 25 × 40 = 1000 mm², the same scale. **No switched-current path may exist at y > 28.0** (J-ARM's ARM_A/ARM_B pins at y 31.36/36.44 are DC dividers, not switched current).

**The justification for R4 must be rewritten.** The analysis agent's 80–200 mV per servo (4–10 nH loop × 2 A / 100 ns) **was overturned by the checker**: JLC's standard 4-layer L1–L2 prepreg is 0.2104 mm, and `L = µ0·h·l/w` gives **0.529 nH** for a 5 mm-wide pour 10 mm long and 1.322 nH for 25 mm — 5–10× lower than assumed; more fundamentally, the 100 ns edges are generated inside the servo case, behind 150–300 mm of lead (≈ 0.3–1 µH), so the board only sees a slewed envelope. The realistic magnitude is **10–25 mV per servo, 40–100 mV with all four in phase**. R4 still stands, but the reason is **radiated coupling into the SAM-M10Q** and **keeping servo return current out of the sensor reference**, not those voltages.

### 5.5 Connector and device current re-check (filling gaps in the frozen document)

| Item | Load | Rating | Utilisation |
|---|---|---|---|
| J-BAT BAT+ single pin | 7.862 A | 16 A (UL group B) | 49.1 % |
| J-BAT worst case, both channels firing (0.8 Ω bridgewire, 9.84 A) | 17.50 A / 20 ms | 16 A (**steady-state** thermal rating) | 109 %, **thermally irrelevant**: a 6 mm × 25 mm × 35 µm pour rises 0.69 °C adiabatically |
| J-SERVO single contact | 1.916 A | 3 A | 63.9 %; honest range **1.1×–1.6×** (all-contacts-loaded derating assumed 0.7; not published by the maker) |
| J-ARM single channel | 4.0–9.84 A / ≤ 20 ms | 16 A / 24 A | Pass |
| Q1/Q2 AON6403 pair | 55.4 mV @ 7.662 A (pair 7.231 mΩ, linearly interpolated at −7.64 V gate drive); cold 0.212 W per package, hot (×1.4) **0.297 W per package** | 2.3 W @ T_A = 25 °C / **1.4 W @ T_A = 70 °C** | 12.9 % @ 25 °C / **21.2 % @ 70 °C**; current 36.5 % / **45.1 %** |
| C-BULK1 470 µF ripple | Per servo `0.3248 × 1.916 = 0.622 Arms` (supply-side rms upper bound for a stalled motor at duty D, `I_stall·D^1.5·(1−D)^0.5`, maximised at D = 3/4); four in phase **2.489 Arms**, uncorrelated 1.244 Arms | 4.1 Arms | **60.7 % / 30.4 %** |

> **Delete the narrative "146 % ripple at 12 A, rescued by the current correction"** — it applied stall current and 50 % duty at the same time, which is physically impossible. With the correct envelope even the old 12 A baseline is only 95 %: tight but legal. Both 470 µF capacitors keep their values.

### 5.6 Pyro AO3400A (kept, with two new hard requirements)

- Single-pulse capability: the Fig 11 single-pulse curve @ 20 ms reads ≈ 0.105 × RthJA 125 °C/W = **13.1 °C/W**, allowing 9.5 W (independently cross-checked against Fig 10: 8–10 W).
- But the gate is driven by a 3.3 V GPIO, so **interpolate the datasheet MAX column** (48 mΩ @ 2.5 V, 32 mΩ @ 4.5 V → 41.6 mΩ at 3.3 V, × 1.6 hot = **66.6 mΩ**); do not scale the typ curve:
  - 5.89 A nominal: 2.31 W → ΔTj 30.3 °C → **Tj ≈ 90 °C** (60 °C board) ✓
  - 6.81 A (1.0 Ω + leads): 3.09 W → **Tj ≈ 100 °C** ✓
  - **9.84 A (0.8 Ω bare bridgewire): 6.45 W → Tj ≈ 145 °C, close to the 150 °C limit; Figs 10/11 were measured on 1 in² of 2 oz copper and this board's outer layer is 1 oz, so it is worse → rated MARGINAL, not PASS**
- **New design requirement ①**: igniter resistance at the terminal (leads included) **≥ 1.0 Ω**, added to the launch-day checklist.
- **New design requirement ② (firmware)**: time every fire pulse independently with the free-running TIM2 microsecond timebase, with a **measured 25 ms hard abort**, decoupled from the state machine that started it. The frozen §7 "≤ 20 ms, one channel at a time" is not a hygiene clause — **it is this FET's thermal design**.
- The 5 A arming fuse **does not cover** the intermediate state "channel stuck on into a ~1 Ω load that does not fire": 6.81 A is only 136 % of the fuse rating, a fast fuse may take minutes to blow, and the steady-state RthJA of 125 °C/W would give a 313 °C rise. That is why requirement ② exists.

### 5.7 Frozen-document parameter errata (conclusions unchanged, inputs must change)

| Location | Old value | Correct value |
|---|---|---|
| §4.5 AO3400A | Vgs(th) 0.4–1.1 V, Crss 75 pF | **Vgs(th) 0.65/1.05/1.45 V, Crss 50 pF, Ciss 630 pF, Vgs absolute max ±12 V** (AOS Rev 3.1, 2023-07) |
| §1 Miller check | ΔVgs 1.34 V | Qgd (0 → 8.4 V) = 1.8 nC × 8.4 / 15 = **1.01 nC**; into Ciss alone gives **1.60 V**, still above the true minimum threshold of 0.65 V → **the 10 nF gate-source capacitor is confirmed mandatory**; with 10 nF, 95 mV. The 1k pull-down gives 0.065–0.106 V, **1/6.1** of the true minimum threshold |
| §2.2 inrush | 99 A / τ = 83 µs / only 2.3 mJ in the FETs / "the load switch is not a soft start" | The gate network 100k ‖ 10k = **9.091 kΩ** Thevenin source; AON6403 Ciss 6100/7600/9120 pF → τ **55–83 µs**, Miller plateau **24–55 µs**, the same order as the 42 µs RC of 492 µF through 85 mΩ → **the 99 A peak is never reached; it is a 40–55 µs soft start**, with each FET absorbing about **8.7 mJ** (Zth_JC ≈ 0.1–0.2 °C/W @ 50 µs → about 26 °C rise, far from the 280 A IDM and 150 °C). *(SIMULATION.md later measured this in SPICE: see there for the current numbers.)* |
| §2.2 servo-rail 22 µF | 2 × 22 µF | 0805 / 25 V / X5R loses 40–60 % at 8.4 V DC bias → really **2 × ~11 µF**; total RAW capacitance **≈ 492 µF**. No design change, but all ripple must be booked on the polymer |

---

## 6. GNSS ruling

### Ruling: **SAM-M10Q stays on board, radial orientation kept (option a). Zero BOM change. Zero change to the long-axis budget (Z7 + Z8 = 25.50 mm kept in full).**

**Reasons (evidence chain after checker corrections)**

1. **The width problem disappears at 46 mm.** Centred, the module is **15.25 mm** from each board edge; the 10 mm ring closes with 5.25 mm per side; the ground plane is 46 mm, 15 % above u-blox's stated 40 × 40 mm degradation threshold (a 40 mm board sits on the threshold with **zero margin**). It is still 8 % short of the 50 × 50 optimum; from the 18 × 18 × 4 curve in UBX-15030289 Fig 19, with a slope of 0.095 dB/mm in the 40–50 mm range, that is **about 0.4 dB** — and u-blox says on the same page that "smaller patches need a smaller ground plane to reach peak gain than large ones"; the SAM's patch is 15 × 15, smaller than any curve on the figure, so 0.4 dB is an **upper bound**.
2. **Nose-end M3 holes are fully legal at 46 mm with corner holes and nylon hardware** (§2.1); the 36 mm cantilever is gone and no metal is pushed into the antenna near field.
3. **The orientation penalty is real but was downgraded by the checker.** The analysis agent's "33–35 dB-Hz, yellow zone, loses satellites at lift-off" conclusion treated −130 dBm (the **guaranteed minimum** received power) as the expected value, contradicting the same u-blox document's "a well-designed system should see 44–50 dB-Hz on high-elevation satellites". Recomputed with typical values: radial mounting gives about **36–40 dB-Hz, with roll nulls bottoming at 31–34 dB-Hz**, inside Featherweight's 32–40 "cold-start acquirable" band, not the yellow zone. The orientation penalty (about 10–11 dB for zenith satellites, 13 dB peak-to-peak roll fading for 45–75° satellites, 31–165 ms each at 2–5 rev/s) is still real, but **the severity is TIGHT, not BLOCKER**.
4. **Option (b) (Ø52–53 mm disc mounted crosswise on the avionics-bay forward bulkhead) has two unresolved conflicts and cannot be frozen now**: (i) the forward bulkhead is exactly where the recovery harness U-bolt/eye-bolt goes, i.e. a piece of steel at zero distance in the antenna main lobe — worse than the M3 screws it would replace; (ii) **the airframe material is undecided**. If carbon fibre, the TE11 cut-off of a Ø54.66 mm tube is `1.8412c/(πD) = 3.214 GHz`, and attenuation at L1 is about **0.51 dB/mm ≈ 51 dB per 100 mm** — the inside of the tube is dead. Then a bulkhead disc inside the bay is the most shielded spot on the rocket, and the answer is forced to "antenna in a fibreglass/plastic nose cone + a cable across the separation plane", exactly what option (b) itself forbids.
5. **Radial mounting does not lose on the design's stated primary use.** The frozen document positions GPS as "pad lock + descent/recovery aid". Axial mounting wins outright on the pad (airframe vertical, main lobe at zenith, +2.7 dBic vs −7.8), but **during descent and after landing the roll axis is horizontal**, so an axial patch deterministically points at the horizon (−8.7 dBic, every time), while a radial patch's main lobe is spread evenly in the vertical plane and wins more often.

**Escape hatch (zero BOM change, just put it in the schematic)**: redefine the **J-SPARE 1×5 unfitted pads as 3V3 / GND / GNSS_TX / GNSS_RX / spare**, on the same nets as USART6. Then a later switch to option (b) is a **no-respin** change: remove the SAM-M10Q + its 100 nF + 22 µF from the board (−3 parts), add at system level 1 PCB + 1 SAM-M10Q + 2 capacitors + 1 header + 1 harness (+5 parts), freeing **25.50 mm** of length. Option (c) (MAX-M10S + u.FL) is **rejected**: it needs all of option (b)'s mechanical work, saves only 10.9 mm, runs a coax carrying −130 dBm across the airframe in a vibration/shock environment, and is +1 to +3 parts on the board rather than −2.

**Mandatory GNSS layout rules (to be written into §2.1)**

- Inside the module's 10 mm ring: **no part taller than 3 mm, no metal fasteners, no signal tracks and no signal vias**; 0402/0603, the 0.91 mm IMU, the 1.0 mm barometer and the 2.15 mm SOIC-8 flash may enter the ring (keeping the frozen document's lenient reading of integration manual §4.3, but **the document must state that this is an explicit choice between two conflicting u-blox sentences**, and that the strict §4.4 reading applies to metal/tall parts).
- **GND stitching vias must fill the area under and around the module (about 2–3 mm pitch)** — required explicitly under Fig 21 on p. 62 of the integration manual. The earlier claim "no vias at all inside the ring" confused signal layer changes with ground stitching and was backwards.
- Mounting holes are a Ø3.2 drill + at most a Ø4.2–4.5 isolation ring, **with the ground plane flowing continuously around the hole**; the earlier claim that "two 7.5 mm square cut-outs chop the ground plane at that y station to 25.5 mm and cost another 1.5–2 dB" does not hold and has been deleted.
- **The 20 mm layer-change rule cannot be met by any flat board inside this airframe**: a centred 15.5 mm module needs 15.5 + 40 = **55.5 mm** of board width, 0.84 mm wider than the 54.66 mm airframe ID. A 46 mm board falls 4.75 mm short per side (40 mm: 7.75; 50 mm: 2.75). **Do not chase this number sideways**; satisfy it along the length (Z7 stays 10 mm, can grow to 20 mm at +10 mm of length if needed), and eliminate layer changes in that band with §5.3's "SPI1/I2C1 entirely on L1 with zero vias".
- **Spur risk (unique to this board, not previously noticed)**: 25 MHz × 63 = **1575.000 MHz**, only 420 kHz from the L1/E1 centre and inside the GPS C/A main lobe (±1.023 MHz); 25 MHz × 64 = **1600.000 MHz**, inside GLONASS L1 FDMA (1598.06–1605.38); SYSCLK 200 MHz × 8 = **1600.000 MHz** lands there too. The thermal noise floor in a 2 MHz band is `−174 + 10·log10(2e6) = −111.0 dBm`, and the GNSS carrier is another 19 dB below that. Available measures: minimise the 25 MHz crystal loop area and keep it ≥ 40 mm from the module, keep the H7 core-clock return tight under the LQFP, and if in-band spurs are measured on the bench, disable GLONASS in the u-blox configuration (keep GPS + GAL + BDS). **Do not change SYSCLK** — the frozen §1 ruled 200 MHz and explicitly "do not run 480 MHz"; the 400 MHz in the earlier "400 × 4 = 1600" reason for switching to 480 MHz came from nowhere.
- The SAM-M8Q-0 (C5447387) fallback is **geometrically identical** (same 15.5 × 15.5 LGA, same integrated patch); every coordinate and conclusion in this section applies unchanged.
- `CFG-NAVSPG-DYNMODEL = Airborne < 4g` stays (integration manual Table 5: the sanity check is "Altitude" only; 500 m/s horizontal speed is not a rejection criterion, so supersonic flight does not fail on a speed test).

---

## 7. Mechanical stack

### 7.1 Two envelope models (46 mm board)

| Model | Formula | Result | Assessment |
|---|---|---|---|
| Naive inscribed rectangle | `2·√(27.33² − 23²) − 21.6` | **7.925 mm** | **Wrong model.** It forces the 17 mm battery, the sled and the top-side parts to all be 46 mm wide. Taken at face value, not even one bare plugged servo connector (16.75 mm) would fit |
| **Chord-height model (adopted)** | The battery sits at its own best height | Below | Each object is charged only for **its own width** |

**Chord-height derivation (all inputs labelled)**

```
R = 54.66 / 2 = 27.33 ;  radial wall clearance 0.5 mm (assumption) → R_eff = 26.83 , R_eff² = 719.8489
2S battery 35 mm wide × 17.0 mm thick (35 mm is an assumption, 17.0 given by the brief)
Battery lower corner y = −√(719.8489 − 17.5²) = −√413.599 = −20.337
Stack (bottom to top, assumed order): battery 17.0 → sled 3.0 → PCB 1.6
PCB top face z = −20.337 + 21.6 = +1.263
Clearance h(x) = √(719.8489 − x²) − 1.263 ,  x = board coordinate − 23
```

| \|x − 23\| | h | Corresponds to |
|---|---|---|
| 0 | **25.567** | Board centreline |
| 5.20 | **25.058** | Outer edge of the servo plug block |
| 10.795 | 23.300 | End of the J-BAT body |
| 15.39 | 20.714 | J-ARM top outer corner |
| 18.00 | 18.633 | J-ARM wire-entry face / crimp-housing placement limit |
| 23.00 | **12.552** | Board edge |

### 7.2 Part-by-part check

| Part | Height | At \|x − 23\| | Available | Margin |
|---|---|---|---|---|
| **J-SERVO + plugged servo connectors + 90° wire bend** | **23.50** | 5.20 | 25.058 | **+1.558 ← binding constraint** |
| J-SERVO bare header | 8.50 (2.5 insulator + 6.0 pin) | 5.20 | 25.058 | +16.56 |
| Crimp housing (without the bend) | 16.75 | ≤ 18.0 | ≥ 18.633 | +1.88 |
| J-BAT / J-ARM body | 14.50 (max material) | 10.795 / 15.39 | 23.300 / 20.714 | +8.80 / +6.21 |
| 470 µF polymer Ø8.0 × H10.0 | 10.00 | ≤ 19 | ≥ 17.13 | +7.13 |
| SAM-M10Q | 6.80 (F max) | ≤ 7.75 | ≥ 24.44 | +17.64 |
| USB-C | 3.16 | 23.00 | 12.552 | +9.39 |
| MLT-8530 buzzer | 3.30 | ≤ 11 | ≥ 23.13 | +19.83 |
| SWPA4030 inductor | 3.00 | ≤ 14 | ≥ 21.70 | +18.70 |

**The binding constraint is the plugged servo header, with 1.558 mm of margin for the whole board.**

### 7.3 Three hard requirements for the mechanical drawings

1. **The sled must have relief slots under the pin fields of J-BAT, J-ARM and J-SERVO.** The DB128V tail is 3.50 ± 0.30; through a 1.6 mm board it **protrudes 1.90–2.20 mm**, plus ~0.3 mm of solder fillet ≈ 2.5 mm; the 3×4 header tail is 3.00 → about 1.6 mm. Yet the whole calculation in §7.1 assumes the PCB lies **flat** on the sled with zero gap. Raising it on 2.5 mm standoffs moves z to +3.763 and drops centreline clearance to 23.07 mm, **0.43 mm short of 23.50, which kills the only workable servo header position**. Even 1.6 mm standoffs leave only 0.47 mm.
2. **2S battery width ≤ 36 mm is a hard constraint.** Sensitivity: 30 mm → 3.46 mm spare; **35 mm → 1.558**; 36 mm → 1.12; 38 mm → **0.16**; 40 mm → **−0.90 (fails)**.
3. **The terminals cannot be tightened inside the airframe.** The DB128V screw axis is about 5.25 mm inside the wire-entry face; clearance at the J-BAT screws is 23.30 − 14.00 = **9.30 mm**, at J-ARM 22.34 − 14.00 = **8.34 mm**. An M2.5 screwdriver will not fit. **All 4 battery/switch wires and all 6 ARM/PYRO wires must be terminated and torqued outside the airframe, pre-formed and dressed aft, before the sled is inserted; any re-termination on the pad requires pulling the sled.** This is the same class of rule as §3.4's "USB is bench-only" and goes into the documentation together with it.

### 7.4 Tie-rod compatibility (46 mm board)

The rod axis moves on a circle of radius `R − d/2`; beside the board the clearance is `(R − d/2) − d/2 − 23`.

| Size | Major diameter d | Reachable axis x | **Beside-board clearance per side** | Max board width for 1.5 mm clearance |
|---|---|---|---|---|
| **M3** | 3.000 | 25.830 | **+1.330 mm** | 45.66 mm |
| **#6-32** | 3.505 | 25.578 | **+0.825 mm** | 44.65 mm |
| **1/4-20** | 6.350 | 24.155 | **−2.020 mm (infeasible)** | 38.96 mm |

**Ruling: tie rods = M3, not beside the board, passing straight through the board's own corner holes H1→H3 and H2→H4.** The two hole pairs are collinear at x = 4.000 and x = 42.000, 112.0 mm apart; the rods sit entirely inside the board outline, the airframe radial-clearance problem disappears, and the mounting rectangle is 38.0 × 112.0 mm with no cantilever.
Beside the board, M3 leaves only 1.330 mm on a 46 mm board, 0.17 mm below the 1.5 mm design clearance, and airframe ID tolerance ±0.2, rod straightness ±0.3 and board routing ±0.2 eat it entirely — **beside-board is only an option for boards ≤ 45.66 mm wide**. 1/4-20 is infeasible either way (through the board needs a Ø6.6 clearance hole + Ø12.7 washer; two washers eat 25.4 mm of the 46 mm end edge).
*(Later superseded — see HISTORY.md §2: the M3 rods only clamp the sled/bulkheads and never pass through a PCB; the board is screwed to the sled. Hole positions remain open.)*

---

## 8. Changes relative to the frozen document

| Frozen document location | Original | Superseded by | Basis |
|---|---|---|---|
| §1 / §2.1 board size | 50.0 × 110.0 mm | **46.0 × 120.0 mm** | §1, §2 |
| §1 / §8-1 minimum airframe | 3 in / 75 mm, ID 72.87 mm; "a 54 mm airframe does not work" | **Airframe ID 54.66 mm, the design works** (46 mm board + chord-height model + battery ≤ 36 mm + sled relief slots) | §7 |
| §2.1 mounting holes | Two battery-end holes in the corners; two nose-end holes moved to the long edges at x = 3.5, y ≈ 94/99; mounting rectangle 43 × 95 | **All four holes in the corners: (4,4) (42,4) (4,116) (42,116), keep-out R3.5, mounting rectangle 38 × 112**; H3/H4 use **nylon hardware** | §2.1, §6 |
| §2.1 long-axis zoning | Nine zones, 0–110 | **The full table in §4, 0–120** | §4 |
| §2.1 "0–8.2 BAT 4-pos terminal + 3×4 servo header side by side (20.32 + 11.0 = 31.3 of 50)" | — | **Void.** J-BAT has the end edge to itself; J-SERVO moves inboard to the centreline, x 17.8–28.2 / y 12.4–20.4 | §3.1, §3.2 |
| §2.1 "6-pos terminal fixed on the long edge, y ≈ 1–34, 9.8 mm wide" | — | **J-ARM on the port long edge, inset 5.00 mm, body x 5.0–15.7 / y 8.5–40.45**, 15.70 mm wide | §3.3 |
| §2.1 height rule "any top-side part ≤ 26.9 mm (naive rectangle bound)" | — | **`h(x) = √(719.8489 − (x − 23)²) − 1.263`**: 12.552 mm at the board edge, 25.567 mm at the centreline | §7.1 |
| §2.1 "buck-to-sensor spacing 36/52 mm" | — | **43.60 mm / 64.15 mm** (new coordinates) | §4 |
| §2.1 stackup "L3 signals (sensor nets run here)" | — | **SPI1/I2C1 entirely on L1 with zero vias** (meets both the u-blox 20 mm layer-change rule and a whole L2) | §5.3 |
| §2.2 inrush "99 A / τ = 83 µs / only 2.3 mJ in the FETs / the load switch is not a soft start" | — | **It is a 40–55 µs soft start**; 99 A is never reached; about 8.7 mJ and ~26 °C rise per FET | §5.7 |
| §2.2 "FET pair 86 mV / 0.52 W per package at 12 A" | — | **55.4 mV / cold 0.212 W / hot 0.297 W per package at 7.662 A**; at 70 °C 21.2 % of power rating, 45.1 % of current | §5.5 |
| §2.3 servos / §4.5 J-SERVO / §8-2 "3 A per pin → servo stall must be ≤ 3 A, the board's only hard constraint on servo choice" | — | **Constraint released.** MKS HV6120 stalls at 1.916 A per channel at 8.4 V and each pin carries one servo → 63.9 %; the "two 3×2 headers / four separate terminals" fallback is void. The honest 1.1×–1.6× range and the bench-measurement recommendation remain | §5.5 |
| §4.5 J-BAT/J-ARM "body length unverified, draw at 5.08N + 2.54" | — | **Closed: body = exactly N × 5.08** (4P 20.32, 6P 30.48), plus a **0.57 mm dovetail** (outside the dimension line; must be drawn in the outline with a fixed orientation). Also confirmed depth 10.20, pin row 5.00, height 14.00, hole Ø1.60, tail 3.50 ± 0.30 | §3 |
| §2.3 pyro / §5.2 J-ARM pin order "ARM/ARM/PYRO1/PYRO1/PYRO2/PYRO2" | — | **PYRO1_B / PYRO1_A / PYRO2_B / PYRO2_A / ARM_A / ARM_B** (aft → forward), the two switched nodes at the battery end | §3.3 |
| §4.5 J-BAT net order "BAT+/BAT−/SW/SW" | — | **SW / BAT+ / BAT− / SW** (port → starboard) | §3.1 |
| §4.5 AO3400A "Vgs(th) 0.4–1.1 V, Crss 75 pF" | — | **0.65/1.05/1.45 V, Crss 50 pF, Ciss 630 pF, Vgs absolute max ±12 V** (AOS Rev 3.1). The 10 nF gate-source capacitor goes from "optional" to confirmed **mandatory** | §5.7 |
| §1 copper "a 1 oz, 40 mm inner plane already carries 17.3 A > 12 A per IPC-2221" | — | **Plane ampacity is no longer quoted** (the IPC-2221 curve tops out around 700 mil²; this is a 3× extrapolation; IPC-2152 has shown the internal derating goes the wrong way). First principles instead: **28.8 mW and 0.60 °C rise at 7.66 A**. RAW bus **drawn at 6.00 mm, never below 5.00 mm** | §5.2 |
| §7 firmware (new) | — | **Time every fire pulse independently with TIM2, measured 25 ms hard abort**; igniter resistance at the terminal **≥ 1.0 Ω** added to the launch-day checklist | §5.6 |
| §8-1 / §8-2 | To be confirmed | **Answered: airframe ID 54.66 mm; servo = MKS HV6120 (3.5–8.4 V, explicitly "2S LiPo un-regulated", stall 1.87 A @ 8.2 V / 1.916 A @ 8.4 V, 5.4 kg·cm @ 8.2 V, 11 g, 23 × 8 × 25.25 mm, centre 1520 µs, frame 333 Hz, dead band 1 µs)** | Brief |
| §4.6 J-SPARE 1×5 | 3V3/GND/SCL/SDA/ADC (PB0) | **3V3 / GND / GNSS_TX / GNSS_RX / spare** (same nets as USART6), the zero-respin escape hatch for an external GNSS | §6 |
| (new mechanical rules) | — | **①** the sled must have relief slots under the pin fields of the three terminals/headers (otherwise the servo header position dies); **②** 2S battery width ≤ 36 mm; **③** terminals can only be tightened outside the airframe; **④** USB is bench-only, no service port in the airframe; **⑤** tie rods = M3 through H1→H3 / H2→H4 | §7.3, §7.4, §3.4 |

---

## 9. Still to be confirmed

| # | Item | Why it must be asked now |
|---|---|---|
| 1 | **Airframe and nose-cone material** | If carbon fibre or metal, the Ø54.66 mm tube's TE11 cut-off is 3.214 GHz and attenuation at L1 is **≈ 0.51 dB/mm** — there is no GNSS signal inside the tube at all, and all of §6 is discussing the wrong problem. The only solutions are then an antenna inside a fibreglass/plastic nose cone (wired across the separation plane) or an RF window ≥ 1 in × 1 in directly above the antenna. **This should be answered before anything is ordered.** |
| 2 | **Measured width and thickness of the 2S battery** | The frozen document gives only 17.0 mm thickness; **width appears nowhere**. This document derived all radial clearances assuming 35 mm; **≤ 36 mm closes, 38 mm leaves only 0.16 mm, 40 mm fails** (§7.3-2) |
| 3 | **Tie-rod size** (known open item) | This document rules M3 through H1→H3 / H2→H4. If existing hardware is 1/4-20: beside the board the clearance is −2.02 mm, and through the board it eats 25.4 mm of end edge — **both are infeasible**, the board would have to shrink to ≤ 38.96 mm, and the width ruling in §1 would reopen |
| 4 | **Actual minimum bend radius of the MKS HV6120 leads** | 5.5–6.0 mm of the 23.50 mm is a bend-radius assumption. If the leads are 26 AWG ribbon and a 3.5 mm radius works, the budget drops to **20.90 mm**, the placement window widens from ±10.33 to ±15.12 mm, and the 40 mm battery case also passes. **This one number currently decides two rulings on its own; worth measuring once with calipers.** |
| 5 | **Do the plugs supplied with the MKS HV6120 fit side by side on a 2.54 mm column pitch?** | A standard 0.1" single-row crimp housing is **exactly** 2.54 mm thick; four side by side have zero gap and overhang 0.10 mm at each end. A 3-row × N servo header is the standard Pixhawk / RC receiver topology and should pass a priori, but a keyed rib or flash on the MKS housings would prevent it. **Measure one plug's width; if it fails, re-crimp the servo leads into standard 0.1" housings (5 minutes) — do not change the header** |
| 6 | **Actual form of the sled and how it sits in the tube** | All height numbers in §7 assume "a flat sled at least 40 mm wide, the PCB flat on top, the battery underneath". If the sled rides on rails or bulkhead slots, every 1 mm the board is raised removes 1 mm of clearance from the whole table, and the binding constraint has only 1.558 mm |
| 7 | Items 3/4/5/6/7/9/10 of the original §8 | Untouched by this round's geometry changes; still open |

### Inputs in this document labelled "unverified / assumption", carried forward as-is

- **2S battery width** (35 mm used; it appears in no document); **stack order** (battery – sled – PCB – components up, inferred from the brief's 21.6 mm arithmetic, not stated in the frozen document); **0.5 mm radial wall clearance** (with zero clearance every clearance grows by about 1.2 mm).
- **Wire gauge and bend radius**: ARM/PYRO taken as 22 AWG ≈ 1.7 mm OD with 4–5.5 mm radius; servos as 26 AWG. J-ARM's wire-exit margin is entirely a function of this assumption.
- **DB128V wire-entry hole axis height 2.8–4.9 mm**: read off the drawing scale, not a dimensioned value; the opening drawn is only 1.31 mm tall, inconsistent with the 22–12 AWG / 2.5 mm² rating, which suggests the clamp position is drawn. The radial check uses the upper edge of that band, 4.9 mm.
- **HX PZ2.54-3×4P body dimensions**: the LCSC PDF is a 7-page approval spec with **no dimension drawing and no numeric dimensions**; it supports only 3 A per contact, 250 V and materials/plating. The 2.50 insulator / 6.00 mating pin / 3.00 tail come from the LCSC parameter table (checked). The body is conservatively taken as the 2.54 grid nominal **10.16 × 7.62** throughout.
- **Servo plug 14.00 ± 0.25 mm**: from Pololu's 0.1" crimp housing drawing, **not MKS's** (both official MKS pages returned 404).
- **All-contacts-loaded derating factor 0.7 for the 3×4 header**: not published by the maker, hence §5.5 gives a 1.1×–1.6× range rather than a single 1.60×.
- **25 mΩ ESR and 4.1 Arms of the 470 µF/25 V polymer (C46550466)**: from the LCSC parameter table only; no maker datasheet (already flagged in the frozen document).
- **u-blox does not publish how many dB "significantly degraded below 40 × 40 mm" means**: neither the SAM-M10Q integration manual nor its datasheet gives a number. The 0.4 dB (46 → 50 mm) and 0.7–1.1 dB (40 → 50 mm) are interpolated from a **third-party INPAQ 18 × 18 patch** curve in a different application note, UBX-15030289 Fig 19; the SAM's own patch is 15 × 15, smaller than any curve on that figure. **Use as an estimate, not a specification.**
- **AO3400A Zth_JA (20 ms) = 13.1 °C/W**: a graphical reading of the Fig 11 single-pulse curve; Note F says Figs 10/11 were measured on 1 in² of **2 oz** copper, and this board's outer layer is 1 oz, so the true value is worse.
- **Servo cruise current 1.50 A**: MKS publishes only stall current; the value rests entirely on the duty-cycle assumptions in §5.1 and must be measured on the bench before it is used for battery-capacity estimates.
- **USB-C TYPE-C-31-M-12 body 8.94 × 3.26 mm**: carried over from the frozen document, not independently re-checked this round (LCSC only gives "Length 7.35 mm", i.e. insertion depth).
