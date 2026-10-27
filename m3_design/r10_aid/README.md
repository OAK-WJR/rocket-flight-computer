# R10 placement and routing aids (design aids, not build stages)

Run with KiCad's Python (`KPY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3`, `-I`).
Work on a scratch project made by `m3_design/r10_sch.py --out <dir>` then `m3_design/r10_pcb.py --project <dir>`
(the board must be named `m3.kicad_pcb` beside `m3.kicad_pro` / `m3.kicad_dru`, or DRC uses default rules).

- `ptool.py base.kicad_pcb moves.tsv out_prefix`: apply moves (`ref x y rot side`, or `@group dx dy refs...`), then
  report same-side courtyard overlaps, courtyards outside the outline, Edge.Cuts holes inside courtyards and bottom parts
  within 1 mm of a through-hole pin. Writes `out_prefix.kicad_pcb`.
- `writeback.py board.kicad_pcb m3_design/r10_place.tsv "basis"`: copy changed positions into the placement table.
- `pads.py board REF...`, `box.py board REF...`, `region.py board F|B x0 x1 y0 y1`, `items.py board x0 x1 y0 y1`:
  pad / courtyard / region / copper queries.
- `map.py board out`: copy with courtyard boxes and designators on silkscreen, for `kicad-cli pcb render`.
- `drc.sh board [regex]`: DRC summary (unconnected count, violations except silkscreen and dangling vias).
- `ncroute.py` (+ `sigroute.py`, kernel `astar.c`, net list `signal_nets.txt`, `freeze_signals.py`): the non-critical
  signal router of R10_DECISIONS D-R2-07 (octilinear A* with negotiated congestion). Compile the kernel beside it
  (`cc -O2 -o astar astar.c -lm`), point `R10_NUMPY_PATH` at a numpy for KiCad's Python 3.9, run on the board built
  through the `signals` family, then freeze with `freeze_signals.py routes.json board m3_design/r10_route_signals.py`.
  The frozen table was hand-cleaned afterwards; re-running the aid replaces those edits.
