# M3-ASSY-R2 actuator band — what the simulations say

Scope: sheets 11–14 of the R2 schematic (actuator switch, both pyro channels, servo outputs, pull-pin), simulated with ngspice using the component values as drawn. Every number is in [`RESULTS.md`](RESULTS.md); re-run with `python3 m3_design/sim_r2/run.py` (needs `ngspice`). Models and their datasheet sources are in [`models.inc`](models.inc). **Nothing here is a bench measurement.**

## Summary

| Area | Result |
|---|---|
| Actuator switch turn-on / turn-off, 6.0 and 8.4 V, no load / cruise / all four servos stalled, typical and slow AON6403 | **PASS.** RAW_ACT reaches 95 % in 6–13 ms. Worst Q121 junction rise is 30 K (turn-on into four stalled servos). Turn-off is slow (C120 × R120 = 220 ms): Q121 absorbs up to 334 mJ spread over ~300 ms, but the junction rise stays at 18 K |
| Pyro fire, 6.0 V / 80 mΩ worst corner, max-RDS FET, weakest legal GPIO | **PASS.** The gate reaches 2.5 V in 99 µs, the final VGS is 3.07 V, and the bridgewire current is 4.07 A (recommended all-fire is 1.0 A). The GPIO peaks at 17.2 mA (limit 20 mA) |
| ARM plug insertion with the FET off (Miller), weakest-threshold part (VGS(th) 0.4 V), contact bounce, MCU unpowered or driving low | **PASS with a wide margin.** Peak VGS is 24 mV, and the igniter sees 2.4 µA²s. With C126 removed (DEMO), the peak becomes 550 mV — above threshold — which confirms that C126 (220 nF) is what makes this safe |
| Servo signal chafed onto RAW_ACT (8.4 V and 10.5 V), pin low / high / Hi-Z | **PASS.** Pin current is ≤ 10.4 mA (limit 20 mA), R150 dissipates ≤ 108 mW (0805 rating 125 mW), and the Hi-Z node sits at 4.1 V (FT limit 7.3 V) |
| Pull-pin line chafed onto RAW_ACT | **PASS.** The PC14 node is clamped to 3.69 V, R160 (0402) dissipates 46 mW, and 6.8 mA is pushed back into 3V3 |
| **Shorted igniter on one channel** | **FAIL — see finding 1** |
| Continuity / arm-sense with the plug out | **MARGINAL — see finding 2** |

## Finding 1 — a shorted igniter on one channel can take down the computer (and, at the worst corner, the FET)

This case is a crushed or shorted igniter, or leads shorted at J121, when the channel fires. Nothing limits the current except the battery, wiring and the 5 A arming-plug fuse. The Littelfuse 217 5 A fast-acting fuse has a melting I²t of 42.8 A²s, so it takes milliseconds to open:

| Short at | Pack | Peak current | Fuse opens | BAT_IN | AON7524 ΔTj |
|---|---|---|---|---|---|
| J121 terminal | 8.4 V, 20 mΩ | 131 A (> IDM 112 A) | 4.0 ms | 3.7 V, < 5 V for 3.9 ms | **124 K (fail)** |
| J121 terminal | 7.4 V, 40 mΩ | 110 A | 8.0 ms | 2.6 V, < 5 V for 7.9 ms | 75 K |
| J121 terminal | 6.0 V, 80 mΩ | 85 A | 24.5 ms | 1.5 V, < 5 V for 24.6 ms | 28 K |
| far end of 1 m lead | 6.0 V, 80 mΩ | 30 A | > 60 ms | 3.7 V, < 5 V for 60 ms | 9 K |

The two channels have separate fuses and FETs, but they share the battery. While the fuse is melting, BAT_IN collapses for longer than the ~3 ms of logic hold-up found in the R1 study. So **the MCU is expected to reset, and channel 2 will only fire 2 s later if firmware resumes the flight state after a reset.** That undermines the on-board redundancy ruling for exactly the failure (a damaged igniter) it is meant to cover. At the fresh-battery corner, the AON7524 also exceeds its IDM and its junction limit before the fuse opens.

Options (owner decision, not applied):

1. **Firmware (needed in any case):** keep flight state in backup SRAM and resume after an in-flight reset, so channel 2 still fires. Also limit each fire pulse (for example 50 ms).
2. **Hardware:** add a series resistor per channel. The script simulates 1.0 Ω. It keeps BAT_IN ≥ 5.4 V and the FET cool in every short case, and still gives 2.42 A of fire current at the worst corner. However, with a short the fuse then no longer opens, and the resistor takes about 62 W for as long as the gate is on. It is only viable together with the firmware pulse limit and a pulse-rated part; no part has been chosen.
3. **Fuse:** a 5 A fast-acting fuse with a much lower melting I²t opens sooner. MARGIN_PRESCRIPTION P0-3a asks for ≥ 8 A²s so that a legitimate fire does not blow it; the 217 series has 42.8 A²s.

## Finding 2 — plug-out self-test margins are thin

With the plug out, the only signal is the 47 kΩ cold pull-up (FMEA H-1). Worst-case ranges (6.0/8.4 V, 3V3 ± 5 %, 1 % resistors):

| State (plug out) | PYRO_CONT |
|---|---|
| igniter OK, FET OK | 27–31 mV |
| igniter open | 49–57 mV |
| FET shorted | 0 mV |

"FET shorted" vs "OK" is separated by 27 mV, and "igniter open" vs "OK" by 18 mV. Firmware can tell them apart only if the ADC error after calibration is below about ±9 mV. With the plug in, the separations are about 0.5 V (PASS). A stronger cold pull-up (a smaller R131/R143) would scale these levels up. This needs a bench check of ADC offset before it is relied on.

## Finding 3 — RAW_ACT_SENSE can exceed VDDA during a TVS clamp

If BAT_IN is clamped at 15.4 V (SMBJ9.0CA VC), RAW_ACT_SENSE reaches 4.9 V on PB0 in analog mode (limit VDDA). The current is < 0.2 mA through R124, and only during the transient, so this is INFO.

## Not covered here

- U9 (TPS259470L) behaviour: current limit, fault latch and reverse blocking. It is modelled as an ideal switch.
- The buzzer: see the R1 study; D123 is fitted as that study requires.
- Servo motor dynamics, EMI, and PCB copper heating of the 2.6 mm servo neck.
- Everything that needs a real board: the bench tests listed in `docs/M3_ACTUATOR_MERGE.md` §4.
