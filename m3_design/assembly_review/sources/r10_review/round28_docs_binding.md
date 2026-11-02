# Round 28 docs_binding review

Target commit `19dd0b5`; board SHA-256 `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c` before and after (2,369,507 bytes). Reviewer: claude.

**Totals: 0 Critical / 0 Major / 0 Minor.** No false current-board statement, broken link or broken anchor found.

## Findings
None.

## Fix verification
- **D-R27-01**: parts_budget.json (SHA-256 ecc45417..., matches parts_qualification.md) pack_7V4_four_stall_loaded_V 5.881013615, pack_6V0_four_stall_loaded_V 4.388744837; STATUS / parts_qualification quote 5.881 / 4.389 V. Verdict: confirmed.
- **D-R27-02**: r10_binding_note.json sources.mcu_revision names the two Rev 11 Table 109 exceptions (6.0 V FT cap, 4.0 V ADC-mode maximum); the obligations text labels both as Rev 11 / Inference. Verdict: confirmed.
- **D-R27-03**: telemetry.kicad_sch carries 4 M3:PortTerminal occurrences (definition + J410 / J420 / J440); J9 unchanged; board pads J410/J420/J440 pins 1-4 = PORT_4V8 / GND / *_TX_WIRE / *_RX_WIRE. Verdict: confirmed.
- **D-R27 docs (In2 3V3 fill)**: In2 3V3 zone fill 1430.05 mm2, one outline (pcbnew on a copy). Verdict: confirmed.
- **D-R27 docs (J440 lead direction)**: J440 pads y 11.0-21.5, courtyard to y 23.695; handoff 'aft of y 23.5 (y < 23.5)' with y=0 aft. Verdict: confirmed.
- **D-R26-01**: GND vias 0.5/0.3 mm at (7.4,16.5) and (7.4,20.0); pins 3/4 of J410/J420/J440/J9 unconnected-layer mode 3 (no inner rings); pins 1/2 keep rings. Verdict: confirmed.
- **D-R26-02 / -04**: PYRO1_OUT-3V3 min 1.050 F.Cu / 1.0511 B.Cu (R173.1-D120.3) / 1.065 In2 fill; PYRO1_OUT-3V3A 1.040 B.Cu; PYRO1_GATE_N-3V3 1.065 (R127.1); PYRO1_GATE-3V3 1.0585 (R128.1); PYRO1_GATE-3V3A 1.145; PYRO1_OUT-BUZZ_DRV 0.7935 (R173.1-R162.1); PYRO1_OUT-GND 0.1768 B.Cu / 0.180 F.Cu; C10 B(17.5,53.5), C11 B(17.5,51.45), R164 B(17.325,55.25), R173 B(16.87,59.05); vias (19.55,55.825) 3V3, (9.2,52.55) 3V3, (19.423,52.373) / (19.65,53.45) GND; straps and CONT_MID path as recorded in AVA_LAYOUT. Verdict: confirmed.
- **D-R26-03**: budget four-stall BAT_IN 5.7132 V (fire_current_GAP1 pack_7V4 stall 4); docs quote 5.71 V / 5.713 V consistently in AGENTS, STATUS, M3_R10, handoff. Verdict: confirmed.

## Checks executed
- Board SHA-256 before/after = a0ec075e... (shasum); file size 2,369,507 bytes
- Full-hash grep across the 12 files; every current-board full hash equals the board; binding note netlist (535a8fdf...), pin_table (b94133e6...) and circuit (3220e5f9...) hashes recomputed and equal
- parts_budget.json SHA-256 ecc45417... equals parts_qualification.md; fire-path lengths, loop 4.617803 ohm, 0-4 stall currents, copper mOhm match
- Markdown link and anchor checker (GitHub slug rules) over STATUS, AGENTS, M3_R10, ORDERING, HANDOFF, VALIDATION, FMEA, REQUIREMENTS, parts_qualification, AVA_LAYOUT: 0 missing files, 0 missing anchors; backtick path references resolved (only two .supervisor-local artefacts unresolved by tracked path)
- pcbnew read-only dump on a copy: 216 footprints, 1059 segments, 0 arcs, 309 vias (170 GND; 304 x 0.5/0.3, 4 x 0.6/0.3, 1 x 1.0/0.5), 1866.794 mm track, 123 visible / 93 hidden refs, 44 silkscreen legends; positions/sides/rotations/values of ~60 parts cited in AGENTS, ORDERING, HANDOFF, M3_R10
- Terminal pad nets for J1, J400, J121, J410, J420, J440, J9, J122 against the handoff terminal table; port UART chain (1 k resistors to PD8/PD9, PB13/PB12, PC6/PC7) and camera reversal
- Pin map: all 100 U1 pads vs pin_table r10_net (0 mismatches); binding note u1_pins vs pin_table (0 mismatches)
- Silkscreen legend side check against the handoff list of bottom legends
- Net-pair shape-distance probe (pcbnew SHAPE.Collide bisection, zones 5 um step) for PYRO1_OUT, gate nets, BAT_ENABLE, ARM1_SENSE, RAW_ACT, PYRO1_CONT_MID, PORT_4V8, CAM_5V pairs quoted in AGENTS / M3_R10 / FMEA / VALIDATION
- Zone fill areas (In2 3V3 1430.05 mm2)
- Fab package: manifest output hashes equal files; BOM 81 lines; CPL 206 (70/136); cost_check total 85.26, parts 60.47, 12:44:13Z, 45 Extended; stock_check 12:43:17Z, U4 9/2, U9 30/-81/min 7, C2757925 35895/35052, C535146 196/189; min-purchase 61.01+24.79=85.80; fixed 83.96/5=16.79; price-movement diff vs 01:43:55Z run: 8 lines, -0.3374
- hotplug_results.json: 2304 rows, 0 failures, min -14.807 V, fall 8.995 V/us, rise 5.088 V/us, shared 1643.90 uF, bound 5.914 V
- Round 24-27 triage totals and round 27 lens totals vs STATUS / VALIDATION counts

## Observations (not counted)
- AGENTS.md row and status text in the session-start context (2026-11-01, 92c3ad59..., $85.60) differ from the committed AGENTS.md (2026-11-02, a0ec075e..., $85.26); the committed file is correct; the context copy was stale, not the repository.
- docs/R10_VALIDATION.md cites `adjacency_a3144b15.json` and `detour.py` by bare name; both exist only under .supervisor/ probe directories (r19_safety, r2x_routing), which are local review artefacts, not tracked evidence links; not a broken markdown link.
- FMEA I-5 row quotes 'the unconnected In2 rings of J440.1 and J9.1, 0.2505 mm from 3V3': J440.1 / J9.1 still keep unconnected inner rings (pad mode 0) and PORT_4V8 / CAM_5V reach the In2 3V3 fill at 0.250-0.255 mm (5 um search step), consistent.
- ORDERING section 8 says 'x=0 west, y=0 aft, y=90 forward' in KiCad millimetres; consistent with the handoff's forward edge y > 90 and J440 lead rule (aft of y 23.5).
- binding note's '297 kOhm x 0.72 x 220 nF' EN timing text is a power-lens calculation; not re-derived here.
- STATUS test counts (R10 268, route 72, check_r10 37 / 37) were not re-run (read-only brief forbids full check.sh on the canonical tree).

## Coverage limits
- R10_VALIDATION.md (3200 lines) and M3_R10.md were checked on current-state sections, hashes, links and the quoted numbers listed; sealed historical round sections were not re-verified line by line
- Electrical calculations (EN timing, chatter, hold-up, U401 thermal) checked only for cross-document consistency and against the budget JSON, not re-derived
- Test counts and check_r10 rule counts not re-run (read-only brief)
- Zone-distance figures carry a 5 um search step

Probe scripts: `.supervisor/r28_docs_binding/` (links.py, dump.py, stats.py, pair.py, silk.py, tr.py, zones.py).
