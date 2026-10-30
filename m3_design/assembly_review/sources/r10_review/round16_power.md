# Round 16 full power and electrical review

Target commit: `b1b8658d5bf541795b7e7636c09f2e886ea8c67a` (root target packet).
PCB SHA-256 before and after: `632a9ad36c19426ede219b6ff6b0d638955665cac1b4704d3392a6afdbe03982`.
**Result: 0 Critical / 0 Major / 1 Minor, carried.** No actual AGENTS section2 violation or demonstrated required-function failure was found. Structured evidence: [round16_power.json](round16_power.json).

## Active finding

**R16-PWR-01 - Minor, carried: L400 retains the reduced heel land.**

Fresh native L400 is F(24.2,5.55), rotation0, Bourns SRP5030T-6R8M/C1329837,
`rocket:M3_SRP5030TA`. Its pads are1.8x2.5mm at local x+/-2.35mm:
inner gap2.90mm, outer span6.50mm. The complete rendered [maker sheet p1](https://www.bourns.com/docs/product-datasheets/srp5030t.pdf)
recommends2.0x1.8mm at+/-2.25mm, inner gap2.50mm. The permitted contact heel
is `(5.7-0.3)/2-(1.1+0.3)=1.30mm`; native copper begins1.45mm from the centre.
Thus **0.15mm can remain uncovered** at a dimensional corner. Nominal coverage
remains; an electrical failure or physical solder defect is not demonstrated.
This carries R15-PWR-02/R14-PWR-01/R13-BOM-01/R13-MFG-02.

**Fix:** adopt the exact maker land through a covered generator/layout revision
with DRC, routing, paste, orientation and provenance checks; or retain this exact
owner/assembler deviation and qualify real coverage, fillets, seating and tolerance
on first articles.

## Fresh full-lens evidence

AGENTS was read first, followed by both review packets, steer and current
requirements/decisions/AVA/M3/validation/vehicle/handoff records. All119 D IDs
through D-R15-03 and22 amended owner mandates were considered. The current
single-switch, direct always-on GPS/radio, retained switched/isolated camera,
DB125 and microSD circuit governs; old three-bank/switch/header budgets do not.
Severity follows the packet's operational meanings and R9 precedents; R9 has no
literal severity table. No current-round16 peer report/probe was read.

- **Native topology and current paths:** all274 numbered physical pads in90
  power/fire/port components agree with the native XML netlist. Selected S-1..S-9,
  K-contract/K-copper/K-inner/K-width and F9-1/F9-2 pass with the actual BOM/CPL:
  15 read-only native rules. RAW_ACT remains behind Q120/Q121; PC1 and PE4 are
  separate externally biased controls with the required gate networks. An own
  pad-aware graph finds0series fire vias. Including the actual routed drain-pad
  entry gives BAT_IN/source/RAW_ACT/IGN/OUT lengths6.307107/2.200000/5.886133/
  10.230382/7.854478mm at widths1.0/0.4/0.5/0.5/0.5mm. Fresh production-budget
  regeneration exactly matches the saved board-bound JSON.
- **Independent source and firing arithmetic:** stated hot copper/FET/contact/
  harness assumptions give4.617458ohm loop,12.370807W other load and0..4-stall
  currents1.544366/1.479438/1.414264/1.348805/1.283013A. All exceed1.125A.
  [J-Tek p1](https://electricmatch.com/upload/JTEK_TECHNICAL_INFORMATION_SHEET_SPECIFICATIONS.PDF)
  defines0.75A with a0.5s test; this does not qualify the actual20ms lot/charge.
  [AONR21357 Rev2.1 pp1-4](https://www.aosmd.com/res/datasheets/AONR21357.pdf)
  supports the selected gate rating/test voltage; a deliberately conservative
  four-stall gate calculation using the maximum4.262A branch-drop allowance is
  4.946V magnitude, above4.5V. Q124 drive estimates2.806V versus the
  [AON7524 Rev1.1 p2](https://www.aosmd.com/sites/default/files/res/datasheets/AON7524.pdf)
  2.5V resistance test point. Hot on-resistance and actual gate behavior remain
  unmeasured. With a shorted match, four stalls and no copper/FET resistance credit,
  the static pack estimate is5.492179V, above the70C resistor-corner UVLO4.811062V.
  This rejects a demonstrated static brownout, not dynamic qualification.
- **Actual-feed hot-plug:** normalized fresh native inputs and electrical digest
  `e4f13accbe3011affc9e9f748c0f72c48eb4f444536248a25903b8c6a0a25ed3`
  match canonical. The entire2304 required-case sweep,60local cases, refinements,
  convergence, no-clamp and retained-OUT checks pass; fresh results exactly match
  canonical. Minimum IN-14.807373V, maximum falling8.991477V/us, refined rising
  5.091053V/us; retained OUT estimate5.877715V after2s. Own graph traversal proves
  C88 separates U9 from other modeled terminals and detects an in-memory bypass.
  An additional64cases with independent C80/C96/C89/C95 low/high mismatch plus
  refined extrema pass. Two HotplugNumerics tests pass, including the independent
  Python-MNA/compiled-solver comparison on the historical failing split-feed
  constant-C control. The additional check uses the unchanged production C solver,
  not a second independent full nonlinear model. [TI RevC pp7/62-63](https://www.ti.com/lit/ds/symlink/tps25947.pdf)
  supplies the device limits and local-protection guidance. The0.193V negative
  margin remains numerical; ideal ground/pads, typical C(V), estimated parasitics,
  installed>=0.03ohm/0.1-2uH harness and R166 durability require measurement.
- **Regulation and current coordination:** independent arithmetic reproduces buck
  5.366682..5.546269V, conservative LDO4.711504..4.873250V and camera/radio/GPS
  endpoint minima5.031682/4.601504/4.631504V under the stated harness/transient
  allocations. [Diodes DS41326 Rev3-2 pp5/13-15](https://www.diodes.com/datasheet/download/AP63200-AP63201-AP63203-AP63205.pdf),
  [TPS7A91 SBVS282A pp5-6](https://www.ti.com/lit/ds/symlink/tps7a91.pdf) and
  [TPS2553 SLVS841G pp6-7/19-21](https://www.ti.com/lit/ds/symlink/tps2553.pdf)
  support these parameter choices. [MicoAir](https://micoair.com/en/docs/telemetry/lr900/lr900-telemetry),
  [HGLRC](https://www.hglrc.com/products/hglrc-m100_mini-gps) and
  [RunCam p1](https://www.runcam.com/download/split4k/RC_Split_4k_Manual_EN.pdf)
  confirm the selected voltage envelopes. Camera limit1.040891..1.249498A;
  U9/R84 bound3.946188..4.856999A leaves0.202391A above the3.743797A threshold-based
  port-fault allocation. Shared-port hiccup/thermal cycling is allowed; no
  continuous-short or transient selectivity guarantee follows. Normal U401 loss
  0.406177W with inferred80..110C/W gives102.494..114.679C at70C ambient;
  the two exact VIPPO sites do not prove a thermal coefficient.
- **Bypasses, pulse heat and timing:** fresh F9-2 gives C82 OUT/GND/total3.577817/
  9.426346/13.004163mm and D9 6.585534/8.176346/14.761880mm, within unchanged
  engineering bounds. They are geometric loops. R134 stress is35.797W and0.716/
  1.289J at20/36ms. The complete rendered [CRM2512 p3](https://www.bourns.com/docs/product-datasheets/CRM.pdf)
  supports only the conditional61.204/44.134W graph interpolation; it does not
  qualify repeated/hot pulses. An own rho(T) adiabatic calculation gives0.5mm
  copper rises7.159/13.006C at35um and11.259/20.565C at28um. IPC long-conductor,
  short-neck and plane estimates do not establish actual neck/via temperatures.
  Current official [ST DS12110 Rev11 p233](https://www.st.com/resource/en/datasheet/stm32h743vi.pdf)
  confirms29.4..33.6kHz:960cycles gives28.571..32.653ms and the allocated fault
  bound34.853ms remains below36ms. Real firmware/reset/current tails are unqualified.
- **Hold-up, bounce, USB and capacitance:** independent energy arithmetic gives
  300.8uF-to3.8V all-port/SD-write0.490..0.571ms, camera-off/logic-shed/card-idle
  1.533..1.655ms. GPS/radio/card remain powered. [TPS2121 pp7-8/33](https://www.ti.com/lit/ds/symlink/tps2121.pdf)
  does not justify reverse-blocking credit below its threshold. C87 needs at
  least1.184188uF effective for the stated150ms bounce model at70C resistor corner;
  actual bias/aging/leakage/bounce remains open. [TPS709 p14](https://www.ti.com/lit/ds/symlink/tps709.pdf)
  requires1.5uF effective; C92's2.211uF estimate remains conditional. C19/C20 exact
  [Samsung part](https://product.samsungsem.com/mlcc/CL10A225KO8NNN.do) meets nominal
  selection, while ST Rev11Table114p211's actual combined-condition C/ESR/mode
  qualification remains unresolved as disclosed. No guaranteed joint minimum is
  inferred from multiplying typical curves. USB limit347.690..453.049mA and
  nominal514.1uF/2.41627mC imply only ideal unloaded5.333..6.949ms charging;
  host/load-aware startup, source transfer and powered-off back-feed remain bench
  obligations. The shared servo return bound remains0.6144A under the specified
  star harness, not a measured installed current.

## Closed and rejected candidates

**R15-PWR-01 is closed:** current Pack prose correctly distinguishes4.778382V at
25C from4.811062V at70C (also the adverse-absolute-TCR -20C corner);125C4.851401V
is a separate sensitivity. Independent KCL includes0.1uA adverse EN leakage and
the actual470k+470k/300k network. Gradients, added leakage and transients remain open.

No Critical/Major bypass/default-gate defect, insufficient selected firing margin,
static shorted-match brownout, required numerical hot-plug failure or demonstrated
pulse overload was found. The JSON preserves each candidate and its limits.
U9 OVLO above its1.5V recommended range during wrong-pack/clamp faults remains
explicitly disclosed; no failed fault-state response was demonstrated. VCAP joint
corners,20ms lot firing and firmware/physical qualification alone are not converted
into invented hardware failures.

## Execution limits

No native CLI/DRC, full check.sh/build, GUI, firmware, physical/first-article/flight
test, git action or order was performed. Only this new report pair and ignored own
probes were written; root owns the complete1942-file freeze audit. API wx/image-handler
diagnostics did not prevent successful checks. An initial own graph omitted common
package-drain aliases; it was corrected from the maker pinout. Tuple/list comparison
was normalized through JSON, and via-layer indices were corrected to native API
layers before final evidence. No canonical file changed. Temporary extracted PDF
texts/rasters were removed. Source notes and durable probe hashes are in the JSON.
This report pair is immutable after handoff.
