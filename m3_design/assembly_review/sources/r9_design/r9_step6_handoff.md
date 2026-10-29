# R9 step 6 (power): handoff

Step 6 of `r9_plan.md` §4. The power copper is built by `m3_design/r9_power.py` on the step-5 board and gated by
`m3_design/r9_power_check.py`. Both run in `m3_design/r9_build.sh`, after a re-placed east column (42 rows of
`r9_place.tsv`). The built board is `m3_design/assembly_review/m3.kicad_pcb`, SHA-256 `47fb298d…`
(`step6_evidence/build_sha256.txt`), and two full builds reproduce every built file byte for byte. The step gate passes
in full, as do the step-2, -3, -4 and -5 gates in the same build. Nothing committed or pushed. Decisions:
`R9_DECISIONS.md` D-S6-01 … D-S6-14. Log: `r9_step6_progress.md`. Evidence: `step6_evidence/`.

**Environment (read §6 first).** The machine has no logged-in GUI session, so `kicad-cli pcb drc` crashes. Every DRC
stage of steps 2-6 ran through a scratch shim (D-S6-14). With a GUI or screen-sharing session logged in, `r9_build.sh`
runs as is.

## 1. What was produced

| File | What it is |
|---|---|
| `m3_design/r9_power.py` | The builder (tables in board mm). PARTS freezes the 75 parts the copper lands on (asserted: a moved part stops the build). Sections: In2's four regions; the 7.7 A path (BAT_IN / ACT_FET_S / RAW_ACT pours on F / B / In2 and their via fields, J124.2's RAW bar); the battery taps, switch legs and damper; the gate network; RAW_PROTECTED (U9's output, the F.Cu pour R9_RAW_PROTECTED_F, its branches); VLOGIC and the 3V3 buck; the camera supplies; U1's decoupling; the power parts' GND vias. It also declares NETS / PARTIAL / RAILS / PENDING, runs a dry-run recorder (`build(b, dry=True)`) and checks every via's net after the fill |
| `m3_design/r9_power_check.py` | The step gate: template, in2, dc, supply, f9, pyro, contract, actuators, drc, route (§2). Judging functions importable (`parse_dc`, `judge_dc`, `judge_f9`, `judge_drc`, `chains`) |
| `m3_design/r9_place.tsv` | 42 rows changed, each basis naming its D-S6 (D-S6-01): the U9 cluster, the RAW_PROTECTED parts, the actuator driver column, C120 / R120 / TP121, the logic block (U11, U2, L1, C5-C9, C84 turned, C97-C99, R86-R88, C85), R80 / R165, C89, R89 / R91 (to the MCU end), TP80 / TP87 / TP90 |
| `m3_design/r9_build.sh` | Step-6 stages appended: `r9_power.py`, `r9_power_check.py --numpy-py "$NUMPY_PY"` |
| `tools/test_r9_power.py` | 19 tests: DC row judging (D12, R8 rises, D_raw, via currents, unbound / missing solves), the hot-plug judging, the DRC judging (pending vias, deferred silk, parity, step-net opens, partial nets), the pending-copper chains, the tables' widths; on the built board the template and In2 gates hold, a moved part stops the template, and extra / missing copper, an In2 track and a foreign In2 zone are each caught |
| `sources/r9_design/step6_evidence/hotplug_feed_r9.py` | R8's hot-plug model (imported unchanged) with R9's R_b and feed estimate (F9, D-S6-11) |
| `sources/r9_design/step6_evidence/` | `r9_power_check.{json,txt}` (the gate on the final board), `check_r9_full.{json,txt}` (the whole contract with plate, fit and seed), `rule_h_seed.{json,txt}`, `dc01_*.txt` / `dc005_*.txt` (the 7.7 A solves at 0.1 / 0.05 mm, each bound by SHA), `supply_dc.txt`, `hotplug_feed_r9.json`, `scorecard_quick.{md,json}` and `x_metrics.json` (the R9 scorecard at the 0.1 mm grid), `build.txt`, `build_sha256.txt`, `tests.txt` |

## 2. Verification (r9_plan §4 step 6 and the brief)

| Item | Result on board `47fb298d…` |
|---|---|
| run_dc at 0.1 mm: D12 limits | RAW_ACT 12.7 °C (≤ 20), BAT_IN 12.1 (≤ 20), ACT_FET_S 20.8 (≤ 30): OK |
| every rise ≤ R8 | R8 at 0.1 mm 17.6 / 14.8 / 22.3 °C: OK. At 0.05 mm: 12.7 / 12.1 / 20.4 against R8's 17.5 / 14.5 / 21.4-21.5: OK |
| D_raw ≤ 1.0 mΩ | 0.79 mΩ (R8 1.45); BAT_IN 0.17 (0.44), ACT_FET_S 0.27 (0.19) |
| necks | RAW_ACT 7.82 mm B.Cu (R8 5.90), BAT_IN 8.19 mm B.Cu (6.85), ACT_FET_S 5.11 mm B.Cu (4.80) |
| barrel current ≤ 1 A per via | 7.7 A paths: 0.65 A max (BAT_IN), RAW_ACT 0.46, ACT_FET_S 0.25; none over 0.65 A. RAW_PROTECTED → U11 0.50 A at 0.5 A; the U7 and CAM_5V vias each 1.00 A at a 1 A load (one via, as R8) |
| D18 (inner RAW_ACT / BAT_IN ≥ 2.65 mm plan view from bus / igniter / drain) | 4.953 mm (In2 RAW_ACT to R131.1); R8 2.65 |
| D85 / X2d (battery-live ≥ 2.5 mm same layer from armed copper) | no BAT_IN / ACT_FET_S copper within the check's reach; X2 = X2b = 0 (no foreign net within 3 mm of armed copper) |
| F9 hot-plug feed | U9 13.22 mm from J1.1 (F9-1 ≤ 27.07; the protection parts 4.69-8.90 ≤ 10.6). R_b 2.32 mΩ (R8 17.3), feed ≈ 3.2 nH (estimate). R8's model gives U9 IN within 0.0021 V / x1.028 slew of the input node, and 0.0036 V / x1.037 at R8's 5 nH bound. The R4 figures stay inside the TPS25947's −15 V / 10 V/µs (≈ −14.60 V, 9.46 V/µs) |
| check_r9 power / pyro rules | the whole contract passes but K-legends (step 8) and K-contract's camera-bypass routes C100 / C93 (step 7). Among them: LC-1, P-0 (A 0.27, B 0.32, C 0.277, D 0.251, G 0.112 (D-S5-13), H 0.225; H+ 0.025, GS 0.48, AG 0.134), P-3 (no foreign net in the hull), P-4 (seeded suite OK), P-5 (133 pairs, 0 forbidden), P-6 (1.03 mm), P-7, M-2 (252.3 Hz), M-5 (support 4.600 / 5.008), M-6, R-1 … R-13, F9-1, K-copper, K-power-pyro, K-inner (no In1 / In2 track). C29's direct route now holds |
| step-5 pyro gates on the powered board | margins at their floors (D-S5-13's exception only), bridge table 0 forbidden and no fires-class pair between parts under 1.5 mm, GATE_N's neighbours GND only (0.888 mm), sense MCU sides clean, X2 = 0 |
| In2 | four regions, each one piece (RAW_ACT 244.5, BAT_IN 115.3, 3V3 1098.9 mm²), GND the rest, no track |
| DRC + parity | 0 violations but step 8's silkscreen classes and 9 dangling GND vias (the 8 of PENDING and step 5's guard via, all waiting for In1 GND); 0 parity; no unconnected item on NETS; partial nets open only at R177.1, R60.1, U13.1 / R104.1 / C91.1 |
| route_check r9 | 0 failing but those vias and their straps (dangling_via / dead_copper); info on the step's nets: 5 pad_end_offcentre, 2 segment_inside_pad, 6 passes_through_pad, 3 width changes, 5 power vias without a GND via within 1.5 mm |
| template | 153 segments, 97 vias, 11 zones, 319.9 mm of track, equal to the builder's dry run; nothing else on the step's nets |
| reproducible | two full builds: board, sheets, netlist, DRU and variant files byte-identical (`build_sha256.txt`) |
| tests | 23 suites / 417 tests OK (test_r9_power 19 new); quality_audit 21 OK under both pythons; audit_artifacts exit 0 |
| scorecard (0.1 mm) | index_r9 56.8 (≤ 73). Power done rows met. Missed: X2g = 1 and P6 1201 mm (D-S6-13). P7 / P9 / P10 / R6b are step 8's |

## 3. Reproduce

```bash
R=rocket-pcb/rocket-flight-computer-r9                                    # this worktree
KP=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
NP=<python3 with numpy>                                                   # the parent project's cfd/venv/bin/python3
NUMPY_PY=$NP $R/m3_design/r9_build.sh       # steps 2-6 and their gates (~6 min); needs a GUI session for kicad-cli DRC
(cd $R && PYTHONUNBUFFERED=1 $KP -I -B m3_design/r9_power_check.py --numpy-py $NP --report out.json --dc-dir dc)  # ~3 min
(cd $R && bash tools/run_dc.sh m3_design/assembly_review/m3.kicad_pcb dc005 0.05)     # the qualification grid
(cd $R/m3_design/assembly_review/sources/r9_design/step6_evidence && $NP -I hotplug_feed_r9.py --rb 2.32)
(cd $R/tools && $KP -B -m unittest test_r9_power)
NO_GATE=1 DC_GRID=0.1 NUMPY_PY=$NP bash $R/tools/run_r9_survey.sh $R/m3_design/assembly_review/m3.kicad_pcb survey
```
Without a GUI session, see §6.

## 4. What the next steps must know

**Copper the step owns** (r9_power_check's template rejects anything else on these nets in the build):
- NETS (complete): BAT_IN, BAT_DAMP, BAT_SW_SOURCE, BAT_SW_RETURN, ACT_FET_S, ACT_GATE, ACT_DRV, ACT_EN,
  RAW_PROTECTED, SW_NODE, BST, CAM_INPUT_LIMITED, CAM_SW, CAM_BST, CAM_FB, VCAP1, VCAP2.
- PARTIAL: RAW_ACT (open at R177.1), VLOGIC (R60.1), CAM_5V (U13.1, R104.1, C91.1).
- A later step that adds copper to one of these nets edits its own gate's expectations. r9_power_check stays a step-6
  gate: it runs on the step-6 board in the build.

**Step 7 (routing families).**
- **power_ctl** owns:
  - U9's control pins: EN (U9.1), OVLO (U9.2 - R82.2 - R83.1), FLT (U9.4), DVDT (U9.7 - C81.1), ILIM (U9.9 - R84.1 -
    TP89) and its GND pin U9.8;
  - U11's: OVLO (U11.5 - R87.2 - R88.1), ST (U11.9), ILIM (U11.10 - R86.1), SS (U11.11 - C85.1) and GND (U11.3 / 4 / 6
    / 12; the step drew only U11.12's strap);
  - U7's, which are the camera family's in R8;
  - BAT_ENABLE: R165.2 at J1.4 (14.03, 90.2) → U9.1, R81.1, C87.1 (top) and TP84, about 28 mm across the forward
    edge;
  - BAT_FAULT_N / LOGIC_SOURCE_ST: R89 / R91 now sit at the MCU end (28.8, 46.9 / 45.0, bottom); their lanes run to
    U9.4 / TP85 and U11.9 / TP87 in the east column;
  - USB_LIMITED.
- **USB_LIMITED corridor note** (measured on this board, 0.4 mm lane, `corridor.py` in scratch). U10.6 (13.9, 31.95),
  C86.1, TP82 → C98.1 (36.23, 62.8), R87.1, U11.7 (39.3, 65.83). R8 drew it in its power step (D42: B.Cu under U1's
  aft row, north at x 29.95, one F.Cu hop, east to C98). R9's middle band is denser.
  - Clear runs (≥ 1.0 mm from all copper):
    - B.Cu and F.Cu, the gap band y 26.5 from x 16 to 28.9;
    - F.Cu, x 28.9 from y 26.5 to 43.6;
    - B.Cu, x 36.23 from y 57.4 to 62.8 into C98.1 (C98.2 0.895 mm).
  - F.Cu x 33.0 from y 27 to 51.5 is clear today (0.45 mm to a GND via), but U1 → U12's camera UART lanes cross it.
  - Blocked runs:
    - B.Cu x 28.9 north: D122, R161, R70, TP73's 1.0 mm zone, C90, R177, R89 / R91;
    - B.Cu y 36.3 under U1's aft row: R70;
    - F.Cu x 28.9 above y 43.6: R170 and the ARM lane;
    - the J122-east passage at y 56.6: R103.1 0.35 mm, R157.1 0.49 mm, the tie hole (30.8, 59) 0.6 mm.
  - Inference: every candidate crosses lanes other families have not drawn yet (U1.27-31's eastward escapes, D-S5-02,
    and the camera UART). Plan it first in power_ctl, with those families' layer assignment, or re-place R89 / R91 / R103 / TP73 if needed
    (record why).
- **The RAW_ACT_SENSE tap** (step 7 "pyro" family, D-S5-07): R177.1 joins RAW_ACT. The RAW_ACT B.Cu pour's south-west
  corner is (18.4, 60.56) and the F.Cu pour starts at y 65.4. Keep rule A + 0.2 mm from ARM1_SENSE (fill margins do this
  for pours).
- **VLOGIC_SENSE** R60.1 (15.42, 54.5) joins VLOGIC (nearest copper: the U11 / U2 column x 40.0, the C84 via (38.2,
  69.6), TP83's via (44.6, 66.2)).
- **CAM_5V to U13.1 / R104.1 / C91.1** and K-contract's C100 / C93 bypass routes are the camera family's.
- **3V3**: the In2 region covers x 0.5-35.3 from y 23.5, the camera tongue to x 38.0 for y 52-56.7, and the finger x
  36.3-37.8 up to y 79.3. Pull-ups and bypasses tap it by vias; keep its north edge (the CH1 hull) GND-only (P-3).
- The step's vias step 7 must keep clear of: R122's (37.26, 80.9), U11's IN1 (39.3, 68.2), U7's (42.15, 31.5), the
  VLOGIC (38.2, 69.6), (44.6, 66.2), 3V3 (37.6, 78.9), FB (37.3, 71.3), CAM_FB (38.25, 37.1) and CAM_5V (40.75, 45.4)
  vias, and the ACT_GATE hop vias (26.6, 87.4) / (37.35, 89.0). The F.Cu ACT_GATE hop runs y 87.4 from x 26.6 to 36.6.

**Step 8 (ground).**
- **Pending:** the GND vias of `r9_power.PENDING` sit in In2 3V3 / RAW_ACT and wait for In1 GND: (24.25, 40.9),
  (12.5, 40.8), (16.4, 38.8), (9.85, 52.8), (16.82, 55.3), (24.2, 47.7), (12.88, 49.85), (31.4, 73.6). Step 5's guard
  via (13.5, 54.6) waits too.
- The F.Cu / B.Cu GND pours must keep the DRU's fill margins near pyro copper (automatic).
- The power pours have priority 20 (In2 regions 10-12; R9_GND_In2 2, and the strip's In2 pour keeps its own). A
  board-wide F.Cu / B.Cu GND pour needs a lower priority than 20, so the power pours win.
- The east column's GND pads with no copper yet (DRC on the final board):
  - U9.8, U11.3 / 4 / 6 (power_ctl may strap them between the control pins);
  - C81.2, R84.2, R83.2, R81.2, R86.2, C85.2, R88.2, C98.2, and C87.2 on the top;
  - the hold-up C84.2 (top, 1.9 x 4.4 mm, (37.0, 84.85)) and C121.2 (top, (33.4, 63.3)), which need the F.Cu pour and
    vias;
  - TP74 / TP88 (the GND test pads).
  They need the pours and stitching.
- The scorecard's P7 / P9 / P10 / R6b are step 8's; P6 (In2 perimeter) is D-S6-13's recorded miss.

**Records (steps 9-10).**
- F7's fire-loop revalidation on the final copper: J124.2's RAW bar adds 10.5 mΩ (dc_solve).
- The 7.7 A stall test (ORDERING §5); the hot-plug bench test (U9 IN).
- M3_R9's power table: D-S6-02's and D-S6-05 / 06's figures; the In2 plan (D-S6-03).
- The owner's deviation list: D-S6-13 (X2g, P6).

## 5. Open

- **Not blockers for step 6, risks for step 7:** the USB_LIMITED corridor (§4) and the power_ctl lanes into the
  east column (BAT_ENABLE across the forward edge, the status lanes past the camera translator cluster and the mid
  support). Step 7 may need to re-place small parts with recorded reasons.
- **Done-row misses for the owner (D-S6-13), not unsafe:**
  - X2g = 1: ACT_GATE to TP121 in the CH1 courtyard box's empty corner. No legal TP121 spot exists outside the box.
  - P6 1201 mm (≤ 900): inherent to four In2 regions, each boundary counted twice (Inference).
- **Minor:**
  - VLOGIC C84.1 → U2: 9.84 mΩ (R8 2.60), because the hold-up sits over the FET pair; 3 mV at 0.3 A.
  - Info-level pad entries: Q120.4's gate exits at 45 degrees from its centre. U11.1, C99.1, U2.3 and C6.1 sit on the
    VLOGIC column, and C120.2 on the gate bus, as passes-through. C97.1's IN1 entry lands 0.325 mm off centre.
  - The stretch row "all three necks inside 20 °C": ACT_FET_S 20.8 / 20.4 °C, limited by the FETs' own pins.
- **No question for the owner** arises: nothing is unsafe and no requirement's intent changes.

## 6. Environment: kicad-cli DRC without a GUI session

After the reboot nobody is logged into the Mac's GUI (loginwindow at the login screen, no Aqua session for the user),
so `[NSScreen screens]` is empty. `kicad-cli 10.0.6 pcb drc` (only DRC: ERC, exports and renders run) crashes:
`JobExportDrc → BOARD_COMMIT::Push → TOOL_MANAGER::doRunAction → wxGetMousePosition → wxFromNSPoint`, then a Swift
"Array index out of range". All gates of steps 2-6 call it. Step 6 ran them with a scratch dylib that interposes both
`wxGetMousePosition` overloads to (0, 0), loaded through `DYLD_INSERT_LIBRARIES` (kicad-cli's entitlements allow
DYLD variables). `/bin/bash` (SIP) strips DYLD_*, so `r9_build.sh`'s stages were replayed one by one from KiCad's python
by a scratch runner that reads the script's own command lines. Validated: the step-5 gate on the step-5 board gave
exactly its recorded result (DRC OK); the replayed builds are byte-identical; DRC finds real violations with it
(the R123 rotation short during the work). Nothing in the repo depends on the shim. **To run `r9_build.sh` unchanged,
log into the GUI (or connect by screen sharing) first.**

To regenerate the shim (session scratch `<scratch>/s6/`; nothing goes into the repo):

```cpp
// nomouse.cpp: wxGetMousePosition() without a screen (kicad-cli pcb drc, no GUI session)
struct wxPoint { int x, y; };
wxPoint wxGetMousePosition();
void wxGetMousePosition(int *x, int *y);
static wxPoint my_mouse_pt() { wxPoint p; p.x = 0; p.y = 0; return p; }
static void my_mouse_xy(int *x, int *y) { if (x) *x = 0; if (y) *y = 0; }
struct interpose { const void *replacement; const void *replacee; };
__attribute__((used)) static const interpose interposers[] __attribute__((section("__DATA,__interpose"))) = {
    {(const void *)(wxPoint (*)())my_mouse_pt, (const void *)(wxPoint (*)())wxGetMousePosition},
    {(const void *)(void (*)(int *, int *))my_mouse_xy, (const void *)(void (*)(int *, int *))wxGetMousePosition},
};
```
```bash
F=/Applications/KiCad/KiCad.app/Contents/Frameworks
clang++ -dynamiclib -o nomouse.dylib nomouse.cpp $F/libwx_osx_cocoau-3.2.0.4.1.dylib -Wl,-rpath,$F
DYLD_INSERT_LIBRARIES=$PWD/nomouse.dylib <KiCad python3> -I -B m3_design/r9_power_check.py --numpy-py <numpy python3>
```
Run each `r9_build.sh` line in that environment from an unprotected process (not /bin/bash or /bin/zsh scripts, which
strip DYLD_*). Step 6's runner (`<scratch>/s6/tools/build.py`) reads the script's command lines, expands its
variables and runs them in order with the variable set; it stops at the first failing stage, as `set -e` does.
