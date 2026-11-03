# Round13 manufacturing review

Target commit `fa897c81abac3026e75ca5cc88bef0c2659a7130`; PCB `7355ae1aeb1fdfdf6f64317945a0bf114d94c2bb65fb04adfbcd5a2b8037b09c`.
Read-only identity checks before and after match. Read-only HEAD/ref resolution also matches the assigned commit.
**Totals: 0 Critical / 0 Major / 2 Minor**: one new drawing group and one carried land group. No C/M candidate.

## Current findings

| ID | Severity/status | Evidence and implication | Concrete closure |
|---|---|---|---|
| R13-MFG-01 | Minor,new | Additional Fab labels are still crossed by their own borders. Fresh native glyph polygons find27 rectangular-border intersections; e.g. U400 F(16.9,5.55)0.192164mm2,C461 F(27,18.8)0.192164,C407 F(31.8,19.5)0.192193,U11 B(24.65,64.5)0.130485,Q121 B(13.5,68.6)0.041128,Q120 B(13.5,73.6)0.041252. These crossings remain visible at600dpi, including hidden-on-silk U11. Both complete assembly pages and current PDFs were independently inspected; their180dpi renders match fresh target exports pixel-for-pixel. This is an inspection-aid defect; no electrical/placement failure is demonstrated. | Extend the generator's Fab label fit pass to move/shrink these labels off their own graphics while retaining reference/pose/mirroring/association; re-export/bind through a covered revision. If retained, include these additional residuals in the board-bound deviation list and use the native CPL/factory preview for inspection. |
| R13-MFG-02 | Minor,carried from R12-BOM-01 | L400 F(24.2,5.55),C1329837/SRP5030T-6R8M,has1.8x2.5mm pads at localx+/-2.35(native centres21.85/26.55,5.55),inner gap2.9mm. [Bourns p1](https://www.bourns.com/docs/product-datasheets/srp5030t.pdf) recommends2.0x1.8mm at+/-2.25,inner gap2.5mm; outer span6.5mm is the same. Maker tolerance corners can place the termination heel atx1.3 versus native pad edge1.45: possible0.15mm uncovered heel strip(Calculation). Nominal contact remains over copper; no actual failed solder joint is shown. | Retain explicit owner/assembler disposition and qualify first-article coverage/seating/retention, or adopt the maker land through the generator with covered copper,paste,DRC,orientation,fit and binding review. |

The JSON records all 27 rectangular-border intersection with coordinate and area.
The same native walk counts 49 much smaller pin1-dot intersections(max0.007873mm2); these are graphical grazes, not all classified as obscured labels.

## Fresh executed checks

- Official KiCad10.0.7, sequential under an explicit exclusive root reservation: direct all-severity DRC0/unconnected0/schematic parity0 and ERC0,all exit0. `verify_board.py` independently refilled an isolated native copy and ran all-severity/all-track DRC plus parity/ERC:0,with no ignored checks. The reservation was released.
- Metadata audit:209 footprints,199 fitted,zero missing/conflicting identity fields; all199 models resolve,none absolute. The82 cached supplier MPNs agree exactly with current BOM MPNs; this was a dated snapshot check,not a live supplier refresh.
- Fresh temp fab export exit0:82 BOM lines/199placements,no unknown orientations. BOM and CPL bytes match current exports. All14 Gerber/drill/job members match after timestamp normalization; they include11 layers,PTH,NPTH and job file. Job has4layers,1.6mm,ENIG. Current five-output manifest passes. Both PDF binaries remain separately manifest-bound; fresh/current raster equality is stated only for180dpi.
- CPL check exit0:66top+121bottom supplier-pad reconstructions plus12 nonpolar-resistor placement-only checks=199; worst residual0.491mm,no errors. Paste check exit0:245top/373bottom flashes on exactly245/373 pasted pads; no missing/stray/duplicate paste.
- Native selected S-4,T-1,K-legends,K-copper,K-inner all pass. All199 required-fitted members are in schematic/BOM/CPL. There are23 correct individual terminal labels,118visible/91hidden refs,zero silk/mask overlaps and zero legend-distance review items. All visible refs are1.0mm/0.15mm. Independent silk export finds0off-board stroke points.
- Native copper/paste checks cover613 SMD pads and768 via/paste pairs; the sole SMD in-pad exception is exactly two U401 GND0.5/0.3mm vias at(27.3,13.6)/(27.9,13.6),requiring filled/capped planar VIPPO. All five DB125 GND contacts have explicit local thermal setting1. No new pad-hole/paste exception was introduced.
- Independent Fab walk finds209refs,none missing. R10,C29,C92,R8,C5 have zero own-graphic intersections: the five named R12-MFG-01 cases are closed. J122's prior centre-drill label collision is closed. Vector zoom remains necessary for small Fab text.

## Source/process and visual coverage

Applied the PDF skill read-only. Inspected both complete one-page A4 assembly drawings at180dpi and600dpi detailed aft/port,core,power and pyro regions; bottom is mirrored. Complete primary-source pages were also rendered/inspected:
[Bourns p1](https://www.bourns.com/docs/product-datasheets/srp5030t.pdf),
[TI TPS7A91 DSK0010A stencil p36](https://www.ti.com/lit/ds/symlink/tps7a91.pdf),
[DORABO T0-1 sheet1](https://atta.szlcsc.com/upload/public/pdf/source/20251124/8C215F69B14C8E54AE0F8E5023D4AE9F.pdf),
[MA capacitor all 4 pages](https://atta.szlcsc.com/upload/public/pdf/source/20260306/24758A4FC016E80367B87853635CDCC1.pdf),and
[Molex SD-47219-001 sheet1](https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/salesdrawingpdf/472/47219/472192001_sd.pdf)
from its original-document [mirror](https://cdn.promelec.ru/upload/items/2020/09/01/472192001_sd.pdf) after direct maker download failure.

U401 retains two1.13x0.89mm paste windows over1.2x2.0mm pad11(about83.808% rectangular area,the maker84% example). J430 has eight0.8x1.5mm signal and four1.45x2mm shell lands,all on B.Paste; its maker permits0.10/0.12mm stencil and100% openings. DB1251.9/1.3mm copper/drill and3.5mm pitch are as recorded; the maker's1.2mm recommended hole departure already has a seating/assembly disposition. The exact MA sheet supplies no soldering profile,so ORDERING8 correctly keeps C84 absent during both reflows and requires separately validated manual fitting afterward.

Active ORDERING8 includes no-clean paste/no washing,U5 two-reflow confirmation,bottom-first/top-last,all23 current THT contacts and five explicit thermals,preferred0.10mm stencil/supplied apertures,U401 VIPPO,manual C84 and U4 consignment/preview. T-1 finds legal5mm windows,including aft-east37.0-45.5mm. Actual rail/tab artwork,process quote,manufacturer acceptance,hole fill and first articles remain pending obligations. The existing snapshot retains R430/U4 stock blockers and minimum-purchase/cost acceptance; these are not newly demonstrated hardware failures.

Read AGENTS first,both review packets,REQUIREMENTS,current owner decisions and all110 D IDs(including D-R12-01/02/03),r10_plan amendments,AVA_LAYOUT,M3_R10,current R10 validation/deviations,R9 severity precedents,the read-only VEHICLE source and current in-worktree vehicle handoff. Earlier review outcomes supplied context only.

## Limits

No peer round13 report was read. Only this new report pair and ignored probes/renders were written; no canonical build/full check,GUI/native CAD save,git mutation or other-worktree edit. Unbound assembly-directory r10_top/r10_bottom PNGs visibly show older circuit-pass hardware and were excluded; active documentation does not link them. Current PDF evidence is target-bound.

No physical/firmware,electrical/thermal/transient/endurance,VIPPO/soldering/yield,panel,coating,retention/harness/tool/card/stack or flight qualification follows. Maker land/stencil checks were selective,not a new82-code datasheet qualification. Orientation has12 placement-only symmetric-resistor checks and still requires factory preview. Tiny glyph intersections and the stated raster scales do not certify every print scale. No current C/M evidence is withheld.

Full structured checks,measurements,source URLs and limits: `round13_manufacturing.json`.
