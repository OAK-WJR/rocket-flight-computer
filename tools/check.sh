#!/usr/bin/env bash
# Board gate: DRC/parity, ERC, metadata/models, silkscreen, R8 CAD contract, clean routing, actuator contract and fit.
# R8 (M3-ASSY-R8): tools/check_r8.py and route_check profile r8. The R7 record is checked with tools/check_r7.py and
# route_check.py --profile r7 (both still pass on R7 board c872a3d3...).
# Usage: tools/check.sh [path/to/board.kicad_pcb]      exit 0 = every check clean
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BOARD="${1:-$ROOT/m3_design/assembly_review/m3.kicad_pcb}"
BOARD="$(cd "$(dirname "$BOARD")" && pwd)/$(basename "$BOARD")"   # absolute: the audit step runs in quality_audit/
CLI="${KICAD_CLI:-$(command -v kicad-cli || true)}"
if [[ -z "$CLI" ]]; then
  for candidate in /Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli /Applications/KiCad.app/Contents/MacOS/kicad-cli; do
    if [[ -x "$candidate" ]]; then CLI="$candidate"; break; fi
  done
fi
CLI="$(command -v "$CLI")" || { echo 'KiCad CLI unavailable; set KICAD_CLI' >&2; exit 1; }
CLI="$(python3 -c 'from pathlib import Path; import sys; print(Path(sys.argv[1]).resolve())' "$CLI")"
if [[ -z "${KICAD_PY:-}" ]]; then
  candidate="$(dirname "$CLI")/../Frameworks/Python.framework/Versions/Current/bin/python3"
  if [[ -x "$candidate" ]]; then KICAD_PY="$candidate"; else KICAD_PY=python3; fi
fi
KICAD_PY="$(command -v "$KICAD_PY")" || { echo 'KiCad Python unavailable; set KICAD_PY' >&2; exit 1; }
KICAD_PY="$(python3 -c 'from pathlib import Path; import sys; print(Path(sys.argv[1]).resolve())' "$KICAD_PY")"
export KICAD_PY
OUT="$(mktemp -d)"
trap 'echo "reports: $OUT"' EXIT
"$CLI" pcb drc --severity-all --schematic-parity --format json -o "$OUT/drc.json" "$BOARD" >/dev/null
"$CLI" sch erc --severity-all --format json -o "$OUT/erc.json" "${BOARD%.kicad_pcb}.kicad_sch" >/dev/null
python3 - "$OUT" <<'PY'
import json, sys, collections
o = sys.argv[1]
d = json.load(open(o + '/drc.json')); e = json.load(open(o + '/erc.json'))
v, u, p = d['violations'], d['unconnected_items'], d.get('schematic_parity', [])
erc = [x for s in e['sheets'] for x in s['violations']]
print(f"DRC violations {len(v)}  unconnected {len(u)}  schematic parity {len(p)}  ERC {len(erc)}")
for k, n in collections.Counter(x['type'] for x in v + erc).most_common(15): print(f"  {n:4d}  {k}")
sys.exit(1 if (v or u or p or erc) else 0)
PY
(cd "$ROOT/quality_audit" && python3 verify_board.py "$BOARD" --cli "$CLI" --output "$OUT/audit.json" >/dev/null) \
  && echo "metadata / 3D model audit: OK" || { echo "metadata / 3D model audit FAILED: see $OUT/audit.json"; exit 1; }
python3 "$ROOT/tools/silk_check.py" "$BOARD" --cli "$CLI"     # DRC skips silkscreen wholly outside the outline
"$KICAD_PY" -I "$ROOT/tools/check_r8.py" "$BOARD" --report "$OUT/r8.json"
"$KICAD_PY" -I "$ROOT/tools/route_check.py" "$BOARD" --profile r8 --report "$OUT/route.json" \
  | { grep -E '^(FAIL|routing hygiene: [0-9])' || true; }       # clean routing (AGENTS.md §3); full list in route.json
python3 "$ROOT/m3_design/check_actuators.py" "$BOARD"
"$KICAD_PY" -I "$ROOT/tools/fit_check.py" "$BOARD" --report "$OUT/fit.json"
