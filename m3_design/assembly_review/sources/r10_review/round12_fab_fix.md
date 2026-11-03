# Round 12 Fab fix: source and focused proof

**R12-MFG-01 source fix is ready; full integration remains pending.** Only `m3_design/r10_post.py` changed, plus these two receipts. The frozen canonical PCB remains `0ad0135cb9ff1f6ace7ef9d5ba9006b727b293d7b5224bb97dad47859b91238d` (2,263,730 bytes); all five canonical fab-output hashes still match the review package. No canonical board/fab save, build, full gate or Git action occurred.

`fab_reference_details` at line543 is called at line680 after the existing Fab-reference/J122 setup and before `r9_post.fab_clear`. It changes only the five `${REFERENCE}` **B.Fab** texts to **0.4×0.4 mm,0.06 mm stroke**:

| Ref | Native position before (mm) | Native position after (mm) | Angle/mirror |
|---|---|---|---|
| R10 | (20.000,44.690) | (20.000,44.790) | 180°, mirrored |
| C29 | (28.000,43.520) | (27.950,43.520) | 90°, mirrored |
| C92 | (32.350,52.500) | unchanged | 180°, mirrored |
| R8 | (9.000,32.500) | unchanged | 270°, mirrored |
| C5 | (22.200,71.430) | unchanged | 180°, mirrored |

All angles, mirroring, layer and reference content are preserved. The function anchors the offsets to each footprint and is idempotent. **These smaller labels serve the zoomable vector assembly aid and may need detail zoom/high-resolution rendering. All production silkscreen properties remain unchanged at their existing1.0 mm/0.15 mm minimums.** No copper, pad, model, zone or footprint pose changes are introduced.

## Focused validation

The actual edited module was imported under the project KiCad Python. On an in-memory copy of the frozen board, the existing `silk.fab_refs`, J122 placement, new helper and `r9_post.fab_clear` were executed. No other Fab reference moved. The saved temporary board is **byte-identical** to the previously geometry/PDF-checked candidate:

`3c1b7c436bbfc761b121e8c9d297339c5e0a3f4edd8e5794e2a68702abc35ac4`.

The exact original/candidate comparison contains **five Fab-text-only hunks**. All other serialized board properties are identical, covering silkscreen, copper, pads, models, zones and poses. The native copper/zone/pad/pose digest is also unchanged (`c198efe388d556984cdf3cfe80183eb271ddb7ccc6dac92f16a9d326ab2dc14c`). A second helper application produces identical candidate bytes. Source AST/order assertions pass.

Actual rendered-glyph polygons were checked against all bottom Fab graphics, every other Fab reference and all pad/support holes. Native polygon error is0.0001 mm; distance-search resolution is0.00001 mm.

| Ref | Nearest Fab graphic (mm) | Nearest other Fab reference (mm) | Nearest drill/support hole within5 mm |
|---|---:|---|---|
| R10 | 0.041759, own pin-1 dot | U4,1.644133 | none |
| C29 | 0.027960, own pin-1 dot | C26,1.854713 | none |
| C92 | 0.245426, own pin-1 dot | R103,1.439265 | none |
| R8 | 0.095604, own pin-1 dot | R7,2.911147 | J3.1,2.663123 mm |
| C5 | 0.095604, own pin-1 dot | U2,1.786898 | none |

The minimum exceeds the previously checked0.025 mm graphic clearance. The retained candidate PDF SHA-256 is `b3337298592c3dc26995b07c8885a2c9fdfb6452a4216538793e105c1c347027`; the reviewer and root previously inspected its complete page and all five labels at detail zoom. Exact candidate-board identity makes a duplicate PDF export unnecessary for this focused source proof. The temporary candidate PCB/PDF remain available for integration.

## Source fingerprints and remaining work

- Before: `c084a24768c59949790d65768e654f2737aee58a74ff141a1aa9b4fc569bdbb0`.
- After: `94a467a2e823ca7e5160aceb7baf7d1f474b056ed54a608ee713690c6bf5eaeb`.

`round12_fab_fix.json` contains exact before/after properties, the five native diff hunks, measured clearances and hash evidence. Root must integrate the workers' source changes and perform the complete builds, check.sh, provenance/fab regeneration and reproducibility checks. No physical assembly or firmware qualification is claimed.
