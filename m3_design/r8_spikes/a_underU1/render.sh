#!/bin/bash
# Spike (a) review images: crop of the U1 region per layer set (kicad-cli SVG -> qlmanage PNG). Scratch use only.
# usage: render.sh BOARD OUTPREFIX [x0 y0 w h]
set -euo pipefail
CLI=${KICAD_CLI:-/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli}
B=$1; P=$2; X=${3:-11}; Y=${4:-33}; W=${5:-24}; H=${6:-26}
D=$(dirname "$P"); mkdir -p "$D"
for spec in "F:F.Cu,F.Fab,F.CrtYd,Edge.Cuts" "B:B.Cu,B.Fab,B.CrtYd,Edge.Cuts" "In2:In2.Cu,Edge.Cuts" "FB:F.Cu,B.Cu,Edge.Cuts"; do
  name=${spec%%:*}; layers=${spec#*:}
  svg="$P.$name.svg"
  "$CLI" pcb export svg --mode-single --page-size-mode 2 --exclude-drawing-sheet --drill-shape-opt 2 \
      --layers "$layers" -o "$svg" "$B" >/dev/null 2>&1
  python3 - "$svg" "$X" "$Y" "$W" "$H" <<'EOF'
import re, sys
p, x, y, w, h = sys.argv[1], *map(float, sys.argv[2:])
s = open(p).read()
s = re.sub(r'width="[^"]*" height="[^"]*" viewBox="[^"]*"',
           f'width="{w*40:.0f}" height="{h*40:.0f}" viewBox="{x} {y} {w} {h}"', s, count=1)
s = s.replace('<title>', '<rect x="%s" y="%s" width="%s" height="%s" fill="#ffffff"/><title>' % (x, y, w, h), 1)
open(p, 'w').write(s)
EOF
  qlmanage -t -s 1600 -o "$D" "$svg" >/dev/null 2>&1 || true
  mv -f "$svg.png" "$P.$name.png" 2>/dev/null || true
  rm -f "$svg"
done
ls "$P".*.png
