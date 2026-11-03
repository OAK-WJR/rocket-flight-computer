# R10 round 31: power lens

Target commit `3366287`, board SHA-256 `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c` before and
after (unchanged). Strict real-error rule (`.supervisor/r31_review_brief.md`).

**Totals: 0 Critical, 0 Major, 0 Minor.** No real error found. 19 observations (not counted).

## Findings

None.

## What was checked

- **Budget binding and D-R28-01.** `r10_parts.py --check --budget-only` exits 0, so `parts_budget.json` is current
  (SHA-256 `4267634220f4…`, as parts_qualification.md quotes). A hand solve of the four-stall pack sag (0.15 Ω, 8.3175 A
  constant current, 10.646 W constant power) gives 5.880831 / 4.388491 V. Every current quote matches, and no stale figure
  remains outside dated history.
- **Audit A's power figures in parts_qualification.md.**
  - USB attach: 514.1 / 516.1 µF, the same as the board's VLOGIC and USB_LIMITED capacitors; 347.7–453.0 mA;
    5.33–6.95 / 5.35–6.98 ms.
  - C120 off time constant: 64.52 ms (129.03 ms with one resistor open).
  - GAP-1: loop 4.617803 Ω, stall currents 1.540851–1.278747 A.
  - GAP-3: 0.490 W, junction 109.2–123.9 °C, theta ceiling 112.3 °C/W.
  - GAP-5: 28.571–32.653 ms; 0.739 ms gate tail; 34.853 ms in all; R134 35.80 W.
  - Ride-through table: every cell matches its budget key.
  - OQ-5: VOFF 5.73–6.30 V, VON 6.48–6.94 V, 3.8 / 6.0 and 1.6 / 2.5 ms (correct roundings).
- **Rails against their limits.** All are inside their limits:
  - Buck 5.367–5.546 V and LDO 4.712–4.873 V; headroom 0.443 V; bleeder 5.63 mA.
  - Endpoint minima 5.031682 / 4.601504 / 4.631504 / 4.641504 V.
  - Current limits: U402 1.041–1.249 A, U11 1–2 A, U9 3.946–4.857 A against the 3.744 A fault bound.
  - Every regulator input against its maker range, and U9's EN / OVLO against 6.5 V at the 19.9 V TVS clamp.
- **IPC-2152.** Every K-power floor meets the width for its design current. The In2 power fills are each one piece, and
  3V3 is 0.300 mm from the rail fills (as owner row 1 states). The 0.549 mm 3V3 neck is above the 0.375 mm width needed
  for 2.0 A.
- **Hot-plug.** The inputs bind `a0ec075e…`, and the canonical digest matches the results file. The extrema reproduce
  from all 2304 rows. The retained-output inventory lists all 73 board capacitors. The limits match SLVSFC9C §6.1.
- **Regulator taps.** R400.1 taps at C403.1 and R402.1 on U401's OUT run, with no via in either; U2.1 senses locally.
  U401's PG, SS_CTRL and EN and U13's open EN agree with the maker sheets.
- **EN / J400 figures.** All of these reproduce:
  - turn-on and drop-out times;
  - window limits 9.594 / 7.501 / 7.629 / 5.871 ms;
  - turn-off 4.802 / 4.835 V;
  - the 4.29–4.80 / 4.72–5.25 V ramp window;
  - the damaged-EN corners;
  - the four-stall-plus-fire corners (5.50 V is the lower corner of 5.50–5.51 V).

## Fix verification

| Item | Verdict | Measurement |
|---|---|---|
| R30-TRI-01 (EN-load sibling; power-adjacent) | confirmed | R10_VALIDATION:2670 gives 5.6 kΩ with the e-match or dummy fitted (11.2 k ∥ 11.2 k); EN is then about 0.05 V. The §1 figures (2.19–2.21 V, 0.107–0.109 mA) reproduce |
| R30-TRI-02 (chamber criterion) | confirmed | No live "LS120 ≤ 70 °C" pass clause remains. The pass is "every 85 °C part ≤ 85 °C"; LS120's rise is recorded and is not a gate |
| D-R28-01 | confirmed | port_A = 1.461 + AUX feeds both ports_w and loaded_pack; the hand solve agrees |
| D-R29-01 / -02 | confirmed (spot check, outside the lens) | 47.8 / 53.0 / 58.3 µs reproduce |

## Observations (not counted)

1. The budget is current and its SHA matches the record.
2. The D-R28-01 pack sag reproduces.
3. The USB attach inventory matches the board.
4. The C120 off and enable networks reproduce.
5. GAP-1 reproduces.
6. GAP-3 reproduces.
7. GAP-5 reproduces.
8. The ride-through table reproduces.
9. OQ-5 reproduces.
10. The post-trip hold-up reproduces.
11. The EN / J400 figures reproduce.
12. The four-stall-plus-fire corners reproduce.
13. The rail tolerance bands, endpoint minima, current limits and part input ranges all hold.
14. The regulator taps are as recorded.
15. The IPC widths, In2 fills and gaps are as recorded.
16. The hot-plug binding and inventory are as recorded.
17. The probe positions and the C84 capacitance window are as recorded.
18. Three classes were already observed in earlier rounds:
    - USB_LIMITED 63.605 mm, labelled Round 18 (63.115 mm now, conservative);
    - U400 / L400 "1.2–2.2 W";
    - the U400 input feed outside K-power.
19. The REQUIREMENTS Pack row's "about 1.7 W, 0.23 A" reproduces with the 11 mA quiescent allowance (1.73 W, 0.234 A).

## Coverage limits

- No simulation was re-run.
- No `tools/check.sh` ran on the canonical tree.
- The VLOGIC-drop and port-lag models were checked for plausibility only.
- The sealed pad-energy worksheet was not recomputed.
- No other round 31 lens report was opened.

Probe scripts are in `.supervisor/r31_power/`.
