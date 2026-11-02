# R10 round 25 — mechanics lens (Claude)

- Commit `c4bb56b`; board SHA-256 `92c3ad59…` before and after (unchanged).
- Totals: **0 Critical / 0 Major / 2 Minor** (real errors only). JSON: `round25_mechanics.json`.

## Findings

- **R25-MECHANICS-01 (doc, Minor).** `docs/M3_R10.md` line 874 and `docs/R10_VALIDATION.md` line 2709 say R150–R155
  are "still missing" from the plate tool's strain table. They have been in `tools/plate_model.py` `STRAIN_PARTS`
  since round 19 (commit 2ca63a1; R10_DECISIONS line 3199). This round's run reports 1336–1420 µε for them
  (100 g, D5 pinned). Fix: say they were added in round 19.
- **R25-MECHANICS-02 (doc, Minor).** ORDERING 8.4 (line 699) offers "4.5 mm standoffs with a plate ≤ 0.8 mm (keeps
  h + t < 5.3 mm at x 3.7)". 4.5 + 0.8 = 5.3 mm, which is not below the strict 5.3 mm bound in M3_R10 857 / 911,
  HANDOFF 76 and R10_VALIDATION 2938. The exact bound is 5.365 mm, so the part fits physically; the statement is
  what's false. Fix: write "plate < 0.8 mm", or state the bound as ≤ 5.3 mm inside 5.365 mm (in all four places that
  give the option).

## Fix verification

- R24-TRI-08 (98–163 g): **confirmed**. 6.2 m/s gives 98.0 g, 8.0 m/s gives 163.2 g, and no live "168 g" remains.
- R24-TRI-09 (J2 lands at 3.880 / 3.987 mm, range 3.808–3.987 mm, 0.31–0.49 mm to the washer edge): **confirmed**
  in all five documents.
- D-R24-11 D402 at B(4.45, 65.9): **confirmed**. Bore margin 5.60 mm; no support conflict; plate figures unchanged.
- D-R24-15 R92 / TP88 moves: **confirmed**. TP88.1 is 5.75 mm from the (42, 86) support.

## Checks

- **fit_check.py (r10).** OK. 216 footprints (207 rows + 9 bare features). Worst margin is J3 at 0.886 mm, and the
  terminals have 2.976 mm. Wire room is 5.003–5.603 mm on all eight DB125. The nearest bottom envelope is C32.2 at
  4.536 mm, and the nearest top land is LED2.2 at 3.808 mm.
- **plate_model.py (r10) on 92c3ad59.** 180.8 Hz pinned D5 for 78.6 g, matching the records. The other figures
  (255.6 / 287.8 / 407.0 Hz, 1.27 mm) are the same on 5516eeec and 1407e850. The records label 256.1 / 287.9 /
  407.1 Hz and 1.24 mm as 632a9ad3 figures.
- **Contact at 4 mm standoffs (D5).** C431 125 g, C421 132 g, J9 tails 162–167 g, C411 174 g, L1 213 g. The pocket or
  4.5 mm standoffs clear all of them past 163 g.
- **Support holes.** Five Ø3.2 mm support holes at the recorded centres. Copper on all four layers stops 0.5 mm from
  each hole edge.
- **Hand checks.** Nut-stack bounds 6.018 / 5.365 mm; L1 gap 0.984175 mm.

## Observations

7, in the JSON. Among them: row 32's wording "above the 125 g", and the J9 / J420 tails missing from ORDERING's
contact list (both covered by the vehicle item).
