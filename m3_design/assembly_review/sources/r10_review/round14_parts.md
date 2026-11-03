# Round14 — independent full parts, BOM, footprints, supplier and placement review

Target commit `f5e4a5a94013514edb952fd328325341b63a98df`.
PCB SHA-256 **before and after**: `e0e3ad841654128792b32ab778ca19e4a71e596fa89864074ec4e91e6a5ccfc6`.
**0 Critical / 0 Major / 1 active Minor**, carried. One historical Minor is independently closed below. No C/M candidate was suppressed. R9 has no literal severity table; the review packet's operational definitions apply. Pending qualification alone is not a demonstrated functional failure.

The [structured evidence](round14_parts.json) contains all 82 supplier records with actual per-query UTC times/raw-response SHA, all 199 placement results, all 44 footprint pad geometries, manufacturer document hashes, seven terminal pin maps, twelve SD lands and the 113 decision/22 mandate scope index. This is a full fresh lens, not a fix-delta pass. Prior reports supplied context; current native geometry and original maker/supplier sources supplied proof. Only these two new reports and ignored probes were written; no CLI, build, full check, git mutation, GUI retry, source/native edit or peer current-round report was used.

## Finding and historical closure

**R14-BOM-01 — Minor, carried: L400 can leave a0.15mm heel strip uncovered.** L400 F(24.2,5.55),0°, C1329837/Bourns SRP5030T-6R8M, uses `kilib/rocket.pretty/M3_SRP5030TA.kicad_mod`: native1.8×2.5mm lands centred x±2.35. [Bourns p1](https://www.bourns.com/docs/product-datasheets/srp5030t.pdf) recommends2.0×1.8 at±2.25. Native inneredge1.45 versus allowed component heel `(5.7−0.3)/2−(1.1+0.3)=1.30mm` leaves0.15mm potentially uncovered. Nominal contact remains; no failed required function is demonstrated. This independently reproduces R13-BOM-01/R12-BOM-01/R4-BOM-01. **Fix:** adopt the maker land through separately reviewed generator/layout work, or obtain documented assembler/owner acceptance plus actual tolerance/fillet qualification of this exact retained land. A low orientation residual does not qualify its fillets.

**R13-BOM-02 — closed Minor: Molex fitting nails/tolerance omission.** J430 B(24,24.3),0°, now has local model/check box x±7.525,y−9.70…+6.00,z0…2.10mm. [Molex SD-47219-001G sheet1](https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/salesdrawingpdf/472/47219/472192001_sd.pdf) gives width `(13.60+0.15)+2×(0.50+0.15)=15.05mm`, including both fitting nails. The independent y-datum stack−9.70…+5.35 is included; the retained card-front+6 and common centred seating datum remain labelled Inference. Native global box is x16.475…31.525,y18.300…34.000,z−3.700…−1.600, with15.210798mm bore margin. No further CAD omission is shown for this **closed** allocation. Opening, actual card seating/locking and retention remain qualification obligations.

## Entire fitted population and placement

Native KiCad10.0.6 read-only parsing finds209 footprints,199 fitted,82 distinct LCSC codes and44 fitted lands;966 segments/296 vias agree with the target packet. The ten excluded board features are J2 and nine test pads. Every fitted native LCSC/Manufacturer/Manufacturer Part agrees with `schematic.net.xml`; every reference's LCSC, exact MPN, land and quantity agrees with `fab/m3_bom_jlc.csv`. No missing, extra or duplicated BOM/CPL reference was found. Retained `LCSC Part` aliases agree with canonical `LCSC`; no contradictory second part code was found. All199 native pad signatures match their local library's number, local position, size, drill, shape and attribute; a separate local-angle comparison modulo180 also finds zero mismatches. Custom drain polygon evidence is separately retained.

All82 exact public JLC model strings equal the BOM MPNs; supplier brand variations are legal-name/case aliases, including Bourns, JSCJ and Jieerrui. This verifies identity, not every supplier electrical attribute. In particular AP63201's supplier quiescent-current attribute is not substituted for the Diodes datasheet.

All199 CPL rows reconstruct independently against numbered official supplier pads: **67 top/132 bottom,169 rows from62 freshly fetched exact maps,30 rows from20 exact-code cache maps**. Global projection uses the CPL centre/angle, supplier pad coordinates and explicit bottom reflection; it does not read `jlc_corrections.json`. No required pad number is missing. The largest distance is0.491288mm at R134's enlarged two-pad land; LS120 is0.449970005mm against its explicitly reviewed0.451 allowance. Distinct MOSFET source/gate/drain fingers establish pose; arbitrary exposed-pad anchors are excluded. U5's masked copper-only tails are excluded from the solder-contact comparison.

Fresh C21190 maps now reconstruct the former12 placement-only resistor rows. Fresh C1329837 supplies L400's exact map, avoiding reliance on a different-inductance proxy for this independent check. A separate read-only `jlc_orient.py --verify-cpl` with the fresh-map overlay likewise returns199 reconstructed,0 placement-only,0 errors. The existing canonical187+12 result remains a dated result; no cache/correction/CPL was changed. Twenty new map requests returned curl56/no body; their explicit fallback cache SHA is `4ca1019f4928ddd84be118de801156b0cc9a7284e2876d04e46013d07e5a00ab`. Placement reconstruction does not replace JLC's actual placement preview or first article.

## All seven DB125 terminals

The original [DORABO supplier-linked T0-1 sheet1](https://atta.szlcsc.com/upload/public/pdf/source/20251124/8C215F69B14C8E54AE0F8E5023D4AE9F.pdf) was rendered and visually read in full: pitch3.5mm,pin0.50×0.85,reference holeØ1.20,tail3.50±0.30 below seating,body height8.60 plus general tolerance0.30;28–16AWG,4–5mm strip,0.2N·m,10A UL/13.5A IEC. Native terminals use Ø1.90 copper/Ø1.30 finished drill,radial annulus0.30 and nominal interpad gap1.60mm. The selected larger drill is explicit; physical joints/contact heating are not measured.

| Ref; native top pose | Exact code; identity | Pin order in native numbering |
|---|---|---|
| J1;(7.4,75.85),−90° | C466970;green2P | 1 BAT_IN;2 GND |
| J121;(7.4,55.85),−90° | C52993880;black2P | 1 PYRO1_OUT;2 PYRO1_IGN |
| J400;(7.4,65.85),−90° | C466970;green2P | 1 SW_SOURCE;2 SW_RETURN |
| J410;(38.6,15.5),+90° | C2757925;green4P | 1 PORT_4V8;2 GND;3 GPS_TX/TXO;4 GPS_RX/RXI |
| J420;(38.6,31.5),+90° | C2757925;green4P | 1 PORT_4V8;2 GND;3 RADIO_TX/TXO;4 RADIO_RX/RXI |
| J9;(38.6,47.5),+90° | C2757925;green4P | 1 CAM_5V;2 GND;3 CAM_RX/RXI;4 CAM_TX/TXO |
| J122;(38.6,71.5),+90° | C3646874;green5P | 1–4 SERVO1–4;5 GND |

No R9 terminal role alias, J124, servo motor-power row, GH port header or on-board RF module remains. The camera's RX/TX order intentionally differs from GPS/radio. Exact pad global coordinates/nets are in the JSON; GPIO directions still require the separately reviewed firmware binding.

The independent maximum body/interlock union is local x−4.62…+3.70 for2P,−8.32…+7.20 for4P and−10.07…+8.95 for5P; all share y−4.10…+4.00,z0…8.90. Current model/check boxes contain those maxima, including the asymmetric interlock. Their outward faces are x3.4/42.6. With bore radius25.4,wire axis z5.0,board axis x23 and0.3mm transverse allowance, bare-bore wire room is `sqrt(25.4²−5²)−19.6−0.3 = 5.003011866mm`, **0.053011866 above the owner's4.95 floor**. Using24.9 usable body radius and both0.3 transverse tolerances gives2.976268mm minimum body margin. Adjacent4P maximum bodies retain0.48mm longitudinal separation.

All23 terminals' tails are independently included to3.8mm below seating,2.2mm below the1.6mm board,leaving nominal1.8mm above a plate on4mm standoffs; minimum bore margin is7.558359mm. Their transverse extent uses the native copper-pad AABB, expressly an Inference rather than a pin/fillet/bent-tail model. These are CAD allocations. Actual16–22AWG wires/ferrules/bends,screw motion,screwdriver,sled obstruction,retention and contact/pulse heating remain unqualified.

## Hinged microSD and maker package checks

Molex **472192001/C164170** is the hinged socket, without mechanical card detect or spring eject. The original drawing and official product page agree. All eight0.80×1.50 contacts at1.10mm pitch and four1.45×2.00 shell lands match the native land and independently fetched official pad map. Local contacts x3.205,2.105,1.005,−0.095,−1.195,−2.295,−3.395,−4.495,y0 correspond to DAT2,CD/DAT3(SPI CS),CMD(MOSI),VDD,SCK,VSS,DAT0(MISO),DAT1. The label CD on DAT3 does not provide a mechanical switch. ShellG1→12,G2→9,G3→10,G4→11;all four and VSS are GND. This explicitly checks the shell aliases as well as electrical pin numbering. [Molex product](https://www.molex.com/en-us/products/part-detail/472192001).

All twelve SD apertures are100% native copper area with zero mask/paste margin, consistent with Molex's0.10/0.12mm stencil examples; the maker discourages0.08mm. Actual stencil acceptance remains open. The closed union includes nails and tolerance; hinge opening is not represented. Current instructions require the unpowered board unbolted/removed for card operations, or qualification of an installed hinge window.

The JSON matrix records all 44 footprint names, every fitted reference, exact native dimensions/drills and source IDs. Important checks against complete original maker drawing pages include:

| Parts/package | Independent maker comparison and limits |
|---|---|
| Q120/Q121;Q124 | [AOS PO00047 revI](https://www.aosmd.com/sites/default/files/res/packaging_information/DFN3x3A_8L_EP1_P.pdf):source/gate row0.65 pitch,0.35×0.50 lands;drain comb/tiebars and pin identities match. Q124 merges the whole drain into custompad5; AONR21357 retains fingers5–8 plus EP9. Q120/Q121 common source ACT_FET_S and opposite bottom poses verified. |
| U9;U11 | TI [TPS25947](https://www.ti.com/lit/ds/symlink/tps25947.pdf) RPW0010A and [TPS2121](https://www.ti.com/lit/ds/symlink/tps2121.pdf) RUX0012A lands/numbering checked. U9's L-shaped unions are14 native rectangles for10 logical pins. Paste area reductions match the stated~93% corner/~82% bar allocations; scaled contiguous bars are not a literal copy of the split example. |
| U401 | TI [TPS7A91](https://www.ti.com/lit/ds/symlink/tps7a91.pdf) DSK10:0.60×0.25 lands,0.5pitch,EP1.2×2.0; two1.13×0.89 paste windows give83.8083% EP area. Exactly two native GND via centres at(27.3,13.6)/(27.9,13.6),Ø0.5/0.3,occupy pad11. Filled/capped planar VIPPO acceptance remains mandatory. |
| U10/U402;U13;U12 | TI DBV/DCU maker lands and pins match. U12 survives on **bottom**(31.6,39.8),0°. The deleted GPS/radio translators/switches are not included in assembly. |
| U400;U2 | [Diodes AP6320x p17](https://www.diodes.com/assets/Datasheets/AP63200-AP63201-AP63203-AP63205.pdf):new U400 uses maker land. U2's retained generic TSOT land is a different example with adequate lead overlap; fixed AP63203 pin1 is VOUT,AP63201 pin1 FB. |
| U1;U4 | ST LQFP100 and LGA14 numbering/package dimensions checked. U1's longer retained lands share maker outeredge16.7mm and add0.4mm heel length. U4 bottom180 and enlarged lands/paste/mask agree with the reviewed axis frame; this does not qualify firmware or sensor calibration. |
| U5 | TE MS5611 original2017 p16:the eight1.1×0.6 inner solder contacts match; outer copper-only tails are masked and paste-free. No-clean,pressure-port exclusion and actual two-reflow process remain open. |
| U3;Y1 | [Winbond W25Q128JV RevG p67](https://www.winbond.com/resource-files/w25q128jv%20revg%2004082019%20plus.pdf) confirms208mil SOIC,pin functions and1.27pitch; [NDK NX3225GA](https://www.ndk.com/images/products/catalog/c_NX3225GA_e.pdf) confirms25MHz/8pF,signal1/3 and grounded2/4. |
| J3 | Original HRO TYPE-C-31-M-12 drawing confirms contact/power/CC/data aliases,four shell slots and twoØ0.6locators. Native slot drills0.6×1.7/0.6×1.4; shell paste+0.1;0.45mm west shell overhang remains. |
| LEDs;D120/D123/D9;ESD | NationStar LED1 cathode1 versus Kento LED2 anode1 explicitly verified. BAT54A common anode3,AO3400A G1/S2/D3,Hottech5819WS cathode1 and B340A cathode1 agree with nets. Bidirectional SMBJ12CA and ESD103 do not depend on polarity. Semtech/ST six-pin arrays match supplier pad numbering. |
| C84;LS120;R134/R166;L1 | C84's exact polymer identity/polarity and derived land are explicit; no maker reflow profile is supplied,so manual fit after both reflows remains required. MLT5020 enlarged pads retain its body frame. Bourns CRM2512 and UniRoyal2512 maker lands match R134/R166. Sunlord4030 maximum case4.2×4.2×3.0 and terminal overlap checked; its imported nominal4.0mm model is not a tolerance certificate. |
| All remaining passives | Exact Samsung/Murata/Fenghua/Yageo/Vishay/UniRoyal codes,case sizes,end dimensions and supplier numbering checked across0402/0603/0805/1206/1210/2512. GRM32 native gap2.0,pad1.0×2.3 is inside Murata's stated ranges. Generic retained lands are not claimed to duplicate every maker example or establish first-article fillets. |

The supplier-linked H743 PDF bytes are **Rev8**, while the official current web PDF is Rev11(Jan2026); the current LQFP100 Figure117,p320 was also checked. USBLC6's supplier original is Rev5 versus current official Rev7. Several direct maker PDF downloads failed; maker-branded supplier originals and a cached original Molex drawing were independently read instead. The JSON preserves actual PDF hashes and those version/source limits.

## Paste, mask and live procurement

Read-only `paste_check.py` compares current Gerbers to native geometry at1µm: **245 top/373 bottom apertures,618/618 matched**, no missing/extra/double flashes. Native pad process extraction confirms U4 mask+0.025 and minimum adjacent mask web0.10mm; U401's split EP windows; Infineon's separate paste-only lands; Q124 custom-drain paste−0.06; USB shell paste+0.1. No ordinary SMD pad contains a via centre:only the two exact U401GND thermal vias do. This does not independently repeat full DRC or prove stencil thickness,volume,reflow yield or filled-via fabrication.

The exact-code JLC public API query ran **2026-10-30T11:02:47.315965Z–11:03:42.599036Z**, two workers with0.35s pause each. All82 exact-code responses succeeded. The durable records retain true individual query times,raw SHA,exact model/package,stock,minimum,fitted quantity and applicable price intervals. Basic36/Extended46;no separate Extended-count cap is reinstated.

| Five-board supply/cost fact | Fresh result |
|---|---|
| U4 C26633007 | Stock0;requires5:short |
| R430 C185349 | Stock17;5fitted but minimum3610:short |
| U9 C3662793 | Stock113;requires5;minimum now **1**, not the prior7 |
| Other 79 codes | No stock-short or thin result at the modeled purchase quantities |
| Fitted component prices | $57.5514/board |
| Standard feeder share | 82×$1.53÷5=$25.092/board |
| Placed+feeder model | **$82.6434/board** versus$84.41 |
| Minimum purchases+feeders | **$84.4456/board**, **$0.0356 over**$84.41 |

The current [official JLC fee page](https://jlcpcb.com/help/article/pcb-assembly-price) confirms Standard feeder fees apply to both Basic and Extended codes. Setup/stencil/fixture add$83.96/order;handling may add$14.93. PCB,panel/rails,soldering/X-ray,VIPPO,C84 manual process,consignment,attrition,shipping/tax are additional. This is neither a quote nor a complete payable-board cost. Stock/minimum/cost/process and owner acceptance remain ordering obligations; no order or substitution is authorized by this evidence.

## Coverage and stage limits

AGENTS and both review packets were read first; REQUIREMENTS,all 113 decision IDs through D-R13-03,AVA_LAYOUT,M3_R10,R10/R9 validation and the read-only parent VEHICLE source were considered under current amendment scope. The parts qualification,ordering and final-deviation records supplied additional context. Historical GH/RF/servo-header/pull-pin choices and poses do not override current screw terminals,single switch,always-on GPS/radio and hinged SD. No owner acceptance of remaining agent choices is inferred.

Actual checks were native read-only board/field/pad/model parsing,identity/quantity/membership checks,44-land signatures,primary document/PDF inspection,82 fresh supplier lookups,62 fresh official map lookups plus explicit cache fallback,199 independent CPL projections,the separate orientation verifier,618-aperture paste parity,native via-centre/mask/paste inspection and current fit calculations. No CLI/DRC/ERC/parity/full gate/build or source refresh was executed by this lens.

R10 remains an unaccepted,unordered CAD candidate. Firmware,physical/electrical/thermal/transient/endurance,lot20ms firing,installed RF/ESD,harness/retention,screwdriver/card/stack/bore fit and first article remain unqualified. This review does not establish assembly-process compatibility or actual seated part tolerances from numerical parity. Standard two-sided reflow,VIPPO,C84 post-reflow manual fit,U5 no-clean/pressure-port protection,panel acceptance and supplier placement preview still require the stated manufacturing dispositions. No AGENTS section2 limit was changed.
