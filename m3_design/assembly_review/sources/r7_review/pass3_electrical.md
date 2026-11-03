# R7 pass 3: schematic and electrical correctness (final board)

Reviewer scope: the electrical design of the final R7 board and schematic. That covers U30 MAX-F10S (and the
MAX-M10S drop-in), U31 E22-900MM22S, the antenna-bias limiter with its new C304 footprint, the RF ESD and pi
networks, reset and ROM-bootloader states, the U1 pin and EXTI contract, the 3V3 budget and the reworked FB31
feed, DNP handling, and whether anything needed was removed. I also checked the electrical side of the fix pass's
whole-board copper changes (F1–F3). Routing style, RF layout, DFM and mechanics belong to the parallel reviewers
and appear here only where an electrical conclusion depends on them. This is a read-only review: I changed no
repository file other than this report.

## Baseline and what was run

- Worktree `rocket-flight-computer-r7`, branch `m3-assy-r7`, uncommitted, on R6 `3b215ba`.
  - Board SHA-256 `7660620cfa834e4d381d2a2638780e9a341341c9b93c6e6f526791204dc77c9c`, identical before and after
    the review; this is the "final" board in `docs/R7_VALIDATION.md`.
  - Schematic `m3.kicad_sch` SHA-256 `47057f7d97c7d748…`.
- **`tools/check.sh`** (temporary copies) exited 0:
  - DRC 0, unconnected 0, parity 0, ERC 0;
  - metadata/3D OK, silkscreen 0, R7 CAD contract OK;
  - routing hygiene: 0 failing, 20 allowlisted, 0 stale;
  - actuator contract OK, fit OK.
- **Netlists.** I exported both with `kicad-cli sch export netlist --format kicadxml` on scratch copies:
  - the current schematic;
  - the pass-2 schematic, the copy saved with the pass-2 board `03fe7572…` in the review scratchpad (`base/`).

  I compared them component by component, property by property and pin by pin.
- **Board.** I read the final board and the pass-2 board with pcbnew (no save):
  - placement, pad nets and zone connections of every R7 part;
  - every R7 supply and limiter net's tracks and vias;
  - the footprint-by-footprint differences between the two boards;
  - power-net widths and via counts;
  - the 3V3/GND copper around U2 and L1;
  - same-layer clearances round the BAT_ILIM node.
- **DC solves:** `tools/dc_solve.py`, run on scratch copies.
- **Fab outputs.** I cross-checked `fab/m3_bom_jlc.csv` and `m3_cpl_jlc.csv` against the schematic's fitted and
  excluded parts.
- **Maker documents.** I re-read them from text extracts in the review scratchpad (list in "Sources"):
  - MAX-F10S data sheet R03 Tables 10–13;
  - MAX-F10S integration manual R01, Table 1 and §4.1.1;
  - EBYTE E22 manual ch. 3–4;
  - AP63203 DS41326 electrical table;
  - AN2606 Rev 70 Table 135;
  - TPS25947 SLVSFC9C, the ILM sections.
- **Scripts:** in the scratchpad, `p3el/` (`netparse.py`, `diff.py`, `brd1.py`, `net3v3.py`, `padsnet.py`,
  `zones.py`, `fpcmp.py`, `widths.py`, `near.py`).

## 1. Summary

- **No Critical and no Major finding.**
  - **Pass-2 findings.** All five electrical findings (ELECTRICAL-01 to -05, all Minor) are closed or properly
    dispositioned in `docs/R7_VALIDATION.md` (§2).
  - **Schematic change since pass 2:** C304 (DNP, GNSS_ANT_GATE to GND) and the `C0402_DNP` footprint on the
    four pi-network shunts. Nothing else changed: no pin, value or part number.
  - **Board change since pass 2:**
    - the limiter (Q30–Q32, R300–R303) is re-placed, with the same topology and a correct Kelvin sense across
      R300;
    - C304 is placed;
    - C311 and C312 moved 0.2 mm;
    - TP89 moved to the bottom.
  - **Fix-pass copper (F1–F3).** It removed no needed copper or via, and narrowed no power path:
    - VLOGIC U11 → U2 is unchanged at 9.40 mΩ, and C84 → U2 improved from 53.9 to 36.5 mΩ;
    - the buck's input-capacitor–GND link is kept;
    - the 3 3V3 vias that went belonged to removed R6 port copper.
- **Two Minor findings**, both documentation:
  - **P3-ELECTRICAL-01:** the limiter's short-circuit figures were not carried consistently into the
    schematic note, ORDERING §5 and M3_R7 after pass 2 corrected them;
  - **P3-ELECTRICAL-02:** the bench-fit guidance for the DNP lands is incomplete: C305's DC constraint is
    missing from the sheet-15 note, and C304 has no part specification.
- **What checks out:**
  - U30 and U31 pin connections against the maker documents;
  - reset and bootloader states: R311 holds the radio in reset, NSS is high, RXEN low;
  - the U1 pins and the EXTI notes;
  - the reworked FB31 feed: it lands in the main 3V3 In2 polygon, and the radio supply is about 3.26 V at the
    pin at the regulator minimum;
  - the GNSS feed: about 0.06 Ω against u-blox's 0.2 Ω limit;
  - the 3V3 budget: unchanged, 0.66 A worst case of 2 A;
  - ESD: the RF GND pads are now solid, with a via 0.16 mm away;
  - DNP handling: schematic flags, board flags, no paste, absent from the BOM and CPL.

## 2. Pass-2 findings in this dimension: closure check

| Pass-2 ID | Pass-2 ask | Disposition in R7_VALIDATION | Verified on the final design | Closed? |
|---|---|---|---|---|
| ELECTRICAL-01 | 0402 footprint GNSS_ANT_GATE → GND next to R302 (fit 1–2.2 nF, or DNP and fit on the bench result); a bench pass criterion | Fixed: C304 DNP 0402, fit 1–2.2 nF only if the short test oscillates (ORDERING §5) | **Schematic:** C304, pins 1 GNSS_ANT_GATE, 2 GND; `dnp`, `exclude_from_bom` and `exclude_from_pos_files` set; footprint `rocket:C0402_DNP`. **Board:** B.Cu at (7.74, 16.90), DNP flags set, no B.Paste. Pad 1 (7.32, 16.90) is fed by a 1.15 mm 0.2 mm B.Cu link from R302.1 (7.32, 15.75), on the gate node with R301.2, Q32.3 and Q30.1. Pad 2 is GND (thermal) and connected (DRC unconnected 0). **ORDERING §5:** scope GNSS_ANT_GATE and VCC_RF, cold and hot; fit C304 and repeat if it oscillates | **Yes** |
| ELECTRICAL-02 | State the antenna side (≤ 20 mA, works from 2.7 V) in F10 and ORDERING §7; record the VCC_RF drop | Documented | F10 (REQUIREMENTS l. 60) and ORDERING §7 (l. 195) both carry ≤ 20 mA and 2.7 V. ORDERING §5 (l. 155) records the measured VCC_RF drop | **Yes** (figure consistency: P3-ELECTRICAL-01) |
| ELECTRICAL-03 | BUSY/EXTI9_5 and TIMEPULSE/EXTI14 notes in the pin contract | Documented | M3_R7 l. 143–145 and F10's binding note carry both. The firmware's EXTI use is unchanged (`power_status_stm32.c:6`, EXTI0/1/4/9_5) | **Yes** |
| ELECTRICAL-04 | Record the D30 trade-off and a GNSS-lead ESD handling rule | Accepted, documented | M3_R7 §"RF chains" (l. 189–194) carries the trade-off. ORDERING §5 (l. 145) and §7 (l. 195) carry the handling rule, and the §5 short test fits the short unpowered | **Yes** |
| ELECTRICAL-05 | Correct Q30's short-circuit temperature rise | Documented | M3_R7 l. 168: about +30–40 K on this layout, Tj ≈ 115–125 °C, labelled Inference | **Yes** |

## 3. Findings

| ID | Sev. | Req. | Finding | Evidence | Recommended fix |
|---|---|---|---|---|---|
| P3-ELECTRICAL-01 | Minor | AGENTS §2.5 (inferences labelled, one record); F10 (≤ 50 mA) | **The limiter's short-circuit figures were not carried consistently after pass 2.** Pass 2 recomputed the limit as 37–48 mA cold and 25–38 mA hot, which F10 and ORDERING §7 now use. Three places still quote the superseded pass-1 numbers: the sheet-15 note ("about 27-46 mA over -20..+85 C"), ORDERING §5's short test ("design ≤ 46 mA"), and M3_R7's limiter table. That table keeps "≤ 46 mA" in bold, with "pass 2: ≤ 48 mA" in brackets. Its VEB row (0.43–0.66 V, "conservative cold") is contradicted by pass 2's cold range of 0.55–0.71 V. The bench comparison the record invites is against a 50 mA limit, so the stated margin is 4 mA where the inferred worst case leaves 2 mA | `m3_design/r7_sch.py:308` (rendered in `telemetry.kicad_sch` l. 1674); `docs/ORDERING.md:155`; `docs/M3_R7.md:164–167`; `pass2_electrical.md` §4.3; REQUIREMENTS F10 l. 60 ("about 25–38 mA at +85 °C") | Use one figure set everywhere: ≤ 48 mA at −20 °C and 25–38 mA at +85 °C (Inference). Update the r7_sch note (then regenerate the sheet and netlist), ORDERING §5 and M3_R7's VEB, −20 °C and 25/85 °C rows. Keep the pass-1 numbers only as history |
| P3-ELECTRICAL-02 | Minor | F10 (pi network, C303/C305 DNP), ORDERING §5 (C304 bench fit) | **Bench-fit guidance for the DNP lands is incomplete.** (a) The sheet-15 note says "DNP shunts are tuning placeholders (C303 capacitive only)". With R304 at 0 Ω, however, C305 (GNSS_RF_IN) sits on the same 3.2 V DC bias node as C303 (GNSS_RF_ANT). An inductor fitted at C305 during VNA work would short the antenna bias into the limiter, and the antenna would go dark. M3_R7 l. 187 says this correctly ("either position"), but the schematic does not. (b) ORDERING §5 and the sheet-15 note ask the bench to fit "1–2.2 nF" at C304 but name no part, dielectric or voltage. No LCSC part is on the BOM for it | `r7_sch.py:309`; nets GNSS_RF_ANT = {C303.1, D30.1, J30.5, L30.2, R304.1} and GNSS_RF_IN = {C305.1, R304.2, U30.11} (netlist); R304 = 0R C17168 fitted; `docs/ORDERING.md:155`; `r7_sch.py:238–240` | (a) Note text: "C303 and C305 capacitive only while R304 is 0R". (b) Name the bench part in ORDERING §5, for example a 0402 X7R or C0G 1.0–2.2 nF, ≥ 10 V (the gate node never exceeds VCC_RF ≈ 3.2 V) |

## 4. Checks on the final design

### 4.1 Schematic and netlist since pass 2

- **Components.** The only new component is C304. C303, C305, C313 and C314 changed footprint, from
  `rocket:C0402` to `rocket:C0402_DNP`. Every C symbol's `ki_fp_filters` gained `C0402_DNP`. No value, LCSC,
  manufacturer field or pin net changed on any other part. The netlist pin diff is exactly C304.1 →
  GNSS_ANT_GATE and C304.2 → GND.
- **U30/U31 pin nets** (netlist), unchanged from pass 2 and matching the maker documents:
  - **U30:**
    - pins 7 and 8 on 3V3_GNSS;
    - pin 9 GNSS_RESET_N, pin 11 GNSS_RF_IN, pin 13 GNSS_LNA_EN, pin 14 GNSS_VCC_RF;
    - pins 5, 6, 15, 16 and 17 unconnected; pin 18 to TP30 only;
    - checked against MAX-F10S DS R03 Table 10 (pin list) and footnote 14 (SAFEBOOT_N to TIMEPULSE through
      1 kΩ).
  - **U31:**
    - pin 1 3V3_RADIO, pin 3 RADIO_NRST, pin 6 RADIO_RF;
    - pin 9 and pin 19 (DIO2) on RADIO_TXEN, pin 10 RADIO_RXEN;
    - pins 11–15 BUSY, MISO, MOSI, NSS and SCK; pin 20 DIO1;
    - pins 4, 5, 8, 17 and 18 unconnected;
    - checked against the EBYTE manual ch. 3 pin table and §4.2 ("DIO2 can be connected with TXEN"; "32 MHz
      passive crystal oscillator").
- **Limiter nets.** VCC_RF = {U30.14, R300.1, Q32.2 (E)}; ANT_SRC = {R300.2, Q30.2 (S), Q32.1 (B), R301.1};
  ANT_GATE = {Q30.1, Q32.3 (C), R301.2, R302.1, C304.1}; ANT_PD = {R302.2, Q31.3}; LNA_EN = {U30.13, Q31.1,
  R303.1}; ANT_DC = {Q30.3 (D), L30.1, C302.1}.
- **U1** is unchanged from pass 2. The R7 pins are 45 PE15 RXEN, 51–54 PB12–PB15 SPI2, 55 PD8 BUSY, 56 PD9
  NRST, 57 PD10 DIO1, 61 PD14 TIMEPULSE and 63–65 PC6/PC7/PC8. PA7, PC9, PA8, PA9 and PA10 are unconnected.

### 4.2 Limiter as re-placed (F1) and C304

- **Placement** (B.Cu, under U30's west half):
  - Q30 at (4.75, 11.75), rotated −90°;
  - Q32 at (8.75, 13.25), rotated 90°;
  - R300 at (8.75, 10.75), rotated 180°;
  - R301 at (5.75, 14.25), R302 at (7.75, 15.75), R303 at (12.25, 11.75), Q31 at (12.0, 14.25);
  - C304 at (7.74, 16.90).

  The pad nets equal the netlist (parity 0). The pinouts are the pass-2-verified SOT-23 assignments: AO3401A and
  AO3400A 1 G, 2 S, 3 D; S8550 1 B, 2 E, 3 C. The board-embedded footprints of these parts are pad-for-pad
  identical to the pass-2 board (`fpcmp.py`: only position and rotation changed).
- **Kelvin sense.**
  - Load current enters R300.1 (9.575, 10.75) from VCC_RF's via side (y < 10.75).
  - Q32's emitter is tapped from R300.1 on the far side, at (9.575, 10.75) → (9.575, 12.25).
  - Load current leaves R300.2 (7.925, 10.75) westward to Q30.2.
  - Q32's base is tapped from R300.2 northward, at (7.925, 10.75) → (7.925, 12.25).

  Trace resistance therefore does not enter the current limit. The limit is still VEB / R300.
- **Copper in the bias path** (dc_solve): VCC_RF 8.75, ANT_SRC 13.45 and ANT_DC 32.72 mΩ, about 55 mΩ in all.
  At 15 mA that is 0.8 mV, so pass 2's 2.928 V at the regulator minimum is unchanged to the first decimal of a
  millivolt.
- **C304 fitted (Inference).** These are first-order estimates; the pass-2 model covers the loop itself.
  - The gate turns on through R302 with τ ≈ 10 kΩ × (2.2 nF + Ciss ≈ 0.65 nF) ≈ 29 µs, a softer antenna
    start-up.
  - It turns off through R301 with τ ≈ 0.29 ms.
  - At power-up C304 holds the gate low, so Q30 conducts while VCC_RF rises. LNA_EN's reset-state pull-up
    (DS Table 11: "In reset mode … all PIOs are configured as input pull-up") turns Q30 on anyway, so the
    behaviour does not change.
  - On a sudden short, Q32 must slew roughly 3 nF by about 1.9 V. That adds tens of nanoseconds to the
    sub-microsecond overcurrent transient pass 2 described. It is not a thermal or rating concern.
  - Pass 2's loop model gives a worst phase margin of 62° with 1 nF.
- **DNP land on the gate node.** Pad 1 is bare (ENIG, mask open, no paste) at 0.34 mm from its GND pad.
  - A leak there can only turn the antenna bias on when LNA_EN asks for it off. That needs below about
    530 kΩ at VGS(th) 0.5 V (Inference).
  - The limiter still limits with such a leak.
  - So it is harmless; there is no finding.

### 4.3 Supplies, FB31 feed and 3V3 budget

- **FB31 feed (RQ-03 rework).**
  - FB31.1 (35.10, 22.15) runs on 0.4 mm F.Cu to via (35.73, 27.342), 0.6/0.3 mm, with R161.1 tapped at
    (35.03, 26.8).
  - The via lands inside the **main** 3V3 In2 fill polygon (bbox x 9.73–36.40, y 25.40–75.52, 434.78 mm²), not
    in an island.
  - C90's 0.2 mm In2 link also ends at this via.
  - DC from L1.2 to FB31.1 is **13.61 mΩ** (my dc_solve run, 0.1 mm grid, 6,670 CG iterations). That equals
    F3's 13.6137 mΩ. The pass-2 board gives 29.33 mΩ by the same method, so the rework more than halves it. At
    0.12 A it is a 1.6 mV drop.
- **Radio supply.**
  - FB31.2 → C310.1 (22 µF) → C312.1 (10 nF) → C311.1 (100 nF) → U31.1, all on 0.4 mm F.Cu.
  - 3V3_RADIO from FB31.2 to U31.1 is 6.53 mΩ (dc_solve).
  - At AP63203 VFB minimum (3.27 V, which DS41326's table applies over −40…+85 °C and 3.8–32 V) and 119 mA
    of transmit current, the pin sees 3.27 − 0.119 × (0.0136 + 0.050 + 0.0065) ≈ **3.262 V**.
  - That matches pass 2's 3.26 V. The EBYTE "≥ 3.3 V ensures output power" note stays an observation, not a
    requirement.
- **GNSS feed.**
  - 3V3 L1.2 → FB30.1 is 5.06 mΩ (F3) through FB30.1 → F.Cu → via (11.58, 26.2) into the main In2 polygon.
  - FB30 is ≤ 0.050 Ω.
  - 3V3_GNSS from FB30.2 to U30.7/8 is 6.03 mΩ (dc_solve).
  - Total ≈ **0.061 Ω**, against u-blox IM §4.1.1's "Do not add series resistance greater than 0.2 Ω".
  - The order FB30 → C300 10 µF → C301 100 nF → pins 7/8 is unchanged.
- **3V3 budget.** No load was added (C304 is unfitted). Pass 2's 0.66 A worst case and U2's ΔTj of about +31 K
  stand.
- **Fix-pass copper on power nets** (pass-2 board → final):
  - **VLOGIC** (dc_solve, 0.1 mm grid):
    - U11:1,8 → U2:2,3 is 9.40 → 9.40 mΩ;
    - C84:1 → U2:2,3 is 53.94 → 36.54 mΩ.
  - **Buck loop.** The duplicate B.Cu GND runs U2.4 ↔ C7.2 ↔ via (19.5, 35.2) were removed. The direct
    0.5 mm U2.4 → C7.2 run (19.0, 34.2) → (20.6, 34.2) remains. U2.4 is SMD on GND_B, which connects solid
    (pad connection "THT thermal"), so via (19.5, 35.2) still reaches U2.4 through solid pour. The hot loop is
    intact.
  - **FB sense.** U2.1 still reaches its remote-sense via (16.25, 31.6): the track end (16.85, 31.6) lies inside
    the pad (x 16.775–17.325).
  - **Minimum widths** of every power net (`widths.py`): none narrower than on the pass-2 board. 3V3_RADIO went
    from 0.3 to 0.4 mm.
  - **3V3 vias**, 39 → 36. The three removed vias, (32.57, 35.0), (32.87, 34.3) and (34.663, 36.105), were the
    R6 R205 port-part star (F2 §2, RG-04). Nothing that remains used them: the U1.75, U1.27, U3.8, FB30 and FB31
    solves are equal or lower than on the pass-2 board.
  - **VLOGIC vias** 6 → 5, which F3 §4 explains (they joined only C99 and the R60 sense line).

### 4.4 Reset and ROM-bootloader states (unchanged circuit; re-confirmed)

- **MCU in reset:** every new U1 pin is analog (DS12110 §3.8).
  - RADIO_NRST is held low by R311 2.0 kΩ, at the U31 end (37.0, 14.43).
  - NSS is high (R310 100 kΩ to 3V3_RADIO), RXEN low (R312 100 kΩ), and TXEN is DIO2, held low in SX1262 reset.
  - The GNSS keeps running: RXD idles high on the module pull-up, and RESET_N is released.
- **ROM bootloader** (AN2606 Rev 70 Table 135, which I re-read):
  - PB14 is USART1_TX (AF push-pull, pull-up) and PB15 is USART1_RX (input pull-up).
  - With the radio in reset and NSS high, MISO is high-Z: there is no contention, and nothing can drive PB15.
  - The bootloader's SPI2 is on PI0–PI3, which are not bonded in LQFP100.
  - USART6 (GNSS) is not a bootloader interface.
- **The fix pass changed none of these parts or nets.**

### 4.5 Pin contract and EXTI notes

- **The pin contract** in M3_R7 matches the netlist row by row.
- **EXTI lines** (pin number = line):
  - line 8: PD8 BUSY and PB8 I2C1_SCL (an AF output, no EXTI); its vector EXTI9_5 is shared with PD6 USB_FAULT_N;
  - line 10: PD10 DIO1 only;
  - line 14: PD14 TIMEPULSE and PC14 PULLPIN;
  - line 15: PD15 VBUS_SENSE.
- **ELECTRICAL-03's two constraints** are recorded.

### 4.6 ESD

- **D30/D31 placement** (ESD103-B1-02EL): D30.1 is on the GNSS_RF_ANT pad row at (12.85, 5.20) and D31.1 at
  (31.54, 5.20).
- **GND pads.** They are now `ZONE_CONNECTION_FULL` (zc 2 on the board), each with a GND via 0.16 mm from its pad
  edge (F1 RF-02). That lowers the clamp loop's inductance compared with the pass-2 thermal spokes.
- **Ratings** are as pass 2 found: VWM ±15 V against 3.2 V bias and 4.0–8.0 V radio peaks. The GNSS clamp
  trade-off and the handling rule are recorded (ELECTRICAL-04).

### 4.7 DNP handling

- **Schematic:** C303, C304, C305, C313 and C314 each carry `dnp`, `exclude_from_bom` and
  `exclude_from_pos_files`. Each has value "DNP" and no LCSC code.
- **Board:** all five have the DNP, exclude-from-BOM and exclude-from-position flags set. `rocket:C0402_DNP`
  carries copper and mask only, with no paste.
- **Fab:**
  - every fitted schematic part is in the BOM and the CPL: 219 = 219, with no extras;
  - the excluded set is exactly the five DNP shunts, J2 and the 24 test pads;
  - the BOM's LCSC codes agree with the schematic on all 219.
  - The F1 handoff reports the Gerbers carry no paste at the five DNP lands; `check_r7.dnp_paste` passes.

### 4.8 Nothing needed removed

- **Schematic:** pass 2 → final only adds a part.
- **Board:**
  - pad groups per net are unchanged (F3 invariant; I re-confirmed with DRC unconnected 0 and parity 0);
  - the footprint diff shows only the expected moves;
  - the copper removed on power nets is either duplicate or R6 port-part residue (§4.3);
  - BAT_ILIM is one link, with TP89 on the bottom.

## 5. Observations (no finding)

- **EXTI15_10 vector.** DIO1 (line 10) shares the EXTI15_10 vector with PULLPIN (PC14, line 14) and VBUS_SENSE
  (PD15, line 15).
  - Today neither is an interrupt: VBUS_SENSE is polled (`m3_firmware/src/usb_stm32.c:81`), and PULLPIN has no
    EXTI.
  - If either becomes one, the handler must test EXTI_PR1 per line. That is normal practice, and the binding can
    note it next to the BUSY/EXTI9_5 note.
- **TP89 (BAT_ILIM) on the bottom** is 1.075 mm from a RADIO_NSS B.Cu track and 1.575 mm from RADIO_SCK
  (same-layer clearance, `near.py`).
  - TI asks for no coupling to switching signals on the ILM node (SLVSFC9C §8.4.1). The node is low impedance
    (R84 750 Ω), so a coupled edge of about 0.05 pF against several pF of node capacitance is tens of
    millivolts for nanoseconds (Inference). That is far from a trip.
  - This is a large improvement on pass 2's 0.225 mm beside QSPI_IO0 over a long run.
  - The TP89 branch (pad, 4.5 mm of track, one via; about 1–2 pF, Inference) also keeps the ILM pin well under
    TI's 50 pF loading limit (§7.3.6 note and §8.4.1).
- **U31 decoupling order.** The 10 nF (C312) sits about 1 mm farther along the feed than the 100 nF (C311). F1
  moved both 0.2 mm east, so C311.1 is 1.97 mm from U31.1. At 915 MHz both are inductive, so the difference is
  negligible.
- **Pre-existing, outside the R7 change.** In the ROM bootloader, which is now the documented USB-DFU re-flash
  route after J2 is coated (ORDERING §5), these pins are bootloader interfaces (AN2606 Table 135):
  - PA2/PA3 (SERVO3/4_MCU) are USART2;
  - PB10/PB11 (camera UART) are USART3;
  - PB6 (QSPI_NCS) is I2C1 SCL.

  On bootloader versions before 0x91, PA2 may idle high with servo power on. ACT_EN is hardware-driven by Q122
  (the logic path), so the servos are powered in DFU. This is R6 behaviour on the bench only. Re-flash with the
  servos unplugged.

## 6. Sources

- u-blox MAX-F10S data sheet UBXDOC-963802114-12732 R03:
  https://content.u-blox.com/sites/default/files/documents/MAX-F10S_DataSheet_UBXDOC-963802114-12732.pdf
  - Table 10, pins and footnote 14 (SAFEBOOT_N to TIMEPULSE through 1 kΩ), p. 9;
  - Table 11, pin states (LNA_EN: output high / input pull-down / input pull-up; "In reset mode … all PIOs are
    configured as input pull-up");
  - Table 12 (ICC_RF 200 mA abs max, V_DCrfin ±5.5 V);
  - Table 13 (VCC_RF = VCC − 0.1 V typical, ICC_RF 50 mA).
- u-blox MAX-F10S integration manual UBXDOC-963802114-12892 R01:
  https://content.u-blox.com/sites/default/files/documents/MAX-F10S_IntegrationManual_UBXDOC-963802114-12892.pdf
  - Table 1 (VCC_RF "internally connected to VCC through a ferrite bead");
  - §4.1.1 (≤ 0.2 Ω series resistance);
  - §4.3 (L4 > 500 Ω at L1/L5).
- EBYTE E22-900MM22S user manual v1.3, ch. 3 pin table, §4.2 (DIO2 → TXEN; 32 MHz passive crystal), ch. 2
  (1.8–3.7 V; ≥ 3.3 V for output power):
  https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2212192008_Chengdu-Ebyte-Elec-Tech-E22-900MM22S_C5333985.pdf
- Diodes AP63200/01/03/05 DS41326 Rev 3-2, electrical characteristics: VFB 3.27–3.33 V, limits over
  −40…+85 °C and 3.8–32 V; tSS 4 ms; θJA 89 °C/W; output capacitance 22–68 µF:
  https://www.diodes.com/assets/Datasheets/AP63200-AP63201-AP63203-AP63205.pdf
- ST AN2606 Rev 70, §60, Table 135 (pp. 320–323):
  https://www.st.com/resource/en/application_note/an2606-stm32-microcontroller-system-memory-boot-mode-stmicroelectronics.pdf
- ST DS12110 Rev 11, §3.8 (GPIOs analog after reset): https://www.st.com/resource/en/datasheet/stm32h743vi.pdf
- TI TPS25947 SLVSFC9C (revised May 2026): RILM 549–6650 Ω (RILM 750 Ω gives 3.96–4.84 A); ILM pin loading
  < 50 pF (§7.3.6 note, §8.4.1); §8.4.1 layout guidelines (ILM traces "must not have any coupling to switching
  signals"): https://www.ti.com/lit/ds/symlink/tps25947.pdf
- For the pinouts and the parameters this pass did not re-derive (AO3401A/AO3400A, S8550, ESD103, BLM18KG,
  LQG15HS, SX1262), see `pass2_electrical.md` §7. The library footprints and part numbers are unchanged since
  pass 2.

## 7. Inferences (not measured, or not checked against a primary source)

- **Limiter:**
  - the C304-fitted time constants and short-transient extension;
  - the leak threshold on C304's bare land;
  - every limiter current and voltage figure from pass 2 (VCC_RF minimum and source impedance, S8550 VEB below
    1 mA).
- **Supply:**
  - the radio pin voltage, which uses the FB31 DCR maximum, the dc_solve copper values and AP63203 VFB minimum;
  - the effect of the ferrite's DC bias.
- **ILM coupling:** the TP89 coupling estimate (capacitance from geometry, not extracted).
- **Bootloader:** the PA2 behaviour on pre-0x91 bootloaders.
