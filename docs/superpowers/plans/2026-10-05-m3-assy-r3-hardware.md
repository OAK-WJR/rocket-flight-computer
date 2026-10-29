# M3-ASSY-R3 Hardware Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the R2 KiCad project into M3-ASSY-R3: GNSS removed, 46 × 193 mm outline, cost-down BOM, all gates green, fab package regenerated.

**Architecture:** Every board edit is done by one committed, re-runnable script (`m3_design/r3_cut.py`, pcbnew API) plus three small schematic edits, so the change is reviewable and reproducible. Only deletions, the outline, two hole circles, two silkscreen strings, zone outlines and zone refills change; no verified track or via is re-routed.

**Tech Stack:** KiCad 10.0.6 (`kicad-cli`, pcbnew Python at `/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3`), Python 3, JLC parts API via curl.

**Spec:** `docs/superpowers/specs/2026-10-05-m3-assy-r3-design.md`

## Global Constraints

- Branch `m3-assy-r3`; one PR to `main`; never push to `main` (AGENTS.md §4).
- `tools/check.sh` must report `DRC violations 0  unconnected 0  schematic parity 0  ERC 0` and `metadata / 3D model audit: OK` before every commit.
- No copper outside the GNSS nets, the U6 3V3A branch and GND stitching beyond y = 186.2 is changed.
- Board outline 46.0 × 193.0 mm; forward M3 holes at (4,189) and (42,189), Edge.Cuts circles r = 1.6.
- BOM swaps only same-footprint, equal-or-better spec; protected parts never change (spec §2).
- Inferences are labelled INFERENCE in every document (AGENTS.md safety rule 5).
- Research evidence for this plan: scratchpad reports `pcb-cut.md`, `repo-refs.md`, `bom-costdown.md`, `jlc-fees.md` (summarised in `docs/M3_R3.md`, Task 6).

---

### Task 1: Schematic — remove GNSS, flag PC6/PC7, revision R3

**Files:**
- Modify: `m3_design/assembly_review/diagnostics.kicad_sch` (delete U6 L760–806, its wiring L807–1035, C33 L1036–1113, C34 L1114–1191, note L1890–1896, cached `M3:GNSS` lib symbol L119–359; title L7 → `04 | Voltage diagnosis and indicators`)
- Modify: `m3_design/assembly_review/mcu.kicad_sch:2202-2233` (delete GPS_TX/GPS_RX wires + labels on U1 pins 63/64; add two `no_connect` at (63.5,140.97) and (63.5,143.51))
- Modify: `m3_design/assembly_review/m3.kicad_sch:2703` (Sheetname of sheet 04)
- Modify: all 14 `*.kicad_sch` title blocks: `(rev "M3-ASSY-R1")`/`(rev "M3-ASSY-R2")` → `(rev "M3-ASSY-R3")`

- [x] **Step 1: Apply the edits** (done in commit `2b37048`; the diff contains only the listed deletions, the two `no_connect` items, the sheet title and the revision fields).
- [ ] **Step 2: Run ERC.**
  Run: `kicad-cli sch erc --severity-all --format json -o /tmp/erc.json m3_design/assembly_review/m3.kicad_sch && python3 -c "import json;d=json.load(open('/tmp/erc.json'));print(sum(len(s['violations']) for s in d['sheets']))"`
  Expected: `0`
- [ ] **Step 3:** Do not commit yet (parity fails until Task 2).

### Task 2: PCB cut script and board edit

**Files:**
- Create: `m3_design/r3_cut.py`
- Modify: `m3_design/assembly_review/m3.kicad_pcb`

**Interfaces:**
- Produces: `python3-kicad m3_design/r3_cut.py <board.kicad_pcb>` — idempotent: running on an R3 board changes nothing and prints `already R3`.

- [x] **Step 1: Write `m3_design/r3_cut.py`** (committed). Derived from the research recipe, mode B (keep the 12 forward-strip GND vias that are ≥ 3.5 mm + 0.3 mm from the new hole centres and below y = 192), plus:
  - an idempotence guard: if no footprint U6 exists and the board's max Edge.Cuts y is 193.0, print `already R3` and exit 0;
  - silkscreen: replace text `M3-ASSY-R2 - DATA` → `M3-ASSY-R3 - DATA` and `2S INPUT / M3-ASSY-R2` → `2S INPUT / M3-ASSY-R3`;
  - a final self-check that asserts: no footprint at y > 186.2; no track/via net `GPS_TX`/`GPS_RX`; the Edge.Cuts segment endpoints are exactly (0,0),(46,0),(46,193),(0,193) (not `GetBoardEdgesBoundingBox`, which includes line width and returns 193.1); the 8 M3 hole centres are exactly {(4,4),(42,4),(4,88),(42,88),(4,128),(42,128),(4,189),(42,189)}.
- [ ] **Step 2: Run it.**
  Run: `/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 m3_design/r3_cut.py m3_design/assembly_review/m3.kicad_pcb 2>/dev/null`
  Expected: counts `fp 3, gps_trk 109, gps_via 4, 3v3a_branch 15, gnd_via ~99, silk_dot 3, zone 1`, `moved hole to 4.0 189.0`, `moved hole to 42.0 189.0`, `saved`, `self-check OK`.
- [ ] **Step 3: Run it again** — Expected: `already R3`.
- [ ] **Step 4: Gate.** Run: `bash tools/check.sh` — Expected: all zeros and audit OK.
- [ ] **Step 5: Safety contract.** Run: `python3 m3_design/check_actuators.py` — Expected: `actuator safety contract: OK`.
- [ ] **Step 6: Regenerate netlist and renders.**
  Run: `kicad-cli sch export netlist --format kicadxml -o m3_design/assembly_review/schematic.net.xml m3_design/assembly_review/m3.kicad_sch` and
  `kicad-cli pcb render --side top -o m3_design/assembly_review/top.png m3_design/assembly_review/m3.kicad_pcb` and `--side bottom -o .../bottom.png`.
- [ ] **Step 7: Commit.**
```bash
git add m3_design/r3_cut.py m3_design/assembly_review/*.kicad_sch m3_design/assembly_review/m3.kicad_pcb m3_design/assembly_review/schematic.net.xml m3_design/assembly_review/top.png m3_design/assembly_review/bottom.png
git commit -m "M3-ASSY-R3: remove GNSS, cut board to 46 x 193 mm"
```

### Task 3: BOM cost-down swaps

**Files:**
- Modify: schematic LCSC / Manufacturer / Manufacturer Part fields of C71, C74, C83, C90, C93, C128, C140 (`camera_power`, `logic_power_path`, `camera_uart`, `pyro` sheets) and R74, R77, R100, R101, R103 (`camera_power`, `camera_uart`)
- Modify: `m3_design/procurement_catalog.json` (entries for C1591 and C22548)

| Refs | From | To | Evidence |
|---|---|---|---|
| ~~C71 … C140~~ | C1591 100 nF 50 V X7R | not swapped | C128/C140 are on PYRO_OUT in the simulated actuator band and no DC-bias curve exists for C14663; leaving them on C1591 keeps the line Extended, so the swap saves nothing |
| R74 R77 R100 R101 R103 | C22548 Yageo RC0603FR-071KL 1 k 1 % 0603 (Extended) | **C21190 UNI-ROYAL 0603WAF1001T5E** 1 k 1 % 100 ppm 0603 (Basic) | LCSC C21190 page |

- [x] **Step 1:** Edit the 5 resistors' LCSC, LCSC Part, Manufacturer and Manufacturer Part fields in the schematic **and in the PCB footprints** (export_fab reads the PCB fields; kicad-cli has no headless update-PCB), keeping `Value` unchanged. Done in `46039a7`.
- [ ] **Step 2:** Update both procurement catalog entries.
- [ ] **Step 3:** Update PCB from schematic (fields only): re-run `tools/check.sh` (parity must stay 0) and `cd quality_audit && python3 -m unittest test_quality_tools`.
- [ ] **Step 4: Commit** `M3-ASSY-R3: move two passive lines to JLC Basic`.

### Task 4: Fab package, stock, cost

**Files:**
- Modify (generated): `m3_design/assembly_review/fab/m3_bom_jlc.csv`, `fab/m3_cpl_jlc.csv`, `fab/stock_check.json`, `fab/cost_check.json`, `tools/jlc_corrections.json`, `tools/jlc_easyeda/pads.json` (add C14663, C21190 pad data)
- Create: `tools/jlc_cost.py` (already drafted)

- [ ] **Step 1:** Fetch EasyEDA pad data for C14663 and C21190 into `tools/jlc_easyeda/pads.json` the same way the existing entries were produced, then run `KiCad-python tools/jlc_orient.py tools/jlc_easyeda/pads.json` — Expected: `CHECK: none`.
- [ ] **Step 2:** Run `python3 tools/export_fab.py` — Expected: `parts without LCSC code: none`, `CPL rows without a verified JLC orientation correction: none`, 75 BOM lines.
- [ ] **Step 3:** Run `python3 tools/jlc_stock.py --boards 5` — Expected short list: only `C22459454 U4` (JLC stock 0 on 2026-10-05; protected, so it is sourced via JLC Global Sourcing/consignment, documented in ORDERING.md).
- [x] **Step 4:** Run `python3 tools/jlc_cost.py` (defaults: parts ≤ $56, ≤ 48 unique extended codes; counts codes, not CSV rows) — met: $54.94, 48 codes.
- [ ] **Step 5: Commit** `M3-ASSY-R3: regenerate fab package, add JLC cost gate`.

### Task 5: Library and data cleanup — dropped

**Files:**
- Delete: `m3_design/assembly_review/kilib/rocket.pretty/LCC-20_L15.5-W15.5-P1.90_SAM-M10Q-00B.kicad_mod`, `kilib/rocket.3dshapes/M3_SAM_M10Q_ENVELOPE.wrl` (unused after Task 2)
- Modify: `m3_design/assembly_review/bom_review.json`, `verification_assembly.json` (mark as R1/R2 history, not R3 evidence)

Not done: `kilib/core.kicad_sym` and `kilib/m3.kicad_sym` still name this footprint as the GNSS symbol's default, so deleting it would leave a dangling library reference for no gain.

### Task 6: Documentation and pin map

**Files:**
- Create: `docs/M3_R3.md` (design record: what changed and why, cut geometry and margins — J3 washer clearance 1.075 mm, minimum legal length 191.925 mm —, GNSS removal list, BOM swaps with evidence, cost result vs targets with the JLC fee table, U4 stock, bay cross-section: battery no longer under the board, coupler bore Ø50.8 to joint + 120, servo header 72.9 mm from aft edge)
- Modify: `STATUS.md`, `AGENTS.md` §1 table, `README.md`, `docs/ORDERING.md` (size 46 × 193, U4 Global Sourcing instead of U6, cost numbers)

- [ ] **Step 1:** Write/modify the files.
- [ ] **Step 2:** `bash tools/check.sh` — all zero.
- [ ] **Step 3: Commit** `M3-ASSY-R3: design record, status, ordering guide`.
- [ ] **Step 4:** Open the PR with the `tools/check.sh` output in the description (AGENTS.md §3).

## Not verifiable in this work (report separately)
- `m3_design/sim_r2/run.py` needs ngspice (not installed). The actuator band is unchanged, so the committed results still describe it; re-run when ngspice is available.
- No physical board is built.
