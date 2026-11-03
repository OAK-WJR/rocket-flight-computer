# Round 14 documentation and firmware binding review

Target commit `f5e4a5a94013514edb952fd328325341b63a98df`. PCB before and after: `e0e3ad841654128792b32ab778ca19e4a71e596fa89864074ec4e91e6a5ccfc6`.
Native read-only inventory: 46 x 90 x 1.6 mm, 2,259,597 bytes, 209 footprints, 966 segments, 296 vias (168 GND), 1802.125220 mm track.

**Active totals: 0 Critical, 0 Major, 3 Minor** (2 new, 1 carried). No hardware-function failure was established. Correctly disclosed pending firmware/physical qualification is not a new failure. This is a full independent lens; prior reports were context only and current peer R14 reports were not read.

## Active findings

### R14-DOC-01 - Minor, new: active FMEA fire-current summary is stale

`docs/FMEA_REDUNDANCY.md:21` gives 1.546/1.481/1.284 A at 0/1/4 persistent stalls in its current R10 amendment. Fresh native `power_budget()` equals `sources/r10_design/parts_budget.json`; a separately written quadratic solve gives **1.544366/1.479438/1.283013 A**, exactly matching that board-bound worksheet (lines 322-347). The discrepancy is +1.634/+1.562/+0.987 mA. Relevant terminal: J121 F(7.4,55.85), pins 1 OUT/2 IGN.

Fix: use 1.544/1.479/1.283 A and the current board/worksheet binding, or scope the old values to their historical target. Preserve the equivalent 7.4 V fire-time reserve, 1.125 A floor, and selected-lot/source/harness/20 ms qualification. The [MJG technical source, p1](https://electricmatch.com/upload/JTEK_TECHNICAL_INFORMATION_SHEET_SPECIFICATIONS.PDF) is the unchanged match basis; this is a transcription finding. All current cases still exceed the project floor, so no required-function failure follows.

### R14-DOC-02 - Minor, new: U9 supplier row differs from its named snapshot

`docs/ORDERING.md:278` says 101 U9s available and USD0.53784/board extra for seven pieces versus five fitted. The original public JLC query item, production `fab/stock_check.json:655` and `fab/cost_check.json:913` all give **94 stock, minimum 7, USD1.3455 each** at 2026-10-30T08:38:52.797802Z. Independently: `(7-5)*1.3455/5 = USD0.53820/board`. Relevant part: U9 B(18.5,81.6), [C3662793](https://jlcpcb.com/partdetail/TexasInstruments-TPS259470LRPWR/C3662793). Exact raw-response hash/extract is preserved in the JSON.

Fix: use 94 and USD0.53820, or reference the bound record instead of duplicating precise figures. Seven for five remains correct; U9 is still sufficiently stocked for that minimum. The complete cost totals already reconcile, while R430/U4 still block stock release. No new quote or supplier query was made by this lens.

### R14-DOC-03 - Minor, carried: parent vehicle candidate mirror remains stale

`../../docs/VEHICLE.md:39` still describes GH4 ports, ARM terminals, GH2 J400 at (10.5,85.5), and the old 0.03 mm GH mating margin. Fresh native J400 is F(7.4,65.849999), -90 degrees, BAT_SW_SOURCE/RETURN; there is no J124. All seven current terminal poses/roles agree with `docs/R10_VEHICLE_HANDOFF.md:11`. The [DB125 source drawing, p1](https://atta.szlcsc.com/upload/public/pdf/source/20251124/8C215F69B14C8E54AE0F8E5023D4AE9F.pdf) is the present terminal basis; old GH fit does not transfer.

Fix: apply the complete current handoff through the separately authorized parent-repository workflow, preserving accepted R9 history, or explicitly obsolete the parent candidate paragraph and link the handoff. No other-worktree edit was performed. This carries R11-m03/R12-m02/R12-DOC-02/R13-DOC-03; correct local instructions and openly pending physical fit bound the severity.

## Fresh evidence

- All 100 MCU pins agree across native board, netlist, reviewed table and note; all 663 schematic-backed numbered pads agree with the native board. The source schematic contract reports zero issues, and all 18 pinned R9 source files match their manifest.
- `r10_binding_note.json` regenerates identically **in memory**, including current board/netlist/table/circuit hashes. U4 is B(17,45.9), 180 degrees; fresh maker Figure 5/pin-map comparison supports roll=-gyro_Y, thrust=-a_Y and x lever arm=-6 mm. Model-derived z=-2.06 mm remains an Inference; physical sign checks remain mandatory.
- Executable `assembly_binding.py`/protocol/proof remain **R1-bound**, with proof/protocol SHA e432d343...; an import-only probe fails on unavailable `check_assembly`. No firmware was compiled or run. The R10 note is evidence only and cannot qualify this board.
- The entire native power worksheet replays exactly. Independent arithmetic confirms all five coupled fire cases, IWDG 28.571-32.653 ms/34.853 ms fault allocation, O6 0.6144 A reference-share bound and 3.342171 V single-resistor sense bound. These retain their stated unmeasured assumptions.
- Fresh native hot-plug extraction JSON-normalizes identically to current inputs. Input/electrical/model digests and 2304 required +4 refined +60 local +4 local-refined records validate with zero issues. This lens did **not** rerun the full numerical sweep.
- All 42 generated-file receipt hashes and the manifest's 193 input/five output hashes match. BOM/CPL sets agree: 82 codes, 199 fitted rows, 67 top/132 bottom CPL. All native model paths are project-relative. Current 118 visible/91 hidden references and the complete M3 hidden-reference list agree.
- All 113 unique decision IDs, titles and source lines exactly match the current ledger; all 22 owner mandates/amendments were considered. All 58 catalog paths exist with no applicable hash mismatch; 315 source JSON pointers resolve. The JSON contains the full decision and mandate coverage index.
- Independent supplier-line totals are USD57.5538 parts +USD25.092 feeder share =USD82.6458; minima give USD84.9862, USD0.5762 over USD84.41 before excluded costs. R430 17<3610 and U4 0<5 remain pending procurement blockers. Current acceptance/STATUS/AGENTS/AVA/ordering/deviation records correctly require fresh full14/15, owner acceptance and process/stock closure.

## Closed and qualified items

R13-DOC-01 is closed: O6 now names signal-reference branches. R13-DOC-02 is closed: AGENTS correctly separates the record-only R10 note from the executable R1 chain. R13-DOC-04 is closed: current servo-raceway risk uses estimated Mach1.9. Each closure was checked against current source/native evidence before consulting the prior report for classification.

Fresh [ST DS12110 Rev11](https://www.st.com/resource/en/datasheet/stm32h743vi.pdf) and [AN2606 Rev70](https://www.st.com/resource/en/application_note/an2606-stm32-microcontroller-system-memory-boot-mode-stmicroelectronics.pdf) crosschecks cover AF/ADC/loader roles, the operating pull-off condition and LSI range. Current direct UART RX pulls are always disabled, separately from the 4 V absolute-stress note. PDF skill/Poppler inspection of primary [DS14623 Rev1](https://www.st.com/resource/en/datasheet/lsm6dsv320x.pdf), complete p9/p10, checked the axis/pin-1 drawing; p15's 40 ms gyro turn-on is typical only, not a worst-case readiness guarantee. Startup validity remains an explicit sensor/firmware qualification obligation.

## Limits

No git action, canonical edit/build, native CLI DRC/ERC/export, full check.sh, GUI launch/retry, firmware compile/programming, supplier requery, quote/order/owner acceptance or other-worktree write occurred. Root reserves CLI and full-gate work. Native API checks emitted nonfatal wx/image-handler diagnostics; final probe exited0. One supplementary pointer visitor type error and tuple/list comparison were corrected only in ignored probes before final results.

Existing full-build/DRC receipts were rehashed, not relabelled as newly executed here. Stored schematic/source agreement does not replace root's fresh native export/parity gate. No prior clean pair transfers after this PCB change. No physical, firmware, electrical/thermal/transient/endurance, SD/e-match lot, RF/ESD, harness/switch/retention, tool/card access, bore/stack/flight or first-article qualification is claimed. No hidden AVA electrical choices were inferred.

Durable hashes, checks, minimal raw supplier proof, arithmetic, all 113 decisions/22 mandates and coverage limits: [round14_docs_binding.json](round14_docs_binding.json).
