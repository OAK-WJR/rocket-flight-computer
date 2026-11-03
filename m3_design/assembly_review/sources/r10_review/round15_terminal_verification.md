Fresh focused independent DB125 verification, R15. Target commit supplied by root: `789f4d516251991bdf1518254d537ff7b41f65bb`. Native PCB SHA-256 before and after: `7866d6b895573eb10c14d0227ee4bdde8b4fba6145529786cd554cdb80121783`. Prepared 2026-10-30T14:08:50Z. Read-only slice verification; no full-review credit.

**PASS for the candidate’s classification and current nominal CAD checks. R15-BOM-02 remains Minor. This scope finds 0 confirmed Critical and 0 confirmed Major issues.** The evidence establishes a missing fit allocation, not actual insertion failure. Retain the present footprint as a CAD candidate pending maker/assembler allocation and first-article qualification; do not enlarge its holes solely from the sharp-rectangle calculation.

Read AGENTS.md, REQUIREMENTS, current owner amendments, relevant R10_DECISIONS through D-R14-03, current assembly instructions, native PCB and library lands. Initial maker/native checks preceded reading the assigned round15_parts report. No other current peer report or probe was read. Root’s target-commit/1909-file freeze is a supplied receipt; no git command was used.

The exact [DORABO T0-1 drawing, 2022-11-26, sheet 1/1](https://atta.szlcsc.com/upload/public/pdf/source/20251124/8C215F69B14C8E54AE0F8E5023D4AE9F.pdf) was freshly fetched: 381230 bytes, SHA-256 `76a55d0cbb4d30bf4d714401b8612365b6b35fedcd9660adae81c0e79d86ff7a`, matching the named static cache. A fresh full-page Poppler render was inspected in memory. Its family/color notation covers the selected 2P green/black, 4P green and 5P green bodies. The orthogonal views show nominal 0.50×0.85 mm pin dimensions and a tapered tip; they do not specify the complete insertion-section corner/burr/form envelope. Pitch is 3.50 mm and the recommended PCB hole is Ø1.20 mm.

The drawing’s linear table gives ±0.20 mm through 6 mm. Applying it independently to both pin dimensions produces a conditional sharp 0.70×1.05 mm rectangle. That is not proof of the manufactured cross-section. Its cited [GB/T 14486-2008 standard concerns moulded plastic parts](https://openstd.samr.gov.cn/bzgk/std/newGbInfo?hcno=D13DCBFC8E64A2B32F77B4CE9EBD4B92). This creates an applicability question for metal-pin dimensions; it does not justify automatically discarding the drawing’s own table. Obtain maker clarification. No guaranteed corner rounding, stamping benefit, lead compliance or tighter metal tolerance was found.

[Current JLC capabilities](https://jlcpcb.com/capabilities/pcb-capabilities) give finished PTH tolerance +0.13/−0.08 mm and hole position ±0.075 mm. An older search snippet says ±0.05 mm; the freshly opened page takes precedence. The page provides no separate guaranteed hole-pitch correlation/allocation. It recommends ≥0.20 mm annulus for multilayer 1 oz, with 0.15 mm stated as absolute minimum. Position’s datum/radial interpretation, layer registration and outer barrel envelope remain insufficiently specified for a certified combined stack.

Native KiCad 10.0.7 API inspection confirms all 23 contacts are circular Ø1.90 mm copper/Ø1.30 mm holes at 3.50 mm pitch, with the exact expected identities and nets:

| Terminal | Part / code | Native origin, mm / rotation | Native pad centers, mm |
|---|---|---|---|
| J1 | DB125-3.5-2P-GN-S / C466970 | (7.4,75.85), −90° | x=7.4; y=74.1,77.6 |
| J121 | DB125-3.5-2P-BK-S / C52993880 | (7.4,55.85), −90° | x=7.4; y=54.1,57.6 |
| J400 | DB125-3.5-2P-GN-S / C466970 | (7.4,65.849999), −90° | x=7.4; y=64.099999,67.599999 |
| J410 | DB125-3.5-4P-GN-S / C2757925 | (38.6,15.5), +90° | x=38.6; y=20.75,17.25,13.75,10.25 |
| J420 | same 4P | (38.6,31.5), +90° | x=38.6; y=36.75,33.25,29.75,26.25 |
| J9 | same 4P | (38.6,47.5), +90° | x=38.6; y=52.75,49.25,45.75,42.25 |
| J122 | DB125-3.5-5P-GN-S / C3646874 | (38.6,71.5), +90° | x=38.6; y=78.5,75,71.5,68,64.5 |

Independent calculations:

- Nominal sharp-section diagonal: `hypot(0.50,0.85)=0.986154146 mm`.
- Conditional maximum sharp-section diagonal: `hypot(0.70,1.05)=1.261942946 mm`.
- Minimum standard finished hole: `1.30−0.08=1.22 mm`.
- Nominal-section diametral allowance at that hole: `+0.233845854 mm`.
- Conditional maximum sharp-section allowance: `−0.041942946 mm`, before pattern/form/assembly allocation.
- Present nominal radial annulus: `(1.90−1.30)/2=0.30 mm`; adjacent land gap: `3.50−1.90=1.60 mm`.

The negative conditional allowance is reproducible. It demonstrates that this independent-envelope model does not close; it does not establish that actual pins violate the required insertion profile. Conversely, the maker’s nominal hole recommendation and nominal positive clearance do not certify every fabrication/part corner. Individual pitch tolerances must not be repeatedly added on top of an already dimensioned row-span tolerance as though all were independent. Relative pattern error after best alignment, pin form and any approved forming process require an explicit allocation.

Focused native S-8 API execution passes: four protected barrels, zero violations. Independent distance calculations over current native polygons find J121.1 at (7.4,54.1), PYRO1_OUT, governs: **1.102501576 mm** from its nominal hole wall to In2 3V3 fill. The nearest fill point is (8.916706,53.222011). Its nominal reserve above 1 mm is 0.102501576 mm. All 23 terminal lands have approximately 0.250500 mm nearest foreign-fill clearance; the smallest non-fill clearance is J121.1 to the 3V3 via at (9.20,52.98), 0.920001 mm.

These native dimensions are not fabricated tolerances. Illustratively, a +0.13 mm finished diameter adds 0.065 mm radius; an additional 0.075 mm displacement toward foreign copper would consume 0.140 mm. That exceeds the present nominal S-8 reserve. This is an unclosed process-corner allocation, not a measured S-8 failure or a new nominal CAD violation. Average plating thickness is not a maximum barrel-wall allowance; layer registration and actual outer barrel dimensions also need process definition.

Hole/land options below are calculations against unchanged current fill, not qualified redesigns:

| Hole / land, mm | Minimum finished hole | Sharp-envelope size-only allowance | Nominal annulus | Adjacent land gap | J121.1 nominal S-8 gap |
|---|---:|---:|---:|---:|---:|
| 1.30 / 1.90 | 1.22 | −0.041943 | 0.30 | 1.60 | 1.102502 |
| 1.35 / 1.90 | 1.27 | +0.008057 | 0.275 | 1.60 | 1.077502 |
| 1.35 / 1.95 | 1.27 | +0.008057 | 0.30 | 1.55 | 1.077502 |
| 1.40 / 1.90 | 1.32 | +0.058057 | 0.25 | 1.60 | 1.052502 |
| 1.40 / 2.00 | 1.32 | +0.058057 | 0.30 | 1.50 | 1.052502 |
| 1.50 / 2.00 | 1.42 | +0.158057 | 0.25 | 1.50 | 1.002502 |

Thus Ø1.35 barely clears the conditional section and leaves no established position/pitch allowance. Ø1.40 does not close the complete fit budget either. Increasing the hole without its land also reduces annulus. Under the illustrative maximum-finished-hole plus 0.075 mm hole-to-pad eccentricity model, residual annulus is 0.160 mm for current 1.30/1.90, 0.110 mm for 1.40/1.90 and 0.160 mm for 1.40/2.00; these exclude etch and outer barrel details and are not fabricator-approved guarantees. A tighter hole process also needs explicit acceptance rather than an assumed automatic benefit.

All five GND pads have explicit `zone_connect=1`. Independent 360-point sampling at radius 1.075 mm confirms four separated fill-contact runs on F.Cu/In1.Cu/B.Cu and zero In2 GND contacts for each. Current GND zones use 0.25 mm thermal gap/0.30 mm spoke width. Changed lands require refill and renewed thermal checks; larger holes change solder-volume and process requirements. [JLC’s assembly guidance](https://jlcpcb.com/blog/pcb-header-design) separately calls for finished-hole, seating and solder-fill inspection. None is qualified by native relief geometry alone.

Concrete closure: retain Minor R15-BOM-02 in the owner/assembler qualification record; replace unbounded “conservative” hole wording with the actual nominal and conditional limits. Obtain the exact pin insertion-profile maximum, relative pitch/form limits and approved seating/lead-form method from maker/assembler. Agree minimum/maximum finished holes, relative pattern error, annulus and barrel-to-inner-copper realization with the fabricator. A sufficient geometric allocation is `Dhole_min ≥ Dpin_circumscribed_max + 2×eresidual + positive assembly allowance`, with residual error defined after permitted alignment/forming. Validate the selected exact part variants on first articles, all 23 contacts, for seating, undamaged barrels/plating and solder fill, then complete existing harness/staking/retention obligations.

If that allocation cannot close, revise the generated drills and lands together, adjust protected inner copper as necessary and rerun covered native DRC/S-8/fill/thermal/fab/reproducibility checks. Preserve pitch, pin roles, orientation and surrounding footprints unless a separately reviewed move is needed. No particular enlarged drill is approved by this verification.

Checks executed: document/source reads; native pad/identity inventory; fresh primary PDF retrieval/hash and full-page in-memory render; live primary fabrication/standards lookup; native copper distance and focused S-8 execution; independent polygon-distance calculation; five-pad thermal sampling; option calculations; before/after PCB hashes. Final geometric scripts exited zero. Early API prototypes failed on unavailable `GetProperties`, UTF8 serialization and optional thermal values; these were corrected. An attempted wx initialization lacked display access and was not retried. Old alternate maker PDF retrieval returned 403, and direct supplier product pages were inaccessible through web; neither was used as current dimensional proof. No CLI, build, full check, git action, GUI validation, physical experiment or source edit was performed.

Residual risks: actual section/pitch limits, insertion force, manufacturing correlation, solderability, wire/tool access, vibration retention and physical assembly remain unverified. This focused evidence supports the existing seven-terminal CAD interface and its nominal electrical isolation; it does not prove whole-board or flight functionality. The Critical/Major insertion-failure hypothesis is rejected for insufficient evidence, while the bounded qualification gap remains Minor.
