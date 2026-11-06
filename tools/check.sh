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
# R11 (M3-ASSY-R11, D-R11-08): when m3_design/r11/m3.kicad_pcb is tracked by git, the R11 section below runs on it after
# R10's gate; a board passed explicitly whose title-block revision is M3-ASSY-R11 runs the R11 section alone (R10's gate
# is for R10 boards). R11 section: DRC / parity / ERC on m3_design/r11/, m3_design/r11_sch_check.py (required: a missing
# R11 schematic contract fails), metadata / models, silkscreen, fit_check --profile r11, tools/check_r11.py,
# route_check --profile r11 and the R11 fab package (tools/fab_manifest_r11.py --content on the repository R11 board);
# its self-test (tools/test_r11_check.py) then must not skip its real-board tests (R11_BOARD_REQUIRED).
# R12 (M3-ASSY-R12, m3_design/r12/design/r12_plan.md section 4): when m3_design/r12/m3.kicad_pcb is tracked by git, the
# R12 section runs on it after R10's and R11's; a board passed explicitly whose title-block revision is M3-ASSY-R12 runs
# the R12 section alone. R12 section: DRC / parity / ERC on m3_design/r12/, m3_design/r12_sch_check.py (required), the
# R12 library check (m3_design/r12_parts.py --check), metadata / models, silkscreen, fit_check --profile r12,
# tools/check_r12.py, route_check --profile r12 and the R12 fab package (tools/fab_manifest_r12.py --content on the
# repository R12 board, required once the board is tracked); its self-test (tools/test_r12_check.py) then must not skip
# its real-board tests (R12_BOARD_REQUIRED). The R12 fab and stage D self-tests (tools/test_r12_fab.py,
# tools/test_r12_stageD.py; R12F4-TRI-01) always run; test_r12_fab's package tests use R12_BOARD, else the repository
# R12 board, and skip only when no R12 board exists.
# Usage: tools/check.sh [path/to/board.kicad_pcb]      exit 0 = every check clean
set -euo pipefail
# Fail closed on a parse error: bash reads a script as it runs, so a syntax error late in the file would otherwise let
# the earlier stages run and the EXIT trap end the run with status 0. Parse the whole file before any stage runs.
bash -n "$0" || { echo "check.sh does not parse: refusing to run" >&2; exit 2; }
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CANON="$ROOT/m3_design/assembly_review/m3.kicad_pcb"
CANON11="$ROOT/m3_design/r11/m3.kicad_pcb"
CANON12="$ROOT/m3_design/r12/m3.kicad_pcb"
BOARD="${1:-$CANON}"
[[ -f "$BOARD" ]] || { echo "board not found: $BOARD" >&2; exit 1; }
BOARD="$(cd "$(dirname "$BOARD")" && pwd)/$(basename "$BOARD")"   # absolute: the audit step runs in quality_audit/
revision() {          # the title-block revision of a saved board
  python3 -c 'import re, sys; m = re.search(r"\(title_block\b.*?\(rev\s+\"([^\"]*)\"", open(sys.argv[1], errors="ignore").read(), re.S); print(m.group(1) if m else "")' "$1"
}
unset R11_BOARD R11_BOARD_REQUIRED   # set below only when the R11 section has run on a board
unset R12_BOARD R12_BOARD_REQUIRED   # set below only when the R12 section has run on a board
R11=""                # the R11 board the R11 section checks, if any
R12=""                # the R12 board the R12 section checks, if any
R10_RUN=1
if [[ "$(revision "$BOARD")" == "M3-ASSY-R12" ]]; then
  R12="$BOARD"; R10_RUN=0
elif [[ "$(revision "$BOARD")" == "M3-ASSY-R11" ]]; then
  R11="$BOARD"; R10_RUN=0
else
  if git -C "$ROOT" ls-files --error-unmatch "m3_design/r11/m3.kicad_pcb" >/dev/null 2>&1; then
    [[ -f "$CANON11" ]] || { echo "R11 board tracked but missing: $CANON11" >&2; exit 1; }
    R11="$CANON11"
  fi
  if git -C "$ROOT" ls-files --error-unmatch "m3_design/r12/m3.kicad_pcb" >/dev/null 2>&1; then
    [[ -f "$CANON12" ]] || { echo "R12 board tracked but missing: $CANON12" >&2; exit 1; }
    R12="$CANON12"
  fi
fi
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
trap 'status=$?; echo "reports: $OUT"; exit $status' EXIT   # keeps a failing stage's status (a parse error is the bash -n check's)
drc_erc() {            # DRC every severity with schematic parity, ERC on the sibling schematic: all zero
  local board="$1" out="$2"
  "$CLI" pcb drc --severity-all --schematic-parity --format json -o "$out/drc.json" "$board" >/dev/null
  "$CLI" sch erc --severity-all --format json -o "$out/erc.json" "${board%.kicad_pcb}.kicad_sch" >/dev/null
  python3 - "$out" <<'PY'
import json, sys, collections
o = sys.argv[1]
d = json.load(open(o + '/drc.json')); e = json.load(open(o + '/erc.json'))
v, u, p = d['violations'], d['unconnected_items'], d.get('schematic_parity', [])
erc = [x for s in e['sheets'] for x in s['violations']]
print(f"DRC violations {len(v)}  unconnected {len(u)}  schematic parity {len(p)}  ERC {len(erc)}")
for k, n in collections.Counter(x['type'] for x in v + erc).most_common(15): print(f"  {n:4d}  {k}")
sys.exit(1 if (v or u or p or erc) else 0)
PY
}
if (( R10_RUN )); then
drc_erc "$BOARD" "$OUT"
# R23-GATE-06: the schematic contract and its sheet replay, the step r10_build.sh runs (about 6 s): every committed sheet,
# the netlist and the DRU must be what m3_design/r10_sch.py regenerates, so a hand-edited sheet note fails here.
KICAD_CLI="$CLI" "$KICAD_PY" -I -B "$ROOT/m3_design/r10_sch_check.py" --project "$(dirname "$BOARD")" \
  --json "$OUT/sch_check.json" > "$OUT/sch_check.txt" 2>&1 \
  && echo "schematic contract and sheet replay (r10_sch_check): OK" \
  || { echo "schematic contract / sheet replay FAILED: see $OUT/sch_check.json"; exit 1; }
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
fi
# ---- R11 section (D-R11-08) -------------------------------------------------------------------------------------------
if [[ -n "$R11" ]]; then
  echo "== R11 gate: $R11"
  O11="$OUT/r11"; mkdir -p "$O11"
  drc_erc "$R11" "$O11"
  [[ -f "$ROOT/m3_design/r11_sch_check.py" ]] \
    || { echo "R11 schematic contract FAILED: m3_design/r11_sch_check.py missing while the R11 board exists"; exit 1; }
  KICAD_CLI="$CLI" "$KICAD_PY" -I -B "$ROOT/m3_design/r11_sch_check.py" --project "$(dirname "$R11")" \
    --json "$O11/sch_check.json" > "$O11/sch_check.txt" 2>&1 \
    && echo "R11 schematic contract and sheet replay (r11_sch_check): OK" \
    || { echo "R11 schematic contract / sheet replay FAILED: see $O11/sch_check.json"; exit 1; }
  (cd "$ROOT/quality_audit" && python3 verify_board.py "$R11" --cli "$CLI" --output "$O11/audit.json" >/dev/null) \
    && echo "R11 metadata / 3D model audit: OK" || { echo "R11 metadata / 3D model audit FAILED: see $O11/audit.json"; exit 1; }
  python3 "$ROOT/tools/silk_check.py" "$R11" --cli "$CLI"
  "$KICAD_PY" -I "$ROOT/tools/fit_check.py" "$R11" --profile r11 --report "$O11/fit.json"
  "$KICAD_PY" -I "$ROOT/tools/check_r11.py" "$R11" --fit "$O11/fit.json" --report "$O11/r11.json"
  "$KICAD_PY" -I "$ROOT/tools/route_check.py" "$R11" --profile r11 --report "$O11/route.json" \
    | { grep -E '^(FAIL|routing hygiene: [0-9])' || true; }
  M11="$(dirname "$R11")/fab/m3_fab_manifest.json"
  if [[ "$R11" -ef "$CANON11" ]]; then
    python3 "$ROOT/tools/fab_manifest_r11.py" "$CANON11" --content \
      || { echo "R11 fab package unbound, bound to a different board or failing its content checks"; exit 1; }
  elif [[ -f "$M11" ]]; then
    echo "R11 fab manifest: not checked (board copy)"
  fi
  export R11_BOARD="$R11" R11_BOARD_REQUIRED=1
fi
# ---- R12 section (r12_plan.md section 4) ------------------------------------------------------------------------------
if [[ -n "$R12" ]]; then
  echo "== R12 gate: $R12"
  O12="$OUT/r12"; mkdir -p "$O12"
  drc_erc "$R12" "$O12"
  [[ -f "$ROOT/m3_design/r12_sch_check.py" ]] \
    || { echo "R12 schematic contract FAILED: m3_design/r12_sch_check.py missing while the R12 board exists"; exit 1; }
  KICAD_CLI="$CLI" "$KICAD_PY" -I -B "$ROOT/m3_design/r12_sch_check.py" --project "$(dirname "$R12")" \
    --json "$O12/sch_check.json" > "$O12/sch_check.txt" 2>&1 \
    && echo "R12 schematic contract and sheet replay (r12_sch_check): OK" \
    || { echo "R12 schematic contract / sheet replay FAILED: see $O12/sch_check.json"; exit 1; }
  "$KICAD_PY" -I -B "$ROOT/m3_design/r12_parts.py" --check
  (cd "$ROOT/quality_audit" && python3 verify_board.py "$R12" --cli "$CLI" --output "$O12/audit.json" >/dev/null) \
    && echo "R12 metadata / 3D model audit: OK" || { echo "R12 metadata / 3D model audit FAILED: see $O12/audit.json"; exit 1; }
  python3 "$ROOT/tools/silk_check.py" "$R12" --cli "$CLI"
  "$KICAD_PY" -I "$ROOT/tools/fit_check.py" "$R12" --profile r12 --report "$O12/fit.json"
  "$KICAD_PY" -I "$ROOT/tools/check_r12.py" "$R12" --fit "$O12/fit.json" --report "$O12/r12.json"
  "$KICAD_PY" -I "$ROOT/tools/route_check.py" "$R12" --profile r12 --report "$O12/route.json" \
    | { grep -E '^(FAIL|routing hygiene: [0-9])' || true; }
  M12="$(dirname "$R12")/fab/m3_fab_manifest.json"
  if [[ "$R12" -ef "$CANON12" ]]; then
    [[ -f "$ROOT/tools/fab_manifest_r12.py" ]] \
      || { echo "R12 fab package FAILED: tools/fab_manifest_r12.py missing while the R12 board is tracked"; exit 1; }
    python3 "$ROOT/tools/fab_manifest_r12.py" "$CANON12" --content \
      || { echo "R12 fab package unbound, bound to a different board or failing its content checks"; exit 1; }
  elif [[ -f "$M12" ]]; then
    echo "R12 fab manifest: not checked (board copy)"
  fi
  export R12_BOARD="$R12" R12_BOARD_REQUIRED=1
fi
# Gate self-tests (R4-GATE-02): a weakened gate fails here. Seeded faults on synthetic boards and on a temporary copy of
# the R10 board (R10_BOARD, set here to the checked board); about 2 minutes.
if (( R10_RUN )); then export R10_BOARD="$BOARD"; else export R10_BOARD="$CANON"; fi
selftest() {          # print the unittest summary; a failing run prints its tail and fails the gate
  local out
  out="$("$@" 2>&1)" || { { printf '%s\n' "$out" | grep -v Debug || true; } | tail -40; echo "gate self-test FAILED: $*"; exit 1; }
  { printf '%s\n' "$out" | grep -v Debug || true; } | tail -3
}
selftest python3 "$ROOT/tools/test_check_shell.py"       # check.sh itself fails closed (R8-GATE-01)
selftest python3 "$ROOT/tools/test_procurement.py"       # required R9 / R10 limits cannot be weakened by report data
selftest python3 "$ROOT/tools/test_fab_validation.py"    # placement, export and binding regressions (R18-GATE-04)
selftest "$KICAD_PY" "$ROOT/tools/test_fit_check.py"       # no -I: the test imports fit_check from its own folder
selftest "$KICAD_PY" -I "$ROOT/tools/test_paste_check.py"
selftest "$KICAD_PY" -I "$ROOT/tools/test_r10_parts.py"
selftest "$KICAD_PY" -I "$ROOT/tools/test_route_check.py"
selftest "$KICAD_PY" -I "$ROOT/tools/test_r10_check.py"
selftest "${NUMPY_PY:-python3}" -I "$ROOT/tools/test_r10_check.py" HotplugNumerics Plate   # Plate: R18-MEC-01 strain table
selftest "$KICAD_PY" -I "$ROOT/tools/test_r12_fab.py"      # R12F4-TRI-01: R12 fab tooling; exports R12_BOARD when present
selftest python3 -I "$ROOT/tools/test_r12_stageD.py"       # R12F4-TRI-01: R12 stage D / hot-plug wrappers (no pcbnew)
selftest "$KICAD_PY" -I "$ROOT/tools/test_r11_check.py"    # D-R11-08: R11 rules; real-board seeds when R11_BOARD is set
selftest "$KICAD_PY" -I "$ROOT/tools/test_r12_check.py"    # R12 gate skeleton, schematic contract, windows; board seeds later
