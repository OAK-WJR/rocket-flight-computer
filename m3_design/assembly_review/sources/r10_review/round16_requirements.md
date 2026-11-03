# Round16: full requirements and every owner decision

Full independent lens on committed `b1b8658d5bf541795b7e7636c09f2e886ea8c67a`.
PCB SHA256 before/after: `632a9ad36c19426ede219b6ff6b0d638955665cac1b4704d3392a6afdbe03982`.
Fresh inventory:46x90x1.6mm,209 footprints,951 segments,296 vias(168GND),1788.675665mm track.
**0 Critical /0 Major /3 Minor: two carried groups and one new active-record group.**
No C/M candidate is withheld. Severity follows R9 precedents and the review packet,
which distinguish demonstrated failure from disclosed pending qualification.

All119 unique D IDs through D-R15-03,all addenda,and all22 owner-mandate scopes
were read and mapped under their current amendments. [JSON](round16_requirements.json)
contains every ID,source line,current disposition,actual evidence and limits,plus
each F1-F10/P1-P3/M1-M3 row. The earlier circuit-only stop is superseded.
Prior reports were context; no peer current-round16 report/probe was read.

## Active findings

| ID | Severity/status | Evidence | Concrete fix |
|---|---|---|---|
| R16-REQ-01 | Minor,carried R15-REQ-01 | `../../docs/VEHICLE.md:39` still gives GH ports,ARM hardware and GH2 J400(10.5,85.5). Native J400 is DB1252P(7.4,65.85); all seven wired connectors are DB125,J123/J124 absent. | Apply `docs/R10_VEHICLE_HANDOFF.md` through the separately authorized parent workflow,preserving R9. Physical fit remains open. |
| R16-REQ-02 | Minor,carried M2 | Fresh scan:140=111ordinary+23inside-pad+6noncritical,46 bump windows,zero blocking/allowed/stale/critical bumps. USB_ILIM(14.825,27.2)3.33mm vs1.05mm baseline,ratio3.18; BAT_OVLO B(16.4,83)0.150mm segment. | Preserve the current partition and six location/end tuples once in the final owner M2 inventory,or make separately covered native-qualified generator redraws. Actual rules remain unchanged. |
| R16-REQ-03 | Minor,new | `m3_design/assembly_review/sources/r10_design/r10_plan.md:5-11` labels7866d6b8/957segments and D-R14 current,and requests15/16. Exact target is632a9ad3/951segments,119 decisions through D-R15-03,requiring16/17. | Refresh only the active status/supersession block,or label it historical. Preserve original reviews and no transferred clean credit. |

The six noncritical leftovers are listed once in JSON evidence R:BAT_OVLO
B(16.4,83),BUZZ_DRV F(20.5,51.8),BAT_FAULT_N B(28.2,47.5),I2C1_SDA
B(9.97,51.5),BAT_ENABLE B(21,68.6),USB_ILIM net(14.825,27.2).
The named R15 M3/STATUS/cost/ledger pointer findings close; the active plan
block above is a separate remaining record defect.

## Fresh checks

- All651 unique PCB/XML reference-pin mappings agree with663 numbered physical pads
  after twelve duplicate fingers collapse. All100 MCU pins agree with reviewed table
  and binding; all209 identity triplets/footprints agree. All199 fitted BOM/CPL parts
  and all34 in-memory schematic contract seeds pass.
- All31 native rule functions pass in two read-only API invocations. K-reference:
  158499 samples,zero loose; K-region:161 items/62176 samples. All nine refilled
  zone symmetric differences are0 at the unchanged0.01mm2 tolerance. No CLI or
  full tools/check.sh/DRC/ERC pass is claimed by this lens.
- Binding and native-bound budget regenerate exactly. Independent source bisection
  reproduces1.544366/1.479438/1.414264/1.348805/1.283013A for0..4 persistent stalls,
  above the selected1.125A floor under stated source/material/harness assumptions.
  Eighty divider corners give3.342170829V at19.9V. Independent watchdog/fault/neutral
  allocations are28.571-32.653/34.853/48.653ms,still firmware/bench obligations.
- Fit includes23 tail allocations and closed SD. Independent wire-face arithmetic
  gives5.003011866mm versus4.95mm at all seven terminals. Bottom/top support
  minima are4.536177/3.807887mm. Ferrules,bends,tool/hinge,sled and actual stack remain open.
- Fresh schema3 feed extraction/validation passes. Independently deleting C88's
  graph node isolates U9 from every other terminal. The stored2304required+60local
  sweep is correctly bound; this lens did not rerun the full numerical sweep.
- All five manifest outputs and42 generated-file hashes match the completed R15
  integration receipt. This is checksum evidence,not a new build/export,live quote,
  process approval or assembly-drawing visual review.

Fresh primary checks support sensor/interface capability:[ST IMU DS14623Rev1pp1-3](https://www.st.com/resource/en/datasheet/lsm6dsv320x.pdf),
[ST MCU DS12110Rev11pp91-92/211/233](https://www.st.com/resource/en/datasheet/stm32h743vi.pdf),
[TE MS5611 06/2017pp1-3](https://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocFormat=pdf&DocLang=English&DocNm=MS5611-01BA03&DocType=Data+Sheet&PartCntxt=MS561101BA03-50),
[HGLRC](https://www.hglrc.com/products/hglrc-m100_mini-gps),
[MicoAir](https://micoair.com/en/docs/telemetry/lr900/lr900-telemetry),
[RunCam p1](https://www.runcam.com/download/split4k/RC_Split_4k_Manual_EN.pdf),
[MJG p1](https://electricmatch.com/upload/JTEK_TECHNICAL_INFORMATION_SHEET_SPECIFICATIONS.PDF),and
[DORABO T0-1sheet1](https://atta.szlcsc.com/upload/public/pdf/source/20251124/8C215F69B14C8E54AE0F8E5023D4AE9F.pdf).
The complete terminal drawing was rendered and inspected using the PDF skill.
The named cached MCU copy was found to beRev8 and excluded fromRev11 conclusions;
current officialRev11 supplies the cited AF/VCAP/LSI facts.

## Rejected severity hypotheses and limits

No actual AGENTS2 violation was demonstrated. Post-load-switch feed,separate
PC1/PE4 controls,reset-off gate networks,on-rail/on-last/off-first,launch/ground
refusal/in-flight never-veto and no-backfeed-while-connecting-match remain explicit.
The shared MCU,no powered physical break,ordinary surface clearance,always-on
ports and loss of servo power cutoff are owner-amended constraints.

The VCAP combined-C/ESR and DB125 insertion/fabricated-barrel hypotheses remain
bounded disclosed qualification gaps; nominal selection alone proves neither
failure nor operating/process compliance. MJG's0.5s all-fire datum does not prove
20ms lot firing. The narrow hot-plug simulation margin does not prove measured
pin compliance. JSON preserves each C/M hypothesis and why it was not established.

No firmware,SD latency/power-loss,e-match lot,actual tail/watchdog,thermal/transient/
endurance,installedRF/ESD,harness/contact/retention,physical access/bore/stack/modal/
flight or first-article qualification was performed. Executable firmware remains
R1-bound; the exact R10 note is record-only evidence. No git action,canonical edit,
other-worktree write,subagent,GUI retry,CLI or owner question occurred. Initial
probe metadata/SWIG corrections are disclosed in JSON and are not board findings.

Fresh complete16/17 on this changed PCB must earn the final same-board pair.
Owner deviation/cost acceptance,R430/U4 supply,process/panel quote and fresh
pre-order data remain required. R10 remains unaccepted and unordered.
