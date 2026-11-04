#!/usr/bin/env bash
# The M3-ASSY-R11 fab package and its checks (D-R11-08, D-R11-67), on the board m3_design/r11_build.sh made: R10's
# m3_design/r10_fab.sh with R11's board, layers, corrections and binding (R10's tools and their inputs stay unchanged).
#
# usage: m3_design/r11_fab.sh               (from anywhere in the repo; m3_design/r11_build.sh runs it last)
#        FAB_NET=1 m3_design/r11_fab.sh     also prices and stocks the BOM at JLC for 5 boards (live public supplier
#                                           data, read-only, valid 24 h; writes fab/cost_check.json and stock_check.json)
#
#   jlc_orient_r11.py   placement corrections (tools/jlc_corrections_r11.json) by matching every LCSC footprint's pads to
#                       ours (tools/jlc_easyeda/pads_r11.json); fails on any part it cannot match ("CHECK: none")
#   export_fab_r11.py   Gerber zip (15 layers: six copper, PTH / NPTH drill, job file), the JLC BOM (one line per LCSC
#                       code), the CPL and the assembly drawings into m3_design/r11/fab, unbound (--pending)
#   fab_manifest_r11.py --bind   the content checks on the exported package, then the manifest binding it to the CAD and
#                       export inputs (the board's SHA-256), written only when every check passes:
#     check_r11.py --only S-4 --bom --cpl   every required-fitted part in the exported BOM and CPL; J1 / J121 wire pads
#                       on board and schematic, out of BOM and CPL
#     jlc_orient_r11.py --verify-cpl   every CPL row rebuilt from JLC's own footprint and compared with our pads
#     paste_check.py    the paste Gerbers against the pads: one opening per pasted pad, none stray
#   fab_manifest_r11.py the outputs still match the CAD and export inputs; tools/check.sh repeats the content checks
#   renders             m3_design/r11/r11_top.png and r11_bottom.png (kicad-cli pcb render)
#   FAB_NET=1           jlc_stock.py, jlc_cost.py --profile r10 (REQUIREMENTS M3's $84.41 per board, R10's cap, kept for
#                       R11: D-R11-01) on m3_design/r11/fab
# The Gerbers carry their creation date, so the package is not byte-reproducible; the manifest binds it instead.
set -euo pipefail
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
KICAD_PY=${KICAD_PY:-/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3}
KICAD_CLI=${KICAD_CLI:-/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli}
export KICAD_CLI KICAD_PY
D=m3_design/r11
B=$D/m3.kicad_pcb
grep -q '"M3-ASSY-R11"' "$B" || { echo "r11_fab: $B is not an M3-ASSY-R11 board"; exit 1; }
quiet() { grep -v 'Debug: Adding duplicate\|create wxApp\|Fontconfig' || true; }
RECORD_DIR="$(mktemp -d)"
trap 'rm -rf "$RECORD_DIR"' EXIT
PYTHONUNBUFFERED=1 "$KICAD_PY" -I tools/jlc_orient_r11.py tools/jlc_easyeda/pads_r11.json "$B" 2>&1 | quiet | tail -1
python3 tools/export_fab_r11.py "$B" --out "$D/fab" --pending "$RECORD_DIR/export.json"
python3 tools/fab_manifest_r11.py "$B" --bind "$RECORD_DIR/export.json"
python3 tools/fab_manifest_r11.py "$B"
for SIDE in top bottom; do
  "$KICAD_CLI" pcb render --side "$SIDE" -w 1150 -h 1250 --quality high -o "$D/r11_$SIDE.png" "$B" > /dev/null 2>&1
done
echo "renders: $D/r11_top.png $D/r11_bottom.png"
if [[ -n "${FAB_NET:-}" ]]; then
  STATUS=0
  python3 tools/jlc_stock.py --fab "$D/fab" --boards 5 || { STATUS=1; echo "jlc_stock: short lines above"; }
  python3 tools/jlc_cost.py --profile r10 --fab "$D/fab" --boards 5 || { STATUS=1; echo "jlc_cost: \$84.41 target missed (above)"; }
  exit $STATUS
fi
