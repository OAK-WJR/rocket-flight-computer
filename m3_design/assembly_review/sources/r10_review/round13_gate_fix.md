# Round13 gate fixes

The three prospective Minor checker gaps are implemented and frozen for root integration. Root released the canonical freeze after all10 full R13 handoffs; all six owned files matched their prepared original hashes before application.

PCB before/after remains `7355ae1aeb1fdfdf6f64317945a0bf114d94c2bb65fb04adfbcd5a2b8037b09c`. The original `round13_gate.md/.json` reports are unchanged. This receipt validates the scoped code fixes; it is not a new full review round.

| Finding | Implemented behavior | Actual original seed/control |
|---|---|---|
| R13-GATE-01 | Known MPN/LCSC aliases must agree; canonical identity fields remain required | Extra R134 MPN20R0 versus canonical2R00 now produces one metadata conflict; actual board has zero conflicts |
| R13-GATE-02 | Each assembly designator belongs to one row; within-row distinct Qty/CPL semantics preserved | Duplicate R134 now fails S-4 at BOM line84, first seen line60; genuine199-part BOM passes |
| R13-GATE-03 | Flash aperture geometry matches native expected paste polygons | Original1µm-square D28 seed now fails all10 affected pads; current245 top/373 bottom apertures all match |

Changed files are `quality_audit/audit_artifacts.py`, `quality_audit/test_quality_tools.py`, `tools/check_r10.py`, `tools/test_r10_check.py`, `tools/paste_check.py` and `tools/test_paste_check.py`. The R10 checker/test edits touch only assembly row semantics and their regression. Before/after source hashes are in [round13_gate_fix.json](round13_gate_fix.json).

Executed on applied canonical code:

- Quality suite22 tests, R10 Assembly9 tests and paste11 tests: all pass.
- Native original three fault artifacts reject directly; corresponding actual board/BOM/package controls pass. Exact issues and evidence are in the JSON.
- During ignored preparation, new regression cases failed against the unchanged original code and passed against the prepared code. Preparation/full-suite logs are hash-bound in the receipt.

Paste parity preserves reviewed native margins, maker split-EP windows, current custom-pad deflation and explicit native dry/manual-process patterns. It uses1µm position/boundary comparison and100nm curve polygon approximation; custom shapes use the board's native plot polygonization before margin application (current5µm). It supports C/R/O and macro primitives1/4/20 with exposure/arithmetic/rotation; unsupported aperture/image operations fail closed. Tests cover under/oversize, same-area wrong shape, equivalent macros, clear cutouts, margins, rotated rounded pads, the TI split-window pattern and explicit dry lands. No universal copper-coverage percentage, solder-volume claim, stencil/process threshold or reference-name exemption is added.

The implementation follows [KiCad10.0.7 plotPadLayer](https://raw.githubusercontent.com/KiCad/kicad-source-mirror/10.0.7/pcbnew/plot_board_layers.cpp) and [Ucamco Gerber §§4.4–4.5](https://www.ucamco.com/files/downloads/file_en/456/gerber-layer-format-specification-revision-2024-05_en.pdf). The current [TI DSK0010A](https://www.ti.com/lit/ds/symlink/tps7a91.pdf) split-window pattern remains valid; geometry parity does not qualify solder deposition or the manual C84 process.

The current data were correct before these changes. Their broader unchanged manifest/native-budget bindings caught altered artifacts as recorded in the original review. Direct local rejection is now added; no whole-gate escape is claimed.

No native CLI, full build/check, fabrication regeneration, canonical CAD save, GUI, git mutation or other-worktree edit was performed by this slice. Root owns integrated checks/binding/docs. No firmware, electrical/physical/process/flight qualification follows; AGENTS section2 and existing limits are unchanged.
