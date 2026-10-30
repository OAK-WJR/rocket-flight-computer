# Round 12: parts, BOM, footprints, stock and orientation

Target supplied in the task: commit `d57b216c365fc8d18896bceba37f63caf20d52a4`, branch `m3-assy-r10`. Native PCB SHA-256 before and after review: `0ad0135cb9ff1f6ace7ef9d5ba9006b727b293d7b5224bb97dad47859b91238d` (2,263,730 bytes). No Git operation or canonical edit was performed. Other round-12 reports were not consulted.

**Result: 0 Critical / 0 Major / 1 Minor.** New: 0; carried: 1. Two prior parts items are closed on the current target. Evidence and per-part measurements: [round12_parts.json](round12_parts.json).

## Current finding

**R12-BOM-01 — Minor, carried: L400 retains a reduced heel land.**

At F(24.2, 5.55), rotation 0, `M3_SRP5030TA` has 1.8 x 2.5 mm pads centred at local x +/-2.35 mm: inner gap 2.90 mm and outer span 6.50 mm. Bourns' [SRP5030T p1 Recommended Layout](https://www.bourns.com/docs/Product-Datasheets/SRP5030T.pdf) gives 6.50 mm outer span, 2.50 mm inner gap and 1.80 mm transverse height: 2.0 x 1.8 mm pads at +/-2.25 mm. The product tolerances permit a contact heel at x=1.30 mm while native copper starts at 1.45 mm, leaving a possible 0.15 mm heel strip uncovered. Nominal contacts are covered; no functional failure is demonstrated. This carries R4-BOM-01 and the retained ORDERING section 8.2 deviation.

Fix: use the maker land through its generator and rerun routing/paste/orientation/DRC/binding, or retain this exact measured deviation for explicit owner disposition with assembler and first-article joint qualification. A proxy supplier-pad match does not prove maker heel geometry.

## Closed prior findings

- **R11-BOM-01, former Major: closed.** The complete [DORABO T0-1 sheet 1](https://atta.szlcsc.com/upload/public/pdf/source/20251124/8C215F69B14C8E54AE0F8E5023D4AE9F.pdf) was rendered and read independently. Maximum local x unions are [-4.62,+3.70], [-8.32,+7.20], [-10.07,+8.95] mm for 2/4/5P; local y [-4.10,+4.00], height 8.90 mm. All seven current terminals calculate **5.003011866 mm** wire room, exceeding the accepted 4.95 mm floor by 0.053012 mm. Adjacent maximum 4P bodies have 0.480 mm gap; courtyards add 0.20 mm around the unions. No physical wiring or screwdriver qualification is inferred.
- **R11-BOM-02, former Minor: closed in current instructions.** The current circuit amendment and ORDERING section 8 describe the actual terminal rows and J9 pin3 board RX / pin4 board TX. Superseded GH/header/parked-radio records remain historical.

## Terminal and microSD checks

Native terminal poses and contact roles match schematic/BOM/CPL. All have 3.50 mm pitch, 1.90 mm copper and 1.30 mm finished drill versus the maker's recommended 1.20 mm drill. The 0.30 mm nominal radial annulus is a calculation. Body envelopes retain 2.976269 mm radial margin under the body-fit assumptions. Maximum 3.80 mm tails extend 2.20 mm below a 1.60 mm board.

| Ref | Native F centre, mm / rotation | Entry | Pins in order |
|---|---|---|---|
| J1 | (7.4,75.85), -90 | west | BAT+, GND |
| J121 | (7.4,55.85), -90 | west | OUT, IGN |
| J400 | (7.4,65.85), -90 | west | switch source, return |
| J410 | (38.6,15.5), 90 | east | 4V8, GND, board TX, board RX |
| J420 | (38.6,31.5), 90 | east | 4V8, GND, board TX, board RX |
| J9 | (38.6,47.5), 90 | east | CAM supply, GND, board RX, board TX |
| J122 | (38.6,71.5), 90 | east | SERVO1-4, reference GND |

J430 is Molex 472192001/C164170, B(24,24.3), native 0 / CPL 180 degrees. The complete [Molex SD-47219-001 Rev G sheet 1](https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/salesdrawingpdf/472/47219/472192001_sd.pdf) was inspected via its maker-document [mirror](https://cdn.promelec.ru/upload/items/2020/09/01/472192001_sd.pdf) after the maker download timed out. Native 0.80 x 1.50 mm signal pads, 1.10 mm pitch and 1.45 x 2.00 mm shell lands match. Pins1-8 are DAT2/CS/CMD/3V3/SCK/GND/DAT0/DAT1; all four shell aliases are GND. R460-464 supply the five 10k pulls; C460/C461 are 100nF/22uF rail bypass. Maker 0.10/0.12 mm stencils require full openings; current instructions and paste agree. The contact rating is 0.5 A. Closed-card geometry remains an inference; lid access, chosen-card operation and retention are not physically qualified.

Q120/Q121 native source/gate/drain fingers and common drain polygon agree with [AOS PO-00047 version I, p1](https://www.aosmd.com/sites/default/files/res/packaging_information/DFN3x3A_8L_EP1_P.pdf). Fresh supplier matches preserve their opposed bottom rotations. U401, U12 and C84 placements also reconstruct correctly; supplier centre differences are measured in JSON, not treated as maker-land changes.

## BOM, placement and fabrication evidence

All **199** fitted native parts agree with schematic `LCSC`/manufacturer/MPN, BOM identities and CPL population; there are **82** unique codes and ten bare patterns. No native DNP/exclusion, contradictory extra MPN field or absolute model path was found. All 82 exact MPNs also match the fresh JLC response. Manufacturer differences are ordinary corporate/spelling aliases listed in JSON.

The complete cached supplier/CPL reconstruction passes: **66 top + 121 bottom** rows reconstructed, 12 symmetric nonpolar resistor rows checked by placement only, 199 total; worst residual 0.491 mm. Fresh **JLCEDA/EasyEDA Official Library** data ([JLCEDA](https://lceda.cn/), [EasyEDA](https://easyeda.com/)) independently reconstructs all seven terminals, J430, Q120/Q121, U401, U12 and C84. Maximum absolute pad errors: terminals 0.000134 mm, J430 0.005134 mm, AOS fingers 0.100125 mm, U401 0.007480 mm, U12 0.147413 mm, C84 0.045016 mm. Factory body/pin1/polarity and bottom-side preview remain required.

Executed focused checks all exit 0: `jlc_orient.py --verify-cpl`; `paste_check.py` (245 F / 373 B flashes, zero dry pads); `fab_manifest.py` (all five outputs); `fit_check.py --profile r10` (CAD only). Native read-only probes independently checked the terminal dimensions/roles, SD lands/support nets and all fitted-part identities. No native DRC, full gate or build was run by this lens.

## Fresh procurement snapshot: pending items

The exact-code public JLC lookup completed **2026-10-30T06:11:29Z**: 82/82 exact MPN matches, 46 Extended / 36 Basic; all required prices returned. Raw responses are ignored scratch `.supervisor/round12_parts_supplier.json`, SHA-256 `5ea50a4d9d3a56ba0035e4d5cd410207578f88a1c4f8d170dfb67b0ec49fc12f`. Fresh library raw digest: `511e266dd094ab9c89c449d380fe8628c42f0d41ab7ea20279d3e8c2d1e2c336`.

Under the required Standard feeder model at five boards: placed parts **$57.5554** + 82 x $1.53 /5 = **$25.092** feeders, total **$82.6474 ($82.65)** against $84.41. Minimum purchases raise parts to **$59.8958** and the total to **$84.9878 ($84.99)**, $0.58 above that target. The $2.3404 uplift is R430 $1.8022 plus U9 $0.5382 per board. Preserve this surcharge for quote/cost acceptance; no quote is accepted here.

| Part | Stock | Needed at 5 boards | Supplier minimum | Result |
|---|---:|---:|---:|---|
| R430 C185349 RC0603FR-0722K6L | 17 | 5 | 3610 | short against purchase minimum |
| U4 C26633007 LSM6DSV320XTR | 0 | 5 | 1 | stock/consignment hold |
| U9 C3662793 TPS259470LRPWR | 101 | 5 | 7 | stock passes; minimum adds cost |
| J1/J400 C466970 | 35576 | 10 | 1 | passes |
| J121 C52993880 | 346 | 5 | 1 | passes |
| J9/J410/J420 C2757925 | 38851 | 15 | 1 | passes |
| J122 C3646874 | 4169 | 5 | 1 | passes |
| J430 C164170 | 8659 | 5 | 1 | passes |

No thin lines. These are procurement/owner items, not new CAD Critical/Major findings. Fixed fees ($83.96/order), possible handling ($14.93), PCB/rails/joints, VIPPO, manual C84, consignment, attrition and shipping are additional. Refresh within 24 h of ordering.

## Coverage limits

No board, firmware, bench, shock, retention or physical fit qualification is claimed. Fresh dimensional rereads covered the seven terminals, microSD, load FETs and L400; all 82 maker datasheets were not independently reread. The full placement check uses the reviewed cached supplier set; nine exact codes were fetched anew. C84's inferred land/manual operation, exact U401 VIPPO, U4 mask webs, terminal hole fill/staking and factory previews remain explicit process items. No current-round peer report was read and no reviewer findings were exchanged.
