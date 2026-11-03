# Round 12 safety review

Target supplied by the supervisor: committed `d57b216c365fc8d18896bceba37f63caf20d52a4`.
PCB SHA-256 before and after review: `0ad0135cb9ff1f6ace7ef9d5ba9006b727b293d7b5224bb97dad47859b91238d`.
Review date: 2026-10-29 local. Native CAD, sources and Git state were not changed.

**Current findings: 0 Critical / 0 Major / 0 Minor.** No new or carried defect was demonstrated in this lens. One previous Minor group is closed below. This report grants no clean-round, fabrication, firmware or flight acceptance.

## Method and scope

Read AGENTS.md, including section 2 verbatim; REQUIREMENTS; R10_DECISIONS through the round-11 completion; AVA_LAYOUT; M3_R10; R10_VALIDATION; R9_VALIDATION; the read-only parent VEHICLE; and the supervisor packet. Current owner amendments supersede the historical ARM-link, switched-port and three-divider text. No other round-12 report was read or current findings shared with reviewers. Prior round-11 safety evidence was consulted only after native topology and independent fault work.

R9_VALIDATION contains precedents, but no literal severity rubric. The supervisor clarified the operational meanings: Critical is a credible inadvertent-fire/comparable serious hazard; Major is a demonstrated required function/constraint failure within stated conditions; Minor is a bounded residual, prospective gate gap or evidence/procedure defect. Correctly stated unperformed qualification is not itself a demonstrated hardware failure.

Inspected native PCB pad nets and coordinates against `schematic.net.xml`, current gate/route generators and the binding obligations. Executed S-1 through S-9 on the actual loaded board, supplying current BOM/CPL: all nine returned zero issues; S-4 covers 199 required fitted parts. These are focused checks, not DRC, ERC or a full gate/build. Five genuine in-memory pad-net faults were rejected: R128.2, C126.2 and R123.2 changed to 3V3; C120.1 changed to 3V3; R134.2 changed to BAT_IN. No mutant was saved. An earlier removal experiment encountered a SWIG lifetime exception after detecting the R128 removal; that interrupted experiment receives no complete-run credit. The subsequent five-miswire probe completed successfully.

An independent nodal solver, populated from native schematic resistors, executed **118,784 DC solves**: 1,024 resistor corners, two cold source endpoints, powered 8.4/19.9 V states, and baseline plus individual open/short faults on ten resistors, three capacitors and D120. Additional open/short-match and grounded-drain cases were solved. The JSON retains compact fault-family extrema, native pad roles, gate evidence, mutation results, exact assumptions and reproducible probe/source fingerprints; raw solve rows are omitted. DC diode states are idealized; leakage, ADC error and transient behavior are excluded and remain qualification limits.

## Native safety chain

| Subject | Current evidence in `m3_design/assembly_review/m3.kicad_pcb` and `schematic.net.xml` |
|---|---|
| Pack / arming contact | J1 F(7.4,75.85): 1 BAT_IN, 2 GND. J400 F(7.4,65.85): BAT_SW_SOURCE / RETURN, only through R80 / R165, each 470 kΩ, to BAT_IN / U9 EN. R81 300 kΩ and C87 2.2 µF remain. S-5 finds no contact/resistor bypass. |
| Pyro feed | Q120 B(13.5,73.6) drain BAT_IN; Q120/Q121 sources ACT_FET_S; Q121 B(13.5,68.6) drain RAW_ACT. R134 B(16.5,64), 2 Ω, links RAW_ACT to J121.2 IGN. J121.1 OUT reaches Q124 F(13.9,57.37) drain; its sources are GND. No J124, separate PYRO1_BUS or direct battery bypass was found. |
| Independent controls | PC1/U1.16 → R122 1 kΩ → Q122 gate; R123 100 kΩ to GND. Q122 pulls ACT_GATE through R121 10 kΩ. R120 100 kΩ and C120 1 µF/25 V connect gate to the common P-FET source. PE4/U1.3 separately drives Q124 through R126 220 Ω; R127 1 kΩ on the MCU side, R128 10 kΩ and C126 220 nF/25 V to GND remain. |
| Sense banks | OUT: R173/R129 two 5.1 kΩ tops, R130/R178 parallel 2 kΩ bottoms, C127 10 nF, direct PC0. RAW_ACT: R132/R175, R133/R180 and C129, direct PC5. Removed duplicate bank and ADC tails remain absent. |
| Physical source path | Manually inspected retained native segments: BAT_IN 5.6+0.707107 mm at 1 mm; RAW_ACT 4.391133+1.495 mm at 0.5 mm; IGN 1.8+6.505382+1.925 mm at 0.5 mm; OUT 3.23+1.414214+3.210265 mm at 0.5 mm. The conservative aligned source path is two 1.1 mm/0.4 mm legs. No series fire-current via; the OUT via is a sense branch. |

Maker pin roles agree with these connections: [AONR21357 Rev2.1 pp1–2](https://www.aosmd.com/res/datasheets/AONR21357.pdf), [AO3400A Rev3.1 pp1–2](https://www.aosmd.com/sites/default/files/res/datasheets/AO3400A.pdf), and [AON7524 Rev1.1 pp1–2](https://www.aosmd.com/sites/default/files/res/datasheets/AON7524.pdf). The P-FET's ±25 V gate rating and C120's 25 V rating cover the recorded approximately 18 V gate excursion condition; this does not certify the transient waveform. C120/C126 values and ratings also agree with the [Samsung 1 µF](https://product.samsungsem.com/mlcc/CL10B105KA8NNN.do) and [220 nF](https://product.samsungsem.com/mlcc/CL10B224KA8NNN.do) characteristic tables.

GPIO analog reset mode and external pulls provide static off bias; no on-by-default connection was found. [ST DS12110 Rev11 §3.8 p32](https://www.st.com/resource/en/datasheet/stm32h743vi.pdf) supports the reset state. Reset, power attachment, Miller coupling, hot leakage, trace override and actual turn-off are still unmeasured. Two pins on one MCU do not create independent software safety.

## Recomputed electrical corners

| Check | Independent result and interpretation |
|---|---|
| One divider resistor fault | With ±1.45% adopted resistor corners, either one top short or one bottom open gives at most **3.342170829 V at 19.9 V**. Top-short bank current is at most **1.397310 mA at 8.4 V**. The absolute ceiling is not a valid ADC reading guarantee. [ST tables109–110 pp207–208](https://www.st.com/resource/en/datasheet/stm32h743vi.pdf) give the applicable 4 V analog ceiling and injection constraint. |
| Other single-component sense faults | Either upper open, either lower short, or a filter short forces the affected ADC low. Cold R131/D120 opens remove bias; their individual shorts remain current limited. Filter/output-capacitor opens can preserve the same DC signature and require dynamic checks. A grounded OUT, including a pre-existing Q124/C128 short, gives both cold readings zero. A later OUT-to-GND fault can fire an enabled match: retained single-string risk. |
| Passive cold screen | At 3.1 V diode-side bias, 1.5 Ω match and 2 Ω R134, CONT/BUS are **99.368924/99.337881 mV**. Open match gives **146.226415/0 mV**. A short match resembles healthy and is not detected by these DC bands. A conservative cold-source current ceiling 3.465 V/9.855 kΩ is **0.351598 mA**, below the selected match's 40 mA test maximum. Thresholds remain unqualified. [MJG p1](https://electricmatch.com/upload/JTEK_TECHNICAL_INFORMATION_SHEET_SPECIFICATIONS.PDF). |
| Physical pulse envelope | 960 LSI cycles at 29.4–33.6 kHz gives **28.571–32.653 ms**; adding 0.2 ms synchronization, 0.5 ms reset and 1.5 ms actual-current tail gives **34.853 ms**, below the 36 ms guard. [ST table136 p233](https://www.st.com/resource/en/datasheet/stm32h743vi.pdf). These are allocations, not measured maxima. |
| Q124 discharge | 10 kΩ ∥ (220 Ω+1 kΩ) = **1087.344 Ω**. At the adopted maximum R/C corner, 3.6→0.4 V RC discharge is **0.678195 ms**; the recorded gate-charge allowance brings the estimate to approximately **0.7392 ms**. Hot gate charge and an off criterion inferred from threshold data do not prove the 1.5 ms physical-current tail. |
| R134 short-load stress | At 70°C, adopted Rmin **1.97109 Ω** gives upper bounds **4.261601 A /35.797452 W**, **0.715949 J at20 ms /1.288708 J at36 ms**, ignoring beneficial series resistance. Freshly rendered [Bourns CRM p3](https://www.bourns.com/docs/product-datasheets/CRM.pdf) shows approximately90 W at10 ms and25 W at100 ms; log interpolation gives61.204/44.134 W at20/36 ms. Graph interpolation is Inference, not repetitive/hot-board pulse qualification. |
| Coupled fire load | Re-solving the current 4.467458 Ω fire branch, 0.15 Ω source, 7.4 V equivalent fire-time source, 12.370807 W converter allocation and 1.92 A/stall gives **1.544366/1.479438/1.414264/1.348805/1.283013 A** for0…4 stalls, all above1.125 A. The source/harness/FET/material premises are unmeasured. The selected maker's0.75 A all-fire datum is a0.5 s test; it does not qualify a20 ms lot/charge. |
| Short match / logic margin | Under the same source/load model and four stalls, a zero-ohm match gives approximately **5.576 V pack /2.260 A fire**, before dynamic effects. This is a static conditional estimate, not proof of logic survival through a short or port transient. |
| Switch bounce | Using native EN resistors, adopted ±1.45% corners, TI's1.116 V maximum falling threshold and0.1 µA EN sink leakage, C87 must retain **≥1.184243 µF effective** to provide150 ms at7.4 V. Nominal2.2 µF gives278.659 ms with those electrical corners. Actual biased/cold/aged capacitance and bounce remain unmeasured. [TPS25947 SLVSFC9C p9](https://www.ti.com/lit/ds/symlink/tps25947.pdf). |

## Ground, flight and back-feed boundaries

Current schematic notes, binding obligations, M3_R10 and ORDERING§8 agree: PC1/PE4 low for the passive screen; after prior enable, ≥1 s plus verified discharge; a ground fault refuses enable; only then PC1 high, PE4 low and ≥100 ms before powered checks. Firmware must require accelerometer+barometer launch detection, and continuity/bus values must never veto a fire in flight. No R10 implementation or timing/threshold proof exists.

USB supplies logic through U10/U11 independently of J400. With the pack connected, powered logic can command the separate pyro switch even while J400 is open. GPS/radio power pins directly share PORT_4V8; their UARTs have1 kΩ and ground-only ESD, without powered-off isolation. Camera alone keeps U402/U12/U13. [TPS2553 RevG p7/§8.3.2 p15](https://www.ti.com/lit/ds/symlink/tps2553.pdf) has a95–190 mV reverse trip and3–7 ms turn-off, rather than an ideal enabled reverse block. [TPS2121 RevF p8/§9.3.6 p15](https://www.ti.com/lit/ds/symlink/tps2121.pdf) specifies0.2–2 A reverse detection. Thus hold-up or external sources cannot be assumed isolated in every state. Exact installed reverse paths and decay remain Inference pending measurement.

The current operating rules correctly prohibit USB/self-powered back-feed when connecting the e-match, and require pack or e-match disconnected for USB bench work. No direct J400 sensor exists; an opening hidden by back-feed cannot be promised detectable. Always-on ports cannot be individually shed, cycled or declared fault-isolated. F6's short ports-on hold-up and the firmware/bench load-decay obligation remain explicit; no new hardware cutoff or physical guarantee was inferred.

## Retained fault risks and measured geometry

The owner-selected single switch, ordinary surface clearance, absence of battery fuse and external servo power are retained decisions, not current-board release acceptance. Preserve the remaining safety deviations in the final board-bound inventory:

- S-8's unchanged1 mm protected-barrel limit passes. Fresh nearest non-GND inner-copper gaps are **1.103 mm** at J121.1 OUT to In2 3V3, **1.900 mm** at J121.2 IGN to J121.1 OUT, **2.699 mm** at OUT via(11.63,55.1) to In2 3V3, and **2.100 mm** at gate via(14.4,53.3) to USB_LIMITED In2. Geometry resolution is approximately0.001 mm. GND remains allowed and an OUT-to-GND defect can fire an enabled match.
- Q124 own gate–drain gap is **0.520 mm**; R126.2-to-drain **1.516 mm** and C126.1-to-drain **1.870 mm** after the moves. Both high-side source-pad1-to-own-drain gaps are **0.520 mm**. Inspection/coating and pre-enable screening do not prevent a later bridge or failed-short part.
- A healthy reset stops Q124 quickly while the high-side gate may relax much more slowly. The36 ms contract requires intact hardware; it does not cover a failed-short Q124/C128, a pin held high by hardware damage, or another gate-network fault. One-resistor divider protection does not extend to every component or to two-fault combinations.
- Pack-to-U9/Q120 copper, TVS/caps and leads are unfused by OQ-6. Servo shorts can collapse the shared pack. O6's reference-current bound depends on the measured pack-star harness; the backup Blue Jay must remain electrically isolated.
- The qualified silicon/LSI range, no-watchdog-refresh-during-fire policy, actual20/36 ms current bounds, ≤50 ms neutral command, lot firing, coating/rework, harness/switch retention, installed RF immunity, power/thermal behavior and physical access remain unverified. They must not be turned into acceptance by this review.

## R12-SAF-01 — prior safety-record group closed

**Minor; classification: closed; prior R11-SAF-01, not in current totals.** Current ORDERING§8.3 now uses final-part/copper coating selection, the sole bus bank and full sensor exclusions. It correctly locates TP121 B(10.5,71.5), TP122 B(13.3,53.3), C24.1 B(25.45,49.42), C15.1 B(29.05,47.82), TP74 B(42.5,58) and TP88 F(35.5,87), and requires staking all seven DB125s including J400. The native fire lengths above agree with `parts_budget.json` bound to this PCB and its current4.617458126 Ω loop. The concrete prior fix—refreshing geometry/procedure and extracting the fire budget from the target—has been implemented. Physical process and source/harness qualification remain open.

The JSON is the structured evidence. No DRC/full gate/build, GUI, firmware, bench, RF or flight test was run by this lens. No complete current-board deviation acceptance, order permission or clean-round credit is claimed.
