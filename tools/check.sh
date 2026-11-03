#!/usr/bin/env bash
# Board gate: DRC/parity, ERC, metadata/models, silkscreen, fit, the R10 CAD contract, clean routing, the
# actuator contract and the gates' own seeded tests (including routing, R10 and procurement).
# R10 (M3-ASSY-R10, r10_plan.md section 4): tools/check_r10.py reads the fit report made here (--profile r10),
# route_check profile r10, and K-actuators inside check_r10. The plate model is optional (requirements audit2).
# R10 has no pyro-specific spacing rule (r10_plan section 2 item 1), so the rule-H seeded suite (tools/rule_h_seed.py)
# no longer runs. R9's contract stays in tools/check_r9.py (route_check --profile r9) for the R9 record, R8's in
# tools/check_r8.py (--profile r8), R7's in tools/check_r7.py (--profile r7).
# The optional plate model is separate; NUMPY_PY (default python3) runs the numerical gate self-tests.
# The self-tests' real-board seeds run on the board being checked (R10_BOARD is exported as BOARD below, R5-GATE-03).
# The repository board (recognised as the same file, however its path is spelled) must carry its bound fab package,
# and the package must pass its content checks (R17-GATE-01, R18-GATE-04 / -05); a board copy is not held to one.
# Usage: tools/check.sh [path/to/board.kicad_pcb]      exit 0 = every check clean
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CANON="$ROOT/m3_design/assembly_review/m3.kicad_pcb"
BOARD="${1:-$CANON}"
[[ -f "$BOARD" ]] || { echo "board not found: $BOARD" >&2; exit 1; }
BOARD="$(cd "$(dirname "$BOARD")" && pwd)/$(basename "$BOARD")"   # absolute: the audit step runs in quality_audit/
CLI="${KICAD_CLI:-$(command -v kicad-cli || true)}"
if [[ -z "$CLI" ]]; then
  for candidate in /Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli /Applications/KiCad.app/Contents/MacOS/kicad-cli; do
    if [[ -x "$candidate" ]]; then CLI="$candidate"; break; fi
  done
fi
CLI="$(command -v "$CLI")" || { echo 'KiCad CLI unavailable; set KICAD_CLI' >&2; exit 1; }
CLI="$(python3 -c 'from pathlib import Path; import sys; print(Path(sys.argv[1]).resolve())' "$CLI")"
# Every child, including the schematic replay inside the seeded tests, must use this selection.
export KICAD_CLI="$CLI"
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
# R23-GATE-06: the schematic contract and its sheet replay, the step r10_build.sh runs (about 6 s): every committed sheet,
# the netlist and the DRU must be what m3_design/r10_sch.py regenerates, so a hand-edited sheet note fails here.
KICAD_CLI="$CLI" "$KICAD_PY" -I -B "$ROOT/m3_design/r10_sch_check.py" --project "$(dirname "$BOARD")" \
  --json "$OUT/sch_check.json" > "$OUT/sch_check.txt" 2>&1 \
  && echo "schematic contract and sheet replay (r10_sch_check): OK" \
  || { echo "schematic contract / sheet replay FAILED: see $OUT/sch_check.json"; exit 1; }
"$KICAD_PY" -I -B "$ROOT/tools/check_r10_diagnostic_profile.py" "$BOARD"
(cd "$ROOT/quality_audit" && python3 verify_board.py "$BOARD" --cli "$CLI" --output "$OUT/audit.json" >/dev/null) \
  && echo "metadata / 3D model audit: OK" || { echo "metadata / 3D model audit FAILED: see $OUT/audit.json"; exit 1; }
python3 "$ROOT/tools/silk_check.py" "$BOARD" --cli "$CLI"     # DRC skips silkscreen wholly outside the outline
"$KICAD_PY" -I "$ROOT/m3_design/r10_parts.py" --check --board "$BOARD"   # D-R11-03: libraries and native fire budget
"$KICAD_PY" -I "$ROOT/tools/fit_check.py" "$BOARD" --profile r10 --report "$OUT/fit.json"
"$KICAD_PY" -I "$ROOT/tools/check_r10.py" "$BOARD" --fit "$OUT/fit.json" \
  --report "$OUT/r10.json"
"$KICAD_PY" -I "$ROOT/tools/route_check.py" "$BOARD" --profile r10 --report "$OUT/route.json" \
  | { grep -E '^(FAIL|routing hygiene: [0-9])' || true; }       # clean routing (AGENTS.md §3); full list in route.json
# R17-GATE-01 / R18-GATE-05: the repository board requires its bound fab package; absence must fail too. -ef recognises
# it by device and inode (a case variant, symlink or relative spelling of the same file is the repository board). There
# is no skip: m3_design/r10_build.sh rebuilds the package (m3_design/r10_fab.sh) before it runs this gate.
# R18-GATE-04: besides the hash binding, the bound package must pass its content checks (fab_manifest.content_checks:
# check_r10 S-4 on the exported BOM / CPL, jlc_orient --verify-cpl, paste_check). A board copy is not held to a package.
MANIFEST="$(dirname "$BOARD")/fab/m3_fab_manifest.json"
if [[ "$BOARD" -ef "$CANON" ]]; then
  python3 "$ROOT/tools/fab_manifest.py" "$CANON" --content \
    || { echo "fab package unbound, bound to a different board or failing its content checks: run m3_design/r10_fab.sh"
         exit 1; }
elif [[ -f "$MANIFEST" ]]; then
  echo "fab manifest: not checked (board copy)"
fi
# Gate self-tests (R4-GATE-02): a weakened gate fails here. Seeded faults on synthetic boards and on a temporary copy of
# the R10 board (R10_BOARD, set here to the checked board); about 2 minutes.
export R10_BOARD="$BOARD"
selftest() {          # print the unittest summary; a failing run prints its tail and fails the gate
  local out
  out="$("$@" 2>&1)" || { { printf '%s\n' "$out" | grep -v Debug || true; } | tail -40; echo "gate self-test FAILED: $*"; exit 1; }
  { printf '%s\n' "$out" | grep -v Debug || true; } | tail -3
}
selftest python3 "$ROOT/tools/test_check_shell.py"       # check.sh itself fails closed (R8-GATE-01)
selftest python3 "$ROOT/tools/test_schematic_repro.py"   # exporter metadata must not hide electrical edits
selftest python3 -B "$ROOT/diagnostics/test_r10_offline.py"  # offline records, never a board connection
selftest python3 -B "$ROOT/diagnostics/test_r10_swd.py"      # fake readers only; no probe enumeration
selftest python3 -B "$ROOT/diagnostics/test_r10_firmware.py" # synthetic DP/image/mailbox; never opens a probe
selftest python3 -B "$ROOT/m3_firmware/r10/test_r10.py"     # real portable C + saved records; no probe/flash
selftest python3 -B "$ROOT/m3_firmware/r10/imu/test_imu_core.py" # fitted ST sensor core, scripted registers only
selftest python3 -B "$ROOT/m3_firmware/r10/baro/test_baro.py" # MS5611 core, scripted I2C only
selftest python3 -B "$ROOT/m3_firmware/r10/voltage/test_voltage.py" # voltage core + fake-MMIO ADC; no physical hardware
selftest python3 "$ROOT/tools/test_procurement.py"       # required R9 / R10 limits cannot be weakened by report data
selftest python3 "$ROOT/tools/test_fab_validation.py"    # placement, export and binding regressions (R18-GATE-04)
selftest "$KICAD_PY" "$ROOT/tools/test_fit_check.py"       # no -I: the test imports fit_check from its own folder
selftest "$KICAD_PY" -I "$ROOT/tools/test_paste_check.py"
selftest "$KICAD_PY" -I "$ROOT/tools/test_r10_parts.py"
selftest "$KICAD_PY" -I "$ROOT/tools/test_route_check.py"
selftest "$KICAD_PY" -I "$ROOT/tools/test_r10_check.py"
selftest "${NUMPY_PY:-python3}" -I "$ROOT/tools/test_r10_check.py" HotplugNumerics Plate   # Plate: R18-MEC-01 strain table
