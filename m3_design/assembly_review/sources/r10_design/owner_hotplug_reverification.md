# OQ-2: independent failure verification, 2026-10-28

Target: committed board `407d1d8408330849526dbd31cf70ec94b9f012b23ff5c8324eb8a7b1f98bed05`.
This is a focused verification before the fresh full round 9, not a full review round.

**Confirmed Major: the saved R10 input-feed topology fails the falling-slew model within F9's harness envelope.**
The root accepted this finding after a fresh read-only verifier independently inspected the board and reproduced
the transient with a separate RK4 circuit model and the extracted distributed MNA model. This is a simulation
failure; no physical waveform has been measured.

`m3_design/r10_route_power.py`, `battery()`, gives J1.1 two parallel branches: F.Cu to the TVS / bulk capacitors and
B.Cu through Q120's drain region to U9 / C88. The J1-to-C95 track centreline is 23.526 mm, J1-to-C80 is 31.326 mm,
and J1-to-U9 is 46.560 mm plus drain-pad copper. There is no BAT_IN pour. The nearest In2 copper beneath the B.Cu
feed is RAW_PROTECTED; In1 is the guaranteed GND plane. Both reference assumptions were tested.

[TI TPS25947, SLVSFC9C, p. 7](https://www.ti.com/lit/ds/symlink/tps25947.pdf) limits falling input slew to
10 V/us and rising slew to 100 V/us. At cold temperature VIN must also remain above `max(-15 V, VOUT - 21 V)`.
The inherited R8 feed script explicitly lacks the original nonlinear R4 model and does not qualify absolute
voltage or slew; its historical 9.2 V/us result cannot be transferred to R10 by a fixed-capacitance ratio.

For a 0.1 uH / 0.03 ohm harness, nominal 20 uF main capacitance, 44 uF damper capacitance and 100 nF C88, the
distributed MNA model's In1-reference falling slew is 10.886591 / 10.888282 / 10.888701 V/us at 1 / 0.5 / 0.25 ns
steps. The worst event is about 85.6 ns after contact, at U9 approximately +1.408 V. The nearest-plane assumption
gives 14.275961 V/us. Even C88 at +10% gives 10.435488 V/us with the In1 reference. Resistance below 0.03 ohm is
an additional sensitivity, not necessary to establish this failure.

The verifier's separate two-branch RK4 model uses a 5.2 nH / 15.2 milliohm protection branch, 22.39 nH /
27 milliohm U9 branch, the same harness, a 0.33 ohm damper and a 10 kohm input bleeder. Starting all capacitors
at +2 V and connecting -8.4 V gives 10.642949 V/us with nominal capacitors at a 0.25 ns step. With 9.4 uF /
16.7 uF / 50 nF, 0.5 / 0.25 / 0.1 ns steps give 14.777574 / 14.777658 / 14.777689 V/us. The cap voltages remain
positive at this first peak, so low-bias nominal capacitance is also a meaningful check of the mechanism.

Inferred cause: differential ringing between the remote bulk-capacitor branch and the small local C88 branch.
The authorized remedy experiment is a U9 takeoff downstream of the input capacitors, retaining the independent
Q120 pyro load-switch feed. No owner answer is needed to test this change: OQ-2 explicitly authorizes a layout
change if the R10 model fails.

The simplified failure models assume ideal pad / ground connections, estimated uncoupled inductance and an ideal
source step. C88 loop and package dynamics are not resolved. Absolute qualification of a revised board requires
the actual new topology, capacitor voltage dependence, temperature / tolerance corners and numerical convergence.
Samsung's manufacturer product pages expose numeric capacitance-versus-voltage curves, allowing a new model
rather than an unsupported transfer of R4's margin. Physical reverse-plug qualification must also capture
RAW_PROTECTED (U9 OUT) during the existing two-second discharge check to verify the cold input limit.

## Remediation model completion

The revised feed takes U9 from the protection-column branch through one 1.0 / 0.5 mm via, leaving Q120's
J1 feed independent. No protection part moved. With the inherited 0.33 Ω damper its cold/tolerance corner
reaches -15.100485 V, so R166 changes to 0.36 Ω on the same land. The copper-complete experiment's 2304
nonlinear cases pass, including the half-step convergence and selected no-clamp controls: U9 minimum
-14.497874 V, maximum falling slew 8.654350 V/µs. `hotplug.md` records the complete corners, source
assumptions, stress checks and electrical signature. The production build must regenerate the board-bound
input and result files after final post-processing; this experiment is not a full review or board acceptance.

The inventory calculation is 1675.3395136 µF at its stated conservative envelope, yielding 5.954856276 V
after two seconds through R92 alone. It remains an inferred common-node model. Physical U9 IN / OUT
waveforms, actual unfused harness resistance (≥0.03 Ω for this model), capacitor/package parasitics and
R166 pulse durability remain unmeasured. The resistor maker supplies no microsecond pulse curve; the
simulated ≈504 W peak and ≈2.89 mJ do not establish that the part survives repeated insertion.

## Local-path sensitivity and feed-first completion

The preceding 2304-case result used an idealized C88-to-U9 connection and is superseded as qualification
evidence by D-OA-07. Retaining the path, an independently coded constant-C MNA sensitivity with an assumed
100 pF U9 input capacitance and a 1 ns contact edge reaches about 13.60 V/µs near 51 ns. Subtracting the
trace centreline inside the ideal pads still gives about 12.60 V/µs; a 2 ns edge or 1 nF input shunt changes
the result substantially. Those are exploratory parasitics, not maker bounds, and establish no physical
failure. They justify removing the independently driven, unbypassed U9 spur from the candidate model/layout.

The feed now reaches C88.1 first, then U9. The model retains every local trace and checks that removing
C88's node disconnects U9 from all other modeled terminals. The via moves to (34.7, 84.0) to clear J122's
harness legend; no part or additional via is required. The three new necks use 0.7 mm copper, retaining
the existing 0.3 mm U9 pad entry. Scratch DRC, unconnected items and routing hygiene all pass at zero;
post-processing fits the essential legends without changing copper, pads, zones or footprint positions.

Selected previous worst cases and 45 finite-edge/input-capacitance sensitivities pass on this graph,
with local maximum fall 4.812532 V/µs and less than 0.000005 V/µs half-step change. These first-0.5-µs
sensitivities use assumed 0–10 nF input capacitance and 0.1 / 1 / 10 ns edges; they do not replace the
full 150 µs sweep or qualify arbitrary package/contact behavior. The production build reruns the
complete sweep and records its final board binding in `hotplug_inputs.json` / `hotplug_results.json`.

That production sweep is now complete on board `3b960b46…` (electrical signature `1f638065…`): all 2304
required cases, four refined extrema, four no-clamp controls and 60 local-path sensitivities with three
refined extrema pass. Final minimum is -14.497873371 V; maximum falling/rising slew is
8.525257186 / 4.523495972 V/µs. `validate()` reports no issue. The final local sensitivity reaches
5.197426601 V/µs, within the same limits. Lower-resistance harness sensitivities remain failing,
and the physical qualification limitations above remain open.

The fresh verifier also independently checked the exact 13-edge revised graph with constant capacitances
at the maker's +2 V values, an assumed 100 pF input shunt and 1 ns source edge. Python MNA gives
4.792413155 V/µs at 25 ps versus 4.792413154 from the compiled solver; at 12.5 ps the values are
4.792595860 / 4.792595859 V/µs. All extracted edges and pins stay in the circuit, the actual topology
passes, and a seeded feed bypassing C88 fails. This validates the numerical implementation for that
control, while leaving the parasitic values explicitly unqualified assumptions.
