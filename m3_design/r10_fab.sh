#!/usr/bin/env bash
# The M3-ASSY-R10 fab package and its checks (R10_DECISIONS D-R2-15), on the board m3_design/r10_build.sh made
# (R9's m3_design/r9_fab.sh with R10's board, renders and cost target; the tools are the same).
#
# usage: m3_design/r10_fab.sh               (from anywhere in the repo)
#        FAB_NET=1 m3_design/r10_fab.sh     also prices and stocks the BOM at JLC (live public supplier data, read-only,
#                                           valid 24 h)
#
#   jlc_orient.py   placement corrections (tools/jlc_corrections.json) by matching every LCSC footprint's pads to ours;
#                   fails on any part it cannot match ("CHECK: none")
#   export_fab.py   Gerber zip (11 layers, PTH / NPTH drill, job file), the JLC BOM (one line per LCSC code), the CPL
#                   and the assembly drawings, unbound: it deletes the old manifest and records the export (--pending)
#   fab_manifest.py --bind   R18-GATE-04: the content checks on the exported package, then the manifest binding it to
#                   the CAD and export inputs (the board's SHA-256), written only when every check passes:
#     check_r10.py --only S-4 --bom --cpl   R1-07: every required-fitted part is in the exported BOM and CPL
#     jlc_orient.py --verify-cpl   every CPL row rebuilt from JLC's own footprint and compared with our pads
#     paste_check.py  the paste Gerbers against the pads: one opening per pasted pad, none stray
#   fab_manifest.py the outputs still match the CAD and export inputs; tools/check.sh repeats the content checks
#   renders         m3_design/assembly_review/r10_top.png and r10_bottom.png (kicad-cli pcb render)
#   FAB_NET=1       jlc_stock.py, jlc_cost.py against REQUIREMENTS M3's R10 target (R3's $84.41 per board: R10 carries
#                   no on-board radio or GPS, so R7's $42.00 RF allowance no longer applies; code counts informational;
#                   R10_DECISIONS D-R1-06) and check_procurement.py --profile r10 --cost-only
# The Gerbers carry their creation date, so the package is not byte-reproducible; the manifest binds it instead.
set -euo pipefail
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
KICAD_PY=${KICAD_PY:-/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3}
KICAD_CLI=${KICAD_CLI:-/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli}
export KICAD_CLI
D=m3_design/assembly_review
B=$D/m3.kicad_pcb
grep -q '"M3-ASSY-R10"' "$B" || { echo "r10_fab: $B is not an M3-ASSY-R10 board"; exit 1; }
quiet() { grep -v 'Debug: Adding duplicate\|create wxApp\|Fontconfig' || true; }
RECORD_DIR="$(mktemp -d)"
trap 'rm -rf "$RECORD_DIR"' EXIT
PYTHONUNBUFFERED=1 "$KICAD_PY" -I tools/jlc_orient.py tools/jlc_easyeda/pads.json "$B" 2>&1 | quiet | tail -1
python3 tools/export_fab.py "$B" --pending "$RECORD_DIR/export.json"
# R1-07 / R3-GATE-05 / R18-GATE-04: S-4 on the exported BOM and CPL (every required-fitted safety and contract part, with
# its native identity), jlc_orient --verify-cpl and paste_check (tools/fab_manifest.content_checks), then the manifest;
# any failing check fails the script and leaves the package unbound
KICAD_PY="$KICAD_PY" python3 tools/fab_manifest.py "$B" --bind "$RECORD_DIR/export.json"
python3 tools/fab_manifest.py "$B"
RENDER_DIR=${R10_RENDER_DIR:-$D}
mkdir -p "$RENDER_DIR"
for SIDE in top bottom; do
  "$KICAD_CLI" pcb render --side "$SIDE" -w 1016 -h 1988 --quality high -o "$RENDER_DIR/r10_$SIDE.png" "$B" > /dev/null 2>&1
done
echo "renders: $RENDER_DIR/r10_top.png $RENDER_DIR/r10_bottom.png"
if [[ -n "${FAB_NET:-}" ]]; then
  python3 tools/jlc_stock.py || echo "jlc_stock: short lines above (U4 is consigned when out of JLC stock: ORDERING section 1)"
  STATUS=0
  python3 tools/jlc_cost.py --profile r10 || { STATUS=1; echo "jlc_cost: R10 target missed (above)"; }
  python3 tools/check_procurement.py --profile r10 --cost-only || STATUS=1
  exit $STATUS
fi
