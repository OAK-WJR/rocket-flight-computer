# R9 pass 1: mechanical fit and robustness review

Independent, read-only review (2026-10-25) of the uncommitted M3-ASSY-R9 board (worktree
`rocket-flight-computer-r9`, branch `m3-assy-r9`). The board file `m3_design/assembly_review/m3.kicad_pcb` had
SHA-256 `fc3d5b34a4bfbaecfbcb44bdf8144c87015fc71be7accf48354f23410e8d0f51` at the start, after the gate run and at the
end of this review. No repository file was changed apart from this report. R7 and R8 boards were read from git objects
(`git show 431025d:…`, `git show 9c8179b:…`, R8 = `cc044ea0…`), never from the sibling worktrees.

Scope (the brief's mechanical dimension): the 46 × 102 mm outline and P1; the bore envelope (fit_check, J122 turned on
the axis); the five supports, including the mid support at (42, 59.5); the plate model (f1 against the 209 Hz gate and
the 241 Hz target); the SMA jacks, their retention and staking; lead directions (pyro west, battery east) and wire room;
the IMU lever arm and its 180° rotation; tall-part staking; the bay stack (the proposed parent VEHICLE.md row).
Vehicle-level choices and firmware are out of scope. Coordinates are KiCad mm (x = 0 west edge, y = 0 aft edge).

What was run:
- `tools/check.sh` (GUI session logged in, no shim; `NUMPY_PY` = the cfd venv): **exit 0**. DRC 0 / unconnected 0 /
  parity 0 / ERC 0; audit, silk, fit, plate, seeded rule-H suite, check_r9 (all 40 rules), route_check r9 (0 failing,
  0 allowlisted, 0 leftovers) and check_actuators OK. Board SHA and `git status` unchanged by the run.
- `tools/fit_check.py` on the board: the same figures as `step10_evidence/gate/check_sh.txt`.
- `tools/plate_model.py` on that fit report: identical to `step10_evidence/gate/plate.json` (the only difference is
  the `bound_by` key that `step10/bind_report.py` adds).
- `tools/check_r9.py --only M-2,M-3,M-4,M-5,M-6,M-7,P-10,P-11,T-1,F9-1`: all OK. The evidence matches the records.
- The same fit_check / plate_model on R8 `cc044ea0…` (f1 208.7 Hz, reproducing the R8 record) and on R7 `431025d`.
- Own read-only pcbnew scripts: copper, pads and courtyards round every hole on every layer; the jack-leg
  surroundings; the terminal silkscreen (entry arrows, legends); a legal-spot scan for an M3 hole in the middle third
  of the board; mode shapes and modal participation from `plate_model.Plate` (code in the Appendix).
- Maker documents: the DORABO DB128L-5.08-XXP-C-S drawing (LCSC C430601 datasheet,
  https://datasheet.lcsc.com/datasheet/pdf/774f77501d8e260538e3ee59c3ecee93.pdf?productCode=C430601). The ST
  LSM6DSV320X datasheet (DS14623) could not be fetched (st.com timed out twice), so the IMU map was checked against R8's
  recorded map and the pad copper, not against the maker's axis figure again.

## 1. Summary

**Critical 0, Major 0, Minor 5.**

R9 meets every mechanical requirement and gate I checked:
- **P1:** the board is 46.00 × 102.00 mm (120 mm maximum).
- **P2, bore fit:** every part and mated envelope fits.
  - The binding envelope is still J9's mated plug, at 0.028 mm (R6's figure, unchanged).
  - J122's mated plugs have 0.50 mm, turned on the axis (0.71 mm unturned; owner decision 5's default, M-5 floor 0.49).
  - J121 and J124 have 1.232 mm, better than R8's 1.153. C84 has 1.367 mm.
- **P2, supports:** five M3 supports at (4, 4), (42, 4), (4, 98), (42, 98) and (42, 59.5).
  - Bottom clearance 4.600 mm (R300.2) and top clearance 5.008 mm (TP30.1), against 3.5 / 3.8 mm.
  - The mid support is effective: f1 is 128.7 Hz with the corners only.
- **P2, vibration:** f1 is 256.6 / 362.9 Hz pinned and 434.8 / 614.9 Hz clamped (gate 209 Hz, target 241 Hz; R8 208.7 Hz).
  - The 100 g static deflection falls from R8's 0.98 mm to 0.66 mm.
  - Strain at U31, U1, U4, U5, C121 and J122 falls by 15–33 % against R8; U30, C84, J1 and J124 are within about 5 %.
- **Wire entries:** J121 and J124 enter from −x with 6.353 mm to the bore wall (P-11, ≥ 6.25 mm). J1 enters from +y,
  1.855 mm from the forward edge with nothing in front (M-4). The silkscreen arrows under all three bodies point to
  those edges.
- **IMU:** the R9 map (U4 bottom, rotation 180°, pad 1 at (+1.21, −0.75) mm from its centre) is R8's map turned 180°
  about z. It is carried consistently by the binding note, M3_R9, ORDERING §5 and the check_r9 M-7 gate.
- **Staking and SMA retention:** the staking list covers every two-terminal tall part. The SMA retention chain is
  complete in substance (counter-hold, torque, structural staking, the sled carrying the plugs). The staking text
  misses R9's new neighbours of J30's legs (R9P1-MECHANICAL-04).

The five findings are records and robustness observations:
1. **R9P1-MECHANICAL-01: the IMU is back on the first-mode antinode.**
   - U4 sits at 0.76 of the peak mode-1 amplitude and U5 at 0.89. R8 had 0.18, R7 0.72.
   - Estimated board-amplified vibration at U4 is about 2.2× R8's in rms over six modes, 4.9× in mode 1.
   - The east mid support (owner decision 5's default) causes it. The owner's own fallback, (4, 49.5), would give
     f1 248.8 Hz and about a third of that exposure, but U5 now occupies that spot.
   - Not recorded anywhere. Record it for the owner and measure the vibration at U4 on the bench.
2. **R9P1-MECHANICAL-02: the bay-stack and harness records are incomplete.**
   - M3_R9 has no bay-stack paragraph (P1).
   - The proposed VEHICLE row again leaves out the ≥ 3.5 mm standoffs (R7 P3-MECHANICAL-03), the battery lead's
     U-turn beyond the forward edge, and the owner's harness sides.
   - ORDERING's "battery leads along the bay's east wall" is not possible on the top side, where J9's mated plug
     comes within 0.03 mm of the wall.
3. **R9P1-MECHANICAL-03: REQUIREMENTS P2 is stale.** It still says the owner's ruling on R8's sixth support is open.
   M2 records R8's list, C10 included, as accepted on 2026-10-20.
4. **R9P1-MECHANICAL-04: ORDERING's assembly notes miss R9's new neighbours.**
   - **Hardware:** masked RAW_PROTECTED (0.55 mm from the (42, 59.5) hole edge) and BAT_ENABLE run under the top
     washers, and BAT_FAULT_N and LOGIC_SOURCE_ST under the standoffs. The records say only GND lies there.
   - **SMA staking:** J30's leg fillet now reaches C303's tuning land on the GNSS RF node (0.81 mm; R7/R8 3.40 mm),
     C302 and L30 (1.37–1.49 mm), and the limiter's R300 and R303 on the bottom (2.28 / 3.18 mm; R7/R8 5.63 mm). The
     text names only D30/D31.
   - **C121's fillet** is 1.33 mm from the east tie hole.
   - **U5's light foam** sits 2.4 mm from U4.
   - All of this is text only. Nylon hardware is already mandatory.
5. **R9P1-MECHANICAL-05: the DB128L stacking nubs are not in the model.**
   - The DB128L carries 0.57 mm stacking nubs on one end face (DORABO drawing). Neither the 3D model nor the courtyard
     includes them.
   - R9 abuts J121 and J124 (0.07 mm body gap) and puts J124's forward end 0.82 mm from J1's back face. That gap is
     0.25 mm if the nub end faces J1.
   - My reading of the drawing puts the nubs on the aft end (Inference). An assembly note and a first-article check
     settle it.

## 2. Earlier findings in this dimension

No R9 review pass has run before this one. The last mechanical reviews were R7 passes 2 and 3, since R8's review had no
mechanical reviewer and the owner accepted its C10 vibration item. This table checks each of those findings on R9.

| Earlier finding | Disposition then | Status on R9 (`fc3d5b34…`) |
|---|---|---|
| MECHANICAL-01 (Major → Minor): SMA retention on soldered legs alone | Counter-hold, torque, staking after the RF tests, the sled carries the plugs | **Closed** as a retention chain: REQUIREMENTS P3; ORDERING §5 (counter-hold, 0.8–1.13 N·m Kinghelm p. 1 or the plug maker's lower value, staking order) and §7 Sled (saddle at the plug axis). R9's jacks use the same footprint `M3_SMA_KH_KE8_EDGE` (check_r9 R-3/R-4) at x 13.59 / 32.29, 18.70 mm apart. The regenerated strip brought RF and limiter parts closer to J30's legs than on R7/R8: C303 0.81 mm (R7/R8 3.40), and R300 2.28 mm on the bottom (R7/R8 5.63). The staking text names only D30/D31: **R9P1-MECHANICAL-04** (§4.5) |
| MECHANICAL-02 (Major): no vibration estimate | Recorded in M3_R7, bench tap check | **Closed.** M3_R9 §"Mechanical" and gate M-2 on `fc3d5b34…`, reproduced here (§4.4) |
| MECHANICAL-03 (Major → Minor): bay stack not recorded | M3_R7 paragraph and parent VEHICLE row | **Partly.** The R9 row is proposed in `r9_step10_handoff.md` §4 and not applied (D-S10-11, the coordinator's call); M3_R9 carries only a pointer. See **R9P1-MECHANICAL-02** |
| MECHANICAL-04 (Minor): coax plug undocumented | Open, tracked | **Properly dispositioned** (ORDERING §7 "Plugs": choose and cite the plug; 44–48 mm loop zone) |
| MECHANICAL-05 (Minor): hardware size | ORDERING §7 Mounting hardware | **Closed** for sizes: M3 nylon, washer ≤ 7.0 mm OD, standoff ≤ 5.5 AF and ≥ 3.5 mm. R9's nearest pads are 4.62–5.01 mm from the centres (§4.3). The masked tracks under the hardware are **R9P1-MECHANICAL-04** |
| P3-MECHANICAL-01 (Minor): torque value without source | — | **Closed** (ORDERING §5 cites Kinghelm p. 1 and Amphenol's cut sheet) |
| P3-MECHANICAL-02 (Minor): saddle preload, jack share | — | **Closed** (ORDERING §7 Sled; REQUIREMENTS P3 "relieves most, not all") |
| P3-MECHANICAL-03 (Minor): VEHICLE row lacks J1's forward entry and the standoff height | — | **Half closed.** The R9 proposal names J1's forward entry; the standoff height (≥ 3.5 mm) and the leads' U-turn are still missing. See **R9P1-MECHANICAL-02** |
| P3-MECHANICAL-04 (Minor): fit_check skipped bare bottom pads in the standoff rule | — | **Closed.** `tools/fit_check.py` `check_board` adds the exposed bottom pads of board features and DNP parts to the standoff list |
| R8 C10: f1 13 % below R6; sixth-support ruling | Owner-accepted with R8's list, 2026-10-20 | Superseded for R9 (256.6 Hz > R6's 241). P2 still calls the ruling open: **R9P1-MECHANICAL-03** |
| Step 10 observation D-S10-18: check_r9's M-7 docstring says "rotation 0 (the M3_R5 axis map)" | Recorded, not fixed | Still open. The rule itself keys 180° on the title-block revision and passes (verified, §4.8). It belongs to the gate-integrity dimension, so it is not raised again here |

## 3. Findings

| ID | Sev. | Req. | Finding | Evidence | Fix |
|---|---|---|---|---|---|
| R9P1-MECHANICAL-01 | Minor (worth fixing: records and a bench line) | P2 (vibration estimates on the final geometry); F1 (roll-angle budget; "measure temperature/vibration/acceleration sensitivity"); owner decision 5 | **The IMU (U4) and the barometer (U5) are back on the board's first-mode antinode, and the owner never saw the trade.** The east mid support leaves the west edge unsupported for 94 mm, from (4, 4) to (4, 98). Mode 1 (256.6 Hz) peaks at the west edge's mid-span (0, 52.5), where U4 and U5 sit. R8's west support at (4, 64) had put U4 near a node, which was incidental. The model estimates about 2.2× R8's board-amplified vibration at U4 (rms over six modes), 4.9× in mode 1. That is R7's level, which the owner accepted without this metric being recorded. Owner decision 5's fallback, (4, 49.5), would meet f1 ≥ 241 Hz and cut the exposure to about a third. U5 now sits on that spot, and the scan finds no other legal M3 spot in the middle third. M3_R9 and R9_VALIDATION record f1, the static deflection and the lever arm, but not this. plan_flowline had flagged it ("Open risk (vibration): the IMU sits mid-plate, possibly near the mode-1 antinode"); plan_spine and the B-spine steps never evaluated it. The absolute level is unknown (no PSD exists for these motors, DESIGN_ASSURANCE §6.1), so this is a trend, not an overload. It sets the environment F1's vibration-sensitivity work must measure. The low-g ±16 g accelerometer channel will saturate more often in boost (Inference; the high-g channel covers it, F2) | **Mode-1 shape** (`plate_model.Plate`, jacks only, pinned, D 5; normalised to the peak, sign of the peak): R9 U4 **0.76**, U5 **0.89**, J3 0.78, U1 0.63, J121 0.64 (antinode (0.0, 52.5)). R8 U4 **0.18**, U5 0.18 (antinode (46.0, 60.5), C84 0.81, J9 0.84). R7 U4 0.72, U5 0.77 (antinode (46.0, 61.5)). **Relative response at U4** (Miles, Q 10, flat 0.04 g²/Hz GEVS-workmanship analogue, participation factor of the mass-normalised mode; trend only, Inference): R9 mode 1 18.1 g rms, RSS of modes 1–6 18.8; R8 3.7 / 8.4; R7 16.3 / 19.0. Mode 1 carries 54 % effective mass on both R8 and R9. **Support alternatives on R9's geometry:** (42, 55.5) 257.4 Hz / 18.6; (4, 49.5) 248.8 Hz / 6.4; (4, 59.5) 251.0 Hz / 13.8; interior (30.5, 50) 357.4 Hz / 15.6; (16, 52) 374.4 Hz / 6.3. **Legal-spot scan** (y 34–68, 0.5 mm grid; courtyards and pads ≥ 3.8 mm top / 3.5 mm bottom, stricter than fit_check's bodies; no non-GND track or via within 2.1 mm; hole edges ≥ 1 mm apart): no spot but the existing (42, 59.5) region. (4, 49.5) fails on U5's courtyard (U5 at (5.6, 50.6), bottom, x 2.8–8.4, y 48.3–52.9). **Records:** M3_R9 l. 224–231 and R9_VALIDATION l. 144 give f1 and the (0, 54) deflection, nothing on U4's mode position. D-S3-08 / D-S6-09 chose (42, 59.5) on "the DC solve holds" alone. plan_flowline.md l. 203 | (1) Record U4's and U5's modal position and the R7 / R8 / R9 comparison in M3_R9 §"Mechanical", and add the consequence to R9_VALIDATION's D-row for D-S3-08 / D-S6-09, so the owner accepts the east support knowing it. Give the alternative there too: the (4, 49.5) fallback or a near-U4 interior support, which needs U5 and some west-band routing re-placed (not measured beyond the scan). (2) ORDERING §5 tap check: put the external accelerometer at U4's location ((12.0, 47.4), bottom) or at the west edge's mid-span (0, 52), and log U4 at its highest output rate during the tap, or on a shaker or static motor test, so F1's vibration-sensitivity measurement uses the board's real exposure |
| R9P1-MECHANICAL-02 | Minor (worth fixing: text only) | P1 ("Record final outline, orientation and bay stack in the revision record (M3_R9.md) and parent VEHICLE"); P2 (sled); owner decision 1 (harness sides); R7 P3-MECHANICAL-03 | **The bay-stack and harness records are incomplete, and one harness instruction cannot be followed on the top side.** (a) M3_R9 has no bay-stack text (M3_R7 had a "Placement and orientation in the bay" paragraph); it points to a step handoff. (b) The proposed VEHICLE row repeats an omission R7 P3-MECHANICAL-03 asked to fix: it gives no standoff height. The sled tongue must pass under the SMA plug nuts, 2.6 mm below the bottom face, so the standoffs must be ≥ 3.5 mm (ORDERING §7). (c) The proposal names J1's forward entry but not its consequence: the battery leads run the board's length and turn back into J1 beyond the forward edge, inside the "eyebolt nut and charge wiring ~25" zone, which allocates no room for that bend. (d) Neither the proposal nor M3_R9 records the owner's harness sides (battery east, igniter and ARM leads west), which plan_spine §11 said to record in ORDERING §7 and the VEHICLE row. Only ORDERING §7 has them. (e) ORDERING §7 "Battery lead" says the leads "run along the bay's east wall to J1's forward entry". On the top side the east wall is closed: J9's mated camera plug comes within 0.03 mm of the wall allowance. So the run must pass below the board and sled, or over the top inboard of J9, and the forward-edge bend must clear the (42, 98) standoff boss. **Related (Inference):** turning J122 puts each servo plug's three contacts fore-aft (y 59.46 / 62.0 / 64.54). A flat three-wire servo ribbon then bends easily only sideways (±x), not aft toward the raceway. The R5 23.5 mm envelope was drawn for the unturned header and is "physical fit unverified" | `docs/M3_R9.md` l. 224–231: "the stack row (parent VEHICLE.md) changes (proposed in `r9_step10_handoff.md`)". `r9_step10_handoff.md` l. 73–92: the proposed row (… "nylon standoffs at the five M3 holes … clears the bottom parts, which hang up to 3.0 mm below the board" …), with no standoff height, U-turn or harness sides. R7 `pass3_mechanical.md` l. 73 (P3-MECHANICAL-03). `plan_spine.md` l. 244–245 (§11). ORDERING l. 203 (east wall), l. 210 (Sled), l. 211 (standoffs ≥ 3.5 mm). fit_check: J9 mated x 40.95–45.20, z 0–10.30, margin 0.028 mm (y 44.1–52.3); C84 1.367 mm (y 75.25–85.75); J123 mated 2.36 mm (y 27.85–32.45). The slack arithmetic of the proposal is right: 595 − (80 + 44…48 + 102 + 25 + 260) = 80–84 mm (loops beside the shroud); with the aft edge at joint +91…95, 68–72 mm; "~68–84 mm" | (1) Copy the stack row into M3_R9 §"Mechanical" as a short "Placement and orientation in the bay" paragraph, as M3_R7 has. (2) Add to the proposed row: "standoffs ≥ 3.5 mm (the sled tongue passes under the SMA plug nuts, 2.6 mm below the bottom face); the battery leads run aft-to-forward along the east side, below the sled (the top-side east wall is closed by the camera plug), and turn back into J1 beyond the forward edge, so allow that bend forward of the board; the igniter and ARM leads run along the west side". (3) ORDERING §7 "Battery lead": say "along the east side, below the board and sled (the top side is closed by J9's plug), turning up round the forward edge into J1"; "Sled": leave the forward end open for that bend. (4) Add the servo-lead dress over the turned header to the bench harness-fit list (P2 "qualify actual … harness … fit") |
| R9P1-MECHANICAL-03 | Minor (worth fixing: one clause) | P2 text; M2 (R8 list accepted) | **REQUIREMENTS P2 contradicts M2 on R8.** P2 says "the owner's ruling on the sixth support for R8 is open, R8_VALIDATION C10". M2 says R8's deviation list, "including the C10 vibration item", was accepted on 2026-10-20. Step 10 left the sentence as written; R9 does not depend on it | `docs/REQUIREMENTS.md` l. 67 (P2) against l. 75 (M2: "accepted by the owner on 2026-10-20, including the C10 vibration item"). `r9_step10_handoff.md` §5: "R8-era text left as written" | P2: "… (R8: f1 is 13 % below R6's; accepted with R8's deviation list (C10) on 2026-10-20)" |
| R9P1-MECHANICAL-04 | Minor (worth fixing: text only) | P2 (nylon hardware); P3 (staking, MEMS); MECHANICAL-05 precedent; AGENTS §2.5 | **ORDERING's assembly notes do not name R9's new neighbours of the hardware, staking and foam sites.** (a) **Hardware.** The records say only GND copper lies under the support hardware, but power, enable and status tracks run there. At (42, 59.5), RAW_PROTECTED, the battery-derived rail feeding the camera eFuse U7 (0.40 mm F.Cu), passes 0.55 mm from the hole edge under the top washer, in the 2.40 mm web between the hole and the east edge. BAT_FAULT_N and LOGIC_SOURCE_ST (B.Cu) pass under the bottom standoff. At (42, 98), BAT_ENABLE (F.Cu) lies under the top washer and BAT_FAULT_N (B.Cu) under the standoff; BAT_ENABLE is U9's enable node, and about 0.8 MΩ of leakage across the switch turns the board on (ORDERING §7). Everything is masked and nylon is mandatory, so nothing fails, but "GND pours" is the only reason the records give for nylon (cf. R7's BUZZ_DRV, MECHANICAL-05). (b) **SMA staking.** The fillet goes "along the four GND legs on both faces", kept off the centre pad, the RF line and D30/D31 only. On R9, C303's DNP tuning land (pad 1 on the GNSS RF node) is 0.81 mm from J30's east top leg pad, and C302 / L30 are 1.37–1.49 mm from the west one. On the bottom, the limiter's R300 / R303 are 2.28 / 3.18 mm from J30's legs. R7 and R8 had C303 at 3.40 mm and nothing on the bottom within 5.6 mm. Epoxy there loads the GNSS RF node and blocks later re-tuning of C303 (a VNA land, ORDERING §4). (c) **C121.** Its staking fillet ("on all sides") is 1.33 mm from the east tie hole (30.8, 59), courtyard to hole edge. (d) **Foam.** ORDERING §7 puts open-cell foam over U5, whose body is 2.4 mm from U4's (courtyards 1.71 mm); §5 keeps resin 3 mm off U4 but says nothing on the foam | pcbnew, copper edge from the hole centre (r 1.6). **(42, 59.5):** F.Cu RAW_PROTECTED **2.150** / 2.947 (washer r 3.5); B.Cu BAT_FAULT_N **2.371** / 2.778, LOGIC_SOURCE_ST **3.132** (standoff r ≤ 3.2). **(42, 98):** B.Cu BAT_FAULT_N **2.900**; F.Cu BAT_ENABLE **3.101**. (4, 4), (4, 98), (42, 4): no non-GND copper within 5 mm. `requalify_r9.json` `mech.holes` lists pads and fills only. R9_VALIDATION l. 146 ("GND on all four layers within each washer radius and no other net's fill"); ORDERING l. 211 ("Nylon, because the GND pours …"). **Jack legs** (courtyard to leg pad, mm): R9 J30.2–C303 **0.81**, J30.1–C302 1.37, J30.1–L30 1.49, J30.3–R300 **2.28**, J30.3–R303 3.18; R7 / R8 J30.2–C303 3.40, J30.3–R300 5.63 (same script on `431025d` / `cc044ea0…`). C303 (14.53, 5.76) DNP, C302 (11.32, 6.18), L30 (13.127, 6.18), R300 (8.775, 7.4, bottom). ORDERING l. 149 (staking), l. 211 (hardware), §7 "Foam". U4 box x 10.50–13.50, U5 box x 3.10–8.10 (fit_check) | ORDERING §7 Mounting hardware and R9_VALIDATION "Holes and washers": name the masked RAW_PROTECTED / BAT_ENABLE tracks under the top washers and BAT_FAULT_N / LOGIC_SOURCE_ST under the standoffs (nylon only, no over-torque). ORDERING §5 Staking: "on J30 stop the fillet at the leg pads' inner ends (y ≤ 4.4) and keep it off C302, C303 (a tuning land on the RF node), L30, R300 and R303"; "keep C121's fillet off the tie hole (30.8, 59)". §7 Foam: "trimmed to U5, off U4". Optionally extend `requalify_r9.py` `mech.holes` to list tracks within the hardware radii. No copper change |
| R9P1-MECHANICAL-05 | Minor | P2 (fit of fitted parts); AGENTS §3 (dimensions from the maker's drawing) | **The DB128L's stacking nubs are not modelled, and R9 is the first revision to place a terminal against another body.** The DORABO drawing shows two 0.57 mm nubs on one end face (body N × 5.08 + 0.57 mm). The 3D model, a centred 10.16 mm box, and the courtyard leave them out. R9 places J121 and J124 end to end (courtyards abutting, bodies 0.07 mm apart), which the footprint description intends ("end-stackable, two make the 4P envelope"). The pair's free forward end (J124) is 0.82 mm nominal from J1's back face, 0.25 mm if the nub end faces J1. The tolerance stack (length ±0.50, pin-to-face ±0.20, 0.8 × 1.05 mm pins in 1.6 mm holes) can close it. On R8, J124 was 7 mm from J1. The nub end follows the part's orientation, which JLC sets (theta 0 through PAD_ALIAS). My reading of the top view, with the entry face at the top, puts the nubs on the left end seen from the entry side, which is the aft end on this board. If so, J124's nubs enter J121's grooves and J124's forward end is plain. That reading is an Inference. The consequence is small: plastic-to-plastic contact, with J124 or J1 seated slightly proud | DORABO DB128L-5.08-XXP-C-S drawing: height 14.10, depth 10.10 with the pin row 5.00 from one face, pins 0.80 × 1.05, 3.50 ± 0.30 below the body, length N × 5.08 plus a 0.57 mm nub pair on one end face (top view); GB/T 14486-2008 tolerances ±0.50 (over 10 to 30 mm), ±0.20 (to 6 mm). `kilib/rocket.3dshapes/M3_DB128L_2P_BK.wrl`: "10.16 x 10.7 (incl tolerance/tongue) x 14.4". fit_check boxes: J121 y 68.19–78.35, J124 y 78.42–88.58 (x 4.75–15.45); J1 x 9.20–30.80, y 89.05–99.75 (the box includes 0.35 mm of tolerance). J1's footprint: "pin row 5.00 from the back face" puts the nominal back face at y 94.40 − 5.00 = 89.40. Courtyards: J124 to 88.615, J1 from 88.855 (0.24 mm). M3_R4 AG5 kept small parts clear of "a 0.6 mm dovetail tongue … on either end" | ORDERING §4 THT remarks: "J121 and J124 are fitted as one interlocked pair (DB128L end-stacking nubs into the neighbour's grooves); the pair's free forward end (J124) must not bear on J1". First article: check J124 and J1 seat flat. Optionally add the nubs to the DB128L envelope on the confirmed end, so fit and courtyard checks see them |

## 4. Measurements (board `fc3d5b34…`)

### 4.1 Outline (P1)

- **Edge.Cuts:** four lines (0, 0)–(46, 0)–(46, 102)–(0, 102), square corners, 0.05 mm strokes.
- **Holes:** seven Ø3.2 circles:
  - supports at (4, 4), (42, 4), (4, 98), (42, 98) and (42, 59.5);
  - tie holes at (15.6, 62) and (30.8, 59).
- **Edge webs:** 2.40 mm hole edge to board edge at every support, the mid support included (east edge).
- **Title-block revision:** "M3-ASSY-R9". Board thickness 1.6 mm.
- **Length:** 102 mm is owner decision 1's last fallback (98 and 100 mm failed legalisation, D-S3-03). Every record
  says 102 mm: M3_R9, R9_VALIDATION, REQUIREMENTS P1 / F10, ORDERING, AGENTS and the VEHICLE proposal.
- **Orientation:** recorded in ORDERING l. 5 ("y = 0 is the aft edge, where the two SMA jacks are") and in M3_R9
  "Placement".

### 4.2 Bore fit (P2, `fit_check`)

Radius 24.9 mm (Ø50.8 less 0.5), axis x 23.0, ±0.3 mm sled tolerance, top face on the axis.

| Item | Box x; z (mm) | Margin R9 | R8 |
|---|---|---|---|
| J9 mated (GH, R6 position) | 40.95–45.20; 0–10.30 | 0.028 | 0.028 |
| J122 mated (turned, plugs along x) | 17.92–28.08; 0–23.50 | 0.500 | 0.715 |
| J3 (USB-C, 0.45 mm over the west edge) | −0.45–7.45; −0.85–3.25 | 0.886 | 0.886 |
| J121 / J124 (DB128L, 14.4 mm envelope) | 4.75–15.45; 0–14.40 | 1.232 | 1.153 |
| C84 (OS-CON Ø10, 12.8 mm) | 31.75–42.25; 0–12.80 | 1.367 | 1.366 |
| J123 mated (PH) | 37.00–43.00; 0–9.50 | 2.358 | — |
| Worst bottom: C72 / C73 (1210, bottom, east edge) | 42.06–44.76; −4.30…−1.60 | 2.37 | 2.36 (C91) |
| Deepest bottom part: L1 (40.0, 76.6) | −4.62 (3.02 mm below the bottom face) | — | same |

- The 0.50 mm J122 figure follows directly from turning the ±5.08 × ±4.0 mm envelope by 90°:
  √(24.9² − (5.08 + 0.3)²) − 0.3 − 23.5 = 0.51 mm.
- It is the recorded owner default with check_r9's M-5 floor of 0.49 mm.

### 4.3 Supports and hardware (P2)

Distances are from each hole centre; the hole is r 1.6 mm. "Top" uses the 3.8 mm rule (7 mm washer + 0.3 mm), bottom
the 3.5 mm rule.

| Support | Nearest top body / exposed pad | Nearest bottom part / exposed pad | Non-GND copper within washer (F.Cu, r 3.5) / standoff (B.Cu, r 3.2) |
|---|---|---|---|
| (4, 4) | U30 courtyard 3.849 (body box 5.36); TP30.1 5.009, U30.18 5.013 | R300 courtyard 4.248; R300.2 4.682 (fit_check's model box 4.600) | none |
| (42, 4) | J31 courtyard 6.215; J31.2 6.561 | J31.4 6.561 | none |
| (4, 98) | J1 courtyard 4.955; J1.4 7.821 | J1.4 7.821 | none |
| (42, 98) | R166 courtyard 4.785; R166.1 5.030 | R83 courtyard 4.375; R83.1 4.626 | F.Cu BAT_ENABLE 3.101; B.Cu BAT_FAULT_N 2.900 |
| (42, 59.5) | TP76 courtyard 4.887; TP76.1 5.233 | C98 courtyard 4.365; C98.2 4.806 | F.Cu RAW_PROTECTED 2.150 (0.40 mm track, 0.55 mm from the hole edge), 2.947; B.Cu BAT_FAULT_N 2.371, 2.778; LOGIC_SOURCE_ST 3.132 |

- **Rules met.** Every top and bottom figure meets the 3.8 / 3.5 mm rules and check_r9's R8 floors (M-5: 4.452 /
  5.008). Every hole has GND fill on all four layers to 0.5 mm from its edge and no other net's fill
  (`requalify_r9.json` `mech.holes`, confirmed).
- **ORDERING's 9 mm washer remark** ("would clear every pad, by 0.12 mm") is right for pads (R83.1, 4.626 mm). It
  ignores U30's courtyard at (4, 4) (3.849 mm), so a 9 mm washer would land on U30's castellation zone, though not on a
  pad or the module body (body box 5.36 mm). The ≤ 7.0 mm rule stands.
- **Spans.** West edge 94.0 mm unsupported, from (4, 4) to (4, 98); east edge 55.5 + 38.5 mm; aft and forward pairs
  38.0 mm.
- **The mid support is effective.** f1 is 128.7 Hz with the corners only and 256.6 Hz with it, 2.0×. It lies in the
  middle third (y 34–68).

### 4.4 Plate model (P2; gate M-2)

`tools/plate_model.py` (R7 pass 2's code) on this board's fit report. The jacks are rigid overhangs, with the plugs
carried by the sled (P3). The values are f1 in Hz.

| Case | R9 | R8 `cc044ea0…` | R7 `431025d` |
|---|---|---|---|
| Pinned D 5 / D 10 | **256.6** / 362.9 | 208.7 / 295.1 | 221.0 / 312.5 |
| Clamped D 5 / D 10 | 434.8 / 614.9 | 346.3 / 489.7 | 376.8 / 532.8 |
| Plugs hanging on the jacks (P3 forbids), pinned D 5 | 183.7 | 173.2 | 176.1 |
| Corners only, pinned D 5 | 128.7 | 97.7 | 98.0 |
| Board mass, jacks only (g) | 47.1 | 49.8 | 49.8 |
| 100 g static, largest deflection (mm, at) | 0.66 (0, 54) | 0.98 (46, 63.5) | 0.91 (46, 64) |

All three columns come from the same tool on each board's own fit report. The R7 column reproduces R7 pass 2's
221 / 313 / 377 / 533 Hz.

**100 g quasi-static load (jacks only, D 5 pinned):**
- The largest deflection is R9 0.66 mm at (0, 54) against R8 0.98 mm at (46, 63.5).
- Peak principal strain, R9 against R8 (µε):

| Part | R9 | R8 |
|---|---|---|
| U31 | 434 | 578 |
| U30 | 484 | 496 |
| U4 | 405 | 483 |
| U1 | 488 | 578 |
| J121 | 780 | 899 |
| J124 | 840 | 799 |
| C121 | 557 | 796 |
| C84 | 596 | 586 |
| U5 | 480 | 602 |
| J1 | 888 | 878 |
| J122 | 519 | 774 |

- U31, U1, U4, U5, C121 and J122 are 15–33 % lower than on R8. U30 (−2 %), C84 (+2 %), J1 (+1 %) and J124 (+5 %)
  are about equal.

**Mode shapes** (mass-normalised Ritz eigenvectors of the same `Plate`, normalised to the peak; Appendix):

| Board, mode 1 | Antinode | U4 | U5 | U1 | J3 | J121 | J124 | C84 | C121 | J9 |
|---|---|---|---|---|---|---|---|---|---|---|
| R9, 256.6 Hz | (0.0, 52.5) west edge | **0.76** | **0.89** | 0.63 | 0.78 | 0.64 | 0.42 | 0.12 | 0.23 | 0.05 |
| R8, 208.7 Hz | (46.0, 60.5) east edge | **0.18** | 0.18 | 0.46 | 0.09 | 0.48 | 0.17 | 0.81 | 0.22 | 0.84 |
| R7, 221.0 Hz | (46.0, 61.5) east edge | **0.72** | 0.77 | 0.47 | 0.03 | 0.51 | 0.18 | 0.13 | 0.69 | 0.81 |

- R9 mode 2 is at 473.9 Hz (antinode (46, 30.5)) and mode 4 at 709.9 Hz (26 % effective mass).
- R9 moves C84 off the antinode (R8 C10's cause, D75) and puts the IMU and the barometer on it.

**Relative response at U4** (Inference; a trend, not a qualification value):
- Method: Miles' equation per mode with the mass-normalised participation factor, Q 10, a flat 0.04 g²/Hz input (the
  DESIGN_ASSURANCE GEVS workmanship analogue).
- R9: 18.1 g rms in mode 1, 18.8 g rms over modes 1–6.
- R8: 3.7 / 8.4. R7: 16.3 / 19.0.
- The same metric for other mid-support spots on R9's geometry is in R9P1-MECHANICAL-01.
- The legal-spot scan finds no M3 position in y 34–68 but the existing one, so moving the support means re-placing
  parts (U5 above all).

**Screwdriver push** (a 40 N point load on each terminal, pinned D 5; Inference; checked for regressions):
- J121 1.04 mm, J124 0.57 mm, J1 0.32 mm.
- R8: J121 1.03 mm (east edge), J124 0.53 mm, J1 0.35 mm.
- No regression.

### 4.5 SMA jacks (F10, P2, P3)

- **Placement.** J30 (GNSS) at x 13.59 and J31 (RADIO) at x 32.29 on y = 0, rotation 0, 18.70 mm apart; check_r9
  R-3 / R-4 hold them.
  - The jack bodies reach 9.5 mm beyond the edge, the mated plugs 25.5 mm.
  - The margins are 9.6 mm mated and 11.2 mm for the body.
  - No rail or tab on the aft edge (ORDERING §3).
- **Leg pads.** Pads 1–4 are 1.2 × 4.2 mm at x ±2.55, y 0.2–4.4, with six GND stitching vias at 0.20 mm from each
  leg pad. The staking fillet runs "along the four GND legs on both faces". Nearest courtyards to each leg pad (mm),
  R9 against R7 and R8, which are equal:

| Pad | R9 | R7 / R8 |
|---|---|---|
| J30 pad 1 (F, west leg) | D30 1.04, C302 1.37, L30 1.49 | C302 1.37, L30 1.49, D30 1.67 |
| J30 pad 2 (F, east leg) | **C303 0.81** (DNP shunt land at the bias node, pad 1 on GNSS_RF_ANT; D-S4-02), D30 1.67, L30 2.05 | D30 1.04, L30 2.05; C303 3.40 |
| J30 pad 3 (B, west leg) | **R300 2.28**, R303 3.18, Q32 3.96 (the limiter under U30, D-S4-03) | R300 5.63 |
| J30 pad 4 (B, east leg) | R303 3.44 | none |
| J31 pads 1–4 | D31 1.04 / 1.67 (F); nothing on the bottom | identical |

  - ORDERING §5 keeps the fillet off "the centre pad, the RF line and D30/D31" only. On J30, C303's tuning land
    (an RF-node stub) and the limiter resistors are now within reach: **R9P1-MECHANICAL-04**.
- **Supports beside the jacks.** The corner standoffs (Ø ≤ 6.4 at x 4 / 42) are 3.1 mm from the jacks' 6.5 mm
  flanges.
- **Retention chain.** Present for R9: REQUIREMENTS P3; ORDERING §5 counter-hold, torque and staking order; §7 Sled
  (tongue, saddle at the plug axis 0.45 mm above the top face, relief for the flanges 1.2–1.4 mm below and the nuts
  2.6 mm below the bottom face); MARGIN_PRESCRIPTION R14 (R7).

### 4.6 Terminals, lead directions, wire room

- **Entries.** J121 (10.1, 73.27) and J124 (10.1, 83.5), rotation 90, both enter −x. J1 (20.0, 94.4), rotation 180,
  enters +y.
  - check_r9 P-11 and M-4 confirm the entries.
  - The `M3_DB128*` footprints enter on local −y, and `entry_dir` agrees with the arrows.
  - Silkscreen "<" arrows sit under J121 and J124 at x 6.7–7.5 at each pin, pointing −x; "V" arrows sit under J1 at
    y 97.0–97.8, pointing +y.
  - Legends: "IGN" (3.46, 67.63) and "1:E1-" at J121's aft end, "ARM" (4.03, 89.91) and "2:RAW" at J124's forward
    end, the bottom-face pin legends, and "J124 2-FUSE-1: ARM LAST".
- **Wire room.** 6.353 mm (P-11, R8 6.253) and 6.4–7.0 mm at 5 mm height (fit_check).
  - The DB128L drawing puts the pin row 5.00 mm from one face of a 10.10 mm body.
  - The model's entry face (x 4.75, ±5.35 about the pin row) is therefore 0.25–0.35 mm conservative.
- **Shared west channel.** J121's igniter leads run forward past J124's entry face, which also takes the ARM link's
  two wires.
  - The channel between J124's face and the wall is about 6–7 mm wide at 0–5 mm height and about 4.3 mm at 10 mm
    height.
  - Four 22 AWG wires fit (Inference).
  - ORDERING §7 records the shared edge and the need to route and label the harnesses so they cannot be swapped.
- **Swap detection.** A swap (igniter into J124, ARM link into J121) would read "armed" on ARM1_SENSE and "no
  continuity" before the link goes in, so the ground pre-arm refusals see it (Inference; firmware not written).
- **J1.** Courtyard face 1.855 mm from the forward edge, nothing in front (M-4); J1 to J121 23.33 mm and to J124
  14.72 mm (≤ 25).
- **DB128L stacking and body gaps.** The drawing and the J124 / J1 gaps are covered in R9P1-MECHANICAL-05.
- **Pin tails.** DB128L pins are 3.50 ± 0.30 mm below the body, so they stand 1.6–2.2 mm below the bottom face,
  under the ≥ 3.5 mm standoffs.

### 4.7 J122 turned, and its retention tie (P2, P3)

- **Position.** J122 sits at (23.0, 62.0), rotation 180, on the roll axis. Plug columns are at x 19.19 / 21.73 /
  24.27 / 26.81; signal row y 59.46, RAW_ACT y 62.0, GND y 64.54.
- **Tie holes.** (15.6, 62) and (30.8, 59), 2.28 and 2.68 mm past the courtyard ends (M-3: 1–4 mm). The tie line
  crosses the plugs 0.71–2.21 mm off their centre lines, inside their ±3.81 mm length.
  - The nearest bottom part to the line is R124, 2.007 mm away, so a 2.5 mm tie clears it by 0.75 mm.
- **Hole rims.** The tie bears on each hole's rim on the side facing J122.
  - West hole: R178 (PYRO1_CONT divider) is 0.41 mm from the rim on the west side, away from the tie.
  - East hole: the ARM1_SENSE lane is 0.57 mm from the rim (F.Cu, masked); TP90 is on the far side.
  - The tie is nylon, so neither is an electrical concern.
- **Staking near the east hole.** C121's staking fillet ("on all sides") can reach the east hole: its courtyard is
  1.33 mm from the hole edge (part of R9P1-MECHANICAL-04).
- **Tie size.** A Ø3.2 hole passes a 2.5 × 1.0 mm tie but not a standard 3.6 mm one (Inference, band diagonal),
  inherited from R5–R8.
- **Servo-lead dress.** See R9P1-MECHANICAL-02 (Inference).

### 4.8 IMU (F1, F5; check_r9 M-7)

- **Pad copper.** U4 is on the bottom at (12.0, 47.4), rotation 180. Pad 1 (SPI1_MISO) is at (13.21, 46.65), offset
  (+1.21, −0.75) mm.
  - R5 recorded (−1.21, +0.75) for the bottom at rotation 0 (M3_R5 §3).
  - So the R9 map is R8's turned 180° about z: +X_imu = −x_board, +Y_imu = −y_board, +Z_imu out of the bottom face.
    This is right-handed in KiCad's frame.
  - Roll about +y_board reads −gyro_Y, thrust reads −a_Y, and "forward edge up" reads a_Y = −1 g.
  - All match the binding note, M3_R9, ORDERING §5 and AGENTS.
- **M-7 gate.** It keys 180° on revision "M3-ASSY-R9" (`IMU_ROTATION_R9`), so an accidental turn fails. Lever arm
  |x − 23| = 11.000 mm (the done row ≤ 11 is met at its limit; gate ≤ 13). No via or fill lies under U4 or U5 on
  B.Cu.
- **Centripetal term.** The 1.17 g figure at 1850 °/s is the x component: ω² × 11.0 mm.
  - With z = −2.06 mm, the full lever arm is 11.19 mm: 1.19 g toward the axis, with 0.22 g along +z_top, read as
    −a_Z.
  - The binding note carries z, so firmware can include it. Observation only.
- **Modal exposure.** See R9P1-MECHANICAL-01.

### 4.9 Tall parts and staking (P3)

**Tall parts** (heights in mm):

| Part | Height | Staked by ORDERING §5 |
|---|---|---|
| J1 (DB128V) | 14.5 | Yes ("the three screw terminals") |
| J121 / J124 (DB128L, drawing 14.10) | 14.4 envelope | Yes ("the three screw terminals") |
| C84 | 12.8 | Yes |
| C121 | 10.5 | Yes |
| J122 | 8.54 (23.5 mated) | Yes; the mated servo plugs get zip ties |
| J123 | 6.0 (9.5 mated) | Yes; epoxy or RTV on the PH plug |
| J30 / J31 | Body 3.8 above / 2.9 below the top face; overhang 9.5 mm | After the RF tests |
| J9 | 4.2 | No: low, SMD GH with retention tabs; GH plug latch |
| J3 | 3.25 | No |
| L1 / L3 (bottom) | 3.0 | No (bottom cans, SMD) |
| LS120 | 2.5 | No |
| U30 / U31 | ≤ 2.7 | No: 0.5 g each, no adhesive (u-blox IM §5.2) |

- Every two-terminal tall part is staked, as R7 pass 2 found for the same parts. No staking site lies over or near
  U4 or U5 (C84 at (37, 80.5), C121 at (33.4, 66.6); `ordering_facts.json` `under`).

### 4.10 Bay stack and harness (P1; parent VEHICLE.md)

- **The proposed row checks out** (`r9_step10_handoff.md` §4):
  - length 102, the hole list, the 9.5 mm jack overhang, J1's forward entry, the pyro entries from x = 0, the 3.0 mm
    bottom parts;
  - the slack ("~68–84 mm with R9; ~52–68 mm with R8"): 595 − (80 + 44…48 + 102 + 25 + 260) = 80–84 mm with the
    loops beside the shroud, and with the aft edge at joint +91…95 and the board forward of it, 68–72 mm.
- **What it leaves out** is R9P1-MECHANICAL-02: standoff height, the leads' U-turn, harness sides, and the M3_R9
  copy.
- **Coupler bore.** The board's forward end crosses the coupler's forward end (joint +120; Ø54.6 above it) for
  most positions. fit_check uses Ø50.8 everywhere, which is conservative.
- **Shroud.** The camera shroud (joint +4…+47, 18.4 mm from the axis) limits only the coax loops (REQUIREMENTS
  "Board position"), unchanged from R7.

## 5. Checked, no finding

- Board width 46.00 mm; length 102 mm ≤ 120 (fit_check); the strip is y 0–22.0 with its contents held by check_r9 R-1…R-13 (passes).
- Every footprint has a readable 3D model (fit_check fails otherwise). The R9 variants reuse the base models: DB128L, a centred box; the 3 × 4 header, symmetric. The mated envelopes are reviewed per reference (J9, J30/J31, J122 `_MIR`, J123).
- No mated envelope intersects another part's box (fit_check).
- No bottom part has through-hole pads. Bottom parts are ≥ 1.5 mm from through-hole pads, ≥ 3.5 mm from M3 centres and ≥ 1.0 mm from the pyro via (check_r9 M-6).
- The coat region (PYRO_BLOCK + J2) is 5.526 mm from U4 and holds no test pad but TP122 (P-10).
- T-1 holds. The tab plan's four tabs keep the east middle third (beside the (42, 59.5) hole, 2.4 mm web) free of mouse bites.
- The J1 / J121 / J124 THT orientation remarks to JLC ("every terminal's wire entry faces the nearest board edge", ORDERING l. 107) and the silkscreen arrows agree with the entries.
- jlc_orient's PAD_ALIAS keeps the DB128L body unturned (theta 0; D-S2-08), so a mirrored-numbering 180° turn cannot slip through.
- J3 overhangs the west edge by 0.45 mm (margin 0.886 mm, as R8). J9's courtyard reaches 0.045 mm beyond the east edge; its body ends 0.82 mm inside (DFM dimension; inherited from R6).
- R8's plate result was reproduced (208.7 Hz) with the R9 tool, so the R9/R8 comparison uses one method.

## 6. Sources

- DORABO DB128L-5.08-XXP-C-S customer drawing, LCSC C430601: height 14.10; depth 10.10 with the pin row 5.00 from a face; pins 0.80 × 1.05, 3.50 ± 0.30 long; N × 5.08 length with a 0.57 mm nub pair on one end; GB/T 14486-2008 tolerances.
  https://datasheet.lcsc.com/datasheet/pdf/774f77501d8e260538e3ee59c3ecee93.pdf?productCode=C430601 (page via https://www.lcsc.com/datasheet/C430601.pdf).
- Kinghelm KH-SMA-KE8-G (LCSC C530661), as cited in ORDERING §5 and R7 pass 2 / pass 3 (not re-fetched; same footprint and documents).
- Project files:
  - `tools/fit_check.py`, `tools/plate_model.py`, `tools/check_r9.py` (M-2…M-7, P-10, P-11, T-1);
  - `docs/REQUIREMENTS.md` P1–P3 (l. 66–68) and M2 (l. 75);
  - `docs/ORDERING.md` l. 5, 97, 105–107, 149, 170, 201–211;
  - `docs/M3_R9.md` l. 57–82, 224–247;
  - `docs/R9_VALIDATION.md` l. 140–153;
  - `R9_DECISIONS.md` D-S1-11, D-S1-21, D-S2-01, D-S2-08, D-S3-08, D-S6-09, D-S7-06, D-S10-11, D-S10-18;
  - `R9_OWNER_DECISIONS.md` items 1 and 5;
  - `plan_spine.md` §1, §11, §13;
  - `plan_flowline.md` l. 203;
  - `r9_step10_handoff.md` §4–§5;
  - `step10_evidence/requalify_r9.json` (`mech.*`, `imu`), `r9_binding_note.json`, `gate/plate.json`;
  - `kilib/rocket.pretty/M3_DB128L_2P_BK.kicad_mod`, `M3_DB128V_4P_Entry.kicad_mod`;
  - `kilib/rocket.3dshapes/M3_DB128L_2P_BK.wrl`, `M3_DB128V_4P.wrl`;
  - R7 `sources/r7_review/pass2_mechanical.md`, `pass3_mechanical.md`;
  - `docs/M3_R5.md` §3 (bottom-side IMU map);
  - `docs/M3_R4.md` AG5 (DB128L tongue);
  - parent `docs/VEHICLE.md` (stack row, coupler, shroud).

## 7. Inferences (not measured, not from a maker document)

- **Plate model inputs** (D 5–10 N·m, laminate 3.65 kg/m², lumped masses, point supports) are R7 pass 2's
  inferences. The R7 / R8 / R9 ratios are the robust result.
- **The modal response at U4** (Miles, Q 10, a flat 0.04 g²/Hz input) is a relative trend. No measured PSD exists for
  these motors.
- **Low-g saturation and gyro vibration rectification** are qualitative consequences, not measured.
- **The 40 N screwdriver push** is an assumed load.
- **The DB128L nub end on this board (aft)** is read from the drawing's top view and needs a first-article
  confirmation. The ≈ 6–7 mm wire channel's capacity for four 22 AWG wires is also an Inference.
- **The servo-ribbon bend direction** over the turned header assumes a flat bonded three-wire lead.
- **The tie-band width** passing a Ø3.2 hole is band-diagonal geometry.
- **The ground pre-arm refusals catching a terminal swap** depend on firmware that does not exist yet.

## Appendix: modal participation (numpy; uses `tools/plate_model.py` unchanged)

```python
import json, math, numpy as np, sys
sys.path.insert(0, 'tools'); import plate_model as PM
fit = json.load(open(FIT_JSON))                       # tools/fit_check.py --report output
p, masses, total = PM.build(fit, 5.0, False, 'jacks_only')   # optionally fit['supports'] = [...] for other spots
Z = p.basis(); Kr, Mr = Z.T @ p.K @ Z, Z.T @ p.M @ Z
Li = np.linalg.inv(np.linalg.cholesky(Mr)); A = Li @ Kr @ Li.T; w2, V = np.linalg.eigh((A + A.T) / 2)
one = np.zeros(p.K.shape[0]); one[0] = 1.0             # rigid translation (P0 P0 = 1)
for i in range(6):
    f = math.sqrt(w2[i]) / (2 * math.pi); c = Z @ (Li.T @ V[:, i])     # mass-normalised mode
    gam = float(c @ (p.M @ one))                                      # participation factor
    x, y = masses['U4'][1], masses['U4'][2]
    phi = float(p.field(c, np.array([x]), np.array([y]))[0, 0])
    print(f, gam * phi * math.sqrt(math.pi / 2 * f * 10 * 0.04))      # g rms, Q 10, 0.04 g^2/Hz
```

Mode-shape tables normalise `p.field(c, …)` by its peak over a 0.5 mm raster. The legal-spot scan kept every
courtyard and pad ≥ 3.8 mm (top) and ≥ 3.5 mm (bottom) from the centre, stricter than fit_check, which uses bodies and
exposed pads. It kept non-GND tracks and vias ≥ 2.1 mm from the centre on every layer (hole r 1.6 + 0.5 mm
copper-to-edge) and hole edges ≥ 1 mm apart, on a 0.5 mm grid over x 2.5–43.5, y 34–68. Plane fills were ignored
(a hole would refill round them). Its control case, the existing (42, 59.5), passes.
