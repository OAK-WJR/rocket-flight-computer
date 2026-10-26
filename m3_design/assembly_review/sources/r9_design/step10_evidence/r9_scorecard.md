# m3_design/assembly_review/m3.kicad_pcb sha256 4f841a0e44ebb1829ad7996dfe6320ed527fce1fdb1e5ff11658e0705b44ac14 (tools/run_r9_survey.sh, 0.05 mm DC and the gate, R9 review pass 1 fix pass)
# R9 scorecard: <scratch>/ev/survey

index_r8 (repo 12-row index, R8 = 100): **95.2**; index_r9 (+ clean-sheet rows): **83.8**

## hard: 16 met, 0 missed, 1 not measured

| Row | Board | Goal | Met | Note |
|---|---:|---|---|---|
| G_gate_exit | 0 | == 0 | yes | R9 check.sh: DRC incl. pyro A-H / A2, ERC, parity, check_r9, route_check r9, fit |
| D_raw_neck_dT_C | 12.6 | <= 20 | yes | D12 |
| D_bat_neck_dT_C | 12.1 | <= 20 | yes | D12 |
| D_fet_neck_dT_C | 20.5 | <= 30 | yes | D12 |
| LC1_local_clearance_overrides | 0 | == 0 | yes | R8 29 (J124.2, J122 RAW pads, 24 test pads) |
| X2d_pyro_nearest_battery_live_mm | None | >= 2.5 | - | R8 1.089 (ACT_FET_S pour to J124.1, B.Cu) |
| X9_rf_sep_nearest_part_mm | 6.04 | >= 5.94 | yes | R8 5.94 (R306 to U1) |
| X9c_inner_power_pyro_mm | 4.953 | >= 2.65 | yes | R8 2.65 |
| S15_in2_signal_track_mm | 0 | == 0 | yes | R8 3.4 (rigid CH1 link): no exemption in R9 |
| S16_in1_track_mm | 0 | == 0 | yes | R8 0 |
| F1_fit_worst_top_margin_mm | 0.028 | >= 0.0 | yes | P2 (fit_check) |
| M2_f1_hz | 256.6 | >= 209 | yes | plate model, jacks only, pinned, D 5; R8 208.7 |
| X1b_board_width_mm | 46.0 | == 46 | yes | P1 |
| X3d_non_rf_parts_in_strip | 0 | == 0 | yes | F10 strip contents |
| S13_critical_layer_changes_no_gnd_via | 0 | == 0 | yes | AGENTS 3; R8 0 |
| F3_support_bottom_clear_mm | 4.483 | >= 3.5 | yes | P2 |
| F4_support_top_clear_mm | 5.008 | >= 3.8 | yes | P2 |

## done: 34 met, 16 missed, 3 not measured

| Row | Board | Goal | Met | Note |
|---|---:|---|---|---|
| X1_board_length_mm | 102.0 | <= 100 | no | r9_plan: plan 98 mm; R8 118 |
| X2_pyro_foreign_nets_3mm_same_layer | 0 | == 0 | yes | R8 6 |
| X2b_pyro_foreign_nets_3mm_plan | 0 | == 0 | yes | R8 7 |
| X2g_ch1_through_nets | 7 | == 0 | no | R8 6 |
| X2c_pyro_nearest_foreign_mm | None | >= 3.0 | - | R8 0.70 |
| Z1a_pyro_rule_A_margin_mm | 0.23 | >= 0.2 | yes | every Z1 margin >= max(R8, 0.2) |
| Z1b_pyro_rule_B_margin_mm | 0.32 | >= 0.2 | yes | every Z1 margin >= max(R8, 0.2) |
| Z1c_pyro_rule_C_margin_mm | 0.277 | >= 0.2 | yes | every Z1 margin >= max(R8, 0.2) |
| Z1d_pyro_rule_D_margin_mm | 0.251 | >= 0.2 | yes | every Z1 margin >= max(R8, 0.2) |
| Z1e_pyro_rule_E_margin_mm | None | >= 0.3 | - | every Z1 margin >= max(R8, 0.2) |
| Z1f_pyro_rule_F_margin_mm | None | >= 0.2 | - | every Z1 margin >= max(R8, 0.2) |
| Z1g_pyro_rule_G_margin_mm | 0.27 | >= 0.2 | yes | every Z1 margin >= max(R8, 0.2) |
| Z1h_pyro_rule_H_margin_mm | 0.225 | >= 0.2 | yes | every Z1 margin >= max(R8, 0.2) |
| Z2r9_exit_net_track_mm | 66.4 | <= 80 | yes | GATE_N + CONT + ARM1_SENSE track (whole nets: R9 has no rigid block) |
| Z4_vias_in_test_pads | 0 | == 0 | yes | R8 1 (A8) |
| C6_agents3_rule_instances | 0 | == 0 | yes | R8 1 (A8) |
| Z5_bare_pyro_gate_to_armed_live_mm | 2.354 | >= 2.0 | yes | R8 1.027 |
| Z5b_bare_gate_to_always_live_mm | 1.03 | >= 1.0 | yes | R8 0.634 |
| C1_route_gated_category_instances | 0 | == 0 | yes | empty allowlist; R8 3 |
| C3_route_allowlisted | 0 | == 0 | yes | R8 3 |
| S8_nets_ratio_over_1_6 | 2 | <= 1 | no | RADIO_TXEN only (keep-out-forced); R8 4 |
| S9_nets_ratio_over_2 | 2 | <= 1 | no | as S8; R8 4 |
| S1_signal_track_mm | 1306.9 | <= 1497.9 | yes | <= R8 |
| S6_detour_weighted | 1.152 | <= 1.174 | yes | <= R8 |
| S7_detour_excess_mm | 207.5 | <= 285.8 | yes | <= R8 |
| S10b_signal_bends_total | 260 | <= 231 | no | <= R8 |
| S12_critical_layer_changes | 18 | <= 25 | yes | <= R8 |
| S17_route_mst_total_mm | 1367.5 | <= 1638.9 | yes | <= R8 |
| S4_signal_layer_change_vias | 57 | <= 70 | yes | owner decision 4 (per-family budgets); R8 55 |
| X5_track_widths | 5 | <= 6 | yes | R8 11 (flowline graft: six widths) |
| X8c_pour_trim_areas | 0 | == 0 | yes | R8 8 |
| Y1_close_pairs_lt_0p2 | 30 | <= 10 | no | R8 27 |
| Y1b_close_pairs_at_drc_min | 14 | == 0 | no | R8 8 |
| Y2c_pad_close_at_drc_min | 11 | == 0 | no | R8 4 |
| Y6_m2_poured_hops | 0 | == 0 | yes | R8 2 |
| Y7_m2_via_steps | 1 | == 0 | no | R8 1 |
| Y5_m2_via_folds | 34 | <= 10 | no | R8 26 |
| P6_in2_perimeter_mm | 1479.4 | <= 900 | no | R8 1752.2 |
| P7_outer_gnd_islands_le1_via | 9 | == 0 | no | R8 1 |
| P9_gnd_dist_p95_mm | 3.37 | <= 3.5 | yes | R8 4.47 |
| P10_gnd_dist_max_mm | 7.32 | <= 7.0 | no | R8 9.65 |
| R6b_cref_r6_unreferenced_share | 0.1022 | <= 0.08 | no | R8 0.1107 |
| D_raw_mohm | 0.8 | <= 1.0 | yes | r9_plan; R8 1.45 |
| D_raw_neck_dT_C | 12.6 | <= 17.5 | yes | every rise <= R8 (17.5) |
| D_bat_neck_dT_C | 12.1 | <= 14.5 | yes | every rise <= R8 (14.5) |
| D_fet_neck_dT_C | 20.5 | <= 21.5 | yes | every rise <= R8 (21.4-21.5) |
| X3_rf_strip_depth_mm | 20.5 | <= 21.4 | yes | R8 21.39 |
| X3f_rfif_track_mm | 291.8 | <= 250 | no | R8 321.3 |
| R5_gcpw_z_min_ohm | 50.165 | >= 47.5 | yes | GCPW 50 +- 2.5 ohm at every sample (tools/gcpw_solve.py) |
| R5_gcpw_z_max_ohm | 50.514 | <= 52.5 | yes | GCPW 50 +- 2.5 ohm at every sample (tools/gcpw_solve.py) |
| M2_f1_hz | 256.6 | >= 241 | yes | R6 target; R8 208.7 |
| Z3_imu_lever_arm_abs_mm | 11.0 | <= 11.0 | yes | R8 13.0 |
| index_r9 | 83.8 | <= 73 | no | R8 = 100 |

## stretch: 0 met, 9 missed, 0 not measured

| Row | Board | Goal | Met | Note |
|---|---:|---|---|---|
| S4_signal_layer_change_vias | 57 | <= 55 | no | owner decision 4 stretch |
| X1_board_length_mm | 102.0 | <= 96 | no | plan_spine: 95-96 with a tighter cluster (Inference) |
| X2e_ch1_bbox_area_mm2 | 721.0 | <= 500 | no | R8 662.4 |
| Y1_close_pairs_lt_0p2 | 30 | == 0 | no |  |
| D_fet_neck_dT_C | 20.5 | <= 20 | no | all three paths inside 20 C |
| X6c_mean_segment_mm | 2.15 | >= 3.5 | no | R8 2.629 |
| Z3_imu_lever_arm_abs_mm | 11.0 | <= 5.0 | no |  |
| F1_fit_worst_top_margin_mm | 0.028 | >= 0.5 | no | R8 0.028 (J9 mated) |
| index_r9 | 83.8 | <= 50 | no |  |

## All rows

| Row | Board | Baseline |
|---|---:|---:|
| G_drc | 0 | 0 |
| G_erc | 0 | 0 |
| G_gate_exit | 0 | 0 |
| G_parity | 0 | 0 |
| G_unconnected | 0 | 0 |
| C1_route_gated_category_instances | 0 | 3 |
| C2_route_info_instances | 114 | 91 |
| C3_route_allowlisted | 0 | 3 |
| C4_route_leftovers | 0 | 0 |
| C5_route_failures | 0 | 0 |
| C6_agents3_rule_instances | 0 | 1 |
| S1_signal_track_mm | 1306.9 | 1497.9 |
| S2_total_track_mm | 1853.1 | 2087.2 |
| S3_signal_vias | 57 | 56 |
| S4_signal_layer_change_vias | 57 | 55 |
| S5_power_vias_non_gnd | 96 | 125 |
| S6_detour_weighted | 1.152 | 1.174 |
| S7_detour_excess_mm | 207.5 | 285.8 |
| S8_nets_ratio_over_1_6 | 2 | 4 |
| S9_nets_ratio_over_2 | 2 | 4 |
| S10_bends_per_10mm_signal | 1.99 | 1.542 |
| S10b_signal_bends_total | 260 | 231 |
| S11_bends_per_two_pad_signal_route | 1.7 | 1.62 |
| S12_critical_layer_changes | 18 | 25 |
| S13_critical_layer_changes_no_gnd_via | 0 | 0 |
| S14_critical_weighted_ratio | 1.114 | 1.182 |
| S15_in2_signal_track_mm | 0 | 3.4 |
| S16_in1_track_mm | 0 | 0 |
| S17_route_mst_total_mm | 1367.5 | 1638.9 |
| S18_track_segments | 862 | 794 |
| R1_ref_r6_unreferenced_mm | 0.0 | 2.9 |
| R2_ref_r6_referenced_share | 0.899 | 0.8934 |
| R3_ref_ext_unreferenced_mm | 0.0 | 2.9 |
| R4_ref_ext_crossings | 32 | 28 |
| R5_cref_r6_samples | 31359 | 46845 |
| R5_gcpw_gap_max_mm | 0.28 | 0.31 |
| R5_gcpw_gap_min_mm | 0.26 | 0.26 |
| R5_gcpw_z_max_ohm | 50.514 | 50.958 |
| R5_gcpw_z_min_ohm | 50.165 | 50.165 |
| R6_cref_r6_unreferenced | 3206 | 5186 |
| R6b_cref_r6_unreferenced_share | 0.1022 | 0.1107 |
| R7_cref_ext_samples | 83715 | 102408 |
| R8_cref_ext_unreferenced | 3931 | 5944 |
| P1_in1_gnd_coverage | 0.9095 | 0.9051 |
| P2_in1_gnd_islands | 1 | 1 |
| P3_in1_large_voids | 16 | 16 |
| P3b_in1_slots | 4 | 4 |
| P4_in2_regions | 5 | 5 |
| P5_in2_nets | 4 | 4 |
| P6_in2_perimeter_mm | 1479.4 | 1752.2 |
| P7_outer_gnd_islands_le1_via | 9 | 1 |
| P8_gnd_stitch_per_cm2 | 9.49 | 8.15 |
| P9_gnd_dist_p95_mm | 3.37 | 4.47 |
| P10_gnd_dist_max_mm | 7.32 | 9.65 |
| P11_outer_gnd_pour_dist_p95_mm | 2.85 | 2.9 |
| D_bat_mohm | 0.16 | 0.45 |
| D_bat_neck_dT_C | 12.1 | 14.5 |
| D_bat_neck_mm | 8.15 | 6.99 |
| D_fet_mohm | 0.26 | 0.18 |
| D_fet_neck_dT_C | 20.5 | 21.5 |
| D_fet_neck_mm | 5.18 | 4.97 |
| D_grid_mm | 0.05 | 0.05 |
| D_min_neck_fraction_of_20C_width | 0.981 | 0.941 |
| D_raw_mohm | 0.8 | 1.45 |
| D_raw_neck_dT_C | 12.6 | 17.5 |
| D_raw_neck_mm | 7.89 | 5.94 |
| Q1_top_utilisation | 0.481 | 0.401 |
| Q2_bottom_utilisation | 0.195 | 0.182 |
| Q3_grid_util_max | 1.0 | 0.805 |
| F1_fit_worst_top_margin_mm | 0.028 | 0.028 |
| F2_fit_worst_bottom_margin_mm | 2.366 | 2.357 |
| F3_support_bottom_clear_mm | 4.483 | 4.452 |
| F4_support_top_clear_mm | 5.008 | 5.008 |
| LC1_local_clearance_overrides | 0 | 29 |
| M2_f1_hz | 256.6 | 208.7 |
| X1_board_length_mm | 102.0 | 118.0 |
| X1b_board_width_mm | 46.0 | 46.0 |
| X1c_outline_area_mm2 | 4635.8 | 5371.8 |
| X1d_envelope_length_mm | 111.8 | 127.8 |
| X1e_aft_overhang_mm | 9.79 | 9.79 |
| X2_pyro_foreign_nets_3mm_same_layer | 0 | 6 |
| X2b_pyro_foreign_nets_3mm_plan | 0 | 7 |
| X2c_pyro_nearest_foreign_mm | None | 0.7 |
| X2d_pyro_nearest_battery_live_mm | None | 1.089 |
| X2e_ch1_bbox_area_mm2 | 721.0 | 662.4 |
| X2f_ch1_courtyard_fill | 0.458 | 0.498 |
| X2g_ch1_through_nets | 7 | 6 |
| X2h_ch1_through_items | 9 | 28 |
| X3_rf_strip_depth_mm | 20.5 | 21.39 |
| X3b_rf_strip_area_mm2 | 642.5 | 696.4 |
| X3c_rf_strip_share | 0.139 | 0.13 |
| X3d_non_rf_parts_in_strip | 0 | 0 |
| X3e_rf_track_mm | 17.5 | 18.4 |
| X3f_rfif_track_mm | 291.8 | 321.3 |
| X3g_rf_zone_depth_mm | 29.91 | 30.52 |
| X3h_rf_zone_area_mm2 | 1184.0 | 1184.9 |
| X4_parts | 249 | 249 |
| X4b_parts_per_cm2 | 5.37 | 4.64 |
| X4c_courtyard_per_outline | 0.676 | 0.584 |
| X4d_courtyard_per_outline_outside_rf | 0.64 | 0.547 |
| X4e_distinct_rotations | 4 | 4 |
| X4f_parts_off_90 | 0 | 0 |
| X5_track_widths | 5 | 11 |
| X5b_signal_track_widths | 5 | 7 |
| X5c_power_track_widths | 5 | 8 |
| X5d_gnd_track_widths | 5 | 7 |
| X5e_via_geometries | 2 | 2 |
| X6_signal_bends_per_mm | 0.199 | 0.1542 |
| X6b_all_bends_per_mm | 0.1775 | 0.1365 |
| X6c_mean_segment_mm | 2.15 | 2.629 |
| X7_vias_total | 583 | 609 |
| X7b_gnd_vias | 430 | 428 |
| X7c_non_gnd_vias | 153 | 181 |
| X8_copper_zones | 16 | 14 |
| X8b_rule_areas | 11 | 19 |
| X8c_pour_trim_areas | 0 | 8 |
| X9_rf_sep_nearest_part_mm | 6.04 | 5.94 |
| X9b_rf_sep_nearest_fast_line_mm | 5.005 | 5.075 |
| X9c_inner_power_pyro_mm | 4.953 | 2.65 |
| X9d_battery_pyro_mm | None | 1.089 |
| Y1_close_pairs_lt_0p2 | 30 | 27 |
| Y1b_close_pairs_at_drc_min | 14 | 8 |
| Y2_pad_close_lt_0p2 | 28 | 33 |
| Y2b_pad_close_foreign | 15 | 15 |
| Y2c_pad_close_at_drc_min | 11 | 4 |
| Y3_m2_chain_detours | 18 | 23 |
| Y4_m2_routes_over_1_25 | 38 | 28 |
| Y5_m2_via_folds | 34 | 26 |
| Y6_m2_poured_hops | 0 | 2 |
| Y7_m2_via_steps | 1 | 1 |
| Y8_m2_short_hops | 7 | 9 |
| Z1a_pyro_rule_A_margin_mm | 0.23 | 0.001 |
| Z1b_pyro_rule_B_margin_mm | 0.32 | 0.17 |
| Z1c_pyro_rule_C_margin_mm | 0.277 | 0.077 |
| Z1d_pyro_rule_D_margin_mm | 0.251 | 0.001 |
| Z1g_pyro_rule_G_margin_mm | 0.27 | 0.0 |
| Z1h_pyro_rule_H_margin_mm | 0.225 | 0.025 |
| Z2_pyro_exit_lanes_mm | 0 | 137.5 |
| Z2b_pyro_exit_vias | 0 | 3 |
| Z2r9_exit_net_track_mm | 66.4 | 160.3 |
| Z3_imu_lever_arm_abs_mm | 11.0 | 13.0 |
| Z4_vias_in_test_pads | 0 | 1 |
| Z5_bare_pyro_gate_to_armed_live_mm | 2.354 | 1.027 |
| Z5b_bare_gate_to_always_live_mm | 1.03 | 0.634 |
| check_r9_failing_rules | 1 | 17 |
| index_r8 | 95.2 | None |
| index_r9 | 83.8 | None |
