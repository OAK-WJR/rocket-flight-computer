# Round 11 terminal Major: fresh closure verification

A fresh read-only validator independently rechecked the rebuilt PCB `0ad0135cb9ff1f6ace7ef9d5ba9006b727b293d7b5224bb97dad47859b91238d` and returned a scoped PASS for R11-BOM-01 / R11-MEC-01. The coordinator transcribed its report; the validator wrote no files. Before/after board hashes agree. This is closure evidence, not a full review round.

The [maker T0-1 drawing, sheet 1](https://atta.szlcsc.com/upload/public/pdf/source/20251124/8C215F69B14C8E54AE0F8E5023D4AE9F.pdf) supports the maximum 2P/4P/5P unions in [the structured receipt](round11_terminal_closure.json). All models match within 0.00001 mm with outward handedness. Every terminal has 5.003011866 mm wire room, 0.053011866 mm above the unchanged 4.95 mm floor, and a calculated body-to-bore margin of 2.976268566 mm.

The west row is x=7.4 mm, the east row x=38.6 mm. Adjacent 4P maximum bodies have 0.48 mm gap; courtyard lines have 0.08 mm and their strokes 0.03 mm. Across 483 terminal/top-courtyard pairs there are no positive stroke overlaps; there are no terminal/body intersections. All 35 D-R11-01 poses match their generator records. Focused fit, P-11 and M-6 each return no findings.

The 17 repaired bottom parts retain 1.536–3.955 mm to through-hole pad copper. The independent scan checked 2,227 body pairs and 2,346 courtyard pairs. Body models remain separate. Three drawing residuals remain: C421/U12 courtyard lines touch (0.050 mm stroke overlap); R151/D121 and R152/D121 lines have 0.010 mm gaps (0.040 mm stroke overlap). Native courtyard polygons do not intersect; modeled body gaps are 0.500/0.949914/0.949914 mm. These are recorded presentation residuals; no blocking graphics-stroke rule is inferred.

No Critical or Major was found in this scope. The full gate, fab package, reproducibility, firmware and physical harness/screwdriver/bore/stack qualification are outside this receipt. The complete build and fresh full rounds must provide their own evidence.
