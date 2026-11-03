# R10 round 29: requirements lens

Target commit `09a564e`, board `a0ec075e…`. The board SHA-256 was the same before and after the review:
`a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c`. The review was read-only; probe scripts are in
`.supervisor/r29_requirements/`.

## Totals

| Critical | Major | Minor |
|---|---|---|
| 0 | 0 | 1 |

## Findings

### R29-REQUIREMENTS-01 (doc, Minor): the hot-end requirement and its test cover only 85 °C parts, but LS120 is a +70 °C part

**What the records say.**
- The REQUIREMENTS Temperature row sets the bay at −20…+70 °C.
- It judges hot-end ratings against part temperature, using a board rise of +10–22 K over bay air at the pad load
  (Inference).
- It then protects only the 85 °C parts: an interim limit of bay air ≤ 55 °C, and a first-article 70 °C chamber test
  that passes when "every 85 °C part ≤ 85 °C".
- ORDERING 8.3 (line 608), owner row 33 (R10_VALIDATION:2405) and M3_R10:472–475 say the same.

**The datasheet.** The fitted buzzer LS120, MLT-5020 (C94598), is rated −20～+70 ℃ operating
([datasheet](https://datasheet.lcsc.com/datasheet/pdf/23f5c6599ed9cb614c21ac31ad2b1106.pdf?productCode=C94598) p2, item 6;
storage is +85 ℃). It must operate on the pad: F11 makes it the pad annunciator, and F12 the post-landing locator.

**Calculation**, using the row's own Inference:

| Bay air | LS120 temperature (bay + 10–22 K) | Against the 70 °C rating |
|---|---|---|
| 70 °C (the stated bay) | 80–92 °C | 10–22 K over |
| 55 °C (the interim limit) | 65–77 °C | up to 7 K over |

- With no rise at all, a 70 °C bay is already at the limit.
- The chamber test holds LS120 above its rating for the whole run and never checks it.
- The same arithmetic the row uses for the 85 °C parts gives about 48 °C bay air for a 70 °C part.

**Not raised before.** R23-PARTS-01 noted "LS120 +70 C (already recorded)", but its fix covered only the 85 °C parts.
The current records mention LS120 only for its −20 °C cold end, and no round 24–28 triage observation covers its hot end.

**Fix** (text only):
- List LS120 as a +70 °C part.
- Add "LS120 ≤ 70 °C, thermocouple on LS120" to the chamber-test pass criterion.
- State that LS120 is out of rating at a 70 °C bay. Then either set the buzzer's interim limit to about 48 °C bay air
  (Inference), or have the owner accept the buzzer as best-effort above 70 °C.
- Alternatively, fit a +85 °C buzzer on the same land at the next board change.

## Fix verification (round 28, this lens)

| Item | Verdict |
|---|---|
| R28-TRI-07: F4 hinge, 64–84 %, 77–84 % nominal to high | Confirmed: L1000W 63.9–84.3 %, nominal 77.47 %, high 84.33 % |
| R28-TRI-08: stale 525 s | Confirmed: the only remaining 525 s is the labelled superseded estimate |
| D-R28-01: pack sag | Confirmed: REQUIREMENTS quotes none of the changed figures |
| D-R28-04: F9 port-supply lead | Confirmed: 20.8–26.3 ms; 166–196 V/s is SLVSEA3F Table 9-1 p13 scaled to 470 nF; U400 is fed ahead of U11 |
| §2.5 labels on the F8 cold screen and on F4 / F6 C87 | Confirmed: 99.369 / 99.338 / 146.23 mV and every EN figure reproduced |

## Observations (not counted, 14)

- **F4 hinge, flight 1.** The K850DM cases reach up to 85.0 % (at M1.17), but F4 makes no flight-1 claim, and flight 1
  has one servo.
- **Envelope.** Every figure in the derived envelope, F3's 8.8 km / about 317 hPa, F1's apogee temperatures and the
  35 s window, and F5's 2–3.5 MB log size are reproduced.
- **P3 chute naming.** P3's "flat" 36 in chute uses the model's Cd 1.5, which the model and the parent notes call
  "elliptical". This is unsourced and labelled Inference, so it is not a finding.
- **Board position.** The stack arithmetic against VEHICLE.md is reproduced: joint + 79.4–83.4 mm.
- **EN model.** An independent worst-corner model reproduces every F4 / F6 single-drop-out, train, window and
  trip-fraction figure. The nominal EN timing, D402's 5.7 mV, the ESD 7.5 / 9.6 V and the Pack row's 4.802 V are
  reproduced too.
- **Fire budget.** 1.541 / 1.476 / 1.279 A and 5.713 V re-solved. The hold-up figures are reproduced.
- **Requirement-to-board map.** All confirmed on the board:
  - F4: servo outputs;
  - F5: microSD;
  - F7: fire-path widths, with seven 0.4 mm bridges;
  - F8: gate networks, dividers, BAT_SW_RETURN membership, colours and every legend;
  - F9: D402 tap 4.114 mm and its GND via at 0.700 mm, and C88 feeding U9 first;
  - F10 and F11: pins;
  - P1 and P2: outline, holes and land distances;
  - P3: no MEMS under-body via or fill.
- **F8 / F9 figures.** Cold-screen, one-fault 3.342171 V / 1.397 mA, and Q122 0.218 V are reproduced.
- **Cold end.** The bay can fall below −20 °C in descent; this is already R23-REQUIREMENTS-08.
- **U9 turn-off at board temperature.** At bay + 22 K the turn-off corner extrapolates to about 4.85 V, above PA6's
  4.84 V lower edge. The records already disclose this as unqualified.
- **Supplier figures.** M1 / M3 match stock_check.json and cost_check.json. M3's "about $102–$105" is right on the
  $85.26 basis and ambiguous only if the minimum-purchase figure is meant.
- **Silkscreen.** All 167 visible texts are 1.0 mm high with 0.15 mm strokes.

## Coverage limits

- I did not run DRC, route_check or check.sh.
- The chute Cd is not verified against a citable source.
- LS120's own temperature rise is not modelled beyond the records' board-level Inference.
