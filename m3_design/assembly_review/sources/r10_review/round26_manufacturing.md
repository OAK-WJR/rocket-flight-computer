# R10 round 26 — manufacturing lens (Claude)

Target `3d8e845`, board `92c3ad59174afe1ffe206f6384c8cd9a8962e09647ccd6a8c418b95b5312056f` (before and after, unchanged).
Probe directory: `.supervisor/r26_manufacturing/`. Machine-readable: `round26_manufacturing.json`.

**Totals: 0 Critical / 0 Major / 2 Minor.**

## Findings

### R26-MANUFACTURING-01 (doc, Minor): the C84 heat-limit list names the wrong joints
ORDERING 8.2 (line 435) and R10_VALIDATION (line 2755) say four bottom joints sit directly under C84's lands
(L1.2, C7.2, C9.1, C9.2) and that L1.1 is 0.60 mm and C7.1 0.90 mm away. Copper polygons on `92c3ad59…` give a different set:
- L1.1 (SW_NODE) overlaps land 2 by 0.03 mm².
- C7.1 (VLOGIC) overlaps land 2 by 0.0036 mm², so it abuts the land.
- C9.1 (3V3) is 0.545 mm from land 1, not under it.
- L1.2, C7.2 and C9.2 are under the lands, as stated.
- C8.2 / C8.1 are 0.605 / 0.814 mm from land 2. C8 is in neither the fixture list nor the inspection list.

Fix: correct the list in both places and add C8 to the keep-off and inspection lists.

### R26-MANUFACTURING-02 (doc, Minor): the J3 hand-finish neighbours omit R7
ORDERING 8.2 (line 461) says to keep the iron off bottom C83 and R8. R10_VALIDATION R7-MFG-03 gives "C83 / R8, 1.95 / 2.15 mm".
Copper gaps to the J3 shell slots:

| Part | Gap | Nearest slot |
|---|---|---|
| C83.1 | 1.952 mm | J3.4 |
| R7.2 | 2.010 mm | J3.4 |
| R8.1 | 2.145 mm | J3.1 |
| R9.2 | 2.785 mm | J3.4 |

R7 is nearer than R8 but is in neither statement. Fix: name C83, R7 and R8 (1.952 / 2.010 / 2.145 mm) in both places.

## Fix verification (D-R24 in this lens): all confirmed
- **D-R24-11:** D402 is in the BOM and CPL.
- **D-R24-12:** 14 parts have no Fab body outline, as recorded.
- **D-R24-13:** the JLCJLCJLCJLC placeholder is gone.
- **D-R24-14:** In2 under the tabs is as recorded.
- **D-R24-15:** R92's courtyard is 2.525 mm and TP88's 2.555 mm from the forward edge.
- **D-R24-20:** the six M-8 distances are as recorded.
- **D-R24-23:** the CPL has 206 rows, 70 top and 136 bottom.

## Observations (13, not counted)
- **Gerbers and drill files:** a fresh export of the 11 Gerbers differs from the zip only in the creation dates. The drill and job files are byte-identical. The manifest binds all 193 inputs and 6 outputs.
- **DRC:** all severities with schematic parity gives 0 violations, saved and refilled.
- **JLC capabilities:** every measured figure is within JLC's published limits: tracks, vias, rings, slots, NPTH, silk and mask dams.
- **BOM, CPL and owner BOM:** their formats, counts and fields match the board.
- **Content checks:** `jlc_orient` (worst residual 0.491 mm, R134) and `paste_check` (249 / 381) pass.
- **U401 VIPPO:** the via coordinates, the 0.04 mm drill overlap and the 0.22 mm window gap are correct.
- **Tabs:** the windows and margins match the tab plan.
- **Short edges:** the distances match the six recorded DFM queries.
- **DB125 neighbours:** the list and range are correct.
- **Assembly PDFs:** both are complete, and the bottom view is mirrored.
- **Probe worksheet and terminal table:** both match the board.
- **Cost and stock:** the quoted figures match the files.
- **Q120 / Q121:** each EP merges with its drain pads (same net).

## Coverage limits
- JLC's quote form is script-driven and was not read.
- The JLC041611-7628 stackup name was not confirmed on JLC's stackup page.
- FreePoly pads were approximated in the mask analysis.
- No physical or DFM-upload check was made.
