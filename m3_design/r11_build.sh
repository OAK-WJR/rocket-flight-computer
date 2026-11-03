#!/usr/bin/env bash
# Build M3-ASSY-R11 (m3_design/r11/design/r11_plan.md, R11_DECISIONS.md) into m3_design/r11 from R10's hash-pinned
# inputs (m3_design/r11/design/r10_input/manifest.json, R10 commit deb179e). Each stage is deterministic: fixed UUID
# namespaces, explicit tables, no search, no autorouting (D-R11-07).
#
# usage: m3_design/r11_build.sh            (from anywhere in the repo)
#        KICAD_PY=/path/to/kicad/python3 KICAD_CLI=/path/to/kicad-cli m3_design/r11_build.sh
#
# Stage A (parts and schematic):
#   r11_parts.py --library-only   kilib/: R10's symbols with MCU_TFBGA100 / CameraGH6 / GH texts, R10's footprints and
#                                 models that R11 uses, the TFBGA-100, JST GH and AWG 20 wire-pad lands, envelopes
#   r11_sch.py --out              the 15 sheets, schematic.net.xml (kicad-cli export), m3.kicad_dru, m3.kicad_pro and
#                                 the lib tables, from r10_input/ + circuit.json + pin_table.tsv (BALL)
#   gate                          r11_parts.py --check, then r11_sch_check.py (strict ERC, every pin and part, R10's
#                                 contracts re-keyed to balls, regeneration, seeded faults)
# Later stages add their steps at the hooks below (r11_plan.md section 4); each hook is a no-op until its script exists.
# The JLC stock record (r11_parts.py --stock) needs the network and is run by hand, not here.
set -euo pipefail
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
KICAD_PY=${KICAD_PY:-/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3}
KICAD_CLI=${KICAD_CLI:-/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli}
export KICAD_CLI
D=m3_design/r11
T=$(mktemp -d)
trap 'echo "build reports: $T"' EXIT

# --- stage A: parts and schematic ------------------------------------------------------------------------------------
"$KICAD_PY" -I -B m3_design/r11_parts.py --library-only
"$KICAD_PY" -I -B m3_design/r11_sch.py --out "$D"
"$KICAD_PY" -I -B m3_design/r11_parts.py --check
PYTHONUNBUFFERED=1 "$KICAD_PY" -I -B m3_design/r11_sch_check.py --project "$D" --json "$T/sch_check.json" \
  > "$T/sch_check.txt" 2>&1 || { echo "r11_sch_check: FAIL (see $T/sch_check.json)"; exit 1; }
echo "r11_sch_check: OK"

# --- stage B hook: board, stackup and placement (r11_pcb.py, r11_place.tsv) -----------------------------------------
#   r11_pcb.py      six-layer board (JLC06161H-3313), outline / supports and every part from r11_place.tsv, the sensor
#                   rule areas, title block, r11/design/r11_gate_data.json (imu, short_edge_queries); its own
#                   legality checks (courtyards, edges, supports, bottom keep-outs) stop the build
#   gate            fit_check --profile r11, then native DRC with schematic parity: no violation and no parity issue;
#                   only unconnected items are allowed until stage C draws the copper
if [[ -f m3_design/r11_pcb.py ]]; then
  PYTHONUNBUFFERED=1 "$KICAD_PY" -I -B m3_design/r11_pcb.py
  "$KICAD_PY" -I -B tools/fit_check.py --profile r11 --report "$T/fit.json" "$D/m3.kicad_pcb" > "$T/fit.txt" 2>&1 \
    || { echo "fit_check r11: FAIL (see $T/fit.txt)"; exit 1; }
  echo "fit_check r11: OK"
  if [[ ! -f m3_design/r11_route.py ]]; then
    "$KICAD_CLI" pcb drc --schematic-parity --severity-all --format json -o "$T/drc_placed.json" "$D/m3.kicad_pcb" \
      > /dev/null
    "$KICAD_PY" -I -B - "$T/drc_placed.json" <<'PY' || { echo "placed-board DRC: FAIL (see $T/drc_placed.json)"; exit 1; }
import json, sys
d = json.load(open(sys.argv[1]))
bad = [v['type'] + ': ' + v['description'] for v in d.get('violations', []) + d.get('schematic_parity', [])]
print('placed-board DRC:', 'OK,' if not bad else 'FAIL,', len(d.get('unconnected_items', [])), 'unconnected (stage C)')
print('\n'.join(bad))
sys.exit(1 if bad else 0)
PY
  fi
fi

# --- stage C hook: copper by families, gated after each (r11_route.py, r11_stage_check.py) --------------------------
#   r11_route.py F         one family per run in the order core usb pyro power ports servo sd signals status ground; a family
#                          whose m3_design/r11_route_<family>.py does not exist yet is skipped (stageC1.md section 1)
#   r11_stage_check.py F   DRC (dangling ends allowed only on pending nets), unconnected items never rising and none
#                          on a finished net, route_check --profile r11 failing only on pending nets; after ground none
#   r11_escape_check.py    after the families: every used U1 ball has one exit in r11_fanout.tsv, no two exits share a
#                          channel slot, each exit faces its target, and the table matches the copper (D-R11-44)
if [[ -f m3_design/r11_route.py ]]; then
  for FAMILY in ${R11_FAMILIES:-core usb pyro power ports servo sd signals status ground}; do
    PYTHONUNBUFFERED=1 "$KICAD_PY" -I -B m3_design/r11_route.py "$FAMILY"
    if [[ -f m3_design/r11_stage_check.py ]]; then
      PYTHONUNBUFFERED=1 "$KICAD_PY" -I -B m3_design/r11_stage_check.py "$FAMILY" --state "$T/stage.json"
    fi
  done
  # D-R11-44: the pinned U1 escape table (r11_fanout.tsv) proved on its own and against the routed copper
  "$KICAD_PY" -I -B m3_design/r11_escape_check.py --board "$D/m3.kicad_pcb" --json "$T/escape.json" \
    || { echo "r11_escape_check: FAIL (see $T/escape.json)"; exit 1; }
fi

# --- stage D hook: post, fab package and the full gate (r11_post.py, r11_fab.sh, tools/check.sh) -------------------
if [[ -f m3_design/r11_post.py ]]; then
  PYTHONUNBUFFERED=1 "$KICAD_PY" -I -B m3_design/r11_post.py --report "$T/post.json"
fi
if [[ -f m3_design/r11_fab.sh ]]; then
  KICAD_PY="$KICAD_PY" m3_design/r11_fab.sh
fi
if [[ -f "$D/m3.kicad_pcb" ]]; then
  shasum -a 256 "$D/m3.kicad_pcb"
fi
