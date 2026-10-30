# Round 12 — gate adversary

**0 Critical / 0 Major / 3 Minor.** All three findings are prospective checker gaps. No whole-gate escape or current hardware defect was demonstrated. Target commit `d57b216c365fc8d18896bceba37f63caf20d52a4`; PCB SHA-256 before and after: `0ad0135cb9ff1f6ace7ef9d5ba9006b727b293d7b5224bb97dad47859b91238d`.

Native tests used installed KiCad Python and the verified official **10.0.7 CLI**, with isolated copied projects and native in-memory mutations. No canonical source/CAD/build, git action, full `tools/check.sh`, peer round-12 report, or owner question was used. CLI reservation is released. Complete individual seeds/results are in [round12_gate.json](round12_gate.json).

| Executed check | Measured result |
|---|---|
| Native required-fitted population | DNP on all 199 required parts and 33 additional exclusion flags: **232/232 rejected**. |
| All 23 exact terminal pin labels | Wrong role/polarity, hidden text and duplicate footprint text box per pin: **69/69 rejected**. |
| Topology/reset/single-switch | Twelve genuine pad-net/value faults rejected by S-1/S-2/S-3/S-5, including battery feed, independent PC1 enable, gate pull/series/cap and J400. |
| Invalid terminal/SD models | Zero, negative and NaN scaling on seven terminals and J430: **24/24 rejected by fit**. P-11 rejects invalid terminal geometry; J430 is fit's responsibility. |
| S-8 representations | Five board/footprint drawing/text/field variants beside J121.1: **5/5 rejected**. |
| Routing and reference | Three fast-route faults rejected; a 0.30 mm square In1 reference window at USB_DP (13.925,31.550) creates **90 loose samples**, rejected. An ACT_EN_MCU off-angle mutation remains blocking under AUD-2. |
| Real exported-list omissions | U1/U4/U401/R134/J430 removed from each real BOM/CPL: **10/10 rejected**. |
| Fabrication binding/failure handling | Current five-output manifest passes; **12/12** corrupt-output, wrong/missing/malformed manifest and bound-CSV mutations rejected. |
| Saved native projects | Identical baseline passes DRC/unconnected/parity **0/0/0**, fit, all 31 R10 rules and `r10_parts --check`. Six saved mutants tested with native DRC and the entire 31-rule contract; see below. |

The 357 focused phase-1 mutations yielded 355 selected-check rejections and the two misses investigated below. The evidence records 378 probe executions across stages, including repeated faults tested at stronger stages; this is not a count of distinct fault mechanisms. Current reference coverage is 160,761 samples, zero loose, six recorded strays. All seven terminal wire rooms are 5.003 mm under the existing CAD method. These are software/CAD results.

## R12-GATE-01 — Minor, new: positive model shrinkage

`tools/fit_check.py:129` rejects nonfinite, nonpositive and degenerate geometry, but accepts arbitrarily small positive geometry. At J410 **(38.6,15.5)**, set all three model scales to **0.01**. Its normalized height drops from **8.900001 mm to 0.089000 mm**; calculated P-11 wire room increases from **5.003012 to 8.963011 mm**. Fit and P-11 pass. Real all-severity native DRC/unconnected/parity is **0/0/0**.

The complete R10 contract rejects only **F9-1 stale inputs**; the native budget check also rejects the stale board binding. This is a prospective loss of an independent dimensional guard after future regeneration, not a demonstrated full-shell escape. The actual target has the correct maximum envelope. The established maker basis is [DORABO T0-1 sheet 1](https://atta.szlcsc.com/upload/public/pdf/source/20251124/8C215F69B14C8E54AE0F8E5023D4AE9F.pdf), as recorded by D-R11-01; this lens does not independently requalify that drawing.

**Fix:** validate normalized reviewed dimensions/pose for terminal and SD envelopes, allowing real unit conversions when the resulting physical dimensions agree. Add a positive finite shrink regression.

## R12-GATE-02 — Minor, new: foreign inner copper in other representations

`tools/check_r10.py:1749` K-inner iterates tracks only. Two native seeds connect to the existing **3V3 via (28.1,60.0)** on In1.Cu: (1) a 0.20 mm wide PCB_SHAPE from **(28.1,60.0) to (29.1,60.0)**; (2) a priority-10 3V3 zone bounded by **(27.5,59.4)–(28.7,60.6)**. After native refill, both pass real all-severity DRC/unconnected/parity **0/0/0**, fit, K-inner and every R10 rule except stale F9-1. The zone also passes the full route scan and critical bump search with **zero failures/bumps**.

Both fail the board-bound budget check; no whole-gate escape is claimed. Initial disconnected variants were caught by native unconnected/island checks, so those results are not used to claim an escape. The actual target contains **zero inner drawings/fields and zero non-GND In1 zones**.

**Fix:** extend K-inner using the existing complete copper representation walk to board/footprint zones and copper drawings, with explicit treatment of legitimate through-hole pads/vias. Add connected seeds so incidental isolation checks cannot mask the omission.

## R12-GATE-03 — Minor, new: BOM quantity is outside S-4 validation

`tools/check_r10.py:212` checks exported designator membership. In a copy of `fab/m3_bom_jlc.csv`, change only **U1 Qty 1→0**, retaining `Designator=U1`, the native PCB, schematic and real CPL. The actual native **S-4 passes all 199 required references with no issue**. U1 is at **(23,43)**. The unchanged manifest rejects the edited CSV, so this is a bounded future-export validation gap, not evidence of assembler behavior or a current missing MCU. Current BOM has 82 rows, quantity sum 199, zero quantity/reference mismatches; CPL has 199 rows.

**Fix:** in the existing CSV walk, validate positive Qty equal to the row's distinct designator count whenever Qty is present; retain the quantity-free CPL schema. A hypothetical wrong exporter plus newly matching manifest was not manufactured or tested as a full production escape.

The scoped evidence closes the prior round's exact-label, all-part population and nonfinite/nonpositive model defects (R11-GATE-01…03). AUD-2/AUD-10/audit2 and AGENTS §2 remain unchanged. The J400 graphic-short seed produced five real DRC findings despite native CLI exit 0, and S-5 independently reported the bypass; the production JSON-count path must remain mandatory.

No complete fabrication regeneration or production-shell run is claimed. Firmware, physical fit, screwdriver/SD access, retention, VIPPO/manual-solder process, electrical/thermal/transient behavior, source/harness and actual e-match lot qualification remain outside this lens.
