#!/usr/bin/env bash
# Build M3-ASSY-R10 (r10_plan.md; R10_DECISIONS.md, D-R2-15) into m3_design/assembly_review from the hash-pinned R9
# inputs: r10_sch.py checks sources/r10_design/r9_input/manifest.json before generating, and r10_pcb.py reads R9's
# board as a git blob (commit 40a1d28, SHA-256 4f841a0e...) without restoring or checking anything out.
#
# usage: m3_design/r10_build.sh            (from anywhere in the repo)
#        KICAD_PY=/path/to/kicad/python3 NUMPY_PY=/path/to/python3-with-numpy m3_design/r10_build.sh
#
# Stages, each deterministic (fixed UUID namespaces and KIID seeds, explicit tables, no search):
#   r10_sch.py        the 15 sheets, schematic.net.xml (kicad-cli export), m3.kicad_dru (board-default clearance, no
#                     pyro / RF spacing rule: r10_plan section 2 item 1), m3.kicad_pro, the PortLDO symbol
#   gate              r10_sch_check.py: every pin and fitted part against circuit.json / pin_table.tsv, the safety and
#                     UART-isolation contracts, strict ERC, a fresh netlist export, deterministic regeneration and nine
#                     seeded contract faults (in memory)
#   r10_pcb.py        the placement board from r10_place.tsv on R9's netlist importer: 46 x 90 mm outline, five M3
#                     supports, J122's two tie holes, every part placed, no inherited copper
#   r10_route.py F    the copper, one family per run (core: R9's MCU / QSPI / HSE / IMU / barometer tables translated;
#                     usb; pyro; power: In2's four rail regions, BAT_IN, the buck / LDO supplies, hand joins; signals:
#                     every remaining signal hand-drawn, D-R2-08; ground: F.Cu / B.Cu GND pours, the frozen plane-via
#                     table m3_design/r10_fanout.tsv, every via's unconnected inner pads removed)
#   gate              r10_stage_check.py F after each family: DRC (only GND ends pending the ground family may
#                     dangle), unconnected items never rising (after signals only on the ground family's nets, after
#                     ground none), route_check --profile r10 (failing only on pending nets; after ground none)
#   r10_post.py       the silkscreen, pin-1 dots, designators by the R4 rule, Fab references, the title block and the
#                     final zone fill (no copper, zone or pad change: asserted)
#   gate              tools/check.sh, the full gate on the finished board: DRC every severity (silkscreen included)
#                     with schematic parity, ERC, metadata / 3D models, silkscreen outline, fit, plate model,
#                     check_r10, route_check r10, check_actuators
#   record            r10_sch_check.py --binding-note: sources/r10_design/r10_binding_note.json with the board's
#                     SHA-256, U1's pin map read from the board and U4's position / rotation (firmware evidence only)
# It overwrites the sheets, schematic.net.xml, m3.kicad_dru, m3.kicad_pro, kilib/m3.kicad_sym and m3.kicad_pcb in
# m3_design/assembly_review, and the binding note: commit your own changes first. A rebuild reproduces m3.kicad_pcb byte for byte.
set -euo pipefail
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
KICAD_PY=${KICAD_PY:-/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3}
KICAD_CLI=${KICAD_CLI:-/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli}
NUMPY_PY=${NUMPY_PY:-python3}
export KICAD_CLI
D=m3_design/assembly_review
T=$(mktemp -d)
trap 'echo "build reports: $T"' EXIT
quiet() { grep -v 'Debug: Adding duplicate\|create wxApp\|Fontconfig' || true; }
python3 -B m3_design/r10_sch.py --out "$D"
PYTHONUNBUFFERED=1 "$KICAD_PY" -I -B m3_design/r10_sch_check.py --project "$D" --json "$T/sch_check.json" \
  > "$T/sch_check.txt" 2>&1 || { echo "r10_sch_check: FAIL (see $T/sch_check.json)"; exit 1; }
echo "r10_sch_check: OK"
PYTHONUNBUFFERED=1 "$KICAD_PY" -I -B m3_design/r10_pcb.py 2>&1 | quiet
for FAMILY in core usb pyro power signals ground; do
  PYTHONUNBUFFERED=1 "$KICAD_PY" -I -B m3_design/r10_route.py "$FAMILY" 2>&1 | quiet
  PYTHONUNBUFFERED=1 "$KICAD_PY" -I -B m3_design/r10_stage_check.py "$FAMILY" --state "$T/stage.json" 2>&1 | quiet
done
PYTHONUNBUFFERED=1 "$KICAD_PY" -I -B m3_design/r10_post.py --report "$T/post.json" 2>&1 | quiet
shasum -a 256 "$D/m3.kicad_pcb"
# OQ-2: qualify the generated input feed before the full board gate.
"$KICAD_PY" -I -B tools/r10_hotplug.py --extract "$D/m3.kicad_pcb"
"$NUMPY_PY" -I -B tools/r10_hotplug.py
# the fab package is bound to the board it was made from: rebuild it with m3_design/r10_fab.sh, then run tools/check.sh
R10_SKIP_FAB_MANIFEST=1 KICAD_PY="$KICAD_PY" NUMPY_PY="$NUMPY_PY" tools/check.sh
# the firmware binding evidence record (never an approval: AGENTS.md section 3), bound to the board just checked
PYTHONUNBUFFERED=1 "$KICAD_PY" -I -B m3_design/r10_sch_check.py --project "$D" --board "$D/m3.kicad_pcb" \
  --binding-note "$D/sources/r10_design/r10_binding_note.json" > "$T/binding.txt" 2>&1
echo "binding note: $D/sources/r10_design/r10_binding_note.json"
