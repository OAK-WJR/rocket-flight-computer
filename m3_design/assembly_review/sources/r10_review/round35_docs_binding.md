# R10 round 35 — docs_binding lens

Target: commit `c3c4249`, board `a0ec075e…` (SHA-256 identical before and after). Binding note `c5cd0fa3…`, budget `4267634…`.

**Totals: 0 Critical / 0 Major / 0 Minor real errors.**

## Findings
None.

## Fix verification
- **R34-TRI-01 (hot-plug results pointer): confirmed.** `parts_qualification.md` :1036 and :1061-1063 point to
  `hotplug_results.json` / `hotplug_inputs.json` and M3_R10 "Current state". `hotplug.md` has the round 34 pointer and
  the "Historical round-11 fix-pass target" header. The inputs bind `a0ec075e…`. Their canonical digest recomputes to
  `f4d1b57d…`, which equals the results' `inputs_sha256`. The extrema recompute to 8.994764 / 5.087664 V/µs and
  1643.90 µF / 5.914 V, and the `5516eeec…` figures 8.991477 / 5.091053 match `ec8cb98`. The new link resolves.

## Checks executed
- Binding note, pin table and board: U1's 100 pins, 0 mismatches. The IMU block matches U4. The hashes of the pin
  table, circuit and budget match.
- Links and anchors: 230 relative links, 0 bad.
- Every `REF F/B(x,y)` statement in the listed docs, scanned against the 216 footprints. The only mismatches are
  dated records or from → to records.
- Terminal table, AGENTS rows, holes, bottom-side pin legends and the EN via (17.10,82.80).
- M3_R10 board metrics, all exact: bytes, segments, track length, vias by size, references, legends.
- Fab package: BOM, CPL, cost and stock figures and hashes.
- Clearances quoted in AGENTS: 1.040 / 1.0585 / 0.794 mm.
- Budget figures quoted in AGENTS and M3_R10.

## Observations (not counted): 5
- R173 B(16.87,59.70) in three dated records; the board has 59.05.
- R101's via coordinate, already ruled.
- Q122 0.218 V nominal against 0.2203 V, already ruled.
- Two probe-artifact names in R10_VALIDATION.
- From → to move-record hits from the coordinate scan.

## Coverage limits
- R10_VALIDATION, M3_R10 and ORDERING 8 were checked by targeted scans, not line by line.
- The decision counts were not recounted.
- S-8 inner barrels were not re-measured.
- No datasheet re-reads.
