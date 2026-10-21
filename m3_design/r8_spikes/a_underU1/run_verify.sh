#!/bin/bash
# Spike (a): build (optional) + DRC + route_check + spike_verify on a scratch board directory.
# usage: run_verify.sh OUTDIR [--build R7_BOARD [--fallback]] [--no-rc]
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
REPO=$(cd "$HERE/../../.." && pwd)
KPY=${KPY:-/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3}
CLI=${KICAD_CLI:-/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli}
OUT=$1; shift
FB=""; RC=1; BUILD=""
while [ $# -gt 0 ]; do
  case $1 in
    --build) BUILD=$2; shift;;
    --fallback) FB=--fallback;;
    --no-rc) RC=0;;
  esac; shift
done
filt() { grep -v "wxApp\|memory leak\|Debug: \|traits\|swig/python detected"; }
if [ -n "$BUILD" ]; then
  PYTHONUNBUFFERED=1 "$KPY" -I "$HERE/spike_build.py" "$BUILD" "$OUT" $FB 2>&1 | filt || exit 1
fi
B="$OUT/m3s.kicad_pcb"
"$CLI" pcb drc --format json --severity-all --all-track-errors --output "$OUT/drc.json" "$B" >/dev/null 2>&1
ARGS=(--drc "$OUT/drc.json")
if [ $RC = 1 ]; then
  PYTHONUNBUFFERED=1 "$KPY" -I "$REPO/tools/route_check.py" "$B" --report "$OUT/rc.json" > "$OUT/rc.txt" 2>&1
  ARGS+=(--rc "$OUT/rc.json")
fi
PYTHONUNBUFFERED=1 "$KPY" -I "$HERE/spike_verify.py" "$B" "${ARGS[@]}" --pads "$OUT/pads.json" $FB 2>&1 | filt
