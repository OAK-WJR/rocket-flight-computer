# R12 validation: deviations for owner acceptance

**Where R12 stands.** M3-ASSY-R12 is a CAD candidate on branch `m3-assy-r12` (AVA re-layout, D-R12-93 … -99),
PCB `6e874d4e96ba3c6ab5d2a4163769c80aea6ba87002a4dd5c38eb85e7d93ca067` (round 5's fix pass, D-R12-125 … -133; 46 × 90 × 1.6 mm, four
layers, every part on the top face for JLC Economic PCBA). It is not accepted and nothing is ordered; R9 stays the accepted board and R8 its
fallback. Stage F round 1 found verified real errors; its fix passes are recorded in STATUS.md. The AVA re-layout
that followed was reviewed in round 2: 16 real errors (1 Major / 15 Minor), all fixed by D-R12-100 … -106;
that board was unchanged. Round 3 found 14 real errors (2 Major / 12 Minor), all fixed by D-R12-107 … -112;
only C25 / C26 changed on the board (18 → 15 pF). Round 4 found 8 real errors (0 Major / 8 Minor), all fixed by
D-R12-113 … -120; only R166's footprint description changed on the board (`66323cf0…` → `db1f0999…`). The AVA polish
pass (D-R12-121 … -124) then changed signal copper only (`db1f0999…` → `68e6b650…`). Round 5 reviewed `68e6b650…` and
found 22 real errors (1 Critical / 21 Minor), all fixed by D-R12-125 … -133: the Critical one was R12's fire-net copper
breaking the carried R10 limits (rows 1–2). The fire-net copper, U6's corner lands, GPS_TX's pad exit and the J121 pours
changed, and check_r12 S-10 now gates the fire-net gaps, default-deny (`68e6b650…` → `6e874d4e…`). No review round has
seen `6e874d4e…`. No round is clean yet.
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
| A-8 | PORT_4V8 within 4.5–5.0 V at every corner | Inside at every tolerance and drift corner since D-R12-83 (R401 0.1 % 25 ppm/K, R404 5.1k) **while U400 VIN ≥ VO / 0.75: 6.14–6.58 V initial, 6.09–6.63 V drift** (TI SLVSD90B §7.3, 75 % maximum recommended duty; D-R12-131). Below that, at four stalls (U400 VIN about 5.55 V) or on a 6.0 V pack (about 5.49 V), the window rests on an estimate: at 580 kHz the minimum off-time caps the output at 4.51–4.80 V, with the frequency foldback below 7 V at 5.16–5.26 V, above the 4.972 V top (Calculation / Inference; bench item, row 15). With that condition: 4.603–4.938 V initial, 4.571–4.972 V drift at the regulator; ≥ 4.563 V at the ports under the 0.561 A budget on the 90 mm board (Calculation / Inference: drift and load budget). The LR900-F's 4.5–5.0 V is the project record (maker page: "5V DC", no range; Inference); the GPS's 3.3–5 V is the maker's | D-R12-07, -21, -83 | Yes | Open |
| A-9 | Economic reflow 255 ± 5 °C against makers' 250 °C peaks (SS34 D5 / D6 / D9, MS5607 U5; J430 and SRV05-4 by Inference; since D-R12-85 also C84, rated 255 °C peak) | **Accepted by the owner, 2026-11-04**; the effect on each part is an Inference | D-R12-49 | — | Accepted 2026-11-04 |
| A-10 | F1 / F2 name one IMU (low-g, high-g and gyro) | LSM6DSVE (low-g, ±4000 dps) plus FXLS90322 (XY medium-g, ±150 g maximum; search summaries, Inference until FXLS9xxxx Rev 7 is read; O-R12-21) | D-R12-50, -51 | Yes | Open |
| A-11 | P2: five M3 supports at (4,4), (42,4), (4,44.3), (3.7,86), (42,86), no sixth; insulated hardware at all five | Four M3 supports at (3.0, 5.9), (43.0, 5.9), (3.5, 84.1), (42.5, 84.1), nylon hardware at all four; fit_check r12 OK (CAD envelopes only) | D-R12-24, -99, -133 | Yes | Open |
| A-12 | F9: J1 and J400 are separately labelled 2-pos DB125 terminals | J1 is two plated wire pads (`1:BAT+` / `2:GND`) for a soldered 16–20 AWG lead or a later 5.0 mm terminal (hole fit row 14); J400 is an SH-4 (A-6) | D-R12-30, -31, -133 | Yes | Open |
| A-13 | F8: "Ordinary 0.15 mm board clearance applies" to the pyro channel | The board floor is 0.10 mm. The fire nets meet S-10's limits apart from its recorded exceptions, two of them at 0.150 mm (PE4's lane to U1.B2 and to U1.C1). Other pyro / arming nets keep 0.10–0.15 mm gaps, e.g. ACT_FET_S–Q120.1 0.121 mm, RAW_ACT–R132.2 0.137 mm, CONT_MID–R173.1 / R129.2 0.131 mm, ARM1_SENSE, ACT_EN_MCU, PYRO1_CONT and BAT_SW_RETURN to the B GND pour 0.1005 mm (Measured on `6e874d4e…`) | D-R12-03, -126, -133 | Yes | Open |

### Accept (a risk or limit you take on)

| # | You accept | What it means and the figures | Decision / evidence | Blocks order? | Owner answer / date |
|---|---|---|---|---|---|
| 1 | M2 routing deviations ([full list below](#m2-routing-deviations)) | Three critical-net allowlist entries (Measured at `871f77a`; route_check figures fixed in `ROUTE_FIGURES_R12`). **3V3A** 5 vias (72.31 mm against a 48.05 mm MST): the In2 link from the VDDA end (15.5, 60.6) to the R164 / U4 F.Cu island (19.65, 36.9) takes 2 vias. R164.2 supplies U4.5 (23.5, 40.64), C10, U4.8 and C31 on that island. One F→B via (23.5, 39.95) feeds C30 and U5 / C32 through 15.66 mm of B.Cu; each branch returns to F through its own via, (25.7, 42.75) and (25.8, 29.8), respectively. **SPI1_MISO** 3 vias (22.36 mm against 17.25 mm): ball A6 is west of SCK / MOSI but U4.1 is on U4's east face, so MISO crosses both on B and back, plus its U6 branch. **QSPI_CLK** detour 1.63 (19.4 against 11.87 mm): the only F entry to U3.6 is from the pad row's inner end, C19 leaves one 0.7 mm gap that IO3 uses, and B under the BGA carries the IO2 and VCAP lanes. D-R12-75A's SPI1_SCK and USB_DP entries are gone (USB_DP keeps one J3 bridge, vias (40.7, 47.2) / (40.3, 45.75) with GND partners at 1.41 / 1.33 mm, inside the rules) | D-R12-96 | Yes | Open |
| 2 | J122's harness note optional | `SERVO + FROM HARNESS` (18.9 mm of ink) has no legal spot within 6 mm of J122 on either face (Measured, stageD.md §2). check_r12 waives only its absence; every contact legend, word, SWD row and SHOWN_REFS designator is still required. The rule it states is in the handoff | D-R12-81 | Yes | Open |
| 3 | SH friction retention | No latch: each SH plug needs an adhesive / RTV dab or a tie at every flight (handoff, per-flight step 0) | D-R12-31; O-R12-18 | No | Accepted 2026-11-03 |
| 4 | ~~U9 feed at 0.4 mm~~ | **Closed by D-R12-84** (U9 0.3 mm east, C88 on the bar line): the feed is 0.8 mm (24.9 °C at 2.9 A; IPC-2152 upper bound, Calculation / Inference) except U9.5's 1.3 mm, 0.4 mm pin entry; nothing to accept | D-R12-84; O-R12-25 | No | Closed (agent fix) |
| 5 | PA6 can trip during a fire into a shorted match | At four stalls with the match and its leads shorted, VLOGIC's lower-bound margin to PA6's trip top is −0.019 / −0.110 V at nominal / 1 % divider ratio (match alone shorted: +0.025 / −0.066 V; healthy: +0.174 / +0.083 V; Calculation / Inference: per-branch RAW drop, pack and load model, D-R12-108). Firmware must not treat it as a battery loss | stageD_analysis.md §5; O-R12-07, -17 | No | Open |
| 6 | ~~PORT_4V8 at the ports under load~~ | **Closed by D-R12-83**: at the 0.561 A budget the port pins are ≥ 4.596 V initial and ≥ 4.563 V at the drift corner on the 90 mm board (J420 lowest; 4.561 / 4.529 V on the 100 mm board), ≤ 4.972 V at no load (Calculation / Inference). Cost: one Extended code, +$3.07 per order. What stays: bench-read the LR900-F's real floor (row 15) | D-R12-83; O-R12-16, -26 | No | Closed (agent fix) |
| 7 | Q120 / Q121 VGS above 12 V only on a pack above about 14.4 V with the bus on | Maximum-ratio corner: 12 / (51 / 60.8) + 0.1 = 14.41 V, assuming a 0.1 V Q122 drop (Calculation / Inference). A 3S pack is cut off by OVLO; only a transient toward the 19.9 V clamp would exceed ±12 V (Inference). The bus is on from the on-rail check until switch-off, so the case covers the pad dwell as well as flight (D-R12-115) | D-R12-10, -115; O-R12-10 | No | Open |
| 8 | Library silkscreen near openings | Footprint graphics within JLC's 0.15 mm pad-to-silkscreen gap: U403 / U400 pin-1 circles 0.092 mm from C433.2 / C400.2 (Measured on `6e874d4e…` with r12_post's contract; D120's circle, 0.10 mm from R130.1 before, left that neighbourhood when D120 moved in round 5, D-R12-125; U5's outline note is gone). JLC clips silkscreen at openings (Inference). The post stage prints these; it does not draw them | stageD.md §2 | No | Open |
| 9 | 77 hidden designators | 77 designators have no unambiguous spot and are kept on F.Fab (Measured on `6e874d4e…`; round 5 re-drafted the pyro-cell legends: C126, C127 and C25 are now hidden, R127 and R33 shown, D-R12-125; listed in stageE_relayout.md §3); they show on the assembly drawings, not on the board | D-R12-80, -99 | No | Open |
| 20 | PC1 (F2) keeps three inert ball neighbours | G3 is NC since D-R12-93 (PORT_SENSE moved to PD10). One solder bridge from F1 PYRO1_CONT, E2 CAM_5V_SENSE or E1 NRST to PC1 with PC1 high-Z gives Q122 at most 0.399 / 0.273 / 0.213 V (worst corner from the board's own resistors, Calculation / Inference: resistor drift and source bounds; PYRO1_CONT's figure assumes the 8.4 V pack with the bus already on) against the AO3400A's 0.65 V minimum threshold at 250 µA (Datasheet); check_r12 K-neighbours fails any above 0.45 V (the 0.20 V allowance for heat and sub-250 µA conduction is an Inference). The round-1 divider (4.7k / 10k) gave 1.00–1.12 V (Calculation / Inference: drift) and is replaced by 47k / 100k | D-R12-86, -93; R12F1-TRI-01 | No | Open |
| 22 | The 3V3A In2 island is dropped | 3V3A (VDDA and the sensor supplies) has no In2 island: the In2 link from the VDDA end (15.5, 60.6) to the R164 / U4 F.Cu island (19.65, 36.9) takes 2 vias. R164.2 supplies U4.5 (23.5, 40.64), C10, U4.8 and C31 on that island. One F→B via (23.5, 39.95) feeds C30 and U5 / C32 through 15.66 mm of B.Cu; each branch returns to F through its own via, (25.7, 42.75) and (25.8, 29.8), respectively (Measured; row 1); the AVA re-layout needed that In2 area for the CA corridor (supervisor decision). Noise effect on the ADC and sensors is an Inference (bench) | D-R12-95 | No | Open |
| 23 | C24 (NRST filter) at J2's end of the NRST run | C24 sits at (26.6, 45.18) beside J2, 19.54 mm of NRST copper from ball E1, including 15.68 mm on In2 (Measured, barrels excluded), because NRST's In2 lane could not reach the west pocket under the frozen PYRO1_CONT / ACT_EN_MCU runs (K-reference). That this is acceptable for a bench-only reset with the MCU's internal pull-up is an Inference; NRST's loop round J2 is gone since the polish pass (B under J2, D-R12-122): NRST 28.20 mm, routed / MST 1.56 (was 1.96; Measured on `68e6b650…`). No 0402 site with a GND via was found near E1 (D-R12-124; O-R12-30) | D-R12-98 | No | Open |
| 24 | Outline 46 × 90 mm | The owner's "Try 90 mm" (D-R12-99) replaces D-R12-24's 100 mm. Under the 120 mm rule (P1) and fit_check's 100 mm ceiling; the bay / sled length is not in `docs/VEHICLE.md`, so the vehicle fit is unchecked (O-R12-28). Fallback: the 100 mm re-layout on `r12-relayout-int` `4686580`, board `ef3194c0…` | D-R12-99 | Yes | Open |
| 25 | PE4 keeps the D-R11-23 3V3-neighbour exception | B2 / D2 are diagonal 3V3 neighbours of PE4 / C3: 0.731 mm ball-to-ball. Every PE4-to-3V3 item pair inside U1's courtyard under 1.0585 mm is an S-10 exception with a floor at its measured gap (18 pairs, Measured on `6e874d4e…`; `m3_design/r12_fire.py` "D-R11-23"): PE4's lane (20.6, 51.6) → (18.9, 51.6) to U1.B2's land **0.150**, to B2's dog-bone track **0.300** and via (19.8, 50.8) **0.525**, to U1.D2 0.950; the lane's 45° step (21, 52) → (20.6, 51.6) to U1.B2 0.315, the B2 track 0.465, the B2 via 0.856, U1.D2 0.881, D2's via (20.6, 53.2) 0.989 and D2's track 1.031; U1.C3 to U1.B2 / D2 0.731 each, to both dog-bone tracks 0.881 and to D2's via 0.839; PE4's run at x 18.7 to B2's via 0.825 / 0.929 and to its track 1.000 mm. A new or moved 3V3 item there fails S-10. A bridge drives Q124's gate and may fire an enabled match (Inference). This retained exception needs owner acceptance; row 17's X-ray action and rule 3's first-article checks (row 30) also stay | D-R11-23; D-R12-104, -126, -128; R12F2-TRI-12, R12F5-TRI-01 | Yes | Open |
| 26 | The shared RAW trunk (O-R12-31) | The 0.6 mm B.Cu run (45.2, 16.4) → (45.2, 29.2), 12.8 mm, and its 0.6 mm F.Cu link (44.5, 16.4) → (45.2, 16.4), 0.7 mm, carry U400's and D5's currents together: 46.1 °C at the summed design inputs 3.348 A, 34.6 °C at U9's 2.9 A, 4.3 °C at the 1.018 A fire-time budget (IPC-2152 upper bound, Calculation / Inference: load allocations, 80 % efficiency and D5's drop). 0.87 mm would hold 30 °C at 3.35 A. Accept, or widen it in a later copper pass | O-R12-31; D-R12-102, -133 | No | Open |
| 27 | Single-fault pin damage (R10 row 6) | PA6 (U1.J3, VLOGIC_SENSE) still reads VLOGIC through R60 100k over R61 10k (D-R12-21), and VLOGIC is RAW through D5, up to about 8 V, so a shorted R60 puts it on the analog pin: R10 row 6's PA6 case, unchanged | R10 row 6; D-R12-133 | No | Open |
| 28 | VCAP operating capacitance (R10 row 10) | C19 / C20 are still 2.2 µF X5R 0603 (CL10A225KO8NNNC): they meet ST's nominal value, but their combined operating capacitance and ESR are unqualified, as on R10 | R10 row 10; D-R12-133 | No | Open |
| 29 | Retention at 5 × 100 g (R10 row 12, REQUIREMENTS P3) | Still open, not passed by inspection. R12's tall or heavy parts: C84 (11.3 mm tall), J121 (8.9 mm), LS120 (THT) and J430's hinge; row 3 covers only the SH plugs | R10 row 12; D-R12-133 | No | Open |
| 30 | QSPI_IO2 / HSE_OUT next to Q124's gate, held by R12 firmware rule 3 | S-10 excepts 8 PE4-to-QSPI_IO2 pairs (floor 0.839 mm: U1.C3 to IO2's via (21.4, 50.8); 0.856 lane to that via; 1.015 to ball A3) and 8 PE4-to-HSE_OUT pairs (floor 0.720 mm). A steady IO2-against-PE4 fight puts 1.19–1.98 V on the gate and fires the match after about 0.55 ms (Inference, R10 R23-SAFETY-08); an HSE_OUT bridge holds the gate at ≤ 0.39 V while PE4 drives low only if OSC_OUT sources ≤ 8 mA (Inference). Both exceptions are acceptable only with rule 3 ([M3_R12 "Firmware"](M3_R12.md#firmware): quad read-verify ground refusal, QSPI limits while PC1 is high, PE4 low before HSE, HSE failure or CSS refusal, the cold-screen QSPI traffic check, and the first-article U1 X-ray round C3 plus the unpowered U3.3-to-R127.1 meter check) | D-R12-126, -127; R12F5-TRI-01 | Yes | Open |
| 31 | PYRO1_OUT–GND pairs under 1.040 mm | A bridge from PYRO1_OUT to GND passes bus current through an enabled match. S-10 holds PYRO1_OUT ≥ 0.25 mm from GND copper and ≥ 0.5 mm from GND fills (R10 row 1 had 0.177 / 0.180 mm surface pairs). Remaining pairs (Measured on `6e874d4e…`, F unless stated): C128.1–C128.2 0.340 (the capacitor's own lands); OUT track to C128.2 0.370 (two segments); R173.1 to GND via (11.7, 45.2) 0.432; J121.1 to GND_pour_B 0.5005 (B); C128.2 0.507 / 0.770; R173.1 to a GND track 0.507; C128.1 to GND track (4.5, 44.1)–(4.5, 43.6) 0.520; OUT tracks to that track 0.550 / 0.556 / 0.711 / 0.954; R173.1 to R127.2 0.678; OUT track (11.5, 46.7)–(12, 46.2) to the via, track and R127.2 0.719 / 0.794 / 0.903; GND via (4.5, 43.6) pairs 0.945–0.989; Q124.3 to via (8.2, 42.6) 0.975; J121.1's barrel to GND_In1 1.037 (In1). Every pair but the last is on an outer layer, so a bridge there is visible to AOI | D-R12-125, -126, -128 | Yes | Open |
| 32 | PYRO1_OUT–PYRO1_CONT pairs | PYRO1_CONT is PC0's pin: a bridge puts PYRO1_OUT on PC0, whose input clamp can pass bus current through the match into 3V3 (fire-capable or logic-destroying; Inference). Five S-10 exceptions, floors R173.1–R129.2 **0.464**, R173.1 to CONT track (12.9, 47.1)–(12.1, 47.9) 0.806, OUT track to R129.2 0.816, OUT tracks to R130.1 1.000 / 1.000 mm (Measured; surface, AOI-inspectable). Accept, or move R129 about 0.9 mm east to clear them (a crowded pocket; not done in round 5) | D-R12-126, -128 | Yes | Open |
| 33 | PYRO1_IGN rule and its pairs (new) | J121.2 / R134.1 (RAW_ACT through R134 2 Ω) is not a match-fire path, but a bridge to GND with the bus on puts about 3.7 A and 27 W through R134, a 2 W part (Calculation). S-10 holds PYRO1_IGN ≥ 0.25 mm from every net (≥ 0.5 mm from fills) except PYRO1_OUT and RAW_ACT. Pairs (Measured on `6e874d4e…`): R134.1 to GND via (16, 35.7) 0.409, to its track 0.484, to R133.2 0.785; J121.2 to GND_pour_B and GND_In1 0.5005 (was 0.100 / 0.251); R134.1 to **ARM1_SENSE** 0.580 (R133.1), 0.625 (via), 0.750, 0.921: ARM1_SENSE is PC5's pin, so that bridge back-drives the logic with bus voltage, held only at IGN's 0.25 mm limit (Inference on the effect) | D-R12-126, -128 | Yes | Open |

### Do (an order, process or bench action)

| # | You do | What it means | Decision / evidence | Blocks order? | Owner answer / date |
|---|---|---|---|---|---|
| 10 | Re-read AN2606 | DS12110 Rev 8's Tables 9–12 were re-read for every re-pinned ball and AF number (D-R12-93; Datasheet), so that half is done. Still open: AN2606's H74x loader pins for the moved functions (PA8–PA10, PA15, PB6 / PB7, PC9–PC12, PD2, PB10, PE12–PE14, PA7); st.com refused the download, so the roles are R11's AN2606 Rev 64 Table 119 reading (Inference) | D-R12-61A … -64A, -93; O-R12-23 | Yes | Open |
| 11 | Read the missing datasheets | FXLS90322 dual-channel (FXLS9xxxx Rev 7): pin-out, axis frame, medium-g range codes. LSM6DSVE: no datasheet found at ST | D-R12-50, -51; O-R12-21 | Yes | Open |
| 12 | Bench-check the axis signs | U4: roll = −gyro_Y, thrust −a_Y. U6 channel 1: +a forward. Both are a Calculation / Inference from figures and need a 1 g and rotation check before flight | D-R12-54; O-R12-15 | No (before flight) | Open |
| 13 | Check SH mating and the H743 lead | Mate a sample clone header with JST SH housings and confirm friction retention (O-R12-04). Check the pin orders against a real MicoAir H743 lead: the pin-1 end is unmarked in the source image, and the owner's board may be the v1 (O-R12-19) | D-R12-15, -31 | Yes | Open |
| 14 | Confirm the THT parts on Economic and J1's hole fit | J121 (DB125) and LS120 (QMB-09B-03), both JLC THT assembly, on the Economic order page; J1's 1.40 mm holes with a sample 5.0 mm terminal or the chosen lead | D-R12-29, -30, -85; O-R12-20 | Yes | Open |
| 15 | Bench items | LMR50410 with 4.7 µH: load step and stability (O-R12-06). HSE crystal after C25 / C26 15 pF: gm_crit 0.726–1.244 / 1.5 mA/V (17.1 % margin; Calculation / Inference: stray, D-R12-107); the old 18 pF +5 % corner reached 1.5027 mA/V. Cold start-up, drive level and frequency (MCO) remain bench checks (O-R12-09). PORT_4V8 over temperature and the LR900-F's real supply floor (O-R12-05, D-R12-83). PORT_4V8 at the ports during a four-stall fire and on a 6.0 V pack, when U400 runs past its 75 % recommended duty (VIN about 5.49–5.55 V): confirm the frequency foldback holds the window (D-R12-131, A-8) | R12_DECISIONS §4 | No | Open |
| 16 | Get JLC's DFM acceptance | Not queried: 0.10 mm track and clearance, the TFBGA escape with 0.3 / 0.45 mm vias at interstitial sites (0.2 mm via hole to copper, D-R12-23), the six recorded short-edge courtyards, and the reflow class of unread parts (O-R12-02). JLC's SMD pad-to-pad (different nets) 0.15 mm is now a DRU rule, and U6's eight corner lands carry NXP's 0.143 mm inner-corner cut (corner gap 0.344 mm, was 0.141 mm; mask web 0.244 mm; no different-net SMD pair under 0.2 mm; Measured, D-R12-129) | D-R12-03, -23, -24, -129 | Yes | Open |
| 17 | U1 X-ray at first article | As R11: a TFBGA bridge cannot be seen; X-ray U1 with attention to the balls around C3 (PE4) and F2 (PC1). PE4 spacing acceptance is row 25; X-ray fees are included in row 18's minimum totals | R11 row 17 | Yes | Open |
| 18 | Re-run cost and stock on order day | Live 2026-11-06T17:54–17:56Z on `66323cf0…` (JLC BOM byte-identical on `db1f0999…`, `68e6b650…` and `6e874d4e…`; the CPL too until round 5 moved four rows, D-R12-113, -121, -125): no shortfalls at 2 or 5 boards; M3 metric $65.02 / $45.68 per board; minimum all-in $173.69 / $279.93 including U1-only X-ray ($3.28 / $8.20; Calculation / Inference: X-ray count; bare PCB the Live 46 × 90 ENIG 0.5 oz quote, $25.10, cost_study.md §2.1), $3.69 over the $170 target at 2 boards. Counting U1 / U4 / U5 / U6 / U9 gives $186.81 / $292.23–300.43, above $170 at 2 boards and straddling $295 at 5 boards (Calculation / Inference: qualifying count and fee tier). Confirm the count and tier, including possible D402 / Y1 fees, on JLC's quote (D-R12-105). D120 / BAT54C Preferred Extended is exempt: 21 charged codes, $64.47 per order (D-R12-110; O-R12-12 closed). Re-run `FAB_NET=1 m3_design/r12_fab.sh` | stageE_relayout.md §5; D-R12-110 | Yes | Open |
| 19 | Accept the list and the agent decisions | Accept or reject the rows above and D-R12-01 … D-R12-133 | R12_DECISIONS.md | Yes | Open |
| 21 | JLC review of U5 and Y1 | JLC's Economic order page marks U5 (MS5607-02BA03, C97627) and Y1 (X322525MOB4SI, C9006): "The processing of this component is difficult. After placing an order, it will be reviewed. If PCBA advanced option is required, additional fees will be charged." Both carry JLC's `needAuditFlag` with no listed special fee (Measured 2026-11-06T00:58Z); every brand-name barometer on JLC is flagged, so U5 stays; Y1 stays on Basic because the review happens for U5 anyway. On order day accept JLC's review result by email; if it adds a fee for Y1 larger than an Extended feeder fee, swap Y1 to YXC C5444544 (same YSX321SL sheet, land and pinout; its 12 pF load is an Inference until its LCSC listing is read, as C9006's 12 pF comes from its listing, not the sheet) | D-R12-92, -117 | Yes | Open |

### R10 / R11 rows that carry to R12

R12 keeps the R10 safety networks and the single-switch scope, so these apply with the R12 dummy-fire threshold override in M3_R12 "Firmware" (D-R12-109;
0.4 V under its fixed 2 Ω test conditions) and R10 rule 3 restated for the BGA (D-R12-127); copper-dependent figures were
re-run in `stageD_analysis.md` and `stageE_relayout.md` §4:

- **R10 rows 1–2's fire-net gaps, re-listed with R12's own pairs (D-R12-128; Measured on `6e874d4e…`, check_r12
  S-10).** Row 2 (Q124's gate nets ≥ 1.0585 mm, R10 D-R26-04): PYRO1_GATE has no copper but GND within 1.0585 mm
  except Q124.3, its own drain land (1.044 mm, excepted); PYRO1_GATE_N–3V3 outside U1's courtyard is 1.420 mm (C13.1)
  and –PYRO1_OUT / CONT_MID 1.080 mm (R173); every pair under 1.0585 mm is an S-10 exception: the D-R11-23 3V3 pairs
  (row 25), QSPI_IO2 and HSE_OUT (row 30), HSE_IN (7 pairs, 0.150 mm at U1.C1: no DC drive), BOOT0 (0.625 mm: input
  with R5 10 kΩ to GND) and BAT_FAULT_N (0.950 mm: gate ≤ 0.29 V). U1's NC balls near PE4 (B1 0.150, B3 0.316, C4 / D3
  0.400, A1 0.450, B4 / D4 0.731 mm) stay analog (rule 3). Row 1 (PYRO1_OUT ≥ 1.040 mm from 3V3 / 3V3A, R10 D-R26-02):
  holds; no 3V3 / 3V3A copper within 1.6 mm on F and J121.1's barrel 1.0405 mm from the In2 3V3 fill (to the finished
  hole; the drilled wall is probably nearer, Inference). R12 widens it: PYRO1_OUT is ≥ 1.040 mm from every net but GND
  (row 31), PYRO1_CONT (row 32) and the not-a-path nets PYRO1_IGN / _COLD / _CONT_MID. The new PYRO1_IGN rule is row 33.
- One switch, no fuse, servo return through J122's shared GND, always-on ports. These are R10 rows 1–4 (rows 1–2's
  fire-net figures as above).
- R10 rows 6, 10 and 12 carry as rows 27–29.
- The 20 ms fire and the 36 ms watchdog guard (34.853 ms, Calculation on allocations / Inference).
- Switch-bounce immunity: R10 row 21's rule; the R12 worst-corner limit is 7.56 ms (Calculation / Inference).
- Pack selection, microSD and pad-check policy (R10 rows 13, 17, 18).
- Thermal qualification and the buzzer's +70 °C rating (R10 rows 33, 36; QMB-09B-03 shares the +70 °C limit).
- **Hold-up changes on R12.** C84 holds VLOGIC only (2.23–6.12 ms from a break, Calculation / Inference); the required
  hold-up time is still the open owner question (R10 rows 5, 25).

## M2 routing deviations

Measured on the current PCB `6e874d4e96ba3c6ab5d2a4163769c80aea6ba87002a4dd5c38eb85e7d93ca067` (round 5's fix pass,
D-R12-125 … -133) with `route_check --profile r12`; the review-only residual count below is `be81f40b…`'s (44 on both). All remain deviations pending owner acceptance (row 1). Coordinates are board
millimetres; `net` locations are the report's net anchors.

**Critical allowlist (3, D-R12-96).** 3V3A, SPI1_MISO and QSPI_CLK; reasons and measured lengths are in row 1.

**Noncritical leftovers (8; 11 before the polish pass).** Counted for review under M2 / audit 2 item 7, with no
per-instance measured exception required; retained cleanup items, not owner-accepted routing. The polish pass removed
CC1's and LED_YEL's tiny jogs and I2C1_SDA's neck (D-R12-123); NRST's detour (ratio 1.96, its F loop round J2) became
an `extra_vias` leftover (4 vias, ratio 1.56) when it moved under J2 on B (D-R12-122).

| Category | Net | Layer / report anchor |
|---|---|---|
| `tiny_jog` | SERVO2_MCU | B.Cu (28.6, 17.5) |
| `extra_vias` | BAT_FAULT_N | net (20.6, 11.97) |
| `extra_vias` | CAM_5V_SENSE | net (13.2, 57.82) |
| `extra_vias` | NRST | net (26.6, 45.6) |
| `extra_vias` | SERVO2_MCU | net (28.95, 11.35) |
| `extra_vias` | SERVO3_MCU | net (28.95, 9.05) |
| `extra_vias` | SERVO4_MCU | net (27.05, 9.05) |
| `extra_vias` | VLOGIC_SENSE | net (12.2, 57.82) |

**Review-only residuals (44, AUD-10 / `R10_REVIEW`).** 31 collinear nodes (exact straight splits; 21 of them sit on the
zone joins at y 17.5 and y 45.4, where `zones/merge.py` joins two fragments) and 13 segments wholly inside their own
pad (GND Y1.4, GND U6.17, GND R5.2, GND C31.2, GND U6.17, VBUS J3.B4A9, 3V3 R11.2, 3V3A R164.2, SPI1_MOSI U4.14, VLOGIC TP83.1, I2C1_SDA R13.1, BAT_ILIM R84.1, BST U2.1). No duplicate segments. Retained for review, not gated; connectivity, partial overlaps, crossings and DRC
remain gated.

**Information-only categories.** `route_check.py` `INFO` counts: `pad_end_offcentre` 285, `power_via_no_gnd` 12,
`passes_through_pad` 11, `short_layer_hop` 9, `width_change_junction` 6, `u_turn` 5, `extra_bends` 3 (on `6e874d4e…`;
`pad_end_offcentre` 292 on `68e6b650…`; `short_layer_hop` 10 and `u_turn` 6 before the polish pass). The count alone
does not establish a removable defect; they remain M2 review information, not acceptance.
