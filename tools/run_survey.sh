#!/usr/bin/env bash
# run_survey.sh BOARD.kicad_pcb OUTDIR [BASE_BOARD.kicad_pcb]
# The R8 scorecard (r8_plan.md section 2) of one filled board, read-only on BOARD: geometry metrics
# (survey_metrics.py), route_check counts, critical-reference sampling, the three 7.7 A DC solves with their
# IPC-2152 necks (run_dc.sh), the board gate (check.sh) and the scorecard against the R7 baseline (scorecard.py).
# Metric definitions: m3_design/assembly_review/sources/r8_design/survey_baseline.md. A soft report, never a gate.
#
# Environment (defaults in brackets):
#   ROUTE_PROFILE route_check profile for the C rows  [r8; r7 reproduces the R7 record's counts on an R7 board]
#   KICAD_PY      KiCad's python3                     [/Applications/KiCad/... on macOS]
#   KICAD_CLI     kicad-cli                           [/Applications/KiCad/... on macOS]
#   NO_GATE=1 skip check.sh;  NO_DC=1 skip the DC solves;  DC_GRID [0.05] (0.05 mm: ~40 min, set by BAT_IN; 0.1: ~5 min)
#   BASELINE      a survey OUTDIR or scorecard JSON to compare against [tools/scorecard_r7.json, or
#                 tools/scorecard_r7_quick.json when DC_GRID=0.1, so DC rows are compared on like grids]
# BASE_BOARD (optional): also run critical_reference.py BASE BOARD (losses relative to the base, R6 method).
# Outputs in OUTDIR: survey.json survey.txt route.json route.txt cref_self*.json cref_vs_base*.json dc_*.txt gate.txt
#                    scorecard.md scorecard.json
set -uo pipefail
[[ $# -ge 2 ]] || { sed -n '2,4p' "$0"; exit 2; }
BOARD="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"; OUT=$2; BASEB=${3:-}
mkdir -p "$OUT"; OUT="$(cd "$OUT" && pwd)"
HERE="$(cd "$(dirname "$0")" && pwd)"
export KICAD_PY=${KICAD_PY:-/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3}
export KICAD_CLI=${KICAD_CLI:-/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli}
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
PROFILE=${ROUTE_PROFILE:-r8}
quiet() { grep -v 'Debug: Adding duplicate\|create wxApp\|memory leak' || true; }
echo "== survey_metrics";  "$KICAD_PY" -I "$HERE/survey_metrics.py" "$BOARD" --tools "$HERE" --json "$OUT/survey.json" 2>&1 | quiet > "$OUT/survey.txt"
echo "== route_check ($PROFILE)"
"$KICAD_PY" -I "$HERE/route_check.py" "$BOARD" --profile "$PROFILE" --report "$OUT/route.json" --routes 2>&1 | quiet > "$OUT/route.txt"
echo "== critical_reference"
"$KICAD_PY" -I "$HERE/critical_reference.py" "$BOARD" "$BOARD" --json "$OUT/cref_self.json" 2>&1 | quiet > "$OUT/cref_self.txt" &
"$KICAD_PY" -I "$HERE/critical_reference.py" "$BOARD" "$BOARD" --extended --json "$OUT/cref_self_ext.json" 2>&1 | quiet > "$OUT/cref_self_ext.txt" &
if [[ -n "$BASEB" ]]; then
  "$KICAD_PY" -I "$HERE/critical_reference.py" "$BASEB" "$BOARD" --json "$OUT/cref_vs_base.json" 2>&1 | quiet > "$OUT/cref_vs_base.txt" &
  "$KICAD_PY" -I "$HERE/critical_reference.py" "$BASEB" "$BOARD" --extended --json "$OUT/cref_vs_base_ext.json" 2>&1 | quiet > "$OUT/cref_vs_base_ext.txt" &
fi
wait
if [[ -z "${NO_DC:-}" ]]; then echo "== DC solves"; "$HERE/run_dc.sh" "$BOARD" "$OUT" "${DC_GRID:-0.05}" | quiet; fi
if [[ -z "${NO_GATE:-}" ]]; then
  echo "== gate"; mkdir -p "$OUT/tmp"
  (TMPDIR="$OUT/tmp" bash "$HERE/check.sh" "$BOARD"; echo "exit $?") > "$OUT/gate.txt" 2>&1
fi
if [[ "${DC_GRID:-0.05}" == "0.1" ]]; then BASELINE=${BASELINE:-$HERE/scorecard_r7_quick.json}; else BASELINE=${BASELINE:-$HERE/scorecard_r7.json}; fi
if [[ -e "$BASELINE" && "$BASELINE" != "$OUT" ]]; then
  python3 "$HERE/scorecard.py" "$OUT" --baseline "$BASELINE" --md "$OUT/scorecard.md" --json "$OUT/scorecard.json"
else
  python3 "$HERE/scorecard.py" "$OUT" --md "$OUT/scorecard.md" --json "$OUT/scorecard.json"
fi
