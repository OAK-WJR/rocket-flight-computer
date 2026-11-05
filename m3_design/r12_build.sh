#!/usr/bin/env bash
# Build M3-ASSY-R12 (m3_design/r12/design/r12_plan.md, R12_DECISIONS.md) into m3_design/r12 from R11's hash-pinned
# netlist (m3_design/r12/design/r11_input/manifest.json). Every stage is deterministic: fixed UUID namespaces and KIID
# seeds, explicit tables, no search and no autorouting in the build (D-R12-26: the routing drafting aid
# m3_design/r12_aid/ is run by hand and its output frozen into m3_design/r12_routes.tsv).
#
# usage: m3_design/r12_build.sh            (from anywhere in the repo)
#        KICAD_PY=/path/to/kicad/python3 KICAD_CLI=/path/to/kicad-cli m3_design/r12_build.sh
#
# Stage A (parts and schematic): r12_parts.py --library-only, r12_sch.py --out, r12_parts.py --check, r12_sch_check.py
#   (strict ERC, every pin and part, the AGENTS section 2 net contracts, seeded faults, replay); r12_budget.py --check.
# Stage B (board and placement): r12_pcb.py (four layers, outline / supports / every part from r12_place.tsv, sensor rule
#   areas, title block, design/r12_gate_data.json; its legality checks stop the build), fit_check --profile r12,
#   check_r12 --stage placement.
# Stage C (copper): r12_route.py replays r12_routes.tsv (tracks, vias) and draws the planes of r12_planes.tsv, the B.Cu
#   GND pour and the S-8 keep-outs, fills the zones; then native DRC with schematic parity (no violation, no unconnected
#   item, no parity issue), route_check --profile r12 and check_r12 --stage copper (R12_ROUTE_HYGIENE=report, pass 1:
#   route_check hygiene and check_r12's K-reference / K-region / K-plane are reported, not fatal; strict: fatal).
# Stage D (post, fab) hooks run when their scripts exist.
set -euo pipefail
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
KICAD_PY=${KICAD_PY:-/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3}
KICAD_CLI=${KICAD_CLI:-/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli}
export KICAD_CLI
D=m3_design/r12
T=$(mktemp -d)
trap 'echo "build reports: $T"' EXIT

# --- stage A ---------------------------------------------------------------------------------------------------------
"$KICAD_PY" -I -B m3_design/r12_parts.py --library-only
"$KICAD_PY" -I -B m3_design/r12_sch.py --out "$D"
"$KICAD_PY" -I -B m3_design/r12_parts.py --check
PYTHONUNBUFFERED=1 "$KICAD_PY" -I -B m3_design/r12_sch_check.py --project "$D" --json "$T/sch_check.json" \
  > "$T/sch_check.txt" 2>&1 || { echo "r12_sch_check: FAIL (see $T/sch_check.json)"; exit 1; }
echo "r12_sch_check: OK"
python3 -I -B m3_design/r12_budget.py --check

# --- stage B ---------------------------------------------------------------------------------------------------------
PYTHONUNBUFFERED=1 "$KICAD_PY" -I -B m3_design/r12_pcb.py
"$KICAD_PY" -I -B tools/fit_check.py --profile r12 --report "$T/fit_placed.json" "$D/m3.kicad_pcb" \
  > "$T/fit_placed.txt" 2>&1 || { echo "fit_check r12 (placed): FAIL (see $T/fit_placed.txt)"; exit 1; }
echo "fit_check r12 (placed): OK"

# --- stage C (runs once the frozen copper table m3_design/r12_routes.tsv exists; stageC.md) --------------------------
if [[ ! -f m3_design/r12_routes.tsv ]]; then
  "$KICAD_CLI" pcb drc --schematic-parity --severity-all --format json -o "$T/drc_placed.json" "$D/m3.kicad_pcb" > /dev/null
  "$KICAD_PY" -I -B - "$T/drc_placed.json" <<'PY' || { echo "placed-board DRC: FAIL (see $T/drc_placed.json)"; exit 1; }
import json, sys
d = json.load(open(sys.argv[1]))
bad = [v['type'] + ': ' + v['description'] for v in d.get('violations', []) + d.get('schematic_parity', [])]
print('placed-board DRC:', 'OK,' if not bad else 'FAIL,', len(d.get('unconnected_items', [])), 'unconnected (stage C)')
print('\n'.join(bad))
sys.exit(1 if bad else 0)
PY
  "$KICAD_PY" -I -B tools/check_r12.py "$D/m3.kicad_pcb" --stage placement --fit "$T/fit_placed.json" \
    --report "$T/r12_placed.json" || { echo "check_r12 (placement): FAIL"; exit 1; }
  shasum -a 256 "$D/m3.kicad_pcb"
  exit 0
fi
PYTHONUNBUFFERED=1 "$KICAD_PY" -I -B m3_design/r12_route.py
"$KICAD_CLI" pcb drc --schematic-parity --severity-all --format json -o "$T/drc.json" "$D/m3.kicad_pcb" > /dev/null
"$KICAD_PY" -I -B - "$T/drc.json" <<'PY' || { echo "DRC: FAIL (see $T/drc.json)"; exit 1; }
import json, sys
d = json.load(open(sys.argv[1]))
bad = [v['type'] + ': ' + v['description'] for v in d.get('violations', []) + d.get('schematic_parity', [])]
bad += ['unconnected: ' + v['description'] for v in d.get('unconnected_items', [])]
print('DRC:', 'OK' if not bad else f'FAIL ({len(bad)})')
print('\n'.join(bad[:40]))
sys.exit(1 if bad else 0)
PY
"$KICAD_PY" -I -B tools/fit_check.py --profile r12 --report "$T/fit.json" "$D/m3.kicad_pcb" > "$T/fit.txt" 2>&1 \
  || { echo "fit_check r12: FAIL (see $T/fit.txt)"; exit 1; }
echo "fit_check r12: OK"
# Stage C pass 1 (D-R12-66A, owner: connect first, clean later): route_check's hygiene findings are reported, not
# fatal, until pass 2 sets R12_ROUTE_HYGIENE=strict (the default then). DRC, parity and unconnected stay fatal above.
if ! "$KICAD_PY" -I -B tools/route_check.py "$D/m3.kicad_pcb" --profile r12 --report "$T/route.json" > "$T/route.txt" 2>&1; then
  tail -1 "$T/route.txt"
  if [[ "${R12_ROUTE_HYGIENE:-report}" == strict ]]; then echo "route_check r12: FAIL (see $T/route.txt)"; exit 1; fi
  echo "route_check r12: hygiene findings reported, not fatal in stage C pass 1 (see $T/route.txt)"
else
  tail -1 "$T/route.txt"
fi
# D-R12-67A: in pass 1 check_r12's signal-reference rules (K-reference, K-region, K-plane) are reported, not fatal;
# R12_ROUTE_HYGIENE=strict (pass 2's default) makes them fatal. Every other copper rule (S-, M-, W-, LC-, V-, K-inner,
# K-copper, K-fill ...) is fatal in both tiers; check_r12 refuses to make an S- / M- / W- / LC- rule advisory.
ADVISORY=K-reference,K-region,K-plane
[[ "${R12_ROUTE_HYGIENE:-report}" == strict ]] && ADVISORY=
"$KICAD_PY" -I -B tools/check_r12.py "$D/m3.kicad_pcb" --stage copper --fit "$T/fit.json" --report "$T/r12.json" \
  --advisory "$ADVISORY" || { echo "check_r12 (copper): FAIL"; exit 1; }

# --- stage D hooks ---------------------------------------------------------------------------------------------------
if [[ -f m3_design/r12_post.py ]]; then
  PYTHONUNBUFFERED=1 "$KICAD_PY" -I -B m3_design/r12_post.py --report "$T/post.json"
fi
if [[ -f m3_design/r12_fab.sh ]]; then
  KICAD_PY="$KICAD_PY" m3_design/r12_fab.sh
fi
shasum -a 256 "$D/m3.kicad_pcb"
