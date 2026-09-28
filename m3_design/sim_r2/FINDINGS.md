# M3-ASSY-R2 actuator band — what the simulations say

**Scope.** Sheets 11–14 of the R2 schematic: the actuator switch, both pyro channels, the servo outputs and the pull-pin. They were simulated with ngspice using the component values as drawn.
- Every number is in [`RESULTS.md`](RESULTS.md).
- To re-run: `python3 m3_design/sim_r2/run.py` (needs `ngspice`).
- The models and the datasheets they came from are in [`models.inc`](models.inc).

**Nothing here is a bench measurement.**

## Summary (current design)

| Area | Result |
|---|---|
| Actuator switch on and off: 6.0 and 8.4 V; no load, cruise, or all four servos stalled; typical and slow AON6403 | **PASS.** RAW_ACT reaches 95 % in 6–13 ms. Worst Q121 junction rise is 16 K (turn-off into four stalled servos at 8.4 V) |
| Pyro fire at the worst corner (6.0 V, 80 mΩ pack, max-RDS FET, weakest legal GPIO) | **PASS.** 1.72 A in a 1.2 Ω bridgewire + 1 m 26 AWG (MJG recommended all-fire is 1.0 A). The gate reaches 2.5 V in 99 µs; GPIO peak current is 17.2 mA (limit 20 mA) |
| Firing into a shorted igniter, all six corners | **PASS** with R134/R135 (below). The worst case is 4.1 A, BAT_IN ≥ 5.69 V, and ~0 K FET rise. R134 peaks at 33 W; the CRM2512 chart allows 63 W for 20 ms |
| ARM plug insertion with the FET off (Miller), weakest-threshold part, contact bounce | **PASS.** Peak VGS is 17 mV against a 0.4 V threshold. With C126 removed (DEMO) it reaches 0.5 V, which is why C126 must stay |
| Plug-out self-test (10 k cold pull-up, ratiometric ADC) | **PASS.** 0 / 95–100 / 141–148 mV for a shorted FET / a good igniter / an open igniter. The good-vs-open gap is 41 mV, so the ADC must be calibrated within ±20 mV |
| Servo signal and pull-pin line chafed onto RAW_ACT | **PASS.** Pin current ≤ 10.4 mA, resistors within rating, and nodes within the FT limits |

## Finding 1 (fixed) — a shorted igniter used to take down the computer

As merged in PR #1, there was no series resistance in the pyro path. Firing into a shorted igniter was then limited only by the pack, the wiring and the 5 A arming fuse, which has a melting I²t of 42.8 A²s. The `OLD-FAIL` rows in RESULTS.md re-simulate that design:
- BAT_IN stayed below 5 V for 4–20 ms.
- That is longer than the ~3 ms of logic hold-up, so the MCU would reset and channel 2 would never fire.
- At a fresh 8.4 V pack, the AON7524 also carried 131 A (IDM is 112 A) and rose 124 K.

**Fix, now on the board:**
- R134 and R135 are Bourns CRM2512-FX-2R00ELF (2 Ω, 2 W, pulse-rated), one per channel, between the fused bus and the igniter terminal.
- R131 and R143 (the cold pull-ups) change from 47 k to 10 k, which is what makes the plug-out self-test above pass.
- Details are in `docs/M3_ACTUATOR_MERGE.md` §2.6.

**Firmware rules the fix relies on:**
- Every fire pulse must end after 20 ms. If the gate were left on into a dead short, R134 would reach its pulse limit after about 60 ms and fail open. That loses the channel, but it is not a fire hazard.
- Flight state must survive an MCU reset.

## Finding 2 (fixed) — plug-out self-test margin

With the original 47 k pull-up, the three plug-out states were only 18–27 mV apart. Two changes fix this:
- the 10 k pull-up;
- evaluating the reading the way the ADC actually sees it. VREF+ is 3V3A, taken from the same 3V3 rail as the pull-up, so the ±5 % tolerance of that rail cancels.

## Finding 3 (info) — RAW_ACT_SENSE during a TVS clamp

If BAT_IN is clamped at 15.4 V, PB0 sees 4.9 V in analog mode. This happens only during the transient, and less than 0.2 mA flows through R124.

## Not covered here

- U9 (TPS259470L) current limit, fault latch and reverse blocking: U9 is modelled as an ideal switch.
- The buzzer: see the R1 study. D123 is fitted.
- Servo motor dynamics, EMI, and copper heating on the PCB.
- Everything that needs a real board: see `docs/M3_ACTUATOR_MERGE.md` §4.
