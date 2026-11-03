# Round 11, lens 1: requirements and every owner decision

Target commit supplied by orchestrator: `21bc3b2`. Native PCB independently read as SHA-256
`0c50b9fd0930f34edab7129fc21b8e71d0ee03bc079e1900b7e131cece6bfaf8`, 2,245,484 bytes,
46 × 90 mm, 209 footprints, 981 track segments and 294 vias. Review is read-only except this report.
No other round-11 lens report was read. No Git operation, direct KiCad CLI, build-service request,
CAD save, other-worktree edit or implementation edit was performed.

**Result: 0 Critical, 0 Major, 3 Minor groups.** R11-REQ-01 is an independently measured calculation
refresh; R11-REQ-02 is current-record drift; R11-REQ-03 is a read-only external-document follow-up.
Existing adopted architecture risks and explicitly unverified physical/firmware obligations are inventoried
below and are not counted again as newly discovered defects. None of these findings changes AGENTS §2.

## New findings

### R11-REQ-01 — Minor — final fire-current calculation still uses pre-relayout copper

Evidence: `m3_design/r10_parts.py:333–338` labels its hard-coded paths “final AUD/GAP CAD path lengths”.
`parts_budget.json:275–307` under `sources/r10_design/` still gives those lengths; `parts_qualification.md:268–272`
 calls them “final recorded CAD tracks” and explicitly requires remeasurement when the paths change.
`docs/REQUIREMENTS.md:58` F7 and `docs/M3_R10.md` current fire budget repeat the resulting currents.
The AVA layout moved Q120/Q121 and redrew the R134 feed, so the old path numbers are no longer board-bound.

Native track inventory, pruning non-fire dead ends using the named S-9 terminal pairs:

| Net / path | Recorded length / width mm | Current length / width mm | Current endpoints / useful vertices mm |
|---|---:|---:|---|
| BAT_IN J1.1 to Q120 drain | 7.121320 / 1.0 | 6.000000 / 1.0 | B.Cu (7,74.1) to (13,74.1) |
| ACT_FET_S conservative one-branch bound | 2.200000 / 0.4 | 2.200000 / 0.4, unchanged | Source-leg geometry translated +1 mm; retain the existing conservative bound without parallel credit |
| RAW_ACT Q121 drain to R134.2 | 6.500000 / 0.5 | 5.886133 / 0.5 | B.Cu (14.475,67.105) → (17.58,64) → (19.075,64) |
| PYRO1_IGN R134.1 to J121.2 | 4.850000 / 0.5 | 10.396068 / 0.5 | B.Cu (13.925,64) → (12,64) → (7,59) → (7,57.6) |
| PYRO1_OUT J121.1 to Q124 drain | 7.954478 / 0.5 | 7.954478 / 0.5, unchanged | F.Cu (7,54.1) → (10.33,54.1) → (11.33,55.1) → (13.6,57.37) |

Using the existing resistivity 1.72e-8 Ωm, 35 µm thickness and 0.00393/K TCR, current conservative
track resistance is 29.472622 mΩ at 20°C and 35.263992 mΩ at 70°C; recorded values are 25.176022 /
30.123110 mΩ. Preserve the existing R134, hot-FET, GND/contact, match/harness and source allocations.
The updated fire branch excluding pack is 4.467589992 Ω. Independent quadratic source/load solve with
12.370806905 W converter load, 7.4 V equivalent source and 0.15 Ω pack gives 1.544322 / 1.479396 /
1.414223 / 1.348767 / 1.282976 A for zero through four persistent 1.92 A servo stalls. The lowest case
still exceeds the adopted 1.125 A floor by 0.157976 A. These are Calc / Inference, not measured currents.

Concrete fix: update the generator to derive or explicitly bind these five current-path allocations to the
saved board, regenerate `parts_budget.json`, and refresh active F7 / qualification / revision / binding
obligations that quote the resulting figures. Keep historical named-board figures historical. No PCB change,
R134 change, all-fire relaxation or owner question is needed. The power lens was notified for independent verification.

### R11-REQ-02 — Minor — a few active requirement/plan paragraphs contradict the current layout

Evidence and measured reason:

- `docs/REQUIREMENTS.md:104`, accepted-risk “Harness miswiring”, says camera J9 “is now keyed GH”.
  Native J9 is `DB125-3.5-4P-GN-S`, F.Cu (39,47.5), +90°, with CAM_5V/GND/CAM_RX_WIRE/CAM_TX_WIRE
  on pins 1/2/3/4; it is unkeyed. F8 at line 59 and ORDERING's current amendment correctly describe it.
  Scope the older keyed-GH mitigation to R6–R9 and retain the current all-terminal pin/polarity checks.
- `docs/M3_R10.md:120–127`, the unqualified Placement section, still says radio is parked west and the
  AVA pass is future. Native J420 is F.Cu (39,31.5), +90°; the six other terminals already form the
  completed rows. Replace the paragraph with D-AVA-01 / AVA_LAYOUT's actual row coordinates or mark it historical.
- `sources/r10_design/r10_plan.md:5` calls `6e73b6eb…` the “Current board” and says layout is pending.
  The native board is `0c50b9fd…`; preserve the circuit-pass block as history and add the completed AVA candidate.

This is record drift, not a missing connector, missing relayout or unauthorized loss of keying. The newest
owner decision, native CAD, current F8/F10/P2 and AVA_LAYOUT already agree. Explicitly historical ORDERING §8
snapshots (the supersession begins at lines 220–245) and the old deviation list are not promoted to standalone
Majors; their final refresh is already part of this task. Low-risk fix scope is documentation only.

### R11-REQ-03 — Minor — parent vehicle mirror still describes removed hardware

Read-only evidence: parent `docs/VEHICLE.md` main-section-stack row, line 39, still describes R10 GH-4
ports, an ARM terminal, GH-2 J400 at (10.5,85.5), and 0.03 mm mated-GH bore margin. Native J124 is absent;
J400 is a 2-position DB125 at (7,65.85), −90°; every wired connection is DB125. The parent paragraph correctly
retains 46 × 90 mm, five supports and OQ-7's forward-of-joint+47 mm rule. `docs/M3_R10.md:466` already
acknowledges part of the stale mirror. This reviewer did not edit another worktree.

Concrete in-worktree handoff: “R10 candidate 0c50b9fd… is 46 × 90 mm, five supports unchanged, no RF/SMA
overhang. West outward-facing terminal centres x=7: IGN y55.85, SWITCH y65.85, BAT y75.85. East centres
x=39: GPS y15.5, RADIO y31.5, CAM y47.5, SERVO y71.5. All seven are DB125 3.5 mm; J124 and GH envelopes
are absent. J122 has four signals plus shared GND, motor power/return in pack-star harness. Keep the board
aft edge plus axial tolerance wholly forward of joint+47 mm; fitted harness, screwdriver, card, sled and
stack remain physically unverified.” Record this external follow-up in the final deviation list; do not edit
the parent worktree under the current task's explicit prohibition.

## Direct native-CAD checks

PCB and stored XML were parsed independently of saved gate summaries. All 100 U1 table rows agree with both
native PCB pad nets and `schematic.net.xml`; zero mismatches. Selected parts and nets were inspected individually:

- U4 B.Cu (17,45.9), 180°; the transverse centreline x23 gives lever x−6 mm. Its SPI, IMU_INT1, 3V3A and GND
  pins agree with the reviewed table; no pose change is inferred. Actual signed-axis qualification is still bench work.
- J410/J420 pins 1 PORT_4V8, 2 GND, 3 board TX, 4 board RX; J9 pins 1 CAM_5V, 2 GND, 3 board RX, 4 board TX.
  The different UART order is intentional and every terminal must be checked end to end.
- J122 exactly five pins: SERVO1_OUT through SERVO4_OUT and GND. R150–153 each 1 kΩ; R154–157 each 10 kΩ
  to GND; D121 retains all four MCU-side channels, 3V3 and GND. No designed motor feed exists at J122.
- J400 has only BAT_SW_SOURCE / BAT_SW_RETURN. R80 and R165 are 470 kΩ, R81 300 kΩ, C87 2.2 µF.
- Q120: drain BAT_IN, source ACT_FET_S; Q121: source ACT_FET_S, drain RAW_ACT. R134 is 2 Ω from RAW_ACT to IGN.
  PC1 ACT_EN_MCU reaches R122 1 kΩ / Q122; R123 100 kΩ holds ACT_EN low. PE4 independently reaches R126 220 Ω;
  PYRO1_GATE retains C126 220 nF and R128 10 kΩ to GND. J121 remains black and battery green.
- ARM1_SENSE reaches PC5 and continuity reaches PC0 directly; two top resistors / two lower parallel legs and
  10 nF remain per bank. PB0 and PC13 are NC. Single-fault ratios remain the adopted two-bank calculation;
  no fault-injection or physical waveform claim is added by topology inspection.
- J430 B.Cu (24,24.3), 0°, value 472192001. Pins 1 DAT2, 2 CS, 3 MOSI, 4 3V3, 5 SCK, 6 GND, 7 MISO,
  8 DAT1; shield 9–12 GND. C460 100 nF / C461 22 µF and data/CS pull-ups exist.
- Removed refs absent: J123/J124, U30/U31/J30/J31, U410/U420/U411/U421/U412/U422, R168/R170,
  R177/R124/R125/R182/R172/C122, TP84/85/86/87/89/92, C121/C150/C151.
- Retained U9/U10/U11, U400/U401 and camera U402/U12/U13 match the adopted source and port architecture.
  U401 remains B.Cu (27.6,13.6), preserving the exact VIPPO coordinates. No new electrical qualification is inferred.

## Functional, physical and manufacturing requirement coverage

| Requirement | Traceability result / remaining obligation |
|---|---|
| F1/F2 | LSM6DSV320X retained; ±4000 dps / high-g capability is the existing maker-qualified choice. Current Mach1.45/1.9 trajectory, sensor accuracy/high-g/vibration/clipping and ≤5° integration error remain unqualified, expressly open. |
| F3 | MS5611 retained; transonic estimator, venting, opaque foam/light and coating exclusions are retained. No installed cover test is claimed. |
| F4 | Four protected 3.3 V PWM lanes and five-pin terminal verified; 333 Hz, neutral-first behavior, harness current/retention and hinge loads require firmware/bench work. |
| F5 | QSPI retained plus SPI3 hinged microSD; native pin map/pulls/bypass agree. Whole-flight storage, ≥800 Hz sample / 500 Hz log, latency/buffering/power loss, current and ≥25% throughput margin remain unimplemented/unverified. |
| F6 | EN bounce hardware retained; always-on ports cannot be shed. C84, PA6 watchdog obligations, 20/36 ms current and ≤50 ms neutral-command allocations remain separate conditional/bench obligations. No physical battery-break immunity is proven by the CAD. |
| F7 | Post-load-switch/R134 topology intact; native final-current calculation discrepancy is R11-REQ-01. Updated conservative corner still passes1.125 A. Selected-lot20 ms firing, actual source/harness/copper and reserve stay open. |
| F8 | Single switch, separate PC1/PE4, direct single-safe split dividers, no ARM/pull-pin, ground refusals/in-flight never-veto and mandatory coating preserved. Firmware/ground thresholds and fault waveforms absent by declaration. |
| F9 | U9, USB limiter/mux, C84 and no pack fuse agree with owner decisions. Actual-feed hot-plug evidence is current-board-bound; physical IN/OUT, harness≥0.03Ω/0.1–2µH, damper durability, dry screw contact and back-feed/short tests remain open. |
| F10 | No on-board RF; external GPS/radio and retained camera isolation verified. Direct UART/FT operating limits, manual radio channels12–25 or maker-confirmed hop set, no RF arming/fire, installed RF/ESD testing remain obligations. |
| P1 | Native board46×90 mm≤120; no RF overhang. No shorter-board claim substitutes for complete bay fit. |
| P2 | Five supports and no servo-tie holes retained; OQ-1's bare-bore4.95 mm method and OQ-7 placement explicitly conditional on fitted harness/card/tool/sled/stack checks. Parent mirror discrepancy is R11-REQ-03. |
| P3 | Staking all DB125s/C84/LS120/J3, MEMS exclusion, mandatory coat, J2 cover, NRST≥0.90×3V3/250kΩ and 500g-equivalent retention assertion remain qualification instructions, not inspection passes. |
| M1 | Same4-layer1.6mm/1oz stack and ENIG/Standard assembly; exact two U401 VIPPOs and post-reflow manual C84 are quote/process conditions. Stock/consignment and factory preview remain open. |
| M2 | Hand-drawn generators, no board edit; critical allowlist empty. AVA handoff records12 noncritical leftovers,27 inside-pad segments,2 collinear nodes and hidden references for final inventory; fast returns/safety/DRC remain blocking. Owner deviation acceptance remains pending. |
| M3 | R10 cap$84.41; Extended count informational. Last circuit snapshot$82.59 excludes fixed/PCB/shipping and carries R430 minimum-purchase/U4 shortage caveats. New quote/stock and minimum/consignment cost must qualify before order; historical$84.43 miss is not current proof of a miss. |

## Every owner decision and amendment

Later amendments govern; the original requirement is not silently treated as current after its explicit replacement.

| Owner choice | Current disposition / concrete evidence |
|---|---|
| Original two-flight/one-board goals, roll burn+coast, integrated angle, neutral on fault, four-servo limit, no tab sensing | REQUIREMENTS sources/F1–F7 retain them; no flight or firmware qualification is claimed. Independent Blue Jay remains electrically separate. |
| O1 | GPS off board; native U30/J30 absent, J410 DB125 external always-on port. L5 loss and installed module/antenna obligations disclosed. |
| O2 | Radio off board; native U31/J31 absent, J420 DB125, UART5 PB13/PB12. Band/uplink/RF restrictions preserved. |
| O3 | Servo motor power/return external; native J122 signal/GND only. Lost board power cutoff is explicitly a deviation. |
| O4 | Regulated camera supply retained: U400→U402→CAM_5V, U12/U13 isolation retained. |
| O5 | Separate5.456V buck/4.792V LDO retained; later always-on decision removes GPS/radio switches only. Camera switch retained for its back-feed path. |
| O6 | Pack-star motor returns retained, reference-current bound0.6144A conditional on≤1mΩ star/≥50mΩ branches. Shared J122 GND does not establish a measured zero current; harness qualification remains. |
| No pyro-specific surface rules | Default0.15mm is intentional; S-8≥1mm foreign inner-copper exclusion, functional gate/sense rules and mandatory coat remain. Surface single-defect losses stay on deviation list. |
| D-R2-04 / D-R2-08, routing policy | Critical then every signal hand-drawn; production sources are explicit polylines, historical router aid not a production stage. |
| OQ-1 | Accepted4.95mm wire-room floor; current seven-terminal layout records4.953mm. Physical16–22AWG dress remains unverified. |
| OQ-2 | Actual-feed re-model/remediation implemented; C88-before-U9, R92=3.3k/R166=0.36Ω retained, schema3 inputs/results identify current PCB. Simulation is not a measured guarantee. |
| OQ-3 | Historical miss does not block clean rounds; cost/stock and actual owner-paid quote still required. No acceptance inferred. |
| OQ-4 | Aft-edge tab/rail retained rather than moving port row. JLC process/panel acceptance remains before order. |
| OQ-5 | Keep C84/no hardware cutoff. Latest always-on GPS/radio removes their software shedding, and updated F6 states shorter loaded ride-through. Camera/logic shedding and latency remain bench obligations. |
| OQ-6 | No battery-lead fuse, superseding earlier≤10A choice; hard pack-side shorts remain accepted risk with harness mitigation. Later single switch also removes ARM-link fuse. |
| OQ-7 | Entire board incl. axial tolerance forward of joint+47mm; no shroud clocking choice remains. Physical fit open. |
| Single screw switch | J124/ARM/fuse removed; PC1 independently enables load switch, PE4 fires; both externally low/reset-safe. On-rail/on-last/off-first and no-back-feed e-match rule retained. |
| AUD-1 | Surviving camera IO C92=4.7µF C19666, inferred2.211µF effective against1.5µF maker requirement. |
| AUD-2 | Named slow nets only leave partner/reference rules; fast interfaces/S-8/hygiene retained. |
| AUD-3 | Q120/Q121 AONR21357, exact AOS land; C120 now1µF25V and≥100ms enable settling. Hot SOA/waveform claims remain conditional. |
| AUD-4 | Complete pull-pin removed, PC13 NC; independent acceleration+barometer launch detection preserved. |
| AUD-5 | Selected probes removed; necessary supply/pyro probes retained. |
| AUD-6 | Fire-only0.5mm with exact source bridges; no continuous-current claim. |
| AUD-7 | Ordinary pull-up families; servo1k0603/100mW and72mW chafe calculation retained. Removed GPS/radio controls do not survive as required hardware. |
| AUD-8 | GPS/radio IO-LDO removal is superseded by complete translator removal; camera U13/C92 remains. |
| AUD-9 | U10/U11 USB-only bench power retained. |
| AUD-10 | Only exact harmless representations/distance reviewed; electrical connectivity/clearance/fast-return blocks remain. |
| GAP-1 | Selected J-Tek0.75A ×1.5=1.125A; native current geometry refresh R11-REQ-01, lot20ms firing unverified. |
| GAP-2 | Local C82/D9 retained beside U9, original actual-loop gates preserved; no TI numeric loop limit invented. |
| GAP-3 | Exact two U401 thermal vias and mandatory resin-filled/capped/planar VIPPO process retained. |
| GAP-4 | C84 required-fitted manually after both reflows; no borrowed OS-CON profile. |
| GAP-5 |20ms normal incl.tail/36ms intact-hardware watchdog fault guard;≤50ms neutral command; physical response separate. |
| AVA comparison follow-up | Owner explicitly retained single switch despite corrected AVA ARM-terminal observation; duplicate RAW_ACT sense removed; adopt ten layout items without reviving removed sense/port functions. |
| Always-on ports | Native U410/U420/U411/U421 absent; direct1k/ESD UART, no port EN/OE/FAULT/powercycle promise; camera remains switched/isolated. |
| microSD | Native J430 hinged Molex on SPI3, QSPI retained, insertion off/outside bay; card and logging qualifications open. |
| Servo/switch screw terminals and Steer1 all-wired amendment | All seven native DB125s,5P servo/2P switch/4P ports; no GH/header/tie holes. Every pin labelled; clamps28–16AWG, no keying/ferrule/splice/harness qualification disclosed. |
| Audit2 item1 | Duplicate bus bank removed, PB0 NC; PC5 sole bus ADC. |
| Audit2 item2 | R168/R170/tails removed; split tops/parallel bottoms/10nF retained, single-fault3.342171V<4V assumption explicit. |
| Audit2 item3 | ACT_FET_S0.5mm except seven exact0.4mm source legs. |
| Audit2 item4 | Only named low-current resistor taps exempt power-feed width; no load-feed exemption. |
| Audit2 item5 | In1 GND tracks allowed, no foreign-net signal tracks. |
| Audit2 item6 | No209Hz release threshold or mandatory stale plate report; physical retention/fit remains. |
| Audit2 item7 | Count/locate noncritical leftovers once; critical exceptions still measured/blocking. |
| Audit2 item8 | NRST250kΩ/0.90×3V3 with10MΩ powered instrument; unpowered ohmmeter not a substitute. |
| Audit2 item9 | No independent52-Extended cap; actual count and$84.41 cost/stock stay. |
| Audit2 item10 | Redundant walks removed; native fitted population/schematic/BOM/CPL/full DRC/K-actuators remain. |
| Audit2 item11 | Sole full MCU map is reviewed r10_net column; all100 native/XML pins matched independently. |
| Audit2 item12 | Retain actual−6mm axis binding, remove redundant13mm ceiling. |
| Audit2 item13 | Applicable local-clearance floors retained; no DRC bypass. |
| Audit2 item14 | Full check.sh zero before commit, PR summary/evidence and STATUS once/reviewed change; cosmetic hash provenance retained, electrical/axis review when those facts change. |
| Audit2 item15 | Always-on port scope/logging policy carried into current requirements/binding. |
| Audit2 item16 | LED-dark restriction stays until installed opaque-cover/light test passes; no cover test claimed. |
| D-CIR-01/D-CIR-02 | Agent selection J-Tek and≥2.6Ah two-hour pad allocation/≥4Ah continuous-camera case explicitly recorded as conditional; no acceptance or battery-fit claim. |
| D-AVA-01/D-AVA-02 | Current outward terminal rows/local cells, unchanged circuit/pins/supports/IMU; P-11 covers all seven and regression fixtures translate without changing limits. |

## Complete decision-heading census

Read all 1,743 lines of R10_DECISIONS, newest through D-AVA-02, plus AGENTS, REQUIREMENTS, AVA_LAYOUT,
M3_R10, earlier-round validation and the parent vehicle physics. The following is the complete 102-heading
agent-decision index, including suffix IDs. Earlier experimental poses, removed hardware and historical failures
remain superseded by their later owner/AUD/CIR/AVA amendment; they are not silently transferred as current measurements.

| ID | Decision read |
|---|---|
| D-R1-01 | Review the plan before changing CAD |
| D-R1-02 | O1 needs a voltage decision |
| D-R1-03 | Separate camera and radio voltage budgets |
| D-R1-04 | Review concurrency limit |
| D-R1-05 | Baseline environment |
| D-R1-06 | Close round 1 at the owner-decision boundary |
| D-R1-07 | Implement O5 and O6 |
| D-R2-01 | Placement legalised by moves, not rebuilt |
| D-R2-02 | Pyro channel and USB / SWD routing redrawn from the pads |
| D-R2-03 | Port supply re-planned for routability |
| D-R2-04 | Hand-routing kept for critical nets (owner, 2026-10-26) |
| D-R2-05 | U9 cell moved; In2 split into four rails |
| D-R2-06 | Rail fan-out finished; radio UART on UART5 (PB12 / PB13) |
| D-R2-07 | Signal routing: pin re-map, re-placements, hand-routed escapes and a frozen router table |
| D-R2-08 | Owner: hand-route every signal (2026-10-27) |
| D-R2-09 | Placement relieved south and east of U1; three status pins re-mapped |
| D-R2-10 | K-reference re-derived on R10's planes; via inner pads removed |
| D-R2-11 | Copper fixes for K-copper, K-retained and schematic parity |
| D-R2-12 | Placement relief for the supports, J122's pins and the tie channel |
| D-R2-13 | T-1 re-derived for R10 |
| D-R2-14 | P-11 and F9-1: owner questions, R10 figures held meanwhile |
| D-R2-15 | Build and fab scripts |
| D-R2-16 | Silkscreen |
| D-R3-01 | R410 (GPS ILIM) stays 100 kΩ; the port budget re-derived on it |
| D-R3-02 | In2 is GND under the CH1 pyro column (R3-SAF-01) |
| D-R3-03 | U9's power path widened (R3-PWR-01) |
| D-R3-04 | In2 regions re-cut for the port control nets (R3-RTE-01, R3-PWR-04) |
| D-R3-05 | Buck input loop (R3-PWR-05) |
| D-R3-06 | Crystal In2 GND restored (R3-RTE-02) |
| D-R3-07 | Camera supply vias, ACT_GATE partner, J122 relief |
| D-R3-08 | GND stitching (R3-RTE-05) |
| D-R3-09 | Port-signal layer changes and hops (R3-RTE-01, -03, -04, -06, -07) |
| D-R3-10 | Gates |
| D-R3-11 | Silkscreen and footprint graphics |
| D-R3-12 | R162 1 kΩ (PC14's 3 mA) |
| D-R3-13 | Records |
| D-R4-01 | In2 under the CH1 sense runs re-cut to one region (R4-RTE-01) |
| D-R4-02 | Pad entries straightened (R4-RTE-05) |
| D-R4-03 | Gates (R4-RTE-01/-02, R4-GATE-01 … -06, R4-SAF-01/-02, R4-MEC-05) |
| D-R4-04 | Records (R4-REQ-01 … -06, R4-MEC-01 … -04, R4-PWR-01/-02, R4-BOM-01 … -03, R4-MCU-01 … -04, R4-DOC-*) |
| D-R5-01 | In2 edges re-cut for pads, margins and chains (R5-RTE-01 / -02 / -06) |
| D-R5-02 | Pad entries, stubs and silkscreen edge margin (R5-RTE-03 / -04 / -07, R5-MFG-02) |
| D-R5-03 | Gates (R5-RTE-01 / -02 / -05 / -06, R5-SAF-01 / -02, R5-GATE-01 … -03) |
| D-R5-04 | Records (R5-MFG-01, R5-REQ-01 … -04, R5-PWR-01 … -04, R5-MCU-01 … -05, R5-MEC-01 … -05, R5-DOC-01 / -02) |
| D-R6-01 | CH1 In2 GND arms widened round the sense vias (R6-RTE-01) |
| D-R6-02 | Gates and the fit tool (R6-RTE-02, R6-SAF-01 / -02, R6-GATE-01 … -08, R6-MEC-04 / -05) |
| D-R6-03 | Records (R6-MEC-01 … -06, R6-REQ-01 … -08, R6-PWR-01 … -03, R6-MCU-01 … -05, R6-SAF-03 / -04, R6-MFG-02, R6-RTE-03) |
| D-R7-01 | Gates (R7-GATE-01 … -04, R7-SAF-01 / -02) |
| D-R7-02 | Records (R7-REQ-01 / -02, R7-PWR-02, R7-SAF-03, R7-MCU-01 … -04, R7-MEC-01 … -07, R7-MFG-01 … -04, R7-BOM-03, R7-DOC-01 / -02) |
| D-R8-01 | Copper clean-ups (R7-RTE-01 / -02 / -03, R8-RTE-03) |
| D-R8-02 | Gates (R8-GATE-01 … -05) |
| D-R8-03 | Records (R8-MEC-01, R8-MFG-01 / -02 / -03, R8-REQ-01 … -04, R8-SAF-01, R8-MCU-01 / -02, R8-MEC-02 … -05, R8-RTE-01 / -02, R8-DOC-01 / -02) |
| D-OA-01 | Harness, fit and assembly records (OQ-1 / -4 / -6 / -7) |
| D-OA-02 | Firmware shedding and thermal estimate (OQ-5 / R9-PWR-01) |
| D-OA-03 | Historical routing aids |
| D-OA-04 | OQ-2 failure confirmation |
| D-OA-05 | Retained U9 output voltage |
| D-OA-06 | Input feed and damper requalification |
| D-OA-07 | C88 intercepts the feed; local copper remains in the model |
| D-OA-08 | Record corrections before the fresh full round 9 |
| D-OA-09 | Complete the interrupted pass before audit implementation |
| D-SS-01 | Implement the two independent MCU controls in the recorded decision |
| D-SS-02 | One named post-switch net and a shorter fire path |
| D-SS-03 | Keep required assembly references visible |
| D-AUD-01 | Size the surviving IO-LDO capacitor for its electrical load |
| D-AUD-02 | Keep fast returns constrained; simplify slow returns by explicit name |
| D-AUD-03 | Use a qualified smaller post-switch pair |
| D-AUD-04 | Delete the advisory pull-pin as a complete function |
| D-AUD-05 | Remove redundant probe branches |
| D-AUD-06 | Size fire-only copper for bounded pulse energy |
| D-AUD-07 | Use ordinary digital pull-ups and fault-rated servo resistors |
| D-AUD-08 | Share 3V3 for GPS / radio UART IO; retain local bypasses |
| D-AUD-09 | Keep USB-only programming and log download |
| D-AUD-10 | Report harmless drawing artifacts without blocking the electrical gate |
| D-GAP-01 | Superpose all pack loads at the fire instant |
| D-GAP-02 | Make U9's output-protection loop local |
| D-GAP-03 | Add two explicitly manufactured U401 thermal vias |
| D-GAP-04 | Fit C84 after all reflow |
| D-GAP-05 | One physical-current duration contract |
| D-AUD-03a | Correct the retained gate-slew capacitor's voltage rating |
| D-AUD-03b | Verify new assembly orientation against the supplier |
| D-SS-04 | Recalculate passive cold readings before enabling the merged bus |
| D-GAP-01a | Final track-based conservative fire envelope |
| D-GAP-02a | Reject the nearer diode position on measured clearance |
| D-AUD-03c | Match orientation by distinct fingers, not an arbitrary EP anchor |
| D-GAP-02b | Freeze the actual output and return paths |
| D-AUD-01a | Keep one assembly land per supplier code |
| D-R9-01 | Complete existing capacitor labels and use the current fault-delay bound |
| D-R9-02 | Put the cold screen before enabling the bus |
| D-R9-03 | Reject unmeasured gate exceptions and select R10 procurement explicitly |
| D-R9-04 | Remove demonstrated detours and align three supply entries |
| D-R9-05 | Include both transverse sled tolerances |
| D-R9-06 | Cover the Minor fix pass in the fresh round 10 |
| D-R10-01 | Close two representation gaps without changing CAD |
| D-R10-02 | Correct PA6 limits and preserve the barometer coating exclusion |
| D-R10-03 | Freeze the reviewed board and finish the complete acceptance inventory |
| D-CIR-01 | Select the real e-match before choosing the all-fire margin |
| D-CIR-02 | Switched camera pad energy |
| D-CIR-03 | Circuit-pass placement and routing (minimum for a connected DRC-clean board) |
| D-CIR-04 | Gate fixes |
| D-AVA-01 | AVA terminal rows and local cells (2026-10-29; CAD layout complete) |
| D-AVA-02 | Gates and reproducibility support |

## Limits and final-inventory carry-forward

This lens did not run a build/DRC, supplier quote or physical/firmware test; the orchestrator owns current full-gate
verification through the prescribed service. Native KiCad Python loading emitted the known nonfatal wx assertion
and exited0; no CLI or GUI workaround was used.

Retain current-board-bound final deviations for: single-switch/shared-MCU and surface-fault envelope; external servo
power/return/source reserve; unkeyed terminal/UART/back-feed/shared-port-fault behavior; hold-up/hot-plug/thermal/pulse
inferences; firmware/watchdog/storage; every routing residual/hidden reference; harness/tool/card/sled/shroud/retention;
L400/other qualified land compromises; VIPPO/manual-C84/U5 process; cost/stock/quote/panel; historical-source and every
agent-decision applicability. AVA resemblance is layout inspiration only. No independent software safety, actual
20ms firing, qualified gyro envelope, installed RF immunity, physical bore fit or manufacturing release is inferred.
