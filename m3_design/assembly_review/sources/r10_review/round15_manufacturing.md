# R15 manufacturing review

Full independent lens8 review of committed `789f4d516251991bdf1518254d537ff7b41f65bb`. PCB before/after:
`7866d6b895573eb10c14d0227ee4bdde8b4fba6145529786cd554cdb80121783`,46x90x1.6mm,2,257,812bytes.
**0 Critical /0 Major /2 carried Minor groups;0 new findings.** No AGENTS section2 change.
All1,909 preexisting tracked files remain byte-identical.

| ID | Severity/status | Current evidence | Concrete disposition |
|---|---|---|---|
| R15-MFG-01 | Minor,carried (R14-MFG-01/R13-MFG-02/R12-BOM-01/R4-BOM-01) | L400 F(24.2,5.55),SRP5030T-6R8M: native1.8x2.5mm lands at localx+/-2.35 give2.90mm inner gap; [Bourns p1](https://www.bourns.com/docs/product-datasheets/srp5030t.pdf) recommends2.0x1.8 at+/-2.25,2.50mm gap. Permitted heel=(5.7-0.3)/2-(1.1+0.3)=1.30mm versus nativeedge1.45mm: possible0.15mm uncovered strip. | Adopt maker land through covered generator/CAD work, or retain exact deviation for owner/assembler acceptance and actual seating/fillet/tolerance/retention qualification. Nominal contact remains; no failed required function is demonstrated. |
| R15-MFG-02 | Minor,carried (D-R14-02/current deviation section7) | All209 native courtyards scanned:16 ink-intersection pairs (6top/10bottom),0.020..0.050mm actual stroke penetration; native collision polygons remain0.010..0.040mm apart. Exact inventory below. | Retain per-pair owner/assembler first-article/access disposition. Any removal needs deliberate source geometry/placement and covered rebuild/review; do not shrink a physical courtyard merely to remove ink. No body collision is established. |

Courtyard measurements are native drawing geometry, not a maker tolerance or assembly qualification.
The0.05mm line centres and KiCad's0.005mm-inset cached collision polygons differ;
ink penetration below comes from actual stroked-polygon intersections.

| Pair/side | x,y mm | Collision-polygon gap mm | Actual ink penetration mm |
|---|---|---|---|
| C97/D123 F | 23.560000, 63.310000 | 0.030000 | 0.030000 |
| L400/R400 F | 21.040000, 2.540000 | 0.030000 | 0.030000 |
| LED1/R32 F | 10.465000, 42.119999 | 0.040000 | 0.020000 |
| LED2/R33 F | 10.065000, 45.545000 | 0.020000 | 0.040000 |
| C60/R60 F | 33.200000, 58.165000 | 0.040000 | 0.020000 |
| D8/R121 F | 14.500000, 72.745000 | 0.020000 | 0.040000 |
| C85/R86 B | 27.899999, 64.987499 | 0.024999 | 0.035001 |
| C421/U12 B | 32.687500, 38.350000 | 0.010000 | 0.050000 |
| D121/R152 B | 33.215000, 70.260000 | 0.020000 | 0.040000 |
| R64/U5 B | 11.230000, 51.405000 | 0.020000 | 0.040000 |
| C31/U4 B | 15.135000, 46.875000 | 0.040000 | 0.020000 |
| D121/R151 B | 33.215000, 72.740000 | 0.020000 | 0.040000 |
| C22/C26 B | 26.435000, 45.935000 | 0.040000 | 0.020000 |
| C28/C83 B | 11.690000, 24.900000 | 0.030000 | 0.030000 |
| R10/Y1 B | 20.885000, 44.704999 | 0.040000 | 0.020000 |
| C18/C30 B | 17.475000, 49.140000 | 0.020000 | 0.040000 |

Fresh checks executed:

- Official unmodified KiCad10.0.7,root-reserved CLI: all-severity/all-track/parity DRC exits0;
  violations0,unconnected0,parity0,ignored checks0. No complete build or full check.sh by this lens.
- Independent ignored five-output export exits0. BOM/CPL byte-identical; all14 Gerber/drill/job members
  identical after creation-time records alone are removed. Both complete assembly-page144dpi rasters
  are pixel-identical (top`a9f0fa4a…`,bottom`d2d816d0…`). Canonical manifest:5 outputs/193 inputs match.
- All199 fitted native parts equal199 BOM/CPL designators across82 codes; quantities,identities,
  duplicates and model metadata pass. No absolute model path,missing model,courtyard or fitted identity.
- Fresh production correction derivation:CHECK:none. Canonical CPL verification is187 reconstructed
  (66top/121bottom)+12 placement-only,0 errors,worst0.491mm. A separate exact-code supplement fetched
  [C21190](https://easyeda.com/api/products/C21190/components) and
  [C1329837](https://easyeda.com/api/products/C1329837/components) at
  `2026-10-30T13:53:22.011034..13:53:22.840586Z`. It reconstructs **all199** current placements
  (67top/132bottom),0 placement-only/0 errors,same0.491mm worst. Production maps/corrections/CPL stay frozen.
  Exact timestamps,response/normalized hashes and only normalized pad geometry are embedded in JSON;
  raw API owner/account metadata was discarded. This is supplier geometry,not factory-preview evidence.
- All618 actual paste apertures (245top/373bottom) match native plotted polygons within1um;
  no missing,extra,dry or unsupported geometry. U401 split windows and J430 full openings preserved.
- Independent native polygon scan:308 silk objects,118 visible/91 hidden references,40 legends;
  minimum1.0mm text/0.15mm stroke; minimum mask gap0.150mm (U3 outline toU3.1,B);
  no mask/edge conflict. All209 Fab references/722 characters exist; no outline/polarity-text or
 37 drill/cutout intersections. J122-to-drill gap0.094527mm. Small Fab labels0.3..1.0mm require
  vector zoom; minimum own-Fab shape gap is0.005480mm atR167,without intersection.
- Full current top/bottom assembly pages and600dpi aft/forward details visually inspected independently,
  including terminal bodies,pyro/core/sensors/SD and all changed Fab-label locations. PDF skill applied.
- All five terminal GND contacts have local thermal override1. Saved-fill sampling at1.1mm radius,
  1,800 angular samples/contact/layer,finds four separated spokes onF/In1/B and noIn2 GND connection.
  Exactly two qualified0.5/0.3mm GND vias at(27.3,13.6)/(27.9,13.6) lie inU401.11;
  resin-filled,copper-capped planar VIPPO remains mandatory. Native tenting flags do not qualify fabrication.
- Selected native S-4,K-legends,K-copper,T-1,M-6,K-rules pass. Metadata audit passes209 footprints.

Primary process checks: [DORABO T0-1 p1](https://atta.szlcsc.com/upload/public/pdf/source/20251124/8C215F69B14C8E54AE0F8E5023D4AE9F.pdf)
confirms3.5mm pitch/28-16AWG/4-5mm strip/0.2Nm maximum; native23 contacts use1.9/1.3mm pads/drills
versus maker1.2mm holes,with first-article seating/hole-fill still required.
[Molex SD-47219-001G sheet1](https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/salesdrawingpdf/472/47219/472192001_sd.pdf)
permits0.10/0.12mm stencils with100% openings and discourages0.08mm.
[TI DSK0010A stencil p36,drawing4218903/C09/2025](https://www.ti.com/lit/ds/symlink/tps7a91.pdf)
matches U401's1.13x0.89mm split windows on1.2x2.0mm EP.
U11's0.2x0.6mm rectangle has calculated area ratios0.75/0.625 at0.10/0.12mm thickness;
this supports the existing0.10mm preference,not a solder-volume guarantee.
[MA supplier pp2/4](https://atta.szlcsc.com/upload/public/pdf/source/20260306/24758A4FC016E80367B87853635CDCC1.pdf)
contains no soldering profile: C84 must remain manually fitted after both reflows under the separately
validated operation. [TE MS5611 pp15/17,06/2017](https://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocFormat=pdf&DocLang=English&DocNm=MS5611-01BA03&DocType=Data+Sheet&PartCntxt=MS561101BA03-50)
supports protected ports/no-clean handling. [MLT-5020 pp2/3](https://datasheet.lcsc.com/datasheet/pdf/23f5c6599ed9cb614c21ac31ad2b1106.pdf?productCode=C94598)
gives0.5g nominal and250C peak/10s maximum above245C; the top-only single reflow respects the written limits.
[JLC capabilities](https://jlcpcb.com/capabilities/pcb-capabilities) and
[via-covering guide](https://jlcpcb.com/help/article/pcb-via-covering) were checked fresh;
ordinary ink covering is distinct from the specified planar filled/capped pad-via operation.

Rejected/closed C/M candidates are preserved individually in JSON: stale package,wrong bottom placement,
unqualified ordinary via-in-pad,C84 reflow exposure,U5 washing/coating conflict,obscured Fab identification,
courtyard-as-body-collision and L400-as-proved-converter-failure. Historical missing THT thermals and
Fab-reference collisions are freshly closed by the checks above. None is promoted from pending qualification
to a demonstrated hardware failure.

Limits: all116 D IDs and22 owner mandates considered under current amendments; no current-round peer
report/probe read,peer findings shared,subagent,canonical edit,git mutation,other-worktree access,
GUI retry/bypass,order or supplier message. Prior records are context only. ERC,full routing/hot-plug,
binding/reproducibility and physical/firmware qualification were not rerun by this lens.
Factory preview,exact VIPPO/manual-C84/two-U5-reflow/no-clean/THT/panel acceptance,first article,
actual solder/stencil/coating/thermal/retention/harness/tool/card/bore fit,stock/quote and owner deviation
acceptance remain open. The separately owned vehicle mirror remains a disclosed integration obligation.

Evidence: companion JSON embeds checks,supplier geometry,timestamps,source hashes,closed candidates and
probe digests. All1,909 frozen tracked-file hashes match; inventory digest before/after
`2a41824b222a6bdf4bed2aeb18afb94f616562739104f2e75b00fce768997f44`.
Final PCB SHA-256 before/after:`7866d6b895573eb10c14d0227ee4bdde8b4fba6145529786cd554cdb80121783`.
