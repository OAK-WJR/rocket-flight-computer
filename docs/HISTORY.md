# Design history

A short record of decisions that were made and later reversed, so they are not re-litigated.

## 1. Single board → two boards → single board

- **REV-G (2026-09-03)**: one 46 × 120 mm four-layer board (`GEOMETRY_REV_G.md`).
- **REV-H/M (2026-09-04)**: split into M1 (power + actuators, 46 × 50–66 mm) and M2 (MCU + sensors, 46 × 96 mm) joined by two JST PH harnesses (S12B-PH / S9B-PH, 21 wires). The argument was cost distribution: ~80 % of the BOM value (GNSS, MCU, IMU, barometer) sat on M2, while every open connector defect sat on the cheap power board, so power-board respins would be cheap.
- **M3 (2026-09-07 onward)**: the split was **reversed** — M1 and M2 are merged back into one board. Reasons: one assembly order instead of two (the fixed JLCPCB setup / stencil / feeder costs are paid once), no 21-contact inter-board harness, no hot-plug rule, and a shorter avionics bay (one board instead of 50 + 18 + 96 mm). The cost accepted: every respin now carries the full set of expensive silicon, and destructive power tests can no longer be done on a cheap sacrificial board.

The legacy M1 power/actuator design lives in `../reference/m1_power_actuator/` because its pyro, arming, servo, pull-pin and buzzer circuits still have to be merged into M3.

## 2. Rules from REV-H/M that still apply

- **M3 tie rods only clamp the bulkheads/sled and never pass through a PCB.** The board is fixed to the sled with its own M3 screws. (REV-G §7.4 had the rods pass through holes 112 mm apart in the plane of the board, which is geometrically impossible for a straight rod.) Hole positions are still open pending the sled design.
- **Connectors are not structural elements** (IREC DTEG 2026 V1.1 §6.12.3.2–6.12.3.3). Any harness connector needs an external retention means: one zip tie over the housing and a second anchoring the harness to the sled ~30 mm downstream. JST does not publish mating/retention force for PH, so the tie is the only defensible retention.
- **Separation targets on the MCU side**: buck switching loop ≥ 30 mm from the IMU; 25 MHz crystal ≥ 40 mm from the GNSS antenna (25 MHz × 63 = 1575.000 MHz, 420 kHz from L1 centre).
- **No switched high current across any boundary**: the 7.66 A servo bus and the 4.0–9.84 A pyro pulses stay in one compact corner.
- **Board placement is coplanar on the sled**: the envelope `h(x) = √(719.8489 − (x − 23)²) − 1.263` from `GEOMETRY_REV_G.md` is unchanged; the binding item is still the plugged servo header (23.50 mm needed, 1.558 mm margin).
