# R10 round 36: docs_binding lens

Target commit `c3c4249`; board SHA-256 `a0ec075e…` before and after (unchanged). Binding note `c5cd0fa3…`, budget `4267634…`.

**Totals: 0 Critical / 0 Major / 0 Minor.** No real errors found.

## Checks executed
- Links and anchors in STATUS, AGENTS, M3_R10, ORDERING, handoff, R10_VALIDATION, FMEA, REQUIREMENTS, parts_qualification, AVA_LAYOUT, hotplug.md: 205 relative links, 0 bad.
- Binding note fields (board, pin table) equal the files; pin_table `r10_net` vs U1 pad nets: 0 mismatches.
- 40 cited part positions / sides / rotations, LS120, the five M3 holes, the 46 × 90 outline and J3's overhang match the AGENTS rows.
- Fab: 81 codes (45 Extended / 36 Basic), 206 placed, C535146 × 9, CPL 70 / 136, paste 249 / 381, manifest hashes bound to `a0ec075e…`.
- Cost $85.26 (12:44:13Z) and stock (U4 9/2, U9 30/−81, min 7; 12:43:17Z) consistent across docs; $85.60 is labelled as the earlier run.
- Metrics 216 footprints / 309 vias (304 / 4 / 1) / 1866.794 mm / 2,369,507 bytes match M3_R10, R10_VALIDATION, AVA_LAYOUT.
- Budget four-stall 5.713 V matches the 5.71 V figures; 5.73 V uses are labelled history.

## Fix verification
- R34-TRI-01: confirmed (parts_qualification R92 / R166 pointers; hotplug.md pointer and historical label; hotplug_inputs bound to `a0ec075e…`, results digest `f4d1b57d…`, 1643.90 µF / 5.914 V).

## Observations (not counted)
- R10_VALIDATION:2751 / :3033 name earlier probe artifacts (`adjacency_a3144b15.json`, `detour.py`) as method tools in dated sections; not links.
- Docs name rounds 35 and 36 as the planned closing pair; true at commit time.

## Coverage limits
Sampled numeric re-checks, not every figure in R10_VALIDATION / FMEA / parts_qualification; no datasheet re-reads.
