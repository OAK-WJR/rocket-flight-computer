# R12 validation: deviations for owner acceptance

**Where R12 stands.** M3-ASSY-R12 is a CAD candidate on branch `m3-assy-r12` (AVA re-layout, D-R12-93 … -99),
PCB `be81f40be9d5b5ea60b3f1484324dab4dc999446dd75f493dd41e7f6982ddae8` (hash as of `871f77a`; 46 × 90 × 1.6 mm, four
layers, every part on the top face for JLC Economic PCBA). It is not accepted and nothing is ordered; R9 stays the accepted board and R8 its
fallback. Stage F round 1 found verified real errors; its fix passes are recorded in STATUS.md. The AVA re-layout
that followed was reviewed in round 2: 16 real errors (1 Major / 15 Minor), all fixed by D-R12-100 … -106;
the board is unchanged and round 2 is not clean.
The full state is stated once, in
[M3_R12.md, "Current state"](M3_R12.md#current-state). This file lists what the owner must accept or do for R12.
Decision IDs are in [`m3_design/r12/design/R12_DECISIONS.md`](../m3_design/r12/design/R12_DECISIONS.md); evidence labels
as AGENTS §2.5.

**How to answer.** Write your answer and the date in the "Owner answer / date" column, or in a dated note here that
names the row. Row A-9 is accepted (owner, 2026-11-04), as is acceptance row 3 (owner, 2026-11-03, D-R12-31).
Answer the "Blocks order" rows before ordering.

## R12 owner decision table

### Requirement text R12 departs from (R12_DECISIONS §3)

| # | Requirement today | R12 | Decision | Blocks order? | Owner answer / date |
|---|---|---|---|---|---|
| A-1 | M1: Standard PCBA, 1 oz inner copper | Economic PCBA, one side, 0.5 oz inner | D-R12-01, -03 | Yes | Open |
| A-2 | F9 / F11: U10 USB limiter and U11 source selection | Diode-OR D5 / D6. Gone: the USB current limit toward the host, USB OVLO, the USB ESD clamp (STM32 pin ESD only, Inference) and the USB_FAULT_N / LOGIC_SOURCE_ST flags. USB-only power needs ≥ 4.45 V at J3 (O-R12-03) | D-R12-04 | Yes | Open |
| A-3 | F10: each port line 1 kΩ plus a ground-only ESD clamp | 1 kΩ only (D402 kept on J400.2) | D-R12-18 | Yes | Open |
| A-4 | F3 names the MS5611 | MS5607-02BA03 (10–1200 mbar; full accuracy from 300 mbar) | D-R12-52 | Yes | Open |
| A-5 | F10 / R10: camera via the U402 limiter and U12 / U13 isolation | U403 buck EN is the camera switch; 1 kΩ series; no CAM_FAULT_N. A 3–5 A partial short could reach U9's limit (Inference) | D-R12-08 | Yes | Open |
| A-6 | F10 / P2: JST GH latching ports (R11) | SH 1.0 mm clones with friction-only retention (D-R12-31; the owner chose SH on 2026-11-03), mating with JST housings an Inference (O-R12-04) | D-R12-15, -31 | Yes | Open |
| A-7 | F11: LS120 MLT-5020 | QMB-09B-03 THT, JLC THT assembly (D-R12-85: nothing owner-fitted); pin 1 = (+): JLC's footprint prints '+' at pad 1 and the CPL maps that pad onto ours (residual 0.0 mm, Measured); marked '+' / '-' on F.Fab (D-R12-82) | D-R12-16, -85 | Yes | Open |
| A-8 | PORT_4V8 within 4.5–5.0 V at every corner | Inside at every tolerance and drift corner since D-R12-83 (R401 0.1 % 25 ppm/K, R404 5.1k): 4.603–4.938 V initial, 4.571–4.972 V drift at the regulator; ≥ 4.563 V at the ports under the 0.561 A budget on the 90 mm board (Calculation / Inference: drift and load budget). The LR900-F's 4.5–5.0 V is the project record (maker page: "5V DC", no range; Inference); the GPS's 3.3–5 V is the maker's | D-R12-07, -21, -83 | Yes | Open |
| A-9 | Economic reflow 255 ± 5 °C against makers' 250 °C peaks (SS34 D5 / D6 / D9, MS5607 U5; J430 and SRV05-4 by Inference; since D-R12-85 also C84, rated 255 °C peak) | **Accepted by the owner, 2026-11-04**; the effect on each part is an Inference | D-R12-49 | — | Accepted 2026-11-04 |
| A-10 | F1 / F2 name one IMU (low-g, high-g and gyro) | LSM6DSVE (low-g, ±4000 dps) plus FXLS90322 (XY medium-g, ±150 g maximum) | D-R12-50, -51 | Yes | Open |

### Accept (a risk or limit you take on)

| # | You accept | What it means and the figures | Decision / evidence | Blocks order? | Owner answer / date |
|---|---|---|---|---|---|
| 1 | M2 routing deviations ([full list below](#m2-routing-deviations)) | Three critical-net allowlist entries (Measured at `871f77a`; route_check figures fixed in `ROUTE_FIGURES_R12`). **3V3A** 5 vias (72.31 mm against a 48.05 mm MST): the In2 link from the VDDA end (15.5, 60.6) to the R164 / U4 F.Cu island (19.65, 36.9) takes 2 vias. R164.2 supplies U4.5 (23.5, 40.64), C10, U4.8 and C31 on that island. One F→B via (23.5, 39.95) feeds C30 and U5 / C32 through 15.66 mm of B.Cu; each branch returns to F through its own via, (25.7, 42.75) and (25.8, 29.8), respectively. **SPI1_MISO** 3 vias (22.36 mm against 17.25 mm): ball A6 is west of SCK / MOSI but U4.1 is on U4's east face, so MISO crosses both on B and back, plus its U6 branch. **QSPI_CLK** detour 1.63 (19.4 against 11.87 mm): the only F entry to U3.6 is from the pad row's inner end, C19 leaves one 0.7 mm gap that IO3 uses, and B under the BGA carries the IO2 and VCAP lanes. D-R12-75A's SPI1_SCK and USB_DP entries are gone (USB_DP keeps one J3 bridge, vias (40.7, 47.2) / (40.3, 45.75) with GND partners at 1.41 / 1.33 mm, inside the rules) | D-R12-96 | Yes | Open |
| 2 | J122's harness note optional | `SERVO + FROM HARNESS` (18.9 mm of ink) has no legal spot within 6 mm of J122 on either face (Measured, stageD.md §2). check_r12 waives only its absence; every contact legend, word, SWD row and SHOWN_REFS designator is still required. The rule it states is in the handoff | D-R12-81 | Yes | Open |
| 3 | SH friction retention | No latch: each SH plug needs an adhesive / RTV dab or a tie at every flight (handoff, per-flight step 0) | D-R12-31; O-R12-18 | No | Accepted 2026-11-03 |
| 4 | ~~U9 feed at 0.4 mm~~ | **Closed by D-R12-84** (U9 0.3 mm east, C88 on the bar line): the feed is 0.8 mm (24.9 °C at 2.9 A; IPC-2152 upper bound, Calculation / Inference) except U9.5's 1.3 mm, 0.4 mm pin entry; nothing to accept | D-R12-84; O-R12-25 | No | Closed (agent fix) |
| 5 | PA6 can trip during a fire into a shorted match | At four stalls with the match and its leads shorted, VLOGIC is 0.036 V into PA6's trip band at the nominal divider ratio and 0.127 V into it with the 1 % divider (match alone shorted: 0.083 V into it with tolerance; Calculation / Inference, 90 mm board: D5 now hangs off the RAW trunk). Firmware must not treat it as a battery loss | stageD_analysis.md §5; O-R12-07, -17 | No | Open |
| 6 | ~~PORT_4V8 at the ports under load~~ | **Closed by D-R12-83**: at the 0.561 A budget the port pins are ≥ 4.596 V initial and ≥ 4.563 V at the drift corner on the 90 mm board (J420 lowest; 4.561 / 4.529 V on the 100 mm board), ≤ 4.972 V at no load (Calculation / Inference). Cost: one Extended code, +$3.07 per order. What stays: bench-read the LR900-F's real floor (row 15) | D-R12-83; O-R12-16, -26 | No | Closed (agent fix) |
| 7 | Q120 / Q121 VGS above 12 V only on a pack above about 14.4 V with the bus on | Maximum-ratio corner: 12 / (51 / 60.8) + 0.1 = 14.41 V, assuming a 0.1 V Q122 drop (Calculation / Inference). A 3S pack is cut off by OVLO; only a transient toward the 19.9 V clamp would exceed ±12 V (Inference) | D-R12-10; O-R12-10 | No | Open |
| 8 | Library silkscreen near openings | Footprint graphics within JLC's 0.15 mm pad-to-silkscreen gap: D120's circle 0.10 mm from R130.1, U403 / U400 pin-1 circles 0.092 mm from C433.2 / C400.2 (Measured on `be81f40b…` with r12_post's contract; U5's outline note is gone). JLC clips silkscreen at openings (Inference). The post stage prints these; it does not draw them | stageD.md §2 | No | Open |
| 9 | 76 hidden designators | 76 designators have no unambiguous spot and are kept on F.Fab (on `be81f40b…`; listed in stageE_relayout.md §3); they show on the assembly drawings, not on the board | D-R12-80, -99 | No | Open |
| 20 | PC1 (F2) keeps three inert ball neighbours | G3 is NC since D-R12-93 (PORT_SENSE moved to PD10). One solder bridge from F1 PYRO1_CONT, E2 CAM_5V_SENSE or E1 NRST to PC1 with PC1 high-Z gives Q122 at most 0.399 / 0.273 / 0.213 V (worst corner from the board's own resistors, Calculation / Inference: drift; PYRO1_CONT's figure assumes the 8.4 V pack with the bus already on) against the AO3400A's 0.65 V minimum threshold at 250 µA (Datasheet); check_r12 K-neighbours fails any above 0.45 V (the 0.20 V allowance for heat and sub-250 µA conduction is an Inference). The round-1 divider (4.7k / 10k) gave 1.00–1.12 V (Calculation / Inference: drift) and is replaced by 47k / 100k | D-R12-86, -93; R12F1-TRI-01 | No | Open |
| 22 | The 3V3A In2 island is dropped | 3V3A (VDDA and the sensor supplies) has no In2 island: the In2 link from the VDDA end (15.5, 60.6) to the R164 / U4 F.Cu island (19.65, 36.9) takes 2 vias. R164.2 supplies U4.5 (23.5, 40.64), C10, U4.8 and C31 on that island. One F→B via (23.5, 39.95) feeds C30 and U5 / C32 through 15.66 mm of B.Cu; each branch returns to F through its own via, (25.7, 42.75) and (25.8, 29.8), respectively (Measured; row 1); the AVA re-layout needed that In2 area for the CA corridor (supervisor decision). Noise effect on the ADC and sensors is an Inference (bench) | D-R12-95 | No | Open |
| 23 | C24 (NRST filter) at J2's end of the NRST run | C24 sits at (26.6, 45.18) beside J2, 19.54 mm of NRST copper from ball E1, including 15.68 mm on In2 (Measured, barrels excluded), because NRST's In2 lane could not reach the west pocket under the frozen PYRO1_CONT / ACT_EN_MCU runs (K-reference). That this is acceptable for a bench-only reset with the MCU's internal pull-up is an Inference; NRST is also the worst routed / MST ratio, 1.96 (Measured at `871f77a`; O-R12-30) | D-R12-98 | No | Open |
| 24 | Outline 46 × 90 mm | The owner's "Try 90 mm" (D-R12-99) replaces D-R12-24's 100 mm. Under the 120 mm rule (P1) and fit_check's 100 mm ceiling; the bay / sled length is not in `docs/VEHICLE.md`, so the vehicle fit is unchecked (O-R12-28). Fallback: the 100 mm re-layout on `r12-relayout-int` `4686580`, board `ef3194c0…` | D-R12-99 | Yes | Open |
| 25 | PE4 keeps the D-R11-23 3V3-neighbour exception | B2 / D2 are diagonal 3V3 neighbours of PE4 / C3: 0.731 mm ball-to-ball. On `be81f40b…`, PE4's 0.1 mm PYRO1_GATE_N lane (20.6, 51.6) → (18.9, 51.6) is 0.150 mm from U1.B2's 3V3 land and 0.300 mm from its track (Measured by round-2 triage). A bridge drives Q124's gate and may fire an enabled match (Inference). This retained exception needs owner acceptance; row 17's X-ray action also stays | D-R11-23; D-R12-104; R12F2-TRI-12 | Yes | Open |

### Do (an order, process or bench action)

| # | You do | What it means | Decision / evidence | Blocks order? | Owner answer / date |
|---|---|---|---|---|---|
| 10 | Re-read AN2606 | DS12110 Rev 8's Tables 9–12 were re-read for every re-pinned ball and AF number (D-R12-93; Datasheet), so that half is done. Still open: AN2606's H74x loader pins for the moved functions (PA8–PA10, PA15, PB6 / PB7, PC9–PC12, PD2, PB10, PE12–PE14, PA7); st.com refused the download, so the roles are R11's AN2606 Rev 64 Table 119 reading (Inference) | D-R12-61A … -64A, -93; O-R12-23 | Yes | Open |
| 11 | Read the missing datasheets | FXLS90322 dual-channel (FXLS9xxxx Rev 7): pin-out, axis frame, medium-g range codes. LSM6DSVE: no datasheet found at ST | D-R12-50, -51; O-R12-21 | Yes | Open |
| 12 | Bench-check the axis signs | U4: roll = −gyro_Y, thrust −a_Y. U6 channel 1: +a forward. Both are a Calculation / Inference from figures and need a 1 g and rotation check before flight | D-R12-54; O-R12-15 | No (before flight) | Open |
| 13 | Check SH mating and the H743 lead | Mate a sample clone header with JST SH housings and confirm the latch / friction (O-R12-04). Check the pin orders against a real MicoAir H743 lead: the pin-1 end is unmarked in the source image, and the owner's board may be the v1 (O-R12-19) | D-R12-15, -31 | Yes | Open |
| 14 | Confirm the THT parts on Economic and J1's hole fit | J121 (DB125) and LS120 (QMB-09B-03), both JLC THT assembly, on the Economic order page; J1's 1.40 mm holes with a sample 5.0 mm terminal or the chosen lead | D-R12-29, -30, -85; O-R12-20 | Yes | Open |
| 15 | Bench items | LMR50410 with 4.7 µH: load step and stability (O-R12-06). HSE crystal at gm_crit 1.43 / 1.5 mA/V: cold start-up and drive level (O-R12-09). PORT_4V8 over temperature and the LR900-F's real supply floor (O-R12-05, D-R12-83) | R12_DECISIONS §4 | No | Open |
| 16 | Get JLC's DFM acceptance | Not queried: 0.10 mm track and clearance, the TFBGA escape with 0.3 / 0.45 mm vias at interstitial sites (0.2 mm via hole to copper, D-R12-23), the six recorded short-edge courtyards, and the reflow class of unread parts (O-R12-02) | D-R12-03, -23, -24 | Yes | Open |
| 17 | U1 X-ray at first article | As R11: a TFBGA bridge cannot be seen; X-ray U1 with attention to the balls around C3 (PE4) and F2 (PC1). PE4 spacing acceptance is row 25; X-ray fees are included in row 18's minimum totals | R11 row 17 | Yes | Open |
| 18 | Re-run cost and stock on order day | Live 2026-11-06T10:06–10:08Z on `be81f40b…`: no shortfalls at 2 or 5 boards; M3 metric $66.55 / $46.29 per board; minimum all-in $176.75 / $282.99 including U1-only X-ray ($3.28 / $8.20; Calculation / Inference: 100 mm PCB quote used for 90 mm), $6.75 over the $170 target at 2 boards. Counting U1 / U4 / U5 / U6 / U9 gives $189.87 / $295.29–303.49, above both $170 / $295 targets (Calculation / Inference: qualifying count and fee tier; bare PCB is the 100 mm quote used for 90 mm). Confirm the count and tier, including possible D402 / Y1 fees, on JLC's quote (D-R12-105). JLC may or may not waive the BAT54C Preferred Extended feeder fee (O-R12-12). Re-run `FAB_NET=1 m3_design/r12_fab.sh` | stageD.md §7 | Yes | Open |
| 19 | Accept the list and the agent decisions | Accept or reject the rows above and D-R12-01 … D-R12-106 | R12_DECISIONS.md | Yes | Open |
| 21 | JLC review of U5 and Y1 | JLC's Economic order page marks U5 (MS5607-02BA03, C97627) and Y1 (X322525MOB4SI, C9006): "The processing of this component is difficult. After placing an order, it will be reviewed. If PCBA advanced option is required, additional fees will be charged." Both carry JLC's `needAuditFlag` with no listed special fee (Measured 2026-11-06T00:58Z); every brand-name barometer on JLC is flagged, so U5 stays; Y1 stays on Basic because the review happens for U5 anyway. On order day accept JLC's review result by email; if it adds a fee for Y1 larger than an Extended feeder fee, swap Y1 to YXC C5444544 (same YSX321SL sheet, land, pinout and 12 pF load) | D-R12-92 | Yes | Open |

### R10 / R11 rows that carry to R12

R12 keeps the R10 safety networks and the single-switch scope, so these apply as written (copper-dependent figures were
re-run in `stageD_analysis.md`):

- One switch, no fuse, servo return through J122's shared GND, always-on ports. These are R10 rows 1–4.
- The 20 ms fire and the 36 ms watchdog guard (34.853 ms, Calculation on allocations / Inference).
- Switch-bounce immunity: R10 row 21's rule; the R12 worst-corner limit is 7.56 ms (Calculation / Inference).
- Pack selection, microSD and pad-check policy (R10 rows 13, 17, 18).
- Thermal qualification and the buzzer's +70 °C rating (R10 rows 33, 36; QMB-09B-03 shares the +70 °C limit).
- **Hold-up changes on R12.** C84 holds VLOGIC only (2.23–6.12 ms from a break, Calculation / Inference); the required
  hold-up time is still the open owner question (R10 rows 5, 25).

## M2 routing deviations

Measured on PCB `be81f40be9d5b5ea60b3f1484324dab4dc999446dd75f493dd41e7f6982ddae8` (`871f77a`) with
`route_check --profile r12`. Routing metrics are the final board's, after the signal-only AVA cleanup. All remain deviations pending owner acceptance (row 1). Coordinates are board
millimetres; `net` locations are the report's net anchors.

**Critical allowlist (3, D-R12-96).** 3V3A, SPI1_MISO and QSPI_CLK; reasons and measured lengths are in row 1.

**Noncritical leftovers (11).** Counted for review under M2 / audit 2 item 7, with no per-instance measured exception
required; retained cleanup items, not owner-accepted routing. NRST's detour (ratio 1.96) is D-R12-98's C24 move (row 23).

| Category | Net | Layer / report anchor |
|---|---|---|
| `neck_down` | I2C1_SDA | F.Cu (19.15, 42.05) |
| `tiny_jog` | SERVO2_MCU | B.Cu (28.6, 17.5) |
| `tiny_jog` | CC1 | F.Cu (38.25, 46.75) |
| `tiny_jog` | LED_YEL | F.Cu (13.5, 55.2) |
| `extra_vias` | BAT_FAULT_N | net (20.6, 11.97) |
| `extra_vias` | CAM_5V_SENSE | net (13.2, 57.82) |
| `detour` | NRST | net (26.6, 45.6) |
| `extra_vias` | SERVO2_MCU | net (28.95, 11.35) |
| `extra_vias` | SERVO3_MCU | net (28.95, 9.05) |
| `extra_vias` | SERVO4_MCU | net (27.05, 9.05) |
| `extra_vias` | VLOGIC_SENSE | net (12.2, 57.82) |

**Review-only residuals (44, AUD-10 / `R10_REVIEW`).** 31 collinear nodes (exact straight splits; 21 of them sit on the
zone joins at y 17.5 and y 45.4, where `zones/merge.py` joins two fragments) and 13 segments wholly inside their own
pad (GND Y1.4, GND U6.17, GND R5.2, GND C31.2, GND U6.17, VBUS J3.B4A9, 3V3 R11.2, 3V3A R164.2, SPI1_MOSI U4.14, VLOGIC TP83.1, I2C1_SDA R13.1, BAT_ILIM R84.1, BST U2.1). No duplicate segments. Retained for review, not gated; connectivity, partial overlaps, crossings and DRC
remain gated.

**Information-only categories.** `route_check.py` `INFO` counts: `pad_end_offcentre` 292, `power_via_no_gnd` 12,
`passes_through_pad` 11, `short_layer_hop` 10, `width_change_junction` 6, `u_turn` 6, `extra_bends` 3. The count alone
does not establish a removable defect; they remain M2 review information, not acceptance.
