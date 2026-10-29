# R8 review pass 3: planes and return paths

Reviewer: independent, dimension "planes and return paths". Board `m3_design/assembly_review/m3.kicad_pcb`, SHA-256
`990c8040c5b8457bd2bd1717ed3e5c2725f32c1dda1cd7f826a0c2b458d28b18`. I hashed it before and after the review, and it is
unchanged. `git status --short` is also unchanged by my runs. Read-only: I edited nothing in the repository except this
file. Every pcbnew edit below (one via removed, a zone refill) was made in memory on a loaded copy and never saved.

## Verdict

**0 Critical, 0 Major, 2 Minor (both records).**

All three pass-2 findings in this dimension are closed or properly dispositioned. Fix pass 2 caused no plane regression.
I diffed the copper and fills against the pass-2 board `6600ef94…`, taken from fix pass 2's own pre-fix archive
(`fix2/pre_fix2_state.tgz`, hash checked). Every plane change is one of the intended ones:
- the In2 BAT_IN cut-back (D97);
- the U9.8 pad via (D102);
- J123.2's relief, with its island via (D101);
- R81's move and the regenerated grid vias next to it (D100);
- C83.2's link (D99);
- four vias shrunk from 0.6 to 0.5 mm (D98).

The two Minor items:

1. **(Worth fixing, records.)** The "candidate for pass 3" that fix pass 2 recorded is aimed at the wrong copper. It is
   step 7's tented GND via (15.0, 107.3), 0.180 mm from bare R120.2 (ACT_GATE).
   - Masked GND pour is already closer than that via to five bare actuator-gate pads:
     - B.Cu: 0.150 mm from R120.2 and C120.2 (ACT_GATE);
     - F.Cu: 0.150 mm from Q122.3 and R121.2 (ACT_DRV) and from R121.1 (ACT_GATE).
   - So moving the via, as the open item proposes, changes nothing. I found that a legal spot exists at (15.0, 108.1), so
     the move is possible, but it gains nothing.
   - The records (pyro observations, C12b #19, "Open after fix pass 2") should state the pour figure and close the item.
     Alternatively they can name the real lever, a fill clearance from GND to ACT_GATE / ACT_DRV, as an owner choice.
2. **(Worth fixing, records.)** R8_VALIDATION's P3b scorecard row names only three of the four In1 slots. It leaves out
   the SPI1 / IMU_CS via cluster, which M3_R8 "Ground" does name.
   - The row also says "no critical track crosses them". For the cluster that is not quite true: SPI1_SCK's F.Cu edge
     passes over it (34 edge samples, already counted in the reference audit's 226 "other via" samples).

## Gates and tools run (on `990c8040…`)

| Run | Result |
|---|---|
| `tools/check.sh` | **exit 0**: DRC 0, unconnected 0, parity 0, ERC 0; metadata / 3D OK; silk OK; R8 contract OK; route_check r8 0 failing, 3 allowlisted, 0 stale, 0 leftovers, 0 removable; check_actuators OK; fit OK |
| `m3_design/r8_ground_check.py --report` | **all 14 gates OK**. Reach: board p95 4.47 / max 9.65 mm at (0.25, 88.25); pours p95 2.90 / max 5.89 mm. Islands: **21**; the one weak island is D4.2's (F, 2.891 mm², 1 via) |
| `tools/reference_audit.py` (R6 set / extended) | 46,845 / 5,186 (11.07 %): own via 3,592, keep-out 1,368, other via 226. Extended: 102,384 / 5,944 (5.81 %). **Equal to M3_R8 "Return paths" and to pass 2** |
| `NO_GATE=1 NO_DC=1 tools/run_survey.sh` | P1 0.905 (gnd_coverage 0.905 at 4 decimals, In1 4,861.7 mm²), P2 1, P3 16, P3b 4, P4 5, P6 1752.5 mm, P7 1, P8 8.15 / cm², P9 / P10 4.47 / 9.65 mm, P11 2.90 mm, R1 / R3 2.9 / 2.9 mm, R6b 0.1107, S12 25, C6 1. **Equal to R8_VALIDATION's scorecard** |
| `tools/test_reference_audit.py` | 3 tests OK |
| Own scripts (pcbnew, read-only, listed at the end) | zone inventory; islands with their vias; full critical-net sampling with split crossings; B.Cu split crossings and foreign antipads on every net; In1 holes and slots; In2 and In1 erosion; finger pieces at 0.75 / 1.0 mm; GND-pad copper reach; copper and fill diffs against `6600ef94…`; buck input-loop copper paths; clearances of the new vias; GND copper near the actuator-gate pads; an in-memory `make_ground.legal()` trial |

## 1. Pass-2 findings in this dimension

| Pass-2 item | Status on `990c8040…` | Evidence |
|---|---|---|
| R8P2-PLANES-01: U9's GND terminal was 14.1 mm of copper from a via | **Closed** | The via is `r8_ground.tsv` line 203, `pad U9.8`: GND, 0.5 / 0.3 mm, at (44.65, 86.775). It has GND on In2, which is GND there since D97, and on In1. It joins the B.Cu island of U9.8, R84.2 and C81.2. Its clearances: 0.176 mm to the F.Cu RAW_PROTECTED trunk (x 45.2, rule 0.15 + 0.02); 0.496 mm to R84.1 (BAT_ILIM); 0.92 mm to the BAT_ILIM track; 1.35 mm to the outline; 1.94 mm to the next GND via (42.9, 87.6). Copper reach (0.1 mm raster): **U9.8 2.57 mm** (record 2.54 at 0.05 mm), C81.2 3.56 mm (3.51), R84.2 under 1.1 mm (0.64). The C15 piece (B.Cu 42.05–45.5, 82.44–87.27) fell from 14.8 to **4.74 mm** of maximum copper distance. C88's IN–GND bypass loop now closes C88.2 → via (42.9, 87.6), 0.35 mm → In1 1.94 mm → via (44.65, 86.775) → U9.8, 2.6 mm: about 4.9 mm of return path, down from about 26 mm. TI SLVSFC9C §8.4.1 (https://www.ti.com/lit/ds/symlink/tps25947.pdf, as quoted in pass 2 and M3_R8 "Power") is now met in substance |
| R8P2-PLANES-02: M3_R8 "Ground" figures were stale | **Closed** (one row left; finding 02) | M3_R8 line 154 says 90.50 %, four slots, 21 islands. Survey: P1 0.905, P3b 4, and the slots listed in `survey.json` are J123 (5.60 mm², x 10.25–14.15, y 74.45–76.35), J3 leg 1, J3 leg 4 (3.99 mm² each) and the SPI1 / IMU_CS cluster (2.95 mm²). Islands: F.Cu 12 + B.Cu 9 = 21. R8_VALIDATION's P3b row still names three of the four slots |
| R8P2-PLANES-03: no gate or record measured GND-pad copper reach | **Closed in part** (accepted) | D102's pad stage runs on every build, for IC pads only. I re-measured C15's figures at 0.1 mm: U13.2 9.31, C93.2 7.24, J9.2 7.00, Q122.2 12.47, R123.2 13.06 mm. They agree with the record's 0.05 mm figures (9.28 / 7.24 / 6.92 / 12.42 / 12.98) to within the raster. C15's other pieces also agree with `fix2_measurements.json` `fingers_w1_maxdist`: 11.14 mm; 10.34 mm (my 10.52 at 0.1 mm); 9.92 mm |

## 2. What fix pass 2 changed on the planes

The copper diff against `6600ef94…` (`copperdiff.py`) shows these changes:
- **Footprint:** R81 moved.
- **BAT_ENABLE:** the spine is split at y 92.1, with a 0.82 mm stub to R81.1.
- **C83.2's link:** two GND segments became one, (11.1, 35.4) → (9.55, 35.4).
- **Four vias shrunk from 0.6 to 0.5 mm:** GND (33.9, 45.2), (41.4, 47.8) and (41.45, 32.6), and RAW_PROTECTED (35.25, 60.5).
- **Two grid vias regenerated beside R81:** (39.0, 91.3) → (38.85, 91.3) and (43.0, 91.5) → (42.9, 91.45).
- **Two new vias:** (13.5455, 74.2255), basis `island B`, and (44.65, 86.775), basis `pad U9.8`.
- **J123.2:** solid connection → thermal relief.
- **The In2 BAT_IN zone:** x 12.4–45.5 / y 100.3–117.5 became x 12.4–33.5 / y 100.3–112.6. The In2 GND zone's matching
  cut-out followed; its 34-vertex outline is otherwise identical.

The fill diff (`filldiff.py`, pieces ≥ 0.3 mm²), and what each change does to the planes:
- **In2 GND:** +304.4 mm² (BAT_IN −306.5 mm²).
  - In2 is still one GND outline, now 2,686.8 mm².
  - At 0.4 mm erosion it is a single core. Pass 2 had the south-west pocket hanging on a 0.8 mm strip at x 11.2–12.1;
    that pocket now also joins along y 112.6–117.5, forward of the trimmed island.
  - The right forward tab (y 105–110) and the hole (42, 114.4) are GND on all four layers (`fix2_measurements.json`).
  - U9's feed lane (BAT_IN, B.Cu x 41.25) and the BAT_ENABLE spine (x 40.42) now run over In2 GND. BAT_ENABLE's length
    over In2 BAT_IN is 0.18 mm, at R165's via end.
- **J123:** In1 −2.04 mm², F.Cu −2.94 mm², B.Cu −3.22 mm².
  - These are J123.2's relief ring and J123.1's antipad merged into the fourth In1 slot (5.60 mm²).
  - No F.Cu track lies over the slot. The only tracks in its box are B.Cu PULLPIN (x 14.23) and PULLPIN_EXT, which
    reference In2 (3V3 there).
  - The B.Cu piece west of J123 (7.67 mm²) is island 3. It holds the vias (11.875, 72.125) and (13.5455, 74.2255) plus
    J123.2's two B.Cu spokes.
- **In2 3V3:** −0.68 mm², the antipad of the new J123 island via.
  - Its edge sits 0.02 mm from PULLPIN's B.Cu track edge, in plan view.
  - D62's guard (0.3 mm + ring + margin) holds: 0.5845 mm from the via centre to the track edge, against 0.57 required.
  - PULLPIN is a DC detect line, not an AGENTS §3 net, so its reference is intact but only just.
- **In2 3V3 near (33.9, 45.2):** +0.2 mm², from the via shrink.
- **In1 near V_IN1 (35.25, 60.5):** +0.17 mm², a ring, from the via shrink. The antipad is still present (probed).
  `filldiff.py` also printed a 0.96 mm² "gain" there; it is a fracturing artefact, and the box-area comparison shows only
  the ring.
- **B.Cu round R81:** −1.6 / +1.0 mm². route_check finds no new sliver or finger there, and the gate passes.

## 3. In1

- **The plane.** One GND outline, 4,861.7 mm² (pass 2: 4,863.6). There is no In1 track (S16 = 0).
- **Holes.** 196 in all, 305.6 mm² (the scan covers the In1 fill inside the outline less 0.55 mm). Those larger than an
  antipad:
  - the J121 / J124 / J1 / J122 barrels;
  - the J30 / J31 launch cut-outs, 7.29 mm² each, intended;
  - the SPI1 / IMU_CS cluster, 2.95 mm²;
  - J3's legs 1 and 4, 3.99 mm² each;
  - **J123, 5.60 mm², new** (D101).
- **Critical F.Cu tracks over a foreign In1 hole.** Edge samples only; no centre line crosses one. All are equal to
  pass 2:
  - RADIO_NRST 0.60 mm, along the 3V3 / CAM_MCU_RX pair;
  - USB_DM 0.48 mm, at VBUS_SENSE's via (16.6, 35.1);
  - QSPI_CLK 0.46 mm, at the 3V3 via (28.75, 45.1);
  - QSPI_IO2 0.14 mm, at QSPI_NCS's via;
  - SPI1_SCK, edge, at the cluster;
  - GNSS_RF_ANT and RADIO_RF_ANT, 2.32 mm of centre line each over their own launch cut-outs (intended).
- **RF strip.** Fix pass 2 changed no copper at y < 30; the check_r8 rigid digests, fence and strip reach pass.

## 4. In2

- **Region structure, by erosion of the unfractured fills.**
  - The 3V3 region keeps one core at 0.5 mm erosion; it has 3 large cores at 1.0 mm, the same necks as pass 2.
  - GND is one core at 0.4 mm, an improvement on pass 2 (see section 2).
  - BAT_IN is solid to 0.4 mm erosion.
  - The RAW_ACT islands are solid at 1.0 mm.
- **B.Cu signals over In2, every non-power net** (centre line):
  - GND 245.2 mm (pass 2: 244.3; +0.9 mm is R81's stub);
  - 3V3 212.4 mm;
  - BAT_IN 5.3 mm;
  - RAW_ACT 0.8 mm;
  - crystal keep-out 4.6 mm;
  - antipads 43.2 mm.
- **Split crossings** (all three unchanged):
  - ARM1_SENSE, 3V3 → GND at (18.18, 53.86), after 14.52 mm over 3V3. Recorded in M3_R8 "Return paths" (D47 / D70).
  - ACT_GATE, RAW_ACT → GND at (11.31, 105.97). An inherent slow gate at the facing-FET band, a pass-1 / pass-2
    observation.
  - ACT_GATE, GND → BAT_IN at (12.41, 107.07). The same observation; the island's west edge x 12.4 did not move.
  - No critical net crosses the new BAT_IN edges at x 33.5 or y 112.6.
- **Critical vias** (28). Each has its nearest GND via or plated GND hole within 0.71–1.47 mm, except:
  - A8 (PYRO1_GATE in TP122): 2.72 mm, allowlisted;
  - NRST (24.0, 51.1): 2.93 mm, not an AGENTS §3 net.

  These are unchanged from pass 2.

## 5. Crystal, QSPI, SPI, USB, SWD

None of these changed in fix pass 2. I re-listed the crystal keep-out box (`Y1_In2_keepout`, x 18.9–26.8, y 46.3–50.95):
- **Crystal.**
  - The keep-out holds only HSE_IN / HSE_OUT, the load capacitors' GND links ((19.53 → 18.75, 49.7) and
    (26.17 → 26.95, 47.5)) and three GND vias.
  - HSE_OUT keeps its D86 geometry (F.Cu (23.0, 52.55) → (23.0, 49.19) → via (24.69, 47.5) → B.Cu to C26.1), with its
    GND partner 1.25 mm away.
  - Y1.4's GND reach is 2.67 mm.
- **QSPI / SPI1.** The B.Cu stubs over In2 3V3 have their pass-1 figures: QSPI 12.3 mm in all; SPI1 / IMU_CS
  0.40–0.72 mm.
- **USB.** DP / DM run on F.Cu over solid In1.
  - D4.2's pocket still has 2.891 mm² and its one via (9.0, 33.8).
  - C83.2's new straight link (B.Cu, y 35.4) gives U10.2 a reach of 1.96 mm.
- **SWD.** F.Cu over In1 GND for its whole length.

**Bucks (an extra check; nothing found).** The input-capacitor return of each buck closes on B.Cu, beside the IC:
- C6.2 → U2.4: 0.90 mm of copper;
- C72.2 → U8.4: 1.05 mm.

That is Diodes' layout as D40 / D41 cite. The switch nodes still lie over In2 GND, since fix pass 2 changed no In2 copper
there.

## 6. GND pours: islands, fingers, stitching

- **Islands.** F.Cu has 12 and B.Cu 9; pass 2 had 12 / 8. The new B.Cu island is J123's (7.67 mm²: two vias plus
  J123.2's spokes). Every island has ≥ 2 vias or holes except the D4.2 pocket (D63 / D68, gate `WEAK_EXCEPT`).
- **D63 / D64.**
  - P7 = 1.
  - P9 / P10 are 4.47 / 9.65 mm against floors of 4.32 / 9.42 and ceilings of 4.6 / 9.7 mm; P11 is 2.90 / 5.89 mm.
  - The maximum is still at (0.25, 88.25), under the triple-layer RAW_ACT band, so the floors and dispositions stand
    (Inference). The In2 trim did not touch the RAW_ACT corridor or the west band.
- **Fingers.** The counts equal C15:
  - R7 method (rings kept, F / B): **10 / 17**;
  - gate method (rings excluded, all layers): **6 / 14**.

  The worst copper distances are:
  - B.Cu round U13: 11.14 mm;
  - the F.Cu strip that carries Q122's pocket: 10.52 mm;
  - the In1 west edge: 10.0 mm;
  - B.Cu at the east edge: 7.13 mm;
  - In2 (11.23–12.12, 100.3–108.35), 6.72 mm: the In2 GND strip between the RAW_ACT and BAT_IN islands, also in the
    record's 14.
- **Stitching.** P8 is 8.15 vias / cm². There are 193 step-7 vias: 89 grid, 54 cover, 25 fence, 16 return, 5 island,
  2 stitch, 1 C24 and 1 pad. Each moved via keeps ≥ 1.0 mm from the other GND vias (the gate's `table` and
  `islands`).

## 7. GND-pad copper reach (gndpads.py, 0.1 mm raster)

| Pad | Layer | Copper to nearest GND via / plated hole | Pass 2 | Note |
|---|---|---:|---:|---|
| R123.2 / Q122.2 (gate drive) | F | 13.06 / 12.47 mm | 12.98 / 12.42 | C15, D64's trade (B.Cu BAT_IN neck under the pocket) |
| U13.2 / C93.2 (camera IO LDO) | B | 9.31 / 7.24 mm | 9.28 / 7.24 | C15, no legal spot |
| J9.2 (camera GND) | F | 7.00 mm | 6.92 | C15, no legal spot |
| R102.2 (CAM_UART_OE pull-down) | F | 5.39 mm | 5.32 | DC |
| R105.2 (CAM_5V_SENSE) | B | 4.14 mm | — | sense divider, DC |
| U11.12 / U11.6 (TPS2121) | B | 3.80 / 3.54 mm | — | under D102's 4 mm |
| **U9.8** | B | **2.57 mm** | **14.06** | closed (D102) |
| **C81.2** | B | **3.56 mm** | **8.64** | closed (D102) |
| every other GND SMD pad | F / B | ≤ 4.27 mm | | |

## 8. Findings

### R8P3-PLANES-01: Minor, worth fixing (records)
**Fix pass 2's open item, "step 7 keeps 0.5 mm from pyro and arming nets but not from the actuator gate nets (R120.2's
0.180 mm GND via)", is aimed at the wrong copper. The GND pours themselves come to 0.150 mm from five bare
actuator-gate pads, closer than that via. So moving the via, the fix the records invite, would gain nothing.**

- **Requirement.** REQUIREMENTS M2 says every review-only residual is listed with its *measured* reason, and AGENTS §3
  says records must state the board as built. The pyro-observations row, C12b #19 and "Open after fix pass 2" name only
  the via.
- **Evidence** (pcbnew on `990c8040…`; `padfill.py`, `probept.py`, `nearpad.py`):
  - **The via.** The grid via (15.0, 107.3) (`r8_ground.tsv` line 125, basis `grid`) is 0.180 mm, edge to edge, from
    R120.2 (ACT_GATE, B.Cu, bbox x 14.03–14.57, y 106.877–107.443). It is the only GND via within 0.52 mm of any
    ACT_GATE / ACT_DRV / ACT_EN pad.
  - **The via is tented** on both sides (board setup `tenting (front yes) (back yes)`, `pad_to_mask_clearance 0`).
  - **GND fill to the nearest bare pad edge, by polygon distance:**
    - B.Cu: **R120.2 0.150 mm** and **C120.2 0.150 mm** (ACT_GATE). Probed at 0.14 mm: no fill. At 0.16 mm: GND, on
      R120.2's east and south sides and C120.2's west and south sides.
    - F.Cu: **Q122.3 0.150 mm** and **R121.2 0.150 mm** (ACT_DRV; GND at 0.16 mm north and south) and **R121.1
      0.150 mm** (ACT_GATE, at a corner).
  - **No GND pad lies within 1.0 mm of any ACT_GATE / ACT_DRV pad** (`padpad.py`). Rule H's pad-to-pad 1.0 mm intent is
    therefore met. The DRU says "Tracks, vias and zones keep rules A-G and A2", so masked GND copper next to these pads
    stands at the board's 0.15 mm.
  - **A move is possible but gains nothing.** In-memory trial (`actgate_spot.py`):
    - I removed the via, refilled, and called `make_ground.legal()` with ACT_GATE / ACT_DRV / ACT_EN held at 0.5 mm.
    - The grid node's nearest legal spot is **(15.0, 108.1)**, 0.80 mm away (within SNAP), with no other GND via within
      2.0 mm of the node.
    - With the via there, the nearest GND copper to R120.2 would still be the pour, at 0.150 mm.
- **Effect.** Inference:
  - A short from ACT_GATE or ACT_DRV to GND turns Q120 / Q121 on with the power switch open, as M3_R4 gives as rule H's
    reason. It cannot fire a channel by itself, since Q124 stays off.
  - For masked copper (pour or tented via) the short needs a mask defect plus a solder or debris bridge.
  - It is screened by ORDERING §5's "RAW_ACT dead with the switch open, link out and in" step.
  - It is the same class of exposure the board has at every bare pad beside the GND pour (R7 practice, owner-accepted).
- **Fix** (records, cheap):
  1. In R8_VALIDATION's pyro-observations ACT_GATE row and C12b #19, add the pour figures: B.Cu GND 0.150 mm from R120.2
     and C120.2, F.Cu GND 0.150 mm from Q122.3, R121.2 and R121.1. All are masked; the via at 0.180 mm is tented.
  2. Close the "Open after fix pass 2" item as "no gain from moving the via". Optionally, offer the owner the effective
     lever as a separate choice: a fill-clearance rule GND ↔ ACT_GATE / ACT_DRV, e.g. 0.5 mm like Pyro D, applied to
     zones, together with the matching `make_ground.clearance` entry.
  - That option is a copper change round R120, C120, R121 and Q122 that I have not trialled. It is not needed by
    any rule the project has.

### R8P3-PLANES-02: Minor, worth fixing (records)
**R8_VALIDATION's scorecard row P3b names three In1 slots, leaving out the SPI1 / IMU_CS via cluster. Its "no critical
track crosses them" would not hold for the cluster.**

- **Requirement.** Records state the board as built (AGENTS §3). M3_R8 "Ground" and R8_VALIDATION should agree.
- **Evidence.**
  - `docs/R8_VALIDATION.md` line 91 reads: "the In1 "slots" are the thermal-relief rings round J3's legs 1 and 4, D89,
    and since fix pass 2 J123.1's antipad merged with J123.2's relief ring, D101; no critical track crosses them".
  - `survey.json` `planes.in1_slots` lists four slots: J123, 5.60 mm²; J3 legs, 3.99 mm² each; and the SPI1 / IMU_CS
    cluster, x 8.29–11.00, y 55.15–56.85, 2.95 mm².
  - M3_R8 line 154 names all four.
  - `reference_audit.py`: SPI1_SCK F.Cu has 34 edge samples over the cluster at SPI1_MISO's via (centre 0.00 mm).
    These are among the 226 "other via" samples M3_R8 already explains. The sentence is therefore wrong only for the
    slot it leaves out.
- **Fix.** Change the row to: "the In1 slots are the SPI1 / IMU_CS via cluster (SPI1_SCK's F.Cu edge passes it, inside
  the audit's 226 other-via samples), the relief rings round J3's legs 1 and 4 (D89) and J123.1's antipad merged with
  J123.2's relief ring (D101); no critical track crosses the last three".

## 9. Observations (not findings)

- **U9's new via** sits 0.176 mm from the F.Cu RAW_PROTECTED trunk (U9's output, at most 2.2 A). That is the board rule
  plus 0.02 mm, and both items are masked. A bridge would short the protected rail to GND, and U9's current limit would
  then hold it (Inference). This is the same class as C12's GND / RAW_PROTECTED 0.171 mm pair.
- **J123's island via** (13.5455, 74.2255) puts an In2 3V3 antipad edge 0.02 mm from PULLPIN's B.Cu edge, inside D62's
  guard. PULLPIN is a DC detect line with a 10 kΩ pull-up, so there is no consequence.
- **ARM1_SENSE over 3V3** (14.52 mm), **D4.2's single via** and **G7** are unchanged from pass 2. The pass-2 inferences
  stand.
- **C88's bypass loop** now closes through two vias 1.94 mm apart. The loop could be shortened further only by joining
  C88.2 to U9.8's B.Cu piece across BAT_ILIM, which is not practical. TI's "minimize the loop area" is met in substance.

## Method and scripts

The scripts are in the session scratchpad, `p3planes/`. All are read-only on the board, and pass 2's copies were reused
where possible.
- `zones.py`, `islands.py`, `islvias.py`: the zone inventory, and the outer GND islands with the vias and pads that
  touch them.
- `refall.py`, `splitall.py`, `b_over_antipad.py`, `critvias.py`: reference and split sampling for every critical net
  (plus SWD and NRST), B.Cu crossings, foreign antipads, and critical vias with their GND partners.
- `in1holes.py`, `necks.py`, `necks_in1.py`: In1 holes and slots, and erosion of the In1 and In2 fills.
- `fingers.py`: route_check `pour_pieces` at 0.75 / 1.0 mm, with and without rings, plus copper distance.
- `gndpads.py`: GND-pad copper reach. `p2p.py`: same-layer copper distance between pads (the buck loops).
- `copperdiff.py`, `filldiff.py`, `areabox.py`, `zoutline.py`, `probe.py`: the diff against `6600ef94…`. That board was
  extracted from fix pass 2's archive into `p3planes/base/` and deleted after use.
- `area.py`, `viaclr.py`, `nearpad.py`, `padpad.py`, `padfill.py`, `probept.py`: local inventories, via clearances, and
  GND copper near the actuator-gate pads.
- `actgate_spot.py`: an in-memory `make_ground.legal()` trial with the via removed and ACT_* held at 0.5 mm, never
  saved.
