# R16 manufacturing review

Full independent lens8 review of target commit `b1b8658d5bf541795b7e7636c09f2e886ea8c67a`.
PCB before/after: `632a9ad36c19426ede219b6ff6b0d638955665cac1b4704d3392a6afdbe03982`,
46x90x1.6mm,2,256,162bytes. **0 Critical /0 Major /2 carried Minor groups;0 new findings.**
No AGENTS section2 change, acceptance or order is inferred.

| ID | Severity/status | Fresh evidence | Concrete disposition |
|---|---|---|---|
| R16-MFG-01 | Minor,carried R15-MFG-01/R4-BOM-01 | L400 F(24.2,5.55),SRP5030T-6R8M: native1.8x2.5mm lands at localx+/-2.35 have2.90mm inner gap. [Bourns p1](https://www.bourns.com/docs/product-datasheets/srp5030t.pdf) recommends2.0x1.8mm at+/-2.25,gap2.50mm. Conditional heel=(5.7-0.3)/2-(1.1+0.3)=1.30mm versus nativeedge1.45mm: possible0.15mm uncovered strip. | Adopt maker land through covered generator/CAD work, or retain exact deviation for owner/assembler acceptance and actual seating/fillet/tolerance/retention qualification. Nominal contact remains; converter failure is not demonstrated. |
| R16-MFG-02 | Minor,carried R15-MFG-02/D-R14-02 | All209 native courtyards scanned:16 literal ink-intersection pairs,6top/10bottom. Actual ink penetration0.020..0.050mm; native collision polygons remain0.010..0.040mm apart. Complete inventory below. | Retain per-pair owner/assembler first-article/access disposition. Any correction needs deliberate source geometry and covered rebuild/review; do not shrink physical courtyards for a counter. No body collision is established. |

| Pair/side | Location mm | Collision-polygon gap mm | Ink penetration mm |
|---|---|---:|---:|
| C97/D123 F | 23.560000,63.310000 | 0.030000 | 0.030000 |
| R32/LED1 F | 10.465000,42.119999 | 0.040000 | 0.020000 |
| R400/L400 F | 21.040000,2.540000 | 0.030000 | 0.030000 |
| LED2/R33 F | 10.065000,45.545000 | 0.020000 | 0.040000 |
| R121/D8 F | 14.500000,72.745000 | 0.020000 | 0.040000 |
| C60/R60 F | 33.200000,58.165000 | 0.040000 | 0.020000 |
| C421/U12 B | 32.687500,38.350000 | 0.010000 | 0.050000 |
| R152/D121 B | 33.215000,70.260000 | 0.020000 | 0.040000 |
| C83/C28 B | 11.690000,24.900000 | 0.030000 | 0.030000 |
| C85/R86 B | 27.899999,64.987499 | 0.024999 | 0.035001 |
| C22/C26 B | 26.435000,45.935000 | 0.040000 | 0.020000 |
| D121/R151 B | 33.215000,72.740000 | 0.020000 | 0.040000 |
| R64/U5 B | 11.230000,51.405000 | 0.020000 | 0.040000 |
| U4/C31 B | 15.135000,46.875000 | 0.040000 | 0.020000 |
| Y1/R10 B | 20.885000,44.704999 | 0.040000 | 0.020000 |
| C18/C30 B | 17.475000,49.140000 | 0.020000 | 0.040000 |

Fresh verification:

- Official unmodified KiCad10.0.7 under root reservations: complete-copy all-severity/all-track/parity DRC and strict ERC exit0; violations/unconnected/parity/ERC0,ignored checks0. No canonical build/full check.sh was run by this lens.
- Independent five-output export exits0. BOM/CPL byte-identical; all14 CAM archive members identical after creation-time records alone are removed. Both complete assembly180dpi rasters are pixel-identical. The canonical five-output/193-input manifest verifies before and after.
- All199 fitted native parts,67top/132bottom,match199 BOM/CPL designators across82 codes; native/XML/BOM identities,quantities and duplicate checks pass. Metadata audit finds no missing fitted identity/model/courtyard,contradiction or absolute model path.
- Fresh82-code orientation derivation reports CHECK:none and equals the canonical corrections. CPL checks reconstruct187 rows(66top/121bottom),plus12 explicit nonpolar position/side/rotation checks;0errors,worst residual0.491mm under the reviewed part-specific/two-pad tolerances. Production maps contain named proxies/donors. C21190's fresh API request returned403; no fresh exact-code supplement is claimed.
- All618 actual paste apertures,245top/373bottom,match native plotted polygons within1um. No missing/extra/dry flash. U401 retains two1.13x0.89mm windows on its1.2x2.0mm exposed pad; J430 retains full native openings. This is geometry,not stencil-volume/voiding qualification.
- Independent silk scan:308 objects,118 visible/91 hidden references,40legends,text>=1.0mm/stroke>=0.15mm;mask minimum0.150mm atU3,zero mask/edge conflicts. Required individual terminal labels and nearest-pin contracts pass. Fresh F/B-mirrored silk SVGs visually inspected,with only drawing-sheet groups omitted in the visual crop.
- All209 Fab references/722characters exist;completed glyph scan finds no Fab-shape/polarity/drill/cutout/reference intersections. Complete current top/bottom pages and six600dpi details independently inspected. Fab0.3..1.0mm labels require vector zoom. These drawings do not qualify first-article identification.
- All five terminal GND contacts have local thermal override1. Saved-fill sampling at1.1mm radius,1800samples/contact/layer,finds four separated spokes onF/In1/B and noIn2GND connection. K-copper permits exactly two U401.11 GND0.5/0.3mm sites(27.3,13.6)/(27.9,13.6);actual filled/capped/planar fabrication remains mandatory.
- Actual drill archive has296via holes,23terminal holes and4J3 plated slots,plus5NPTH locators;five M3 supports are milled Edge.Cuts circles. Selected S-4,K-legends,K-copper,T-1,M-6,K-rules,M-7,P-11 and native fit pass. These are CAD checks only.

Primary process/drawing review used the PDF skill and fresh complete relevant pages:
[DORABO T0-1 p1](https://atta.szlcsc.com/upload/public/pdf/source/20251124/8C215F69B14C8E54AE0F8E5023D4AE9F.pdf),
[Molex SD-47219-001G sheet1](https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/salesdrawingpdf/472/47219/472192001_sd.pdf),
[TI TPS7A91 pp35-36/drawing4218903-C09/2025](https://www.ti.com/lit/ds/symlink/tps7a91.pdf),
[MA supplier pp2/4](https://atta.szlcsc.com/upload/public/pdf/source/20260306/24758A4FC016E80367B87853635CDCC1.pdf),
[TE MS5611 pp15-17/06-2017](https://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocFormat=pdf&DocLang=English&DocNm=MS5611-01BA03&DocType=Data+Sheet&PartCntxt=MS561101BA03-50),
and [MLT-5020 pp2-3](https://datasheet.lcsc.com/datasheet/pdf/23f5c6599ed9cb614c21ac31ad2b1106.pdf?productCode=C94598).
Selected AOS,HRO and ST drawings are also indexed with exact hashes/pages in JSON.
Molex specifies0.10/0.12mm stencils with100% openings and discourages0.08mm.
U11's0.2x0.6mm aperture gives area ratios0.75/0.625 at0.10/0.12mm,consistent with the written0.10mm preference;no solder-volume guarantee follows.
[JLC capabilities](https://jlcpcb.com/capabilities/pcb-capabilities) and
[via covering](https://jlcpcb.com/help/article/pcb-via-covering) were checked fresh.

Current ORDERING8 preserves manual C84 fitting after BOTH reflows,exact U401 VIPPO,
no PCBA washing/cleaning,bottom-first/top-last,explicit two-U5-reflow acceptance,
hand/selective terminal soldering,all23contact hole-fill checks,J3 slot finishing,
U4 mask webs,consignment and panel/tab acceptance. DB125 insertion/relative-pattern/
finished-hole/barrel allocation and exact VCAP combined C/ESR/process remain open.
These correctly disclosed pending qualifications are not demonstrated hardware failures.

Rejected/closed C/M hypotheses remain individually in JSON:stale package,wrong bottom placement,
unapproved ordinary via-in-pad,C84 reflow exposure,U5 washing/coating conflict,obscured Fab references,
courtyard-as-body-collision,L400-as-proved-converter-failure,terminal process allocation as a proved
failure,and missing terminal thermals. None was promoted from an unmeasured obligation.

Limits:all119D IDs/22owner scopes considered;no currentR16peer report/probe read,peer findings shared,
subagent,owner question,canonical edit,git action,other-worktree write,GUI retry/bypass,order or supplier message.
Native API10.0.6 and officialCLI10.0.7 used. Full build/routing/hot-plug/reproducibility/firmware were not rerun.
Root owns the separate1942tracked-file freeze proof;this lens verifies193manifest inputs/five outputs.
Completed local probes supersede disclosed API-adapter/rasterizer setup failures.
Factory preview/process/first article,actual solder/coating/thermal/retention,harness/tool/card/bore fit,
stock/quote and owner acceptance remain unverified. The separately owned vehicle mirror remains a disclosed integration obligation.

Companion JSON embeds actual checks,source/output hashes,selected native lands,all courtyard pairs,
orientation derivation,closed hypotheses and coverage limits. Final PCB before/after:
`632a9ad36c19426ede219b6ff6b0d638955665cac1b4704d3392a6afdbe03982`.
