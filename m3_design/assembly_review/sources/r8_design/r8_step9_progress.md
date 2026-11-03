# R8 step 9 progress log (requalification and records)

Board under requalification: m3_design/assembly_review/m3.kicad_pcb, expected SHA-256 429b6db4dc95c1a0fd3e736625c416c20fa0e7fc72f6f6c9c576003340dc1987 (step 8).

## Log
- Started: read r8_plan.md, step 8 handoff, survey_constraints §1 and §12-13.
- Board SHA confirmed 429b6db4. Scratch: $SCRATCH/r8_step9 (board copy, R7 copy from 431025d). Started run_dc.sh 0.05 (dc005/) and check.sh (check1.log) in background.
- Scripts for this step go in sources/r8_design/step9/.
- check.sh on 429b6db4: exit 0 (reports copied to $SCRATCH/r8_step9/check1_reports). Board SHA unchanged after.
- step9/dump_board.py: parts/pads/vias/holes/silk to JSON (r8.json, r7.json in scratch).
- Vibration (step9/plate_model.py, numpy venv $SCRATCH/r8_step9/venv): reproduces R7 pass-2 figures exactly (221/313/377/533;
  176/249/269/380; no-jack static 0.94 mm @ (46,63)). R8 flight config (jacks only) 208.7/295.1/346.3/489.7 Hz (-6..-8 %);
  cause: C84 moved to (37, 63.2) at the right-edge mode-1 antinode (-16.6 Hz), C121 west (+7.5 Hz). Strains no-jack D5:
  U31 579, U30 555, U4 509, U1 609, J121 906, C121 803 ue; max deflection 1.01 mm @ (46, 62.5).
- Hot-plug (step9/hotplug_feed.py): input parts within 4.6-10.6 mm of J1.1; U9 27 mm on a 0.5 mm B.Cu lane over In2 GND,
  est. 4.2 nH; U9 IN vs node: +0.002 V, slew x1.008 (5 nH case); 15 nH x1.045; 30 nH x1.095.
- IMU: U4 (10.0, 53.8) B rot 0 (R7 (36, 78.3) B rot 0): axis map unchanged; lever arm x -13.0 (R7 +13.0).
- DC 0.05 mm on 429b6db4 (scratch dc005/): RAW_ACT 1.45 mOhm 5.94 mm F.Cu 17.5 C; BAT_IN 0.42 mOhm 7.00 mm B.Cu 14.5 C;
  ACT_FET_S 0.18 mOhm 4.97 mm B.Cu 21.5 C: all D12 OK. Supply paths: step9/run_supply_dc.sh at 0.1 mm (running).
- tools/reference_audit.py (+ tools/test_reference_audit.py, 3 tests OK): R8 R6 set 47769 samples, 5525 unreferenced
  (11.57 % = R6b); causes own_via 3589, Y1_In2_keepout 1710 (HSE B.Cu), other_via 226; 0 over another fill / split /
  void. Extended 103308 / 6283 (6.08 %). R7: 27.91 % (track 6198, fill_gap 4310, void 887, over_fill 121 ...).
- step9/requalify.py (R8 + R7 JSON in scratch req_*.json) and step9/pyro_neighbours.py: pyro rule margins, exits, bare
  copper, block vias, A8, probes, holes, edges, tabs, mark, parts, RF, IMU. Pyro neighbourhood much cleaner than R7.
- Datasheets fetched to scratch ds/: TI TXU0202 SCES942A (Mar 2022): A-port outputs referenced to VCCA, VOH <= VCCO, abs
  max VO <= VCCA + 0.5 V (7.1 p. 5), ICCA+ICCB <= 6 uA (7.5 p. 8); U12.3 = 3V3 (VCCA), U12.7 = CAM_IO_3V3 (VCCB).
  Huaneng MLT-5020 (LCSC C94598): 4000 +- 200 Hz (item 5), 0.5 g (item 9).
- step9/binding_note.py -> step9/r8_binding_note.json (board 429b6db4, U1 map = pin table, 27 changed pins, D6/D27).
- Survey quick on 429b6db4 = step 8 (index 14.4 without DC rows). Next: write docs (M3_R8, R8_VALIDATION, STATUS, ...).
- Written: docs/M3_R8.md (SUPPLY_TABLE placeholder until the 3V3 solves finish), docs/R8_VALIDATION.md, R8_DECISIONS D74-D84
  (+ D3 buzzer note), STATUS.md R8 section (R7 = accepted fallback). Q30 limiter copper = R7's (thermal note holds).
- Remaining: supply DC table, AGENTS section 1/3, REQUIREMENTS, MARGIN, ORDERING rewrite, full tests, check.sh, handoff.
- Supply DC done (25 rows, step9/run_supply_dc.sh), table in M3_R8. Evidence copied to step9/evidence/ (paths scrubbed).
- Records edited: AGENTS section 1 rows + section 3 silkscreen pointer; REQUIREMENTS F4/F10/P1/P2/M2/M3 + R8 acceptance;
  MARGIN P1-9 R8 status, R14 (R7) R8 note; ORDERING regenerated for R8 (sections 1-7).
- Remaining: full test suites, final check.sh, optional full rebuild to confirm SHA, handoff.
- Tests: 269 tests / 17 suites OK + quality_audit 21 x 2 OK. Handoff drafted (REBUILD_LINE placeholder). Full rebuild
  running (log $SCRATCH/r8_step9/rebuild.log; pre/post SHA files beside it).
- Final rebuild: sheets, netlist and board SHA identical (429b6db4), build's check.sh exit 0. Fab manifest OK.
- Step 9 complete; handoff written (r8_step9_handoff.md).
