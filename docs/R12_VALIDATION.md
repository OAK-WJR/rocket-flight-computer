# R12 validation: deviations for owner acceptance

**Where R12 stands.** M3-ASSY-R12 is a CAD candidate on branch `r12-stage-d`, PCB
`d776c5d7181e10f0ea3d16960050b63b5c5e7d61bb26074c4ea3b204b71b7161` (46 × 100 × 1.6 mm, four layers, every part on
the top face for JLC Economic PCBA). It is not accepted and nothing is ordered; R9 stays the accepted board and R8 its
fallback. No review round has run on it yet (stage F of `r12_plan.md`). The full state is stated once, in
[M3_R12.md, "Current state"](M3_R12.md#current-state). This file lists what the owner must accept or do for R12.
Decision IDs are in [`m3_design/r12/design/R12_DECISIONS.md`](../m3_design/r12/design/R12_DECISIONS.md); evidence labels
as AGENTS §2.5.

**How to answer.** Write your answer and the date in the "Owner answer / date" column, or in a dated note here that
names the row. Only row A-9 is accepted (owner, 2026-11-04). Answer the "Blocks order" rows before ordering.

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
| A-7 | F11: LS120 MLT-5020 | QMB-09B-03 THT, owner-fitted; pin 1 = (+) an Inference (now marked '+' / '-' on F.Fab, D-R12-82) | D-R12-16 | Yes | Open |
| A-8 | PORT_4V8 within 4.5–5.0 V at every corner | Inside at initial tolerance at the regulator (4.539–4.943 V); 4.489–4.999 V in the independent-drift bound (Calculation). See also row 6 for the ports under load | D-R12-07, -21; O-R12-05, -16 | Yes | Open |
| A-9 | Economic reflow 255 ± 5 °C against makers' 250 °C peaks (SS34 D5 / D6 / D9, MS5607 U5; J430 and SRV05-4 by Inference) | **Accepted by the owner, 2026-11-04**; the effect on each part is an Inference | D-R12-49 | — | Accepted 2026-11-04 |
| A-10 | F1 / F2 name one IMU (low-g, high-g and gyro) | LSM6DSVE (low-g, ±4000 dps) plus FXLS90322 (XY medium-g, ±150 g maximum) | D-R12-50, -51 | Yes | Open |

### Accept (a risk or limit you take on)

| # | You accept | What it means and the figures | Decision / evidence | Blocks order? | Owner answer / date |
|---|---|---|---|---|---|
| 1 | Two route_check allowlist entries | SPI1_SCK takes 3 vias (19.34 mm): the SPI1 pin orders of U4, U6 and U1 cross on a one-sided board, and clearing it means rotating U6, an axis-map change. USB_DP takes 3 vias (19.22 mm): J3's 0.5 mm pin interleave forces a B.Cu link. Both have a GND via within 1.5 mm of each layer change (Measured; route_check figures fixed in `ROUTE_FIGURES_R12`) | D-R12-75A | Yes | Open |
| 2 | J122's harness note optional | `SERVO + FROM HARNESS` (18.9 mm of ink) has no legal spot within 6 mm of J122 on either face (Measured, stageD.md §2). check_r12 waives only its absence; every contact legend, word, SWD row and SHOWN_REFS designator is still required. The rule it states is in the handoff | D-R12-81 | Yes | Open |
| 3 | SH friction retention | No latch: each SH plug needs an adhesive / RTV dab or a tie at every flight (handoff, per-flight step 0) | D-R12-31; O-R12-18 | Yes | Open |
| 4 | U9 feed at 0.4 mm | The C96.1 → C88.1 → U9.5 run is 0.4 mm wide for 4.13 mm. IPC-2152 upper bound (no plane credit): 55.2 °C rise at R10's 2.9 A design current, about 36 °C at the 2.34 A fire-time current, over the 30 °C basis (Calculation / Inference). It is 0.4 mm because of R10's C88 topology and U9.4's escape via; widening it means a layout pass | D-R12-79; O-R12-25 | No | Open |
| 5 | PA6 can trip during a fire into a shorted match | At four stalls with the match and its leads shorted, VLOGIC is 0.005 V into PA6's trip band at the nominal divider ratio and 0.096 V with the 1 % divider (Calculation / Inference). Firmware must not treat it as a battery loss | stageD_analysis.md §5; O-R12-07, -17 | No | Open |
| 6 | PORT_4V8 at the ports under load | At the 0.561 A always-on budget the port pins are ≥ 4.497–4.500 V initial and ≥ 4.447–4.450 V at the drift corner (J420 lowest), against the MicoAir LR900's 4.5 V floor (Calculation / Inference). The 75 mm, 0.5 mm east-edge feed is 70–75 mΩ. Options: accept, measure the module's real floor, raise the setpoint (the drift-bound top is then above 5.0 V), or widen the feed | stageD_analysis.md §6; O-R12-16, -26 | Yes | Open |
| 7 | Q120 / Q121 VGS above 12 V only on a pack above 14.60 V with the bus on | Gate drive is −0.833 × BAT_IN. A 3S pack is cut off by OVLO; only a transient toward the 19.9 V clamp would exceed ±12 V (Inference) | D-R12-10; O-R12-10 | No | Open |
| 8 | Library silkscreen near openings | Footprint graphics within JLC's 0.15 mm pad-to-silkscreen gap: D120's circle 0.10 mm from R130.1, U403 / U400 pin-1 circles 0.092 mm from C433.2 / C400.2, U5's outline 0.13 mm from C30.1 / .2 (Measured). JLC clips silkscreen at openings (Inference). The post stage prints these; it does not draw them | stageD.md §2 | No | Open |
| 9 | 76 hidden designators | 76 designators have no unambiguous spot and are kept on F.Fab (listed in stageD.md §2); they show on the assembly drawings, not on the board | D-R12-80 | No | Open |

### Do (an order, process or bench action)

| # | You do | What it means | Decision / evidence | Blocks order? | Owner answer / date |
|---|---|---|---|---|---|
| 10 | Re-read DS12110 Rev 8 Tables 10–14 and AN2606 | Confirm the alternate-function numbers of the stage C re-pins, which were read only from KiCad's ST symbol: PB10 AF9 QUADSPI_BK1_NCS, PA8 / PC9 AF4 I2C3, PE12–PE14 AF5 SPI4. Confirm PA7 / PA10 / PC11 as GPIO, and the H74x loader pins | D-R12-61A … -64A; O-R12-23 | Yes | Open |
| 11 | Read the missing datasheets | FXLS90322 dual-channel (FXLS9xxxx Rev 7): pin-out, axis frame, medium-g range codes. LSM6DSVE: no datasheet found at ST | D-R12-50, -51; O-R12-21 | Yes | Open |
| 12 | Bench-check the axis signs | U4: roll = −gyro_Y, thrust −a_Y. U6 channel 1: +a forward. Both are a Calculation / Inference from figures and need a 1 g and rotation check before flight | D-R12-54; O-R12-15 | No (before flight) | Open |
| 13 | Check SH mating and the H743 lead | Mate a sample clone header with JST SH housings and confirm the latch / friction (O-R12-04). Check the pin orders against a real MicoAir H743 lead: the pin-1 end is unmarked in the source image, and the owner's board may be the v1 (O-R12-19) | D-R12-15, -31 | Yes | Open |
| 14 | Confirm J121 on Economic and J1's hole fit | J121 (DB125 THT, JLC-fitted) on the Economic order page; J1's 1.40 mm holes with a sample 5.0 mm terminal or the chosen lead | D-R12-29, -30; O-R12-20 | Yes | Open |
| 15 | Bench items | LMR50410 with 4.7 µH: load step and stability (O-R12-06). HSE crystal at gm_crit 1.43 / 1.5 mA/V: cold start-up and drive level (O-R12-09). PORT_4V8 over temperature (O-R12-05) | R12_DECISIONS §4 | No | Open |
| 16 | Get JLC's DFM acceptance | Not queried: 0.10 mm track and clearance, the TFBGA escape with 0.3 / 0.45 mm vias at interstitial sites (0.2 mm via hole to copper, D-R12-23), the six recorded short-edge courtyards, and the reflow class of unread parts (O-R12-02) | D-R12-03, -23, -24 | Yes | Open |
| 17 | U1 X-ray at first article | As R11: a TFBGA bridge cannot be seen; X-ray U1 with attention to the balls around C3 (PE4) and F2 (PC1) | R11 row 17 | Yes | Open |
| 18 | Re-run cost and stock on order day | Live 2026-11-05: no shortfalls at 2 or 5 boards; M3 metric $61.88 / $44.38 per board. JLC may or may not waive the BAT54C Preferred Extended feeder fee (O-R12-12). Re-run `FAB_NET=1 m3_design/r12_fab.sh` | stageD.md §4 | Yes | Open |
| 19 | Accept the list and the agent decisions | Accept or reject the rows above and D-R12-01 … D-R12-82 | R12_DECISIONS.md | Yes | Open |

### R10 / R11 rows that carry to R12

R12 keeps the R10 safety networks and the single-switch scope, so these apply as written (copper-dependent figures were
re-run in `stageD_analysis.md`):

- One switch, no fuse, servo return through J122's shared GND, always-on ports. These are R10 rows 1–4.
- The 20 ms fire and the 36 ms watchdog guard (34.853 ms, Calculation on allocations).
- Switch-bounce immunity: R10 row 21's rule; the R12 worst-corner limit is 7.56 ms.
- Pack selection, microSD and pad-check policy (R10 rows 13, 17, 18).
- Thermal qualification and the buzzer's +70 °C rating (R10 rows 33, 36; QMB-09B-03 shares the +70 °C limit).
- **Hold-up changes on R12.** C84 holds VLOGIC only (2.23–6.12 ms from a break, Calculation / Inference); the required
  hold-up time is still the open owner question (R10 rows 5, 25).
