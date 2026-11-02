# Round 24 manufacturing lens (Claude)

Target commit `f2b8251`. Board SHA-256 before and after: `1407e8506efbac0f664b3aeb65568c32ae9670c9b45b502a465cba1130de522e`.

**Totals:** 0 Critical / 0 Major / 0 Minor. No real error was found.

## What was checked

- **Fab package binding.** `tools/fab_manifest.py --content` passes: six outputs bound, S-4 BOM/CPL OK, CPL rebuilt for
  67 + 125 rows plus 14 placement-only checks (206), and paste 249 / 381 on every pasted pad.
- **Re-export.** A probe re-export of a board copy gives:
  - a byte-identical BOM, owner BOM and CPL;
  - all 14 Gerber, drill and job files identical apart from their date lines;
  - content-identical assembly PDFs.
- **DRC.** All severities, with schematic parity, on a copy: 0 / 0 / 0. check_r10, full, on the copy: all rules OK
  except K-binding, which failed only because the binding note is not beside the copy.
- **JLC capabilities** (multilayer, read 2026-11-01). Everything is met:
  - via rings 0.1 mm;
  - PTH ring at least 0.300 mm;
  - NPTH at least 0.6 mm;
  - via-to-via walls at least 0.259 mm (same net) and 0.350 mm (different nets);
  - pad hole walls at least 0.920 mm;
  - copper to edge 0.5 mm;
  - mask 1:1, with no web under 0.13 mm between different pads and no opening within 0.12 mm of foreign copper;
  - silk at least 0.15 mm.
- **VIPPO.** The two U401.11 vias, and the split paste windows (0.22 mm gap, 0.04 mm drill overlap), reproduce as
  ORDERING 8.1 states.
- **BOM, CPL and owner BOM formats.**
  - JLC headers are correct.
  - The 81 codes are unique and the quantities sum to 206.
  - The CPL lists the same 206 designators (70 top / 136 bottom).
  - The cost and stock evidence hashes match the files.
- **Assembly PDFs.**
  - Every footprint's Fab reference is on its own side's drawing (74 top / 142 bottom), with none missing.
  - D402 is on the bottom drawing.
  - There is no JLC order mark.

## Fix verification

| Decision | Verdict | Measured |
|---|---|---|
| D-R24-11 (fab side) | confirmed | C535146 is 9 per board; the CPL row for D402 is (4.45, −65.9), Bottom, 90; B.Paste is 381; D402 is in the PDF |
| D-R24-13 | confirmed | No `JLCJLC` on the board or in the PDFs |
| D-R24-14 | confirmed (deviation disclosed) | In2 RAW_PROTECTED fill is x 44.00–45.49 and PORT_5V3 is x 41.0–43.69, joining at y ≈ 63.4; tab-band areas match |
| D-R24-15 | confirmed | R92 courtyard is 2.525 mm and TP88's is 2.555 mm from the forward edge; the rest match the DFM list |
| D-R24-12 | confirmed (deferred) | The 5 parts with no Fab shape and the 9 with only a dot are exactly ORDERING 8.2's list |
| D-R24-09 / -17 (fab side) | confirmed | R402 / R403 / C88 CPL rows are correct; vias 302 / 4 / 1 match the drill hits 306 + 1 |

## Observations (not counted)

11 observations are recorded in the JSON. Among them:

- **D-R24-14's "x 44.0–45.7".** This is the zone outline; the fill stops at 45.49. It is consistent with the board.
- **Stackup name.** JLC041611-7628 is not on JLC's impedance page, which lists only the 0.5 oz inner JLC04161H-*
  stackups. Round 23 read the name from the quote page; it was not re-read here.
- **Bottom pads near the DB125 terminals.** Their copper sits 1.762–2.172 mm from the DB125 pads, inside ORDERING
  8.2's stated range.

## Coverage limits

- The JLC quote and Confirm Production File were not exercised.
- The mask check covers pads and tracks, not zone edges.
- No physical inspection was done.
