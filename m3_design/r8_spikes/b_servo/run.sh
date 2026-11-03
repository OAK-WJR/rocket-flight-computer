#!/usr/bin/env bash
# R8 spike 3(b) servo bus: build the scratch board and verify it.
# usage: m3_design/r8_spikes/b_servo/run.sh SCRATCH_DIR [in2-full-tongue]
#   SCRATCH_DIR gets r7/ (R7 from git 431025d), base/ (make_base.py), route/ (servo_route.py) and report files.
#   Every folder holds m3.kicad_pcb with R7's m3.kicad_pro / m3.kicad_dru, so pcbnew loads and saves the real rules.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(git -C "$HERE" rev-parse --show-toplevel)"
S="${1:?scratch dir}"; mkdir -p "$S"; S="$(cd "$S" && pwd)"
KPY=${KICAD_PY:-/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3}
SEED=${SEED:-$HERE/seed_b0_place_final.tsv}      # Strategy B seed placement (survey partial/b0_place_final.tsv, copied)
D=m3_design/assembly_review
for d in r7 base route; do
  mkdir -p "$S/$d"
  git -C "$ROOT" show 431025d:$D/m3.kicad_pro > "$S/$d/m3.kicad_pro"
  git -C "$ROOT" show 431025d:$D/m3.kicad_dru > "$S/$d/m3.kicad_dru"
  git -C "$ROOT" show 431025d:$D/fp-lib-table > "$S/$d/fp-lib-table"
  ln -sfn "$ROOT/$D/kilib" "$S/$d/kilib"            # ${KIPRJMOD}/kilib/rocket.pretty, read only
done
git -C "$ROOT" show 431025d:$D/m3.kicad_pcb > "$S/r7/m3.kicad_pcb"
shasum -a 256 "$S/r7/m3.kicad_pcb" | grep -q '^c872a3d3' || { echo 'R7 board hash mismatch'; exit 1; }
run() { PYTHONUNBUFFERED=1 "$KPY" -I "$@" 2>&1 | grep -v -e 'memory leak' -e 'stdpbase.cpp' || true; }
run "$HERE/make_base.py" "$S/r7/m3.kicad_pcb" "$ROOT/$D/schematic.net.xml" "$SEED" "$S/base/m3.kicad_pcb"
run "$HERE/servo_route.py" "$S/base/m3.kicad_pcb" "$S/route/m3.kicad_pcb" ${2:+--$2}
for d in base route; do   # pcbnew rewrites the project file on save; put R7's back before kicad-cli reads it
  git -C "$ROOT" show 431025d:$D/m3.kicad_pro > "$S/$d/m3.kicad_pro"
done
run "$HERE/verify.py" "$S/route/m3.kicad_pcb" --report "$S/verify.json"
