# R8 build step 6 handoff: signal families

Step 6 of `r8_plan.md` section 3 (Strategy B): every signal net routed by deterministic family modules, each followed
by its gate, appended to `m3_design/r8_build.sh`. Decisions D51-D61 in `R8_DECISIONS.md`; the running log is
`r8_step6_progress.md`. Nothing was committed or pushed.

## Result

- `m3_design/r8_build.sh` builds R8 from R7 (431025d) through steps 2, 4, 5 and 6 in about 5.5 min and stops on any
  failed gate. Final board `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
  `b7a4d34d7af69fcdeaeb49652264b85393ca9da20d20f875c3da44495e93caae`, reproduced byte for byte by three consecutive
  full builds.
- Every net on the board is complete (DRC: 0 unconnected items, GND included), DRC with schematic parity is clean
  apart from the silkscreen classes step 8 settles, and the 12 rigid R7 digests are unchanged.

| Family | Nets | Signal mm | Signal vias | Critical layer changes | Bends | Worst ratio (net) | Budget (mm / vias / ratio) |
|---|---|---:|---:|---:|---:|---|---|
| qspi_hse | QSPI, HSE, BOOT0 (spike a) | 65.5 | 9 | 8 | 18 | 1.38 | 68 / 9 / 1.40 |
| rf | radio, GNSS, strip leads, limiter (spike d, D51) | 434.2 | 4 | 4 | 83 | 1.91 (GNSS_VCC_RF, D51) | 445 / 4 / 1.95 |
| servo | four lanes, D121 (spike b) | 141.0 | 4 | 0 | 12 | 1.13 | 145 / 4 / 1.15 |
| pyro | CH1 exits, RAW_ACT_SENSE (spike a, D32 / D33) | 166.8 | 4 | 3 | 29 | 1.37 (CONT) | 170 / 4 / 1.40 |
| usb_swd | USB, VBUS, U10, SWD, NRST (D53) | 148.0 | 4 | 0 | 38 | 1.30 (DM, F10) | 155 / 4 / 1.35 |
| imu | U4, U5, pull-ups, 3V3A (D54) | 105.6 | 7 | 4 | 18 | 1.56 (SCK crossing) | 110 / 7 / 1.6 |
| camera | UART via U12, U7 network, CAM_5V sense, U13 rail (D56) | 91.9 | 6 | 0 | 19 | 1.50 (PWR_EN, D37) | 95 / 6 / 1.55 |
| status | LEDs, buzzer, pull-pin, sense dividers, D50 lanes, BAT_ENABLE (D58) | 209.4 | 8 | 0 | 31 | 1.20 | 215 / 8 / 1.3 |
| links | U11 / U9 locals (D59) | 19.2 | 0 | 0 | 9 | 1.00 | 20 / 0 / 1.3 |
| **Total** | | **1381.6** | **46** | **19** | **257** | | targets 2300 / 75 / 32 crit / 400 bends |

The ratio is copper over the octilinear MST (the D10 keep-out baseline where it applies) and counts only nets more than
route_check's 2 mm slack longer than their MST.

## Files

New:
- `m3_design/r8_route.py`: driver and Draw primitives (refuse off-angle / zero-length segments, two vias at one
  point, a pad not where or on the net its table assumes; a family runs once; KIID seed per family; native fill;
  rigid digests asserted).
- `m3_design/r8_route_{qspi_hse,rf,servo,pyro,usb_swd,imu,camera,status,links}.py`: one module per family: NETS,
  CONTINUES, RAILS, BUDGET, the copper as explicit tables; each docstring records its topology.
- `m3_design/r8_route_check.py`: the per-family gate (rigid, drc + parity, complete, route, budget, pyro, inner,
  in2, contract, l10, reserved; `--report`).
- `tools/test_r8_route.py`: 12 seeded-defect tests of the primitives and the gate logic.
- `r8_step6_progress.md`, this handoff.

Changed:
- `m3_design/r8_build.sh`: the nine family stages with their gates.
- `m3_design/r8_place.tsv`: placement amendments, basis D52 (D4, R85, TP86, C30-C32, R11-R13, R64), D55 (U12,
  C100, C93, R100-R102, TP75, TP76, TP91, R104, R105, C94), D57 (R162, C160). The placement gate passes on every one.
- `m3_design/r8_keepclear.tsv`: regenerated with `--routed` (D60): 29 rows left, all step 7's.
- `sources/r8_design/step4/make_keepclear.py`: `--routed` mode (drops the nets step 6 completes).
- `m3_design/r8_legalise.py`: optional `copper=` (default unchanged: every board item, the placed board's rigid copper).
- `tools/route_check.py` (+ `test_route_check.py`): D51's two allowlist entries with measured reasons, ROUTE_FIGURES.
- `tools/test_r8_place.py`, `tools/test_r8_power.py`: adapted to the step-6 board (D60, D61; see progress log).
- `R8_DECISIONS.md`: D51-D61.

## How it was verified

- Full build three times (`r8_build.sh`): every gate OK each time (placement, power, nine route gates), identical
  SHA-256.
- Each route gate on its family: DRC with schematic parity (no violation outside the deferred silkscreen classes),
  its nets complete (every net after links; GND whole from imu on), route_check profile r8 (no failure or unrecorded
  leftover on its nets or rails except GND pour fingers, deferred to step 7), budget, D18 / D19 (pyro vs inner power,
  gate vs servo 0.5 mm), no inner track, the In2 map, check_r8 (later-step findings only) + check_actuators, L10 at
  the pyro vias (D61), step 7's reservations overlaid on the copper (DRC copper rules) and no stale row.
- Unit tests: `test_r8_route test_route_check test_r8_power test_r8_place test_r8_check`: 108 tests OK.
- `tools/check_r8.py` on the final board: 27 findings, all owned by later steps (J9 / J2 pin legends: step 8; strip
  fence opening and strip GND reach: step 7; the rigid ARM1_SENSE In2 link: D15 open item). camera_bypass now passes
  (C100 1.2 mm to U12.3 and 1.2 mm GND return; C93 3.78 mm through its via, limit 5).
- The reservation table regenerates byte for byte from the build's own output (two-pass procedure below).
- Scorecard quick pass (`NO_DC=1 NO_GATE=1 tools/run_survey.sh`, soft): simplicity index 19.1 (R7 = 100, target
  <= 35); signal track 1500 mm (<= 2300), signal layer-change vias 55 (<= 75), critical layer changes 25 (<= 32),
  none without a GND via, route MST 1644 mm (<= 1850), weighted detour 1.18 (<= 1.18), route_check failures 1 (a GND
  pour finger, step 7), allowlisted 3 (A8 + D51). Nets over 1.6 x plain MST: RAW_ACT_SENSE_MCU (D33's crossover, 1.94
  mm excess), RADIO_TXEN (keep-out forced, D10), GNSS_VCC_RF / GNSS_LNA_EN (D51). The GND / In2 rows (P6, P9-P11)
  are step 7's.
- Not done in this step: the 7.7 A DC solves (step 6 changed no 7.7 A copper), any physical or bench test, firmware.

## Reproduce

```bash
cd rocket-pcb/rocket-flight-computer-r8
KPY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
m3_design/r8_build.sh                                          # ~5.5 min; ends "R8 route gate (links): OK"
shasum -a 256 m3_design/assembly_review/m3.kicad_pcb           # b7a4d34d7af69fcd...
(cd tools && PYTHONUNBUFFERED=1 $KPY -m unittest test_r8_route test_route_check test_r8_power test_r8_place test_r8_check)
PYTHONUNBUFFERED=1 $KPY -I m3_design/r8_route_check.py links --report /tmp/route_links.json   # any family name
PYTHONUNBUFFERED=1 $KPY -I tools/check_r8.py m3_design/assembly_review/m3.kicad_pcb        # 27 later-step findings
NO_DC=1 NO_GATE=1 tools/run_survey.sh m3_design/assembly_review/m3.kicad_pcb /tmp/survey
```

**Reservations after a family or placement change.** The route gates' `reserved` check fails on a stale row. The table
needs a freshly placed board; place on a copy, then pass the built board with `--routed`. If the placement itself
moved, place first with the current table (`r8_pcb.py --keepclear` takes another), regenerate, place again with the
new table and confirm the regeneration is unchanged:

```bash
D=/tmp/r8p; mkdir -p $D && git show 431025d:m3_design/assembly_review/m3.kicad_pcb > $D/m3.kicad_pcb
cp m3_design/assembly_review/m3.kicad_{pro,dru} $D/
PYTHONUNBUFFERED=1 $KPY -I m3_design/r8_pcb.py --board $D/m3.kicad_pcb
PYTHONUNBUFFERED=1 $KPY -I m3_design/assembly_review/sources/r8_design/step4/make_keepclear.py \
    $D/m3.kicad_pcb m3_design/r8_keepclear.tsv m3_design/assembly_review/m3.kicad_pcb --routed
```

**Iterating on one family.** `r8_route.py FAMILY --board B` rebuilds B in place and refuses to run if the family's nets
already carry copper, so start from a copy of the board after the previous family (the build overwrites
`m3.kicad_pcb` stage by stage; save copies between stages), then `r8_route_check.py FAMILY B`.

## What the next steps must know

1. **Step 7 (GND)** starts from this board.
   - route_check's one remaining failure: a GND pour finger on F.Cu between SCL's and SDA's diagonals over U5 (box x
     9.1-12.3, y 59.8-62.9). The route gates defer GND pour fingers / slivers / pad pour cuts to step 7; nothing else
     is deferred.
   - The 29 reservations left are step 7's: spike (d)'s fence row on y 23.3 and two strip stitches, and spike (a)'s
     C24 GND stub and via (26.17-26.95, 51.1). check_r8's strip fence opening and strip GND reach findings are the
     same work.
   - Keep GND whole: r8_route_check's `complete` requires it from imu on, and found two islands during step 6 (D56,
     D58); a stitching change that cuts a pour into an island fails the same way.
   - Scorecard GND rows to improve: P9 GND distance p95 11.55 mm (target 3.5), P10 23.5 mm, P11 10.0 mm, P7 12 outer
     GND islands with <= 1 via; route_check information: 22 power vias without a GND via within reach.
2. **Step 8 / 9.**
   - J9 / J2 pin legends (check_r8) and the deferred silkscreen DRC classes are r8_post's.
   - Test pads moved (D55): TP75 (37.65, 40.3) and TP76 (37.5, 51.1) on the top, TP91 (32.5, 52.3) on the bottom;
     the probe list and coating mask must follow. R102, R100, R101, R104, R105, C93, C94, C100, U12, R162, C160 moved
     or turned (r8_place.tsv basis D52 / D55 / D57).
   - Deviations for the owner's acceptance list (REQUIREMENTS M2): D51's two limiter detour allowlist entries, A8
     (inherited), D61's four L10 pyro-via exceptions.
3. **Code contracts.**
   - A family module's PADS table asserts every pad it draws to, so a placement change fails loudly; update the table
     and the copper together.
   - The legaliser keeps its build behaviour; tests on a later-step board pass `copper=r8_power_check.rigid_items(b)`.
   - make_keepclear `--routed` drops every row of a net the families complete; a new family must be added to
     `r8_route.FAMILIES` (the build loop and a test check the order).

## Left open (not escalated; none is unsafe or changes a requirement's intent)

1. **D61 L10 exceptions**: ARM1_SENSE_MCU's dive 0.635 mm from R170 / R172 and 0.835 mm from C15; PYRO1_CONT_MCU's
   0.235 mm from R168. MCU side of the 4.7 kOhm sense resistors, tented vias, closer in R7 (R5_VALIDATION exception).
   For the owner's review.
2. **D59**: the links are not r5_maze's output (it cannot meet route_check's hygiene there); the plan's constraint is
   asserted instead. A plan-letter deviation, recorded.
3. **D51 allowlist** (limiter detours) awaits owner acceptance with the other M2 deviations.
4. **Inference** (D56): camera-side U12 / C93 supplies on 0.5 mm vias carry a few mA (TXU0202 static current, not
   re-read from TI's datasheet here); step 9's electrical review cites it.
5. No independent review of the step-6 modules and gate was possible inside this step (r8_plan section 4); the
   orchestrator schedules it.
