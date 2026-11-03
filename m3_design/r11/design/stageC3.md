# R11 stage C3: families `ports`, `servo`, `status` (first part) and the stage C2c items (2026-11-03)

Stage C of `r11_plan.md` §4, third part. Nothing is committed or ordered. Decisions D-R11-31 … -40 are in
`R11_DECISIONS.md`; stage C2's own items are recorded in `stageC2.md` §9. Evidence labels as AGENTS §2.5. Coordinates are
board mm (x east, y forward from the aft edge, KiCad's y). Every route was drafted with a scratch maze aid (octilinear A*,
45° bends only, a drafting rule that keeps new tracks out from between a small part's pads) or by hand, reviewed, and
frozen as explicit tables in `m3_design/r11_route_{pyro,power,ports,servo,status}.py` (D-R11-07: the build never
searches; the aid is not in the repository).

**State.** Stage C3 is **not complete**. Written: `ports` (the wire sides of all four ports), `servo` (J122's four
outputs), `status` (LED anodes, buzzer); not written: `sd`, `signals`. No MCU-side net of the ports, servo, camera, SD,
LED or buzzer families is drawn: the south-west fan-out of U1 cannot carry them out of the field on the current core
copper (section 4, O-C3-1). Stage C2 is complete except ARM1_SENSE's MCU run, BAT_FAULT_N / R89 and three K-power
single-barrel taps (`stageC2.md` §9).

## 1. Gate results (Measured, `m3_design/r11_build.sh`, twice)

| Family | NETS done (cumulative) | r11_stage_check | unconnected after |
|---|---|---|---|
| core | 22 | OK | 461 |
| usb | 32 | OK | 428 |
| pyro (+ PYRO1_CONT, ARM1_SENSE_MID) | 46 | OK | 379 |
| power (+ VLOGIC_SENSE, LOGIC_SOURCE_ST) | 73 | OK | 239 |
| ports (8 wire nets) | 81 | OK | 225 |
| servo (4 output nets) | 85 | OK | 221 |
| sd, signals | not written: skipped | | |
| status (4 nets) | 89 | OK | 215 |
| ground | not written: 33 nets pending | | |

DRC on every stage copy: no violation other than `via_dangling` on pending nets (48 on the final board: GND vias waiting
for In1 / In4); route_check r11: 0 failing instances outside the pending nets after every family. Unconnected after
`status`: 215 = **164 GND + 51 non-GND** (31 nets; 3V3 1, R89.1). Both full builds gave SHA-256
`86fc465220faefc6a644233a26635e07e81a1852bf9d4fdc6fe0a067e3619ce0`.

## 2. What the new families draw

**ports (D-R11-37).** One cell per GH port translated by the port centre x0 (J420 12.4, J410 23.0, J440 33.6) and the
camera port J9. check_r11 K-ports evidence (Measured, track length pin centre to clamp pad centre, R not crossed): J410.3 /
J420.3 / J440.3 2.702 mm, J410.4 / J420.4 / J440.4 2.864 mm, J9.5 3.375 mm, J9.6 3.916 mm (bound 4.5); clamp GND pad to its
GND via 0.625 mm (D400.2 0.475 mm; bound 1.0). Each wire via has a GND via within 0.76-0.83 mm (GH cells) and 1.125 / 0.625 mm
(J9) (Calculation on the table; route_check `critical_via_no_gnd` finds none missing, Measured). New GND vias: (x, 46.45)
for x in 13.025, 14.275, 23.625, 24.875, 34.225, 35.475, and (28.75, 1.05), (30.2, 1.05), (29.0, 4.5), (31.55, 3.6). The
vias under J9's / J410's housings are tented (Inference, stage D's mask review).

**servo (D-R11-38).** SERVO1-4_OUT: one via each, (18.25, 2.175), (20.45, 3.075), (22.0, 6.325), (22.5, 6.625).

**status (D-R11-39).** LED_RED_A, LED_YEL_A (F.Cu, no via); BUZZ_G (B.Cu); BUZZ_OUT (B.Cu, one via (42.45, 40.15) to
LS120.2). Test points: no new copper needed (D-R11-39).

## 3. check_r11 on a zone-filled copy of the final board (Measured)

OK: S-1, S-2, S-3, S-3c, S-4, S-5, S-6, S-7, S-8, S-9, W-1, W-2, LC-1, M-1, **M-3** (now pinned, D-R11-32), M-5, M-6, M-7,
M-8, **K-copper** (D4.2 fixed, D-R11-31), K-inner, **K-region**, K-plane, K-fill, K-lands, K-width, K-loader.

| Failing rule | Findings | Cause | Owner of the fix |
|---|---|---|---|
| K-legends | 400 | silkscreen / designators not placed | stage D (r11_post.py) |
| K-reference | 1 (87 491 samples) | In1 / In4 GND not poured | ground family |
| K-rules | 14 | R10's floors applied to R11's D-R11-15 rules; condition-blind later-rule test (D-R11-40) | gate lane (tools/) |
| K-power | 23 | 17 GND joints and Q124's two fire-return vias wait for the ground pours; PA4 (2 vias), BOOT0 (2), VCAP2 (1) hang on single barrels (O-C3-5) | ground family; O-C3-5 |
| K-ports | 1 | D402.2 (J400's clamp, power family) has no GND via yet | ground family (O-C2-8) |

## 4. Open items (not verified)

* **O-C3-1 the south-west fan-out does not reach the north half (Measured on the board, Inference for the remedies).**
  Not drawn: ARM1_SENSE (U1.H4 to its bank), BAT_FAULT_N (H3 to U9, and R89 still in the BAT_IN area), SERVO1-4_MCU (G2-K2
  to R150-R157 / D121), CAM_MCU_RX / TX (H5 / J5 to U12), CAM_UART_OE (K5), CAM_PWR_EN (H6), CAM_FAULT_N (J6),
  CAM_5V_SENSE (K4), and the ports' MCU sides GPS / RADIO / AUX (J8 / K8 / J9 / K9 / E10 / F10). Thirteen of these leave
  balls in rows G-K but end north of the field (y 4-15) or west of it (the bank, y 22.8). The field is ringed on every
  layer: In3 by core's I2C run (y 23.0 / 23.6 / 24.4 from x 22.8 west, then x 13.2 / 13.75 south to y 41), NRST (x 19.6 from
  y 27.6, then y 33.5 east to x 33.1), QSPI_NCS (y 26.0, x 29.5) and USB_FAULT_N (y 25.6 east); B.Cu by QSPI_IO2 (y 24.4,
  x 21.6-29.0), SWD (y 23.2 / 23.6, x 26.8-32.35), the crystal's copper and the D120 / K1 3V3 run (x 11.0 and y 31.7); F.Cu
  by the A-row vias, PE4 / PC1's lanes west and the USB / QSPI lanes east. The B.Cu lane x 20.4 under ball column 1 (one
  track) now carries PYRO1_CONT; LOGIC_SOURCE_ST uses the In3 corridor through the field (x 22.8, y 26.8). Inside the
  field, H3, J3 and H4 share the two F.Cu lanes x 21.6 / 22.4 (G3 took the y 28.8 row gap): VLOGIC_SENSE uses x 21.6, so
  BAT_FAULT_N and ARM1_SENSE compete for x 22.4, and H4's own via (23.2, 29.6) is pinched on B.Cu between C21.2 and BOOT0's
  via (0.23 mm hole clearance at x 22.82, below the 0.25 mm rule). Ways out (Inference, each a stage C1 / A decision): move
  NRST to B.Cu or under the field's south edge so In3 opens west and south; move C17 / C21 (and C20) so G3 / H3 / J3 / D5 /
  E7 get interstitial vias; or re-assign the north-going functions to north / east balls (stage A pin table). The SD
  family (O-C3-4) and the LEDs (O-C3-3) need the same north-east re-plan.
* O-C3-2 the ports' MCU sides: the GH cells leave the gap between each port's two resistors (x0 + 0.91 … x0 + 1.59, north
  of y 44.6) for the TX MCU line into R4x1.1 and the north side of R4x0.2 for RX; the In3 run south of the field must lie in
  the 3V3 region south of NRST's y 33.5 run (stageC2.md §8 regions) with a GND via within 1.5 mm of each layer change.
* O-C3-3 LED_RED: its only via site, the dog-bone (24.8, 24.8), voids the In2 3V3 neck beside C6's via (24.8, 25.6) under
  QSPI_NCS's In3 run, which fails K-region (Measured on a trial board: K-region failed with the via and passed without it).
  A route that stays on F.Cu needs R32 / LED1 on the east side (swap the LED cells), which in turn needs a D6 route.
  LED_YEL (D6) has one site (24.8, 26.4) boxed by NCS's In3 lane, C6's via and the SD F.Cu lanes x 25.6 / 26.4 / 27.2.
  BUZZ_DRV (A1, site (20.0, 24.0)) to R162.1 at (44.4, 39.0) is about 35 mm across the field's north side (not drafted).
* O-C3-4 SD: R460-R464 now sit on the route (D-R11-33). Plan (Inference): SD_SCK by the site (27.2, 24.8) to In3 north
  along x 28.0-29.0 (the 3V3 strip between 3V3A and PORT_5V3), the others up the F.Cu lanes x 25.6 / 26.4 and east between
  R33 and the SWD vias (room for two tracks: R33's pad edge y 22.67 and the SWD vias' holes, 0.25 mm), D8 (CS) has no lane
  of its own; then B.Cu under J430 as nested L's in pin order (DAT1 north to DAT2 south), passing south of J430.4's moved 3V3
  via. The resistor column leaves one F.Cu track between its SD pads and C400 / C404 and via room only north of R463 and
  south of R464 and in the C400 / C404 gap: R462 (MISO) has no via of its own (Calculation on the placed pads). A first
  aid pass routed SCK, MISO, DAT1, DAT2 and failed MOSI / CS. A row reorder or one resistor on B.Cu is the next step.
* O-C3-5 K-power single-barrel taps: BOOT0 (D5, vias (23.2, 27.2) and (23.2, 32.4)), VCAP2 (E7, (24.8, 27.2)) and PA4
  (G3, (23.2, 28.8) and (16.23, 41.6)) have no second-barrel site under the TFBGA (D-R11-34). PA4's south via could take a
  second barrel beside R91 once the first is solved. Owner / gate decision: re-plan the bottom decoupling, or exact
  `single_open_exceptions` entries with measured reasons as R10 had before D-R24-03 / -04.
* O-C3-6 CAM_IO_3V3 (U12.7, U13.5, C93.1, C92.1, R103.1): U12.7 is boxed by U12.6 / U12.8 and CAM_5V's B.Cu run x 24.97
  (0.37 mm gap; a 0.2 mm power track does not fit, Calculation); only C92.1 - R103.1 was drafted. CAM_RX / TX_BUFFER: an
  aid pass found B.Cu routes along y 6.1 and under J430's west edge, not adopted because they cross the servo MCU region
  (D121, R154-R157) that O-C3-1 still needs.
* O-C3-7 GND for the ground family (Measured with pcbnew on the final board): 50 GND vias drawn, 48 dangling until In1 / In4
  are poured (this stage added the 10 listed in section 2). 118 GND SMD pads have no GND track end or via in them yet: C10.2
  C100.2 C11.2 C127.2 C129.2 C14.2 C16.2 C22.2 C23.2 C24.2 C29.2 C32.2 C400.2 C401.2 C403.2 C404.2 C405.2 C406.2 C407.2
  C408.2 C410.2 C411.2 C420.2 C421.2 C430.2 C431.2 C444.2 C445.2 C460.2 C461.2 C6.2 C60.2 C7.2 C8.2 C80.2 C81.2 C82.2 C84.2
  C85.2 C87.2 C88.2 C9.2 C90.2 C91.2 C92.2 C93.2 C94.2 C96.2 C97.2 C99.2 D121.2 D402.2 D8.2 D9.2 J122.5 J2.5 J3.B1A12
  J410.2 J420.2 J430.6 J430.9 J430.10 J430.11 J430.12 J440.2 J9.3 J9.4 LED1.1 LED2.2 Q123.2 R102.2 R103.2 R105.2 R130.2
  R133.2 R154.2-R157.2 R163.2 R166.2 R167.2 R178.2 R180.2 R401.2 R403.2 R405.2 R430.2 R431.2 R61.2 R64.2 R81.2 R83.2 R84.2
  R86.2 R92.2 TP74.1 TP88.1 U11.3 U11.4 U11.6 U11.12 U12.2 U13.2 U2.4 U3.4 U400.4 U401.4 U401.6 U401.11 U402.2 U5.3 U5.4
  U5.5 U9.8 (pads listed once per number; U5's are land pairs). J430.6 needs its via south of its pin (planned (35.205,
  14.35), so the SD runs pass) or north of it.
* O-C3-8 check_r11 K-rules (D-R11-40) is a gate-lane item.

## 5. Checks run

* `m3_design/r11_build.sh` end to end, twice: stage A gate OK, fit_check r11 OK, every stage check OK, identical SHA-256
  (section 1).
* `tools/check_r11.py` (full) on a zone-filled scratch copy of the project with its fit report (section 3).
* Not run: tools/check.sh (not this lane), any electrical test, signal integrity, JLC DFM of the new 0.1 mm runs, the plate
  model.

## 6. Status after stage C1b (2026-11-03, stageC1b.md)

* O-C3-1 (the escape): **re-planned** (D-R11-41 … -44): one pinned escape table, its checker in the build; every
  family passes its stage check. Of the nets listed here, still without escape copper: CAM_UART_OE (K5) and SERVO4_MCU
  (K2) (stageC1b.md O-C1b-1); drawn but pending (route_check findings, O-C1b-5): CAM_MCU_RX / TX, CAM_FAULT_N,
  SERVO1 / SERVO3_MCU, ARM1_SENSE, BAT_FAULT_N (R89 not moved), GPS_TX_MCU, AUX_TX_MCU. Finished: CAM_PWR_EN,
  CAM_5V_SENSE, SERVO2_MCU, GPS_RX_MCU, RADIO_TX_MCU, RADIO_RX_MCU, AUX_RX_MCU.
* O-C3-2 (ports' MCU sides): drawn by the escape table; GPS_TX / AUX_TX pending (tiny jogs).
* O-C3-3 (LEDs, buzzer): LED_RED and BUZZ_DRV (now PB15, ball G10, D-R11-42) finished; LED_YEL open (O-C1b-1).
* O-C3-4 (SD): SD_SCK / MISO / CS / DAT1 / DAT2 finished; SD_MOSI pending (O-C1b-5).
* O-C3-5 (single barrels): BOOT0 / VCAP2 / PA4's in-field dog-bones in `single_open_exceptions` (D-R11-45); PA4's via
  (14.65, 39.90) open (O-C1b-4).
* O-C3-6 (CAM_IO_3V3, CAM_RX / TX_BUFFER): drawn (U13 rotated, D-R11-43), pending (O-C1b-5).
* O-C3-7 (GND): the list is extended in stageC1b.md O-C1b-6 (65 GND vias now).
* O-C3-8 (K-rules): check_r11 K-rules OK on the C1b board (the gate lane's fix).
