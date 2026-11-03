# Round 22 manufacturing review

Target commit `ec8cb98`, board `5516eeec…` (SHA-256 the same before and after). **Totals: 0 Critical, 0 Major, 2 Minor.** Machine-readable twin: `round22_manufacturing.json`.

## Findings

### R22-MANUFACTURING-01 (Minor, new): the DB125 keep-off list in ORDERING 8.2 leaves out four parts

The fix for R21-MEC-01 added this bullet to ORDERING 8.2: "Bottom-side parts sit 1.76–2.17 mm (copper edge to edge) from the DB125 holes; keep the iron and any nozzle off them." It then lists the parts.

I measured B.Cu SMD pad copper to DB125 pad copper on the board. Four bottom parts fall inside the stated range but are not listed:

| Part | Nearest terminal | Distance |
|---|---|---|
| R102.4 | J9 | 1.997 mm |
| C410.2 | J410 | 2.003 mm |
| C420.2 | J420 | 2.003 mm |
| C431.1 | J9 | 2.050 mm |

All four are closer than U5 (2.171 mm), which is listed. Every listed distance is confirmed: R13 1.762, the TSLP clamps 1.771–1.900, C91 1.800, C421 1.850, R150–R153 1.825–1.894, R90 1.953, TP82 2.100 mm.

- **Impact:** an inspection and procedure gap only. An iron near these joints would be caught at first-article inspection.
- **Fix (text only):** add J9 R102 / C431, J410 C410 and J420 C420 to the list, or generate the list from the board at 2.2 mm.

### R22-MANUFACTURING-02 (Minor, carried; noted in round 14 and R20-MFG-03, no disposition recorded): assembly drawings lack bodies for 14 parts

Some footprints have little or nothing on F.Fab / B.Fab:
- **No Fab graphics at all:** Q122, Q123, D120, D123 and J2.
- **Only a 0.06 mm pin-1 dot:** U1, U2, U3, U4, U5, D4, D121, Y1 and J3.

In the 300 dpi and 900 dpi renders, U1 (LQFP-100), the bottom IMU U4, and U3, U5, Y1 and U2 appear as bare references with no outline. Q123 and D121 also have hidden silk designators, so for them the drawing is the only identification, and it shows neither body nor pin 1.

ORDERING 8.2 asks the assembler to inspect pin 1 and polarity on these parts. The board silkscreen does mark pin 1 or polarity for all 14, which limits the impact.

**Fix.** Either option works:
- add Fab body rectangles and pin-1 / cathode marks (a non-copper board-file change, then refresh the hash and PDFs);
- or, as text only, tell the assembler to check these 14 parts against the silkscreen and JLC's preview.

## Fix verification

| Item | Verdict | Measurement |
|---|---|---|
| D-R21-01 | confirmed | **DRU:** has the three JLC rules as recorded; DRC reports 0. **Inner layers:** every PTH wall is at least 0.5505 mm from foreign In1 / In2 copper (J1.2 In2 0.5505; J400.2 In1 0.5505; J3.1–.4 In2 0.5505; J121.1 1.05). **Outer layers:** PTH to foreign copper is at least 0.5505 mm. **Hole to hole:** no PTH–PTH or via–PTH pair is under 1 mm; the least PTH–NPTH gap is 0.835 mm. **Fills:** every inner fill is one piece. **K-rules:** JLC_HOLE_TABLE pins 0.2 / 0.3 / 0.28 / 0.45 mm; DRU hash 1d2dbe77… matches the manifest. |
| D-R21-05 | confirmed | R81 and C87 are at the recorded positions. Both removed vias are gone: 300 vias, 302 → 300. All eight S-8 keep-outs still enclose a barrel. |
| D-R21-06 | confirmed | The west aft keep-out matches its record (In2, fills barred, tracks allowed). The band areas equal the record: east aft RAW_PROTECTED 7.497 + PORT_5V3 3.077 mm²; east forward 12.244 mm²; west 0. |
| D-R21-08 | confirmed | 215 Fab references, all legible in the renders, including the 0.3 mm D8. Body outlines are outside this gate (finding 02). |
| D-R21-09 | confirmed | All nine moved or shown designators match. 122 visible + 93 hidden. No designator is nearer another courtyard than its own: R81 0.312 vs 0.567 mm, C87 0.256 vs 0.427 mm. |
| R21-MFG-02 (records) | confirmed | 300 vias = 295 / 4 / 1. The drill file has 299 hits at 0.300 mm and 1 at 0.500 mm. 167 GND vias, 983 segments, 1871.611826 mm of track. |
| R21-MEC-01 (records) | partly | The listed distances are right, but the list is incomplete (finding 01). |

## Closed (measured against JLC's capabilities page, read 2026-10-31)

- **DRC:** 0 violations, 0 unconnected, 0 parity issues, 0 ignored (kicad-cli 10.0.7, all severities).
- **Track and space:** least track 0.20 mm (In2 0.25 mm); clearance floor 0.15 mm. JLC: 0.09 mm.
- **Vias:** 0.5 / 0.3 mm meets JLC's via rules ("0.1 mm (0.15 preferred) larger than the hole"; minimum 0.15 / 0.25 mm). The 0.15 mm ring row on the page is for PTH pads.
  - least via hole to hole: 0.259 mm (JLC 0.2);
  - via hole to inner copper: at least 0.2505 mm (JLC 0.2).
- **VIPPO:** only (27.3, 13.6) and (27.9, 13.6) are flagged filled and capped. Both are in U401.11 and sit in the drill file's ordinary 0.3 mm group, as ORDERING says.
- **PTH rings:** DB125 0.30 mm; J3 slots 0.30 / 0.20 mm. Plated slot width 0.6 mm (JLC 0.35).
- **NPTH:** J3's locating holes are 0.2001 mm from J3's own pads, equal to JLC's 0.2 mm. This is the vendor land and is carried.
- **Removed non-functional pads:** the Gerbers have no inner flash at J121.1 and J400.2 (In1 and In2) or at J1.2 (In2). The inner via-pad counts (172 on In1, 80 on In2) match the board.
- **Edges:** copper to the routed edge or an M3 hole is at least 0.5005 mm (JLC 0.2). Drilled hole to edge is at least 0.75 mm.
- **Solder mask:** the least web is 0.15 mm, at U4 (JLC 0.10).
- **Gerber zip:** identical to a fresh export, apart from the date lines. The manifest's 199 hashes all match.
- **BOM / CPL / owner BOM:**
  - BOM: 81 lines, quantities consistent;
  - CPL: 205 rows (72 top / 133 bottom), sides correct, positions exact apart from the verified J430 / J3 JLC offsets;
  - C84 is only on the owner BOM;
  - all three files use CRLF line endings.
- **ORDERING 8.2:**
  - all 24 listed positions match the board;
  - C84's lands are bare, with mask openings and no paste;
  - paste flashes 253 top / 375 bottom.
- **Order-number placeholder:** at B (20.35, 35.6), mirrored, 1.0 / 0.15 mm, 0.576 mm from the nearest mask opening.
- **Silkscreen:**
  - all 167 visible texts are 1.0 / 0.15 mm;
  - least ink to mask 0.156 mm; text to text 0.155 mm; ink to edge 0.302 mm;
  - four bottom designators sit under their top-side parts, which AGENTS §3 allows.
- **Fiducials:** none on the board; JLC's rails add them. Section 8 does not restate this (section 4 does); a one-line add is optional.
- **Not filed (owner and ordering items):** the east tabs over In2 power copper, the cost cap, and U4 / U9 stock.

## Fix now

- R22-MANUFACTURING-01: add four parts to the ORDERING 8.2 keep-off list (text only).
- R22-MANUFACTURING-02: text-only note in ORDERING 8.2, or Fab outlines (a non-copper board-file change).

## Coverage limits

No JLC DFM upload or quote. Holes are measured as drawn, with drill tolerance not modelled. Silkscreen graphics were not measured individually. check.sh was not re-run (read-only brief). Supplier data was not re-queried. Probe outputs are in `.supervisor/r22_manufacturing/`.
