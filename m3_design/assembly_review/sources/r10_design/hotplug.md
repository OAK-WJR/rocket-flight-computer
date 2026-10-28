# R10 reverse hot-plug re-model (OQ-2, 2026-10-28)

This is a **simulation / Inference**, not a bench result. The model uses the saved board's copper and maker capacitor
curves. No R4 qualification result is transferred to R10. `hotplug_inputs.json` and `hotplug_results.json` are the
current-board evidence; `hotplug_baseline_inputs.json` records the original split feed on board `407d1d84…`.
The completed schema-3 model passes all 2304 required corners on the single-switch CAD board `60be35ea…` (unchanged input-feed electrical signature `1f638065…` from `b860afbe…`); it retains
the C88 path and checks the feed-first topology. Physical qualification remains open.

## Why the distance gate was insufficient

R8's `step9/hotplug_feed.py` is a constant-capacitance, two-node comparison. Its protection capacitors, damper and TVS
share node A; U9 and C88 are node B. Its docstring explicitly says the original R4 voltage-dependent model is absent
and that its absolute minima are not qualification figures. R10 instead fed U9 along a separate B.Cu branch from J1,
while the bulk capacitors and damper were on F.Cu. Thus U9 could move before the remote bulk capacitance limited the
transient. Holding the old measured part distances did not test that failure mechanism.

The actual original copper, from the pad/track graph (pad copper treated as ideal):

| Path | Track length | Trace resistance at 20 °C | Estimated inductance |
|---|---:|---:|---:|
| J1.1 to C95.1 | 23.526 mm, 1.0 mm F.Cu | 11.56 mΩ | 4.35 nH |
| J1.1 to C80.1 | 31.326 mm, 1.0 mm F.Cu | 15.40 mΩ | 5.79 nH |
| J1.1 to D8.1 | 16.551 mm, 1.0 mm F.Cu | 8.13 mΩ | 3.06 nH |
| J1.1 to U9.5 | 46.560 mm, B.Cu, plus ideal Q120 drain-pad crossing | 24.95 mΩ | 8.96–22.39 nH |
| C89.2 to R166.1 | 10.413 mm, 0.4 mm F.Cu | 12.79 mΩ | 3.40 nH |

Every C80/C96/C89/C95 node is separate in the model. The BAT_DAMP tracks to R166, the R167 branch, and any feed vias
are included. Unloaded test/control stubs are pruned. There is no BAT_IN pour. Extraction rejects such a pour, or an
arc, rather than silently applying the track-only model to it.

The baseline nonlinear sweep fails the 10 V/µs falling-input limit. An independently reproduced failure occurs
within the first 60 ns while U9 IN is still positive, before D8 conducts. It also occurs with nominal bulk capacitance
and 110 nF at C88; it is not caused solely by a low-capacitance or low-resistance corner. Independent RK4 and the
distributed model agree on the mechanism. The recovery takes U9's feed from the protection column, keeping Q120's
pyro supply on its original J1 branch. No component relocation is needed.

## Circuit and input derivation

`tools/r10_hotplug.py --extract BOARD` uses KiCad's loaded pads, tracks, vias and the saved board stack-up. It splits
tracks at actual branch junctions, joins copper through pads, removes open-ended measurement/control stubs and
combines only series edges. The JSON records each piece's coordinates, length, width and layer. The gate re-extracts
these inputs and compares the complete record, the board SHA-256 and the electrical signature. A changed pad, width,
feed via, component value, source curve, solver or corner set invalidates the evidence. Every board capacitor is
inventoried for retained-output discharge, including exact maker identities, nominal values and net roles.

- Trace resistance: `rho L/(width thickness)`, rho 1.72e-8 Ω m at 20 °C, copper thickness from the board (35 µm outer).
  This is a calculation, not a four-wire measurement; pad copper is ideal and no solder/contact resistance is credited.
- Trace inductance: R8's microstrip estimate (`L' = Z0 sqrt(eps_eff)/c`, including the narrow-line expression).
  F.Cu uses In1 GND, 0.2355 mm between copper mid-planes. The B.Cu bracket uses the nearest In2 plane, 0.2355 mm, and
  In1 GND, 1.2955 mm. In2 under the original feed is RAW_PROTECTED, so treating it as a guaranteed ground would be
  wrong. These estimates bracket reference-plane coupling; they are not a field solve or measured bounds.
- Feed via: actual drill and stack height, 20 µm barrel plating (Inference), `R = rho h/(pi drill plating)`;
  `L = 0.2 h [ln(4h/drill)+1]` nH with dimensions in mm. No series via is dropped from the model.
- C88's full local path to U9 is retained: 3.92 mm centreline, 4.436898 mΩ, 1.176695–2.424048 nH. It is never
  contracted to an ideal shunt. The feed reaches C88's BAT_IN pad before the U9 branch. The topology check removes
  C88's node and requires U9 to be disconnected from every other modeled terminal; it also holds the local path
  to 4 mm, 5 mΩ and 2.6 nH in either reference estimate. An independently driven U9 spur or remote C88 fails.
  The centreline estimate includes trace inside the ideal pad copper (1.2 mm in U9's bar, 0.25 mm in C88's pad);
  it is a conservative approximation of that path, not a field extraction of pad inductance.
- TI does not specify U9's input capacitance or the harness contact edge in the cited datasheet. The main sweep
  uses no additional U9 shunt and an instantaneous source step. A separate early-time sensitivity adds an
  assumed 0 / 10 / 100 / 1000 / 10000 pF at U9 and a +2 to -8.4 V ramp over 0.1 / 1 / 10 ns. These are exploratory
  values, not manufacturer limits. Scope U9 IN to U9 GND; package/return-path effects are not bounded by this model.
- The common ground is ideal; the trace-inductance estimate includes its image return. Ground-plane discontinuities,
  capacitor package ESL/ESR, contact bounce, aging beyond the stated capacitor tolerance and harness geometry beyond
  the specified R/L envelope need physical qualification. The model does not claim a worst-case manufacturer guarantee
  from typical capacitor curves.

## Maker sources and corners

Retrieved 2026-10-28. `hotplug_capacitors.json` preserves the numerical graphs and each source response's SHA-256.
The graphs' voltage samples are sorted before integration. Numerical graph data avoids digitizing a rendered plot.

| Component | Original source | Use |
|---|---|---|
| TPS259470 U9 | [TI SLVSFC9C, §6.1](https://www.ti.com/lit/ds/symlink/tps25947.pdf) | IN minimum `max(-15, VOUT-21)` below -10 °C; `max(-15, VOUT-22)` from -10 °C up; IN maximum 28 V; falling slew 10 V/µs, rising slew 100 V/µs |
| C80/C96, CL31A106KBHNNNE | [Samsung product data](https://product.samsungsem.com/mlcc/CL31A106KBHNNN.do) | 10 µF, 50 V, ±10%, X5R; differential C(V), unbiased TCC and biased TCC |
| C89/C95, CL31A226KAHNNNE | [Samsung product data](https://product.samsungsem.com/mlcc/CL31A226KAHNNN.do) | 22 µF, 25 V, ±10%, X5R; same graphs |
| C88, CL05B104KB54PNC | [Samsung product data](https://product.samsungsem.com/mlcc/CL05B104KB54PN.do) | 100 nF, 50 V, ±10%, X7R; same graphs |
| D8, Littelfuse SMBJ12CA | [Littelfuse SMBJ datasheet](https://www.littelfuse.com/assetdocs/littelfuse_tvs_diode_smbj_datasheet.pdf?assetguid=09a6ae9a-73cb-4ac4-acac-e6dab92ab953) | VBR 13.3–14.7 V at 25 °C; 19.9 V clamp at 30.2 A; typical temperature coefficient 0.1%/°C |

The model integrates `Q(V) = integral C(V) dV`, with symmetric negative-voltage capacitance. Samsung labels these
curves typical design-reference data. Each family's low/high multiplier independently combines ±10% part tolerance
with the envelope of normalized biased and unbiased temperature curves over -40…85 °C. The biased TCC graphs are
absolute capacitance change: they are normalized to their own 25 °C value before multiplication, so DC bias is not
counted twice. Applying the temperature envelope to every voltage is an **Inference**. Pairwise capacitor mismatch
within a family and parasitic uncertainty remain bench/model-refinement items.

The 2304 required cases sweep:

- Harness 0.1 / 0.5 / 1 / 2 µH and 0.03 / 0.1 Ω; reversed 8.4 V pack; all input capacitors initially at +2 V.
- Independent low/high bulk, damper and C88 factors; R166 0.3378672 / 0.3825072 Ω, combining its
  0.36 Ω nominal, ±1% tolerance and ±800 ppm/°C over a 65 °C excursion from 25 °C.
- D8 knee 12.4 / 14.7 / 15.6 V, bracketing the room-temperature range with its typical temperature coefficient
  (-40 °C low estimate 12.4355 V; +85 °C high estimate 15.582 V). The soft knee and 0.2 Ω dynamic resistance are
  R8's model, not a manufacturer SPICE model. Selected extreme cases are also run with D8 disabled (1000 V knee).
- Both reference-plane inductance estimates above; extracted copper resistance multiplied independently by
  0.75 / 1 / 1.3. These cover the approximately 0.764–1.255 factors from copper's 0.00393/°C coefficient over
  -40…85 °C, with rounding outward (Inference); they do not establish manufacturing/parasitic tolerance bounds.

**No battery-lead fuse is assumed.** F9's required ≥0.03 Ω pack-plus-harness resistance must be measured on the actual
unfused harness; it no longer follows from a blade-fuse assumption. Selected worst cases also run at 0 and 0.01 Ω.
Those sensitivity cases fail voltage and/or slew limits and must not be relabelled qualified. A lower-resistance
harness needs further protection work or separate qualification before use.

## Numerical checks and acceptance

`tools/r10_hotplug_solver.c` solves the charge-based nonlinear circuit using trapezoidal integration and a
backward-Euler first step to establish the algebraic node voltages after contact. Every Newton step and state must
remain finite. Capacitor currents use `Qnew-Qold` before division by the timestep, avoiding cancellation between
large companion-source currents in the pF sensitivity. The steps are 0.5 ns through 1 µs, 2 ns through 20 µs and 10 ns through 150 µs. Each extremum's case is
rerun at half those steps. Acceptance requires every required corner and refined result inside -15…28 V,
falling slew ≤10 V/µs and rising slew ≤100 V/µs; convergence changes ≤2 mV and ≤0.01 V/µs. The model's cold VOUT
dependent absolute limit must additionally be satisfied; the -15 V gate alone does not establish that condition.

The finite-edge/input-capacitance sensitivity runs each selected main-sweep extreme through the first 0.5 µs
at 0.0125 ns, with its own extremes rerun at 0.00625 ns and the same voltage/slew/convergence checks. It probes
the unresolved local mode; it does not replace the full 150 µs sweep or establish bounds on the assumed parasitics.
The feed-first topology is checked independently of those assumptions.

`HotplugNumerics` compares the compiled charge solver against a separately implemented Python MNA integrator with
constant capacitances and checks a real baseline failing case. `HotplugEvidence` seeds stale sources/inputs, a
missing corner, false pass summaries, failing/non-finite extrema, a shortened run, a coarse step, topology controls
and invalid convergence evidence. Non-finite/boolean extrema, negative slew magnitudes and voltage extrema
that do not contain the +2 V initial state also fail closed. A feed bypassing C88 and missing, changed, shortened,
failing or nonconvergent local sensitivities fail. Real-board tests move D8 and narrow a feed track to prove stale evidence fails.

Reproduction (from the repository root; the two Python interpreters may differ):

```sh
"$KICAD_PY" -I tools/r10_hotplug.py --extract m3_design/assembly_review/m3.kicad_pcb
"$NUMPY_PY" -I tools/r10_hotplug.py
"$NUMPY_PY" -I tools/test_r10_check.py HotplugEvidence HotplugNumerics
"$KICAD_PY" -I tools/check_r10.py --only P-11,F9-1,K-legends
```

No simulator binary is retained: the C helper is compiled in a temporary directory and removed after the run.
Model, capacitor-source and input hashes are checked again at completion, so a run cannot bind old calculations to
sources edited while it was executing. Physical reverse-plug, hot/cold, retained-output and harness measurements
remain mandatory bench work; neither the CAD gate nor the simulation is flight approval.

## R166 and retained output after the owner-answer fixes

The downstream takeoff with the inherited 0.33 Ω damper reached -15.100485 V at its 0.3097116 Ω cold/tolerance
corner (2 µH / 0.03 Ω harness, high bulk, low damper, high bypass, 15.6 V TVS knee, In1 reference, 0.75 copper-R
factor). The 0.36 Ω replacement on the same land passes the 2304 required cases. The revised part identity, temperature coefficient and
pulse-rating limitation are in `parts_qualification.md`. The model reports R166's peak instantaneous power and
integrated energy over 150 µs. They are simulated stress, not evidence that a general thick-film part survives
that pulse. No high-frequency pulse rating is inferred from its 1 W continuous rating.

### Superseded preliminary model

The preliminary sweep used electrical signature `1aec729cda80980725c4fe96d3e51a26df5415f5d40a0aca9ed601607cc54e6d`
and contracted C88's local path. Its 2304 cases passed with -14.497874 V minimum and 8.654349 V/µs maximum
falling slew. A later independent sensitivity retained the path and used an assumed 100 pF at U9 with a 1 ns contact
edge; the separate Python constant-C MNA calculation reached about 13.60 V/µs near 51 ns, at U9 about +1.88 V.
Neither parasitic is a maker limit, so this does not prove a physical failure. It does show that the old local-shunt
approximation cannot qualify that mode. D-OA-07 supersedes it with the feed-first topology and uncontracted model.

### Feed-first implementation

The new 1.0 mm feed via is at (34.7, 84.0), with a 0.5 mm drill; its F.Cu approach clears the existing J122 harness
legend. The B.Cu feed enters C88.1 through a 0.7 mm × 0.8 mm neck. Its exit to U9 is 0.7 mm over 1.15 + 0.97 mm,
then the existing 0.3 mm bar entry. A 1.0 mm exit over 0.97 mm failed the routing short-segment gate; 0.7 mm uses
one width for all three new necks and passes without an exception. No component or extra via is added.

The short-neck conduction estimate uses 4.84 A, 35 µm copper, resistivity 2.1586e-8 Ω m at 85 °C and conductivity
385 W/(m K). Treating the 2.92 mm of 0.7 mm copper plus the 0.6 mm external 0.3 mm pad entry as one rod with both
ends held at the same temperature gives 3.806184 mΩ, 89.16 mW loss and 5.10 °C maximum rise above those ends.
This is an **Inference** for short copper necks alongside the board's IPC-2152 routing assessment; it assumes heat
conduction to the adjoining copper and U9 pad and is not a measured assembly temperature. The rejected 0.4 mm
version gives 127.14 mW and 10.38 °C on the same basis. The 0.7 mm entry leaves 0.22 mm to C88's GND pad by geometry;
scratch DRC and routing hygiene pass at zero, and final post-processing fits all essential legends.

A fresh independent Python constant-C MNA control on the exact 13-edge feed-first graph uses the maker's
capacitances at +2 V, an assumed 100 pF U9 shunt and a 1 ns source ramp. Its falling slew is 4.792413155 V/µs
at 25 ps versus 4.792413154 from the compiled solver; at 12.5 ps the two give 4.792595860 / 4.792595859 V/µs.
This checks the finite-edge integration independently of the production solver. All local edges remain;
seeding a feed that bypasses C88 fails the topology check.

### Final production sweep

The generated board SHA-256 is `3b960b46e72b74cc8b78ec942f558420f276e23976eb13f49759a7e6c40daeac`, with electrical
signature `1f638065387491e1e8c9102de0f59067cc7bce60e9f5f288faa193001b7ade6d`. `hotplug_results.json` binds its
2304 cases and model-source hash to those inputs; `validate()` reports no issue. Required and half-step extrema are:

| Metric | Result | Limit |
|---|---:|---:|
| U9 IN minimum | -14.497873371 V | ≥ -15 V |
| U9 IN maximum | +2 V (initial state) | ≤ +28 V |
| Falling slew | 8.525257186 V/µs | ≤ 10 V/µs |
| Rising slew | 4.523495972 V/µs | ≤ 100 V/µs |

All four selected no-clamp controls pass; their minimum is -14.497873398 V. The largest main-sweep half-step
changes are 0.000302095 V in the minimum, zero in the maximum, 0.001170947 V/µs falling and 0.000855916 V/µs rising,
inside the stated convergence limits. All 60 local-path sensitivity cases and their three refined extrema pass;
the maximum falling slew is 5.197426601 V/µs, with half-step changes at most 0.000002151 V and 0.000025451 V/µs.
Selected 0 / 0.01 Ω harness sensitivities fail; their lowest input is -18.100487 V and fastest fall is
15.300938 V/µs. They remain outside the required ≥0.03 Ω envelope.

Across the required cases R166 reaches 504.292318 W peak and 2.888490051 mJ over 150 µs (different corners).
Separate half-step checks of those two stress corners give 504.293235 W and 2.888489824 mJ, respectively.
These specify the waveform qualification needed; neither the five-second overload test nor low total energy
establishes microsecond pulse durability.

R92 is 3.3 kΩ, ±1%, ±100 ppm/°C. `retained_output` inventories every board capacitor, doubles nominal C84,
and uses +20% tolerance and +15% temperature for all other capacitors. All are conservatively placed on one
8.5 V node and discharged only through R92 at 3354.6645 Ω; no load, divider or U11 reverse-blocking credit is
used. The 1675.3395136 µF envelope yields 5.954856276 V after two seconds, making the cold IN floor -15 V. This is an
**Inference**, not a guaranteed bound for arbitrary converter reverse-energy transfer or the unprovided C84
capacitance-versus-temperature behavior. Scope U9 OUT together with IN during reverse insertion after two seconds.

The capacitor curves are typical, matched family multipliers omit within-family mismatch, and the common ground,
additional U9 input capacitance, contact edge, capacitor package parasitics and trace-inductance estimates remain approximations. Physical
qualification must establish the real unfused harness resistance, U9 pin waveforms and R166 pulse durability over
temperature and repeated insertions. These limitations remain open even when every numerical corner passes.
