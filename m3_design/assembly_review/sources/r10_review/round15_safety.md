# Round15 safety review

**0 Critical / 0 Major / 0 Minor.** Complete fresh safety review of committed `789f4d516251991bdf1518254d537ff7b41f65bb`. No demonstrated AGENTS section2 violation in the current stated scope. Firmware and physical safety remain unqualified.

PCB SHA256 before and after: `7866d6b895573eb10c14d0227ee4bdde8b4fba6145529786cd554cdb80121783` (2,257,812bytes;209 footprints,957tracks,296vias). No preexisting source/CAD/fab/report was changed. No peer round15 material,CLI,full build/check.sh,GUI,subagent or git action was used.

## Fresh reconstruction

Actual native sheet/library pin geometry,wire segments,labels and NC flags across15 reachable sheets produce651 unique contact mappings,with zero XML or PCB mismatch. All100 MCU nets agree with the reviewed table and all four evidence hashes match. Read-only S1-S9,K-actuators,K-loader and S4 with the actual BOM/CPL pass;all199 required parts are fitted. Eight in-memory unsafe topology/bias controls are rejected.

| Check | Current evidence |
|---|---|
| Single switch | J400 F(7.4,65.85) has only protected switch contacts;R80/R165470k reach BAT_IN/U9 EN. No J124,pull-pin or direct switch sensor |
| Fire source | J1 -> Q120 drain/shared sources/Q121 drain RAW_ACT -> R1342ohm -> J121.2 IGN -> match -> J121.1 OUT -> Q124 -> GND. No direct-pack or RAW_PROTECTED bypass |
| Two controls | PC1/U1.16 ->R1221k/Q122,with R123100k pull-down;PE4/U1.3 ->R126220ohm/Q124,with R1271k,R12810k,C126220nF |
| High-side off network | Q120/Q121 B(13.5,73.6)/(13.5,68.6) retain source-referenced R120100k/C1201uF25V and R12110k to Q122 drain |
| Sense banks | PC0 CONT/PC5 sole RAW_ACT bank each have two5.1k series tops,two2k parallel bottoms and10nF;duplicate bank/ADC tails absent |
| Single faults | Every bank resistor individually open/short,plus each filter open/short:20 modes,352 tolerance evaluations including healthy. Maximum3.342170829V at19.9V;worst8.4V diagnostic branch1.397310mA |
| Cold screen | Independent nodal solve:healthy1-2ohm CONT99.367503-99.370345mV/BUS99.334868-99.340894mV;open146.226415/0mV;grounded drain0/0mV;10,240 source/diode/resistor cold corners evaluated;no threshold/leakage qualification inferred |
| Barrels | Four native protected barrels pass>=1mm;nearest J121.1-to-In2 3V3 approximately1.103mm. Other minima1.900/2.699/2.100mm at the probe's1micrometre search resolution |

[AONR21357 Rev2.1 pp1-2](https://www.aosmd.com/sites/default/files/res/datasheets/AONR21357.pdf),[AON7524 Rev1.1 pp1-2](https://www.aosmd.com/sites/default/files/res/datasheets/AON7524.pdf) and [AO3400A Rev3.1 pp1-2](https://www.aosmd.com/sites/default/files/res/datasheets/AO3400A.pdf) confirm device roles. The AON7524 gate-leakage bound is10microamp,not100nanoamp. Conditional reset-leakage examples give Q122 gate0.111595V/Q124 gate0.011935V. These maker-test calculations do not prove hot,Miller,power-up or unpowered waveforms. [ST DS12110 Rev11 Tables109/110](https://www.st.com/resource/en/datasheet/stm32h743vi.pdf) supplies the4V analog stress ceiling;no generic positive VDD-clamp behavior was invented for the FT banks.

Native retained firing tracks independently measure BAT_IN6.307107mm/1mm,one source path2.2mm/0.4mm,RAW_ACT5.886133mm/0.5mm,IGN10.230382mm/0.5mm and OUT7.854478mm/0.5mm. There is no series fire via or parallel-source credit. The stated hot/source/harness/load assumptions give4.617458126ohm loop and1.544366/1.479438/1.414264/1.348805/1.283013A at0-4 stalls. All exceed1.125A. [MJG J-Tek p1](https://electricmatch.com/upload/JTEK_TECHNICAL_INFORMATION_SHEET_SPECIFICATIONS.PDF) defines its0.75A datum over0.5s;it does not qualify our actual lot/charge20ms pulse.

The960-cycle IWDG allocation gives28.571429-32.653061ms and34.853061ms with stated synchronization/reset/tail allocations,below36ms. Independent nominal floating-gate RC to0.4V is0.504796ms;the tolerance RC plus22nC allowance is approximately0.739195ms. Actual current tail<=1.5ms remains a bench obligation. R134's conservative70C stress is35.797452W,0.715949J/20ms or1.288708J/36ms. [Bourns CRM p3](https://www.bourns.com/docs/product-datasheets/CRM.pdf) visually supports approximate61/44W graph interpolation;hot/repetitive/installed pulse qualification is absent.

## Policy and residual scope

The native schematic note,current binding,M3 record,FMEA and ORDERING8 agree:both controls low for passive cold screening **before PC1 enable**;after prior enable wait>=1s and verify discharge/gate off;then PC1 high/PE4 low and>=100ms settling. Ground faults hard-refuse. Accelerometer+barometer launch detection precedes fire;in-flight sense readings only log/annunciate and never veto fire. Normal physical current including tail<=20ms,no watchdog refresh during firing,and valid safety refresh<=5ms after current ends remain explicit unimplemented obligations.

On-rail/on-last/off-first J400 use,no USB/self-powered source while attaching the match,and USB bench pack-or-match disconnection are preserved. GPS/radio are always on/direct;camera alone retains U402/U12/U13. [TPS2553 RevG p7](https://www.ti.com/lit/ds/symlink/tps2553.pdf) specifies delayed enabled reverse cutoff;[TXU0202 RevA](https://www.ti.com/lit/ds/symlink/txu0202.pdf) signal isolation does not establish power-pin disconnection. No unobservable switch-opening detector or removed port shedding is credited.

Current ordering/coating instructions retain dummy loads,per-pin DB125 verification,qualified clamps/ferrules,all-seven-body staking/strain relief,mandatory local pyro coating/taped-acrylic J2,U4/U5 exclusions and the sole controlled TP122 exception. Repeat gate/NRST checks after coating,rework or firmware changes. The single MCU,ordinary surface gaps,no powered physical break,unfused input,off-board servo motor wiring and isolated Blue Jay remain disclosed architecture. Pending physical/FW qualification alone is not converted into a demonstrated failure.

All116 decision IDs and22 owner mandates were considered under their latest amendments;AGENTS section2 is preserved verbatim in JSON. AVA images supply no hidden circuit evidence. Closed rechecks:R14-SAF-01 FMEA currents now match the fresh native budget;R13-SAF-01 correctly names signal-reference resistance;R9-SAF-01 cold ordering is retained. No active C/M candidate remains.

The JSON records executed checks,measured native evidence,20 single-bank fault modes,closed/rejected hypotheses,source versions/hashes and limits. Named cached ST material was Rev8 and excluded from current limits;fresh official Rev11 web text was used after local downloads failed. No local Rev11 visual review is claimed. Scratch API/argument/solver setup failures were corrected and rerun;they supply no passing evidence. No firmware,physical pulse,selected-lot firing,shorted-match logic survival,electrical/thermal/transient/RF/harness/coating/retention/access/fit/flight or first-article qualification was performed.
