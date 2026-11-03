# R7 pass 3: RF layout and coexistence review

Independent read-only review, 2026-10-17, of `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
`7660620cfa834e4d381d2a2638780e9a341341c9b93c6e6f526791204dc77c9c` (the final pass-2-fix board; checked before and
after this review, unchanged). Schematic `47057f7d97c7d748…`. Dimension: RF layout and coexistence (REQUIREMENTS
F10, the RF parts of M1/M2, and the RF copper against M2's clean-routing criterion). Vehicle-level choices and
firmware are out of scope. The pass-2 board (`03fe7572…6d54`, a reference copy in the pass-2 reviewers' scratchpad)
was used for before/after comparisons.

What was run:
- `tools/check.sh` (exit 0): DRC 0, unconnected 0, schematic parity 0, ERC 0; metadata/3D OK; silkscreen 0;
  R7 CAD contract OK; routing hygiene 0 failing / 20 allowlisted / 0 stale; actuator contract OK; fit OK.
  `check_r7` evidence: fence 21 vias, openings x 6.3–12.4 and 20.0–23.8; line-side gaps GNSS west 3.90, east 2.65,
  radio 1.55 / 1.55 mm; In1 missing 0.0 mm²; RF ground vias 0.16 mm from all seven RF GND pads.
- `tools/route_check.py --report` (RF and RF-interface instances read individually).
- KiCad 10.0.6 `pcbnew` scripts on the board and on the pass-2 board: strip copper diff (tracks, vias, pads,
  footprints, zones and rule areas, y < 26 mm); lateral GND gap and In1/In2 presence every 0.05 mm along every RF
  segment; launch In1/In2/B.Cu point tests; stitching per side in path order; F.Cu/B.Cu GND lattice voids;
  through-copper (geodesic) distance from module/RF GND pads and from every strip GND copper point to the nearest
  GND via; thin-pour scan (filled GND narrower than 0.25 mm); courtyard and net-copper distances.
- A native `ZONE_FILLER` refill of a scratch copy (fills identical in the area of P3-RF-01, so the saved fills are
  current).
- A DRC trial on a scratch copy (three RADIO_TXEN test tracks added) to prove the new U31 body keep-out works.
- Gerber parse of `fab/m3_gerber.zip` (paste layers) and the fab manifest binding.
- Maker documents: u-blox MAX-F10S integration manual §4.4; EBYTE E22-900MM22S manual §4.1; JLCPCB capabilities
  page (section 6).

Coordinates: KiCad mm, y = 0 at the aft edge.

## 1. Summary

**No Critical. One Major (P3-RF-01, a regression from the fix pass). Three Minor (P3-RF-02 to P3-RF-04).**

All five pass-2 RF findings are closed or properly dispositioned (section 2). The RF lines, launches, stackup,
In1/In2 reference, chain order, part positions on the chains, the fence and the line-side stitching are unchanged
from the pass-2 board and re-measure the same (section 3). The fix pass improved the RF grounds (pad-to-via copper
path 0.196–0.221 mm on all seven RF GND pads, was 0.325–0.914 mm), moved the antenna DC feed out from under the GNSS
line, and the new U31 body keep-out demonstrably catches B.Cu and In2 copper under the module.

The Major is new copper hygiene in the strip, created by the RQ-10 width change: a 15.2 mm long, 0.15 mm wide
F.Cu GND pour sliver between RADIO_RXEN and RADIO_BUSY, grounded at its aft end only and carrying no via. u-blox
says ground stubs "must be avoided or ended with a via", and M2 forbids stubs. Its RF effect is small (Inference);
the Major rests on the requirement prong, and no gate catches pour slivers.

| ID | Sev. | Requirement | Finding | Evidence | Fix |
|---|---|---|---|---|---|
| P3-RF-01 | Major | M2 / AGENTS.md §3 ("no … stubs"; clean copper, owner criterion); u-blox MAX-F10S IM §4.4 p. 66 ("Any stubs at the ground planes must be avoided or ended with a via to the reference ground. Otherwise, they could pick up and propagate interference.") | **New 15.2 mm open-ended F.Cu GND sliver, no via, between the two modules.**<ul><li>Filled GND_F copper 0.15 mm wide at x 20.83–20.97 from y ≈ 11.6 to ≈ 26.8, between RADIO_RXEN (F.Cu x 20.6, 0.15 mm) and RADIO_BUSY (F.Cu x 21.2, 0.15 mm), 0.155 mm from each.</li><li>It joins the pour only at its aft end (y ≈ 11.4, where BUSY turns east to U31.11 at y 11.46). The forward end is open at y ≈ 26.8, cut off by the clearance round RXEN's via (20.6, 27.05). Nothing on it is a via (it is too narrow for one); the nearest GND vias, (20.0, 15.0/19.0/23.3), are across RXEN.</li><li>It runs alongside U30's east side (5.4 mm from the body), crosses the strip fence through the radio-lane opening (x 20.0–23.8) and ends in the band.</li><li>**Regression:** absent on the pass-2 board. RQ-10 narrowed the lanes 0.2 → 0.15 mm (fix2_F1 §2), so the 0.6 mm RXEN–BUSY pitch now leaves 0.45 mm = 2 × 0.15 mm zone clearance + the 0.15 mm GND_F minimum width. With 0.2 mm lanes the gap was 0.40 mm and no copper filled.</li><li>No gate sees it: DRC passes (legal copper), `route_check` ignores pour fills, `check_r7` checks only via pitch. It is the longest sub-0.25 mm GND piece on the board (scan, section 3.9).</li><li>Magnitude (Inference): a microstrip about 0.15 mm wide, 0.203 mm over solid In1, shorted at one end, is 0.09 λg at 915 MHz and 0.16 λg at 1.575 GHz, with its first quarter-wave resonance near 2.8 GHz. Its only drivers are the slow RXEN/BUSY lines it hugs. A measurable RF effect is unlikely; the finding is the stated rule, not a predicted failure.</li></ul> | pcbnew on the saved fills and on a natively refilled scratch copy: F.Cu GND present at x 20.83–20.97 for y 12.0 … 26.5 (sampled every 0.5–1 mm), absent at y 26.9 and y 27.0 in x 20.4–21.4; 0.58 mm wide at y ≤ 11.0. Zone `GND_F`: min width 0.15 mm, clearance 0.15 mm. Tracks: RADIO_RXEN (20.6, 27.05)→(20.6, 8.3) 0.15 mm; RADIO_BUSY (21.2, 27.7)→(21.2, 11.76) 0.15 mm. Thin-pour scan (filled GND minus its 0.125 mm opening): F.Cu piece 15.2 mm, bbox (20.83, 11.56)–(21.01, 26.73), 2.25 mm²; no such piece on `03fe7572…`. Through-copper distance to the nearest GND via: 18.28 mm at the open end (20.85, 26.7), only 1.13 mm away in a straight line; the next-worst F.Cu point in the strip is 4.99 mm (section 3.9). | Stop the fill between the two lanes: an F.Cu zone-fill keep-out rule area over x 20.68–21.12, y 11.5–27.1 (built in `r7_route.py`/`r7_rework.py`), or move one lane 0.05 mm, or give GND_F a 0.2 mm minimum width (then recheck every other fill). Add a strip check to `check_r7`: every F.Cu/B.Cu GND copper point in the strip within, say, 4 mm of a GND via **through copper** (section 3.9 gives the method). Re-run the thin-pour scan on the whole board: the same scan finds a second new 5.9 mm sliver outside the strip (section 5). |
| P3-RF-02 | Minor | M1/M2 (assembly), F10 (ESD at each jack, bias tee) | **The RF-02 fix made three fitted small parts thermally asymmetric.**<ul><li>D30.2, D31.2 (ESD103, TSLP-2-20, 0.35 × 0.6 mm pads) and C302.2 (0402, 10 nF bias-tee capacitor) now connect solid to the F.Cu pour, with a GND via 0.16 mm away. Their other pads sit on 0.30 / 0.25 mm traces.</li><li>`check_r7.thermal_policy` exempts them from the house small-pad relief rule (lines 673–674). No assembly assessment is recorded.</li><li>Inference (general SMT practice, no maker figure): an 0402-class part with one pad in a plane is the classic tombstoning case.</li><li>Consequences are mild. The RF line runs under D30.1/D31.1 as one segment, so a lifted diode leaves the line intact and only loses the ESD clamp. A lifted C302 leaves L30's cold end unbypassed.</li><li>ORDERING §5 already inspects D30/D31 beside the centre pads; C302 is not named.</li></ul> | pcbnew `GetLocalZoneConnection()` = FULL (2) on D30.2, D31.2, C302.2 (pass-2 board: THERMAL); paste apertures 2 per part in `m3-F_Paste.gbr` (D30 (12.845/13.505, 5.2), D31 (31.535/32.195, 5.2), C302 (11.0/10.16, 6.18)); `check_r7.py` l. 656–681. | C302 gains nothing RF-wise from a solid ground (L30 > 500 Ω sits ahead of it), so return C302.2 to the house relief and drop it from `RF_SOLID_GND`. Keep D30/D31 solid (the clamp inductance matters), and add "D30, D31, C302 seated flat (no tombstone or skew)" to the first-article inspection in ORDERING §5. |
| P3-RF-03 | Minor | Record accuracy (AGENTS.md §3 STATUS rule; R7_VALIDATION) | **Three fix-pass changes in the strip are not, or not fully, recorded.**<ul><li>**RF-02 is marked "Fixed".** Its third part, abutting each shunt land to its series pad, was not done: the 0.94 mm stubs C303.1→12.85, C305.1→13.71, C313.1→31.54 and C314.1→32.40 (y 7.13 / 7.6) are unchanged. RF-02 said to include them when tuning on the VNA; ORDERING §5 does not.</li><li>**One J30 launch via was dropped.** The via at (14.10, 4.15) disappeared when D30.2's via went in at (14.05, 4.65). J31 kept its (32.79, 4.15) and gained (32.79, 4.75), so the two launch patterns now differ. RF effect nil (east gap ≤ 1.08 mm, Inference); unrecorded.</li><li>**U30.10/U30.12 lost their direct via links.** Pass 2 had 0.225 mm of copper from each pad to a via. Now it is 0.575 / 0.775 mm: DFM-07 removed (12.86, 8.83) and (14.56, 8.83), and `r7_hygiene` near_dup removed the pad-to-via tracks (12.61/14.81, 10.2 → 8.3). The pour now carries the joint. M3_R7 records only the two vias. RF effect negligible (about 0.1–0.2 nH, Inference).</li></ul> | Strip diff, pass-2 → final (vias removed (14.1, 4.15), (12.86, 8.83), (14.56, 8.83); F.Cu GND tracks removed (12.61, 10.2)–(12.61, 8.3) and (14.81, 10.2)–(14.81, 8.3)); through-copper pad-to-via distances (section 3.6); R7_VALIDATION RF-02 row; fix2_F1 §2 "RF-02 / DFM-07". | R7_VALIDATION RF-02: "Fixed (solid grounds, vias); shunt stubs unchanged, include them in VNA tuning". Add a line to ORDERING §5's RF match step. Note both strip removals in M3_R7 §"RF strip and lines". No copper change needed. |
| P3-RF-04 | Minor | F10 regression protection (pass-2 RF-05 follow-through) | **`check_r7` still has gaps in the RF geometry it pins.**<ul><li>C304's DNP / exclude-from-BOM / exclude-from-position flags are not in its DNP contract: `DNP = ('C303', 'C305', 'C313', 'C314')` at l. 64, used at l. 360. `dnp_paste` only looks at parts that already carry both flags.</li><li>In2 GND under the two launch cut-outs is not checked, and it is the launch's only reference there. It is present today, with 1 missing point at (11.85, 4.8) in the GNSS_ANT_DC via antipad, outside the cut-out.</li><li>No check bounds unstitched GND copper in the strip, which is how P3-RF-01 got through.</li></ul> | `tools/check_r7.py` l. 64, 360–364, 426–478, 553–634; launch point test (section 3.3). | Add C304 to the DNP contract; add an In2-GND-under-launch area test (cut-out +0.3 mm); add the through-copper stub check of P3-RF-01, with tests. |

## 2. Pass-2 RF findings: closure

| Pass 2 | Disposition in R7_VALIDATION | Verified on `7660620c…` |
|---|---|---|
| RF-01 (paste on DNP shunts) | Fixed | **Closed.** `rocket:C0402_DNP` differs from `C0402` only in name, description, UUIDs and the two pads' missing `F.Paste` (file diff). `m3-F_Paste.gbr`: 0 flashes at C303/C304/C305/C313/C314; 2 each at R304, R316, D30, D31, C302 and L30; 0 at J30/J31 (B_Paste: none). Manifest binds `7660620c…` and `m3_gerber.zip` (`febe979b…`). |
| RF-02 (RF ground parasitics) | Fixed | **Closed for grounds and vias:** FULL connection and a via 0.16 mm from the pad edge on D30.2, D31.2, C302.2, C303.2, C305.2, C313.2 and C314.2. The through-copper pad-to-via path is 0.196–0.221 mm (pass 2: 0.325–0.914 mm). **Record gap:** the shunt stubs are unchanged (P3-RF-03); assembly side effect (P3-RF-02). |
| RF-03 (stitching record) | Accepted, documented | **Closed.** Re-measured on the final board, identical to pass 2: GNSS west 4.27 mm ((11.60, 4.15)→(12.61, 8.30)), GNSS east 2.18, radio west 3.68 ((30.69, 6.75)→(31.13, 10.40)), radio east 1.85 mm. F10 and M3_R7 carry both methods and the λ/20 reasoning (λ_FR4/20 = 4.44 mm at 1.61 GHz). |
| RF-04 (F10 strip wording) | Documented | **Closed.** F10's "What the strip may hold" matches the copper (`check_r7.rf_strip` OK: F.Cu 67, B.Cu 30 tracks, 202 vias, all on allowed nets; In1/In2 GND only). C304 (GNSS_ANT_GATE, B.Cu) falls under "the antenna-bias limiter … on B.Cu under U30". |
| RF-05 (regression checks, U31 keep-out) | Fixed | **Closed** (residual gaps in P3-RF-04). The second `U31_KEEPOUT` covers 24.86–34.86 × 9.0–19.0 on In2 and B.Cu. DRC trial on a scratch copy: RADIO_TXEN tracks added on B.Cu (25.2, 12–13), on B.Cu (30–31, 18.6) and on In2 (34.5, 12–13) were each flagged "Items not allowed (rule 'R7 U31 keep-out')". `rf_stitching` gates fence pitch, line-side gaps and In1. |

Pass-2 items from other dimensions that touch the strip:
- **DFM-07:** the two vias under U30's paste extensions are gone; side effect in P3-RF-03.
- **ELECTRICAL-01:** C304 (`C0402_DNP`) sits on B.Cu at (7.74, 16.9). Pad 1 is fed straight from R302.1 by a 1.15 mm 0.20 mm track; pad 2 is on GND with a thermal relief and a GND via 0.84 mm away. It is dnp, out of the BOM and position files, and has no paste.
- **RQ-12:** RXEN now leaves pad 10 along y 8.0, aft of U31 (body y ≥ 9.0). Its track is about 2.95 mm from RADIO_RF_ANT copper (C313.1); pad 10 itself is 2.6 mm away, as before. It is 5.70 mm from GNSS RF copper (pass 2: 5.92 mm).

No pass-2 Critical or Major was in this dimension.

## 3. Measurements on the final board

### 3.1 What changed in the strip (pass-2 board → final, y < 26 mm)

- **RF tracks: identical.** 8 segments of 0.30 mm on F.Cu: GNSS (12.85, 2.3)→(12.85, 7.13), stub to 11.91;
  (13.71, 7.13)→(13.71, 10.2), stub to 14.65. Radio (31.54, 2.3)→(31.54, 7.6), stub to 30.60; (32.40, 7.6)→(32.40, 9.05),
  stub to 33.34. The KiCad stackup block is byte-identical (JLC041611-7628); the job file still says M3-ASSY-R7.
- **RF parts on the chains:** positions unchanged. C303/C305/C313/C314 swapped to `C0402_DNP`.
- **Limiter** (Q30–Q32, R300–R303) re-placed on B.Cu under U30, and C304 added.
  - GNSS_ANT_DC now runs (11.45, 5.15)→(5.85, 10.75)→Q30.3 on B.Cu, away from the GNSS line. On the pass-2 board
    it ran under the line at x 13.55.
  - The B.Cu diagonal clears the C303.2 via by about 0.2 mm (DRC-legal).
- **C311/C312** moved 0.2 mm east, onto C310.1's axis; 3V3_RADIO widened to 0.4 mm.
- **Interface lanes** in the strip went from 0.20 to 0.15 mm, the cause of P3-RF-01.
- **GND vias.**
  - Removed: (14.1, 4.15), (10.0, 7.0), (28.0, 7.0), (36.0, 7.0), (12.86, 8.83), (14.56, 8.83), and the old limiter-area
    lattice (4.0, 11.0), (9, 13), (13, 13), (10, 15), (7, 17).
  - Added: the seven RF ground vias; (28.19, 7.2), (23.0, 9.0), (23.2, 14.67), (23.8, 17.7), (31.73, 20.55),
    (33.0, 20.55); and lattice (7, 13), (11, 13), (8, 15), (9, 17), (7.66, 23.55), (9.61, 25.0).
  - Strip GND vias: 187 → 194.
- **F.Cu GND tracks removed** (pour now carries these joints): U30.10/U30.12 → (14.81/12.61, 8.3); U31.7 → (31.13, 10.4);
  U31.2 → (33.6, 15.27); U31.16 → (27.32, 17.6); C310.2 → (38.78, 20.85).
- **Rule areas:** a second `U31_KEEPOUT` (In2, B.Cu). The launch cut-outs `R7_J30/J31_launch_In1` (11.95–13.75 /
  30.64–32.44 × 0–4.6, In1, no fill) are unchanged.

### 3.2 GCPW gap and reference (every 0.05 mm along each RF segment)

| Segment | F.Cu GND gap, min (each side) | In1 under centre and ±0.45 mm | In2 |
|---|---|---|---|
| GNSS_RF_ANT x 12.85 | 0.26 / 0.26 mm | present for y > 4.6; absent in the cut-out by design | present |
| GNSS_RF_IN x 13.71 | 0.255 / 0.255 | present | present |
| RADIO_RF_ANT x 31.54 | 0.255 / 0.255 | present for y > 4.6 | present |
| RADIO_RF x 32.40 | 0.545 / 0.545 (inside U31.6's pad clearance) | present | present |
| Pi-row stubs (y 7.13 / 7.6) | 0.31 mm | present | present |

These are the same values as on the pass-2 board, except on the GNSS_RF_ANT east side, which now reads 0.26–0.755 mm
(pass 2: 0.325–0.925 mm): D30.2's solid connection brought pour closer beside the diode. The line therefore still solves
to 50.3 Ω coated (pass2_rf §3.2; no geometry change).

### 3.3 Launches

- **In1 at y 2.3** is absent across exactly the cut-out, x 11.95–13.70 and 30.64–32.39 (0.05 mm sampling), and
  present outside it.
- **In2 GND under each launch** (axis ±1.0 mm, y 0.6–4.8) is present except one point, (11.85, 4.8). That point
  is inside the antipad of the GNSS_ANT_DC via (11.45, 5.15), outside the cut-out, and was on pass 2 too.
- **B.Cu GND** lies under both centre pads (±0.6 mm).
- **Launch stitching:**
  - J30 keeps (11.4/14.3, 1.0/2.3/3.6) and (11.60, 4.15). Its east (14.10, 4.15) is replaced by D30.2's
    (14.05, 4.65).
  - J31 keeps all eight and gains (32.79, 4.75).
  - Leg pads and the 1.2 × 4.2 mm centre pad are unchanged.

### 3.4 Stitching beside the lines and the fence

- **Continuous via-to-via gaps** (GND vias within 2 mm of the line, pass-2 method): GNSS west 4.27, east 2.18;
  radio west 3.68, east 1.85 mm. All are unchanged.
  - GNSS line, east side: (14.05, 4.65), 1.20 mm from the line, replaces the launch via (14.10, 4.15).
  - The other new RF ground vias are 2.1–3.1 mm from the line centres, so they do not count as line-side vias.
- **Fence at y 23.3:** 21 vias at 1.4–2.0 mm pitch, openings x 6.3–12.4 and 20.0–23.8, as on pass 2.
- **Via hole spacing:** the closest strip pairs are 0.285 mm hole to hole (same net), and GND to signal pairs
  0.421 mm. JLC's via hole-to-hole minimum is 0.2 mm (capabilities page); the board rule is 0.25 mm.

### 3.5 GND lattice

The farthest filled-GND point in the strip from any GND via (Euclidean):

| Layer | Pass-2 board | Final board | Location (final) |
|---|---|---|---|
| F.Cu | 3.81 mm | 3.48 mm | (9.8, 20.8), among U30's forward escapes |
| B.Cu | 3.88 mm | 3.64 mm | (9.8, 20.6) |

The lattice improved slightly despite the removed vias. The Euclidean metric cannot see a thin finger next to a
via across a track, which is the shape of P3-RF-01; section 3.9 covers that case.

### 3.6 Module and RF ground pads: copper path to the nearest GND via (F.Cu, through-copper raster 0.025 mm)

| Pad | Pass 2 | Final | | Pad | Pass 2 | Final |
|---|---|---|---|---|---|---|
| U30.10 (GND beside RF_IN) | 0.225 | **0.575** | | D30.2 | 0.331 | 0.196 |
| U30.12 (GND beside RF_IN) | 0.225 | **0.775** | | D31.2 | 0.346 | 0.196 |
| U30.1 | 0.85 | 0.85 | | C302.2 | 0.325 | 0.221 |
| U31.7 (GND beside ANT) | 0.35 | 0.35 | | C303.2 / C305.2 | 0.575 / 0.629 | 0.200 / 0.221 |
| U31.2 / U31.16 | 0.20 / 0.35 | 0.20 / 0.35 | | C313.2 / C314.2 | 0.914 / 0.497 | 0.221 / 0.221 |
| J30/J31 legs (F.Cu) | 0.25 | 0.25 | | C310.2 / C311.2 / C312.2 | 0.33 / 1.17 / 1.20 | 0.33 / 0.97 / 1.00 |
| C300.2 / C301.2 | 3.32 / 1.09 | 1.82 / 1.09 | | | | |

### 3.7 Keep-outs and distances

- **Courtyard to courtyard, RF parts to U2/L1/C5–C9/U7/U8/L3/C72–C77/R71/R72/TP71/U1/U3/Y1:** FB30–C6 5.87,
  C301–C6 6.99, U30–C6 7.19, C300–C6 7.20, U31–C6 9.09, FB31–U3 9.90 mm. F10's 5 mm is met.
- **Aggressor copper:** no SW_NODE, BST, CAM_SW/BST/FB, QSPI, SPI1, SWD, USB, HSE or IMU_CS copper within 10 mm of
  U30, U31 or either RF line.
- **Radio lines to U30's body** (DS Table 21 rectangle 5.36–15.46 × 10.10–19.80):

  | Line | To U30's body | To GNSS RF copper |
  |---|---|---|
  | DIO1 | 4.88 mm | 13.3 mm |
  | RXEN | 5.07 mm | 5.70 mm |
  | NRST | 5.63 mm | 14.0 mm |
  | BUSY | 5.67 mm | 7.05 mm |
  | SPI | ≥ 6.07 mm | ≥ 7.66 mm |

- **Radio lines to U30's courtyard:** DIO1 3.1 (via), NRST 3.87, RXEN 4.17, BUSY 4.77 mm, matching M3_R7's
  3.06 / 3.82 / 4.14 / 4.74 within the bisection step.
- **Under the modules:**
  - DRC keeps non-GND copper out of `U30_KEEPOUT` (F.Cu/In1) and of both `U31_KEEPOUT` areas (proved by the
    trial in section 2).
  - RXEN along y 8.0 passes 0.225 mm aft of U31's aft pad row, outside the body.
  - TXEN's B.Cu loop is 0.29 mm outside the body.

### 3.8 Radio-to-GNSS coupling paths on the board

Coupling is unchanged from pass2_rf §3.11 in substance. The fix pass changed four things:
- **RXEN:** it now runs aft of U31 along y 8.0, then up x 20.6 as before. Its approach to GNSS RF copper went from
  5.92 to 5.70 mm; its track is about 2.95 mm from the radio's own pi-row land. It is static during TX and RX.
- **Bias feed:** GNSS_ANT_DC no longer crosses under the GNSS line on B.Cu. This removes a DC-feed/RF-line overlap
  behind two planes (improvement).
- **Radio supply:** 3V3_RADIO is 0.4 mm. FB31 is fed from its own In2 3V3 lobe (13.6 mΩ from L1.2, per fix2_F3 §4; not re-solved here). The two
  modules still share only the 3V3 plane, behind separate ferrites and local capacitors.
- **New copper between the modules:** the P3-RF-01 sliver. It is grounded at one end, couples to RXEN/BUSY, and
  has no gain path into RF_IN (Inference: negligible).

Conclusion as in pass 2: no board-level path is expected to use a meaningful share of the 39 dB budget
(Inference). ORDERING §5's S21 J30↔J31 and keyed C/N0 tests remain the evidence.

### 3.9 Pour slivers and unstitched GND (whole board, filled GND narrower than 0.25 mm and longer than 3 mm)

| Board | F.Cu | B.Cu |
|---|---|---|
| Pass 2 `03fe7572…` | 4.0 mm (8.0–8.7, 93.9–97.9); 3.5 mm (38.1–38.3, 93.0–96.6) | 5.9 mm (12.2–12.5, 66.4–72.2) |
| Final `7660620c…` | **15.2 mm (20.83–21.01, 11.56–26.73), new, in the strip (P3-RF-01)**; **5.9 mm diagonal (23.1, 66.5)–(29.0, 72.4) between SPI1_MISO and SPI1_MOSI, new**; the two pass-2 pieces unchanged | unchanged |

Method: per layer, the union of GND fills, minus the same set opened by 0.125 mm and re-grown by 0.135 mm. Pieces
longer than 3 mm with area > 0.2 mm² are listed.

**Through-copper distance from GND copper to the nearest GND via** (F.Cu and B.Cu, window x 0–46, y 0–28,
0.05 mm raster, Dijkstra search from every GND via ring; points cut off by the window edge are ignored):

| Board | F.Cu, farthest points (through copper / straight line to a via) | B.Cu, farthest points |
|---|---|---|
| Pass 2 | 7.43 / 1.79 mm at (20.9, 9.45), the pocket at the RXEN/BUSY corner; 6.63 at (7.9, 20.8); 5.83 at (12.15, 20.75) | 11.31 at (5.2, 26.0), 8.68 at (8.05, 26.95), 8.08 at (6.7, 13.1) (band and limiter area) |
| Final | **18.28 / 1.13 mm at (20.85, 26.7)**, the open end of the P3-RF-01 sliver; 15.26 at (20.9, 23.7), 12.28 at (20.85, 20.7), 9.26 at (20.9, 17.7), 6.28 at (20.85, 14.7), all on the sliver; next is 4.99 at (12.15, 20.75) | 6.25 at (23.0, 25.25) (band), 4.85 at (6.6, 10.45), 4.10 at (24.75, 8.2) |

Apart from the sliver, the fix pass shortened every unstitched run in the strip (F.Cu ≤ 5.0 mm, B.Cu ≤ 4.9 mm
through copper). The sliver's open end is 18 mm of copper from a via, 3.7 times the next-worst point.

## 4. Inferences (not measured, or not from a primary source)

- **P3-RF-01's RF magnitude:** microstrip about 75 Ω, εeff about 3.1, quarter-wave near 2.8 GHz; not modelled
  in 3-D.
- **P3-RF-02's tombstoning risk:** general SMT practice, with no maker or JLC figure. Vendor articles: NextPCB
  (https://www.nextpcb.com/blog/smt-passive-assembly-tombstoning-solder-balling-0201-0402) and AllPCB
  (https://www.allpcb.com/allelectrohub/smt-pad-thermal-relief-preventing-tombstoning-and-ensuring-reliable-soldering).
- **Via and pour inductances** (P3-RF-03): rule-of-thumb estimates.
- **Coupling conclusions** (3.8): carried from pass 2, not computed with a 3-D solver.

## 5. Outside this dimension (noted, not graded)

- **A second new F.Cu GND pour sliver,** 5.9 mm long and about 0.17 mm wide, runs diagonally from (23.1, 66.5) to
  (29.0, 72.4) between the SPI1_MISO and SPI1_MOSI diagonals near the IMU. It is absent on the pass-2 board. It is
  the same class of defect as P3-RF-01; for the routing reviewers.

## 6. Sources

- **u-blox MAX-F10S integration manual** UBXDOC-963802114-12892 R01, §4.4 "Layout", p. 66–67: keep 5 mm to RF
  components; "Any stubs at the ground planes must be avoided or ended with a via to the reference ground";
  ground the top and second layer under the module; CPW with ground on the second layer; GND vias around the RF
  line. §4.4.1 T-shaped paste.
  https://content.u-blox.com/sites/default/files/documents/MAX-F10S_IntegrationManual_UBXDOC-963802114-12892.pdf
- **EBYTE E22-900MM22S user manual** §4.1, via LCSC: no high-frequency digital, analog or power routing under the
  module; top-layer copper under the module "all copper is laid and well grounded".
  https://datasheet.lcsc.com/datasheet/pdf/70331b0eaf0eedaea0129e9e66d9a011.pdf?productCode=C5333985
- **JLCPCB PCB capabilities** (read 2026-10-17): via hole-to-hole spacing 0.2 mm; via hole to track 0.2 mm;
  minimum via 0.15 / 0.25 mm. https://jlcpcb.com/capabilities/pcb-capabilities
- **Project:**
  - `docs/REQUIREMENTS.md` F10, M2; `docs/M3_R7.md` §"RF chains", §"RF strip and lines"; `docs/R7_VALIDATION.md`;
    `docs/ORDERING.md` §5;
  - `m3.kicad_dru` (R7 RF rules, U30/U31 keep-out rules);
  - `tools/check_r7.py` l. 64–95, 360–364, 426–681;
  - `m3_design/r7_route.py` `stitch()`, `r7_lib.py`;
  - `fix2_F1_handoff.md`, `fix2_F3_handoff.md`; `pass2_rf.md`.

## 7. Method (reproduction)

All scripts ran under KiCad's Python against the repository board (read-only) or scratch copies in the session
scratchpad (`p3rf/`). Nothing in the repository was written except this report.

- **Strip diff:** dump tracks, vias, pads (with zone connection), footprints, zones and rule areas with y < 26 mm
  for both boards, then compare the sets.
- **GCPW scan:** at each 0.05 mm step along every RF segment, step outward from the track edge in 5 µm increments
  until F.Cu GND copper (fills, pads, tracks, vias) is hit; point-test In1/In2 GND fills at the centre and ±0.45 mm.
- **Through-copper distance:** rasterise F.Cu GND copper at 0.025 mm (pads) or 0.05 mm (strip), then run a
  Dijkstra search from the pad (or from all via rings) with 8-neighbour steps.
- **Sliver scan:** `SHAPE_POLY_SET.Deflate(0.125 mm)`, then `Inflate(0.135 mm)`, then subtract from the original.
  The sliver profile was re-measured after a `ZONE_FILLER` refill of a scratch copy.
- **Keep-out trial:** scratch copy plus three 0.15 mm RADIO_TXEN tracks; `kicad-cli pcb drc --severity-all` with
  the project's `.kicad_pro` and `.kicad_dru` beside it.
- **Paste:** parse D03 flashes in `m3-F_Paste.gbr` and `m3-B_Paste.gbr` (Gerber Y = −y) and match them to pad
  positions.
- **Gate:** `KICAD_CLI=… tools/check.sh` exit 0. Board SHA-256 unchanged after the review.
