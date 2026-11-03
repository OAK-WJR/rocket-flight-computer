# R15 lens 10: documentation and firmware binding

Fresh full review of commit `789f4d516251991bdf1518254d537ff7b41f65bb`, PCB
`7866d6b895573eb10c14d0227ee4bdde8b4fba6145529786cd554cdb80121783`
(2,257,812 bytes). **0 Critical / 0 Major / 2 Minor.** All 1,909 preexisting
tracked files and the target commit/PCB were hashed before and after: unchanged.
No peer R15 reports/probes, subagents, canonical writes, Git mutations or GUI retries.

## Findings

| ID | Severity/status | Current evidence | Concrete fix |
|---|---|---|---|
| R15-DOC-01 | Minor, new | Active summaries drift beneath correct R14 headers. `M3_R10.md:100` says113 decisions throughR13 versus116 throughR14; `STATUS.md:43` also stops atR13. `M3_R10.md:147` and ledger `/current_topics/historical_count/required_closure` still request14/15 rather than15/16. `M3_R10.md:476` and ledger `/owner_mandates/10/disposition` retain82.65/84.99USD and U9minimum7; current11:03 snapshot is82.6434/84.4456USD,U9stock113/minimum1. `R10_VEHICLE_HANDOFF.md:39` gives C431's modeled100g/D5 gap0.274mm; current board-bound `round14_plate.json` gives0.270912671mm at B(39.3,57.75). | Correct only active summaries/fields to the existing current records:116/D-R14-03, full15/16, dated11:03 procurement figures and0.270913mm modeled gap. Preserve immutable historical reports. No native or qualification change is required. |
| R15-DOC-02 | Minor, carried | Read-only `../../docs/VEHICLE.md:39` still describes GH ports, GH-2J400 at(10.5,85.5), ARM terminals and0.03mm mated-GH margin. Native J400 is DB125-2F(7.4,65.85); all seven wired terminals are DB125, J124 is absent, and the old mating margin is inapplicable. The current in-worktree HANDOFF already supplies replacement facts. | Apply that R10-only replacement through the separately authorized parent-document workflow, preserve acceptedR9 history/OQ-7 and keep physical fit open. Do not edit the other worktree during this review. |

Both are bounded record/integration defects. Correct current headers, native
artifacts and release restrictions already exist; no hardware function failure
or false owner acceptance is demonstrated.

## Fresh checks

- Read AGENTS first; both review packets, REQUIREMENTS, complete decisions through
  D-R14-03, AVA_LAYOUT, M3_R10, R10_VALIDATION, R9 severity precedents and read-only
  VEHICLE. Considered all116 decision IDs and22 owner-mandate records under their
  current amendments; exact source/ledger ID sets match.
- One root-reserved official native CLI schematic export exits0. Its209 component
  identities/flags and651 unique reference/pin nets equal committed XML. PCB,
  XML, pin table and evidence note agree on all100 MCU pins; all four binding
  hashes match.663 numbered PCB pads collapse to651 unique pairs because of12
  duplicate fingers. The existing count-label erratum is correct.
- Native API confirms209 footprints/957segments/296vias/1797.140177594mm track,
  46x90x1.6mm, seven terminal maps/poses, J430B(24,24.3),118shown/91hidden refs
  and40legends. U4B180(17,45.9),pad1offset(+1.21,-0.75),leverx-6 and roll=-gyroY
  agree; leverz-2.06 remains model-derived Inference.
- The fresh schematic contract returns no issues. In-memory note and native-bound
  budget regenerate identically. Independent quadratic arithmetic reproduces
  1.544366071699..1.283013039049A across0..4stalls.960LSIcycles gives
  28.571428571..32.653061224ms and the allocated34.853061224ms fault bound.
- Five-output fab manifest passes against193 current inputs.82 BOM codes contain
  199 distinct fitted references with matching positive quantities; CPL has the
  same199 native-fitted parts,67top/132bottom.187 reconstructed plus12
  placement-only checks is correctly distinguished from all199 rows. All17
  currentR14 source-catalog hashes match.
- The executable chain remains R1: `assembly_binding.py:20`,
  `protocol_assembly.json:7`, ICM-45686 requirement in `build.py:92`, and no R10
  build target. The read-only binding import stops at missing legacy
  `check_assembly`, before compilation or artifact creation. The regenerated
  R10 JSON explicitly says record-only; it is not executable approval.

## Source checks and rejected candidates

[ST DS12110 Rev11, January2026](https://www.st.com/resource/en/datasheet/stm32h743vi.pdf)
supports selected UART AF, input/pull and LSI facts. The named static H743 cache
was actually Rev8 and was rejected; current Rev11 text was checked live after
local download failures. [ST DS14623 Rev1 p9](https://www.st.com/resource/en/datasheet/lsm6dsv320x.pdf)
was visually inspected for axes. Complete [DORABO T0-1 sheet1](https://atta.szlcsc.com/upload/public/pdf/source/20251124/8C215F69B14C8E54AE0F8E5023D4AE9F.pdf)
and [Huaneng MLT-5020 p2 item9](https://datasheet.lcsc.com/datasheet/pdf/23f5c6599ed9cb614c21ac31ad2b1106.pdf?productCode=C94598)
were visually inspected; the latter gives nominal0.5g.
[MJG J-Tek p1](https://electricmatch.com/upload/JTEK_TECHNICAL_INFORMATION_SHEET_SPECIFICATIONS.PDF)
defines its0.75A all-fire datum at0.5s. The actual20ms lot test remains pending.

No false executable binding, current map/axis/package mismatch or AGENTSsection2
violation was found. Explicitly absent firmware/physical qualification is not a
proved hardware failure. The old unreferenced `schematic_validation.json`
(250parts/746pins/old seed names) was rejected as current evidence; the actual
build writes its fresh schematic receipt separately. JSON preserves these
rejected/closed C/M candidates and their evidence.

This lens did not rerun a canonical build/full check, PCB DRC/ERC, full
orientation/paste suites,2304case sweep or optional plate solve. Exact-board
receipts were hash-checked, while fresh schematic/mapping/regeneration checks
above were actually executed. No physical, firmware, installed RF/ESD, harness,
fit, flight, process, quote, order or owner acceptance is inferred. Reports are
read-only evidence; all retained qualification and procurement obligations stay
open. Structured measurements,116IDs,22mandates, source hashes and limitations
are in the companion JSON.
