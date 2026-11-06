# R12 validation: deviations for owner acceptance

**Where R12 stands.** M3-ASSY-R12 is a CAD candidate on branch `r12-port-fix`, PCB
`d6e4f7ee0fc3c5d72176493717eb692316e84a21ac892437b56f649e8e76fc64` (46 × 100 × 1.6 mm, four layers, every part on
the top face for JLC Economic PCBA). It is not accepted and nothing is ordered; R9 stays the accepted board and R8 its
fallback. Stage F round 1 found verified real errors; its documentation fix pass is recorded in STATUS.md.
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
| A-8 | PORT_4V8 within 4.5–5.0 V at every corner | Inside at every tolerance and drift corner since D-R12-83 (R401 0.1 % 25 ppm/K, R404 5.1k): 4.603–4.938 V initial, 4.571–4.972 V drift at the regulator; ≥ 4.529 V at the ports under the 0.561 A budget (Calculation). The LR900-F's 4.5–5.0 V is the project record (maker page: "5V DC", no range; Inference); the GPS's 3.3–5 V is the maker's | D-R12-07, -21, -83 | Yes | Open |
| A-9 | Economic reflow 255 ± 5 °C against makers' 250 °C peaks (SS34 D5 / D6 / D9, MS5607 U5; J430 and SRV05-4 by Inference; since D-R12-85 also C84, rated 255 °C peak) | **Accepted by the owner, 2026-11-04**; the effect on each part is an Inference | D-R12-49 | — | Accepted 2026-11-04 |
| A-10 | F1 / F2 name one IMU (low-g, high-g and gyro) | LSM6DSVE (low-g, ±4000 dps) plus FXLS90322 (XY medium-g, ±150 g maximum) | D-R12-50, -51 | Yes | Open |

### Accept (a risk or limit you take on)

| # | You accept | What it means and the figures | Decision / evidence | Blocks order? | Owner answer / date |
|---|---|---|---|---|---|
| 1 | M2 routing deviations ([full list below](#m2-routing-deviations)) | SPI1_SCK takes 3 vias (19.34 mm): the SPI1 pin orders of U4, U6 and U1 cross on a one-sided board, and clearing it means rotating U6, an axis-map change. USB_DP takes 3 vias (19.22 mm): J3's 0.5 mm pin interleave forces a B.Cu link. Both have a GND via within 1.5 mm of each layer change (Measured; route_check figures fixed in `ROUTE_FIGURES_R12`) | D-R12-75A | Yes | Open |
| 2 | J122's harness note optional | `SERVO + FROM HARNESS` (18.9 mm of ink) has no legal spot within 6 mm of J122 on either face (Measured, stageD.md §2). check_r12 waives only its absence; every contact legend, word, SWD row and SHOWN_REFS designator is still required. The rule it states is in the handoff | D-R12-81 | Yes | Open |
| 3 | SH friction retention | No latch: each SH plug needs an adhesive / RTV dab or a tie at every flight (handoff, per-flight step 0) | D-R12-31; O-R12-18 | No | Accepted 2026-11-03 |
| 4 | ~~U9 feed at 0.4 mm~~ | **Closed by D-R12-84** (U9 0.3 mm east, C88 on the bar line): the feed is 0.8 mm (24.9 °C at 2.9 A) except U9.5's 1.3 mm, 0.4 mm pin entry; nothing to accept | D-R12-84; O-R12-25 | No | Closed (agent fix) |
| 5 | PA6 can trip during a fire into a shorted match | At four stalls with the match and its leads shorted, VLOGIC is +0.007 V above PA6's trip top at the nominal divider ratio, 0.084 V into the band with the 1 % divider (match alone shorted: 0.040 V into it with tolerance; Calculation / Inference). Firmware must not treat it as a battery loss | stageD_analysis.md §5; O-R12-07, -17 | No | Open |
| 6 | ~~PORT_4V8 at the ports under load~~ | **Closed by D-R12-83**: at the 0.561 A budget the port pins are ≥ 4.561 V initial and ≥ 4.529 V at the drift corner (J420 lowest), ≤ 4.972 V at no load (Calculation / Inference). Cost: one Extended code, +$3.07 per order. What stays: bench-read the LR900-F's real floor (row 15) | D-R12-83; O-R12-16, -26 | No | Closed (agent fix) |
| 7 | Q120 / Q121 VGS above 12 V only on a pack above about 14.4 V with the bus on | Maximum-ratio corner: 12 / (51 / 60.8) + 0.1 = 14.41 V, assuming a 0.1 V Q122 drop (Calculation / Inference). A 3S pack is cut off by OVLO; only a transient toward the 19.9 V clamp would exceed ±12 V (Inference) | D-R12-10; O-R12-10 | No | Open |
| 8 | Library silkscreen near openings | Footprint graphics within JLC's 0.15 mm pad-to-silkscreen gap: D120's circle 0.10 mm from R130.1, U403 / U400 pin-1 circles 0.092 mm from C433.2 / C400.2, U5's outline 0.13 mm from C30.1 / .2 (Measured). JLC clips silkscreen at openings (Inference). The post stage prints these; it does not draw them | stageD.md §2 | No | Open |
| 9 | 76 hidden designators | 76 designators have no unambiguous spot and are kept on F.Fab (listed in stageD.md §2); they show on the assembly drawings, not on the board | D-R12-80 | No | Open |

### Do (an order, process or bench action)

| # | You do | What it means | Decision / evidence | Blocks order? | Owner answer / date |
|---|---|---|---|---|---|
| 10 | Re-read DS12110 Rev 8 Tables 10–14 and AN2606 | Confirm the alternate-function numbers of the stage C re-pins, which were read only from KiCad's ST symbol: PB10 AF9 QUADSPI_BK1_NCS, PA8 / PC9 AF4 I2C3, PE12–PE14 AF5 SPI4. Confirm PA7 / PA10 / PC11 as GPIO, and the H74x loader pins | D-R12-61A … -64A; O-R12-23 | Yes | Open |
| 11 | Read the missing datasheets | FXLS90322 dual-channel (FXLS9xxxx Rev 7): pin-out, axis frame, medium-g range codes. LSM6DSVE: no datasheet found at ST | D-R12-50, -51; O-R12-21 | Yes | Open |
| 12 | Bench-check the axis signs | U4: roll = −gyro_Y, thrust −a_Y. U6 channel 1: +a forward. Both are a Calculation / Inference from figures and need a 1 g and rotation check before flight | D-R12-54; O-R12-15 | No (before flight) | Open |
| 13 | Check SH mating and the H743 lead | Mate a sample clone header with JST SH housings and confirm the latch / friction (O-R12-04). Check the pin orders against a real MicoAir H743 lead: the pin-1 end is unmarked in the source image, and the owner's board may be the v1 (O-R12-19) | D-R12-15, -31 | Yes | Open |
| 14 | Confirm the THT parts on Economic and J1's hole fit | J121 (DB125) and LS120 (QMB-09B-03), both JLC THT assembly, on the Economic order page; J1's 1.40 mm holes with a sample 5.0 mm terminal or the chosen lead | D-R12-29, -30, -85; O-R12-20 | Yes | Open |
| 15 | Bench items | LMR50410 with 4.7 µH: load step and stability (O-R12-06). HSE crystal at gm_crit 1.43 / 1.5 mA/V: cold start-up and drive level (O-R12-09). PORT_4V8 over temperature and the LR900-F's real supply floor (O-R12-05, D-R12-83) | R12_DECISIONS §4 | No | Open |
| 16 | Get JLC's DFM acceptance | Not queried: 0.10 mm track and clearance, the TFBGA escape with 0.3 / 0.45 mm vias at interstitial sites (0.2 mm via hole to copper, D-R12-23), the six recorded short-edge courtyards, and the reflow class of unread parts (O-R12-02) | D-R12-03, -23, -24 | Yes | Open |
| 17 | U1 X-ray at first article | As R11: a TFBGA bridge cannot be seen; X-ray U1 with attention to the balls around C3 (PE4) and F2 (PC1) | R11 row 17 | Yes | Open |
| 18 | Re-run cost and stock on order day | Live 2026-11-05T19:19–19:21Z: no shortfalls at 2 or 5 boards; M3 metric $66.51 / $46.25 per board; all-in $173.39 / $274.59 (Calculation; the 2-board total is $3.39 over r12_plan's $170 target). JLC may or may not waive the BAT54C Preferred Extended feeder fee (O-R12-12). Re-run `FAB_NET=1 m3_design/r12_fab.sh` | stageD.md §7 | Yes | Open |
| 19 | Accept the list and the agent decisions | Accept or reject the rows above and D-R12-01 … D-R12-85 | R12_DECISIONS.md | Yes | Open |

### R10 / R11 rows that carry to R12

R12 keeps the R10 safety networks and the single-switch scope, so these apply as written (copper-dependent figures were
re-run in `stageD_analysis.md`):

- One switch, no fuse, servo return through J122's shared GND, always-on ports. These are R10 rows 1–4.
- The 20 ms fire and the 36 ms watchdog guard (34.853 ms, Calculation on allocations / Inference).
- Switch-bounce immunity: R10 row 21's rule; the R12 worst-corner limit is 7.56 ms.
- Pack selection, microSD and pad-check policy (R10 rows 13, 17, 18).
- Thermal qualification and the buzzer's +70 °C rating (R10 rows 33, 36; QMB-09B-03 shares the +70 °C limit).
- **Hold-up changes on R12.** C84 holds VLOGIC only (2.23–6.12 ms from a break, Calculation / Inference); the required
  hold-up time is still the open owner question (R10 rows 5, 25).

## M2 routing deviations

Measured on PCB `d6e4f7ee0fc3c5d72176493717eb692316e84a21ac892437b56f649e8e76fc64`; source: round 1
`reports/route.txt` (counts) and `reports/route.json` (locations), with stageC.md §4 for the noncritical leftovers.
This is the reviewed board's list, not a claim about later copper. All remain deviations pending owner acceptance
(row 1). Coordinates are board millimetres; `net` locations are the report's net anchors, not individual via sites.

**Critical allowlist (2, D-R12-75A).** Reasons and measured lengths are in row 1. SPI1_SCK's three vias are
(23.8, 38.0), (24.7, 38.9), (24.2, 46.3): the SPI pin orders cross. USB_DP's three vias are (38.0, 43.25),
(38.0, 44.25), (27.4, 51.2): J3's interleave and the crossing to U1 require the B.Cu link.

**Noncritical leftovers (13).** These are counted for review under M2 / audit 2 item 7, with no per-instance
measured exception required. They are retained cleanup items, not owner-accepted routing; stageC.md records a
specific obstacle only for LED_RED (the GPS / RADIO bus and NRST's F.Cu run block a shorter crossing).

| Category | Net | Layer / report anchor |
|---|---|---|
| `tiny_jog` | SERVO1_MCU | F.Cu (22.95, 48.2) |
| `tiny_jog` | SERVO3_MCU | F.Cu (18.3, 55.6) |
| `extra_vias` | BAT_FAULT_N | net (14.4, 62.57) |
| `extra_vias` | BUZZ_DRV | net (8.6, 77.93) |
| `extra_vias` | CAM_5V_SENSE | net (28.58, 21.6) |
| `extra_vias` | I2C1_SCL | net (32.37, 33.2) |
| `extra_vias` | IMU_INT1 | net (24.2, 52) |
| `detour` | LED_RED | net (30.07, 73.6) |
| `extra_vias` | SERVO1_MCU | net (27.05, 11.35) |
| `extra_vias` | SERVO2_MCU | net (28.95, 11.35) |
| `extra_vias` | SERVO3_MCU | net (28.95, 9.05) |
| `extra_vias` | SERVO4_MCU | net (27.05, 9.05) |
| `extra_vias` | VLOGIC_SENSE | net (27.4, 28.02) |

**Review-only residuals (23, AUD-10 / `R10_REVIEW`).** The 19 collinear nodes are exact straight splits with no
extra path; the 2 duplicate segments are redundant same-net copper; the 2 inside-pad segments lie wholly inside
the named pad. These categories are retained for review rather than gated under AUD-10; that classification is
not a reason to claim the cleanup complete. Connectivity, partial overlaps, crossings and DRC remain gated.

| Category | Net | Layer / location |
|---|---|---|
| `segment_inside_pad` | 3V3 | F.Cu (29.48, 41.7), U6.1 |
| `segment_inside_pad` | BAT_ILIM | F.Cu (17.5, 17.1), R84.1 |
| `duplicate_segment` | GND | F.Cu (36.3, 19.9)–(36.3, 20.4) |
| `duplicate_segment` | GND | F.Cu (14.7, 53.4)–(15.2, 53.4) |
| `collinear_unmerged` | PORT_SENSE | B.Cu (20.7, 73.8) |
| `collinear_unmerged` | PORT_SENSE | B.Cu (21.8, 58.4) |
| `collinear_unmerged` | CAM_5V_SENSE | F.Cu (18.6, 53.2) |
| `collinear_unmerged` | CAM_5V_SENSE | B.Cu (21.8, 40) |
| `collinear_unmerged` | VLOGIC_SENSE | F.Cu (21.4, 58.4) |
| `collinear_unmerged` | ACT_GATE | F.Cu (5.8, 25.7) |
| `collinear_unmerged` | USB_DM | F.Cu (27.4, 52) |
| `collinear_unmerged` | LED_RED | F.Cu (21.8, 58.4) |
| `collinear_unmerged` | HG_CS | F.Cu (25.4, 49.6) |
| `collinear_unmerged` | GPS_TX_MCU | F.Cu (25.2, 81.1) |
| `collinear_unmerged` | SERVO3_MCU | F.Cu (18.6, 55.6) |
| `collinear_unmerged` | BOOT0 | B.Cu (23.4, 49.6) |
| `collinear_unmerged` | SERVO4_MCU | F.Cu (18.2, 56.8) |
| `collinear_unmerged` | PYRO1_CONT | F.Cu (18.6, 54.4) |
| `collinear_unmerged` | HSE_IN | F.Cu (18.6, 52) |
| `collinear_unmerged` | BAT_SW_RETURN | F.Cu (11.3, 6.5) |
| `collinear_unmerged` | I2C1_SDA | F.Cu (27.4, 53.2) |
| `collinear_unmerged` | I2C1_SCL | F.Cu (27.4, 52.4) |
| `collinear_unmerged` | AUX_TX_MCU | F.Cu (27.4, 54.4) |

**Information-only categories (566 instances).** `route_check.py` `INFO` counts these shapes / proximities;
the count alone does not establish a removable defect. They remain M2 review information, not acceptance.

| Category | Count | Why information-only |
|---|---|---|
| `width_change_junction` | 5 | Width changes at a branch or via, rather than a gated series neck-down |
| `pad_end_offcentre` | 485 | Off-centre entry within a pad; the count alone does not establish a routing violation |
| `passes_through_pad` | 3 | Same-net pad crossings; connectivity and DRC are separate checks |
| `extra_bends` | 28 | Bend-count heuristic; removable staircase / local-bump rules are gated separately |
| `u_turn` | 5 | Cumulative heading-change heuristic; it does not itself prove a removable detour |
| `short_layer_hop` | 22 | Short-hop heuristic; layer-change GND partners and removable chain defects are checked separately |
| `power_via_no_gnd` | 18 | The mandatory GND-partner rule applies to critical signals, not power rails |
