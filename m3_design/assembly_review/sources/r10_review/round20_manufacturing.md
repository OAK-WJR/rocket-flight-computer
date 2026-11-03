# Round 20 manufacturing review

Target commit 6628488, board `50a39de5…` (SHA-256 identical before and after). Totals: **0 Critical, 0 Major, 4 Minor** (all new).

## Findings

### R20-MFG-01 (Minor, new): Three of the four proposed R10 panel tabs (and the aft-edge alternative) sit over In2 power copper to 0.5 mm from the edge; the R8/R9 "GND only under every tab" rule is neither kept nor recorded for R10

- Evidence: pcbnew filled-zone intersection with each 5 mm tab span x 1 mm / 3 mm inward band: West aft (x=0, y 12.50-17.50): F GND / In1 GND / In2 3V3 / B GND. East aft (x=46, y 6.75-11.75): In2 RAW_PROTECTED (3 mm band also PORT_5V3 3.08 mm2). East forward (x=46, y 63.75-68.75): In2 RAW_PROTECTED 12.24 mm2. Aft-edge alternative (x 38-43, y=0): In2 RAW_PROTECTED. West forward (y 60-65): GND on all four layers. Fills start 0.50 mm inside the edge (2.50 mm2 of each 5 mm2 1 mm band). Scan of every legal window at 0.25 mm steps: the only GND-only (all four layers, 3 mm band) 5 mm positions are west y 51.75-66.25; none exists in the west aft third or on the east edge.
- Reference: ORDERING section 3 (R9): "Under every tab all four copper layers carry GND only, so a crack at a tab cannot join a live region to GND (R8's y 63-68 tab sat over In2 3V3, R8P3-POWER-05)"; R8P2-POWER-02 fixed by making the tab GND on all four layers; tab_windows.py: "Reported, not gated: the In2 net under each window ... keep tabs off In2 regions other than GND where possible". ORDERING 8.1 (R10) lists nearest part per tab but not the In2 net.
- Impact: Depaneling (nibbling and filing the tab stubs) puts the highest board-edge stress exactly where In2 3V3 or RAW_PROTECTED lies 0.203 mm (prepreg) from B.Cu GND and ~1.03 mm from In1 GND. A delamination / crack or a smeared burr there can short a supply to GND: 3V3 or the U9-protected rail (current limited, so a dead or browning-out board, not a fire). The protection that R8/R9 deliberately kept was dropped silently for R10; the owner is not told.
- Fix: Either (a) CAD: add In2 fill-only rule-area keep-outs 5.0 x 3.0 mm at each chosen tab span (west x 0-3, y 12.5-17.5; east x 43-46, y 6.75-11.75 and 63.75-68.75), with In2 GND (or nothing) filling there, then confirm no In2 3V3 / RAW_PROTECTED neck falls below its present minimum and re-run K-region / K-power; or (b) records: add an "In2 under tab" column to the ORDERING 8.1 tab table (3V3 / RAW_PROTECTED / RAW_PROTECTED / GND) and an owner-deviation row in R10_VALIDATION, and gate it as tab_windows reports it.

### R20-MFG-02 (Minor, new): Three visible designators sit inside a large neighbour's courtyard, nearer to it than to their own part (C400 new from D-R19-14); the courtyard-nearest check skips large parts

- Evidence: Ink polygon (TransformShapeToPolygon) to courtyard polygon on the text's face: C400 F.Silkscreen ink x 9.08-10.27, y 4.24-7.86 overlaps J440's F courtyard (y from 7.685) by 0.151 mm2, own courtyard 0.082 mm away (new: absent on a3144b15). C94 F ink x 31.44-32.63, y 49.92-52.64 overlaps U1's courtyard (x to 31.645) by 0.266 mm2, own 0.142 mm. R461 B ink x 20.45-24.02, y 17.54-18.74 overlaps J430's B courtyard (y from 18.605) by 0.306 mm2, own 0.018 mm. R166 ink overlaps C84's courtyard 0.561 mm2 (tie: inside its own as well). courtyard_fails only compares courtyards whose bbox centre is within 8 mm of the ink centre in x and y; U1 (9.03 / 8.28 mm), J440 (2.22 / 9.64 mm) and J430 (1.76 / 8.26 mm) fall outside, so they are never tested.
- Reference: AGENTS section 3 silkscreen rule ("never next to another part"; nearer its own part than any other); D-R19-12 / D-R19-14 (C400 moved by the designator search).
- Impact: Legibility / attribution only: C400 reads at J440's north end beside the AUX cell, C94 inside U1's pin field corner, R461 at the microSD socket edge. C400's ink ends about 0.02 mm short of J440's 3D fit envelope at the pin-1 end (Inference from D-R19-08's 1.12-1.32 mm envelope overhang), so a tolerance shift can hide it under the body. No electrical effect.
- Fix: In courtyard_fails / courtyard_offenders, pre-filter by polygon distance (or bbox gap < 8 mm) instead of bbox-centre distance, so large courtyards are tested; re-run r10_post: C400 should land south of its own body (or hide), C94 / R461 move or hide (hidden count may rise above 94; record it).

### R20-MFG-03 (Minor, new): Assembly drawing: Fab references of the new AUX parts and R119 cross their own Fab outlines (R119 prints as "R1119"); no gate covers it

- Evidence: Text-polygon / own-Fab-stroke intersections: C445 0.192 mm2 (glyphs C and 5 over the body sides), D440 and D441 0.048 mm2 each (D and 0 cut by the outline), C123 0.001 mm2, R119 seven strokes 0.010-0.163 mm2 (1.0 mm text on a 0402 outline at B(11.57, 71.10); the 1200 dpi render reads "R1119" between Q121 and Q120). On a3144b15 only R119 / R173 crossed; C445, D440, D441 and C123 are new. FAB_REFERENCE_CLEARANCES_R13 lists C411, D410, D411 (the templates) but not C445, D440, D441, C123 or R119. Separately (carried, noted in round 14): 14 footprints have no Fab body outline, only a pin-1 dot: D120 D121 D123 D4 J2 J3 Q122 Q123 U1 U2 U3 U4 U5 Y1.
- Reference: Round 12 R12-MFG-01 / round 13 R13-MFG-01 (the same defect class, closed by the static table); ORDERING 8.2 says to inspect pin 1 / polarity in the preview using the assembly drawings as aids.
- Impact: The assembly PDFs are the owner's inspection aid for the factory preview and the hand work; R119 (the Q121 gate-source resistor, D-R18-02) is unreadable there, and U4 (the bottom LGA whose pin 1 must be confirmed in JLC's preview, D-R19-11) is shown only as a dot and a name. No fabrication output is affected.
- Fix: Add to FAB_REFERENCE_CLEARANCES_R13: C445 (0, 0, 0.7) like C411; D440 / D441 with D410 / D411's offset and 0.8 mm; C123 (0, 0, 0.4); R119 (0, 0, 0.4). Add a gate check: every visible Fab reference polygon has zero intersection with its own Fab strokes. Optionally draw body outlines for U1-U5, Y1 and the diodes on Fab.

### R20-MFG-04 (Minor, new): The R10 ordering worksheet does not say to choose "Specify a location" for JLC's order number or where the R10 placeholder is; the only instruction is R9's, with R9 coordinates

- Evidence: R10 placeholder: B.Silkscreen, mirrored, at (20.35, 35.6); ink x 15.32-25.42, y 34.98-36.13 (Gerber Y -35.6); 1.0 mm / 0.15 mm; nearest via ring 0.733 mm (GND (25.95, 34.15), the C23.2 via moved by D-R19-14), nearest bottom mask opening C16.2 0.552 mm. grep of section 8 for "JLCJLC", "order number", "Specify a location": no hit. Section 3 gives the R9 position (23.65, 76.4) on board 4f841a0e; section 8 opens by saying sections 1-7 are R9 and apply only where restated.
- Reference: AGENTS section 3 (JLC order-number placeholder is a required legend); r10_post.py line 25 places it.
- Impact: If the order is placed from section 8 alone, the "Specify a location" option may be left at its default and JLC prints its order number wherever it chooses, possibly over legends or fine-pitch parts on this crowded 46 x 90 mm board; anyone reading section 3 gets a wrong (R9) coordinate.
- Fix: Add one row to ORDERING 8.1 / 8.2: "Order-number mark: Specify a location; bottom silkscreen placeholder JLCJLCJLCJLC at KiCad (20.35, 35.6) (Gerber Y -35.6), ink x 15.32-25.42, y 34.98-36.13", and mark the section 3 row as R9 history.

## Round 19 fix verification

| Item | Verdict | Measurement |
|---|---|---|
| D-R19-07 | confirmed | Board pads C84.1/.2 on F.Cu + F.Mask only; Gerber F_Paste 257 flashes, none within 3 mm x 5 mm of C84; F_Mask flashes at (27.5,-75.25) and (27.5,-81.75); m3_bom_owner.csv = C84 only (C46550466, MA25V470M8x10, manual note); C84 absent from JLC BOM and CPL; paste totals F 257 / B 371 match AGENTS / M3_R10 (the record's "245 -> 245" predates D-R19-14's +12 AUX apertures) |
| D-R19-03 | confirmed | TP121 not on board, not in BOM / CPL / owner BOM |
| D-R19-04 | confirmed | BOM line C123,C408 C15195 CL05B103KB5NNNC; CPL C123 18.2200 / -71.8500 Top 0; designator hidden (on Fab) |
| D-R19-05 | confirmed | pad local zone connection = 0 (ZONE_CONNECTION_NONE); DRC library comparison clean |
| D-R19-06 | confirmed | Text bboxes: RADIO y 28.65-30.35 inside J420 courtyard y 24.05-40.06; GPS y 8.78-10.47 inside J410 8.05-24.07; AUX y 9.35-11.05 inside J440 7.685-23.695 |
| D-R19-08 | partly | All 45 board legends and 121 visible designators are 1.0 / 0.15 mm; smallest ink to mask opening 0.156 mm (R460 ref), legends 0.186 mm (2:GND J440); smallest ink to board edge 0.302 mm (J420 outer column); 3D render (kicad-cli 10.0.7, high) shows every word legible, none under a body. Envelope distances not re-measured independently (mechanics lens). |
| D-R19-09 | confirmed | Vias present at (29.8,81.15) VLOGIC, (42.75,61.8), (26.45,11.95), (24.9,14.9) PORT_5V3, (29.75,9.95), (30.5,9.95) PORT_4V8; all 0.5 / 0.3 mm; DRC 0; 300 x 0.3 mm + 1 x 0.5 mm drill hits = 301 vias |
| D-R19-10 | confirmed | BOM line C87,C126 C21120 CL10B224KA8NNNC; CPL C87 17.0 / -65.0 Top 0 |
| D-R19-11 | confirmed | BOM U4 C51931514 ISM6HG256XTR; CPL U4 17.0 / -45.9 Bottom 180; jlc_corrections C51931514|LGA-14 theta 180, residual 0.040 mm, next best 2.005 mm, 14/14 pads by number |
| D-R19-12 | confirmed | 94 hidden on the board = the 94-reference list in M3_R10 line 494 exactly (C28, R110, R88, C123, D440, D441 hidden; all 94 keep a Fab reference); R123 margin to C84 courtyard 0.156 mm; but see R20-MFG-02 for C400 |
| D-R19-14 (manufacturing) | partly | BOM/CPL: J440 (C2757925, THT, rot 270), C444 C14663, C445 C21397, D440/D441 C535146, R470/R471 C21190; all LCSC / MPN fields equal board; drill T4 1.30 mm = 27 terminal holes; tab windows reproduce, but see R20-MFG-01 (In2 3V3 under the west aft tab) and R20-MFG-02 / -03 |
| Fab manifest | confirmed | All six output SHA-256 and all 193 input SHA-256 recomputed from the commit: 0 mismatch; m3.kicad_pcb input = 50a39de5 |

## Fix now

- R20-MFG-03: r10_post.FAB_REFERENCE_CLEARANCES_R13 add C445 (0.0,0.0,0.7), D440 (0.05,-1.0,0.8), D441 (0.0,-1.0,0.8) (D410/D411 pattern; confirm direction for J440 cell), C123 (0.0,0.0,0.4), R119 (0.0,0.0,0.4); Fab-only, no copper, Gerbers unchanged except none (Fab is not exported).
- R20-MFG-04: docs/ORDERING.md 8.1: add the R10 order-number row (Specify a location; B(20.35,35.6), ink x 15.32-25.42, y 34.98-36.13).
- R20-MFG-01: Preferred: In2 fill-only keep-outs 3 x 5 mm at the west aft and both east tab spans, if K-region / K-power and the In2 neck widths still pass; otherwise at least the records change (In2-under-tab column and owner-deviation row).
- R20-MFG-02: courtyard_fails pre-filter by polygon / bbox gap instead of bbox-centre distance; regenerate silkscreen (C400 / C94 / R461).

## Closed candidates

- kicad-cli 10.0.7 DRC, all severities, schematic parity, all track errors: 0 violations, 0 unconnected, 0 parity; no DRC exclusions; no rule set to ignore. Closed.
- Zone fills current: refill on a copy changes only sub-0.03 mm vertex positions; DRC 0 after refill. Closed.
- Gerber zip: all 11 Gerbers, both drill files and the job file re-exported from the board with export_fab.py's exact options are identical after removing timestamp lines. Closed.
- JLC 4-layer basics: min track 0.20 mm drawn (rule 0.15), clearance 0.15, vias 0.5/0.3 (ring 0.10 mm), 0.6/0.3 x4, 1.0/0.5 x1; terminal PTH 1.9/1.3 (ring 0.30); J3 plated slots 0.6 x 1.4 / 0.6 x 1.7; NPTH 0.6 x2 and 0.991 x3 (J2 Tag-Connect); hole-to-hole 0.25; copper to edge >= 0.50 (zones), 0.609 (BAT_IN tracks, forward edge), 0.65 (GND stitch vias x 0.9); vias to M3 holes >= 1.48 mm. Within JLC multilayer capabilities as recorded in prior rounds; not re-quoted. Closed.
- Stackup / job file: 4 layers, 1.6 mm, ENIG, F/B 0.035, inner 0.030, prepreg 0.203, core 1.03 = ORDERING 8.1 JLC041611-7628. Closed (template availability not re-checked live).
- VIPPO: exactly two vias (27.3,13.6) and (27.9,13.6) carry filling yes / capping yes; global tenting front/back yes; no other via touches an SMD mask opening (U401 paste-window overlaps only). Carrier is the order remark only, as ORDERING 8.1 states. Closed as documented.
- Mounting holes are Edge.Cuts circles (3.2 mm, milled) at the five documented positions; silkscreen ink >= 2.43 mm from every hole edge (washer clear). Closed.
- BOM/CPL/owner-BOM: 81 lines, 205 unique refs, Qty sums equal, every LCSC and Manufacturer Part equals the board field, CPL 205 rows (74 top / 131 bottom), owner BOM C84 only, no excluded part listed, no CPL ref missing from the board; CPL offsets only J3 (-0.095 mm x) and J430 (-1.55 mm y), both reviewed corrections. Closed.
- Fiducials: none on the board; JLC Standard rails add them (ORDERING section 4). Closed, as in round 19.
- Top parts with designators on the bottom (U400, R404, C402, C444) sit under their own pad extent (C444 centre 0.01 mm outside, within the search's position tolerance). Closed.
- Silkscreen rules: all designators / legends 1.0 mm / 0.15 mm; none over a mask opening (min 0.156 mm); none off the edge (min 0.302 mm); legends within their own terminal span; hidden list matches records. Closed except R20-MFG-02.
- DB125 wire-entry direction in the JLC placement (EasyEDA pads give no body): rounds 18-19 parts checked the EasyEDA outlines (entry on local +y like ours); J440 uses the same footprint at the same rotation family as J1 / J400 / J121. Closed.
- Cost $85.35 vs $84.41 cap: open owner decision, not filed (brief).

## Checks executed

- Board SHA-256 before and after (canonical file and git archive copy of 6628488): 50a39de5...
- kicad-cli 10.0.7 pcb drc --severity-all --schematic-parity --all-track-errors (probe drc.json); a second DRC with --refill-zones on a copy (refill_drc.json) and diff of the saved copy
- git archive of 6628488 into the probe dir; manifest re-hash of 193 inputs and 6 outputs
- Gerber + drill re-export with export_fab.py options; text diff against the unzipped package
- pcbnew probes (native KiCad Python): track / via / pad / annular statistics; design rules; via fill / cap flags; copper to edge and holes; zone nets under each proposed tab and a GND-only tab scan; BOM / owner BOM / CPL cross-check with board fields; paste pad counts; silkscreen text sizes, ink to mask openings, edge and holes; designator ambiguity by ink-to-courtyard polygons (side-aware) and by pad boxes; hidden designator list vs M3_R10; Fab text vs own Fab outline intersections; Fab outline presence
- Gerber parse: F_Paste / B_Paste / F_Mask flash counts and flashes near C84; drill tool hit counts and slots
- Assembly PDFs rendered with pdftoppm (300 dpi full page, 1200 dpi details at R119 / Q120-Q121 and the J440 cell) and inspected
- kicad-cli pcb render top and bottom (quality high) inspected for legend legibility
- jlc_corrections.json entries for C51931514, C2757925, C535146, C15195, C21120, C46550466
- Comparison board a3144b15 (git show 1e60441) for the new / carried split of R20-MFG-02 and -03

## Coverage limits

- No JLC DFM, quote or capability page was fetched this round: VIPPO per-via mixing, stackup template availability, tab acceptance and mouse-bite drill/offset remain JLC questions (ORDERING 8.1).
- The DB125 3D fit envelope distances of D-R19-08 were not re-measured independently (render inspection only); mechanics lens.
- The In2 neck consequence of the proposed tab keep-outs (R20-MFG-01 fix a) was not computed.
- Gerbers checked by regeneration and parsing, not by an independent Gerber viewer.
- Supplier stock / cost not re-queried (cost over cap is an open owner decision).
