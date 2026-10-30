**Round14 gate adversary — full independent lens9**

Target commit `f5e4a5a94013514edb952fd328325341b63a98df`. PCB SHA-256 before and after: `e0e3ad841654128792b32ab778ca19e4a71e596fa89864074ec4e91e6a5ccfc6`. Native totals:209 footprints,966 segments,296 vias,1802.125220mm track. All22 snapshotted canonical files remain byte-identical; current193-input/five-output fabrication manifest passes.

**0 Critical /0 Major /1 Minor.** The Minor is a new prospective checker-policy gap. No seeded defect is present in the actual package; no whole-gate escape or actual hardware failure is demonstrated. Three prior R13 gate gaps are freshly closed below. AGENTS section2 is unchanged.

**R14-GATE-01 — legacy image controls bypass the advertised closed paste subset (Minor, active/new).** `tools/paste_check.py:148–151,235–264` rejects modern transform operations but silently ignores legacy image controls. In the actual top paste Gerber, insert `%OFA1.0B0*%` immediately after `%MOMM*%`; both direct checking and a repacked actual Gerber ZIP still pass245 top/373 bottom flashes and618 native geometry matches. `%MIA1B0*%`, `%IR90*%` and `%SFA2B1*%` independently survive the same check. U1.1 at(17.0,50.55)mm, native pad0.3x1.6mm, is one of the245 top apertures whose raw coordinates are compared without those command states.

The [official Ucamco2026.05 specification](https://www.ucamco.com/files/downloads/file_en/554/gerber-layer-format-specification-revision-2026-05_en.pdf), pp186–195, permits ignoring several deprecated transforms; p187 identifies non-default rejection as the safer alternative. AS has no computer-to-computer image effect, and the IP overview permits warning/skip. Thus this is an inconsistency with the project's advertised fail-closed subset and an interpretation ambiguity, **not guaranteed CAM displacement** or a standards-mandated rejection. AS/IP acceptance is not counted as another defect. Mixed G70/G91 and M00 probes are robustness observations, not certified valid manufacturing outputs.

Controls: current native files and all neutral/default legacy controls pass; metadata IN/LN/G04 remains valid. Modern LPC/LM/LR/LS rejects. The current paste files contain no legacy image controls. The original manifest accepts the real ZIP and rejects the modified ZIP; reissuing a matching manifest was not tested. **Fix:** explicitly reject non-default legacy transforms and unsupported state changes, or compare their effective image; state AS/IP policy explicitly. Preserve native/neutral/metadata controls, modern rejection and reviewed paste margins/EP windows. No new coverage-percentage rule is justified.

Fresh evidence ([structured report](round14_gate.json)):

| Check actually executed | Result |
|---|---|
| Native R10 contract, actual BOM/CPL supplied | All31 rules pass; native Python10.0.6 |
| Full existing R10 suite |173 tests, exit0;169 execute in KiCad Python,4 NumPy cases resolved separately with supplied interpreter; no unresolved skip |
| Genuine official10.0.7 CLI controls inside that suite | Exact-target baseline and copied J2/TP all-severity/parity DRC seeds pass; reserved sequential CLI use released |
| Fresh target fault seeds |16/16 rejected: pack-fed pyro, real R134/J400 copper bypass, automatic/undefended enable, missing gate pull,99nF gate cap,DNP/excluded safety/IMU parts,sense-value/map changes,GPS resistor bypass,radio clamp-to-gate,servo power contact,wrong SD rail |
| Schematic/source agreement |209 components;34 in-memory source faults reject.651 raw XML nodes=651 unique(ref,pin) electrical keys; native663 numbered physical pads collapse to the same651 keys. All663 individually match, including100 MCU pads; total physical pads682 |
| Binding/electrical evidence | Fresh R10 note exactly equals current note; MCU100/IMU pose/axes agree. Native-bound libraries/power budget current. This is no executable firmware approval |
| Actual assembly |82 BOM rows/199 references match native LCSC,MPN and footprint;66 top+121 bottom source-pad reconstructions plus12 placement-only checks;0 errors |
| Actual paste and existing paste suite |618/618 geometry matches;11 tests pass. Expanded legacy boundary28 cases recorded |
| Fresh routing |140 information instances,0 blocking/allowed/stale;22 AUD-10 review items and8 noncritical leftovers retained for owner review |
| Gate failure propagation | Existing5 synthetic shell-protocol tests pass; their isolated stubs supply no actual-board DRC/check credit |
| Exact native save control | Byte-identical to target; original fabrication manifest still passes |

Closed historical findings: **R13-GATE-01** conflicting R134 MPN now rejects while matching alias passes; **R13-GATE-02** duplicated R134 BOM row and zero/wrong Qty reject while actual BOM passes; **R13-GATE-03** actual D28 aperture reduced0.566x0.540→0.001x0.001mm now rejects all ten affected pad geometries.

Read AGENTS first, both packets, requirements/plan/current decisions, AVA/M3/validation/R9 precedents, vehicle handoff and read-only VEHICLE. All113 decision IDs through D-R13-03 and22 owner mandate/amendment records were considered using current scope; their IDs/source hashes are in JSON. No current-peer R14 report or findings were read. The separately owned VEHICLE remains a stale mirror.

Limits: no build, full actual-board check.sh, GUI, git action, source/CAD change or child agent. The suite's CLI baseline is all-severity/parity; no separate all-track-errors DRC or ERC/schematic re-export/fab regeneration was run. F9-1 freshly extracts and validates stored model evidence, but this lens did not rerun the complete2304-case sweep. No firmware, physical fire/current-tail, thermal/transient/endurance, selected-card behavior, RF/ESD, harness/switch/retention, access/fit, first-article/process, flight or owner acceptance follows. R10 is unaccepted and unordered. Ignored repro scripts are in `.supervisor/r14_gate/`; downloaded primary PDF/full text were removed after hash/page verification.
