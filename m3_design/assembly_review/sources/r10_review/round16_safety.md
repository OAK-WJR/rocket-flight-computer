# Round16 safety review

**0 Critical / 0 Major / 0 Minor.** Fresh full safety review of committed `b1b8658d5bf541795b7e7636c09f2e886ea8c67a`. No demonstrated current AGENTS §2 violation was found in the amended CAD-candidate scope. Firmware and physical safety remain unqualified.

PCB SHA256 before/after: `632a9ad36c19426ede219b6ff6b0d638955665cac1b4704d3392a6afdbe03982` (2,256,162 bytes). No canonical edit,git action,GUI attempt,subagent,full build or check.sh run. No current-round peer material was read. All119 decision IDs and22 owner scopes were considered under their latest amendments;the JSON preserves §2 verbatim and the scope inventory.

## Fresh topology and fault evidence

One root-reserved official Eeschema10.0.7 export exited0. All209 parts/651 unique pin mappings match the saved netlist;native PCB pad nets have0 mismatches. The source schematic SHA stayed `4c3cd068…`;fresh export SHA is `5111171216e8288a449421040ca2f3e9a5b62b42ab7ec8bb6686dc1ccce46f49`.

| Property | Current reconstruction |
|---|---|
| Fire source | J1.1 -> Q120 drain/shared ACT_FET_S sources/Q121 drain RAW_ACT -> R1342ohm -> J121.2 IGN -> match -> J121.1 OUT -> Q124 -> GND. No BAT_IN or RAW_PROTECTED bypass |
| Switch | J400 F(7.4,65.85),through separate R80/R165470k to BAT_IN/U9 EN. No J124,pull-pin or switch-state input |
| Controls | PC1/U1.16 -> R1221k/Q122,with R123100k toGND;PE4/U1.3 -> R126220ohm/Q124,with R1271k,R12810k,C126220nF |
| High-side off bias | Q120/Q121 B(13.5,73.6)/(13.5,68.6) retain R120100k and C1201uF25V to their shared source,and R12110k to Q122. This P-channel source pull-up is distinguished from Q124's required pull-down |
| Sense | PC0/U1.15 CONT and PC5/U1.33 sole RAW_ACT bank each have two5.1k series tops,two2k parallel bottoms,10nF filter. Duplicate bank/ADC tails absent |
| Fault algebra | Eight divider resistors individually open/short and two filters open/short:352 tolerance evaluations including healthy. Maximum3.342170829V at19.9V;maximum8.4V branch1.397310178mA |
| Cold algebra | Nominal healthy CONT/BUS99.368924/99.337881mV;open146.226415/0mV;grounded drain0/0mV.16,384 illustrative cold corners across four states;shorted match resembles healthy. Bands exclude leakage/ADC errors |
| Inner copper | Four native protected barrels pass1mm. Binary collision search gives J121.1-to-In2 3V3≈1.102502mm;J121.2/OUT via/GATE via minima1.900001/2.698436/2.100001mm. Fabricated-hole/registration allocation remains open |

Fresh native S-1…S-9,K-contract,K-loader,K-actuators with actual BOM/CPL pass;all eight in-memory bypass/bias/capacitor/population negative controls reject. These are selected checks,not a full gate or DRC run.

[AONR21357 Rev2.1 pp1–2](https://www.aosmd.com/res/datasheets/AONR21357.pdf),[AON7524 Rev1.1 pp1–2](https://www.aosmd.com/sites/default/files/res/datasheets/AON7524.pdf) and[AO3400A Rev3.1 pp1–2](https://www.aosmd.com/sites/default/files/res/datasheets/AO3400A.pdf) confirm pin roles/ratings. AON7524 page2 was visually inspected:gate leakage is10microamp. Conditional25C static gate examples are Q12235.7mV/Q12411.368mV;they do not prove hot or Miller behavior. Fresh[ST DS12110 Rev11](https://www.st.com/resource/en/datasheet/stm32h743vi.pdf) p32 gives analog reset defaults;Tables109/110 pp207–208 give4V analog stress and zero positive-injection allowance. The named cached ST PDF was Rev8 and excluded from current limits;local Rev11 downloads failed,so no local Rev11 visual review is claimed.

Fresh native firing paths measure BAT_IN6.307107mm/1mm,one source path2.2mm/0.4mm,RAW_ACT5.886133mm/0.5mm,IGN10.230382mm/0.5mm and OUT7.854478mm/0.5mm. Independent coupled-load algebra reproduces4.617458126ohm loop and1.544366/1.479438/1.414264/1.348805/1.283013A at0…4stalls,above1.125A under the stated conditions. [MJG J-Tek p1](https://electricmatch.com/upload/JTEK_TECHNICAL_INFORMATION_SHEET_SPECIFICATIONS.PDF) gives0.75A all-fire under0.5s and40mA maximum test current;the actual20ms lot/charge pulse remains unqualified.

The960-cycle IWDG allocation is28.571429–32.653061ms;sync/reset/tail allocations give34.853061ms<36ms. Nominal floating-gate RC to0.4V is0.504796ms;the tolerance model plus22nC is0.739195ms,not a measured tail. R134's conservative70C stress is35.797452W/1.288708J at36ms. Fresh complete-page[Bourns CRM p3](https://www.bourns.com/docs/product-datasheets/CRM.pdf) inspection supports about61/44W at20/36ms by graph interpolation;actual hot/repeated pulses are unqualified.

## Policy and rejected hypotheses

Current schematic note,binding,REQUIREMENTS,M3,FMEA and ORDERING8 agree:both controls low for the PASSIVE cold screen beforePC1 enable;after prior enable wait>=1s and verify discharge/gate off;thenPC1 high/PE4 low>=100ms before powered checks. Ground faults hard-refuse. Accelerometer+barometer launch detection precedes fire;in-flight sensing logs/annunciates and never vetoes recovery. Normal physical current including tail<=20ms,no watchdog refresh during fire,and valid SAFETY refresh<=5ms after current ends remain unimplemented obligations.

On-rail/on-last/off-first J400 use,no USB/self-powered source while attaching a match,and USB bench pack-or-match disconnection are retained. GPS/radio stay always-on/direct;camera alone keeps U402/U12/U13. No hidden switch-opening detector,removed shedding or software-independent two-channel safety is credited. Ordinary surface faults,unfused entry,shared MCU and isolated Blue Jay are disclosed architecture. Current coating/staking/harness instructions retain dummy loads,all-seven-terminal retention,J2 covering and sensor exclusions.

The JSON preserves six rejected C/M hypotheses:direct-pack bypass,unbiased healthy reset gates,single-divider overstress,cold-screen-after-enable,failed current/watchdog budget,and an undisclosed back-feed/trace/surface-bridge safe state. None is an active finding. Historical R9 cold-order,R13 reference-branch wording andR14 fire-current rechecks close on current evidence. A later failed-short Q124 or conductive contamination can still fire an enabled match;this is not prevented by a prior cold screen.

No firmware,threshold/current-tail,selected-lot firing,shorted-match logic-survival,electrical/thermal/transient/endurance,installed RF/ESD,harness/switch/coating/retention/access/fit/flight or first-article result was produced. Initial API probe setup failure and nonfatal native/Fontconfig diagnostics are disclosed in JSON. Reports are final and immutable after handoff.
