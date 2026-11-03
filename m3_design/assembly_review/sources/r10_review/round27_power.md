# R10 round 27 — power lens (Claude)

Target commit `816038c`, board `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c` before and after
(sha256 checked both times; git status clean). Read-only; probes in `.supervisor/r27_power/`.

**Totals: 0 Critical / 0 Major / 3 Minor.** Machine-readable copy: `round27_power.json`.

## Findings

### R27-POWER-01 (doc, Minor): the TCR pair is not "computed at 5.73 V, not re-run at 5.71 V"
- **What is wrong.** `docs/R10_VALIDATION.md` lines 2181–2182 (round 26 index, observations) say "7.31 / 7.18 ms at 70 °C,
  computed at 5.73 V, still above 7 ms; not re-run at 5.71 V". `round26_fix_docs.md` item 5 says the same.
- **What it contradicts.** The pair's source, `round26_safety.md` line 68 and `round26_safety.json`, gives 7.31 ms at
  5.73 V and 7.18 ms at 5.713 V.
- **Evidence.** I re-ran the worst-corner EN model with the resistor tolerance widened to ±1.45 % (1 % plus 100 ppm/K ×
  45 K), C87 at 0.72 × 220 nF, 0.1 µA plus 50 nA leakage, 1.116 V threshold, one open block per 100 ms
  (`tcr.py`). It gives 7.309 ms at 5.73 V and 7.183 ms at 5.7132 V. The same model gives 7.629 / 7.503 ms at the 1 %
  corner, which reproduces D-R26-03.
- **Impact.** The figure at the 5.71 V bench voltage exists (7.18 ms, 0.18 ms above the 7 ms line), but the index
  says nobody computed it.
- **Fix.** Write "(7.31 ms at 5.73 V and 7.18 ms at 5.71 V, at 70 °C; still above 7 ms)" in R10_VALIDATION and in
  round26_fix_docs.

### R27-POWER-02 (calc, Minor): parts_qualification's GAP-3 thermal paragraph uses the pre-AUX allocation
- **What is wrong.** `parts_qualification.md` lines 673–686 are in the current section "Voltage, current and thermal
  budgets", which says it reports `parts_budget.json`. The paragraph uses "allocated 460 mA output … 0.406177 W". From
  that it gives a junction of 102.494–114.679 °C at a 70 °C bay, 117.494–129.679 °C at 85 °C, and a 135.409 °C/W
  ceiling.
- **What it contradicts.**
  - Since D-R19-14 the allocation includes the 100 mA AUX allowance.
  - `r10_parts.py` line 516 computes (buck_max − ldo_min) × (0.46 + aux_A) + buck_max × 0.004 = 0.48965 W.
  - `parts_budget.json` gives a junction of 109.17–123.86 °C at 70 °C and 124.17–138.86 °C at 85 °C.
  - The ceiling is (125 − 70) / 0.48965 = 112.32 °C/W.
  - M3_R10 line 710 and R10_VALIDATION line 2558 already state 0.490 W and up to 123.9 °C.
- **Impact.** The contract shows 25 °C/W of headroom over the inferred 110 °C/W. The real headroom is 2.3 °C/W.
- **Fix.** State 560 mA (GPS 150 + radio 300 + AUX 100 mA), 0.490 W (0.406 W before the AUX allowance), 109.2–123.9 °C
  at 70 °C, 124.2–138.9 °C at 85 °C and a 112.3 °C/W ceiling.

### R27-POWER-03 (doc, Minor): the In2 3V3 fill is 1430.05 mm², not 1466.52 mm²
- **What is wrong.** `docs/M3_R10.md` line 712 sits in the Power section, whose lead-in says it holds current facts. It
  says "The In2 3V3 fill is one piece, 1466.52 mm²".
- **Evidence.**
  - On `a0ec075e…` the 3V3 In2 fill is one outline of 1430.05 mm² (pcbnew filled polygons, `area.py`). check_r10
    K-plane reports the same (`k_power_plane.json`).
  - It was 1431.06 mm² on `92c3ad59…`.
  - 1466.52 mm² was D-R18-06's figure on its own board (round19_power line 58).
- **Impact.** The section states a stale area as current. No rule depends on it.
- **Fix.** "1430.05 mm² on `a0ec075e…` (1466.52 mm² when D-R18-06 joined it)".

## Fix verification

| Change | Measurement | Verdict |
|---|---|---|
| D-R26-03 | **Four-stall point:** 5.7132 V (typical-hot FETs 5.7112 V).<br>**Chatter at 5.71 V:** single drop-out 8.067 ms; window limit 7.503 ms; margin 0.50 ms; the 7 ms line holds down to 5.6465 V; EN at the 7 ms line 1.12954 V.<br>**Fractions:** fast-chatter 19.716 %; periodic 19.6 / 18.6 / 17.4 / 14.8 / 11.4 / 4.5 %.<br>**5.73 V check:** the late-block train reaches 1.11677 / 1.11623 V at 7.6 / 7.62 ms.<br>**Exchange identity:** 0.17625 V.<br>**Rule 8:** 5.7132 / 5.5555–5.5576 / 5.5085 V; 5.37 V would need 13.53 A.<br>**Text:** the generated text is byte-identical to the binding note, and every current doc quote uses 5.71 V. | confirmed |
| D-R26-02 / -04 (power) | **Placement:** C11 (17.5, 51.45), C10 (17.5, 53.5) and R164 (17.325, 55.25), all on B.Cu.<br>**3V3A trunk:** 0.25 mm.<br>**3V3 vias:** (19.55, 55.825) and (9.2, 52.55) both land in the one-piece In2 3V3 fill.<br>**Necks:** 0.549 / 0.549 / 0.589 / 0.706 mm, unchanged.<br>**Checks:** K-power passes; F9-1 binds the hot-plug model to `a0ec075e…` with the extremes unchanged. | confirmed |
| D-R26-01 (power) | The two partner vias sit in the In2 3V3 fill. The fill stays one piece (1431.06 → 1430.05 mm²) and K-plane passes. | confirmed |

## Observations (not counted)

**Chatter and rule 8 figures**
1. All of D-R26-03 reproduces from `parts_budget.json` with an independent EN model (figures above).
2. **Rule 8 corner at the R134 floor.** With R134 at its 1.98 Ω floor the corner is 5.550 / 5.501 V, which still rounds to the stated figures.
   - With every FET and allowance set to zero it is 5.48 V.
   - Its VLOGIC, about 5.32 V, stays above PA6's 5.27 V top edge.
3. Every current quote of the chatter and rule 8 figures uses 5.71 V; checked in AGENTS, STATUS, REQUIREMENTS F4 / F6 / 106, M3_R10, ORDERING 8.3, the handoff, R10_VALIDATION rows 21 / 25 and §4, parts_qualification, and the binding note. The remaining 5.73 V figures are dated history.
4. **Other EN figures reproduce:**
   - turn-on 30.3–130.3 ms, and the nominal 88 / 56 / 45 ms and 19 / 33 / 41 ms;
   - pack window on 4.72–5.25 V, off 4.29–4.80 V;
   - Pack row 4.802 / 4.835 / 4.875 V;
   - a single 10 ms drop-out needs 5.9556 V;
   - F4's 1.088 V; the 3 × 4 ms train 1.028 / 1.025 V; 8 ms / 50 ms at 6.0 V gives 1.095 V.
5. Hold-up figures reproduce: from the trip 0.103–0.164 / 0.291–0.430 ms (0.22–0.31 of the break hold-up); from the break 0.464–0.539 / 1.304–1.412 ms.
6. The upper end of VLOGIC's "0.09–0.16 V" drop reproduces. The lower end depends on on-resistance and load assumptions, and only the upper end affects the PA6 margin.
7. **Rule 4's ratio.** "0.93–1.01×" also covers round 23's −20 °C and Q120-removed variants, and 1.128 / 1.063 A reproduce from the current budget.

**Rails, widths and hot-plug**

8. **Gates on `a0ec075e…`.** K-power, K-plane, K-width, S-9, K-binding, K-fill and F9-1 all pass.
   - IPC-2152 floors are met on all 14 paths.
   - Single-via regulator taps occur only at the listed exceptions.
   - The EN via (17.10, 82.80) is the owner's respin item.
9. All 3V3A copper is 0.25 mm. R164's and R13's 3V3 straps are 0.2 mm. These carry a few mA, and no rule names a 3V3A design current.
10. **Hot-plug.**
    - The model is bound to `a0ec075e…` and all 2304 rows pass.
    - Extremes: −14.807373 V; 8.994764 / 5.087664 V/µs; 579.049 W / 2.979359 mJ.
    - Retained output: 5.914 V at 1643.90 µF, as M3_R10 states.
11. **Rail nominals and limits reproduce:**
    - PORT_5V3 5.456 V and PORT_4V8 4.792 V;
    - OVLO 10.18 V;
    - U10 limit 0.3477–0.4530 A;
    - USB-only draw 0.4596 A.
12. U400's RAW_PROTECTED input (0.4 mm F.Cu) is not a K-power path. That width carries about 2.14 A at a 30 °C rise, against about 1.8–2.1 A of input at the low-pack corner.
13. In2 3V3 has a pinch of about 0.47 mm to a 14 mm² dead-end finger with no landing. K-plane ignores such pieces by design, and M3_R10's "about 0.50 mm" approximates the pinch.

**Stale but labelled, or legacy text**

14. parts_qualification's "Inference, stall input" (5.921 / 4.436 V) is pre-AUX; the budget gives 5.899 / 4.414 V. The paragraph also cites superseded port enables, so it reads as legacy text.
15. M3_R10's USB-only bullet uses a 63.605 mm USB_LIMITED track; it is now 63.115 mm. The bullet is labelled as a Round 18 calculation.
16. The four-stall model lumps the board's own battery lead into the 0.15 Ω source resistance, as REQUIREMENTS Pack defines it.
17. R10_VALIDATION line 2933's old R164 via figures are in its historical round 10 section.

## Checks executed
- **Calculations (scripts in `.supervisor/r27_power/`):** the independent EN model (`en_model.py`), the rule 8 corner (`corner.py`) and the TCR sensitivity (`tcr.py`).
- **Selected check_r10 rules, read-only:**
  - on the committed board: K-power, K-plane, F9-1, K-width, S-9, K-binding and K-fill;
  - on `3d8e845`'s board copy: K-plane, for the before figures.
- **Board and model reads:** pcbnew dumps of pads, copper, poses, In2 areas and a deflation neck scan; the hot-plug results read back.
- **Text checks:** a byte comparison of the binding note against the generator, and a doc grep for every old and new figure.

## Coverage limits
- No full `tools/check.sh`, DRC or route_check on the canonical tree.
- The hot-plug model was not re-run.
- U9 / U11 on-resistances came from round 26's triage bounds.
- I did not open the other lenses' round 27 reports.
