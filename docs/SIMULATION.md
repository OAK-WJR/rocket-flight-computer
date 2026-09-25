# Rocket Flight Computer v1 — SPICE Simulation Report (partial: 5 of 9 cases delivered)

> Scope note: these simulations were run on the legacy two-board design (M1 power/actuator, M2 MCU/sensors). The pyro, servo, hold-up and buzzer circuits carry over to the single-board M3, so the results still apply to those circuits. The SPICE decks, run scripts and waveform plots were produced locally (ngspice-46) and are **not** included in this repository; every number below is quoted from the recorded results, not re-derived.

---

## 0. What this is, and where its credibility ends

- **Source**: the JSON output of the `rocket-spice-sim` workflow. Every number in this document is taken verbatim from `result.cases[*].results[*]` and `summary` in that JSON. Two exceptions, each marked where used: §6.4's four objections come from the reviewer's own notes file (the JSON kept only the count and a truncated first objection), and §7's `check1.py` numbers come from running that script.
- **Scale**: 9 cases, 21 agents. The session quota ran out in the Verify phase; the report agent never ran, and this document replaces it. **5 cases delivered data, 111 quantified results in total** (21 / 27 / 17 / 25 / 21); the other 4 cases produced nothing (§8).
- **Verdict counts** (111): PASS 44, FAIL 24, INFO 41, and 2 split verdicts (PASS/FAIL by brown-out duration in the same row).
- **"confirmed" in the logs does not mean "reviewed"**: each case had two adversarial reviewers (a `parameters` view and a `physics` view). Of 10 reviewers **only one returned a verdict** (`camera_uart_injection:parameters`: **REFUTED**, 4 objections); the other 9 died on the quota. So `confirmed (0 objections)` for `m1_load_switch`, `vlogic_holdup`, `buzzer_drive` and `servo_line_fault` really means **"nobody had time to object"**. This document therefore says "the simulation gives" for those cases, never "verified". The only case genuinely reviewed was **refuted on the spot**, and `servo_line_fault`'s reviewer left a real objection on disk before dying (§5.5).

---

## 1. Overall verdict

| Case | Delivered | Results | PASS / FAIL / INFO | Review status | One-line conclusion |
|---|---|---|---|---|---|
| `m1_load_switch` | Yes | 21 | 15 / 0 / 6 | Unreviewed | Passes at all three voltage corners and device corners; but check1.py's three Q2 numbers (18.1 mJ / 288 µs / 63 W) have the wrong mechanism (§7) |
| `vlogic_holdup` | Yes | 27 | 6 / 8 / 11 (+2 split) | Unreviewed | **Hold-up does not hold at flight corners**: only 3.09 ms at 6.0 V / 0.5 A (2.53 ms with −20 % capacitance); 20 ms and 50 ms brown-outs reset at every corner; VBUS back-feed of 6.08–6.22 V confirms CIRCUIT_REVIEW §3.2 |
| `buzzer_drive` | Yes | 17 | 6 / 2 / 9 | Unreviewed | D6 is mandatory (105 V on the drain without it; modelled as a 30 V avalanche clamp, 63.0 mW of repetitive avalanche with no EAS/IAS rating in AO3400A Rev 3.1); coil inductance only bounded below (≥ 1.29 mH); for L ≥ 4 mH the coil does not reset — an open risk |
| `servo_line_fault` | Yes | 25 | 7 / 7 / 11 | Unreviewed | **Pin driven low + 8.4 V chafe exceeds the 20 mA absolute maximum at every voltage corner** (23.7–38.2 mA); R24 130–320 mW against 125 mW; the SRV05-4 carries 0.00 mA in that state and does nothing |
| `camera_uart_injection` | Yes | 21 | 10 / 7 / 4 | **REFUTED, 4 objections; repair never ran** | R65 470R 0603 dissipates 117–134 mW in an 8.4 V short, over its 100 mW rating; positive injection into RAW is non-compliant with IINJ +0 mA at any series resistance |
| `m1_pyro_channel` | **No** | 0 | — | — | No data (§8) |
| `sense_dividers_adc` | **No** | 0 | — | — | No data |
| `3v3a_lc_filter` | **No** | 0 | — | — | No data |
| `pullpin_nrst_debounce` | **No** | 0 | — | — | No data |

---

## 2. `m1_load_switch` — battery load switch (Q1/Q2 AON6403, back-to-back common source)

**Brief**: the arming switch closes at t = 0 with RAW loaded by C1 + C2 + C3 and the M2 side (D2 → C4 470 µF); report inrush peak, gate ramp, time for RAW to reach 95 %, linear-region FET energy and peak power, and compare with check1.py's 18.1 mJ / 288 µs / 63 W; a 7.5 A servo-stall step (100 µs edge) with 20 mΩ of wiring; battery reversal at −8.4 V.

**Model**: battery EMF + 40 mΩ internal resistance (corners 20/80 mΩ) + 100 nH lead + 20 mΩ wiring; bidirectional SMBJ12CA; Q1/Q2 AON6403 subcircuit (Rg 2 Ω, level-1 MOS VTO −2.1 V, explicit Cgs/Cgd, Cds 2 nF, body diode BV 30 V); R1 100k / R2 10k gate divider; R51 0R cut link; external switch Ron 50 mΩ; C1 470 µF (25 mΩ) + C2/C3 22 µF; M2 side via R50 → D2 SS34 → C4 470 µF + C6/C7 22 µF, buck as a constant-power load.

| # | Quantity | Result | Limit | Verdict |
|---|---|---|---|---|
| 1 | Q2 inrush peak, typical, Rpack 40 mΩ + 20 mΩ wiring, M1 + M2 load | 33.2 A @ 6.0 V (peak 187 µs after closing) / 45.8 A @ 7.4 V (148 µs) / 54.8 A @ 8.4 V (130 µs) | IDM −280 A | PASS |
| 2 | Q2 inrush, worst peak-current corner @ 8.4 V (Vth min −1.2 V, Ciss −20 %, Rpack 20 mΩ, no wiring R, L 20 nH) | 99.1 A (84 µs); I²t 0.46 A²s | IDM −280 A (2.8×) | PASS |
| 3 | D2 SS34 inrush RAW_IF → C4, typical / worst | 16.2 / 22.1 / 26.3 A @ 6.0/7.4/8.4 V; worst 45.6 A; I²t 0.03–0.11 A²s | IFSM 80 A (I²t ≈ 26.6 A²s) | PASS |
| 4 | Gate ramp @ 8.4 V: Vgs to −1.2 / −2.1 / −4.5 V / 90 % | 31 / 54 / 260 / 530 µs; ~80 µs plateau at −2.7…−2.9 V (Miller + FET_S sagging under IR drop); final −5.44 / −6.72 / −7.63 V; equivalent τ ≈ 284 µs (pure RC 168 µs) | Vgs ±20 V; RDS(on) spec point −4.5 V | PASS |
| 5 | Time for RAW to reach 95 % Vbat (M1 + M2); M1 only | 389 / 350 / 332 µs @ 6.0/7.4/8.4 V; 217 µs M1 only; VLOGIC 95 %: 428/386/367 µs | check1.py estimate 288 µs | INFO |
| 6 | Q2 linear-region energy | 8.07 mJ typical @ 8.4 V (7.2 mJ while Vds > 0.5 V; 4.99 mJ @ 6.0 V, 6.69 mJ @ 7.4 V); peak-current corner 10.5 mJ; slow corner 7.7 mJ; without M2 load 5.5 mJ | check1.py 18.1 mJ / limit 50 mJ | PASS |
| 7 | Q2 peak power and equivalent pulse width | 64 / 104 / 138 W, FWHM 73/59/53 µs; worst 257 W / 36 µs | AON6403 Fig. 10 single-pulse ≈ 350–500 W @ 50–100 µs (graph read) → ≥ 2×; check1.py assumed 63 W average | PASS |
| 8 | Q2 junction rise | 7.5 / 10.9 / 13.7 °C typical; worst 20.7 °C | Tj max 150 °C | PASS |
| 9 | Q1 dissipation | 0.97 / 1.39 / 1.72 mJ, peak 9.8 / 16.4 / 22 W (worst 2.6 mJ / 58 W) | — | PASS |
| 10 | Energy split @ 8.4 V (battery EMF delivers 66.6 mJ) | Capacitor storage 34.6 mJ; battery R + wiring 15.6 mJ; Q2 8.1 mJ; D2 2.9 mJ; Q1 1.7 mJ. Charge through Q2 7.9 mC (4.0 mC with M1 only) | check1.py assumed all 0.5CV² = 18.1 mJ in Q2 | INFO |
| 11 | 7.5 A servo-stall step: RAW dip, typical | 0.504 / 0.496 / 0.493 V (66 mΩ loop); RAW minimum 5.49 / 6.90 / 7.90 V; no overshoot or ringing | — | INFO |
| 12 | Worst corner @ 6.0 V (Rds max, cold battery 80 mΩ) | 0.82 V dip, RAW minimum 5.17 V | — | INFO |
| 13 | VLOGIC minimum vs AP63203 UVLO | 5.14 / 6.56 / 7.56 V typical; worst 4.82 V (1.12 V above UVLO rising max 3.70 V) | UVLO rising 3.30/3.50/3.70 V | PASS |
| 14 | Settling / recovery after the step | 28–50 µs (worst 143 µs); release 81–119 µs (worst 279 µs); no overshoot | — | PASS |
| 15 | Loaded Vgs and Rds(on) | −7.20 / −6.29 / −5.01 V at 7.5 A; worst corner −4.73 V, Rds 4.40 mΩ; 0.16–0.26 W per FET | RDS(on) spec point −4.5 V (only 0.23 V left at worst corner) | PASS |
| 16 | Reverse −8.4 V: current through the switch | 5.4 µA (switch closed) / 5.1 µA (open); ~1.7 µA at 25 °C spec | ≈ 0 | PASS |
| 17 | Reverse: Q1 Vds / Vgs | Vds(Q1) −7.97 V / −7.40 V, hot-plug transient −9.1 V; Vgs +0.39 V / 0.0001 V | VDS −30 V; VGS ±20 V | PASS |
| 18 | Reverse: D1 SMBJ12CA | −8.4 V DC, −8.56 V ringing; 0.7 µA leakage | VRWM 12 V | PASS |
| 19 | Reverse: negative voltage on RAW / VLOGIC / C1 | −0.12 V (closed) / −0.65 V (open, hot-leakage corner; ~−0.15 V at 25 °C) | AP63203 VIN min −0.3 V (exceeded only at the hot/open corner, ≤ 5 µA available) | INFO |
| 20 | Reverse hot-plug gate coupling | Vgs momentarily −1.47 V, below −1.2 V for 54 µs (closed) / 398 µs (open); a Vth-min part would conduct < 0.1 A for < 0.4 ms | Vgs(th) min −1.2 V | INFO |
| 21 | Forward hot-plug with the switch open: FETs must stay off | Vgs minimum −0.57 V, returning to zero with τ ≈ 1.85 ms; RAW ≤ 0.4 mV | Vgs(th) min −1.2 V (0.63 V margin) | PASS |

**Verdict**: passes at every voltage and device corner (15 PASS, 6 INFO, 0 FAIL). Three new facts for the documentation: **loaded gate voltage falls to −4.73 V worst case, only 0.23 V from the −4.5 V specification point**; **reversal pulls RAW/VLOGIC to −0.12 V (closed) / −0.65 V (open, hot leakage)**; **reverse hot-plug couples the gate to −1.47 V**. Conflicts with earlier documents: the frozen document's "99 A / τ 83 µs / FET 2.3 mJ" and CIRCUIT_REVIEW's "90 A / 226 W / 7.2 mJ / 30 µs" overestimate peak current (typical 55 A; 99 A only at the worst corner), underestimate FET energy (typical 8 mJ, worst 10.5 mJ) and pulse width (53 µs FWHM); CIRCUIT_REVIEW's τ of 138 µs measures 284 µs. "The load switch is not a soft start" still holds qualitatively.

---

## 3. `vlogic_holdup` — logic supply front end (RAW_IF → D2 → VLOGIC ← D3 ← VBUS, AP63203)

**Brief**: VLOGIC waveform when RAW collapses to 0 V for 10 / 20 / 50 ms (servo-stall brown-out), time and energy budget to buck UVLO / minimum VIN from 6.0 V and 7.4 V; OR-ing with RAW 7.4 V and VBUS 5 V both present; reverse leakage into the USB port; whether the buck runs without RAW; inrush into C4 when RAW rises in 300 µs vs SS34 IFSM. 83 decks; parameters from AP63203 DS41326 (UVLO 3.50 V rising / 3.06 V falling typical, 3.70/3.26 V max, recommended VIN min 3.8 V, 4 ms soft start, efficiency 0.88/0.90), MDD SS34 (VF 0.55 V max @ 3 A, IFSM 80 A, IR 0.5 mA @ 25 °C / 5 mA @ 125 °C), JIERR MA25V470M8X10 (470 µF ±20 %, 25 mΩ, 4.1 Arms).

| # | Quantity | Result | Limit | Verdict |
|---|---|---|---|---|
| 1 | VLOGIC static (RAW 7.4 / 6.0 / 8.4 V, 0.25 A) | 7.037 / 5.629 / 8.042 V (D2 drop 0.36 V @ 0.13 A) | VIN 3.8–32 V | PASS |
| 2 | Buck input power | 0.936 W @ 0.25 A; 1.830 W @ 0.5 A | — | INFO |
| 3 | Hold-up to UVLO, 7.4 V / 0.25 A, nominal C4 | 10.88 ms (VLOGIC < 3.8 V @ 9.35 ms) | 10 / 20 / 50 ms brown-out | PASS 10 ms (marginal: VLOGIC min 3.47 V, 3V3 min 3.25 V); FAIL 20 ms; FAIL 50 ms |
| 4 | Same, C4 −20 % | 8.86 ms | 10 / 20 / 50 ms | FAIL all |
| 5 | 7.4 V / 0.50 A, nominal / −20 % | 5.52 / 4.50 ms | 10 / 20 / 50 ms | FAIL |
| 6 | 6.0 V / 0.25 A, nominal / −20 % | 6.13 / 5.00 ms | 10 / 20 / 50 ms | FAIL |
| 7 | 6.0 V / 0.50 A, nominal / −20 % / −20 % + UVLO max | 3.09 / 2.53 / 2.34 ms | 10 / 20 / 50 ms; MARGIN_PRESCRIPTION's worst corner 2.46 ms | FAIL (agrees with 2.46 ms) |
| 8 | 8.4 V full, 0.25 / 0.50 A, nominal (−20 %) | 14.93 (12.14) / 7.58 (6.17) ms | 10 / 20 / 50 ms | 0.25 A: PASS 10 ms, FAIL 20/50 ms; 0.50 A: FAIL |
| 9 | Reproducing the frozen design's "18.2 ms" corner (8.4 V, 0.17 A) | < 3.8 V @ 20.0 ms; UVLO @ 22.3 ms | Frozen claim 18.2 ms | INFO: only valid at full battery + light load, not a flight corner |
| 10 | Energy budget, 500 µF total from V0 to 3.5 / 3.06 V | 7.4 V: 9.32 / 10.04 mJ; 6.0 V: 4.86 / 5.58 mJ; 8.4 V: 13.11 / 13.83 mJ | Needed: 9.4 / 18.7 / 46.8 mJ at 0.936 W; 18.3 / 36.6 / 91.5 mJ at 1.83 W | FAIL except 7.4 V and 8.4 V at 0.25 A for 10 ms |
| 11 | Energy actually drawn before UVLO (7.4 V, 0.25 A) | 10.02 mJ / 0.921 W average (matches 10.04 mJ stored) | — | INFO |
| 12 | Capacitance needed at the worst corner (6.0 V, 0.5 A) for 10 / 20 / 50 ms | 1.66 / 3.33 / 8.3 mF (0.85 / 1.7 / 4.25 mF at 0.25 A) | 500 µF today | INFO |
| 13 | 3V3 collapse after buck shutdown (7.4 V, 0.25 A): < 2.97 V / < 1.62 V (POR) | 10.64 / 11.24 ms (within 0.36 ms after UVLO) | MCU must not reset | FAIL: any brown-out longer than hold-up = MCU reset (triggers FMEA's "reset = permanent disarm") |
| 14 | 3V3 recovery after RAW returns (4 ms soft start) | 4.05–4.12 ms; a 20 ms brown-out at 7.4 V/0.25 A interrupts 3V3 for ≈ 13.4 ms | — | INFO |
| 15 | D2 recharge peak when RAW returns (300 µs ramp) | 9.6 / 12.2 / 13.9 A | IFSM 80 A | PASS |
| 16 | Bench case: same 50 ms brown-out with USB 5 V present | VLOGIC floor 4.625 V (D3 takes over), buck keeps running | — | INFO: **the flight brown-out weakness is invisible on a bench with USB plugged in** |
| 17 | OR-ing: RAW 7.4 V + VBUS 5.0 V | D2 conducts 133 mA; D3 reverse-biased 2.04 V | — | INFO: D2 always wins for RAW ≥ ~5.1 V |
| 18 | OR-ing crossover: RAW 5.0 V + VBUS 5.25 V | D3 takes over (192 mA), VLOGIC 4.877 V | — | INFO |
| 19 | D3 reverse leakage into the USB host | 2.4 µA (25 °C typ) / 98 µA (75 °C) / 544 µA (100 °C) / 161 µA (25 °C datasheet max) / 1.6 mA (125 °C max) | Absorbed by a powered host | INFO |
| 20 | USB back-voltage with RAW present and the cable's far end unpowered (R9 100k, no pull-down) | VBUS floats to 6.08 / 6.18 / 6.22 V (25/75/100 °C), clamped by the USBLC6 VBUS channel; PD15 always reads high | USB-IF back-voltage 400 mV | FAIL: confirms CIRCUIT_REVIEW §3.2 |
| 21 | USB only (no RAW), VBUS 5.0 V | VLOGIC 4.625 / 4.598 V, buck runs, 3V3 3.29 V | VIN min 3.8 V | PASS |
| 22 | USB only, VBUS 4.75 / 4.40 V, 0.25 / 0.50 A | 4.373 / 4.345 V; 4.020 / 3.992 V (0.459 A drawn at 4.4 V/0.5 A) | VIN min 3.8 V | PASS (only 0.19 V margin at 4.40 V/0.5 A, and 0.46 A exceeds the unenumerated USB 100 mA budget) |
| 23 | RAW lifted by D2 reverse leakage on USB only (only 147k on RAW) | 0.20 V at 25 °C typical; 4.61–4.62 V ≈ VLOGIC at 75/100 °C typical or with a max-leakage part | FMEA T-1: PC4 < 0.2 V → RAW < 0.63 V | FAIL (hot board or max part): T-1 is not robust, and USB puts 4.6 V on the servo header V+ |
| 24 | Arming inrush: RAW_IF 300 µs ramp, D2 peak | 10.0 / 12.3 / 14.0 A (~430 µs, 3.2–4.3 mC) | IFSM 80 A | PASS (5.7× at 8.4 V) |
| 25 | Inrush I²t, 8.4 V / 300 µs | 0.048 A²s | 26.6 A²s | PASS |
| 26 | Sensitivity to rise time (8.4 V): 100 µs / 1 ms; 100 nH harness | 38.6 A / 4.2 A; no effect of 100 nH; peak ≈ 0.51 mF × Vbat / t_rise, reaching 80 A only for t_rise < ~55 µs | IFSM 80 A | INFO: the load switch must rise in ≥ ~60 µs (§2 gives 332–389 µs) |
| 27 | C4 charge peak and VLOGIC overshoot (8.4 V / 300 µs) | 13.2 A single pulse; VLOGIC peak 8.066 V, no overshoot | No surge rating published for the capacitor | INFO |

**Verdict and consequence chain**: 500 µF discharging from 7.04 V to 3.06 V holds only 10.0 mJ, while the buck needs 18.7 / 36.6 mJ over 20 ms at 0.25 / 0.5 A. **Only the 7.4 V/0.25 A/nominal and 8.4 V/0.25 A corners survive 10 ms**; every 20 ms and 50 ms case fails. Once the buck enters UVLO, 3V3 falls below 2.97 V within 0.36 ms and reaches the 1.62 V POR → MCU reset → FMEA's "reset = permanent disarm" triggers; after RAW returns, the 4 ms soft start adds to the outage. The frozen design's **18.2 ms** is only true at a full battery and 0.17 A. **Bench trap**: with USB plugged in D3 takes over and the flight weakness is invisible. Confirms CIRCUIT_REVIEW §3.2 (VBUS back-feed to 6.08–6.22 V; the proposed 10k/10k divider fix had not yet been applied). Overturns FMEA T-1's criterion (RAW on USB alone reaches 4.6 V on a hot board). A reverse constraint on §2: the load switch rise time must stay ≥ ~60 µs or D2 exceeds its surge rating.

---

## 4. `buzzer_drive` — buzzer (LS1 MLT-8530 + Q5 AO3400A low side + D6 freewheel)

**Brief**: 3.3 V / 2.7 kHz / 50 % square-wave gate drive; coil current, 3V3 peak and RMS current, turn-off flyback on BUZZ_OUT with and without D6 against the AO3400A's BVDSS, FET dissipation, and the 3V3 ripple (including its 2.7 kHz component, since it shares the rail with the 3V3 → L2 → 3V3A filter).

**The inductance is the largest uncertainty**: the Huaneng datasheet gives no inductance. Sweeping L with the datasheet's own recommended drive circuit (saturated NPN + 1N4148, 5 Vo-p, 2700 Hz, 50 %, 16 Ω), only the "supply average current" interpretation reaches 95 mA, giving **L ≥ 1.29 mH as a lower bound**. A comparable TDK SDR08540M3-01 gives ≥ 0.27 mH. Cases bracket 0.27 / 1.3 / 4 / 10 mH with 1.3 mH as baseline.

| # | Quantity | Result | Limit | Verdict |
|---|---|---|---|---|
| 1 | Coil inductance from the datasheet's 95 mA rating | L ≥ 1.29 mH (lower bound) | TDK comparable ≥ 0.27 mH; frozen estimate 2–10 mH | INFO |
| 2 | Coil current, baseline (3.30 V, 16 Ω, 1.3 mH, D6 max-VF fit) | Rises to 185.0 mA in the 185 µs on-time (τ 81 µs), freewheels through D6 to 0 mA ~150 µs into the off-time (full reset); avg 91.6 mA, RMS 110.2 mA, coil I²R 194 mW | 95 mA max is specified at 5 Vo-p (the same model gives 165 mA RMS at 5 V) | PASS |
| 3 | Coil peak / RMS over design corners | Peak 107.5 (10 mH) … 215.3 (13 Ω) … 255.7 mA worst; RMS 91.0 … 169.5 mA | AO3400A ID 4.7 A @ 70 °C; D6 IF(AV) 1.0 A | PASS |
| 4 | 3V3 rail current, baseline | 62.6 mA avg, 95.6 mA RMS, 185 mA peak; 207 mW | AP63203 2 A; worst 113.8 mA avg / 256 mA peak | PASS |
| 5 | 2.7 kHz fundamental of the 3V3 current | 90.7 mA baseline (58.6–127.4 mA across L; 156.0 mA worst); harmonics 27.6 mA @ 5.4 kHz, 21.7 mA @ 8.1 kHz | — | INFO |
| 6 | Transfer 3V3 → L2 (4.7 µH, 60 mΩ) → 3V3A at 2.7 kHz (no buck loop modelled) | +0.80 dB (nominal C) / +0.48 dB (60 % derated C): **L2 does not attenuate the buzzer fundamental — it passes it slightly amplified**; LC resonance at 8.8 / 11.4 kHz (+12.6 / +14.7 dB), next to the 8.1 kHz third harmonic | — | INFO |
| 7 | 3V3 node impedance at 2.7 kHz (buck loop open) and ripple bound | 0.48 / 0.81 Ω → 44 / 73 mV peak (75 / 126 mV worst); the buck loop will reduce this, not simulated | — | INFO |
| 8 | BUZZ_OUT flyback peak with D6 | 3.74 V (3.79 V worst), no overshoot above the diode clamp | BVDSS 30 V (8× margin) | PASS |
| 9 | Without D6, no avalanche allowed (hypothetical) | 105 V peak | BVDSS 30 V → it must avalanche | FAIL |
| 10 | Without D6, avalanche modelled as a 30 V clamp | 1.3 mH: 172 mA avalanche peak, 19.9 µJ per cycle, 53.7 mW avalanche + 9.3 mW channel = 63.0 mW; 0.27 mH: 7.1 mW; 10 mH: 39.2 mW | **AO3400A Rev 3.1 has no EAS/IAS rating** → repetitive avalanche at 2700 Hz is outside any guarantee; D6 mandatory | FAIL |
| 11 | Q5 channel dissipation with D6 | 0.35–0.81 mW; Vds(on) 23–35 mV; ΔTj ≤ 0.10 °C | PD 0.9 W @ 70 °C | PASS |
| 12 | Q5 gate drive as drawn (R34 470R, R35 10k) | Vgs 3.14 V (2.20 V with the 1k the documents describe); both switch fully at 185 mA | Board source says R35 = 10k; the frozen design and CIRCUIT_REVIEW say 1k — no functional effect, but source and documents disagree | INFO |
| 13 | D6 1N5819WS stress | Avg 28.9 mA (44.7 mA at 10 mH), peak 185 mA (256 mA worst), 11.9 mW (18.3 mW at 10 mH), 3.30 V reverse | IF(AV) 1.0 A, VRRM 40 V, ~137 mW @ 70 °C | PASS |
| 14 | Does the coil reset in the off half-cycle vs L (I_min / I_peak) | 0.27 mH: 0; 1.3 mH: 0 (reset in ~150 of 185 µs); 4 mH: 0.38; 10 mH: 0.68 (essentially DC bias + 34 mA ripple) | CIRCUIT_REVIEW's concern **confirmed for L ≥ ~4 mH**; only a lower bound on L is known, so measure it (LCR at 2.7 kHz, or SPL with/without D6) | INFO |
| 15 | CIRCUIT_REVIEW proposal: 22 Ω in series with D6 | Peak 7.81 / 6.21 / 5.42 V (1.3 / 4 / 10 mH); reset ratio 0 / 0.10 / 0.43 (10 mH still not fully reset: τ 263 µs > 185 µs); the 22 Ω dissipates 31–33 mW, more than D6 | BVDSS 30 V; 0805 125 mW | INFO |
| 16 | 3V3 tolerance sensitivity (3.27 / 3.30 / 3.33 V) | Coil peak 183.3 / 185.0 / 186.7 mA; battery voltage does not reach this circuit | — | INFO |
| 17 | SPL at 3.3 V vs datasheet conditions | Not a SPICE quantity; coil RMS 110 mA vs 165 mA at the 5 Vo-p condition (−3.5 dB electrical), consistent with CIRCUIT_REVIEW's "~76 dB, not 80 dB" | — | INFO |

**Verdict**: both FAILs are in the hypothetical "no D6" case — **D6 is mandatory**. The real open risk is **coil reset for L ≥ ~4 mH**: measure L on the bench. And **L2 does not attenuate the buzzer's 2.7 kHz** on the 3V3A rail; whether ripple reaches 3V3A depends on the buck's output impedance at 2.7–8 kHz, which was never simulated (the `3v3a_lc_filter` case did not run). Assumptions: L is a fitted lower bound; pure R-L coil without motional impedance; AO3400A level-1 fit; D6 max-VF fit; ideal 3V3 source.

---

## 5. `servo_line_fault` — a servo signal line chafed onto the 8.4 V servo supply

**Brief**: with the servo signal shorted to 8.4 V (a plug one position off or a chafed harness), give the current into the MCU pin, the current and dissipation of R24 against its 0805 rating, and node voltages, with the pin **driven low / driven high / high-impedance (reset)**; check CIRCUIT_REVIEW's predicted 29–34 mA vs the 20 mA absolute maximum; size R24 to hold the pin below 5 mA worst case while still driving the servo.

**Model**: PA0 → SERVO1_MCU (10k pull-down, SRV05-4 channel) → R24 220R 0805 → J5.1, fault J5.1 shorted to RAW. MCU driver fitted to DS12110 Table 60 (VOL 0.4 V @ 8 mA, 1.3 V @ 20 mA → weakest legal silicon, saturating at 23.7 mA), plus 2×/4×/ideal-sink corners since the datasheet gives only limits. DC sweep of battery 6.0–8.4 V and R24 100–3300 Ω.

| # | Quantity | Result | Limit | Verdict |
|---|---|---|---|---|
| 3 | Pin driven low, 8.4 V, R24 220R: current into PA0 | 23.7 mA (weakest driver, saturated) to 38.2 mA (ideal sink); 33.5 mA at 2× | IIO 20 mA abs max | FAIL |
| 4 | Driven low at 7.4 / 6.0 V | 23.7–33.6 / 20.7–27.3 mA | 20 mA | FAIL |
| 5 | Driven low: node voltage and D5 current | 0.004–3.05 V; **D5 0.00 mA in every corner** | D5 conducts only above 4.1–4.5 V | INFO |
| 6 | Driven low 8.4 V: P(R24) | 130–320 mW = 104–256 % of rating (126–311 % of the 85 °C derated 103 mW) | 125 / 103 mW | FAIL |
| 7 | Driven low 7.4 / 6.0 V: P(R24) | 128–249 / 97–163 mW | 125 / 103 mW | FAIL |
| 8 | CIRCUIT_REVIEW's prediction (29.5–34.3 mA, 191–259 mW, SRV05-4 not conducting) | Confirmed: inside the simulated band; even the weakest silicon exceeds 20 mA | — | INFO |
| 9 | Driven high 8.4 V: current into PA0 (through the PMOS into 3V3) | 19.0–22.5 mA; 0.00–0.37 mA through D5 | 20 mA | FAIL |
| 10 | Driven high 8.4 V: node and P(R24) | 3.30–4.04 V; 87–118 mW (84–115 % of the derated 103 mW) | 125 / 103 mW | FAIL |
| 11 | Driven high 7.4 / 6.0 V | 15.1–18.0 / 9.7–11.6 mA | 20 mA | PASS |
| 12 | High-Z (reset / MCU dead) 8.4 V: current into PA0 | 0.00 mA | 20 mA / 5 mA IINJ | PASS |
| 13 | High-Z: node = 3V3 + VF(D5) | 4.16–4.51 V | 5.5 V operating, 7.3 V abs max | PASS |
| 14 | High-Z node above VDD + 0.3 V → PA0–PA3 internal pulls must stay off (PUPDR = 00) | 4.16–4.51 V | Table 20 note 4 / Table 23 note 3 | INFO |
| 15 | High-Z: I(R24), P(R24), current pushed into 3V3 via D5 | 17.7–19.3 mA; 69–82 mW; 16.8–18.4 mA per channel into 3V3 | Buck cannot sink; MCU load must exceed it | PASS |
| 16 | The frozen design's figures (4.1–4.5 V, 17.7–19.5 mA, 69–84 mW) | Reproduced — but only in this state | — | INFO |
| 17 | Voltage across R24 when driven low vs 0805 RCWV = √(0.125 W × 220 Ω) | Up to 8.40 V continuous | 5.24 V | FAIL |
| 18 | All four channels faulted and driven low | 4 × 38.2 = 153 mA out of VSS pin 26 (95 mA at the weakest corner) | IVSS 100 mA per pin, ΣI 140 mA | INFO |
| 19 | R24 needed for ≤ 20 mA worst case | ≥ 420 Ω; 680 Ω gives 12.4 mA (62 %) | 20 mA | INFO |
| 20 | R24 needed for ≤ 5 mA worst case | ≥ 1680 Ω → E24 1.8 kΩ: 4.67 mA | 5 mA | INFO |
| 21 | P(R24) at 680 Ω / 1 kΩ / 1.8 kΩ (driven low, ideal sink, 8.4 V) | 104 mW (101 % of the 85 °C derated value) / 70.5 mW / 39 mW | 125 / 103 mW | INFO |
| 22 | Servo drive level with R24 = 1.8 kΩ, servo input 10k / 4.7k / 47k | 2.78 V (1.20× VIH) / 2.37 V (1.02×) / 3.16 V | Assumed VIH 2.31 V | INFO |
| 23 | Drive level with 680 Ω / 1 kΩ (10k; 4.7k input) | 3.07 V; 2.86 V / 2.98 V; 2.70 V | VIH 2.31 V | PASS |
| 24 | Rise time with 1.8 kΩ, 4.7k input, 100 pF | 0.31 µs | 1–2 ms pulse | PASS |
| 25 | MCU source current in normal drive | 0.93–1.26 mA | 20 mA | PASS |

(Rows 1–2 were model-fit checks, INFO.)

**Verdict**: the **driven-low state — the frozen design's safe state, occupying 100 % of the pad wait — fails at every battery voltage and every driver corner**, even with the weakest silicon the datasheet allows, and the SRV05-4 does nothing in that state. The high-impedance state passes and reproduces the frozen document's figures, which were wrongly presented as "a sustained fault current that can be tolerated indefinitely". R24 sizing: ≥ 420 Ω for 20 mA; 680 Ω–1 kΩ is the practical compromise (1.8 kΩ leaves no drive margin against a 4.7k servo input). `check1.py` had no check for this fault at all.

### 5.5 A reviewer note left on disk that never reached a verdict

The `parameters` reviewer of this case, before dying on the quota, confirmed every part value, the topology, the datasheet entries and every headline number — and found a real **problem**: the agent used a self-made SRV05-4 "typical VF" corner, while **Semtech publishes a SPICE model** (IS 1e-13 A, N 1.1, RS 0.31 Ω, BV 180, CJO 3 pF). With the maker's model, VF = 0.737 V @ 15 mA (27 °C) / 0.647 V (85 °C); the agent's corners overestimated VF below 15 mA and did not cover hot silicon. Re-running the 8.4 V fault with the maker's model: high-Z at 27 °C, node 4.04 V, I(R24) 19.79 mA, 18.98 mA into 3V3, 86.2 mW (85 °C: 20.19 / 19.40 mA / 89.7 mW); **driven high (weak PMOS) D5 takes 2.05 mA (27 °C) and 7.20 mA (85 °C)**, not "0.00–0.37 mA"; **driven low (weak driver, 85 °C) D5 carries 0.76 mA**, not "0.00 mA in every corner". No headline verdict flips, but high-Z dissipation, the current pushed into 3V3 (19.4 mA per channel → 77.6 mA for four, i.e. CIRCUIT_REVIEW's 78 mA) and the clamp share when driven high were **underestimated non-conservatively**. Four minor issues were also noted. **Had this reviewer lived a few minutes longer, the case would not read "confirmed (0 objections)".**

---

## 6. `camera_uart_injection` — camera UART (PB10/PB11 + R65/R66 470R)

**The only case genuinely adversarially reviewed, and it was refuted on the spot (4 objections); the repair agent never ran. The table below is the refuted version.**

**Brief**: (1) current into PB11 through R66 when the camera drives TX at 3.3 V (and a faulty 5 V) with the MCU unpowered, and the edge-time cost of a larger R66 at 115200 baud; (2) MCU TX edges into a 100 pF harness + camera RX; (3) CAM_TX shorted to the 8.4 V camera supply: PB10 current driven low / high and R65's dissipation against its 0603 rating. PB10/PB11 modelled as FT_f, CIO 5 pF, drivers fitted to Table 60, no diode to VDD, an ideal clamp at the absolute-maximum VIN to bound current.

| # | Quantity | Result | Limit | Verdict |
|---|---|---|---|---|
| 1 | PB10/PB11 I/O structure (DS12110 Rev 5 Table 8) | FT_f (5 V tolerant), not FT_h | — | INFO |
| 2–3 | VDD = 0, camera TX 3.3 V: VIN and current into PB11 | 3.3 V, leakage only (~0 mA) for any R66 | 4.0 V abs max; IINJ +0 mA | PASS |
| 4 | VDD = 0, camera TX 5 V (fault) | Pad held at 4.0 V only if it clamps (behaviour above VIN max undefined) | 4.0 V abs max | FAIL |
| 5 | Same, current into PB11 for R66 = 470R / 1k / 2.2k / 4.7k / 10k | 2.12 / 1.00 / 0.45 / 0.21 / 0.10 mA | IINJ +0 mA → violation at any R66 | FAIL |
| 6–7 | RX edges at PB11, real and bracketing topologies, R66 470R → 10k | Real: tf/tr 13.4 ns → 111 ns; bracketing: 120 ns → 2.32 µs, valid-level width 99.5 % → 89.7 % of the 8.68 µs bit | Delay ≤ 3.80 µs (7/16 bit) | PASS |
| 8 | CAM_RX shorted to RAW_IF, MCU powered, R66 470R, RAW 6.0 / 7.4 / 8.4 V | Pad 6.0 V, 0 mA / 7.30 V, 0.20 mA / 7.30 V, 2.34 mA (1.10 mA with 1k) | 7.3 V abs max, 5.5 V operating, IINJ +0 mA | FAIL |
| 9–11 | Far-end levels and edges at the camera RX (R65 470R / 1k, 100–470 pF) | VOL 0.163 V (1k: 0.314 V); tf 154–671 ns; valid-low width ≥ 93.6 % of the bit | Delay ≤ 3.80 µs | PASS |
| 12 | CAM_TX shorted to RAW_IF, PB10 driven low: current into PB10 | 11.4 / 14.0 / 15.8 mA (weak), 12.1 / 14.9 / 16.9 mA (2×) | IIO 20 mA | PASS |
| 13 | R65 (470R 0603) dissipation in that short | 61 / 92 / 117 mW (weak), 68 / 104 / 134 mW (2×) | 100 mW | FAIL |
| 14 | R65 as 1k 0603 at 8.4 V | 63 / 67 mW, 7.96 / 8.18 mA | 100 mW | PASS |
| 15 | CAM_TX shorted to RAW_IF, PB10 driven high | 5.2 / 7.9 / 9.9 mA (weak) back-fed through the PMOS into 3V3; pad 3.55–3.75 V | IINJ +0 mA | FAIL |
| 16 | Same, PB10 input / tri-state (before init) | 0 / 0.20 / 2.32 mA (ideal clamp at 7.3 V; behaviour above undefined) | 7.3 V abs max, 5.5 V operating | FAIL |
| 17 | Same, MCU unpowered | Pad at 4.0 V; 4.2 / 7.2 / 9.3 mA | 4.0 V abs max with VDD = 0 | FAIL |
| 18 | PB10 driven high, CAM_TX shorted to GND | 6.3 mA, VOH 2.96 V, R65 19 mW | 20 mA; 100 mW | PASS |
| 19 | Document conflict | The frozen design lists PB10/PB11 as "avoid" (ROM bootloader USART3, PB10 push-pull); the board source assigns them to the camera UART | — | INFO |
| 20 | Camera supply vs the maker's documentation | RunCam Split 4 manual: "DC 5–20V (Non-direct power supply from battery, powered directly with battery will generate surges and burn the camera.)"; the two-board design fed the camera straight from the switched 2S rail | — | INFO |
| 21 | Reachability of "VDD = 0 with the camera powered" | The camera rail is the same one that feeds VLOGIC → buck → 3V3, so it needs a 3V3-rail fault or a bench setup with the camera on its own supply | — | INFO |

*(M3 later gave the camera its own regulated supply domain with an enable that defaults off; see `../STATUS.md`.)*

### 6.4 The four objections, and whether they were resolved

| # | Objection (reviewer's gist) | Nature | Resolved? |
|---|---|---|---|
| 1 | The driver model's header claims a fit to "VOL = 0.4 V @ 8 mA / 19.5 mA @ VDS 1.3 V", but independently recomputed the actual fit is VOL = 0.436 V @ 8 mA, 1.349 V @ 20 mA, VOH 2.864 V @ −8 mA, 1.951 V @ −20 mA — **9 % weaker** than the Table 60 limit it claims to reproduce | Labelled parameters don't match the actual fit | **No** — repair never ran |
| 2 | The weak driver is labelled "worst case", but for "current into PB10" and "R65 dissipation" **the strongest driver is worst**; the driver-independent upper bound (VOL → 0, R65 at −1 %) is **18.05 mA / 152 mW @ 470R** and **8.48 mA / 71 mW @ 1k**, and the driven-high back-feed bound is (8.4 − 3.3)/470.1 = **10.85 mA**; "PASS with 16–21 % margin" should read "≥ 10 % margin against the bound" | Non-conservative fit direction + wording | **No** |
| 3 | The "2× stronger = typical" corner has **no source** (no IBIS model or typical Ron cited) | Unsourced corner | **No** (the reviewer notes it becomes unimportant once objection 2's bound is used) |
| 4 | The report misses that fault conditions push the pad above VDD + 0.3 V / 4 V, where DS12110 Table 20 note 4 and Table 23 note 3 **require internal pulls to be off**; a UART RX internal pull-up on PB11 is a one-line CubeMX default, so **PUPDR[PB10/PB11] = 00 must be written as a firmware constraint** | Missing firmware constraint | **No** (compare `servo_line_fault` row 14, which states the same rule for PA0–PA3) |

The reviewer stated explicitly that **no PASS/FAIL verdict flips**; what was refuted were the numbers and wording of the Q3 rows (15.8/16.9 mA, 117/134 mW and "16–21 % margin" are not bounds and must be replaced by the 18.05 mA / 152 mW bound). A second note from the `physics` reviewer ("not refuted", with six caveats — most importantly that every current computed "after the pad exceeds the absolute-maximum VIN" is an artefact of the ideal 1 Ω clamp in the model, **not a prediction**; the correct statement is "the Table 20 VIN limit has been exceeded, independent of the series resistor; the pin current is undefined by the datasheet") was left on disk, but that reviewer died before returning a verdict, so it is not counted.

---

## 7. Conflicts with `check1.py`

`check1.py` was the electrical checker for the legacy M1 power board (25 checks, 0 failing). It is not included in this repository.

### 7.1 Conflict C-1 (core): load-switch inrush — check1.py's three numbers have the wrong mechanism

| Quantity | check1.py | Simulation |
|---|---|---|
| Inrush current | Implicitly assumes a constant `I_SAT = 15.0 A` | **33.2 / 45.8 / 54.8 A** at 6.0 / 7.4 / 8.4 V; **99.1 A** at the worst corner |
| Q2 energy | `0.5·C_LOAD·8.4² =` **18.13 mJ**, "all in Q2", limit 50 mJ, PASS | **8.07 mJ** @ 8.4 V (4.99 / 6.69 mJ at 6.0 / 7.4 V; 10.5 mJ worst); @ 8.4 V the 66.6 mJ from the battery splits into capacitor 34.6 + battery/wiring 15.6 + **Q2 8.1** + D2 2.9 + Q1 1.7 mJ |
| RAW rise time | `C_LOAD·8.4/15 A =` **287.8 µs**, limit 2000 µs, PASS | **389 / 350 / 332 µs** to 95 % (including M2's 470 µF); 217 µs with M1 capacitance only |
| Q2 power | `E/t =` **63 W** average, limit 120 W, PASS | Peak **64 / 104 / 138 W**, FWHM 73/59/53 µs; worst **257 W / 36 µs** |
| Load capacitance | `C1 + C2 + C3 = 514 µF` (M1 only) | **Misses M2's C4 470 µF via D2**: charge through Q2 7.9 mC vs 4.0 mC — doubled |

Four independent mechanism errors: (1) **15 A constant current does not hold** — the gate crosses threshold in ~50 µs and current rises to 40–55 A, then is set by loop resistance (battery 40 mΩ + wiring 20 mΩ ≫ 2 × 3 mΩ of FET), not by FET limiting; (2) **0.5CV² does not all land in Q2** — Q2 takes only 12 % of the 66.6 mJ, so check1 overestimates Q2 energy 2.2× (conservative); (3) **comparing average power to SOA is non-conservative** — the real 138 W peak is 2.2× check1's 63 W and **exceeds check1's own 120 W limit on the same line**, which still reads PASS only because it compares an average (the simulation's PASS uses AON6403 Fig. 10's ~350–500 W single-pulse rating); (4) **M2's 470 µF was missed**. **The conclusions do not flip** (8.07 mJ < 50 mJ, 332–389 µs < 2000 µs), but **18.1 mJ / 288 µs / 63 W must no longer be quoted as "Q2's dissipation"**. A new checker should include M2's C4, use 8.1 mJ typical / 10.5 mJ worst for Q2, and compare **peak 138 W (257 W worst) against the Fig. 10 single-pulse curve**.

### 7.2 Conflict C-2: the gate-voltage check covers only the unloaded case

check1's static divider `Vgs = −Vb·R1/(R1 + R2)` gives 7.636 / 6.727 / 5.455 V, matching the simulated unloaded values to the last digit. But the divider references FET_S, which sags with IR drop under load: at 7.5 A Vgs falls to −7.20 / −6.29 / −5.01 V, **−4.73 V at the worst corner, only 0.23 V from the −4.5 V RDS(on) specification point**. check1 used the 2.4 V worst-case Vgs(th) as its limit, hiding the tight one.

### 7.3 Conflict C-3: the servo checks do not reach the real fault state

check1's "servo pull-down load on the MCU" (330 µA, PASS) matches normal drive (0.93–1.26 mA), but the **fault state** (signal chafed onto 8.4 V + pin driven low) is 23.7–38.2 mA, 119–191 % of the 20 mA absolute maximum. Its "servo signal level with M2 absent" (hard-coded 0.0 V) concerns the signal line, whereas `vlogic_holdup` found a different path: on USB alone, hot or with a max-leakage part, D2 leakage lifts RAW to ≈ 4.6 V, **putting USB-derived voltage on the servo header V+**. check1 had **no R24 dissipation check** at all (130–320 mW in the fault state; 8.4 V continuous across it exceeds the 0805's 5.24 V RCWV).

### 7.4 Conflict C-4: check1.py covers none of the 24 FAILs

Out of scope (not check1's fault): `vlogic_holdup`, `buzzer_drive` and `camera_uart_injection` were on M2. In scope but missing: `servo_line_fault`'s R24 and J5 header were M1 parts, yet only the normal state was checked.

### 7.5 Items with no simulation support (do not treat as "supported by simulation")

check1's anti-Miller capacitor division (3.9 mV with 10 nF, 55.6 mV without) corresponds to `m1_pyro_channel`, **which never ran**; its divider and sense-current checks correspond to `sense_dividers_adc`, also no data. [INFERENCE] The only related evidence is `m1_load_switch`'s reverse hot-plug, where capacitive division momentarily pulled Vgs to −1.47 V, below Vth min −1.2 V for 54 / 398 µs, suggesting that "static capacitive divider" estimates of this kind should be re-checked with transient simulation — **an inference, not a result of this round**.

---

## 8. Cases that never ran (gap list)

9 cases / 21 agents; 6 agents delivered and 15 died; **4 cases produced no data at all**.

### A. Four SPICE cases with no data

| Case | What it was meant to answer | Cause |
|---|---|---|
| `m1_pyro_channel` | Gate and current rise times, peak current, FET Vds and instantaneous power, FET energy over a 10 ms pulse (0.7 Ω and 1.2 Ω × 8.4 V and 6.0 V) against check1's 11.5 A / 3.7 W and the AO3400A SOA; anti-Miller (drain 0 → 8.4 V in 1 µs, with/without C35 10 nF); continuity sensing and **the avalanche when the bridgewire burns open at 11 A with 100 nH of lead inductance**, against the ADC pin's 5.5 V / 7.3 V limits | Stopped by an API safety filter, not the quota (5 tool calls) |
| `sense_dividers_adc` | DC readings of every ADC divider, **sample-and-hold settling error** at 1.5/8.5/64.5/810 ADC clocks at 12/16 bits, and injection current through the upper arms with the MCU unpowered | Session limit |
| `3v3a_lc_filter` | AC transfer of 3V3 → L2 → 3V3A, attenuation at the switching frequency and harmonics, **resonant frequency and Q**, droop and ringing for a 60 mA / 1 µs GNSS burst and a 20 mA step, DC drop at 30/100 mA | Session limit |
| `pullpin_nrst_debounce` | Pull-pin input (10k pull-up, 1k series, 100 nF) time to a clean high after pulling, effect of a 3 ms bounce train, immunity to 1 µs / 100 µs false triggers, loop current with the pin in; NRST 100 nF rise time and filtering of 100 ns / 1 µs glitches | Session limit |

Partial files exist in some of these case directories, but no structured results reached the JSON, so no numbers from them are quoted.

### B. Nine adversarial reviews started but never returned a verdict

Both reviewers of `m1_load_switch`, `vlogic_holdup`, `buzzer_drive` and `servo_line_fault`, plus the `physics` reviewer of `camera_uart_injection` — all died on the session limit. Two left notes on disk (§5.5 and §6.4), neither counted as a vote.

### C. The repair stage for `camera_uart_injection` never started

So none of the four objections in §6.4 was fixed.

### D. The report stage never started

This document replaces it.

### E. Eight reviews never created

The pipeline does not enter Verify when a simulation fails, so the two reviewers of each of the four cases in A were never created.

---

## 9. Reproduction

Simulator: ngspice-46 in batch mode; post-processing with python3 + numpy + matplotlib. The case directories (decks, `run.sh`, logs, waveform data, `results.json`, 22 PNG plots) were kept in the original local working tree and are not part of this repository. To reproduce, rebuild the decks from the topology and model descriptions in §2–§6.

---

## 10. Open items (listed only, not decided)

1. **`vlogic_holdup`'s FAIL is the heaviest of this round**: flight-corner hold-up is 2.34–6.13 ms, a 20 ms brown-out always resets, and the FMEA rule is "reset = permanent disarm". Either add capacitance (1.66 / 3.33 / 8.3 mF at the worst corner for 10 / 20 / 50 ms), change the "reset = disarm" rule, or show that a servo stall cannot collapse RAW for more than 10 ms.
2. **`servo_line_fault`'s FAIL covers 100 % of the pad wait**: R24 = 220 Ω must be re-sized (≥ 420 Ω to get under 20 mA; 680 Ω–1 kΩ is the simulated compromise).
3. `camera_uart_injection` needs its repair re-run (the four objections + the suggestion to make R65 1k 0603).
4. Any successor to `check1.py` must use the §7.1 numbers for the load switch and add checks for the R24 fault state and the M2-side 470 µF.
5. The four cases that never ran need to be run; `m1_pyro_channel` is the one that bears directly on "can inserting the arming plug fire a charge".
