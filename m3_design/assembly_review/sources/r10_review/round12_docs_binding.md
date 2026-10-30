# Round 12: documentation and firmware binding

Assigned commit `d57b216c365fc8d18896bceba37f63caf20d52a4`; native PCB SHA-256 `0ad0135cb9ff1f6ace7ef9d5ba9006b727b293d7b5224bb97dad47859b91238d`, verified before and after.

**0 Critical / 0 Major / 2 Minor groups, both carried documentation residuals.** No missing current safety/electrical binding obligation or demonstrated required-function failure was established. Only the two assigned reports were written; no current-round peer report was read.

## Current findings

### R12-DOC-01 — Minor, carried: active summaries still mix older board geometry with the corrected target

The generated evidence and current assembly worksheet agree with native CAD. Parallel active prose is incompletely refreshed:

- `docs/REQUIREMENTS.md:156-165` explicitly calls `0c50b9fd…` the current board, gives 981 segments / 294 vias / 23 reproduced files, says no review has run and starts fresh reviews at 11. The frozen target is `0ad0135c…`, 973 segments / 295 vias; all 42 recorded hashes match. Round 11 is completed and non-clean on the older target.
- `docs/M3_R10.md:130-139` says the corrected rows still require a future supervised build despite its correct opening completion banner.
- `docs/M3_R10.md:178-189` gives old Power-cell poses and fire-length/resistance figures without a historical-board heading:

| Subject | Prose | Current native / board-bound evidence |
|---|---|---|
| Q120 / Q121, bottom | (13.5,72.6) / (13.5,67.6) | (13.5,73.6) / (13.5,68.6), rotations 0° / 180° |
| C82, bottom | (39.8,74.75) | (19.3,76.75), 90° |
| D9, bottom | (43.35,73.45) | (15,79.3), −90° |
| R92, top | “now” (35.25,57) | (31,87.5), 0° |
| RAW_ACT / IGN / OUT tracks | 6.500 / 4.850 / 7.954478 mm | 5.886133 / 10.230382 / 7.854478 mm |
| Hot credited copper | 30.1231 mΩ | 35.132126 mΩ |

The current CH1 budget and `parts_qualification.md` already contain the corrected calculation. This is the residual narrative portion of R11-m01/m02, with newly located requirement-summary evidence, **not a failed fire-current margin**.

Fix: update these current summaries from the frozen target or put retained paragraphs under their exact historical PCB. Link the current assembly/budget worksheet instead of maintaining contradictory coordinate copies. No CAD or requirement relaxation is needed. Maker page: not applicable to a native/prose mismatch.

### R12-DOC-02 — Minor, carried R11-m03: parent VEHICLE still names removed hardware

Read-only `../../docs/VEHICLE.md:39` still describes an ARM terminal, GH-4 ports, GH-2 J400 at (10.5,85.5), and a 0.03 mm mated-GH margin. Native CAD has no J124/J123/GH/header. Its outward-facing west DB125 row is x7.4: IGN y55.85, switch y65.85, battery y75.85; east x38.6: GPS y15.5, radio y31.5, camera y47.5, servos y71.5. J430 is bottom (24,24.3).

The mismatch is already disclosed and does not prove physical interference. The separate parent document remains untouched as instructed.

Fix handoff: in a separately authorized parent update, preserve R9 history and replace the R10 clause with the seven DB125s/current rows, sole J400 power/arming switch, no ARM/GH/header/tie holes, always-on external GPS/radio and retained switched/isolated camera, bottom hinged card and its sled-removal/access-window condition. Preserve 46×90 mm/five supports, no RF overhang, board wholly forward of joint+47 mm including tolerance, and unqualified harness/bore/stack fit. Keep calculated 5.003 mm wire room distinct from physical fit; integrate the required 2.6/4 Ah pack case without treating old coax slack as fit proof. Maker page: not applicable.

## Verified evidence and prior closures

- **100/100 U1 pins** agree across native PCB, XML, reviewed `r10_net` table and saved binding; modes also agree between table/note. All **4/4 binding hashes** match: PCB, XML, table and circuit.
- **209/209 component sets**, **663 shared numbered pad nets** and all compared LCSC/Manufacturer/Manufacturer Part fields agree. All **68 explicit circuit parts / 186 pins** agree with native pad nets. Removed ARM/pull-pin/RF/port-switch/translator/duplicate-divider parts are absent.
- **34 firmware obligations** and all five static source/state/policy/test sections match generator literals by passive Python AST inspection. No generator was executed. The handoff preserves both-low passive screening before PC1, ≥1 s verified discharge after prior enable, ≥100 ms settle, launch-only firing, ground refusal/in-flight non-veto, dual locks/readbacks, 20/36 ms physical-current contracts, no refresh during fire, neutral-first ≤50 ms, always-on-port restrictions, bounded SD/QSPI/UART work, PA6 shedding, ADC/EXTI/PA15/LSE/trace and dark-in-flight LEDs pending cover test.
- **U4** is bottom/180° at (17,45.9), pad1 (18.21,45.15), offset (+1.21,−0.75), x lever −6 mm. Binding remains roll −gyro_Y / thrust −a_Y; z −2.06 mm is explicitly inferred. This verifies native pose/binding consistency, not a newly derived maker-axis diagram or a bench sign check.
- All **42 recorded generated-file hashes**, **193 fabrication-input hashes** and **5 output hashes** match. CPL has **199 rows: 67 top / 132 bottom**, BOM **82 codes**. These are existing-artifact checks, not new builds/exports or physical assembly evidence.
- R11-DOC-01's underlying generated budget is closed: current budget SHA `55b84df3…` matches the native-bound receipt and qualification record; conditional loop 4.617458126 Ω gives 1.544366072 A idle / 1.283013039 A four stalls. Stale parallel prose remains above. No new solver run is claimed.
- R11-DOC-02's ordering/retention portions are closed: §8 now has correct connector/probe poses and J9 board directions, staking for all seven DB125s including J400, full U4/U5 masks, manual C84/VIPPO process and bottom-card access. The parent-mirror defect remains carried.
- All **25 retained firmware binding JSONs** target older profiles; zero match this R10 PCB. Static builder inspection retains profile/board/source checks and the R1 assembly chain; no R10 executable binding or firmware approval is claimed. No firmware builder was run.

## Primary-source checks and limits

Selected [ST DS12110 Rev11](https://www.st.com/resource/en/datasheet/stm32h743vi.pdf) checks covered Table10 pp91–92, Table9 p67 and RevV Table136 p233: UART/ADC facts and 29.4–33.6 kHz LSI basis agree; 960 cycles yields 28.571–32.653 ms. [AN2606 Rev70 Table135 pp320–323](https://www.st.com/resource/en/application_note/an2606-stm32-microcontroller-system-memory-boot-mode-stmicroelectronics.pdf) retains the cited loader output/input roles. This is selected verification, not a complete new AF/silicon review. [MJG p1](https://electricmatch.com/upload/JTEK_TECHNICAL_INFORMATION_SHEET_SPECIFICATIONS.PDF) agrees on 0.75 A/0.5 s all-fire and the retained shroud; 1.5× gives 1.125 A, with selected-lot 20 ms firing correctly unqualified. ST's IMU PDF exceeded the web tool size limit, so no new maker-axis-diagram check is credited.

Read the complete chronological owner-decision record through round11 completion, all packet read-first records, original plan O1–O6 and amendments, parent VEHICLE, current ordering/FMEA/status/qualification and binding sources. All owner choices and original functional/physical/manufacturing obligations were reconciled at the documentation level; correctly disclosed unimplemented firmware, physical/process/stock/quote qualification and the planned final deviation inventory are not new hardware findings.

Executed only reads, hashing, CSV/XML/AST comparisons and read-only KiCad Python parsing. Native parsing emitted a nonfatal wx assertion and exited0. Two preliminary probe mistakes (unsupported GetProperty API and logical manifest-path prefix) were corrected and successfully rerun, with no file mutation. No Git action, source/CAD edit, CLI/DRC/ERC, gate, build, generator, export, simulation solve, GUI retry, supplier refresh, firmware execution or physical test. No current-round peer findings were accessed. The supervisor request file was absent when reports were written. Structured details: `round12_docs_binding.json`.
