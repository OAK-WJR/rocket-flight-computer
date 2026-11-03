# Round 12: independent power and electrical review

Assigned commit: `d57b216c365fc8d18896bceba37f63caf20d52a4`.
PCB SHA-256 before and after review:
`0ad0135cb9ff1f6ace7ef9d5ba9006b727b293d7b5224bb97dad47859b91238d`.
Native inventory: 209 footprints, 973 straight tracks, 295 vias.

**Current findings: 0 Critical / 0 Major / 1 carried Minor.** No new demonstrated
required-function failure was found. This lens awards no clean-round, owner,
firmware, manufacturing, physical or flight acceptance. The source and bench
conditions below remain essential to the calculations.

Reviewed the current native board and exported schematic pins against AGENTS,
REQUIREMENTS, the owner decisions and later amendments in R10_DECISIONS,
AVA_LAYOUT, M3_R10, R10_VALIDATION, R9 review severity precedents, the supervisor
packet and read-only VEHICLE context. No current-round peer report was read.
No CAD/source edit, canonical build/check/DRC, GUI, Git mutation or other-worktree
edit was performed. The companion JSON contains the numerical evidence and
independent calculation scripts; downloaded working files were temporary.

## R12-PWR-01: retained remote C98 ground return

**Minor; carried; open.** This is the power aspect of R11-RTE-02 / R11-m09,
explicitly retained by D-R11-04, not a newly demonstrated transient failure.

File: `m3_design/assembly_review/m3.kicad_pcb`. C98 is the 1 uF USB_LIMITED
bypass at B(24.575,62.2); its GND pad is (23.8,62.2). U11 is B(24.65,64.5),
input pin 7 at (24.3,63.825), GND pin 12 at (25.8,65.25), all millimetres.
Fresh native measurements give:

| Quantity | Current CAD result |
|---|---:|
| U11.7 to C98.1 direct distance | 1.934716 mm |
| U11.7 to C98.1 endpoint-linked B.Cu route | 2.059924 mm |
| C98.2 to U11.12 diagnostic saved-copper GND path | 31.812237 mm |

The last measurement uses a 0.05 mm B.Cu/In1 raster, a 12 mm expanded local
window and full 1.6 mm penalties per via transition. The path detours through
the upper island to the stitch near (30.15,52.0), then returns on In1 to the
U11 ground vicinity. It is a geometric diagnostic, not measured inductance or
a transient simulation. The short power connection alone does not make this
a short bypass loop. [TI TPS2121 SLVSEA3F p33, sections 11-12](https://www.ti.com/lit/ds/symlink/tps2121.pdf#page=33)
calls for close input bypassing and short, wide connections.

**Concrete fix:** re-place C98 with a local connection to U11's power ground,
or redraw the surrounding supply/return corridor to give C98 a nearby In1
stitch and a short return to U11. Rebuild/refill and verify native DRC, signal
references and the resulting loop before accepting that change. Retaining it
requires the recorded deviation and USB attach/source-transfer waveform tests.
No fully validated replacement placement is claimed by this read-only review.

## R12-PWR-02: previous electrical-number discrepancy closed

**Minor; closed; excluded from current totals.** R11-PWR-01's hard-coded
circuit-pass firing lengths have been replaced by native extraction. Independent
track-graph traversal, including the routed Q120 drain-pad entry and excluding
dead sense branches, reproduces the current budget. The current hot-plug and
local output-path records also bind the present PCB. Historical named-board
figures remain historical. No CAD change was needed to establish this closure.

## Independent electrical calculations

### Converter, endpoint and shared-fault limits

Native fitted feedback values reproduce the following conditional bounds:

| Quantity | Recomputed result |
|---|---:|
| PORT_5V3 buck | 5.366682-5.546269 V |
| PORT_4V8 LDO | 4.711504-4.873250 V |
| Camera input, 1 A | >=5.031682 V |
| Radio / GPS inputs, 0.30 / 0.15 A | >=4.601504 / 4.631504 V |
| Radio / GPS upper input, including transient allocation | <=4.923250 V |
| LDO headroom after buck negative transient allocation | >=0.443432 V |
| Camera current-limit range | 1.040891-1.249498 A |
| USB current-limit range | 0.347690-0.453049 A |

These retain the stated 50 mV transient and 0.15/0.20 ohm total loop allowances,
resistor initial/TCR corners and regulator-reference/leakage limits. They do
not establish those harness losses, transients or module peak currents.
The radio's 4.5-5 V range and 1 W maximum average demand are confirmed by its
[maker manual, Specifications](https://micoair.com/en/docs/telemetry/lr900/lr900-telemetry).
[HGLRC's specification](https://www.hglrc.com/products/hglrc-m100_mini-gps)
gives 3.3-5 V; [RunCam's manual p1](https://www.runcam.com/download/split4k/RC_Split_4k_Manual_EN.pdf)
gives 5-20 V and requires a regulated source.

At the allocated normal load, U400 draws 1.461 A output; L400's conservative
8.4 V / minimum-L / 470 kHz ripple estimate gives about 1.83 A peak. The added
SD allocation gives an inferred U2 output load about 0.564 A and about 0.822 A
peak using 3.33 V, minimum 4.7 uH and 1.034 MHz. These remain below converter
limits under the allocation. L400 is the fitted Bourns 6.8 uH, with 4 A Irms /
4.3 A Isat and 76.2 milliohm maximum DCR in the
[maker table p1](https://www.bourns.com/docs/product-datasheets/srp5030t.pdf).
L1's native 4.7 uH Sunlord part remains well below its heat/saturation entries
in the [maker SWPA4030S table](https://www.sunlordinc.com/uploads/files/20221122/SWPA%20series%20of%20SMD%20Power%20Inductor.pdf).
These are calculations, not an assembled thermal result.

The always-on LDO hard-short maximum is not its typical foldback figure.
A short on either GPS/radio port plus a 1 A camera prospectively demands
2.911 A, exceeding U400's 2 A continuous rating. The accepted response is
current limiting/hiccup and loss of port service, not continuous operation
there. The upstream threshold-only bound, 3.1 A plus core/SD and allowances,
is 3.743797 A versus U9's 3.96 A minimum. Comparator overshoot, rail dips and
logic survival are not established by that difference. Original limits:
[AP6320x DS41326 pp4-5,11,14-15](https://www.diodes.com/datasheet/download/AP63200-AP63201-AP63203-AP63205.pdf),
[TPS7A91 pp4-6,22](https://www.ti.com/lit/ds/symlink/tps7a91.pdf),
[TPS2553 SLVS841G pp5-7](https://www.ti.com/lit/ds/symlink/tps2553.pdf).

U401's 0.406177 W loss gives 102.494-114.679 C at 70 C ambient using the
retained inferred 80-110 C/W. This is not the JEDEC reference-board coefficient
or a measured value. Both exact GND 0.5/0.3 mm thermal vias at (27.3,13.6) /
(27.9,13.6) are present; VIPPO process qualification remains open. U400's loaded
dropout and switching/conduction losses have no worst-case guarantee from the
typical resistance curves. Four servo stalls can remove camera headroom even
while logic/recovery survives; no full-peripheral low-pack guarantee is claimed.

### Actual firing path and source sag

Independent graph traversal split tracks at real collinear junctions, retained
the routed terminal-pad entry and took one aligned source path without parallel
credit. The following are current-path lengths, not net-wide copper sums:

| Net | Length / width, mm | Native endpoints |
|---|---|---|
| BAT_IN | 6.307107 / 1.0 | J1.1 (7.4,74.1) to Q120 drain anchor (13.5,73.6) |
| ACT_FET_S | 2.200000 / 0.4 | Q120.2 to Q121.3, x13.175, y72.2-70.0 |
| RAW_ACT | 5.886133 / 0.5 | Q121.8 (14.475,67.105) to R134.2 (19.075,64) |
| PYRO1_IGN | 10.230382 / 0.5 | R134.1 (13.925,64) to J121.2 (7.4,57.6) |
| PYRO1_OUT | 7.854478 / 0.5 | J121.1 (7.4,54.1) to Q124.5 (13.9,57.37) |

No series firing via is needed. With 35 um copper, 1.72e-8 ohm m at 20 C and
0.00393/K TCR, the copper is 29.362412 / 35.132126 milliohm at 20/70 C.
Retaining the specified hot devices, R134, match/lead/contact/GND allowances,
the branch is 4.467458 ohm; with pack resistance it is 4.617458 ohm.

Solving `(1+Rpack/Rbranch)V^2-(Voc-Rpack*Iservo)V+Rpack*Pother=0`
at Voc 7.4 V, Rpack 0.15 ohm and Pother 12.370807 W gives:

| Persistent 1.92 A stalls | Fire current, A | Loaded BAT_IN, V |
|---:|---:|---:|
| 0 | 1.544366 | 6.899391 |
| 1 | 1.479438 | 6.609326 |
| 2 | 1.414264 | 6.318164 |
| 3 | 1.348805 | 6.025730 |
| 4 | 1.283013 | 5.731807 |

The last case is 0.158013 A above the selected 1.125 A criterion. It also gives
about 5.05 V minimum settled high-side gate drive using the retained drain and
resistor allowances. A deliberately pessimistic shorted-match load solve with
the same normal converter load remains above 5.5 V at four stalls; it does not
prove transient brownout immunity. The 7.4 V equivalent source is required at
deployment after pad/flight drain, not merely at launch. A neutral command does
not clear a jam. The <=0.6144 A board reference-return inference remains
conditional on the actual pack-star/harness resistances.

[MJG's sheet p1](https://electricmatch.com/upload/JTEK_TECHNICAL_INFORMATION_SHEET_SPECIFICATIONS.PDF)
defines the selected 0.75 A all-fire figure using a 0.5 s test. Its current
margin does not qualify this project's <=20 ms pulse. The selected lot, charge,
source reserve, harness and hot devices remain bench obligations.

### FET, resistor, copper and timing stress

Re-read and rendered the original [AONR21357 Rev2.1 pp1-5](https://www.aosmd.com/res/datasheets/AONR21357.pdf)
and [CRM2512 pp1-3](https://www.bourns.com/docs/product-datasheets/CRM.pdf).
The high-side part has -30 V drain and +/-25 V gate limits and a specified
12.3 milliohm maximum at -4.5 V / 25 C. The retained 40 milliohm hot ceiling
and actual-board linear SOA remain conditional. The shorted-load turn-on
load-line maximum is about 8.95 W at 4.2 V / 2.13 A, below the derated maker
reference-graph envelope; its heatsink/1-square-inch-board conditions do not
qualify the small native thermal land. Q124's fitted gate network is intact;
its [maker limits](https://www.aosmd.com/sites/default/files/res/datasheets/AON7524.pdf)
do not replace hot waveform/current-tail tests.

Ignoring all other resistance at 8.4 V and taking R134's adverse 70 C corner
gives 35.797452 W, 0.715949 J / 20 ms and 1.288708 J / 36 ms. The approximate
single-pulse graph comparison passes, with modest fault-pulse margin and no
repetitive-pulse permission. Independent hot-copper adiabatic estimates for
0.5 mm / 35 um are 7.076 K at 20 ms and 12.736 K at 36 ms; 28 um gives about
11.06/19.90 K. No spreading is credited. The seven retained 0.4 mm source
bridges share current; the single aligned resistance path is conservative for
voltage drop, not proof that every bridge carries all current thermally.

The 960-cycle watchdog range is 28.571-32.653 ms using the Rev V limits in
[ST DS12110 Rev11 Table136 p233](https://www.st.com/resource/en/datasheet/stm32h743vi.pdf#page=233);
adding the stated 0.2/0.5/1.5 ms
allocations gives 34.853 ms within the 36 ms guard. Normal physical current
must still finish within 20 ms including tail, with no watchdog refresh during
fire. Silicon revision, LSI bounds, reset/startup, actual gate current decay
and neutral response remain unimplemented/unmeasured.

### Switch bounce, physical breaks, USB and bypasses

The native EN network is still 470k + 470k, 300k and C87 2.2 uF X5R. A fresh
[Samsung typical bias curve](https://product.samsungsem.com/mlcc/CL10A225KO8NNN.do)
read gives about -14.62% near the nominal 1.790 V EN level. Applying explicit
0.9 initial, 0.85 temperature, 0.9 aging factors, +/-2% resistor bounds and
TI's adverse EN leakage/falling threshold estimates about 159.75 ms from
7.4 V. This conditional check passes 150 ms but gives little reason to treat
the inherited 0.21 s figure as measured. Typical bias/aging and the actual
loaded source must be qualified.

Independent C84 constant-power energy calculations to 3.8 V reproduce:

| Case | 300.8 uF | 470 uF |
|---|---:|---:|
| All ports and SD writing | 0.490197-0.571129 ms | 0.765932-0.892390 ms |
| Camera off, GPS/radio on, logic shed, SD idle | 1.532615-1.655039 ms | 2.394711-2.585999 ms |

These are endpoint-state estimates, not proven shedding transitions. Camera
turn-off can take 3 ms; a busy SD card can keep drawing current after clocks
stop. GPS/radio cannot be shed. U11 cannot be treated as an ideal diode during
a break: its [reverse detection threshold, p8](https://www.ti.com/lit/ds/symlink/tps2121.pdf#page=8)
is 0.2-2 A. The shortest full-load estimate is the appropriate retained
planning figure until actual load decay is measured. OQ-5 remains unchanged.

USB nominal charge behind U10 is about 2.416 mC to 4.7 V; its ideal no-load
charge time is about 5.33-6.95 ms at the calculated limit. Host-dependent
attach/programming, USB-to-pack transfers and disabled/enabled camera
back-feed remain bench tests. The current [TPS2553 datasheet pp6-7,13-14](https://www.ti.com/lit/ds/symlink/tps2553.pdf)
distinguishes slow reverse cutoff, off-state leakage and normal enable
turn-off; it gives no basis for instantaneous enabled-port isolation.
GPS/radio have direct power/UART paths. The no-self-powered-port/e-match
procedure and the independent PC1/PE4 controls remain necessary.

Fresh native C91 input bypass measurement is 4.092142 mm direct / 5.035660 mm
routed, with 6.273402 mm diagnostic ground return to U13. C92's corresponding
power/ground paths are 4.205635 / 2.531371 mm. These retained local-cell
compromises remain transient/stability qualification items under
[TPS709 p16](https://www.ti.com/lit/ds/symlink/tps709.pdf#page=16);
no instability is demonstrated. C92's typical-data effective-capacitance
estimate remains 2.211 uF versus the 1.5 uF effective requirement.

### U9 feed, output and hot-plug

Fresh native extraction, JSON-normalized, exactly equals the saved inputs;
digest `7528385758d3e4db4a0225cefd9a096d2322cd2c42bb6b6a6889402a0693f9db`.
C88 still separates U9 from every upstream modeled terminal. Its complete
3.92 mm local branch remains modeled. The actual 0.3 mm U9 entries and two
0.5/0.3 mm OUT vias at (20.3,79.1)/(21.1,79.1) were inspected, rather than
transferring the old four-via description. No full track/via DC/thermal solve
or absolute short-neck temperature qualification was performed.

The project's IPC-2152 curve-fit equations independently give 7.412/19.238 K
for a long 1 mm outer conductor at 1.8/2.9 A, and 4.594/8.502 K for a long
1.2 mm inner conductor at 1.461/2.02 A. Those long-conductor estimates do not
establish the temperature of the pad-limited short necks or the current planes.
The two-via barrel resistance alone is small (about 0.73 milliohm parallel at
20 C assuming 20 um plating), but current sharing/plating/board heating remain
unmeasured.

Re-measured saved-copper U9 protection loops without changing the target:

| Part | OUT / GND / total, mm |
|---|---:|
| C82 | 3.577817 / 9.426346 / 13.004163 |
| D9 | 6.585534 / 8.176346 / 14.761880 |

These fit the unchanged GAP-2 engineering bounds. They implement
[TI TPS25947 section8.4.1, pp62-63](https://www.ti.com/lit/ds/symlink/tps25947.pdf),
not a numerical inductance guarantee.

Fresh simulations executed by this lens: four selected nonlinear extrema at
full and half timesteps; 36 early local-path sensitivities; four selected
no-TVS controls; eight selected 0/0.01 ohm harness sensitivities; and two
selected damper-stress corners. **No full 2304-case rerun is claimed.**
The selected nominal-step extrema reproduce -14.807373236 V, 8.991477109 V/us
falling and 5.090699647 V/us rising; the refined rising maximum is
5.091052577 V/us. Maximum selected half-step changes are 0.0345 mV and
0.000725 V/us. The selected no-clamp minimum is -14.807406082 V. The selected
local and no-clamp controls pass; the lower-R
harness controls fail, as expected outside the qualified domain. The exact
unfused harness must measure >=0.03 ohm and 0.1-2 uH.

An independently written descriptor-system MNA integrator used the extracted
graph with nominal constant capacitors and no TVS for two controls, each at
full and half timestep. It agrees with the compiled charge solver to
<7e-9 V and <9e-9 V/us. This tests numerical implementation in a linear control;
it does not independently qualify the nonlinear component model or layout.

The retained common-node OUT estimate is 5.877715489 V after two seconds,
so [TI's cold limit p7](https://www.ti.com/lit/ds/symlink/tps25947.pdf#page=7)
still reduces to the -15 V floor. The selected no-clamp minimum has only 0.192594 V
margin. Ideal ground/pads, estimated inductance, typical capacitor curves,
family matching, package parasitics and unknown pin/contact behavior prevent
calling this a manufacturer worst-case physical bound. R166's approximately
579.05 W / 2.97936 mJ extrema are in different corners; no microsecond pulse
rating or durability guarantee is inferred from a continuous rating.

## Executed checks and limits

- Native read-only API: current part identities, power/control topology,
  thermal-via geometry, 144 selected native-to-exported-schematic pad/net
  comparisons, independent firing-track graph, protection and bypass paths.
- Independent arithmetic: rail/endpoint tolerances, shared-short coordination,
  converter/inductor allocations, coupled source sag, shorted-match sensitivity,
  hot pulse energy, IPC-fit/adiabatic copper, SD states, hold-up and switch bounce.
- Original maker PDFs/web pages: regulator limits and layout, P-FET SOA and
  reference conditions, Q124, R134 pulse graph, e-match definition and endpoint
  supply specifications. SOA and pulse pages were rendered and visually read.
- Native hot-plug re-extraction plus the explicitly enumerated simulations and
  independent linear numerical controls above. Source and board bytes were not
  changed; before/after PCB hashes match.

No firmware, actual e-match lot/charge, source reserve, installed harness,
converter stability, electrical/thermal waveform, cold C84 ESR, switch bounce,
physical-break recovery, SD busy/power-loss handling, watchdog/current tail,
R166 endurance, USB host compliance, RF/ESD immunity or assembly process was
physically tested. Correctly disclosed pending qualifications are not counted
as new demonstrated hardware failures. AGENTS section2 and all owner decisions
remain unchanged.
