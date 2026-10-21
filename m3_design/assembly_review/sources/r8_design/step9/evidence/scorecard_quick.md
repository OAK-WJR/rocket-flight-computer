# Scorecard: (survey output folder)

Simplicity index vs baseline (./tools/scorecard_r7.json): **14.4** (100 = baseline, lower = simpler)

| Metric | Board | Baseline | Ratio |
|---|---:|---:|---:|
| C1_route_gated_category_instances | 3 | 74 | 0.041 |
| C2_route_info_instances | 93 | 252 | 0.369 |
| C3_route_allowlisted | 3 | 45 | 0.067 |
| C4_route_leftovers | 0 | 29 | 0.0 |
| C5_route_failures | 0 | 0 |  |
| C6_agents3_rule_instances | 1 | 9 | 0.111 |
| S1_signal_track_mm | 1500.1 | 3354.7 | 0.447 |
| S2_total_track_mm | 2098.1 | 4428.3 | 0.474 |
| S3_signal_vias | 56 | 218 | 0.257 |
| S4_signal_layer_change_vias | 55 | 217 | 0.253 |
| S5_power_vias_non_gnd | 125 | 114 | 1.096 |
| S6_detour_weighted | 1.18 | 1.396 | 0.845 |
| S7_detour_excess_mm | 295.5 | 1080.8 | 0.273 |
| S8_nets_ratio_over_1_6 | 4 | 23 | 0.174 |
| S9_nets_ratio_over_2 | 2 | 12 | 0.167 |
| S10_bends_per_10mm_signal | 1.56 | 1.932 | 0.807 |
| S10b_signal_bends_total | 234 | 648 | 0.361 |
| S11_bends_per_two_pad_signal_route | 1.62 | 5.05 | 0.321 |
| S12_critical_layer_changes | 25 | 73 | 0.342 |
| S13_critical_layer_changes_no_gnd_via | 0 | 8 | 0.0 |
| S14_critical_weighted_ratio | 1.183 | 1.314 | 0.9 |
| S15_in2_signal_track_mm | 3.4 | 901.0 | 0.004 |
| S16_in1_track_mm | 0 | 0 |  |
| S17_route_mst_total_mm | 1642.9 | 2727.3 | 0.602 |
| S18_track_segments | 797 | 1724 | 0.462 |
| R1_ref_r6_unreferenced_mm | 4.7 | 60.3 | 0.078 |
| R2_ref_r6_referenced_share | 0.8882 | 0.7302 | 1.216 |
| R3_ref_ext_unreferenced_mm | 4.7 | 115.9 | 0.041 |
| R4_ref_ext_crossings | 28 | 116 | 0.241 |
| R5_cref_r6_samples | 47769 | 95979 | 0.498 |
| R6_cref_r6_unreferenced | 5525 | 26789 | 0.206 |
| R6b_cref_r6_unreferenced_share | 0.1157 | 0.2791 | 0.415 |
| R7_cref_ext_samples | 103308 | 220968 | 0.468 |
| R8_cref_ext_unreferenced | 6283 | 52285 | 0.12 |
| P1_in1_gnd_coverage | 0.9065 | 0.8796 | 1.031 |
| P2_in1_gnd_islands | 1 | 1 | 1.0 |
| P3_in1_large_voids | 15 | 18 | 0.833 |
| P3b_in1_slots | 1 | 16 | 0.062 |
| P4_in2_regions | 5 | 8 | 0.625 |
| P5_in2_nets | 4 | 5 | 0.8 |
| P6_in2_perimeter_mm | 1788.7 | 1580.9 | 1.131 |
| P7_outer_gnd_islands_le1_via | 1 | 32 | 0.031 |
| P8_gnd_stitch_per_cm2 | 8.14 | 7.22 | 1.127 |
| P9_gnd_dist_p95_mm | 4.48 | 6.12 | 0.732 |
| P10_gnd_dist_max_mm | 9.65 | 13.78 | 0.7 |
| P11_outer_gnd_pour_dist_p95_mm | 2.9 | 5.09 | 0.57 |
| D_bat_mohm | None | 3.03 |  |
| D_bat_neck_dT_C | None | 30.2 |  |
| D_bat_neck_mm | None | 3.82 |  |
| D_fet_mohm | None | 1.16 |  |
| D_fet_neck_dT_C | None | 44.2 |  |
| D_fet_neck_mm | None | 2.65 |  |
| D_min_neck_fraction_of_20C_width | None | 0.502 |  |
| D_raw_mohm | None | 3.71 |  |
| D_raw_neck_dT_C | None | 38.3 |  |
| D_raw_neck_mm | None | 3.0 |  |
| Q1_top_utilisation | 0.401 | 0.422 | 0.95 |
| Q2_bottom_utilisation | 0.182 | 0.163 | 1.117 |
| Q3_grid_util_max | 0.805 | 0.967 | 0.832 |

R8 targets (r8_plan.md section 2; soft report): 17 met, 11 missed, 3 not measured

| Target | Board | Goal | Met | Note |
|---|---:|---|---|---|
| C1_route_gated_category_instances | 3 | <= 1 | no | hard gate: 0 but A8 |
| C2_route_info_instances | 93 | <= 80 | no |  |
| C3_route_allowlisted | 3 | <= 1 | no | hard gate: A8 only |
| C4_route_leftovers | 0 | == 0 | yes | hard gate |
| C5_route_failures | 0 | == 0 | yes | hard gate |
| C6_agents3_rule_instances | 1 | <= 1 | yes | hard gate: A8 only |
| S1_signal_track_mm | 1500.1 | <= 2300 | yes |  |
| S4_signal_layer_change_vias | 55 | <= 75 | yes |  |
| S6_detour_weighted | 1.18 | <= 1.18 | yes |  |
| S7_detour_excess_mm | 295.5 | <= 350 | yes |  |
| S8_nets_ratio_over_1_6 | 4 | == 0 | no | except keep-out-forced nets |
| S9_nets_ratio_over_2 | 2 | == 0 | no | except keep-out-forced nets |
| S10b_signal_bends_total | 234 | <= 400 | yes |  |
| S12_critical_layer_changes | 25 | <= 32 | yes |  |
| S15_in2_signal_track_mm | 3.4 | == 0 | no | hard gate (check_r8 D20) |
| S16_in1_track_mm | 0 | == 0 | yes | hard gate (check_r8 D20) |
| S17_route_mst_total_mm | 1642.9 | <= 1850 | yes |  |
| P1_in1_gnd_coverage | 0.9065 | >= 0.9 | yes |  |
| P3b_in1_slots | 1 | <= 4 | yes |  |
| P4_in2_regions | 5 | <= 5 | yes |  |
| P6_in2_perimeter_mm | 1788.7 | <= 900 | no |  |
| P7_outer_gnd_islands_le1_via | 1 | == 0 | no |  |
| P9_gnd_dist_p95_mm | 4.48 | <= 3.5 | no |  |
| P10_gnd_dist_max_mm | 9.65 | <= 7 | no |  |
| R1_ref_r6_unreferenced_mm | 4.7 | <= 5 | yes |  |
| R3_ref_ext_unreferenced_mm | 4.7 | <= 15 | yes |  |
| R6b_cref_r6_unreferenced_share | 0.1157 | <= 0.08 | no | critical_reference |
| D_raw_neck_dT_C | None | <= 20 | - | D12: >= 5.3 mm outer / 5.6 mm inner |
| D_bat_neck_dT_C | None | <= 20 | - | D12: >= 5.3 mm outer / 5.6 mm inner |
| D_fet_neck_dT_C | None | <= 30 | - | D12: >= 3.71 mm on B.Cu |
| index_vs_baseline | 14.4 | <= 35 | yes | simplicity index |
