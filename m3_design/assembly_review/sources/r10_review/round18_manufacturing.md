# Round 18 manufacturing review (Claude)

Board SHA unchanged 632a9ad3. DRC (all severities, parity) 0/0/0. Gerbers regenerate identically; manifest hashes match; BOM/CPL consistent.

Totals: 0 Critical, 0 Major, 6 Minor.

- **R18-MFG-01** (new): R10 fab package carries no concrete panel/tab plan; stale R9 tab spans remain in ORDERING order remarks. Fix: Add a single R10 tab-plan table (edge, KiCad y/x span, Gerber coords, nearest part) from t1() windows to section 8.1, and mark section 4 line 99 as R9 history.
- **R18-MFG-02** (carried (U4 mask webs, ORDERING section 8.2)): U4 LGA-14 solder-mask webs are exactly 0.100 mm, zero margin to JLC green minimum. Fix: Keep the order remark; optionally 0.015 mm expansion (web 0.12) if the paste/pad fit allows.
- **R18-MFG-03** (new): Mixed via covering (two filled/capped vias, one 0.5 mm plugged via, rest tented/plugged) is only a free-text order request; no file carries it. Fix: State a fallback in ORDERING (e.g. whole-board capped fill or move the vias outside the pad) and mark the two vias in a fab drawing/note layer.
- **R18-MFG-04** (new): All 158 silkscreen texts sit at JLC absolute minimum, 1.0 mm high with 0.15 mm stroke (1:6.7 vs recommended 1:6). Fix: No change for this board; if respun use 0.17 mm stroke on legends (not designators crowded near pads).
- **R18-MFG-05** (new): Procurement numbers in AGENTS.md disagree with current fab/cost_check.json and ORDERING; stock_check.json fails while cost_check passes. Fix: Update AGENTS.md row to the 17:15Z snapshot.
- **R18-MFG-06** (new): C84 is an ordinary SMT line in BOM and CPL although the order requires it absent from both reflows. Fix: Rely on written JLC confirmation before payment (already required); consider marking the BOM row "THT/manual" in the Assembly column.
