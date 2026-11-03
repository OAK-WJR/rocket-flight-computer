# Round11: fresh verification of the generator fix

The coordinator transcribed the fresh validator's result; it saved no CAD or files.
Target PCB remains`0c50b9fd…`. This is an in-memory fix check, not round12,
Major closure, a service build or a full DRC result. Exact source hashes, passing
coordinates, counts and limitations are in[round11_fix_geometry.json](round11_fix_geometry.json).

The first fix prototype had five affected-geometry defect groups: C92-return and
U402-return vias hit moved pads; camera enable hit the switch fault pad/lane;
the shifted igniter diagonal hit R131; Q124-return holes entered the moved pads.
The verifier derived and checked the replacements now applied to generators:
rotated C60 atF(33.2,56.8), west sense lanex32.3, C92return(32.8,53.25),
U402return(32.3,59.5) via a dogleg, camera enable(34.4,57.4), original-line
IGN diagonal(7.4,59.4)→(12,64), and Q124return viasx15.85.

Reported alternative:977segments/294vias,2309effective shapes,532nearby foreign
pairs,zero clearance/acute/off-angle/arc/critical-partner findings. K-copper
checks613soldered pads/763via-paste pairs withzero findings; S-8 checks all4barrels
withzero findings. Corrected maximum envelopes/courtyards pass fit; all7terminals
have5.003012mm wire room, terminal bore minimum2.976269mm. J122's actual0.8mm
Fab text at(36.5,71.5) clears all drills by at least0.094831mm.

Three permissible own-net ring/opening webs remain in this prototype:≈0.050mm
at each Q124return and≈0.066mm at C92.2; hole gaps≈0.150/0.166mm pass the ordinary
rules, with no via in paste. The fartherQ124x16.05 option fails OUTclearance at
0.035376mm; selectedx15.85 gives0.176802mm. Inventory these pairs afresh on the
rebuilt board; they are deviations pending owner acceptance, not hidden waivers.

**Still required:** supervised full build/DRC/connectivity/reference-region gate,
actual-feed hot-plug, new fab/binding, byte reproducibility, commit, full clean
reviews and final measured acceptance inventory. No physical qualification.
