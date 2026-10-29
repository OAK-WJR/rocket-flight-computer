# R9 review pass 2: manufacturability and fab package (independent review)

Read-only review, 2026-10-25 PDT (2026-10-26 01:14–02:30Z), of the R9 board after review pass 1's fix pass. Worktree
`rocket-flight-computer-r9`, branch `m3-assy-r9`, uncommitted, on top of R8 `9c8179b`.

- **Board:** `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
  `4f841a0e44ebb1829ad7996dfe6320ed527fce1fdb1e5ff11658e0705b44ac14`, hashed before the first run and after the last;
  unchanged. `git status --short` was identical before and after every run. No repository file was written except
  this report; every regeneration and experiment went to the session scratch folder `r9review/dfm2/` (deleted at the
  end).
- **Coordinates:** KiCad mm, x = 0 the west (left) edge, y = 0 the aft (SMA) edge; Gerber Y = −y.
- **Inference** marks anything not measured and not taken from a maker or JLC document (AGENTS §2.5).
- **Previous pass in this dimension:** `pass1_dfm.md` (on `fc3d5b34…`), its fix pass (`fix1_handoff.md`,
  R9_VALIDATION "Review pass 1"). §2 checks each of its eight findings; §4 checks every fix-pass change that touches
  the fab package.

## 1. Summary

**Critical 0, Major 0, Minor 3 (all three worth fixing: two are order text or records, one is an owner option on a
generator table).**

The fab package is complete, reproducible and bound to `4f841a0e…`:
- `tools/check.sh` exits 0: DRC 0 at every severity (no ignored check; warnings and exclusions included),
  unconnected 0, parity 0, ERC 0; metadata / 3D audit; silkscreen; fit; plate model; rule-H seeded suite; check_r9
  40 / 40; route_check r9 0 failing / 0 allowlisted / 0 leftovers; check_actuators.
- `export_fab.py --out <scratch>` gives a BOM (`ab3d8171…`) and CPL (`e879ae2a…`) byte-identical to `fab/`. All 14
  Gerber, drill and job files equal `fab/m3_gerber.zip` once the creation-date line is removed.
- `jlc_orient.py --out <scratch>` regenerates `tools/jlc_corrections.json` byte for byte (CHECK: none).
- `--verify-cpl` (78 top + 133 bottom rows rebuilt, 8 placement-only, worst residual 0.491 mm), `paste_check`
  (F 335 / B 372 flashes, 20 dry pads), `fab_manifest` (both on `fab/` and on the scratch export) and
  `check_procurement.py` (cost-only and full) are OK.
- My live JLC run (scratch copy of the BOM / CPL, 2026-10-26 01:29–01:30Z) gives $109.39 per board (the record:
  $109.38 at 00:57–01:00Z), 52 of 52 extended codes, short none, thin none; U4 40 and U30 34 in JLC stock.
- The six DFM test suites pass (100 tests: paste_check 5, fab_validation 23, procurement 15, r9_sch 21, r9_post 13,
  fit_check 23).

Every pass-1 DFM finding is closed or properly dispositioned (§2). The fix pass's changes leave the manufacturing
geometry sound (§4):
- Its 12 new or moved vias (the three U31 module-ground vias, the moved strip grid via, the RAW_ACT via
  (31.5, 78.2), the ground aid's copper-stage and re-placed vias) all keep their rings ≥ 0.16 mm and their holes
  ≥ 0.31 mm from every mask opening.
- No via lies in any pad or test pad.
- C98's new CPL row (39.275, −64.2, Bottom, 0) is verified by `--verify-cpl`.
- The silkscreen changes only round C98: C98's designator moved, R87's appeared, and U11's is now hidden (listed in
  M3_R9; U11 keeps its pin-1 dot).

The three findings:
1. **R9P2-DFM-01:** J1's +180° body correction puts JLC's pin 1 on our pin 4, the same pin-1 mismatch as the mirrored
   terminals. The order remark and the expected DFM query that pass 1's fix added (ORDERING l. 103, l. 115) name only
   J121 / J124 / J122. A JLC "pin-1 correction" of J1 would turn its wire entry aft, 0.64 mm from J124's body.
2. **R9P2-DFM-02:** C21 offers the owner only "all four J122 GND pins relieved" (the fix pass found a new
   single-spoke island) or "all four solid". A third option works: relieve J122.6 / 9 / 12 and keep J122.3 solid. On a
   scratch copy it passes every gate of `r9_ground_check.py` (DRC with parity, islands P7 still 9, reach, copper,
   reference, pyro, contract, actuators) and the whole `tools/check.sh`, with 4 / 4 / 2 spokes per relieved pin; the
   servo GND return goes from 0.32 to 0.33 mΩ. It cuts the solid through-hole GND joints from four to one, and leaves
   M2's relief rule with one justified exception instead of four.
3. **R9P2-DFM-03:** three record statements went stale with the fix pass. ORDERING l. 3 says no independent review
   pass has run on R9. ORDERING's §7 Sled row still gives step 10's "nearest 4.60 mm, R300.2", where `fit_check` now
   gives C98.1 at 4.483 mm from (42, 59.5). The open R9P1-DFM-08's trigger ("at the next ground-table change") has
   passed: the fix pass regenerated the table.

## 2. Pass-1 DFM findings on `4f841a0e…`

| Pass-1 ID | Disposition in the records | Measured now | Status |
|---|---|---|---|
| R9P1-DFM-01 (mirrored pin-1, no order remark) | Fixed (records): ORDERING §4 remark l. 103, expected query l. 115 | Both present and correct for J121 / J124 / J122. CPL J121 / J124 (10.1, −73.27 / −83.5, Top, 90), J122 (23.0, −62.0, Top, 180); `jlc_corrections.json` theta 0, offset 0, residual 0 through PAD_ALIAS | **Closed.** Residual gap for J1: R9P2-DFM-01 |
| R9P1-DFM-02 (actuator gate pads 0.15 mm from GND pour) | Listed C19; REQUIREMENTS "Accepted risks" (l. 100) retired for the pyro gate nets only, kept for ACT_GATE / ACT_DRV | C120.2, R121.1, Q121.4 (ACT_GATE), Q122.3, R121.2 (ACT_DRV) 0.1505 mm from the B.Cu GND fill; R120.2 0.9325, Q120.4 1.4355, TP121.1 1.0005 mm (as C19) | **Properly dispositioned** (owner option recorded) |
| R9P1-DFM-03 (J122 GND pins solid, unlisted) | Listed C21; M2's relief pointer names R9_VALIDATION C21 (l. 75) | J122.3 / 6 / 9 / 12 pad-level FULL: solid on F.Cu and In1; on B.Cu solid round 0.84 of the ring, the north side held off by the RAW_ACT B.Cu pour (0.30 mm away); J122.3 also on In2 (0.38 of the ring) | **Properly dispositioned**; a third option measured: R9P2-DFM-02 |
| R9P1-DFM-04 (own-net via rings under JLC's 0.10 mm web) | Listed C13 | Mask: 23 own-net pairs at 20 vias under 0.10 mm, worst 0.005 (GND (42.0, 81.26) to C8.2 / C9.2), 0.007 (R63.2), 0.014 (D4.5); foreign minimum 0.150 mm; every hole ≥ 0.107 mm from its opening. Stencil: 18 pairs at 15 vias under 0.10 mm, worst 0.005 mm, no overlap | **Properly dispositioned.** C13's "21 pairs at 18 vias" is the gate's paste model (`check_r8.paste_polys`): Q121.1–.3 sit at 0.090 mm there but 0.114 mm on the stencil. The model is conservative, so this is not a defect (observation) |
| R9P1-DFM-05 (M1's U4 clause) | Fixed (records) | M1 (l. 74): "U4 … has been out of JLC stock: if the order-day stock run shows it short or thin, it is bought … and consigned"; this agrees with "R9 acceptance" and ORDERING §1 | **Closed** |
| R9P1-DFM-06 (J1 legends split top / bottom) | Open ("at the next forward-edge ground change") | Unchanged: `1:BAT+`, `4:SW` top; `2:GND`, `3:SW` bottom. Two of the three blocking vias, (17.525, 101.1) and (22.525, 101.1), are C80.2 / C96.2's input-capacitor GND vias (`r9_power.py` l. 535–536), not ground-table vias | Open, cosmetic; acceptable as recorded |
| R9P1-DFM-07 (two outlines within 0.15 mm of another part's opening) | Open (cosmetic) | Unchanged: C84's outline 0.076 mm from TP88.1, U5's arc 0.136 mm from C32.1; no silkscreen item overlaps any opening | Open, cosmetic; acceptable as recorded |
| R9P1-DFM-08 (J2 NPTH 0.39 / 0.41 mm from GND vias) | Open ("at the next ground-table change") | Unchanged: NPTH (3.366, 45.84) to GND via (4.4, 45.9) 0.391 mm (LED1's GND via, `r9_route_status.py` l. 45); NPTH (2.35, 40.76) to (3.4, 40.7) 0.407 mm (a ground-table "grid" row, `r9_ground.tsv` l. 40). The fix pass regenerated the table and kept the second via | Open; the trigger is stale: R9P2-DFM-03 (c) |

## 3. Findings

| ID | Sev. | Requirement | Finding | Evidence | Fix |
|---|---|---|---|---|---|
| R9P2-DFM-01 | Minor (worth fixing: order text) | REQUIREMENTS M1 ("every placement-file rotation verified against JLC's footprint"); F8 (terminals take their wires); ORDERING §4; R9P1-DFM-01's own fix | **J1 carries the same pin-1 mismatch as the mirrored terminals, but the order remark and expected DFM query added for R9P1-DFM-01 leave it out.** `jlc_orient`'s BODY rule adds +180° for C2915641 (DB128V), so JLC's pin 1 lands on our pin 4. Our square pad (J1.1, BAT_IN) and the `1:BAT+` legend are at the other end. ORDERING says so only in the orientation paragraph (l. 106, "a screw terminal does not care"); remark l. 103 and query l. 115 name J121 / J124 / J122 only. If a JLC engineer turns J1 180° to put JLC's mark on the square pad (the risk pass 1 inferred for J121 / J124, Inference), the wire entry faces aft. The entry face would sit at y ≈ 89.2, 0.64 mm from J124's courtyard (y ≤ 88.56): pin 4's entry (x 12.38) faces J124's body (x ≤ 15.79), pin 3's (x 17.46) partly, and pins 2 and 1 face into the PYRO_BLOCK area (x 1.2–28.4, y 54.2–89.8), so the battery leads, which come round the forward edge, could not be fitted. The owner's 3D-preview check (l. 108) is the only safeguard. The class is old (R4 W1) and is not a fix-pass regression | `tools/jlc_easyeda/pads.json` C2915641: pad 1 local (−7.62, 0) … pad 4 (+7.62, 0). `tools/jlc_corrections.json` `C2915641\|M3_DB128V_4P_Entry`: theta 180, body_correction_deg 180. CPL `J1,20.0000mm,-94.4000mm,Top,0`, so JLC pad 1 lands at (12.38, 94.4) = J1.4 (BAT_SW_RETURN). J1.1 (27.62, 94.4) is the square pad (pcbnew pad shape RECT). J1 courtyard y 88.91–100.09 (pin row 94.4; DORABO: entry face 5.20 mm, back face 5.00 mm). J124 courtyard x 4.61–15.79, y 78.44–88.56 | Extend ORDERING §4's order remark (l. 103) and expected query (l. 115) to J1: "J1 (C2915641): your pin 1 lands on our pin 4 by design (the body correction +180°). Place it exactly as the CPL rotation; do not turn it to match pin 1. Its wire entry faces the forward edge, Gerber Y −102 (silkscreen arrows)." No copper or tool change |
| R9P2-DFM-02 | Minor (worth fixing: an owner option for C21, generator table) | REQUIREMENTS M2 ("through-hole GND pins use thermal reliefs wherever their spokes are not starved"); R9_VALIDATION C21; ORDERING §4 hole-fill note | **J122's GND pins can be three-quarters relieved with no side effect; C21 offers the owner only all-or-nothing.** The fix pass relieved all four, found that J122.3's ring closes the F.Cu channel against D120's 3V3 lane (a 0.86 mm² single-spoke piece), and kept all four solid. Only J122.3 causes that. On a scratch copy I relieved J122.6, J122.9 and J122.12 (pad zone connection inherited, the zones' THT relief) and kept J122.3 solid, then refilled (native filler; the same refill of the unchanged board reproduces `4f841a0e…` byte for byte). `m3_design/r9_ground_check.py` passes every gate on it: table, DRC with parity at every severity, route, stitch, in2, xtal, islands (P7 9, no new pocket), reach (p95 3.37, max 7.32 mm, unchanged), copper, reference (R6b 0.1022, unchanged), pyro, contract, actuators. The whole `tools/check.sh` passes on it too (exit 0: DRC, unconnected, parity and ERC 0; check_r9 40 / 40, K-copper's thermal policy included; route_check 0 / 0 / 0; check_actuators). Each relieved pin keeps 4 spokes on F.Cu, 4 on In1 and 2 on B.Cu (0.5 mm spokes on F / B), about 0.2 A per spoke at 1.9 A per pin. With three of the four pins on reliefs, hole fill in JLC's hand or selective THT step is easier there (general practice, Inference). J122.3 stays the one listed solid exception, for the reason the fix pass measured. The servo GND return on this copper is 0.33 mΩ against 0.32 mΩ now (2.5 mV at 7.7 A; §8) | Scratch relief board (`relieve.py` pins 6, 9, 12) → `r9_ground_check.py <board> --report` exit 0, every gate OK, and `tools/check.sh <board>` exit 0 (§8). Spokes counted on the refill. `dc_solve.py` servo return 0.33 mΩ (current board 0.32). Control: the refill with no change gives SHA-256 `4f841a0e…`. The all-four variant fails only the islands gate (0.86 mm² F.Cu piece, P7 10), as D-F1-06 recorded (§8) | Owner option (c) for C21, alongside (a) solid and (b) all four relieved: restore the fix pass's reverted `RELIEVE` step in `r9_pcb.py` (pad-level FULL → inherited) for J122.6 / 9 / 12 only, keep J122.3 FULL (R8's instance setting, D-S2-03), rebuild from that stage on as the fix pass did, re-run the servo GND-return solve and the fab package, and narrow C21 to J122.3. Cheap and gate-checked. If the owner keeps all four solid, record this option in C21 |
| R9P2-DFM-03 | Minor (worth fixing: records) | AGENTS §3 (records match the board); REQUIREMENTS M2 (owner acceptance of a measured list); ORDERING is the order-day document | **Three record statements went stale with the fix pass.** (a) ORDERING l. 3: "R9 is not yet orderable: no independent review pass has run on it". Pass 1 has run (0 Critical, 1 Major confirmed as Minor) and pass 2 is due. The real blockers are r9_plan §5's two consecutive clean passes, the owner's acceptance and the commit. (b) ORDERING §7 Sled row (l. 211): "no bottom part within 3.5 mm of a hole centre: nearest 4.60 mm, R300.2 at (4, 4)". That was step 10's `fit_check` figure; on `4f841a0e…` `fit_check` gives "C98.1, 4.483 mm from support (42.0, 59.5)", and the next row of the same table (l. 212) gives C98.1 4.55 mm and R300.2 4.68 mm (pad distances). (c) R9_VALIDATION "Review pass 1", R9P1-DFM-08 (l. 325): Open "at the next ground-table change". The fix pass regenerated `r9_ground.tsv` (187 rows) and kept the via (3.4, 40.7) 0.407 mm from J2's NPTH. The other via, (4.4, 45.9), belongs to `r9_route_status.py` (LED1), not the table | ORDERING l. 3 and l. 211–212; my `tools/check.sh` run: `nearest bottom/pin envelope: C98.1, 4.483 mm from support (42.0, 59.5) (minimum 3.5 mm)`; R9_VALIDATION l. 325; `r9_ground.tsv` l. 40 (`via GND FB 0.5/0.3 3.4 40.7 grid`); `r9_route_status.py` l. 45 | (a) Reword ORDERING l. 3 as in STATUS: pass 1 run on `fc3d5b34…`, pass 2 due on `4f841a0e…`, not orderable until r9_plan §5, the owner's dated acceptance and the commit. (b) Sled row: "nearest 4.48 mm, C98.1 at (42, 59.5) (`fit_check`)". (c) Restate DFM-08's trigger as a next-revision item (move (3.4, 40.7) and LED1's (4.4, 45.9) ≥ 0.07 mm off J2's holes), or take it now in the table. A JLC query about it is unlikely (JLC lists no NPTH-to-via figure; R7 was accepted at 0.39 mm) |

## 4. The fix pass's changes, checked for manufacturing

**Vias** (`fc3d5b34…` → `4f841a0e…`, matched by position, net and size): 8 removed, 12 added, 579 → 583. All 583
are 0.5 / 0.3 (345) or 0.6 / 0.3 (238), ringed on F.Cu and B.Cu. Inner flashes: In1 430 + 26 THT = 456, In2 416 + 26
= 442, against 609 plated holes, as ORDERING §2 and `fab.txt` say.

| New or moved via | Net, size | Nearest opening, F side: ring / hole (mm) | B side: ring / hole (mm) |
|---|---|---|---|
| (28.07, 17.6), U31 module ground | GND 0.6 | U31.16: 0.300 / 0.450 | 5.806 / 5.956 |
| (31.88, 10.4), U31 module ground | GND 0.6 | U31.7: 0.300 / 0.450 | 5.895 / 6.045 |
| (34.35, 15.27), U31 module ground | GND 0.6 | U31.2: 0.160 / 0.310 | 9.651 / 9.801 |
| (24.65, 10.45), the strip grid via moved 0.05 mm west | GND 0.6 | U31.11: 0.318 / 0.468 | 7.234 / 7.384 |
| (31.5, 78.2), RAW_ACT (was (29.6, 78.2) and (31.0, 78.2), in TP120) | RAW_ACT 0.6 | TP120: 0.250 / 0.400 | Q121: 0.335 / 0.485 |
| (32.9, 99.85), copper stage, forward strip | GND 0.5 | C95: 0.950 / 1.050 | R167: 0.925 / 1.025 |
| (35.6, 64.8), copper stage, C121.2's corridor exception | GND 0.5 (no In2 flash) | C121: 1.320 / 1.420 | R87: 0.675 / 0.775 |
| (41.4, 41.1), copper stage | GND 0.5 | C77: 1.147 / 1.247 | L3: 0.261 / 0.361 |
| (38.55, 58.95), (38.45, 61.35), (38.45, 62.55), (39.7431, 62.5955): re-placed round C98 | GND 0.5 | ≥ 1.945 / 2.045 | C98: ≥ 0.882 / 0.982 (the nearer pre-existing GND via (38.5, 65.2): 0.275 / 0.375 to C98.2, same net); C92 1.700 |

- Six of the twelve have a ring within 0.35 mm of an opening, and one of them, (34.35, 15.27), also its hole (0.310 mm to
  U31.2, GND). JLC will not ink-plug such a via ("Filled vias should have ≥ 0.35 mm clearance from other soldermask
  openings"), and ORDERING §4's remark asks for it to be tented.
  - Four sit beside same-net pads: U31.2 / .7 / .16 (GND) and TP120 / Q121.6 (RAW_ACT).
  - Two sit beside another net's pad, with mask webs far above JLC's 0.10 mm: GND (24.65, 10.45) 0.318 mm from U31.11
    (RADIO_BUSY), and GND (41.4, 41.1) 0.261 mm from L3.1 (CAM_SW) on the bottom.
  - 132 vias in all have a hole within 0.35 mm of an opening (pass 1: 135 on `fc3d5b34…`).
- The three U31 module-ground vias sit under the module body (10 × 10 mm at (30.61, 14.0)), as on R7. They are tented
  GND next to GND pads, so a failed tent cannot short anything.
- Hole spacing at the new vias: (31.5, 78.2) to (32.2, 78.2) is 0.400 mm edge to edge, and (38.55, 58.95) to
  (38.45, 58.35) 0.308 mm. Both meet JLC's 0.2 mm, and the board minimum is still 0.250 mm.
- **TP120:** no via hole or ring in its opening; the nearest via ring is 0.250 mm away. M2's "no via in a test pad"
  now holds everywhere (no via hole within 0.1 mm of any opening).

**C98:** moved from (37.0, 62.8, 0, B) to (39.275, 64.2, 180, B), still on the bottom. The CPL row changed to
`C98,39.2750mm,-64.2000mm,Bottom,0`; the BOM did not. `--verify-cpl` rebuilds the row from JLC's footprint.
- Its openings keep ≥ 0.275 mm from every via ring: C98.2 (GND) to the GND via (38.5, 65.2) 0.275 mm, C98.1
  (USB_LIMITED) ≥ 0.88 mm.
- It is the nearest bottom item to a support: `fit_check` 4.483 mm from (42, 59.5), the minimum 3.5 mm.

**Silkscreen:** 461 items, as before.
- C98's designator moved; R87's appeared. U11's designator is now hidden; U11 keeps its board-level pin-1 dot.
- 139 designators shown and 110 hidden, exactly `post_report.json`'s list, as M3_R9 §"Silkscreen" records.
- No item overlaps a mask opening. The nearest foreign items are the two of R9P1-DFM-07.

**Zones:** RAW_ACT_F's edge moved (PLANES-01). The zone minimum widths are 0.15–0.3 mm. DRC reports no
`copper_sliver`, `isolated_copper` or `starved_thermal` at any severity.

**Fab package:** the CPL changed only in C98's row and the BOM not at all (`ab3d8171…`, R8's lines but the three
variant footprint fields). The manifest's 175 inputs include both untracked variant footprints. The assembly drawings
carry all 219 placed designators (83 top, 136 bottom; `pdftotext`).

## 5. Footprint variants and JLC placement

- **Library** (`FootprintLoad`, `M3_DB128L_2P_BK_SW` and `HDR-TH_12P-P2.54-V-M-R3-C4-S2.54_MIR` against their bases):
  - every variant pad n sits on base pad `PAD_ALIAS[n]` with the same size, drill, attribute and layers, and is the
    mirror of base pad n;
  - the graphics (12 and 11 items) are mirrored-equal;
  - the 3D model is the same file at offset 0, rotation 0;
  - the square pad is variant pad 1.
- **Board:** J121.1 (10.1, 70.73) PYRO1_OUT and J124.1 (10.1, 80.96) PYRO1_BUS are the square pads; J122.1
  (19.19, 59.46) is SERVO1_OUT. Nets per pad match the role table, and DRC reports 0 `lib_footprint_mismatch`.
- **Wire-entry arrows:** J121 and J124's arrows sit at x 6.63–7.57, west of the pin column (x 10.1), so the entries
  face x = 0. J1's sit at y 96.93–97.87, forward of the pin row (y 94.4).
- **jlc_orient:**
  - C430601 and C32713291: theta 0, offset 0, residual 0, next-best 3.592 / 6.476 mm;
  - C2915641 (J1): theta 180 through BODY, residual 0, next-best 10.776 mm (R9P2-DFM-01).
- **Not re-read:** EasyEDA's component API answered 403 to this session. The pad data used is the repository's
  `tools/jlc_easyeda/pads.json` (the tool's input). Pass 1's reading of C430601's marking layer stands.

## 6. Holes, mask, paste, silkscreen and edges (measured on `4f841a0e…`)

| Item | Board | JLC limit (capabilities page, read 2026-10-25) | Result |
|---|---|---|---|
| Via hole to hole, edge to edge | min 0.250 mm ((13.61, 21.65)–(13.6, 22.2)) | 0.2 | OK |
| NPTH to via hole | J2 0.391 / 0.407 mm; J3 0.638 mm | none listed; pad hole-to-hole 0.45 | R9P1-DFM-08 (open) |
| Via hole to foreign copper, outer / inner | 0.250 / 0.2505 | 0.2 / 0.2 | OK |
| PTH hole to foreign copper, outer / inner | 0.4005 (J122.10 to GND fill) / 0.4519 (J3.1 to In2 3V3) | 0.28 / 0.3 | OK |
| NPTH to copper | 0.2014 (J3 to J3.A1B12; HRO layout, expected query) | 0.2 | OK |
| Milled holes (Edge.Cuts circles) to copper | 0.498 mm on every layer | routed edge 0.2 | OK |
| Copper to the board edge | 0.2 (SMA pads, expected query); 0.5005 elsewhere | 0.2 | OK |
| Plated slots (J3 legs) | 0.6 × 1.4 / 1.7 mm | multilayer ≥ 0.35 | OK |
| Via hole to a pad opening | min 0.107 mm (R63.2) | M2 ≥ 0.1 | OK |
| Via ring to an opening: foreign / own net | 0.150 (U31.5 / U31.11) / 23 pairs at 20 vias under 0.10, worst 0.005 | web 0.10 | OK / C13 |
| Via ring to a stencil aperture | 18 pairs at 15 vias under 0.10, worst 0.005, no overlap | K-copper `via_paste` | OK / C13 |
| Pad-to-pad mask webs, different nets | U4 only, 0.100 mm (8 pairs; ORDERING remark) | 0.10 (1 oz, green) | at the limit, recorded |
| Paste area ratio, 0.12 / 0.10 mm stencil | U11 0.625 / 0.75, U7 0.694 / 0.833, D30 / D31 0.719 / 0.863, U9 0.725 / 0.870; all else ≥ 0.85 at 0.12 | IPC-7525 0.66 | as recorded (0.10 mm preferred) |
| Silkscreen | 174 texts ≥ 1.0 mm high, ≥ 0.15 mm stroke; lines ≥ 0.15; none off the board; none on an opening | 1.0 / 0.15 | OK (R9P1-DFM-07) |
| Order mark | strokes (Gerber) 0.366 mm from GND via (23.0, 77.45)'s ring, 0.958 mm from C150's opening | off pads and vias | OK, as ORDERING |
| THT zone connections | J122.2 / 3 / 5 / 6 / 8 / 9 / 11 / 12 and J1.1 solid; J1.2, J123.2, J3.1–4 relieved; J124.2 a 1.0 mm track | M2 (C21) | as ORDERING §4 |
| Edge distances (rail removal) | J2 NPTH 0.84, TP30 1.25, C32 1.33 (left); J9 tabs 0.50, TP88 0.55, east TP column 0.65, TP72 1.05, D9 1.15 (right) | — | as ORDERING §5 |

The gate's paste model (`check_r8.paste_polys`) against the exported stencil: every one of the 707 apertures matched.
Where they differ, the stencil extends at most 0.007 mm beyond the model (U4's and U9's square corners, against the
model's rounded inflation). The model is larger elsewhere (Q121.1–.4: 1.021 against 0.971 mm), so `via_paste`'s
0 mm ring clause is not blinded.

## 7. Panel, tabs and rails; procurement and cost

- **`tab_windows.py`** (read-only run on `4f841a0e…`):
  - west 0.5–7.25, 12.0–20.5, 53.5–101.5;
  - east 0.5–27.0, 92.75–101.5;
  - In2 GND under every window but west 53.5–101.5 (3V3 and GND), as T-1 and the record say.
- **The four tabs** (west 0.5–5.5 and 96.5–101.5, east 8.75–13.75 and 96.5–101.5):
  - zone fills, tracks, vias and pads in the 0–3 mm band are GND only on all four layers;
  - no pad lies within 5 mm of the edge along any tab span;
  - none of the fix pass's vias is near a tab: the nearest, (34.35, 15.27), is 8.78 mm from the east aft tab's
    0–3 mm band.
- **Tab count:** four tabs on 102 mm remains an Inference to confirm in Confirm Production File, as recorded.
- **Procurement:**
  - the recorded reports (stock 00:59:10Z, cost 01:00:11Z on 2026-10-26) are bound to the current BOM / CPL, and
    `check_procurement.py` full mode is OK; they lapse at 2026-10-27 ≈ 00:59Z;
  - my live run: 92 codes, 52 extended / 40 basic, $81.24 parts + 92 × $1.53 / 5 = $109.39 per board (cap $126.41),
    short none, thin none;
  - the tightest lines by stock against order: U30 34 / 5, U4 40 / 5, D30 / D31 208 / 10, U31 436 / 5;
  - M3 is met with no extended code to spare;
  - U4 needs no consignment today (ORDERING §1's order-day rule covers it).

## 8. J122 relief trial (R9P2-DFM-02)

Scratch copy of `m3_design/assembly_review/` (board, project, DRU, the 15 sheets, `fp-lib-table`, `sym-lib-table`,
`kilib`); `pcbnew` sets the pads' zone connection to inherited, then `ZONE_FILLER.Fill` and `Save`.

| Variant | Board SHA-256 | `r9_ground_check.py` | Spokes per relieved pin (F.Cu / In1 / B.Cu) |
|---|---|---|---|
| Control (no change, refilled) | `4f841a0e…` (identical to the repository's) | — | — |
| J122.6 / 9 / 12 relieved, J122.3 solid | `6523ea3d…` | **exit 0; every gate OK**: table, drc, route, stitch, in2, xtal, islands (P7 9), reach (p95 3.37, max 7.32 at (31.25, 91.25)), copper, reference (R6b 0.1022), pyro, contract, actuators. Also `kicad-cli pcb drc --severity-all --schematic-parity`: 0 violations, 0 unconnected, 0 parity; and `tools/check.sh` exit 0 (ERC 0, check_r9 40 / 40, route_check 0 / 0 / 0, check_actuators OK) | 4 / 4 / 2; J122.3 unchanged (solid) |
| All four relieved (the fix pass's trial) | `08c013b6…` | **exit 1: islands FAIL (1):** "F.Cu island [18.15, 62.61, 19.13, 64.31] (0.86 mm2) holds 0 GND via(s)" (P7 10); every other gate OK. This reproduces D-F1-06's measurement: J122.3's relief ring is the cause | 4 / 4 / 2 each |

Servo GND return on the three-pin variant (`tools/dc_solve.py --net GND --source J122:3,6,9,12 --sink J1:2 --grid 0.1
--window 0,50,46,102`, the window step 10 used; the output's first line binds board `6523ea3d…`):
- R = 0.33 mΩ against 0.32 mΩ on the current board (`step10_evidence/dc/gnd_servo.txt`): at 7.7 A, a 2.5 mV drop
  (2.4) and 0.019 W of copper loss (0.019).
- Layer shares at mid-path F.Cu 9, In1 40, In2 29, B.Cu 22 % (9 / 41 / 29 / 21 %).
- 152 GND vias carry current, the largest 0.29 A, none over 0.5 A (unchanged).
- The narrowest cut lies at J1.2's spokes (cut box x 21.4–23.7, y 93.3–95.5), which the change does not touch;
  `run_dc.sh` reports that neck and does not gate it.

## 9. Sources

- JLCPCB PCB capabilities, https://jlcpcb.com/capabilities/pcb-capabilities (read 2026-10-25). In the page's wording:
  - Via Hole-to-Hole Spacing 0.2 mm; Pad Hole-to-Hole Spacing 0.45 mm (PTH and NPTH not separated; no NPTH-to-via
    row);
  - NPTH to Track 0.2 mm; Via hole to Track 0.2 mm; PTH to Track 0.28 mm (0.35 recommended);
  - Inner layer via hole to copper 0.2 mm; inner layer PTH pad hole to copper 0.3 mm;
  - Soldermask bridge 0.10 mm (1 oz, green and four other colours);
  - Pad To Silkscreen 0.15 mm; text ≥ 1.0 mm, line ≥ 0.15 mm;
  - filled vias: no openings on either side, ≥ 0.35 mm from other openings, ≤ 0.5 mm diameter;
  - thickness tolerance ± 10 % (≥ 1.0 mm); routed copper-to-edge ≥ 0.2 mm; non-plated holes ≥ 0.50 mm;
    multilayer plated slots ≥ 0.35 mm; PTH annular ring ≥ 0.20 mm.
- JLC public component search through `tools/jlc_stock.py` and `tools/jlc_cost.py` (live, 2026-10-26 01:29–01:30Z).
- `tools/jlc_easyeda/pads.json` (EasyEDA pad records for C2915641, C430601, C32713291); `tools/jlc_corrections.json`;
  `tools/jlc_orient.py` (BODY, PAD_ALIAS).
- IPC-7525 stencil area ratio ≥ 0.66 (general practice).
- Project records: REQUIREMENTS M1 (l. 74), M2 (l. 75), "Accepted risks" (l. 100); ORDERING l. 3, §1–§5 (l. 29–33,
  57–63, 80–120), §7 (l. 211–212); R9_VALIDATION C13, C19, C21 and "Review pass 1" (l. 318–325); M3_R9
  §"Silkscreen", §"R9 manufacturing outputs"; `fix1_handoff.md`; `step10_evidence/fab.txt`, `post_report.json`,
  `requalify_r9.json` `mech.mark`; `m3_design/r9_power.py` l. 535–540, `r9_route_status.py` l. 45, `r9_ground.tsv`
  l. 40.

## 10. Inferences

- That a JLC engineer may turn a terminal to put JLC's pin-1 mark on the board's square pad (R9P2-DFM-01; as pass 1's
  R9P1-DFM-01).
- That relieving a through-hole GND pin eases hole fill in hand or selective soldering, and the per-spoke current
  (R9P2-DFM-02).
- That JLC will not query J2's NPTH-to-via spacing (R9P2-DFM-03 (c)).
- JLC's acceptance of four tabs; JLC's treatment of the 132 vias that cannot be ink-plugged (the order remark asks for
  tenting).

## 11. Method (reproducible, read-only)

**Scripts** (session scratchpad `r9review/dfm2/`, deleted at the end). KiCad 10.0.6 Python, `pcbnew.LoadBoard`; no
repository board saved.
- `export_geom.py`: pads per copper layer (flash-aware), holes, vias with per-layer flashing, tracks, zone fills,
  silkscreen and courtyard polygons and the outline, to JSON (`fc3d5b34…` from the fix pass's backup archive, and
  `4f841a0e…`).
- `gerb.py`: a Gerber parser (C / R / O / P apertures, the RoundRect and FreePoly macros, draws, arcs, regions,
  polarity, `%TO.C`).
- Analyses (shapely 2.0.7 in a scratch venv):
  - `viadiff.py`: vias added, removed or reflashed;
  - `dfm_mask.py`: via against mask and paste, mask webs;
  - `holes.py`: hole spacing, hole-to-copper per layer, edge and milled-hole clearances;
  - `silk.py`: sizes and openings;
  - `thtzc.py`: THT zone connections;
  - the tab-band and edge scans;
  - `pastepolys.py`: the gate's paste model against the stencil;
  - `pin1.py`, `refs.py`: pin-1 marks, shown and hidden designators;
  - `variants.py`: library and instances.
- `relieve.py`: the J122 relief variants (§8).

**Tool runs:**
- `NUMPY_PY=<cfd venv> tools/check.sh` (exit 0);
- `tools/export_fab.py --out <scratch>` and the BOM, CPL and Gerber diffs;
- `tools/jlc_orient.py … --out <scratch>`, and `--verify-cpl` on `fab/`;
- `tools/paste_check.py`; `tools/fab_manifest.py` (both folders); `tools/check_procurement.py` (both modes);
- `tools/jlc_stock.py` / `tools/jlc_cost.py --fab <scratch>` (live);
- `tools/tab_windows.py --json <scratch>`;
- `m3_design/r9_ground_check.py` on the two relief variants; `tools/dc_solve.py` (servo GND return);
- the six DFM suites (KiCad Python, `-B -m unittest`);
- `pdftotext -layout` on both assembly drawings.
