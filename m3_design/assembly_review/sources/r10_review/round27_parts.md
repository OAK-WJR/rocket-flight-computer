# R10 round 27: parts lens (Claude)

Target commit `816038c`; board SHA-256 before and after `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c`.

**Totals: 0 Critical / 0 Major / 0 Minor.** No real errors found.

## Findings

None.

## Fix verification

- **D-R26-02 / D-R26-04 CPL rows C10, C11, R164, R173**: CPL C10 (17.5,-53.5) Bottom 180, C11 (17.5,-51.45) Bottom 180, R164 (17.325,-55.25) Bottom 0, R173 (16.87,-59.05) Bottom 270; board origins (17.5,53.5), (17.5,51.45), (17.325,55.25), (16.87,59.05), rotations unchanged from 3d8e845; jlc_orient --verify-cpl 0 errors; BOM and owner BOM byte-identical to 3d8e845. Verdict: confirmed.
- **D-R26-01 terminal pins 3/4 unconnected inner rings removed**: J9/J410/J420/J440 pads 3,4: size 1.9 x 1.9 mm, drill 1.3 mm, layer set unchanged; only the unconnected-layer mode changed (0 -> 3); BOM line C2757925 and CPL rows unchanged. Verdict: confirmed (parts aspect only).
- **Supplier evidence re-run after the CPL move**: cost_check.json 85.26 USD, 2026-11-02T12:44:13Z, binds BOM 00af5358, owner BOM c48868b3, CPL 1f899750; stock_check.json 12:43:17Z; AGENTS, M3_R10, ORDERING, R10_VALIDATION, REQUIREMENTS, HANDOFF and STATUS quote these. Verdict: confirmed.

## Observations (not counted)

- BOM/CPL/board/schematic agree on all 207 BOM-listed parts: LCSC, Manufacturer Part, value and footprint identical on board and schematic (kicad-cli sch export bom vs pcbnew fields), 0 mismatches; 9 excluded parts (J2, 8 TPs) are out of both.
- Every CPL row's position equals the board origin (y negated) except J3 (x 4.505 vs 4.6) and J430 (y 25.85 vs 24.3), which are the jlc_orient footprint-origin corrections; jlc_orient --verify-cpl rebuilds all 192 matched rows from JLC's footprints with 0 errors.
- The four moved CPL rows (C10 17.5/-53.5 180, C11 17.5/-51.45 180, R164 17.325/-55.25 0, R173 16.87/-59.05 270, all Bottom) match the board positions and unchanged board rotations; r10_place.tsv matches all 216 footprints.
- Manufacturer-name spelling differs between the board field and tools/verified_part_metadata.json for C3013496 (Bourns vs BOURNS) and C4241878 (Vishay Beyschlag vs Vishay Intertech); same maker, LCSC and MPN agree, so no contradictory part number.
- MPN decodes match values: 0603WAF220KT5E = 2.2 ohm (UniOhm K = x0.01), 25121WF360LT4E = 0.36 ohm, MCT0603MD2004BP500 = 2 Mohm 0.1 %, FRC0603F2262TS = 22.6 k; check_r10 S-4 (MPN value decode) passes on the exported BOM/CPL.
- Voltage ratings vs operating points: every capacitor's rating is at least 1.9x its net's maximum (16 V parts on 3V3 / VBUS / VCAP / CAM_IO_3V3; 25 V or 50 V on BAT_IN / RAW_PROTECTED / PORT rails, 8.4 V pack, TVS-clamped); ESD103-B1-02EL VRWM +/-15 V vs J400.2's about 5.2 V closed (Infineon datasheet, IR max 50 nA at 15 V, as the records use).
- Resistor steady-state dissipation is far below rating: R92 3.3 k on RAW_PROTECTED 21 mW, R405 820 ohm on PORT_4V8 28 mW, R167 7 mW (0603, 0.1 W); R134 / R166 pulse duty is recorded as pending qualification.
- Pin mappings checked against datasheets: BAT54A (pin 3 common anode = 3V3, cold pull-up), SRV05-4, USBLC6-2SC6, TPS2553 (EN active high), TPS709 (EN floating = on, "EN can be left floating"), TPS7A9101 (EN pin 7 to IN, SS_CTRL pin 6 to GND, IN 9/10, OUT 1/2), AONR21357 back-to-back, AO3400A, AON7524.
- U400 (AP63201) uses 6.8 uH and no feed-forward capacitor at 5.456 V, whereas DS41326 Table 1 lists 10 uH and C4 100 pF for 5 V; the table is a recommendation the R10 records do not claim to follow, and L sits in the datasheet's 2.2-10 uH range, so not a finding.
- Feedback dividers reproduce the documented rails: PORT_5V3 = 0.8 x (1 + 58.2 k / 10 k) = 5.456 V; PORT_4V8 = 0.8 x (1 + 49.9 k / 10 k) = 4.792 V.
- Supplier counts in the records match the committed files: 81 JLC codes (45 Extended / 36 Basic) + C84 owner line, 206 CPL rows (70 top / 136 bottom), $85.26 at 2026-11-02T12:44:13Z (cost_check.json), stock 12:43:17Z; paste_check reproduces 249 / 381 flashes.
- D-R26-01 changed only the unconnected-layer mode of the 4-way terminals' pins 3/4 (J9, J410, J420, J440); pad size 1.9 mm, drill 1.3 mm and layer set are unchanged, so the BOM part, land and CPL are unaffected.

## Checks executed

- pcbnew field dump of all 216 footprints vs m3_bom_jlc.csv / m3_bom_owner.csv / m3_cpl_jlc.csv (.supervisor/r27_parts/bomcpl.py)
- kicad-cli 10.0.7 sch export bom vs board fields (.supervisor/r27_parts/sch_bom.csv)
- tools/jlc_orient.py --verify-cpl (output to probe dir): 67 top + 125 bottom rebuilt, 0 errors, 14 placement-only
- tools/paste_check.py on the committed zip: 249 / 381 flashes, OK
- tools/check_r10.py --only S-4 --bom --cpl: OK
- tools/fab_manifest.py (verify): 6 outputs match
- pad-by-pad comparison 3d8e845 vs 816038c boards (.supervisor/r27_parts/padcmp.py)
- r10_place.tsv vs board positions
- net-per-pad dump and voltage/power rating review (.supervisor/r27_parts/nets.txt)
- datasheet reads: Infineon ESD103, BAT54A, TPS709, TPS7A91, TPS25947, AP6320x, Bourns SRP5030T

## Coverage limits

- Did not query JLC/LCSC live; supplier data taken from committed files.
- Did not re-verify every custom footprint land against its maker drawing (prior rounds' scope); checked only the D-R26 changes and pin-to-net mapping of the actives.
- Pulse ratings of R134 / R166 not re-derived; records list them as pending qualification.
