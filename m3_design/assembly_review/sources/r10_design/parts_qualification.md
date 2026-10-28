# R10 component and harness qualification

This is the component contract, not board acceptance. `parts.json` contains exact
parts, pads and intended nets for the schematic generator; its final `circuit.json`
resolves connector role names and MCU signals. `r10_parts.py` reproduces six local
lands, six small VRML envelopes, and `parts_budget.json`. It never edits the board.
Sources were read on 2026-10-26 locally; the R3 fix pass (2026-10-27) re-read
DS41326, SLVS841F, SLVSEA3F, SBVS282A, SCES942A and the LR900 manual. No physical
tests were performed. The 2026-10-28 AUD/GAP amendments below supersede earlier
R10 part selections and timing figures; dated review records remain historical.


## AUD/GAP component amendments (2026-10-28; CAD / Calc / Inference only)

**AUD-1:** C92 is Samsung CL10A475KO8NNNC / C19666, 4.7 µF 16 V X5R ±10%
0603, B (34.2,45.2), −90°, using `rocket:C0603` as already used by C23/C28
with the same C19666 code. The FAB integration correction uses these local-library measurements:
local pad centres ±0.775 → ±0.700 mm, pads 0.90 × 0.95 mm roundrect →
0.80 × 0.90 mm rectangular, courtyard 2.96 × 1.46 → 2.70 × 1.40 mm.
C92.1/.2 move to (34.2, 44.500) / (34.2, 45.900); three local routing corners
must follow the 0.075 mm inward pad shifts. The component value, nets and
capacitance calculation are unchanged. [The exact maker page](https://product.samsungsem.com/mlcc/CL10A475KO8NNN.do)
gives a typical retained fraction 0.6832757 at 3.4 V. Applying 0.9 initial,
0.85 temperature and 0.9 aging factors gives **2.211046 µF**, above
[TPS709's 1.5 µF effective minimum](https://www.ti.com/lit/ds/symlink/tps709.pdf).
Bias and aging allowances are **Inference**, not a guaranteed production minimum;
the part is NRND. Bench stability and load-transient verification remain open.

**AUD-3 / D-AUD-03a:** Q120/Q121 become AOS AONR21357 / C431196.
[Maker Rev2.1 pp1–4](https://www.aosmd.com/res/datasheets/AONR21357.pdf)
specifies −30 V drain, ±25 V gate and 12.3 mΩ maximum at −4.5 V /25°C.
The ~18 V gate event therefore remains inside its absolute gate limit.
The ~1.4 hot factor at 125°C is a typical curve: 17.22 mΩ is **Inference**;
use **40 mΩ per FET** for the primary fire-current acceptance envelope and
measure hot resistance. At 6 V loaded BAT_IN, 4.2 A through that source-side
resistance, 0.1 V allowed at Q122 drain, and resistor 1% plus 100 ppm/K through
125°C, settled |Vgs| ≥5.1916 V. Fully-on 4.2 A /20 ms at 40 mΩ dissipates
0.706 W /0.0141 J per FET. The shorted-load turn-on line is
I=(8.4−|Vds|)/R134min; maximum one-FET linear dissipation is 8.95 W at
|Vds|=4.2 V, I=2.13 A. This is inside the maker's reference-case SOA after
70°C derating; the reference-board 50 ms power curve is about24 W at25°C,
about15 W after derating. These graph reads and extrapolation to actual copper
are **Inference**: note F assumes a heatsink, note H a 1 in² /2 oz board.
Bench shorted-dummy enabling and 20 ms /4.2 A pulses at70°C must measure Vgs,
Vds, current and case rise; 85°C remains a sensitivity until qualified.

The new land follows [AOS PO-00047 rev I](https://www.aosmd.com/sites/default/files/res/packaging_information/DFN3x3A_8L_EP1_P.pdf),
DFN3x3A_8L_EP1_P: nominal3×3 mm body, max3.1×3.1×0.9 mm and3.3 mm lead span.
Local S1–3/G4 centres are x−0.975/−0.325/+0.325/+0.975,y+1.4, pads0.35×0.50;
D5–8 are x+0.975/+0.325/−0.325/−0.975,y−1.495, pads0.40×0.31 (0.01 overlap
with drain9, leaving the maker's0.30 mm finger copper union). Drain9 is the
maker polygon, x±1.225,y−1.35…+0.63, with wings to x±1.605 at y±0.215.
The 3.3×3.3×0.9 mm model is a fit envelope. Verify actual supplier numbered
pads and CPL orientation, stencil/assembly quality and solder coverage before order.

C120 reuses Samsung **CL10B105KA8NNNC / C29936**, 1 µF 25 V X7R ±10%, on
`rocket:C_0603_1608Metric`, matching C86/C97/C98 with the same C29936 code.
This FAB integration correction supersedes the initial unchanged-C0603-land choice:
the pad and courtyard changes are the reverse of C92's above. Move C120 0.075 mm
north to B (17.1, 71.525), −90°, retaining pad 2 on the existing ACT_GATE lane
at (17.1, 72.300); pad 1 becomes (17.1, 70.750). Review its source tap and local
clearance after regeneration. The electrical timing assumptions are unchanged.
[Maker identity and typical curves](https://product.samsungsem.com/mlcc/CL10B105KA8NNN.do)
replace the former2.2 µF16 V part's above-rating condition. Cmax=1.265 µF;
R120∥R121 gives tau≤11.73 ms and ≤23.65 ms to |Vgs|=4.5 V at the corner above.
Hold PE4 low and wait **≥100 ms after ACT_EN** before bus checks or a permitted
fire. The typical bias curve with0.9 tolerance/0.85 temperature/0.9 aging yields
Ceff≈0.587 µF at4.5 V (linear interpolation), so both FETs'2×70 nC maximum10 V total gate charge
would step it about0.239 V (**Inference**, not a hot off-state guarantee).
Check Miller turn-on with power attachment, reset/unpowered behavior and gate
turn-off on the actual board. The load-switch off RC is≤129.03 ms; Q124's
independent fast current-off contract remains below.

**AUD-4/5/7/9:** J123/R160/R161/C160/D122 and TP84/85/86/87/89/92 are removed;
PC13 U1.7 is NC/analog, no EXTI13. Keep TP80–83/TP120–122 and USB-only U10/U11.
R412/R422/R432 use10 kΩ1%0402 C25744; R150–153 use1 kΩ1%0603 C21190,
UNI-ROYAL0603WAF1001T5E rated100 mW through70°C.
[Maker series specification](https://datasheet.lcsc.com/datasheet/pdf/0a975aaa49b7c97f38a963127be4a823.pdf)
gives the above10Ω resistors100 ppm/K. The8.4 V chafe is64 mW with a0.4 V
low output, or a conservative72 mW at0 V and980Ω; neither needs the inherited
30%-of-rating rule. Port and servo component changes retain their protective networks.

**Single-switch passive cold check (Calc / Inference, no firmware thresholds):**
keep PC1 ACT_EN low and PE4 low. If the load switch was previously enabled, wait
at least1 s and verify RAW_ACT has discharged / ACT_GATE has returned off before
classifying a reading. New C120/R120 maximum off tau≈129 ms makes1 s about7.75tau;
this wait is provisional until bench-qualified. At boot without a prior enable,
C120 starts near Vgs=0. Only after a valid passive fault check may firmware enable
PC1, still holding PE4 low, then wait≥100 ms before powered-bus checks.

OUT has one11.2 kΩ divider; merged RAW_ACT has two11.2 kΩ dividers in parallel.
Each is10.2 kΩ over1 kΩ (two5.1 kΩ series, two2 kΩ parallel). With a1–2Ω e-match
plus R1342Ω, all three banks load D120/R13110 kΩ. For U=3V3−Vf,
Rload=11.2k∥(Rmatch+R134+5.6k), Vout=U×Rload/(10k+Rload),
Vraw=Vout×5.6k/(Rmatch+R134+5.6k); each sense ADC is its bus divided by11.2.
Use nominal3V3=3.3 V, Vf=0.20 V for the nominal column. The illustrative band
uses3V3=3.135–3.465 V (existing±5% budgeting assumption), Vf=0–0.32 V, and each
resistor at±1.45% (1% plus100 ppm/K to70°C). The diode range is an **Inference**
from the [JSCJ BAT54/A/C/S25°C table](https://www.lcsc.com/datasheet/lcsc_datasheet_1809200014_Jiangsu-Changjing-Electronics-Technology-Co---Ltd--BAT54A_C8591.pdf)
(Vf max0.32 V at1 mA, above the diagnostic current); it is not a guaranteed hot/cold
range. Original supplier PDF access was blocked in this pass; the cached maker
excerpt was available. ADC pins are analog with no pull, fully settled, and the
listed bands assume zero ADC/FET/board leakage and no external backfeed.

| ACT_EN off / PE4 low, settled state | CONT ADC nominal (illustrative band) | ARM1 and RAW_ACT ADC nominal (illustrative band) |
|---|---|---|
| Healthy1–2Ω dummy e-match |75.27 mV (65.58–87.65 mV)|75.22 mV (65.54–87.60 mV each)|
| Open e-match |146.23 mV (129.16–168.02 mV)|0 V before leakage|
| Q124 drain grounded / stuck-on, e-match connected |approximately0 V|approximately0 V|
| Shorted e-match |approximately the healthy row|approximately the healthy row; not distinguishable here|

These bands exclude leakage, ADC offset, reference error, acquisition effects and
unqualified diode temperature behavior. As sensitivity only, ±10 µA net leakage
at both OUT and RAW shifts a healthy ADC about±4.85 mV; with an open e-match,
±10 µA shifts CONT about±4.72 mV or a RAW sense about±5.0 mV. ADC-pin leakage of
1 µA can add roughly5.7 mV through its4.7 kΩ plus divider impedance. These are
assumptions, not published hot leakage guarantees. Bench the actual low/healthy/open
states and unexpected powered-bus states across temperature before selecting hard
refusal thresholds. Old ARM-plug-out≈100 mV bands do not transfer. These checks
are hard refusals on the ground; in flight they only log/annunciate and never veto
a fire (AGENTS§2.3).

**GAP-1:** `parts_budget.json` includes the actual11.545807 W worst normal
logic/ports allocation, rather than assuming all other pack loads vanish. The
pack has Voc=7.4 V equivalent **at the fire instant after pad/flight drain**, Rpack≤0.15Ω;
servo stall current is1.92 A each. Solve
(1+Rpack/Rfire)V²−(Voc−Rpack×Iservo)V+Rpack×Pother=0, taking the high root,
then Ifire=V/Rfire. Include R134 upper tolerance/temperature, 2Ω e-match,
≤0.3Ω external leads/harness, final CAD copper, hot FETs, 5 mΩ GND-return and
10 mΩ contact allowances. Copper at20°C is scaled to70°C by1.1965 using
[standard annealed copper TCR0.00393/K](https://nvlpubs.nist.gov/nistpubs/Legacy/hb/nbshandbook100.pdf);
actual thickness, contact, source and harness resistance remain bench conditions.
The old4.533Ω loop with a fixed1.5 A other load gives1.58284 A idle or1.45577 A
with two stalls; these are illustrations, not qualification of changed copper.
The primary40 mΩ/FET final calculation and secondary17.22 mΩ curve estimate
are generated in the budget. Final CAD track bounds at20°C are BAT_IN3.49962,
ACT_FET_S2.70286 (one2.2 mm/0.4 mm aligned path; no parallel-leg credit),
RAW_ACT6.38857, IGN4.76686 and OUT7.81812 mΩ: total25.17602 mΩ, or30.12311 mΩ
at70°C. With R134max2.02909Ω, Q1248.236 mΩ hot inference, and the stated
allowances, primary total loop including pack is4.612449Ω. At7.4 V equivalent,
Ifire is1.550071 A idle,1.485263 A with one persistent stall,1.420229 A with two,
1.354934 A with three and1.289335 A with four. Idle-servo≥1.5 A remains required
and passes; even one persistent stall misses the primary margin. Two stalls imply
a compatible all-fire limit0.946819 A, or require≥7.753406 V equivalent at fire
for the existing1 A all-fire part under the same conditions. The secondary
17.22 mΩ/FET case gives1.565516 A idle /1.434377 A with two stalls; it does not
set acceptance. A neutral command and200 ms wait cannot unload a jam. The compatible
all-fire limit is derived, not adoption of another e-match, and a margin failure
does not establish that a1 A-rated e-match will not fire. Measure source reserve
and resistance at the deployment time, not only prelaunch voltage.

**GAP-5:** [ST DS12110 Rev11 Table136 p233](https://www.st.com/resource/en/datasheet/stm32h743vi.pdf)
gives RevV LSI29.4–33.6 kHz through Tj125°C (29.76 kHz applies only through110°C;
RevY has a different qualification). Bind the actual silicon ID and temperature.
IWDG prescaler÷4/reload239 =960 cycles, nominal30 ms, actual28.571–32.653 ms.
Refresh immediately **before** PE4 rises and never refresh while fire is active.
An independent timer/DMA abort ends normal **physical current within20 ms**,
including gate tail; set its command cutoff early enough for the measured tail.
After current off, complete a valid SAFETY pass and refresh within5 ms:
20+5<28.571 ms. Refreshing during fire is invalid: a late hang adds the watchdog
time to elapsed current and can exceed the resistor envelope.

Floating-MCU discharge is10 kΩ∥(220Ω+1 kΩ)=1087.344Ω. C126 is Samsung
[CL10B224KA8NNNC / C21120](https://product.samsungsem.com/mlcc/CL10B224KA8NNN.do),220 nF X7R ±10% with±15% temperature:
Cmax278.3 nF. Resistor1%+100 ppm/K through125°C gives Rmax1109.091Ω.
From3.6 V to0.4 V, RC≤0.67820 ms; adding [AON7524's22 nC maximum gate-charge](https://www.aosmd.com/sites/default/files/res/datasheets/AON7524.pdf)
allowance yields≈0.73920 ms (**Inference**: hot charge and0.4 V off criterion
are not guaranteed). Use **1.5 ms actual-current tail** only after bench validation.
With prefire/sync≤0.2 ms and reset-to-HiZ≤0.5 ms, total≤34.8531 ms, guarded
at **36 ms**. No firmware or reset/current-tail bench test has passed.

[Bourns CRM2512 maker pulse chart p3](https://www.bourns.com/docs/product-datasheets/CRM.pdf),
≥1Ω curve, reads about90 W at10 ms and25 W at100 ms. Log interpolation gives
61.204 W at20 ms /44.134 W at36 ms (**Inference**, graphical precision).
R134 minimum at70°C is1.97109Ω; ignoring every other series resistance gives
35.7975 W,0.71595 J/20 ms and1.28871 J/36 ms. Thus36 ms has about1.23×
chart margin at70°C under those assumptions. Applying linear155°C derating at
85°C gives only36.345 W versus35.851 W demand (**Inference**), essentially no
useful margin; the85°C condition is unqualified. Scope watchdog refresh, PE4,
TP122, NRST and dummy-load current for early/late CPU starvation, normal abort,
postfire refresh, reset/unpowered gate tails and hot R134 pulses; record resistor
drift and actual physical20/36 ms limits across supply and temperature.

## Supply contract and sources

RAW_PROTECTED feeds U400 AP63201WU-7 (C2071044), with EN tied to its input.
The buck is always ready with battery protection on; the three port switches default
off. Neither the buck nor its LDO nor any port supply connects to VLOGIC or 3V3.
The existing logic/USB mux and hold-up path remain separate. U401 is
TPS7A9101DSKR (C2878140); U402/U410/U420 are TPS2553DBVR (C55266).

- [Diodes AP63200/1/3/5, DS41326 Rev3-2](https://www.diodes.com/assets/Datasheets/AP63200-AP63201-AP63203-AP63205.pdf), pp1,5,11–14:
  AP63201 forced PWM, 500 kHz, reference 0.792–0.808 V, input 3.8–32 V,
  high-side current limit 2.5–3.1 A. Pin1 FB,2 EN,3 VIN,4 GND,5 SW,6 BST.
  Section13 supports near-100% duty with bootstrap refresh; it does not specify a
  guaranteed maximum loaded dropout. The 125/68 mΩ switch resistances are typical,
  not maximum. Existing local TSOT26 land is reused.
- [TI TPS7A91 SBVS282A](https://www.ti.com/lit/ds/symlink/tps7a91.pdf), pin table p3,
  electrical table pp5–6, DSK0010A drawing4218903/C:
  output accuracy ±1% for 5 mA–1 A; feedback leakage ±100 nA; dropout at most
  200 mV at 1 A; input at most6.5 V. The electrical table takes precedence over
  contradictory 100 mV prose on the cover. R405820Ω provides at least5.63 mA
  when all ports are off, keeping the accuracy claim inside its specified range.
  IN9/10, OUT1/2, FB3, GND4/11, PG5 unused, SS_CTRL6 ground, EN7 input,
  NR/SS8 has10 nF. No extrapolated accuracy at zero load is used.
- [TI TPS2553 SLVS841F](https://www.ti.com/lit/ds/symlink/tps2553.pdf), pp5–7,13–16:
  operating2.5–6.5 V, DBV maximum RON135 mΩ over temperature; current-limit
  equations with resistor tolerance; fault debounce up to10 ms. Pin1 IN,2 GND,
  3 EN,4 open-drain FAULT,5 ILIM,6 OUT. EN has a100 kΩ pull-down; FAULT has a
  logic-side pull-up. Each switch has local input and output capacitors.
- [Bourns SRP5030T](https://www.bourns.com/docs/product-datasheets/srp5030t.pdf):
  L4006.8µH C1329837, ±20%, DCR76.2 mΩ maximum, Irms4 A, Isat4.3 A.
  Keep the existing maker land. At8.4 V input,5.367–5.546 V output, Lmin5.44µH
  and470 kHz (500 kHz less the±6% spread spectrum, DS41326 p5; Inference for the
  low edge), calculated ripple is0.74–0.76 A (DS41326 p13 equation). The peak
  inductor current at the all-ports-shorted load is in the next section. Isat is a
  typical20% drop rating, not an absolute limit.
- [Yageo RT part specification](https://yageogroup.com/component-documentation/download/specsheet/RT0603BRD0725K5L)
  and the same RT0603BRD ordering family establish0.1%/25 ppm/°C.
  [UNI-ROYAL thick-film specification](https://www.uni-royal.cn/en/images/userfile/file/1753752986c56505e6d9ab55c7.pdf)
  specifies100 ppm/°C for0603 values above10Ω. The calculation conservatively
  combines initial tolerance with100°C excursion from25°C independently for
  each resistor. The buck itself is rated ambient−40…85°C, not125°C ambient.
- Capacitors reuse Murata GRM32ER71E226KE15L C21397,22µF/25 V X7R10%,
  with two at the buck input, two at its output, one at LDO input and two at
  LDO output. Existing100 nF bootstrap C14663 and10 nF C15195 are reused.
  **Open:** verify effective capacitance at bias/temperature/aging against
  the maker curves and the assembled converter's stability. Nominal44µF is
  not a stability proof. The LDO requires at least10µF effective at its input
  and output. No substitution to lower-voltage small MLCCs is qualified here.

## Voltage, current and thermal budgets

The rail remains named PORT_5V3 but its qualified *nominal setting* is5.456 V:
R40056.2 kΩ0.1% plus R4042 kΩ1% over R40110 kΩ0.1%.
O5 explicitly leaves the exact set point to implementation. A5.3 V setting cannot
cover the full1 A camera load after aged GH contacts and harness loss.
The LDO nominal is4.792 V:49.9 kΩ/10 kΩ, both0.1%.

The reproducible values in `parts_budget.json` include reference tolerance,
resistor initial tolerance/TCR and LDO feedback leakage. They give:

| Boundary | Calculated bound | Explicit acceptance condition |
|---|---:|---|
| Buck steady rail | 5.367–5.546 V | Regulating input, specified component temperature |
| LDO steady rail | 4.712–4.873 V | Input headroom;5 mA minimum ensured by bleeder |
| Camera at module | ≥5.032 V at1 A | Switch135 mΩ; harness+contacts+copper≤150 mΩ; negative transient≤50 mV |
| Radio at module | ≥4.561 V at300 mA | Harness+contacts+copper≤200 mΩ; negative transient≤50 mV |
| GPS at module | ≥4.611 V at150 mA | Same200 mΩ and50 mV limits |
| Radio/GPS maximum | ≤4.923 V | Positive transient≤50 mV |
| LDO headroom | ≥443 mV | Includes buck negative50 mV; exceeds200 mV maximum dropout |

The manufacturer [LR900 manual](https://micoair.com/en/docs/telemetry/lr900/lr900-telemetry)
specifies4.5–5 V and3.3 V UART. [HGLRC](https://www.hglrc.com/products/hglrc-m100_mini-gps)
specifies3.3–5 V. The300/150 mA allocations above are **engineering load envelopes**,
not proven maximum module demand; measure radio TX peaks, GPS startup and camera
startup. The RunCam minimum5 V and battery-surge prohibition remain as cited in
`docs/SIMULATION.md` item20. A current allocation is not permission to exceed GH's
1 A/contact rating. The camera's fault limit exceeds1 A briefly; firmware must
turn off a faulted port, with thermal cycling only a backup.

R430(camera)22.6 kΩ, R420(radio)66.5 kΩ, R410(GPS)100 kΩ (R10_DECISIONS
D-R3-01: the board's value, on the existing 100 kΩ line C14675, no extra code)
include1% initial plus1% temperature allowance in TI SLVS841F equation 1 (p15,
IOSmin/IOSmax). Bounds: camera1.041–1.249 A, radio0.348–0.453 A, GPS0.230–0.309 A.
A camera short with the other two at their normal allocations is1.711 A. The
LDO's two shorted ports (0.762 A) stay below its1 A rating.

**All three ports shorted** (three simultaneous faults) plus11 mA quiescent,
divider and bleeder load draw2.022 A from the buck,1.1% over the AP63201's2 A
continuous rating (DS41326 p1). The criterion that matters is the cycle-by-cycle
limit: the peak inductor current, 2.022 A plus half the ripple (L400 6.8µH−20%,
buck output5.367–5.546 V), must stay below the2.5 A minimum HS peak current
limit (DS41326 p5). Calculated (`parts_budget.json`): 2.38 A at8.4 V and500 kHz,
2.40 A at8.4 V and470 kHz; at the9.97 V OVLO corner (the highest RAW_PROTECTED
U9 lets through, M3_R4 A2)2.48 A at500 kHz and2.51 A at470 kHz, i.e. up to
0.007 A over the limit at the spread-spectrum low edge. If the limit is reached
the buck limits each cycle and after2 ms enters hiccup (DS41326 p11): the ports
lose supply, VLOGIC and3V3 are a separate path. Accepted as a triple-fault,
out-of-range-input corner (Inference, no transient simulation). `r10_parts.py`
asserts the8.4 V figure below2.41 A and the OVLO figures below2.5 A (500 kHz)
and2.51 A (470 kHz). Shorted switch outputs dissipate watts before shutdown; do
not characterize this as continuous thermal capability. Hardware limits current
even before the MCU handles FAULT.

**Inference, upstream coordination:** with≥80% buck efficiency,5.8 V buck input,
logic path≤0.5 A and all port shorts, U9 current is about2.92 A (below2.95 A,
asserted), versus its3.96 A minimum limit. Buck's own3.1 A maximum peak limit
plus0.5 A logic is3.6 A.
These bounds exclude switching overshoot and are not a proof of transient
selectivity. Starting the2 A logic mux and all peripherals together is prohibited;
port enables default off and firmware sequences their startup. Test a short on
one port and all ports while checking3V3 and VLOGIC remain in regulation.

**Inference, stall input:** for0.15Ω pack resistance,7.68 A stalled servos,
0.5 A board input logic allocation,1.46 A at5.456 V peripheral output and80%
efficiency, solving the constant-power pack sag gives5.921 V from a7.4 V open-pack
floor, before U9 and board losses. A6 V open pack gives4.436 V. Buck near-100%
duty cannot boost either case. No all-load camera guarantee exists at the low-pack
four-stall corner. Shed all port enables before RAW_PROTECTED falls below6.2 V;
accept loss of peripheral operation while retaining logic/recovery. The MCU's
actual threshold, sampling latency, load transients and 3V3 ride-through require
simulation and bench testing. Even at6 V loaded input, loaded-dropout qualification
is open because AP63201 only gives typical switch resistance; never label that
corner guaranteed from the nominal duty calculation.

**GAP-3, LDO thermal (Calc / Inference):** allocated 460 mA output, extreme
rail tolerances and 4 mA quiescent draw give 0.406177 W. U401 pad 11 is
1.2 × 2.0 mm, centred at (27.6,13.6), and now has two GND vias at
(27.3,13.6)/(27.9,13.6), 0.5 mm ring / 0.3 mm drill. These two vias require
resin filling, copper capping and planar VIPPO; the maker's paste windows stay
unchanged. Fabricator acceptance is pending. TI TPS7A91 §7.1.4 / layout guidance
calls for thermal vias; its 62.5°C/W JEDEC thetaJA is not this board's thermal
resistance. Retain 80–110°C/W as a conservative **Inference**, without claiming
that the vias establish or improve that number. Junction estimate is
102.494–114.679°C at the 70°C bay ambient, below 125°C recommended maximum;
at 85°C it is 117.494–129.679°C, an unqualified unshaded sensitivity. Full-load
thermal measurement remains required; the inferred theta ceiling for 125°C at
70°C is 135.409°C/W. Measure the complete power knot and qualify the actual
fabricated via process; do not substitute an unfilled hole or shrink the paste.
Buck thermal qualification remains open:89°C/W is a reference-board metric,
maximum MOSFET resistance and switching loss are not specified, and80% conversion
efficiency is an input-current budgeting assumption rather than a guarantee of
acceptable junction temperature. Test the complete power knot under full load.

## Off-state and USB back-feed

**AUD-8:** U411/U421 TXU0202DCUR C5186957 now use main 3V3 on both VCCA and
VCCB. U412/U422, R443/R453 and C441/C442/C451/C452 are removed. C443/C453 remain
100 nF local VCCB bypasses, retagged to 3V3: [TI TXU0202 §12.1 and Fig12-1](https://www.ti.com/lit/ds/symlink/txu0202.pdf)
recommend a local 0.1 µF at each supply. C440/C450 remain the VCCA bypasses.
Camera U13 TPS70933DBVR and C92/C93 remain because PORT_5V3 can exceed the
TXU0202's 5.5 V maximum supply. Port ESD returns to GND. EN/OE default low;
firmware holds OE low whenever its peripheral supply is off, and lowers OE before
EN. Accepted: incorrect OE can feed an unpowered external module a few mA through
1 kΩ. Partial-power isolation still requires the installed-module bench test.

TPS2553 specifies≤1µA reverse leakage at OUT6.5 V/IN0 V **at25°C only**.
It is not an instantaneous ideal diode: powered reverse detection can take7 ms
and requires up to190 mV difference. EN input leakage is±0.5µA and FAULT off
leakage≤1µA under their stated electrical-table conditions. The datasheet does
not separately guarantee every unpowered EN/FAULT combination across temperature.
Radio USB-powered/board-off and board-on transitions must be measured; the reverse
transient can charge the shared rail before cutoff. Camera supply back-drive remains
prohibited. Small leakage does not establish a zero-voltage unpowered rail without
its discharge impedance. No unconditional back-feed immunity claim is made here.

**Back-feed through an ENABLED switch (R3-SAF-02).** TPS2553's reverse comparator
trips only when OUT exceeds IN by95/135/190 mV, after3/5/7 ms (SLVS841F §7.5 p7,
§9.3.2 p14); with r_DS(on)≤135 mΩ that is≥0.7 A of reverse current before any
blocking. A self-powered or USB-powered GPS (J410), radio (J420, LR900-F has its
own USB-C) or camera (J9) on an enabled port therefore back-feeds GPS_4V8 /
RADIO_4V8 → PORT_4V8 → U401 (TPS7A91 states no reverse-current behaviour:
Inference) → PORT_5V3, and CAM_5V → PORT_5V3, then through U400's high-side body
diode (Inference) into RAW_PROTECTED. From there U11 can keep VLOGIC and the MCU alive with the external screw
switch open. The single-switch implementation replaces the former automatic R122/R123 divider with PC1
(ACT_EN_MCU) through R122 1 kΩ and R123 100 kΩ to GND. The pyro load switch is off during MCU reset or loss of
3V3, but a still-running MCU can retain its deliberate enable: no physical ARM break remains. Treat the pyro
channel as live while any source powers the board. Connect the e-match only with the screw switch off and no USB
or self-powered port attached; perform bench work from USB with the e-match disconnected. Firmware drops UART
OEs and port ENs on a VLOGIC sag, clears PC1 and PE4 on every safety fault, and must never fire before a confirmed
accelerometer-plus-barometer launch. No separately wired switch-position input exists, so firmware cannot promise
to detect a switch opening that a back-fed supply hides. The installed dummy-load bench test measures the behavior
with each port independently powered and enabled. A passing CAD gate does not verify these firmware or transient
behaviors (D-SS-01).

The camera back-feed prohibition (REQUIREMENTS
"Camera") extends to J410 and J420.

**Port UART ESD (R3-MCU-05).** D400/D401, D410/D411, D420/D421 are ESD103-B1-02EL
(shared code with R9's RF clamps): ±15 V working, clamping at about20/36/48 V at
1/8/16 A TLP (Infineon ESD103-B1-02 datasheet; R3 review read rev 1.3 Tables 3/5
p6, R7 pass 2 v2.0 Tables 2/4/6). That clamp is far above a 3.3–5 V I/O, so the
diode only limits the surge; the port pin is protected by the 1 kΩ series resistor
into TXU0202's B-side cell, rated ±2500 V HBM (TI SCES942A §7.2 p5), and the
MCU sits behind the translator's A side. Accepted as a handling-level protection
(Inference: no system-level IEC 61000-4-2 rating is claimed); connect port
harnesses with the board unpowered on an ESD-safe bench.

**Camera supply loop split (R3-PWR-08; harness specification).** The camera's
≥5.03 V at 1 A rests on a ≤150 mΩ supply-plus-return loop (table above). Of it,
the board-end GH contacts may take up to 2 × 50 mΩ = 100 mΩ (JST eGH, maximum after
test) and the board copper CAM_5V / GND about 14 mΩ (R3 review figure, not
re-solved here), leaving **≤36 mΩ for both harness conductors and any camera-end
termination**. At about 0.134 Ω/m for 26 AWG (GH's largest wire; Inference,
typical annealed copper) that is about 0.13 m of conductor in total, roughly a
6–7 cm two-wire lead with a soldered camera end. A longer lead or a camera-end
connector needs a measured camera minimum below 5 V, a lower camera current or a
different supply arrangement (owner / harness item); measure the installed loop
four-wire.

**LR900-F maker figures (R3-REQ-08/09).** MicoAir's LR900 manual (URL above,
updated 2026-10-25): LR900-F 27 dBm (500 mW) transmit, **maximum average power
consumption 1 W**, 4.5–5 V supply, operating band **890–915 MHz** with manual
channels 0–25 for 890–915 MHz: only channels 12–25 (902–915 MHz) lie in the US
902–928 MHz band, and the FHSS channel set and its restriction are not documented.
Configure manual channels 12–25 only, or confirm the FHSS set with MicoAir before
flight (regulatory: Inference). R420's 0.348 A minimum limit covers the 1 W
average (≈0.21 A at 4.8 V), but the transmit peak is unpublished: measure the
radio's supply current at full power on J420 before flight; R420 is not changed.

## Battery-lead break ride-through (REQUIREMENTS F6; R3-PWR-02)

C84 sits on VLOGIC after U11. In a battery-lead break it also back-feeds
RAW_PROTECTED through U11: TPS2121 blocks reverse current only above IRCB
0.2/1/2 A (SLVSEA3F §7.5 p8), and the port buck U400 on RAW_PROTECTED has EN tied
to VIN, so it keeps drawing until RAW_PROTECTED collapses; firmware shedding of the
ports cannot act in time (TPS2553 turn-off up to3 ms, SLVS841F §7.5 p7). Energy
from 7.4 V, constant-power loads, no credit for RAW_PROTECTED, C6 / C7 capacitance
or for U11 blocking (Calc / Inference; `parts_budget.json`
`battery_break_ride_through_ms`; each case includes an explicit 16.93 mW constant allowance for R92 at 7.4 V and minimum resistance, D-OA-05):

| Case (load at the converter inputs) | C84 300.8 µF, to 3.5 V / 3.8 V | C84 470 µF, to 3.5 V / 3.8 V |
|---|---|---|
| (a) ports off, logic shed: 0.62 W retained + 0.1 W idle port chain | 8.7 / 8.2 ms | 13.6 / 12.9 ms |
| (b) ports off, no shed: 0.6–1.4 W logic (`pass1_electrical.md` §4.4, no RF) + 0.1 W | 4.2–8.9 / 4.0–8.5 ms | 6.6–13.9 / 6.2–13.2 ms |
| (c) camera 1 A, radio, GPS on: 9.2–10.1 W ports + 0.6–1.4 W logic | 0.55–0.65 / 0.53–0.62 ms | 0.87–1.02 / 0.82–0.96 ms |

3.5 V is the logic floor used since R7; 3.8 V is the AP63203's minimum input
(DS41326 p4). Case (a) assumes shedding from the first moment (detection latency
not credited). R9 had the same camera-on limitation (about 1–3 ms, its F6 text);
R10 adds the radio and GPS to it.

**OQ-5 hardware option (not adopted by the owner, 2026-10-28):** an AP63201 EN divider
from RAW_PROTECTED to GND in place of the EN–VIN tie (DS41326 p10 eq. 1–2), on
existing BOM values R5 47 kΩ 1% (C25819) / R6 10 kΩ, turns the port buck off at
VOFF 5.73–6.30 V (6.01 V typical; VEN_L 1.05–1.15 V, EN currents typical) and back
on at VON 6.49–6.94 V, which puts this file's own rule "shed all port enables
before RAW_PROTECTED falls below 6.2 V" into hardware. In a lead break with all
ports on, C84 then carries the ports only from 7.4 V down to VOFF (0.29–0.53 ms at
the lowest VOFF) and the logic alone below it: ride-through at least 4.6 / 7.2 ms
with shedding and 2.3 / 3.7 ms without (300.8 / 470 µF, to 3.5 V;
`parts_budget.json` `option_oq5_*`). Cost: two 0603 parts on existing codes, a
0.13 mA divider load, a placement and routing change at U400.2; the ports turn off
whenever a four-servo stall pulls the pack below about 6 V (already accepted for
the firmware rule).

## Local lands, envelopes and assembly

All models are small generated fit envelopes, not vendor STEP models. Their paths
use `${KIPRJMOD}/kilib/rocket.3dshapes`. New lands have no clearance overrides.

| Part | Source and local land | Qualification status |
|---|---|---|
| DB125 black C52993880; green C466970 | [DORABO supplier-linked T0-1 drawing](https://atta.szlcsc.com/upload/public/pdf/source/20251124/8C215F69B14C8E54AE0F8E5023D4AE9F.pdf):3.5 mm pitch,7.0×7.4×8.6 mm body,28–16 AWG,10 A UL/13.5 A IEC,0.2 N·m,4–5 mm strip. Pads±1.75 mm,Ø1.9 copper/Ø1.3 drill. Bodyy−3.9…3.5; wire-entry+y. | This T0-1 supplier drawing recommendsØ1.2 holes; the [older maker drawing](https://www.nbdibo.com/wp-content/uploads/2020/06/DB125-3.5-XXP-C-S.pdf) was reported as1.3 in round1.1.3 selected conservatively. Nominal copper gap1.6 mm and radial annulus0.3 mm are calculated, not actual manufactured measurements. Final board must hold≥1.5 mm including tracks; no role alias inherited from R9. Envelope7.3×7.7×8.9 includes general tolerance. J1 peak≈6 A is below10 A; validate installed wire/contact heating. |
| GH2 C161690 | [JST eGH pp2–3](https://www.jst-mfg.com/product/pdf/eng/eGH.pdf):1.25 mm pitch; pads0.6×1.7 atx±0.625,y1.95; tabs1×2.8 atx±2.475,y−1.4. | Same frame as GH4; mechanical pads unnamed. Body5.75×4.25, mated height7.3 mm, further3 mm wire allowance belongs to fit gate.1 A withAWG26; contact50 mΩ maximum after test. Harness allocation must include both supply and return contacts. |
| GH4 C161692 | Existing M3_GH_BM04B_GHS_TBT land/model, same JST drawing. | Used for camera/GPS/radio; keyed connectors remain electrically different, require labels and harness pin check. |
| TPS7A9101 C2878140 | TI DSK0010A:0.6×0.25 pads,0.5 pitch,row centres±1.15; pad11 1.2×2.0. | Maker land, thermal-pad paste split to the maker's84%. GAP-3 adds two 0.5/0.3 GND vias in pad11, resin-filled/copper-capped planar VIPPO; original paste windows unchanged (thermal estimate above). Body maximum2.6×2.6×0.8 mm. |
| C84 MA25V470M8x10 C46550466 | [MA-series supplier datasheet](https://atta.szlcsc.com/upload/public/pdf/source/20260306/24758A4FC016E80367B87853635CDCC1.pdf), logo JIERRUI/深圳市捷而瑞:470µF25 V,25 mΩ/100 kHz,4.1 A ripple/105°C; tolerance±20%, endurance±20% of initial andESR≤150%. Base8.3±0.2, lead gap3.1±0.2,width0.8–1.1, height10±0.5 plus0.3 mm projection conservatively. | Inference: derived3.5×1.7 pads at±3.25 give3.0 mm copper gap and toe allowance. Envelope8.5×8.5×10.8. Not a maker-recommended land: datasheet supplies no land/reflow profile. GAP-4: manually fit AFTER ALL REFLOW; do not expose this part to an unprovided reflow profile. Keep fitted BOM/CPL identity/polarity, with manual-fit order remarks. Qualify the hand-solder process and first-article capacitance/ESR, polarity and height before release. |

C84 conservative beginning/end-of-life capacitance is470×0.8×0.8=300.8µF,
ESR at most37.5 mΩ under the specified endpoint test. Neither number supplies an
unpublished cold ESR bound. R10 hold-up simulation must use these values and a
separately sourced temperature factor; nominal470µF is insufficient.

Supplier/EasyEDA API calls for the four new package codes returnedHTTP403 in this
session. Their pad-number/orientation check remains open; no CPL rotation correction
has been guessed. Local maker geometry was parsed and checked using KiCad. Final
BOM/CPL gate must fetch each actual supplier package and check numbered pads and
GH mechanical tabs.

**CPL orientation items to confirm in JLC's placement preview (R4-BOM-01 to -03;
`tools/jlc_corrections.json`, residuals are the worst pad distance between our land and the EasyEDA
footprint):**

- **L400 (C1329837, SRP5030T-6R8M, land `M3_SRP5030TA` at (24.2, 5.55), rotation 0):** EasyEDA has no entry for
  C1329837, so the JLC orientation comes from the proxy C189932 (SRP5030T-100M, the same SRP5030T package): rotation
  correction 0, offset 0, residual 0.15 mm. The part is symmetric (two terminals, no pin-1 mark that matters
  electrically), so a 180° error is harmless electrically; the land itself is still to be checked against Bourns' own
  drawing (the proxy supplies the numbering, not the dimensions; Inference until done).
- **U411 / U12 / U421 (TXU0202DCUR C5186957, land `M3_TXU0202_DCU`, top, rotation −90 on the board):** correction
  180°, offset 0, residual 0.147 mm. Pin 1 on JLC's footprint is matched by pad
  geometry, not by the mark: confirm pin 1 in JLC's preview on all three before paying.
- **C84 (C46550466, MA25V470M8x10, top at (38.5, 74.0), rotation 90):** correction 0, residual 0.045 mm. The board has
  + on pad 1 (VLOGIC at (38.5, 77.25)) and − on pad 2 (GND at (38.5, 70.75)); the polarity in JLC's CPL / preview
  is not confirmed (the MA-series datasheet gives no land, see the parts table above): confirm + on the VLOGIC pad in the
  preview, and check the fitted part's polarity stripe on the first boards (ORDERING §8). `parts_stock.json` is a dated component snapshot, not a final
BOM stock gate. Camera ILIM resistor C185349 (R430): 17 in stock against a 3,610-piece minimum purchase
(JLC, 2026-10-27): sufficient for a small prototype batch only; recheck the actual quantity before ordering.

## Servo-reference return and mechanical mass

The adopted O6 harness topology is a pack-negative star: every servo has its own
paired positive/negative motor lead directly to the pack. Each J122 reference wire
returns to the pack star, **not to the servo's motor-negative terminal**. Keep motor
return contacts separate from board-reference contacts. If their finite star
transfer resistance is≤1 mΩ at7.68 A, the potential spread is≤7.68 mV. With four
reference branches each≥50 mΩ, an intentionally conservative independent-branch
sum is4×7.68 mV/50 mΩ=0.6144 A through the board, ignoring the additionalJ1 return
impedance. Qualify board/J122 reference copper for1 A; record≤0.62 A residual under
these conditions. Four-wire measurements must establish both transfer resistance
and minimum branch resistance on the assembled harness. Do not obtain the latter
from a guessed wire length. Strain relief and star attachments are bench acceptance
items. An open reference branch must leave the servo's direct motor ground intact.

If reference leads instead join the negative at each servo,50 mΩ motor return and
130 mΩ reference return permit2.13 A through the board at four stalls; shorter
reference leads can approach the whole7.68 A. That alternative is not the accepted
R10 harness topology. This analysis does not claim zero servo return.

`masses.json` explicitly lists R10 body and additive plug/local-wire masses. These
are conservative **Inference** allowances, not manufacturer or measured masses.
A plate result using them remains conditional on weighing the populated assembly
and supporting the long leads independently. Four corner mounting alone and bore
fit must be established from the final board and actual mated plugs.

## Round-5 power and pin records (R5-PWR-01 … -04, R5-MCU-04 / -05)

Figures are Calc from the netlist values unless marked; datasheet figures marked "reviewer" are the round-5
reviewer's readings and were not re-read from the PDFs in this pass (Inference until checked).

- **U9 OVLO pin range (R5-PWR-01).** U9.2 sits on R82 2 MΩ / R83 280 kΩ (ratio 280 / 2280 = 0.1228). The pin leaves
  the recommended 0.5–1.5 V range (reviewer, TPS259470L) above an input of 1.5 / 0.1228 = about 12.2 V, reaches
  2.44 V at the 19.9 V D8 clamp, and would reach the 6.5 V absolute maximum (reviewer) only at 52.9 V, far above the clamp.
  Above 12.2 V the part is in the over-voltage state it is there to detect; the out-of-range pin in that
  fault state is recorded and accepted (Inference: behaviour of the pin outside its range is not specified).
- **TP89 on U9 ILM (R5-PWR-02).** TP89 is the BAT_ILIM node (U9 pin 9, R84 750 Ω to GND; C81 4.7 nF is on BAT_DVDT, pin 7), an analog monitor that the
  maker marks "do not leave floating" (reviewer). Bench probing is high-impedance only; never load, short or drive
  it (ORDERING §8 bench gates). Loading it changes the current limit and the monitor reading.
- **AP63201 quiescent current (R5-PWR-03).** 258 µA per the Diodes AP63200/1/3/5 datasheet (DS41326; reviewer); LCSC's
  22 µA is the AP63200 / 63203 / 63205 figure. No idle figure in this directory used 22 µA; the 11 mA
  "quiescent, divider and bleeder" allowance in the all-ports-shorted budget covers 0.258 mA of it with margin (Calc).
- **Low-pack dropout (R5-PWR-04).** The AP63201's loaded dropout is typical-only (already stated above under
  "Inference, stall input"); ORDERING §8 adds a bench step with the port rails read at a 6.0 V loaded battery.
- **PA6 (VLOGIC_SENSE) single-fault pin damage (R5-MCU-04).** The divider is R60 100 kΩ (VLOGIC) / R61 10 kΩ with C60
  10 nF, and there is no 4.7 kΩ pin resistor. A shorted R60 puts VLOGIC (up to RAW_PROTECTED, 8.4 V nominal full
  pack) straight on PA6, an FT_a pin whose limit is min(VDD, VDDA, VBAT) + 4.0 V = 7.3 V with 0 mA injection
  allowed (DS12110 Tables 21 / 22; reviewer): above 7.3 V the pin is overstressed. Single-fault case, pin damage;
  listed as an owner deviation by the orchestrator. Mitigation none on the board.
- **PB1 (CAM_5V_SENSE) single-fault pin damage (R5-MCU-04).** The divider is R104 10 kΩ (CAM_5V) / R105 1 kΩ with C94,
  and PB1 has no 4.7 kΩ pin resistor. An open R105 puts CAM_5V (5.456 V nominal) on PB1 through R104 10 kΩ; PB1
  is a TT_a pin with a 4.0 V limit (reviewer) and the fault current is about 0.15–0.19 mA ((5.456 − 4.0) / 10 kΩ to
  (5.456 − 3.56) / 10 kΩ, depending on where the clamp conducts; the reviewer's figure is 0.19 mA). Single-fault
  case, pin damage; listed as an owner deviation by the orchestrator.
- **VBUS_SENSE threshold (R5-MCU-05).** PC8 = VBUS / 2 (R9 1 kΩ / R110 1 kΩ 1 %). At 4.4 V VBUS the node is 2.20 V,
  below VIH = 0.7 × VDD = 2.31 V at 3.3 V (VIH as reviewer's figure, DS12110 row not re-read): VBUS detection needs
  VBUS ≥ 4.62 V (2 × 2.31 V) at VDD 3.3 V. A host or charger within USB's 4.40–5.25 V band can read "absent".
  Firmware must not treat a low PC8 as "no USB" in a safety decision (binding note).
- **LSEON (R5-MCU-02).** PC14 is OSC32_IN and drives BUZZ_DRV through R162; VBAT is tied to 3V3, so a stray LSEON set in
  the backup domain survives NRST and would load the buzzer node: LSEON stays 0 and the backup domain is never
  set up for the LSE (binding note).

## Round-6 records (historical pre-AUD hardware; Calc unless marked)

- **USB-only attach (R6-PWR-02).** With only USB-C connected, VBUS feeds VLOGIC through U10 (TPS2553, current limit
  355–445 mA as the round-6 reviewer reads it; ILIM resistor and datasheet limit not re-read here) and U11 behind it:
  C84 470 µF, C6 and C7 22 µF each and C99 100 nF are charged through that limit. With the load ignored, the charge
  of about 514 µF to 5 V (2.57 mC) takes 5.8 ms at 445 mA and 7.2 ms at 355 mA (dV/dt about 0.7–0.87 V/ms; Calc).
  Bench: attach USB alone and measure the VBUS current and dV/dt, and the 3V3 start-up. USB-only programming or logging
  needs a host that allows at least 450 mA (Inference: a USB 2.0 port allows 500 mA after enumeration, 100 mA before; the
  board's draw with the MCU running and the ports off is not measured).
- **Q120 / Q121 turn-on time (R6-PWR-03).** The gate network is R120 100 kΩ (gate to source, RAW side) in parallel with
  R121 10 kΩ (gate to Q122's drain) charging C120 2.2 µF: R120 ∥ R121 = 9.09 kΩ, tau = 9.09 kΩ x 2.2 µF = 20.0 ms.
  Q120 / Q121 are fully enhanced about 22 ms after Q122 turns on (1.1 tau: Vgs about 67 % of its final value, which
  is 0.909 x RAW, so about −4.5 V at 7.4 V; threshold and Rds(on) against Vgs not re-read; Calc). This supersedes the
  microsecond-scale switching figures of R9's servo-power path for R10, where Q120 / Q121 only switch the pyro bus:
  RAW_ACT (TP120) rises over tens of milliseconds, so a gate or RAW_ACT reading taken sooner than about 50 ms after the
  enable is not valid (Inference: 50 ms is about 2.5 tau).
- **PORT_5V3 In2 band narrowest point (R6-PWR-01).** 1.20 mm at x about 30.25 (a via clearance notch; round-6
  reviewer's measurement, not re-measured here); `tools/ipc2152.py` internal fit, 1.20 mm, 2.02 A: 8.5 °C (re-computed),
  so the earlier 1.49 mm / 6.7 °C figure is superseded.

## Round-7 records (R7-PWR-02, R7-BOM-03, R7-MCU-03 / -04; Calc unless marked)

- **USB attach inrush (R7-PWR-02).** Behind U10 sit C84 470 µF, C6 / C7 22 µF each and C99 100 nF, about 514 µF; charged to about 4.7 V that is about 2.4 mC, which at U10's 355–445 mA limit (round-6 reviewer's reading, not re-read) takes about 6 ms. USB 2.0's attach allowance of about 10 µF (50 µC at 5 V) is quoted from memory of the specification (**Inference**, not re-read), so the board is about 48× over it. USB-only attach is host-dependent: test against a current-limited hub and record the hosts that fail (ORDERING §8 bench gate).
- **Camera ILIM fallback (R7-BOM-03).** TI SLVS841F (revision F, August 2016), equation 1, read in this pass: IOSmax = 22980 / RILIM^0.94 mA, IOSnom = 23950 / RILIM^0.977, IOSmin = 25230 / RILIM^1.016 (RILIM in kΩ, 15–232 kΩ). With RILIM ±2 % (1 % initial plus 1 % temperature, as the camera bounds above): 22.6 kΩ (R430, C185349) gives 1.041–1.249 A (reproduces the record above); a **22 kΩ** resistor (C31850, basic; code and value as the reviewer gave them, **not checked on LCSC here**) gives 1.070–1.282 A. The camera-short case with the other two ports at their allocations rises from 1.711 A to about 1.744 A and the all-ports-shorted draw from 2.022 A by about 0.033 A. A fallback only, **not adopted**: it needs the port budget and U400's peak-current check redone first. R430 itself: 17 in stock, 3,610-piece minimum purchase (JLC, 2026-10-27); confirm acceptance in the quote.
- **W25Q128JV erase times (R7-MCU-04).** Winbond W25Q128JV Rev I (08/23/2021), AC characteristics (erase and program), read in this pass: sector (4 KB) erase 45 ms typical / 400 ms maximum, 32 KB block 120 ms / 1,600 ms, 64 KB block 150 ms / 2,000 ms, chip erase 40 s / 200 s, /CS high to next instruction after suspend (tSUS) 20 µs. The earlier "about 45 ms" was the typical value only; the maximum is 400 ms.
- **IWDG period (R7-MCU-03).** LSI 29.76–33.60 kHz (DS12110 Table 39 as the reviewer read it; **not re-read**, ST's server refused the download in this pass) gives a nominal 32 ms setting a worst case of about 34 ms (32 ms × 32 kHz / 29.76 kHz ≈ 34 ms with a 32 kHz-based reload), inside F6's 50 ms target. A started IWDG cannot be stopped; a loader jump after it starts lands in the application about 32 ms later with BOOT0 low (**Inference**, AN2606 not read).
- **PA15 reset state (R7-MCU-01).** PA15 resets to JTDI with the internal pull-up, not analog (**Inference**: the reviewer's reading of DS12110 / RM0433, not re-read); firmware sets it to analog explicitly.

## Round-8 records (historical pre-AUD hardware; records only, board unchanged)

- **GPS UART level (R8-MCU-02).** HGLRC's M100 Mini page gives the supply as 3.3–5 V and does not specify the UART
  logic level. **Inference:** a u-blox M10 part with 3.3 V I/O; the J410 translator (TXU0202, B side on GPS_IO_3V3
  from U412, enabled with GPS_4V8)
  tolerates a B2 input up to 5.5 V, so a 3.3 V or a 5 V device both stay inside its rating. Measure the module's TX
  high level before flight; do not treat the level as qualified.
- **GPS cable (R8-MCU-02).** The GPS's own cable is SH1.0-4P (plan, as the owner's list gives it; not re-checked
  against HGLRC's drawing here), while J410 is a JST GH 1.25 mm 4-position header: a **SH1.0-to-GH1.25 harness
  adapter** is needed, with the pin order of ORDERING §8 "Camera harness and port cables" checked end to end.
- **DB125 height (R8-MEC-05).** DORABO T0-1 drawing (read 2026-10-28, link in the "Local lands" table above): body
  height 8.60 mm with the drawing's general tolerance ±0.30 mm for 6–10 mm (so 8.9 mm maximum, the envelope used),
  body width 7.40 mm, pin length below the body 3.90 mm. A first-article caliper check of the seated terminal remains
  advised.
- **Port UART break (R8-MCU-01).** With a port's OE high and its device unplugged or unpowered, the TXU0202's 5 MΩ
  input pull-down holds the MCU RX low, a continuous break (Inference from the pull-down, not measured): the firmware
  obligation is in the binding note and M3_R10 "Firmware".

## R92 discharge change before the fresh round 9 (2026-10-28)

OQ-2's requalification must include U9 OUT as well as IN: below -10 C, TPS25947's input limit is
`max(-15 V, VOUT - 21 V)` (TI SLVSFC9C p. 7). R92 changes from 10 kohm to **3.3 kohm, 1%, 0603** on the same land
and RAW_PROTECTED-to-GND nets. This reduces retained output voltage after unplugging without adding a component or
changing the pack-change waiting rule. U11's reverse-current threshold is not treated as an ideal blocking diode.

The replacement is **UNI-ROYAL 0603WAF3301T5E, C22978**. The
[LCSC part specification](https://www.lcsc.com/product-detail/Chip-Resistor-Surface-Mount_Uniroyal-Elec-0603WAF3301T5E_C22978.html)
gives 100 mW, 75 V, +/-1%, +/-100 ppm/C and -55 to +155 C; the same 0603 package family preserves the existing land.
[JLC's part page](https://jlcpcb.com/partdetail/C22978) and the exact-code public lookup on 2026-10-28 identify it as
Basic, with 5,345,859 available and a 1-piece tier of USD 0.0022. This adds one Basic code, no extended code; refresh
the complete BOM cost/stock evidence before ordering. The fields in `circuit.json` agree on this exact part.

At 8.5 V the nominal loss is 21.89 mW (14.67 mW more than 10 kohm). The hot-plug record includes the board's
capacitor inventory, a doubled-C84 sensitivity and the other explicit model assumptions. With all 1675.3395136 uF
of that conservative inventory initially at 8.5 V, R92 alone at its +1% tolerance and +0.65% temperature corner
(3354.6645 ohm) gives 5.954856276 V after two seconds in the common-node model. No load current or divider bleeds are
credited. These are CAD estimates, not a guarantee of C84's unprovided capacitance-versus-temperature curve or
of arbitrary converter reverse-energy behavior. The existing simultaneous U9 IN / OUT reverse-plug bench
qualification remains mandatory.

## R166 damper change before the fresh round 9 (2026-10-28)

OQ-2's model selects **0.36 Ω, 1%, UNI-ROYAL 25121WF360LT4E / C168925** in place of 0.33 Ω. The preliminary
feed with 0.33 Ω reaches -15.100485 V at the cold/tolerance corner; 0.36 Ω passed that model's 2304 cases.
The preliminary local-shunt approximation is superseded by D-OA-07: C88 is now fed before U9 and its actual
trace path stays in the model. Final qualification comes from the production-bound model results in
`hotplug_results.json`: all 2304 required cases pass on board `3b960b46…`, with -14.497874 V minimum and
8.525257 V/µs maximum falling slew. Its assumptions in `hotplug.md` remain simulation inferences.
[LCSC's exact-part page](https://item.szlcsc.com/180309.html) confirms the identity and 2512 package.
[UNI-ROYAL SMD-SP-001 V10, pp. 4–6](https://www.uni-royal.cn/en/images/userfile/file/1753752986c56505e6d9ab55c7.pdf)
gives 6.35 ±0.10 × 3.20 ±0.20 × 0.55 ±0.10 mm, matching the existing family and land; 1 W through 70 °C,
derating to zero at 155 °C; and ±800 ppm/°C below 1 Ω. Over -40…85 °C, tolerance and temperature give
0.3378672–0.3825072 Ω, swept independently of the capacitor and copper corners. `circuit.json` binds the new
value, order code and maker part without changing nets or footprint. Refresh BOM stock and cost before ordering.

**Pulse qualification remains open.** The maker's ordinary thick-film specification gives a five-second overload
test at 2.5 times sqrt(P×R), or 1.5 V for this value at the 1 W rating; it supplies no microsecond pulse curve.
The absolute 200 V family ceiling is not the low-value resistor's allowable continuous voltage. The final sweep
gives 504.292318 W peak and 2.888490051 mJ over 150 µs in different corners; separate half-step checks give
504.293235 W and 2.888489824 mJ. A low energy alone does not prove survival. Obtain maker confirmation for
that waveform or test repeated hot/cold insertions and resistance drift. This is a component-data/model update,
not a claim of measured pulse durability or board acceptance.
