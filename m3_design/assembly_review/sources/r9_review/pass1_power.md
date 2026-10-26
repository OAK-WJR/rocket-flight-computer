# R9 review pass 1: power, thermal and hot-plug

**Board:** `m3_design/assembly_review/m3.kicad_pcb`, SHA-256 `fc3d5b34a4bfbaecfbcb44bdf8144c87015fc71be7accf48354f23410e8d0f51`
(R9 steps 1–10). I hashed it before and after the review: unchanged. This was a read-only review. The only repository file
I wrote is this report. `git status --short --ignored` was equal before and after, apart from the `r9_review/`
reports (this one and the other pass-1 reviewers', written in parallel) and an ignored `r8_design/step9/__pycache__/`
that a parallel session created and removed. My Python runs used `-I` with `-B` or `PYTHONDONTWRITEBYTECODE`, or found
the cache current. I measured with KiCad 10.0.6 pcbnew (KiCad
Python) from scratch scripts in the session scratchpad (`r9review/power/`). Nothing was saved to the repository board;
one scratch copy (J122's GND pads on reliefs, for a DRC trial, finding 04) was made there and deleted. Maker documents
were fetched this session (URLs at each use). Every figure is measured on the board unless it is marked Calc or
Inference.

**Result: 0 Critical, 0 Major, 5 Minor (4 worth fixing).**

- **The 7.7 A copper is sound and reproduces the record.** At the build's 0.1 mm grid: RAW_ACT 0.79 mΩ, neck 7.79 mm on
  B.Cu, 12.8 °C; BAT_IN 0.17 mΩ, 8.19 mm, 12.1 °C; ACT_FET_S 0.27 mΩ, 5.11 mm, 20.8 °C (D12: 20 / 20 / 30 °C). No series
  via; the largest barrel currents 0.46 / 0.65 / 0.25 A. The 0.05 mm evidence (12.7 / 12.1 / 20.4 °C) is bound to the
  same SHA-256. J122's RAW row, which the equipotential sink leaves unloaded, carries 5.8 A at four equal stalls through
  B.Cu 2.88 mm + In2 8.69 mm of copper (about 5 °C by the fit, Calc).
- **The F9 reverse hot-plug premise holds.** The model re-run gives the evidence to the digit, and the battery-entry
  leakage paths are better separated than R8's.
- **Supply paths and the servo GND return:** seven supply rows and the 0.32 mΩ return re-solved, each equal to its
  evidence. All zone fills equal a fresh refill. `tools/check.sh` exits 0.
- **Findings** (all Minor):
  - **01** (worth fixing, copper and records): three power-IC bypass capacitors regressed from R8 against TI's layout
    rules, and R9 records none of them. U10's C83 is 11.6 mm of track from U10.IN (R8 1.73 mm after D88 fixed
    R8P1-POWER-03). U11's IN1 cap C98 is 5.3 mm away (R8 1.73 mm). U9's OUT cap C82 is about 20 mm away (R8 8.1 mm,
    recorded as a deviation).
  - **02** (worth fixing, records): R84 = 750 Ω sets U9's limit at 3.96–4.84 A. The records still carry R3's 1.80–2.20 A
    (2.2 A), and R9's RAW_PROTECTED sizing basis rests on it.
  - **03** (worth fixing, records): R9 drops R8's list of single-via rail links (MARGIN_PRESCRIPTION R15). Seven of them
    are undocumented: the 3V3 domain feed, U11's battery input, the hold-up, the camera feed, CAM_5V, VDDA's hop and
    USB_LIMITED's two vias in series.
  - **04** (worth fixing): J122's four GND pins are solid on F.Cu, In1 and B.Cu. That is an M2 thermal-relief exception
    R9 does not list (R8's C17). Its R8 basis, a starved spoke, does not hold on R9's copper: with reliefs the pins get
    4 / 4 / 2 spokes and DRC reports no starved thermal.
  - **05** (not worth fixing): R8P4-POWER-02's records fix (the thermal-relief rule as built) did not carry into R9.

## 1. What was run

| Check | Result |
|---|---|
| `tools/check.sh` (repository board, real kicad-cli, KiCad Python, `NUMPY_PY` = the cfd venv) | **exit 0** in 4 min 16 s: DRC 0, unconnected 0, parity 0, ERC 0; metadata / 3D audit OK; silkscreen 0; fit OK; plate model; rule-H seeded suite; check_r9 OK on every rule (F9-1, K-power-pyro, K-copper among them); route_check r9 0 failing / 0 allowlisted / 0 leftovers; check_actuators OK. The report folder was deleted after copying `r9.json` to scratch |
| `tools/run_dc.sh <board> <scratch> 0.1` | Each output's first line carries `fc3d5b34…`. **RAW_ACT** 0.79 mΩ; neck 7.79 mm B.Cu, cut box (28.7–35.5, 78.43–81.03) on Q121's drain row, 12.8 °C ≤ 20; mid-path F.Cu 6 % / In2 47 % / B.Cu 47 %; 32 vias carry current, max 0.46 A at (32.2, 78.2), none over 0.5 A. **BAT_IN** 0.17 mΩ; 8.19 mm B.Cu, (29.81–31.11, 89.85–97.75), 12.1 °C; 9 vias, max 0.65 A at (32.0, 96.4), 5 over 0.5 A. **ACT_FET_S** 0.27 mΩ; 5.11 mm B.Cu, (31.45–35.25, 88.0–89.3), 20.8 °C ≤ 30; 8 vias, max 0.25 A. These equal step 9's post-check figures (`step9_evidence/r9_post_check.json`) and match the 0.05 mm evidence (`step9_evidence/dc005_*.txt`: 7.81 / 8.15 / 5.18 mm, 12.7 / 12.1 / 20.4 °C, vias 0.46 / 0.61 / 0.22 A) within the grid difference |
| RAW_ACT to one J122 pin (`dc_solve.py --sink J122:2` and `J122:11`, 7.7 A, 0.1 mm) | All 7.7 A to J122.11, the pin nearest the spine: 0.79 mΩ, the same neck as the four-pin solve. The record's equipotential sink therefore feeds almost everything to J122.11, and the RAW row carries nothing (run_dc.sh's docstring says so). All 7.7 A to J122.2, the farthest pin: 1.35 mΩ, neck 5.36 mm (In2 3.0 + B.Cu 2.8 mm, x 20.4–21.6), 20.8 °C. That is an upper bound, since each pin carries ≤ 1.925 A. Geometric cut at x 25.54 (between J122.11 and J122.8, 5.78 A at four equal stalls): RAW_ACT B.Cu 2.88 mm + In2 8.69 mm, equal at x 23.0 / 20.46; 10.3 mm 35 µm-equivalent, about 5.2 °C at 5.78 A by `tools/ipc2152.py` (Calc). No F.Cu at the RAW row (the F.Cu pour starts at y 65.4) |
| Supply rows (`dc_solve.py`, 0.1 mm) | USB_LIMITED U10:6 → U11:7 **83.02 mΩ** (two vias, 0.50 A each at 0.5 A); RAW_PROTECTED U9:6 → U7:3,4 **77.11** (the U7 via 1.00 A at 1 A), → U11:2 **16.22** (the U11 via 0.50 A); BAT_IN J1:1 → U9:5 **2.32**; CAM_5V L3:2 → J9:1 **2.88** (one via, 1.00 A); 3V3 L1:2 → U1:75 **15.25** (the feed via (37.6, 78.9) carries all of it); VLOGIC C84:1 → U2:2,3 **9.54** (the hold-up via (38.5, 69.6) carries all of it). Each equals `step10_evidence/dc/dc_summary.txt`. New rows: RAW_PROTECTED U9:6 → C82:1 8.08 mΩ; VBUS U10:1 → C83:1 19.15 mΩ (finding 01) |
| Servo GND return (`dc_solve.py --net GND --source J122:3,6,9,12 --sink J1:2 --window 0,50,46,102`, 0.1 mm, 39 min) | **0.32 mΩ** (2.5 mV, 0.019 W at 7.7 A); mid-path In1 40 %, In2 29 %, B.Cu 22 %, F.Cu 9 %; peak 1.70 A/mm at J1.2's spokes (21.35, 93.45); 151 vias carry current, max 0.29 A at (22.25, 87.45); 4296 CG iterations. Equal to `step10_evidence/dc/gnd_servo.txt` line for line. The fire-loop return (0.81 mΩ) was read from the evidence |
| Hot-plug model (`step6_evidence/hotplug_feed_r9.py --rb 2.32`, cfd venv numpy) | 512 cases. L_b 3.232 nH: +0.0021 V, slew × 1.028; 5 nH: 0.0036 V, × 1.0372; 15 nH × 1.0746; 30 nH × 1.1193; lowest A = B = −14.114 V; fastest B 7.66 V/µs. Identical to `step10_evidence/hotplug_feed.json`. No bytecode was left in the repository |
| Zone fills (every copper zone refilled in memory with `ZONE_FILLER`, not saved) | 16 zone-layers, **0 differ** from the saved fill in area, island or hole count, so the Gerbers carry current fills |
| Pad-to-pour contact (fill ∩ a 0.1 mm ring just outside each pad) | J1.1 solid on F.Cu, In2 and B.Cu. J1.2: F.Cu 4 × 0.5, In1 4 × 0.4, In2 4 × 0.4, B.Cu 2 × 0.5 mm spokes (the BAT_IN B.Cu pour takes the other two). J122's RAW pins solid on In2 and B.Cu (no F.Cu). J122's GND pins solid on F.Cu, In1 and B.Cu (J122.3 also on In2). J124.2 has no pour contact (fed by the 1.0 mm RAW bar). J123.2 4 / 4 / 4 / 4 spokes |
| Zone and pad connection settings | Every power zone (BAT_IN, RAW_ACT, ACT_FET_S, RAW_PROTECTED; F / B / In2) is FULL. GND F / B / In2 are THT-thermal (0.5 / 0.5 mm on the outer layers), In1 thermal (0.25 / 0.4 mm), In2 3V3 thermal. Pad overrides: 98 SMD GND pads THERMAL (the house small-pad rule, 12 of them 0805 / 1206: finding 05), J122.3 / 6 / 9 / 12 FULL (finding 04), 6 RF pads FULL. No override on any BAT_IN / RAW_ACT / ACT_FET_S / RAW_PROTECTED pad |
| Single-via links (each of the 97 power-net vias removed in turn in memory, connectivity rebuilt, unconnected count compared; scratch `singlevia.py`) | 47 single vias. Eight are the rail carriers of finding 03. The other 39: 28 3V3 bypass / pull-up / FB taps; the RAW_ACT_SENSE, VLOGIC_SENSE, TP83 and R122 (ACT_EN pull-up) taps; VCAP1 / VCAP2; J3's two VBUS pins and D4's VBUS pin (bench-only USB); CAM_IO_3V3's two (mA, the camera translator) |
| Decoupling (nearest same-net capacitor to every IC supply pin; track path where it matters, scratch `trackpath.py`; the same paths on R8 `cc044ea0…`, read only) | §4 and finding 01 |
| Battery-live gaps (bare pad to bare pad, and all copper, BAT_IN / RAW_ACT / ACT_FET_S / RAW_PROTECTED / BAT_DAMP / switch nets to every non-GND net, own-part pads excluded) | Bare pads: C95.1 (BAT_IN) to R166.1 (BAT_DAMP) 0.52 mm and R122.1 (RAW_PROTECTED) to R123.1 (ACT_EN) 0.551 mm (the damper's own pair and the gate-drive divider's own pair; benign). BAT_IN to BAT_ENABLE or the switch nets: U9.5 to U9.1 0.20 mm (U9's own pitch); U9.5 to the EN entry track 0.40 mm; every other pair ≥ 0.85 mm (R80's own pads), TP84 1.04 mm from the masked BAT_IN F.Cu pour. J1.3 / J1.4 sit in In1 and In2 GND, with no inner BAT_IN beside them (R8: In2 BAT_IN 0.3–0.35 mm from them) |
| In2 map (zone fills, gap bands) | Each region one island: RAW_ACT 241.9, BAT_IN 115.3, 3V3 1037.1 mm²; GND 1742.2 + strip 982.1 + crystal plane 35.3 mm². The 3V3 finger is 1.49 mm wide (x 36.31–37.8) for about 22.6 mm, y 56.7–79.3 (about 8.7 mΩ, Calc). In2 RAW_ACT to 3V3 is 0.30 mm along the finger (x 36.15, y 57.1–79.2) and along y 56.85 (11 mm). BAT_IN In2 is ≥ 0.5 mm from 3V3 and RAW_ACT |
| Panel tabs (fills sampled 0.6 / 1 / 2 / 3 mm in, 21 points along each tab, four layers) | All four tabs GND only on F.Cu, In1, In2 and B.Cu (the unfilled samples are at the corner holes' clearance) |
| Holes (distance from each hole centre to non-GND fill and copper) | Mounting holes: the nearest non-GND fill is BAT_IN 4.62 mm from (42, 98) (the hole radius is 1.6). Tracks: RAW_PROTECTED's 0.4 mm camera branch passes 0.55 mm from the (42, 59.5) hole edge, under its washer (recorded in D-S6-09; nylon hardware, ORDERING §7). Tie holes: RAW_ACT fill 0.5 mm from the (30.8, 59) hole edge on B.Cu / In2 (DRU edge clearance; the ties are nylon) |
| Tests | `test_dc_solve`, `test_r9_power`: 24 tests OK |
| Maker documents read this session | TI TPS25947 SLVSFC9C (May 2026) §6.1, §6.5, §7.3.5.3 (Eq. 7), §8.3.1, §8.4.1 (https://www.ti.com/lit/ds/symlink/tps25947.pdf); TI TPS2595 SLVSE57C §7.5, §11.1 (https://www.ti.com/lit/ds/symlink/tps2595.pdf); TI TPS2121 SLVSEA3F §7.5, §9.3.2 (Eq. 2), §11, §12.1 (https://www.ti.com/lit/ds/symlink/tps2121.pdf); TI TPS2553 SLVS841F §5 pin table, §7.1, §10.2.1.2.4, §12.1 (https://www.ti.com/lit/ds/symlink/tps2553.pdf); Diodes AP63203 DS41326 Rev 3-2 "PCB Layout" items 1–6, fSW 1100 kHz (https://www.diodes.com/assets/Datasheets/AP63200-AP63201-AP63203-AP63205.pdf); Diodes AP63301 DS42002 Rev 3-2 "PCB Layout" items 1–9, θJA 89 °C/W (https://www.diodes.com/datasheet/download/AP63300_AP63301.pdf) |

## 2. Previous findings in this dimension

This is R9's first review pass. The last power pass was R8 pass 4. Because R9 is a clean sheet, I also checked each
earlier R8 power fix that a redraw could lose.

| Item | Status on `fc3d5b34…` |
|---|---|
| R8P4-POWER-01: the stall test read the RAW_ACT neck where it carries least current; J122 had no pass line | **Closed (carried).** ORDERING §5 (l. 167) moves the judgement to the FETs and the copper beside them (≤ about 29 °C, MARGIN R1), since all three R9 necks lie at an FET (D-S10-06; my 0.1 mm cut boxes lie on Q121's drain row, Q120's source row and beside Q120's drain). It records the neck readings as information and keeps J122's ≤ 30 K line |
| R8P4-POWER-02: twelve 0805 / 1206 GND pads on 0.3 mm spokes while the DRU comment says 0402 / 0603 only; fixed in R8's records | **Not carried into R9's records:** finding 05 |
| R8P1-POWER-01: GND return and via-field currents missing from the F4 record | **Closed.** REQUIREMENTS F4 (l. 54), M3_R9 "Power", MARGIN P1-9's R9 status and R9_VALIDATION give the servo and fire-loop returns and the per-via maxima |
| R8P1-POWER-02 / R8P2-POWER-01 / R8P3-POWER-01: the stall test missing, then untestable as written | **Closed** (ORDERING §5 l. 167: steady state, bottom face, the FETs judged) |
| R8P1-POWER-03: U10's input bypass C83 17.5 mm from U10.IN; fixed by R8 D88 (1.73 mm) | **Regressed:** finding 01 (11.64 mm of track) |
| R8P1-POWER-04: U9's D9 / C82 7–8 mm from OUT; recorded by R8 as a TI §8.4.1 deviation | **Partly:** D9 now sits on U9's output vias (3.35 mm, better), but C82 is about 20 mm of copper away and R9 records no deviation: finding 01 |
| R8P1-POWER-05 / R8P3-POWER-02: single-via rail links; R8 recorded them as accepted single points (M3_R8 l. 116–131) | **Not carried:** finding 03 |
| R8P1-POWER-06: `dc_solve.py`'s docstring claimed through-hole pads join layers | **Closed** (the docstring states that only vias join layers and terminal pads are held on every layer) |
| R8P2-POWER-02: dead-end In2 BAT_IN copper to the edges, a tab and a hole | **Closed.** In2 BAT_IN is x 24.4–37.4, y 89.6–99.2, inside the outer pours' extent; no tab or hole has BAT_IN within 4.6 mm |
| R8P2-POWER-03: U13's capacitors 5.6 / 6.75 mm from its pins | **Improved:** C91 2.21, C92 4.42, C93 1.62 mm of track (R8 6.00 / 6.75 mm, measured on `cc044ea0…`) |
| R8P2-POWER-04: the build's DC gate had no seeded test | **Addressed for the judge.** `tools/test_r9_power.py` tests the DC judge's fail paths on synthetic solves: a D12 rise, a rise over R8, D_raw, a via over 1 A and an unbound or failed solve. There is no seeded narrow neck on a board copy; R8 rated that optional |
| R8P3-POWER-04: F9 distances labelled pad edge but measured centre to centre | **Consistent.** check_r9 F9-1 measures J1.1's centre to each part's nearest pad centre (D8 5.22, C80 8.90, C96 5.72, C89 4.79, C95 4.69, R166 8.38, R167 5.59, U9 13.22 mm), and the records say "from J1.1" |
| R8P3-POWER-05: a tab over In2 3V3 | **Closed:** all four R9 tabs are GND on all four layers (measured) |
| R8_VALIDATION C17: J122's GND pins solid, listed as an M2 exception | **Not listed for R9**, and its basis no longer holds: finding 04 |

## 3. Findings

### R9P1-POWER-01 (Minor, worth fixing): three power-IC bypass capacitors regressed from R8 against TI's layout rules, and R9 records none of them

**U10 (TPS2553, USB switch), input bypass C83: worst, and a fixed R8 finding undone.**
- *TI's rule.* SLVS841F pin table: IN, "connect a 0.1 µF or greater ceramic capacitor from IN to GND as close to the IC
  as possible". §12.1: "placing the 100-nF bypass capacitor near the IN and GND pins, and make the connections using a
  low-inductance trace". §10.2.1.2.4: "reduces ringing on the input".
- *History.* R8P1-POWER-03 found C83 17.5 mm from U10.IN, and R8 D88 fixed it: 1.73 mm of track, measured this session on
  R8 `cc044ea0…`.
- *R9 (measured).* U10 is at (12.6, 31.0) on B.Cu. IN U10.1 is at (11.3, 31.95), GND U10.2 at (11.3, 31.0), and EN U10.3
  (tied to VBUS) at (11.3, 30.05). C83 sits at (10.2, 28.4) and C28 (4.7 µF) at (13.05, 28.4), both on U10.3's EN branch
  (`r9_place.tsv` l. 38 / 55: "legaliser proposal").
- U10.1 is fed from the south run (y 33.5), so its only path to them is the loop U10.1 → (11.35, 33.5) → (7.25, 33.5) →
  the J3 via (7.95, 31.4) → (9.3, 30.05) → C83.1. That is 11.64 mm of 0.3 mm track (C28.1: 14.04 mm), 19.15 mΩ.
- Inference: about 4–5 nH by the microstrip estimate, against R8's about 0.7 nH.

**U11 (TPS2121, logic mux), USB input IN1 bypass C98.**
- *TI's rule.* SLVSEA3F §11: "Bypass capacitors on these pins should be placed as close to the device as possible".
  D-S6-06 cites the rule as met ("U11's input / output capacitors at their pins").
- *R9 (measured).* C98.1 (36.225, 62.8) is 5.29 mm of 0.3 mm track from U11.7 (39.3, 65.825). USB_LIMITED's corridor
  (D-S7-16) puts C98 on the trunk before the pin. R8: 1.73 mm.

**U9 (TPS25947, battery eFuse), output bypass.**
- *TI's rule.* SLVSFC9C §8.3.1: "Connect a low ESR capacitor larger than 1μF at the OUT pin very close to the device".
  §8.4.1: "TI recommends to add a ceramic decoupling capacitor of 1μF or greater between OUT and GND. These components
  must be physically close to the OUT pins."
- *R9 (measured).* The only RAW_PROTECTED capacitors are C82 (22 µF), C97 (1 µF, at U11) and C71 (100 nF, at U7).
  C82.1 (40.9, 72.4) is 17.76 mm from U9.6 (40.3, 90.15), centre to centre. The copper path is about 20 mm: the 0.3 mm
  B.Cu entry, two vias, then the F.Cu pour; dc_solve gives U9:6 → C82:1 8.08 mΩ.
- *History.* R8 had D9 / C82 7.3 / 8.1 mm of track away, and recorded it as a §8.4.1 deviation (M3_R8 l. 122–124).
  R7 had C82 2.25 mm away.
- R9 put D9 (the clamp) on U9's output vias, 3.35 mm from U9.6, which addresses the negative-transient half of §8.4.1.
  But it moved C82 to the trunk's far end (`r9_place.tsv` l. 54), and no R9 record mentions the deviation.

**Impact.**
- No requirement fails; each is an improbable-fault margin (Inference).
- USB is bench-only. D4 clamps VBUS, and the cable's µH dwarfs the added nH, but U10.IN's absolute maximum is 7 V
  (SLVS841F §7.1) on a 5 V input.
- D9 now clamps U9's OUT negative transient close to the pin.
- What makes this a finding: the R8 fix for U10 was lost in the clean sheet, D-S6-06's compliance sentence is false for
  C98, and the U9 deviation R8 recorded has vanished from the R9 list the owner is asked to accept.

**Fix.**
- **U10 (cheap):** put C83 on U10.1's run with its GND pad at U10.2 (R8 D88's recipe; the legaliser picks the spot west
  of U10). Alternatively, redraw the VBUS tee so that the J3 run reaches U10.1 through C28.1 / C83.1 first. Then re-run
  check.sh and the USB_LIMITED row.
- **C98:** move it beside U11.7 / U11.6 if a legal spot exists. Otherwise record it.
- **C82:** record the §8.4.1 deviation as M3_R8 did, with D9's improvement.
- Correct D-S6-06's TI sentence. TI's capacitor sentence is §11; §12.1 is "short wide traces".

### R9P1-POWER-02 (Minor, worth fixing, records): U9's current limit is 3.96–4.84 A, not the 2.2 A the records carry, and R9's RAW_PROTECTED sizing rests on the wrong figure

**What the board has.**
- R84 = 750R 0.1 % (`battery_entry.kicad_sch` l. 1915; BOM C861551 RT0603BRD07750RL).
- TI SLVSFC9C §6.5 gives the overcurrent threshold at RILM = 750 Ω as **3.960 / 4.452 / 4.840 A**, and §7.3.5.3 Eq. 7
  gives RILM = 3334 / ILIM. At RILM = 1.65 kΩ it is 1.800 / 2.028 / 2.200 A.
- R84 was 1.65 kΩ through R5 and became 750 Ω in R6 (commit 3b215ba, `battery_entry.kicad_sch`). No record found gives
  the reason.

**What the records say.**
- R3_VALIDATION l. 252: "current limit 1.80–2.20 A".
- R8_DECISIONS D46 (l. 1158): "U9 limits at 1.80–2.20 A, R3_VALIDATION".
- M3_R8 l. 96–97 and l. 130: "24.6 °C at U9's 2.2 A limit", "19 °C at U9's 2.2 A limit".
- R9 inherits this as the basis of its RAW_PROTECTED layout. R9_DECISIONS D-S6-05 (l. 936): "U9's current limit (R84)
  through one via was R8's choice; two vias halve each barrel's share". `r9_power.py` l. 365–366 says the same.
- No R9 record gives U9's limit or an IPC-2152 check of RAW_PROTECTED at all. R8 sized its trunk explicitly.

**Why 750 Ω probably makes sense (Inference), and what the copper sees.** The downstream limiters cap the normal fault
states:
- U7 (TPS259570, R70 1.78 kΩ): 1.09 / 1.17 / 1.24 A (SLVSE57C §7.5).
- U11 (TPS2121, R86 80.6 kΩ): 1 / 1.5 / 2 A (SLVSEA3F §7.5 at 80 kΩ; Eq. 2 gives 1.49 A typical).
- Their sum, 3.24 A, is below U9's 3.96 A minimum, so U9 acts only on a fault on RAW_PROTECTED itself.

R9's RAW_PROTECTED, at the IPC-2152 fit (no plane credit):

| Copper | Path | Rise |
|---|---|---|
| U9.6 entry, 0.3 mm B.Cu, 1.1 mm from the end of U9's 2.4 mm OUT bar to the column x 42.3 | → two 0.5 / 0.3 vias (42.3, 88.0 / 91.3) → F.Cu pour, ≥ 1.45 mm (D-S8-09) | 21.7 °C at the 1.54 A worst steady load and 96 °C at 3.24 A as a long conductor. The entry is too short for the fit; conduction into the bar and vias governs it (Inference) |
| U11 branch, 0.4 mm | → one 0.6 / 0.3 via (39.3, 68.2) | 26 °C at U11's 2.0 A maximum; the via then carries 2.0 A |
| Camera branch, 0.4 mm F.Cu, 44 mm | → one 0.6 / 0.3 via (42.15, 31.5) | 10 °C at U7's 1.24 A maximum; the via then carries 1.24 A |

- CAM_5V's single via (40.75, 45.4) can see about 1.9 A in a camera-side overload before U7 limits: 8.4 V × 1.24 A ×
  0.9 / 5 V (Inference).
- A resistive fault on a branch drawing between about 1.5 and 3.96 A is not limited by U9 at all. The 0.4 mm camera
  branch would then rise about 100 °C by the fit (103 °C at 3.96 A).

**Impact.**
- Normal loads are well inside the copper's capacity. The coordination looks sound.
- But the recorded limit is wrong by a factor of 2.2. The step-6 rule "barrel current ≤ 1 A" is met only at load
  currents. R9 has no recorded sizing of a battery-fed rail that AGENTS §3 asks to size per IPC-2152.
- The soft-fault exposure of the 44 mm camera branch is an improbable-fault margin, not a defect.

**Fix (records; no copper required).**
- State U9's limit as 3.96–4.84 A (SLVSFC9C §6.5, Eq. 7) in D-S6-05 and the r9_power.py comment. Note in M3_R9 that
  R8's "2.2 A" figures (D46, M3_R8) were R5's R84.
- Record RAW_PROTECTED's IPC-2152 check at the coordinated limits (U7 1.24 A, U11 2.0 A, the shared entry and pour
  ≤ 3.24 A), with U9's 3.96–4.84 A as the fault case on the net itself.
- Accept the camera branch's soft-fault exposure as an improbable-fault item, or widen it where it runs free.

### R9P1-POWER-03 (Minor, worth fixing, records): seven single-via rail links on lose-the-vehicle chains are undocumented

**Requirement.** MARGIN_PRESCRIPTION R15 (l. 307): "No undocumented single point may exist on any lose-the-vehicle
chain". R8 documented its single-via rail links as accepted single points, after R8P1-POWER-05 and R8P3-POWER-02
(M3_R8 l. 116–131). R9's records have no such list: "single" appears in M3_R9 only for the P7 GND pockets.

**Measured.** I removed each of the 97 vias on power nets in turn, in memory, and rebuilt KiCad's connectivity. These
are the vias that leave a pad unconnected and carry a rail. All are 0.6 / 0.3 mm vias.

| Via | What it alone carries | Load |
|---|---|---|
| 3V3 (37.6, 78.9) | the buck output into the In2 3V3 finger: the whole 3V3 domain (MCU, flash, sensors' filter, GNSS, radio) | ≤ about 0.5 A; it carries the whole 3V3 solve current |
| RAW_PROTECTED (39.3, 68.2) | all of U11's battery input (pin 2, IN2_BAT in the netlist; `r9_power.py` calls the via V_IN1) and C97 | 0.50 A at 0.5 A; ≤ 2.0 A at U11's limit |
| VLOGIC (38.5, 69.6) | the hold-up C84, F6's ≥ 0.15 s ride-through | 0.50 A at 0.5 A |
| RAW_PROTECTED (42.15, 31.5) | the camera feed into U7 | 1.00 A at 1 A |
| CAM_5V (40.75, 45.4) | J9.1, the camera's 5 V | 1.00 A at 1 A |
| 3V3A (22.0, 50.75) | U1.20 / U1.21 (VREF+ / VDDA) to the 3V3A B.Cu trunk and its capacitors | mA |
| USB_LIMITED (18.25, 39.75) and (26.05, 51.15), in series | the USB logic supply (bench only) | 0.50 A each |

- R9 improved one of R8's links: U9.6's output now has two vias.
- The other 39 single vias are one-per-part bypass and pull-up taps, VCAP1 (24.25, 39.5), VCAP2 (13.0, 38.8),
  signal-level links (R122's ACT_EN pull-up tap (37.26, 80.9), the sense taps), the bench-only VBUS vias and the camera
  translator's mA supply. They are inherent to bottom-side decoupling and of the class R8 did not list.

**Impact.**
- Each barrel carries its load with margin. A 0.3 mm / 20 µm barrel at 1 A rises a few °C (Inference, as R8).
- The concern is failure mode: one cracked barrel removes the rail.
- For the 3V3 feed, U11's input and the hold-up, that loses the primary computer, and recovery then rests on the backup
  altimeter (FMEA's independent channel).
- Improbable, but R15 requires it documented.

**Fix (records).** Add M3_R9's equivalent of M3_R8 l. 116–131: these vias, each barrel's load and "accepted single
point (MARGIN R15)". Optionally, add a second via at the 3V3 feed, U11's input and the hold-up where the legaliser finds
a spot. The finger is 1.49 mm wide, so a second 3V3 feed via must keep D-S8-02's narrow-region rule.

### R9P1-POWER-04 (Minor, worth fixing): J122's four GND pins are solid on three layers, an M2 thermal-relief exception R9 does not list, and its R8 basis does not hold on R9's copper

**Requirement.** REQUIREMENTS M2 (l. 75): "Through-hole GND pins use thermal reliefs wherever their spokes are not
starved (exceptions listed in M3_R4 §2; R8: R8_VALIDATION C17)". Every exception is a deviation for the owner's dated
acceptance.

**Board (measured).**
- J122.3 / .6 / .9 / .12 carry a pad-level FULL connection, inherited from R7 / R8's J122 pads. They join the F.Cu,
  In1 and B.Cu GND pours solid (J122.3 also In2).
- ORDERING §5 (l. 94) mentions it as a hole-fill instruction ("its GND pins solid on F.Cu, In1 and B.Cu … preheat").
- R9_VALIDATION part C has no row for it. R8 listed it as C17 (R8_VALIDATION l. 494), on the measured R8 fact that
  "J122.3 would be starved on F.Cu".

**R9 trial (scratch copy, deleted).**
- I set the four pads to inherit the zone setting (THT relief: 0.5 mm gap / 0.5 mm spokes on F / B, 0.25 / 0.4 mm on
  In1), refilled natively and ran `kicad-cli pcb drc`.
- No starved_thermal. The only DRC items were the copy's missing footprint-library table.
- Spokes per pin: F.Cu 4, In1 4, B.Cu 2. In2 has none, since the pins sit in the RAW_ACT region's antipads; J122.3 has 2.

**Cost of reliefs (Calc).**
- Per pin: 4 F.Cu spokes 0.5 × 0.5 mm (0.12 mΩ in parallel) ‖ 4 In1 spokes 0.4 × 0.25 mm (0.09 mΩ) ‖ 2 B.Cu (0.25 mΩ)
  gives about 0.04 mΩ.
- That is 0.08 mV and 0.16 mW per pin at 1.925 A. J1.2 already returns the whole board's current, about 9 A, through
  14 such spokes (M3_R8's conduction argument).

**Impact.**
- No electrical issue either way.
- Solid joints to three full GND planes make J122's hand / selective-solder hole fill harder on the servo header that
  carries the return. ORDERING already asks for inspection.
- The real defect is an unlisted M2 exception with an obsolete basis.

**Fix.** Preferred: drop the four FULL overrides in the R9 build so that the pins take the zone's THT relief, then
re-run the servo GND return and check.sh. Otherwise, list them in R9_VALIDATION part C with the R9 measurement (not
starved: 4 / 4 / 2) and a current-based reason for the owner.

### R9P1-POWER-05 (Minor, not worth fixing): R8P4-POWER-02's records fix did not carry into R9

**The rule as built.**
- `m3.kicad_dru` l. 128–129 still says the rule puts only "two-pad 0402/0603 parts" on spokes and "Other GND SMD pads
  stay solid".
- In fact the rule applies to every SMD GND pad with a local THERMAL override. R9 has the same twelve 0805 / 1206
  capacitor GND pads on 0.3 mm spokes as R7 / R8: C6.2, C7.2, C8.2, C9.2, C10.2, C11.2, C80.2, C96.2, C150.2, C151.2,
  C310.2 and C91.2.
- R8's fix pass 4 named this in M3_R8 "Ground" (l. 194–201). M3_R9 has no equivalent.

**Impact.**
- Electrically negligible (Inference, about 0.05 nH and 0.1 mΩ per pad).
- In R9 the hot-loop returns do not even depend on the spokes. U2's C6.2 has a 1.0 mm strap to U2.4. C8.2 / C9.2 and
  C150.2 / C151.2 have straps and their own vias.
- check_r9 K-copper's thermal policy passes (86 small pads).

**Fix.** One line in M3_R9 "Ground", as M3_R8's. The DRU comment can stay if `check_actuators` pins the file.

## 4. Checked, no finding

**7.7 A path and D12.** Reproduced at 0.1 mm (§1), and the 0.05 mm evidence is bound.
- There is no series via. BAT_IN runs J1.1 → B.Cu pour → Q120's drain, carried 100 % on B.Cu at the cut. ACT_FET_S is
  the B.Cu bridge plus the F.Cu plate over 8 vias of ≤ 0.25 A. RAW_ACT runs B.Cu from Q121's drain to J122's RAW pins
  directly, with In2 and F.Cu in parallel.
- The necks sit at Q121, beside Q120 and inside Q120 (D-S10-06). Each is set by the FET's own pins, and the stall test
  judges those parts.
- The RAW_ACT current crowds to 3.53 A/mm at the spine-to-row inside corner (28.58, 63.41; 0.05 mm evidence). The
  equipotential cuts there are wider than the neck.
- J122's RAW row is as in §1.

**GND returns.**
- The servo return is 0.32 mΩ, reproduced (§1; 151 vias, max 0.29 A). It runs south from J122 to J1.2, away from U1 and
  the sensors.
- The fire-loop return is 0.81 mΩ. Its two vias at Q124 carry 1.23 / 1.00 A for ≤ 20 ms; adiabatically a 0.3 mm /
  20 µm barrel at 1.23 A rises about 0.4 K in 20 ms (Calc). At a shorted igniter, about 3.9 A through R134 and about
  1.7 A in that via, it is about 0.7 K.
- J1.2's spokes (§1) carry the whole return. They are short, and conduction judges them as R8's were.

**Hot-plug and input protection (F9).**
- The model re-run is identical (§1). From its sweep, the premise holds to a feed of about 19 nH: 9.2 V/µs × ratio
  ≤ 10 V/µs, interpolated (Inference). The estimate is 3.2 nH.
- The TVS loop is short: J1.1 → D8.1 (27.15, 89.2), and D8.2 → a direct B.Cu track to J1.2, about 5 × 5 mm.
- C80.2 and C96.2 each have a GND via 1.40 mm away.
- The hand-soldered battery pins keep the project's 0.3 mm hand-solder gap (the DRU's RAW_ACT-pin rule) to foreign
  outer pours. J1.1 (BAT_IN) is 0.326 mm from the masked F.Cu GND pour (0.251 mm on In1, the inner antipad). J1.2's bare
  bottom ring is 0.305 mm from the masked BAT_IN B.Cu pour, which wraps its south side and takes two of its spokes. A
  bridge there would short the pack, but it needs a mask failure, and ORDERING §5's first power-up (USB, then a
  current-limited bench supply, never a battery first; l. 151) exposes it safely.
- R166.2 (the damper) returns through a 1353 mm² F.Cu GND island with 136 vias. Its nearest via is 4.24 mm away,
  negligible against 0.33 Ω at the 35 kHz harness resonance (Inference).
- U9.8 has a GND via 1.1 mm away. U9's IN abs max is max(−15 V, VOUT − 21 V) and SR_IN(F) 10 V/µs (SLVSFC9C §6.1), as
  F9 and ORDERING §5 use.
- U9's IN and OUT bars each take one 0.3 mm entry. TI §8.4.1 asks for plane and thermal vias for dissipation and sense
  accuracy, but U9 dissipates about 0.07–0.1 W at 1.54 A (28.3 mΩ typical, Calc), as R8 judged.

**Bucks.**
- *U2 (AP63203, 1.1 MHz).* C6.1 is 1.81 mm from VIN; the GND side is a 1.0 mm strap to U2.4, with a via 1.21 mm from
  U2.4. SW runs 1.0 mm into L1.1. FB senses the In2 finger on its own via. In2 and In1 are GND under U2 / L1 (probed).
  This matches DS41326 items 2–5.
  - Information: C5 (BST–SW, 0402) and the SW stub to (38.6, 74.6) lie over the In2 3V3 finger (probed (37.2, 73.85):
    3V3), about 0.1 pF of switch-node coupling into 3V3 (Inference). Negligible.
- *U8 (AP63301).* This is R8's maker layout moved with the block. C72 is 2.91 mm of 1.0 mm track from VIN, U8.4 → C72.2
  runs on a 0.4 mm strap, and In2 / In1 are GND under it.
  - U8.4's nearest GND via is still 2.95 mm (DS42002 item 7). This is R8 pass 1's "optional improvement", unchanged.
  - Junction about 100–105 °C at a 1 A camera in a 70 °C bay on the single-layer θJA, as R8 found (Inference).

**Decoupling** (track or centre distances; R8 on `cc044ea0…`):

| Part | Capacitor(s) | Distance |
|---|---|---|
| U1 | VDD caps | 0.91–2.07 mm |
| U1 | VCAP | 2.15–2.21 mm |
| U1 | VDDA (C21) | 1.47–1.76 mm |
| U3 | — | 1.87 mm |
| U4 | — | 1.09–1.52 mm |
| U5 | — | 1.44–2.63 mm |
| U12 | C100 / C93 | 1.21 / 1.73 mm |
| U13 | C91 / C92 / C93 | 2.21 / 4.42 / 1.62 mm of track |
| U9 IN | C88 | 2.10 mm (as R8) |
| U10 OUT | C86 | 2.24 mm |
| U11 battery input | C97 | 2.05 mm (via under the pin) |
| U7 IN | C71 | 4.67–5.17 mm of track (R8 4.08–4.58). TPS2595 SLVSE57C §11.1 asks for ≥ 0.01 µF "closest to the IN and GND terminals"; behind a 77 mΩ, 44 mm branch the input spike on a trip is about 1.24 A × √(25 nH / 100 nF) ≈ 0.6 V, against a 20 V absolute maximum (Inference). Information |

U10, U11.7 and U9's OUT are in finding 01.

**In2.**
- Each region is one island. D-S6-03's plan is as built.
- RAW_ACT to 3V3 is 0.30 mm for about 33 mm on the inner layer, 8.4 V to 3.3 V. That is far above IPC-2221B's internal
  minimum and inside JLC's electrical test (Inference).
- The 3V3 finger is the buck's only path (finding 03 lists its via). It is about 8.7 mΩ (Calc); 0.5 A drops about
  4 mV.

**Supply drops.**
- Every row is under 80 mV at its load. The largest is RAW_PROTECTED → U7, 77 mV at 1 A.
- USB_LIMITED is 83.02 mΩ (42 mV at 0.5 A). Its route through U1's interior keeps ≥ 0.2 mm from every other copper item
  (0.206 mm via to NRST's via, both layers). That is electrically benign: about 0.3 pF to NRST against C24's 100 nF
  (Inference). Its beauty is the routing reviewer's call.

**Thermal.**
- The FETs' drain copper is smaller than R8's: Q120's BAT_IN is 153 (B) + 115 (In2) + 60 (F) mm², against R8's 217.5 +
  229.8 + 92.9; Q121's RAW_ACT is 178 + 242 + 120 mm².
- At about 0.34 W per AON6403 (MARGIN), the junction rise sits near R1's 29 °C line (Inference, as R8 pass 2 estimated
  18–31 °C). The ORDERING §5 stall test judges exactly that.
- C84 (OS-CON, 105 °C) sits on the top over Q121. That is fine at the bay's 70 °C plus the stall rise (Inference).
- The test-pad and hole checks are in §1.

**Records checked against the board.**
- F4's, F7's (1.651 A = 7.4 / 4.4821 Ω) and P1-9's R9 figures.
- M3_R9's supply table, for the seven rows re-solved.
- R9_VALIDATION's hot-plug row and F9-1's figures.

## 5. Not verified

- I did not re-run the 0.05 mm grid. The 0.1 mm run reproduces the build gate, and the 0.05 mm evidence is bound to the
  same SHA-256.
- Supply rows other than the seven re-solved were read from `dc_summary.txt`. The fire-loop rows, the fire-loop GND
  return among them, were read from `step10_evidence/dc/`.
- The J122 arm's four-pin current split is bounded (single-pin solves and a geometric cut), not solved with per-pin
  current sinks. `dc_solve.py` has none.
- Every inductance, coupling, temperature-rise (beyond the IPC fit), leakage and failure-mode statement not marked
  measured is an Inference or Calc. I did no bench work.
