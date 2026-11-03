# Round14 safety review

**0 Critical / 0 Major / 1 Minor.** Fresh full review of committed `f5e4a5a94013514edb952fd328325341b63a98df`; no demonstrated AGENTS section2 hardware violation within the stated design scope. Firmware and physical safety behavior remain unqualified.

PCB before and after: `e0e3ad841654128792b32ab778ca19e4a71e596fa89864074ec4e91e6a5ccfc6`. Native inventory:209 footprints,966 straight segments,296 vias. No canonical files changed; only this report pair and ignored probes were written. No peer round14 report was read.

## Active finding

**R14-SAF-01 - Minor, new: active FMEA amendment retains circuit-pass firing currents.** `docs/FMEA_REDUNDANCY.md:21-22` states1.546/1.481/1.284A for0/1/4 stalls. Fresh native endpoint sums at Q120 B(13.5,73.6),Q121 B(13.5,68.6),R134 B(16.5,64),Q124 F(13.9,57.37) give a4.617458126ohm loop and **1.544366072/1.479437787/1.283013039A**, matching the current board-bound `parts_budget.json`. This is a bounded stale record: the lowest result still exceeds1.125A; no function failure follows. [MJG sheet,p1](https://electricmatch.com/upload/JTEK_TECHNICAL_INFORMATION_SHEET_SPECIFICATIONS.PDF) supplies the selected all-fire datum, not the source/board calculation or20ms qualification.

**Fix:** update the active FMEA header to1.544/1.479/1.283A and the current PCB binding, or label the old numbers with their circuit-pass board. Preserve source/hot-FET/harness and selected-lot20ms qualifications.

## Independent reconstruction

| Check | Current evidence |
|---|---|
| Exact identity | Target HEAD and PCB hash match; hash rechecked after native probes |
| Native/schematic consistency | 651 XML contact keys;zero native/XML differences. All100 U1 pins agree with r10_net/binding; all four evidence hashes match |
| Single switch | J400 contacts only BAT_SW_SOURCE/RETURN through R80/R165470k to BAT_IN/U9 EN; R81300k/C872.2uF retained. No J124/pull-pin or switch-state sensor |
| Power path | J1.1 BAT_IN ->Q120 drain/shared ACT_FET_S sources/Q121 drain RAW_ACT ->R1342ohm ->J121.2 IGN ->external match ->J121.1 OUT ->Q124 ->GND. No direct BAT_IN/RAW_PROTECTED bypass |
| Independent controls | PC1/U1.16 ->R1221k ->Q122, R123100k toGND. PE4/U1.3 ->R126220ohm ->Q124 gate; R1271k MCU-side pull/R12810k gate-source pull/C126220nF retained |
| High-side off bias | Q120/Q121 share R120100k/C1201uF25V to their source and R12110k to Q122 drain. This is the source-referenced off network for the P-channel pair |
| Direct sensing | PC0/U1.15 CONT and PC5/U1.33 sole RAW_ACT sense. Each has two5.1k series tops,two2k parallel bottoms,10nF;duplicate PB0 bank and ADC tails absent |
| Single-resistor faults | 288 independent evaluations: each top/bottom open or short,+/-1.45% corners,19.9V bus. Maximum **3.342170829V**, below the4V absolute-stress ceiling; ground/fault thresholds still require qualification |
| Cold screen | Independent nodal solve: healthy1-2ohm CONT99.367503-99.370345mV,BUS99.334868-99.340894mV;open CONT146.226415mV/BUS0;grounded Q124 drain near0. Corner evaluations and assumptions are in JSON |
| Protected barrels | Independent native minima **1.102502/1.900001/2.698435/2.100000mm** for J121 OUT/IGN,OUT via and GATE via. No inner drawings/fields. Unchanged floor1mm passes |
| Population | S-4 separately checked actual BOM/CPL:all199 required-fitted parts pass; no omitted gate/sense/current-limit parts |
| Negative controls | Seven in-memory cap/pull/enable/bypass/coalesced-control mutants all detected. These are focused-contract checks, not whole-gate escape tests |

[AONR21357,pp1-2](https://www.aosmd.com/res/datasheets/AONR21357.pdf) and [AON7524,pp1-2](https://www.aosmd.com/sites/default/files/res/datasheets/AON7524.pdf) confirm the P/N-channel roles; [AO3400A,p2](https://www.aosmd.com/sites/default/files/res/datasheets/AO3400A.pdf) supports the enable stage. A conservative leakage example gives Q122 gate0.111595V and Q124 gate0.011935V. The latter uses the actual AON7524 **10uA** gate-leakage limit, not AO3400A's100nA. These are calculations at maker test premises, not measured hot/unpowered transition guarantees.

Independent native firing lengths/widths(mm):BAT_IN6.307107/1.0,ACT_FET_S2.2/0.4,RAW_ACT5.886133/0.5,IGN10.230382/0.5,OUT7.854478/0.5. Copper29.362412milliohm at20C/35.132126milliohm at70C;no series fire via or parallel-source credit. The current F7 source/material/FET/harness allocations reproduce0-4 stall currents1.544366/1.479438/1.414264/1.348805/1.283013A. Those allocations are not measured source/current guarantees.

The960-cycle watchdog gives28.571429-32.653061ms under [ST DS12110 Rev11,Table136](https://www.st.com/resource/en/datasheet/stm32h743vi.pdf); adding the stated synchronization/reset/tail allocations gives34.853061ms versus36ms. R134's conservative70C stress is35.797452W,0.715949J/20ms and1.288708J/36ms. [Bourns CRM,p3](https://www.bourns.com/docs/product-datasheets/CRM.pdf) visually supports approximately61/44W at20/36ms by log interpolation;this is not hot-board/repetitive-pulse qualification. Normal physical current including tail remains<=20ms;no refresh while firing;actual tail and timing are unmeasured.

## Safety policy and current amendments

The current schematic note,circuit manifest,binding,M3 record and ORDERING all preserve both-low **passive screening before PC1 enable**,>=1s plus verified discharge after prior enable,then PC1 high/PE4 low with>=100ms settling before powered checks. No firing before accelerometer+barometer launch detection. Ground sense failures hard-refuse;in-flight readings only log/annunciate and never veto. No R10 firmware implements this yet. R1 `assembly_binding.py`/build.py do not become an R10 executable binding through the evidence JSON.

Current procedures retain on-rail/on-last/off-first J400 use,USB bench work with pack or match disconnected,and **no USB/self-powered back-feed source when connecting the match**. Native GPS/radio supplies/UARTs are always-on/direct;camera alone retains U402/U12/U13. Back-feed can conceal switch opening;no firmware observation or removed port cutoff is credited. The unfused battery stretch and servo fault risks remain disclosed;the Blue Jay remains electrically isolated.

All113 decision IDs and22 owner mandates were considered under the latest single-switch,AUD/GAP,always-on/microSD,all-DB125,audit2 and R11-R13 amendments. Earlier ARM links,three sense banks,port switches/translators,header/tie holes and old stop instructions were not treated as current. No AGENTS section2 limit was changed. JSON records every ID and source hash.

Closed rechecks: R13-SAF-01 reference-branch wording is corrected;R9-SAF-01 cold-screen ordering is corrected;R3-SAF-01 protected-barrel placement passes the current amended floor. Existing surface-bridge,back-feed,unfused-entry and physical/firmware qualification risks remain in the current deviation inventory rather than being counted as new failures.

## Executed checks and limits

Fresh read-only native API:pad/XML graph,100-pin/four-hash comparison,independent saved-fill/pad/via/track geometry,S-1..S-9/K-actuators/K-loader,actual-export S-4,and seven in-memory negative controls. Independent arithmetic:single-resistor faults,cold nominal/corners,native-copper fire/pack sag,watchdog and R134 stress. Fresh maker originals and rendered AOS/JSCJ/MJG/Bourns pages were inspected;ST/TI official web text was checked. Local ST PDF download failed;no local ST visual review is claimed.

No native CLI,full build/check.sh,GUI retry,canonical source/CAD edit,physical test,firmware execution,owner acceptance or order. Failed scratch API probes are disclosed in JSON and supply no passing evidence. Thresholds,reset/Miller/current tail,hot R134/shorted-match logic survival,switch/harness,RF/ESD,coating/process and installed physical behavior remain unqualified. The durable measurements,states,source URLs/hashes and check results are in `round14_safety.json`.
