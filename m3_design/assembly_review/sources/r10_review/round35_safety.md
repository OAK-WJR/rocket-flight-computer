# R10 round 35: safety lens

Target: commit `c3c4249`, board `a0ec075e…` (SHA-256 identical before and after the review).

**Totals: 0 Critical / 0 Major / 0 Minor real errors.**

## What I checked
- **AGENTS §2 on the board as built.**
  - §2.4: the gate networks of Q124, Q122 and Q120 / Q121, checked from the pcbnew pad nets.
  - §2.2: the RAW_ACT feed (ruled before).
  - §2.3 and §2.1: the firmware rules, as text.
  - §2.5: the labels on the rule 3 / 4 figures, the §1 table and owner rows 1 / 2.
- **Fire-chain adjacencies.** My own scan of all four layers, fills included. It covers every foreign item within 0.6 mm
  of the pyro, arming, gate, sense and EN nets, and within 1.2 mm of the gate nets, PYRO1_OUT and the EN chain.
  - Every figure in §1, owner row 1 and owner row 2 reproduces.
  - Five key pairs were confirmed by KiCad's own collision test, for example R81.1 to its GND via 0.1732 mm and R173.1
    to R162.1 0.7935 mm.
- **Rules 3 and 4.** The text is consistent across the binding note, M3_R10, ORDERING 8.3 and FMEA I-2 / H-2. I
  recomputed the figures: 0.91 kΩ, 3.23 V, 47–58 µs, the cold CONT readings 0.099 / 0.146 / 0.295 V, and the unclamped
  ESD figure 7.5 V.
- **Whole-board single faults.**
  - Bus energised with J400 open: disclosed under owner row 2 and screened by per-flight step 2.
  - Fire with the bus disabled: none found.
  - Board on with J400 open: the EN leak thresholds and harness cases reproduce (1.52–1.83, 0.58, 1.69–1.96 and
    0.29 MΩ; 2.88 / 1.87 / 1.28 V).
- **Per-flight steps 2–4.** All three can be carried out on the intact circuit.

## Findings
None.

## Observations (not counted)
11, in the JSON. Each is a reproduction of a recorded figure or a class already ruled:
- rule 4's 0.93–1.01× envelope;
- Q124's gate-to-drain gap, 0.520 mm;
- the ACT_EN_MCU run to BUZZ_OUT, 0.520 mm;
- U9's EN to OVLO, 0.200 mm;
- the AGENTS 1.279 A label.

## Fix verification
- R34-TRI-01 (the hot-plug results pointer): confirmed. The JSON bindings and the figures match the new pointers.
