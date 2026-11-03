# R7 fix pass 3: documentation fixes (handoff)

Documentation agent, fix pass 3. Files changed: `docs/REQUIREMENTS.md`, `docs/ORDERING.md`,
`docs/MARGIN_PRESCRIPTION.md`, `AGENTS.md`. Not touched: the board, scripts, tools, fab outputs, `docs/M3_R7.md`,
`docs/R7_VALIDATION.md`, `STATUS.md`, `docs/FMEA_REDUNDANCY.md` (nothing in my list touches it) and the parent
repository. Nothing committed. Inputs: `pass3_*.md`, `pass3_verdicts.json`; board read-only at SHA-256
`7660620c…7c9c` (unchanged when I last probed it); cost and stock from the bound `fab/cost_check.json`
(2026-10-17T21:01:10Z) and `fab/stock_check.json` (21:02:23Z), both bound to BOM `3a0c2f12…`.

## 1. Changes per finding

| Finding | What changed |
|---|---|
| P3-ELECTRICAL-01 (limiter short-circuit figures) | One figure set, 37–48 mA at −20 °C and 25–38 mA at +85 °C (Inference, `pass2_electrical.md` §4.3), in **REQUIREMENTS F10** (cold figure added; "27–46 mA" marked superseded), **ORDERING §5** GNSS short test ("design ≤ 46 mA" replaced by the required ≤ 50 mA plus both inferred ranges and the ~2 mA cold margin) and **ORDERING §7** "Antennas and coax" (cold figure added). The schematic note and M3_R7's table are not mine (§3) |
| P3-ELECTRICAL-02 (DNP bench-fit guidance) | **ORDERING §4 "DNP placeholders"** now lists C304 and says what each land may take, never as a JLC line (each new code would be Extended, past the 52-code limit): C303 capacitor only (3.2 V bias node, ≥ 6.3 V); C305 capacitor only while R304 is 0 Ω (inductor only once R304 becomes a series capacitor; RF_IN is DC-blocked in the module); C313/C314 capacitor or inductor (no DC on the radio line; C313 can take a DC-bleed inductor, EBYTE §5.1); C304 capacitor only, 1.0–2.2 nF 0402 X7R/C0G ≥ 10 V, start at 1.0 nF, never an inductor or short (it would hold Q30's gate at GND: no current limit and no LNA_EN switch-off). Example parts, checked on JLC's parts API today: Samsung CL05B102KB5NNNC, LCSC C14442 (1 nF 50 V X7R 0402; https://www.lcsc.com/datasheet/lcsc_datasheet_2304140030_Samsung-Electro-Mechanics-CL05B102KB5NNNC_C14442.pdf) and CL05B222KB5NNNC, LCSC C84703 (2.2 nF; https://www.lcsc.com/datasheet/lcsc_datasheet_2304140030_Samsung-Electro-Mechanics-CL05B222KB5NNNC_C84703.pdf), both Extended. **ORDERING §5** short test names the C304 part and points at §4. **REQUIREMENTS F10** pi-network clause points at ORDERING §4 |
| P3-DFM-01, P3-REQUIREMENTS-04(a,b) (C304, TP89) | **ORDERING §1** expected export output now `C303, C304, C305, C313, C314`. **§4** assembly split: 2 top test pads (TP30, TP84), 22 bottom (TP89 moved in pass 2); DNP bullet includes C304 (bottom, at (7.74, 16.90)); paste remark names the five unfitted lands as pasteless on purpose ("do not add apertures"). Checked on the board: TP top {TP30, TP84}, bottom 22; DNP {C303 F, C304 B, C305 F, C313 F, C314 F} |
| P3-DFM-02, P3-REQUIREMENTS-03 (cost/stock snapshot) | **ORDERING l.3:** about $106 per board (2026-10-17). **§1 result paragraph** rewritten from the bound reports: 92 codes, 52 Extended, parts $77.81, $105.96 per board, $79.23 with minimum purchases, short U4 only, thin none, stale after 24 h. **§1 U30 note:** not thin (161 in stock, 152 available, 2026-10-17), reserve anyway (18 on 2026-10-16); **§4 parts table** "Thin stock" dropped. U4 availability date extended to 2026-10-17. **REQUIREMENTS M3** "R7 as built" now the 2026-10-17 21:01Z run bound in `cost_check.json`: $105.96 = $77.81 + 92 × $1.53 / 5, 52 extended, $79.23 with minimum purchases; the 05:14Z $110.93 kept as history; RF lines MAX-F10S $17.38, E22 $6.52, SMAs $0.72, the rest about $1.05 (sum of the R7 references' lines in `cost_check.json`); U4 at JLC's $8.39, consigned total about $109.4–114.5 |
| P3-DFM-03 (order-number mark, tab table) | **ORDERING §3:** placeholder at (23.65, 103.15), Gerber Y −103.15, ink x 18.4–28.9, y 102.3–104.0 (measured on `7660620c…`), over two tented vias, with a note that `r7_post.py` places it and the position must be rechecked when copper changes. Forward-tab row x 6–11: nearest capacitor C120 17.29 mm, nearest 5 mm-rule item TH3 6.17 mm (pass3_dfm's scan); the note cites P3-DFM-03 |
| P3-DFM-04, P3-REQUIREMENTS-05 (J2.1 in-pad via) | **REQUIREMENTS M2:** the exemption now reads "bare contacts with no paste and no part (TP*, and J2, both exempt in `tools/check_r7.py`)" and names the J2.1 via as an exception: 3V3, (44.035, 77.92), inherited from R6, hole edge 0.14 mm inside the Ø0.787 mm opening; open and unplugged; expected DFM query; J2 taped and coated before flight. **ORDERING §3** "Via covering" row, the **§4** via remark and the **§4 expected DFM queries** list it next to TP122 (Gerber X 44.035, Y −77.92). Board probe: via at (44.035, 77.92), 3V3, 0.3 mm drill, 0.40 mm from J2.1's centre |
| P3-REQUIREMENTS-02, P3-MECHANICAL-03 (parent items done) | **REQUIREMENTS P1:** the parent VEHICLE R7 stack row is recorded (parent commit `43af048`); the board position stays open for the shroud measurement. No other file of mine listed the VEHICLE row or CLAUDE.md E22 wording as open. Stale entries in M3_R7, R7_VALIDATION and STATUS are the records agent's (§3); the proposed VEHICLE additions are the coordinator's (§2) |
| P3-MECHANICAL-01 (SMA torque) | The unsourced "about 0.45 N·m" is replaced in **REQUIREMENTS P3**, **ORDERING §5** (first power-up), **ORDERING §7** (antennas) and **MARGIN R14 (R7)** by the makers' recommended mating torque: 0.8–1.13 N·m for the jack (Kinghelm KH-SMA-KE8-G datasheet p. 1, re-extracted today), or the chosen plug's (or VNA cable's or load's) maker's value where lower, recorded with the plug choice; counter-hold kept; calibrated SMA torque wrench. **Source of the old 0.45:** Amphenol's SMA cut sheet gives 0.45 N·m (4 in-lb) recommended and 0.60 N·m (5.2 in-lb) maximum for its **brass** SMA series (stainless: 7–10 in-lb, 15 in-lb max); I cite it as the example of a plug that would set a lower value, so a brass plug is never over-torqued to the jack's range (re-extracted from https://www.tti.com/content/dam/ttiinc/manufacturers/amphenol/RF/Products/pdf/SMA-Cutsheet.pdf, "Brass SMA Specifications") |
| P3-MECHANICAL-02 (tie/saddle assumption, R14 (R7)) | **MARGIN R14 (R7):** the sled carries the coax and most of the plug; jack and tie share the plug by stiffness (zip tie compliant); jack moment at 5 × 100 g ≈ 45 N·mm (tie takes all), ≈ 190 N·mm (half), ≈ 370 N·mm (none); saddle off-axis adds preload; no pad strength on record, so the solder joints are not shown to hold 5×; status changed from "✅ ≫ 5×" to "⚠ ≥ 5× rests on the staking (Inference, not shown by calculation)", checked by inspection and the tap check; tie share labelled Inference with `pass3_mechanical.md` cited. **ORDERING §7 "Sled":** saddle set to the plug axis (jack axis 0.45 mm above the top face) so the plug rests on it unloaded before the tie closes, no visible jack/plug deflection on closing, stiff tongue. **REQUIREMENTS P3** and **ORDERING §7 antennas** say the same ("saddle and tie"; "relieves most, not all") instead of "the board's pads never carry cable loads" |
| P3-REQUIREMENTS-07 (wording gaps) | (a) **AGENTS §3** routing rule: GND via within 1.5 mm of every layer change of a critical signal net (RF, pyro/arming, crystal, USB data, SPI/QSPI/IMU CS, other RADIO_*/GNSS_*), which is `route_check`'s `SIGNAL_CRITICAL` set and `GND_REACH`; points at REQUIREMENTS M2 for the full list and at `tools/route_check.py` (gate, allowlist with measured reasons, rest by review). **M2** uses the same scope and wording. (b) **REQUIREMENTS P2:** "owner-delegated decision", as M3_R7 l.444. (c) **REQUIREMENTS F10** binding note: DIO1 (EXTI10) shares EXTI15_10 with PULLPIN (EXTI14) and VBUS_SENSE (EXTI15); the handler checks each pending bit if more than one is an interrupt (RM0433, not re-read) |
| P3-REQUIREMENTS-01 (M2 wording only) | **M2's last sentence** replaced by "What the gate enforces" / "What review checks". Gated on every net: the AGENTS §3 rule categories (listed) and the pour categories (slivers, unstitched GND fingers). Gated on critical nets (signal nets plus power rails and GND): the hygiene items (micro- and short segments, tiny jogs, … track loops), detours (pad-to-pad on a net without a pour, > 1.6 × octilinear and > 2 mm longer) and extra vias (any between pads sharing a layer, > 1 otherwise). Exceptions are allowlist entries with measured reasons; stale entries fail; an allowlisted entry stays a recorded deviation until the owner accepts it. Review: detours, extra vias and hygiene on non-critical nets, layer hops and pad-entry tidiness on every net, every allowlisted deviation. **Not from a handoff:** `fix3_F4_handoff.md` did not exist when I finished. The wording follows the board agent's task list and the **in-progress** docstring of `tools/route_check.py` (untracked file, modified 16:43; categories `short_segment`, `detour` with DETOUR_MAX 1.6 / DETOUR_SLACK 2 mm, `extra_vias`, `pour_sliver`, `pour_finger`; `short_layer_hop`, `pad_end_offcentre`, `power_via_no_gnd` information only). **Records agent: confirm against `fix3_F4_handoff.md` and the final tool** (§3) |

## 2. For the coordinator (parent repository, not edited)

P3-MECHANICAL-03 asks for two facts missing from the committed VEHICLE.md row (parent `43af048`). Proposed insertions
in the "Main-section stack, bulkplate up" row, inside the board's parenthesis:
- after "…overhang its aft edge by 9.5 mm;": "J1's battery entry faces forward at the board's forward edge, so the
  battery leads run the board's length and turn back into J1 beyond it (inside the ~25 mm eyebolt-nut and
  charge-wiring zone);"
- replace "clears the bottom parts, which hang up to 3.0 mm below the board," with "sits on standoffs ≥ 3.5 mm tall,
  clearing the bottom parts (up to 3.0 mm below the board) and the SMA plug nuts (2.6 mm),".
- Optional: "aft edge at joint ≥ +80…83 with the loops off the shroud side, or ≥ +91…95 with them forward of it".

VEHICLE.md had uncommitted edits by someone else at the start of this session; merge with them.

## 3. For the other agents

**Board agent (scripts and tools):**
- `m3_design/r7_sch.py` notes (sheet 15), then regenerate the sheet and netlist:
  - l.308: "…limits a shorted antenna or coax to about 37-48 mA at -20 C and 25-38 mA at +85 C (Inference, bench
    check)…" (P3-ELECTRICAL-01);
  - l.309: "DNP shunts are tuning placeholders: C303 and C305 capacitive only while R304 is 0R; C313/C314 C or L.
    C304 capacitor only, 1.0-2.2 nF." (P3-ELECTRICAL-02a).
- `tools/check_r7.py` `DNP`: add C304 (P3-REQUIREMENTS-04c).
- **If the J2.1 via is moved** ≥ 0.1 mm off J2.1's opening, delete the named exception from REQUIREMENTS M2 and the
  J2.1 entries in ORDERING §3 ("Via covering") and §4 (via remark and expected DFM queries); keep "TP*, J2" in the
  M2 exemption only if `check_r7` keeps exempting J2.
- **If the JLC placeholder moves** (r7_post on new copper, or pinned), update ORDERING §3 "Order-number mark".

**Records agent (M3_R7, R7_VALIDATION, STATUS):**
- **Confirm M2's "What the gate enforces" sentence against `fix3_F4_handoff.md`** and the final
  `tools/route_check.py` (`GATE`, category lists, detour/via-count limits, which nets they cover, whether short
  layer hops are gated). If they differ, correct M2 and AGENTS §3 to match (they are worded so that only M2's
  gated list needs to change).
- Recheck ORDERING §3's placeholder position and the J2.1 via against the final board SHA.
- M3_R7 limiter table (P3-ELECTRICAL-01): VEB −20 °C 0.55–0.71 V (pass 2), short-circuit 37–48 mA at −20 °C (not
  bold ≤ 46), 34–41 mA at 25 °C, 25–38 mA at +85 °C (`pass2_electrical.md` §4.3); pass-1 figures only as history. RF chains: "C305 capacitive only while R304 is 0 Ω; C304 capacitor only" (ORDERING §4).
- M3_R7 l.453 and R7_VALIDATION l.213: torque per ORDERING §5 (Kinghelm 0.8–1.13 N·m or the plug maker's lower
  value), not "about 0.45 N·m" (P3-MECHANICAL-01).
- M3_R7 §Mechanical (P3-MECHANICAL-02): "the tie relieves most, not all, of the plug; jack moment 45–190 N·mm at
  5 × 100 g; ≥ 5× rests on the staking (Inference)"; relabel the table row "plug carried by the jack alone (not
  allowed in flight)".
- M3_R7 l.280, R7_VALIDATION l.205/212/215/279 and STATUS l.107–108: VEHICLE row and CLAUDE.md E22 wording done
  (parent `43af048`); keep the shroud measurement and plug choice open (P3-REQUIREMENTS-02, P3-MECHANICAL-03).
- M3_R7 binding note: the EXTI15_10 sentence as in F10 (P3-REQUIREMENTS-07c).
- M3_R7 parts table: U30 stock 161 (2026-10-17) instead of "18 (ATP 9)" (P3-REQUIREMENTS-03).
- R7_VALIDATION: disposition DFM-01's third item (J2.1) as documented (M2 exception, ORDERING §3/§4).

## 4. Not done here

- **Incidental fix:** ORDERING §3's impedance row had an unescaped "|Γ|" that split the table row; now `\|Γ\|`.

- **P3-DFM-05** (tombstoning check of D30/D31/C302) and **P3-DFM-06(c)** (ORDERING §4 l.105 "J31 (915 MHz radio)"
  versus the RADIO legend) were not in my list; both would be one-line ORDERING edits.
- **Owner acceptance of the route_check allowlist** (P3-REQUIREMENTS-01 option b) is not recorded anywhere; M2 now
  says allowlisted entries remain deviations until the owner accepts them.
- The jack's assembly torque (Kinghelm "≥ 0.5 N·m", the jack's own nut-to-body joint) is not a mating figure and is
  not used.
