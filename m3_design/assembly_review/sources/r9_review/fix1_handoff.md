# R9 review pass 1: fix pass handoff

Status: **done; the gate passes.** The fix pass applied review pass 1's confirmed findings (`pass1_*.md`, on step 10's
board `fc3d5b34…`) through the R9 generators and tables only, so `m3_design/r9_build.sh` reproduces the result. No
copper was hand-patched, no check was weakened and no pyro, arming or actuator safety rule was relaxed (three gate rules
were added: check_r9 P-7b, r9_ground_check's copper gate, R-8 over U31's whole body). Nothing is committed.

- **Board:** `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
  `4f841a0e44ebb1829ad7996dfe6320ed527fce1fdb1e5ff11658e0705b44ac14` (netlist and DRU unchanged).
- **Builds:** two, byte-identical in every built file (the stage replay in the worktree and `r9_build.sh` run whole in a scratch clone, 45 min, rc 0; `sources/r9_design/step10_evidence/build_sha256.txt`).
- **Gate:** `tools/check.sh` exit 0 (DRC 0 at every severity, unconnected 0, parity 0, ERC 0; check_r9 40 / 40;
  route_check r9 0 failing / 0 allowlisted / 0 leftovers; check_actuators OK).
- **Records:** R9_VALIDATION "Review pass 1" lists every pass-1 finding with its severity, the fix brief's verdict and
  its disposition; the deviation list (C1–C25, part D) is rewritten with like-for-like R8 figures; M3_R9, STATUS,
  REQUIREMENTS, ORDERING, FMEA_REDUNDANCY, MARGIN_PRESCRIPTION, AGENTS, README and the step-3 handoff are updated;
  decisions R9_DECISIONS D-F1-01 … D-F1-11. Log: `fix1_progress.md`.

## 1. What changed, per finding

| Finding | Change |
|---|---|
| PYRO-01 | `r9_route_imu_baro.py`: QSPI_IO2's east run on y 50.6, 0.55 mm from U1.3 (was 0.25; R8 0.75). `check_r9` P-7b: U1's gate pin pad ≥ 0.5 mm from any non-U1, non-GND copper (seeded test) |
| PYRO-02, -03, DFM-01, -02, -05, REQ-01 … -10, RF-02, ROUTING-03, MECH-01 … -04, POWER-02, -03, PLANES-03, -04, -06 | records (R9_VALIDATION, M3_R9, STATUS, REQUIREMENTS, ORDERING, FMEA, MARGIN, D-S6-05 / D-S6-06 / D-S8-20 / D-S10-09 / -12 / -14 / -18, the step-3 handoff) |
| REQ-02, ROUTING-02 | `r9_power.RAW_ACT_VIAS`: (29.6, 78.2) dropped, (31.0, 78.2) → (31.5, 78.2): no via in TP120 (Z4 0); `r9_extra_metrics.py` / `r9_scorecard.py` count Z4 over every TP* pad |
| REQ-04, POWER-04, DFM-03 | J122's GND pins: the relief was built (DRC clean; 4 / 4 / 2 spokes by the reviewers' count) but J122.3's ring leaves a 0.86 mm² single-spoke F.Cu piece (the islands gate fails it), so the pins stay solid as R7 / R8; listed C21 with the measurement (C20: the RF clamps); D-F1-06 |
| RF-01, ROUTING-01 | `r9_rf.py`: R7's three U31 module-frame GND vias (pins 0.20 / 0.35 / 0.35 mm of copper from a via, were ≈ 1.1); TXEN at 0.2 mm, the grid via (24.7, 10.45) → (24.65, 10.45); `r9_route.WIDTHS` five widths |
| RF-03, INTEGRITY-01, -02, -05 | `check_r9.py`: R-5 nearest pad, sorted; R-7 compass sides; R-8 In1 over U31's body; M-7 docstring. `pyro_probe.py`: sorted nets, (mm, labels) ties. Two separate gate runs give identical reports |
| POWER-01 | `r9_place.tsv` C98 → (39.275, 64.2) rot 180 B; `r9_route_power_ctl.py` USB_LIMITED's end redrawn (C98.1 1.94 mm of track from U11.7, was 5.29). C83 and C82 recorded (C23): no legal C83 spot on U10.1's run |
| PLANES-01, -02 | `r9_power.RAW_ACT_F` 29.75 edge to y 76.6 (the guard strip's 0.37 mm neck now 0.72 mm). `r9_ground_aid.py` copper stage (pads > 5 mm, clusters > 8 mm of copper; `place_safe` refuses a via that adds a weak island; C121.2's corridor box). `r9_ground_check.py` copper gate with six cluster and one pad exceptions. Table regenerated (187 rows, 183 vias; `--check` reproduces it): vias (35.6, 64.8), (32.9, 99.85), (41.4, 41.1). C121's return 11.98 → 1.38 mΩ; F.Cu worst reach 28.41 → 9.50 mm; the forward strip 12.45 → 6.04 mm; RAW_ACT 0.80 mΩ, 12.6 °C (was 0.79, 12.7) |
| Not in the brief | PLANES-05, MECH-05, DFM-06 … 08, INTEGRITY-03 / -04 / -06 open (R9_VALIDATION "Review pass 1"); POWER-05, PLANES-04 / -06, ROUTING-04 / -05, INTEGRITY-05 fixed in the records |

## 2. Gate, scorecard and evidence

- Step gates: every stage of both builds passed (placement, RF, pyro, power, ten route families, ground with its new
  copper gate, post, check.sh). The first ground-gate run failed only on the copper gate's then-empty exception list;
  the six clusters and J9.2 were measured and recorded, and lines 36–39 re-run.
- Scorecard (`step10_evidence/r9_scorecard.md` against `step9_evidence/r9_scorecard.md`): done rows 34 met / 16 missed
  (step 9 reported the same with Z4 wrongly met; fc3d5b34 was truly 33 / 17); index_r9 84.8 → 83.8; X5 6 → 5; Y1 31 →
  30; P9 3.45 → 3.37 mm; D_raw 0.79 → 0.80 mΩ, neck 7.81 → 7.89 mm, 12.8 → 12.6 °C; P6 1478.1 → 1479.4; S6 / S7 / S17
  1.151 / 206.6 / 1365.5 → 1.152 / 207.5 / 1367.5; vias 579 → 583 (GND 425 → 430); F3 4.600 → 4.483 mm (C98.1). No row
  crossed its target.
- DC (`step10_evidence/dc/`): 0.05 mm RAW_ACT 0.80 / BAT_IN 0.16 / ACT_FET_S 0.26 mΩ, 12.6 / 12.1 / 20.4 °C; the 32 rows equal step 10's but USB_LIMITED 85.91 mΩ (83.02; C98's detour, 43 mV at 0.5 A), RAW_ACT → J124.2 10.14 (10.13) and → R177 6.12 (6.11); fire loop 32.1 mΩ, 1.65 A (unchanged); servo GND return 0.32 mΩ; C121's GND return 1.38 mΩ (11.98).
- Reference audit unchanged (R6b 0.1022); requalification unchanged for pyro and RF but P-7b and the module pins.
- Tests: 478 tests in 26 suites OK, none skipped (step 10's 474 plus P-7b and three copper-gate tests); quality_audit 21 under both Pythons; audit_artifacts exit 0. Fab: `FAB_NET=1 m3_design/r9_fab.sh` OK (CPL 78 + 133 rebuilt, 8 placement-only; paste OK; manifest bound); live JLC 2026-10-26 00:57–01:00Z: $109.38 per board, 52 extended codes, short none (U4 40, U30 34); check_procurement full OK. Records check: `step10/check_records.py` OK (70 evidence files bound, 151 hashed inputs, 87 figures).
- `step10_evidence/` holds the re-run on `4f841a0e…` (D-F1-11; the 0.05 mm DC moved there); `step9_evidence/` stays
  step 9's record of `fc3d5b34…`. Fix-pass measurements and their scripts: `fix1/` (see §4).

## 3. What the next pass must know

- **Pass 2 reviews `4f841a0e…`.** Inputs: R9_VALIDATION ("Review pass 1", the deviation list), this handoff.
- **New gate rules to review (gate integrity):** P-7b; the copper gate and its exceptions (`r9_ground_check.py`
  COPPER_EXCEPT / COPPER_PAD_EXCEPT); the aid's copper stage and `place_safe`; C121.2's CORRIDOR_EXCEPT box in the aid
  and the stitch gate; R-5 / R-7 / R-8 changes; pyro_probe's tie rule; the scorecard's Z4.
- **Owner decisions pending:** the length option (C1: 98 mm by reclassifying, or 100 mm at 5.0–5.94 mm); the crystal
  plane (C14); the actuator gate-pad zone rule option (C19); J122 relief or solid (C21); the east mid support with the
  sensors on mode 1's antinode (part D); the deviation list's dated acceptance.
- **Not done and why:** the optional R-7 module-ground-pin row (the fix restores R7's measured 0.20 / 0.35 / 0.35 mm;
  a gate at exactly 0.35 mm on a 0.05 mm raster would sit at its limit), pyro.bare own-part pads, JLC_Assembly fields,
  the DFM-04 via moves and the second single-point vias: optional, recorded; C83's move (no legal spot); the DRU
  comment of INTEGRITY-03 (pinned by check_actuators' DRU_SHA).

## 4. Fix-pass evidence outside step10_evidence

- `fix1/fix1_measure.py` and its outputs on both boards (`fix1/fix1_measure_fc3d5b34.json`,
  `fix1/fix1_measure_4f841a0e.json`): module GND pins, via rings to openings, gate pads to GND fill, hardware, thin GND
  pieces, test-pad vias, through-copper GND reach, single vias.
- `fix1/dc_c121_gnd.txt`, `fix1/dc_c150_gnd.txt`: the GND returns of C121 and C150 on `4f841a0e…`.
- `fix1/aid_copper.txt`: the aid's copper-stage log (the refused spots and the logged clusters).

## 5. Proposed parent VEHICLE.md stack-row update (D-S10-11; not applied)

Step 10's proposal (`sources/r9_design/r9_step10_handoff.md` §4) with review pass 1's additions (R9P1-MECHANICAL-02):

> flight computer board 102 (M3-ASSY-R9, the current candidate, 46 × 102 mm; M3-ASSY-R8, the owner-accepted fallback,
> is 46 × 118 mm with R7's outline, holes and jacks; parts on both sides; two edge-launch SMA jacks overhang its aft
> edge by 9.5 mm; J1's battery-wire entry faces the forward edge and both pyro terminals take their wires from the left
> (x = 0) edge; it fits the Ø50.8 mm coupler bore along its whole length; the sled puts the board's top face on the bore
> axis on nylon standoffs at least 3.5 mm tall (the sled tongue passes under the SMA plug nuts, 2.6 mm below the bottom
> face) at the five M3 holes (4, 4), (42, 4), (4, 98), (42, 98) and (42, 59.5) mm, clears the bottom parts, which hang
> up to 3.0 mm below the board, is non-conductive under the whole bottom face, and carries both SMA plugs about 25–30 mm
> aft of the board edge; the battery leads run aft to forward along the east side below the board and sled (the
> top-side east wall is closed by the camera plug) and turn back up into J1 beyond the forward edge, so allow that bend
> forward of the board; the igniter and ARM leads run along the west side), eyebolt nut and charge wiring ~25, recovery
> ~260 (…). Leaves ~68–84 mm of slack with R9 (~52–68 mm with R8's 118 mm board); …

## 6. Reproduce

```bash
R=rocket-pcb/rocket-flight-computer-r9; KP=<KiCad python3>; NP=<cfd/venv python3>
cd $R && NUMPY_PY=$NP bash m3_design/r9_build.sh          # ~40 min, rebuilds 4f841a0e… byte for byte
$KP -I -B m3_design/r9_ground_aid.py STEP7.kicad_pcb out.tsv --check   # STEP7 beside the project's .kicad_pro / .kicad_dru
NUMPY_PY=$NP bash tools/run_r9_survey.sh m3_design/assembly_review/m3.kicad_pcb OUT          # the scorecard
```
The step-10 evidence commands are `sources/r9_design/r9_step10_handoff.md` §3's, run on this board.
