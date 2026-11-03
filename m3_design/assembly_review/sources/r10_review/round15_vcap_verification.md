# Round 15 focused VCAP verification

PASS — independent assessment complete. Retain R15-MCU-01 as a Minor qualification gap. No installed capacitance/ESR violation or regulator failure was demonstrated. This does not establish electrical qualification.

Target commit before/after: `789f4d516251991bdf1518254d537ff7b41f65bb`.
PCB SHA256 before/after: `7866d6b895573eb10c14d0227ee4bdde8b4fba6145529786cd554cdb80121783`.
PCB size: 2,257,812 bytes. Finished 2026-10-30T14:10:49.507641Z.

## Native evidence

Read AGENTS.md, the assigned verifier packet, REQUIREMENTS, current owner amendments and newest R10_DECISIONS entries. Initial maker/native inspection preceded reading only the assigned original round15_mcu report.

| Ref | Native pose | Identity | Connection |
|---|---|---|---|
| C19 | B(28.35,37.65), −90° | Samsung CL10A225KO8NNNC, C23630; 2.2uF 16V X5R 10%; rocket:C0603 | Pad1 (28.35,36.95), VCAP1/U1.48; pad2 (28.35,38.35), GND |
| C20 | B(19.8,37.3), 0° | Same fitted part and footprint | Pad1 (19.1,37.3), VCAP2/U1.73; pad2 (20.5,37.3), GND |

Both capacitors are fitted and included in BOM/placement attributes. Each land is 0.8×0.9mm, with 1.4mm centre pitch. Native mcu.kicad_sch and schematic.net.xml agree with PCB identities and separate nets. U1 is STM32H743VIT6TR at F(23,43), rotation0.

The existing parts_qualification.md row inventories nominal values but does not close combined operating capacitance or ESR.

## Requirement and interpretation

[ST DS12110 Rev11](https://www.st.com/resource/en/datasheet/stm32h743vi.pdf), Table114 p211, specifies 2.2uF typical with ±20% variation and ESR<100mΩ. Its bypass alternative uses 100nF. The table supplies no measurement frequency/amplitude or explicit definition separating initial selection tolerance from combined effective capacitance.

Therefore 1.76–2.64uF is the numerical interpretation to resolve for in-circuit qualification, not a newly proven effective-capacitance guarantee. Fitted nominal tolerance gives 1.98–2.42uF and complies with nominal selection.

The active project bay is −20…+70°C. Firmware is unqualified; its thermal policy calls for 200MHz normally, at most300MHz, or monitored/throttled400MHz. A200MHz requirement does not prove VOS3 selection. Local capacitor temperature is not MCU junction temperature or measured bay temperature.

## Fresh maker evidence and calculations

[Samsung exact family data](https://product.samsungsem.com/mlcc/CL10A225KO8NNN.do) includes the fitted packaging variant and labels characterization typical. Fresh interpolation reproduces the original candidate's1.716525uF inference. Detailed conditions and results are in the JSON.

The [current exact-part specification](https://product.samsungsem.com/part/download.do?masterKey=CL10A225KO8NNN&type=specsheet), issued2024-05-08, was obtained directly from Samsung. Page2 was rendered and visually checked. Its capacitance test is1kHz±10%/1.0±0.2Vrms following150°C heat treatment and24±2h recovery; X5R temperature variation is±15%. Manual pp12–17 requires consideration of AC/DC voltage, temperature and aging; aging is model dependent.

The unclosed zero-bias tolerance/temperature allocation is1.683–2.783uF. These are conservative allowed bounds, not demonstrated attainable corners.

The separate typical TCC/DC-bias product is an inference, not a guaranteed joint corner. Samsung's8V biased-temperature example also shows temperature/bias dependence need not separate: its25→70°C change is+1.97258%, while the zero-bias curve changes−9.72467%. The8V data cannot qualify VCAP.

Small-signal AC dependence adds uncertainty. It must not be blindly multiplied into the other curves. No exact-part guaranteed aging coefficient, combined effective-C envelope or operating ESR limit was established. Typical ESR at selected frequencies cannot supply that guarantee.

## Disposition and concrete closure

The earlier Major hypothesis remains recorded: inadequate stabilization could impair MCU functions. It is narrowed because neither the interpretation needed to prove a violation nor an actual out-of-limit component/regulator result has been demonstrated.

Retaining the existing parts is bounded to the unqualified CAD candidate. Close the qualification row by:

1. Resolving ST's intended C/ESR measurement conditions and recording silicon revision and allowed startup/operating regulator modes.
2. Obtaining maker-supported combined-condition bounds, or qualifying exact fitted parts after process/rework and defined aging over actual bias, local temperature and relevant frequency/ripple conditions.
3. Checking both capacitance limits, ESR, startup and load/clock transients. Keep capacitor surface temperature within its rating.

No replacement is established as necessary or qualified. A3.3uF±10% substitution has a2.97–3.63uF nominal range, already above2.64uF. Any future replacement needs exact maker identity, suitable lands/process and verified lower/upper capacitance plus ESR; larger nominal capacitance alone is not a correction.

## Checks and limits

- Python hashlib and raw HEAD/ref reads: assigned commit and PCB hash match before/after; no git commands.
- Native pcbnew.LoadBoard/GetFields/Pads/GetTracks: identities, poses, fitted attributes and connections confirmed. Initial GetProperties probe was unsupported; corrected API checks exited0. Nonfatal headless wx warnings were disclosed.
- Native schematic and XML inspection: matching identities and per-pin nets. Initial root-sheet lookup was corrected to mcu.kicad_sch.
- Samsung direct specification download:38pages,3,011,426bytes; SHA256 `7ad029052a9bd944e0fd77e7d8e814676dfb7285a5e18b8760a538d5a978e49e`. Text inspected and p2 JPEG rendered in memory; initial PNG transfer exceeded output allowance.
- Samsung chart JSON and unit JavaScript: fresh parsing/interpolation completed; no peer probes used.
- Current official ST web table, footnotes and mode limits: read successfully. Direct PDF fetch timed out; current ST page visuals were not inspected. Cached Rev8 was excluded.
- No files/probes edited, native CLI invoked, build/full gate run, GUI operated or subagents spawned.

These checks connect native decoupling selection to the MCU regulator and project operating policy. They do not prove whole-board operation, stability, lifetime or physical/firmware qualification. The full-round review remains separate.
