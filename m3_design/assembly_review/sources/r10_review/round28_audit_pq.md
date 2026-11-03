# R10 round 28 fix pass: audit lane A, `parts_qualification.md` (2026-11-02)

Scope: `m3_design/assembly_review/sources/r10_design/parts_qualification.md` only (plus this hand-back). Base commit
`19dd0b5`, branch `m3-assy-r10`. No git change, no other file edited, no local absolute path added.

**Board.** Every board read (KiCad Python, read-only: footprints, pads, nets, tracks, vias, check_r10's `port_clamps`,
`s8`, `barrel_shapes`, `barrel_rings`) was on PCB `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c`;
the SHA-256 was checked before and after each read. While I worked, the CAD lane's build and checks rewrote
`m3.kicad_pcb` in passing (`b3b4aac5…` and `64f7ee2d…` were seen mid-run; `a0ec075e…` again in between). Root: confirm
the final board is `a0ec075e…`, because the file now says the round 28 fix pass leaves the board unchanged.

**Budget.** The CAD lane regenerated `parts_budget.json` (D-R28-01, R28-TRI-03). Its working-tree SHA-256 is
`4267634220f4254aef28dfc9756c68b29784560c11b994c14274790dd631fab2`. Only lines 91–92 changed, to 5.8808312447840425 /
4.388490666810671 V. `round28_fix_cad.md` had not appeared when I finished. **Root to bind:** check the GAP-1 budget-SHA
sentence (file line 493) against the CAD lane's final hash.

**Sources used:**
- the board, `schematic`-level facts through the board netlist, and `pin_table.tsv`;
- `fab/` (JLC BOM 81 lines, 206 placed; CPL 206 rows; `cost_check.json` 12:44:13Z; `stock_check.json` 12:43:17Z);
- `parts_budget.json` (above), `r10_parts.py`, `circuit.json`, `tools/jlc_corrections.json`, `r10_place.tsv`;
- R10_DECISIONS (D-R18-08, D-R20-09, D-R21-07, D-R24-17, D-R26-01…04, D-R27-01, D-R28-01);
- cached datasheets (`.supervisor/primary_pdf_cache_paths.json`), read as text with printed page = PDF page: DS12110 Rev 8,
  DS15034 Rev 1, DS14623 Rev 1, DS14764 Rev 1, SLVSFC9C, SBVS282A, DS41326 Rev 3-2, SLVS841G, SLVSEA3F, ESD103 Rev 1.3,
  J-Tek sheet, AONR21357 Rev 2.1, AO3400A Rev 3.1, AON7524 Rev 1.1, SRP5030T, TPS709, SCES942A, MA-series (C84), FOJAN FRC,
  LED1 / LED2 / LS120 sheets, W25Q128JV (cached Rev G);
- the round 18 boards `632a9ad3…` (commit `dcbb6c8`) and `a3144b15…` (`acba196`), extracted to scratch for copper
  comparisons.

Scratch probes (ignored by git): `.supervisor/r28_audit_pq/` (`dump.py`, `tracks.py`, `clamps.py`, `s8.py`, `s8b.py`,
`netgeo.py`, `pg.py`, `q.py`, the board and track JSON, and `pq_before.md`, the file before this pass).

## 1. Section classification

| Lines (after) | Section | Class |
|---|---|---|
| 1–8 | Title and scope | Current (with dated source-reading records) |
| 11–14 | Current circuit amendment and review status | Current |
| 16–24 | Round 24 component amendment (D402) | Current |
| 26–28 | Round 19 amendments, totals paragraph | History (says so: "at the time", "superseded by the round 24 figures above") |
| 30–38 | Round 19 table (U4, U4 alternate, C87, C123, J440 cell, C84, TP121) | Current (dated stock lines are labelled as dated) |
| 40–47 | Round 23 notes; cold-end ratings | Current |
| 49–62 | R16 retained MEMS stress deviation | Current deviation (R16 figures, re-sampled) |
| 64–72 | R17 record amendments | Record of D-R17-01 (the sealed pad worksheet; current worksheet in ORDERING 8.1.1) |
| 74–88 | Programming acceptance; U5 height | Current |
| 90–110 | Always-on GPS/radio | Current |
| 112–131 | Camera switch; camera harness; Round 12 correction | Current |
| 133–152 | Shared port fault budget | Current |
| 154–202 | microSD socket and supply | Current (dated stock line) |
| 204–246 | All wired connectors use screw terminals | Current (dated stock line, D-R11-01 envelope) |
| 249–264 | Round-9 retained capacitor labels | Current inventory (now stated as 19 of the original 21) |
| 266–343 | Round-15 component qualification | Mixed: measurements on `7866d6b8…` (labelled), current S-8 figures added |
| 346–562 | AUD/GAP amendments (AUD-1, -3, -4/5/7/9, cold check, GAP-1, -5, -2) | Current parts and figures; the 2026-10-28 placements are now labelled history |
| 564–616 | Supply contract and sources | Current (one labelled history note) |
| 618–727 | Voltage, current and thermal budgets | Mixed: labelled history (GPS / radio rows, R18-PWR-03, per-port budget, upstream coordination) and current (stall input, GAP-3) |
| 729–812 | Off-state and USB back-feed | Mixed: AUD-8 labelled history for GPS / radio; the rest current; GH-era loop split labelled history |
| 814–853 | Battery-lead break ride-through; OQ-5 | Current (R3 table kept as labelled history); OQ-5 hypothetical, not adopted |
| 855–899 | Local lands, envelopes and assembly | Current (GH rows and the first-session HTTP 403 note now labelled history) |
| 901–925 | Servo-reference return and mass | Current |
| 927–974 | Round-5 records; current USB-only calculation | Current records (TP89 item now says the pad is gone) |
| 976–1033 | Round-6, Round-7, Round-8 records | History (each heading or first sentence now names the current figure) |
| 1034–1088 | Historical R92 / R166 changes before round 9 | History (first sentence now names the current part and results) |

## 2. Statements changed (before → after, evidence)

### Triage items
1. **R28-TRI-02** (GAP-1, l.475): "includes 12.370807 W ... always-on GPS/radio" → "13.064091 W (12.370807 W before D-R19-14's
   100 mA AUX allowance) ... the always-on GPS/radio/AUX ports". Evidence: budget `other_converter_load_W` 13.06409056783647;
   5.546269 × 1.561 / 0.8 + 1.4 + 0.825 + 0.016933 = 13.0641 W; with 1.461 A, 12.3708 W.
2. **R28-TRI-03** (stall input, l.693–703): "1.56 A ... (1.46 A plus the 0.1 A AUX allowance)", "4.389 V", "5.881014 / 4.388745 V"
   → "1.561 A (camera 1 A, radio 0.3 A, GPS 0.15 A and 11 mA quiescent, 1.461 A, plus the 0.1 A AUX allowance ...)",
   "4.388 V", "5.880831 / 4.388491 V since D-R28-01, R28-TRI-03; D-R27-01's code used 1.56 A, without the 11 mA, and gave
   5.881014 / 4.388745 V". Evidence: `loaded_pack` re-solved: 1.561 A → 5.8808312 / 4.3884907 V; the regenerated budget lines
   91–92 equal these. 7.4 V figure still rounds to 5.881 V.
3. **R28-TRI-03** (GAP-1 budget SHA, l.493): `ecc45417…` (round 27) → `4267634220f4…` (round 28 fix pass, D-R28-01, the two
   loaded-pack lines only), with `ecc45417…` moved into the history chain. **Root to bind** (see top).
4. **R28-TRI-04** (capacitor bullet, l.609–612): "four on PORT_4V8 (C406, C407, C411, C421, plus C410 and C420 ...)" → "five on
   PORT_4V8 (C406, C407, C411, C421, C445, plus the 100 nF C410, C420 and C444 ...)"; added that the C21397 line's other two,
   C82 and C461, are covered elsewhere. Evidence: board PORT_4V8 = {C406, C407, C410, C411, C420, C421, C444, C445, ...};
   BOM C21397 lists 13 refs including C445, C82, C461.
5. **R28-TRI-06** (Round-5 PB1, l.957–959): "PB1 is a TT_a pin with a 4.0 V limit (reviewer)" → "a TT_u pin (DS12110 Rev 8
   Table 9 p70; corrected from 'TT_a' in round 28, R28-TRI-06) with a 4.0 V limit (Rev 8 Table 119 p212, TT_xx pins)".
   Evidence: Table 9 p70, pin 35 PB1 I/O TT_u; Table 119 TT_xx 4.0 V; pin_table row 35.

### Root-routed items (coordinator message)
6. **Status line** (l.13): "Round 27 ... so rounds 28 and 29 review it" → round 27 sentence closed; "Round 28 found 1 Major
   and 8 Minor real errors on `a0ec075e…` (R28-TRI-01 … -09, none on the board copper), and its fix pass (D-R28-01 onward)
   leaves the board unchanged, so rounds 29 and 30 review it". Also: "where a section below is marked historical it
   describes hardware that was removed" → "... records an earlier board or round, or hardware since removed ...; the current
   figure is given there or in the current section it names" (several historical sections describe parts still fitted,
   e.g. R92, R166); "The round 19 amendments" → "The round 24 and round 19 amendments".
7. **Port lead** (l.102–107): "PORT_4V8 rises about 44 ms or more before 3V3" → "can rise tens of ms before 3V3 (Calculation /
   Inference, not measured: U11's 470 nF soft-start slews VLOGIC at about 166–196 V/s, SLVSEA3F Table 9-1 p13 scaled from
   100 nF / 1 µF; U2 starts at 3.3–3.7 V with a 4 ms soft-start, DS41326 p5, so 3V3 regulates about 21–26 ms into the slew,
   after U11's settling time; the earlier figure was VLOGIC's whole slew to 7.4 V (round 20), not a lower bound)". Evidence:
   C85 470 nF on LOGIC_SS; Table 9-1 780–880 V/s at 100 nF, 88–92 V/s at 1 µF; DS41326 p5 VIN UVLO rising 3.30–3.70 V,
   tSS 4 ms; round20_mcu.md: "VLOGIC takes about 44 ms to reach 7.4 V"; audit lane B row 9. The same correction in the
   upstream-coordination note (l.686–687).
8. **§2.5 labels (EN timing, fire budget):**
   - l.20 (D402 row): "... turn-on 30–130 ms and a turn-off corner of 4.80 V (Calculation)" → "(Calculation / Inference: the
     timing figures use C87's 0.72 × minimum, whose ≤ 6 % X7R DC-bias part is an Inference, C87 row below, and the 5.71 V
     four-stall point is GAP-1's fire budget, Calc / Inference; the 4.80 V corner is Calculation only)"; "worst-corner limit
     7.50 ms" + "Calculation / Inference on the same C87 minimum".
   - l.34 (C87 row): "EN thresholds (Calculation):" → "(Calculation; the ranges and worst cases below use C's 0.72 × floor,
     which carries the DC-bias Inference at the end of this row, so they are Calculation / Inference)".
   - l.488–491 (GAP-1 fire currents): added "Calculation / Inference: Q124's inherited hot factor is an Inference, and the
     40 mΩ FET ceiling, R134 hot corner, harness, ground, contact and converter-load figures are unmeasured allowances"
     (`r10_parts.py`: "inherited hot-factor inference").

### Audit findings (false or stale current statements)
9. **Intro** (l.4–5): "reproduces nine local lands, nine small VRML envelopes" → "ten ... ten ... (nine of each until D-R18-08
   added the SRP5030T land)". Evidence: `r10_parts.py` FOOTPRINTS 10, MODELS 10; nine at `dcbb6c8`; `M3_SRP5030TA` added
   in `acba196` (D-R18-08).
10. **U4 row** (l.32): "Figure 5 p9 and Table 2 pp10–11" → "Table 2 p11". Evidence: DS15034 Rev 1: p10 is §3.1 / Figure 6;
    Table 2 (pins 1–14 and both notes) is entirely on p11; p12 starts §4.
11. **J440 row** (l.36): "4.08 / 4.18 mm from their pins centre to centre (3.16 / 3.19 mm pad edge to pad edge)" → "on
    `a0ec075e…` each clamp pad is 3.864 / 3.964 mm of track from its pin, pad centre to pad centre (check_r10 K-ports;
    4.075 / 4.175 mm before D-R24-17 chamfered the bend), and 3.157 / 3.194 mm away in a straight line, centre to centre (the
    '3.16 / 3.19 mm pad edge to pad edge' of earlier records is this straight-line distance)". Evidence: `port_clamps` on the
    board: J440.3→D440.1 3.864, J440.4→D441.1 3.964 mm; tracks 2.59 + 0.509 + 0.765 / 0.865 mm; pad centres J440.3 (7.4,18.0)
    to D440.1 (4.45,19.125) = 3.157 mm, J440.4 (7.4,21.5) to D441.1 (4.45,22.725) = 3.194 mm (pad edge to pad edge is about
    1.9 mm). Same row: "Per board the terminal code is now 4 and the ESD code 8" → "At round 19 ... was 4 ... and 8 ...;
    the ESD code is 9 per board since D402" (BOM C535146 qty 9).
12. **R16 MEMS** (l.52): added "R16 figures, which a round 28 re-sample on `a0ec075e…` matches within 0.001 mm" (re-sample:
    IMU_CS 0.760 + 0.0921, SPI1_MISO 0.325, IMU_INT1 0.325, 3V3A 0.325 mm).
13. **Always-on ports** (l.90–93): J440 named as on PORT_4V8 with its R470 / R471, D440 / D441, C444 / C445 cell; l.98: "(Rev 8
    Table 119 pp. 212–213 ..." → "... and Table 120 p. 213" (zero positive injection is Table 120); l.108–109: "no
    self-powered GPS/radio" → "GPS/radio/AUX module".
14. **Round 12** (l.127): added "(Rev 8 Table 159 p249)" beside the Rev 11 citation (verified 3 mA test point, PC13–PC15).
15. **Shared port fault budget** (l.135, 149–152): "A GPS/radio cable short can collapse both modules" → "A cable short on any
    PORT_4V8 port (GPS, radio or AUX) can collapse all three modules"; "bench a short on either port" → "on each PORT_4V8
    port"; added AUX's 4.641504 V (`aux_module_min_V`).
16. **microSD** (l.200–202): "GPS/radio/card remain powered" → "the GPS/radio/AUX ports and the card"; case named (d) with
    0.561 A (budget note).
17. **Screw terminals** (l.204–213, 235, 243): "J400 uses green 2-position" → "J1 and J400 use" (BOM C466970 J1, J400);
    "J9/J410/J420" + "(and J440 since round 19)"; "All 23 contacts" → "All 27 contacts (23 before J440, D-R19-14)"
    (2+2+2+4×4+5 = 27); port convention and copper-loop allowance include AUX (`aux_module_min_V` uses 0.2 Ω).
18. **Round-9 labels** (l.251–252): "`value_overrides` expands 21 retained R9 Value labels" → "expanded 21 ... at round 9; it now
    holds 19, the rows below (C87 left it in round 19, D-R19-10, and C122 was removed)". Evidence: `circuit.json`
    `value_overrides` has 19 keys, exactly the table's refs.
19. **Round-15** (l.274–276, 288–293, 306, 318): "All seven exact terminal variants have 23 contacts" + "(on `7866d6b8…`; since
    J440 ... eight terminals carry 27)"; added the current S-8 figures: minimum 1.021 mm (PYRO1_OUT via (11.63, 55.10) to
    In1 / In2 GND), J121.1 1.050 mm to GND and 1.061 mm to the In2 3V3 fill, gate / enable barrels' minimum 1.050 mm, 12
    barrels + 2 inner rings (read-only `s8` at a 1.3 mm search); process-corner arithmetic + "0.881 mm at the current 1.021 mm
    minimum"; first-article "inspect all 23 contacts" → "all 27 contacts (23 at round 15)"; VCAP + "(Rev 8 Table 124 p216 gives
    the same)".
20. **AUD/GAP header** (l.348–351): new first paragraph: the AUD-1 / AUD-3 placements are 2026-10-28 history; current C92
    B(32.35,52.5) 0° (pads (31.65,52.5) / (33.05,52.5)) and C120 B(17.1,72.525) −90° (pad 1 (17.1,71.75), pad 2 ACT_GATE
    (17.1,73.3)) from the board and `r10_place.tsv`. C120 paragraph marked the same.
21. **AUD-3** (l.375–376, 404, 410–412): settled |Vgs| ≥ 4.7444 V and the 31.89 ms + "Calculation / Inference" (Q122's
    conduction within the 0.1 V drain allowance at its 1.92–2.19 V drive is an Inference); "The load-switch off RC is ≤129.03
    ms" → "≤ 64.52 ms through R119∥R120 (50 kΩ × 1.02 × 1.265 µF; ≤ 129.03 ms with either resistor open ...)". Evidence:
    ACT_DRV = {Q122.3, R121.2} only, so C120 discharges through R119 ∥ R120 (both 100 kΩ, ACT_GATE–ACT_FET_S).
22. **AUD-4/5/7/9** (l.415–416): "Keep TP80–83/TP120–122" → "TP80–83, TP120 and TP122 (TP121 went in round 19, D-R19-03)";
    "R412/R422/R432 use 10 kΩ ..." → "R432 uses ... (R412/R422 went with the always-on ports)". Board: TP121, R412, R422 absent.
23. **Passive cold check** (l.426–427): "New C120/R120 maximum off tau≈129 ms makes 1 s about 7.75 tau" → "about 64.5 ms through
    R119∥R120 (about 129 ms with either open), so 1 s is about 15.5 tau (7.75 tau with one open)".
24. **Cold-screen Vf = 0.30 V figures** (l.437): "(a 3.0 V source; Calculation)" → "Calculation / Inference, as both Vf values
    are assumed BAT54 drops" (matches audit lane B's ORDERING label).
25. **GAP-5** (l.510–511, 526–527, 535): added "Rev 8 Table 146 p238 gives the same 29.4–33.6 kHz through Tj 125 °C and 29.76 kHz
    through 110 °C"; total ≤ 34.8531 ms + "(Calculation / Inference: the 1.5 ms tail and the 0.2 / 0.5 ms terms are unmeasured
    allocations)"; "about 1.23× chart margin" + "(Inference, from the chart read)".
26. **GAP-2** (l.542–562): "two local vias at (20.3,79.1)/(21.1,79.1), joined by a 0.8 mm-long 0.4 mm B.Cu track" → "(20.3,79.1)
    and (21.1,78.25), each on its own 0.7 mm B.Cu leg (0.85 / 0.8 mm) off a 1.0 mm run from C82.1 (D-R24-17; until then ...
    (21.1,79.1), ... 0.4 mm link)"; added that the OUT routes, re-summed from the board's tracks, are unchanged (1.8 + 0.778 +
    1.0 = 3.578 mm; 1.8 + 3.536 + 1.25 = 6.586 mm) while the GND routes and areas are the earlier measurements, not re-measured
    since D-R24-17; "gives" → "gave"; the round 19 hand-back clause re-worded as dated.
27. **Supply contract** (l.568): "U402 is the only TPS2553 on the current board" → "the only port switch ... (the board's other
    TPS2553DBVR is U10, the USB current limiter, with EN tied to VBUS and R85 66.5 kΩ)". Board: U10 = TPS2553DBVR C55266.
28. **TPS2553 bullet** (l.587–595): "electrical table p7" → "recommended operating conditions p5, electrical table pp6–7 (§6.5),
    current-limit equations pp16–17" (Rev G: RON 135 mΩ and IEN p6, deglitch p7, equations pp16–17); "EN has a 100 kΩ
    pull-down; FAULT has a logic-side pull-up" → "U402's EN ... (R431) and its FAULT ... (R432 to 3V3)"; "Each switch (U402 and
    U10)". Board: R431 100 kΩ CAM_PWR_EN–GND, R432 10 kΩ CAM_FAULT_N–3V3, U10 EN = VBUS.
29. **Capacitor bullet**: "Nominal 44 µF is not a stability proof" → "Nominal capacitance is not a stability proof" (no rail now
    has 44 µF nominal except the buck input; the figure was ambiguous).
30. **Budgets** (l.620–622): "A 5.3 V setting cannot cover the full 1 A camera load after aged GH contacts" → "could not ... (the
    GH-era reason for the setting; the current DB125 allocation is in ...)"; l.640: added the AUX minimum 4.641504 V; l.646–647:
    "not permission to exceed GH's 1 A/contact rating" → "a connector, contact or harness rating (the GH-era version ... J9 is
    now a DB125 screw terminal)"; l.658–659: "GPS and radio share PORT_4V8 ... collapse both ports" → "GPS, radio and AUX ...
    all three ports"; l.666: "Calculated (`parts_budget.json`)" → "(the then `parts_budget.json`)" in the labelled history.
31. **Upstream coordination** (l.679–691): labelled history (per-port switch budget, before the microSD and AUX loads); "is about
    2.92 A ... asserted" → past tense; added "Current (Calc / Inference): ... prospective U9 input is now 4.420 A
    (`u9_prospective_input_without_buck_limiting_A`), above U9's 3.946188 A minimum, so the coordination rests on the
    AP63201's 3.1 A peak limit: 3.743861 A, 0.202327 A below"; "port enables default off and firmware sequences their
    startup" → history, with "only the camera's U402 enable defaults off".
32. **Stall input** (l.702): "Shed all port enables" + "(only the camera's U402 enable remains; GPS, radio and AUX are always on)".
33. **Back-feed** (l.746–749, 755–759, 764–765, 771–772): "Radio USB-powered/board-off ... transitions must be measured; the
    reverse transient can charge the shared rail before cutoff" → camera / U402 for the reverse transient; GPS, radio and AUX
    have no switch and back-feed PORT_4V8 directly; "A self-powered or USB-powered GPS (J410), radio (J420 ...) or camera (J9)
    on an enabled port therefore back-feeds GPS_4V8 / RADIO_4V8 → PORT_4V8 ..." → camera behind an enabled U402 back-feeds
    CAM_5V → PORT_5V3; GPS / radio / AUX need no enable and back-feed PORT_4V8 → U401 → PORT_5V3 (GPS_4V8 / RADIO_4V8 are
    gone); "Firmware drops UART OEs and port ENs on a VLOGIC sag" → "drops the camera's EN / OE (the only port enable and OE
    left) and parks PD8 / PB13 / PC6 analog on a VLOGIC sag (binding note)"; "extends to J410 and J420" → "J410, J420 and J440".
34. **Camera loop, DB125 version** (l.802): added "The solve was on `632a9ad3…`; on `a0ec075e…` CAM_5V's copper is unchanged, and
    PORT_5V3 has three more vias with their links, one chamfered corner and a 0.1 mm shorter L400.2 feed (D-R18-08's land) with
    the same In2 fill area, not re-solved". Evidence: track / via / zone comparison against `632a9ad3…` (CAM_5V identical;
    PORT_5V3 +vias (24.9,14.9), (26.45,11.95), (42.75,61.8), the (25.65,14.1) corner chamfered, L400.2 feed x 26.55 → 26.45;
    In2 fill 218.6153 mm² both).
35. **Ride-through** (l.816–839): "firmware shedding of the ports cannot act in time (TPS2553 turn-off up to 3 ms, SLVS841G §6.5 p7)"
    → "Firmware can shed only the camera, and not in time (U402's turn-off is up to 3 ms, SLVS841G §6.5 p6); the GPS, radio and
    AUX ports have no switch" (toff is on p6); the table now gives the budget's current values with the microSD and AUX loads
    and adds case (d): (a) 7.43–7.49 / 7.05–7.11 and 11.61–11.71 / 11.01–11.10 ms, (b) 2.73–4.28 / 2.59–4.06 and 4.27–6.69 /
    4.05–6.34 ms, (c) 0.49–0.57 / 0.46–0.54 and 0.76–0.89 / 0.73–0.84 ms at 9.86–10.82 W ports, (d) 1.37–1.49 / 1.30–1.41 and
    2.15–2.33 / 2.04–2.21 ms (`battery_break_ride_through_ms`); the R3 values are kept as a labelled history sentence; (a) / (b)
    need physically absent ports. The old table (8.7 / 8.2 ... 0.55–0.65 ms) was pre-microSD / pre-AUX while citing the budget
    key (R28-POWER obs 1, R25 obs 9).
36. **OQ-5** (l.841–853): "VON 6.49–6.94 V" → "6.48–6.94 V (6.66 V typical)" (6.4845 V); "(0.29–0.53 ms at the lowest VOFF)"
    → "(0.25 / 0.40 ms for 300.8 / 470 µF at the lowest VOFF and the highest case (c) load)"; "at least 4.6 / 7.2 ms with shedding
    and 2.3 / 3.7 ms without" → "3.8 / 6.0 ms ... 1.6 / 2.5 ms" (`option_oq5_*` 3.8426 / 6.0041 / 1.5722 / 2.4565 ms), R3's
    figures kept as history; labelled "hypothetical, Calc / Inference with typical EN currents"; R5 / R6 named as DS41326's.
37. **Local lands** (l.862): DB125 "Envelope 7.3×7.7×8.9 includes general tolerance" → "The generated envelope is D-R11-01's
    maximum-tolerance union ...: 8.32×8.10×8.90 mm for two positions (15.52 / 19.02 mm long for four / five); the first R10
    envelope, 7.3×7.7×8.9 (body plus general tolerance), is superseded" (`r10_parts.MODELS`). GH2 / GH4 rows labelled history
    (no GH footprint on the board; the GH4 row said "Used for camera/GPS/radio"). C84 row: "Keep fitted BOM/CPL identity /
    polarity" → "on the owner BOM (since the round 18 fix pass it is not in the JLC BOM / CPL)".
38. **EasyEDA note** (l.873–878): "API calls ... returned HTTP 403 in this session. Their pad-number/orientation check remains open
    ... Final BOM/CPL gate must ... check ... GH mechanical tabs" → labelled history; current: `tools/jlc_corrections.json` has a
    status-OK pad match for all 82 placed codes (81 BOM + C84; L400 via proxy C189932) and `r10_fab.sh` runs
    `jlc_orient --verify-cpl`; no GH parts.
39. **CPL items** (l.889–897): "U411 / U12 / U421 (... top, rotation −90 ...) ... confirm pin 1 ... on all three" → "U12 (... now on
    the bottom at B(31.6,39.8), rotation 0, CPL Bottom 0; U411 / U421 went ...) ... confirm pin 1 in JLC's bottom-side preview";
    C84: "+ on pad 1 (VLOGIC at (38.5, 77.25)) and − on pad 2 (GND at (38.5, 70.75)); ... confirm + on the VLOGIC pad in the
    preview" → current pads (27.5, 81.75) / (27.5, 75.25), old ones marked historical, and no JLC preview exists for a hand-fitted
    part: check polarity at the hand fit and on first boards.
40. **Servo return** (l.910): 0.6144 A + "(Calculation on those unmeasured ≤1 mΩ / ≥50 mΩ allocations, so Inference until the
    measurements below)".
41. **Round-5** (l.937–940, 963): TP89 item: "TP89 is the BAT_ILIM node" → "TP89 was the BAT_ILIM test pad; it was removed with
    AUD-4/5/7/9 ..., and the rule now applies to any probe on BAT_ILIM itself (U9 pin 9 / R84.1 ...)" (TP89 absent; ORDERING
    probes R84.1); VBUS_SENSE: "(VIH as reviewer's figure, DS12110 row not re-read)" → "(the reviewer's figure, which DS12110
    Rev 8 Table 157 p246 confirms)".
42. **USB-only** (l.971–972): added "with C86 / C98, 1 µF each on USB_LIMITED between U10's output and U11's IN1 (516.1 µF in all),
    it is 2.426 mC and 5.35–6.98 ms" (USB_LIMITED = {C86, C98, R87, TP82, U10.6, U11.7}).
43. **Round-6 / -7 / -8 headings, R92 / R166 histories**: a first sentence each naming the current figure (USB-only
    calculation, AUD-3 gate network, GAP-5 IWDG, R430 = C2999509, the port rules, `hotplug.md` / `hotplug_results.json`,
    R92 at F(31,86.7), R166 at F(23.5,86.3)); Round-6 notes its PORT_5V3 band reading was not re-measured.

## 3. Statements verified as correct (by section; count of independent checks)

- **Intro (5):** `circuit.json`, `pin_table.tsv`, `parts.json` (retired, `superseded_by`) exist; `r10_parts.py` writes
  `parts_budget.json` and never edits a board.
- **Review status (9):** 46 × 90 mm (edge bbox 46.05 × 90.05 with line width); rounds 22 / 23 = 22 / 55 Minor; round 24 board and
  fix-pass IDs and hashes; round 25 / 26 / 27 counts; round 26's two J440 GND vias and C10 / C11 / R164 / R173 / R164-via moves
  (D-R26-01 / -02 / -04).
- **Round 24 amendment (31):** D402 code, maker part, B(4.45,65.9) rot 90, under J400's body between its pins (64.1 / 67.6);
  4.114 mm tap (K-ports); 0.7 mm to GND via (5.15,65.575); BAT_SW_RETURN = {J400.2, R165.1, D402.1}; IR ≤ 50 nA at 15 V,
  VTrig 21 V (Rev 1.3 Table 3 p6); J400.2 = 5.216 V; 5.69 mV formula; 22.7 mV EN-leakage shift (a quarter); 14.3 mV on C87;
  nominal turn-on 87.7 / 55.5 / 44.7 ms and drop-out 18.9 / 32.8 / 41.1 ms re-derived from SLVSFC9C p9 (1.20 / 1.09 V); the
  D-R24-19 worst figures as reproduced by the round 28 power lens; $0.2306 × 9; BOM 81 / 45 Extended / 36 Basic / 206 placed;
  $85.26 and $0.85 over at 12:44:13Z; $85.60 / $85.36 history; U4 9 / 2 / 5, U9 30 / −81 / 7, C535146 196 / 189 / 45; C88,
  R402, R403, R92, TP88 positions and C88 on U9.5's axis (x 18.25).
- **Round 19 table and notes (52):** U4 code / land / pose; DS15034 2.5 × 3.0 × 0.83 mm and −40…+105 °C (p1), p187 pads
  14 × 0.475 × 0.25 at 0.5, Figure 5 p9, pins 10–11 unconnected on the board and "VDDIO or leave unconnected" (Table 2),
  WHO_AM_I 73h (p66, both parts), Table 150 p93 codes (both parts), Table 3 p12 ranges; CPL Bottom 180 and theta 180 /
  residual 0.04 (jlc_corrections); $14.3422; DS14623 p9 / p187; C87 code, value, F(18.7232,81.8768), R81 F(18.8482,80.0),
  2.032 / 2.063 V (≤ 2.06 V as rounded), EN/UVLO 6.5 V (SLVSFC9C p7), 8 %; C19 / C20 C23630; C123 code, F(18.22,71.85),
  ACT_EN–GND, 667 Ω, Ciss 630 pF (AO3400A Rev 3.1 p2), 7.09 µs; J440 cell codes and nets, D440 / D441 positions, USART6
  PC6 / PC7 (U1.63 / 64), USART3 PD8 / PD9 AF7 (Table 13 p94), FT_h (Table 9 p75), 8 terminals / 27 contacts, Ø1.30 / Ø1.90;
  C84 footprint without F.Paste; TP121 absent and ACT_GATE = {R119.1, R120.2, C120.2, ...}; 3.904 mg/LSB at code 010 on all
  three IMUs (DS15034 / DS14623 Table 3 p12 ±128 g, DS14764 Table 3 p12 ±80 g, Table 138 p81); LS120 −20…+70, LED1 −30…+85,
  LED2 −40…+85 °C.
- **R16 MEMS (6):** body rectangle; four net lengths re-sampled; 0.20 / 0.25 mm widths.
- **R17 record (4):** three 0.8 ratios; ORDERING 8.1.1 anchor resolves.
- **Programming / U5 (5):** PA2 = SERVO3 and USART2_TX loader pin (pin_table); 3.0 / 2.9 mm gaps; U5 on B.Cu.
- **Always-on ports (20):** 16 removed refs absent; J410 / J420 / J440 pin 1 on PORT_4V8; R440 / R441 / R450 / R451 nets; pin
  types (PD8 / PD9 FT_h p75, PC6 / PC7 FT_h pp78–79, PB12 / PB13 FT_u p74); AF tables pp90–94; Table 119 p212 notes 3–4
  p213; Table 122 note 3 p215; Table 157 note 7 p247.
- **Camera switch, harness, Round 12 (9):** U402, U12, U13 present; camera EN / OE / FAULT on U1.41 / .39 / .42 only;
  5.031682 V; R162 1 kΩ 1 % 0805, R163 10 kΩ; 3.3 / 3.363636 / 0.306 mA.
- **Shared port fault budget (16):** TPS7A91 1.5–1.9 A (p5) and ≈1.45 A foldback (p18); 2.911 / 3.160498 A; 3.1 A (DS41326
  p5); 3.743861 A re-summed; OVLO corner 10.176 V; 3.147 / 3.083 mA; IOVLKG ±0.1 µA (p9); 3.946188 / 4.856999 A; 0.202327 A;
  3.96–4.84 A at 750 Ω (p9), eq 7 p32; R84 RT0603BRD07750RL; 4.601504 / 4.631504 V.
- **microSD (24):** code, no CD; pin and shell pad table (generator); shell pads GND; 15.05 mm arithmetic; −9.70…+6.00 mm
  model; SPI3 PC10 / PC11 / PC12 AF6 on U1.78 / 79 / 80, CS PD0 U1.81; card pinout from the nets; R460–R464 10 kΩ to 3V3 on
  CS / CMD / DAT0 / DAT1 / DAT2; C460 100 nF, C461 22 µF; no clock pull; PC11 loader output (SPI3_MISO); 0.776–0.825 /
  0.116–0.124 W.
- **Screw terminals (20):** codes per ref (BOM); J121 black; contact x positions; envelope table and +4.00 mm (generator);
  0.20 mm courtyard; 0.48 mm at the 16 mm pitch (J410 / J420 / J9 at y 15.5 / 31.5 / 47.5); JLCEDA residuals and next-best
  7.425 / 9.899 / 11.362 mm (jlc_corrections); J122 pins 1–4 SERVO1–4_OUT, 5 GND; J400 pins; port and camera pin conventions.
- **Round-9 labels (8):** seven table rows (values, codes, makers) against the BOM; 19 override keys.
- **Round-15 (13):** 1.30 / 1.90 / 3.50 / 0.30 mm; 0.140 / 0.9625 / 0.910 mm arithmetic; VCAP1 = U1.48 / C19, VCAP2 = U1.73 /
  C20; 1.98–2.42, 1.76–2.64, 1.683–2.783, 2.97–3.63 µF; Rev 8 Table 124 p216 (2.2 µF ±20 %, ESR < 100 mΩ).
- **AUD / GAP (71):** C92 code, rocket:C0603 shared with C23 / C28, 0.8 × 0.9 pads at ±0.7; 2.211046 µF; TPS709 1.5 µF; AONR21357
  −30 V / ±25 V / 12.3 mΩ / Qg(10 V) 70 nC; 17.22 mΩ; 4.7444 / 5.1916 V; 0.706 W / 0.0141 J; 8.95 W / 2.13 A; land geometry
  (generator); C120 code, footprint shared with C86 / C97 / C98, 1.265 µF, 10.7525 / 31.89 ms, 0.587 µF, 0.239 V; AUD-4/5/7/9
  removed refs absent, PC13 NC, R432 / R150–R153 codes; 64 / 72 mW; divider refs and values (R173 / R129, R132 / R175 5.1 kΩ;
  R130 / R178, R133 / R180 2 kΩ; C127 / C129); removed chain and PB0 NC; table values (budget); 96.2 / 96.1 / 141.5 mV;
  6.4103 / 4.72 / 10.0 mV; 0.911 mV; 9.11 µs; 3.342171 V; J-Tek seven figures (sheet); 1.125 A; solve formula; 2.02909 Ω;
  path lengths, widths, entries and copper (budget); fire currents (budget); budget board hash; IWDG 960 cycles, 30 /
  28.571–32.653 ms; 25 < 28.571 ms; 1087.344 Ω; 278.3 nF; 1109.091 Ω; 0.67820 ms; AON7524 22 nC; 0.73920 ms; 34.8531 ms;
  Bourns 61.204 / 44.134 W (budget), 35.7975 W, 0.71595 / 1.28871 J, 36.345 / 35.851 W; U9 / C82 / D9 / C126 poses; OUT routes;
  via geometry.
- **Supply contract (30):** U400 code, EN tied to VIN (U400.2 = RAW_PROTECTED); U401 / U402 codes; DS41326 (VIN 3.8–32 V p4,
  PWM-only AP63201 p16, 500 kHz, VFB 792–808 mV p5, IPEAK 2.5–3.1 A p5, pins p2, §13 bootstrap p14, 125 / 68 mΩ typical p5);
  TPS7A91 (±1 % 5 mA–1 A, IFB ±100 nA, 200 mV at 1 A, 6.5 V, cover 100 mV, pins vs U401's nets incl. EN = IN, PG open,
  SS_CTRL GND, NR/SS C408 10 nF, 4218903/C pp34–35); 5.63 mA bleeder; TPS2553 (2.5–6.5 V p5, 135 mΩ p6, deglitch 3–11 / 2–7 ms
  and 3–7 ms p7, pins p4, Rev F → G history p27); SRP5030T-6R8M (6.8 µH ±20 %, 76.2 mΩ, 4 A, 4.3 A, 20 % drop); ripple
  0.74–0.76 A; FOJAN ±100 ppm/°C (0603).
- **Budgets (24):** R400 / R404 / R401 and R402 / R403 values; 4.792 V; table rows (budget); 11 ms deglitch (p7); R430 C2999509
  and 1.041–1.249 A; SIMULATION.md item 20; current 3.657 / 3.627 A (budget); 4.420 A; GAP-3 0.490 W, 109.2–123.9 / 124.2–138.9
  °C, 112.3 °C/W, pad 11 1.2 × 2.0 at (27.6,13.6), vias 0.5 / 0.3 at (27.3,13.6) / (27.9,13.6), 62.5 °C/W (p4), §7.1.4 vias
  (p23), 89 °C/W (p4, p12).
- **Back-feed and ESD (22):** AUD-8 refs present / absent; TXU0202 5.5 V vs 5.546 V; R431 / R102 pull-downs; IREV ≤ 1 µA at
  25 °C, IEN ±0.5 µA, FAULT ≤ 1 µA (p6–7); ≥ 0.70 A; R122 / R123 nets (ACT_EN_MCU, ACT_EN); ESD103 ±15 V and 20 / 36 / 48 V
  (Table 5 p6); D400 … D441 and D402 codes; SCES942A 2500 V HBM; R100 / R101 1 kΩ into U12; the six direct paths and pins;
  97 mΩ; LR900 0.209 A and channels 12–25; TPS7A91 states no reverse behaviour (text search).
- **Ride-through and OQ-5 (12):** IRCB 0.2 / 1 / 2 A (SLVSEA3F §7.5 p8); 16.93 mW; 3.8 V (p4); VOFF 5.7265 / 6.0115 / 6.2965 V,
  VON max 6.9405 V; 0.13 mA; DS41326 p10 R5 / R6 naming.
- **Local lands, CPL (14):** DB125 pads; TPS7A91 land and 84 % paste; C84 pads and 3.0 mm gap; C84 −55…+105 °C, ±20 %, endurance;
  300.8 µF, 37.5 mΩ; model sizes for TPS7A91, C84, AONR, microSD, GH2; L400 pose and proxy residual 0.05; U12 correction 180 /
  0.147; C84 correction 0 / 0.045.
- **Servo, mass (3):** 0.6144 A; 2.133 A; `masses.json` exists.
- **Round-5 and USB (14):** R82 2 MΩ / R83 280 kΩ; 0.1228, 12.2, 2.44, 52.9 V; D8 SMBJ12CA; OVLO 0.5–1.5 V (p8) and 6.5 V (p7);
  ILM "do not leave floating" (p6); 258 / 22 µA (DS41326 p5, p10); R60 / R61 / C60, PA6 FT_a (p69), 0.764 V; R104 / R105 / C94;
  0.146–0.190 mA; PC8 U1.65, R9 / R110; 2.20 / 2.31 / 4.62 V; VBAT on 3V3 (U1.6); 347.7–453.0 mA; 514.1 µF on VLOGIC
  (C84, C6, C7, C99); 2.416 mC; 5.33–6.95 ms.
- **History sections:** read as records; no current claim left in them without a pointer.

## 4. Siblings in other files (not edited; for root to route)

| Statement | Files | Correct value |
|---|---|---|
| J440 clamps "4.08 / 4.18 mm centre to centre (3.16 / 3.19 mm pad edge to pad edge)" | **docs/M3_R10.md:132** (current board table); docs/R10_VALIDATION.md:1756 and :2735 (R20-RTE-05 records); R10_DECISIONS.md:3563 (D-R21-07: "3.157 / 3.194 pad edge to pad edge") | On `a0ec075e…`: 3.864 / 3.964 mm of track, pad centre to pad centre (K-ports; 4.075 / 4.175 mm before D-R24-17); 3.157 / 3.194 mm is the straight-line centre-to-centre distance, not pad edge to pad edge |
| DS15034 "Table 2 pp10–11" | docs/R10_VALIDATION.md:2688 | Table 2 is on p11 |
| USB attach inventory "514.1 µF, 2.416 mC, 5.33–6.95 ms" | docs/M3_R10.md:731; docs/R10_VALIDATION.md:2654 and :3088 | VLOGIC 514.1 µF; with C86 / C98 on USB_LIMITED 516.1 µF, 2.426 mC, 5.35–6.98 ms (0.4 %) |
| "PORT_4V8 rises about 44 ms or more before 3V3" | docs/M3_R10.md:1179, docs/REQUIREMENTS.md:64 (docs lane); m3_design/r10_sch_check.py:342 → binding note (CAD lane); as routed by audit lane B | "can rise tens of ms" (Calculation / Inference) |
| TRI-03 / TRI-06 siblings | STATUS.md:17, docs/R10_VALIDATION.md:2243, :1915 | Already in the docs lane's hand-back |

Historical records with the old figures, no action: R10_DECISIONS.md:995 and :1140 (TP120–122 kept, AUD-5 record),
`audit_preflight.md:14` (R412 / R422 / R432), R10_DECISIONS.md:547 (R3 ride-through), docs/R10_VALIDATION.md:1612 (round 18
via positions), docs/R10_VALIDATION.md:1463 / 1476 / 1550 and docs/M3_R10.md:1311 (23 contacts, 1.102501576 mm on older
boards). No current sibling of: nine lands, 12.370807 W, "four on PORT_4V8", "only TPS2553", "GH's 1 A/contact", 2.92 A,
GPS_4V8 / RADIO_4V8 back-feed, "J410 and J420" prohibition, the ride-through / OQ-5 figures, "SLVS841G §6.5 p7", the
U411 / U12 / U421 CPL item, C84's (38.5, 77.25), the 129 ms off tau, "Nominal 44 µF", the DB125 7.3 × 7.7 × 8.9 envelope.

## 5. Not verified here (coverage limits)

- Rev 11 citations of DS12110 (Tables 109 / 110 / 114 / 136 / 149) and SLVS841F (Rev F) pages: no cached copy; they stay
  labelled with their revision. Where Rev 8 / Rev G holds the same content, the Rev 8 / Rev G page is now cited beside them.
- External pages and raster drawings: Molex 472192001 page and drawing, DORABO T0-1, MS5611 p15 Fig 18, JST eGH, HGLRC and
  LR900 manual, AN2606 Rev 70, SD Physical Layer v9.10, Bourns CRM chart, Samsung NRND status, LCSC / JLC dated lookups.
- No DC copper re-solve (camera loop, GAP-2 GND paths) and no re-run of the hot-plug model or the EN chatter model; the D-R24-19
  worst-case EN figures rest on the round 28 power lens's reproduction plus my nominal re-derivation.
- No physical test of anything.
