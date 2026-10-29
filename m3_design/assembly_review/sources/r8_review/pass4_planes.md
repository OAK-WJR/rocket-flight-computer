# R8 review pass 4: planes and return paths

Reviewer: independent, dimension "planes and return paths". Board `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
`c84f00b88f5fb9409de40f33b2d51a48fb29fb66c386c869b7f93ea791e37c54` (netlist `0cc1ed69…`). I hashed it before and after
the review and it is unchanged; `git status --short` is also unchanged by my runs. Read-only: I edited nothing in the
repository except this file. The pass-3 board `990c8040…` was rebuilt for the diffs from commit `431025d` plus the
coordinator's backup (`r8_backup_990c8040/tracked.diff`), hash-checked, in the session scratchpad, and deleted after use.

## Verdict

**0 Critical, 0 Major, 1 Minor (records).**

- Both pass-3 findings in this dimension are closed (section 1).
- Fix pass 3 caused no plane regression. Its copper diff against `990c8040…` is exactly the five intended edits, and
  every plane change is accounted for (section 2):
  - USB_LIMITED's trunk moved to y 37.3;
  - R172 and the RAW_ACT_SENSE lane moved to x 30.65;
  - CAM_PWR_EN's lower leg redrawn on x 28.25 with one 45° run;
  - R165's BAT_ENABLE via is now 0.5 mm (was 0.6);
  - one cover via moved, (28.875, 32.875) → (29.125, 32.625).

  The pass-3 measurements that did not move are equal sample for sample: the reference audit, the critical vias, the
  split crossings, the island count with via counts per island, the finger counts, the GND-pad reach, and P3 / P3b / P4
  / P7–P11.
- The single Minor: R8_VALIDATION's scorecard still has two stale P6 / P1 records after fix pass 3. The C4 row says
  1752.5 mm, the column header says "fix pass 2", and the intro credits the P1 / P6 moves to the wrong edit (D106 /
  D107 rather than D108).

## Gates and tools run (on `c84f00b8…`)

| Run | Result |
|---|---|
| `tools/check.sh` | **exit 0**: DRC 0, unconnected 0, parity 0, ERC 0; metadata / 3D OK; silk 0 points outside; R8 contract OK; route_check r8 0 failing, 3 allowlisted, 0 stale, 0 leftovers, 0 removable (22 bump windows); check_actuators OK; fit OK |
| `m3_design/r8_ground_check.py --report` | **all 14 gates OK** (rigid, table, drc, route, islands, reach, power, trims, pyro, inner, in2, contract, l10, reserved). Reach: board p95 4.47 / max 9.65 mm at (0.25, 88.25); pours p95 2.90 / max 5.89 mm (16,618 points; pass 3 16,608). Islands 21; the one weak island is D4.2's (F.Cu, 2.891 mm², 1 via). The report's only differences from pass 3's are the board SHA, `L10_EXCEPT` R172 0.635 → 0.685 mm (D106) and the pour point count |
| `step7/make_ground.py <board> --built` | 201 rows (fence 25, stitch 2, c24 2, trim 7, return 16, grid 89, cover 54, island 5, pad 1; 193 vias); **byte-identical** to `m3_design/r8_ground.tsv` |
| `tools/reference_audit.py` (R6 set / extended) | 46,845 / 5,186 (11.07 %): own via 3,592, keep-out 1,368, other via 226. Extended 102,384 / 5,944 (5.81 %). **The JSON reports equal pass 3's in every key** (all entries) |
| `NO_GATE=1 NO_DC=1 tools/run_survey.sh <board> <out> <990c8040 board>` | P1 0.9051, P2 1, P3 16, P3b 4, P4 5, P5 4, P6 1752.2 mm, P7 1, P8 8.15 / cm², P9 / P10 4.47 / 9.65 mm, P11 2.90 mm; R1 / R3 2.9 / 2.9 mm; R6b 0.1107; S12 25, S13 0; C6 1. `critical_reference.py 990c8040 c84f00b8`: **0 samples lost** (R6 set and extended) |
| `tools/test_reference_audit.py`, `tools/test_r8_ground.py` | 14 tests OK |
| Own scripts (pcbnew, read-only, listed at the end) | copper and fill diffs against `990c8040…`; zone inventory; islands with their vias; fingers at 0.75 / 1.0 mm with and without rings; GND-pad copper reach; critical vias with GND partners; full critical-net split sampling; B.Cu over foreign antipads; In1 holes; In2 erosion; In2 reference under every changed track; antipads at the changed vias; the moved cover via's connections; GND fill to the ACT_GATE / ACT_DRV pads |

## 1. Pass-3 findings in this dimension

| Pass-3 item | Status on `c84f00b8…` | Evidence |
|---|---|---|
| R8P3-PLANES-01: fix pass 2's "move R120.2's GND via" candidate is aimed at the wrong copper; the pours are nearer | **Closed** (D109) | The candidate is closed and the pour figures are recorded in: C12b #18; the pyro observations ACT_GATE row (R8_VALIDATION line 552); M3_R8 lines 370–380; `fix2_handoff.md` (marked correction); D109. The GND-to-gate zone clearance is offered as an owner option in "Open after fix pass 3". I re-measured with a polygon distance (`padfill.py`): GND fill 0.150 mm from R120.2 and C120.2 (B.Cu) and from R121.1, R121.2 and Q122.3 (F.Cu); Q121.4 0.667 mm; Q120.4 1.649 mm; TP121.1 1.000 mm. The records give 0.151 mm (fix pass 3's `min_gap` method); both figures are the board's 0.15 mm zone clearance |
| R8P3-PLANES-02: the P3b row named three of four In1 slots | **Closed** | R8_VALIDATION line 97 now names all four slots. They match `survey.json` `planes.in1_slots`: J123 5.60 mm², J3 legs 3.99 mm² ×2, and the SPI1 / IMU_CS cluster 2.95 mm² at x 8.29–11.00, y 55.15–56.85. The row also gives SPI1_SCK's 34 F.Cu edge samples, which `reference_audit` confirms (SPI1_SCK F.Cu, other_via at SPI1_MISO's via, 34). One wording nit is folded into finding 01: the row says the cluster is "under U4's pads", but it lies just aft of U4's aft pad row |

## 2. What fix pass 3 changed on the planes

**Copper diff** (`copperdiff.py`, `990c8040…` → `c84f00b8…`). It contains no zone outline change and nothing on F.Cu,
In1 or In2. All changes are on B.Cu:
- R172 moved x 30.6 → 30.65;
- RAW_ACT_SENSE moved x 30.6 → 30.65, (30.0, 58.1) → (30.65, 57.45) → (30.65, 48.53);
- RAW_ACT_SENSE_MCU's stub now ends at x 30.65;
- USB_LIMITED: five segments moved y 37.25 → 37.3;
- CAM_PWR_EN (31.85, 36.8) → (28.25, 36.8) → (28.25, 30.025) → (30.775, 27.5), replacing x 28.0 and the L;
- the BAT_ENABLE via (16.6, 104.5) went from 0.6 / 0.3 to 0.5 / 0.3 mm;
- the GND cover via moved (28.875, 32.875) → (29.125, 32.625).

**Fill diff, by plane.**

| Layer / net | Change | Cause |
|---|---|---|
| In1 GND | +0.167 mm² (In1 fill 4,861.74 → 4,861.91 mm²; P1 0.905 → 0.9051) | The BAT_ENABLE via's antipad: hole 0.958 → 0.791 mm², perimeter 3.48 → 3.16 mm (`holeat.py`). `filldiff.py` also prints a 0.96 mm² "gain"; that is the fracture artefact pass 3 described |
| In2 BAT_IN | +0.18 mm² (229.6 → 229.8 mm²) | The same via's antipad: hole 1.139 → 0.958 mm², perimeter 3.795 → 3.479 mm. This is the −0.3 mm in P6 (1752.5 → 1752.2 mm). Erosion is unchanged: BAT_IN is solid to 0.4 mm |
| In2 3V3 | 0 (0.35 mm² moved) | The moved cover via's antipad. The hole is 0.792 mm², 3.17 mm perimeter, before and after, so area and perimeter are neutral. 3V3 erosion cores are equal to pass 3's. No B.Cu or F.Cu critical track lies over either position (`b_over_antipad.py` output equal) |
| In2 GND, RAW_ACT | none | — |
| B.Cu GND | +1.4 mm² (zone 3,428.8 → 3,430.2 mm²) | CAM_PWR_EN's new leg. Per island (via counts unchanged): 1,719.13 → 1,720.52 mm² (263 vias); 90.18 → 90.34 (11); 63.31 → 63.23 (7); 1,056.39 → 1,056.29 (99). Plots of x 24–34 / y 25–39 and x 13–32 / y 34–41 show no new pocket, neck or sliver. The pour no longer reaches between CAM_PWR_EN (y 36.8) and USB_LIMITED (y 37.3): the gap is 0.200 mm, under two clearances, as at 0.150 mm before |
| F.Cu GND | +0.09 mm² | The BAT_ENABLE via shrink |

**Changed tracks over In2** (`chref.py`: centre line and both edges every 0.01 mm). Every changed B.Cu track runs over
In2 3V3, as before, and none crosses a split:
- CAM_PWR_EN: 19.76 mm over 3V3 (was 21.72), plus 0.52 mm at its own via, as before.
- USB_LIMITED: the trunk is all over 3V3, as before.
- RAW_ACT_SENSE: 21.22 mm over 3V3.
  - Since it moved 0.05 mm east, its east edge passes the In2 3V3 antipad of USB_LIMITED's 0.6 mm hop via (31.25,
    55.3) for 0.47 mm (was 0.15 mm).
  - RAW_ACT_SENSE is a DC divider node, not an AGENTS §3 critical net, so this is an observation only.
- BAT_ENABLE: 0.24 mm over In2 BAT_IN at its via end (was 0.18). It is a µA enable divider.

**The moved cover via** (29.125, 32.625) is fully joined on F.Cu, In1 and B.Cu GND (16 / 16 probes at r 0.3 mm on each),
with a 3V3 antipad on In2. Its nearest GND vias are 2.30 and 2.50 mm away (before: 2.45 / 2.65 mm). `make_ground.py
--built` reproduces the table that places it.

## 3. In1

- **The plane.** One GND outline, 4,861.9 mm² (P2 1). There is no In1 track (S16 0).
- **Holes.** 196 holes, 305.4 mm² (pass 3: 305.6). The difference is the BAT_ENABLE antipad. The same list as pass 3:
  - the J121 / J124 / J1 / J122 barrels;
  - the J30 / J31 launch cut-outs (7.29 mm² each);
  - J123 (5.60 mm²);
  - J3's legs 1 and 4 (3.99 mm² each);
  - the SPI1 / IMU_CS cluster (2.95 mm²).
- **Critical F.Cu tracks over a foreign In1 hole.** Unchanged, edge samples only:
  - RADIO_NRST 0.60 mm;
  - USB_DM 0.48 mm at VBUS_SENSE's via (16.6, 35.1);
  - QSPI_CLK 0.46 mm at the 3V3 via (28.75, 45.1);
  - QSPI_IO2 0.14 mm at QSPI_NCS's via;
  - SPI1_SCK's edge at the cluster;
  - GNSS_RF_ANT and RADIO_RF_ANT, 2.32 mm over their own launch cut-outs (intended).

  `refall.py` output is identical to pass 3's.

## 4. In2, references and split crossings

- **Regions.**
  - P4 5 regions and P5 4 nets.
  - The In2 GND outline is unchanged (2,686.8 mm²) and is one core at 0.4 mm erosion.
  - The 3V3 region keeps one core at 0.5 mm erosion and three at 1.0 mm, as pass 3 found.
  - The RAW_ACT islands are solid at 1.0 mm.
- **B.Cu non-power signals over In2** (centre line): GND 245.2 mm, 3V3 210.4 (pass 3: 212.4; −2.0 is CAM_PWR_EN's
  shorter leg), BAT_IN 5.3, RAW_ACT 0.8, crystal keep-out 4.6, antipads 43.1 mm.
- **Split crossings.** The same three as pass 3, at the same coordinates:
  - ARM1_SENSE, 3V3 → GND at (18.18, 53.86), after 14.52 mm over 3V3 (M3_R8 "Return paths", D47 / D70);
  - ACT_GATE, RAW_ACT → GND at (11.31, 105.97);
  - ACT_GATE, GND → BAT_IN at (12.41, 107.07).

  No critical net gained or lost a crossing.
- **Reference audit.** It is equal to pass 3's in every entry. 0 samples lie over another net's fill, a split or a
  void. Every unreferenced sample is at an own antipad (3,592), the crystal keep-out (1,368) or a neighbour's antipad
  (226). M3_R8's "Return paths" table and C6 (69 / 26 / 4 %) agree.
- **Critical vias** (28, `critvias.py`, identical output). Each has its nearest GND via within 0.71–1.47 mm, except:
  - A8 (PYRO1_GATE at (20.45, 92.4)): 2.72 mm, allowlisted;
  - NRST (24.0, 51.1): 2.93 mm, not an AGENTS §3 net.

  ARM1_SENSE_MCU (29.3, 47.5), beside the moved R172, keeps 0.71 mm.

## 5. Crystal, QSPI, SPI, USB, SWD

Fix pass 3 drew no copper in any of these return paths. The nearest edit is USB_LIMITED's B.Cu trunk, 5.3 mm forward of
the QSPI_IO1 via. It is a 0.45 A supply track over In2 3V3, and it touches neither In1 nor any critical track's
reference.

- **Crystal.** `Y1_In2_keepout` (x 18.9–26.8, y 46.3–50.95) and HSE_IN / HSE_OUT's 870 / 498 keep-out samples are
  unchanged. HSE_OUT's via (24.69, 47.5) keeps its GND partner at 1.25 mm, and HSE_IN's (22.0, 51.1) at 1.00 mm. Pass
  1's trade-off note on an In2 GND island in the keep-out (about 0.1–0.2 pF per node, Inference) still applies; it is
  not a finding.
- **QSPI.** Six dives with GND partners 0.78–1.27 mm. The B.Cu stubs over In2 3V3 are unchanged.
- **SPI1 / IMU.** The cluster is unchanged. Its GND partners are 0.88–1.47 mm away, the nearest at (10.6, 57.0) and
  (9.25, 57.1).
- **USB.** DP / DM run on F.Cu over solid In1. The D4.2 pocket still has 2.891 mm² and one via (C2, D63 / D68).
- **SWD.** F.Cu over In1 GND for its whole length.

## 6. GND pours: islands, fingers, stitching, D63 / D64

- **Islands.** 12 on F.Cu and 9 on B.Cu (21), with the same via, THT and pad counts per island as pass 3. Every island
  has ≥ 2 vias or holes except the D4.2 pocket (`WEAK_EXCEPT`).
- **Fingers.** `route_check.pour_pieces` gives the same counts:
  - 0.75 mm: 11 with rings kept, 6 with rings excluded;
  - 1.0 mm: 21 with rings kept, 14 with rings excluded.

  Only one piece moved: the B.Cu piece east of the RAW_ACT_SENSE lane (x 30.9–33.73, y 53.74–54.95) went from 2.36 to
  2.29 mm², and its copper distance from 4.30 to 4.24 mm. The worst copper distances are unchanged:
  - B.Cu round U13: 11.14 mm;
  - the F.Cu strip carrying Q122's pocket: 10.52 mm;
  - the In1 west edge: 9.97 mm.
- **Stitching.** P8 8.15 vias / cm² from 193 step-7 vias (89 grid, 54 cover, 25 fence, 16 return, 5 island, 2 stitch,
  1 C24, 1 pad).
- **D63 / D64** are unchanged and still hold:
  - P7 = 1;
  - P9 / P10 = 4.47 / 9.65 mm, against D64's floors of 4.32 / 9.42 mm and the gate ceilings of 4.6 / 9.7 mm;
  - P11 = 2.90 / 5.89 mm;
  - the maximum is still at (0.25, 88.25), under the triple-layer RAW_ACT band.

## 7. GND-pad copper reach (`gndpads.py`, 0.1 mm raster)

Identical to pass 3, every row:
- R123.2 13.06 mm and Q122.2 12.47 mm (F.Cu, C15 / D64);
- U13.2 9.31 mm and C93.2 7.24 mm (B.Cu, no legal spot);
- J9.2 7.00 mm and R102.2 5.39 mm;
- U9.8 2.57 mm and C81.2 3.56 mm (D102).

## 8. Findings

### R8P4-PLANES-01: Minor, worth fixing (records)
**R8_VALIDATION's scorecard records were not fully moved to fix pass 3. The P6 deviation row (C4) still gives 1752.5 mm,
the scorecard's value column is headed "R8 (fix pass 2)" over fix-pass-3 values, and the scorecard intro credits the P1
/ P6 moves to D106 / D107's B.Cu edits, which cannot change In1 or In2. The P1 and P6 moves come from D108's via shrink.**

- **Requirement.** AGENTS §3 asks that records state the board as built. REQUIREMENTS M2 asks that each deviation be
  listed with its *measured* reason.
- **Evidence.**
  - `docs/R8_VALIDATION.md` line 336, C4: "1752.5 mm against ≤ 900 mm". The same file's line 98 and
    `step9/evidence/fix3_scorecard.md` line 49 give **1752.2 mm**, as does my survey on `c84f00b8…`
    (`P6_in2_perimeter_mm 1752.2`).
  - Line 83: `| Metric | R7 | R8 (fix pass 2) | Target | Met |`. Its rows hold fix pass 3's values with fix pass 2's in
    parentheses, e.g. S1 "1497.6 mm (1499.6)" and P1 "0.9051 (0.905)".
  - Lines 78–80: "Fix pass 2's value is given in parentheses where fix pass 3 changed a row (S1, S2, S6, S7, S10, P1,
    P6: D106 / D107's shorter CAM_PWR_EN and the moved trunk)".
  - The copper diff puts D106 / D107 on B.Cu only, and the fill diff shows they change no In1 or In2 fill. The In1 / In2
    changes are:
    - R165's BAT_ENABLE via (16.6, 104.5), 0.6 → 0.5 mm (D108):
      - In1 GND antipad 0.958 → 0.791 mm², the whole P1 move (In1 4,861.74 → 4,861.91 mm²);
      - In2 BAT_IN antipad 1.139 → 0.958 mm², perimeter 3.795 → 3.479 mm, the whole P6 move (−0.3 mm).
    - The moved cover via's In2 3V3 antipad, which is area- and perimeter-neutral (0.792 mm² / 3.169 mm at both
      positions).
  - A wording nit in line 97 (P3b): "the SPI1 / IMU_CS via cluster under U4's pads". U4's pads end at y 55.05 and its
    courtyard at y 55.45. The slot is y 55.15–56.85 and the vias are at y 55.65–56.35, so the cluster lies just aft of
    U4's aft pad row (inside the courtyard edge only to y 55.45), not under the pads.
- **Effect.** Records only. The board, the gates and the scorecard values are right. A reader of C4 sees a figure that
  differs from the scorecard row beside it. The attribution would send a later reviewer looking at the wrong edit for a
  plane change.
- **Fix** (cheap, records only):
  1. C4: change "1752.5 mm" to "1752.2 mm", and add "(fix pass 2 1752.5; fix pass 3's 0.5 mm BAT_ENABLE via, D108,
     −0.3 mm)".
  2. Line 83: change the header to "R8 (fix pass 3)".
  3. Lines 78–80: change the attribution to "S1, S2, S6, S7, S10: D106 / D107's shorter CAM_PWR_EN and the moved
     trunk; P1, P6: D108's 0.5 mm BAT_ENABLE via (smaller In1 GND / In2 BAT_IN antipads)".
  4. Line 97: change "under U4's pads" to "beside U4's aft pad row".

## 9. Observations (not findings)

- **RAW_ACT_SENSE over an In2 antipad.** Since D106, RAW_ACT_SENSE's east edge runs 0.47 mm (was 0.15 mm) over the In2
  3V3 antipad of USB_LIMITED's hop via (31.25, 55.3). The net is a DC divider node behind 4.7 kΩ, not an AGENTS §3 net,
  so there is no consequence.
- **The 0.151 / 0.150 mm pour figure.** The records' 0.151 mm and the 0.150 mm from pass 3 and from this pass are the
  same 0.15 mm zone clearance, read by two methods (`min_gap` against a polygon point distance). No action is needed.
- **Unchanged pass-3 observations.** These stand as recorded:
  - U9's pad via at 0.176 mm from the RAW_PROTECTED trunk;
  - J123's island via, whose In2 3V3 antipad edge is 0.02 mm from PULLPIN's B.Cu edge;
  - ARM1_SENSE's 14.52 mm over 3V3;
  - D4.2's single via;
  - G7;
  - C88's bypass loop through two vias 1.94 mm apart.

## Method and scripts

The scripts are in the session scratchpad, `p4planes/`. Most are pass 3's (`p3planes/`), reused unchanged. All are
read-only on the board.
- `copperdiff.py`, `filldiff.py` (threshold 0.01 mm²), `holeat.py`: the diff against `990c8040…`, and the antipad area
  and perimeter at the changed vias.
- `plot.py`: B.Cu renders of the CAM_PWR_EN and trunk windows, before and after.
- `chref.py`: In2 / In1 net under every sample of the changed tracks. `nearvia.py`, `viaprobe.py`: the via beside the
  RAW_ACT_SENSE lane, and the moved cover via's connections and spacing.
- `zones.py`, `islands.py`, `fingers.py`, `gndpads.py`, `critvias.py`, `splitall.py`, `in1holes.py`, `necks.py`,
  `refall.py`, `b_over_antipad.py`: each run on `c84f00b8…` and diffed against pass 3's saved output.
- `padfill.py`: GND fill to the ACT_GATE / ACT_DRV pads. `u4.py`: U4's pads and courtyard against the In1 via cluster.
- Repository tools:
  - `tools/check.sh`;
  - `m3_design/r8_ground_check.py --report` (diffed against pass 3's report);
  - `step7/make_ground.py --built` (cmp against `r8_ground.tsv`);
  - `tools/reference_audit.py` (plain and extended, JSON diffed against pass 3's);
  - `tools/run_survey.sh` with the pass-3 board as base;
  - `tools/test_reference_audit.py` and `tools/test_r8_ground.py`.
