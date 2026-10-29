# R8 step 2 progress log (schematic)

Resume from the last entry. Outputs: `m3_design/r8_sch.py` (idempotent R7 -> R8 schematic transform), the edited
schematic sheets and `schematic.net.xml`, R8_DECISIONS additions (if any), `r8_step2_handoff.md`.

Scratch: `$SCRATCH/step2/` (session scratchpad; probes only, delete when done).

## Log

1. Read r8_plan, R8_DECISIONS D1-D23, step-0 and step-1 handoffs/progress, AGENTS, r7_sch.py (the R6 -> R7 transform
   this step mirrors). No step-2 log existed: fresh start.
2. Survey: U1's 100 pins on mcu.kicad_sch are each a short wire + global label or a no-connect flag (R7 style); all
   U1 connections live on the MCU sheet, so other sheets need note edits only. R310.1 is a global label on the
   telemetry sheet. TH1-TH3 are not schematic parts (D8: nothing to do). D121 channel map already as D7 wants (no net
   change). The committed R7 netlist re-exports byte-identically from 431025d's sheets with kicad-cli 10.0.6; R7 ERC 0.
   `sheets/` PNG/SVG exports and erc.json/drc.json in assembly_review are stale since R3/R5: left alone.
3. Wrote m3_design/r8_sch.py (reads pin_table.tsv; label text in place for reassigned pins, wire+label out / NC in for
   freed, NC out / wire+label in for moved-in; moved labels keep the net's R7 shape; R310.1 label 3V3_RADIO -> 3V3;
   notes; rev R8). Dry run on a scratch copy of R7: 27 pins (13 reassigned, 7 moved in, 7 freed) + R310; second run
   no-op; ERC 0. Parity of the R7 board vs the R8 schematic: exactly 28 net_conflict items (27 U1 pads + R310.1).
4. Wrote m3_design/r8_sch_check.py (KiCad Python): ERC, netlist freshness, R7 netlist reproduced, semantic netlist diff
   == decided set, RF/safety, parity both ways, check_actuators + check_r8 netlist checks on a netlist-applied R7 board.
   Next: apply r8_sch.py --netlist to the worktree, run r8_sch_check.py.
5. Applied r8_sch.py --netlist to the worktree (twice: second run no-op). r8_sch_check.py first run: 14 false failures
   from KiCad's `+no_connect` pin-type suffix (follows the NC flag); the check now strips the suffix and asserts it
   matches NC-ness. Then all OK.
6. Rendered the MCU / servo / camera-UART sheets (kicad-cli svg -> qlmanage png): no overlaps. New notes now take the
   font size of their neighbours (MCU 1.05, servos 1.27); sheets regenerated from R7 (git restore 431025d + run):
   byte-identical to the idempotent rerun (hashes in the handoff).
7. Added --project to r8_sch_check.py; seeded defects on scratch copies all caught (QSPI swap, R310 on 3V3_RADIO, R312
   on PYRO1_GATE_N, stale netlist); r8_sch.py refuses a pin in a third state and an unchanged pin that drifted.
   test_fab_validation + test_r8_check: 42 tests OK (tools untouched).
8. R8_DECISIONS D24-D28 appended (D27 corrects the PC13 2 MHz citation: DS12110 Table 53 note 2, p. 142).
   Handoff written. Scratch step2/ deleted. STEP 2 COMPLETE.
