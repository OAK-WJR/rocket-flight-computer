# R10 round 27 — manufacturing lens

Target commit `816038c`, board `a0ec075e…` (SHA-256 identical before and after the review).

**Totals: 0 Critical / 0 Major / 0 Minor real errors.**

## Checks
- DRC (kicad-cli 10.0.7, all severities, probe copy with DRU and libraries): 0 violations, 0 unconnected; no rule set to ignore.
- JLC capabilities (read 2026-11-02): via ring min 0.100 mm; PTH rings 0.300 mm; via hole-to-hole min 0.259 mm (JLC 0.2); pad hole-to-hole min 0.920 mm (JLC 0.45); PTH hole to foreign inner copper min 0.5505 mm (JLC 0.3, DRU 0.55); via hole to foreign inner copper min 0.250 mm (JLC 0.2).
- D-R26-01 vias (7.4,16.5) / (7.4,20.0): 0.700 mm hole to hole from J440.3 / J440.4, In1 ring 0.600 mm from the pin hole, 0.300 / 0.800 mm pad clearances, tented. Pins 3 / 4 of J410, J420, J440 and J9 have no In1 / In2 flash.
- Gerbers, drill and assembly PDFs re-exported with export_fab.py's options: identical to the committed package except creation dates. Drill: 0.3 × 308, 0.5 × 1, 0.6 × 4 slots, 1.3 × 27; NPTH 0.6 × 2, 0.991 × 3.
- fab_manifest verify OK; paste_check 249 / 381, 0 dry pads; jlc_orient --verify-cpl 67 + 125 rebuilt, 14 placement-only, no errors.
- CPL: every row matches the board (J3 / J430 carry their recorded corrections); C10, C11, R164 and R173 at their new positions. BOM 81 codes, 206 parts; cost $85.26 and $16.79 fixed recompute.

## Fix verification
- D-R26-01: confirmed. D-R26-02: confirmed (CPL rows). D-R26-04: confirmed (C10 row, regenerated files).

## Observations (17, not counted)
See `round27_manufacturing.json`. The only point that might be worth a look is that KiCad's stackup gives 0.030 mm inner copper while ORDERING orders 1 oz inner copper. The job file is informational, so this is not a finding.
