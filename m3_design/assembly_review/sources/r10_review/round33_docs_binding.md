# Round 33 — docs_binding lens (Claude)

Target commit `feed21f`, PCB `a0ec075e…` (SHA-256 identical before and after). Binding note `c5cd0fa3…`, budget `4267634…`.

**Totals (real errors): 0 Critical / 0 Major / 1 Minor.**

## Findings

### R33-DOCS_BINDING-01 (doc, Minor): U9 pad exposure stated as 0.10 mm
- **Statement:** `docs/ORDERING.md` line 552 (8.3 probe worksheet, U9 IN / OUT row): "U9's pads 5 and 6 expose only 0.10 × 0.30 mm beyond the body at each end".
- **Contradicts:** TI SLVSFC9C RPW0010A outline (body 1.9–2.1 mm, 2 × 2 mm nominal; https://www.ti.com/lit/ds/symlink/tps25947.pdf) and the board's U9 B.Fab body.
- **Evidence:** pcbnew on `a0ec075e…`: pads 5 / 6 y 80.40–82.80; B.Fab body rect y 80.55–82.65 (2.10 mm, the datasheet maximum, line width 0.10 mm). Exposure is 0.15 mm at the maximum body, 0.20 mm nominal, 0.25 mm minimum. The 0.10 mm figure came from round 23 reading the fab line's outer edge (17.40–19.60); the same 2.10 mm rect is on the round 18 and round 24 boards.
- **Impact:** a wrong procedure fact (conservative); the probe point B(18.25,80.45) is still on exposed copper.
- **Fix:** "expose 0.15–0.25 mm (0.20 mm nominal; RPW0010A body 1.9–2.1 mm) × 0.30 mm beyond the body at each end".

## Fix verification (round 32)
- R32-TRI-01 (R166-to-C84 0.65 / 0.60 mm): confirmed by pcbnew courtyards (R166 y from 84.40, C84 to 83.75).
- R32-TRI-02 (C84 heat-limit summary): confirmed against ORDERING 8.2.
- R32-TRI-03 (85 °C lists): confirmed; the 16 X5R designators equal the BOM's X5R lines exactly.

## Checks executed
Links and anchors (0 broken); binding-note hashes (board, netlist, pin table, circuit) and all 100 U1 pins against pin_table and the board's pad nets; board metrics (bytes, footprints, segments, vias, track length, references, legends); every F/B coordinate in the docs against the 216 footprints; terminal pins and legend faces; five supports; key net clearances (1.040 / 1.0585 / 0.7935 mm); ORDERING 8.3 probe pads; cost and stock figures; decision counts (229).

## Observations (6, not counted)
ORDERING's "pad 9 itself is under the body" (its outer 0.15–0.25 mm is exposed; the instruction stays right); R10_VALIDATION (d′) R173 B(16.87,59.70) is inside the labelled round 18 record; other coordinate mismatches are in labelled history; the 5.71 V "four-stall" point is defined as including the fire current; the 7 µA and 5.7 mV J400 figures and the 88 / 56 / 45 ms turn-on reproduce.

## Coverage limits
Not every prose figure in R10_VALIDATION / FMEA was re-derived; the electrical models were spot-checked only at nominal turn-on; part temperature ratings are left to the parts lens.
