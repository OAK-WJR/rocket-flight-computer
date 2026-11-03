#!/usr/bin/env python3
"""R9 firmware board-binding note (AGENTS.md section 3): the facts a future m3_firmware binding for R9 must carry.

usage: <KiCad python3> -I binding_note_r9.py BOARD.kicad_pcb OUT.json

A record, not a binding: m3_firmware/assembly_binding.py and build.py are bound to the archived R1 board and their
build chain cannot run in this repository (AGENTS section 1). R9 keeps R8's U1 pin map (R9_DECISIONS D-S1-07: the
pin table is sources/r8_design/pin_table.tsv, checked by check_r9 K-contract), so R8's binding constraints
(sources/r8_design/step9/binding_note.py CONSTRAINTS, R8_DECISIONS D6 / D27, imported unchanged) carry over; what
changes is the board / netlist hash and the IMU axis map (D-S7-06: U4 turned 180 degrees). It writes:
  - the board, netlist and pin-table SHA-256 a binding must be generated against;
  - U1's full pin map read from the board's pads, checked equal to pin_table.tsv's r8_net column (it fails otherwise),
    and the pins whose net differs from R8 (none expected: it fails if any);
  - R8's binding constraints, unchanged, and the R9 IMU axis map and lever arm measured on the board (U4's face,
    rotation, pad-1 offset, position; its z from fit_check's model box when FIT.json is given).
"""
import argparse
import csv
import hashlib
import importlib.util
import json
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
R8_STEP9 = HERE.parents[1] / 'r8_design/step9'
PIN_TABLE = HERE.parents[1] / 'r8_design/pin_table.tsv'
NETLIST = ROOT / 'm3_design/assembly_review/schematic.net.xml'
mm = pcbnew.ToMM
_spec = importlib.util.spec_from_file_location('r8_binding_note', R8_STEP9 / 'binding_note.py')
R8B = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(R8B)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('board', type=Path)
    ap.add_argument('out', type=Path)
    ap.add_argument('--fit', type=Path, help="tools/fit_check.py's report of the same board (U4's z)")
    a = ap.parse_args()
    b = pcbnew.LoadBoard(str(a.board.resolve()))
    rows = list(csv.DictReader(open(PIN_TABLE, encoding='utf-8'), delimiter='\t'))
    u1 = b.FindFootprintByReference('U1')
    pads = {p.GetNumber(): p.GetNetname() for p in u1.Pads()}
    mism = []
    for r in rows:
        net = pads.get(r['pin'], '')
        want = r['r8_net']
        if want in ('NC', '-', ''):
            if net and not net.startswith('unconnected-'):
                mism.append((r['pin'], want, net))
        elif net != want:
            mism.append((r['pin'], want, net))
    if mism:
        raise SystemExit(f'U1 pads differ from pin_table.tsv (R8 map): {mism}')
    u4 = b.FindFootprintByReference('U4')
    p1 = u4.FindPadByNumber('1')
    c = (mm(u4.GetPosition().x), mm(u4.GetPosition().y))
    z = None
    if a.fit:
        fit = json.loads(a.fit.read_text())
        if fit.get('board_sha256') != sha(a.board):
            raise SystemExit('the fit report is not of this board')
        row = next(r for r in fit['rows'] if r[1] == 'U4')
        z = round((row[3][4] + row[3][5]) / 2, 2)
    rot = u4.GetOrientationDegrees()
    if abs(abs(rot) - 180.0) > 1e-6 or not u4.IsFlipped():
        raise SystemExit(f'U4 rotation {rot}, face {"B" if u4.IsFlipped() else "F"}: not the D-S7-06 axis map')
    omega = 1850.0 * 3.141592653589793 / 180.0
    lever = abs(c[0] - 23.0) / 1000.0
    note = dict(
        profile='M3-ASSY-R9', status='record only: no binding generated (the R1 binding chain cannot run here)',
        board_sha256=sha(a.board), netlist_sha256=sha(NETLIST), pin_table_sha256=sha(PIN_TABLE),
        u1_map='equal to pin_table.tsv r8_net (R8\'s map, D-S1-07): 0 pins differ from R8',
        u1_pins={r['pin']: dict(port=r['port'], net=r['r8_net'], mode=r['r8_mode_af']) for r in rows},
        changed_from_r8={},
        constraints=R8B.CONSTRAINTS,
        imu=dict(part='U4 LSM6DSV320X', face='B', rotation=rot, at_mm=[round(c[0], 3), round(c[1], 3)],
                 pad1_offset_mm=[round(mm(p1.GetPosition().x) - c[0], 3), round(mm(p1.GetPosition().y) - c[1], 3)],
                 axes='+X_imu = -x_board, +Y_imu = -y_board (aft), +Z_imu out of the bottom face (R9_DECISIONS '
                      'D-S7-06: R8\'s bottom-face map, M3_R5 section 3, turned 180 degrees about z_board)',
                 roll='-gyro_Y (R7 / R8: +gyro_Y); thrust (forward, +y_board) reads -a_Y; check_r9 M-7 keys the '
                      'required rotation on the title-block revision',
                 lever_arm_mm=dict(x=round(c[0] - 23.0, 2), z=z, z_basis='fit_check model-box centre (bottom face)'),
                 centripetal_at_1850_dps_g=round(omega * omega * lever / 9.80665, 2),
                 centripetal_note='U4 sits west of the roll axis (as R8, 11.0 mm against R8\'s 13.0): the centripetal '
                                  'acceleration points to +x_board, which reads as -a_X in the R9 map (R8: +a_X)',
                 bench='rotate the board about +y_board (right-handed) and confirm gyro_Y reads negative, and confirm '
                       'a_Y reads -1 g with the forward edge up, before any flight (D-S7-06; ORDERING section 5)'),
    )
    a.out.write_text(json.dumps(note, indent=1) + '\n')
    print(f'binding note for {note["board_sha256"][:12]}: U1 map = pin table (R8), U4 rot {rot}, lever arm '
          f'{note["imu"]["lever_arm_mm"]}')


if __name__ == '__main__':
    main()
