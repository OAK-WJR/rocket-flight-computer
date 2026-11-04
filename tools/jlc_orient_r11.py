#!/usr/bin/env python3
"""R11's JLC placement corrections (D-R11-67): tools/jlc_orient.py run unchanged on R11's files. R10's jlc_orient.py,
jlc_corrections.json and jlc_easyeda/pads.json are bound inputs of R10's frozen fab package, so R11 reads its own
corrections file (tools/jlc_corrections_r11.json) and pad file (tools/jlc_easyeda/pads_r11.json, from
tools/jlc_easyeda_r11.py), and adds the mechanical tab numbers of its side-entry JST GH ports (R11_MECHANICAL; EasyEDA
numbers the two fixing tabs, KiCad leaves them unnumbered). The R10 source is executed with exactly these replacements,
each asserted to occur as counted, so an upstream edit fails here instead of being silently skipped.

usage: <KiCad python3> -I tools/jlc_orient_r11.py tools/jlc_easyeda/pads_r11.json [board] [--out FILE]
       <KiCad python3> -I tools/jlc_orient_r11.py tools/jlc_easyeda/pads_r11.json [board] --verify-cpl CPL.csv
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'tools/jlc_orient.py'
# (left tab, right tab) in the footprint's own x: EasyEDA's numbers (C189893 SM02B 4 / 3, C189895 SM04B 6 / 5,
# C189896 SM05B 7 / 6, C133065 SM06B 7 / 8; tools/jlc_easyeda/pads_r11.json, read 2026-11-03)
R11_MECHANICAL = {'M3_GH_SM02B_GHS_TB': ('4', '3'), 'M3_GH_SM04B_GHS_TB': ('6', '5'),
                  'M3_GH_SM05B_GHS_TB': ('7', '6'), 'M3_GH_SM06B_GHS_TB': ('7', '8')}
REPLACE = (("ROOT / 'tools/jlc_corrections.json'", "ROOT / 'tools/jlc_corrections_r11.json'", 2),
           ("MECHANICAL = {'M3_GH_BM04B_GHS_TBT'", "MECHANICAL = {**R11_MECHANICAL, 'M3_GH_BM04B_GHS_TBT'", 1),
           ("str(ROOT / 'm3_design/assembly_review/m3.kicad_pcb')", "str(ROOT / 'm3_design/r11/m3.kicad_pcb')", 1))


def source():
    text = SOURCE.read_text()
    for old, new, count in REPLACE:
        if text.count(old) != count:
            raise SystemExit(f'jlc_orient_r11: {SOURCE.name} no longer has {count} x {old!r}')
        text = text.replace(old, new)
    return text


if __name__ == '__main__':
    sys.path.insert(0, str(ROOT / 'tools'))
    code = compile(source(), str(SOURCE), 'exec')
    exec(code, {'__name__': '__main__', '__file__': str(SOURCE), 'R11_MECHANICAL': R11_MECHANICAL})
