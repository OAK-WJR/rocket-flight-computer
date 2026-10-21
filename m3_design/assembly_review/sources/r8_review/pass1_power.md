# R8 review pass 1: power, thermal and hot-plug

**Board:** `m3_design/assembly_review/m3.kicad_pcb`, SHA-256 `429b6db4dc95c1a0fd3e736625c416c20fa0e7fc72f6f6c9c576003340dc1987`
(checked before and after this review; unchanged). Read-only review: no repository file changed except this report.
Measurements were made with KiCad 10.0.6 pcbnew on a scratch copy of the board, using scratch scripts. The methods are
described below so they can be repeated.

**Result: 0 Critical, 0 Major, 6 Minor (3 worth fixing).** The 7.7 A copper reproduces the record and meets D12. The
In2 map, the buck layouts, the decoupling and the F9 input-node geometry are sound. The findings are record gaps (the
servo GND return and the via-field currents are not in the F4 record; the bench stall test is missing from ORDERING
§5) and three layout regressions from R7 at small parts (U10's input bypass, U9's output capacitor and clamp, and
single-via supply links). None of them is unsafe.

## 1. What was run

| Check | Result |
|---|---|
| `tools/check.sh` (full gate) | exit 0: DRC 0, unconnected 0, parity 0, ERC 0; audit, silk, check_r8, route_check r8 (0 failing, 3 allowlisted), check_actuators, fit_check all OK |
| `tools/run_dc.sh <copy> <out> 0.1` | RAW_ACT 1.45 mΩ, neck 5.90 mm F.Cu, 17.6 °C; BAT_IN 0.42 mΩ, 6.86 mm B.Cu, 14.8 °C; ACT_FET_S 0.19 mΩ, 4.77 mm B.Cu, 22.5 °C. All OK against D12, and equal to D67's 0.1 mm figures. The record's 0.05 mm figures (5.94 / 7.00 / 4.97 mm) are within the 3 % grid difference D49 gives. No neck level was discarded by the < 1 mm filter |
| Per-via barrel currents (`dc_solve.py` copy that prints `g·ΔV` for each via link) | RAW_ACT: 66 vias, max **0.89 A** at (11.3, 85.6), F.Cu–In2; 8 vias over 0.5 A, none over 1 A. BAT_IN: 15 vias, max **0.70 A** at (21.25, 100.9), In2–B.Cu; 5 over 0.5 A |
| Servo GND return (`dc_solve.py` copy, `--net GND --source J122:3,6,9,12 --sink J1:2`, clipped to y ≥ 64, 0.2 mm grid, track-width check skipped) | R ≈ **0.74 mΩ** (5.7 mV, 44 mW at 7.7 A). In1 carries 85 % mid-path, In2 9 %, B.Cu 6 %, F.Cu 1 %. Max GND via current 0.39 A. The narrowest cut is J1.2's thermal spokes (see R8P1-POWER-01) |
| J122 arm between the + pins (copper across y 78.24 / 75.70 / 73.16) | F.Cu 3.40, In2 4.40, B.Cu 3.40 mm at every gap: ≥ 10 mm 35 µm-equivalent for ≤ 5.8 A |
| Pad-to-pour contact (ring sampling at 0.12 mm) and spoke count | J1.1 BAT_IN solid on F/In2/B; Q120/Q121 source and drain pads solid; J122 + pins and J124.2 solid; J1.2 GND 4 × 0.5 mm spokes on F and B, 4 × 0.4 mm on In1, none on In2 (J1.2 sits in the In2 BAT_IN island) |
| Zone map (all zones, pad-connection mode, islands) | In2: GND 1 island (2396 mm², THT thermal), 3V3 1 (1512 mm², thermal), RAW_ACT 2 (west 288, J122 finger 58 mm², full), BAT_IN 1 (506 mm², full). Outer power pours full. GND_F / GND_B: thermals on THT pads only |
| Tests | `test_dc_solve`, `test_r8_power`: 10 tests OK |
| Maker documents read | TI TPS2553 SLVS841F (Aug 2016) §7.1, §10.2.1.2.4, §12.1 (https://www.ti.com/lit/ds/symlink/tps2553.pdf); TI TPS25947 SLVSFC9C (May 2026) §6.1, §6.7, §8.4.1 (https://www.ti.com/lit/ds/symlink/tps25947.pdf); Diodes AP63300/AP63301 DS42002 Thermal Resistance (θJA 89 °C/W TSOT26), Recommended Operating TJ 125 °C, Layout items 1–9 (https://www.diodes.com/datasheet/download/AP63300_AP63301.pdf) |

## 2. Previous findings in this dimension (R7 → R8)

This is R8's first review pass. These are the R7 power and hot-plug items that carry over:

| R7 item | Status on `429b6db4…` |
|---|---|
| C1: 7.7 A neck rise 38 / 30 / 44 °C, accepted as estimated | **Closed by R8 copper.** D12's limits are met and I reproduced the figures (§1). P1-9's 10 mm is still not met as written (owner-delegated D12) |
| F9 premise broken (U9 71 mm and D8 80 mm from J1) | **Restored (layout verified).** D8, C80, C96, C89, C95, R166 and R167 lie within 4.6–10.6 mm of J1.1 (nearest pad), on the BAT_IN pours. U9's feed is 0.5 mm B.Cu on x 41.25: over In2 BAT_IN for y 102.4–100.3 and In2 GND for y 100.3–87.6 (rendered and checked). The 4.2 nH microstrip estimate is plausible. D76's model is an Inference, and the bench test (ORDERING §5) probes U9 IN at C88. U9's GND pin is downstream of the input capacitors' GND, as seen from J1.2, so the reversed-plug charging current does not flow under it (Inference) |
| "the servo GND return (planes) was not analysed" (M3_R7) | **Still not in the R8 record.** Measured here: R8P1-POWER-01 |
| P1-9 R8 status: "via fields at the layer changes are not assessed for current" | **Measured here** (≤ 0.89 A per via). Recording it is part of R8P1-POWER-01 |

## 3. Findings

### R8P1-POWER-01 (Minor, worth fixing): the F4 record leaves out the servo GND return and the via-field currents

- **Requirement.** REQUIREMENTS F4 says "size and independently solve the final copper … at this load, including
  pad/via transitions and necks". MARGIN P1-9's prescription covers "RAW and servo GND". MARGIN P1-9's R8 status says
  "the via fields at the layer changes are not assessed for current". M3_R7 noted "the servo GND return (planes) was
  not analysed", and R8 re-placed the battery band without solving it either.
- **What `run_dc.sh` solves.** It solves only the supply side (RAW_ACT, BAT_IN, ACT_FET_S). Its neck method ignores
  via fields and the 0–3 % of the drop next to each terminal.
- **Measured (this review):**
  - **GND return.** J122:3,6,9,12 → J1:2 is about 0.74 mΩ (0.2 mm grid, so the result is an upper bound: KiCad draws
    J1.2's spokes at 45°, and the solver's 4-connected grid only partly joins diagonal spokes). That is 5.7 mV at 7.7 A.
    In1 carries 85 %. No GND via carries more than 0.39 A.
  - **The whole board return** (7.7 A servo current plus logic) enters J1.2 (25.54, 110.4) through thermal spokes:
    4 × 0.5 mm on F.Cu, 4 × 0.5 mm on B.Cu and 4 × 0.4 mm on In1 (J1.2 has no In2 connection, because it sits in the
    In2 BAT_IN island). Shared evenly, that is about 5.4 mm of 35 µm copper.
  - **What the tool reports.** On the GND solve, `--necks` puts the neck at those spokes: 0.91 mm at level 0.045, cut
    box (24.5–26.5, 109.2–111.6), and a meaningless IPC "146.8 °C". The long-conductor fit does not apply to
    0.25–0.5 mm-long spokes bonded to the pin. A conduction estimate gives well under 1 K (Inference).
  - **Via fields.** The maximum barrel current is 0.89 A at RAW_ACT via (11.3, 85.6) and 0.70 A at BAT_IN via
    (21.25, 100.9). A 0.3 mm / 20 µm barrel treated as a 1.0 mm × 20 µm external conductor rises about 3 °C at 0.89 A
    by `ipc2152.py`'s fit (Inference).
  - **Sink model.** `run_dc.sh` holds J122:2,5,8,11 at one potential, so the arm between the + pins carries no
    current in the solve. In reality the arm carries up to 5.8 A. It is ≥ 10 mm 35 µm-equivalent on three layers
    (§1), so it is fine, but the model does not show it.
- **Impact.** The copper is adequate: the return is about 0.7 mΩ, the vias are ≤ 0.9 A each and the spokes are
  short. But F4 / P1-9 coverage is incomplete in the record. Anyone who later runs the D12 neck method on the return
  will find J1.2's spokes as the "neck".
- **Fix (records and tools only, no copper):**
  - Add a GND-return row to `tools/run_dc.sh` and M3_R8 §"DC solve" (0.05 mm, so that the 45° spokes resolve), and
    state how J1.2's spokes are judged: short spokes, a conduction estimate, and M2's THT-GND thermal rule.
  - Add the per-via maximum currents to M3_R8 and to MARGIN P1-9's R8 status, replacing "not assessed".
  - Note the equipotential-sink caveat for J122's arm.

### R8P1-POWER-02 (Minor, worth fixing): the F4 thermal-camera stall test is cited as "the check" but is not in ORDERING §5

- **Where it is cited.** M3_R8 l. 160 says "the thermal-camera stall test (F4, ORDERING §5) is the check". MARGIN
  l. 196 says the same, and REQUIREMENTS F4 says "Perform a thermal-camera stall test".
- **What ORDERING §5 has.** It contains no such test (grep for "stall", "thermal"). The only stall in it is "a held
  servo stall" inside the pyro no-fire gate (l. 156). R7's ORDERING had none either. The last defined procedure is
  M3_R5's bring-up gate 1, written for R5's locations.
- **Why it matters.** Every D12 rise is a no-plane-credit Inference, and this test is the only measurement planned
  for it. R8's hot spots are new, and three of five are on the bottom face:
  - ACT_FET_S bridge, B.Cu x 11.8–14.15, y 98.05–104.5;
  - BAT_IN neck, B.Cu x 17.25–20.25, y 98.65–104.5;
  - Q120 (16.38, 101.72) and Q121 (8.0, 103.0), bottom;
  - RAW_ACT neck, F.Cu x 20.25–21.8, y 80.65–86.25;
  - J1.2's spokes.

  A test written from the R5 text would image the wrong places.
- **Fix.** Add a bench item to ORDERING §5:
  - four servos (or an electronic load) at 7.7 A on J122 for the firmware's stall limit;
  - thermal camera on both faces at the coordinates above;
  - pass criteria against D12's estimates (17.5 / 14.5 / 21.5 °C rise, upper bounds);
  - RAW_ACT ripple at C121.

### R8P1-POWER-03 (Minor, worth fixing): U10's 100 nF input bypass C83 is 17.5 mm of track from U10.IN (R7: 1.8 mm), against TI's layout rule and R8_DECISIONS D42

- **TI's guidance.** SLVS841F §12.1: "placing the 100-nF bypass capacitor near the IN and GND pins … low-inductance
  trace". §10.2.1.2.4: "0.1-µF or greater ceramic bypass … as close to the device as possible … reduces ringing on the
  input".
- **The R8 record.** D42 (R8_DECISIONS l. 1060) records "TPS2553 §12.1: U10's bypass, unchanged".
- **Measured on R8:**
  - C83 sits at (12.0, 26.0) B, placement basis "seed" (`r8_place.tsv` l. 81). U10 is at (12.4, 35.4) B.
  - C83.1 reaches U10.1 IN (11.1, 36.35) along 0.3 mm B.Cu: (11.225, 26.0) → (7.95, 26.0) → (7.95, 36.85) →
    (10.6, 36.85) → (11.1, 36.35). That is 17.5 mm, about 6 nH over In2 (Inference).
  - C28 (4.7 µF, (9.5, 41.8)) is 8.65 mm of track away.
  - In R7, C83 (14.1, 82.15) F sat 1.8 mm from U10 (15.0, 80.6) B.
- **Impact.** USB is a bench-only feed (F9). U10's IN pin is rated to 7 V absolute maximum (SLVS841F §7.1). A
  current-limit or short transient now rings on the IN pin with no local HF bypass. This is an improbable-fault
  margin, and D42's compliance statement is false for R8.
- **Fix.** Move C83 beside U10 pins 1/2 on the bottom, with its VBUS pad on the y 36.85 run into U10.1 and its GND
  pad toward U10.2 (for example near (10.0, 36.0), rotation 90; the legaliser decides). Correct D42.

### R8P1-POWER-04 (Minor): U9's output clamp D9 and bulk C82 sit on a 5.5 mm stub beyond the trunk via, 7–8 mm from OUT (R7: C82 2.25 mm)

- **TI's guidance.** SLVSFC9C §8.4.1 asks for a protection Schottky and "a ceramic decoupling capacitor of 1 μF or
  greater between OUT and GND … physically close to the OUT pins … minimize the loop area". §6.1 limits OUT to ≥ −0.3 V
  (−0.8 V for pulses under 1 µs).
- **Measured on R8.** U9.6 (41.75, 85.5) runs 1.8 mm of 0.3 mm B.Cu to the only trunk via (41.75, 83.7). The B.Cu
  column then continues south to D9.1 (43.51, 80.0) and C82.1 (40.95, 78.2): 7.3 and 8.1 mm of track from OUT. Both
  parts hang beyond the node where the load current leaves for F.Cu. D9.2's GND via is at (43.51, 74.2), so the clamp
  loop is about 11 mm long. In R7, C82.1 (13.45, 40.35) sat 2.25 mm from U9.6 (11.2, 40.35). D9 was already about
  9 mm away in R7.
- **Impact.** After a hard short downstream of U9 (fast trip at 2 × ILIM, ≤ 500 ns response, §6.7), the stub's
  inductance (roughly 2 nH, Inference) adds L·di/dt to D9's forward drop against the −0.8 V pulse limit. The camera
  has its own eFuse U7, so a hard short behind U9 is an internal board fault: an improbable-fault margin.
- **Fix.** If U9's neighbourhood is reworked, put C82, and ideally D9, beside U9.6, with the trunk via after them.
  Otherwise record the deviation from §8.4.1. Not worth a placement change on its own.

### R8P1-POWER-05 (Minor): single-via series links carry whole supply rails

- **Measured on R8.** Each of these vias is the only copper joining its two sides:
  - **3V3:** the In2 3V3 plane (1512 mm², every 3V3 load) is fed from the buck output line only through via
    (34.4, 69.65), at the region's south-east corner (`r8_power.py` l. 324). The load is about 0.5 A peak.
  - **RAW_PROTECTED:** U9.6 to the F.Cu trunk through via (41.75, 83.7) (l. 261). It carries all logic and camera
    current: 1.54 A steady worst case, 2.2 A at U9's limit (D46).
  - **Camera feed:** via (42.15, 25.6) into U7 (≤ 1 A) and the CAM_5V via (40.75, 41.4) to J9.1 (1 A).
  - **Hold-up:** VLOGIC via (35.5, 66.6) to the hold-up C84.
- **Capacity is adequate.** By `ipc2152.py`'s fit with the barrel as a 1.0 mm × 20 µm conductor: about 9 °C at
  1.54 A and 19 °C at 2.2 A (an upper bound, Inference).
- **The concern is failure mode.** One cracked barrel removes the rail. That is the single point MARGIN R15 asks to
  document, and P1-9 prefers parallel vias ("one cracked via is graceful degradation").
- **Fix (optional).** A second via at each link. RAW_PROTECTED's needs care: R92.1 (top, x 42.075–42.875) leaves no
  room at (41.75, 82.4–83.0). The 3V3 feed needs TP83's 1.0 mm bare-pad zone or the region corner moved. Alternatively,
  record these links as accepted single points. Improbable fault, so not worth a rework by itself.

### R8P1-POWER-06 (Minor): `dc_solve.py`'s docstring says through-hole pads join their layers, but only vias do

- **Code.** `tools/dc_solve.py` l. 13 says "Through-hole pads join their layers outright". In the code, layers are
  linked only in the via loop (l. 303). Pads are rasterised per layer (l. 270) and linked only when they are terminals
  (fixed potential).
- **Effect.** A non-terminal through-hole pad on the solved net, such as J124.2's 1.6 mm barrel on RAW_ACT, is not an
  inter-layer conductor in the solve. The recorded resistances and via currents are therefore slightly pessimistic,
  which is the safe direction.
- **Fix.** Correct the docstring, or link through-hole pad cells across layers.

## 4. Checked, no finding

- **7.7 A paths.** BAT_IN has no series via: the B.Cu pour joins J1.1 to Q120's drain directly, and In2 runs in
  parallel. RAW_ACT has one series via stage (B.Cu/In2 at Q121 to F.Cu; 66 vias, ≤ 0.89 A each). The neck is F.Cu
  only, because the In2 J122 finger and the B.Cu box are separate islands from the west pours (D47). This is
  consistent with the record's "100 % F.Cu".
- **FET dissipation.** About 0.33–0.46 W per AON6403 at 7.7 A (Inference from Rds(on) at Vgs ≈ −6.7 V). Both drain
  pads sit in about 600–800 mm² of full-connection pours. MARGIN R1 records the AON6403 at 80–85 °C.
- **In2 map.**
  - Islands are as D47 states. D18 is gated (nearest 2.65 mm).
  - J124.1 sits in In2 GND, and J124.2 in the RAW_ACT island (exempt).
  - The 3V3 region stops at x 35.3, so both buck stages (U2/L1, U8/L3) sit over In2 GND, with In1 solid GND.
  - 3V3 to RAW_ACT In2 gap is 0.3 mm at y 81.3/81.6 (8.4 V, inner layer: acceptable).
  - In2 BAT_IN lies 0.3–0.35 mm from J1.3/J1.4's inner pads. A leak there under about 1.3 MΩ would act like a closed
    switch (U9 EN threshold), but it is inner-layer, with no surface path. Noted only.
- **3V3 buck U2 (DS41326 items 2–5).**
  - C6 sits 1.79 mm from VIN on the VLOGIC column. C6.2's GND joins U2.4 within 0.57 mm through the B.Cu pour, by its
    south spoke: C0805's house thermal relief, 4 spokes about 0.3 mm wide with a 0.5 mm gap, the same footprint as R7.
  - The SW strap is 0.8 mm. The BST cap is local. FB senses the output line at (36.75, 70.4).
  - U2.4's nearest GND via is 2.35 mm away (R7 1.14 mm). The load is light, so this does not matter.
- **Camera buck U8 (DS42002 items 2–6).**
  - C72 sits across VIN/GND at the IC with solid pads. The SW strap is 0.7 mm. The output caps are at L3.
  - The remote sense line on F.Cu crosses over the SW node with In1 and In2 GND between them.
  - Junction estimate at a 1 A camera: about 0.37 W IC loss × 89 °C/W (datasheet single-layer figure) + 70 °C ≈
    103 °C, against 125 °C operating and MARGIN R1's 110 °C (Tj(max) 160 °C − 50 K). That is margin with four layers
    (Inference).
  - Item 7 (vias at the GND pin) is not followed: the nearest via to U8.4 is 2.90 mm. That is an optional
    improvement.
- **Decoupling.**
  - U1's 100 nF caps are 1.5–2.2 mm from their pins, with GND vias 0.78–1.09 mm away. VCAP is 2.15–2.2 mm away.
  - VDDA has C22 (2.72 mm) and C21 (2.63 mm).
  - U3, U4, U5 and U12 caps are 1.2–1.9 mm away. U9's C88 is 2.1 mm away (0.9 mm from the pad end). U11's C97, C98 and
    C99 are 1.7–2.4 mm away.
- **Supply drops** (M3_R8 table). RAW_PROTECTED's widths agree with `ipc2152.py`: 0.5 mm, 12.0 °C at 1.54 A, 24.5 °C
  at 2.2 A. The BAT_IN feed lane matches. The U9 pad entries (0.3 mm, ≤ 0.9 mm long) are package-limited and short.
- **Hot-plug spokes.** The reversed-plug charging current through C80.2 and C96.2's thermal spokes is adiabatically
  negligible (≪ 1 K, Inference).
- **Forward panel tabs.** RAW_ACT (left, y 100–105) and In2 BAT_IN (right, y 105–110) sit at 0.51 mm. This is covered
  by R8P1-DFM-02; nothing to add from the power side.

## 5. Not verified

- The 0.05 mm DC grid (about 40 min) was not rerun. The 0.1 mm run matched D67 exactly.
- The GND return was solved only at 0.2 mm (spokes under-resolved).
- The hot-plug script was read, not rerun (it needs numpy, which is absent).
- Every temperature and inductance figure above is an Inference unless it says "measured". No bench item was done.
