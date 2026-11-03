# R17 parts/BOM/footprints/stock/orientation

Target commit `ac483f40d38db6e0424227bd32d2a5d5f9f60c3e`; PCB before/after `632a9ad36c19426ede219b6ff6b0d638955665cac1b4704d3392a6afdbe03982`.
Full independent lens: **0 Critical, 0 Major, 4 carried Minor groups**. All1,966 frozen canonical files match before and after. No implementation, Git, CLI/build, order or peer-R17 evidence was used.

The amended requirements and all122 decision/23 owner scopes were considered, including D-R16-03: retain the PCB and circuit/placement/routing generators for Minors. R9 remains accepted; this report is no manufacturing or flight release.

## Fresh native checks

- 209 footprints,199 fitted parts,82 BOM rows/codes and199 CPL rows. Current15-sheet schematic metadata agrees with every fitted native LCSC/MPN/manufacturer/land. No duplicate designators or quantity mismatch;128 legacy LCSC fields agree.
- All44 fitted land patterns match their local library instances:199 pad-parameter comparisons and2,838 pad-layer polygon instances, including custom shapes, at1um tessellation. All199 model paths are relative and exist.
- Supplier-CPL reconstruction exits0:66 top+121 bottom reconstructed,12 nonpolar resistor placement-only checks. Fresh correction derivation changes no rotation/offset/status. Worst0.491mm residual is R134, whose native2.45x3.7mm lands match Bourns' drawing; it is not a substituted resistor.
- Native/Gerber paste check exits0:245 top+373 bottom=618 matching geometries, no dry omissions. Read-only fit check exits0; physical fit is unverified.

## Current Minor findings

| ID | Status | Evidence and required closure |
|---|---|---|
| R17-BOM-01 | Carried | L400 F(24.2,5.55): native1.8x2.5mm lands at +/-2.35 versus Bourns2.0x1.8 at +/-2.25. Inner gap2.90 versus2.50mm; an independent tolerance stack permits a0.15mm uncovered heel strip. Retain owner/assembler wetting and first-article solder/retention qualification on the unchanged board. [Bourns SRP5030T p1](https://www.bourns.com/docs/product-datasheets/srp5030t.pdf). |
| R17-BOM-02 | Carried | All23 DB125 contacts use nominal1.30mm holes/1.90mm copper. Conditional sharp0.70x1.05mm pin diagonal1.261943mm exceeds conditional1.22mm finished hole. Metal profile/pattern applicability is unresolved. J121.1 at(7.4,54.1) freshly measures1.102501576mm nominal hole-wall to In2 3V3 fill; illustrative diameter/position allocation gives0.962501576mm. Obtain maker/assembler/fabricator insertion, pattern, annulus and S-8 allocation and inspect all23 first-article contacts; no blind drill change. These assumptions do not demonstrate actual insertion or isolation failure. [DORABO T0-1 sheet1](https://atta.szlcsc.com/upload/public/pdf/source/20251124/8C215F69B14C8E54AE0F8E5023D4AE9F.pdf), [JLC drilling tolerances](https://jlcpcb.com/capabilities/pcb-capabilities). |
| R17-BOM-03 | Carried | C19 B(28.35,37.65)/C20 B(19.8,37.3) are exact Samsung C23630,2.2uF16V X5R +/-10%; nominal1.98..2.42uF meets nominal selection. ST's numerical1.76..2.64uF/ESR<0.1ohm operating interpretation, combined bias/temperature/AC/aging/process and actual regulator modes remain unqualified. Resolve supported limits or qualify both fitted capacitors, both C limits/ESR and startup/load/VOS transitions; no arbitrary larger-cap substitution. [ST DS12110 Rev11 p211 Table114](https://www.st.com/resource/en/datasheet/stm32h743vi.pdf), [exact Samsung sheet pp1-2/manual pp12-17](https://product.samsungsem.com/part/download.do?masterKey=CL10A225KO8NNN&type=specsheet). |
| R17-BOM-04 | Carried | Fresh exact82-code supplier run still blocks ordering: R430/C185349 stock17<3610 minimum; U4/C26633007 stock0<5. U9/C3662793 is83/minimum7, sufficient but adds0.5382USD/board. Secure exact stock/consignment and terms, obtain process/panel quote and refresh within24h before ordering. No unqualified substitution or order. |

## Terminals, card and process

Fresh maker/native inspection covers all seven outward-facing DB125s. Maximum local x unions for2/4/5positions are[-4.62,+3.70]/[-8.32,+7.20]/[-10.07,+8.95]mm, y[-4.10,+4.00], height8.90. These unions retain5.003011866mm bare-bore wire room and0.48mm between adjacent4P bodies. All23 tails have separate3.80mm seating-length allocations; minimum modeled tail/bore gap7.558359mm. All five terminal GND pads explicitly use thermals; saved-fill sampling independently finds four spokes on F/In1/B and no In2 GND connection each. Real insertion, solder fill, torque, wires and tool access remain open.

J430 is the exact locking-hinge Molex472192001 at B(24,24.3), not a mechanical detect switch. All8 contacts and4 GND shell lands agree with the maker drawing;100% paste is21.2mm2. CPL is Bottom,(24,-25.85)mm,180degrees with supplier offset(0,+1.55)mm and0.005mm residual. The15.05x15.70x2.10mm closed allocation includes nails/tolerances; common seating and card-front projection remain Inference. Service remains board off/out of bay and off the continuous sled unless a hinge window is qualified. [Molex SD-47219-001G sheet1](https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/salesdrawingpdf/472/47219/472192001_sd.pdf).

C84 exact MA25V470M8x10 retains derived lands and positive pad1 VLOGIC at F(27.5,81.75). The four-page supplier maker sheet gives470uF/25V,25mohm at100kHz and4.1A ripple but no land/manual/reflow profile. ORDERING8 correctly requires separately qualified manual fit after both reflows. U401 retains exactly two0.5/0.3mm GND vias at(27.3,13.6)/(27.9,13.6), mandatory filled/capped planar VIPPO and original split paste. Standard/no-clean/two-U5-reflow/selective-THT/stencil/preview obligations remain explicit; pending physical process approval is not an invented hardware failure. [MA series](https://atta.szlcsc.com/upload/public/pdf/source/20260306/24758A4FC016E80367B87853635CDCC1.pdf), [TI TPS7A91 DSK drawings](https://www.ti.com/lit/ds/symlink/tps7a91.pdf).

## Original supplier snapshot

Public exact-code query: **2026-10-30T17:15:34.705395Z through 2026-10-30T17:15:45.842149Z**, max3 concurrent,82/82 exact MPNs,46 Extended/36 Basic,0 unknown prices. No numeric normalization was required; integer counts and price-break bounds were already numeric. Original timestamps/raw responses are preserved in ignored `.supervisor/r17_parts_probe/` under the `tools/jlc_stock.py supplier_snapshot` schema.

Five-board Standard model:54.4312USD parts+25.092USD feeder share=**79.5232USD/board**. Minimum purchases give56.7716+25.092=**81.8636USD**, both below84.41 before fixed/process/PCB/shipping. Historical snapshot minima remain historical; U9's changed minimum explains this run's uplift.

- Snapshot SHA256: `b8a5a145db87273db0ba127b689d3c8a69864f207987d29c8e0860b3ea1943e5`.
- Raw82-response hash-manifest SHA256: `a9dc0ecd9a6f4905718521e7f68a86b675fefac163ec563f196d8ee4b33fb6df`.
- The JSON includes every sanitized code/identity/count/price and original raw response hash; signed download URLs remain ignored. Exact package checks additionally refreshed all four terminal codes, Molex and exact/proxy L400 from the [JLCEDA/EasyEDA Official Library](https://easyeda.com/) ([JLCEDA](https://lceda.cn/)); exact L400 and proxy now share the same package, so proxy visibility alone is closed.

## Limits and rejected hypotheses

No present maximum-terminal-room, wrong-card-contact, missing-paste, BOM/CPL substitution or C84 transferred-reflow Major was established. Conditional terminal and VCAP hypotheses are retained as bounded Minors, not measured failures. Full maker pages were rendered and inspected for DB125, Molex, Bourns, MA, Samsung and16 additional package/drawing pages; detailed source hashes/pages are in the JSON.

Current official ST Rev11 text was checked; the permitted binary cache was Rev8, and current binary fetch failed. No Rev11 raster inspection is claimed. Remaining supplier pad maps were reprocessed from existing primary evidence;12 resistor rows remain placement-only. This lens ran no full DRC/build/gate and claims no firmware, electrical/thermal/transient/endurance, physical/flight, SD latency/power-loss or first-article qualification. Reports and evidence remain read-only after handoff.
