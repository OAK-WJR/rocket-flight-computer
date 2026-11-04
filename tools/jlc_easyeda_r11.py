#!/usr/bin/env python3
"""R11's JLC footprint pad file (D-R11-67): tools/jlc_easyeda/pads_r11.json is R10's tools/jlc_easyeda/pads.json (left
unchanged: it is one of R10's bound fab inputs) plus the LCSC codes the R11 board adds, each fetched once from the
JLCEDA / EasyEDA Official Library's public product-to-component mapping (https://easyeda.com/api/products/<code>/
components; source: JLCEDA / EasyEDA Official Library, https://lceda.cn/, https://easyeda.com/). Run by hand when the
R11 parts list gains a code (needs the network); the build and the gate only read the file.

usage: <KiCad python3> -I tools/jlc_easyeda_r11.py [board.kicad_pcb]      (default m3_design/r11/m3.kicad_pcb)
Each record is {"title": the EasyEDA package name, "head": [x, y] of the footprint origin, "pads": the PAD~ shapes},
R10's format (tools/jlc_orient.py ez_pads).
"""
import json
from pathlib import Path
import sys
import subprocess

import pcbnew

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / 'tools/jlc_easyeda/pads.json'
OUT = ROOT / 'tools/jlc_easyeda/pads_r11.json'
URL = 'https://easyeda.com/api/products/{}/components'


def fetch(code):
    # curl, not urllib: KiCad's bundled Python has no system certificate store
    data = json.loads(subprocess.run(['curl', '-sfm', '30', URL.format(code)], check=True, capture_output=True,
                                     text=True).stdout)
    if not data.get('success'):
        # R10's convention (C861313): no EasyEDA footprint, so jlc_orient takes no correction from this record; a
        # standard chip on a footprint another code verified gets that donor's correction (jlc_orient's proxy rule)
        return {'error': f'API returned success:false, {data.get("code")} "{data.get("message")}" (curl, R11 fetch)'}
    package = (data.get('result') or {}).get('packageDetail') or {}
    shape = package.get('dataStr') or {}
    head = shape.get('head') or {}
    pads = [s for s in shape.get('shape', []) if s.startswith('PAD~')]
    if not pads:
        raise ValueError(f'{code}: no footprint pads in the EasyEDA record')
    return {'title': head.get('c_para', {}).get('package') or package.get('title'),
            'head': [float(head['x']), float(head['y'])], 'pads': pads}


def main():
    board = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'm3_design/r11/m3.kicad_pcb'
    b = pcbnew.LoadBoard(str(board))
    pads = json.loads(BASE.read_text())
    if OUT.exists():
        pads.update({k: v for k, v in json.loads(OUT.read_text()).items() if k not in pads})
    codes = sorted({f.GetField('LCSC').GetText() for f in b.GetFootprints() if f.HasField('LCSC')} - {''})
    added = []
    for code in codes:
        if code in pads:
            continue
        pads[code] = fetch(code)
        added.append(f'{code} {pads[code].get("title")} ({len(pads[code].get("pads", []))} pads)'
                     + (f' {pads[code]["error"]}' if 'error' in pads[code] else ''))
    OUT.write_text(json.dumps(dict(sorted(pads.items())), indent=1) + '\n')
    print(f'{OUT.relative_to(ROOT)}: {len(pads)} codes; added {len(added)}:', *added, sep='\n  ')


if __name__ == '__main__':
    main()
