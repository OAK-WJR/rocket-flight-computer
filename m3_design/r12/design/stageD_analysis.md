# R12 stage D: electrical analyses on R12's copper (2026-11-05)

**Superseded for the current board by `stageE_relayout.md` §4** (the AVA re-layout, 46 × 90 mm, 46 × 88 mm since
D-R12-144, board `be81f40b…`, `66323cf0…` since R12F3-TRI-05, `db1f0999…` since R12F4-TRI-06, `68e6b650…` since the AVA polish pass D-R12-121 … -124,
`14b82d39…` (lane P) and `6e874d4e…` (lane P2) in the round-5 fix pass R12F5-TRI-01 / -06 / -21, 2026-11-06, and
`3f9579fa…` (lane P), `6a1c99e0…` (lane P3) and `f26dfef1…` (lane P4) in the round-6 fix pass D-R12-134 …
-143, 2026-11-07; R12F6-TRI-10; and `82eddc69…` in round 7, `418e5ea9…` in round 8, and current `a02a6181…` (46 × 85 mm) after round 9, D-R12-161 … -165): the hot-plug result is unchanged; the RAW_PROTECTED, VLOGIC, PORT_4V8 and 3V3 copper figures, the PA6
corners and U6's supply changed. This file records the 100 mm boards as they were.

**Final round 9 binding (`6403f0a`, D-R12-165).** Current board and source SHA-256 in `stageD_budget.json`:
`a02a618101d620b6c61e49899aaec8a8253afda4920581173efacc2417057c77`. D8/D121 part fields changed; all DC solves and lane B figures
below are unchanged. Hot-plug electrical SHA `cda2664b…`, 2304 / 2304 pass, minimum −14.255 V
(Simulation / Inference). Stage D uses the as-saved fills; lane B's refill caveat below still applies.

**Round 9 lane B (R12F9-TRI-04, owner option (b) adopted by the orchestrator; `stageD_budget.json` re-run on board
`86f015c2…`, which differs from `3ccb3a53…` only in R60 / R61's part fields, as-saved fills (K-fill-checked) with
`--source-board`, both hashes `86f015c2…`).** R60 is YAGEO RT0402BRD07100KL (C852472) and R61 RT0402BRD0710KL (C190095,
R401's line), both 0.1 % 25 ppm/K; `r12_budget.PA6_TOL` = TOL_PRECISE (0.1 %; 0.1 % + 25 ppm/K × 67 K) and the
firmware PA6 band is **0.425–0.455 V** (was 0.42–0.45 V): `pa6_corners.owner_options.band_derivation` centres the 30 mV
band in the 0.1 % drift case's room 0.4203–0.4603 V (top below the healthy four-stall VLOGIC, bottom above U9's turn-off
through D5), centre 0.440 V. Trip window 4.675–5.005 / 4.667–5.014 / 4.652–5.029 V (nominal / 0.1 % / drift). Margins
to the trip top (lower bounds): healthy **+0.084 / +0.074 / +0.059 V**; match shorted −0.067 / −0.076 / −0.092 V; match
and leads shorted −0.111 / −0.120 / −0.136 V (a shorted match still trips PA6; firmware rule 4). Trip bottom above U9's
turn-off through D5 **+0.123 / +0.114 / +0.051 V** (was +0.068 / −0.015 / −0.119 V). Hold-up from the PA6 trip,
unshed 0.487–1.853 ms at drift (was 0.382–1.980 ms), shed 1.457–3.464 ms. Every DC solve, the fire loop, EN, ports, U403
and U6 are unchanged (Calculation / Inference: DC-solve bounds, SS34 VF, allocations, 70 °C copper, the drift case).
A native ZONE_FILLER refill of the scratch copy on this KiCad did not reproduce the saved fills (hash `b9a0b051…`) and
moved the plane-dependent solves by up to 10 % (RAW_PROTECTED U9 → U403 15.67 → 14.09 mΩ); on that copper the
derivation gives 0.426–0.456 V and the adopted band still clears both limits at drift (+0.063 / +0.051 V; Inference on
fill variation). Hot-plug re-bound on `86f015c2…`: 2304 / 2304 pass, minimum −14.255 V (rows identical).

**Round 9 analyses lane (R12F9-TRI-04, -05; `stageD_budget.json` re-run on board `3ccb3a53…` (46 × 85 mm, lane L),
zone-filled scratch copy with `--source-board`, the refill reproducing the board hash).** Fire loop (4.726884 Ω,
1.24995 A at 5.72088 V), GND return (2.670 mΩ), EN, hold-up and every earlier DC solve are unchanged from lane L's run;
one solve is new, VLOGIC D5 → R60 (12.316 mΩ at 20 °C).
- **Copper at 70 °C (TRI-04).** The four-stall BAT_IN is the fire loop's 70 °C corner, so `pa6_corners`, `u400_input`
  and `u403_input` now take the J1 → U9, RAW_PROTECTED and CAM_5V copper at 70 °C too (`HOT_CU` = 1 + 0.00393 × 50 =
  1.1965), and `pa6_corners` charges U2's input current (logic + microSD write, about 0.437 A) at the VLOGIC copper
  from D5 to R60's tap, min(R(D5 → R60), R(D5 → U2)) × 1.1965 = 7.69 mΩ (3.4 mV). Margins to the PA6 trip top
  (nominal / 1 % / drift; lower bounds): healthy **+0.138 / +0.048 / −0.014 V** (lane L: +0.154 / +0.064 / +0.002);
  match shorted **−0.012 / −0.103 / −0.165 V**; match and leads shorted **−0.056 / −0.147 / −0.209 V**. Four-stall
  VLOGIC 5.088–5.288 / 4.938–5.138 / 4.894–5.094 V. At drift a healthy four-stall fire can therefore sit inside the PA6
  trip window (Calculation / Inference: DC-solve bounds, SS34 VF, allocations, the 70 °C copper temperature, drift).
  U400 VIN at four stalls **5.507 V** (5.525 V at 20 °C), 5.440 V on the 6.0 V pack; U403 VIN **5.554 V**, camera-pin
  estimate 4.91 / 5.01 V.
- **PA6 owner options (`pa6_corners.owner_options`).** With R60 / R61 at 0.1 % 25 ppm/K (YAGEO RT0402BRD07100KL C852472
  and RT0402BRD0710KL C190095) and the present 0.42–0.45 V threshold: healthy +0.130 / **+0.114 V** (1 % / drift case
  of the parts), trip bottom above U9's turn-off +0.060 / −0.003 V; with the band moved to 0.4253–0.4553 V both
  limits clear at drift by +0.055 V. With the 1 % divider no 30 mV band meets both limits at drift (room 17.6 mV).
- **Dummy-fire bound (TRI-05).** New `fire.dummy_fire`: R134 at its low end at 70 °C (1.97109 Ω at 1 %, 1.9666 Ω in the
  drift case) gives 1.5246 / **1.5260 A** and a BAT_IN − RAW_ACT bound of 0.2675 / **0.2677 V** (was 0.264 V at the
  budget's high-end R134), under the 0.4 V reject line (Calculation / Inference: hot factors, pack, converter loads,
  copper model, drift).

**Round 8 analyses lane (R12F8-TRI-06 … -10; `stageD_budget.json` re-run on board `418e5ea9…`, zone-filled scratch copy
with `--source-board`, the refill reproducing the board hash).** The fire loop (4.726884 Ω, 1.24995 A at 5.72088 V), GND
return (2.672 mΩ) and every DC solve are unchanged from lane P's run; the figures below changed with the inputs.
- **Resistor drift case (TRI-06).** The EN model (`r12_budget.en_model`, R10's model with the tolerance as a parameter;
  identical to `r11_stageD.en_model` at 1 %) and the PA6 divider now run in both of R12's cases (1 %; 1 % + 100 ppm/K
  over 67 K = ±1.67 %, the bound). EN at the four-stall 5.7209 V, 1 % / drift: single drop-out 8.13 / **7.61 ms**;
  bench-rule worst-corner limit 7.56 / **7.08 ms** (0.56 / **0.08 ms** over the 7 ms line, which still holds); the 7 ms
  line holds down to 5.647 / **5.710 V**; a single 10 ms drop-out needs 5.956 / **6.025 V** (10.35 / **9.81 ms** at
  6.0 V); turn-on 30.3–131.5 / **29.9–135.9 ms** (Calculation / Inference: C87's X7R allowances, the drift case). PA6
  trip window 4.62–4.95 V nominal ratio, 4.537–5.041 V at 1 %, **4.482–5.103 V** at drift (Calculation; drift Inference).
- **U9 RON at 45 mΩ (TRI-07)**, TI SLVSFC9C §6.5's maximum (2.7–23 V, 3 A, −40…125 °C), in every bound
  (`r12_budget.U9_RON`); it was 40 mΩ. Four-stall VLOGIC 5.112–5.312 V (healthy), 4.962–5.162 V (match shorted),
  4.918–5.118 V (match and leads shorted). Margins to the PA6 trip top (nominal ratio / 1 % / drift): healthy +0.162 /
  +0.071 / **+0.009 V**; match shorted +0.012 / −0.079 / −0.141 V; match and leads shorted −0.032 / −0.123 / −0.184 V
  (Calculation / Inference: DC-solve upper bounds on the drop, SS34 VF, allocations, drift). U400 VIN 5.541 V at four
  stalls (5.474 V on the 6.0 V pack).
- **D-R12-21's margin (TRI-06).** U9's highest turn-off BAT_IN is 4.802 V at 1 % (4.851 V at drift), 4.552 / 4.601 V
  through D5 at VF 0.25 V. The PA6 trip bottom lies **+0.068 V** above it only at the nominal ratio; with the divider
  and EN chain in the same case it is **−0.015 V (1 %)** and **−0.119 V (drift)** below it. A PA6 threshold bottom of
  0.4214 V (1 %) / 0.4311 V (drift) would be needed to restore it (`r12_windows.json` `vlogic`; Calculation /
  Inference: D5 VF, drift).
- **Hold-up from the PA6 trip (TRI-08)**, unshed + SD write: 0.467–1.718 ms nominal ratio, **0.415–1.873 ms** over the
  1 % divider, **0.382–1.980 ms** at drift; shed + SD idle 1.40–3.21 / 1.24–3.50 / 1.14–3.70 ms. From the battery break
  2.23–6.10 ms (U9 at 45 mΩ). `r12_budget.holdup()` now starts at R12's window (it used R10 / R11's 4.84–5.17 V:
  0.607–2.098 ms, wrong).
- **U403 and the camera pin (TRI-09)**, new `u403_input` (per-branch bound at U403's own resistance, 11.53 mΩ): U403 VIN
  **5.574 V** at four stalls (drop 0.1465 V); the optimistic camera-pin estimate **4.93 / 5.03 V** (200 kHz, tOFF
  310 / 220 ns; L401 → J9 9.51 mΩ, R10's 0.15 Ω harness and 0.05 V allowances). §6's 5.60 V and 4.95 / 5.05 V were the
  100 mm board's lumped figures. U400 feed drop (`u400_feed_drop`, U400 IN 50.78 mΩ plus D5's current on the two shared
  runs): **0.121 V** at the design inputs, **36.1 mV** at the budget (Calculation on CAD copper; currents Inference).
- **OVLO pin (TRI-10)**: 5.71 V × 133 k / 1133 k = **0.670 V** (0.6585–0.6822 V at 1 %), inside SLVSFC9C's 0.5–1.5 V;
  0.676 V matched no corner.

**Round 7 (D-R12-144 … -151; `stageD_budget.json` bound to `82eddc69…`, re-run by the records lane on a zone-filled
copy with `--source-board`).** The 88 mm outline and the FMEA I-5 copper moved the RAW_PROTECTED, PORT_4V8 and 3V3
solves, the PA6 corners and U6's supply; the fire loop, GND return, EN chatter and hold-up are unchanged (the figures
are in `stageE_relayout.md` §4 "Round 7" and D-R12-151). Labels: every generated figure resting on the 3V3 window
(Q124's gate drive, U6's supply, the PORT_SENSE thresholds, the cold screen) now reads "Calculation / Inference (3V3
window, D-R12-139)" (D-R12-149, R12F7-TRI-02). The EN turn-on bound now spans C87's specified range (D-R12-150,
R12F7-TRI-17; §3 below).

**Round 6 3V3 window (R12F6-TRI-03, D-R12-139; computed on board `3f9579fa…`, re-bound to `f26dfef1…`).** `r12_budget.py` now takes the 3V3 window from TI SLUSDW3A
§7.8's PFM output regulation band (−1.5 / +2.5 %, typical components over T_J; U2 is the PFM variant LMR50410XDBVR) with
the 1 % divider on top: **3.254–3.482 V initial, 3.224–3.516 V drift** (was 3.270–3.431 / 3.240–3.464 V from §7.5's
V_FB alone; Calculation; the band at R12's VIN and its stacking with the resistors are Inference). The 3V3-based figures
in the sections below (§2 Q124 VGS and PE4's load, §7 U6 VCC, §10 PORT_SENSE) are their boards' figures on the old
window. On `3f9579fa…`, again on `f26dfef1…` and on `82eddc69…` (the round-7 `stageD_budget.json` was bound to it; the same at three
decimals, margins 101.8 / 71.6 mV there), stage D gives U6 VCC
≥ 3.237 / 3.207 V at U2's 1 A (margins 102 / 72 mV over 3.135 V), Q124 VGS ≥ 2.761 V and PE4's load ≤ 3.925 mA (inside
the 4 mA VOH row); `r12_windows.json` gives the cold screen at 10.2 kΩ (`cold_screen`, R12F6-TRI-01, D-R12-140).

**Re-run on `r12-port-fix` (D-R12-83 … -85).** Board `d6e4f7ee0fc3c5d72176493717eb692316e84a21ac892437b56f649e8e76fc64`
(two builds, same hash): PORT_4V8 divider R400 47k + R404 5.1k over R401 10k 0.1 % (D-R12-83), U9 0.3 mm east and C88
on the bar line with a 0.8 mm feed (D-R12-84), C84 the reflow-rated Honor HV1E477M0810PZ and nothing owner-fitted
(D-R12-85). `stageD_budget.json` and the hot-plug files were re-run on it (the saved fill already matched a native
refill: the refilled copy has the board's own hash); the hot-plug electrical SHA is `15c76382…`. Every table below
gives this board's figures where they changed (marked **port-fix**); the rest are unchanged. §10 lists the changes. The
text that follows this paragraph describes the stage D board as it was.

Stage D board (superseded): the final stage D board `d776c5d7181e10f0ea3d16960050b63b5c5e7d61bb26074c4ea3b204b71b7161` (`m3_design/r12_build.sh`,
two builds, same hash; stageD.md), analysed through a copy refilled with `pcbnew.ZONE_FILLER` (`75557a54…`). It carries
the stage D fix pass (D-R12-78: C79, a third 22 µF damper capacitor; D-R12-79: the U9 feed through C88; the copper fixes
in §9) and D-R12-80's legend-column copper moves: J410 / J420 pin 2 reach PORT_4V8 through their 100 nF pad (C410 /
C420) and its via, J122.5's GND via at (19.9, 7.0), J122's SERVO3_OUT hop at x 22.05, J9's CAM_5V via at (33.0, 8.8)
and D402 at (10.6, 7.8). `stageD_budget.json` and the hot-plug files were re-run on this board; the hot-plug extract's
electrical SHA (`db6dfd75…`) is the fix-pass board's, so its network is unchanged. Figures that moved with D-R12-80 are
marked "final board" below; every other figure is identical to the fix-pass board's (`5a301b1b…`, scratch build). The
first run of this analysis on the stage C board `e2b005b5…` (before the fixes) is summarised in §8 / §9 for comparison.

Labels (AGENTS §2.5): **Calculation** = arithmetic on CAD copper and datasheet values; **Simulation** = the numerical
hot-plug model; **Inference** = anything resting on an unmeasured or estimated input (a figure whose inputs include an
Inference is an Inference). Nothing here is Measured on hardware.

| File | What |
|---|---|
| `m3_design/r12_stageD.py` | fire budget on R12 copper (R10 GAP-1 pack model, R12 FETs and loads), EN / chatter / turn-on, hold-up, PA6 corners, rail paths + IPC-2152, DC solves (r11_dc_net's method on four layers), U6 and port supply drop, gate copper, IMU placement → `stageD_budget.json` |
| `tools/r12_hotplug.py` | R10's hot-plug model run on R12's BAT_IN / BAT_DAMP copper with R12's parts and three damper capacitors (R10's `r10_hotplug.py` and C solver executed with asserted replacements, unedited); `--variant`, `--no-clamp-all`, `--rdamp-scale`, `--damper-scale` |
| `hotplug_inputs_r12.json`, `hotplug_results_r12.json` | extraction (electrical SHA `db6dfd75…`) and the 2304-case run |
| `hotplug_variants_r12.json` | six variant runs (2304 cases each) |
| `tools/test_r12_stageD.py` | wrapper and record self-tests (no pcbnew, no numpy) |

Run (`FILLED` = a zone-filled copy of the board):
`PYTHONHASHSEED=0 <KiCad python3> -I -B m3_design/r12_stageD.py FILLED --source-board m3_design/r12/m3.kicad_pcb`
(about 9 min; two runs give byte-identical JSON, Measured); `<KiCad python3> -I -B tools/r12_hotplug.py --extract
FILLED`, then `<python3 with numpy> -I -B tools/r12_hotplug.py` (about 2.5 min).

## 1. Stack-up (from the board file)

F 35 µm / 0.2104 mm / In1 15.2 µm / 1.065 mm core / In2 15.2 µm / … / B 35 µm; depths F 0.018, In1 0.253, In2 1.333,
B 1.569 mm. Every fire path and every power feed's narrow copper is on outer 35 µm copper, as on R10 / R11.

## 2. Fire budget (Calculation / Inference: FET hot factors, pack 0.15 Ω at 7.4 V, harness, match, converter load)

All five fire paths are F.Cu, no via (checked by the script). R12 mixes widths on one path, so the series copper is
summed per segment (R10's one-width formula is not used); routed entries into terminal pads are counted, as R10's.
The fix pass did not touch the fire paths.

| Item | R11 (`3bb83272…`) | R12 |
|---|---|---|
| PYRO1_IGN | 6.911 mm × 0.5, 6.793 mΩ | 4.597 mm × 0.8, 2.824 mΩ |
| PYRO1_OUT | 8.618 mm × 0.5, 8.471 mΩ | 8.768 mm (0.8 and 0.5 mm), 5.855 mΩ |
| RAW_ACT | 6.586 × 0.5, 6.473 mΩ | 2.828 × 0.5, 2.780 mΩ |
| ACT_FET_S | 6.456 × 0.5, 6.345 mΩ | 6.160 × 0.5, 6.054 mΩ |
| BAT_IN (J1 → Q120) | 7.767 × 1.0, 3.817 mΩ | 12.405 × 1.0, 6.096 mΩ |
| Copper 20 / 70 °C | 31.899 / 38.167 mΩ | **23.610 / 28.249 mΩ** |
| GND fire return Q124 → J1.2 (DC solve, window x 0–14.5, y 6.8–48.0) | 2.503 mΩ | **2.594 mΩ** port-fix (C88's old GND via gone from the window); 2.575 mΩ on the stage D final board (2.594 on the fix-pass board, 3.248 before the second via), inside the 5 mΩ allowance (the loop keeps 5 mΩ) |
| FETs hot (D-R12-10, Inference) | 2 × 40 + 8.2 mΩ | 2 × 73.5 mΩ (AO3401A 60 mΩ × 1.225) + 57.4 mΩ (AO3400A 48 mΩ × 1.195) |
| Converter load during the fire | 13.07 W | 12.953 W port-fix (camera 1 A at 5.691 V and ports 0.561 A at 4.938 V over 0.80, logic 1.4 W, microSD 0.825 W, D5, R92; was 12.957 W at 4.943 V) |
| **Total loop** | 4.620493 Ω | **4.726699 Ω** |
| Fire current idle / 1 / 2 / 3 / 4 stalls (7.4 V) | 1.539955 … 1.278004 A | **1.505934 / 1.442375 / 1.378562 / 1.314454 / 1.250000 A** port-fix (stage D: … 1.249978 A) |
| Four-stall BAT_IN | 5.7133 V | **5.7209 V** port-fix (5.7208 V) |
| MJG J-Tek floor 1.125 A | pass (1.136×) | **pass, 1.111× (+11.1 %)**; D-R12-10's placeholder on R11 copper was 1.2473 A |

**Shorted match (Calculation / Inference):** match shorted 2.608 A idle / 2.164 A at four stalls; match and leads
shorted 2.929 / 2.430 A. Dissipation at the worst (match and leads shorted, idle): Q120 / Q121 0.631 W each, Q124
0.492 W, R134 17.4 W, for ≤ 36 ms (the watchdog guard). Gate drive (corrected by R12F2-TRI-08, 2026-11-06: the gate
divider hangs on ACT_FET_S, the common source node, which sits I_fire × RDS(Q120) below BAT_IN during the fire; the
−4.65 V first quoted here took BAT_IN itself; corrected again by R12F5-TRI-03, 2026-11-06: BAT_IN_V is J1's terminal,
so the fire current also crosses the J1 → Q120 BAT_IN copper (6.096 mΩ at 20 °C) before Q120, and R119 / R120 tap
ACT_FET_S at Q120's source by a stub that carries no current while the fire current runs the ACT_FET_S copper
(6.054 mΩ) on to Q121's source; copper at 70 °C, × 1.1965): at the four-stall point (BAT_IN 5.7209 V, 1.250 A) Q120's
source is 5.6199 V (9.1 mV of BAT_IN copper, 91.9 mV across Q120) and Q121's 5.6108 V, so **Q120 VGS −4.569 V and Q121
VGS −4.560 V**, 0.069 / 0.060 V beyond the −4.5 V RDS(on) row (the single-node figure first given here, −4.576 V /
0.076 V, left out both copper drops; Calculation / Inference: the Q120 hot factor and the 0.1 V Q122 drop are
Inference); during a fire at BAT_IN 6.0 / 7.4 / 8.4 V Q120 −4.80 / −5.93 / −6.75 V and Q121 −4.79 / −5.92 / −6.73 V;
with the bus on before the fire (no fire current, no copper drop) −4.88 / −6.04 / −6.87 V. With a shorted match at
four stalls |VGS| is 4.39 / 4.37 V (Q120 / Q121; 4.33 / 4.32 V with the leads shorted too), below the −4.5 V row, so the shorted-match FET figures
here use an RDS(on) below the real one (a fault case; Inference). Above ±12 V only with the pack above about 14.4 V
(maximum-ratio corner: 12 / (51 / 60.8) + 0.1 = 14.41 V, assuming a 0.1 V Q122 drop; Calculation / Inference,
O-R12-10), and only while the bus is on, which is from the on-rail check until switch-off (Inference that no transient
above 14.4 V occurs while it is on, pad or flight; R12F4-TRI-03); time to −4.5 V after enable 27.4 / 14.7 / 11.4 ms at 6.0 / 7.4 / 8.4 V (C120 1 µF × 1.10 ×
1.15, no bias credit; inside the ≥ 100 ms enable wait). Q124 VGS ≥ 2.78 V (2.777 V; R12F5-TRI-05: 2.778 V took R126 /
R128 at their 1 % ends, not the drift case's ±1.67 %) at the 3V3 drift minimum less PE4's
VOH allowance (DS12110 Rev 8 Table 158: VOH ≥ VDD − 0.4 V at 4 / 8 mA; PE4's steady load, R127 1k plus R126 220R +
R128 10k, is about 3.56 mA, ≤ 3.87 mA at the 3V3 drift maximum with every resistor at its drift low end, within the 4 mA
row (R12F4-TRI-02; the 0.32 mA first given here left out R127); R126 / R128 at their drift ends (1 % + 100 ppm/K over
67 K); Calculation / Inference: drift;
R12F3-TRI-06, was 3.17 V with VOH = VDD), above the 2.5 V
RDS(on) row (VGS(th) ≤ 1.45 V); gate τ 48.4 µs. Gate copper: PYRO1_GATE_N 17.38 mm F.Cu, no via; PYRO1_GATE 7.20 mm F + 5.37 mm In2,
two vias; microstrip L ≤ 10.2 / 7.3 nH, negligible against the 48 µs gate time constant.

**Watchdog guard (carried, identical inputs; Calculation on allocations / Inference):** 28.571–32.653 ms + 0.2 + 0.5
+ 1.5 ms = 34.853 ms < 36 ms; R134 ≥ 1.97109 Ω at 70 °C, fault 35.80 W.

**Adiabatic rise at the 4.2 A shorted-igniter bound (Inference, no spreading):** 0.5 mm × 35 µm 5.74 K at 20 ms /
10.34 K at 36 ms; 0.8 mm 2.24 / 4.04 K; 1.0 mm 1.44 / 2.58 K. Q124's source (fire return) now leaves its GND pad on two
0.3 mm F.Cu tracks (0.50 and 0.71 mm) to two vias at (8.2, 42.6) and (9.2, 42.6); one track alone carrying the whole
4.2 A would rise 15.96 K at 20 ms.

## 3. J400 / U9 EN timing and chatter (Calculation / Inference: C87's 0.72 X7R allowance, leakages at their bounds)

R12 keeps R80 / R165 470 k, R81 300 k, C87 220 nF, D402 and the TPS25947 EN limits (the A variant shares the L
variant's EC table, D-R12-09), so R10's EN model (`r11_stageD.en_model`) applies unchanged; only the four-stall BAT_IN
moves (5.7208 V). Unchanged by the fix pass.

| Figure | R11 | R12 |
|---|---|---|
| Single drop-out that trips U9, 6.0 / 7.4 / 8.4 V | 10.35 / 20.11 / 26.02 ms | 10.35 / 20.11 / 26.02 ms |
| At the four-stall BAT_IN | 8.07 ms at 5.7133 V | **8.13 ms at 5.7208 V** |
| At 5.5 V | 6.30 ms | 6.30 ms |
| One open block per 100 ms that trips U9 (worst-corner limit of the bench rule) | 7.50 ms at 5.71 V | **7.56 ms at 5.7208 V** (7.48 at 5.71, 7.63 at 5.73, 9.59 at 6.0, 5.87 at 5.5) |
| EN at the 7 ms pass line (threshold 1.116 V) | 1.1296 V | 1.1311 V |
| The 7 ms line holds down to | 5.65 V | 5.647 V |
| Single 10 ms drop-out needs a pack of at least | 5.96 V | 5.956 V |

The J400 bench rule (D-R25-01: total open time < 7 ms in every sliding 100 ms window, U9 on for the whole run at the
four-stall BAT_IN) stands; its worst-corner limit on R12 is 7.56 ms, 0.56 ms over the 7 ms line. Turn-on (EN rising
1.183–1.223 V, unloaded pack 6.0–8.4 V): nominal 88 / 56 / 45 ms at 6.0 / 7.4 / 8.4 V; the bound computed here was
27–114 ms (C87 220 nF × 0.72 × 0.9 … × 1.1, 1 % resistors, leakages; Calculation / Inference). That C87 range counted
−10 % twice at the fast end and left out X7R's +15 % over temperature (R12F7-TRI-17): since D-R12-150 the bound uses
R10 D-R19-10's 0.72–1.265 × and is **30.3–131.5 ms** (Calculation / Inference: the X7R temperature and bias
allowances), close to R10's recorded 30–130 ms.

## 4. Hold-up (Calculation / Inference: constant-power allocations, D5 VF 0.25–0.45 V, C84 300.8 µF allowance, 3.8 V end)

On R12 C84 holds VLOGIC only: D5 blocks RAW_PROTECTED, so the port and camera bucks and R92 drop with the pack
(D-R12-04). Loads: unshed logic 0.6–1.4 W + microSD write 3.3 V × 0.2 A / 0.85–0.80; shed 0.62 W + microSD idle.
Unchanged by the fix pass.

| Case | Battery break (7.4 V less U9 and D5) to 3.8 V | PA6 trip to 3.8 V (×11 / with 1 % divider) |
|---|---|---|
| Unshed + SD write | **2.23–6.12 ms** | **0.47–1.72 ms** / 0.42–1.87 ms |
| Shed + SD idle | 6.68–11.43 ms | 1.40–3.21 ms / 1.24–3.50 ms |
| R11 (C84 back-fed the bucks through U11) | 0.46–0.54 ms all ports on | 0.10–0.16 ms all ports on |

The C84 → U2 copper is 47.8 mΩ (DC solve; 24 mV at 0.5 A), not in the constant-power model. The required hold-up time
is still an open owner question (R19-REQ-07).

## 5. PA6 trip window during the fire (O-R12-07; Calculation / Inference)

PA6 = VLOGIC / 11 (R60 100 k / R61 10 k); firmware threshold 0.42–0.45 V (D-R12-21) → VLOGIC trip 4.62–4.95 V with the
nominal ratio, 4.54–5.04 V with the two 1 % resistors. VLOGIC during the fire = BAT_IN less U9 (0.04 Ω, Inference) and
its copper (J1 → U9.5 11.13 mΩ, U9.6 → D5 7.38 mΩ) at the 2.26–2.34 A converter current, less D5 (0.25–0.45 V):

| Four-stall case | BAT_IN | VLOGIC | Margin to the trip top (×11 / with tolerance) |
|---|---|---|---|
| Healthy match | 5.721 V | 5.138–5.338 V | +0.188 / +0.097 V |
| Match shorted | 5.575 V | 4.989–5.189 V | +0.039 / **−0.052 V** |
| Match and leads shorted | 5.532 V | 4.945–5.145 V | **−0.005 / −0.096 V** |

(R12F3-TRI-09: this table charges the whole converter current at U9.6 → D5's resistance, including the camera buck's
share, which leaves the RAW island nearer U9; so the drop is an upper bound and the margins lower bounds. The current
board's figures, with each branch at its shared resistance, are in `stageE_relayout.md` §4.)

So with D5 at its 0.45 V corner, a fire into a shorted match at four stalls can take VLOGIC into PA6's trip band
(firmware rule 8's load shed during a fire). Not a fire-path hazard (the fire current is unchanged), but the firmware
must not treat a PA6 trip during the 20 ms pulse as a battery loss (firmware item, O-R12-07 / -17).

## 6. Rails: resistance and IPC-2152 (Calculation on CAD widths; IPC rise is the long-conductor fit, no plane credit: an upper bound, Inference)

Paths are `check_r10.path_graph` between R12's terminals (end = the path's first vias where none is named), at R10's
design currents by function. Since R12F2-TRI-06 / -07 (2026-11-06, the 90 mm board; `stageE_relayout.md` §4) the
RAW_PROTECTED load paths end at the vias joined to the In2 RAW_PROTECTED island, U400 IN starts at VIN (pin 3) only (its
EN pin 5 is tied to VIN by a stub that carries no load current), and a track on more than one load path is rated at the
summed current (`stageD_budget.json` `rails_shared`). The 100 mm figures below predate that and are kept as recorded.

| Path (A) | Series R | Widths: length, rise | Vias |
|---|---|---|---|
| U9 IN BAT_IN J1 → U9.5 (2.9) | **7.55 mΩ port-fix** (10.23) | **port-fix: 0.8 mm 9.69 mm 24.9 °C (C96.1 → C88.1 1.3 mm included); 0.4 mm C88.1 → U9.5 1.3 mm, 55.2 °C, the pin entry (0.53 mm outside pads)**; stage D: 0.4 mm C96.1 → C88.1 → U9.5 4.13 mm 55.2 °C | 0 |
| U9 OUT RAW_PROTECTED (2.9) | **4.22 mΩ port-fix** (5.57) | **port-fix: 0.3 mm 1.6 mm (bar to 0.4 mm past it) 76.8 °C, 0.8 mm 0.82 mm 24.9 °C into C82.1, 0.45 mm via stubs 1.0 mm 48.2 °C (each carries about half): only pin-entry lengths over 30 °C**; stage D: 0.3 mm 3.4 mm | **2** (20.6, 15.0) / (20.6, 16.2) |
| U400 IN (2.05, port 1.9 A at 4.938 V / 0.80 from 5.71 V) | 1.64 mΩ | 0.3 mm pin entry 1.0 mm 38.5 °C | 2 |
| U403 IN (1.56) | 0.82 mΩ | 0.3 mm 0.5 mm 22.1 °C | 1 |
| D5 IN (1.294) | 1.64 mΩ | 0.3 mm 1.0 mm 15.3 °C | 2 |
| VLOGIC D5 → U2 (1.294) | 9.87 mΩ | 0.4 mm F 3.92 + B 4.11 mm 11.0 °C | 2 |
| C84 hold-up (1.294) | 49.59 mΩ | 0.5 mm 43.3 mm 8.5 °C, 0.4 mm 5.8 mm 11.0 °C | 0 |
| U400 OUT PORT_4V8 (1.9) | 100.66 mΩ | trunk 0.5 mm F 1.9 + B 72.8 mm 18.3 °C; the 0.3 mm B 16.6 mm segment (33.0 °C) is R400's sense stub, which carries no load current | 3 |
| J410 / J420 / J440 feeds (1.9) | 3.11 / 3.11 / 0.98 mΩ (final board) | J410 / J420: 0.3 mm 1.9 mm, pin 2 → C410.1 / C420.1 → via (D-R12-80), 33.0 °C at R10's 1.9 A design current, negligible at the 0.561 A budget; J440: 0.3 mm pin entry 0.6 mm 33.0 °C | 1 each |
| CAM_5V L401 → J9 (1.249) | 9.34 mΩ | 0.6 / 0.5 / 0.45 mm, ≤ 8.9 °C | 0 |
| U2 OUT 3V3 (2.0) | 1.64 mΩ | 0.3 mm pin entry 1.0 mm 36.5 °C | 2 |

DC solves (all four layers, 0.1 mm grid, filled zones; Calculation), **port-fix**: BAT_IN J1 → U9.5 8.193 mΩ (11.133),
J1 → Q120 5.414; RAW_PROTECTED U9 → U400 5.791, → U403 7.445, → D5 5.328 (8.104 / 8.957 / 7.553: U9 0.3 mm nearer);
VLOGIC D5 → U2 13.873, C84 → U2 47.816, D6 → U2 30.509; PORT_4V8 L400 → J410 73.564, → J420 74.769, → J440 69.569,
→ R400 36.975; CAM_5V L401 → J9 9.506; 3V3 L1 → U6 6.762, L1 → R14 5.347, R14 → U6 8.022 (the moved vias change the In2
3V3 pour); GND Q124 → J1.2 2.594 mΩ.

**Port supply, port-fix (D-R12-83; Calculation; the LR900-F's 4.5 V floor and 5.0 V top and the load allocation are
Inference).** Regulator window 4.603–4.938 V initial, 4.571–4.972 V drift (R401 0.1 % 25 ppm/K). At the 0.561 A budget,
same bound: J410 ≥ 4.562 / 4.529 V, **J420 ≥ 4.561 / 4.529 V (+61 / +29 mV over 4.5 V)**, J440 ≥ 4.564 / 4.532 V
(initial / drift); no-load top 4.938 / 4.972 V, ≤ 5.0 V (the HGLRC M100 Mini's 3.3–5 V, hglrc.com, read 2026-11-05).
`port_supply.all_ports_inside_4V5_5V0_at_0A561` is true. At R10's 1.9 A design current (not the budget) J420 is
4.461 / 4.429 V. **O-R12-16 and O-R12-26 are closed.** Stage D's figures, superseded: U400 regulates at R400.1,
whose sense stub joins the east-edge trunk 5 mm from L400; the ports are 70 mm forward. Bound (maximum principle: no
node lies outside the source-sink potentials; mutual ≤ driving-point resistance): drop to port k ≤ R(L400 → port k) ×
I. At the always-on budget 0.561 A (final board): ≤ 42.0 mV at J420 → **4.497 V initial (2.6 mV under the LR900's 4.5 V),
4.447 V drift**; J410 4.498 / 4.448 V, J440 4.500 / 4.450 V; the bound counts about 8 mΩ of trunk before the sense tap, so the estimate is about 36 mV → 4.503 V initial.
At R10's 1.9 A: 4.40 / 4.35 V. The copper adds 36–41 mV to O-R12-16's drift-bound shortfall (was 11 mV); harness drop
not included. Owner item.

**CAM_5V (Calculation; drift and harness Inference):** only while U403 VIN ≥ VO / 0.75 (TI SLVSD90B §7.3).
9.5 mΩ, 9.5 mV at 1 A: 5.212 V initial / 5.152 V drift at J9 before the harness (camera 5.0 V minimum;
with R10's 0.15 Ω harness and 0.05 V transient allowances the drift corner is 4.95 V, Inference).

**Four-stall dropout (R12F1-TRI-17, Calculation / Inference).** TI SLVSD90B §6.4.1 allows frequency foldback
below 7 V to about 200 kHz; minimum off-time is 220 ns typical / 310 ns maximum (§5.5). The corresponding duty
ceilings are about 95.6 / 93.8 %. U403 VIN ≈ 5.720875 − 0.121180 = 5.599695 V (`stageD_budget.json`, healthy
four-stall case). Even the initial 5.221 V floor needs about 93.2 % lossless or 94.9 % with the typical 95 mΩ
high-side switch at 1 A: it is not a supported minimum at this input. An optimistic estimate at the camera pins,
using R10's allowances above, is D × (5.599695 − 1 × 0.095) − 1 × 0.009506 − 1 × 0.15 − 0.05 ≈ **4.95 / 5.05 V**
for maximum / typical off-time. This omits low-side, inductor and contact losses and uses an approximate foldback
frequency and typical switch resistance: it is not a guaranteed window or proof of camera failure. Measure the
camera supply under the actual load, harness and low-input transients. Source: [TI SLVSD90B](https://www.ti.com/lit/ds/symlink/tps563208.pdf).

## 7. U6 (FXLS90322) supply, O-R12-22 (Calculation / Inference: drift case and load currents Inference)

U2 regulates at R14.1. Bound on R14.1 → U6 VCC (pins 1, 13, 15, 16): (R(L1 → U6) + R(L1 → R14)) × I_3V3 =
(7.205 + 5.441) mΩ × I (final board). At U2's 1 A rating: 12.6 mV → **VCC ≥ 3.258 V initial / 3.227 V drift, margin
123 / 92 mV over 3.135 V** (port-fix: (6.762 + 5.347) mΩ, 12.1 mV → ≥ 3.258 / 3.228 V, margin 123 / 93 mV); at a 0.5 A 3V3 allocation 6.3 mV (99 mV drift margin); U6's own 6 mA through R14 → U6
(8.7 mΩ) 0.05 mV.
O-R12-22 closes as a calculation; load steps at U6 are an Inference (bench).

IMU placement (Calculation on CAD): U4 at (23.0, 31.6), top, rotation 180, lever arm x = 0.000 mm (D-R12-54 map);
U6 at (27.5, 40.5), lever arm x = +4.5 mm, which puts the roll centripetal term on channel 0 (lateral), not on the
axial channel 1.

## 8. Hot-plug (D-R12-09, -78, -79; Simulation / Inference)

R10's model, corners (2304) and limits on R12's extracted feed (`tools/r12_hotplug.py`): all BAT_IN / BAT_DAMP copper is
F.Cu track (no pour), so R10's four-layer extractor applies; R80's BAT_IN pad joins the R167 bleed branch (every
BAT_IN / BAT_DAMP pad is an ideal join). C79 is modelled exactly as C89 / C95 (same maker C(V) curve, factors and
'damper' corner; the R10 sources are executed with asserted replacements: three damper rows, CMAX 7). D8 SMAJ12CA keeps
R10's TVS model (its 0.2 Ω slope is stiffer than SMAJ12CA's 0.26 Ω, Inference; the no-clamp run bounds it).
Network (12 edges; port-fix): J1.1 → C80 (6.97 mm × 1.0); J1.1 → C89.1 (4.99 mm × 0.8) → D8 / C95.1 → C96.1 (2.2 mm ×
0.8) → C88.1 (1.3 mm × 0.8) → U9.5 (1.3 mm × 0.4, 1.60 mΩ, 0.42 nH; stage D: C88.1 1.1 mm × 0.4, then 3.03 mm × 0.4,
3.72 mΩ, 0.99 nH); C95.1 → C79.1 (3.70 mm × 0.8) and C95.2 → C79.2 (3.84 mm
× 0.8); R167 10.1 mm × 0.4 off C96.1 through R80.1.

| Figure (limit) | R11 `3bb83272…` | R12 before the fixes (`e2b005b5…`) | **R12 stage D (`5a301b1b…`); port-fix (`d6e4f7ee…`) where it differs** |
|---|---|---|---|
| Required cases failing | 0 / 2304 | 8 / 2304 | **0 / 2304** |
| Minimum U9 IN (≥ −15.0 V) | −14.630 V | −15.097 V | **−14.255 V** (0.1 µH) |
| Minimum by harness 0.1 / 0.5 / 1 / 2 µH | — | −14.347 / −14.554 / −14.081 / −15.097 V | −14.255 / −14.147 / −13.388 / −12.692 V |
| Steepest fall (≤ 10 V/µs) | 8.663 | 9.286 | **9.251 V/µs** (0.1 µH); port-fix 9.254 V/µs |
| Steepest rise (≤ 100 V/µs) | 4.899 | 5.387 | 5.402 V/µs |
| R166 damper peak / energy | 547.4 W / 2.925 mJ | 618.7 W / 3.053 mJ | 643.0 W / 4.186 mJ |
| C88 topology (feed passes C88 before U9; local path ≤ 4 mm, 5 mΩ, 2.6 nH) | pass | fail | **pass** |
| Cold IN-to-OUT limit | pass | fail | **pass** |
| Retained-output bound (2 s) | 5.914 V at 1643.90 µF | 5.534 V | 5.585 V at 1419.8 µF |
| Convergence (half step) | pass | pass | pass (max Δ 3.0 mV/µs) |
| No-clamp control / local-path sensitivity | pass / pass | 1 fail / pass | **pass / pass** |
| Below-envelope 0 / 0.01 Ω harness rows | 14 fail (known) | 14 fail | 12 fail (known class, outside F9's ≥ 0.03 Ω) |
| Passed | true | false | **true** |

**Keep or drop R166 (D-R12-09): keep R166 and the damper capacitors.** Variant runs on this board, 2304 cases each
(`hotplug_variants_r12.json`; Simulation / Inference):

| Variant | Failing | Minimum | Steepest fall |
|---|---|---|---|
| As built (R166 0.36 Ω, C89 + C95 + C79 22 µF) | 0 | −14.255 V | 9.25 V/µs |
| R166 shorted (the capacitors straight to GND) | **1164** | −20.83 V | 4.81 |
| No damper (R166, C89, C95, C79 removed) | **1920** | −20.26 V | 16.66 |
| R166 × 0.75 / × 1.3 | 0 / 112 | −13.96 / −15.48 V | 8.11 / 10.15 |
| No TVS in any case (D8 VBR 1000 V) | 0 | −14.255 V | 9.25 |
| Damper capacitance × 2/3 (44 µF in all, the pre-C79 value, on the new copper) | 8 | −15.081 V | 9.33 |

Dropping R166 (and its Extended feeder fee) fails 1164 cases; the third capacitor (C79) is what moves the 2 µH corner
from −15.08 V to −12.69 V; with it the result no longer depends on D8 (0 failing with no clamp at all).

## 9. Findings and status

Fixed by the stage D fix pass (D-R12-78 / -79 and the copper changes; Measured on the CAD, figures above):
1. **Hot-plug** (was 8 / 2304 failing at −15.10 V, C88 topology and cold limit failing): C79 added, the U9 feed drawn
   through C88.1; now 0 / 2304, every check passes.
2. **Fire return single via:** Q124.2 now has two 0.3 mm tracks to two GND vias, (8.2, 42.6) and (9.2, 42.6); GND
   return 2.594 mΩ on the fix-pass board, 2.575 mΩ on the final board.
3. **U9 OUT single via:** a second via at (20.6, 15.0) joins U9.6 to the In2 RAW_PROTECTED island.
4. **Duplicate RAW_PROTECTED track** (20.1, 16.2) → (20.6, 16.2): removed.
5. **BAT_IN C95.1 → C96.1:** widened from 0.4 to 0.8 mm.

D-R12-80 (legend columns) then moved five copper items (header); the re-run on the final board changed only the figures
marked "final board" above, none across a limit except PORT_4V8 at the ports, already under 4.5 V (item 7).

Still open at stage D (6 and 7 closed on `r12-port-fix`, §10):
6. **(closed by D-R12-84) BAT_IN C96.1 → C88.1 → U9.5 at 0.4 mm for 4.13 mm** (D-R12-79's route): 55.2 °C at R10's 2.9 A design current,
   about 36 °C at the 2.34 A fire-time converter current (IPC upper bound, no plane credit; Inference), above the 30 °C
   basis and longer than the 2 mm pin-entry class. Its 3.7 mΩ is inside R10's C88 local-path bound (5 mΩ). A 0.6 mm
   run, if it fits, would bring the 2.9 A rise to about 35 °C (Calculation on the IPC fit).
7. **(closed by D-R12-83) PORT_4V8 at the ports (final board):** 4.497–4.500 V initial bound and 4.447–4.450 V drift at the 0.561 A budget
   (J420 lowest), against the LR900's 4.5 V (Calculation / Inference); the 75 mm east-edge feed (0.5 mm B.Cu) is about
   70–75 mΩ. Owner item (O-R12-16, O-R12-26).
8. **PA6 during a fire into a shorted match:** VLOGIC can reach the trip band (§5; firmware, O-R12-07).

Everything else re-run here passes: fire floor at four stalls 1.249978 A (+11.1 %), GND return 2.575 mΩ < 5 mΩ, watchdog
guard 34.853 < 36 ms, EN / chatter (7 ms line holds to 5.647 V), hold-up 2.2–6.1 ms from a break, U6 ≥ 3.227 V (final
board), the hot-plug model and all its checks (re-run on the final board: 0 / 2304, −14.255 V, 9.251 V/µs).

## 10. Port-fix re-run (D-R12-83 … -85, board `d6e4f7ee…`)

Every analysis above was re-run once on `d6e4f7ee…` (`stageD_budget.json`, about 9.5 min; hot-plug inputs electrical SHA
`15c76382…`, the 2304-case results and the six variants re-run on them). What changed:

| Item | Stage D (`d776c5d7…`) | Port-fix (`d6e4f7ee…`) | Label |
|---|---|---|---|
| PORT_4V8 window at the regulator | 4.539–4.943 V initial, 4.489–4.999 V drift | **4.603–4.938 V, 4.571–4.972 V** | Calculation; drift Inference |
| Ports under 0.561 A (J420 lowest) | ≥ 4.497 / 4.447 V | **≥ 4.561 / 4.529 V** (J410 4.562 / 4.529, J440 4.564 / 4.532) | Calculation / Inference |
| Ports at no load (ceiling 5.0 V) | ≤ 4.943 / 4.999 V | **≤ 4.938 / 4.972 V** | Calculation / Inference |
| PA4 PORT_SENSE | 3.07–3.38 V initial, 3.02–3.44 V drift | 3.11–3.38 V, 3.08–3.42 V | Calculation; drift Inference |
| U9 IN path (2.9 A) | 0.4 mm 4.13 mm at 55.2 °C (not pin-entry class) | **0.8 mm everywhere (24.9 °C) but the 1.3 mm 0.4 mm pin entry**; 7.55 mΩ | Calculation / Inference (IPC upper bound) |
| U9 OUT path (2.9 A) | 0.3 mm 3.4 mm, 76.8 °C | 0.3 mm 1.6 mm (pin entry), 0.8 mm 0.82 mm 24.9 °C, 0.45 mm via stubs 1.0 mm; 4.22 mΩ | Calculation / Inference |
| C88 local path | 3.03 mm, 3.72 mΩ, 0.99 nH | 1.3 mm, 1.60 mΩ, 0.42 nH | Calculation (extractor) |
| Hot-plug | 0 / 2304, −14.255 V, 9.251 V/µs | 0 / 2304, −14.255 V, 9.254 V/µs, rise 5.402 V/µs, R166 643.0 W / 4.186 mJ; every check passes; variants unchanged (R166 shorted 1164, no damper 1920, × 1.3 112, 2/3 damper 8 failing) | Simulation / Inference |
| Fire, four stalls | 1.249978 A at 5.7208 V | 1.250000 A at 5.7209 V (+11.1 %); loop 4.726699 Ω unchanged | Calculation / Inference |
| GND return Q124 → J1.2 | 2.575 mΩ | 2.594 mΩ (< 5 mΩ) | Calculation |
| BAT_IN J1 → U9.5 / RAW U9 → U400 / U403 / D5 | 11.133 / 8.104 / 8.957 / 7.553 mΩ | 8.193 / 5.791 / 7.445 / 5.328 mΩ | Calculation |
| PA6 margin, match and leads shorted (×11 / with tolerance) | −0.005 / −0.096 V | +0.007 / −0.084 V (match shorted +0.051 / −0.040; healthy +0.200 / +0.109) | Calculation / Inference |
| U6 VCC at U2's 1 A | ≥ 3.258 / 3.227 V | ≥ 3.258 / 3.228 V | Calculation / Inference: drift case and load currents Inference |
| EN single drop-out / bench-rule limit | 8.13 / 7.56 ms | 8.13 / 7.56 ms | Calculation / Inference |
| Hold-up | 2.23–6.12 ms from a break | unchanged (C84's 470 µF ±20 % and 300.8 µF allowance kept) | Calculation / Inference |

Still open: item 8 (PA6 during a fire into a shorted match, firmware O-R12-07).
