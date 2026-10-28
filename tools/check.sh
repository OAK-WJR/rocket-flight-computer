#!/usr/bin/env bash
# Board gate: DRC/parity, ERC, metadata/models, silkscreen, fit, vibration, the R10 CAD contract, clean routing, the
# actuator contract and the gates' own seeded tests (including routing, R10 and procurement).
# R10 (M3-ASSY-R10, r10_plan.md section 4): tools/check_r10.py (rule-based; it reads the fit report and the plate model
# made here, both --profile r10), route_check profile r10 (empty allowlist, no RF parts), check_actuators --profile r10.
# R10 has no pyro-specific spacing rule (r10_plan section 2 item 1), so the rule-H seeded suite (tools/rule_h_seed.py)
# no longer runs. R9's contract stays in tools/check_r9.py (route_check --profile r9) for the R9 record, R8's in
# tools/check_r8.py (--profile r8), R7's in tools/check_r7.py (--profile r7).
# The plate model needs a python3 with numpy: set NUMPY_PY (default python3).
# The self-tests' real-board seeds run on the board being checked (R10_BOARD is exported as BOARD below, R5-GATE-03).
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
"$KICAD_PY" -I "$ROOT/tools/fit_check.py" "$BOARD" --profile r10 --report "$OUT/fit.json"
"${NUMPY_PY:-python3}" -I "$ROOT/tools/plate_model.py" "$OUT/fit.json" --profile r10 \
  --mass-spec "$ROOT/m3_design/assembly_review/sources/r10_design/masses.json" --json "$OUT/plate.json" > "$OUT/plate.txt"
"$KICAD_PY" -I "$ROOT/tools/check_r10.py" "$BOARD" --fit "$OUT/fit.json" --plate "$OUT/plate.json" \
  --report "$OUT/r10.json"
"$KICAD_PY" -I "$ROOT/tools/route_check.py" "$BOARD" --profile r10 --report "$OUT/route.json" \
  | { grep -E '^(FAIL|routing hygiene: [0-9])' || true; }       # clean routing (AGENTS.md §3); full list in route.json
python3 "$ROOT/m3_design/check_actuators.py" "$BOARD" --profile r10
# R8-GATE-05: the fab package (if one sits next to the board) is bound to the board it was made from. Only the repository
# board is held to it; a copy elsewhere is not.
MANIFEST="$(dirname "$BOARD")/fab/m3_fab_manifest.json"
if [[ "${R10_SKIP_FAB_MANIFEST:-0}" == 1 ]]; then   # m3_design/r10_build.sh: the package is rebuilt after the board
  echo "fab manifest: not checked (build stage: run m3_design/r10_fab.sh, then tools/check.sh)"
elif [[ -f "$MANIFEST" ]]; then
  if [[ "$BOARD" == "$ROOT/m3_design/assembly_review/m3.kicad_pcb" ]]; then
    python3 "$ROOT/tools/fab_manifest.py" "$BOARD" \
      || { echo "fab package bound to a different board: run m3_design/r10_fab.sh"; exit 1; }
  else
    echo "fab manifest: not checked (board copy)"
  fi
fi
# Gate self-tests (R4-GATE-02): a weakened gate fails here. Seeded faults on synthetic boards and on a temporary copy of
# the R10 board (R10_BOARD, set here to the checked board); about 2 minutes.
export R10_BOARD="$BOARD"
unset R10_SKIP_FAB_MANIFEST     # test_check_shell runs check.sh copies of its own
selftest() {          # print the unittest summary; a failing run prints its tail and fails the gate
  local out
  out="$("$@" 2>&1)" || { { printf '%s\n' "$out" | grep -v Debug || true; } | tail -40; echo "gate self-test FAILED: $*"; exit 1; }
  { printf '%s\n' "$out" | grep -v Debug || true; } | tail -3
}
selftest python3 "$ROOT/tools/test_check_shell.py"       # check.sh itself fails closed (R8-GATE-01)
selftest python3 "$ROOT/tools/test_procurement.py"       # required R9 / R10 limits cannot be weakened by report data
selftest "$KICAD_PY" "$ROOT/tools/test_fit_check.py"       # no -I: the test imports fit_check from its own folder
selftest "$KICAD_PY" -I "$ROOT/tools/test_paste_check.py"
selftest "$KICAD_PY" -I "$ROOT/tools/test_route_check.py"
selftest "$KICAD_PY" -I "$ROOT/tools/test_r10_check.py"
selftest "${NUMPY_PY:-python3}" -I "$ROOT/tools/test_r10_check.py" Plate HotplugNumerics
