# R9 review pass 2: power, thermal and hot-plug

**Board:** `m3_design/assembly_review/m3.kicad_pcb`, SHA-256 `4f841a0e44ebb1829ad7996dfe6320ed527fce1fdb1e5ff11658e0705b44ac14`
(review pass 1's fix pass). Netlist `8b0e04ea…` and DRU `ea77b791…`, both unchanged. I hashed the board before and after
the review: unchanged. This was a read-only review; the only repository file I wrote is this report.
`git status --short --ignored` was equal before and after. The ignored `__pycache__` folders existed before; tool runs
refreshed files in them, mine and the parallel reviewers'.

- `tools/check.sh` and two unit suites ran on the repository board as they are. They only read it; check.sh writes its
  reports to the system temp folder, which I deleted.
- Every other measurement ran on byte copies in the session scratchpad (`r9review/power2/`): the board, the pre-fix
  board `fc3d5b34…` (from the fix pass's backup `orig/worktree_before_fix1.tgz`) and trial copies.
- Trial copies were refilled natively with the project's own `.kicad_pro` / `.kicad_dru` beside them, and never saved
  over the repository.
- I used KiCad 10.0.6 pcbnew (KiCad Python) and the repository's own tools. My own scripts ran with `-I -B`.
- I fetched the maker documents this session; the URLs are at each use.

Every figure is measured on the board unless it is marked **Calc** or **Inference** (AGENTS §2.5).

**Result: 0 Critical, 0 Major, 5 Minor (4 worth fixing).**

- **Pass 1's five power findings are closed or properly dispositioned.**
  - C98 now sits 1.94 mm of track from U11.7.
  - C83, C82, J122's solid pins and the camera branch are listed (C21, C23, C24).
  - U9's limit and the single-via list are in the records.
  - I recomputed every IPC-2152 figure in the records.
- **The 7.7 A copper reproduces the evidence exactly.**
  - At 0.05 mm all three solves equal `step10_evidence/dc/dc005_*.txt` line for line: RAW_ACT 0.80 mΩ, neck 7.89 mm,
    12.6 °C; BAT_IN 0.16 mΩ, 8.15 mm, 12.1 °C; ACT_FET_S 0.26 mΩ, 5.18 mm, 20.4 °C.
  - D12's limits are 20 / 20 / 30 °C. The largest via barrel currents are 0.47 / 0.61 / 0.22 A, none over 1 A.
  - At 0.1 mm the solves are 0.80 / 0.17 / 0.27 mΩ.
  - The 26 supply rows equal `dc_summary.txt`, including every via-current line. So do the two GND returns (servo
    0.32 mΩ, fire loop 0.81 mΩ).
  - The hot-plug model gives `hotplug_feed.json` to the digit.
  - All 33 zone-layers equal a fresh native refill.
  - `tools/check.sh` exits 0.
- **The fix pass did not regress the power copper.**
  - Every battery-live gap (BAT_IN, ACT_FET_S, RAW_ACT and RAW_PROTECTED to GND and to other nets, per layer) is
    identical on `fc3d5b34…` and `4f841a0e…`.
  - The power zones lose under 0.7 mm² each, and every power region is still one island.
  - The copper-stage via (35.6, 64.8) notches only the east edge of In2 RAW_ACT, off the 7.7 A path. The 3V3 finger
    keeps 1.49–1.50 mm.
  - The copper-stage via (41.4, 41.1) improves the camera buck. U8.4's GND copper reach drops from 2.46 to 0.54 mm,
    and its nearest GND via from 2.95 to 1.16 mm. That closes the "optional improvement" that R8 pass 1 raised and R9
    pass 1 tied to Diodes DS42002 layout item 7.
- **Findings (all Minor):**
  - **01 (worth fixing, copper and records):** U2's regulation loop closes through two single vias that R8's loop did
    not have.
    - The FB sense via is (37.3, 71.3) and the feed via is (37.6, 78.9).
    - R8 (D40) tapped FB on the B.Cu output line before its feed via.
    - So on R9 a cracked barrel can open the loop of the 3V3 buck and drive the 3V3 domain toward VLOGIC (Inference).
      C25 records only "removes the rail".
    - D-F1-09 gives a reason for not doubling the feed via that does not apply.
    - Trial: a second feed via and a second FB via are DRC-clean, add no weak island and pass route_check.
  - **02 (worth fixing):** C21's exception is needed for J122.3 only.
    - Relieving J122.6, .9 and .12 is DRC-clean, adds no weak island and passes route_check (trial).
    - Only J122.3's relief makes the 0.86 mm² piece D-F1-06 found.
  - **03 (worth fixing, records):** C98's move left two stale records of the nearest bottom part to a support:
    M3_R9 l. 310 and ORDERING §7's sled row say R300.2 at 4.60 mm. The fit gate now gives C98.1 at 4.483 mm.
  - **04 (worth fixing, records):** C17's open inference, "USB_LIMITED's 0.45 A limit not re-derived from R85", can be
    closed. TPS2553 Eq. 1 with R85 = 66.5 kΩ gives 354.8 / 396.7 / 444.5 mA.
  - **05 (not worth fixing, records):** C24's soft-fault band ends at U9's minimum threshold.
    - A part at its 4.84 A maximum leaves the 0.4 mm camera branch unlimited up to 4.84 A, 153.7 °C by the same fit.
    - A fault that does trip U9 latches it off (TPS259470L) for the rest of the flight.

## 1. What was run

| Check | Result |
|---|---|
| `tools/check.sh` (repository board, real kicad-cli, a GUI session; reports in the system temp folder, deleted after) | **exit 0** in 7 min 24 s: DRC 0, unconnected 0, parity 0, ERC 0; metadata / 3D audit OK; silkscreen 0; fit OK (nearest bottom envelope C98.1 4.483 mm from (42, 59.5)); plate model; rule-H seeded suite OK; check_r9 40 / 40 OK (F9-1 evidence D8 5.22, C80 8.90, C96 5.72, C89 4.79, C95 4.69, R166 8.38, R167 5.59, U9 13.22 mm; K-power-pyro inner power to pyro 4.953 mm); route_check r9 0 failing / 0 allowlisted / 0 leftovers; check_actuators OK |
| `tools/run_dc.sh <copy> <scratch> 0.1` | RAW_ACT 0.80 mΩ, neck 7.92 mm on B.Cu, cut box (28.7–35.5, 78.43–81.03), 12.6 °C, 31 vias carry current, largest 0.49 A at (31.5, 78.2); BAT_IN 0.17 mΩ, 8.19 mm, 12.1 °C, largest 0.65 A at (32.0, 96.4), 5 over 0.5 A; ACT_FET_S 0.27 mΩ, 5.11 mm, 20.8 °C, largest 0.25 A. All within D12 and under the build's R8-rise gate at this grid (17.6 / 14.8 / 22.3 °C, `r9_power_check.py` R8_RISE) |
| `tools/run_dc.sh <copy> <scratch> 0.05` (14 min) | **identical line for line** (but the path line) to `step10_evidence/dc/dc005_raw.txt`, `dc005_bat.txt`, `dc005_fet.txt`: 0.80 / 0.16 / 0.26 mΩ; necks 7.89 / 8.15 / 5.18 mm on B.Cu; 12.6 / 12.1 / 20.4 °C; largest barrel 0.47 / 0.61 / 0.22 A |
| `step10/run_dc_r9.sh <copy> <scratch> supply` (26 rows, 0.1 mm) | every R and every via-current line equal to the evidence file of the same name (USB_LIMITED 85.91, RAW_PROTECTED → U7 77.11 / → U11 16.22, BAT_IN J1:1 → U9:5 2.32, VLOGIC C84 → U2 9.54, CAM_5V → J9 2.88, the 3V3 rows 1.18–44.85 mΩ) |
| `step10/run_dc_r9.sh <copy> <scratch> gnd` (servo return and fire-loop return, 0.1 mm, window x 0–46, y 50–102; about 41 min of CPU each on a loaded machine) | servo return J122.3/6/9/12 → J1.2 **identical line for line** to `step10_evidence/dc/gnd_servo.txt`: 0.32 mΩ (2.4 mV, 0.019 W at 7.7 A), In1 41 % / In2 29 % / B.Cu 21 % / F.Cu 9 % at mid-path, 152 vias, largest 0.29 A at (22.25, 87.45), none over 0.5 A; fire-loop return Q124.1/2/3 → J1.2 **identical line for line** to `fire_gnd.txt`: 0.81 mΩ (2.3 mV at 2.8 A), In1 71 % / F.Cu 29 %, the two vias beside Q124's source pins 1.23 / 1.00 A of the ≤ 20 ms pulse (C25's / M3_R9's adiabatic treatment) |
| Hot-plug model (`step6_evidence/hotplug_feed_r9.py --rb 2.32`, cfd venv) | 512 cases; feed estimate 3.232 nH; +0.0021 V / × 1.028 at the estimate, 0.0036 V / × 1.0372 at 5 nH; lowest A = B = −14.114 V; fastest B 7.66 V/µs: **equal to `step10_evidence/hotplug_feed.json`** in every field |
| Zone fills (copy refilled with `ZONE_FILLER`, compared by area, outline and hole count) | 33 zone-layers, **0 differ**: the Gerbers carry current fills |
| Board diff `fc3d5b34…` → `4f841a0e…` (scratch `viadiff.py`) | Vias removed: RAW_ACT (29.6, 78.2), (31.0, 78.2); GND (38.45, 59.05), (38.55, 63.65), (38.75, 79.55), (38.8, 61.65), (40.2431, 64.8455) and the strip's (24.7, 10.45). Added: RAW_ACT (31.5, 78.2); GND (35.6, 64.8), (32.9, 99.85), (41.4, 41.1), (38.45, 61.35), (38.45, 62.55), (38.55, 58.95), (39.7431, 62.5955), and the strip's / module's (24.65, 10.45), (28.07, 17.6), (31.88, 10.4), (34.35, 15.27). Tracks: USB_LIMITED's end (7 segments for 6), QSPI_IO2, RADIO_TXEN. Moved: C98 only. Zone deltas: RAW_ACT B 178.145 → 177.789, F 119.552 → 119.202, In2 241.892 → 241.225 mm²; GND B −3.46, F −0.22, In1 +0.53 mm²; 3V3 In2 +0.006 mm²; BAT_IN, ACT_FET_S, RAW_PROTECTED unchanged |
| Battery-live gaps (minimum copper-to-copper per layer, BAT_IN / ACT_FET_S / RAW_ACT / RAW_PROTECTED to GND and to every other net, own-part pads excluded; scratch `livegap.py`) | **identical on both boards**: e.g. B.Cu BAT_IN–GND 0.150 mm (a 0.25 mm BAT_IN track at (20.12, 91.04), the zone clearance), F.Cu BAT_IN–BAT_DAMP 0.251 mm (via vs C89.2), B.Cu RAW_PROTECTED–BAT_ILIM 0.190 mm (42.15, 87.08), In2 RAW_ACT–GND 0.251 mm, In1 BAT_IN–GND 0.250 mm (J1.1's antipad). The new GND via (32.9, 99.85) is 0.40 mm (pad edge) from the BAT_IN F.Cu pour, more than BAT_IN's own 0.3 mm zone clearance and none of the minima above |
| GND reach of 45 power-area GND pads (centre distance to the nearest GND via and through-copper reach on the ground aid's raster, both boards; scratch `gndreach.py` importing `r9_ground_aid`) | unchanged for every pad but C121.2 16.1 → 1.5 mm (via 5.16 → 2.66 mm), C98.2 0.74 → 0.40 mm (moved part), C92.2 1.70 → 1.80 mm and **U8.4 2.46 → 0.54 mm** (nearest via 2.95 → 1.16 mm, the copper-stage via (41.4, 41.1)). U11.3 / .4 / .6 / .12 0.9 / 1.4 / 0.3 / 0.8 mm on both boards, although the ground table moved two vias round C98. Weak GND islands: the same 9 on both boards |
| Power vias' nearest GND via (both boards) | changed only where the vias moved: the 3V3 feed via (37.6, 78.9) 1.32 → 1.52 mm (the reach via (38.75, 79.55) is gone; a power via into a pour, which AGENTS §3's 1.5 mm rule does not cover); RAW_ACT spine vias nearer a GND via at (35.6, 64.8) |
| Pad zone connections | unchanged: 98 SMD GND pads THERMAL, 10 FULL (the six RF pads of C20 and J122.3 / 6 / 9 / 12); no override on any power-net pad |
| In2 (zone list and 0.01 mm line scans) | every power region one island: RAW_ACT 241.2, BAT_IN 115.3, 3V3 1037.1 mm²; GND 1742.2, strip 982.1, crystal plane 35.3 mm². The 3V3 finger is x 36.30–37.79 (1.49–1.50 mm) at y 57–79; RAW_ACT 0.30–0.31 mm from it, but 1.15 mm at y 64.8, the GND via's notch |
| J122 relief trials and second-via trials (finding 01, 02) | §3 |
| Camera return (`dc_solve.py --net GND --source J9:2`, window x 32–46, y 36–56, 0.1 mm, 1.9 A, the camera-overload estimate of C25) | J9.2 → U8.4 **5.10 mΩ** (9.7 mV, 0.018 W), J9.2 → C75.2 5.16 mΩ; all on F.Cu at mid-path; narrowest counted cut 1.01 mm on F.Cu (8.1 °C at 1.9 A by the fit; the 0.46 mm contours next to J9.2 are terminal-adjacent and not counted by the tool); the copper-stage via (41.4, 41.1) carries 0.69 A of it. Supports C22's J9.2 exception: no power concern at ≤ 1.9 A |
| IPC-2152 figures in the records (`tools/ipc2152.py`) | 0.3 mm B.Cu 21.7 °C at 1.54 A, 95.9 °C at 3.24 A; 1.45 mm F.Cu 15.7 °C at 3.24 A, 23.4 °C at 3.96 A (35.0 °C at 4.84 A); 0.4 mm 26.2 °C at 2.0 A, 10.1 °C at 1.24 A, 14.8–102.9 °C at 1.5–3.96 A (153.7 °C at 4.84 A); USB_LIMITED 0.3 mm 1.85 °C at 0.445 A. Every figure in M3_R9 "Power" and C24 reproduces |
| Single vias | `sources/r9_review/fix1/fix1_measure_4f841a0e.json` `single_vias`: 47 of 96 power-net vias, the same set as on `fc3d5b34…` (97, less the dropped RAW_ACT via) |
| Maker documents read this session | TI TPS2553 SLVS841F (Nov 2008, rev. Aug 2016) §7.1, §9.5.1 Eq. 1, §12.1 (https://www.ti.com/lit/ds/symlink/tps2553.pdf); TI TPS25947 SLVSFC9C (Oct 2020, rev. May 2026) device comparison table (TPS259470LRPW "Latch-Off"), §8.3, §8.3.1, §8.4.1 (https://www.ti.com/lit/ds/symlink/tps25947.pdf); Diodes AP63200/01/03/05 DS41326 Rev 3-2 (Nov 2024) pin descriptions (FB), Figure 3 functional block diagram, Application Information 1, 6, 7, PCB Layout items 1–6 (https://www.diodes.com/assets/Datasheets/AP63200-AP63201-AP63203-AP63205.pdf) |

## 2. Previous findings in this dimension (pass 1 on `fc3d5b34…`)

| Finding | Status on `4f841a0e…` |
|---|---|
| R9P1-POWER-01: three power-IC bypass capacitors regressed | **Closed** for C98 (copper): C98 (39.275, 64.2, bottom), C98.1 on the trunk 1.94 mm of track from U11.7 ((40.05, 64.2) → (39.3, 64.95) → (39.3, 65.825)), the trunk passing through C98.1 before the pin; C98.2 0.40 mm of copper from the GND via (38.5, 65.2), 1.00 mm away; USB_LIMITED 85.91 mΩ (83.02 before; 38 mV at the 0.445 A limit). **Properly dispositioned** for C83 and C82: R9_VALIDATION C23 with TI SLVS841F and SLVSFC9C citations, C83 11.64 mm (pass 1's 11.64), R8's figures for comparison, D-F1-05 giving the legaliser's reasons; D-S6-06's TI citation is corrected (SLVSEA3F §11). One record left stale by the move: finding 03 |
| R9P1-POWER-02: U9's limit 3.96–4.84 A, not 2.2 A | **Closed** (records): D-S6-05, `r9_power.py` l. 370–373, M3_R9 "Power" l. 126–137 and C24 state 3.960 / 4.452 / 4.840 A (SLVSFC9C §6.5, Eq. 7) and the IPC-2152 check at the coordinated limits; I recomputed each figure (§1). A precision point about the band's top end: finding 05 |
| R9P1-POWER-03: seven single-via rail links undocumented | **Closed** (records): M3_R9 l. 146–164 and C25 list the seven with their barrel loads as accepted single points (MARGIN R15); the set is unchanged on this board. But the stated consequence for the 3V3 feed and the stated reason for not doubling it do not hold: finding 01 |
| R9P1-POWER-04: J122's GND pins solid, unlisted, with an obsolete basis | **Properly dispositioned** (C21, D-F1-06: the relief was built, judged and its side effect measured; the owner chooses). I reproduced the side effect (§3, finding 02): relieving all four adds one weak F.Cu island at (18.64, 63.46). It comes from J122.3 alone, so the exception can shrink to one pin: finding 02 |
| R9P1-POWER-05: the DRU's relief comment | **Closed** (records): M3_R9 "Thermal reliefs" (l. 262–266) names the twelve 0805 / 1206 pads; the DRU comment stays (pinned by check_actuators' DRU_SHA) |
| R9P1-PLANES-01 (power aspect): C121's GND return through a 0.37 mm neck | **Closed** for this dimension: C121.2's copper reach 1.50 mm (16.10), its via (35.6, 64.8) 2.66 mm away; the via sits in the In2 gap between RAW_ACT and the 3V3 finger (hole 0.30 mm from RAW_ACT copper, 0.55 mm from 3V3), on B.Cu in a GND notch of the RAW_ACT pour's east edge; RAW_ACT's 7.7 A solve 0.80 mΩ at both grids (0.79 on `fc3d5b34…`, with both of the fix pass's RAW_ACT changes; the neck stays at Q121's via row) |

## 3. Findings

### R9P2-POWER-01 (Minor, worth fixing): U2's feedback loop closes through two single vias that R8's did not have; an open barrel can over-voltage the 3V3 domain, which C25 does not record, and the reason given for not doubling the feed via does not apply

**Copper (measured).**
- U2 is the AP63203WU-7, the fixed 3.3 V part, on the bottom at (40.0, 71.8).
- *Feedback.* U2.1 (FB, (39.05, 70.6)) runs on a 0.2 mm B.Cu stub through (39.05, 71.3) to a 0.5 / 0.3 via at
  (37.3, 71.3) into the In2 3V3 finger (`r9_power.py` l. 425 `V_FB`, l. 443).
- *Output.* L1.2 → C8.1 → C9.1 is a 1.0 mm column. Then a 0.4 mm B.Cu track runs (40.0, 78.9) → (37.6, 78.9) to the one
  0.6 / 0.3 feed via into the finger's tip.
- So the regulation loop is: output caps → feed via → finger, 7.6 mm of it → FB via → U2.1. Both vias are single,
  and either one open opens the loop.
- *R8 had no via in the loop.* R8_DECISIONS D40 (l. 1014–1016): "The output is one 0.6 mm column … then west to the In2
  3V3 via (34.4, 69.65). FB (pin 1) taps that line at (36.75, 70.4)". R8's generator agrees (`r8_power.py` l. 345–355,
  read only): "FB (U2.1) senses that trace", a 0.2 mm B.Cu stub onto the output trace before its single feed via.
- *Capacitance.* C8 and C9 (2 × 22 µF, Samsung CL21A226MAQNNNE, BOM line 3) are 44 µF of the 3V3 net's 49.6 µF nominal,
  and both sit on the buck side of the feed via. The 3V3 net beyond it holds C23 (4.7 µF) and nine 100 nF, 5.6 µF
  nominal. The GNSS's 10.1 µF sits behind FB30, the radio's 22.1 µF behind FB31 (BLM18KG221SN1D) and 3V3A's 45.4 µF
  behind R164 (2.2 Ω).

**What a failed barrel does** (Inference from DS41326 Rev 3-2: pin table "FB: feedback sensing terminal for the output
voltage"; Application Information 1, a peak-current-mode loop that raises COMP while FB is low; Figure 3 shows only an
FB UVP comparator; no FB-open or output-side sense is described):
- **FB via open.** U2.1 is left on a floating stub, and the internal divider of the fixed part pulls its sense low. COMP
  then rises to the limit, and the buck drives the intact feed via and the whole 3V3 domain toward VLOGIC (7–8.4 V in
  flight).
  - If the UVP comparator forces hiccup, the domain still sees an overshoot at each soft-start, because FB stays low
    while the output rises.
  - Every 3V3 part's absolute maximum is far below VLOGIC (REQUIREMENTS F9 quotes ≤ 3.6 V at the GNSS and ≤ 3.7 V at the
    radio; the MCU and the flash are 3.3 V parts). The MCU drives the pyro gate (PE4); its behaviour when over-stressed
    is unknown.
- **Feed via open.** The domain loses supply, the classified consequence. But the loop is open too, so the isolated
  C8 / C9 charge toward VLOGIC.
  - An intermittent barrel then shares that charge with the domain's 5.6 µF of local capacitance on reconnection.
    With about 20 µF effective at 7 V: (20 × 7 + 5.6 × 3.3) / 25.6 ≈ 6 V before the beads and R164 let the other banks
    help (Calc on assumed effective values).
- **On R8**, an open feed via only removed the rail, and R8 had no FB via. R9's sensing choice is reasonable in itself:
  it keeps FB away from the SW node, and the finger is a quiet sense point. The cost is these two vias.

**Records.**
- C25 and M3_R9 "Power" (l. 146–164) give the 3V3 feed via's consequence as "a cracked barrel removes the rail …
  losing the primary computer".
- The FB via is not listed: pass 1 classed it with the mA taps.
- M3_R9 l. 162–164 and D-F1-09 say: "No second via is added: the 3V3 finger is 1.49 mm wide and D-S8-02's narrow-region
  rule bars a second antipad there". D-S8-02's rule (R9_DECISIONS l. 1472–1473) is "no antipad in an In2 power region's
  narrow outline". That rule is about other nets' vias. A 3V3 via in the 3V3 finger takes a flashed In2 pad, not an
  antipad (measured below).

**Trial (scratch copies, deleted).**
- I added a 0.6 / 0.3 3V3 via at **(37.0, 78.9)** on a 0.6 mm extension of the 0.4 mm feed track, copying the
  existing via's unconnected-layer mode. It flashes F / In2 / B like (37.6, 78.9).
- I added a 0.5 / 0.3 3V3 via at **(36.7, 71.3)** on a 0.6 mm, 0.2 mm wide extension of the FB stub. (36.8, 71.3) fails
  min_hole_to_hole at 0.20 mm; 36.7 gives 0.30 mm.
- I refilled natively with the project's DRU.
- `kicad-cli pcb drc --severity-all`: only the scratch copy's 199 `lib_footprint_issues` (no library table there; the
  unmodified copy gives the same 199), 0 unconnected.
- In2 3V3 is still one island (1037.13 mm²). The aid's weak GND islands are the same 9.
- `route_check.py --profile r9`: 0 failing. Two new information-only `short_layer_hop` instances (the via pairs).
- `dc_solve` 3V3 L1:2 → U1:75 is 14.98 mΩ (15.25 on the board), and the two feed vias share 0.32 / 0.18 A of 0.5 A.

**Impact.**
- An improbable fault: a latent or cracked via barrel. No hard requirement fails. But MARGIN R15 ("no undocumented
  single point") is not met for the FB via, whose consequence is not that of the tap class it was filed under.
- But R9 made the consequence worse than R8's for the same single point. It added a second single point (the FB via)
  whose failure can over-voltage the primary computer, not just stop it.
- R9_VALIDATION asks the owner to accept these links on a consequence statement that is incomplete.
- The CAM_5V link (40.75, 45.4) has the same structure: U8's FB divider top R71 is fed by the 0.25 mm F.Cu sense run
  from J9.1, beyond the via. That copper is R8's camera layout moved (D-S6-07), and its consequence is the camera and
  its translator only.

**Fix.**
- Add the two vias in `r9_power.py` (the 3V3 feed and the FB sense), rebuild and re-run the gates and the 3V3 rows.
- Or tap FB on the B.Cu output copper as R8 did, keeping clear of SW.
- Correct C25, M3_R9 l. 146–164 and D-F1-09: the consequence of an open 3V3 feed or FB via (and of CAM_5V's for the
  camera), and the real reason if a via is still not added.

### R9P2-POWER-02 (Minor, worth fixing): C21's solid exception is needed for J122.3 only

**Measured** (trial copies refilled natively with the project's DRU; fill contact in a 0.1 mm ring just outside each
pad):
- *As built.* J122.3 / 6 / 9 / 12 are FULL: F.Cu 2.642 mm² (whole ring), In1 2.642, B.Cu 0.473 (the RAW_ACT pour takes
  the rest). J122.3 also has In2 0.204.
- *All four relieved* (the zones' THT relief). Each pin gets F.Cu 4 spokes, In1 4, B.Cu 2 (J122.3 also In2 2). The aid's
  weak islands go 9 → 10. The new one is the F.Cu piece at (18.64, 63.46), D-F1-06's 0.86 mm² piece (x 18.15–19.13,
  y 62.61–64.31).
- *J122.6, .9 and .12 relieved, J122.3 solid.*
  - Weak islands stay 9, no new one.
  - DRC: only the copy's 199 `lib_footprint_issues`, 0 unconnected, no starved thermal.
  - route_check r9: 0 failing.
  - The relieved pins keep 4 / 4 / 2 spokes.

**Requirement.** REQUIREMENTS M2: "Through-hole GND pins use thermal reliefs wherever their spokes are not starved
(exceptions listed …)".
- C21 gives two reasons. The first is "for the 7.7 A servo return (≈ 1.9 A per pin)". Reliefs cost about 0.04 mΩ and
  0.16 mW per pin at 1.925 A (pass 1's spoke calculation, Calc), so it does not need solid pins.
- The second is J122.3's island. It holds for J122.3 only.
- The ORDERING §4 hole-fill concern (solid joints to F.Cu, In1 and B.Cu pours on the header that carries the return)
  then applies to one pin instead of four.

**Fix.**
- Relieve J122.6 / .9 / .12 in `r9_pcb.py` (the fix pass's RELIEVE list less J122.3), rebuild, re-run the servo GND
  return and the gates, and shrink C21 to J122.3 with its island reason.
- Or give the owner this option in C21 alongside "all solid".

### R9P2-POWER-03 (Minor, worth fixing, records): C98's move left the nearest-part-to-a-support figure stale in two records

- The gate's fit check on this board says "nearest bottom/pin envelope: C98.1, 4.483 mm from support (42.0, 59.5)".
  `step10_evidence/gate/fit.json` `nearest_support` agrees.
- R9_VALIDATION l. 76 and l. 155 carry 4.483 mm, and ORDERING §7's hardware row carries C98.1 at 4.55 mm.
- But M3_R9 l. 310 still says "support clearances 4.600 mm bottom (R300.2 at (4, 4))". ORDERING §7's sled row (l. 211)
  still says "no bottom part within 3.5 mm of a hole centre: nearest 4.60 mm, R300.2 at (4, 4)".
- Impact: none on the copper (4.483 mm ≥ the 3.5 mm limit). The two records are wrong for the board they are bound to.
- **Fix:** C98.1, 4.48 mm from (42, 59.5), in both lines.

### R9P2-POWER-04 (Minor, worth fixing, records): C17's open inference on USB_LIMITED's current limit can be closed

- C17 lists "USB_LIMITED's 0.45 A limit from R8 D42 (not re-derived from R85)" as an open inference.
- R85 is 66.5 kΩ 1 % (`logic_power_path.kicad_sch` l. 1456; Yageo RC0603FR-0766K5L, C137691).
- TI SLVS841F §9.5.1 Eq. 1:
  - IOSmax = 22980 / R^0.94 → **444.5 mA**;
  - IOSnom = 23950 / R^0.977 → **396.7 mA**;
  - IOSmin = 25230 / R^1.016 → **354.8 mA** (R in kΩ, valid 15–232 kΩ).
- With R85's ±1 %: 351–449 mA (Calc).
- So the recorded 0.45 A is the maximum, and the supply rows' 0.5 A is an upper bound. At 0.445 A the trunk's two single
  vias carry 0.445 A each, the 85.91 mΩ trunk drops 38 mV, and the 0.3 mm track rises 1.85 °C (Calc).
- The minimum, 355 mA, sits above the bench logic load fed from USB (about 0.3 A at the buck's input with the radio
  transmitting, Inference). That is a schematic fact, not a layout one.
- **Fix:** replace C17's item with the derived band and its source.

### R9P2-POWER-05 (Minor, not worth fixing, records): C24's soft-fault band stops at U9's minimum threshold, and the latch-off consequence is not stated

- C24 says that a resistive fault on the 0.4 mm, 44 mm camera branch "drawing 1.5–3.96 A is limited by neither U7 nor U9
  … would heat it about 15–103 °C".
- 3.96 A is U9's *minimum* threshold. A part at its 4.840 A maximum (SLVSFC9C §6.5) leaves the branch unlimited up to
  4.84 A: 153.7 °C by the same fit (Calc).
- A fault above the part's threshold trips U9, and the TPS259470**L** is the latch-off variant (SLVSFC9C device
  comparison table: TPS259470LRPW "Latch-Off"; M3_R4 l. 415 notes it).
  - RAW_PROTECTED then stays off until a power cycle.
  - So do VLOGIC (U11's only in-flight source) and ACT_EN's pull-up (R122 from RAW_PROTECTED).
  - The primary computer and the servo supply are lost for the flight (Inference from the netlist). Recovery is left
    to the backup altimeter (MARGIN R15's external redundancy).
- Not worth fixing: both are improbable faults and the owner's judgement would not change. One clause in C24 makes the
  item complete.

## 4. Fix-pass changes in this dimension, checked, no finding

- **The DC gate is intact.**
  - `tools/dc_solve.py`, `run_dc.sh` and `ipc2152.py` are unchanged since R8's commit 9c8179b (`git diff HEAD` is
    empty).
  - `m3_design/r9_power_check.py` and `r9_post_check.py` hold D12, D_raw ≤ 1.0 mΩ, every rise ≤ R8 and ≤ 1 A per via
    on every build. The fix pass did not change them: they equal the pre-fix backup.
  - `test_r9_power` and `test_dc_solve` pass: 24 tests (KiCad Python, `-B`).
- **TP120's via row (D-F1-04).**
  - (29.6, 78.2) is dropped and (31.0, 78.2) moved to (31.5, 78.2).
  - (31.5, 78.2) and (32.2, 78.2) are 0.70 mm apart: hole to hole 0.40 mm, at least the project's 0.25 mm.
  - The moved via is 0.40 mm of hole from TP120's opening.
  - It carries the row's largest current, 0.47 A at 0.05 mm (0.49 A at 0.1 mm).
  - The RAW_ACT neck moves to 7.89 mm at the row (cut box x 28.65–35.55, y 78.13–79.63) and still lies at Q121.
- **RAW_ACT_F's west edge** at x 29.75 now runs to y 76.6. F.Cu RAW_ACT loses 0.35 mm²; F.Cu carries 6 % at mid-path,
  as before.
- **The copper-stage vias.**
  - (35.6, 64.8): §2.
    - The fix pass's own C121 solve (`fix1/dc_c121_gnd.txt`) sends 6.82 A of a nominal 7.7 A, 89 %, through this one
      via.
    - So the servo bulk capacitor's ripple return rides on one 0.3 mm barrel. If that barrel opened, the return would
      fall back to the F.Cu guard strip, now 0.72 mm.
    - C121's ripple current is not specified (no maker datasheet, ORDERING §5), so the via's share against MARGIN P1-9's
      1 A per barrel is unverified. Information only: the via is far better than the 11.98 mΩ neck it replaced, and
      the aid refused every spot inside the RAW_ACT B.Cu pour, each a new P7 pocket (`fix1_progress.md` session 2).
  - (32.9, 99.85): in the forward strip; no BAT_IN zone changed.
  - (41.4, 41.1): U8.4 now reaches GND within 0.54 mm of copper. It carries 0.69 A of the 1.9 A camera-overload return
    in the J9.2 solve.
- **The ground table round C98.** The patch, island and grid vias moved to (38.45, 62.55), (39.7431, 62.5955) and
  (38.45, 61.35). U11's GND pins keep their reach (§1).
  - The reach via (38.75, 79.55) is gone.
  - So the 3V3 feed via's nearest GND via goes from 1.32 to 1.52 mm. This is negligible for a 1.1 MHz buck output into
    a plane, and AGENTS §3's 1.5 mm rule is for critical signal nets.
- **USB_LIMITED's new end.**
  - It runs (36.225, 62.425) → (37.0, 63.2), east on y 63.2 to (40.05, 63.2), north into C98.1, 45° into U11.7, with a
    T up into R87.1.
  - It passes 0.375 mm from C98.2 and 0.25 mm from the GND via (38.45, 62.55).
  - The C98.1-first entry is the capacitor practice TI §11 asks for.
  - It costs 2.9 mΩ (85.91 against 83.02), 1.3 mV at the 0.445 A limit.
- **Unchanged and re-verified.**
  - U2's and U8's hot loops (pass 1 §4).
  - Every bypass distance in pass 1's table but C98.
  - The input protection's distances from J1.1 (F9-1).
  - The TVS loop.
  - The pad overrides.
  - The 7 short power hops of C15 (AGENTS §3 applies the 1.5 mm rule to critical nets only).
  - The fire-loop return's two vias at Q124 (1.23 / 1.00 A of the 2.8 A pulse for ≤ 20 ms; about 0.9 K adiabatic for
    the shorted-igniter pulse, Calc).
  - U9's TI §8.4.1 items: the IN cap C88 2.1 mm; D9 3.35 mm; R84 (RILM) 2.4 mm of 0.2 mm track from U9.9. The ILM
    net also runs about 7 mm on to TP89 (44.6, 83.4, top) through one via, about 2 pF in all against TI's "below 50pF"
    (Calc). The nearest switching copper, L1.1, is about 8 mm from it. C82 and the eFuse ground island are as recorded.

## 5. Not verified

- **Grids.** Both GND returns reproduce at 0.1 mm (§1), but I did not solve them at a finer grid. They are upper bounds
  over the window x 0–46, y 50–102, as recorded.
- **Trials were not built.** The two second-via trials and the J122 relief trial are scratch edits of the built board,
  not generator changes. Each must still pass `r9_build.sh`'s stage gates: the trial checks were DRC, the islands
  function and route_check, but not check_r9's seeded suite or the ground gate's other rows.
- **Not modelled.** The AP63203's behaviour with FB open or low (finding 01) is Inference: DS41326 does not describe it.
  The overvoltage magnitude depends on the converter's loop and the domain's capacitance, which I did not model.
- **No bench work.** Every temperature, inductance and failure-mode statement not marked measured is Calc or Inference.
