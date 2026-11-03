# Round 17 full power and electrical review

Target commit `ac483f40d38db6e0424227bd32d2a5d5f9f60c3e`; PCB SHA-256 before and after
`632a9ad36c19426ede219b6ff6b0d638955665cac1b4704d3392a6afdbe03982`.
**Result: 0 Critical / 0 Major / 2 Minor: one new, one carried.** No demonstrated
AGENTS section 2 violation or required electrical-function failure was found.
[Structured evidence](round17_power.json). All 1,966 frozen files match before
and after the review. No implementation or canonical build was performed.

## Findings

**R17-PWR-01 — Minor, active/carried: L400 retains a reduced heel land.**

Native L400, Bourns SRP5030T-6R8M/C1329837, is F(24.2,5.55), rotation 0,
`rocket:M3_SRP5030TA`. Its two 1.8 x 2.5 mm pads are centred at x21.85/26.55:
inner gap 2.90 mm, outer span 6.50 mm. The complete rendered
[Bourns sheet p1](https://www.bourns.com/docs/product-datasheets/srp5030t.pdf)
recommends 2.0 x 1.8 mm pads, inner gap 2.50 mm. The permitted contact heel
can be `(5.7-0.3)/2-(1.1+0.3)=1.30 mm` from the centre; native copper begins
1.45 mm away. Therefore a **0.15 mm heel strip can remain uncovered** at a
dimensional corner. Nominal coverage remains; no physical solder defect or
failed power function is demonstrated. This independently remeasures the
carried R16-PWR-01/R15-PWR-02 deviation.

**Disposition/fix:** retain this exact dimensional departure for owner/assembler
acceptance and inspect actual seating, contact coverage and fillets on first
articles. D-R16-03 forbids a PCB/generator change for this Minor. If qualification
establishes a required-function failure, a separately reviewed maker-land
correction must cover DRC, routing, paste, orientation and provenance.

**R17-PWR-02 — Minor, active/new: pad-capacity examples mix operating points.**

REQUIREMENTS' “Pad time” row uses a **0.77 A** battery-current increment for a
1 A camera and adds **1.155 Ah** for the extra 1.5 hours of recording. D-CIR-02
names the **6.0 V / 80%** converter corner but carries the old 1.76 Ah subtotal
without a reproducible current-board duty worksheet. The native U400 divider
(R400 56.2k + R404 2k over R401 10k, F(16.9,5.55) converter) sets 5.456 V;
its conditional minimum/nominal/maximum are 5.366682/5.456000/5.546269 V.
[Diodes DS41326 Rev3-2 pp5/13](https://www.diodes.com/assets/Datasheets/AP63200-AP63201-AP63203-AP63205.pdf)
supports the reference and divider method; 80% is the project's budgeting
assumption, not a maker efficiency guarantee.

At the stated 6 V/80% point, `Ipack_camera = Vbuck * 1 A / (6 V * 0.8)` is
**1.118059/1.136667/1.155473 A**, giving **1.677088/1.705000/1.733209 Ah** for
1.5 hours, a nominal increment difference of **0.550 Ah**. At a separate 7.4 V/80%
point the nominal camera input is 0.921622 A; battery voltage must be stated.
The old 1.76 Ah subtotal already contains **0.5 hours of camera use** at an
unspecified operating point, alongside an unspecified noncamera subtotal.
Adding the corrected 1.5-hour term to that old subtotal would still mix bases;
it is **not** a complete corrected capacity calculation. Rebase the original
0.5-hour camera term and noncamera duty as well.

A separate fresh uniform 6 V/80% evaluation of the **whole current upper load
allocation** (buck high corner, 1.4 W logic, allocated radio/GPS and continuous
SD writes) gives 2.390393 Ah for 30 minutes of camera use or 4.123602 Ah for two
hours, before servo motor charge. The corresponding capacity figures for 20%
unused capacity are 2.987991/5.154503 Ah. These examples replace every camera
duty term consistently; they are not a qualification of a selected battery.
These are conditional calculations, not measured duty or installed-pack failure.

**Fix:** add a current-board duty/energy worksheet with explicit battery voltage,
converter efficiency, camera/radio/GPS/logic/SD states and servo charge; correct
active capacity examples and distinguish illustrative from qualified selections.
Preserve D-CIR-02's dated historical basis through a new amendment. Actual aged/
cold capacity, fire-time source reserve and bay fit remain required. This is a
docs/evidence correction; no CAD change is warranted by this finding.

## Fresh executed evidence

AGENTS was read first, followed by both packets and the mandatory requirements,
decisions, AVA, revision, validation, vehicle and handoff sources. The frozen
scope contains all **122 D IDs through D-R16-03 and 23 amended owner mandates**.
The current single-switch/direct-port/SD circuit and latest unchanged-board
Minor policy govern. Historical hardware descriptions are superseded. R9 has no
literal severity table; the packet's operational meanings and R9 precedents apply.
No current-round peer report or probe was read.

- **Native circuit:** 258 numbered physical pad rows, collapsing to 254 unique
  reference/pin pairs across 82 reviewed power/fire/port references, all agree
  with the XML netlist; none is missing. Fresh native measurements give fire
  paths BAT_IN/source/RAW_ACT/IGN/OUT of 6.307107/2.200000/5.886133/10.230382/
  7.854478 mm at 1.0/0.4/0.5/0.5/0.5 mm. The OUT via is a sense branch, not a
  series fire via. RAW_ACT is behind source-facing Q120/Q121; PC1 and PE4 have
  separate required bias/gate networks. GPS/radio share PORT_4V8; camera alone
  retains U402/U12/U13. Sixteen scoped read-only native rules pass, including
  S-1..S-9, F9-1/F9-2 and copper/width/contract checks with the actual BOM/CPL.
  Production power-budget regeneration exactly matches the saved JSON.
- **Independent arithmetic:** hot copper is 35.132126 milliohm; the conditional
  4.617458 ohm loop and 12.370807 W other load give 0..4-stall currents
  1.544366/1.479438/1.414264/1.348805/1.283013 A. The selected
  [MJG J-Tek p1](https://electricmatch.com/upload/JTEK_TECHNICAL_INFORMATION_SHEET_SPECIFICATIONS.PDF)
  0.75 A all-fire datum uses 0.5 s; one margin gives 1.125 A, not certification
  of the actual 20 ms lot/charge. With zero fire-copper/FET/harness resistance
  credit and four stalls, the static shorted-match source is 5.492179 V versus
  the 70 C resistor-corner UVLO 4.811062 V. Conservative settled PFET/commanded
  Q124 drive estimates are 4.948735/2.805754 V. These reject the specific static
  failure hypotheses; hot resistance, waveforms and transient survival remain
  unmeasured. Maker references: [AONR21357 Rev2.1 pp1–4](https://www.aosmd.com/res/datasheets/AONR21357.pdf),
  [AON7524 Rev1.1 pp1–2](https://www.aosmd.com/sites/default/files/res/datasheets/AON7524.pdf).
- **Fresh actual-feed model:** extracted inputs and full fresh results exactly
  match canonical. All 2,304 required cases, 60 local cases, refined extrema,
  no-clamp and retained-OUT controls pass. Minimum IN -14.807373 V; maximum
  falling/rising 8.991477/5.091053 V/us; retained OUT 5.877715 V at 2 s. An
  independent graph cut isolates U9 when C88's node is removed and detects an
  added feed bypass. C88-to-U9 remains 3.920 mm, 4.436898 milliohm and
  1.176695–2.424048 nH estimated. A further bounded 64-case independent-capacitor
  mismatch sensitivity and refined extrema pass using the same production C
  kernel. Nine HotplugNumerics/HotplugEvidence tests pass, including the
  independent Python-MNA/compiled-solver comparison and failing split-feed
  control. [TI TPS25947 RevC pp7/60–63](https://www.ti.com/lit/ds/symlink/tps25947.pdf)
  supplies the limits/guidance. Lower-R sensitivities have 14 failing metrics
  outside the required >=0.03 ohm harness domain. The 0.193 V negative margin,
  ideal ground/pads and typical capacitance curves are not physical guarantees.
- **Regulation/coordination:** independently reproduced camera/radio/GPS minima
  5.031682/4.601504/4.631504 V depend on stated complete-loop and transient
  allocations. The module ranges remain consistent with
  [RunCam p1](https://www.runcam.com/download/split4k/RC_Split_4k_Manual_EN.pdf),
  [MicoAir](https://micoair.com/en/docs/telemetry/lr900/lr900-telemetry) and
  [HGLRC](https://www.hglrc.com/products/hglrc-m100_mini-gps).
  Camera limit is 1.040891–1.249498 A. U9/R84 gives 3.946188–4.856999 A;
  threshold-based port-fault allocation 3.743797 A leaves 0.202391 A.
  Shared-short prospective demand 3.160498 A exceeds the buck's continuous 2 A;
  current limit/hiccup and loss of both GPS/radio are explicitly allowed.
  This does not prove transient selectivity. Sources:
  [TPS2553 RevG pp6–7/17](https://www.ti.com/lit/ds/symlink/tps2553.pdf),
  [TPS7A91 RevA pp5–6](https://www.ti.com/lit/ds/symlink/tps7a91.pdf).
- **Heat, pulses and bypasses:** U401's two exact 0.5/0.3 mm VIPPO sites are
  (27.3,13.6)/(27.9,13.6). Its 0.406177 W and inferred 80–110 C/W give
  102.494–114.679 C at 70 C ambient; geometry does not measure thetaJA.
  R134 stress is 35.797452 W, 0.715949 J/20 ms and 1.288708 J/36 ms.
  Complete rendered [CRM2512 p3](https://www.bourns.com/docs/product-datasheets/CRM.pdf)
  supports conditional 61.204/44.134 W graph interpolation, not hot/repeated
  pulse qualification. The allocated watchdog/current-tail total is 34.853061 ms
  against 36 ms. Native C82/D9 OUT-and-GND loops are 13.004163/14.761880 mm,
  inside unchanged engineering limits. IPC long-conductor and adiabatic pulse
  estimates do not establish actual short-neck/via temperatures. R166 reaches
  579.049 W/2.979359 mJ in different model corners; its ordinary UNI-ROYAL
  specification supplies no microsecond endurance guarantee.
- **Hold-up/USB/O6:** independent energy arithmetic gives 300.8 uF-to-3.8 V
  0.490197–0.571129 ms all-port/SD-write or 1.532615–1.655039 ms with camera off,
  logic shed and card idle. GPS/radio/card remain powered. No
  [TPS2121 RevF pp7–8/15](https://www.ti.com/lit/ds/symlink/tps2121.pdf) ideal reverse-blocking
  credit is taken. C87 needs about 1.18424 uF effective in the stated 150 ms
  contact-opening model; real bounce/capacitance is unqualified. USB's
  347.690–453.049 mA and nominal 2.41627 mC imply only unloaded
  5.333353–6.949487 ms charging. O6 still yields 0.6144 A under its specified
  star-transfer/reference-branch bounds, not measured installed return current.

## Rejected blocking candidates and limits

No current fire-feed bypass, missing reset bias, insufficient selected current
margin, static shorted-match brownout, required model-corner failure or
conditional R134 pulse overload was demonstrated. Shared port faults, low-pack
camera dropout, U9 OVLO above its recommended range during faults and direct-port
back-feed remain explicitly bounded qualifications. C19/C20 nominal selection
and typical-curve joint C/ESR uncertainty do not demonstrate an installed regulator
failure. The pad arithmetic issue is Minor because no installed pack or measured
duty is being released. Firmware/physical obligations alone are not hardware
failure findings.

No KiCad CLI/DRC, full check/build, GUI, firmware, first-article, electrical,
thermal, harness, endurance, RF/ESD or flight test was performed. No git action,
order or canonical edit occurred. Native API wx/image-handler and initial
layer-unspecified GetWidth diagnostics did not prevent successful read-only
results; final via measurements use layer-qualified width. PDF text/rasters used
for maker review were removed. Only this new report pair and own ignored probes
were written. Reports are immutable after handoff.
