# Round 15 full power and electrical review

Target commit: `789f4d516251991bdf1518254d537ff7b41f65bb` (root target packet).
PCB SHA-256 before and after: `7866d6b895573eb10c14d0227ee4bdde8b4fba6145529786cd554cdb80121783`.
**Result: 0 Critical / 0 Major / 2 Minor: one new, one carried.**
No unresolved Critical/Major candidate or actual AGENTS section 2 violation was demonstrated.
Structured evidence: [round15_power.json](round15_power.json).

## Findings

**R15-PWR-01 - Minor, new: the active 4.78 V U9 turn-off figure omits resistor temperature drift.**

`docs/REQUIREMENTS.md:83` calls 4.78 V U9's worst-case turn-off. Native R80 and
R165 are 470 kohm 1% UNI-ROYAL 0603WAF4703T5E; R81 is 300 kohm 1%
0603WAF3003T5E. R80 is F(13.25,69.2), R81 F(20.5,65), U9 B(18.5,81.6).
The closed-switch top resistance is R80+R165. [TI SLVSFC9C p9](https://www.ti.com/lit/ds/symlink/tps25947.pdf)
gives maximum falling EN threshold 1.116 V and 0.1 uA sink leakage.
[UNI-ROYAL V10, 2025-07-28, pp2/6](https://www.uni-royal.cn/en/images/userfile/file/1753752986c56505e6d9ab55c7.pdf)
establishes 1% initial tolerance and +/-100 ppm/K for these >10 ohm 0603 parts.

Steady-state nodal KCL gives
`VBAT_off = 1.116*(1 + Rtop/Rbottom) + 0.1e-6*Rtop`.
At 25 C, `Rtop=940000*1.01`, `Rbottom=300000*0.99` gives **4.778382 V**.
At the stated 70 C bay maximum, including 45 K drift,
`Rtop=940000*1.01*1.0045`, `Rbottom=300000*0.99*0.9955` gives
**4.811062 V**. The -20 C bay end has the same 45 K excursion under independent
adverse TCR signs. A separate 125 C resistor sensitivity gives **4.851401 V**;
125 C is not substituted for the specified bay range. These are conditional
calculations, excluding added board/capacitor leakage, drift and thermal gradients.

The error is confined to Pack prose: a literal search of 28 current requirement,
qualification, binding, budget, circuit, generator and gate files found no second
4.78 claim or budget/gate threshold. The conditional firing envelope still passes;
an independent 7.4 V/0.15 ohm/four-stall/shorted-match calculation gives BAT_IN
5.492179 V before board losses. This is an evidence correction, not a demonstrated
logic brownout.

**Fix:** label 4.78 V as the 25 C calculation and state the temperature-scoped
4.811 V conditional 70 C result, with physical threshold/bounce qualification
still open. Preserve circuit, pins and existing source/harness limits. The
reproducible proof is `.supervisor/r15_power_probe/calculations.py` and its JSON;
`uvlo_claim_scope.json` records the searched files.

**R15-PWR-02 - Minor, carried: L400 retains the reduced heel land.**

Fresh native L400 is F(24.2,5.55), rotation0, Bourns SRP5030T-6R8M/C1329837.
Its two pads are 1.8 x 2.5 mm at local x +/-2.35 mm, inner gap 2.90 mm and outer
span 6.50 mm. The complete rendered [Bourns SRP5030T p1](https://www.bourns.com/docs/product-datasheets/srp5030t.pdf)
recommends 2.0 x 1.8 mm at +/-2.25 mm, inner gap 2.50 mm. The permitted contact
heel is `(5.7-0.3)/2-(1.1+0.3)=1.30 mm`, while native copper begins at 1.45 mm:
**0.15 mm can remain uncovered**. Nominal coverage is intact; no electrical
function failure is demonstrated. This carries R14-PWR-01/R13-BOM-01/R13-MFG-02.

**Fix:** adopt the maker land through a covered generator/layout revision with
DRC, routing, paste, orientation and provenance checks; or retain this exact
owner/assembler deviation and qualify real seating/fillets/tolerance on first articles.

## Fresh checks and rejected failure candidates

AGENTS was read first, followed by both packets and the current requirements,
all 116 D IDs through D-R14-03, 22 amended owner mandates, AVA/M3/validation,
vehicle/handoff, circuit, qualification, budget and hot-plug sources. Severity
uses the packet's operational meanings and R9 precedents; R9 has no literal
severity table. No peer round15 report/probe was read or findings shared with peers.

- **Native topology and population:** 15 selected read-only rules pass: S-1..S-9,
  K-contract, K-copper, K-inner, K-width, F9-1/F9-2. All 261 numbered physical pads
  in the 84-component power/fire/port subset agree with the native XML netlist.
  RAW_ACT remains behind Q120/Q121; PC1 and PE4 are separate, externally biased
  controls. The off-board servo motor path, retained USB mux, camera isolation,
  always-on GPS/radio and SD bypass topology match the current scope.
- **Firing reserve:** an independent pad-aware shortest-path graph finds no
  series fire via. External BAT_IN/source/RAW_ACT/IGN/OUT lengths are
  5.600000/2.200000/5.886133/10.230382/7.854478 mm. The native production budget
  additionally counts the conservative 0.707107 mm drain-pad entry. Fresh budget
  regeneration exactly matches the canonical JSON. Separate resistance/quadratic
  arithmetic reproduces the 4.617458 ohm loop and 1.544366/1.479438/1.414264/
  1.348805/1.283013 A for 0..4 persistent stalls, above the 1.125 A project floor.
  [J-Tek p1](https://electricmatch.com/upload/JTEK_TECHNICAL_INFORMATION_SHEET_SPECIFICATIONS.PDF)
  defines the 0.75 A datum with a 0.5 s test; it does not qualify the actual 20 ms lot.
  The four-stall gate-drive control still estimates 4.946 V magnitude after the
  stated conservative drops, above the maker's 4.5 V RDS(on) test point. Hot
  40 milliohm/FET and installed source/harness premises remain unmeasured.
- **Hot-plug:** fresh native extraction, normalized inputs and electrical digest
  match. The entire 2304 required-case nonlinear sweep, refined extrema, 60 local
  sensitivities, no-clamp controls, convergence and retained-OUT checks were
  rerun successfully; the new report equals canonical results. Required minimum
  IN is -14.807373 V, maximum falling 8.991477 V/us, refined rising 5.091053 V/us,
  retained OUT 5.877715 V after 2 s. A copy seed bypassing C88 is rejected.
  Lower-resistance controls retain failures outside the >=0.03 ohm domain.
  [TI pp7/62-63](https://www.ti.com/lit/ds/symlink/tps25947.pdf) supports the limits/local bypass guidance.
  The ~0.193 V negative margin is numerical; ideal ground/pads, typical C(V),
  package parasitics, installed R/L and R166 pulse endurance remain unqualified.
- **Supply/current coordination:** independent scalar arithmetic and freshly read
  [AP63201 DS41326 Rev3-2 pp5/13-15](https://www.diodes.com/assets/Datasheets/AP63200-AP63201-AP63203-AP63205.pdf),
  [TPS7A91 SBVS282A pp5-6](https://www.ti.com/lit/ds/symlink/tps7a91.pdf) and
  [TPS2553 SLVS841G pp6-7/19-21](https://www.ti.com/lit/ds/symlink/tps2553.pdf)
  support buck 5.366682..5.546269 V, LDO 4.711504..4.873250 V, camera/radio/GPS
  endpoint minima 5.031682/4.601504/4.631504 V under their harness/transient
  allocations, and camera limit 1.040891..1.249498 A. Fresh [LR900](https://micoair.com/en/docs/telemetry/lr900/lr900-telemetry),
  [HGLRC](https://www.hglrc.com/products/hglrc-m100_mini-gps) and
  [RunCam p1](https://www.runcam.com/download/split4k/RC_Split_4k_Manual_EN.pdf)
  specifications agree with the selected voltage envelopes. R84 tolerance gives
  U9 3.946188..4.856999 A; the disclosed 3.743797 A peak allocation stays below
  the lower figure. A shared port short may hiccup/thermally cycle the port rail;
  threshold arithmetic does not prove transient logic selectivity.
- **Bypasses, heat and pulse stress:** current U9 C82 OUT/GND/total is
  3.577817/9.426346/13.004163 mm; D9 6.585534/8.176346/14.761880 mm. Both pass
  unchanged bounds. Exact U401 two-via VIPPO intent passes. Its 0.406177 W and
  inferred 80..110 C/W give 102.494..114.679 C at 70 C ambient; thermal resistance
  is not measured. The 0.5 mm/35 um copper adiabatic model including rho(T)
  rises 7.159/13.006 C at 20/36 ms; 28 um sensitivity gives 11.259/20.565 C.
  These and long-conductor IPC fits do not establish short-neck/via temperatures.
  R134 stress is 35.797 W and 0.716/1.289 J at 20/36 ms. Complete visual inspection
  of [CRM p3](https://www.bourns.com/docs/product-datasheets/CRM.pdf) and
  [AONR21357 Rev2.1 pp1-5](https://www.aosmd.com/res/datasheets/AONR21357.pdf)
  supports only the recorded conditional graph/SOA analysis, not hot/repeated qualification.
- **Hold-up/timing:** energy arithmetic reproduces 300.8 uF-to-3.8 V all-port/SD-write
  0.490..0.571 ms, camera-off/logic-shed/card-idle 1.533..1.655 ms; GPS/radio/card
  remain powered. [TPS2121 pp7-8/33](https://www.ti.com/lit/ds/symlink/tps2121.pdf)
  does not justify assuming reverse blocking below its threshold. C87's conditional
  steady-current model requires >=1.184188 uF effective for 150 ms bounce at the
  70 C resistor corner; its [Samsung data](https://product.samsungsem.com/mlcc/CL10A225KO8NNN.do)
  is typical, not a measured biased/aged floor. [TPS709 p14](https://www.ti.com/lit/ds/symlink/tps709.pdf)
  requires >=1.5 uF effective; C92's existing 2.211 uF estimate remains conditional.
  Fresh official [ST Rev11 p233](https://www.st.com/resource/en/datasheet/stm32h743vi.pdf)
  confirms 29.4..33.6 kHz: 960 cycles gives 28.571..32.653 ms and the allocated
  34.853 ms fault duration is below 36 ms. The cached st_h743 PDF was Rev8;
  decisive ST limits were read from current official Rev11. Native C19/C20 are
  2.2 uF on VCAP1/2; nominal topology does not qualify effective capacitance/ESR.

The suspected shorted-match brownout, insufficient selected firing-current
margin, four-stall gate underdrive and numerical hot-plug failure were rejected
under the stated conditional envelope. Pending firmware, 20 ms lot firing,
physical current tails and transient qualification alone are not demonstrated
required-function failures. U9 OVLO above its 1.5 V recommended range during a
12.6 V wrong-pack fault remains disclosed; this review did not demonstrate a
failed protection response. No fuse, powered-off port isolation, instantaneous
shedding, continuous short tolerance or unmeasured thermal guarantee is inferred.

## Limits and handoff

No KiCad CLI/DRC, full check.sh/build, GUI, firmware, physical/first-article/flight
test, git action or order was performed. Native API wx/image-handler diagnostics
did not prevent successful probes. Temporary extraction tuple/list comparison was
normalized before evaluating equality. Root owns the full 1909-file freeze audit.
Only this new report pair and ignored probes were written; PCB hash is unchanged.
Ignored scripts/JSON preserve reproducible calculations; temporary extracted PDF
texts/rasters were removed after inspection. This report pair is immutable after handoff.
