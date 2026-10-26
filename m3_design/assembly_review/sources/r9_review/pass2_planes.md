# R9 review pass 2: planes and return paths

Reviewer: independent, dimension "planes and return paths". Board under review: `m3_design/assembly_review/m3.kicad_pcb`,
SHA-256 `4f841a0e44ebb1829ad7996dfe6320ed527fce1fdb1e5ff11658e0705b44ac14` (review pass 1's fix pass), design rules
`ea77b791…`, netlist `8b0e04ea…`, ground table `m3_design/r9_ground.tsv` `71be4615…`.

I hashed the board before and after the review; it is unchanged, and `git status` equals the snapshot taken before
pass 2 started. I edited nothing in the repository except this file. The one trial edit (a single added GND via, two
variants) was made on copies in the session scratchpad, refilled there with KiCad's native filler, measured and
deleted. The comparison board for "before the fix pass" is `fc3d5b34…`, extracted from the fix pass's own backup
(`scratchpad/r9review/orig/worktree_before_fix1.tgz`, SHA-256 checked) and deleted after use. The read-only scripts and
their text outputs (including the trials' DRC, gate and DC outputs) stay in the scratchpad's `r9review/planes2/`.

## Verdict

**0 Critical, 0 Major, 3 Minor.**

- **All six pass-1 findings in this dimension are closed or properly dispositioned** (§1). R9P1-PLANES-01, the one
  Major, is fixed on the board: C121's GND return is 1.38 mΩ (was 11.98), 87 % on In1 through the copper stage's via
  (35.6, 64.8); the guard strip's 0.37 mm neck is gone (0.655 mm along its length, 0.715 mm at the old neck); the new
  copper gate holds the class. R9P1-PLANES-05 (tool coverage) stays open as recorded and is carried as R9P2-PLANES-02.
- **No regression from the fix pass in this dimension** (§10). In1 is one plane, every In2 region is one piece, every
  critical net is referenced as on pass 1 (the reference table of all 60 AGENTS §3 critical nets is identical but for
  RADIO_TXEN's new width), R6b is 0.1022 with the same causes, P9 3.37 mm, P10 7.32 mm, the nine pockets are the same,
  every via's inner pads follow its connections and the Gerbers agree. The full ground gate passes (13 / 13).
- **Minor:**
  - **R9P2-PLANES-01 (worth fixing).** The worst outer GND copper on the board, C22's F.Cu strip at (37.45, 73.75),
    9.50 mm of copper from a via, and the worst B.Cu cluster, (35.95, 74.25), 6.65 mm, are recorded as having no via
    spot because "the 3V3 finger takes no antipad". That is the design aid's own rule (IN2_NARROW), not a constraint:
    with only that rule lifted the aid finds 1.12 mm² of legal centres, and a scratch trial with one via at
    (37.8, 72.4) removes both clusters, necks the In2 3V3 finger from 1.485 to 1.085 mm over about 0.5 mm, keeps every
    region one piece and adds no DRC item.
  - **R9P2-PLANES-02 (carried R9P1-PLANES-05, not worth fixing on its own).** The reference gate still samples only
    the R6 and extended nets; the two 0.400 mm tangencies on ARM1_SENSE_MCU and RADIO_NRST are unchanged.
  - **R9P2-PLANES-03 (records, not worth fixing on its own).** D-S8-02 / D-S8-16 still describe the step-8 table: the
    regenerated table dropped the reach via (38.75, 79.55), a grid and an island via and moved four others round C98's
    new spot. The totals happen to be unchanged (183 vias, 187 rows), so D-F1-07, M3_R9 and the fix handoff read as if
    only the three copper vias changed. C22's list of GND pads beyond 3 mm also omits four of eleven.

## 1. The previous pass in this dimension (`pass1_planes.md`, board `fc3d5b34…`)

| Finding | Pass-1 severity | Status on `4f841a0e…` | Evidence |
|---|---|---|---|
| R9P1-PLANES-01 C121's GND return 11.98 mΩ through a 0.37 mm neck | Major (fix brief: Minor) | **Closed** | `dc_solve.py --net GND --source C121:2 --sink J122:3,6,9,12 --grid 0.1 --window 18,54,40,82` (re-run): **1.38 mΩ**, F.Cu 13 % / In1 87 % at mid-path, via (35.6, 64.8) carries 6.82 of the solver's 7.7 A (89 %); C121.2 1.50 mm of copper from a via (gate raster; 16.10 on `fc3d5b34`), R103.2 3.74 (20.67); guard strip (x 28.785–29.44) 0.655 mm for y 65.6–75.6, 0.715 mm at y 75.8 (the old 0.37 mm neck), ≥ 0.9 mm from y 76.0 (`widths.py`); RAW_ACT 0.80 mΩ, 12.6 °C (`step10_evidence/dc/dc005_raw.txt`); copper gate present and passing. The fix pass used one via, not the trial's two: every spot inside the RAW_ACT B.Cu pour makes the via its own B.Cu ring, which the aid's `place_safe` refuses as a new P7 pocket (`fix1/aid_copper.txt`); 1.38 mΩ is below C150's accepted 2.58 mΩ, and the guard strip remains a second path if the via opened |
| R9P1-PLANES-02 forward-edge strip 12.5 mm | Minor, worth fixing | **Closed** | via (32.9, 99.85); the strip's worst point 6.04 mm at (26.75, 100.05) |
| R9P1-PLANES-03 no record of unstitched pieces / pad reach | Minor, worth fixing | **Closed** (one reason inaccurate: R9P2-PLANES-01; the pad list short: R9P2-PLANES-03) | R9_VALIDATION C22; every figure it gives reproduces on the gate's raster (`reach2.py`): F.Cu p95 4.13 / max 9.50 mm, B.Cu 3.01 / 6.65 mm, the six F.Cu clusters 9.50 / 9.37 / 8.95 / 8.61 / 8.48 / 8.05 mm, pads J9.2 6.99, R102.2 4.68, C87.2 4.25, R130.2 3.81, R103.2 3.74, C122.2 3.74, C28.2 3.69 mm (four more pads lie between 3.04 and 3.23 mm) |
| R9P1-PLANES-04 crystal plane: AN2867 "distinct" clause, via count | Minor | **Closed** (records) | C14 and D-S8-20 name the nine bonding vias, U1.10's via, U4's shared via and the clause deliberately not followed |
| R9P1-PLANES-05 reference gate samples only R6 / extended nets | Minor | **Open as recorded** ("Review pass 1": not in the brief) | unchanged on this board: carried as R9P2-PLANES-02 |
| R9P1-PLANES-06 M3_R9 gave step 6's In2 areas | Minor | **Closed** (records) | M3_R9 l. 120–121: RAW_ACT 241.2, BAT_IN 115.3, 3V3 1037.1 mm²; measured fills 241.23 / 115.25 / 1037.13 mm² |

## 2. Gates and tools run on `4f841a0e…`

| Run | Result |
|---|---|
| `m3_design/r9_ground_check.py --report` (in place, read-only; 7 min) | **13 / 13 gates OK** (table, drc, route, stitch, in2, xtal, islands, reach, copper, reference, pyro, contract, actuators). Reach: 18,544 points, P9 p95 **3.37 mm**, P10 **7.32 mm** at (31.25, 91.25), 824 points beyond 3.5 mm. P7 9. Reference: 3,206 / 31,359 (R6b **0.1022**), 1 sample outside own antipads (the recorded REF_STRAY); extended set 3,930 own + 1 |
| `tools/reference_audit.py` (R6, `--extended`) | 3,206 / 31,359 and 3,931 / 83,715; every sample `own_via` but USB_DM's edge at CC1's via (7.85, 32.75); per-side counts as D-S8-17 |
| `refall.py` (every signal track, centre and both edges every 0.02 mm, F.Cu → In1, B.Cu → In2) | identical to pass 1's table on `fc3d5b34` except RADIO_TXEN (0.2 mm now: 122 / 122 own-via samples, was 124 / 124) and the order of two non-critical change lists |
| `critvias.py` (critical layer changes) | identical to `fc3d5b34`; every critical via has a GND via within 0.69–1.39 mm (PYRO1_GATE (9.125, 61.955) the farthest; S13 0) |
| `vias.py` | 583 vias (345 × 0.5 / 0.3, 238 × 0.6 / 0.3), all "remove unconnected, keep start and end"; inner flashing equals same-net fill contact at every via (0 mismatches); In1 430 flashed (= the GND vias), In2 416; unflashed antipads 0.400 mm (0.450 mm in the 0.3 mm-clearance RAW_ACT / BAT_IN regions, 8) |
| Gerber package `fab/m3_gerber.zip` (bound to this board) | In1 ViaPad flashes 257 + 173 = 430, In2 214 + 202 = 416, via drill T1 0.300 mm `ViaDrill` 583 hits |
| `zones.py`, `erode.py`, `in1holes.py` | §3 |
| `islands.py`, `pocketspots3.py` | §8 |
| `reach2.py` (the copper gate's own `reach_maps` / `over_clusters` / `pad_reach`, 0.1 mm, y ≥ 23.5, every part class) | §7; the same script on `fc3d5b34` for the deltas |
| `legal_try.py`, `legal_pts.py` (`r9_ground_aid.legal()`, read-only, as is and with IN2_NARROW lifted) | §7, R9P2-PLANES-01 |
| Scratch trial `t1` (+1 GND via at (37.8, 72.4)) and `t2` ((37.2, 71.95)) | R9P2-PLANES-01: kicad-cli DRC, the ground gate's geometric gates (`trial_gates.py`), reach, In2 width, DC |

## 3. In1 and In2

- **In1.** One GND outline, 4,216.15 mm² (pass 1 4,215.6: the five added GND vias flash on In1, one RAW_ACT via fewer),
  170 holes, 311.0 mm². Eroding by 0.25 / 0.5 / 1.0 mm leaves one main piece each time; only bits between via and pin
  antipads (≤ 1.3 mm²) fall away, as on pass 1. No track on In1 or In2 (gate in2, check_r9 K-inner).
- **In1 slots** (holes with aspect > 1.8 and a long side > 1.2 mm): five, none under a foreign F.Cu signal.
  - J123's merged pin antipads (3.9 × 1.9 mm) and the strip vias GNSS_VCC_RF / GNSS_ANT_DC / GNSS_LNA_EN
    (2.65 × 0.8 mm, 0.79 mm from GNSS_RF_ANT's edge): pass 1's.
  - SERVO3_MCU's via (25.54, 54.4) and a 3V3 via (25.54, 55.35) (0.8 × 1.75 mm): SERVO4_MCU's F.Cu edge passes 0.445 mm
    from (25.54, 54.4), outside the 0.40 mm antipad (refall: SERVO4_MCU only own-via samples). Present on `fc3d5b34` too.
  - RAW_ACT vias (34.6 / 35.5, 78.2) (1.7 × 0.8 mm) and, **new**, (31.5 / 32.2, 78.2) (1.5 × 0.8 mm): D-F1-04 moved
    (31.0, 78.2) to (31.5, 78.2), 0.7 mm from its neighbour, so the two antipads merge. Both lie under the RAW_ACT
    F.Cu and B.Cu pours, where no signal runs; I find no electrical effect (observation, §12).
- **In2 regions** (fills): GND 1,742.24, strip GND 982.09, crystal plane 35.31, 3V3 1,037.13, RAW_ACT 241.23, BAT_IN
  115.25 mm², each one piece (gate in2). RAW_ACT is 0.67 mm² smaller than on pass 1: the copper via (35.6, 64.8) is
  unflashed there and its 0.45 mm antipad bites the region's east edge (x 35.15–36.05), off the 7.7 A path (RAW_ACT
  0.80 mΩ, unchanged within 0.01 mΩ). Necks under erosion are pass 1's (3V3's spine finger vanishes at 0.75 mm; In2 GND
  splits at 1.0 mm near (35–44, 56–58)); In1 is solid under both, so neither matters for returns.

## 4. Critical-signal references, R6b and split crossings

- **Every critical net is referenced.** Over all 60 AGENTS §3 critical nets (route_check's rf, pyro, crystal, usb, spi
  and rfif classes) unreferenced samples fall only in their own via antipads, their own terminal pads' In1 antipads
  (PYRO1_BUS / IGN / OUT at J124 / J121), the two qualified launch windows (GNSS_RF_ANT, RADIO_RF_ANT, R-4) and three
  0.400 mm tangencies: USB_DM at CC1's via (the recorded REF_STRAY), ARM1_SENSE_MCU at RAW_ACT_SENSE_MCU's via
  (26.95, 46.5) and RADIO_NRST at CAM_MCU_RX's via (33.15, 44.5). Identical to pass 1.
- **The fix pass's critical-net changes kept their references.** QSPI_IO2's re-routed east run (y 50.6, D-F1-01) is on
  F.Cu over In1 GND, 12.61 mm, with only its via's own samples unreferenced; its edge keeps more than the 0.40 mm
  antipad radius from every foreign via centre it passes: U1.6's 3V3 via (14.5, 50.65) 0.502 mm, IMU_INT1's
  (13.21, 49.15) 0.590 mm, QSPI_NCS's (14.57, 45.4) 0.430 mm the closest (`qspi2.py`; D-F1-01's 0.252 / 0.34 mm are
  edge-to-edge gaps). RADIO_TXEN (0.2 mm, D-F1-02) is B.Cu over the strip's In2 GND for its whole 21.99 mm.
- **R6b 0.1022 and its causes hold.** 24 via sides of the 12 critical layer-change vias (QSPI × 6, HSE × 2, SPI1 × 3,
  IMU_CS), 119–133 samples a side and 172 / 241 / 242 on the three two-branch sides, plus the one REF_STRAY sample:
  D-S8-17's classes exactly. The floor arithmetic (24 × 119 = 2,856 = 0.091 > 0.08) and "12 is the minimum" (U3, Y1
  and U4 on the bottom under U1, one via per net) stand. The metric counts no physical loss of reference; the 0.08 miss
  is honestly recorded (C11).
- **No critical track crosses an In2 split** or lies over RAW_ACT / BAT_IN. The B.Cu critical runs over In2 3V3
  (QSPI, SPI1, IMU_CS; 0.29–7.37 mm) each have a GND via 0.77–1.30 mm away and a 3V3 / 3V3A capacitor 1.71–5.40 mm
  from the via (C29, C16, C17, C31), as on pass 1. Non-critical crossings (information): BAT_FAULT_N and
  LOGIC_SOURCE_ST over In2 RAW_ACT for 5.1 / 5.7 mm (slow open-drain flags), and five slow status / sense lines across
  3V3 / GND boundaries; unchanged.

## 5. The crystal's local In2 plane (D-S8-20) against ST AN2867

- **Unchanged by the fix pass** (`xtal.py` output identical on both boards): R9_GND_In2_Y1 fills 35.31 mm² in one piece,
  bonded to In1 by nine GND vias, all flashed on In2; the only foreign In2 copper in the area is U1.6's 3V3 via ring at
  (14.5, 50.65), 0.05 mm across its forward edge; NRST's notch (x 18.9–20.73, y 50.2–50.45) keeps NRST's B.Cu run over
  3V3 with 0.05 mm to spare.
- **Sources.** AN2867 Rev 10 (DocID15287, August 2015) §5.1, the revision the records cite (pass 1's copy:
  https://www.raltron.com/webproducts/technical/technical_notes/Oscillator-design-guide-for-STM8S-STM8A-and-STM32-microcontrollers-ST-MICRO-1.pdf),
  and **AN2867 Rev 15 (October 2021) §7.1 "PCB design guidelines", p. 45**, ECS Inc.'s copy of ST's document
  (https://www.ecsxtal.com/store/pdf/stm32-microcontroller-application-note-092823.pdf). Rev 15 keeps Rev 10's
  wording: "The oscillator PCB should be underlined with a dedicated underneath ground plane, distinct from the
  application PCB ground plane. The oscillator ground plane should be connected to the nearest microcontroller ground.
  … Note that if a crystal in a metallic package is used, it should not been connected to the oscillator ground." ST's
  site lists a later revision (Rev 24, February 2026); ST's server refused every automated download, so I could not
  read it.
- **As built against the clauses.** Nearest MCU ground: met (U1.10, about 1 mm of F.Cu from via (16.0, 50.6)). Guard:
  Y1.2 / Y1.4 and the main B.Cu GND island surround the crystal. Stray capacitance: about +0.37 pF per HSE node
  (Inference, recorded). "Distinct from the application ground": deliberately not followed, now recorded (C14). The
  metallic-package note: Y1 (NX3225GA) has its pads 2 / 4 ("NC, grounded" in ROCKET_FC_FROZEN_DESIGN's part table)
  tied to that same bonded ground; whether they reach the lid is not checked here. With the local plane bonded at nine
  points the note has no separate content (Inference), and the bench HSE check (ORDERING §5) stands. No defect.

## 6. Via pads (D-S8-19)

- All 583 vias use "remove unconnected layers, keep start and end"; inner pads appear exactly where same-net fill
  touches (0 mismatches on In1 and In2). The new vias follow the rule: the three U31 module vias and the three copper
  vias are GND, flashed on In1, and on In2 where GND fill meets them; (35.6, 64.8) is unflashed in the In2 RAW_ACT
  region.
- Unflashed vias clear the planes by 0.400 mm (0.450 mm in the 0.3 mm regions): copper 0.25 / 0.30 mm from the 0.30 mm
  hole against JLC's "Inner layer via hole to copper clearance: 0.2mm"; component holes keep their inner pads (JLC
  "Inner layer PTH pad hole to copper clearance: 0.3mm"); the 0.5 / 0.3 and 0.6 / 0.3 mm vias are well inside JLC's
  multilayer via minimum of 0.15 mm hole / 0.25 mm pad (https://jlcpcb.com/capabilities/pcb-capabilities, read
  2026-10-25). Vias are tented both sides (board setup).
- The Gerbers carry the same flashes (430 / 416) and 583 via drills. D-S8-19 is correct.
- Side note (not a finding): dc_solve assumes 20 µm via plating; JLC's page gives an average of 18 µm, so via barrel
  resistances are about 10 % optimistic in every solve. No via in the recorded solves is near a limit.

## 7. Stitching density and through-copper reach

- **P9 / P10** (gate reach, 0.5 mm raster): 3.37 / 7.32 mm, the maximum at (31.25, 91.25) in the battery entry, where
  F.Cu, In2 and B.Cu are BAT_IN (D-S8-16's recorded cause, unchanged). P8 9.49 GND vias per cm² (R8 8.15).
- **Through-copper reach on the copper gate's raster** (0.1 mm, y ≥ 23.5, every outer GND point to the nearest GND via
  or plated GND hole):

  | | F.Cu p95 / max | B.Cu p95 / max | worst GND SMD pad (any part class) |
  |---|---|---|---|
  | `fc3d5b34` (pass 1) | 4.84 / 28.41 mm (37.45, 73.75) | 3.03 / 6.65 mm | R103.2 20.67, C121.2 16.10 mm |
  | `4f841a0e` (now) | 4.13 / **9.50 mm (37.45, 73.75)** | 3.01 / **6.65 mm (35.95, 74.25)** | J9.2 6.99 mm (recorded), then R102.2 4.68 mm |

  - The six F.Cu clusters beyond 8 mm are exactly COPPER_EXCEPT's: the east strip 9.50, the ARM1_SENSE guard strip
    9.37 and its north end 8.61, J9's piece 8.95 and its corner 8.05, the piece over the FET pair 8.48 mm.
  - The aid's `legal()` (read-only) finds no spot in any of them, as recorded. With only its IN2_NARROW rule lifted
    (no antipad in an In2 power region narrower than 2.5 mm), it finds **1.12 mm² of legal centres in the east strip**
    (x 36.6–37.8, y 70.1–72.4), 0.52 mm² that also serve the B.Cu cluster, and none in the other five
    (R9P2-PLANES-01).
  - Every D, L, Y and FB GND pad is within 1.5 mm of copper (D122.1 1.48 mm the farthest diode pad); the copper gate
    checks only C / U / Q / J pads, which today loses nothing (observation, §12).
  - One cluster below the gate grew: the F.Cu strip between V_HOLDUP's run (x 38.5) and the RAW_PROTECTED pour,
    x 38.15–39.45, y 72.55–76.15, 6.84 → 7.47 mm, because the regenerated table no longer has the reach via
    (38.75, 79.55) (R9P2-PLANES-03).

## 8. The nine single-via pockets (P7)

- `islands.py` finds F.Cu 23 and B.Cu 16 GND outlines, each with at least one GND via or plated GND hole. Exactly nine
  have one: WEAK_EXCEPT's, at their recorded areas (F 0.27, 6.03, 2.82, 0.71; B 0.78, 3.51, 0.88, 7.71, 1.77 mm²).
- No second via fits in any (aid's island stage log on the fix pass's step-7 board; my independent `pocketspots3.py`
  on this board: 0 candidates in all nine).
- Pads in the pockets: D4.2 (USB ESD, bench-only, R8 D63), C150.2 / C151.2 (2.58 mΩ, one barrel), the RAW_ACT_SENSE
  divider bottom (µA). Unchanged and recorded (C9).

## 9. GND islands, fingers and thin pieces

- route_check r9: no sliver, no finger, no starved thermal, no dead copper (gate route OK, DRC 0).
- Thin outer pieces (route_check `thin_pieces`, ≥ 2 mm, ≥ 0.15 mm²): F.Cu 50 / 69 and B.Cu 59 / 86 narrower than
  0.75 / 1.0 mm (`fix1_measure.py`, as C22 records).
- The guard strip beside ARM1_SENSE no longer carries C121's return; it is joined at both ends and its midpoint is
  9.37 mm of copper from a via (recorded; no spot even with IN2_NARROW lifted: the RAW_ACT corridor and PYRO_GAP leave
  none, and the 0.655 mm strip is narrower than a via with its clearances).

## 10. The fix pass's changes, one by one (regression check)

| Change | Effect in this dimension |
|---|---|
| Copper vias (35.6, 64.8), (32.9, 99.85), (41.4, 41.1) | C121.2 1.50 mm and 1.38 mΩ; forward strip 6.04 mm; east-edge strip under 8 mm. (35.6, 64.8) cuts the In2 / B.Cu RAW_ACT edge inside its recorded box only; RAW_ACT 0.80 mΩ |
| RAW_ACT_F 29.75 edge to y 76.6 | guard strip ≥ 0.655 mm everywhere |
| U31 module vias (3) | GND, flashed In1 / In2, tented; R-8's In1 / In2 coverage under U31 holds (check_r9 in the gate) |
| RAW_ACT via (29.6, 78.2) dropped, (31.0 → 31.5, 78.2) | one more merged In1 antipad pair under the RAW_ACT pours (§3); no signal over it |
| Table regenerated (C98 moved): reach (38.75, 79.55), grid (38.8, 61.65), island (40.24, 64.85) dropped; cover (38.45, 61.35), island (39.74, 62.60) added; patch (38.55, 63.65) → (38.45, 62.55), (38.45, 59.05) → (38.55, 58.95) | P9 3.45 → 3.37 mm; P7 9; no new island; one sub-gate cluster 6.84 → 7.47 mm; records not updated (R9P2-PLANES-03) |
| QSPI_IO2 y 50.6, TXEN 0.2 mm, C98 / USB_LIMITED | references unchanged (§4) |
| Copper gate, CORRIDOR_EXCEPT, `place_safe` | sound: a pad the raster cannot reach fails (None), stale entries fail, the corridor exception is tested on via centres inside one box; coverage note in §12 |

## 11. Findings

### R9P2-PLANES-01: Minor, worth fixing

**The board's worst unstitched GND copper, C22's east strip (F.Cu, 9.50 mm of copper from a via at (37.45, 73.75)),
and its worst B.Cu cluster ((35.95, 74.25), 6.65 mm) are recorded as having no via spot because "In2's 3V3 finger
takes no antipad". That is the ground aid's IN2_NARROW design rule, not a physical or board-rule constraint: one GND
via at (37.8, 72.4), legal under every other aid rule, removes both clusters and leaves the 3V3 finger one piece.**

- **Requirement.** REQUIREMENTS M2: every review-only residual is listed "with location, rule, measured reason and why
  it cannot reasonably be removed"; "unstitched GND pour fingers" are an M2 item. Owner priority 2 (robust, simple
  layout). Pass 1's R9P1-PLANES-02, a 12.5 mm strip fixed by one via, was the same class and was marked worth fixing.
- **Evidence** (pcbnew on `4f841a0e`; scripts in `planes2/`):
  - The strip x 36.15–38.05, y 65.4–74.2 lies between the RAW_ACT F.Cu pour and VLOGIC's sense tap / V_HOLDUP's run,
    dead-ended at C84.1; its only via is (35.6, 64.8) at its north end. In2 under it: the 3V3 finger, 1.485 mm wide
    (x 36.31–37.795) at y 71.35–72.4 (`in2neck.py`). B.Cu under its south part: the (35.95, 74.25) cluster.
  - `r9_ground_aid.legal(revive=True, spacing=0.6)` as is: 0 mm² in the strip (the recorded result). With
    `IN2_NARROW` lifted and nothing else changed: **1.12 mm²** (x 36.6–37.8, y 70.1–72.4; `legal_try.py`,
    `legal_pts.py`).
  - **Scratch trial t1**, one 0.5 / 0.3 mm GND via in D-S8-19's pad mode at **(37.8, 72.4)**, native refill:
    - F.Cu: the 9.50 mm cluster is gone (the strip's worst now about 5.9 mm); the board's F.Cu worst becomes the
      recorded guard strip, 9.37 mm; F.Cu p95 4.13 → 4.00 mm.
    - B.Cu: worst 6.65 → **5.96 mm** (27.25, 56.15); p95 3.01 → 2.98 mm; the box round (35.95, 74.25) 6.65 → 4.87 mm.
    - In2: the via is unflashed in the 3V3 finger; the finger narrows to **1.085 mm** over about 0.5 mm
      (1.42 / 1.14 / 1.085 / 1.14 / 1.42 mm at y 72.0 … 72.8), one piece (gate in2 OK).
    - The ground gate's geometric gates (`trial_gates.py`): stitch, in2, xtal, islands (P7 9), reach (P9 3.37 →
      3.32 mm), reference (3,206, unchanged) OK; copper fails only on the then-stale COPPER_EXCEPT entry
      (37.45, 73.75), as it must.
    - kicad-cli DRC on the copy: no new violation (the same 199 `lib_footprint_issues` as the unmodified copy in the
      scratch folder, which has no library table), 0 unconnected.
    - DC, `dc_solve.py --net 3V3 --source L1:2 --sink U1:75 --grid 0.1` on t1: **15.41 mΩ** against 15.25 mΩ on this
      board (`step10_evidence/dc/v33_u1_75.txt`): +0.16 mΩ, 0.08 mV at 0.5 A.
  - Trial t2 at (37.2, 71.95) also removes both clusters but splits the finger into 0.485 + 0.19 mm strands round the
    antipad; t1's edge spot is the right one.
- **Impact** (Inference). The strip carries no pad, so no return current depends on it; it is a 9 mm dead-end GND
  stub over In1, the class M2 names. The fix removes the board's worst F.Cu dead end and its worst B.Cu cluster for one
  table row. The cost, a 1.085 mm local neck in a 1.485 mm 3V3 feed carrying well under 1 A, is 0.16 mΩ on the
  3V3 solve above, far below anything the 3V3 budget can see.
- **Fix.** In `r9_ground_aid.py`, an `IN2_NARROW` exception box beside the existing `CORRIDOR_EXCEPT` (for example
  x 37.55–38.05, y 72.0–72.6, "the east strip's via at the 3V3 finger's edge; finger ≥ 1.0 mm, one piece"), so the
  copper stage's cluster pass places the via itself; regenerate and freeze the table (`--check`), drop COPPER_EXCEPT's
  (37.45, 73.75) entry (it fails as stale otherwise), re-run stages 35–39, `tools/check.sh`, the 3V3 DC rows and the
  scorecard. If the owner prefers no copper change: correct C22's and COPPER_EXCEPT's reason to say a spot exists at
  (37.8, 72.4) with a 1.085 mm finger neck, so the deviation states why it is kept.

### R9P2-PLANES-02: Minor, not worth fixing on its own (carried from R9P1-PLANES-05)

**The reference gate (`r9_ground_check` reference, `reference_audit.py`, R6b) still samples only the R6 and extended
nets; the pyro / arming nets and the non-SPI RADIO_* / GNSS_* nets are never sampled, so a later split crossing on one
of them would pass the gate.**

- **Status.** R9_VALIDATION "Review pass 1" lists R9P1-PLANES-05 as open (not in the fix brief). Nothing changed.
- **Evidence on `4f841a0e`.** `critical_reference.R6_NETS` / `EXTENDED` unchanged. Sampled by `refall.py`, all 60
  AGENTS §3 nets are clean but for the two 0.400 mm tangencies of pass 1: ARM1_SENSE_MCU (5 samples) at
  RAW_ACT_SENSE_MCU's via (26.95, 46.5) and RADIO_NRST (5 samples) at CAM_MCU_RX's via (33.15, 44.5).
- **Fix** (with the next gate change): sample route_check's SIGNAL_CRITICAL classes in the reference gate, treating a
  net's own plated terminal holes like its own vias, the two launch windows as R-4's, and the two tangencies as
  REF_STRAY entries.

### R9P2-PLANES-03: Minor, not worth fixing on its own (records)

**The fix pass regenerated the ground table with C98 moved, and the regeneration changed more than the three copper
vias the records name; D-S8-02 and D-S8-16 still describe the step-8 table, including a reach via that no longer
exists.**

- **Evidence** (`diff` of `r9_ground.tsv` against the fix pass's backup of `fc3d5b34`'s table):
  - dropped: reach (38.75, 79.55), grid (38.8, 61.65), island B (40.2431, 64.8455);
  - added: cover (38.45, 61.35), island B (39.7431, 62.5955) and the three copper vias;
  - moved: patch (38.55, 63.65) → (38.45, 62.55), patch (38.45, 59.05) → (38.55, 58.95).
  - Stage counts now: return 11, pad 3, grid 88, cover 37, island 13, patch 26, strap 5, reach 1, copper 3 (183 vias,
    187 rows, the same totals as step 8's, so the change is invisible in the totals).
  - D-S8-16 still says the reach stage added "(31.05, 51.25) (26 points …) and (38.75, 79.55) (6 points)"; D-S8-02's
    stage counts are step 8's; D-F1-07, M3_R9 "Ground" and `fix1_handoff.md` name only the three copper vias.
  - Effect measured: the F.Cu strip at (38.95, 72.55) went 6.84 → 7.47 mm of copper from a via (below the 8 mm gate);
    P9 improved (3.45 → 3.37 mm).
- **A second, smaller records gap in the same area.** C22's "GND pads beyond 3 mm" lists seven pads (J9.2 6.99 …
  C28.2 3.69 mm); on this board eleven are beyond 3 mm. Missing: C94.2 3.23, C100.2 3.19, R178.2 3.16 and U5.3
  3.04 mm (`reach2.py`; the copper gate's own `pads_over_3mm` evidence lists C94.2, C100.2 and U5.3 too). All are
  within the gate's 5 mm; only the list is short.
- **Fix** (next records edit): one sentence in D-F1-07 (and a "superseded" pointer on D-S8-16) listing the regenerated
  table's stage changes and their cause (C98's new spot; the reach stage met P9 with one via); complete C22's pad list.

## 12. Observations (not findings)

- **C121's return through one via.** 89 % of C121's return crosses one 0.3 mm barrel between F.Cu and In1 (0.24 mm
  long, about 0.2 mΩ). C121 carries only ripple, not the servos' DC return, so the solver's "6.82 A at 7.7 A" is a
  scaling, not a load (Inference). A second via is refused only by `place_safe`'s rule that a via may not form its own
  ring inside the RAW_ACT B.Cu pour, the same harmless geometry as WEAK_EXCEPT's C150 entry; adequate as built.
- **The copper gate's pad classes.** It checks C / U / Q / J pads only; D (ESD, TVS, clamp), L, Y and FB GND pads are all
  within 1.5 mm today, R pads within 4.68 mm (R102.2, a 10 kΩ pull-down). Adding D to `REACH_PARTS` would cost nothing
  and keep the ESD returns covered if a later change moves them.
- **In1 slot at (31.1–32.6, 77.8–78.6)** (§3): created by D-F1-04's 0.7 mm via spacing in a 1.2 mm-pitch row; harmless
  under the pours. The row's irregular pitch (31.5, 32.2, 33.4, 34.6, 35.5) is the routing reviewer's to judge.
- **Guard-strip width in the records.** D-S8-05 and the `r9_power.py` comment say 0.69 mm; the fill is 0.655 mm
  (C22's "0.66 mm" is right). R9_VALIDATION's "the 0.37 mm neck is 0.72 mm" is the width at the old neck, correct as
  stated.
- **AN2867's metallic-package note** is not mentioned in C14; with the plane bonded at nine points it adds nothing to
  the recorded departure from the "distinct" clause (§5).
- **R9P1-PLANES-01's severity.** The fix brief carried it as a confirmed Minor; on this board the class is closed and
  gated either way.

## Method and scripts

All scripts are in the session scratchpad, `r9review/planes2/` (pass 1's helpers copied and re-run, plus new ones).
All are read-only on the repository board; the trials were built by `fixtrial.py` on copies (`trial/`) and deleted.

- **Inventory and vias:** `zones.py`, `vias.py`, `in1holes.py`, `slotover.py`, `erode.py`; Gerber counts with
  `gcount.py` on an extract of `fab/m3_gerber.zip` (deleted after use).
- **References:** `refall.py` (both boards; outputs `refall_new.txt`, pass 1's `refall.txt`), `critvias.py`,
  `qspi2.py`, `tools/reference_audit.py`, `r9_ground_check.py --report`.
- **Crystal:** `xtal.py`, `xtal2.py`, `u1gnd.py` (both boards, outputs compared); AN2867 Rev 15 text extracted from
  ECS's copy in its own folder.
- **Reach and islands:** `reach2.py` (the copper gate's `reach_maps` / `over_clusters` / `pad_reach`), `unreached.py`,
  `ptreach.py`, `islands.py`, `pocketspots3.py`, `widths.py`, `piece.py`, `legal_try.py`, `legal_pts.py`.
- **DC:** `tools/dc_solve.py` (C121:2 → J122 GND on this board; 3V3 L1:2 → U1:75 on trial t1).
- **Trials:** `fixtrial.py`, `trial_gates.py`, `in2neck.py`, kicad-cli DRC on the copies.
- **Sources:** ST AN2867 Rev 10 §5.1 (Raltron's copy) and Rev 15 §7.1 p. 45 (ECS's copy), URLs in §5; JLC PCB
  capabilities (URL in §6, read 2026-10-25): inner-layer via hole to copper 0.2 mm, inner-layer PTH hole to copper
  0.3 mm, multilayer via 0.15 mm hole / 0.25 mm pad, average hole plating 18 µm.
