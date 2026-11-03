# Scorecard: <survey folder>

Board `990c8040c5b8457bd2bd1717ed3e5c2725f32c1dda1cd7f826a0c2b458d28b18` (fix pass 2): `NO_GATE=1 NO_DC=1 tools/run_survey.sh` with the 0.05 mm `tools/run_dc.sh` outputs (fix2_dc_*.txt) added for the D rows.

Simplicity index vs baseline (tools/scorecard_r7.json): **15.3** (100 = baseline, lower = simpler)

| Metric | Board | Baseline | Ratio |
|---|---:|---:|---:|
| C1_route_gated_category_instances | 3 | 74 | 0.041 |
| C2_route_info_instances | 90 | 252 | 0.357 |
| C3_route_allowlisted | 3 | 45 | 0.067 |
| C4_route_leftovers | 0 | 29 | 0.0 |
| C5_route_failures | 0 | 0 |  |
| C6_agents3_rule_instances | 1 | 9 | 0.111 |
| S1_signal_track_mm | 1499.6 | 3354.7 | 0.447 |
| S2_total_track_mm | 2090.8 | 4428.3 | 0.472 |
| S3_signal_vias | 56 | 218 | 0.257 |
| S4_signal_layer_change_vias | 55 | 217 | 0.253 |
| S5_power_vias_non_gnd | 125 | 114 | 1.096 |
| S6_detour_weighted | 1.177 | 1.396 | 0.843 |
| S7_detour_excess_mm | 289.4 | 1080.8 | 0.268 |
| S8_nets_ratio_over_1_6 | 4 | 23 | 0.174 |
| S9_nets_ratio_over_2 | 4 | 12 | 0.333 |
| S10_bends_per_10mm_signal | 1.54 | 1.932 | 0.797 |
| S10b_signal_bends_total | 231 | 648 | 0.356 |
| S11_bends_per_two_pad_signal_route | 1.62 | 5.05 | 0.321 |
| S12_critical_layer_changes | 25 | 73 | 0.342 |
| S13_critical_layer_changes_no_gnd_via | 0 | 8 | 0.0 |
| S14_critical_weighted_ratio | 1.182 | 1.314 | 0.9 |
| S15_in2_signal_track_mm | 3.4 | 901.0 | 0.004 |
| S16_in1_track_mm | 0 | 0 |  |
| S17_route_mst_total_mm | 1638.9 | 2727.3 | 0.601 |
| S18_track_segments | 795 | 1724 | 0.461 |
| R1_ref_r6_unreferenced_mm | 2.9 | 60.3 | 0.048 |
| R2_ref_r6_referenced_share | 0.8934 | 0.7302 | 1.224 |
| R3_ref_ext_unreferenced_mm | 2.9 | 115.9 | 0.025 |
| R4_ref_ext_crossings | 28 | 116 | 0.241 |
| R5_cref_r6_samples | 46845 | 95979 | 0.488 |
| R6_cref_r6_unreferenced | 5186 | 26789 | 0.194 |
| R6b_cref_r6_unreferenced_share | 0.1107 | 0.2791 | 0.397 |
| R7_cref_ext_samples | 102384 | 220968 | 0.463 |
| R8_cref_ext_unreferenced | 5944 | 52285 | 0.114 |
| P1_in1_gnd_coverage | 0.905 | 0.8796 | 1.029 |
| P2_in1_gnd_islands | 1 | 1 | 1.0 |
| P3_in1_large_voids | 16 | 18 | 0.889 |
| P3b_in1_slots | 4 | 16 | 0.25 |
| P4_in2_regions | 5 | 8 | 0.625 |
| P5_in2_nets | 4 | 5 | 0.8 |
| P6_in2_perimeter_mm | 1752.5 | 1580.9 | 1.109 |
| P7_outer_gnd_islands_le1_via | 1 | 32 | 0.031 |
| P8_gnd_stitch_per_cm2 | 8.15 | 7.22 | 1.129 |
| P9_gnd_dist_p95_mm | 4.47 | 6.12 | 0.73 |
| P10_gnd_dist_max_mm | 9.65 | 13.78 | 0.7 |
| P11_outer_gnd_pour_dist_p95_mm | 2.9 | 5.09 | 0.57 |
| D_bat_mohm | 0.45 | 3.03 | 0.149 |
| D_bat_neck_dT_C | 14.5 | 30.2 | 0.48 |
| D_bat_neck_mm | 6.99 | 3.82 | 1.83 |
| D_fet_mohm | 0.18 | 1.16 | 0.155 |
| D_fet_neck_dT_C | 21.5 | 44.2 | 0.486 |
| D_fet_neck_mm | 4.97 | 2.65 | 1.875 |
| D_min_neck_fraction_of_20C_width | 0.941 | 0.502 | 1.875 |
| D_raw_mohm | 1.45 | 3.71 | 0.391 |
| D_raw_neck_dT_C | 17.5 | 38.3 | 0.457 |
| D_raw_neck_mm | 5.94 | 3.0 | 1.98 |
| Q1_top_utilisation | 0.401 | 0.422 | 0.95 |
| Q2_bottom_utilisation | 0.182 | 0.163 | 1.117 |
| Q3_grid_util_max | 0.805 | 0.967 | 0.832 |

R8 targets (r8_plan.md section 2; soft report): 20 met, 11 missed, 0 not measured

| Target | Board | Goal | Met | Note |
|---|---:|---|---|---|
| C1_route_gated_category_instances | 3 | <= 1 | no | hard gate: 0 but A8 |
| C2_route_info_instances | 90 | <= 80 | no |  |
| C3_route_allowlisted | 3 | <= 1 | no | hard gate: A8 only |
| C4_route_leftovers | 0 | == 0 | yes | hard gate |
| C5_route_failures | 0 | == 0 | yes | hard gate |
| C6_agents3_rule_instances | 1 | <= 1 | yes | hard gate: A8 only |
| S1_signal_track_mm | 1499.6 | <= 2300 | yes |  |
| S4_signal_layer_change_vias | 55 | <= 75 | yes |  |
| S6_detour_weighted | 1.177 | <= 1.18 | yes |  |
| S7_detour_excess_mm | 289.4 | <= 350 | yes |  |
| S8_nets_ratio_over_1_6 | 4 | == 0 | no | except keep-out-forced nets |
| S9_nets_ratio_over_2 | 4 | == 0 | no | except keep-out-forced nets |
| S10b_signal_bends_total | 231 | <= 400 | yes |  |
| S12_critical_layer_changes | 25 | <= 32 | yes |  |
| S15_in2_signal_track_mm | 3.4 | == 0 | no | hard gate (check_r8 D20) |
| S16_in1_track_mm | 0 | == 0 | yes | hard gate (check_r8 D20) |
| S17_route_mst_total_mm | 1638.9 | <= 1850 | yes |  |
| P1_in1_gnd_coverage | 0.905 | >= 0.9 | yes |  |
| P3b_in1_slots | 4 | <= 4 | yes |  |
| P4_in2_regions | 5 | <= 5 | yes |  |
| P6_in2_perimeter_mm | 1752.5 | <= 900 | no |  |
| P7_outer_gnd_islands_le1_via | 1 | == 0 | no |  |
| P9_gnd_dist_p95_mm | 4.47 | <= 3.5 | no |  |
| P10_gnd_dist_max_mm | 9.65 | <= 7 | no |  |
| R1_ref_r6_unreferenced_mm | 2.9 | <= 5 | yes |  |
| R3_ref_ext_unreferenced_mm | 2.9 | <= 15 | yes |  |
| R6b_cref_r6_unreferenced_share | 0.1107 | <= 0.08 | no | critical_reference |
| D_raw_neck_dT_C | 17.5 | <= 20 | yes | D12: >= 5.3 mm outer / 5.6 mm inner |
| D_bat_neck_dT_C | 14.5 | <= 20 | yes | D12: >= 5.3 mm outer / 5.6 mm inner |
| D_fet_neck_dT_C | 21.5 | <= 30 | yes | D12: >= 3.71 mm on B.Cu |
| index_vs_baseline | 15.3 | <= 35 | yes | simplicity index |
