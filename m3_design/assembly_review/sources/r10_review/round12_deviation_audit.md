# R12 deviation inventory preparation audit (historical snapshot)

Status: **PREPARATION**. Full build B, the two-build 42-file comparison, reviewed commit and fresh full rounds 13/14 are pending. No clean pair, owner acceptance, quote/order or physical/firmware qualification is claimed. R9 remains accepted; AGENTS section 2 is unchanged.

`r10_final_deviations.json` SHA-256: `e1a05bc3040acfca6cd1d5a1a5063522e34f7c45f5aaf064ac59856280c41a86`.

Coverage checks passed in the preparation script:

- 46 historical groups and 229 prior rows retain exact source pointers and current applicability/reason; every row names an existing current topic and its concrete closure.
- 110 unique source D IDs match exactly, including suffixes and D-R12-01/02/03; repeated verification addenda do not inflate the count. D-R3-12 explicitly carries the corrected current evidence.
- 22 owner mandates/amendments and all 12 consolidated R12 Minor groups have explicit dispositions and concrete closure requirements.
- Nine noncritical leftover locations appear once at `#/routing_inventory/noncritical_leftovers_once`, with only category/net/layer/x/y. Other records link to that inventory.
- All local JSON pointers resolve; the closed-card envelope pointer resolves to `round12_fix_native.json#/full_gate/fit/mated_envelopes`. No host-absolute path or dangling `#/evidence` pointer remains.

Original native observations stay bound to `0ad0135c…` and their hashed sources. The exact comparison in `round12_fix_native.json` preserves original parts/poses/pad lands/nets/GND tracks/vias; it does not relabel old generated bindings, fills, simulations or execution results. Newly executed `7355ae1a…` metrics/return/native results have separate provenance. This author read receipts only and did not read or measure the mutable PCB, run a build/gate/CLI, use GUI/git or edit any existing canonical record.

The finished-board native route receipt records 141 actual instances: 110 ordinary informational, 22 AUD-10 inside-pad and nine hygiene leftovers; no supplemental bump candidate remains, with 56 windows searched. Historical routing-lens 140 meant 139 instances plus one supplemental bump and is not the final denominator. New C98 stitch and BAT_ENABLE whole-chain annotations remain explicit M2 deviations; both simplest two-segment BAT_ENABLE alternatives fail the recorded native 0.15 mm clearance screen. No optimality claim is made.

The inventory retains L400's possible 0.15 mm uncovered heel; PC14 resistor-only 3.3/3.363636 mA bounds with dynamics unmeasured; actual new C98 return 7.345584 mm plus separately focused 0.025 mm-grid 7.270584 mm; ordinary-stitch 0.300 mm offset/0.050 mm overlap and 0.125 mm hole-to-mask/paste versus 0.100 mm floor; five Fab labels 0.4/0.06 mm with focused minimum glyph gap 0.027960 mm and vector-zoom limit. R432's 0.020 mm shape-boundary depth remains distinct from the narrower two-AABB-endpoint diagnostic.

The 2026-10-30T06:11:29Z public supplier snapshot is hashed `5ea50a4d9d3a56ba0035e4d5cd410207578f88a1c4f8d170dfb67b0ec49fc12f`: $82.65 placed/feeder, $84.99 with minimum purchases versus $84.41, a $0.58 minimum-cost excess. R430 stock 17 < 3610 minimum; U4 stock 0 < 5; U9 minimum 7 for five needed. Complete process/panel/quote/supply acceptance and an ordering-time refresh remain pending. Raw snapshot is a relative scratch reference; durable summarized figures and input hashes are also retained in the canonical R12 parts report.

Root must replace preparation completion fields only after actual full-build comparison and fresh full-round receipts, then reconcile final prose, commit/hash binding and owner items. Physical and firmware obligations remain unverified regardless of CAD gates.

## Root integration completion addendum

The preparation status and hash above identify the author's earlier snapshot.
Root has now completed both full native builds/check0 and42-file byte equality;
`round12_fix_validation.json` is authoritative. The current inventory SHA-256
is `3050403875aea523513165bbb2c3699a6315800433595290ede86edd1bcb99e3`.
Its source catalog and all12R12 dispositions are refreshed. Fresh full
rounds13/14 and owner acceptance remain pending. No physical/firmware or
factory qualification is inferred; the PCB is unchanged after buildB.
