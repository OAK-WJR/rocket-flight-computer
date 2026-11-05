#!/usr/bin/env python3
"""R12's fab export: tools/export_fab.py run unchanged on R12's board (R11's method, D-R11-67) with R12's four copper
layers (F / In1 / In2 / B), one assembled side (every part on F, D-R12-01: no B.Paste Gerber), R12's placement
corrections (tools/jlc_corrections_r12.json, from tools/jlc_orient_r12.py), R12's owner-fitted parts and R12's fab
binding (tools/fab_manifest_r12.py: the export record carries R12's input hashes). R10's export_fab.py is one of R10's
bound fab inputs, so it is not edited; its source is executed with exactly the replacements below, each asserted to
occur as counted.

Owner-fitted parts (m3_design/r12/design/circuit.json "owner_fit", read through m3_design/r12_parts.py bom_lines())
replace R10's MANUAL_FIT: a part listed there would leave the JLC BOM and CPL for an owner BOM. Since D-R12-85 (owner
2026-11-05: every part JLC-assembled) the list is empty, so no owner BOM is written; C84 is placed (SMT) and LS120 /
J121 are JLC THT assembly. Parts excluded from the BOM on the board (wire pads, test pads, the TC2030
footprint) are in no BOM or CPL. Runs under KiCad's Python (r12_parts.bom_lines() reads the lands with pcbnew).

usage: <KiCad python3> -I tools/export_fab_r12.py m3_design/r12/m3.kicad_pcb --out m3_design/r12/fab --pending RECORD
(m3_design/r12_fab.sh runs it, then tools/fab_manifest_r12.py --bind RECORD)
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'tools/export_fab.py'
REPLACE = (("ROOT / 'tools/jlc_corrections.json'", "ROOT / 'tools/jlc_corrections_r12.json'", 1),
           ("'F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts'",
            "'F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts'", 1),
           ("MANUAL_FIT = {'C84': 'manual, after both reflow passes (docs/ORDERING.md section 8.2)'}",
            "MANUAL_FIT = R12_OWNER_FIT", 1),
           ("m3_design/r10_fab.sh", "m3_design/r12_fab.sh", 3))


def source():
    text = SOURCE.read_text()
    for old, new, count in REPLACE:
        if text.count(old) != count:
            raise SystemExit(f'export_fab_r12: {SOURCE.name} no longer has {count} x {old!r}')
        text = text.replace(old, new)
    return text


if __name__ == '__main__':
    sys.path.insert(0, str(ROOT / 'tools'))
    import fab_manifest_r12
    fab_manifest_r12.install()           # export_fab imports input_hashes / write_pending from fab_manifest: R12's
    owner = fab_manifest_r12.r12_parts_bom()['owner']
    code = compile(source(), str(SOURCE), 'exec')
    exec(code, {'__name__': '__main__', '__file__': str(SOURCE), 'R12_OWNER_FIT': owner})
