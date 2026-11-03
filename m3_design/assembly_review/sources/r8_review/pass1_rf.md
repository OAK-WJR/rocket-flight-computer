# R8 pass 1: RF layout, interface buses and coexistence review

Independent read-only review, 2026-10-19, of `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
`429b6db4dc95c1a0fd3e736625c416c20fa0e7fc72f6f6c9c576003340dc1987` (checked before and after this review, unchanged;
`git status` unchanged). Dimension: RF (REQUIREMENTS F10, the RF parts of M1/M2 and P3, the rigid strip and its
hashes, the new U1-to-strip interface buses, F10's 5 mm separation, GND vias at layer changes, the fence, coexistence
paths and the reset states of the radio and GNSS lines). Vehicle-level choices and firmware are out of scope. The R7
board (`git show 431025d:…/m3.kicad_pcb`, `c872a3d3…`) was used for every before/after comparison.

Coordinates: KiCad mm, y = 0 at the aft (SMA) edge.

## 1. Summary

**No Critical. No Major. Four Minor (R8P1-RF-01 to R8P1-RF-04).**

The RF strip is R7's where it matters, and the new buses are clean:
- `check_r8`'s 12 rigid digests equal R7's. An independent item diff of everything with y < 23.5 against R7, and a fill
  XOR, show that the RF lines, the strip parts, the strip GND vias, the GCPW coplanar ground and the GND under both
  module bodies on all four layers are identical to R7 (section 3.1).
- All 12 radio and GNSS interface nets run from U1 to the strip on F.Cu over solid In1 GND, with no via. The only layer
  changes on RF-family nets are R7's TXEN loop and the limiter's three vias, each with a GND via within 1.5 mm.
- The fence has 25 vias. All 14 crossing lanes are on F.Cu, in gaps of 1.20–2.60 mm. F10's 5 mm separation holds
  (nearest 5.94 mm to a part, 5.075 mm to a fast line). Every reset and bootloader state holds the radio in reset.

The four Minors:
- **R8P1-RF-01:** an unstitched GND finger runs in the new radio bus between RADIO_NSS and RADIO_SCK. It is 0.535 mm
  wide and its tip is 15.06 mm of copper from a GND via. `pour_finger` gates only fingers under 0.5 mm, so it misses
  this one by 0.035 mm.
- **R8P1-RF-02:** the R7 pass-4 RF dispositions are not carried into the R8 record. These are P4-RF-01 (R7 deviation
  C11), P4-RF-02 (now partly closed by `strip_gcpw`) and the D30.2 / D31.2 solid-ground decision (R7 C13). Neither
  R8_VALIDATION nor the R8 deviation list mentions them.
- **R8P1-RF-03:** ORDERING §5's RF bench step checks "PD9 high-impedance" for the radio-in-reset test. PD9 is
  RADIO_RXEN in R8; RADIO_NRST is on PE9.
- **R8P1-RF-04:** R8 moved the camera supply from the forward end to 13.5 mm from U31 and 24.8 mm from U30. The
  coexistence bench step never runs the GNSS with the camera supply on.

## 2. Previous pass in this dimension: closure

R7's last RF pass was pass 4 (`sources/r7_review/pass4_rf.md`); passes 5–8 had no RF reviewer. Its three findings:

| R7 finding | R7 disposition (R7_VALIDATION) | On R8 `429b6db4…` |
|---|---|---|
| P4-RF-01 (Minor): unstitched GND fingers 0.5–1.0 mm wide outside the gate | Not done; recorded as R7 deviation C11 (23 pieces under 0.75 mm, 48 under 1.0 mm by the records' method; worst 10.7 mm of copper from a via) | **Open, not re-dispositioned.** R8's copper outside the strip is all new. The same scan (`route_check.pour_pieces`, relief rings excluded, at `FINGER_W` 0.75 / 1.0 mm) finds 7 / 15 pieces; R7 by that method gives 13 / 37. So R8 is better. One of the 7 lies in the radio bus (R8P1-RF-01). R8_VALIDATION has no C11-type row (R8P1-RF-02) |
| P4-RF-02 (Minor): no gate pins the GCPW's coplanar ground, F.Cu under the modules, or where a pour trim lands | Not done (tools); recorded open | **Closed in part, not recorded.** `check_r8.strip_gcpw` hashes the F.Cu GND gap profile beside all 8 RF tracks against R7's (equal), so a trim or track that removed coplanar ground would now fail the gate. Still ungated: F.Cu GND under both module bodies (`module_ground` checks U31 In1 / In2 and U30 In1 only), and where a trim lands. R8 trim G5 lies 0.489 mm² inside U31's courtyard, between pads 13 and 14 and outside the body. Measured today: F.Cu GND under U31 79.77 mm², under U30 75.68 mm², both equal to R7. No R8 record mentions P4-RF-02 (R8P1-RF-02) |
| P4-RF-03 (Minor): C302 relief, D30 / D31 / C302 seating step | Fixed: C302.2 relief; D30.2 / D31.2 solid by decision (R7 C13); ORDERING first-article step | **Closed on the copper** (`strip_parts` digest equal; `thermal_policy` and `rf_grounds` OK; ORDERING §5 l. 139 keeps the seating inspection). R7's C13 deviation has no R8 counterpart (R8P1-RF-02) |

## 3. Measurements on the final board

### 3.1 Rigid strip and its hashes

- `tools/check.sh` exit 0 (run in this review): DRC 0, unconnected 0, parity 0, ERC 0; `check_r8` OK; route_check r8 0
  failing / 3 allowlisted; actuators OK; fit OK. `test_r8_check.py`: 20 tests OK.
- `check_r8` evidence:
  - rigid: 12 / 12 digests equal R7's (`strip_parts` 22, `strip_rf_copper` 11, `strip_gnd` 176, `strip_rule_areas` 5,
    `strip_gcpw` 8 items);
  - line stitching: GNSS west 3.90, east 2.65, radio 1.55 / 1.55 mm; In1 missing under RF copper 0.0 mm²;
  - launches: In2 1025 / 1025 samples each;
  - module ground: U31 In1 / In2 2601 / 2601, U30 In1 1976 / 1976;
  - RF ground vias 0.16 mm from all six RF GND pads;
  - strip GND reach F.Cu 3.04, B.Cu 3.49 mm.
- **Independent item diff, y < 23.5, R7 → R8** (`stripdiff.py`; tracks, vias, footprints with pad nets and zone
  connections, zones). 88 items removed and 88 added, every one of them in these classes:
  - **fence row:** 21 vias (0.6 / 0.3 mm) replaced by 25 (0.5 / 0.3 mm) on y 23.3;
  - **interface leads:** BUSY, MISO, MOSI, NSS, SCK, RXEN, NRST and DIO1, and the GNSS TXD / RXD / TIMEPULSE /
    RESET_N / TP leads, redrawn at 0.2 mm (R7: 0.15 mm), all on F.Cu. NSS's B.Cu hop and two vias and DIO1's B.Cu hop
    and via are gone (D4);
  - **limiter DC copper (D11 / D51):** the GNSS_LNA_EN and GNSS_VCC_RF vias moved from y 8.3 to 8.9 (0.6 → 0.5 mm),
    LNA_EN's B.Cu path redrawn, and a 0.03 mm end shift on GNSS_ANT_SRC;
  - **parts:** R310 left the strip (now on 3V3 at (24.1, 29.5), D4); C300 moved 0.08 mm, R305 0.13 mm and R312 0.25 mm;
  - **feeds:** the 3V3_RADIO run along y 21.6 that R7's R310 needed is gone; FB31's 3V3 stub is 0.2 mm shorter;
  - **zones:** `R7_GND_In2_strip` replaced by `R8_GND_In2`; `R7_POUR_TRIM_9` replaced by `R8_POUR_TRIM_G5`.

  No RF track, RF-chain part, strip GND via (fence row excepted), keep-out or launch cut-out differs.
- **Fill XOR, R7 → R8, GND per layer** (`fillxor.py`):

  | Region | F.Cu | In1 | In2 | B.Cu |
  |---|---|---|---|---|
  | U31 body (24.86–34.86, 9–19) | 79.77 = 79.77 mm² | 100.00 = | 100.00 = | 100.00 = |
  | U30 body (5.56–15.26, 9.9–20) | 75.68 = | 97.97 = | 97.97 = | 77.12 → 77.14 (limiter path) |
  | Radio line zone (28–36, 0–10) | 55.17 = | 67.82 = | 75.20 (−0.001) | 75.39 = |
  | GNSS line zone (10–17, 0–11) | +0.83 | +0.28 | +0.27 | +0.51 |

  The GNSS-zone changes are the two limiter vias' antipads moving 0.6 mm forward. They are 2.2 mm from GNSS_RF_IN;
  In1 under every RF track and pad + 0.3 mm stays complete, and the GCPW profile digest is unchanged.

### 3.2 Interface buses U1 → strip

`dump_rf.py`, `iface.py`, `cross.py`, `aggr.py`:

| Net | Copper | Vias | Termination |
|---|---|---|---|
| RADIO_SCK_MCU / RADIO_SCK | 15.73 + 13.19 mm, F.Cu | 0 | R313 33 Ω at the MCU end (driver) |
| RADIO_MOSI_MCU / RADIO_MOSI | 9.76 + 17.15 mm | 0 | R315 at the MCU end (driver) |
| RADIO_MISO / RADIO_MISO_MCU | 1.48 + 27.90 mm | 0 | R314 at U31 (driver) |
| RADIO_NSS | 32.21 mm | 0 | R310 100 kΩ to 3V3, a 0.9 mm T at (24.1, 29.93) |
| RADIO_BUSY / RXEN / DIO1 / NRST | 32.01 / 40.02 / 25.04 / 41.04 mm | 0 | R312 / R311 at the radio |
| GNSS_TXD / GNSS_TXD_MCU | 2.19 + 26.87 mm | 0 | R305 220 Ω at U30 (driver) |
| GNSS_RXD_MCU / GNSS_RXD | 9.16 + 19.36 mm | 0 | R306 220 Ω at the MCU end (driver) |
| GNSS_TP_MCU / GNSS_TIMEPULSE | 25.97 + 2.45 mm | 0 | R307 1 kΩ at U30 |
| GNSS_RESET_N | 23.89 mm | 0 | none (open drain) |
| RADIO_TXEN (R7's loop, unchanged) | 25.17 mm, F.Cu + B.Cu | 2 | — |

- **Reference:** In1 GND lies under every F.Cu interface track (centre and ±0.2 mm, every 0.05 mm). It is missing only:
  - inside the limiter / TXEN via antipads;
  - inside the launch cut-outs (by design);
  - for 33 samples at the +0.2 mm edge of RADIO_NRST at (33.6, 44.25–44.4), where CAM_MCU_RX's via (33.9, 44.0)
    antipad reaches about 0.05 mm under the lane's edge.

  In2 GND lies under the limiter's B.Cu tracks.
- **Aggressor proximity** (plan view, every layer, < 1.5 mm): the only close neighbours are U1's pin pitch, where
  QSPI_IO0 / IO1 / IO3 (pins 58–60) sit between the radio pins (53–56) and the GNSS pins (61–64) at 0.25–1.45 mm.
  - CAM_MCU_RX crosses RADIO_NRST at (31.85, 45.5), on B.Cu under F.Cu, with In1 and In2 GND between them.
  - USB_DM passes 1.38 mm from GNSS_TXD_MCU.
  - No switch node, crystal or SWD copper comes within 1.5 mm of an interface lane.
- **Safety nets:** the nearest pyro, arming or RAW_ACT copper to any radio or GNSS copper is RAW_ACT_SENSE_MCU, 2.15 mm
  from RADIO_NRST at U1's east face. No pyro gate, bus or igniter copper lies within 6 mm.

### 3.3 F10 5 mm separation

`check_r8.rf_separation` re-run, and an extra scan of every part on the camera supply nets (`sep.py`):
- **Parts:** the nearest restricted part is U1, 5.94 mm from R306 (R310 / R313 / R315: 6.04 mm). Then come U7–FB31 6.66,
  C73–C310 7.86 and U7–U31 9.41 mm.
- **Fast lines:** the nearest is USB_DM at (13.4, 35.64), 5.075 mm from R306; R315 is 5.82 mm from USB_DM.
- **Buck capacitors:** the camera buck's input capacitors C72 / C73 / TP71 are 7.86–11.84 mm from any RF part. The parts
  2.15–4.83 mm from FB31 / R313 are the eFuse U7's DC network (TP70, R75, C71, C70, R74, R70). None of them is a
  switching part, so none is restricted (D17).
- **Bucks:** the logic buck is ≥ 43 mm from both modules (U2–U31 45.06, U2–U30 47.77 mm). R7's nearest buck parts were
  7.19–11.97 mm away.

### 3.4 GND vias at layer changes (critical RF-family nets)

| Via | Nearest GND via, centre to centre | R7 |
|---|---|---|
| GNSS_ANT_DC (11.45, 5.15) | 1.011 mm | 1.011 |
| RADIO_TXEN (31.13, 20.15) | 0.721 | 0.721 |
| RADIO_TXEN (28.59, 7.80) | 0.721 | 0.721 |
| GNSS_LNA_EN (11.51, 8.90) | 1.253 | 1.100 (at y 8.3) |
| GNSS_VCC_RF (10.41, 8.90) | **1.4996** (9.025, 8.325) | 1.221 (at y 8.3) |

All are within AGENTS §3's 1.5 mm. The VCC_RF via meets it with 0.4 µm to spare (an observation, not a finding: the build
is byte-reproducible, and the net carries DC bias). The interface buses have no layer change. The 3V3 feed vias have
GND vias at 1.10 mm (FB30's, (12.33, 24.4)) and 1.30 mm (FB31's, (35.1, 24.4)). R310's 3V3 via (24.1, 28.45) is
1.95 mm from one; it is a via-to-pour joint carrying microamps, outside AGENTS §3's scope.

### 3.5 Fence and crossings

- **Vias:** 25 GND vias on y 23.3 at x 0.9, 2.9, 4.9, 6.4, 7.685, 9.7, 12.3, 14.2, 16.2, 18.2, 20.0, 22.1, 24.15, 26.0,
  28.0, 30.0, 31.8, 33.0, 34.4, 35.8, 37.8, 39.4, 40.6, 42.6, 44.6. The edges are 0.9 and 1.4 mm away.
- **Openings over 2.0 mm** (D16 limit 2.7 mm): 7.685–9.70 (GNSS_RXD, GNSS_TP_MCU), 9.70–12.30 (3V3_GNSS),
  20.00–22.10 (RXEN, BUSY, MISO_MCU) and 22.10–24.15 (MOSI, NSS). R7 had 6.10 and 3.80 mm openings.
- **Crossings:** all 14 non-GND crossings of y 23.3 are on F.Cu: the 12 interface lanes, 3V3 to FB31, and 3V3_GNSS.
  Single-lane gaps are 1.20–2.00 mm (NRST and DIO1 1.20, 3V3 1.40, TXD_MCU 1.285, SCK 1.85, RESET_N 2.00 mm). Edge
  clearances to the fence-via rings are ≥ 0.15 mm (DRC-legal).
- **Planes:** no In1, In2 or B.Cu track crosses the fence. The In2 3V3 region starts at y 24.0, forward of F10's strip
  (y ≤ 23.5).
- **GND reach through copper** (`band_reach.py`):

  | Region | F.Cu | B.Cu | In1 | In2 | R7 (pass 4) |
  |---|---|---|---|---|---|
  | strip | 3.04 | 3.49 | 3.49 | 3.49 mm | 3.14 / 3.49 |
  | band y 23.5–28.5 | 5.20 | 6.06 | 3.17 | 3.02 | 17.21 / 6.22 |
  | bus y 28.5–45 | **15.06** at (31.98, 38.58), R8P1-RF-01 | 11.63 at (30.33, 37.08) | 4.59 | 4.08 | — |

### 3.6 Coexistence paths

- **Unchanged from R7** (rigid):
  - the RF lines are 15.45 mm apart, the jacks 18.69 mm and the module courtyards 7.66 mm;
  - each module has its own ferrite (FB30 / FB31) and local bulk capacitance.

  Isolation stays the F10 bench figure.
- **Supply:** both ferrites are fed from the In2 3V3 region by one via each, 22.8 mm apart (R7 fed them from 3V3 too).
- **Radio lines near U30** (body box of 10.1 mm across x): RXEN 5.44 mm, BUSY 5.94, MISO_MCU 6.44 mm. DIO1 and NRST,
  4.9 / 5.6 mm from U30 in R7, now run east of U31. These are the quasi-static lines R7 pass 2 §3.10 accepted. SCK is
  ≥ 9 mm from U30 and its parts.
- **Aggressors moved by R8** (R8P1-RF-04):
  - the camera supply U7 / U8 / L3 moved from y 87–100 to y 30.7–40.8: U8 is 13.49 mm from U31 and 24.81 mm from U30;
  - the MCU moved: U1 is 15.06 mm from U30 and Y1 25.37 mm (Y1 R7 (25.6, 53.75), R8 (22.85, 48.6));
  - the logic buck moved to the far end (≥ 43 mm).

  F10's 5 mm rule is met everywhere.

### 3.7 Reset and bootloader states of the radio and GNSS lines

The netlist (`schematic.net.xml`) matches F10 and D2 exactly:

| Line | Part | MCU in reset or in the ROM bootloader |
|---|---|---|
| RADIO_NRST (PE9) | R311 2 kΩ to GND | Low: SX1262 held in reset, cannot transmit. PE9 is not a bootloader pin (pin_table, AN2606 Table 135 as cited) |
| RADIO_RXEN (PD9) | R312 100 kΩ to GND | Low |
| RADIO_NSS (PB11) | R310 100 kΩ to 3V3 | High: SX1262 deselected, so USART3_RX idles high and USART3 is never detected (D2) |
| RADIO_SCK / MOSI (PB10 / PB14) | — | May be driven by the loader into SX1262 inputs held in reset; no contention (D2) |
| RADIO_MISO (PB15) | — | Pulled up by the loader; SX1262 MISO high-Z |
| RADIO_BUSY, DIO1 | — | SX1262 outputs into high-Z inputs |
| RADIO_TXEN | U31.19 DIO2 ↔ U31.9 | Module-internal; no TX while in reset |
| GNSS_RESET_N (PD14) | none (open drain, no capacitor) | GNSS runs on its internal pull-up |
| GNSS_TP_MCU (PD15) | R307 1 kΩ series, no pull-down | GNSS output into a high-Z input |
| GNSS_RXD_MCU / TXD_MCU (PC6 / PC7) | R306 / R305 220 Ω | Not bootloader pins |

- No radio or GNSS line is on PA13 / PA14 / PA15 / PB3 / PB4, the pins with reset-time pulls.
- No RF-part pin is on a safety net (`check_r8` contract OK; R310 joins RADIO_NSS and 3V3).
- **R310's position:** R310 sits at the electrical midpoint of the NSS lane (16.1 mm from the U1 pin, 16.1 mm from
  U31.14). It is nearer U1's centre than U31's by 1.0 mm, so `check_r8.PULL_END` passes. Where a 100 kΩ pull-up sits
  makes no electrical difference (observation only).

## 4. Findings

| ID | Sev. | Requirement | Finding | Evidence | Fix |
|---|---|---|---|---|---|
| R8P1-RF-01 | Minor (worth fixing) | M2: "unstitched GND pour fingers" (gate below 0.5 mm, review beyond); u-blox MAX-F10S IM §4.4 ("stubs at the ground planes must be avoided or ended with a via") as general guidance | **An unstitched F.Cu GND finger runs in the new radio bus.** It sits between the RADIO_NSS diagonal ((31.65, 38.72)–(23.2, 30.27)) and the RADIO_SCK diagonal ((32.25, 37.85)–(25.1, 30.7)), which are 1.04 mm apart.<ul><li>It is 0.535 mm wide, so `route_check.pour_finger` (FINGER_W 0.5 mm) misses it by 0.035 mm.</li><li>It is about 11 mm long, from R310 / R313 to U1's east face.</li><li>Its tip (31.98, 38.58) is 15.06 mm of copper from the nearest GND via. It belongs to the fill piece that holds the vias (24.15, 26.5), (24.15, 23.3) and (23.8, 17.7).</li><li>RF effect negligible (Inference): about λ/4 at 3 GHz, 0.2 mm over In1. It is new R8 copper, not inherited.</li></ul> | `fingers.py` (route_check.pour_pieces at FINGER_W 0.75): F.Cu (23.76, 27.83)–(32.00, 38.60), len 13.56. `finger_poly.py`: piece bbox (23.45, 15.52)–(32.00, 38.60), 20.25 mm²; perpendicular width 0.535 mm at (25.0, 31.34), (28.0, 34.34) and (31.0, 37.34). `band_reach.py`: F.Cu worst in y 28.5–45 is 15.06 mm at (31.98, 38.58). | Remove it in the generator: add a fill-only F.Cu trim row (G7, outline on the NSS / SCK centre lines from R310 / R313 to U1, as D65 does for G1–G6), or close the NSS–SCK diagonal pitch to the bus's 0.5–0.6 mm so no fill forms. Re-run `pour_finger` and the strip / bus reach. |
| R8P1-RF-02 | Minor (worth fixing) | M2 (every review-only residual listed for the owner, bound to the board; R7's acceptance does not carry over); r8_plan §4 (close the previous pass); AGENTS §3 STATUS rule | **R7's open RF dispositions are missing from the R8 record.**<ul><li>R8_VALIDATION and the R8 deviation list (C1–C10) do not mention P4-RF-01, P4-RF-02, or R7 deviations C11 and C13.</li><li>(a) Unstitched GND pieces 0.5–1.0 mm wide (R7 C11) still exist on R8: 7 under 0.75 mm and 15 under 1.0 mm. The worst are In1 (0.50–1.62, 92.05–107.56), F.Cu (19.82–43.37, 98.66–99.51) and R8P1-RF-01's finger.</li><li>(b) P4-RF-02 is partly closed by `strip_gcpw`, but nothing records that. F.Cu GND under the module bodies and where a trim lands are still ungated: G5 covers 0.489 mm² of U31's courtyard, outside the body.</li><li>(c) D30.2 and D31.2 are still solid to the pour (R7 C13, the house relief rule's RF exception): unchanged, since they are rigid.</li></ul> | `fingers.py`: W < 0.5: 0; W < 0.75: 7; W < 1.0: 15 (R7 by the same method: 13 / 37). `g5.py`: G5 bbox (22.60, 14.00)–(24.40, 15.67), 0.489 mm² in U31's courtyard (23.965–35.755, 8.105–19.895). `fillxor.py`: F.Cu GND under U31 79.77 mm² and under U30 75.68 mm², both = R7. `grep P4-RF docs/R8_VALIDATION.md docs/M3_R8.md R8_DECISIONS.md`: no hit. | Add a short "R7 pass-4 RF items on R8" note to R8_VALIDATION: P4-RF-01 open, with the counts above; P4-RF-02 closed in part by `strip_gcpw`; P4-RF-03 closed. Add C11- and C13-type rows to the R8 deviation list, with the measured pieces and the D30 / D31 reason. Optionally add F.Cu (both bodies) and B.Cu (U31) to `check_r8`'s module-ground check, with R7's coverage as the floor. |
| R8P1-RF-03 | Minor (worth fixing) | F10 (radio held in reset by hardware); AGENTS §3 (records match the board); ORDERING is R8's | **The radio-in-reset bench step probes the wrong pin.** ORDERING §5 l. 161 says: "With the radio held in reset by hardware: PD9 high-impedance (blank or reset MCU), RADIO_NRST reads below 0.66 V". In R8, PD9 (U1.56) is RADIO_RXEN and RADIO_NRST is on PE9 (U1.39). The text is R7's pin, so a technician would confirm the wrong pin. | `docs/ORDERING.md` l. 161; `pin_table.tsv` rows 39 (PE9 RADIO_NRST) and 56 (PD9 RADIO_RXEN); `schematic.net.xml`: RADIO_NRST = R311.1, U1.39, U31.3; RADIO_RXEN = R312.1, U1.56, U31.10. | Change it to "PE9 (U1.39) high-impedance …; RADIO_NRST at R311.1 below 0.66 V". Optionally also check RADIO_RXEN low (R312). |
| R8P1-RF-04 | Minor (worth fixing) | F10 (coexistence shown on the bench; GPS used for tracking in flight, with the camera on) | **The coexistence bench step does not cover R8's relocated aggressors.**<ul><li>R8 moved the camera supply (U7 eFuse, U8 buck, L3) from y 87–100 to y 30.7–40.8. The camera buck is now the nearest switching regulator to both modules: 13.49 mm from U31 and 24.81 mm from U30.</li><li>It also brought U1 and Y1 nearer the strip (U30–U1 15.06 mm, U30–Y1 25.37 mm).</li><li>ORDERING §5 logs GNSS C/N0 only with the radio keyed (and repeated with the buzzer). No step runs the GNSS with the camera supply on or with the MCU at flight load.</li><li>F10's 5 mm rule is met, and R8 is farther from the logic buck than R7 (≥ 43 mm). The concern is verification coverage, not layout.</li><li>25 MHz × 63 = 1575.000 MHz, 0.42 MHz from GPS L1 (1575.42 MHz). Whether HSE harmonics matter here is an Inference that only this test settles.</li></ul> | `sep.py` and `check_r8.rf_separation` evidence; M3_R8 §RF table; ORDERING §5 l. 164 ("Coexistence: radio keyed … Repeat with the buzzer sounding"); R7 positions from `431025d` (U7 / U8 / L3 at y 87–100; Y1 (25.6, 53.75)). | Extend the ORDERING §5 coexistence step. Log C/N0 first with the radio idle, MCU at its flight clock, QSPI logging and the camera powered (CAM_PWR_EN high, camera drawing current), then with the radio keyed and the camera on. Record the C/N0 deltas against camera-off. |

## 5. Inferences (not measured, or not from a primary source)

- **R8P1-RF-01:** the quarter-wave estimate (≈ 3 GHz for about 15 mm of copper, εeff ≈ 3) and its negligible coupling
  were not modelled.
- **R8P1-RF-04:** the 25 MHz harmonic is arithmetic; its level at U30 is unknown. The buck and camera effect on C/N0 is
  not modelled.
- **AN2606 and DS12110 reset and loader states:** taken from `pin_table.tsv` and R8_DECISIONS D2 / D5, which cite AN2606
  Table 135 (pp. 320–323) and DS12110 §3.8 / Table 8. Not re-read for this review.
- **Isolation and pyro immunity:** bench items (F10). No board path between the chains changed, so pass 2's figures
  carry over unrecomputed.

## 6. Sources

- **u-blox MAX-F10S integration manual** UBXDOC-963802114-12892 R01, §4.4 "Layout" (ground under the module on the top
  two layers; ground stubs avoided or ended with a via):
  https://content.u-blox.com/sites/default/files/documents/MAX-F10S_IntegrationManual_UBXDOC-963802114-12892.pdf
- **EBYTE E22-900MM22S user manual** (via LCSC), §4.1 (no wiring under the module, top layer grounded); pin table (pin 9
  TXEN, pin 19 DIO2): https://datasheet.lcsc.com/datasheet/pdf/70331b0eaf0eedaea0129e9e66d9a011.pdf?productCode=C5333985
- **Project:**
  - `docs/REQUIREMENTS.md` F10, M2;
  - `docs/M3_R8.md` §RF, §Ground; `docs/R8_VALIDATION.md`; `docs/ORDERING.md` §5;
  - R8_DECISIONS D2, D4–D6, D11, D15–D17, D51, D65–D67; `pin_table.tsv`;
  - `tools/check_r8.py` (`rf_strip`, `fence`, `rf_line_stitching`, `rf_separation`, `gcpw_profile`, `rigid_groups`);
  - `tools/check_r7.py` (`RF_PART`, `STRIP_*`, `MODULE_GND`); `tools/route_check.py` (`pour_pieces`, `gnd_reach`,
    `critical_transitions`);
  - `sources/r7_review/pass4_rf.md`; `docs/R7_VALIDATION.md` (P4-RF rows, C11, C13).

## 7. Method (reproduction)

Every script ran under KiCad 10.0.6's Python (`PYTHONDONTWRITEBYTECODE=1`, `-I`) against the repository board read-only,
and against `git show 431025d:m3_design/assembly_review/m3.kicad_pcb` copied into the session scratchpad (`p1rf/`,
deleted afterwards). Nothing in the repository was written except this report.

- **Gate:** `KICAD_CLI=… tools/check.sh` exit 0; `tools/test_r8_check.py` 20 OK.
- **`stripdiff.py`:** sets of tracks (net, layer, sorted ends, width), vias, footprints (position, rotation, side, pad
  nets and zone connections) and zones for y < 23.5, on R7 and R8.
- **`fillxor.py`:** GND fill per layer, intersected with each region, R7 minus R8 and R8 minus R7.
- **`dump_rf.py` / `iface.py` / `viaexact.py`:**
  - every RADIO_ / GNSS_ / 3V3_RADIO / 3V3_GNSS track and via;
  - In1 or In2 GND point tests along every interface track (centre and ±0.2 mm every 0.05 mm);
  - nearest GND via at each RF-family via.
- **`cross.py`:** fence vias at y 23.3 ± 0.06 and every non-GND track crossing y 23.3.
- **`aggr.py` / `safety.py`:** edge-to-edge distance by binary search on `SHAPE.Collide`, from interface copper to fast,
  servo, pyro and camera nets (< 1.5 mm listed), and from safety nets to RF copper.
- **`sep.py`:** `check_r8.courtyard` / `min_gap` from every camera-supply part to every RF part.
- **`fingers.py`:** `route_check.pour_pieces` with FINGER_W set to 0.5, 0.75 and 1.0 mm (relief rings excluded, as the
  gate does), on R8 and R7.
- **`finger_poly.py`:** the GND fill piece containing (28.0, 34.336), its vias and perpendicular widths.
- **`band_reach.py`:** `route_check.gnd_reach` over x 0–46, y −1–75, limit 60 mm, per layer and region.
- **`g5.py`:** R8 trims against U31's F.CrtYd.
- **Netlist:** `schematic.net.xml` nodes of every radio, GNSS, NRST and BOOT0 net.
