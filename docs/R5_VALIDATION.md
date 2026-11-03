# R5 independent CAD validation and repair

Review started 2026-10-12. Target: GitHub `m3-assy-r5`, latest verified commit
`2054863083d19c4c45693096b69f467a6d2d2706`. The local R5 checkout matched it with no initial changes.
The older PCB checkout in the parent rocket project contains R4 and is not this review's target.

**Status: fourth CAD implementation and independent revalidation complete; hardware qualification remains open.** Three independent reviewers examined electrical design, actuator safety, and manufacturing/mechanical design before implementation. The four iterations below close the documented CAD repairs and fabrication-file defects. Residual supply, EMC, thermal, mechanical and assembly qualifications are listed explicitly; clean design rules do not establish a flight-ready board.

## Baseline evidence

Native PCB SHA-256: `af78e62a67578d1b5b88ad99214533211f1699613e83482a32472533ae581e59`.

- KiCad 10.0.6, `tools/check.sh`: DRC 0, unconnected 0, schematic parity 0, ERC 0;
  refilled audit OK, inputs unchanged, silkscreen-outline check OK. A sandboxed refill crashed inside
  KiCad; the complete read-only gate passed outside the sandbox. The crash is not a board finding.
- `m3_design/check_actuators.py`: pass. Independent topology inspection confirmed ARM breaks,
  channel separation, reset-state gate networks, split sense dividers and ADC series resistors.
- `tools/fit_check.py`: pass under the stated model/envelope assumptions. C84 margin 0.11 mm,
  mated J122 0.71 mm, bottom parts 2.34 mm. Actual sled fit is unmeasured.
- `tools/dc_solve.py --grid 0.1`: RAW_ACT Q121 to J122 4.82 mΩ, 37.1 mV and 0.286 W at 7.7 A.
  This is a DC copper calculation, not thermal qualification.
- Existing quality-tool tests: 12 passed. No firmware or physical test was performed.

## Findings and closure evidence

| ID | Severity | Finding | Current disposition |
|---|---|---|---|
| R5-V01 | Major | Remote bypassing: U10 IN nearest bulk 8.67 mm, 100 nF 11.85 mm; U11 RAW_PROTECTED / IN2 19.58 mm, USB_LIMITED / IN1 34.63 mm, OUT 8.46 mm. TI calls for local bypassing. | Closed in the first CAD repair: C83/C86 moved opposite U10, C97/C98/C99 added near U11; bulk retained. Full gate and independent electrical review pass; see iteration evidence below. |
| R5-V02 | Major | U12 VCCA at (41.55,34.55) is 15.397 mm from designated C90; nearest 3V3 capacitor is 9.414 mm away. Low baud rate does not remove fast edges. | C100 (existing qualified 100 nF 0402 part) added opposite U12; C90 retained. Closed: full gate and independent placement/routing review pass; the tiny route jog is removed. Its remaining acute join lies wholly within a 0.6 mm via. |
| R5-V03 | Major robustness gap | QSPI_IO2 B.Cu (25.7,39.1) to (25.7,33.3) passes between Y1's pad columns. | Closed geometrically: IO2 now avoids Y1, with local return vias. Independent review and native gate pass; all four data paths, including used barrel depths, span 9.399 mm. Impedance and operating timing remain qualification items. |
| R5-V04 | Major robustness gap | U4 has component-side GND tracks within its MEMS footprint. U5 has SDA and GND tracks between pad rows. ST/TE excludes these routes. | Closed in CAD: U4 uses uniform 0.2 mm straight outward leadouts; U5 has no between-row crossings. Physical duplicate-land continuity independently checked. New native track keepouts reject seeded regressions. |
| R5-V05 | Major | Saved Gerbers differ from fresh export on all four copper layers, F.Mask, F.Paste and both silkscreens, after removing timestamps. | Closed on the fourth-pass board: 84 BOM lines, 209 placements, all 14 archive members independently match native export, and 150 source inputs/five output hashes verify. |
| R5-V06 | Medium assurance error | Checker and R4 notes claimed GCJ soft termination guarantees open failure under flex. Murata describes reduced risk, not fail-open. | Claim corrected. C128/C140 shorts still bypass their FET; pre-arm cold tests detect an existing fault, not one arising after arming. |
| R5-V07 | Medium validation gap | CPL checker accepted a missing MCU, duplicate headers and a source footprint with zero matched MCU pads; it skipped nine placements. Exporter allowed unverified orientations. | Inventory/duplicate/side/position/rotation checks added for all rows, independent pad coverage enforced; exporter rejects missing codes/corrections. 17 regression tests pass; an independent reviewer re-seeded duplicate headers and missing MCU pad numbers and confirmed both fail. Final CAD/output regeneration also passes R5-V05. |
| R5-V08 | Minor | Thirteen bottom courtyard pairs violate the documented extra 0.3 mm spacing, though none overlap; minimum C73–U7 0.06 mm. | C73 and Q120-region spacing repairs independently pass. Actual Q120–C120/R120 gaps are 1.398/1.291 mm. Other courtyard exceptions have adequate body/land gaps. The extra courtyard gap was an engineering target, not a universal assembly rule. |
| R5-V09 | Minor | Parent VEHICLE.md specified four supports; current R5 requires five. | Corrected to five, including (4,46). Physical sled remains unverified. |
| R5-V10 | Minor robustness improvement | SERVO4_OUT is 0.1875 mm from four hand-soldered RAW_ACT pads. Moving it alone collides with SERVO2_MCU. | Closed: joint SERVO4/SERVO2 routing gives 0.3125 mm to each RAW_ACT pad, 0.1625 mm between traces and 0.165 mm to signal pads. Independent geometry and native DRC pass. |
| R5-V11 | Traceability gap | 116 of the original 205 fitted footprints lack Manufacturer Part, including U1; LCSC codes exist. | Closed: verified identities filled 468 fields across 14 files after capacitor additions. Every other parsed CAD field preserved; repeat fill changes zero fields. Completeness gate and 19 quality-tool tests pass. |

The final annotation and route-fragment findings are closed in the fourth pass below. Remaining return-path, decoupling, harness and temperature compromises require qualification; historical acceptance notes are not physical evidence.

## First implementation and independent revalidation

Native PCB SHA-256: `60154e04494152ebccd145a305a99973d348a839c1bfee701292e85e04662a50`.
235 footprint positions; 208 fitted parts (92 top, 116 bottom). C97/C98 reuse the existing 1 µF 25 V
X7R part; C99 reuses the existing 100 nF 50 V part. C28/C82/C6/C7/C84 remain.

- Fresh full gate: DRC 0, unconnected 0, parity 0, ERC 0; refilled metadata/model audit and silk check pass.
- Actuator contract and modeled fit pass; worst bore margin remains C84 at 0.11 mm.
- Independent electrical review confirms capacitor nets, values, schematic wiring and local ground ties.
  Conservative drawn supply lengths are C83 4.67 mm + one via, C86 3.90 mm + one via, C97 3.07 mm,
  C98 6.33 mm and C99 4.02 mm + one via. These are distinct from straight pin-to-pad distances.
- Rebuilt package: 84 BOM lines, 208 placements, no missing codes or corrections; 199 rows have independent
  pad reconstruction and nine have explicit placement checks. Manifest covers all five release outputs. An independent native re-export matches all 11 Gerbers, both drill files and the job file, ignoring creation timestamps only.
- Refreshed public supplier snapshot: no shortage for five boards; U4 stock is exactly five. Parts and
  Standard feeder fees total $80.04 per board against the $84.41 target (PCB/rails/shipping excluded).
- Manufacturing regression tests: 17 passed; quality/metadata tests: 19 passed; actual repeated identity
  fill: zero changes. Native top/bottom 3D renders inspected; Computer Use was unavailable in this session,
  so no GUI interaction check is claimed.

C73's spacing repair also passes refilled DRC/parity, fit, actuator checks and independent
geometry review: C73 shifts 0.6 mm right, U7 separation becomes 1.15 mm, bore margin 2.96 mm and nearest
through-hole pad-to-courtyard gap 1.93 mm. This is now integrated with C100 in the second iteration below.

## Second implementation and revalidation

Native PCB SHA-256: `5993ff5875058f4238d90886a658758168472b8f8d4c870efc6bc780947df171`.
236 footprints; 209 fitted parts (93 top, 116 bottom). C100 adds a local 100 nF bypass at U12 VCCA;
its source branch is 2.45 mm plus one via, and its ground trace is 0.78 mm to a dedicated nearby via.
C90 remains. The independently reviewed C73 spacing repair is integrated.

- Full native gate again passes DRC/opens/parity/ERC at zero, metadata/models and silkscreen checks.
- Actuator contract, modeled fit and zero-change repeated metadata fill pass.
- Visual review caught C97/C100 symbols overlapping sheet notes, which ERC did not report. C97–C99
  moved to a clear row at y = 152.4 mm; C100 moved to y = 165.1 mm. The two changed sheets are stamped
  R5 / 2026-10-12. ERC remains zero and both re-rendered pages are clear. Replay payloads match these positions.
- At this iteration, the fabrication package and stock/cost snapshot still bound the first iteration. The fourth pass below supersedes both.

## Third implementation and independent revalidation

Native integrated PCB SHA-256: `da9abbba78c015dc1d9a0681e39740f7fc4d515fb349474b7a04f9a64e5fc347`.
236 footprints / 209 fitted parts remain. This historical snapshot contains the reviewed routing, spacing and sensor-land repairs. Annotation and leftover-route work was completed in the fourth pass below.

- U4/U5 internal routes are removed. Every connected U4 pad starts with a straight outward 0.2 mm trace; no central copper intrusion remains. U5 duplicate lands have real copper connections, independently checked beyond netlist equivalence.
- C121 shifts 0.3 mm right. Local MOSI and PYRO1_CONT detours preserve widths and connectivity; independent modeled fit passes. C100's route is simplified.
- QSPI_IO2 avoids the crystal. C14 rotates in place with local supply and ground connections preserved. All six QSPI nets remain connected. Data lengths including used barrel depth are IO0 27.636602, IO1 30.087354, IO2 37.035882 and IO3 27.827556 mm, span 9.399280 mm. This conservative matching target does not establish 50 Ω impedance or interface timing.
- C120/R120/TP121 move to clear Q120. The corrected gate branch has no exposed acute junction. SERVO4 clears all four RAW_ACT header pads by 0.3125 mm.
- U4's 14 lands and exported mask/paste flashes independently match the new geometry. Copper gap is 0.150 mm, mask web 0.100 mm and mask-to-unrelated-copper clearance at least 0.175 mm. The land width follows ST; reduced mask relief follows current JLC multilayer LDI capability, rather than ST's nominal +0.05 mm relief. Preserve the supplied mask and paste apertures.
- Native no-track regions protect the IMU's central body and the barometer's between-row space. Both seeded forbidden tracks produce `items_not_allowed`; the unseeded integrated board passes.
- Guarded replay was independently tested against missing/modified/duplicate objects, partial states, regenerated UUIDs and native KiCad serialization. Overlapping edits are composed into one patch so repeated replay is safe. No git restore, commit or push was run.

## Fourth implementation and independent revalidation

Final native PCB SHA-256: `6fc208d613dc2c1a6e9381ec3e1a5888c223ea6246336ae8320421272ca93a43`.
236 footprint positions; 209 fitted parts (93 top, 116 bottom). This is the current snapshot; the three earlier hashes above identify historical iterations.

- **Final native gate:** DRC 0, unconnected 0, schematic parity 0, ERC 0; refilled metadata/model audit and silkscreen-outline check pass. Durable evidence: [r5_review.json](../m3_design/assembly_review/r5_review.json), [r5_audit.json](../m3_design/assembly_review/r5_audit.json), [drc.json](../m3_design/assembly_review/drc.json) and [erc.json](../m3_design/assembly_review/erc.json). The actuator contract and modeled fit pass; repeated metadata fill changes zero fields.
- **Annotations:** five native objects changed without copper changes. The switch legend now reads `J1 SW 3-4` on the bottom at (9.7, 5.1), 90°; J1's reference is at (7.7, 5.5), 90°. Obscured U1/U3/J3 references are hidden and retained in fabrication documentation. C99/C100 were already hidden by the bypass repairs, bringing the total from 78 to 83. Independent body/pad/edge clearance review passes. R32, R81, TP122 and BAT+/GND historical defect claims were disproved on the native geometry.
- **Route fragments:** eight redundant segments removed and one trimmed, with independent connectivity/geometry review and native checks passing. The USB_DM fold provides a required layer transition and was not demonstrated to be an unused stub.
- **Reproducibility and checks:** `r5_repair.py`/`.json` now record bypass additions, placement, routing, sensor lands and keepouts, labels and fragment cleanup. Guarded scoped replay preserves unrelated objects and rejects incompatible/partial state. Native CAD is authoritative; the full destructive R4 rebuild was not run. Replay tests: 13 pass; fabrication tests: 17 pass; quality/metadata tests: 19 pass.
- **Fabrication:** regenerated 84-line BOM and 209-row CPL; 200 placements have supplier-pad reconstruction and nine have explicit placement-only checks. Independent review verifies all 150 source inputs and five outputs in the manifest. All 14 Gerber/drill/job archive members match fresh native export, ignoring timestamps only. CLI board/schematic/assembly renders were reviewed; native GUI interaction was unavailable. The assembly PDF export now uses a clear black-and-white, automatically scaled page without the overlapping drawing frame.
- **Cost/stock snapshot (2026-10-12):** $55.26 parts per board rounded; unrounded parts plus Standard feeder fees give $80.05 per board for five boards, excluding PCB/rails/shipping and the separately listed fixed fees. There are 81 supplier codes, 47 extended codes and no shortage; U4 stock is exactly five for five boards. Recheck stock before ordering.
- **Panelization:** exact 5 mm tab windows in KiCad coordinates are X = 0, Y = 45–50, 71–76 and 78.5–83.5 mm; X = 46, Y = 43.75–48.75 mm. Independent geometry review passes across all 236 pad/courtyard envelopes, closing the CAD tab-location finding. Production-panel approval must reproduce these windows and keep actual mouse-bite hole edges at least 0.50 mm from copper on every layer. For Ø0.60 mm holes, centers must lie at least 0.30 mm outside the finished board in sacrificial tabs; no on-edge centers. Supplier rail/support review remains required (ORDERING).

No git action or fabrication order was performed. The current checks establish consistency of the reviewed CAD and manufacturing files; they do not establish physical reliability.

## Remaining qualifications

| Item | Current evidence and required qualification |
|---|---|
| Flash bypass | C29 100 nF is 5.872 mm from U3 VCC; C9 bulk is 3.11 mm away. This remains an unqualified supply-noise/timing compromise. The previous “slow or current-limited” rationale is invalid for flash edges. Measure supply droop and read/write integrity at the intended clock during buck, servo and camera activity. |
| Bulk return paths | C150/C151's nearest GND vias are 4.333/3.094 mm away, not 6–8 mm; C121's is 1.179 mm. Check RAW_ACT ripple and load transients. |
| Camera supply | The 78.33 mm × 0.4 mm trunk is approximately 0.096 Ω: about 0.12 V drop and 0.15 W at 1.24 A. These are DC estimates, not a verified temperature rise. Measure camera voltage and copper/via temperature under load. |
| Return paths and harness coupling | IMU_INT1 return vias are 1.812/1.518 mm from its two transitions. Other inherited reference-plane transitions and long servo cable-side traces remain EMC/sensor-noise and armed dummy-load qualification items; nominal bus/PWM frequency does not qualify edge behavior. |
| MCU-side pyro vias | The vias near bottom parts are tented, not exposed copper. The sub-1 mm spacing remains an L10 engineering exception, not a demonstrated solder-bridge defect. Coating, contamination control and the existing armed/cold/dummy-load gates still apply. |
| Mechanical and assembly | Five nylon supports/washers, non-conductive sled clearance, connector/tie retention, shock/vibration, sensor offset/noise, sensor land/mask/paste and reflow sequence need physical qualification. Confirm MS5611 tolerates the two planned reflows. |
| Power and firmware | Servo stall/neck thermal tests, reverse-hot-plug and USB/switchover tests, coating/retention, R5 firmware binding, IMU axes, reset/watchdog behavior and complete REQUIREMENTS/ORDERING bench gates remain open. No fabricated R5 or physical results are available. |

## Additional electrical verification

An independent second electrical pass found no new pin/topology defect: all 14 U4 Mode 1 nets,
U5 I2C straps/address, and STM32 supply/reset/clock, QSPI, SPI1, I2C1, USART3, USB and SWD
assignments agree with manufacturer pin tables. A later sensor-land review confirms U5 exposed copper, mask and paste match TE’s 1.10 × 0.60 mm lands and 2.20 mm row spacing. U4 now uses ST-derived 0.575 × 0.35 mm lands. The +0.025 mm mask relief is a documented JLC multilayer LDI adaptation, giving a 0.100 mm web; paste coverage remains 88.36%. Fresh Gerbers and all 14 pad identities independently pass. Physical reflow qualification remains open.
Historical notes that treat 7.3 V as a general FT-pin rating are superseded: current DS12110 caps
FT digital input stress at 6 V and normal operation at 5.5 V, subject to the supply/mode-specific
conditions. ADC pins require their analog limits. No new actual pin-overvoltage defect was demonstrated.

A separate power-corner pass found no new proven CAD defect beyond the bypass findings then open (now repaired as recorded above). U9/U10/U11
limit resistors and U9 OVLO agree with their datasheets; the AP63203 output network and STM32
VDD/VDDA/VREF/VCAP bypass networks match the checked recommendations. U9 reverse-hot-plug qualification
now explicitly measures OUT − IN ≤ 21 V at −20 °C as well as IN ≥ −15 V and falling slew ≤ 10 V/µs
([TPS25947 Rev C §6.1](https://www.ti.com/lit/ds/symlink/tps25947.pdf)). These checks do not establish
actual transient, DC-bias, pulse-endurance or temperature margins without the hardware tests.

## Manufacturer evidence

- [TI TPS2553](https://www.ti.com/lit/ds/symlink/tps2553.pdf), §§10.2.1.2.4 and 12.1: local bypassing.
- [TI TPS2121](https://www.ti.com/lit/ds/symlink/tps2121.pdf), §11: capacitor placement.
- [TI TXU0202](https://www.ti.com/lit/ds/symlink/txu0202.pdf), §12.1: bypass both supplies.
- [ST AN2867](https://www.st.com/resource/en/application_note/an2867-oscillator-design-guide-for-stm8afals-stm32-mcus-and-mpus-stmicroelectronics.pdf), §7.1: oscillator layout.
- [ST TN1383](https://www.st.com/resource/en/technical_note/tn1383-pcb-design-guidelines-for-mems-sensors-stmicroelectronics.pdf), §§3.2–3.5: MEMS routing.
- [TE MS5611-01BA03](https://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocLang=English&DocNm=MS5611-01BA03&DocType=Data+Sheet), page 16: no tracks between pads.
- [JLC current PCB capabilities](https://jlcpcb.com/capabilities/pcb-) and [mask process](https://jlcpcb.com/blog/basic-design-of-solder-mask): multilayer LDI, mask webs and aperture clearance.
- [Murata GCJ](https://www.murata.com/en-sg/products/capacitor/ceramiccapacitor/overview/lineup/smd/gcj): resin terminations reduce cracking/short risk.

## Iteration requirements

After edits: fresh refilled DRC/ERC/parity, actuator contract, modeled fit, independent review of changed
circuits/routing and relevant requirements. Regenerate BOM/CPL/Gerbers/assembly drawings; verify full
placement inventory and orientation, then the source/output manifest. Recheck cost/stock if parts change.
Keep schematic, native board and any reproducible repair script synchronized.

The objective is not complete while CAD findings remain open. CAD checks cannot substitute for physical
sled/harness, reflow qualification, thermal/stall, hot-plug, oscillator/sensor, armed dummy-load, ESD,
coating/retention and firmware gates in REQUIREMENTS and ORDERING. No fabricated board, R5 firmware
binding, or physical results are available in this checkout.
