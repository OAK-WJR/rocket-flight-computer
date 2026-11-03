# Round 12 gate fix receipt

The three prospective gate gaps R12-GATE-01…03 are implemented and regression-validated. Four source files are frozen. This agent changed no canonical CAD, model, fabrication output, generator, pin table, decision/status record or Git state. Root has begun the separate integration build; the tests below cover PCB `0ad0135cb9ff1f6ace7ef9d5ba9006b727b293d7b5224bb97dad47859b91238d`, before that build.

- **R12-GATE-01:** `fit_check.model_box` compares the normalized reviewed DB125 maximum and closed-SD envelopes, before footprint placement/flip. All eight models differ from their reviewed bounds by at most **1.49e-6 mm**; six-decimal WRL endpoint quantization bounds error at **1.905e-6 mm**. The guard is **2e-5 mm**. Positive wire-direction scaling **0.99999** and a **3e-5 mm** offset reject. All eight physically equivalent metre-to-mm conversions pass. Generic models retain their existing positive-scale/rigid-transform behavior. No physical margin or generic minimum scale is introduced.
- **R12-GATE-02:** K-inner now uses the existing complete manufactured-copper walk for drawings/text and filled board/footprint zones, alongside the unchanged track check. Pads and vias remain excluded from this new representation walk, preserving legitimate traversal/barrels. Connected native board-zone and board/footprint-drawing regressions reject; the unchanged board's legitimate inner planes/barrels pass. The native filler leaves footprint-owned copper zones empty, so an empty footprint-zone fixture is not credited as a filled-copper regression.
- **R12-GATE-03:** The existing S-4 CSV walk validates positive integer Qty equal to the row's distinct designator count. A production BOM must include Qty; a quantity-free CPL remains valid. Real BOM copies with U1 Qty zero or a missing Qty column reject. No population walk is duplicated.

| Validation actually run | Result |
|---|---|
| Full native fit suite | **29 tests pass**, no skips |
| R10 suite excluding its one reserved CLI method | **170 tests**, no failures/errors; three NumPy-dependent skips |
| Pending native contact-DRC method | **1 test passes**, official KiCad **10.0.7**; clean baseline plus genuine J2/TP122 clearance seeds |
| Supplied NumPy interpreter, HotplugNumerics and Plate | **3 tests pass**, resolving all three native-interpreter skips |

All **171 unique R10 tests** are covered across those runs, with no unresolved skip. The earlier focused proposed-code run passed 42 tests; the corresponding old-code run exposed 46 seeded subtest failures without interpreter errors. The native contact test uses the real vendor CLI; no fake real-board gate was used. The supplied-interpreter run emits NumPy overflow warnings in the synthetic Plate test and completes with exit 0.

| Frozen file | SHA-256 prefix |
|---|---|
| `tools/check_r10.py` | `b129c1b06dbedeb6` |
| `tools/fit_check.py` | `52f780c61feca88c` |
| `tools/test_r10_check.py` | `35b2cbd731fc7818` |
| `tools/test_fit_check.py` | `752d8536d0c913c1` |

Full before/after source hashes, all eight rounding measurements, exact selected test IDs, hashed log receipts and invocation details are in [round12_gate_fix.json](round12_gate_fix.json). Base hashes were verified before copying the reviewed patch. The closed-SD fixture's trailing whitespace is removed.

AGENTS §2, AUD-2/AUD-10/audit2, clearances, wire-room floors, routing allowlists and the VIPPO exception are unchanged. This is a checker-only receipt: no canonical build/full `tools/check.sh`, new-board integration result, fabrication regeneration, firmware or physical qualification is claimed by this agent. Root owns those builds and the supervisor request. Exclusive CLI use is released; no further edits to the four source files will be made without coordination.
