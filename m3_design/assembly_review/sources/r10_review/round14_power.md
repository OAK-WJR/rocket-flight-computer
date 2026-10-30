# Round 14 full power and electrical review

Target commit: `f5e4a5a94013514edb952fd328325341b63a98df`.
PCB SHA-256 before and after: `e0e3ad841654128792b32ab778ca19e4a71e596fa89864074ec4e91e6a5ccfc6`.
**Result: 0 Critical / 0 Major / 1 Minor** (0 new, 1 carried).
No unresolved Critical/Major candidate or AGENTS section 2 violation was demonstrated.
This is a fresh full power lens; CAD, numerical controls and pending qualification are distinguished.
Structured evidence: [round14_power.json](round14_power.json).

## Active finding

**R14-PWR-01 - Minor, carried: L400 retains a reduced heel land.**
Native L400 is F(24.2,5.55), rotation0, C1329837/Bourns SRP5030T-6R8M.
`kilib/rocket.pretty/M3_SRP5030TA.kicad_mod:51` and the loaded PCB give
1.8x2.5mm pads centred at local x+/-2.35mm: outer span6.50mm, inner gap2.90mm.
The freshly rendered [Bourns SRP5030T p1](https://www.bourns.com/docs/product-datasheets/srp5030t.pdf)
recommends2.0x1.8mm at+/-2.25mm, inner gap2.50mm. Its contact tolerance permits
heel `(5.7-0.3)/2-(1.1+0.3)=1.30mm`, while native copper starts at1.45mm:
**0.15mm may remain uncovered**. Nominal contact is covered; no required electrical
function failure is demonstrated. This independently carries R13-BOM-01/R13-MFG-02/R4-BOM-01.

**Fix:** adopt the maker land through a separately covered generator/layout change,
rerunning routing/paste/orientation/DRC/binding; or explicitly retain this measured
deviation for owner/assembler disposition and first-article fillet/tolerance qualification.

## Closed prior power findings

- **R13-PWR-01:** current R10_VALIDATION:1317 and ORDERING:484 correctly put
  >=50mOhm on signal-reference branches and <=1mOhm on star transfer. Native J122.5
  is GND; motor power/return are external. The0.6144A inference/1A allowance is still unmeasured.
- **R13-PWR-02:** native R84 B(21.6,81.825) is750Ohm RT0603BRD07750RL.
  Current source/budget includes +/-0.35% inverse-R sensitivity:
  3.946188-4.856999A, leaving0.202391A over3.743797A. Fresh
  [TI p9/p32](https://www.ti.com/lit/ds/symlink/tps25947.pdf) and
  [Yageo RT V17 p2](https://yageogroup.com/content/datasheet/asset/file/pyu-rt_1-to-0-01_rohs_l)
  support those inputs. Scaling is an Inference; overshoot/rail dips remain unqualified.
- **R12-PWR-01, geometry only:** C98's saved-copper U11 return is7.345584mm
  through the stitch(23.8,62.95), versus31.812237mm before. Its in-fill M2
  annotation and actual source-transfer/attach waveforms remain open.

## Executed checks

Read AGENTS first, both packets, mandatory requirements/decisions/AVA/M3/R10/R9
validation/vehicle sources, current qualification/budget/hot-plug sources, ORDERING
section8 and vehicle handoff. All113 unique D IDs through D-R13-03 and22 owner
mandates were considered by their current amended scope. R9 has no literal severity
table; this report uses the packet's operational meanings and R9 precedents.
No peer round14 report was read and no findings were shared with peers.

- A fresh read-only KiCad10.0.6 API inventory finds209 footprints,966 tracks,
  296 vias. All370 numbered pads of89 power/connector/fire/sense/support components
  match the schematic netlist. Post-switch RAW_ACT, independent PC1/PE4 controls,
  gate networks and removed motor-power/ARM/pull-pin hardware agree with the current scope.
- An independent endpoint/pad-shape graph, including overlapping drain fingers,
  finds no series firing via. External BAT_IN/source/RAW_ACT/IGN/OUT lengths are
  5.600000/2.200000/5.886133/10.230382/7.854478mm. The production budget additionally
  counts the conservative0.707107mm BAT_IN drain-pad entry. Native-bound budget regeneration
  agrees exactly; coupled-load bisection independently reproduces1.544366/1.479438/
  1.414264/1.348805/1.283013A for0-4 persistent stalls to<=2.3e-16A.
  The selected [J-Tek p1](https://electricmatch.com/upload/JTEK_TECHNICAL_INFORMATION_SHEET_SPECIFICATIONS.PDF)
  0.75A datum gives the project1.125A floor, but its0.5s test does not certify20ms firing.
- Native S-9, continuous-width, U9-output-loop, exact U401 VIPPO and SD-bypass
  checks return zero issues. C82 OUT/GND/total is3.577817/9.426346/13.004163mm;
  D9 is6.585534/8.176346/14.761880mm. C91/C92 GND returns are6.273402/2.531371mm.
  SD C460/C461 VDD-pad distances are2.680019/5.057571mm. These are saved geometry.
- Complete live hot-plug extraction matches the saved JSON after serialization
  normalization; digest `a6823d75c2588c917706dfeda324d4f06b1f2adf49c20a6c66c2983a7abbb2a2`.
  All2304 required and60 local stored records, source binding, completeness,
  convergence and retained-OUT validation pass. Six voltage/slew/damper extremes
  were rerun to150us at production/half steps with exact replay; changes stay
  <=34.454uV and0.000886V/us, below2mV/0.01V/us. Six fresh no-clamp controls pass.
  Adding a bypass around C88 is rejected. Six zero-harness-resistance controls
  expose negative-voltage/slew failures, preserving the >=0.03Ohm installation condition.
- A separate block-MNA integrator agrees with the compiled charge solver within
  7.0e-11V/1.31e-9V/us at12.5/6.25ps. This0.5us control freezes C at+2V,
  adds100pF/1ns contact edge and disables the TVS; finite states and <=1.02uA KCL
  residuals were checked. It tests numerical consistency, not physical parasitic bounds.
- Independent tolerance calculations reproduce buck5.366682-5.546269V,
  LDO4.711504-4.873250V, camera/radio/GPS minima5.031682/4.601504/4.631504V,
  and camera limit1.040891-1.249498A. Fresh
  [AP63201 p5/p13-14](https://www.diodes.com/datasheet/download/AP63200-AP63201-AP63203-AP63205.pdf),
  [TPS7A91 p5](https://www.ti.com/lit/ds/symlink/tps7a91.pdf) and
  [TPS2553 RevG p19-21](https://www.ti.com/lit/ds/symlink/tps2553.pdf) were checked.
  Shared cable shorts can overload/hiccup the2A buck; no continuous-fault guarantee is inferred.
- Independent energy arithmetic reproduces300.8uF-to3.8V hold-up0.490-0.571ms
  with all ports/SD writing and1.533-1.655ms with camera off/logic shed/card idle.
  GPS/radio/card stay powered. USB limit347.690-453.049mA and nominal514.1uF
  give ideal no-load5.333-6.949ms charging to4.7V, not a host/startup guarantee.
- Fresh [Samsung C87 data](https://product.samsungsem.com/mlcc/CL10A225KO8NNN.do)
  and TI EN thresholds give170.139ms bounce hold in an explicit typical-C(V)
  control using tolerance/temperature/10%-aging assumptions and100nA sink leakage.
  This supports a conditional calculation only;150ms real bounce remains unmeasured.
- Independent adiabatic rho(T) integration from70C at4.261601A gives0.5mm/35um
  copper rise7.159/13.006C at20/36ms;28um sensitivity11.259/20.565C. An isolated
  full-current0.4mm/28um rod gives32.738C at36ms, without parallel/short-length heat-flow credit.
  Long-conductor IPC fits are diagnostics, not absolute short-neck/via temperatures.
- R134's conservative35.797W stress gives0.716/1.289J at20/36ms. Full-page visual
  inspection of [CRM p3](https://www.bourns.com/docs/product-datasheets/CRM.pdf)
  reproduces the approximate61.20/44.13W interpolations; neither hot/repeated pulse
  performance nor this PCB is qualified by that graph. The
  [AONR21357 p4](https://www.aosmd.com/res/datasheets/AONR21357.pdf) SOA is conditional
  on its gate/temperature/reference-board premises. [ST Table136 p233](https://www.st.com/resource/en/datasheet/stm32h743vi.pdf)
  confirms29.4-33.6kHz:960 cycles gives28.571-32.653ms, allocated fault34.853ms<36ms.

## Retained limits

U9/U400 short-neck/via sharing and whole-board DC/thermal behavior, U401's
80-110C/W estimate (102.494-114.679C at70C ambient;85C sensitivity up to129.679C),
C91 locality, loaded dropout, effective capacitance, USB attach, port faults,
back-feed, switch contacts, PA6/SD shedding, actual gate tail and chosen-lot firing
remain correctly disclosed qualification work. U401 has exactly the two specified
filled/capped VIPPO intents; fabrication quality is unverified. C84 must be manually
fitted after both reflows under a separately validated process. U9 OVLO is nominally
1.547368V at12.6V input, above its1.5V recommended range; fault-state behavior
remains unqualified. Nominal VCAP topology was checked; all-temperature biased/aged
core-regulator stability is not established by nominal2.2uF labels or generic derating.

Hot-plug remains Simulation/Inference: minimum IN-14.807373V, refined falling/rising
8.991477/5.091053V/us, retained OUT5.877715V after2s. Ideal ground/pad copper,
typical C(V), mismatch/package parasitics, installed R/L and R166579.049W/2.979359mJ
durability are unqualified. [UNI-ROYAL pp4-6](https://www.uni-royal.cn/en/images/userfile/file/1753752986c56505e6d9ab55c7.pdf)
provides1W/800ppm/K and a5s overload test, not a microsecond endurance guarantee.
The Littelfuse primary asset URL redirected to page-not-found in this review;
no new D8 waveform/temperature guarantee is inferred from an inaccessible link.

No native CLI DRC, full check.sh/build, GUI, firmware, physical/first-article/flight
test or order was performed. The full2304/60 numerical sweep was validated but not
rerun wholesale. The initial scratch tuple comparison/thermal-API unpack were
corrected; final probes exit0 despite native wx/image-handler diagnostics.
No executable R10 firmware, acceptance or safety-rule change follows.
Only this report pair and ignored probes were written; canonical files are unchanged.
Temporary downloaded PDFs/rasters/full HTML are removed after evidence capture.
