# Manufacturing-file consistency audit

Tools that check a KiCad board for problems DRC does not catch, and bind the evidence to the exact input files.

| Script | What it checks |
|---|---|
| `audit_artifacts.py` | Conflicting distributor part-number fields on the same part (e.g. `LCSC` vs `LCSC Part`), missing or unresolved 3D model paths, absolute (non-portable) model paths, footprints without a courtyard |
| `normalize_metadata.py` | Reads a board's part table and reports drift against a generator's intended part table |
| `verify_board.py` | Fresh read-only DRC (all severities + schematic parity) and ERC with SHA-256 hashes of every input (board, schematic sheets, libraries, models); exits non-zero on any unresolved finding |
| `sexpr.py` | Minimal KiCad s-expression reader shared by the scripts |

Usage (also wrapped by `tools/check.sh`):

```sh
python3 quality_audit/verify_board.py m3_design/assembly_review/m3.kicad_pcb --output /tmp/audit.json
python3 -m unittest quality_audit.test_quality_tools
```

A zero exit status covers only the checks listed; it says nothing about electrical, mechanical or flight readiness.

History: the first audit (2026-09-07) of the legacy two-board design found 60 components carrying two contradictory LCSC numbers (footprints imported from EasyEDA carried a baked-in example part number), absolute 3D model paths, and build scripts that hid upstream failures. Those were fixed in the M3 libraries; the current M3-ASSY-R1 board passes this audit with no findings.
