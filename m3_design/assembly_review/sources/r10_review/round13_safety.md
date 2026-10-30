# Round13 safety review

Target commit `fa897c81abac3026e75ca5cc88bef0c2659a7130`; PCB SHA-256 before and after:
`7355ae1aeb1fdfdf6f64317945a0bf114d94c2bb65fb04adfbcd5a2b8037b09c` (2,264,839 bytes).

**0 Critical / 0 Major / 1 Minor.** No demonstrated AGENTS section 2 violation.
This is CAD/analytic review; firmware and bench qualification remain open.
R9 supplies severity precedents, not a literal severity-definition table.

## New finding

**R13-SAF-01 — Minor, open: O6 resistance assigned to the wrong branch.**
`docs/R10_VALIDATION.md:1231` says the 0.6144 A board-return bound uses
“>=50 milliohm motor branches”. D-R1-07 (`R10_DECISIONS.md:101`) and the
correct current harness worksheet (`docs/ORDERING.md:485`) require this
resistance in each **signal-reference branch**. Native J122 F(38.6,71.5)
has signals 1–4 / GND 5; motor power/return are external. The retained arithmetic
is 4 × 7.68 mV / 50 mΩ = 0.6144 A; at 5 mΩ reference resistance its upper bound
becomes 6.144 A even if motor branches meet 50 mΩ. This is a conditional
counterexample, not measured board current. A maker page does not apply to this
owner-defined harness condition. **Fix:** change “motor branches” to
“signal-reference branches” in that active paragraph. Preserve the 50 mΩ / 1 mΩ
conditions and 1 A allowance. The detailed assembly instruction is correct;
no hardware failure is shown.

## Independent evidence

Actual native schematic symbol/wire/global-label geometry was parsed before
comparison with the XML export and PCB: 271 selected pins across 50 parts,
including all 100 MCU pins; zero net/value discrepancies. Native connectivity
has zero unconnected items. All pads on 17 safety nets share their intended
connected components, without a foreign pad.

J400 F(7.4,65.85) reaches U9 EN through R80/R165, each 470 kΩ. RAW_ACT is
exclusively post-Q120/Q121. R134 2 Ω feeds J121.2 IGN; J121.1 OUT returns through
Q124. PC1/U1.16 independently reaches Q122 through R122 1 kΩ / R123 100 kΩ.
PE4/U1.3 uses R126 220 Ω, R127 1 kΩ, R128 10 kΩ and C126 220 nF. High-side
gates retain R120 100 kΩ, R121 10 kΩ and C120 1 µF / 25 V. Native required-fit
flags and selected safety contracts pass.

Independent saved-copper barrel measurements exceed the unchanged 1 mm floor:

| Barrel | Centre (mm) | Nearest foreign inner copper | Gap (mm) |
|---|---|---|---:|
| J121.1 OUT | 7.4,54.1 | In2 3V3 | 1.102501 |
| J121.2 IGN | 7.4,57.6 | Other terminal pad | 1.900001 |
| OUT via | 11.63,55.1 | In2 3V3 | 2.698435 |
| Gate via | 14.4,53.3 | In2 USB_LIMITED | 2.100000 |

174,080 analytic passive cases cover the eight divider resistors at ±1.45%,
16 single open/short modes plus healthy, source/diode corners and five cold-load
states. Worst pin voltage is 1.410766 V at 8.4 V or 3.342171 V at 19.9 V, below
the 4 V ADC-mode absolute ceiling. Worst 8.4 V divider diagnostic current is
1.397310 mA, below the selected match's 40 mA maximum test current. Healthy
1–2 Ω cold CONT is 86.986–115.191 mV and BUS 86.957–115.157 mV; open CONT is
129.162–168.020 mV / BUS 0; a grounded Q124 drain gives 0/0. A short match
resembles healthy. These exclude leakage/ADC errors and do not set thresholds.

Conditional low-side floating-MCU discharge is 10 kΩ || (220 Ω + 1 kΩ) =
1087.344 Ω: nominal 3.3→0.4 V takes 0.5048 ms; the stated tolerance/charge
allowance gives 0.7396 ms. This does not prove the required 1.5 ms actual-current
tail. The 960 LSI cycles give 28.571–32.653 ms; allocated fault total 34.853 ms
remains below 36 ms. R134's adverse 70°C short estimate is 35.797 W,
0.715949 J / 20 ms or 1.288708 J / 36 ms.

Native fire tracks independently give BAT_IN 6.307107 mm / 1 mm, one aligned
source leg 2.2 mm / 0.4 mm, RAW_ACT 5.886133 mm / 0.5 mm, IGN 10.230382 mm /
0.5 mm and OUT 7.854478 mm / 0.5 mm, without a series fire via. At the stated
material/source/harness/load assumptions this is a 4.617458 Ω loop, giving
1.544366 A idle and 1.283013 A with four persistent stalls, above 1.125 A.
This is calculation, not selected-lot 20 ms firing or shorted-match survival
qualification.

Maker checks: [ST DS12110 Rev11 pp207–208/233](https://www.st.com/resource/en/datasheet/stm32h743vi.pdf),
[AONR21357 pp1–2/4](https://www.aosmd.com/res/datasheets/AONR21357.pdf),
[AON7524 pp1–2](https://www.aosmd.com/sites/default/files/res/datasheets/AON7524.pdf),
[AO3400A pp1–2](https://www.aosmd.com/sites/default/files/res/datasheets/AO3400A.pdf),
[Bourns CRM pp1–3](https://www.bourns.com/docs/product-datasheets/CRM.pdf),
[MJG sheet p1](https://electricmatch.com/upload/JTEK_TECHNICAL_INFORMATION_SHEET_SPECIFICATIONS.PDF).
The MJG all-fire datum is a 0.5 s test; it does not certify this board's 20 ms pulse.

## Executed checks and limits

The ignored probes `r13_safety_probe.py`, `r13_safety_geometry.py`,
`r13_safety_seeds.py` and `r13_safety_firepath.py` ran with the provided KiCad
10.0.6 Python `-I -B`; `r13_safety_calcs.py` ran with Python 3. Final exits are 0.
Selected S1–9/K-loader/K-actuators give zero findings. Six in-memory faults are
rejected: direct-pack R134 feed, automatic enable from RAW_PROTECTED, C126 DNP,
R127 at 10 MΩ, R129 at 0 Ω and a J400 contact bridge. The first R129 probe had an
unchanged text-backed context; correcting the probe rejects it. The bridge also
intersects saved GND fill, so it is not an isolated contact-only fault.
Initial connectivity signature/cast setup errors were corrected. Nonfatal wx
warnings are not DRC evidence. No real CLI, full gate, build, GUI or git action ran.

The current cold-screen order/probe/coating worksheet agrees with native CAD;
those prior record defects are not reproduced. Retained architecture/qualification
limits are carried separately, not recounted as new defects: one MCU/two controls,
ordinary surface gaps, unfused entry, no powered physical break, no GPS/radio off
isolation, physical switch access/retention and mandatory coating/isolated backup.
Connect an e-match without USB/self-powered sources; USB bench uses pack or e-match
disconnected. Camera's retained [TXU0202 pp1/4](https://www.ti.com/lit/ds/symlink/txu0202.pdf)
and [TPS2553 p7](https://www.ti.com/lit/ds/symlink/tps2553.pdf) do not establish
instantaneous power disconnection from an enabled back-fed camera.

No R10 firmware, actual reset/trace/watchdog/current-tail/ground-refusal/launch
behavior, selected-match firing, electrical/thermal/transient/RF/harness/coating,
retention/fit or physical process test was performed. No peer round13 report was
read. The JSON contains compact native topology, calculations, seed results,
primary-source pages, checks and coverage limits. Canonical files stayed frozen.
