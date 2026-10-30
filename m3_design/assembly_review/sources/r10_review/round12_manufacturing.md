# Round 12: manufacturing, native DRC/ERC, silkscreen and fabrication

**Result: 0 Critical, 0 Major, 1 Minor (new).** Target supplied as commit `d57b216c365fc8d18896bceba37f63caf20d52a4`. PCB SHA-256 before and after every probe: `0ad0135cb9ff1f6ace7ef9d5ba9006b727b293d7b5224bb97dad47859b91238d`, 2,263,730 bytes. Canonical CAD, fab and implementation files remain unchanged.

## R12-MFG-01: five Fab labels are obscured by their own outlines

**Minor; new report of inherited drawing geometry.** `fab/m3_assembly_bottom.pdf`, page 1, prints R10, C29, C92, R8 and C5 at 1.0 mm/0.15 mm over their own heavy Fab outlines. Complete-page Poppler inspection and 600 dpi detail views confirm obscured glyphs. Native text/outline polygon intersections agree; R10 intersects six line shapes plus its pin-1 dot, C29/C5 ten line/arc shapes plus the dot. This affects the supplementary assembly aid, including hidden-silk R10/C92; no electrical malfunction is demonstrated.

`r5_post.fab_refs` keeps existing 1 mm text when it does not overlap another reference; `r9_post.fab_clear` checks reference-to-reference boxes. Neither checks this own-outline conflict. No maker rule is needed to establish the visible drawing defect.

**Concrete Fab-only fix:** add a narrow override in `m3_design/r10_post.py` immediately after `silk.fab_refs` and J122's explicit Fab position (current lines 667-669), before `r9_post.fab_clear` (670). Set these five `${REFERENCE}` **B.Fab** texts to **0.4 mm height/width, 0.06 mm stroke**, preserving angles/mirroring:

| Ref | Native position before (mm) | Checked replacement (mm) |
|---|---|---|
| R10 | (20.000, 44.690) | (20.000, 44.790) |
| C29 | (28.000, 43.520) | (27.950, 43.520) |
| C92 | (32.350, 52.500) | unchanged |
| R8 | (9.000, 32.500) | unchanged |
| C5 | (22.200, 71.430) | unchanged |

A native temporary board contains exactly five text-only diff hunks. Each replacement clears all bottom Fab graphics, other references and drills by the checked 0.025 mm. Merely shrinking R10/C29 in place still touches their pin-1 dots, hence their offsets. Official CLI export and Poppler complete-page/detail visual inspection show the replacements legible. **These are small vector-detail labels and may require zoom/high-resolution rendering; production silkscreen remains 1.0/0.15 mm.** This candidate is not applied to the target. Regenerate the PCB hash provenance and bound fab package after implementation. Candidate positions, hashes and render basenames are in the JSON. Root confirmed inspection of the complete after-page and all three detail PNGs; those PNGs were then removed after hashing. The exact temporary candidate PCB/PDF and native-copy proof remain for integration.

## Fresh checks

| Check | Actual result |
|---|---|
| Official unmodified KiCad 10.0.7 DRC | `--severity-all --all-track-errors --schematic-parity --exit-code-violations`: exit 0; **0 violations /0 unconnected /0 parity**, `ignored_checks=[]`, errors/warnings/exclusions included. No refill/save flag. |
| Official 10.0.7 ERC | `--severity-all --exit-code-violations`: exit 0, **0 violations across all 15 sheets**, no ignored checks. CLI reservation released afterward. |
| Exact package binding | `fab_manifest.py` checked twice: **193 CAD/export inputs, all five outputs match**. ZIP/BOM/CPL/both PDFs are current. |
| Population and identity | **209 footprints, 199 fitted =67 top+132 bottom, 82 BOM codes, 199 BOM quantity/CPL rows**; no missing/extra/duplicate BOM refs or native/netlist/BOM identity mismatches. S-4 now verifies all199 required-fitted parts. |
| Placement | Fresh CPL check: **66 top+121 bottom** independently reconstructed, plus12 placement-only nonpolar resistors; no errors; worst residual0.491 mm (retained R134 land). Factory body/polarity preview remains required. |
| Paste | **245 F+373 B=618** flashes match all pasted pads; none missing/stray/doubled. Independent aperture-size/rotation/margin comparison passes618/618, worst bbox difference0.000200 mm against0.002 mm tolerance. |
| Gerber/drill inventory | 11 layer Gerbers, job file, PTH and NPTH. PTH:294 Ø0.300 mm vias, one Ø0.500 mm via,23 Ø1.300 mm terminal contacts, four0.600 mm USB shell slots. NPTH:two Ø0.600 and three Ø0.991 locators. |
| Silkscreen | **308 visible items;158 texts=118 designators+40 legends**. Minimum text1.0 mm/stroke0.15 mm; nonzero graphic stroke0.15 mm, two filled zero-outline-width dots. Minimum ink/mask gap rounds0.150 mm; ink/outer edge0.500 mm; outline export finds0 outside stroke points. |
| Hidden references | **91 hidden**, all retained among209 unique Fab references; complete current list is in JSON. Four top parts have bottom designators: C402/J400/R404/U400. Mandatory connector/safety refs and all terminal tables pass. |
| Mask/vias | 692 pad openings=281 F+411 B. Minimum distinct-net pad-mask web0.100 mm at U4; none below0.100 mm. Ordinary holes do not enter a soldered pad opening; minimum hole gap0.150 mm. Exactly two U401.11 VIPPO sites remain. |
| Selected contracts | **7/7 pass**: S-4, LC-1, M-6, T-1, K-legends, K-copper, K-rules. This is not a complete gate/build. |

The raw zero-finding DRC/ERC JSONs, command flags, all current hidden references, mask/ring coordinates, thermal samples, package hashes and candidate proof are embedded in `round12_manufacturing.json`.

## Prior findings closed

- **R11-MFG-01:** all five DB125 GND contacts now have explicit `zone_connect=1`. Fresh saved-fill sampling at1.075 mm radius finds **four separated spokes,68/360 occupied samples** on F.Cu/In1.Cu/B.Cu for every contact; no In2 GND fill connects there. Native DRC passes. Physical hole fill is still a first-article process check.
- **R11-MFG-02:** J122's Fab reference at(36.5,71.5) is clear of its centre drill at(38.6,71.5), native gap0.0946 mm. Fresh top-PDF detail is legible; no Fab reference intersects a drill anywhere.

## Retained inventory and qualification limits

The current board has **18 same-net ring/opening pairs at17 ordinary vias** below0.100 mm; minimum0.014 mm at VBUS(11.95,30.6) toD4.5. These are covered same-net via rings, not two different-net open mask apertures. Their holes remain outside soldered openings. **171 ordinary vias** are within0.35 mm of a pad opening and need the current tent/mask-cover instruction instead of indiscriminate ink plugging; the two U401 VIPPO sites are separate. All current native via tenting flags are true. Keep this exact board-bound residual inventory and first-article inspection.

Fresh DRC/M-6 pass; the previously recorded C421/U12 and R151/R152-to-D121 courtyard-line stroke residuals are not demonstrated body collisions. L400's retained proxy-land deviation, U4's0.100 mm mask web, C84's separately validated manual operation after both reflows, and the two resin-filled/copper-capped/planar U401 vias remain explicit qualification/process conditions. None is a newly demonstrated hardware failure here.

The checked [JLC PCB capability table](https://jlcpcb.com/capabilities/pcb-capabilities) supports the stated green1 oz mask-web and legend limits and restricts ordinary ink plugging by opening clearance and diameter. [Standard PCBA](https://jlcpcb.com/capabilities/pcb-assembly-capabilities) supports both-sided SMT/THT at240±5°C; actual rail/panel, VIPPO/manual-C84/no-clean/reflow-order/hand-selective-THT acceptance is still required. [ST TN0018 Rev8 §3.3 p9](https://www.st.com/resource/en/technical_note/tn0018-surface-mounting-guidelines-for-mems-sensors--in-an-lga-package--stmicroelectronics.pdf) gives90-150 µm stencil and70-90% signal-pad paste area; U4's native0.5405×0.329 versus0.575×0.350 mm is88.36%, consistent with the selected0.10 mm stencil.

No full `tools/check.sh`, build, Git action, GUI launch/retry, assembly or firmware test was performed. Direct Molex-sheet download failed; no new stencil/hinge qualification is credited to that attempt. R430/U4 stock, factory preview/process acceptance, soldering/hole-fill, U5 two-reflow acceptance, coating, electrical/thermal behavior, retention and actual harness/screwdriver/bore fit remain open. No other current-round lens report was read. Historical records are context; this report's native/PDF checks are fresh.
