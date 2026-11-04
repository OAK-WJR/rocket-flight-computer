# R11 stage D: electrical analyses on R11's copper

Board: the C4/C5 copper at commit `c275e7b`, `m3_design/r11/m3.kicad_pcb` SHA-256 `b7e2decb…` (zones unfilled, as
the routing leaves them). Every copper figure below was computed on a scratch copy filled with `pcbnew.ZONE_FILLER`
(`893c1823…`; copper tracks and vias identical, Measured: only the fill differs). Decisions D-R11-73 … D-R11-77.

Labels (AGENTS §2.5): **Calculation** = arithmetic on CAD copper and datasheet values; **Simulation** = the numerical
hot-plug model; **Inference** = anything resting on an unmeasured or estimated input. A figure whose inputs include an
Inference is an Inference. No physical test was run.

Tools and outputs:

| File | What |
|---|---|
| `m3_design/r11_stageD.py` | runs R10's `r10_parts.power_budget` (unchanged) on the R11 board, with R11's fire copper checked against the six-layer stack-up; rail paths, DC solves, EN, hold-up, PA6 corners, gate copper, U401 pad, U4 |
| `tools/r11_dc_net.py` | dc_solve's method on all six layers (R10's `dc_solve.py` is four-layer and unchanged) |
| `tools/r11_hotplug.py` | R10's hot-plug model (`r10_hotplug.py`, unchanged) on R11's copper, six layers and the In2 BAT_IN pour |
| `m3_design/r11_binding_note.py` | the binding note generator (`--check` compares) |
| `stageD_budget.json` | every number below except hot-plug |
| `hotplug_inputs_r11.json`, `hotplug_results_r11.json` | the hot-plug extraction and its 2304-case run |
| `r11_binding_note.json` | the record-only binding note |

Run: `<KiCad python3> -I -B m3_design/r11_stageD.py FILLED --source-board m3_design/r11/m3.kicad_pcb` (about 3 min);
`<KiCad python3> -I -B tools/r11_hotplug.py --extract FILLED`, then `<python3 with numpy> -I -B tools/r11_hotplug.py`
(about 7 min). Re-run both after any copper change and after r11_post's own fill.

## 1. Stack-up (JLC06161H-3313, from the board file)

F 35 µm / pp 0.0994 / In1 15.2 µm / core 0.55 / In2 15.2 / pp 0.1088 / In3 15.2 / core 0.55 / In4 15.2 / pp 0.0994 /
B 35 µm. R10 (JLC04161H-7628): outer 35 µm, inner **30 µm**, F–In1 0.203 mm. R11's inner copper has twice R10's
sheet resistance (1.13 vs 0.57 mΩ/sq), and In2 sits 0.565 mm from In1 (R10's power plane was 1.03 mm from In1 and
0.203 from B). Outer copper is unchanged, which is why the fire budget formula carries over.

## 2. Fire budget (D-R11-75; Calculation / Inference: hot Q124 factor, FET hot R, harness, pack R are R10's inferred inputs)

All five fire paths lie on F.Cu (35 µm), one width each (checked by the script before R10's formula is used).

| Item | R10 (`a0ec075e…`) | R11 | Why it changed |
|---|---|---|---|
| PYRO1_IGN copper | 10.523 mm × 0.5, 10.343 mΩ | 6.911 mm × 0.5, 6.793 mΩ | J121 wire pad beside R134 |
| PYRO1_OUT | 7.854 mm × 0.5, 7.720 mΩ | 8.618 mm × 0.5 (incl. 0.9 mm Q124 drain entry), 8.471 mΩ | layout |
| RAW_ACT | 5.886 × 0.5, 5.785 mΩ | 6.586 × 0.5, 6.473 mΩ | layout |
| ACT_FET_S | 2.2 × 0.4, 2.703 mΩ | 6.456 × 0.5, 6.345 mΩ | Q120 / Q121 side by side with a dog-leg bar, not facing |
| BAT_IN (J1 → Q120) | 6.307 × 1.0, 3.099 mΩ | 7.767 × 1.0, 3.817 mΩ | layout |
| Copper 20 / 70 °C | 29.650 / 35.477 mΩ | 31.899 / 38.167 mΩ | sum of the above |
| Total loop | 4.617803 Ω | **4.620493 Ω** | +2.69 mΩ |
| Fire current idle / 1 / 2 / 3 / 4 stalls (7.4 V) | 1.540851 / 1.475765 / 1.410416 / 1.344761 / 1.278747 A | **1.539955 / 1.474907 / 1.409596 / 1.343979 / 1.278004 A** | loop |
| Same, typical-hot FETs | — | 1.555270 … 1.290705 A | |
| MJG J-Tek floor (0.75 A × 1.5) | 1.125 A | 1.125 A, **all cases pass** (four stalls 1.136×) | |
| Four-stall BAT_IN | 5.7132 V (quoted 5.713) | **5.7133 V** | loop |
| GND fire return (Q124 source → J1.2), allowance in the loop | 0.005 Ω allowance, not solved | **2.470 mΩ** DC solve (In1 / In4 at 15.2 µm, vias, window x 0–16, y 8–33: upper bound), inside the 5 mΩ allowance | Calculation |
| Terminal allowance 0.010 Ω | DB125 screw terminals | kept for the soldered J1 / J121 wire pads (conservative; Inference) | |

The DC solve of BAT_IN J1.1 → Q120 drain on all layers gives 3.021 mΩ (the budget keeps the 3.817 mΩ track-only
figure, the larger). R134 stays 2 Ω (2512, 2 W pulse, same part).

**Shorted igniter and watchdog guard (unchanged, no copper input; Calculation on allocations / Inference):** R134 at
70 °C ≥ 1.97109 Ω, fault 35.80 W, 0.716 J in 20 ms and 1.289 J in 36 ms against the inferred pulse curve 61.2 / 44.1 W;
watchdog 28.571–32.653 ms + 0.2 + 0.5 + 1.5 ms = **34.853 ms < 36 ms**; the gate-discharge model is RC to 0.4 V
0.678 ms + gate-charge tail 0.061 ms = 0.739 ms (R126 220 Ω, R127 1 k, R128 10 k, C126 220 nF: values unchanged; R126
is now 0402, D-R11-06). R11's gate copper: PYRO1_GATE 6.90 mm and PYRO1_GATE_N 11.77 mm, all F.Cu, **no via** (R10 had
one PYRO1_GATE via); microstrip L ≤ 1.85 / 5.30 nH, negligible against the 47–58 µs gate time constant (Calculation).

**Adiabatic rise at the 4.2 A shorted-igniter current (Inference, upper bound, no spreading):** 0.5 mm × 35 µm (every
R11 fire track) 5.7 K at 20 ms / 10.3 K at 36 ms (R10's 0.4 mm ACT_FET_S: 9.0 / 16.2 K); 1.0 mm BAT_IN 1.4 / 2.6 K. The
fire return leaves Q124's source pads on four 0.3 mm tracks (K-power fire_return): one alone would rise 16.0 / 28.7 K.

**PA6 trip-window corners (R10 rule 8; Calculation / Inference):** four stalls, healthy match 5.713 V (typical-hot
5.711 V), match shorted 5.558 / 5.552 V, match and leads shorted 5.512 / 5.503 V; R10: 5.71 / 5.55–5.56 / 5.50 V.
Unchanged to the quoted precision.

## 3. J400 / U9 EN timing and chatter (D-R11-73; Calculation / Inference: C87's 0.72 X7R allowance)

Inputs are R10's values and tolerances: R80 / R165 470 k, R81 300 k (all 1 %, now 0402, same values), C87 220 nF
(unchanged), U9 and D402 leakages. R10's model re-implemented in `en_model` reproduces every R10 figure, so it is
the same model:

| Figure | R10 | R11 |
|---|---|---|
| Single drop-out that trips U9, 6.0 / 7.4 / 8.4 V | 10.3 / 20.1 / 26.0 ms | 10.35 / 20.11 / 26.02 ms |
| At the four-stall BAT_IN | 8.07 ms at 5.713 V | 8.07 ms (8.068) at 5.7133 V |
| At 5.5 V | 6.3 ms | 6.30 ms |
| One open block per 100 ms that trips U9 (window limit) | 7.50 ms at 5.71 V, 7.63 at 5.73, 9.59 at 6.0, 5.87 at 5.5 | 7.50 / 7.63 / 9.59 / 5.87 ms |
| EN at the 7 ms pass line | 1.1295 V (5.71 V) | 1.1296 V at 5.7133 V (threshold 1.116 V) |
| The 7 ms line holds down to | 5.65 V | 5.65 V (7.03 ms) |

The F6 bench rule (under 7 ms open in every 100 ms window, U9 on throughout at 5.71 V) stands unchanged. The turn-on
delay (30–130 ms) was not re-derived; its inputs are identical (Inference by identity of inputs).

## 4. Hold-up (Calculation / Inference: constant-power allocations, C84 without a cold factor)

C84 (470 µF polymer, 300.8 µF allowance) and the load allocations are R10's, so every figure is identical:
break-to-3.8 V 0.464–0.539 ms all ports on, 1.304–1.412 ms camera off / shed; from the PA6 trip 0.103–0.164 ms and
0.291–0.430 ms. R10: the same. The open owner question (R19-REQ-07) is unchanged. The copper between C84 and U2 is
longer on R11 (VLOGIC U11 → U2 20.5 mΩ DC solve, R10's trunk track 7.0 mΩ); at the 1.294 A design current that is
a 26 mV drop the constant-power model does not include (it had no copper term on R10 either; Calculation, effect on
the hold-up not computed).

## 5. Rails: resistance and IPC-2152 (Calculation on CAD widths; IPC rise is the external / internal long-conductor fit, no plane credit: an upper bound, Inference)

Per K-power path (R10 → R11), series track resistance at R11's copper and the IPC-2152 rise of each drawn width at the
path's design current. Every R11 power path is on F.Cu or B.Cu (35 µm), so the inner 15.2 µm copper only enters
through the In2 regions (DC solves below). K-power passes on the filled board.

| Path (A) | R10: R, widest-run rise | R11: R, rise per width |
|---|---|---|
| U9 IN BAT_IN (2.9) | 17.66 mΩ; 1.0 mm F 19.2 °C, 0.3 mm entry 76.8 °C | 14.16 mΩ; 0.7 mm B 15.5 mm **29.0 °C**; 0.3 mm C88→U9.5 bar 2.0 mm 76.8 °C (D-R11-25 narrow entry) |
| U9 OUT RAW_PROTECTED (2.9) | 5.36 mΩ | 4.04 mΩ; 0.7 mm 29.0 °C; 0.3 mm bar 1.5 mm 76.8 °C (D-R11-25) |
| U401 IN PORT_5V3 (1.9) | 6.18 mΩ | 3.52 mΩ; 0.4 mm 23.7 °C; 0.25 mm pin link 0.5 mm 40.7 °C (D-R11-26) |
| U401 OUT PORT_4V8 (1.9) | 6.70 mΩ | 3.26 mΩ; 0.4 mm 23.7 °C |
| U402 IN PORT_5V3 (1.249) | 16.52 mΩ | 23.71 mΩ; 0.4 mm 10.2 °C |
| J410 / J420 / J440 feeds (1.9) | 4.52 / 5.90 / 31.00 mΩ | 1.84 mΩ each; 0.4 mm 23.7 °C |
| CAM_5V out (1.249) | 17.54 mΩ | 21.31 mΩ; 0.4 mm 10.2 °C |
| C84 hold-up VLOGIC (1.294) | 32.09 mΩ | 15.97 mΩ; 0.4 mm 11.0 °C |
| VLOGIC trunk (1.294) | 7.03 mΩ | 26.23 mΩ; 0.4 mm 11.0 °C |
| U400 OUT PORT_5V3 (1.81) | 5.47 mΩ | 2.83 mΩ; 0.4 mm 21.5 °C |
| U2 OUT 3V3 (2.0) | 11.81 mΩ | 4.58 mΩ; 0.5 mm 20.3 °C (R10 0.4 mm 26.2 °C) |

All within the 30 °C K-power basis except the recorded narrow pin entries (≤ 2 mm, the same exception class as R10).
DC solves through the In2 regions (all layers, 0.1 mm grid; Calculation): BAT_IN J1 → U9.5 11.84 mΩ; RAW_PROTECTED U9
→ U11 14.77, U9 → U400 23.69; PORT_5V3 L400 → U401 9.72, → U402 19.37; PORT_4V8 U401 → J410 17.49, J420 19.73, J440
15.11; VLOGIC U11 → U2 20.46 mΩ. Worst port drop: 1.9 A design current × 19.7 mΩ = 37 mV (the always-on ports draw
at most 0.561 A in the budget: 11 mV). The endpoint minima (camera 5.031682 V, radio 4.601504 V, GPS 4.631504 V, AUX
4.642 V) take only the harness, switch and transient allowances, as on R10; R11's board copper adds at most 0.6 mV at
the radio's 0.30 A and 25 mV at the camera's 1 A through U402's feed and CAM_5V (Calculation), not in those minima.

**USB-only power (Calculation; R10 rule stands):** path U10 0.135 + U11 0.100 + USB_LIMITED copper + 0.02 Ω. R11's
USB_LIMITED is 37.3 mm × 0.3 mm on B.Cu, 58.3 mΩ solved (R10: 63.1 mm × 0.4 mm on In2, 91.2 mΩ), path 0.3133 Ω (R10
0.3462). 1.4 W + 0.825 W draws 0.4582 A at VBUS 5.00 V (R10 0.4596) and 0.4839 A at 4.75 V (R10 0.4856), still above
U10's 0.453 A maximum limit; the 0.6 + 0.776 W allocation draws 0.280–0.295 A (R10 0.281–0.296). R10's bench rule
(full-speed / SD-logging tests on pack power, or capped clock and SD rate on USB) applies unchanged.

**U401 thermal (Inference; open item):** R10's GAP-3 figure (junction 109.2–123.9 °C at a 70 °C bay with the AUX
allowance, inferred 80–110 °C/W) rested on two filled and capped vias in U401's thermal pad. R11's U401 (F.Cu, pad 11
1.2 × 2.0 mm) has **no via in the pad**; the nearest GND vias are 1.81 / 1.82 mm away, and the inner planes are half
R10's copper. The 80–110 °C/W inference therefore does not carry over, and with only 1.1 °C of margin on R10 the
100 mA AUX allowance is **not established on R11**. Not a pyro hazard (loss of the three ports); a board-level
item for the owner: add thermal vias (GAP-3 VIPPO) or a pour, or re-derive θJA (D-R11-75).

## 6. Hot-plug (D-R11-74; Simulation / Inference)

R10's model, corners and limits on R11's extracted feed (`tools/r11_hotplug.py`). What the R11 copper changes:

* **Topology.** On R10 the C80 / C96 / C89 / C95 bank and D8 sat on the track feed ahead of C88 and U9. On R11 the
  pack reaches U9 over a B.Cu trunk (J1.1 → C88.1 → U9.5, 1.796 + 8.111 + 0.8 + 4.79 mm at 0.7 mm, then a 2.0 mm
  0.3 mm bar), and D8, C80 / C96 and the C89 / C95 damper bank hang off that trunk through two 0.6 / 0.3 mm vias at
  (7.2, 6.2) / (8.0, 6.2) and the **In2 BAT_IN pour** (0.3–19 × 0.3–16.35 mm, 202 mm² filled, 15.2 µm). R10's
  extractor refused any BAT_IN pour; the R11 variant reduces the filled pour (20 181 cells at 0.1 mm, CG 995
  iterations) to an exact DC network between its six via terminals (Kron reduction; Calculation) and gives each plane
  edge L = R · µ0 h t / ρ: h = 0.565 mm to In1 ('gnd' corners, 628 nH/Ω) or In1 ∥ In4 0.311 mm ('near' corners,
  345 nH/Ω) (Inference: plane-pair current pattern, ideal returns, no antipad correction). Plane edges between
  terminals: 0.38–32.8 mΩ.
* **Required cases: 2304 (R10's set, identical corners). Result: FAIL.** 576 of the 2304 required cases fail, every
  one on the falling-slew limit and every one at the 0.1 µH harness corners (both references, both harness
  resistances, all capacitor, TVS, damper and copper-scale corners); 3 more fail in the half-step convergence rows.
  Convergence passes (max Δ 0.0076 V/µs), the component and C88-topology checks pass, the cold IN-to-OUT limit passes.

| Figure (limit) | R10 `a0ec075e…` | R11 |
|---|---|---|
| Minimum U9 IN (≥ −15.0 V) | −14.807 V | −14.586 V (pass) |
| Steepest fall (≤ 10 V/µs) | 8.995 V/µs | **15.04 V/µs ('gnd'), 12.32 V/µs ('near'): fail** |
| Steepest fall, harness ≥ 0.5 µH | — | 3.69 V/µs (pass) |
| Steepest rise (≤ 100 V/µs) | 5.088 V/µs | 12.53 V/µs (pass) |
| R166 damper peak / energy | 579.0 W / 2.979 mJ | 518.1 W / 2.906 mJ |
| Retained-output bound (2 s) | 5.914 V at 1643.90 µF | 5.914 V at 1643.90 µF (same capacitor inventory) |
| No-clamp control | pass | 3 fail (falling slew) |
| Local-path sensitivity (0–10 nF, 0.1–10 ns edges) | pass | fail |
| Below-envelope 0 / 0.01 Ω harness | fail (known) | 14 fail (known class) |
| Passed | true | **false** |

**Why it fails, and how sure (Simulation / Inference):** with a short (0.1 µH) harness the −8.4 V step reaches U9.5
along the trunk with only C88 (100 nF) beside U9, while the 64 µF bank and D8 are behind the pour's inductance. A
sensitivity on the worst corner (scratch, not a gate run): plane-edge L × 0.55 / 0.45 / 0.4 → 12.3 / 11.6 / 11.3 V/µs
(fail); plane and via L × 0.3 → 7.9 V/µs (pass); pour open → 160 V/µs. So the result fails for any plane-pair
inductance within a factor of 2.5 of the model, and passes only if the pour plus its vias were about a third of the
modelled inductance. The minimum-voltage margin is better than R10's (−14.586 V). **This is a design issue, not fixed
here.** Remedies for the owner / layout lane: put a bulk capacitor (or C80 / C96) on the B.Cu trunk next to C88 / U9.5,
or feed U9 through the bank (R10's order), or require the installed harness ≥ 0.5 µH (R10's F9 domain is 0.1–2 µH).

## 7. IMU axis and lever arm (D-R11-76; Calculation on the CAD placement, Inference where labelled)

U4 (ISM6HG256X) on the bottom at (23.0, 20.5), rotation 180 (pad centre (23.0, 20.5)): the same signed frame as R9 /
R10. **Roll about +y_board reads −gyro_Y; forward thrust −a_Y** (R10: the same). **Lever arm to the roll axis (x 23):
x = 0.0 mm** (R10 −6.0 mm), z = −2.06 mm (U4 3D-model box centre on a 1.6 mm board, Inference, as R10; the axis datum
at x 23 on the top face is R10's sled convention, Inference for R11's sled). In the IMU frame the lever arm is
(+0.0, ·, +2.06) mm. With x = 0 the roll centripetal term on a_X is nominally zero (R10's "a_X reads negative" sign
check does not apply; the 2.06 mm z offset puts it on a_Z, Inference). check_r11 M-7 holds U4 at lever 0.0 ± 0.05 mm
(`r11_gate_data.json` imu). A bench sign check precedes flight.

## 8. Binding note (D-R11-76)

`r11_binding_note.json`, generated by `m3_design/r11_binding_note.py` from the c275e7b board (`b7e2decb…`): 100 balls
with port, net, R11 mode and R10 LQFP pin, the 51 MCU signal nets (port, ball, AF / peripheral), the board map
checked against U1's pads (0 mismatches), the U4 axis map above, R10's sources / port states / arming policy / fire
timing and its 49 firmware obligations carried verbatim as R10 text, and 19 R11 deltas naming the obligation each
changes. Record only: not an executable binding. Neither `m3_firmware/assembly_binding.py` (R1's chain, reads only
`m3_design/assembly_review`) nor `tools/check_r11.py` (its docstring drops K-binding: "R11's is a stage E record")
checks an R11 binding; no firmware was changed.

**Firmware conflict found (D-R11-77, open):** D-R11-49 put IMU_INT1 on PD5 "EXTI5", but BAT_FAULT_N is on PA5, also
EXTI line 5, and R10's rule 7 rate-limits an EXTI5 interrupt on PA5. SYSCFG_EXTICR selects one port per line
(Inference: RM0433 not re-read), so both cannot interrupt. Either is pollable (IMU data-ready at the roll-loop rate
is the one that wants an interrupt), or a re-map in a later layout pass. Other R11 binding facts: camera UART4 PB9 /
PB8 AF8, servos on TIM4_CH2 / TIM2_CH1 / TIM5_CH1 / TIM5_CH2, CAM_5V_SENSE on PC2_C (ADC3_INP0; its single-fault
voltage limit must be re-read for the _C analog pad), U5 on I2C2 PB10 / PB11, buzzer PE8.
**Superseded (D-R11-81, -85, -86, -87):** IMU_INT1 is on PD3 (EXTI3); the camera UART is USART2 on PD5 / PD6; servos 3 /
4 are TIM5_CH2 / CH3 on PA1 / PA2; PC2_C is a TT_a pad, 4.0 V absolute maximum (DS12110 Rev 8 Table 119 p. 211), 0 mA
injection (Table 156 p. 244), protected by the four-resistor divider of D-R11-86; the EXTICR layout is checked against
ST's CMSIS stm32h743xx.h (cmsis-device-h7 8f922cdc), RM0433 still unread.

## 9. What fails a limit (design issues reported, not fixed)

1. **Hot-plug falling slew at U9 IN:** 576 / 2304 required cases (all 0.1 µH harness corners), up to 15.04 V/µs
   against 10 V/µs (Simulation / Inference). R10 passed (8.995).
2. **U401 thermal floor not established:** no thermal via in U401's pad (R10's GAP-3 basis had two) (Inference).
3. **EXTI line 5 shared** by BAT_FAULT_N (PA5) and IMU_INT1 (PD5) (Inference on RM0433). Closed by D-R11-81 / -85
   (IMU_INT1 on PD3, EXTI3).

Everything else re-run here passes its R10 limit: fire floor 1.125 A at four stalls (1.278004 A), watchdog guard
34.853 < 36 ms, GND return 2.47 mΩ < 5 mΩ allowance, EN / chatter and hold-up identical, K-power IPC widths.

**Fix pass (stageD2.md, D-R11-78 … -84):** items 1–3 above are closed on board `5f1a7e1d…`: hot-plug 0 / 2304 failing,
steepest fall 8.663 V/µs (C80 on the B.Cu trunk, D-R11-79); U401.11 carries R10's two GAP-3 VIPPO vias (D-R11-80; its
thermal figure an Inference); IMU_INT1 on PD6, EXTI6 (D-R11-81). The figures above are the stage D board's.
