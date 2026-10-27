# R10 component and harness qualification

This is the component contract, not board acceptance. `parts.json` contains exact
parts, pads and intended nets for the schematic generator; its final `circuit.json`
resolves connector role names and MCU signals. `r10_parts.py` reproduces five local
lands, five small VRML envelopes, and `parts_budget.json`. It never edits the board.
Sources were read on 2026-10-26 locally. No physical tests were performed.

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
  Keep the existing maker land. At8.4 V input,5.456 V output, Lmin5.44µH and
 470 kHz, calculated ripple is approximately0.75 A; 2 A plus half this ripple
  is below the buck's2.5 A minimum peak limit. Isat is a typical20% drop rating,
  not an absolute limit.
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

R430(camera)22.6 kΩ, R420(radio)66.5 kΩ, R410(GPS)120 kΩ include1% initial
plus1% temperature allowance in the switch equations. Approximate bounds are
camera1.041–1.249 A, radio0.348–0.453 A, GPS0.191–0.260 A.
All three simultaneous port shorts plus11 mA for quiescent/divider/bleeder load
stay below2 A. A camera short with the other two at their normal allocations is
1.711 A. The LDO's two shorted ports stay below its1 A rating. Shorted switch
outputs dissipate watts before shutdown; do not characterize this as continuous
thermal capability. Hardware limits current even before the MCU handles FAULT.

**Inference, upstream coordination:** with≥80% buck efficiency,5.8 V buck input,
logic path≤0.5 A and all port shorts, U9 current is below2.9 A, versus its3.96 A
minimum limit. Buck's own3.1 A maximum peak limit plus0.5 A logic is3.6 A.
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

**Inference, LDO thermal:** at the allocated460 mA output, extreme rail tolerance
and4 mA quiescent draw, loss≈0.406 W; TI's62.5°C/W reference-board thetaJA gives
junction≈110.4°C at85°C ambient. Actual board copper must be reviewed and measured.
Solder pad11, provide ground heat spreading and thermal vias in the board.
Buck thermal qualification remains open:89°C/W is a reference-board metric,
maximum MOSFET resistance and switching loss are not specified, and80% conversion
efficiency is an input-current budgeting assumption rather than a guarantee of
acceptable junction temperature. Test the complete power knot under full load.

## Off-state and USB back-feed

TXU0202DCUR C5186957 and TPS70933DBVR C89347 reproduce the camera's two-domain
UART isolation separately for radio and GPS. Their peripheral supply comes from
the corresponding switched port; OE defaults low. Port ESD must return to GND,
never clamp an externally powered line into main3V3. Firmware must disable OE
before switching a port off. See the final schematic contract for actual nets.

TPS2553 specifies≤1µA reverse leakage at OUT6.5 V/IN0 V **at25°C only**.
It is not an instantaneous ideal diode: powered reverse detection can take7 ms
and requires up to190 mV difference. EN input leakage is±0.5µA and FAULT off
leakage≤1µA under their stated electrical-table conditions. The datasheet does
not separately guarantee every unpowered EN/FAULT combination across temperature.
Radio USB-powered/board-off and board-on transitions must be measured; the reverse
transient can charge the shared rail before cutoff. Camera supply back-drive remains
prohibited. Small leakage does not establish a zero-voltage unpowered rail without
its discharge impedance. No unconditional back-feed immunity claim is made here.

## Local lands, envelopes and assembly

All models are small generated fit envelopes, not vendor STEP models. Their paths
use `${KIPRJMOD}/kilib/rocket.3dshapes`. New lands have no clearance overrides.

| Part | Source and local land | Qualification status |
|---|---|---|
| DB125 black C52993880; green C466970 | [DORABO supplier-linked T0-1 drawing](https://atta.szlcsc.com/upload/public/pdf/source/20251124/8C215F69B14C8E54AE0F8E5023D4AE9F.pdf):3.5 mm pitch,7.0×7.4×8.6 mm body,28–16 AWG,10 A UL/13.5 A IEC,0.2 N·m,4–5 mm strip. Pads±1.75 mm,Ø1.9 copper/Ø1.3 drill. Bodyy−3.9…3.5; wire-entry+y. | This T0-1 supplier drawing recommendsØ1.2 holes; the [older maker drawing](https://www.nbdibo.com/wp-content/uploads/2020/06/DB125-3.5-XXP-C-S.pdf) was reported as1.3 in round1.1.3 selected conservatively. Nominal copper gap1.6 mm and radial annulus0.3 mm are calculated, not actual manufactured measurements. Final board must hold≥1.5 mm including tracks; no role alias inherited from R9. Envelope7.3×7.7×8.9 includes general tolerance. J1 peak≈6 A is below10 A; validate installed wire/contact heating. |
| GH2 C161690 | [JST eGH pp2–3](https://www.jst-mfg.com/product/pdf/eng/eGH.pdf):1.25 mm pitch; pads0.6×1.7 atx±0.625,y1.95; tabs1×2.8 atx±2.475,y−1.4. | Same frame as GH4; mechanical pads unnamed. Body5.75×4.25, mated height7.3 mm, further3 mm wire allowance belongs to fit gate.1 A withAWG26; contact50 mΩ maximum after test. Harness allocation must include both supply and return contacts. |
| GH4 C161692 | Existing M3_GH_BM04B_GHS_TBT land/model, same JST drawing. | Used for camera/GPS/radio; keyed connectors remain electrically different, require labels and harness pin check. |
| TPS7A9101 C2878140 | TI DSK0010A:0.6×0.25 pads,0.5 pitch,row centres±1.15; pad11 1.2×2.0. | Maker land, thermal-pad paste split to the maker's84%; ground vias supplied by board generator. Body maximum2.6×2.6×0.8 mm. |
| C84 MA25V470M8x10 C46550466 | [MA-series supplier datasheet](https://atta.szlcsc.com/upload/public/pdf/source/20260306/24758A4FC016E80367B87853635CDCC1.pdf), logo JIERRUI/深圳市捷而瑞:470µF25 V,25 mΩ/100 kHz,4.1 A ripple/105°C; tolerance±20%, endurance±20% of initial andESR≤150%. Base8.3±0.2, lead gap3.1±0.2,width0.8–1.1, height10±0.5 plus0.3 mm projection conservatively. | Inference: derived3.5×1.7 pads at±3.25 give3.0 mm copper gap and toe allowance. Envelope8.5×8.5×10.8. Not a maker-recommended land: datasheet supplies no land/reflow profile. Verify polarity, mounting height and manufacturer/JLC reflow compatibility before fabrication. A fitted part is not qualified by stock alone. |

C84 conservative beginning/end-of-life capacitance is470×0.8×0.8=300.8µF,
ESR at most37.5 mΩ under the specified endpoint test. Neither number supplies an
unpublished cold ESR bound. R10 hold-up simulation must use these values and a
separately sourced temperature factor; nominal470µF is insufficient.

Supplier/EasyEDA API calls for the four new package codes returnedHTTP403 in this
session. Their pad-number/orientation check remains open; no CPL rotation correction
has been guessed. Local maker geometry was parsed and checked using KiCad. Final
BOM/CPL gate must fetch each actual supplier package and check numbered pads and
GH mechanical tabs. `parts_stock.json` is a dated component snapshot, not a final
BOM stock gate. Camera ILIM resistor C185349 had only17 units: sufficient for a
small prototype batch only; recheck the actual quantity before ordering.

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
