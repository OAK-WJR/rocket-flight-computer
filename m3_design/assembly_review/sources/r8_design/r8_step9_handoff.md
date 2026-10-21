# R8 build step 9 handoff: requalification and records

Step 9 of `r8_plan.md` section 3 (Strategy B): every qualification survey_constraints section 13 lists as invalidated by a
re-placement, re-measured on the final board, and the records rewritten for R8. Decisions D74–D84 in `R8_DECISIONS.md`
(plus a correction note on D3's buzzer figure); the running log is `r8_step9_progress.md`. Nothing was committed or pushed.

## Result

- **Board unchanged:** `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
  `429b6db4dc95c1a0fd3e736625c416c20fa0e7fc72f6f6c9c576003340dc1987` (step 8's). Step 9 changed no build input; a full
  `m3_design/r8_build.sh` run at the end of the step reproduced the board, the sheets and the netlist byte for byte and
  ended with `tools/check.sh` exit 0 (step-9 rebuild: 15 sheets, schematic.net.xml and m3.kicad_pcb SHA-256 identical before and after; board `429b6db4…`).
- **`tools/check.sh` exit 0** on the final board (step-9 run before the rebuild, and inside the rebuild): DRC 0 at every
  severity, unconnected 0, parity 0, ERC 0; metadata / 3D audit OK; silkscreen in the outline; check_r8 OK; route_check
  r8 0 failing, 3 allowlisted (A8, D51 × 2), 0 leftovers; check_actuators OK; fit_check OK.
- **Every invalidated item is closed with evidence or listed as a bench / owner item** (R8_VALIDATION "Requalification"):

| Item | Result on `429b6db4…` |
|---|---|
| F4 DC at 0.05 mm with IPC-2152 | RAW_ACT 1.45 mΩ, neck 5.94 mm F.Cu, 17.5 °C; BAT_IN 0.42 mΩ, 7.00 mm B.Cu, 14.5 °C; ACT_FET_S 0.18 mΩ, 4.97 mm B.Cu, 21.5 °C: all within D12 (R7 38 / 30 / 44 °C). 25 supply paths at 0.1 mm, every drop < 26 mV at its load |
| Absolute critical reference | new `tools/reference_audit.py`: 47,769 samples, 5,525 unreferenced (11.57 % = R6b): own via antipads 3,589, the crystal's In2 keep-out 1,710, other vias' antipads 226; **0 over another fill, a split or a void** (R7: 27.9 %, 11,516 such samples) (D74) |
| Pyro exits, rule margins | every DRC pyro rule's closest approach listed (A 0.501 at a pour edge, E 1.30, F 0.501, H 1.025 mm ...); exits on B.Cu with no In2 hop; 7 non-pyro nets within 3 mm of armed copper (R7: 23) |
| Coating and leakage | rigid block: bare gate to bare bus / igniter 1.03–2.00 mm (= R7; ORDERING's old "0.79 mm" was R4's PYRO2); no bare 3V3 / RAW_ACT pad within 5 mm of a pyro gate pad; 40 tented GND vias in PYRO_BLOCK (34 new), nearest armed copper 0.52 mm (rule D) |
| A8 | TP122's via: hole 0.60 mm inside the pad, nearest GND via 2.717 mm, nearest foreign copper 1.001 mm: the allowlist reason holds |
| RF tables | strip rigid (field solve, launch, stitching carry over); nearest RF part to a restricted part R306–U1 5.94 mm; modules ≥ 43 mm from the logic buck; radio lines near U30 ≥ 5.44 mm (DIO1 / NRST now 16.8 / 19.3 mm); fast copper ≥ 11.2 mm from U30 |
| Vibration | `step9/plate_model.py` (pass 2's code; reproduces R7 exactly): f1 209 / 295 / 346 / 490 Hz with the sled carrying the plugs, 6–8 % below R7; cause C84 on the mode-1 antinode (D75) |
| F9 hot-plug premise | protection parts within 4.6–10.6 mm of J1.1; `step9/hotplug_feed.py`: U9's 27 mm feed (≈ 4.2 nH) adds ≤ 0.002 V and 0.8 % slew at U9 IN (Inference) (D76) |
| IMU axis map | unchanged (bottom, rotation 0, pad 1 at (−1.21, +0.75)); lever arm x −13.0 mm, sign flipped (D77) |
| Firmware binding | note `step9/r8_binding_note.json`: hashes, U1 map checked against the pin table, 27 changed pins, D6 / D27 constraints, IMU (D78) |
| Electrical inferences | TXU0202 A-port output referenced to VCCA = 3V3 (TI SCES942A) (D80); buzzer 4.0 ± 0.2 kHz (Huaneng) (D79) |

## Files

New:
- `docs/M3_R8.md` (design record), `docs/R8_VALIDATION.md` (build summary, hard gates, scorecard, requalification table,
  the R8 deviation list for owner acceptance, open items).
- `tools/reference_audit.py` (absolute critical-reference audit) and `tools/test_reference_audit.py` (3 tests).
- `sources/r8_design/step9/`: `dump_board.py`, `requalify.py`, `pyro_neighbours.py`, `plate_model.py`, `hotplug_feed.py`,
  `run_supply_dc.sh`, `binding_note.py`, `r8_binding_note.json`, and `evidence/` (DC outputs, requalify / neighbour /
  reference / plate / hot-plug JSON for R8 and R7, check_r8 and route_check reports, the quick scorecard; local paths
  scrubbed).
- `r8_step9_progress.md`, this handoff.

Changed:
- `STATUS.md`: R8 the current candidate (new section); R7 "owner-accepted, orderable fallback" (and its commit line).
- `AGENTS.md` section 1: the column is R8's, rows updated; section 3's silkscreen rule points at M3_R8 and check_r8.
- `docs/REQUIREMENTS.md`: F4 (the R8 solve; R7's C1 acceptance), F10 (check_r8, gap figures, fence), P1, P2, M2 (J2.1
  exception lapsed, R8 list not accepted), M3 (R8 cost run), new "R8 acceptance" section.
- `docs/ORDERING.md`: now R8's (title, cost and stock, via covering, five tabs and no forward rail, order mark, assembly
  counts, hole fill, rail-removal cautions, coating and leakage figures, NRST probe, staking, hot-plug probe point,
  tap-check estimate, sled pours and tie channel, washer clearances). R7's version stays at 431025d.
- `docs/MARGIN_PRESCRIPTION.md`: P1-9 R8 status; R14 (R7) R8 note.
- `R8_DECISIONS.md`: step-9 block D74–D84; D3's buzzer figure annotated.

## How it was verified

- `tools/check.sh` exit 0 on `429b6db4…` (before the rebuild; the board SHA was unchanged after it) and again inside the
  final rebuild.
- Full rebuild (`m3_design/r8_build.sh`) at the end of the step: the 15 sheets, schematic.net.xml and m3.kicad_pcb SHA-256 identical before and after (board `429b6db4…`); its closing `tools/check.sh` exit 0.
- Tests (KiCad Python): 269 tests in 17 suites, all OK (step 8's 266 + `test_reference_audit` 3); quality_audit 21 OK under
  KiCad's Python and python3.
- `reference_audit.py` count equals `critical_reference.py BOARD BOARD` (5,525 / 47,769 and 6,283 / 103,308), asserted in
  its test.
- `plate_model.py` reproduces pass2_mechanical's R7 figures exactly (frequencies) and within 2 % (strains).
- Every R8 measurement was also taken on R7 (git 431025d) with the same script for comparison.
- Datasheets read for the closed Inferences: TI TXU0202 SCES942A (§7.1 p. 5, §7.5 p. 8, pin table p. 4); Huaneng MLT-5020
  (LCSC C94598, items 5 and 9).

## Reproduce

```bash
cd rocket-pcb/rocket-flight-computer-r8
KPY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
D=m3_design/assembly_review/sources/r8_design/step9
B=m3_design/assembly_review/m3.kicad_pcb
shasum -a 256 $B                                                      # 429b6db4dc95c1a0...
bash tools/check.sh                                                   # exit 0
tools/run_dc.sh $B /tmp/dc005 0.05                                    # ~40 min; the three 7.7 A necks, D12 verdicts
bash $D/run_supply_dc.sh $B /tmp/dc_supply 0.1                        # ~60 min (the 3V3 rows are slow)
PYTHONUNBUFFERED=1 $KPY -I tools/reference_audit.py $B [--extended]   # 5 s each
PYTHONUNBUFFERED=1 $KPY -I $D/requalify.py $B /tmp/req_r8.json        # ~1 min
PYTHONUNBUFFERED=1 $KPY -I $D/pyro_neighbours.py $B /tmp/nb_r8.json
PYTHONUNBUFFERED=1 $KPY -I tools/fit_check.py $B --report /tmp/fit.json
python3 -m venv /tmp/venv && /tmp/venv/bin/pip install numpy          # plate and hot-plug scripts need numpy
/tmp/venv/bin/python $D/plate_model.py /tmp/fit.json --label R8
/tmp/venv/bin/python $D/hotplug_feed.py
PYTHONUNBUFFERED=1 $KPY -I $D/binding_note.py $B $D/r8_binding_note.json
(cd tools && PYTHONUNBUFFERED=1 $KPY -m unittest test_reference_audit)
# R7 comparison: git show 431025d:m3_design/assembly_review/m3.kicad_pcb > /tmp/r7/m3.kicad_pcb (with the .kicad_pro /
# .kicad_dru and a kilib link beside it for fit_check), then the same commands on it.
```

## What the next steps must know

1. **The review loop (r8_plan section 4) has not run on R8.** Start it on `429b6db4…`; R8_VALIDATION is its input.
   Items worth a reviewer's attention:
   - C10 (vibration): f1 6–8 % below R7's because C84 moved to the right edge's mode-1 antinode; moving C84 toward a
     support recovers about 17 Hz but re-opens power / routing stages. Owner or review decision; not escalated (inside the
     100 g design load, Inference; no requirement sets an f1 floor).
   - Pyro observations (DRC-legal): the RAW_ACT F.Cu pour at rule A's 0.5 mm from C127.1 (R7 0.95 mm); the ACT_FET_S B.Cu
     pour at rule F's 0.5 mm from J124.1's bottom ring (R7 had BAT_IN there at 0.501 mm on B.Cu and In2). Both under mask.
   - J123: rotation 0 as in R7 but now at (12.2, 75.4); R7's ORDERING said "the PH latch faces inboard". The latch side is
     the same board direction as R7's, which is no longer "inboard" in y if that is what R7 meant (unverified which side
     the latch is on); fit_check passes with the mated envelope and the plug is RTV-retained. A reviewer may confirm the
     latch side does not matter (Inference that it does not).
2. **Owner items:** the dated acceptance of R8_VALIDATION "R8 deviations for owner acceptance" (3 allowlist entries, 10
   review rows, 93 information instances); a ruling on C10.
3. **Before ordering R8:** U4 consigned; JLC's acceptance of five long-edge tabs on a 118 mm board without a forward rail
   (D35, Inference); `FAB_NET=1 m3_design/r8_fab.sh` within 24 h. Until R8 is accepted, R7 (431025d) is the board to
   order.
4. **Firmware:** start an R8 binding from `step9/r8_binding_note.json` (not from the R1 chain).
5. **Scorecard suggestion (not done; the plan's targets are not this step's to change):** add the reference audit's
   "over another fill / split / void" share (0 on R8) beside R6b, which mostly counts own-via antipads and the deliberate
   crystal keep-out.

## Proposed parent VEHICLE.md stack-row update (D84; not applied)

In the parent repository's `docs/VEHICLE.md` (`../../docs/VEHICLE.md` from this repository), row "Main-section stack, bulkplate up", replace the flight-computer
clause with:

> flight computer board 118 (M3-ASSY-R8, the current candidate; M3-ASSY-R7, the owner-accepted fallback, has the same
> outline, holes, jacks and J1: 46 × 118 mm, parts on both sides; two edge-launch SMA jacks overhang its aft edge by
> 9.5 mm; J1's battery-wire entry faces the forward edge; it fits the Ø50.8 mm coupler bore along its whole length; the
> sled puts the board's top face on the bore axis on nylon standoffs ≥ 3.5 mm tall at the five M3 holes (4, 4),
> (42.3, 4), (4, 64), (4, 114.4) and (42, 114.4) mm, clears the bottom parts, which hang up to 3.0 mm below the board,
> is non-conductive under the whole bottom face, and carries both SMA plugs about 25–30 mm aft of the board edge)

Every number is unchanged from the R7 row (measured on R8: outline, holes and jacks rigid; deepest bottom part L1 3.02 mm);
it adds the two clauses STATUS already proposed for R7 (J1's forward entry, standoffs ≥ 3.5 mm). The parent repository's
rule is to commit and push knowledge changes there; that is the coordinator's call, not this step's.

## Left open

1. The r8_plan section 4 independent review loop on R8 (none has run).
2. The owner's acceptance of the R8 deviation list (M2) and a ruling on C10.
3. Bench and physical tests: none (STATUS "Needs the bench": hot-plug at U9 IN, CAM_5V remote sense, IMU signs with the new
   lever arm, tap check against 209–490 Hz, the thermal-camera stall test, every R7 bench item).
4. R8 firmware binding (note only).
5. The parent VEHICLE.md row (proposed above, not applied).
