#!/usr/bin/env bash
# run_dc.sh BOARD OUTDIR [GRID]: DC solve and IPC-2152 equipotential-cut neck of the three 7.7 A servo-feed paths
# (REQUIREMENTS F4) with dc_solve.py --necks, each against its R8_DECISIONS D12 rise limit (RAW_ACT and BAT_IN 20 C,
# ACT_FET_S 30 C), with the five largest via barrel currents of each (MARGIN_PRESCRIPTION P1-9). Default grid 0.05 mm
# (the qualification grid); 0.1 mm is the quick iteration grid (within 3 %), which m3_design/r8_build.sh runs on the
# finished copper so no table or generator change can narrow a neck past its limit unnoticed (fix pass 1,
# R8P1-INTEGRITY-02). Each output file's first line is the board's SHA-256 (dc_solve.py).
# The terminals are the R7 designators (Q120/Q121 AON6403 actuator switch, J1 battery terminal, J122 servo header),
# which R8 keeps. Writes OUTDIR/dc_{raw,bat,fet}.txt; exit 1 if a solve fails or a neck exceeds its limit.
# DC_GND=GRID (opt-in; fix pass 1, R8P1-POWER-01) also solves the servo GND return, J122's four GND pins to J1.2, over
# the window x 0-46, y 64-118 (the region the return crosses; the copper outside it left out, an upper bound on R) at
# that grid (>= 0.1 mm: GND has 0.2 mm tracks), into OUTDIR/dc_gnd.txt. Its neck is reported, not gated: the narrowest
# cut is J1.2's thermal spokes, 0.25-0.5 mm long, which the long-conductor IPC-2152 fit does not describe (judged by
# conduction and M2's THT-GND relief rule, docs/M3_R8.md "DC solve"). J122's four + pins (supply) and four GND pins
# (return) are each held at one potential, so the copper between pins of one group carries no current in the model.
# Runtime (pure-Python CG, no numpy): 0.05 mm ~40 min (BAT_IN; RAW_ACT ~15, ACT_FET_S ~1); 0.1 mm a few minutes for
# all three; DC_GND=0.1 about an hour.
set -uo pipefail
[[ $# -ge 2 ]] || { sed -n '2,3p' "$0"; exit 2; }
BOARD=$1; O=$2; G=${3:-0.05}; mkdir -p "$O"
HERE="$(cd "$(dirname "$0")" && pwd)"
PY=${KICAD_PY:-/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3}
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
run() { name=$1; shift; "$PY" -I "$HERE/dc_solve.py" "$BOARD" --grid "$G" --necks --via-currents 5 "$@" > "$O/$name.txt" 2>&1; }
run dc_raw --net RAW_ACT --source Q121:5,6,7,8,9 --sink J122:2,5,8,11 --max-rise 20 & p1=$!
run dc_bat --net BAT_IN --source J1:1 --sink Q120:5,6,7,8,9 --max-rise 20 & p2=$!
run dc_fet --net ACT_FET_S --source Q120:1,2,3 --sink Q121:1,2,3 --max-rise 30 & p3=$!
pids="$p1 $p2 $p3"
if [[ -n "${DC_GND:-}" ]]; then
  "$PY" -I "$HERE/dc_solve.py" "$BOARD" --grid "$DC_GND" --necks --via-currents 5 --net GND \
    --source J122:3,6,9,12 --sink J1:2 --window 0,64,46,118 > "$O/dc_gnd.txt" 2>&1 & pids="$pids $!"
fi
rc=0; for p in $pids; do wait "$p" || rc=1; done
grep -H "sha256\|R = \|neck\|vias\|FAIL" "$O"/dc_*.txt
exit $rc
