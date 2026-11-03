# R10 round 26: gate lens

- Target: commit `3d8e845`, board `92c3ad59174afe1ffe206f6384c8cd9a8962e09647ccd6a8c418b95b5312056f` (before and after).
- Reviewer: Claude.
- Probe directory: `.supervisor/r26_gate/` (seed scripts `seed_ops.py`, `seed_ra.py`, `run_seed.sh`; seeded copies and checker output).

## Totals

0 Critical, 0 Major, 0 Minor. No realistic seed passed the gate.

## Fix verification

| Change | Seed and checker output | Verdict |
|---|---|---|
| D-R25-01 chatter obligation | a1, "under 7 ms" → "under 8 ms" without regenerating: K-binding FAIL ("saved firmware_obligations differs"). a2, the same edit regenerated: K-binding OK, `test_r23_binding_note_rules_and_pin_table` FAIL | confirmed |
| D-R25-01 battery_entry note | b1, generator edited without regenerating, and b3, the sheet hand-edited: `r10_sch_check` FAIL ("nonreproducible generated artifact: battery_entry.kicad_sch"). b2, regenerated: the replay passes and `test_r21_sheet_notes` FAILS | confirmed |
| D-R25-02 rule 8 hold-up | f1, the old 0.157–0.182 ms put back: K-binding FAILS before regeneration and test_r23 after it. Recomputed: 0.1034–0.1643 / 0.2906–0.4303 ms, fractions 0.223–0.305 | confirmed |
| D-R25-03 OVLO corner | d1, VOV(R) 1.224 V without regenerating: `r10_parts --check` exits 1 ("stale: parts_budget.json"). d2, regenerated: passes. 10.1764 V, 3.6565 / 3.6268 A and 3.743861 A reproduced | confirmed |
| D-R24-20 M-8 | R92 +0.03 mm: M-8 FAILS at 2.495 mm | confirmed |
| D-R24-17 right_angle | Plain 90° corners on LED_YEL (14.4,43.0) and RAW_ACT (22.8,63.875): FAIL. The overshoot and stop-short variants (0.003–0.1 mm) fail through dead_copper / overlap_only_joint | confirmed |
| D-R24-02 / -08 / -03 second vias | ACT_GATE (15.4,72.85), LOGIC_SOURCE_ST (30.45,51.4) and BOOT0 (14.2,46.0) each deleted with their stubs: K-power single-via FAIL, and route_check parallel_via FAIL | confirmed |

The representative seeds were run on full project clones and refilled. Each one fails its rule:
- S-1: R173.1 on RAW_ACT;
- S-2: C128.1 on BAT_IN;
- S-3: R123 at 20k;
- S-4 / K-actuators: R134 at 1R;
- S-5: R165 at 47k;
- S-6: D410.1 on PYRO1_OUT;
- S-7: J122.5 on RAW_PROTECTED;
- S-8: three hazard-net vias moved 0.4 mm and refilled (0.626–0.777 mm);
- S-9: PYRO1_IGN / RAW_ACT at 0.45 mm;
- K-power: BAT_IN at 0.9 mm, the C88 feed at 0.5 mm.

A refill-only control passes every one of these rules. The full `test_r10_check.py` and `test_route_check.py` were run on the base copy.

## Observations (not counted)

1. **Unpinned figures in the generated text.** These edits, regenerated, pass every gate (text-pin class, as R25-GATE observations 2–6):
   - 9.59 → 10.59 ms in the chatter obligation;
   - turn-on 88/56/45 → 98/56/45 ms in the battery_entry note;
   - 300.8 → 470 µF in rule 8.
2. **Budget-derived figures are hand-typed.** Seed e1 adds 0.1 A of port load and regenerates the budget, and every check passes. The real all-ports-on hold-up becomes 0.441–0.510 ms, but AGENTS still says 0.46–0.54 ms and rule 8 is unchanged. No stated rule asks the gate to tie the text to `parts_budget.json`.
3. **U9.6's branch to D9.1 is not gated.** It is RAW_PROTECTED's 0.7 mm run to the B340A clamp, and narrowed to 0.6 mm it passes K-power. It is not on U9 OUT's path to the vias, D9 carries only transients, and no floor is stated for it.
4. **S-6 reads its clearance from the `.kicad_pro`.** A board copied alone reads 0.2 mm and shows a false S-6 hit. Only copies are affected: check.sh always runs with the project.
5. **right_angle catches near-miss corners.** Overshoot and stop-short corners fail through dead_copper / overlap_only_joint on both critical and non-critical nets.

## Limits

- The full `r10_build.sh` was not run on a seeded generator; its regeneration commands were run one at a time instead.
- DRC was not run on the board seeds.
- The D-R25-01 chatter limits were not re-simulated.
