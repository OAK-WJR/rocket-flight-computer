#!/usr/bin/env python3
"""Create review copies with consistent metadata and project-local model paths.

Does not regenerate boards, choose replacement parts or change electrical geometry.
The existing board's explicit LCSC field is authoritative for alias repair only.
Differences from the builder's PARTS table remain visible review blockers.
"""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

from sexpr import patch, properties, protected_digest, quote, read


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def part_table(script):
    # Parse data without importing/running the board-generation code.
    nodes = [n for n in ast.parse(script.read_text()).body
             if isinstance(n, ast.Assign) and any(
                 isinstance(t, ast.Name) and t.id == 'PARTS' for t in n.targets)]
    if len(nodes) != 1:
        raise ValueError('Expected one literal PARTS assignment: ' + str(script))
    return ast.literal_eval(nodes[0].value)


def model_path(name, project):
    expanded = name.replace('${KIPRJMOD}', str(project))
    if '${' in expanded or '$(' in expanded:
        raise ValueError('Unresolved model variable: ' + name)
    path = Path(expanded)
    path = (path if path.is_absolute() else project / path).resolve()
    relative = path.relative_to(project.resolve())
    if not path.is_file():
        raise FileNotFoundError(path)
    return '${KIPRJMOD}/' + relative.as_posix(), relative


def normalize(text, project, library=False):
    root = read(text)
    footprints = [root] if library else root.children('footprint')
    edits, changes, model_files = [], [], set()
    refs = set()
    for fp in footprints:
        props = properties(fp)
        ref = fp.items[1].atom if library else props['Reference'].items[2].atom
        if ref in refs:
            raise ValueError('Duplicate footprint reference ' + ref)
        refs.add(ref)
        canonical = props.get('LCSC')
        if not library and canonical is None:
            raise ValueError('No explicit LCSC field for ' + ref)
        value = None if library else props['Value'].items[2].atom
        for key in ('LCSC', 'LCSC Part'):
            node = props.get(key)
            if node is None:
                # A single canonical field is sufficient. Do not invent a duplicate
                # field's UUID or display geometry in a routed-board review copy.
                continue
            before = node.items[2].atom
            if library:
                edits.append((node.start, node.end, ''))
                changes.append({'ref': ref, 'field': key, 'before': before, 'after': None})
            elif before != canonical.items[2].atom:
                token = node.items[2]
                after = canonical.items[2].atom
                edits.append((token.start, token.end, quote(after)))
                changes.append({'ref': ref, 'field': key, 'before': before, 'after': after})
        for desc in fp.children('descr'):
            after = fp.items[1].atom if library else value + ' ' + canonical.items[2].atom
            edits.append((desc.items[1].start, desc.items[1].end, quote(after)))
        # An optional Description field is descriptive only; leave its display settings intact.
        if 'Description' in props and props['Description'].items[2].atom:
            token = props['Description'].items[2]
            after = fp.items[1].atom if library else value + ' ' + canonical.items[2].atom
            edits.append((token.start, token.end, quote(after)))
        for model in fp.children('model'):
            token = model.items[1]
            after, relative = model_path(token.atom, project)
            model_files.add(relative)
            if after != token.atom:
                edits.append((token.start, token.end, quote(after)))
                changes.append({'ref': ref, 'field': 'model path',
                                'before': token.atom, 'after': after})
    output = patch(text, edits)
    if protected_digest(text) != protected_digest(output):
        raise RuntimeError('Protected PCB or model geometry changed')
    return output, changes, model_files


def table_drift(text, table):
    differences, seen = [], set()
    for fp in read(text).children('footprint'):
        p = properties(fp)
        ref = p['Reference'].items[2].atom
        seen.add(ref)
        actual = (p['LCSC'].items[2].atom, fp.items[1].atom.split(':')[-1],
                  p['Value'].items[2].atom)
        expected = tuple(table[ref][:3]) if ref in table else None
        if actual != expected:
            differences.append({'ref': ref, 'board': actual, 'PARTS': expected})
    for ref in table.keys() - seen:
        differences.append({'ref': ref, 'board': None, 'PARTS': table[ref][:3]})
    return differences


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--boards', nargs='+', default=['m1', 'm2'])
    parser.add_argument('--apply-library', action='store_true')
    args = parser.parse_args()
    project, output = args.project.resolve(), args.output.resolve()
    if output.exists():
        raise ValueError('Output already exists; use a new directory to preserve evidence')
    plans, model_files = [], set()
    board_names = {name + '.kicad_pcb' for name in args.boards}
    paths = [project / n for n in sorted(board_names)]
    paths += sorted((project / 'kilib/rocket.pretty').glob('*.kicad_mod'))
    if not paths or not any(p.suffix == '.kicad_mod' for p in paths):
        raise ValueError('Footprint library is missing')
    for path in paths:
        before = path.read_text()
        library = path.suffix == '.kicad_mod'
        after, changes, models = normalize(before, project, library)
        drift = [] if library else table_drift(before, part_table(path.with_suffix('.py')))
        plans.append((path, before, after, changes, drift))
        model_files.update(models)
    # Everything is parsed and validated before any changes are written.
    review, backup = output / 'review', output / 'before'
    review.mkdir(parents=True)
    backup.mkdir()
    manifest = {'created_utc': datetime.now(timezone.utc).isoformat(),
                'scope': 'Metadata/path normalization only; NOT a fabrication release.',
                'electrical_design_verified': False, 'mechanical_fit_verified': False,
                'files': []}
    for path, before, after, changes, drift in plans:
        rel = path.relative_to(project)
        old, new = backup / rel, review / rel
        old.parent.mkdir(parents=True, exist_ok=True)
        new.parent.mkdir(parents=True, exist_ok=True)
        old.write_text(before)
        new.write_text(after)
        if args.apply_library and path.suffix == '.kicad_mod':
            if path.read_text() != before:
                raise RuntimeError('Concurrent modification: ' + str(path))
            path.write_text(after)
        manifest['files'].append({'source': str(path), 'review': str(rel),
                                  'before_sha256': sha(old), 'after_sha256': sha(new),
                                  'protected_geometry_sha256': protected_digest(before),
                                  'changes': changes, 'builder_drift': drift})
    for rel in sorted(model_files):
        dst = review / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(project / rel, dst)
    # Copy STEP counterparts too, when available for local viewing/export.
    for rel in sorted(model_files):
        for ext in ('.step', '.stp'):
            sibling = (project / rel).with_suffix(ext)
            if sibling.is_file():
                shutil.copy2(sibling, (review / rel).with_suffix(ext))
    for name in args.boards:
        pro = project / (name + '.kicad_pro')
        if pro.is_file():
            shutil.copy2(pro, review / pro.name)
        shutil.copy2(project / (name + '.py'), backup / (name + '.py'))
    (review / 'fp-lib-table').write_text(
        '(fp_lib_table (version 7) (lib (name "rocket") (type "KiCad") '
        '(uri "${KIPRJMOD}/kilib/rocket.pretty") (options "") '
        '(descr "Review copy; not electrically or mechanically qualified")))\n')
    (review / 'README.txt').write_text(
        'Review copy: only metadata and model paths are unified. Circuit, copper, pads, references, values,\n'
        'coordinates and model rotation / offset / scale are all preserved. Not a manufacturing release package.\n'
        'Consistent fields do not mean the part numbers are right; check builder_drift in manifest.json.\n')
    manifest['review_file_hashes'] = {
        str(p.relative_to(review)): sha(p) for p in sorted(review.rglob('*')) if p.is_file()}
    (output / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print('Review copies:', review)
    for item in manifest['files']:
        if item['review'].endswith('.kicad_pcb'):
            print(item['review'], 'metadata/path edits:', len(item['changes']),
                  'unresolved builder drift:', len(item['builder_drift']))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
