# R10 round 30 — manufacturing lens (Claude)

Target: commit `0afaed3`, board `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c` (SHA-256 identical
before and after). Probe directory: `.supervisor/r30_manufacturing/`.

## Totals

**0 Critical / 0 Major / 0 Minor real errors.**

## Findings

None. Every manufacturing statement checked matched the board, the fab package, JLC's published capabilities, or a
correct recalculation.

## What was checked

- **DRC and JLC capabilities.** I ran DRC with every severity and schematic parity on a probe copy: 0 violations,
  0 unconnected items, 0 parity issues, and the project has no exclusions. I also checked the board against JLC's
  capabilities page (read 2026-11-02):
  - tracks are at least 0.20 mm;
  - vias are 0.5/0.3, 0.6/0.3 and 1.0/0.5 mm;
  - the smallest PTH annular ring is 0.20 mm;
  - NPTH holes are 0.6 and 0.991 mm, and plated slots are 0.6 mm wide;
  - silkscreen text is at least 1.0 mm high with 0.15 mm strokes;
  - DRC holds 0.55 mm from inner-layer PTH pad holes to copper.

  Everything is within JLC's limits.
- **Gerber, drill and PDF outputs.** I re-exported the Gerbers, drill files and job file with `export_fab.py`'s
  exact flags. All 14 files are identical to the committed zip apart from their dates. The drill groups are:
  - 0.300 mm: 308 holes;
  - 0.500 mm: 1 hole;
  - 0.600 mm: 4 slots;
  - 1.300 mm: 27 holes.

  Both assembly PDFs are also identical apart from dates, and all 216 footprints carry a Fab reference.
- **Content checks and manifest.** All three content checks pass, run read-only on the committed package:
  - S-4: OK;
  - `jlc_orient --verify-cpl`: 192 rows rebuilt plus 14 placement-only, worst residual 0.491 mm;
  - `paste_check`: 249 / 381 flashes.

  All 193 input hashes and all 6 output hashes in the manifest match the tree.
- **BOM, CPL and owner BOM.**
  - The JLC BOM has 81 lines. The 206 designators in it equal the 206 CPL rows (70 top / 136 bottom).
  - Every row's LCSC code, part number and layer equals the board's.
  - The parts left out are C84 (owner BOM) and J2 plus 8 test points (excluded from the BOM and position files).
  - Both files have the columns JLC requires.
  - The cost and stock evidence ($85.26; U4 2 orderable, U9 −81) agrees with ORDERING §8.1, M3_R10, AGENTS and the
    handoff.
- **ORDERING §8.1 and §8.2.** I re-measured these on the native board, and all agree:
  - the tab-to-terminal gaps (3.155 mm);
  - the VIPPO vias: exactly two are filled and capped, and the paste gap and drill overlap are 0.22 / 0.04 mm;
  - the DB125-to-bottom-part gaps (1.763–2.172 mm), with the per-terminal part lists complete;
  - D402's M-6 gaps (1.768 / 1.808 mm) and J440's partner-via gaps (0.30 mm);
  - the J3 slot gaps;
  - the short-edge courtyard gaps;
  - the C84 land projections;
  - U4's mask webs (0.150 mm) and paste (88.4 %);
  - U11's apertures, J430's 100 % paste openings and L400's land;
  - every terminal and part position and rotation;
  - the 14 parts without a Fab body;
  - the 13 bottom-side pin legends;
  - the GND thermal spokes.
- **ORDERING §8.3.** I re-read every probe contact (position and net), the coating and switch-enable via list, D402's
  tap, the U5 / TP122 boxes and the VLOGIC capacitor set behind the TP83 rule. All agree.
- **REQUIREMENTS M2.** No via hole is within 0.1 mm of an SMD mask opening, apart from the two GAP-3 U401.11 vias. The
  next nearest is 0.125 mm (C98.2), and the rule is gated by `check_r7.vias_in_smd_pads` via check_r10.
- **check_r10.** T-1, M-1, M-3, M-6, M-8, K-legends, LC-1 and P-11 all pass on the probe copy.

## Fix verification

| Item | Verdict |
|---|---|
| Round 29 re-export: outputs changed only in their dates, and the manifest is re-bound to `a0ec075e…` | confirmed (regenerated outputs are identical; the hashes match) |
| R29-TRI-04: LS120 ≤ 70 °C added to the §8.3 chamber test | confirmed |
| R29-TRI-03: 27 terminal tails / contacts | confirmed (27 drill holes; P-11 OK) |
| D-R29-01 / -02 | no manufacturing effect (BOM, owner BOM and CPL hashes unchanged) |

## Observations (not counted)

6 observations, listed in the JSON:
- the stale R9 title of ORDERING;
- the BOM's "JLC THT assembly" label against the hand-solder remark (consistent);
- gaps quoted to 0.001 mm, which match within polygon tolerance;
- the U4 "outline", which is the courtyard and silk union;
- mask webs against JLC's dam figure;
- the job-file inner copper, a stackup default.

## Coverage limits

- No JLC DFM upload, quote or production-file confirmation.
- No live supplier query.
- No visual page-by-page review of the PDFs.
- No physical process work.
