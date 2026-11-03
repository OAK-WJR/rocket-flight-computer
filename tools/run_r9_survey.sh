#!/usr/bin/env bash
# tools/run_r9_survey.sh BOARD.kicad_pcb OUTDIR
# The R9 scorecard of one filled board, read-only on BOARD (r9_plan.md section 2): the repo survey (tools/run_survey.sh:
# survey_metrics, route_check, critical_reference, the three 7.7 A DC solves, the gate), then the R9 additions
# (r9_extra_metrics.py, reference_audit both sets, step9 requalify / pyro_neighbours / m2_sweep, fit_check, the plate
# model, check_r9) and r9_scorecard.py against R8. Row definitions: sources/r9_design/survey_baseline.md section 3.
#
# Environment (defaults in brackets):
#   GATE_SH     the gate run by the survey [tools/check.sh, the R9 contracts]
#   ROUTE_PROFILE route_check profile for the survey rows [r9]
#   R8_BASE     R8 baseline (survey OUTDIR or scorecard JSON) [tools/scorecard_r8_r9.json; _quick when DC_GRID=0.1]
#   NUMPY_PY    a python3 with numpy for the plate model [python3]
#   NO_DC=1 / NO_GATE=1 / DC_GRID=0.1 as run_survey.sh;  NO_M2=1 skips the M2 sweep (~1 min)
set -uo pipefail
[[ $# -ge 2 ]] || { sed -n '2,3p' "$0"; exit 2; }
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/.." && pwd)"
BOARD="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"; mkdir -p "$2"; OUT="$(cd "$2" && pwd)"
CLI="${KICAD_CLI:-$(command -v kicad-cli || echo /Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli)}"
CLI="$(python3 -c 'from pathlib import Path; import sys; print(Path(sys.argv[1]).resolve())' "$CLI")"   # as check.sh
export KICAD_CLI="$CLI"
export KICAD_PY="${KICAD_PY:-$(dirname "$CLI")/../Frameworks/Python.framework/Versions/Current/bin/python3}"
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 ROUTE_PROFILE="${ROUTE_PROFILE:-r9}"
if [[ "${DC_GRID:-0.05}" == "0.1" ]]; then R8_BASE=${R8_BASE:-$HERE/scorecard_r8_r9_quick.json}; else R8_BASE=${R8_BASE:-$HERE/scorecard_r8_r9.json}; fi
S9="$REPO/m3_design/assembly_review/sources/r8_design/step9"
pyc0=$(ls -d "$REPO"/tools/__pycache__ "$REPO"/m3_design/__pycache__ 2>/dev/null)
cleanup() { for d in "$REPO"/tools/__pycache__ "$REPO"/m3_design/__pycache__; do
  [[ -d "$d" && "$pyc0" != *"$d"* ]] && rm -rf "$d"; done; }
trap cleanup EXIT
quiet() { grep -v 'Debug: Adding duplicate\|create wxApp\|memory leak\|stdpbase' || true; }
GATE_SH=${GATE_SH:-$REPO/tools/check.sh}
NO_GATE=1 bash "$REPO/tools/run_survey.sh" "$BOARD" "$OUT"
if [[ -z "${NO_GATE:-}" ]]; then
  mkdir -p "$OUT/tmp"; (TMPDIR="$OUT/tmp" bash "$GATE_SH" "$BOARD"; echo "exit $?") > "$OUT/gate.txt" 2>&1
fi
echo "== R9 additions"
"$KICAD_PY" -I -B "$HERE/r9_extra_metrics.py" "$BOARD" --tools "$HERE" --json "$OUT/x_metrics.json" 2>&1 | quiet > "$OUT/x_metrics.txt" &
"$KICAD_PY" -I -B "$HERE/reference_audit.py" "$BOARD" --json "$OUT/refaudit.json" 2>&1 | quiet > "$OUT/refaudit.txt" &
"$KICAD_PY" -I -B "$HERE/reference_audit.py" "$BOARD" --extended --json "$OUT/refaudit_ext.json" 2>&1 | quiet > "$OUT/refaudit_ext.txt" &
"$KICAD_PY" -I -B "$S9/requalify.py" "$BOARD" "$OUT/requalify.json" 2>&1 | quiet > "$OUT/requalify.txt" &
"$KICAD_PY" -I -B "$S9/pyro_neighbours.py" "$BOARD" "$OUT/pyro_neighbours.json" 2>&1 | quiet > "$OUT/pyro_neighbours.txt" &
[[ -z "${NO_M2:-}" ]] && { "$KICAD_PY" -I -B "$S9/m2_sweep.py" "$BOARD" --json "$OUT/m2_sweep.json" 2>&1 | quiet > "$OUT/m2_sweep.txt" & }
"$KICAD_PY" -I -B "$HERE/fit_check.py" "$BOARD" --report "$OUT/fit.json" 2>&1 | quiet > "$OUT/fit.txt"
"${NUMPY_PY:-python3}" -I -B "$HERE/plate_model.py" "$OUT/fit.json" --json "$OUT/plate.json" > "$OUT/plate.txt" 2>&1
"$KICAD_PY" -I -B "$HERE/check_r9.py" "$BOARD" --fit "$OUT/fit.json" --plate "$OUT/plate.json" \
  --report "$OUT/r9_check.json" 2>&1 | quiet > "$OUT/r9_check.txt"
wait
rm -rf "$OUT/tmp"
python3 -I -B "$HERE/r9_scorecard.py" "$OUT" --baseline "$R8_BASE" --tools "$HERE" --md "$OUT/r9_scorecard.md" \
  --json "$OUT/r9_scorecard.json" > /dev/null && echo "R9 scorecard: $OUT/r9_scorecard.md"
