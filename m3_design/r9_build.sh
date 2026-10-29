#!/usr/bin/env bash
# Build M3-ASSY-R9 from the committed, owner-accepted R8 (commit 9c8179b): a clean-sheet B-spine board at 46 x 102 mm
# (98 mm planned; 102 mm by the step-3 kill path, owner decision 1; m3_design/assembly_review/sources/r9_design/
# r9_plan.md; R9_OWNER_DECISIONS.md; decisions in R9_DECISIONS.md).
#
# usage: m3_design/r9_build.sh            (from anywhere in the repo)
#        KICAD_PY=/path/to/kicad/python3 NUMPY_PY=/path/to/python3-with-numpy m3_design/r9_build.sh
#
# Stages (r9_plan.md section 4; each build step's stages and its step gate, and the full gate tools/check.sh last, on
# the finished board):
#   step 2  R8's sheets, netlist and design rules restored from git (worktree only, the index is untouched), then
#     r9_lib.py   the footprint variants M3_DB128L_2P_BK_SW (J121, J124) and HDR-TH_12P-P2.54-V-M-R3-C4-S2.54_MIR
#                 (J122), generated from their base footprints: the same parts on the same lands, the numbering
#                 mirrored (owner decisions 2 and 5)
#     r9_dru.py   m3.kicad_dru: rule G's P-1b scope; R8's pad clearance overrides become two rules (LC-1); the zone
#                 fill margins of pyro rules A-G / A2 (step 5, D-S5-12)
#     r9_sch.py   the sheets: the three footprint fields, notes, rev M3-ASSY-R9; schematic.net.xml regenerated
#     gate        r9_sch_check.py: ERC, the variants, the DRU against R8's, the netlist diff (footprint fields and rev
#                 only), RF / safety, BOM codes (52 extended), and on a scratch R8 board with the variants: parity,
#                 library match, LC-1, check_actuators, pin map, pad roles, DRU liveness, JLC placement
#   step 3  R8's board restored from git (worktree only), then
#     r9_pcb.py   the placement board from r9_place.tsv: the variants exchanged in place, overrides cleared (LC-1), every
#                 R8 track / via / zone / outline / hole / board drawing gone (the sensor and Y1 rule areas, PYRO_BLOCK
#                 and the ARM / IGN legends kept), the 46 x 102 mm outline, five M3 supports and J122's two tie holes,
#                 all 249 parts placed, PYRO_BLOCK derived from the CH1 placement, native fill; any legaliser violation
#                 stops the build
#     gate        r9_place_check.py: legaliser (all parts), DRC + parity, fit, plate f1, F9-1, R-10, the pyro pad
#                 rules (A-H, A2, H+, GS, AG, P-5, P-6), M-4, T-1, MST, check_r9's placement-bound rules,
#                 check_actuators, the rule areas. The plate model needs a python3 with numpy (NUMPY_PY)
#   step 4  r9_rf.py     the RF strip on the placement board: the U30 / U31 keep-outs and the launch cut-outs, the strip's
#                 GND pours (all four layers to y 23.0), the two RF chains and the launches by template in each jack's
#                 frame (R7's qualified geometry), each module's own copper and U30's antenna-bias limiter (B.Cu under
#                 U30) in the module's frame, the fence on y_f and the strip stitching grid; strip-internal nets only
#     gate        r9_rf_check.py: frames, R7 congruence (recorded deviations only), the launches against R7's J31,
#                 check_r9 R-1 ... R-13 / LC-1 / K-copper, GCPW 50 +- 2.5 ohm at every line sample (tools/gcpw_solve.py),
#                 route_check profile r9 (no allowlist), DRC + parity (no strip net open), the lane corridors kept free
#   step 5  r9_pyro.py   the CH1 pyro column, pad-referenced: the fire loop (J124 BUS == R134 == J121 IGN, J121 OUT into
#                 Q124's drain, C128, the R173 / R131 and R132 taps), the gate network with TP122 (its GND partner on
#                 Q124's source return) and the GATE_N guard, the CONT and ARM dividers with their exits to the 4.7 k
#                 at U1 (all F.Cu, one via: the gate's to TP122), D120's 3V3 feed out of the column; PYRO_BLOCK
#                 re-derived with the copper
#     gate        r9_pyro_check.py: the template, pyro_probe with every A-H / A2 margin >= max(R8, 0.2 mm), the bridge
#                 table (no fires-class pair under 1.5 mm), the seeded rule-H suite, GATE_N's neighbours (GND or
#                 < 0.2 V in reset within 1.5 mm), check_r9 LC-1 / P-0 ... P-11 / M-6 / R-13 / K-*, check_actuators,
#                 DRC + parity, route_check profile r9 (only the step's GND / 3V3 copper pending steps 6 and 8)
#   step 6  r9_power.py  the power copper on the frozen east column: In2's four regions (GND, RAW_ACT, BAT_IN, 3V3), the
#                 7.7 A path (BAT_IN, ACT_FET_S and RAW_ACT pours on F.Cu / B.Cu / In2 with their via fields, no series
#                 via), the actuator switch's gate network, RAW_PROTECTED (U9's output, an F.Cu pour down the east
#                 column, the U11 / R122 / TP81 / camera branches), VLOGIC and the 3V3 buck, the camera supplies, U1's
#                 decoupling and the power parts' GND vias
#     gate        r9_power_check.py: the template, In2's regions, tools/run_dc.sh at 0.1 mm (D12 and every rise <= R8,
#                 D_raw <= 1.0 mOhm, vias <= 1 A), the supply paths, F9's hot-plug feed (R8's model, NUMPY_PY), the
#                 step-5 pyro gates on the powered board, check_r9 (but M-2, K-legends and the camera bypass routes),
#                 check_actuators, DRC + parity, route_check profile r9 (only the In1-bound GND vias pending step 8)
#   step 7  r9_route.py FAMILY  the signal copper, one family per run in r9_route.FAMILIES order, each from its tables
#                 (m3_design/r9_route_<family>.py: deliberate octilinear polylines and vias, no autorouter)
#     gate        r9_route_check.py FAMILY after each: the template, DRC + parity (the done nets complete, only pending
#                 GND vias dangling), route_check profile r9 (empty allowlist), the family budget and S4's 70 signal
#                 vias, the step-5 pyro functions (GATE_N neighbours, X2), check_r9 (P-7, D19 in K-power-pyro, D20,
#                 R-1 ... R-13, ...), check_actuators
#   step 8  r9_ground.py  the ground: the RF strip's F.Cu / B.Cu / In1 GND pours grown over the board (same zones and
#                 settings), then the GND stitching of m3_design/r9_ground.tsv (vias and pad straps; generated by the design
#                 aid m3_design/r9_ground_aid.py and frozen; no pour trims), the crystal's In2 GND plane in place of its
#                 In2 void (AN2867), and every via's unconnected inner pads removed
#     gate        r9_ground_check.py: the pours, the table, the crystal plane and the via pads, DRC + parity (no
#                 unconnected item, GND included; only the silkscreen classes step 9 settles), route_check profile r9 (no
#                 failing instance: no GND sliver, finger, dangling or dead copper, a GND via at every critical layer
#                 change), the stitching's keep-outs (power pours, the 7.7 A In2 corridors, pyro copper), In2's regions
#                 whole, In2 under the crystal GND only, P7 islands (recorded pockets only), P9 / P10 reach, the
#                 critical-reference count and its classes, the step-5 pyro functions, check_r9, check_actuators
#   step 9  r9_post.py   the silkscreen drawn from nothing: the SMA jack legends, J122's plug numbers, the part legends
#                 beside their parts (connector words, pin tables, fuse / arming notes), the terminal pin legends by pin
#                 (each nearest its own pin), the revision legend and JLC's order-number mark, pin-1 dots, every
#                 designator by the R4 rule (hidden ones kept on Fab), the Fab designators, the title-block revision; no
#                 copper, zone, pad or footprint position changes (asserted)
#     gate        r9_post_check.py: every required legend once, check_r9 K-legends, ARM / IGN, designator and legend
#                 text sizes, and the final copper's 7.7 A paths (D12, every rise <= R8, D_raw, via currents), supply
#                 paths and F9 hot-plug premise at 0.1 mm (D-S9-04)
#     gate        tools/check.sh, the full gate, on the finished board: DRC (every severity, silkscreen included) with
#                 parity, ERC, metadata / 3D models, silkscreen outline, fit, plate model, seeded rule-H suite,
#                 check_r9, route_check r9, check_actuators. The fab package is m3_design/r9_fab.sh's (not byte-
#                 reproducible: the Gerbers carry their creation date)
# Every stage is deterministic (fixed UUID namespaces and KIID seed, no search), so a run reproduces the files byte for
# byte. It overwrites the sheets, schematic.net.xml, m3.kicad_dru, the two variant footprints and m3.kicad_pcb in
# m3_design/assembly_review: commit or stash your own changes first.
set -euo pipefail
R8=9c8179b
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
KICAD_PY=${KICAD_PY:-/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3}
NUMPY_PY=${NUMPY_PY:-python3}
D=m3_design/assembly_review
git restore --source="$R8" --worktree -- "$D"/*.kicad_sch "$D"/schematic.net.xml "$D"/m3.kicad_dru
python3 -B m3_design/r9_lib.py
python3 -B m3_design/r9_dru.py
python3 -B m3_design/r9_sch.py --netlist
PYTHONUNBUFFERED=1 "$KICAD_PY" -I -B m3_design/r9_sch_check.py
git restore --source="$R8" --worktree -- "$D"/m3.kicad_pcb
PYTHONUNBUFFERED=1 "$KICAD_PY" -I -B m3_design/r9_pcb.py
PYTHONUNBUFFERED=1 "$KICAD_PY" -I -B m3_design/r9_place_check.py --numpy-py "$NUMPY_PY"
PYTHONUNBUFFERED=1 "$KICAD_PY" -I -B m3_design/r9_rf.py
PYTHONUNBUFFERED=1 "$KICAD_PY" -I -B m3_design/r9_rf_check.py
PYTHONUNBUFFERED=1 "$KICAD_PY" -I -B m3_design/r9_pyro.py
PYTHONUNBUFFERED=1 "$KICAD_PY" -I -B m3_design/r9_pyro_check.py
PYTHONUNBUFFERED=1 "$KICAD_PY" -I -B m3_design/r9_power.py
PYTHONUNBUFFERED=1 "$KICAD_PY" -I -B m3_design/r9_power_check.py --numpy-py "$NUMPY_PY"
PYTHONUNBUFFERED=1 "$KICAD_PY" -I -B m3_design/r9_route.py rf_if
PYTHONUNBUFFERED=1 "$KICAD_PY" -I -B m3_design/r9_route_check.py rf_if
PYTHONUNBUFFERED=1 "$KICAD_PY" -I -B m3_design/r9_route.py qspi_hse
PYTHONUNBUFFERED=1 "$KICAD_PY" -I -B m3_design/r9_route_check.py qspi_hse
PYTHONUNBUFFERED=1 "$KICAD_PY" -I -B m3_design/r9_route.py pyro
PYTHONUNBUFFERED=1 "$KICAD_PY" -I -B m3_design/r9_route_check.py pyro
PYTHONUNBUFFERED=1 "$KICAD_PY" -I -B m3_design/r9_route.py servo
PYTHONUNBUFFERED=1 "$KICAD_PY" -I -B m3_design/r9_route_check.py servo
PYTHONUNBUFFERED=1 "$KICAD_PY" -I -B m3_design/r9_route.py imu_baro
PYTHONUNBUFFERED=1 "$KICAD_PY" -I -B m3_design/r9_route_check.py imu_baro
PYTHONUNBUFFERED=1 "$KICAD_PY" -I -B m3_design/r9_route.py usb_swd
PYTHONUNBUFFERED=1 "$KICAD_PY" -I -B m3_design/r9_route_check.py usb_swd
PYTHONUNBUFFERED=1 "$KICAD_PY" -I -B m3_design/r9_route.py camera
PYTHONUNBUFFERED=1 "$KICAD_PY" -I -B m3_design/r9_route_check.py camera
PYTHONUNBUFFERED=1 "$KICAD_PY" -I -B m3_design/r9_route.py status
PYTHONUNBUFFERED=1 "$KICAD_PY" -I -B m3_design/r9_route_check.py status
PYTHONUNBUFFERED=1 "$KICAD_PY" -I -B m3_design/r9_route.py power_ctl
PYTHONUNBUFFERED=1 "$KICAD_PY" -I -B m3_design/r9_route_check.py power_ctl
PYTHONUNBUFFERED=1 "$KICAD_PY" -I -B m3_design/r9_route.py links
PYTHONUNBUFFERED=1 "$KICAD_PY" -I -B m3_design/r9_route_check.py links
PYTHONUNBUFFERED=1 "$KICAD_PY" -I -B m3_design/r9_ground.py
PYTHONUNBUFFERED=1 "$KICAD_PY" -I -B m3_design/r9_ground_check.py
PYTHONUNBUFFERED=1 "$KICAD_PY" -I -B m3_design/r9_post.py
PYTHONUNBUFFERED=1 "$KICAD_PY" -I -B m3_design/r9_post_check.py --numpy-py "$NUMPY_PY"
KICAD_PY="$KICAD_PY" NUMPY_PY="$NUMPY_PY" tools/check.sh
