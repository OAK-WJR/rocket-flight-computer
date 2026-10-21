#!/usr/bin/env bash
# The M3-ASSY-R8 fab package and its checks (build step 8, R8_DECISIONS D72), on the board m3_design/r8_build.sh made.
#
# usage: m3_design/r8_fab.sh               (from anywhere in the repo)
#        FAB_NET=1 m3_design/r8_fab.sh     also prices and stocks the BOM at JLC (live supplier data, valid 24 h)
#
#   jlc_orient.py   placement corrections (tools/jlc_corrections.json) by matching every LCSC footprint's pads to ours;
#                   fails on any part it cannot match ("CHECK: none")
#   export_fab.py   Gerber zip (11 layers, PTH / NPTH drill, job file), the JLC BOM (one line per LCSC code), the CPL,
#                   the assembly drawings and the manifest binding them to the CAD inputs
#   jlc_orient.py --verify-cpl   every CPL row rebuilt from JLC's own footprint and compared with our pads
#   paste_check.py  the paste Gerbers against the pads: one opening per pasted pad, none stray, none on the SMA jacks
#                   or the unfitted lands
#   fab_manifest.py the outputs still match the CAD and export inputs
#   renders         m3_design/assembly_review/r8_top.png and r8_bottom.png (kicad-cli pcb render, as R7's)
#   FAB_NET=1       jlc_stock.py, jlc_cost.py (REQUIREMENTS M3: <= $126.41 per board, <= 52 extended codes) and
#                   check_procurement.py --cost-only; the full procurement gate also needs U4 consigned (ORDERING)
# The Gerbers carry their creation date, so the package is not byte-reproducible; the manifest binds it instead.
set -euo pipefail
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
KICAD_PY=${KICAD_PY:-/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3}
KICAD_CLI=${KICAD_CLI:-/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli}
export KICAD_CLI
D=m3_design/assembly_review
B=$D/m3.kicad_pcb
quiet() { grep -v 'Debug: Adding duplicate\|create wxApp' || true; }
PYTHONUNBUFFERED=1 "$KICAD_PY" -I tools/jlc_orient.py tools/jlc_easyeda/pads.json "$B" 2>&1 | quiet | tail -1
python3 tools/export_fab.py "$B"
PYTHONUNBUFFERED=1 "$KICAD_PY" -I tools/jlc_orient.py tools/jlc_easyeda/pads.json "$B" \
  --verify-cpl "$D/fab/m3_cpl_jlc.csv" 2>&1 | quiet
PYTHONUNBUFFERED=1 "$KICAD_PY" -I tools/paste_check.py "$B" "$D/fab/m3_gerber.zip" 2>&1 | quiet
python3 tools/fab_manifest.py "$B"
for SIDE in top bottom; do
  "$KICAD_CLI" pcb render --side "$SIDE" -w 1016 -h 2208 --quality high -o "$D/r8_$SIDE.png" "$B" > /dev/null
done
echo "renders: $D/r8_top.png $D/r8_bottom.png"
if [[ -n "${FAB_NET:-}" ]]; then
  # jlc_stock fails while U4 (C26633007) is out of JLC stock: it is consigned (ORDERING section 1), so its result is
  # reported here and left to the full procurement gate (check_procurement.py without --cost-only)
  python3 tools/jlc_stock.py || echo "jlc_stock: short lines above (U4 is consigned: ORDERING section 1)"
  python3 tools/jlc_cost.py
  python3 tools/check_procurement.py --cost-only
fi
