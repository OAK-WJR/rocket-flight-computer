# R9 clean-sheet survey: the hard constraints, re-derived

Read-only survey for the R9 clean-sheet redesign. For every footprint and block it separates what a requirement, a
safety rule, a maker document, the bay stack and harness, the bore fit or a manufacturing rule truly fixes from what
R7 and R8 only inherited by convention or by rigid copy. For the CH1 pyro block and the RF strip it lists the analyses
that must be redone to qualify a new geometry, and it proposes rule-based checks to replace `check_r8`'s rigid hashes
and `check_actuators`' PYRO_BLOCK rectangle without weakening them.

- **Board read:** `rocket-flight-computer-r9/m3_design/assembly_review/m3.kicad_pcb` (R8, branch m3-assy-r9 at 9c8179b),
  SHA-256 `cc044ea0922ff826df19af9d9726d92c096ab2b127025b55d123d8772e5fb4a7`, re-hashed before and after this survey.
  It was loaded read-only with KiCad 10.0.6 `pcbnew` and never saved.
- **Scripts and dumps** (scratch, next to this file): `constraints_tools/dump_r8.py` (`r8_fp.json`: 249 footprints,
  their courtyards, model boxes and rule areas), `pads.py` (module and terminal pad maps), `block_probe.py` and
  `hull_probe.py` (nets inside the pyro block).
- **Documents read:** `AGENTS.md`; `docs/REQUIREMENTS.md` (F1–F10, P1–P3, M1–M3, operating assumptions); `docs/M3_R8.md`;
  `docs/R8_VALIDATION.md`; `docs/ORDERING.md` §3, §5, §7; `docs/MARGIN_PRESCRIPTION.md` P0-1, P1-9, P1-13, P1-14, R14;
  `docs/M3_R4.md` §1c–§3 (the solder-bridge, divider and coating work); `docs/M3_R5.md` L3, L8, L10, L11, V1;
  `docs/M3_R6.md` (owner decisions); `docs/DESIGN_ASSURANCE.md`; `m3.kicad_dru`; `m3_design/check_actuators.py`;
  `tools/check_r8.py`, `check_r7.py`, `fit_check.py`, `route_check.py` (constants); the r8_design files
  `R8_DECISIONS.md`, `r8_plan.md`, `plan_cleansheet.md`, the R7-based `survey_constraints.md` and `step9/*.py`;
  r7_review `pass1_layout.md` §3–6 and `pass2_rf.md` §3–7; and the parent `CLAUDE.md` and `docs/VEHICLE.md`.
- **Coordinates:** KiCad mm, as R7 and R8: x = 0 is the left long edge, y = 0 the aft edge (SMA jacks), y grows
  forward. The bore axis is x = 23 on the top face.

**Inference** marks anything not measured here and not taken from a requirement or a maker document (AGENTS §2.5).

---

## 0. Fixity classes used below

| Class | Meaning | How it may change |
|---|---|---|
| **REQ** | Requirement text (REQUIREMENTS, AGENTS §2) or the safety meaning behind it | Only by an owner-approved requirement edit |
| **SAFE** | A safety contract that is net- or pad-based and holds anywhere (`check_actuators`, `m3.kicad_dru` rules A–H/A2, `check_r8` D18/D19/D85) | Never weakened; a deliberate strengthening is re-pinned after review |
| **MAKER** | A maker document or JLC capability (datasheet, integration manual, land drawing, stack-up) | Only with a different part or process |
| **BAY** | The vehicle and harness: the parent VEHICLE stack row, the operating assumptions, ORDERING §7 | Owner or vehicle change |
| **FIT** | Computed from P2's bore formula (`fit_check`: margin = 24.9 − hypot(\|x − 23\| + 0.3, \|z\| + 0.3) ≥ 0) | Follows from the part height; not negotiable |
| **OWN** | A recorded owner decision that is not written as a requirement (M3_R6 decisions table; owner-delegated R8 decisions) | With the owner's word |
| **TEXT** | Requirement or record text that only quotes R7/R8 geometry (for example F10's "y 0–23.5 mm of a 46 × 118 mm board") | Record maintenance when the geometry changes; flag it to the owner, but it is not a design constraint |
| **INH** | Inherited by convention, by an R5–R8 engineering choice, or by rigid copy only | Free in R9 |

---

## 1. Summary

### 1.1 Truly fixed (REQ / SAFE / MAKER / BAY / FIT / M1–M3)

- **Outline:** 46 mm wide (P1, REQ). Length ≤ 120 mm and **as short as possible** (P1): an objective, not a fixed
  number (section 2).
- **Fit (P2, FIT):** every part and every mated plug fits the Ø50.8 mm bore less 0.5 mm, with the top face on the axis
  ±0.3 mm. This alone fixes the x band of every tall part (section 2.2).
- **Supports (P2):** five M3 holes, one within 6 mm of each corner on both axes and one in the middle third of the
  length; ≥ 3.5 mm bottom and ≥ 3.8 mm top clearance; nylon hardware; no sixth support (owner-delegated). Two Ø3.2 tie
  holes beyond both ends of J122, with a ~4 mm under-board tie path (P2, P3, MARGIN P1-13).
- **SMA jacks J30/J31 (F8, F10, M1):** on the **aft** edge, top side, rotation 0, ≥ 12 mm centre to centre, no paste,
  fitted in the through-hole step; "GNSS" and "RADIO" legends. Their x positions are **not** fixed.
- **RF strip (F10, MAKER):** at the aft end, full width, with its per-layer content rules (In1 and In2 GND only; F.Cu
  and B.Cu GND outside the RF lines, module pads and the modules' own supply and interface traces); nothing but GND
  under U31 on any layer (EBYTE manual §4.1); only GND and U30's own escapes under U30 on F.Cu and In1 (u-blox IM §4.4);
  50 Ω GCPW for JLC041611-7628 over unbroken ground; an ESD diode at each jack; a pi-network footprint; the bias tap on
  the antenna side; RF parts ≥ 5 mm from switching regulators, the MCU, the crystal and fast digital lines; a GND via
  fence at the strip boundary; both modules on the top side.
- **Pyro safety (AGENTS §2, F7, F8, SAFE):** the ARM break (net membership, rule E 1.0 mm, rule H 1.0 mm pads), the
  pyro bus after the load switch, the gate network topology and values, the split-top / parallel-bottom sense dividers
  with a 4.7 kΩ at each ADC pin, rules A–H and A2 on every layer, battery-live copper ≥ 1.0 mm from bus/igniter/drain
  copper (D85), no inner RAW_ACT / BAT_IN within 2.5 mm of armed-live copper (D18), GATE_N ≥ 0.5 mm from servo PWM
  (D19), no test pad on BUS/IGN/OUT, TP122 on the bottom, mandatory local coating of the block and of J2 (P3).
- **Part identities (F8, M3):** black DB128L 2P for J124 (ARM) and J121 (IGN), green DB128V 4P for J1, keyed GH 4P for
  J9, ARM / IGN / pin legends; the BOM at 52/52 extended codes, so **no new extended part** is possible.
- **U1 contract pins (SAFE, `check_actuators`):** PE4 (pin 3) gate, PC0 (15) continuity, PC5 (33) arm sense, PB0 (34)
  RAW_ACT sense, PA0–PA3 (22–25) servos, the sentinels 2, 4, 5, 16, 32 and NC pins 40, 97, IMU_INT1 on 98.
- **Process (M1, M2):** JLC 4-layer 1.6 mm, 1 oz inner, JLC041611-7628, ENIG, two-sided Standard PCBA at 240 °C; the
  modules reflowed last on the top; no via holes in soldered pads (the TP122 gate via is the only named exception, and
  a free block layout can remove it); the clean-routing list.
- **MEMS (P3):** no vias or copper fill under a MEMS sensor on its component side; a 3 mm coating- and staking-free
  zone round the IMU.

### 1.2 Owner decisions (OWN): fixed until the owner says otherwise

- **J1 grouped with the CH1 terminals** ("battery and CH1 terminals form a clear screw-terminal group", M3_R6;
  `check_r7`/`check_r8`: J1 within 25 mm of both terminal centres).
- **No sixth support** (R7 pass 2, owner-delegated; R8's C10 vibration item accepted 2026-10-20).
- **7.7 A neck limits** (R8_DECISIONS D12, owner-delegated): RAW_ACT and BAT_IN ≤ 20 °C (≥ 5.3 mm outer / 5.6 mm inner),
  ACT_FET_S ≤ 30 °C (≥ 3.71 mm), a rise above R7's accepted 44 °C a regression.
- **"UART ports share one edge block"** (M3_R6): **moot since R7**, which removed the radio and GPS ports; only J9
  remains, so it binds nothing.

### 1.3 Text that only quotes R7/R8 geometry (TEXT): update the record, do not design to it

F10's strip coordinates ("y 0–23.5 mm of a 46 × 118 mm board"), its quoted stitching gaps (4.27 / 3.68 mm; 3.90 / 2.65 /
1.55 / 1.55 mm), "the antenna-bias limiter sits on B.Cu under U30" (an R7 placement written into F10; the maker rule is
only "nothing but GND on F.Cu and In1 under U30"), P1's "R7 and R8 are 46 × 118 mm", P2's R8 f1 figures, F4's R8 solve
numbers, M2's R8 deviation list, ORDERING's coordinates, J124 "unmoved", the PYRO_BLOCK extent quoted for the fuse-holder
keep-off, and the parent VEHICLE stack row (118 mm, the five hole coordinates).

### 1.4 Inherited only (INH): free in R9

Everything inside the pyro block and the RF strip (positions, rotations, internal copper), the jack x positions and the
GNSS/radio side assignment, the strip depth, the outline length and hole positions (within P2), J122's position within
the axis band, the tie-hole positions relative to J122, the terminals' entry directions, J1's entry direction, J9 and J123
anywhere they fit, J3 on either long edge, J2's place, U1's place and rotation, every non-contract MCU pin (with the
D5 loader and D6 EXTI rules), the IMU's and barometer's side, place and rotation (with a recorded axis map), every
power-conversion block, and every hash constant in `check_r8` (`RIGID_BASELINE`, `CH1_PADS`, `EXIT_VIAS`, `RIGID_IN2`,
`JACKS`, `STRIP_Y`, `FENCE_Y`, `U31_BODY`, `MODULE_GND`, `STITCH_ACCEPTED`), `check_actuators` 15b's rectangle and
`fit_check.RETENTION_HOLES`.

### 1.5 What a clean sheet costs

A full requalification: every placement-bound item of R8_VALIDATION's requalification list, plus the two things R8
avoided by rigid copy: the pyro block's spacing, bridge, coating and gate-neighbour qualification (section 9.4), and the
RF strip's GCPW, launch, stitching, discontinuity and coexistence qualification (section 8.4). The RF field solver used
in R7 pass 2 is **not in the repository** (pass2_rf §7) and must be rebuilt.

---

## 2. Board envelope and the P1 length

### 2.1 Envelope

| Item | Rule | Class |
|---|---|---|
| Width | 46.00 mm (± 0.01 in `check_r8` and `fit_check`). The bare board could be about 49 mm wide before its edges touch the bore (hypot(w/2 + 0.3, 1.9) ≤ 24.9), but edge parts would lose height; 46 is the owner's figure | REQ (P1, owner M3_R6) |
| Length | ≤ 120.01 mm; as short as possible. The SMA overhang (9.5 mm), mated plugs and the 44–48 mm coax loop zone count in the bay stack, not in the outline | REQ (P1); BAY |
| Bay slack | VEHICLE: ~52–68 mm of slack with the 118 mm board; every mm saved adds slack | BAY |
| Stack-up | 4 layers, 1.6 mm, 1 oz outer and inner, JLC041611-7628; In1 the solid GND reference (no In1 track, D20); In2 power regions and GND (no signal track, D20) | REQ (M1); SAFE-adjacent (D20) |
| Track / space / via | 0.15 / 0.15 mm; vias 0.3 / 0.5 minimum, 0.6 standard; copper 0.5 mm from edges (SMA pads 0.2 mm, DRU); hole clearance 0.25 mm (J3's locating holes 0.20 mm) | MAKER (JLC); `m3.kicad_dru` |
| Bottom depth | No bore limit in practice; the sled standoffs (≥ 3.5 mm) set it: bottom parts ≤ 3.0 mm below the bottom face (R8: L1 3.02 mm); SMA lower flanges 1.2–1.4 mm and plug nuts 2.6 mm below | BAY (ORDERING §7) |

### 2.2 Height allowed above the top face, by the farthest corner's distance d = |x − 23|

| d (mm) | 0 | 5 | 10 | 14 | 16 | 18 | 19.8 | 21 | 22 | 23 |
|---|---|---|---|---|---|---|---|---|---|---|
| Max height (mm) | 24.6 | 24.0 | 22.4 | 20.1 | 18.5 | 16.6 | 14.4 | 12.6 | 10.8 | 8.5 |

What this fixes (FIT; same formula as `fit_check`):

| Part / envelope | Height | Allowed d of its farthest corner | R8 margin |
|---|---|---|---|
| J122 mated (servo plugs + wire bend, R5 allocation) | 23.5 | **centre within ±3.02 of x 23 at rotation 90/270; ±1.94 at 0/180** | 0.71 |
| J121 / J124 (DB128L 2P) | 14.4 | ≤ 19.8 (outer face at x ≥ 3.2 or ≤ 42.8) | 1.15 |
| J1 (DB128V 4P) | 14.5 | ≤ 19.7 | 6.4 (R7) |
| C84 (OS-CON) | 12.8 | ≤ 20.9 | 1.37 |
| C121 (470 µF) | 10.5 | ≤ 22.1 | — |
| J9 mated (GH + 3 mm wire) | 10.3 | ≤ 22.2 | **0.03** |
| SMA jack + straight plug | z −4.1…+5.1, x ±4.6 | **jack axis within x 3.6–42.4** | — |

So J122 is the only part pinned to the axis; the terminals, J1 and C84 need only to keep their outer corners inside the
band; J9 does **not** need an edge (it is a vertical top-entry part; its R8 edge position gives the worst margin on
the board).

### 2.3 How short can it be? (Inference; to be settled by the placement analyst)

R8's courtyards cover 2156 mm² on the top and 979 mm² on the bottom: 40 % and 18 % of 46 × 118 mm. The length is set
by the items that cannot share a y band, because each needs most of the width or the axis:

| Item | y depth it needs (R8 figure) | Why it cannot share the band |
|---|---|---|
| RF strip | 21.5–23.5 mm (jack pad 4.4 + chain to the module pin ≈ 4 + module 10 + feed/fence ≈ 3–5) | F10: full width, In1/In2 GND only |
| RF-to-MCU gap | ≥ 5 mm (F10) | the 5 mm separation from U1 and its fast lines |
| U1 band | 17.3 mm courtyard + escapes | 17.3 mm wide |
| J122 + tie holes | ≈ 14–17 mm | axis band; can share U1's band only if U1 sits off axis (U1 right courtyard edge ≤ J122's left edge; J122 at x ≈ 26 leaves U1 centre ≤ 13.5) |
| CH1 block | ≈ 18 mm (R8 81.3–99.2); the interior could pack tighter | the two terminals span 37 mm when both face the long edges |
| J1 | 11.3 mm + 1.9 mm to the forward edge | 22.2 mm wide, cannot sit between the terminals (14.5 mm gap) |

Stacking these gives roughly 23.5 + 5 + 20 (U1 with J122 beside it) + 18 + 13 ≈ 80 mm of central column, about 95–100 mm
with J122 in its own band, before the corner holes, the mid-span hole and routing room. A 90–105 mm board at 50–55 % top
density looks reachable (Inference). Shorter also helps P2/P3: R8's mode 1 is the unsupported long edge, so f1 rises as
the span shrinks (Inference: roughly with 1/L² for that mode). The trade is routing room (priority 2), which the owner
ranks after P1's "as short as possible".

---

## 3. Supports, tie holes and panel tabs

| Feature | What is fixed | What is inherited | Class |
|---|---|---|---|
| Five M3 holes (Ø3.2, Edge.Cuts) | Five; one within 6 mm of each corner on both axes; one in the middle third of the length; bottom parts and pads ≥ 3.5 mm from each centre, top bodies and exposed pads ≥ 3.8 mm (7 mm washer + 0.3); nylon hardware (washer ≤ 7 mm OD, standoff ≤ 5.5 mm AF, ≥ 3.5 mm tall) | R7/R8 positions (4, 4), (42.3, 4), (4, 64), (4, 114.4), (42, 114.4). The (42.3, 4) offset is an R6 LED2 leftover. The mid-span hole on the left edge leaves the right edge unsupported for 110 mm, which is R8's mode 1, and C84 on its antinode cost 16.6 Hz | REQ (P2) / FIT; positions INH |
| "Effective" mid-span support | P2's word; `fit_check` only asks for the middle third | Which edge or interior point: free. An interior or right-edge mid-span point would suppress the mode R8 measured (Inference) | REQ; place INH |
| Sixth support | None | — | OWN |
| Vibration | P2: re-derive on the final geometry; tap check on the sled with both coax leads | R8 f1 209–490 Hz (R7 221–533, R6 241–559; R6's figure was the basis of the no-sixth-support decision) | REQ |
| J122 tie holes (2 × Ø3.2) | Beyond both ends of J122 so the tie passes over all four plugs and closes under the board; a ~4 mm under-board channel between them clear of bottom parts | (21.5, 68.6) and (27.0, 82.6), hard-coded in `fit_check.RETENTION_HOLES` and `r8_legalise.TIE`; the forward hole sits off axis only because R5's RAW_ACT column ran there (L11) | REQ (P2, P3, MARGIN P1-13); positions INH |
| Tooling holes | None needed for Standard PCBA (removed in R8, D8) | — | — |
| Panel tabs | Long edges only; nothing on the aft edge (jacks overhang 9.5 mm); 5 mm tabs; ≥ 1.5 mm from parts and pads, ≥ 5 mm from capacitors, R166, LED2 and both modules, ≥ 2 mm from connectors, 1.5 mm from holes; mouse-bite hole edges ≥ 0.5 mm from copper; 4–6 tabs for a board over 100 mm; nibble, never snap; no V-cut (J3 overhang) | R8's five tab spans; JLC's acceptance of five long-edge tabs is still to be confirmed | MAKER (JLC) / ORDERING §3 |

A clean sheet should keep a legal 5 mm window on each long edge near both ends (R8 has them; R7 had none forward of
y 71.5), and keep tabs off In2 regions other than GND where it can (R8's y 63–68 tab sits over In2 3V3, R8P3-POWER-05).

---

## 4. Connector edges and entry directions

| Part | Truly fixed | Inherited only | Consequences a clean sheet must respect |
|---|---|---|---|
| **J30, J31** (Kinghelm KH-SMA-KE8-G edge-launch, C530661) | **Aft edge** (F8, F10), top side, rotation 0 (flange on the routed edge, local y = 0 on Edge.Cuts), ≥ 12 mm c-c, no paste, THT step after reflow (M1), GNSS / RADIO legends (F8). Land per the Kinghelm drawing: centre pad 1.2 × 4.2 mm, legs ±2.55 on both faces, pads 0.2 mm from the edge (DRU) | x = 12.85 / 31.54 (`check_r7.JACKS`); GNSS on the left | Jack axis within x 3.6–42.4 (plug envelope fit). Corner holes need 3.8 mm top clearance to the jack bodies (the courtyard is ±3.55 mm about the axis). The sled saddles carry both plugs 25–30 mm aft; the coax loops stay off the camera-shroud side and are axially staggered (BAY), and the shroud's angular position is still unmeasured, so the side assignment may later be forced by the bay. Plug nuts are counter-held on the 6.5 mm flange; the jacks are staked flange-back to board edge after the RF tests (P3), so keep the edge region beside each flange free of parts the epoxy could reach. |
| **J1** (green DB128V-4P, C2915641; BAT+, GND, SW, SW) | Part identity and colour (F8, `check_actuators` 16); within 25 mm of both CH1 terminal centres (OWN, M3_R6); 14.5 mm tall (FIT) | Forward edge, rotation 180, entry facing +y, 1.9 mm from the edge (R6 onwards); x = 23 | The battery leads come from the aft battery bay (BAY), so they run past the board and turn into J1. A clean sheet must not let them cross the RF strip or lie over the top-side pyro block. Entry +y at the forward edge is the only entry that satisfies both with the strip aft; a long-edge entry is possible by fit but gives the wire about 6–7 mm to the wall (as J121/J124) for 15 A leads (Inference: too tight). The 7.7 A path J1 → Q120 → Q121 → J122 wants J1, the FETs and J122 close (MARGIN P1-9 "one corner"; D12). |
| **J124** (ARM, black DB128L-2P, C430601) and **J121** (IGNITER 1, same body) | Identity and colour; ARM / IGN legends and pin legends nearest their own pins (F8, `check_actuators` 11, D92); 14.4 mm tall (FIT); the ARM link fuse holder stays off the pyro block (ORDERING §7); uninsulated ferrules or solid wire bent within 2 mm of the entry (FMEA I-4) | Entries facing the long edges (J124 −x, J121 +x), 6.3–6.9 mm of wire room to the wall (`fit_check` SIDE_ENTRY); both in one y band, 26 mm apart | The igniter leads go forward to the charge wells (BAY); how the ARM link is fitted on the pad is open (FMEA H-6). A +y entry at the forward edge is possible by fit (outer faces within d ≤ 19.8), but J1 (22.2 mm) + two terminals (10.2 mm each across their pin row) = 42.6 mm > the 39.6 mm the bore allows at 14.4 mm height, and the corner holes take more: **at most two of the three screw terminals can face +y on the forward edge.** Any entry must keep the wire-room check (≥ R8's 6.3 mm for a wall entry, or the wire's bend radius to the next obstacle for an axial entry) and the owner's grouping. |
| **J122** (3 × 4 header, servo + GND, middle row RAW_ACT) | Vertical; mated envelope 23.5 mm, so the centre is within ±3.02 mm of x 23 at rotation 90/270 (±1.94 at 0/180) (FIT); middle row RAW_ACT so a reversed plug is harmless (DESIGN_ASSURANCE hard rule; `check_actuators` 7); tie holes beyond both ends (REQ) | (23, 75.7), rotation 90 | The servo leads arrive from the fin can by the external raceway (aft, BAY). The 7.7 A feed wants J122 near the FETs (D12, P1-9). The SRV05-4 clamp D121 belongs at J122 (R8 D7: a transient clamp at the entry; engineering). |
| **J9** (keyed JST GH 4P top entry, C161692) | Keyed GH, the four camera nets (F8, F10, `check_actuators`) | East long edge at rotation −90 (an R6 "edge block" with the radio/GPS ports, gone since R7) | Top entry: needs no edge. Its corner must stay within d ≤ 22.2 mm; R8's edge spot gives 0.03 mm margin, the board's worst. The camera sits in the shroud aft (joint +4…+47 mm); its lead length and side are open (BAY). |
| **J3** (HRO TYPE-C-31-M-12 USB-C) | Horizontal receptacle facing the airframe wall when installed, used only out of the bay (F9): **a long edge**; 0.45 mm overhang, so tab-routed rails, no V-cut; 2 mm tab keep-out; J3's locating holes at JLC's 0.20 mm NPTH minimum (DRU) | West edge at y 29–38 | Either long edge. ESD (D4) and CC pull-downs beside it (engineering). |
| **J123** (JST PH 2P top entry, pull-pin) | Advisory witness only (F9); RTV retention (no tie point, P3) | (12.2, 75.4); latch inboard, wires toward the axis | Free; mated 9.5 mm envelope (d ≤ 22.6). |
| **J2** (TC2030-IDC-NL SWD pattern) | Bare pattern, three NPTH, 0.508 mm to foreign copper (Tag-Connect note; DRU); pins 3V3 / SWDIO / NRST / SWCLK / GND / NC (`check_actuators`); no via in its pads (M2; R8 has none; the R7 J2.1 exception lapsed); coated over tape after the last SWD session, so it must lie where the pyro-block coat can be brushed without reaching U4's 3 mm zone (P3, ORDERING §5) | West edge (2.35, 42.75), top side | Free in place and, in principle, side. The probe head needs clearance from tall parts round the pattern (not modelled in `fit_check`; Inference: a few mm). NRST's bare pad is 0.483 mm from GND by the TC2030 pattern itself (fixed), which is why the NRST ≥ 1 MΩ gate exists. |

**Board orientation in the bay (BAY):** battery bay aft, then the leads and coax loop zone, then the board, then the
eyebolt nut and charge wiring, then recovery. "Aft edge" in F8/F10 is the edge toward the battery bay. Moving the jacks
to the forward edge (pass1_layout §3.2 judged it best for RF and cabling) needs an F8/F10 edit **and** a J1 that no longer
enters from the forward edge: an owner topic, not a clean-sheet freedom.

---

## 5. MCU orientation and pins

- **U1 position and rotation: free** (INH). Top side (fine pitch, heavy-on-top engineering rule R5 L10).
- **Contract pins (SAFE):** LQFP100 side 1 (pins 1–25) holds the gate PE4 (3), continuity PC0 (15), NRST (14), HSE
  (12/13) and the four servo PWMs PA0–PA3 (22–25); side 2 holds the arm and RAW_ACT senses (33, 34). The sentinels
  2, 4, 5, 16, 32 flank the gate, continuity and arm-sense pins (MARGIN P1-10). Changing any of them is a reviewed
  `check_actuators` change.
- **Consequence:** side 1 should face the pyro block and J122, and the RF pins (R8's map: pins 45–47 and 53–64, the
  side 2/3 corner and side 3) should face the strip. With the strip aft and the block and J122 forward, that is U1 with
  side 3 aft and side 1 forward, which is what R8's rotation 0 does. Other non-contract pins may move again, each with
  its DS12110 alternate function cited, the D5 rule (pins the ROM bootloader drives carry only their allowed net, an
  LED or nothing) and the D6 EXTI-sharing rules; any move rewrites `pin_table.tsv` and the binding note.
- **Local rules (REQ/engineering, gated):** decoupling at its pins; C29 ≤ 2 mm from U3.8 with a ≤ 3 mm direct route;
  C100 / C93 at U12 (`camera_bypass`); every series resistor at its driving end (`check_r7.SERIES`); R310 at the MCU end
  of the NSS lane (D4); the crystal Y1 with its In2 keep-out (R5 V1) and ≥ 5 mm from every RF part; VDDA's 1 µF near the
  pins (an R4 deviation a clean sheet can close); C24 (NRST) near pin 14, with a 3V3 pad on the same face beside it for
  ORDERING §5's NRST gate.

---

## 6. Bottom side and the sensors

| Item | Truly fixed | Inherited only |
|---|---|---|
| U4 IMU (LSM6DSV320X, consigned) | No vias or copper fill under it on its component side (P3); a 3 mm coating- and staking-free zone on both faces (ORDERING §5, ST TN1383); ±4000 dps / ≥ ±64 g (F1, F2: the part) | **Bottom side** (R5 L8: room on top, an engineering choice), rotation 0 (keeps the M3_R5 §3 axis map: roll = +gyro_Y), its place (R8 (10.0, 53.8), 13.2 mm from the roll axis). Any side or rotation change rewrites the axis map and the binding note, with a bench sign check either way. **Lever arm:** at r = 13.2 mm the centripetal term is 1.4 g at 1850 °/s and 6.6 g at 4000 °/s; under the axis (r ≈ 2.06 mm, the board thickness) it is 0.22 g and 1.0 g (Calc, ω²r). Near x 23 is a free improvement no requirement asks for |
| U5 barometer (MS5611) | Never washed or cleaned (TE); vented bay and opaque black foam; both LEDs dark from arming to landing (operating assumption); no tracks between its pad rows (TE land); reflow only (AN808) | **Bottom side** (R5 L8, "faces the sled, away from the LEDs"). On the bottom it sees two reflows, an open TE confirmation item; on the top it would see one (Inference: removes that item; the foam and dark LEDs already cover light). |
| Bottom parts | SMD only; ≤ 3.0 mm deep (sled); ≥ 1.5 mm from THT pads (pin tails), ≥ 3.5 mm from an M3 centre, ≥ 1.0 mm from a pyro via, ≥ 2.0 mm from TP122 (R5 L10, gated in R8's legaliser; D61's two MCU-side pyro vias excepted) | Which parts go bottom |
| Top-only parts | U30, U31 (single final reflow; U30 MSL 4, M1); J30/J31; terminals, connectors, U1, C84, C121, LS120 (heavy/tall, R5 L10) | — |
| Test pads | Bare 1.5 mm pads; 1.0 mm foreign copper on the exposed face (`check_r7.foreign_clearances`); exposed bottom lands count for standoff clearance (`fit_check`); none on BUS / IGN / OUT; TP122 on the bottom (`check_actuators` 4c) | Which face the other test pads use (DESIGN_ASSURANCE preferred the bottom; R8 has several on top) |
| Sled | Non-conductive under the whole bottom face, clear of pin tails, test pads, TP122 and bottom power pours; a tongue carrying both SMA plugs 25–30 mm aft | Its drawing follows the hole positions |

---

## 7. Power and servo placement constraints

| Item | Truly fixed | Class |
|---|---|---|
| 7.7 A path (J1 → Q120/Q121 → J122, four servos stalled) | IPC-2152 rise limits of D12 at every neck (RAW_ACT, BAT_IN ≤ 20 °C; ACT_FET_S ≤ 30 °C); the final copper DC-solved and bound to the board (F4); a thermal-camera stall test (ORDERING §5). MARGIN P1-9 asks for ≥ 10 mm equivalent mirrored on L1/L4, 6.1 mm only at pad necks, zero series vias, the parts in one corner (not met as written by R7 or R8) | OWN (D12) / REQ (F4) |
| Pyro bus after the load switch | RAW_ACT is Q121's drain, Q120's drain on BAT_IN, no pyro terminal pin on BAT_IN (`check_actuators` 3) | SAFE |
| Load-switch gate | Every ACT_* net pinned exactly; C120 gate-to-source (`check_actuators` 8a/8b); ACT_GATE / ACT_DRV pads in rule H | SAFE |
| Reverse hot-plug (F9) | The R4 model lumps the harness into one input node: D8, C80/C96, C89/C95/R166 and R167 at J1 (R8: 3.9–10.6 mm from J1.1, D76); U9's feed modelled (`step9/hotplug_feed.py`: 27 mm adds ≤ 0.002 V) | REQ (F9) premise |
| External switch legs | R80 / R165 470 kΩ on each side of the contact (F9, `check_actuators` 12): logically at J1.3 / J1.4, so keep them at J1 (R7 had R80 86 mm away) | REQ |
| Bucks U2, U8 | Maker layouts (Diodes AP63203 / AP63301: compact switching loop); ≥ 5 mm from every RF part (F10); L1 / L3 the deepest bottom parts | MAKER / REQ |
| Servo chain | MCU → 10 kΩ pull-down + SRV05-4 clamp → 1 kΩ 0805 → header (`check_actuators` 7); defined low through reset (F6) | SAFE |
| C84 (hold-up), C121 (RAW_ACT bulk) | Staked (P3, R14); not over or within 3 mm of U4 when staked; C84's 1.8 g mass on a mode antinode costs f1 (R8 C10) | REQ / engineering |

---

## 8. RF strip (F10)

### 8.1 What each rule rests on

| Rule | Basis | Class | Survives a re-layout as |
|---|---|---|---|
| Strip at the aft end, full width | F10 text (R7 pass 1's floorplan choice, written into F10) | REQ (place) / TEXT (y 0–23.5) | a strip boundary at y_f, recorded |
| In1, In2 GND only in the strip; per-layer net lists | F10; `check_r7.STRIP_F`, `check_r8.STRIP_B` / `STRIP_VIA` | REQ | net rules (geometry-free) |
| Nothing but GND under U31 on any layer | EBYTE E22-900MM22S manual §4.1 | MAKER | `U31_KEEPOUT` (all layers) on the body |
| Only GND and U30's own escapes under U30 on F.Cu and In1 | u-blox MAX-F10S IM §4.4 | MAKER | `U30_KEEPOUT` (F.Cu, In1) |
| Limiter on B.Cu under U30 | F10 text, from R7's design; the maker rule is only the F.Cu/In1 keep-out | TEXT | free with an F10 edit |
| 50 Ω GCPW for the ordered stack-up over unbroken ground | F10; u-blox IM §4.4 (CPW, ground on layer 2, 50 Ω, short, GND vias) | REQ / MAKER | W 0.30 / gap 0.25 mm in the DRU (net-based) is the qualified cross-section |
| ESD diode rated for the RF swing at each jack | F10; ESD103-B1-02 (VRWM ±15 V, 0.09 pF) | REQ / MAKER | part and chain order |
| Bias tap on the antenna side; pi network footprint (series 0 Ω fitted, shunts DNP, no paste) | F10; u-blox IM §4.3.4 (L4 > 500 Ω) | REQ | chain order |
| Bias current ≤ 50 mA into a short, ≥ 2.9 V at 15 mA | F10 (circuit) | REQ | circuit; copper drop negligible (Inference) |
| GNSS VCC series resistance ≤ 0.2 Ω | u-blox IM §4.1.1 (FB30 path) | MAKER | DC solve of the 3V3 → U30 VCC path |
| Separate ferrites and local decoupling for each module | F10 | REQ | placement at each VCC pin |
| RF parts ≥ 5 mm from switching regulators, MCU, crystal, fast digital lines | F10; u-blox IM §4.4 ("at least 5 mm to any RF component") | REQ / MAKER | `check_r8.rf_separation` (D17) |
| GND via fence between the strip and the rest | F10 (R8: ≤ 2.0 mm, openings ≤ 2.7 mm crossed by a lane, D16) | REQ | `check_r8.fence` on y_f |
| Jacks on the aft edge, ≥ 12 mm apart | F8, F10 | REQ | rule (section 4) |
| Modules on the top side, reflowed last; MAX-M10S fits U30's land; E22-900M22S needs a respin | M1, F10 | REQ | — |
| No RF-part pin on a pyro, arming, actuator, RAW_ACT, BAT_IN, BOOT0 or NRST net | F10 | REQ | `check_r7.SAFETY_NETS` (pad-level) |
| TXEN driven by DIO2 (U31 pins 9 and 19 joined) | F10 | REQ | forces a loop round U31 (section 8.2) |

### 8.2 What the maker pinouts force (MAKER)

- **U30 (MAX-F10S, LCC-18):** RF_IN (pin 11) shares its side with LNA_EN (13), VCC_RF (14) and SAFEBOOT_N (18), with
  GND at 10 and 12; UART, TIMEPULSE, VCC and RESET_N (2–4, 7–9) are on the opposite side. The RF line and the limiter's
  two DC leads leave the same side; U30_KEEPOUT bars their vias under the body and the module's T-shaped paste
  extensions cover 0.6 mm past the pad ends. That is the cause of R8's two allowlist detours (A2, A3: GNSS_LNA_EN 2.06×,
  GNSS_VCC_RF 2.37×). A clean sheet can remove them only by moving the limiter off B.Cu-under-U30 (an F10 edit) or by
  finding a via spot beside pins 13/14 outside the paste.
- **U31 (E22-900MM22S):** ANT (6) shares its side with GND (7), TXEN (9) and RXEN (10); SPI and BUSY (11–15) are on a
  second side, VCC and NRST (1, 3) on a third, DIO1 and DIO2/TXEN (19, 20) on the fourth. TXEN's pins 9 and 19 sit on
  opposite sides, and nothing may cross the pad field, so **the TXEN loop must go round the module**, crossing either
  the SPI side, the VCC/NRST side or the RF line (R8: one allowlist-free detour on D10's keep-out baseline). This is
  geometry-forced by F10 + the maker; only an F10 change (TXEN from an MCU GPIO) removes it.
- **Kinghelm jack:** centre pin Ø0.95 × 4 mm; legs 0.9 mm square at 4.2 / 6.0 mm spacing; DC–6 GHz, VSWR ≤ 1.35.

### 8.3 Code constants that only encode R7's strip (INH)

| Constant | R7/R8 value | Replace with |
|---|---|---|
| `check_r7.JACKS` | x 12.85 / 31.54 | the jacks found by footprint (`M3_SMA_KH_KE8_EDGE`) on the outline's minimum-y edge |
| `check_r7.STRIP_Y`, `FENCE_Y` | 23.5, 23.3 | one recorded strip boundary y_f; the fence row within ±0.3 mm of it |
| `check_r7.U31_BODY`, `MODULE_GND` | (24.86, 9, 34.86, 19); U30 box (5.36, 11.25, 15.46, 18.65) | the module body boxes in each footprint's frame (EBYTE 10 × 10; u-blox DS Table 21 10.1 × 9.7), transformed by the footprint's position and rotation (`route_check.MODULE_BODIES` already does this for U31) |
| `check_r7.STITCH_ACCEPTED` | GNSS west 4.0, east 2.7 | removed: one limit for every side (section 8.5 R-7) |
| `R7_J3x_launch_In1` names and coordinates | x ±0.9 about each axis, y 0–4.6 | a launch area keyed to each jack, checked in the jack's frame |
| `check_r8.RIGID_BASELINE` strip groups | `strip_parts`, `strip_rf_copper`, `strip_gnd`, `strip_rule_areas`, `strip_gcpw` | the rules of section 8.5 |
| `check_r8.BUCK_PARTS` / `NOISY_PARTS` (refdes lists) | C6–C9, C72–C76, U7, TP71; U1, U3, Y1 | roles derived from nets (every part on a switch-node net or a buck's input/output net, the MCU, the flash, the crystal) |

### 8.4 Analyses to redo for a new strip geometry

1. **GCPW cross-section and impedance.** Sample every RF track at 0.05 mm: width, gap to F.Cu GND on each side, In1 GND
   beneath. Every section with the qualified cross-section (W 0.30, gap 0.25–0.30 as filled, In1 under ±(W/2 + gap +
   0.3)) inherits R7 pass 2's solve (50.3 Ω coated, εeff 3.18; JLC engine 50.24 Ω). Any new cross-section (a different
   W or gap, a missing side ground, a bend region, a section over an In1 relief) needs a new 2-D field solve and a JLC
   impedance-engine run. **The solver is not in the repository** (pass2_rf §7 gives the method: 2-D finite volume,
   symmetric half-domain, grounded lid at 3 mm, SOR to 1e-8); rebuild it as a tool so it can be re-run on each build.
2. **Launch.** If each jack's land, its In1 cut-out (x ±0.9, y 0–4.6), the 0.30 mm launch gap, its eight stitching vias
   (±1.45 at y 1.0 / 2.3 / 3.6, ±1.25 at y 4.15) and In2 GND under the cut-out are congruent in the jack's frame, the
   49.0 Ω launch carries over; otherwise re-solve (without the cut-out the pad is 21–23 Ω).
3. **Discontinuities and return loss.** Re-list every discontinuity on each line (0402 pads on the line, about
   35–39 Ω over 0.5–0.6 mm; the bias-tap pad; the DNP shunt stubs, R7 0.94 mm; bends; the module pad entry) and re-run
   pass2_rf §3.12's cascade (R7: RL ≈ 19–21 dB GNSS, ≈ 25 dB radio; Inference). Line length jack-pad end to module pad
   edge was 5.76 mm (GNSS) and 4.76 mm (radio).
4. **Stitching and reference.** Side gaps along each line (R7/R8: GNSS 3.90 / 2.65, radio 1.55 / 1.55 mm), the fence,
   strip GND reach (R8 F.Cu 3.04, B.Cu 3.49 mm against 4.0), RF ground pads solid with a GND via ≤ 0.6 mm, In1/In2
   coverage of the strip (R7: F.Cu 76.7 %, B.Cu 92.0 %, In1 95.1 %, In2 96.6 %), signal-via antipads clear of the RF
   keep-in. F10's quoted gap figures are rewritten from the new measurement.
5. **Keep-outs and module ground.** The two rule areas re-derived from the module bodies; GND fill sampled every 0.2 mm
   under U31's body on In1 and In2 and under U30's keep-out on In1 (`module_ground`).
6. **Chain topology.** Jack → ESD → bias tap (GNSS) → pi → module, in path order; ESD within about 1 mm of the jack pad
   end (R7 0.8 mm); L30 on the line with no stub, C302 at its cold end (R7 0.92 mm); DNP lands unpasted.
7. **Separations (F10, D17).** Every RF part ≥ 5 mm (courtyards) from the restricted parts and, in plan view, from fast
   lines. R8: nearest part 5.94 mm (R306–U1), nearest fast line 5.08 mm (R306–USB_DM).
8. **Coexistence (pass2_rf §3.10–3.11).** Radio interface lines to U30's body and to GNSS RF copper (R8: RXEN 5.44 /
   6.00 mm, BUSY 5.94, SPI ≥ 6.44 mm; DIO1 16.84, NRST 19.25); RF line to RF line (R7/R8 15.45 mm), jack to jack
   (18.69 mm), module courtyards (7.66 mm); supply separation (FB30 / FB31, decoupling distances to the VCC pins:
   C311 1.8, C312 2.0, C310 3.6 mm from U31.1); HSE and radio-crystal harmonics (arithmetic, levels unknown, bench).
   The ≥ 39 dB isolation and the pyro immunity under +22 dBm stay bench items (S21 J30↔J31 ≤ −50 dB target; keyed C/N0
   per band).
9. **Limiter thermal and DC.** Q30's copper (R7: 0.2 mm on B.Cu, a 2–3× RθJA note) re-estimated; the VCC_RF and
   GNSS VCC path resistances (≤ 0.2 Ω) solved.
10. **Mechanics.** Jack plug envelopes (fit), corner-hole washer clearance, staking surfaces at each flange, the sled
    tongue and saddle positions, plug-nut depth under the board (2.6 mm), coax loop side; the vibration model with the
    jack and module positions; MARGIN R14 (R7) for the jacks re-read on the new edge position.
11. **Records.** The VNA tuning model (shunt-trace lengths), ORDERING §5's RF steps and coordinates, F10's quoted
    figures.

### 8.5 Proposed rule-based checks (replace the five strip hash groups; none weaker)

| Check | Asserts | Not weaker than |
|---|---|---|
| **R-1 strip_extent** | One recorded y_f. Every strip part's courtyard lies at y < y_f + 0.3 (the strip parts: modules, jacks, ESD, bias tap, pi network, limiter, module feeds and module-end interface parts); no non-RF part's pad lies at y < y_f; the strip spans x 0–46 | F10's strip, by content instead of by R7's 23.5 |
| **R-2 strip_layers** | `rf_strip` with y_f: In1 / In2 GND only, F.Cu and B.Cu net lists, no non-GND pour in the strip. STRIP_B tightened to GND + the limiter nets (+ RADIO_TXEN only if its loop runs on B.Cu, with its B.Cu length ≤ R8's) | R8's STRIP_B (it already removed NSS and DIO1) |
| **R-3 jacks** | Each SMA footprint on the top side, rotation 0, centred on the outline's minimum-y edge (±0.005); ≥ 12 mm c-c; no paste; legends; plug envelope fit | `check_r8.check_contract` minus the x constants |
| **R-4 launch_congruent** | For each jack, in its own frame: the In1 cut-out rectangle equals x ±0.9, y 0–4.6 (±0.01), In1 only, no fill; In2 GND under it grown 0.3 mm (`launch_reference`, jack-relative); its eight stitching vias at the qualified relative positions (±0.05); F.Cu GND ≥ 0.30 mm from the centre pad (DRU) | the hash of R7's launch (it allows only translation along the edge, which keeps the qualified field) |
| **R-5 gcpw_rule** | Along every RF track at 0.05 mm: W 0.30 (DRU); F.Cu GND present on both sides at a gap of 0.25–0.30 mm, except inside declared discontinuity windows (a part pad on the line, a T to the bias or shunt stub, the module pad entry, the launch), each ≤ 0.6 mm long, with no more windows per chain than R7 had (GNSS: D30, L30, R304 with its two stubs; radio: D31, R316 with its two stubs); In1 GND beneath across ±(0.15 + 0.25 + 0.30) mm outside the launch | `strip_gcpw` (R7's exact profile) for every section; anything outside the qualified profile fails unless re-solved and recorded |
| **R-6 rf_line_length** | Jack pad end to module RF pad edge ≤ R7's 5.76 mm (GNSS) and 4.76 mm (radio) + 0.5 mm, with ≤ 2 bends per line | R7's lengths (u-blox: "as short as possible") |
| **R-7 rf_stitching** | One limit, no named ceilings: side gaps ≤ 2.5 mm on both sides of both lines (F10 tolerates up to λ/20 ≈ 4.4 mm; R7 needed 4.0 / 2.7 ceilings only because L30/C302/C303 left no via spot); the D16 fence on y_f; strip GND reach ≤ 4.0 mm; RF ground pads solid with a via ≤ 0.6 mm; strip ground coverage per layer ≥ R7's figures (reported) | `STITCH_ACCEPTED` and `strip_gnd` |
| **R-8 module_keepouts** | `U30_KEEPOUT` (F.Cu, In1) and `U31_KEEPOUT` (all four layers; on B.Cu and In2 the whole body) cover the footprint-derived body boxes; GND under them sampled at 0.2 mm (`module_ground`, `u31_body_keepout` with derived boxes); no non-GND track or via inside (DRU) | `strip_rule_areas`, `U31_BODY`, `MODULE_GND` |
| **R-9 chain_topology** | Path order jack → ESD → bias tap → pi → module along each line; ESD ≤ 1.0 mm (path) from the jack pad end; the bias inductor's line pad on the line (no stub); C302 ≤ 1.0 mm from L30's cold pad; DNP shunt stubs ≤ 0.94 mm | R7's measured chain |
| **R-10 rf_separation** | D17 unchanged in substance, with the restricted set derived from net roles | D17 |
| **R-11 coexistence_geometry** | Every RADIO_* non-RF copper ≥ 5.0 mm from U30's body box and ≥ 6.0 mm from GNSS RF copper; RADIO SPI copper ≥ 6.0 mm from U30's body; U30–U31 courtyards ≥ 5 mm (u-blox IM §4.4); GNSS RF copper ≥ 15.0 mm from radio RF copper unless the RF reviewer re-derives the coupling (R7 15.45 mm; Inference < −60 dB) | pass2_rf §3.10 / §3.11 accepted figures and R8's measured ones |
| **R-12 rf_supply** | FB30 and FB31 separate; each module's decoupling within R7's distances of its VCC pin (C311 ≤ 1.8, C312 ≤ 2.0, C310 ≤ 3.6 mm from U31.1; C300 / C301 likewise at U30's VCC); GNSS VCC path ≤ 0.2 Ω (DC solve) | pass2_rf §3.11, u-blox IM §4.1.1 |
| **R-13 rf_vs_pyro** | Report, and gate at a value the RF and pyro reviewers set (proposal: ≥ 40 mm, Inference), the distance from U31, J31 and the radio RF line to any PYRO1_* or ARM1_* copper and to J121/J124 (R8: U31–J121 68.4 mm) | R7 pass 1's "radio ≥ 68 mm from J121/J124" rationale; F10's pyro immunity is still a bench item |

---

## 9. CH1 pyro block (F7, F8, AGENTS §2)

### 9.1 What each rule rests on

| Rule | Basis | Class | Geometry-free? |
|---|---|---|---|
| ARM break: PYRO1_BUS = {J124.1, R134.2, R132.1}, PYRO1_IGN = {J121.2, R134.1}, RAW_ACT on J124.2 only | AGENTS §2.1, F8; `check_actuators` 1 | SAFE | yes (netlist) |
| Rule E: RAW_ACT ≥ 1.0 mm from bus and igniter copper, every layer | F8; DRU | SAFE | yes |
| Rules A–D, F, A2 (0.3–0.5 mm, every layer) | F8; DRU (R4 pass 2–12) | SAFE | yes |
| Rule G: gate nets ≥ 0.3 mm from every other live net **inside PYRO_BLOCK** | F8; DRU | SAFE | **no: depends on the PYRO_BLOCK area** |
| Rule H: every exposed bus, igniter, drain and RAW_ACT pad ≥ 1.0 mm from every sense and gate pad (ACT_GATE / ACT_DRV included); every midpoint pad ≥ 1.0 mm from every gate pad; each FET's own pads exempt | F8; DRU (R4 passes 13–14) | SAFE | yes (pads) |
| Battery-live copper (BAT_IN, ACT_FET_S) ≥ 1.0 mm from bus, igniter and drain copper, same layer | F8 (R8 text); `check_r8.battery_pyro` (D85, D103) | SAFE | yes |
| No inner RAW_ACT / BAT_IN within 2.5 mm (plan view) of BUS / IGN / OUT copper; J124's own pads exempt | `check_r8.inner_power_pyro` (D18) | SAFE | yes |
| PYRO1_GATE_N ≥ 0.5 mm from servo PWM copper, same or near layer | `check_r8.gate_servo` (D19) | SAFE | yes |
| Gate network: 220 Ω series, 1 kΩ pull-down on GATE_N (MCU side), 10 kΩ + 220 nF gate-source, AON7524; defined off in reset | AGENTS §2.4; MARGIN P0-1, P0-2; `check_actuators` 4–4c | SAFE | yes (netlist, values, codes) |
| Sentinel pins flank the gate, continuity and arm-sense pins | MARGIN P1-10; `check_actuators` 5 | SAFE | yes |
| Divider tops 2 × 5.1 kΩ in series, bottoms 2 × 2 kΩ in parallel, 4.7 kΩ at each ADC pin; no part spans RAW_ACT and RAW_ACT_SENSE | F8; `check_actuators` 6b; M3_R4 passes 9–12 | SAFE | yes (netlist) |
| R134 2 Ω 2 W pulse; cold pull-up R131 10 kΩ via D120 BAT54A | F7, FMEA H-1; `check_actuators` 1b, 1c, 10 | SAFE | yes |
| No test pad on BUS / IGN / OUT; TP122 (bare gate pad) on the bottom; bottom parts ≥ 2.0 mm from TP122; bare test pads 1.0 mm from foreign copper | DESIGN_ASSURANCE; `check_actuators` 2, 4c; R5 L10; `check_r7.foreign_clearances` | SAFE | yes |
| Local conformal coating of the block, J2 taped and coated; keep-offs (U4 + 3 mm, U5 port, modules, jack threads, connector mating faces, LS120, other test pads; TP122 coated last) | P3; MARGIN §4.13, P1-13; ORDERING §5 | REQ | the mask list is part-based; the distances are geometry |
| Terminal identity and legends | F8; `check_actuators` 11; D92 | SAFE | yes |
| Shorted-igniter current limit; ≤ 20 ms pulses | F7; sim_r2 | REQ | circuit |
| Pyro traces sized adiabatically, not by IPC-2221 (1 mm × 1 oz rises ~6 K at 8.8 A / 20 ms) | MARGIN P1-9 | engineering | yes |

**Inherited only (INH):** every part position and rotation inside the block, its copper, the exit vias, the In2
ARM1_SENSE link (`RIGID_IN2`), `CH1_PADS` (R5's pad distances), `EXIT_VIAS`, the PYRO_BLOCK rectangle (x 4–42,
y 84–114.4), the terminals' entry directions, TP122's in-pad via (A8).

### 9.2 What R7/R8 inherited and a clean sheet should not keep

Measured on R8 (`block_probe.py`, `hull_probe.py`, M3_R8):
- **R8's PYRO_BLOCK rectangle holds copper of 25 named nets** (plus two unconnected pads), among them the whole battery band (BAT_IN, BAT_SW_*, BAT_DAMP), U9's
  network (BAT_ENABLE, BAT_FAULT_N, BAT_OVLO), the actuator switch (ACT_GATE, ACT_DRV, ACT_EN, ACT_FET_S) and
  RAW_PROTECTED. The rectangle was sized in R4 for a two-channel block plus J1, not for the block itself.
- **Inside the convex hull of the 22 CH1 courtyards grown by 1 mm** (x 3.5–42.5, y 80.4–100.1, 627 mm²), nine foreign
  nets have copper: 3V3 (D120's anode, by design), ACT_FET_S and BAT_IN fills (B.Cu), ACT_GATE, BAT_ENABLE, BAT_FAULT_N
  (tracks and vias on F.Cu and B.Cu), BAT_OVLO, RAW_ACT (J124.2's feed and fills, by design) and RAW_PROTECTED (F.Cu).
  BAT_ENABLE runs on F.Cu 0.216 mm from bare R175.2 (ARM1_SENSE) and 0.70 mm from both R134 pads.
- **Armed-live copper is confined:** no PYRO1_BUS / IGN / OUT copper lies outside the rectangle.
- **Gate-net neighbours:** PYRO1_GATE_N runs 40 mm (F + B, one via) with ARM1_SENSE 0.22 mm away and the In2 3V3 area
  0.45 mm from its via; PYRO1_CONT runs 0.30 mm beside it for 33.5 mm. A hard GATE_N–ARM1_SENSE short leaves the gate at
  about 0.37 V with the MCU in reset (ORDERING §5 note, R8P1-PYRO-04), against the AON7524's 0.4 V minimum threshold at
  25 °C (lower hot): a margin that rests on the lane layout, not on a rule.
- **Rule G's margin is zero by construction** (0.300 mm, six pairs within 0.1 mm), because G applies to the whole
  33.5 mm GATE_N segment that reaches into the area.
- **The gate test pad's via (A8)** is the board's only AGENTS §3 instance; it exists only because the block was rigid.
- **Margins inherited from R4:** rule H 1.025 mm (Q124.5–R129.2), B 0.67, C 0.377, D 0.501, E 1.30, F 0.70, G 0.300.

### 9.3 Physical facts that do bind the block (MAKER / FIT)

- Terminal pitch 5.08 mm, pads Ø2.6 mm: J124.1 (BUS) to J124.2 (RAW_ACT) edge gap 2.48 mm, so the ARM break inside the
  terminal is the maker's geometry.
- The terminals are THT: their bus, igniter and drain pads are **bare on B.Cu too**, so the bottom under them is part of
  the block (rules D, F, H, D85 and R5 L10 all act there).
- R134 is a 2512 (courtyard 8.2 × 4.3 mm), Q124 a DFN 3 × 3 (AON7524); the 0402 divider and gate parts.
- The fire loop: RAW_ACT → J124.2 → link + 5 A fuse → J124.1 → R134 → J121.2 → igniter → J121.1 → Q124 → GND
  (1.3–2.8 A for ≤ 20 ms, 4.1 A into a shorted igniter). F7's budget assumes ≤ 0.3 Ω of leads, fuse and harness; the
  board copper is small but must be solved on the final copper (F7: "revalidate on the final copper").

### 9.4 Analyses to redo for a new block geometry

1. **DRC A–H and A2** on the whole board (automatic), plus the closest approach and location per rule
   (`step9/requalify.py pyro_rules`) for the record.
2. **Rule H liveness** (R4 pass 14's method): on a scratch copy, seed faults (each closest H pair moved 0.05 mm inside
   1.0 mm; the rule's minimum lowered; the rule deleted, moved first or narrowed; RAW_ACT or ACT_GATE dropped from it)
   and confirm DRC or `check_actuators` fails each.
3. **The R4 solder-bridge residual table** (M3_R4 §1n–§1o and §2): enumerate every pair of exposed pads (same face,
   mask openings, different nets) within 1.0 mm (report to 1.5 mm) where either net is a pyro, arming, sense, midpoint,
   gate, actuator-switch gate, RAW_ACT, battery-live or 3V3 net; give each pair its single-bridge consequence (fires;
   puts live copper past a divider top; overstresses an ADC pin; bypasses the ARM break; turns the actuator switch on with
   the power switch open; shows in the cold test; tolerated: shorts one divider half or two nodes at nearly equal voltage)
   and the cold-test signature from M3_R4 §3. R4's tolerated classes (drain vs its own midpoint, drain vs its own COLD
   pad, COLD vs its own midpoint) are the only ones allowed.
4. **Divider fault tolerance:** the circuit analysis (any single shorted or open resistor leaves the node ≤ 1.4 V,
   3.3 V at the 19.9 V clamp, an armed igniter ≤ 1.4 mA; two faults ≤ ~1 mA into the pin, ≤ 9.4 mA through the igniter)
   is placement-free and holds; re-prove only its layout preconditions: each half a separate part, no single bridge
   shorting a whole top (rule H covers drain/bus/RAW_ACT pad vs node pad), the 4.7 kΩ at the MCU end with short *_MCU
   nets (R8: 2.1 / 2.6 mm), and the node-side lanes' neighbours (a bridge there sees the divider's Thevenin source, not a
   stiff one; list each neighbour and the pin current it could force).
5. **Coating and leakage distances** (`step9/requalify.py bare`): bare pyro-gate copper (R126.2, C126.1, R128.1, Q124.4,
   TP122) and the actuator switch's bare gate copper to the nearest bare armed-live and always-live pad on the same face
   (R8: gate to bus/igniter 1.027–2.001 mm; no bare 3V3 / RAW_ACT within 5 mm of a pyro gate pad; ACT gate to armed-live
   2.88 mm); GND beside the drain (rule D 0.50 mm; a ≤ 24 Ω leak passes the e-match no-fire current, Inference); J2's
   NRST pad; the coating mask list and region (block outline + J2) against the coating keep-offs; ORDERING §5's text.
6. **Gate reset behaviour:** topology and values (`check_actuators`, unchanged); sentinels (unchanged pins); the
   bootloader-entry binding (PE4 low, then R127 holds the gate; F10, D6.8; unchanged); **the GATE_N / GATE lane
   neighbours** with the gate voltage each hard short would give with the MCU in reset (R127 1 kΩ to GND, 220 Ω / 10 kΩ
   divider to the gate): a sense node through its divider Thevenin (ARM1_SENSE about 0.75 V open-circuit through about
   0.9 kΩ gives 0.37 V), any driven logic line or rail fires (Calc / Inference); the gate network parts within a few mm
   of Q124 (R8: R128 1.3, C126 2.6, R126 4.4, R127 5.3 mm centre to Q124.4) so PYRO1_GATE stays short (R8 5.3 mm).
7. **Exits** (`requalify.py exits`): length, layers, vias and nearest nets of GATE_N, CONT, ARM1_SENSE and their MCU
   sides; D19; R5 L10 at every pyro via (D61's two MCU-side exceptions re-measured).
8. **Block purity and neighbours** (`step9/pyro_neighbours.py`): every net within 3 mm of armed-live copper, bare or
   covered (R8: 7 nets; R7: 23).
9. **TP122:** its gate via either gets a GND via within 1.5 mm (removing A8) or keeps a measured reason; the leakage
   gate's probe access on the bottom.
10. **Fit and harness:** terminal bore margin, wire room or axial bend room for the chosen entries, the fuse-holder
    keep-off text, "never probe R134 armed" and the GND probe points named in ORDERING (keep them away from bare bus and
    igniter copper).
11. **Fire-loop copper** solved (`tools/dc_solve.py` on the PYRO1 nets) for F7's budget, and the adiabatic note.
12. **Pyro RF immunity geometry** (R-13) for the record; the bench test stays.

### 9.5 Proposed rule-based checks (replace `ch1_parts`, `ch1_copper`, `pyro_block_area`, `CH1_PADS`, `EXIT_VIAS`, `RIGID_IN2` and `check_actuators` 15b's rectangle)

| Check | Asserts | Not weaker than |
|---|---|---|
| **P-1 block_area** (replaces 15b's coordinates) | Exactly one PYRO_BLOCK rule area, one outline, on all four copper layers, restricting nothing (as 15b), that **contains** every CH1 part's courtyard grown by 1.0 mm, all copper of PYRO1_GATE, PYRO1_BUS, PYRO1_IGN, PYRO1_OUT, PYRO1_COLD and the *_MID nets, and the CH1-side copper of PYRO1_GATE_N, PYRO1_CONT and ARM1_SENSE up to 3 mm past the last CH1 pad | 15b's rectangle: rule G then covers all block gate copper wherever the block is; the rectangle covered no gate copper the derived area would miss |
| **P-1b gate rule scope (optional strengthening)** | Rule G applied to PYRO1_GATE and PYRO1_GATE_N everywhere outside U1's courtyard (DRU `!A.intersectsCourtyard('U1')`), not only inside PYRO_BLOCK; re-pin DRU_SHA / PYRO_RULE_SHA after review | rule G as written, and REQUIREMENTS' accepted risk "gate-net spacing outside the pyro block is the board's 0.15 mm default" (which it would retire) |
| **P-2 armed_live_confined** | Every PYRO1_BUS / IGN / OUT pad, track and via lies inside PYRO_BLOCK | R8 (holds) |
| **P-3 block_purity** | Inside the CH1 hull grown by 1.0 mm: on F.Cu only CH1 nets, GND, RAW_ACT (J124.2's feed) and 3V3 (D120's anode); on In1 and In2 GND only; on B.Cu, foreign copper only ≥ 1.0 mm from CH1 copper and foreign bare pads ≥ 1.5 mm from the terminals' bottom pads | R8's block (BAT_ENABLE, RAW_PROTECTED and others cross it): strictly stricter |
| **P-4 rule_h_live** | The seeded-fault suite of 9.4 item 2 runs in the test suite on every build | R4 pass 14's one-off proof |
| **P-5 bridge_table** | 9.4 item 3 as a gate: no pad pair < 1.0 mm in a forbidden consequence class; the tolerated pairs listed with their signature | R4 §2's residual list (no new class) |
| **P-6 bare_gate** | Bare pyro-gate and actuator-gate pads ≥ 1.0 mm from every bare always-live pad (3V3, RAW_ACT, BAT_IN, ACT_FET_S, RAW_PROTECTED, VLOGIC, VBUS, CAM_5V and the like), each part's own pads exempt; bare pyro-gate copper ≥ 1.0 mm from bare bus and igniter copper (R8 1.027 mm) | R4's accepted 0.79 mm 3V3-to-gate residual (gone since R6) and R8's measured figures |
| **P-7 gate_guard** | PYRO1_GATE and PYRO1_GATE_N copper ≥ 0.5 mm, on the same layer and on layers < 0.5 mm away through the stack, from every non-GND net whose hard short would put ≥ 0.2 V on the gate with the MCU in reset (every rail and driven logic net; each sense node by its divider Thevenin), outside U1's courtyard and the gate network's own parts | D19 (servo PWM only) and R8's layout (would fail it at ARM1_SENSE 0.22 mm and PYRO1_CONT 0.30 mm): stricter |
| **P-8 sense_end** | R168, R170, R172 at the MCU end: *_MCU nets ≤ 3 mm of copper (R8 2.1 / 2.6 mm); the divider tops at the block (no armed-live copper leaves the block to reach a divider) | R8's measured layout; F8's purpose |
| **P-9 test_pads** | `check_actuators` 2 and 4c (unchanged); bottom parts ≥ 2.0 mm from TP122 promoted from the legaliser to the gate; bare test pads 1.0 mm (unchanged); the PYRO1_GATE layer change has a GND via within 1.5 mm (AGENTS §3, removes A8) | R8 (A8 allowlisted) |
| **P-10 coat_region** | The coat region (PYRO_BLOCK outline and J2's courtyard) ≥ 3 mm + 2 mm brush margin (Inference) from U4's body on both faces, and contains none of U5, U30, U31, LS120, the jacks, J3, J9, J122, J123 or a test pad other than TP122 | ORDERING §5's keep-offs (procedure only today) |
| **P-11 terminal_entry** | Each terminal's entry face and its wire room (wall entry ≥ R8's 6.3 mm at 5 mm height, or bend room for an axial entry), as `fit_check` SIDE_ENTRY generalised to any entry direction | R8's wire room |
| **Kept unchanged** | `check_actuators` 1–14, 16 and the DRU text pins (DRU_SHA, PYRO_RULE_SHA); `battery_pyro` (D85), `inner_power_pyro` (D18), `gate_servo` (D19), `rf_strip` safety nets, the J1 25 mm grouping | — |

`CHECK_ACTUATORS_SHA` in `check_r8` then pins the reviewed R9 version of `check_actuators.py` (only 15b changes).

---

## 10. Replacing the rigid contracts: the full map

| R8 contract | Where | R9 replacement |
|---|---|---|
| `rigid` group `outline` | `check_r8.RIGID_BASELINE` | `check_contract`'s 46 × ≤ 120 test (exists) + rectangle with corners on (0, 0), the length recorded |
| `m3_holes` | same | `fit_check.support_check` (exists) + hole diameter 3.2 exact + f1 gate (M-2 below) |
| `j122_tie` | same; `fit_check.RETENTION_HOLES`; `r8_legalise.TIE` | M-3: exactly two Ø3.2 holes on J122's long axis beyond each end (1–4 mm past the courtyard ends), the tie line crossing all four plug positions, a 4 mm channel (±2 mm about the hole-to-hole line) clear of bottom courtyards; RETENTION_HOLES derived from J122 |
| `j1` | same | M-4: J1 identity (pinned code), ≤ 25 mm from both terminal centres (exists), entry face ≤ 2 mm from its edge (or the owner-set direction), fit |
| `pyro_block_area` | same; `check_actuators` 15b | P-1 |
| `ch1_parts`, `ch1_copper` | same | DRC A–H/A2 + P-2 … P-11 |
| `CH1_PADS` pairwise distances | `check_r7`, run by `check_r8.check_contract` | removed (P-4, P-5 carry the bridge qualification) |
| `EXIT_VIAS`, `RIGID_IN2` (In2 ARM1_SENSE link) | `check_r8` | removed; D20 with no exception |
| `strip_parts`, `strip_rf_copper`, `strip_gnd`, `strip_rule_areas`, `strip_gcpw` | `check_r8.RIGID_BASELINE` | R-1 … R-12 |
| `JACKS`, `STRIP_Y`, `FENCE_Y`, `U31_BODY`, `MODULE_GND`, `STITCH_ACCEPTED`, launch-area names | `check_r7` (imported) | derived values (section 8.3) |
| `actuators_unchanged` (byte hash) | `check_r8` | the reviewed R9 `check_actuators.py` hash |
| `route_check` profile r8 (A1–A3) | `tools/route_check.py` | a profile r9 starting empty; A1 should not recur (P-9); A2/A3 recur only if the limiter stays under U30 |
| Fit margins ≥ R7's per category (D39) | `r8_plan` / legaliser | M-5: every `fit_check` category ≥ 0 and ≥ R8's figure (J9 mated 0.03, J122 0.71, J3 0.89, terminals 1.15, C84 1.37, worst bottom 2.36, nearest bottom pad to a support 4.45, nearest exposed top pad 5.01 mm), or a recorded reason |
| Vibration | P2 record | M-2: plate model (`step9/plate_model.py`) on the final board: f1 (pinned, D 5) ≥ R8's accepted 209 Hz as the gate, R6's 241 Hz as the target |
| IMU | D13 / D38 | M-7: bottom, rotation 0 (or a recorded new map); IMU rule areas derived from the footprint; lever arm ≤ R8's 13.2 mm (target ≤ 3 mm) |
| Bottom keep-outs (R5 L10) | `r8_legalise` | promoted to the gate (they are in the legaliser only) |

---

## 11. Qualifications a clean sheet invalidates

| Qualification | Tool in the repo? | R9 must |
|---|---|---|
| F4 DC solve and the D12 necks | yes (`tools/dc_solve.py`, `--necks`, `run_dc.sh`) | re-solve at 0.05 mm, bound to the new SHA; rewrite F4's line |
| Pyro spacing, bridge table, coating / leakage, gate neighbours, exits, A8 | partly (`step9/requalify.py`, `pyro_neighbours.py`); the bridge-consequence table and the seeded-fault suite are new | section 9.4 |
| RF GCPW, launch, discontinuities, stitching, coexistence geometry | partly (`check_r7` / `check_r8` RF functions); **the field solver is not in the repo** | section 8.4 |
| Absolute critical-reference audit | yes (`tools/reference_audit.py`, D74) | re-run; R8 missed R6b (0.1107 > 0.08) with measured causes |
| Reverse hot-plug premise | yes (`step9/hotplug_feed.py`) | re-run if the input parts or U9 move |
| Vibration | yes (`step9/plate_model.py`) | re-run on the new holes and heavy parts |
| IMU axis map / lever arm | — | record; bench sign check |
| Firmware binding | `step9/binding_note.py` | new note; pin-table review |
| Fab package, CPL rotations | yes (`r8_fab.sh`, `fab_manifest.py`, `jlc_orient.py`) | regenerate; per-footprint corrections survive |
| Cost and stock (M3) | yes (`tools/jlc_cost.py`) | unchanged BOM keeps $106 / 52 codes; rerun within 24 h of ordering |
| Deviation list and owner acceptance (M2) | `route_check`, `step9/m2_sweep.py` | a new list, a new dated acceptance |
| ORDERING coordinates (tabs, mark, probe points, NRST gate pads, sled, staking, coating) | `requalify.py` (tabs, mark, probes, holes, edges) | regenerate |
| Review history | — | a new review loop (two consecutive passes with no Critical or Major) |

**Placement-free and surviving:** the circuit analyses (F6 ride-through, F7 budget except its copper term, F8 divider
faults, limiter currents, gate-network margins, MARGIN tables), the DRU rule texts, `check_actuators` 1–14 and 16, and the
topology-based bench gates (static, leakage and dynamic pyro gates, RF immunity, plug-out cold test, antenna short,
radio reset hold, coexistence and S21 targets, NRST ≥ 1 MΩ, hot-plug).

---

## 12. Requirement and record text a clean sheet must update (TEXT)

- F10: the strip's coordinates and board size; the quoted stitching gaps; "limiter on B.Cu under U30" if the limiter
  moves; the R8 references to rigid strip copper and D15's groups; "since R7 pass 4 … check_r8 measures …".
- F8: the R8 references to rigid CH1 copper (`check_r8.battery_pyro` text stays).
- P1 ("R7 and R8 are 46 × 118"), P2 (R8 f1 and C10), P3 (unchanged in substance), F4 (R8 solve), M2 (the R8 list and
  acceptance), M3 (R8 cost), and a new "R9 acceptance" clause naming the R9 contracts instead of `check_r8`'s hashes.
- AGENTS §1 rows (R8 rigid copies, positions).
- ORDERING §3–§7 (all coordinates, tabs, mark, probe and coat points, sled hole list, J124 "unmoved", PYRO_BLOCK extent).
- Parent `docs/VEHICLE.md` stack row: board length, hole coordinates, jack overhang, board position.

---

## 13. Owner decisions a clean sheet needs or may want

**Needed before or during R9 (each is a real lever):**
1. **Board length target** (P1 is an objective): accept a placement study over about 90–110 mm (section 2.3).
2. **Mid-span support position** (any point in the middle third; an interior or right-edge point would raise f1):
   updates the VEHICLE row and the sled.
3. **Terminal entry directions** (J121 / J124 at the long edges as now, or one of them axial at the forward edge) and
   J1's entry, within the 25 mm grouping.
4. **F10 text:** the strip depth for the new board; whether the limiter may leave B.Cu-under-U30 (removes A2/A3).
5. **Strengthened pyro rules** P-1b (rule G board-wide outside U1), P-3 (block purity) and P-7 (gate guard): they make
   the DRU and check text change, so the owner should see them, though they only tighten.

**Possible, but only if the owner asks:**
- Jacks on the forward edge (F8/F10 edit and J1 re-entry; pass1_layout §3.2).
- TXEN from an MCU GPIO instead of DIO2 (F10 edit; removes the TXEN loop).
- Any contract-pin move (`check_actuators` change).
- Any new part (impossible at 52/52 extended codes unless one extended code is removed).

---

## Sources

**In `rocket-flight-computer-r9`:** `AGENTS.md` §1–3; `docs/REQUIREMENTS.md` F4, F6–F10, P1–P3, M1–M3, operating
assumptions, accepted risks; `docs/M3_R8.md` (placement, pyro block, RF, mechanical, hot-plug, IMU); `docs/R8_VALIDATION.md`
(allowlist A1–A3, deviations C1–C20); `docs/ORDERING.md` §3, §5, §7; `docs/MARGIN_PRESCRIPTION.md` P0-1, P0-2, P1-9,
P1-10, P1-13, P1-14, R14 (R7); `docs/M3_R4.md` §1c–§1o, §2, §3; `docs/M3_R5.md` L3, L8, L10, L11, V1; `docs/M3_R6.md`
decisions table; `docs/DESIGN_ASSURANCE.md` (test points, hard rules); `m3_design/assembly_review/m3.kicad_dru`;
`m3_design/check_actuators.py`; `tools/check_r8.py`, `tools/check_r7.py`, `tools/fit_check.py`, `tools/route_check.py`;
`m3_design/r8_legalise.py`, `r8_pcb.py`; `m3_design/assembly_review/sources/r8_design/` (`R8_DECISIONS.md` D1–D111,
`r8_plan.md`, `plan_cleansheet.md`, `survey_constraints.md`, `pin_table.tsv`, `step9/requalify.py`,
`pyro_neighbours.py`, `plate_model.py`, `hotplug_feed.py`); `m3_design/assembly_review/sources/r7_review/`
(`pass1_layout.md` §3–6, `pass2_rf.md` §3–7).

**Maker documents (as cited in those records):** u-blox MAX-F10S integration manual UBXDOC-963802114-12892 R01 §4.1.1,
§4.3, §4.4, §5; MAX-F10S data sheet R03 Tables 12, 13, 21; MAX-M10S IM R05 Table 43; EBYTE E22-900MM22S manual §2.1,
§2.2, §3, §4.1, §7.1; Kinghelm KH-SMA-KE8-G drawing (2019-08-10); Infineon ESD103-B1-02 rev 1.3; TI TPS25947; ST TN1383;
TE MS5611 / AN808; Tag-Connect TC2030-IDC-NL Rev B note 2; JLC capabilities and the JLC041611-7628 template.

**Parent repository:** `CLAUDE.md`; `docs/VEHICLE.md` (bay stack, coupler bore, camera shroud).

**This survey's measurements** (R8 board `cc044ea0…`): `constraints_tools/dump_r8.py` → `r8_fp.json`; `pads.py`;
`block_probe.py`; `hull_probe.py`; the bore-height and lever-arm arithmetic in section 2.2 and 6 (Calc).
