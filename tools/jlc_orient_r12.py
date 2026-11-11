#!/usr/bin/env python3
"""R12's JLC placement corrections: tools/jlc_orient.py run unchanged on R12's files, R11's method (D-R11-67).

R10's jlc_orient.py, jlc_corrections.json and jlc_easyeda/pads.json are bound inputs of R10's frozen fab package, so
R12 reads its own pad file (tools/jlc_easyeda/pads_r12.json) and writes its own corrections
(tools/jlc_corrections_r12.json). Every correction is reconstructed by matching JLC's own (JLCEDA / EasyEDA) footprint
pads to ours (rotation 0 / 90 / 180 / 270 and offset; jlc_orient.py's docstring), so the CPL puts JLC's footprint on
our copper. The R10 source is executed with exactly the replacements in REPLACE, each asserted to occur as counted, so
an upstream edit fails here instead of being silently skipped. The owner-fitted parts (m3_design/r12/design/circuit.json
"owner_fit", read through m3_design/r12_parts.py bom_lines()) replace R10's MANUAL_FIT: they would be in no CPL. Since
D-R12-85 the list is empty: every part, C84 and the THT LS120 / J121 included, is in the CPL and matched here.

The only hard-coded placement data are R12_MECHANICAL below, the per-footprint table of the mechanical tab numbers JLC's
footprint carries and ours leaves unnumbered, and R12_BODY, the body turns pad matching cannot see (D-R12-174). R10's own tables in jlc_orient.py (ONLY, OFFSET, BODY, PAD_TOLERANCE,
PAD_ALIAS) stay in force for the R10 footprints R12 reuses.

usage: <KiCad python3> -I tools/jlc_orient_r12.py --fetch [board]   make pads_r12.json hold exactly the board's LCSC
                                                                     codes (network for codes no earlier file has)
       <KiCad python3> -I tools/jlc_orient_r12.py tools/jlc_easyeda/pads_r12.json [board] [--out FILE]
       <KiCad python3> -I tools/jlc_orient_r12.py tools/jlc_easyeda/pads_r12.json [board] --verify-cpl CPL.csv
(board default m3_design/r12/m3.kicad_pcb; m3_design/r12_fab.sh runs the second form, tools/fab_manifest_r12.py
--verify-cpl the third)
"""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'tools/jlc_orient.py'
PADS = ROOT / 'tools/jlc_easyeda/pads_r12.json'
PRIOR_PADS = (ROOT / 'tools/jlc_easyeda/pads_r11.json', ROOT / 'tools/jlc_easyeda/pads.json')   # reused as read
BOARD = ROOT / 'm3_design/r12/m3.kicad_pcb'
URL = 'https://easyeda.com/api/products/{}/components'

# Per-footprint table (R12's one hard-coded placement table): (left tab, right tab), by the sign of the tab's x in the
# footprint's own frame, of the numbers JLCEDA gives the two fixing tabs of the Megastar ZX-SH1.0 side-entry headers;
# our lands (m3_design/r12_parts.py ghc()) leave them unnumbered. Read 2026-11-04 from
# https://easyeda.com/api/products/<code>/components: C7430446 ZX-SH1.0-4PWT pad 6 left, pad 5 right; C7430448
# ZX-SH1.0-6PWT pad 8 left, pad 7 right. Matching the tabs as well as the signals fixes the body's direction.
R12_MECHANICAL = {'M3_SHC_4P': ('6', '5'), 'M3_SHC_6P': ('8', '7')}
# D-R12-174: R12's body corrections, added to R10's BODY (a symmetric pin row, an asymmetric body: pad matching cannot
# see a 180 deg turn). Kefa KF301-5.0-2P (C474881): JLCEDA's footprint (https://easyeda.com/api/products/C474881/
# components, read 2026-11-10) draws the body -4.00 / +3.70 mm about the pin row with the two wire-cage outlines on its
# +y side, so its wire face is +y; ours (m3_design/r12_parts.py kf301()) is at local -y, toward the west edge. +180 makes
# JLC fit J1 wire face out; JLC's pin 1 then lands on our pin 2, which a two-way screw terminal does not care about.
R12_BODY = {'C474881': 180}

REPLACE = (("ROOT / 'tools/jlc_corrections.json'", "ROOT / 'tools/jlc_corrections_r12.json'", 2),
           ("MECHANICAL = {'M3_GH_BM04B_GHS_TBT'", "MECHANICAL = {**R12_MECHANICAL, 'M3_GH_BM04B_GHS_TBT'", 1),
           ("BODY = {'C2915641': 180}", "BODY = {'C2915641': 180, **R12_BODY}", 1),
           ("str(ROOT / 'm3_design/assembly_review/m3.kicad_pcb')", "str(ROOT / 'm3_design/r12/m3.kicad_pcb')", 1),
           ("    from export_fab import MANUAL_FIT          # D-R18-09: hand-fitted after reflow, never in the CPL\n",
            "    MANUAL_FIT = R12_OWNER_FIT                 # R12: owner-fitted after reflow, never in the CPL\n", 1))


def source():
    text = SOURCE.read_text()
    for old, new, count in REPLACE:
        if text.count(old) != count:
            raise SystemExit(f'jlc_orient_r12: {SOURCE.name} no longer has {count} x {old!r}')
        text = text.replace(old, new)
    return text


def fetch_record(code):
    """One JLCEDA footprint record in R10's format ({"title", "head", "pads"}), or R10's error record for a code with no
    footprint (jlc_orient then takes the correction of a verified code on the same footprint, if there is one)."""
    # curl, not urllib: KiCad's bundled Python has no system certificate store
    data = json.loads(subprocess.run(['curl', '-sfm', '30', URL.format(code)], check=True, capture_output=True,
                                     text=True).stdout)
    if not data.get('success'):
        return {'error': f'API returned success:false, {data.get("code")} "{data.get("message")}" (curl, R12 fetch)'}
    package = (data.get('result') or {}).get('packageDetail') or {}
    shape = package.get('dataStr') or {}
    head = shape.get('head') or {}
    pads = [s for s in shape.get('shape', []) if s.startswith('PAD~')]
    if not pads:
        raise ValueError(f'{code}: no footprint pads in the EasyEDA record')
    return {'title': head.get('c_para', {}).get('package') or package.get('title'),
            'head': [float(head['x']), float(head['y'])], 'pads': pads}


def fetch(board):
    """pads_r12.json holds exactly the board's LCSC codes: kept from itself, else R11's / R10's file, else fetched."""
    import pcbnew
    b = pcbnew.LoadBoard(str(board))
    codes = sorted({f.GetField('LCSC').GetText() for f in b.GetFootprints() if f.HasField('LCSC')} - {''})
    known = {}
    for path in (PADS, *PRIOR_PADS):
        if path.exists():
            for code, record in json.loads(path.read_text()).items():
                known.setdefault(code, record)
    pads, added = {}, []
    for code in codes:
        if code not in known:
            known[code] = fetch_record(code)
            added.append(f'{code} {known[code].get("title")} ({len(known[code].get("pads", []))} pads)'
                         + (f' {known[code]["error"]}' if 'error' in known[code] else ''))
        pads[code] = known[code]
    PADS.write_text(json.dumps(pads, indent=1, sort_keys=True) + '\n')
    print(f'{PADS.relative_to(ROOT)}: {len(pads)} codes; fetched {len(added)}:', *added, sep='\n  ')


def owner_fit():
    import fab_manifest_r12
    return fab_manifest_r12.r12_parts_bom()['owner']


if __name__ == '__main__':
    sys.path.insert(0, str(ROOT / 'tools'))
    if '--fetch' in sys.argv[1:]:
        rest = [a for a in sys.argv[1:] if a != '--fetch']
        fetch(Path(rest[0]) if rest else BOARD)
        sys.exit(0)
    code = compile(source(), str(SOURCE), 'exec')
    exec(code, {'__name__': '__main__', '__file__': str(SOURCE), 'R12_MECHANICAL': R12_MECHANICAL, 'R12_BODY': R12_BODY,
                'R12_OWNER_FIT': owner_fit() if '--verify-cpl' in sys.argv else {}})
