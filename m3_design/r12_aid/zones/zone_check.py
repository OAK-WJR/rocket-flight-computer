#!/usr/bin/env python3
"""D-R12-96 (AVA re-layout): build a scratch copy of the R12 board with some zone fragments and report KiCad DRC
(with schematic parity), route_check r12 and check_r12 copper findings, each sorted into the routing zone(s) of
zones.json by position. Nothing in the repository changes (the placed board is regenerated in a temporary project).

usage: <KiCad python3> -I -B m3_design/r12_aid/zones/zone_check.py [--zone W3] [--out DIR] [--no-route-check]
           [--no-check-r12] [fragment.tsv ...]
Fragments default to every m3_design/r12_aid/zones/r12_routes_W*.tsv present. Unconnected items are listed with the
zones of their two ends; items whose two ends are in different zones are expected until those zones are merged.
"""
import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
import merge                     # noqa: E402
import zone_guard                # noqa: E402

KICAD_PY = os.environ.get('KICAD_PY', sys.executable)
KICAD_CLI = os.environ.get('KICAD_CLI', '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli')
Z = json.loads((HERE / 'zones.json').read_text())


def zones_of(x, y):
    return sorted(z for z, d in Z['zones'].items() if zone_guard.inside(d['polygon'], x, y)) or ['outside']


def route_zones(finding):
    """Prefer route_check's x/y; skip labels such as at='free' when trying older coordinate fields."""
    for xy in ((finding.get('x'), finding.get('y')), *(finding.get(k) for k in ('at', 'xy', 'pos'))):
        if isinstance(xy, dict):
            xy = (xy.get('x'), xy.get('y'))
        if (isinstance(xy, (list, tuple)) and len(xy) >= 2
                and all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in xy[:2])):
            return zones_of(*xy[:2])
    return ['?']


def run(cmd, **kw):
    env = dict(os.environ, PYTHONHASHSEED='0', KICAD_CLI=KICAD_CLI)
    return subprocess.run([str(c) for c in cmd], capture_output=True, text=True, env=env, cwd=ROOT, **kw)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--zone')
    ap.add_argument('--out', type=Path)
    ap.add_argument('--no-route-check', action='store_true')
    ap.add_argument('--no-check-r12', action='store_true')
    ap.add_argument('frags', nargs='*')
    a = ap.parse_args()
    out = a.out or Path(tempfile.mkdtemp(prefix='r12zone_'))
    out.mkdir(parents=True, exist_ok=True)
    frags = a.frags or [str(HERE / f'r12_routes_W{i}.tsv') for i in range(1, 6) if (HERE / f'r12_routes_W{i}.tsv').exists()]
    proj = out / 'r12'
    if proj.exists():
        shutil.rmtree(proj)
    shutil.copytree(ROOT / 'm3_design/r12', proj, ignore=shutil.ignore_patterns('fab'))
    r = run([KICAD_PY, '-I', '-B', 'm3_design/r12_pcb.py', '--project', proj])
    if r.returncode:
        print(r.stdout[-3000:], r.stderr[-3000:]); sys.exit('zone_check: placement failed')
    routes = out / 'routes.tsv'
    routes.write_text(merge.merge(frags))
    board = proj / 'm3.kicad_pcb'
    r = run([KICAD_PY, '-I', '-B', 'm3_design/r12_route.py', '--board', board, '--routes', routes])
    print((r.stdout + r.stderr).strip().splitlines()[-1] if (r.stdout + r.stderr).strip() else '')
    if r.returncode:
        print(r.stderr[-3000:]); sys.exit('zone_check: r12_route failed')
    drc = out / 'drc.json'
    run([KICAD_CLI, 'pcb', 'drc', '--schematic-parity', '--severity-all', '--format', 'json', '-o', drc, board])
    d = json.loads(drc.read_text())
    summary = {}
    lines = []
    for v in d.get('violations', []):
        zs = sorted({z for it in v['items'] for z in zones_of(it['pos']['x'], it['pos']['y'])})
        for z in zs:
            summary.setdefault(z, {}).setdefault('violations', 0)
            summary[z]['violations'] += 1
        if not a.zone or a.zone in zs:
            lines.append(f"VIOL {'/'.join(zs)} {v['type']}: " + ' | '.join(
                f"{it['description']} @({it['pos']['x']:.3f},{it['pos']['y']:.3f})" for it in v['items']))
    for v in d.get('unconnected_items', []):
        zs = [zones_of(it['pos']['x'], it['pos']['y'])[0] for it in v['items']]
        key = 'unconnected_cross' if len(set(zs)) > 1 else 'unconnected'
        for z in set(zs):
            summary.setdefault(z, {}).setdefault(key, 0)
            summary[z][key] += 1
        if not a.zone or a.zone in zs:
            lines.append(f"UNCON {'/'.join(zs)}: " + ' | '.join(
                f"{it['description']} @({it['pos']['x']:.3f},{it['pos']['y']:.3f})" for it in v['items']))
    for p in d.get('schematic_parity', []):
        lines.append(f"PARITY {p['type']}: {p['description']}")
    if not a.no_route_check:
        rc = out / 'route.json'
        run([KICAD_PY, '-I', '-B', 'tools/route_check.py', board, '--profile', 'r12', '--report', rc])
        try:
            rep = json.loads(rc.read_text())
            fails = rep.get('failures') or rep.get('failing') or []
            for f in fails:
                txt = json.dumps(f)
                zs = route_zones(f)
                if not a.zone or a.zone in zs:
                    lines.append(f"ROUTE {'/'.join(zs)} {txt[:400]}")
                for z in zs:
                    summary.setdefault(z, {}).setdefault('route_check', 0)
                    summary[z]['route_check'] += 1
        except Exception as e:                       # report shape differs: point at the file
            lines.append(f'ROUTE report not parsed ({e}); see {rc}')
    if not a.no_check_r12:
        cr = out / 'r12.json'
        run([KICAD_PY, '-I', '-B', 'tools/check_r12.py', board, '--stage', 'copper', '--report', cr,
             '--advisory', ''])
        try:
            rep = json.loads(cr.read_text())
            for i in rep.get('issues', []):
                lines.append(f'CHECK_R12 {str(i)[:400]}')
        except Exception as e:
            lines.append(f'CHECK_R12 report not parsed ({e}); see {cr}')
    (out / 'findings.txt').write_text('\n'.join(lines) + '\n')
    print('\n'.join(lines[:400]))
    print('summary per zone:', json.dumps(summary, sort_keys=True))
    print('board:', board, '| reports:', out)


if __name__ == '__main__':
    main()
