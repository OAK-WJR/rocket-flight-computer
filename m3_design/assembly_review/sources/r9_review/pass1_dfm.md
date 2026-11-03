# R9 review pass 1: manufacturability and fab package (independent review)

Read-only review, 2026-10-25, of the R9 board as built by steps 1–10. Worktree `rocket-flight-computer-r9`, branch
`m3-assy-r9`, uncommitted, on top of R8 `9c8179b`.

- **Board:** `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
  `fc3d5b34a4bfbaecfbcb44bdf8144c87015fc71be7accf48354f23410e8d0f51`, hashed before the first run and after the last;
  unchanged. `git status --short` was identical before and after every run (md5 `e0986e38…`). No repository file was
  written except this report; every regeneration went to a scratch folder, since deleted.
- **Coordinates:** KiCad mm, y = 0 at the aft (SMA) edge; Gerber Y = −y.
- **Inference** marks anything not measured and not taken from a maker or JLC document (AGENTS §2.5).
- **Previous pass in this dimension:** none on R9. R8's DFM findings (passes 1–4) are the predecessor; their classes
  are re-checked on R9 in §2.

## 1. Summary

**Critical 0, Major 0, Minor 8 (5 worth fixing, all records or order text; 3 not worth fixing).**

The fab package is complete, reproducible and bound to `fc3d5b34…`:
- `tools/check.sh` exits 0 (DRC 0 at every severity, unconnected 0, parity 0, ERC 0; audit, silk, fit, plate, rule-H
  suite, check_r9 40/40, route_check r9 0/0/0, check_actuators).
- `export_fab.py --out <scratch>` gives a BOM (`ab3d8171…`) and CPL (`eee180fb…`) byte-identical to `fab/`. All 14
  Gerber, drill and job files equal `fab/m3_gerber.zip` once the creation-date line is removed. The PDFs differ only in
  their dates.
- `jlc_orient.py --out <scratch>` regenerates `tools/jlc_corrections.json` byte for byte (CHECK none).
- `--verify-cpl`, `paste_check`, `fab_manifest` and `check_procurement.py` (both modes) are OK.
- A live JLC run (2026-10-25 19:44–19:45Z, scratch `--fab` copy) reproduces the recorded figures exactly: $109.38 per
  board, 52 of 52 extended codes, short none, thin none; U4 40 and U30 34 in JLC stock.
- The six DFM test suites pass (100 tests).

The mirrored footprint variants are exact: same land, numbering mirrored, graphics mirrored-equal, same 3D model. The
instances equal their library variants, and PAD_ALIAS gives theta 0, offset 0, residual 0. EasyEDA's own footprint
for C430601 confirms that, at the CPL rotation, JLC's body puts the wire entry toward x = 0 (§4).

Hole, mask, paste, silkscreen and edge geometry meet every JLC limit I could cite (§5), with two exceptions:
- the own-net via-to-pad class R8 accepted, now worse and unrecorded;
- J2's NPTH-to-via spacing, where it is unclear whether JLC's rule applies.

Tab windows and the four-tab plan reproduce, with GND only under every tab on all four layers.

The five worth-fixing items:
1. **R9P1-DFM-01:** the mirrored variants put the board's pin-1 square pad under JLC's pin 2 (J121/J124) or pin 10
   (J122). No order remark or expected DFM query tells JLC to keep the CPL rotation, and a JLC "pin-1 correction" of
   J121/J124 would turn both wire entries into the board.
2. **R9P1-DFM-02:** five bare actuator-gate-network pads sit at the 0.150 mm default from the GND pour, and a bridge
   there fails the actuator switch on. R8 recorded this class (C12b #18). R9 does not, and REQUIREMENTS calls the
   gate-net-spacing risk "retired for R9", which holds only for the pyro gate nets.
3. **R9P1-DFM-03:** J122's four GND pins are solid on three or four layers. M2's relief-exception list has no R9 entry
   (R8 had C17), and R8's starvation basis no longer holds: with reliefs, R9 resolves at least 2 spokes on every layer.
4. **R9P1-DFM-04:** the own-net via-ring-to-pad class (R8P3-DFM-02) is worse on R9 and unrecorded: 21 openings at 18
   vias have a mask web under JLC's 0.10 mm, the worst 0.005 mm (R8: worst 0.025 mm).
5. **R9P1-DFM-05:** REQUIREMENTS M1 still says U4 is out of JLC stock and must be consigned. The R9 acceptance clause,
   ORDERING §1 and today's stock (40) say "in JLC stock or consigned".

## 2. R8's DFM findings: their classes on R9

| R8 ID | R8 disposition | Measured on `fc3d5b34…` | R9 status |
|---|---|---|---|
| R8P1-DFM-01 (paste over limiter vias; via ring on C7.1's paste) | Fixed; `via_paste` gate (D87) | No via ring touches a paste aperture (nearest 0.005 mm); check_r9 K-copper runs `via_paste` | **Closed** (the sub-0.1 mm class: R9P1-DFM-04) |
| R8P1-DFM-02 (tab on the 7.7 A band) | Fixed (D93) | All four tabs GND-only on F / In1 / In2 / B in the 0–3 mm band (`tabcu` scan, §6) | **Closed** |
| R8P1-DFM-03 (solid THT GND pins) | J3 / J123.2 relieved; J122 recorded C17 | J3.1–4, J1.2, J123.2 THT_THERMAL (J123.2 4 spokes per layer); J122.3/6/9/12 FULL | **Class persists, unrecorded:** R9P1-DFM-03 |
| R8P1-DFM-04 (doc details) | Fixed | ORDERING §7 "C84 … the tallest part at the bore wall; J1 … near the axis"; U4 "west of U1" (U4 (12.0, 47.4), U1 (18.0, 44.5)) | **Closed** |
| R8P2-DFM-01 (J123.2 starved thermal) | Fixed (D101) | J123.2 relieved, 4 spokes on all four layers; DRC `starved_thermal` (error) 0 | **Closed** |
| R8P2-DFM-02 (J1 1:BAT+ legend aft) | Accepted | `1:BAT+` now in front of the entry (24.65–29.66, 100.18–101.33); but `2:GND` / `3:SW` moved to the bottom | **Closed**; new cosmetic split R9P1-DFM-06 |
| R8P2-DFM-03 (tab table; C83 in J3 steps) | Fixed | ORDERING §3 gives J30 10.05 / J31 10.94 mm from the aft tabs; §4 / §5 name C83 and R8 | **Closed** |
| R8P3-DFM-01 (bare ACT_GATE pads 0.150 mm from the GND pour; via-only candidate) | Fixed (records) in C12b #18 / #23; pour rule offered to the owner | C120.2, Q121.4, R121.1 (ACT_GATE), R121.2, Q122.3 (ACT_DRV) 0.1505 mm from GND_B; R120.2 0.933 mm (improved); J1.4 0.149, J123.1 0.150 mm | **Class persists, unrecorded, and REQUIREMENTS calls it retired:** R9P1-DFM-02 |
| R8P3-DFM-02 (own-net via rings < 0.1 mm from paste) | Accepted, recorded (12 at 11, worst 0.025 mm) | 18 ring-to-paste pairs at 15 vias, 21 openings at 18 vias under 0.10 mm web, worst 0.005 mm | **Class worse, unrecorded:** R9P1-DFM-04 |
| R8P3-DFM-03 (Q123's dot on R162.2's opening) | Accepted (C20) | No silkscreen item overlaps any mask opening (all 461 items; text by its box, conservative) | **Closed**; nearest foreign gaps R9P1-DFM-07 |
| R8P4-DFM-01 / 02 (R8 records; R70 designator) | Fixed (records) | R8-specific; R9's silkscreen is built by `r9_post.py`, two builds byte-identical | **N/A** |

R9_VALIDATION C18 (TP120's two RAW_ACT vias in a bare contact) is **properly dispositioned**. My measurements:
- Pad x 29.45–30.95, y 77.65–79.15. The (29.6, 78.2) hole lies inside the pad; the (31.0, 78.2) hole, x 30.85–31.15,
  crosses its east edge.
- The 7.7 A via grid (1.2–1.8 mm pitch on rows y 76.8 / 78.2) leaves no via-free 1.5 mm square inside the RAW_ACT
  pour.
- There is no paste and no part, and ORDERING §3 and §4 name both vias.

From a DFM view, open unplugged vias in a probe pad are harmless unless someone solders a wire there.

## 3. Findings

| ID | Sev. | Requirement | Finding | Evidence | Fix |
|---|---|---|---|---|---|
| R9P1-DFM-01 | Minor (worth fixing: order text) | REQUIREMENTS M1 (placement verified against JLC's footprint), F8 (terminal entry); ORDERING §4 | **The mirrored-numbering variants put the board's pin-1 indicator where JLC's footprint has another pin, and nothing tells JLC to keep the CPL rotation.** The CPL is right: `jlc_orient` matches through PAD_ALIAS, theta 0, residual 0. But JLC's engineers compare their pin-1 marker with the board's. On J121 and J124 the square pad (our pin 1: OUT / BUS1, aft) sits under JLC's pin 2. JLC's component-marking dot for C430601 lands by our pin 2, on the body's back (east) side. A "polarity correction" (180°) to put JLC's pin 1 on the square pad would also turn the body: both wire entries would face +x, into the CH1 column. J122's square pad sits under JLC's pin 10. The header is a symmetric, unkeyed 3 × 4 array, so a turn is harmless there, but it can still raise a query. R8 had no such mismatch: its base footprints put the square pad on JLC's pin 1. ORDERING §4 asks for the wire entry to be checked in the 3D preview, which is the only safeguard. The order remarks (l. 89–102) and the expected DFM queries (l. 113–119) do not mention it | Board: J121.1 (10.1, 70.73) square, PYRO1_OUT; J121.2 (10.1, 75.81) round; J124.1 (10.1, 80.96) square, PYRO1_BUS; J124.2 (10.1, 86.04) round; CPL rows J121 / J124 (10.1, −73.27 / −83.5, Top, 90). EasyEDA C430601 (`https://easyeda.com/api/products/C430601/components`, read 2026-10-25): pad 1 local (−2.54, 0) and pad 2 (+2.54, 0), both round. Layer-101 circle (component marking, Inference from EasyEDA's layer table) at (−5.08, +5.10). Body (layer 99) x ±5.08, y −5.0…+5.1. Document-layer clamp outlines and arrows at y −2.7…−4.8 (entry −y), 3D model rotation 0,0,0. With `jlc_orient`'s rotation (r 90: (x, y) → (y, −x)), JLC pad 1 lands on J121.2 / J124.2 and the dot at (15.2, 78.35) / (15.2, 88.58). C32713291 pin 1 (−3.81, +2.54) lands on J122.10 (26.81, 59.46); our square pad is J122.1 (19.19, 59.46). `tools/jlc_corrections.json` C430601 / C32713291: theta 0, offset 0, residual 0 | ORDERING §4: add an order remark and an expected DFM query: "J121 / J124 (C430601) and J122 (C32713291) use mirrored pad numbering on the maker's land. The square pad (our pin 1) is your pin 2 (pin 10 on J122) by design. Place exactly as the CPL rotation; do not turn these parts to match pin 1. J121 / J124 wire entries face the left edge, X = 0 (silkscreen arrows)." Optionally put the same sentence in the parts' `JLC_Assembly` field, which `export_fab.py` copies to the BOM Assembly column. No copper |
| R9P1-DFM-02 | Minor (worth fixing: records; DRU rule optional) | REQUIREMENTS "Accepted risks" (gate-net spacing), M2 (deviation list); AGENTS §2.5; R8P3-DFM-01 / C12b #18 | **Five bare pads of the actuator switch's gate network sit at the board's 0.15 mm default from the GND pour; R9's records drop the class and call the risk retired.** A GND bridge on ACT_GATE or ACT_DRV turns the P-FET pair Q120 / Q121 on with the power switch open: RAW_ACT goes live (R8 C12b #18's consequence). R8 recorded these pads in C12b #18 as "REQUIREMENTS' accepted gate-net spacing outside the pyro block" and offered a GND-to-gate zone rule as an owner option. On R9: R120.2 improved to 0.933 mm, and the strict pad rule AG (≥ 1.2 mm) covers only pad-to-pad pairs. REQUIREMENTS "Accepted risks" says the gate-net risk is "retired for R9, whose rule G covers every gate-net item outside U1's courtyard at 0.3 mm". Rule G names only PYRO1_GATE / PYRO1_GATE_N and excludes GND, so it does not reach these pads. The bridge still needs a mask breach (mask web 0.15 mm ≥ JLC's 0.10 mm; Inference as R8's). ORDERING §5's switch-off and "RAW_ACT dead with the switch open" steps screen it on the bench. BAT_ENABLE, BAT_SW_RETURN, PULLPIN_EXT and the pyro gate pads at 0.148–0.150 mm all fail safe (off / no fire) | Zone-fill distances (pcbnew fills; shapely): C120.2 (27.6, 84.8), Q121.4 (30.83, 85.1), R121.1 (37.35, 87.98) ACT_GATE; R121.2 (37.35, 87.12), Q122.3 (37.35, 85.5) ACT_DRV: 0.1505 mm to R9_GND_B. R120.2 0.9325, Q120.4 1.4355, TP121.1 1.0005 mm. `m3.kicad_dru` l. 83 / 112 (rule G condition). REQUIREMENTS "Accepted risks", gate-net bullet. `m2_sweep.txt` adjacency_pad lists tracks and vias only, not pours | Records: in REQUIREMENTS "Accepted risks", retire the bullet for the pyro gate nets only. Keep the actuator gate nets (ACT_GATE / ACT_DRV pads to the GND pour at 0.15 mm, five bare B.Cu pads, fail-on) as accepted, or name them as an owner item. Add the row to R9_VALIDATION C (as C12b #18 did). Owner option, as in R8: a DRU zone rule keeping ACT_GATE / ACT_DRV pads ≥ 0.3 mm from GND zones. It is cheap, but the fill changes, so the fill-dependent gates must be re-run |
| R9P1-DFM-03 | Minor (worth fixing: records, or relieve) | REQUIREMENTS M2 ("through-hole GND pins use thermal reliefs wherever their spokes are not starved; exceptions listed …") | **J122's four GND pins are solid, and R9 lists no exception.** J122.3 / 6 / 9 / 12 carry ZONE_CONNECTION_FULL: solid on F.Cu, In1 and B.Cu, and J122.3 also on In2. M2's pointer names only M3_R4 §2 and R8_VALIDATION C17. R9_VALIDATION has no relief-exception row, and ORDERING §4 mentions the solid pins only for the hole-fill check. R8 C17's basis was the 7.7 A return, J122.3 starved on F.Cu, and the rigid `j122_tie` digest. On R9 only the current reason remains: the pins are not rigid, and with reliefs they do not starve. Solid connections to three or four planes make hole fill harder in JLC's hand or selective THT step (DFM view; ORDERING already asks for preheat) | `tht_zc.py`: J122 GND pads pad_zc FULL; J1.2, J123.2, J3.1–4 THT_THERMAL / THERMAL. Scratch copy of the project: J122's GND pads set to inherited, zones refilled with `ZONE_FILLER`, `kicad-cli pcb drc` → **0 violations, no `starved_thermal`** (error severity, `min_resolved_spokes` 2). Spokes counted on the refill: F.Cu 4, In1 4, B.Cu 2 on each pin, and J122.3 In2 2. R8_VALIDATION l. 494 (C17) | Owner choice, either: (a) list R9's exception as a deviation row (J122.3 / 6 / 9 / 12 solid for the 7.7 A return; reliefs would not starve on R9) and add "R9: R9_VALIDATION C…" to M2's pointer; or (b) relieve the four pins (set them inherited in the R9 build), then re-run the servo GND-return solve and the gate. Either is cheap; (a) has no copper change |
| R9P1-DFM-04 | Minor (worth fixing: records; via moves optional) | REQUIREMENTS M2 (paste per maker / IPC-7525; within JLC's limits); R8P3-DFM-02 | **Own-net via rings sit closer to pad openings than JLC's 0.10 mm soldermask bridge on 21 openings at 18 vias, the worst 0.005 mm. R8 recorded the class (12 pairs at 11 vias, worst 0.025 mm); R9 does not.** Every pair is own-net (no short possible). Every hole keeps ≥ 0.107 mm from the opening, so M2's hole rule holds. With 0 mm mask expansion the web equals the gap, so JLC cannot hold it. These vias are within 0.35 mm of openings, so JLC will not ink-plug them (JLC rule). The likely effect is a sliver of exposed ring beside the pad and a smaller fillet. If the opening reached an open hole, a 0.3 mm barrel (≈ 0.11 mm³) could take most of an 0805 pad's paste (Inference). Three are at 0.005–0.014 mm: the shared GND via between the 3V3 buck's output caps C8 / C9, R63's GND via, and D4's VBUS via. Step 7's handoff noted the 0.005 mm figure, but no record carries it to the owner | `dfm.py` (paste / mask Gerbers parsed; vias from pcbnew); pcbnew pad copper confirms: GND via (42.0, 81.26) Ø0.6 → C8.2 and C9.2 0.005 mm (hole 0.155); GND via (16.82, 55.3) Ø0.5 → R63.2 0.007 (hole 0.107); VBUS via (11.95, 34.1) → D4.5 0.014 (hole 0.164); then C6.2 0.043, D9.2 0.050, R89.1 0.050, Q121.1/2/3 0.061 (ACT_FET_S, the 7.7 A source pins), R71.2 / R72.1 0.071, C10.2 / C11.2 0.075, C13.1 0.080, C99.2 0.080, R13.1 0.087, C18.2 0.087, C76.2 0.090, R303.1 0.095, C31.2 0.097. Ring-to-paste < 0.1 mm: 18 pairs at 15 vias. Foreign via-ring-to-opening minimum 0.150 mm. R8_VALIDATION l. 292; `r9_step7_handoff.md` l. 53 | Records: add the class to R9_VALIDATION C13 (counts, worst three, own-net, tented, effect). Optional, at the next copper change: move the three vias under 0.02 mm ((42.0, 81.26), (16.82, 55.3), (11.95, 34.1)) at least 0.1 mm off their pads, and ratchet `via_paste`'s ring clause so no new pair under 0.1 mm appears |
| R9P1-DFM-05 | Minor (worth fixing: records) | REQUIREMENTS M1 vs "R9 acceptance"; ORDERING §1 | **M1 still says U4 is out of JLC stock and must be bought and consigned, contradicting the R9 acceptance clause and ORDERING.** M1 (l. 74): "Every part in stock for 5 boards, except U4 …: out of JLC stock, it is bought from a franchised distributor and consigned into JLC's parts inventory before ordering". R9 acceptance (l. 126): "M1 stock is met, U4 in JLC stock or consigned". ORDERING §1 (l. 32): consign only "if the order-day run shows it short or thin". Live today: U4 40 in JLC stock, short none, thin none; `check_procurement.py` (full gate) OK | My live run (scratch `--fab`, 2026-10-25 19:44:38Z): U4 C26633007 `jlc_stock` 40, min purchase 1; 52 extended / 40 basic; $109.38 | Reword M1's U4 clause: "U4 has been out of JLC stock; if the order-day stock run shows it short or thin, buy and consign it (ORDERING §1)". The acceptance clauses then read consistently |
| R9P1-DFM-06 | Minor (not worth fixing) | REQUIREMENTS F8 ("unambiguous pin legends"), AGENTS §3 silkscreen | **Half of J1's pin legends are on the bottom face.** `1:BAT+` and `4:SW` are in the top forward strip, in front of the entry. `2:GND` and `3:SW` are on the bottom, aft of the pins, because three GND stitching vias occupy the top strip between them. With the board on its sled, the bottom face is hidden, so from the top only pins 1 and 4 are labelled. F8 is still met in substance: BAT+ is labelled, GND is its neighbour, and a reversed 2S is within U9's protection (R4). R8 had all four on the top | Top: `1:BAT+` box 24.65–29.66 × 100.18–101.33, `4:SW` 10.89–14.23 × 100.23–101.43. Bottom: `2:GND` 19.92–21.07 × 90.13–94.42, `3:SW` 15.74–16.89 × 89.51–92.89. GND vias (17.525, 101.1), (22.525, 101.1), (23.95, 101.05). J1 pins y 94.4, x 27.62 / 22.54 / 17.46 / 12.38 | None now. At the next forward-edge ground change, free x ≈ 15.5–24.0 of the top strip (e.g. drop or shift those three vias) so `r9_post.py` can place `3:SW` and `2:GND` on the top |
| R9P1-DFM-07 | Minor (not worth fixing) | REQUIREMENTS M2 (silkscreen never on pads); JLC pad-to-silkscreen 0.15 mm | **Two footprint outlines come within JLC's 0.15 mm pad-to-silkscreen distance of another part's opening** (no overlap anywhere, so R8P3-DFM-03's class is closed). C84's outline is 0.076 mm from TP88.1's opening (top); TP88 was moved by D-S9-01. U5's arc is 0.136 mm from C32.1's (bottom). JLC's CAM trims the ink; cosmetic. A further 69 footprint-graphic items sit within 0.15 mm of their own pads (library outlines); no text does | `silk.py`: 461 silkscreen items against the mask Gerbers' openings. Intersection area 0 for every item; all texts ≥ 1.0 mm height, ≥ 0.15 mm stroke; all graphics ≥ 0.15 mm | None (the project's DRC `min_silk_clearance` is 0.0; raising it to 0.15 for footprint graphics would surface these in the build) |
| R9P1-DFM-08 | Minor (not worth fixing) | JLC capabilities (Pad hole-to-hole 0.45 mm; Via hole-to-hole 0.2 mm) | **Two of J2's NPTH locating holes sit 0.390 and 0.406 mm (edge to edge) from GND vias.** That is below JLC's "Pad hole-to-hole 0.45 mm" if JLC applies it to NPTH-to-via pairs. JLC lists no NPTH-to-via figure; via-to-via is 0.2 mm (Inference: which rule applies). R8's minimum was 0.732 mm. R7 was accepted with 0.39 mm (TH3 to a GND via). Every other hole pair meets JLC's figures, and every hole-to-copper clearance meets JLC's outer and inner limits (§5) | `npth.py` (pcbnew): NPTH (3.366, 45.84) Ø0.991 ↔ GND via (4.4, 45.9) 0.390 mm; NPTH (2.35, 40.76) ↔ GND via (3.4, 40.7) 0.406 mm. R8 board (read-only): J2 ↔ GND via (0.8, 44.02) 0.732 mm. R7: TH3 ↔ (0.775, 112.925) 0.390 mm | None alone. At the next ground-table change, move both vias ≥ 0.07 mm away from J2's holes |

## 4. Footprint variants and JLC placement (R9-specific)

- **Library:** `M3_DB128L_2P_BK_SW` and `HDR-TH_12P-P2.54-V-M-R3-C4-S2.54_MIR` against their bases (`variants.py`,
  `FootprintLoad`):
  - every variant pad n sits on the base pad `PAD_ALIAS[n]` with the same size, drill, layers and attribute, and is
    the mirror of base pad n;
  - the 12 graphics each are mirrored-equal;
  - the 3D model is the same file at offset 0 and rotation 0 (the bodies are symmetric in x);
  - the square pad moves with pin 1.
- **Board instances:** DRC reports 0 `lib_footprint_mismatch`, so each instance equals its library variant.
  - Nets per pad match the role table (J124.1 BUS / J124.2 RAW, J121.1 OUT / J121.2 IGN, J122 1 / 4 / 7 / 10 signals,
    2 / 5 / 8 / 11 RAW_ACT, 3 / 6 / 9 / 12 GND).
  - J122's GND pads keep the instance-level FULL connection (D-S2-03).
- **CPL:**
  - J121 and J124 are at rotation 90, J122 at 180; theta 0, offset 0, residual 0 through PAD_ALIAS.
  - `jlc_corrections.json` differs from R8's only in the two key names.
  - `test_r9_sch` checks the alias table against the library files (21 tests OK).
- **Body side (closing the 180° question R4 W1 answered for the base):** EasyEDA's C430601 footprint puts the wire
  clamp and its arrows on local −y, with the 3D model at rotation 0. Our base and variant also put the entry on local
  −y.
  - At CPL rotation 90, JLC's body therefore faces x = 0, as ORDERING §4 asks the owner to confirm.
  - DB128V (C2915641) carries its marks on +y with the model at 0,0,180, which is why `jlc_orient` adds +180 for J1
    only.
- **Residual risk:** JLC's own pin-1 check (R9P1-DFM-01).

## 5. Holes, mask, paste, vias and silkscreen (measured)

Geometry: pcbnew export (pads, vias, tracks, zone fills) plus a Gerber parser for the mask, paste and silkscreen
layers, analysed with shapely (§10). JLC limits are from its capabilities page (§8).

| Item | Board | JLC limit | Result |
|---|---|---|---|
| Via hole-to-hole (edge) | min 0.250 mm (GND (13.61, 21.65)–(13.6, 22.2)) | 0.2 | OK |
| PTH / NPTH to via hole | THT min 0.565 (J122.1–GND (20.45, 59.35)); NPTH 0.390 (J2) | 0.45 (pad holes) | R9P1-DFM-08 |
| Via hole to foreign copper, outer / inner | 0.250 / 0.2505 | 0.2 / 0.2 | OK |
| THT hole to foreign copper, outer / inner | 0.4005 (J122.1/4/10 to GND) / 0.4505 (J3 legs to In2 3V3) | 0.28 / 0.3 | OK |
| NPTH to copper | 0.2001 (J3, HRO layout, ORDERING expected query); J2 0.2505 | 0.2 | OK |
| THT annular ring | ≥ 0.25 (J122 1.6 / 1.1) | 0.15 (rec. 0.20) | OK |
| Vias | 343 × 0.5 / 0.3, 236 × 0.6 / 0.3; every via ringed on F.Cu and B.Cu; In1 / In2 425 / 413 via flashes (+ 26 THT = 451 / 439, as ORDERING) | 0.25 / 0.15 | OK |
| Via hole in a pad opening | only TP120's two (C18) | M2 exception | Dispositioned |
| Via hole to pad opening | min 0.107 mm (R63.2) | M2 ≥ 0.1 | OK |
| Foreign via ring to opening | min 0.150 mm (GND vias at U30 / U31 / LS120 pads) | web ≥ 0.10 | OK |
| Own-net via ring to opening | 21 under 0.10, worst 0.005 | web ≥ 0.10 | R9P1-DFM-04 |
| Vias with hole within 0.35 mm of an opening (not ink-pluggable) | 135 (R8: 93) | JLC plug rule | ORDERING §4 asks JLC to tent them |
| Pad-to-pad mask webs, different nets | only U4's 0.100 mm (8 pairs, documented) | 0.10 | OK |
| Paste area ratio, t = 0.12 / 0.10 mm | U11 0.625 / 0.75 (ORDERING prefers 0.10 mm), U7 0.694 / 0.83, D30 0.719 / 0.86, U9 0.725 / 0.87, the rest ≥ 0.85 | IPC-7525 0.66 | as recorded |
| Paste flashes | F 335 / B 372 on as many pads; 20 dry (J30 / J31, 5 DNP lands); J3 pin-in-paste only | — | OK |
| Silkscreen text / lines | all 174 texts ≥ 1.0 mm, ≥ 0.15 mm stroke; graphics ≥ 0.15 mm; no ink on any opening | 1.0 / 0.15 | OK (R9P1-DFM-07) |
| Courtyards | every pad inside its own courtyard; no overlaps (DRC) | M2 | OK |
| Bottom courtyards to THT rings (M-6) | TP70 1.505 (J123.1), C83 1.539, D121 1.605, R177 1.652 (J122.10, not in ORDERING's list), D8 1.655 | 1.5 | OK |
| Order mark | over no via; 0.27 mm from GND via (23.0, 77.45) by the text's box (ORDERING's 0.365 is to the strokes); 0.80 mm to C150.1's opening | JLC: off pads / vias | OK |

- **THT zone connections:**
  - solid: J122.2/5/8/11 (RAW_ACT; B.Cu, In2), J122.3/6/9/12 (GND), J1.1 (BAT_IN; F, B, In2);
  - J124.2 is fed by a 1.0 mm track;
  - relieved: J1.2, J123.2, J3.1–4.

  This matches ORDERING §4's hole-fill list.
- **Small GND pads:** they carry thermal reliefs (check_r7 `thermal_policy` in K-copper), so the decoupling caps'
  tombstoning exposure stays the R8 baseline.
- **Second-reflow drop:** no heavy bottom part. L1 SWPA4030 4 × 4 × 3 mm, the 1210 caps and the PDFN Q120 / Q121
  all have large wetted pads (Inference by mass per pad area).

## 6. Panel, tabs and rails

- **`tab_windows.py` (read-only run):**
  - west 0.5–7.25, 12.0–20.5, 53.5–101.5;
  - east 0.5–27.0, 92.75–101.5;
  - In2 under the windows GND (west 53.5–101.5: 3V3 and GND).

  These equal the record and gate T-1.
- **The four chosen tabs** (west 0.5–5.5 and 96.5–101.5, east 8.75–13.75 and 96.5–101.5): GND only on all four layers
  in the 0–3 mm band (zone fills, tracks, vias and pads scanned). Distances equal `tab_plan.json`: TP30 3.20, U30
  5.57, C310 7.32, R83 3.31 / C87 6.11, hole edges 2.40 mm.
- **J3's 0.45 mm overhang** fits JLC's 1.6 / 2.0 mm routed gap. Mouse-bite tabs at JLC's 5 mm minimum.
- **Four tabs on 102 mm** remain the recorded Inference ("4–6 over 100 mm"), to confirm in Confirm Production File.
- **No change needed.**

## 7. Procurement and cost (M1, M3)

- **Recorded reports:** `cost_check.json` and `stock_check.json` (2026-10-24 21:02–21:03Z) are bound to this BOM and
  CPL. `check_procurement.py` is OK in both `--cost-only` and full mode.
- **Live re-run (2026-10-25 19:44–19:45Z, scratch copies, repository untouched):**
  - 92 codes, 52 extended / 40 basic (the same extended set);
  - $81.23 parts + 92 × $1.53 / 5 = $109.38 per board (cap $126.41); minimum purchases add nothing;
  - short none, thin none;
  - U4 40 (min purchase 1), U30 34, U31 436, J9 33,373 (min 1).

  M3 is met with no extended code to spare. The 24 h window of the recorded run ends 2026-10-25 ≈ 21:03Z, so
  `FAB_NET=1 m3_design/r9_fab.sh` is still due before any order (ORDERING §1).
- **U4 consignment:** handled by ORDERING §1 (Parts Manager by hand; the tools have no consignment path). M1's
  wording: R9P1-DFM-05.
- **BOM against R8's:** only the footprint column of J121 / J124 / J122 differs. The CPL holds the same 219
  designators: 83 top (76 SMD + J30 / J31 + 5 THT) and 136 bottom, 26 parts having changed side. Test pads: 14 top,
  10 bottom. DNP C303 / C304 / C305 / C313 / C314 are in no BOM or CPL. All of this equals ORDERING §4.

## 8. Sources

- JLCPCB PCB capabilities, https://jlcpcb.com/capabilities/pcb-capabilities (read 2026-10-25). Each line is the
  page's wording:
  - Via Hole-to-Hole Spacing 0.2 mm; Pad Hole-to-Hole Spacing 0.45 mm;
  - Via hole to Track 0.2 mm; PTH to Track 0.28 mm min (0.35 mm recommended);
  - Inner layer via hole to copper 0.2 mm; inner layer PTH pad hole to copper 0.3 mm;
  - NPTH to Track 0.2 mm; Min. non-plated holes 0.50 mm;
  - Min. pad spacing (soldermask bridge) 0.10 mm, green;
  - "The Minimum Distance Between Pad and Silkscreen is 0.15mm"; character width ≥ 0.15 mm, height ≥ 1.0 mm;
  - copper clearance from routed edges ≥ 0.2 mm;
  - plugged ("filled") vias: no opening on either side, ≥ 0.35 mm from other openings, ≤ 0.5 mm diameter;
  - thickness tolerance ±10 % (≥ 1.0 mm);
  - mouse-bite breakaway ≥ 5 mm; panel spacing 1.6 or 2 mm;
  - 1 oz annular ring minimum 0.15 mm (recommended 0.20).
- EasyEDA / LCEDA component data, `https://easyeda.com/api/products/{C430601,C430603,C2915641}/components` (read
  2026-10-25): pad, silkscreen, document-layer, component-marking and 3D-model records.
- JLC public component search (`jlc_stock.py` / `jlc_cost.py`, live 2026-10-25 19:44–19:45Z).
- IPC-7525 stencil area ratio ≥ 0.66 (general practice).
- Project records:
  - REQUIREMENTS M1 (l. 74), M2 (l. 75), "Accepted risks" and "R9 acceptance" (l. 118–126);
  - ORDERING §1–§5 (l. 29–33, 61–76, 89–119);
  - R9_VALIDATION C13, C18 and "Open"; M3_R9 §"Silkscreen" and §"R9 manufacturing outputs";
  - R9_DECISIONS D-S2-01…03, D-S2-08, D-S9-01, D-S10-03, D-S10-09, D-S10-14;
  - `r9_step7_handoff.md` l. 53; `r9_step9_handoff.md`; `r9_step10_handoff.md`;
  - R8_VALIDATION l. 292 (R8P3-DFM-02), l. 494 (C17), l. 559 ff. (C12b #18 / #23);
  - R8 review `pass3_dfm.md`, `pass4_dfm.md`;
  - `m3.kicad_dru` l. 83 / 112;
  - `tools/jlc_orient.py` (PAD_ALIAS, BODY), `tools/jlc_corrections.json`.

## 9. Inferences

- That EasyEDA layer 101 is the component-marking (pin-1 / polarity) layer JLC's placement review shows, and that a JLC
  engineer may turn a terminal to put that mark on the square pad (R9P1-DFM-01).
- That a bridge from a bare pad to masked copper 0.15 mm away needs a mask breach (R9P1-DFM-02, as R8).
- That an open via whose ring is exposed beside a pad can draw solder from the joint, and the volume comparison
  (R9P1-DFM-04).
- Whether JLC applies its 0.45 mm pad-hole spacing to NPTH-to-via pairs (R9P1-DFM-08).
- That no bottom part risks dropping in the second reflow (mass per pad area, no maker figure).
- JLC's acceptance of four tabs (inherited).

## 10. Method (reproducible, read-only)

**Scripts** (session scratchpad `r9review/dfm1/`, deleted after the run). KiCad 10.0.6 Python, `pcbnew.LoadBoard`; no
board saved, except a scratch copy for the relief experiment.
- `export_geom.py`, `export_silk.py`: pads per layer, vias with per-layer flashing, tracks, zone fills, courtyards and
  silkscreen items to JSON.
- `gerb.py`: a Gerber flash, draw, region and polarity parser for KiCad's apertures (C / R / O / RoundRect /
  FreePoly).
- Analyses (shapely 2.0.7 in a scratch venv):
  - `dfm.py`: via against mask and paste;
  - `dfm2.py`: mask webs, paste area ratios and coverage;
  - `holes.py`: hole spacing, hole-to-copper per layer, annular rings;
  - `silk.py`: silkscreen sizes and openings.
- `variants.py`: library and instance comparison of the variants.
- `tht_zc.py`, `spokes.py`, `j122_relief.py`: zone connections; the relief experiment on a scratch copy with
  `ZONE_FILLER` and `kicad-cli pcb drc`.
- `npth.py`: NPTH-to-via on R9, R8 and R7, the latter two read-only.
- `markcheck.py`: the order mark.

**Tool runs:**
- `NUMPY_PY=<cfd venv> tools/check.sh` (exit 0);
- `tools/export_fab.py --out <scratch>`, with the BOM, CPL, Gerber, drill, job-file and PDF diffs;
- `tools/jlc_orient.py … --out <scratch>` and `--verify-cpl`; `tools/paste_check.py`; `tools/fab_manifest.py`;
- `tools/check_procurement.py` (both modes);
- `tools/jlc_stock.py` / `tools/jlc_cost.py --fab <scratch>` (live);
- `tools/tab_windows.py --json <scratch>`;
- the test suites `test_paste_check` 5, `test_fab_validation` 23, `test_procurement` 15, `test_r9_sch` 21,
  `test_r9_post` 13, `test_fit_check` 23: all OK;
- `pdftotext -layout` on both assembly PDFs: all 219 placed designators present.
