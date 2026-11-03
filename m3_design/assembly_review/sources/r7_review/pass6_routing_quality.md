# R7 review pass 6: routing quality of critical and changed nets

Reviewer scope: electrical routing quality of the nets fix pass 5 touched (QSPI_CLK, the radio band and RXEN,
ACT_GATE, RAW_ACT, the camera UART wires, USB_LIMITED, VLOGIC, PYRO1_CONT, CAM_FAULT_N, SERVO4_MCU, LOGIC_*,
PULLPIN_EXT, CAM_EN, CAM_5V(_SENSE), LED_RED, 3V3_RADIO, GND, BAT_IN) and of the pyro nets, SPI1, SWD and the power
feeds, against the owner's clean-routing criterion (REQUIREMENTS M2, AGENTS.md §3): detour ratio, vias and layer
hops, bus tidiness, reference continuity and split crossings, and whether a cleaner route fits where a messy one
remains.

Board reviewed: `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
`1ffc2585cbbb2a49623a5010b2792500849f06989cf43e48fb3e56068cddf9df` (fix pass 5 final, the hash bound in M3_R7 and
R7_VALIDATION). Same hash before and after this review. Comparison boards: the pass-5 board `c6fe595c…c7c7` and R6
`3b215ba` (+18 mm in y). Read-only: boards were copied to my scratch folder; one scratch experiment (§7, P6-01) saved a
modified copy there only. The only repository file written is this report.

## 1. Method

1. **Gate.** `tools/check.sh` on the repository board: exit 0 (DRC 0, unconnected 0, parity 0, ERC 0; audit OK; silk
   0; R7 contract OK; `routing hygiene: 0 failing, 33 allowlisted, 0 stale allowlist entries, 0 out-of-date no-GND
   reasons, 30 leftovers recorded (0 unrecorded, 0 stale), 0 out-of-date route figures, 0 removable jog / staircase /
   short-segment exceptions: OK`; actuator contract OK; fit OK).
2. **Copper diff**, pass-5 board → final, every track and via per net (`diffp3.py` against `p5.json`).
3. **Per-net metrics**: `route_check --routes` on both boards; `route_check --report` instance diff (same tool on both).
4. **Independent geometry scans**: the pass-5 `scan5.py` and the pass-2 `scan.py` on both boards, instance diff; a new
   local-detour finder (`bumps.py`: every window of ≥ 3 segments inside a plain-node chain whose first and last
   segments are parallel and whose path exceeds the octilinear end-to-end distance by > 0.8 mm and 1.3×), on every
   critical net (signal classes, power rails).
5. **Reference planes**: `refscan.py` widened to every non-GND net (0.05 mm samples; F→In1, In2→B, B→In2), both
   boards, event diff; `tools/critical_reference.py` pass-5 → final (`--extended`) and R6 → final (R6 method and
   `--extended`).
6. **Pours**: piece counts and areas of every power and GND fill on both boards.
7. **GND vias** at every critical-net via (nearest GND via centre).
8. **Neighbours**: every new or moved track/via of fix pass 5 against other-net copper on shared layers
   (`newnbr.py`, pcbnew shapes, edge gaps < 0.25 mm); coupled length of the CAM_FAULT_N / SERVO4_MCU pair;
   `mind.py` net-to-net minima.
9. **Candidate routes**: `probe2.py` (edge gaps of candidate copper to every other-net track, via and pad with the
   applicable rule, and power-zone outlines crossed) for SERVO4_MCU, QSPI_IO3, I2C1_SCL, CAM_RX_WIRE, the 3V3 B.Cu dent
   east of U1.
10. **Experiment** (P6-01): QSPI_IO3 straightened on a scratch copy, native `ZONE_FILLER` refill, `kicad-cli pcb drc
    --severity-all --schematic-parity`, `route_check`, `check_r7`, `check_actuators`, `critical_reference`, `scan5`.
11. **Renders** (`render_pdf.py` + `pdftocairo`): band, QSPI_CLK/RXEN, camera wires, PYRO1_CONT/NRST/SWCLK cluster,
    CAM_FAULT_N/SERVO4_MCU, USB at J3.

## 2. Pass-5 findings in this dimension: closure

| Pass 5 | Disposition (R7_VALIDATION) | Checked on the final board | Verdict |
|---|---|---|---|
| P5-ROUTING_QUALITY-01 (band-end split crossings) | Fixed (`band_end`) | `R7_GND_In2_strip` covers x 6.9–9.9, y 25.0–31.3; BAT_IN vias (7.6, 26.6), (8.8, 26.6) gone (diff). refscan: the 7 band-end GND → BAT_IN change events gone (BUSY, DIO1, MISO_MCU, MOSI, NRST, NSS, SCK); RADIO_MOSI and RADIO_SCK now have 0 mm over BAT_IN. Radio B.Cu over In2 BAT_IN 24.33 → 12.16 mm (U1 end only). BAT_IN In2 one piece (770.8 → 760.3 mm²); GND In2 one piece (+12.5 mm²). M3_R7 l.500–505 corrected | **Closed.** One stale figure left in C5 (P6-02) |
| P5-ROUTING_QUALITY-02 (PYRO1_CONT S/SE/S/SE; unrecorded approaches) | Fixed and recorded | F.Cu now (35.78, 60.65) → (35.78, 65.25) → (40.88, 70.35) → (40.88, 74.75): S 4.6 / SE 7.21 / S 4.4, same 11.61 mm, `extra_bends` instance gone. Gaps (`mind.py`): PYRO1_GATE_N 1.079, PYRO1_GATE 3.078, PYRO1_OUT 0.715 (rule C 0.3), SPI1_SCK 2.750, SPI1_MOSI 3.323, IMU_CS 1.895 mm, no RAW_ACT copper on a shared layer. GND via at every layer change: 1.112, 0.721, 1.014, 0.728, 0.764, 1.408 mm (unchanged). The approaches are in M3_R7 "Close adjacencies kept", the P4-REGRESSION-01 row and C15, plus the new GND via (41.375, 70.625) 0.170 mm | **Closed** |
| P5-ROUTING_QUALITY-03 (NRST records; own-net stacking) | Records fixed; optional copper not done | M3_R7 l.440–445 and C10 now say 10.35 mm with no B.Cu GND above, 3V3A over 6.4–7.2 mm, no PYRO1_CONT. NRST copper unchanged: B.Cu (30.8, 53.1) → (30.8, 52.3) → (31.5, 51.6) still lies on its own In2 branch for about 1.5 mm | **Records closed.** The stacking is a review-only residual that is not in the deviation list (P6-03) |
| P5-ROUTING_QUALITY-04 (three lengthened jogs) | 2 removed, 1 forced and recorded (C16) | LOGIC_ILIM now S 0.6 / SW 0.742 / SE 2.51 (no A,B,A); SERVO4_MCU one In2 run x 15.505 (67.15 → 101.127). I2C1_SCL: a straight run down x 25.35 overlaps BOOT0's via (`probe2`: gap 0.000) — forced as recorded. C16 also names QSPI_CLK's new 0.509 mm step and CAM_RX_WIRE's In2 step (its straight drop at x 44.251 overlaps BAT_SW_RETURN's In2 run, `probe2` gap 0.000: forced) | **Closed** |
| P5-ROUTING_QUALITY-05 (A5 obstacle) | Closed by P5-RG-01 (A5 deleted) | No QSPI_CLK allowlist entry; C16 names QSPI_IO3's via (22.5, 40.3). QSPI_CLK → IO3 via 0.310 mm, → RXEN via 0.240 mm (record: 0.24) | **Closed** |
| Related: P5-REGRESSION-02 (single-via GND pieces) | Fixed (4 second vias) | Vias present (diff); `critical_reference` pass-5 → final 0 lost; refscan: no event on any critical net from them | Closed (their adjacencies: P6-03) |
| Related: P5-ROUTING_GEOMETRY-01/-03 (band staircases, QSPI_CLK jog, ARM1_SENSE GND vias) | Fixed | Band: E-lane / 45° fan-in step / E-lane / 1.004 mm corner chamfer, nested corners (render); BUSY/MISO_MCU fan-in steps (A3/A4) remain allowlisted. ARM1_SENSE vias (14.55, 94.15) / (14.55, 97.55) have GND vias at 0.721 mm | Closed |

## 3. What fix pass 5 changed (copper diff, pass-5 board → final)

Tracks 1,809 → 1,777, vias 694 → 706 (GND +22 / −4, of which 4 are 20 µm moves; BAT_IN −2; CAM_5V_SENSE −2;
CAM_TX_WIRE −2 +1; CAM_RX_WIRE −2 +2; LED_RED −1), zones 52 → 54. Changed nets, exactly the handoff's list: 3V3_RADIO,
ACT_GATE, BAT_IN, CAM_5V, CAM_5V_SENSE, CAM_EN, CAM_FAULT_N, CAM_RX_WIRE, CAM_TX_WIRE, GND, LED_RED, LOGIC_ILIM,
LOGIC_SOURCE_ST, PULLPIN_EXT, PYRO1_CONT, QSPI_CLK, RADIO_BUSY, RADIO_MISO_MCU, RADIO_MOSI, RADIO_RXEN, RAW_ACT,
SERVO4_MCU, USB_LIMITED, VLOGIC. SPI1, SWD, HSE, USB data, NRST, PYRO1_GATE(_N), ARM1_SENSE tracks, the RF lines and
the radio/GNSS corridor are byte-identical.

## 4. Per-net metrics (route_check --routes, pass-5 → final)

| Net | Length / ratio / vias | Comment |
|---|---|---|
| QSPI_CLK | 13.35 / 1.00 / 0 → 13.40 / 1.01 / 0 | pin column x 22.85 → 0.509 mm 45° step → lane x 23.21 (C16, forced by QSPI_IO3's via and RXEN's via) |
| RADIO_RXEN | 51.88 / 1.21 / 4, unchanged length | lane on its via column x 23.8; RXEN–QSPI_CLK parallel edge gap 0.25 → 0.415 mm |
| RADIO_BUSY / MISO_MCU / MOSI | 66.66 → 66.42, 61.90 → 61.80, 45.90 | nested 45° corners; fan-in pitch 0.5 → 0.4 mm in 0.1 mm-per-lane steps |
| PYRO1_CONT | 53.33 / 1.31 / 6, unchanged | S/SE/S |
| CAM_RX_WIRE | 27.54 / 1.23 / 3 → 29.02 / 1.30 / 3 | +1.48 mm: the via moved to (43.75, 42.625) so that TX can run straight east |
| CAM_TX_WIRE | 20.99 / 1.26 / 2 → 20.31 / 1.22 / 1 | off In1; In1 now carries no signal copper |
| CAM_5V_SENSE | 36.91 / 4 vias → 36.75 / 2 vias | one In2 run |
| LED_RED | 3 → 2 vias | hop on F.Cu |
| ACT_GATE | 27.82 → 27.33 mm | square T on Q121.4's horizontal (the T lands on that segment's centre line) |
| USB_LIMITED, VLOGIC, 3V3_RADIO, CAM_5V, CAM_EN, CAM_FAULT_N, LOGIC_*, PULLPIN_EXT, SERVO4_MCU | ±0.5 mm | tidy-ups; new information instances only `pad_end_offcentre` 3V3_RADIO into C310.1 (0.304 mm, a 45° entry ending at the foot of the perpendicular from the pad centre, inside a 1.41 × 1.35 mm pad) and `width_change_junction` USB_LIMITED (0.25 mm branch to C98 at a T on the 0.4 mm trunk) |
| Unchanged | SPI1_SCK 1.20 / 1, MOSI 1.12, MISO 1.04, IMU_CS 1.08; QSPI_IO0–3 1.16–1.25; USB_DP/DM 1.24/1.27; HSE 1.00/1.18; SWCLK 1.90 / 4, SWDIO 1.48 / 4; NRST 1.33 / 4 | — |

`route_check` instance diff (same tool on both boards, 342 → 312): only removals, plus six new instances, all
information or allowlisted categories: `extra_bends` LED_RED / RADIO_BUSY / RADIO_MISO_MCU / SERVO4_MCU,
`pad_end_offcentre` 3V3_RADIO, `width_change_junction` USB_LIMITED. `scan5.py` 545 → 501: jog_tiny 11 → 4 (BUSY and
MISO_MCU fan-in steps, SW_NODE, the GND step inside via (31.5, 53.5)), staircase 7 → 0, via ring overlap 3 → 0,
redundant copper 1 → 0, critical layer change without GND via 11 → 9; nothing new on a critical net except the
re-shaped band lanes and QSPI_CLK's 0.509 mm step.

## 5. Reference planes and split crossings

- **critical_reference, pass-5 → final (extended set):** 0 lost, 0 candidate-new. **R6 → final:** 603 lost / 882
  candidate-new (R6 method; the +21 are QSPI_CLK F.Cu at (23.31, 39.35–39.55), its lane edge grazing RXEN's via
  antipad, recorded in C2); extended 2,312 / 4,325. Matches the handoff and M3_R7.
- **refscan, all non-GND nets, pass-5 → final:** every change is neutral or better on the critical nets. Radio band
  lines lose their GND → BAT_IN change events; RADIO_RXEN, LED_RED, CAM_RX/TX_WIRE, CAM_5V_SENSE, SERVO4_MCU,
  VLOGIC_SENSE gain referenced length; PYRO1_CONT void +0.05 mm (16.08 → 16.13, the new x 40.88 end at its via);
  CAM_FAULT_N void +0.52 mm, CAM_EN +0.17, PULLPIN_EXT +0.15 (non-critical). No new plane-net change event on any net.
- **Remaining split crossings on critical nets:** only the corridor's U1 end, 7 lines GND → BAT_IN (BUSY, DIO1,
  MISO_MCU, MOSI_MCU, NRST, NSS, SCK_MCU) plus MISO_MCU's 3V3 → BAT_IN edge, x 5.3–10.2, y 47.5–50.5; there the In2
  BAT_IN arm is U9's J1 feed, so the record's reason holds (C5). Its per-line length is misquoted (P6-02).
- **Pours:** 3V3 In2 5 pieces (455.35 / 74.51 / 17.64 / 10.33 / 7.46 mm²; the U1/U4 island still one 74.51 mm²
  piece), 3V3A 1, BAT_IN In2 1, CAM_5V 1, GND In1 1, GND In2 1; GND F.Cu 43 / B.Cu 35 pieces as recorded (C14).

## 6. GND vias at critical layer changes

Nearest GND via centre to every via of the critical signal nets on the final board: PYRO1_CONT 0.721–1.408;
PYRO1_GATE_N 0.750, 1.309; ARM1_SENSE 0.776, 0.750, 0.721, 0.721; PYRO1_CONT_MCU 1.005; ARM1_SENSE_MCU 0.776;
SPI1_SCK 0.781, MOSI 0.849, MISO 1.379; IMU_CS 1.204; HSE_IN 0.900, HSE_OUT 1.204; USB_DP 0.802 / 1.250 / 0.806,
USB_DM 1.393 / 1.390; QSPI_IO0 0.776 ×2, IO1 1.500 / 0.849, IO2 0.800 / 0.752 / 0.781, IO3 0.806 ×2, NCS 0.800 /
0.922. Over 1.5 mm: only the 8 allowlisted radio vias (1.65–3.57 mm) and PYRO1_GATE's TP122 pad via (2.93 mm, A8) —
the gate's `nognd_audit` reports 0 out of date. (QSPI_IO1 (13.0, 51.5) sits at exactly 1.500 mm.)

## 7. Findings

No Critical. **One Major**, two Minor.

| ID | Sev. | New in fix pass 5 | Finding |
|---|---|---|---|
| P6-ROUTING_QUALITY-01 | **Major** | no (R6 copper, never raised individually) | QSPI_IO3 keeps a needless square bump (1.2 mm west and back, four extra 90° corners, +2.40 mm) where one straight segment clears every rule; it is in no deviation list, and R7_VALIDATION part F files the scan category that finds it ("chain detours") as "not defects by M2's wording" |
| P6-ROUTING_QUALITY-02 | Minor | yes (stale after the band-end fix) | Deviation C5 and M3_R7 l.503 still give "3.1–3.8 mm over BAT_IN per line" for the U1 end; that was the per-line total over both ends; the U1 end alone is 1.50–1.96 mm (12.16 mm for 7 lines) |
| P6-ROUTING_QUALITY-03 | Minor | partly | Records: the new GND via (35.85, 53.275) is 0.177 mm from NRST's via (35.8, 53.95), missing from the adjacency lists (and an NRST–GND short is not of the "fail-safe" kind the list describes); CAM_FAULT_N / SERVO4_MCU parallel coupling grew from 6.9 to 30.4 mm at < 0.2 mm without the length being recorded; NRST's own-net stacking (P5-RQ-03 option) is not in the deviation list |

### P6-ROUTING_QUALITY-01 (Major): QSPI_IO3's inherited square bump is a needless detour on a critical net

**Geometry (final board, all R6 copper translated +18 mm; `q.py`/`common.py` origin check).** QSPI_IO3 F.Cu, w 0.2 mm,
from its via (22.5, 40.3) to U3.7 (21.07, 34.63):
(22.5, 40.3) → (22.5, 37.7) → **(21.3, 37.7) → (21.3, 36.7) → (22.5, 36.7)** → (22.5, 35.4) → (21.7, 34.6).
The bold part is a rectangular excursion 1.2 mm west and back for 1.0 mm (N, W, N, E, N): +2.40 mm and four 90°
corners on a critical (QSPI) net. The pass-2 geometry scan listed it once in its appendix (`pass2_routing_geometry.md`
l.1915, "chain detour … 8.431 vs 6.031 mm"); no pass has raised it, and today's gate cannot see it: the net's overall
ratio is 1.19 (below `route_check`'s 1.6× net-level detour test), the turns cancel (not a `u_turn`), and N/W/N/E/N is
not an A,B,A,B run (not `extra_bends`). My local-detour finder (`bumps.py`) over every critical net finds it as the only
such bump that is not a corridor Z-route or a forced dogleg (the others: the radio lanes' E/N/E runs through the strip
openings, PYRO1_GATE_N's In2 Z, and a 3V3 B.Cu dent round C11.2 whose straight alternative comes 0.170 mm from C11.2).

**Nothing forces it.** Nothing lies inside the bump on F.Cu, and no length-matching intent exists (QSPI IO lengths on
R6: 27.64 / 26.96 / 33.91 / 24.70 mm, unmatched; M3_R5 l.176: "length matching alone is not a qualification").
`probe2.py`, straight segment (22.5, 40.3) → (22.5, 35.4), w 0.2: nearest U3.8 (3V3) 0.205 mm (the existing segment
(22.5, 35.4)–(22.5, 36.7) already passes U3.8 at the same 0.205 mm), GND via 0.400 mm, QSPI_CLK 0.510 mm; no power-zone
outline crossed. The same probe on the R6 board is also clear (QSPI_CLK 0.450 mm): the bump was already needless on R6.

**Experiment** (scratch only, `p6rq/mod_io3.py`: the five segments replaced by the one straight segment, native
`ZONE_FILLER` refill, saved to `p6rq/exp/m3.kicad_pcb`):
- `kicad-cli pcb drc --severity-all --schematic-parity`: **0 violations, 0 unconnected, 0 parity**.
- `route_check`: `0 failing, 33 allowlisted, 0 stale …, 30 leftovers recorded (0 unrecorded, 0 stale), 0 out-of-date
  route figures, 0 removable …: OK`; instance list identical to the final board's (312 → 312, none new or gone).
- `check_r7`: OK. `check_actuators`: OK.
- `critical_reference` final → experiment (extended): **0 lost**, 0 candidate-new.
- `scan5.py`: 501 → 499 (QSPI_IO3's two jogs gone), nothing new.
- QSPI_IO3 24.06 → **21.66 mm** (ratio 1.19 → 1.07), corners 6 → 2; GND F.Cu fill +1.88 mm².

**Records.** R7_VALIDATION "F. Outside the list" puts the pass-2 scan's 61 `chain_detour` instances "out of scope of
this list" because they "are not defects by M2's wording, and the M2 items among them (detours, …) are measured by
`route_check`". M2 lists "no needless detours" and assigns to review "detours … on nets with a pour … and pad-entry
tidiness on every net"; the gate's detour test is per net, so a local needless detour on a net under 1.6× is measured by
nothing. M2 also requires every review-only residual to be listed for the owner's acceptance. This one is neither
removed nor listed, so the owner's acceptance of the present list would not cover it.

**Severity.** Major by this review's calibration: messy routing on a critical net, the requirement (M2 "no needless
detours", whole board, inherited copper included) is not met for this instance, a gate-clean removal exists, and the
records misfile it. Electrical effect: none expected (about 2.4 mm ≈ 15 ps on a QSPI data line, In1 GND under the whole
bump); the finding is about the owner's routing criterion and the completeness of the deviation list, not function.

**Fix.** Add a stage to `r7_polish` that replaces the five segments by (22.5, 40.3) → (22.5, 35.4) (or redraw it in the
R6 inheritance step), rebuild and rerun the gate. Then correct part F: chain detours on critical nets are review items
under M2; state that the other 60 were judged (the radio Z-routes are covered by A/B detour entries or are under 1.6×
with measured strip constraints; PYRO1_CONT's U-turn at the divider goes round R130.2; ARM1_SENSE's is an L; USB_DM/DP's
are the USB-C A6/B6/A7/B7 crossover) or list any that remain.

### P6-ROUTING_QUALITY-02 (Minor): C5's per-line figure is the old two-end total

**Evidence.** R7_VALIDATION C5 (l.706) and M3_R7 l.503: "the 7 radio lines cross … at the U1 end … 3.1–3.8 mm over
BAT_IN per line". refscan (radio B.Cu length over In2 BAT_IN): pass-5 board BUSY 3.525, DIO1 3.533, MISO_MCU 3.819,
NRST 3.429, NSS 3.100 mm (both ends together), MOSI 1.657 / SCK 1.853 (band end) and MOSI_MCU 1.657 / SCK_MCU 1.753
(U1 end). Final board, U1 end only: **BUSY 1.862, DIO1 1.867, MISO_MCU 1.960, MOSI_MCU 1.657, NRST 1.564, NSS 1.500,
SCK_MCU 1.753 mm (12.16 mm total)**; the band-end nets MOSI and SCK 0. The 3.1–3.8 mm range is the P3-ROUTING_QUALITY-02
two-end figure carried into the one-end deviation.

**Impact.** Records only; the deviation is smaller than written.

**Fix.** C5 and M3_R7 l.503: "1.5–2.0 mm over BAT_IN per line (12.2 mm in all)".

### P6-ROUTING_QUALITY-03 (Minor): three record gaps on fix-pass-5 copper

1. **GND via beside NRST.** `mind.py`: GND via (35.85, 53.275) (fix pass 5, `gnd_pieces`) to NRST's via (35.8, 53.95):
   **0.177 mm** edge gap (both 0.5 mm; hole-to-hole 0.377 mm). M3_R7 "fix pass 5's copper" and C15 list this GND via
   only against 3V3A (0.176 mm). C15 says each listed short "is fail-safe or harmless"; an NRST–GND short holds the MCU in
   reset (the board does not boot), which bench bring-up and JLC's electrical test would catch but which is not one of
   the "reads no continuity / disarmed" cases (Inference).
2. **CAM_FAULT_N / SERVO4_MCU coupling.** Fix pass 5 straightened both In2 runs onto adjacent columns (x 15.19 and
   15.505). Length of CAM_FAULT_N within 0.2 mm (edge) of SERVO4_MCU: **6.9 mm → 30.4 mm** (within 0.5 mm: 22.9 → 36.2 mm);
   the records give only the gap (0.162–0.166). Probes: SERVO4_MCU cannot move east at the top (CAM_FAULT_N's via
   (16.044, 67.456): x 15.6 → gap 0.069 mm), CAM_FAULT_N cannot move west near y 93 (CAM_PWR_EN's via (14.65, 92.95)), so
   more spacing needs jogs again: a straightness-for-spacing trade worth stating. Electrical estimate (Inference): a
   3.3 V SERVO4_MCU edge through roughly 1–2 pF into CAM_FAULT_N (10 kΩ pull-up R76, about 15 pF) moves the high level by
   about 0.3 V, far from STM32 V_IH (0.7 × VDD); benign.
3. **NRST own-net stacking not listed.** NRST's B.Cu branch out of via (30.8, 53.1) still lies on its own In2 branch
   for about 1.5 mm ((30.8, 53.1)→(30.8, 52.3) over In2 (30.8, 53.1)→(30.8, 52.2); (30.8, 52.3)→(31.5, 51.6) 0.07 mm off
   In2 (31.3, 51.7)→(30.8, 52.2)). R7_VALIDATION mentions it only in the P5-RQ-03 row as an option not taken; it is not
   in parts A–D, which M2 requires for every review-only residual.

**Fix.** Add (1) to M3_R7 and C15 with the correct consequence; add the coupled length to the SERVO4_MCU – CAM_FAULT_N
entry; list (3) in part C or D (or start the B.Cu branch east of the via).

## 8. What is clean (checked on the final board)

- **Pyro nets:** PYRO1_CONT's new run is S/SE/S, every layer change ≤ 1.408 mm from a GND via, gaps to the pyro nets
  and SPI1 as §2; PYRO1_GATE_N / PYRO1_GATE / ARM1_SENSE tracks unchanged, ARM1_SENSE's two layer changes now 0.721 mm
  from GND vias; no reference loss.
- **SPI1 / IMU, SWD, HSE, USB data:** copper identical to pass 5; no reference loss (critical_reference 0/0); no new
  neighbour within 0.25 mm except recorded GND vias.
- **QSPI_CLK / RXEN:** forced 0.509 mm step recorded (C16); RXEN on its via column; their parallel gap opened to
  0.415 mm; QSPI_CLK fully In1-GND referenced (13.40 mm).
- **Radio band:** a regular fan-in (0.5 → 0.4 mm pitch, 0.1 mm per lane, steps aligned within 0.6 mm) and nested
  corner chamfers; band-end split crossings gone; the two remaining fan-in steps allowlisted with `alt_audit`.
- **Camera UART wires:** In1 free of signal copper; TX straight on F.Cu to one via; RX's In2 step forced by
  BAT_SW_RETURN (probe).
- **Power feeds:** USB_LIMITED square T at U11.7; VLOGIC runs end at the U2 pad centres; RAW_ACT's tail 0.5 mm
  inside its fill; 3V3_RADIO one 45° run through FB31.2. Power pours unchanged in piece count; BAT_IN In2 one piece.
  DC (`tools/dc_solve.py`, board stack-up, 0.1 mm grid), re-run here: BAT_IN J1:1 → Q120:5–9 **4.58 mΩ** (35.2 mV,
  0.271 W at 7.7 A; In2 100 % at mid-path, peak 6.17 A/mm), as the handoff states. The handoff's RAW_ACT 3.95 mΩ and
  BAT_IN J1 → U9 15.18 mΩ were still solving when this report was written (shared CPU) and are quoted, not
  re-measured here.
- **Not raised (inherited, harmless):** a 0.5 mm² RAW_ACT F.Cu fill fragment (11.46–12.86, 81.2–81.6) round the via
  (12.6, 81.27), byte-identical on R6, below `pour_sliver`'s 3 mm length threshold; the threshold-tuned shapes
  (0.509 mm steps, 1.004 mm chamfers) are recorded honestly in C16 / M3_R7, and P5-RQ-04's optional offset-only jog test
  remains not done (recorded).

## 9. Scripts and outputs (scratch, not in the repository)

`<scratch>/p6rq/`:
`r7.kicad_pcb` (`1ffc2585…`), `p5.kicad_pcb` (`c6fe595c…`), `r6.kicad_pcb`; dumps `r7.json`, `p5.json`, `r6.json`;
`check.log` (gate); `diff_p5_r7.txt`; `route_r7.json/.txt`, `route_p5.json`, `routes_r7.txt`, `routes_p5.txt`;
`scan5_r7.json`, `scan5_p5.json`, `scan2_r7.json`, `scan2_p5.json`; `refscan_all.py`, `ref_r7.json`, `ref_p5.json`,
`refcmp_p5_r7.txt`; `cref_p5_r7_ext.json`, `cref_r6_r7.json`, `cref_r6_r7_ext.json`; `newnbr.py`, `newnbr.txt`;
`bumps.py`; `q.py`; `zarea.py`; `probe2.py`, `mind.py` (pass-5 copies); experiment `mod_io3.py`, `exp/` (board,
`drc.json`, `route.json`, `r7.json`, `scan5.json`); renders `img/*.png`.
