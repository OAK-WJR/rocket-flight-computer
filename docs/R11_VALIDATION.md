# R11 validation: deviations for owner acceptance

**Where R11 stands.** M3-ASSY-R11 is a CAD candidate on branch `m3-assy-r11`, PCB
`5f1a7e1dfcae95a3ebe06801cc74dc366aa83f477b416e25e72649f4365d2b63` (46 × 50 × 1.6 mm, six layers). It is not
accepted and nothing is ordered; R9 stays the accepted board and R8 its fallback. No review round has run on it yet
(stage F of `r11_plan.md`). The full state is stated once, in [M3_R11.md, "Current state"](M3_R11.md#current-state).
This file lists what the owner must accept or do for R11. Decision IDs are in
[`m3_design/r11/design/R11_DECISIONS.md`](../m3_design/r11/design/R11_DECISIONS.md); evidence labels as AGENTS §2.5.

**How to answer.** Write your answer and the date in the "Owner answer / date" column, or in a dated note here that
names the row. Nothing below is accepted yet. "Blocks order" rows must be answered before ordering.

## R11 owner decision table

### Accept (a risk or limit you take on)

| # | You accept | What it means and the measured figures | Decision / evidence | Blocks order? | Owner answer / date |
|---|---|---|---|---|---|
| 1 | PE4's spacing to 3V3 at the TFBGA | Ball C3 (PE4, PYRO1_GATE_N) is 0.731 mm from the 3V3 balls B2 / D2 (Calculation on the 0.8 mm pitch and 0.40 mm land). PE4's only F.Cu lane runs in the C2 / D2 row gap, 0.200 mm from D2's land and 0.300 mm from D2's dog-bone track (Measured). R10's floor is 1.0585 mm (D-R26-04). Every other PYRO1_GATE_N copper is ≥ 4.085 mm, PYRO1_GATE ≥ 3.106 mm and PYRO1_OUT ≥ 4.370 mm from 3V3 / 3V3A. A 3V3 bridge to PE4's net drives Q124's gate and may fire an enabled match (Inference, R10's reasoning). Only a fan-out or pin-map change could reach the limit. | D-R11-23, D-R11-30; stageD2.md §7 | Yes | Open |
| 2 | PE4's orthogonal neighbour is a driven output (found in stage E, not in any decision record) | Ball C3 (PE4) is 0.400 mm land to land from B3 (PE3, IMU_CS), which R11 drives push-pull and idles high (D-R11-49); PE4's track is 0.550 mm from B3's land (Measured by the stage E lane, pcbnew on `5f1a7e1d…`). On R10, PE3 was an undriven analog sentinel. A C3–B3 bridge fights PE4's low driver on Q124's gate network: R10's QSPI_IO2 / PE4 analysis of the same fight put 1.19–1.98 V on the gate and fired an enabled match after about 0.55 ms in most modelled corners (M3_R10 "Firmware" rule 3; Inference on driver resistances). No R11 analysis, screen or mitigation exists beyond the first-article U1 X-ray. Options: accept with the X-ray; add an unpowered meter check IMU_CS (U4.12) to R127.1 like rule 3's U3.3 check (Inference: not designed); or move IMU_CS off B3 in a re-plan. | M3_R11 "CH1 pyro"; binding note obligation 38 delta | Yes | Open |
| 3 | PYRO1_OUT to GND on the surface | Minimum 0.175 mm on F.Cu (the track at (6.3, 30.0) to the GND via (6.92, 31.6)), then 0.257 and 0.300 mm (Measured by the stage E lane). A bridge bypasses Q124 and fires an enabled match by itself: the same class as R10's 0.177 / 0.180 mm (R10 owner row 1). | M3_R11 "CH1 pyro" | Yes | Open |
| 4 | Nine single-via points (K-power `single_open_exceptions`) | Under the TFBGA: PA4's dog-bone (21.60, 28.80), BOOT0's (23.20, 27.20), VCAP2's (24.80, 27.20); outside: PA4's In3-to-B.Cu via (14.65, 39.90); R86.2 / C85.2's GND via (16.40, 39.00); R88.2's GND via (18.95, 32.47); R430.2's two GND vias (22.15, 9.75) / (24.70, 11.55); U402.2's GND via (22.15, 9.75). Each has a measured no-site reason in `r11_gate_data.json`. Effects: an open PA4 floats LOGIC_SOURCE_ST, so firmware rule 5 is an extra barrier, not a guarantee; the GND opens float an IC or divider ground (behaviour not re-read from the data sheets: Inference). Respin items if a later placement opens a site. | D-R11-34, -45, -48, -49, -58; stageC4.md §5 | Yes | Open |
| 5 | Two route_check allowlist entries | `critical_via_no_gnd SD_MOSI` at (29.80, 17.05): no legal GND via within 1.5 mm in an 11,289-point search, nearest 2.242 mm (Measured). `extra_vias CAM_RX_BUFFER`: 4 vias against 0 + 2, 19.2 mm; a grid router found a minimum of 3 vias, and 2 only through an In3 run that K-region forbids (Measured). | D-R11-54, D-R11-61, D-R11-63; `tools/route_check.py` ALLOWLIST_R11 | Yes | Open |
| 6 | The R11 legend set (owner acceptance pending, D-R11-83) | No legal silkscreen spot exists on either face for the middle GH contacts (J122.2–.4, J9.2–.4, J410 / J420 / J440 .2–.3), the words SERVO, RADIO and AUX, J2's rows 3–6 and J122's `SERVO + FROM HARNESS` note (Measured by the aid; 9 of the 12 contacts have none even with every via removed). R11 labels each GH port by its designator, pin 1 and the last pin (J9 also 5:RXI, J410 also GPS), J2 rows 1:3V3 and 2:SWDIO; the full maps move to the [harness pin map](R11_VEHICLE_HANDOFF.md#harness-pin-map). Every pyro, arming and battery legend is drawn and protected (J121 1:E1− / 2:E1+, J1 1:BAT+ / 2:GND, J400 1:SW / 2:SW, IGN, BAT, SWITCH). R10's terminal-legend rule D-AVA-01 is otherwise unchanged. | D-R11-66, -82, -83; stageD.md §3; stageD2.md §6 | Yes | Open |
| 7 | CAM_5V_SENSE single fault on PC2_C | R105 open puts CAM_5V (5.456 V nominal) on PC2_C through R104 10 kΩ. PC2_C is a TT_a pad whose absolute maximum is 4.0 V (DS12110 Rev 8 Table 119 p. 211, Table 9 p. 67; read in stage E from the R10 review extract, see M3_R11 "Sources"), so the fault exceeds it, as on R10's PB1 (R10 owner row 6). PC2_C's injection susceptibility is 0 / 0 mA (Table 156). The PA6 divider's single-fault case of R10 row 6 is unchanged. No design change. | D-R11-81; binding note obligation 29 delta | Yes | Open |
| 8 | Inner copper 0.5 oz and the 0.1 mm plane necks | JLC06161H-3313 has 15.2 µm inner copper (R10 30 µm; REQUIREMENTS M1 names 1 oz inner). The In2 3V3 base fill and the In1 / In4 GND planes are drawn at 0.12 mm clearance and 0.1 mm minimum width, so they pass between ball-field vias in necks about 0.16 mm wide (Calculation). Plane current capacity in those necks is not analysed; the narrowest current-carrying In2 neck (RAW to U400) is 1.4 mm against a 0.88 mm floor at 1.9 A (Calculation, Inference inputs). | D-R11-03, -27, -46, -50; stageB.md §3; stageC4.md §8 | Yes | Open |
| 9 | U401's thermal figure is an Inference | U401.11 has R10's two GAP-3 VIPPO vias, but R10's 80–110 °C/W and 109.2–123.9 °C junction figures carry over only as an Inference (thinner inner planes, U401 over J430); R10's 1.1 °C margin is not claimed. The 100 mA AUX allowance rests on that Inference until a first-article thermal test. | D-R11-75, D-R11-80; stageD_analysis.md §5 | No, if accepted with the test | Open |
| 10 | Three recorded narrow power pin entries | `power_narrow`: U9.5 (BAT_IN) 0.3 mm for 2.0 mm, U9.6 (RAW_PROTECTED) 0.3 mm for 1.5 mm, U401.9 (PORT_5V3) 0.25 mm for 0.5 mm, against the IPC-2152 30 °C floors (the same exception class as R10). | D-R11-25, -26; stageD_analysis.md §5; `r11_gate_data.json` | Yes | Open |
| 11 | Routing leftovers (REQUIREMENTS M2) | route_check r11 counts 25 unrecorded non-critical leftovers (378 instances in all categories), listed but not gated, as R10's AUD-10 class. | stageD2.md §2, §8; stageC5.md §6 | Yes | Open |
| 12 | New ROM-loader pin members | PB9 (CAM_MCU_TX, loader I2C1_SDA), PA15 (SERVO2_MCU, loader SPI3_NSS, held low by R155) and PB10 / PB11 (U5's I2C, loader USART3). The cases (no I2C master, no SPI3 clock, U12 and U402 held off, PA15's JTDI pull-up giving at most 0.83 V against R155) are Inference unless labelled; check_r11 K-loader passes with LOADER_R11. | D-R11-41, -49; stageC1b.md §7, §8.4 | Yes | Open |
| 13 | The e-match is never connected at the board | J121 is a pair of plated wire pads with a permanent AWG 20 pigtail to the bay's field terminal; R10's J121.2 pad check and igniter-resistance check move to that terminal. Soldered joints have no contact to open; the harness is tied to the sled within 20 mm of the pads. Joint quality and pigtail retention are unqualified. | D-R11-05, -13; [handoff](R11_VEHICLE_HANDOFF.md#pyro-pigtail-and-per-flight-checks) | Yes | Open |
| 14 | S-8 margins | 8 barrels, 24 inner rings; nearest foreign inner copper 1.012 mm (BAT_FAULT_N to an ACT_GATE via ring), ACT_DRV 1.069 mm, J121 holes 1.100 mm, against 1.0 mm (Measured). CAD clearances only, as R10 row 9. | stageD2.md §7; D-R11-60 | No, if accepted | Open |
| 15 | K-reference reads a sample within 0.005 mm of a plane edge as over it | 430 of 181,143 samples sit on the In1 / In4 antipad boundary drawn at the same 0.25 mm hole clearance; KiCad's polygon arcs lie up to 0.005 mm outside the circle. The gate now treats them as referenced; `m3.kicad_dru` is unchanged. | D-R11-59, -62 | No | Open |

### Do (an order, process or bench action)

| # | You do | What it means | Decision / evidence | Blocks order? | Owner answer / date |
|---|---|---|---|---|---|
| 16 | Get JLC's DFM acceptance | Not queried: the 0.1 mm track and clearance (JLC multilayer 0.09 mm) and the BGA escapes; the 0.1 mm plane necks; the 24 short-edge parts nearer than 2.5 mm (`short_edge_queries`, 0.555–1.955 mm) on an assembly panel with 5 mm rails on both short edges and mouse-bite tabs between the GH bodies (Inference until JLC accepts); the U401 VIPPO vias (resin-filled, copper-capped, planar: R10's ORDERING §8 item); naming JLC06161H-3313 on the order; U12's library pin-1 circle 0.025 mm from U13 pad 5's mask opening (JLC clips silkscreen at openings: Inference); C84 fitted by hand after both reflows. | D-R11-12, -15, -46, -50, -80; stageD.md §2; stageB.md §3 | Yes | Open |
| 17 | U1 X-ray at first article | A TFBGA bridge cannot be seen; R10's visual inspection of "U1 pins 1–5" becomes an X-ray of U1, with attention to C3's neighbours (rows 1–2). The U3.3-to-R127.1 meter check stays. | binding note obligation 38 delta | Yes (order the inspection) | Open |
| 18 | Fix the stock | Live JLC 2026-11-03T23:01:04Z: U9 C3662793 stock 18, orderable −93; U4 C51931514 stock 4, orderable −3; U2 C780769 stock 66, orderable −2866 (orderable an Inference about JLC's field, R20-BOM-01). Confirm in the cart on order day, else consign (ORDERING §8.1). Cost is $79.79 per board against the $84.41 cap ($4.62 under; M3 met on this snapshot). | D-R11-69, -84; stageD2.md §8 | Yes | Open |
| 19 | Read RM0433 for the register items | The EXTICR one-port-per-line layout is now checked against ST's CMSIS header (M3_R11 "Sources"); RM0433 itself was not read for SYSCFG_PMCR.PC2SO, the USB regulator bypass and VREFBUF on TFBGA-100 (stageA.md §2). Firmware items, not board items. | D-R11-81; stageA.md §2 | No | Open |
| 20 | First-article thermal, plate and fit checks | The plate model has no r11 profile and was not run (four corner supports, spans 39 × 43 mm: stiffness claim an Inference); the fit figures are stage B's (wire-pad allowances 0.36 mm from the bore, GH mouths 1.1 mm inside their edge, deepest bottom part C421 2.7 mm below the board); the U4 copper under its body against TN1383 is not measured on R11. | D-R11-10; stageB.md §4, §5, §11 | No, if accepted | Open |
| 21 | Accept the list and the agent decisions | Accept or reject the rows above and D-R11-01 … D-R11-84. | R11_DECISIONS.md | Yes | Open |

### R10 rows that carry to R11 unchanged in substance

R11 keeps R10's circuit (D-R11-01), so these rows of [R10_VALIDATION.md, owner decision table](R10_VALIDATION.md#owner-decision-table)
apply to R11 as written, except where noted; copper-dependent figures were re-run in stageD_analysis.md and agree:

- Row 1 (one switch, no fuse, no physical break while powered); row 2's load-switch, enable and sense latent faults
  (R11's surface pairs are not re-measured except rows 1–3 above).
- Row 3 (servo return through the shared GND pin of J122); row 4 (always-on GPS, radio and AUX on one supply).
- Rows 5 and 25 (hold-up 0.46–0.54 ms with all ports on, the open hold-up requirement): identical figures
  (stageD_analysis.md §4).
- Row 6 (single-fault pin damage): PA6 unchanged; PB1's case moved to PC2_C (row 7 above).
- Row 7 (20 ms firing and the 36 ms guard are calculations on allocations): 34.853 ms unchanged.
- Row 10 (VCAP C19 / C20 operating capacitance): same parts.
- Row 12 (retention at 5 × 100 g): GH latches and soldered pads replace the DB125s; unproven.
- Rows 13, 17 and 18 (microSD, pack selection, pad-check policy).
- Row 21 (switch-bounce immunity): the same figures (stageD_analysis.md §3).
- Rows 33 and 36 (thermal qualification, the 55 °C interim site limit and LS120's +70 °C rating): same parts; R11's
  board-to-air figure is not re-derived (Inference).
- Row 29 (U9 EN through one via) is **closed on R11**: the EN chain has no via (D-R11-25). Rows 22, 28, 30 and 31 are
  R10 layout items with no R11 counterpart (R11 has no DB125 wire-room rule; its J400 chain is one B.Cu run).
