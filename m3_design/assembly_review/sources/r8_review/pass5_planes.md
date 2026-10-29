# R8 review pass 5: planes and return paths

Reviewer: independent, dimension "planes and return paths". Board under review: `m3_design/assembly_review/m3.kicad_pcb`,
SHA-256 `cc044ea0922ff826df19af9d9726d92c096ab2b127025b55d123d8772e5fb4a7` (fix pass 4), netlist `0cc1ed69…`.

I hashed the board before and after the review, and it is unchanged. `git status --short` is also identical before and
after my runs. I edited nothing in the repository except this file.

For the diffs I rebuilt the pass-4 board `c84f00b8…` in the session scratchpad, from commit `431025d` plus the
coordinator's backup (`r8_backup_c84f00b8/tracked.diff`, only the board's hunk). I hash-checked the rebuild
(`c84f00b88f5f…`) and deleted it after use.

## Verdict

**0 Critical, 0 Major, 1 Minor (records, not worth fixing on its own).**

- **Pass 4's finding is closed.** R8P4-PLANES-01 is closed in the records (section 1).
- **Fix pass 4 caused no plane regression.**
  - Ignoring UUIDs, the board's diff against `c84f00b8…` is exactly the two intended items:
    - D110: the radio trio's below-fence lanes, plus three GND vias moved 0.05 mm;
    - D111: the USB_LIMITED T at R87.1.
  - Footprints, zone outlines and zone settings, the board setup and every graphic are equal.
  - Each fill change follows from those two edits (section 2).
- **Both edits improved the pours slightly.**
  - The F.Cu GND sliver in the MISO–MOSI slot widens from 0.495 to 0.595 mm, which is now above the gate's 0.5 mm
    finger width.
  - The B.Cu sub-0.5 mm piece between USB_LIMITED's trunk and its old R87.1 branch is gone. The local worst GND reach
    there drops from 5.58 to 5.09 mm.
- **Every critical reference, split crossing, critical via partner, In1 hole, island via count, finger list and GND-pad
  reach is equal to pass 4's.**
- **The finding.** R8_VALIDATION's scorecard intro says "no P, R or D row moved", but R7 (extended reference samples)
  moved from 102,384 to 102,408. The paragraph discloses that move itself a few lines later.

## Gates and tools run (on `cc044ea0…`)

| Run | Result |
|---|---|
| `tools/check.sh` | **Exit 0.** DRC 0, unconnected 0, parity 0, ERC 0; metadata / 3D OK; silk 0 points outside; R8 contract OK; route_check r8 0 failing, 3 allowlisted, 0 stale, 0 leftovers, 0 removable (22 bump windows); check_actuators OK; fit OK |
| `m3_design/r8_ground_check.py --report` | **All 14 gates OK.** Reach: board p95 4.47 / max 9.65 mm at (0.25, 88.25); pours p95 2.90 / max 5.89 mm (16,619 points). Islands 21; the one weak island is D4.2's (F.Cu, 2.891 mm², 1 via). The JSON differs from pass 4's only in the board SHA, the two fence openings' x (19.95–22.05 and 22.05–24.15, both now 2.10 mm), pour points 16,618 → 16,619, and route_check's `width_change_junction` 14 → 15 (D111's T) |
| `step7/make_ground.py <board> --built` | 201 rows (fence 25, stitch 2, c24 2, trim 7, return 16, grid 89, cover 54, island 5, pad 1); **byte-identical** to `m3_design/r8_ground.tsv` |
| `tools/reference_audit.py` (R6 set / extended) | R6 set: 46,845 samples, 5,186 unreferenced (11.07 %); own via 3,592, keep-out 1,368, other via 226. **The JSON equals pass 4's in every key.** Extended: 102,408 / 5,944 (5.80 %). The only change is `RADIO_MISO_MCU F.Cu` samples 8,400 → 8,424; the unreferenced count is unchanged |
| `NO_GATE=1 NO_DC=1 tools/run_survey.sh <board> <out> <c84f00b8 board>` | P1 0.9051, P2 1, P3 16, P3b 4, P4 5, P5 4, P6 1752.2 mm, P7 1, P8 8.15 / cm², P9 / P10 4.47 / 9.65 mm, P11 2.90 mm; R1 / R3 2.9 / 2.9 mm; R6b 0.1107; S12 25, S13 0; C6 1. `critical_reference.py c84f00b8 cc044ea0`: **0 samples lost** (R6 set and extended). `survey.json` against pass 4's: the planes keys that moved are F.Cu GND area 3,353.8 → 3,354.1 mm² and B.Cu GND area 3,430.2 → 3,431.0 mm² (with their coverage / perimeter), plus `outer_pour_points`. In1, In2, islands, voids, slots and stitching are equal |
| `tools/test_reference_audit.py`, `tools/test_r8_ground.py` | 14 tests OK |
| Own scripts (pcbnew, read-only; listed at the end) | Top-level item diff with and without UUIDs; copper and fill diffs; zone inventory; islands with their vias; fingers at 0.75 / 1.0 mm both ways; every thin piece (0.5 / 0.75 / 1.0 mm) of the GND, 3V3, BAT_IN and RAW_ACT pours on all four layers; GND-pad copper reach; critical vias with GND partners; full critical-net split sampling; B.Cu over foreign In2 antipads; In1 holes; In2 erosion; per-track reference (centre line and both edges every 0.01 mm) under every changed track; connection probes at the three moved vias; via-to-track edge gaps; local through-copper GND reach at both edits |

## 1. Pass-4 finding in this dimension

| Pass-4 item | Status on `cc044ea0…` | Evidence |
|---|---|---|
| R8P4-PLANES-01: stale scorecard records after fix pass 3 (C4 1752.5 mm; column header "R8 (fix pass 2)"; the P1 / P6 moves credited to D106 / D107; P3b's cluster "under U4's pads") | **Closed** | All four parts are fixed in `docs/R8_VALIDATION.md` (see below). The disposition row is line 342 |

The four parts in `docs/R8_VALIDATION.md`:
1. **C4** (line 410) reads "1752.2 mm … fix pass 2 1752.5 … fix pass 3 −0.3 mm by D108's 0.5 mm BAT_ENABLE via,
   R8P4-PLANES-01". This matches the survey (`P6_in2_perimeter_mm 1752.2`).
2. **The column header** (line 97) reads "R8 (fix pass 4)". The column now holds fix pass 4's values.
3. **The attribution.** The intro (lines 87–94) now credits only S / C2 rows to D110 / D111. Line 122 credits fix pass
   3's "P1 0.905 → 0.9051, P6 1752.5 → 1752.2 mm" without naming D106 / D107.
4. **P3b** (line 111) reads "beside U4's aft pad row".

## 2. What fix pass 4 changed on the planes

### Board diff against `c84f00b8…` (`topdiff.py`, `copperdiff.py`)

I parsed every top-level item of both files with the zone fills stripped.

**Ignoring UUIDs**, 16 items were removed and 15 added. All of them are D110 / D111 copper:
- **RADIO_RXEN / RADIO_BUSY / RADIO_MISO_MCU (F.Cu):** three segments each, x 20.6 / 21.1 / 21.6 → 20.5 / 21.0 / 21.5. The
  steps now end at y 22.5 / 22.707 / 22.914, and the 45° runs to U1 are on the same lines.
- **Three GND vias (0.5 / 0.3 mm):** (20.0, 23.3) → (19.95, 23.3), (22.1, 23.3) → (22.05, 23.3), and (22.1, 26.7) →
  (22.05, 26.7).
- **USB_LIMITED (B.Cu):**
  - removed: trunk (31.25, 55.3) → (34.35, 55.3), and the branch (35.25, 56.2) → (32.7, 56.2) → (32.2, 56.7) →
    (32.2, 57.775);
  - added: the trunk split at (32.2, 55.3) and the drop (32.2, 55.3) → (32.2, 57.775), 0.25 mm wide.

Nothing else changed: no footprint, pad or zone connection, zone outline or zone setting, board setup, graphic or text.

**With UUIDs** there are 215 / 214 items. The extra 199 differ only in their `uuid`: 35 `gr_text`, 6 `gr_circle`, 22
GND vias and 136 other-net tracks and vias, mostly 3V3, VLOGIC, 3V3A and CAM_*. `r8_build.sh` uses a fixed KIID seed,
so items emitted after an edited one take new identifiers. Their geometry is identical. This has no plane or
fabrication effect, and I note it for the integrity dimension only.

### Fill diff, by plane (`filldiff.py`, threshold 0.01 mm²)

| Layer / net | Change | Cause |
|---|---|---|
| In1 GND | **none** (4,861.91 mm², one outline; P1 0.9051) | The moved vias are GND vias, which have no In1 antipad |
| In2 3V3 | 0.05 mm² lost at x 21.55–22.03 and 0.05 mm² gained at x 22.12–22.60, y 26.20–27.20 | The stitch via's antipad moved 0.05 mm west. The area is neutral (1,513.8 mm²). The erosion cores are equal to pass 4's except the largest 1.0 mm core, 585.6 → 585.5 mm² (`necks.py`) |
| In2 GND, BAT_IN, RAW_ACT | none | The two fence vias sit in In2 GND, which joins them (16 / 16 probes at r 0.3 mm) |
| F.Cu GND | −0.46 mm² at x 20.11–20.75, +0.70 mm² at x 21.75–22.13 (zone 3,353.8 → 3,354.1 mm²) | The trio's 0.1 mm westward shift. The MISO–MOSI slot's island widens (below) |
| B.Cu GND | −0.37 mm² at the new drop, +1.25 mm² at x 32.48–34.66, y 55.79–56.86 (zone 3,430.2 → 3,431.0 mm²) | D111: the pour fills the old branch's wedge |

### The three moved vias (`viaprobe.py`, `viagap.py`)

**Connections.** All three are joined to GND on F.Cu, In1 and B.Cu.
- The fence vias are also joined to In2 GND.
- The stitch via (22.05, 26.7) keeps its In2 3V3 antipad, as at (22.1, 26.7).
- F.Cu contact improved from 10 / 16 to 14 / 16 probes at both slot vias. The slot island is wider (below).

**Edge gaps.**
- RXEN to (19.95, 23.3) is 0.200 mm (was 0.250).
- RADIO_MISO_MCU and RADIO_MOSI to (22.05, 23.3) and to (22.05, 26.7) are 0.200 mm each (were 0.150).

These match D110 and `fix4_measurements.json`.

**The fence row.** Its openings are now 1.75 / 2.10 / 2.10 mm, against D16's ≤ 2.7 mm. The ground gate's contract
evidence lists the lanes per opening. At 0.9–1.6 GHz a 2.1 mm opening is far below λ/20 in FR-4 (Inference: about 9 mm
at 1.6 GHz).

## 3. In1

- **The plane.** One GND outline, 4,861.9 mm² (P2 1). There is no In1 track (S16 0).
- **Holes.** 196 holes, 305.4 mm². The list is identical to pass 4's (`in1holes.py` output equal):
  - the J121 / J124 / J1 / J122 barrels;
  - the J30 / J31 launch cut-outs;
  - J123;
  - J3's legs 1 and 4;
  - the SPI1 / IMU_CS cluster.
- **The changed F.Cu lanes** (`chref.py`, every 0.01 mm, centre and both edges): all over In1 GND, with no transition.
  - RXEN 7.90 / 0.71 / 8.49 mm;
  - BUSY 7.49 / 0.71 / 8.49 mm;
  - MISO_MCU 7.07 / 0.71 / 8.49 mm.
- **`refall.py`.** Its unreferenced and crossings JSON is identical to pass 4's. The only text change is the three
  lanes' F:GND lengths: BUSY 32.20 → 32.28, MISO_MCU 28.10 → 28.18 and RXEN 40.30 → 40.36 mm.

## 4. In2, references and split crossings

- **Regions.** P4 5 regions, P5 4 nets. The In2 GND outline is unchanged (2,686.8 mm², one core at 0.4 mm erosion). The
  3V3 region keeps one core at 0.5 mm erosion. The RAW_ACT islands are solid at 1.0 mm.
- **B.Cu non-power signals over In2** (centre line), equal to pass 4's: GND 245.2 mm, 3V3 210.4, BAT_IN 5.3, RAW_ACT
  0.8, crystal keep-out 4.6, antipads 43.1 mm. `b_over_antipad.py` output is identical: no B.Cu signal lies over the
  moved stitch via's antipad.
- **USB_LIMITED's new copper** (a 0.45 A supply, not an AGENTS §3 net): the 2.48 mm drop and the trunk east of the T are
  all over In2 3V3.
- **Split crossings.** The same three as pass 4, at the same coordinates (`splitall.py` output identical):
  - ARM1_SENSE, 3V3 → GND at (18.18, 53.86);
  - ACT_GATE, RAW_ACT → GND at (11.31, 105.97);
  - ACT_GATE, GND → BAT_IN at (12.41, 107.07).
- **Reference audit.** Equal to pass 4's (section "Gates"). 0 samples lie over another net's fill, a split or a void.
  Every unreferenced sample is at an own antipad, the crystal keep-out or a neighbour's antipad. M3_R8's "Return paths"
  table (line 331) records the extended set's +24 samples correctly.
- **Critical vias** (28, `critvias.py`): the output is identical to pass 4's. A8 (PYRO1_GATE) is the only one beyond
  1.5 mm (2.72 mm, allowlisted). NRST is at 2.93 mm and is not an AGENTS §3 net. S13 is 0 and C6 is 1.

## 5. Crystal, QSPI, SPI, USB, SWD

Fix pass 4 drew no copper in any of these return paths. The nearest edit is D111's T at (32.2, 55.3), on B.Cu over In2
3V3, more than 12 mm from the nearest QSPI via. D110's lanes are the radio's control and MISO lines, F.Cu over solid In1.

- **Crystal.** `Y1_In2_keepout` is unchanged, and HSE_IN / HSE_OUT keep 870 / 498 keep-out samples.
- **QSPI and SPI1 / IMU.** Their own-via samples are unchanged, and so are their GND partners (`critvias.py` equal).
- **USB.** DP / DM run on F.Cu over In1 GND. The D4.2 pocket still has 2.891 mm² and one via.
- **SWD.** F.Cu over In1 GND for its whole length.

## 6. GND pours: islands, fingers, stitching, D63 / D64

### Islands (`islands.py`)

There are 12 on F.Cu and 9 on B.Cu, with the same via, THT and pad counts per island as pass 4. Three areas moved:
- F.Cu isl4 (the strip-side pour) 528.52 → 528.06 mm²;
- F.Cu isl9 (the MISO–MOSI slot) 3.47 → 4.16 mm², still 2 vias;
- B.Cu isl1 1,056.29 → 1,057.16 mm².

Every island has ≥ 2 vias or holes except the D4.2 pocket (`WEAK_EXCEPT`, D63).

### The MISO–MOSI slot island (`slot.py`)

This is the F.Cu GND strip between RADIO_MISO_MCU (x 21.5) and RADIO_MOSI (x 22.6), y 22.53–30.19.
- **Width.** It is now 0.595 mm wide from y 23.0 to 28.0 (was 0.495 mm). It narrows to 0.425 mm at y 29, beside the
  MOSI series part, and tapers to its tip at y 30.19.
- **Stitching.** It is stitched by the fence via (22.05, 23.3) and the stitch via (22.05, 26.7). The tip is 3.5 mm of
  copper beyond the second via, inside the gate's 4.0 mm.
- **The gate's finger width.** At route_check's 0.5 mm `FINGER_W`, the whole 7.68 mm strip used to be a thin piece. Now
  only the 1.64 mm taper (0.56 mm²) and a 0.59 mm piece at the fence end are (`thinall.py`).

### Every thin piece (`thinall.py`)

I listed the thin pieces at 0.5 / 0.75 / 1.0 mm of GND, 3V3, BAT_IN and RAW_ACT on all four layers: 1,921 → 1,919.
Every difference is at the two edits:
- **B.Cu.** The pieces between the trunk and the old branch are gone:
  - 0.5 mm: x 32.31–34.36, y 55.65–56.04, 0.51 mm²;
  - 0.75 mm: 0.60 mm²;
  - 1.0 mm: 0.76 mm² and 0.07 mm².

  One 1.0 mm piece of 0.09 mm² was added, at x 31.38–31.92, y 55.65–56.17, between the hop via (31.25, 55.3) and the
  new drop.
- **F.Cu.** The slot island described above. The piece near (20.0, 26.5), between RXEN's diagonal and the pour edge,
  moved 0.1 mm west with the same size.

No new piece appears anywhere else.

### Fingers (`fingers.py` = `route_check.pour_pieces` with reach)

The counts are equal to pass 4's, piece for piece:
- 0.75 mm: 11 with rings kept, 6 with rings excluded;
- 1.0 mm: 21 with rings kept, 14 with rings excluded.

The worst copper distances are unchanged: B.Cu round U13 11.14 mm, the F.Cu strip carrying Q122's pocket 10.52 mm, and
the In1 west edge 9.97 mm. C15's F / B counts (10 / 17 rings kept; 6 / 14 rings excluded on every layer) match.

(Pass 4's `f075.txt` / `f075r.txt` file names were swapped against the script's flag, but their contents are equal to
mine, matched by label.)

### Local reach at the edits (`localreach.py`, `route_check.gnd_reach`, 0.05 mm raster)

- B.Cu x 31.5–35, y 55.5–57.5: max 5.58 → **5.09 mm**, with no unreached point.
- F.Cu x 19–23, y 22–31: max 3.25 mm, unchanged.

### Stitching

P8 is 8.15 vias / cm², from 428 GND vias. The step-7 table has the same 201 rows and 193 vias, and only three via
coordinates changed.

### D63 / D64

Both still hold:
- P7 = 1 (D4.2);
- P9 / P10 = 4.47 / 9.65 mm, against D64's floors of 4.32 / 9.42 mm and the gate ceilings of 4.6 / 9.7 mm;
- P11 = 2.90 / 5.89 mm, against 3.5 / 7.0 mm;
- the maximum is still at (0.25, 88.25), under the triple-layer RAW_ACT band.

## 7. GND-pad copper reach (`gndpads.py`, 0.1 mm raster)

Identical to pass 4, every row:
- R123.2 13.06 and Q122.2 12.47 mm (F.Cu, C15 / D64);
- U13.2 9.31 and C93.2 7.24 mm (B.Cu, no legal spot);
- J9.2 7.00 and R102.2 5.39 mm;
- U9.8 2.57 and C81.2 3.56 mm (D102).

## 8. Findings

### R8P5-PLANES-01: Minor, not worth fixing on its own (records)

**The scorecard intro in R8_VALIDATION says "no P, R or D row moved" in fix pass 4, but an R row did. R7, the extended
reference sample count, went from 102,384 to 102,408. The same paragraph lists that move a few lines later, and
`fix4_handoff.md` repeats the contradiction.**

- **Requirement.** AGENTS §3 asks that the records state the board as built.
- **Evidence.**
  - `docs/R8_VALIDATION.md` line 93: "no P, R or D row moved (D110 moved three GND vias 0.05 mm …)".
  - Lines 119–120 of the same file: "Other rows that moved in fix pass 4: … R7 extended reference samples 102,384 →
    102,408".
  - `step9/evidence/fix4_scorecard.md` line 41: `R7_cref_ext_samples | 102408`.
  - `sources/r8_review/fix4_handoff.md` line 57: "Every P, R and D row equal", after line 56 lists "R7 extended samples
    102384 → 102408".
  - My survey: `R7_cref_ext_samples 102408`. The 24 samples come from RADIO_MISO_MCU's 0.08 mm longer lane (reference
    audit: `RADIO_MISO_MCU F.Cu` 8,400 → 8,424), and none of them is unreferenced.
- **Effect.** None on the board. Every P row, R1–R6b, R8 and every D row is equal, and the statement is only off by the
  one count row, which the paragraph itself discloses.
- **Fix** (records, one phrase; fold it into the next records edit): line 93, "no P or D row moved, and of the R rows
  only R7's sample count (+24 on RADIO_MISO_MCU's longer lane, none unreferenced)". Make the same change in
  `fix4_handoff.md` line 57.

## 9. Observations (not findings)

- **UUID churn.** Fix pass 4's board gives new `uuid`s to 199 items whose geometry did not change, because the build's
  KIID seed is fixed and the sequence shifts after an edited item. There is no plane, fabrication or gate effect. It is
  noted for the integrity reviewer, who owns build reproducibility.
- **The MISO–MOSI GND strip.** At 0.595 mm × 7.7 mm it is still a narrow F.Cu island. It is stitched twice, its tip is
  3.5 mm from the nearer via, and it is wider than the gate's 0.5 mm finger width. It acts as a guard between the radio
  MISO and MOSI lanes (Inference: it adds coupling isolation and costs nothing). No action.
- **Unchanged pass-3 / pass-4 observations.** These stand as recorded:
  - RAW_ACT_SENSE's 0.47 mm over USB_LIMITED's hop-via antipad;
  - U9's pad via 0.176 mm from the RAW_PROTECTED trunk;
  - J123's island-via antipad;
  - ARM1_SENSE's 14.52 mm over 3V3;
  - D4.2's single via;
  - G7;
  - C88's two-via bypass loop;
  - the crystal keep-out trade-off (pass 1; Inference).
- **C15's distance figures.** C15 gives 10.3 / 9.9 mm for the Q122 strip and the In1 west edge. They come from fix pass
  2's method; `fingers.py` gives 10.52 / 9.97 mm. Both are unchanged since pass 3, and the difference lies in the method
  (raster and window). No action.

## Method and scripts

The scripts are in the session scratchpad, `p5planes/`. Most are pass 4's (`p4planes/`), reused unchanged. All are
read-only on the board.

**New for this pass:**
- `stripfill.py` + `topdiff.py`: the top-level item diff with fills stripped, with and without UUIDs, and the UUID-only
  classification.
- `slot.py`: the slot island's width profile and its thin pieces.
- `thinall.py`: every thin piece of four nets on four layers at three widths.
- `viagap.py`: edge gaps of the moved vias.
- `localreach.py`: `route_check.gnd_reach` around each edit.

**Reused from pass 4:**
- `copperdiff.py`, `filldiff.py`, `viaprobe.py`, `chref.py`;
- `zones.py`, `islands.py`, `fingers.py`, `gndpads.py`, `critvias.py`, `splitall.py`, `in1holes.py`, `necks.py`,
  `refall.py`, `b_over_antipad.py`. Each was run on `cc044ea0…` and diffed against pass 4's saved output;
- `plot.py`: F.Cu renders of x 18–25, y 20–32 and B.Cu renders of x 30–36.5, y 53–59, before and after.

**Repository tools:**
- `tools/check.sh`;
- `m3_design/r8_ground_check.py --report` (diffed against pass 4's report);
- `step7/make_ground.py --built` (cmp against `r8_ground.tsv`);
- `tools/reference_audit.py`, plain and extended (JSON diffed against pass 4's);
- `tools/run_survey.sh`, with the `c84f00b8…` board as base (`survey.json` diffed against pass 4's);
- `tools/test_reference_audit.py` and `tools/test_r8_ground.py`.
