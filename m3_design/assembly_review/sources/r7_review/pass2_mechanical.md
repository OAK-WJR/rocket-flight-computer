# R7 pass 2: mechanical fit and robustness review

Independent, read-only review (2026-10-15) of the uncommitted M3-ASSY-R7 board on branch `m3-assy-r7`. The
board file `m3_design/assembly_review/m3.kicad_pcb` had SHA-256
`03fe75720f46b1382d9d3216dbffd8ae642d0125722c04589ff97c964aa86d54` before and after this review (checked
three times). Scope: P1–P3 mechanics, meaning bore fit, supports and keep-outs, SMA overhang, mated plugs
and coax room, part heights, staking and retention, and the bay-stack consequences in the parent
`docs/VEHICLE.md`. Vehicle-level choices and firmware are out of scope. No repository file was changed apart
from this report. The scratch scripts are in the session scratchpad, and the plate model is reproduced in
the Appendix.

What was run:
- `tools/check.sh` (exit 0): DRC 0, unconnected 0, parity 0, ERC 0; audit, silk, R7 contract, actuator
  contract and fit all OK.
- `tools/fit_check.py`, and its `check_board()` called directly for the RF rows.
- KiCad 10.0.6 `pcbnew` dumps of every footprint: model boxes via `fit_check.model_box`, courtyards, pads,
  Edge.Cuts circles, tracks and vias, and zone fills. Zones were filled in memory only; nothing was saved.
- The same dump of the committed R6 board (`git show 3b215ba:…/m3.kicad_pcb`, SHA-256 `184a87e8…0680`).
- A Kirchhoff-plate Rayleigh–Ritz modal and quasi-static model of both boards on their point supports
  (numpy). It was validated against closed-form cases (§3.3).
- Maker documents fetched: the Kinghelm KH-SMA-KE8-G datasheet and drawing, the u-blox MAX-F10S data sheet
  R03, the EBYTE E22-900MM22S manual, and an Amphenol SMA crimp-plug outline.

## 1. Summary

**Critical 0, Major 3, Minor 2.**

The CAD envelopes pass. Every part and mated plug fits the Ø50.8 mm bore with the top face on the axis.
The new RF parts have large margins: J30 mated 8.91 mm, U30 6.12 mm, U31 12.28 mm. The thinnest margins
are still R6's, unchanged: J9 mated 0.03 mm and C84 0.11 mm. The five supports meet P2's 3.5 mm bottom and
3.8 mm top clearances, and the J122 tie path is preserved.

The problems sit at the aft end and in the records:
1. **MECHANICAL-01 (Major, P3):** each edge-launch SMA jack holds its mated plug, and takes the maker's
   0.8–1.13 N·m mating torque, only through four 0.9 mm brass legs soldered to 1.2 × 4.2 mm SMD pads.
   - Nothing stakes, clamps or counter-holds the jack.
   - The documents say "torque the SMA nuts".
   - The sled wording contradicts the 2 cm coax tie.
   - P3's ≥ 5× at 100 g cannot be shown for J30/J31.
2. **MECHANICAL-02 (Major, P2):** the support-span and vibration estimate P2 requires on the R7 geometry has
   not been made. My plate model reproduces the R5 record's estimates for the R6-style supports. It gives:
   - R7's first mode at 176–380 Hz, against 241–559 Hz for R6: about 30 % lower.
   - The cause: the now 110.4 mm unsupported right edge, plus ~11 g of jack and plug cantilevered beyond the
     aft edge. The overhang adds an aft-rocking mode at 269–380 Hz and raises U31's 100 g strain about 1.6×.
   - The mid-span hole (4, 64) is effective: f1 is 1.9–2.3× the corners-only value.
   - Carrying the plugs on the sled and adding a right-edge support would give 385–994 Hz.
3. **MECHANICAL-03 (Major, P1):** the bay stack is not recorded for R7. VEHICLE.md still describes the R5
   board (100 mm, mid hole at (4, 46), 15 mm lead zone, ~115 mm slack), and M3_R7 has no stack section.
   - The REQUIREMENTS board-position assumption (aft edge at joint +50) puts the mated SMA plugs about
     11 mm into the documented battery bay, and the coax loops about 26 mm into it.
4. **Minor:**
   - MECHANICAL-04: the coax-loop allocation (~40 mm) rests on an undocumented plug length, and two equal
     U-turn loops must cross under the board.
   - MECHANICAL-05: the mounting-hardware size is not specified, although the (4, 64) clearance is only
     0.059 mm above the rule for a 7 mm washer.

## 2. Findings

| ID | Sev. | Req. | Finding | Evidence | Recommended fix |
|---|---|---|---|---|---|
| MECHANICAL-01 | Major | P3 (≥ 5× at 100 g; "SMA nuts torqued"; coax tie), F10 jack | J30/J31 retention rests on the solder joints alone. The jack (and its mated plug, ~5.5 g with its centre of mass ~14 mm beyond the edge, Inference) is held only by four 0.9 mm square brass legs straddling the board, soldered to 1.2 × 4.2 mm SMD pads, plus the Ø0.95 centre-pin joint. No anchoring PTH, staking, clamp or counter-hold is specified. The maker recommends 0.8–1.13 N·m mating torque. The jack has no hex, only a 1.5 mm-thick 6.5 mm square flange beyond the edge. The documents tell the builder to torque the plug nut, so the board's pads react that torque. The required sled/tie arrangement is self-contradictory, so the plug may be carried by the jack alone. | **Footprint** `kilib/rocket.pretty/M3_SMA_KH_KE8_EDGE.kicad_mod`: pads 1/2 F.Cu and 3/4 B.Cu at x ±2.55, 1.2 × 4.2 mm at y 0.2–4.4; centre pad 5; `attr smd`. **Kinghelm datasheet** p. 1: "Recommended mating torque 0.8～1.13 N·m"; p. 2 drawing: 13.5 = legs 4 + flange 1.5 + thread 8, 6.5 mm square flange. **Load (Inference)**: 100 g gives 5.4 N and 75 N·mm at the edge; at 5×, 27 N and 373 N·mm, reacted across the ~4 mm leg overlap as a 93–138 N couple, i.e. **47–69 N per leg**. **Torque**: 0.8–1.13 N·m / (4 × 2.55 mm) gives **78–111 N per leg** (157–222 N if only the two bearing legs share it). **Capacity**: typical 1 oz copper peel ≈ 1–1.4 N/mm (Inference); no pad pull-off rating is available, so ≥ 5× cannot be shown. **Documents**: REQUIREMENTS P3 (l. 68) and ORDERING §7 "Antennas and coax" (l. 190): "Torque the SMA nuts and witness-mark them", with no value and no counter-hold. ORDERING §5 staking list (l. 139) omits J30/J31. MARGIN_PRESCRIPTION R14 (l. 270) has no R7 row. ORDERING §7 "Sled" (l. 193): "must end at the aft edge or be relieved there", but l. 190 wants a tie "within about 2 cm of its jack", and the plug alone reaches 25.5 mm beyond the edge (`fit_check` MATED box). | (1) P3 and ORDERING §5/§7: counter-hold the jack's square flange (flat-jaw pliers or a thin 7 mm open-end spanner) whenever the plug nut is turned. Give the torque value (the plug maker's, ≤ Kinghelm's 1.13 N·m), and never let the board react it. (2) After the RF bench tests, stake each jack: a structural-epoxy fillet from the flange back face to the board edge and along the four GND legs on both faces. Keep it off the centre pad/GCPW, the threads and the mating face. Add J30/J31 to the ORDERING §5 staking list and an R7 row to MARGIN_PRESCRIPTION R14 (U30/U31 need none, §3.5). (3) Carry the plugs on the sled: a sled tongue ≈ 25–30 mm aft of the board edge with a saddle or tie at each plug's crimp ferrule, or a block with 6.5 mm square pockets that captures both flanges. Keep it below the plug nuts, which hang ≈ 2.5 mm below the bottom face. Rewrite the ORDERING "Sled" row to match. This reacts lateral loads and torque into the sled, and takes the overhang mass off the board (MECHANICAL-02). |
| MECHANICAL-02 | Major | P2 ("Re-derive … support-span/vibration estimates on final R7 geometry") | Not re-derived. A plate model puts R7's first mode at **176–380 Hz, about 30 % below R6's 241–559 Hz**. The same model gives 128–181 Hz → 241–341 Hz pinned for R6-style supports, matching the R5 record's ~140 → ~270–290 Hz. Two R7 changes cause the drop. (a) The right edge is now 110.4 mm unsupported (R6 92.4 mm); mode 1 peaks there at y ≈ 46–62 with U1 and C121. (b) About 11 g of jack and plug is cantilevered at the aft edge, which adds an aft-rocking mode at 269–380 Hz (point-clamped bound) and couples into mode 1. The mated plugs raise U31's 100 g strain about 1.6×, to the highest value of any IC on the board. (4, 64) is effective: f1 is 1.9–2.3× the corners-only value. A right-edge support is the most effective addition, but the aft mode caps it until the plugs leave the board. | **No R7 estimate exists**: M3_R7.md, R7_VALIDATION.md, stepB_handoff.md and ORDERING contain none (grep "Hz"). pass1_layout §3.3: "it is not done here". **Supports** (Edge.Cuts Ø3.2, pcbnew): (4, 4), (42.3, 4), (4, 64), (4, 114.4), (42, 114.4). Left spans 60.0 / 50.4 mm (R6 42.0 / 50.4); right edge 110.4 mm unsupported (R6 92.4); aft corners 38.3 mm apart. **f1 (§3.3), pinned D 5 → clamped D 10 N·m**: R6 241–559 Hz; R7 with plugs **176–380 Hz** (152–510 Hz over overhang-mass sensitivity); R7 corners only 91–276 Hz; R7 with the plugs carried off the board 221–533 Hz; that plus a support at (43, 69) 385–994 Hz; plugs on the jacks plus (43, 69) 191–383 Hz. **100 g quasi-static strain at U31** (Inference): 918 → 459 µε with plugs against 560 → 280 µε without. Other ICs are at or below R6 (U4 678 vs 682, U1 392 vs 540 µε at D 5). **Precedent**: M3_R5 §1e R2 rated the corners-only in-band first mode (~140 Hz) Major and accepted ~270–290 Hz. | Record the R7 estimate (method, inputs, results) in M3_R7. Carry the SMA plugs on the sled (MECHANICAL-01 fix 3): f1 is then 221–533 Hz, about R6's value. To exceed R6, add a sixth support on the right edge. A courtyard-clear window exists at about (42.5–43.5, 69.0), ≥ 3.8 mm top / ≥ 3.5 mm bottom from courtyards; an F.Cu NRST track and a GND via within 2.1 mm would have to move. With the plugs carried, f1 becomes 385–994 Hz. Moving the mid support there instead is worse (207–486 Hz). Bench: tap or modal check of the board on its sled with both coax leads fitted. |
| MECHANICAL-03 | Major | P1 ("Record final outline, orientation and bay stack in M3_R7.md and parent VEHICLE"); REQUIREMENTS board position | The parent VEHICLE.md stack row is R5's, and M3_R7 has no bay stack. A sled built from VEHICLE puts the forward standoffs at y 96.4 and the mid one at y 46. The board-position assumption still in REQUIREMENTS is now infeasible. At the aft edge's stated joint +50 ± 3, the mated SMA plugs reach joint +24.5, 10.9 mm inside the battery bay, and the coax loops reach joint ≈ +9. Orientation (jacks aft at y = 0; J1's entry facing forward at y = 118, so the battery leads run the board's length) is not recorded either. | VEHICLE.md l. 39: "flight computer board 100 (M3-ASSY-R5, 46 × 100 mm … mid-span at PCB (4, 46) mm …)", "battery leads ~15", "Leaves ~115 mm of slack". The working-tree diff does not touch R7. `grep -i "stack\|bay\|VEHICLE" docs/M3_R7.md`: none. REQUIREMENTS l. 86 "Aft edge about 70 mm below the coupler's forward end, ± 3 mm"; VEHICLE coupler to joint +120 gives joint +50. Battery bay: bulkplate top joint −44.6 + 80 = joint +35.4. Jack faces +40.5; plug ends +24.5 (`fit_check` 16 mm), or +20.5 with a 20 mm plug. Needed: aft edge ≥ joint +76 (41 mm zone), or ≥ +88 if the loops must clear the shroud (joint +4…+47). Slack 595 − (80 + 41 + 118 + 25 + 260) = **71 mm**, or **59 mm**. Known open: STATUS.md l. 34, R7_VALIDATION L3. | Update the VEHICLE row (text in §3.6). Add an "R7 bay stack and orientation" paragraph to M3_R7. Replace the REQUIREMENTS board-position value with "aft edge at joint ≥ +76 (coax loops on the side away from the shroud) or ≥ +88 (loops entirely forward of the shroud); fixed after the Onshape shroud measurement". |
| MECHANICAL-04 | Minor | P1/P2 (coax loop allocation, SMA-plug envelope basis) | The ~40 mm coax zone is optimistic, for two reasons. The 16 mm mated-plug length and 5/16″ hex in `fit_check` have no drawing behind them. And two equal 13 mm-radius U-turns cannot both stay inside the bore without crossing under the board in the same axial slab. Radial fit is unaffected. | `tools/fit_check.py` l. 42–50 basis: "about 16 mm more (5/16 in coupling nut, 9.17 mm across corners; Inference)". ORDERING l. 190: "about 40 mm". Amphenol SMA crimp-plug outline (LCSC C5868624 datasheet; Amphenol 132113 rev D, drawn for RG-58): 8 mm [.315] hex (9.24 mm AC) and an 18.2 mm REF body from the nut face, plus a ferrule. Radial margin with 9.24 AC: J30 8.90 mm (8.91 modelled). **Loop geometry (Inference)**: J30 starts at (−10.15, +0.45) mm and J31 at (+8.54, +0.45) mm from the axis. A 26 mm chord must point within ±65° of the inward direction to keep the cable at r ≤ 23.65 mm. The two loops then cross at ~85 % of the chord, ~19.6 mm below the top face. | Choose the plug and coax, and cite the plug drawing in the MATED basis. Allocate ~44–48 mm with axially staggered loops (≥ 1 cable OD), or use right-angle plugs. State this in ORDERING §7 and VEHICLE (slack then ~64–68 mm, or ~52–56 mm with shroud clearance). |
| MECHANICAL-05 | Minor | P2 (nylon hardware, top hardware clearance) | The hardware size is unspecified while the clearance is at the rule's edge. `fit_check` assumes a 7 mm OD washer (3.8 mm rule). At (4, 64), the exposed TP89 pad is 3.859 mm from the centre: 0.059 mm of margin, inside TP89's courtyard (3.555 mm). BUZZ_DRV (F.Cu and B.Cu) runs 0.78 mm from that hole's edge, under the washer and standoff. BAT_IN (In2) and GND pours come to 0.5 mm from the milled hole edges (±0.2 mm). ORDERING says "nylon standoffs, or nylon washers and screws" with no size; a common 9 mm (DIN 9021-type) washer would cover TP89. | pcbnew: top pad TP89.1 3.859 mm, courtyard 3.555 mm; tracks B.Cu/F.Cu BUZZ_DRV within 2.376 mm of the (4, 64) centre; fills at 2.1 mm from every support centre (In2 BAT_IN at (4, 64), In2 BAT_IN and F.Cu RAW_ACT at (4, 114.4)). ORDERING l. 194. | ORDERING "Mounting hardware": M3 nylon screws and nuts, nylon washers ≤ 7.0 mm OD, nylon standoffs ≤ 5.5 mm AF (≤ Ø6.4 mm), the standoff ≥ 3.5 mm tall so the plate clears L1 (3.02 mm below the bottom face). |

## 3. Measurements

### 3.1 Bore fit (P2), `fit_check` model plus own checks

Usable radius 24.9 mm (Ø50.8 less 0.5 mm wall), axis x = 23.0, sled tolerance ±0.3 mm in both axes, top face
on the axis.

| Item | Box (x; z), mm | Margin |
|---|---|---|
| J9 mated (R6, unchanged) | 40.95–45.20; 0–10.30 | 0.03 |
| C84 (R6, unchanged) | 2.25–12.75; 0–12.80 | 0.11 |
| J122 mated | 19.00–27.00; 0–23.50 | 0.71 |
| U30 MAX-F10S (2.7 mm max, DS R03 Table 21 "C") | 4.76–16.06; 0–2.70 | 6.12 |
| J30 mated (plug box ±4.6 mm, z −4.1…+5.1) | 8.25–17.45; −4.1–5.1 | 8.91 (8.90 with an 8 mm AF hex) |
| J31 mated | 26.94–36.14; −4.1–5.1 | 10.42 |
| J30 / J31 jack body (flange 6.7 sq. with tolerance, z −2.9…+3.8) | 9.50–16.20 / 28.19–34.89 | 10.50 / 12.04 |
| U31 E22-900MM22S (2.5 ± 0.2, modelled 2.7) | 24.76–34.96; 0–2.70 | 12.28 |
| Bare board corner (x 0/46, z −1.6) | — | 1.52 (r = 23.38) |

- **Jack geometry from the Kinghelm drawing.** The jack axis is 0.45 mm above the top face: slot top 2.8 + 0.9
  below the flange top, against a 3.25 mm half-flange. The flange spans z −2.8…+3.7, so it hangs 1.2 mm
  below the bottom face (1.4 mm at +0.2 tolerance; ORDERING says "about 1.3").
- **Mated plug.** With an 8 mm AF hex, the coupling nut reaches z −4.17, about 2.57 mm below the bottom face.
- **Clearances.** Every jack and plug point is at r ≤ 15.9 mm, including tolerance, so all clear the camera
  shroud's 18.4 mm chord at any angle. Only the coax loops can reach it.

### 3.2 Supports, spans, keep-outs

| Support | Top courtyard / exposed pad (rule 3.8 hardware) | Bottom courtyard / pad (rule 3.5) | Copper within 3.5 mm |
|---|---|---|---|
| (4, 4) | U30 4.52 / TP30 5.01 | J30 5.31 / J30.3 5.70 | GND via; GND fill on all layers at 2.1 mm |
| (42.3, 4) | J31 7.22 / J31.2 7.61 | J31 7.22 / J31.4 7.61 | GND via; GND fills |
| (4, 64) | TP89 courtyard 3.555 / **TP89.1 3.859** | TP92 4.18 / 4.60 | BUZZ_DRV F.Cu and B.Cu (2.38 mm); In2 BAT_IN fill |
| (4, 114.4) | TH3 tooling-hole edge 2.96 (NPTH, R6 geometry) | Q121 5.46 / TH3 | F.Cu RAW_ACT and In2 BAT_IN fills at 2.4 mm |
| (42, 114.4) | J1 7.91 / J1.1 10.44 | C76 3.86 / 4.42 | GND via, GND fills |

- **Spans.** Left edge 60.0 mm (4 → 64) and 50.4 mm (64 → 114.4). Right edge 110.4 mm unsupported. Aft pair
  38.3 mm apart, forward pair 38.0 mm.
- **Tie path.** The J122 tie line (21.5, 68.6)–(27.0, 82.6) is clear of bottom parts by ≥ 3.25 mm (D121). It
  crosses J122's own pin tails, as designed since R5.

### 3.3 Plate model: modes and quasi-static flex (P2)

**Method.** The board is a Kirchhoff plate (46 × L mm) analysed by Rayleigh–Ritz.
- **Basis:** products of Legendre polynomials up to degree 20 in x and y. Converged within 2.5 % (degree
  14 → 26: 178 → 174 Hz).
- **Supports:** point constraints at the five hole centres, either pinned (w = 0, lower bound) or
  point-clamped (w = ∂w/∂x = ∂w/∂y = 0, an upper bound for a nut-and-washer clamp).
- **Validation:**
  - corner-supported square: λ = 7.111 (Leissa 7.12);
  - simply supported square: λ1 = 2π² exactly, and centre deflection 0.00406 qa⁴/D;
  - clamped strip: 3.516.
- **Stiffness:** D = 5 N·m (E ≈ 14–15 GPa, Steinberg-type) and 10 N·m (1.566 mm JLC041611 laminate at
  20 GPa plus ~50 % outer and ~80 % inner copper fill). Both are Inference.
- **Mass:**
  - laminate 3.65 kg/m² (Inference);
  - small parts at 3 g/cm³ of their model-box volume;
  - lumped heavy parts (Appendix table): U30 and U31 at 0.5 g from the maker data sheets, the rest Inference;
  - each mated SMA jack and plug as a rigid overhang at the aft edge (5.55 g, centre of mass 13.7 mm beyond
    the edge, 335 g·mm² about its own centre of mass), coupled to w and ∂w/∂y.
- The R6 board is modelled the same way at its own positions.
- **Cross-check against the record:** for R6 the model gives 128–181 Hz with the corners only and 241–341 Hz
  with the mid hole (pinned, D 5–10). M3_R5 §1e records ~140 Hz and ~270–290 Hz.
- **Appendix code:** run on the dumped geometry, it reproduces the pinned values (R6 241 / 341 Hz, R7 176 /
  249 Hz).

| Case (board mass) | Pinned, D 5 | Pinned, D 10 | Clamped, D 5 | Clamped, D 10 |
|---|---:|---:|---:|---:|
| R6, 5 supports (44.3 g) | 241 | 341 | 396 | 559 |
| R6, 4 corners only (cf. R5 record ~140 Hz) | 128 | 181 | 251 | 355 |
| R7, plugs mated on the jacks (57.3 g) | **176** | **249** | **269** | **380** |
| R7, plugs mated, 4 corners only | 91 | 129 | 195 | 276 |
| R7, jacks only (plug mass carried by the sled) | 221 | 313 | 377 | 533 |
| R7, no jacks or plugs, 5 supports (46.2 g) | 222 | 314 | 377 | 533 |
| R7, no jacks or plugs, 4 corners only | 98 | 139 | 198 | 281 |
| R7, no plugs, + support (43, 69) | 385 | 544 | 703 | 994 |
| R7, plugs on the jacks, + support (43, 69) | 191 | 270 | 271 | 383 |
| R7, no plugs, mid support moved to (43, 69) | 207 | 293 | 343 | 486 |
| R7 overhang sensitivity: 3.5 g at 11.5 mm / 7 g at 15 mm | 208 / 152 | 294 / 215 | 361 / 223 | 510 / 316 |
| Bare laminates R6 / R7 | 408 / 324 | 578 / 458 | 668 / 538 | 944 / 760 |

All values are f1 in Hz.

**Mode shapes** (D 5, pinned; amplitudes normalised to the largest):
- R7 with plugs, mode 1 (176 Hz):
  - right edge: (46, 35) −1.00, (46, 60) −0.99, (46, 90) −0.53;
  - parts: U1 −0.54, C121 −0.57;
  - aft-edge centre +0.38, J30/J31 edges +0.31/+0.39, left (0, 34) −0.34.
- R7 with plugs, modes 2 and 3 (240 and 283 Hz): right-edge modes, with the jacks out of phase in mode 3
  (J30 +0.39, J31 −0.68).
- The pure aft-rocking mode (both jacks in phase, peak at (29.5, 0)) is mode 1 of the point-clamped cases,
  at 269–380 Hz. It also caps the right-edge-support case at 191–383 Hz.
- R7 without plugs, mode 1 (222 Hz): right edge (46, 60) 1.00, (46, 35) 0.75, (46, 90) 0.69, with C121 0.69
  and U1 0.47; the aft strip about 0.
- R6 mode 1 (241 Hz): right edge (46, 60) −1.00, (46, 35) −0.86, with U1 −0.53 and C121 −0.58.

**Quasi-static 100 g transverse** (D 5, pinned; halve for D 10, about 0.3–0.4× for clamped).
- Maximum deflection: R6 0.74 mm at (46, 53.5); R7 with plugs 0.77 mm at (46, 69.5); R7 without plugs
  0.94 mm at (46, 63).
- The aft overhang partly counter-balances the board, so the maximum falls with the plugs on.
- Peak principal surface strain, D 5 → D 10 (µε):

| Part | R6 | R7, plugs mated | R7, no plugs |
|---|---:|---:|---:|
| U31 (stamp hole) | — | **918 → 459** | 560 → 280 |
| U30 (LCC) | — | 614 → 307 | 538 → 269 |
| U4 (IMU, LGA) | 682 → 341 | 678 → 339 | 688 → 344 |
| U1 (LQFP-100) | 540 → 270 | 392 → 196 | 513 → 257 |
| J121 | 834 → 417 | 832 → 416 | 873 → 436 |
| C121 | 683 → 341 | 679 → 339 | 687 → 344 |

**Context (Inference).** DESIGN_ASSURANCE's GEVS workmanship analogy is 0.04 g²/Hz.
- With Q = 10, a mode at 176–380 Hz responds at about 10.5–15.5 g rms (32–46 g at 3σ); the 0.16 g²/Hz ELV
  analogy gives 21–31 g rms (63–93 g at 3σ).
- Both are inside the 100 g design load, so fixing MECHANICAL-01's retention also covers the jacks under
  vibration.
- The board-level concern is the missing P2 estimate, an f1 about 30 % below the accepted R6 value, and the
  highest IC strain now at the leadless U31. It is not an immediate overload.

### 3.4 SMA jacks J30/J31 (F10, P2, P3)

**Position.**
- J30 at x 12.85 and J31 at x 31.54, both at y = 0 (the footprint origin is the edge), 18.69 mm apart centre
  to centre.
- The flange back face is flush with the routed edge. The legs run y 0–4.0, on pads at y 0.2–4.4.
- The body reaches 9.5 mm beyond the edge; `fit_check` takes the mated plug to 25.5 mm.

**Torque and lateral load path.**
- The four legs sit at x ±2.55 mm, two on each face.
- Torque about the jack axis, and bending about x, are reacted by one leg pair bearing on the board and the
  other in peel. The split depends on the solder fill in the 0.13 mm slot play (slot 1.7 mm against the
  1.566 mm laminate).
- In-plane bending, about z, goes into solder shear and flange bearing on the edge.
- If the legs or pads yield, the centre-pin joint (Ø0.95 tail on the 1.2 mm pad) cracks first (Inference).
  That gives an RF open or an intermittent fault that inspection does not see.

**Axial loads** (boost, ejection, landing, along the jack axis) are shear on five pads: 27 N at 5 × 100 g
spread over five joints. This is benign.

**Load and capacity numbers** are in the MECHANICAL-01 row.
- Mass estimates (Inference): jack ≈ 1.8 g from the brass volume (flange 44 mm³, thread shell 121 mm³, legs
  13 mm³ at 8.5 g/cm³, plus 0.28 g of PTFE); plug ≈ 3.5 g; RG316 ≈ 12 g/m.
- The plug length and hex come from the Amphenol outline.

**Sled interface.**
- The flanges hang 1.2–1.4 mm and the plug nuts about 2.6 mm below the bottom face.
- The standoffs must exceed L1's 3.02 mm in any case, so the plate never needs relief for the flanges.
- A sled tongue under the plugs (MECHANICAL-01 fix 3) keeps about 0.45 mm under the nuts at the minimum
  standoff height. Set the standoff at ≥ 3.5 mm.

### 3.5 Modules, heights, staking (P3)

**Tall parts** (top unless noted; heights in mm):
J1 14.5, J121/J124 14.4, C84 12.8, C121 10.5, J122 8.54 (23.5 mated), J123 6.0 (9.5 mated), J9 4.2,
J30/J31 3.7 (+0.2), J3 3.25, L1 and L3 3.0 (bottom), U30/U31 ≤ 2.7.

**Staking list.** ORDERING §5 stakes C84, C121, the three terminals, J122 and J123. That covers every
two-terminal tall part.
- The only new parts needing retention are J30/J31 (MECHANICAL-01).

**U30 and U31.**
- U30: 0.5 g, u-blox DS R03 Table 21, 18 LCC pads. U31: 0.5 ± 0.02 g, EBYTE manual, stamp holes.
- At 100 g each sees 0.49 N, far below the shear capacity of 18–22 joints. No staking is needed.
- Coating and adhesive stay off both (ORDERING §5, u-blox IM §5.2).
- Their exposure is board strain (§3.3), not inertia.

### 3.6 Bay stack (P1, parent VEHICLE.md)

Joint coordinates, from VEHICLE:
- bulkplate top −44.6;
- battery bay 80 mm, to +35.4;
- camera shroud +4…+47, to 18.4 mm from the axis;
- coupler bore Ø50.8 to +120, Ø54.6 above;
- free length 595 mm to the nose-shoulder base at +550.

| Arrangement | Aft edge (joint) | Coax zone | Board forward edge | Slack |
|---|---|---|---|---|
| REQUIREMENTS "Board position" as written | +50 ± 3 | Plugs to +24.5 (to +20.5 with a 20 mm plug), **inside the battery bay by 11–15 mm**; loops to ≈ +9 | +168 | n/a (overlap) |
| Loops may overlap the shroud's axial range (away from its side) | ≥ +76.4 (41 mm zone) / +80–83 (44–48 mm, MECHANICAL-04) | jack 9.5 + plug 16–20 + loop 15.5 (+2.5 stagger) | +194–201 | **71 / 64–68 mm** |
| Loops entirely forward of the shroud | ≥ +88 / +91–95 | same | +206–213 | **59 / 52–56 mm** |

Suggested VEHICLE row text:

> "… battery bay ~80 mm, battery leads and RF coax loop zone ~45 (two RG316 loops, 13 mm bend radius,
> staggered; off the camera-shroud side between joint +4 and +47), flight computer board 118 (M3-ASSY-R7,
> 46 × 118 mm, parts on both sides; two edge SMA jacks on its aft edge reaching 9.5 mm beyond it, straight
> plugs ~16–20 mm more; J1's battery entry faces forward at the board's forward edge; the sled puts the top
> face on the bore axis on nylon standoffs at all five M3 holes — corners (4, 4), (42.3, 4), (4, 114.4),
> (42, 114.4) and mid-span (4, 64) mm — plate ≥ 3.5 mm below the bottom face, non-conductive, carrying both
> SMA plugs aft of the board edge) … Leaves ~52–71 mm of slack depending on the shroud clearance."

## 4. Items checked and found acceptable (no finding)

- **Bore fit.** All 219 fitted footprints with models, plus the mated GH, servo, pull-pin and SMA envelopes,
  are inside the bore (§3.1). The 3D envelopes of U30, U31 and J30/J31 use the maker maxima. No mated
  envelope intersects another body.
- **P2 support rules.** 3.5 mm bottom and 3.8 mm top hold at all five supports (§3.2). There is a corner
  support within 6 mm of each corner, and (4, 64) lies in the middle third.
- **J122 tie path.** Both retention holes are preserved.
- **Module and jack heights.** ≤ 3.8 mm above the top face in the strip, with ≥ 6 mm radial margin.
- **SMA spacing.** 18.69 mm centre to centre leaves a 9.5 mm gap between the mated plug nuts (8 mm hex).
  Spanner access to each nut is an Inference.
- **Sled clearance under the strip.** The jacks' bottom legs (z −1.7…−2.6) and flanges are above any plate
  that clears L1.

Inherited from R6 and unchanged, not new findings:
- J9 mated margin 0.03 mm and C84 0.11 mm;
- TH3 tooling hole under the (4, 114.4) washer and standoff, with a 1.36 mm web between the hole edges;
- the forward 50 mm with no panel tab (DFM; ORDERING §3).

## 5. Sources

- Kinghelm KH-SMA-KE8-G datasheet and drawing (LCSC C530661):
  https://datasheet.lcsc.com/datasheet/pdf/35ad22a9bea57e53d493009a20c931ef.pdf?productCode=C530661
  - p. 1: mating torque 0.8–1.13 N·m, assembly torque ≥ 0.5 N·m, brass HPb59-1 body, wave-solder 240–250 °C
    5 s;
  - p. 2: 13.5 / 4 / 8 mm, 6.5 mm square flange, 1.7 mm slot, 0.9 mm legs, 4.2 / 6 mm leg spacing, Ø0.95 pin.
- u-blox MAX-F10S data sheet UBXDOC-963802114-12732 R03, Table 21 (A 10.1 max 10.7, B 9.7, C 2.5 max 2.7,
  weight 0.5 g):
  https://content.u-blox.com/sites/default/files/documents/MAX-F10S_DataSheet_UBXDOC-963802114-12732.pdf
- EBYTE E22-900MM22S manual (10 × 10 × 2.5 mm, stamp holes at 1.27 mm, "Product net weight 0.5 g ± 0.02 g"):
  https://datasheet.lcsc.com/datasheet/pdf/70331b0eaf0eedaea0129e9e66d9a011.pdf?productCode=C5333985
- Amphenol RF SMA crimp plug customer outline, part 132113 rev D (8 mm [.315] hex, 18.2 mm REF body; drawn
  for RG-58):
  https://datasheet.lcsc.com/datasheet/pdf/d19b1483006bb614f660993a6029c8ad.pdf?productCode=C5868624
- JLC parts API (POST https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList),
  2026-10-15. Attributes only: DB128V-4P "Height Above Board 14mm", DB128L-2P 14.1 mm, 35SVPK330M Ø10 ×
  12.6 mm, MA25V470M8x10 Ø8 × 10 mm. No weights are published.
- RG316 13 mm minimum bend radius as cited by pass1_layout §7 (L-com RG316-1K). Not re-fetched: the L-com URL
  returned HTML.
- Project files:
  - `tools/fit_check.py`;
  - `docs/REQUIREMENTS.md` P1–P3 (l. 66–68) and Board position (l. 86);
  - `docs/ORDERING.md` §5 (l. 139) and §7 (l. 190, 193, 194);
  - `docs/MARGIN_PRESCRIPTION.md` R14 (l. 270);
  - `docs/M3_R5.md` §1e;
  - `docs/DESIGN_ASSURANCE.md` §6.1 (l. 240);
  - `STATUS.md` l. 34;
  - `docs/R7_VALIDATION.md` (L3);
  - parent `docs/VEHICLE.md` l. 36–41;
  - `m3_design/assembly_review/sources/r7_review/pass1_layout.md` §3.3, §6.

## 6. Inferences (not measured, not from a primary source)

- **Masses** of the jack (1.8 g, from brass volume), the straight SMA plug (3.5 g), RG316 (≈ 12 g/m), the
  screw terminals (≈ 1.3 g per pole plus lead share), the cans, J122 with its servo plugs, and the small
  parts (3 g/cm³ of box volume). U30/U31 at 0.5 g are maker data.
- **Plate stiffness** D = 5–10 N·m and laminate areal density 3.65 kg/m². Point supports as pinned or
  point-clamped bounds. A rigid jack and plug, and a rigid sled. The coax is assumed to add no stiffness,
  which is conservative.
- **Strain levels and the vibration response** (Miles' equation, Q = 10, GEVS analogies). They are trends
  and orders of magnitude, not qualification values. The R6/R7 ratio is the robust result.
- **Per-leg loads** from a lever split over the 4 mm leg overlap and the 2.55 mm leg offset. Copper peel
  strength ≈ 1–1.4 N/mm is a typical laminate value, not this order's laminate.
- **Plug length beyond the jack face** (14–20 mm) for an RG316 crimp plug, inferred from the 132113 body
  length.
- **Coax-loop crossing**, from planar U-turn geometry at 13 mm bend radius.

## Appendix: plate model (numpy; reproduces §3.3)

Lumped masses (g):

| Part | Mass | Part | Mass |
|---|---:|---|---:|
| J1 | 6.2 | J121, J124 | 3.1 each |
| J122 (with plugs) | 4.0 | C84 | 1.8 |
| C121 | 1.5 | J3, J9 | 0.8 each |
| J123 | 0.6 | U1 | 0.65 |
| U30, U31 | 0.5 each | L3, LS120 | 0.3 each |
| L1, U3 | 0.15 each | R6 only: J130, J131 | 0.8 each |
| R6 only: L4 | 0.3 | | |

SMA overhang: m 5.55 g, d 13.7 mm, I 335 g·mm². Supports: the board's Ø3.2 Edge.Cuts circles less the two
J122 tie holes. ν = 0.15. Units SI.

```python
import numpy as np, math
from numpy.polynomial import legendre as L
def leg(n, t):
    V = np.zeros((n+1, t.size)); V1 = np.zeros_like(V); V2 = np.zeros_like(V)
    for i in range(n+1):
        c = np.zeros(i+1); c[i] = 1
        V[i] = L.legval(t, c)
        if i >= 1: V1[i] = L.legval(t, L.legder(c, 1))
        if i >= 2: V2[i] = L.legval(t, L.legder(c, 2))
    return V, V1, V2
class Plate:                       # a, b [m]; D [N m]; rho_h [kg/m^2]
    def __init__(s, a, b, D, nu, rho_h, N=20):
        s.a, s.b, s.N = a, b, N; t, w = L.leggauss(2*N+4); X, X1, X2 = leg(N, t)
        I = lambda A, B, j, k: (A*w) @ B.T * j * k
        sx, sy = 2/a, 2/b
        Ex = {k: v for k, v in [((0,0), I(X,X,a/2,1)), ((2,2), I(X2,X2,a/2,sx**4)),
              ((0,2), I(X,X2,a/2,sx**2)), ((1,1), I(X1,X1,a/2,sx**2))]}
        Ey = {k: v for k, v in [((0,0), I(X,X,b/2,1)), ((2,2), I(X2,X2,b/2,sy**4)),
              ((0,2), I(X,X2,b/2,sy**2)), ((1,1), I(X1,X1,b/2,sy**2))]}
        k = np.kron
        s.K = D*(k(Ex[2,2],Ey[0,0]) + k(Ex[0,0],Ey[2,2]) + nu*(k(Ex[0,2].T,Ey[0,2]) + k(Ex[0,2],Ey[0,2].T))
                 + 2*(1-nu)*k(Ex[1,1],Ey[1,1]))
        s.M = rho_h*k(Ex[0,0], Ey[0,0]); s.C = []
    def phi(s, x, y, dx=0, dy=0):
        X = leg(s.N, np.array([2*x/s.a-1]))[dx][:,0]*(2/s.a)**dx
        Y = leg(s.N, np.array([2*y/s.b-1]))[dy][:,0]*(2/s.b)**dy
        return np.kron(X, Y)
    def mass(s, x, y, m): p = s.phi(x, y); s.M += m*np.outer(p, p)
    def overhang(s, x, m, d, I):    # rigid body at (x, 0), CM at y = -d
        p, q = s.phi(x, 0), s.phi(x, 0, dy=1); u = p - d*q
        s.M += m*np.outer(u, u) + I*np.outer(q, q)
    def support(s, x, y, clamp=False):
        s.C.append(s.phi(x, y))
        if clamp: s.C += [s.phi(x, y, dx=1), s.phi(x, y, dy=1)]
    def modes(s, n=4):
        _, sv, vt = np.linalg.svd(np.array(s.C)); Z = vt[int((sv > sv[0]*1e-10).sum()):].T
        Kr, Mr = Z.T@s.K@Z, Z.T@s.M@Z; Li = np.linalg.inv(np.linalg.cholesky(Mr))
        w2 = np.linalg.eigvalsh((Li@Kr@Li.T + (Li@Kr@Li.T).T)/2)
        return np.sqrt(w2[:n])/(2*math.pi)
```
