# Round 25 docs_binding lens (R10, commit c4bb56b)

Board SHA-256 before and after: `92c3ad59174afe1ffe206f6384c8cd9a8962e09647ccd6a8c418b95b5312056f`. Reviewer: Claude. Read-only.

**Totals: 0 Critical / 0 Major / 1 Minor.**

## Findings

### R25-DOCS_BINDING-01 (doc, Minor): two current-board statements name the superseded `1407e850…`
- **Contradicts:** AGENTS.md section 1 status and M3_R10 "The board" (current PCB `92c3ad59…`); R10_VALIDATION "Inventory basis" (section 1 is for `92c3ad59…`).
- **Evidence:** `docs/FMEA_REDUNDANCY.md` line 86 (row I-11, V-19, H-6 (R10)): "**Current R10 (`1407e850…`; …)**". The committed board hashes to `92c3ad59…`; `1407e850…` is the f2b8251 board. The label went 5516eeec (9b27268) → 1407e850 (f2b8251) and was not advanced in the fix pass. `docs/R10_VALIDATION.md` line 2329 (S-8 barrels, section 1): "6 of them carry plated barrels on this board (`1407e850…`), 12 barrels in all". The count is right on `92c3ad59…` (check_r10 S-8: 12 barrels), but the board named is wrong.
- **Fix:** FMEA line 86 → "Current R10 (`92c3ad59…`; …)"; R10_VALIDATION line 2329 → "on this board (`92c3ad59…`, unchanged from `1407e850…`)".

## Fix verification
- D-R24-18 BAT_FAULT_N chamfer cap: confirmed (F.Cu chamfer (16.55,83.03)-(16.87,83.35); BAT_ENABLE via (17.1,82.8) to BAT_FAULT_N 0.200 mm (pcbnew shape clearance))
- D-R24-19 EN text with D402 leakage: confirmed (docs binding only; timing model not re-derived) (Records agree: 10.3/20.1/26.0 ms, 8.2 ms at 5.73 V, 5.96 V, 30-130 ms in AGENTS, STATUS, M3_R10, REQUIREMENTS F6, ORDERING 8.3, R10_VALIDATION row 21, parts_qualification, binding note; 5.7 mV = 50 nA x R80 x R81/(R80+R165+R81) recomputed 5.69 mV)
- D-R24-20 check_r10 M-8: confirmed (check_r10 37/37 OK; six courtyards under 2.5 mm with the recorded distances)
- D-R24-23 CPL row counts in records: confirmed (CPL 70 Top + 136 Bottom = 206)
- Round 24 fix docs lane (round24_fix_docs.md): partly (Board-table counts, cost, stock, links all match; two current-board labels missed (R25-DOCS_BINDING-01))

## Checks executed
- Board SHA-256 before/after: 92c3ad59... both (shasum -a 256)
- pcbnew read-only measure (KiCad 10.0.7 Python): 216 footprints, 1057 segments, 307 vias (168 GND; 302 at 0.5/0.3, 4 at 0.6/0.3, 1 at 1.0/0.5), 1867.046187 mm track, 4 layers, 1.6 mm, outline 46 x 90, 2,363,951 bytes; 124 visible / 92 hidden references, 44 board silk legends
- Every 'REF at F/B(x,y)' and 'REF (x,y)' statement in the 14 scoped files compared against footprint positions/sides (regex probe coords.py / coords2.py); all mismatches are before->after history or R9 sections
- Nets/pinouts: J1, J400, J121, J122, J9, J410, J420, J440, D402, R165, R80, R81, C87, U9, Q120/Q121, R119/R120 pad nets; BAT_SW_RETURN = {J400.2, R165.1, D402.1}
- pin_table.tsv r10_net vs U1 pad nets on the board: 100 rows, 0 mismatches; pin_table SHA matches r10_binding_note.json; binding note board_sha256 = 92c3ad59
- Vias named in docs: EN via (17.1,82.8) BAT_ENABLE; D-R24 vias (15.4,72.85), (11.74,72.3), (14.2,46.0), (18.3,36.8), (32.3,60.1), (34.5,62.4), (30.45,51.4), (28.1,59.4), (29.75,11.65), (16.6,28.0), (22.0,62.25), (5.15,65.575), (17.5,87.15); U401 VIPPO vias (27.3,13.6)/(27.9,13.6) GND
- BAT_ENABLE via to BAT_FAULT_N F.Cu gap 0.200 mm; BAT_FAULT_N chamfer (16.55,83.03)-(16.87,83.35) 0.453 mm
- D402 tap 4.114 mm (2.59+0.509+1.015); U9.1->via->R81.1 EN path 3.890 mm
- M-8 courtyard distances: R400/R401/R404 1.025, C403 1.955, C95 1.505, R166 1.755 mm (only six under 2.5 mm)
- Mounting holes from Edge_Cuts gerber: 3.2 mm circles at (4,4), (42,4), (4,44.3), (3.7,86), (42,86)
- Fab package: BOM 81 lines, CPL 206 rows (70 Top / 136 Bottom), paste flashes 249 F / 381 B, manifest outputs hashes verified, manifest binds board 92c3ad59; BOM/owner BOM/CPL/cost/stock byte-identical between f2b8251 and c4bb56b
- cost_check.json: parts 60.8123 + 81 x 1.53/5 = 85.598 -> $85.60, +$1.19 over $84.41; min-purchase parts 61.35 -> $86.14; fixed fees 83.96/5 = 16.79 -> $102.39; +14.93/5 -> $105.38; 45 Extended charged codes; stock_check: U4 9/2, U9 28/-83 min 7, C535146 201/194 vs 45
- tools/fit_check.py (profile r10, report in probe dir): wire room 5.003 mm on all eight terminals; LED2.2 3.808 mm from (4,44.3)
- tools/check_r10.py (report in probe dir): 37 rules OK, S-8 12 barrels, K-binding OK, M-8 six queries
- tools/route_check.py profile r10 (report in probe dir): 0 failing, 0 allowlisted, 0 stale, 5 unrecorded leftovers
- tools/test_r10_check.py: 263 test functions (static count)
- Silkscreen pin legends: 13 bottom pin legends match ORDERING 8.2 and R10_VEHICLE_HANDOFF
- R18_BARREL_KEEPOUT_* zones: ten; parts_budget.json SHA 52ada1ed... and board hash 92c3ad59
- Relative markdown links and anchors in the 13 scoped .md files: 0 broken (links.py)
- Decision ledger arithmetic: 126 + (11+15+11+9+7+11+23 = 87) = 213

## Observations (not counted)
- M3_R10.md 'Cost and stock' says D402 'adds $0.2306 per board' while ORDERING/R10_VALIDATION say D402 plus price movement adds $0.24 ($85.36 at 2026-11-01T23:44:48Z to $85.60); not contradictory, the M3_R10 sentence omits the price movement.
- Board silk prints '1:E1-' with an ASCII hyphen; docs write `1:E1−` (Unicode minus); same legend.
- CPL Mid for J430 is (24.0,-25.85) while the footprint origin is (24.0,24.3); a JLC centre/correction convention, not a docs statement checked here.

## Coverage limits
- Docs are about 9,600 lines; current-state sections, coordinates, hashes, counts, cost/stock, pinouts, legends and links were checked mechanically or by reading; long narrative sections (M3_R10 Firmware, R10_VALIDATION round histories, ORDERING 8.3 checklist prose) were sampled, not read line by line.
- Calculations (EN timing, hot-plug, fire budget, thermal) were checked for consistency across documents, not re-derived from models, except the D402 5.7 mV and the cost arithmetic.
- Test counts other than R10 263 and check_r10 37 were not re-run (no full check.sh by rule).
