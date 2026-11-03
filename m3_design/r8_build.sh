#!/usr/bin/env bash
# Build M3-ASSY-R8 from the committed, owner-accepted R7 (commit 431025d): a fresh, deterministic build, no R7 patch
# stages, no autorouter (r8_plan.md; R8_DECISIONS.md).
#
# usage: m3_design/r8_build.sh            (from anywhere in the repo)
#        KICAD_PY=/path/to/kicad/python3 m3_design/r8_build.sh
#
# Stages (build steps 2-8). Each step gate stays: it holds checks the full gate lacks (budgets, islands, GND reach, trims,
# reservations); the full gate tools/check.sh runs last, on the finished board:
#   schematic   R7's sheets and netlist restored from git (worktree only, the index is untouched), then r8_sch.py
#               applies pin_table.tsv and D4 and regenerates schematic.net.xml (step 2; byte for byte)
#   r8_pcb.py   R7's board restored from git (SHA-256 checked): R8 pad nets, the rigid R7 copper kept (check_r8 D15
#               groups), every other track / via / zone removed, TH1-TH3 removed, the placement of r8_place.tsv,
#               checked by r8_legalise.py against r8_keepclear.tsv (the build stops on any violation), native fill,
#               the 12 rigid digests asserted
#   gate        r8_place_check.py: rigid digests, legaliser, DRC with parity, F10 separation, fit against R7, tab
#               windows, placement MST, the check_r8 contract, check_actuators, sensor rule areas, reserved routes
#   r8_power.py the In2 map, the 7.7 A copper and via fields of spike (c), RAW_PROTECTED, the logic and camera supplies
#               (step 5), native fill, the 12 rigid digests asserted
#   gate        r8_power_check.py: rigid, DRC with parity (pyro rules A-H), complete power nets, D18 / D19, no inner
#               track, the In2 islands and GND under the CH1 pads and the pyro / servo lanes, route_check, the later
#               steps' reservations against the power copper (the 7.7 A DC solves run after step 7, below)
#   r8_route.py the signal families in order (step 6, R8_DECISIONS D51 on), one module m3_design/r8_route_<family>.py
#               each: qspi_hse, rf, servo, pyro, usb_swd, imu, camera, status, links; native fill, the 12 rigid
#               digests asserted
#   gate        r8_route_check.py FAMILY after each: rigid, DRC with parity, its nets complete (every net after
#               links), route_check, its length / via / ratio budget, D18 / D19, no inner track, In2, the check_r8
#               contract (later-step findings only), step 7's reservations
#   r8_ground.py the GND stitching of r8_ground.tsv (step 7, R8_DECISIONS D62 on): the strip fence row, spike (d)'s
#               stitches, C24's GND stub, GND vias beside power layer changes, the 4 mm stitching grid, island and
#               reach vias, seven pour trims (D65, D90); native fill, the 12 rigid digests asserted
#   gate        r8_ground_check.py: rigid, the table built, DRC with parity (every net whole), route_check (no
#               failure; A8 and D51 only), outer GND islands >= 2 vias (D63), GND via reach (D64), no via in a power
#               pour or 7.7 A corridor or by pyro copper, trims on GND only, D18 / D19, inner, In2, the check_r8
#               contract (fence, strip GND reach), L10, no reservation left
#   gate        tools/run_dc.sh at 0.1 mm: the three 7.7 A paths' IPC-2152 necks within R8_DECISIONS D12's limits
#               (RAW_ACT and BAT_IN 20 C, ACT_FET_S 30 C), exit 1 on a miss (fix pass 1, R8P1-INTEGRITY-02; the 0.05 mm
#               qualification solve stays a record item, docs/M3_R8.md "DC solve")
#   r8_post.py  the silkscreen, drawn again from nothing (step 8, R8_DECISIONS D71): jack, connector, pin-table, fuse,
#               revision and order-number legends beside their subjects, pin-1 dots, designators (>= 1.0 mm, nearer
#               their own part, courtyard test, no run-on text; the rest hidden and kept on Fab), Fab references; no
#               copper edit (asserted), the 12 rigid digests asserted
#   gate        tools/check.sh: DRC (every severity) with parity, ERC, metadata / 3D models, silkscreen in the outline,
#               check_r8, route_check r8, check_actuators, fit_check
# The fab package is not part of the build (its Gerbers carry a creation date): m3_design/r8_fab.sh makes and checks it.
# Every stage is deterministic (fixed KIID seed, no random search), so a run reproduces the files byte for byte. It
# overwrites the sheets, schematic.net.xml and m3.kicad_pcb in m3_design/assembly_review: commit or stash your own
# changes first.
set -euo pipefail
R7=431025d
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
KICAD_PY=${KICAD_PY:-/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3}
D=m3_design/assembly_review
git restore --source="$R7" --worktree -- "$D"/*.kicad_sch "$D"/schematic.net.xml
python3 m3_design/r8_sch.py --netlist
git restore --source="$R7" --worktree -- "$D"/m3.kicad_pcb
PYTHONUNBUFFERED=1 "$KICAD_PY" -I m3_design/r8_pcb.py
PYTHONUNBUFFERED=1 "$KICAD_PY" -I m3_design/r8_place_check.py
PYTHONUNBUFFERED=1 "$KICAD_PY" -I m3_design/r8_power.py
PYTHONUNBUFFERED=1 "$KICAD_PY" -I m3_design/r8_power_check.py
for FAMILY in qspi_hse rf servo pyro usb_swd imu camera status links; do
  PYTHONUNBUFFERED=1 "$KICAD_PY" -I m3_design/r8_route.py "$FAMILY"
  PYTHONUNBUFFERED=1 "$KICAD_PY" -I m3_design/r8_route_check.py "$FAMILY"
done
PYTHONUNBUFFERED=1 "$KICAD_PY" -I m3_design/r8_ground.py
PYTHONUNBUFFERED=1 "$KICAD_PY" -I m3_design/r8_ground_check.py
DC_OUT=$(mktemp -d)                  # the copper is final: the F4 / D12 neck limits at the 0.1 mm grid (fix pass 1)
KICAD_PY="$KICAD_PY" tools/run_dc.sh "$D/m3.kicad_pcb" "$DC_OUT" 0.1
rm -rf "$DC_OUT"
PYTHONUNBUFFERED=1 "$KICAD_PY" -I m3_design/r8_post.py
KICAD_PY="$KICAD_PY" tools/check.sh
