# Round 11 — manufacturing, DRC, silkscreen and fabrication

**Result: 0 Critical, 0 Major, 2 Minor findings.** Frozen target supplied by the review packet: commit `21bc3b2`; native PCB SHA-256
`0c50b9fd0930f34edab7129fc21b8e71d0ee03bc079e1900b7e131cece6bfaf8`, independently measured unchanged.
This is manufacturing/CAD review, not assembler, electrical, firmware or physical qualification.

Read the required decisions, requirements, AVA hand-off, revision/validation records and R9 severity precedents.
No other round-11 report was read. Only this report and its matching evidence JSON are delivered.
No CAD, implementation, Git state, build request or fabrication output was changed.

## Findings

### R11-MFG-01 — four DB125 ground contacts retain solid In1 connections

**Minor; worth fixing.** `docs/ORDERING.md:230` says “GND pins use thermal relief.” Four of the five DB125 ground
contacts inherit the full-connection In1 zone (`m3.kicad_pcb:65030`):

| Contact | Native pad line | Centre (mm) | Saved In1 fill at radius 1.075 mm |
|---|---:|---|---:|
| J1.2 | 6514 | 7.000, 77.600 | 360/360 angular samples |
| J9.2 | 7373 | 39.000, 49.250 | 360/360 |
| J410.2 | 11083 | 39.000, 17.250 | 360/360 |
| J420.2 | 15014 | 39.000, 33.250 | 360/360 |

All four have inherited pad/footprint settings; In1 is `ZONE_CONNECTION_FULL=2`.
Their outer layers have thermal relief. J122.5 (`m3.kicad_pcb:3246`) explicitly uses
`ZONE_CONNECTION_THERMAL=1` and has 68/360 samples on each connected layer.
The sampling ring lies outside the 0.950 mm pad radius and inside the nominal 1.200 mm thermal-clearance radius,
so this distinguishes full-plane connection from spokes.

The current hand/selective-solder and hole-fill instructions mitigate assembly risk; no defective joint is demonstrated.
M2 nevertheless requires usable THT ground thermals or a listed exception.
**Fix:** record these four inner-plane exceptions and require preheat/first-article hole-fill inspection, or give the four
pads explicit thermal connections (native per-pad `zone_connect 1`) after a refill/DRC confirms usable spokes. Preserve the frozen board during Phase A.
The [DORABO T0-1 drawing, p1](https://atta.szlcsc.com/upload/public/pdf/source/20251124/8C215F69B14C8E54AE0F8E5023D4AE9F.pdf)
establishes the THT construction; thermal relief is the project's M2 rule.

### R11-MFG-02 — J122's assembly-drawing reference crosses its centre drill

**Minor; worth fixing.** The exported `fab/m3_assembly_top.pdf`, page 1, partly obscures “J122” with its centre hole.
The native Fab text at (38.800,71.500), `m3.kicad_pcb` J122 footprint beginning at line 3047, intersects
J122.3's Ø1.300 mm drill at (39.000,71.500), pad line 3228. Polygon/circle intersection and the rendered PDF agree.
This affects the supplemental assembly drawing.
**Fix:** offset J122's Fab reference into clear space alongside its pin row in the Fab-reference generator, then
regenerate and bind both drawing outputs. Concrete candidate: local Fab text (0,-2.5), giving board (36.5,71.5) mm at
the current 90° footprint rotation; verify the new render. No datasheet limit applies to this drawing-legibility finding.

## Verified coverage

Fresh read-only checks and an independent native-geometry walk produced the following results; detailed values,
all 87 hidden references and all close ring/opening pairs are in `round11_manufacturing.json`.

| Area | Tested coverage / result |
|---|---|
| Binding | `fab_manifest.py`: **5/5 outputs match all 193 recorded CAD/export inputs**. ZIP, BOM, CPL and both assembly PDFs are current. |
| Population | **209 footprints; 199 fitted = 67 top + 132 bottom**, 82 BOM codes, 199 BOM quantities and 199 CPL rows. Native/schematic/BOM identity and footprint comparison: zero missing, extra, duplicate or mismatched fitted references. All 113 required-fitted contract members pass S-4. |
| Orientation | **82/82 reviewed correction entries OK**. Fresh CPL reconstruction: **66 top + 121 bottom**, plus **12 placement-only** nonpolar-resistor checks; zero errors. Worst pad residual 0.491 mm is the retained two-terminal R134 land. DB125 corrections are 0° with ≤0.0001 mm origin offset; J430 uses the reviewed +1.550 mm local-y offset, ≤0.005 mm residual over all 12 lands. Factory body/polarity preview remains required. |
| Gerber/drills | ZIP has **11 layer Gerbers + PTH + NPTH + job file**. PTH: 293 Ø0.300 vias, one Ø0.500 via, 23 Ø1.300 terminal contacts and four 0.600 mm USB shell slots. NPTH: two Ø0.600 J3 locators and three Ø0.991 J2 locators. Five M3 circles remain in Edge.Cuts. Four copper layers, 1.6 mm, ENIG and 35 µm outer copper agree with native manufacturing settings. |
| Paste completeness | **245 top + 373 bottom = 618 flashes** match all native pasted pads; no stray/doubled/missing flashes, regions or draws. An additional independent aperture parser compared every flash's dimensions with the native paste margin and rotation: **618/618**, worst bounding-box delta **0.000500 mm** (0.002 mm tolerance). |
| DB125 | **7 bodies / 23 connected contacts**: three west-facing 2P bodies; three east-facing 4P and one east-facing 5P. Native pitch 3.500 mm, Ø1.900 copper / Ø1.300 drill, 0.300 mm radial annulus, 1.600 mm nominal interpad copper gap. Maker recommends Ø1.200 holes; the larger retained drill is disclosed in qualification notes. All 23 pin legends agree with pad roles. |
| THT process | Current ordering amendment specifies hand/selective soldering for all seven DB125 bodies and inspection of every connected contact; no wave soldering. Nearest bottom courtyard to a THT pad is **1.510 mm**, C83 to J3.4; DB125 nearest is **1.555 mm**, C91 to J9.1/.2. These support the stated local hand/selective process. Inner-plane relief exceptions are R11-MFG-01. |
| Silkscreen | **312 visible items**, including **162 texts = 122 designators + 40 legends**. Minimum text size **1.000 mm** and text/nonzero graphic stroke **0.150 mm**. Two filled dots have zero outline width. Minimum ink-to-mask gap **0.150 mm**, minimum ink-to-edge gap **0.500 mm**; zero overlaps, undersize texts or support-hardware incursions. Required references, all 23 terminal pin labels, six J2 rows, harness note, revision and order mark pass; zero legend-distance residuals. |
| Hidden references | **87 hidden**, all retained among **209 Fab references**. Four top parts use bottom designators: C402, J400, R404, U400. All mandatory connector/safety references remain shown. The one Fab/drill overlap is R11-MFG-02. |
| Mask / vias | **692 native pad openings = 281 top + 411 bottom**. Minimum different-net web **0.100 mm** at U4; none below 0.100 mm. Ordinary via-hole to soldered-pad opening minimum **0.150 mm**; no ordinary hole enters a pad opening. Exactly two allowed U401 vias remain. **17 own-net ring/opening pairs at 16 vias** are below 0.100 mm, worst **0.014 mm**, VBUS via (11.950,30.600) to D4.5; retain this measured manufacturing compromise in the refreshed deviation list. |
| Selected CAD rules | Fresh **6/6 pass**: S-4, LC-1, T-1, K-legends, K-copper, K-rules. This covers local clearance floors, exact VIPPO exception, required assembly population, legend content and the pinned DRU/project rule floors. |

The root owns the requested fresh full `tools/check.sh`/native DRC receipt. This lens did not run CLI DRC, a full gate or
a build, and did not consume the historical `.supervisor/build_result.txt` while the new request was pending.
The AVA two-build result remains explicitly historical evidence, not this lens's new whole-board DRC result.

## Maker/process cross-checks and retained release conditions

- **MicroSD J430:** native B(24.000,24.300), 8 signal lands 0.800×1.500 mm and four shell lands 1.450×2.000 mm,
  zero paste shrinkage on all 12. The [Molex SD-47219-001 Rev G, sheet 1](https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/salesdrawingpdf/472/47219/472192001_sd.pdf)
  requires 100% openings at 0.12 mm stencil or at least 100% at 0.10 mm, and discourages 0.08 mm.
  The maker-hosted download timed out locally; the same signed drawing was rendered from its
  [document mirror](https://cdn.promelec.ru/upload/items/2020/09/01/472192001_sd.pdf).
  Current 0.10 mm/100% instructions agree. Hinge/card retention and open-lid access remain physical checks, with insertion only off/out of the bay.
- **U401:** exactly two GND 0.500/0.300 mm through vias at (27.300,13.600)/(27.900,13.600), both completely inside
  its 1.200×2.000 mm exposed land. Two 1.130×0.890 mm paste windows with 0.220 mm central gap give 83.81% nominal area.
  This agrees with the [TI DSK0010A stencil example, drawing 4218903/C, datasheet p36](https://www.ti.com/lit/ds/symlink/tps7a91.pdf).
  Filling/capping flags and exact CAD exception pass. Resin-filled, copper-capped planar VIPPO remains mandatory in the quote/inspection; ink plugging is insufficient.
- **C84:** required in the current BOM/CPL as MA25V470M8x10 / C46550466, now at F(27.500,78.500), positive pad 1
  VLOGIC at (27.500,81.750). Derived 3.500×1.700 mm lands at ±3.250 mm remain consistent with the recorded land choice.
  The [supplier MA sheet, pp1–4](https://atta.szlcsc.com/upload/public/pdf/source/20260306/24758A4FC016E80367B87853635CDCC1.pdf)
  supplies electrical/body data but no soldering profile or recommended land.
  Ordering explicitly keeps C84 absent from both reflows and manually fits it afterward under a separately validated process.
  Its BOM Assembly cell still reads “SMT”, so order-process acceptance must carry the manual operation. Polarity, seating/height,
  capacitance and ESR before/after fitting remain required first-article evidence.
- **Fine-pitch stencil:** U11's 0.200×0.600 mm apertures have calculated area ratio 0.75 at 0.10 mm stencil
  (0.625 at 0.12 mm). U4's 0.5405×0.329 mm paste is **88.36%** of each 0.575×0.350 mm land.
  [ST TN0018 Rev8 §3.3, p9](https://www.st.com/resource/en/technical_note/tn0018-surface-mounting-guidelines-for-mems-sensors--in-an-lga-package--stmicroelectronics.pdf)
  permits 90–150 µm stencil and 70–90% signal-pad area. Preserve supplied apertures and U4's 0.100 mm mask webs.
- **Vendor/process:** [JLC's current PCB capabilities](https://jlcpcb.com/capabilities/pcb-capabilities) support the measured
  1.0 mm text, 0.15 mm stroke/pad-to-silk and green 1 oz 0.10 mm mask web. Its plug-ink rule requires 0.35 mm clearance;
  **171 ordinary vias** are closer than that to an opening and require the existing tent/mask-cover instruction.
  The large BAT_IN via is 1.000/0.500 mm at (17.500,87.300); preserve its covering instruction.
  [Standard PCBA](https://jlcpcb.com/capabilities/pcb-assembly-capabilities) supports two-sided SMT/THT at 240±5°C with rails/fiducials.
  Current order text retains no-clean paste/no washing, bottom-first/top-last reflow, supplied paste, U4 consignment,
  THT method and hole-fill inspection. [TE MS5611 pp3/17](https://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocFormat=pdf&DocLang=English&DocNm=MS5611-01BA03&DocType=Data+Sheet&PartCntxt=MS561101BA03-50)
  supports the 250°C/40 s maximum and no-clean handling. U5 two-reflow acceptance, actual panel/rail plan, VIPPO,
  C84 manual operation and factory placement preview remain pre-order process conditions.
- **Existing deviations:** L400 still has its recorded proxy land (native 1.800×2.500 mm at ±2.350 mm) and requires the
  existing assembly-qualification disposition. Current ring/web residuals, 87 hidden references and opposite-side
  references need the refreshed board-bound inventory. R430/U4 shortages and the circuit-pass cost snapshot remain
  preliminary procurement evidence. No new quote, supplier stock qualification or flight release is claimed.

All listed pending factory/physical qualifications remain open; their absence alone is not counted as a new Major.

