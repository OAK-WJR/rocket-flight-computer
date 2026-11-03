# R10 round 33: manufacturing lens

Target `feed21f`, board `a0ec075e…` (SHA-256 identical before and after). Reviewer: claude. Read-only; probes in `.supervisor/r33_manufacturing/`.

**Totals:** 0 Critical / 0 Major / 0 Minor. No real errors found.

## Findings

None.

## Fix verification (round 32, this lens)

- R32-TRI-01 (ORDERING 8.2 R166-to-C84 courtyard gap): ORDERING 8.2 now reads 0.65 mm centreline / 0.60 mm outer edges; R166 courtyard bbox y >= 84.355 with C84's upper edge near 83.75 (centreline), matching the triage figures. **confirmed**.
- R32-TRI-02 (R10_VALIDATION hand-solder sentence): ORDERING 8.2 C84 heat-limit text sets top-only heating, bottom supported on a heat-sinking fixture, minimum dwell and a recorded tip temperature and time, with no preheat or temperature limit. **confirmed for the ORDERING side; the R10_VALIDATION wording is outside this lens and was not re-read**.

## Observations (not counted)

- KiCad 10.0.7 DRC, all severities, schematic parity, on a copy with project libraries: 0 violations, 0 unconnected, 0 parity. A copy without fp-lib-table gives 199 lib_footprint_issues warnings, a test-setup artefact only.
- Design minimums: track 0.20 mm, vias 0.5/0.3 (304), 0.6/0.3 (4), 1.0/0.5 (1); min PTH annulus 0.30 mm (J440.1); plated slots 0.6 mm; silk text >= 1.0 mm / 0.15 mm stroke. All inside JLC's published capabilities.
- PTH drill file: T1 0.300 x308, T2 0.500 x1, T3 0.600 slots x4 (J3 shell), T4 1.300 x27 (DB125 contacts). NPTH: 0.600 x2 (J3 locators), 0.991 x3 (J2). Matches the board and ORDERING 8.1's 308-hole 0.3 mm group and 309-via counts.
- Five M3 supports are Edge.Cuts circles of r = 1.6 mm at the five documented centres (milled holes; listed as an expected DFM query in 8.2).
- Paste Gerbers 249 top / 381 bottom flashes; fab_manifest --content passes (S-4, CPL rebuilt 67 + 125 + 14 placement-only, worst residual 0.491 mm, paste). Manifest binds six outputs; BOM 00af5358, owner BOM c48868b3, CPL 1f899750 match cost_check bindings quoted in 8.1.
- BOM 81 codes / 206 refs with Qty = ref count on every line; CPL 206 rows (70 top / 136 bottom); every row's LCSC and Manufacturer Part matches the footprint fields; every fitted footprint is in the JLC or owner BOM; the 9 excluded footprints are 8 test pads and J2.
- CPL positions match footprint origins within 0.3 mm except J430 (dy 1.55 mm), which is the recorded jlc_corrections.json centroid offset for C164170.
- U4 lands 0.575 x 0.35 mm at 0.5 mm pitch, mask relief 0: web 0.150 mm; paste aperture 0.5405 x 0.329 mm = 88.4 % of land, as 8.2 states.
- Bottom-part copper gaps to DB125 pads 1.762 (R13 at J121) to 2.172 mm (U5 at J121), matching 8.2's 1.76-2.17 mm and its per-terminal lists; J440.3 / J440.4 to their GND vias 0.30 mm; J3 slot gaps C83 / R7 / R8 1.952 / 2.010 / 2.146 mm. D402's 1.768 / 1.808 mm are M-6 courtyard-to-pad figures, as labelled.
- Short-edge courtyard distances R400 / R401 / R404 1.025, C95 1.505, R166 1.755, C403 1.955 mm, next L400 2.505 mm: the six recorded DFM exceptions and nothing else under 2.5 mm.
- 14 parts without Fab body outline and 93 hidden designators match 8.2. 13 bottom pin legends match the 8.2 list.
- All 8.2 terminal and part position / rotation rows and all 8.3 probe-worksheet contacts (TP80-TP122, R119.1, R120.2, C120.2, C24, C15.1, C88.1, C82.1, R84.1, U9 pads 5/6 ends, J2) match the board, and so do the vias (24.3,66.0), (16.0,50.2), (27.0,49.25), (17.1,82.8), (19.675,66.6), (21.3,68.9), (27.3,13.6) and (27.9,13.6); the two U401 vias are the only filled and capped ones.
- 8.1 cost arithmetic reproduces from cost_check.json: 81 x $1.53 / 5 = $24.79; $60.47 + $24.79 = $85.26; $61.01 + $24.79 = $85.80; + $16.79 = $102.05; + $2.99 = $105.04.
- 8.3's C84 presence criterion: (376-564) + 2 x (17.6-26.4) uF = 0.41-0.62 mF; without C84 0.035-0.053 mF; 0.3 mF threshold separates them.
- J440 Fab rectangle ends at y 23.30 and its courtyard at 23.675; 8.4's 23.45 mm body end comes from the fit_check maker body (round 27 triage), and the y < 23.5 lead rule holds against it.

## Checks executed

- shasum -a 256 board before/after
- kicad-cli 10.0.7 pcb drc --severity-all --schematic-parity on a probe-dir copy with libraries
- pcbnew geometry probes (geo, edge, via, cpl, ex, pos, dist, probe, u4, u9, misc, j440, j3 .py in .supervisor/r33_manufacturing/)
- Gerber zip unpacked; drill tool/hit counts, paste/mask flash counts, U4 paste apertures
- tools/fab_manifest.py (bind verify) and --content (read-only)
- BOM / CPL / owner-BOM format, qty, field and coverage cross-check
- cost_check.json / stock_check.json and file hashes vs ORDERING 8.1
- pdftotext / pdfinfo of the assembly PDFs

## Coverage limits

- Gerbers were not re-exported and compared line by line; their binding rests on the manifest and the drill/paste counts.
- JLC web pages were not re-read live this round.
- Assembly PDFs were checked only for presence, title and text; not rendered visually.
- Firmware and electrical procedures in 8.3 were read only for manufacturing facts (positions, contacts, C84 check).
