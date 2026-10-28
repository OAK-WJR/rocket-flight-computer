# R10 component and harness qualification

This is the component contract, not board acceptance. `parts.json` contains exact
parts, pads and intended nets for the schematic generator; its final `circuit.json`
resolves connector role names and MCU signals. `r10_parts.py` reproduces five local
lands, five small VRML envelopes, and `parts_budget.json`. It never edits the board.
Sources were read on 2026-10-26 locally; the R3 fix pass (2026-10-27) re-read
DS41326, SLVS841F, SLVSEA3F, SBVS282A, SCES942A and the LR900 manual. No physical
tests were performed.

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

**Inference, LDO thermal (R3-PWR-09):** at the allocated460 mA output, extreme
rail tolerance and4 mA quiescent draw, loss≈0.406 W. **U401's thermal pad 11 has
no thermal via:** M2 bars vias in SMD pads, so the pad (bottom side, 1.2×2.0 mm at
(27.6, 13.6)) joins the B.Cu GND pour solidly and the nearest GND via, (27.6,
14.95), sits 0.35 mm (centre) outside the pad edge; In2 under it is PORT_5V3
(pad, via and In2 zone read on board `579575bd…` in round 4: pad 11 1.2×2.0 mm at (27.6, 13.6), the nearest GND via
(27.6, 14.95) 1.35 mm centre to centre from the pad centre, In2 zone R10_PORT_5V3_In2; the round-4 routing pass was
not re-measured on `b242ab8e…`). TI's62.5°C/W thetaJA (SBVS282A p4) is the
JEDEC high-K board figure and is not used. Without vias under the pad, take
80–110°C/W (Inference, outer-layer pour spreading only, RθJC(bot)7.8°C/W): the
full allocation gives a32–45 K rise, junction≈117–130°C at85°C ambient and
≈102–115°C in the70°C bay, against the125°C recommended maximum (SBVS282A p4;
thermal shutdown160°C typical). A typical load (radio about0.2 A from LR900-F's
1 W maximum average, GPS about0.05 A) is about0.19 W, +15–21 K. Measure U401 with
a thermal camera at full port load (ORDERING R10 bench list); the 85°C case is the
unshaded worst case (REQUIREMENTS "Temperature").
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

**Back-feed through an ENABLED switch (R3-SAF-02).** TPS2553's reverse comparator
trips only when OUT exceeds IN by95/135/190 mV, after3/5/7 ms (SLVS841F §7.5 p7,
§9.3.2 p14); with r_DS(on)≤135 mΩ that is≥0.7 A of reverse current before any
blocking. A self-powered or USB-powered GPS (J410), radio (J420, LR900-F has its
own USB-C) or camera (J9) on an enabled port therefore back-feeds GPS_4V8 /
RADIO_4V8 → PORT_4V8 → U401 (TPS7A91 states no reverse-current behaviour:
Inference) → PORT_5V3, and CAM_5V → PORT_5V3, then through U400's high-side body
diode (Inference) into RAW_PROTECTED. From there U11 feeds VLOGIC (the logic can
stay up) and R122/R123 put about half of RAW_PROTECTED on ACT_EN: at a back-fed
≈4.4 V that is ≈2.2 V, above AO3400A's1.45 V maximum threshold, so Q122 turns the
pyro-bus load switch Q120/Q121 on and RAW_ACT is live from BAT_IN **with the power
switch open** (Inference). Mitigation: firmware drops every port EN and UART OE
when the power switch opens or VLOGIC sags (binding note), all EN pull-downs keep a
reset or unpowered MCU from enabling a port, and the ORDERING R10 bench step checks
it with each port device self- or USB-powered and enabled (RAW_ACT < 1 V within
1 s of opening the switch). The camera back-feed prohibition (REQUIREMENTS
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
`battery_break_ride_through_ms`):

| Case (load at the converter inputs) | C84 300.8 µF, to 3.5 V / 3.8 V | C84 470 µF, to 3.5 V / 3.8 V |
|---|---|---|
| (a) ports off, logic shed: 0.62 W retained + 0.1 W idle port chain | 8.9 / 8.4 ms | 13.9 / 13.2 ms |
| (b) ports off, no shed: 0.6–1.4 W logic (`pass1_electrical.md` §4.4, no RF) + 0.1 W | 4.3–9.1 / 4.0–8.7 ms | 6.7–14.3 / 6.3–13.5 ms |
| (c) camera 1 A, radio, GPS on: 9.2–10.1 W ports + 0.6–1.4 W logic | 0.55–0.65 / 0.53–0.62 ms | 0.87–1.02 / 0.82–0.96 ms |

3.5 V is the logic floor used since R7; 3.8 V is the AP63203's minimum input
(DS41326 p4). Case (a) assumes shedding from the first moment (detection latency
not credited). R9 had the same camera-on limitation (about 1–3 ms, its F6 text);
R10 adds the radio and GPS to it.

**Owner question OQ-5 (hardware option, not implemented):** an AP63201 EN divider
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
| TPS7A9101 C2878140 | TI DSK0010A:0.6×0.25 pads,0.5 pitch,row centres±1.15; pad11 1.2×2.0. | Maker land, thermal-pad paste split to the maker's84%. No via in pad 11 (M2); it joins the B.Cu GND pour solidly, nearest GND via0.35 mm outside the pad edge (thermal estimate above). Body maximum2.6×2.6×0.8 mm. |
| C84 MA25V470M8x10 C46550466 | [MA-series supplier datasheet](https://atta.szlcsc.com/upload/public/pdf/source/20260306/24758A4FC016E80367B87853635CDCC1.pdf), logo JIERRUI/深圳市捷而瑞:470µF25 V,25 mΩ/100 kHz,4.1 A ripple/105°C; tolerance±20%, endurance±20% of initial andESR≤150%. Base8.3±0.2, lead gap3.1±0.2,width0.8–1.1, height10±0.5 plus0.3 mm projection conservatively. | Inference: derived3.5×1.7 pads at±3.25 give3.0 mm copper gap and toe allowance. Envelope8.5×8.5×10.8. Not a maker-recommended land: datasheet supplies no land/reflow profile. Verify polarity, mounting height and manufacturer/JLC reflow compatibility before fabrication. A fitted part is not qualified by stock alone. |

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

## Round-6 records (R6-PWR-02 / -03; Calc unless marked)

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
