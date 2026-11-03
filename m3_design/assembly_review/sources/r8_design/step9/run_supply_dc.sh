#!/usr/bin/env bash
# run_supply_dc.sh BOARD OUTDIR [GRID]: the supply-path DC solves of M3_R7's table on an R8 board (tools/dc_solve.py,
# path resistance only, no neck limit), one file per path in OUTDIR, then a summary. Default grid 0.1 mm (M3_R7's
# table grid for these rows); track-limited paths are good to about +-5 % there (M3_R7 "What the grid resolves").
set -uo pipefail
[[ $# -ge 2 ]] || { sed -n '2,4p' "$0"; exit 2; }
BOARD=$1; O=$2; G=${3:-0.1}; mkdir -p "$O"
ROOT="$(cd "$(dirname "$0")/../../../../.." && pwd)"
PY=${KICAD_PY:-/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3}
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
PATHS=(
  "raw_j124 RAW_ACT Q121:5,6,7,8,9 J124:2 7.7"
  "raw_r177 RAW_ACT Q121:5,6,7,8,9 R177:1 0.001"
  "bat_u9 BAT_IN J1:1 U9:5 1"
  "bat_c89 BAT_IN C89:1 U9:5 1"
  "bat_c95 BAT_IN C95:1 U9:5 1"
  "bat_d8 BAT_IN J1:1 D8:1 1"
  "v33_u1_75 3V3 L1:2 U1:75 0.1"
  "v33_fb31 3V3 L1:2 FB31:1 0.1"
  "v33_u1_100 3V3 L1:2 U1:100 0.1"
  "v33_u1_27 3V3 L1:2 U1:27 0.1"
  "v33_r164 3V3 L1:2 R164:1 0.1"
  "v33_c100 3V3 L1:2 C100:1 0.1"
  "v33_fb30 3V3 L1:2 FB30:1 0.1"
  "v33_u3 3V3 L1:2 U3:8 0.1"
  "v33_c9 3V3 L1:2 C9:1 0.1"
  "v33a_u4_5 3V3A U4:5 C31:1 0.01"
  "v33a_u4_8 3V3A U4:8 C31:1 0.01"
  "rp_u11 RAW_PROTECTED U9:6 U11:2 0.5"
  "rp_u7 RAW_PROTECTED U9:6 U7:3,4 1"
  "rp_tp81 RAW_PROTECTED U9:6 TP81:1 1"
  "vl_u2 VLOGIC C84:1 U2:2,3 0.5"
  "vl_c99 VLOGIC U11:1 C99:1 0.5"
  "usb USB_LIMITED U10:6 U11:7 0.5"
  "cam_r104 CAM_5V U13:1 R104:1 0.01"
  "cam_j9 CAM_5V L3:2 J9:1 1"
)
pids=()
for row in "${PATHS[@]}"; do
  set -- $row
  "$PY" -I "$ROOT/tools/dc_solve.py" "$BOARD" --grid "$G" --net "$2" --source "$3" --sink "$4" --amps "$5" > "$O/$1.txt" 2>&1 &
  pids+=($!)
  if (( ${#pids[@]} >= 6 )); then wait "${pids[0]}"; pids=("${pids[@]:1}"); fi
done
wait
rc=0
for row in "${PATHS[@]}"; do
  set -- $row
  r=$(grep -o "R = [0-9.]* mOhm" "$O/$1.txt" || true)
  [[ -n "$r" ]] || rc=1
  printf '%-12s %-14s %-18s -> %-14s %s\n' "$1" "$2" "$3" "$4" "${r:-FAILED}"
done
exit $rc
