#!/usr/bin/env bash
# Regenerate M3-ASSY-R5 from the M3-ASSY-R4 board (docs/M3_R5.md "How R5 is built").
#
# usage: m3_design/r5_build.sh            (from anywhere in the repo)
#        KICAD_PY=/path/to/kicad/python3 m3_design/r5_build.sh
#
# Restores the R4 board from git (commit R4 below, worktree only, the index is untouched), runs r5_pcb.py
# (placement, zones, scripted critical copper), applies the Freerouting session in git (r5_route.py import;
# no Java needed), applies the finisher's recorded result in git (r5_finish.py --replay=m3_design/r5_finish.json;
# without that file it runs the search, r5_finish.py --shake, and records it), runs r5_post.py (clean-up, silkscreen,
# refill), then the board gate, the actuator safety
# contract and the envelope check. The schematic is R4's, unchanged. It overwrites
# m3_design/assembly_review/m3.kicad_pcb, so commit or stash your own changes first. The fab package is not
# rebuilt: run tools/jlc_orient.py, tools/export_fab.py, tools/jlc_stock.py and tools/jlc_cost.py afterwards.
#
# To re-route after changing r5_pcb.py: run up to r5_pcb.py, then
#   "$KICAD_PY" -I m3_design/r5_route.py export [--seed=N] && java -jar freerouting-2.4.1.jar \
#       -de m3_design/r5_autoroute.dsn -do m3_design/r5_autoroute.ses -mp 80 \
#       --router.optimizer.enabled=false --router.automatic_neckdown=false --router.neck_width_um=150 \
#       --router.copper_to_edge_clearance_um=520 --router.hole_clearance_um=260
# (Freerouting v2.4.1 only, kept outside the repo) and run this script again. --seed=N shuffles the DSN's order
# (another, equally valid attempt; Freerouting is order-sensitive); keep the DSN that produced the session with it,
# and delete m3_design/r5_finish.json so the finisher searches again (KiCad's DRC does not list the open connections
# the same way on every run, so its search is not repeatable: keep a run that leaves nothing open).
# Optional second session: run this script up to r5_finish.py --force (which also draws what is still open across
# the router's copper), export with --warm (the router's own copper stays movable, the scripted and finisher copper
# fixed) to m3_design/r5_autoroute_warm.dsn, route it to r5_autoroute_warm.ses with the same flags, and run this
# script again.
# The session in git was exported with --seed=61; r5_finish.json is a recorded run of the finisher's search
# (r5_finish.py --shake) on it, less one 0.32 mm GND stub its island search had left 0.12 mm from C14.1 (C14.2 reaches the
# pour without it), with LOGIC_SOURCE_ST's via link at (19.4, 41.2) drawn straight onto its trace (it left an acute
# corner).
set -euo pipefail
R4=fa68b38
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
KICAD_PY=${KICAD_PY:-/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3}
D=m3_design/assembly_review
git restore --source="$R4" --worktree -- "$D"/m3.kicad_pcb
"$KICAD_PY" -I m3_design/r5_pcb.py
"$KICAD_PY" -I m3_design/r5_route.py import
if [ -f m3_design/r5_autoroute_warm.ses ]; then   # second Freerouting session, warm-started from the finished board
  "$KICAD_PY" -I m3_design/r5_finish.py --force     # (the board the warm session's DSN was exported from)
  "$KICAD_PY" -I m3_design/r5_route.py import "$D"/m3.kicad_pcb m3_design/r5_autoroute_warm.ses
fi
if [ -f m3_design/r5_finish.json ]; then          # the finisher's recorded result (its search is not repeatable)
  "$KICAD_PY" -I m3_design/r5_finish.py --replay=m3_design/r5_finish.json
else
  "$KICAD_PY" -I m3_design/r5_finish.py --shake --record=m3_design/r5_finish.json
fi
"$KICAD_PY" -I m3_design/r5_post.py
tools/check.sh
python3 m3_design/check_actuators.py
"$KICAD_PY" -I tools/fit_check.py
