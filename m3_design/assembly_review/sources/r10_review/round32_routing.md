# R10 round 32 routing lens

Target `3366287`, board `a0ec075e…` (SHA-256 before and after: `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c`). Reviewer: claude. Strict real-error rule.

**Totals:** 0 Critical, 0 Major, 0 Minor. No real error found.

## Findings

None.

## Fix verification

- **R30-TRI-01 (ARM1_SENSE-to-CAM_IO_3V3 bridge figures; EN load 5.6 kOhm):** ARM1_SENSE B.Cu to U13.5 measured 0.150 mm on a0ec075e, the location the corrected text names; corrected text (2.19-2.21 V, 0.107-0.109 mA, cold pull-up) present at R10_VALIDATION:2637; '5.6 kOhm with the e-match' present (2 places). Verdict: confirmed (routing geometry); electrical figures belong to the safety lens.
- **R30-TRI-02 (LS120 not a chamber pass / fail gate):** not measured. Verdict: outside the routing lens.
- **D-R29-01 / -02:** board SHA unchanged a0ec075e before and after. Verdict: no routing change to verify.

## Observations (not counted)

1. route_check --profile r10 on a copy of a0ec075e: 0 failing, 0 allowlisted, 0 stale, 5 unrecorded noncritical leftovers (BAT_OVLO short_segment B(16.4,83.0); tiny_jog BUZZ_DRV F(20.5,51.8), BAT_FAULT_N B(28.2,47.5), I2C1_SDA B(9.97,51.5); detour USB_ILIM), 28 bump windows: matches M3_R10 'Routing evidence' and R10_VALIDATION section 6.
2. Information counts reproduce the records: pad_end_offcentre 70 and segment_inside_pad 27 (round 24's 57 -> 70 / 22 -> 27); also width_change_junction 11, extra_bends 14, u_turn 5, short_layer_hop 18, power_via_no_gnd 28, collinear_unmerged 1, passes_through_pad 1, via_on_track_in_fill 1 (review-only M2 items awaiting the owner list).
3. Independent heading audit (own script on a pcbnew dump, 1059 tracks, 309 vias): 0 arcs, 0 segments off a 45-degree multiple (0.1 deg / 2 um).
4. Independent bend audit: 395 plain 45-degree bends, 0 plain 90-degree bends; 35 two-end 90-degree bends and 4 two-end 135-degree turns sit at pads or vias, and in every one the inner corner (or acute wedge apex) lies inside the holder's copper (pcbnew effective shapes for the acute cases C89.1, D8.1, C100.2 T).
5. Independent dangling-end scan: every track end touches a same-net pad, via or track (0 free ends).
6. Critical-signal layer changes (AGENTS section 3 / M2 list incl. the R10 port UART nets, minus AUD-2's slow list): 25 vias, all with tracks on F.Cu and B.Cu, GND via 0.770 mm (QSPI_NCS (19.57,43.9)) to 1.4916 mm (PYRO1_GATE (14.4,53.3)); plus the plated pins J440.3 / J440.4 at exactly 1.500 mm (GND vias (7.4,16.5) / (7.4,20.0)); no other PTH pad of a critical net has tracks on two layers.
7. R18-RTE-02 record reproduced: of the 25 vias, 21 have In2 3V3 (17) or PORT_4V8 (4) on the B.Cu side (ring sampling 0.45-0.8 mm); HSE_IN / HSE_OUT / PYRO1_GATE over In2 GND, PYRO1_OUT in its no-net K-region void; the 21's partners are 0.77-1.43 mm (SD_SCK 1.4318 max), as the text states (the 1.4916 mm PYRO1_GATE partner is outside that set).
8. J440 partner geometry: pad dia 1.9 mm, via dia 0.5 mm: own-pin edge gap 1.5-0.95-0.25 = 0.300 mm, neighbouring pin 0.800 mm; In2 under J440.3 / .4 at 1.1-1.6 mm is 3V3; C460.1 (3V3) 16.28 / 15.86 mm: matches section 6 (16.3 / 15.9 mm).
9. J440 clamp runs (round 28 corrected): B.Cu AUX_TX_WIRE 3.8641 mm, AUX_RX_WIRE 3.9641 mm; centre to centre 3.1572 / 3.1942 mm; pad edge to pad edge 1.865 / 1.900 mm: all as M3_R10 line 140 and R10_VALIDATION section 6 state.
10. USB pair: D+ y 31.55 / D- y 29.65 (1.90 mm) over x 11.1-15.85, VBUS via (11.95,30.6) and GND via (15.6,30.5) between, diagonals 0.707 mm apart; trunks from J3 B6 / B7 14.70 / 16.45 mm (totals 16.461 / 19.286 mm less the J3 straps): as recorded.
11. Detour table recomputed with my own octilinear-MST code: 1500.8 / 1236.8 mm, 1.213x over 117 non-pour nets with at least two pads (record 116 nets, 1236.6 mm, 1.214x: a net-membership / pad-dedupe method difference of 0.2 mm); every listed row (USB_LIMITED 81.62 / 53.39 ... ACT_EN_MCU 24.36 / 20.85) and the sub-line QSPI_IO2 +3.3 / USB_DM +3.1 reproduce to 0.01 mm.
12. Owner row 8 / section 6 lists reproduce: five 0603 under-body vias (R86, R89, R91, R101, R401), the five 1210 between-pad vias (C400, C405, C411, C421, C461), BAT_FAULT_N 0.180 mm from GND via (27.9,64.25) and 0.380 mm from 3V3 via (28.1,60.0).
13. ARM1_SENSE B.Cu (29.75,45.85)-(29.75,49.4) to U13.5 0.150 mm on a0ec075e, as R10_VALIDATION:2637 states for 5516eeec (geometry unchanged but for the D-R24-17 chamfer).
14. M2 via-to-pad-opening scan (pcbnew polygons, mask margin 0): only U401.11's two GAP-3 VIPPO vias (27.3,13.6) / (27.9,13.6) open into a soldered pad, as GAP-3 permits.
15. Gate probe (not a miss): a 90-degree NRST bend seeded at B(22.54,36.2393) fails route_check right_angle; the same bend with a zero-length segment at the corner passes route_check (micro_segment counted as a noncritical leftover; right_angle's two-end test sees four ends), but after a zone refill KiCad DRC reports track_dangling on the zero-length track and tools/check.sh fails on any DRC violation, so the gate as a whole catches it. Possible hardening (not required): ignore sub-micron segments when counting the bend's ends.
16. Only inner-layer tracks: In2 3V3A 11.39 mm and USB_LIMITED 63.115 mm (the corrected 63.115 mm of R27 / R31 triage).

## Checks executed

- shasum -a 256 of the board before and after (a0ec075e both)
- tools/route_check.py --profile r10 on a copy (.supervisor/r32_routing/board.kicad_pcb)
- pcbnew dump (dump.py) and independent scans: angle, bend / inner corner (analyze.py, corner.py, wedge.py), dangling ends, partner vias (partner.py), In1 / In2 ring sampling (in2b.py), via-to-pad openings (viapad.py), detour MST, USB pair, J440 clamp geometry, under-body vias
- gate seeds: seed_plain (90-degree NRST bend) and seed_zero (same + zero-length segment) through route_check; seed_zero refilled (refill.py) and run through kicad-cli 10.0.7 pcb drc --severity-all

## Coverage limits

- High-current widths (IPC-2152, K-power) and pyro / 3V3 adjacency left to the power and safety lenses beyond a width listing
- Pad shapes in the bulk bend scan use bounding boxes; the acute cases and route_check use real shapes
- Detour net set differs from the record by one net (method), totals agree to 0.2 mm
- No physical, SI or return-current measurement
