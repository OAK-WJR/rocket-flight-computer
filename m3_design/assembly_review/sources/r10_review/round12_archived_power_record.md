# Archived power prose from commit d57b216

This is the Power section as found in docs/M3_R10.md at the round12 target.
It mixes earlier circuit/layout snapshots and is preserved as historical prose,
not current coordinate, copper, transient or physical evidence. The corrected
active M3_R10 section and board-bound parts_qualification/budget supersede it.

## Power (`m3_design/r10_route_power.py`, D-R2-03, -05, -06, -11, -12)

- **Current circuit overrides:** GPS/radio connect directly to PORT_4V8 and their
  3.3 V MCU UARTs through 1 kΩ / ESD; U410 / U420 / U411 / U421 and their controls
  and obsolete local parts are removed. Camera U402 / U12 / U13 remain. C92 is CL10A475KO8NNNC / C19666, 4.7 µF / 16 V X5R 0603; estimated effective
  capacitance is 2.211 µF with the recorded bias/tolerance/temperature/aging allowances (Inference), above TPS709's
  1.5 µF requirement. Camera OE must be low when its port is off. Camera U13 stays because
  the camera rail's upper corner exceeds TXU0202's 5.5 V recommended supply limit.
- **Compact pyro cell (AUD-3 / -6 / -7):** Q120 / Q121 are AONR21357 / C431196, B(13.5, 72.6) / B(13.5, 67.6),
  rotations 0° / 180°, with the maker DFN3x3A_8L_EP1 land. C120 is 1 µF / 25 V X7R (C29936), B(17.1, 71.525) on its incumbent metric 0603 land, correcting the old
  16 V part's clamp-event overstress. Fire-only tracks are 0.5 mm: RAW_ACT 6.500 mm, IGN 4.850 mm and OUT
  7.954478 mm; their total 19.304478 mm plus the battery branch and conservative source bridge gives 30.1231 mΩ
  at 70 °C (Calc / Inference). Normal 20 ms pulses give about 5.6 K adiabatic rise from room temperature, about
  7 K at the hot low-R134 corner; the separate 36 ms watchdog-fault guard gives about 10.1 / 13 K (Inference,
  no plane credit). Continuous battery / U9 feed width is unchanged. R150–R153 are 1 kΩ / 100 mW 0603; the
  conservative 8.4 V chafe case is 72 mW through 70 °C, not a 30%-rating claim.
- **U9 output cell (GAP-2):** C82 B(39.8, 74.75), D9 B(43.35, 73.45); R92 now F(35.25, 57) to clear the larger terminals/damper. Historical saved-copper
  OUT + GND path totals are C82 12.568808 mm / projected area 2.3153 mm², D9 16.691778 mm / 17.4197 mm².
  The return model includes full-board-thickness via penalties where used. These geometry regression bounds
  implement TI's qualitative short-loop guidance; they do not measure inductance or transient performance.
- **U401 thermal land (GAP-3):** exactly two GND vias, 0.5 mm pad / 0.3 mm drill, at (27.3, 13.6) and
  (27.9, 13.6), inside U401.11. Maker paste windows are unchanged. Resin-filled, copper-capped, planar VIPPO
  manufacture is mandatory; CAD filling flags are not process proof. C84 is fitted manually after both reflow
  passes under a separately validated process (GAP-4), and remains required in BOM / CPL.
- **Battery (owner-answer routing, D-OA-06 / -07):** J1.1 → BAT_IN on F.Cu (1.0 mm) past D8 to the input-protection
  column C95 / C89 / C96 / C80. U9 takes its feed from that column through one 1.0 / 0.5 mm via now at (36, 84),
  then B.Cu along y 86.6 into C88's input pad before U9's IN bar. The 0.7 mm C88 entries are 0.80 / 1.15 / 0.97 mm;
  U9 retains its 0.3 mm, 0.6 mm external pad neck (D-R3-03). Q120 keeps a separate J1 feed for the pyro load switch;
  its former long branch now ends at R80. R166 is 0.36 Ω on its existing 2512 land; R92 is 3.3 kΩ on its existing
  0603 land. R167 bleeds BAT_IN; R80 / R165 / J400 form the external-switch loop (≈ 7 µA, 470 kΩ each side).
  The circuit pass moves R166 to F(35.25, 64), R82 to B(36.825, 81.9), rotation 0,
  and the switch-loop passives clear J400/J122. Fresh actual-feed extraction and
  numerical results belong to the final circuit-pass board; old transient maxima below are historical.
- **No battery-lead fuse (OQ-6, revised 2026-10-28, `f202ec3`):** the owner superseded the earlier ≤ 10 A proposal.
  A hard short in the pack-to-U9 / Q120 stretch (lead, J1, BAT_IN copper, D8, C80 / C96 / C89 / C95) is not
  current-limited; this residual risk is accepted with strain relief, no chafe points and crimped or soldered leads.
  U9 limits its downstream load to 3.96–4.84 A and R134 limits a shorted igniter to about 4.2 A for ≤ 20 ms, but
  neither protects that stretch. The battery-fuse legend is removed. The later single-switch decision also removes J124 and its 5 A fused ARM link; current R10 has neither fuse.
- **Hot-plug (OQ-2, simulation / Inference):** `m3_design/assembly_review/sources/r10_design/hotplug.md` records the schema-3 model,
  maker capacitor C(V) curves and board-derived R/L graph. The old split feed on `407d1d84…` failed; the revised
  feed reaches C88 before U9. Every local path remains in the model, including C88 → U9 (3.92 mm centreline,
  4.436898 mΩ, 1.176695–2.424048 nH). The topology gate removes C88's node and requires U9 to disconnect from
  every other modeled terminal. The round-9 fix sweep bound to `b337fe63…` (electrical signature `c424a714…`) passes all
  **2304 required cases**: U9 IN minimum **−14.497873371 V**, maximum +2 V (initial state), maximum falling slew
  **8.525257186 V/µs**, rising 4.523495972 V/µs; half-step checks, the cold retained-OUT limit and all 60 local-path
  sensitivities pass. The gate re-extracts the board and checks the complete inputs, model sources and topology.
  The required unfused harness has 0.1–2 µH and measured resistance **≥ 0.03 Ω**; the 0 / 0.01 Ω sensitivity
  cases fail and are outside qualification. Typical capacitor curves, family matching, ideal common ground,
  package ESL/ESR, estimated trace inductance, assumed pin capacitance/contact edges and C84's unpublished
  temperature behavior remain limitations. Scope U9 IN and OUT together, measure the installed harness and
  qualify repeated hot/cold insertions; no physical transient or flight guarantee follows from the simulation.
- **R92 / R166 (D-OA-05 … -07):** R92 is 3.3 kΩ, 1%, UNI-ROYAL 0603WAF3301T5E / C22978 on the same 0603 land.
  The retained-output calculation places all inventoried capacitance on one 8.5 V node, doubles C84 and allows
  +20% tolerance / +15% temperature on the rest: 1586.1915136 µF discharged only through R92 at 3354.6645 Ω
  gives 5.836941131 V after two seconds (Inference, not a measured discharge bound). R166 is 0.36 Ω, 1%,
  UNI-ROYAL 25121WF360LT4E / C168925 on the same 2512 land; the 0.33 Ω candidate failed a cold/tolerance corner.
  Required model cases give about 504.3 W peak and 2.8885 mJ over 150 µs in different corners. The maker's
  continuous rating and five-second overload test do not establish microsecond pulse durability; maker approval
  or repeated hot/cold pulse testing with resistance-drift checks remains open.
- **Logic:** U9 (TPS25947 eFuse) → RAW_PROTECTED (1.0 mm run, four vias to In2, D-R3-03) → U11 (logic / USB mux) → VLOGIC (C84 hold-up) → U2 3V3 buck (L1). The
  VLOGIC divider R60 / R61 / C60 feeds VLOGIC_SENSE on PA6 (ADC12_INP3) for F6's analog-watchdog load shedding.
  **OQ-5 selects C84 plus firmware shedding; no hardware port-buck cutoff is added.** With SD writing and all
  ports on, the current allocation predicts **0.490–0.571 ms** at reduced 300.8 µF to 3.8 V;
  camera off, GPS/radio on, logic shed and SD idle gives **1.533–1.655 ms** under the same capacitance/endpoint
  assumptions (Calc / Inference). GPS/radio cannot be shed. The longer historical "ports off" cases require
  their physical absence. TPS2553 turn-off can take 3 ms, so no calculation proves that firmware sheds the camera
  before brownout. The PA6 watchdog threshold and worst-case
  latency through interrupt handling, OE removal and actual port-load removal remain firmware and bench obligations;
  flight state, IMU, barometer and safety timing must be retained.
- **Ports:** RAW_PROTECTED → U400 (AP63201, L400 6.8 µH, feedback R400 / R404 / R401) → PORT_5V3 → U402 → CAM_5V (J9.1);
  PORT_5V3 → U401 (TPS7A9101, R402 / R403, C408 NR/SS, R405 820 Ω bleed) → PORT_4V8 directly to J410.1 / J420.1.
  Camera U402 retains its 100 kΩ EN pull-down, 22.6 kΩ ILIM resistor and FAULT pull-up. A GPS/radio cable short may
  collapse both always-on ports or make U400 hiccup; there is no independent port fault flag or software cycling.
  Set points, shared-fault bounds and tolerance budgets: `parts_qualification.md` / `parts_budget.json`
  (calculations, not measurements).
- **Round-5 power records (R5-PWR-01 … -04; `parts_qualification.md` "Round-5 power and pin records"):** (1) U9's OVLO pin (U9.2, divider R82 2 MΩ / R83 280 kΩ, ratio 0.1228) leaves the maker's recommended 0.5–1.5 V range above an input of about 12.2 V (1.5 V / 0.1228) and reaches about 2.4 V at the 19.9 V clamp, still below the 6.5 V absolute maximum (reached at 52.9 V) (Calc; the range and limit are the reviewer's reading of the TPS259470L datasheet, not re-read here): above 12.2 V the part is in the OVLO fault state it exists to detect, so the out-of-range pin is a fault-state condition, recorded and accepted as such (Inference). (2) Before AUD-5 removed TP89, it sat on U9's ILM pin (net BAT_ILIM), an analog monitor with "do not leave floating" in the maker's text: bench probing is high-impedance only, never loaded or shorted (ORDERING §8 bench gates). (3) The AP63201's quiescent current is 258 µA per the Diodes datasheet (DS41326); LCSC's 22 µA is the AP63200 / 63203 / 63205 figure. No idle figure in this record used 22 µA; the all-ports-shorted budget already carries 11 mA of quiescent, divider and bleeder load, of which the buck's 0.258 mA is a small part (Calc). (4) The AP63201's loaded dropout is typical-only: ORDERING §8 gains a bench step with the port rails at a 6.0 V loaded battery. **F6 bounce figure:** U9's EN network is R9's (C87 2.2 µF, R80 / R165 470 kΩ, R81 300 kΩ, 227 kΩ recharge; compared on the netlists), so REQUIREMENTS F6's ≥ 0.15 s (0.21 s at 7.4 V) carries over; the switch now goes through J400 (DB125-2).
- **Historical In2 regions** (D-R2-05 / D-R2-06, re-cut in round 3, D-R3-04; current boundaries are explicit in the generator and requalified by K-reference): RAW_PROTECTED wraps the board (forward area, east
  strip x > 40, the aft band to the buck input, ending at y 4.4 east of x 24.2); PORT_5V3 a column x 35.2–39.7 (to
  y 42.5, narrowest 2.4 mm) plus the buck-output band y 4.7–6.8 aft of U410 (narrowest point 1.20 mm at x about 30.25, a via clearance notch; round-6 measurement, not re-measured here; the earlier 1.49 mm figure is superseded) and a western extension
  under the camera switch's control runs; PORT_4V8 U410's cell and the LDO block (x 28.3–33.6, y 7.1–29); 3V3 the rest,
  with a forward finger for the 3V3 buck output; GND under the CH1 pyro column (D-R3-02) and under the crystal
  (`R10_GND_In2_Y1`, R9's D-S8-20 restored, D-R3-06). In1 is solid GND; F.Cu and
  B.Cu carry GND pours. Every rail pad reaches its plane by its own via (the frozen fan-out table
  `m3_design/r10_fanout.tsv`, with recorded hand edits) or a hand join; vias keep pads only on the layers they connect
  (D-R2-10). In2 carries no tracks (RADIO_4V8 on B.Cu since D-R3-04). 37 GND stitching vias (D-R3-08).
- **Historical pre-AUD IPC-2152 estimate** (`tools/ipc2152.py`, no plane credit; D-R3-03; current fire paths / output loop superseded above): BAT_IN and U9's RAW_PROTECTED 1.0 mm runs
  7.4 / 19.2 °C at 1.8 / 2.9 A (design load / all port shorts: the port buck draws 1.1–1.6 A at 8.4–6.0 V with
  the ports at their allocations, `parts_budget.json `, an **Inference** at 80–85 % efficiency); fire loop at 4.2 A / 20 ms
  (adiabatic) 1.4 °C on the 1.0 mm runs, 9 °C on the 0.4 mm ACT_FET_S bridge, 16 °C on Q124's 0.3 mm source bar; the
  In2 PORT_5V3 band at its narrowest point (1.20 mm) 3.4 / 8.5 °C at 1.25 / 2.02 A (`tools/ipc2152.py` internal fit, re-computed in round 6; the earlier 2.7 / 6.7 °C were the same fit for 1.49 mm). No DC solve was run on tracks or vias (open item).
  **Historical short necks (R4-PWR-01; copper facts measured on `579575bd…`, before the owner-answer BAT_IN feed change):** U9's IN and OUT pads (5, 6) are 0.3 × 2.4 mm, so the B.Cu entries are 0.3 mm wide and run 0.6 mm beyond each
  pad edge: (38.75, 81.4) → (38.75, 79.6) BAT_IN and (39.25, 79.6) → (39.25, 77.8) RAW_PROTECTED, then the 1.0 mm runs;
  RAW_PROTECTED then reaches In2 through a 0.4 mm B.Cu via ladder, vias at x 40.3, 41.0, 41.7 and 42.4, y 76.725; U400's
  0.4 mm RAW_PROTECTED F.Cu input feeds end in the vias (14.1, 9.0) and (14.1, 7.6). These are pad-pitch-limited short
  necks. The IPC-2152 figure for a 0.3 mm track at 2.9 A (76.8 °C) is an infinitely-long-track figure and does not
  apply to a sub-millimetre neck whose ends are held by a pad and a plane (Inference); the bench thermal check (ORDERING
  §5, the full port load with a thermal camera) covers them, and no calculation here bounds their temperature.
  **Owner-answer C88 entry:** the new 0.7 mm necks total 2.92 mm, followed by the existing external 0.3 mm / 0.6 mm
  U9 entry. At 4.84 A and 85 °C, a one-dimensional rod calculation with both ends held at the same temperature
  gives 3.806184 mΩ, 89.16 mW and 5.10 °C rise above those ends (Inference; `hotplug.md`, D-OA-07), not the
  board's absolute temperature. This replaces the old BAT_IN approach; the OUT ladder and U400 copper are unchanged.
  **Plane-only DC solve (reviewer's, R4-PWR-02; Inference, not run in this repository):** In2 RAW_PROTECTED alone, 2.9 A
  in at U9's vias, 2.4 A out at U400's and 0.5 A at U11's: 36 mV drop, the narrowest cut 3.6 mm at y ≈ 35.2–35.8. It
  covers the plane only; "DC solve not run" still holds for tracks and vias.

