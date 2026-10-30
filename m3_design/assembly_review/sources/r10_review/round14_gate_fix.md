**Round14 gate fix — R14-GATE-01**

Implemented and focused-tested; canonical integration remains root-owned. Base reviewed commit `f5e4a5a94013514edb952fd328325341b63a98df`. PCB SHA-256 before/after: `e0e3ad841654128792b32ab778ca19e4a71e596fa89864074ec4e91e6a5ccfc6`. Native CAD, fabrication ZIP and both original round14 gate reports remain byte-identical.

`tools/paste_check.py` now validates an explicit native command subset before comparing paste. It accepts one mm/absolute4.6 header pair, native dark polarity/aperture macros/attributes and a terminal M02. It rejects non-default legacy IR/MI/OF/SF, unsupported unit/notation/stop changes, unknown commands and data after M02. Neutral legacy values use exact decimal equality. ASAXBY/IPPOS are accepted; non-default AS/IP are rejected by project policy. G71/G90/M01 and IN/LN/G04 metadata remain valid. Modern-transform rejection,1um geometry comparison, margins, split EP windows and dry/manual policy remain; no stencil-coverage rule is added. Command boundaries replace line-based parsing, and deleting an unrelated named attribute no longer clears the component name.

The [official Ucamco2026.05 specification](https://www.ucamco.com/files/downloads/file_en/554/gerber-layer-format-specification-revision-2026-05_en.pdf), pp186–195, permits readers to ignore several legacy controls. This fix makes the project's accepted subset explicit; it does not claim that rejection is universally required, that old CAM output necessarily moved, or that the earlier mutant escaped the whole gate.

Fresh focused evidence ([JSON receipt](round14_gate_fix.json)):

| Check | Result |
|---|---|
| Existing paste tests plus5 new cases |16 tests pass,0 skips; geometry/margins/macros/split-EP/manual controls preserved |
| Actual native ZIP, old versus new checker |32 copied-ZIP cases:16 intended controls pass and16 unsupported cases reject under new policy |
| Original `%OFA1.0B0*%` fault in actual repacked native ZIP |Exact old source accepts245/373 flashes and618geometry matches; patched checker rejects the OF command |
| Current native package |Native-Python entrypoint exit0; all245 top+373 bottom geometries match |
| Actual fault package entrypoint |Exit1, one explicit unsupported-OF finding |
| Compact actual native export |All618 geometries still match |
| Protected files |PCB/fab ZIP/original round14 MD+JSON hashes unchanged |

The receipt records source hashes before/after, each actual copied-ZIP result, exact old-code proof and log hashes. Reproduction files are ignored under `.supervisor/r14_gate_fix/`; temporary per-case ZIPs are removed automatically. No full canonical build/check, KiCad CLI, git action, GUI or physical qualification was performed. Root must integrate/build/check and refresh records before fresh full15/16 reviews. No acceptance or order follows. Edits stop at this handoff.
