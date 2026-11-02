# Round 27 fix pass: CAD lane (generators, generated text, checks)

## Scope

- **Brief:** `.supervisor/r27_fix_brief.md` items 1-4, on `round27_triage.md` / `.json`. In this lane: R27-TRI-02's
  generator part, R27-TRI-04, R27-TRI-07 and the records.
- **Base:** `816038c`, board `a0ec075e…`.
- **Records:** D-R27-01 … D-R27-03 in `sources/r10_design/R10_DECISIONS.md` (record index 223 through D-R27-03). No
  older decision line became false: R19-MCU-02 already labels the two Rev 11 limits, and no decision names the ports'
  symbol or the four-stall loaded-pack figures.

Changes went through the generators and their input (`circuit.json`) only; nothing in the CAD was hand-edited.
- AGENTS section 2 holds, and every existing check is unchanged or stricter (one new schematic check with four seeds).
- No git state was changed.
- STATUS.md, AGENTS.md, docs/*.md, parts_qualification.md, AVA_LAYOUT.md and other review records were not touched.
  They carry the docs lane's uncommitted edits.

## Board

- **PCB SHA-256 after the build:** `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c`, **unchanged**.
  - One complete `m3_design/r10_build.sh` (1672 s, exit 0) reproduced it, so no second build was needed.
  - The board takes nets, values, footprints and fields from the netlist, and none of them changed. The PCB carries no
    pin names.
- **Fab outputs:** only their creation dates changed, in the Gerber zip (14 files) and the two assembly PDFs.
  - BOM, owner BOM, CPL and paste (249 / 381) are byte-identical, so the supplier evidence still binds them
    (`cost_check.json` / `stock_check.json` unchanged). The build's own `r10_fab.sh` re-exported the package; no
    networked run was needed.
  - The manifest re-binds two changed inputs: `telemetry.kicad_sch` and `kilib/m3.kicad_sym`.
- **Hot-plug model:** inputs and results byte-identical. 2304 cases, 0 failures; minimum -14.807 V (limit -15.0),
  steepest fall 8.995 V/us (limit 10), steepest rise 5.088 V/us (limit 100).

## Items

| # | Item | Result | Before -> after | Files |
|---|---|---|---|---|
| 1 | R27-TRI-02, generator part | done (D-R27-01) | `loaded_pack` power 5.456 V x 1.46 A -> 5.456 V x (1.46 A + aux_A). `parts_budget.json` lines 91-92: 5.899 / 4.414 V -> 5.881 / 4.389 V. | `m3_design/r10_parts.py`, `tools/check_r10.py` (comment); regenerated `parts_budget.json` |
| 2 | R27-TRI-04 | done (D-R27-02) | The binding note's `mcu_revision` now names the two labelled Rev 11 Table 109 limits as exceptions, in the triage's words. | `m3_design/r10_sch_check.py`, `tools/test_r10_check.py`; regenerated `r10_binding_note.json` |
| 3 | R27-TRI-07 | done (D-R27-03) | J410 / J420 / J440: M3:CameraTerminal (5V OUT / GND / RX FROM CAMERA TX / TX TO CAMERA RX) -> M3:PortTerminal (4V8 / GND / TXO / RXI). J9 unchanged. | `m3_design/r10_parts.py`, `m3_design/r10_sch.py`, `sources/r10_design/circuit.json`, `m3_design/r10_sch_check.py`, `tools/test_r10_check.py`; regenerated `telemetry.kicad_sch`, `kilib/m3.kicad_sym`, `schematic.net.xml` |
| 4 | records | done | D-R27-01 … -03 | `R10_DECISIONS.md` |

### Item 1 (R27-TRI-02, generator part)

- **`parts_budget.json`:** SHA-256 `5204280e…` -> `ecc45417a4b9ec6ad021f52153cf2f59b547ac8e1afbd39dbd7d6e4c39f9a8bb`.
  - Line 91: `"pack_7V4_four_stall_loaded_V": 5.881013614959047` (was 5.899191137113537).
  - Line 92: `"pack_6V0_four_stall_loaded_V": 4.388744837110238` (was 4.414001778867496).
  - Both match the triage's 5.881 / 4.389 V. They are the file's only change; the fire budget (5.713 V four-stall,
    1.279 A) already used `ports_w`.
- **Budget SHA binders:** none in code. `r10_parts.py --check` in check.sh regenerates and compares the budget, and the
  hot-plug inputs and the binding note do not carry its hash. The docs quote it (below).
- **Sweep for the pre-AUX allocation** (460 mA, 1.46 A without AUX):
  - In `r10_parts.py`, every other port figure already carries `aux_A`: `ports_w`, the battery-break loads, the
    camera-short buck case, U401's loss and junction estimates. The LDO-short cases are bounded by U401's shared limit,
    which covers all three ports.
  - The sheet notes (`circuit.json`, `r10_sch.py`) and the binding-note obligations quote the 100 mA allowance.
  - `tools/r10_hotplug.py` carries no port current.
  - `tools/check_r10.py`'s K-power comment quoted round 18's pre-AUX "11.5 W normal, about 1.56 A at 7.4 V". It now
    quotes the budget's c_camera_radio_gps_on, 11.25-13.06 W, at most about 1.77 A at 7.4 V. This is a comment only;
    the rule's 2.9 A design current is D-R3-03's.

### Item 2 (R27-TRI-04)

- **Binding note:** `sources.mcu_revision` reads "…(section 7; the LCSC copy is byte-identical), except the two design
  limits labelled as read from Rev 11 Table 109 in round 14 (the 6.0 V FT cap and the 4.0 V ADC-mode maximum;
  R5-MCU-04 obligation, Inference); Rev 11 and RM0433 were not re-read in round 19 (R19-MCU-02)".
- **Hashes:** binding note SHA-256 `b2112fb3…` -> `e8f10fb3ef1c4bd8428035dc17a08accde8b69675f1449bbc30c037b6cf37a3b`.
  This also carries item 3's netlist and circuit hashes. K-binding passes.
- **Pinned in `test_r23_binding_note_rules_and_pin_table`:**
  - the new words;
  - the old "byte-identical); Rev 11" rejected;
  - the obligation's "were read from Rev 11 Table 109 in round 14" still present.

### Item 3 (R27-TRI-07)

- **Symbol:** `r10_parts.port_terminal_symbol()` defines M3:PortTerminal.
  - It is a box with pins 1 4V8, 2 GND, 3 TXO and 4 RXI, all passive like CameraTerminal's, filtered to M3_DB125_4P_GN.
  - `r10_sch.py` adds it to `kilib/m3.kicad_sym`, asserts that a copy already there equals the generator's, and
    refreshes embedded copies.
- **`circuit.json`:** J410, J420 and J440 take `M3:PortTerminal`; J9 keeps `M3:CameraTerminal`.
- **`schematic.net.xml`:** SHA-256 `762bc13d…` -> `535a8fdfe96c3a771a901db2bb9d2cd1a6674b001dfe1e18aa7d600e3aea7e9a`.
  - The three ports' pin functions read 4V8_1 / GND_2 / TXO_3 / RXI_4.
  - Their libsource and libpart are PortTerminal.
  - Nets, values, footprints and fields are unchanged.
- **Sheets:** `telemetry.kicad_sch` (`6e310ef4…` -> `695cfa0d…`) changes the three lib_ids and their pin leads; the box
  is narrower. The other 14 sheets are byte-identical.
- **Other hashes:** `kilib/m3.kicad_sym` `979cf095…` -> `7a3c7d8d…`; `circuit.json` `aeb1674f…` -> `3220e5f9…`.
- **Schematic results:** ERC 0, schematic parity 0, DRC 0.
- **New check in `r10_sch_check.py`:**
  - The three ports must carry F10's names (the board legends) and J9 the camera terminal's, in both the checked
    netlist and the fresh export.
  - Four seeds run in memory: the camera names on a port, TXO / RXI swapped, a port supply named 5V OUT, and the port
    names on J9. All four are caught.
  - Run on round 27's netlist, the check fails once for each of J410, J420 and J440.
- **Seed:** `test_r10_check.SchematicContract.test_r27_port_terminal_pin_names`.
  - The board's netlist passes.
  - The names equal check_r10's TERMINAL_PINS_R10 legends and `r10_parts.PORT_TERMINAL_PINS`.
  - `circuit.json` assigns the symbols.
  - The camera names put back fail three times, and the four seeds are each caught.

## Checks and tests

- **Build:** one complete `m3_design/r10_build.sh` (KiCad CLI 10.0.7, `NUMPY_PY=.supervisor/venv/bin/python`), exit 0.
  - r10_sch_check OK (43 seeds caught: 39 contract, 4 name);
  - every stage check;
  - DRC 0, unconnected 0, parity 0, ERC 0;
  - check_r10 37 / 37 OK;
  - route_check 0 failing, 0 allowlisted, 5 unrecorded noncritical leftovers as before;
  - the fab content checks and the manifest;
  - K-binding.

  The build ends with `tools/check.sh`, which exited 0. Only `R10_DECISIONS.md` changed after the build (records; no
  gate reads it).
- **Tests:**
  - All OK: shell 11, procurement OK, fab validation 34, fit 33, paste 16, R10 parts 5, route 72, R10 268 (was 267;
    6 numpy skips), numpy hot-plug / plate 6.
  - Added: `test_r27_port_terminal_pin_names`.
  - Extended: `test_r23_binding_note_rules_and_pin_table`.
- **Not run:** no physical test. The pack-sag figures are calculations.

## Residual grep hits

- **Swept:** every tracked text file outside the docs-lane files, for each replaced value, phrase or name:
  - `5.456 * 1.46`, `5.899`, `4.414`, `11.5 W`, `1.56 A at 7.4`;
  - `byte-identical); Rev 11`;
  - `M3:CameraTerminal`, the camera pin names (both spellings);
  - the old hashes `5204280e`, `762bc13d`, `aeb1674f` and `b2112fb3`.
- **Current statements:** all fixed. `5.456 * 1.46` has no hit.
- **Deliberate:**
  - J9's CameraTerminal names in `camera_connector.kicad_sch`, `kilib/m3.kicad_sym` and `schematic.net.xml`, and J9's
    `circuit.json` entry (correct for the camera);
  - `r10_sch_check.CAMERA_PIN_NAMES` and its seeds;
  - the comments in `r10_parts.py` and `check_r10.py` that name what they replace;
  - the test's rejected "byte-identical); Rev 11".
- **History:**
  - the D-R27 records' own before figures;
  - `round18_gate.json` (11.5 W);
  - round 25 / 26 review records (the old netlist, circuit and budget hashes);
  - the hash-pinned R9 inputs (`r9_input/`);
  - `r6_sch.py`;
  - the R1 reference board's "5V OUT" text.
- **Coincidences:** `5.899` / `4.414` inside other numbers (the hot-plug results and capacitors, round 11's routing
  JSON, R8 evidence, PCB fill coordinates).
- **Not swept:** the docs-lane files (theirs).

## For the docs lane

- **`parts_budget.json`:**
  - SHA-256 `5204280e…` -> `ecc45417a4b9ec6ad021f52153cf2f59b547ac8e1afbd39dbd7d6e4c39f9a8bb` (parts_qualification
    line 475 quotes the old one).
  - Four-stall loaded pack 5.899 / 4.414 V -> 5.881 / 4.389 V (5.881014 / 4.388745 V), from a 7.4 / 6.0 V open pack at
    1.56 A of ports (the stall-input paragraph).
- **Binding note:** SHA-256 `b2112fb3…` -> `e8f10fb3…`, with the `mcu_revision` wording above.
- **`schematic.net.xml`:** `762bc13d…` -> `535a8fdf…`.
- **`circuit.json`:** `aeb1674f…` -> `3220e5f9…`.
- **Port symbol:** J410 / J420 / J440 use M3:PortTerminal (pins 4V8 / GND / TXO / RXI). J9 keeps M3:CameraTerminal.
- **Unchanged:** the PCB `a0ec075e…`, BOM, CPL, paste, supplier evidence ($85.26, U4 / U9 short) and hot-plug results.
