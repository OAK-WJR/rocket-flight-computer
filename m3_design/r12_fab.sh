#!/usr/bin/env bash
# The M3-ASSY-R12 fab package and its checks (r12_plan.md section 4, stage D) on m3_design/r12/m3.kicad_pcb, placed
# (m3_design/r12_build.sh stops after stage B until the copper table exists) or routed (r12_build.sh runs this last):
# R11's m3_design/r11_fab.sh with R12's board, layers, (no) owner-fitted parts, corrections and binding. R10's tools and their
# inputs stay unchanged; R12 runs them through its wrappers.
#
# usage: m3_design/r12_fab.sh               (from anywhere in the repo)
#        FAB_NET=1 m3_design/r12_fab.sh     also stocks and prices the BOM at JLC, Economic PCBA, for 2 and 5 boards
#                                           (live public supplier data, read-only, valid 24 h; writes fab/stock_check_<n>.json
#                                           and fab/cost_check_<n>.json)
#
#   jlc_orient_r12.py   placement corrections (tools/jlc_corrections_r12.json) by matching every LCSC footprint's pads to
#                       ours (tools/jlc_easyeda/pads_r12.json); fails on any part it cannot match ("CHECK: none"). A code
#                       missing from the pad file: run `<KiCad python3> -I tools/jlc_orient_r12.py --fetch` (network).
#   export_fab_r12.py   into m3_design/r12/fab, unbound (--pending): the Gerber zip (F / In1 / In2 / B copper, both masks,
#                       F paste, both silks, Edge.Cuts, PTH / NPTH drill, job file), the JLC BOM (one line per LCSC code),
#                       the owner BOM (owner-fitted parts: none since D-R12-85, so not written), the CPL and the
#                       top / bottom assembly drawings
#   fab_manifest_r12.py --bind   the content checks on the exported package, then the manifest binding it to the CAD
#                       and export inputs (the board's SHA-256), written only when every check passes:
#     --verify-cpl      BOM and CPL designator sets equal and exactly r12_parts' JLC parts, owner BOM exactly the
#                       owner-fitted parts (none), every CPL row Top, every row rebuilt from JLC's footprint onto our pads
#     --paste           the Gerber zip's file set; paste_check's rules on F paste; one flash per pasted pad, paste only
#                       on parts in the CPL
#   fab_manifest_r12.py the outputs still match the CAD and export inputs; tools/check.sh repeats --content
#   FAB_NET=1           jlc_stock.py and jlc_cost.py --tier economic --profile r10 (REQUIREMENTS M3's $84.41 per board)
#                       for 2 and 5 boards
# The Gerbers carry their creation date, so the package is not byte-reproducible; the manifest binds it instead.
# The generated package (m3_design/r12/fab/) is tracked in git, as R11's is, so tools/check.sh can verify it (stage D).
set -euo pipefail
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
KICAD_PY=${KICAD_PY:-/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3}
KICAD_CLI=${KICAD_CLI:-/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli}
export KICAD_CLI KICAD_PY
D=m3_design/r12
B=$D/m3.kicad_pcb
[[ -f "$B" ]] || { echo "r12_fab: $B missing (build it with m3_design/r12_build.sh)"; exit 1; }
grep -q '"M3-ASSY-R12"' "$B" || { echo "r12_fab: $B is not an M3-ASSY-R12 board"; exit 1; }
quiet() { grep -v 'Debug: Adding duplicate\|create wxApp\|Fontconfig\|stdpbase' || true; }
RECORD_DIR="$(mktemp -d)"
trap 'rm -rf "$RECORD_DIR"' EXIT
PYTHONUNBUFFERED=1 "$KICAD_PY" -I tools/jlc_orient_r12.py tools/jlc_easyeda/pads_r12.json "$B" > "$RECORD_DIR/orient.txt" 2>&1 \
  || { quiet < "$RECORD_DIR/orient.txt" | grep -v ' OK '; echo "r12_fab: placement corrections incomplete"; exit 1; }
quiet < "$RECORD_DIR/orient.txt" | tail -1
"$KICAD_PY" -I tools/export_fab_r12.py "$B" --out "$D/fab" --pending "$RECORD_DIR/export.json" 2>&1 | quiet
[[ -f "$RECORD_DIR/export.json" ]] || { echo "r12_fab: export failed"; exit 1; }
python3 tools/fab_manifest_r12.py "$B" --bind "$RECORD_DIR/export.json"
python3 tools/fab_manifest_r12.py "$B"
if [[ -n "${FAB_NET:-}" ]]; then
  STATUS=0
  for N in 2 5; do
    # plain python3, not -I: jlc_cost imports jlc_stock from tools/
    python3 tools/jlc_stock.py --fab "$D/fab" --boards "$N" || { STATUS=1; echo "jlc_stock ($N boards): short lines above"; }
    [[ -f "$D/fab/stock_check.json" ]] && mv "$D/fab/stock_check.json" "$D/fab/stock_check_$N.json"
    python3 tools/jlc_cost.py --tier economic --profile r10 --fab "$D/fab" --boards "$N" \
      || { STATUS=1; echo "jlc_cost ($N boards): \$84.41 target missed or pricing unknown (above)"; }
    [[ -f "$D/fab/cost_check.json" ]] && mv "$D/fab/cost_check.json" "$D/fab/cost_check_$N.json"
  done
  exit $STATUS
fi
