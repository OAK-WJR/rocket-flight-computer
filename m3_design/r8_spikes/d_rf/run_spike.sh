#!/usr/bin/env bash
# Spike (d), RF buses: rebuild the scratch boards and run every check. Read-only on the repository.
# usage: m3_design/r8_spikes/d_rf/run_spike.sh OUTDIR        (OUTDIR is created; about 2 minutes)
set -euo pipefail
OUT=${1:?usage: run_spike.sh OUTDIR}
HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$HERE/../../.." && pwd)
KPY=${KICAD_PY:-/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3}
run() { PYTHONUNBUFFERED=1 "$KPY" -I "$@" 2>&1 | grep -v 'wxApp\|Debug:\|memory leak' || true; }

mkdir -p "$OUT/r7" "$OUT/base" "$OUT/rf"
for f in m3.kicad_pcb m3.kicad_pro m3.kicad_dru; do               # R7 as pushed (431025d), project rules included
  git -C "$ROOT" show "431025d:m3_design/assembly_review/$f" > "$OUT/r7/$f"
done
echo "R7 board sha256 $(shasum -a 256 "$OUT/r7/m3.kicad_pcb" | cut -c1-16)  (expect c872a3d30509cccf)"

run "$HERE/spike_base.py" "$OUT/r7/m3.kicad_pcb" "$ROOT/m3_design/assembly_review/schematic.net.xml" \
    "$HERE/seed_b0_place_final.tsv" "$OUT/base/m3.kicad_pcb" --place "$HERE/d_rf_place.tsv"
run "$HERE/rf_route_r8.py" "$OUT/base/m3.kicad_pcb" "$OUT/rf/m3.kicad_pcb" --report "$OUT/rf/route.json"
shasum -a 256 "$OUT/base/m3.kicad_pcb" "$OUT/rf/m3.kicad_pcb"

echo "== spike checks (rigid hashes, strip, fence, F10, DRC and route_check on the spike's nets)"
run "$HERE/spike_verify.py" "$OUT/rf/m3.kicad_pcb" --json "$OUT/rf/verify.json"
echo "== strip_gcpw sample comparison with R7"
run "$HERE/gcpw_compare.py" "$OUT/r7/m3.kicad_pcb" "$OUT/rf/m3.kicad_pcb" | tail -1
echo "== tab windows"
run "$HERE/tab_scan.py" "$OUT/rf/m3.kicad_pcb"
echo "== route figures of the spike's nets"
run "$ROOT/tools/route_check.py" "$OUT/rf/m3.kicad_pcb" --routes \
  | grep -E '^route (RADIO|GNSS|3V3_GNSS|3V3_RADIO|LED)' || true
echo "== full check_r8 (other families' findings expected on a spike board)"
run "$ROOT/tools/check_r8.py" "$OUT/rf/m3.kicad_pcb" --report "$OUT/rf/check_r8.json" | tail -1
