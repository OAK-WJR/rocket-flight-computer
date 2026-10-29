# R9 step 7 (routing families): handoff

Status: **complete.** All ten families of `r9_plan.md` §4 step 7 are built and gated in `r9_build.sh` order (rf_if,
qspi_hse, pyro, servo, imu_baro, usb_swd, camera, status, power_ctl, links). The step-7 gate (D-S7-18) passes on the
built board `m3_design/assembly_review/m3.kicad_pcb`, SHA-256 `8504c2c6c74b601b009f22d0f1dd41aa27e7035b44614282b9560a70cb0a0230`,
and two full builds reproduce every built file byte for byte. Nothing committed or pushed. Decisions: `R9_DECISIONS.md`
D-S7-01 … D-S7-19. Log: `r9_step7_progress.md`. Evidence: `step7_evidence/`.

**Environment.** No logged-in GUI session: `kicad-cli pcb drc` needs the scratch shim of D-S6-14, and `r9_build.sh`'s
stages are replayed from KiCad's python (§3). With a GUI or screen-sharing session logged in, `r9_build.sh` runs as is.

## 1. Produced

| File | What |
|---|---|
| `m3_design/r9_route.py` | the step-7 builder: FAMILIES, Draw primitives (octilinear / width / pad / net asserts, `move_via`), dry-run `build`, KIID seed 9910 + index (D-S7-01 / 07) |
| `m3_design/r9_route_{rf_if,qspi_hse,pyro,servo,imu_baro,usb_swd,camera,status}.py` | sessions 1-6's families (D-S7-02 … 15) |
| `m3_design/r9_route_power_ctl.py` | **new** USB_LIMITED (B.Cu under U1's aft row, F.Cu through U1's interior, B.Cu up the x 32.3-33.9 corridor into C98 / R87 / U11.7), LOGIC_SOURCE_ST, BAT_FAULT_N, BAT_ENABLE, BAT_ILIM, the pull-ups' 3V3 vias, U9.8 / U11.3/4/6 GND straps (D-S7-16) |
| `m3_design/r9_route_links.py` | **new** the constrained short-link stage: BAT_OVLO, BAT_DVDT, LOGIC_ILIM, LOGIC_SS, USB_OVLO, one layer, no via, <= 1.3 x octile (asserted) (D-S7-17) |
| `m3_design/r9_route_check.py` | the per-family gate (D-S7-01); the links gate is the whole-board step-7 gate (D-S7-18) |
| `m3_design/r9_build.sh` | stage pairs for the ten families (the scratch runner's stages 14-33) |
| `m3_design/r9_place.tsv` | step 7's re-placements, each basis citing its decision; this session (D-S7-16 / 17): C81, C85, C86, C90, C97, R84, R85, R86, R89, R90, R91, TP82, TP83, TP84, TP85, TP87, TP89 |
| `m3_design/r9_power.py` | step-6 table edits, this session (D-S7-16): C97 0.7 mm east and its two F.Cu straps, R92.2 on its own GND via (42.4, 84.725), TP83's VLOGIC tap moved with TP83 (via (43.35, 78.2); the via (44.6, 66.2) and the column aft of y 70.6 gone), the RAW_ACT B.Cu pour's south step at x 32.2-34.85 from y 61.1 to 61.45 |
| `m3_design/r9_route_usb_swd.py` | R85.1 on U10.5's line (USB_ILIM straight), R90 0.3 mm west with its 3V3 via (D-S7-16) |
| `tools/test_r9_route.py` | LinksStage (2 tests: the links' one-layer / no-via tables, a seeded detour over 1.3 x fails) |

## 2. Verification (board `8504c2c6…`)

- **Build:** `r9_build.sh` replayed in full twice (stages 0-33): every stage rc 0; the placement, RF strip, pyro block,
  power and all ten family gates **OK**; the sheets, schematic.net.xml, m3.kicad_dru, the variant footprints and the
  board byte-identical (`step7_evidence/build_sha256.txt`).
- **Family gates** (each at its stage: template, DRC + parity, route_check r9 with the empty allowlist, budget, S4, the
  step-5 pyro functions, check_r9 but M-2 / K-legends, check_actuators):

  | family | nets | signal mm | signal vias | critical layer changes | worst ratio | budget | board signal vias |
  |---|---|---|---|---|---|---|---|
  | rf_if | 15 | 333.6 | 0 | 0 | 1.257 | 420 / 0 / 0 / 1.45 | 9 |
  | qspi_hse | 6 | 43.5 | 6 | 6 | 1.383 | 50 / 6 / 6 / 1.40 | 15 |
  | pyro | 3 | 17.6 | 1 | 0 | 1.0 | 18 / 1 / 0 / 1.45 | 16 |
  | servo | 8 | 48.5 | 4 | 0 | 1.298 | 50 / 4 / 0 / 1.40 | 20 |
  | imu_baro | 12 | 64.0 | 10 | 6 | 1.34 | 66 / 10 / 6 / 1.45 | 30 |
  | usb_swd | 11 | 134.8 | 8 | 0 | 1.495 (NRST) | 140 / 8 / 0 / 1.50 | 38 |
  | camera | 15 (+ CAM_5V) | 107.1 | 7 | 0 | 1.332 | 110 / 7 / 0 / 1.40 | 45 |
  | status | 11 (+ VLOGIC) | 129.8 | 5 | 0 | 1.494 (V3V3_SENSE) | 140 / 5 / 0 / 1.50 | 50 |
  | power_ctl | 5 | 174.9 | 7 | 0 | 1.363 (BAT_FAULT_N) | 175 / 7 / 0 / 1.40 | 57 |
  | links | 5 | 10.9 | 0 | 0 | 1.0 | 12 / 0 / 0 / 1.3 | 57 |

  USB_LIMITED (power class, not in the signal figures): 51.9 mm, 2 vias, ratio 1.13.
- **Step-7 gate** (the links gate on the finished board, D-S7-18): DRC 0 violations but step 8's silkscreen classes and
  32 via_dangling, all GND vias of the families' / steps' PENDING lists; parity 0; unconnected 112, all GND (step 8's
  pours); route_check r9 (no allowlist, no leftovers): 91 failing, all GND dead_copper / dangling_via of those pending
  vias and their straps (`step7_evidence/route_check_r9.*`); S4 57 signal vias (<= 70 met; stretch <= 55 missed by 2,
  D-S7-19); P-7, D19, D18 (4.953 mm), D85, D20, R-1 … R-13, K-copper (nearest via ring 0.005 mm from a paste aperture,
  step 6's (42.0, 81.26)), check_actuators all OK.
- **check_r9 in full** (fit, plate model, seeded rule-H suite): 39 rules OK, K-legends FAIL (22 legends, step 8's
  silkscreen). M-2 f1 256.6 Hz; M-5 support bottom 4.600 / top 5.008; T-1 east windows 0.5-27.0 and 92.75-101.5
  (forward third met); P-3 no foreign net in the CH1 hull; P-5 132 pairs, 0 forbidden; P-6 1.03 mm; R-10 6.04 / 5.005 mm.
- **USB_LIMITED DC** (dc_solve U10.6 -> U11.7, 0.45 A, 0.05 mm): 82.9 mOhm, 37.3 mV, 0.45 A per via, neck rise 0.4 C.
- **Step 6's gate on its board** (stage 13): DC unchanged by this session's table edits (RAW_ACT 0.79, BAT_IN 0.17,
  ACT_FET_S 0.27 mOhm; 12.7 / 12.1 / 20.8 C), template, In2, supply, F9 OK.
- **Tests** (built board, shim in the environment): test_r9_route, test_r9_rf, test_r9_place, test_r9_pyro,
  test_r9_power, test_r9_sch, test_r9_check: 167 OK, none skipped (`step7_evidence/tests.txt`).

## 3. Reproduce

```bash
R=rocket-pcb/rocket-flight-computer-r9
KP=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
NP=<python3 with numpy>                                        # the parent project's cfd/venv/bin/python3
NUMPY_PY=$NP $R/m3_design/r9_build.sh                          # with a GUI session (kicad-cli DRC), ~17 min
# without a GUI session (D-S6-14): replay the script's own lines with the scratch shim
$KP <scratch>/s6/tools/build.py --from 0 --to 33               # --list prints the stages; 30-33 are power_ctl / links
(cd $R && DYLD_INSERT_LIBRARIES=<scratch>/s6/inj/nomouse.dylib $KP -I -B m3_design/r9_route_check.py links --report out.json)
(cd $R && $KP -I tools/dc_solve.py --net USB_LIMITED --source U10:6 --sink U11:7 --amps 0.45 --grid 0.05 --necks)
(cd $R/tools && DYLD_INSERT_LIBRARIES=<scratch>/s6/inj/nomouse.dylib $KP -B -m unittest test_r9_route test_r9_rf \
    test_r9_place test_r9_pyro test_r9_power test_r9_sch test_r9_check)
```

The shim (`<scratch>/s6/inj/nomouse.dylib`, a dylib returning (0, 0) for wxGetMousePosition, loaded by
DYLD_INSERT_LIBRARIES) and the runner (`<scratch>/s6/tools/build.py`, which reads r9_build.sh's own command lines) are
scratch files (D-S6-14); rebuild them if the scratch folder is gone. A family's gate takes every family before it in
FAMILIES as done, so run each gate at its own stage (as r9_build.sh does); the links gate is the whole-board gate.

## 4. What step 8 (ground) must know

- **Pending GND vias** (In2 under them is 3V3 or RAW_ACT; they wait for In1 GND): step 6's `r9_power.PENDING`, step 5's
  guard via (13.5, 54.6), and the families' PENDING (qspi_hse's, imu_baro's, usb_swd's D4.2 (9.95, 34.1) and J2.5
  (0.95, 44.57), camera's R70.2 (30.0, 36.9), status's LED1 (4.4, 45.9), buzzer driver (29.6, 23.9) and VLOGIC divider
  (29.2, 47.75)); 32 vias in all (DRC via_dangling list in `step7_evidence/`). power_ctl's GND vias (U9.8 (40.1, 88.4),
  U11.6 (38.5, 65.2), U11.3/4 (38.5, 68.35)) and R92.2's (42.4, 84.725) land on In2 GND and are already connected.
- **GND pads left to the pours** (112 unconnected GND items): the earlier families' list (the step-6 handoff, sessions
  3-6), and this session's C81.2, R84.2, R81.2, R83.2, R86.2, C85.2, R88.2, C98.2, C86.2, C90.2 (B.Cu) and C87.2 (F.Cu).
  C86.2 and C90.2 sit in open bottom copper; C81.2 / R84.2 sit south of U9 beside U9.8's GND via.
- **Power vias without a GND via within 1.5 mm** (route_check INFO): USB_LIMITED's two ((18.25, 39.75) under U1,
  (26.05, 51.15) in the box), VLOGIC's TP83 via (43.35, 78.2), and the earlier families' (VBUS, CAM_IO_3V3, VLOGIC,
  CAM_5V, 3V3A): step 8's stitching.
- The RAW_PROTECTED F.Cu pour now has three test-pad vias in its 1 mm margin west of TP83 / TP85 / TP89 (x 43.35); the
  fill recedes 0.3 mm round each.

## 5. Open items and records for steps 9-10

- **Axis map (D-S7-06):** the R9 firmware binding note must carry roll = -gyro_Y, thrust -a_Y; a bench sign check before
  flight. Step 10's records (M3_R9) must state it.
- **Test-pad and part moves visible to the bench / BOM (this session):** TP84 (BAT_ENABLE) is at the forward edge
  (35.0, 100.4) on the top, no longer in the east column; the east column (top, x 44.6) now reads, aft to forward,
  TP87 LOGIC_SOURCE_ST 67.8, TP74 GND 70.4, TP88 GND 73.0, TP81 RAW_PROTECTED 75.6, TP83 VLOGIC 78.2, TP85 BAT_FAULT_N
  80.8, TP89 BAT_ILIM 83.4 (slot 86.0 empty); TP82 (USB_LIMITED) is on the bottom under U1's aft row (18.25, 36.75); C90
  (camera UART sheet, 3V3 100 nF) at (3.5, 26.0) bottom. ORDERING / bench procedures that name these test pads (TP80
  below 1 V, TP84 / TP85 / TP89 for U9) must use the new spots (step 10). From session 6: LS120 at the south-centre, U13 /
  C92 on the bottom (JLC placement in step 9).
- **Done rows for the owner's deviation list:** S4 stretch 57 > 55 (D-S7-19), with D-S6-13's X2g and P6.
- **Inferences, not measured:** the buzzer's 4 kHz drive 4.5 mm from the radio module's keep-out (D-S7-14); the
  TPS2553 limit of 0.45 A used for USB_LIMITED's DC check is R8 D42's figure, not re-derived here from R85's value.
- **INFO only (route_check, this session's nets):** a U-turn at TP85's T (its via must sit west of the pad: TP83 / TP89
  are 1.1 mm away, the test-pad rule); extra bends at the corridor's 45-degree jogs (past OE's via); power_via_no_gnd of
  USB_LIMITED's two vias and VLOGIC's TP83 via (§4). The entries into U9.9 (0.075 mm) and U9.8 (0.025 mm) are inside
  route_check's off-centre tolerance.
  Earlier sessions' INFO is listed in their decisions (QSPI_IO2 0.5 mm off U1.1's centre, the 3V3A via, J2's
  off-centre entries, u-turns of J3's DM join, SWDIO, V3V3_SENSE, PULLPIN_EXT, width changes at step 6's VLOGIC /
  CAM_5V vias).
- **Scratch to delete when the step is accepted:** `<scratch>/s7*`, `<scratch>/r9/t1`, `r9/st29` (the shim and runner in
  `<scratch>/s6` are still needed without a GUI session).
