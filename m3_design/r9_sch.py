#!/usr/bin/env python3
"""Reproducible R8 -> R9 schematic transform (M3-ASSY-R9, build step 2; r9_plan.md sections 1, 4;
R9_OWNER_DECISIONS.md items 2 and 5; R9_DECISIONS.md D-S2-*).

usage: python3 m3_design/r9_sch.py [project_dir] [--netlist]
The input is the committed R8 project (commit 9c8179b; m3_design/r9_build.sh restores its sheets first); a second run
changes nothing. --netlist also regenerates schematic.net.xml with kicad-cli (local path made relative and the date
blanked, as r7_sch.py / r8_sch.py do). Verification: <KiCad python3> -I m3_design/r9_sch_check.py.

No net, pin or part changes: R9 keeps R8's netlist (every pin on its R8 net, the same parts and values, the same LCSC
codes), so check_actuators' netlist contract, the U1 pin table (sources/r8_design/pin_table.tsv) and the BOM hold as
they are. What changes:
1. Footprint fields (owner decisions 2 and 5): J121 and J124 -> rocket:M3_DB128L_2P_BK_SW, J122 ->
   rocket:HDR-TH_12P-P2.54-V-M-R3-C4-S2.54_MIR (m3_design/r9_lib.py: the same part on the same land, the numbering
   mirrored, so both pyro terminals turn to enter from -x with J124's RAW pin forward and J122's plug 1 lies west).
2. Notes: the pyro sheet's pin-order note and the servo sheet's D121 note (it described R8's lane reversal, which the
   mirrored J122 removes) are rewritten in place (same UUID); the servo sheet gains the J122 numbering note.
3. Every sheet: rev M3-ASSY-R9.
"""
import re
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import r7_sch as r7       # noqa: E402 (R7 helpers: symbol blocks, netlist export)
import r9_lib             # noqa: E402

NS = uuid.UUID('3f6d2b8e-91c4-5a7e-b0d2-6e4f8a1c9d35')    # fixed namespace -> stable R9 UUIDs
REV_OLD, REV = 'M3-ASSY-R8', 'M3-ASSY-R9'
SHEETS = 15
FOOTPRINTS = {   # ref -> (sheet, R8 footprint field, R9 footprint field)
    ref: (sheet, f'{r9_lib.LIB_NICK}:{r9_lib.VARIANTS[variant][0]}', f'{r9_lib.LIB_NICK}:{variant}')
    for ref, sheet in (('J121', 'pyro.kicad_sch'), ('J124', 'pyro.kicad_sch'), ('J122', 'servos.kicad_sch'))
    for variant in (r9_lib.VARIANT_REFS[ref],)}
NOTES = {   # sheet -> [(R8 text, R9 text)], rewritten in place (same UUID)
    'pyro.kicad_sch': [
        ('Igniter across J121.1 OUT and J121.2 IGN. J124 and J121 pin ordering is retained from the reviewed CH1.',
         'Igniter across J121.1 OUT and J121.2 IGN. J124 and J121 pin numbering (the net on each pin) is retained from '
         'the reviewed CH1. R9: both on M3_DB128L_2P_BK_SW (the DB128L with pads 1 and 2 swapped: same part C430601, '
         'same land), turned so both wires enter from -x (pyro leads west) with pin 2 (RAW / IGN) forward and pin 1 '
         '(BUS / OUT) aft.'),
    ],
    'servos.kicad_sch': [
        ('R8 (D7): D121 keeps the pass-5 channel map (pins 1/3/4/6 = SERVO1-4_MCU, 2 GND, 5 3V3); on the board it sits '
         'on the bottom side, on the U1-ordered servo lanes ahead of their reversal into J122\'s row order.',
         'R8 (D7), kept in R9: D121 keeps the pass-5 channel map (pins 1/3/4/6 = SERVO1-4_MCU, 2 GND, 5 3V3).'),
    ],
}
NEW_NOTES = {   # sheet -> [(key, text, x, y, font size)], in free sheet space one row above the sheet's notes, their size
    'servos.kicad_sch': [
        ('r9:servos:j122', 'R9: J122 on HDR-TH_12P-P2.54-V-M-R3-C4-S2.54_MIR (same part and land; plug columns numbered '
         'from +x, rows unchanged). At rotation 180 plug 1 (SERVO1) is the west plug: U1.22-25 reach plugs 1-4 in order.',
         20.32, 237.38, 1.27),
    ],
}


def uid(key):
    return str(uuid.uuid5(NS, key))


def note(textline, x, y, key, size):
    """A sheet note in r8_sch.note's format, with an R9 UUID."""
    return (f'\t(text "{textline}"\n\t\t(at {r7.fmt(x)} {r7.fmt(y)} 0)\n\t\t(effects\n\t\t\t(font'
            f'\n\t\t\t\t(size {size} {size}))\n\t\t\t(justify left))\n\t\t(uuid {uid(key)}))\n')


def t_footprints(name, t):
    """Section 1: the footprint field of each variant part on this sheet."""
    for ref, (sheet, old, new) in FOOTPRINTS.items():
        if sheet != name:
            continue
        assert t.count(f'(property "Reference" "{ref}"') == 1, f'{name}: {ref} not found once'
        s, e = r7.symbol_block(t, ref)
        blk = t[s:e]
        o, n = f'(property "Footprint" "{old}"', f'(property "Footprint" "{new}"'
        if blk.count(n) == 1 and o not in blk:
            continue
        assert blk.count(o) == 1 and n not in blk, f'{name}: {ref} footprint field is neither R8\'s {old} nor R9\'s {new}'
        t = t[:s] + blk.replace(o, n) + t[e:]
    return t


def t_notes(name, t):
    """Section 2: notes rewritten in place, R9 notes added once (UUIDs from fixed keys, as r8_sch)."""
    for old, new in NOTES.get(name, ()):
        assert '"' not in new and '\\' not in new
        o, n = f'(text "{old}"', f'(text "{new}"'
        if t.count(n) == 1 and o not in t:
            continue
        assert t.count(o) == 1 and n not in t, f'{name}: note not found once: {old[:60]}...'
        t = t.replace(o, n)
    for key, text, x, y, size in NEW_NOTES.get(name, ()):
        assert '"' not in text and '\\' not in text
        block = note(text, x, y, key, size)
        if block in t:
            assert t.count(block) == 1
            continue
        assert f'(uuid {uid(key)})' not in t, f'{name}: note {key} present in another form: restore the R8 sheets'
        assert not re.search(rf'\(at {r7.fmt(x)} {r7.fmt(y)} ', t), f'{name}: ({x}, {y}) is taken'
        t = r7.insert(t, block)
    return t


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    project = Path(args[0]) if args else Path(__file__).resolve().parent / 'assembly_review'
    sheets = sorted(project.glob('*.kicad_sch'))
    assert len(sheets) == SHEETS, f'expected the {SHEETS} R8 sheets, found {len(sheets)}'
    lib = project / 'kilib' / f'{r9_lib.LIB_NICK}.pretty'
    for _ref, (_sheet, _old, new) in FOOTPRINTS.items():
        assert (lib / f'{new.split(":", 1)[1]}.kicad_mod').is_file(), f'{new} missing: run m3_design/r9_lib.py first'
    for f in sheets:
        original = f.read_text()
        text = t_footprints(f.name, original)
        text = t_notes(f.name, text)
        text = text.replace(f'(rev "{REV_OLD}")', f'(rev "{REV}")')
        assert text.count(f'(rev "{REV}")') == 1, f'{f.name}: one title block with rev {REV}'
        if text != original:
            f.write_text(text)
            print('edited', f.name)
    if '--netlist' in sys.argv:
        r7.export_netlist(project)
    print(f'R9 schematic: footprint fields {", ".join(f"{r} {n}" for r, (_s, _o, n) in sorted(FOOTPRINTS.items()))}; '
          f'{sum(len(v) for v in NOTES.values())} notes rewritten, {sum(len(v) for v in NEW_NOTES.values())} added; '
          f'rev {REV}')


if __name__ == '__main__':
    main()
