# R11 stage C1b: the U1 escape re-plan (2026-11-03)

Stage C of `r11_plan.md` §4, a re-plan of stage C1's fan-out. Nothing is committed or ordered. Decisions D-R11-41 … -49
are in `R11_DECISIONS.md`. Evidence labels as AGENTS §2.5. Coordinates are board mm (x east, y forward from the aft
edge, KiCad's y). U1 (TFBGA-100, 0.8 mm) sits at (24, 28): ball column c at x = 20.4 + 0.8 (c - 1), row A..K at
y = 24.4 + 0.8 r; interstitial (dog-bone) sites at x 20.8 + 0.8 i, y 24.8 + 0.8 j.

**State (after D-R11-49, section 8).** The escape-first pin map is drawn and gated: every used ball has escape copper
(`r11_escape_check`: 69 rows, 0 open), every non-GND net is joined (unconnected after `status`: 184, all GND), every
family from `core` to `status` passes `r11_stage_check`, and two full builds give one hash. Four drawn nets keep
route_check findings and stay pending (ARM1_SENSE, GPS_TX_MCU, SD_MOSI, CAM_RX_BUFFER; section 8.6), and check_r11's
remaining findings are the pours (ground family), silkscreen (stage D) and K-loader entries that need `tools/` (section
8.4). Sections 1-7 are the history of the first re-plan (D-R11-41 … -48).

## 1. Why (stageC3.md O-C3-1 … O-C3-7)

Stage C1 routed the core one family at a time; its In3 / B.Cu / F.Cu runs (I2C west at y 23.0-24.4 then south along
x 13.2 / 13.75, NRST down x 19.6 and east along y 33.5, QSPI_NCS along y 26.0 and down x 29.5, USB_FAULT_N along y 25.6,
BOOT0 down x 23.6, SWD north of row A, the A-row dog-bones) ringed the field on every layer, and the bottom decoupling
(C17, C21, R5) closed every interstitial site of rows F-K in columns 3-6. The balls of rows G-K whose targets are north
(servo, camera, BAT_FAULT_N) and the north / south crossings (I2C, NRST, ports) had no way out (Measured, stageC3.md).

## 2. The plan (D-R11-44)

Measured geometry under the field: a 0.4 / 0.2 mm via at an interstitial site is 0.4 mm from the two ball-column lines
beside it, so **every ball-column line (and every row line) on In3 and B.Cu is a free channel for one 0.1 mm track**
whatever vias sit on the sites (0.15 mm copper and 0.25 mm hole clearance, the D-R11-15 floors), and a site line is a
channel where no via sits on it (x 24.0 never carries a via: C19 / C20 close it). F.Cu inside the field carries only the
outer two rings and short row-gap lanes. So the plan is:

* **In3 is the north-going highway.** Balls in rows G-K whose targets lie north (SERVO1-4, CAM_PWR_EN, CAM_FAULT_N,
  CAM_5V_SENSE, CAM_MCU_RX / TX, the camera buffer) drop at their own dog-bone and run north on their own column line,
  leaving the field on In3 or after one more via on B / F north of row A (table: 5 In3-N, 3 B-N, 6 F-N exits).
* **South-going nets leave on F.Cu or In3 through the south edge** (ports J8 / J9 / K8 / K9, I2C on J7 / K7, LOGIC,
  VLOGIC, BOOT0 to R5) and **east-going nets on F / B / In3 through the east edge** (USB, QSPI, AUX, SWD, BUZZ, SD_SCK
  / CS / MOSI, USB_FAULT_N); the west edge carries HSE, PE4, PC1, PYRO1_CONT, NRST to C24, and the west-bound
  BAT_FAULT_N / ARM1_SENSE / SERVO3 (whose targets lie north-west).
* **Room was made** by moving C17, C21 and R5 out of the field (sites (21.6 / 22.4, 28.8 … 31.2) and (23.2 … 24.8,
  31.2 / 32.0) open), giving C19.2 its own GND via at the site (24.0, 31.2), and by three re-pins (D-R11-41 / -42):
  the I2C pair to PB10 / PB11 (balls J7 / K7, peripheral I2C2, south-west going like its targets) and BUZZ_DRV to PB15
  (ball G10, east edge). SWD now leaves east (SWCLK B.Cu y 23.6, SWDIO via moved to A10's north-east site (28.0, 24.0),
  B.Cu y 24.0) so both exits face J2.
* **Outside the field:** U13 rotated 180 and its CAM_5V tap redrawn north of it (the corridor east of U12.6 opens),
  R150-R153 put in J122's pin order (the servo outputs no longer cross, so R153.1 is reachable), LED cells unchanged.

The exits are pinned in `m3_design/r11_fanout.tsv` (one row per used ball: path, via site, exit side, exit layer,
slot, target and its centre; rails as `P`). `m3_design/r11_escape_check.py` proves from the table that every used ball
has a row, that no two exits on one layer and side are closer than 0.2 mm (one track per channel slot) and that each
exit faces its target, and with `--board` that every via exists on its net, every target pad is where the table says,
the copper crosses the courtyard at the pinned slot and every crossing of each net faces one of its own pads. It runs in
`r11_build.sh` after the families.

## 3. What moved

| Item | Change | Decision |
|---|---|---|
| Pin map | I2C1_SCL PB8 (B4) -> PB10 (J7), I2C1_SDA PB9 (A4) -> PB11 (K7), peripheral I2C2 AF4; BUZZ_DRV PC14 (A1) -> PB15 (G10); B4 / A4 / A1 now NC | D-R11-41, -42 |
| Placement | C17 (3V3) to (30.3, 25.3) B under U3's north end; C21 (3V3A) to F (19.0, 22.1) over the In2 3V3A strip; R5 to (28.4, 33.9) B; U13 rotation 180; R150-R157 order reversed (SERVO1 east) | D-R11-43 |
| core | I2C, NRST, BOOT0, QSPI_NCS removed from core's own tables and redrawn from the escape table; SWD re-laid (exit E); C17 / C21 / C19.2 / R5.2 vias; C13 / C15 GND strap shortened | D-R11-44 |
| power | LOGIC_SOURCE_ST's In3 run removed (escape table draws it); CAM_5V U13 tap redrawn for U13's rotation | D-R11-43, -44 |
| usb | USB_FAULT_N's In3 run and the C6 dog-bone removed; U10.4 to R90.2 one B.Cu run | D-R11-44 |
| servo | the four outputs redrawn straight (one via each, F.Cu under J122's housing) | D-R11-43 |
| new | `r11_escape.py` (all re-planned MCU-side copper, per family), `r11_route_sd.py`, `r11_route_signals.py` | D-R11-44 |

Every route of the escape table was drafted with a scratch negotiated-congestion router (octilinear A* on a 0.05 mm
grid, 45° bends only, net-aware clearance raster with the DRU's 0.25 mm hole and 1.0 mm test-pad rules, In3 limited to
the 3V3 region for critical nets, a GND partner via searched within 1.5 mm of each critical layer change), then frozen
as explicit tables in `r11_escape.py` (D-R11-07: the build never searches; the aid is not in the repository).

## 4. Gate results (Measured, `m3_design/r11_build.sh`, twice)

| Family | NETS done (cumulative) | r11_stage_check | unconnected after |
|---|---|---|---|
| core | 21 | OK | 466 |
| usb | 30 | OK | 433 |
| pyro | 44 | OK | 383 |
| power | 71 | OK | 241 |
| ports | 83 | OK | 227 |
| servo | 88 | OK | 214 |
| sd | 93 | OK | 210 |
| signals | 95 | OK | 199 |
| status | 101 | OK | 191 |
| ground | not written: 21 nets pending | | |

Unconnected after `status`: **191 = 181 GND + 10 non-GND in 6 nets** (QSPI_NCS 2, SERVO4_MCU 3, CAM_UART_OE 2,
LED_YEL 1, BAT_FAULT_N 1 (R89, still in the BAT_IN region), 3V3 1 (R89.1)) (stageC3: 164 GND + 51 non-GND in 31 nets).
DRC on every stage copy: no violation except `via_dangling` on GND (65 vias waiting for In1 / In4). r11_escape_check:
69 rows, 69 used balls, exits B-E 4, B-N 3, B-S 3, B-W 4, F-E 9, F-N 6, F-S 1, F-W 2, In3-E 3, In3-N 5, In3-S 6, In3-W
3, board checked OK, 4 open rows. Both full builds: SHA-256
`e57cb55e87cff7c4a7826d338b10dca7004fb6647f760a643a5988d137e9ac53`. Stage A gate OK with the re-pins (strict ERC 0,
54 / 54 seeded faults, `r11_sch_check`).

### check_r11 on a zone-filled copy (Measured; fit report from `fit_check --profile r11`)

OK: S-1 … S-9, W-1, W-2, LC-1, M-1, M-3, M-5 … M-8, K-copper, K-inner, K-plane, K-fill, **K-rules** (now OK after the
gate lane's fix), K-lands, K-width.

| Failing rule | Findings | Cause | Owner of the fix |
|---|---|---|---|
| K-legends | 397 | silkscreen not placed | stage D |
| K-reference | 1 | In1 / In4 GND not poured | ground family |
| K-region | 6 | In3 runs of CAM_MCU_RX (3 runs in the field), SD_MOSI (x 28.7), RADIO_TX_MCU (x 25.6), AUX_RX_MCU (south-east diagonal) cross places where the In2 3V3 fill is cut away between neighbouring vias (0.2 mm zone clearance): "over no In2 copper" | O-C1b-3 |
| K-power | 19 | 17 GND joints and Q124's fire return wait for the pours; PA4's second via (14.65, 39.90) is a single point (the three in-field single points now have `single_open_exceptions` entries, D-R11-45) | ground family; O-C1b-4 |
| K-ports | 1 | D402.2's GND via (ground family) | ground family |
| K-loader | 4 | PB10 / PB11 (I2C, USART3 loader pins) and PB15 (BUZZ_DRV, USART1 loader pin) carry nets without a LOADER allowance; PB9's allowance is stale | O-C1b-2 (gate lane / owner) |

## 5. Open items (not verified)

* **O-C1b-1 four balls without escape copper.** B5 QSPI_NCS (a regression: stage C1 routed it on the In3 y 26.0 lane the
  re-plan gave to the north-going lines), D6 LED_YEL, K2 SERVO4_MCU, K5 CAM_UART_OE: the drafting router found no route
  once the other nets held their channels (Measured on the scratch board). Remedies (Inference): QSPI_NCS on B.Cu along
  the site line y 24.8 and down x 28.8 between QSPI_IO3's via and QSPI_IO2; LED_YEL to a north
  row ball (PA15, A8, with its JTDI pull-up at reset) or the LED cells moved; SERVO4 / CAM_UART_OE by ripping the
  camera nets that now pass between U12 and U13.
* **O-C1b-2 K-loader.** The three re-pins land on ROM-loader pins (AN2606 Rev 64 Table 119: PB10 USART3_TX driven by
  the loader, PB11 USART3_RX and PB15 USART1_RX input pull-up). With BOOT0 high the loader drives SCL and pulls SDA /
  Q123's gate up (the buzzer may sound; Inference). R10 accepted I2C1 on loader pins PB8 / PB9 with an allowance; the
  same allowance for PB10 / PB11 / PB15 (and dropping PB9's) is a gate-lane / owner decision, else another ball (no
  non-loader I2C pair exists on this package: I2C1 PB6-PB9, I2C2 PB10 / PB11, I2C3 PA8 / PC9, Inference from DS12110
  Table 11 / AN2606).
* **O-C1b-3 K-region.** Either re-route the six runs along column lines whose In2 fill survives, or reduce In2's zone
  clearance under the field from 0.2 to 0.15 mm so the 3V3 fill stays between vias 0.8 mm apart (Calculation: 0.8 -
  2 × (0.2 + 0.15) = 0.1 mm, below the 0.2 mm minimum width, so 0.15 is not enough between two vias; only the column
  lines with one neighbouring via keep fill; Inference until re-drawn).
* **O-C1b-4 single barrels.** PA4's via (14.65, 39.90) south of L1 can take a second barrel (not drawn); BOOT0, VCAP2
  and PA4's dog-bones are listed in `single_open_exceptions` with measured reasons (D-R11-45).
* **O-C1b-5 drawn nets still pending (route_check, Measured on the final board).** Not in their family's NETS until
  cleaned: CAM_MCU_RX / TX (tiny jog, staircase, 3 missing GND partners, extra vias), CAM_FAULT_N (tiny jogs, extra
  vias), CAM_IO_3V3 (tiny jog), CAM_RX / TX_BUFFER (short segment, tiny jog, detour 1.82, extra vias), SD_MOSI
  (crossing without node at (29.5, 16.75), 2 missing partners, extra vias), GPS_TX_MCU and AUX_TX_MCU (tiny jogs),
  SERVO1_MCU (staircase), SERVO3_MCU (acute T at (21.05, 9.7)), ARM1_SENSE (short segment, tiny jogs), USB_FAULT_N
  (acute at U10.4), BAT_FAULT_N (R89 not moved to a 3V3 area).
* **O-C1b-6 GND vias for the ground family.** 65 GND vias are drawn and dangling until In1 / In4 are poured: stageC3's
  50 (O-C3-7), the moved parts' C17.2 (30.72, 24.7), C21.2 (19.43, 22.95), C19.2 (24.0, 31.2), R5.2 (29.27, 34.35), and
  15 partner vias of the escape table: (13.7, 43.0), (24.65, 32.4), (26.35, 43.1), (23.8, 43.15), (35.0, 42.5),
  (29.4, 27.4), (29.45, 22.45), (29.45, 13.7), (29.15, 20.0), (37.3, 17.65), (34.05, 20.9), (20.25, 13.7),
  (22.65, 6.65), (22.5, 13.5), (28.0, 23.2). stageC3's list of GND pads without a via (O-C3-7) stands; the moved C17.2 /
  C21.2 / R5.2 / C19.2 now have theirs.
* The firmware binding must take D-R11-41 / -42 (I2C peripheral I2C2 on PB10 / PB11; BUZZ_DRV on PB15, a normal GPIO
  instead of PC14's 3 mA RTC-domain pin) and the D-R11-43 servo resistor order (none: nets unchanged).

## 6. Checks run

* `m3_design/r11_build.sh` end to end, twice (stage A gate with the re-pins, fit_check r11, every stage check, escape
  check): identical SHA-256 (section 4).
* `tools/check_r11.py` (full) on a zone-filled scratch copy with its fit report (section 4).
* Not run: tools/check.sh (not this lane), signal integrity, JLC DFM of the new runs, any electrical test.

## 7. Follow-up pass (2026-11-03, after commit 51a4c02)

Decisions D-R11-46 … -48 in `R11_DECISIONS.md`. Measured on the board built by `r11_build.sh` unless labelled.

| Item (section 5) | Result |
|---|---|
| O-C1b-3 K-region | **Closed.** The In2 3V3 base fill now keeps 0.12 mm clearance and 0.1 mm minimum width (D-R11-46), so it stays continuous between two foreign vias 0.8 mm apart (0.8 - 2 × (0.2 + 0.12) = 0.16 mm, Calculation): CAM_MCU_RX's three runs and RADIO_TX_MCU now sit over one region. SD_MOSI and AUX_RX_MCU were re-routed clear of the fill voids at the 3V3A / PORT_5V3 strip and J2's holes. check_r11 K-region OK; S-8, K-plane, K-inner, K-copper still OK. |
| O-C1b-4 PA4 second barrel | **Not drawable.** A trial second barrel at (16.05, 38.50) on PA4's In3 run, joined to its B.Cu run, shorted LOGIC_ILIM's B.Cu run and C85.2 and came within clearance of VLOGIC's F.Cu run (DRC, Measured); the site (14.65, 39.90) is boxed by the I2C vias (0.57 mm), the 3V3 via (14.82, 40.90) and R86.1. The via is a fourth `single_open_exceptions` entry with that measured reason (D-R11-48). K-power: no U1 tap finding left. |
| BAT_FAULT_N / R89 | **BAT_FAULT_N closed, R89.1 open.** R89 moved to F.Cu (17.5, 19.3) rotation 180 (D-R11-47); R89.2 taps BAT_FAULT_N's In3 run by a via at its corner (17.30, 20.45), so BAT_FAULT_N is complete and in power's NETS. R89.1 (3V3) is not joined: R89 sits over an In2 3V3 strip that is an island (RAW south of y 18.6, 3V3A north and east), so any 3V3 via there makes K-plane fail (2 pieces, Measured on a trial); F.Cu from R89.1 is boxed (drafting router, Measured) and a B.Cu / In3 hop to R11.2 crosses CAM_5V_SENSE's B.Cu run. Open item: R89 to a spot over the main 3V3 fill, or R89.1 to C461.1 / R11.2 after the camera nets are re-planned. |
| O-C1b-2 K-loader, BUZZ_DRV | A non-loader ball was tried: BUZZ_DRV on PD15 (ball G8, not in AN2606 Rev 64 Table 119 / Rev 70 Table 135). The drafting router found no route from G8 (its four sites are taken by the QSPI_CLK / IO0 lanes, C18 and the port escapes, Measured on the scratch board), so BUZZ_DRV stays on PB15 (G10) with the allowance case below. |
| O-C1b-2 K-loader, I2C | No non-loader pair is escapable: the only I2C pair off the loader list is I2C1 / I2C4 SCL PB8 (B4) with SDA PB7 (A5); A5 is IMU_CS, and B4 / A5 sit in the north row where the pair walled the field in stage C3 (O-C3-1). PB6 / PB9 (I2C1) and PA8 / PC9 (I2C3) are loader pins, PF0 / PF1 (I2C2) and PF14 / PF15 / PH (I2C4) are not on this package, PD12 / PD13 (I2C4) carry QSPI IO1 / IO3 (DS12110 Rev 8 Table 11-13; AN2606 Rev 64 Table 119). The allowance case is below. |
| PB9's stale allowance | It lives in `tools/check_r10.py` LOADER_R10, not in `r11_gate_data.json`: a gate-lane item (remove PB9; add PB10 / PB11 / PB15 if the case below is accepted). |
| O-C1b-1, O-C1b-5 | **Still open.** QSPI_NCS, LED_YEL, SERVO4_MCU and CAM_UART_OE have no escape copper; SD_MOSI (no legal GND partner site within 1.5 mm of its vias (27.20, 25.60) and (29.80, 17.05): the partner search finds none, Measured; extra vias), CAM_MCU_RX / TX, CAM_FAULT_N, CAM_IO_3V3, CAM_RX / TX_BUFFER, GPS_TX_MCU, AUX_TX_MCU, SERVO1 / SERVO3_MCU, ARM1_SENSE and USB_FAULT_N keep their route_check findings and stay out of NETS. A negotiated re-route of these twenty nets with the rest held fixed did not converge (fails at SERVO4 / LED_YEL / BUZZ_DRV, overlaps in the field after 5 iterations, Measured on the scratch board); the field needs another re-plan of its In3 / B line allocation, not more local repair. |

### K-loader allowance case (R3-MCU-01 / R17-MCU-02 form; Inference unless labelled)

The ROM loader runs only from system-memory boot: BOOT0 high, or BOOT_ADD0 = 0x1FF0 with BOOT0 low (AN2606 Rev 70
Table 2 pattern 10). On this board BOOT0 is held low by R5 10 k (D-R11-45 single point); the BOOT_ADD0 read-back stays
the pre-flight item R10's PA2 allowance records.

* **PB10 (USART3_TX, loader drives push-pull) carries I2C1_SCL** (members R12.1 4.7 k pull-up to 3V3, U5.8 MS5611
  SCL). Idle board: the loader leaves USART3_TX at its idle level, high, the same level R12 holds; the pin transmits only
  after the loader has accepted a 0x7F sync on PB11, which cannot happen (below). U5's SCL is an input (MS5611: no clock
  stretching), so there is no contention: a high pin against a pull-up draws nothing, a low pin at most 3.3 V / 4.7 k =
  0.7 mA (Calculation), far below the 20 mA absolute maximum. The barometer sees no START (SDA stays high), so no
  transaction.
* **PB11 (USART3_RX, loader input with pull-up) carries I2C1_SDA** (members R13.1 4.7 k pull-up, U5.7 MS5611 SDA, open
  drain). Idle board: R13 and the loader's pull-up hold the line high, a continuous UART mark. The MS5611 drives SDA low
  only to acknowledge or return data after a master's START and its own address; in system-memory boot no code drives
  SCL / SDA as an I2C master (the MCU runs the loader; U5 is the only other device on the bus), so the barometer never
  drives SDA. With no falling edge there is no start bit, so the 0x7F sync byte cannot form.
* **PB15 (USART1_RX, PB14 / PB15 map, loader input with pull-up) carries BUZZ_DRV** (members R162.1 1 k to Q123's
  gate, R163 10 k gate to GND). Idle board: the loader's pull-up (about 40 k, DS12110 RPU, Inference) against
  R162 + R163 sets the pin near 3.3 V × 11 k / 51 k = 0.7 V and Q123's gate near 0.65 V (Calculation): a constant level,
  below Q123's threshold, so the buzzer stays off. A constant level has no falling edge followed by the 0x7F bit pattern,
  so no sync forms; nothing else drives BUZZ_DRV.
* The I2C1_SDA allowance on PB9 is stale (PB9 is NC since D-R11-41) and should be dropped.

### Follow-up gate results (Measured)

* `r11_build.sh` twice: every stage check OK, escape check OK (69 rows, 4 open), identical SHA-256
  `6dfac724838162e4377540a000985be277141a8fa86aedb2c0cf3e1efc7301d3`.
* Unconnected after `status`: 191 = 182 GND + 9 non-GND in 5 nets (QSPI_NCS 2, SERVO4_MCU 3, CAM_UART_OE 2, LED_YEL 1,
  3V3 1 at R89.1).
* check_r11 (full, zone-filled copy): OK S-1 … S-9, W-1, W-2, LC-1, M-1, M-3, M-5 … M-8, K-copper, K-inner, **K-region**,
  K-plane, K-fill, K-rules, K-lands, K-width; FAIL K-legends 394 (stage D), K-reference 1 (pours), K-power 18 (all GND
  joints and Q124's fire return, waiting for the pours; no U1 tap left), K-ports 1 (D402.2's GND via), K-loader 4 (the
  allowance case above; PB9's stale allowance is in tools/).

## 8. Escape-first pin map (D-R11-49, 2026-11-03)

Coordinator decision: re-plan the whole pin map escape-first on six layers. Fixed: PE4, PC1, PC0, PC5, BOOT0, NRST,
PH0 / PH1, PA11 / PA12, PA13 / PA14, VCAP, VREF and the supplies. Everything else could move to any ball whose function
DS12110 Rev 8 Tables 9-14 give. Measured on the board built by `r11_build.sh` unless labelled.

### 8.1 Capacity per side

The field box is U1's courtyard (x 19.38-28.62, y 23.38-32.62). North is aft (row A), south is forward (row K).

Channel capacity per side and layer (Calculation; DRU floors D-R11-15):
* **F.Cu:** the 10 edge balls, plus one 0.1 mm track in each of the 9 gaps between them (0.4 mm gap = 0.1 mm track +
  2 × 0.15 mm), so at most 19 exits.
* **In3 and B.Cu:** bounded by via sites, not by crossing slots (9.24 mm / 0.2 mm = 46 per layer). Of the 81
  interstitial sites, 26 are closed by bottom parts (C13-C16, C18-C20), 14 carry rail dog-bones, 17 carry signal
  escapes and 24 are free (Measured, final board). Some escapes use sites just outside the box (for example
  (19.9, 24.0), (23.2, 25.6), (21.6, 28.0)).

Demand and use per side: demand is the balls whose target lies on that side; "used" counts the pinned exits per layer
(Measured, `r11_fanout.tsv`). No side exceeds its capacity, so eight layers were not needed (Calculation).

| Side | Demand (balls) | F used / 19 | In3 used | B used | Balls |
|---|---|---|---|---|---|
| North (aft: IMU, camera, servo resistors, LED2) | 16 | 8 | 7 | 1 | A1 A2 A4 A5 A6 A7 A8 B1 B3 B4 B6 B7 B8 C5 C8 E2 |
| East (QSPI, USB, SD, SWD, AUX) | 15 | 10 | 2 | 3 | A3 A9 A10 B5 B9 B10 C10 D8 E10 F10 G5 G9 H9 J10 K10 |
| South (forward: ports, I2C, R5, LED1, buzzer) | 12 | 3 | 7 | 2 | D5 F9 G3 J3 J5 J7 J8 J9 K4 K7 K8 K9 |
| West (HSE, pyro / arming, NRST, U9, servos 3 / 4) | 10 | 2 | 4 | 4 | C1 C3 D1 E1 F1 F2 G2 H2 H3 H4 |
| Rails (dog-bone to plane / capacitor) | 16 | - | - | - | exit P |

SERVO3 / SERVO4 leave west and turn north outside the field. Their first pads, R152.1 (19.2, 3.8) and R153.1
(17.4, 3.8), lie beyond the north-west corner, so the escape check accepts either side.

### 8.2 Firmware binding list

The binding list (function: ball at HEAD 33876fe → D-R11-49 ball, mode) is the table in `R11_DECISIONS.md` D-R11-49.
The source of truth is `pin_table.tsv` column `r11_net` with the "R11 mode:" text in `r11_ball_source`, generated from
`r11_sch.R11_REPIN` (the citation for each row is there).

Summary:
* camera UART on UART4 AF8: PB9 TX / PB8 RX;
* SERVO1 TIM4_CH2 (PB7), SERVO2 TIM2_CH1 (PA15), SERVO3 / SERVO4 TIM5_CH1 / CH2 (PA0 / PA1);
* IMU_CS PE3, IMU_INT1 PD5 (EXTI5);
* camera control: CAM_UART_OE PC15, CAM_PWR_EN PC14, CAM_FAULT_N PC13;
* CAM_5V_SENSE PC2_C (ADC3_INP0);
* LED_RED PB1, LED_YEL PD2, USB_FAULT_N PD10, BUZZ_DRV PE8.

PC13-PC15 are low-speed outputs (3 mA, 2 MHz; DS12110 Rev 8 Table 62 p. 142 and p. 143 note 2). Their loads are
≤ 0.33 mA (Calculation). Firmware rule: an R11 binding must change the TIM, UART and EXTI assignments together. The
R10 firmware cannot run on R11.

### 8.3 Placement and power changes

* **Placement:**
  * LED1 / R32 move forward beside the ports, to (20.6, 42.3) / (23.0, 42.3).
  * U12 is rotated 180, so pins 4 / 5 face U1.
  * C93 moves to (22.6, 12.4).
  * C21 moves 0.15 mm west, to (18.85, 22.1). Its GND via goes to (19.45, 22.52) and its 3V3A via to (18.57, 21.12).
    This opens CAM_5V_SENSE's north exit at x 19.45.
* **U4's SPI:**
  * MISO goes F to a via at (25.0, 19.3), then B.
  * SCK has a via at (25.2, 23.6), runs In3 to (22.75, 18.3), then B.
  * U4.8's 3V3A via moves to (19.6, 21.25).
* **R89.1 (3V3):** joins R11.2 through a via over the 3V3A block, (18.57, 20.55).
  * The 3V3A block's west edge stays at x 20.8. A 21.2 trial left the In2 3V3 strip under R89 joined only by a neck
    under 0.5 mm (K-plane, Measured).
  * An In2 fill keep-out (0.5 mm radius) around the via stops the 3V3 base fill leaving a 0.18 mm² sliver inside
    3V3A's clearance ring (K-plane, Measured).
* **CAM_MCU_TX:** its via moves to (21.4, 16.75), and the GND via (20.8, 15.9) is dropped (GND (21.6, 18.1) is its
  partner). Before this, R11.2's 3V3 via (20.75, 16.6) joined the fill only through a neck (K-plane, Measured).
* **BOOT0:** gets a second barrel at R5's end, (28.30, 33.10). D5's dog-bone (23.20, 27.20) replaces the D-R11-45 site
  in `single_open_exceptions`; that site now carries SD_MOSI's GND partner.

### 8.4 K-loader cases (R3-MCU-01 / R17-MCU-02 form; Inference unless labelled)

The loader runs only from system-memory boot (section 7). BOOT0 is held low by R5, and BOOT_ADD0 read-back stays a
pre-flight item.

* **PB9 (I2C1_SDA, loader open drain, no pull) carries CAM_MCU_TX.**
  * Members: U12's A input (the camera UART buffer, CMOS input) only.
  * Idle board: the loader leaves PB9 open drain and released, so the line floats into U12's input.
  * U12 is disabled: OE is low by R102 10 k while PC15 is an input. The camera is unpowered: U402 EN is held low by
    R431 100 k while PC14 is an input. So nothing reaches J9.
  * Loader I2C1 is a slave and needs clock edges on SCL, PB6 (QSPI_NCS, held high by R10 10 k). No device on the
    board is an I2C master, so there are none and no address byte or command forms.
  * Firmware drives PB9 push-pull only after the UART4 binding.
* **PA15 (SPI3_NSS, loader input, no pull) carries SERVO2_MCU.**
  * Members: R151 1 k to SERVO2_OUT, R155 10 k pull-down, a D121 channel.
  * The loader only reads PA15, and R155 holds it low (0 V). The servo sees a constant low level and no pulses.
  * An SPI3 frame needs SCK edges on PC10 (SD_SCK). With no card activity there are none, so no command forms.
  * With PA15 held low the loader's SPI3 slave is selected for as long as the loader runs. Whether the loader then
    drives MISO (PC11, SD_MISO) with NSS low and no SCK was not re-read from AN2606's SPI section in this pass
    (Inference: an SPI slave shifts only on SCK edges, so at most it holds PC11 at a static level). That is harmless:
    the other members of SD_MISO are the card's DO and R462 (10 k pull-up to 3V3). The card's CS (SD_CS, PD0) is held
    high by R460 (10 k 1 % to 3V3; Measured on the R11 netlist, `schematic.net.xml`, and on the C4 board: R460.1
    SD_CS, R460.2 3V3), PD0 is not a loader pin and stays a reset-state input, and no SD_SCK edges reach the card,
    so its DO stays high-impedance and nothing contends with PC11 (Inference; SD card data sheet not re-read). A
    static PC11 level into R462 sources or sinks at most 3.3 V / 10 k = 0.33 mA (Calculation). Added in stage C4 at
    the gate lane's request (stageC4.md section 9).
  * PA15 resets as JTDI with an internal pull-up (DS12110 Table 9 note). Against R155 10 k that pull-up gives at most
    3.3 V × 10 k / (10 k + 30 k) = 0.83 V (Calculation, 30 kΩ the minimum pull-up, Inference). That stays below a
    servo's logic threshold (Inference) until firmware sets the pin to TIM2.
* **PB10 / PB11 (I2C on USART3):** unchanged, as section 7.
* **Freed loader pins:** PB15, PA2, PA3, PE11 and PE12 now carry no net, so the case for each is "NC".
* **Still in `tools/check_r10.py` LOADER_R10:** check_r11 shows 8 K-loader findings:
  * no allowance yet for PA15, PB10 and PB11;
  * PB9's allowance is still I2C1_SDA;
  * stale allowances for PA2, PA3, PE11 and PE12.

  All eight are gate-lane edits in `tools/`, which this lane does not change.

  **Status after stage C4 (stageC4.md):** the gate lane's LOADER_R11 is committed; check_r11 K-loader is OK on the C4
  board (Measured).

### 8.5 Gate results (Measured)

* `r11_build.sh` twice: every stage check OK and the escape check OK, with identical SHA-256 (section 8.7).
* Stage A: `r11_sch_check` OK.

| Family | NETS done (cumulative) | unconnected after |
|---|---|---|
| core | 22 | 470 |
| usb | 32 | 437 |
| pyro | 46 | 387 |
| power | 74 | 243 |
| ports | 87 | 230 |
| servo | 95 | 214 |
| sd | 100 | 210 |
| signals | 108 | 193 |
| status | 115 | 184 (all GND) |

* **New in NETS:**
  * core: QSPI_NCS;
  * usb: USB_FAULT_N;
  * ports: AUX_TX_MCU;
  * servo: SERVO1 / 3 / 4_MCU;
  * signals: CAM_FAULT_N, CAM_UART_OE, CAM_MCU_TX / RX, CAM_TX_BUFFER, CAM_IO_3V3;
  * status: LED_YEL.
* **Pending:** GND, 3V3 (the power family's own findings), ARM1_SENSE, GPS_TX_MCU, SD_MOSI and CAM_RX_BUFFER.
* **r11_escape_check:** 69 rows, 0 open. Exits: N 16 (F 8, In3 7, B 1), E 15, S 12, W 10, P 16. Board checked OK.
* **check_r11 (full, zone-filled copy):**
  * OK: S-1 … S-9, W-1, W-2, LC-1, M-1, M-3, M-5 … M-8, K-copper, K-inner, K-region, K-plane, K-fill, K-rules,
    K-lands, K-width.
  * FAIL K-legends 394: stage D.
  * FAIL K-reference 1: the pours.
  * FAIL K-power 18: GND joints and Q124's fire return, waiting for the pours (the same set as before). No single-via
    finding is left.
  * FAIL K-ports 1: D402.2's GND via.
  * FAIL K-loader 8: section 8.4.

### 8.6 Open items

* **ARM1_SENSE** (2 tiny jogs, 1 short segment, In3 near (17.5, 29.2)): the jog is forced by GND vias (18.0, 29.2) and
  (17.0, 29.3) and the 3V3A via (18.95, 31.1). A straight diagonal fails hole clearance (DRC, Measured). It was already
  pending before.
* **GPS_TX_MCU** (tiny jog at (26.3, 38.65)): forced by C99, C9.1 and VLOGIC's F.Cu. A single diagonal shorts them
  (DRC, Measured).
* **SD_MOSI:**
  * tiny jog at (28.6, 19.75): SD_CS's In3 run at x 28.95 and the 3V3 via (28.27, 19.25) leave no straight B.Cu line;
  * no GND partner within 1.5 mm of the via (29.8, 17.05): SD_CS's F.Cu at y 17.45, C400 / C404 and the PORT_5V3
    region leave no legal site (partner search, Measured);
  * 4 vias against a need of 1.
* **CAM_RX_BUFFER** (4 vias where none are needed): a B.Cu-only route is impossible, and the F / B minimum across the
  CAM_5V path is 4 (drafting router, Measured).
* **Ground family:** In1 / In4 pours and the GND joints (unchanged list in O-C1b-6, plus the moved C21.2 via
  (19.45, 22.52)).
* **Gate lane:** the `tools/` LOADER_R10 edits (section 8.4).

### 8.6a Status after stage C4 (2026-11-03, stageC4.md)

* ARM1_SENSE: **closed** (one In3 diagonal, D-R11-51); in pyro's NETS.
* GPS_TX_MCU: **closed** (jog middle 0.5 mm, D-R11-52); in ports' NETS.
* SD_MOSI: jog **closed** (D-R11-53); the via count (4 against 1 + 2) and the missing GND partner at (29.80, 17.05) are
  forced (Measured) and are allowlist requests to the gate lane (stageC4.md section 4).
* CAM_RX_BUFFER: forced (4 vias against 0 + 2, Measured), an allowlist request (stageC4.md section 4).
* Ground family: written (D-R11-50); 0 unconnected items.
* Gate lane: K-loader OK on the C4 board.

### 8.7 Checks run

* `m3_design/r11_build.sh` end to end, twice: identical SHA-256 `fdd011541bda7c9b9359357912c5fdbf4aba01aebcb1157c80bcc9323e85bea2`.
* `tools/check_r11.py` (full) on a zone-filled copy of the built board with its `fit_check --profile r11` report.
* `r11_escape_check --board`.
* Not run: tools/check.sh (not this lane), signal integrity, JLC DFM, any electrical test.
