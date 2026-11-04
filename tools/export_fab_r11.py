#!/usr/bin/env python3
"""R11's fab export (D-R11-67): tools/export_fab.py run unchanged on R11's board with R11's six copper layers
(D-R11-03: F / In1 / In2 / In3 / In4 / B), R11's placement corrections (tools/jlc_corrections_r11.json) and R11's
fab binding (tools/fab_manifest_r11.py: the export record carries R11's input hashes). R10's export_fab.py is one of
R10's bound fab inputs, so it is not edited; its source is executed with exactly the replacements below, each asserted
to occur as counted.

usage: python3 tools/export_fab_r11.py m3_design/r11/m3.kicad_pcb --out m3_design/r11/fab --pending RECORD
(m3_design/r11_fab.sh runs it, then tools/fab_manifest_r11.py --bind RECORD)
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'tools/export_fab.py'
REPLACE = (("ROOT / 'tools/jlc_corrections.json'", "ROOT / 'tools/jlc_corrections_r11.json'", 1),
           ("'F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste", "'F.Cu,In1.Cu,In2.Cu,In3.Cu,In4.Cu,B.Cu,F.Paste", 1),
           ("m3_design/r10_fab.sh", "m3_design/r11_fab.sh", 3))


def source():
    text = SOURCE.read_text()
    for old, new, count in REPLACE:
        if text.count(old) != count:
            raise SystemExit(f'export_fab_r11: {SOURCE.name} no longer has {count} x {old!r}')
        text = text.replace(old, new)
    return text


if __name__ == '__main__':
    sys.path.insert(0, str(ROOT / 'tools'))
    import fab_manifest_r11
    fab_manifest_r11.install()           # export_fab imports input_hashes / write_pending from fab_manifest: R11's
    code = compile(source(), str(SOURCE), 'exec')
    exec(code, {'__name__': '__main__', '__file__': str(SOURCE)})
