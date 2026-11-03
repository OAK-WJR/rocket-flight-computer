# R10 round 36 — routing lens (Claude)

Target commit `c3c4249`, board `a0ec075e…` (SHA-256 verified identical before and after).

**Totals: Critical 0 / Major 0 / Minor 0.** No real errors found.

## Findings
None.

## Fix verification
- R34-TRI-01 was a parts_qualification text fix, not a routing change; the board is unchanged (SHA confirmed). n/a.

## Checks executed
- shasum -a 256 of the board before and after (a0ec075e...)
- route_check.py --profile r10 on a probe copy, with and without --bumps-all: 0 failing, 0 allowlisted, 0 stale, 5 unrecorded noncritical leftovers (BAT_OVLO short_segment, BUZZ_DRV / BAT_FAULT_N / I2C1_SDA tiny_jog, USB_ILIM detour); 28 critical / 49 all-net bump windows; category counts pad_end_offcentre 70, segment_inside_pad 27 (match R10_VALIDATION 57->70, 22->27)
- Independent pcbnew script: 1059 segments, 0 arcs, 0 off-angle headings, 0 zero-length; every two-end 90-degree junction tested for inner-corner pad/via coverage (33, all covered); acute pairs checked against pad polygons (4, all inside); dangling ends (6, all Ts on same-net segment bodies)
- Independent GND-partner-via distance for every layer-changing non-GND via, compared against AGENTS 3 critical list and critical_reference.R10_SLOW_RETURN_NETS
- Plated-pad layer survey (pad_layer_changes scope) against the R10_VALIDATION statement
- J440 clamp runs: AUX_TX_WIRE B.Cu 3.864 mm, AUX_RX_WIRE 3.964 mm; centre-to-centre 3.157 / 3.194 mm; partner vias (7.4,16.5)/(7.4,20.0) 1.500 mm from pin centres, 0.300 mm ring gap to own pad, 0.800 mm to neighbouring pin: all match R10_VALIDATION
- U401 OUT T (29.75,12.85): 0.075 mm inside R402.1 land, 0.325 mm inside-pad segment: matches
- kicad-cli 10.0.7 pcb drc --severity-all on the probe copy

## Observations (not counted)
- VBUS B.Cu: the branch to (11.3,28.45) joins the (9.95,30)-(11.35,30) trunk at a T at (11.3,30.0), 0.05 mm before the trunk's 45-degree vertex; a T is not a bend (M2), connectivity is a centre-line anchor, not overlap-only; tidiness preference, not a rule violation.
- BUZZ_G B.Cu: T at (20.5,58.7), 0.02 mm before the vertex (20.5,58.72); same reasoning as VBUS (a BUZZ_G T was already a round 24 observation).
- CAM_RX_WIRE / CAM_TX_WIRE / RADIO_TX_WIRE / RADIO_RX_WIRE B.Cu: 90-degree T taps at x 35.75 from their straight port runs; Ts are not bends under D-R24-17.
- 33 two-end 90-degree junctions at pads or vias: the inner corner N + h_b u_a + h_a u_b lies inside the same-net pad or via copper in every case (independent script); 0 open-copper 90-degree bends.
- 4 acute (45-degree) branch pairs at C80.2, J9.1, U10.4, C98.1: the inner-edge apex lies inside the pad polygon in all four, so the wedge does not open outside pad copper (route_check acute_angle rule).
- All non-GND layer-change vias with no GND via within 1.5 mm are on non-critical nets, power rails or AUD-2 slow nets (ACT_GATE, BAT_ENABLE, BAT_SW_SOURCE, PYRO1_CONT, CAM_PWR_EN, CAM_UART_OE).
- Plated pads with tracks on two layers: J440.3 / J440.4 (partner GND vias at 1.500 mm), J400.2 (AUD-2 slow), J1.1 (power); J121, J122, J410, J420, J9 one layer each, as R10_VALIDATION states.
- ACT_GATE short_layer_hop (11.14,71.7)-(11.74,72.3), 0.849 mm: the D-R24-02 parallel second barrel, not a needless hop.
- r10_final_deviations.json routing_inventory remains bound to 632a9ad3; already ruled an observation in round 24 triage.
- kicad-cli DRC on the probe copy: 0 copper / clearance violations, 0 unconnected; 199 lib_footprint_issues only because the copy dir does not resolve the project library (environment artefact).

## Coverage limits
- Pour/reference-plane geometry relied on route_check and check_r10 categories rather than an independent fill analysis; check_r10 not re-run (no fit report built).
- Noncritical pad-entry tidiness reviewed by category counts only; earlier triage rulings on those were not re-litigated.
- IPC-2152 current sizing not re-derived.
