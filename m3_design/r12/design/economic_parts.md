# R12 BOM against JLC Economic PCBA (research lane, 2026-11-04)

Read-only audit of every R12 BOM line against JLC Economic PCBA. Nothing in the board, schematic, `r12_parts.py`,
`r12_place.tsv` or `R12_DECISIONS.md` was changed. Evidence labels follow AGENTS §2.5: **Live** (JLC page or API,
2026-11-04T22:00–22:25Z), **Datasheet** (the maker datasheet LCSC/JLC serve for that code, URL given), **Inference**
(anything not read directly).

Input: the quote BOM and CPL generated from the placed board at `3c28986` (54 JLC lines, 173 placements, every one
on Top), plus the two owner-fitted lines C84 and LS120 (`jlc_r12_stock.json`). Note: the quote BOM already carries
D-R12-29 / -31 (J121 DB125 C52993880; SH 1.0 ports C7430446 / C7430448), which `jlc_r12_stock.json` still lists as the
GH clones.

## Resolution (2026-11-04, after this audit; R12_DECISIONS D-R12-49 … -54)

The owner chose "go fully Economic" and **accepts parts rated to a 250 °C peak on Economic's 255 ± 5 °C reflow** (owner
deviation, D-R12-49, owner acceptance A-9; the effect of the 5–10 °C over-peak on each part is an **Inference**). JLC's
"Standard Only" flag remains a hard rule. Item by item:

| Item | Audit verdict | Resolution |
|---|---|---|
| U4 ISM6HG256XTR (§3.1) | FAIL: Standard Only | **Resolved**, D-R12-50: LSM6DSVETR (C41785564) on the same land and nets (pin map from JLCEDA C41785564; ST datasheet for the "E" variant not found: Inference); plus D-R12-51 below for F2 |
| F2 high-g channel (§3.5.1) | – | **Resolved**, D-R12-51: new U6 FXLS90322AESR2 (C5190712), XY medium-g (±150 g max; NXP part page), SPI on SPI1 with HG_CS on PA10, C33 100 nF; NXP part page: MSL 3, 260 °C / 40 s. The listing's "±500 g, XYZ" is wrong for this part number |
| U5 LPS28DFWTR (§3.2) | FAIL: Standard Only | **Resolved**, D-R12-52: MS5607-02BA03 (C97627, Economic) on R11's MS5611 land; 250 °C / 40 s accepted under D-R12-49. The KP215F1701 analog route of §3.5.3 was not taken |
| D5 / D6 / D9 SS34 (§3.3) | FAIL: 250 °C | **Resolved by acceptance** (D-R12-49): SS34 kept; B340A not adopted |
| D121 SRV05-4 (§3.4) | UNVERIFIED | **Kept** (Economic-flagged; D-R12-49); ProTek swap not made |
| J430 472192001 (§3.4) | UNVERIFIED (250 °C, Inference) | **Kept** (D-R12-49); microSD stays |
| Other UNVERIFIED lines (§3.4) | UNVERIFIED | unchanged; all are JLC-flagged Economic; O-R12-02 |

New cost (Live 2026-11-04T23:25:09Z, `r12_cost.json`): 2 boards $159.92 ($79.96 per board), 5 boards $260.08 ($52.02
per board); every JLC-placed line is Economic-flagged.

## 0. Answer in short

| Verdict | Lines |
|---|---|
| OK | 36 |
| FAIL | 3: **U4** ISM6HG256XTR and **U5** LPS28DFWTR (JLC marks both "Standard Only"), **D5 / D6 / D9** SS34 (maker rating 250 °C) |
| UNVERIFIED | 15 (no maker peak-reflow figure found; all are JLC-flagged "Economic and Standard") |
| N/A (owner-fitted, never reflowed) | 2: C84, LS120 (superseded by D-R12-85: both now JLC-assembled, see the resolution note below the parts table) |

**Why the owner's "some parts are not Economic-compatible" is true:** every JLC part page carries a "PCBA Type" field.
For 52 of the 54 JLC lines it reads "Economic and Standard"; for **U4 (C51931514)** and **U5 (C3263277)** it reads
**"Standard Only"** (Live, jlcpcb.com/partdetail pages; JLC's component-detail API gives no reason; U5's record also
has `needAuditFlag: true`). JLC states no reason on the page; that the flag follows the listing rather than the package
is an **Inference** from the pattern below (genuine Bosch BMP388 and Infineon DPS368 are "Standard Only", while
Tokmas clones of the same parts in the same packages are "Economic and Standard").

The JLC flag does not track the maker's thermal rating: MS5611 / MS5607 / HP203B (makers' limit 250 °C) are flagged
"Economic and Standard", while LPS28DFW (J-STD-020) is "Standard Only". Both tests are applied here.

**No Economic-flagged replacement for U4 or U5 meets the requirements with a verified ≥ 260 °C rating** (§3). Every
in-stock high-g accelerometer and every genuine ST / Bosch / Infineon / TDK barometer checked is "Standard Only". This
is the decision for the owner; §3 lists the options and what each changes.

## 1. Economic limits used (Live, JLC capabilities page, as given in the brief and cost_study §1.1)

One-side placement (SMT, plus THT hand-soldered); fixed reflow 255 ± 5 °C, so a reflowed part needs a maker peak rating
of at least 260 °C; smallest package 0402; IC pin pitch ≥ 0.4 mm, BGA pitch ≥ 0.5 mm; no castellated holes or edge
plating; and the per-part JLC "PCBA Type" flag.

Package check (Calculation on the R12 footprints in `m3_design/r12/kilib/rocket.pretty`): every part is on Top; the
smallest bodies are 0402 and ESD103 TSLP-2-20 (1.0 × 0.6 mm, Datasheet Fig. 13, i.e. 0402 size); the finest pitches are
U9 RPW 0.45 mm (pins 2–3 of `M3_TPS25947_RPW`), USB-C J3 0.5 mm, U4 LGA-14 0.5 mm, U1 TFBGA 0.8 mm. No footprint
has castellations. **Every line passes the package limits**; failures below are all thermal or JLC flag.

## 2. Line by line

Columns: JLC = PCBA Type on the part page (E = "Economic and Standard", **S = "Standard Only"**), MSL as JLC lists it.
"Rating" is the maker's peak reflow / soldering-heat figure read in the datasheet at the link. Datasheet links are the
LCSC copies JLC points to (`https://www.lcsc.com/datasheet/lcsc_datasheet_<id>.pdf`; the id is given). JLC page:
`https://jlcpcb.com/partdetail/<suffix>/<code>`.

### 2.1 Resistors (UNI-ROYAL) — all OK

Rating (Datasheet, same UNI-ROYAL chip-resistor general spec for every code below): "Resistance to soldering heat:
dip … solder bath 260 ± 5 °C, 10 ± 1 s" and leaching 30 s at 260 °C. JLC E for all. Package R0402 / R0603 / R2512, OK.

| Code | Part | Refs | LCSC datasheet id | Verdict |
|---|---|---|---|---|
| C11702 | 0402WGF1001TCE 1k | R9 R100 R101 R110 R122 R127 R162 R440 R441 R450 R451 R470 R471 | 2206010216_UNI-ROYAL-Uniroyal-Elec-0402WGF1001TCE_C11702 | OK |
| C25091 | 0402WGF2200TCE 220R | R32 R33 R126 | 2205311900_…-0402WGF2200TCE_C25091 | OK |
| C25741 | 0402WGF1003TCE 100k | R60 R83 R119 R120 R431 | 2206010100_…-0402WGF1003TCE_C25741 | OK |
| C25744 | 0402WGF1002TCE 10k | R5 R10 R11 R61 R89 R112 R121 R128 R131 R154–R157 R163 R167 R401 R434 R435 R460–R464 | 2411221126_…-0402WGF1002TCE_C25744 | OK |
| C25765 | 0402WGF2002TCE 20k | R15 | 2206010100_…_C25765 | OK |
| C25779 | 0402WGF3302TCE 33k | R93 | 2206010100_…_C25779 | OK |
| C25792 | 0402WGF4702TCE 47k | R14 R400 | 2206010100_…_C25792 | OK |
| C25794 | 0402WGF5102TCE 51k | R433 | 2411221126_…_C25794 | OK |
| C25867 | 0402WGF1501TCE 1.5k | R84 R94 | 2206010045_…_C25867 | OK |
| C25900 | 0402WGF4701TCE 4.7k | R12 R13 R111 R404 | 2206010045_…_C25900 | OK |
| C25905 | 0402WGF5101TCE 5.1k | R7 R8 R104 R107 R129 R132 R173 R175 | 2206010045_…_C25905 | OK |
| C26083 | 0402WGF1004TCE 1M | R82 | 2206010030_…_C26083 | OK |
| C4109 | 0402WGF2001TCE 2k | R105 R106 R123 R130 R133 R178 R180 | 2206010230_…_C4109 | OK |
| C21190 | 0603WAF1001T5E 1k | R150–R153 | 2206010130_…_C21190 | OK |
| C22939 | 0603WAF220KT5E 2.2R | R164 | 2206010130_…_C22939 | OK |
| C22978 | 0603WAF3301T5E 3.3k | R92 | 2206010116_…_C22978 | OK |
| C23024 | 0603WAF3003T5E 300k | R81 | 2206010116_…_C23024 | OK |
| C23178 | 0603WAF4703T5E 470k | R80 R165 | 2206010116_…_C23178 | OK |
| C168925 | 25121WF360LT4E 0.36R 2512 | R166 | 2205312316_…-25121WF360LT4E_C168925 | OK |

### 2.2 Capacitors — all OK

Samsung (Datasheet, Samsung MLCC general spec served for every CL code): "Pb-free plating, reflow soldering 260 +0/−5 °C,
10 s max", solder-heat test 260 ± 5 °C 10 s. FH (Datasheet, FH general MLCC spec): "Resistance to solder temperature
265 ± 5 °C, 10 ± 1 s". JLC E, MSL 1 for all.

| Code | Part | Refs | LCSC datasheet id | Verdict |
|---|---|---|---|---|
| C12891 | CL31A226KAHNNNE 22 µF 1206 | C6 C8 C10 C82 C89 C95 C400 C406 C407 C431 C433 C434 C461 | 2304140030_Samsung-Electro-Mechanics-CL31A226KAHNNNE_C12891 | OK |
| C13585 | CL31A106KBHNNNE 10 µF 50 V 1206 | C80 C96 | 2304140030_…_C13585 | OK |
| C15195 | CL05B103KB5NNNC 10 nF 0402 | C60 C94 C123 C127 C129 | 2304140030_…_C15195 | OK |
| C15849 | CL10A105KB8NNNC 1 µF 0603 | C22 C97 C120 | 2304140030_…_C15849 | OK |
| C19666 | CL10A475KO8NNNC 4.7 µF 0603 | C23 C28 | 2304140030_…_C19666 | OK |
| C21120 | CL10B224KA8NNNC 220 nF 0603 | C87 C126 | 2304140030_…_C21120 | OK |
| C23630 | CL10A225KO8NNNC 2.2 µF 0603 | C19 C20 | 2304140030_…_C23630 | OK |
| C307331 | CL05B104KB54PNC 100 nF 0402 | C5 C13–C18 C21 C24 C29–C32 C83 C88 C99 C128 C402 C410 C420 C432 C444 C460 | 2304140030_…_C307331 | OK |
| C1538 | FH 0402B472K500NT 4.7 nF | C81 | 2304140030_FH--Guangdong-Fenghua-Advanced-Tech-0402B472K500NT_C1538 | OK |
| C1549 | FH 0402CG180J500NT 18 pF C0G | C25 C26 | 2304140030_…-0402CG180J500NT_C1549 | OK |

### 2.3 Semiconductors, magnetics, connectors

| Code | Part | Refs | Package / limits | Maker rating (Datasheet unless marked) | JLC | Verdict |
|---|---|---|---|---|---|---|
| C964146 | STM32H743VIH6 | U1 | TFBGA-100, 0.8 mm, OK | Not in DS12110 (LCSC 2203091604_…_C964146); JLC lists MSL 3. 260 °C class is an **Inference** (ST ECOPACK practice) | E | UNVERIFIED |
| C97521 | W25Q128JVSIQ | U3 | SOIC-8 1.27 mm, OK | "Compliant with JEDEC J-STD-20C for small body … Pb-free assembly" (1811142111_Winbond-Elec-W25Q128JVSIQ_C97521); the 260 °C value of that class is an **Inference** (J-STD-020 table not read) | E | UNVERIFIED |
| C51931514 | ISM6HG256XTR | U4 | LGA-14 2.5 × 3, 0.5 mm, OK | ST DS15034 not downloadable (st.com HTTP/2 refusal); no LCSC datasheet | **S** | **FAIL** (Standard Only; also 4 in stock, 0 pre-sale: unorderable) |
| C3263277 | LPS28DFWTR | U5 | CCLGA-7 2.8 × 2.8, OK | "qualified for soldering heat resistance according to JEDEC J-STD-020" (2211080600_STMicroelectronics-LPS28DFWTR_C3263277) | **S** | **FAIL** (Standard Only) |
| C3662799 | TPS259470ARPWR | U9 | VQFN-HR 10, 0.45 mm, OK | TI orderable table: Level-2-**260C**-1 YEAR (2410121729_…_C3662799) | E | OK |
| C2841056 | LMR50410XDBVR | U2 | SOT-23-6, OK | Level-2-**260C**-1 YEAR (2303132130_…_C2841056) | E | OK |
| C468250 | TPS563208DDCR | U400 U403 | SOT-23-6 (DDC), OK | Level-1-**260C**-UNLIM (2004061031_…_C468250) | E | OK |
| C20917 | AO3400A | Q122 Q123 Q124 | SOT-23, OK | None in AOS datasheet (1811081213_…_C20917; also aosmd.com/res/datasheets/AO3400A.pdf read) | E | UNVERIFIED |
| C15127 | AO3401A | Q120 Q121 | SOT-23, OK | None in AOS datasheet (2412061733_…_C15127; aosmd.com AO3401A.pdf read) | E | UNVERIFIED |
| C37704 | BAT54C,215 (Nexperia) | D120 | SOT-23, OK | None in datasheet (2407241028_Nexperia-BAT54C-215_C37704); nexperia.com returned 403 | E, Preferred | UNVERIFIED |
| C535146 | ESD103-B1-02EL E6327 | D402 | TSLP-2-20 1.0 × 0.6 (0402 size), OK | None in Infineon Rev 1.3 (2304140030_…_C535146) | E | UNVERIFIED |
| C13612 | SRV05-4.TCT (Semtech) | D121 | SOT-23-6, OK | None in Semtech datasheet (1809212114_SEMTECH-SRV05-4-TCT_C13612) | E | UNVERIFIED |
| C78399 | SMAJ12CA (Brightking) | D8 | SMA, OK | "Peak temperature (TP) 260 °C"; MSL 1 per J-STD-020 (2304140030_Brightking-SMAJ12CA-TR13_C78399) | E | OK |
| C8678 | SS34 (MDD) | D5 D6 D9 | SMA, OK | "High temperature soldering guaranteed: **250 °C / 10 s** at terminals" (2407101107_MDD-Microdiode-Semiconductor-SS34_C8678) | E | **FAIL** (250 °C < 255 ± 5 °C) |
| C191023 | 1N5819WS (Hottech) | D123 | SOD-323, OK | None (2409300937_Guangdong-Hottech-1N5819WS_C191023) | E | UNVERIFIED |
| C2296 | KT-0805Y (KENTO) | LED2 | 0805, OK | "Reflow soldering: 260 °C, 10 s" (1806151129_Hubei-KENTO-Elec-KT-0805Y_C2296) | E | OK |
| C84256 | NCD0805R1 (NationStar) | LED1 | 0805, OK | None (2409272203_Foshan-NationStar-Optoelectronics-NCD0805R1_C84256) | E | UNVERIFIED |
| C9006 | X322525MOB4SI (YXC) | Y1 | 3.2 × 2.5, OK | None (one-page YSX321SL sheet, 2403291504_…_C9006) | E | UNVERIFIED |
| C57269 | SWPA4030S4R7MT (Sunlord) | L1 L400 L401 | 4 × 4, OK | Not found (image-only PDF, 2310251551_Sunlord-SWPA4030S4R7MT_C57269) | E | UNVERIFIED |
| C3013496 | Bourns CRM2512-FX-2R00ELF | R134 | 2512, OK | Soldering profile "Peak 260 +5/−0 °C", MSL 1 (wmsc v2/lcsc 2206201745_BOURNS-CRM2512-FX-2R00ELF_C3013496) | E | OK |
| C165948 | HRO TYPE-C-31-M-12 | J3 | USB-C 0.5 mm, OK | Not found (one-page drawing, 2205251630_…_C165948) | E | UNVERIFIED |
| C164170 | Molex 472192001 microSD | J430 | 1.1 mm, OK | No datasheet at JLC/LCSC; molex.com refused. Distributor mirrors are summarised by search as "process temperature max **250 °C**, 3 s, 2 cycles" (**Inference**, not read on a Molex document) | E | UNVERIFIED (likely FAIL) |
| C7430446 | Megastar ZX-SH1.0-4PWT | J400 J420 J440 | SH 1.0, OK | Not found (one-page drawing, 2306191203_Megastar-ZX-SH1-0-4PWT_C7430446) | E | UNVERIFIED |
| C7430448 | Megastar ZX-SH1.0-6PWT | J9 J122 J410 | SH 1.0, OK | Not found (2306191203_Megastar-ZX-SH1-0-6PWT_C7430448) | E | UNVERIFIED |
| C52993880 | DORABO DB125-3.5-2P-BK-S | J121 | THT (JLC "Wave Soldering", hand-soldered on Economic) | Not reflowed; no datasheet at JLC. Reflow limit does not apply | E | OK (THT); stock 186 (Live) |
| C46550466 | MA25V470M8x10 | C84 | owner-fitted | not reflowed (R10 GAP-4) | E | N/A (superseded, D-R12-85) |
| C96256 | QMB-09B-03 | LS120 | owner-fitted THT | 250 °C (D-R12-16) but not reflowed | E | N/A (superseded, D-R12-85) |

**D-R12-85 (owner, 2026-11-05: "I want everything to be asssembled by jlc").** No part is owner-fitted any more:

| Code | Part | Refs | Assembly | Maker reflow rating | JLC PCBA type (Live 2026-11-05) | Verdict |
|---|---|---|---|---|---|---|
| C5246546 | Honor Elec HV1E477M0810PZ, 470 µF 25 V polymer, D8 × 10.5 (replaces C46550466) | C84 | SMT, reflowed | Peak 255 °C for 5 s, 230–255 °C ≤ 30 s (Honor CDHV specification item 14, LCSC C5246546 PDF, Datasheet); the 255 ± 5 °C upper end is 5 °C over it, inside the owner's A-9 acceptance of 250 °C-rated parts | Economic and Standard (componentProductType 0, the value every Economic line shows; Standard-only U4 / U5 read 2) | OK under A-9 |
| C46550466 | jieerrui MA25V470M8x10 (dropped) | — | — | No reflow figure in its 4-page MA series sheet (JLC mirror, Datasheet read 2026-11-05) | Economic and Standard | not usable: no published rating |
| C96256 | QMB-09B-03 | LS120 | JLC THT assembly (hand-soldered after reflow, as J121) | Not reflowed; the Huawha sheet's solderability test is a 255 ± 5 °C dip for 3 s (item 8) | Economic and Standard | OK (THT) |
| C190095 | YAGEO RT0402BRD0710KL 10k 0.1 % 25 ppm/K (D-R12-83) | R401 | SMT | Not read (YAGEO RT series; O-R12-02 class, Inference) | Economic and Standard | UNVERIFIED (as the other unread lines) |

Pyro / gate / fire-path lines (J121, Q120–Q124, R134 and their gate R / C, D402): J121, R134 and every gate R / C
(R119, R120, R122, R123, R126, C120, C123, C126 …) are OK. Q120–Q124 (AOS) and D402 (Infineon) are UNVERIFIED only
because their makers' datasheets give no reflow figure; no swap is proposed for them (owner rule), see §3.4.

## 3. Alternatives for every FAIL and UNVERIFIED line

Prices: JLC tier price at the order quantity (2 boards / 5 boards), Live 2026-11-04T22Z. Feeder fee $3.07 per Extended
code per order on Economic; Basic free; Preferred Extended free is an **Inference** (O-R12-12).

### 3.1 U4 ISM6HG256XTR (FAIL: Standard Only, and unorderable)

Requirements: F1 gyro ≥ ±4000 dps; F2 accelerometer ≥ ±64 g plus a precise low-g channel.

| Candidate | LCSC | JLC flag | Stock (Live) | Price 2 / 5 | Meets F1 / F2? |
|---|---|---|---|---|---|
| LSM6DSV320XTR (same land and pin map, R10 second fallback) | C26633007 | **S** | 27 / 6 pre-sale | $13.19 | yes / yes, but Standard Only |
| LSM6DSV80XTR (same land) | C46898862 | **S** | 0 | – | yes / yes (±80 g), Standard Only, no stock |
| LSM6DSV16XTR, LSM6DSV32XTR | C5267406, C22461202 | **S** | in stock | $3.36, $4.23 | yes / no (±16, ±32 g) |
| **ICM-45686** (TDK) | **C22459454** | **E** | 2018 / 1900 | $10.24 / $10.24 | yes (±4000 dps) / **no: ±32 g max** (Datasheet DS-000577, LCSC 2411220643_TDK-InvenSense-ICM-45686_C22459454) |
| KX134-1211 (±64 g), ADXL375 (±200 g), ADXL372, H3LIS331DL, ICM-40609-D, BMI088 | C2157908, C481898, C579465, C2655074, C5360621, C194919 | all **S** | – | – | high-g partners, all Standard Only |

**No drop-in exists on Economic.** Options, best first:
1. **Keep ISM6HG256X / LSM6DSV320X and take U4 off the JLC order** (land unchanged, no routing change); fit it after
   delivery by hot air with a stencil (owner or a third party). LGA-14 at 0.5 mm with no leads to inspect: the fit
   risk and the need for an X-ray or electrical check are an **Inference**. Parts must be bought elsewhere (no
   franchised stock on 2026-11-01, AGENTS R10 row). JLC parts −$14.34 per board and −$3.07 feeder per order.
2. **ICM-45686** on Economic: needs a new land (LGA-14 2.5 × 3.0 × 0.81 mm, 0.5 mm, TDK Fig. 4), a pin-map check against
   R12's U4 nets (TDK's pin order differs from ST's: **Inference**, not compared pin by pin), a new IMU axis map, a new
   driver, and it **breaks F2** (±32 g against the 37 g flight peak: clips in boost). Saves $4.10 per board. Not
   recommended unless the owner relaxes F2.
3. Move the whole order to Standard: defeats D-R12-01 (cost_study §1.2: about +$40 fixed plus $1.53 per code).

Reflow ratings of the candidates were not read (ST datasheets not downloadable; ICM-45686's reflow section not found by
search of the text): **UNVERIFIED** for each.

### 3.2 U5 LPS28DFWTR (FAIL: Standard Only)

Requirement: F3 readings to ≥ 300 hPa (D-R12-13 also wanted the 260 hPa / 10 km margin).

| Candidate | LCSC | JLC flag | Stock | Price 2 / 5 | Range | Maker reflow | Notes |
|---|---|---|---|---|---|---|---|
| LPS22HHTR, LPS25HBTR, LPS22DF, LPS33HW | C2827824, C87898, C3253714, C2760770 | **S** | – | – | 260–1260 hPa | – | Standard Only |
| BMP581, BMP388 (Bosch), DPS368 (Infineon), ICP-20100, SPL07-003 | C5362283, C779278, C3232508, C5343527, C3253727 | **S** | – | – | – | – | Standard Only |
| MS5611 / MS5607 (TE) | C15639 / C97627 | E | 1429 / 3645 | $6.50 / $4.39 | 10–1200 mbar | **250 °C, 40 s** (Datasheet 1808280521_…_C15639) | Economic-flagged but below 255 ± 5 °C: FAIL (the reason R12 dropped it) |
| HP203B (HopeRF) | C138665 | E | 2477 | $1.27 | – | **250 °C, 40 s** (Datasheet 1811071023_…_C138665) | FAIL on rating |
| **BMP388 (Tokmas clone)** | **C54582187** | **E** | 8196 / 8122 | $1.58 / $1.58 | 300–1250 hPa for Bosch's BMP388; the clone's range is an **Inference** | **no datasheet at JLC: UNVERIFIED** | LGA-10 2 × 2, MSL 2a |
| **DPS368 (Tokmas clone)** | **C55090144** | **E** | 10191 / 10178 | $2.16 / $2.16 | 300–1200 hPa for Infineon's DPS368; clone **Inference** | **UNVERIFIED** | LGA-8 2.0 × 2.5, MSL 2a |

**No verified drop-in exists on Economic.** Options:
1. **Keep LPS28DFW and take U5 off the JLC order**; fit after delivery by hot air (CCLGA-7, 1.125 mm min pad spacing,
   easier than U4; **Inference**). No land, placement or routing change. JLC parts −$6.70 per board, −$3.07 per order.
2. **Tokmas BMP388 clone** C54582187 (Economic): −$5.11 per board. Changes: new LGA-10 2 × 2 land, new placement and
   I²C / supply routing round U5, SDO / CSB strapping, a BMP3xx driver; range floor 300 hPa (F3 met with zero
   margin, the 10 km line lost); clone accuracy and reflow rating unverified. Request the Tokmas datasheet before use.
3. Tokmas DPS368 clone C55090144: same pattern, −$4.53 per board, LGA-8 land.

### 3.3 D5 / D6 / D9 SS34 MDD C8678 (FAIL: 250 °C)

**Proposed: Vishay B340A-E3/61T, C15570** — same SMA (DO-214AC) land and polarity band, a drop-in. Datasheet
(LCSC 1810311715_Vishay-Intertech-B340A-E3-61T_C15570): "Meets MSL level 1, per J-STD-020, LF maximum peak of
DO-214AC (SMA) **260 °C**"; 40 V, 3 A; VF max 0.55 V at 3 A (SS34 MDD: 0.55 V, equal); IFSM 65 A (SS34: 80 A, lower;
that 65 A covers R12's surge cases is an **Inference** for the O-R12-08 re-run). JLC E, MSL 1, Extended, 59 425 in stock,
$0.0957 at 6 and at 15 pieces. Electrical change: none intended; the PA6 window (O-R12-07) uses SS34's VF and should be
re-checked with B340A's curve.
Alternate: Diodes B340A-13-F C85098 ($0.0834, VF max 0.50 V, "MSL 1 per J-STD-020" without a temperature: 260 °C is an
Inference) — lower VF moves the PA6 window more.

### 3.4 UNVERIFIED lines

| Line | Proposal | Drop-in? |
|---|---|---|
| D121 SRV05-4 Semtech C13612 | **ProTek SRV05-4-P-T7, C85364** — "Solder reflow temperature 260–270 °C"; 500 W / 30 A (8/20 µs) vs Semtech 300 W / 12 A; pin configuration 1 I/O1, 2 GND, 3 I/O2, 4 I/O3, 5 REF, 6 I/O4 (Datasheet 1809192313_ProTek-Devices-SRV05-4-P-T7_C85364); SOT-23-6; JLC E, **Preferred Extended**, 14 764 / 9 422; $0.2349 at 2 and 5. That Semtech's pin order is the same is read from its pin figure (1-6 numbering); confirm on the land before swapping. Alternate: Littelfuse SRV05-4HTG-D C1975211 ($0.1699, "peak 260 +0/−5 °C", Extended) | yes |
| D123 1N5819WS Hottech C191023 | No candidate with a stated rating in stock found (Vishay BAT54WS-E3-08 C917483 and Nexperia PMEG4005EJ C426868 datasheets give none). Keep; ask JLC / Hottech | – |
| LED1 NCD0805R1 C84256 | KENTO KT-0805R C2295 (red, family of LED2 which states 260 °C; its own datasheet text is not extractable: **Inference**); Extended (+$3.07 per order). Land `M3_NCD0805R1_K1` vs `M3_KT0805Y_A1`: pin 1 polarity differs, so it needs LED2's footprint or a 180° rotation. Not recommended for cost | land / rotation |
| Q120 Q121 AO3401A, Q122–Q124 AO3400A | **No swap (pyro / gate rule).** AOS datasheets give no reflow figure; obtain AOS's MSL / peak statement (aosmd.com product pages timed out). A third-party AO3400A sheet (GOOD-WORK) gives 260 +0/−5 °C (search summary, **Inference**, not AOS) | – |
| D402 ESD103 C535146 | **No swap (fire path).** Ask Infineon / check its product page for the TSLP-2-20 MSL / peak (not in the datasheet) | – |
| D120 BAT54C Nexperia C37704 | Keep (Nexperia page 403). onsemi BAT54CLT1G C14308 is the same SOT-23 pin-out, but its datasheet also gives no figure: no gain | – |
| U1 STM32H743VIH6, U3 W25Q128JVSIQ | No alternative; confirm on st.com / winbond.com. W25Q128 cites J-STD-20C Pb-free (260 °C class is an Inference) | – |
| Y1 YXC, L1/L400/L401 Sunlord, J3 HRO USB-C, J400/J410/J420/J440/J9/J122 Megastar SH | No alternative found with a published rating on JLC (the LCSC copies are drawings). Ask the makers; these are JLC-flagged Economic | – |
| J430 Molex 472192001 | Search-reported 250 °C limit (Inference). LCSC copies of the in-stock alternatives (Molex 1040310811 C585350, HRO TF-01A C91145, XKB XKTF-015-N C381082, all JLC E) are drawings with no rating either. Any of them is a **new land and placement**, not a drop-in (472192001 is a hinged socket). Options: confirm the rating on Molex PS-47219-001; or delete J430 (cost_study §1.2 lists microSD deletion, F5 secondary log) | no |

### 3.5 Wider search for U4 and U5 within the Economic flag (follow-up, 2026-11-04T22:30–23:30Z)

Method: JLC's search API was paged through the keywords "accelerometer", "Accelerometers", "IMU", "attitude sensor",
the named barometer families and "barometric" / "Pressure Sensors" (about 200 accelerometer / IMU and 236 pressure
listings with stock ≥ 10). Each candidate's "PCBA Type" was then read on its JLC part page (Live). Ranges come from the
JLC listing text unless a datasheet is cited. Prices are JLC tier prices for 2 and 5 boards (the same tier for every
line here).

#### 3.5.1 High-g partner for a two-chip IMU (F2: ≥ ±64 g on the axial axis)

| Part | LCSC | JLC flag | Stock / pre-sale | Price | Range, interface | Package | Maker reflow |
|---|---|---|---|---|---|---|---|
| **NXP FXLS90322AESR2** | **C5190712** | **E** (MSL 3) | 1348 / 1348 | **$2.87** | listing: ±500 g, SPI / I²C, 12-bit, 3.135–5.25 V. Datasheet (FXLS9xxx0 Rev 6, LCSC copy of C5190712): one axis, lateral X / Y or vertical Z; high-g ranges ±50 … ±500 g; SPI or I²C on SS_B / SCLK; VCC_BUF min 3.135 V. | HLQFN-16 4 × 4 × 1.45 mm, **0.8 mm pitch** (Datasheet Table 1) | none in the datasheet text: UNVERIFIED |
| NXP FXLS93230AESR2 | C5190722 | E | 42 / 42 | $6.44 | X, H range, **PSI5 only** (Datasheet Table 2): no SPI / I²C | HLQFN-16 | – |
| ADI ADXL1005BCPZ | C662293 | E | 5 / 4 | $62.43 | ±100 g, X, analog | LFCSP-32 5 × 5 | – (too few, too dear) |
| ADI ADXL1001 | C662286 | not probed | 8 | $83.18 | ±100 g analog | LFCSP-32 | – |
| KX134-1211 | C2157908 | **S** | 10 212 | $10.67 | ±64 g | LGA-12 2 × 2 | – |
| ADXL375 / ADXL372 / ADXL373 | C481898 / C579465 / C3216384 | **S** | – | $19–22 | ±200 g | LGA | – |
| ADXL356 / 357 / 359 | C579461 / C662377 / C17664662 | S (359), others not probed | – | $31–113 | ±40 g max: fails F2 | LCC / LGA | – |
| ADXL382-2 | C41769491 | **S** | 20 | $53.61 | ±60 g: fails F2 | LGA-14 | – |
| LIS331HH | C2655073 | **S** | 9 | $13.53 | ±24 g only: fails F2 | LGA-16 | – |
| IIS2ICLX, IIS3DWB | C1857737, C51915717 | **S** | ≤ 7 | – | low-g / vibration | – | – |
| QMA6100P (QST) | C2887190 | **S** | 26 921 | $0.59 | ±32 g max (Inference from the family): fails F2 | LGA-12 | – |
| H3LIS100DL, MC3672, MMA6525 / 6555, AIS1120SX, AIS2120SX, ADXL377, ADXL001, KX132 | – | – | 0 at JLC | – | – | – | not orderable |

**FXLS90322AESR2 is the only in-stock, Economic-flagged, digital accelerometer above ±64 g found.** Its exact suffix
"90322" is not in the datasheet's ordering-options table (Table 2 lists FXLS90220 / 90230 / 90120 / 90130 / 90620 / 90630
for SPI / DSI3), so its axis, range and protocol come only from the JLC listing (±500 g, SPI / I²C): **Inference**
until NXP confirms. The part is an automotive airbag satellite sensor: SPI operation without the DSI3 / PSI5 bus, its
register set and the 3.135 V supply minimum against R12's 3V3 tolerance are **Inference** to check.

#### 3.5.2 Gyro / low-g part and other single-chip IMUs (F1: ±4000 dps)

| Part | LCSC | JLC flag | Stock | Price | Range (listing) | Package |
|---|---|---|---|---|---|---|
| **ST LSM6DSVETR** | **C41785564** | **E** (MSL 3) | 502 / 428 | **$6.19** | ±16 g, **±4000 dps**, SPI / I²C / I³C | **LGA-14L 2.5 × 3**, the same outline as U4 |
| TDK ICM-45686 | C22459454 | E | 2018 / 1900 | $10.24 | ±32 g, ±4000 dps (Datasheet DS-000577) | LGA-14 2.5 × 3 |
| TDK ICM-42688-P | C1850418 | E | 1253 / 658 | $20.04 | ±16 g, ±2000 dps: fails F1 | LGA-14 |
| ICM-42688-P (Tokmas clone) | C54308212 | E | 2327 | $2.94 | ±2000 dps (Inference): fails F1 | LGA-14 |
| TDK ICM-45605 | C38673635 | E | 36 | $42.52 | ±16 g, ±2000 dps: fails F1 | LGA-14 |
| BMI323, ICM-42670-P / -L, IAM-20680HT, IIM-42653, LSM6DSR, LSM6DSV16BX, ICM-42688P-HXY | C5368700, C3288646 / C49073546, C3288649, C30724128, C784817, C5267394, C46550687 | **S** | – | – | ≤ ±16 / 32 g | – |

**No single-chip IMU reaching ±64 g is Economic-flagged.** Every in-stock single-chip part stops at ±16 g or ±32 g;
the ±64 g+ ones (ISM6HG256X, LSM6DSV320X, LSM6DSV80X) are Standard Only. IAM-20685 had no JLC stock.

LSM6DSVE is the notable find: an **ST** LGA-14L part that is Economic-flagged (so the flag is not "all ST LGA"). Its
range comes from the JLC listing; the datasheet was not obtainable (LCSC copy empty, st.com refused). That its pin map
matches ISM6HG256X's on the existing U4 land (both LSM6DSV-family LGA-14L) is an **Inference**: compare DS15034 with the
LSM6DSVE datasheet before relying on it. The firmware register set is close to the LSM6DSV family's (**Inference**).

#### 3.5.3 Barometers (F3: ≤ 300 hPa, better ≤ 260 hPa)

| Part | LCSC | JLC flag | Stock | Price | Range | Package | Maker reflow |
|---|---|---|---|---|---|---|---|
| **Infineon KP215F1701** | **C538491** | **E** (MSL 3) | 2122 / 1817 | **$1.79** | listing: **10–115 kPa**, 4.5–5.5 V, 1.4 kPa accuracy | DSOF-8 | no datasheet at JLC: UNVERIFIED |
| Infineon KP212K1409 | C3232021 | E (MSL 1) | 15 / 14 | $5.11 | **15–115 kPa**, ratiometric analog 0.5–4.5 V, ±1.0 kPa (Datasheet Rev 1.0) | PG-DSOF-8-16 | "suitable for Pb-free soldering according to IPC/JEDEC J-STD-020" (Datasheet; the 260 °C class is an Inference) |
| NXP MPXHZ6115A6T1 | C3235759 | E | 2615 / 2600 | $8.40 | 15–115 kPa analog, 4.75–5.25 V (listing; the LCSC sheet is the MP3H6115A, a 3 V sibling) | SOIC-8 300 mil | none found |
| Alps HSPPAD132A | C351181 | E | 43 | $12.07 | 30–110 kPa, I²C, −10…+60 °C (listing) | – | none found |
| TE MS5637-02BA03, MS5837-02BA01 | C3033010, C5785272 | E | ~1000 | $3.04, $4.70 | 30–120 kPa | 3 × 3 mm | **250 °C, 40 s** (Datasheet): FAIL |
| TE MS5611 / MS5607, HopeRF HP203B | C15639 / C97627, C138665 | E | – | – | 10–120 / 30–120 kPa | – | **250 °C**: FAIL (§3.2) |
| WF183DE 15BA | C51484413 | E | 1797 | $0.78 | 0–1.5 MPa (15 bar), 0.5 kPa resolution (listing) | LGA-8 3.6 × 3.8 | none: too coarse for F3 (Inference) |
| BMP388 / DPS368 Tokmas clones | C54582187 / C55090144 | E | 8196 / 10 191 | $1.58 / $2.16 | 30 kPa floor (Inference from the originals) | LGA-10 / LGA-8 | no datasheet |
| LPS27HHW, LPS33W, LPS22HH, LPS25HB | C3010792, C3210737, C2827824, C87898 | **S** | – | – | 26 kPa | – | – |
| BMP585, BMP581, BMP388, BME680, ICP-10111, ICP-20100, CPS121, CPS122, CPS171, WF282A, WF5803F (01BA / 02BA / 10BA), SPL07-003, DPS368 | various | **S** | – | – | 1–30 kPa floors | – | – |
| SPL06-001, SPL06-007, QMP6988, HSPPAD143A, BMP280, BMP390, LPS22HB / LPS22DF (and clones) | – | – | 0 or < 10 at JLC | – | – | – | not orderable |

**No Economic-flagged digital barometer reaching ≤ 300 hPa has a verified ≥ 260 °C rating.** The Economic-flagged
ones that reach the range are **analog** automotive MAP sensors (Infineon KP215F1701 / KP212K1409, NXP MPXHZ6115A),
which need a 5 V supply, a divider to a 3.3 V STM32 ADC pin and an ADC-based driver, plus the TE / HopeRF parts that
fail on their 250 °C rating, and the undocumented Tokmas clones.

#### 3.5.4 JLC's rules for "Standard Only"

- JLC's help page "Common BOM and CPL matching issues" (Live, jlcpcb.com/help/article/common-bom-and-cpl-matching-issues-and-explanations):
  "You selected Economic PCBA as the order type, but the order contains components that are exclusive to Standard
  PCBA orders." Fixes it offers: switch to Standard, **select "Do not place this part"**, or contact support. The same
  page: "Orders containing special-handling components will be subject to manual review after submission." It gives
  no criterion for the flag.
- No JLC page found states a cause (MSL, bake need, price or value). The data argue against MSL as the cause: Standard
  Only parts include MSL 1 parts (BMP388, BMP581, CPS122, ICP-10111, LSM6DSV16X), while Economic parts include MSL 3
  parts (STM32H743 TFBGA, LSM6DSVE, FXLS90322). That the flag is set per listing, not per package or MSL, is an
  **Inference** (genuine Bosch / Infineon listings are S, Tokmas clones of the same packages are E).
- JLC's PCBA FAQ (Live, jlcpcb.com/help/article/pcb-assembly-faqs, FAQ 7): Preferred Extended parts "are exempt from
  the Feeders Loading fee for Economic PCB assembly". This confirms the waiver that O-R12-12 and §4 treated as an
  Inference, so §4's "if waived" rows apply.
- **"Bake Components" and consignment:** JLC's consignment terms mention baking moisture-sensitive parts (about 48 h
  after arrival), a per-piece consignment fee and manual handling (search summary of
  jlcpcb.com/help/article/consignment-part-terms-conditions, not read on the page itself: **Inference**). No JLC page
  says that baking or consigning lifts a Standard Only flag. Because the flag does not track MSL, baking is unlikely to
  change it (**Inference**). Whether a consigned ISM6HG256X or LPS28DFW can be placed on an Economic order is
  **unknown**: ask JLC support before relying on it.

#### 3.5.5 Ranked recommendation (keeps F1–F3)

Costs are JLC parts plus feeder against the current U4 ($14.34) or U5 ($6.70) line, at 2 and 5 boards. The Extended
feeder is $3.07 per code per order.

**U4**

| Rank | Option | Cost change | Land / placement | Remaining Inference |
|---|---|---|---|---|
| 1 | **LSM6DSVETR (C41785564) on the existing U4 land for F1 and the low-g channel, plus FXLS90322AESR2 (C5190712) as the axial high-g channel.** Both are Economic. Mount the FXLS so its sensing axis lies along the rocket axis. | Parts $9.06 against $14.34 (−$5.27 per board), plus one more Extended code (+$3.07 per order): **−$3.74 per board at 2, −$4.66 per board at 5** | U4 land kept if the pin maps match. **New** HLQFN-16 4 × 4 land and placement for the FXLS, with its decoupling, on U4's SPI bus with one more chip-select GPIO and 3V3: this changes routing | LSM6DSVE range and pin map (listing only); FXLS90322's axis, range and SPI mode (suffix not in NXP's table); both makers' reflow ratings; FXLS VCC min 3.135 V against the 3V3 tolerance; a free GPIO for the second chip select |
| 2 | ICM-45686 (C22459454) plus FXLS90322AESR2 | $13.11 (−$1.23 per board) + $3.07 per order: +$0.31 per board at 2, −$0.61 per board at 5 | **Two** new lands (TDK pin map differs from ST's), new axis map and driver | as rank 1, plus ICM-45686's pin map against R12's nets |
| 3 | Keep ISM6HG256X (or LSM6DSV320X) and mark U4 "Do not place" (a JLC-offered fix); hot-air fit after delivery | −$14.34 per board and −$3.07 per order on JLC; the part is bought elsewhere (no franchised stock on 2026-11-01) | none | hand-fit yield of a 0.5 mm LGA; parts availability |

**U5**

| Rank | Option | Cost change | Land / placement | Remaining Inference |
|---|---|---|---|---|
| 1 | **Keep LPS28DFW, mark U5 "Do not place", hot-air fit after delivery** (CCLGA-7, pads ≥ 1.125 mm apart, the easiest LGA on the board) | −$6.70 per board on JLC, −$3.07 per order; bought elsewhere | none | hand-fit result; parts availability outside JLC |
| 2 | **Infineon KP215F1701 (C538491)** analog: 10–115 kPa keeps the 260 hPa / 10 km line | $1.79: **−$4.91 per board** (same Extended count) | **New** DSOF-8 land and placement, a 5 V-class supply (PORT_4V8, nominal 4.79 V, is inside 4.5–5.5 V but is off on USB-only power), a divider from its 0.5–4.5 V output to a free STM32 ADC pin, an ADC driver | range and interface (listing only; no datasheet obtained); reflow rating; 1.4 kPa accuracy is coarse in absolute terms, while apogee detection uses relative change (Inference) |
| 3 | Infineon KP212K1409 (C3232021): datasheet-backed, 15–115 kPa, ±1.0 kPa, J-STD-020 Pb-free | $5.11: −$1.59 per board | as rank 2 | only 15 in stock; 260 °C class Inference |
| 4 | Tokmas BMP388 clone (C54582187), digital I²C / SPI | $1.58: −$5.11 per board | new LGA-10 2 × 2 land | 300 hPa floor (F3 met with zero margin; the 10 km line is lost); no datasheet, so range, accuracy and reflow are all Inference |

## 4. Cost change (parts + feeder, per order; joint fees unchanged)

| Change | 2 boards | 5 boards |
|---|---|---|
| D5/D6/D9 → B340A-E3/61T (+$0.0606 × 3 per board, +$3.07 feeder) | +$3.43 | +$3.98 |
| D121 → ProTek (+$0.0718 per board; Semtech's $3.07 feeder dropped if Preferred is waived, Inference) | −$2.93 | −$2.71 |
| **Recommended drop-ins, net** | **+$0.50 ($0.25 per board)** | **+$1.27 ($0.25 per board)** |
| same, if JLC charges the Preferred feeder | +$3.57 ($1.79 per board) | +$4.34 ($0.87 per board) |
| U4 off the JLC order (option 3.1-1) | −$31.74 | −$74.76 (owner buys ISM6HG256X elsewhere) |
| U5 off the JLC order (option 3.2-1) | −$16.47 | −$36.56 (owner buys LPS28DFW elsewhere) |
| U5 → Tokmas BMP388 (option 3.2-2) | −$10.23 | −$25.57 |
| U4 → ICM-45686 (option 3.1-2, breaks F2) | −$8.19 | −$20.48 |

## 5. What would touch the routing

- **No change** for: B340A (D5/D6/D9), ProTek SRV05-4 (D121), and taking U4 / U5 off the JLC order (lands kept).
- **New land and placement**: U5 → BMP388 / DPS368 clone; U4 → ICM-45686 (also the axis map and the pin map); J430 →
  any other microSD socket.
- **Rotation or land swap**: LED1 → KT-0805R (pin-1 polarity of the R12 lands differs).

## 6. Method and limits

- PCBA Type, assembly type, MSL, stock and price were read from each JLC part page (`jlcpcb.com/partdetail/…`, field
  "PCBA Type") and JLC's component-detail API (`cart.jlcpcb.com/shoppingCart/smtGood/getComponentDetail`), Live
  2026-11-04T22Z. Stock moves daily.
- Datasheets were the LCSC copies JLC links; several are image-only drawings, so "none found" means none in the
  extractable text. ST, Molex, Nexperia and AOS web pages refused or timed out from this session.
- No JLC cart or Economic quote was run: whether JLC's cart actually refuses U4 / U5 on Economic, or offers to drop
  them, is an **Inference** from the "Standard Only" flag.
