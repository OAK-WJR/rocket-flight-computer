# R10 round 35 review: power lens

Target: commit `c3c4249`, board `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c` (SHA-256 checked
before and after the review: unchanged). Reviewer: Claude. Rule: real errors only.

## Totals

0 Critical / 0 Major / 0 Minor. No findings.

## What was checked

- **Budget figures (`parts_budget.json` / `r10_parts.py`).** I re-derived every key the lens names by hand:
  - rail bands, endpoint minima and the camera ILIM;
  - the OVLO corner, U9's limit, its fault bound and the prospective input;
  - D-R28-01's shared port current (1.461 A + AUX), which gives a loaded pack of 5.880831 / 4.388491 V;
  - the ride-through cases a–d and the PA6-trip hold-up;
  - OQ-5's VOFF / VON and ride-through;
  - GAP-1 (loop resistance 4.617803 Ω, 1.540851 … 1.278747 A), GAP-3 (0.490 W, 109.2–123.9 °C) and GAP-5
    (34.853 ms, R134 pulse figures);
  - C120's on and off time constants (64.52 / 129.03 ms off).

  Everything reproduces, and the matching text in `parts_qualification.md`, M3_R10, ORDERING 8.3 and the handoff agrees.
- **USB attach inventory, read from the board.** VLOGIC carries 514.1 µF and USB_LIMITED 2 µF, 516.1 µF in all. That
  gives 2.426 mC and 5.35–6.98 ms at 347.7–453.0 mA. The USB-only draw figures reproduce.
- **Rails against their limits.**
  - K-power and S-9 pass on a probe copy. Every path floor is at or above its IPC-2152 width.
  - The single-via taps are exactly the disclosed exceptions.
  - A raster-erosion neck test of the In2 RAW_PROTECTED, PORT_5V3 and PORT_4V8 fills shows each stays connected at
    1.0 mm between its via groups, above the internal IPC widths (0.71 / 0.32 / 0.34 mm).
  - Rail voltages are within the part ratings. The regulator taps and the TPS2121 pin map match the datasheets.
- **Hot-plug.** The bound inputs and results are on `a0ec075e…` and all pass flags are true. The 1643.90 µF retained
  inventory lists exactly the board's capacitors.

## Fix verification (round 34)

- R34-TRI-01 (hot-plug results pointer): **confirmed**. `parts_qualification.md` (R92, R166 sections) and `hotplug.md`
  point to `hotplug_results.json` / `hotplug_inputs.json` (board `a0ec075e…`) and M3_R10 "Current state".

## Observations (not counted)

There are 17 in the JSON. Most are reproductions. Two are classes earlier rounds already observed and are not
re-reported:
- the Round 18 USB_LIMITED length: 63.605 mm in the record, 63.116 mm on the board;
- the U400 input feed outside K-power: 0.4 mm drawn, above the 0.385 mm IPC width.

## Coverage limits

- No transient, DC or thermal re-solve, and no re-run of the hot-plug or EN chatter models.
- The neck test is a raster approximation.
- No physical test.

Probes are in `.supervisor/r35_power/` (`caps.py`, `netcopper.py`, `export_poly.py`, `neck.py`, `kpower.json`).
