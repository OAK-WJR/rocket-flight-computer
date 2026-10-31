# Round 18 power and electrical review (Claude)

Target commit `dcbb6c8f040b7012f78934e1caf1b401db84d356`. PCB SHA-256 was
`632a9ad36c19426ede219b6ff6b0d638955665cac1b4704d3392a6afdbe03982` before and after the review.
**Result: 0 Critical / 0 Major / 3 Minor (all new).** [Structured evidence](round18_power.json).

## Findings

**R18-PWR-01 (Minor): the In2 3V3 plane fills as three pieces.** The native fill of `R10_3V3_In2` has
three outlines: 1354.23, 63.11 and 30.54 mm². Every other plane is a single fill. The In2 USB_LIMITED route
(63.6 mm) encloses island A, at (17.71–25.75, 51.3–61.35). Island A feeds R164 (the 3V3 to 3V3A filter for U4,
U5 and VDDA/VREF+), the buzzer LS120/D123, the cold pull-up D120 and R62. It reaches the main 3V3 region through
only one link: a 0.30 mm, 4.74 mm B.Cu track between vias (19.5,49.15) and (22.6,52.15). DC solve gives L1.2 to
R164.1 32.83 mΩ, all of it through that link. Island B carries only U2's FB sense, taken from the L1 pad. All buck
output reaches the main plane through one via pair, at (26.4,79.26) and (30.8,79.26). Calculated buzzer ripple at
3V3A is about 1–2 mV, so no failure is demonstrated; the defect is a single-link analog source and a fragmented
plane. Fix: re-plan In2 so 3V3 is one region, or add a second link plus a local bypass at LS120. Another lens
also reports the split; see the disclosure under Limits.

**R18-PWR-02 (Minor): the USB-only budget is undocumented and over the limit.** The allocation is 1.4 W of logic
plus 0.825 W of SD writes at the converter input. On USB power that draws 0.460–0.486 A at VBUS 5.00–4.75 V. U10's
R85 sets IOS to 0.348–0.453 A, so demand exceeds the whole band. At IOSmin the guaranteed input is about 1.61 W.
The current records cover only the zero-load startup charge. This is bench mode only (brownout or reset loop under
USB-only logging) and has no flight effect. Fix: add the budget to the records, plus a rule to run full-load or SD
tests on pack power with the e-match disconnected, or a firmware cap keyed on LOGIC_SOURCE_ST. No CAD change.

**R18-PWR-03 (Minor): stale component contract.** `parts_qualification.md` (l.548–551, 589, 630–635, 696–699,
755–762 and 771–773) still describes U410/U420/U411/U421 and R410/R420 as fitted. It states "two at LDO output",
but the board has 4 × 22 µF there. It claims "two shorted ports 0.762 A < 1 A", whereas a shared PORT_4V8 short
reaches U401's 1.5–1.9 A limit. Its camera-loop split is the GH-era one. Measured board supply copper is 36.07 mΩ
(PORT_5V3) plus 17.06 mΩ (CAM_5V), totalling 53.1 mΩ, against the stale 14 mΩ. Fix: label these sections
historical, or rewrite them for the current topology.

## Executed evidence

- **Pin maps:** checked against the maker pin tables for U9, U11, U2, U400, U401, U402, U10 and U13.
- **Recomputed values:**
  - U9: UVLO 4.96 V, OVLO 9.77 V, ILIM 4.445 A, dVdt 0.426 V/ms.
  - U11: ILM 1.49 A, OV1 trip 5.76–6.27 V.
  - Regulator bands: 5.367–5.546 V and 4.712–4.873 V.
  - Switch limits: camera 1.041–1.250 A, USB 0.348–0.453 A.
  - Inductors: L400 Isat 4.3 A against a 3.1 A converter limit; L1 rated 2.9 A against 3.1 A, which matters only at
    a fault.
  - Hold-up: 0.490–0.571 ms.
- **DC solves of the power copper:** every continuous neck is ≥ 1.0 mm, with IPC rise ≤ 5.1 °C at 1.5 A.
- **Hot-plug model:** it models the correct reverse circuit. My probe harness reproduces the canonical extrema
  exactly. A new forward-polarity sweep of all 2304 cases gives at most 13.796 V, 3.855 V/µs falling and
  7.090 V/µs rising, well inside TI's limits.
- **Reverse-polarity pin currents:** EN 6.7 µA and OVLO 5.4 µA, both under TI's 10 µA.

## Limits

- No DRC run, no full gate run, and no physical tests.
- Converter stability was judged from guidance, not modeled.
- **Disclosure:** an earlier-rounds grep also printed three lines of `round18_routing.md` (including its
  plane-split title) and listed `round18_safety.md` by name. I opened neither file. My island result came from my own
  fill extraction, which I ran before that grep.
