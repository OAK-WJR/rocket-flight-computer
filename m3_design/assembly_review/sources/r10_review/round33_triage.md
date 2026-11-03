# R10 round 33 triage

Target `feed21f`, board `a0ec075e…` (SHA-256 before and after: `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c`).
Ten lens reports read; nine reported 0 real errors, docs_binding one Minor.

**Totals: 0 Critical / 0 Major / 1 Minor real error; no board change. 11 observation groups; 0 not reproducible.**

## R33-TRI-01 (doc, Minor; board_change false). Merges R33-DOCS_BINDING-01 and docs_binding observation 0
ORDERING 8.3 says U9's pads 5 / 6 "expose only 0.10 × 0.30 mm beyond the body at each end" and that "pad 9 itself is
under the body". Measured on the board (pcbnew, `.supervisor/r33_triage/u9.py`): pads 5 / 6 span y 80.40–82.80, pad 9
spans x 19.10–19.70; the B.Fab body centreline is 17.45–19.55 / 80.55–82.65 (2.10 mm; bounding box 17.40–19.60 includes
the 0.10 mm line). TI SLVSFC9C RPW0010A (4225183/A): body 1.9–2.1 mm. So pads 5 / 6 expose 0.15–0.25 mm (0.20 nominal)
× 0.30 mm at each end, and pad 9 extends 0.15–0.25 mm beyond the body. Round 23 read the Fab line's outer edge as the
body. The probe points and the R84.1 instruction stay right.

- Places: `docs/ORDERING.md:552`, `docs/ORDERING.md:555`. Origin (frozen history, not edited):
  `round23_docs_binding.md:55`, `round23_docs_binding.json:82`. Sweep (`git grep` for the figure, "beyond the body",
  "under the body", "exposed pad", the 17.40–19.60 box): no other current statement.
- Fix: line 552 "expose 0.15–0.25 mm (0.20 mm nominal; RPW0010A body 1.9–2.1 mm, SLVSFC9C) × 0.30 mm beyond the body
  at each end"; line 555 "(R84 750 Ω, BAT_ILIM; pad 9 exposes only 0.15–0.25 × 0.25 mm beyond the body)". Text only.

## Root-flagged observation
- MCU obs 3 (parts_qualification:949 cites the PA6 4.0 V limit to Rev 11 without an Inference label): **observation**.
  The value was read from the maker datasheet Rev 11 and is cited as Rev 11; it claims nothing for Rev 8, so AGENTS §2.5
  is not breached. The Rev 8 applicability labels are where Rev 8 is claimed (M3_R10:547–548, R10_VALIDATION:2902, the
  binding note), and M3_R10 already names these two Rev 11 limits.

## Other observations (not counted)
Safety 0–6, power 0–16, routing 0–14, MCU 0–2 / 4–6, gate 0–10, parts 0–2, mechanics 0–9, manufacturing 0–14,
requirements 0–6, docs_binding 1–5: reproduced or consistent with the records, disclosed, or already ruled in rounds
24–32. Rechecked on their face: safety 6 (M3_R10:650's J121.2 2.1–2.2 mm is the stated wall basis; the 1.902 mm ring
also clears 1.0 mm); requirements 0 ("about 1.7 W, 0.23 A": 1.66 W rounds to 1.7 W and 1.7 / 7.4 = 0.23 A, labelled
Inference). Neither meets the definition.

Round 33 has one real error, so it is not a clean round; the closing pair moves to rounds 34 and 35 (the board is
unchanged).
