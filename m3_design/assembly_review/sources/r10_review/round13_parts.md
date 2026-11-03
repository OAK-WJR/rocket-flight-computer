# ROUND13 lens4: parts, BOM, lands, supplier and orientation

Target commit `fa897c81abac3026e75ca5cc88bef0c2659a7130`. PCB SHA-256 before/after:
`7355ae1aeb1fdfdf6f64317945a0bf114d94c2bb65fb04adfbcd5a2b8037b09c`.

**0 Critical / 0 Major / 2 Minor: one new, one carried.** No C/M candidate was suppressed or downgraded. R9 precedents and the packet's operational severity meanings apply; a disclosed qualification obligation alone is not a demonstrated functional failure. No canonical CAD, source, cache, CPL or document changed. No git action, CLI, build, full check or GUI was used. No current-round peer report was read.

AGENTS was read first, then both review packets and their mandatory requirements, decisions, AVA, M3, validation and vehicle sources. All110 D IDs and22 owner mandates were considered by their amended scope. Later DB125/always-on/SD/two-bank/single-switch decisions supersede the older GH/ARM/header assumptions; AGENTS section2 remains authoritative. This full parts lens covers the entire current population, rather than only the last fixes. Structured measurements, source hashes, all199 reconstruction rows, all82 supplier identities and authority IDs are in [round13_parts.json](round13_parts.json).

## Findings

**R13-BOM-01 — Minor, carried: L400 can leave a0.15mm heel strip uncovered.** At F(24.2,5.55),0°, exact C1329837/Bourns SRP5030T-6R8M uses `M3_SRP5030TA`:1.8×2.5mm lands centred x±2.35mm. [Bourns p1](https://www.bourns.com/docs/product-datasheets/srp5030t.pdf) recommends2.0×1.8mm at±2.25mm. Native inner edge1.45mm versus permitted component heel `(5.7−0.3)/2−(1.1+0.3)=1.30mm` leaves0.15mm potentially uncovered. Nominal contact is retained; neither supplier orientation residual0.150106mm nor nominal overlap qualifies worst-tolerance fillets. This independently reproduces R12-BOM-01/R4-BOM-01; no failed required function is demonstrated. **Fix:** adopt the maker land in separately covered generator/layout work, or obtain documented assembler/owner acceptance and actual tolerance/fillet qualification of this exact retained land.

**R13-BOM-02 — Minor, new: the closed Molex model omits fitting nails and part of the dimensional tolerance stack.** J430 is B(24,24.3),0°. The actual model `kilib/rocket.3dshapes/M3_MICROSD_MOLEX_472192001.wrl` decodes to x±7.000mm/y−9.500…+6.000/z0…2.100. [Molex SD-47219-001G sheet1, top view and tolerance block](https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/salesdrawingpdf/472/47219/472192001_sd.pdf) shows13.60mm shell plus0.50mm lateral fitting-nail projection on each side: nominal14.60mm,0.30mm per side beyond the model. The fresh official-library outline independently gives57.4802×0.254=14.5999708mm. The complete maker-identified drawing was visually inspected via its [mirror](https://cdn.promelec.ru/upload/items/2020/09/01/472192001_sd.pdf) after the local official download timed out.

General two-decimal dimensions are±0.15mm; relevant recommended-PCB datums are explicitly±0.05mm. Under a common centred datum and zero seating offset, independently stacking those tolerances gives width15.05mm, socket y−9.70…+5.35mm and closed height≤2.05mm. Keeping the existing inferred card-front+6.00mm and z2.10mm gives a simple diagnostic union x±7.525/y−9.70…+6.00/z0…2.10mm. These are conservative **Calculation/Inference**, not maker-certified assembled/card maxima; exact body-to-land centring, actual card seat and solder stand-off remain unqualified. The y stack also exceeds the present model by0.20mm at its rear.

This union occupies board x16.475…31.525/y18.3…34.0. An independent native screen against every bottom stroked-courtyard AABB finds no overlap: nearest C23 gap0.575mm, versus0.775mm with the old box; R460/R461 remain0.745mm. Its specific radial extent at both±0.3mm transverse allowances leaves15.210799mm to r24.9mm. These are bounded CAD diagnostics, not full DRC/fit or a physical collision guarantee; the conclusion does not rely solely on shell-pad extent. **Fix:** include nails and maker tolerances in the closed envelope, or model them separately at their real height; recheck clearance/fit, model-identity expectation and bindings in covered work. Confirm card/seating assumptions. Until then, qualify the14mm box as incomplete rather than a conservative complete socket union.

## Population and orientation reconciliation

| Current native/file inventory | Top/F | Bottom/B | Total |
|---|---:|---:|---:|
| All native footprints |70|139|209|
| Native fitted purchased components |67|132|199|
| Actual current CPL rows |67|132|199|
| Current cached supplier-pad reconstructions |66|121|187|
| Current cache: placement-only C21190 resistors |1|11|12|
| This review, supplemented with fresh exact C21190 map |67|132|199|

The10 unpurchased feature footprints are J2 plus9 test pads. The82 BOM rows sum to199 positive quantities, equal their distinct designators; no omission or duplicate. All fitted PCB/XML Value, footprint, LCSC, Manufacturer and Manufacturer Part fields agree; no contradictory supplier code field was found. There are664 native pad instances:648 numbered/netted instances agree with XML, plus16 unnamed paste/mechanical pads. All209 footprints match their local library's numbered pad shape types, local centres, dimensions and drills. All199 model paths are existing relative `${KIPRJMOD}/kilib/...` paths with finite positive scales.

Independent CPL position/side/rotation and numbered-pad reconstruction finds zero errors. Worst residual0.491288mm is R134; its native2.45×3.7mm lands at±2.575mm give the7.6mm outer span in [Bourns CRM p2](https://www.bourns.com/docs/product-datasheets/CRM.pdf). Thus that supplier-centre difference is not proof of a bad physical land. LS120 retains its documented maker-derived enlarged lands/residual0.449970mm; U12 residual0.147412mm; Q120/Q1210.100124mm. Maker lands remain the authority.

The cached12 placement-only rows are R100/R101/R103/R110/R150–153/R440/R441/R450/R451. Fresh exact C21190 pads now permit independent reconstruction of all12 with0.071636mm maximum residual, without editing a cache or CPL. The historical72Top/115Bottom figure belongs to the circuit-pass `6e73b6eb…` reconstruction; it is not the current7355 CPL population.

Fresh geometry source: **JLCEDA/EasyEDA Official Library**, [JLCEDA](https://lceda.cn/) and [EasyEDA](https://easyeda.com/). Fourteen codes fetched08:47:10–08:47:16UTC:12 cached exact maps unchanged, L400's C189932 proxy confirmed, and C21190 newly available. Position reconstruction certifies the stated geometry comparison, not an assembler preview or first article.

## All seven DB125 terminals

| Ref | Exact supplier code; positions/colour | Native pose, F(mm,°) | Contact roles in numbered order |
|---|---|---|---|
|J1|C466970;2 green|(7.4,75.85),−90|BAT_IN,GND|
|J121|C52993880;2 black|(7.4,55.85),−90|OUT,IGN|
|J400|C466970;2 green|(7.4,65.85),−90|SW source,SW return|
|J410|C2757925;4 green|(38.6,15.5),90|4V8,GND,board TX,board RX|
|J420|C2757925;4 green|(38.6,31.5),90|4V8,GND,board TX,board RX|
|J9|C2757925;4 green|(38.6,47.5),90|CAM_5V,GND,board RX,board TX|
|J122|C3646874;5 green|(38.6,71.5),90|SERVO1–4_OUT,GND|

All23 lands independently match3.5mm pitch, Ø1.9mm copper/Ø1.3mm drill and1.6mm nominal interpad gap. [DORABO T0-1 p1](https://atta.szlcsc.com/upload/public/pdf/source/20251124/8C215F69B14C8E54AE0F8E5023D4AE9F.pdf) recommends Ø1.2mm holes, specifies28–16AWG,4–5mm strip,0.2N·m maximum torque and3.50±0.30mm tails. The retained larger finished drill remains an assembly qualification item. A3.8mm tail through1.6mm board leaves2.2mm nominal under-board projection before seating/solder tolerance.

Decoded maximum body unions are x[−4.62,+3.70]/[−8.32,+7.20]/[−10.07,+8.95] for2/4/5P, y[−4.10,+4.00], height8.90mm, within0.00000149mm quantization. All seven face outward and yield `sqrt(25.4²−5²)−19.6−0.3=5.003011866mm` bare-bore wire room. Adjacent maximum4P unions leave0.480mm. This independently closes the former R11 terminal Major on this target; wires/ferrules/screwdrivers/staking and physical fit remain unverified. All five terminal GND contacts have explicit thermal overrides; all terminals need staking and externally supported leads.

## Hinged microSD and other critical parts

J430 is exact Molex472192001/C164170, with eight electrical contacts and four GND shell contacts. Native8×0.8×1.5mm signal lands at1.1mm pitch and4×1.45×2.0mm shell lands match the maker layout after the bottom-side mirror. Pin order is DAT2,CS,CMD/MOSI,3V3,CLK,GND,DAT0/MISO,DAT1; shell aliases12/9/10/11 all reach GND. Five10k pulls,100nF/22uF bypass allocation and all12 full paste apertures are present. The maker sheet requires100% apertures with0.10/0.12mm stencil and discourages0.08mm; the [maker product page](https://www.molex.com/en-us/products/part-detail/472192001) supplies−20…85°C and0.5A/contact. No mechanical card-detect switch or ejector is inferred. Opening requires unpowered PCB removal from a continuous sled or a qualified window; card/hinge retention, busy current/latency and power-loss behavior remain unqualified. The incomplete model is separately reported above.

Q120/Q121 have the genuine AONR21357 identity, opposing B0/B180 poses and correct source/gate/drain nets. Their asymmetric maker land was inspected against [AOS PO-00047I](https://www.aosmd.com/sites/default/files/res/packaging_information/DFN3x3A_8L_EP1_P.pdf), rather than treating the EP anchor as its copper boundary. C120 remains1uF25V X7R; no unqualified X5R cost merge was made. Q124 remains AON7524 with the required gate network. Retired ARM/pull-pin/GPS-radio isolation/duplicate-ADC/servo-power parts are absent.

Independent native hole-to-pasted-SMD shape screening finds zero ordinary intersections. U401's non-pasted EP separately contains exactly two GND Ø0.5/0.3mm vias at(27.3,13.6)/(27.9,13.6); they require resin-filled/copper-capped planar VIPPO, not tenting. [TI TPS7A91](https://www.ti.com/lit/ds/symlink/tps7a91.pdf) pin/land and [TXU0202](https://www.ti.com/lit/ds/symlink/txu0202.pdf) camera pin/supply roles were checked. CAD cannot qualify VIPPO, stability or actual heat paths.

C84 remains exact MA25V470M8x10/C46550466 with positive pad1 VLOGIC at(27.5,81.75), F90. Its [exact MA sheet](https://atta.szlcsc.com/upload/public/pdf/source/20260306/24758A4FC016E80367B87853635CDCC1.pdf) supplies electrical/body data but no land/reflow/manual profile. Manual fitting after both reflows, validated process and polarity/seating/height/capacitance/ESR inspection remain explicit obligations, not new failures.

## Fresh supply and manufacturing limits

Fresh public JLC exact-code queries08:38:42–08:38:52UTC match all82 MPNs; no unknown identity. Important current lines:

|Code/refs|Stock|Needed for5 fitted boards|Minimum purchase|
|---|---:|---:|---:|
|C466970 J1/J400|35571|10|1|
|C52993880 J121|346|5|1|
|C2757925 J9/J410/J420|38841|15|1|
|C3646874 J122|4169|5|1|
|C164170 J430|8667|5|1|
|C185349 R430|17|5|3610|
|C26633007 U4|0|5|1|
|C3662793 U9|94|5|7|

All other codes cover their greater-of-fitted/minimum quantity. Parts57.5538USD/board plus25.092 feeder share gives82.6458; minimum purchases59.8942+25.092=84.9862USD,0.5762 above84.41. These reproduce the known stock/cost obligations, not new review failures. Fixed/process/PCB/rails/consignment/shipping remain additional; there is no accepted quote or order. Resolve R430/U4, account for U9's minimum, obtain owner/process/panel acceptance and refresh within24h of ordering.

Standard bottom-first/top-last, no-clean processing, U5 two-reflow acceptance,0.10mm preferred stencil, C84 manual-after-reflow, U401 VIPPO and all23 THT contact hole fills remain assembler obligations. No firmware, physical/flight, first-article, installed RF/ESD, actual solder/retention, electrical/thermal/transient/endurance, harness/switch or card/sled qualification is claimed. The exact source and fresh-snapshot evidence, successful checks, initial probe/API limitations and bounds are separated in the JSON. Canonical sources remain frozen.

Preserved raw fresh supplier snapshot: `.supervisor/r13_parts_supplier_raw.json`, SHA-256 `b925f9fb991c9aac14cd3dfd92f4bd0cee263043398dfd8411e0afdf0c330357`. The JSON lists the normalized fresh maps and Molex drawing/detail evidence hashes for the subsequent correction.
