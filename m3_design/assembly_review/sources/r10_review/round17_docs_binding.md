# R17 lens 10: documentation and firmware binding

Fresh full review of commit `ac483f40d38db6e0424227bd32d2a5d5f9f60c3e`.
PCB before/after: `632a9ad36c19426ede219b6ff6b0d638955665cac1b4704d3392a6afdbe03982`.
All **1,966 frozen files** remained byte-identical. **0 Critical / 0 Major / 1 Minor**.
The [structured report](round17_docs_binding.json) contains every MCU row,
122 decision dispositions, 23 owner scopes, source receipts and rejected hypotheses.

## Current defect

**R17-DOC-01, Minor, carried:** `../../docs/VEHICLE.md:39` still names GH-4
ports, ARM/IGN terminals, GH-2 J400 at (10.5,85.5) and the obsolete 0.03 mm GH
fit margin. Fresh native J400 is DB125-2 at **(7.4,65.85), -90 degrees**;
all seven wired connectors are DB125 and J123/J124 are absent. The current
[local handoff](../../../../docs/R10_VEHICLE_HANDOFF.md) supplies correct poses,
contact roles and open qualification limits. Apply it through the separately
authorized parent workflow, preserving accepted R9. This is an integration-record
defect; no physical collision or required-board-function failure is demonstrated.
No parent edit was made during the freeze.

## Fresh evidence

- Official KiCad 10.0.7 exported the actual native schematic under an exclusive
  reservation: exit 0, 391,212-byte XML. All **651 numbered PCB pads**, all stored
  schematic pin nets and component fields/flags agree with that fresh export.
  All **100 MCU pins** also agree with `pin_table.tsv` and the saved binding note.
- Fresh in-memory binding generation equals the saved note exactly (SHA-256
  `35a72d796c7a6dd51eb1dc32f652c9c9f702f07121c466eb5d117e494ab392bf`).
  Current K-binding passes the canonical note and rejects isolated zero-hash,
  wrong-U1.3-net, reversed-roll-sign, malformed and missing-note controls.
  Nothing regenerated or rewrote canonical evidence.
- All 100 port names were checked against [ST DS12110 Rev11 Figure5, p55](https://www.st.com/resource/en/datasheet/stm32h743vi.pdf).
  The named cached Rev8 diagram was also rendered and inspected; its Figure5
  numbering matches the live primary Rev11 text. U4 is bottom/180 at (17,45.9),
  pin1 (18.21,45.15). [ST DS14623 Rev1 Figure5, p9](https://www.st.com/resource/en/datasheet/lsm6dsv320x.pdf)
  was rendered and inspected from the named original cache: the recorded
  `roll=-gyro_Y`, `thrust=-a_Y`, x lever arm -6 mm and frame conversion agree.
  z=-2.06 mm remains explicitly model-based Inference; bench signs remain open.
- The 18 pinned R9 source files, 142 current catalog hashes and exact historical
  decision prefix validate. Nineteen catalog aliases explicitly retain older
  blob scope; 16 ignored/external receipts were not opened or relabelled as fresh.
  Every one of the 122 D-heading IDs/titles/lines agrees with its indexed scope;
  all 23 owner mandates include the latest no-Minor-CAD-change steer.
- All 199 used 3D-model paths are relative and present. Twelve active documents
  have no broken local Markdown links or personal host paths. All 193 fab
  manifest inputs and five output hashes agree. BOM/CPL contain 82 codes and
  199 fitted placements, 46 Extended/36 Basic.

## Scope and rejected blocking hypotheses

The R10 note is explicitly **record-only**. `assembly_binding.py`, protocol and
v0.8.1 manifests retain R1 identity; diagnostics defaults to the archived R1
board. A fresh import fails at missing historical `check_assembly`, consistent
with the disclosed withdrawn R1 build chain. No firmware compile, programmer,
transport or flight behavior was tested. Missing flight firmware is not
misrepresented as implemented or qualified.

Current status/requirements/validation/ordering/AVA/handoff/qualification records
keep full R16 as the first same-PCB clean round and full R17 pending. The two
R15 builds retain their original 31-rule/176-test scope; one new R16 build and
a separate standalone check carry 32-rule/180-test scope. They are not described
as a new two-build pair. Older boards, findings, methods and acceptance lists
retain their original applicability; no prior clean pair transfers to a changed PCB.

The exact supplier snapshot remains **2026-10-30T15:30:40.008183Z**, distinct
from its 16:25 rebind. Its bound BOM/CPL and arithmetic reproduce **$79.5232**
placed/feeder share and **$81.3254** with minimum purchases versus $84.41, before
fixed/process/PCB/shipping costs. R430 **17 < 3610** and U4 **0 < 5** still fail
stock; U9 is 123/minimum1 for five fitted. No new supplier query, quote, order,
owner cost acceptance or release is claimed.

The current no-back-feed/on-rail/on-last/off-first, launch/ground/in-flight,
reset-off bias and independent-control contracts preserve AGENTS section2.
Timing, selected-lot 20 ms firing, SD latency/power loss, VCAP conditions,
DB125 insertion/fabricated S-8 allocation, electrical/thermal/transient/endurance,
RF/ESD, harness/access/retention, vehicle fit and first-article/process remain
explicitly unqualified. These omissions do not alone establish a hardware
failure. Retained M2/MEMS/land/process deviations remain pending acceptance;
the latest steer cancels their Minor CAD adoption.

No Critical/Major hypothesis survived this lens. The JSON preserves the exact
rejection evidence and limits. This lens ran no full build/check.sh, DRC/ERC,
simulation or physical qualification, and opened no peer R17 report/probe.
It made no canonical edit or git operation. Native export fontconfig warnings
did not prevent the completed semantic export. Live LSM PDF fetch and direct
Rev11 download attempts failed; only the inspected primary caches/online text
are credited.
