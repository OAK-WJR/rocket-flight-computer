#!/usr/bin/env bash
# Regenerate M3-ASSY-R4 from the M3-ASSY-R3 design files (docs/M3_R4.md "How R4 is built").
#
# usage: m3_design/r4_build.sh            (from anywhere in the repo)
#        KICAD_PY=/path/to/kicad/python3 m3_design/r4_build.sh
#
# Restores the R3 board, schematic sheets and footprint library from git (commit R3 below, worktree
# only, the index is untouched), runs r4_lib.py, r4_sch.py and r4_pcb.py, then the board gate and the
# actuator safety contract. It overwrites m3_design/assembly_review/*.kicad_pcb/.kicad_sch and the
# library files it edits, so commit or stash your own changes first. The fab package is not rebuilt:
# run tools/jlc_orient.py, tools/export_fab.py, tools/jlc_stock.py and tools/jlc_cost.py afterwards.
set -euo pipefail
R3=533af8e
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
KICAD_PY=${KICAD_PY:-/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3}
D=m3_design/assembly_review
git restore --source="$R3" --worktree -- "$D"/*.kicad_pcb "$D"/*.kicad_sch "$D"/kilib/rocket.pretty
"$KICAD_PY" -I m3_design/r4_lib.py
python3 m3_design/r4_sch.py
"$KICAD_PY" -I m3_design/r4_pcb.py
# netlist evidence hashed by quality_audit/verify_board.py: regenerated, with the local source path made relative
CLI=${KICAD_CLI:-$(command -v kicad-cli || echo /Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli)}
"$CLI" sch export netlist --format kicadxml -o "$D/schematic.net.xml" "$D/m3.kicad_sch" >/dev/null
python3 - "$D/schematic.net.xml" "$(cd "$D" && pwd)/" <<'PY'
import sys, re
from pathlib import Path
p, root = Path(sys.argv[1]), sys.argv[2]
t = p.read_text().replace(root, '')
p.write_text(re.sub(r'<date>[^<]*</date>', '<date></date>', t))
PY
tools/check.sh
python3 m3_design/check_actuators.py
