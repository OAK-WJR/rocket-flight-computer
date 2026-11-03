# R11 stage C1: routing infrastructure and family `core` (2026-11-02)

Stage C of `r11_plan.md` §4, first part. Nothing is committed or ordered. Decisions D-R11-15 … -19 are in
`R11_DECISIONS.md`. Evidence labels as AGENTS §2.5. Coordinates are board mm (x east, y forward from the aft edge).

## 1. Infrastructure

| File | What it does |
|---|---|
| `m3_design/r11_route.py` | Copper primitives (`Draw`: octilinear, non-zero segments only; widths from the R11 set 0.1 … 2.0 mm; vias 0.4 / 0.2, 0.45 / 0.25, 0.6 / 0.3 mm, all through F → B; no via placed twice), the six-layer map (F, In1, In2, In3, In4, B), the family order `core usb pyro power ports servo sd signals ground`, fixed KIID seeds. A family whose `r11_route_<family>.py` does not exist is skipped. |
| `m3_design/r11_stage_check.py` | After each family, on a zone-filled temporary copy: kicad-cli DRC (every severity; only track / via dangling on pending nets allowed), unconnected items never rising (`--state`), no unconnected item on a finished net, `route_check --profile r11` failing only on pending nets. "Finished" = the `NETS` of the family and every earlier one; everything else is pending. After `ground` nothing is pending; while `ground` is not written it reports the pending count (`--final` makes that a failure). |
| `m3_design/r11_build.sh` | Its stage C hook (already present) now runs: each family, then its stage check, in order; missing families are skipped. |
| `m3_design/r11_sch.py` | Net classes in the generated `m3.kicad_pro` (D-R11-15). |
| `m3_design/r11_route_core.py`, `m3_design/r11_fanout.tsv` | The family and its frozen per-ball fan-out table. |

Net classes (D-R11-15): Default 0.1 mm track / 0.1 mm clearance / 0.4 / 0.2 mm via (JLC multilayer 0.09 mm track and
space plus 0.01, https://jlcpcb.com/capabilities/pcb-capabilities, read 2026-11-02, the DRU floor rule); Power (the
rails) 0.3 mm / 0.1 mm / 0.45 / 0.25 mm. DRC takes clearance from `m3.kicad_dru`, not the classes (Measured: a 0.12 mm
via-to-pad gap passes with the Default class at 0.15). Two DRU facts that shaped every via (Measured with kicad-cli on
a test copy): the 'General copper to hole clearance' 0.25 mm rule makes a 0.4 / 0.2 via keep 0.15 mm copper-to-copper
from any foreign copper (two foreign vias ≥ 0.55 mm apart), and the 1.0 mm test-pad clearance is effective.

## 2. What core routes

All 22 core nets are complete: HSE_IN / HSE_OUT, NRST, BOOT0, VCAP1 / VCAP2, SWDIO / SWCLK, I2C1_SCL / SDA, BARO_SDO,
IMU_CS, SPI1_SCK / MISO / MOSI, IMU_INT1, QSPI_CLK / NCS / IO0 … IO3. Plus the rail fan-out: every U1 supply / ground /
VCAP / VDDA ball's dog-bone and the bottom decoupling straps (3V3, 3V3A, GND are pending nets until C2 / ground).

Via sites under the ball field: a 0402 / 0603 part on B.Cu closes every interstitial site within (pad half-size +
0.3 mm) of its pads, which leaves columns x 20.8, 23.2, 24.8, 27.2 open, x 21.6 / 22.4 / 25.6 / 26.4 only on row
y 28.0 (and 30.4 / 31.2 east), x 24.0 never. Those closed sites are the F.Cu channels other nets use.

| Group | Layers | Vias | Route |
|---|---|---|---|
| HSE | F stub, B | 1 each | C1 / D1 to vias outside the west column; on B HSE_IN runs through the 0.5 mm gap between Y1's pad rows to Y1.1, C25 north; HSE_OUT into Y1.3, C26 south. GND vias (20.8, 25.6), (18.95, 25.15), (19.0, 27.5) within 1.5 mm. Y1.2 / Y1.4 / C25.2 / C26.2 to GND vias. No In2 / In3 copper under Y1 (only In3 I2C passes north of it, y ≤ 23.65). |
| NRST | F, B, In3 | 2 | E1 west to (19.6, 27.6); C24 on B; In3 down x 19.6 and east along y 33.5 to a via beside J2.3 (track ends inside J2.3, outside J2's F.Cu keep-out strip). |
| BOOT0 | F, In3, B | 2 | D5 dog-bone (23.2, 27.2); In3 down the via-free x 23.6 lane; via (23.2, 32.4); R5.1 on B. |
| VCAP | F, B | 1 each | E7 → (24.8, 27.2) → C20.1; F8 → (25.6, 28.0) → C19.1 (C19 / C20 swapped, D-R11-17). |
| SWD | F, B | 2 each | A9 / A10 vias north; B.Cu east along y 23.2 / 23.6 and down the free column x 32.0 / 32.35 under U3 (between the B.Cu USB / VBUS column x ≤ 31.52 and U10 / D4 x ≥ 33.05); vias beside J2.2 / J2.4. |
| QSPI | F (CLK, IO0, IO1 no via); IO3 F+In3; IO2 F+B; NCS F+In3+B | 0 / 0 / 0 / 2 / 2 / 2 | Under U3's body, north → south: IO3 y 28.35 (pin 7), CLK 28.8 (pin 6), IO0 29.6 (pin 5), IO2 30.6 (pin 3), IO1 31.6 (pin 2); NCS into pin 1 from (29.5, 32.4), R10 on B from that via. IO2 goes B.Cu y 24.4 / x 29.0, NCS In3 y 26.0 / x 29.5, IO3 an In3 hop over CLK / IO0. |
| IMU | CS F+B, MOSI F+B, SCK In3+B, MISO B, INT1 F+B | 1 / 1 / 2 / 1 / 1 | CS and MOSI down the F.Cu channel between LED1 / R32 and LED2 / R33 (x 22.85 … 25.35) over U4 to vias aft of pins 12 / 14; SCK on In3 aft of MOSI's via (U1's MOSI-west-of-SCK order is the reverse of U4's); MISO round U4's east on B; INT1 F channel x 22.4, B.Cu above U4's pin row into pin 4. U4 supply: 3V3A pins 5 / 8 and C30 / C31 to their own vias, GND 2 / 3 and 6 / 7 to vias, all clear of LED1 / LED2 / R32 / R33 on F (LED2 moved, D-R11-17). |
| I2C, BARO | F stub, In3, B | 3 / 3 / 2 | SDA (A4) / SCL (B4) In3 west north of Y1, south down x 13.2 / 13.75; a via beside R13 / R12, then In3 under U5 to vias south of pads 7 / 8. BARO_SDO from R64 by In3 to a via south of pad 6 (U5's inter-row band is closed to tracks). |

Track length (copper, Measured on the board): QSPI CLK 10.2, IO0 8.9, IO1 5.4, IO2 20.3, IO3 6.6, NCS 17.9 mm (loose
match only; 3V3 SPI flash, no length rule set). Via counts: 66 total; 23 GND, 7 3V3, 4 3V3A; signal vias as tabled.

GND partner vias (AGENTS §3): every layer change of a critical core net (HSE, QSPI, SPI1 / IMU_CS) has a GND via centre
within 1.5 mm; route_check's `critical_via_no_gnd` finds none missing.

## 3. In2 region plan (stage C2 draws it; nothing is poured now)

| Region | Covers | Feeds |
|---|---|---|
| 3V3 (main) | U1's field and its east side to x ≈ 37, aft over U4's lanes (y ≥ 17.5) and forward to J2 (y ≈ 42) | B2 / D2 / F4-F7 / K1 dog-bones, C14-C18 vias, U3, J2.1, R10 / R90 / R460-R464, C8 / C9 |
| 3V3A | a strip from R164.2 / H1's via (20.0, 30.4) west of U1, north to U4's vias (19.9, 21.0) and (23.6, 22.2), C30 / C31's (26.75, 20.7), and south-west to U5 / C32 / C10 / C11 | VDDA, U4, U5 |
| VCAP | none: B.Cu straps only | |

Every critical In3 run of core must lie under one In2 net (check_r11 K-region): NCS (y 26.0, x 29.5), IO3's hop
((28.0, 30.4)–(28.4, 28.35)) and SCK (x 24.6, y 18.25 … 23.6) all sit inside the 3V3 region as planned. The 3V3A strip
must therefore reach U4's pin-5 via (23.6, 22.2) and C30 / C31 (26.75, 20.7) without passing over SCK's In3 run at
x 24.6: that means a 3V3A neck between x 24.0 and 24.4 is not available, and C2 must either feed (26.75, 20.7) from the
east (y ≤ 18) or tie C30 / C31 to pin 5 differently. Recorded as open item O-C1-3 (Inference until C2 draws it).
Y1: no In2 / In3 copper under the crystal (x 14.26 … 18.95, y 24 … 28), as R10.

## 4. Open items left to later stages (not verified)

* O-C1-1 Fan-out for other families (`r11_fanout.tsv`, 69 connected balls: 35 core rows drawn): 32 rows reserve a
  lane or a via site, checked by
  `r11_route_core.fanout_check` only for "no core via on a reserved site"; whether each family's whole route fits was
  not checked (Inference). Two rows are `open`: C6 USB_FAULT_N and D6 LED_YEL have free dog-bone sites ((24.8, 25.6),
  (24.8, 26.4)) but NCS's In3 lane y 26.0 and IO2's B.Cu lane y 24.4 bound their exits; B6 LED_RED's planned exit
  (In3 west along y 25.2 to a via near (19.6, 24.6), F.Cu to R32.1) is a plan, not checked. The family that routes them
  may move NCS's In3 lane (core's table) if needed.
* O-C1-2 SCK's detour ratio is 1.57 against route_check's 1.6 limit (Calculation from the copper lengths); a later move
  of SCK's vias must keep it.
* O-C1-3 the In2 3V3A strip to U4 / C30 / C31 (section 3).
* O-C1-4 vias under C84's can on F.Cu (I2C / BARO_SDO at y 36–43.6, none in a pad): acceptable for a tented via under
  a can (Inference); stage D's paste / mask review confirms.
* O-C1-5 route_check information items on core nets (not gated): BARO_SDO detour (non-critical, 2 vias round U5's
  closed inter-row band), I2C extra bends, pad-end offsets at J2 (tracks end inside J2's pads outside its keep-out).

## 5. Checks run

* `m3_design/r11_build.sh` end to end: stage A gate OK, `fit_check r11` OK, `r11_stage_check core` OK — DRC 30 items,
  all `via_dangling` on pending GND / 3V3 / 3V3A vias (0 counted); unconnected 461 (from 497 placed), none on core's
  22 nets; route_check r11 82 failing, all on pending nets (dead copper / dangling vias of rails waiting for their
  planes), 0 on core's nets. Families after core: skipped (not written).
* Determinism: two builds of the board gave the same SHA-256 `3a36ab0bb3b447a65a387843d99a1b95666b10ebccbe8c9f15b89f44bdf9dea4`
  (the full build and a stage-B+core rebuild).
* `tools/check_r11.py --only K-copper,S-8,M-6,M-7` OK on the routed board; K-reference fails only because In1 / In4 are
  not poured yet (expected until the ground family).
* Freerouting 2.4.1 (local jar) was run once offline on a copy with U1's signal nets as a drafting aid; its result was
  not adopted (46 → 33 unrouted after 15 passes) and nothing from it is in the repository.

Not verified: any copper of the other families, In2 / In1 / In4 pours, K-region, signal integrity (no impedance or
crosstalk analysis), JLC DFM of the 0.1 mm channels, electrical figures that depend on copper.
