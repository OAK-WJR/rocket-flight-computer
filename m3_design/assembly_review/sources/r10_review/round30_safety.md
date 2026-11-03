# R10 round 30: safety lens

Target: commit `0afaed3`. Board SHA-256 `a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c`, the same
before and after. The review was read-only. Probes are in `.supervisor/r30_safety/`. The JSON
(`round30_safety.json`) holds the full evidence.

## Totals

| Critical | Major | Minor | Observations |
|---|---|---|---|
| 0 | 0 | 2 | 10 |

## Findings (real errors)

### R30-SAFETY-01 (calc, Minor): the ARM1_SENSE-to-CAM_IO_3V3 bridge figures omit the cold pull-up

**What the record says.** R10_VALIDATION §1 (line 2603) says a bridge from ARM1_SENSE to U13.5 (CAM_IO_3V3) gives
"about 1.73 V on RAW_ACT with the bus off, about 0.15 mA through the match", after which "the cold screen then reads
the bus as live".

**Where the figure comes from.** round22_safety.json derives it as 3.3 × 11.2 / (10.2 + 11.2). That divider counts only
R132 + R175 against the CONT bank.

**What it misses.** CAM_IO_3V3 exists only while the board runs. It is U13's output, fed from CAM_5V through U402,
which is enabled by PE11 with a 100 kΩ pull-down. While the board runs, 3V3 also feeds PYRO1_OUT through D120 and R131
(10 kΩ).

**Corrected values.** A nodal solve (`camio_bridge.py`) reproduces 1.7274 V / 0.1542 mA when the pull-up is left out.
With the pull-up and Vf = 0.20–0.24 V (BAT54 VF1 is at most 0.24 V at 0.1 mA), the board-on values are:
- RAW_ACT 2.19–2.21 V;
- match current 0.107–0.109 mA.

1.73 V applies only with 3V3 off, which needs a back-fed camera. The procedure forbids that.

**Impact.** None on the conclusion: the current is far below the 0.30 A no-fire, and PC5 reads 3.3 V, so the cold
screen refuses.

**Fix.** Text only. Give the board-on values and keep the off case as a parenthesis.

### R30-SAFETY-02 (doc, Minor): the 70 °C chamber test cannot pass as written

**The criterion.** The round 29 fix added "LS120 ≤ 70 °C (thermocouple on LS120)" to the first-article 70 °C chamber
test at the pad load. It appears in six places:
- REQUIREMENTS, the Temperature row;
- ORDERING 8.3;
- M3_R10 "Hot-end temperature";
- owner rows 33 and 36;
- parts_qualification.

**Why it cannot pass.** With the board dissipating 1.0–1.5 W in 70 °C air, every part soldered to the board sits above
70 °C. The same sentences put LS120 at 80–92 °C there.

**Consequences.**
- The test fails on every board, so the "until it passes" 55 °C site limit can never be lifted.
- The listed failure remedies (a camera or port duty limit, or X7R parts) do not lower LS120's rise.
- Owner row 36 accepts LS120's hot end as best-effort, which contradicts using it as a gate.

**Fix.** Drop LS120 from the pass criterion. Instead, record LS120's rise over chamber air: the buzzer stays in rating
for bay air up to 70 °C minus that rise, a measured figure that replaces the inferred 48 °C.

## Fix verification

| Item | Verdict | Basis |
|---|---|---|
| D-R29-01 (rule 3 time constant) | Confirmed | 47.78 / 53.03 / 58.28 µs. The phrase is in the binding note `c5cd0fa3…`, M3_R10, FMEA I-2 / H-2 and §1. |
| D-R29-02 (test pins) | Confirmed | The (a)–(f) phrases are pinned, the two old forms are rejected, and every phrase is present in the note. |
| R29-TRI-01 label places | Confirmed | The 9.6 V, 991 microstrain, fire currents, 34.853 ms, gate-net 3.23 V and budget lines are labelled. A fresh scan found no further unlabelled inferred-input safety figure. |
| R29-TRI-04 LS120 docs | Partly | The figures are right, but the new chamber clause is unattainable (R30-SAFETY-02). |

## Observations (not counted)

1. **BAT_ENABLE to BAT_OVLO, 0.200 mm (U9.1–U9.2), not in §1.** Fail-safe: EN sits at about 0.57 V with J400 open, and
   OVLO trips with J400 closed.
2. **ACT_GATE to BAT_IN, 0.2177 mm, not in §1.** A bridge holds the FET pair off, and rule 4 catches the lost bus.
3. **PYRO1_OUT to BUZZ_G, 0.510 mm.** Unchanged from `92c3ad59…`. The bridge current is about 10 mA at most: no fire.
4. **The U9.1–U9.5 range "1.52–1.83 MΩ".** It mixes the threshold extremes, while the RAW_ACT row uses the worst
   threshold. The convention is inconsistent but not wrong.
5. **R134 "22–29 W".** The exact range is 21.8–28.4 W; the top is a loose bound.
6. **The J440.3 chafe figure, 1.28 V.** It is correct once the 1 kΩ TX resistor is counted (1.284 V).
7. **Rule 4's probe points match the copper.** R120 and C120 sit on Q120's gate island.
8. **Rule 3's meter path.** U3.3 is QSPI_IO2, which has no pull-up, so the 0.91 kΩ path holds.
9. **Single-fault sweep with J400 open.** Nothing fires, and nothing turns the board on, outside owner rows 1, 2 and 24
   and per-flight steps 2 and 3.
10. **AGENTS §2.4 holds on the board** for Q124, Q122 and Q120 / Q121.

## Checks executed

- **Board-wide gaps.** Every §1, owner row 1 / 2 / 24 and FMEA gap figure was re-measured with pcbnew on all four layers;
  all agree to rounding.
- **D-R26 changes.** The fire-net scan was re-run on `92c3ad59…` for comparison.
- **Recomputation.** The sense, EN, ESD, gate and meter figures were recomputed.
- **Labels.** The current docs were label-scanned.
- **Firmware rules 3 and 4.** Checked against the binding note and the board.
- **Per-flight list.** ORDERING 8.3 steps 1–7 were checked against the circuit.

## Not covered

- No physical, firmware or thermal test, and no gate seeds.
- The power models (31.9 ms, the fire budget, EN timing) were checked for their labels only.
