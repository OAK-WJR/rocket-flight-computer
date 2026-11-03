# R10 round 11: gate adversary

Target: `21bc3b2`, PCB SHA-256 `0c50b9fd0930f34edab7129fc21b8e71d0ee03bc079e1900b7e131cece6bfaf8`.
Result: **0 Critical / 0 Major / 3 Minor**. All three are prospective gate-coverage gaps; none of the seeded
faults is present on the canonical board. This lens made no production change and verified the PCB hash unchanged.

Read scope: AGENTS, REQUIREMENTS, R10 decisions through D-AVA-02, AVA_LAYOUT, M3_R10, historical R10/R9 validation,
native PCB/netlist, gate implementations, their tests and build/fab dispatch. No other round-11 report was read.
The [97 recorded checker outcomes](round11_gate.json) include controls and multiple checks of some faults; they
are not 97 independent seeded boards. Probes used KiCad's Python API, isolated text/netlist mutations and synthetic
fixtures. No `kicad-cli`, `check.sh`, full build or supervisor request was run by this lens. **No seed is claimed to
survive full DRC or the complete build.** Root owns fresh full-gate evidence.

The unmodified board passed 21 selected native R10 rules, native fit, the exact schematic contract and the
five-output fab-manifest check. Fit's minimum recorded bore margin was 0.886129 mm. All canonical model transforms
were finite, with positive unit scales. Current U1/U2/L1/U3/U4/U5/Y1 are fitted. These are CAD/software observations;
no physical, firmware or electrical qualification is inferred.

## Findings

### R11-GATE-01 — Minor: individual terminal text boxes and polarity text evade the conflict check

**Sources:** `tools/check_r8.py:758–761` only walks board `PCB_TEXT` for expected individual terminal words.
`tools/check_r10.py:2293,2304–2309` skips a bare word if it appears anywhere in the global terminal-word set and its
fallback regex excludes `+`/`-`. The new textbox support therefore covers combined alphanumeric tables and unknown
alphanumeric words, but leaves the current individual-label representation incomplete.

**Native seed:** add an F.Silk `PCB_TEXTBOX`, box **(29,10)–(34,12) mm**, text **`4:TXO`**, 1.0 mm size / 0.15 mm
stroke, border disabled. It lies nearest GPS **J410.4 (39,10.25)**, whose actual role and existing legend are
**`4:RXI`**. `check_r10.check_board(..., only={'K-legends'})` returns **0 issues**, with **0 additional mask
overlaps**. `4:TXO` is globally known from the camera, so the conflict helper ignores it; the legacy individual-label
walk ignores its textbox type.

Additional clear-mask textbox seeds at (9,12)–(21,14) also return 0 issues: `3:RXI`, `1:BAT-`, `1:E1+`, and explicit
**`J1 1:BAT-`**. The last contradicts battery **J1.1 (7,74.1), BAT_IN / `1:BAT+`** regardless of location. Controls:
plain-board-text `3:RXI` is rejected by the terminal walk; textbox `2:RXI` is rejected by the conflict helper.
Baseline K-legends is clean. No production conflicting textbox was found.

**Fix:** share one individual-terminal-label walk across board/footprint text and text boxes; associate every
candidate with its intended/nearest connector pin, check that pin's exact word, and count it once. Parse the `+`/`-`
characters already required by BAT/IGN legends. Retain AUD-10's distance-only review treatment and blocking
mask/clearance rules. Add the two native textbox seeds above with an explicit zero-mask-overlap assertion.

### R11-GATE-02 — Minor: the final required-population set omits the functional core

**Sources:** `tools/check_r10.py:127–134,1439–1459,200–204`. Native and exported-list population checks share
`REQUIRED_FITTED`, which omits **U1/U2/L1/U3/U4**. The circuit/actuator checks verify electrical pad facts and values,
not those parts' DNP attributes.

**Native seeds:** independently set `FP_DNP` on **U1 (23,43), U2 (25,69.8), L1 (25,74.6), U3 (22.6,41.2),
U4 (17,45.9)**. U1 is top; the other four are bottom. Each returns **0 issues** from
`check_r10.check_board(..., only={'S-4','K-contract','K-actuators'})`; the unmodified control returns 0. Separately
delete U1, U3 or U4 from each actual `fab/m3_bom_jlc.csv` and `fab/m3_cpl_jlc.csv`: all six omissions return
**0 issues** from `assembly_population()`, while both original lists return 0. These omit the MCU, primary QSPI
logger or IMU required by F1/F2/F5/F6.

**Existing detection:** `r10_sch_check.contract()` rejects all five equivalent schematic DNP mutations with
`changed assembly flag dnp` (`m3_design/r10_sch_check.py:126–128`). Full-build preflight dispatches it at
`m3_design/r10_build.sh:43`; an unrebound PCB edit also fails manifest integrity. `check.sh` itself does not dispatch
the exact schematic contract; fab's S-4 invocation at `m3_design/r10_fab.sh:34` inherits the limited set. Thus this
is a final-population/assembly-list coverage gap, **not demonstrated complete-build or full-gate survival**. The
canonical board and lists include all five parts.

**Fix:** extend the existing final fitted-reference invariant to the functional core and mandatory support, or
share the reviewed source's fitted-reference set with S-4 and exported-list validation. Preserve explicit bare-board
and owner-assembly exceptions. Reuse the existing native walk; no additional complete schematic walk is needed.
Add native DNP and BOM/CPL-omission controls for the functional core.

### R11-GATE-03 — Minor: invalid model transforms can pass fit and wire-room checks

**Sources:** `tools/fit_check.py:129–152` validates raw model vertices but does not validate model transforms or
the transformed box. `tools/check_r9.py:812–818` / `tools/check_r10.py:1881–1904` use that model box for P-11's face.

**Paired native terminal seed:** move J410 from **(39,15.5) to (40,15.5)**, retaining its rotation and real model.
`p11()` correctly fails, reporting **3.953 mm** wire room against the **4.95 mm** floor. On that same moved
footprint, assign the model's native scale XYZ **(0,0,0)**. `p11()` now returns **0 issues**, reports **7.603 mm**
wire room, and `fit_check.check_board(profile='r10')` returns clean with a degenerate J410 body box
**(40,15.5,40,15.5,0,0)**. The modeled body has disappeared; the original terminal envelope still gives the 3.953 mm
failure. This is a model-validity failure, not a claim that moving a routed terminal passes electrical DRC.

**Nonfinite native seed:** set only **J430's model scale.x = NaN** at its actual **(24,24.3), bottom** pose.
Native fit returns **`ok:true`, 0 issues**, with a **NaN J430 body box/margin**. Its separate finite mated-card
allocation does not reject the bad body row. All original models have finite transforms and unit scales.

**Fix:** reject nonfinite scale/offset/rotation and transformed points/boxes; reject zero scale and degenerate
fitted-body envelopes. Keep valid documented model conversions. Make invalid geometry fail both the fit check and
any P-11 model consumer, and add the two paired native tests. No maker electrical parameter or dimensional change
is proposed; these findings concern malformed geometry handling, so no external datasheet claim is involved.

## Tested boundaries that held

| Coverage | Checker and measured result |
|---|---|
| Always-on ports, direct ADC, SD circuit | `functional(seed_text)` rejects GPS RX's 1 kΩ bypass, J420.1 moved to CAM_5V, PC5 moved onto continuity, J430 shield pad 9 on DAT1, and R464.2 supplied by PORT_4V8: 2 / 2 / 3 / 2 / 1 issues. Original exact schematic contract: 0. |
| Fast reference scope | All six SD nets, all eight GPS/radio MCU/wire UART nets and both pyro gate nets: 16 native-track fixtures each have 0 issues over a reference plane; removing it gives 603 loose samples and a failing `references()` result each. |
| Fast via partners | The same 16 nets: `critical_transitions()` sees a 1.000 mm GND partner in every control and no partner in every fault. No slow-net prefix exemption admitted them. |
| Single-region scope | Native filled In2 GND/3V3 split fixtures fail `region_issues()` for SD_SCK, GPS_RX_WIRE and RADIO_TX_MCU; each unsplit control has 0 issues. |
| AUD-2 stays narrow | ARM1_SENSE/PYRO1_CONT/ACT_GATE/CAM_UART_OE retain their exact reference/partner exemptions. With a separately referenced USB control track, all four reference controls pass. A 0.141421 mm 45° jog on each remains critical and fails `route_check.scan/evaluate` with micro/tiny-jog findings. |
| Fire/source width | Actual fire-path ACT_FET_S bridge reduced 0.4→0.2 mm fails S-9, including stale exact exception; RAW_ACT and PYRO1_OUT 0.5→0.49 mm fail; BAT_IN 1.0→0.5 mm fails. Long RAW_PROTECTED 0.7→0.3 mm fails K-width's 2 mm run cap (measured 5.34 mm chain). |
| Fab integrity | Canonical five-output manifest passes. Independently append one newline to BOM or CPL: each fails `verify_manifest()`. Remove CPL's required manifest entry: fails. Temporary packages are deleted. |
| Required dispatch | Source inspection confirms complete check_r10 and route_check profile r10, current repository manifest validation, shell/procurement/fit/paste/route/R10 self-tests, and separate NumPy HotplugNumerics dispatch. Full build dispatches exact schematic preflight and fab before its final unskipped check.sh. Execution belongs to root's service. |

An early width fixture selected a non-fire gate-bias branch; it was discarded and replaced with an actual
`fire_path()` member. Early mask-colliding, unrouted-only and unchanged-model-copy fixtures were likewise excluded
from the scored evidence. The recorded faults identify the invoked checker and its actual outcome; a subset check
does not certify full DRC, electrical behavior, manufacturing, firmware or physical fit.
