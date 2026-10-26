#!/usr/bin/env python3
"""F7's fire loop on R9's final copper (R9_DECISIONS D-S10-04): the board's share of the CH1 fire current's loop.

usage: python3 fire_loop_r9.py DC_DIR STEP9_EVIDENCE [--out FILE]

Sums the solved copper of every board segment of the loop (tools/dc_solve.py outputs; each file's first line names the
board's SHA-256, and every file must name the same one):
  DC_DIR/fire_raw.txt   RAW_ACT  Q121's drain pins -> J124.2 (the RAW pad), 0.05 mm      (step10/run_dc_r9.sh)
  DC_DIR/fire_bus.txt   PYRO1_BUS J124.1 -> R134.2, 0.05 mm
  DC_DIR/fire_ign.txt   PYRO1_IGN R134.1 -> J121.2, 0.05 mm
  DC_DIR/fire_out.txt   PYRO1_OUT J121.1 -> Q124's drain, 0.05 mm
  DC_DIR/fire_gnd.txt   GND Q124's source pins -> J1.2, 0.1 mm, window x 0-46, y 50-102 (an upper bound)
  STEP9/dc005_bat.txt   BAT_IN J1.1 -> Q120's drain pins, 0.05 mm                        (tools/run_dc.sh)
  STEP9/dc005_fet.txt   ACT_FET_S Q120's source pins -> Q121's source pins, 0.05 mm
adds the three FETs at their data-sheet maxima at a specification point the drive exceeds, and puts the total into F7's
budget formula (REQUIREMENTS F7: 7.4 V / (0.15 ohm pack + 2 ohm R134 + 2 ohm e-match + <= 0.3 ohm leads, fuse and
arming harness) = 1.66 A against 1.5 x the 1 A all-fire current). The connectors' and the FETs' package resistances
beyond the data-sheet RDS(on) maxima are not included (Inference: tens of microohms each).
"""
import argparse
from pathlib import Path
import re
import sys

SEGMENTS = [   # (file, directory key, what)
    ('dc005_bat.txt', 'step9', 'BAT_IN J1.1 -> Q120 drain (0.05 mm)'),
    ('dc005_fet.txt', 'step9', 'ACT_FET_S Q120 source -> Q121 source (0.05 mm)'),
    ('fire_raw.txt', 'dc', 'RAW_ACT Q121 drain -> J124.2 RAW pad (0.05 mm)'),
    ('fire_bus.txt', 'dc', 'PYRO1_BUS J124.1 -> R134.2 (0.05 mm)'),
    ('fire_ign.txt', 'dc', 'PYRO1_IGN R134.1 -> J121.2 (0.05 mm)'),
    ('fire_out.txt', 'dc', 'PYRO1_OUT J121.1 -> Q124 drain (0.05 mm)'),
    ('fire_gnd.txt', 'dc', 'GND Q124 source -> J1.2 (0.1 mm, window x 0-46, y 50-102: upper bound)'),
]
# data-sheet maxima (AOS data sheets as read in docs/CIRCUIT_REVIEW.md and docs/MARGIN_PRESCRIPTION.md)
FETS = [
    ('Q120 AON6403', 4.3, 'RDS(on) max at Vgs -4.5 V; the gate sees -6.73 V at 7.4 V (CIRCUIT_REVIEW, gate divider)'),
    ('Q121 AON6403', 4.3, 'same'),
    ('Q124 AON7524', 5.8, 'RDS(on) max at Vgs 2.5 V; the gate sees >= 2.77 V at the guaranteed corner '
                          '(MARGIN_PRESCRIPTION, the pyro gate drive row and the AON7524 paragraph)'),
]
V_FLOOR, R_PACK, R_PULSE, R_MATCH, R_HARNESS = 7.4, 0.15, 2.0, 2.0, 0.3     # REQUIREMENTS F7
ALL_FIRE, MARGIN = 1.0, 1.5


def read(path):
    text = path.read_text()
    first = text.splitlines()[0]
    sha = re.search(r'sha256 ([0-9a-f]{64})', first)
    r = re.search(r'R = ([0-9.]+) mOhm', text)
    if not sha or not r:
        sys.exit(f'{path}: no board SHA-256 on the first line or no "R = ... mOhm" line')
    return sha.group(1), float(r.group(1))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('dc', type=Path)
    ap.add_argument('step9', type=Path)
    ap.add_argument('--out', type=Path)
    a = ap.parse_args()
    dirs = {'dc': a.dc, 'step9': a.step9}
    rows, shas = [], set()
    for name, key, what in SEGMENTS:
        sha, r = read(dirs[key] / name)
        shas.add(sha)
        rows.append((name, what, r))
    if len(shas) != 1:
        sys.exit(f'the solves name {len(shas)} different boards: {sorted(shas)}')
    sha = shas.pop()
    copper = sum(r for _, _, r in rows)
    fets = sum(r for _, r, _ in FETS)
    board = copper + fets
    base = R_PACK + R_PULSE + R_MATCH + R_HARNESS
    i_budget = V_FLOOR / base
    i_board = V_FLOOR / (base + board / 1000.0)
    out = [f'# m3_design/assembly_review/m3.kicad_pcb sha256 {sha} (step10/fire_loop_r9.py; R9_DECISIONS D-S10-04)',
           'F7 fire loop, board share (each solve bound to the board above):']
    out += [f'  {r:7.2f} mOhm  {what}  [{name}]' for name, what, r in rows]
    out.append(f'  {copper:7.2f} mOhm  board copper, sum of the seven segments')
    out += [f'  {r:7.2f} mOhm  {ref}: {why}' for ref, r, why in FETS]
    out.append(f'  {fets:7.2f} mOhm  the three FETs at their data-sheet maxima')
    out.append(f'  {board:7.2f} mOhm  board total (copper + FETs)')
    out.append(f'F7 budget without the board: {V_FLOOR} V / {base:.2f} ohm = {i_budget:.3f} A')
    out.append(f'F7 budget with the board:    {V_FLOOR} V / ({base:.2f} + {board / 1000.0:.4f}) ohm = {i_board:.3f} A')
    ok = i_board >= MARGIN * ALL_FIRE
    out.append(f'against {MARGIN} x {ALL_FIRE} A all-fire = {MARGIN * ALL_FIRE:.2f} A: '
               f'{"met" if ok else "NOT MET"} ({i_board / ALL_FIRE:.2f} x all-fire)')
    text = '\n'.join(out) + '\n'
    if a.out:
        a.out.write_text(text)
    print(text, end='')
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
