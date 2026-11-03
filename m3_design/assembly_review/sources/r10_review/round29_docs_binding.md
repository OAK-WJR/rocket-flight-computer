# R10 round 29: docs_binding lens

Target commit `09a564e`, board `a0ec075e…` (SHA-256 before and after:
`a0ec075ed3697a738d2fb9391e66e54a196d95bc6335d9d00fbe217a1a2e733c`). Read-only; probes in `.supervisor/r29_docs_binding/`.
Budget `4267634…` and binding note `30796f5e…` hash as recorded.

## Totals

| Critical | Major | Minor |
|---|---|---|
| 0 | 0 | 0 |

No false statement and no broken link or anchor was found in the in-scope current-board text.

## What was checked

- **Coordinates.** Every F(x,y) / B(x,y) part pose stated as current in STATUS, AGENTS, M3_R10, ORDERING, the handoff,
  R10_VALIDATION, FMEA, REQUIREMENTS, parts_qualification and AVA_LAYOUT matches the board within 0.05 mm. The
  scanner's mismatches are all labelled history (round 18–26 before/after tables) or list-parse artefacts.
- **Pin map.** `pin_table.tsv` `r10_net` matches all 100 U1 pad nets; the binding note's pins, IMU pose, EXTI lines and
  obligations' part facts (R431, R102, R460–R464, R9/R110, R104/R105, R60/R61, R10–R13, U5 PS/CSB, NC pins) match the netlist.
- **Board metrics.** 2,369,507 bytes, 216 footprints, 1059 segments, 309 vias (170 GND; 304 / 4 / 1), 1866.794 mm,
  123 visible / 93 hidden references, 44 legends: as stated.
- **Fab package.** CPL 206 (70 / 136), BOM 81 lines and 206 designators, C535146 × 9, 45 Extended / 36 Basic,
  paste 249 / 381, manifest bound to `a0ec075e…` with all six outputs hash-matching; C10 / C11 / R164 / R173 CPL rows at
  the D-R26 poses.
- **Cost and stock.** $85.26, $60.47 / $24.79, $61.01 with minimums, U9 30 / −81, U4 9 / 2, timestamps and input hashes
  match `cost_check.json` / `stock_check.json`.
- **Spacings.** 24 stated net-pair minima reproduce (non-zone copper): PYRO1_OUT to 3V3 / 3V3A 1.0501 / 1.0400 mm,
  gate nets to 3V3 1.0651 / 1.0587 mm, BUZZ_DRV–PYRO1_OUT 0.794 mm, OUT–GND 0.177 / 0.180 mm, CONT_MID 0.250 / 0.175 mm,
  EN-node 0.200 / 0.330 mm, R164's via 0.2335 / 0.206 / 0.997 mm.
- **Other geometry.** The (4,44.3) support lands, the C84 heat-limit joint list, the ESD clamp distances, the seven
  0.4 mm ACT_FET_S bridges and U400 / L400 to U401 (13.39 / 8.74 mm).
- **Links.** 174 relative links and anchors resolve, backticked paths resolve, and the quoted section names exist.
- **Arithmetic.** Hold-up from the PA6 trip, USB attach charge, the C84 capacitance window, divider ratios, the PB1
  fault current, the U401 θ ceiling and the decision counts (227 / 101).

## Fix verification (round 28, this lens)

| Item | Verdict |
|---|---|
| R28-TRI-01 FMEA divider wording | confirmed (netlist: two 5.1 kΩ tops, two 2 kΩ bottoms, no R168 / R170 / R172) |
| R28-TRI-02 13.064091 W | confirmed |
| R28-TRI-03 docs 5.881 / 4.388 V | confirmed (budget 5.880831 / 4.388491 V) |
| R28-TRI-04 PORT_4V8 capacitors | confirmed (eight on the net) |
| R28-TRI-05 / -09 rule 3 criterion and Inference label | confirmed in binding note, M3_R10, FMEA, ORDERING; 0.91 kΩ from board values |
| R28-TRI-06 PB1 TT_u | confirmed |
| R28-TRI-07 F4 64–84 % | confirmed (text; hinge script not re-run) |
| R28-TRI-08 525 s | confirmed (only the labelled superseded estimate remains) |
| Rule 4 Q120 criterion, gate barrels | confirmed |
| "Tens of ms" port lead, DS15034 Table 2 p11 | confirmed |
| AUX clamp distances, USB 516.1 µF / 2.426 mC, U400 / L400 8.7–13.4 mm | confirmed |
| Audit B samples (C84 pass value, ESD dummy load, step 4 no-USB) | confirmed |

## Observations

There are 17 observations, none counted; they are listed in the JSON. Among them:
- the session context's AGENTS copy is stale ($85.60), while the committed file is right;
- BAT_ENABLE to ACT_EN_MCU / RAW_ACT measures 0.5200 / 0.5002 mm here against the stated 0.5205 / 0.5008 mm, a method
  difference already ruled in round 28;
- R10_VALIDATION's R19-RTE-04 history gives R101's via coordinate, not the part's.

## Coverage limits

- Long historical sections were only scanned mechanically.
- Zone copper was excluded from the distance probe.
- No gate, model or datasheet re-read was done.
