# R11 stage C2: families `usb`, `pyro` and `power` (first part) (2026-11-02)

Stage C of `r11_plan.md` §4, second part. Nothing is committed or ordered. Decisions D-R11-20 … -24 are in
`R11_DECISIONS.md`. Evidence labels as AGENTS §2.5. Coordinates are board mm (x east, y forward from the aft edge,
KiCad's y). Every route was drafted with a scratch maze aid or by hand and is frozen as explicit tables in
`m3_design/r11_route_{usb,pyro,power}.py` (D-R11-07: the build never searches).

**State (after C2c, section 9).** C2c routed PYRO1_CONT, ARM1_SENSE_MID, VLOGIC_SENSE and LOGIC_SOURCE_ST, fixed D4.2's via,
pinned the supports and gave VCAP1 a second barrel. Still open: ARM1_SENSE's MCU run, BAT_FAULT_N / R89 and the BOOT0 /
VCAP2 / PA4 single barrels (section 9.3). **State (after C2b, section 8).** `usb` and `pyro` route every net they own except the three sense nets of O-C2-1;
`power` routes every rail and In2 region, the J400 / EN chain and the regulator cells. Not routed: the sense lines
(O-C2-1), BAT_FAULT_N / LOGIC_SOURCE_ST / VLOGIC_SENSE (O-C2-4) and with them R89.1 (3V3). Stage C2 is therefore **not
complete**; sections 1-7 are the first part's record, section 8 is C2b's and supersedes them where they differ.

## 1. Gate results (Measured)

| Family | NETS done | r11_stage_check | unconnected after |
|---|---|---|---|
| core (C1) | 22 | OK | 461 |
| usb | 10: USB_DP, USB_DM, VBUS, CC1, CC2, VBUS_SENSE, USB_ILIM, USB_FAULT_N, USB_LIMITED, USB_OVLO | OK: DRC 0 counted, route_check 0 outside pending | 428 |
| pyro | 12: ACT_FET_S, ACT_GATE, ACT_DRV, ACT_EN, ACT_EN_MCU, RAW_ACT, PYRO1_IGN, PYRO1_OUT, PYRO1_GATE, PYRO1_GATE_N, PYRO1_COLD, PYRO1_CONT_MID | OK | 387 |
| power (part 1) | 7: BAT_DVDT, BAT_ILIM, BAT_OVLO, BAT_DAMP, CAM_ILIM, LOGIC_ILIM, LOGIC_SS | OK | 378 |

`tools/check_r11.py --only S-1,S-2,S-3,S-3c,S-5,S-6,S-8,S-9` on the board after `pyro`: all OK (Measured; In1 / In2 / In4
not poured yet, so S-8 is measured against the inner copper that exists, section 3). Determinism: two full builds gave
the same SHA-256 `34d5d839bbe4ac507f1a2ddce1dcb276e8e6f3ca57ec7a8573ac3eda5a4154c3` (Measured).

## 2. usb (D-R11-20)

* **Pair.** D+ (U1.B10) and D- (U1.C10) leave the field east on F.Cu at y 25.2 / 25.6 (0.2 mm, 0.4 mm pitch), pass north
  of U3's pin row, turn south at x 36.25 / 35.8 and run to J3 on F.Cu. J3's D+ pads B6 / A6 are joined by a loop west of
  the pads (x 37.45); A7 (D-, inside the loop) drops by V_A7 (38.1, 29.75) and rejoins D- on In3 at V_DM (35.8, 30.75);
  B7 takes the F.Cu trunk. D4 (USBLC6, B.Cu) taps each line by one via (V_DP (36.25, 28.6), V_DM), its two pins of a
  line bridged under its body. GND partners (Measured centre to centre): V_DM–(35.15, 30.4) 0.74 mm; V_DP–(37.15, 28.75)
  0.91 mm and V_DP–R85.2's via (35.33, 28.6) 0.92 mm; V_A7–(37.15, 28.75) 1.38 mm. route_check finds no critical via
  without a partner.
* **VBUS.** J3.B4A9 → VB1 (38.3, 27.6) → B.Cu to U10.3 (EN) and under U10's body to U10.1 (IN); U10.2's GND via north of
  it. J3.A4B9 → C28 / C83 on F.Cu at the pin (moved there), VB2 (38.0, 32.4) to D4.5 on B.Cu; VB1 and VB2 joined on In3
  east of V_A7 (0.2 mm). R9 (sense top, beside U1) fed by a 0.2 mm F.Cu run south of U3 and one via. 3 VBUS vias
  (route_check extra_vias limit 3).
* **CC.** Each CC pad by one via to B.Cu; CC2 under J3's body (x 40.92, between its shell pins and holes), CC1 east of
  C28; R7 / R8 rotated, their GND pads joined to one via south of them, clear of LS120's dummy pad.
* **Limiter.** U10 rotated 270 (IN / EN aft, OUT / ILIM / FAULT forward): ILIM to R85 and FAULT to R90 in the strip between
  U10 and D4 (no via on the ILIM tap); FAULT to In3 at (36.75, 27.0) and west along y 25.6 to C6's dog-bone (24.8, 25.6).
  USB_LIMITED: U10.6 down the column west of D4 (between the SWD B.Cu lines and D4) to C86 / C98, north of J2's holes to
  TP82 (moved onto the run) and west along y 41.15 to U11.7; R87 / R88 (U11's USB OV divider) moved beside U11.5 so
  USB_OVLO stays 2 mm long.
* **VBUS_SENSE.** F9's dog-bone (27.2, 28.0), B.Cu south at x 27.2 and 45° to R110.1; R9.2 to R110.1.

Widths: pair 0.2 mm; VBUS 0.3–0.4 mm; USB_LIMITED 0.3 mm (TPS2553 limit set by R85 66.5 k, about 0.36 A: 1.9 °C rise
at 0.2 mm by tools/ipc2152.py external fit, Inference); signals 0.1–0.15 mm.

## 3. pyro (D-R11-21, -22, -23)

**Fire path (F.Cu only, no series via).** BAT_IN J1.1 → Q120's drain tab, 1.0 mm (S-9 floor). ACT_FET_S 0.5 mm: Q120's
sources (now its north row, Q120 rotated 180) → through the 1.09 mm gap between the FETs (0.295 mm each side to the drain
tabs) → Q121's sources (south row). RAW_ACT 0.5 mm: Q121's east drain tab → x 14.65 → R134.2, with taps to R132 (bus-sense
top) and TP120 (moved east of R134.2). PYRO1_IGN 0.5 mm R134.1 → J121.2. PYRO1_OUT 0.5 mm J121.1 → trunk x 4.3 (taps
R173.1, R131.1) → Q124's drain; C128.1 by a 0.3 mm branch. Q124's sources: 0.3 mm bar, two 0.6 / 0.3 mm GND vias
(6.925, 31.6) and (8.225, 31.6) (R10 FIRE_RETURN).

Rise of the drawn widths at the 4.2 A, 20 ms fire pulse (adiabatic, 35 µm outer copper, Inference as R10 D-R3-03):
0.5 mm 5.7 K, 1.0 mm 1.4 K, the 0.3 mm return bar 16.0 K. tools/ipc2152.py's steady-state fit (external, no plane
credit) gives 89.5 °C at 0.5 mm and 40.4 °C at 1.0 mm for a continuous 4.2 A: an upper bound that does not apply to a
20 ms pulse (Inference).

**Gate drive.** Each P-FET has its own 100 k gate–source resistor on F.Cu beside its gate (R120 for Q120, R119 for Q121;
S-3c OK). Q120's island (Q120.4, R120.2, C120.2) and Q121's island (Q121.4, R119.1) each drop by one ACT_GATE barrel,
(14.6, 15.9) and (13.95, 21.0), to a 0.3 mm B.Cu trunk west of the crystal ending at R121 (moved to B.Cu, (14.4, 29.6));
Q122's drain reaches R121.2 by one ACT_DRV barrel (15.4, 29.7). Q122, R122 (PC1's 1 k), R123 (2 k) and C123 (10 nF) sit
south of PE4's lane on PC1's lane (y 28.0). Q124's network: PE4's lane west along y 26.4 / 27.3 to R126.1 and R127.1;
a gate column x 10.97 (R126.2, R128.1, C126.1, TP122) with Q124.4 on its own branch; a GND column to one via.

**S-8 (Measured on this board, nearest foreign inner copper to each barrel's inner ring).** ACT_GATE (13.95, 21.0):
1.750 mm (In3 I2C1_SDA); ACT_GATE (14.6, 15.9): none within 4 mm; ACT_DRV (15.4, 29.7): 1.218 mm (In1 ring of the GND
via (14.73, 31.2)); J121.1 / J121.2: 1.300 mm (each other's 2.5 mm inner ring). Each ACT_GATE / ACT_DRV barrel carries a
1.3 mm rule area on In1..In4 (no tracks, no fills) and J121's pads 2.3 mm areas (In1..In4 for J121.1, In2 / In3 for
J121.2), so the later In1 / In2 / In4 pours keep 1.0 mm (Inference until poured: re-measure after `ground`).

**Gate-net spacing (Measured, same layer).** PYRO1_OUT to 3V3: 4.154 mm (F.Cu, D120's 3V3 via (10.6, 21.8)); PYRO1_GATE
to 3V3 / 3V3A: none within 5 mm; **PYRO1_GATE_N to 3V3: 0.150 mm** (F.Cu, PE4's lane past U1.D2, a 3V3 ball). R10's
1.0585 mm (D-R26-04) cannot hold at the TFBGA: ball C3 (PE4) is 0.73 mm edge to edge from the 3V3 balls B2 and D2
(D-R11-23, owner deviation). No 3V3 / 3V3A inner copper exists yet; the In2 regions must keep 1.06 mm from these nets'
inner copper (they have none: all F.Cu).

**Not done (O-C2-1).** PYRO1_CONT, ARM1_SENSE (the two sense banks to U1.F1 / U1.H4) and ARM1_SENSE_MID (R132.2 to the
bus-sense bank): every path from the field or from R132 to the banks under Q120 crosses the ACT_GATE B.Cu trunk, core's
In3 I2C wall (x 13.2 / 13.75 from y 23.6, y 23.0 / 23.6 from x 13.8) or the crystal's B.Cu copper. Options: move the two
banks onto B.Cu east of the trunk (x 14.9 … 19.5, y 19.8 … 22.9 is free) and take the sense lines to the MCU on In3 north
of the I2C run, or move core's I2C In3 run west.

## 4. power, first part (D-R11-24)

Drawn: U9's dV/dt (C81), ILIM (R84) and OVLO (R82 / R83) legs on B.Cu; the damper R166 → C89 / C95 (BAT_DAMP, 0.5 mm F.Cu
north of R166's GND pad); U402's ILIM (R430, under the switch body); U11's ILIM (R86) and soft-start (C85). No via.

## 5. In2 plan (not drawn; Inference until poured)

| Region | Covers | Notes |
|---|---|---|
| RAW_PROTECTED | front-end block x 4.0–20.6, y 6.7–17.4; west corridor x 4.6–10.0 to y 33.2; x 10–15.2, y 33.2–36.6 to U11 / C97 / TP81; aft band y 4.9–6.7 to x 39.8 and a drop at U400 (x 37.4–39.8, y 6.7–8.1) | avoids the S-8 rule areas; U9 OUT vias (2 × 0.6 / 0.3, K-power) east of U9 |
| PORT_5V3 | x 35.4–45.5, y 11.4–13.4 (L400.2's vias); east column x 39.6–45.5, y 13.4–24.6 (C403, U401 IN, R400); band x 29.4–39.6, y 16.6–20.6 (C404 / C405) | U402.1 / C430 need a feed (O-C2-2) |
| 3V3 | U1's field and east to x 38.4 (covering the USB D- In3 run x 35.6–38.4, y 29.5–31.0 for K-region), forward to y 43.0 (J2, R460–R464, C460, LS120, D123, R91, R12 / R13); aft-middle x 19.5–25, y 8.4–17.5 (C461, U12.3, R432.2, D121.5, C90); a 1 mm finger along y 22.4–23.4 west to D120's via (10.6, 21.8) | keep 1.06 mm from PE4 / Q124 gate copper (none on inner layers) |
| 3V3A | from R164.2 / H1's via (20.0, 30.4) west of U1 north to U4's vias (19.9, 21.0), (23.6, 22.2), then **east of SCK's In3 run** to C30 / C31 (26.75, 20.7) entering from y ≤ 18 (O-C1-3); south-west to U5 / C32 / C10 / C11 / C22 | SCK's In3 x 24.6 stays under 3V3 only |
| PORT_4V8 | forward band y 43.3–49.2, x 8.5–39 (J410 / J420 / J440 pin 1, C410 … C445); joined to U401 by a B.Cu run east of J3 (x 42.3 / 43.2) plus a second link (K-plane: ≥ 2 links) | an In2 strip past J3 is too narrow (J3.2 / J3.3 shell pins) |

## 6. Open items (not verified)

* O-C2-1 the sense lines (section 3).
* O-C2-2 power placement before the rails can be drawn: (a) U9's west cell: EN (U9.1 → R165.2 at J400, R81 / C87) crosses
  the OVLO / FAULT / IN / OUT exits on B.Cu, so EN needs an F.Cu hop with two BAT_ENABLE barrels (as R10's one-via
  deviation) or a re-placed R165 / R81 / C87; (b) L1's SW pad faces away from U2 and C5 (BST) sits south of U2, away from
  BST / SW: rotate L1 180° and move C5 north of U2's pin row; (c) U400's SW pin faces east while L400 is west, so PORT_SW
  would detour 12 mm round U400 (aid result): rotate U400 180°; (d) U402.1 (PORT_5V3) is cut off from any PORT_5V3 region
  by RAW_PROTECTED and 3V3; (e) PORT_4V8 from U401 to the forward ports (section 5).
* O-C2-3 3V3 (45 pads) and 3V3A (15 pads): each pad's via to its In2 region; D120.3's via (10.6, 21.8) waits for the 3V3
  finger. TP80 / TP81 / TP88 (moved to y 34) wait for BAT_IN / RAW_PROTECTED / GND.
* O-C2-4 BAT_FAULT_N (H3), LOGIC_SOURCE_ST (G3), VLOGIC_SENSE (J3): their F.Cu lanes south of U1 and the long runs.
* O-C2-5 gate inconsistency: route_check r11 has no PARALLEL_VIAS (D-R11-08), so a second barrel beside a single-via tap
  fails track_loop / extra_vias, while check_r11 K-power (R10's SINGLE_OPEN_TAPS) fails any tap on one via: Q120.4 /
  Q121.4 → R121.1 (one ACT_GATE barrel each), R85.2 / R7.2 / R8.2 / U10.2 (own GND vias). Needs R11 entries in one of
  the two lists (owner / gate lane).
* O-C2-6 check_r11 K-power inherits R10's POWER_PATHS via specs: 'U9 IN' wants a 1.0 / 0.5 mm via on J1.1 → U9.5, but
  R11's J1 is a plated wire pad (no via on the path) and r11_route's via set has no 1.0 / 0.5 size; R11_DATA power_narrow
  is empty, so U9's 0.3 mm pin entries will fail the 1.0 / 0.7 mm floors. Needs R11 gate data (gate lane).
* O-C2-7 J121 / J1 wire pads keep 2.5 mm inner rings (pcbnew FlashLayer true on In1..In4), not "no unconnected inner
  rings" as stageB.md §9 says; S-8 then needs the 2.3 mm areas above. Setting the pads to remove unconnected inner layers
  (R10 D-R20-05) would shrink them to 1.75 mm (stage B footprint change).
* O-C2-8 GND pads of these families without a via yet (ground family): R84.2, C81.2, R83.2, R86.2, C85.2, R430.2, D402.2,
  C86.2 / C98.2 have one; Q124's return vias and the local GND vias stay dangling until In1 / In4 are poured.
* O-C2-9 the USB D- In3 run and VBUS / USB_FAULT_N In3 runs need their In2 region (K-region) once In2 exists.

## 7. Checks run

* `r11_stage_check` after each family (core → usb → pyro → power) on a scratch copy: all OK (section 1).
* `tools/check_r11.py --only S-1,S-2,S-3,S-3c,S-5,S-6,S-8,S-9` after pyro: OK.
* Full `m3_design/r11_build.sh` twice (stage A gate, fit_check r11, every stage check OK): identical SHA-256
  `34d5d839bbe4ac507f1a2ddce1dcb276e8e6f3ca57ec7a8573ac3eda5a4154c3`.
* Not run: check_r11 full (In1 / In2 / In4 not poured), K-region, K-power, plate model, any electrical test.

## 8. Stage C2b (2026-11-02): power placement, rails, In2 regions, barrels, PE4

Decisions D-R11-25 ... -30 (and D-R11-23 corrected) in `R11_DECISIONS.md`. Everything below is Measured on the board built by
`m3_design/r11_build.sh` unless labelled.

### 8.1 What was done

| Item | Result |
|---|---|
| O-C2-2 a, U9 west cell | U9 rotated 180; EN U9.1 -> R81 -> C87 -> R165.2 one B.Cu run, no via; U9 IN J1.1 -> C88.1 -> U9.5 B.Cu, no via (D-R11-25) |
| O-C2-2 b-e | L1 / U400 / L400 rotated, C5 / C402 at the BST / SW pins, U402 fed from L400.2 through C430.1, U401's divider and SS cap re-sided, PORT_4V8 to the ports through one In2 piece under J3 (D-R11-26) |
| Rails and In2 | BAT_IN, RAW_PROTECTED, VLOGIC, CAM_5V, PORT_5V3, PORT_4V8, 3V3A complete; 3V3 complete but R89.1 (D-R11-27) |
| O-C1-3 / K-region | SCK's In3 run under 3V3A only, NRST's under 3V3 only: check_r11 K-region OK |
| O-C2-3 | every 3V3 / 3V3A pad but R89.1 has its via to its region |
| O-C2-7 | J1 / J121 drop unconnected inner rings; J121 keep-outs 1.75 mm; S-8 OK (D-R11-28) |
| O-C2-5 | second barrels and `parallel_vias` entries (D-R11-29) |
| D-R11-23 | PE4 0.200 mm from D2 (was 0.150), every other gate-net copper >= 3.105 mm from 3V3 / 3V3A (D-R11-23, -30) |
| Gate data | `r11_gate_data.json`: `parallel_vias` (5 pairs), `power_narrow` (U9.5, U9.6, U401.9), `single_open_exceptions` empty |

Placement changes (r11_place.tsv): U9, C88, R81, C87, R82, R83, R84, C81, D402, TP80 (U9 cell); L1, C5, U400, L400, C402,
R400, R401, R404, R430, C430, C431, C99, TP83 (bucks / U402 / VLOGIC); R402, R403, R405, C408 (U401); C24 (NRST cap, core's
stub shortened to it). Fit, courtyards and DRC re-checked in the build.

### 8.2 Gate results

* `r11_build.sh` end to end, twice: every stage check OK; core 461, usb 428, pyro 387, power **252** unconnected (all on
  pending nets: GND 162 and the signal families). Identical SHA-256 both runs:
  `58371a74c08fbc9e431ed25b988c996f1c01802171f163e910f06b681d3910f4`.
* `tools/check_r11.py` on a zone-filled copy (In1 / In4 not poured): OK S-1, S-2, S-3, S-3c, S-5, S-6, S-7, S-8, S-9, W-1,
  W-2, LC-1, M-1, M-5, M-6, M-7, M-8, K-inner, K-region, K-plane, K-fill, K-lands, K-width, K-loader. Failing and why:
  K-power (23: 19 GND taps and Q124's return wait for the ground pours; U1.G3 / LOGIC_SOURCE_ST is O-C2-4; BOOT0, VCAP1,
  VCAP2 hang on core's single dog-bone vias, O-C2-12); K-copper (2: usb's GND via (35.15, 30.4) at D4.2's mask / paste,
  O-C2-13); K-ports (17, ports family); K-reference (ground family); K-legends (stage D); K-rules (14) and M-3 (1) are
  gate-lane / gate-data items (DRU floors, supports pin); S-4 cannot read the schematic from a scratch copy (run in place).
* check_r11 K-power power paths (U9 IN / OUT, U401 IN / EN / OUT, U402 IN, port feeds, CAM_5V, C84 hold-up, VLOGIC
  trunk, U400 OUT, U2 OUT): no finding.

### 8.3 Open items (not verified)

* O-C2-1 the sense lines (unchanged). A viable In3 corridor (Inference): y 18.5 from x 16 west to x 6.6 runs between the
  ACT_GATE keep-outs (VG_X / VG_X2 to y 17.2, VG_B / VG_B2 from y 19.7) and north of I2C's In3 run; the bank-side via is
  the hard part (R173 / PYRO1_OUT and the bank pads leave no legal site at x 6-7, y 22-24 on first look).
* O-C2-4 BAT_FAULT_N, LOGIC_SOURCE_ST, VLOGIC_SENSE; R89 (FAULT pull-up) is still at the aft edge in the BAT_IN In2 region
  and needs moving to a 3V3 area with the FAULT run. Every path from U9's side to U1's south / west balls crosses core's
  I2C In3 wall (x 13.2 / 13.75, y 23.0 / 23.6) and NRST's In3 run; the crossing has to be on F.Cu or B.Cu.
* O-C2-12 core's BOOT0 / VCAP1 / VCAP2 single vias fail K-power's single-open taps (core family).
* O-C2-13 usb's D4.2 GND via (35.15, 30.4) fails K-copper (mask / paste).
* O-C2-8 (GND, ground family): the local GND copper drawn here ends in pads with no via yet: U9.8 / R84.2 / C81.2 joint,
  R81.2, C87.2, R83.2, C88.2, R401.2, R403.2, C408.2, C430.2, R430.2, C402's neighbour U400.4, U401.4 / .6 / .11, C406.2,
  C407.2, and every decoupling cap's GND pad; Q124's two return vias wait for In1.
* D8 (input TVS) reaches In2 BAT_IN by one 0.6 / 0.3 mm via beside D8.1; its surge path impedance is not assessed
  (Inference).
* J400.2's BAT_SW_RETURN is one barrel: open, the board stays off (fail-safe, Inference).
* PE4 / D2 0.200 mm stays an owner deviation (D-R11-23).


## 9. Stage C2c (2026-11-03): sense lines, status lines, D4.2, supports, VCAP1

Decisions D-R11-31 … -36 and -40 in `R11_DECISIONS.md`; the C3 families of the same pass are in `stageC3.md`. Measured on
the board built by `m3_design/r11_build.sh` (SHA-256 `86fc4652…`, stageC3.md §1) unless labelled.

### 9.1 Done

| Item | Result |
|---|---|
| O-C2-1 | PYRO1_CONT (3 vias: (20.0, 28.8), (16.9, 21.9), (14.0, 19.0)) and ARM1_SENSE_MID (2 vias: (15.6, 20.02), (6.95, 23.47)) routed; both bank rows drawn (D-R11-35). ARM1_SENSE from U1.H4 not drawn (9.3) |
| O-C2-4 | VLOGIC_SENSE (1 via (21.6, 32.6)) and LOGIC_SOURCE_ST (2 vias (23.2, 28.8), (16.23, 41.6)) routed (D-R11-36). BAT_FAULT_N not drawn, R89 not moved (9.3) |
| O-C2-12 | VCAP1 second barrel (26.4, 28.0), listed in `parallel_vias` (D-R11-34); BOOT0 / VCAP2 have no site (9.3) |
| O-C2-13 | D4.2's GND via at (35.35, 30.4), 0.4 / 0.2 mm; check_r11 K-copper OK (D-R11-31) |
| M-3 | `supports` pinned from `r11_pcb.SUPPORTS`; check_r11 M-3 OK (D-R11-32) |
| K-rules | cause found: R10's floors and a condition-blind later-rule test in the gate (D-R11-40); not changed (tools/ is the gate lane's) |
| Placement | R460-R464 to an F.Cu column north-east of U1, J430.4's 3V3 via to the pin (D-R11-33) |

S-1 … S-9 OK on the final board; PYRO1_CONT / ARM1_SENSE_MID In3 runs keep the ACT_GATE barrels' S-8 keep-outs (check_r11
S-8 OK, Measured). PYRO1_CONT / ARM1_SENSE_MID are pyro-class critical nets: route_check gates their hygiene (0 findings);
they are on AUD-2's slow-return list, so no GND partner or one-region rule applies.

### 9.2 Gate results

r11_stage_check after pyro and power OK (unconnected 379 and 239); check_r11 results in stageC3.md §3.

### 9.3 Open items carried to stage C3's record

* ARM1_SENSE (H4) and BAT_FAULT_N (H3) / R89: stageC3.md O-C3-1. H3 and H4 have only the F.Cu lane x 22.4 between them
  (VLOGIC_SENSE took x 21.6); H4's via is pinched on B.Cu (C21.2 / BOOT0's via, 0.23 mm hole clearance against 0.25 mm,
  Calculation); the west-bound route must cross core's I2C In3 wall and the D120-K1 3V3 B.Cu run.
* BOOT0, VCAP2 and PA4 (LOGIC_SOURCE_ST) single barrels: stageC3.md O-C3-5 (check_r11 K-power, 5 findings).
* O-C2-8 (GND of the earlier families) continues as stageC3.md O-C3-7.

## 10. Status after stage C1b (2026-11-03, stageC1b.md)

* ARM1_SENSE (H4): drawn by the escape table (west on B.Cu, In3 to the bank), pending on route_check hygiene
  (stageC1b.md O-C1b-5).
* BAT_FAULT_N (H3): drawn to U9.4 (west, In3); R89 (its 3V3 pull-up) is still in the BAT_IN region, so R89.1 (3V3) and
  BAT_FAULT_N stay unconnected there (O-C1b-5).
* BOOT0 / VCAP2 / PA4 single barrels: in-field dog-bones excepted (D-R11-45); PA4's via (14.65, 39.90) open (O-C1b-4).
* LOGIC_SOURCE_ST and NRST were re-drawn by the escape table (D-R11-44); USB_FAULT_N re-drawn, pending (acute join at
  U10.4); QSPI_NCS lost its route and is open (O-C1b-1).
