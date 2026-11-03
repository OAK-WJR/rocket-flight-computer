# Round 17 manufacturing review

Fresh full lens 8 review of commit `ac483f40d38db6e0424227bd32d2a5d5f9f60c3e`.
PCB SHA-256 before and after:
`632a9ad36c19426ede219b6ff6b0d638955665cac1b4704d3392a6afdbe03982`.
46 x 90 x 1.6 mm; 2,256,162 bytes; 209 footprints, 951 segments, 296 vias.
All 1,966 frozen files match before and after. **0 Critical / 0 Major / 2 carried Minor.**
No Critical/Major candidate remains unresolved. This is CAD/manufacturing-file evidence, not assembly or flight qualification.

Read AGENTS first, both target packets, REQUIREMENTS, the complete R10 decisions, plan, AVA handoff, M3_R10,
R10_VALIDATION, current ORDERING and vehicle handoff, R9 severity precedents and the separately owned VEHICLE source.
All 122 unique D IDs and 23 owner scopes were considered under current amendments; their complete index is in the
[JSON report](round17_manufacturing.json). D-R16-03 forbids Minor PCB/generator changes. No peer current-round report,
subagent, GUI retry, git action, canonical build or full check.sh was used.

## Current findings

| ID/status | Evidence and impact | Concrete disposition |
|---|---|---|
| R17-MFG-01, Minor, carried | L400 F(24.2,5.55), rotation 0: native pads 1.8 x 2.5 mm at local x +/-2.35; [Bourns SRP5030T p1](https://www.bourns.com/docs/product-datasheets/srp5030t.pdf) recommends 2.0 x 1.8 at +/-2.25. Outer span is 6.50 mm in both; inner gap is 2.90 versus 2.50. A conditional terminal heel at x1.30 versus native inner edge1.45 leaves a possible 0.15 mm strip. This is a real land departure, not demonstrated joint/converter failure. | Preserve CAD per D-R16-03; retain the exact deviation and obtain assembler disposition plus first-article heel/solder coverage qualification. No maker-land revision is authorized for this Minor. |
| R17-MFG-02, Minor, carried | Fresh native polygons reproduce 16 courtyard stroke intersections, 6 top/10 bottom, while collision outlines remain 0.010-0.040 mm apart. Example: C421 B(33.8,36.75)/U12 B(31.6,39.8), gap0.010 mm. All pairs and poses are embedded in JSON. This is drawing separation, not proof of body collision or access qualification. | Preserve CAD; retain all 16 pairs in deviations and obtain assembler/first-article assessment of actual tolerances/access. Do not shrink courtyard geometry to suppress the count. |

Bourns' exact four-page cached maker PDF was newly rendered/viewed, SHA-256
`c52004cbb76ccf3275e5a94ca6c437fc5a0b81ca8c3643abf1fee902f83741d2`.
Its current primary URL was also inspected; direct PDF download returned403. Prior reports were not substituted for measurements.

## Fresh checks

- Under an explicit root CLI reservation, the genuine 10.0.7 CLI ran in a complete copy of all frozen files,
  including project/rules/libraries: severity-all, all-track, refilled DRC with schematic parity exits0;
  **0 violations / 0 unconnected / 0 parity**. Severity-all ERC exits0 with no ignored checks.
- Genuine fabrication export exits0. BOM82 codes/199 parts and CPL199 rows are byte-identical to the target.
  All14 archive members match after removing creation-date fields/comments only; no geometry normalization.
  Both manifests verify five outputs and their193 input-hash maps agree.
- Fresh correction generation reports `CHECK: none`; CPL reconstructs66 top+121 bottom rows from supplier pads,
  plus12 placement-only nonpolar resistor checks. Worst reconstructed-pad residual0.491 mm. S-4 verifies199
  native/schematic/BOM/CPL identities and fitted quantities. No factory preview is claimed.
- Paste245 top+373 bottom: all618 actual aperture geometries pass, with no missing/stray issue.
  Native S-8, M-6, T-1, K-legends, K-copper, K-inner, K-rules and K-retained pass.
- Silk118 shown/91 hidden references+40 legends, including23 individual terminal-pin labels; minimum1.0 mm
  text/0.15 mm stroke, zero mask overlaps and zero AUD-10 legend-distance findings.
- Both complete one-page A4 assembly PDFs, including mirrored bottom, were viewed at200dpi; all board areas
  were also inspected in six600dpi details. Canonical/fresh page PNGs are byte-identical. All209 Fab references/
  722 characters have zero polygon intersections with Fab graphics/polarity text/drill cutouts. The smallest
  nominal glyph clearance is0.004643 mm at R167; small0.3-1.0 mm vector Fab text needs zoom.
- All23 terminal contacts retain1.30 mm drills/1.90 mm lands/3.50 mm pitch. All five GND contacts have explicit
  thermal overrides and four separated saved-fill spokes on F/In1/B, measured at radius1.10 mm in0.5-degree steps;
  none joins In2 GND. Native J121.1 OUT hole-wall to In2 3V3 is independently **1.102501576 mm**, closest fill
  edge(8.916706,53.222011). This is nominal geometry.

Ignored probe evidence is under `.supervisor/r17_manufacturing_probe/`; JSON records its hashes and exact executed checks.
The CLI reservation was released after exports. No canonical file changed.

## Rejected blocking hypotheses and remaining process scope

Stale/different package, blocking native clearance/parity/ERC, omitted/swapped fitted parts, wrong paste geometry,
ordinary SMD via-in-pad, solid terminal GND joints and obscured/missing actual reference glyphs were tested and
rejected within the scopes above. Conditional DB125 insertion/S-8 corners do not establish a fabricated failure.
The two findings above remain Minor; no pending physical test alone was promoted to a hardware defect.

- Only U401.11 vias(27.3,13.6)/(27.9,13.6),0.5/0.3 mm, use resin-filled/copper-capped planar VIPPO. Preserve its
  two split paste windows. [TI TPS7A91 RevA, September2026](https://www.ti.com/lit/ds/symlink/tps7a91.pdf),
  DSK0010A4218903/C09/2025 package pp34-36 supports the land/stencil geometry; fabrication remains unqualified.
- C84 remains fitted in BOM/CPL with two native paste apertures and BOM Assembly=`SMT`; these do not encode manual
  timing. The existing explicit order remarks must be accepted: absent from both reflows, manually fitted afterward
  under a validated operation, then polarity/height/C/ESR checks. Its exact [MA supplier sheet](https://atta.szlcsc.com/upload/public/pdf/source/20260306/24758A4FC016E80367B87853635CDCC1.pdf)
  supplies no soldering profile. No actual assembly mistake is observed.
- Obtain Standard PCBA panel/process acceptance: selected aft tab/frame, rails/tooling/fiducials, no washing,
  bottom-first/top-last and U5's two passes. Legal T-1 windows do not constitute an accepted panel.
  [Current JLC capabilities](https://jlcpcb.com/capabilities/pcb-assembly-capabilities) still require this process choice.
- Preserve all supplied paste, U4 mask webs and J430's twelve100% openings. [Molex SD-47219-001 RevG,
  sheet1](https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/salesdrawingpdf/472/47219/472192001_sd.pdf)
  permits0.10/0.12 mm stencils and discourages0.08 mm. Actual release/volume and both-side body/pin1/polarity
  factory previews remain open; the locating PDFs are not complete body/polarity maps.
- Hand/selective solder all23 DB125 contacts; finish the four J3 plated shell slots (two0.6x1.7/two0.6x1.4 mm)
  and inspect fill. [DORABO T0-1,2022-11-26,sheet1](https://atta.szlcsc.com/upload/public/pdf/source/20251124/8C215F69B14C8E54AE0F8E5023D4AE9F.pdf)
  gives nominal pins/hole/tail dimensions; [JLC drilling limits](https://jlcpcb.com/capabilities/pcb-capabilities)
  do not resolve exact insertion/form/pattern/outer-barrel/registration allocation. No enlarged drill is approved.

This lens did not execute generator reproducibility, factory preview, stencil release, soldering, physical fit,
firmware or electrical/thermal/transient tests. Root owns integration. Current stock/cost/process/owner acceptance,
VCAP, coating/staking/retention/harness/tool/card and first-article obligations remain open. AGENTS section2 is unchanged;
R9 stays accepted and R10 remains unaccepted/unordered.
