# R7 review pass 2: requirements conformance and documents

Reviewer: independent, pass 2, dimension "requirements conformance and document consistency".
Board reviewed: `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
`03fe75720f46b1382d9d3216dbffd8ae642d0125722c04589ff97c964aa86d54` (unchanged before and after this review;
checked 2026-10-16 05:55Z). Fab package: `m3_design/assembly_review/fab/` (`tools/fab_manifest.py`: OK, 5 outputs
bound to the current CAD). Baseline for comparison: R6 board from `git show 3b215ba:...` (SHA-256 `184a87e8…0680`),
translated +18 mm in y. Read-only review: no repository file was changed except this report.

## 1. Summary

The R7 CAD meets the large majority of REQUIREMENTS as written. `tools/check.sh` reproduces clean on the
reviewed board (DRC 0, unconnected 0, parity 0, ERC 0, audit OK, silkscreen 0, R7 contract OK, actuator contract
OK, fit OK). The F10 pin contract, reset-state parts, supplies, RF chain, jack positions, keep-outs, stackup, the P1
outline, the P2 envelopes and supports, and M3 cost (US$110.93 per board with 52 extended codes) all check out on
the board and the fab files. The parent CLAUDE.md avionics decisions on disk (on-board MAX-F10S and E22-900MM22S,
SMA antennas, board ≤ 120 mm, uplink can never arm or fire, single pyro channel, isolated Blue Jay) are met.

The review found **0 Critical, 3 Major and 10 Minor** issues:

- **Major REQUIREMENTS-01: P3 cannot be met as written, and ORDERING says the opposite.** P3 requires J2 to be
  locally coated. J2 has been bare TC2030 pads since R6, and ORDERING §5 says to keep coating off them. The bare
  NRST pad sits 0.483 mm from the bare GND pad. The leak that would hold the MCU in reset (about 13–21 kΩ) is in the
  same range that made pyro coating mandatory. The item is still undecided.
- **Major REQUIREMENTS-02: P2's support-span and vibration estimate was not redone for R7.** The free right edge
  grew from 92.4 to 110.4 mm and the left aft bay from 42 to 60 mm, and both SMA jacks with mated plugs now hang
  beyond the aft edge. No R7 document tracks the estimate as open.
- **Major REQUIREMENTS-03: a via hole opens into a soldered SMD pad, which M2 forbids.** The via is in R100 pad 1
  (CAM_RX_WIRE, bottom side), inherited from R6. No gate tool checks M2's via-to-pad-opening rule.

The Minor findings are mostly document drift:
- the F4 solve wording (R6's solve still covers the servo path, shown below);
- F10's "GND on every copper layer" text, which no design could meet;
- the stale bay stack in the parent VEHICLE.md;
- an LS120 reflow rating that can now be closed;
- 0.12 mm LS120 silkscreen lines;
- antenna-lead labels;
- the M3 cost breakdown wording and the U4 consignment cost;
- one verification claim credited to the wrong tool;
- SMA retention at 100 g not assessed;
- small cross-document mismatches.

R7 acceptance status: the gate, M3 and fab-binding conditions are met now. The review condition (this pass), M1
stock (U4 consignment) and the three Majors above are open.

## 2. Findings

| ID | Sev. | Requirement | Finding | Evidence | Fix |
|---|---|---|---|---|---|
| REQUIREMENTS-01 | Major | P3 (pyro block and J2 coated); ORDERING §5 | P3 says, in bold, that J2 is coated. J2 is a TC2030 pad pattern (since R6), and ORDERING §5 says "keep coating off its six pads… how to protect the bare NRST pad is open". The requirement cannot be met and the build document contradicts it. A leak to GND on NRST holds the MCU in reset: no primary deployment, no servo pulses. | J2 pads (board, F.Cu, all with mask openings): 3 NRST at (43.635, 76.65), 5 GND at (43.635, 75.38), 4 SWCLK at (42.365, 76.65), 1 3V3 at (43.635, 77.92), all Ø0.787 mm. The bare NRST pad has edge gaps of **0.483 mm** to pads 5 (GND), 4 and 1. NRST pull-up 30–50 kΩ (REQUIREMENTS F6, from DS12110). With VIL(NRST) ≈ 0.3 VDD (DS12110; not re-read here, **Inference**), a leak of ≤ about 12.9–21.4 kΩ to GND holds reset. MARGIN_PRESCRIPTION line 108 judges 12–13 kΩ "entirely achievable on a damp FR-4 surface with black-powder residue". STATUS open items and R7_VALIDATION "Carried to pass 2" list it as undecided. | Decide and make P3 and ORDERING §5 agree. Options: (a) after the last programming, coat the J2 area too, and record that the TC2030 probe then needs the coating scraped off (or add a removable polyimide cover over J2, and a ≥ 1 MΩ NRST-to-GND bench reading after coating as a gate); (b) amend P3 to accept bare J2 pads with a recorded rationale and that leakage gate; (c) a board change that raises NRST's leak tolerance (check against ST's reset-pulse guidance before adding any external pull-up). |
| REQUIREMENTS-02 | Major | P2 ("Re-derive all positions and support-span/vibration estimates on final R7 geometry") | Not done, and not listed as open in STATUS, R7_VALIDATION, M3_R7 or ORDERING. pass1_layout §3 says outright "it is not done here". R7 lengthens every span and adds mass hanging off the aft edge, so R5's estimate no longer applies. | Supports (board Edge.Cuts): (4, 4), (42.3, 4), (4, 64), (4, 114.4), (42, 114.4). Unsupported right edge: R6 92.4 mm, R7 **110.4 mm**. Left aft bay: R6 42 mm, R7 **60 mm** (pass1_layout §3 agrees). J30/J31 bodies 9.5 mm beyond the aft edge, plus about 16 mm of mated plug each (fit_check envelope). R5's record (M3_R5 §1 table, R2): four corners about 140 Hz, with the mid-span hole about 270–290 Hz. Scaling the governing span (50.4 → 60 mm; right edge 92.4 → 110.4 mm) gives roughly 190–205 Hz before the added aft mass (**Inference**, not a substitute for the model). | Rerun the R5 plate model (or an FE model) on the R7 outline, supports and masses, including the jack and plug mass at the aft edge. Record the first-mode estimate in M3_R7, and list the item in STATUS until it is done. If the result is well below R5's, consider a support near the right edge's mid-span. |
| REQUIREMENTS-03 | Major | M2 ("No via holes open into soldered SMD pads, and every via hole ≥ 0.1 mm from a pad opening") | A CAM_RX_WIRE via hole lies inside the paste-printed pad 1 of R100 (1 kΩ 0603, bottom side, reflowed first and then upside down through the second reflow). Solder can wick into the 0.3 mm barrel and starve the joint. The functional consequence is limited to the camera RX line. The same via is on R6 at (42.175, 38.2731), so the R6 review missed it. No gate tool checks this M2 rule (DRC has no default via-in-pad rule; `check_r7` checks vias on through-hole pads only). M3_R4's claim of "via-to-pad mask dams ≥ 0.125 mm everywhere except the test pads" is no longer true. | Via at (42.175, **56.2731**), drill 0.30, Ø0.60, F.Cu–B.Cu, no via mask opening. R100.1 at (42.175, 56.65), 0.80 × 0.95 mm, mask expansion 0, so the opening spans y 56.175–57.125. The hole spans y 56.123–56.423: its centre is 0.098 mm inside the opening and about 0.25 mm of its 0.30 mm diameter opens into the pad. A whole-board scan (hole edge to SMD pad copper less mask expansion, bare TPs excluded) finds only this one case. | Move the via about 0.45 mm north (hole edge ≥ 0.1 mm outside the opening) or fan out from the pad end, then rerun DRC. Add a via-hole-to-pad-opening check to `check_r7.py` so M2 is enforced. |
| REQUIREMENTS-04 | Minor | F4 (solve the R7 copper) | F4 still records that the R7 copper "has not been re-solved". The comparison below shows the servo current path is copper-identical to R6, so R6's RAW_ACT 3.96 mΩ and BAT_IN 3.91 mΩ solves carry over. The document gap remains. | Zone outlines R6 (+18 mm) vs R7: RAW_ACT_F, R6_RAW_ACT_F, RAW_ACT_B, ACT_FET_S_B, BAT_IN_F, BAT_IN_B and R6_BAT_IN_crossbar_F are identical. R6_BAT_IN_In2 differs only aft of y 32.6: R7 starts at y 26 and loses the x 9.9–15 block at y 18.3–32.6. The only BAT_IN track change is a B.Cu jog at (9.3–10.62, 52.1–53.38). The servo path J1 → Q120 → Q121 → J122 lies at y ≥ 68. | Either run the solve on R7, or amend F4 and M3_R7 to accept R6's solve with this copper-identity evidence. Close the STATUS item either way. |
| REQUIREMENTS-05 | Minor | F10 ("every copper layer GND outside the module pads and RF lines"; "≥ 5 mm from … fast digital lines") | The literal text is not met, and no design could meet it: the module pins need interface leads inside the strip. F.Cu carries the GNSS/radio leads and 3V3 feeds. B.Cu carries the bias limiter plus RADIO_TXEN, RADIO_DIO1 and RADIO_NSS. In1/In2 are GND only. The deviations are recorded in stepB_handoff §3–4 and the RF risk is low. `check_r7.py` says these B.Cu exceptions are documented in M3_R7 "R7 board", but M3_R7 names only the limiter. | `check_r7` strip evidence: F.Cu 75 and B.Cu 39 track items, 195 vias; In1/In2 GND only (OK). Keep-outs: U31_KEEPOUT on all four layers, x 25.66–34.06, y 9.80–18.20; U30_KEEPOUT on F.Cu/In1, x 5.36–15.46, y 11.25–18.65 (u-blox: top two layers; EBYTE manual §4.1: no wiring under the module on any layer). My proximity scan (courtyard boxes): RADIO_DIO1 via 3.03 mm, RADIO_NRST 3.80 mm and RADIO_BUSY 4.72 mm from the U30 courtyard; SPI SCK/MOSI/MISO not within 5 mm of any GNSS RF part; no QSPI, SPI1, USB, SWD or HSE copper within 5 mm of any RF part; U2 9.56 mm, L1 10.76 mm, U1 23.46 mm, Y1 31.12 mm. | Amend F10 to say what the strip may hold: In1/In2 GND only; F.Cu and B.Cu GND-poured except module pads, the RF chain, module interface leads and the limiter; no copper but GND under U31 on any layer or under U30 on F.Cu/In1; slow control lines may pass within 3 mm of U30. Record acceptance in R7_VALIDATION, and point the `check_r7` comment at stepB_handoff §4 item 5 (or copy the list into M3_R7). |
| REQUIREMENTS-06 | Minor | P1 (record bay stack in M3_R7 and the parent VEHICLE); op. assumption "Board position" | The parent VEHICLE.md stack row still describes the R5 board ("flight computer board 100 (M3-ASSY-R5, 46 × 100 mm…)", mid-span support at (4, 46)), in both the committed and the uncommitted versions. M3_R7 records no bay stack. A sled built from VEHICLE would put the mid-span standoff 18 mm from the R7 hole at (4, 64). The board-position assumption ("aft edge about 70 mm below the coupler's forward end ± 3 mm") is the R6 figure. With VEHICLE's battery bay plus leads (95 mm above the bulkplate top at joint −44.6, i.e. up to joint +50.4) and ORDERING §7's ~40 mm coax zone aft of the board, that position overlaps the battery zone by about 40 mm (**Inference** from VEHICLE numbers). Tracked as open (L3). | `<parent repo>/docs/VEHICLE.md` line 39 ("Main-section stack…"); REQUIREMENTS op. assumptions "Board position"; ORDERING §7 "Antennas and coax" and "Sled". | Update the VEHICLE stack row to R7: 118 mm board, supports (4, 4), (42.3, 4), (4, 64), (4, 114.4), (42, 114.4), jacks and coax zone aft of the board. Record the stack and orientation in M3_R7. Mark the board-position figure as superseded until the shroud is measured. |
| REQUIREMENTS-07 | Minor | M1 (every part rated for 240 ± 5 °C; "the replacement LS120 needs its own verified profile") | ORDERING §4, STATUS open items and R7_VALIDATION (R7P1-13) say the LS120 rating has not been read. It can now be closed: the datasheet's reflow-test figure (item 9) gives a 250 °C maximum peak and at most 10 s above 245 °C, within Standard PCBA's 240 ± 5 °C. | Huaneng MLT-5020 datasheet (LCSC C94598) §3 "Reliability Test", item 9 "Soldering Test" figure: 250 °C max peak, 10 s max above 245 °C, preheat 170–190 °C for 90 ± 30 s, ramps ≤ 4 °C/s. It was read from the rendered figure; the axis labels are partly cut off but legible. | Record it in `procurement_catalog.json` (C94598), ORDERING §4 and §6, M1, and STATUS; close R7P1-13. |
| REQUIREMENTS-08 | Minor | M2 (silkscreen ≥ 0.15 mm lines) | LS120's footprint outline is drawn in 0.12 mm silkscreen lines. DRC enforces only text height and thickness, and `silk_check` only bounds, so the gate does not catch it. Inherited from R6 (same 0.12 mm). | Board scan: 4 LS120 F.SilkS line items of 0.12 mm width; every board text and visible reference is ≥ 1.0 mm high and ≥ 0.15 mm thick. | Widen to 0.15 mm in `kilib` (M3_MLT5020_3pad) and regenerate; or record a deviation. |
| REQUIREMENTS-09 | Minor | F8 (antenna ports "labelled GNSS and RADIO"; "antenna leads are labelled as well") | GNSS is on the top silkscreen and RADIO only on the bottom, so a top view of the board shows only GNSS. ORDERING §7 labels the leads "GNSS" and "915", which does not match the board's "RADIO". M3_R7 says the legends are "beside their jacks" without saying RADIO is on the bottom. | Board texts: F.SilkS 'GNSS' at (8.05, 8.10); B.SilkS 'RADIO' at (31.14, 7.90), both 1.0 mm / 0.15 mm. ORDERING §7: "Label both leads GNSS and 915". stepB_handoff §4 item 11 gives the reason (no top spot). | Use the same words on the leads as on the board (e.g. "RADIO 915"). Note in ORDERING §4/§7 and M3_R7 that the RADIO legend is on the bottom face (or find a top spot). |
| REQUIREMENTS-10 | Minor | M3 (text and owner cost) | (a) "plus the feeder fees of 7 new extended codes" is wrong for Standard PCBA, which charges $1.53 per unique code, Basic or Extended: R7 adds 14 codes and drops 4, a net +10 (+$3.06 per board). The items listed (19.78 + 6.52 + 0.72 + 1.04 − 5.77 = $22.29) also do not add up to the tool's parts change of +$23.47 (82.78 − 59.31; different price snapshots). The bottom line, $110.93 from `jlc_cost.py`, is right. (b) U4 is priced at JLC's $11.21, but JLC cannot supply it. Consigning 7–10 parts at about $8.48 (ST eStore, ORDERING §1) costs the owner $11.87–16.96 per board plus shipping, so the total is up to about $116.7: still within the $126.41 cap. | `fab/cost_check.json`: parts $82.78, 92 codes charged, 52 extended, total $110.93, supplier snapshot 2026-10-16T05:13:51Z, U4 line $11.2079. The RF-strip small parts sum to $1.0427 (matches "about $1.04"). | Reword the M3 breakdown (net +10 codes; one snapshot). Note the consigned-U4 owner cost and its margin. |
| REQUIREMENTS-11 | Minor | Verification claims (STATUS "Shown in CAD") | STATUS says "no RF net on safety copper (`check_actuators`)". `check_actuators.py` explicitly hands RF to `check_r7.py` (docstring lines 2–5). `check_r7` checks pads only: no pin of an RF part sits on a PYRO/ARM/ACT_/RAW_ACT/BAT_IN/BOOT0/NRST net. Connectivity separation comes from DRC/parity. | `m3_design/check_actuators.py` lines 2–5; `tools/check_r7.py` lines 75, 343–348. | Credit the check to `check_r7` (pad-level) plus DRC/parity. |
| REQUIREMENTS-12 | Minor | P3 ("every connector and tall part holds ≥ 5× its load at 100 g") | No retention assessment is recorded for the new SMA jacks, which carry mated plugs and coax beyond the aft edge, or for the two modules. P3 adds torque, witness marks and a coax tie within 2 cm (ORDERING §7), but MARGIN_PRESCRIPTION R14's 5× check was not extended to R7. **Inference**: likely ample (four soldered legs plus a centre pin, and the tie takes the cable), but it is unrecorded. | grep for "100 g" and "retention" across the R7 records: no SMA or module entry. | Add a short R14-style estimate (jack and plug mass × 100 g against the joint and leg strength) to M3_R7, or list it as a bench item. |
| REQUIREMENTS-13 | Minor | Document consistency | (a) ORDERING §7 battery row gives "≥ 1.0 Ah flight 1, ≥ 1.5 Ah flight 2" without REQUIREMENTS' "≥ 2 Ah if the radio transmits continuously on the pad". (b) The body of FMEA V-19 still says "no telemetry on board; LoRa is unfitted pads only" (only the summary row at line 18 is updated). (c) The parent CLAUDE.md names the "E22-900M22S as the alternate" next to "the MAX-M10S fits the same pads". The E22-900M22S is 20 × 14 mm with a different land (pass1 R7P1-09; EBYTE manual §8 lists it as 14×20), so it is a respin alternate, not drop-in. (d) M3_R7 gives 3.2–4.7 mm for the radio lines near U30; my scan gives 3.03 mm for the DIO1 via (via pad included). | Files and lines cited. | Align the texts. Mark the E22-900M22S "layout alternate (respin)" in the parent CLAUDE.md, or in F10 if it is meant to be recorded there. |

## 3. Requirement walk (R7 CAD, gate output, fab package)

Verdicts: **Pass** = shown on the board, schematic, gate or fab files; **Fail** = not met; **NV** = not verifiable in
CAD (bench, flight or firmware); **Partial** = the CAD part passes and the rest is open.

### Sources and owner decisions

| Item | Verdict | Evidence |
|---|---|---|
| Hold roll rate, roll program | NV (firmware, flight) | — |
| Flight 1 K850DM M1.45, flight 2 L1000W M1.9 | Recorded | Envelope table; consistent with the uncommitted parent VEHICLE diff (721 mm booster for both) |
| Single deploy, one pyro channel, isolated Blue Jay | Pass | `check_r7` REMOVED set (no CH2 parts or nets); no backup interface (AGENTS §1) |
| One board, both flights, no respin | Recorded | Requirement basis |
| Flight condition from accel + baro; roll from gyro | NV (firmware) | Parts present (U4, U5) |
| Tab to neutral on reset/hang/brownout | Partial | Hardware side under F6 |
| Control active in burn and coast | NV | — |
| 4-servo limit | Pass | J122 3×4, SERVO1–4 (check_actuators OK) |
| No in-flight tab sensing | Recorded | — |
| On-board MAX-F10S and E22-900MM22S, JLC-assembled; uplink never arms or fires | Pass (CAD) | BOM: U30 C30005563, U31 C5333985 (SMT); no RF part pin on a safety net (`check_r7`) |
| Tripoli/NAR | Partial | F8 below |

### Functional

| ID | Verdict | Evidence / remark |
|---|---|---|
| F1 gyro ≥ ±4000 dps | Pass (part); NV (error budget) | U4 LSM6DSV320XTR (C26633007), unchanged |
| F2 accel ≥ ±64 g + low-g | Pass (part) | U4 (±16 g + ±320 g) |
| F3 baro ≥ 10 km | Pass (part) | U5 MS561101BA03-50 |
| F4 servo outputs and copper | Partial | Outputs pass (check_actuators). The R7 solve was not run, but the servo-path copper equals R6's (REQUIREMENTS-04). Stall/thermal test is bench |
| F5 IMU rate, 16 MB flash | Pass (part); NV (firmware) | U3 W25Q128JVSIQ |
| F6 failsafe hardware | Pass (CAD part) | Servo pull-downs and pyro gate networks (check_actuators). R7 adds: RADIO_NRST R311 2 kΩ to GND, RADIO_NSS R310 100 kΩ to 3V3_RADIO, RADIO_RXEN R312 100 kΩ to GND (`check_r7`). Ride-through and watchdog numbers are calc/firmware |
| F7 one pyro channel | Pass (CAD) | R134 2 Ω C3013496, Q124 AON7524; CH2 absent. Fire budget is calc/bench |
| F8 Tripoli/NAR, spacing, legends | Pass (CAD), with REQUIREMENTS-09 | DRC 0 under the nine pyro rules (DRU hash pinned in check_actuators); legends ARM, IGN, BAT/1:BAT+…, J9, SERVO, GNSS (top), RADIO (bottom). Bench gates NV |
| F9 interfaces | Pass (CAD part) | Unchanged R6 circuit. GPS/radio on regulated 3V3 (FB30/FB31 from 3V3); EBYTE abs. max 3.7 V confirmed (manual §2.1) |
| F10 camera GH4 | Pass | `check_r7` J9 pin map |
| F10 RF strip y 0–23.5, 46 × 118 | Pass (outline); text deviation | REQUIREMENTS-05 |
| F10 U30 MAX-F10S, M10S on the same land | Pass (CAD) | U30 at (10.41, 14.95), top side; the M10S alternate is in the catalog and ORDERING §1 |
| F10 GNSS UART USART6 with series R | Pass | PC6 (63) → GNSS_RXD_MCU → R306 220 Ω → U30.3; U30.2 → R305 220 Ω → PC7 (64) |
| F10 RESET_N on PC8, no cap | Pass | GNSS_RESET_N = U1.65 and U30.9 only |
| F10 TIMEPULSE → PD14 via 1 kΩ, no pull-down | Pass | U30.4 → R307 1 kΩ → U1.61; no other pad |
| F10 SAFEBOOT_N on TP; V_BCKP, VIO_SEL open | Pass | TP30.1; U30.6 and U30.15 unconnected |
| F10 bias limiter switched by LNA_EN; ≤ 50 mA short | Pass (topology); NV (≤ 46 mA by calc, partly Inference) | VCC_RF → R300 15 Ω → Q30 → L30; Q31 gate on GNSS_LNA_EN with R303 100 kΩ to GND; Q32 sense. Bench item in ORDERING §5 |
| F10 ≥ 2.9 V at 15 mA | NV (calc typical: 2.93 V, 30 mV margin, VCC_RF drop typical only, Inference) | ORDERING §5 bench item |
| F10 pi network, series 0 Ω fitted, shunts DNP | Pass | R304/R316 fitted; C303/C305/C313/C314 DNP, excluded from BOM and CPL |
| F10 radio SPI2, BUSY PD8, NRST PD9 pull-down, DIO1 PD10, RXEN PE15 pull-down, TXEN = DIO2 | Pass | U1.51–57, U1.45; U31.9 and U31.19 tied (RADIO_TXEN) |
| F10 power from 3V3 via separate ferrites, bulk + bypass | Pass | FB30 3V3 → 3V3_GNSS (C300 10 µF, C301 100 nF); FB31 3V3 → 3V3_RADIO (C310 22 µF, C311 100 nF, C312 10 nF); BLM18KG ≤ 0.05 Ω per M3_R7 |
| F10 SMA jacks aft edge, ≥ 12 mm apart, THT step | Pass | J30 (12.85, 0), J31 (31.54, 0), 18.69 mm; BOM Assembly "THT (JLC through-hole step…)". JLC API classifies C530661 as "Plugin". No paste (check_r7) |
| F10 ESD diode at each jack | Pass (part) | D30/D31 ESD103-B1-02EL on the antenna nodes; rating per M3_R7 (not re-read) |
| F10 50 Ω GCPW for the ordered stackup | Pass (geometry and stackup) | W 0.30 on all RF tracks (DRC rule min = max 0.30); gap ≥ 0.25 (rule); stackup 0.035/0.203/0.03/1.03/0.03/0.203/0.035 in the board and job file, matching JLC041611-7628 data (secondary source, §6). My closed-form GCPW estimate is about 51–54 Ω (Inference) against the 50.2 Ω quoted from JLC's engine (not reproduced) |
| F10 ≥ 5 mm from bucks, MCU, crystal, fast digital lines | Pass, with documented slow-line exceptions | REQUIREMENTS-05 numbers |
| F10 no signals under modules (top two layers; U31 all) | Pass | Keep-outs and DRC 0 |
| F10 GND via fence | Pass | 21 GND vias at y 23.3 (x 0.9–45.1); openings x 6.3–12.4 and 20.0–23.8 (RF effect: layout dimension) |
| F10 coexistence ≥ 39 dB; pyro immunity; FCC use; GPS use | NV (bench, firmware) | ORDERING §5 has the steps |
| F10 firmware bindings recorded | Partial | Pin contract in M3_R7; firmware binding not written (open, AGENTS §3) |

### Physical

| ID | Verdict | Evidence |
|---|---|---|
| P1 46 wide, ≤ 120 mm, coupler fit | Pass | Edge.Cuts 46 × 118; fit_check OK (radius 24.9) |
| P1 record outline, orientation, bay stack | Partial | M3_R7 has the outline; bay stack and parent VEHICLE not updated (REQUIREMENTS-06) |
| P2 envelopes incl. GH, SMA, servo, pull-pin | Pass (CAD) | Worst J9 mated 0.03 mm, C84 0.11 mm; J30/J31 mated 8.91/10.42 mm |
| P2 five supports, ≥ 3.5 mm bottom clearance | Pass | Nearest bottom envelope C76 4.150 mm; top hardware TP89 3.858 mm (≥ 3.8) |
| P2 retention holes and tie path | Pass | Ø3.2 at (21.5, 68.6), (27.0, 82.6). Tie path under the board crosses only J122 pin tails (0.19–1.56 mm), as in R5/R6 |
| P2 re-derive span/vibration | **Fail** | REQUIREMENTS-02 |
| P2 sled/harness/shroud fit | NV | — |
| P3 retention ≥ 5× at 100 g | Partial | New SMA/modules not assessed (REQUIREMENTS-12) |
| P3 SMA torque/witness/tie | Pass (procedure) | ORDERING §7 |
| P3 no vias/fill under MEMS on component side | Pass | IMU_body_B and BARO_body_B rule areas (vias and fill disallowed), DRC 0 |
| P3 pyro block and J2 coated | **Fail** (J2) | REQUIREMENTS-01 |

### Manufacturing and cost

| ID | Verdict | Evidence |
|---|---|---|
| M1 4L 1.6 mm, 1 oz, JLC041611-7628, ENIG | Pass | Board stackup and gbrjob (ENIG, 1.6, 4 layers, rev M3-ASSY-R7) |
| M1 Standard PCBA incl. THT; SMA in THT step; modules top, last reflow; MSL 4 | Pass (files and remarks) | CPL: 96 top / 123 bottom = 219; U30/U31 not flipped (check_r7); ORDERING §4 remarks |
| M1 stock for 5 except U4 (consign) | Pass except U4 (open, as allowed) | `stock_check.json`: short = U4 only; U30 18 in stock (reserve) |
| M1 rotations verified | Pass (per step C) | `--verify-cpl` per ORDERING §4 (not re-run: read-only constraint on outputs) |
| M1 reflow ratings | Pass after this review | MAX-F10S 245 °C peak (IM §5, as cited); E22-900MM22S Pb-free peak 230–250 °C (manual v1.3 §7.1, re-read); LS120 250 °C max (REQUIREMENTS-07); C121 no datasheet (recorded) |
| M2 JLC rules | Pass | DRC 0 |
| M2 via holes vs SMD pad openings | **Fail** | REQUIREMENTS-03 (one case) |
| M2 courtyards enclose pads | Pass | Scan: 0 pads outside their courtyard |
| M2 silkscreen ≥ 0.15 mm lines, ≥ 1.0 mm text, not off board | Partial | Text OK; silk_check 0; LS120 lines 0.12 mm (REQUIREMENTS-08) |
| M3 ≤ $126.41 and ≤ 52 extended at 5 boards | Pass | $110.93, 52 (margin 0), snapshot 2026-10-16T05:13:51Z (under 1 h old at review) |

### Operating assumptions

Pack, pad time, igniters, ARM link, temperature, static ports, camera, harness and storage: updated for the
on-board radio and GPS where relevant; consistent with F6/F9 and pass1_electrical (not re-derived). Board position:
see REQUIREMENTS-06.

### R7 acceptance (REQUIREMENTS last section)

| Condition | Status |
|---|---|
| `check.sh` zero under R7 contracts; actuators and fit OK | Met (reproduced, §5) |
| Independent review pass with no open Critical or Major | Open: this pass reports 3 Major |
| M3 met on a ≤ 24 h snapshot | Met now (rerun before ordering) |
| M1 stock, U4 by consignment | Open (not consigned) |
| Fab outputs regenerated and bound | Met (`fab_manifest.py` OK) |

## 4. Parent CLAUDE.md avionics decisions (file on disk, commit 48b4081)

| Decision | Status |
|---|---|
| STM32H743, 4 servo outputs, single pyro channel | Met (U1 STM32H743VIT6; J122 4 servos; CH1 only) |
| Fully isolated Blue Jay, own battery and deployment circuit | Met (no interface; AGENTS §1) |
| One board flies both flights | Requirement basis (F-rows) |
| Radio and GPS on the board, JLC-assembled: MAX-F10S (M10S alternate on the same pads) and E22-900MM22S on SPI | Met. The "E22-900M22S as the alternate" wording implies drop-in; it is not (REQUIREMENTS-13c) |
| Antennas off-board on edge-launch SMAs; board ≤ 120 mm | Met (118 mm) |
| Uplink can never arm or fire pyros | Met in CAD (no RF pin on safety nets; ARM is the physical J124 link); firmware rule recorded |
| GPS tracking only | Recorded (F10) |

Note: the CLAUDE.md copy loaded into this review session was older (E22-900T22D UART radio, HGLRC M100 GPS). The
file on disk was updated in 48b4081 and agrees with R7.

## 5. Measurements and reproductions

- `tools/check.sh` (2026-10-16 ~05:40Z, temp copies): `DRC violations 0  unconnected 0  schematic parity 0  ERC 0`;
  metadata/3D audit OK; silkscreen outside outline 0; `R7 CAD contract: OK`; `actuator safety contract: OK`;
  `fit check: OK (CAD envelopes only)`. Board SHA in the r7 and fit reports: `03fe7572…6d54`.
- Outline: Edge.Cuts lines (0, 0)–(46, 118). Ø3.2 circles at (4, 4), (4, 64), (4, 114.4), (42, 114.4), (42.3, 4)
  (supports) and (21.5, 68.6), (27.0, 82.6) (ties). Tooling holes TH1 (44.8, 27.2), TH2 (1.4, 82.6), TH3 (1.4, 112.0).
- RF tracks (F.Cu, all 0.300 mm): GNSS_RF_ANT (12.85, 2.30)–(12.85, 7.13) 4.83 mm plus a 0.94 mm stub to C303;
  GNSS_RF_IN (13.71, 7.13)–(13.71, 10.20) 3.07 mm plus a 0.94 mm stub to C305; RADIO_RF_ANT (31.54, 2.30)–(31.54, 7.60)
  5.30 mm plus a 0.94 mm stub to C313; RADIO_RF (32.40, 7.60)–(32.40, 9.05) 1.45 mm plus a 0.94 mm stub to C314.
- Rule areas: U30_KEEPOUT, U31_KEEPOUT, R7_J30_launch_In1 x 11.95–13.75 / R7_J31_launch_In1 x 30.64–32.44, y 0–4.6
  (In1 only, no fill), PYRO_BLOCK x 4–42, y 84–114.4.
- Module and part placements: as in M3_R7 (U30 (10.41, 14.95) rot 90; U31 (29.86, 14.0) rot 180; J123 (36.0, 34.6)).
- Hidden references: 90, the same list as M3_R7 §"R7 board".
- Fab: BOM 95 lines, 92 codes; CPL 219 rows (96 top, 123 bottom); C303/C305/C313/C314/TP30 in neither file;
  `fab_manifest.py` OK.
- Cost: `cost_check.json` parts $82.78, 92 charged codes × $1.53 / 5, total $110.93, 52 extended, ok = true,
  inputs bound to the BOM/CPL hashes.
- R6 → R7 power-path zone comparison: REQUIREMENTS-04.

## 6. Sources

- EBYTE E22-900MM22S user manual v1.3 (2023-12-13), LCSC:
  https://datasheet.lcsc.com/datasheet/pdf/70331b0eaf0eedaea0129e9e66d9a011.pdf?productCode=C5333985 —
  §2.1 limit parameters (VCC 0–3.7 V), §3 pinout (9 TXEN, 10 RXEN, 19 DIO2), §4.1 (no wiring under the module on any
  layer), §4.2 (DIO2 to TXEN), §7.1 (Pb-free peak 230–250 °C), §8 (E22-900M22S is 14×20 mm).
- Huaneng MLT-5020 datasheet, LCSC C94598:
  https://datasheet.lcsc.com/datasheet/pdf/23f5c6599ed9cb614c21ac31ad2b1106.pdf?productCode=C94598 — §3 item 9
  reflow figure (page 3).
- JLC parts API (POST selectSmtComponentList, keyword C530661, 2026-10-16): componentSpecificationEn "Plugin",
  stock 959.
- JLC041611-7628 layer data: third-party mirror of JLC impedance-tool data,
  https://raw.githubusercontent.com/gsuberland/jlcpcb_autogenerated_stackups/main/normalised_json/jlcpcb_4L_1.6mm_outer1oz_inner1oz_JLC041611-7628.json
  (0.035 / 0.203 7628 Dk 4.4 / 0.03 / 1.03 core / 0.03 / 0.203 / 0.035). Secondary source. JLC's own page
  (https://jlcpcb.com/impedance) as fetched showed only JLC04161H-7628 (0.2104 / 1.065).
- Repository documents as cited: REQUIREMENTS, STATUS, ORDERING, M3_R7, R7_VALIDATION, AGENTS, FMEA_REDUNDANCY,
  MARGIN_PRESCRIPTION, M3_R5, the pass-1 reviews, stepB_handoff; parent `<parent repo>/CLAUDE.md` and
  `docs/VEHICLE.md`.

## 7. Inferences (not checked against a primary source)

- The 190–205 Hz first-mode figure (REQUIREMENTS-02) is a span-squared scaling of R5's recorded estimate, not a model.
- The 51–54 Ω GCPW figure is a closed-form conformal-mapping estimate (thickness-corrected, no mask). JLC's
  50.2 Ω engine result was not reproduced.
- VIL(NRST) ≈ 0.3 VDD and the 12.9–21.4 kΩ leak threshold (REQUIREMENTS-01) use typical STM32H7 NRST
  characteristics. DS12110 was not re-read in this pass; the 30–50 kΩ pull-up is as cited in REQUIREMENTS F6.
- The coax-zone overlap with the battery bay (REQUIREMENTS-06) uses VEHICLE's estimated stack lengths.
- The SMA retention margin (REQUIREMENTS-12) is judged likely ample without a calculation.
