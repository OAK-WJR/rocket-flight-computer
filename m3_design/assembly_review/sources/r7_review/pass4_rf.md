# R7 pass 4: RF layout and coexistence review

Independent read-only review, 2026-10-17, of `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
`636a6bdc7234586a659741a3da921335a47197648c29cd9612c8374733847650` (the fix-pass-3 board; checked before and after
this review, unchanged). Schematic `47057f7d97c7d748…`, rules `m3.kicad_dru` `1674d58b…`. Dimension: RF layout and
coexistence (REQUIREMENTS F10, the RF parts of M1/M2, the RF copper against M2's clean-routing criterion, and, as
asked for this pass, pour slivers and stitching over the whole board). Vehicle-level choices and firmware are out
of scope. The pass-3 board (`7660620c…7c9c`, the copy `fx3/base.kicad_pcb` in the session scratchpad) and the
committed R6 board (`git show 3b215ba:…/m3.kicad_pcb`, `184a87e8…`) were used for before/after comparisons.

What was run:
- `tools/check.sh` (exit 0): DRC 0, unconnected 0, schematic parity 0, ERC 0; metadata/3D OK; silkscreen 0;
  R7 CAD contract OK; routing hygiene 0 failing / 42 allowlisted / 0 stale; actuator contract OK; fit OK.
  `check_r7` evidence: fence 21 vias, openings x 6.3–12.4 and 20.0–23.8; line-side gaps GNSS west 3.90, east 2.65,
  radio 1.55 / 1.55 mm; In1 missing 0.0 mm²; RF ground vias 0.16 mm from all seven RF GND pads; launch In2
  1025 / 1025 samples each; module ground 0 missing (U31 body In1/In2 2601 each, U30 keep-out In1 1976); strip GND
  reach F.Cu 3.14, B.Cu 3.49 mm; strip items F.Cu 67, B.Cu 30 tracks, 205 vias.
- `tools/test_r7_check.py` (34 OK) and `tools/test_route_check.py` (27 OK) under KiCad's Python (in-memory boards).
- KiCad 10.0.6 `pcbnew` scripts (scratchpad `p4rf/`), on copies of the board:
  - whole-board copper diff against the pass-3 board (tracks, vias, footprints with pads and zone connections,
    zones and rule areas) and an RF-strip dump (y < 28);
  - GCPW scan: lateral F.Cu GND gap every 0.05 mm along every RF segment, In1/In2 under each line;
  - launch point tests (In1 row at y 2.3, In2 and B.Cu under each launch);
  - through-copper GND reach (8-neighbour raster Dijkstra, 0.05 mm, `route_check.gnd_reach`) for the strip, the
    band y 23.5–35 and the whole board on all four layers;
  - thin-pour scan of every pour net and layer (pass-3 method, opening 0.125 mm);
  - unstitched-finger scans at width limits 0.5, 0.75 and 1.0 mm (the `route_check` finger method with a
    different width), run on this board, the pass-3 board and R6;
  - GND fill under both module bodies on all four layers; GND pad pour connections next to each trim area;
  - pad-to-via copper distances; via-spot search with the build's own `r7_route.ViaCheck`.
- A native `ZONE_FILLER` refill of a scratch copy with the project's `.kicad_pro` and `.kicad_dru` beside it: the
  XOR between saved and refilled fills is 0.0 mm² for every zone and layer, so the saved fills are current.
- A DRC trial on a scratch copy (one GND via added near the x 40 finger, refilled natively, `kicad-cli pcb drc`).
- Gerber parse of `fab/m3_gerber.zip` (`m3-F_Cu.gbr` regions) and the manifest binding.
- Maker documents: u-blox MAX-F10S integration manual §4.4; EBYTE E22-900MM22S manual §4.1 and pin table.

Coordinates: KiCad mm, y = 0 at the aft edge.

## 1. Summary

**No Critical. No Major. Three Minor (P4-RF-01 to P4-RF-03).**

All four pass-3 RF findings are closed or properly dispositioned (section 2): P3-RF-01 (the Major) is fixed and
verified on the copper, in the saved fills, in a native refill and in the fab Gerbers; P3-RF-03 and P3-RF-04 are
fixed; P3-RF-02 is recorded as open (carried forward in P4-RF-03).

Fix pass 3 changed no RF copper. No track or via of any RF or radio/GNSS-interface net moved anywhere on the board,
no footprint moved or changed, the stackup block is identical, and the GCPW gap and the In1/In2 reference measure
the same as on the pass-3 board at every sample. In the strip it added one fill keep-out (`R7_POUR_TRIM_7`, the
RXEN/BUSY sliver) and three GND stitching vias, and it removed four dead GND stubs just forward of the fence. The
strip's worst through-copper distance to a GND via fell from 18.3 mm (the sliver's tip) to 3.14 mm on F.Cu and from
4.87 to 3.49 mm on B.Cu. No sliver longer than 3 mm is left on any net or layer of the board.

The Minors are about the whole-board scope and the gates, not the RF strip:
- P4-RF-01: the gate's finger rule stops at 0.5 mm width. Wider unstitched GND fingers remain, among them one in R7
  copper, 0.7 mm wide and 17 mm of copper from a via, with no legal via spot.
- P4-RF-02: `pour_trim` now writes fill keep-outs automatically on every build, with no guard near RF copper, and
  no gate pins the GCPW's coplanar ground or the top-layer ground under the modules.
- P4-RF-03: P3-RF-02 is still open, and STATUS and R7_VALIDATION list a "D30/D31/C302 seating" bench item that
  ORDERING does not contain.

| ID | Sev. | Requirement | Finding | Evidence | Fix |
|---|---|---|---|---|---|
| P4-RF-01 | Minor | M2 ("What the gate enforces: … unstitched GND pour fingers"); owner criterion over the whole board, inherited copper included; u-blox MAX-F10S IM §4.4 p. 66 (ground stubs "avoided or ended with a via") as general guidance | **Unstitched GND fingers wider than 0.5 mm are outside the gate, and one is R7 copper.**<ul><li>`route_check.pour_finger` takes only fill pieces narrower than 0.5 mm (FINGER_W, "too narrow to hold a via"). `check_r7.rf_gnd_reach` bounds every width, but only in the strip (y ≤ 23.5).</li><li>Elsewhere, with the same method at wider limits, the final board has 20 GND pieces narrower than 0.75 mm and 48 narrower than 1.0 mm, each longer than 3 mm with a point more than 4 mm of copper from a GND via. R6 had 53 and 82, so fix pass 3 cut them.</li><li>**Worst R7-era piece:** F.Cu x 39.78–40.47, y 28.27–37.32 (plus a fork round LED2 at its aft tip), 0.695 mm wide. It sits between CAM_MCU_TX (x 39.55) and LED_YEL (x 40.7), both redrawn in fix pass 2. It is joined to the pour only at its forward end (y ≈ 38), and its aft tip (40.08, 27.38) is 17.2 mm of copper from a GND via.</li><li>`r7_route.ViaCheck` finds no legal 0.5 mm via spot inside it. It was absent on the pass-2 board (`03fe7572…`; no fill between those tracks) and present on the pass-3 board. Pass 3 scanned only the strip, so nobody saw it.</li><li>**Worst inherited piece:** F.Cu along the forward edge, 1.68 mm wide (y 115.81–117.49, x ≈ 8.6–32), ending in a patch at x 0.5–8.6 round the support hole (4, 114.4). The patch is 47.3 mm of copper from a via at (3.23, 112.33). It is the same on the pass-3 board and on R6.</li><li>RF effect is negligible (Inference). The x 40 finger is about 9 mm long, so its quarter-wave resonance is near 3 GHz; it is 8.65 mm from U31's courtyard, across the fence, beside slow nets. The forward strip is 90 mm from the radio chain, 0.2 mm over In1 and low impedance. The finding rests on M2's wording, which is broader than the tool's definition.</li></ul> | Finger scans (`p4rf/fingers_w.py`, `route_check.thin_pieces` plus `reach`): W < 0.5 mm: 0 (pass-3 board 19); W < 0.75: 20 (pass 3: 42; R6: 53); W < 1.0: 48 (R6: 82). Cross-sections of the x 40 finger: GND fill x 39.78–40.47 at y 31.5, 33, 34.5 and 36; 0.205 mm wide at y 30 beside R33.1. Whole-board reach (`p4rf/reach_all.py`): F.Cu worst 47.29 mm (3.23, 112.33); band y 23.5–28.5 worst 17.21 mm (40.08, 27.38). Via-spot search (`p4rf/viaspot.py`, ViaCheck, 0.025 mm grid, window x 39.6–41.3, y 27.2–38.5): legal spots only at x 41.275–41.3, y 27.2–27.575. A DRC trial via there (DRC clean) leaves the finger's reach unchanged, so that spot is in another fill piece. Forward strip: ViaCheck finds 5416 legal spots at 0.1 mm in x 0.5–32.5, y 112–117.5, for example (2.5, 112.4), (5.4, 112.4), (12.0, 116.6), (20.0, 116.6) and (28.0, 116.6). Pass-2 board cross-section at y 28.5–36: no fill between CAM_MCU_TX and LED_YEL. | Trim the x 40 finger with a fill keep-out, as `pour_trim` does for narrow ones (e.g. extend FINGER_W to about 0.75 mm, or add a reach test for pieces that ViaCheck cannot stitch). Stitch the forward-edge strip and patch with GND vias at the legal spots listed (about every 8 mm). Then either stitch or trim the other wide fingers, or write the width limit into M2 ("fingers narrower than 0.5 mm are gated; wider unstitched pour peninsulas are review items") and list the rest as recorded deviations for the owner. |
| P4-RF-02 | Minor | F10 (50 Ω GCPW "over unbroken ground"; no signals and ground under the modules), u-blox IM §4.4 ("ground the area below the module, on the top and second layer"), EBYTE manual §4.1; regression protection | **Automatic pour trimming can remove RF ground without any gate noticing.**<ul><li>`r7_polish.pour_trim` (l. 486–532) runs on every build after all copper stages. It turns every pour piece narrower than 0.25 mm (sliver) or 0.5 mm (unstitched finger) into a zone-fill keep-out, with no exclusion near RF nets.</li><li>If a later copper change ever leaves such a piece beside a GCPW line, the build trims the coplanar ground there. The gap would widen from 0.25 mm towards the next copper and the line would go high-impedance.</li><li>No gate would see it: DRC's "R7 RF50 coplanar gap" is a minimum only. `check_r7.rf_stitching` checks via gaps and In1, not F.Cu ground beside the line. `module_ground` checks In1/In2 under U31 and In1 under U30, not F.Cu under either module (u-blox and EBYTE both ask for top-layer ground). The only catch is TRIM_EXPECTED = 21, a count, which says nothing about where a new trim lands.</li><li>**Today nothing is wrong:** no trim lies in the RF chains; the GCPW gap re-measures as on pass 3; and F.Cu, In1 and In2 GND cover both module bodies (0 voids in 10201 and 9996 samples at 0.1 mm). The finding is about future builds.</li></ul> | `r7_polish.py` l. 486–532 (no RF test before `base.rule_area`); `check_r7.py` l. 526–549 (`MODULE_GND`: U31 In1/In2, U30 In1 only), l. 643–724 (`rf_stitching`); `m3.kicad_dru` l. 18–20 (min 0.25 mm only). GCPW scan: identical on both boards (GNSS_RF_ANT 0.26/0.26 mm, east to 0.755 by D30; GNSS_RF_IN 0.255; RADIO_RF_ANT 0.255; RADIO_RF 0.545 inside U31.6's pad clearance; pi rows 0.31). The only trim in the strip is `R7_POUR_TRIM_7` (x 20.81–21.24, y 11.24–26.75), 6.7 mm from GNSS_RF_IN copper (pads included) and 9.8 mm from RADIO_RF_ANT; the nearest other trim, `R7_POUR_TRIM_19`, is 18.8 mm from RF copper. | In `check_r7`, require F.Cu GND within about 0.40 mm of each edge of every GCPW segment at 0.05 mm steps, with the measured exceptions named (the D30 east side to 0.76 mm, U31.6's pad clearance, the launch pads). Add F.Cu to `module_ground` for both bodies. Make `pour_trim` assert that no new keep-out comes within 1 mm of RF-net copper or inside a module body. Add tests. |
| P4-RF-03 | Minor | M1/M2 assembly (pass-3 P3-RF-02, P3-DFM-05); record accuracy (AGENTS.md §3 STATUS rule) | **P3-RF-02 is still open, and two records cite a bench step that does not exist.**<ul><li>C302.2, D30.2 and D31.2 are still FULL to the pour. C302 was not returned to thermal relief.</li><li>R7_VALIDATION (P3-RF-02 and P3-DFM-05 rows, "Open after fix pass 3") correctly says the tombstone inspection is not in ORDERING.</li><li>But STATUS l. 108 ("Needs the bench … (ORDERING §5): … D30/D31/C302 seating") and R7_VALIDATION l. 446 ("Bench and physical (ORDERING §5): … D30/D31/C302 seating") list it as an ORDERING §5 step.</li><li>ORDERING inspects only D30/D31, for bridges and shift (§4 l. 93, §5 l. 137). It has no C302 item and no tombstone or seating check. A reader of STATUS would believe the step is covered.</li></ul> | pcbnew: `GetLocalZoneConnection()` = 2 (FULL) on C302.2, D30.2, D31.2. `docs/ORDERING.md` l. 93 and 137 (D30/D31 only); `STATUS.md` l. 108 and 118; `docs/R7_VALIDATION.md` l. 316, 330, 427, 446. | As P3-RF-02: return C302.2 to the house relief (it gains nothing from a solid ground behind L30), keep D30/D31 solid, and add "D30, D31, C302 seated flat (no tombstone or skew)" to ORDERING §5's first-article inspection. Until then, remove "D30/D31/C302 seating" from STATUS l. 108 and R7_VALIDATION l. 446, or mark it "not yet in ORDERING". |

## 2. Pass-3 RF findings: closure

| Pass 3 | Disposition in R7_VALIDATION | Verified on `636a6bdc…` |
|---|---|---|
| P3-RF-01 (Major; 15.2 mm F.Cu GND sliver between RADIO_RXEN and RADIO_BUSY) | Fixed: 21 `R7_POUR_TRIM` keep-outs, 3 strip vias, `pour_sliver` / `pour_finger` / `rf_gnd_reach` gated | **Closed.** See the checks below. |
| P3-RF-02 (Minor; D30.2/D31.2/C302.2 solid, tombstoning) | Not done, open | **Open, recorded.** Still FULL on all three. Carried forward as P4-RF-03 because of the STATUS / R7_VALIDATION bench-list wording. |
| P3-RF-03 (Minor; record gaps) | Fixed (record) | **Closed.** R7_VALIDATION's pass-2 RF-02 row now says "Fixed in part" with the stubs left for VNA tuning. M3_R7 §"RF strip and lines" records the J30/J31 launch-via difference and the U30.10/U30.12 via links. ORDERING §4 l. 84 makes the 0.94 mm traces part of the tuning model. |
| P3-RF-04 (Minor; check_r7 gaps) | Fixed (tools) | **Closed.** C304 is in `DNP` (`check_r7.py` l. 65), and the board has C304 dnp, excluded from BOM and position files, `rocket:C0402_DNP` (no paste). `launch_reference` passes 1025 / 1025 samples per launch; `module_ground` passes; `rf_gnd_reach` passes. Each has a failing-and-passing unit test (`test_r7_check.py` l. 377–424, 34 OK). Residual gaps: P4-RF-02. |

**P3-RF-01 checks:**
- **Copper and fills:** `R7_POUR_TRIM_7` (F.Cu, x 20.81–21.24, y 11.24–26.75) removes the fill between the lanes,
  and the thin-pour scan finds no piece there. The second sliver (SPI1_MISO/MOSI, 5.9 mm) is gone under
  `R7_POUR_TRIM_4`.
- **Whole board:** no pour piece narrower than 0.25 mm and longer than 3 mm on any net or layer; the pass-3 board
  had 6. Three short GND pieces of 2.1–2.3 mm remain, all outside the strip. No GND finger narrower than 0.5 mm has
  a point beyond 4 mm of copper from a via; the pass-3 board had 19.
- **Strip reach:** F.Cu worst 3.14 mm at (28.53, 21.23), B.Cu worst 3.49 mm at (0.53, 10.23); the pass-3 board
  had 18.30 and 4.87 mm.
- **Fills current:** the saved fills equal a native refill (XOR 0.0 mm²).
- **Fab Gerbers:** `m3-F_Cu.gbr` in the bound `m3_gerber.zip` (`3b16d03e…`, manifest bound to `636a6bdc…`) has no
  copper region at (20.9, 12 … 26); the pass-3 zip had copper at every one of those points.
- **Gates:** `route_check pour_sliver` / `pour_finger` and `check_r7.rf_gnd_reach` are in `tools/check.sh`, with
  tests. `pour_trim` is regenerated on every build and asserts its count.

Pass-3 items from other dimensions that touch the strip: P3-REQUIREMENTS-06 (Q30–Q32 in the RF-part filter) is
closed. `RF_PART` includes `Q3\d` (l. 104), and `rf_part_coverage` (l. 489–497, run from `check_contract` l. 378)
fails any part with a GNSS_/RADIO_/3V3_GNSS/3V3_RADIO pad outside the filter. The final board has none, and the
unit test with a stray part `X9` fails as it should.

No pass-3 Critical was in this dimension.

## 3. Measurements on the final board

### 3.1 What fix pass 3 changed (pass-3 board → final)

**Whole board:**
- 176 tracks removed and 66 added; 37 vias removed and 22 added.
- **None of them is on an RF or radio/GNSS-interface net**, i.e. `^(RADIO_|GNSS_|3V3_RADIO|3V3_GNSS)`.
- 0 footprints changed (position, rotation, side, library ID, attributes, pad nets, pad zone connections).
- Zones: only the 21 `R7_POUR_TRIM_n` rule areas added; no zone outline or setting changed.
- The KiCad stackup block is byte-identical.

**Strip and band (items with y < 28):**
- **GND vias added** (0.5/0.3 mm, tented):
  - (11.975, 21.575): 0.266 mm from C301.1 and 0.345 mm from C300.1 (3V3_GNSS bypass), 0.235 mm from a 3V3_GNSS
    track. Its ring overlaps U30's courtyard edge (y 21.39) by 0.065 mm. No U30 pad is nearer than 0.727 mm (U30.6).
  - (9.025, 8.325): 0.18 mm from the GNSS_ANT_DC B.Cu diagonal; U30.15 is 0.725 mm away.
  - (25.025, 8.525): 0.20 mm from RXEN (F.Cu) and from TXEN (B.Cu). It is inside U31's courtyard (y ≥ 8.11) but
    0.475 mm aft of the module body (ring 0.225 mm clear of y 9.0), and no U31 pad is within 1.2 mm.
  - All three: DRC clean, hole-to-hole ≥ 1.08 mm. None lies on an RF line's side, so the line-side gaps are
    unchanged.
- **GND tracks removed** (dead stubs ending in a pour): B.Cu (30.80, 27.38)–(32.09, 28.67), (32.2, 27.03)–(32.2,
  28.12) and (32.59, 28.12)–(33.03, 27.68), all at R105.2; F.Cu (38.3, 27.65)–(38.3, 28.32) at LED1.1. None is an RF
  ground.
- **Rule areas added:** `R7_POUR_TRIM_7` (above) and `R7_POUR_TRIM_19` (B.Cu, x 0.48–0.99, y 25.17–52.94: the
  edge-side GND finger beside GNSS_RESET_N in the corridor; the lanes keep In2 GND under them).
- No new aggressor copper between the strip and y 35. The changes there are dead 3V3 In2 runs removed at L1, one
  RAW_PROTECTED corner redrawn at (14.5–15.7, 31.2–32.4), GND tracks, and the GND via (35.5, 29.4).

### 3.2 GCPW gap and reference (every 0.05 mm along each RF segment)

Identical to the pass-3 board at every sample:

| Segment | F.Cu GND gap, min (each side) | In1 under centre and ±0.45 mm | In2 |
|---|---|---|---|
| GNSS_RF_ANT x 12.85 | 0.26 / 0.26 mm (east to 0.755 beside D30) | present for y > 4.6; absent in the cut-out by design | present |
| GNSS_RF_IN x 13.71 | 0.255 / 0.255 | present | present |
| RADIO_RF_ANT x 31.54 | 0.255 / 0.255 | present for y > 4.6 | present |
| RADIO_RF x 32.40 | 0.545 / 0.545 (U31.6 pad clearance) | present | present |
| Pi-row stubs (y 7.13 / 7.6) | 0.31 mm | present | present |

### 3.3 Launches, stitching, fence

- **In1 at y 2.3:** the row is identical: absent across x 11.95–13.70 and 30.64–32.39 only.
- **In2 under each launch** (axis ±1.0 mm, y 0.6–4.8): one missing point, (11.85, 4.8), in the GNSS_ANT_DC via
  antipad outside the cut-out, as before. `launch_reference`: 1025 / 1025.
- **B.Cu under both centre pads:** complete.
- **Fence:** 21 vias at y 23.3, openings x 6.3–12.4 and 20.0–23.8; line-side gaps 3.90 / 2.65 / 1.55 / 1.55 mm.
  All unchanged.
- **RF ground pads:** via 0.16 mm from D30.2, D31.2, C302.2, C303.2, C305.2, C313.2 and C314.2, unchanged.

### 3.4 Ground under the modules (0.1 mm samples; a void is a point with no GND fill more than 0.35 mm from other copper)

| Body | F.Cu | In1 | In2 | B.Cu |
|---|---|---|---|---|
| U31, x 24.86–34.86, y 9.0–19.0 | 0 / 10201 | 0 | 0 | 0 |
| U30, x 5.56–15.26, y 9.9–20.0 | 0 / 9996 | 0 | 0 | 2 at (5.56/5.66, 13.6), body edge, limiter copper |

### 3.5 GND reach (through copper to the nearest GND via or plated GND hole)

| Region | Final board | Pass-3 board |
|---|---|---|
| Strip y ≤ 23.5, F.Cu | 3.14 mm (28.53, 21.23) | 15.05 (sliver) |
| Strip, B.Cu | 3.49 (0.53, 10.23) | 4.87 (6.58, 10.43) |
| Strip, In1 / In2 | 3.49 / 3.49 | 3.54 / 3.54 |
| Band y 23.5–28.5, F.Cu | 17.21 (40.08, 27.38), the x 40 finger (P4-RF-01) | 18.30 (sliver tip), then 17.21 |
| Band, B.Cu | 6.22 (22.98, 25.28), a 9.4 mm B.Cu bridge joined at both ends | same |
| Whole board, F.Cu | 47.29 (3.23, 112.33), forward edge (P4-RF-01) | same |
| Whole board, B.Cu | 19.52 (20.13, 98.03) | 22.02 (22.23, 86.43) |

Every F.Cu and B.Cu GND fill piece on the final board (43 and 39 pieces) contains at least one GND via or plated
GND hole.

### 3.6 Part order, keep-outs and distances

- **Chains:** order and positions unchanged (no footprint changed). `U30_KEEPOUT`, both `U31_KEEPOUT` areas and the
  two launch cut-outs are unchanged, and DRC passes.
- **Distances** carried from pass 3 (nothing moved): every RF part ≥ 5.87 mm from the bucks, MCU and crystal;
  nearest RF-chain copper 15.45 mm apart; jacks 18.69 mm apart.
- **Pin contract:** U31.19 (DIO2) is on RADIO_TXEN with U31.9 (TXEN), as EBYTE allows ("DIO2 can be connected
  with TXEN", manual pin table). That is why RADIO_TXEN goes round the module, an allowlisted detour.

### 3.7 Trim side effects on GND pads (outside RF; noted)

`R7_POUR_TRIM_8`, `_11` and `_21` removed every B.Cu pour spoke of C150.2, C7.2, R64.2, C31.2 and C30.2. Each pad
still reaches GND through its tracks: C7.2 through 1.8 mm of 0.5 mm track to U2.4 and the via (19.5, 35.2).

The copper distance from each pad to the nearest GND via is unchanged within 0.04 mm (C7.2 0.85, C150.2 3.73,
R64.2 6.35, C31.2 7.64, C30.2 8.94 mm; pass-3 board 0.85 / 3.69 / 6.32 / 7.62 / 8.92). The spokes led into dead-end
fill, so nothing electrical changed.

The `pour_trim` docstring's "nothing else of any fill changes" holds for connectivity (pad groups), not for pad
spokes.

## 4. Inferences (not measured, or not from a primary source)

- **P4-RF-01 magnitudes:**
  - x 40 finger: quarter-wave resonance near 3 GHz, from about 9 mm of length and εeff ≈ 3.3.
  - Forward-edge strip: about 10 Ω, roughly 40–47 mm of path, first quarter-wave near 0.9–1.0 GHz. It is weakly
    coupled: 0.2 mm over solid In1 and about 90 mm from the radio chain. The F10 pyro-immunity bench test covers the
    system outcome.
  - Neither was modelled in 3-D.
- **P4-RF-02:** the impedance rise from losing coplanar ground (towards about 60 Ω with only the In1 reference)
  is a rule-of-thumb estimate, not a solve.
- **Coupling and isolation figures:** carried from pass 2 and pass 3, not recomputed (no RF copper changed).

## 5. Outside this dimension (noted, not graded)

- **C30/C31 (3V3A bypass at the barometer):** their B.Cu GND pads are 7.6–8.9 mm of copper from the nearest GND
  via, the same on R6 (inherited). For the electrical reviewers.
- **Trimmed pad spokes:** section 3.7. No electrical change; the records could mention it beside the 21 keep-outs.

## 6. Sources

- **u-blox MAX-F10S integration manual** UBXDOC-963802114-12892 R01, §4.4 "Layout", p. 66–67:
  - "Any stubs at the ground planes must be avoided or ended with a via to the reference ground";
  - "It is recommended to ground the area below the module, on the top and second layer";
  - CPW with ground on the second layer.
  - https://content.u-blox.com/sites/default/files/documents/MAX-F10S_IntegrationManual_UBXDOC-963802114-12892.pdf
- **EBYTE E22-900MM22S user manual** (via LCSC):
  - §4.1 hardware design (no high-frequency wiring under the module; top layer grounded);
  - pin table: pin 9 TXEN ("microcontroller IO or DIO2"), pin 19 DIO2;
  - "DIO2 can be connected with TXEN".
  - https://datasheet.lcsc.com/datasheet/pdf/70331b0eaf0eedaea0129e9e66d9a011.pdf?productCode=C5333985
- **Project:**
  - `docs/REQUIREMENTS.md` F10, M2; `docs/M3_R7.md` §"RF chains", §"RF strip and lines"; `docs/R7_VALIDATION.md`
    (pass-3 table, "Open after fix pass 3"); `docs/ORDERING.md` §4, §5; `STATUS.md`;
  - `m3.kicad_dru` (R7 RF rules, keep-out rules);
  - `tools/check_r7.py` l. 65, 104–107, 434–569, 643–724; `tools/route_check.py` l. 59–66, 107–110, 901–991;
  - `m3_design/r7_polish.py` l. 480–592;
  - `fix3_F4_handoff.md`, `fix3_docs_handoff.md`; `pass3_rf.md`, `pass3_verdicts.json`.

## 7. Method (reproduction)

All scripts ran under KiCad's Python (`PYTHONDONTWRITEBYTECODE=1`) against copies of the board in the session
scratchpad (`p4rf/`). Nothing in the repository was written except this report; the board's SHA-256 was the same
before and after.

- **Diffs** (`fulldiff.py`, `fpdiff.py`, `zonediff.py`, `dump.py`): sets of tracks (net, layer, sorted ends,
  width), vias, footprints with pad nets and zone connections, zones and rule areas with outlines and settings, for
  the pass-3 board and the final board.
- **GCPW** (`cpw.py`, from pass 3): at each 0.05 mm step along every RF segment, step outward in 5 µm increments
  until F.Cu GND copper is hit; point-test In1/In2 GND at the centre and ±0.45 mm. **Launch:** `launch.py`.
- **Reach** (`reach_all.py`, `reach_region.py`, `png.py` for maps): `route_check.gnd_reach` with windows covering
  the region plus at least 30 mm.
- **Thin pour** (`thin_all.py`): per net and layer, fill minus (fill deflated 0.125 mm, re-inflated 0.135 mm);
  pieces longer than 2 mm and larger than 0.1 mm² listed.
- **Fingers** (`fingers_w.py`): `route_check.thin_pieces(fill, W/2)`, length > 3 mm, then `route_check.reach` from
  every GND via and plated GND hole over the piece's box plus 4.5 mm; listed when a piece point is unreached or
  farther than 4 mm. Run at W = 0.5, 0.75 and 1.0 mm on the final, pass-3 and R6 boards.
- **Refill currency** (`refill_cmp.py`): copy the board with `m3.kicad_pro` and `m3.kicad_dru`, run `ZONE_FILLER`
  on all zones, then XOR each zone's fill per layer with the saved one.
- **Gerbers** (`gbr_regions.py`): parse the G36/G37 regions of `m3-F_Cu.gbr` (Gerber Y = −y) and point-test.
- **Via spots** (`viaspot.py`): `r7_route.ViaCheck(b).ok(p, 0.5)` at every 0.025 mm point inside the GND fill of
  the window. DRC trial: one GND via added to a scratch copy, refilled natively, `kicad-cli pcb drc`.
- **Module ground** (`under.py`), **pad spokes** (`padconn.py`), **pad-to-via copper** (`padreach.py`).
- **Gate:** `KICAD_CLI=… tools/check.sh` exit 0; `test_r7_check` 34 OK; `test_route_check` 27 OK.
