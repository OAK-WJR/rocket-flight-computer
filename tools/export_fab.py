#!/usr/bin/env python3
"""Manufacturing package for the M3 board: Gerbers + drill (zipped), JLCPCB-style BOM and CPL.

usage: tools/export_fab.py [board.kicad_pcb] [--out DIR]
Needs kicad-cli (KICAD_CLI env var or on PATH / default macOS location).
Everything is regenerated from the KiCad project; nothing here is hand-edited.
The BOM/CPL are a *candidate* assembly package: JLCPCB rotation offsets and
through-hole assembly service must be checked in their preview before ordering.
"""
import argparse, csv, os, re, shutil, subprocess, sys, tempfile, zipfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'quality_audit'))
from sexpr import read, properties  # noqa: E402

CLI = os.environ.get('KICAD_CLI') or shutil.which('kicad-cli') or '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
if not Path(CLI).exists():
    CLI = '/Applications/KiCad.app/Contents/MacOS/kicad-cli'


def run(*args):
    subprocess.run([CLI, *args], check=True, capture_output=True, text=True)


def footprints(board):
    rows = []
    for fp in read(board.read_text()).children('footprint'):
        p = properties(fp)
        get = lambda k: p[k].items[2].atom if k in p else ''
        attrs = {a.atom for n in fp.children('attr') for a in n.items[1:] if hasattr(a, 'atom')}
        at = fp.children('at')[0].items
        rows.append(dict(ref=get('Reference'), value=get('Value'), lcsc=get('LCSC'),
                         mpn=get('Manufacturer Part'), fp=fp.items[1].atom.split(':')[-1],
                         x=float(at[1].atom), y=float(at[2].atom),
                         rot=float(at[3].atom) if len(at) > 3 else 0.0,
                         layer=fp.children('layer')[0].items[1].atom,
                         smd='smd' in attrs, tht='through_hole' in attrs,
                         no_bom='exclude_from_bom' in attrs, no_pos='exclude_from_pos_files' in attrs))
    return rows


def natural(ref):
    m = re.match(r'([A-Za-z]+)(\d+)', ref)
    return (m.group(1), int(m.group(2))) if m else (ref, 0)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('board', nargs='?', default=str(ROOT / 'm3_design/assembly_review/m3.kicad_pcb'))
    ap.add_argument('--out', default=str(ROOT / 'm3_design/assembly_review/fab'))
    a = ap.parse_args()
    board, out = Path(a.board).resolve(), Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    stem = board.stem
    with tempfile.TemporaryDirectory() as tmp:
        g = Path(tmp) / 'gerber'; g.mkdir()
        run('pcb', 'export', 'gerbers', '--no-protel-ext', '--layers',
            'F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts',
            '-o', str(g) + '/', str(board))
        run('pcb', 'export', 'drill', '--format', 'excellon', '--excellon-separate-th',
            '--generate-map', '--map-format', 'gerberx2', '-o', str(g) + '/', str(board))
        zpath = out / f'{stem}_gerber.zip'
        with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED) as z:
            for f in sorted(g.iterdir()):
                z.write(f, f.name)
    rows = [r for r in footprints(board) if r['ref'] and not r['ref'].startswith('#')]
    # BOM: one line per (value, footprint, LCSC); DNP / board-only items excluded
    groups = defaultdict(list)
    for r in rows:
        if r['no_bom']: continue
        groups[(r['value'], r['fp'], r['lcsc'], r['mpn'])].append(r['ref'])
    with open(out / f'{stem}_bom_jlc.csv', 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['Comment', 'Designator', 'Footprint', 'LCSC Part #', 'Manufacturer Part', 'Qty', 'Assembly'])
        for (val, fp, lcsc, mpn), refs in sorted(groups.items(), key=lambda kv: natural(sorted(kv[1], key=natural)[0])):
            refs = sorted(refs, key=natural)
            tht = any(r['tht'] for r in rows if r['ref'] in refs)
            w.writerow([val, ','.join(refs), fp, lcsc, mpn, len(refs), 'THT (hand/THT service)' if tht else 'SMT'])
    with open(out / f'{stem}_cpl_jlc.csv', 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation'])
        for r in sorted(rows, key=lambda r: natural(r['ref'])):
            if r['no_bom'] or r['no_pos'] or not r['smd']: continue
            # KiCad y grows downward; JLC expects the usual Cartesian sign.
            w.writerow([r['ref'], f"{r['x']:.4f}mm", f"{-r['y']:.4f}mm",
                        'Top' if r['layer'] == 'F.Cu' else 'Bottom', f"{r['rot'] % 360:.0f}"])
    missing = sorted({r['ref'] for r in rows if not r['no_bom'] and not r['lcsc']}, key=natural)
    print('wrote', zpath.name, f'{stem}_bom_jlc.csv', f'{stem}_cpl_jlc.csv', 'to', out)
    print('BOM lines', len(groups), '| placed parts', sum(1 for r in rows if not r['no_bom']),
          '| parts without LCSC code:', ', '.join(missing) or 'none')


if __name__ == '__main__':
    main()
