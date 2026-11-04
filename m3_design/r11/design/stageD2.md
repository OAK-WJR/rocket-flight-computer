# R11 stage D fix pass (2026-11-03)

Follows stageD.md and stageD_analysis.md; decisions D-R11-78 … D-R11-84 in `R11_DECISIONS.md`. Nothing is committed or
ordered. Labels (AGENTS §2.5): **Measured** = read from the CAD or a tool run on it; **Calculation** = arithmetic on CAD
copper and datasheet values; **Simulation** = the numerical hot-plug model; **Inference** = anything resting on an
unmeasured or estimated input (a figure with an inferred input is an Inference). No physical test was run. Coordinates
are board mm (x east, y forward from the aft edge).

## 1. Result

Board `m3_design/r11/m3.kicad_pcb` SHA-256 `5f1a7e1dfcae95a3ebe06801cc74dc366aa83f477b416e25e72649f4365d2b63`, built
twice from the final tree by `m3_design/r11_build.sh` with the same hash (Measured). The board and `m3_design/r11/fab/`
are staged in git (not committed). On it (Measured): DRC 0 violations, 0 unconnected, 0 parity, ERC 0; r11_sch_check
OK; metadata / 3D audit OK; check_r11 every rule OK, K-legends, K-copper (GAP-3) and the new K-exti included;
route_check r11 0 failing, 2 allowlisted, 0 stale; the R11 fab package bound and its content checks OK;
`tools/test_r11_check.py` 48 tests OK with `R11_BOARD_REQUIRED=1`. `tools/check.sh` exit status: section 8.

| Stage D finding | Fix | Decision |
|---|---|---|
| Metadata audit: 21 parts with R10's `LCSC Part` | the field follows `LCSC` | D-R11-78 |
| Hot-plug: 576 / 2304 fail the 10 V/µs fall | C80 on the B.Cu trunk beside C88 | D-R11-79 |
| U401.11 without thermal vias | R10's two GAP-3 VIPPO vias restored | D-R11-80 |
| EXTI line 5 shared by PA5 / PD5 | IMU_INT1 to PD6 (C6, EXTI6) | D-R11-81 |
| K-legends: 22 items with no legal spot | room for SWITCH and Q120; R11 legend set for the rest | D-R11-82, -83 |

## 2. Copper and placement changes (Measured)

* **C80** F (14.9, 9.0) rot 90 → B (7.6, 8.6) rot 0. Pad 1 (6.125, 8.6) → 0.7 mm B.Cu stub to the trunk at
  (6.125, 7.15); pad 2 (9.075, 8.6) → 0.4 mm B.Cu to C88.2's GND via (10.21, 8.6). C80.1–C96.1 F.Cu link removed.
  C88.2's link widened 0.3 → 0.4 mm; D8.2's F.Cu GND run extended to C96.2's via (16.2, 8.275); C96.2's run 0.4 → 0.5 mm.
* **U401.11**: GND vias 0.5 / 0.3, filled and capped, at (41.2, 22.4) and (41.8, 22.4); the pad's link to U401.4 now
  (41.5, 22.9) → (40.35, 22.9), 0.4 mm.
* **IMU_INT1**: U1.C6 → dog-bone via (24.8, 25.6) → In3 (25.6, 24.8) → x 25.6 lane → U4.4 as before; via (24.8, 24.8) gone.
* **GND vias**: C87.2's (14.8, 6.53) → (14.05, 6.63); R81.2's second barrel (14.38, 9.15) removed.

route_check r11 against the stage D board `d799a0b6…` (Measured, by category and instance): 0 failing on both; the
allowlist (2) and the 25 unrecorded leftovers are the same items; instances 381 → 378. Gone: IMU_INT1's In3
collinear_unmerged at (25.2, 24.4), a U401.11 segment_inside_pad and U401.11's pad_end_offcentre at (41.0, 22.9)
(0.707 mm). New: U401.11's pad_end_offcentre at (41.5, 22.9) (0.5 mm), the same pad's one entry, moved off the VIPPO
vias (a link from the pad centre would cross both vias: via_on_track). No other new instance in any category.

## 3. Hot-plug (Simulation / Inference; `tools/r11_hotplug.py`, R10's model, corners and limits unchanged)

Inputs `hotplug_inputs_r11.json` (board `5f1a7e1d…`, 33 network edges), results `hotplug_results_r11.json`.

| Figure (limit) | R10 `a0ec075e…` | R11 stage D `b7e2decb…` | R11 now |
|---|---|---|---|
| Required cases failing | 0 / 2304 | 576 / 2304 | **0 / 2304** |
| Steepest fall (≤ 10 V/µs) | 8.995 | 15.04 ('gnd'), 12.32 ('near') | **8.663** ('near'), 8.500 ('gnd') |
| Steepest fall by harness 0.1 / 0.5 / 1 / 2 µH | — | 15.04 / 3.69 / — / — | 8.663 / 3.821 / 2.391 / 1.466 |
| Minimum U9 IN (≥ −15.0 V) | −14.807 | −14.586 | −14.630 |
| Steepest rise (≤ 100 V/µs) | 5.088 | 12.53 | 4.899 |
| R166 damper peak / energy | 579.0 W / 2.979 mJ | 518.1 W / 2.906 mJ | 547.4 W / 2.925 mJ |
| Retained-output bound (2 s) | 5.914 V | 5.914 V | 5.914 V (1643.90 µF) |
| Convergence, C88 topology, components, cold limit, no-clamp, local-path sensitivity | pass | convergence pass, rest pass, no-clamp 3 fail, local fail | **all pass** |
| Below-envelope 0 / 0.01 Ω harness rows | fail (known) | 14 fail | 14 fail (known class, outside F9's ≥ 0.03 Ω domain) |

Scratch comparison on the stage D board, 576 cases at 0.1 µH (Simulation): two extra BAT_IN vias near C88 / C80 only,
144 fail at 10.685 V/µs; C80 moved onto the trunk, 0 fail at 8.684 V/µs. The 'near' / 'gnd' plane-pair inductance
(Inference) no longer decides the result: the bulk capacitor is on outer copper over In4 GND.

## 4. Stage D budget re-run (`m3_design/r11_stageD.py` on `5f1a7e1d…`; Calculation / Inference as stageD_analysis.md)

Unchanged (to the printed precision): fire loop 4.620493 Ω, four-stall fire 1.278004 A and BAT_IN 5.7133 V, every
fire-copper length, the EN / chatter, hold-up and PA6 figures, the USB-only draw, the rail series resistances and IPC
rises, the gate copper. Moved (DC solves, mΩ, stage D → now): BAT_IN J1 → U9.5 11.840 → 11.771; GND fire return
Q124 → J1.2 2.470 → 2.503 (inside the 5 mΩ allowance); RAW_PROTECTED U9 → U11 14.766 → 14.470, U9 → U400 23.689 →
22.733; PORT_5V3 L400 → U401 9.717 → 9.668; PORT_4V8 U401 → J410 17.488 → 17.742, → J420 19.733 → 19.951, → J440
15.112 → 15.398 (worst port drop at 1.9 A: 37.9 mV, was 37.5 mV; at the 0.561 A budget 11.2 mV). BAT_IN J1 → Q120
3.021, PORT_5V3 → U402 19.367, VLOGIC 20.456 and USB_LIMITED 58.279 mΩ unchanged. U401: 2 GND vias in pad (was 0).

## 5. Pin map and sources (D-R11-81)

EXTI lines (Measured by check_r11 K-exti on the board): 4 LOGIC_SOURCE_ST PA4 (G3), 5 BAT_FAULT_N PA5 (H3),
6 IMU_INT1 PD6 (C6), 8 VBUS_SENSE PC8 (F9), 10 USB_FAULT_N PD10 (H9), 13 CAM_FAULT_N PC13 (A2). PD5 (B6) is NC.
**Corrected (D-R11-87):** DS12110 Rev 8 gives PC2_C as a TT_a pad (Table 9 p. 67), 4.0 V absolute maximum (Table 119
p. 211) and 0 mA injection (Table 156 p. 244), so the R105-open fault (CAM_5V through R104 10 kΩ) broke the limit; it is
fixed by D-R11-86 (stageD3.md). The SYSCFG_EXTICR field layout is checked against ST's CMSIS header stm32h743xx.h
(cmsis-device-h7 commit 8f922cdc); RM0433 is still unread (Inference). The EXTI map above was superseded by D-R11-85
(IMU_INT1 on PD3, EXTI3; PD5 / PD6 carry the camera UART).

## 6. Silkscreen and the R11 harness pin map (D-R11-82, D-R11-83)

`r11_legends.tsv` refrozen from the routed board (469 rows, **0 open rows**; aid run twice, byte-identical, Measured).
Post stage: 26 legends, 51 designators shown, 165 hidden (Fab only). Placed (Measured): SWITCH F (14.80, 3.18) 90°;
J400 1:SW F (13.93, 8.80) 90°, 2:SW B (9.78, 3.00); J121 1:E1− F (2.8, 26.8), 2:E1+ F (2.8, 18.9); J1 1:BAT+ F (3.2, 16.4),
2:GND F (2.8, 8.5); IGN F, BAT B; Q120's designator B (8.27, 18.18) under its part; every SHOWN_REFS designator shown.
Not drawn (optional in the R11 legend set, no legal spot): the middle GH contacts, SERVO / RADIO / AUX, J2 rows 3–6,
`SERVO + FROM HARNESS`. Their content is here; stage E carries it into the R11 vehicle hand-off.

| Port | Pin 1 | 2 | 3 | 4 | 5 | 6 | Silkscreen on R11 |
|---|---|---|---|---|---|---|---|
| J122 servo signals (GH-5) | S1 SERVO1 | S2 SERVO2 | S3 SERVO3 | S4 SERVO4 | GND (signal) | — | J122, 1:S1, 5:GND; servo + comes from the pack-star harness, not the board |
| J9 camera (GH-6) | 5V4 CAM_5V | 5V4 CAM_5V | GND | GND | RXI (board receives: camera TX here) | TXO (board transmits) | J9, 1:5V4, 5:RXI, 6:TXO |
| J410 GPS by default (GH-4) | 4V8 PORT_4V8 | GND | TXO (to module RX) | RXI (from module TX) | — | — | J410, GPS, 1:4V8, 4:RXI |
| J420 radio by default (GH-4) | 4V8 | GND | TXO | RXI | — | — | J420, 1:4V8, 4:RXI |
| J440 AUX spare (GH-4) | 4V8 | GND | TXO | RXI | — | — | J440, 1:4V8, 4:RXI |
| J2 SWD (TC2030) | 3V3 | SWDIO | NRST | SWCLK | GND | NC | J2, 1:3V3, 2:SWDIO |
| J400 switch (GH-2) | SW BAT_SW_SOURCE | SW BAT_SW_RETURN | — | — | — | — | SWITCH, 1:SW, 2:SW (all required) |

Owner acceptance of this legend set is pending (D-R11-83).

## 7. Safety and spacing figures re-measured on `5f1a7e1d…` (Measured)

* S-8: 8 barrels and 24 inner rings; nearest foreign inner copper 1.012 mm (BAT_FAULT_N on In1–In4 to the ACT_GATE via
  (14.60, 15.90)'s inner ring), against the 1.0 mm rule; J121.1 / J121.2 holes 1.100 mm.
* PYRO gate-net spacing to 3V3 / 3V3A on every layer, fills included: PYRO1_GATE 3.106 mm (TP122.1 to the 3V3A via
  (15.05, 32.60)); PYRO1_OUT 4.370 mm (C128.1 to the 3V3A via (8.94, 37.60)); PYRO1_GATE_N outside U1's ball field
  4.085 mm (to the 3V3 via (20.80, 27.20)); inside it only the D-R11-23 exception: the 0.1 mm lane 0.200 mm from D2's
  land (and 0.300 mm from D2's 3V3 dog-bone track at (21.20, 26.80), the same lane), balls B2 / D2 0.731 mm. Copper there
  is unchanged by this pass.
* K-region, K-reference (181080 samples, 0 loose), K-power, K-loader, K-plane, K-inner: OK.

## 8. Fab, cost, stock and the gate

`m3_design/r11_fab.sh` (Measured): JLC BOM 75 lines, 204 placed parts (BOM and owner BOM byte-identical to stage D);
CPL 80 top + 119 bottom rows rebuilt from JLC footprints, worst residual 0.491 mm; paste 346 top / 321 bottom flashes
on as many pasted pads; S-4 OK; manifest bound. Live JLC, 5 boards (cost_check.json 2026-11-03T23:01:53Z,
stock_check.json 23:01:04Z): parts $56.84 + 75 × $1.53 / 5 = **$79.79 per board** against $84.41 ($4.62 under; $79.73 at
stage D, JLC price movement); fixed fees $83.96 per order; with minimum purchases $58.08 per board ordered. **Stock
short**: U9 C3662793 (stock 18, orderable −93, minimum purchase 7), U4 C51931514 (stock 4, orderable −3), U2 C780769
(stock 66, orderable −2866, minimum purchase 8); orderable = min(stockCount, canPresaleNumber), an Inference about
JLC's field (R20-BOM-01). Confirm in the cart on order day, else consign (ORDERING §8.1).

| File | SHA-256 |
|---|---|
| m3_design/r11/m3.kicad_pcb | 5f1a7e1dfcae95a3ebe06801cc74dc366aa83f477b416e25e72649f4365d2b63 |
| m3_design/r11/fab/m3_bom_jlc.csv | 90310a4ef51af42bd425507460ed1c4af12fe651b87350d5ab0c99869327e616 |
| m3_design/r11/fab/m3_cpl_jlc.csv | 63df52d46818400f032d2c70dea0c22020a5bf648de45967ef848df4dbca1466 |
| m3_design/r11/fab/m3_fab_manifest.json | e0983d94d71f6e12a78d4140dccb29614ccd15acdc874366aa11aa0ba99edc2f |
| m3_design/r11/fab/cost_check.json | 7f7197e3bdd60320ad682ef8f4e57f130b647466deb83c4e848db0b84f319ca2 |
| m3_design/r11/fab/stock_check.json | ea8bdc0480ea1d449de921a227c20e5a8cee17c9d36eaf9b2639af374beb9c5d |

`tools/check.sh` with the R11 board and fab package staged (2026-11-03, Measured): **exit 0**. R11 section: DRC 0 /
unconnected 0 / parity 0 / ERC 0; r11_sch_check OK; metadata / 3D audit OK; check_r11 full OK (K-legends, K-copper,
K-exti included); route_check r11 0 failing, 2 allowlisted, 25 unrecorded leftovers (as stage D); R11 fab manifest OK
with its content checks; test_r11_check 48 tests OK with R11_BOARD_REQUIRED. R10's gate on R10's board unchanged, OK.

## 9. Open

* Owner: accept the R11 legend set (D-R11-83); RM0433's SYSCFG_EXTICR stays unread (D-R11-87; the PC2_C limit is
  now sourced and fixed, D-R11-86); U401's thermal figure is an Inference until a first-article test (D-R11-80); stock (section 8).
* Not run: the plate model, JLC DFM on the panel, first-article checks, firmware.
