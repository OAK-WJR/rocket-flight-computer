# R7 fix pass 6, agent F7: running log

Start board SHA-256 1ffc2585cbbb2a49623a5010b2792500849f06989cf43e48fb3e56068cddf9df (copy: <scratchpad>/fx6/base.kicad_pcb).
Scope: items 1-8 of the F7 brief (P6-RQ-01, P6-REG-01/02, P6-RG-01/02, P6-DOCS-01, records, J31 value).

## Log
- Read pass-6 reports, verdicts, F6 handoff.
- Dev pipeline fx6/dev.sh (fx4/hyg post-hygiene board -> polish -> post) reproduces 1ffc2585 exactly. pre6 = polish --stop rf_relief.
- route_check: added compound tiny_jog (k>=2 middle), chain_detour and pour_net_hop on poured nets (hygiene, gated), measured
  figures for them (6th entry element), alt_audit for chain_detour, path_defects compound check. Base board: 18 chain_detour,
  5 pour_net_hop, 1 compound jog (LOGIC_SS).
- r7_polish fix-6 stages added: qspi6, sw6, logic_ss6, servo_fault6, v3v3_6, raw_act6 (SPLIT_OK for RAW_ACT), ties6. Stage-level run OK.
- Item 8 done: r7_sch.py J31 value 'RADIO ANT SMA'; r7_sch.py --netlist reran on repo (only telemetry Value + netlist value changed).
- BAT_IN_F: no legal via spot inside BAT_IN_F reaching In2 BAT_IN except (8.75,35.65); TP89 1.0 mm keep-out and radio B.Cu block the rest.
  Variants v1..v5 being DC-solved (fx6/dcbat.out).
- BAT_IN DC variants (C89.1/C95.1 -> U9.5, mOhm): base 10.35/7.37; v1 (8.75,35.65) 8.66/5.75; v5 zone+(9.7,35.5) 7.78/5.84;
  v3 zone+(9.7,31.75)+(9.7,35.5) 7.05/5.60; v4 v3+(8.75,35.65) 6.88/5.30. Chose v3 (bat_in_f6).
- ties6 extended: GND J3.1->C28.2 (freed by the R85 redraw; first candidate broke the 0.25 mm NPTH copper-to-hole rule at J3's
  peg -> alt_audit and polish draw() now check NPTH holes; test added). pour_trim expected 23 -> 22.
- SW allowlist A3-A5 deleted; 13 new allowlist entries (9 chain_detour, 5 pour_net_hop ... minus J3.1/C28 fixed) with measured figures.
- dev d4 (pre6 -> polish from qspi6 -> post): DRC 0 / unconnected 0 / parity 1 (J31 value: board predates new netlist; full build fixes),
  route_check OK (0 failing, 43 allowlisted, 30 leftovers), actuators OK, check_r7 only duplicate-UUID artefacts of --start.
- Full r7_build.sh x2 from R6: board 4673c0a0f9fd290af694d6ca5a97e99b3b225466882ba5c6e57a9ad856b96ebd both times; check.sh exit 0
  (DRC/unconnected/parity/ERC 0; routing 0 failing, 43 allowlisted, 30 leftovers; contracts OK).
- Tests: 172 tool tests OK (route_check 45), quality_audit 21 x2; test_r5_repair known error. Fab regenerated (BOM line 36 only),
  verify-cpl OK, stock/cost refreshed live ($105.98, U4 short). Renders regenerated. critical_reference 0/0; DC table in handoff.
- Handoff written: fix6_F7_handoff.md. DONE.
