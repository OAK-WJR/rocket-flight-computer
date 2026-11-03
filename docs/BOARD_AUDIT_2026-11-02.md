# R10 integration, requirements audit and fresh model runs — 2026-11-02

The checked candidate is **M3-ASSY-R10**, one 46 × 90 mm, four-layer board. Its PCB SHA-256 is `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c`. This audit changes records and version labels only; it does not change the circuit, copper, manufacturing files, numerical models or firmware bindings. R10 remains an unaccepted CAD candidate. Nothing was ordered, connected, flashed, powered or flown.

## Repository integration

[PR #8](https://github.com/OAK-WJR/rocket-flight-computer/pull/8) merged the local and GitHub histories into `main` at `7a7b9c38d0a5285c4c789f5523fd262257d8e528`. Immediately after fetching that commit, all 20 enumerated local/remote branch refs were ancestors of `origin/main` (zero commits missing). This includes the R2–R10 histories and the local MIT review. Old branches remain available. The GitHub merge tree is identical to the tested integration tree, `388bf3f6f1c85c2fbe61c07c2b79a98960067b72`; no historical board was overlaid on the current R10 layout. Existing PRs #6 and #7 were no longer open after integration.

## Current-board checks

The fresh complete `tools/check.sh` finished with **exit code 0**. DRC at every severity, unconnected items, schematic parity and ERC are all zero. Nine regression groups report 455 case entries: six numerical cases were skipped by the KiCad Python group and then actually run in the NumPy environment with zero skips (449 non-skipped case executions overall). The raw-report hashes are recorded in [machine evidence](BOARD_AUDIT_CHECKS_2026-11-02.json). The gate also checks schematic regeneration; footprint/part metadata and 3D references; silkscreen; bore/support/terminal fit; current R10 contracts; routing hygiene and return partners; fabrication BOM/CPL orientation, paste and package binding; and seeded faults. Software/CAD success remains separate from the procurement failures and hardware qualifications below.

The separate fit extraction is bound to the same PCB: no reported CAD-fit issues, all eight terminal wire faces have 5.003 mm nominal bore room against the recorded 4.95 mm floor, and the closest exposed top pad is 3.807887 mm from a support against the 3.8 mm hardware-radius gate. These are small **CAD** margins. They do not qualify real ferrules, bends, solder tails, screwdrivers, insulated washers or the sled. The report explicitly sets `physical_fit_verified: false`.

Fresh top and bottom renders were inspected. Several terminals and large parts deliberately use simplified block envelopes; a rectangular 3D body is not by itself evidence of a wrong land pattern. The automated metadata/model audit and physical-fit model passed their stated checks. These views cannot establish pin insertion, solderability, actual part heights or closed/open microSD access on a populated assembly. Existing first-article obligations remain.

The routing checker reports zero blocking findings and zero allowlisted blocking exceptions. It also reports **five noncritical informational geometry items**. Under the current R10 policy these do not fail the gate; a zero exit code must not be presented as absence of every routing compromise. They are located here rather than silently omitted:

| Net | Layer / coordinate, mm | Informational item |
|---|---|---|
| BAT_OVLO | B.Cu, (16.4,83.0) | 0.150 mm short segment, width 0.2 mm. |
| BUZZ_DRV | F.Cu, (20.5,51.8) | Small jog, 0.300 mm offset, 0.424 mm middle segment. |
| BAT_FAULT_N | B.Cu, (28.2,47.5) | Small jog, 0.200 mm offset, 0.283 mm middle segment. |
| I2C1_SDA | B.Cu, (9.97,51.5) | Small jog, 0.280 mm offset, 0.396 mm middle segment. |
| USB_ILIM | Net starting at R85.1, (14.825,27.2) | 3.33 mm route versus 1.05 mm tree baseline, ratio 3.18; one via, one needed. |

These are review items under the existing M2/deviation policy, not five newly established electrical faults. No geometry was changed to hide or reclassify them.

## Requirements disposition

This matrix covers all 18 current top-level IDs in [REQUIREMENTS.md](REQUIREMENTS.md). “CAD verified” means the listed representation or gate is checked. “Conditional model” relies on the stated allocations and model domain. Neither means complete system or hardware acceptance. The current requirements include later owner decisions; merging old branches does not restore the abandoned two-board design or older interfaces.

| ID | Evidence available now | Remaining obligation / disposition |
|---|---|---|
| F1 | Correct fitted IMU and reviewed axis/pin contract in CAD. | Temperature compensation, bias/noise under vibration and the error budget at the current mission window remain unqualified; the document itself requires recomputing the 30 s budget for up to 35 s. No R10 acquisition/control firmware. |
| F2 | The fitted IMU provides the specified high-g and low-g hardware ranges. | Actual range configuration, acceleration calibration, clipping and installed dynamics need firmware and measurement. |
| F3 | MS5611 present; part and port constraints recorded. | Cold/vacuum characterization to 300 hPa, installed light/pressure behavior and estimator use remain open; the specified error band stops at 450 mbar. |
| F4 | Four protected signal outputs and signal GND are routed. Servo motor power and return are in the external harness. | PWM/reset behavior, actual servo levels, stall return and installed neutral behavior need R10 firmware and bench evidence. |
| F5 | 16 MB QSPI and secondary microSD hardware are present and connected. | ≥800 Hz acquisition, required log rates, buffering, card latency, corruption handling and power-loss survival are not established for R10. |
| F6 | Reset defaults, filtered switch and hold-up circuitry meet the CAD contract; the current calculation records limited ride-through. | From PA6 trip only 0.103–0.164 ms with ports on, or 0.291–0.430 ms shed (Calculation/Inference). Actual detection/shedding latency and switch chatter require measurement. This does not guarantee completion of a 3 ms flash program. |
| F7 | Existing recovery-output hardware passes the current static contract. | Selected-lot and assembled-system qualification and compatible firmware do not exist. Static checks are not output qualification. |
| F8 | Current single-switch topology and terminal identities are checked against the later R10 requirements. | Rail access, back-feed behavior, operating procedures and firmware state behavior remain open. No owner-deviation acceptance is inferred from permission to merge Git branches. |
| F9 | Board-bound reverse hot-plug model freshly passes its 2304 required cases; see the domain below. | Actual source resistance/inductance, transients, thermal behavior, ESD and upstream unfused-harness exposure remain unqualified. Outside-domain low-resistance cases fail. |
| F10 | External GPS/radio/AUX UART and power ports are routed; no onboard RF is fitted. | Device TX levels, back-feed, installed RF/ESD and firmware port mapping require testing. One common supply is not independent redundancy. |
| F11 | USB/SWD, LEDs, advisory buzzer and diagnostic sense hardware are represented. | R10 firmware and automated fault-localization coverage are absent. The +70 °C buzzer is explicitly best-effort in a hot bay; its thermal rise and installed sound need measurement. |
| F12 | The CAD has the interfaces needed for the documented landed/beacon state. | Landed-state, shutdown, beaconing, watchdog and recovery-duration behavior are firmware/bench obligations, not implemented proof. |
| P1 | Native outline is 46 × 90 mm, within the 120 mm length maximum. | CAD dimension verified; vehicle integration and owner acceptance remain separate. |
| P2 | Bore, closed-card envelopes, five supports and model allocations pass the fit checker. | Physical stack, wires/ferrules, access, fastening, insulation and real assembly fit remain unverified. |
| P3 | Fresh diagnostic plate-model results are bound to the current PCB. | Connector/tall-part retention, vibration, shock and landing loads are not measured; the 500 g-equivalent assertion remains open. No modal release floor is defined. |
| M1 | Fabrication package and assembly process requirements are checked in the gate, including the two specified filled/capped U401 thermal vias. | Fresh stock check fails on U4 and U9 for five boards. Supplier acceptance, insertion/reflow and first-article assembly quality also require resolution. |
| M2 | Native/routing/fab checks meet their enforced rules. | Existing documented routing/MEMS/process compromises still need the recorded owner disposition and first-article qualification. A clean gate does not erase those exceptions. |
| M3 | Fresh part-plus-feeder estimate is $85.13 per board at five boards. | The $84.41 cap is missed by $0.72 per board; cost acceptance and stock remain open. This is not the total landed price; no order was placed. |

Additional user-facing requirements were checked against that matrix:

- **Camera:** the four-position power/GND/UART port exists, with board receive/transmit directions opposite to the interchangeable GPS/radio/AUX terminal convention. Its nominal 5.456 V and conditional loaded minimum are allocations, not measured output quality. Follow the individual pin legends; the green bodies are unkeyed.
- **One replaceable, diagnosable assembly:** one PCB is implemented; external devices and harnesses are replaceable. It does not provide independent replacement of every onboard block. Existing host diagnostic tools and v0.8.1 firmware are bound to historical R1 and do not diagnose R10 merely because the board fits or the USB protocol number matches. Their entry pages now state that scope explicitly.
- **Industrial reliability / multiple protection layers:** independent backup recovery remains a separate electrically isolated device. The CAD has shared power, sensor/MCU and harness failure domains. Neither this audit nor a count of protective components establishes ten independent protection layers, a numerical reliability target, or SpaceX-equivalent reliability. Fault coverage, required environment and measured first-article evidence are still needed.

## Fresh procurement check

The existing read-only JLC tools queried all 82 unique codes, including the owner-fitted C84, from the public supplier API. The snapshot completed at **2026-11-03 05:25:19 UTC** (2026-11-02 in Los Angeles). The original fabrication package was not rewritten; its BOM/CPL hashes match the isolated copy used for these checks.

- At five boards, parts are $60.35 per board and the existing Standard-PCBA fee model adds 81 × $1.53 per order, giving **$85.13 per board** against the $84.41 component-plus-feeder cap. The cost tool exits 1, correctly retaining the $0.72 miss.
- The tool separately reports $83.96 fixed setup/stencil/fixture fees per order and a possible $14.93 handling fee. PCB, edge rails, solder joints, shipping, import charges, attrition and actual checkout adjustments are not included in the cap or the $85.13 figure. These fixed-fee assumptions were not a new assembler quotation.
- U4 / C51931514: `stockCount=4`, `canPresaleNumber=-3`, five required. U9 / C3662793: `stockCount=19`, `canPresaleNumber=-92`, minimum purchase seven. The stock tool exits 1. Treating the minimum of those two fields as orderable is the repository's conservative **Inference**, not a confirmed explanation of JLC's reservation system; confirm in the actual cart or arrange the documented sourcing option.
- Final procurement verification also exits 1 on the cost target; the independent stock result is retained separately. Unknown or negative orderable quantities were not converted into a pass, and no target was relaxed.

The supplier snapshot/report hashes and exact BOM/CPL binding are in the machine evidence. Nothing was purchased, substituted or marked available on the strength of historical stock.

## Fresh numerical tests

### Reverse hot-plug model (Simulation/Inference)

Inputs were extracted afresh from the unchanged native PCB, then simulated with the existing schema-3 nonlinear charge model and maker C(V) curves. Both the PCB hash and electrical signature were checked. `r10_hotplug.validate()` independently accepted the fresh input/report/model bindings, corner coverage, numerical convergence, local-path sensitivity, no-clamp control and retained-output calculation; no reported validation issues.

- 2304 required corners, zero failing corners, source −8.4 V, initial input +2 V, 150 µs duration.
- Installed-harness premise: source/harness resistance ≥0.03 Ω and inductance 0.1–2 µH, with the modeled component/parasitic envelopes. The required corner sweep actually samples 0.03 / 0.10 Ω and 0.1 / 0.5 / 1 / 2 µH; it is discrete numerical evidence, not proof of every continuous operating point.
- Worst input minimum −14.807373 V against −15 V; maximum +2 V against +28 V; falling slew 8.994764 V/µs against 10 V/µs; rising slew 5.087664 V/µs against 100 V/µs.
- Four refined corners, 60 local-path cases plus four refined cases, and four no-clamp controls complete the checked model evidence.
- All eight selected **outside-domain** 0 / 0.01 Ω cases violate one or more criteria (14 metric violations); the worst minimum is −19.061981 V and the worst falling slew 17.074570 V/µs. These are retained failures, not removed from the report or relabelled as passing.

Maker curves are typical; temperature/bias combinations and PCB parasitics are estimates. Real harness measurements and device-pin waveforms are still required. This is an existing circuit model, not a full MCU, regulator-loop, firmware or flight simulation.

### Plate model (Calculation/Inference)

The existing optional Kirchhoff/Rayleigh–Ritz model was rerun with the fresh current-board fit report, five supports and the committed R10 mass specification. Estimated populated board/local-wire mass is 78.6 g. First-mode bounds are 180.8 / 255.6 Hz pinned and 287.8 / 407.0 Hz point-clamped for the two assumed stiffnesses. Under the modeled 100 g transverse load, maximum deflection is 1.27 mm at the east edge, (46,44.5) mm; the reported part strains include 1016 µstrain at U1, 462 at U4, 1221 at C431 and 1489 at J122.

Those figures are model outputs, not measured strength, resonance qualification or proof that solder joints/components survive them. The report has no pass/fail modal floor. Weighing, real support/harness boundary conditions and assembly-level vibration/shock tests remain necessary. Earlier records that say the plate model had not been run on `a0ec075e…` describe their earlier runs; this audit adds a new run without rewriting those historical results.

## Remaining release blockers

The current [owner-decision table](R10_VALIDATION.md#r10-deviations-for-owner-acceptance) still has 35 open rows and one explicitly closed/not-needed row. That count is a record check, not 35 newly discovered PCB errors. Several rows contain already chosen design decisions whose implementation/qualification still needs disposition. This audit accepts none of them on the owner's behalf.

The highest-impact unresolved items are compatible R10 firmware and diagnostics, actual power/thermal/hold-up behavior, source/harness domain validation, component supply and cost disposition, manufacturer/process agreement, and physical assembly/retention/vehicle tests. No new copper defect was established by the checks in this audit. Passing repository checks does not close the above requirements or authorize manufacture/flight.

## Reproduction and evidence

Use the repository's KiCad CLI/Python and a NumPy-capable isolated Python. The gate's numeric stage must actually run, not be mistaken for a pass when skipped:

```sh
NUMPY_PY="$NUMERIC_PY" tools/check.sh
"$KICAD_PY" -I tools/r10_hotplug.py --extract m3_design/assembly_review/m3.kicad_pcb --inputs "$OUT/hotplug_inputs.json"
"$NUMERIC_PY" -I tools/r10_hotplug.py --inputs "$OUT/hotplug_inputs.json" --output "$OUT/hotplug_results.json"
"$KICAD_PY" -I tools/fit_check.py m3_design/assembly_review/m3.kicad_pcb --profile r10 --report "$OUT/fit.json"
"$NUMERIC_PY" -I tools/plate_model.py "$OUT/fit.json" --profile r10 --mass-spec m3_design/assembly_review/sources/r10_design/masses.json --json "$OUT/plate.json"
```

Create `OUT` as a fresh output directory and set the interpreter/tool variables for the local machine. Exact fresh report/log SHA-256 values and the branch-coverage records are in [machine evidence](BOARD_AUDIT_CHECKS_2026-11-02.json). Full numerical output and renders are retained locally; no large model-output payload or personal absolute path is committed.
