# R9 step 6 (power): progress log

Step 6 of `r9_plan.md` §4: `m3_design/r9_power.py`, four In2 regions, the east power spine (RAW_ACT on F.Cu / B.Cu /
In2), the face-to-face FETs, logic / camera supplies, the spine's stitching. Verify: run_dc at 0.1 mm (D12 limits and
every rise <= R8; D_raw <= 1.0 mOhm), D18, D85, barrel current <= 1 A per via, the F9 hot-plug feed.

## Session 1

- No step-6 log existed: fresh start. Read r9_plan, owner decisions, step 1-5 handoffs, plan_spine.

### Findings on the step-5 board (before any power copper)

1. The east column's small parts were legalised by proposal ("nearest legal spot"), not placed for routing: U9's
   network boxes its IN / OUT bar ends (R82.2 OVLO on pin 5's axis, R89.1 3V3 on pin 6's), C89 / C95 interleave
   BAT_IN and BAT_DAMP on one column, the 3V3 buck's C5 / C6 / C9 cross their pins, Q122 / R121 cross ACT_DRV and
   ACT_GATE, R80's BAT_IN pad faces away from BAT_IN, R177 (RAW_ACT_SENSE divider top) sits in U1's east escape band.
2. The mid support (42, 59.5) removes B and F parts from x >= 37.6, y 55-64 (M-5 floors 4.452 / 5.008 mm): the east
   column is y 64-93.5 only; the forward-east support (42, 98) caps it at y ~93.5.
3. The gate network is held by P-6 (gate pads >= 1.0 mm from always-live pads, ACT_FET_S included), AG (>= 1.2 mm from
   GND pads) and H+ (>= 1.2 mm from RAW_ACT pads): C120 / R120 / R121 / Q122 cannot be packed tightly.
4. Q120.4 (east end) and Q121.4 (west end) sit at opposite corners of the face-to-face pair (inherent), so ACT_GATE
   crosses the ACT_FET_S bridge once on F.Cu (R8 D20 / spike (c)).

### Plan (session 1)

Floorplan of the east column, B unless noted: U9 cluster (U9 B rot 90, IN fed from the west end straight off Q120's
drain pour) y 86.8-93.5; RP output (C82, D9, R92) and the ACT driver column (Q122, R121, R122, R123 beside Q120.4)
y 80.5-86.5; 3V3 buck y 71-80; U11 cluster y 64-71; C84 (F) hold-up; 3V3 to In2 by a B.Cu lane west of the buck;
RAW_PROTECTED trunk on F.Cu under C84 and down the east to U11 and the camera (R8 D46 route, translated).

### Log (session 1)

- Harness: scratch `…/scratchpad/s6/` (exp.py applies placement moves to the step-5 board, runs the legaliser on the
  moved parts and r9_power.build, fills; drc.sh; run_dc.sh at 0.1 mm). Moves live in `s6/moves.json` until they go
  into r9_place.tsv.
- First 7.7 A copper (B / F / In2 spine, BAT_IN island, B bridge): RAW_ACT 0.76 mOhm, 7.69 mm, 13.0 C; BAT_IN
  0.16 mOhm, 7.35 mm, 13.7 C; ACT_FET_S 4.62 mm, 23.3 C (over R8's 22.3) -> C120 / R120 moved west off the bridge, an
  F.Cu ACT_FET_S plate over Q121's source row with 5 vias: 4.86 mm, 22.0 C. Every via <= 0.63 A. D18 / D85 / P-0 / P-5
  / P-6 OK. In2 3V3 first cut entered the CH1 hull (P-3): the north edge now follows the hull, offset 0.15 mm.
- East column re-placed (legaliser clean): U9 B rot 90 (IN from the west straight off Q120's drain pour; OUT east to
  a via; OVLO divider R82 / R83 north with FLT under R82's body; C81 / R84 south); R81 / C87 (EN) and C82 (RP output
  cap) on F above U9; ACT driver column (Q122, R121, R122, R123) east of the FET pair beside Q120.4, gate hop on F;
  U11 B rot 90 + network (R86 / C85 east, R87 / R88 west, C98 USB input, C99 output); 3V3 buck U2 / L1 / C5 / C6 /
  C8 / C9 north of U11 per DS41326 Fig. 25; C7 VLOGIC; D9, C97 on F (S pocket); R92 B east of U9; C84 rot 270 (its
  VLOGIC pad aft, beside the VLOGIC via); R89 / R91 (BAT_FAULT_N / LOGIC_SOURCE_ST pull-ups) at the MCU end in the
  3V3 region; TP80 B on the BAT_IN island; TP87 / TP90 moved; R80 / R165 under J1.3 / J1.4; C89 rot 270.
- Scope found: the USB_LIMITED lane U10 -> U11 has no corridor through U1's east escape field, the RAW_ACT_SENSE
  divider and the camera translator cluster that does not cross a step-7 lane or the divider tap (R8's corridor is
  occupied by R9's servo clamp / divider / translator parts) -> deferred to step 7 (power_ctl) with a corridor note.

## Session 2 (after the reboot)

- The scratch folder was emptied: `s6/moves.json` and the harness were gone. The moves were recovered by replaying
  session 1's own edits of moves.json from its transcript (44 parts; R123 back to rot 90, the summary's value, which
  the DRC confirms) and are now rows of `m3_design/r9_place.tsv` (bases name D-S6-01 / 02 / 04 / 05 / 06).
- Environment: the machine has no GUI session (rebooted, nobody logged in), so `kicad-cli pcb drc` crashes in
  wxGetMousePosition ([NSScreen screens] empty; BOARD_COMMIT::Push -> TOOL_MANAGER::doRunAction). Every gate's DRC
  stage needs it. Workaround (scratch only, nothing in the repo): a dylib interposing wxGetMousePosition to (0, 0),
  loaded through DYLD_INSERT_LIBRARIES (kicad-cli's entitlements allow it); /bin/bash strips DYLD_* (SIP), so the build
  is replayed stage by stage from KiCad's python (`s6/tools/build.py` reads r9_build.sh's own command lines).
  Validated: the step-5 gate on the step-5 board passes exactly as recorded (DRC OK).
- Build through step 5 with the moves: every gate of steps 2-5 passes (place, RF, pyro).
- r9_power.py finished: PARTS frozen (74 parts), RAW_PROTECTED as an F.Cu pour down the east column (two U9 vias;
  the track loop and extra-via failures gone), GND straps without short segments, the U7 approach without a short
  segment, In2 BAT_IN trimmed to y 99.2 (no In2 GND finger at the forward edge), Q120.4's gate exit at 45 degrees,
  the 3V3 column split at C8.1, NETS / PARTIAL / RAILS, a dry-run recorder for the template gate.
- r9_power_check.py written; on the scratch board every gate passes: DC RAW_ACT 0.79 mOhm 12.7 C, BAT_IN 0.17 / 12.1,
  ACT_FET_S 0.27 / 20.8, via max 0.65 A; F9 R_b 2.32 mOhm (R8 17.3), feed ~3.2 nH: U9 IN departs 0.002 V / x1.028.
- The step's stages are in r9_build.sh; the full build (steps 2-6, every gate) passes and two builds are byte-identical:
  board 47fb298d…. Evidence in step6_evidence/ (gate report, full contract with plate / fit / seed, DC at 0.1 and
  0.05 mm, supply paths, hot-plug model, scorecard, tests). 23 suites / 417 tests OK.
- Done-row misses recorded (D-S6-13): X2g = 1 (TP121 in the CH1 box corner; no legal spot outside it within 9 mm of
  the gate copper, measured search) and P6 1201 mm (four In2 regions, boundaries counted twice).
- USB_LIMITED corridor measured (handoff section 4): clear runs and blockers listed; left to step 7 power_ctl.
- Decisions D-S6-01 … D-S6-14 recorded; handoff written. Step 6 done.
