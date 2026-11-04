> Copied into the R12 records on 2026-11-04 from the read-only cost-study lane (stage A input to `r12_plan.md`).
> Text as written by the study, with its working-file references replaced; R12's decisions that depart from it
> are in `R12_DECISIONS.md` (D-R12-06 3V3 buck, D-R12-07 / -08 TPS563208, D-R12-09 OVLO, D-R12-16 owner-fitted
> buzzer).

# Low-cost revision: cost study (read-only lane, 2026-11-04 UTC)

Evidence labels (AGENTS §2.5): **Live** = queried today from JLC (component API `selectSmtComponentList`
via `tools/jlc_stock.lookup`, or the cart.jlcpcb.com/quote form driven in the owner's browser);
**Datasheet** = read from the maker's PDF; **Calculation** = arithmetic on Live/Datasheet values;
**Inference** = anything resting on an unmeasured or unverified input. Nothing here is a measurement of hardware.

Timestamps: component prices and stock 2026-11-04T00:51:36Z (R11 BOM) and 01:12–01:15Z (candidate BOMs);
assembly fee page read 2026-11-04 ~00:45Z (page "updated Oct 22, 2026"); PCB quotes 2026-11-04 ~00:55–01:40Z.
All component figures came from the study lane's raw JLC responses and pricing script, which were working files and are
not tracked; the per-line result is reproduced in section 3.1 below. R12's own live run is `jlc_r12_stock.json` /
`r12_cost.json` beside this file.

---------------------------------------------------------------------------------------------------------

## 0. Recommendation (summary)

**Cheapest reasonable architecture: R10/R11's circuit (same netlist family, R11 part values), pruned and
re-sourced as below, laid out on a NEW single-sided 4-layer 46 × ~100 mm board (all parts on the top face),
STM32H743VIH6 TFBGA-100 kept, 0.3 mm-drill vias only, 0.5 oz inner copper, ENIG, ordered as JLC
Economic PCBA.** Basis: the existing R10 (4L LQFP, both sides) and R11 (6L TFBGA, both sides) layouts both
force Standard two-sided assembly; neither can be reused as-is. The lean board is a new layout either way.

| Order (Live / Calculation) | Today R11 (Std, 2 sides, 75 codes) | Recommended (Economic, 1 side, 51 codes, 16 charged) | Δ |
|---|---|---|---|
| 2 boards, assembly (parts with JLC min-buy + feeder + setup/stencil[/fixture]) | **$327.65** | **$143.96** (incl. $3.58 hand-solder fee for one THT buzzer) | −$183.69 |
| 5 boards, assembly | **$482.91** ($489.13 with min-buy) | **$266.27** | −$216.64 |
| Bare PCB, 5 pcs (JLC minimum; also the 2-board case) | 6L 46 × 50 ENIG 0.5 oz: **$48.90** at the free 7–8-day build ($181.30 with the form's default 3–4-day build) | 4L 46 × 100 ENIG 0.5 oz: **$25.10** (keep L ≤ 100 mm: 46 × 105 is $45.10) | −$23.80 |
| **Total, 2 boards** | $376.55 | **$169.06** | −55 % |
| **Total, 5 boards** | $531.81 | **$291.37** | −45 % |
| Parts + feeder per board at 5 (REQUIREMENTS M3 metric, cap $84.41) | $79.79 | **$50.60** | |

Not in either column (same for both): SMT joint fee $0.0016/joint (~650–700 joints → ≈ $1.1/board), shipping, tax,
C84 hand-fit labour. With the out-of-stock LSM6DSV80X instead of the ISM6HG256X: $127.92 (2 b) / $226.18 (5 b).

**Functions or margins given up (every one is listed; nothing in AGENTS §2 is touched):**
1. USB path: U10 (USB current limit), U11 (priority mux, its OVLO and ILIM) and D4 (USB ESD) deleted; VLOGIC becomes a
   diode-OR of RAW_PROTECTED and VBUS (two 1N5819WS). Lost: USB inrush/fault current limit toward the host, USB OVLO,
   USB ESD clamp, the LOGIC_SOURCE_ST / USB_FAULT_N flags (firmware reads VBUS_SENSE and VLOGIC_SENSE instead).
   Bench-only mode; Inference that hosts tolerate C84's inrush.
2. Port ESD: the 8 ground-only ESD103 diodes on GPS / radio / AUX / camera UART wires deleted (1 kΩ series stays).
   D402 (J400.2 → EN clamp, required by F9's calculation) stays.
3. Camera: U402 (TPS2553 limiter), U12 (TXU0202 isolator) and U13 (TPS70933) deleted. The camera gets its own
   TPS563201 buck whose EN pin is the MCU-controlled camera switch (pull-down kept) and whose cycle-by-cycle limit
   (3.3–5.1 A valley, Datasheet) contains a camera fault. CAM_FAULT_N is lost (CAM_5V_SENSE stays). UART is 1 kΩ
   series like the other ports; new firmware rule: camera TX/RX pins analog whenever the camera buck is off.
4. Port rail: U401 TPS7A91 LDO (and its two GAP-3 VIPPO vias) deleted; GPS / radio / AUX fed from a dedicated
   TPS563201 at 4.57–4.96 V (Calculation, 1 % 51k + 1k / 10k). Loss: LDO-grade ripple on the port rail (Inference: the
   modules regulate internally).
5. Precision: every 0.1 % divider becomes 1 % basic with the window shown by calculation (§3.3).
6. Copper: 0.5 oz inner instead of M1's 1 oz (R11 already deviates); 4 layers instead of R11's 6.
7. Parts with smaller ratings: SMAJ12CA (400 W) for SMBJ12CA (600 W); 1206 X5R 22 µF for 1210 X7R (less bias-
   retained capacitance; port and hot-plug figures need re-running, Inference); AO3401A / AO3400A for AONR21357 /
   AON7524 (Calculation in §3.4).
8. Connectors: JST-GH replaced by GH-1.25 clones (Inference: mate with JST GH housings and latch; must be checked on
   a sample); J400 and J122 move to 4- and 6-pin bodies to share codes (unused pins).
9. Buzzer: SMD MLT-5020 → THT QMB-09B-03 (needed for Economic's 255 °C reflow; bigger, 9 mm).
10. Barometer: MS5611 → LPS28DFW (260–4060 hPa, 260 °C-class LGA, Inference on its reflow rating) for Economic.
    If Economic is rejected, use MS5607-02BA03 (same land as MS5611, −$2.11) on Standard one-sided.
11. Crystal: NX3225GA 8 pF → X322525MOB4SI 12 pF basic (gm_crit 1.11 mA/V vs ST's 1.5 mA/V limit; Calculation with an
    assumed 3 pF C0, Inference); existing 10 pF load caps kept, frequency pulled a few tens of ppm (Inference).

**Owner checks before this can be adopted:** (a) reflow ratings ≥ 260 °C for every part on the Economic BOM (§1.2);
(b) GH-clone mating; (c) LR900-F and M100 Mini supply ranges at 4.57–4.96 V; (d) U9 auto-retry (A) instead of
latch-off (L) variant; (e) hot-plug and F6 hold-up re-run with the diode-OR and the new OVLO (13 V class, §3.3);
(f) a new single-sided layout (none exists).

---------------------------------------------------------------------------------------------------------

## 1. Assembly tier and sides

### 1.1 JLC fees (Live, https://jlcpcb.com/help/article/pcb-assembly-price, "updated Oct 22, 2026")

| Fee | Economic | Standard |
|---|---|---|
| Setup | $8.18 | $25.56 one side / $51.12 two sides |
| Stencil | $1.53 | $8.21 one side / $16.42 two sides |
| Feeder loading | $3.07 per **Extended** code (Basic free; JLC's prototype-assembly page says **Preferred Extended** is also free on Economic: https://jlcpcb.com/solutions/pcb-prototype-assembly, via search, Inference on the current wording) | $1.53 per code, Basic or Extended |
| Fixture (rigid, 1–29 pcs) | – | $16.42 |
| Handling | – | ≥ $14.93 when the Standard/Economic gap is under $14.93 |
| SMT joints | $0.0016 / joint | $0.0016 / joint (1–50 000) |
| Manual (THT) joints | $0.0164 / joint + $3.58 hand-soldering labour per order | same |

Capabilities (Live, https://jlcpcb.com/capabilities/pcb-assembly-capabilities): Economic reflow **255 ± 5 °C, not
adjustable**; Standard 240 ± 5 °C. Economic = single-sided placement (SMT/THT), single PCB 10 × 10 – 470 × 500 mm,
2/4/6 layers, BGA ≥ 0.5 mm pitch, IC pitch ≥ 0.4 mm; Standard single PCB ≥ 70 × 70 mm (a 46 mm-wide board needs JLC
edge rails). Economic parts down to 0402 only (JLC FAQ via search) — R11 uses 0402, so this is fine.

### 1.2 Tier × sides × boards (Live parts, Calculation fees)

| BOM / tier / sides | 2 boards | 5 boards | codes / charged |
|---|---|---|---|
| R11 as committed, Standard, 2 sides | $327.65 | $482.91 ($489.13 with min-buy) | 75 / 75 |
| Lean BOM (§3), Standard, 1 side | $213.35 | $335.66 | 51 / 51 |
| Lean BOM, MS5607 variant, Standard, 1 side | $205.71 | $321.94 | 51 / 51 |
| Lean BOM, **Economic, 1 side** (recommended) | **$143.96** | **$266.27** | 51 / 16 extended |
| … same, LSM6DSV80X for U4 (0 stock) | $127.92 | $226.18 | 51 / 16 |
| … same, microSD deleted (F5's own removal list) | $139.40 | $259.48 | 50 / 15 |

R11 cannot use Economic at all (two-sided). Standard one side vs two saves $33.77 per order (setup $25.56 + stencil
$8.21). Economic one side vs Standard one side saves $40.48 fixed plus the per-code difference (51 × $1.53 = $78.03
vs 16 × $3.07 = $49.12).

### 1.3 Which parts fail Economic's 255 ± 5 °C (validation pass 6)

From docs/ORDERING.md §3 and REQUIREMENTS M1 (Datasheet citations there): **U5 MS5611** (TE: 250 °C, 40 s), **LS120
MLT-5020** (Huaneng: 250 °C peak, ≤ 10 s above 245 °C) and **C84** polymer (no maker profile; already hand-fitted
after reflow, GAP-4). R7–R9's RF modules are gone. Removal of each limit:

| Part | Alternative | Why it removes the limit |
|---|---|---|
| U5 MS5611 | LPS28DFWTR C3263277, $6.70, 324 orderable, 260–4060 hPa (Live listing). Meets F3 (≥ 300 hPa) and the envelope's "≥ 10 km" (260 hPa ≈ 10.3 km ISA, Calculation). | ST LGA, J-STD-020 260 °C class (**Inference**: ST datasheet soldering section not read). Cheaper same-land MS5607 C97627 $4.39 keeps the 250 °C limit (TE family, Inference) → Standard only. ICP-10111 ($1.39) / BMP388-clone ($1.58) stop at 300 hPa: zero margin on F3, fail the 10 km line. LPS22DF ($3.27) has 0 stock. |
| LS120 MLT-5020 | QMB-09B-03 C96256, THT passive electromagnetic 9 mm, 3 V, 2.7 kHz, $0.118 (Live). | THT is hand-soldered by JLC (Economic supports THT), so it never sees reflow. Same Q123 / D123 drive (50 mA vs MLT-5020's 95 mA class, Inference on the drive margin). |
| C84 | unchanged, hand-fitted (owner BOM) | not reflowed |

**Not yet verified for 260 °C (must be checked before an Economic order):** the GH-1.25 clone connectors (C52037406 /
C52037408), Molex 472192001, USB-C TYPE-C-31-M-12, SRV05-4, SWPA4030 inductors, the LEDs, ISM6HG256X / STM32 TFBGA
(ST parts are normally J-STD-020 260 °C, Inference). The JST GH datasheet download was blocked; its rating is unknown here.

### 1.4 Length for one side (Calculation from R11 courtyards, Measured on `1dc2194`)

R11 courtyard bounding boxes: 2085 mm² (1335 top + 750 bottom, 216 footprints; stage B quoted 2046 mm² from
polygons). Lean deletions (U10, U11, U12, U13, U401, U402, L400, D4, 8 ESD, ~20 passives ≈ −160 mm²) and additions
(two bucks and two 4 × 4 inductors ≈ +72 mm², THT buzzer +60 mm²) give ≈ 2050 mm² (Calculation / Inference).

| Placement density (one face) | Area | Length at 46 mm |
|---|---|---|
| 56.6 % (R11's top face, 6 layers) | 3620 mm² | 79 mm |
| 50 % | 4100 mm² | 89 mm |
| **45 % (LEVIA-H7's both-face density; 4 layers, through vias)** | **4560 mm²** | **99 mm** |
| 40 % | 5130 mm² | 112 mm |

LQFP-100 instead of TFBGA adds ≈ 190 mm² (≈ +4 mm). Target **46 × ≤ 100 mm**: it keeps the JLC 4-layer $8 promotion ($25.10 with ENIG at 46 × 100;
$45.10 at 46 × 105). AVA is 47.4 × 98.5 mm (`reports/AVA board layout images.md`).
The 200 mm allowance is not needed; longer boards add $25 engineering fee + ~$3–6 board (§2).

---------------------------------------------------------------------------------------------------------

## 2. Layers and package

### 2.1 Bare-board quotes (Live, https://cart.jlcpcb.com/quote, qty 5 = JLC's minimum, FR-4 1.6 mm, green, 1 oz outer)

| Config | Price (5 pcs) | Breakdown |
|---|---|---|
| 2L 46 × 100 ENIG, tented | $21.10 | $4 promo + ENIG $17.10 |
| 2L 46 × 120 ENIG, tented | $23.90 | $4 eng. fee + $17.20 + board $2.70 |
| 4L 46 × 90 HASL, 0.5 oz inner | $8.00 | promo |
| **4L 46 × 90 ENIG, 0.5 oz inner** | **$25.10** | $8 + ENIG $17.10 |
| **4L 46 × 100 ENIG, 0.5 oz inner** | **$25.10** | $8 promo + ENIG $17.10 (re-read in a fresh session) |
| 4L 46 × 100 LeadFree HASL, 0.5 oz | $13.10 | HASL $5.10; not advised for the 0.8 mm TFBGA / 0.5 mm LGA (flatness, Inference) |
| 4L 46 × 105 / 110 ENIG 0.5 oz | $45.10 / $45.40 | promo gone: eng. fee $25 + board $3.00–3.20 → **a $20 cliff just above 100 mm** |
| 4L 46 × 90/100 ENIG, 1 oz inner (M1) | $41.81 / $41.83 | + inner 1 oz $16.71–16.73 (one 46 × 101 reading also showed the promo; treated as form lag) |
| 4L 46 × 120 ENIG 0.5 / 1 oz | $45.70 / $62.47 | eng. fee $25 + ENIG $17.20 + board $3.50 (+ $16.77) |
| 4L 46 × 150 / 200 ENIG 1 oz | $63.53 / $65.32 | |
| 4L, min via 0.25 mm / 0.2 mm / 0.15 mm (46 × 90, 1 oz) | +$16.88 / +$17.05 / +$34.11, each also adding "4-Wire Kelvin Test" $16.82 and Material $3.41 | R11's 0.2 mm-drill vias would cost ≈ +$37 on 4 layers |
| 4L Epoxy Filled & Capped (VIPPO for U401's two vias) | +$17.05 (+$3.36 plating method) | lean board deletes U401, so none |
| **6L 46 × 50 ENIG 0.5 oz (R11)** | **$48.90** at 7–8-day build; the form's default 3–4-day build adds $132.40 → $181.30 | $32 promo + ENIG $16.90 |
| 6L 46 × 50 ENIG 1 oz inner | $65.54 (7–8 day) | + $16.64 |
| 6L 46 × 90 ENIG 0.5 oz | $49.10 (7–8 day) | |
| 6L 46 × 120 ENIG 0.5 oz | $53.80 (7–8 day) | eng. fee $33 + $17.20 + board $3.60 |

Surcharges asked for: **min hole** — free at 0.3 mm drill (0.4/0.45 mm pad), extra below (rows above); **min trace** —
the form has no trace/space field for 4/6 layers (R11's 0.1 mm rules priced no surcharge; JLC multilayer limit 0.09 mm);
**via-in-pad** — Epoxy Filled & Capped +$17.05 on 4L, $0 shown on 6L; **impedance** — "Specify Stackup: No" (R10/R11 have
no controlled-impedance lines), no fee; **flying probe** — the form's only Electrical Test option is "Flying Probe
Fully Test" and it shows no fee line at qty 5 (ORDERING §8's "has a fee" is not borne out today for 5 boards).
Readings carry ±1 configuration lag risk on the form; the rows above were each read after the price was stable.

### 2.2 MCU price (Live)

| Part | 2 boards | 5 boards | Stock (orderable) |
|---|---|---|---|
| STM32H743VIH6 TFBGA-100 C964146 (R11) | $8.84 | $8.84 | 4221 (3913) |
| STM32H743VIT6 LQFP-100 C114409 (tray) | $10.70 | $9.42 | 6178 (5750) |
| STM32H743VIT6TR C5271084 (R10's code) | $12.60 | $10.79 | 298 (183) |

TFBGA is $1.86 (2 b) / $0.58 (5 b) per board cheaper than LQFP and ≈ 190 mm² smaller. A 0.8 mm-pitch TFBGA on
4 layers with free 0.3/0.45 mm vias: via centre to ball centre 0.566 mm, minus 0.2 mm ball-pad radius and 0.225 mm via
radius = 0.141 mm clearance (Calculation, ≥ JLC's 0.1 mm), so dog-bone escapes need no paid via; full escape of the
10 × 10 array on two signal layers is an **Inference** (rings 1–2 on top, ring 3 dog-boned, inner balls mostly
supply/GND). If the router disagrees, fall back to LQFP-100 (R10's proven 4-layer fan-out) at +$0.58–1.86/board.

### 2.3 Two layers

Not plausible without giving up function/plane requirements: the H743's VCAP / VDD decoupling, the BGA (or LQFP)
escape, the ground plane under the IMU/baro/crystal (REQUIREMENTS M2 partner-via rule and S-rules assume planes) and the
pyro return all rely on inner planes. It also saves only $4 per order (2L $21.10 vs 4L $25.10). Not recommended.

---------------------------------------------------------------------------------------------------------

## 3. Line-by-line BOM (R11 committed BOM, 75 lines + owner C84)

Prices: Live unit at 2 / 5 boards. Library: base = Basic, expand = Extended (pref = Preferred Extended).
Decision: **K** keep, **D** delete, **M** merge into another code, **R** replace.

| # | R11 code | Part (refs) | Unit $ 2b/5b | Lib | Decision | Replacement / reason |
|---|---|---|---|---|---|---|
| 1 | C307331 | 100 nF 0402 50 V ×25 | 0.009 | base | K (26) | −C93 (U13 gone), +1 BST, +C128 merged |
| 2 | C45783 | 22 µF 0805 25 V X5R ×6 | 0.184 | base | M → C12891 | 1206 22 µF 25 V X5R basic $0.12; single side has room |
| 3 | C23630 | 2.2 µF 0603 VCAP ×2 | 0.012 | base | K | |
| 4 | C15849 | 1 µF 0603 50 V X5R | 0.015 | base | K (3) | takes C97, C120 from #12 |
| 5 | C19666 | 4.7 µF 0603 ×3 | 0.015 | base | K (2) | C92 (CAM_IO_3V3) gone |
| 6 | C32949 | 10 pF C0G ×2 | 0.006 | base | K | crystal load |
| 7 | C15195 | 10 nF 0402 ×6 | 0.004 | base | K (5) | C408 (LDO SS) gone |
| 8 | C13585 | 10 µF 1206 50 V ×2 | 0.141 | base | K | BAT_IN |
| 9 | C85980 | 4.7 nF C0G 0603 (C81 U9 dV/dT) | 0.019 | expand | R → C1538 | 0402B472K500NT basic $0.0038, 50 V X7R; dV/dT tolerance only shifts the start ramp (margin) |
| 10 | C21397 | 22 µF 1210 X7R ×13 | 0.270 | expand | R → C12891 (11) | basic 1206 X5R 25 V $0.12, stock 1.24 M. C404/C405 deleted (two bucks give 20–68 µF each per TI Table 7-2). Bias-retained capacitance lower: re-run hot-plug and hold-up (Inference) |
| 11 | C1623 | 470 nF (C85 U11 SS) | 0.013 | base | D | U11 deleted |
| 12 | C29936 | 1 µF 0603 25 V X7R ×4 | 0.018 | expand | M → C15849 | C86/C98 (USB_LIMITED) deleted; C97, C120 → 1 µF 50 V X5R basic (X5R 85 °C ≥ bay 70 °C) |
| 13 | C21120 | 220 nF 0603 ×2 (C87 EN, C126 Q124 gate) | 0.009 | base | K | §2.4 gate network |
| 14 | C12891 | 22 µF 1206 X5R ×2 (C89, C95 damper) | 0.120 | base | K (19) | absorbs #2, #10 |
| 15 | C1848 | 1 µF 1206 50 V (C91 CAM_5V) | 0.062 | base | D | camera buck output caps cover it |
| 16 | C161115 | 100 nF 0603 X7R automotive (C128 PYRO1_OUT) | 0.056 | expand | M → C307331 | 0402 50 V X7R basic; same value and rating |
| 17 | C7519 | USBLC6-2SC6 (D4) | 0.180 | expand | D | bench-only USB; STM32 USB pins' own ESD (Inference). AVA: plain micro-USB ×3 |
| 18 | C83849 | SMBJ12CA (D8) | 0.128 | expand | R → C78399 | SMAJ12CA/TR13 $0.046, 12 V / 19.9 V clamp, 400 W (margin cut from 600 W; Inference that the harness surge is below 400 W) |
| 19 | C85098 | B340A (D9, RAW_PROTECTED) | 0.083 | expand | R → C8678 | SS34 basic $0.035, 40 V 3 A Schottky; U9's VOUT,PLS ≥ −0.8 V (Datasheet) still needs a clamp |
| 20 | C8591 | BAT54A (D120 cold pull-up) | 0.024 | expand | R → C37704 | BAT54C,215 Preferred Extended $0.015 (free on Economic); one diode used: pin 1 anode 3V3, pin 3 cathode PYRO1_COLD |
| 21 | C13612 | SRV05-4 (D121) | 0.163 | expand | K | F4 names it explicitly |
| 22 | C191023 | 1N5819WS (D123) | 0.012 | base | K (3) | + two VLOGIC diode-OR diodes (1 A, 40 V; VLOGIC load ≤ 0.37 A on USB, Calculation) |
| 23 | C535146 | ESD103-B1-02EL ×9 | 0.231 | expand | K ×1 (D402) / D ×8 | ports keep 1 kΩ series (MCU clamp current ≤ (V_esd)/1 kΩ, Inference); D402 is required by F9's EN calculation |
| 24 | C165948 | USB-C TYPE-C-31-M-12 (J3) | 0.187 | expand | K | C56112381 "TYPE-C 16PIN 2MD" $0.065 exists but brand/land unknown (Inference); saves only $0.12 |
| 25 | C133065 | SM06B-GHS-TB (J9) | 0.358 | expand | R → C52037408 | GH1.25-6PWT $0.139, 1.25 mm, right-angle, 1 A, latch (Live listing; mating with JST GH = Inference) |
| 26 | C189896 | SM05B-GHS-TB (J122) | 0.204 | expand | M → C52037408 | 6-pin body, pin 6 unused; saves a code |
| 27 | C189893 | SM02B-GHS-TB (J400) | 0.433 | expand | M → C52037406 | 4-pin body, pins 3–4 unused (dry contact, 7 µA) |
| 28 | C189895 | SM04B-GHS-TB ×3 | 0.654 | expand | R → C52037406 | GH1.25-4PWT $0.112, 4493 orderable |
| 29 | C164170 | Molex 472192001 hinged microSD | 0.730 | expand | K | no cheaper hinged socket found (push-push TF-01A $0.19 risks ejection under boost, Inference). F5 allows deleting J430 + R460–R464 + C460/C461 (−$4.37 on 2 boards incl. fee) |
| 30 | C57269 | SWPA4030S4R7MT 4.7 µH (L1) | 0.057 | expand | K ×3 | 3 bucks; TI Table 7-2 allows 2.2–4.7 µH (3.3 V) and 3.3–4.7 µH (5 V); Isat 2 A (listing) vs ≤ 1.3 A peak (Calculation, camera 1 A + ripple) |
| 31 | C1329837 | SRP5030T 6.8 µH (L400) | 1.438 | expand | M → C57269 | |
| 32 | C84256 | LED red | 0.014 | base | K | |
| 33 | C2296 | LED yellow | 0.015 | base | K | |
| 34 | C94598 | MLT-5020 (LS120) | 0.401 | expand | R → C96256 | QMB-09B-03 THT $0.118 (Economic reflow; §1.3). On Standard keep MLT-5020 or MLT-8530 C94599 $0.20 |
| 35 | C431196 | AONR21357 ×2 (Q120/Q121) | 0.355 | expand | R → C15127 | AO3401A basic $0.096: −30 V, ±12 V Vgs, 4 A, 47 mΩ @ 10 V (listing). Vgs from R119∥R120 / R121 = −(50k/60k)·V_BAT = −7.0 V at 8.4 V, −10.5 V at a wrong 3S 12.6 V: inside ±12 V (Calculation). Fire current: two in series add ≈ 0.1 Ω to a ≈ 4.5 Ω loop → four-stall 1.279 A becomes ≈ 1.25 A > 1.125 A floor (Calculation / Inference; redo with hot Rds) |
| 36 | C20917 | AO3400A ×2 (Q122, Q123) | 0.089 | base | K (3) | + Q124 |
| 37 | C431195 | AON7524 (Q124 fire FET) | 0.371 | expand | M → C20917 | AO3400A 30 V, 5.7 A, Vgs ±12 V; inductive turn-off energy ½·L·I² = ½·1 µH·(3.7 A)² ≈ 7 µJ (Calculation, 1 µH lead assumed = Inference) — avalanche rating not read. Gate network R126/R127/R128/C126 unchanged (§2.4) |
| 38 | C25744 | 10k 0402 ×26 | 0.003 | base | K (22) | −R88, R90, R91, R102, R432 (deleted functions); +1 bucks |
| 39 | C25905 | 5.1k ×6 | 0.002 | base | K | |
| 40 | C11702 | 1k 0402 ×15 | 0.001 | base | K (18) | + R150–R153 merged, −R103, R110 kept, + port FB 1k |
| 41 | C25900 | 4.7k ×2 | 0.002 | base | K | |
| 42 | C25091 | 220R ×3 | 0.002 | base | K | |
| 43 | C25741 | 100k ×4 | 0.001 | base | K (5) | + R83 OVLO bottom |
| 44 | C25790 | 470k 0402 (R80, R165) | 0.003 | expand (pref) | R → C23178 | 0603WAF4703T5E basic; same 1 % value, F6 network unchanged |
| 45 | C25774 | 300k 0402 (R81) | 0.001 | expand (pref) | R → C23024 | 0603 basic |
| 46 | C4241878 | 2M 0.1 % (R82 OVLO top) | 0.100 | expand | R → C26083 1M basic | OVLO = 1.183–1.223 V × (1 + 1M/100k) with 1 % → 12.5–14.0 V (Calculation, TI SLVSFC9 VOV(R)). Everything downstream of U9 is now ≥ 17 V-rated (TPS563201 VIN 17 V, abs 19 V; C84 25 V; MLCCs 25 V), so a full 3S (12.6 V) is tolerated, not a hazard. The old 9.77 V trip protected parts that the lean board deletes (Inference: R10's reasoning not re-read) |
| 47 | C705755 | 280k 0.1 % (R83) | 0.057 | expand | R → C25741 100k | as above |
| 48 | C852911 | 750R 0.1 % (R84 ILIM) | 0.027 | expand | R → 2 × C25867 1.5k ∥ | U9 ILIM at 750 Ω is 3.96–4.84 A (Datasheet); a 1 % resistor moves it 1 %, inside the part's ±9 % — the 0.1 % bought nothing |
| 49 | C29381 | 66.5k (R85 U10 ILIM) | 0.001 | expand | D | U10 deleted |
| 50 | C852923 | 80.6k 0.1 % (R86 U11 ILIM) | 0.026 | expand | D | U11 deleted |
| 51 | C25792 | 47k (R87 USB OVLO) | 0.002 | base | D | U11 deleted |
| 52 | C22978 | 3.3k 0603 (R92 bleed) | 0.002 | base | K | |
| 53 | C4109 | 2k ×6 | 0.002 | base | K (5) | R404 (U400 FB) gone |
| 54 | C3013496 | CRM2512 2 Ω pulse (R134) | 0.558 | expand | K | F7 shorted-igniter limit; a basic 2512 lacks a published 20–36 ms pulse rating here |
| 55 | C21190 | 1k 0603 ×4 (R150–153 servo) | 0.002 | base | M → C11702 | 0402 1k, 3.3 V logic |
| 56 | C22939 | 2.2R 0603 (R164) | 0.003 | base | K | |
| 57 | C168925 | 0.36R 2512 (R166 damper) | 0.039 | expand | K | hot-plug damper tied to U9's 28 V abs max; delete only after the hot-plug model is re-run without it (AVA has none, Inference) |
| 58 | C705636 | 56.2k 0.1 % (R400 U400 FB) | 0.027 | expand | D | port buck FB = 51k + 1k / 10k basic |
| 59 | C190095 | 10k 0.1 % ×2 (R401, R403) | 0.026 | expand | D | → 10k 1 % basic |
| 60 | C705780 | 49.9k 0.1 % (R402 LDO FB) | 0.031 | expand | D | U401 deleted |
| 61 | C23253 | 820R 0603 (R405 LDO load) | 0.002 | base | D | U401 deleted |
| 62 | C26960 | 22.6k (R430 U402 ILIM; 65 orderable) | 0.001 | expand | D | U402 deleted |
| 63 | C964146 | STM32H743VIH6 | 8.845 | expand | K | §2.2 |
| 64 | C780769 | AP63203WU-7 (U2) — min 8, −2876 orderable | 4.769 / 1.192 | expand | R → C116592 | TPS563201DDCR $0.066, 113 k orderable: VIN 4.5–17 V, 3 A, VFB 0.749–0.787 V (Datasheet). 33k/10k → 3.17–3.44 V (Calculation, inside STM32 1.71–3.6, SD/flash 2.7–3.6) |
| 65 | C97521 | W25Q128JVSIQ | 2.462 | base | K | |
| 66 | C51931514 | ISM6HG256X (U4) — 4 stock, −3 orderable | 14.337 | expand | K (or R → C46898862) | F1 ±4000 dps + F2 ≥ ±64 g. Only cheaper same-land fit: LSM6DSV80X $6.32 (±4000 dps, ±80 g high-g), 0 stock. LSM6DSV32X $4.23 (309 stock) is ±32 g: fails F2 alone; + a ≥ 64 g accelerometer (KX134 $10.67, ADXL375 $22.21, H3LIS331 $12.85) costs more. Either way consign franchised parts |
| 67 | C15639 | MS5611 (U5) | 6.496 | expand | R → C3263277 (Economic) / C97627 (Standard) | §1.3 |
| 68 | C3662793 | TPS259470LRPWR (U9) — min 7, −94 orderable | 4.604 / 1.315 | expand | R → C3662799 | TPS259470**A**RPWR $1.294, 2128 orderable, same RPW land and pinout (Datasheet device table: only the fault response differs, auto-retry vs latch-off). Keeps reverse (−15 V), OVLO, ILIM, J400 EN (§2.1). A discrete P-FET switch would save a further ≈ $1.3 + $3.07 but loses current limit and the calculated EN chain: not recommended |
| 69 | C55266 | TPS2553 ×2 (U10, U402) | 0.555 / 0.460 | expand | D | U10 → diode-OR; U402 → camera buck EN + its current limit |
| 70 | C485916 | TPS2121 (U11) | 0.920 | expand | D | diode-OR |
| 71 | C5186957 | TXU0202 (U12) | 0.863 | expand | D | 1 kΩ series + firmware pin parking |
| 72 | C89347 | TPS70933 (U13) | 0.346 | expand | D | |
| 73 | C2071044 | AP63201WU-7 (U400) | 1.225 | expand | M → C116592 | ports buck (51k + 1k / 10k → 4.57–4.96 V) and camera buck (68k / 10k → 5.74–6.25 V; RunCam Split 4 input 5–20 V per its manual quoted in docs) |
| 74 | C2878140 | TPS7A9101 (U401) | 0.805 | expand | D | + its VIPPO order condition |
| 75 | C1985619 | NX3225GA 25 MHz 8 pF (Y1) | 0.391 | expand | R → C9006 | X322525MOB4SI basic $0.095 (12 pF, ±10 ppm, 50 Ω ESR): gm_crit = 4·50·(2π·25 MHz)²·(3 + 12 pF)² = 1.11 mA/V < STM32H7 Gm_crit,max 1.5 mA/V (Calculation; C0 = 3 pF Inference; ST limit from DS12110, not re-read here) |
| – | C46550466 | C84 470 µF polymer (owner) | 0.203 | expand | K | AVA also carries a bulk cap |

Result: 75 → 51 codes; Extended non-preferred 44 → 16; parts at 2 boards $128.94 (with min-buy) → $81.55.

### 3.1 Recommended BOM (Live, 2026-11-04T01:14:47Z), Economic, 1 side

Every line with unit price at 2 and 5 boards, library and stock (columns: code, part, use, qty per board, SMT / THT,
library, unit $ at 2 boards, unit $ at 5 boards, stock / orderable):

| Code | Part | Use | Qty | Mount | Library | Unit $ 2 b | Unit $ 5 b | Stock / orderable |
|---|---|---|---|---|---|---|---|---|
| C307331 | CL05B104KB54PNC | 100nF 0402 50V: 25 R11 sites -C93 +1 BST +C128 | 26 | smt | base | 0.009 | 0.009 | 20536676/15434912 |
| C12891 | CL31A226KAHNNNE | 22uF 25V X5R 1206: 13x1210 -2, 6x0805, C89/C95 | 19 | smt | base | 0.1198 | 0.1198 | 1662882/1242972 |
| C23630 | CL10A225KO8NNNC | VCAP | 2 | smt | base | 0.0119 | 0.0119 | 2645674/2075578 |
| C15849 | CL10A105KB8NNNC | 1uF 0603 50V: C22,C97,C120 | 3 | smt | base | 0.0145 | 0.0145 | 12318109/9267456 |
| C19666 | CL10A475KO8NNNC | 4.7uF: C23,C28 | 2 | smt | base | 0.0151 | 0.0151 | 4135667/3366409 |
| C32949 | CL05C100JB5NNNC | 10pF HSE | 2 | smt | base | 0.0058 | 0.0058 | 2309579/1963176 |
| C15195 | CL05B103KB5NNNC | 10nF: C60,C94,C123,C127,C129 | 5 | smt | base | 0.0039 | 0.0039 | 5729980/4674970 |
| C13585 | CL31A106KBHNNNE | 10uF 50V 1206 BAT_IN | 2 | smt | base | 0.1413 | 0.1413 | 3046918/2144424 |
| C1538 | 0402B472K500NT | 4.7nF 0402 X7R U9 dVdT (C81) | 1 | smt | base | 0.0038 | 0.0038 | 1036290/926812 |
| C21120 | CL10B224KA8NNNC | 220nF C87,C126 | 2 | smt | base | 0.0093 | 0.0093 | 928190/757393 |
| C78399 | SMAJ12CA/TR13 | SMAJ12CA BAT_IN TVS (D8) | 1 | smt | expand | 0.0456 | 0.0456 | 207593/204515 |
| C8678 | SS34 | SS34 (D9) | 1 | smt | base | 0.0351 | 0.0351 | 3170866/2942536 |
| C37704 | BAT54C,215 | BAT54C,215 pref-ext D120 (one diode used) | 1 | smt | expand (pref) | 0.0152 | 0.0152 | 440279/418255 |
| C13612 | SRV05-4.TCT | SRV05-4 D121 | 1 | smt | expand | 0.1631 | 0.1631 | 70715/69632 |
| C191023 | 1N5819WS | 1N5819WS D123 + VLOGIC diode-OR x2 | 3 | smt | base | 0.0124 | 0.0124 | 3124765/2854796 |
| C535146 | ESD103-B1-02EL E6327 | ESD103 D402 only | 1 | smt | expand | 0.2305 | 0.2305 | 191/184 |
| C165948 | TYPE-C-31-M-12 | USB-C J3 | 1 | smt | expand | 0.1873 | 0.1873 | 167285/154583 |
| C52037408 | GH1.25-6PWT | GH1.25-6PWT J9, J122 | 2 | smt | expand | 0.1393 | 0.1393 | 2645/2622 |
| C52037406 | GH1.25-4PWT | GH1.25-4PWT J400,J410,J420,J440 | 4 | smt | expand | 0.1124 | 0.1124 | 4541/4493 |
| C164170 | 472192001 | microSD hinged J430 | 1 | smt | expand | 0.7299 | 0.7299 | 6679/6277 |
| C57269 | SWPA4030S4R7MT | 4.7uH L1 x3 bucks | 3 | smt | expand | 0.0571 | 0.0571 | 36675/35821 |
| C84256 | NCD0805R1 | LED red | 1 | smt | base | 0.0135 | 0.0135 | 2356818/1999406 |
| C2296 | KT-0805Y | LED yel | 1 | smt | base | 0.0149 | 0.0149 | 605875/538736 |
| C96256 | QMB-09B-03 | QMB-09B-03 THT buzzer | 1 | tht | expand | 0.1183 | 0.1183 | 107365/106318 |
| C15127 | AO3401A | AO3401A Q120,Q121 | 2 | smt | base | 0.0962 | 0.0962 | 1675244/1546053 |
| C20917 | AO3400A | AO3400A Q122,Q123,Q124 | 3 | smt | base | 0.0891 | 0.0891 | 913708/761716 |
| C25744 | 0402WGF1002TCE | 10k | 22 | smt | base | 0.0028 | 0.0028 | 15776399/10420493 |
| C25905 | 0402WGF5101TCE | 5.1k | 6 | smt | base | 0.0023 | 0.0023 | 4815386/4034871 |
| C11702 | 0402WGF1001TCE | 1k incl servo + port FB series | 18 | smt | base | 0.0013 | 0.0013 | 21237195/18118647 |
| C25900 | 0402WGF4701TCE | 4.7k | 2 | smt | base | 0.002 | 0.002 | 14096007/12117904 |
| C25091 | 0402WGF2200TCE | 220R | 3 | smt | base | 0.0018 | 0.0018 | 1914838/1715378 |
| C25741 | 0402WGF1003TCE | 100k (+R83 OVLO bottom) | 5 | smt | base | 0.0013 | 0.0013 | 7590885/5850326 |
| C4109 | 0402WGF2001TCE | 2k | 5 | smt | base | 0.0019 | 0.0019 | 10691542/10126084 |
| C22939 | 0603WAF220KT5E | 2.2R | 1 | smt | base | 0.0027 | 0.0027 | 254301/168534 |
| C22978 | 0603WAF3301T5E | 3.3k R92 | 1 | smt | base | 0.0022 | 0.0022 | 4988899/4401662 |
| C23178 | 0603WAF4703T5E | 470k 0603 R80,R165 | 2 | smt | base | 0.003 | 0.003 | 988018/837831 |
| C23024 | 0603WAF3003T5E | 300k 0603 R81 | 1 | smt | base | 0.0038 | 0.0038 | 508008/421668 |
| C26083 | 0402WGF1004TCE | 1M R82 OVLO top | 1 | smt | base | 0.0015 | 0.0015 | 2684706/2222363 |
| C25867 | 0402WGF1501TCE | 1.5k||1.5k ILIM | 2 | smt | base | 0.0029 | 0.0029 | 1501710/1260052 |
| C25779 | 0402WGF3302TCE | 33k 3V3 FB | 1 | smt | base | 0.0019 | 0.0019 | 2330823/2160605 |
| C25794 | 0402WGF5102TCE | 51k port FB | 1 | smt | base | 0.0019 | 0.0019 | 1149578/955851 |
| C36871 | 0402WGF6802TCE | 68k cam FB | 1 | smt | expand (pref) | 0.0012 | 0.0012 | 1155002/1094739 |
| C3013496 | CRM2512-FX-2R00ELF | R134 2R pulse | 1 | smt | expand | 0.5577 | 0.5577 | 2222/2149 |
| C168925 | 25121WF360LT4E | R166 0.36R | 1 | smt | expand | 0.0386 | 0.0386 | 1545/1545 |
| C964146 | STM32H743VIH6 | STM32H743VIH6 | 1 | smt | expand | 8.8446 | 8.8446 | 4221/3913 |
| C116592 | TPS563201DDCR | TPS563201 x3 (3V3, ports, camera) | 3 | smt | expand | 0.066 | 0.066 | 115303/113184 |
| C97521 | W25Q128JVSIQ | W25Q128 | 1 | smt | base | 2.4617 | 2.4617 | 75330/55964 |
| C51931514 | ISM6HG256XTR | ISM6HG256X | 1 | smt | expand | 14.337 | 14.337 | 4/-3 |
| C3263277 | LPS28DFWTR | LPS28DFW baro (260C, 26 kPa) | 1 | smt | expand | 6.6979 | 6.6979 | 367/324 |
| C3662799 | TPS259470ARPWR | TPS259470A U9 | 1 | smt | expand | 1.294 | 1.294 | 2044/2128 |
| C9006 | X322525MOB4SI | X322525MOB4SI basic crystal 12pF | 1 | smt | base | 0.0953 | 0.0953 | 372531/330392 |
| C46550466 | MA25V470M8x10 | C84 polymer | 1 | owner | expand | 0.2031 | 0.2031 | 110787/109984 |

 The 16 charged
Extended codes: ISM6HG256X, STM32H743VIH6, LPS28DFW, TPS259470A, 472192001, CRM2512 2 Ω, GH-4P clone, GH-6P clone,
ESD103 (D402), TPS563201, USB-C, SWPA4030, SRV05-4, QMB-09B-03, SMAJ12CA, 0.36 Ω 2512. Preferred (free): 68k, BAT54C.

### 3.2 Stock (Live)
Short today: **U4 ISM6HG256X** (4 in stock, −3 orderable) on every variant; consign franchised parts (ORDERING §8.1).
U2's and U9's shortages disappear (TPS563201 113 k, TPS259470A 2128 orderable). LPS28DFW 324 orderable (enough for 5 + spares).

### 3.3 Divider calculations (Calculation on Datasheet thresholds, 1 % resistors, worst case)
- 3V3: 0.749 × (1 + 33·0.99/10.1) = 3.17 V … 0.787 × (1 + 33·1.01/9.9) = 3.44 V.
- Ports: (51k + 1k)/10k → 4.57 … 4.96 V (≤ 5.0 V for the M100 Mini "3.3–5 V", r10_plan; LR900-F range Inference).
- Camera: 68k/10k → 5.74 … 6.25 V; RunCam Split 4 input 5–20 V (manual as quoted in docs). Below ≈ 6.3 V of VIN the buck
  runs at maximum duty and tracks VIN (Inference); at the four-stall 5.71 V BAT_IN the camera still gets > 5 V minus harness.
- U9 OVLO 12.5–14.0 V; ILIM 3.96–4.84 A (as now).

### 3.4 Pyro / AGENTS §2 check
§2.1 J400 still drives U9 EN (unchanged network R80/R81/R165/C87, D402). §2.2 pyro bus still after the Q120/Q121
load switch, fed from BAT_IN. §2.3 firmware unchanged. §2.4 Q124 keeps R126 220 Ω series, R127/R128 pull-downs,
C126 gate–source; Q120/Q121 keep R119/R120/C120; Q122 keeps R122/R123/C123; all off in reset. §2.5 labels above.

---------------------------------------------------------------------------------------------------------

## 4. BPS.space AVA as the benchmark

Sources: repo `reports/AVA board layout images.md` (with its links: YouTube "The AVA Flight Computer" 8:54
https://youtu.be/qaWvCy2DRSA?t=534 — four layers, 1.6 mm, 0.15 mm trace/space, 1 oz, 0603 passives on the back, ICs at
45°; @bps_space 2020-08-27 https://x.com/bps_space/status/1299081393029382144; "Troubleshooting AVA's CAN bus" 3:29
https://youtu.be/AXdSFODM97E?t=209 for the R1→R2 changes), r10_plan.md §1 (AVA comparison), Hackaday 2020-10-02
https://hackaday.com/2020/10/02/advanced-model-rocket-flight-computer-reaching-for-the-stars/ (MK20DX256 + two ATSAMD21,
each with its own micro-USB; two IMUs, GPS, barometer). A Hackster summary (via search, page itself 403) names a Rohm
KX134 ±64 g accelerometer and a u-blox ZOE-M8Q. **No AVA schematic or BOM is public** (Joe Barnard keeps them private),
so every "AVA has / lacks X" below is an **Inference** from photos and spoken descriptions.

| Our protection / margin part | AVA equivalent | Rule that needs ours | Verdict |
|---|---|---|---|
| U9 eFuse (reverse, OVLO, ILIM, J400 switch) | none visible; R3 adds a two-terminal diode between BATT and 12V terminals | §2.1 (switch), F9 | keep, cheaper A variant |
| D8 TVS on BAT_IN | R3's diode (likely) | U9 abs max (hot-plug model) | keep, SMAJ |
| D9 Schottky at U9 output | none visible | U9 VOUT,PLS ≥ −0.8 V (Datasheet) | keep, SS34 basic |
| R166 + C89/C95 hot-plug damper | none visible | hot-plug model only | candidate delete after re-simulation |
| U10 USB limiter, U11 mux, D4 USB ESD | three bare micro-USB ports | none (bench mode) | delete |
| 8 port ESD diodes | none visible on UART JSTs | none (F10 describes, not requires) | delete |
| D402 J400 ESD | n/a (no dry-contact EN) | F9 calculation | keep |
| SRV05-4 servo clamp | unknown | F4 names it | keep |
| U402 / U12 / U13 camera limiter and isolation | camera switched by a transistor | none | replace with camera buck EN + 1 kΩ |
| U401 port LDO | SOT-223 linear on the bottom (R2/R3) | none | replace with a buck |
| 0.1 % resistors | unknown | none (1 % meets every window, §3.3) | replace |
| R134 2 Ω | unknown ("pyro-channel protection" added in R2) | F7 | keep |
| Q120/Q121 load switch, gate networks | unknown | §2.2, §2.4 | keep (basic FETs) |
| C84 bulk | bulk cap on the back | F6 | keep |
| Buzzer | AST-1240 transducer (Inference) | F11/F12 | keep, cheaper |

**Layout lessons that cut our cost:** AVA is 4-layer (not 6), ~47 × 99 mm (≈ our 46 × 100 target), 0.15 mm rules (we
need 0.1 mm only for TFBGA escape; JLC prices both the same), and one connector family per job. AVA puts parts on both
sides because Joe assembles by hand; at JLC that choice costs +$33.77 (Standard two-sided) and rules out Economic, so
the single-sided board is the deliberate deviation from AVA. AVA's screw terminals (R10's DB125 path) are THT parts;
on Economic each THT joint costs $0.0164 + $3.58/order, and R10's DB125 codes add Extended fees — GH clones are cheaper.

---------------------------------------------------------------------------------------------------------

## 5. Caveats
- The JLC quote form was read through the page UI; two of three browser sessions were lost mid-run and re-run; each
  quoted row was read after the price stopped changing. Prices change daily.
- Joint fees, shipping, tax, attrition and the owner's C84 hand-fit are excluded from every total (same for both sides).
- R11's 5-board figure: $482.91 without JLC minimum purchases, $489.13 with them.
- No layout exists for the recommended board; the length is an area estimate, not a placement.
