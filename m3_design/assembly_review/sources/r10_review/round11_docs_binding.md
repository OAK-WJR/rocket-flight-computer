# Round 11 — documentation and firmware binding

Target: commit `21bc3b2`, PCB `0c50b9fd0930f34edab7129fc21b8e71d0ee03bc079e1900b7e131cece6bfaf8`.

**Result: 0 Critical, 0 Major, 2 Minor groups.** Read-only canonical-source audit; only this report and its JSON were written. No other round-11 report, other worktree, Git action, CLI/build/gate or supervisor request was used. The root owns the fresh baseline check. The two builds in `ava_layout_validation.json` remain historical build evidence; this review does not relabel their result as a new gate.

## Findings

### R11-DOC-01 — Minor: fire calculation uses older copper after the AVA reroute

`m3_design/r10_parts.py:333–337` hardcodes the AUD/GAP lengths into the current `parts_budget.json:275`. `docs/M3_R10.md:146` and `docs/REQUIREMENTS.md:58` present the resulting circuit current numbers as current.

| Fire conductor | Stored length (mm) | Native routed centreline (mm) |
|---|---:|---:|
| BAT_IN J1.1 → Q120 drain | 7.121320 | 6.707107 |
| RAW_ACT Q121.8 → R134.2 | 6.500000 | 5.886133 |
| PYRO1_IGN J121.2 → R134.1 | 4.850000 | 10.396068 |
| PYRO1_OUT J121.1 → Q124.5 | 7.954478 | 7.954478 |

Native IGN is B.Cu 0.5 mm, (7,57.6) → (7,59) → (12,64) → (13.925,64). Native RAW_ACT is B.Cu 0.5 mm, (14.475,67.105) → (17.58,64) → (19.075,64).

**Convention:** BAT_IN's full routed centreline includes the 0.707107 mm segment from (13,74.1) to the Q120 drain anchor (13.5,73.6), inside the common drain polygon. The external conductor alone is 6.0 mm, as the root independently noted. Either convention differs from the stored length. Retaining the existing conservative single aligned 2.2 mm / 0.4 mm source-leg model and all other assumptions gives hot copper **35.679767 mΩ**, versus stored **30.123110 mΩ**, and loop **4.618006 Ω**, versus **4.612449 Ω**. The same coupled calculation gives **1.544183 A idle / 1.282861 A four stalls**, still above the selected **1.125 A** criterion. These are Calc / Inference, not physical resistance/current qualification. This is stale evidence, not a demonstrated F7 failure.

Fix: extract/bind the final native paths with an explicit pad-entry convention, regenerate the budget, and refresh active current/resistance prose. Preserve old values under a named historical board. Source: native PCB and `r10_route_pyro.py`; maker page is not applicable to the geometry mismatch.

### R11-DOC-02 — Minor: active R10 narrative still describes old connectors and an unfinished AVA pass

`docs/M3_R10.md:120–127` still says the radio is west, switch/servos forward, and a separate AVA pass “will arrange” the rows. Its unqualified retention table at **374–381** still calls J122 a 12-pin 3×4 header with two tie holes, J9/J410/J420 GH-4, and J400 GH-2, with J400 not staked. The panel paragraph at **384** still calls the row GH. The current source is seven DB125 bodies: J122 is 5-position at **(39,71.5)**, J400 is 2-position at **(7,65.85)**, J420 is east **(39,31.5)**; no servo tie holes remain. REQUIREMENTS P3 explicitly stakes all DB125 bodies. `docs/ORDERING.md:219–225` correctly supersedes the old hardware but still describes the AVA pass as future.

The current top banners and AVA hand-off are correct, and ORDERING's older §8 snapshots are explicitly historical. Those snapshots are not counted as fresh hardware failures. The active prose/table nevertheless contradict the current board and retention requirement.

Fix: update the active placement/retention/process narrative and ordering stage, or move obsolete paragraphs under an explicit historical baseline. Keep the old measurements as history. Source: native PCB, `AVA_LAYOUT.md`, D-AVA-01 and REQUIREMENTS P3; maker page is not applicable.

## Tested coverage

- **100/100 U1 pins:** exact equality across native PCB, schematic XML, reviewed table and generated binding; zero mismatches. Checked the assigned GPIO/AF/ADC/EXTI obligations for consistency; this does not claim a new maker-level AF review.
- **4/4 binding hashes:** PCB, netlist, pin table and circuit agree. In-memory `r10_sch_check.binding_note(project, board)` equals the saved JSON exactly.
- **IMU:** native U4 B180 at **(17,45.9)** matches the binding; roll **−gyro_Y**, forward thrust **−a_Y**, x lever **−6 mm**. z **−2.06 mm** stays explicitly inferred; bench sign check remains required. No new physical axis qualification is claimed.
- **23/23 recorded generated-file hashes** and **5/5 fabrication-output hashes** match their recorded current-board manifests. Native totals exactly match AVA: **209 footprints / 981 segments / 294 vias / 1818.769511 mm**, **166 GND vias**, **122 shown / 87 hidden references**. CPL has **199 rows, 67 top / 132 bottom**; AVA's **66 top / 121 bottom** are the 187 reconstructed rows plus 12 placement-only rows, not a count conflict. BOM has **82 codes**.
- **R1 fail-closed chain:** inspected `build.py`, assembly/status/GNSS/USB/UART binding modules and retained proof. The assembly proof targets **e432d343…**, not R10; its check modules are absent from this tree. The builder also requires protocol/profile/exact-board identity before artifact creation. All **25** retained build binding JSONs target older profiles; **0** match the R10 SHA. No builder was executed. R8/R9 evidence notes retain their explicitly historical cc044ea0… / 4f841a0e… hashes; neither is promoted to R10 firmware.
- Read the review packet/read-first records and chronological owner amendments: O1–O6, OQ1–OQ7, single switch, AUD/GAP, always-on ports, microSD, all wired screw terminals, audit 2 and D-AVA-01/02. Checked their current precedence against native connector/pin facts and firmware obligations. Adopted architecture and pending physical/firmware/process qualification are not reclassified as new Majors.
- Checked passive cold screen before PC1 enable; ≥1 s verified discharge / ≥100 ms settle; PC1/PE4 low and dual lock/readback; 20 ms normal / 36 ms fault physical-current contracts; launch and ground/in-flight sense policy; neutral-first 50 ms target; PA6 shedding and always-on ports; ADC/EXTI mapping; PA15/LSE/trace; bounded QSPI/SD/UART handling; dark-in-flight LEDs.

## Scope and retained limits

The **parent `../../docs/VEHICLE.md:39` is still stale** (ARM terminal, GH ports/GH2, old switch pose). This is already acknowledged in M3_R10's open items, not a new finding; it needs a separately authorized parent-repository update. Read only; not edited.

Current top-level docs correctly state R9 remains accepted, R10 is not accepted or ordered, old rounds 9/10 cover b337fe63… only, and fresh review begins at 11. The old acceptance inventory is explicitly superseded and awaits a new board-bound list after these rounds. Cost/stock evidence is dated preliminary carry-forward; no fresh supplier quote is asserted.

No new DRC, build/reproducibility execution, maker electrical verification, firmware implementation/execution, bench measurement, electrical/thermal/EMC, coating, e-match lot, SD behavior, harness, retention or physical fit is claimed. Full details and native measurements are in `round11_docs_binding.json`.

