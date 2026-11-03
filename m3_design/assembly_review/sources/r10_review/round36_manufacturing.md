# R10 round 36 review: manufacturing lens

- Commit `c3c4249`; board SHA-256 `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c`, the same before and after.
- Totals: **0 Critical / 0 Major / 0 Minor** (no real errors).

## Findings

None.

## Fix verification

- R34-TRI-01 (outside this lens): confirmed. parts_qualification.md:1037 and :1061 point to `hotplug_results.json` and M3_R10 "Current state".

## Observations (not counted)

- DRC (kicad-cli 10.0.7, --severity-all --schematic-parity) on the board: 0 violations, 0 unconnected, 0 parity issues.
- Gerbers and both drill files re-exported from a probe copy of the board with export_fab.py's exact kicad-cli arguments are identical to m3_gerber.zip's 14 files apart from creation dates.
- fab_manifest.py --content (read-only): binding OK for 6 outputs; S-4 OK; CPL rebuilt 67 top + 125 bottom + 14 placement-only, worst residual 0.491 mm; paste 249 / 381 flashes, 0 dry pads. These match ORDERING 8.2 and AGENTS.
- BOM / CPL: 81 JLC lines, 206 designators, Qty matches the designator count on every line, LCSC and Manufacturer Part agree with every footprint field, no DNP or excluded part, CPL 70 Top / 136 Bottom with sides matching the board, C84 only on the owner BOM, and only TP* / J2 left out (not placed). J430's CPL centroid is 1.55 mm from the footprint origin; jlc_orient --verify-cpl accepts it (JLC centroid correction).
- Assembly PDFs: the top lists exactly the 74 top references and the bottom exactly the 142 bottom references (pdftotext token set against the board).
- Vias: 309 (304 at 0.5 / 0.3, 4 at 0.6 / 0.3, 1 at 1.0 / 0.5, the BAT_IN via at (17.5,87.15)); the 0.300 mm drill group holds 308 holes; only the U401.11 vias at (27.3,13.6) and (27.9,13.6) are flagged filled and capped. U401's B.Paste windows (y 13.71 / 13.49) leave a 0.22 mm gap, so they overlap each 0.3 mm drill by 0.04 mm, as ORDERING 8.1 says.
- JLC capabilities (page re-read 2026-11-02): silk 1.0 mm text / 0.15 mm strokes meet 'line width >= 0.15 mm' and 'text height 1.0 mm'; PTH rings are 0.3 mm (DB125) and 0.2 mm (J3 slots) against 0.20 / 0.15 mm; plated slots are 0.6 mm wide against 0.35 mm; vias are 0.3 / 0.5 mm, above the 0.15 / 0.25 mm minimum; the inner PTH hole-to-copper DRC rule is 0.55 mm against JLC's 0.3 mm.
- U4 lands are 0.575 x 0.35 mm with 0 mask relief, so the webs are 0.150 mm; paste ratio -0.03 gives 88.4 % of the land, as ORDERING 8.2 says.
- Only six courtyards are within 2.5 mm of a short edge: R400 / R401 / R404 at 1.025, C403 at 1.955, C95 at 1.505 and R166 at 1.755 mm. They match the six DFM queries in ORDERING 8.2 and M-8; R92 is at 2.525 mm and TP88 at 2.555 mm.
- ORDERING 8.2's terminal table, Q120 / Q121 / Q124 / C126 / C123 / C411 / C421 / C431 / C91 / C92 / C84 / D9 / U4 / J430 positions and rotations, C84's and D9's pad nets and positions, the 93 hidden designators and the 14 parts with no Fab body outline all match the board.
- Copper gaps from DB125 / J3 holes to bottom parts are 1.762-2.172 mm, inside ORDERING 8.2's 1.76-2.17 mm, and C83 / R7 / R8 are 1.952 / 2.010 / 2.146 mm. D402's 1.768 / 1.808 mm are M-6's courtyard-to-pad figures (pad-to-pad 1.96 mm), as labelled. The J440 GND partner vias are 0.302 mm from J440.3 / J440.4.
- ORDERING 8.3's probe-worksheet contacts (TP80-TP122, R119.1, R120.2, C120.2, C24, C15.1, TP74, TP88, C88.1, C82.1, R84.1, U9 exposed-pad ends) match the board's pad positions and nets.
- The six GND terminal contacts have local zone_connect=1 and GND fill on F.Cu / In1 / B.Cu only, with no In2, as ORDERING 8.2 says.
- U4's 'bottom outline x15.1-19.1' in ORDERING 8.3 is the union of the courtyard and the silk pin-1 mark (courtyard x15.125-18.875; silk to x19.065), which round 30 / 31 already judged. Not re-reported.
- The cost figures in AGENTS, STATUS, ORDERING and M3_R10 ($85.26, parts $60.47, feeder $24.79, fixed $16.79) match cost_check.json (12:44:13Z); the $85.60 figures are dated history. The AGENTS copy injected into the session context is stale, but the committed AGENTS.md at c3c4249 is current (as round 34 already noted).
- The KiCad stackup in the board and job file (inner copper 0.03 mm, core 1.03 mm) is a CAD setting, not the ordered stackup; ORDERING 8.1's order form fixes JLC041611-7628 with 1 oz inner copper, and no R10 requirement uses the KiCad stackup figures.

## Checks executed

- shasum -a 256 on the board before and after
- kicad-cli 10.0.7 pcb drc --severity-all --schematic-parity (output in the probe directory)
- python3 tools/fab_manifest.py <board> --content (read-only)
- unzip m3_gerber.zip into the probe directory; read the job, drill and Edge_Cuts files
- kicad-cli gerber + drill re-export from a probe copy of the board, and a diff ignoring dates
- pcbnew probes (probe1-6.py in .supervisor/r36_manufacturing/): positions, vias and VIPPO flags, paste and mask, courtyards at the edges, BOM / CPL field agreement, Fab outlines, THT gaps, probe contacts, GND thermal settings
- pdftotext of both assembly PDFs, set-compared with the board's references
- WebFetch of JLC PCB capabilities

## Coverage limits

- JLC's assembly-terms and via-covering pages were not re-read this round; the citations from round 23 were taken as given.
- No live JLC quote or DFM upload.
- ORDERING 8.3 was checked for its coordinates and process statements only, not for its electrical bench-gate procedures (other lenses).
- The panel / tab In2 copper was not re-measured (unchanged board; earlier rounds measured it).
