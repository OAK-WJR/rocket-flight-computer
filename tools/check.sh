#!/usr/bin/env bash
# Board gate: DRC (all severities + schematic parity), ERC, metadata/model audit.
# Usage: tools/check.sh [path/to/board.kicad_pcb]      exit 0 = every check clean
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BOARD="${1:-$ROOT/m3_design/assembly_review/m3.kicad_pcb}"
CLI="${KICAD_CLI:-$(command -v kicad-cli || echo /Applications/KiCad.app/Contents/MacOS/kicad-cli)}"
OUT="$(mktemp -d)"
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
echo "reports: $OUT"
