#!/usr/bin/env bash
# Regenerate M3-ASSY-R7 from the committed M3-ASSY-R6 board (docs/M3_R7.md "R7 board").
#
# usage: m3_design/r7_build.sh            (from anywhere in the repo)
#        KICAD_PY=/path/to/kicad/python3 m3_design/r7_build.sh
#
# Restores the R6 board from git (commit R6 below, worktree only, the index is untouched), then runs, in order:
#   r7_pcb.py    the +18 mm translation, 46 x 118 mm outline, supports, J123's move, the R6 port parts and their
#                copper out, the R7 parts from the netlist, RF-strip placement, stackup JLC041611-7628, pours and
#                keep-out areas (SHA-256 check of the R6 board first);
#   r7_route.py  the scripted copper (U1-side surgery, both GCPW lines, the GNSS feed limiter, both modules' local
#                copper, the interface corridor and band), the strip fence and stitching, and the redraw of the
#                non-critical R6 connections the new copper displaced, from explicit geometry (r7_redraw.py; it also
#                removes the R6 copper the removed port parts left behind; sources/r7_review/fix2_F2_handoff.md);
#   r7_rework.py the review pass-2 fixes outside the RF strip, on the routed board: GND return vias, CAM_RX_WIRE's
#                via out of R100.1, RXEN, FB31's feed, In2 GND forward of the strip and under the left-edge corridor,
#                interface widths (sources/r7_review/fix2_F1_handoff.md);
#   r7_hygiene.py the last copper stage: canonical copper on the whole board (inherited R6 copper included) — hand
#                redraws of the doubled / tangled conductors, then generic duplicate, copy, dead-copper, merge and
#                chain clean-up, then GND return vias at critical layer changes, then hand redraws of the residue
#                (hand_post); connectivity is checked after every stage (sources/r7_review/fix2_F3_handoff.md;
#                tools/route_check.py, run by the gate, holds it);
#   r7_polish.py the review pass-3 and pass-4 fixes on the cleaned board: dead copper under route_check's pour-island
#                rule, SWCLK / SWDIO and PYRO1_CONT rerouted (PYRO1_CONT on its plane-preserving 6-via route), short
#                corners redrawn, the L1.2 node, the radio band fan-in, non-critical debris, C302.2 relief, GND return
#                vias (r7_hygiene.gnd_vias again on the final copper), the pour slivers and unstitched fingers kept out
#                of the fill (R7_POUR_TRIM_n rule areas, never a pad's relief ring) and the RF strip's GND stitched to
#                within 4 mm of copper (sources/r7_review/fix3_F4_handoff.md, fix4_F5_handoff.md); fix pass 5: the
#                remaining removable jogs, staircases, stubs and hops, the band-end In2 GND, ARM1_SENSE's GND vias, the
#                forward-edge stitching and the single-via GND pieces (fix5_F6_handoff.md); fix pass 6: QSPI_IO3's bump,
#                SW_NODE, LOGIC_SS, CAM_FAULT_N / SERVO4_MCU apart, the 3V3 C179 dip, RAW_ACT's B.Cu duplicate, the poured-net
#                runs route_check's chain_detour test finds, BAT_IN_F's In2 vias (fix6_F7_handoff.md); fix pass 7: the
#                local bumps route_check's local_bump test finds, the redundant 3V3 via pair, ACT_EN's In2 hop,
#                ARM1_SENSE's split at R180.1, CAM_FAULT_N / I2C1_SDA, CAM_5V_SENSE / SERVO2_OUT, the BAT_IN via
#                on its track, the 3V3A hop, BAT_IN_B's lobe, two 3V3 plane duplicates, two non-critical bumps, the 7.7 A necks
#                (fix7_F8_handoff.md);
#   r7_post.py   silkscreen (M3-ASSY-R7, GNSS / RADIO jack legends, TP30 SAFEBOOT, designators; every visible
#                designator passes the courtyard test or is hidden; fix pass 7: part legends beside their part), refill;
# and the board gate. Every step is deterministic (fixed KIID seeds, no random search), so a run reproduces the
# board in git byte for byte. It overwrites m3_design/assembly_review/m3.kicad_pcb, so commit or stash your own
# changes first. The fab package is not rebuilt: run tools/jlc_orient.py, tools/export_fab.py, tools/jlc_stock.py
# and tools/jlc_cost.py afterwards.
set -euo pipefail
R6=3b215ba
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
KICAD_PY=${KICAD_PY:-/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3}
D=m3_design/assembly_review
git restore --source="$R6" --worktree -- "$D"/m3.kicad_pcb
PYTHONUNBUFFERED=1 "$KICAD_PY" -I m3_design/r7_pcb.py
PYTHONUNBUFFERED=1 "$KICAD_PY" -I m3_design/r7_route.py
PYTHONUNBUFFERED=1 "$KICAD_PY" -I m3_design/r7_rework.py
PYTHONUNBUFFERED=1 "$KICAD_PY" -I m3_design/r7_hygiene.py
PYTHONUNBUFFERED=1 "$KICAD_PY" -I m3_design/r7_polish.py
PYTHONUNBUFFERED=1 "$KICAD_PY" -I m3_design/r7_post.py
tools/check.sh
