# R9 owner decisions (2026-10-20)

Asked once against r9_plan.md §3; the owner chose the recommended option each time.

1. Architecture: B-spine at 46 × 98 mm (fallback 100 / 102 mm if placement fails). Pyro leads exit the west edge, battery leads the east edge.
2. Pyro: adopt the stricter pyro rules (P-1b, P-3, P-7 and the strict pad rules of r9_plan.md §1) and renumber J121/J124 pads (same part, same land; check_actuators unchanged).
3. RF: the RF strip boundary becomes y 0–22.0 (F10 text updated); the radio-to-pyro distance of about 45 mm is accepted, verified by the keyed-radio pyro-immunity bench test.
4. Signal vias: done at ≤ 70 with per-family budgets, stretch target 55.
5. Defaults taken without a separate question (r9_plan.md §3): J122 turned (reason recorded); the mid-span support at (42, 55.5) if the DC solve holds, else (4, 49.5).

# R9 owner decisions (2026-10-25)

Asked after review passes 1 and 2; the owner chose the recommended option each time.

6. Length: keep the board at 46 × 102 mm (R9_VALIDATION C1, option (c)), over (a) 98 mm by taking R306 / R310 / R313 / R315 out of F10's RF-part list and (b) 100 mm with the four interface resistors 5.0–5.94 mm from U1.
7. Acceptance: the R9 deviation list in R9_VALIDATION, bound to `4f841a0e…`, is accepted as of 2026-10-25, including the agent decisions in its part D (U4 turned 180° with roll = −gyro_Y, the crystal's local In2 GND plane); commit and push branch `m3-assy-r9`.
