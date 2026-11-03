# R17 full gate adversary

Target `ac483f40d38db6e0424227bd32d2a5d5f9f60c3e`, PCB `632a9ad36c19426ede219b6ff6b0d638955665cac1b4704d3392a6afdbe03982` before and after. **0 Critical / 0 Major / 1 Minor.** All 1,966 frozen preexisting files match before/after. This is a fresh full lens, considering all 122 D IDs and 23 owner scopes; D-R16-03's unchanged-board disposition applies. No canonical build/edit, Git action, subagent or peer R17 report/probe was used.

## R17-GATE-01 — Minor, new/active: missing canonical manifest fails open

`tools/check.sh:59` verifies fabrication only inside `elif [[ -f "$MANIFEST" ]]`; lines54–66 have no missing-file refusal or diagnostic. Normal S-4 receives neither BOM nor CPL, so the missing stage also loses the normal output binding. R10 acceptance in `docs/REQUIREMENTS.md` requires regenerated, board-bound fabrication outputs.

Fresh reproduction copied **all 1,966 frozen files** into a complete project, preserving project/rules/libs and the shell's canonical ROOT/BOARD equality. The unchanged genuine full gate exits **0**, explicitly verifying **5 outputs**. Deleting **only** copied `fab/m3_fab_manifest.json` then yields another complete **exit 0**, without any manifest-stage message. All 1,965 other files remain byte-identical; both runs finish the full native R10 suite. R10/fit/route JSONs match between runs. No fake CLI, skip flag, tool substitution or partial-check claim was used.

This is a demonstrated **prospective complete-gate artifact-completeness escape**. The actual target manifest is present and correct; no corrupt production output or current hardware failure is claimed. A focused restored-manifest control validates five outputs, and a one-file assembly-PDF byte mutation is rejected by the actual verifier.

**Fix:** require a manifest for canonical full checks except the explicit documented build-stage mode, invoke the verifier, and fail closed on absence. Add a canonical missing-manifest regression in `test_check_shell.py`, preserving noncanonical-copy behavior. This needs checks only; no PCB, placement, routing or circuit-generator change.

## Fresh checks

- Real vendor KiCad **10.0.7**, native Python API **10.0.6**: severity error/warning/exclusion, no ignored checks; DRC/unconnected/parity/ERC **0/0/0/0**. Metadata/models, silkscreen, native parts/budget, fit, all **32 R10 rules** including K-binding, routing and five-output manifest pass.
- Suites invoked by the complete gate pass: shell5, procurement, fit31, paste16, parts5, route67, R10 **180 tests with four native NumPy skips**, then HotplugNumerics2. Supplied NumPy Plate2 separately passes, resolving all four skips. The single missing-manifest run finishes the same complete sequence.
- Native census:209 footprints/951 segments/296 vias(168GND),1788.675665mm track,1.6mm thickness. All **100 U1 pad nets** match the reviewed `r10_net` table; saved binding regenerates identically. Record-only binding is not executable R10 firmware.
- Fresh return evidence:158,499 reference samples/0loose; K-region161items/62,176samples; all9 saved/refilled zones have **0.0mm²** symmetric difference at the unchanged0.01mm² threshold. Routing has0blocking/0allowlisted/0stale,140information annotations and6count-only noncritical leftovers.
- Seven terminals pass the accepted4.95mm floor at5.003mm rounded wire room. Fit allocates23tails and reports7.558359mm minimum tail/bore margin; nearest bottom/top support clearances4.536177/3.807887mm. These are CAD results.
- Independent in-memory negatives reject C126220nF→1nF, R123100k→1k, excluded/DNP R134 and removal of the filled intent at U401.11's(27.3,13.6)via. A saved binding with a zero board hash is rejected. These are focused controls, not additional complete runs.

## Rejected blocking hypotheses and limits

The fresh S-1/S-2/S-3/S-4 results and native net census reject a current unswitched fire feed, missing required gate networks or wrong100-pin map in the checked CAD scope. Real all-severity DRC, K-rules/LC-1/S-8/K-inner and symmetric-difference K-fill reject the current hidden-rule/inner-copper/stale-fill hypotheses within their implemented scope. The genuine present-manifest output mismatch and unfilled-via controls reject those fault hypotheses; the absent-manifest case remains the Minor above.

Official [ST DS12110 Rev11](https://www.st.com/resource/en/datasheet/stm32h743vi.pdf),pp207–211, was checked for separate pin absolute/operating conditions and VCAP Table114. These retain qualification obligations; they do not establish a fitted-capacitor or firmware failure. The named local `st_h743.pdf` cache was Rev8 and was excluded from Rev11 evidence. Direct retrieval produced no retainedPDF; official parsed text supplied the current check. No new manufacturing drawing visual QA is claimed.

No fresh source build, complete2304-case sweep, supplier query, independent187-row orientation reconstruction or618-aperture re-export was performed. F9-1 checks saved board-bound model evidence; the fresh numerical controls are narrower. No firmware, physical/electrical/transient/thermal/endurance, SD/e-match lot firing, RF/ESD, insertion/fabricatedS-8, combinedVCAP C/ESR, harness/switch/retention, tool/card/bore/stack or flight qualification is inferred. Existing disclosed qualification limits and M2/MEMS departures are not new demonstrated functional failures.

Raw receipts are in ignored `.supervisor/r17_gate_probe/`; durable exact results/hashes, all source hashes,122D/23owner coverage, negative distinctions and rejected hypotheses are embedded in [round17_gate.json](round17_gate.json). Positive log SHA256 `1d91ae1798d3d343dbbe9fe963c057743151b7371cb550fd9bcfc06eb2a8ba07`; missing-manifest log `8d04c2792abde99f2e6555e951d7959dc0ac8653f81127df3150b97293d23dcc`. A census attempt's unsupported accessor was corrected before its successful read-only run; raw failure is retained. Original handoff is immutable.
