# R10 round 34 — power lens (Claude)

Target commit `c2a11fd`, board SHA-256 `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c` before and
after (unchanged). Probes: `.supervisor/r34_power/`.

**Totals: 0 Critical / 0 Major / 0 Minor real errors.**

## What was checked
- **Budget figures (D-R28-01):** `loaded_pack` with `port_A` = 1.461 + 0.1 A reproduces 5.8808312 / 4.3884907 V, the
  same in `parts_budget.json`, `parts_qualification.md`, STATUS and M3_R10.
- **parts_qualification (audit A):** the USB attach inventory (514.1 µF on VLOGIC plus C86 / C98: 516.1 µF, checked
  against the board's pads; 2.426 mC, 5.35–6.98 ms at 347.7–453.0 mA); C120's off tau (64.515 ms, 129.03 ms with one
  resistor open, 15.5 / 7.75 tau in 1 s); GAP-1 (copper 29.650 / 35.477 mΩ, 1.2787 A at four stalls); GAP-3
  (0.48965 W, 109.2–123.9 °C, 112.3 °C/W); GAP-5 (34.853 ms bound, the R134 pulse figures); the ride-through table; and
  OQ-5. All of them reproduce.
- **Rails:** every power-net segment below its floor is either a sense, divider or bias branch, or a named POWER_NARROW
  entry. The K-power floors meet the `tools/ipc2152.py` widths at their design currents. The regulator feedback taps
  (U400, U2, U401) sense where the records say they do. The hot-plug inputs bind `a0ec075e…`, all 2304 rows pass, and
  the extremes match M3_R10.

## Fix verification
- R33-TRI-01: **confirmed.** U9's pads 5 / 6 run y 80.40–82.80 and pad 9 runs x 19.10–19.70. Against the 1.9–2.1 mm
  body, each end is exposed by 0.15–0.25 mm, as ORDERING 8.3 lines 552 / 555 now say.

## Observations (16, not counted)
Most are reproductions of the figures above. Already-observed items seen again:
- the Round 18 USB_LIMITED length of 63.605 mm (the board has 63.116 mm);
- Q122's 0.218 V, which is 0.2203 V with 1 % parts.

New, judged historical: `hotplug.md`'s dated "Round-11 fix-pass target" header still quotes `0ad0135c…` and
1616.12 µF / 5.878 V. M3_R10 carries the current 1643.90 µF / 5.914 V. Full list in the JSON.

## Coverage limits
- The hot-plug and chatter models were not re-simulated.
- Datasheet limits were taken as the records cite them.
- No full gate run.
