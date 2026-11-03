# Round14 requirements and every owner decision

Fresh full independent review of committed `f5e4a5a94013514edb952fd328325341b63a98df`.
PCB SHA-256 before and after:
`e0e3ad841654128792b32ab778ca19e4a71e596fa89864074ec4e91e6a5ccfc6`.
Native inventory: 46 × 90 × 1.6 mm, four layers, 209 footprints, 966 segments,
296 vias, 1802.125220 mm track, 2,259,597 bytes. **0 Critical / 0 Major / 4 Minor**: two new
bounded record defects and two carried groups. No C/M candidate is withheld.
R9 supplies review precedents, not a literal severity-definition table.

All mandatory sources, all 113 unique D IDs through D-R13-03, their addenda and
all 22 owner-mandate groups were read against current amendment scope. The
[JSON](round14_requirements.json) lists every ID and each F1-F10/P1-P3/M1-M3
assessment. This is a complete lens review, not a delta. Prior reports were
context; no peer round14 report was read. No canonical file or CAD was changed.

## Active findings

| ID | Severity/status | Concrete evidence | Concrete fix |
|---|---|---|---|
| R14-REQ-01 | Minor, carried R13-REQ-03 | Read-only `../../docs/VEHICLE.md:39` still gives GH ports, ARM hardware and GH-2 J400 (10.5,85.5). Native J400 is DB125-2 (7.4,65.85), all seven wired connections are DB125; J124/J123 are absent. | Apply the exact local `docs/R10_VEHICLE_HANDOFF.md` facts through the separately authorized parent workflow; preserve R9. Local disclosure is correct; physical fit remains open. |
| R14-REQ-02 | Minor, carried M2 | Fresh route scan exactly reproduces 140 = 110 ordinary + 22 AUD-10 + 8 noncritical items. At (14.825,27.2), USB_ILIM is 3.33 mm versus 1.05 mm baseline, ratio 3.18. BAT_OVLO B(16.4,83) retains a 0.15 mm segment; BUZZ_DRV F(20.5,51.8) retains 0.30 mm offset/0.424 mm middle. Principal ledger counts/locations are correct. | Retain measured deviations for dated owner M2 acceptance, or adopt only native-qualified generator redraws with new review coverage. Actual fast/critical rules remain blocking. |
| R14-REQ-03 | Minor, new record inconsistency | `docs/REQUIREMENTS.md:67` P1 says R10 “no overhang.” Fresh J3 transformed model reaches x = −0.449880 mm across y = 26.330107…35.269891; current M3/handoff already disclose approximately 0.45 mm west shell projection. | Qualify P1 as “no SMA/aft overhang; J3 shell projects approximately 0.45 mm west.” No new physical overhang or bore-fit failure is alleged. |
| R14-REQ-04 | Minor, new record inconsistency | `r10_final_deviations.json` at `#/record_conventions/location_inventory` and `#/routing_inventory/pad_endpoint_semantics/required_closure` still says nine location rows. Actual array/fresh scan has eight; main completion/partition fields correctly say eight. | Correct those two current explanatory labels or explicitly scope them as archived 7355/nine-row wording. Preserve original immutable findings and all eight current entries. |

These findings concern owner routing requirements and project/native record
consistency; no maker parameter is inferred from them. Exact files, coordinates,
measurements, source-scope notes and fixes are retained in JSON. The parent
mirror and M2 compromises remain active despite correct disclosure. Pending
physical/firmware qualifications were not counted as demonstrated failures.

## Fresh evidence

- All 100 MCU pins agree across native PCB/XML/reviewed table/binding. All 209
  component identity triplets and 663 XML pin nodes agree. Binding and budget
  regenerate identically in memory. The 199 fitted parts occur exactly once in
  the actual 199-row CPL and 82-code BOM, with correct positive quantities.
- All 21 selected native contracts pass, including S-1…S-9, fit/axis/loader,
  K-reference (160170 samples, zero loose), K-region (165 items, 62653 samples,
  zero issues), inner-layer policy and limited resistor-tap widths. Q120/Q121
  remain the post-load-switch pyro path; PC1/PE4 and off-bias networks remain.
- Fresh fit includes all 23 tail allocations and closed SD, 15.05 × 15.70 ×
  2.10 mm. The independent wire-face equation gives 5.003011866 mm at all seven
  terminals against 4.95 mm. Minimum bottom/top support clearances of
  4.536177/3.807887 mm pass.
- An independent pack fixed-point solve reproduces 1.544366/1.479438/1.414264/
  1.348805/1.283013 A for zero through four persistent stalls under stated
  conditions. Eighty divider corners reproduce 3.342170829 V maximum at 19.9 V.
  Independent watchdog/fault/neutral allocations are 28.571–32.653/34.853/48.653 ms.
- Fresh live schema-3 hot-plug extraction equals stored inputs; removing C88
  isolates U9 from every other model terminal. All 2304 stored cases validate;
  the full numerical sweep was not rerun here. These remain Simulation/Inference.
- The fresh all-net route/bump scan exits zero: zero blocking/allowlisted/stale,
  54 windows, the exact 140-item ledger partition and all eight location tuples.
  No missing current residual was found. Imperfect routing awaits owner acceptance.
- All 113 decision IDs match the source exactly; all 22 mandates are accounted
  for. Of 58 source-catalog entries, 55 current hashes match and three archived
  snapshot pointers are scoped correctly. All 315 JSON source references resolve;
  42 current generated files match the complete integration receipt. Receipt
  checks are not new build executions.

Primary maker sources were reopened: [ST IMU capability](https://www.st.com/content/st_com/en/products/mems-and-sensors/inemo-inertial-modules/lsm6dsv320x.html),
[ST MCU Rev11](https://www.st.com/resource/en/datasheet/stm32h743vi.pdf) (selected muxes, LSI and I/O limits),
[TE MS5611](https://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocFormat=pdf&DocLang=English&DocNm=MS5611-01BA03&DocType=Data+Sheet&PartCntxt=MS561101BA03-50) (pp. 1/4),
[MJG p1](https://electricmatch.com/upload/JTEK_TECHNICAL_INFORMATION_SHEET_SPECIFICATIONS.PDF),
[HGLRC specifications](https://www.hglrc.com/products/hglrc-m100_mini-gps) and
[MicoAir manual](https://micoair.com/en/docs/telemetry/lr900/lr900-telemetry).
The sensor range supports the CAD capability; accuracy and installed flight
performance remain open. MJG's 0.5 s datum does not prove 20 ms lot firing.

## Disposition and limits

R13-REQ-01's signal-reference wording and R13-REQ-02's preparation/index/build
state defects are corrected. R13-REQ-04's missing/stale inventory defect closes:
the current native partition matches; retained M2 compromises remain above.
The terminal CAD floor remains repaired without changing 4.95 mm. Current source
distinguishes R10 evidence JSON from the executable R1 binding.

Single switch/on-rail/on-last/off-first, launch detection, ground hard refusals,
in-flight never-veto, post-load-switch bus, reset-off gates and inference labels
remain authoritative. O6's return bound, actual feed parasitics, 20 ms current tail,
SD latency/power loss, hold-up, thermal/RF/ESD, tool/card/harness/sled/stack and
5 × 100 g retention remain conditional qualifications. LEDs stay dark until the
actual opaque-cover test passes. The vehicle's K850DM/L1000W model is still to
be updated/weighed; neither old I500T figures nor optional plate frequency is a
release criterion.

No full build/check.sh, KiCad CLI DRC/ERC/export, GUI, canonical save or git mutation
was run. Native functions partly reuse production check logic; independent
comparisons/calculations and coverage limits are explicit in JSON. No complete
100-pin mux/source rederivation, full 2304-case rerun, live 82-code supplier refresh,
assembly-PDF visual review or physical/firmware test is claimed.

The full 14/15 same-board review pair, dated owner deviation acceptance, stock/process/
quote resolution and fresh pre-order supplier data remain required. The recorded
placed model is $82.6458 versus $84.41; minimum purchases are $84.9862, with R430/U4 short.
No R10 acceptance, order, firmware, physical or first-article approval follows.
