# R13 focused Fab-reference correction

Source is ready for the integrated build. This is a focused correction receipt, not another full review. Target commit `fa897c81abac3026e75ca5cc88bef0c2659a7130`; canonical PCB remains `7355ae1aeb1fdfdf6f64317945a0bf114d94c2bb65fb04adfbcd5a2b8037b09c`. Only `m3_design/r10_post.py` was edited; canonical post/build/check/PCB-save operations were not run.

The explicit 77-row override table fixes the complete native scan's 27 rectangular-border intersections,49 pin1-dot contacts and LS120's intersections with its own `+`/`-` texts. It runs after existing Fab placement, with no new runtime search/global shrink. All132 already-clear reference objects, including R12's R10/C29/C92/R8/C5, are preserved. Electrical/copper/fill/pad/model/footprint poses,all silkscreen/text content and every other object are exact.

Frozen `r10_post.py` SHA256: `94a467a2e823ca7e5160aceb7baf7d1f474b056ed54a608ee713690c6bf5eaeb`. Corrected SHA256: `13d953083d6673e806635536fb2facaea0f8e9077c9ec289d9a8f4637f23d21f`. Isolated candidate: `2c6b53beca6896655549d729c8f3ff6ca112d892b84190459e126394f66ff961`. Immutable full-review pair remains unchanged (hashes in JSON). Root owns integration and final hash/package refresh.

Validation:

- Native10.0.6 API:209 references/722 rendered characters (70top/139bottom);77 changed references/284 characters (17top/60bottom). Exact parsed native comparison changes only each named reference's position,font size/stroke;132 references and all non-reference objects match.
- Every reference tested against1018 Fab graphic primitives,all other reference glyphs,2 visible LS120 polarity texts and37 drill/cutout polygons. Zero positive intersections after the correction; every changed glyph also clears after0.025mm inflation. Polygon accuracy0.001mm; positive area threshold0.000001mm2. Every reference's ink stays inside46x90mm; every changed centre is nearest its own courtyard. The harmless native wxApp diagnostic is retained in ignored probe output; all final probe assertions and exits pass.
- Executing only the new helper on the frozen PCB reproduces the candidate byte for byte; executing it twice is byte-idempotent. Canonical source parses successfully; all existing functions are AST-identical after excluding the single new helper call. No full post-stage execution,zone refill,DRC/ERC/gate or build is claimed here.
- Official10.0.7 CLI version and sequential top/bottom PDF exports each exit0. Each PDF is one A4 landscape page. Both complete pages inspected at180dpi; all77 changed references inspected in five600dpi detail sheets. Full outlines/holes/map,labels,association and polarity marks are visually clear at those views. PDF hashes and commands are in the JSON; ignored outputs are under `.supervisor/r13_fab_fix_prepare/`.

Corrected sizes:49 at0.4mm,2 at0.5mm,12 at0.6mm,6 at0.7mm,7 at0.8mm,1 at1.0mm. The nine testpad references and LED1/2 use0.6mm; LS120 keeps0.8mm at `(23,59.7)`. Small Fab references require vector zoom/enlarged details. The two already-clear0.3mm labels C80/D8 remain unchanged; this does not establish readability at physical-size printing. Silkscreen's>=1.0mm rule is unchanged. The0.025mm geometric margin is not a printer/process guarantee. Complete600dpi board sweeps and physical tests were not performed.

The JSON contains per-reference old/new coordinates,height,stroke,angle/mirror preservation,baseline intersection areas and association distances. R13-MFG-02 L400 maker-land/first-article disposition is outside this correction and remains open. Full integrated build/gate,final assembly/fab exports,binding and manifest refresh remain root work before final closure; no manufacturing/firmware/physical qualification is claimed.

| Reference | Layer | Old centre mm / height mm | New centre mm / height mm | Baseline intersection |
| --- | --- | --- | --- | --- |
| C10 | B.Fab | (17.5, 54.1) / 1 | (17.5, 54.2) / 1 | Circle |
| C100 | B.Fab | (28.85, 39.97) / 0.4 | (28.8, 39.97) / 0.4 | Circle |
| C13 | B.Fab | (14.85, 50.1) / 0.4 | (14.8, 50.1) / 0.4 | Circle |
| C14 | B.Fab | (21.4, 52.15) / 0.4 | (21.4, 52.1) / 0.4 | Circle |
| C15 | B.Fab | (29.05, 47.4) / 0.4 | (29.15, 47.4) / 0.4 | Circle |
| C16 | B.Fab | (26.6, 36.62) / 0.4 | (26.6, 36.57) / 0.4 | Circle |
| C17 | B.Fab | (17, 37.9) / 0.4 | (16.95, 37.9) / 0.4 | Circle |
| C18 | B.Fab | (18.3, 49.15) / 0.4 | (18.3, 49.1) / 0.4 | Circle |
| C21 | B.Fab | (28.1, 49.25) / 0.4 | (28.1, 49.35) / 0.4 | Circle |
| C24 | B.Fab | (25.45, 49) / 0.4 | (25.55, 48.9) / 0.4 | Circle |
| C25 | B.Fab | (19.95, 47.7) / 0.4 | (19.95, 47.65) / 0.4 | Circle |
| C26 | B.Fab | (25.75, 45.5) / 0.4 | (25.75, 45.6) / 0.4 | Circle |
| C30 | B.Fab | (17.05, 48.73) / 0.4 | (17, 48.73) / 0.4 | Circle |
| C31 | B.Fab | (14.7, 47.07) / 0.4 | (14.65, 47.07) / 0.4 | Circle |
| C32 | B.Fab | (8.72, 45.85) / 0.4 | (8.82, 45.85) / 0.4 | Circle |
| C407 | F.Fab | (31.8, 19.5) / 0.8 | (31.8, 19.5) / 0.6 | Rect |
| C408 | B.Fab | (24.8, 13.6) / 0.4 | (24.8, 13.55) / 0.4 | Circle |
| C411 | B.Fab | (34.2, 22.75) / 0.8 | (34.2, 22.75) / 0.7 | Rect |
| C461 | F.Fab | (27, 18.8) / 0.8 | (27, 18.8) / 0.7 | Rect |
| C88 | B.Fab | (19.4, 83.95) / 0.4 | (19.5, 83.95) / 0.4 | Circle |
| C99 | B.Fab | (25.42, 66.9) / 0.4 | (25.42, 67) / 0.4 | Circle |
| D400 | B.Fab | (35.75, 43.7) / 0.8 | (35.9, 44.8) / 0.8 | Rect |
| D401 | B.Fab | (35.75, 47.2) / 0.8 | (35.75, 48.3) / 0.8 | Rect |
| D410 | B.Fab | (35.75, 12.3) / 0.8 | (35.8, 11.3) / 0.8 | Rect |
| D411 | B.Fab | (35.75, 8.7) / 0.8 | (35.75, 7.7) / 0.8 | Rect |
| D420 | B.Fab | (35.75, 31.2) / 0.8 | (35.75, 32.3) / 0.8 | Rect |
| D421 | B.Fab | (35.75, 27.7) / 0.8 | (35.9, 28.8) / 0.8 | Rect |
| LED1 | F.Fab | (8.95, 42.6) / 0.4 | (7.5, 42.6) / 0.6 | Rect |
| LED2 | F.Fab | (8.95, 46.5) / 0.4 | (7.5, 46.5) / 0.6 | Rect |
| LS120 | F.Fab | (23, 58.5) / 0.8 | (23, 59.7) / 0.8 | text |
| Q120 | B.Fab | (13.5, 73.6) / 0.8 | (13.5, 73.6) / 0.7 | Rect |
| Q121 | B.Fab | (13.5, 68.6) / 0.8 | (13.5, 68.6) / 0.7 | Rect |
| R104 | F.Fab | (33.2, 46.5) / 0.4 | (33.2, 46.65) / 0.4 | Circle |
| R105 | F.Fab | (33.2, 48.6) / 0.4 | (33.2, 48.55) / 0.4 | Circle |
| R11 | B.Fab | (14.2, 43.75) / 0.4 | (14.3, 43.75) / 0.4 | Circle |
| R12 | B.Fab | (7, 49.37) / 0.4 | (7.1, 49.37) / 0.4 | Circle |
| R120 | B.Fab | (18.5, 72.6) / 0.4 | (18.45, 72.6) / 0.4 | Circle |
| R121 | F.Fab | (14.5, 71.87) / 0.4 | (14.45, 71.87) / 0.4 | Circle |
| R122 | F.Fab | (19.6, 69.8) / 0.4 | (19.7, 69.8) / 0.4 | Circle |
| R123 | F.Fab | (20.6, 70.66) / 0.4 | (20.7, 70.66) / 0.4 | Circle |
| R127 | F.Fab | (19.8, 54.24) / 0.4 | (19.8, 54.19) / 0.4 | Circle |
| R128 | F.Fab | (18.3, 57.405) / 0.4 | (18.4, 57.405) / 0.4 | Circle |
| R129 | B.Fab | (23, 57.4) / 0.4 | (23.1, 57.4) / 0.4 | Circle |
| R13 | B.Fab | (10.25, 52.55) / 0.4 | (10.2, 52.55) / 0.4 | Circle |
| R130 | B.Fab | (23.43, 55.85) / 0.4 | (23.43, 55.95) / 0.4 | Circle |
| R131 | B.Fab | (10.8, 61.15) / 0.4 | (10.8, 61.25) / 0.4 | Circle |
| R132 | B.Fab | (28, 57.6) / 0.4 | (28.1, 57.6) / 0.4 | Circle |
| R133 | B.Fab | (28.43, 54.25) / 0.4 | (28.43, 54.35) / 0.4 | Circle |
| R154 | B.Fab | (32.45, 74.53) / 0.4 | (32.4, 74.53) / 0.4 | Circle |
| R155 | B.Fab | (30.55, 74.53) / 0.4 | (30.5, 74.53) / 0.4 | Circle |
| R156 | B.Fab | (30.55, 68.4) / 0.4 | (30.65, 68.4) / 0.4 | Circle |
| R157 | B.Fab | (32.45, 68.4) / 0.4 | (32.55, 68.4) / 0.4 | Circle |
| R163 | B.Fab | (21.8, 59.3) / 0.4 | (21.75, 59.3) / 0.4 | Circle |
| R173 | B.Fab | (23, 59.2) / 0.4 | (23.1, 59.2) / 0.4 | Circle |
| R175 | B.Fab | (28, 55.8) / 0.4 | (28.1, 55.8) / 0.4 | Circle |
| R178 | B.Fab | (23.43, 54.85) / 0.4 | (23.43, 54.95) / 0.4 | Circle |
| R180 | B.Fab | (28.43, 53.25) / 0.4 | (28.43, 53.35) / 0.4 | Circle |
| R432 | B.Fab | (35.7, 57.8) / 0.4 | (35.7, 57.95) / 0.4 | Circle |
| R60 | F.Fab | (33.2, 58.6) / 0.4 | (33.2, 58.7) / 0.4 | Circle |
| R61 | F.Fab | (33.2, 54) / 0.4 | (33.2, 53.95) / 0.4 | Circle |
| R62 | B.Fab | (25.5, 55.7) / 0.4 | (25.5, 55.8) / 0.4 | Circle |
| R63 | B.Fab | (25.5, 56.7) / 0.4 | (25.5, 56.65) / 0.4 | Circle |
| R64 | B.Fab | (11.23, 52.28) / 0.4 | (11.18, 52.28) / 0.4 | Circle |
| TP120 | B.Fab | (18, 68.6) / 0.8 | (18, 67.45) / 0.6 | Rect |
| TP121 | B.Fab | (10.355, 71.455) / 0.3 | (10.5, 70.35) / 0.6 | Rect |
| TP122 | B.Fab | (13.3, 53.3) / 0.4 | (13.3, 52.15) / 0.6 | Rect |
| TP74 | B.Fab | (42.5, 58) / 0.4 | (42.5, 56.85) / 0.6 | Rect |
| TP80 | F.Fab | (9.8, 83.8) / 0.8 | (9.8, 82.65) / 0.6 | Rect |
| TP81 | B.Fab | (31, 84.8) / 0.8 | (31, 83.65) / 0.6 | Rect |
| TP82 | B.Fab | (10.8, 21.3) / 0.4 | (10.8, 20.15) / 0.6 | Rect |
| TP83 | B.Fab | (34.5, 81.5) / 0.8 | (34.5, 80.35) / 0.6 | Rect |
| TP88 | F.Fab | (35.5, 87) / 0.8 | (35.5, 85.85) / 0.6 | Rect |
| U10 | B.Fab | (12.6, 27.5) / 0.8 | (12.6, 27.5) / 0.5 | Rect |
| U11 | B.Fab | (24.65, 64.5) / 0.8 | (24.65, 64.5) / 0.7 | Rect |
| U12 | B.Fab | (31.6, 39.8) / 0.8 | (31.6, 39.8) / 0.7 | Rect |
| U13 | B.Fab | (31.85, 49.7) / 0.8 | (31.85, 49.7) / 0.5 | Rect |
| U400 | F.Fab | (16.9, 5.55) / 0.8 | (16.9, 5.55) / 0.4 | Rect |
