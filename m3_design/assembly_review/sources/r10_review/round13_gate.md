# Round13 gate adversary

Target commit `fa897c81abac3026e75ca5cc88bef0c2659a7130`. PCB SHA-256 before and after: `7355ae1aeb1fdfdf6f64317945a0bf114d94c2bb65fb04adfbcd5a2b8037b09c`. Canonical CAD/source files remained frozen.

**0 Critical / 0 Major / 3 Minor.** All three are newly demonstrated prospective checker gaps. The actual committed board/package have none of the seeded defects. The unchanged broader manifest/native-budget binding rejects the relevant mutants. No whole-gate escape is claimed. No AGENTS section2 rule changes.

## New Minor findings

### R13-GATE-01 — contradictory additional MPN is ignored

`quality_audit/audit_artifacts.py:35–46` requires canonical identity fields and compares only `LCSC` against `LCSC Part`. On a native API copy, add hidden `MPN=CRM2512-FX-20R0ELF` to **R134 (16.5,64.0)**, retaining correct `Manufacturer Part=CRM2512-FX-2R00ELF`. Metadata audit, K-contract and K-actuators report zero issues. Official KiCad10.0.7 all-severity/all-track DRC with schematic parity also reports **0 violations /0 unconnected /0 parity**. This violates AGENTS§3's no-contradictory-second-part-number requirement locally. [Bourns CRM p2](https://www.bourns.com/docs/product-datasheets/CRM.pdf) specifies the resistance-code decimal convention; the two codes name different resistances.

Control: changing the canonical `Manufacturer Part` instead yields one genuine `footprint_symbol_field_mismatch` warning. Exact native SaveBoard control has the original board hash and DRC/parity0. The actual board contains no alternate MPN/Part Number fields. Original manifest rejects either mutant; recomputed native budget also detects changed board provenance.

**Fix:** normalize known part-number aliases in the existing metadata walk and reject conflicting second identities; seed conflicting and matching aliases, or explicitly prohibit redundant aliases. Preserve canonical identity/parity checks.

### R13-GATE-02 — S-4 accepts one reference on two BOM rows

`tools/check_r10.py:212–228` unions designators before checking only each row's Qty. Append a second **R134 (16.5,64.0)** row, Qty1, changed MPN `CRM2512-FX-20R0ELF`, bogus code `C0`, while keeping every original row and the real native PCB/schematic/CPL. Current BOM has **82 rows /199 parts**, R134 at line60; mutant has **83 rows /200 parts**, R134 at lines60/84. Both `assembly_population(require_qty=True)` and **actual S-4** accept it with zero issues and199 required references. The [Bourns ordering code, p2](https://www.bourns.com/docs/product-datasheets/CRM.pdf) makes the conflicting identity concrete; uniqueness is the board's assembly contract, not a maker electrical limit.

Current BOM has unique references and correct quantities. The original manifest rejects the edited CSV; present exporter regeneration from unique board references also prevents it. A faulty future exporter plus newly matching manifest was not executed.

**Fix:** retain first-row ownership for each designator and reject any later row reusing it. Preserve the existing within-row distinct-count semantics and quantity-free CPL.

### R13-GATE-03 — paste flash geometry is unchecked

`tools/paste_check.py:51–81,98–110` records the aperture number but never reads its dimensions. In a scratch copy of the actual F_Paste Gerber, change only **`%ADD28R,0.566000X0.540000*%` → `%ADD28R,0.001000X0.001000*%`**. Repackage all Gerbers with every other byte unchanged. Both direct-layer and actual repacked-zip paste checks accept **245 top /373 bottom flashes**, zero issues.

Ten real pads are affected: R127 at **(19.8,54.24)**, R104/R105/R60/R61. Their native pads/apertures are0.566x0.540mm. Area drops0.30564→0.000001mm², **99.9996728%**, while centres and component IDs remain unchanged. R127 is [C11702 / UNI-ROYAL0402WGF1001TCE, primary supplier product specifications](https://www.lcsc.com/product-detail/C11702.html). The comparison uses existing native paste geometry; no invented maker stencil floor is asserted. Almost-zero solder coverage is a prospective manufacturing inference, not an assembled failure.

Current exported aperture is correct. Original manifest rejects the changed zip. No reissued-manifest/faulty-exporter whole-gate escape or solder-process result is claimed.

**Fix:** parse ADD/macro geometry and compare exported geometry/area with expected native paste polygons. Ordinary leads follow reviewed native paste margins; exposed pads retain maker-approved split/window patterns, with explicit manual-after-reflow process exceptions kept scoped. Preserve valid current patterns through expected-area/pattern semantics or a maker/process-sourced bound where necessary. Add no universal copper-coverage percentage or solder-volume claim. Reject unsupported geometry; retain count/centre/dry-pad rules and test under/oversize, equivalent geometry and valid window/manual exceptions.

## Fresh checks actually executed

| Scope | Actual result |
|---|---|
| Exact committed board, official10.0.7 DRC | All severities/all-track/parity:0 violations,0 unconnected,0 parity; exact native save control identical |
| Native R10 contract | All31 rules accepted in two selected-rule API calls; no build/fullcheck run |
| Native fit | Accepted; two0.1mm outward terminal moves reduce wire room to4.90mm and are rejected against4.95mm |
| Safety/electrical seeds |99nF pyro cap, reset pull-up, automatic ACT enable, real R134 copper bypass, GPS clamp-to-gate, IMU DNP,10ohm servo resistor, wrong SD socket/IMU axis all rejected |
| Local/thermal/width controls | SWD0.507mm rejected/0.508mm accepted; uncapped/20µm-shifted U401 VIPPO rejected; actual0.490mm fire-path segment rejected |
| Model contract |0.01/0.99999 shrink and0.000030mm SD offset rejected; correctly converted doubled model units/half positive scale accepted |
| Route/returns | Fresh scan141 information instances,0 blocking/allowlist/stale; skewed QSPI midpoint rejected; exact duplicate stays AUD-10 information |
| Fast transitions |25 transitions, maximum partner distance1.491643389mm. Removing selected GND partner makes PYRO1_GATE(14.4,53.3)1.900657781mm and is detected |
| Inner copper/barrels |3V3 In1 drawing rejected/In2 power drawing accepted; actual near-J121.1 drawing rejected at0.250mm versus1.0mm |
| Hot-plug evidence validator | Actual saved control accepted; missing/failing/nonfinite corners, relaxed limit, stale source/electrical hash, wrong topology, missing local refinement and149.999µs duration rejected |
| Fab binding | Actual/current exact control five outputs pass; corruption of each of five outputs and missing assembly PDFs rejected; restored package passes |
| Broader catches | Original manifest rejects extra MPN CAD, duplicated BOM and tiny-aperture Gerber zip; native electrical-budget provenance rejects identity CAD mutants |

The structured [round13_gate.json](round13_gate.json) records each executed seed/control, actual issues, source/script hashes and coverage limits. Repro scripts/raw markers are ignored under `.supervisor/r13_gate_probes/`.

## Scope and limits

Read AGENTS first, both review packets, requirements, all110 D IDs/current amendments,22 owner mandates, AVA/plan/M3/R10/R9 records and the read-only VEHICLE/handoff. No peer current-round report or findings were used. R9 provides severity precedents, not a literal definition table. R12's model/inner-copper/per-row-Qty fixes are covered but this lens also exercised the complete board and new fault families.

Four preliminary API-name errors interrupted probes and were corrected; none counts as a pass. An initial equivalent-unit fixture omitted VRML's2.54mm/unit conversion and was correctly rejected as physically2.54x oversized; the corrected positive control passes. Native debug messages did not replace result checks.

No canonical build/fullcheck/source/CAD save, GUI, git mutation, other-worktree edit or child agent. CLI reservation was exclusive and released. F9 extraction/saved2304-case validation was exercised; the full solver sweep was not rerun by this lens. No firmware, physical, thermal/transient, installed RF/ESD, harness/fit, selected-card/e-match or assembly/process qualification follows. All accepted architecture/qualification/procurement deviations remain separately scoped.
