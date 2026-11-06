#!/usr/bin/env python3
"""D-R12-96 (AVA re-layout): merge the zone fragments m3_design/r12_aid/zones/r12_routes_W1..W5.tsv, in that order,
into one copper table (r12_routes.tsv columns). Exact duplicate rows are an error, as is a via placed twice.

usage: python3 -I -B m3_design/r12_aid/zones/merge.py [--out m3_design/r12_routes.tsv] [fragment ...]
"""
import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
HEADER = ('# M3-ASSY-R12 copper table (stage C, D-R12-26; AVA re-layout D-R12-96): the zone fragments of '
          'm3_design/r12_aid/zones/\n# (W1 aft power / pyro / camera / servo, W2 east power, W3 MCU core, W4 sensors and CA, '
          'W5 ports), merged by merge.py; m3_design/r12_route.py replays it.\n'
          '# Coordinates in mm, board frame (x east, y forward from the aft edge).\n'
          'kind\tnet\tlayer\twidth\tx0\ty0\tx1\ty1\n')


def rows(path):
    for line in Path(path).read_text().splitlines():
        if not line.strip() or line.startswith('#') or line.startswith('kind\t'):
            continue
        r = line.split('\t')
        assert r[0] in ('track', 'via') and len(r) == 8, f'{path}: bad row {line!r}'
        yield line


def merge(frags):
    out, seen, vias = [], set(), set()
    for f in frags:
        out.append(f'# --- {Path(f).name}')
        for line in rows(f):
            assert line not in seen, f'{f}: duplicate row {line!r}'
            seen.add(line)
            r = line.split('\t')
            if r[0] == 'via':
                k = (round(float(r[4]), 4), round(float(r[5]), 4))
                assert k not in vias, f'{f}: via twice at {k}'
                vias.add(k)
            out.append(line)
    return HEADER + '\n'.join(out) + '\n'


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--out', type=Path, default=ROOT / 'm3_design/r12_routes.tsv')
    ap.add_argument('frags', nargs='*')
    a = ap.parse_args()
    frags = a.frags or [HERE / f'r12_routes_W{i}.tsv' for i in range(1, 6) if (HERE / f'r12_routes_W{i}.tsv').exists()]
    a.out.write_text(merge(frags))
    print(f'merge: {len(frags)} fragments -> {a.out}')


if __name__ == '__main__':
    sys.exit(main())
