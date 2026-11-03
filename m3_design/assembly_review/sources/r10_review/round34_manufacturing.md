# R10 round 34 — manufacturing lens

Target `c2a11fd`, board `a0ec075e…` (SHA-256 before and after: `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c`).

**Totals: 0 Critical / 0 Major / 0 Minor real errors.**

## Findings
None.

## Fix verification
- R33-TRI-01 (ORDERING 8.3, U9 pads 5 / 6 / 9 beyond the body 0.15–0.25 mm): **confirmed** — pads 5/6 span 2.40 mm, 0.30 mm wide; pad 9 ends at x 19.70; body 1.9–2.1 mm centred at (18.5, 81.6).

## Observations (not counted)
- KiCad 10.0.7 DRC, all severities, schematic parity, on a copy with the project libraries and sheets: 0 violations, 0 unconnected, 0 parity; a copy without fp-lib-table gives 199 lib_footprint_issues warnings (test-setup artefact, as in round 33).
- Gerbers (11 layers), PTH / NPTH drill and job file re-exported from the board with export_fab.py's exact options are identical to m3_gerber.zip apart from creation-date lines; both assembly PDFs re-exported are stream-identical to the packaged ones.
- Drill: PTH 0.300 x 308, 0.500 x 1 (BAT_IN), 1.300 x 27 (DB125), 0.600 x 4 (J3 slots); NPTH 0.600 x 2, 0.991 x 3; matches ORDERING 8.1 (309 vias = 304 + 4 + 1; 308 holes in the 0.300 group).
- Least via hole-to-hole 0.259 mm (same net, GND), least different-net via pair 0.350 mm (3V3 / VCAP1 at (29.25,38.65)/(29.25,38.0)); records and DRU rules (vias 0.25 mm, pad holes 0.45 mm) already disclose this basis; not re-reported.
- Tracks >= 0.2 mm, vias 0.5/0.3 (ring 0.10), PTH ring >= 0.30 mm on DB125, least hole to board edge 0.775 mm, silk text >= 1.0 mm / 0.15 mm strokes (JLC legend minimum ruled met in round 28).
- BOM: 81 lines, 206 parts, each line's Qty equals its designator count, LCSC / MPN / value agree with the board fields for every part; owner BOM holds only C84 C46550466; no fitted part is missing from both BOMs.
- CPL: 206 rows (70 Top / 136 Bottom), same set as the BOM, every layer matches the board; only J430 (1.55 mm) and J3 (0.095 mm) carry recorded origin offsets.
- Content checks re-run read-only: S-4 OK, jlc_orient --verify-cpl OK (192 rebuilt + 14 placement-only, residual 0.491 mm), paste_check OK (249 / 381), fab_manifest OK (6 outputs bound to a0ec075e).
- Gate seeds on copies: one U401 B.Paste window removed -> paste_check FAIL; U4 CPL rotation 180 -> 0 -> jlc_orient FAIL ('rotation differs').
- U401 VIPPO paste: B.Paste windows 1.13 x 0.89 mm at Gerber Y -14.155 / -13.045 leave a 0.22 mm gap; the 0.3 mm drills at Y -13.6 overlap each window by 0.04 mm, as ORDERING 8.1 states.
- ORDERING 8.2 positions and rotations of all eight DB125, Q120/Q121/Q124, C126 and its via, C123, C411/C421/C431/C91/C92, C84 and its pads, D9 pads, U4, J430, L400 lands reproduce on the board.
- Bottom-part copper gaps to DB125 pads 1.762 (R13-J121.1) to 2.172 mm (U5-J121.1), matching '1.76-2.17 mm'; J3 slot gaps C83/R7/R8 1.952/2.010/2.146 mm; J440 GND partner vias 0.300 mm from J440.3/.4; D402 1.768/1.808 figures are M-6's courtyard basis (pad-copper gap 1.96 mm), consistent with the label.
- Short-edge courtyards: R400/R401/R404 1.025, C95 1.505, R166 1.755, C403 1.955 mm (the six recorded DFM queries); R92 2.525, TP88 2.555, L400 2.505 mm meet 2.5 mm.
- 14 parts without a Fab body (Q122, Q123, D120, D123, J2 none; U1-U5, D4, D121, Y1, J3 pin-1 dot only) and 93 hidden designators reproduce; 13 bottom pin legends reproduce.
- ORDERING 8.3 probe worksheet contacts (TP80-TP122, R119.1/R120.2/C120.2, C24, C15.1, TP74/TP88, C88.1, C82.1, R84.1, U9 pads), U5 pad extent, TP122 box, vias (24.3,66.0), (16.0,50.2), (27.0,49.25), BAT_ENABLE vias and Q120/Q121 gate vias reproduce.
- Cost / stock: 45 Extended + 36 Basic JLC codes (46 expand incl. C84), $60.47 + $24.79 = $85.26, +$16.79 = $102.05, +$2.99 = $105.04; cost file binds BOM 00af5358 / owner c48868b3 / CPL 1f899750; U4 2 orderable, U9 -81 / min 7, C2757925 and C535146 rows match ORDERING 8.1.

## Checks executed
- sha256 of the board before and after
- kicad-cli 10.0.7 pcb drc --severity-all --schematic-parity on a probe copy (with and without project libraries)
- kicad-cli gerbers/drill/pdf re-export with export_fab.py options into the probe directory, compared with the packaged zip and PDFs
- pcbnew read-only scripts geom.py, bomcpl.py, pos.py, probe.py, fab.py, edge.py, tht.py, silk.py, leg.py (in .supervisor/r34_manufacturing/)
- check_r10 --only S-4 --bom --cpl; jlc_orient --verify-cpl; paste_check; fab_manifest (read-only)
- drill-file tool counts; B.Paste flash parse at U401
- seeds on copies: paste window removed, U4 CPL rotation changed
- cost_check.json / stock_check.json arithmetic and bindings

## Coverage limits
- No live JLC DFM upload or quote; JLC's web capability page not re-fetched this round
- No physical inspection; spoke counts at GND THT contacts not re-read
- Did not re-derive every per-part CPL orientation beyond the jlc_orient reconstruction
