# Round 15 requirements and every owner decision

Full independent requirements-lens review of committed `789f4d516251991bdf1518254d537ff7b41f65bb`.
PCB SHA-256 before and after: `7866d6b895573eb10c14d0227ee4bdde8b4fba6145529786cd554cdb80121783`.
Fresh native inventory: 46 × 90 × 1.6 mm, 209 footprints, 957 segments, 296 vias,
1797.140178 mm track, 2,257,812 bytes. **0 Critical / 0 Major / 3 Minor**:
two carried groups and one new bounded record group. No C/M candidate is withheld.
R9 supplies severity precedents, not a literal definition table.

All mandatory sources, all **116 unique D IDs through D-R14-03**, their addenda,
and all **22 owner-mandate groups** were considered under the latest amendments.
[JSON](round15_requirements.json) lists every ID, owner mandate and F/P/M row.
Earlier reports were context; no peer round 15 report or probe was read.

## Active findings

| ID | Severity/status | Evidence | Concrete fix |
|---|---|---|---|
| R15-REQ-01 | Minor, carried | Read-only `../../docs/VEHICLE.md:39` still gives GH ports, ARM hardware and GH-2 J400 (10.5,85.5). Fresh native J400 is DB125-2 (7.4,65.85); all seven wired connectors are DB125, J123/J124 absent. | Apply the exact local `docs/R10_VEHICLE_HANDOFF.md` facts through the separately authorized parent workflow; preserve R9. Physical fit remains open. |
| R15-REQ-02 | Minor, carried M2 | Fresh route scan reproduces **139 = 109 ordinary + 22 AUD-10 + 8 noncritical** items and all eight location/end tuples. USB_ILIM (14.825,27.2) retains 3.33 mm vs 1.05 mm baseline, ratio 3.18; BAT_OVLO B(16.4,83) retains 0.150 mm segment. | Retain measured compromises for dated owner M2 acceptance, or adopt only separately covered native-qualified generator redraws. Current blocking rules remain unchanged. |
| R15-REQ-03 | Minor, new record inconsistency | `docs/M3_R10.md:100` says 113 decisions through D-R13-03; `STATUS.md:43` stops at D-R13-03. M3 placement line 147 still calls R13 fixes current and requests 14/15. M3 open-cost lines 476–479 and ledger OQ-3 retain predecessor numbers/U9 minimum; R14-INT-01 still says integration pending. | Update active pointers to 116/through D-R14-03 and 15/16; use current bound $82.6434/$84.4456 cost and U9 minimum 1 and completed integration state, or label the old fields explicitly historical. Preserve immutable original reports. |

These are internal integration, owner-cleanliness and record defects. None
establishes a new maker-limit breach or a demonstrated physical/FW failure.
Correct opening status and the complete 116-ID current ledger were found.

## Fresh verification

- All **100 MCU pins** agree across native PCB/XML/reviewed table/binding.
  **651 XML nodes/unique mappings** agree with **663 numbered physical pads
  collapsed to 651 pairs**; twelve duplicate fingers explain the difference.
  All 209 part identity triplets agree. The 199 fitted parts occur once each in
  BOM/CPL; all 82 BOM quantities match their distinct references.
- Thirty selected native contracts pass, including S-1…S-9, post-switch pyro,
  reset-off networks, loader, widths, inner copper, fit, legends and fast return.
  K-reference has 159810 samples/zero loose; K-region 163 items/62590 samples.
  This is selected native-API evidence, not a new full gate or CLI DRC/ERC.
- Binding and native-bound budget regenerate identically. Independent closed
  quadratic source equations reproduce **1.544366/1.479438/1.414264/1.348805/
  1.283013 A** for 0…4 persistent stalls, above the selected 1.125 A floor under
  stated assumptions. Eighty divider corners reproduce **3.342170829 V** max
  at 19.9 V. Independent watchdog/fault/neutral allocations are
  **28.571–32.653/34.853/48.653 ms**; these remain firmware/bench obligations.
- Fresh fit includes 23 tail allocations and closed SD; independent wire-face
  arithmetic gives **5.003011866 mm** at all seven terminals versus 4.95 mm.
  Minimum bottom/top support clearances are 4.536177/3.807887 mm. These are CAD
  allocations; ferrules, screwdriver, hinge, sled and actual harness remain open.
- Fresh schema-3 extraction validates against the stored 2304-case evidence.
  Independently deleting C88's model node isolates U9 from every other terminal.
  The complete numerical sweep was not rerun by this lens.
- Native all-net scan exits 0: no blocking/allowlisted/stale item, 54 bump windows,
  exact 139-item ledger partition and all 8 noncritical locations. Sixteen paste
  regressions and two NumPy Plate tests pass. The optional plate tests emit
  numerical runtime warnings but return their asserted positive/negative controls.
- All 193 fab input and 5 output hashes match freshly; all 42 generated files match
  the integration receipt. Of 96 source-catalog entries, 86 hashes match and 10
  are explicitly archived-path snapshots. This is checksum verification only,
  not a newly executed build/export or physical process acceptance.

Fresh primary sources support sensor and interface capability:
[ST IMU](https://www.st.com/en/mems-and-sensors/lsm6dsv320x.html),
[ST MCU Rev11](https://www.st.com/resource/en/datasheet/stm32h743vi.pdf),
[TE MS5611 06/2017](https://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocFormat=pdf&DocLang=English&DocNm=MS5611-01BA03&DocType=Data+Sheet&PartCntxt=MS561101BA03-50),
[MJG p1](https://electricmatch.com/upload/JTEK_TECHNICAL_INFORMATION_SHEET_SPECIFICATIONS.PDF),
[HGLRC](https://www.hglrc.com/products/hglrc-m100_mini-gps) and
[MicoAir](https://micoair.com/en/docs/telemetry/lr900/lr900-telemetry).
MJG's 0.5 s datum does not prove 20 ms lot firing; sensor specifications do not
qualify the installed Mach 1.45/1.9 vehicle, temperature or vibration behavior.

## Disposition and limits

R14-REQ-03's overhang wording and R14-REQ-04's eight-location labels close on the
current source. The repaired terminal Major remains closed at the unchanged
4.95 mm floor. The R14 XML denominator erratum is freshly confirmed.

Single-switch/on-rail/on-last/off-first, launch detection, hard ground refusals,
in-flight never-veto, post-load-switch feed, reset-off gate networks and inference
labels remain authoritative. No section 2 violation was demonstrated. R10
firmware and all declared bench/physical/process qualifications remain open;
they were not converted into invented hardware failures. The no-powered-break,
servo-power-cutoff loss, always-on/direct UARTs and optional-plate scope follow
explicit owner amendments.

No canonical edit, KiCad CLI, full build/check.sh, GUI, git action, other-worktree
write or subagent was used. Initial probe setup corrections (fit SHA metadata
and six manifest tooling-path roots) are recorded in JSON and are not findings.
No complete 100-pin maker-mux rederivation, full hot-plug rerun, live 82-code
supplier refresh, assembly-PDF visual review, firmware or physical test is claimed.
Only the assigned new reports and ignored probes were written.

Fresh complete 15/16 must earn the final same-board pair; owner deviation/cost
acceptance, R430/U4 supply, process/panel quote and fresh pre-order data remain
required. No R10 acceptance or order follows.
