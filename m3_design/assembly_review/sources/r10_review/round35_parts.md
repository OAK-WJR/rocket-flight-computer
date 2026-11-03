# R10 round 35 parts lens

Target commit `c3c4249`, board `a0ec075e…` (SHA-256 `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c` before and after).

**Totals: 0 Critical / 0 Major / 0 Minor real errors.**

## Findings

None.

## Fix verification

- R34-TRI-01: confirmed. `parts_qualification.md:1061-1062` points to `hotplug_results.json` / `hotplug_inputs.json` and M3_R10 "Current state"; `hotplug.md` opens with the round 34 pointer to the `a0ec075e…` results.

## Observations (not counted)

- BOM (81 JLC lines + C84 owner line) vs board fields: LCSC, Manufacturer Part, footprint and value agree for all 207 BOM references; the 9 non-BOM footprints (TP74/80-83/88/120/122, J2) are excluded from BOM and position files by attribute.
- CPL: 206 rows, sides all match the board; positions equal the board positions except J3 (-0.095 mm x) and J430 (+1.55 mm y), the recorded JLC-footprint origin offsets (parts_qualification 'microSD socket' +1.550 mm).
- jlc_orient --verify-cpl (read-only) on the committed CPL: 67 top + 125 bottom rows rebuilt, errors none, 14 placement-only; worst residual 0.491 mm is inside the 2-pad 0.6 mm tolerance.
- Every manufacturer part number decodes to the BOM value / rating (Samsung, Murata, Yageo CC/RC/RT, Fenghua, UniRoyal incl. 0603WAF220KT5E = 2.2 ohm and 25121WF360LT4E = 0.36 ohm by the UniRoyal K = 1e-2 / L = 1e-3 multiplier, Vishay MCT 2004B).
- Capacitor and semiconductor voltage ratings exceed their nets' worst operating points (BAT_IN up to the SMBJ12CA 19.9 V clamp on 25/50 V parts; RAW_PROTECTED <= 10.18 V OVLO; Q120/Q121 Vgs about 16.6 V at the clamp vs +-25 V; Q124/Q122/Q123 Vds <= 19.9 V vs 30 V; AON7524/AO3400A Vgs 3.3 V vs +-12 V).
- Pin maps of U9 (TPS25947 RPW), U11 (TPS2121 RUX), U12 (TXU0202 DCU), U13 (TPS709, EN floating allowed, SBVS... p. 'EN can be left floating'), U401 (TPS7A91 DSK), U2/U400 (AP6320x), U10/U402 (TPS2553), Q120/Q121, Q124, D4, D121, D120 (BAT54A common anode pin 3), U3, U5, J430 match the cached maker datasheets.
- parts_qualification spot recalculations reproduce: R134 1.97109 ohm / 35.7975 W / 61.20 / 44.13 W chart reads / 36.345 vs 35.851 W at 85 C; floating-gate tail 1087.344 ohm, 0.6782 ms; IWDG 28.571-32.653 ms; continuity bands 99.3689 / 99.3379 / 146.23 mV; 3.342171 V single-fault clamp; U9 minimum 3.96/1.0035 = 3.946188 A; fire loop 4.4678 ohm branch; LDO 0.48965 W, 109.2-123.9 C, 112.3 C/W ceiling; R405 bleeder 5.634 mA; C123 tau 7.1 us.
- Datasheet facts checked against cached PDFs: SRP5030T-6R8M 76.2 mOhm / 4 A / 4.3 A; TPS7A91 ILIM 1.5-1.9 A; AP63201 peak limit 2.5-3.1 A; TPS2553 DBV 135 mOhm max; TPS25947 3.96-4.84 A at 750 ohm; CRM2512 2 W at 70 C; NX3225GA STD-CRG-2 CL 8 pF; MLT-5020 -20..+70 C; LED1 -30..+85 C; LED2 -40..+85 C.
- MLT-5020 coil 12 +-3 ohm with 3.3 V drive is inside the maker's 2-4 Vo-p operating range; current is a recorded firmware/bench item (AGENTS buzzer row), not a rating violation.
- docs/M3_R10.md:1047 (L1 at (33.0,71.6), C88.1 / J400 shell-pad clearances) is labelled as the R4-MEC-03 inventory on 877d0199...; outside this lens (mechanics) and dated.
- cost_check.json: 45 Extended of 81 charged codes, 60.47 + 123.93/5 = 85.26 USD per board and 83.96/5 = 16.79 fixed fees, matching AGENTS, ORDERING 8.1 and parts_qualification.

## Checks executed

- sha256 of m3.kicad_pcb before and after
- pcbnew dump of all 216 footprints (fields, value, footprint, side, rotation, DNP/BOM/pos attributes, pad nets) into .supervisor/r35_parts/fps.json
- BOM/owner BOM/CPL cross-check script .supervisor/r35_parts/cmp.py (identity, footprint, value, side, position, rotation deltas)
- tools/jlc_orient.py --verify-cpl on the committed CPL (read-only)
- pdftotext of cached maker datasheets and grep of ratings, pin functions and temperature ranges
- recalculation of the parts_qualification R134 pulse, gate tail, IWDG, continuity, U9 limit, fire loop, LDO thermal and bleeder figures
- U401 pad 11 / thermal via / paste geometry read from the board
- cost_check.json totals and input hashes against the committed BOM/CPL

## Coverage limits

- Datasheets read from the local cache (.supervisor/r14_parts_pdf), not re-downloaded
- No live LCSC/JLC page re-read; supplier stock/cost not re-queried
- CPL bottom-side rotation convention itself (KiBot mirror_bottom) is an Inference already recorded; not re-validated against a JLC preview
- Schematic fields not separately compared beyond the board (r10_sch_check / quality_audit cover sync)
