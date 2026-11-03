# R10 round 33 — routing lens

Target commit `feed21f`, board `a0ec075e…` (SHA-256 checked before and after: unchanged). Read-only; probes in `.supervisor/r33_routing/`.

**Totals: 0 Critical / 0 Major / 0 Minor real errors.** No findings.

## Fix verification
- Round 32's corrections (R32-TRI-01 … -03) are text outside this lens; the board and routing figures are unchanged.

## Checks executed
- tools/route_check.py --profile r10 --report on a copy (exit 0)
- own pcbnew scans: heading, 90-degree bend with inner-corner coverage, plated-pad layer changes, critical via GND partner distance and In2 reference sampling, 3V3 capacitor distances, per-net octilinear MST detour table, J440 clamp runs and pad gaps, USB pair, BAT_ENABLE EN run, via size counts
- kicad-cli 10.0.7 pcb drc --severity-all on a copy with the project files

## Observations (not counted)
1. route_check --profile r10 on a probe copy: exit 0; 0 failing, 0 allowlisted, 0 stale, 181 counted instances, 28 bump windows, 5 unrecorded noncritical leftovers (BAT_OVLO short_segment B(16.4,83.0); tiny_jog BUZZ_DRV F(20.5,51.8), BAT_FAULT_N B(28.2,47.5), I2C1_SDA B(9.97,51.5); detour USB_ILIM (14.825,27.2)), as the records state.
2. Independent 90-degree bend scan (own script, every net and layer, two track ends only, no T): 33 bends at 89.5-90.5 deg, all at a pad or via whose copper covers the inner corner N + h_b u_a + h_a u_b; 0 in open copper. Agrees with right_angle 0.
3. Independent heading scan: 1059 segments, 0 arcs, 0 more than 0.1 deg off a multiple of 45 deg.
4. Board totals reproduce M3_R10 / R10_VALIDATION: 1059 segments, 309 vias (170 GND; 304 x 0.5/0.3, 4 x 0.6/0.3, 1 x 1.0/0.5), 1866.794 mm of track.
5. J440 clamp runs reproduce: AUX_TX_WIRE B.Cu 2.590 + 0.509 + 0.765 = 3.864 mm, AUX_RX_WIRE 2.590 + 0.509 + 0.865 = 3.964 mm; centre to centre 3.157 / 3.194 mm; pad edge to pad edge 1.865 / 1.900 mm (B.Cu shape clearance).
6. J440.3 / J440.4 GND partner vias (7.4,16.5) / (7.4,20.0): 1.500 mm centre to centre; 0.300 mm to their own pin's 1.9 mm pad, 0.800 mm to the neighbouring pin's, as ORDERING 8 and R10_VALIDATION state.
7. Plated-pad layer scan: only J440.3, J440.4 (critical UART), J400.2 (AUD-2 slow) and J1.1 (power) carry tracks on two layers; J121, J122, J410, J420, J9 and J3 one layer each, matching R10_VALIDATION.
8. 25 critical-signal via layer changes (non-AUD-2): GND partner 0.770-1.492 mm; In2 under them 3V3 x17, PORT_4V8 x4, GND x4 (HSE_IN, HSE_OUT, PYRO1_GATE, and PYRO1_OUT beyond its 1.1-1.3 mm S-8 void); the 21 rail vias' partners 0.770-1.432 mm, as R10_VALIDATION states.
9. Nearest 3V3-GND capacitor distances reproduce: SD_MISO 6.19, SD_SCK 5.33, SD_MOSI 5.07, SD_CS 4.84 (C17), QSPI_NCS 5.32 (C18), SPI1 5.04-5.77, CAM_MCU_RX 4.02 (C29); J440.3 / J440.4 to C460 16.28 / 15.86 mm, over In2 3V3.
10. Detour table recomputed with the r21 method (zero-length nets excluded): 116 nets, 1500.8 / 1236.6 mm, every listed row's routed / tree / excess / via figures reproduce. Below the +3.5 mm line ACT_FET_S (+3.07) and RADIO_TX_MCU (+3.07) also sit at about +3.1 mm next to USB_DM (+3.10); the sentence names two examples and does not claim completeness, so not an error.
11. USB pair figures reproduce: 1.90 mm on F.Cu, 0.707 mm on the diagonals, J3-to-U1 trunks 16.45 (DM) / 14.70 (DP) mm.
12. BAT_ENABLE: U9.1 to R81.1 through the one via (17.10,82.80) is 0.707 + 1.306 + 1.877 = 3.890 mm, as D-R21-05 states; its B.Cu hop at (19.675,66.6) (2.973 mm, 3 vias = need + 2) is the disclosed short layer hop, not gated (extra_vias passes).
13. r10_final_deviations.json noncritical_leftovers_once is still bound to 632a9ad3 and lists 6 rows (with the fixed BAT_ENABLE jog); already ruled not yet due by the round 24 triage and noted in round 31; no new fact.
14. KiCad 10.0.7 DRC (all severities, project rules beside the copy) 0 violations, 0 unconnected. A first run without the .kicad_pro / .kicad_dru beside the copy gave 304 (default rules, no library table); that run is not a board result.
15. PYRO1_CONT_MID u_turn B(16.87,59.48), path 10.575 mm, persists on a0ec075e; the detour row's '(with a u-turn, on 92c3ad59)' does not claim it was removed.

## Coverage limits
- No schematic-parity DRC run (board-only DRC).
- IPC-2152 current sizing and S-8 / adjacency left to the power and safety lenses.
- Gate seeds not re-run this round: no candidate miss was found to seed.
- Fills judged as committed (no refill).
