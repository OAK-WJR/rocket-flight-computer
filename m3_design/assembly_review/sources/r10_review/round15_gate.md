# Round15 lens9: gate adversary

Target commit `789f4d516251991bdf1518254d537ff7b41f65bb`; PCB SHA-256
`7866d6b895573eb10c14d0227ee4bdde8b4fba6145529786cd554cdb80121783`,2,257,812bytes.
The PCB hash is identical before and after. **0 Critical /0 Major /3 Minor.**
All three are prospective detector gaps; the current native board/package has
no demonstrated instance. No complete-gate mutant acceptance is claimed.

This is a fresh complete assigned-lens review. AGENTS, requirements, all116
D IDs through D-R14-03,22 owner mandates/amendments, AVA/M3/validation and the
vehicle handoff/source were considered with their current amendment scopes.
Historical passes are context, not proof. The root packet identifies the exact
commit; no Git command was used. No peer current-round report/probe was read.

## Active findings

### R15-GATE-01 — Minor,new: production BOM identity is unchecked

`tools/check_r10.py:212` checks Designator/Qty/presence without comparing LCSC,
Manufacturer Part or footprint with the native part. R134 is B(16.5,64),
`CRM2512-FX-2R00ELF/C3013496`,2ohm. Replacing its actual BOM row with the
existing R166 `25121WF360LT4E/C168925`,0.36ohm identity,while retaining Qty1 and
Designator R134,passes genuine S-4 with no issues. The unmodified production
row passes; zero-Qty and duplicate-R134 rows reject.

The original manifest rejects the altered CSV. Calling the real
`fab_manifest.write_manifest` on an ignored package then verifies five hashes;
that function is an integrity binding,not a BOM semantic comparison. Current
native R134 remains correct. This establishes a local population/package
validation gap,not a wrong assembled board or unmodified-full-gate escape.
The family/rating basis is [Bourns CRM2512 p1](https://www.bourns.com/docs/product-datasheets/CRM.pdf);the exact reviewed order identity is the native R134/BOM identity.

Fix: reuse the existing BOM walk to compare every designator's LCSC,canonical
MPN and footprint with its native fitted part,rejecting unexpected or wrong
members while preserving valid merged rows and quantity-free CPL semantics.

### R15-GATE-02 — Minor,new scope: positive shrink remains possible at C84

C84 is F(27.5,78.5). The real allocation is approximately8.5x8.5x10.8mm.
Setting only its native model scale XYZ to0.01 produces0.085x0.085x0.108mm;
fit and P-11 pass,and real native all-severity DRC/unconnected/parity stays0/0/0.
`tools/fit_check.py:180` enforces normalized dimensions only for the named
DB125/SD models. All8 positive0.99999 terminal/SD seeds reject correctly.
The current C84 is full size,and its altered-board native-budget binding rejects.

The [MA supplier sheet](https://atta.szlcsc.com/upload/public/pdf/source/20260306/24758A4FC016E80367B87853635CDCC1.pdf)
p2 gives the8x10 mechanical family;p4 names MA25V470M8X10. The four-page sheet
has no explicit revision seen; inspected cache SHA-256 is
`5ab3c478e90f1826a614a56af8164bb4bab3143affaae1ad7aa69fc0c1981997`.
This is a representation gap extending the closed R12 terminal/SD scope,not a
present physical collision or transferred acceptance failure.

Fix: add the reviewed M3_MA_8x10 normalized envelope to the existing model-box
validation,with C84 shrink rejection and equivalent-unit positive controls.
Keep the present conservative allocation and physical qualification limits.

### R15-GATE-03 — Minor,new: equal-area stale fill passes K-fill

`tools/check_r10.py:2707` compares only zone area after a real native refill.
Translate the saved-only R10_GND_In2_CH1 In2 fill by(+0.1,0)mm,keeping its actual
outline/keepouts unchanged. Original filled bbox is(0.5005,51.3005)–(24,66.099999).
Area remains237.869754823186mm2 exactly; symmetric difference is5.694234392076mm2.
K-fill reports9 zone/layer entries,stale0,tolerance0.01mm2. Explicit r10 K-inner,S-8 and
reference checks also remain clean. The native-budget board binding rejects
the changed PCB. No stale fill is demonstrated on the target.

Fix: compare normalized saved/refilled polygons per zone UUID/layer/net using
symmetric difference or equivalent geometric equality with explicit numerical
tolerance; add same-area translation/reshape negatives and unchanged positives.
This invariant has no maker-datasheet parameter.

## Fresh controls and rejected Critical/Major hypotheses

| Check | Actual result |
|---|---|
| Genuine KiCad10.0.7 all-severity/parity control | DRC0,unconnected0,parity0,no ignored checks |
| All31 current check_r10 rules | Complete,all pass |
| Native metadata/libraries/budget |209footprints,199fitted,no missing/conflicting identities,no stale generated input |
| Fit | Pass;23 tails;minimum tail/bore7.558359mm |
| Production package | Five-output manifest;618paste apertures match native geometry |
| CPL |66top+121bottom independently rebuilt,12placement-only,199expected,errors0 |
| Routing |139information items,8noncritical hygiene leftovers;0blocking/allowed/stale/local-bump findings |
| Native schematic/binding | Contract clean,34contract seeds reject;fresh binding note equals stored note |
| Focused regression suites | Fit30,paste16,routing60,assembly/legend/selection/schematic17;all pass,no skips |

A real0.5mm B.Cu drawing across R134's pads(13.925,64)–(19.075,64)
gets11 native DRC violations and S-1/S-2 rejection: the potential Critical
current-limit bypass does not escape. C126 DNP gets a parity finding and S-4
rejection: topology-only S-3 acceptance is expected. Each of the five actual
retained fire paths rejects a0.25mm seed. C12610nF,R128/R1271Mohm and R12310Mohm
bias faults reject S-3; a contradictory serialized R134 MPN alias rejects
metadata. D04,D09 and post-M02 paste data reject. The three active findings
therefore remain Minor local gaps,not demonstrated Critical/Major hardware or
complete-gate failures. Correctly disclosed R1-bound executable firmware and
pending physical/FW tests are not counted as failed hardware.

Two fixture corrections are retained explicitly: the first CLI width probe
selected a pruned PYRO1_OUT sense branch,so its S-9 pass was correct;all five
actual fire paths were then selected natively and reject. A direct K-inner
helper inherited default r8 classification and produced two false PORT-plane
diagnostics;the explicit r10 rerun is clean. Neither is a finding.

## Scope and evidence

Only ignored own native copies/in-memory/package variants were mutated.
Five genuine CLI DRC calls ran sequentially under the root reservation,which
was then released. No fake CLI,gate skip,canonical build/full check,Git action,
other-worktree edit,subagent or GUI retry was used. No fresh ERC/full exporter,
full173-test suite,whole hot-plug sweep,procurement or reproducibility claim is
made by this lens. No electrical/thermal/transient/endurance,firmware,e-match,
RF/ESD,physical fit/retention or first-article qualification was performed.

The companion `round15_gate.json` embeds findings,closed C/M hypotheses,actual
checks,source/receipt hashes and limitations. Ignored reproducible receipts are
`.supervisor/r15_gate_probes/{native_results,api_results,all31,geometry_matrix_results,fill_recheck,route_control,focused_suites}.json`.
No host-specific absolute path or binary is embedded in either durable report.
