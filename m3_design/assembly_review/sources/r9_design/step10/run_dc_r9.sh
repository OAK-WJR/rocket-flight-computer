#!/usr/bin/env bash
# run_dc_r9.sh BOARD OUTDIR: R9 step 10's DC solves beyond tools/run_dc.sh (tools/dc_solve.py, path resistance; each
# output's first line is the board's SHA-256):
#   supply   R8 step 9's 25 supply paths (step9/run_supply_dc.sh; R9 keeps R8's designators) + RAW_PROTECTED -> R122,
#            at 0.1 mm (M3_R7's table grid; track-limited paths good to about +-5 %)
#   fire     F7's fire loop on the final copper at 0.05 mm: RAW_ACT Q121 -> J124.2 (RAW), PYRO1_BUS J124.1 -> R134.2,
#            PYRO1_IGN R134.1 -> J121.2, PYRO1_OUT J121.1 -> Q124 drain, and the GND return Q124's source pins -> J1.2
#            (window x 0-46, y 50-102, the region the return crosses; copper outside it left out: an upper bound;
#            solved with the gnd rows)
#   gnd      the fire loop's GND return (above) and the servo GND return, J122's four GND pins -> J1.2, 7.7 A, same
#            window, both at 0.1 mm (GND has 0.2 mm tracks)
# Usage: run_dc_r9.sh BOARD OUTDIR [supply|fire|gnd ...]   (default: all)
set -uo pipefail
[[ $# -ge 2 ]] || { sed -n '2,12p' "$0"; exit 2; }
BOARD=$1; O=$2; shift 2; mkdir -p "$O"
WHAT=${*:-supply fire gnd}
ROOT="$(cd "$(dirname "$0")/../../../../.." && pwd)"
PY=${KICAD_PY:-/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3}
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WIN=0,50,46,102
SUPPLY=(
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
  "rp_r122 RAW_PROTECTED U9:6 R122:1 0.001"
  "vl_u2 VLOGIC C84:1 U2:2,3 0.5"
  "vl_c99 VLOGIC U11:1 C99:1 0.5"
  "usb USB_LIMITED U10:6 U11:7 0.5"
  "cam_r104 CAM_5V U13:1 R104:1 0.01"
  "cam_j9 CAM_5V L3:2 J9:1 1"
)
FIRE=(
  "fire_raw RAW_ACT Q121:5,6,7,8,9 J124:2 2.8 0.05"
  "fire_bus PYRO1_BUS J124:1 R134:2 2.8 0.05"
  "fire_ign PYRO1_IGN R134:1 J121:2 2.8 0.05"
  "fire_out PYRO1_OUT J121:1 Q124:5 2.8 0.05"
)
GND=("fire_gnd GND Q124:1,2,3 J1:2 2.8 0.1 $WIN" "gnd_servo GND J122:3,6,9,12 J1:2 7.7 0.1 $WIN")
rows=()
for w in $WHAT; do
  case $w in
    supply) for r in "${SUPPLY[@]}"; do rows+=("$r 0.1"); done ;;
    fire) rows+=("${FIRE[@]}") ;;
    gnd) rows+=("${GND[@]}") ;;
  esac
done
JOBS=${DC_JOBS:-8}                 # parallel solves; a slot is refilled as soon as any solve ends (bash 3.2: no wait -n)
for row in "${rows[@]}"; do
  set -- $row
  extra=(); [[ -n "${7:-}" ]] && extra=(--window "$7")
  while (( $(jobs -rp | wc -l) >= JOBS )); do sleep 2; done
  "$PY" -I "$ROOT/tools/dc_solve.py" "$BOARD" --grid "$6" --net "$2" --source "$3" --sink "$4" --amps "$5" \
    --via-currents 3 ${extra[@]+"${extra[@]}"} > "$O/$1.txt" 2>&1 &
done
wait
rc=0
for row in "${rows[@]}"; do
  set -- $row
  r=$(grep -o "R = [0-9.]* mOhm" "$O/$1.txt" || true)
  [[ -n "$r" ]] || rc=1
  printf '%-11s %-14s %-18s -> %-12s %-5s A grid %-5s %s\n' "$1" "$2" "$3" "$4" "$5" "$6" "${r:-FAILED}"
done
exit $rc
