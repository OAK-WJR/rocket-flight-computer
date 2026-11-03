# Round15 gate fixes

Checker-only closure of R15-GATE-01/02/03 on PCB
`7866d6b895573eb10c14d0227ee4bdde8b4fba6145529786cd554cdb80121783`.
The canonical board is unchanged. This is focused implementation evidence;
root owns the subsequent build, complete gate, fabrication and reproducibility.

- S-4 reuses the existing CSV walk and native footprint table. Every production
  BOM designator must identify its fitted native LCSC, canonical Manufacturer
  Part and footprint. Wrong/blank/missing identity columns, an excluded J2 and
  a wrong second merged member reject. Native 199-part merged rows and the
  quantity-free CPL pass; positive Qty and duplicate-row checks remain active.
- `fit_check` adds only the reviewed M3_MA_8x10 local box
  `(-4.25,-4.25,4.25,4.25,0,10.8)` mm to its existing normalized-box guard.
  The [MA supplier sheet](https://atta.szlcsc.com/upload/public/pdf/source/20260306/24758A4FC016E80367B87853635CDCC1.pdf)
  p2 and `parts_qualification.md` provide the retained conservative allocation:
  base8.3±0.2, height10±0.5 plus an inferred0.3mm projection. This does not
  qualify the land, soldering, seating or installed fit. XYZ scale0.01 and
  scale0.99999 reject. Equivalent metre coordinates with scale1000 pass with
  zero board-box difference. The existing0.000020mm tolerance is unchanged;
  synthetic offsets0.000019mm pass and0.000021mm reject. DB125/SD guards remain.
- K-fill snapshots native polygons before refill and compares the two Boolean
  differences for each zone UUID/layer/net. The existing0.01mm² tolerance now
  bounds symmetric difference. The sealed0.1mm In2-GND translation has equal
  saved/refilled area237.869754823186mm² but difference5.694234392076mm² and
  rejects. A native refill passes. Area-preserving shear rejects; reordered
  vertices/collinear subdivision pass. The synthetic boundary is0.010000mm²
  accepted and0.010020mm² rejected; neither is an additional design allowance.

| Executed check | Result |
|---|---|
| Old implementation, five focused R10 methods |exit1;18 detector-assertion failures,0errors |
| Old implementation, C84 fit method |exit1;3 detector-assertion failures,0errors |
| Updated R10 focused regressions |exit0;18tests,0failures/errors/skips |
| Complete fit regression suite |exit0;31tests,0failures/errors/skips |
| Direct native controls and sealed mutants |exit0;S-4/K-fill/P-11/fit controls pass; targeted mutants reject |
| Unchanged7866, production API10.0.6 |9entries;area delta0 and symmetric difference0 |
| Unchanged7866, official API10.0.7 |9entries;max area delta0.000081856282mm²;max difference0.000155117521mm² |

Both API versions pass the unchanged board/complete-copy geometry control at
0.01mm². An exact copy without its project/rules changes F.Cu GND by
1.5250980535325mm²; symmetric difference1.5250997953055mm²(API6) /
1.5250997767865mm²(API7), and correctly rejects. The new saved-board test copies
its project/rules. Initial diagnostic runs also corrected `HoleCount(0)` and
the synthetic fit fixture's existing profile. Those incomplete-fixture runs
are not closure evidence. No interpreter migration or tolerance change is used.

Definitive tests use the existing production API10.0.6. No native CLI was
invoked, so no fresh DRC/parity/ERC, full gate or export is claimed here.
No NumPy-dependent path changed. No canonical CAD, generator, model, fab,
firmware, pin/axis, AGENTS§2, Git or other-worker edit was made. No complete-gate
mutant acceptance, owner acceptance or physical/electrical/thermal/flight
qualification is inferred. The original findings remain prospective local gaps.

The companion [JSON receipt](round15_gate_fix.json) preserves source hashes,
exact version/geometry controls, native outcomes, log hashes and limitations.
Ignored reproduction scripts/logs are in `.supervisor/r15_gate_fix_probes/`.
