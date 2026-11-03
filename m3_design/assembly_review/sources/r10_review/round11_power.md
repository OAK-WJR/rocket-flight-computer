# Round 11: independent power and electrical review

Target: commit `21bc3b2`, PCB SHA-256
`0c50b9fd0930f34edab7129fc21b8e71d0ee03bc079e1900b7e131cece6bfaf8`.
Read-only review; no production file, generator, CAD, supervisor request or Git state changed.
Only this report and `round11_power.json` are reviewer outputs. No other round-11 report was read.

**Result: 0 Critical, 0 Major, 1 Minor group.** No Critical/Major candidate requires a fresh verifier.
The Minor is stale electrical evidence after the AVA placement/routing change; independent recalculation
continues to meet the selected 1.125 A all-fire floor. Existing disclosed physical/firmware qualifications
remain open; they are not newly counted findings.

## Finding R11-PWR-01 — Minor: refresh electrical numbers for the AVA copper

`m3_design/r10_parts.py:333–337` calls hard-coded circuit-pass lengths the final CAD path and regenerates
`parts_budget.json` from them. The current-fire paragraph in `docs/M3_R10.md:146–150` consequently still gives
4.612449 ohm and 1.284404 A at four stalls. The actual native board has different current paths:

| Net | Circuit-pass budget, mm / width | Native AVA current path, mm / width | Native endpoints / representative coordinates, mm |
|---|---:|---:|---|
| BAT_IN | 7.121320 / 1.0 | 6.000000 / 1.0 | J1.1 (7,74.1) to the Q120 drain copper at (13,74.1) |
| ACT_FET_S | 2.200000 / 0.4 | 2.200000 / 0.4, retained conservative aligned route | Q120.2 / Q121.3 at x13.175, y72.2 / 70.0; no parallel-source credit |
| RAW_ACT | 6.500000 / 0.5 | 5.886133 / 0.5 | Q121.8 (14.475,67.105), (17.58,64), R134.2 (19.075,64) |
| PYRO1_IGN | 4.850000 / 0.5 | 10.396068 / 0.5 | J121.2 (7,57.6), (7,59), (12,64), R134.1 (13.925,64) |
| PYRO1_OUT | 7.954478 / 0.5 | 7.954478 / 0.5 | J121.1 (7,54.1), (10.33,54.1), (11.33,55.1), Q124.5 (13.6,57.37) |

Method: native KiCad pad/track parsing and `check_r10.fire_path()` pruning of non-fire sense branches.
The source pair's two aligned paths are each 2.2 mm; summing all seven parallel source bridges would not be
a series-loop resistance. Pad copper remains ideal, matching the existing budget convention.

Using the existing material, hot-device, source, contact and harness assumptions gives **29.472622 mOhm at
20 C**, **35.263992 mOhm at 70 C**, branch resistance **4.467589992 ohm** and total loop **4.617589992 ohm**.
Solving the independent quadratic with 12.370806905 W other load, 7.4 V equivalent source, 0.15 ohm pack
resistance and 1.92 A per stalled servo gives:

| Persistent stalls | Fire current, A | Loaded pack, V |
|---:|---:|---:|
| 0 | 1.544322027 | 6.899397631 |
| 1 | 1.479395599 | 6.609332973 |
| 2 | 1.414223452 | 6.318170542 |
| 3 | 1.348766504 | 6.025735735 |
| 4 | 1.282976471 | 5.731812841 |

These are **Calc / Inference**, not measured currents. The limiting case remains 0.157976 A above 1.125 A;
this does not establish a firing-current violation. The original R134 stress bound deliberately ignores
all other resistance, so its 35.797452 W / 0.715949 J normal / 1.288708 J fault bounds remain conservative.

Two related records also need an AVA-bound replacement rather than transfer of historical measurements:

* `sources/r10_design/hotplug.md:6–16` identifies earlier boards, and `docs/R10_VALIDATION.md:1061–1062`
  still lists -14.497873 V and 504.293 W / 2.888490 mJ. Current input/result files are correctly bound to
  this board: **2304 required cases**, minimum **-14.798507843 V**, maximum +2 V initial state, maximum
  falling **8.959750934 V/us**, maximum rising including refinement **5.068601567 V/us**. R166 stress
  maxima across required cases are **577.218700 W / 2.977159763 mJ**, in different corners. The retained
  output envelope is **1616.123714 uF / 5.877715489 V after 2 s**. These numbers pass the stated model
  limits; pulse durability remains unqualified.
* `docs/M3_R10.md:171–174` and `docs/R10_VALIDATION.md:1063` retain historical output-loop measurements.
  Native F9-2 returns C82 OUT **3.577817 mm**, GND **9.426346 mm**, total **13.004163 mm**, projected area
  **6.591563 mm2**; D9 OUT **6.585534 mm**, GND **8.176346 mm**, total **14.761880 mm**, area
  **7.012187 mm2**. C82 is B(19.3,76.75), D9 B(15,79.3), U9 B(18.5,81.6). Both pass the unchanged
  engineering bounds. These are saved-copper geometry metrics, not measured inductance.

**Concrete fix:** change `r10_parts.py:336–337` to the native BAT_IN / RAW_ACT / IGN lengths above; keep the
aligned ACT source allowance and OUT length. Regenerate `parts_budget.json` through the build. Update its
status to the AVA board and refresh REQUIREMENTS F7, M3_R10's current fire paragraph, the current
`parts_qualification.md:263–275` calculation, the new decision entry, hotplug's current summary and the
replacement deviation list with the current numbers. Preserve historical named-board figures as historical.
The current U9 output ladder is two RAW_PROTECTED vias at (20.3,79.1)/(21.1,79.1), so the current deviation
row must also stop describing the former four-via ladder. No board or electrical-topology change is needed.

## Native coverage and adversarial checks

* Verified SHA-256 directly from the native PCB. Independently re-extracted every hot-plug input using
  `r10_hotplug.extract()`; JSON-normalized extraction exactly equals saved `hotplug_inputs.json`.
  Electrical signature is `84814409193955d81b1c24aafa8bce861f2c04aec092ea58c0f6491ccb5fb15c`.
  `r10_hotplug.validate()` returns no issue. No full 2304-case simulation rerun is claimed by this lens;
  the root owns the supervised build/check.
* Reviewed the actual feed topology and local C88-to-U9 edge rather than relying on the pass summary.
  C88 still intercepts U9's sole feed; the 3.92 mm local path is retained. The model remains conditional on
  unfused harness resistance at least 0.03 ohm and 0.1–2 uH. Lower-resistance sensitivity cases fail and
  cannot qualify a different harness. Half-step deltas remain within 2 mV / 0.01 V/us. The common-ground,
  capacitor-package and device-capacitance assumptions remain explicitly limited.
* S-9 independently passes on native copper, including every named source bridge. Fire paths have no
  series via. Current capacity is evaluated by pulse energy rather than the abandoned 7.7 A continuous
  servo route: at 70 C and the low-R134 current corner the 0.5 mm / 35 um conductor's independent
  adiabatic estimate is 7.08 K at 20 ms / 12.74 K at 36 ms (ignores spreading; Inference). A 28 um
  sensitivity gives 11.06 / 19.90 K. The qualified seven 0.4 mm source branches are retained; they share
  current and are not a license for new narrow fire copper. R134's energy upper bound is unchanged.
* Native F9-2 output-loop checks pass with the measured lengths above; C82 remains 22 uF / 25 V and
  D9 remains B340A-13-F with the correct OUT/GND roles. The input/output pad entries and via ladders are
  short necks; infinitely long IPC-2152 track temperatures do not establish their assembly temperatures.
  The recut In2 rails, 0.4 mm 3V3 bridge and retained In1 ground were inspected through native geometry
  and routing generators. No complete track/plane/via DC or thermal field solve is claimed.
* Independently recalculated buck/LDO settings from native fitted feedback identities, the core+SD
  load and the shared port-fault budget. Nominal endpoint budgets remain conditional; camera at 1 A
  gives 5.031682 V minimum, direct radio/GPS 4.601504 / 4.631504 V. The shared-port prospective demand
  exceeds U400's continuous rating; actual current-limit/hiccup is the documented fault response, not an
  assumption of continuous operation at that demand. The 3.743797 A threshold-based U9 input estimate
  remains below 3.96 A before unbounded switching overshoot; port-short logic survival is still a bench test.
* Recomputed C84 energy with 300.8 uF, 7.4-to-3.8 V and the explicit SD allocation: all loads give
  **0.490197–0.571129 ms**; camera off / GPS-radio on / logic shed / card idle gives
  **1.532615–1.655039 ms**. These are conditional states, not guaranteed transition times. SD can remain
  busy after clocks stop, and the 3 ms camera-switch turn-off exceeds the shortest estimate. OQ-5 and
  the later always-on-port decision are preserved; no hardware cutoff or GPS/radio shedding is inferred.
* U401 still has its two exact filled/capped vias. Its unchanged 0.406177 W normal-loss estimate and
  inferred 80–110 C/W give 102.494–114.679 C junction at 70 C ambient; 85 C remains unqualified.
  New routing does not turn that inferred coefficient into a measured thermal result. U400 losses,
  converter effective capacitance, low-input dropout and C84 cold ESR remain bench obligations.
* Checked physical-pulse/watchdog assumptions: normal current including tail <=20 ms; 960 LSI cycles
  at the stated qualified revision give 28.571–32.653 ms; 0.2+0.5+1.5 ms allocations yield 34.853 ms,
  guarded to 36 ms. The calculation excludes a failed-short switch, repeated pulses and unknown silicon
  timing. No firmware or actual current-tail qualification is claimed.

## Maker documents re-read

* [TI TPS25947 SLVSFC9C](https://www.ti.com/lit/ds/symlink/tps25947.pdf), pp7–8 and section8.4:
  negative-input/output differential limits, input slew limits, operating limits and local protection guidance.
  The official PDF was fetched directly when browser extraction timed out. Current model's cold OUT estimate
  leaves the -15 V absolute floor applicable; its minimum has 0.201492 V numerical margin.
* [Diodes AP6320x DS41326 Rev3-2](https://www.diodes.com/assets/Datasheets/AP63200-AP63201-AP63203-AP63205.pdf),
  pp5,11,14–15: reference tolerance, high-side peak limit, hiccup, bootstrap refresh and layout. Typical-only
  switch resistance does not establish a worst-case loaded dropout or thermal guarantee.
* [TI TPS7A91 SBVS282A](https://www.ti.com/lit/ds/symlink/tps7a91.pdf), pp3–6,22,25–26:
  supply/output pins, input/output capacitance, regulation range, current limit and local/thermal layout.
  The native fitted 22 uF input and two 22 uF outputs are present; effective capacitance and stability remain
  physical qualifications. The 200 mV electrical-table dropout limit takes precedence over cover prose.
* [TI TPS2121 SLVSEA3F](https://www.ti.com/lit/ds/symlink/tps2121.pdf), pp8,15: the reverse-current detection
  threshold prevents crediting ideal isolation of C84 from the port loads during a battery break.
* [AOS AONR21357 Rev2.1](https://www.aosmd.com/res/datasheets/AONR21357.pdf), pp1–4: voltage ratings,
  -4.5 V resistance, gate charge, hot curves and case-temperature SOA. The 40 mOhm hot/device allowance and
  actual shorted-load turn-on remain conditional on measured gate drive and temperature.
* [Bourns CRM2512](https://www.bourns.com/docs/product-datasheets/crm.pdf), pp1–3: R134 rating, temperature
  derating and single-pulse graph. The existing 20/36 ms stress comparison does not authorize automatic retry.
* [MJG J-Tek maker sheet](https://electricmatch.com/upload/JTEK_TECHNICAL_INFORMATION_SHEET_SPECIFICATIONS.PDF),
  p1: selected all-fire/test definitions and retained shroud. Its 0.5 s all-fire test does not certify the
  project's 20 ms pulse; the lot/charge/source qualification remains necessary.

## Not verified

No firmware, card latency/power-loss recovery, actual e-match firing, harness resistance/inductance, converter
stability/thermal behavior, reverse-input waveform, R166 durability, physical current tail, repeated pulses or
assembly process was measured. Those limitations are retained, without changing AGENTS section2 or the owner's
single-switch, unfused-input, always-on-port and hold-up choices.
