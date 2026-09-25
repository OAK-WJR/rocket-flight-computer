#!/usr/bin/env python3
"""Read-only KiCad artifact metadata audit. Does not certify electrical correctness."""
import argparse
import hashlib
import json
import re
from pathlib import Path
from sexpr import read


def parse(text):
    root = read(text)
    if root.key != 'kicad_pcb':
        raise ValueError('Expected one kicad_pcb root')
    return root.value()


def children(node, key):
    return [x for x in node if isinstance(x, list) and x and x[0] == key]


def audit(board):
    data = board.read_bytes()
    root = parse(data.decode('utf-8'))
    footprints = children(root, 'footprint')
    conflicts, missing_fields, models, no_courtyard = [], [], [], []
    for fp in footprints:
        fields = {p[1]: p[2] for p in children(fp, 'property') if len(p) >= 3}
        ref = fields.get('Reference', '?')
        a, b = fields.get('LCSC', '').strip(), fields.get('LCSC Part', '').strip()
        if a and b and a != b:
            conflicts.append({'ref': ref, 'value': fields.get('Value'),
                              'LCSC': a, 'LCSC Part': b})
        if not a and not b:
            missing_fields.append(ref)
        if not any(isinstance(x, list) and any(
                layer[1] in ('F.CrtYd', 'B.CrtYd') for layer in children(x, 'layer'))
                   for x in fp):
            no_courtyard.append(ref)
        for model in children(fp, 'model'):
            name = model[1]
            resolved = name.replace('${KIPRJMOD}', str(board.parent))
            path = Path(resolved)
            unresolved = '${' in resolved or '$(' in resolved
            if not path.is_absolute():
                path = board.parent / path
            models.append({'ref': ref, 'path': name,
                           'absolute_path': Path(name).is_absolute(),
                           'exists': None if unresolved else path.is_file(),
                           'transform': {k: children(model, k) for k in
                                         ('offset', 'scale', 'rotate')},
                           'mechanical_geometry_verified': False})
    return {'board': str(board), 'sha256': hashlib.sha256(data).hexdigest(),
            'footprints': len(footprints), 'conflicting_part_fields': conflicts,
            'no_part_field': missing_fields, 'no_courtyard': no_courtyard,
            'models': models}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('boards', nargs='+', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    result = {'scope': 'Metadata/path audit only; no board modification or certification.',
              'boards': [audit(p.resolve()) for p in args.boards]}
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    for item in result['boards']:
        print('{}: footprints={}, conflicting part fields={}, missing models={}, '
              'absolute model paths={}, no courtyard={}'.format(
                  Path(item['board']).name, item['footprints'],
                  len(item['conflicting_part_fields']),
                  sum(m['exists'] is False for m in item['models']),
                  sum(m['absolute_path'] for m in item['models']),
                  len(item['no_courtyard'])))
    # Fail closed for proven metadata conflicts/missing model files. Missing fields
    # and courtyards are review items (e.g. intentionally unpopulated hardware).
    return int(any(b['conflicting_part_fields'] or
                   any(m['exists'] is False for m in b['models']) for b in result['boards']))


if __name__ == '__main__':
    raise SystemExit(main())
