# Round 12 requirements and owner-decision review

Target: commit `d57b216c365fc8d18896bceba37f63caf20d52a4`, PCB `0ad0135cb9ff1f6ace7ef9d5ba9006b727b293d7b5224bb97dad47859b91238d`. SHA-256 matched before and after this read-only review. Independent lens 1; no other round 12 reports read. Only the two assigned reports are written outside scratch.

**Open findings: 0 Critical / 0 Major / 3 Minor (1 new, 2 carried).** No demonstrated required-function or AGENTS §2 failure found within this lens. This is no clean-round, acceptance, fabrication or flight-release claim. R9 severity precedents distinguish demonstrated failures from explicitly pending qualification; the R9 record has no literal standalone severity rubric.

## Findings

### R12-REQ-01 — Minor, new: Active requirements snapshot still names the pre-fix PCB and says it was never reviewed

Contradictory acceptance-entry evidence can bind a subsequent review to the wrong board or resurrect stale unreviewed/fix status. Native CAD and the opening current validation record are consistent.

- `docs/REQUIREMENTS.md:156-165`: Current board names 0c50b9fd, 981 segments/294 vias, 23-file equality and says no review round has run. Round 11 did review 0c50b9fd; the exact current PCB is 0ad0135c with 973/295, and current build records state 42-file equality.

- `docs/M3_R10.md / Placement`: The row correction still requires a fresh supervised build and describes old hand-off measurements as pending, after this file already records two completed direct builds.

- `m3_design/assembly_review/sources/r10_design/r10_plan.md:5-13`: Opening AVA review baseline still says generator fixes/new build evidence are pending.

Fix: Replace or explicitly archive the stale active snapshot; name d57b216/0ad0135c, 973 segments/295 vias and the 42-file fix-build record. State round 11 reviewed 0c50b9fd and earned no clean credit; current full rounds start at 12. Retain outstanding process/stock/acceptance conditions.

### R12-REQ-02 — Minor, carried: Vehicle integration mirror still describes removed GH/ARM/header hardware

A sled/harness designer using the vehicle reference can design obsolete mating clearances and switch routing. This is not a proved collision in the current board; OQ-7 placement is still correctly stated there.

- `../../docs/VEHICLE.md:39`: R10 stack entry still says GPS/radio on GH-4, battery and ARM/IGN at x0, GH-2 J400(10.5,85.5), and 0.03 mm mated-GH margin.

- `m3_design/assembly_review/sources/r10_design/R10_DECISIONS.md / D-R11-04`: Explicitly recognizes this stale parent mirror and requires a separately owned handoff.

Fix: Keep an explicit parent-repository handoff for its owner: seven DB125s, west x7.4/east x38.6 rows and current y positions; J400 sole power/arming switch, no J124/link/fuse/pull-pin or servo tie holes; direct always-on GPS/radio, retained camera isolation; bottom hinged SD with removal/access-window requirement; current calculated terminal room5.003 mm and physical fit unverified. Do not edit the separately owned mirror in this review.

### R12-REQ-03 — Minor, carried: M2 drawing and noncritical routing residuals remain for the current-board deviation inventory

These are deliberately nonblocking AUD-10/audit2 review items and bounded M2 cleanliness departures, not connectivity, clearance or fast-return failures. They have not become owner-accepted merely because the gate passes.

- `m3_design/assembly_review/m3.kicad_pcb`: Fresh route_check profile r10: 139 total informational instances, zero blocking failures/allowlist entries/stale entries; 22 inside-pad segments and nine unrecorded noncritical leftovers. Exact categories/locations are in this JSON.

- `native PCB (16.4, 83.0) B.Cu BAT_OVLO`: short_segment

- `native PCB (9.97, 51.5) B.Cu I2C1_SDA`: tiny_jog

- `native PCB (14.825, 27.2) net USB_ILIM`: detour

Fix: Use the current exact instance list below in the final 0ad0135c deviation inventory, replacing the 0c50/b337 lists. Simplify noncritical polylines when a fully checked generator change is warranted; otherwise retain their named/count/location disposition as allowed by audit2. Preserve blocking electrical rules.

The nine noncritical leftovers are intentionally count/location-only under audit2; they do not require per-instance measured paperwork or become blocking because their coordinates changed:

| Category | Net | Layer | x,y mm |
|---|---|---|---|
|short_segment|BAT_OVLO|B.Cu|16.4,83.0|
|tiny_jog|V3V3_SENSE|B.Cu|26.25,52.5|
|tiny_jog|BAT_FAULT_N|B.Cu|26.0,47.3|
|tiny_jog|BUZZ_DRV|F.Cu|20.5,51.8|
|tiny_jog|BAT_FAULT_N|B.Cu|28.2,47.5|
|tiny_jog|I2C1_SDA|B.Cu|9.97,51.5|
|tiny_jog|BAT_ENABLE|F.Cu|19.675,66.0|
|tiny_jog|BAT_ENABLE|B.Cu|21.0,68.6|
|detour|USB_ILIM|net|14.825,27.2|

All 139 current routing information instances,22 inside-pad segments,91 hidden references and exact native measurements are embedded in `round12_requirements.json`; no historical82-instance/b337 or12-leftover/0c50 list is substituted.

## Executed evidence and limits

| Evidence | Actually executed/result |
|---|---|
|E-N|Read-only custom pcbnew/XML/TSV/binding/population probes; no saved CAD mutation. |
|E-F|KiCad Python10.0.6: fit_check --profile r10; check_r10 --only selected 25 rules with current BOM/CPL. |
|E-R|Fresh route_check.py --profile r10; read current explicit routing-family source for router references. |
|E-H|Fresh native r10_hotplug --extract to scratch; NumPy run_nonlinear on four current extreme cases at half step; validate stored 2304/refinement/sensitivity evidence against fresh extraction and model. Uses project solver/model; not an independent physical model or new 2304-case sweep. All results Simulation/Inference.|
|E-B|r10_parts.py --check on exact board; custom independent resistor/cold-network/coupled-source/watchdog/wire-room algebra. Current native path extraction uses project model; material/FET/source/harness/capacitance assumptions remain unmeasured.|
|E-M|fab_manifest.py read-only verification plus independent schematic exclusion/BOM/CPL set equality and recorded supplier arithmetic/input hash checks. Did not regenerate package, repeat supplier-pad orientation/paste analysis or fetch a new supplier quote.|
|E-O|Read current ORDERING8, generated binding obligations, REQUIREMENTS/AGENTS, FMEA references, r10_plan/107decisions, AVA/M3/R10 records, parent VEHICLE and R1 firmware binding guard. No R10 firmware or physical test performed.|
|E-P|Read-only historical review/process/build provenance reconciliation. No canonical build/full check.sh, native CLI DRC/ERC/parity, GUI, git command, source/CAD edit or other-worktree edit.|

Native comparison:209 PCB/XML components,651 XML pin mappings and all 100 MCU pins agree; all four binding hashes match. The 10 excluded items are bare programming/probe contacts, leaving 199 functional fitted parts exactly equal to BOM/CPL. All deleted ARM/pull-pin/duplicate-sense/port-switch/translator parts checked are absent; no absolute model references found. Fresh fit and selected 25 contract rules pass, as does the five-output manifest. The fresh routing scan has zero blocking/allowlist/stale findings and 139 information instances.

Fresh model extraction has 11 edges and equals the saved current input. All 2304 saved cases/refinements/local sensitivities validate against it. Four newly solved half-step extreme cases have no violation: minimum−14.807372 V, maximum falling8.990753 V/us and rising5.091053 V/us among those four. This uses the project nonlinear model and is Simulation/Inference, not a fresh entire2304 sweep or a physical guarantee. Retained-OUT, local parasitics, actual harness and damper durability remain explicit limits.

Independent algebra reproduces the single-resistor-fault ADC maximum 3.342171 V at 19.9 V and one-top-short1.397310 mA at 8.4 V; passive healthy CONT/BUS99.368924/99.337881 mV and open CONT146.226415 mV; conditional fire 1.544366 A idle and 1.479438/1.414264/1.348805/1.283013 A with 1..4persistent stalls;960-cycle watchdog28.571429..32.653061 ms and nominal floating gate3.3->0.4 V discharge0.504796 ms. These equations verify the records, not actual ADC discrimination, source reserve, pulse tail or firing reliability.

The selected rules are `S-1,S-2,S-3,S-4,S-5,S-6,S-7,S-8,S-9,K-contract,K-loader,LC-1,M-1,M-3,M-5,M-6,M-7,P-11,F9-2,T-1,K-legends,K-copper,K-inner,K-width,K-retained`. Full native DRC/ERC/parity, reference/fill self-tests, a canonical rebuild and complete check.sh were **not** run by this lens. Root build receipts are historical provenance only. No GUI was launched or rejection bypassed; no git command or other-worktree write occurred.

## Functional, mechanical and manufacturing trace

| Requirement | Native/current evidence and disposition | Remaining qualification |
|---|---|---|
|F1|U4 is LSM6DSV320X; native B180 at(17,45.9), pad1 offset(+1.21,-0.75), roll=-gyro_Y. ST primary product confirms gyro +/-4000dps. **CAD capability/pose verified; accuracy and flight envelope open.** (E-N/E-F/S-IMU)|Measure bias/temperature/vibration/high-g effects and qualify <=5deg over <=30s against updated K850DM/L1000W model.|
|F2|Same U4 retains separate low-g/high-g accelerometers; primary maker range includes +/-64 g and higher. **Part capability verified; trajectory/clipping qualification open.** (E-N/S-IMU)|Establish current vehicle mass/acceleration and anti-alias/filter/range settings; old I500T estimates do not qualify either flight.|
|F3|U5 MS561101BA03 on 3V3 A/I2C1; maker pp1/4 gives 10..1200mbar extended range, sufficient for >=10km pressure range (altitude inference). U5/nearby masks and dark LEDs remain procedural obligations. **Part/topology verified; installed pressure behavior open.** (E-N/E-O/S-BARO)|Vent/foam recovery, transonic estimator use, light/LED rejection, temperature and actual installed altitude accuracy.|
|F4|J122 has exactly SERVO1..4_OUT plus GND; each output has 1k resistor,10k MCU-side pull-down and SRV05-4. No servo positive/motor-return copper. **CAD verified;333 Hz/servo/harness behavior open.** (E-N/E-F/E-B)|Qualify motor/reference star, >=50 mohm branches/<=1 mohm transfer and <=0.6144 A inferred board share with 1 A allowance; physical neutral and hinge loads.|
|F5|U3 W25Q128JV retained; J430 Molex472192001 with five10k pulls and 100 nF/22 uF bypass, SPI3 PC10/PC11/PC12+PD0. Exact socket/MCU nets checked. **CAD paths verified; logging implementation open.** (E-N/E-F/E-O)|>=800 Hz sampling,500 Hz/high-rate and<=50 Hz descent logs, total-flight coverage, >=25% throughput margin, busy/erase buffering, reset/power-loss behavior and selected-card<=200 mA/30 mA current. No blocking safety flush.|
|F6|R80/R165 470 kOhm, R81 300 kOhm, C87 2.2 uF retained; U10/U11, C84 470 uF and PA6 sense retained. Independent timing algebra gives 28.571..32.653 ms IWDG and nominal gate discharge0.504796 ms. **Topology/calculations verified; failsafe timing unqualified.** (E-N/E-B/E-O)|>=150 ms switch bounce, actual break hold-up, PA6 latency/camera current decay, sensor/flight-state survival, first neutral<=50 ms, no refresh during current and valid refresh<=5 ms after. GPS/radio/card stay powered.|
|F7|BAT_IN->Q120/Q121->RAW_ACT->R134 2 ohm->J121.2; J121.1->Q124->GND. Independent coupled-load solve gives 1.544366 A idle to 1.283013 A at four stalls, above selected 1.125 A floor. **Native topology/conditional current budget verified; physical firing open.** (E-N/E-F/E-B/S-MATCH)|Measure source/harness/hot copper/FETs, retain7.4 V equivalent at fire after pad drain, prove20 ms selected-lot/charge firing and shorted-load logic survival; no claim from maker0.5s current data alone.|
|F8|One J400, no J124/pull-pin; independent PC1/PE4 controls have required bias/series/capacitor networks. Two direct10.2k/1k/10 nF banks. Independent one-fault max3.342171 V at 19.9 V; native colored terminal roles/labels agree. **CAD and stated resistor-fault calculation verified; operating safety implementation open.** (E-N/E-F/E-B/E-O/S-MCU)|Both-low passive screen before enable, >=1s verified discharge, >=100 ms settling; qualified threshold/leakage bands; launch detection, ground refusals/in-flight never-veto; no e-match with back-feed source. Double-fault damage remains accepted.|
|F9|U9 TPS259470L/U10/U11 and actual C88-first feed retained; exact0.36ohmR166 / 3.3 kOhm R92. Fresh 11-edge model extraction matches and four fresh refined extreme cases pass. Direct always-on UART/supply architecture matches owner amendment. **CAD/model binding verified; transient/harness/power qualification open.** (E-N/E-H/E-B/E-O)|Measured unfused harness>=0.03 ohm/0.1..2uH; simultaneous U9IN/OUT/cold slew;R166 endurance; dry-contact vibration; delivered port rails, short/back-feed and logic survival. No downstream protection claim for unfused BAT stretch.|
|F10|No U30/U31/J30/J31/RF; direct GPS/radio1k+ground ESD and camera U12/U13/U402 retained. Native UART/EXTI/SD map matches table/binding. Maker radio manual confirms3.3 V interface/4.5..5 V supply and configured-band limitation. **Interface architecture/map verified; installed RF and firmware open.** (E-N/E-F/E-O/S-RADIO/S-MCU)|Endpoint voltages/edges/ESD/back-feed, full-power installed immunity, legal manual12..25 or maker-confirmed hop set, shared EXTI demux, trace-off/PC1+PE4 locks/readback, no uplink arm/fire.|
|P1|Four Edge.Cuts lines form46x90 mm; five3.2 mm circles at required supports; no servo tie holes. Board is single PCB; no SMA overhang. **Native outline/supports verified; integration mirror stale.** (E-N/E-F)|Parent vehicle candidate update R12-REQ-02; exact full stack and external module/harness fit physical.|
|P2|Fresh max-envelope fit passes radius24.9 mm/axis23/tolerance0.3; all seven row faces give 5.003011866 mm bare-bore room. Nearest bottom C32.2=4.536177 mm; top LED2.2=3.807887 mm. **CAD envelopes verified; physical fit open.** (E-N/E-F/E-B/E-O/S-TERMINAL)|Actual wire/ferrule bends, screwdriver/staking room, hardware/sled eccentricity and both tolerances, closed-card fit/lid access, aft edge plus axial tolerance wholly forward joint+47. No plate-frequency release floor.|
|P3|Selected M-7 sees no prohibited sensor-side fill/via under MEMS; current ORDERING preserves U4/U5 exclusions, sole TP122 exception and all-seven-terminal staking. **CAD exclusion/procedure verified; strength/coating qualification open.** (E-F/E-O)|5x100 g retention, actual shock/vibration, no-clean/two-reflow U5, foam, masking/cure, post-coat NRST>=0.90x3V3 with 10Mohm meter/leakage>=250k, clamps/hinge and installed fit.|
|M1|Four-layer native project and 82-code/199-part package; all 209 identities and 651 XML pin mappings agree.199 functional fitted parts equal BOM/CPL. Two U401.11 vias have exact0.5/0.3 geometry; C84 kept fitted. **CAD/population/package binding verified; stock and process open.** (E-N/E-M/E-F/E-O)|Order 1.6 mm / 1 oz ENIG Standard two-side/required inner stack; JLC acceptance of VIPPO/manualC84/no-clean/two U5 reflows/THT process/panel; preview, supplier/part/land exceptions and stock/consignment. No first article exists.|
|M2|Selected local-clearance, copper, width, silk, inner-net and fitted-population rules pass; fresh route scan has 0 failures/allowlist entries and 139 information instances. **Selected CAD policies verified; full DRC not rerun in this lens.** (E-F/E-R/E-O)|R12-REQ-03 current-board information inventory; full native DRC/check.sh/reproducibility belongs to root. Physical mask, solderability, fill/cap quality and workmanship unverified.|
|M3|Recorded final-CPL supplier snapshot05:00Z gives$54.44 parts+$25.092 feeder=$79.53/board; min-purchase parts$56.78+$25.092=$81.87, against$84.41.82codes/46Extended informative. **Recorded snapshot arithmetic/binding checked; no fresh supplier fetch by this lens.** (E-M/E-O)|U4 zero/consign,R430 17<3610minimum,U9 minimum 7 vs 5; actual quote/fixed/process/PCB/shipping/consignment costs, owner full-deviation acceptance and<=24h stock/cost before order.|

## Owner mandates and supersession

Owner choices govern; the exact setpoints, MCU allocation, footprint implementation, path bounds, model assumptions and process defaults chosen by agents remain reviewable choices. AVA photographs provide layout inspiration only; no hidden AVA circuit/copper/firmware is inferred. The K850DM/Mach1.45 and L1000W/Mach1.9 vehicle envelope,2S source, one recovery output and isolated Blue Jay remain the basis. Updated trajectory, mass and physical assembly remain open.

| Owner item | Authority | Current disposition | Evidence |
|---|---|---|---|
|Initial plan items1-4|Owner mandate|Ordinary0.15 mm clearance retained with S-8; black3.5 mm IGN and separate battery/switch terminals; C84470 uF/25 V. J124/keyed switch and original fuse wording superseded.|E-N/E-F/E-O|
|O1|Owner mandate, amended|External HGLRC GPS retained; final DB125/4V8 direct supply+1kUART replaces original GH/switched3V3;L5 loss accepted.|E-N/E-B|
|O2|Owner mandate, amended|External LR900-F, no on-board RF; final DB125/direct4V8 and UART5; uplink arm/fire prohibition and installed immunity remain.|E-N/E-O|
|O3|Owner mandate|Servo motor power/return off board, protected signals retained; Q120/Q121 serve pyro only; loss of servo power cutoff explicitly retained.|E-N/E-F|
|O4|Owner mandate|Regulated camera5 V-class supply; U402/U12/U13 retained. Actual5.456 V setpoint is an agent-selected tolerance solution, not a new owner voltage mandate.|E-N/E-B|
|O5|Owner mandate, amended|Separate buck/LDO voltage architecture retained; later owner cut removes GPS/radio switches/translators while camera isolation/switch survives.|E-N/E-B|
|O6|Owner mandate|Pack-star motor pairs and bounded reference return retained;0.6144 A is an unmeasured harness inference, qualified with 1 A allowance.|E-N/E-B/E-O|
|D-R2-04 then D-R2-08|Owner mandate|All current signals hand-routed; old permission for noncritical autorouting superseded.|E-R|
|OQ-1|Owner mandate|4.95 mm floor accepted; current maximum terminal unions give 5.003012 mm. Physical16-22AWG fit stays open.|E-F/E-B|
|OQ-2|Owner mandate|Actual-feed distributed model implemented with C88 intercept; new native extraction matches and four refined extrema rerun. Full2304 stored evidence validated, not rerun wholesale here.|E-H|
|OQ-3|Owner item, pending|Current recorded price meets cap; no acceptance of quote or complete deviation list inferred. Historical cost misses do not change the cap.|E-M/E-O|
|OQ-4|Owner mandate|Aft-edge tab/rail selected; panel acceptance before ordering remains open even though current tab windows permit other locations.|E-F/E-O|
|OQ-5|Owner mandate, amended|Keep C84/firmware shedding, no hardware cutoff. Always-on GPS/radio/card mean no claim that software can shed them.|E-N/E-B/E-O|
|OQ-6|Owner mandate, revised|No battery-lead fuse; unfused lead/copper/TVS/cap risk retained. Later single-switch decision also removes ARM-link fuse.|E-N/E-O|
|OQ-7|Owner mandate|Board plus axial mounting tolerance wholly forward of joint+47 mm, all roll orientations; freed length remains slack.|E-O|
|Single switch and keep-one-switch reaffirmation|Owner mandate|J400 powers/arms, no J124; two separately driven series firing controls, on-rail/on-last/off-first, launch/ground/in-flight policy retained. AVA photo correction does not restore ARM terminal.|E-N/E-O|
|AUD-1..10 and GAP-1..5|Owner direction; implementation choices remain agent choices|Adopted narrow reductions and real gaps traced individually in107-index. Later always-on/terminal/audit2 decisions supersede old port/header clauses. No AGENTS §2 rule relaxed.|E-N/E-F/E-B/E-O|
|AVA comparison10 layout items|Owner layout direction|Rows/local cells/battery/buzzer/sense/probes implemented, with actual camera/SD/THT constraints. Exact translated cells/old coordinates are not frozen requirements.|E-N/E-F/E-R|
|Always-on ports plus microSD|Owner mandate|Direct GPS/radio supply/UART; camera switch/isolation; hinged SD alongside primary QSPI, no card-detect promise; current startup/latency/lid obligations explicit.|E-N/E-F/E-O|
|All wired screw terminals / Steer1|Owner mandate|All seven DB125s correct; USB-C and hinged card remain separate. Legacy circuit-only stop superseded by current full review assignment.|E-N/E-F|
|Requirements audit2 items1-13,15|Owner mandate|Direct two-bank ADCs/removals, limited thin taps, In1GND routing allowance, optional plate, count-only leftovers, NRST metric, no Extended cap, single reviewed map, local floors and always-on obligations retained.|E-N/E-F/E-R/E-O|
|Requirements audit2 item14/16|Owner mandate, conditional|check.sh zero before each commit retained; STATUS is current. Hash provenance refreshed, electrical/axes review when changed. LEDs stay dark until actual opaque-cover test passes; no test is claimed.|E-N/E-O/E-P|

AGENTS §2 is preserved: sole power/pad switch on last/off first on-rail; pyro feed behind load switch; ground bus/continuity refusals and in-flight never-veto; gate pull-down/series/cap and reset-off; inferences identified. Two GPIOs share one MCU and do not establish independent software safety. Back-feed restrictions and absence of physical powered ARM break are owner-adopted limitations, not newly invented failure criteria.

## 107-decision disposition index

Exactly 107 unique `D-*` headings were parsed and read from `R10_DECISIONS.md`, including suffixes and newest D-R11-01 addenda. Every heading appears once below. `O` means an explicit owner mandate in its heading; `A` means agent implementation/process choice, even when implementing a separate owner mandate. Historical/superseded coordinates and test claims are not transferred to the current board. Full exact titles/line numbers are in JSON.

| Decision | Authority | Disposition | Current trace |
|---|---|---|---|
|D-R1-01|A|historical|Plan-first/R9 baseline rule satisfied historically; current target is separately bound, not relabelled R9. (E-N/E-P)|
|D-R1-02|A|superseded|O5 and the later always-on amendment replace the infeasible 3V3 GPS proposal; J410.1 is PORT_4V8. (E-N/E-B)|
|D-R1-03|A|current|Separate camera buck and GPS/radio LDO remain; endpoint corners are conditional harness budgets. (E-N/E-B)|
|D-R1-04|A|historical|Past review concurrency limitation; no ten-at-once claim is transferred to this lens. (E-P)|
|D-R1-05|A|superseded|Old headless interposer/default-NumPy workaround is replaced for current DRC by D-R11-05; no CLI DRC run here. (E-P)|
|D-R1-06|A|historical|Plan review stop and seven Majors are history; no R9 gate result qualifies this board. (E-P)|
|D-R1-07|A|mixed|O5/O6 implementation retained as amended: external servo power/return, 1 A board-return allowance; GPS/radio isolation/switches later removed. (E-N/E-B/E-O)|
|D-R2-01|A|superseded|Core at U1(23,43) remains; early terminal/header layout is replaced by AVA and R11. (E-N/E-F)|
|D-R2-02|A|mixed|Explicit pyro/USB/SWD routing remains; J124-era fire path and old return-via coordinates are superseded. (E-N/E-R)|
|D-R2-03|A|mixed|U400/U401/camera regulator architecture remains; early switch cells and region coordinates do not. (E-N/E-B)|
|D-R2-04|O|superseded|Owner critical-hand-routing mandate strengthened by D-R2-08 to every signal; autorouting permission no longer applies. (E-R/E-P)|
|D-R2-05|A|superseded|U9 and rail geometry were subsequently moved/re-cut; native current feed and four rails supersede early coordinates. (E-N/E-H)|
|D-R2-06|A|mixed|Radio PB12/PB13 UART5 survives; old translator/fan-out and IO-plane descriptions are superseded. (E-N)|
|D-R2-07|A|mixed|Surviving camera/buzzer GPIO choices remain; deleted port controls/pull-pin and router table are superseded. (E-N/E-R)|
|D-R2-08|O|current|Owner requires hand routing on every signal; current routing modules use deliberate polylines, with no AUTO/ncroute/freerouting production reference. (E-R)|
|D-R2-09|A|mixed|PA4 source, PA5 fault, PA6 sense and PC14 buzzer survive; removed sense tails and placement coordinates do not. (E-N/E-O)|
|D-R2-10|A|mixed|Unused inner-via pads/reference policy survives; regions and stray geometry are current-generator choices, with AUD-2's narrow exclusions. (E-N/E-R/E-O)|
|D-R2-11|A|mixed|TP122 bottom and retained camera/flash bypass contracts survive; historical pad/via fixes are checked at current poses. (E-N/E-F)|
|D-R2-12|A|mixed|Five supports survive exactly; header/tie-channel requirements are explicitly removed by the terminal amendment. (E-N/E-F)|
|D-R2-13|A|current|Panel support concept retained and OQ-4 selected aft tab/rail; JLC acceptance remains pending. (E-F/E-O)|
|D-R2-14|A|superseded|OQ-1 accepts 4.95 mm; OQ-2 demands actual-feed simulation. Neither old R8 distance floor remains an active requirement. (E-F/E-H)|
|D-R2-15|A|current|Build/fab generator chain retained; this lens verifies current package binding, not another canonical rebuild. (E-M/E-P)|
|D-R2-16|A|superseded|Legacy ARM/PULL/header legends removed; current individual terminal and J2 legends pass selected K-legends. (E-N/E-F)|
|D-R3-01|A|superseded|R410 and independent GPS current limit were deleted; current shared-LDO fault budget supersedes 2.022 A old switch budget. (E-N/E-B)|
|D-R3-02|A|mixed|S-8 1.0 mm barrel exclusion/GND neighborhood retained; current four barrels pass. Old J124 window and 1.458 mm minima are history. (E-F)|
|D-R3-03|A|mixed|Continuous BAT/U9 width floors survive; current local ladder/output geometry replaces old four-via figures; thermal qualification remains open. (E-N/E-F/E-O)|
|D-R3-04|A|superseded|Old port-control In2 edges are replaced by AUD-2/AVA; removed RADIO_4V8 switching net is absent. (E-N/E-O)|
|D-R3-05|A|current|U400 input bypass cell remains; selected retained-copper checks pass, transient behavior remains unmeasured. (E-N/E-F/E-O)|
|D-R3-06|A|current|Local Y1 In2 GND/reference intent remains; no PCB change made in this review. (E-N/E-O)|
|D-R3-07|A|mixed|Camera supply/return constraints remain; ACT slow-return exemption supersedes its partner rule and all five terminal GNDs now use thermals. (E-N/E-F)|
|D-R3-08|A|mixed|Stitching intent retained, but AVA/R11 local stitch geometry supersedes the original 37-coordinate count. (E-N/E-R)|
|D-R3-09|A|mixed|Fast UART return/one-transition intent survives; removed pull-pin/port-control geometry does not. (E-N/E-R)|
|D-R3-10|A|mixed|Arc, loader, barrel, width and assembly checks survive with narrow later amendments; plate is optional and old literal coordinates are retired. (E-F/E-R)|
|D-R3-11|A|mixed|Mask/text/mark requirements retained; obsolete ARM/fuse/header words are absent. Current legends pass, with 91 hidden references. (E-F)|
|D-R3-12|A|current|R162 remains 1k on PC14 buzzer drive; no LSE operation is authorized. (E-N/E-O)|
|D-R3-13|A|mixed|Old ride-through/port-switch/EXTI figures are historical; current always-on and card budgets/binding apply. (E-B/E-O)|
|D-R4-01|A|superseded|Slow sense-plane arms are removed by AUD-2 and AVA; this is an explicit owner scope change, not a fast-return waiver. (E-N/E-O)|
|D-R4-02|A|mixed|Centered-entry intent remains; moved terminals/routes supersede exact early pad entries. Residual M2 information is counted afresh. (E-R)|
|D-R4-03|A|mixed|Strengthened rules remain as amended by audit2; local overrides/assembly/mapping pass selected checks. Full DRC/reference/fill not rerun here. (E-F/E-R/E-P)|
|D-R4-04|A|mixed|R10-specific ordering/firmware/fit records remain necessary; historical quantities and connector coordinates are superseded. (E-O)|
|D-R5-01|A|superseded|Old chain/plane contours replaced by AUD-2/AVA; retained fast-reference intent is not relaxed. (E-N/E-O)|
|D-R5-02|A|mixed|Legal text/pad-entry intent remains; current moved cells supersede early coordinates and hidden-reference count. (E-F/E-R)|
|D-R5-03|A|mixed|Hardened value/gate/reference logic remains; audit2 direct ADCs and named slow exclusions supersede obsolete tails/scope. (E-F/E-O)|
|D-R5-04|A|mixed|Via-covering, load/thermal, hardware and NC-pin obligations survive; current ORDERING replaces historical counts. (E-O)|
|D-R6-01|A|superseded|Sense-return In2 arms expressly removed by AUD-2; no requirement to restore their old dimensions. (E-N/E-O)|
|D-R6-02|A|mixed|Functional and geometry hardening survives; old GH mated envelopes and obsolete raw/ARM topology do not. (E-F)|
|D-R6-03|A|mixed|Forward-of-joint+47, hardware, axes and bench duties survive; removed probes/pull-pin and old geometry are historical. (E-N/E-F/E-O)|
|D-R7-01|A|mixed|Parsing/membership/seeds remain as amended; three-divider and MCU-tail membership is superseded by audit2. (E-F/E-O)|
|D-R7-02|A|mixed|Source reserve, lock/readback, watchdog/erase and hardware obligations retained; new ematch/current loads replace old 1.5 A fire threshold. (E-B/E-O)|
|D-R8-01|A|mixed|Old local cleanups are not immutable routing; present noncritical return/pad compromises are re-inventoried. (E-R)|
|D-R8-02|A|mixed|Full-gate/fab binding and required legends remain; old J124/fuse/14-ref list superseded by all-part population and current terminal legends. (E-F/E-M/E-P)|
|D-R8-03|A|mixed|No-clean/coat/standoff/HSE obligations retained; current contacts, sense banks and budgets replace old GH/header facts. (E-O)|
|D-OA-01|A|mixed|OQ-1/4/6/7 survive; its retained ARM link/fuse was removed by the subsequent single-switch owner decision. (E-N/E-F/E-O)|
|D-OA-02|A|mixed|No hardware cutoff and conservative LDO thermal inference retained; GPS/radio shedding superseded by always-on ports. (E-B/E-O)|
|D-OA-03|A|current|Router experiments remain historical design aids; production signal tables are explicit hand routes. (E-R)|
|D-OA-04|A|historical|Failure of old split feed justified remediation; current C88-intercept topology is separately extracted and checked. (E-H)|
|D-OA-05|A|mixed|R92 3.3k retained; capacitor inventory/retained-OUT estimate is regenerated for current population, not old literal inventory. (E-N/E-H)|
|D-OA-06|A|current|R166 0.36 ohm and actual-feed/harness-domain contract retained; repeated pulse durability remains open. (E-N/E-H/E-O)|
|D-OA-07|A|current|C88 separates U9 from all other modeled terminals; local branches are retained. Fresh extraction equals current saved model. (E-H)|
|D-OA-08|A|mixed|Canonical part fields and rejection of obsolete fuse legends retained; old GPS translator statement is historical. (E-N/E-F)|
|D-OA-09|A|historical|Interrupted preparation/commit limitation is past process history; no clean or rebuild credit transferred. (E-P)|
|D-SS-01|A|current|PC1 through R122/Q122 and separate PE4/R126/Q124 match native circuit; external bias and two GPIO locks remain required. (E-N/E-F/E-O)|
|D-SS-02|A|mixed|Canonical post-switch RAW_ACT, no J124/net tie retained; duplicate sense chain and early R134 placement were later superseded. (E-N/E-B)|
|D-SS-03|A|current|Required safety references visible; current legends pass. Old mass totals and coordinates do not qualify current mechanics. (E-F/E-O)|
|D-AUD-01|A|current|C92 is 4.7 uF/16 V C19666; effective-capacitance inference and physical stability duty remain. (E-N/E-B/E-O)|
|D-AUD-02|A|current|Only explicitly named slow nets lose numeric return geometry; fast rules, S-8 and critical hygiene remain required. (E-R/E-O)|
|D-AUD-03|A|current|Genuine AONR21357 pair retained on maker land, current poses; 100 ms settling and hot/SOA tests remain obligations. (E-N/E-O)|
|D-AUD-04|A|current|Complete pull-pin deletion and PC13 NC confirmed; accelerometer+barometer launch rule remains. (E-N/E-O)|
|D-AUD-05|A|current|Six probe deletions confirmed; retained hot-plug and pyro probe map is current in ORDERING. (E-N/E-O)|
|D-AUD-06|A|current|Fire-only 0.5 mm with bounded pulse retained; continuous BAT feed unchanged in width. Pulse/thermal inference is not qualification. (E-F/E-B)|
|D-AUD-07|A|mixed|Servo 1k/100mW 0603 and camera 0402 pull-up survive; GPS/radio fault pull-ups are deleted with their switches. (E-N/E-O)|
|D-AUD-08|A|superseded|All GPS/radio translators and their bypass/IO cells later deleted; camera U12/U13 still present. (E-N)|
|D-AUD-09|A|current|U10/U11 retained for USB-only bench operation; host/inrush qualification remains explicitly pending. (E-N/E-O)|
|D-AUD-10|A|current|Only exact drawing artifacts/legend distance are nonblocking; current 22 inside-pad items and other residual inventory recorded, no electrical waiver. (E-R/E-F)|
|D-GAP-01|A|mixed|Coupled source/load method survives; unnamed 1 A ematch/1.5 A criterion superseded by selected J-Tek 1.125 A floor. (E-B)|
|D-GAP-02|A|current|C82/D9 local OUT and saved GND paths pass unchanged engineering bounds on current board; physical transient qualification remains. (E-F/E-O)|
|D-GAP-03|A|current|Exactly two U401.11 GND vias at mandated coordinates/sizes confirmed; filled/capped planar VIPPO quote/inspection remains required. (E-N/E-F/E-O)|
|D-GAP-04|A|current|C84 remains fitted in 199-part package; current order remarks require manual fitting after both reflows and qualified process. (E-N/E-M/E-O)|
|D-GAP-05|A|current|20 ms normal/36 ms intact-hardware guard and no-refresh interval retained; independent watchdog/gate RC arithmetic agrees, implementation/bench pending. (E-B/E-O)|
|D-AUD-03a|A|current|C120 native 1 uF/25 V X7R C29936 and matching existing land confirmed; bias/slew assumptions remain bench work. (E-N/E-O)|
|D-AUD-03b|A|current|Exact supplier orientation provenance retained; current fab binding passes. Factory preview is still required, not an assembled result. (E-M/E-O)|
|D-SS-04|A|mixed|Passive screen-before-enable and discharge/100 ms waits retained; two-bank nominal readings now 99.369/99.338 mV, not old three-bank 75 mV. (E-B/E-O)|
|D-GAP-01a|A|superseded|Old fixed path lengths/current values replaced by D-R11-03 native extraction, current load and selected match; R134 remains 2 ohm. (E-N/E-B)|
|D-GAP-02a|A|historical|Rejected diode placement is historical; present local-loop bounds are freshly checked, not that candidate's clearance. (E-F)|
|D-AUD-03c|A|current|Eight-finger orientation/body-origin method retained; no part/land substitution or widened generic tolerance inferred. (E-M/E-O)|
|D-GAP-02b|A|mixed|Numerical local-loop bounds survive; old positions/12.569/16.692 mm values replaced by current 13.004/14.762 mm. (E-F)|
|D-AUD-01a|A|current|C92/C120 share their existing supplier-code lands; all 209 native/XML values/footprints/identities agree. (E-N/E-M)|
|D-R9-01|A|current|Complete capacitor labels and current camera FAULT-delay obligation retained; labels agree natively, timing is not qualified. (E-N/E-O)|
|D-R9-02|A|current|Both-low passive screening, then PC1 with PE4 low, two locks/readback and no trace remain in generated obligations. (E-N/E-O)|
|D-R9-03|A|current|Current part population, pin legends and width checks pass; explicit R10 cost target retained, Extended cap removed later by owner audit2. (E-F/E-M/E-O)|
|D-R9-04|A|mixed|Earlier routing edits are historical coordinates; current AVA/R11 routes and residual M2 entries are scanned afresh. (E-R)|
|D-R9-05|A|current|Both centering tolerances and nut-inclusive <6.0/<5.3 mm hardware bounds are retained; actual hardware/fit remains pending. (E-F/E-O)|
|D-R9-06|A|historical|Rounds9/10 credit covers b337fe63 only; changed current layout requires fresh rounds. No old clean credit transferred. (E-P)|
|D-R10-01|A|current|Textbox/complete copper representation checks retained; selected current legend and barrel rules pass. No new mutation suite executed here. (E-F)|
|D-R10-02|A|current|4 V ADC limit and U5 body-plus-pad coating exclusion retained; C11/R13/R64 masking remains explicit. (E-B/E-O)|
|D-R10-03|A|superseded|Freeze/acceptance inventory applies only to historical b337fe63; later owner circuit/layout changes invalidate transfer of old clean pair. (E-P)|
|D-CIR-01|A|current|Selected MJG J-Tek 0.75 A x1.5=1.125 A floor retained; current conditional four-stall result is 1.283013 A, 20 ms lot test open. (E-B/E-O)|
|D-CIR-02|A|current|Camera-off pad policy and >=2.6Ah/>=4Ah duty-dependent packs retained as inferences; capacity/fire-time reserve and bay fit unmeasured. (E-O)|
|D-CIR-03|A|superseded|Circuit connectivity/pins remain; parked radio and forward terminals were explicitly temporary and replaced by AVA/R11. (E-N/E-F)|
|D-CIR-04|A|current|Circuit-pass fixture/legend fixes remain; current pin labels/required population pass. No canonical build rerun by this lens. (E-F/E-P)|
|D-AVA-01|A|mixed|Seven rows/local cells retained with R11 coordinates; exact translated GPS/radio cells and old 0c50 metrics superseded by bottom assembly repair. (E-N/E-F/E-R)|
|D-AVA-02|A|current|All-seven-terminal floor, fixed source bridges and manifest-before-final-gate support retained; current bindings/population pass. (E-F/E-M)|
|D-R11-01|A|current|Maximum terminal unions and x7.4/38.6 rows give 5.003012 mm; current poses/support/1.5 mm THT floor pass; pending physical fit remains explicit. (E-N/E-F/E-B)|
|D-R11-02|A|current|Required-fitted coverage now includes all 199 functional parts; current legends/model bounds pass selected native checks; regression suite not rerun here. (E-F/E-M)|
|D-R11-03|A|current|Budget bound to exact PCB and current copper; parts --check regenerates identically, independent coupled-load algebra reproduces all five fire cases. (E-B/E-N)|
|D-R11-04|A|mixed|Current ORDERING fixes camera/direct-UART/SD access/coat/staking duties; parent VEHICLE still stale (R12-REQ-02); procurement latest addendum applies. (E-O/E-N/E-M)|
|D-R11-05|A|current|Unmodified official10.0.7 CLI is the recorded root build environment; no DRC/CLI/version-validation rerun or patch by this lens. (E-P)|

## Prior-item closure checks

| Prior item | Current status | Fresh/current evidence |
|---|---|---|
|R11-BOM-01 / R11-MEC-01|closed for CAD floor in this lens|Fresh maker drawing+native x7.4/38.6+independent bare-bore equation=5.003011866 mm, all seven selected P-11 checks pass. Physical fit remains pending.|
|R11-REQ-01 / R11-PWR-01 / R11-DOC-01 firing-copper portion|closed for current evidence binding|parts --check recomputes current native budget identically; board SHA matches; five conditional fire cases reproduced. No physical current/20 ms proof inferred.|
|R11-m04 / R11-m07|current procedural correction present|ORDERING8.3/8.4 uses final selection-based coat mask/current probes/all-seven staking and explicit PCB removal or qualified SD lid-access window.|
|R11-m12|current recorded thermal correction present|All five DB125 GND pads are recorded with explicit thermals and selected K-copper passes; current package binding verified. Physical solder fill and first article assembly remain unqualified.|

## Primary sources and qualification boundary

- S-IMU: [All features](https://www.st.com/en/mems-and-sensors/lsm6dsv320x.html). Fresh primary HTML; +/-4000dps and dual low/high-g full scales. Large datasheet fetch failed (web size limit; CLI timeout), so no fresh full-datasheet ODR/accuracy qualification claimed.

- S-MCU: [DS12110 Rev11 Tables109-110 pp207-208; related pin table](https://www.st.com/resource/en/datasheet/stm32h743vi.pdf). Fresh primary PDF text; analog FT_a4 V ceiling, digital FT supply-dependent ceiling/pulls and injection limits. Native pin agreement is separate from AF/firmware qualification.

- S-BARO: [06/2017 pp1,3-4,15,17](https://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocFormat=pdf&DocLang=English&DocNm=MS5611-01BA03&DocType=Data+Sheet&PartCntxt=MS561101BA03-50). Fresh primary PDF;10..1200mbar, supply/reflow/no-clean handling. No repeat-reflow or installed sensor performance inferred.

- S-MATCH: [p1, firing characteristics/test definitions](https://electricmatch.com/upload/JTEK_TECHNICAL_INFORMATION_SHEET_SPECIFICATIONS.PDF). Fresh maker sheet;0.75 A all-fire is a0.5s test.1.125 A is project1.5x margin;20 ms lot/charge qualification remains open.

- S-TERMINAL: [DORABO T0-1 sheet1/1,2022-11-26](https://atta.szlcsc.com/upload/public/pdf/source/20251124/8C215F69B14C8E54AE0F8E5023D4AE9F.pdf). Downloaded primary drawing and visually inspected:7.40 depth,3.90 rear datum/general tolerances,8.60 height,3.50+/-0.30tail,0.42interlock,28-16AWG,10AUL,0.2Nm. Current envelope unions/calculated wire room checked independently.

- S-RADIO: [Specifications/Interfaces/Communication Frequency](https://micoair.com/en/docs/telemetry/lr900/lr900-telemetry). Fresh primary maker HTML: LR900-F3.3 V UART,4.5-5Vsupply,1Wmaximum average;890-915 MHz and manual0-25. No installed/regulatory/ESD qualification inferred.

Other historical maker/source selections remain linked in `parts_qualification.md`; this lens did not independently re-read every component datasheet or reconstruct every supplier pad map. A Molex drawing download timed out; native socket/pin/bypass requirements were checked without claiming a fresh full drawing requalification. Downloaded temporary files are removed after report creation.

The recorded05:00UTC supplier snapshot meets the board-cost cap at$79.53, about$81.87 including minimum purchases/feeder share, before fixed/process/PCB/shipping/consignment. U4/R430 stock and U9 minimum purchase remain ordering constraints. This lens checked snapshot arithmetic/input binding, not a new live supplier quote. Firmware, selected-card behavior, e-match lot/charge firing, electrical/thermal/hot-plug waveforms, installed RF/ESD, harness/switch/sled/bore/shroud fit, coating/retention, VIPPO/manual-C84/panel acceptance and first article workmanship remain unverified. No clean-round or owner-acceptance claim is made.
