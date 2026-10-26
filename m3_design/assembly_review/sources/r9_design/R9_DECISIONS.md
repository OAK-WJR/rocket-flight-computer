# R9 decisions

Design and gate decisions taken while building R9, each with its basis. The owner's own decisions are in
`R9_OWNER_DECISIONS.md`; the plan is `r9_plan.md`. "Inference" marks reasoning not measured or not from a maker
document (AGENTS §2.5). Step 1 (the gate) is `D-S1-*`.

## Step 1: the rule-based gate

### D-S1-01. LC-1 is board-wide

**Decision.** No pad and no footprint may carry a local clearance override anywhere on the board, not only on pyro,
RAW, gate, sense, BAT_IN or ACT_* pads (r9_plan §1 named those).

**Basis.** Measured in KiCad 10.0.6 on a scratch copy of R8 (`r9_step1_progress.md`): a 0.2 mm override on the GND
test pad TP74 silenced rule D for a PYRO1_BUS track 0.40 mm away (DRC flags it with no override). An override
therefore replaces the custom pyro rules for every pair its pad is in, whatever the pad's own net. Zone clearances are
floors, not overrides: R8's fills keep rule A and rule D (0.501 mm) above their 0.3 / 0.15 mm zone clearances, so
zones are measured by P-0 instead. R8's 1.0 mm test-pad overrides also fail LC-1; step 2 moves that clearance into the
DRU (r9_plan §4 step 2).

### D-S1-02. check_actuators 15b becomes rule-based

**Decision.** `m3_design/check_actuators.py` changes in 15b only (plus `import math`): the PYRO_BLOCK area must still
be exactly one area, one outline, on F.Cu / In1 / In2 / B.Cu, restricting nothing; the fixed rectangle
(x 4–42, y 84–114.4) is replaced by containment of the bounding box of every CH1 courtyard grown by 1.0 mm, every
pad, track, arc, via and fill of the block-internal nets, and the exit nets' copper within 3 mm of a CH1 pad. Every
other rule (1–14, 16, the DRU text pins) is byte-identical. `check_r9` pins the new file (`CHECK_ACTUATORS_SHA`
6fa58a41…); `test_r8_check` now reads R8's copy from commit 9c8179b for R8's own D14 pin.

**Why it must change.** R9 is 98 mm long; R8's rectangle reaches y 114.4 and cannot hold the R9 block (west column,
y ≈ 52–85).

**Why it is strictly stronger.** It keeps every structural assertion and replaces "this one rectangle" with "covers
everything rule G and the block need", which the rectangle never guaranteed once parts may move: on R8's own
geometry the old rectangle misses J121's and J124's courtyards + 1 mm and D120 (its COLD pad included), so R8 fails
the new 15b. Bounding boxes make the test conservative (an area must be larger, never smaller). A larger area only
widens rule G (stricter DRC); `check_r9` P-10 bounds it from above (coat keep-offs, U4).

### D-S1-03. R-1's strip parts leave out the four MCU-end interface resistors

**Decision.** R-1 holds every RF part (`check_r7.RF_PART`) inside y < y_f = 22.0 except R306, R310, R313 and R315.

**Basis.** r9_plan grafts "the RF zone inside y_f = 22.0" from plan C, but `check_r7.SERIES` (series resistor at
its driving end: nearer U1 than the module) and R8 D4 (R310 at the MCU end of the NSS lane) put those four at the MCU
end. With U1 at rotation 0 forward of the strip and ≥ 5 mm from every RF part (F10), a resistor inside y < 22 is
nearer the module than U1's centre (Calc: U1 centre ≈ 8.7 mm inside its courtyard, so ≥ 13.7 mm away; the module
centre ≤ 11 mm). The rest of the RF zone, ferrites and decoupling included, must sit inside y_f.

### D-S1-04. R-5's qualified profile, windows and bends

**Decision.** Outside the windows every RF-track sample keeps F.Cu GND on both sides at 0.25–0.30 mm within one
0.01 mm scan step (25–31 steps). Windows are only the chain's own parts (launch, ESD, bias tap, pi parts, module pad
entry); a part pad on the line may be at most 0.6 mm long. At bends the gap may reach 0.55 mm. In1 GND covers
±0.70 mm under every RF track and +0.3 mm round every RF pad outside the launch cut-outs.

**Basis.** R7 pass 2 qualified W 0.30 / gap 0.25 (50.3 Ω coated) and the 0402 pads on the line (35–39 Ω over
0.5–0.6 mm). `tools/gcpw_solve.py`, validated against pass 2 (coated 49.96 / bare 51.995 / launch 48.79 Ω against
50.3 / 52.2 / 49.0), gives Z0 = 52.3 Ω at a 0.58 mm symmetric gap; Z0 rises monotonically with each gap, so any
section with both gaps in 0.25–0.55 mm lies within 50.3–52.3 Ω (inside 50 ± 2.5). R8's corners (0.31 mm) pass this
way, "re-solved and recorded" as the survey asks.

### D-S1-05. R-7 measures stitching along the line

**Decision.** GND-via gaps beside each RF line are measured along the line's path, per segment (a via counts beside
every segment its foot lands on, within 0.5 mm of the segment ends), not along y.

**Basis.** Identical to R8's method on a straight line (the R9 plan aligns each jack with its module pin); stricter at
a jog because the jog's length counts (R8's GNSS west gap: 3.90 mm along y, 2.73 mm along the path with per-segment
feet). Both exceed 2.5 mm, so R8 fails either way.

### D-S1-06. R-12 re-measures R7's decoupling with one metric

**Decision.** Decoupling distance = module VCC pad centre to the capacitor's supply pad centre; limits are R7/R8's
own geometry measured so: C311 1.97, C312 2.19, C310 3.64 mm (U31.1), C301 2.18, C300 3.02 mm (U30.7/8). The GNSS
VCC series resistance is bounded as FB30's 0.050 Ω + Σ 3V3_GNSS track (L/W × 0.62 mΩ/□, 85 °C) + 1 mΩ per via +
0.020 Ω for the 3V3 side (pass 3 solved 5.06 mΩ), ≤ 0.2 Ω.

**Basis.** pass2_rf §3.11 quoted 1.8 / 2.0 / 3.6 mm from an unstated reference point; no metric reproduces them on
R8's (rigid R7) geometry, so the limits are re-measured, not quoted. FB30: Murata JENF243A-0003 §3 (pass2_electrical
§4.5).

### D-S1-07. R9 keeps R8's pin table

**Decision.** `check_r9` reads `sources/r8_design/pin_table.tsv` for U1's map and the loader pins.

**Basis.** plan_spine §2.2: no MCU pin moves. A future pin move gets its own table and decision.

### D-S1-08. P-7's reset-voltage model

**Decision.** Gate copper (outside U1's courtyard) keeps ≥ 0.5 mm, same layer and layers < 0.5 mm apart, from every
net whose hard short puts ≥ 0.2 V on the gate with the MCU in reset. Sources: sense nodes by their divider's Thevenin
(8.4 V / 11.2 through 0.91 kΩ), MCU-side sense lanes through the extra 4.7 kΩ, midpoints through 2.78 kΩ, GND and
no-net pads 0 V, everything else (rails, armed copper, COLD, driven logic) stiff.

**Basis.** survey §9.4 item 6 and P-7. ARM1_SENSE gives 0.367 V (R8P1-PYRO-04's 0.37 V); an MCU-side lane 0.102 V.
AON7524 minimum threshold 0.4 V at 25 °C (lower hot); 0.2 V keeps a factor of two (survey). Treating unknown nets as
stiff is the conservative side.

### D-S1-09. P-5's consequence classes and thresholds

**Decision.** Gated: exposed pad pairs of different parts, same face, under 1.0 mm (1.2 mm for the strict classes:
live or RAW_ACT against a sense node or gate, midpoint against a gate, gate against sense / midpoint / COLD, actuator
gate against GND) whose bridge can change a pyro or actuator-switch state. Tolerated: R4's own-divider classes, a
live net on a divider midpoint (F8's single-fault bound), and the fail-safe equivalents of one analysed part fault
(gate to GND, GATE to GATE_N, node / midpoint / MCU side to GND, node to its own MCU side, actuator gate to its source
or battery input, ACT_GATE to ACT_DRV), a gate against a passive source under 0.2 V in reset, and no-net pads. Pairs
of power, logic and GND nets only (a short that shows at power-up) are out of scope; a part's own pads are listed,
not gated.

**Basis.** survey §9.4 item 3 and P-5; M3_R4 §1n–§1o, §2, §3; r9_plan's strict pad rules. On R8 the table finds
Q124.5 (drain) to C128.2 (GND) at 0.970 mm (a bridge fires the igniter when armed; outside rule H, rule D holds) and
C128.2 to R134.1 (igniter) at 0.621 mm: recorded as R8 observations (handoff).

### D-S1-10. R-13 measures to the terminals and armed copper

**Decision.** U31, J31 and the radio RF copper keep ≥ 40 mm from J121 / J124 and from bus / igniter / drain copper;
the distance to every other PYRO / ARM copper is reported.

**Basis.** Owner decision 3 accepted about 45 mm radio-to-pyro (plan_spine: terminals to radio). "Any PYRO1 / ARM1
copper" would include the MCU-side sense lanes at U1, 27.4 mm from U31 even on R8, which no compact floorplan can move.

### D-S1-11. M-2 at 209 Hz, the plate model in tools/

**Decision.** f1 (jacks only, pinned, D 5) ≥ 209 Hz, from `tools/plate_model.py` (a verbatim copy of R8 step 9's) on
this board's fit report, bound by board SHA. `tools/check.sh` runs it with `NUMPY_PY` (a python3 with numpy).

**Basis.** r9_plan §2 hard row. R8's own 208.7 Hz fails it by its rounding (recorded).

### D-S1-12. M-5 floors

**Decision.** Each fit category ≥ R8's figure truncated to 0.001 mm (J9 mated 0.028, J3 0.886, J121 / J124 1.153,
C84 1.366, worst bottom 2.356, support bottom 4.452, support top 5.008 mm); J122 mated ≥ 0.49 mm with the recorded
reason (owner decision 5: J122 turned, 0.4995 mm by the fit formula at x 23).

### D-S1-13. Kept rules strengthened to r9_plan's hard rows

**Decision.** D85 battery-live to bus / igniter / drain ≥ 2.5 mm (X2d), D18 inner RAW_ACT / BAT_IN to armed copper
≥ 2.65 mm (X9c), RF separation to restricted parts ≥ 5.94 mm (X9; fast lines stay 5.0 mm), D20 with no In2
exemption (S15 = 0).

### D-S1-14. F9-1 input-protection distance

**Decision.** D8, C80, C96, C89, C95, R166, R167 within 10.6 mm of J1.1 (centre to nearest pad centre) and U9's
nearest BAT_IN pad within 27.07 mm.

**Basis.** R8 D76 (the hot-plug premise lumps the harness at J1); 27.07 mm is R8's measured U9 distance, the geometry
`step9/hotplug_feed.py` modelled ("U9 27 mm away"). Plan C's "F9 input-protection distance as a rule".

### D-S1-15. P-3 uses the courtyard hull and keeps RAW_ACT off the inner layers

**Decision.** The hull is the CH1 courtyards' convex hull + 1.0 mm (survey P-3), not plan A's copper-and-pad hull.
RAW_ACT is allowed on F.Cu inside it; on In1 / In2 only GND copper, CH1 / GND vias and the CH1 parts' own barrels;
on B.Cu foreign copper (RAW_ACT included) ≥ 1.0 mm from CH1 copper.

**Basis.** The courtyard hull contains the pad hull, so it is the stricter of the two; plan_spine §10 reports its
prototype passing it.

### D-S1-16. Terminal entries pinned to the owner's sides

**Decision.** P-11 / M-4 pin the entries: J121 and J124 enter from −x with ≥ 6.25 mm to the bore wall at 5 mm height
(R8: 6.253 mm), J1 from +y with its courtyard face ≤ 2.0 mm from the forward edge (R8 1.86 mm) and nothing in front.

**Basis.** Owner decision 1 (pyro leads west, battery leads east to J1's forward entry); the DB128 footprints enter on
local −y (their descr).

### D-S1-17. M-6 has no D61 exception

**Decision.** Bottom parts keep ≥ 1.0 mm from every PYRO / ARM via, the MCU-side ones included.

**Basis.** Clean sheet: R8's two MCU-side exceptions came from its rigid block; nothing forces them in R9.

### D-S1-18. T-1: a tab in both end thirds of each long edge

**Decision.** Each long edge admits a legal 5 mm tab wholly in its aft third and one wholly in its forward third
(ORDERING §3's clearances, the jacks left out, the board's own outline).

**Basis.** survey §3 ("a legal 5 mm window on each long edge near both ends"); plan C's tab-window check.

### D-S1-19. R-4 holds pass 2's eight launch vias

**Decision.** Each jack's eight stitching vias at (±1.45, 1.0 / 2.3 / 3.6) and (±1.25, 4.15) in its frame, ±0.05 mm.

**Basis.** survey R-4 / pass2_rf §3.5. R7 / R8's J30 has its east (+1.25, 4.15) via at (+1.20, 4.65): R8 fails R-4,
recorded as an R7 / R8 deviation from its own qualification text (J31 matches).

### D-S1-20. P-1b's DRU text, written in step 2

**Decision.** `check_r9` requires rule G's condition to carry `(A.intersectsArea('PYRO_BLOCK') ||
!A.intersectsCourtyard('U1'))` in place of `A.intersectsArea('PYRO_BLOCK')`; the geometric P-0 already applies that
scope with the gate copper clipped to outside U1's courtyard. Step 2 edits the DRU (with the test-pad clearances) and
re-pins `DRU_SHA` and `PYRO_RULE_SHA['Pyro G…']` in `check_actuators.py` after review.

**Basis.** Owner decision 2 (P-1b adopted). The DRU belongs to the project files step 2 regenerates. KiCad's
`intersectsCourtyard` exempts a whole segment that touches U1's courtyard; P-0's clipping closes that gap.

### D-S1-21. M-3's tie holes are derived from J122

**Decision.** `fit_check.retention_holes()` finds one Ø3.2 hole beyond each end of J122 (centre 1–4 mm past the
courtyard along the plug row, ≤ 6 mm off it) whose hole-to-hole line crosses every plug's centre line within the
plug's length (pins ± half a pitch); `fit_check.check_board` uses it; M-3 adds the 4 mm bottom channel. On R8 it
returns the old constants.

### D-S1-22. R-8's keep-out regions from the footprints

**Decision.** U31: B.Cu and In2 cover its 10 × 10 mm body; F.Cu and In1 the pad-ring interior (pad inner edges less
0.15 mm). U30: F.Cu and In1 cover the body (u-blox DS Table 21: 10.1 mm along the pad rows × 9.7 mm) between the pad
rows less 0.15 mm.

**Basis.** EBYTE manual §4.1, u-blox IM §4.4; the derivation reproduces R8's areas exactly.

### D-S1-23. M-7's MEMS body and interior

**Decision.** For U4 and U5 the body is the courtyard less 0.25 mm (R8's IMU_body_B / BARO_body_B) and the interior
the body clipped at the pad rows' inner edges; no via or fill under the body on its side, no track inside the
interior.

### D-S1-24. P-4's seeded suite runs in the gate

**Decision.** `tools/check.sh` runs `tools/rule_h_seed.py` on every build (three closest rule-H pairs × eight
variants, ≈ 2–3 min) and `check_r9` P-4 reads its report.

**Basis.** survey P-4 ("on every build"); plan_spine §9.10.

### D-S1-25. The R9 scorecard

**Decision.** `tools/r9_scorecard.py` carries r9_plan §2's hard / done rows exactly (S4 done ≤ 70, stretch 55, owner
decision 4), with new rows LC-1 overrides, plate-model f1, the R-5 GCPW bound (gcpw_solve at the widest and narrowest
gap on the lines) and Z2 as the three exit nets' whole track length (R9 has no rigid block; R8 160.3 mm). R8's
baselines: `tools/scorecard_r8_r9.json` and `_quick.json`.

## Step 2: schematic, footprints and design rules

### D-S2-01. A footprint variant is its base mirrored about the local y axis; pin-1 marks move with pin 1

**Decision.** `M3_DB128L_2P_BK_SW` (J121, J124) and `HDR-TH_12P-P2.54-V-M-R3-C4-S2.54_MIR` (J122) are generated by
`m3_design/r9_lib.py` from `M3_DB128L_2P_BK` and `HDR-TH_12P-P2.54-V-M-R3-C4-S2.54`: every pad, graphic and text
position has x → −x. Each pad keeps its number, shape, size, drill and layers; the set of pad positions, sizes and
drills is the base's (the same land); the courtyard, fabrication outline and the single 3D model are the base's. So the
square THT pad (pin 1) and the header's pin-1 silkscreen corner and dot sit at pin 1's new position (DB128L local +2.54;
header local +3.81 / +2.54). Pad alias (variant pad → base pad at the same position): DB128L 1:2 2:1; header 1:10 2:11
3:12 4:7 5:8 6:9 7:4 8:5 9:6 10:1 11:2 12:3.

**Basis.** Owner decision 2 ("renumber J121/J124 pads, same part, same land") and r9_plan §3 item 2 (mirrored J122
numbering, adopted with every recommended option). plan_spine §2.3: "pads 1 and 2 swapped … any pad-level property must
move with its role". The library marks pin 1 by the square THT pad (J1's DB128V, the DB128L, the 3 × 4 header: checked
in `kilib/rocket.pretty`), and the board's terminal legends name pins by number ("1:BUS1", "2:RAW", D92), so the square
pad stays on pin 1 = BUS / OUT as in R8 (R8: J124.1 BUS and J121.1 OUT are the square pads). Keeping the square pad at
its old position (what plan_spine's prototype did: it swapped nets, not pads) would put it on RAW_ACT and IGN, and on
SERVO4's signal pin for J122, against the legends. `r9_lib.build` asserts the bodies are symmetric (courtyard and fab
outline equal to their mirror; texts on x = 0), so the mirror changes no body. The header's EasyEDA 3D model: body box
symmetric (±5.08 × ±3.79 mm); its asymmetric vertices are a white glyph on the top face and the mesh triangulation
(Inference from the model's vertex data; the part, hanxia HX PZ2.54-3x4P ZZ C32713291, is unkeyed square pins:
ROCKET_FC_FROZEN_DESIGN), so the base model is reused. The DB128L model is a centred box. Rows of J122 do not move: RAW
stays the middle row (a reversed servo plug stays harmless, DESIGN_ASSURANCE).

**Consequence for the pyro geometry.** Against plan_spine's prototype the square (corner 1.84 mm from centre, not
1.30) is on J124's BUS pad and J121's OUT pad, as in R8. Steps 3 and 5 measure every margin on the real geometry
(pyro_probe, DRC, P-0); the prototype's margins (RAW branch to BUS 3.0 mm against rule E's 1.0) leave room.

### D-S2-02. The variants are assigned in the schematic; nets stay on pad numbers

**Decision.** `m3_design/r9_sch.py` changes only the Footprint fields of J121, J124 (→ `rocket:M3_DB128L_2P_BK_SW`)
and J122 (→ `rocket:HDR-TH_12P-P2.54-V-M-R3-C4-S2.54_MIR`), three notes and the rev. No pin, net, value or code changes.

**Basis.** Owner decision 2: "check_actuators unchanged". check_actuators 1 (J124.1 BUS, J124.2 RAW_ACT, J121.1 OUT,
J121.2 IGN) and 7 (SERVOi_OUT on J122.1/4/7/10, RAW on 2/5/8/11, GND on 3/6/9/12) read nets by pad number, so the
contract holds byte for byte. Measured: the netlist diff R8 → R9 is the three parts' `<footprint>` and Footprint field
and the 15 sheets' rev (`r9_sch_check.py`, step2 evidence).

### D-S2-03. The board takes the variants by an in-place exchange

**Decision.** `r9_lib.apply_variants(board)` (for step 3's builder) turns each base instance of J121 / J124 / J122
into its variant in place: the same mirror applied to its pads and graphics in its own frame, FPID and description
set; reference, fields, path, UUIDs, pad nets and pad-level settings untouched. It asserts the result equals the
library variant (`compare_to_library`) and is idempotent.

**Basis.** R8's instances carry board decisions that are not library data (J122's GND pads ZONE_CONNECTION_FULL for
the 7.7 A return, ORDERING §4); a library reload would drop them silently. Measured on a scratch R8 copy: KiCad DRC
reports no `lib_footprint_mismatch` after the exchange and does report one when the pads are mirrored with the FPID
left at the base (negative control), so KiCad's own check holds each instance to its library footprint.

### D-S2-04. All 29 local clearances go

**Decision.** `r9_lib.clear_overrides(board)` removes every pad and footprint local clearance. R8 has 29, all on pads:
J124.2 and J122.2 / 5 / 8 / 11 (RAW_ACT) 0.3 mm and the 24 test pads 1.0 mm; no footprint-level override; the library
carries none.

**Basis.** LC-1 (D-S1-01, board-wide). The clearances themselves move into the DRU (D-S2-06).

### D-S2-05. Rule G's P-1b scope

**Decision.** In rule G's condition `A.intersectsArea('PYRO_BLOCK')` becomes `(A.intersectsArea('PYRO_BLOCK') ||
!A.intersectsCourtyard('U1'))` (check_r9 G_SCOPE); the rule's name and the rest of its text stay; the pyro comment
block says so. check_actuators `PYRO_RULE_SHA['Pyro G…']` → `740c8388e07e6197`.

**Basis.** Owner decision 2 (P-1b adopted); D-S1-20. The old scope is a subset of the new one, so it only tightens.
The name stays because check_actuators' `PYRO_RULES` keys, check_r9's `RULE_G` and rule_h_seed address the rule by name
(renaming would touch the step-1 gate for no safety gain). Measured: a PYRO1_GATE_N track 0.25 mm from 3V3 on In1,
outside PYRO_BLOCK and U1's courtyard, is reported under rule G with R9's DRU and not with R8's.

### D-S2-06. R8's overrides become two DRU rules

**Decision.** `m3_design/r9_dru.py` adds:
- "R9 RAW_ACT pins to foreign copper": every RAW_ACT through-hole pad ≥ 0.3 mm from all other copper, placed before the
  pyro rules (after the RF rules, which name no RAW_ACT copper);
- "R9 bare test pads to foreign copper": every `TP*` pad ≥ 1.0 mm from all other copper, placed last.
Pyro rules A–F, A2 and H and every other R8 rule stay byte for byte (asserted by `r9_dru.verify`).

**Basis.** KiCad applies the last matching rule. The RAW rule's 0.3 mm is below or equal to every pyro rule, so placed
before them it never governs a pyro pair: at J124.2 / J122's RAW pins DRC now enforces A (0.5), E (1.0), F, A2 and H,
which R8's 0.3 mm overrides switched off (plan_spine §0.5). The test-pad rule's 1.0 mm is at least every rule in the
file (E and H are 1.0, none larger), so placed last it only raises a test pad's clearance, exactly as R8's override
replaced everything with 1.0; check_r9 P-4 allows a later rule only at ≥ 1.0 mm. Both rules equal
`check_r7.foreign_clearances` (RAW_ACT PTH 0.3, bare test pads 1.0), which check_r9 P-9 measures geometrically, so DRC
and the gate agree. KiCad facts measured on a scratch R8 copy: `memberOfFootprint('TP*')` wildcards match (and 'TQ*'
does not); each rule reports its seeded violation (3V3 0.6 mm from TP74; GND 0.2 mm from J122.2) and R8's DRU with the
overrides cleared reports neither. Fills, on R8's board (zones unfilled, refilled natively): R8 refilled under R8's DRU
is byte-identical to the committed board; with the 29 overrides cleared under R8's rules plus the two LC-1 rules, all
14 zone-layer fills equal R8's committed fills exactly (boolean difference 0 nm² both ways): the rules replace the
overrides exactly in the filler (`r9_sch_check.py` gates this). Under R8's DRU with the overrides cleared the GND pours
move up to the test pads and RAW pins (GND_F, GND_B and R8_RAW_ACT_F gain 34, 116 and 2.6 mm²): the overrides mattered, the rules carry
them. Rule G's wider scope (D-S2-05) alone changes R8_3V3_In2's fill by sub-µm² slivers (0.52 / 0.30 µm² in all,
nanometre-thin, along y ≈ 54; isolated by filling with only that edit), a polygon-arithmetic effect of the extra
clearance evaluation, no copper change. `DRU_SHA` → `5aa63b0aeabb43eb`.

### D-S2-07. Notes

**Decision.** The pyro sheet's "pin ordering is retained" note says pin numbering is retained and the R9 footprint
turns the pins (pin 2 forward, wires from −x); the servo sheet's D121 note drops R8's "ahead of their reversal into
J122's row order" (R9 has no reversal); a servo-sheet note records J122's mirrored numbering, placed one row above the
sheet's notes (the slot below them, y 283.1, rendered on the frame line; SVG checked).

### D-S2-08. JLC placement matches pads through the maker's numbering

**Decision.** `tools/jlc_orient.py` maps our pad numbers to the maker's (`PAD_ALIAS`, the D-S2-01 alias) before matching,
in both the generator and `--verify-cpl`, and takes `--out`. `tools/jlc_corrections.json` is regenerated on the final
board (step 9), not here.

**Basis.** JLC places with the maker's (EasyEDA) footprint and numbering. Measured on the scratch variant board: with
the alias both variants come out theta 0, offset 0, residual 0, OK, identical to R8's base entries; without it the
DB128L comes out theta 180 with status OK (JLC would turn the terminal body, wire entry facing into the board, with
pads still on pads, so `--verify-cpl` would pass it) and the header CHECK. `tools/test_r9_sch.py` checks the table
against the library files. Until step 9 the corrections file has no variant entries, so `export_fab.py` refuses the
R9 board (fails safe).

### D-S2-09. fit_check knows the header variant

**Decision.** `tools/fit_check.MATED` carries `HDR-TH_12P-P2.54-V-M-R3-C4-S2.54_MIR` with the base's envelope.

**Basis.** The same body; the envelope (±5.08 × ±4.0 mm) is symmetric. Without the entry fit_check fails J122 as "mated
envelope not reviewed" (fail-safe). The DB128L variant is covered by fit_check's `M3_DB128` prefix rules.

### D-S2-10. No new part: still 52 extended codes

**Decision / evidence.** Every part's LCSC code is R8's; R8's JLC BOM (92 lines, 219 parts) reproduces from the R9
netlist code by code; R8's supplier check (`fab/cost_check.json`, 2026-10-19, bound to that BOM's SHA-256 be711876…)
classes 52 of those codes extended: 52 ≤ 52 (REQUIREMENTS M3). The re-run within 24 h of ordering stays M3's (step 9).
The R9 BOM's Footprint column will name the variants for J121 / J124 / J122.

### D-S2-11. check_actuators and check_r9 re-pinned

**Decision.** check_actuators `DRU_SHA` and rule G's `PYRO_RULE_SHA` follow the reviewed R9 DRU (nothing else in the
file changes); check_r9 `CHECK_ACTUATORS_SHA` → `0a4269ca…`.

**Basis.** Step 1 handoff ("after review, re-pin DRU_SHA and the changed PYRO_RULE_SHA entries, then
CHECK_ACTUATORS_SHA"). Rule H's text is unchanged (P-4 cross-checks it). On the worktree's R8 board with R9's DRU
check_actuators fails only 15b (R8's rectangle, known since step 1).

### D-S2-12. check_r9 pins the variants

**Decision.** check_r9 K-contract requires J121 / J124 on `M3_DB128L_2P_BK_SW` and J122 on the `_MIR` header
(`R9_FOOTPRINTS`), beside check_r7's footprint pins. R8 therefore fails K-contract too (18 rules; test_r9_check's
`R8_FAILING`).

**Basis.** The owner decisions, held by the gate rather than only by the schematic (parity holds the board to the
schematic, DRC's lib_footprint_mismatch holds each instance to the library). Stricter only. The same test shows
check_r9's D92 legend rule catches R8's terminal legends beside the wrong pins once the pads swap: the step-8
silkscreen must draw them by pin.

### D-S2-13. r9_build.sh starts with step 2

**Decision.** `m3_design/r9_build.sh` restores R8's sheets, netlist and DRU from 9c8179b and runs r9_lib.py, r9_dru.py,
r9_sch.py --netlist and the step gate r9_sch_check.py; each later step appends its stages, tools/check.sh last.
Measured: two runs reproduce the sheets, netlist, DRU and variant files byte for byte.

## Step 3: placement freeze

### D-S3-01. The legaliser applies the R9 contract to every part

**Decision.** `m3_design/r9_legalise.py` (R8's legaliser generalised) decides placement legality; `r9_pcb.py` refuses
any violation and `r9_place_check.py` gates it over all 249 parts. Nothing is a fixed coordinate: the outline, the
supports and J122's tie holes are read from the board. It checks: outline and holes; courtyards (0.02 mm gap, polygon
courtyards); pad-to-pad clearance as the largest of every matching R9 DRU rule (netclass 0.15, RF50 / SMA to GND 0.25
/ 0.30, RAW_ACT through-hole pads 0.3, Tag-Connect 0.508, bare test pads 1.0, pyro A–H and A2, rule G in its P-1b
scope), the strict pad rules (H+ 1.2, GS 1.2, AG 1.2), P-6 and P-5's forbidden bridge classes; M-6 bottom keep-outs
and the M-3 tie channel; M-5's support floors (4.452 bottom / 5.008 top, fit_check's measures) and fit floors; R-1
(y_f 22.0, both clauses) and R-10 (5.94 mm courtyards / 5.0 mm fast-net pads); P-3 for pads; P-10 on the derived
PYRO_BLOCK and J2; M-4's J1 entry corridor. Every limit is imported from check_r9 / pyro_probe / bridge_table, never
restated.

**Basis.** r9_plan §4 step 3 ("0 violations across 249 parts", strict pad rules in the legaliser: plan C graft); a
legal table cannot fail these gate rules later. U1's own pads count as inside U1's courtyard for rule G (the MCU
pin's escape, DRU text `!A.intersectsCourtyard('U1')`). KiCad applies the last matching rule and every later R9 rule
is ≥ the earlier ones it overlaps (D-S2-06), so the maximum equals or exceeds DRC.

### D-S3-02. PYRO_BLOCK is derived from the CH1 placement

**Decision.** `r9_legalise.block_area`: the union of the CH1 courtyards grown 1.0 + 0.1 mm and of the exit-net CH1
pads grown 3.0 + 0.1 mm, closed by ±1.5 mm (gaps under 3 mm between boxes filled), rectilinear, snapped outward to a
0.1 mm grid. `r9_pcb.py` gives the kept PYRO_BLOCK rule area this outline (34 vertices, bbox 1.2–28.4 × 54.2–89.8 mm).

**Basis.** P-1 (the block by content, check_r9 COURTYARD_GROW / EXIT_REACH) and check_actuators 15b, which now pass on
the built board (R8's rectangle failed 15b since step 1). The 0.1 mm margins keep grid snapping from cutting an
item's reach.

### D-S3-03. 102 mm by the kill path

**Decision.** The board is 46 × 102 mm. The four MCU-end interface resistors sit on the top side, in lane order:
R306 (16.5, 29.2), R315 (20.7, 28.8), R310 (21.7, 28.8), R313 (23.3, 29.2).

**Basis.** F10 counts R306 / R310 / R313 / R315 as RF parts (`check_r7.RF_PART`), so R-10 keeps them ≥ 5.94 mm
(courtyards) from U1 / U3 / Y1 and ≥ 5.0 mm from fast-net pads; K-contract SERIES / PULL_END (`check_r7.SERIES`, R8
D4) wants each centre nearer U1's centre than its module's. U1's centre lies 8.6 mm inside its courtyard, so each
resistor is ≥ ~15 mm from U1's centre and the window between the two rules opens only as U1 moves away from the
strip. `m3_design/r9_kill_path.py` (evidence `step3_evidence/kill_path.*`) rebuilds the table at each length (R8 from
git, everything outside the RF strip moved with the forward edge) and searches top-side spots, legal under the gate's
legaliser, SERIES / PULL_END margin ≥ 0.25 mm, legal 0.2 mm nearer U1, lane detour ≤ 6 mm, then the four in lane
order with least detour:
- 98 mm: no R306 spot at all (at the R-10 limit R306 must lie east of x ≈ 22 and the radio resistors west of
  x ≈ 19.8, so the GNSS lane would cross the radio lanes);
- 100 mm: R306 and the radio resistors share a 2.9 mm wide window: no lane-ordered arrangement;
- 101 mm: holds (total detour 5.53 mm), but it is not one of the owner's lengths;
- 102 mm: holds, total detour 2.62 mm; SERIES margins 1.47 (R315), 0.77 (R310), 0.69 (R306), 0.36 (R313) mm;
  nearest R-10 6.24 mm (R310–U1), nearest fast-net pad 5.197 mm (R306–USB_DM).
r9_plan §4 step 3 ("if 98 fails, go to 100") and owner decision 1 ("fallback 100 / 102 mm") give 102. Spots that are
legal at 98 / 100 mm with resistors on the bottom or out of lane order need crossing lanes or layer hops on critical
interface nets, which REQUIREMENTS M2 (no needless detours, vias or layer hops) rules out when an owner-approved length
avoids them. Everything forward of the strip moved 4 mm forward unchanged (the table's 98 mm design), so every other
rule result carries over and is re-measured by the gate at 102.

**Owner option (not a blocker).** Measured (`step3_evidence/option_98mm_f10.txt`): at 98 mm with the four resistors at
U1's pins, the only violations are R-10 between them and U1 / U3 / U7 / C76; with the four outside F10's RF-part list
the legaliser reports 0. They carry digital-side MCU signals by design (SERIES, R8 D4), so the owner may prefer to
reclassify them and return to 98 mm (an F10 text change, not taken here).

### D-S3-04. The RF strip inside y_f 22.0

**Decision.** U30 moves from R8's (10.41, 14.95) to (11.15, 14.05); the GNSS supply / interface row sits forward of
it in one 1.5 mm band: R305 (TXD series, module pad in front of U30.2), R307 (TIMEPULSE series at U30.4), C300, C301
(in front of U30.8) and FB30 (3V3_GNSS pad onto C301.1), each abutting U30's courtyard; FB31 turns to rot 0 at
(34.4, 20.95) forward of U31. J30, the GNSS chain and limiter, J31, U31 and the radio parts keep R8's positions.

**Basis.** Owner decision 3 (y_f 22.0); R-1 measured deepest courtyard 21.955 mm (C300). R-12 limits (C301 ≤ 2.18,
C300 ≤ 3.02 mm from U30's VCC pins) leave C301 a 0.93 mm and C300 a 1.49 mm tall slot between U30's courtyard and y_f
only with U30 ≥ 0.855 mm aft of R8 (and ≤ 0.945 mm: the chain parts aft of it); measured C301 2.13 mm, C300 2.556 mm.
U30.18's exposed pad must stay ≥ 5.008 mm from the (4, 4) support (M-5): at R8's x it would be 4.703 mm, so U30
moves 0.74 mm east (5.012 mm). Moving the jack and chain east with it puts GNSS RF copper 14.71 mm from radio RF
copper (R-11 15.0, measured), so they stay: U30.11 lies 0.74 mm east of R304.2, a jog step 4's module segment takes
(r9_plan: chains regenerated in each jack's and module's frame). The row is planar for step 4: TXD, RXD (between R305
and R307), TIMEPULSE, the 3V3_GNSS group and RESET_N (east under FB30, then forward) leave in U30's pin order; the
U30.13 / U30.14 escape vias fit in the 1.0 mm between U30's aft pads and C303's pads (Inference: a 0.45 mm via with
0.275 mm clearances; step 4 routes it). Corrects step-3 FINDING 2's first note (r9_step3_progress.md).

### D-S3-05. U1 block first, then the forward half

**Decision.** U1 at (18, 44.5) rot 0; U3, Y1, R10 and the under-U1 decoupling keep R8's spike-a block, translated with
U1; U4 (12, 47.4) and U5 (5.6, 50.6) on the bottom at rot 0, their rule areas and Y1's In2 keep-out translated with
them (offsets equal R8's, gated); forward-face decoupling C14 / C21 / C22 and the 3V3A filter on the bottom at U1's
forward pins; the MCU-end sense resistors R168 / R170 / R172 at their pins (P-8).

**Basis.** r9_plan step 3 (aft cluster first; U1 rot 0, 5 mm west of the axis); M3_R5 axis map (U4 rot 0 on the
bottom); IMU lever arm 11.0 mm (done row ≤ 11); P-10: U4 5.526 mm from the coat region (≥ 5.0).

### D-S3-06. West column, CH1 column, servo header

**Decision.** West edge: J3 (USB, 4.6, 34.3) and D4 between it and U1, J2 (SWD) beside them, status LEDs and the
buzzer driver, LS120 and U5 below. CH1 (owner decisions 1 and 2): J124 (10.1, 83.5) and J121 10.23 mm aft, both rot
90 (entry −x, RAW / IGN pin forward), R134 bridging J121.2 and J124.1 with two straight bars, Q124 under J121's OUT
pin, the gate / CONT row, D120 in the IGN-bar bay, the arm divider on the BUS bar. J122 turned on the axis (23, 62)
rot 180, one 1 kΩ under each plug column, D121 and the pull-downs on the bottom; tie holes (16, 62) and (29.9, 59).

**Basis.** plan_spine's prototype, re-measured on the real variant geometry: pyro pad margins H 0.225, H+ 0.025, GS
0.151, AG 0.162, A 0.767, C 0.609 mm (all ≥ 0); P-11 wire room 6.353 mm; P-3 no foreign net in the hull; J1 23.33 /
14.72 mm from J121 / J124 (M-4 ≤ 25). USB pads ≥ 5.0 mm from strip RF parts (R-10).

### D-S3-07. East: camera, logic supply, battery entry, actuator switch

**Decision.** The camera block keeps R8's relative arrangement (moved with the forward block), U13 on top between U1
and U12; C84 over the FET pair, U11 / U2 / L1 on the bottom east of the spine; J1 (20, 94.4) rot 180 at the forward
edge; Q120 / Q121 face to face on the bottom; D8 at J1.1, the damper (C89, C95, R166) east of J1, U9 on top east of
the damper with its network; the test pads in a column at the east edge.

**Basis.** F9-1 measured: D8 5.22, C96 5.72, C80 8.90, C89 4.79, C95 4.69, R166 8.38, R167 5.59 mm (≤ 10.6), U9
12.8 mm (≤ 27.07) from J1.1; F10 nearest RF part 6.24 mm; fit minimum 0.028 mm (J9 mated, R8's floor).

### D-S3-08. Supports

**Decision.** Corners (4, 4), (42, 4), (4, 98), (42, 98); mid-span east (42, 59.5).

**Basis.** P2; owner decision 5 gives (42, 55.5) at 98 mm "if the DC solve holds" (the solve is step 6's): the support
moves with the forward block it was chosen against (+4 mm). Plate model f1 252.1 Hz (jacks only, pinned, D 5; hard
≥ 209, done ≥ 241).

### D-S3-09. The step gate

**Decision.** `m3_design/r9_place_check.py` gates: legaliser; kicad-cli DRC with parity (allowed only unconnected
items and step 8's silkscreen classes); fit (M-5); plate f1; F9-1; R-10; the pyro pad rules (pyro_probe, bridge_table,
P-6); M-4; T-1; MST ≤ 1638.9 mm (R8's measure, r8_place_check.mst); check_r9's placement-bound rules (LC-1, P-1,
P-2, P-3, P-10, P-11, R-1, R-3, R-11, R-12, R-13, M-3, M-6, M-7, K-contract, K-actuators); check_actuators; the
rule-area offsets against R8's board from git.

**Basis.** r9_plan §4 step 3's verify list. K-contract's route-only items (C29's direct route, the camera bypass
routes) wait for copper; their pad distances are gated now. Measured on the built board: all gates OK; MST 1468.0 mm;
DRC 0 violations, 0 parity, 499 unconnected, deferred silk 5 / 78 / 128.

### D-S3-10. The builder and the build stage

**Decision.** `m3_design/r9_pcb.py` builds the placement board from R8's committed board (SHA asserted) and
`r9_place.tsv`; `r9_build.sh` restores R8's board from git and runs r9_pcb.py and the gate after the step-2 stages.

**Basis.** "Every board change lives in the r9 build scripts". Measured: two full builds reproduce every built file
byte for byte (board `349c1477…`); the netlist assert finds 761 pads, 0 changed (D-S2-02).

### D-S3-11. R8-era test suites read R8's committed board

**Decision.** `tools/r8_record.board()` returns the worktree board while it is R8's, else R8's committed project
(board, pro, DRU, sheets from 9c8179b) in a temporary folder; test_r8_place, test_r8_power, test_r8_ground,
test_r8_route, test_reference_audit and test_fab_validation use it.

**Basis.** They test R8's build tools (and the R8 fab package, until step 9) on R8's board; with the R9 board in the
worktree their board-bound tests failed for that reason alone (33 failures / errors). Same pattern as step 2's reservation test (D-S2 handoff).
Measured: all suites pass.

## Step 4: RF strip

### D-S4-01. The chains and launches are R7's, by template in each jack's frame

**Decision.** `m3_design/r9_rf.py` draws each RF chain and launch from tables in the jack's frame (x from the jack
axis, board y): R7's rows (ESD y 5.2, bias tap 6.18, GNSS pi 7.13 / radio pi 7.6), W 0.30 GCPW, R304 / R316 jogging
+0.86 mm onto the module's RF pin, the eight launch vias at R7's built spots (+-1.45 at 1.0 / 2.3 / 3.58, +-1.25 at
4.15, 0.6 / 0.3 mm) and the In1 cut-out x +-0.9, y 0-4.6. The frames are tied together: J30 sits 0.86 mm west of
U30.11, J31 0.86 mm west of U31.6 (asserted), so J30 moves to x 13.59 (R8 12.85) with step 3's U30.

**Basis.** r9_plan §1 graft (RF chains congruent with R7, regenerated by template) and §4 step 4. check_r9 R-4 holds
the launch vias to pass 2's spots within 0.05 mm; R7 built the (+-1.45, 3.6) pair at 3.58, where the 0.6 mm rings
clear the (+-1.25, 4.15) pair (at 3.6 they overlap by 0.015 mm: route_check via_overlap), so R7's built launch is the
template (its J30 east via at (+1.20, 4.65), D-S1-19, is not copied). Measured: launch window copper equal to R7's J31
to 0.0008 mm2 for both jacks, J30 = J31 exactly; R-6 GNSS 4.85 mm / 2 bends, radio 4.75 mm / 2 bends (limits 6.26 /
5.26); R-9 ESD 0.795 mm from the jack pad end, C302 0.925 mm, stubs 0.94 mm.

### D-S4-02. GNSS chain sides; the radio group 0.75 mm east

**Decision.** In the GNSS chain D30 is turned 180 degrees (GND pad west of the line) and C303, the pi network's first
shunt, sits at the bias-tap node east of the line (stub 0.94 mm from L30's line pad), turned 90 degrees with its GND
end aft; L30's cold end, C302 and the ANT_DC feed stay west (R7). The radio group (U31, J31, D31, R316, C313, C314,
C310-C312, R311, R312, R314, FB31) moves 0.75 mm east; the radio chain is R7's exactly. These are the only chain
deviations from R7 (`r9_rf.R7_DEVIATIONS`, gated by r9_rf_check `r7`).

**Basis.** Step 3 put U30 0.9 mm aft of R8 (D-S3-04: C300 / C301 inside y_f 22.0), so U30's aft pads end at y 8.4 and
the u-blox T-paste at 7.8, 0.4 mm above R7's pi row (top 7.40). Measured on the R7 chain: whichever way R304 jogs, one
pi shunt lies under U30.12 / U30.13 (C303 x 11.56-12.90 or C305 x 12.42-13.76 at y 6.86-7.40), so LNA_EN has no via
spot aft of its pin (via ring off the paste needs y <= 7.55, off the shunt >= 7.80): r9_plan's graft (shunts east of
the GNSS line) is required, not optional. R-7 (side gaps <= 2.5 mm) then fixes the sides: the 4.86 mm line needs a
via on each side at mid-chain; the pi row's east is R304.2 / C305 and the bias row's west is L30 / C302, so the bias row
east must keep a via spot, which C303 turned (GND end aft) leaves at offset 1.75 mm; D30's GND pad west frees the east
row-1 spot (a west via still fits beyond D30.2). Measured: GNSS side gaps 2.38 / 1.75 mm, radio 1.70 / 2.41 mm.
R-11 (GNSS to radio RF copper >= 15.0): with U30.11 0.74 mm east, C305.1 reaches x 15.64; the radio group 0.75 mm east
gives 15.46 mm (R7 15.45); everything the radio side measures in R7 / R8 moves with it (R-12 C311 1.97, C312 2.191,
C310 3.639 mm; R-11 radio SPI 6.84 mm from U30's body; R-13 46.13 mm). ESD103-B1-02EL is bidirectional (JLC C535146
part attributes "Polarity: Bidirectional"; ±15 V working, pass1_electrical E8 from the maker's data sheet v2.0), so
turning D30 changes nothing electrically. C303 is unfitted (DNP, no paste): it moves 0.95 mm along the line to the
bias node with the same 0.94 mm stub, about 3 degrees at 1.6 GHz (Inference: lambda in the line about 105 mm,
eps_eff 3.2), so the unfitted chain's discontinuities are R7's; ORDERING §4's bench-tuning note (C303 at the bias node,
before R304) is step 10's record.

### D-S4-03. The limiter on B.Cu under U30 with no lead doubling back

**Decision.** U30.14 (VCC_RF) drops by one 45-degree run to V1 (10.4, 7.4), U30.13 (LNA_EN) straight aft to V2
(12.25, 7.4), ANT_DC rises from C302.1 to V3 (11.3, 7.4) between them (0.5 / 0.3 mm vias, rings 0.15 mm off the
T-paste). On B.Cu the cluster sits forward of the vias under U30 with each net entering at the pad nearest its via:
R300 at the via row west of V1, Q32 (E from V1, B on R300.2), Q30 rotation -90 with its drain straight forward of V3
(0.40 mm lead), R301 between Q30.S and Q30.G, R303 beside V2, Q31's gate from R303.1, R302 on the gate trunk, C304
(DNP) off the trunk. GND partner vias within 1.5 mm of V1 / V2 / V3 (route_check critical_via_no_gnd).

**Basis.** F10 ("the antenna-bias limiter sits on B.Cu under U30"; no F10 edit) and r9_plan's graft "no A2/A3
detours": route_check (profile r9, empty allowlist) finds no detour on GNSS_LNA_EN, GNSS_VCC_RF or GNSS_ANT_DC. The
order V1, V3, V2 along the aft edge is the one in which the cluster is planar (VCC_RF, SRC, ANT_DC, GATE, PD, LNA_EN
round its boundary). Q30's short-circuit dissipation (about 0.11-0.12 W, M3_R7 "Antenna bias limiter") now runs into
a 0.40 mm drain lead, V3 and the F.Cu ANT_DC copper, 0.2 mm above In2's strip GND plane (R7: 0.2 mm B.Cu tracks); R7's
bound Tj about 115-125 °C in an 85 °C bay stands (Inference, not re-solved). Q30 sits 4.3 mm from the (4, 4) support
(courtyard; M-6 3.5).

### D-S4-04. Stitching: chain vias, the fence on y_f and a 2.5 mm grid

**Decision.** GND vias: the RF ground pads' and side-stitch vias in the jack frames (0.5 / 0.3 mm where the chain is
tight, R8's radio vias but its (+1.25, 4.75), whose ring touched the launch's), the fence at y 22.2 (23 vias, pitch
<= 1.95 mm, 0.5 / 0.3), a rectangular 2.5 mm grid (0.6 / 0.3) snapped to legal spots within 0.45 mm, four patches at
U31's west pad-row gaps and one under Q30's body (the limiter's B.Cu pocket); GND partners for the TXEN loop's vias
(R8's). The grid was proposed by a scratch design aid (legal spots: rule clearances, no via in a pad, rings off paste,
0.5 mm from the edge and holes, outside the launch windows, small parts' courtyards and the lane corridors) and frozen
as the table `r9_rf.GRID`.

**Basis.** check_r9 R-7: fence within 0.3 mm of y_f, gaps <= 2.0 mm (no lanes yet); strip GND reach <= 4.0 mm on F.Cu
and B.Cu; RF ground pads solid with a via <= 0.6 mm. Measured: reach F.Cu 3.10, B.Cu 3.57 mm; RF ground vias D30.2
0.23, C303.2 0.05, C305.2 0.06, D31.2 / C313.2 / C314.2 0.16 mm; strip GND coverage F.Cu 82.5, In1 95.0, In2 96.6,
B.Cu 93.0 % (R7: 76.7, 95.1, 96.6, 92.0). A regular grid replaces R7's irregular one (186 GND vias in the strip, R8
200).

### D-S4-05. The step draws the strip-internal nets only; corridors for step 7

**Decision.** r9_rf.py draws exactly the nets whose every pad lies in the strip (`r9_rf.strip_nets`, asserted): the RF
nets, GNSS_ANT_* / LNA_EN / VCC_RF, GNSS_TXD, GNSS_TIMEPULSE, GNSS_SAFEBOOT_N, 3V3_GNSS, 3V3_RADIO, RADIO_MISO and
RADIO_TXEN. The interface nets that cross y_f (GNSS_TXD_MCU, GNSS_RXD, GNSS_TP_MCU, GNSS_RESET_N, the radio SPI /
BUSY / RXEN / DIO1 / NRST lanes, the 3V3 feeds of FB30 / FB31) are step 7's family rf_if. Lane corridors
(`r9_rf.CORRIDORS`, F.Cu) are kept free of this step's F.Cu copper and vias; the fence row is not, because R-7 needs
it complete now: step 7 opens lane gaps in it (each <= 2.7 mm and crossed by a lane, R-7) by editing `FENCE_X`.

**Basis.** r9_plan §4 (step 4 RF templates, step 7 rf_if family); one owner per net keeps every gate's scope clear.

### D-S4-06. The modules' own copper

**Decision.** U30: TXD straight from pin 2 to R305.1; TIMEPULSE straight at x 10.0 (0.05 mm off U30.4 and R307.1,
which step 3 placed 0.1 mm apart); SAFEBOOT_N west to TP30; 3V3_GNSS: pin 8 straight up to C301.1 and on to FB30.2,
pins 7 / 8 joined 0.25 mm beyond their pad ends under their own T-paste (R7 / R8's join), C300.1 off pin 7 by one
45-degree run; C301.2 (GND) has its own 0.3 mm lead to a via north of it. U31: R8's copper in U31's frame (3V3_RADIO
through C310 / C312 / C311, MISO to R314, the TXEN loop round U31's west side on B.Cu, 22.72 mm as R8), 3V3_RADIO
re-drawn from step 3's FB31.

**Basis.** route_check profile r9 finds no instance but information ones (R7 / R8 precedents: the in-pad final
segments at C300.1, C310.1 and TP30, the lines through D30.1 / D31.1, the TXEN u-turn, the 3V3_GNSS width change at
its T). C301.2 is boxed by C300.1 (0.46 mm), C301.1 and the pin-7 / pin-8 join, so a pour-only connection was a
one-spoke thermal relief (KiCad starved_thermal); check_r7.thermal_policy keeps the pad's thermal setting, the lead
and via give it its return (DRC clean). R-12 GNSS VCC series 0.088 ohm (limit 0.2).

### D-S4-07. Strip pours on four layers

**Decision.** GND pours R9_GND_F_strip / _B_ / _In1_ / _In2_strip over x 0.3-45.7, y 0.3-23.0 with R7 / R8's
per-layer settings (F / B: 0.15 mm clearance, THT thermal; In1: 0.25 mm, thermal; In2 0.25 mm, THT thermal). Step 8
extends F.Cu, B.Cu and In1 over the board; step 6 owns In2 forward of y 23.0 (and must keep y < y_f GND only, R-2).

**Basis.** R-2 / R-4 / R-5 / R-7 need the strip's ground now; board-wide pours at this step would starve unrouted pads
elsewhere (two starved_thermal DRC errors in a trial).

### D-S4-08. The step gate

**Decision.** `m3_design/r9_rf_check.py` gates: frames; R7 congruence (recorded deviations only); the launches against
R7's J31 from git 431025d (vias, foreign copper, F.Cu GND copper XOR <= 0.02 mm2, the In1 cut-out); check_r9 R-1 ...
R-13, LC-1, K-copper; GCPW Z0 from tools/gcpw_solve.py at every R-5 line sample within 50 +- 2.5 ohm; route_check
profile r9; DRC with parity (no strip net open); the corridors. `tools/test_r9_rf.py` (16 tests) seeds a defect for
each gate.

**Basis.** r9_plan §4 step 4 verify list. Measured: all gates OK; GCPW 79 line samples, gap pairs 0.26-0.32 mm,
Z0 50.16-51.08 ohm (coated, over In1).

## Step 5: pyro block

### D-S5-01. The ARM1_SENSE corridor east of J122

**Decision.** J122's east tie hole moves from (29.9, 59) to (30.8, 59); C92 to (34.1, 57.9) and TP91 to (34.0, 59.35)
to clear it; C121 turns 90 degrees at (33.4, 66.6) (RAW_ACT pad forward, GND pad aft); U13 moves 0.5 mm east to
(31.5, 53.5). The ARM1_SENSE lane then runs straight down x 28.53 from the divider to R170.

**Basis.** plan_spine §5.1 chose the east route (no via on the sense lane; it crosses J122's RAW mouth on F.Cu over In1
GND, the spine dipping to B.Cu / In2). Measured on the step-3 placement: rule A + 0.2 mm to J122.11 (RAW_ACT) needs the
lane centre at x >= 28.41, the tie hole (copper to edge 0.5 mm) needed <= 27.95 and C121's GND pad <= 28.05; a dogleg
between the two disks cleared J122.10 by 0.04 mm only. Moving C121 0.6 mm east broke M-5's support top floor (4.539
against 5.008 mm), so it turns instead (its body box keeps 5.13 mm). U13's CAM_5V pad was 0.52 mm from the lane; at
x 31.5 it is >= 1.0 mm. M-3 holds (2.68 mm past J122's courtyard, the tie line inside every plug, the 4 mm channel
clear; TP91 >= 2.0 mm from the tie path); the step-3 gate passes (legaliser, fit, f1 252.3 Hz, MST 1461.4 mm).

### D-S5-02. R170 on the top, east of U1.33

**Decision.** R170 at (28.1, 47.0), rotation 180, top: ARM1_SENSE_MCU runs straight from U1.33 (2.12 mm, P-8) and
ARM1_SENSE arrives from the north on F.Cu: the whole ARM path has no via.

**Basis.** On the bottom the path needed two layer changes, each with a GND partner (AGENTS §3), and M-6 keeps every ARM
via >= 1.0 mm from bottom courtyards (R170, R172, R177, C15, C90 left no spot). R170.2 must stay >= 1.0 mm from U1.34
(P-5: RAW_ACT_SENSE_MCU on ARM1_SENSE_MCU is a forbidden pair under 1.0 mm): 1.037 mm at x 28.1. Consequence for step 7
(recorded in the handoff): U1.27-U1.31's eastward lanes cross the ARM lane on B.Cu, with vias in the 1.6 mm between
U1's pad ends and the lane (pins 28, 29, 31 are slow status / enable lines).

### D-S5-03. The gate and CONT rows on one line

**Decision.** R126 (y 60.23), C126 (60.53), C127 (10.8, 60.53), R130 (12.2) and R178 (13.2) put every GATE and CONT
row pad on y 61.23: one straight GATE run R126.2 - C126.1 - R128.1 and one CONT run R178.1 - R130.1 - C127.1; R178.1
sits under R129.2 (one CONT column, x 13.2); the CONT exit leaves between C127.2 and R130.2 (0.24 mm each side).

**Basis.** R128.1 (GATE) to C127.1 (CONT) was 1.48 mm on the step-3 placement: a fires-class pair (0.41 V on the gate
in reset, bridge_table) under the step's 1.5 mm; now 1.68 mm (GS 1.2 holds with 0.48). Pads on one line give straight
runs with centred pad entries.

### D-S5-04. The CONT / COLD cluster and C128, C129

**Decision.** R129 (13.2, 65.1) and R173 (13.2, 67.0): OUT north on the OUT branch line, MID between, CONT south; R131
rotation 0 at (14.9, 67.66) (OUT west on the branch, COLD east); D120 at (17.9, 70.08) with its COLD pad on R131.2's
45-degree line; C128 at (6.0, 63.825), its OUT pad on the drain land's west tab line; C129 at (23.4, 78.7) on
R175.2's 45-degree line.

**Basis.** flowline's arrangement (r9_plan §1): each divider top's own pads face away from its taps, so rule C's
margin rises from R8's 0.077 to 0.277 mm. R131 rotation 90 (step 3) sent COLD back past its own OUT pad. D120's 3V3 pad
and its feed stay >= 3 mm from armed copper (X2 = X2b = 0, X2c >= 3: measured none within 3 mm). The AON7524 land is
a 2.45 x 1.98 mm body with a 0.38 x 0.43 mm tab on the pad's centre line (the footprint's custom pad): a C128 branch
beside the tab touched the land by track width only (route_check overlap_only_joint), on the tab line it enters the
body straight. C129.2 (GND) keeps 0.37 mm from the ARM lane's knee.

### D-S5-05. The west tie hole and D120's 3V3

**Decision.** J122's west tie hole moves from (16, 62) to (15.6, 62). D120.3's 3V3 drops to D120.1's line, turns 45
degrees to x 17.9 and runs south past J122's west end to a via at (17.9, 56.3), outside the CH1 hull + 1 mm, where
step 6's In2 3V3 region must reach it.

**Basis.** P-3 keeps In1 / In2 GND-only inside the hull, so the feed must leave on F.Cu, and J122's west end is the only
way out (the IGN bar, the OUT bar and J121 close the others). At (16, 62) the window between the hole (copper to edge
0.5 mm) and J122.2 (RAW_ACT pin rule 0.3 mm) was 0.04 mm; at 15.6 the lane keeps 0.6 and 0.39 mm. R178.1 keeps
0.53 mm from the hole. M-3 holds (2.28 mm past J122's courtyard). The feed is drawn here, not by step 6, so the gate
can hold it to the pyro rules (F, P-6, P-7, X2) on the step's own board.

### D-S5-06. TP122 and its GND partner

**Decision.** TP122 at (7.58, 63.5) on the bottom, one 45-degree B.Cu run from the gate via (9.125, 61.955), which sits
at the GATE run's knee; the gate via's GND partner is Q124's source via (10.425, 62.45), 1.39 mm away.

**Basis.** survey P-9 / plan_flowline §7.1 (removes A8): no via in TP122, a GND via within 1.5 mm of the layer change
(AGENTS §3). TP122's pad keeps 1.77 mm from the partner's ring (bare test pads 1.0 mm), no bottom part within 2.0 mm,
2.35 mm from the nearest armed pad (Z5 >= 2.0).

### D-S5-07. The step draws every CH1 net whole

**Decision.** r9_pyro.py draws PYRO1_BUS / IGN / OUT / GATE / GATE_N / CONT / CONT_MID / CONT_MCU / COLD and ARM1_SENSE /
SENSE_MID / SENSE_MCU from the terminals to U1's pins (the 4.7 kΩ at the MCU end included), the column's own GND copper
(Q124's source return, the GATE_N guard, TP122's partner) and D120's 3V3 feed. RAW_ACT (J124.2's branch, the spine), the
GND pours and the small parts' GND stitching, and the RAW_ACT_SENSE divider are later steps'.

**Basis.** The step's verify list (GATE_N's neighbours, P-8, the coat region, P-1 with the exits' copper) needs the
exits; one owner per net (D-S4-05). Step 7's "pyro" family is left the RAW_ACT_SENSE divider (R8 drew it in its pyro
family).

### D-S5-08. The fire loop and the board's track widths

**Decision.** The bars on F.Cu at 1.0 mm: J124.1 - R134.2 and R134.1 - J121.2 straight on the terminals' pin lines,
J121.1 straight into the drain land (ending 0.6 mm inside its forward edge); the C128 branch 0.4 mm, Q124's source comb
0.3 mm to two GND vias, every other track 0.2 mm. The board's widths are now 0.15, 0.2, 0.25, 0.3, 0.4 and 1.0 mm (X5's
done limit 6; review pass 1 drops 0.15 with RADIO_TXEN at 0.2 mm, D-F1-02: five widths); step 6's RAW branch to J124.2
takes 1.0 mm.

**Basis.** MARGIN P1-9 (adiabatic: 1 mm x 1 oz rises about 6 K at 8.8 A / 20 ms; the fire pulse is <= 4.1 A, <= 20 ms
(F7), about 1.3 K by the I² scaling, Calc). Bar copper 3.15 / 4.96 / 4.96 mΩ (OUT / BUS / IGN, 1 oz at 85 °C, Calc)
against F7's 0.3 Ω allowance for leads, fuse and harness; F7's revalidation on the final copper (dc_solve) is the
records step's. The OUT bar's cap keeps 1.7 mm from the source pins (rule D + 0.2 needs 0.7; ending at the pad centre
gave 0.66).

### D-S5-09. Divider pad entries

**Decision.** A track into an 0402 divider pad that faces the part's other (live or sense) pad ends 0.1 mm past the
pad centre, away from it: the BUS tap into R132.1, the OUT branch into R131.1, CONT_MID out of R173.2 and ARM1_SENSE_MID
out of R132.2, COLD out of R131.2.

**Basis.** The part's own pads are exempt from rules C / F, its tracks are not: 0.29 mm between an 0402's pads leaves a
centre-ended 0.2 mm track 0.477 mm from the other pad, under rule C + 0.2 (0.5); 0.1 mm outward gives 0.577.

### D-S5-10. GATE_N and its guard

**Decision.** GATE_N runs R126.1 - R127.1, east on R127.1's line, one 45-degree run to 0.5 mm outside U1.3 and straight
into the pin: F.Cu, no via, 11.97 mm. A GND guard runs on its north-east side at a uniform 1.24 mm (centre lines) from
C126.2 to a GND via between C11.2 and C10.2 (13.5, 54.6), which is also C10 / C11's GND stitch.

**Basis.** r9_plan §1 graft (a GND guard beside GATE_N). The guard faces U1's forward-face escapes and C10 / C11 /
R164's vias (the region the other lanes can reach); the via spot is the only legal one on that line (C10 / C11's
pads on B.Cu; a 0.5 mm guard has none near U1); the CONT lane runs 3.3 mm away (centre lines), so it needs no guard of
its own. Measured: GATE_N's only neighbour within 1.5 mm is GND (the guard via 0.89 mm). After step 8's In1 pour the
guard lies on a path between a pad and the pour island (route_check: live).

### D-S5-11. PYRO_BLOCK counts exit copper only within 15b's reach

**Decision.** r9_legalise.block_area adds an exit-net track only where it lies within check_actuators 15b's reach of a
CH1 pad of its net (EXIT_REACH plus the pad's half diagonal from the pad centre, sampled at 0.05 mm), no longer by the
track's whole bounding box. r9_pyro.py re-derives PYRO_BLOCK with its copper.

**Basis.** P-1 and 15b require only that reach. A long GATE_N run's bounding box pulled the area, and with it rule G's
DRU scope and the coat region, out to U1's pins (rule G then measured the pin entry against the sentinel pins, P-10
against U4). Step 3's area (no copper) is unchanged; the area is a superset of what P-1 and 15b check (both pass).

### D-S5-12. Zone fill margins in the design rules

**Decision.** m3_design/r9_dru.py adds, after rule A2 and before rule H, one rule per pyro rule A-G and A2, "R9 fill
margin <X>": rule X's condition on pairs with a zone, minimum raised by 0.25 mm (E: 0.35 mm). check_actuators DRU_SHA
is re-pinned (ea77b791eaa4026d), so check_r9 CHECK_ACTUATORS_SHA (3f22b273…); r9_sch_check's fill-equivalence test
removes the fill block to isolate the LC-1 change (r9_dru.without_fill); test_r9_sch adds the fill-rule test.

**Basis.** r9_plan §2 done row Z1 (every pyro margin >= max(R8, 0.2 mm); E keeps R8's 0.30) and +0.05 mm for the
filler's arc tolerance. A fill stops exactly at the clearance that governs it, so the GND, RAW_ACT and power pours of
steps 6 and 8 would otherwise meet rules D and A with no margin (R8: 0.001 mm). Stricter only: zones only, after the
rule each repeats (it governs those pairs), no pad, track or via pair changes, rule H still last (P-4). Measured
(test_r9_pyro): a GND pour over the column keeps 0.751 mm from armed copper (rule D margin 0.251) with the rules and
0.501 mm without.

### D-S5-13. Rule G's margin at U1.3's entry

**Decision.** The step gate holds every pair of rules A-H and A2 to its Z1 floor but one: GATE_N's entry into U1.3,
0.412 mm from the no-net sentinel pins U1.2 / U1.4 (rule G 0.3 holds; margin 0.112). The gate excepts exactly those
pairs (U1.2 / U1.4, no net); recorded as a done-row deviation for the owner's list.

**Basis.** Geometry: the LQFP pitch is 0.5 mm and U1's courtyard ends 0.3 mm past the pad ends, so copper entering
pin 3 straight is 0.39-0.42 mm from the neighbours' corners just outside the courtyard; pyro_probe clips gate copper at
U1's courtyard (D-S1-20), DRC exempts the whole segment. The neighbours are the sentinel pins check_actuators 5 places
beside the gate pin (no net: bridge class "no consequence", 0 V in reset). The scorecard's Z1g (R8's step-9 requalify,
G for gate copper touching PYRO_BLOCK, whole segments) is 0.27 mm on this board (GATE_N's 45-degree run 0.57 mm from
U1.2; step5_evidence/requalify_pyro.json): the done row holds by its own measure; the 0.112 is pyro_probe's stricter,
clipped P-1b scope at the pin stub.

### D-S5-14. The step gate

**Decision.** m3_design/r9_pyro_check.py: template (the copper equals r9_pyro's pad-derived template), margins
(pyro_probe; every A-H / A2 pair >= minimum + max(R8, 0.2), D-S5-13's exception), bridges (no forbidden pair; no
fires-class pair between parts under 1.5 mm), rule_h (rule_h_seed on the board), gate_n (every copper item within
1.5 mm of GATE_N outside U1's courtyard, but U1's and the gate network's own pads, is GND, no-net or < 0.2 V in reset),
sense (the divider-fault analysis' layout preconditions: the MCU sides have no above-logic copper within 1.5 mm; every
sense lane's neighbours listed), armed (X2 / X2b), contract (check_r9 LC-1, P-0 … P-11, M-6, R-13, K-power-pyro,
K-copper, K-inner, K-actuators), actuators, DRC with parity (no CH1 net open; the step's GND / 3V3 vias pending),
route (route_check r9; only the step's own GND / 3V3 items pending steps 6 and 8). tools/test_r9_pyro.py (19 tests)
seeds a defect for each.

**Basis.** r9_plan §4 step 5's verify list. "Neighbour" is taken as 1.5 mm, the bridge table's reach and the step's
fires-class distance (a credible single defect); U1's own pads are excepted as P-1b excepts U1's courtyard (pins 1 and
6 sit 0.83 / 1.31 mm from GATE_N's last 0.2 mm outside it; P-7's 0.5 mm holds). Measured on the built board
(a6454f78…): all gates OK; margins A 0.32, B 0.32, C 0.277, D 0.27, G 0.112 (D-S5-13), H 0.225 (H+ 0.025, GS 0.48);
E, F, A2 no pair within reach; 129 bridge pairs under 1.5 mm, none forbidden, no fires-class pair between parts;
GATE_N's neighbours GND only; no foreign net within 3 mm of armed copper; exit track 66.4 mm (Z2r9 <= 80); Z5 2.35 mm;
P-8 2.86 / 2.12 mm; P-10 U4 5.53 mm; P-11 wire room 6.353 mm.

### D-S5-15. test_r9_rf reads the step-4 tables

**Decision.** test_r9_rf's drawn-nets test compares r9_rf's own copper tables with the strip nets, and checks they are
on the board, instead of every net on the board.

**Basis.** From step 5 on, later steps' nets share the board; the test's intent (D-S4-05: step 4 draws exactly the
strip-internal nets) is unchanged.

## Step 6: power

### D-S6-01. The east column re-placed for its copper

**Decision.** 42 rows of `r9_place.tsv` change (each basis names its D-S6), all on the east column and the battery
band. U9 turns to the bottom at rot 90 (40.3, 90.4): its IN bar faces west onto the BAT_IN pour beside Q120's drain,
OUT faces east to its column. Its network packs round it: R82 / R83 (OVLO) north, C81 / R84 (DVDT / ILIM) south, R81
(EN) east, C88 on the IN bar's line, C87 (EN) on the top. The RAW_PROTECTED output parts go on the trunk: D9 (top) on
U9's vias, R92 on U9's output column, C82 (top) at the trunk's aft end. The actuator driver Q122 / R121 / R122 / R123
forms a column east of the FET pair beside Q120.4 (D-S6-04). The logic block is U11 (bottom, rot 90) forward of the
mid support with R87 / R88 / C98 west and R86 / C85 east, C97 (top) over its IN1 via and C99 between U11 and U2. The 3V3
buck U2 / L1 / C5-C9 sits north of U11 (D-S6-06). C84 is turned with its VLOGIC pad aft. R80 / R165 sit straight
under J1.3 / J1.4, and C89 is turned so its BAT_IN pad faces Q120's drain. The BAT_FAULT_N / LOGIC_SOURCE_ST pull-ups
R89 / R91 go to the MCU end (28.8, 46.9 / 45.0), TP80 onto the bottom BAT_IN pour, and TP87 / TP90 off the U11 network.

**Basis.** Step 3 legalised the east column's small parts "by proposal" (nearest legal spot), not for routing
(r9_step6_progress.md findings 1-4). U9's network boxed its IN / OUT bar ends. C89 / C95 interleaved BAT_IN and
BAT_DAMP. The buck's C5 / C6 / C9 crossed their pins, and Q122 / R121 crossed ACT_DRV and ACT_GATE. Four more limits
shaped the layout:
- the mid support (42, 59.5) clears B and F parts from x >= 37.6, y 55-64 (M-5 floors 4.452 / 5.008 mm);
- the forward support (42, 98) caps the column at y ~93.5;
- the gate network is held apart by P-6, AG and H+ (D-S6-04);
- the east column had no room left for R89 / R91.
The moves were chosen in step-6 session 1 and recovered in session 2 from that session's own edits, the scratch file
being lost in the reboot. With them the step-3, -4 and -5 gates all pass in the build (legaliser, DRC, fit (support
bottom 4.600 mm, top 5.008), f1 252.3 Hz, F9-1, tabs, MST 1425.7 mm; RF strip; pyro block).

### D-S6-02. The 7.7 A path: three layers, no series via

**Decision.** J1.1 -> BAT_IN (B.Cu pour, F.Cu pour, In2 region; 9 vias) -> Q120 -> ACT_FET_S (the B.Cu bridge between
the facing source rows, an F.Cu plate over Q121's source row joined by 8 vias) -> Q121 -> RAW_ACT (B.Cu pour from Q121's
drain down the spine to J122's RAW row, F.Cu pour x 29.4-35.75, the In2 region round J122 and the spine; 31 vias: a
row and two columns round Q121's drain, then a 1.8 mm grid) -> J122.2 / 5 / 8 / 11, J124.2 (F.Cu 1.0 mm bar on its pin
line, D-S5-08) and C121 / C150 / C151. The input damper (C89 == C95 == R166, 1.0 mm), R80's BAT_IN tap, the switch legs
and U9's IN feed (C88.1 into the IN bar's west end, 0.3 mm) complete BAT_IN.

**Basis.** r9_plan section 3 / plan_spine section 4: no series via, the spine on F.Cu, B.Cu and In2 in parallel, the
FETs face to face. R8 D12's limits and the r9_plan section 2 rows (every rise <= R8, D_raw <= 1.0 mOhm, vias <= 1 A,
MARGIN P1-9), measured by tools/run_dc.sh (dc_solve --necks, IPC-2152, no plane credit) on the built board 47fb298d…:

| Path | Grid | R | Neck | Rise | R8 (same grid) | Largest via |
|---|---|---|---|---|---|---|
| RAW_ACT Q121 -> J122 | 0.1 | 0.79 mOhm | 7.82 mm B.Cu | 12.7 C | 17.6 C, 1.45 mOhm | 0.46 A |
| | 0.05 | 0.79 mOhm | 7.84 mm | 12.7 C | 17.5 C | 0.46 A |
| BAT_IN J1.1 -> Q120 | 0.1 | 0.17 mOhm | 8.19 mm B.Cu | 12.1 C | 14.8 C | 0.65 A |
| | 0.05 | 0.16 mOhm | 8.15 mm | 12.1 C | 14.5 C | 0.61 A |
| ACT_FET_S Q120 -> Q121 | 0.1 | 0.27 mOhm | 5.11 mm B.Cu | 20.8 C | 22.3 C | 0.25 A |
| | 0.05 | 0.26 mOhm | 5.18 mm | 20.4 C | 21.4-21.5 C | 0.22 A |

C120 / R120 sit west of the bridge (on it, ACT_FET_S rose 23.3 C, over R8's 22.3); the F.Cu plate took it to 20.8 C.
The ACT_FET_S neck is set by the FETs' own source pins (plan_spine 5.3), so the stretch row "all three inside 20 C"
stays 0.8 C short at 0.1 mm. Inference (as R8): the long-conductor fit overstates a 3.5 mm bridge cooled by the FET
bodies. J124.2's bar adds 10.5 mOhm in the ARM fire path (dc_solve RAW_ACT Q121 -> J124.2; R8 0.44): 0.5 % of R134's
2 ohm. The fire pulse is <= 4.1 A, <= 20 ms, and a 1.0 mm bar is adiabatic there (MARGIN P1-9). F7's fire-loop
revalidation stays step 9/10's.

### D-S6-03. In2: four regions

**Decision.** In2 is GND (R9_GND_In2, from the strip pour's edge y 23.0 to the forward edge) less three regions:
- RAW_ACT: the spine column and J122's whole footprint, stepping round the CH1 hull;
- BAT_IN: J1.1 to Q120's drain, trimmed to the outer pours' extent (y <= 99.2);
- 3V3: the MCU domain from y 23.5, its north edge following the CH1 hull, the camera translator tongue, and a 1.5 mm
  finger up the spine's east side to the buck's output via and its FB sense via.
No In2 track.

**Basis.** r9_plan section 3 ("four simple power regions"). P-3: GND only in the CH1 hull + 1 mm (no foreign net).
D18 / X9c: inner RAW_ACT / BAT_IN >= 2.65 mm in plan view from bus / igniter / drain copper, measured 4.953 mm (R8
2.65). R-2: In2 GND-only below y_f. R8 D97 trimmed In2 BAT_IN where it carries no current; here the trim also removes
an In2 GND finger at the forward edge (route_check pour_finger). DC unchanged (0.17 mOhm). D120's 3V3 via (17.9, 56.3)
lands in the 3V3 region (the step-5 pending item). Each region fills as one piece: RAW_ACT 244.5, BAT_IN 115.3, 3V3
1098.9 mm². The finger carries the buck's output: on F.Cu, C84's VLOGIC pad and the RAW_PROTECTED pour block every
other path (D-S6-13 on the perimeter row).

### D-S6-04. The actuator switch's gate network

**Decision.** ACT_GATE is a B.Cu bus on Q121.4's row with three things on it: C120.2 (2.2 µF to source), R120.2 (100 k
to source) and TP121. One F.Cu hop (y 87.4) crosses the ACT_FET_S bridge to the east via (37.35, 89.0). That via
takes Q120.4 (a 45-degree exit from the pad centre) and R121.1. The driver column (B.Cu, x 37.35 / 36.4) runs Q122.3
-> R121.2 (ACT_DRV) and Q122.1 -> R122.2 -> R123.1 (ACT_EN). R122.1 takes RAW_PROTECTED by a via between C84's pads.

**Basis.** The facing FETs' gate pins sit at opposite corners (inherent; R8 D20 / spike (c)), so one crossing is
needed; it is on F.Cu over the bridge's B.Cu, the bridge pour unbroken. The strict pad rules measure on the built
board:
- P-6 (bare gate pads >= 1.0 mm from always-live pads): 1.03 mm, R120.2 to C120.1;
- AG (ACT gate pads >= 1.2 mm from GND pads): margin 0.134;
- H+ (>= 1.2 mm from RAW_ACT pads): margin 0.025 (the pyro pair Q124.5 / R129.2, unchanged).

### D-S6-05. RAW_PROTECTED: an F.Cu pour down the east column

**Decision.** U9.6 runs east on B.Cu to its column x 42.3 (R92.1 on it) and two vias. From the vias an F.Cu pour
(R9_RAW_PROTECTED_F, x 39.85-42.85, y 72.0-91.6, under C84's body) carries the rail to C82.1, with D9.1 on it. The
pour keeps 1.0 mm from the test-pad column and 0.35 mm from C87. Tracks branch off:
- U11's IN1 via (39.3, 68.2), on to U11.2 (B) and C97.1 (F);
- R122;
- TP81;
- the camera branch: R8 D46's route moved +4 mm in y, east of C82, past TP83, round the mid support at x 44.35, down
  x 42.15 between J9's pins and its mounting pads to U7's via (42.15, 31.5), then B.Cu to C71.1, TP70 and U7.3 / U7.4.

**Basis.** U9's current limit (R84) through one via was R8's choice; two vias halve each barrel's share. (Corrected
by review pass 1, D-F1-08: with R84 = 750 Ω U9 limits at 3.96–4.84 A, not R5's 2.2 A; the two vias share at most the
downstream limiters' 3.24 A, 1.62 A each, and U9's own limit is the fault case on the net itself.) As tracks, two
vias between a B.Cu column and an F.Cu trunk form a track loop, and the net then needs five vias (route_check
track_loop and extra_vias: a pourless net may have only need + 2). A pour is the conventional copper for a rail limited
at amperes; it lowers resistance and needs no exception. Measured (dc_solve, 0.1 mm):

| Path | R9 | R8 D49 | Largest via |
|---|---|---|---|
| U9.6 -> U11.2 | 15.0 mOhm | 47.3 | 0.50 A at 0.5 A |
| U9.6 -> U7.3 / 4 | 75.0 mOhm | 76.3 | 1.00 A at 1 A, the single U7 via |
| U9.6 -> TP81 | 8.1 mOhm | 9.8 | |

The U7 via carries the camera rail alone, as in R8; the camera eFuse U7 limits it (R8 D37).

### D-S6-06. VLOGIC and the 3V3 buck

**Decision.**
- VLOGIC (0.4 mm, B.Cu): U11.8 -> U11.1 -> C99.1 -> U2.2 (EN) / U2.3 (VIN) -> C6.1 -> a column x 44.6 to C7.1, with
  TP83's via. One via (38.2, 69.6) feeds the hold-up C84.1 (top).
- U2 (AP63203, bottom, rot 0), per the maker's layout:
  - C6 sits across VIN / GND, the GND side a 1.0 mm strap to U2.4 with its via off the strap;
  - SW runs straight into L1.1;
  - C5 sits BST - SW;
  - L1.2 -> C8.1 -> C9.1 is a 1.0 mm column, with one via into the In2 3V3 finger;
  - FB (pin 1, the fixed 3.3 V part) senses the In2 plane on its own via.

**Basis.** Diodes DS41326 Rev 3-2, PCB Layout items 2-5 and Figure 25 (R8 D40: VIN capacitor close, feedback close to
FB, vias at the capacitors' GND side, GND under the device: In2 is GND under U2, In1 GND). TI SLVSEA3F section 11
(R8 D42): bypass capacitors "as close to the device as possible" (section 12.1 asks for short wide traces; corrected by
review pass 1). C98, U11's USB-input capacitor, sat 5.29 mm of track from U11.7 until the fix pass moved it beside the
pin (D-F1-05). Measured (dc_solve, 0.1 mm):
- VLOGIC U11.1 -> C99.1: 1.23 mOhm (R8 1.91);
- VLOGIC C84.1 -> U2.2 / 3: 9.84 mOhm (R8 2.60): the hold-up sits over the FET pair, not over U2; 3 mV at 0.3 A;
- 3V3 L1.2 -> U1.75 / U1.100 / U1.27 / U3.8: 14.5-15.6 mOhm (R8 15.3-18.8).

### D-S6-07. Camera supplies

**Decision.** The camera buck's copper is R8's CAMERA_TRACKS / CAMERA_GND (D37 / D41, the maker's layout) moved with the
camera block (+4 mm in y). Widths are mapped onto the board's six (0.5 / 0.6 / 0.8 -> 1.0; the 0.7 SW strap -> 0.4,
because 1.0 mm would sit 0.1 mm from U8.4 / U8.6). The CAM_INPUT_LIMITED, CAM_SW, CAM_BST and CAM_FB nets are complete.
CAM_5V is complete to C75, C76, TP72, R78, R71 / C77 and J9.1.

**Basis.** R8 D41 (Diodes DS42002 Rev 3-2 Figure 39) on the unchanged relative arrangement (D-S3-07); X5 <= 6 widths
(r9_plan flowline graft). CAM_5V L3.2 -> J9.1: 2.88 mOhm (R8 2.72), its via 1.0 A at 1 A.

### D-S6-08. U1's decoupling and VCAP

**Decision.** R8 spike (a)'s decoupling and VCAP copper is moved with U1 (-5, -0.5): U3.8 -> C29, VCAP1 / VCAP2, U1.6 /
11 / 27 / 50 / 75 to their caps and In2 vias. C13 and C14, placed differently in R9, get their own taps. The 3V3A pocket
(C21 / C22 / U1.20-21) stays step 7's (step-5 handoff). Seven of the GND vias land in the In2 3V3 region and wait for
step 8's In1 GND (D-S6-10). K-contract's C29 direct route now holds.

**Basis.** R8 D31 / spike (a), qualified, on the same U1-relative arrangement (D-S3-05).

### D-S6-09. The mid support stays at (42, 59.5)

**Decision.** Owner decision 5's east mid support holds: the DC solves pass with it, and the spine copper does not come
near it (RAW_ACT pours end at x 35.75; the camera branch passes it at x 44.35, 0.55 mm from its hole).

**Basis.** R9_OWNER_DECISIONS item 5 ("if the DC solve holds"). The solve holds (D-S6-02), so the fallback (4, 49.5) is
not needed; f1 252.3 Hz.

### D-S6-10. What the step leaves to steps 7 and 8

**Decision.** The step completes BAT_IN, BAT_DAMP, BAT_SW_SOURCE, BAT_SW_RETURN, ACT_FET_S, ACT_GATE, ACT_DRV, ACT_EN,
RAW_PROTECTED, SW_NODE, BST, CAM_INPUT_LIMITED, CAM_SW, CAM_BST, CAM_FB, VCAP1 and VCAP2 (`r9_power.NETS`). Three
nets stay partial, each missing only the pads `r9_power.PARTIAL` names:
- RAW_ACT: R177.1, the RAW_ACT_SENSE divider top (step 7 "pyro", D-S5-07);
- VLOGIC: R60.1, VLOGIC_SENSE's divider top (step 7 status / sense);
- CAM_5V: U13.1, R104.1 and C91.1, the translator supply and sense (step 7 camera).
Step 7 (power_ctl) takes the rest:
- U9's, U11's and U7's control pins and their own GND pins;
- BAT_ENABLE, the status lanes BAT_FAULT_N / LOGIC_SOURCE_ST;
- the 3V3 pull-ups and bypasses, the 3V3A filter;
- USB_LIMITED from U10 to U11, with the corridor note of the handoff.
Step 8's In1 / F.Cu / B.Cu GND pours join the eight GND vias of `r9_power.PENDING` and step 5's guard via.

**Basis.** r9_plan section 4: step 6 is "four In2 regions, the spine, the stitching" plus the logic / camera supplies;
the control and status nets belong to step 7's families. The previous attempt's measured finding stands:
USB_LIMITED has no lane from U10 to U11 that avoids crossing step-7 lanes and the divider tap. The corridor needs those
families planned with it (handoff section 4).

### D-S6-11. F9's hot-plug premise on R9's feed

**Decision.** The premise holds. U9 sits 13.2 mm from J1.1 (F9-1 <= 27.07). It is fed from the B.Cu BAT_IN pour with
R_b 2.32 mOhm (dc_solve J1.1 -> U9.5; R8 17.3) and about 3.2 nH (the model's microstrip estimate of the pour band, its
finger and the 0.3 mm feed). R8's model (`step9/hotplug_feed.py`, unchanged, imported by
`step6_evidence/hotplug_feed_r9.py`) gives U9 IN within 0.0021 V and x1.028 in slew of the protected input node. At
R8's 5 nH bound the figures are 0.0036 V and x1.037. The R4 figures (-14.6 V, 9.2 V/us) then stay inside the TPS25947's
-15 V / 10 V/us (about -14.60 V, 9.46 V/us).

**Basis.** R8 D76 (the same model and corners: harness 0.1-2 µH, derated C80 + C96 and damper, D8 12.65 / 13.3 V,
C88 50 / 100 nF). The lower R_b damps the feed less, so the slew ratio is higher than R8's (x1.008 at 5 nH) but stays
far inside the limit. Inference, as R8: constant derated capacitances, estimated L_b. The bench test (ORDERING
section 5) measures U9 IN.

### D-S6-12. The step gate and its tests

**Decision.** `m3_design/r9_power_check.py` checks the following, appended to `r9_build.sh` after `r9_power.py`:
- template: the board's copper equals a dry run of the builder; nothing else on the step's nets;
- in2: four regions, each one piece, no track;
- dc: run_dc.sh at 0.1 mm against D12, every rise <= R8, D_raw <= 1.0, vias <= 1 A;
- supply: the RAW_PROTECTED / CAM_5V paths' vias <= 1 A, and R_b;
- f9: the hot-plug model, <= 0.01 V and x1.05 up to 5 nH;
- pyro: the step-5 gate's margins, bridges, GATE_N neighbours, sense and X2 on the powered board;
- contract: check_r9, all rules but M-2, K-legends and the camera-bypass routes, P-4 with the board's seeded suite;
- actuators: check_actuators;
- drc: DRC + parity, only the PENDING vias' dangling and the PARTIAL pads open;
- route: route_check r9, only those vias and their straps pending.
`tools/test_r9_power.py` has 19 tests: the judging functions on synthetic inputs and the board gates on seeded defects.

**Basis.** r9_plan section 4 step 6's verify list and the brief's (D18, D85, barrel current, the F9 feed, check_r9
power / pyro rules). The thresholds are the plan's and R8's, never weaker. The f9 limits put the R4 figures inside the
TPS25947's.

### D-S6-13. Done rows missed, with their measured causes

**X2g (CH1 through nets) = 1 (done 0; R8 6).** ACT_GATE's bus ends at TP121 (24.0, 85.86), which step 3 placed in the
empty north-east corner of the CH1 courtyard bounding box (x <= 26.32, y <= 88.61). The spot is outside PYRO_BLOCK
(P-10), 1.95 mm from D8.1 (P-6) and > 3 mm from armed copper (X2 = X2b = 0, P-3 clean), so this is no pyro-safety
finding. A search of every legal TP121 spot on either side within 9 mm of the gate copper, outside that box, found
none. The search used the legaliser, plus 1.0 mm from every foreign track and via. The blockers are C84, the FETs, J1,
D8, R166, D9, C81, PYRO_BLOCK, and the J124.2 RAW bar against the 1.0 mm test-pad rule. For the owner's deviation list.

**P6 (In2 perimeter) = 1201 mm (done <= 900; R8 1752).** The metric counts every region boundary twice (the GND hole
and the region's own outline) and every hole: GND 716 (its outline, the
region boundaries, seven Ø3.2 holes, the U31 all-layer keep-out and the terminals' antipads: 28 voids, the largest
136 mm²), 3V3 294, RAW_ACT 147, BAT_IN 45 (survey_metrics planes). Inference: with the four regions r9_plan section 3
asks for, each boundary counted twice, 900 looks out of reach (plan_spine section 6 estimated 800-900). Dropping the 3V3 finger would save about 70 mm (estimate), but it is the buck's only path (D-S6-03). For
the owner's deviation list; step 7's signal vias will add antipads.

### D-S6-14. Kicad-cli DRC without a GUI session (environment, no repo change)

**Decision.** In a session with no logged-in GUI, kicad-cli 10.0.6's `pcb drc` crashes: BOARD_COMMIT::Push ->
TOOL_MANAGER::doRunAction -> wxGetMousePosition indexes an empty [NSScreen screens]. Step 6 ran every gate with a
scratch dylib that returns (0, 0) for wxGetMousePosition, loaded through DYLD_INSERT_LIBRARIES; kicad-cli's
entitlements allow it. Because /bin/bash strips DYLD_*, r9_build.sh's stages were replayed one by one from KiCad's
python, reading the script's own command lines. Nothing in the repo depends on it.

**Basis.** The step-5 gate on the step-5 board gives exactly its recorded result with the shim (DRC OK, every gate OK),
and two replayed builds are byte-identical. With a GUI session (or screen sharing) logged in, `r9_build.sh` runs as is.

## Step 7: routing families

### D-S7-01. One module per family, one gate per family

**Decision.** `m3_design/r9_route.py FAMILY` draws one family's copper from its module `r9_route_<family>.py`
(NETS, RAILS, optional CONTINUES / PENDING, BUDGET, PADS, draw): explicit octilinear polylines and vias, no
autorouter. The Draw primitives refuse a non-octilinear or zero-length segment, a width outside the board's six, two
vias at one point, a pad that is not where (or on the net) the table says, and a family that draws a net it does not
own or leaves one of its NETS undrawn. `move_via` relocates a via an earlier step's table placed (asserting it is there,
on its net and size): the table move by which rf_if opens the fence (D-S7-03). Fixed KIID seed per family (9910 +
index). `m3_design/r9_route_check.py FAMILY` gates each family on the built board: the template (every done family's
tracks and vias present, moved vias gone, no other copper on their nets), DRC with parity (only step 8's silkscreen
classes and the pending GND vias dangling; no unconnected item on a done family's NETS; every rail / continued pad its
PADS name joined, GND's excepted: they hang on PENDING vias until step 8's In1 pour, which r9_ground_check gates),
route_check profile r9 with its empty allowlist (only the pending GND vias' dangling_via / dead_copper), the family
BUDGET (signal length, signal vias, critical layer changes, worst detour ratio beyond route_check's slack), S4's 70
signal vias on the whole board (stretch 55 reported), the step-5 pyro functions (margins, bridge table, GATE_N's
neighbours, sense MCU sides, X2), check_r9 but M-2 / K-legends (P-7, K-power-pyro's D19, K-inner's D20, R-1 ... R-13
included; K-contract's C100 / C93 camera-bypass items deferred to the camera family) and check_actuators.
`tools/test_r9_route.py` seeds defects into the primitives, the DRC judge and the board gates.

**Basis.** r9_plan section 4 step 7 (family modules; per-family budgets; empty allowlist; P-7; D19) and section 9 of
plan_spine (a `r9_route_check.py` gate per family); R8's r8_route / r8_route_check pattern, with R9's rule contracts in
place of R8's digests.

### D-S7-02. The radio's MCU-end resistors in one row

**Decision.** R315 (RADIO_MOSI series, 22.0, 28.8, rot 90), R310 (RADIO_NSS pull-up, 22.88, 28.8, rot 270) and R313
(RADIO_SCK series, 24.465, 29.45, rot 180) sit in one row at the MCU end, each on its own lane (r9_place.tsv).

**Basis.** check_r9 K-contract: SERIES (nearer U1's centre than U31's: R315 0.92 mm, R313 0.25 mm inside the limit
line) and PULL_END (R310 0.28 mm); R-10 (R313's courtyard 6.04 mm from U1's, >= 5.94). On the lanes the series parts
cost no bend; the step-3 placement gate passes with them.

### D-S7-03. Step 4 closes the fence, rf_if opens its lane gaps

**Decision.** `r9_rf.FENCE_X` is the closed fence (every opening <= 2.0 mm), so step 4's gate holds R-7 before any lane
exists. rf_if moves six fence vias (17.45 -> 17.25, 21.3 -> 20.95, 23.25 -> 23.05, 32.95 -> 32.5, 34.9 -> 35.2,
40.75 -> 41.3), adds one (33.8) and adds the grid via (23.05, 17.4) between its MISO and MOSI lanes. Step 4's grid keeps
four 0.5 mm patches at U31's west pins and FB31 (`GRID_SMALL`) so the MOSI / NSS / SCK lanes keep 0.2 mm.

**Basis.** check_r9 R-7: an opening <= 2.7 mm must be crossed by a lane; the strip's GND reach <= 4.0 mm (the new grid
via closes the strip between the MISO and MOSI lanes). D-S4-05 planned rf_if to open the gaps; a table move in the
family keeps the step-4 board's R-7 true at its own gate.

### D-S7-04. rf_if: every interface lane on F.Cu, no via

**Decision.** The GNSS lanes (TXD, RXD through R306, TP, RESET_N) and the radio lanes (aft bus RXEN / BUSY /
MISO_MCU / MOSI_MCU stepping west past the resistor row and back; NSS / SCK from the east face; DIO1; NRST) run on F.Cu
over In1 GND from pad centre to pad centre, through the fence openings of D-S7-03, with FB30 / FB31 / R310 fed from In2
3V3 by one via each. 15 nets, 333.6 mm, 0 signal vias, worst detour ratio 1.257, 61 bends.

**Basis.** R-11 on the built board: BUSY 5.7, RXEN 5.2, MISO_MCU 6.2, MOSI 7.3, NSS 7.75, SCK 8.35 mm from U30's body
(>= 5.0 / 6.0 for the radio SPI) and >= 6.0 mm from GNSS RF copper; no layer change, so no GND partner is needed
(AGENTS section 3); the rf_if gate passes (D-S7-01).

### D-S7-05. qspi_hse: R8's dives, moved with the cluster

**Decision.** QSPI_IO0 / IO1 / IO3 / CLK and HSE_IN / HSE_OUT are R8's spike (a) dives moved by (-5, -0.5), with their
GND partners and the load caps' straps; C25.2's GND via moves north of its pad (14.53, 49.95): R8's spot lies on the
IMU body's no-via area (M-7). QSPI_NCS, QSPI_IO2 and BOOT0 (R8's members) move to imu_baro: they leave U1's west face and
north-west corner through the IMU's corner, and the bump audit judges a critical net against the copper already drawn,
so IO2 must be drawn together with the IMU lanes it has to avoid. 6 nets, 43.5 mm, 6 signal vias, worst ratio 1.383.

**Basis.** D-S3-05 (the U1 / U3 / Y1 / C25 / C26 / R10 cluster keeps R8's relative placement) and R8 D31 / D86; the
gate passes.

### D-S7-06. U4 turned 180 degrees (a recorded new axis map)

**Decision.** U4 stays on the bottom at (12.0, 47.4) and turns 180 degrees. Axis map for R9: +X_imu = -x_board,
+Y_imu = -y_board, +Z_imu out of the bottom face (unchanged); roll = -gyro_Y; thrust reads -a_Y; the lever arm is
unchanged (|x - 23| = 11.0 mm). check_r9 M-7 now keys the required rotation on the title-block revision (R7 / R8: 0, the
M3_R5 map; R9: 180, this map), so an accidental turn still fails; the R9 firmware binding note must carry the map, and
a bench sign check (rotate the board about +y, read gyro_Y's sign) precedes flight.

**Basis.** survey_constraints section 1.4 lists the IMU's side, place and rotation as free in R9 "with a recorded axis
map". The routing aid (scratch `s7/aid/west5.py`, a negotiated-congestion router, with `ratios.py` applying route_check's
detour test, len > 1.6 x MST and > MST + 2 mm) on the placed board:
- rotation 0, U4 where placed: U1's west face runs SCK 45.0, MISO 45.5, MOSI 46.0, NCS 46.5, CS 47.0 ... INT1 49.5 (pin
  y), while U4's west column runs INT1, GND, GND, MISO (south to north) and its north row MOSI, SCK, CS. INT1's short
  route then encloses U4.2 / U4.3 (GND) against the IMU body (no via can sit there: U1's west pads on F.Cu, x 9.3-11.6),
  and every route round them fails the detour test (MST 3.0 mm; best found 6.3 mm); MISO / MOSI / CS / SCK need wraps
  (9 variants: resistor column, LEDs, C18 / C31 removed; none passes);
- U4 can move only east, by <= 1.97 mm (Y1's courtyard; U3 south, P-10 west and north): CS / MISO / MOSI still fail;
- rotation 180 (same spot): INT1 3.5 mm (ratio 1.07), MISO 4.4, MOSI 2.9, NCS 4.8 mm, U4.2 / U4.3 straight to C30.2's
  GND, all within the test; SCK and CS reach their south-row pads through a south-band via and a pad-end entry (estimate,
  imu_baro designs them; R10 / R11 may move).
The IMU body and interior keep-outs are symmetric about U4's centre, so step 3's rule areas are unchanged.

### D-S7-07. Family order: pyro, servo, imu_baro before usb_swd

**Decision.** `r9_route.FAMILIES` = rf_if, qspi_hse, pyro, servo, imu_baro, usb_swd, camera, status, power_ctl, links
(KIID seed 9910 + index: pyro 9912 and servo 9913 unchanged, imu_baro 9914).

**Basis.** A family's gate takes every family before it as done (D-S7-01), so imu_baro could not gate while usb_swd, with
no module yet, stood ahead of it. The three families share no net with usb_swd; usb_swd's escapes past the IMU knot are
left open (D-S7-10).

### D-S7-08. pyro: the RAW_ACT_SENSE divider re-placed, battery-live copper 1.35 mm

**Decision.** The divider moves (r9_place.tsv): R177 (27.88, 56.6) and R124 (29.64, 56.6) in a row, R125 (30.5, 55.5),
R182 (30.5, 54.4), C122 (30.77, 53.2) with their SENSE pads on one column x 30.07, and R172 (25.85, 46.1, rot 0) under
U1's east pad ends at U1.34. Copper, all B.Cu but U1.34's stub: one via (27.45, 57.95) from In2's RAW_ACT region (step
6's PARTIAL rail) straight into R177.1; MID straight across into R124.1 under the ARM lane; SENSE down the column, one
45-degree step onto y 52.45, west, one 45-degree corner and down x 25.42 into R172.1; U1.34 east on F.Cu to the via
(26.95, 46.1) and B.Cu into R172.2. 3 nets, 17.6 mm, 1 signal via, worst ratio 1.0; budget 18.0 mm / 1 via / 1.45.

**Basis.** D-S5-07 / D-S6-10 leave the divider and R177.1 to this family. The battery-live part (RAW_ACT) is the 1.35 mm
tap instead of a lane; the sense node (1 / 11.2 of the battery: 10.2 k over 1.0 k) is the long run. The tap sits west of the
ARM1_SENSE F.Cu lane (0.73 mm from it): east of the lane the J122 tie hole's 0.5 mm Edge.Cuts clearance leaves no via
spot inside the RAW_ACT region (y >= 57.0). Bridge table (P-5, step 3 gate): R177.1 >= 1.0 mm from R124.1, every sense
pad >= 1.0 mm from the 3V3 pads of C90 / R89 / R91. P-8: U1.34 to R172.2 is 2.24 mm of track (<= 3.0). The sense nets
are not route_check critical, so the MCU-side via needs no GND partner; R125.2 / R182.2 / C122.2 are step 8's. The pyro
gate passes on the step's board. Step 6's template gate owns RAW_ACT as a PARTIAL net and stays a step-6 gate (it runs on
the step-6 board in the build; step-6 handoff section 4); test_r9_power, which runs it on the latest board, now expects
exactly the copper a drawn family's table adds to a PARTIAL net it CONTINUES (`continued_extras`) and nothing else, and a
seeded RAW_ACT track beside the tap is still named extra.

### D-S7-09. servo: D121 turned between the lane vias, one via per lane

**Decision.** D121 turns 90 degrees to (23.0, 55.35) and the pull-downs move beside the lane vias: R154 (18.05, 53.75),
R155 (19.25, 53.97), R156 (26.75, 53.97), R157 (27.95, 53.75), all rot 90, bottom. Each lane runs on F.Cu from U1.22-25
in pin order into its 1 k (R150-R153, top, under the plug columns, D-S3-06) and on to one via in the gap beside the 1 k
column (18.05 / 20.46 / 25.54 / 27.95); on B.Cu the via runs into its clamp pin and its pull-down (D121 pins counter-
clockwise S1 NW, S2 SW, S3 SE, S4 NE, like the vias west to east, so every link is planar). OUT: one straight F.Cu
segment per lane into J122. D121.2 (GND) and D121.5 (3V3) strap sideways to one via each in the column gaps; U1.19 (GND),
boxed in by S1, drops to one GND via. 8 nets, 48.5 mm, 4 signal vias, worst ratio 1.298; budget 50.0 / 4 / 1.40.

**Basis.** check_actuators 7's chain (MCU, then pull-down and clamp, then the 1 k, then the header) on the built board;
the bottom clamp and pull-downs force one layer change per lane, the servo lanes are not critical (no GND partner
needed). The outer lanes turn on y 53.85, clear of the y 53.3 band where the status family drops U1.17 / 18. D19: the
gate lanes are 8 mm away. The GND vias are PENDING (step 8's In1); the pull-downs' GND pads are step 8's.

### D-S7-10. imu_baro: the west knot, its parts re-placed, two step-6 table edits

**Decision.** Parts (r9_place.tsv, all bottom): R5 (8.0, 46.67, 90) beside BOOT0's west via; R10 (15.0, 46.19, 0) on
one B.Cu line U3.1 - NCS via - R10.1 (its R8 spot is where the SCK / MISO vias must be); R11 (9.2, 45.25, 90) west of
U1's pins 89 / 90; R12 (2.0, 50.87, 90) and R13 (4.97, 54.05, 270) beside the I2C vias; R64 (6.23, 53.78, 270) straight
north of U5.6; R164 (12.325, 57.4, 180) so that R164.2 heads one 3V3A trunk x 11.5 over C10.1 / C11.1; C30 (12.05,
50.23, 270) and C31 (9.7, 48.57, 270) on the 3V3A rail; C32 (2.0, 48.15, 180) at its west end; C21 (23.1, 50.75, 0) and
C22 (22.0, 48.8, 90) under U1 beside the inward 3V3A via of U1.20 / 21, off the forward face that the servo lanes use.
Step-6 table edits (r9_power.py): R10 leaves the step-6 parts (its 3V3 strap is now this family's; C23's strap ends at
C23.1); C18.2's GND via moves from (12.88, 49.85) to (13.2, 50.05), clear of INT1's 45-degree run. Routes (module
docstring): SPI inward to vias under U1 and into U4's pads from below; NCS inward; CS and BOOT0 by 45-degree stubs to
west vias; INT1 inward into pad 4; QSPI_IO2 by the one F.Cu corridor from U1.1 round INT1's and NCS's vias to U3.3; I2C
on F.Cu over the buzzer LS120 between its pads to vias west and north of U5; 3V3A as one B.Cu trunk, a "U" round U4's
GND pads, an east line to U1.20 / 21 and a west line to U5. 12 nets, 64.0 mm, 10 signal vias, 6 critical layer changes
(SPI x3, CS, NCS, IO2, each with a GND via within 1.5 mm), worst ratio 1.34; board 30 signal vias (S4 <= 70).

**Basis.** D-S7-06 (the turned IMU) and D-S7-05 (NCS / IO2 / BOOT0 move here). The 0.5 mm pin pitch leaves a via on a
pin's own line exactly 0.15 mm from the next pin's lane, so every west escape turns 45 degrees before its via. The CS
net was the detour test's case: with R11 under pins 90 / 91 on the run's T the net measured 5.32 mm against an MST of
2.63 mm (ratio 2.02, excess 2.69 > route_check's 2 mm); with R11 on a branch off the west step's corner its pad lengthens
the MST to 3.12 mm and the net is 4.90 mm (within the slack). K-copper drove the small moves: no via ring on a paste
aperture and no via hole within 0.1 mm of one (R11 off the CS via, G_CS off R5.2). Neighbours kept open (edge clearances computed on the
step's board for sketched escapes): USB_FAULT_N's west via about (9.25, 44.0) (R11.2 0.29 mm off it) and its B.Cu run
south; LED_RED / LED_YEL on F.Cu west, LED_YEL turning south-west at x <= 8.95 (0.23 mm past R11's 3V3 via); pins 17 /
18 north into the servo family's y 53.3 band. The imu_baro gate passes on the step's board.

### D-S7-11. usb_swd: D4 bridged under its body, VBUS east of D4, NRST and USB_FAULT_N by interior exits

**Decision.** Parts (r9_place.tsv): D4 0.05 mm aft (9.95, 34.1) so that its DP pins sit on J3's DP lane; R9 (9.95, 32.4,
90) and R7 (9.0, 32.4, 90) on the VBUS side beside J3; R90 (14.6, 34.8, 180) beside USB_FAULT_N's B.Cu lane; TP86 (13.6,
25.9) south of U10, 1 mm clear of the VBUS copper; C23 (the 3V3 bulk) to (22.8, 36.8, 180) off U1's west face. Step-6
table edits (r9_power.py): C23's PARTS row and strap (to C16.1; the via (11.7, 42.75) sat in USB_FAULT_N's interior
lane and is gone). Copper (module docstring): USB data on F.Cu only, J3's pin pairs joined by the inner U (DM) and the T
(DP), D4's pin pairs bridged under its body (R8's way), one DM jog of 0.4 mm on a 0.57 mm diagonal; VBUS a B.Cu tree from
J3's two pairs (no loop), D4.5 by the via V_D east of D4; CC by one via each into R7 / R8; VBUS_SENSE by two vias (R9.2
beside J3, F.Cu to U1.65, B.Cu to R110 / TP92); USB_FAULT_N inward on F.Cu to the interior's south-west corner via and
B.Cu south under U1's west pads and U10's body to U10.4, R90 and TP86; USB_ILIM straight; SWDIO / SWCLK on F.Cu west to
J2; NRST inward east of HSE_OUT and parallel to QSPI_IO3, a via under U3's south-west half, B.Cu by W41.44 to J2.3.
11 nets, 135.5 mm, 8 signal vias, 0 critical layer changes, worst ratio 1.495 (NRST); budget 140 / 8 / 0 / 1.50; board
38 signal vias.

**Basis.** D-S7-07 (family order). R-10 / F10: DM leaves its row at x 11.95, so every USB data copper keeps >= 5.0 mm
from R306's courtyard (5.10 mm centre line). D4's GND pin is enclosed by the DM / DP lanes on F.Cu, so the one via that
fits under D4's body (between the bridges) is D4.2's GND; VBUS leaves east. route_check: the tiny_jog rule (a jog's
45-degree run >= 0.5 mm) set the DM jog and D4's 0.05 mm move; J2's footprint keep-out (no track inside its pad
rectangle) keeps the J2 track ends on the pads' outer halves. NRST's ratio is the inward route: U1.14 is sealed north of
the forward face like U1.7 / 8 / 17 and J2 is on the west edge; a via further north-east (18.2, 41.0) measured 1.451 and
crossed QSPI_IO1's B.Cu diagonal, so the budget's ratio is 1.50 (route_check's detour limit 1.6 stays the hygiene gate).
The SWD nets and NRST are not critical classes. D4.2's and J2.5's GND vias wait for step 8 (PENDING).

### D-S7-12. pyro's MCU-side via on pin 34's line

**Decision.** r9_route_pyro.V_MCU moves from (26.95, 46.1) to (26.95, 46.5): U1.34 runs straight east on F.Cu into it,
B.Cu takes one 45-degree step west into R172.2. P-8 stays 2.24 mm of track.

**Basis.** U1.35 (CAM_5V_SENSE) can leave east only on its own line y 46.0, and the old via sat 0.1 mm off that line.
At (26.95, 46.5) the via is 0.15 mm from CAM_5V_SENSE and 0.15 mm from ARM1_SENSE_MCU (y 47.0), DRC's minimum. The
pyro gate (sense neighbours, X2, P-8) passes at its stage and on the later boards.

### D-S7-13. camera: RX hops under TX, OE through the pin-28..31 box, the translator supply under U12

**Decision.** Parts (r9_place.tsv): U13 (the CAM_IO LDO) and C92 to the bottom under U12's north (U13 (37.6, 53.6, 180),
C92 (35.45, 57.72, 270)), C91 (42.15, 53.3) at U13.1, C93 (34.675, 51.875, 90) at U12.7's via; TP90 (33.65, 58.35) and
R103 (35.1, 60.5) on F.Cu off one via; TP91 to F.Cu (32.4, 54.4) beside OE's via; the CAM_5V_SENSE divider beside C76.1
(R104 (32.8, 46.55, 180), R105 (32.8, 47.55), C94 (32.3, 45.4)); R70 (31.6, 36.9, 180) beside U7.7 and TP73 (30.4,
39.3); power_ctl's pull-ups R89 / R91 north to (30.6, 49.6) / (30.6, 51.1), in the box's exit band that their own lanes
use. Step-6 table edit (r9_power.CAMERA_GND): R78.2's GND via from (33.9, 49.2) to (34.675, 50.15) (OE's lane), shared
with U12.2 / C100.2 and C93.2. Copper (module docstring). 15 nets and CAM_5V's three open pads, 107.1 mm, 7 signal vias,
0 critical layer changes, worst ratio 1.332; budget 110 / 7 / 0 / 1.40; board 45 signal vias.

**Basis.** The RX / TX crossing is inherent: at U1 TX (38) is south of RX (37), at U12 RX (4) is on the south row and
TX (5) on the north row, both at the west end. RX hops beside U1 so that B.Cu y 44.5 runs under every F.Cu lane east;
TX stays on F.Cu. U1.28-31 are boxed on F.Cu by ARM1_SENSE_MCU, R170 and the ARM1_SENSE lane (x 28.53), so OE needs a
via; it takes the box's exit band's south edge (y 48.4) and turns north east of the band, so power_ctl's BAT_FAULT_N /
LOGIC_SOURCE_ST can leave the box east above it and turn north at x ~32.8-33.4 (east of C122 / R125 / R182 and of the
hole (30.8, 59), west of OE's via; TP91 is on F.Cu to keep that corridor). In2's 3V3 region ends at x ~33.4 for
y < 52, so U12.3 / C100's 3V3 runs on F.Cu x 34.975 to a via between R76 and C74, through R76.1 and one In2 via (33.1,
42.65). The (42, 59.5) support's M-5 disk (4.452 mm) keeps parts off the space east of C92, so TP90 / R103 moved to
F.Cu. camera_bypass (check_r9): C100 at U12.3 on the same side (direct), C93 at U12.7 by one via. No camera net is a
critical class; K-copper: no via ring on a paste aperture (C94 / R76 / C60 drove the via spots).

### D-S7-14. status: the buzzer to the south-centre, the VLOGIC divider at its sense exit, LEDs re-placed

**Decision.** Parts (r9_place.tsv): LS120 (29.0, 25.5) with Q123 (29.6, 25.0, 180), R162 (26.1, 26.15), R163 (26.6,
24.3, 90), D123 (29.8, 27.25) under it on the bottom; R32 / R33 (6.9, 41.15 / 43.1, 180), LED1 (6.05, 45.1), LED2 (6.85,
47.0); R160 (27.0, 30.5, 270), R161 (27.43, 33.5, 180), C160 (26.58, 35.6, 180) on the PULLPIN column x 27.0; the
VLOGIC divider R60 (30.4, 46.0, 90), R61 (28.0, 45.98, 270), C60 (29.2, 46.25, 270) beside VLOGIC_SENSE's exit; the
V3V3 divider R62 (15.85, 54.5, 180) / R63 (15.85, 55.38) in R60 / R61's old spots. Step-6 table edit (r9_power.py):
C19 0.25 mm aft (23.35, 39.95) with its GND strap and via on y 40.65, so BUZZ_DRV's interior exit E41.44 passes north
of C19.2. Copper (module docstring). 11 nets and VLOGIC's open pad, 129.8 mm, 5 signal vias, 0 critical layer changes,
worst ratio 1.494 (V3V3_SENSE); budget 140 / 5 / 0 / 1.50; board 50 signal vias (S4 <= 70; the stretch row <= 55 met).

**Basis.** imu_baro's I2C crosses the buzzer's west footprint (D-S7-10), so LS120.2 had no reach; the south-centre spot
is the free F.Cu area between the radio lanes and RADIO_DIO1 (4.5 mm from U31's keep-out). Inference, not measured:
the MLT-5020 is a magnetic transducer driven at 4 kHz on the pad, not during flight, and its square-wave drive and
field near the radio module are not analysed. U1.7 / 8 / 17 are sealed north of the forward face (servo fan on F.Cu,
the pocket's B.Cu) and leave inward through the exits between U3's pads (E41.44, E43.97, E46.4). VLOGIC_SENSE's
divider at its exit keeps the sense lane short (route_check detour: a divider at VLOGIC's end measured 1.72 x MST)
and puts C60 at the ADC end; VLOGIC comes down F.Cu x 30.4 from the hold-up via (no new via but the one into R60.1:
extra_vias keeps VLOGIC at 3), 2.1 mm from ARM1_SENSE_MCU (r9_pyro_check: no HIGH net within 1.5 mm of an MCU-side
sense lane). V3V3_SENSE's only way into the pocket is round the servo pull-downs; with the divider in R60 / R61's old
spots its ratio is 1.494 (1.52 in the far spots), so the budget's ratio is 1.50. BUZZ_OUT has one via between Q123.3,
D123.2 and LS120.2 (detour within MST + 2 mm). PULLPIN_EXT keeps 1.05 mm from TP70 (test-pad rule). The driver's GND
strap runs on y 23.9, leaving B.Cu below y ~23.5 free (D-S7-15).

### D-S7-15. What the three families leave for power_ctl

**Decision.** Recorded corridors (no copper): BAT_FAULT_N / LOGIC_SOURCE_ST from vias in the pin-28..31 box (x 26.75,
y 48.9-51) east on B.Cu north of OE's y 48.4 (round or past C90, which power_ctl may re-place) through R89 / R91 and
north on x ~32.85 / 33.35 (OE's via (33.9, 53.4) 0.2 mm; the hole (30.8, 59) needs x >= 32.75), east at y ~61.5-62
south of C98 to U11's east side. USB_LIMITED remains the open problem D-S6-10 named: from U10 / C86 / TP82 it can take
B.Cu y ~23.15 east under the buzzer driver (clear below y 23.5) but then meets walls on both layers: B.Cu PULLPIN_EXT
(y 27-29.1, x 27-39), the camera eFuse's CAM_INPUT_LIMITED (y 35.65) and U7 / U8; F.Cu RADIO_NRST's diagonal and x 33.65,
RADIO_DIO1, RAW_PROTECTED x 42.15 and J9. Candidates for power_ctl: an F.Cu hop over PULLPIN_EXT in the triangle east of
RADIO_DIO1 (x 33.4-37, y 24-30), with TP70 / PULLPIN_EXT's east end re-placed to clear the test-pad rule, then a B.Cu
lane west of U7 or an In2 USB_LIMITED finger (a step-6 region change, an owner decision if it touches the 3V3 plane).

**Basis.** D-S6-10 left USB_LIMITED's corridor to be planned with the step-7 families. The usb_swd / camera / status
copper keeps the band y < 23.5 (B.Cu) and the north corridor x 32.6-33.6 (B.Cu, y 48.5-64) free; it could not also keep a
continuous single-layer USB_LIMITED path, because the pull-pin wire (U1 to J123), the camera eFuse block and the radio
lanes cut the board between U10 and U11 on both layers.

### D-S7-16. power_ctl: USB_LIMITED through U1's interior, the status lanes up one corridor, the U9 / U11 pins

**Decision.** `m3_design/r9_route_power_ctl.py` draws USB_LIMITED, LOGIC_SOURCE_ST, BAT_FAULT_N, BAT_ENABLE and
BAT_ILIM, the pull-ups' 3V3 vias and the GND straps of U9.8 and U11.3 / 4 / 6 (routes in the module docstring):
- USB_LIMITED (0.3 mm, two vias): B.Cu from U10.6 through C86.1 and TP82 under U1's aft row, F.Cu through U1's interior
  (a NE diagonal between NRST's and QSPI_IO3's, north on x 23.1 between the interior vias, out at the NE corner between
  U1.25 and U1.26), B.Cu from a via in the pin-28..31 box along the box's exit band, up the corridor x 32.3-33.9 and
  through the slot between C92 and the RAW_ACT pour into C98.1, R87.1 and U11.7 (IN2) from the south.
- LOGIC_SOURCE_ST and BAT_FAULT_N leave U1.29 / U1.28 by two box vias (crossing there on F.Cu, so that LOGIC_SOURCE_ST is
  the middle lane), run beside USB_LIMITED along the band (R91 above its lane, R89 below its own) and up the corridor,
  then round the (42, 59.5) support's north-west: LOGIC_SOURCE_ST into U11.9 and east to TP87, BAT_FAULT_N up the east
  edge (x 45.25) with a T to TP85 and round U9's OVLO divider into U9.4.
- BAT_ENABLE: R165.2 by one via to F.Cu, north between J1.4 and J1.3 and along the forward edge north of the BAT_IN
  pour through TP84, past the (42, 98) support into C87.1, a T to a via inside BAT_FAULT_N's loop; B.Cu round R83 to
  U9.1 and R81.1.
- BAT_ILIM: U9.9 into R84.1, east of R84 below the RAW_PROTECTED column's via, to TP89.
Placement (r9_place.tsv, each row cites this decision): C86, TP82, R85, R90 (usb_swd's R90 / R85 rows and copper follow),
R89, R91, C90 (to free bottom space over the In2 3V3 plane at (3.5, 26.0)), C81, R84, TP84, and the east test-pad
column's slots reassigned: TP87 at 67.8 (its via south of the pad, from U11.9), TP83 (VLOGIC) at 78.2, TP85 at 80.8,
TP89 at 83.4 (each via west of its pad, in the RAW_PROTECTED pour's 1 mm margin); slot 86.0 is empty. Step-6 table edits
(r9_power.py): C97 0.7 mm east (C97.1 straight under U11's IN1 via, C97.2's strap re-angled), R92.2 on its own GND via
(42.4, 84.725) instead of the strap to C9.2, TP83's VLOGIC tap moved with TP83 (the column x 44.6 continued north from
C7.1's corner to a via west of TP83; the via (44.6, 66.2) and the column aft of y 70.6 removed), and the RAW_ACT B.Cu pour's
south step at x 32.2-34.85 raised from y 61.1 to 61.45. usb_swd (r9_route_usb_swd.py): R85.1 on U10.5's line (USB_ILIM
straight) and R90 0.3 mm west with its 3V3 via. Figures (gate at its stage): 5 nets, 174.9 mm of signal copper,
7 signal vias, 0 critical layer changes, worst ratio 1.363 (BAT_FAULT_N); USB_LIMITED 51.9 mm, 2 vias, ratio 1.13;
budget 175 / 7 / 0 / 1.40; board 57 signal vias.

**Basis.** D-S6-10 / D-S7-15 left USB_LIMITED without a corridor. Measured on the status board (scratch A* aid
`s7e/solo3.py`, the gate's DRC and route_check r9):
- the only all-B.Cu route is the board's perimeter (B.Cu y 23.3 under the buzzer driver, up the east edge): 89-96 mm
  against an octilinear MST of 51.5 mm, over route_check's detour limit (1.6 x) on a power net, so no B.Cu route
  exists; any middle route meets U1's east-face fan on both layers (CAM_FAULT_N / RADIO_NRST / TX on F.Cu, RX / OE /
  VLOGIC_SENSE / PULLPIN / BUZZ_DRV on B.Cu), which only U1's own interior bypasses: F.Cu inside the pad ring is open
  on x 23.1 between the interior vias, and the NE corner gap between U1.25 and U1.26 leads into the pin-28..31 box. With
  a 50-mm via cost the aid's best route was that one (48.8 mm, two vias); it is the drawn route.
- USB_LIMITED: dc_solve U10.6 -> U11.7 at 0.45 A (the TPS2553 limit set by R85, R8 D42), 0.05 mm grid: 82.9 mOhm,
  37.3 mV drop, 0.45 A per via (<= 1 A, R8 D12), neck rise 0.4 C (`step7_evidence/dc_usb_limited.txt`). 0.3 mm instead
  of R8's 0.4: the corridor holds three lanes (0.3 + 0.2 + 0.2 at 0.15 mm, 1.48 mm wide beside OE's via).
- Three lanes must pass the corridor's top between C92.2 and the RAW_ACT pour (0.93 mm; 1.0 mm needed). C92 cannot move
  south (U13's courtyard) and the slot is the corridor's only exit east, so the pour's step (a dead corner of the
  spine's south end, no current path: the spine runs north-south from x 28.6) moves 0.35 mm north. The step-6 gate
  (DC, regions, template) passes at its stage with it.
- U1.28 is north of U1.29 but BAT_FAULT_N must be the outer (south) lane: LOGIC_SOURCE_ST turns north into U11.9 west of
  where BAT_FAULT_N turns north at the east edge, so the two vias are set so that the lanes cross once, on F.Cu in the box.
- Only one B.Cu lane passes the VLOGIC column (x 44.6) on the east edge, so the pad reached from U11 (TP87) takes the
  column's south slot (via south of the pad), VLOGIC's TP83 moves to a slot north of the column, and BAT_FAULT_N's TP85
  sits south of BAT_ILIM's TP89 so that the two lanes reach their vias without crossing.
- U9's pins: FLT (U9.4) is reachable only from the north between R82's pads (the BAT_IN pour bounds the west, x 39.6 is
  0.3 mm from its outline); BAT_OVLO's R82 -> R83 link closes the R82 / R83 gap, so EN (U9.1) is fed from the east on
  y 92.0 from a via east of R83, inside BAT_FAULT_N's loop; ILIM leaves U9.9 straight down beside U9.8's GND via
  (x 40.6 / 40.1 / DVDT 39.6, 0.15 mm each); C81 sits on U9.7's line (0.1 mm west, as far as Q122's courtyard allows)
  and 0.6 mm lower, R84 0.2 mm west and 0.75 mm lower so that BAT_ILIM passes below the RAW_PROTECTED column's via
  (42.3, 88.0);
  R92.2's strap crossed BAT_ILIM's way to TP89.
- U11.6 sits between USB_OVLO and USB_LIMITED with C97.2 above it on F.Cu and VLOGIC's F.Cu lane west: its GND via
  fits south of the pin only with C97 0.7 mm east (also straightening C97.1's feed).
- BAT_ENABLE: the BAT_IN pours (F.Cu x 26.3-33.4 to y 99.2, B.Cu to y 100.9) wall J1 off from U9, so the lane crosses
  on F.Cu north of them; TP84 on that lane (its column slot cost a 6.7 mm descent past R81 / R92: 56.4 mm, ratio 1.57,
  against 51.9 mm, ratio 1.28 now). C87 keeps its spot: >= 5 mm from the east edge (T-1's capacitor margin) and
  >= 5.008 mm from the (42, 98) support (M-5).
- The pull-ups R89 / R91 hang off their lanes in the band (R89 below BAT_FAULT_N, R91 above LOGIC_SOURCE_ST) with their
  3V3 vias clear of the ARM1_SENSE F.Cu lane (x 28.53); their 3V3 pads stay >= 1.0 mm from the RAW_ACT_SENSE pads
  (P-5). C90 (the camera UART sheet's 3V3 100 nF) had its R8 spot in the band; it moves to free bottom space over the
  same plane.
- Mounting holes are Edge.Cuts, so copper keeps the 0.5 mm edge clearance from them (the corridor's lanes at x >= 33.07
  past the (30.8, 59) hole, BAT_ENABLE's diagonal 2.26 mm from (42, 98)).
- route_check: the lanes' corners are 90 degrees or chamfers that break no staircase (an A,B,A,B run with two segments
  under 1 mm failed until BAT_FAULT_N's slot and east-edge corners became square); BAT_FAULT_N's F.Cu stub to its box
  via offsets 0.4 mm on a 0.57 mm run (a 0.35 mm offset was a tiny jog). INFO only: the T to TP85 is a U-turn (the via
  must sit west of the pad: TP83 / TP89 are 1.1 mm away), extra bends at the corridor jogs, the two USB_LIMITED vias'
  power_via_no_gnd (step 8's stitching).
None of power_ctl's nets is a critical class but USB_LIMITED (power), so no GND partner vias. X2 / P-3 / P-7 / D19 and
the step-5 pyro functions hold (gate).

### D-S7-17. links: the U9 / U11 divider and timing pins on their parts' lines

**Decision.** `m3_design/r9_route_links.py` draws BAT_OVLO (U9.2 -> R82.2 -> R83.1), BAT_DVDT (U9.7 -> C81.1),
LOGIC_ILIM (U11.10 -> R86.1), LOGIC_SS (U11.11 -> C85.1, one 45-degree run) and USB_OVLO (U11.5 -> R87.2 -> R88.1),
each one B.Cu link with no via, copper <= 1.3 x its octilinear pad-to-pad distance (asserted while drawing; a seeded
detour fails, `test_r9_route.LinksStage`). R86 to y 66.25 (on U11.10's line) and C85 to y 67.725 (the 45-degree run
clear of U11.12's pad and R86.1, the courtyards 0.025 mm apart). Figures: 5 nets, 10.9 mm, 0 vias, ratio 1.0.

**Basis.** r9_plan section 4 step 7 ("then a constrained short-link stage") and r9_route.py's links contract; R8 D59's
drawn-polyline form. The links are the nets left after power_ctl; U9's corner pins are two rectangles (an L) and each
link ends on the centre of one of them.

### D-S7-18. The step-7 gate

**Decision.** Step 7 is done when, in one `r9_build.sh` run, every family's gate passes at its own stage (rf_if ...
links, `r9_route_check.py FAMILY`) and the steps 2-6 gates still pass; the links gate is then the whole-board gate
(every family done): DRC with parity showing only step 8's silkscreen classes and the pending GND vias' via_dangling,
every net complete but GND (its pads and pending vias wait for step 8's pours), route_check r9 with the empty
allowlist failing only on those vias and their straps, board signal vias <= 70, P-7 / D19 / D18 / D85 / D20, the step-5
pyro functions and check_actuators; check_r9 in full (fit, plate model, seeded rule-H suite) passes but K-legends (step
8's silkscreen); two replays give byte-identical files. Result: board `8504c2c6…`, 57 board signal vias (S4 done row
<= 70 met; the stretch row <= 55 missed by 2), every family within its budget, 167 tests OK.

**Basis.** r9_plan section 4 step 7's verify list (per-family budgets, empty allowlist, P-7, D19) and the brief's full
gate; a family gate takes every family before it as done (D-S7-01), so the last family's gate covers the board.

### D-S7-19. Done rows after step 7

**S4 (signal vias) = 57**: owner decision 4's done row (<= 70) is met, the stretch row (<= 55) is not. The vias by
family: rf_if 0, qspi_hse 6, pyro 1, servo 4, imu_baro 10, usb_swd 8, camera 7, status 5, power_ctl 7, links 0, steps
4-6's 9. power_ctl's seven are each forced: two box vias (U1.28 / U1.29 are boxed on F.Cu by ARM1_SENSE_MCU, R170 and
the ARM1_SENSE lane, D-S7-13), three test-pad vias (the east column's pads are on F.Cu and no F.Cu lane reaches them past
the RAW_PROTECTED pour, D-S7-16), BAT_ENABLE's two (R165 sits on B.Cu under J1.4 and the BAT_IN pours wall it from U9 on
B.Cu). For the owner's deviation list with D-S6-13's rows.

## Step 8: ground

### D-S8-01. The strip's GND pours become the board's

**Decision.** `m3_design/r9_ground.py` grows step 4's R9_GND_F_strip / _B_strip / _In1_strip (D-S4-07) in place to
x 0.3-45.7, y 0.3-101.7 (the In2 GND pours' extent) and renames them R9_GND_F / _B / _In1; settings, priorities and
UUIDs stay (F / B: priority 0, 0.15 mm clearance and minimum width, THT thermal 0.5 / 0.5; In1: priority 1, 0.25 / 0.2,
thermal 0.25 / 0.4). It asserts each strip pour's step-4 settings and outline first. In2 stays step 6's (strip pour +
R9_GND_In2 and the three power regions).

**Basis.** D-S4-07 ("step 8 extends F.Cu, B.Cu and In1 over the board ... with the same settings"). One pour per layer
is the simplest copper; a second, abutting forward pour with the same net and priority is a DRC zones_intersect (seen
in a trial with a 0.25 mm minimum width forward pour, which also gave 10 starved thermals and 6 more islands). The
strip's fill is unchanged (R-4 / R-5 / R-7 re-measured by check_r9 in the step gate).

### D-S8-02. The stitching table and its design aid

**Decision.** The GND vias and straps are rows of `m3_design/r9_ground.tsv` (186 rows: 182 vias of 0.5 / 0.3 mm, 4 strap
tracks of 0.3 mm), drawn by r9_ground.py and generated by the design aid `m3_design/r9_ground_aid.py` from the step-7
board (deterministic: two runs give the same table; `--check` compares with the frozen table). Stages: return (a GND
via within 1.5 mm of power layer changes: 11), pad (IC GND pads beyond 4 mm of copper, R8 D102: 3), grid (4 mm, plan_spine
section 9: 89), cover (3.4 mm: 37), island (two vias per outer GND island where a spot exists: 14), patch (P9 radius
3.45 mm: 25), finger (none needed now), strap (C17.2, C24.2: 4 tracks and 1 via), reach (2, D-S8-16). R8's make_ground.py
legality, with these R9 changes: every via >= 0.2 mm from foreign copper (MARGIN 0.05: no new Y1 / Y1b close pair);
0.75 mm from bus / igniter / drain copper (rule D plus its fill margin, so Z1d keeps >= 0.2) and 0.5 mm from the other
pyro / arming nets; 0.8 mm from the outline (the DRU's 0.5 mm copper-edge clearance + the ring + MARGIN); outer power
pours and the 7.7 A In2 corridors (tools/run_dc.sh terminals + 2 mm) uncut, the corridor margin 0.3 mm + ring + MARGIN
(the In2 zones' own clearance: no notch); no antipad in an In2 power region's narrow outline (< 2.5 mm: the 3V3 finger up
the spine, which a first trial split, DRC unconnected 3V3); no In2 antipad under a critical / reference B.Cu track (R8
guarded every B.Cu track; the slow control lanes need no reference); off 2-4-pad part bodies; spacing 1.0 mm in the first
four stages, 0.6 mm in the later ones (holes 0.3 mm apart >= the project's 0.25 mm min_hole_to_hole); the island stage
also stitches the RF strip's pockets, 1.0 mm from RF copper and outside the launch windows. Session 2: no antipad
may reach into a 7.7 A corridor from just outside it either (the stitch gate tests the via's circle against the region's
fill inside the corridor; with the vias' unconnected pads removed, D-S8-19, a via's antipad no longer hides that fill from
the test): the cover via (25.65, 59.95), inside the In2 RAW_ACT region 0.05 mm south of its corridor box, went, and the
regenerated table has 187 rows (183 vias: cover 36, patch 27; (20.45, 59.35), (16.75, 57.85) and (25.55, 59.15) in, (17.15,
58.05) out).

**Basis.** r9_plan section 4 step 8 and the brief (GND vias at critical layer changes, stitching, fence, pour hygiene,
no trims if avoidable); R8 D62-D67 and make_ground.py; AGENTS 3. The fence and the strip's 2.5 mm stitching (R-7) are
step 4's and still pass (check_r9 R-7). Critical layer changes: route_check finds none without a GND via within 1.5 mm
(S13 = 0). Power layer changes without one (route_check information, AGENTS 3 asks it of critical signals only): 7, each
with no legal spot within 1.5 mm (3V3 (24.25, 38.5), (24.2, 50.0), (15.2, 53.6); 3V3A (22.0, 50.75); CAM_5V
(40.75, 45.4); CAM_IO_3V3 (35.45, 51.95), (34.6, 57.4)).

### D-S8-03. No pour trims; fingers and slivers removed at their cause

**Decision.** The table holds vias and tracks only (r9_ground.py rejects any other item); X8c = 0. The board-wide
pours first gave one GND sliver and seven fingers (route_check r9). Two were served by stitching; the others came from
two copper features 0.45-0.8 mm apart (a GND fill under 0.5 mm wide that no via fits) and were removed by moving the
copper that formed them, in the owning step's table (D-S8-04 ... D-S8-10), each re-gated by its step's gate in the
build.

**Basis.** The brief ("no pour trims if avoidable"); r9_scorecard X8c = 0 (done); flowline's graft ("no pour trims").
A strip 0.5-0.6 mm wide would pass route_check's 0.5 mm finger test yet be the same unstitched copper, so each fix either
closes the gap below the fill's minimum (no copper) or opens it to a real pour.

### D-S8-04. usb_swd: NRST's diagonal 0.04 mm east

**Decision.** NRST's via under U3 (17.5, 40.0) -> (17.54, 40.0) and its F.Cu corner (20.3, 42.8) -> (20.3, 42.76); the
B.Cu run starts with (16.1, 41.44). NRST's diagonal is now 0.68 mm (centre lines) from USB_LIMITED's parallel F.Cu run:
0.43 mm between edges, so the GND fill (0.15 mm off each) is 0.13 mm < its 0.15 mm minimum and does not form. The via
keeps 0.20 mm from USB_LIMITED's via.

**Basis.** route_check r9 pour_sliver / pour_finger at (19.45, 41.48): a 0.157 mm GND sliver 3.6 mm long between the two
diagonals. usb_swd's gate passes (length +0.0 mm).

### D-S8-05. RAW_ACT F.Cu pour: west edge 29.75 beside the ARM lane

**Decision.** r9_power.RAW_ACT_F's west edge 29.4 -> 29.75 for y 65.4-75.6 (where ARM1_SENSE runs straight at x 28.53).
The GND between the lane and the pour is 0.69 mm wide (0.30 before) and joined at both ends: a guard, not a finger. The
spine's x 29.9 vias now straddle the edge (fill joins them).

**Basis.** route_check pour_finger (28.95, 70.56): 0.30 mm x 10.9 mm. The RAW_ACT fill cannot close the gap from the other
side (fill margin A keeps it 0.75 mm off the sense lane, D-S5-12). DC (step-6 gate, 0.1 mm): RAW_ACT 0.79 mOhm, neck rise
12.8 C (12.7 before; D12 20, R8 17.6).

### D-S8-06. RAW_ACT F.Cu pour over the RAW bar's east end

**Decision.** RAW_ACT_F gains x 26.9-31.15, y 85.5-87.0 (to 0.3 mm off the ACT_GATE hop at y 87.4) and J124.2's 1.0 mm
RAW bar ends at x 27.6, 0.7 mm inside the pour (a longer run inside the fill is a route_check pour_stub).

**Basis.** route_check pour_finger (28.57, 86.91): 0.45 mm GND between the bar and the hop, 4.8 mm long, its only
access at the west (no via fits; B.Cu under it is the ACT_FET_S pour). Moving the hop north would leave a 0.26 mm sliver
over the ACT_FET_S F.Cu plate. The pyro fill margins apply to the new RAW_ACT fill (A, E); RAW_ACT is allowed in the
block (P-3). The bar's resistance only falls (F7 records, step 10).

### D-S8-07. camera: CAM_FAULT_N bends beside CAM_PWR_EN

**Decision.** CAM_FAULT_N's F.Cu run: U1.41 east to x 28.669, 45 degrees to y 41.6 (0.20 mm beside CAM_PWR_EN's diagonal
and 0.20 mm off D122's 3V3 via (30.0, 42.45)), east to its via (32.775, 41.6). Same length, one more bend (S10b).

**Basis.** route_check pour_finger (28.92, 43.5): 0.50 mm GND between CAM_FAULT_N (y 43.0) and RADIO_NRST (y 44.0) for
4.9 mm, dead-ended at U1.40 (no net); it is now 2.4 mm long (route_check's finger needs > 3 mm). Three 0.2 mm lanes from
U1.39 / 41 / 42 at 0.5 mm pitch cannot close both gaps; a via in it would sit at the DRC minimum (Y1b).

### D-S8-08. power_ctl: BAT_FAULT_N's east-edge lane at x 45.15

**Decision.** r9_route_power_ctl.X_E 45.25 -> 45.15: BAT_FAULT_N runs 0.35 mm (edges) beside BAT_ENABLE's x 44.6 column
at U9, so no GND forms between them (0.05 mm < 0.15). Length -0.3 mm (power_ctl 174.6 mm of its 175 budget).

**Basis.** route_check pour_finger (44.85, 91.2) on B.Cu: 0.30 mm x 3.0 mm between the two lanes. The first fix (BAT_ENABLE
east by 0.1 mm) took power_ctl to 175.2 mm, over its budget; the budget is kept.

### D-S8-09. RAW_PROTECTED F.Cu pour narrowed to x 41.3 (y 72.0-84.2)

**Decision.** r9_power.RP_F's east edge 42.85 -> 41.3 for y 72.0-84.2 (kept at 42.85 north of y 84.2 for U9's vias and
D9.1). The camera branch leaves C82.1 east at y 72.4 (it started inside the old pour). The C6 / C7 / C8 GND vias
(41.9, 73.75), (42.2, 76.8), (42.0, 81.26) now sit in the F.Cu GND east of the pour, which joins the test-pad column's GND.

**Basis.** Each of those vias was a via-only GND island inside the pour (P7, 0.27-0.39 mm2), and TP74 / TP88 sat in an F.Cu
GND island with no via. RAW_PROTECTED is 1.45 mm wide there; supply solves (step-6 gate): U9.6 -> U7 77.1 mOhm (75.0;
R8 D49 76.3; 77 mV at 1 A), U9.6 -> U11 16.2 mOhm (15.0; R8 47.3).

### D-S8-10. VLOGIC's hold-up via at x 38.5

**Decision.** r9_power.V_HOLDUP (38.2, 69.6) -> (38.5, 69.6), its F.Cu run to C84.1 x 38.5 then 45 degrees; status's VLOGIC
tap leaves the via 45 degrees to (37.6, 68.7). VLOGIC and U11's IN1 branch (x 39.3) are 0.40 mm apart (edges): no GND
between them.

**Basis.** route_check pour_finger (38.77, 70.92): 0.40 mm x 3.6 mm between the two 0.4 mm rails; its far end was 4.2 mm of
copper from U11's GND via, and U2 / L1 / BST leave no via spot at its north end.

### D-S8-11. The east test-pad column reordered

**Decision.** TP81 (RAW_PROTECTED) 75.6 -> 70.4, TP74 (GND) 70.4 -> 73.0, TP88 (GND) 73.0 -> 75.6; TP81 is fed by a T off
the camera branch at y 70.4. The column reads, aft to forward: TP87 LOGIC_SOURCE_ST 67.8, TP81 70.4, TP74 GND 73.0,
TP88 GND 75.6, TP83 VLOGIC 78.2, TP85 80.8, TP89 83.4.

**Basis.** With TP81's branch at y 75.6 the F.Cu GND round TP74 / TP88 was an island holding one via (the C6 GND via),
B.Cu under it is full (C6, C7, L1, the VLOGIC column). The GND pads now share one island with the C6 / C7 / C8 GND vias
(three vias). ORDERING / bench text naming these test pads must use the new spots (step 10).

### D-S8-12. TP90 at (33.85, 58.65)

**Decision.** TP90 (CAM_IO_3V3) moves (+0.2, +0.3) mm; its F.Cu feed: the via (34.6, 57.4) down 0.5 mm and 45 degrees into
the pad, the pad to R103.1 down x 33.85 and 45 degrees.

**Basis.** The RAW_ACT_SENSE divider's GND pads (R125.2, R182.2, C122.2) sat in a B.Cu island no via could reach (DRC
unconnected): the divider column, USB_LIMITED and the J122 tie hole wall it, and TP90 / TP91's 1.0 mm test-pad
keep-outs covered its last via spot. TP90's courtyard keeps 0.03 mm from R103's; its pad 1.1 mm from R103.2.

### D-S8-13. R105 turned

**Decision.** R105 (31.94, 47.55, 180): R105.1 stays on the sense node (32.37, 47.55), the GND pad R105.2 now faces west
into open GND.

**Basis.** At (33.23, 47.55) R105.2 was boxed by R104.1, R105.1 and the CAM_UART_OE lane: one thermal spoke of the
rule's two (DRC starved_thermal), and no strap could reach a via (U12's pads and CAM_MCU_RX above it on F.Cu).

### D-S8-14. R182 0.2 mm forward

**Decision.** R182 (30.5, 54.4) -> (30.5, 54.6); the divider column's node moves with R182.1.

**Basis.** C122.2 got one thermal spoke (DRC starved_thermal): the fill between it and R182.2 was narrower than the
pour's minimum. With 0.68 mm between the pads the fill forms; C122.2 gets its second spoke and the C122 / R182 islands
merge. A strap from C122.2 to R182.2 left it at one spoke (measured), unlike C17.2's / C24.2's straps (D-S8-02).

### D-S8-15. P7: nine recorded pockets

**Decision.** `r9_ground_check.WEAK_EXCEPT` records the nine outer GND islands with one GND via (area, via, reason); a
pocket that grows or loses its via, or an entry that matches nothing, fails the gate. The pockets: the F.Cu ring of C150
/ C151's GND via in the RAW_ACT spine pour (0.27 mm2) and their B.Cu pocket (0.88); U1's interior west over U4 (6.03,
IMU_body_B bars a via, M-7); D4.2's pocket (2.82, R8 D63's exception); the radio MOSI / NSS pocket at U31 (0.71, R8 trim
G5); U4's 3V3A loop (0.78, R8 G3); the camera buck's pocket between the CAM_INPUT_LIMITED bar and U8 (3.51, R8 G6); the
divider's GND island (7.71, TP90 / TP91 / the VLOGIC tap leave one spot); the LOGIC_SOURCE_ST / USB_LIMITED pocket (1.77,
the reach via, D-S8-16).

**Basis.** No legal spot for a second via in any of them (measured by the aid's island stage and r9_ground_check); the
alternatives are pour trims (X8c, D-S8-03) or re-routing steps 4-7's copper round each pocket. P7's done row (= 0) is
missed: 9 (R8 1, with 8 trims). For the owner's deviation list.

### D-S8-16. P9 and P10

**Decision.** The reach stage adds GND vias while P9 > 3.45 mm, at the spot that brings most points beyond 3.5 mm within
reach, even where that revives a removed GND island held by the one via: (31.05, 51.25) (26 points; the D-S8-15 pocket)
and (38.75, 79.55) (6 points). P9 = 3.45 mm (done <= 3.5 met). P10 = 7.32 mm at (31.25, 91.25), the centre of the battery
entry's BAT_IN pours (F.Cu, B.Cu and In2 between J1.1 and Q120), where a GND via would cut the 7.7 A path. With every
legal spot of the step-7 board used at once (no spacing between them) the maximum is still 7.28 mm there
(`step8_evidence/reach_floor.py`, `reach_floor.txt`): P10 <= 7.0 is out of reach without a GND via in the battery entry.
r9_ground_check holds P10 <= 7.35 with this recorded cause.

**Basis.** The brief ("P10 <= 7 (or a measured, recorded cause)"). Without the reach vias P9 is 3.51 (931 points beyond
3.5 mm, 927 allowed): the remaining points lie round the U1-east / divider lanes, reachable only through removed pockets.
(reach_floor's P9 figure is not a bound: later stages' vias change the fills, and with them the legal spots.)

### D-S8-17. R6b: 0.1022, better than R8's 0.1107; 0.08 out of reach by the board rules

**Decision (session 2, replacing session 1's "not reachable by step 8", which recorded 0.1732 and was not accepted:
worse than R8).** R6b = **0.1022** (3,206 of 31,359 critical samples), from two step-8 changes: every via's unconnected
inner pads removed (D-S8-19: own antipads r 0.50 -> 0.40 mm) and the crystal's In2 void made its local GND plane
(D-S8-20: the keep-out class gone). r9_ground_check's reference gate holds the count <= 3,206 and fails any unreferenced
sample outside its own net's via antipad (0.45 mm of a same-net via) but the one recorded in REF_STRAY. Every remaining
sample, by class (measured, `step8_evidence/reference_causes.txt`):
- **one-branch own antipads, 21 via sides, 2,550 samples**: the In1 / In2 hole round each of the 12 critical
  layer-change vias (QSPI x6, HSE x2, SPI1 x3, IMU_CS) under the 0.2 mm track's centre line and both edges, r 0.40 mm =
  hole r 0.15 + the board's 0.25 mm hole clearance: 119-122 samples a side, SPI1's sides beside the neighbouring SPI1
  vias a little more (SCK B.Cu 129, MISO 125 / 124, MOSI F.Cu 133: +35 in all). 12 is the minimum: U3, Y1 and U4 sit on
  the bottom under U1 (D-S3-05, D-S7-06), so each of the 12 nets needs one via, and step 7 has exactly one per net;
- **two-branch own antipads, 3 via sides, 655 samples** (+298 over one branch each): HSE_OUT B.Cu 241 (the in-line via
  between Y1.3 and C26.1, R8 D86, the simplest crystal topology), QSPI_NCS B.Cu 242 (R10.1's pull-up branch leaves the
  via opposite U3.1; a via beyond R10.1 is barred by QSPI_IO2's diagonal), IMU_CS B.Cu 172 (the T to R11 0.28 mm off the
  via; a via further off is barred by BOOT0's via 0.5 mm away);
- **one edge sample at another net's antipad**: USB_DM's copper edge 0.401 mm from CC1's via (7.85, 32.75) (REF_STRAY).
The floor with 12 vias is 24 sides x ~119 = 2,856 samples = **0.091 > 0.08**: R6b <= 0.08 needs fewer than 12 critical
vias (parts off the bottom, under U1) or a smaller antipad (a via hole < 0.3 mm, the board minimum, or a hole clearance
< 0.25 mm, the DRU's general rule: both weaker than R8's rules; with 0.45 / 0.2 critical vias the board measured 0.0888,
not adopted). The 0.08 done row stays missed with these causes for the owner's deviation list.

**Basis.** The coordinator's direction (R6b worse than R8 not accepted: fewer critical layer changes, HSE off the keep-out,
smaller antipads within JLC's capability and the DRC; target 0.08, floor better than R8). Measured what-ifs on the built
board (`<scratch>/s8b/exp2.py`; session-2 log): pads removed 0.1396; plus the crystal plane 0.1022; rule-preserving
routing changes without the crystal plane reach about 0.12 at best (the Y1-to-load-cap B.Cu runs lie inside the
keep-out by definition: 2 x 1.63 mm x 3 sample lines), so the crystal plane is the one lever past R8. JLC
(https://jlcpcb.com/capabilities/pcb-capabilities, 2026-10-23): inner-layer via hole to copper 0.2 mm (the board keeps
0.25). critical_reference.py's R6 method (centre and both edges every 0.01 mm; F.Cu against In1 GND, B.Cu against In2
GND / 3V3 / 3V3A) is unchanged.

### D-S8-18. Silkscreen and the step gate

**Decision.** K-legends and DRC's silk classes are step 9's (r9_post.py: r9_plan section 4 step 9, plan_spine section 9);
the earlier handoffs' "step 8's silkscreen" referred to the plan's former numbering. `m3_design/r9_ground_check.py` gates
step 8 (r9_build.sh stage after r9_ground.py): the pours and table (with the crystal plane and every via's pad mode,
D-S8-19 / 20), DRC + parity (no violation but silk, no unconnected item), route_check r9 (0 failing), the stitching
keep-outs (power pours, 7.7 A In2 corridors, pyro copper, 0.6 mm spacing), In2's regions whole (step 6's gate), the
crystal plane (xtal), P7 (D-S8-15), P9 <= 3.5 / P10 <= 7.35, R6b's count and its classes (D-S8-17), the step-5 pyro
functions, check_r9 (all but M-2 and K-legends) and check_actuators.

**Basis.** r9_plan section 4 (step 9: post and fab, silkscreen); the brief's verify list.

### D-S8-19. Every via keeps pads only on the layers it connects

**Decision.** r9_ground.py sets every via on the board (steps 4-8, 0.5 / 0.3 and 0.6 / 0.3 mm) to KiCad's "remove
unconnected layers, keep start and end layers" (r9_ground.VIA_MODE) before the fill: a via keeps its F.Cu / B.Cu pads and
its pads on the inner layers whose same-net fill it joins (a GND via on In1 GND, a 3V3 via in the In2 3V3 region), and
loses the unconnected inner rings. The In1 / In2 planes then clear the hole by the board's 0.25 mm hole clearance (hole
r 0.15 + 0.25 = 0.40 mm) instead of the 0.25 mm ring plus the 0.25 / 0.3 mm zone clearance (0.50 / 0.55 mm). The table
gate fails any via left with pads on every layer; unground.py restores them.

**Basis.** R6b (D-S8-17): own antipads r 0.50 -> 0.40 (4,145 -> 3,386 samples), other nets' antipads 293 -> 1. JLC's
capability (inner-layer via hole to copper >= 0.2 mm, via hole to track 0.2 mm) is met with margin by the DRU's 0.25 mm
hole clearance, which stays; no board rule changes, no pyro or RF rule is touched (the planes only gain copper round
foreign holes, so every clearance grows or holds; the RF strip's GND vias join every GND layer and keep their pads, R-4
and R-7 re-measured by check_r9 in the gate). Precedent: R4 pass 1 (E4-F1, r4_pcb.py) removed the In1 rings of the
RAW_ACT stitching vias for the same reason. An unconnected inner ring carries no current, so the DC paths are unchanged
(Inference: barrel anchoring by non-functional pads is not needed on a 1.6 mm 4-layer FR4 board; fabricators commonly
remove them). Side effect, found by the gate: the stitch gate now sees a via inside an In2 power region whose antipad
reaches its 7.7 A corridor (before, the antipad's own 0.55 mm radius hid the fill from the 0.55 mm test), hence the aid
change in D-S8-02.

### D-S8-20. The crystal's In2 void becomes its local ground plane

**Decision.** In r9_ground.py the rule area Y1_In2_keepout (R5 V1; In2 under Y1, C25, C26 and the HSE lines, x 13.9-21.8,
y 45.8-50.45, moving with Y1 from step 3) keeps In2 tracks out and no longer bars fills, and a GND zone R9_GND_In2_Y1,
R9_GND_In2's settings, priority 11 (over R9_3V3_In2's 10, under the RAW_ACT / BAT_IN regions' 12), fills it: In2 under the
crystal and its load caps is GND, tied through the six GND vias inside it (C25.2's, the crystal guard, (14.6, 47.4),
(19.875, 49.859), (20.35, 48.75), (20.42, 49.6)) to the board's GND (review pass 1, R9P1-PLANES-04: nine vias bond it to
In1, those six with their centres inside and (16.0, 50.6), (19.69, 45.75) and (21.95, 47.0) overlapping its edge; U1.10's
VSS, the nearest MCU ground, is about 1 mm of F.Cu from (16.0, 50.6), and U4's GND pins 2 / 3 return through (14.6, 47.4).
AN2867's "distinct from the application PCB ground plane" is therefore deliberately not followed: on a 4-layer board with
a solid In1 GND 0.2 mm under the top layer the local plane is bonded at nine points, the usual practice, Inference), and no 3V3 or other net's In2 copper lies there (the
only foreign In2 copper in the area is U1.6's 3V3 via ring (14.5, 50.65), 0.05 mm across the area's forward edge, as
before). The plane's outline is the area less one notch per B.Cu track of critical_reference's R6 / extended nets lying
wholly outside the area within reach of it (r9_ground.xtal_outline: the track's box grown by its half width + 0.3 mm, the
plane's 0.25 mm clearance + 0.05): one notch, x 18.9-20.73, y 50.2-50.45, under NRST's run (19.3, 50.6)-(20.33, 50.6) to
C24.1, 0.05 mm forward of the area, so the 3V3 fill, 0.25 mm off the plane, still covers that run with 0.05 mm to spare,
as it did with the void (a first build without the notch moved the 3V3 edge to y 50.7 and left NRST 0.33 mm over the
gap: one more extended-set split crossing). Elsewhere the 3V3 fill keeps 0.25 mm outside the area, and the two critical
tracks that cross into it (HSE_IN from its via (17.0, 50.6), QSPI_NCS's branch into R10.1) cross that gap inside their own
via antipads. r9_ground_check's xtal gate: no other net's fill in the area beyond its own vias' pads, the plane >= 90 % of
the area in one piece with >= 2 GND vias (measured 0.961, one piece, 6 vias); its table gate requires the outline
xtal_outline computes; its reference gate fails any sample outside its own via antipad in the R6 and the extended sets
(one recorded: USB_DM at CC1's via). r9_power_check.gate_in2 accepts R9_GND_In2_Y1 (IN2_LATER: optional at steps 6-7, GND
only).

**Basis.** ST AN2867 Rev 10 (DocID15287), section 5.1 "PCB design guidelines": "The oscillator PCB should be underlined
with a dedicated underneath ground plane, distinct from the application PCB ground plane. The oscillator ground plane
should be connected to the nearest microcontroller ground", and figure 10 ("local ground plane (other layer)"). R5 V1's
concern (QSPI_IO2 between Y1's pads, the arm-sense and servo lines on In2 under the crystal, from AN2867) is kept: In2
carries no track anywhere (K-inner, gate_in2) and the rule area still bars In2 tracks; only the 3V3 plane's absence
becomes a GND plane. r9_plan / plan_spine section 8 asked to keep the keep-out and route HSE off it to recover R8's
keep-out samples; the crystal-to-load-cap runs (Y1.1-C25.1, Y1.3-C26.1, 1.63 mm each on B.Cu) lie inside it by its
definition, so no routing recovers more than HSE_IN's 1.25 mm approach (and only by re-routing BUZZ_DRV and PULLPIN over
Y1); the plane recovers all of it (992 samples) and the R6b floor beyond R8 (D-S8-17). Cost (Inference, parallel-plate,
fringing ignored, stackup B.Cu-In2 0.203 mm, er 4.4): each HSE node gains about 0.37 pF to GND (Y1's 1.4 x 1.2 mm pad
0.32 pF, the cap pad and run 0.11 pF, less the 0.07 pF it had to In1 1.26 mm away), so CL rises about 0.19 pF over the
NX3225GA's 8 pF with C25 / C26 = 10 pF: a pull of a few ppm and gm_crit about 2-3 % higher ((C0 + CL)^2), inside the margins
and the bench plan of docs/CIRCUIT_REVIEW.md (HSE frequency error by MCO, a cold start, C25 / C26 a bench variable; AN2867's
"high values of stray capacitance ... should be avoided"). The owner may restore the void (one table flag: XTAL_ZONE and
the rule area's flags) at the cost of R6b 0.1396 (worse than R8). Step 10 records the plane and the bench check.

## Step 9: post and fab

### D-S9-01. Footprint silkscreen collisions are the placement's: fixed at the parts, gated at step 3

**Decision.** Three placement-only silkscreen collisions (footprint graphics against footprint graphics or a pad opening,
no text involved) found by DRC once the designators were placed are fixed by moving the parts, and the step-3 gate now
fails any such violation:
- Q31 0.15 mm east (14.53, 10.1) and Q32 0.1 mm west (8.05, 9.9): their body-end outline strokes sat 0.02 / 0.09 mm from
  Q30's (0.15 mm strokes on their courtyard lines, courtyards abutting). r9_rf.py's PARTS and the limiter leads follow
  in U30's frame: R300.1 -> Q32.E, R300.2 -> Q32.B, Q32.B -> Q30.S, Q32.C -> trunk, Q31.D -> R302.2 re-anchored on the
  moved pads (each still octilinear, no new bend); R303.1 -> Q31.G keeps D-S4-03's 0.52 mm rise clear of R303.2 and
  enters Q31.G at 45 degrees 0.15 mm short of its centre (ending on the centre would cut the rise to a 0.37 mm tiny jog;
  a straight 45-degree run from R303.1 failed DRC against R303.2, both measured).
- D123 (+0.45, +0.35) to (30.25, 27.6): its pin-1 mark and Q123's both reach outside their courtyards into the gap
  between them (the circles 0.25 mm apart, the outlines' strokes 0.01 mm). The buzzer's 3V3 via moves to (29.08, 28.4)
  (straight down into D123.1, one 45-degree run into LS120.1) and the BUZZ_OUT via to (31.42, 25.82), on Q123.3's
  45-degree line and D123.2's axis (one 45-degree run from Q123.3, straight up into D123.2 and into LS120.2's pad):
  every lead of the buzzer is one straight run, Q123.3's one segment fewer than before, and BUZZ_OUT's route ratio is
  1.245 with no bend (step 8: about 1.55; a first placement of the via at (32.4, 26.4) gave 1.605, one more net over
  S8's 1.6).
- TP88 0.1 mm east (44.7, 75.6): C84's "+" polarity mark (1.3 mm outside C84's courtyard) reached 0.025 mm into TP88's
  square opening; the column's pitch (2.6 mm under the 1.0 mm test-pad rule) leaves no room along y.
r9_place_check's drc gate defers a silkscreen violation only when one of its items is a text (a designator, a value or a
board legend: r9_post.py's); one made of footprint graphics, pads and the edge alone fails at placement (judge_drc,
tools/test_r9_place GateDrc). The GND stitching table follows step 8's procedure: m3_design/r9_ground_aid.py on the new
step-7 board regenerated it (185 rows, was 187; every changed row lies round the buzzer: its return via (29.33, 28.45) ->
(28.38, 28.55), grid vias (26.4, 29.45) -> (31.0, 28.55) and (31.65, 24.85) -> (31.55, 25.1), cover / island / patch rows
between x 33 and 38.5, y 27-31)
and `--check` reproduces the frozen table; the ground gate's measures are step 8's (P9 3.45 mm, P10 7.32 mm, P7 the nine
recorded pockets, R6b 0.1022), and every step gate of the build passes.

**Basis.** check.sh holds DRC at every severity, silkscreen included (AGENTS §3, REQUIREMENTS M2: silkscreen never on
pads). Every gate of steps 3-8 deferred all three silk classes as "r9_post's", but r9_post moves only texts: the
footprint graphics depend on the placement alone, so the collisions were the placement's and invisible to the
legaliser, whose model is courtyards (on this board 24 footprint types draw silk past their courtyards, among them the
EasyEDA SOT-23 / SOD-323 pin-1 marks and C84's "+"). Editing the library silk instead would touch 7 SOT-23s and every
R8-era DRC test that links this worktree's kilib, and a hand-trimmed instance fails DRC's lib_footprint_mismatch; the
moves are 0.1-0.57 mm, change no net and no copper class, and were checked by DRC on a scratch board first (no silk
violation left). Stricter only: the gate now catches what it did not.

### D-S9-02. The silkscreen rules of r9_post.py

**Decision.** r9_post.py is R8's post stage (m3_design/r8_post.py, imported: RunOnSilk, the courtyard and run-on
designator pass, the fixed digest) on R9's geometry, with four changes:
1. Terminal pin legends go to the free spot nearest their own pin (top face first) whose bounding box has that pin as its
   nearest connector pin by OWN_MARGIN 0.3 mm (check_r8.terminal_legends' own measure, D92), searched within 6 mm; J1's
   go in the forward-edge strip over their pins where it has room (R8 fix pass 1). R8's hand-cut windows assumed pins
   in a row; R9's J121 / J124 stack along y with J121.2 and J124.1 facing each other at the junction, so the ownership
   test replaces the windows.
2. J122's plug numbers 1-4 are one row of digits on the plug columns (west to east: the _MIR numbering, owner decision
   2), each within 0.5 mm of its column's centre line, placed before the part legends so they get the plug side.
3. Pin-1 dots: r5_post's search (eight directions at fixed reaches) found no spot for U11 / U13; r9_post's searches the
   free spot nearest pad 1 within 1.0 mm in 64 directions whose nearest pad is pad 1, and fails the run if a part gets
   none (r5_post only printed it).
4. A pair of Fab designators still overlapping after r5_post.fab_refs' shrink (D8 / TP121) has the smaller part's moved
   inside its own courtyard box; a pair left overlapping fails the run.
The revision legend is M3-ASSY-R9 and JLC's order-number mark JLCJLCJLCJLC, both required. The outline is read from the
Edge.Cuts end points (R8 took the stroke-inclusive box).

**Basis.** AGENTS §3 silkscreen rule, REQUIREMENTS F8 (unambiguous pin legends, ARM / IGN), M2 (>= 1.0 mm text, never on
pads or off the board, legends within 6 mm of their part), r9_plan §4 step 9, D-S2-01 / D-S2-12 (renumbered pins:
legends drawn by pin).

### D-S9-03. Designators: 139 shown, 110 hidden on Fab

**Decision.** The R4 designator rule (r5_post.designators, then R8's courtyard and run-on tests) is applied unchanged: on
the finished board (fc3d5b34...) 139 designators are shown (6 top parts' on the bottom under their part) and 110 are
hidden and kept on the Fab layers (the assembly drawings carry every designator); the list is
`step9_evidence/post_report.json` (`hidden_references`) for step 10's M3_R9 silkscreen record (AGENTS §3). R8 showed 168
and hid 81. (Session 1's board 13c18075 showed 138 / hid 111: moving the BUZZ_OUT via to (31.42, 25.82), D-S9-01, freed
a spot for R75's.)

**Basis.** AGENTS §3 / REQUIREMENTS M2 (a designator with no spot nearer its own part than any other, clear of pads and
vias, on either face, is hidden, kept on Fab and listed). The rise in hidden designators is the denser board (courtyard
per outline 0.676 against R8's 0.584, 4,636 mm2 of outline against 5,372, survey X4c / X1c) with more tented stitching
vias (579 against 609 vias in 14 % less area); relaxing the rule (smaller text, text over vias) would weaken M2.

### D-S9-04. The finished board's power copper is held by the build again

**Decision.** r9_build.sh runs m3_design/r9_post_check.py after r9_post.py: the legend set (every required legend once,
no other board text, sizes, K-legends, ARM / IGN, the title revision) and, on the final copper, r9_power_check's dc
(D12, every rise <= R8, D_raw <= 1.0 mOhm, no via over 1.0 A), supply and f9 gates at 0.1 mm. tools/check.sh runs last.

**Basis.** Steps 7 and 8 drew copper after step 6's DC gate (D-S8-05 / 06 / 09 edited the RAW_ACT and RAW_PROTECTED
pours), and R8's build held D12 on its final copper (r8_build.sh's run_dc stage, R8_DECISIONS D95, fix pass 1
R8P1-INTEGRITY-02): without the stage R9's build would hold less than R8's. The gate calls r9_power_check's functions
unchanged.

### D-S9-05. The fab package is R9's

**Decision.** m3_design/r9_fab.sh (r8_fab.sh with R9's renders r9_top.png / r9_bottom.png) makes the package in
m3_design/assembly_review/fab/ from the finished board: jlc_orient regenerates tools/jlc_corrections.json (the variants
through PAD_ALIAS, D-S2-08), export_fab, the CPL verify, paste_check, fab_manifest, the renders; FAB_NET=1 adds the live
JLC stock and cost runs and check_procurement --cost-only. tools/test_fab_validation.py judges the worktree's board
again (it judged R8's committed board through r8_record until this step).

**Basis.** r9_plan §4 step 9; D-S2-08 ("tools/jlc_corrections.json is regenerated on the final board, step 9");
REQUIREMENTS M1 / M3.

### D-S9-06. kicad-cli DRC without a GUI session, unchanged scripts

**Decision.** With no logged-in GUI session (D-S6-14), the full gate and the build run unchanged: tools/check.sh and
run_r9_survey.sh take KICAD_CLI, so they get a scratch wrapper that sets DYLD_INSERT_LIBRARIES to step 6's shim and
execs kicad-cli (a shell may set the variable for its child; SIP only purges it when a protected binary is launched);
the build's gates (which call kicad-cli by its path) are replayed by the scratch runner as before. Nothing in the repo
depends on either.

**Basis.** D-S6-14; measured: kicad-cli pcb drc through the wrapper from /bin/bash reports the board's 187 silk
violations and 0 parity, as the shim does from KiCad's python.

### D-S9-07. The scorecard at step 9: every hard row met, the done rows reported

**Decision.** Step 9's survey (tools/run_r9_survey.sh with the 0.05 mm DC and the gate, on the finished board
fc3d5b34...; step9_evidence/r9_scorecard.md) is the step's verification of r9_plan §2, reported row by row in the step-9
handoff. Hard: 16 met, none missed; X2d "not measured" means no BAT_IN / ACT_FET_S copper within the metric's 3 mm reach
of bus / igniter / drain copper on the same layer, and check_r9 K-power-pyro (D85 at 2.5 mm, searched to 3.5 mm) finds
none (X2d > 3.5 mm). Done: 34 met, 16 missed, 3 "not measured" that are met by construction (X2c: no foreign net within
3 mm of armed copper, X2 = X2b = 0; Z1e / Z1f: no rule-E / rule-F pair within pyro_probe's reach). The 16 misses are
the earlier steps' recorded ones, unchanged by step 9 (the post stage changes no copper, asserted), each with its
record: X1 102 (D-S3-03, owner decision 1's 102 mm fallback); X2g 7 (CH1 parts' bounding box 4.0-26.3 x 56.3-88.6 mm
crossed by 3V3A, ACT_GATE, SERVO1_MCU, SERVO1-3_OUT, SERVO4_MCU, none within 3 mm of armed copper; D-S6-13 for ACT_GATE,
steps 6-7, step8_deltas.txt); S8 / S9 2 (RADIO_TXEN, the row's keep-out-forced net: the TXEN loop round U31's west side on B.Cu, R7 / R8's, D-S4-06; RAW_ACT_SENSE_MCU 2.24 mm of
track on a 0.90 mm MST, U1.34 on F.Cu to R172.2 on B.Cu through one via on pin 34's line, D-S7-12, 1.34 mm absolute
excess); S10b 260, Y1 31, Y1b 14, Y2c 11, Y5 34, Y7 1, X3f 291.8 (steps 4-7's routing, step8_deltas.txt); P6 1478.1
(D-S6-13); P7 9 (D-S8-15); P10 7.32 (D-S8-16); R6b 0.1022 (D-S8-17); index_r9 84.8 (the composite of these). No row
moved between step 8's board and step 9's (S8 went to 3 on session 1's first via placement and back to 2 with the
via at (31.42, 25.82), D-S9-01).

**Basis.** r9_plan §4 step 9 ("survey with the 0.05 mm DC") and §2; §5's stop rule leaves the done-row misses to the
owner's acceptance or the review loop. Step 9's brief is post and fab; reworking steps 3-8's copper for those rows is
outside it, and none of them is a hard row or a safety rule.

## Step 10: requalification and records

### D-S10-01. Requalification is measured on the final board by the gate's own code and bound to its SHA-256

**Decision.** Every qualification survey_constraints §8.4, §9.4 and §11 lists as invalidated by a clean sheet is
re-measured on board `fc3d5b34…` (step 9's, unchanged by step 10) by `step10/requalify_r9.py`, which calls the gate's
functions (tools/check_r9.py, pyro_probe.py, bridge_table.py, rule_h_seed's report, r9_pyro_check, r9_rf_check,
gcpw_solve) and reuses R8 step 9's measurement code (`sources/r8_design/step9/requalify.py`, imported) only where it
measures geometry without R8 constants, with R9's own constants put in (PYRO_BLOCK from its rule area, U30's body box
from U30, the tie holes from check_r9 M-3, the tab windows from tools/tab_windows.py). Nothing is copied from R7 or R8
except where congruence is shown on this board (the RF launches and chains, rf.launch / rf.r7). Each file in
`step10_evidence/` names the board SHA-256 in its first line or its `board_sha256` field, and requalify_r9.json also
hashes itself and every input it imports.

**Basis.** The brief ("requalification evidence bound to the board SHA ... never copied, never weakened"); r9_plan §4
step 10; survey_constraints §11 (what a clean sheet invalidates).

### D-S10-02. The return-loss cascade is a record (Inference), not a qualification

**Decision.** `requalify_r9.return_loss` re-runs pass2_rf §3.12's lossless ABCD cascade on each chain as drawn: the
launch at its solved 48.79 ohm for 4.2 mm then 0.2 mm at about 70 ohm, the line at the sample-weighted solved Z0
(50.34 ohm), the line pads at their solved 36.6 ohm over their drawn lengths, the ESD diode 0.2 pF (Infineon
ESD103-B1-02 data sheet, the maximum at 1 MHz), the bias choke as >= 500 ohm (u-blox), the DNP shunt lands as 0.94 mm
open stubs ending in 0.03 pF, the 0 ohm series part as 0.4 nH and the module port as 50 ohm. Result: GNSS |S11|
0.042-0.074 (RL 22.6-27.6 dB) over 1.176-1.61 GHz, radio 0.064-0.066 (RL 23.6-23.9 dB) at 902-928 MHz (R7 pass 2:
about 19-21 and 25 dB). Every parameter but the drawn lengths and solved impedances is pass 2's assumption, so the figure
is labelled Inference; the VNA bench step (ORDERING section 5) is the evidence.

**Basis.** survey_constraints §8.4 item 3; AGENTS §2.5 (inferences labelled); step 4's open item (D-S4-02: C303 moved to
the bias node, the cascade not re-run there).

### D-S10-03. Four panel tabs, one in each end third of each long edge, GND under each, none beside the CH1 column

**Decision.** ORDERING §3 asks JLC for four 5 mm long-edge tabs, chosen by `step10/tab_plan_r9.py`
(`step10_evidence/tab_plan.json`) among every legal 5 mm position (tab_windows' rules and 0.25 mm step): one wholly in
each end third of each long edge (T-1); GND only on all four copper layers in the tab's inner band (0.5-3 mm from the
edge, fills sampled and any track, via or pad reaching in); >= 5 mm from the PYRO_BLOCK area; then the largest smallest
margin over the part / pad (1.5 mm), capacitor-class (5 mm), connector (2 mm) and hole (1.5 mm) rules, ties toward the
board end. Chosen: west y 0.5-5.5 (TP30 3.20 mm, U30 5.57 mm, the (4, 4) hole 2.40 mm) and y 96.5-101.5 (J1 8.91 mm,
the (4, 98) hole 2.40 mm); east y 8.75-13.75 (C310 7.32 mm) and y 96.5-101.5 (R83 3.31 mm, C87 6.11 mm, the (42, 98)
hole 2.40 mm). There is no mid-span tab: every legal west position in the middle third (window y 53.5-101.5, starts
below 68) lies within 3.4 mm of the PYRO_BLOCK area, and on that window a tab clears the 5 mm block margin only from
y 93.5 (102 of its 115 forward-third positions fail it); the east edge has no legal position in its middle third
(windows 0.5-27.0 and 92.75-101.5). That JLC accepts four tabs on a 102 mm board is an Inference (JLC suggests 4-6 over 100 mm; R8 asked five on
118 mm): confirm in Confirm Production File.

**Basis.** survey_constraints §3 (4-6 tabs, GND-only In2 under tabs where possible, R8P3-POWER-05); D-S1-18 (T-1);
depaneling stress on an MLCC can crack it into a short (house 5 mm margin), and in the CH1 column a cracked C128 is a
drain-to-GND short (fires when armed) and a cracked C126 a gate fault: no tab stress there is the safe choice.

### D-S10-04. F7's fire loop on the final copper: every board segment solved, the FETs at their data-sheet maxima

**Decision.** F7 ("revalidate on the final copper") is closed by `step10/run_dc_r9.sh` on every board segment of the
fire loop: RAW_ACT Q121 -> J124.2 (the RAW bar), PYRO1_BUS J124.1 -> R134.2, PYRO1_IGN R134.1 -> J121.2, PYRO1_OUT
J121.1 -> Q124's drain (each at 0.05 mm), BAT_IN J1.1 -> Q120 and ACT_FET_S Q120 -> Q121 (step 9's 0.05 mm solves,
`step9_evidence/dc005_{bat,fet}.txt`) and the GND return Q124's source pins -> J1.2 (0.1 mm, window x 0-46, y 50-102: an
upper bound); plus the three FETs at their data-sheet maxima at the specification points the drive exceeds (AON6403 <=
4.3 mOhm at Vgs -4.5 V each, the gate seeing -6.7 V at 7.4 V; AON7524 <= 5.8 mOhm at Vgs 2.5 V, the gate seeing >= 2.77
V at the guaranteed corner (MARGIN_PRESCRIPTION's pyro gate drive row; corrected in D-S10-16); docs/CIRCUIT_REVIEW.md,
docs/MARGIN_PRESCRIPTION.md, both citing the AOS data sheets). Result (`step10_evidence/dc/fire_loop.txt`, D-S10-16):
17.7 mOhm of board copper (RAW_ACT -> J124.2 10.06 mOhm, bus 2.41, igniter 2.42, drain 1.58 mOhm, BAT_IN 0.16, ACT_FET_S
0.26 and the GND return <= 0.81 mOhm, an upper bound) and 14.4 mOhm of FETs, 32.1 mOhm on the board; F7's budget becomes
7.4 V / (4.45 ohm + 0.0321 ohm) = 1.65 A (without the board 1.66 A) against 1.5 x 1 A all-fire: met on the final copper
(1.65 x all-fire). The harness term (<= 0.3 ohm) stays a bench item (ORDERING section 5's commanded fire).

**Basis.** REQUIREMENTS F7 (budget 7.4 V / 4.45 ohm = 1.66 A against 1.5 x 1 A all-fire; "revalidate on the final
copper"); step 5's and step 6's records items (bars 3.15 / 4.96 / 4.96 mOhm by sheet resistance; the RAW bar about
10.5 mOhm). R8 recorded only the RAW_ACT -> J124.2 term (0.44 mOhm, M3_R8); R9's RAW bar is a 1.0 mm F.Cu track from
the spine to J124.2, so it is the largest copper term, and the FETs, which F7's formula leaves out, are counted.

### D-S10-05. The DC solve set and its scheduler

**Decision.** `step10/run_dc_r9.sh` solves, on the final board: R8 step 9's 25 supply paths (R9 keeps R8's
designators) and RAW_PROTECTED -> R122 at 0.1 mm (M3_R7's table grid); the fire loop (D-S10-04) at 0.05 mm; the GND
returns (fire loop and servo, J122's four GND pins -> J1.2 at 7.7 A) at 0.1 mm in the window x 0-46, y 50-102 (copper
outside it left out, so R is an upper bound; GND has 0.2 mm tracks, so 0.1 mm is the finest legal grid). Each output's
first line is the board SHA-256 (tools/dc_solve.py). The queue refills a slot whenever any solve ends (`DC_JOBS`,
default 8): session 1's version waited on the oldest solve, which left the supply rows idle behind the hour-long GND
window.

**Basis.** survey_constraints §11 (F4 re-solved, bound to the new SHA); R8 step 9's precedent (run_supply_dc.sh,
run_dc.sh DC_GND).

### D-S10-06. ORDERING is rewritten for R9 from measured facts

**Decision.** Every R9 coordinate, count and distance in docs/ORDERING.md comes from a file bound to `fc3d5b34…`:
`step10_evidence/ordering_facts.json` (`step10/ordering_facts_r9.py`: assembly counts, edge distances, J3's legs, J2's
pads, PYRO_BLOCK's contents by face, staking, U9's IN pin, the bottom power pours, jack-to-ESD gaps, the 7.7 A necks'
cut boxes against the FETs), requalify_r9.json (probes, holes, mark, bare copper, IMU), tab_plan.json, the gate reports
and the step-9 fab reports. Two R9 facts change procedures, not just numbers:
- **Stall test.** All three 7.7 A necks lie at an FET (RAW_ACT's cut box inside Q121's courtyard, BAT_IN's 0.24 mm from
  Q120's, ACT_FET_S's inside Q120's; all on B.Cu), where each AON6403's own dissipation dominates the reading, so the
  FETs and the copper beside them are judged against MARGIN R1 (<= about 29 C rise, as R8 judged its BAT_IN / ACT_FET_S
  readings) and the neck readings are recorded against D12's 12.7 / 12.1 / 20.4 C estimates as information. J122 keeps
  R8's <= 30 K line.
- **Terminals.** Both pyro terminals' wires enter from the west edge, and the pad roles are named, never positions
  (D-S10-09).

**Basis.** survey_constraints §12 ("ORDERING §3-§7: all coordinates, tabs, mark, probe and coat points, sled hole list,
J124 'unmoved', PYRO_BLOCK extent"); AGENTS §3 (verify, don't guess).

### D-S10-07. tools/check.sh runs through the scratch kicad-cli wrapper with KICAD_PY set

**Decision.** Without a logged-in GUI session (D-S6-14), `tools/check.sh` is run with `KICAD_CLI` = the scratch wrapper
of D-S9-06 (it sets `DYLD_INSERT_LIBRARIES` to the D-S6-14 shim and execs kicad-cli) and `KICAD_PY` set explicitly to
KiCad's python3: check.sh derives KICAD_PY from the kicad-cli path, and the wrapper is not inside KiCad.app, so without
it the metadata audit falls back to /usr/bin/python3 (no pcbnew) and fails. Environment only; no repository change.

**Basis.** D-S6-14, D-S9-06; session 1's first check.sh run (failed at the metadata audit only, then exit 0 with
KICAD_PY set).

### D-S10-08. REQUIREMENTS: R9 clauses, F10's strip boundary, and an R9 acceptance clause; no intent changed

**Decision.** docs/REQUIREMENTS.md gains R9 clauses beside R8's (R8 stays the accepted fallback, so its text stays):
F4 (the R9 solve and stall-test basis), F7 (D-S10-04's figure), F8 (D85 at 2.5 mm, rule G's P-1b scope, the strict pad
rules, P-3 / P-7, the fill margins), F10 (owner decision 3: the strip is y 0-22.0 of the 46 x 102 mm board; check_r9's
R-rules hold the strip by rule, not hash; the stitching gaps and the fence as measured; the radio module 46.13 mm from
the nearest armed copper, accepted against R7 pass 1's 68 mm rationale on the strength of the keyed-radio immunity bench
test), P1, P2 (the mid-span support east at (42, 59.5), owner decision 5's default; the plate model's figures), M2 (A8
gone; the R9 list awaiting acceptance), M3 (the R9 cost run); the accepted risk "gate-net spacing outside the pyro
block is the board's 0.15 mm default" is retired for R9 by rule G's P-1b scope (kept for R8); and a new "R9 acceptance"
section names check_r9 and the R9 contracts in place of check_r8's hashes.

**Basis.** R9_OWNER_DECISIONS items 1-5; survey_constraints §12; step 2's records note (P-1b retires the accepted risk);
the brief ("REQUIREMENTS (F10 strip boundary and the owner decisions)"). Each clause records a decision the owner made
or a measurement; none weakens a requirement.

### D-S10-09. Terminal text names pad roles, never positions

**Decision.** Harness, ORDERING, FMEA and STATUS text for R9's renumbered terminals (D-S2-01) names each pad by its role:
J124's RAW pad (pin 2) is forward (y 86.04) and its BUS1 pad (pin 1) aft (y 80.96); J121's IGN pad (E1+, pin 2) is
forward (y 75.81) and its OUT pad (E1-, pin 1) aft (y 70.73); both terminals' wires enter from the west edge (x = 0);
J122's plug 1 (SERVO1) is the west end. The silkscreen's pin legends (J124 2:RAW on the top, 1:BUS1 on the bottom; J121
1:E1- on the top, 2:E1+ on the bottom) identify them on the board.

**Basis.** D-S2-01 / D-S9-02 (same part and land, numbering mirrored, each pad number keeps its net); step 2's and step
9's records notes ("the harness / FMEA text must use the pad roles, not R8's numbers"); `step10_evidence/ordering_facts.json`
pins. (Review pass 1, R9P1-REQUIREMENTS-08: step 10 did not touch FMEA_REDUNDANCY, which held no position text; the fix
pass wrote its R9 row (I-4 / V-16), by role, with the IGN–BUS1 entry adjacency.)

### D-S10-10. STATUS, AGENTS and README: R9 the current, unreviewed candidate; R8 the accepted, orderable fallback

**Decision.** STATUS.md gets an R9 section ahead of R8's (built, gated, requalified; no review pass; not accepted;
uncommitted) and R8's heading becomes "owner-accepted, orderable fallback"; AGENTS.md §1's status column is R9's, with
R8 named as the fallback; README's status line follows. ORDERING says: until R9 is accepted, order R8.

**Basis.** The brief ("STATUS.md (R9 current, R8 the accepted fallback)", "AGENTS.md §1"); AGENTS §3 (update STATUS
after a board change, stating what was and was not verified).

### D-S10-11. The parent VEHICLE.md stack row is proposed, not applied

**Decision.** The step-10 handoff proposes the parent repository's VEHICLE.md stack-row text for R9 (46 x 102 mm, the
five holes, the jacks' overhang, J1's forward entry, the pyro leads west and the battery lead east); it is not written
into the parent repository.

**Basis.** The brief ("a proposed parent VEHICLE.md stack-row update ... in your handoff"); the parent repository's commit
rule is the coordinator's (R8 D84's precedent). Review pass 1 (R9P1-MECHANICAL-02) extended the proposal with the
standoff height (≥ 3.5 mm), the battery leads' U-turn into J1 beyond the forward edge and the harness sides
(`sources/r9_review/fix1_handoff.md` §5); still not applied.

### D-S10-12. The M2 review sweep: R8's sweep, profile r9, no rigid copper

**Decision.** `step10/m2_sweep_r9.py` runs R8's sweep (`sources/r8_design/step9/m2_sweep.py`, imported unchanged) with
route_check's profile r9 and no rigid copper (a clean sheet inherits none), on `fc3d5b34…`; its counts are the
R9_VALIDATION deviation list's part C and F rows (chain detours 18: 12 with no redraw, 6 with a candidate redraw for the
review loop; adjacency 33 / pad adjacency 28; via steps 1; poured hops 0; routes 38; pad-edge ends 5 at 3 pads; via
folds 34; short hops 7, all power vias with no GND via within 1.5 mm; bumps 1 in 21 windows; margin-free search 2 bumps
in 35 windows and 7 redraws). These are fc3d5b34's counts; the fix pass's are R9_VALIDATION's. The one via step, CC1's
0.113 mm track end inside its via (7.85, 32.75), stands for a 0.22 mm offset jog through the via (R9P1-ROUTING-03:
drawn straight from the via centre it fails route_check's tiny-jog test; no DRC-clean alternative exists in the J3 / D4 /
USB_DM pocket, variants cc1b, cc1c, cc1d); R9_VALIDATION C6 lists it for the owner.

**Basis.** REQUIREMENTS M2 ("What review checks"; the deviation list covers every review category); R8 step 9's
m2_sweep.py.

### D-S10-13. A records check binds the records to their evidence

**Decision.** `step10/check_records.py` checks that every evidence path the R9 records cite exists, that every file in
`step10_evidence/` is bound to the board SHA-256, that no placeholder is left, and that the records' key figures equal
their evidence (a table of claim -> file -> field). It is run at the end of the step and its output is
`step10_evidence/check_records.txt`.

**Basis.** The brief ("Verify: every claim cites an evidence file").

### D-S10-14. TP120's two in-pad RAW_ACT vias are named as R9's bare-contact via exception (found by step 10)

**Decision.** Two RAW_ACT vias of step 6's via row (y 78.2) open into test pad TP120's 1.5 mm square opening (RAW_ACT,
top, centre (30.2, 78.4)): the via at (29.6, 78.2) lies inside the pad's west edge and the one at (31.0, 78.2)
straddles its east edge (0.3 mm holes; `step10_evidence/ordering_facts.json` `vias_in_bare_contacts`; no other bare
contact, TP122 and J2 included, has a via). REQUIREMENTS M2 allows in-pad vias in bare contacts with no paste and no part
(tools/check_r7.py's BARE_CONTACTS, run by check_r9 K-copper), so this is not a rule miss, but like R8's TP122 via it
must be named: in M2's R9 clause, ORDERING §3 (via covering: these two stay open and unplugged, no plug ink on the
contact), ORDERING §4's expected DFM queries, and the R9 deviation list (C18). It is power copper, not a critical signal
net, so AGENTS §3's GND-via rule does not apply; TP120 keeps about 1 mm of solid copper between the holes for a probe.
Not moved here: step 10 changes no copper; a review pass may move TP120 or the two vias (the review loop's call).

**Basis.** REQUIREMENTS M2 (bare-contact exception; R8 named TP122's as its one); AGENTS §3 (verify, don't guess); the
brief (records, no copper change). Found while measuring ORDERING's via-covering line; no earlier R9 record named it.
**Lapsed in review pass 1** (R9P1-ROUTING-02, D-F1-04): the row's west via is dropped and (31.0, 78.2) moved to
(31.5, 78.2), so no via meets TP120's opening.

### D-S10-15. Step 10's last session runs kicad-cli, tools/check.sh and the tests as they are (a GUI session is logged in)

**Decision.** The Mac restarted between sessions 2 and 3 of step 10, and the user is now logged into the GUI (`who`:
`console`). A probe, `kicad-cli pcb drc --severity-all --schematic-parity` straight on the board, returned rc 0 with 0
violations, 0 unconnected and 0 parity issues, so session 3 rebuilt neither the D-S6-14 shim nor the D-S9-06 wrapper:
`tools/check.sh` found kicad-cli and KiCad's python3 by itself (D-S10-07's explicit `KICAD_PY` is not needed with the
real binary), and the tests ran with `KICAD_CLI` set to the real binary. The session-3 gate reports
(`step10_evidence/gate/`) equal session 1's shim-run reports in every field but timestamps (and audit.json's hashes of
the dated DRC / ERC reports), local paths and R-5's per-part split of the in-window GNSS samples (D-S10-18). With a GUI
session, KiCad's binaries print a Fontconfig cache warning and wx's "create wxApp before calling this" assertion on
stderr; the evidence files drop those lines, so each DC output's first line is again the board line that
tools/dc_solve.py writes.

**Basis.** The brief (the shim is rebuilt only without a GUI session); D-S6-14 ("with a GUI or screen-sharing session
logged in, `r9_build.sh` runs as is"); the probe and the report comparison (`r9_step10_progress.md`, session 3).

### D-S10-16. The fire-loop figure comes from the bound solves through a script

**Decision.** `step10/fire_loop_r9.py` sums the seven board segments of F7's loop from their dc_solve outputs (it
refuses solves bound to different boards), adds the three FETs at their data-sheet maxima and evaluates F7's formula,
writing `step10_evidence/dc/fire_loop.txt`; the records quote that file (D-S10-04's result). D-S10-04's gate-drive basis
for Q124 is corrected: MARGIN_PRESCRIPTION gives the fixed gate ≥ 2.77 V at the guaranteed corner (its pyro gate drive
row); session 2's draft said "about 3.2 V" with no source. The AON7524's 5.8 mΩ maximum at Vgs 2.5 V applies either way.

**Basis.** AGENTS §2.5 and §3 (verify, don't guess; an inference is labelled); REQUIREMENTS F7's formula;
MARGIN_PRESCRIPTION (the pyro gate drive row and the AON7524 paragraph); docs/CIRCUIT_REVIEW.md (the AON6403 gate
divider, −6.73 V at 7.4 V, and its 4.3 mΩ maximum at −4.5 V).

### D-S10-17. The DC outputs are evidence files in step10_evidence/dc/

**Decision.** The 32 outputs of `step10/run_dc_r9.sh` (session 3: `DC_JOBS=8`, rows in the order gnd, fire, supply, so
the two long GND windows start first) are copied from the scratch folder into `step10_evidence/dc/`, the board path
written as `<repo>/…` (AGENTS §4) and wx's start-up line removed (D-S10-15), so each file's first line names the board
and its SHA-256. `dc/dc_summary.txt` is the script's own closing table, bound by `step10/bind_report.py`;
`dc/fire_loop.txt` is D-S10-16's. Scratch is not durable: sessions 1 and 2 lost their solves to a restart.

**Basis.** D-S10-01 (every step-10 evidence file bound to the board); D-S10-05; the restart that wiped `<scratch>/r9/s10`.

### D-S10-18. Three gate observations go to the review loop, not to a step-10 fix

**Decision.** Step 10 changes no tool its evidence hashes (requalify_r9.json and the gate reports hash
`tools/check_r9.py`) and no test, so three observations are recorded for the review loop instead of fixed here:
- `tools/check_r9.py`'s docstring still describes M-7 as "U4 bottom, rotation 0 (the M3_R5 axis map)", while the rule
  keys the required rotation on the title-block revision (`IMU_ROTATION`, 180° for M3-ASSY-R9, D-S7-06) and passes on the
  board; the text is stale, the check is not.
- R-5's evidence splits the in-window GNSS samples among the chain's parts differently from run to run (session 1: C303
  12, C305 8, L30 26, R304 36; session 3: C303 8, C305 12, D30 2, L30 28, R304 32, and in its final re-run C303 8,
  C305 8, L30 34, R304 32; 155 samples every time, the radio's split unchanged). The verdict and the totals do not change; an iteration-order effect where windows overlap is the
  likely cause (Inference). Byte-identical gate reports across runs would need the attribution made deterministic.
  (Corrected by review pass 1, R9P1-RF-03 / -INTEGRITY-01: the radio's split varied too, and the cause is measured, not
  inferred: `tools/check.sh` runs the checkers with `python -I`, which ignores PYTHONHASHSEED, and R-5 credited a sample
  to the first part of a set, while pyro_probe kept the first of equal-distance pairs built from a set of net names;
  both are deterministic since D-F1-03.)
- `quality_audit/test_quality_tools.py` is not hermetic: with `KICAD_PY` exported (as `tools/check.sh` exports it for
  its own steps), 4 of its 21 tests fail (3 failures, 1 error), because `verify_board.native_refill_python` prefers the
  environment's `KICAD_PY` to the tests' fake tools and runs a real refill; with `KICAD_PY` and `KICAD_CLI` unset, as
  step 9 ran it, all 21 pass under both Pythons (`step10_evidence/tests.txt`). The tests should clear the variable.

**Basis.** The brief (records; no copper change); the two gate reports (`step10_evidence/gate/r9.json` and session 1's,
compared in `r9_step10_progress.md`); the test runs (`step10_evidence/tests.txt`); r9_plan §5 (the gate-integrity
reviewer checks determinism and live tests).

### D-S10-19. MARGIN_PRESCRIPTION P1-9 gains an R9 status

**Decision.** docs/MARGIN_PRESCRIPTION.md P1-9 ("Copper and vias") gets an R9 status paragraph beside R7's and R8's:
not met as written (no 10 mm equivalent, not mirrored on L4 throughout), the D12 limits met with more margin than R8's
and held by the R9 build at 0.1 mm, no series via on the 7.7 A path, the via fields' largest barrel currents, the servo
GND return (step 10's solve) and the stall test's R9 basis (D-S10-06). REQUIREMENTS F4 cites P1-9's status per
revision, so R9's belongs there; the prescription itself is kept as written.

**Basis.** R8 step 9's precedent (P1-9's R8 status, R8 D74-D84's records pass); REQUIREMENTS F4; the step-9 and step-10
DC evidence (`step9_evidence/dc005_*.txt`, `step10_evidence/dc/gnd_servo.txt`).

## Review pass 1: fix pass (2026-10-25)

Decisions of the fix pass for R9 review pass 1 (`sources/r9_review/pass1_*.md`; log
`sources/r9_review/fix1_progress.md`, handoff `sources/r9_review/fix1_handoff.md`). Every copper change goes through the
R9 generators and tables, so `m3_design/r9_build.sh` reproduces the board; no check is weakened and no pyro, arming or
actuator safety rule is relaxed. The per-finding dispositions are R9_VALIDATION "Review pass 1".

### D-F1-01. QSPI_IO2's escape runs 0.55 mm inward of the gate pin; check_r9 P-7b guards U1's gate pin

**Decision.** In `r9_route_imu_baro.py` QSPI_IO2's east run from U1.1 moves from y 50.9 to y 50.6:
(12.0, 51.55) → (12.0, 50.6) → (13.9, 50.6) → (13.9, 47.1). It passed U1.3 (PYRO1_GATE_N) 0.250 mm from the pad; now
it keeps 0.55 mm from the pad (check_r9 P-7b's table: QSPI_IO2 0.55, 3V3 1.25, IMU_INT1 1.369 mm; R8 0.75 / 1.25 mm, the same table run on R8's board). `tools/check_r9.py` P-7 gains P-7b: U1's gate pin pad (inside the courtyard, which P-7's clipped measure
and rule G exempt) ≥ 0.5 mm from every copper item that is not a U1 pad, GND or unconnected (another net passing the pin
is a short that drives the gate while the MCU runs); its table is the evidence (`mcu_gate_pin`).

**Basis.** R9P1-PYRO-01 (Minor): with the firmware running, PE4 drives low against QUADSPI's IO2 driver, a hard short
sits near mid-rail and the gate reaches about 1.6 V, above the AON7524's 1.2 V maximum threshold (AOS Rev 1.1 p. 2;
Inference); R8 kept 0.750 mm. The reviewer's spot check of y 50.6 (0.55 mm to the pad end, 0.20 mm to U4's GND via
(13.2, 50.05), 0.252 mm to U1.6's 3V3 via, 0.34 mm to INT1's via) is confirmed by the imu_baro gate and DRC. R8's
0.75 mm needs y ≤ 50.4, which moves U4's GND via (D-S7-10's knot): not cheap, not taken. `test_r9_check`
`test_p7b_mcu_gate_pin` seeds the 0.25 mm case.

### D-F1-02. The radio module's ground pins get R7's vias back; TXEN at the signal width

**Decision.** `r9_rf.GND_MODULE` adds R7's three module-frame GND vias (0.6 / 0.3 mm) at U31-relative (+3.74, +1.27),
(+1.27, −3.60), (−2.54, +3.60) (board (34.35, 15.27), (31.88, 10.40), (28.07, 17.60)), the joints of U31.2 / U31.7 /
U31.16, the E22's only grounds. RADIO_TXEN's loop takes the 0.2 mm signal width (`W_TXEN = W_SIG`) and the strip grid
via (24.7, 10.45) moves 0.05 mm west to (24.65, 10.45), so TXEN keeps 0.2 mm from it; `r9_route.WIDTHS` drops 0.15 (the
board has five track widths; D-S5-08's list shortens, X5 = 5).

**Basis.** R9P1-RF-01 (the pins' copper path to a via went from R7's 0.20 / 0.35 / 0.35 mm to 1.15 / 1.12 / 1.05 mm;
EBYTE manual §4.1 "reliably grounded"); R9P1-ROUTING-01 (no R9 decision gave a reason for 0.15 mm; the reviewer's
variant was DRC-clean). Measured on the fix-pass board: the pins' copper path to a via is 0.20 / 0.35 / 0.35 mm again (U31.2 / U31.7 / U31.16; `sources/r9_review/fix1/fix1_measure.py` `module_gnd_pins`), R-7's strip reach 2.99 mm on F.Cu (3.10 before) and its stitching gaps unchanged (GNSS east 2.38 / west 1.75, radio east 1.70 / west 2.405 mm).

### D-F1-03. check_r9 and pyro_probe report deterministically; R-7 names compass sides; R-8 samples U31's body

**Decision.**
- R-5 credits each out-of-profile window sample to the chain part whose pad is nearest (within 0.3 mm), ties to the
  lower designator, iterating sorted designators; the window table is sorted.
- `tools/pyro_probe.py` iterates sorted net names and keeps the smallest (mm, labels) pair, so equal distances name the
  same pair in every run.
- R-7 names its stitching evidence by compass side (east / west for a line run from the jack forward; beside()'s +d is
  east on KiCad's y-down canvas).
- R-8 samples In1 GND over U31's whole 10 × 10 mm body, as In2 already was (survey 8.4 item 5, R8's module_ground); the
  keep-out coverage requirement stays on the interior.
- The module docstring's M-7 line names the per-revision rotation (R9 180°).

**Basis.** R9P1-RF-03, R9P1-INTEGRITY-01 (`check.sh` runs `python -I`, which ignores PYTHONHASHSEED; the R-5 split and
P-0's tie labels changed between runs, so gate reports could not be compared byte for byte); R9P1-RF-02 / -REQUIREMENTS-07
(the records named the sides the wrong way round); R9P1-INTEGRITY-02 (a notch in In1's pad-ring band under U31 would
have passed); R9P1-INTEGRITY-05. Verdicts are unchanged on fc3d5b34; `test_r9_check` gains the In1 body notch and the
'GNSS west' label. This corrects D-S10-18's statement that the radio's split was unchanged.

### D-F1-04. TP120's opening holds no via; the scorecard counts vias in every test pad

**Decision.** `r9_power.RAW_ACT_VIAS` drops the row's west via (29.6, 78.2) and moves (31.0, 78.2) to (31.5, 78.2), so
no via hole meets TP120's 1.5 mm opening (the reviewer's alternative; the column at x 29.6 starts at y 79.6, and the
hole margin to the opening is 0.30 mm (the column's (29.6, 79.6); (31.5, 78.2) 0.40 mm) instead of the 0.101 mm of moving both). D-S10-14's named exception lapses
(REQUIREMENTS M2's R9 clause, ORDERING §3 / §4, R9_VALIDATION C18). `tools/r9_extra_metrics.py` counts Z4 over every
TP* pad's opening and `tools/r9_scorecard.py` prefers it to the R8 survey's A8 (TP122 only).

**Basis.** R9P1-ROUTING-02 (moving TP120 is blocked by C84's courtyard and the 1.0 mm test-pad rule); R9P1-REQUIREMENTS-02
(Z4 was reported met with two vias in TP120: on fc3d5b34 Z4 = 2, so 33 done rows met and 17 missed). The 7.7 A RAW_ACT
solve with one via fewer: 0.80 mΩ, neck 7.89 mm on B.Cu, 12.6 °C at 0.05 mm (fc3d5b34 0.79 mΩ, 7.81 mm, 12.7 °C); 31 vias carry current, the largest 0.47 A, at the moved (31.5, 78.2) (0.46 A).

### D-F1-05. C98 beside U11's USB input; C83 and C82 recorded

**Decision.** C98 (U11's USB-input bypass) moves to (39.275, 64.2), rotation 180, bottom (`r9_place.tsv`,
legaliser-checked), C98.1 on the trunk 1.94 mm of track from U11.7 (was 5.29 mm), C98.2 under U11.6; USB_LIMITED's end
in `r9_route_power_ctl.py` runs south of C98 on y 63.2 (a T up into R87.1), east and north into C98.1, then 45° into
U11.7. C83 (U10's 100 nF input bypass) stays on U10.3's EN branch: the legaliser found no spot on U10.1's run (north of
U10 V_D / USB_FAULT_N and the USB pair; west needs R7 / R9 moved, the CC1 knot), and the VBUS-tee redraw would re-route
the J3 / R9 / U10 knot; it is recorded (R9_VALIDATION C23) with C82's TPS25947 §8.4.1 deviation, as M3_R8 recorded R8's.

**Basis.** R9P1-POWER-01 (TI SLVSEA3F §11: bypass capacitors "as close to the device as possible"; TI SLVS841F pin table
and §12.1 for U10; SLVSFC9C §8.3.1 / §8.4.1 for U9's output). D-S6-06's citation is corrected: TI's capacitor sentence is
SLVSEA3F §11; §12.1 says "short wide traces".

### D-F1-06. J122's four GND pins stay solid; the exception is listed with its R9 measurement

**Decision.** J122.3 / .6 / .9 / .12 keep R7 / R8's pad-level solid connection (F.Cu, In1, B.Cu; J122.3 also In2). The
relief was built and judged: DRC clean, no starved thermal (the reviewers counted 4 / 4 / 2 spokes per pin, F / In1 / B); but on
F.Cu J122.3's 0.5 mm relief ring closes the channel between D120's 3V3 lane (x 17.9) and J122's west column, leaving a
0.86 mm² GND piece (x 18.15–19.13, y 62.61–64.31) joined to the board only by one spoke to J122.3: a new single-stitch
island that `r9_ground_check`'s islands gate fails (0 GND vias counted) and P7 would count. Solid joints keep that copper
joined and the 7.7 A servo return solid. The exception is R9_VALIDATION C21 (the current reason and this measurement;
R8 C17's starvation reason does not hold on R9) for the owner's acceptance; ORDERING keeps the preheat and hole-fill
instructions.

**Basis.** R9P1-POWER-04 / -DFM-03 / -REQUIREMENTS-04 (the reviewers preferred the relief or the listed exception, the
owner's choice); REQUIREMENTS M2 (reliefs wherever the spokes are not starved, exceptions listed); the islands gate
(P7: recorded pockets only). The relief variant of `r9_pcb.py` (RELIEVE) was not kept.

### D-F1-07. The ground aid's copper stage and the ground gate's copper gate; C121's corridor exception

**Decision.**
- `r9_power.RAW_ACT_F`'s west edge x 29.75 runs to y 76.6 (was 75.6), so the GND guard strip beside ARM1_SENSE no
  longer necks to 0.37 mm.
- `r9_ground_aid.py` gains a last stage, `copper`: (a) every GND SMD pad of a C / U / Q / J part forward of the strip
  more than 5 mm of copper from a GND via or plated GND hole gets the legal spot its copper reaches soonest; (b) the
  copper beyond 8 mm of copper from every via, taken as 8-connected clusters (a dead end's far part), worst first, gets
  a via at the legal spot nearest the cluster's worst point along the copper among the spots ≥ 2 mm of copper from
  every via; a cluster with no such spot is logged. A copper-stage via goes only where it leaves no new island with
  fewer than two GND vias (`place_safe`; the first try at C121.2, (34.6, 61.5), revived a 1.34 mm² B.Cu sliver between
  USB_LIMITED and the RAW_ACT pour and was rejected).
- C121.2 (the 470 µF servo bulk capacitor's GND pad) is the one recorded exception to D-S8-02's "7.7 A corridors uncut":
  inside the box x 34.55–35.75, y 61.3–64.85, east of the pad and off the RAW_ACT path from Q121 to J122's RAW row, a GND
  via may cut the RAW_ACT pours (`r9_ground_aid.CORRIDOR_EXCEPT`; `r9_ground_check`'s stitch gate allows the cut inside
  that box only and reports it).
- `r9_ground_check.py` gains the `copper` gate on the aid's raster: every such pad ≤ 5 mm and every cluster ≤ 8 mm of
  copper, but the recorded exceptions (`COPPER_PAD_EXCEPT`, `COPPER_EXCEPT`, each at its measured reach + 0.1 mm; a
  stale entry fails).
- The table is regenerated by the aid from the step-7 board and frozen (`--check` reproduces it): 187 rows, 183 GND vias and 4 strap tracks (the copper stage's three: (35.6, 64.8), (32.9, 99.85), (41.4, 41.1)); `r9_ground_aid.py --check` reproduces it from a copy of the step-7 board.

**Basis.** R9P1-PLANES-01 (C121.2's return 11.98 mΩ through a 0.37 mm neck, its region 28.4 mm of copper from a via; the
reviewer's trial with two vias east of the pad: 0.89 mΩ, the RAW_ACT path unchanged), R9P1-PLANES-02 (the forward-edge
strip, 12.5 mm), R9P1-PLANES-03 (no record of the class). P9 and the cover stages judge straight lines, so a via counted
for copper it was not joined to. Measured on the fix-pass board: C121.2's return (dc_solve, C121:2 → J122's GND pins, 0.1 mm, window x 18–40, y 54–82) 1.38 mΩ, 87 % on In1 at mid-path through the copper stage's via (35.6, 64.8) (fc3d5b34 11.98 mΩ; C150's 2.58 mΩ, unchanged); C121.2's copper reach 1.50 mm (16.10) and R103.2's 3.74 mm (20.67); the worst outer GND copper 9.50 mm of copper from a via (28.41), the forward strip 6.04 mm (12.45); the 7.7 A RAW_ACT solve 0.80 mΩ, neck 7.89 mm, 12.6 °C at 0.05 mm (0.79 mΩ, 7.81 mm, 12.7 °C); six clusters of 8.05–9.50 mm and J9.2's pad (6.99 mm) stay, recorded with the layers under them (R9_VALIDATION C22); P7 stays 9, P9 3.37 mm (3.45), P10 7.32 mm.

### D-F1-08. U9's current limit is 3.96–4.84 A; RAW_PROTECTED is sized at the coordinated limits

**Decision.** The records state U9's limit with R84 = 750 Ω: 3.960 / 4.452 / 4.840 A (TI SLVSFC9C §6.5, §7.3.5.3 Eq. 7,
RILM = 3334 / ILIM); R8's "2.2 A" (R8_DECISIONS D46, M3_R8) was R5's 1.65 kΩ R84 (R6 changed R84). D-S6-05's basis
("U9's current limit (R84) through one via was R8's choice; two vias halve each barrel's share") is read as: the two
U9.6 vias share at most the downstream limiters' 3.24 A (U7 ≤ 1.24 A, SLVSE57C §7.5 at R70 1.78 kΩ; U11 ≤ 2.0 A, SLVSEA3F
§7.5 at R86 80.6 kΩ), 1.62 A each; U9's own 3.96–4.84 A is the fault case on the net itself. M3_R9 records the IPC-2152
check at those limits and accepts the 0.4 mm camera branch's soft-fault exposure (a resistive fault drawing 1.5–3.96 A
on that branch is not limited by U9 and would heat it about 100 °C by the fit, Calc) as an improbable-fault item; no
copper change.

**Basis.** R9P1-POWER-02; `battery_entry.kicad_sch` (R84 750R 0.1 %, C861551); the `r9_power.py` comment is corrected.

### D-F1-09. R9's single-via rail links are listed as accepted single points (MARGIN R15)

**Decision.** M3_R9 "Power" lists the seven rail-carrying single-via links with each barrel's load (the 3V3 feed
(37.6, 78.9), U11's battery input (39.3, 68.2), the hold-up (38.5, 69.6), the camera feed (42.15, 31.5), CAM_5V
(40.75, 45.4), U1's VDDA / VREF+ hop (22.0, 50.75), USB_LIMITED's two vias in series), as M3_R8 did. No second via is
added: the 3V3 finger is 1.49 mm wide and D-S8-02's narrow-region rule bars a second antipad there; the other two sit in
the U11 / U2 knot (Inference: no spot tried).

**Basis.** R9P1-POWER-03; MARGIN_PRESCRIPTION R15 ("no undocumented single point"); M3_R8 l. 116–131.

### D-F1-10. Records: the review's record findings

**Decision.** The records take the review's corrections (R9_VALIDATION "Review pass 1" lists each): the length's cause
(R9P1-REQUIREMENTS-01: 100 mm fails only under r9_plan's X9 ≥ 5.94 mm hard row, not under F10's 5 mm; C1 gains the
owner option of 100 mm with the four interface resistors 5.0–5.94 mm from U1); like-for-like R8 figures on every C row
(-05); the thin margins (-06, DFM-04); the stitching sides (-07, RF-02); the IGN–BUS1 adjacency in FMEA and ORDERING
(-08; D-S10-09's FMEA claim made true); the stall test's D12 framing (-09); the stale lines (-10); the coating record
(PYRO-02); the mirrored-numbering DFM query and order remark (PYRO-03, DFM-01); check_actuators' departure from owner
decision 2's wording as a part-D row (-03); the actuator gate pads' 0.15 mm to the GND pour kept as an accepted risk
(DFM-02); CC1's via step (ROUTING-03); the IMU's modal position (MECHANICAL-01); the bay stack and harness sides
(MECHANICAL-02); P2 (MECHANICAL-03); the hardware, staking and foam neighbours (MECHANICAL-04); M1's U4 clause (DFM-05);
the crystal plane's nine vias and AN2867's "distinct" clause (PLANES-04, folded in with C14).

**Basis.** The pass-1 reports; REQUIREMENTS M2 (the deviation list complete, accurate and like-for-like).

### D-F1-11. Evidence: step 10's requalification re-run on the fix-pass board, in place

**Decision.** `step10_evidence/` is regenerated on the fix-pass board by step 10's own scripts (the gate run and its
reports, the 32 DC rows, the requalification, the tab plan, the ORDERING facts, the binding note, the M2 sweep, the
reference audits, the hot-plug model, the fire loop, the tests, the records check), every file bound to the new board.
The 0.05 mm 7.7 A solves move from `step9_evidence/dc005_*.txt` to `step10_evidence/dc/dc005_*.txt` (with the fix pass's
scorecard survey) and `check_records.py` reads them there. `step9_evidence/` stays step 9's record of fc3d5b34; the
records cite step10_evidence for the current board. The fc3d5b34 figures that changed are kept, with their new values,
in R9_VALIDATION "Review pass 1".

**Basis.** D-S10-01 (requalification bound to the final board); D-S10-13 (the records check); the brief ("the scorecard
(report changes against the previous pass); DC necks; reference_audit; paste_check; the fab script").
