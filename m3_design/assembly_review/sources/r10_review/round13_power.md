# Round 13 power and electrical review

Target commit: `fa897c81abac3026e75ca5cc88bef0c2659a7130`.
PCB SHA-256 before and after: `7355ae1aeb1fdfdf6f64317945a0bf114d94c2bb65fb04adfbcd5a2b8037b09c`.
Result: **0 Critical, 0 Major, 2 Minor**, both new record/calculation defects.
No unresolved Critical/Major candidate or AGENTS section 2 violation was demonstrated.
This is a fresh full power lens, not firmware, physical qualification or acceptance.

## Findings

### R13-PWR-01 - Minor, new: the current summary puts the resistance floor on the wrong servo branches

`docs/R10_VALIDATION.md:1231` says the <=0.6144 A board-return inference uses
">=50 milliohm motor branches". D-R1-07 and the current construction instruction
at `docs/ORDERING.md:485` require >=50 milliohm **reference** branches instead.
J122 is F(38.6,71.5), pin 5 GND; J1 is F(7.4,75.85), pin 2 GND. Their native
net roles agree with the schematic. Motor-branch resistance does not bound this
parallel reference-return path. For example, a 1 milliohm star segment and a
2 milliohm board/reference bypass give 7.68*0.001/(0.001+0.002) = 2.56 A through
that bypass, irrespective of a >=50 milliohm motor lead. This is a circuit
counterexample, not an installed harness measurement.

The actual assembly instruction is correct, so this is a bounded documentation
defect, not proof that the installed harness violates F4. **Fix:** replace
"motor branches" with "reference branches" in the current deviation summary;
retain the star-transfer limit, 1 A allowance and required four-wire/loaded
measurements. No maker parameter supplies this engineering harness condition;
its primary project source is D-R1-07, confirmed by ORDERING section 8.

### R13-PWR-02 - Minor, new: the U9 coordination minimum omits R84 tolerance

`m3_design/r10_parts.py:471` hard-codes `u9_current_limit_min_A=3.96`, propagated
to `parts_budget.json:94` and `parts_qualification.md:71` as 0.216203 A headroom
over the 3.743797155 A port-fault inference. Native R84 is B(21.6,81.825),
750 ohm, Yageo `RT0603BRD07750RL`, between U9.9 BAT_ILIM and GND.

[TI TPS25947 Rev C, p9](https://www.ti.com/lit/ds/symlink/tps25947.pdf) gives
3.960-4.840 A at **RILM=750 ohm**; its p32 equation 7 makes the setting inversely
proportional to resistance. [Yageo RT V17, p2 and p5](https://yageogroup.com/content/datasheet/asset/file/pyu-rt_1-to-0-01_rohs_l)
decodes B as 0.1% and D as 25 ppm/K. Even initial tolerance alone changes the
inverse-R sensitivity to 3.956044-4.844845 A. Under the worksheet's existing
100 K resistor excursion, delta_R = 0.001 + 25e-6*100 = 0.0035, giving:

`Imin = 3.96/1.0035 = 3.946188341 A`

`Imax = 4.84/0.9965 = 4.856999498 A`

`headroom = 3.946188341 - 3.743797155 = 0.202391186 A`

These scaled values are a calculated sensitivity, not a new TI characterization.
The coordination margin remains positive and comparator overshoot/rail dips
already remain explicitly unqualified; no required-function failure follows.
**Fix:** derive the coordination bound from R84's actual identity/tolerance/TCR,
state the inverse-R assumption, and regenerate the worksheet and current
headroom prose. Qualify or conservatively round the engineering bound rather
than presenting the exact-750-ohm table row as an installed minimum. Review
any 4.84 A upper-bound thermal use at the same time. No CAD change is needed.

## Executed checks and evidence

- Read AGENTS first, both supervisor packets, REQUIREMENTS, all R10 decision
  amendments through D-R12-03, the plan/owner amendments, AVA_LAYOUT, M3_R10,
  R10/R9 validation context, the current qualification/budget/hot-plug sources,
  ORDERING section 8, the in-worktree vehicle handoff and read-only VEHICLE.
  No peer round-13 report was read.
- A fresh KiCad 10.0.6 Python API probe compared the native pad nets of 91
  power/port/fire/sense/support components with `schematic.net.xml`: no mismatch.
  It independently walked endpoint/pad-shape graphs for the fire path. Touching
  AONR drain fingers were joined by actual pad-shape collision, not anchor size.
  RAW_ACT/IGN/OUT are 5.886133/10.230382/7.854478 mm at 0.5 mm; the aligned
  source path is 2.2 mm at 0.4 mm. No series firing via is required. The
  deliberately conservative production budget additionally counts routed
  battery drain-pad entries and reproduces the current saved worksheet exactly.
- Native S-9 and continuous-width checks have zero issues. The pulse assessment
  uses the project's IPC-2152 fit without plane credit for steady conductors;
  short necks, pad heat flow, current sharing and absolute temperatures remain
  unqualified. An independent adiabatic integration with rho(T), starting at
  70 C and 4.261601 A, gives 0.5 mm copper rises of 7.159/13.006 K at
  20/36 ms for 35 um, and 11.259/20.565 K for 28 um. A deliberately isolated,
  full-current 0.4 mm/28 um rod reaches 32.738 K at 36 ms; that diagnostic
  takes no parallel-source-leg or short-length heat-flow credit and does not
  describe the actual seven-branch source network or establish a new violation.
- Independent bisection of the coupled source/constant-power/fire equation
  reproduces 0-4 stall currents of 1.544366/1.479438/1.414264/1.348805/1.283013 A
  to <=2.3e-16 A. The four-stall loaded source is 5.731807 V; peripheral
  regulation/dropout remains conditional. The 1.125 A project floor uses the
  selected [MJG J-Tek p1](https://electricmatch.com/upload/JTEK_TECHNICAL_INFORMATION_SHEET_SPECIFICATIONS.PDF)
  0.75 A datum and does not turn its 0.5 s test into a 20 ms firing guarantee.
- The complete live hot-plug extraction digest matches saved inputs. Component,
  topology, 2304-row evidence/completeness, retained-OUT and convergence
  validation return no issue. A temporary graph edge bypassing C88 is rejected.
  Six selected corners (all four voltage/slew extrema plus damper power and
  energy extrema) were rerun to 150 us at the production and half steps; all
  replay exactly and pass. Largest changes are 34.454 uV and 0.000886 V/us,
  below the 2 mV/0.01 V/us limits. This lens did not rerun all 2304 or 60 local cases.
- A separate incremental-voltage Python MNA integrator used the current complete
  graph, constant capacitances frozen at +2 V, 100 pF U9 shunt, 1 ns source edge,
  disabled TVS and 0.5 us duration. At 12.5/6.25 ps it agrees with the compiled
  charge solver within 7.8e-13 V and 7.2e-11 V/us. This verifies a numerical
  control, not the nonlinear capacitor/parasitic physical assumptions.
- The saved nonlinear limits remain min IN -14.807373 V, falling 8.991477 V/us,
  refined rising 5.091053 V/us; retained-OUT estimate 5.877715 V gives the
  -15 V cold floor. Required harness >=0.03 ohm/0.1-2 uH and failed lower-R
  sensitivities remain visible. Ideal ground, typical C(V), capacitor mismatch,
  package parasitics and R166 durability are unmeasured.
- Fresh saved-copper API measurements reproduce C82 OUT/GND/total
  3.577817/9.426346/13.004163 mm and D9 6.585534/8.176346/14.761880 mm;
  both pass their unchanged engineering bounds. C98 now returns 7.345584 mm
  to U11.12 rather than the former 31.812237 mm. C91/C92 diagnostic GND
  returns remain 6.273402/2.531371 mm. These are geometric paths, not inductance.
- Re-read original maker limits for U9/U10/U11/U400/U401/U402/U13, both fire
  FET types, R134, L400, C84 and the Samsung capacitor identities. Applied the
  PDF skill read-only and visually inspected complete Bourns CRM p3 and
  AONR21357 p4 graphs. PDF hashes are in the JSON; downloaded PDFs/renders
  were removed after inspection.

## Retained dispositions and limits

The C98 remote-return geometry issue is remedied; source-transfer/attach
waveforms and its separately disclosed in-fill routing annotation are not
closed by a raster distance. Existing C91 bypass distance, U9 short-neck/via
heating, U401 80-110 C/W estimate, U400 dropout/thermal behavior, R166 pulse
endurance, unfused entry and direct/shared GPS/radio fault/back-feed behavior
remain correctly disclosed qualifications, not newly demonstrated failures.

Endpoint budgets still calculate 5.031682 V camera, 4.601504 V radio and
4.631504 V GPS at their allocated loads. Camera switch minimum is 1.040891 A;
the LDO's prospective 1.9 A fault plus camera can overload the 2 A buck.
Hiccup/thermal loss of the ports is disclosed, while logic survival needs an
actual short test. U401's calculated 0.406177 W and inferred thermal range
give 102.494-114.679 C at 70 C ambient; 85 C is not qualified. The exact two
filled/capped VIPPO sites do not establish thermal resistance.

C84 energy calculations to 3.8 V remain 0.490-0.571 ms with all ports/SD writing
and 1.533-1.655 ms after camera-off/logic-shed/card-idle assumptions. GPS/radio
and card remain powered; camera turn-off is not credited instantaneously.
The R134 20/36 ms stress, gate tail, watchdog/neutral timing and switch-bounce
figures remain calculations/firmware obligations. The maker pulse/SOA graphs
do not qualify this board hot or for repeated faults.

No native CLI DRC, full check.sh, build, GUI, firmware execution, physical
test, full track/via DC/thermal solve or order was performed by this lens.
The scratch endpoint graph initially omitted overlapping drain-pad joins and
was corrected. A direct-voltage MNA form was discarded for cancellation
sensitivity before the incremental control above. API/NumPy diagnostic warnings
were emitted; completed controls checked finite states and exited zero.
Only this report pair and ignored probes were written; canonical files remain
unchanged. There is no owner question or requested safety-rule change.
